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

from app.modules.config.loader import as_date, load_yaml
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


_SEAL = object()


class SealedConstruction(TypeError):
    """Một canonical object bị dựng ngoài factory đã parse (DEC-134, RC-1).

    Architecture Closure Audit chứng minh đây là root cause sâu nhất: biên
    canonical trước đây là một HÀM (`build_employee_master`), không phải một
    KIỂU. Giữ một `EmployeeMaster` vì thế **không chứng minh** nó đã validate,
    đã đóng băng hay đã được định danh — `EmployeeMaster(...)` công khai đi
    vòng qua cả ba, và đo được là nó chấp nhận prefix rỗng, group ma,
    `active="no"`, cùng dict thô sửa được từ bên ngoài.

    Với seal, **việc giữ được object chính là bằng chứng nó hợp lệ**. Một chỗ
    thì đi vòng được; một kiểu thì không.
    """


@dataclass(frozen=True)
class DateWindow:
    """Cửa sổ hiệu lực ĐÃ PARSE (DEC-121, RC-4).

    Parse, đừng validate: khi cửa sổ đã là hai `date` thật thì "ngày méo mó"
    không còn là điều kiện ai đó phải nhớ kiểm — nó là một phép parse thất bại
    tại biên master. Audit đo được bản trước chấp nhận `"hôm qua"`,
    `"2026-13-45"` và `20260101` lúc load rồi nổ `ValueError`/`TypeError`
    **giữa lúc xử lý giao dịch**.
    """

    start: date
    end: date

    def covers(self, when: date) -> bool:
        return self.start <= when <= self.end


@dataclass(frozen=True)
class EmployeeRecord:
    """Một bản ghi employee ĐÃ PARSE sang trạng thái hợp lệ.

    Mọi trường đã đúng kiểu; `window` đã parse và đã kiểm `start <= end`.
    Không consumer nào còn phải tự phòng thủ.

    `__getitem__`/`get` là **cùng một dữ liệu, hai cú pháp đọc** — không phải
    bản sao thứ hai. Chúng tồn tại để `reconcile_conversion.py` đọc được mà
    không phải viết lại logic đối chiếu đã freeze.
    """

    raw_prefix: str
    normalized: str
    group: str
    active: bool
    window: DateWindow
    default_lead_source: Optional[str]
    include_in_kpi: Optional[bool]
    _seal: Any = None

    def __post_init__(self) -> None:
        if self._seal is not _SEAL:
            raise SealedConstruction(
                "EmployeeRecord chỉ dựng được qua `parse_employee_record()`."
            )

    def __getitem__(self, key: str) -> Any:
        if key in ("raw_prefix", "normalized", "group", "active",
                   "default_lead_source", "include_in_kpi"):
            return getattr(self, key)
        if key == "effective_from":
            return self.window.start
        if key == "effective_to":
            return self.window.end
        raise KeyError(key)

    def get(self, key: str, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default


def _parse_date(value: Any, where: str, field_name: str) -> Optional[date]:
    try:
        return as_date(value)
    except (TypeError, ValueError) as exc:
        raise InvalidEmployeeConfig(
            f"{where}: `{field_name}` không phải một ngày hợp lệ ({value!r}) — {exc}"
        ) from exc


def parse_employee_record(row: Any, index: int, declared: frozenset) -> EmployeeRecord:
    """Biến một dòng YAML thô thành `EmployeeRecord` hợp lệ, hoặc raise.

    Đây là **toàn bộ** định nghĩa "master hợp lệ" của hệ thống. Không có danh
    sách điều kiện nào ở nơi khác: cái gì không parse được ở đây thì không tồn
    tại ở hạ nguồn.
    """
    where = f"employees[{index}]"
    if not isinstance(row, dict):
        raise InvalidEmployeeConfig(
            f"{where}: phải là một mapping, gặp {type(row).__name__}"
        )

    for field_name in ("raw_prefix", "normalized"):
        if field_name not in row:
            raise InvalidEmployeeConfig(f"{where}: thiếu `{field_name}` bắt buộc")
        value = row.get(field_name)
        if type(value) is not str:
            raise InvalidEmployeeConfig(
                f"{where}: `{field_name}` phải là chuỗi thuần, gặp "
                f"{type(value).__name__} ({value!r}). Một prefix không phải "
                "chuỗi sẽ nổ `startswith` giữa lúc xử lý giao dịch; một lớp con "
                "của `str` có thể đổi giá trị giữa hai lần đọc."
            )
        if not value.strip():
            raise InvalidEmployeeConfig(
                f"{where}: `{field_name}` rỗng hoặc chỉ có khoảng trắng "
                f"({value!r}). Prefix rỗng khớp mọi chuỗi và sẽ nhận nhầm "
                "doanh số của người khác — HD-110-06 cấm."
            )

    group = row.get("group")
    if type(group) is not str or not group.strip():
        raise InvalidEmployeeConfig(
            f"{where}: thiếu `group` bắt buộc hoặc không phải chuỗi ({group!r})"
        )
    if group not in declared:
        raise InvalidEmployeeConfig(
            f"{where}: `group` {group!r} không có trong `employee_groups` "
            f"(đã khai: {sorted(declared)}). Group là một chiều tra tỉ lệ quy "
            'đổi — một group không tồn tại sẽ rơi xuống dòng `"*"` và đổi tỉ lệ '
            "trong im lặng (HD-110-09)."
        )

    if "active" not in row:
        raise InvalidEmployeeConfig(f"{where}: thiếu `active` bắt buộc")
    if type(row.get("active")) is not bool:
        raise InvalidEmployeeConfig(
            f"{where}: `active` phải là boolean, gặp {row.get('active')!r}. "
            'Một chuỗi "false" là truthy trong Python và sẽ khiến một người đã '
            "nghỉ vẫn được tính active."
        )

    for optional, kinds in (("default_lead_source", (str,)), ("include_in_kpi", (bool,))):
        value = row.get(optional)
        if value is not None and type(value) not in kinds:
            raise InvalidEmployeeConfig(
                f"{where}: `{optional}` phải là {kinds[0].__name__} hoặc null, "
                f"gặp {type(value).__name__} ({value!r})"
            )

    starts = _parse_date(row.get("effective_from"), where, "effective_from") or date.min
    ends = _parse_date(row.get("effective_to"), where, "effective_to") or date.max
    if starts > ends:
        raise InvalidEmployeeConfig(
            f"{where}: cửa sổ hiệu lực bất khả — `effective_from` {starts} sau "
            f"`effective_to` {ends}. Bản ghi này không bao giờ khớp dòng nào, "
            "nên toàn bộ doanh số của người đó biến mất trong im lặng."
        )

    return EmployeeRecord(
        raw_prefix=str(row["raw_prefix"]),
        normalized=str(row["normalized"]),
        group=str(group),
        active=row["active"],
        window=DateWindow(starts, ends),
        default_lead_source=(
            None if row.get("default_lead_source") is None
            else str(row["default_lead_source"])
        ),
        include_in_kpi=row.get("include_in_kpi"),
        _seal=_SEAL,
    )


def parse_employee_master_rows(rows: list, groups: list):
    """Parse toàn bộ master + kiểm các bất biến CHỈ thấy được ở cấp tập hợp."""
    declared = frozenset(
        g.get("code")
        for g in (groups or [])
        if isinstance(g, dict) and type(g.get("code")) is str and g.get("code")
    )
    parsed = tuple(
        parse_employee_record(row, index, declared)
        for index, row in enumerate(rows or [])
    )

    # `raw_prefix` TRÙNG KHÍT giữa hai employee KHÁC NHAU (HD-110-15).
    # `resolve` chọn bản ghi đầu tiên, nên người còn lại mất toàn bộ doanh số
    # mà không có tín hiệu nào — cùng lớp lỗi với group gõ sai ở HD-110-09.
    # Prefix LỒNG NHAU vẫn hợp lệ: `"Vũ Hạnh"` và `"Vũ Hạnh Ly"` là hai người
    # thật, và luật "prefix dài nhất thắng" phân biệt được họ.
    # Chỉ cấm khi CỬA SỔ HIỆU LỰC CHỒNG NHAU. Đó đúng là tình huống gây hại mà
    # HD-110-15 nhắm tới: `resolve` chọn bản ghi đầu tiên, nên người còn lại
    # mất toàn bộ doanh số trong im lặng.
    #
    # Cùng prefix với cửa sổ RỜI NHAU **không** phải lỗi — đó chính là cách
    # DEC-121 diễn đạt một lượt BÀN GIAO: đóng dòng cũ bằng `effective_to`, mở
    # dòng mới bằng `effective_from`. Cấm nó sẽ phá một quy tắc nghiệp vụ
    # canonical, và không có dòng nào bị mất vì bộ lọc hiệu lực phân biệt được
    # hai bản ghi theo ngày của chính dòng đó.
    for index, record in enumerate(parsed):
        for earlier in range(index):
            other = parsed[earlier]
            if record.raw_prefix != other.raw_prefix:
                continue
            if record.window.start > other.window.end or other.window.start > record.window.end:
                continue  # bàn giao (DEC-121) — hợp lệ
            raise InvalidEmployeeConfig(
                f"employees[{index}]: `raw_prefix` {record.raw_prefix!r} trùng "
                f"khít với employees[{earlier}] ({other.normalized!r}) và hai "
                "cửa sổ hiệu lực CHỒNG NHAU. Chỉ một trong hai từng khớp được "
                "dòng nào; người kia mất toàn bộ doanh số trong im lặng "
                "(HD-110-15). Prefix LỒNG NHAU, và cùng prefix với cửa sổ RỜI "
                "NHAU (bàn giao, DEC-121), vẫn hợp lệ."
            )

    return parsed, declared


def _snapshot_payload(records: tuple, groups: frozenset) -> str:
    """Nội dung LOGIC của master, chuẩn hoá — nền của danh tính dẫn xuất."""
    return json.dumps(
        {
            "employees": [
                [r.raw_prefix, r.normalized, r.group, r.active,
                 r.window.start.isoformat(), r.window.end.isoformat(),
                 r.default_lead_source, r.include_in_kpi]
                for r in records
            ],
            "employee_groups": sorted(groups),
        },
        ensure_ascii=False,
    )


@dataclass(frozen=True)
class EmployeeMaster:
    """Master nhân viên: VALIDATED + DEEP IMMUTABLE + IDENTIFIED + SEALED.

    Bốn tính chất đó nay là **một**: chỉ `_build_master()` dựng được object
    này, và nó chỉ dựng từ `EmployeeRecord` đã parse. Giữ được một
    `EmployeeMaster` chính là bằng chứng cả bốn đều đúng — không còn "một hàm
    nào đó lẽ ra đã kiểm" (RC-1).

    **Bất biến sâu là hệ quả, không phải một bước riêng.** `records` là tuple
    các `EmployeeRecord` frozen, mọi trường vô hướng đã parse — không còn dict
    thô nào để alias từ bên ngoài, nên `_freeze()` thủ công biến mất cùng với
    lớp lỗi của nó.

    `snapshot_id` là **property dẫn xuất**, không còn là field: khi nó là
    field, caller đặt được giá trị tuỳ ý và phép so của `Validator` bị qua mặt
    bằng cách dựng master nội dung B mang id của A.
    """

    records: tuple
    group_codes: frozenset
    _seal: Any = None

    def __post_init__(self) -> None:
        if self._seal is not _SEAL:
            raise SealedConstruction(
                "EmployeeMaster chỉ dựng được qua `load_employee_master()` hoặc "
                "`build_employee_master()`. Dựng trực tiếp sẽ đi vòng qua parse, "
                "đóng băng và định danh — đó là RC-1 của Architecture Closure Audit."
            )

    @property
    def snapshot_id(self) -> str:
        """Dẫn từ NỘI DUNG LOGIC, nên 'hai master là cùng một master data' là
        mệnh đề chứng minh được — và không ai đặt được nó bằng tay."""
        return hashlib.sha256(
            _snapshot_payload(self.records, self.group_codes).encode("utf-8")
        ).hexdigest()[:16]

    @property
    def refs(self) -> tuple:
        snapshot_id = self.snapshot_id
        return tuple(
            RecordRef(snapshot_id=snapshot_id, index=i, label=_employee_label(r))
            for i, r in enumerate(self.records)
        )

    def record(self, ref: RecordRef) -> EmployeeRecord:
        """Đọc lại record theo danh tính — TỪ CHỐI ref của snapshot khác."""
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

    def effective(self, as_of: Optional[date]) -> tuple:
        """Chỉ số các record đang hiệu lực tại `as_of`.

        Nguồn sự thật DUY NHẤT cho effective-dating của employee (T7): trước
        đây quy tắc này có ba bản cài đặt (`effective_rows`, `_overlaps`, và
        vòng riêng của script).
        """
        if as_of is None:
            return tuple(range(len(self.records)))
        return tuple(
            i for i, r in enumerate(self.records) if r.window.covers(as_of)
        )


def _build_master(records: list, groups: list) -> EmployeeMaster:
    parsed, declared = parse_employee_master_rows(records, groups)
    return EmployeeMaster(records=parsed, group_codes=declared, _seal=_SEAL)


def load_employee_master(path: Path) -> EmployeeMaster:
    """Biên canonical DUY NHẤT để nạp master nhân viên (INVARIANT L)."""
    data = load_yaml(path)
    return _build_master(
        data.get("employees", []) or [], data.get("employee_groups", []) or []
    )


def build_employee_master(records: list, groups: list) -> EmployeeMaster:
    """Dựng snapshot từ dữ liệu đã đọc sẵn — luôn parse, không có cửa tắt.

    Tham số `validate=False` đã bị **XOÁ** (RC-1): nó là một bypass production
    tồn tại chỉ để phục vụ test. Test cần master mâu thuẫn thì dựng nó bằng
    dữ liệu hợp lệ nhưng mâu thuẫn về nghiệp vụ (ví dụ `active: false` mà vẫn
    có dòng), chứ không bằng cách tắt phép parse.
    """
    return _build_master(records, groups)


def _employee_label(record: EmployeeRecord) -> str:
    """Danh tính người đọc hành động được — chỉ riêng tên là không đủ khi hai
    record cố ý dùng chung tên trong một lượt bàn giao (DEC-121).

    CHỈ để render cho người đọc. Không bao giờ là khoá tra cứu.
    """
    starts = "—" if record.window.start == date.min else record.window.start.isoformat()
    ends = "—" if record.window.end == date.max else record.window.end.isoformat()
    return f"{record.normalized}[{record.raw_prefix}|{starts}..{ends}]"


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

    def record(self, ref: RecordRef) -> EmployeeRecord:
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
        refs = self.refs
        return tuple(
            refs[index]
            for index in self._master.effective(as_of)
            if employee_raw.startswith(self._master.records[index].raw_prefix)
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
        return max(candidates, key=lambda ref: len(self.record(ref).raw_prefix))

    def resolve(
        self, employee_raw: Optional[str], as_of: Optional[date]
    ) -> MappingResult:
        ref = self.resolve_record(employee_raw, as_of)
        if ref is None:
            return MappingResult(None, MAPPING_STATUS_UNMAPPED, None, None)

        best = self.record(ref)
        status = MAPPING_STATUS_MAPPED if best.active else MAPPING_STATUS_INACTIVE
        return MappingResult(
            normalized=best.normalized,
            status=status,
            default_lead_source=best.default_lead_source,
            include_in_kpi=best.include_in_kpi,
            group=best.group,
            record=ref,
        )

    def apply(self, lines: list[WorkingLine]) -> list[WorkingLine]:
        for line in lines:
            result = self.resolve(line.employee_raw, line.date)
            line.employee_normalized = result.normalized
            line.employee_mapping_status = result.status
            line.employee_group = result.group
        return lines
