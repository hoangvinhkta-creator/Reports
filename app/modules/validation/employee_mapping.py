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
            mapped employee
        F6  an employee flagged `active: false` that nevertheless has rows in
            this batch (HD-110-03)

    Info: employees legitimately absent (not yet effective, no longer
    effective, or `active: false` with no rows). Reporting these silently as
    "missing" would train readers to ignore F2.

**F6 exists because of a gap Independent Review #1 exposed.** Removing
`inactive` from the `Missing.employee` rule (Finding 3) would have left a
salesperson marked as having left, yet still selling, with no signal anywhere
— while their revenue kept flowing into their KPI. `active: false` alongside
an open `effective_to` window is contradictory master data. F6 reports it and
changes nothing else: no calculation moves, no KPI ownership moves. The
project owner approved exactly this shape (HD-110-03) rather than letting the
tool invent a rule of its own.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date
from typing import Optional

from app.modules.config.loader import as_date
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
        findings.append(
            MappingFinding(
                criterion="F3",
                bucket=BUCKET_HARD,
                message=(
                    f"F3 — {raw_value!r} khớp nhiều nhân viên cùng hiệu lực tại "
                    f"ngày của dòng đó: {sorted(matches)}"
                ),
                raw_value=raw_value,
                affected_count=unmapped.get(raw_value, 0),
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
            # HD-110-03. Reached only when master data contradicts itself:
            # the row is effective for these dates yet flagged as having left.
            if not active:
                findings.append(
                    MappingFinding(
                        criterion="F6",
                        bucket=BUCKET_WARNING,
                        message=(
                            f"F6 — {name!r} khai `active: false` nhưng vẫn có "
                            f"{mapped[name]} dòng trong kỳ. Master data mâu "
                            "thuẫn: nếu người này đã nghỉ thì `effective_to` "
                            "phải đóng lại. Doanh số vẫn đang tính cho họ — "
                            "cần người xem."
                        ),
                        employee=name,
                        raw_prefix=row.get("raw_prefix"),
                        affected_count=mapped[name],
                    )
                )
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
    dataset_start: Optional[date] = None
    dataset_end: Optional[date] = None
    source_file: Optional[str] = None

    for line in lines:
        raw_value = norm(line.employee_raw)
        when = line.date
        source_file = source_file or line.raw.source_file
        rows_by_raw_value[raw_value].append(line.raw.source_row)

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
        hits = {
            name
            for prefix, name, emp_row in prefixes
            if raw_value.startswith(prefix)
            and (when is None or _overlaps(emp_row, when, when))
        }
        if len(hits) > 1:
            ambiguities[raw_value] = hits

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
    )
