"""Employee-mapping diagnostics F1–F6 — TD-001, HD-110-01, HD-110-03.

**Why this file exists.** These criteria were written for
`tools/analysis/reconcile_conversion.py`, an analysis script somebody runs by
hand. TD-001 (`PROJECT/PROJECT_PROGRESS.md` → "Nợ Kỹ Thuật / Cảnh Báo Vận
Hành") requires F2 and F4 to appear in the Review Queue, and the Review Queue
lives on the import path. So the criteria live here — in production — and the
script imports them back. The direction matters: production owns the rule, the
analysis tool consumes it, never the reverse.

`reconcile_conversion.py` must keep behaving exactly as it did when
CHECK-108A1-15 was signed off — that output is shipped evidence for a task
already reviewed and merged, and quietly shifting it would invalidate a
record, not improve it (CHECK-110-14). That is why `RawMappingVerdict` still
exposes `hard_failures` / `warnings` / `info` as the very same lists of
strings, in the very same order: the script and its tests see no change at
all. Production reads `findings` instead, which carries the same verdicts as
structured objects so each one can be traced back to real rows (Independent
Review #1, Finding 1).

    Hard failures (invariants — cannot be true of correct master data):
        F1  every employee's `group` must be declared in `employee_groups`
        F3  no raw `NVBH` may match two employees whose effective windows
            overlap on that row's own date (DEC-121)
        F5  at least one employee must map at all

    Warnings (heuristics — worth a human's attention, never block):
        F2  a configured employee, active and effective in this dataset's
            range, that matched no row
        F4  an unmapped name carrying at least as many rows as the smallest
            mapped employee. A blank `NVBH` never counts: there is no identity
            for master data to be missing, and that row is already reported as
            `Missing.employee` (Review #2, Finding 1).

    F6 is a warning too, but it does not live in `evaluate_raw_mapping`:
        F6  a config RECORD flagged `active: false` that still owns rows inside
            its own effective window (HD-110-03). It needs each row's date and
            the production mapper's record-selection semantics, which the
            analysis script never collects — see `evaluate_inactive_records`.
            Keeping it out also means `evaluate_raw_mapping` still produces
            exactly the F1–F5 output signed off in CHECK-108A1-15.

    Info: employees legitimately absent (not yet effective, no longer
    effective, or `active: false` with no rows). Reporting these silently as
    "missing" would train readers to ignore F2.

**F6 exists because of a gap Independent Review #1 exposed.** Removing
`inactive` from the `Missing.employee` rule (Finding 3) would have left a
salesperson marked as having left, yet still selling, with no signal anywhere
— while their revenue kept flowing into their KPI. `active: false` covering
rows that actually happened is contradictory master data. F6 reports it and
changes nothing else: no calculation moves, no KPI ownership moves. The
project owner approved exactly this shape (HD-110-03) rather than letting the
tool invent a rule of its own.

Independent Review #2 then found F6 was aggregating by employee NAME. A closed
historical record and a current active record share a name by design — that is
how DEC-121 expresses a handover — so the closed one raised a false F6 on the
active one's transactions. F6 now resolves each row to a specific record by
that row's own date (`evaluate_inactive_records`).
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from typing import Any

from app.modules.domain.canonical import (  # noqa: F401  (`SealedConstruction` re-export)
    FrozenCounter,
    FrozenMapping,
    SealedConstruction,
    canonical,
    factory_for,
    frozen_tuple_map,
)
from app.modules.domain.models import WorkingLine
from app.modules.validation.models import (
    AffectedRow,
    AmbiguousRow,
    Diagnostics,
    RowProvenance,
)
from app.modules.validation.text import normalize_text

BUCKET_HARD = "HARD"
BUCKET_WARNING = "WARNING"
BUCKET_INFO = "INFO"


# Re-exported under its original name: `tools/analysis/reconcile_conversion.py`
# imports `norm` from this module and must keep working untouched
# (CHECK-110-14). The implementation now lives in `text.py` so the validation
# rules and these criteria normalize identically (Review #1, Finding 4).
norm = normalize_text


@dataclass(frozen=True)
class MappingFinding:
    """Một verdict F2–F6, kèm mọi thứ cần để lần ngược về dòng thô.

    **`message` là property DẪN XUẤT** (DEC-134, RC-2): nó được `renderer.py`
    sinh ra từ đúng `diagnostics` + `provenance` của chính finding này. Không
    ai truyền chuỗi vào, nên không chuỗi nào khẳng định được một dòng nằm
    ngoài provenance.

    **F1 không còn ở đây** (HD-110-17): master khai `group` không có trong
    `employee_groups` nay bị từ chối tại biên loader, trước khi một giao dịch
    nào được xử lý. Trạng thái đó không tới được Review Queue nữa, nên một
    tiêu chí báo về nó là mã chết. Đây không phải bỏ kiểm tra — đây là chuyển
    kiểm tra lên sớm hơn và chặt hơn.
    """

    criterion: str
    bucket: str
    diagnostics: "Diagnostics"
    provenance: RowProvenance = field(default_factory=RowProvenance.of)

    @property
    def message(self) -> str:
        from app.modules.validation.renderer import render_message
        from app.modules.validation.models import CATEGORY_EMPLOYEE_MAPPING

        return render_message(
            CATEGORY_EMPLOYEE_MAPPING, self.diagnostics, self.provenance
        )

    @property
    def affected_rows(self) -> tuple:
        return self.provenance.rows

    @property
    def affected_count(self) -> int:
        return self.provenance.affected_count

    @property
    def source_rows(self) -> tuple:
        return self.provenance.source_rows

    @property
    def source_file(self):
        return self.provenance.source_file

    @property
    def batch_scoped(self) -> bool:
        return self.provenance.batch_scoped

    @property
    def employee(self):
        return self.diagnostics.employee

    @property
    def raw_value(self):
        return self.diagnostics.raw_value

    def raw_variants(self) -> dict:
        return self.provenance.raw_variants()

    def render_variants(self) -> str:
        return self.provenance.render_variants()


@dataclass(frozen=True)
class RawMappingVerdict:
    """Outcome of the raw employee-mapping reconciliation.

    `hard_failures` alone decide the exit code. Warnings and info are printed
    but never fail the run — a diagnostic that can be wrong must not be able
    to block a merge on its own.
    """

    findings: list[MappingFinding] = field(default_factory=list)

    def _messages(self, bucket: str) -> list[str]:
        return [f.message for f in self.findings if f.bucket == bucket]

    @property
    def hard_failures(self) -> list[str]:
        return self._messages(BUCKET_HARD)

    @property
    def warnings(self) -> list[str]:
        return self._messages(BUCKET_WARNING)

    @property
    def info(self) -> list[str]:
        return self._messages(BUCKET_INFO)


@dataclass(frozen=True)
class MappingInput:
    """Một dòng thô, ở dạng mà CẢ production LẪN script phân tích đều dựng được.

    Đây là cách RC-3 được đóng ở tầng thu thập: trước đây production đọc
    `WorkingLine` còn script tự đếm từ `.xlsx`, nên hai bên có hai bộ đếm và
    hai vòng khớp prefix. Nay cả hai dựng `MappingInput`, và **một** collector
    duy nhất biến chúng thành `MappingStats`.
    """

    source_file: Optional[str]
    source_row: int
    employee_raw: Optional[str]
    when: Optional[date]
    normalized: Optional[str]
    group: Optional[str]

    @classmethod
    def from_line(cls, line: WorkingLine) -> "MappingInput":
        return cls(
            source_file=line.raw.source_file,
            source_row=line.raw.source_row,
            employee_raw=line.employee_raw,
            when=line.date,
            normalized=line.employee_normalized,
            group=line.employee_group,
        )

    def as_line(self):
        """Adapter tối thiểu cho `AffectedRow.from_line` — cùng một dữ liệu."""
        return _LineView(self)


class _LineView:
    """View đọc-chỉ để `AffectedRow.from_line()` là đường tạo provenance DUY NHẤT."""

    __slots__ = ("_i", "raw")

    def __init__(self, item: "MappingInput"):
        self._i = item
        self.raw = _RawView(item)

    @property
    def employee_raw(self):
        return self._i.employee_raw

    @property
    def date(self):
        return self._i.when


class _RawView:
    __slots__ = ("source_file", "source_row")

    def __init__(self, item: "MappingInput"):
        self.source_file = item.source_file
        self.source_row = item.source_row


@canonical(sealed=True)
@dataclass(frozen=True, slots=True)
class MappingStats:
    """Nguồn sự thật CANONICAL cho một lượt chẩn đoán mapping (RC-3).

    Sở hữu **đồng thời** bộ đếm, chỉ mục dòng và chính mapper. Trước đây
    `evaluate_raw_mapping` nhận bộ đếm và chỉ mục dòng thành **hai tham số
    rời**, `row_index` lại còn optional — nên con số trong message và số dòng
    trong provenance có hai nguồn khác nhau, và đo được là chúng bất đồng
    (message nói "50 dòng", provenance nói 0).

    Ở đây chúng không thể bất đồng: cả hai được dựng trong một vòng lặp duy
    nhất, và mọi con số render ra đều đọc từ `provenance`.

    **Repair R1 chỉ chạm vào AN TOÀN DỰNG của kiểu này, không chạm truth
    model.** Hai việc, và chỉ hai việc: (1) cổng dựng chuyển từ field `_seal`
    sang cơ chế canonical không sao chép được, nên
    `dataclasses.replace(stats, total_rows=-1, mapper=None)` và subclass không
    còn dựng được stats giả; (2) mọi container được SAO CHÉP sang dạng bất
    biến, nên object sealed này không còn giữ mutable alias — Review #8 nêu
    đích danh lớp lỗi đó ở R1.

    Việc `mapped`/`groups`/`ambiguities` là một biểu diễn **song song** với
    row collections, và phải được DẪN XUẤT từ chúng, là **R2** và **không**
    được sửa ở đây. Cấu trúc dữ liệu, cách gom và mọi con số đều giữ nguyên.
    """

    mapper: Any
    mapped: FrozenCounter
    groups: FrozenMapping
    unmapped: FrozenCounter
    ambiguities: FrozenMapping
    dataset_start: Optional[date]
    dataset_end: Optional[date]
    source_file: Optional[str]
    total_rows: int
    _unmapped_rows: FrozenMapping
    _rows_by_record: FrozenMapping
    _ambiguous_rows: FrozenMapping

    def __post_init__(self) -> None:
        # LỚP 1 (R1) — SAO CHÉP sang container bất biến, không chỉ kiểm tra.
        # `frozen=True` chỉ cấm gán lại thuộc tính; nó không cấm sửa `Counter`
        # mà thuộc tính đó trỏ tới, nên trước đây `stats.mapped["BỊA"] = 999`
        # sửa được một canonical object đã sealed.
        object.__setattr__(self, "mapped", FrozenCounter(self.mapped))
        object.__setattr__(self, "unmapped", FrozenCounter(self.unmapped))
        object.__setattr__(self, "groups", FrozenMapping(self.groups))
        object.__setattr__(
            self, "ambiguities",
            FrozenMapping(
                {key: frozenset(value) for key, value in dict(self.ambiguities).items()}
            ),
        )
        for name in ("_unmapped_rows", "_rows_by_record", "_ambiguous_rows"):
            object.__setattr__(self, name, frozen_tuple_map(getattr(self, name)))
        if type(self.total_rows) is not int:
            raise TypeError(
                f"`total_rows` phải là int thuần, gặp {self.total_rows!r}."
            )
        if self.total_rows < 0:
            raise ValueError(
                f"`total_rows` không thể âm ({self.total_rows}) — nó đếm số dòng "
                "đã đi qua collector."
            )
        for name in ("resolve_record", "candidate_records", "record", "records",
                     "ref_for_index"):
            if not hasattr(self.mapper, name):
                raise TypeError(
                    f"`mapper` phải là một EmployeeMapper — thiếu `{name}`. "
                    "Một stats không có mapper thật thì mọi kết luận F2–F6 của "
                    "nó là phỏng đoán."
                )

    def unmapped_rows(self, raw_value: str) -> tuple:
        """F4: các dòng của identity này KHÔNG map được."""
        return self._unmapped_rows.get(raw_value, ())

    def all_unmapped_rows(self) -> tuple:
        """F5: không map được gì cả, nên mọi dòng unmapped đều bị ảnh hưởng."""
        return tuple(r for rows in self._unmapped_rows.values() for r in rows)

    def ambiguous_rows(self, raw_value: str) -> tuple:
        """F3: chỉ các dòng thật sự có nhiều hơn một record cùng hiệu lực."""
        return self._ambiguous_rows.get(raw_value, ())

    def rows_for_record_at(self, index: int) -> tuple:
        """F6: các dòng production đã resolve về ĐÚNG record ở vị trí này
        TRONG MASTER SNAPSHOT — tra bằng `RecordRef`, không so đối tượng."""
        if index < 0 or index >= len(self.mapper.records):
            return ()
        return self._rows_by_record.get(self.mapper.ref_for_index(index), ())

    def dataset_range(self) -> str:
        if self.dataset_start and self.dataset_end:
            return f"{self.dataset_start.isoformat()}..{self.dataset_end.isoformat()}"
        return "không xác định"


@factory_for(MappingStats)
def _materialise_stats(**values: Any) -> MappingStats:
    """Materialiser DUY NHẤT của `MappingStats` (Lớp 2, R1)."""
    return MappingStats(**values)


def collect_mapping_stats(inputs, mapper) -> MappingStats:
    """Collector DUY NHẤT — production và script phân tích cùng đi qua đây.

    `inputs` là một iterable `MappingInput`. Production dựng chúng từ
    `WorkingLine`; `reconcile_conversion.py` dựng chúng khi đọc `.xlsx`. Một
    bản cài đặt, nên hai đường không thể drift.
    """
    mapped: Counter = Counter()
    groups: dict = {}
    unmapped: Counter = Counter()
    ambiguities: dict = {}
    unmapped_rows: dict = defaultdict(list)
    rows_by_record: dict = defaultdict(list)
    ambiguous_rows: dict = defaultdict(list)
    dataset_start = dataset_end = None
    source_file = None
    total = 0

    for item in inputs:
        total += 1
        raw_value = norm(item.employee_raw)
        when = item.when
        source_file = source_file or item.source_file
        view = item.as_line()
        affected = AffectedRow.from_line(view)

        if when:
            dataset_start = when if dataset_start is None else min(dataset_start, when)
            dataset_end = when if dataset_end is None else max(dataset_end, when)

        if item.normalized:
            name = norm(item.normalized)
            mapped[name] += 1
            groups[name] = item.group or "—"
        else:
            unmapped[raw_value] += 1
            unmapped_rows[raw_value].append(affected)

        # Chỉ dòng CÓ NGÀY mới được quy về record và mới tham gia F3
        # (HD-110-04 / HD-110-05): không có ngày thì cửa sổ hiệu lực không áp
        # dụng được, nên mọi kết luận sẽ là phỏng đoán.
        if when is None:
            continue

        ref = mapper.resolve_record(item.employee_raw, when)
        if ref is not None:
            rows_by_record[ref].append(affected)

        candidates = mapper.candidate_records(item.employee_raw, when)
        hits = {norm(mapper.record(c).normalized) for c in candidates}
        if len(hits) > 1:
            ambiguities[raw_value] = hits
            ambiguous_rows[raw_value].append(
                AmbiguousRow.from_line(
                    view,
                    raw_value=raw_value,
                    records=sorted(_record_label(mapper.record(c)) for c in candidates),
                )
            )

    return _materialise_stats(
        mapper=mapper,
        mapped=mapped,
        groups=groups,
        unmapped=unmapped,
        ambiguities=ambiguities,
        dataset_start=dataset_start,
        dataset_end=dataset_end,
        source_file=source_file,
        total_rows=total,
        _unmapped_rows={k: tuple(v) for k, v in unmapped_rows.items()},
        _rows_by_record={k: tuple(v) for k, v in rows_by_record.items()},
        _ambiguous_rows={k: tuple(v) for k, v in ambiguous_rows.items()},
    )


def collect_stats_from_lines(lines, mapper) -> MappingStats:
    """Wrapper production: `WorkingLine` -> `MappingInput` -> collector chung."""
    return collect_mapping_stats((MappingInput.from_line(l) for l in lines), mapper)


def _record_label(record) -> str:
    """Danh tính người đọc hành động được — CHỈ để render, không làm khoá."""
    starts = "—" if record.window.start == date.min else record.window.start.isoformat()
    ends = "—" if record.window.end == date.max else record.window.end.isoformat()
    return f"{record.normalized}[{record.raw_prefix}|{starts}..{ends}]"


def _overlaps_window(record, start: Optional[date], end: Optional[date]) -> bool:
    if start is None or end is None:
        return True  # phạm vi dữ liệu chưa biết: coi như nhân viên còn trong kỳ
    return record.window.start <= end and start <= record.window.end


def evaluate_raw_mapping(stats: MappingStats) -> RawMappingVerdict:
    """Tiêu chí F2–F6 — nhận ĐÚNG MỘT tham số canonical (HD-110-12, RC-3).

    Không còn `employees`/`declared_groups` rời: chúng thuộc master mà `stats`
    đang giữ. Không còn `row_index` optional: provenance luôn có mặt.

    **F1 đã được thay thế** bởi fail-fast tại biên master (HD-110-17): một
    master khai group không tồn tại không parse được, nên không tới được đây.
    """
    findings: list = []
    mapper = stats.mapper
    records = mapper.records

    for raw_value, matches in stats.ambiguities.items():
        findings.append(
            MappingFinding(
                criterion="F3",
                bucket=BUCKET_HARD,
                diagnostics=Diagnostics(
                    criterion="F3",
                    raw_value=raw_value,
                    matched_employees=tuple(sorted(matches)),
                ),
                provenance=RowProvenance.of(stats.ambiguous_rows(raw_value)),
            )
        )

    if not stats.mapped:
        findings.append(
            MappingFinding(
                criterion="F5",
                bucket=BUCKET_HARD,
                diagnostics=Diagnostics(criterion="F5"),
                provenance=RowProvenance.batch(stats.all_unmapped_rows()),
            )
        )
        return RawMappingVerdict(findings)

    for record in records:
        name = norm(record.normalized)
        if name in stats.mapped:
            continue
        starts, ends = record.window.start, record.window.end
        if not record.active:
            reason, bucket = "inactive", BUCKET_INFO
        elif not _overlaps_window(record, stats.dataset_start, stats.dataset_end):
            reason, bucket = "out_of_range", BUCKET_INFO
        else:
            reason, bucket = "effective", BUCKET_WARNING
        findings.append(
            MappingFinding(
                criterion="F2",
                bucket=bucket,
                diagnostics=Diagnostics(
                    criterion="F2",
                    employee=name,
                    raw_prefix=record.raw_prefix,
                    f2_reason=reason,
                    window_start=starts.isoformat() if starts != date.min else str(starts),
                    window_end=ends.isoformat() if ends != date.max else str(ends),
                ),
            )
        )

    smallest_name, smallest = min(stats.mapped.items(), key=lambda kv: kv[1])
    for raw_value, count in stats.unmapped.items():
        # Một `NVBH` trống không phải một IDENTITY chưa map — không có tên nào
        # để master data thiếu. Dòng đó đã được `Missing.employee` báo.
        if not raw_value:
            continue
        if count >= smallest:
            findings.append(
                MappingFinding(
                    criterion="F4",
                    bucket=BUCKET_WARNING,
                    diagnostics=Diagnostics(
                        criterion="F4",
                        raw_value=raw_value,
                        smallest_employee=smallest_name,
                        smallest_count=smallest,
                    ),
                    provenance=RowProvenance.of(stats.unmapped_rows(raw_value)),
                )
            )

    return RawMappingVerdict(findings)


def evaluate_inactive_records(stats: MappingStats) -> list:
    """F6 — bản ghi `active: false` mà vẫn sở hữu dòng (HD-110-03)."""
    findings: list = []
    for position, record in enumerate(stats.mapper.records):
        if record.active:
            continue
        owned = stats.rows_for_record_at(position)
        if not owned:
            continue
        starts, ends = record.window.start, record.window.end
        findings.append(
            MappingFinding(
                criterion="F6",
                bucket=BUCKET_WARNING,
                diagnostics=Diagnostics(
                    criterion="F6",
                    employee=norm(record.normalized),
                    raw_prefix=record.raw_prefix,
                    window_start=starts.isoformat() if starts != date.min else str(starts),
                    window_end=ends.isoformat() if ends != date.max else str(ends),
                ),
                provenance=RowProvenance.of(owned),
            )
        )
    return findings
