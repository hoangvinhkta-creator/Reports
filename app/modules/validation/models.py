"""Review Queue data model — mục §18 đặc tả, TASK-110.

Pure dataclasses, no I/O (ADR-101). A `ReviewItem` is a *finding about* data,
never a copy of it: it carries the back-reference needed to locate what it is
about, and nothing that identifies a customer.
`governance/core/04_SECURITY_RULES.md` §6 makes purchase price and margin
sensitive; `governance/product/17_DATA_GOVERNANCE_PRIVACY.md` makes customer
name/phone/address sensitive. A review queue that leaked either would be a new
exposure surface built by the very task meant to add safety (CHECK-110-17).

**Every item must be traceable.** Independent Review #1 Finding 1 found items
with no back-reference at all — a queue line nobody can act on is only
marginally better than silence. `scope` now makes the required reference
explicit and `__post_init__` enforces it, so an untraceable item cannot be
constructed at all:

    SCOPE_ROW    one raw row      -> `source_file` + `source_row` required
    SCOPE_ORDER  one OrderID      -> `source_file` + `order_id` required
    SCOPE_BATCH  the whole import -> `source_file` required

The queue is built in memory and returned alongside the processed data. It is
never persisted here — storage is TASK-201, audit trail TASK-202, the screen
TASK-305.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from types import MappingProxyType
from typing import Any, Mapping, Optional

# Severity is a READING ORDER label, not a gate. §18 đặc tả: "Không block toàn
# bộ import." `ERROR` means "read this first", never "stop" — CHECK-110-02
# pins that an import whose every row is flagged still returns full results.
SEVERITY_INFO = "INFO"
SEVERITY_WARNING = "WARNING"
SEVERITY_ERROR = "ERROR"
SEVERITIES = (SEVERITY_INFO, SEVERITY_WARNING, SEVERITY_ERROR)

_SEVERITY_ORDER = {SEVERITY_ERROR: 0, SEVERITY_WARNING: 1, SEVERITY_INFO: 2}

# What a finding is about, and therefore what reference it must carry.
SCOPE_ROW = "row"
SCOPE_ORDER = "order"
SCOPE_BATCH = "batch"
SCOPES = (SCOPE_ROW, SCOPE_ORDER, SCOPE_BATCH)

# The eight category codes of the frozen scope table. Seven *loại* in §18
# terms — `Missing` appears twice because DEC-128 §1 splits it by shape: the
# per-row fields stay per-row, the Pending purchase price collapses into one
# aggregate item.
CATEGORY_MISSING = "Missing"
CATEGORY_MISSING_PURCHASE_PRICE = "Missing.PurchasePrice"
CATEGORY_SUSPICIOUS = "Suspicious"
CATEGORY_SUSPICIOUS_ERP = "Suspicious.ERP"
CATEGORY_ORDER_INCONSISTENCY = "OrderInconsistency"
CATEGORY_SOURCE_CLASSIFICATION = "SourceClassification"
CATEGORY_DUPLICATE = "Duplicate"
CATEGORY_EMPLOYEE_MAPPING = "EmployeeMapping"

CATEGORIES = (
    CATEGORY_MISSING,
    CATEGORY_MISSING_PURCHASE_PRICE,
    CATEGORY_SUSPICIOUS,
    CATEGORY_SUSPICIOUS_ERP,
    CATEGORY_ORDER_INCONSISTENCY,
    CATEGORY_SOURCE_CLASSIFICATION,
    CATEGORY_DUPLICATE,
    CATEGORY_EMPLOYEE_MAPPING,
)

# Provenance keys for `CATEGORY_ORDER_INCONSISTENCY`, required verbatim by the
# project owner when freezing the gate. A multi-employee order is NOT resolved
# here — ownership stays an open business decision — so the finding has to
# carry everything a later decision would need:
#
#   employees_found  every distinct selling identity seen on the order
#   legacy_selected  who `order_builder` currently picks (first line's value),
#                    recorded as LEGACY BEHAVIOUR, not as verified ownership
#   source_rows      the raw rows those identities came from
DETAIL_EMPLOYEES_FOUND = "employees_found"
DETAIL_LEGACY_SELECTED = "legacy_selected"
DETAIL_SOURCE_ROWS = "source_rows"
DETAIL_DATES_FOUND = "dates_found"
DETAIL_ROW_HASH = "row_hash"
DETAIL_RULE = "rule"

# Provenance keys for `CATEGORY_EMPLOYEE_MAPPING` (F1–F6). Added by Independent
# Review #1 Finding 1: an F4 that cannot name the rows it is about leaves a
# reader with nothing to open.
DETAIL_CRITERION = "criterion"
DETAIL_EMPLOYEE = "employee"
DETAIL_RAW_VALUE = "raw_value"
DETAIL_RAW_PREFIX = "raw_prefix"
DETAIL_DECLARED_GROUP = "declared_group"
DETAIL_DATASET_RANGE = "dataset_range"
DETAIL_BATCH_ROWS = "batch_rows"

# Added by Independent Review #3.
#
# `raw_variants` (Finding 3): canonical normalization is right for grouping, but
# an audit trail that only keeps the canonical form has destroyed evidence —
# two spellings that normalize alike are still two different things somebody
# typed. The queue keeps every original verbatim, with its own rows.
#
# `ambiguous_rows` / `conflicting_records` (Finding 1): F3 is decided per raw
# row, against that row's own date, so its provenance has to be per row too.
DETAIL_RAW_VARIANTS = "raw_variants"
DETAIL_AMBIGUOUS_ROWS = "ambiguous_rows"
DETAIL_CONFLICTING_RECORDS = "conflicting_records"

# Các khóa MANG THÔNG TIN DÒNG. Chúng thuộc quyền sở hữu của `RowProvenance`
# và do chính `ReviewItem` render ra; không caller nào được phép tự ghi chúng
# (DEC-132, điểm 12). Independent Review #5 chứng minh vì sao: `details` là
# một dict tùy ý, nên một finding về dòng 6 vẫn kèm được `ambiguous_rows` nói
# về dòng 7, và `ReviewItem` sao chép nguyên trạng. Đóng băng dataclass không
# cứu được — `frozen=True` chỉ đóng băng tham chiếu tới dict, không đóng băng
# nội dung nó.
ROW_BEARING_DETAIL_KEYS = frozenset(
    {
        "source_rows",
        "raw_variants",
        "ambiguous_rows",
        "conflicting_records",
    }
)


# `SealedConstruction` được re-export ở đây cho các import cũ. Cơ chế thật
# nằm ở `app/modules/domain/canonical.py`; Repair R1 đã xoá field `_seal` khỏi
# mọi canonical type vì field thì đọc lại, sao chép và truyền vào được.
from app.modules.domain.canonical import (  # noqa: E402,F401  (re-export)
    CanonicalSubclassRejected,
    SealedConstruction,
    canonical,
    factory_for,
    as_exact_date,
    as_exact_str,
)


@canonical(sealed=True)
@dataclass(frozen=True, slots=True)
class AffectedRow:
    """Một dòng thô mà finding thực sự nói về.

    Đơn vị provenance duy nhất trong toàn hệ thống. `raw_original` là danh
    tính đúng như đã gõ — dạng canonical dùng để gom nhóm, còn bản gốc mới là
    thứ người soát cần nhìn thấy.

    **SEALED (RC-1).** Audit chứng minh bản trước dựng được
    `AffectedRow("KHONG_TON_TAI.xlsx", 99999, "Bịa", None)` — nghĩa là
    provenance không buộc phải đến từ dữ liệu thật, và một `ReviewItem` có thể
    "truy vết" về một dòng chưa từng tồn tại. Nay chỉ `from_line()` dựng được,
    nên mọi provenance đều dẫn từ một `RawRow` có thật.
    """

    source_file: Optional[str]
    source_row: int
    raw_original: str = ""
    when: Optional[date] = None

    def __post_init__(self) -> None:
        # LỚP 1 (R1). Không còn `_seal` để kiểm: cổng dựng nằm ở `__new__` và
        # KHÔNG phải một field, nên `dataclasses.replace(row, source_row=99999)`
        # không mượn được nó nữa. Chỗ này chỉ còn luật giá trị.
        if type(self.source_row) is not int:
            raise TypeError(
                f"source_row phải là int thuần, gặp {self.source_row!r}."
            )
        if self.source_file is not None:
            object.__setattr__(self, "source_file", as_exact_str(self.source_file))
        object.__setattr__(self, "raw_original", as_exact_str(self.raw_original))
        if self.when is not None:
            object.__setattr__(
                self, "when", as_exact_date(self.when, "AffectedRow.when")
            )

    @classmethod
    def from_line(cls, line) -> "AffectedRow":
        """Đường DUY NHẤT tạo provenance: từ một `WorkingLine` thật.

        Mọi thuộc tính của `line` được đọc XONG trước khi permit mở, nên một
        `line` giả mạo không lợi dụng được cửa sổ dựng của materialiser.
        """
        return _materialise_affected_row(
            source_file=line.raw.source_file,
            source_row=line.raw.source_row,
            raw_original=line.employee_raw or "",
            when=line.date,
        )


@canonical(sealed=True)
@dataclass(frozen=True, slots=True)
class AmbiguousRow(AffectedRow):
    """Một dòng thô thực sự ambiguous, kèm lý do.

    F3 được chấm theo **ngày của chính dòng đó** (DEC-121 — hai prefix chỉ
    từng tồn tại ở các kỳ rời nhau là một lượt bàn giao, không phải xung đột).
    Ghi ambiguity theo raw *value* vì thế bôi đen cả những dòng chỉ có đúng
    một record hiệu lực. Mọi thứ người soát cần để chấm lại đều nằm đây.
    """

    raw_value: str = ""
    records: tuple = ()

    def __post_init__(self) -> None:
        # Gọi TƯỜNG MINH, không dùng `super()` không tham số: `slots=True` làm
        # `@dataclass` TẠO LẠI class, còn cell `__class__` mà `super()` đọc vẫn
        # trỏ vào class cũ. Đây là hệ quả đã biết của `slots=True`, không phải
        # lựa chọn phong cách.
        AffectedRow.__post_init__(self)
        object.__setattr__(self, "raw_value", as_exact_str(self.raw_value))
        # ÉP SANG TUPLE + SAO CHÉP (INVARIANT C). Truyền một list vào `records`
        # rồi sửa list đó từ bên ngoài từng làm đổi chuỗi `conflicting_records`
        # đã "dẫn xuất". Dẫn xuất từ dữ liệu mutable thì không phải dẫn xuất.
        object.__setattr__(self, "records", tuple(str(r) for r in self.records))

    @classmethod
    def from_line(cls, line, raw_value: str, records) -> "AmbiguousRow":
        return _materialise_ambiguous_row(
            source_file=line.raw.source_file,
            source_row=line.raw.source_row,
            raw_original=line.employee_raw or "",
            when=line.date,
            raw_value=raw_value,
            records=tuple(records),
        )

    def render(self) -> str:
        stamp = self.when.isoformat() if self.when else "không có ngày"
        return f"dòng {self.source_row} ({stamp}) → {', '.join(self.records)}"


@canonical(sealed=True)
@dataclass(frozen=True, slots=True)
class RowProvenance:
    """Tập dòng canonical của một finding, cùng MỌI representation của nó.

    Đây là câu trả lời cấu trúc cho Independent Review #5. Trước đây
    `affected_count` là một field gán tay còn `source_rows` là một chuỗi nối
    tay ở chỗ khác, nên hai bên bất đồng được. Ở đây chúng là property dẫn
    xuất từ đúng một tuple: trạng thái "count nói X, rows nói Y" không còn
    biểu diễn được bằng bất kỳ cách gọi nào.

    `batch_scoped` chỉ đổi CÁCH RENDER, không đổi phép đếm: F5 ("không map
    được gì cả") là phát biểu về cả lô, và in ra 14.000 số dòng sẽ chôn mất
    câu duy nhất đáng đọc. Số đếm vẫn chính xác.
    """

    rows: tuple = ()
    batch_scoped: bool = False

    def __post_init__(self) -> None:
        # Review #6 P3: truyền một list vào `rows` rồi append vào list đó làm
        # `affected_count` nhảy từ 1 lên 2 SAU khi item đã dựng xong.
        # `frozen=True` chỉ cấm gán lại thuộc tính, không cấm sửa đối tượng nó
        # trỏ tới — nên ở biên phải SAO CHÉP, không chỉ kiểm tra.
        object.__setattr__(self, "rows", tuple(self.rows))
        for row in self.rows:
            if not isinstance(row, AffectedRow):
                raise TypeError(
                    f"provenance chỉ nhận AffectedRow, gặp {type(row).__name__}"
                )
        # `batch_scoped` chỉ đổi CÁCH RENDER, nhưng nó quyết định `source_row`
        # trả `None` hay một số dòng thật, nên một giá trị truthy không phải
        # bool là một câu trả lời mơ hồ cho một câu hỏi nhị phân (R1).
        if type(self.batch_scoped) is not bool:
            raise TypeError(
                f"`batch_scoped` phải là bool thuần, gặp "
                f"{type(self.batch_scoped).__name__} ({self.batch_scoped!r})."
            )

    @classmethod
    def of(cls, rows=(), batch_scoped: bool = False) -> "RowProvenance":
        return _materialise_provenance(
            rows=tuple(rows), batch_scoped=batch_scoped
        )

    @classmethod
    def batch(cls, rows=()) -> "RowProvenance":
        return cls.of(rows, batch_scoped=True)

    @property
    def affected_count(self) -> int:
        """Dẫn xuất, không bao giờ được gán. `0` là một câu trả lời thật:
        tiêu chí F2 nghĩa là "không khớp dòng nào"."""
        return len(self.rows)

    @property
    def source_rows(self) -> tuple[int, ...]:
        return tuple(sorted(row.source_row for row in self.rows))

    @property
    def source_file(self) -> Optional[str]:
        for row in self.rows:
            if row.source_file:
                return row.source_file
        return None

    @property
    def primary_row(self) -> Optional[int]:
        rows = self.source_rows
        return rows[0] if rows else None

    def raw_variants(self) -> dict[str, list[int]]:
        """Mọi cách gõ gốc **bên trong finding này**, kèm dòng của chính nó."""
        variants: dict[str, list[int]] = {}
        for row in self.rows:
            if row.raw_original:
                variants.setdefault(row.raw_original, []).append(row.source_row)
        return {key: sorted(value) for key, value in variants.items()}

    def render_variants(self) -> str:
        """`!r` có chủ đích: một khoảng trắng đôi hay một cách dựng NFD là vô
        hình khi in thường, mà đó đúng là khác biệt cần giữ lại."""
        return " ; ".join(
            f"{original!r} → {', '.join(str(r) for r in rows)}"
            for original, rows in sorted(
                self.raw_variants().items(), key=lambda kv: (min(kv[1]), kv[0])
            )
        )

    def rendered_details(self) -> dict[str, str]:
        """Các khóa mang thông tin dòng, render TỪ CHÍNH tuple này.

        Đây là con đường duy nhất để một số dòng đi vào `ReviewItem.details`.
        """
        if self.batch_scoped or not self.rows:
            return {}
        rendered = {"source_rows": ", ".join(str(row) for row in self.source_rows)}
        variants = self.render_variants()
        if variants:
            rendered["raw_variants"] = variants

        # Provenance của F3 cũng DẪN XUẤT, không phải một dict truyền tay:
        # trước đây `ambiguous_rows` / `conflicting_records` được tính ở
        # `evaluate_raw_mapping` rồi sao chép qua `details`, và chính đó là
        # đường thoát mà Independent Review #5 chỉ ra.
        ambiguous = [row for row in self.rows if isinstance(row, AmbiguousRow)]
        if ambiguous:
            rendered["ambiguous_rows"] = " ; ".join(
                row.render() for row in sorted(ambiguous, key=lambda r: r.source_row)
            )
            rendered["conflicting_records"] = ", ".join(
                sorted({label for row in ambiguous for label in row.records})
            )
        return rendered


# ─────────────────────────────────────────── Materialiser (Lớp 2, R1)
#
# Mỗi sealed canonical type có ĐÚNG MỘT materialiser, thân chỉ có lời gọi
# constructor. Permit vì thế mở trong cửa sổ hẹp nhất có thể: mọi việc đọc dữ
# liệu của caller (`line.raw.source_file`, `tuple(rows)`, ...) đã xong trước
# khi permit mở, nên một đối tượng caller giả mạo không lợi dụng được nó.
#
# `factory_for` từ chối đăng ký nếu hàm không nằm trong chính module này, nên
# không có cách nào "thêm một factory" từ bên ngoài.


@factory_for(AffectedRow)
def _materialise_affected_row(**values: Any) -> AffectedRow:
    return AffectedRow(**values)


@factory_for(AmbiguousRow)
def _materialise_ambiguous_row(**values: Any) -> AmbiguousRow:
    return AmbiguousRow(**values)


@factory_for(RowProvenance)
def _materialise_provenance(**values: Any) -> RowProvenance:
    return RowProvenance(**values)


@canonical()
@dataclass(frozen=True, slots=True)
class Diagnostics:
    """Metadata chẩn đoán CÓ KIỂU — thay cho `dict[str, str]` tuỳ ý (DEC-133).

    Independent Review #6 Finding 1 chứng minh rằng đổi tên `details` thành
    `diagnostics` rồi gắn một denylist bốn khoá không đóng được kênh: đo được
    tại `ed38fd6`, một khoá ngoài danh sách (`cac_dong_lien_quan`) đi thẳng
    vào `details`, và sửa chính dict của caller SAU khi `__post_init__` đã
    chạy cũng đi thẳng vào `details`.

    Cách đóng không phải là danh sách dài hơn, mà là **không còn chỗ để đặt
    khoá**. Ở đây mọi trường đều có tên và có kiểu vô hướng. Thêm một trường
    là sửa dataclass và lọt vào code review; thêm một khoá dict thì không ai
    thấy. Và không trường nào trong đây có thể diễn đạt một tham chiếu dòng —
    đó là việc của `RowProvenance`.
    """

    criterion: Optional[str] = None
    employee: Optional[str] = None
    raw_value: Optional[str] = None
    raw_prefix: Optional[str] = None
    rule: Optional[str] = None
    row_hash: Optional[str] = None
    employees_found: tuple = ()
    legacy_selected: Optional[str] = None
    dates_found: tuple = ()
    dataset_range: Optional[str] = None
    batch_rows: Optional[int] = None
    # Tham số của renderer — có kiểu, và KHÔNG cái nào diễn đạt được một tham
    # chiếu dòng. Số dòng luôn đọc từ `RowProvenance` (RC-3).
    order_id: Optional[str] = None
    f2_reason: Optional[str] = None
    window_start: Optional[str] = None
    window_end: Optional[str] = None
    matched_employees: tuple = ()
    smallest_employee: Optional[str] = None
    smallest_count: Optional[int] = None
    manual_value: Optional[str] = None
    auto_value: Optional[str] = None
    observed_value: Optional[str] = None

    def __post_init__(self) -> None:
        # `str(...)` bắt buộc, không chỉ ép tuple: một lớp con của `str` với
        # `__str__` đổi theo lần gọi qua được mọi `isinstance` và làm `details`
        # trả giá trị khác nhau giữa hai lần đọc (Audit P4).
        for name in ("criterion", "employee", "raw_value", "raw_prefix", "rule",
                     "row_hash", "legacy_selected", "dataset_range", "order_id",
                     "f2_reason", "window_start", "window_end",
                     "smallest_employee", "manual_value", "auto_value",
                     "observed_value"):
            value = getattr(self, name)
            if value is not None and type(value) is not str:
                object.__setattr__(self, name, str(value))
        for name in ("employees_found", "dates_found", "matched_employees"):
            object.__setattr__(self, name, tuple(str(v) for v in getattr(self, name)))
        for name in ("smallest_count", "batch_rows"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, int(value))

    def rendered(self) -> dict[str, str]:
        """Projection lúc render. KHÔNG được lưu ở đâu cả."""
        out: dict[str, str] = {}
        for name, value in (
            (DETAIL_CRITERION, self.criterion),
            (DETAIL_EMPLOYEE, self.employee),
            (DETAIL_RAW_VALUE, self.raw_value),
            (DETAIL_RAW_PREFIX, self.raw_prefix),
            (DETAIL_RULE, self.rule),
            (DETAIL_ROW_HASH, self.row_hash),
            (DETAIL_LEGACY_SELECTED, self.legacy_selected),
            (DETAIL_DATASET_RANGE, self.dataset_range),
        ):
            if value is not None:
                out[name] = str(value)
        if self.employees_found:
            out[DETAIL_EMPLOYEES_FOUND] = " | ".join(self.employees_found)
        if self.dates_found:
            out[DETAIL_DATES_FOUND] = ", ".join(self.dates_found)
        if self.batch_rows is not None:
            out[DETAIL_BATCH_ROWS] = str(self.batch_rows)
        return out


# Never allowed inside a `ReviewItem`. Kept as data so the guard is one list
# rather than a habit somebody has to remember (CHECK-110-17).
PII_FIELD_NAMES = ("customer", "customer_code", "phone", "address")


@canonical()
@dataclass(frozen=True, slots=True)
class ReviewItem:
    """Một finding.

    **`ReviewItem` KHÔNG lưu `dict[str, str]` nào** (DEC-133, INVARIANT P).
    `message` và `details` là **projection thuần** tính từ (payload có kiểu,
    provenance của chính item) — không có đầu vào nào khác. Nên một chuỗi nêu
    dòng 7 là bất khả trừ khi dòng 7 nằm trong provenance của item: renderer
    không có cách nào biết tới dòng 7.

    Đó là điểm khác biệt so với Repair #1, vốn vẫn giữ một `dict[str, str]`
    lưu trữ được và cố canh nó bằng một denylist bốn khoá. Review #6 đi vòng
    qua denylist đó bằng ba cách độc lập: sửa dict của caller sau khi
    `__post_init__` đã chạy, dùng một khoá không có trong danh sách, và
    trường hợp batch-scoped nơi phép "provenance đè lên" không chạy.

    `affected_count` có thể hợp lệ bằng **0** — tiêu chí F2 đúng nghĩa là "một
    nhân viên đã cấu hình mà không khớp dòng nào", và báo 1 giả ở đó là khai
    man đúng cái sự thật duy nhất mà finding mang.

    **`message` KHÔNG còn là tham số constructor** (DEC-134, RC-2). Audit đo
    được bản trước dựng được một item sở hữu dòng 6 mà message khẳng định dòng
    7777. Review Queue là sản phẩm cho con người duyệt, nên một message sai
    dòng vẫn là provenance sai đối với người duyệt.
    """

    category: str
    severity: str
    scope: str = SCOPE_ROW
    provenance: RowProvenance = field(default_factory=RowProvenance.of)
    # Chỉ dùng khi provenance KHÔNG có dòng nào (F2, hoặc một finding về cả
    # lô): không có dòng thì không suy ra được tên file. Khi đã có dòng, đặt
    # trường này là lỗi — đó sẽ là kênh thứ hai để bất đồng với provenance.
    batch_source_file: Optional[str] = None
    order_id: Optional[str] = None
    diagnostics: Diagnostics = field(default_factory=Diagnostics)

    @property
    def message(self) -> str:
        """**Dẫn xuất, không phải tham số** (RC-2).

        Renderer chỉ nhận `(diagnostics, provenance)` — nó không có đầu vào nào
        khác, nên không thể nêu một dòng ngoài provenance của chính item này.
        Không blacklist từ khoá, không regex: trạng thái sai đơn giản là không
        biểu diễn được.
        """
        from app.modules.validation.renderer import render_message

        return render_message(self.category, self.diagnostics, self.provenance)

    @property
    def source_file(self) -> Optional[str]:
        return self.provenance.source_file or self.batch_source_file

    @property
    def source_row(self) -> Optional[int]:
        """Dẫn xuất. Một item phạm vi dòng trỏ vào dòng nhỏ nhất mà nó SỞ HỮU."""
        if self.provenance.batch_scoped:
            return None
        return self.provenance.primary_row

    @property
    def affected_count(self) -> int:
        return self.provenance.affected_count

    @property
    def details(self) -> Mapping[str, str]:
        """Projection lúc đọc, KHÔNG phải trạng thái được lưu.

        Trả `MappingProxyType`: người gọi có sửa cũng không ảnh hưởng gì tới
        item, và mỗi lần đọc lại được tính lại từ dữ liệu có kiểu.
        """
        merged = self.diagnostics.rendered()
        merged.update(self.provenance.rendered_details())
        return MappingProxyType(merged)

    def __post_init__(self) -> None:
        # Ép `str` thuần, cùng lý do đã ghi ở `Diagnostics`: một lớp con của
        # `str` với `__str__` đổi theo lần gọi qua được mọi `isinstance` và làm
        # cùng một field trả hai giá trị khác nhau giữa hai lần đọc (Audit P4).
        for name in ("batch_source_file", "order_id"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, as_exact_str(value))
        if self.category not in CATEGORIES:
            raise ValueError(f"Unknown review category: {self.category!r}")
        if self.severity not in SEVERITIES:
            raise ValueError(f"Unknown review severity: {self.severity!r}")
        if self.scope not in SCOPES:
            raise ValueError(f"Unknown review scope: {self.scope!r}")
        if not isinstance(self.diagnostics, Diagnostics):
            raise TypeError(
                "diagnostics phải là `Diagnostics` có kiểu, không phải dict. "
                "Một dict chuỗi tuỳ ý là chính kênh provenance song song mà "
                "Independent Review #6 đã bác bỏ (INVARIANT P)."
            )
        if not isinstance(self.provenance, RowProvenance):
            raise TypeError("provenance phải là `RowProvenance`")

        if self.provenance.rows and self.batch_source_file is not None:
            raise ValueError(
                f"ReviewItem({self.category}): `batch_source_file` chỉ dành cho "
                "item không có dòng nào; khi đã có dòng, tên file lấy từ chính "
                "các dòng đó."
            )

        # Truy vết được là chuyện cấu trúc, không phải quy ước (Review #1,
        # Finding 1).
        if not self.source_file:
            raise ValueError(
                f"ReviewItem({self.category}) needs source_file to be traceable"
            )
        if self.scope == SCOPE_ROW and self.source_row is None:
            raise ValueError(
                f"ReviewItem({self.category}) scope={SCOPE_ROW} needs source_row"
            )
        if self.scope == SCOPE_ORDER and not self.order_id:
            raise ValueError(
                f"ReviewItem({self.category}) scope={SCOPE_ORDER} needs order_id"
            )


@dataclass
class ReviewQueue:
    """The findings from one import, in reading order.

    Sorted by severity (ERROR first), then category, then source row — so the
    same input always produces the same queue, and the things worth a human's
    attention are not buried under a thousand INFO lines.
    """

    items: list[ReviewItem] = field(default_factory=list)

    def add(self, item: ReviewItem) -> None:
        self.items.append(item)

    def extend(self, items: list[ReviewItem]) -> None:
        self.items.extend(items)

    def sorted_items(self) -> list[ReviewItem]:
        return sorted(
            self.items,
            key=lambda i: (
                _SEVERITY_ORDER[i.severity],
                i.category,
                i.source_row if i.source_row is not None else -1,
                i.order_id or "",
                i.message,
            ),
        )

    def by_category(self, category: str) -> list[ReviewItem]:
        return [item for item in self.items if item.category == category]

    def by_severity(self, severity: str) -> list[ReviewItem]:
        return [item for item in self.items if item.severity == severity]

    def by_scope(self, scope: str) -> list[ReviewItem]:
        return [item for item in self.items if item.scope == scope]

    def counts_by_category(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for item in self.items:
            counts[item.category] = counts.get(item.category, 0) + 1
        return counts

    def affected_rows(self) -> int:
        """Total rows behind the queue, expanding aggregate items."""
        return sum(item.affected_count for item in self.items)

    def __len__(self) -> int:
        return len(self.items)

    def __iter__(self):
        return iter(self.sorted_items())
