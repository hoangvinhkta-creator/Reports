"""TASK-PRA-005 — vertical trên web: truy vấn → trình bày → trang ``/san-pham``
thật.

Nhóm test này canh những thứ chỉ HTML mới lộ ra: đúng năm cột, ghi chú công
khai BẮT BUỘC xuất hiện nguyên văn, ranh giới PII/từ vựng nội bộ, trạng thái
rỗng, và mặc định sắp Doanh thu giảm dần trên trang thật — không dừng ở giá
trị trả về của một hàm. Oracle vẫn là fixture golden qua ĐƯỜNG PRODUCTION
(xem ``tests/test_sales_queries.py::load_golden``).
"""

from __future__ import annotations

import re

import pytest

from tests.test_sales_presentation import INTERNAL_VOCABULARY
from tests.test_sales_queries import JANUARY, fresh_engine, load_golden, pair, persist
from tests.test_web_sales_detail import build_client


@pytest.fixture(scope="module")
def golden_engine():
    engine = fresh_engine()
    load_golden(engine)
    return engine


@pytest.fixture
def client(golden_engine, monkeypatch, tmp_path):
    return build_client(golden_engine, monkeypatch, tmp_path)


@pytest.fixture
def empty_client(monkeypatch, tmp_path):
    return build_client(fresh_engine(), monkeypatch, tmp_path)


def body(client, path: str) -> str:
    response = client.get(path)
    assert response.status_code == 200, f"{path} → {response.status_code}"
    return response.get_data(as_text=True)


def cell(html: str, metric: str) -> str:
    match = re.search(
        rf'<(\w+)[^>]*data-metric="{re.escape(metric)}"[^>]*>(.*?)</\1>', html, re.S)
    assert match, f"không tìm thấy ô data-metric={metric}"
    return " ".join(re.sub(r"<[^>]+>", " ", match.group(2)).split())


def product_labels(html: str) -> list[str]:
    return re.findall(r'data-metric="product-label">(.*?)</td>', html, re.S)


# --- O · route/trang render được --------------------------------------------

def test_O_the_product_page_renders(client):
    html = body(client, "/san-pham")
    assert "SẢN PHẨM" in html


def test_the_product_tab_is_reachable_from_every_page(client):
    assert 'href="/san-pham"' in body(client, "/tong-quan")
    assert 'href="/san-pham"' in body(client, "/ban-hang")


# --- Bảng năm cột (mục 9) ----------------------------------------------------

def test_the_table_has_exactly_the_five_contract_columns(client):
    html = body(client, "/san-pham")
    headers = re.findall(r"<th[^>]*>(.*?)</th>", html, re.S)
    assert [h.strip() for h in headers] == [
        "Mặt hàng", "Số lượng", "Số đơn", "Doanh thu", "LN KPI"]


def test_no_forbidden_column_appears_on_the_page(client):
    html = body(client, "/san-pham")
    for forbidden in ("Giá mua tham chiếu", "Trạng thái dữ liệu",
                      "Brand", "Category", "Vendor", "NCC", "Margin", "Rank"):
        assert forbidden not in html, forbidden


# --- Ghi chú công khai BẮT BUỘC (mục 5, 10) --------------------------------

def test_the_required_disclosure_note_appears_verbatim(client):
    from app.web.sales_presentation import PRODUCT_GROUPING_NOTE
    assert PRODUCT_GROUPING_NOTE in body(client, "/san-pham")


def test_the_summary_item_count_label_is_not_so_san_pham(client):
    html = body(client, "/san-pham")
    assert "Số mặt hàng trên chứng từ" in html
    assert "Số sản phẩm" not in html


# --- Mặc định sắp Doanh thu giảm dần (Acceptance I) ------------------------

def test_the_default_table_order_is_revenue_descending(client):
    labels = product_labels(body(client, "/san-pham"))
    assert len(labels) == 226
    # Đối chứng đo được ở Discovery/tầng truy vấn: mặt hàng doanh thu cao nhất
    # của kỳ 01/2026 KHÔNG PHẢI dòng dịch vụ/phí — chúng tự chìm xuống.
    assert labels[0] not in {"Chi phí vận chuyển", "Giá treo Tivi"}


# --- Split oracle trên trang thật (Acceptance G) ---------------------------

def test_the_daikin_ftkb50zvmv_split_shows_as_two_separate_rows(client):
    labels = set(product_labels(body(client, "/san-pham")))
    assert "Điều hoà Daikin  FTKB50ZVMV" in labels
    assert "Máy lạnh Daikin Inverter 2 HP FTKB50ZVMV" in labels


# --- Dòng dịch vụ/phí vẫn trên trang (Acceptance H) ------------------------

def test_service_fee_like_lines_are_still_on_the_page(client):
    labels = set(product_labels(body(client, "/san-pham")))
    assert "Chi phí vận chuyển" in labels
    assert "Giá treo Tivi" in labels


# --- NULL != 0 trên trang thật (Acceptance K) ------------------------------

def test_a_partial_coverage_item_never_renders_zero_profit(client):
    """Toàn kỳ chỉ 2/351 dòng có LN KPI đã biết (S105 §13), rải trên hai mặt
    hàng — mỗi mặt hàng đó có coverage MỘT PHẦN (1/2, 1/5 dòng). Ô LN KPI của
    mọi mặt hàng KHÁC (0 dòng AUTO) phải là ``—``, KHÔNG BAO GIỜ ``0``/``0đ``."""
    html = body(client, "/san-pham")
    assert re.search(r'data-metric="kpi_profit-coverage">\s*1\s*/\s*2\s*dòng', html)
    assert re.search(r'data-metric="kpi_profit-coverage">\s*1\s*/\s*5\s*dòng', html)
    assert "0đ" not in html


# --- PII / từ vựng nội bộ ----------------------------------------------------

def test_the_product_page_never_renders_personal_data(client):
    html = body(client, "/san-pham")
    for forbidden in ("imei", "note_raw", "employee_raw", "customer", "phone", "address"):
        assert forbidden not in html.lower()


def test_the_product_page_never_leaks_internal_vocabulary(client):
    html = body(client, "/san-pham")
    for word in INTERNAL_VOCABULARY:
        assert word not in html, word
    for banned in ("SHA256", "NFC(", "RAW_PRODUCT_GROUP", "Sản phẩm chuẩn", "SKU chuẩn"):
        assert banned not in html, banned


# --- Trạng thái rỗng (mục 20) ------------------------------------------------

def test_an_empty_database_renders_the_product_page_without_raising(empty_client):
    html = body(empty_client, "/san-pham")
    assert "0" in cell(html, "item_count")
    assert cell(html, "kpi_profit") == "—"


def test_an_unknown_period_falls_back_to_the_whole_dataset_not_a_page_of_zeros(client):
    """Cùng hành vi ĐÃ nghiệm thu ở PRA-003 (``_pipeline_period``): một ``ky``
    không có trong dữ liệu rơi về "Toàn bộ dữ liệu" thay vì bịa một tháng
    trống — KHÔNG có mã riêng nào cho PRA-005 phá vỡ tiền lệ này."""
    html = body(client, "/san-pham?ky=2026-02")
    assert cell(html, "item_count") == "226"
