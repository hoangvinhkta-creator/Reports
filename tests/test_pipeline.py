from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional

from app.modules.domain.models import (
    ADS,
    MAPPING_STATUS_MAPPED,
    PERSONAL,
    PRICE_SOURCE_PENDING,
    PRICE_SOURCE_PRICE_MASTER,
)
from app.pipeline import run_import


def test_preview_matches_synthetic_file(synthetic_raw_path, config_dir):
    result = run_import(synthetic_raw_path, config_dir=config_dir)
    assert result.preview.row_count == 8
    assert result.preview.distinct_order_count == 7


def test_seven_orders_built(synthetic_raw_path, config_dir):
    result = run_import(synthetic_raw_path, config_dir=config_dir)
    assert len(result.orders) == 7


def _order(result, order_id):
    return next(o for o in result.orders if o.order_id == order_id)


def test_order_with_ads_line_propagates_to_all_lines(synthetic_raw_path, config_dir):
    result = run_import(synthetic_raw_path, config_dir=config_dir)
    order = _order(result, "BH0002")
    assert order.line_count == 2
    assert order.lead_source_final == ADS
    assert all(line.lead_source_final == ADS for line in order.lines)


def test_tin_phat_defaults_to_ads_without_keyword(synthetic_raw_path, config_dir):
    result = run_import(synthetic_raw_path, config_dir=config_dir)
    order = _order(result, "BH0003")
    assert order.employee_normalized == "Tín Phát"
    assert order.lead_source_final == ADS
    assert "Employee Default" in order.lead_source_source_of_value


def test_normal_order_is_personal(synthetic_raw_path, config_dir):
    result = run_import(synthetic_raw_path, config_dir=config_dir)
    order = _order(result, "BH0001")
    assert order.lead_source_final == PERSONAL


def test_channel_employee_mapped_and_personal(synthetic_raw_path, config_dir):
    result = run_import(synthetic_raw_path, config_dir=config_dir)
    order = _order(result, "BH0006")
    assert order.employee_normalized == "Nội thành"
    assert order.lead_source_final == PERSONAL


def test_discount_deducted_from_total_sales(synthetic_raw_path, config_dir):
    result = run_import(synthetic_raw_path, config_dir=config_dir)
    order = _order(result, "BH0004")
    assert order.total_sales == Decimal("550000")


def test_missing_quantity_leaves_total_sales_none(synthetic_raw_path, config_dir):
    result = run_import(synthetic_raw_path, config_dir=config_dir)
    order = _order(result, "BH0007")
    assert order.lines[0].total_sales is None


def test_unmapped_employee_is_visible_not_dropped(synthetic_raw_path, config_dir):
    result = run_import(synthetic_raw_path, config_dir=config_dir)
    unmapped_orders = {line.order_id for line in result.unmapped_lines}
    assert "BH0005" in unmapped_orders
    # And it must still be present among the built orders — not silently lost.
    order = _order(result, "BH0005")
    assert order.employee_mapping_status != MAPPING_STATUS_MAPPED


def test_default_run_leaves_every_price_pending(synthetic_raw_path, config_dir):
    result = run_import(synthetic_raw_path, config_dir=config_dir)
    all_lines = [line for order in result.orders for line in order.lines]
    assert all_lines  # sanity: fixture actually has lines
    assert all(line.accounting_purchase_price is None for line in all_lines)
    assert all(line.price_source == PRICE_SOURCE_PENDING for line in all_lines)


class _FixedPriceProvider:
    def lookup(self, product_code: Optional[str], sale_date: Optional[date]):
        return Decimal("999000") if product_code == "Máy giặt Test-1" else None


def test_custom_price_provider_injected_without_touching_price_engine(
    synthetic_raw_path, config_dir
):
    result = run_import(
        synthetic_raw_path, config_dir=config_dir, price_provider=_FixedPriceProvider()
    )
    order = _order(result, "BH0001")
    assert order.lines[0].accounting_purchase_price == Decimal("999000")
    assert order.lines[0].price_source == PRICE_SOURCE_PRICE_MASTER

    # Unmatched product in the same run stays Pending — the provider is real,
    # a miss is still a miss, never guessed.
    other_order = _order(result, "BH0004")
    assert other_order.lines[0].accounting_purchase_price is None
    assert other_order.lines[0].price_source == PRICE_SOURCE_PENDING


def test_default_run_leaves_every_accounting_profit_pending(
    synthetic_raw_path, config_dir
):
    # No PriceProvider injected -> every accounting_purchase_price is
    # Pending -> AccountingProfit must stay None too, never 0 (DEC-103).
    result = run_import(synthetic_raw_path, config_dir=config_dir)
    all_lines = [line for order in result.orders for line in order.lines]
    assert all_lines
    assert all(line.accounting_profit is None for line in all_lines)


def test_accounting_profit_computed_when_price_provider_matches(
    synthetic_raw_path, config_dir
):
    result = run_import(
        synthetic_raw_path, config_dir=config_dir, price_provider=_FixedPriceProvider()
    )
    order = _order(result, "BH0001")
    line = order.lines[0]
    assert line.accounting_purchase_price == Decimal("999000")
    assert line.accounting_profit == (line.sell_price - Decimal("999000")) * line.quantity
