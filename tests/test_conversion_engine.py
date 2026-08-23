from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional

from app.modules.conversion.conversion_engine import apply_conversion_schemes
from app.modules.conversion.scheme_resolver import ConversionSchemeResolver
from app.modules.domain.models import (
    DIEN_MAY,
    GIA_DUNG,
    PERSONAL,
    PRODUCT_GROUP_SOURCE_AUTO,
    PRODUCT_GROUP_SOURCE_DEFAULT,
    PRODUCT_GROUP_SOURCE_MANUAL,
    Order,
)
from app.modules.importing.normalizer import normalize_line
from app.modules.product.product_group import DefaultProductGroupProvider
from tests.factories import make_raw_row


def _line(product_raw="Máy giặt Test-1", employee="Vinh", group="NOI_THANH"):
    line = normalize_line(make_raw_row(product_raw=product_raw))
    line.employee_normalized = employee
    line.employee_group = group
    line.lead_source_final = PERSONAL
    return line


def _order(lines):
    return Order(
        order_id="BH0001",
        date=date(2026, 1, 15),
        employee_raw="raw",
        employee_normalized=lines[0].employee_normalized,
        employee_mapping_status="mapped",
        lines=lines,
    )


def _run(orders, config_dir, provider=None):
    resolver = ConversionSchemeResolver.from_yaml(
        config_dir / "conversion_rates.yaml"
    )
    return apply_conversion_schemes(
        orders, resolver, provider or DefaultProductGroupProvider()
    )


def test_phase1_default_is_dien_may_with_default_provenance(config_dir):
    line = _line()
    _run([_order([line])], config_dir)
    assert line.product_group_final == DIEN_MAY
    assert line.product_group_source_of_value == PRODUCT_GROUP_SOURCE_DEFAULT
    assert line.product_group_auto is None
    assert line.conversion_rate_final == Decimal("0.020")


def test_manual_tick_changes_group_and_rate_but_rate_comes_from_config(config_dir):
    line = _line()
    line.product_group_manual = GIA_DUNG  # the "☐ Gia dụng" checkbox
    _run([_order([line])], config_dir)
    assert line.product_group_final == GIA_DUNG
    assert line.product_group_source_of_value == PRODUCT_GROUP_SOURCE_MANUAL
    assert line.conversion_scheme_final == "GIA_DUNG_8"
    assert line.conversion_rate_final == Decimal("0.080")


def test_default_and_manual_provenance_are_distinguishable(config_dir):
    defaulted = _line()
    ticked = _line()
    ticked.product_group_manual = DIEN_MAY  # same VALUE, different provenance
    _run([_order([defaulted]), _order([ticked])], config_dir)
    assert defaulted.product_group_final == ticked.product_group_final == DIEN_MAY
    assert defaulted.product_group_source_of_value == PRODUCT_GROUP_SOURCE_DEFAULT
    assert ticked.product_group_source_of_value == PRODUCT_GROUP_SOURCE_MANUAL


class _StubProductGroupProvider:
    """A future auto-classifier, injected without touching the engine."""

    def lookup(self, product_raw: Optional[str], sale_date):
        return GIA_DUNG if product_raw == "Lò vi sóng Test" else None


def test_auto_provider_is_pluggable_and_recorded_as_auto(config_dir):
    auto = _line(product_raw="Lò vi sóng Test")
    plain = _line(product_raw="Máy giặt Test-1")
    _run([_order([auto]), _order([plain])], config_dir, _StubProductGroupProvider())

    assert auto.product_group_final == GIA_DUNG
    assert auto.product_group_source_of_value == PRODUCT_GROUP_SOURCE_AUTO
    assert auto.conversion_rate_final == Decimal("0.080")

    assert plain.product_group_final == DIEN_MAY
    assert plain.product_group_source_of_value == PRODUCT_GROUP_SOURCE_DEFAULT
    assert plain.conversion_rate_final == Decimal("0.020")


def test_manual_beats_auto_provider(config_dir):
    line = _line(product_raw="Lò vi sóng Test")
    line.product_group_manual = DIEN_MAY  # a person overrides the classifier
    _run([_order([line])], config_dir, _StubProductGroupProvider())
    assert line.product_group_final == DIEN_MAY
    assert line.product_group_source_of_value == PRODUCT_GROUP_SOURCE_MANUAL
    assert line.conversion_rate_final == Decimal("0.020")


def test_one_order_two_product_groups_gets_two_schemes(config_dir):
    # ADR-106: the reason ConversionScheme is line-level. 118 real OrderIDs
    # carry both kinds; one scheme per order would misprice every one of them.
    dien_may = _line(product_raw="Tủ lạnh Test")
    gia_dung = _line(product_raw="Nồi cơm Test")
    gia_dung.product_group_manual = GIA_DUNG
    order = _order([dien_may, gia_dung])

    _run([order], config_dir)

    assert dien_may.conversion_scheme_final == "NOI_THANH_2"
    assert dien_may.conversion_rate_final == Decimal("0.020")
    assert gia_dung.conversion_scheme_final == "GIA_DUNG_8"
    assert gia_dung.conversion_rate_final == Decimal("0.080")
    assert len({line.conversion_scheme_final for line in order.lines}) == 2


def test_standard_sales_line_marked_gia_dung_keeps_five_point_five(config_dir):
    line = _line(employee="Ly", group="STANDARD_SALES")
    line.product_group_manual = GIA_DUNG
    _run([_order([line])], config_dir)
    assert line.conversion_scheme_final == "PERSONAL_5_5"
    assert line.conversion_rate_final == Decimal("0.055")


def test_manual_scheme_override_is_recorded_and_does_not_touch_lead_source(config_dir):
    line = _line()
    line.conversion_scheme_manual = "ADS_7_5"
    _run([_order([line])], config_dir)
    assert line.conversion_scheme_final == "ADS_7_5"
    assert line.conversion_rate_final == Decimal("0.075")
    assert line.conversion_scheme_source_of_value == "Manual"
    assert line.conversion_scheme_auto == "NOI_THANH_2"  # auto verdict preserved
    assert line.lead_source_final == PERSONAL  # untouched — independent field
