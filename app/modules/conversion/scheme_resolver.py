"""`ConversionSchemeResolver` — resolve the conversion rate for one product line.

ADR-104 + ADR-106. Five independent dimensions:

    Employee ≠ EmployeeGroup ≠ LeadSource ≠ ProductGroup ≠ ConversionScheme

The rate is looked up from `config/conversion_rates.yaml` by
`(employee, employee_group, lead_source, product_group, the order's own
date)`. It is never derived from `LeadSource` alone — `PERSONAL` does not mean
5.5%: the Nội thành group sells PERSONAL at 2%, and the same group's Gia dụng
lines convert at 8%.

Resolution (ADR-106 §4):

    1. `lead_source` is a HARD FILTER. A row for the other source is dropped
       outright; no "*" ever wins across the wrong source.
    2. Among the survivors, the MOST SPECIFIC row wins:

           specificity = 4×(employee ≠ "*")
                       + 2×(employee_group ≠ "*")
                       + 1×(product_group ≠ "*")

    3. A tie is an AMBIGUOUS CONFIG ERROR — this module refuses to pick.
    4. No row at all -> `Unresolved`, never a fallback rate.

Points 3 and 4 are the whole safety argument of this module. A missing or
ambiguous rate that raises or lands in the review queue costs someone a
minute; a silently borrowed rate costs someone the wrong salary, and looks
correct on the report.

The specificity weights are this ADR's resolution convention, **not an
immutable business rule**. They encode "an individual is more specific than a
group, a group more specific than a product kind". If a fifth dimension ever
appears, do NOT extend the formula here — reopen ADR-106 and let the project
owner decide the ordering.

Rates are `Decimal`, read from strings in YAML, never `float` (ADR-103):
these numbers are divided into profit figures that become payroll.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any, Optional

from app.modules.config.loader import effective_rows, load_yaml
from app.modules.domain.models import CONVERSION_UNRESOLVED

ANY = "*"

_WEIGHT_EMPLOYEE = 4
_WEIGHT_EMPLOYEE_GROUP = 2
_WEIGHT_PRODUCT_GROUP = 1


class AmbiguousSchemeConfigError(Exception):
    """Two configured rows are equally specific for the same input.

    Deliberately fatal: choosing either one would be a coin flip that lands
    in payroll. The configuration has to say which one wins.
    """


@dataclass(frozen=True)
class SchemeResolution:
    scheme: Optional[str]
    rate: Optional[Decimal]
    source_of_value: str


def _matches(row_value: Any, actual: Optional[str]) -> bool:
    """A `"*"` row matches anything; otherwise the value must be equal.

    An `actual` of `None` (unmapped employee, no group) matches only `"*"` —
    it must never satisfy a specific row.
    """
    if row_value == ANY or row_value is None:
        return True
    return row_value == actual


def _specificity(row: dict[str, Any]) -> int:
    score = 0
    if row.get("employee", ANY) not in (ANY, None):
        score += _WEIGHT_EMPLOYEE
    if row.get("employee_group", ANY) not in (ANY, None):
        score += _WEIGHT_EMPLOYEE_GROUP
    if row.get("product_group", ANY) not in (ANY, None):
        score += _WEIGHT_PRODUCT_GROUP
    return score


class ConversionSchemeResolver:
    def __init__(self, rows: list[dict[str, Any]], default_product_group: str):
        self._rows = rows
        self._default_product_group = default_product_group

    @classmethod
    def from_yaml(cls, path: Path) -> "ConversionSchemeResolver":
        data = load_yaml(path)
        return cls(
            rows=data.get("conversion_schemes", []),
            default_product_group=data.get("default_product_group", ""),
        )

    @property
    def default_product_group(self) -> str:
        return self._default_product_group

    def resolve_auto(
        self,
        employee: Optional[str],
        employee_group: Optional[str],
        lead_source: Optional[str],
        product_group: Optional[str],
        as_of: Optional[date],
    ) -> SchemeResolution:
        """Automatic verdict only — ignores any manual override.

        Kept separate from `resolve_final` so "reset to auto" stays possible
        without recomputing anything else (ADR-102).
        """
        if lead_source is None or as_of is None:
            return SchemeResolution(CONVERSION_UNRESOLVED, None, "Unresolved")

        # An unidentified seller cannot be priced (DEC-127 §8). This check runs
        # BEFORE the universal "*" rows are considered: a `"*"` row means "any
        # KNOWN employee", not "anyone at all". Letting an unmapped name fall
        # through to `* + PERSONAL` would hand a KPI rate to a person nobody
        # has confirmed exists — the review queue is where they belong.
        if employee is None or employee_group is None:
            return SchemeResolution(
                CONVERSION_UNRESOLVED, None, "Unresolved:UnmappedEmployee"
            )

        dated = effective_rows(self._rows, as_of)
        candidates = [
            row
            for row in dated
            if row.get("lead_source") == lead_source  # hard filter, no "*"
            and _matches(row.get("employee", ANY), employee)
            and _matches(row.get("employee_group", ANY), employee_group)
            and _matches(row.get("product_group", ANY), product_group)
        ]
        if not candidates:
            return SchemeResolution(CONVERSION_UNRESOLVED, None, "Unresolved")

        best = max(_specificity(row) for row in candidates)
        winners = [row for row in candidates if _specificity(row) == best]
        if len(winners) > 1:
            names = ", ".join(sorted(str(row.get("scheme")) for row in winners))
            raise AmbiguousSchemeConfigError(
                "Nhiều dòng conversion_rates.yaml cùng độ cụ thể "
                f"(specificity={best}) cho (employee={employee!r}, "
                f"group={employee_group!r}, lead_source={lead_source!r}, "
                f"product_group={product_group!r}, ngày={as_of}): {names}. "
                "Engine không tự chọn — sửa cấu hình cho rõ ràng."
            )

        row = winners[0]
        origin = (
            "Employee"
            if row.get("employee", ANY) not in (ANY, None)
            else "EmployeeGroup"
            if row.get("employee_group", ANY) not in (ANY, None)
            else "ProductGroup"
            if row.get("product_group", ANY) not in (ANY, None)
            else "LeadSource"
        )
        scheme = row.get("scheme")
        return SchemeResolution(
            scheme, Decimal(str(row["rate"])), f"Auto:{origin} ({scheme})"
        )

    def resolve_final(
        self,
        auto: SchemeResolution,
        manual_override: Optional[str],
        as_of: Optional[date] = None,
    ) -> SchemeResolution:
        """A manual scheme override outranks the automatic verdict.

        The override names a scheme, so its rate still comes from the config
        row for that scheme **as of the order's own business date** — a person
        picks *which policy applies*, never the number itself. Using the same
        effective-dating rule as `resolve_auto` matters once a scheme spans
        more than one period: re-running a 2026 report after the 2027 rate
        landed must still produce the 2026 number (DEC-121).

        Taking "the first row naming this scheme" would silently pick whichever
        period happens to sit earlier in the file. That is exactly the class of
        bug this module exists to prevent.
        """
        if not manual_override:
            return auto
        if as_of is None:
            return SchemeResolution(
                manual_override, None, "Manual:NoEffectiveDate"
            )

        matches = [
            row
            for row in effective_rows(self._rows, as_of)
            if row.get("scheme") == manual_override
        ]
        if not matches:
            return SchemeResolution(manual_override, None, "Manual:UnknownScheme")

        rates = {Decimal(str(row["rate"])) for row in matches}
        if len(rates) > 1:
            raise AmbiguousSchemeConfigError(
                f"Scheme {manual_override!r} có {len(rates)} tỉ lệ khác nhau "
                f"cùng hiệu lực ngày {as_of}: {sorted(rates)}. "
                "Engine không tự chọn — sửa cấu hình cho rõ ràng."
            )
        return SchemeResolution(manual_override, rates.pop(), "Manual")
