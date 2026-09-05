"""TASK-PRA-004 — vertical trên web: truy vấn → trình bày → trang thật.

Nhóm test này khẳng định trên HTML THẬT — thứ Owner nhìn thấy — chứ không
dừng ở giá trị trả về của một hàm. Nó canh ba thứ mà chỉ HTML mới lộ ra:
ranh giới PII, từ vựng nội bộ, và một ô lợi nhuận render mà rơi mất coverage.

Oracle vẫn là oracle golden đi qua ĐƯỜNG PRODUCTION (xem
``tests/test_sales_queries.py::load_golden``) — không có fixture "giống
production" nào ở đây.
"""

from __future__ import annotations

import re
import time
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from app.web import analytics_queries as aq
from app.web import history_store
from app.web import sales_presentation as sp
from app.web import sales_queries as sq
from app.web import server as web_server
from tests.test_sales_presentation import INTERNAL_VOCABULARY
from tests.test_sales_queries import JANUARY, fresh_engine, load_golden, pair, persist
from tools.tracking import live_pull

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def golden_engine():
    engine = fresh_engine()
    load_golden(engine)
    return engine


def build_client(engine, monkeypatch, tmp_path):
    monkeypatch.setattr(web_server, "UPLOAD_DIR", tmp_path / "uploads")
    monkeypatch.setattr(web_server, "ARTIFACT_DIR", (tmp_path / "outputs").resolve())
    monkeypatch.setattr(web_server, "select_latest_valid_captures", lambda: None)
    monkeypatch.setattr(live_pull, "is_configured", lambda env=None: False)
    application = web_server.create_app(
        db_path=tmp_path / "runs.db", history=history_store.build(engine=engine),
        snapshots=history_store.SnapshotRepository(engine))
    application.testing = True
    return application.test_client()


@pytest.fixture
def client(golden_engine, monkeypatch, tmp_path):
    return build_client(golden_engine, monkeypatch, tmp_path)


def body(client, path: str) -> str:
    response = client.get(path)
    assert response.status_code == 200, f"{path} → {response.status_code}"
    return response.get_data(as_text=True)


def cell(html: str, metric: str) -> str:
    """Nội dung ĐÚNG ô mang ``data-metric`` — không quét cả trang.

    "Ô lợi nhuận không được hiện 0" là khẳng định về MỘT Ô: một trang chứa
    chữ "0" trong coverage ``0 / 4 dòng`` vẫn hoàn toàn đúng.
    """
    match = re.search(
        rf'<(\w+)[^>]*data-metric="{re.escape(metric)}"[^>]*>(.*?)</\1>', html, re.S)
    assert match, f"không tìm thấy ô data-metric={metric}"
    return " ".join(re.sub(r"<[^>]+>", " ", match.group(2)).split())


def order_row(html: str, order_key: str) -> str:
    match = re.search(rf'<tr data-order="{order_key}".*?</tr>', html, re.S)
    assert match, f"không tìm thấy dòng của đơn {order_key}"
    return match.group(0)


def line_rows(html: str) -> list[str]:
    return re.findall(r'<tr data-line="\d+".*?</tr>', html, re.S)


def reason_blocks(html: str) -> list[list[str]]:
    return [re.findall(r"<li>(.*?)</li>", block)
            for block in re.findall(r'<tr class="reason-row">.*?</tr>', html, re.S)]


# --- Danh sách đơn -------------------------------------------------------

def test_the_sales_page_lists_every_order_of_the_golden_period(client):
    html = body(client, "/ban-hang?ky=tat-ca")
    assert cell(html, "orders") == "254"
    assert len(re.findall(r'<tr data-order="', html)) == 254


def test_the_mixed_order_is_shown_as_review_on_the_list(client):
    """Oracle C trên HTML: đơn có 1 dòng AUTO vẫn hiện CẦN KIỂM TRA."""
    row = order_row(body(client, "/ban-hang?ky=tat-ca"), "BH62439")
    assert cell(row, "status") == sp.STATUS_REVIEW
    assert cell(row, "lines") == "4"
    assert cell(row, "quantity") == "5"
    assert cell(row, "total_sales") == "66.000.000"


def test_the_pure_auto_order_is_shown_as_auto_on_the_list(client):
    row = order_row(body(client, "/ban-hang?ky=tat-ca"), "BH62063")
    assert cell(row, "status") == sp.STATUS_AUTO
    assert cell(row, "total_sales") == "7.500.000"


def test_every_profit_cell_on_the_list_carries_its_coverage(client):
    """INV-7 duyệt bằng DOM trên TOÀN BỘ 254 đơn, không phải bằng mắt trên vài
    dòng: một ô lợi nhuận không mẫu số ở đơn thứ 200 vẫn là cùng một lỗi."""
    html = body(client, "/ban-hang?ky=tat-ca")
    rows = re.findall(r'<tr data-order="[^"]+".*?</tr>', html, re.S)
    assert len(rows) == 254
    for row in rows:
        assert re.fullmatch(r"\d+ / \d+ dòng", cell(row, "kpi_profit-coverage"))
        assert re.fullmatch(r"—|[\d.]+", cell(row, "kpi_profit"))


def test_the_list_hides_accounting_profit_by_default(client):
    """OWNER_PRESENTATION_DECISION — "LN kế toán" không còn management-facing
    trên danh sách đơn; LN KPI vẫn hiện."""
    html = body(client, "/ban-hang?ky=tat-ca")
    assert "LN kế toán" not in html
    assert 'data-metric="accounting_profit"' not in html
    assert "LN KPI" in html


def test_the_mixed_order_shows_partial_coverage_on_the_list(client):
    """Không có đường nào hiện "lợi nhuận 500.000" mà giấu đi mẫu số 1/4."""
    row = order_row(body(client, "/ban-hang?ky=tat-ca"), "BH62439")
    assert cell(row, "kpi_profit") == "400.000"
    assert cell(row, "kpi_profit-coverage") == "1 / 4 dòng"


# --- Chi tiết đơn --------------------------------------------------------

def test_the_detail_page_of_the_mixed_order_reads_as_the_oracle(client):
    html = body(client, "/ban-hang/BH62439?ky=tat-ca")
    assert cell(html, "order-key") == "BH62439"
    assert cell(html, "status") == sp.STATUS_REVIEW
    assert cell(html, "sale-date") == "08/01/2026"
    assert cell(html, "lines") == "4"
    assert cell(html, "quantity") == "5"
    assert cell(html, "total_sales") == "66.000.000"
    assert cell(html, "kpi_profit") == "400.000"
    assert cell(html, "kpi_profit-coverage") == "1 / 4 dòng"


def test_the_detail_page_hides_accounting_profit_and_purchase_price_by_default(client):
    """OWNER_PRESENTATION_DECISION — "Lợi nhuận kế toán" và "Giá vốn (kế
    toán)" không còn management-facing ở khối tổng hợp lẫn bảng dòng hàng."""
    html = body(client, "/ban-hang/BH62439?ky=tat-ca")
    assert "Lợi nhuận kế toán" not in html
    assert "Giá vốn (kế toán)" not in html
    assert 'data-metric="accounting_profit"' not in html
    assert 'data-metric="accounting_purchase_price"' not in html
    assert "Giá mua tham chiếu" in html


def test_the_detail_page_warns_that_the_profit_is_only_part_of_the_order(client):
    """Owner nhìn "500.000" cạnh "66.000.000" sẽ tin đó là lãi của cả đơn nếu
    trang không nói thẳng ra. Cảnh báo này là chính nó."""
    html = body(client, "/ban-hang/BH62439?ky=tat-ca")
    assert "KHÔNG phải" in cell(html, "partial-coverage")


def test_the_pure_auto_order_raises_no_partial_coverage_warning(client):
    html = body(client, "/ban-hang/BH62063?ky=tat-ca")
    assert 'data-metric="partial-coverage"' not in html
    assert cell(html, "kpi_profit-coverage") == "1 / 1 dòng"


def test_the_four_lines_appear_in_the_order_they_had_in_the_book(client):
    rows = line_rows(body(client, "/ban-hang/BH62439?ky=tat-ca"))
    assert [cell(row, "product") for row in rows] == [
        "Tủ lạnh Panasonic NR-BX471GPKV",
        "Máy Giặt Sấy LG FV1414H3BA",
        "Điều hòa Daikin FTHF25XVMV",
        "Máy lạnh Daikin Inverter 2 HP FTKB50ZVMV",
    ]


def test_the_auto_line_shows_the_reference_purchase_price_and_kpi_profit(client):
    """"Giá vốn (KPI)" đổi tên "Giá mua tham chiếu" — giá trị KHÔNG đổi."""
    row = line_rows(body(client, "/ban-hang/BH62439?ky=tat-ca"))[2]
    assert cell(row, "status") == sp.STATUS_AUTO
    assert cell(row, "quantity") == "2"
    assert cell(row, "sell_price") == "10.500.000"
    assert cell(row, "discount") == "100.000"
    assert cell(row, "total_sales") == "20.900.000"
    assert cell(row, "kpi_purchase_price") == "10.250.000"
    assert cell(row, "kpi_profit") == "400.000"


def test_the_pending_lines_show_a_dash_and_never_a_zero(client):
    """INV-6 trên HTML: bốn ô tiền của mỗi dòng PENDING là ``—``, và không ô
    nào trong số đó chứa ``0``/``0đ``/``0%``."""
    rows = line_rows(body(client, "/ban-hang/BH62439?ky=tat-ca"))
    pending = [row for row in rows if cell(row, "status") == sp.STATUS_REVIEW]
    assert len(pending) == 3
    for row in pending:
        for metric in ("kpi_purchase_price", "kpi_profit"):
            value = cell(row, metric)
            assert value == "—"
            assert "0" not in value and "%" not in value


def test_each_pending_line_explains_itself_in_readable_vietnamese(client):
    """Câu hỏi 5 của mục 1: "tại sao dòng này cần kiểm tra?"."""
    blocks = reason_blocks(body(client, "/ban-hang/BH62439?ky=tat-ca"))
    assert len(blocks) == 3
    # DEC-PAN-001 — "Thiếu giá nhập kế toán"/"Thiếu lợi nhuận kế toán" KHÔNG
    # còn xuất hiện trên kết quả MỚI: chúng nhân bản đúng một nguyên nhân gốc
    # đã có mã actionable riêng ("Thiếu giá mua tham chiếu"). Nhãn của chúng
    # vẫn tồn tại để đọc lại lịch sử đã persist, không phải để sinh mới.
    expected = ["Chưa có dữ liệu để nhận diện sản phẩm", "Thiếu giá mua tham chiếu",
                "Thiếu lợi nhuận KPI"]
    assert blocks == [expected] * 3


def test_an_auto_line_carries_no_reason_block(client):
    html = body(client, "/ban-hang/BH62063?ky=tat-ca")
    assert reason_blocks(html) == []
    assert len(line_rows(html)) == 1


def test_the_detail_totals_add_back_up_from_its_own_lines(client):
    """INV-1 + INV-2 khẳng định trên chính HTML mà Owner đọc."""
    html = body(client, "/ban-hang/BH62439?ky=tat-ca")
    rows = line_rows(html)
    assert _sum(rows, "total_sales") == _number(cell(html, "total_sales"))
    assert _sum(rows, "quantity") == _number(cell(html, "quantity"))


def _number(text: str) -> Decimal:
    return Decimal(text.replace(".", ""))


def _sum(rows: list[str], metric: str) -> Decimal:
    return sum(_number(cell(row, metric)) for row in rows)


# --- Reconcile với Tổng quan (CHECK-PRA004-07) ---------------------------

@pytest.mark.parametrize("bounds", [{}, JANUARY])
def test_the_sales_layer_reconciles_with_the_overview_on_the_same_period(
        golden_engine, bounds):
    """Cùng dữ liệu, cùng kỳ ⟹ CÙNG con số. Đây là điều kiện để Owner tin cả
    hai trang: một tổng "40 đơn" ở Tổng quan phải mở ra đúng 40 đơn ở đây."""
    orders = sq.order_list(golden_engine, **bounds)
    totals = aq.period_totals(golden_engine, **bounds)

    assert len(orders) == totals["orders"]
    assert sum(order["lines"] for order in orders) == totals["lines"]
    assert sum(order["quantity"] for order in orders) == totals["quantity"]
    assert sum(order["total_sales"] for order in orders) == totals["total_sales"]
    assert sum(1 for order in orders if order["review"]) == totals["review_orders"]
    assert sum(1 for order in orders if not order["review"]) == totals["auto_orders"]
    assert sum(order["kpi_lines"] for order in orders) == totals["kpi_lines"]
    assert sum(order["accounting_lines"] for order in orders) == \
        totals["accounting_lines"]
    assert _total(orders, "kpi_profit") == totals["kpi_profit"]
    assert _total(orders, "accounting_profit") == totals["accounting_profit"]


def _total(orders: list[dict], metric: str):
    values = [order[metric] for order in orders if order[metric] is not None]
    return sum(values) if values else None


def test_the_two_pages_agree_on_how_many_orders_the_period_has(client):
    """Reconcile ở tầng HTML, không chỉ ở tầng hàm."""
    assert cell(body(client, "/ban-hang?ky=tat-ca"), "orders") == \
        cell(body(client, "/tong-quan?ky=tat-ca"), "orders")


# --- PII và từ vựng nội bộ (CHECK-PRA004-09/10) --------------------------

PROHIBITED = ("imei", "note_raw", "employee_raw", "source_profit", "customer",
              "phone", "address", "shipper")


@pytest.mark.parametrize("path", ["/ban-hang?ky=tat-ca", "/ban-hang/BH62439?ky=tat-ca",
                                  "/ban-hang/BH62063?ky=tat-ca"])
def test_no_new_page_ever_renders_a_personal_data_field(client, path):
    html = body(client, path).lower()
    for word in PROHIBITED:
        assert word not in html, word


@pytest.mark.parametrize("path", ["/ban-hang?ky=tat-ca", "/ban-hang/BH62439?ky=tat-ca"])
def test_no_new_page_leaks_internal_vocabulary(client, path):
    html = body(client, path).lower()
    for word in INTERNAL_VOCABULARY:
        assert word.lower() not in html, word
    assert str(REPO_ROOT).lower() not in html, "đường dẫn tuyệt đối của repo"


def test_the_customer_columns_do_not_even_exist_in_the_schema():
    """Bảo đảm CẤU TRÚC, mạnh hơn một quy ước: các trường này KHÔNG BAO GIỜ
    được persist, nên chúng không thể rò rỉ qua bất kỳ truy vấn nào."""
    text = (REPO_ROOT / "tools/db/schema.py").read_text(encoding="utf-8")
    for column in ("customer", "phone", "address", "shipper"):
        assert not re.search(rf'Column\("{column}', text), column


def test_the_detail_page_does_show_the_product_name(client):
    """Phía còn lại của mục 14.4: ``product_raw`` là REQUIRED_NOW."""
    assert "Điều hòa Daikin FTHF25XVMV" in body(client, "/ban-hang/BH62439?ky=tat-ca")


# --- Biên route ----------------------------------------------------------

def test_an_unknown_order_key_is_a_404_not_an_empty_page(client):
    """404 ≠ "đơn này không có dòng nào" — hai điều đó khác nhau."""
    assert client.get("/ban-hang/BH-KHONG-TON-TAI").status_code == 404


def test_an_invalid_period_falls_back_to_all_data_instead_of_failing(client):
    """Một ``ky`` gõ sai KHÔNG được thành HTTP 500, cũng không được thành một
    bảng rỗng cho một tháng bịa — GIỐNG HỆT quy tắc dự phòng của PRA-003."""
    assert cell(body(client, "/ban-hang?ky=khong-hop-le"), "orders") == "254"


def test_without_a_data_store_the_pages_answer_503_not_no_data_yet(monkeypatch,
                                                                  tmp_path):
    """Lỗi/thiếu kho dữ liệu KHÔNG BAO GIỜ được hiện thành "chưa có dữ liệu"."""
    monkeypatch.setattr(web_server, "UPLOAD_DIR", tmp_path / "uploads")
    monkeypatch.setattr(web_server, "ARTIFACT_DIR", (tmp_path / "outputs").resolve())
    monkeypatch.setattr(web_server, "select_latest_valid_captures", lambda: None)
    monkeypatch.setattr(live_pull, "is_configured", lambda env=None: False)
    application = web_server.create_app(db_path=tmp_path / "runs.db", history=None,
                                        snapshots=None)
    application.testing = True
    client = application.test_client()
    assert client.get("/ban-hang").status_code == 503
    assert client.get("/ban-hang/BH62439").status_code == 503


def test_the_sales_detail_page_still_links_back_to_the_list(client):
    """Điều hướng Option A vẫn đúng GIỮA danh sách và chi tiết của cùng một
    trang Bán hàng. R1 (`GỠ TRÙNG UX`) chỉ bỏ đường chéo `/tong-quan` →
    `/ban-hang` khỏi nav dùng chung (trùng lặp điều hướng phải bỏ) — route
    `/tong-quan` vẫn còn nguyên và render đúng khi vào trực tiếp (§4C)."""
    assert "TỔNG QUAN" in body(client, "/tong-quan")
    assert 'href="/ban-hang?ky=tat-ca"' in body(client, "/ban-hang/BH62439?ky=tat-ca")


def test_the_detail_link_carries_the_period_so_both_pages_stay_in_step(client):
    row = order_row(body(client, "/ban-hang?ky=2026-01"), "BH62439")
    assert 'href="/ban-hang/BH62439?ky=2026-01"' in row


def test_an_empty_period_says_so_instead_of_showing_a_blank_table(monkeypatch,
                                                                 tmp_path):
    client = build_client(fresh_engine(), monkeypatch, tmp_path)
    assert sp.NO_ORDERS_NOTE in body(client, "/ban-hang")


def test_the_pages_are_reachable_without_touching_any_write_path(client):
    """Ranh giới CHỈ-ĐỌC ở mức HTTP: hai route mới chỉ nhận ``GET``."""
    for path in ("/ban-hang", "/ban-hang/BH62439"):
        for method in ("post", "put", "delete"):
            assert getattr(client, method)(path).status_code == 405


def test_a_multi_employee_order_names_every_employee_on_the_page(monkeypatch,
                                                                tmp_path):
    """Mục 9 trên HTML. Fixture golden đã ẩn danh về MỘT nhân viên, nên nhánh
    này chỉ dựng được bằng dữ liệu tổng hợp (FIND-PRA004-03)."""
    engine = fresh_engine()
    persist(engine, [pair("BH1", product="Tủ lạnh", row=6, employee="VuHanhLy"),
                     pair("BH1", product="Máy giặt", row=7, employee="TranMinh")])
    client = build_client(engine, monkeypatch, tmp_path)

    html = body(client, "/ban-hang/BH1")
    assert cell(html, "employees") == "TranMinh · VuHanhLy"
    assert sp.MULTI_EMPLOYEE_NOTE in cell(html, "multi-employee")


def test_an_order_spanning_two_days_shows_a_range_not_one_chosen_day(monkeypatch,
                                                                    tmp_path):
    engine = fresh_engine()
    persist(engine, [pair("BH1", product="Tủ lạnh", row=6, day=5),
                     pair("BH1", product="Máy giặt", row=7, day=9)])
    client = build_client(engine, monkeypatch, tmp_path)
    assert cell(body(client, "/ban-hang/BH1"), "sale-date") == \
        "05/01/2026 – 09/01/2026"


# --- CHECK-PRA004-13 · thời gian tải trên tập lớn ------------------------

def test_the_order_list_stays_usable_on_a_large_period(monkeypatch, tmp_path):
    """RE-TRIGGER CONDITION tường minh: > 3 giây ⟹ pagination trở thành
    REQUIRED và phải mở như một quyết định RIÊNG. Test này CHỈ ĐO — nó không
    tự thêm pagination, và không tự thêm chỉ mục nào."""
    engine = fresh_engine()
    pairs = [pair(f"BH{index // 3:05d}", product=f"SP{index % 3}",
                  row=6 + index, day=1 + index % 28)
             for index in range(12_000)]
    persist(engine, pairs)

    started = time.perf_counter()
    orders = sq.order_list(engine)
    elapsed = time.perf_counter() - started

    assert sum(order["lines"] for order in orders) == 12_000
    assert elapsed < 3.0, f"danh sách đơn mất {elapsed:.2f}s trên 12.000 dòng"
    print(f"\nCHECK-PRA004-13 · {len(orders)} đơn / 12.000 dòng · "
          f"order_list = {elapsed * 1000:.1f} ms")
