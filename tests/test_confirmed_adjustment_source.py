"""`ConfirmedAdjustmentSource` loader — DEC-144 §3/§5 (TASK-108B minimum
B7/B8 slice, Golden #1 KPI vertical slice).

Ba trạng thái không được gộp: UNAVAILABLE (thiếu/hỏng) khác LOADED-rỗng
(DETERMINED_ABSENCE) khác LOADED-có-record.
"""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path

from app.modules.adjustment.confirmed_adjustment_source import (
    ConfirmedAdjustmentSource,
    load_confirmed_adjustments_from_jsonl,
)


def _write(path: Path, *lines: str) -> None:
    path.write_text("\n".join(lines), encoding="utf-8")


def test_missing_file_is_unavailable_not_empty(tmp_path):
    """DEC-144 §3 — thiếu nguồn PHẢI khác xác-định-không-có."""
    source = load_confirmed_adjustments_from_jsonl(tmp_path / "does_not_exist.jsonl")
    assert source.is_available is False
    assert source.lookup("BH0001") is None


def test_empty_file_is_loaded_determined_absence(tmp_path):
    path = tmp_path / "confirmed.jsonl"
    path.write_text("", encoding="utf-8")
    source = load_confirmed_adjustments_from_jsonl(path)
    assert source.is_available is True
    assert source.lookup("BH0001") is None  # DETERMINED_ABSENCE, không phải unavailable


def test_invalid_json_line_makes_whole_source_unavailable(tmp_path):
    path = tmp_path / "confirmed.jsonl"
    _write(path, "{not valid json")
    source = load_confirmed_adjustments_from_jsonl(path)
    assert source.is_available is False


def test_line_missing_required_field_makes_whole_source_unavailable(tmp_path):
    path = tmp_path / "confirmed.jsonl"
    _write(path, json.dumps({"order_id": "BH0001"}))  # thiếu amount/confirmed_by
    source = load_confirmed_adjustments_from_jsonl(path)
    assert source.is_available is False


def test_unparseable_amount_makes_whole_source_unavailable(tmp_path):
    path = tmp_path / "confirmed.jsonl"
    _write(
        path,
        json.dumps(
            {"order_id": "BH0001", "amount": "not-a-number", "confirmed_by": "test"}
        ),
    )
    source = load_confirmed_adjustments_from_jsonl(path)
    assert source.is_available is False


def test_one_bad_line_among_good_lines_still_fails_closed(tmp_path):
    """Fail-closed: một dòng hỏng không cho biết nó lẽ ra khớp order nào, nên
    order khác trong cùng file KHÔNG được coi là đã xác định vắng mặt."""
    path = tmp_path / "confirmed.jsonl"
    _write(
        path,
        json.dumps(
            {"order_id": "BH0001", "amount": "50000", "confirmed_by": "test"}
        ),
        "{broken",
    )
    source = load_confirmed_adjustments_from_jsonl(path)
    assert source.is_available is False


def test_confirmed_record_is_found_by_order_id(tmp_path):
    path = tmp_path / "confirmed.jsonl"
    _write(
        path,
        json.dumps(
            {
                "order_id": "BH0004",
                "amount": "10000",
                "confirmed_by": "chu.du.an",
                "reason": "test fixture",
            }
        ),
    )
    source = load_confirmed_adjustments_from_jsonl(path)
    assert source.is_available is True

    record = source.lookup("BH0004")
    assert record is not None
    assert record.amount == Decimal("10000")
    assert record.confirmed_by == "chu.du.an"

    # Một order khác không có record vẫn là DETERMINED_ABSENCE, không phải lỗi.
    assert source.lookup("BH9999") is None


def test_blank_lines_are_skipped():
    """`ConfirmedAdjustmentSource` construction trực tiếp — records rỗng vẫn
    phân biệt được `is_available` khỏi `None`."""
    assert ConfirmedAdjustmentSource(records={}).is_available is True
    assert ConfirmedAdjustmentSource(records=None).is_available is False
