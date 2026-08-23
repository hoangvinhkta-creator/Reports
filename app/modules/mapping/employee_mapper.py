"""Map raw `NVBH` strings to normalized employees and their group (DEC-104,
DEC-127).

One-to-one on identity: every raw prefix resolves to its own employee, so a
real person is never merged into someone else. Employees that share a
conversion policy are joined by `group` instead — that is what
`employee_group` exists for (DEC-127 §1, ADR-106). An earlier version
collapsed three raw prefixes into a single fake employee; that erased three
real identities and has been undone.

Matching is prefix-based because the raw column carries trailing noise — a
phone number, sometimes a branch suffix (`"Đức Kiên - Tân Á 0867666533"`). A
raw value that matches no configured prefix is never silently dropped — it
comes back flagged `unmapped` so the caller can route it to review, and its
ConversionScheme resolves to `Unresolved` rather than borrowing a rate (C11,
`docs/analysis/10_OPEN_QUESTIONS.md`).

**Đây là NGUỒN SỰ THẬT DUY NHẤT cho việc chọn employee record (DEC-132).**
Trước Independent Review #5, validation mang bản sao riêng của quy tắc này —
`select_effective_record` — cộng thêm một vòng khớp prefix thứ ba dựng ngay
trong `collect_mapping_stats`. Ba bản cài đặt đã drift khỏi nhau theo hai
hướng đo được: prefix rỗng (bản này nhận, bản kia loại) và khoảng trắng (bản
này khớp thô, bản kia khớp sau normalize). Việc chứng minh chúng đồng ý chỉ
mạnh bằng ma trận case của test, và ma trận đó đã bỏ sót đúng hai case trên
suốt bốn vòng review.

Nên module này công bố chính các primitive mà validation cần, và validation
NHẬN LẠI kết quả thay vì tự dựng lại:

    resolve_record(raw, as_of)     -> ĐÚNG record mà `resolve()` đã chọn
    candidate_records(raw, as_of)  -> mọi record hiệu lực khớp, TRƯỚC tie-break
    record(ref) / records          -> đọc lại record theo danh tính

`resolve()` được viết TRÊN `resolve_record()`, nên không tồn tại đường nào để
hai bên bất đồng: chỉ có một phép chọn record trong toàn hệ thống.

**Independent Review #6 chỉ ra rằng như thế vẫn chưa đủ (DEC-133).** `RecordRef`
nêu một *vị trí* mà không nêu *vật chứa*. Vị trí không kèm vật chứa không phải
danh tính — nó là offset, và offset thì alias được sang một list khác: đo được
tại `ed38fd6`, `A.record(ref)` trả `'Ly'` còn `B.record(ref)` trả `'Kiên'`, im
lặng. Repair #1 mới chỉ thay "danh tính theo giá trị" (va chạm) bằng "danh tính
theo vị trí" (alias). Cả hai đều là tái tạo, không cái nào là bằng chứng sở hữu.

Khái niệm còn thiếu là `EmployeeMaster`: **snapshot bất biến, có danh tính dẫn
từ nội dung**. `RecordRef` mang `snapshot_id`, nên một ref lạ bị TỪ CHỐI thay
vì được resolve theo index. Và vì id dẫn từ nội dung, "hai mapper cùng master
data" là một mệnh đề *chứng minh được*, không phải giả định — hai lần đọc cùng
một file không đổi thì bằng nhau một cách chính đáng.

`EmployeeMaster` sở hữu **cả** `employees` lẫn `employee_groups`. Trước đây
`Validator` đọc `employee_groups` bằng một lần `load_yaml` riêng, nên hai nửa
của cùng một master có thể đến từ hai lần đọc khác nhau — đúng lớp lỗi mà
Repair #1 tuyên bố đã đóng. Sở hữu chung cũng là điều khiến referential
integrity (`employee.group ∈ employee_groups`) có một cái nhà (HD-110-09).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, Optional

from app.modules.config.loader import effective_rows, load_yaml
from app.modules.domain.models import (
    MAPPING_STATUS_INACTIVE,
    MAPPING_STATUS_MAPPED,
    MAPPING_STATUS_UNMAPPED,
    WorkingLine,
)


class InvalidEmployeeConfig(ValueError):
    """Master data nhân viên hỏng — KHÔNG phải dữ liệu import xấu (DEC-132).

    §18 đặc tả cấm chặn toàn bộ import vì **dữ liệu xấu**; một dòng thô méo mó
    phải đi vào Review Queue chứ không được làm gãy lượt import. Master data
    hỏng nằm ở phía bên kia lằn ranh đó — cùng phía với một severity gõ sai
    trong `validation.yaml`, thứ vẫn luôn được phép raise. Đây là công cụ
    hỏng, không phải dữ liệu xấu, nên nó fail-fast trước khi import chạy.

    Lằn ranh này chạy theo đúng một chiều và không được nới: một **dòng giao
    dịch** hỏng KHÔNG bao giờ được biến thành config failure. Nó vào Review
    Queue, y như trước (HD-110-09).
    """


class ForeignRecordRef(ValueError):
    """Một `RecordRef` được dùng với master snapshot không sinh ra nó.

    Đây là lỗi lập trình, không phải lỗi dữ liệu, nên nó nổ to. Bản trước im
    lặng resolve theo index và trả về một nhân viên hoàn toàn khác — mà vì
    `employee_group` là một chiều tra tỉ lệ quy đổi, "một nhân viên khác" là
    "một tỉ lệ khác", tức là tiền.
    """


@dataclass(frozen=True)
class RecordRef:
    """Danh tính của MỘT bản ghi employee TRONG MỘT master snapshot (DEC-133).

    `snapshot_id` là phần mà Independent Review #6 chỉ ra là còn thiếu. Không
    có nó, `RecordRef(0, ...)` của master A và của master B **bằng nhau và
    cùng hash** — đo được tại `ed38fd6` — nên một dict khoá bằng `RecordRef`
    trộn được hai master mà không ai biết. Có nó, `__eq__` và `__hash__` tách
    hai bên ra, và `EmployeeMaster.record()` từ chối ref lạ thay vì resolve
    theo index.

    `label` CHỈ để render cho người đọc. Nó không bao giờ được dùng làm khoá
    tra cứu — làm vậy là quay đúng về danh tính theo giá trị đã bị loại bỏ.
    """

    snapshot_id: str
    index: int
    label: str


@dataclass(frozen=True)
class MappingResult:
    normalized: Optional[str]
    status: str
    default_lead_source: Optional[str]
    include_in_kpi: Optional[bool]
    group: Optional[str] = None
    # Record mà phép chọn đã dừng lại. `None` khi không khớp gì. Thêm vào ở
    # Review #5 và KHÔNG ảnh hưởng trường nghiệp vụ nào phía trên.
    record: Optional[RecordRef] = None


def _clean(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def validate_employee_records(rows: list[dict], groups: list = None) -> None:
    """Schema tối thiểu của master data nhân viên — HD-110-06, DEC-132.

    Đặt ở `mapping/` chứ không ở `config/loader.py`: loader tuyên bố ngay
    trong docstring rằng nó chỉ giữ cơ chế generic (đọc YAML, lọc theo ngày),
    còn ngữ nghĩa đặc thù domain thuộc về consumer của từng config. Quy tắc
    "một employee phải có prefix dùng được" là ngữ nghĩa domain.

    **Referential integrity (HD-110-09, DEC-133).** `employee.group` phải có
    trong `employee_groups`. Đây KHÔNG phải luật vệ sinh: `employee_group` là
    một chiều tra `conversion_rates.yaml`, nên một group gõ sai rơi khỏi dòng
    cụ thể và rớt xuống dòng `"*"`. Đo được: `NOI_THANH` → `NOI_THAN_2` rate
    **2.0%**, còn `NOI_THAN` (thiếu một chữ H) → `PERSONAL_5_5` rate **5.5%**.
    Một lỗi gõ dời tỉ lệ quy đổi 175%, im lặng, và tín hiệu duy nhất trước đây
    là một dòng ERROR trong hàng chờ *không chặn import*.

    DEC-129 §1 từng đặt việc này vào Review Queue (tiêu chí F1). DEC-133 **thu
    hẹp** phần đó dựa trên bằng chứng trên — bằng chứng chưa tồn tại khi
    DEC-129 được chốt. DEC-129 không bị sửa hay xoá; F1 vẫn tồn tại và vẫn
    chạy trên đường phân tích và test bypass validate.

    `raw_prefix` rỗng là ca nguy hiểm nhất và là lý do luật này tồn tại:
    `"".startswith` khớp **mọi** chuỗi, nên một prefix rỗng lặng lẽ biến thành
    catch-all và hút toàn bộ dòng lẽ ra `unmapped` về một người — tức là dời
    quyền sở hữu KPI vì một lỗi gõ. HD-110-06 bác bỏ ngữ nghĩa đó dứt khoát:
    prefix rỗng là cấu hình sai, không phải một tính năng.
    """
    for index, row in enumerate(rows):
        where = f"employees[{index}]"
        if not isinstance(row, dict):
            raise InvalidEmployeeConfig(f"{where}: phải là một mapping, gặp {type(row).__name__}")

        for field_name in ("raw_prefix", "normalized"):
            if field_name not in row:
                raise InvalidEmployeeConfig(f"{where}: thiếu `{field_name}` bắt buộc")
            if not _clean(row.get(field_name)):
                raise InvalidEmployeeConfig(
                    f"{where}: `{field_name}` rỗng hoặc chỉ có khoảng trắng "
                    f"({row.get(field_name)!r}). Prefix rỗng khớp mọi chuỗi và "
                    "sẽ nhận nhầm doanh số của người khác — HD-110-06 cấm."
                )

        if not _clean(row.get("group")):
            raise InvalidEmployeeConfig(
                f"{where}: thiếu `group` bắt buộc hoặc để rỗng"
            )

        if "active" not in row:
            raise InvalidEmployeeConfig(f"{where}: thiếu `active` bắt buộc")
        if not isinstance(row.get("active"), bool):
            raise InvalidEmployeeConfig(
                f"{where}: `active` phải là boolean, gặp "
                f"{row.get('active')!r}. Một chuỗi \"false\" là truthy trong "
                "Python và sẽ khiến một người đã nghỉ vẫn được tính active."
            )

    if groups is None:
        return

    declared = {str(g.get("code")) for g in groups if isinstance(g, dict) and g.get("code")}
    for index, row in enumerate(rows):
        group = _clean(row.get("group"))
        if group not in declared:
            raise InvalidEmployeeConfig(
                f"employees[{index}]: `group` {group!r} không có trong "
                f"`employee_groups` (đã khai: {sorted(declared)}). Group là một "
                "chiều tra tỉ lệ quy đổi — một group không tồn tại sẽ rơi xuống "
                "dòng `\"*\"` và đổi tỉ lệ trong im lặng (HD-110-09)."
            )


def _freeze(value: Any) -> Any:
    """Ép sâu sang cấu trúc bất biến (INVARIANT I).

    `frozen=True` chỉ cấm gán lại thuộc tính; nó không cấm sửa đối tượng mà
    thuộc tính trỏ tới. Một record là `dict` nên nếu giữ nguyên tham chiếu của
    caller thì master "bất biến" vẫn đổi được từ bên ngoài — và `snapshot_id`
    đã tính xong sẽ nói dối. Nên ở biên này ta **sao chép và đóng băng**, chứ
    không chỉ kiểm tra.
    """
    if isinstance(value, dict):
        return MappingProxyType({k: _freeze(v) for k, v in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(v) for v in value)
    return value


def _snapshot_id(records: tuple, groups: tuple) -> str:
    """Danh tính DẪN TỪ NỘI DUNG của master snapshot.

    Dẫn từ nội dung chứ không phải `id()` hay một số đếm, để "hai master này
    là cùng một master data" trở thành mệnh đề **chứng minh được**. Nhờ vậy
    `Validator.from_config_dir()` tự dựng mapper từ cùng file vẫn hợp lệ, và
    hai lần đọc một file không đổi bằng nhau một cách chính đáng.

    `sort_keys` + `default=str` để thứ tự khoá trong YAML và các kiểu ngày
    không làm id nhảy loạn giữa hai lần chạy.
    """
    payload = json.dumps(
        {"employees": records, "employee_groups": groups},
        sort_keys=True,
        ensure_ascii=False,
        default=str,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True)
class EmployeeMaster:
    """Master data nhân viên đã validate, bất biến, CÓ DANH TÍNH (DEC-133).

    Sở hữu **cả** `employees` lẫn `employee_groups`. Trước đây `Validator` đọc
    `employee_groups` bằng một lần `load_yaml` riêng kể cả khi đã được truyền
    mapper, nên hai nửa của một master có thể đến từ hai lần đọc khác nhau.
    Gộp chúng lại cũng chính là thứ cho referential integrity một cái nhà:
    `employee.group ∈ employee_groups` chỉ kiểm được khi một đối tượng biết cả
    hai (HD-110-09).
    """

    records: tuple[Mapping[str, Any], ...]
    groups: tuple[Mapping[str, Any], ...]
    snapshot_id: str
    refs: tuple[RecordRef, ...] = field(default_factory=tuple)

    @property
    def group_codes(self) -> frozenset:
        return frozenset(
            str(g.get("code")) for g in self.groups if g.get("code")
        )

    def record(self, ref: RecordRef) -> Mapping[str, Any]:
        """Đọc lại record theo danh tính — TỪ CHỐI ref của snapshot khác.

        Đây là điểm mà Review #6 M1 nổ ra: bản trước index thẳng vào list và
        trả về một nhân viên khác hẳn, im lặng.
        """
        if ref.snapshot_id != self.snapshot_id:
            raise ForeignRecordRef(
                f"RecordRef thuộc snapshot {ref.snapshot_id!r} nhưng đang được "
                f"đọc trên snapshot {self.snapshot_id!r}. Hai master data khác "
                "nhau; resolve theo index sẽ trả về một nhân viên khác, và vì "
                "`employee_group` là một chiều tra tỉ lệ, đó là một tỉ lệ khác."
            )
        return self.records[ref.index]

    def ref_for_index(self, index: int) -> RecordRef:
        return self.refs[index]


def load_employee_master(path: Path) -> EmployeeMaster:
    """Biên canonical DUY NHẤT để nạp master nhân viên (INVARIANT L, DEC-133).

    Mọi consumer đi qua đây. Trước Review #6 có sáu điểm nạp `employees.yaml`,
    ba trong số đó là `load_yaml` thô không validate gì — nên fail-fast không
    có điểm nghẽn và referential integrity không có nhà.
    """
    data = load_yaml(path)
    return build_employee_master(
        data.get("employees", []) or [], data.get("employee_groups", []) or []
    )


def build_employee_master(
    records: list, groups: list, validate: bool = True
) -> EmployeeMaster:
    """Dựng snapshot từ dữ liệu đã đọc sẵn.

    `validate=False` CHỈ dành cho test cần dựng cố ý master mâu thuẫn để quan
    sát hành vi hạ nguồn (ví dụ F6 cần một record `active: false` có dòng).
    Luồng production không bao giờ dùng nó.
    """
    if validate:
        validate_employee_records(records, groups)
    frozen_records = tuple(_freeze(r) for r in records)
    frozen_groups = tuple(_freeze(g) for g in groups)
    snapshot_id = _snapshot_id(frozen_records, frozen_groups)
    refs = tuple(
        RecordRef(snapshot_id=snapshot_id, index=i, label=_employee_label(r))
        for i, r in enumerate(frozen_records)
    )
    return EmployeeMaster(
        records=frozen_records,
        groups=frozen_groups,
        snapshot_id=snapshot_id,
        refs=refs,
    )


def _employee_label(record: dict) -> str:
    """Danh tính người đọc hành động được — chỉ riêng tên là không đủ khi hai
    record cố ý dùng chung tên trong một lượt bàn giao (DEC-121)."""
    starts = record.get("effective_from") or "—"
    ends = record.get("effective_to") or "—"
    return f"{_clean(record.get('normalized'))}[{_clean(record.get('raw_prefix'))}|{starts}..{ends}]"


class EmployeeMapper:
    """Đọc một `EmployeeMaster` bất biến; không sở hữu dữ liệu master.

    Mapper là *hành vi*, master là *dữ liệu có danh tính*. Tách ra như vậy thì
    "validation dùng đúng master đã enrich lines" kiểm được bằng cách so
    `snapshot_id`, thay vì tin vào quy ước (DEC-133).
    """

    def __init__(self, master: "EmployeeMaster"):
        if not isinstance(master, EmployeeMaster):
            raise TypeError(
                "EmployeeMapper nhận EmployeeMaster, không nhận list record "
                "thô. Dựng master qua `load_employee_master()` hoặc "
                "`build_employee_master()` để nó đi qua biên validate canonical "
                "(INVARIANT L)."
            )
        self._master = master

    @classmethod
    def from_yaml(cls, path: Path) -> "EmployeeMapper":
        return cls(load_employee_master(path))

    @property
    def master(self) -> "EmployeeMaster":
        return self._master

    @property
    def snapshot_id(self) -> str:
        return self._master.snapshot_id

    @property
    def _rows(self) -> tuple:
        return self._master.records

    @property
    def records(self) -> tuple:
        """Đúng snapshot mà mọi `RecordRef` chỉ vào — một không gian danh tính
        duy nhất, và nó mang cả `employee_groups`."""
        return self._master.records

    @property
    def refs(self) -> tuple[RecordRef, ...]:
        return self._master.refs

    def record(self, ref: RecordRef) -> Mapping[str, Any]:
        """Uỷ quyền cho master, nên kiểm tra sở hữu không thể bị đi vòng."""
        return self._master.record(ref)

    def ref_for_index(self, index: int) -> RecordRef:
        return self._master.ref_for_index(index)

    def candidate_records(
        self, employee_raw: Optional[str], as_of: Optional[date]
    ) -> tuple[RecordRef, ...]:
        """Mọi record đang hiệu lực khớp `employee_raw`, TRƯỚC khi tie-break.

        F3 hỏi hàm này thay vì tự dựng vòng khớp prefix riêng. Nhờ vậy "có
        nhiều hơn một record cùng hiệu lực tại thời điểm của dòng này" được trả
        lời bằng đúng ngữ nghĩa chuỗi mà production dùng để map — nếu
        production coi một chuỗi là `unmapped` thì validation không thể
        normalize theo cách riêng rồi kết luận ambiguity (HD-110-07/D3).
        """
        if not employee_raw:
            return ()
        if as_of:
            # So khớp theo ĐỊNH DANH ĐỐI TƯỢNG, không theo bằng nhau về giá
            # trị: `effective_rows` trả về chính các dict đã truyền vào, còn
            # hai record trùng nhau từng trường vẫn là hai record khác nhau
            # (đó là toàn bộ nội dung Finding 3). Dùng `in` ở đây sẽ gộp chúng
            # lại đúng theo cách vừa bị loại bỏ.
            effective = {id(row) for row in effective_rows(self._rows, as_of)}
            indexes = [
                index
                for index, row in enumerate(self._rows)
                if id(row) in effective
            ]
        else:
            indexes = list(range(len(self._rows)))
        return tuple(
            self.refs[index]
            for index in indexes
            if employee_raw.startswith(self._rows[index]["raw_prefix"])
        )

    def resolve_record(
        self, employee_raw: Optional[str], as_of: Optional[date]
    ) -> Optional[RecordRef]:
        """ĐÚNG record mà `resolve()` dừng lại — prefix dài nhất thắng.

        Đây là phép chọn record DUY NHẤT trong hệ thống. Validation gọi chính
        hàm này, nên không còn chỗ cho bản cài đặt thứ hai drift khỏi nó.
        """
        candidates = self.candidate_records(employee_raw, as_of)
        if not candidates:
            return None
        # Prefix cụ thể nhất thắng nếu nhiều hơn một dòng cấu hình cùng khớp.
        # `max` giữ phần tử đầu tiên khi hòa, y hệt hành vi trước đây.
        return max(candidates, key=lambda ref: len(self.record(ref)["raw_prefix"]))

    def resolve(
        self, employee_raw: Optional[str], as_of: Optional[date]
    ) -> MappingResult:
        ref = self.resolve_record(employee_raw, as_of)
        if ref is None:
            return MappingResult(None, MAPPING_STATUS_UNMAPPED, None, None)

        best = self.record(ref)
        status = MAPPING_STATUS_MAPPED if best.get("active", True) else MAPPING_STATUS_INACTIVE
        return MappingResult(
            normalized=best["normalized"],
            status=status,
            default_lead_source=best.get("default_lead_source"),
            include_in_kpi=best.get("include_in_kpi"),
            group=best.get("group"),
            record=ref,
        )

    def apply(self, lines: list[WorkingLine]) -> list[WorkingLine]:
        for line in lines:
            result = self.resolve(line.employee_raw, line.date)
            line.employee_normalized = result.normalized
            line.employee_mapping_status = result.status
            line.employee_group = result.group
        return lines
