"""R6 §1 — hợp đồng phạm vi: ĐÚNG MỘT phạm vi, không bao giờ hai.

Mọi bài ở đây chạy trên giá trị thuần: `analysis_range` không đọc database,
không dựng request, nên quy tắc kiểm được mà không cần cả một vertical.
"""

from __future__ import annotations

from datetime import date

import pytest

from app.modules.reporting import analysis_range as ar
from app.web import analytics_queries
from app.web import business_service


def resolve(**kwargs):
    kwargs.setdefault("period_raw", None)
    kwargs.setdefault("from_raw", None)
    kwargs.setdefault("to_raw", None)
    kwargs.setdefault("fallback_period", (2026, 5))
    return ar.resolve(**kwargs)


# --- Một phạm vi, không hai -------------------------------------------------

def test_a_period_alone_resolves_to_that_month():
    scope = resolve(period_raw="2026-09")
    assert scope.kind == ar.SCOPE_PERIOD
    assert scope.period == (2026, 9)
    assert (scope.date_from, scope.date_to) == (date(2026, 9, 1), date(2026, 9, 30))
    assert scope.note is None


def test_a_valid_custom_range_wins_over_the_period_and_carries_no_period():
    """Hai phạm vi gửi cùng lúc ⟹ khoảng ngày thắng, và `period` là `None`.

    `period is None` không phải một chi tiết: nó là thứ giữ cho không màn hình
    nào truyền một tháng vào `service.period(period=...)` và mượn trạng thái
    chốt kỳ của tháng đó cho một khoảng ngày tự chọn.
    """
    scope = resolve(period_raw="2026-09", from_raw="2026-09-03",
                    to_raw="2026-09-11")
    assert scope.kind == ar.SCOPE_CUSTOM
    assert scope.period is None
    assert (scope.date_from, scope.date_to) == (date(2026, 9, 3), date(2026, 9, 11))


def test_the_two_scopes_are_never_intersected():
    """Khoảng ngày NGOÀI tháng đang chọn vẫn được giữ NGUYÊN VẸN.

    Giao hai phạm vi là cách im lặng nhất để một trang trả về ít tiền hơn cả
    hai phạm vi mà người dùng nghĩ mình đã chọn — nên phép giao ấy không được
    tồn tại, kể cả khi hai phạm vi rời nhau hoàn toàn.
    """
    scope = resolve(period_raw="2026-09", from_raw="2026-01-01",
                    to_raw="2026-02-28")
    assert (scope.date_from, scope.date_to) == (date(2026, 1, 1), date(2026, 2, 28))
    assert scope.kind == ar.SCOPE_CUSTOM


def test_a_custom_range_cannot_be_constructed_with_a_period():
    with pytest.raises(ValueError, match="CUSTOM"):
        ar.AnalysisRange(kind=ar.SCOPE_CUSTOM, date_from=date(2026, 1, 1),
                         date_to=date(2026, 1, 2), label="x", period=(2026, 1))


def test_a_period_scope_must_name_its_period():
    with pytest.raises(ValueError, match="PERIOD"):
        ar.AnalysisRange(kind=ar.SCOPE_PERIOD, date_from=date(2026, 1, 1),
                         date_to=date(2026, 1, 2), label="x")


# --- Từ chối, kèm LÝ DO ----------------------------------------------------

def test_a_reversed_range_is_refused_with_a_reason_and_never_swapped():
    scope = resolve(period_raw="2026-09", from_raw="2026-09-20",
                    to_raw="2026-09-10")
    assert scope.kind == ar.SCOPE_PERIOD
    assert scope.period == (2026, 9)
    assert scope.note == ar.NOTE_REVERSED


def test_half_a_range_is_refused_with_the_incomplete_reason():
    scope = resolve(period_raw="2026-09", from_raw="2026-09-01")
    assert scope.kind == ar.SCOPE_PERIOD
    assert scope.note == ar.NOTE_INCOMPLETE


def test_an_unreadable_range_is_refused_with_the_unreadable_reason():
    scope = resolve(period_raw="2026-09", from_raw="01/09/2026",
                    to_raw="10/09/2026")
    assert scope.kind == ar.SCOPE_PERIOD
    assert scope.note == ar.NOTE_UNREADABLE


def test_a_refusal_is_never_silent():
    """Mọi nhánh từ chối phải mang `note`; im lặng ở đây nghĩa là người dùng
    tưởng khoảng ngày của họ đang được áp dụng."""
    for kwargs in ({"from_raw": "2026-09-20", "to_raw": "2026-09-10"},
                   {"from_raw": "2026-09-01"},
                   {"to_raw": "2026-09-01"},
                   {"from_raw": "hôm qua", "to_raw": "hôm nay"}):
        assert resolve(period_raw="2026-09", **kwargs).note is not None


def test_no_range_typed_at_all_produces_no_note():
    assert resolve(period_raw="2026-09").note is None


# --- Rơi về mặc định --------------------------------------------------------

def test_an_invalid_period_falls_back_to_the_caller_default():
    for raw in (None, "", "2026", "2026-13", "1200-01", "abc-def"):
        assert resolve(period_raw=raw).period == (2026, 5)


# --- Cùng quy ước cận ngày với hai hàm đã nghiệm thu ------------------------

def test_month_bounds_matches_the_two_existing_implementations():
    """`analysis_range.month_bounds` phải khớp TỪNG NGÀY với `analytics_
    queries.month_bounds` và `business_service._month_bounds`.

    Ba bản cùng tồn tại là một sự thật của repo này; điều KHÔNG được phép là
    chúng trôi khỏi nhau, vì khi ấy hai trang cùng chọn "tháng 2" sẽ đọc hai
    khoảng ngày khác nhau.
    """
    for year in (2024, 2025, 2026):
        for month in range(1, 13):
            mine = ar.month_bounds(year, month)
            assert mine == analytics_queries.month_bounds(year, month)
            assert mine == business_service._month_bounds(year, month)


def test_february_of_a_leap_year_ends_on_the_29th():
    assert ar.month_bounds(2024, 2)[1] == date(2024, 2, 29)


def test_days_counts_the_upper_bound_inclusively():
    assert ar.custom_range(date(2026, 9, 1), date(2026, 9, 1)).days == 1
    assert ar.period_range((2026, 9)).days == 30


def test_period_value_is_empty_for_a_custom_scope():
    """Bộ chọn kỳ KHÔNG được sáng lên ở một tháng nào khi phạm vi là khoảng
    ngày — không tháng nào là phạm vi đang xem."""
    assert ar.custom_range(date(2026, 9, 1), date(2026, 9, 5)).period_value == ""
    assert ar.period_range((2026, 9)).period_value == "2026-09"
