"""TASK-PRA-002 slice B — coverage semantics và phép toán vắng mặt, kiểm THUẦN.

Hai bất biến được kiểm ở đây, và chúng là lý do slice B tồn tại:

1. Không có đường nào tới ``CONFIRMED_COMPLETE`` mà không đi qua một hành động
   tường minh của con người. Header khớp, ngày cuối tháng, số dòng đẹp — không
   thứ nào được phép nâng trạng thái.
2. "Không thấy" chỉ có nghĩa TRONG phạm vi mà snapshot thực sự đại diện. Một
   sổ 01–10/09 không nói được gì về đơn ngày 20/09, kể cả khi nó được xác nhận
   là đầy đủ cho 01–10/09.

Test thuần, không database: một lỗi ở đây có hậu quả kế toán thật (kết luận
sai rằng một đơn đã biến mất), nên nó phải kiểm được bằng bảng vào/ra.
"""

from __future__ import annotations

from datetime import date

import pytest

from app.history import coverage
from app.history.models import (
    CONFIRMED_COMPLETE, CurrentKey, DETECTED_ONLY, HEADER_CONSISTENT, LineKey,
)
from app.history.reconciler import absent_keys


def key(order="BH1", product="p1", occurrence=1) -> LineKey:
    return LineKey(order, product, occurrence)


def candidate(order="BH1", *, sale_date=date(2026, 9, 5), collision=False,
              product="p1", occurrence=1) -> CurrentKey:
    return CurrentKey(key=key(order, product, occurrence), sale_date=sale_date,
                      order_key_collision=collision)


# --- ba mức coverage ------------------------------------------------------

def test_a_snapshot_with_no_readable_header_stays_detected_only():
    detected = (date(2026, 9, 1), date(2026, 9, 30))
    assert coverage.coverage_state(None, detected) == DETECTED_ONLY


def test_a_header_that_covers_the_data_reaches_header_consistent():
    detected = (date(2026, 9, 2), date(2026, 9, 29))
    header = coverage.parse_header("Từ ngày 01/09/2026 đến ngày 30/09/2026")
    assert coverage.coverage_state(header, detected) == HEADER_CONSISTENT


def test_a_header_narrower_than_the_data_falls_back_to_detected_only():
    """Header hẹp hơn dữ liệu là một CẢNH BÁO, không phải một sự đầy đủ."""
    detected = (date(2026, 9, 1), date(2026, 10, 2))
    header = coverage.parse_header("Từ ngày 01/09/2026 đến ngày 30/09/2026")
    assert coverage.coverage_state(header, detected) == DETECTED_ONLY


@pytest.mark.parametrize("header_text", [
    "Từ 01/09/2026 tới 30/09/2026",
    "Báo cáo tháng 9",
    "Nhân viên: Tín Phát, Quý 3 năm 2026",
    "Từ ngày 1/9/2026 đến ngày 30/9/2026",
    "",
    None,
])
def test_an_unknown_header_shape_never_produces_a_range(header_text):
    """Dạng thứ ba xuất hiện → không đoán. Fail-safe là DETECTED_ONLY."""
    assert coverage.parse_header(header_text) is None
    assert coverage.coverage_state(
        coverage.parse_header(header_text), (date(2026, 9, 1), date(2026, 9, 30)),
    ) == DETECTED_ONLY


def test_the_pure_coverage_layer_can_never_return_confirmed_complete():
    """Không tổ hợp header/dữ liệu nào nâng được trạng thái — chỉ con người."""
    ranges = [
        (date(2026, 9, 1), date(2026, 9, 30)),   # đúng trọn tháng
        (date(2026, 9, 1), date(2026, 9, 1)),
        (date(2026, 1, 31), date(2026, 1, 31)),  # "thấy ngày cuối tháng"
    ]
    headers = [None, coverage.parse_header("Từ ngày 01/09/2026 đến ngày 30/09/2026"),
               coverage.parse_header("Nhân viên: Tín Phát, Tháng 9 năm 2026")]
    for header in headers:
        for detected in ranges:
            assert coverage.coverage_state(header, detected) != CONFIRMED_COMPLETE


# --- xác nhận tường minh --------------------------------------------------

DETECTED = (date(2026, 9, 1), date(2026, 9, 10))


def test_an_unchecked_box_is_never_a_confirmation():
    """Mặc định KHÔNG tick → không bao giờ CONFIRMED_COMPLETE."""
    assert coverage.confirmation_error(
        confirmed=False, start=date(2026, 9, 1), end=date(2026, 9, 10),
        detected=DETECTED,
    ) is not None


def test_a_checked_box_with_a_range_that_covers_the_data_is_accepted():
    assert coverage.confirmation_error(
        confirmed=True, start=date(2026, 9, 1), end=date(2026, 9, 10),
        detected=DETECTED,
    ) is None


def test_the_confirmed_range_may_be_wider_than_the_data_it_contains():
    """Owner được phép khai một khoảng rộng hơn — đó là lời khẳng định của họ."""
    assert coverage.confirmation_error(
        confirmed=True, start=date(2026, 9, 1), end=date(2026, 9, 30),
        detected=DETECTED,
    ) is None


def test_a_range_that_leaves_data_outside_is_refused_and_says_which_date():
    reason = coverage.confirmation_error(
        confirmed=True, start=date(2026, 9, 1), end=date(2026, 9, 5),
        detected=DETECTED,
    )
    assert reason is not None and "2026-09-10" in reason


def test_a_backwards_range_is_refused():
    assert coverage.confirmation_error(
        confirmed=True, start=date(2026, 9, 10), end=date(2026, 9, 1),
        detected=DETECTED,
    ) is not None


def test_a_range_longer_than_a_year_is_refused_as_a_typo_guard():
    assert coverage.confirmation_error(
        confirmed=True, start=date(2026, 9, 1), end=date(2027, 9, 30),
        detected=DETECTED,
    ) is not None


def test_exactly_a_full_leap_year_is_still_accepted():
    """Ranh giới: 366 ngày ĐƯỢC nhận, 367 thì không."""
    start = date(2028, 1, 1)
    assert coverage.confirmation_error(
        confirmed=True, start=start, end=date(2028, 12, 31),
        detected=(date(2028, 6, 1), date(2028, 6, 2)),
    ) is None
    assert coverage.confirmation_error(
        confirmed=True, start=start, end=date(2029, 1, 1),
        detected=(date(2028, 6, 1), date(2028, 6, 2)),
    ) is not None


def test_an_unparseable_date_is_refused_rather_than_guessed():
    assert coverage.parse_iso_date("10/09/2026") is None
    assert coverage.confirmation_error(
        confirmed=True, start=None, end=date(2026, 9, 10), detected=DETECTED,
    ) is not None


def test_a_second_confirmation_is_refused():
    assert coverage.confirmation_error(
        confirmed=True, start=date(2026, 9, 1), end=date(2026, 9, 10),
        detected=DETECTED, already_confirmed=True,
    ) is not None


# --- nhãn hiển thị (FIND-PRA002-A4) ---------------------------------------

def test_every_coverage_state_has_its_own_label():
    labels = {coverage.coverage_label(state)
              for state in (DETECTED_ONLY, HEADER_CONSISTENT, CONFIRMED_COMPLETE)}
    assert len(labels) == 3, "ba trạng thái không được dùng chung một câu"
    assert "ĐÃ XÁC NHẬN" in coverage.coverage_label(CONFIRMED_COMPLETE)
    for state in (DETECTED_ONLY, HEADER_CONSISTENT):
        assert "CHƯA XÁC NHẬN" in coverage.coverage_label(state)


# --- phép toán vắng mặt ---------------------------------------------------

SEPT = (date(2026, 9, 1), date(2026, 9, 30))


def test_a_key_present_in_the_new_snapshot_is_never_absent():
    assert absent_keys(present=[key("BH1")], candidates=[candidate("BH1")],
                       start=SEPT[0], end=SEPT[1]) == ()


def test_a_current_key_missing_from_the_new_snapshot_inside_the_range_is_absent():
    assert absent_keys(present=[key("BH2")], candidates=[candidate("BH1")],
                       start=SEPT[0], end=SEPT[1]) == (key("BH1"),)


def test_a_key_whose_date_is_outside_the_range_is_never_absent():
    """Ranh giới quan trọng nhất của slice B: phạm vi giới hạn thẩm quyền."""
    later = candidate("BH9", sale_date=date(2026, 9, 20))
    assert absent_keys(present=[], candidates=[later],
                       start=date(2026, 9, 1), end=date(2026, 9, 10)) == ()


@pytest.mark.parametrize("day,absent", [(1, True), (10, True), (11, False), (31, False)])
def test_the_range_is_inclusive_at_both_ends(day, absent):
    row = candidate("BH1", sale_date=date(2026, 8, 31) if day == 31 else date(2026, 9, day))
    found = absent_keys(present=[], candidates=[row],
                        start=date(2026, 9, 1), end=date(2026, 9, 10))
    assert bool(found) is absent


def test_a_key_without_a_sale_date_is_never_declared_absent():
    """Không biết dòng thuộc kỳ nào → không snapshot nào có thẩm quyền với nó."""
    assert absent_keys(present=[], candidates=[candidate("BH1", sale_date=None)],
                       start=SEPT[0], end=SEPT[1]) == ()


def test_a_key_under_identity_dispute_is_never_declared_absent():
    assert absent_keys(present=[], candidates=[candidate("BH1", collision=True)],
                       start=SEPT[0], end=SEPT[1]) == ()


def test_an_open_range_yields_nothing_rather_than_everything():
    """Không có phạm vi thì không có thẩm quyền — KHÔNG phải "vắng mặt tất cả"."""
    assert absent_keys(present=[], candidates=[candidate("BH1")],
                       start=None, end=None) == ()
    assert absent_keys(present=[], candidates=[candidate("BH1")],
                       start=SEPT[0], end=None) == ()


def test_each_occurrence_of_a_repeated_product_is_judged_on_its_own():
    rows = [candidate("BH1", occurrence=1), candidate("BH1", occurrence=2)]
    absent = absent_keys(present=[key("BH1", occurrence=1)], candidates=rows,
                         start=SEPT[0], end=SEPT[1])
    assert absent == (key("BH1", occurrence=2),)
