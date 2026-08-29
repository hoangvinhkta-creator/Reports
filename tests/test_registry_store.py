"""`registry_store.load_registry_from_jsonl` — Golden #1 vertical delivery
session brief §2. Loader read-only, một lần, không multi-writer lock (khác
`store.py`/E-F — xem docstring module)."""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from app.modules.product.identity.registry_store import (
    InvalidRegistrySeedRecordError,
    load_registry_from_jsonl,
)
from tests.support import identity_fixtures as fx


def _write_jsonl(path: Path, *records: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def test_missing_file_returns_empty_registry(tmp_path):
    registry = load_registry_from_jsonl(tmp_path / "does-not-exist.jsonl")
    assert registry.current_revision() == 0


def test_loads_a_manual_legacy_entry_and_lookup_matches(tmp_path):
    entry = fx.registry_entry_manual_legacy(
        order_id="BH62063", product_raw="Máy giặt LG 10kg FV1410S4W1"
    )
    path = tmp_path / "registry.jsonl"
    _write_jsonl(path, entry.to_record())

    registry = load_registry_from_jsonl(path)
    assert registry.current_revision() == 1
    found = registry.lookup(
        "BH62063", "Máy giặt LG 10kg FV1410S4W1", fx.PRE_CUTOVER
    )
    assert found is not None
    assert found.confirmed_purchase_price == Decimal("2500000")
    assert found.manual_legacy_confirmation_ref.original_system == "Tracking"


def test_loads_multiple_lines_in_order_and_skips_blank_lines(tmp_path):
    entry_a = fx.registry_entry(entry_id="HCR-A", order_id="ORD-A")
    entry_b = fx.registry_entry_manual_legacy(entry_id="HCR-B", order_id="ORD-B")
    path = tmp_path / "registry.jsonl"
    with path.open("w", encoding="utf-8") as handle:
        handle.write(json.dumps(entry_a.to_record(), ensure_ascii=False) + "\n")
        handle.write("\n")
        handle.write(json.dumps(entry_b.to_record(), ensure_ascii=False) + "\n")

    registry = load_registry_from_jsonl(path)
    assert registry.current_revision() == 2
    assert registry.lookup(
        "ORD-A", entry_a.raw_identity_key, entry_a.sale_date
    ) is not None
    assert registry.lookup(
        "ORD-B", entry_b.raw_identity_key, entry_b.sale_date
    ) is not None


def test_malformed_json_line_raises_instead_of_silently_skipping(tmp_path):
    path = tmp_path / "registry.jsonl"
    path.write_text("{not valid json\n", encoding="utf-8")

    with pytest.raises(InvalidRegistrySeedRecordError):
        load_registry_from_jsonl(path)


def test_the_real_committed_bh62063_seed_file_loads_and_resolves():
    """Đúng file thật `data/historical_confirmed/registry.jsonl` dùng bởi
    Golden #1 vertical trace — không phải một bản sao trong tmp_path."""
    path = Path("data/historical_confirmed/registry.jsonl")
    registry = load_registry_from_jsonl(path)
    entry = registry.lookup(
        "BH62063", "Máy giặt LG 10kg FV1410S4W1", date(2026, 1, 2)
    )
    assert entry is not None
    assert entry.confirmed_purchase_price == Decimal("7000000")
    assert entry.provenance == "OWNER_MANUAL_LEGACY_CONFIRMATION"
    assert str(entry.confirmed_identity) == "TRACKING:FV1410S4W1"
