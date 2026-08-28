"""`FilePriceProvider` — TASK-105B Completion Gate (CHECK-105B-01..17).

Canonical contract: `docs/tasks/TASK-105B-file-price-provider.md` (DEC-145 /
`OD-105B-01`, §38 of `docs/tasks/TASK-108B-eligible-costs-owner-definition.md`).
Each test below is annotated with the CHECK ID(s) it evidences.
"""

from __future__ import annotations

import ast
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from app.modules.pricing.file_price_provider import (
    FilePriceProvider,
    InvalidPriceMasterError,
)

_MODULE_PATH = (
    Path(__file__).resolve().parent.parent
    / "app"
    / "modules"
    / "pricing"
    / "file_price_provider.py"
)


def _row(
    product_key: str = "Máy giặt Test-1",
    effective_from: str = "2026-01-01",
    effective_to: str | None = "2026-01-31",
    purchase_price: object = "5000000",
    source: str | None = None,
) -> dict:
    row = {
        "product_key": product_key,
        "effective_from": effective_from,
        "effective_to": effective_to,
        "purchase_price": purchase_price,
    }
    if source is not None:
        row["source"] = source
    return row


# ---------------------------------------------------------------------------
# CHECK-105B-01 — closed interval, both boundary dates lookup-able.
# ---------------------------------------------------------------------------


def test_closed_interval_both_boundaries_match():
    provider = FilePriceProvider([_row()])
    assert provider.lookup("Máy giặt Test-1", date(2026, 1, 1)) == Decimal("5000000")
    assert provider.lookup("Máy giặt Test-1", date(2026, 1, 31)) == Decimal("5000000")


def test_closed_interval_open_record_end_is_still_effective():
    provider = FilePriceProvider(
        [_row(effective_from="2026-01-01", effective_to=None)]
    )
    assert provider.lookup("Máy giặt Test-1", date(2026, 1, 1)) == Decimal("5000000")
    assert provider.lookup("Máy giặt Test-1", date(2030, 1, 1)) == Decimal("5000000")


# ---------------------------------------------------------------------------
# CHECK-105B-02 — overlap, same normalized key -> InvalidPriceMasterError.
# ---------------------------------------------------------------------------


def test_overlapping_periods_same_key_raises():
    rows = [
        _row(effective_from="2026-01-01", effective_to="2026-01-31"),
        _row(effective_from="2026-01-15", effective_to="2026-02-28"),
    ]
    with pytest.raises(InvalidPriceMasterError) as excinfo:
        FilePriceProvider(rows)
    assert excinfo.value.reason == "overlapping_periods"


# ---------------------------------------------------------------------------
# CHECK-105B-03 — >1 record with effective_to blank, same key -> error.
# ---------------------------------------------------------------------------


def test_multiple_open_records_same_key_raises():
    rows = [
        _row(effective_from="2026-01-01", effective_to=None),
        _row(effective_from="2026-02-01", effective_to=None),
    ]
    with pytest.raises(InvalidPriceMasterError) as excinfo:
        FilePriceProvider(rows)
    assert excinfo.value.reason == "multiple_open_records"


# ---------------------------------------------------------------------------
# CHECK-105B-04 — gap between two closed periods -> None, no extension.
# ---------------------------------------------------------------------------


def test_gap_between_periods_is_pending_not_extended():
    rows = [
        _row(effective_from="2026-01-01", effective_to="2026-01-10"),
        _row(effective_from="2026-01-21", effective_to="2026-01-31", purchase_price="6000000"),
    ]
    provider = FilePriceProvider(rows)
    # Inside the gap.
    assert provider.lookup("Máy giặt Test-1", date(2026, 1, 15)) is None
    # The day right after the first period ends must NOT still resolve to it.
    assert provider.lookup("Máy giặt Test-1", date(2026, 1, 11)) is None
    # The day right before the second period starts must NOT resolve to it either.
    assert provider.lookup("Máy giặt Test-1", date(2026, 1, 20)) is None
    # Both real periods still work.
    assert provider.lookup("Máy giặt Test-1", date(2026, 1, 5)) == Decimal("5000000")
    assert provider.lookup("Máy giặt Test-1", date(2026, 1, 25)) == Decimal("6000000")


# ---------------------------------------------------------------------------
# CHECK-105B-05 — sale_date before the first record -> None, no nearest.
# ---------------------------------------------------------------------------


def test_sale_date_before_first_record_is_pending():
    provider = FilePriceProvider(
        [_row(effective_from="2026-01-01", effective_to="2026-01-31")]
    )
    assert provider.lookup("Máy giặt Test-1", date(2025, 12, 31)) is None


def test_unknown_product_is_pending():
    provider = FilePriceProvider([_row()])
    assert provider.lookup("Sản phẩm không có trong bảng giá", date(2026, 1, 15)) is None


def test_lookup_with_missing_code_or_date_is_pending():
    provider = FilePriceProvider([_row()])
    assert provider.lookup(None, date(2026, 1, 15)) is None
    assert provider.lookup("Máy giặt Test-1", None) is None
    assert provider.lookup(None, None) is None


# ---------------------------------------------------------------------------
# CHECK-105B-06 — normalization: Owner's 3 examples fold to one key; no
# diacritic stripping (NFC + collapse-whitespace + casefold only, DEC-145 §2).
# ---------------------------------------------------------------------------

OWNER_EXAMPLES = [
    "Cây nước Kangaroo KG36A2",
    "Cây nước Kangaroo KG36A2 ",
    "CÂY NƯỚC   KANGAROO KG36A2",
]


@pytest.mark.parametrize("raw_key", OWNER_EXAMPLES)
def test_owner_normalization_examples_hit_same_record(raw_key):
    provider = FilePriceProvider(
        [_row(product_key="Cây nước Kangaroo KG36A2")]
    )
    assert provider.lookup(raw_key, date(2026, 1, 15)) == Decimal("5000000")


def test_normalization_does_not_strip_vietnamese_diacritics():
    provider = FilePriceProvider([_row(product_key="Cây nước Kangaroo KG36A2")])
    # "Cay" (no diacritics) must NOT match "Cây" (diacritics) — normalization
    # is NFC+casefold only, never a diacritic-stripping/fuzzy match.
    assert provider.lookup("Cay nuoc Kangaroo KG36A2", date(2026, 1, 15)) is None


# ---------------------------------------------------------------------------
# CHECK-105B-07 — same normalized key, conflicting price -> error, no pick.
# ---------------------------------------------------------------------------


def test_same_key_different_raw_spelling_conflicting_price_raises():
    rows = [
        _row(
            product_key="Cây nước Kangaroo KG36A2",
            effective_from="2026-01-01",
            effective_to="2026-01-31",
            purchase_price="5000000",
        ),
        _row(
            product_key="Cây nước Kangaroo KG36A2 ",  # different raw, same normalized
            effective_from="2026-01-01",
            effective_to="2026-01-31",
            purchase_price="5500000",
        ),
    ]
    with pytest.raises(InvalidPriceMasterError) as excinfo:
        FilePriceProvider(rows)
    assert excinfo.value.reason == "conflicting_price_same_period"


# ---------------------------------------------------------------------------
# CHECK-105B-08 — provenance keeps raw key / normalized key / matched record.
# ---------------------------------------------------------------------------


def test_provenance_keeps_raw_normalized_and_matched_record():
    provider = FilePriceProvider(
        [_row(product_key="Cây nước Kangaroo KG36A2 ", source="Bảng giá tháng 1")]
    )
    record = provider.find_record("CÂY NƯỚC   KANGAROO KG36A2", date(2026, 1, 15))
    assert record is not None
    assert record.raw_product_key == "Cây nước Kangaroo KG36A2 "
    assert record.normalized_product_key == "cây nước kangaroo kg36a2"
    assert record.purchase_price == Decimal("5000000")
    assert record.source == "Bảng giá tháng 1"
    # The loaded set is also introspectable directly.
    assert record in provider.records


# ---------------------------------------------------------------------------
# CHECK-105B-09 — 8 reject cases (DEC-145 §5).
# ---------------------------------------------------------------------------

REJECT_CASES = [
    (
        "negative_price",
        _row(purchase_price="-100"),
        "negative_price",
    ),
    (
        "empty_key_literal_empty_string",
        _row(product_key=""),
        "empty_key",
    ),
    (
        "empty_key_whitespace_only",
        _row(product_key="   "),
        "empty_key",
    ),
    (
        "invalid_effective_from_format",
        _row(effective_from="not-a-date"),
        "invalid_date",
    ),
    (
        "missing_effective_from",
        _row(effective_from=None),
        "invalid_date",
    ),
    (
        "invalid_effective_to_format",
        _row(effective_to="15/01/2026"),
        "invalid_date",
    ),
    (
        "effective_to_before_effective_from",
        _row(effective_from="2026-01-31", effective_to="2026-01-01"),
        "inverted_range",
    ),
    (
        "blank_purchase_price",
        _row(purchase_price=None),
        "missing_price",
    ),
]


@pytest.mark.parametrize("label,row,expected_reason", REJECT_CASES, ids=[c[0] for c in REJECT_CASES])
def test_reject_cases(label, row, expected_reason):
    with pytest.raises(InvalidPriceMasterError) as excinfo:
        FilePriceProvider([row])
    assert excinfo.value.reason == expected_reason, label


def test_exact_duplicate_row_rejected():
    row = _row()
    with pytest.raises(InvalidPriceMasterError) as excinfo:
        FilePriceProvider([row, dict(row)])
    assert excinfo.value.reason == "exact_duplicate_row"


# ---------------------------------------------------------------------------
# CHECK-105B-10 — declared 0 is valid; blank cell is not silently 0.
# ---------------------------------------------------------------------------


def test_declared_zero_price_is_valid_and_distinct_from_blank():
    provider = FilePriceProvider([_row(purchase_price="0")])
    assert provider.lookup("Máy giặt Test-1", date(2026, 1, 15)) == Decimal("0")


def test_blank_price_cell_raises_not_coerced_to_zero():
    with pytest.raises(InvalidPriceMasterError) as excinfo:
        FilePriceProvider([_row(purchase_price=None)])
    assert excinfo.value.reason == "missing_price"


def test_blank_string_price_cell_raises_not_coerced_to_zero():
    with pytest.raises(InvalidPriceMasterError) as excinfo:
        FilePriceProvider([_row(purchase_price="   ")])
    assert excinfo.value.reason == "missing_price"


# ---------------------------------------------------------------------------
# CHECK-105B-11 — every value is Decimal; zero float() calls in the module.
# ---------------------------------------------------------------------------


def test_price_values_are_always_decimal_never_float():
    provider = FilePriceProvider([_row(purchase_price=5000000)])
    price = provider.lookup("Máy giặt Test-1", date(2026, 1, 15))
    assert isinstance(price, Decimal)
    assert not isinstance(price, float)


def test_module_source_contains_no_float_call():
    source = _MODULE_PATH.read_text(encoding="utf-8")
    assert "float(" not in source


# ---------------------------------------------------------------------------
# CHECK-105B-15 — no import of app.modules.validation.rules; no Q3 keywords;
# CHECK-105B-17 (DEC-146 risk note) — no Firebase/RTDB client import.
# ---------------------------------------------------------------------------

_Q3_KEYWORDS = ["phí", "công lắp đặt", "chênh vat", "chiết khấu", "voucher"]
_FIREBASE_MARKERS = ["firebase", "Firebase", "pyrebase", "google.cloud"]


def test_module_does_not_import_validation_rules():
    source = _MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    assert not any(name.startswith("app.modules.validation.rules") for name in imported)


def test_module_does_not_contain_q3_classification_keywords():
    source = _MODULE_PATH.read_text(encoding="utf-8")
    for keyword in _Q3_KEYWORDS:
        assert keyword not in source, keyword


def test_module_does_not_import_or_mention_firebase_client():
    source = _MODULE_PATH.read_text(encoding="utf-8")
    for marker in _FIREBASE_MARKERS:
        assert marker not in source, marker


# ---------------------------------------------------------------------------
# from_yaml — file-loading path (DEC-145 §4).
# ---------------------------------------------------------------------------


def test_from_yaml_loads_and_validates(tmp_path):
    path = tmp_path / "prices.yaml"
    path.write_text(
        "prices:\n"
        "  - product_key: \"Máy giặt Test-1\"\n"
        "    effective_from: \"2026-01-01\"\n"
        "    effective_to: \"2026-01-31\"\n"
        "    purchase_price: \"5000000\"\n"
        "    source: \"Bảng giá tháng 1\"\n",
        encoding="utf-8",
    )
    provider = FilePriceProvider.from_yaml(path)
    assert provider.lookup("Máy giặt Test-1", date(2026, 1, 15)) == Decimal("5000000")


def test_from_yaml_empty_prices_key_yields_empty_provider(tmp_path):
    path = tmp_path / "prices.yaml"
    path.write_text("prices: []\n", encoding="utf-8")
    provider = FilePriceProvider.from_yaml(path)
    assert provider.lookup("Máy giặt Test-1", date(2026, 1, 15)) is None
    assert provider.records == ()
