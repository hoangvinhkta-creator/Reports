"""R5 §3 — biểu đồ so HAI CỬA SỔ liền kề cùng độ dài.

Trước R5, biểu đồ dựng đúng MỘT `polyline`: Ngày/Tuần/Tháng cắt một chuỗi
theo container lịch của kỳ đang xem, Quý nhìn toàn bộ dòng thời gian. Không
có gì để so với cái gì — người đọc phải nhớ tháng trước bằng đầu.

Quyết định Owner 08/09/2026 (`DEC-R5-02`): hai cửa sổ LIỀN KỀ có CÙNG độ
dài — 30 ngày, 12 tuần, 12 tháng, 8 quý. "Cùng độ dài" là phần quan trọng
nhất và là lý do bỏ cách khoanh theo container lịch: tháng 2 có 28 ngày còn
tháng 3 có 31, nên hai container liền nhau không so được với nhau.

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


# --- 1. Bốn mức đều có hai đường, cửa sổ đúng độ dài ----------------------

@pytest.mark.parametrize("gran,size", [
    ("ngay", 30), ("tuan", 12), ("thang", 12), ("quy", 8),
])
def test_every_windowed_granularity_draws_two_windows_of_the_same_length(
    repository, client, gran, size,
):
    persist(repository, [line("BH1", "43F6000", day=5, sell="8000000")])
    html = body(client, f"/kinh-doanh?muc={gran}&ky=2026-09")

    assert rt.COMPARISON_WINDOW_SIZES[
        {"ngay": rt.DAY, "tuan": rt.WEEK,
         "thang": rt.MONTH, "quy": rt.QUARTER}[gran]] == size
    assert 'data-metric="chart-legend-current"' in html
    assert 'data-metric="chart-legend-comparison"' in html
    # Trục X mang đúng `size` vị trí, và cả hai cửa sổ dùng chung nó.
    slots = rt.window_slots(
        {"ngay": rt.DAY, "tuan": rt.WEEK,
         "thang": rt.MONTH, "quy": rt.QUARTER}[gran], date(2026, 9, 30), size)
    assert len(slots) == size


def test_the_year_level_keeps_a_single_series(repository, client):
    """Owner không yêu cầu cửa sổ so sánh ở mức Năm — không tự thêm."""
    persist(repository, [line("BH1", "43F6000", day=5, sell="8000000")])
    html = body(client, "/kinh-doanh?muc=nam")
    assert 'data-metric="chart-bar-prev"' not in html
    assert 'data-metric="chart-legend-current"' not in html


def test_the_two_windows_are_adjacent_and_do_not_overlap(repository, client):
    """Cửa sổ so sánh kết thúc ĐÚNG một mốc trước khi cửa sổ hiện tại bắt đầu."""
    persist(repository, [
        line("BH1", "43F6000", month=9, day=5, sell="8000000"),
        line("BH2", "XP352", month=6, day=5, sell="3000000"),
    ])
    html = body(client, "/kinh-doanh?muc=thang&ky=2026-09")
    current, previous = bars(html), bars(html, "chart-bar-prev")
    assert set(current) & set(previous) == set(), "hai cửa sổ không được chồng nhau"
    assert "2026-09" in current and "2026-06" in current
    scope = metric(html, "chart-scope")
    assert "10/2025 → 09/2026" in scope
    assert "10/2024 → 09/2025" in scope


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
    assert current["2026-09-06"] == Decimal("0"), (
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
