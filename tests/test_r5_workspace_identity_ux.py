"""R5 §5 — model canonical, các cột đối chiếu, và popover phân loại.

Ba mệnh đề, và cả ba nói về cùng một điều: màn hình phải nói ĐÚNG những gì
hệ thống biết, không hơn.

    dòng ĐÃ phân loại      hiện model canonical (fallback mã Tracking)
    dòng CHƯA phân loại    giữ TÊN THÔ — đó là thứ duy nhất cho người dùng
                           biết dòng này còn phải xử lý
    hãng chưa xác định     một dấu gạch, không phải một cái tên đoán ra

Hai cột Hãng/IMEI mặc định ẩn sau MỘT nút chung, và khi mở phải HẸP: một mã
máy mười lăm chữ số xuống dòng làm cả hàng cao gấp đôi, và một bảng kê mà mỗi
hàng một chiều cao khác nhau thì không dò theo hàng được nữa — đúng thứ nền
xen kẽ theo ngày (`§38`) sinh ra để giữ.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from sqlalchemy import create_engine

import tools.db as history_db
from app.web import business_service, business_store, catalog_display
from app.web import history_store
from app.web import server as web_server

from tests.test_employee_workspace_ux import SEPTEMBER, body, line, metrics, persist
from tests.test_dec185_nav_chart_identity import (  # noqa: F401
    client, identity_store, snapshot, tracking_on, unresolved_line,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


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
def display(tmp_path, monkeypatch):
    """Bản chiếu hiển thị đặt ở thư mục tạm — không chạm `data/` của repo."""
    path = tmp_path / "tracking_display.json"
    monkeypatch.setattr(catalog_display, "DEFAULT_DISPLAY_PATH", path)
    return path


def seed_display(path, rows: dict):
    path.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")


def workspace(client) -> str:
    return body(client, "/kinh-doanh/nhan-vien?ky=2026-09&sheet=noi-thanh")


# --- 1. Bản chiếu hiển thị — đọc, ghi, và hỏng thì im lặng ---------------

def test_the_display_projection_round_trips(display):
    """R5.1 mở rộng bản chiếu thành BA trường — dòng không có gì để nói vẫn
    không chiếm chỗ."""
    catalog_display.write(_snapshot([
        ("65S20M2", "K-65S20M2", "Sony"), ("X", None, None)]))
    assert catalog_display.read() == {
        "65S20M2": {"model_label": "K-65S20M2", "brand": "Sony",
                    "category_label": None}}


def test_a_broken_projection_reads_as_empty_not_as_an_error(display):
    display.write_text("{ hỏng", encoding="utf-8")
    assert catalog_display.read() == {}


def test_a_missing_projection_reads_as_empty(display):
    assert catalog_display.read() == {}


def _snapshot(rows):
    from datetime import datetime

    from app.modules.product.identity.tracking_catalog import (
        CaptureStatus, TrackingCatalogRow, TrackingCatalogSnapshot,
    )
    return TrackingCatalogSnapshot(
        capture_id="c", captured_at=datetime(2026, 9, 8), captured_by="t",
        source_system_ref="s", content_hash="h",
        capture_status=CaptureStatus.COMPLETE,
        rows=tuple(TrackingCatalogRow(
            tracking_code=code, present_in_board=True, name=code,
            model_label=model, brand=brand) for code, model, brand in rows))


# --- 2. Tên hàng trên màn hình ------------------------------------------

def test_an_unclassified_line_keeps_its_raw_name(repository, client, display):
    persist(repository, [unresolved_line("BH1")])
    html = workspace(client)
    assert "Máy giặt Electrolux EWF1143R7SC" in html


def test_a_classified_line_shows_the_canonical_model(
    repository, client, display, tracking_on,
):
    seed_display(display, {"EWF1143R7SC": {"model_label": "EWF1143R7SC",
                                           "brand": "Electrolux"}})
    persist(repository, [unresolved_line("BH1")])
    _classify(client, _keys(client), "EWF1143R7SC")

    html = workspace(client)
    assert metrics(html, "line-brand") == ["Electrolux"]
    assert metrics(html, "line-product") == ["EWF1143R7SC"], (
        "dòng đã phân loại hiện model canonical, không còn cả câu tên hàng")


def test_an_unclassified_line_never_gets_a_brand(repository, client, display):
    seed_display(display, {"EWF1143R7SC": {"model_label": "EWF1143R7SC",
                                           "brand": "Electrolux"}})
    persist(repository, [unresolved_line("BH1")])
    html = workspace(client)
    assert "Máy giặt Electrolux EWF1143R7SC" in html, "giữ TÊN THÔ"
    assert metrics(html, "line-brand") == ["—"], (
        "chưa phân loại thì chưa có hãng — không đoán từ tên hàng")


def _keys(client):
    html = workspace(client)
    match = re.search(
        r'data-metric="identity-open"[^>]*href="[^"]*order_key=(?P<order>[^&"]+)'
        r'[^"]*product_key=(?P<product>[0-9a-f]+)[^"]*'
        r'occurrence_index=(?P<occ>\d+)', html)
    assert match is not None, "phải có lối vào phân loại"
    return match.groupdict()


def _classify(client, keys, code):
    response = client.post("/kinh-doanh/nhan-vien/phan-loai", data={
        "ky": "2026-09", "sheet": "noi-thanh", "order_key": keys["order"],
        "product_key": keys["product"], "occurrence_index": keys["occ"],
        "ma_tracking": code})
    assert response.status_code == 302


# --- 3. Hai cột ẩn/hiện chung một nút, và cắt MỘT DÒNG ------------------

def test_the_optional_columns_are_hidden_by_default_behind_one_shared_button(
    repository, client, display,
):
    """R5.1 thêm "Nhóm hàng" vào ĐÚNG nút chung đã có, không dựng nút thứ hai.

    Một cột đối chiếu thứ ba xứng đáng chung số phận với hai cột kia: hiếm
    dùng, không phải thông tin vận hành hằng ngày, và mở ra thì bắt cả bảng
    hẹp lại.
    """
    persist(repository, [line("BH1", "43F6000", day=5)])
    html = workspace(client)

    assert html.count('data-metric="toggle-optional"') == 1, "MỘT nút chung"
    assert "HIỆN NHÓM HÀNG, HÃNG &amp; IMEI" in html
    assert 'data-optional-hidden="1"' in html, (
        "ẩn ngay từ khung hình đầu — không chờ JavaScript")
    for label in ("Nhóm hàng", "Hãng", "IMEI"):
        assert f'col-optional">{label}</th>' in html


def test_the_hidden_columns_are_narrow_and_cut_to_one_line(display):
    """Cắt một dòng là một mệnh đề CSS, và nó phải đọc được từ CSS."""
    css = (REPO_ROOT / "app/web/static/css/tinphat-ui.css").read_text(
        encoding="utf-8")
    rule = re.search(r"\.sheet-table \.col-narrow \{(.*?)\}", css, re.S)
    assert rule is not None, "phải có luật cho hai cột hẹp"
    body_text = rule.group(1)
    assert "white-space: nowrap" in body_text, "tuyệt đối không xuống dòng"
    assert "text-overflow: ellipsis" in body_text
    assert "max-width" in body_text
    assert ".sheet-table[data-optional-hidden] .col-optional { display: none; }" in css


def test_the_full_value_stays_readable_through_a_tooltip(repository, client, display):
    persist(repository, [line("BH1", "43F6000", day=5)])
    html = workspace(client)
    assert re.search(r'class="col-optional col-narrow[^"]*"[^>]*title="', html)


# --- 4. Popover: một ô tìm, tối đa một gợi ý, không tự map --------------

def test_the_panel_is_a_popover_anchored_by_javascript(
    repository, client, display, tracking_on,
):
    """Server vẫn dựng khối ở đúng chỗ cũ; JS chỉ DỜI nó tới chỗ vừa bấm."""
    persist(repository, [unresolved_line("BH1")])
    keys = _keys(client)
    html = body(client,
                "/kinh-doanh/nhan-vien?ky=2026-09&sheet=noi-thanh&phan-loai=1"
                f"&order_key={keys['order']}&product_key={keys['product']}"
                f"&occurrence_index={keys['occ']}")
    assert "data-identify-pop" in html
    js = (REPO_ROOT / "app/web/static/js/app.js").read_text(encoding="utf-8")
    assert "clientX" in js and "clientY" in js, "neo theo toạ độ click"
    assert '"Escape"' in js, "Escape đóng popover"
    assert "is-anchored" in js


def test_the_popover_offers_one_search_box_and_at_most_one_suggestion(
    repository, client, display, tracking_on,
):
    persist(repository, [unresolved_line("BH1")])
    keys = _keys(client)
    base = ("/kinh-doanh/nhan-vien?ky=2026-09&sheet=noi-thanh&phan-loai=1"
            f"&order_key={keys['order']}&product_key={keys['product']}"
            f"&occurrence_index={keys['occ']}")
    html = body(client, base)
    assert html.count('data-metric="identify-search"') == 1
    assert 'data-metric="identify-select"' not in html, "không còn dropdown"
    assert html.count('data-metric="identify-confirm"') <= 1


def test_out_of_catalog_stays_a_one_click_action_in_the_same_result_line(
    repository, client, display, tracking_on,
):
    persist(repository, [unresolved_line("BH1")])
    keys = _keys(client)
    html = body(client,
                "/kinh-doanh/nhan-vien?ky=2026-09&sheet=noi-thanh&phan-loai=1"
                f"&order_key={keys['order']}&product_key={keys['product']}"
                f"&occurrence_index={keys['occ']}")
    assert 'data-metric="identify-out-of-catalog-confirm"' in html
    assert "identify-result" in html


def test_the_ranking_suggests_but_never_writes():
    """Xếp hạng là GỢI Ý. Chuỗi tìm rỗng ⟹ không gợi ý gì."""
    from app.web import identity_gateway

    snapshot = _snapshot([("EWF1143R7SC", None, None), ("EWF9999", None, None)])
    assert identity_gateway.best_candidate(snapshot, query="") is None
    assert identity_gateway.best_candidate(snapshot, query=None) is None
    exact = identity_gateway.best_candidate(snapshot, query="EWF1143R7SC")
    assert exact.code == "EWF1143R7SC", "khớp CHÍNH XÁC thắng"
    prefix = identity_gateway.best_candidate(snapshot, query="EWF9")
    assert prefix.code == "EWF9999"
