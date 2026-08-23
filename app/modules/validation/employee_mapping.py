"""Employee-mapping diagnostics F1–F5 — TD-001.

**Why this file exists.** These criteria were written for
`tools/analysis/reconcile_conversion.py`, an analysis script somebody runs by
hand. TD-001 (`PROJECT/PROJECT_PROGRESS.md` → "Nợ Kỹ Thuật / Cảnh Báo Vận
Hành") requires F2 and F4 to appear in the Review Queue, and the Review Queue
lives on the import path. So the criteria move here — into production — and
the script imports them back. The direction matters: production owns the rule,
the analysis tool consumes it, never the reverse.

The criteria themselves are UNCHANGED. `reconcile_conversion.py` must keep
behaving exactly as it did when CHECK-108A1-15 was signed off — that output is
shipped evidence for a task already reviewed and merged, and quietly shifting
it would invalidate a record, not improve it (CHECK-110-14).

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

    Info: employees legitimately absent (not yet effective, no longer
    effective, or `active: false`). Reporting these silently as "missing"
    would train readers to ignore F2.
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from datetime import date
from typing import Optional

from app.modules.config.loader import as_date
from app.modules.domain.models import WorkingLine


def norm(value) -> str:
    """NFC-normalize and collapse whitespace (spec section 13)."""
    if value is None:
        return ""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", str(value))).strip()


@dataclass(frozen=True)
class RawMappingVerdict:
    """Outcome of the raw employee-mapping reconciliation.

    `hard_failures` alone decide the exit code. Warnings and info are printed
    but never fail the run — a diagnostic that can be wrong must not be able
    to block a merge on its own.
    """

    hard_failures: list[str]
    warnings: list[str]
    info: list[str]


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
    they are. See the module docstring for F1–F5.

    None of these criteria names an expected employee or group. An
    expected-values table written here would only assert that the config still
    says what it said when this file was authored.
    """
    hard: list[str] = []
    warnings: list[str] = []
    info: list[str] = []

    for row in employees:
        group = row.get("group")
        if group not in declared_groups:
            hard.append(
                f"F1 — nhân viên {row.get('normalized')!r} khai group "
                f"{group!r} không có trong `employee_groups`"
            )

    for raw_value, matches in ambiguities.items():
        hard.append(
            f"F3 — {raw_value!r} khớp nhiều nhân viên cùng hiệu lực tại ngày "
            f"của dòng đó: {sorted(matches)}"
        )

    if not mapped:
        hard.append(
            "F5 — KHÔNG nhân viên nào map được dòng nào. Mapping production "
            "hỏng hoàn toàn."
        )
        return RawMappingVerdict(hard, warnings, info)

    for row in employees:
        name = norm(row["normalized"])
        if name in mapped:
            continue
        starts, ends = _effective_window(row)
        if not row.get("active", True):
            info.append(
                f"F2 — {name!r} `active: false`, không có dòng nào: đúng kỳ vọng"
            )
        elif not _overlaps(row, dataset_start, dataset_end):
            info.append(
                f"F2 — {name!r} hiệu lực {starts}..{ends}, ngoài phạm vi dữ "
                "liệu: đúng kỳ vọng, không phải lỗi"
            )
        else:
            warnings.append(
                f"F2 — {name!r} (raw_prefix {row.get('raw_prefix')!r}) đang "
                "hiệu lực trong kỳ nhưng không khớp dòng nào. Có thể là sai "
                "prefix, cũng có thể chỉ là không có doanh số — cần người xem."
            )

    smallest_name, smallest = min(mapped.items(), key=lambda kv: kv[1])
    for raw_value, count in unmapped.items():
        if count >= smallest:
            warnings.append(
                f"F4 — {raw_value!r} chưa map nhưng có {count} dòng, "
                f"≥ nhân viên nhỏ nhất đã map ({smallest_name}: {smallest}). "
                "Dấu hiệu master data thiếu người đáng kể — chẩn đoán, không "
                "phải kết luận."
            )

    return RawMappingVerdict(hard, warnings, info)


@dataclass(frozen=True)
class MappingStats:
    """The inputs `evaluate_raw_mapping` needs, collected from working lines.

    The analysis script builds the same shape by reading the raw `.xlsx`
    directly. Production builds it from `WorkingLine`s that the real
    `EmployeeMapper` has already resolved, so the two paths agree by
    construction rather than by a second implementation of the matching rule.
    """

    mapped: Counter
    groups: dict[str, str]
    unmapped: Counter
    ambiguities: dict[str, set]
    dataset_start: Optional[date]
    dataset_end: Optional[date]


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
    dataset_start: Optional[date] = None
    dataset_end: Optional[date] = None

    for line in lines:
        raw_value = norm(line.employee_raw)
        when = line.date

        if when:
            dataset_start = when if dataset_start is None else min(dataset_start, when)
            dataset_end = when if dataset_end is None else max(dataset_end, when)

        if line.employee_normalized:
            name = norm(line.employee_normalized)
            mapped[name] += 1
            groups[name] = line.employee_group or "—"
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
    )
