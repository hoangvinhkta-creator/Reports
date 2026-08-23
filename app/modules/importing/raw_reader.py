"""Read the raw sales book `.xlsx` into immutable `RawRow` records.

Layout confirmed against the real file in `docs/analysis/01_DATA_MAPPING.md`
§1–2: header sits on row 4, row 5 carries a secondary description line that
must be skipped, and data starts on row 6. `pandas.read_excel` defaults would
misread row 1 as the header — this reader does not use pandas for that
reason; it reads the sheet directly with `openpyxl`.
"""

from __future__ import annotations

import hashlib
import unicodedata
from datetime import date, datetime
from pathlib import Path
from typing import Optional

import openpyxl

from app.modules.domain.models import RawRow
from app.modules.domain.money import to_decimal

HEADER_ROW = 4
FIRST_DATA_ROW = 6

# 0-based column positions in "SỔ CHI TIẾT BÁN HÀNG", confirmed against the
# real file (docs/analysis/01_DATA_MAPPING.md §2; tools/analysis/extract_evidence.py).
COLUMNS = {
    "date": 0,
    "order_id": 1,
    "note": 2,
    "product": 3,
    "customer_code": 4,
    "customer": 5,
    "address": 6,
    "phone": 7,
    "qty": 8,
    "unit_price": 9,
    "sales": 10,
    "discount": 11,
    "employee": 12,
    "shipper": 13,
    "trip_pay": 14,
    "imei": 15,
    "profit": 16,
}


def _normalize_text(value: object) -> Optional[str]:
    if value is None:
        return None
    text = unicodedata.normalize("NFC", str(value)).strip()
    return text or None


def _to_date(value: object) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    raise TypeError(f"Unexpected date cell value: {value!r}")


def _row_hash(values: tuple) -> str:
    """Stable hash of one raw row's values, for re-import deduplication."""
    canonical = "\x1f".join("" if v is None else str(v) for v in values)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def read_raw_rows(path: Path) -> list[RawRow]:
    """Read every data row of the raw sales book into `RawRow` records.

    A row with no `OrderID` (Số BH) is skipped — it carries no data to
    import. Every other row is kept, including ones with missing employee,
    quantity, or price; those become Review Queue items downstream
    (TASK-110), never a silent drop here.
    """
    workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        sheet = workbook.active
        rows: list[RawRow] = []
        for row_number, values in enumerate(
            sheet.iter_rows(min_row=FIRST_DATA_ROW, values_only=True),
            start=FIRST_DATA_ROW,
        ):
            order_id = _normalize_text(values[COLUMNS["order_id"]])
            if not order_id:
                continue

            rows.append(
                RawRow(
                    source_file=path.name,
                    source_sheet=sheet.title,
                    source_row=row_number,
                    row_hash=_row_hash(values),
                    date=_to_date(values[COLUMNS["date"]]),
                    order_id=order_id,
                    note_raw=_normalize_text(values[COLUMNS["note"]]),
                    product_raw=_normalize_text(values[COLUMNS["product"]]),
                    customer_code=_normalize_text(values[COLUMNS["customer_code"]]),
                    customer=_normalize_text(values[COLUMNS["customer"]]),
                    address=_normalize_text(values[COLUMNS["address"]]),
                    phone=_normalize_text(values[COLUMNS["phone"]]),
                    quantity=to_decimal(values[COLUMNS["qty"]]),
                    sell_price=to_decimal(values[COLUMNS["unit_price"]]),
                    total_sales_raw=to_decimal(values[COLUMNS["sales"]]),
                    discount=to_decimal(values[COLUMNS["discount"]]),
                    employee_raw=_normalize_text(values[COLUMNS["employee"]]),
                    shipper_raw=_normalize_text(values[COLUMNS["shipper"]]),
                    delivery_cost=to_decimal(values[COLUMNS["trip_pay"]]),
                    imei=_normalize_text(values[COLUMNS["imei"]]),
                    source_profit=to_decimal(values[COLUMNS["profit"]]),
                )
            )
        return rows
    finally:
        workbook.close()
