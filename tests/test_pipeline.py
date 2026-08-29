from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

from app.modules.domain.models import (
    ADS,
    MAPPING_STATUS_MAPPED,
    PERSONAL,
    PRICE_SOURCE_HISTORICAL_CONFIRMED_REPORT,
    PRICE_SOURCE_OWNER_MANUAL_LEGACY_CONFIRMATION,
    PRICE_SOURCE_PENDING,
)
from app.modules.product.identity.commands import ConfirmHistoricalEntry
from app.modules.product.identity.registry import (
    ConfirmationAuthority,
    HistoricalConfirmedRegistry,
    HistoricalConfirmedRegistryEntry,
    ManualLegacyConfirmationRef,
    PROVENANCE_OWNER_MANUAL_LEGACY_CONFIRMATION,
    SourceReportRef,
)
from app.modules.product.identity.keys import raw_identity_key
from app.pipeline import run_import


def _historical_registry(
    *, order_id: str, product_raw: str, sale_date: date, price: str
) -> HistoricalConfirmedRegistry:
    """DEC-154 §2/P00: từ S051, đây là cổng DI thật cho giá pre-cutover — thay
    cho `price_provider` (chỉ còn áp cho post-cutover/`date` thiếu, xem
    `app.pipeline._apply_pre_cutover_identity`)."""
    registry = HistoricalConfirmedRegistry()
    entry = HistoricalConfirmedRegistryEntry(
        entry_id=f"HCR-{order_id}",
        sale_date=sale_date,
        order_id=order_id,
        raw_product_identity=product_raw,
        raw_identity_key=raw_identity_key(product_raw),
        confirmed_purchase_price=Decimal(price),
        source_report_ref=SourceReportRef(
            report_id="RPT-TEST", file_name="test.xlsx", content_hash="0" * 64
        ),
        confirmed_by="test",
        confirmed_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        confirmation_authority=ConfirmationAuthority.OWNER,
    )
    registry.append(
        ConfirmHistoricalEntry(
            actor_id="test",
            client_request_id=f"req-{order_id}",
            expected_version=0,
            entry_id=entry.entry_id,
            entry=entry,
        )
    )
    return registry


def _historical_registry_manual_legacy(
    *, order_id: str, product_raw: str, sale_date: date, price: str
) -> HistoricalConfirmedRegistry:
    """Golden #1 vertical delivery session brief §2 — LEGACY DATA GAP: hệ
    thống gốc không giữ lại snapshot lịch sử reopenable. Biến thể
    `_historical_registry()` dùng `ManualLegacyConfirmationRef` thay vì
    `SourceReportRef`."""
    registry = HistoricalConfirmedRegistry()
    entry = HistoricalConfirmedRegistryEntry(
        entry_id=f"HCR-{order_id}",
        sale_date=sale_date,
        order_id=order_id,
        raw_product_identity=product_raw,
        raw_identity_key=raw_identity_key(product_raw),
        confirmed_purchase_price=Decimal(price),
        manual_legacy_confirmation_ref=ManualLegacyConfirmationRef(
            original_system="Tracking",
            reason="hệ thống gốc không giữ lại snapshot lịch sử reopenable",
        ),
        provenance=PROVENANCE_OWNER_MANUAL_LEGACY_CONFIRMATION,
        confirmed_by="test",
        confirmed_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        confirmation_authority=ConfirmationAuthority.OWNER,
    )
    registry.append(
        ConfirmHistoricalEntry(
            actor_id="test",
            client_request_id=f"req-{order_id}-manual",
            expected_version=0,
            entry_id=entry.entry_id,
            entry=entry,
        )
    )
    return registry


def test_manual_legacy_confirmation_wired_end_to_end_through_run_import(
    synthetic_raw_path, config_dir
):
    """Golden #1 session brief §2 — provenance mới phải chảy nguyên vẹn từ
    registry entry tới `WorkingLine.price_source` qua production entry point
    thật (`run_import`), không bị gắn nhầm nhãn `HISTORICAL_CONFIRMED_REPORT`.
    """
    registry = _historical_registry_manual_legacy(
        order_id="BH0001",
        product_raw="Máy giặt Test-1",
        sale_date=date(2026, 1, 15),
        price="7000000",
    )
    result = run_import(
        synthetic_raw_path, config_dir=config_dir, identity_registry=registry
    )
    order = _order(result, "BH0001")
    line = order.lines[0]
    assert line.accounting_purchase_price == Decimal("7000000")
    assert line.price_source == PRICE_SOURCE_OWNER_MANUAL_LEGACY_CONFIRMATION
    assert line.price_source != PRICE_SOURCE_HISTORICAL_CONFIRMED_REPORT
    assert line.accounting_profit == (line.sell_price - Decimal("7000000")) * line.quantity


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
    # DEC-127 §1: Mr Vinh keeps his own identity; NOI_THANH is his group.
    assert order.employee_normalized == "Vinh"
    assert order.lines[0].employee_group == "NOI_THANH"
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


def test_custom_price_provider_injected_without_touching_price_engine(
    synthetic_raw_path, config_dir
):
    # BH0001 (2026-01-15) is pre-cutover (DEC-154 CUTOVER_DATE=2026-09-01):
    # since S051, its price authority is `HistoricalConfirmedRegistry`, not
    # `PriceProvider` (DEC-154 §2/P00 — bypasses PriceProvider entirely).
    registry = _historical_registry(
        order_id="BH0001",
        product_raw="Máy giặt Test-1",
        sale_date=date(2026, 1, 15),
        price="999000",
    )
    result = run_import(
        synthetic_raw_path, config_dir=config_dir, identity_registry=registry
    )
    order = _order(result, "BH0001")
    assert order.lines[0].accounting_purchase_price == Decimal("999000")
    assert order.lines[0].price_source == PRICE_SOURCE_HISTORICAL_CONFIRMED_REPORT

    # Unmatched product in the same run stays Pending — the registry is real,
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
    # BH0001 is pre-cutover — see
    # test_custom_price_provider_injected_without_touching_price_engine.
    registry = _historical_registry(
        order_id="BH0001",
        product_raw="Máy giặt Test-1",
        sale_date=date(2026, 1, 15),
        price="999000",
    )
    result = run_import(
        synthetic_raw_path, config_dir=config_dir, identity_registry=registry
    )
    order = _order(result, "BH0001")
    line = order.lines[0]
    assert line.accounting_purchase_price == Decimal("999000")
    assert line.accounting_profit == (line.sell_price - Decimal("999000")) * line.quantity


def test_conversion_scheme_resolved_per_line_in_default_run(
    synthetic_raw_path, config_dir
):
    result = run_import(synthetic_raw_path, config_dir=config_dir)

    # Channel seller: NOI_THANH group, Điện máy by default -> 2%.
    channel = _order(result, "BH0006")
    assert channel.lines[0].employee_group == "NOI_THANH"
    assert channel.lines[0].conversion_scheme_final == "NOI_THANH_2"
    assert channel.lines[0].conversion_rate_final == Decimal("0.020")

    # Standard seller, PERSONAL -> 5.5%.
    personal = _order(result, "BH0001")
    assert personal.lines[0].employee_group == "STANDARD_SALES"
    assert personal.lines[0].conversion_rate_final == Decimal("0.055")

    # ADS order -> 7.5%, on every line of the order.
    ads = _order(result, "BH0002")
    assert all(
        line.conversion_rate_final == Decimal("0.075") for line in ads.lines
    )


def test_every_line_defaults_to_dien_may_with_visible_provenance(
    synthetic_raw_path, config_dir
):
    # Phase 1 has no auto-classification: the fallback must be visible as a
    # fallback, not look like a decision somebody made (ADR-106 §5).
    result = run_import(synthetic_raw_path, config_dir=config_dir)
    lines = [line for order in result.orders for line in order.lines]
    assert lines
    assert all(line.product_group_final == "DIEN_MAY" for line in lines)
    assert all(
        line.product_group_source_of_value == "DEFAULT" for line in lines
    )


def test_unmapped_employee_line_gets_no_rate_at_all(synthetic_raw_path, config_dir):
    # DEC-127 §8: an unconfirmed seller goes to the review queue. The line must
    # carry NO rate — not the universal 5.5%, not anyone else's.
    result = run_import(synthetic_raw_path, config_dir=config_dir)
    order = _order(result, "BH0005")  # employee not in employees.yaml
    line = order.lines[0]
    assert line.employee_group is None
    assert line.conversion_scheme_final == "Unresolved"
    assert line.conversion_rate_final is None
    assert line.conversion_scheme_source_of_value == "Unresolved:UnmappedEmployee"
    assert line in result.unmapped_lines  # routed to review
