"""TASK-PRA-002 mục 8/9 — máy trạng thái reconcile, kiểm thuần không DB.

Mỗi test dưới đây là một dòng của bảng contract 3.2 mà Owner đã chấp nhận
nguyên văn. Chúng cố ý không dựng database: một lỗi ở đây gây hậu quả kế toán
thật (đếm hai lần một dòng bán → doanh thu/KPI/lương sai), nên nó phải kiểm
được bằng bảng vào/ra chứ không phải bằng cách chạy cả hệ thống rồi đoán.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.history import keys
from app.history.models import (
    COLLISION_DAY_THRESHOLD, CurrentState, LineKey, OUTCOME_COLLISION, OUTCOME_INSERT,
    OUTCOME_SAME, OUTCOME_SOURCE_CHANGED, SourceLine,
)
from app.history.reconciler import reconcile


def source_line(order="BH1", product="Tủ lạnh", occurrence=1, *, row=6,
                sale_date=date(2026, 1, 5), sell_price="8000000", **overrides):
    values = dict(
        sale_date=sale_date, product_raw=product, quantity=Decimal("1"),
        sell_price=Decimal(sell_price), discount=Decimal("0"),
        total_sales_raw=Decimal(sell_price), delivery_cost=None, imei=None,
        note_raw=None, employee_raw="Vũ Hạnh Ly", source_profit=Decimal("500000"),
    )
    values.update(overrides)
    ordered = tuple(values[name] for name in keys.FINGERPRINT_FIELDS)
    number, year_hint = keys.bh_parts(order, values["sale_date"])
    return SourceLine(
        key=LineKey(order, keys.product_key(product), occurrence),
        source_row=row, row_hash="hash", fingerprint=keys.line_fingerprint(ordered),
        bh_number=number, bh_year_hint=year_hint, **values,
    )


def state_of(line: SourceLine, *, version_id=10, version_no=1) -> CurrentState:
    return CurrentState(
        source_version_id=version_id, version_no=version_no,
        fingerprint=line.fingerprint, sale_date=line.sale_date,
        fingerprint_values=line.fingerprint_values,
    )


# --- INSERT ---------------------------------------------------------------

def test_a_key_never_seen_before_becomes_source_version_one_and_current():
    line = source_line()
    decision, = reconcile([line], {}).decisions
    assert decision.outcome == OUTCOME_INSERT
    assert (decision.version_no, decision.creates_version, decision.becomes_current) == (
        1, True, True
    )
    assert decision.changed_fields is None


# --- SAME -----------------------------------------------------------------

def test_the_same_line_again_creates_no_new_version_and_no_diff():
    line = source_line()
    decision, = reconcile([line], {line.key: state_of(line)}).decisions
    assert decision.outcome == OUTCOME_SAME
    assert decision.creates_version is False
    assert decision.becomes_current is True
    assert decision.version_no == 1
    assert decision.previous_version_id == 10


def test_same_verdict_survives_a_pii_only_or_row_position_only_re_export():
    """Fingerprint không chứa PII/vị trí dòng, nên chúng không tạo version mới."""
    before = source_line(row=6)
    after = source_line(row=99)
    decision, = reconcile([after], {before.key: state_of(before)}).decisions
    assert decision.outcome == OUTCOME_SAME


def test_same_verdict_survives_a_pure_number_formatting_change():
    before = source_line(sell_price="8000000")
    after = source_line(sell_price="8000000.00")
    decision, = reconcile([after], {before.key: state_of(before)}).decisions
    assert decision.outcome == OUTCOME_SAME


# --- SOURCE_CHANGED -------------------------------------------------------

def test_an_edited_line_becomes_version_n_plus_one_and_names_what_changed():
    before = source_line(sell_price="8000000")
    after = source_line(sell_price="9000000", total_sales_raw=Decimal("9000000"))
    decision, = reconcile(
        [after], {before.key: state_of(before, version_id=7, version_no=3)}
    ).decisions
    assert decision.outcome == OUTCOME_SOURCE_CHANGED
    assert decision.version_no == 4
    assert decision.creates_version is True and decision.becomes_current is True
    assert decision.previous_version_id == 7
    assert decision.changed_fields == {
        "sell_price": {"old": "8000000", "new": "9000000"},
        "total_sales_raw": {"old": "8000000", "new": "9000000"},
    }


def test_changed_fields_lists_only_the_fields_that_actually_moved():
    before = source_line()
    after = source_line(note_raw="đã đổi ghi chú")
    decision, = reconcile([after], {before.key: state_of(before)}).decisions
    assert set(decision.changed_fields) == {"note_raw"}


# --- ORDER_KEY_COLLISION --------------------------------------------------

def test_the_same_bh_far_apart_in_time_is_never_reconciled_silently():
    """BH có reset theo năm hay không vẫn là UNKNOWN — thà dựng cờ còn hơn đoán."""
    before = source_line(sale_date=date(2026, 1, 5))
    far = date(2026, 1, 5) + timedelta(days=COLLISION_DAY_THRESHOLD + 1)
    after = source_line(sale_date=far)
    decision, = reconcile([after], {before.key: state_of(before)}).decisions
    assert decision.outcome == OUTCOME_COLLISION
    assert decision.becomes_current is False, "hiện trạng cũ KHÔNG được thay thế"
    assert decision.creates_version is True, "bản ghi mới KHÔNG được mất"
    assert decision.collision_detail["day_gap"] == COLLISION_DAY_THRESHOLD + 1
    assert decision.collision_detail["current_sale_date"] == "2026-01-05"


def test_exactly_at_the_threshold_is_still_a_normal_reconcile():
    before = source_line(sale_date=date(2026, 1, 5))
    at_edge = date(2026, 1, 5) + timedelta(days=COLLISION_DAY_THRESHOLD)
    decision, = reconcile(
        [source_line(sale_date=at_edge)], {before.key: state_of(before)}
    ).decisions
    assert decision.outcome == OUTCOME_SOURCE_CHANGED


def test_a_missing_date_on_either_side_never_becomes_a_collision():
    """Thiếu ngày là 'chưa biết', không phải bằng chứng hai đơn cách xa nhau."""
    before = source_line(sale_date=None)
    decision, = reconcile(
        [source_line(sale_date=date(2026, 12, 31))], {before.key: state_of(before)}
    ).decisions
    assert decision.outcome == OUTCOME_SOURCE_CHANGED


# --- tập hợp --------------------------------------------------------------

def test_an_overlapping_snapshot_splits_into_same_for_the_old_and_insert_for_the_new():
    kept = source_line(order="BH1", row=6)
    edited_before = source_line(order="BH2", row=7, sell_price="5000000")
    edited_after = source_line(order="BH2", row=7, sell_price="5500000")
    fresh = source_line(order="BH3", row=8)
    current = {kept.key: state_of(kept), edited_before.key: state_of(edited_before)}
    result = reconcile([kept, edited_after, fresh], current)
    assert result.counts() == {
        OUTCOME_INSERT: 1, OUTCOME_SAME: 1, OUTCOME_SOURCE_CHANGED: 1,
        OUTCOME_COLLISION: 0,
    }


def test_uploading_the_wide_snapshot_first_then_the_narrow_one_adds_nothing():
    """Thứ tự upload đảo ngược: phần chồng nhau vẫn SAME, không có INSERT mới.

    (Các khoá chỉ có ở snapshot rộng sẽ được nêu là NOT_SEEN — bước 4, slice B.)
    """
    wide = [source_line(order=f"BH{i}", row=5 + i) for i in range(1, 5)]
    current = {line.key: state_of(line, version_id=i) for i, line in enumerate(wide, 1)}
    narrow = wide[:2]
    assert reconcile(narrow, current).counts() == {
        OUTCOME_INSERT: 0, OUTCOME_SAME: 2, OUTCOME_SOURCE_CHANGED: 0,
        OUTCOME_COLLISION: 0,
    }


def test_reconcile_reads_the_current_state_and_never_writes_to_it():
    line = source_line()
    current = {line.key: state_of(line)}
    snapshot_before = dict(current)
    reconcile([line], current)
    assert current == snapshot_before


@pytest.mark.parametrize("occurrence", [1, 2, 3])
def test_each_occurrence_of_a_repeated_product_reconciles_on_its_own(occurrence):
    line = source_line(occurrence=occurrence)
    other = source_line(occurrence=occurrence + 1)
    decision, = reconcile([line], {other.key: state_of(other)}).decisions
    assert decision.outcome == OUTCOME_INSERT
