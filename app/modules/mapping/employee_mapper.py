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
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Optional

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
    """


@dataclass(frozen=True)
class RecordRef:
    """Danh tính của MỘT bản ghi employee đã được load (DEC-132).

    `index` là vị trí trong đúng list mà mapper đang giữ — danh tính của **bản
    ghi**, không phải của một bộ giá trị. Đó là toàn bộ điểm mấu chốt:
    Independent Review #5 chứng minh hai record có thể trùng nhau ở
    `normalized` + `raw_prefix` + cửa sổ hiệu lực mà vẫn khác nhau ở `active`
    và `group`. Khóa theo giá trị gộp chúng làm một và phát F6 lên nhầm người;
    khóa theo vị trí thì va chạm là **bất khả**, không phải "khó xảy ra".

    `label` CHỈ để render cho người đọc. Nó không bao giờ được dùng làm khóa
    tra cứu — làm vậy là quay đúng về danh tính theo giá trị vừa bị loại bỏ.
    """

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


def validate_employee_records(rows: list[dict]) -> None:
    """Schema tối thiểu của master data nhân viên — HD-110-06, DEC-132.

    Đặt ở `mapping/` chứ không ở `config/loader.py`: loader tuyên bố ngay
    trong docstring rằng nó chỉ giữ cơ chế generic (đọc YAML, lọc theo ngày),
    còn ngữ nghĩa đặc thù domain thuộc về consumer của từng config. Quy tắc
    "một employee phải có prefix dùng được" là ngữ nghĩa domain.

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


def _employee_label(record: dict) -> str:
    """Danh tính người đọc hành động được — chỉ riêng tên là không đủ khi hai
    record cố ý dùng chung tên trong một lượt bàn giao (DEC-121)."""
    starts = record.get("effective_from") or "—"
    ends = record.get("effective_to") or "—"
    return f"{_clean(record.get('normalized'))}[{_clean(record.get('raw_prefix'))}|{starts}..{ends}]"


class EmployeeMapper:
    def __init__(self, rows: list[dict], validate: bool = True):
        """`validate=False` chỉ dành cho test dựng cố tình master data hỏng để
        quan sát hành vi hạ nguồn; luồng production luôn validate."""
        if validate:
            validate_employee_records(rows)
        self._rows = list(rows)
        self._refs = tuple(
            RecordRef(index=index, label=_employee_label(row))
            for index, row in enumerate(self._rows)
        )

    @classmethod
    def from_yaml(cls, path: Path) -> "EmployeeMapper":
        data = load_yaml(path)
        return cls(data.get("employees", []))

    @property
    def records(self) -> tuple[dict, ...]:
        """Đúng list mà mọi `RecordRef` chỉ vào — một không gian danh tính duy
        nhất. Validation đọc list NÀY, không load lại `employees.yaml` lần hai."""
        return tuple(self._rows)

    @property
    def refs(self) -> tuple[RecordRef, ...]:
        return self._refs

    def record(self, ref: RecordRef) -> dict:
        return self._rows[ref.index]

    def ref_for_index(self, index: int) -> RecordRef:
        return self._refs[index]

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
            self._refs[index]
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
        return max(candidates, key=lambda ref: len(self._rows[ref.index]["raw_prefix"]))

    def resolve(
        self, employee_raw: Optional[str], as_of: Optional[date]
    ) -> MappingResult:
        ref = self.resolve_record(employee_raw, as_of)
        if ref is None:
            return MappingResult(None, MAPPING_STATUS_UNMAPPED, None, None)

        best = self._rows[ref.index]
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
