"""Metadata preview of a raw import, before any normalization (spec §22 step 2).

Reports enough for a human to sanity-check "is this the right file?" before
committing to the rest of the pipeline: row count, date range, raw total
sales, distinct order count, distinct raw employee count. Computed straight
from `RawRow`s — no employee mapping, no discount deduction, no lead-source
classification has happened yet at this point.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional

from app.modules.domain.models import RawRow


@dataclass(frozen=True)
class ImportPreview:
    row_count: int
    distinct_order_count: int
    date_min: Optional[date]
    date_max: Optional[date]
    total_sales_raw: Decimal
    distinct_employee_count: int
    rows_missing_employee: int
    rows_missing_date: int


def build_preview(rows: list[RawRow]) -> ImportPreview:
    dates = [row.date for row in rows if row.date is not None]
    order_ids = {row.order_id for row in rows}
    employees = {row.employee_raw for row in rows if row.employee_raw}

    return ImportPreview(
        row_count=len(rows),
        distinct_order_count=len(order_ids),
        date_min=min(dates) if dates else None,
        date_max=max(dates) if dates else None,
        total_sales_raw=sum(
            (row.total_sales_raw or Decimal("0")) for row in rows
        ),
        distinct_employee_count=len(employees),
        rows_missing_employee=sum(1 for row in rows if not row.employee_raw),
        rows_missing_date=sum(1 for row in rows if row.date is None),
    )
