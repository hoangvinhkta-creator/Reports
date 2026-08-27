"""End-to-end Review Queue behaviour on the real import path — TASK-110.

CHECK-110-01, CHECK-110-02, CHECK-110-06(b), CHECK-110-08, CHECK-110-09(b),
CHECK-110-17.

These run `run_import()` against the synthetic workbook with production config
— no stubbed validator, no hand-built queue.
"""

from __future__ import annotations

import re
from dataclasses import fields, is_dataclass, replace
from datetime import date
from decimal import Decimal
from pathlib import Path

from app.modules.domain.models import (
    MAPPING_STATUS_MAPPED,
    PERSONAL,
    PRICE_SOURCE_PRICE_MASTER,
)
from app.modules.domain.models import WorkingLine
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
    SCOPE_BATCH,
    SCOPE_ORDER,
    SCOPE_ROW,
    SEVERITY_ERROR,
    SEVERITY_INFO,
)
from app.modules.validation.validator import Validator
from app.pipeline import build_working_data, run_import
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

    queue = Validator.from_config_dir(REPO_ROOT / "config")._build(lines, orders)
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

    queue = Validator.from_config_dir(REPO_ROOT / "config")._build([working], [])

    assert queue.by_category(CATEGORY_MISSING_PURCHASE_PRICE) == []


# ------------------------------------------ CHECK-110-09(b) validation is inert

def _freeze(value):
    """A hashable, comparable snapshot of any domain value."""
    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)
    if is_dataclass(value) and not isinstance(value, type):
        return tuple(
            (f.name, _freeze(getattr(value, f.name))) for f in fields(value)
        )
    return repr(value)


def _snapshot(lines, orders):
    """EVERY field of every WorkingLine and Order, by introspection.

    Independent Review #1, Finding 6: the previous version listed 11 fields by
    hand, so a field added later would silently escape the guarantee. Walking
    `dataclasses.fields` means the snapshot cannot drift behind the model.
    `lines` is covered as well as `orders` so a write to a line the order
    graph does not reach is still caught.
    """
    return (_freeze(list(lines)), _freeze(list(orders)))


def test_the_snapshot_actually_covers_every_frozen_field():
    """A guard on the guard: if this ever stops naming a real field, the
    non-mutation test below would be passing vacuously."""
    covered = {f.name for f in fields(WorkingLine)}
    assert {"conversion_rate_final", "conversion_scheme_final", "accounting_profit",
            "lead_source_final", "product_group_final", "employee_normalized",
            "price_source", "quantity", "total_sales", "discount"} <= covered
    assert len(covered) >= 30, f"WorkingLine has {len(covered)} fields"


def test_building_the_queue_changes_nothing_about_the_data(synthetic_raw_path):
    """Validation reads. If it ever wrote, a conversion rate could move
    without a business decision behind it — DEC-128 §4 forbids exactly that.

    **The snapshot is taken before validation has EVER run** (Independent
    Review #2, Finding 4). The previous version called `run_import()`, which
    builds the queue internally, and only then took the "before" picture — so
    a mutation caused by that first pass would already be present on both
    sides and the assertion would happily pass. `build_working_data()` stops
    at step 10, so this really is the pre-validation state, and
    `build_queue()` is then called exactly once.
    """
    working = build_working_data(synthetic_raw_path)

    before = _snapshot(working.lines, working.orders)
    Validator.from_config_dir(REPO_ROOT / "config")._build(
        working.lines, working.orders
    )
    after = _snapshot(working.lines, working.orders)

    assert after == before


def test_the_non_mutation_snapshot_would_actually_catch_a_write(synthetic_raw_path):
    """Falsification: prove the oracle is sensitive, so its passing means
    something. Taken on the same pre-validation state, one deep field is
    mutated by hand and the snapshot must notice."""
    working = build_working_data(synthetic_raw_path)
    before = _snapshot(working.lines, working.orders)

    working.orders[0].lines[0].conversion_rate_final = Decimal("0.99")

    assert _snapshot(working.lines, working.orders) != before


def test_the_oracle_catches_a_mutation_on_a_line_outside_any_order(
    synthetic_raw_path,
):
    """The snapshot covers `lines` as well as `orders`, so a detector that
    wrote to a line the order graph does not reach would still be caught."""
    working = build_working_data(synthetic_raw_path)
    before = _snapshot(working.lines, working.orders)

    working.lines[-1].price_source = "Tampered"

    assert _snapshot(working.lines, working.orders) != before


def test_build_working_data_really_stops_before_the_review_queue(
    synthetic_raw_path,
):
    """If `build_working_data` ever started running validation itself, the
    oracle above would silently go back to snapshotting an 'after' state."""
    working = build_working_data(synthetic_raw_path)

    assert not hasattr(working, "review_queue")
    assert working.lines and working.orders
    # Steps 1–10 did run: conversion resolved, so the state is complete.
    assert any(
        line.conversion_scheme_final is not None
        for order in working.orders
        for line in order.lines
    )


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


def test_keyword_config_expresses_semantics_not_a_historical_count():
    """HD-110-02: the auxiliary-line list is a temporary heuristic, and it must
    NOT be pinned to the 1.261 rows the old regex filter happened to measure.

    So this asserts the *shape* the semantics require — real keywords, no
    trailing-space tricks standing in for a word boundary — and leaves the
    behaviour to `tests/test_validation_text.py`. The previous version of this
    test locked the list to the legacy filter, which is exactly the tuning the
    decision forbids.
    """
    from app.modules.config.loader import load_yaml

    config = load_yaml(REPO_ROOT / "config" / "validation.yaml")
    keywords = config["non_product_lines"]["keywords"]

    assert keywords, "the heuristic needs at least one keyword to do anything"
    for keyword in keywords:
        assert keyword == keyword.strip(), (
            f"{keyword!r} relies on padding; boundaries belong in the matcher"
        )
        assert keyword == keyword.lower(), f"{keyword!r} should be case-folded already"


def test_every_queue_item_from_a_real_import_is_traceable(synthetic_raw_path):
    """Review #1, Finding 6: assert a valid reference per item, rather than
    tolerating items whose references are all None."""
    queue = run_import(synthetic_raw_path).review_queue
    assert len(queue) > 0

    for item in queue:
        assert item.source_file, item
        assert item.source_file.endswith(".xlsx"), item
        assert item.affected_count >= 0, item
        if item.scope == SCOPE_ROW:
            assert isinstance(item.source_row, int), item
        elif item.scope == SCOPE_ORDER:
            assert item.order_id, item
        else:
            assert item.scope == SCOPE_BATCH, item


def _one_row():
    from tests.support.rows import provenance

    return provenance(6)


def test_an_untraceable_item_cannot_even_be_constructed():
    """The invariant is structural, not a convention somebody must remember."""
    import pytest

    from app.modules.validation.models import ReviewItem

    from tests.support.rows import provenance

    # Không có dòng và cũng không có tên file lô: không lần ngược về đâu được.
    with pytest.raises(ValueError, match="source_file"):
        ReviewItem(category=CATEGORY_MISSING, severity=SEVERITY_ERROR,
                   scope=SCOPE_ROW)
    # Có tên file nhưng provenance rỗng: phạm vi dòng mà không có dòng nào.
    with pytest.raises(ValueError, match="source_row"):
        ReviewItem(category=CATEGORY_MISSING, severity=SEVERITY_ERROR,
                   scope=SCOPE_ROW, batch_source_file="s.xlsx")
    with pytest.raises(ValueError, match="order_id"):
        ReviewItem(category=CATEGORY_ORDER_INCONSISTENCY, severity=SEVERITY_ERROR, scope=SCOPE_ORDER,
                   provenance=_one_row())
    with pytest.raises(ValueError, match="scope"):
        ReviewItem(category=CATEGORY_MISSING, severity=SEVERITY_ERROR,
                   scope="galaxy", provenance=_one_row())


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

    queue = Validator(config)._build([working, twin], [])

    assert queue.by_category(CATEGORY_MISSING) == []
    assert len(queue.by_category(CATEGORY_DUPLICATE)) == 1


def test_unknown_category_or_severity_is_rejected_loudly():
    import pytest

    from app.modules.validation.models import ReviewItem

    with pytest.raises(ValueError):
        ReviewItem(category="NotACategory", severity=SEVERITY_ERROR,
                   provenance=_one_row())
    with pytest.raises(ValueError):
        ReviewItem(category=CATEGORY_MISSING, severity="LOUD",
                   provenance=_one_row())


def test_queue_helpers_report_scale_not_just_item_count():
    working = normalize_line(make_raw_row(source_row=6))
    queue = Validator.from_config_dir(REPO_ROOT / "config")._build([working], [])
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

    queue = Validator.from_config_dir(REPO_ROOT / "config")._build(
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
    """`dataclasses.replace` vẫn đi qua `__post_init__`.

    Sau Review #5, `source_row` là property dẫn xuất chứ không còn là field —
    nên cách duy nhất để dời một item sang dòng khác là dời chính provenance
    của nó. Đó đúng là điều mong muốn: số dòng không thể bị sửa rời khỏi tập
    dòng mà item sở hữu.
    """
    from app.modules.validation.models import Diagnostics, ReviewItem
    from tests.support.rows import provenance

    item = ReviewItem(
        category=CATEGORY_MISSING, severity=SEVERITY_ERROR,
        scope=SCOPE_ROW, provenance=provenance(6),
        diagnostics=Diagnostics(rule="date"),
    )
    moved = replace(item, provenance=provenance(7))
    assert moved.source_row == 7 and item.source_row == 6
    assert moved.affected_count == 1


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

    queue = Validator.from_config_dir(REPO_ROOT / "config")._build(
        [working, twin], build_orders([working, twin])
    )

    assert len(queue.by_category(CATEGORY_ORDER_INCONSISTENCY)) == 1
