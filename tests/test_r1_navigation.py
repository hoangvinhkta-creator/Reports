"""R1 (`GỠ TRÙNG UX`) — gỡ trùng navigation/noise, thuần trình bày+điều hướng.

Phạm vi các khẳng định dưới đây bám đúng 12 CASE của chỉ thị R1 (mục 13),
CỘNG một ghi chú tường minh cho CASE 4/5: chỉ thị yêu cầu `/tong-quan` và
`/nhan-vien` REDIRECT sang entry point mới, nhưng cả hai route đó đang mang
hợp đồng non-regression đang được test rất dày (TASK-PRA-001 cho truy cập
KHÔNG tham số của `/nhan-vien`; nhiều trang khác cross-link trực tiếp và có
test riêng cho `/tong-quan`). Redirect vô điều kiện ở đây sẽ phá vỡ những hợp
đồng đó — chỉ thị R1 §12 cũng tự giới hạn: "redirect old route to BÁO CÁO
**if safe**". Quyết định trong bản sửa này: KHÔNG redirect hai route đó —
chỉ gỡ khỏi thanh tab chính (mục tiêu thật của R1 §1: "REDUCE DUPLICATE
NAVIGATION", không phải "xoá route"). CASE 4/5 dưới đây kiểm tra đúng quyết
định đã ghi trong báo cáo cuối (SCOPE_DRIFT/OWNER_DECISIONS_REQUIRED).
"""

from __future__ import annotations

import re
from datetime import date

import pytest
from sqlalchemy import create_engine

import tools.db as history_db
from app.web import business_service, business_store, history_store
from app.web import server as web_server
from tests.test_business_vertical import JANUARY, pair, persist
from tools.tracking import live_pull


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


def nav_html(html: str) -> str:
    match = re.search(r'<nav class="ncc-tabs">(.*?)</nav>', html, re.S)
    assert match is not None, "không tìm thấy thanh tab chính"
    return match.group(1)


# ==========================================================================
# CASE 1 — `/` mở BÁO CÁO, không phải màn hình upload.
# ==========================================================================

def test_case_1_root_redirects_to_the_business_report(repository, client):
    persist(repository, [pair("BH1", kpi_purchase="5000000", kpi_profit="3000000")])
    resp = client.get("/", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/kinh-doanh?ky=2026-01", (
        "kỳ mới nhất có dữ liệu (Current Engine) phải được chọn sẵn")
    followed = client.get("/", follow_redirects=True)
    assert followed.status_code == 200
    assert "TỔNG HỢP KINH DOANH" in followed.get_data(as_text=True)
    assert "CHẠY BÁO CÁO" not in followed.get_data(as_text=True), (
        "`/` không còn là màn hình upload/chạy pipeline")


def test_case_1_root_falls_back_safely_when_no_current_period_has_data(client):
    """Chưa nạp dữ liệu Current Engine nào ⟹ về BÁO CÁO không kèm `ky`, tự
    nói tình trạng của nó — KHÔNG dò kỳ mới nhất bắc qua Legacy (R1 §3)."""
    resp = client.get("/", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["Location"] == "/kinh-doanh"


# ==========================================================================
# CASE 2 · 3 — thanh tab chính rút còn đúng 3 mục, bỏ các mục trùng.
#
# `R1` rút thanh tab từ nhiều mục xuống 4; `DEC-185` `NAV-01`/`NAV-02` rút
# tiếp xuống 3 bằng cách bỏ "Doanh số ngày". Hai test dưới đây KHÔNG bị xoá
# khi con số đổi — chúng vẫn canh đúng tính chất mà `R1` dựng ra ("thanh tab
# là một tập ĐÓNG, giống nhau trên mọi trang"), chỉ đổi tập kỳ vọng sang tập
# đã được Owner chốt. Route `/doanh-so-ngay` vẫn sống và vẫn có test riêng
# (`NAV-03`, ngay dưới).
# ==========================================================================

#: Thanh tab chính sau `DEC-185`. Viết MỘT lần ở đây để hai test không thể
#: nói hai câu khác nhau về cùng một tập.
PRIMARY_TABS = {"/kinh-doanh", "/kinh-doanh/nhan-vien", "/du-lieu"}


def test_case_2_and_3_the_primary_nav_has_exactly_the_three_new_tabs(repository, client):
    persist(repository, [pair("BH1", kpi_purchase="5000000", kpi_profit="3000000")])
    nav = nav_html(body(client, "/kinh-doanh?ky=2026-01"))

    assert nav.count('class="ncc-tab') == 3, "phải có đúng 3 tab chính"
    for kept in PRIMARY_TABS:
        assert f'href="{kept}"' in nav

    for removed in ('href="/tong-quan"', 'href="/nhan-vien"', 'href="/ban-hang"',
                    'href="/san-pham"', 'href="/lich-su"', 'href="/du-lieu/chay-bao-cao"',
                    # `NAV-02` — "Doanh số ngày" không còn là đích UX chính.
                    'href="/doanh-so-ngay"'):
        assert removed not in nav, f"{removed} không còn là tab chính"


def test_case_2_and_3_the_nav_is_identical_on_every_primary_page(repository, client):
    """Cả 3 trang đích của thanh tab đều thấy CÙNG một tập đường dẫn — không
    có trang nào còn giữ lại tab cũ đã bị các trang khác bỏ. (Class `on` của
    tab đang chọn đổi theo trang — đó là highlight, không phải khác nav.)"""
    persist(repository, [pair("BH1", kpi_purchase="5000000", kpi_profit="3000000")])
    navs = {
        path: frozenset(re.findall(r'href="([^"]+)"', nav_html(body(client, path))))
        for path in ("/kinh-doanh?ky=2026-01", "/kinh-doanh/nhan-vien?ky=2026-01",
                     "/du-lieu")
    }
    reference = navs["/du-lieu"]
    assert reference == PRIMARY_TABS
    for path, hrefs in navs.items():
        assert hrefs == reference, path


def test_nav_03_the_daily_sales_route_survives_leaving_the_tab_bar(client):
    """`NAV-03` — bỏ khỏi thanh tab KHÔNG phải xoá route.

    Đây là nửa còn lại của `NAV-02`, và nó phải là một test riêng: một bản
    sửa "bỏ tab" cẩu thả sẽ xoá luôn route, và mọi đường dẫn/bookmark cũ tới
    `/doanh-so-ngay` sẽ 404 mà không test nào đỏ.
    """
    resp = client.get("/doanh-so-ngay")
    assert resp.status_code == 200
    assert 'class="ncc-tab' in resp.get_data(as_text=True), (
        "trang vẫn dựng bằng layout chung, chỉ không còn là một tab")


# ==========================================================================
# CASE 4 · 5 — `/tong-quan` và `/nhan-vien` KHÔNG redirect (quyết định ghi ở
# trên): route vẫn còn nguyên, không 404, không vỡ hợp đồng non-regression.
# ==========================================================================

def test_case_4_tong_quan_is_dropped_from_nav_but_still_resolves(repository, client):
    persist(repository, [pair("BH1", kpi_purchase="5000000", kpi_profit="3000000")])
    resp = client.get("/tong-quan?ky=2026-01")
    assert resp.status_code == 200, (
        "redirect vô điều kiện sang BÁO CÁO không an toàn ở đây — xem docstring "
        "đầu file: nhiều trang/khẳng định khác vẫn phụ thuộc route này render")
    nav = nav_html(resp.get_data(as_text=True))
    assert 'href="/tong-quan"' not in nav


def test_case_5_the_old_top_level_employee_entry_is_dropped_from_nav_but_still_resolves(
    client,
):
    resp = client.get("/nhan-vien")
    assert resp.status_code == 200, (
        "redirect vô điều kiện sẽ phá hợp đồng non-regression TASK-PRA-001 "
        "(truy cập KHÔNG tham số phải giữ nguyên đường legacy) — xem docstring")
    nav = nav_html(resp.get_data(as_text=True))
    assert 'href="/nhan-vien"' not in nav
    assert 'href="/kinh-doanh/nhan-vien"' in nav, (
        "mục NHÂN VIÊN của thanh tab chính trỏ thẳng vào entry point mới")


# ==========================================================================
# CASE 6 — công cụ vận hành (upload/chạy báo cáo) vẫn vào được qua DỮ LIỆU.
# ==========================================================================

def test_case_6_the_upload_tool_is_still_reachable_through_du_lieu(client):
    du_lieu = body(client, "/du-lieu")
    assert 'href="/du-lieu/chay-bao-cao"' in du_lieu

    upload_page = body(client, "/du-lieu/chay-bao-cao")
    assert '<input type="file" name="workbook"' in upload_page
    assert 'action="/run"' in upload_page


# ==========================================================================
# CASE 7 — không có sai lệch số liệu tổng hợp trước/sau R1.
# ==========================================================================

def test_case_7_totals_are_identical_whether_reached_via_root_or_direct_url(
    repository, client,
):
    persist(repository, [pair("BH1", kpi_purchase="5000000", kpi_profit="3000000")])
    via_root = client.get("/", follow_redirects=True).get_data(as_text=True)
    via_direct = body(client, "/kinh-doanh?ky=2026-01")
    for name in ("kpi_profit", "converted_sales", "orders", "lines"):
        assert metric(via_root, name) == metric(via_direct, name), name


# ==========================================================================
# CASE 8 — ô trống vẫn là trống, không thành 0.
# ==========================================================================

def test_case_8_a_missing_purchase_price_stays_blank_not_zero(repository, client):
    persist(repository, [pair("BH1", product="Tivi Sony",
                              kpi_purchase=None, kpi_profit=None)])
    html = body(client, "/kinh-doanh?ky=2026-01")
    assert metric(html, "kpi_profit") == "—"
    assert metric(html, "converted_sales") == "—"


# ==========================================================================
# CASE 9 — coverage vẫn phân biệt được CHÍNH THỨC / CHƯA HOÀN CHỈNH.
# ==========================================================================

def test_case_9_the_coverage_state_tag_is_still_visible(repository, client):
    persist(repository, [
        pair("BH1", kpi_purchase="5000000", kpi_profit="3000000"),
        pair("BH2", product="Tivi Sony", kpi_purchase=None, kpi_profit=None),
    ])
    html = body(client, "/kinh-doanh?ky=2026-01")
    assert metric(html, "state") == "CHƯA HOÀN CHỈNH"
    assert "CHÍNH THỨC" not in metric(html, "coverage-note")


# ==========================================================================
# CASE 10 — huy hiệu PIPELINE/SỐ MỚI không còn lặp lại; cảnh báo bắt buộc
# vẫn còn nguyên.
# ==========================================================================

def test_case_10_the_pipeline_badge_no_longer_repeats_on_the_report_pages(
    repository, client,
):
    persist(repository, [pair("BH1", kpi_purchase="5000000", kpi_profit="3000000")])
    summary_html = body(client, "/kinh-doanh?ky=2026-01")
    assert summary_html.count('tag-pipeline') == 1, (
        "huy hiệu PIPELINE chỉ còn một lần trên trang BÁO CÁO (trước R1: hai lần)")

    employee_html = body(client, "/kinh-doanh/nhan-vien?ky=2026-01&nhan-vien=Vinh")
    assert employee_html.count('tag-pipeline') == 1, (
        "huy hiệu PIPELINE chỉ còn một lần trên trang NHÂN VIÊN (trước R1: hai lần)")


def test_case_10_required_warnings_still_render_when_triggered(repository, client):
    """Cảnh báo bắt buộc (coverage chưa đủ, dòng chưa gán nhân viên) không bị
    dọn theo huy hiệu trang trí — chỉ nhãn hệ thống lặp lại mới bị bỏ."""
    persist(repository, [
        pair("BH1", employee="Ly", group="STANDARD_SALES",
             kpi_purchase="5000000", kpi_profit="3000000"),
        pair("BH2", employee="", group=None, product="Tivi Sony",
             kpi_purchase="5000000", kpi_profit="3000000"),
    ])
    html = body(client, "/kinh-doanh?ky=2026-01")
    assert 'data-metric="coverage-note"' in html
    assert 'data-metric="attribution-note"' in html
    assert 'data-metric="unresolved-employee-lines"' in html


# ==========================================================================
# CASE 11 — tiền hiển thị NGHÌN ĐỒNG, VND đầy đủ vẫn xem được, không đổi số
# lưu trữ/tính toán.
# ==========================================================================

def test_case_11_money_renders_in_thousand_vnd_with_the_full_amount_in_a_tooltip(
    repository, client, service,
):
    persist(repository, [pair("BH1", sell="8000000", kpi_purchase="5000000",
                              kpi_profit="3000000")])
    html = body(client, "/kinh-doanh?ky=2026-01")
    assert metric(html, "sales_revenue") == "8.000", (
        "8.000.000 đồng phải hiện thành 8.000 (nghìn đồng)")
    assert 'title="8.000.000 đồng"' in html, (
        "VND đầy đủ vẫn phải xem được qua tooltip")

    # Số lưu trữ/tính toán không đổi — chỉ cách VIẾT ra màn hình đổi.
    totals = service.period(**JANUARY).totals
    assert totals.sales_revenue == 8_000_000


# ==========================================================================
# CASE 12 — không có vòng lặp redirect trên bất kỳ route nào ở mục 12.
# ==========================================================================

def test_case_12_no_route_from_section_12_redirect_loops(repository, client):
    persist(repository, [pair("BH1", kpi_purchase="5000000", kpi_profit="3000000")])
    routes = (
        "/", "/tong-quan", "/nhan-vien", "/kinh-doanh", "/kinh-doanh/nhan-vien",
        "/kinh-doanh/gia-nhap", "/ban-hang", "/doanh-so-ngay", "/du-lieu",
        "/lich-su", "/du-lieu/chay-bao-cao", "/giai-thich",
    )
    for route in routes:
        resp = client.get(route, follow_redirects=True)
        assert resp.status_code == 200, f"{route} → {resp.status_code}"
