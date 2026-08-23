from __future__ import annotations

from decimal import Decimal

from app.modules.importing.normalizer import normalize_line
from app.modules.orders.order_builder import build_orders
from tests.factories import make_raw_row


def test_groups_multi_line_order():
    lines = [
        normalize_line(make_raw_row(order_id="BH9001", source_row=6, sell_price=Decimal("1000000"))),
        normalize_line(make_raw_row(order_id="BH9001", source_row=7, sell_price=Decimal("500000"))),
        normalize_line(make_raw_row(order_id="BH9002", source_row=8, sell_price=Decimal("200000"))),
    ]
    orders = build_orders(lines)
    by_id = {order.order_id: order for order in orders}

    assert len(orders) == 2
    assert by_id["BH9001"].line_count == 2
    assert by_id["BH9002"].line_count == 1


def test_order_total_sales_sums_lines():
    lines = [
        normalize_line(make_raw_row(order_id="BH9003", source_row=6, quantity=Decimal("1"), sell_price=Decimal("300000"))),
        normalize_line(make_raw_row(order_id="BH9003", source_row=7, quantity=Decimal("1"), sell_price=Decimal("200000"))),
    ]
    orders = build_orders(lines)
    assert orders[0].total_sales == Decimal("500000")


def test_order_takes_first_line_employee_and_date():
    lines = [
        normalize_line(make_raw_row(order_id="BH9004", source_row=6, employee_raw="Vũ Hạnh Ly 0868345633")),
    ]
    orders = build_orders(lines)
    assert orders[0].employee_raw == "Vũ Hạnh Ly 0868345633"
    assert orders[0].date == lines[0].date
