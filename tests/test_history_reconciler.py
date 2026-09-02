"""TASK-PRA-002 mục 8/9 — máy trạng thái reconcile, kiểm thuần không DB.

Mỗi test dưới đây là một dòng của bảng contract 3.2 mà Owner đã chấp nhận
nguyên văn. Chúng cố ý không dựng database: một lỗi ở đây gây hậu quả kế toán
thật (đếm hai lần một dòng bán → doanh thu/KPI/lương sai), nên nó phải kiểm
được bằng bảng vào/ra chứ không phải bằng cách chạy cả hệ thống rồi đoán.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.history import keys
from app.history.models import (
    COLLISION_DAY_THRESHOLD, CurrentState, LineKey, OUTCOME_COLLISION, OUTCOME_INSERT,
    OUTCOME_SAME, OUTCOME_SOURCE_CHANGED, ResultLine, SourceLine,
)
from app.history.reconciler import reconcile, result_revisions


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


# --- RESULT_REVISED (slice C1, mục 8 bước 3) -------------------------------
#
# Trục KẾT QUẢ, không phải trục nguồn: các test dưới đây giữ nguồn ĐỨNG YÊN
# (luôn là SAME trừ khi nói rõ) và chỉ đổi kết quả pipeline, vì đó là đúng
# tình huống mà cờ này tồn tại để mô tả — Reports chạy lại với bằng chứng
# Tracking mới trên cùng một sổ kế toán.

def result_of(line: SourceLine, *, status="AUTO", purchase="5000000", kpi="3000000",
              price_source="TRACKING_PRICE_HISTORY") -> ResultLine:
    return ResultLine(
        key=line.key, status=status, pending_reasons=() if status == "AUTO" else ("x",),
        total_sales=line.total_sales_raw, employee_normalized="VuHanhLy",
        employee_group="G1", lead_source_final="PERSONAL",
        identity_namespace="TRACKING", canonical_product_code="A1",
        accounting_purchase_price=None if purchase is None else Decimal(purchase),
        price_source=price_source, composition_rule="TRACKING_HISTORY_AUTHORITY",
        accounting_profit=Decimal("3000000"),
        kpi_purchase_price=None if purchase is None else Decimal(purchase),
        kpi_purchase_provenance="Config:NoConfirmedAdjustment",
        eligible_kpi_profit=None if kpi is None else Decimal(kpi),
        product_group_final="DIEN_MAY", conversion_scheme_final="S1",
        conversion_rate_final=Decimal("1"),
        result_fingerprint=keys.result_fingerprint(
            status, None if purchase is None else Decimal(purchase),
            None if kpi is None else Decimal(kpi),
        ),
    )


def state_with_result(line: SourceLine, result: ResultLine, *, version_id=10,
                      result_version_id=77, **overrides) -> CurrentState:
    base = state_of(line, version_id=version_id)
    return replace(
        base, result_version_id=result_version_id,
        result_fingerprint=result.result_fingerprint,
        result_values=result.result_values, **overrides,
    )


def classify(line: SourceLine, previous: ResultLine, incoming: ResultLine, *,
             state=None, source_line_now=None):
    """Chạy đúng đường thật: reconcile nguồn trước, rồi phân loại kết quả."""
    current = {line.key: state if state is not None else state_with_result(line, previous)}
    lines = [source_line_now if source_line_now is not None else line]
    decisions = reconcile(lines, current).decisions
    return decisions, result_revisions(decisions, [incoming], current)


def test_same_source_and_identical_result_fingerprint_raises_no_revision():
    """Hợp đồng SAME của slice A: vẫn ghi result version mới, nhưng KHÔNG cờ."""
    line = source_line()
    previous = result_of(line)
    decisions, revisions = classify(line, previous, result_of(line))
    assert decisions[0].outcome == OUTCOME_SAME
    assert revisions == ()


def test_same_source_with_a_changed_status_is_one_revision():
    line = source_line()
    previous = result_of(line, status="PENDING")
    _, revisions = classify(line, previous, result_of(line, status="AUTO"))
    revision, = revisions
    assert revision.key == line.key
    assert revision.from_result_version_id == 77
    assert revision.changed_fields == {"status": {"old": "PENDING", "new": "AUTO"}}


def test_same_source_with_a_changed_accounting_purchase_price_is_one_revision():
    line = source_line()
    previous = result_of(line, purchase="5000000")
    _, revisions = classify(line, previous, result_of(line, purchase="5100000"))
    revision, = revisions
    assert revision.changed_fields == {
        "accounting_purchase_price": {"old": "5000000", "new": "5100000"},
    }


def test_same_source_with_a_changed_eligible_kpi_profit_is_one_revision():
    line = source_line()
    previous = result_of(line, kpi="3000000")
    _, revisions = classify(line, previous, result_of(line, kpi="2900000"))
    revision, = revisions
    assert revision.changed_fields == {
        "eligible_kpi_profit": {"old": "3000000", "new": "2900000"},
    }


def test_all_three_f3_fields_changing_is_still_exactly_one_revision():
    """Một lần chạy lại = một sự kiện, dù đổi bao nhiêu trường trong F3."""
    line = source_line()
    previous = result_of(line, status="PENDING", purchase="5000000", kpi="3000000")
    _, revisions = classify(
        line, previous, result_of(line, status="AUTO", purchase="5100000", kpi="2900000"),
    )
    revision, = revisions
    assert revision.changed_fields == {
        "status": {"old": "PENDING", "new": "AUTO"},
        "accounting_purchase_price": {"old": "5000000", "new": "5100000"},
        "eligible_kpi_profit": {"old": "3000000", "new": "2900000"},
    }


def test_source_changed_wins_and_suppresses_the_result_revision():
    """Kết quả đổi vì NGUỒN đổi — một sự kiện, một cờ, và cờ đó là nguồn."""
    line = source_line(sell_price="8000000")
    moved = source_line(sell_price="8500000")
    decisions, revisions = classify(
        line, result_of(line), result_of(line, purchase="5100000"), source_line_now=moved,
    )
    assert decisions[0].outcome == OUTCOME_SOURCE_CHANGED
    assert revisions == ()


def test_collision_raises_no_revision_even_when_the_result_changed():
    """Khoá tranh chấp danh tính còn không được ghi result version (mục 6)."""
    line = source_line(sale_date=date(2026, 1, 5))
    far = source_line(sale_date=date(2026, 1, 5) + timedelta(days=COLLISION_DAY_THRESHOLD + 1))
    decisions, revisions = classify(
        line, result_of(line), result_of(far, purchase="5100000"), source_line_now=far,
    )
    assert decisions[0].outcome == OUTCOME_COLLISION
    assert revisions == ()


def test_a_first_ever_result_is_not_a_revision():
    """INSERT: chưa có kết quả hiện hành thì không có gì để 'sửa'."""
    line = source_line()
    decisions = reconcile([line], {}).decisions
    assert decisions[0].outcome == OUTCOME_INSERT
    assert result_revisions(decisions, [result_of(line)], {}) == ()


def test_a_field_outside_f3_changing_leaves_the_fingerprint_and_the_verdict_alone():
    """``price_source`` đổi nhãn trong khi ba con số F3 không đổi → 0 cờ."""
    line = source_line()
    previous = result_of(line, price_source="TRACKING_PRICE_HISTORY")
    incoming = result_of(line, price_source="CONFIRMED_ADJUSTMENT")
    assert incoming.result_fingerprint == previous.result_fingerprint
    assert incoming.price_source != previous.price_source
    _, revisions = classify(line, previous, incoming)
    assert revisions == ()


def test_the_detail_diff_is_deterministic_across_equal_but_differently_typed_amounts():
    """``5000000`` và ``5000000.00`` là CÙNG số tiền — không phải một lần sửa."""
    line = source_line()
    previous = result_of(line, purchase="5000000")
    same_value = result_of(line, purchase="5000000.00")
    assert same_value.result_fingerprint == previous.result_fingerprint
    _, revisions = classify(line, previous, same_value)
    assert revisions == ()

    _, changed = classify(line, previous, result_of(line, purchase="5000001"))
    assert [r.changed_fields for r in changed] == [
        {"accounting_purchase_price": {"old": "5000000", "new": "5000001"}},
    ]


def test_a_none_amount_becoming_a_number_is_a_revision_with_canonical_empty_old():
    line = source_line()
    previous = result_of(line, purchase=None)
    _, revisions = classify(line, previous, result_of(line, purchase="5000000"))
    revision, = revisions
    assert revision.changed_fields == {
        "accounting_purchase_price": {"old": "", "new": "5000000"},
    }
