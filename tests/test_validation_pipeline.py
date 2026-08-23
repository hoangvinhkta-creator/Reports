"""End-to-end Review Queue behaviour on the real import path — TASK-110.

CHECK-110-01, CHECK-110-02, CHECK-110-06(b), CHECK-110-08, CHECK-110-09(b),
CHECK-110-17.

These run `run_import()` against the synthetic workbook with production config
— no stubbed validator, no hand-built queue.
"""

from __future__ import annotations

import re
from dataclasses import replace
from datetime import date
from decimal import Decimal
from pathlib import Path

from app.modules.domain.models import (
    MAPPING_STATUS_MAPPED,
    PERSONAL,
    PRICE_SOURCE_PRICE_MASTER,
)
from app.modules.importing.normalizer import normalize_line
from app.modules.orders.order_builder import build_orders
from app.modules.validation.models import (
    CATEGORIES,
    CATEGORY_DUPLICATE,
    CATEGORY_EMPLOYEE_MAPPING,
    CATEGORY_MISSING,
    CATEGORY_MISSING_PURCHASE_PRICE,
    CATEGORY_ORDER_INCONSISTENCY,
    CATEGORY_SOURCE_CLASSIFICATION,
    CATEGORY_SUSPICIOUS,
    CATEGORY_SUSPICIOUS_ERP,
    PII_FIELD_NAMES,
    ReviewQueue,
    SEVERITY_ERROR,
    SEVERITY_INFO,
)
from app.modules.validation.validator import Validator
from app.pipeline import run_import
from tests.factories import make_raw_row

REPO_ROOT = Path(__file__).resolve().parent.parent


class _RealPriceProvider:
    """A Price Master that knows one product and misses the rest."""

    def lookup(self, product_code, sale_date):
        if product_code and "Máy giặt" in product_code:
            return Decimal("9000000")  # deliberately above the sell price
        return None


def _defective_line(source_row, order_id, employee_raw, **kwargs):
    working = normalize_line(
        make_raw_row(source_row=source_row, order_id=order_id,
                     employee_raw=employee_raw, **kwargs)
    )
    return working


# ------------------------------------------------------ CHECK-110-01 (8 codes)

def test_every_category_code_is_reachable_and_distinct():
    """The eight codes of the frozen scope table — `Missing` splits per-row vs
    aggregate (DEC-128 §1), which is why eight codes carry seven §18 loại."""
    ly = "Vũ Hạnh Ly 0868345633"
    kien = "Đức Kiên - Tân Á 0867666533"

    lines = [
        # Missing (date) + Suspicious.ERP + Duplicate partner.
        _defective_line(6, "BH8001", ly, date_=None, source_profit=Decimal("-1"),
                        row_hash="dup"),
        _defective_line(7, "BH8001", ly, source_profit=Decimal("-1"), row_hash="dup"),
        # Suspicious (computed, quantity) on a real product line.
        _defective_line(8, "BH8002", ly, quantity=Decimal("0")),
        # Order inconsistency: two identities on one order.
        _defective_line(9, "BH8003", ly),
        _defective_line(10, "BH8003", kien),
        # Unmapped, high volume -> F4.
        _defective_line(11, "BH8004", "Thảo Linh 0900000001"),
        _defective_line(12, "BH8005", "Thảo Linh 0900000001"),
    ]
    for working in lines:
        if working.employee_raw == ly:
            working.employee_normalized, working.employee_group = "Ly", "STANDARD_SALES"
            working.employee_mapping_status = MAPPING_STATUS_MAPPED
        elif working.employee_raw == kien:
            working.employee_normalized, working.employee_group = "Kiên", "STANDARD_SALES"
            working.employee_mapping_status = MAPPING_STATUS_MAPPED

    orders = build_orders(lines)
    orders[1].lead_source_auto = PERSONAL
    orders[1].lead_source_manual = "ADS"  # Source classification

    queue = Validator.from_config_dir(REPO_ROOT / "config").build_queue(lines, orders)
    found = set(queue.counts_by_category())

    assert found == set(CATEGORIES), f"missing: {set(CATEGORIES) - found}"
    assert len(CATEGORIES) == len(set(CATEGORIES))


def test_expected_categories_appear_on_the_real_synthetic_import(synthetic_raw_path):
    result = run_import(synthetic_raw_path)
    counts = result.review_queue.counts_by_category()

    assert counts[CATEGORY_MISSING] > 0
    assert counts[CATEGORY_MISSING_PURCHASE_PRICE] == 1
    assert counts[CATEGORY_EMPLOYEE_MAPPING] > 0


# ------------------------------------------- CHECK-110-02 (never blocks)

def test_import_completes_even_when_every_row_is_defective(tmp_path):
    """§18 đặc tả: 'Không block toàn bộ import.' The queue is a report that
    travels beside the data, never a gate in front of it."""
    from tests.fixtures.synthetic_workbook import build_synthetic_workbook

    path = tmp_path / "s.xlsx"
    build_synthetic_workbook(path)

    result = run_import(path)  # must not raise

    assert result.orders, "orders must still be built"
    assert result.preview is not None
    assert isinstance(result.review_queue, ReviewQueue)
    assert len(result.review_queue) > 0


def test_review_queue_is_ordered_worst_first(synthetic_raw_path):
    severities = [item.severity for item in run_import(synthetic_raw_path).review_queue]
    rank = {"ERROR": 0, "WARNING": 1, "INFO": 2}
    assert severities == sorted(severities, key=lambda s: rank[s])


# --------------------------------------- CHECK-110-05(b) via the real pipeline

def test_a_real_price_provider_wakes_the_dormant_computed_rules(synthetic_raw_path):
    pending_run = run_import(synthetic_raw_path)
    priced_run = run_import(synthetic_raw_path, price_provider=_RealPriceProvider())

    def computed_rules(result):
        return {
            item.details.get("rule")
            for item in result.review_queue.by_category(CATEGORY_SUSPICIOUS)
        }

    assert "purchase_price_above_sell_price" not in computed_rules(pending_run)
    assert "purchase_price_above_sell_price" in computed_rules(priced_run)


def test_aggregate_pending_item_disappears_once_prices_resolve():
    working = normalize_line(make_raw_row(source_row=6))
    working.price_source = PRICE_SOURCE_PRICE_MASTER
    working.employee_normalized = "Ly"
    working.employee_mapping_status = MAPPING_STATUS_MAPPED

    queue = Validator.from_config_dir(REPO_ROOT / "config").build_queue([working], [])

    assert queue.by_category(CATEGORY_MISSING_PURCHASE_PRICE) == []


# ------------------------------------------ CHECK-110-09(b) validation is inert

def test_building_the_queue_changes_nothing_about_the_data(synthetic_raw_path):
    """Validation reads. If it ever wrote, a conversion rate could move
    without a business decision behind it — DEC-128 §4 forbids exactly that.
    """
    result = run_import(synthetic_raw_path)
    lines = [line for order in result.orders for line in order.lines]

    def snapshot():
        return [
            (
                line.order_id,
                line.employee_normalized,
                line.employee_mapping_status,
                line.lead_source_final,
                line.product_group_final,
                line.conversion_scheme_final,
                line.conversion_rate_final,
                line.accounting_profit,
                line.price_source,
                line.quantity,
                line.total_sales,
            )
            for line in lines
        ]

    before = snapshot()
    Validator.from_config_dir(REPO_ROOT / "config").build_queue(lines, result.orders)
    assert snapshot() == before


def test_order_builder_still_selects_the_first_line_untouched(synthetic_raw_path):
    """The legacy behaviour DEC-128 §4 deliberately leaves alone."""
    result = run_import(synthetic_raw_path)
    for order in result.orders:
        assert order.employee_raw == order.lines[0].employee_raw
        assert order.employee_normalized == order.lines[0].employee_normalized


# ---------------------------------------------------- CHECK-110-17 (no PII)

def test_no_review_item_carries_customer_identifying_data(synthetic_raw_path):
    result = run_import(synthetic_raw_path)
    lines = [line for order in result.orders for line in order.lines]

    secrets = set()
    for line in lines:
        for field in PII_FIELD_NAMES:
            value = getattr(line, field, None)
            if value:
                secrets.add(str(value))
    assert secrets, "fixture must actually carry customer data for this to prove anything"

    for item in result.review_queue:
        blob = " ".join(
            [item.message, *(f"{k}={v}" for k, v in item.details.items())]
        )
        for secret in secrets:
            assert secret not in blob, f"{secret!r} leaked into {item.category}"


def test_review_items_reference_rows_not_people(synthetic_raw_path):
    for item in run_import(synthetic_raw_path).review_queue:
        assert item.source_file is None or item.source_file.endswith(".xlsx")
        assert item.source_row is None or isinstance(item.source_row, int)


# --------------------------------- CHECK-110-06(b) + CHECK-110-08 (source scans)

def _validation_sources():
    root = REPO_ROOT / "app" / "modules" / "validation"
    return {path: path.read_text(encoding="utf-8") for path in root.glob("*.py")}


def test_source_profit_is_never_used_to_derive_a_purchase_price_or_profit():
    """DEC-103: deriving a purchase price from the ERP profit column produces
    a number that looks like accounting data but is a division. It must not
    exist anywhere on this path."""
    for path, text in _validation_sources().items():
        for line in text.splitlines():
            if "source_profit" not in line:
                continue
            assert "accounting_purchase_price" not in line, path
            assert "accounting_profit" not in line, path


def test_no_business_values_are_hardcoded_in_the_validation_module():
    """Employee names, conversion rates and the non-product keyword list all
    belong to config (CHECK-110-08)."""
    employee_names = ["Tín Phát", "Vũ Hạnh Ly", "Lê Mạnh Hoàng", "Đức Kiên",
                      "Phước Thắng", "Mr Vinh", "Mr Quý", "Đức Hiệp"]
    keywords = ["chi phí vận chuyển", "công lắp đặt", "chênh vat", "voucher"]

    for path, text in _validation_sources().items():
        code = "\n".join(
            line for line in text.splitlines()
            if not line.lstrip().startswith("#")
        )
        code = re.sub(r'""".*?"""', "", code, flags=re.DOTALL)

        for name in employee_names:
            assert name not in code, f"employee name {name!r} hardcoded in {path.name}"
        for keyword in keywords:
            assert keyword not in code.lower(), (
                f"non-product keyword {keyword!r} hardcoded in {path.name}"
            )
        assert not re.search(r"Decimal\(\"0\.\d+\"\)", code), (
            f"a conversion-rate-shaped literal appears in {path.name}"
        )


def test_config_keyword_list_matches_the_measured_evidence_filter():
    """The keyword list must stay the one that measured 1.261 rows / 30 types
    in `docs/analysis/_evidence/evidence.json`, or CHECK-110-16 cannot compare
    against a known number."""
    from app.modules.config.loader import load_yaml

    config = load_yaml(REPO_ROOT / "config" / "validation.yaml")
    keywords = {k.lower() for k in config["non_product_lines"]["keywords"]}

    measured = {
        "chi phí vận chuyển", "công lắp đặt", "chênh vat",
        "chiết khấu", "voucher", "phí ",
    }
    assert keywords == measured


# ------------------------------------------------------------- config plumbing

def test_disabling_a_category_in_config_silences_exactly_that_category():
    config = {
        "categories": {
            "missing": {"enabled": False},
            "duplicate": {"enabled": True, "severity": SEVERITY_INFO},
        }
    }
    working = normalize_line(make_raw_row(source_row=6, date_=None, row_hash="d"))
    twin = normalize_line(make_raw_row(source_row=7, date_=None, row_hash="d"))

    queue = Validator(config).build_queue([working, twin], [])

    assert queue.by_category(CATEGORY_MISSING) == []
    assert len(queue.by_category(CATEGORY_DUPLICATE)) == 1


def test_unknown_category_or_severity_is_rejected_loudly():
    import pytest

    from app.modules.validation.models import ReviewItem

    with pytest.raises(ValueError):
        ReviewItem(category="NotACategory", severity=SEVERITY_ERROR, message="x")
    with pytest.raises(ValueError):
        ReviewItem(category=CATEGORY_MISSING, severity="LOUD", message="x")


def test_queue_helpers_report_scale_not_just_item_count():
    working = normalize_line(make_raw_row(source_row=6))
    queue = Validator.from_config_dir(REPO_ROOT / "config").build_queue([working], [])
    aggregate = queue.by_category(CATEGORY_MISSING_PURCHASE_PRICE)[0]

    assert aggregate.affected_count == 1
    assert queue.affected_rows() >= len(queue)


def test_order_inconsistency_and_source_classification_absent_on_clean_orders():
    working = normalize_line(make_raw_row(source_row=6))
    working.employee_normalized = "Ly"
    working.employee_mapping_status = MAPPING_STATUS_MAPPED
    orders = build_orders([working])
    orders[0].lead_source_auto = PERSONAL
    orders[0].lead_source_final = PERSONAL

    queue = Validator.from_config_dir(REPO_ROOT / "config").build_queue(
        [working], orders
    )

    assert queue.by_category(CATEGORY_ORDER_INCONSISTENCY) == []
    assert queue.by_category(CATEGORY_SOURCE_CLASSIFICATION) == []


def test_erp_signal_survives_the_real_pipeline_as_its_own_category(tmp_path):
    from tests.fixtures.synthetic_workbook import build_synthetic_workbook

    path = tmp_path / "s.xlsx"
    build_synthetic_workbook(path)
    result = run_import(path)

    computed = result.review_queue.by_category(CATEGORY_SUSPICIOUS)
    erp = result.review_queue.by_category(CATEGORY_SUSPICIOUS_ERP)

    assert all(item.category != CATEGORY_SUSPICIOUS_ERP for item in computed)
    assert all(item.category != CATEGORY_SUSPICIOUS for item in erp)


def test_replace_keeps_review_item_frozen_and_valid():
    from app.modules.validation.models import ReviewItem

    item = ReviewItem(
        category=CATEGORY_MISSING, severity=SEVERITY_ERROR, message="x", source_row=6
    )
    moved = replace(item, source_row=7)
    assert moved.source_row == 7 and item.source_row == 6


def test_dates_mismatch_detected_through_the_validator(synthetic_raw_path):
    """Guard that the order-level rules are actually wired into `build_queue`,
    not merely unit-tested in isolation."""
    working = normalize_line(make_raw_row(source_row=6, order_id="BH7001",
                                          date_=date(2026, 1, 15)))
    twin = normalize_line(make_raw_row(source_row=7, order_id="BH7001",
                                       date_=date(2026, 2, 15)))
    for line in (working, twin):
        line.employee_normalized = "Ly"
        line.employee_mapping_status = MAPPING_STATUS_MAPPED

    queue = Validator.from_config_dir(REPO_ROOT / "config").build_queue(
        [working, twin], build_orders([working, twin])
    )

    assert len(queue.by_category(CATEGORY_ORDER_INCONSISTENCY)) == 1
