"""Raw → Working normalization: derive `month`, deduct `Chiết khấu` (DEC-114).

Universal formula (`03_RULE_CLASSIFICATION.md` §U, verified against 408 raw
rows with a non-zero discount):

    TotalSales = SellPrice * Quantity - Discount

A missing `Quantity` or `SellPrice` means `TotalSales` cannot be computed at
all — it stays `None`, distinct from a computed `0` (03_DATA_MODEL_RULES §5).
A missing `Discount` is treated as no discount (`0`), matching how the raw
file records it: absence and an explicit `0` mean the same business fact
here, unlike quantity/price which are required inputs.
"""

from __future__ import annotations

from decimal import Decimal

from app.modules.domain.models import RawRow, WorkingLine


def normalize_line(raw: RawRow) -> WorkingLine:
    discount = raw.discount if raw.discount is not None else Decimal("0")

    total_sales = None
    if raw.quantity is not None and raw.sell_price is not None:
        total_sales = raw.sell_price * raw.quantity - discount

    month = f"{raw.date.year:04d}-{raw.date.month:02d}" if raw.date else None

    return WorkingLine(
        raw=raw,
        order_id=raw.order_id,
        date=raw.date,
        month=month,
        note_raw=raw.note_raw,
        product_raw=raw.product_raw,
        customer_code=raw.customer_code,
        customer=raw.customer,
        address=raw.address,
        phone=raw.phone,
        quantity=raw.quantity,
        sell_price=raw.sell_price,
        discount=discount,
        total_sales=total_sales,
        employee_raw=raw.employee_raw,
        shipper_raw=raw.shipper_raw,
        delivery_cost=raw.delivery_cost,
        imei=raw.imei,
        source_profit=raw.source_profit,
    )


def normalize_lines(rows: list[RawRow]) -> list[WorkingLine]:
    return [normalize_line(row) for row in rows]
