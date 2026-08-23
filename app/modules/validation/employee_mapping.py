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
    # THE affected row set — the rows that actually produced this finding, and
    # the single source of every provenance field below. Independent Review #4
    # found F3 and F4 building provenance from a wider set (every row sharing
    # the canonical identity), so a finding about row 6 could name row 7. The
    # fix is structural rather than a guard per criterion: nothing downstream
    # may look rows up by identity, because there is nowhere left to look them
    # up from.
    affected_rows: tuple[AffectedRow, ...] = ()
    # Extra provenance the criterion itself computed, keyed for the queue item.
    details: dict = field(default_factory=dict)
    # What the finding is ABOUT, when that differs from what it can point at.
    # F5 ("nothing mapped at all") is a statement about the whole batch even
    # though every unmapped row is affected — listing 14.000 row numbers in one
    # queue line would bury the one sentence that matters. The count stays
    # exact either way; only the rendering differs.
    batch_scoped: bool = False

    @property
    def affected_count(self) -> int:
        """Derived, never assigned — `affected_count` cannot drift from the
        rows it counts. `0` is a real answer: F2 means "matched no row"."""
        return len(self.affected_rows)

    @property
    def source_rows(self) -> tuple[int, ...]:
        return tuple(sorted(row.source_row for row in self.affected_rows))

    @property
    def source_file(self) -> Optional[str]:
        for row in self.affected_rows:
            if row.source_file:
                return row.source_file
        return None

    def raw_variants(self) -> dict[str, list[int]]:
        """Every original spelling **within this finding**, with its own rows.

        Canonical normalization groups; the originals are the evidence
        (Review #3, Finding 3). Built here — from `affected_rows` — so a
        variant belonging to a row outside the finding cannot appear
        (Review #4).
        """
        variants: dict[str, list[int]] = {}
        for row in self.affected_rows:
            if row.raw_original:
                variants.setdefault(row.raw_original, []).append(row.source_row)
        return {key: sorted(value) for key, value in variants.items()}

    def render_variants(self) -> str:
        """`!r` on purpose: a doubled space or an NFD spelling is invisible
        printed plainly, and those are the differences this preserves."""
        return " ; ".join(
            f"{original!r} → {', '.join(str(r) for r in rows)}"
            for original, rows in sorted(
                self.raw_variants().items(), key=lambda kv: (min(kv[1]), kv[0])
            )
        )


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
    row_index: Optional["MappingStats"] = None,
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
                    affected_rows=(
                        row_index.rows_for_record(row) if row_index else ()
                    ),
                )
            )

    for raw_value, matches in ambiguities.items():
        # `row_index` is optional so `reconcile_conversion.py` — which calls
        # this positionally and only prints strings — keeps working
        # byte-for-byte (CHECK-110-14). Production passes it, and only then
        # does the finding carry rows at all: `ambiguous_rows()` returns ONLY
        # the rows where more than one record was really in force on that
        # row's own date (Review #3 Finding 1, Review #4 Finding 1).
        rows = row_index.ambiguous_rows(raw_value) if row_index else ()
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
                affected_rows=rows,
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
                affected_rows=(
                    row_index.all_unmapped_rows() if row_index else ()
                ),
                batch_scoped=True,
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
                    # ONLY the rows that failed to map. A row of the same
                    # canonical identity that mapped fine is not evidence of
                    # missing master data, and naming it would put a row
                    # outside the finding into the finding's provenance
                    # (Review #4, Finding 2).
                    affected_rows=(
                        row_index.unmapped_rows(raw_value) if row_index else ()
                    ),
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
    employee_rows: list[dict], row_index: "MappingStats"
) -> list[MappingFinding]:
    """F6 — a record flagged `active: false` that still owns rows (HD-110-03).

    Attributed **per config record**, from the row index's own record
    attribution. Independent Review #2, Finding 2: the first version
    aggregated by normalized name and then applied one boolean `active` to
    every record sharing that name, so a closed historical record borrowed the
    current record's transactions and raised a false F6.

    The index attributes a row to a record only when the row has a date
    (HD-110-04): with no date there is no evidence for which record was in
    force, and picking one would manufacture a verdict out of an unknown. Such
    a row is already reported as `Missing.date`.

    Diagnostic only — no rate, no KPI ownership, and no
    `employee_mapping_status` changes because of it.
    """
    findings: list[MappingFinding] = []
    for record in employee_rows:
        if record.get("active", True):
            continue
        owned = row_index.rows_for_record(record)
        if not owned:
            continue
        name, prefix, starts, ends = _record_key(record)
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
                affected_rows=owned,
            )
        )
    return findings


@dataclass(frozen=True)
class AffectedRow:
    """One raw row that a finding is actually about.

    The unit of provenance introduced by Independent Review #4: a finding
    holds these, and every provenance field it exposes is derived from them.
    `raw_original` is the identity exactly as typed — canonical form is for
    grouping, the original is what an auditor needs to see.
    """

    source_file: Optional[str]
    source_row: int
    raw_original: str
    when: Optional[date]


@dataclass(frozen=True)
class AmbiguousRow(AffectedRow):
    """One raw row that really is ambiguous, and why.

    Independent Review #3, Finding 1: F3 is judged against **this row's own
    date** (DEC-121 — two prefixes that only ever existed in disjoint periods
    are a handover, not a clash). Recording ambiguity per raw *value* therefore
    tarred every row carrying that value, including rows where exactly one
    record was in force. Everything a reviewer needs to re-check the verdict
    lives here: the identity as typed, where the row is, its transaction date,
    and the master records that actually collided.
    """

    raw_value: str = ""
    records: tuple[str, ...] = ()

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
    """The counters `evaluate_raw_mapping` needs, plus a SCOPED row index.

    The analysis script builds the counters by reading the raw `.xlsx`
    directly. Production builds them from `WorkingLine`s that the real
    `EmployeeMapper` has already resolved, so the two paths agree by
    construction rather than by a second implementation of the matching rule.

    **The row index is deliberately narrow (Independent Review #4).** An
    earlier version exposed `rows_by_raw_value` / `rows_by_employee` — "every
    row sharing this canonical identity" — and the queue built provenance from
    them. That is wider than any finding: F3 is about the rows where records
    really collided, F4 about the rows that really failed to map. Those broad
    accessors are gone. What remains answers only the questions a criterion is
    entitled to ask, so provenance cannot silently widen again.
    """

    mapped: Counter
    groups: dict[str, str]
    unmapped: Counter
    ambiguities: dict[str, set]
    dataset_start: Optional[date]
    dataset_end: Optional[date]
    source_file: Optional[str]
    total_rows: int
    _unmapped_rows: dict[str, tuple[AffectedRow, ...]]
    _rows_by_record: dict[tuple, tuple[AffectedRow, ...]]
    _ambiguous_rows: dict[str, tuple[AmbiguousRow, ...]]

    # -- scoped accessors: one per question a criterion may ask ------------

    def unmapped_rows(self, raw_value: str) -> tuple[AffectedRow, ...]:
        """F4: rows of this identity that did NOT map. A row of the same
        identity that mapped fine is not evidence of missing master data."""
        return self._unmapped_rows.get(raw_value, ())

    def all_unmapped_rows(self) -> tuple[AffectedRow, ...]:
        """F5: nothing mapped at all, so every unmapped row is affected."""
        return tuple(
            row for rows in self._unmapped_rows.values() for row in rows
        )

    def ambiguous_rows(self, raw_value: str) -> tuple[AmbiguousRow, ...]:
        """F3: only the rows where more than one record was really in force
        on that row's own date."""
        return self._ambiguous_rows.get(raw_value, ())

    def rows_for_record(self, record: dict) -> tuple[AffectedRow, ...]:
        """F1 and F6: rows that production resolved to THIS config record.

        Keyed by record, not by name — two records deliberately share a name
        during a handover (DEC-121).
        """
        return self._rows_by_record.get(_record_key(record), ())

    def dataset_range(self) -> str:
        if self.dataset_start and self.dataset_end:
            return f"{self.dataset_start.isoformat()}..{self.dataset_end.isoformat()}"
        return "không xác định"


def collect_mapping_stats(
    lines: list[WorkingLine], employee_rows: list[dict]
) -> MappingStats:
    """Build the counters and the scoped row index from resolved lines."""
    prefixes = [
        (norm(row["raw_prefix"]), norm(row["normalized"]), row)
        for row in employee_rows
        if row.get("raw_prefix") and row.get("normalized")
    ]

    mapped: Counter = Counter()
    groups: dict[str, str] = {}
    unmapped: Counter = Counter()
    ambiguities: dict[str, set] = {}
    unmapped_rows: dict[str, list[AffectedRow]] = defaultdict(list)
    rows_by_record: dict[tuple, list[AffectedRow]] = defaultdict(list)
    ambiguous_rows: dict[str, list[AmbiguousRow]] = defaultdict(list)
    dataset_start: Optional[date] = None
    dataset_end: Optional[date] = None
    source_file: Optional[str] = None

    for line in lines:
        raw_value = norm(line.employee_raw)
        when = line.date
        source_file = source_file or line.raw.source_file
        affected = AffectedRow(
            source_file=line.raw.source_file,
            source_row=line.raw.source_row,
            raw_original=line.employee_raw or "",
            when=when,
        )

        if when:
            dataset_start = when if dataset_start is None else min(dataset_start, when)
            dataset_end = when if dataset_end is None else max(dataset_end, when)

        if line.employee_normalized:
            name = norm(line.employee_normalized)
            mapped[name] += 1
            groups[name] = line.employee_group or "—"
        else:
            unmapped[raw_value] += 1
            unmapped_rows[raw_value].append(affected)

        # Which config RECORD production resolved this row to — the same
        # semantics `EmployeeMapper` uses, so F1 and F6 attribute rows to a
        # record rather than to a shared name (DEC-121, Review #2 Finding 2).
        #
        # Only DATED rows are attributed (HD-110-04). Without a date the
        # effective-window filter does not apply, so any record picked here
        # would be a guess; a criterion built on it would be accusing master
        # data on evidence that does not exist.
        if when is not None:
            record = select_effective_record(employee_rows, line.employee_raw, when)
            if record is not None:
                rows_by_record[_record_key(record)].append(affected)

        # Ambiguity is judged on THIS row's own date: two prefixes that only
        # ever existed in disjoint periods are a handover, not a clash.
        #
        # HD-110-05 (DEC-131): a row with NO date cannot take part. F3 means
        # "more than one master record was valid at this row's moment" — with
        # no moment there is no evidence for that claim, and treating disjoint
        # windows as simultaneous would manufacture one. The row is already
        # reported as `Missing.date`. The guard lives HERE, in the production
        # collector, and not inside `evaluate_raw_mapping`: the analysis script
        # builds its own `ambiguities` and must keep behaving exactly as
        # CHECK-108A1-15 signed off.
        if when is None:
            continue

        matching = [
            (name, emp_row)
            for prefix, name, emp_row in prefixes
            if raw_value.startswith(prefix) and _overlaps(emp_row, when, when)
        ]
        hits = {name for name, _ in matching}
        if len(hits) > 1:
            # The verdict stays keyed by identity — that is what the analysis
            # script consumes. The ROWS are recorded separately so the queue
            # names only the rows that really collided.
            ambiguities[raw_value] = hits
            ambiguous_rows[raw_value].append(
                AmbiguousRow(
                    source_file=line.raw.source_file,
                    source_row=line.raw.source_row,
                    raw_original=line.employee_raw or "",
                    when=when,
                    raw_value=raw_value,
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
        source_file=source_file,
        total_rows=len(lines),
        _unmapped_rows={k: tuple(v) for k, v in unmapped_rows.items()},
        _rows_by_record={k: tuple(v) for k, v in rows_by_record.items()},
        _ambiguous_rows={k: tuple(v) for k, v in ambiguous_rows.items()},
    )
