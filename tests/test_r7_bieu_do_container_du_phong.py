"""R7 §C + §D — biểu đồ theo CONTAINER LỊCH, dự phóng hết kỳ, số đơn lấp lỗ hổng.

Owner (2026-09-11): *"hiển thị trên biểu đồ là dải 30 ngày sửa lại từ 1 đến
cuối tháng, hiển thị đường doanh số tháng này kì trước và tháng này kì này đến
hiện tại. Thể hiện với tốc độ này thì cuối tháng sẽ đạt được bao nhiêu % so
với kì trước — áp dụng cho cả tuần - tháng - quý - năm"*; và *"biểu đồ số đơn:
lọc ra duy nhất thông tin số đơn [từ sổ thô] để bổ sung dữ liệu cho biểu đồ"*.

Hình dạng cửa sổ được canh ở `tests/test_r5_two_window_chart.py`. File này
canh hai thứ còn lại: PHÉP DỰ PHÓNG (một phép chia, đọc được cả ba số) và
CHUỖI SỐ ĐƠN có lấp lỗ hổng (mỗi ngày đúng một nguồn).
"""
from __future__ import annotations

import re
from datetime import date
from decimal import Decimal
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine

import tools.db as history_db
from app.modules.reporting import line_type as line_type_module
from app.web import business_service, business_store, chart_gapfill, history_store
from app.web import revenue_timeline as rt

from tests.test_employee_workspace_ux import body, line, persist
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
def service(engine):
    return business_service.BusinessReportService(
        engine=engine, store=business_store.BusinessDecisionStore(engine))


def points(values: dict, granularity: str = rt.DAY) -> list[rt.Point]:
    return [rt.Point(key=key, label=rt.bucket_of(date.fromisoformat(key), rt.DAY)[1]
                     if granularity == rt.DAY else key,
                     revenue=Decimal(value), origin=rt.ORIGIN_CURRENT)
            for key, value in values.items()]


# --- 1. Dự phóng: một phép chia, ba con số ---------------------------------

def test_the_day_projection_divides_by_the_elapsed_share_of_the_month():
    """Tháng 9: 10 ngày đầu mỗi ngày 10 ⟹ 100 tới mốc neo 10/09; 10/30 tháng
    đã trôi ⟹ dự phóng 300. Cùng kỳ năm trước trọn tháng 30 × 12 = 360 ⟹
    83 %; tới cùng mốc (10 ngày) năm trước = 120 ⟹ 83 %."""
    current = {f"2026-09-{d:02d}": 10 for d in range(1, 11)}
    previous = {f"2025-09-{d:02d}": 12 for d in range(1, 31)}
    paired = rt.paired_series(points({**current, **previous}), granularity=rt.DAY,
                              anchor=date(2026, 9, 10))
    projection = rt.project(paired)
    assert (projection.elapsed_units, projection.total_units) == (10, 30)
    assert projection.current_to_date == Decimal(100)
    assert projection.projected_total == Decimal(300)
    assert projection.comparison_total == Decimal(360)
    assert projection.comparison_to_date == Decimal(120)
    assert projection.projected_percent == Decimal(83)
    assert projection.to_date_percent == Decimal(83)
    assert projection.comparison_gaps == 0


def test_the_week_projection_measures_days_inside_the_quarter():
    paired = rt.paired_series(points({"2026-08-10": 46}), granularity=rt.WEEK,
                              anchor=date(2026, 8, 15))
    projection = rt.project(paired)
    # Quý 3/2026: 01/07 → 30/09 = 92 ngày; tới 15/08 là 46 ngày.
    assert (projection.elapsed_units, projection.total_units) == (46, 92)
    assert projection.projected_total == Decimal(92)


def test_the_year_level_projects_this_year_against_last_year_only():
    paired = rt.paired_series(
        points({"2026": 253, "2025": 400, "2024": 999}, rt.YEAR),
        granularity=rt.YEAR, anchor=date(2026, 9, 10))
    projection = rt.project(paired)
    # Ngày 10/09 là ngày thứ 253 của năm 2026 (không nhuận, 365 ngày).
    assert (projection.elapsed_units, projection.total_units) == (253, 365)
    assert projection.current_to_date == Decimal(253)
    assert projection.projected_total == Decimal(365)
    assert projection.comparison_total == Decimal(400), "chỉ NĂM TRƯỚC, không 5 năm"
    assert projection.projected_percent == Decimal(91)


def test_a_missing_last_year_gives_no_percent_but_still_a_projection():
    paired = rt.paired_series(points({"2026-09-05": 30}), granularity=rt.DAY,
                              anchor=date(2026, 9, 5))
    projection = rt.project(paired)
    assert projection.projected_total == Decimal(180)
    assert projection.projected_percent is None and projection.to_date_percent is None
    assert projection.comparison_gaps == 30, "30 ngày năm trước đều chưa có bằng chứng"


def test_projection_ignores_data_after_the_anchor_and_pad_slots():
    """Một số có trong sổ nhưng SAU mốc neo (phạm vi tự chọn) không được dự
    phóng — nó không thuộc "đến hiện tại"."""
    paired = rt.paired_series(points({"2026-09-05": 10, "2026-09-25": 990}),
                              granularity=rt.DAY, anchor=date(2026, 9, 10))
    assert rt.project(paired).current_to_date == Decimal(10)
    assert rt.project(None) is None


# --- 2. Chuỗi số đơn có lấp lỗ hổng --------------------------------------

def detail(order: str, when: date) -> dict:
    return {"sale_date": when, "line": SimpleNamespace(
        order_key=order, total_sales=Decimal(1), discount=Decimal(0),
        quantity=Decimal(1), line_type=line_type_module.TYPE_SALE)}


GAPFILL = [
    {"year": 2026, "month": 9, "day": 5, "orders": 7},   # ngày sổ nạp ĐÃ nói tới
    {"year": 2026, "month": 9, "day": 6, "orders": 3},   # ngày sổ nạp im lặng
    {"year": 2025, "month": 9, "day": 6, "orders": 4},
]


def test_count_series_fills_only_the_days_the_book_is_silent_about():
    details = [detail("BH1", date(2026, 9, 5)), detail("BH1", date(2026, 9, 5)),
               detail("BH2", date(2026, 9, 5))]
    by_key = {p.key: p for p in rt.count_series(details, granularity=rt.DAY,
                                                gapfill_days=GAPFILL)}
    assert by_key["2026-09-05"].revenue == Decimal(2), "sổ nạp thắng: 2 đơn, không phải 7"
    assert by_key["2026-09-05"].origin == rt.ORIGIN_CURRENT
    assert by_key["2026-09-06"].revenue == Decimal(3)
    assert by_key["2026-09-06"].origin == rt.ORIGIN_GAPFILL
    assert by_key["2025-09-06"].origin == rt.ORIGIN_GAPFILL


def test_count_series_reaches_month_level_and_says_it_is_mixed():
    """Khác doanh số: KHÔNG có tổng tháng lịch sử nào cho số đơn, nên nguồn
    lấp được gộp lên Tháng — theo NGÀY, mỗi ngày một nguồn."""
    details = [detail("BH1", date(2026, 9, 5))]
    by_key = {p.key: p for p in rt.count_series(details, granularity=rt.MONTH,
                                                gapfill_days=GAPFILL)}
    september = by_key["2026-09"]
    assert september.revenue == Decimal(4)          # 1 (sổ nạp) + 3 (lấp), KHÔNG + 7
    assert september.origin == rt.ORIGIN_MIXED
    assert september.origins == frozenset({rt.ORIGIN_CURRENT, rt.ORIGIN_GAPFILL})
    assert by_key["2025-09"].origin == rt.ORIGIN_GAPFILL


@pytest.mark.chart_gapfill
def test_the_committed_orders_source_is_dates_and_counts_only(tmp_path):
    rows = chart_gapfill.load_daily_order_rows(chart_gapfill.GAPFILL_ORDERS_PATH)
    assert rows, "file đã commit phải đọc được"
    assert all(set(row) == {"year", "month", "day", "orders"} for row in rows)
    assert all(isinstance(row["orders"], int) and row["orders"] >= 0 for row in rows)
    bad = tmp_path / "x.jsonl"
    bad.write_text('{"date": "2026-01-01", "orders": 2.5}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="số nguyên"):
        chart_gapfill.load_daily_order_rows(bad)
    bad.write_text('{"date": "2026-01-01", "orders": -1}\n', encoding="utf-8")
    with pytest.raises(ValueError, match="số đơn âm"):
        chart_gapfill.load_daily_order_rows(bad)


# --- 3. Trên trang thật -------------------------------------------------------

def projection_of(html: str, dom_id: str) -> dict:
    block = html.split(f'id="{dom_id}"', 1)[1]
    match = re.search(r'data-metric="chart-projection"[^>]*data-projected="([^"]*)"'
                      r'[^>]*data-percent="([^"]*)"[^>]*>(.*?)</p>', block, re.S)
    assert match is not None, f"{dom_id} phải có dòng dự phóng"
    return {"projected": match.group(1), "percent": match.group(2),
            "text": " ".join(match.group(3).split())}


def test_both_charts_on_the_report_page_show_the_projection_line(repository, client):
    persist(repository, [line("BH1", "43F6000", day=5, sell="8000000")])
    html = body(client, "/kinh-doanh?muc=ngay&ky=2026-09")
    revenue = projection_of(html, "bieu-do-doanh-thu")
    # 8.000.000 sau 5/30 ngày ⟹ 48.000.000; năm trước chưa có số ⟹ không %.
    assert revenue["projected"] == "48000000" and revenue["percent"] == ""
    assert "5/30 ngày của tháng" in revenue["text"]
    assert "chưa có số để so" in revenue["text"]
    orders = projection_of(html, "bieu-do-so-don")
    assert orders["projected"] == "6"
    assert "đơn" in orders["text"]


def test_the_percent_appears_when_last_year_has_a_number(repository, client):
    persist(repository, [
        line("BH1", "43F6000", day=10, sell="8000000"),
        line("BH0", "43F6000", year=2025, month=9, day=3, sell="12000000"),
    ])
    html = body(client, "/kinh-doanh?muc=ngay&ky=2026-09")
    revenue = projection_of(html, "bieu-do-doanh-thu")
    # 8tr sau 10/30 ⟹ 24tr; năm trước trọn tháng 12tr ⟹ 200 %.
    assert revenue["projected"] == "24000000" and revenue["percent"] == "200"
    assert "200%" in revenue["text"]
