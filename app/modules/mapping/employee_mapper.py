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
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Optional

from app.modules.config.loader import effective_rows, load_yaml
from app.modules.domain.models import (
    MAPPING_STATUS_INACTIVE,
    MAPPING_STATUS_MAPPED,
    MAPPING_STATUS_UNMAPPED,
    WorkingLine,
)


@dataclass(frozen=True)
class MappingResult:
    normalized: Optional[str]
    status: str
    default_lead_source: Optional[str]
    include_in_kpi: Optional[bool]
    group: Optional[str] = None


class EmployeeMapper:
    def __init__(self, rows: list[dict]):
        self._rows = rows

    @classmethod
    def from_yaml(cls, path: Path) -> "EmployeeMapper":
        data = load_yaml(path)
        return cls(data.get("employees", []))

    def resolve(
        self, employee_raw: Optional[str], as_of: Optional[date]
    ) -> MappingResult:
        if not employee_raw:
            return MappingResult(None, MAPPING_STATUS_UNMAPPED, None, None)

        candidates = effective_rows(self._rows, as_of) if as_of else self._rows
        matches = [
            row for row in candidates if employee_raw.startswith(row["raw_prefix"])
        ]
        if not matches:
            return MappingResult(None, MAPPING_STATUS_UNMAPPED, None, None)

        # Most specific prefix wins if more than one configured row matches.
        best = max(matches, key=lambda row: len(row["raw_prefix"]))
        status = MAPPING_STATUS_MAPPED if best.get("active", True) else MAPPING_STATUS_INACTIVE
        return MappingResult(
            normalized=best["normalized"],
            status=status,
            default_lead_source=best.get("default_lead_source"),
            include_in_kpi=best.get("include_in_kpi"),
            group=best.get("group"),
        )

    def apply(self, lines: list[WorkingLine]) -> list[WorkingLine]:
        for line in lines:
            result = self.resolve(line.employee_raw, line.date)
            line.employee_normalized = result.normalized
            line.employee_mapping_status = result.status
            line.employee_group = result.group
        return lines
