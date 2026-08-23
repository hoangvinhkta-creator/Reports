from __future__ import annotations

from decimal import Decimal

from app.modules.importing.normalizer import normalize_line
from tests.factories import make_raw_row


def test_total_sales_deducts_discount():
    raw = make_raw_row(
        quantity=Decimal("2"), sell_price=Decimal("300000"), discount=Decimal("50000")
    )
    line = normalize_line(raw)
    assert line.total_sales == Decimal("550000")


def test_total_sales_none_when_quantity_missing():
    raw = make_raw_row(quantity=None)
    line = normalize_line(raw)
    assert line.total_sales is None


def test_total_sales_none_when_price_missing():
    raw = make_raw_row(sell_price=None)
    line = normalize_line(raw)
    assert line.total_sales is None


def test_missing_discount_treated_as_zero():
    raw = make_raw_row(
        quantity=Decimal("1"), sell_price=Decimal("1000000"), discount=None
    )
    line = normalize_line(raw)
    assert line.total_sales == Decimal("1000000")


def test_month_derived_from_date():
    raw = make_raw_row()
    line = normalize_line(raw)
    assert line.month == "2026-01"


def test_month_none_when_date_missing():
    raw = make_raw_row(date_=None)
    line = normalize_line(raw)
    assert line.month is None
