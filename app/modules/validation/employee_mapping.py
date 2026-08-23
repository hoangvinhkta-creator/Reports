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

from app.modules.config.loader import as_date, effective_rows
from app.modules.domain.models import WorkingLine
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
    """One F1–F6 verdict, with everything needed to trace it back.

    `message` is the exact string the analysis script has always printed —
    it is the rendering, not the record. `criterion`, `employee`, `raw_value`
    and `affected_count` are the record, and they are what the Review Queue
    turns into a traceable item.
    """

    criterion: str
    bucket: str
    message: str
    employee: Optional[str] = None
    raw_value: Optional[str] = None
    raw_prefix: Optional[str] = None
    declared_group: Optional[str] = None
    affected_count: int = 0
    # Rows this finding is about, when the finding itself knows them. F6 must
    # carry its own: two config records can share a `normalized` name, so
    # looking rows up by name would hand one record the other's transactions
    # (Independent Review #2, Finding 2).
    source_rows: tuple[int, ...] = ()
    # Extra provenance the criterion itself computed. Merged into the queue
    # item's `details` verbatim. F3 uses it to name which rows were ambiguous,
    # on what date, against which master records (Review #3, Finding 1).
    details: dict = field(default_factory=dict)


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


def _effective_window(row: dict) -> tuple[date, date]:
    starts = as_date(row.get("effective_from")) or date.min
    ends = as_date(row.get("effective_to")) or date.max
    return starts, ends


def _overlaps(row: dict, start: Optional[date], end: Optional[date]) -> bool:
    if start is None or end is None:
        return True  # unknown dataset range: assume the employee is in scope
    starts, ends = _effective_window(row)
    return starts <= end and start <= ends


def evaluate_raw_mapping(
    mapped: Counter,
    groups: dict[str, str],
    unmapped: Counter,
    ambiguities: dict[str, set],
    employees: list[dict],
    declared_groups: set[str],
    dataset_start: Optional[date] = None,
    dataset_end: Optional[date] = None,
    ambiguity_rows: Optional[dict[str, list["AmbiguousRow"]]] = None,
) -> RawMappingVerdict:
    """Criteria for the raw employee-mapping reconciliation.

    Counting rows and printing them proves nothing on its own: a badly broken
    `employees.yaml` still produces a tidy table, just a wrong one. But the
    opposite failure is just as bad — a criterion that fires on healthy data
    is noise, and noise gets ignored. So the criteria are split by how certain
    they are. See the module docstring for F1–F6.

    None of these criteria names an expected employee or group. An
    expected-values table written here would only assert that the config still
    says what it said when this file was authored.
    """
    findings: list[MappingFinding] = []

    for row in employees:
        group = row.get("group")
        if group not in declared_groups:
            name = norm(row.get("normalized"))
            findings.append(
                MappingFinding(
                    criterion="F1",
                    bucket=BUCKET_HARD,
                    message=(
                        f"F1 — nhân viên {row.get('normalized')!r} khai group "
                        f"{group!r} không có trong `employee_groups`"
                    ),
                    employee=name or None,
                    declared_group=str(group),
                    affected_count=mapped.get(name, 0),
                )
            )

    for raw_value, matches in ambiguities.items():
        # `ambiguity_rows` is optional so `reconcile_conversion.py` — which
        # calls this positionally and only prints strings — keeps working
        # byte-for-byte (CHECK-110-14). Production passes it, and only then
        # does the finding know WHICH rows collided: recording ambiguity per
        # raw *value* tarred every row carrying that value, including rows
        # where exactly one record was in force (Review #3, Finding 1).
        rows = list((ambiguity_rows or {}).get(raw_value, []))
        details: dict[str, str] = {}
        if rows:
            details = {
                "ambiguous_rows": " ; ".join(row.render() for row in rows),
                "conflicting_records": ", ".join(
                    sorted({label for row in rows for label in row.records})
                ),
            }
        findings.append(
            MappingFinding(
                criterion="F3",
                bucket=BUCKET_HARD,
                message=(
                    f"F3 — {raw_value!r} khớp nhiều nhân viên cùng hiệu lực tại "
                    f"ngày của dòng đó: {sorted(matches)}"
                ),
                raw_value=raw_value,
                affected_count=(
                    len(rows) if rows else unmapped.get(raw_value, 0)
                ),
                source_rows=tuple(sorted(row.source_row for row in rows)),
                details=details,
            )
        )

    if not mapped:
        findings.append(
            MappingFinding(
                criterion="F5",
                bucket=BUCKET_HARD,
                message=(
                    "F5 — KHÔNG nhân viên nào map được dòng nào. Mapping "
                    "production hỏng hoàn toàn."
                ),
                affected_count=sum(unmapped.values()),
            )
        )
        return RawMappingVerdict(findings)

    for row in employees:
        name = norm(row["normalized"])
        active = row.get("active", True)

        if name in mapped:
            continue

        starts, ends = _effective_window(row)
        if not active:
            findings.append(
                MappingFinding(
                    criterion="F2",
                    bucket=BUCKET_INFO,
                    message=(
                        f"F2 — {name!r} `active: false`, không có dòng nào: "
                        "đúng kỳ vọng"
                    ),
                    employee=name,
                    raw_prefix=row.get("raw_prefix"),
                )
            )
        elif not _overlaps(row, dataset_start, dataset_end):
            findings.append(
                MappingFinding(
                    criterion="F2",
                    bucket=BUCKET_INFO,
                    message=(
                        f"F2 — {name!r} hiệu lực {starts}..{ends}, ngoài phạm "
                        "vi dữ liệu: đúng kỳ vọng, không phải lỗi"
                    ),
                    employee=name,
                    raw_prefix=row.get("raw_prefix"),
                )
            )
        else:
            findings.append(
                MappingFinding(
                    criterion="F2",
                    bucket=BUCKET_WARNING,
                    message=(
                        f"F2 — {name!r} (raw_prefix {row.get('raw_prefix')!r}) "
                        "đang hiệu lực trong kỳ nhưng không khớp dòng nào. Có "
                        "thể là sai prefix, cũng có thể chỉ là không có doanh "
                        "số — cần người xem."
                    ),
                    employee=name,
                    raw_prefix=row.get("raw_prefix"),
                )
            )

    smallest_name, smallest = min(mapped.items(), key=lambda kv: kv[1])
    for raw_value, count in unmapped.items():
        # A blank/absent `NVBH` is not an unmapped IDENTITY — there is no name
        # for master data to be missing. That row is already reported as
        # `Missing.employee`, and letting it reach F4 produced a finding with
        # no raw identity and no rows to point at (Review #2, Finding 1).
        # `reconcile_conversion.py` never sees blanks either: it skips rows
        # with no `NVBH` before counting, so this changes nothing there.
        if not raw_value:
            continue
        if count >= smallest:
            findings.append(
                MappingFinding(
                    criterion="F4",
                    bucket=BUCKET_WARNING,
                    message=(
                        f"F4 — {raw_value!r} chưa map nhưng có {count} dòng, "
                        f"≥ nhân viên nhỏ nhất đã map ({smallest_name}: "
                        f"{smallest}). Dấu hiệu master data thiếu người đáng "
                        "kể — chẩn đoán, không phải kết luận."
                    ),
                    raw_value=raw_value,
                    affected_count=count,
                )
            )

    return RawMappingVerdict(findings)


def select_effective_record(
    employee_rows: list[dict], employee_raw: Optional[str], when: Optional[date]
) -> Optional[dict]:
    """The config record production resolves this raw value to **on this date**.

    Mirrors `EmployeeMapper.resolve` exactly: filter the rows by their
    effective window against THIS row's own date, prefix-match the raw value,
    longest prefix wins. It reads the raw string unnormalized because the
    production mapper does; matching production is the whole point, so this
    must not quietly be stricter or looser than it.

    The equivalence is asserted against the real `EmployeeMapper` in
    `tests/test_validation_employee_mapping.py` rather than assumed — a second
    implementation of a rule is only safe while something proves the two agree.
    """
    if not employee_raw:
        return None
    candidates = effective_rows(employee_rows, when) if when else employee_rows
    matches = [
        row
        for row in candidates
        if row.get("raw_prefix") and employee_raw.startswith(row["raw_prefix"])
    ]
    if not matches:
        return None
    return max(matches, key=lambda row: len(row["raw_prefix"]))


def _record_key(record: dict) -> tuple:
    """Identity of one config RECORD, not of an employee name.

    Two records can share a `normalized` name — that is exactly how a handover
    is expressed (DEC-121): close the old row with `effective_to`, open a new
    one with `effective_from`. Keying by name alone would merge them.
    """
    starts, ends = _effective_window(record)
    return (
        norm(record.get("normalized")),
        record.get("raw_prefix"),
        starts.isoformat(),
        ends.isoformat(),
    )


def evaluate_inactive_records(
    lines: list[WorkingLine], employee_rows: list[dict]
) -> list[MappingFinding]:
    """F6 — a record flagged `active: false` that still owns rows (HD-110-03).

    Evaluated **per raw row, by that row's own date**, and attributed to the
    specific config record production would have selected. Independent Review
    #2, Finding 2: the first version aggregated by normalized name and then
    applied one boolean `active` to every record sharing that name, so a
    closed historical record borrowed the current record's transactions and
    raised a false F6.

    A record only appears here if rows genuinely resolved to *it*, inside
    *its* effective window. Diagnostic only — no rate, no KPI ownership, and
    no `employee_mapping_status` changes because of it.
    """
    buckets: dict[tuple, list[WorkingLine]] = {}
    records: dict[tuple, dict] = {}

    for line in lines:
        if line.date is None:
            # HD-110-04. With no transaction date there is no evidence for
            # which master record was in force, so there is nothing to accuse.
            # Picking the first match would manufacture a verdict out of an
            # unknown, and asserting the row falls inside any effective window
            # would be a claim the data does not support. The row is already
            # reported as `Missing.date`; fix that first, and F6 becomes
            # answerable on the next import.
            continue
        record = select_effective_record(employee_rows, line.employee_raw, line.date)
        if record is None or record.get("active", True):
            continue
        key = _record_key(record)
        records.setdefault(key, record)
        buckets.setdefault(key, []).append(line)

    findings: list[MappingFinding] = []
    for key in sorted(buckets):
        record = records[key]
        owned = buckets[key]
        rows = sorted(line.raw.source_row for line in owned)
        name, prefix, starts, ends = key
        findings.append(
            MappingFinding(
                criterion="F6",
                bucket=BUCKET_WARNING,
                message=(
                    f"F6 — bản ghi {name!r} (raw_prefix {prefix!r}, hiệu lực "
                    f"{starts}..{ends}) khai `active: false` nhưng có "
                    f"{len(owned)} dòng rơi đúng vào cửa sổ hiệu lực của nó. "
                    "Master data mâu thuẫn: nếu người này đã nghỉ thì "
                    "`effective_to` phải đóng trước các dòng đó. Doanh số vẫn "
                    "đang tính cho họ — cần người xem."
                ),
                employee=name,
                raw_prefix=prefix,
                affected_count=len(owned),
                source_rows=tuple(rows),
            )
        )
    return findings


@dataclass(frozen=True)
class AmbiguousRow:
    """One raw row that really is ambiguous, and why.

    Independent Review #3, Finding 1: F3 is judged against **this row's own
    date** (DEC-121 — two prefixes that only ever existed in disjoint periods
    are a handover, not a clash). Recording ambiguity per raw *value* therefore
    tarred every row carrying that value, including rows where exactly one
    record was in force. Everything a reviewer needs to re-check the verdict
    lives here: the identity as typed, where the row is, its transaction date,
    and the master records that actually collided.
    """

    raw_value: str
    raw_original: str
    source_file: Optional[str]
    source_row: int
    when: Optional[date]
    records: tuple[str, ...]

    def render(self) -> str:
        stamp = self.when.isoformat() if self.when else "không có ngày"
        return f"dòng {self.source_row} ({stamp}) → {', '.join(self.records)}"


def _record_label(record: dict) -> str:
    """A record identity a human can act on — name alone is not enough when
    two records deliberately share it (DEC-121)."""
    starts, ends = _effective_window(record)
    return (
        f"{norm(record.get('normalized'))}"
        f"[{record.get('raw_prefix')}|{starts.isoformat()}..{ends.isoformat()}]"
    )


@dataclass(frozen=True)
class MappingStats:
    """The inputs `evaluate_raw_mapping` needs, collected from working lines.

    The analysis script builds the counters by reading the raw `.xlsx`
    directly. Production builds them from `WorkingLine`s that the real
    `EmployeeMapper` has already resolved, so the two paths agree by
    construction rather than by a second implementation of the matching rule.

    `rows_by_raw_value` / `rows_by_employee` exist only on the production side:
    the script prints to a terminal, but a Review Queue item has to name the
    rows it is about (Review #1, Finding 1).
    """

    mapped: Counter
    groups: dict[str, str]
    unmapped: Counter
    ambiguities: dict[str, set]
    dataset_start: Optional[date]
    dataset_end: Optional[date]
    rows_by_raw_value: dict[str, list[int]]
    rows_by_employee: dict[str, list[int]]
    source_file: Optional[str]
    total_rows: int
    # canonical identity -> {raw string exactly as typed: its source rows}.
    # Canonical form is right for GROUPING; throwing the originals away would
    # destroy the audit trail (Review #3, Finding 3).
    raw_variants: dict[str, dict[str, list[int]]]
    # canonical identity -> only the rows that are genuinely ambiguous, judged
    # on each row's own date (Review #3, Finding 1).
    ambiguity_rows: dict[str, list[AmbiguousRow]]

    def render_variants(self, raw_value: str) -> str:
        """Every original spelling of one canonical identity, with its rows.

        `!r` on purpose: a doubled space or a stray tab is invisible when
        printed plainly, and those are exactly the differences this exists to
        preserve.
        """
        variants = self.raw_variants.get(raw_value, {})
        parts = [
            f"{original!r} → {', '.join(str(r) for r in sorted(rows))}"
            for original, rows in sorted(
                variants.items(), key=lambda kv: (min(kv[1]), kv[0])
            )
        ]
        return " ; ".join(parts)

    def dataset_range(self) -> str:
        if self.dataset_start and self.dataset_end:
            return f"{self.dataset_start.isoformat()}..{self.dataset_end.isoformat()}"
        return "không xác định"


def collect_mapping_stats(
    lines: list[WorkingLine], employee_rows: list[dict]
) -> MappingStats:
    """Build `MappingStats` from lines the pipeline has already mapped."""
    prefixes = [
        (norm(row["raw_prefix"]), norm(row["normalized"]), row)
        for row in employee_rows
        if row.get("raw_prefix") and row.get("normalized")
    ]

    mapped: Counter = Counter()
    groups: dict[str, str] = {}
    unmapped: Counter = Counter()
    ambiguities: dict[str, set] = {}
    rows_by_raw_value: dict[str, list[int]] = defaultdict(list)
    rows_by_employee: dict[str, list[int]] = defaultdict(list)
    raw_variants: dict[str, dict[str, list[int]]] = defaultdict(
        lambda: defaultdict(list)
    )
    ambiguity_rows: dict[str, list[AmbiguousRow]] = defaultdict(list)
    dataset_start: Optional[date] = None
    dataset_end: Optional[date] = None
    source_file: Optional[str] = None

    for line in lines:
        raw_value = norm(line.employee_raw)
        when = line.date
        source_file = source_file or line.raw.source_file
        rows_by_raw_value[raw_value].append(line.raw.source_row)
        if line.employee_raw is not None:
            raw_variants[raw_value][line.employee_raw].append(line.raw.source_row)

        if when:
            dataset_start = when if dataset_start is None else min(dataset_start, when)
            dataset_end = when if dataset_end is None else max(dataset_end, when)

        if line.employee_normalized:
            name = norm(line.employee_normalized)
            mapped[name] += 1
            groups[name] = line.employee_group or "—"
            rows_by_employee[name].append(line.raw.source_row)
        else:
            unmapped[raw_value] += 1

        # Ambiguity is judged on THIS row's own date: two prefixes that only
        # ever existed in disjoint periods are a handover, not a clash.
        matching = [
            (name, emp_row)
            for prefix, name, emp_row in prefixes
            if raw_value.startswith(prefix)
            and (when is None or _overlaps(emp_row, when, when))
        ]
        hits = {name for name, _ in matching}
        if len(hits) > 1:
            # The verdict stays keyed by identity — that is what the analysis
            # script consumes and what CHECK-108A1-15 signed off. The ROWS are
            # recorded separately so the queue can name only the rows that are
            # really ambiguous (Review #3, Finding 1).
            ambiguities[raw_value] = hits
            ambiguity_rows[raw_value].append(
                AmbiguousRow(
                    raw_value=raw_value,
                    raw_original=line.employee_raw or "",
                    source_file=line.raw.source_file,
                    source_row=line.raw.source_row,
                    when=when,
                    records=tuple(
                        sorted(_record_label(emp_row) for _, emp_row in matching)
                    ),
                )
            )

    return MappingStats(
        mapped=mapped,
        groups=groups,
        unmapped=unmapped,
        ambiguities=ambiguities,
        dataset_start=dataset_start,
        dataset_end=dataset_end,
        rows_by_raw_value=dict(rows_by_raw_value),
        rows_by_employee=dict(rows_by_employee),
        source_file=source_file,
        total_rows=len(lines),
        raw_variants={k: dict(v) for k, v in raw_variants.items()},
        ambiguity_rows=dict(ambiguity_rows),
    )
