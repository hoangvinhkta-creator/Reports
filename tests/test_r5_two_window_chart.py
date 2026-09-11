"""R5 §3 — biểu đồ so HAI CỬA SỔ liền kề cùng độ dài.

Trước R5, biểu đồ dựng đúng MỘT `polyline`: Ngày/Tuần/Tháng cắt một chuỗi
theo container lịch của kỳ đang xem, Quý nhìn toàn bộ dòng thời gian. Không
có gì để so với cái gì — người đọc phải nhớ tháng trước bằng đầu.

Quyết định Owner 08/09/2026 (`DEC-R5-02`) dựng hai cửa sổ LIỀN KỀ cùng độ
dài. Quyết định Owner 09/09/2026 (`DEC-211`) giữ nguyên "cùng độ dài" nhưng đổi
cửa sổ so sánh sang CÙNG KỲ NĂM TRƯỚC ở CẢ NĂM mức. Quyết định Owner
11/09/2026 (`R7 §C`, `DEC-222`) đổi cửa sổ thành CONTAINER LỊCH — Ngày trong
một tháng (01 → cuối tháng), Tuần trong một quý, Tháng/Quý trong một năm, Năm
5 mốc — so với đúng container ấy của năm trước; đường hiện tại dừng ở mốc neo
("đến hiện tại"), và có dự phóng hết kỳ.

Hai bất biến phải sống sót qua thay đổi này, và cả hai được canh ở đây:

    MỘT engine doanh thu   `paired_series` KHÔNG cộng lại gì — nó chỉ chọn
                           và xếp các điểm mà `series()` đã tính.
    KHÔNG bịa số 0         thiếu bằng chứng là một khoảng TRỐNG; số 0 chỉ
                           được vẽ khi khoảng ngày ấy nằm trong một sổ đã
                           xác nhận đầy đủ.
"""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine

import tools.db as history_db
from app.web import business_service, business_store, history_store
from app.web import revenue_timeline as rt

from tests.test_employee_workspace_ux import SEPTEMBER, body, line, metric, persist
from tests.test_r3_web_workflow import client  # noqa: F401


@pytest.fixture
def engine():
    engine = create_engine("sqlite://")
    history_db.create_all_for_test(engine)
    return engine


@pytest.fixture
def repository(engine):
    return history_store.SnapshotRepository(engine)


@pytest.fixture
def store(engine):
    return business_store.BusinessDecisionStore(engine)


@pytest.fixture
def service(engine, store):
    return business_service.BusinessReportService(engine=engine, store=store)


def bars(html: str, metric_name: str = "chart-bar") -> dict:
    return {
        key: Decimal(value)
        for key, value in re.findall(
            rf'data-metric="{metric_name}" data-key="([^"]+)"[^>]*'
            r'data-revenue="([^"]+)"', html)
    }


# --- 1. Năm mức đều có hai đường, cửa sổ là CONTAINER LỊCH (`R7 §C`) -------

GRAN_KEYS = {"ngay": rt.DAY, "tuan": rt.WEEK, "thang": rt.MONTH,
             "quy": rt.QUARTER, "nam": rt.YEAR}


@pytest.mark.parametrize("gran,size", [
    ("ngay", 30), ("tuan", 14), ("thang", 12), ("quy", 4), ("nam", 5),
])
def test_every_granularity_draws_two_windows_on_the_calendar_container(
    repository, client, gran, size,
):
    """`R7 §C` — Owner: "dải 30 ngày sửa lại từ 1 đến cuối tháng", áp dụng
    cho cả tuần/tháng/quý/năm. Neo 30/09/2026: Ngày = 30 ngày của tháng 9,
    Tuần = 14 tuần ISO chạm Quý 3 (29/06 → 28/09), Tháng = 12, Quý = 4,
    Năm = 5 (không có container trên năm)."""
    persist(repository, [line("BH1", "43F6000", day=5, sell="8000000")])
    html = body(client, f"/kinh-doanh?muc={gran}&ky=2026-09")

    assert 'data-metric="chart-legend-current"' in html
    assert 'data-metric="chart-legend-comparison"' in html
    slots = rt.container_slots(GRAN_KEYS[gran], date(2026, 9, 30))
    assert len(slots) == size


def test_the_day_window_runs_from_the_first_to_the_last_day_of_the_month():
    slots = rt.container_slots(rt.DAY, date(2026, 9, 10))
    assert slots[0][0] == "2026-09-01" and slots[-1][0] == "2026-09-30"
    assert len(rt.container_slots(rt.DAY, date(2026, 2, 10))) == 28
    assert len(rt.container_slots(rt.DAY, date(2028, 2, 10))) == 29


@pytest.mark.parametrize("gran", ["ngay", "tuan", "thang", "quy", "nam"])
def test_the_comparison_window_is_the_same_container_one_year_earlier(gran):
    """`DEC-211` giữ nguyên ở điểm này: cùng kỳ NĂM TRƯỚC, không phải cửa sổ
    liền trước — nay là container của năm trước."""
    key = GRAN_KEYS[gran]
    anchor = date(2026, 9, 10)
    current = rt.container_slots(key, anchor)
    comparison = rt.container_slots(key, rt.comparison_anchor(key, anchor))
    # Mốc "cùng ngày năm trước" của mốc neo nằm TRONG container so sánh.
    assert rt.bucket_of(rt._same_period_last_year(key, anchor), key)[0] in {
        slot_key for slot_key, _label in comparison}
    low, high = rt.container_bounds(key, anchor)
    prev_low, prev_high = rt.container_bounds(key, rt.comparison_anchor(key, anchor))
    assert (low.year - prev_low.year, high.year - prev_high.year) == (1, 1)
    assert len(current) - len(comparison) in (-1, 0, 1)


def test_a_leap_february_pads_the_shorter_window_with_a_blank_slot():
    """Hai container lệch một mốc ⟹ cửa sổ ngắn hơn được ĐỆM một mốc trống,
    không mang số, không mang khoá lịch — hai đường vẫn chung một trục."""
    paired = rt.paired_series([], granularity=rt.DAY, anchor=date(2028, 2, 29))
    assert paired.size == 29
    pad = paired.comparison[-1]
    assert pad.is_gap and pad.key.startswith(rt.PAD_KEY_PREFIX) and pad.label == ""
    assert not any(slot.key.startswith(rt.PAD_KEY_PREFIX) for slot in paired.current)


def test_the_current_line_stops_at_the_anchor_and_the_comparison_runs_the_whole_container():
    """"Tháng này đến hiện tại" so với "tháng này năm trước TRỌN tháng"."""
    points = [rt.Point(key=f"2026-09-{day:02d}", label="", revenue=Decimal(1),
                       origin=rt.ORIGIN_CURRENT) for day in (5, 10, 25)]
    points += [rt.Point(key=f"2025-09-{day:02d}", label="", revenue=Decimal(1),
                        origin=rt.ORIGIN_CURRENT) for day in (5, 25)]
    paired = rt.paired_series(points, granularity=rt.DAY, anchor=date(2026, 9, 20))
    drawn = {slot.key for slot in paired.current if not slot.is_gap}
    assert drawn == {"2026-09-05", "2026-09-10"}, "25/09 nằm SAU mốc neo"
    previous = {slot.key for slot in paired.comparison if not slot.is_gap}
    assert previous == {"2025-09-05", "2025-09-25"}


def test_the_month_window_compares_against_the_same_year_last_year(
    repository, client,
):
    """Ở mức Tháng container là NĂM: 01→12/2026 so với 01→12/2025."""
    persist(repository, [
        line("BH1", "43F6000", month=9, day=5, sell="8000000"),
        line("BH2", "XP352", month=6, day=5, sell="3000000"),
    ])
    html = body(client, "/kinh-doanh?muc=thang&ky=2026-09")
    current, previous = bars(html), bars(html, "chart-bar-prev")
    assert set(current) & set(previous) == set(), "hai cửa sổ không được chồng nhau"
    assert "2026-09" in current and "2026-06" in current
    scope = metric(html, "chart-scope")
    assert "01/2026 → 12/2026" in scope
    assert "01/2025 → 12/2025" in scope


# --- 2. Một engine doanh thu, không công thức thứ hai --------------------

def test_the_current_window_reuses_exactly_the_existing_revenue_engine(
    repository, service, client,
):
    persist(repository, [
        line("BH1", "43F6000", day=5, sell="8000000"),
        line("BH2", "XP352", day=5, sell="2000000"),
        line("BH3", "Giá treo", day=7, sell="500000"),
    ])
    html = body(client, "/kinh-doanh?muc=ngay&ky=2026-09")
    current = bars(html)
    assert current["2026-09-05"] == Decimal("10000000")
    assert sum(current.values()) == service.period(**SEPTEMBER).totals.sales_revenue


def test_a_line_dropped_from_the_report_leaves_both_windows(
    repository, service, store, client,
):
    """Cùng tập dòng hiệu lực — biểu đồ không có đường đọc dữ liệu riêng."""
    persist(repository, [
        line("BH1", "43F6000", day=5, sell="8000000"),
        line("BH2", "XP352", day=5, sell="2000000"),
    ])
    detail = next(d for d in service.period(**SEPTEMBER).details
                  if d["order_key"] == "BH2")
    store.exclude_line(
        order_key=detail["order_key"], product_key=detail["product_key"],
        occurrence_index=detail["occurrence_index"], excluded_by="test",
        reason="kiểm")
    current = bars(body(client, "/kinh-doanh?muc=ngay&ky=2026-09"))
    assert current["2026-09-05"] == Decimal("8000000")


# --- 3. Thiếu bằng chứng là GAP, không phải 0 ---------------------------

def test_a_bucket_without_evidence_is_a_gap_and_not_a_zero(repository, client):
    persist(repository, [line("BH1", "43F6000", day=5, sell="8000000")])
    html = body(client, "/kinh-doanh?muc=ngay&ky=2026-09")
    current = bars(html)
    assert "2026-09-05" in current
    assert "2026-09-06" not in current, (
        "một ngày chưa có bằng chứng KHÔNG được vẽ thành cột 0")
    # Và đường bị CẮT, không nối thẳng qua chỗ trống.
    assert 'data-metric="chart-gap"' in html


def test_a_confirmed_complete_range_does_turn_an_empty_day_into_a_real_zero(
    repository, client,
):
    """Trong một sổ đã xác nhận đầy đủ, "không có đơn nào" là sự thật đo được."""
    pairs = [line("BH1", "43F6000", day=5, sell="8000000")]
    written = persist(repository, pairs, run_id="run-1",
                      at="2026-10-01T00:00:00", fingerprint="fp-a")
    repository.confirm_coverage(
        written.snapshot_id, start=date(2026, 9, 1), end=date(2026, 9, 30),
        confirmed=True, confirmed_at="2026-10-02T00:00:00")

    current = bars(body(client, "/kinh-doanh?muc=ngay&ky=2026-09"))
    assert current["2026-09-05"] == Decimal("8000000")
    # Mốc neo là ngày có dữ liệu MỚI NHẤT (05/09); ngày trống được kiểm phải
    # nằm TRƯỚC nó trong container tháng 9 (`R7 §C`: sau mốc neo là trống).
    assert current["2026-09-04"] == Decimal("0"), (
        "đã xác nhận đầy đủ ⟹ ngày trống là số 0 THẬT, không phải khoảng trống")


def test_the_gap_rule_is_pure_and_needs_the_whole_bucket_inside_the_range():
    """Một sổ đầy đủ cho 01–10/09 KHÔNG nói gì về mốc THÁNG 09/2026."""
    paired = rt.paired_series(
        [], granularity=rt.MONTH, anchor=date(2026, 9, 30),
        confirmed_ranges=[(date(2026, 9, 1), date(2026, 9, 10))])
    september = [slot for slot in paired.current if slot.key == "2026-09"][0]
    assert september.is_gap, "phủ một phần không phải phủ trọn"

    paired = rt.paired_series(
        [], granularity=rt.MONTH, anchor=date(2026, 9, 30),
        confirmed_ranges=[(date(2026, 9, 1), date(2026, 9, 30))])
    september = [slot for slot in paired.current if slot.key == "2026-09"][0]
    assert september.revenue == Decimal(0)


# --- 4. KPI phía trên không đổi theo cửa sổ biểu đồ ---------------------

def test_the_kpi_strip_above_does_not_move_with_the_chart_window(
    repository, client,
):
    persist(repository, [
        line("BH1", "43F6000", month=9, day=5, sell="8000000"),
        line("BH2", "XP352", month=6, day=5, sell="3000000"),
    ])
    strips = [
        (metric(html, "orders"), metric(html, "lines"))
        for html in (body(client, f"/kinh-doanh?muc={gran}&ky=2026-09")
                     for gran in ("ngay", "tuan", "thang", "quy", "nam"))
    ]
    assert len(set(strips)) == 1, "đổi mức gộp biểu đồ KHÔNG được đổi chỉ tiêu kỳ"
    assert strips[0] == ("1", "1"), "chỉ tiêu vẫn là của kỳ 09/2026, không của cửa sổ"
