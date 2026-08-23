"""Unit tests for the seven Review Queue detectors — TASK-110.

Covers CHECK-110-03 through CHECK-110-07, CHECK-110-10 and CHECK-110-11 at the
rule level. The end-to-end path (real config, real pipeline) is in
`tests/test_validation_pipeline.py`; the TD-001 criteria are in
`tests/test_validation_employee_mapping.py`.

Every `WorkingLine` here is built through the production `normalize_line()` so
the tests exercise the same shape the pipeline produces, not a hand-assembled
approximation of it.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from app.modules.domain.models import (
    ADS,
    MAPPING_STATUS_MAPPED,
    MAPPING_STATUS_UNMAPPED,
    PERSONAL,
    PRICE_SOURCE_PENDING,
    PRICE_SOURCE_PRICE_MASTER,
)
from app.modules.importing.normalizer import normalize_line
from app.modules.orders.order_builder import build_orders
from app.modules.validation.models import (
    CATEGORY_DUPLICATE,
    CATEGORY_MISSING,
    CATEGORY_MISSING_PURCHASE_PRICE,
    CATEGORY_ORDER_INCONSISTENCY,
    CATEGORY_SOURCE_CLASSIFICATION,
    CATEGORY_SUSPICIOUS,
    CATEGORY_SUSPICIOUS_ERP,
    DETAIL_EMPLOYEES_FOUND,
    DETAIL_LEGACY_SELECTED,
    DETAIL_RULE,
    DETAIL_SOURCE_ROWS,
    SEVERITY_ERROR,
    SEVERITY_INFO,
    SEVERITY_WARNING,
)
from app.modules.validation.rules import (
    detect_duplicates,
    detect_missing,
    detect_missing_purchase_price,
    detect_order_inconsistency,
    detect_source_classification,
    detect_suspicious,
    detect_suspicious_erp,
)
from tests.factories import make_raw_row

KEYWORDS = ["chi phí vận chuyển", "công lắp đặt", "chênh vat", "phí "]

MISSING_FIELDS = {
    "date": SEVERITY_ERROR,
    "order_id": SEVERITY_ERROR,
    "employee": SEVERITY_ERROR,
    "quantity": SEVERITY_WARNING,
    "total_sales": SEVERITY_WARNING,
}

SUSPICIOUS_RULES = {
    "quantity_not_positive": SEVERITY_WARNING,
    "sell_price_zero": SEVERITY_WARNING,
    "purchase_price_above_sell_price": SEVERITY_ERROR,
    "accounting_profit_negative": SEVERITY_WARNING,
}


def line(*, mapped: bool = True, **kwargs):
    """A `WorkingLine` built the way the pipeline builds one."""
    working = normalize_line(make_raw_row(**kwargs))
    if mapped:
        working.employee_normalized = "Ly"
        working.employee_mapping_status = MAPPING_STATUS_MAPPED
        working.employee_group = "STANDARD_SALES"
    return working


def rules_of(items):
    return sorted(item.details.get(DETAIL_RULE) for item in items)


# ------------------------------------------------------- CHECK-110-04 Missing

def test_missing_fires_once_per_missing_field():
    lines = [
        line(source_row=6),
        line(source_row=7, date_=None),
        line(source_row=8, quantity=None),
        line(source_row=9, order_id="", quantity=None),
    ]
    items = detect_missing(lines, MISSING_FIELDS)

    # row 7: date. row 8: quantity + total_sales (no qty => cannot compute).
    # row 9: order_id + quantity + total_sales.
    assert len(items) == 6
    assert rules_of([i for i in items if i.source_row == 7]) == ["date"]
    assert rules_of([i for i in items if i.source_row == 8]) == [
        "quantity",
        "total_sales",
    ]
    assert rules_of([i for i in items if i.source_row == 9]) == [
        "order_id",
        "quantity",
        "total_sales",
    ]
    assert all(item.category == CATEGORY_MISSING for item in items)


def test_missing_employee_counts_unmapped_not_merely_absent_name():
    unmapped = line(mapped=False, source_row=6)
    unmapped.employee_mapping_status = MAPPING_STATUS_UNMAPPED
    items = detect_missing([unmapped], {"employee": SEVERITY_ERROR})
    assert len(items) == 1
    assert items[0].severity == SEVERITY_ERROR


def test_missing_carries_back_reference_not_customer_data():
    items = detect_missing([line(source_row=6, date_=None)], MISSING_FIELDS)
    item = items[0]
    assert item.source_file == "synthetic_raw_sample.xlsx"
    assert item.source_row == 6
    assert "Khách Test" not in item.message
    assert "0900000000" not in item.message


# ------------------------------------- CHECK-110-03 Missing purchase price

def test_pending_purchase_price_collapses_to_one_aggregate_item():
    """DEC-128 §1 — one item carrying N, never N items."""
    lines = [line(source_row=6 + i) for i in range(25)]
    for working in lines:
        working.price_source = PRICE_SOURCE_PENDING

    items = detect_missing_purchase_price(lines, SEVERITY_INFO, aggregate=True)

    assert len(items) == 1
    assert items[0].affected_count == 25
    assert items[0].category == CATEGORY_MISSING_PURCHASE_PRICE
    assert "25" in items[0].message


def test_aggregate_false_restores_per_row_for_task_401():
    lines = [line(source_row=6 + i) for i in range(3)]
    items = detect_missing_purchase_price(lines, SEVERITY_INFO, aggregate=False)
    assert len(items) == 3
    assert {item.source_row for item in items} == {6, 7, 8}


def test_no_pending_lines_means_no_item_at_all():
    working = line(source_row=6)
    working.price_source = PRICE_SOURCE_PRICE_MASTER
    assert detect_missing_purchase_price([working], SEVERITY_INFO, True) == []


# ---------------------------------------------------- CHECK-110-05 Suspicious

def test_computed_profit_rules_stay_dormant_while_price_is_pending():
    """Phase 1: no Price Master, so these two rules have no operand.

    Zero findings here is the rule written correctly and waiting, not the rule
    forgotten — the companion test below proves it fires the moment a real
    price arrives.
    """
    lines = [line(source_row=6), line(source_row=7)]
    for working in lines:
        assert working.accounting_purchase_price is None
        assert working.accounting_profit is None

    items = detect_suspicious(lines, SUSPICIOUS_RULES, SEVERITY_INFO, KEYWORDS)
    fired = rules_of(items)
    assert "purchase_price_above_sell_price" not in fired
    assert "accounting_profit_negative" not in fired


def test_computed_profit_rules_fire_once_a_real_price_exists():
    working = line(source_row=6, sell_price=Decimal("1000"))
    working.accounting_purchase_price = Decimal("1500")
    working.accounting_profit = Decimal("-500")

    items = detect_suspicious([working], SUSPICIOUS_RULES, SEVERITY_INFO, KEYWORDS)
    fired = rules_of(items)
    assert "purchase_price_above_sell_price" in fired
    assert "accounting_profit_negative" in fired


def test_quantity_and_sell_price_rules_use_configured_severity():
    working = line(source_row=6, quantity=Decimal("0"), sell_price=Decimal("0"))
    items = detect_suspicious([working], SUSPICIOUS_RULES, SEVERITY_INFO, KEYWORDS)
    assert rules_of(items) == ["quantity_not_positive", "sell_price_zero"]
    assert {item.severity for item in items} == {SEVERITY_WARNING}


def test_a_rule_absent_from_config_simply_does_not_fire():
    working = line(source_row=6, quantity=Decimal("0"))
    items = detect_suspicious([working], {"sell_price_zero": SEVERITY_WARNING},
                              SEVERITY_INFO, KEYWORDS)
    assert items == []


# --------------------------------------------------- CHECK-110-07 Non-product

def test_non_product_line_is_downgraded_but_real_product_is_not():
    """DEC-128 §3 — 1.261 legitimate rows must not drown the real findings."""
    shipping = line(
        source_row=6, product_raw="Chi phí vận chuyển", quantity=Decimal("0")
    )
    product = line(source_row=7, product_raw="Máy giặt Test-1", quantity=Decimal("0"))

    items = detect_suspicious(
        [shipping, product], SUSPICIOUS_RULES, SEVERITY_INFO, KEYWORDS
    )
    by_row = {item.source_row: item.severity for item in items}
    assert by_row[6] == SEVERITY_INFO
    assert by_row[7] == SEVERITY_WARNING


@pytest.mark.parametrize(
    "product_raw",
    ["Chi phí lắp đặt", "Chi phí giao hộ 65C6K x1", "Phí đổi trả", "CHÊNH VAT 25%"],
)
def test_keyword_match_is_case_insensitive_and_covers_measured_variants(product_raw):
    working = line(source_row=6, product_raw=product_raw, quantity=Decimal("0"))
    items = detect_suspicious([working], SUSPICIOUS_RULES, SEVERITY_INFO, KEYWORDS)
    assert [item.severity for item in items] == [SEVERITY_INFO]


# ------------------------------------------------- CHECK-110-06 Suspicious ERP

def test_erp_negative_profit_is_its_own_category_never_merged():
    working = line(source_row=6, source_profit=Decimal("-250000"))

    erp = detect_suspicious_erp([working], SEVERITY_INFO, SEVERITY_INFO, KEYWORDS)
    computed = detect_suspicious([working], SUSPICIOUS_RULES, SEVERITY_INFO, KEYWORDS)

    assert len(erp) == 1
    assert erp[0].category == CATEGORY_SUSPICIOUS_ERP
    assert CATEGORY_SUSPICIOUS_ERP not in {item.category for item in computed}
    assert "CHƯA kiểm chứng" in erp[0].message


def test_erp_rule_ignores_zero_and_positive_profit():
    lines = [
        line(source_row=6, source_profit=Decimal("0")),
        line(source_row=7, source_profit=Decimal("1")),
        line(source_row=8, source_profit=None),
    ]
    assert detect_suspicious_erp(lines, SEVERITY_INFO, SEVERITY_INFO, KEYWORDS) == []


# ------------------------------------------ CHECK-110-09 Order inconsistency

def _two_employee_order():
    first = line(source_row=6, order_id="BH9001")
    second = line(source_row=7, order_id="BH9001")
    second.employee_raw = "Đức Kiên - Tân Á 0867666533"
    second.employee_normalized = "Kiên"
    return build_orders([first, second])


def test_multi_employee_order_is_detected():
    orders = _two_employee_order()
    items = detect_order_inconsistency(orders, SEVERITY_ERROR, SEVERITY_WARNING)
    assert len(items) == 1
    assert items[0].category == CATEGORY_ORDER_INCONSISTENCY
    assert items[0].order_id == "BH9001"


def test_multi_employee_finding_carries_the_provenance_the_owner_required():
    """Ownership stays an open business decision, so the finding must carry
    everything a later decision needs: the OrderID, the identities found, the
    source rows, and who legacy `order_builder` currently picks."""
    items = detect_order_inconsistency(
        _two_employee_order(), SEVERITY_ERROR, SEVERITY_WARNING
    )
    details = items[0].details

    assert items[0].order_id == "BH9001"
    assert details[DETAIL_EMPLOYEES_FOUND] == "Kiên | Ly"
    assert details[DETAIL_LEGACY_SELECTED] == "Ly"
    assert details[DETAIL_SOURCE_ROWS] == "6, 7"
    assert "legacy" in items[0].message.lower()


def test_unmapped_line_beside_a_mapped_one_is_still_an_inconsistency():
    """The worst case: an unmapped person's revenue landing on whoever came
    first. Comparing only mapped names would hide exactly this."""
    first = line(source_row=6, order_id="BH9002")
    second = line(mapped=False, source_row=7, order_id="BH9002")
    second.employee_raw = "Thảo Linh 0900000001"

    items = detect_order_inconsistency(
        build_orders([first, second]), SEVERITY_ERROR, SEVERITY_WARNING
    )
    assert len(items) == 1
    assert "chưa map" in items[0].details[DETAIL_EMPLOYEES_FOUND]


def test_consistent_order_produces_nothing():
    first = line(source_row=6, order_id="BH9003")
    second = line(source_row=7, order_id="BH9003")
    assert detect_order_inconsistency(
        build_orders([first, second]), SEVERITY_ERROR, SEVERITY_WARNING
    ) == []


def test_mixed_dates_on_one_order_are_reported_separately():
    first = line(source_row=6, order_id="BH9004", date_=date(2026, 1, 15))
    second = line(source_row=7, order_id="BH9004", date_=date(2026, 1, 16))
    items = detect_order_inconsistency(
        build_orders([first, second]), SEVERITY_ERROR, SEVERITY_WARNING
    )
    assert len(items) == 1
    assert items[0].severity == SEVERITY_WARNING


# ------------------------------------- CHECK-110-10 Source classification

def test_source_classification_only_fires_on_a_real_disagreement():
    orders = build_orders([line(source_row=6, order_id="BH9005")])
    order = orders[0]

    order.lead_source_auto = PERSONAL
    order.lead_source_manual = None
    assert detect_source_classification(orders, SEVERITY_WARNING) == []

    order.lead_source_manual = PERSONAL
    assert detect_source_classification(orders, SEVERITY_WARNING) == []

    order.lead_source_manual = ADS
    items = detect_source_classification(orders, SEVERITY_WARNING)
    assert len(items) == 1
    assert items[0].category == CATEGORY_SOURCE_CLASSIFICATION
    assert ADS in items[0].message


# ------------------------------------------------------ CHECK-110-11 Duplicate

def test_identical_rows_are_flagged_once_as_a_warning():
    first = line(source_row=6, row_hash="same")
    second = line(source_row=7, row_hash="same")
    third = line(source_row=8, row_hash="other")

    items = detect_duplicates([first, second, third], SEVERITY_WARNING)

    assert len(items) == 1
    assert items[0].category == CATEGORY_DUPLICATE
    assert items[0].severity == SEVERITY_WARNING
    assert items[0].affected_count == 2
    assert items[0].details[DETAIL_SOURCE_ROWS] == "6, 7"


def test_rows_differing_by_one_character_are_not_duplicates():
    first = line(source_row=6, row_hash="abc123")
    second = line(source_row=7, row_hash="abc124")
    assert detect_duplicates([first, second], SEVERITY_WARNING) == []
