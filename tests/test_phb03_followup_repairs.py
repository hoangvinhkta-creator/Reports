"""S120 — bằng chứng cho bản sửa hậu-production của PHB-03 (+ R1/R2/R3).

Bốn nhóm khẳng định, mỗi nhóm đóng đúng một quan sát của chủ dự án trên
production:

    A. BẢNG KÊ CHI TIẾT là KHUNG NHÌN BÁO CÁO, không phải hàng đợi việc tồn.
       Mặc định phải là TẤT CẢ dòng; bộ lọc chỉ thu hẹp DANH SÁCH và không
       bao giờ đụng tới tổng/KPI.
    B. `DEC-PHB02-07` — "So tháng trước" luôn chỉ so DOANH THU BÁN HÀNG của
       CÙNG một engine, và KHÔNG BAO GIỜ chạm vào số cũ (Legacy Reference).
    C. `R1` — cảnh báo NOT_SEEN trên trang Kinh doanh.
    D. `R2`/`R3` — bối cảnh lần Owner sửa, và bộ lọc "dòng tôi đã sửa".

Ba trong bốn nhóm chạy qua HTTP thật vì hiện tượng chủ dự án báo là hiện
tượng TRÊN MÀN HÌNH: một khẳng định ở tầng hàm sẽ không bắt được việc một
đường dẫn mở ra đúng bộ lọc nào.
"""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine

import tools.db as history_db
from app.legacy.models import LegacyWorkbook, MonthlyReference
from app.web import (
    business_presentation, business_service, business_store, history_store,
)
from app.web import server as web_server
from tests.test_business_vertical import JANUARY, pair, persist
from tests.test_snapshot_repository import source_line, write
from tools.tracking import live_pull

FEBRUARY = {"date_from": date(2026, 2, 1), "date_to": date(2026, 2, 28)}


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
def app(monkeypatch, tmp_path, engine, repository):
    legacy = history_store.build(engine=engine)
    monkeypatch.setattr(web_server, "UPLOAD_DIR", tmp_path / "uploads")
    monkeypatch.setattr(web_server, "ARTIFACT_DIR", (tmp_path / "outputs").resolve())
    monkeypatch.setattr(web_server, "select_latest_valid_captures", lambda: None)
    monkeypatch.setattr(live_pull, "is_configured", lambda env=None: False)
    application = web_server.create_app(db_path=tmp_path / "runs.db", history=legacy,
                                        snapshots=repository)
    application.testing = True
    return application


@pytest.fixture
def client(app):
    return app.test_client()


def body(client, path: str) -> str:
    response = client.get(path)
    assert response.status_code == 200, f"{path} → {response.status_code}"
    return response.get_data(as_text=True)


def metric(html: str, name: str) -> str:
    match = re.search(rf'data-metric="{re.escape(name)}"[^>]*>(.*?)<', html, re.S)
    assert match is not None, f"không tìm thấy data-metric={name}"
    return match.group(1).strip()


def order_keys(html: str) -> list[str]:
    """Mã đơn của các dòng ĐANG hiện trên bảng kê, theo đúng thứ tự.

    Mỗi dòng có hai form (giá nhập và nhân viên) nên mã đơn xuất hiện hai lần;
    khử trùng lặp GIỮ thứ tự để khẳng định nói về DÒNG chứ không về form.
    """
    found = re.findall(r'<input type="hidden" name="order_key" value="([^"]+)"', html)
    return list(dict.fromkeys(found))


def product_key_of(html: str, order_key: str) -> str:
    """`product_key` của một dòng cụ thể — nó là hash, không đoán được."""
    match = re.search(
        rf'name="order_key" value="{re.escape(order_key)}">\s*'
        r'<input type="hidden" name="product_key" value="([0-9a-f]+)"', html)
    assert match is not None, f"không tìm thấy dòng {order_key} trên trang"
    return match.group(1)


# =========================================================================
# A. Bảng kê chi tiết = khung nhìn báo cáo
# =========================================================================

MIXED_LINES = (
    # Dòng ĐÃ ĐỦ THÔNG TIN: pipeline có giá nhập, có lợi nhuận.
    ("BH-DU", dict(kpi_purchase="5000000", kpi_profit="3000000")),
    # Dòng CÒN THIẾU: chưa có giá nhập.
    ("BH-THIEU", dict(product="Tivi Sony", kpi_purchase=None, kpi_profit=None)),
)


@pytest.fixture
def mixed(repository):
    persist(repository, [pair(order, **kwargs) for order, kwargs in MIXED_LINES])
    return repository


def test_the_detail_table_defaults_to_every_line_not_only_the_pending_ones(
    mixed, client
):
    """Hiện tượng chủ dự án báo: mở bảng kê ra chỉ thấy dòng CÒN THIẾU.

    Nguyên nhân là bộ lọc MẶC ĐỊNH `thieu-gia`. Một khung nhìn báo cáo không
    được âm thầm giấu bớt dòng, nên mặc định nay là TẤT CẢ.
    """
    html = body(client, "/kinh-doanh/gia-nhap?ky=2026-01")
    assert order_keys(html) == ["BH-DU", "BH-THIEU"]


def test_the_pending_only_view_still_exists_when_the_owner_asks_for_it(
    mixed, client
):
    """Bộ lọc cũ KHÔNG bị bỏ — nó chỉ thôi làm mặc định."""
    html = body(client, "/kinh-doanh/gia-nhap?ky=2026-01&loc=thieu-gia")
    assert order_keys(html) == ["BH-THIEU"]


def test_a_narrowed_list_says_out_loud_that_it_is_narrowed(mixed, client):
    """Một tập con được phép hiện — miễn là trang NÓI RA rằng nó là tập con."""
    assert "Đang hiện MỘT PHẦN" in metric(
        body(client, "/kinh-doanh/gia-nhap?ky=2026-01&loc=thieu-gia"), "filter-note")
    assert "TOÀN BỘ" in metric(
        body(client, "/kinh-doanh/gia-nhap?ky=2026-01"), "filter-note")


@pytest.mark.parametrize("mode", ["tat-ca", "thieu-gia", "chua-ro-nv", "owner-sua"])
def test_no_filter_changes_the_totals_or_the_coverage(mixed, client, mode):
    """`R-E5` — bộ lọc là một khung nhìn của DANH SÁCH, không phải của phép tính.

    Coverage `1 / 2 dòng` phải giống hệt nhau ở mọi chế độ, kể cả chế độ mà
    danh sách bên dưới rỗng: con số của kỳ không phụ thuộc vào việc màn hình
    đang hiện bao nhiêu dòng.
    """
    html = body(client, f"/kinh-doanh/gia-nhap?ky=2026-01&loc={mode}")
    assert metric(html, "coverage") == "1 / 2 dòng"
    assert metric(html, "coverage-percent") == "50%"


def test_the_employee_page_totals_count_every_line_not_only_the_pending_ones(
    repository, client
):
    """`H` của chỉ thị: nếu TỔNG cũng bỏ sót dòng đã hoàn thiện thì báo cáo
    nhân viên SAI. Khẳng định này canh đúng chỗ đó."""
    persist(repository, [
        pair("BH1", employee="Vinh", kpi_purchase="5000000", kpi_profit="3000000"),
        pair("BH2", employee="Vinh", product="Tivi Sony",
             kpi_purchase=None, kpi_profit=None),
    ])
    html = body(client, "/kinh-doanh/nhan-vien?ky=2026-01&nhan-vien=Vinh")
    assert metric(html, "lines") == "2", "cả dòng đã đủ lẫn dòng còn thiếu"
    assert metric(html, "sales_revenue") == "16.000.000"
    assert metric(html, "coverage") == "1 / 2 dòng"


def test_the_employee_page_opens_the_complete_list_of_that_employee(
    repository, client
):
    """Đường vào bảng kê ĐẦY ĐỦ của đúng người + đúng kỳ, luôn có mặt."""
    persist(repository, [
        pair("BH1", employee="Vinh", kpi_purchase="5000000", kpi_profit="3000000"),
        pair("BH2", employee="Ly", group="STANDARD_SALES", product="Tivi Sony",
             kpi_purchase="5000000", kpi_profit="3000000"),
    ])
    page = body(client, "/kinh-doanh/nhan-vien?ky=2026-01&nhan-vien=Vinh")
    link = re.search(r'data-metric="employee-detail-link"\s+href="([^"]+)"', page)
    assert link is not None, "trang nhân viên phải có đường vào bảng kê đầy đủ"
    href = link.group(1).replace("&amp;", "&")
    assert "loc=tat-ca" in href

    listing = body(client, href)
    # Cô lập nhân viên vẫn nguyên: chỉ dòng của Vinh, không có dòng của Ly.
    assert order_keys(listing) == ["BH1"]


def test_employee_isolation_holds_in_every_filter_mode(repository, client):
    persist(repository, [
        pair("BH1", employee="Vinh", kpi_purchase=None, kpi_profit=None),
        pair("BH2", employee="Ly", group="STANDARD_SALES", product="Tivi Sony",
             kpi_purchase=None, kpi_profit=None),
    ])
    for mode in ("tat-ca", "thieu-gia"):
        listing = body(
            client, f"/kinh-doanh/gia-nhap?ky=2026-01&nhan-vien=Vinh&loc={mode}")
        assert order_keys(listing) == ["BH1"], mode


# =========================================================================
# B. DEC-PHB02-07 — MoM cùng engine, không bao giờ chạm số cũ
# =========================================================================

def two_months(repository, *, january_sell: str, february_sell: str):
    persist(repository, [pair("BH1", month=1, day=5, sell=january_sell,
                              kpi_purchase="1000000", kpi_profit="1000000")])
    persist(repository, [pair("BH2", month=2, day=5, sell=february_sell,
                              kpi_purchase="1000000", kpi_profit="1000000")],
            run_id="run-2", at="2026-03-01T00:00:00", fingerprint="fp-b")


def mom_of(service, current: dict, previous: dict, *, period) -> dict:
    return business_presentation.month_over_month(
        service.period(**current).totals.sales_revenue,
        service.period(**previous).totals.sales_revenue,
        has_period=period is not None,
        previous_has_lines=service.period(**previous).totals.lines > 0,
    )


def test_month_over_month_rises_between_two_consecutive_engine_months(
    repository, service
):
    two_months(repository, january_sell="10000000", february_sell="15000000")
    result = mom_of(service, FEBRUARY, JANUARY, period=(2026, 2))
    assert result["percent"] == "+50%"
    assert result["missing"] is False


def test_month_over_month_falls_between_two_consecutive_engine_months(
    repository, service
):
    two_months(repository, january_sell="10000000", february_sell="4000000")
    assert mom_of(service, FEBRUARY, JANUARY, period=(2026, 2))["percent"] == "-60%"


def test_a_previous_month_of_zero_revenue_is_words_never_a_percentage(service):
    """Mẫu số 0 xử lý TƯỜNG MINH — `DEC-PHB02-07` cấm bịa vô cực."""
    result = business_presentation.month_over_month(
        Decimal("5000000"), Decimal(0), has_period=True, previous_has_lines=True)
    assert result["percent"] == "—"
    assert result["note"] == business_presentation.MOM_PREVIOUS_ZERO


def test_a_missing_previous_month_is_words_never_minus_one_hundred_percent(
    repository, service
):
    """Tháng liền trước KHÔNG có dòng nào ≠ doanh thu giảm 100 %."""
    persist(repository, [pair("BH1", month=2, day=5, kpi_purchase="1000000",
                              kpi_profit="1000000")])
    result = mom_of(service, FEBRUARY, JANUARY, period=(2026, 2))
    assert result["percent"] == "—"
    assert result["note"] == business_presentation.MOM_NO_PREVIOUS


def test_viewing_all_data_says_there_is_no_previous_month_to_compare(service):
    result = business_presentation.month_over_month(
        Decimal("5000000"), None, has_period=False, previous_has_lines=False)
    assert result["percent"] == "—"
    assert result["note"] == business_presentation.MOM_ALL_DATA


def test_the_summary_page_renders_the_month_over_month_block(repository, client):
    """Chỉ tiêu được TÍNH mà không được HIỆN thì với chủ dự án là không tồn tại."""
    two_months(repository, january_sell="10000000", february_sell="15000000")
    html = body(client, "/kinh-doanh?ky=2026-02")
    assert "So với Tháng 01/2026" in html
    assert metric(html, "mom") == "+50%"


def test_the_employee_page_renders_the_month_over_month_block(repository, client):
    persist(repository, [pair("BH1", month=1, day=5, sell="10000000",
                              kpi_purchase="1000000", kpi_profit="1000000")])
    persist(repository, [pair("BH2", month=2, day=5, sell="15000000",
                              kpi_purchase="1000000", kpi_profit="1000000")],
            run_id="run-2", at="2026-03-01T00:00:00", fingerprint="fp-b")
    html = body(client, "/kinh-doanh/nhan-vien?ky=2026-02&nhan-vien=Vinh")
    assert "So với Tháng 01/2026" in html
    assert metric(html, "mom") == "+50%"


def test_the_presentation_function_itself_never_goes_looking_for_a_number(
    engine, repository, service
):
    """`S120` viết khẳng định này khi chưa chỉ tiêu nào so được liên-origin.

    `DEC-180` đã đổi câu trả lời NGHIỆP VỤ: chủ dự án chứng minh `Tổng bán`
    cũ và `Doanh thu bán hàng` mới là cùng một chỉ tiêu, nên đúng ca chuyển
    giao tháng nay CÓ một mốc so hợp lệ (xem
    `tests/test_dec180_discount_parity.py`).

    Điều KHÔNG đổi, và là điều khẳng định này canh, là RANH GIỚI KIẾN TRÚC:
    `month_over_month()` nhận một con số đã sẵn sàng và không bao giờ tự đi
    tìm số ở nguồn khác. Việc phân giải nguồn nằm ở tầng ráp (`server.py`),
    nơi nó đi qua `authoritative_period_sales()`, chuẩn hoá đơn vị, và gắn
    nhãn origin. Gọi thẳng hàm trình bày mà không truyền mốc ⟹ vẫn là "chưa
    có dữ liệu tháng trước", dù history store đang giữ đầy đủ số cũ.
    """
    legacy = history_store.build(engine=engine)
    legacy.create_import(LegacyWorkbook(
        source_file_name="Báo cáo Kinh doanh 2026.xlsx",
        file_fingerprint="fp-legacy", file_size=1,
        sheets_imported=[{"sheet_name": "DataChart", "scope": "MONTHLY_REFERENCE"}],
        summary_rows=[],
        daily_sales=[],
        monthly_reference=[MonthlyReference(
            year=2026, month=1, sales_current_year_vnd=Decimal("999000000"))],
    ))
    assert legacy.query_monthly_reference(2026), "số cũ của tháng 01/2026 CÓ mặt"

    persist(repository, [pair("BH1", month=2, day=5, kpi_purchase="1000000",
                              kpi_profit="1000000")])
    previous = service.period(**JANUARY)
    assert previous.totals.lines == 0
    assert previous.totals.sales_revenue is None
    result = mom_of(service, FEBRUARY, JANUARY, period=(2026, 2))
    assert result["note"] == business_presentation.MOM_NO_PREVIOUS
    assert result["percent"] == "—", "hàm trình bày không tự đi tìm số"
    assert result["origin"] == "", "và không tự gắn một nhãn nguồn nào"


def test_the_cross_origin_gate_is_not_wired_into_the_business_pages():
    """Bằng chứng CẤU TRÚC: cổng so sánh legacy↔current không được nhập vào
    tầng nghiệp vụ, nên nó không thể chặn nhầm MoM cùng-engine.

    `DEC-180` KHÔNG nới lỏng ranh giới này. Số cũ nay có thể làm mốc so cho
    tháng liền trước, nhưng việc phân giải nguồn xảy ra ở tầng ráp và đi
    xuống ba module này dưới dạng một `dict` THUẦN — chúng vẫn không biết số
    cũ là gì, và vẫn không thể tự đi tìm nó.
    """
    import inspect

    from app.web import business_presentation as bp
    from app.web import business_queries as bq
    from app.web import business_service as bs

    for module in (bp, bq, bs):
        source = inspect.getsource(module)
        assert "legacy_reference" not in source, module.__name__
        assert "CROSS_ORIGIN" not in source, module.__name__


# =========================================================================
# C. R1 — cảnh báo NOT_SEEN
# =========================================================================

def test_no_warning_when_the_latest_book_saw_every_line(repository, client):
    persist(repository, [pair("BH1", kpi_purchase="5000000", kpi_profit="3000000")])
    absence = repository.latest_snapshot_absence()
    assert absence["not_seen"] == 0
    assert 'data-metric="not-seen-warning"' not in body(client, "/kinh-doanh?ky=2026-01")


def test_no_warning_before_any_book_has_been_loaded(repository, client):
    assert repository.latest_snapshot_absence() is None
    assert 'data-metric="not-seen-warning"' not in body(client, "/kinh-doanh")


def test_a_line_the_latest_book_did_not_see_raises_a_warning(repository, client):
    """Sổ mới thiếu một dòng đang được tính ⟹ chủ dự án phải được báo TRƯỚC
    khi tin vào tổng. Dòng đó VẪN được tính — cảnh báo không sửa số nào."""
    both = [source_line("BH1", row=6), source_line("BH2", row=7)]
    write(repository, both, run_id="run-1", created_at="2026-02-01T00:00:00")
    write(repository, [both[0]], run_id="run-2", fingerprint="fp-b",
          created_at="2026-02-02T00:00:00")

    absence = repository.latest_snapshot_absence()
    assert absence["not_seen"] == 1

    html = body(client, "/kinh-doanh?ky=2026-01")
    assert metric(html, "not-seen-lines") == "1"
    assert business_presentation.NOT_SEEN_WARNING in html
    # Và cả hai dòng vẫn nằm trong tổng của kỳ.
    assert metric(html, "lines") == "2"


def test_the_warning_is_only_a_warning_and_never_a_reconciliation(repository):
    """`OD_C` — không fuzzy-merge, không tự đối soát. Cảnh báo đọc, không ghi."""
    both = [source_line("BH1", row=6), source_line("BH2", row=7)]
    write(repository, both, run_id="run-1", created_at="2026-02-01T00:00:00")
    write(repository, [both[0]], run_id="run-2", fingerprint="fp-b",
          created_at="2026-02-02T00:00:00")
    before = repository.current_totals()
    repository.latest_snapshot_absence()
    assert repository.current_totals() == before


# =========================================================================
# D. R2 — bối cảnh lần sửa · R3 — bộ lọc "dòng tôi đã sửa"
# =========================================================================

def test_an_overridden_row_shows_the_auto_price_it_replaced_and_when(
    repository, client
):
    """`R2` — hai câu chủ dự án cần trả lời được: "trước khi tôi sửa, máy để
    giá bao nhiêu?" và "tôi sửa lúc nào?". Cả hai đã nằm sẵn trong bảng
    override từ ngày đầu — bản sửa này chỉ hiện chúng ra."""
    persist(repository, [pair("BH1", kpi_purchase="5000000", kpi_profit="3000000")])
    html = body(client, "/kinh-doanh/gia-nhap?ky=2026-01")
    product_key = product_key_of(html, "BH1")
    assert client.post("/kinh-doanh/gia-nhap", data={
        "order_key": "BH1", "product_key": product_key, "occurrence_index": "1",
        "ky": "2026-01", "loc": "tat-ca", "gia_nhap": "4.000.000",
    }).status_code == 302

    after = body(client, "/kinh-doanh/gia-nhap?ky=2026-01")
    assert metric(after, "provenance").startswith("Owner đã sửa")
    assert metric(after, "auto-price-at-entry") == "5.000.000"
    assert metric(after, "entered-at") != ""


def test_an_auto_row_is_not_dressed_up_as_an_owner_edit(repository, client):
    """Dòng chưa ai đụng vào KHÔNG được mang bối cảnh "Owner đã sửa"."""
    persist(repository, [pair("BH1", kpi_purchase="5000000", kpi_profit="3000000")])
    html = body(client, "/kinh-doanh/gia-nhap?ky=2026-01")
    assert metric(html, "provenance").startswith("Tự động")
    assert 'data-metric="override-context"' not in html


def test_a_manual_price_with_no_auto_price_shows_only_the_time(repository, client):
    """`MANUAL` (không có giá tự động nào để thay) ⟹ không bịa một "giá trước"."""
    persist(repository, [pair("BH1", kpi_purchase=None, kpi_profit=None)])
    html = body(client, "/kinh-doanh/gia-nhap?ky=2026-01")
    product_key = product_key_of(html, "BH1")
    client.post("/kinh-doanh/gia-nhap", data={
        "order_key": "BH1", "product_key": product_key, "occurrence_index": "1",
        "ky": "2026-01", "loc": "tat-ca", "gia_nhap": "6.000.000"})

    after = body(client, "/kinh-doanh/gia-nhap?ky=2026-01")
    assert metric(after, "provenance").startswith("Owner đã nhập")
    assert 'data-metric="auto-price-at-entry"' not in after
    assert metric(after, "entered-at") != ""


def test_the_owner_edited_filter_returns_exactly_the_lines_the_owner_touched(
    repository, client
):
    """`R3` — một KHUNG NHÌN trên provenance đã có, không phải trạng thái mới."""
    persist(repository, [
        pair("BH-AUTO", kpi_purchase="5000000", kpi_profit="3000000"),
        pair("BH-SUA", product="Tivi Sony", kpi_purchase="5000000",
             kpi_profit="3000000"),
    ])
    html = body(client, "/kinh-doanh/gia-nhap?ky=2026-01")
    assert order_keys(body(client, "/kinh-doanh/gia-nhap?ky=2026-01&loc=owner-sua")) == []

    client.post("/kinh-doanh/gia-nhap", data={
        "order_key": "BH-SUA", "product_key": product_key_of(html, "BH-SUA"),
        "occurrence_index": "1", "ky": "2026-01", "loc": "tat-ca",
        "gia_nhap": "4.000.000"})

    assert order_keys(
        body(client, "/kinh-doanh/gia-nhap?ky=2026-01&loc=owner-sua")) == ["BH-SUA"]


def test_a_line_whose_employee_the_owner_reassigned_counts_as_owner_edited(
    repository, client
):
    """Gán lại nhân viên cũng là một quyết định của chủ dự án (`OD-5`)."""
    persist(repository, [pair("BH1", employee="", group=None,
                              kpi_purchase="5000000", kpi_profit="3000000")])
    html = body(client, "/kinh-doanh/gia-nhap?ky=2026-01")
    client.post("/kinh-doanh/nhan-vien-dong", data={
        "order_key": "BH1", "product_key": product_key_of(html, "BH1"),
        "occurrence_index": "1", "ky": "2026-01", "nhan_vien_moi": "Vinh"})

    assert order_keys(
        body(client, "/kinh-doanh/gia-nhap?ky=2026-01&loc=owner-sua")) == ["BH1"]


def test_the_owner_edited_filter_does_not_mutate_anything(repository, client, store):
    """Bộ lọc là một câu HỎI. Nó không được để lại dấu vết nào."""
    persist(repository, [pair("BH1", kpi_purchase="5000000", kpi_profit="3000000")])
    before = store.purchase_price_overrides(), store.employee_overrides()
    body(client, "/kinh-doanh/gia-nhap?ky=2026-01&loc=owner-sua")
    assert (store.purchase_price_overrides(), store.employee_overrides()) == before


def test_an_unknown_filter_falls_back_to_the_complete_list(mixed, client):
    """Tham số gõ sai không được âm thầm giấu dòng — nó rơi về TẤT CẢ."""
    html = body(client, "/kinh-doanh/gia-nhap?ky=2026-01&loc=khong-co-that")
    assert order_keys(html) == ["BH-DU", "BH-THIEU"]


# =========================================================================
# E. Điều hướng — "Lịch sử" phải có mặt trên thanh tab (PHB-04)
# =========================================================================

def test_every_page_offers_the_lich_su_tab(repository, client):
    """Chủ dự án không thấy tab `Lịch sử` trên production. Đường dẫn có trong
    mã nguồn từ PHB-04; khẳng định này canh để nó không lặng lẽ biến mất."""
    persist(repository, [pair("BH1", kpi_purchase="5000000", kpi_profit="3000000")])
    for path in ("/kinh-doanh?ky=2026-01", "/tong-quan?ky=2026-01", "/lich-su"):
        html = body(client, path)
        assert '>Lịch sử</a>' in html, path
        assert 'href="/lich-su"' in html, path


def test_the_lich_su_route_answers_even_before_any_legacy_year_is_loaded(client):
    assert client.get("/lich-su").status_code == 200
