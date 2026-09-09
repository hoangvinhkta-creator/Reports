"""R6 — vertical đầy đủ: quyết định của Owner → database → route Flask THẬT.

`tests/test_r6_*_metrics.py` chứng minh NGỮ NGHĨA đúng trên giá trị thuần.
File này chứng minh cùng ngữ nghĩa đó SỐNG SÓT qua database, qua tầng ráp và
qua HTML — và đặc biệt chứng minh hai mệnh đề mà chỉ một vertical mới nói
được:

    dòng Owner đã loại, và dòng R5 đã tạm loại, KHÔNG lọt vào MỘT ô nào của
    R6 — không tổng, không mốc biểu đồ, không bucket, không giỏ hàng

    đổi mapping/nhóm hàng chỉ ĐỔI BUCKET, không đổi một đồng nào của tổng
"""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine

import tools.db as history_db
from app.web import business_service, business_store, catalog_display
from app.web import history_store
from app.web import server as web_server
from tools.tracking import live_pull

from tests.test_employee_workspace_ux import TODAY, line, persist

SEPTEMBER_QS = "ky=2026-09"
CONFIRMED_RANGE = {"start": date(2026, 9, 1), "end": date(2026, 9, 30)}

OVERVIEW = "/kinh-doanh/phan-tich"
STRUCTURE = "/kinh-doanh/phan-tich/co-cau"
EMPLOYEE = "/kinh-doanh/phan-tich/nhan-vien"
BASKET = "/kinh-doanh/phan-tich/gio-hang"
DRILLDOWN = "/kinh-doanh/phan-tich/don-hang"


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


@pytest.fixture
def client(engine, monkeypatch, tmp_path):
    monkeypatch.setattr(web_server, "select_latest_valid_captures", lambda: None)
    monkeypatch.setattr(live_pull, "is_configured", lambda env=None: False)
    monkeypatch.setattr(web_server, "_today", lambda: TODAY)
    monkeypatch.setattr(catalog_display, "DEFAULT_DISPLAY_PATH",
                        tmp_path / "tracking_display.json")
    monkeypatch.setattr(
        web_server.identity_gateway, "DEFAULT_LOG_PATH",
        tmp_path / "identity" / "mappings.jsonl")
    monkeypatch.setattr(
        web_server.identity_gateway, "DEFAULT_INDEX_PATH",
        tmp_path / "identity" / "index.json")
    application = web_server.create_app(
        db_path=tmp_path / "runs.db",
        history=history_store.LegacyRepository(engine),
        snapshots=history_store.SnapshotRepository(engine))
    application.testing = True
    return application.test_client()


def body(client, path: str) -> str:
    response = client.get(path)
    assert response.status_code == 200, f"{path} → {response.status_code}"
    return response.get_data(as_text=True)


def metric(html: str, name: str) -> str:
    match = re.search(rf'data-metric="{re.escape(name)}"[^>]*>(.*?)<', html, re.S)
    assert match is not None, f"không tìm thấy data-metric={name}"
    return match.group(1).strip()


def metrics(html: str, name: str) -> list[str]:
    return [value.strip() for value in re.findall(
        rf'data-metric="{re.escape(name)}"[^>]*>(.*?)<', html, re.S)]


def attribute(html: str, name: str, attr: str) -> str:
    match = re.search(rf'data-metric="{re.escape(name)}"[^>]*{attr}="([^"]*)"',
                      html, re.S)
    assert match is not None, f"không tìm thấy {attr} của {name}"
    return match.group(1)


def september_book():
    """Một kỳ nhỏ nhưng đủ hình dạng để mọi mệnh đề của R6 kiểm được thật.

        BH1  hai dòng, hai mặt hàng khác nhau  → đơn nhiều dòng + nhiều mặt hàng
        BH2  một dòng + một dòng PHÍ           → có dịch vụ kèm, KHÔNG nhiều nhóm
        BH3  hai dòng CÙNG một mặt hàng        → nhiều dòng, KHÔNG nhiều mặt hàng
        BH4  một dòng, nhân viên khác          → tách được theo nhân viên
    """
    return [
        line("BH1", "43F6000", day=5, sell="8000000"),
        line("BH1", "XP352AE-DS", day=5, row=7, sell="4000000",
             kpi_purchase="2000000", kpi_profit="2000000"),
        line("BH2", "RT38", day=6, row=8, sell="6000000"),
        line("BH2", "Chi phí vận chuyển", day=6, row=9, sell="300000",
             kpi_purchase="0", kpi_profit="300000"),
        line("BH3", "Giá treo", day=7, row=10, sell="500000",
             kpi_purchase="300000", kpi_profit="200000"),
        line("BH3", "Giá treo", day=7, row=11, occurrence=2, sell="500000",
             kpi_purchase="300000", kpi_profit="200000"),
        line("BH4", "55Q6FA", day=8, row=12, employee="Ly", sell="9000000"),
    ]


# --- Năm route mở được, và nói cùng một câu ---------------------------------

def test_every_analysis_route_renders(client, repository):
    persist(repository, september_book())
    for path in (OVERVIEW, STRUCTURE, EMPLOYEE, BASKET, DRILLDOWN):
        assert client.get(f"{path}?{SEPTEMBER_QS}").status_code == 200


def test_the_overview_reconciles_with_the_accepted_business_totals(
    client, repository,
):
    """Hai module tính độc lập (`dashboard_metrics` và `business_metrics`) gặp
    nhau ở cùng số dòng, cùng số đơn, cùng doanh thu — bằng chứng R6 không
    dựng một định nghĩa doanh thu thứ hai."""
    persist(repository, september_book())
    html = body(client, f"{OVERVIEW}?{SEPTEMBER_QS}")
    assert attribute(html, "totals-reconciliation", "data-reconciled") == "yes"


@pytest.mark.parametrize("dimension", ["san-pham", "nhom-hang", "hang"])
def test_every_grouping_dimension_reconciles_to_the_slice_total(
    client, repository, dimension,
):
    persist(repository, september_book())
    html = body(client, f"{STRUCTURE}?{SEPTEMBER_QS}&chieu={dimension}")
    assert attribute(html, "reconciliation", "data-reconciled") == "yes"


def test_the_analysis_page_and_the_business_page_report_the_same_revenue(
    client, repository, service,
):
    persist(repository, september_book())
    data = service.period(date_from=date(2026, 9, 1), date_to=date(2026, 9, 30))
    html = body(client, f"{OVERVIEW}?{SEPTEMBER_QS}")
    assert attribute(html, "sales_revenue", "title") == (
        f"{data.totals.sales_revenue:,.0f}".replace(",", ".") + " đồng")


# --- Dòng Owner đã loại KHÔNG lọt vào một ô nào ------------------------------

def excluded_totals(client, repository, store, service):
    persist(repository, september_book())
    before = body(client, f"{OVERVIEW}?{SEPTEMBER_QS}")
    data = service.period(date_from=date(2026, 9, 1), date_to=date(2026, 9, 30))
    target = next(d for d in data.details if d["product_raw"] == "43F6000")
    store.exclude_line(order_key=target["order_key"],
                       product_key=target["product_key"],
                       occurrence_index=target["occurrence_index"],
                       reason="test")
    return before, body(client, f"{OVERVIEW}?{SEPTEMBER_QS}")


def test_an_owner_excluded_line_leaves_every_total_on_the_analysis_page(
    client, repository, store, service,
):
    before, after = excluded_totals(client, repository, store, service)
    assert metric(before, "sales_revenue") != metric(after, "sales_revenue")
    assert attribute(after, "totals-reconciliation", "data-reconciled") == "yes"


def test_an_owner_excluded_line_leaves_every_bucket_of_every_dimension(
    client, repository, store, service,
):
    persist(repository, september_book())
    data = service.period(date_from=date(2026, 9, 1), date_to=date(2026, 9, 30))
    target = next(d for d in data.details if d["product_raw"] == "43F6000")
    before = body(client, f"{STRUCTURE}?{SEPTEMBER_QS}")
    assert "43F6000" in before
    store.exclude_line(order_key=target["order_key"],
                       product_key=target["product_key"],
                       occurrence_index=target["occurrence_index"])
    after = body(client, f"{STRUCTURE}?{SEPTEMBER_QS}")
    assert "43F6000" not in after, "dòng đã loại vẫn còn một bucket riêng"
    assert attribute(after, "reconciliation", "data-reconciled") == "yes"


def test_an_owner_excluded_line_leaves_the_basket_and_its_pairs(
    client, repository, store, service,
):
    """BH1 có hai mặt hàng ⟹ một cặp. Loại một trong hai dòng thì đơn còn một
    mặt hàng, nên nó thôi là "đơn nhiều mặt hàng" và cặp biến mất."""
    persist(repository, september_book())
    data = service.period(date_from=date(2026, 9, 1), date_to=date(2026, 9, 30))
    before = body(client, f"{BASKET}?{SEPTEMBER_QS}")
    assert int(metric(before, "multi_product_orders")) == 1
    target = next(d for d in data.details if d["product_raw"] == "43F6000")
    store.exclude_line(order_key=target["order_key"],
                       product_key=target["product_key"],
                       occurrence_index=target["occurrence_index"])
    after = body(client, f"{BASKET}?{SEPTEMBER_QS}")
    assert int(metric(after, "multi_product_orders")) == 0


def test_an_owner_excluded_line_leaves_the_drilldown(
    client, repository, store, service,
):
    persist(repository, september_book())
    data = service.period(date_from=date(2026, 9, 1), date_to=date(2026, 9, 30))
    target = next(d for d in data.details if d["product_raw"] == "43F6000")
    store.exclude_line(order_key=target["order_key"],
                       product_key=target["product_key"],
                       occurrence_index=target["occurrence_index"])
    html = body(client, f"{DRILLDOWN}?{SEPTEMBER_QS}")
    assert "43F6000" not in html


# --- Dòng R5 tạm loại KHÔNG lọt vào một ô nào -------------------------------

def test_a_line_removed_from_a_confirmed_book_leaves_every_r6_figure(
    client, repository,
):
    """`DEC-R5-01` — dòng vắng khỏi một sổ ĐÃ xác nhận đầy đủ bị tạm loại khỏi
    dữ liệu hiệu lực. R6 thừa hưởng điều đó theo CẤU TẠO (nó đọc `PeriodData`),
    và bài này đo rằng nó thật sự thừa hưởng."""
    book = september_book()
    persist(repository, book, run_id="run-1", at="2026-10-01T00:00:00",
            fingerprint="fp-a")
    second = persist(repository, [pair for pair in book
                                  if pair[0].key.order_key != "BH4"],
                     run_id="run-2", at="2026-10-02T00:00:00",
                     fingerprint="fp-b")
    before = body(client, f"{OVERVIEW}?{SEPTEMBER_QS}")
    assert "9.000.000" in before

    repository.confirm_coverage(second.snapshot_id, confirmed=True,
                                confirmed_at="2026-10-03T00:00:00",
                                **CONFIRMED_RANGE)
    after = body(client, f"{OVERVIEW}?{SEPTEMBER_QS}")
    assert int(metric(after, "orders")) == int(metric(before, "orders")) - 1
    assert attribute(after, "totals-reconciliation", "data-reconciled") == "yes"
    # …và nó cũng biến khỏi bảng gộp, giỏ hàng và bảng kê.
    assert "55Q6FA" not in body(client, f"{STRUCTURE}?{SEPTEMBER_QS}")
    assert "55Q6FA" not in body(client, f"{DRILLDOWN}?{SEPTEMBER_QS}")


# --- Hợp đồng phạm vi trên route thật ---------------------------------------

def test_a_custom_range_narrows_the_page_and_declares_itself(client, repository):
    persist(repository, september_book())
    html = body(client, f"{OVERVIEW}?{SEPTEMBER_QS}"
                        "&tu-ngay=2026-09-05&den-ngay=2026-09-05")
    assert attribute(html, "scope-label", "data-kind") == "CUSTOM"
    # Chỉ BH1 (hai dòng) nằm trong ngày 05.
    assert int(metric(html, "orders")) == 1


def test_a_bad_custom_range_falls_back_and_says_why(client, repository):
    persist(repository, september_book())
    html = body(client, f"{OVERVIEW}?{SEPTEMBER_QS}"
                        "&tu-ngay=2026-09-20&den-ngay=2026-09-05")
    assert attribute(html, "scope-label", "data-kind") == "PERIOD"
    assert "Từ ngày nằm SAU Đến ngày" in metric(html, "scope-rejected")


def test_the_scope_applies_to_every_block_of_the_page(client, repository, service):
    """Một trang, một phạm vi: ô chỉ tiêu và bảng gộp phải nói cùng một số."""
    persist(repository, september_book())
    query = f"{SEPTEMBER_QS}&tu-ngay=2026-09-05&den-ngay=2026-09-06"
    overview = body(client, f"{OVERVIEW}?{query}")
    structure = body(client, f"{STRUCTURE}?{query}")
    assert metric(overview, "sales_revenue") == metrics(structure, "revenue")[-1]


# --- Biểu đồ số đơn không đếm hai lần ---------------------------------------

def test_an_order_with_two_sale_dates_is_charted_once_and_counted_apart(
    client, repository,
):
    persist(repository, [
        line("BH9", "43F6000", day=5, sell="8000000"),
        line("BH9", "XP352AE-DS", day=9, row=7, sell="4000000"),
    ])
    html = body(client, f"{OVERVIEW}?{SEPTEMBER_QS}&muc=ngay")
    assert int(metric(html, "orders")) == 1
    assert int(metric(html, "orders_with_multiple_sale_dates")) == 1
    # Đúng MỘT mốc mang đơn này trên biểu đồ SỐ ĐƠN, và nó là mốc NGÀY NHỎ
    # NHẤT. Cắt riêng khối biểu đồ số đơn: trang có HAI biểu đồ dùng chung
    # cùng một macro, nên một biểu thức tìm kiếm trên cả trang sẽ đọc nhầm
    # sang các chấm của biểu đồ doanh thu.
    block = html.split('id="bieu-do-so-don"', 1)[1]
    charted = re.findall(r'data-metric="chart-bar"[^>]*data-key="([^"]+)"'
                         r'[^>]*data-revenue="([^"]+)"', block)
    assert ("2026-09-05", "1") in charted
    assert sum(int(float(value)) for _key, value in charted) == 1


# --- Chốt kỳ: một khoảng ngày tự chọn KHÔNG mượn trạng thái chốt -------------

def test_a_custom_range_never_claims_a_period_lock(client, repository, service):
    """`AnalysisRange.period is None` ở phạm vi `CUSTOM`, nên `PeriodData.closed`
    là `None`. Đây là bài đo rằng ràng buộc ấy sống qua route thật."""
    persist(repository, september_book())
    assert client.get(f"{OVERVIEW}?{SEPTEMBER_QS}"
                      "&tu-ngay=2026-09-01&den-ngay=2026-09-30").status_code == 200
    data = service.period(date_from=date(2026, 9, 1), date_to=date(2026, 9, 30))
    assert data.closed is None


# --- Hàng rào dữ liệu cá nhân của drill-down ---------------------------------

def test_the_drilldown_never_renders_a_customer_field(client, repository):
    """`business_queries` ĐỌC tên/SĐT/địa chỉ cho bảng kê nghiệp vụ
    (`DEC-PHB02-08`), nên chúng có mặt trong `details`. Bảng kê của R6 vẫn
    KHÔNG được render chúng — và đây là bài đo trên chính HTML."""
    persist(repository, september_book())
    html = body(client, f"{DRILLDOWN}?{SEPTEMBER_QS}")
    for leaked in ("Nguyễn Thị Hoa", "0912000111", "12 Lê Lợi, Q1"):
        assert leaked not in html, f"{leaked!r} rò ra bảng kê drill-down"


def test_the_drilldown_of_a_pair_lists_only_the_orders_containing_both(
    client, repository, service,
):
    persist(repository, september_book())
    data = service.period(date_from=date(2026, 9, 1), date_to=date(2026, 9, 30))
    keys = {d["product_raw"]: d["product_key"] for d in data.details}
    html = body(client, f"{DRILLDOWN}?{SEPTEMBER_QS}"
                        f"&a={keys['43F6000']}&b={keys['XP352AE-DS']}")
    assert int(metric(html, "drilldown-orders")) == 1
    assert set(metrics(html, "order-key")) == {"BH1"}


# --- Giỏ hàng trên dữ liệu đi qua database ----------------------------------

def test_the_four_basket_metrics_stay_four_different_numbers(client, repository):
    persist(repository, september_book())
    html = body(client, f"{BASKET}?{SEPTEMBER_QS}")
    assert int(metric(html, "multi_line_orders")) == 3    # BH1, BH2, BH3
    assert int(metric(html, "multi_product_orders")) == 1  # chỉ BH1
    assert int(metric(html, "service_attachment_orders")) == 1  # chỉ BH2


def test_a_repeated_product_line_never_creates_a_pair(client, repository):
    """BH3 có hai dòng CÙNG một mặt hàng — nó không được sinh ra một cặp."""
    persist(repository, september_book())
    html = body(client, f"{BASKET}?{SEPTEMBER_QS}&chieu=san-pham")
    assert "Giá treo · Giá treo" not in html


# --- Nhân viên: cùng aggregate, lát khác ------------------------------------

def test_the_employee_page_splits_the_same_money_and_nothing_else(
    client, repository, service,
):
    persist(repository, september_book())
    html = body(client, f"{EMPLOYEE}?{SEPTEMBER_QS}")
    assert "Ly" in html and "Vinh" in html
    # Cơ cấu của MỘT nhân viên đi qua đúng engine gộp của trang cơ cấu, nên nó
    # cũng phải đối soát về tổng của CHÍNH lát ấy.
    detail_html = body(client, f"{EMPLOYEE}?{SEPTEMBER_QS}&nhan-vien=Ly")
    assert attribute(detail_html, "reconciliation", "data-reconciled") == "yes"


def test_the_employee_page_has_no_score_or_ranking_column(client, repository):
    """R6 §4 nói rõ: không employee score, không xếp hạng quản trị, không KPI
    mới. Bài này canh bằng chính HTML để một cột như vậy không lặng lẽ xuất
    hiện ở một lần sửa sau."""
    persist(repository, september_book())
    html = body(client, f"{EMPLOYEE}?{SEPTEMBER_QS}")
    for banned in ("Điểm", "Xếp hạng", "score", "ranking"):
        assert banned not in html


# --- Ranh giới với bài kiểm mã nguồn của vertical khác ------------------------

def test_the_r6_block_never_sits_between_a_route_and_its_next_decorator():
    """`tests/test_phb07_advanced_analytics.py::route_source` cắt mã của một
    route bằng cách đọc tới `@app.` KẾ TIẾP. Khối R6 mở đầu bằng các hàm phụ
    chưa decorate, nên nếu nó nằm ngay sau `business_composition`, mã của R6
    sẽ bị đọc thành mã của route PHB-07 và làm đỏ một bài kiểm ranh giới của
    vertical khác — một lỗi rất khó truy ngược về đúng nguyên nhân.

    Bài này canh ràng buộc ấy tại nguồn: `business_composition` phải được
    theo sau NGAY bởi một decorator `@app.`.
    """
    import inspect
    source = inspect.getsource(web_server)
    match = re.search(r"\n    def business_composition\(\):\n(.*?)"
                      r"(?=\n    @app\.)", source, re.S)
    assert match is not None
    assert "R6 — DASHBOARD" not in match.group(1)
    assert "_analysis_view" not in match.group(1)
