"""Map raw `NVBH` strings to normalized employees (DEC-104).

Many-to-one: several raw prefixes (Đức Hiệp / Mr Quý / Mr Vinh) collapse to
one normalized employee ("Nội thành"). Matching is prefix-based because the
raw column carries a trailing phone number (`"Tín Phát 0869931931"`). A raw
value that matches no configured prefix is never silently dropped — it comes
back flagged `unmapped` so the caller can route it to review (C11,
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
        )

    def apply(self, lines: list[WorkingLine]) -> list[WorkingLine]:
        for line in lines:
            result = self.resolve(line.employee_raw, line.date)
            line.employee_normalized = result.normalized
            line.employee_mapping_status = result.status
        return lines
