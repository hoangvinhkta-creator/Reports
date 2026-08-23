"""Test-only helpers to build domain objects without touching real files.

DEC-108: real sample workbooks are never committed. Every value here is
synthetic — invented names/phone numbers for structural testing, not derived
from any real customer record.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional

from app.modules.domain.models import RawRow

_DEFAULT_DATE = date(2026, 1, 15)


def make_raw_row(
    *,
    order_id: str = "BH0001",
    source_row: int = 6,
    date_: Optional[date] = _DEFAULT_DATE,
    note_raw: Optional[str] = "Bán hàng Khách Lẻ",
    product_raw: Optional[str] = "Máy giặt Test-1",
    employee_raw: Optional[str] = "Vũ Hạnh Ly 0868345633",
    quantity: Optional[Decimal] = Decimal("1"),
    sell_price: Optional[Decimal] = Decimal("1000000"),
    total_sales_raw: Optional[Decimal] = Decimal("1000000"),
    discount: Optional[Decimal] = Decimal("0"),
    source_profit: Optional[Decimal] = Decimal("100000"),
    row_hash: Optional[str] = None,
) -> RawRow:
    return RawRow(
        source_file="synthetic_raw_sample.xlsx",
        source_sheet="SỔ CHI TIẾT BÁN HÀNG",
        source_row=source_row,
        row_hash=row_hash or f"hash-{order_id}-{source_row}",
        date=date_,
        order_id=order_id,
        note_raw=note_raw,
        product_raw=product_raw,
        customer_code="KH0001",
        customer="Khách Test",
        address="123 Đường Test",
        phone="0900000000",
        quantity=quantity,
        sell_price=sell_price,
        total_sales_raw=total_sales_raw,
        discount=discount,
        employee_raw=employee_raw,
        shipper_raw="Shipper Test",
        delivery_cost=Decimal("50000"),
        imei=None,
        source_profit=source_profit,
    )
