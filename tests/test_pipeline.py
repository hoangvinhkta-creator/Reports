from __future__ import annotations

from decimal import Decimal

from app.modules.domain.models import ADS, MAPPING_STATUS_MAPPED, PERSONAL
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
