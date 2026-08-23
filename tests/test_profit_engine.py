from __future__ import annotations

from decimal import Decimal

from app.modules.importing.normalizer import normalize_line
from app.modules.profit.profit_engine import apply_accounting_profit, compute_accounting_profit
from tests.factories import make_raw_row


def test_computes_profit_when_price_known():
    line = normalize_line(
        make_raw_row(quantity=Decimal("2"), sell_price=Decimal("1000000"))
    )
    line.accounting_purchase_price = Decimal("700000")
    apply_accounting_profit([line])
    assert line.accounting_profit == Decimal("600000")


def test_pending_purchase_price_leaves_profit_none_not_zero():
    line = normalize_line(make_raw_row())
    assert line.accounting_purchase_price is None  # Pending (TASK-105 default)
    apply_accounting_profit([line])
    assert line.accounting_profit is None


def test_missing_quantity_leaves_profit_none():
    line = normalize_line(make_raw_row(quantity=None))
    line.accounting_purchase_price = Decimal("700000")
    apply_accounting_profit([line])
    assert line.accounting_profit is None


def test_missing_sell_price_leaves_profit_none():
    line = normalize_line(make_raw_row(sell_price=None))
    line.accounting_purchase_price = Decimal("700000")
    apply_accounting_profit([line])
    assert line.accounting_profit is None


def test_profit_ignores_discount_and_kpi_adjustment_fields():
    # AccountingProfit has no Discount term and no KpiAdjustment term
    # (DEC-126 điểm 1) — only SellPrice, AccountingPurchasePrice, Quantity.
    line = normalize_line(
        make_raw_row(
            quantity=Decimal("1"),
            sell_price=Decimal("1000000"),
            discount=Decimal("999999"),
        )
    )
    line.accounting_purchase_price = Decimal("400000")
    apply_accounting_profit([line])
    assert line.accounting_profit == Decimal("600000")


def test_applies_to_every_line_in_batch():
    lines = [
        normalize_line(make_raw_row(order_id="BH1", source_row=6)),
        normalize_line(make_raw_row(order_id="BH2", source_row=7)),
    ]
    lines[0].accounting_purchase_price = Decimal("500000")
    apply_accounting_profit(lines)
    assert lines[0].accounting_profit == Decimal("500000")
    assert lines[1].accounting_profit is None  # still Pending


def test_compute_accounting_profit_is_a_pure_function():
    line = normalize_line(
        make_raw_row(quantity=Decimal("3"), sell_price=Decimal("200000"))
    )
    line.accounting_purchase_price = Decimal("150000")
    assert compute_accounting_profit(line) == Decimal("150000")
    assert line.accounting_profit is None  # apply_accounting_profit not called
