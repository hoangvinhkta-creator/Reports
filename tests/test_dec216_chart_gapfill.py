"""`DEC-216` — nguồn lấp lỗ hổng của biểu đồ: xuất xứ, thẩm quyền, bề mặt.

Owner mở trang Báo cáo ở mức Ngày và thấy đường "Cùng kỳ năm trước" trống
trơn. Nguyên nhân đã xác minh: sổ cũ chỉ lưu TỔNG THÁNG, và `§CHART-10` cấm
chia một tổng tháng ra thành ngày. `DEC-216` mở một nguồn thứ ba, chỉ để VẼ.

Một nguồn thứ ba là chỗ dễ làm hỏng sổ sách nhất trong cả module này, nên
file này kiểm đúng những mệnh đề giữ nó ở đúng chỗ:

    THỨ TỰ THẨM QUYỀN      sổ nạp → sổ cũ → lấp lỗ hổng, giải ở mức NGÀY
    KHÔNG CHEN VÀO SỔ SÁCH  chỉ Ngày/Tuần, chỉ biểu đồ doanh thu
    LUÔN ĐỌC RA ĐƯỢC        `DEC-166 E` — mốc lấp lỗ hổng tự khai trên màn hình
    HỎNG THÌ DỪNG           file sai định dạng nổ, file vắng mặt thì không

Marker `chart_gapfill` là cách DUY NHẤT bật lại nguồn thật đã commit (xem
fixture autouse trong `tests/conftest.py`), nên nó cũng là danh sách tường
minh những test được phép đọc dữ liệu thật.
"""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine

import tools.db as history_db
from app.web import (
    business_presentation, business_service, business_store, chart_gapfill,
    history_store, identity_gateway, revenue_timeline as rt,
)
from app.web import server as web_server
from tests.support import identity_fixtures as fx
from tests.test_dec185_nav_chart_identity import chart_block
from tests.test_employee_workspace_ux import TODAY, body, line, persist
from tools.tracking import live_pull

#: Phạm vi mà `data/chart_gapfill/PROVENANCE.md` khai — mọi ngày trong file
#: phải nằm trong đó. Một ngày ngoài phạm vi nghĩa là bước nắn ngày trong quy
#: trình trích xuất đã hỏng, và nó sẽ vẽ ra một chấm ở chỗ không ai kiểm được.
SCOPE_LOW, SCOPE_HIGH = date(2025, 1, 1), date(2026, 8, 31)


def day_row(when: date, vnd: str) -> dict:
    return {"year": when.year, "month": when.month, "day": when.day,
            "sales_vnd": Decimal(vnd)}


# --- Nguồn: chính file đã commit ------------------------------------------

@pytest.mark.chart_gapfill
def test_the_committed_source_parses_and_says_one_value_per_day():
    rows = chart_gapfill.load_daily_rows()
    assert rows, "file nguồn đã commit phải đọc được"
    days = [date(row["year"], row["month"], row["day"]) for row in rows]
    assert days == sorted(days), "phải sắp theo thời gian"
    assert len(set(days)) == len(days), "một ngày chỉ được có MỘT giá trị"
    assert all(SCOPE_LOW <= when <= SCOPE_HIGH for when in days), (
        "mọi ngày phải nằm trong phạm vi mà PROVENANCE.md khai")
    assert all(row["sales_vnd"] > 0 for row in rows), (
        "một ngày không có doanh số thì VẮNG MẶT, không phải bằng 0 — "
        "khoảng trống là 'không có bằng chứng' (GAP_NOTE)")


@pytest.mark.chart_gapfill
def test_the_committed_source_is_recorded_in_vnd_not_thousands():
    """Đơn vị sai hệ số 1.000 sẽ vẽ ra một đường cong trông y như thật.

    Không có cách nào kiểm đơn vị bằng chính file, nên bài kiểm neo vào một
    sự thật NGHIỆP VỤ: doanh số một ngày của cửa hàng này ở mức trăm triệu
    tới vài tỉ đồng. Ghi bằng nghìn đồng sẽ cho ra những con số dưới một
    triệu, và bài kiểm này bắt được đúng lỗi ấy.
    """
    rows = chart_gapfill.load_daily_rows()
    peak = max(row["sales_vnd"] for row in rows)
    assert peak > Decimal("100000000"), (
        f"đỉnh {peak} quá nhỏ để là VND — nhiều khả năng file còn ở kVND")


def test_a_missing_source_file_is_a_quiet_return_to_the_old_shape(tmp_path):
    """Mất file KHÔNG được làm sập trang Báo cáo — nó chỉ đưa biểu đồ về
    đúng hình dạng trước `DEC-216`, tức là có lỗ hổng."""
    assert chart_gapfill.load_daily_rows(tmp_path / "khong-co.jsonl") == ()


def test_a_malformed_line_stops_instead_of_drawing_a_lower_curve(tmp_path):
    """Bỏ qua một dòng hỏng trong im lặng sẽ vẽ ra một đường THẤP HƠN sự thật
    mà không ai nhìn ra được — nên nó phải dừng."""
    path = tmp_path / "hong.jsonl"
    path.write_text('{"date": "2025-08-21", "sales_vnd": "1000"}\n'
                    'khong-phai-json\n', encoding="utf-8")
    with pytest.raises(ValueError, match="không phải JSON hợp lệ"):
        chart_gapfill.load_daily_rows(path)


def test_the_same_day_twice_is_refused(tmp_path):
    """`DEC-180` §9 — MỘT kỳ ⟹ MỘT nguồn ⟹ MỘT giá trị, kiểm ngay ở cửa đọc."""
    path = tmp_path / "lap.jsonl"
    path.write_text('{"date": "2025-08-21", "sales_vnd": "1000"}\n'
                    '{"date": "2025-08-21", "sales_vnd": "2000"}\n',
                    encoding="utf-8")
    with pytest.raises(ValueError, match="xuất hiện hai lần"):
        chart_gapfill.load_daily_rows(path)


def test_a_negative_day_is_refused(tmp_path):
    path = tmp_path / "am.jsonl"
    path.write_text('{"date": "2025-08-21", "sales_vnd": "-1"}\n',
                    encoding="utf-8")
    with pytest.raises(ValueError, match="doanh số âm"):
        chart_gapfill.load_daily_rows(path)


# --- Thẩm quyền: sổ nạp → sổ cũ → lấp lỗ hổng ------------------------------

def test_a_pipeline_day_is_never_overwritten_by_the_gapfill_source():
    """Một con số dựng để VẼ không bao giờ được đè lên một con số dùng để
    ĐỐI SOÁT — kể cả khi nguồn lấp có giá trị cho đúng ngày đó."""
    details = [{"sale_date": date(2026, 8, 20),
                "line": type("L", (), {"total_sales": Decimal("7")})()}]
    points = rt.series(details, granularity=rt.DAY,
                       gapfill_days=[day_row(date(2026, 8, 20), "999")])
    assert [(p.key, p.revenue, p.origin) for p in points] == [
        ("2026-08-20", Decimal("7"), rt.ORIGIN_CURRENT)]


def test_a_legacy_day_is_never_overwritten_by_the_gapfill_source():
    points = rt.series([], granularity=rt.DAY,
                       legacy_days=[day_row(date(2025, 3, 4), "5")],
                       gapfill_days=[day_row(date(2025, 3, 4), "999")])
    assert [(p.key, p.revenue, p.origin) for p in points] == [
        ("2025-03-04", Decimal("5"), rt.ORIGIN_LEGACY)]


def test_the_gapfill_source_fills_only_the_days_nobody_else_claims():
    points = rt.series([], granularity=rt.DAY,
                       legacy_days=[day_row(date(2025, 3, 4), "5")],
                       gapfill_days=[day_row(date(2025, 3, 4), "999"),
                                     day_row(date(2025, 3, 5), "8")])
    assert {p.key: (p.revenue, p.origin) for p in points} == {
        "2025-03-04": (Decimal("5"), rt.ORIGIN_LEGACY),
        "2025-03-05": (Decimal("8"), rt.ORIGIN_GAPFILL)}


@pytest.mark.parametrize("granularity", [rt.MONTH, rt.QUARTER, rt.YEAR])
def test_the_gapfill_source_never_reaches_month_quarter_or_year(granularity):
    """Ở đó tổng tháng chính thức đã có mặt; cộng thêm một nguồn thứ hai cho
    cùng một tháng là đúng thứ `_merge_resolved` sinh ra để chặn."""
    points = rt.series([], granularity=granularity,
                       legacy_months=[{"year": 2025, "month": 3,
                                       "sales_vnd": Decimal("50")}],
                       gapfill_days=[day_row(date(2025, 3, 4), "999")])
    assert [(p.revenue, p.origin) for p in points] == [
        (Decimal("50"), rt.ORIGIN_LEGACY)]


def test_a_week_straddling_the_pipeline_start_says_what_it_is_mixed_of():
    """Tuần vắt qua ngày sổ nạp bắt đầu chạy có CẢ hai nguồn. Nó phải nói ra
    rằng phần kia là bảng kê ngày, KHÔNG phải bản ghi lịch sử — dùng nhầm câu
    ở đây là nói sai về chính con số người đọc đang nhìn (`DEC-166 E`)."""
    monday, thursday = date(2026, 8, 31), date(2026, 9, 3)
    details = [{"sale_date": thursday,
                "line": type("L", (), {"total_sales": Decimal("4")})()}]
    points = rt.series(details, granularity=rt.WEEK,
                       gapfill_days=[day_row(monday, "6")])
    assert len(points) == 1
    point = points[0]
    assert point.revenue == Decimal("10")
    assert point.origin == rt.ORIGIN_MIXED
    assert point.has_gapfill and not point.is_gapfill
    title = business_presentation._chart_bar_title(point)
    assert rt.MIXED_GAPFILL_POINT_NOTE in title
    assert rt.MIXED_POINT_NOTE not in title


def test_a_day_level_gapfill_point_explains_itself():
    points = rt.series([], granularity=rt.DAY,
                       gapfill_days=[day_row(date(2025, 3, 5), "8")])
    assert rt.GAPFILL_POINT_NOTE in business_presentation._chart_bar_title(
        points[0])


def test_the_gapfill_note_replaces_the_no_daily_legacy_note():
    """Hai câu LOẠI TRỪ NHAU: câu kia giải thích một khoảng trống, và giữ nó
    cạnh một đường đã liền là nói với người đọc rằng chỗ họ đang thấy số vẫn
    đang trống."""
    points = rt.series([], granularity=rt.DAY,
                       gapfill_days=[day_row(date(2025, 3, 5), "8")])
    paired = rt.paired_series(points, granularity=rt.DAY,
                              anchor=date(2025, 3, 5))
    chart = business_presentation.paired_revenue_chart(
        paired, granularity=rt.DAY, has_legacy_months=True)
    assert chart["gapfill_note"] == rt.GAPFILL_CHART_NOTE
    assert chart["no_daily_legacy_note"] is None


# --- Bề mặt thật: từ file đã commit ra tới HTML ----------------------------

@pytest.fixture
def engine():
    engine = create_engine("sqlite://")
    history_db.create_all_for_test(engine)
    return engine


@pytest.fixture
def client(engine, monkeypatch, tmp_path, identity_store_path):
    monkeypatch.setattr(web_server, "select_latest_valid_captures", lambda: None)
    monkeypatch.setattr(live_pull, "is_configured", lambda env=None: False)
    monkeypatch.setattr(web_server, "_today", lambda: TODAY)
    monkeypatch.setattr(identity_gateway, "build_store",
                        lambda: identity_store_path)
    application = web_server.create_app(
        db_path=tmp_path / "runs.db",
        history=history_store.LegacyRepository(engine),
        snapshots=history_store.SnapshotRepository(engine))
    application.testing = True
    return application.test_client()


@pytest.fixture
def identity_store_path(tmp_path):
    return fx.store(tmp_path)


def origins(html: str, metric: str) -> dict[str, str]:
    """`{khoá mốc: origin}` đọc từ chính HTML.

    Dấu ngăn giữa hai thuộc tính là `[^>]*`, không phải một dấu cách: Jinja
    xuống dòng ở chỗ khác nhau tuỳ độ dài của `title`, nên một regex đòi đúng
    một dấu cách sẽ trả về `{}` trên một trang và đúng trên trang kia — và một
    bài kiểm trả `{}` là một bài kiểm không bao giờ đỏ được.
    """
    return dict(re.findall(
        rf'data-metric="{metric}"[^>]*data-key="([^"]+)"[^>]*'
        r'data-origin="([^"]+)"', chart_block(html, "bieu-do-doanh-thu")))


@pytest.mark.chart_gapfill
def test_the_comparison_line_is_drawn_and_labelled_as_gapfill(repository_client):
    """Câu hỏi Owner thật sự hỏi: cùng kỳ năm trước đã có đường chưa, và có
    nhìn ra nó không phải sổ sách không."""
    client = repository_client
    html = body(client, "/kinh-doanh?muc=ngay")
    previous = origins(html, "chart-bar-prev")
    assert previous, "cửa sổ so sánh phải có mốc — đây là lỗ hổng DEC-216 lấp"
    assert set(previous.values()) == {rt.ORIGIN_GAPFILL}, (
        "mọi mốc của cùng kỳ năm trước ở đây đều đến từ nguồn lấp lỗ hổng")
    assert 'data-metric="chart-gapfill"' in html, (
        "biểu đồ phải tự khai nguồn lấp lỗ hổng (DEC-166 E)")
    assert 'data-metric="chart-no-daily-legacy"' not in html


@pytest.mark.chart_gapfill
def test_the_current_window_stays_pipeline_only(repository_client):
    """Nguồn lấp KHÔNG được chen vào những ngày sổ nạp đã nói tới — nếu chen
    được thì con số trên biểu đồ và ô chỉ tiêu ở trên sẽ lệch nhau."""
    html = body(repository_client, "/kinh-doanh?muc=ngay")
    current = origins(html, "chart-bar")
    assert current, "cửa sổ hiện tại phải có mốc của sổ nạp"
    assert current.get("2026-09-03") == rt.ORIGIN_CURRENT


@pytest.mark.chart_gapfill
def test_the_orders_chart_reads_its_own_gapfill_source(repository_client):
    """`R7 §D` — trước đây biểu đồ Số đơn KHÔNG đọc nguồn lấp lỗ hổng vì nguồn
    doanh số không có đơn nào. Nay số đơn có nguồn RIÊNG
    (`data/chart_gapfill/daily_orders.jsonl`, chỉ ngày + số chứng từ), và
    đường "Cùng kỳ năm trước" của nó phải có mốc — tự khai là lấp lỗ hổng."""
    html = body(repository_client, "/kinh-doanh?muc=ngay")
    block = chart_block(html, "bieu-do-so-don")
    assert 'data-metric="chart"' in block, "biểu đồ Số đơn vẫn phải có mặt"
    previous = dict(re.findall(
        r'data-metric="chart-bar-prev"[^>]*data-key="([^"]+)"[^>]*'
        r'data-origin="([^"]+)"', block))
    assert previous and set(previous.values()) == {rt.ORIGIN_GAPFILL}
    assert rt.GAPFILL_COUNT_CHART_NOTE[:40] in block
    # Ngày sổ nạp đã nói tới (03/09/2026) vẫn là của sổ nạp, không bị lấp.
    current = dict(re.findall(
        r'data-metric="chart-bar"[^>]*data-key="([^"]+)"[^>]*'
        r'data-origin="([^"]+)"', block))
    assert current.get("2026-09-03") == rt.ORIGIN_CURRENT


@pytest.mark.chart_gapfill
def test_both_pages_draw_the_same_comparison_line_at_day_level(repository_client):
    """`FIND-R6-IR-01` — hai trang cùng sản phẩm, cùng sổ, cùng kỳ, cùng mức
    gộp KHÔNG được cho hai con số.

    Đây là bài kiểm mà `DEC-216` suýt làm đỏ: nối nguồn lấp lỗ hổng vào trang
    Báo cáo mà quên trang Phân tích sẽ cho hai đường "Cùng kỳ năm trước" khác
    nhau, và người đọc không có cách nào biết trang nào đang nói thật.
    """
    def comparison(html: str, dom_id: str) -> dict[str, str]:
        return dict(re.findall(
            r'data-metric="chart-bar-prev"[^>]*data-key="([^"]+)"[^>]*'
            r'data-revenue="([^"]+)"', chart_block(html, dom_id)))

    report = comparison(body(repository_client, "/kinh-doanh?muc=ngay"),
                        "bieu-do-doanh-thu")
    analysis = comparison(
        body(repository_client, "/kinh-doanh/phan-tich?muc=ngay"),
        "bieu-do-doanh-thu-r6")
    assert report, "oracle rỗng thì bài kiểm này không khẳng định được gì"
    assert analysis == report


@pytest.fixture
def repository_client(engine, client):
    persist(history_store.SnapshotRepository(engine),
            [line("BH1", "43F6000", day=3)])
    return client
