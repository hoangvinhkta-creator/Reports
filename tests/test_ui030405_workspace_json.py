"""`UI-03`/`UI-04`/`UI-05` — hợp đồng phía SERVER của ba lát dọc.

Bộ Playwright (`tests/playwright/*.spec.mjs`) chứng minh hành vi trên trình
duyệt thật. File này canh những mệnh đề mà một trình duyệt KHÔNG nhìn thấy
được và một bài browser sẽ không bao giờ đỏ vì chúng:

- phép cắt trang theo RANH GIỚI BH là một hàm thuần, kiểm được bằng danh
  sách dòng dựng tay — kể cả những ca mà fixture thật không sinh ra (một BH
  lớn hơn cả ngưỡng trang, con trỏ trỏ vào một BH đã biến mất);
- đường KHÔNG-JS của ba route ghi vẫn redirect y hệt trước `UI-03` — mệnh
  đề "lớp tăng cường không đổi hành vi cũ" chỉ đúng nếu có cái gì canh nó;
- route phân rã `UI-05` KHÔNG tự cộng: nó phải trả về ĐÚNG con số mà
  `dashboard_metrics.totals()` trả cho cùng lát dữ liệu.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from app.web import dashboard_presentation, workspace_presentation as wp
from app.modules.reporting import dashboard_metrics
from tests.fixtures import workspace_scale as ws
from tests.support import web_client


# --- Phân trang: một hàm thuần, kiểm bằng dòng dựng tay ------------------

def _details(pairs):
    """`[{order_key, sale_date}]` — đúng hai trường mà phép cắt trang đọc."""
    return [{"order_key": order, "sale_date": day} for order, day in pairs]


DAY1, DAY2 = date(2026, 9, 1), date(2026, 9, 2)


def test_a_page_stops_at_an_order_boundary_not_mid_order():
    """Ngưỡng `limit` là NGƯỠNG, không phải một con số chính xác.

    Cắt đúng 2 dòng giữa một BH ba dòng sẽ để lại nửa khối mang `rowspan`
    trỏ vào những hàng không có mặt — `§22` dựng cả cấu trúc bảng để giữ
    quan hệ "ba dòng này là một đơn", và một phép cắt theo dòng phá đúng nó.
    """
    details = _details([("BH1", DAY1), ("BH2", DAY1), ("BH2", DAY1),
                        ("BH2", DAY1), ("BH3", DAY1)])
    page = wp.page_of_groups(details, limit=2)
    assert page["order_keys"] == ["BH1", "BH2"]
    assert len(page["details"]) == 4      # VƯỢT ngưỡng, không cắt giữa BH2
    assert page["next_cursor"] == "BH3"


def test_an_order_larger_than_the_whole_page_still_travels_whole():
    details = _details([("BH1", DAY1)] * 7 + [("BH2", DAY1)])
    page = wp.page_of_groups(details, limit=3)
    assert page["order_keys"] == ["BH1"]
    assert len(page["details"]) == 7
    assert page["next_cursor"] == "BH2"


def test_the_last_page_reports_no_next_cursor():
    details = _details([("BH1", DAY1), ("BH2", DAY1)])
    page = wp.page_of_groups(details, limit=100)
    assert page["next_cursor"] is None
    assert page["total_orders"] == 2


def test_a_cursor_pointing_at_a_vanished_order_restarts_at_the_top():
    """Con trỏ là MÃ BH, và mã ấy có thể biến mất giữa hai lần tải.

    Đúng thao tác mà `UI-03` làm trên cùng màn hình này: loại nốt dòng cuối
    của một đơn. Câu trả lời đúng là dựng lại từ đầu sheet, không phải ném
    lỗi vào mặt người đang cuộn.
    """
    details = _details([("BH1", DAY1), ("BH2", DAY2)])
    page = wp.page_of_groups(details, cursor="BH-KHONG-CON", limit=1)
    assert page["order_keys"] == ["BH1"]


def test_the_page_limit_is_clamped():
    """Không có trần, `limit=999999` biến route phân trang trở lại thành
    đúng cái nó tồn tại để thay thế."""
    details = _details([(f"BH{i}", DAY1) for i in range(1, 40)])
    page = wp.page_of_groups(details, limit=10**9)
    assert len(page["order_keys"]) <= wp.WORKSPACE_PAGE_LINES_MAX


def test_shades_are_a_property_of_the_whole_sheet_not_of_a_slice():
    """Nền xen kẽ theo NGÀY: một lát dựng riêng phải giữ đúng nhịp của cả
    sheet, nếu không phần vừa tải sẽ đổi màu so với phần đang trên màn hình.
    """
    details = _details([("BH1", DAY1), ("BH2", DAY2), ("BH3", DAY2)])
    whole = wp.group_shades(details)
    assert whole == {"BH1": 0, "BH2": 1, "BH3": 1}
    # Lát chỉ gồm BH2/BH3 vẫn mang nền 1, không tự đặt lại về 0.
    part = wp.groups_slice(details, ["BH2", "BH3"])
    assert part["shades"]["BH2"] == 1
    assert part["order_keys"] == ["BH2", "BH3"]
    assert part["cursor"] is None and part["next_cursor"] is None


def test_cursor_for_order_finds_the_page_holding_an_order():
    details = _details([(f"BH{i:02d}", DAY1) for i in range(1, 10)])
    assert wp.cursor_for_order(details, "BH01", limit=3) is None
    assert wp.cursor_for_order(details, "BH05", limit=3) == "BH04"
    assert wp.cursor_for_order(details, "BH09", limit=3) == "BH07"


# --- Các route: app THẬT ------------------------------------------------

@pytest.fixture
def engine():
    return web_client.make_engine()


@pytest.fixture
def client(engine, monkeypatch, tmp_path):
    """App thật + 400 dòng — đủ để bảng kê phải phân trang thật sự.

    Thẩm quyền Product Identity trỏ vào `tmp_path`: file này GHI thật qua
    đường sản xuất, và một lần chạy test không được để lại quyết định trong
    `data/product_identity/` đã commit.
    """
    from app.web import history_store, server as web_server
    monkeypatch.setattr(web_server.identity_gateway, "DEFAULT_LOG_PATH",
                        tmp_path / "mappings.jsonl")
    monkeypatch.setattr(web_server.identity_gateway, "DEFAULT_INDEX_PATH",
                        tmp_path / "index.json")
    ws.install(history_store.SnapshotRepository(engine), 400)
    return web_client.make_client(engine, monkeypatch, tmp_path)


WORKSPACE = "/kinh-doanh/nhan-vien?ky=2026-09&sheet=noi-thanh"


def body(client, url: str) -> str:
    response = client.get(url)
    assert response.status_code == 200, url
    return response.get_data(as_text=True)


def test_the_html_page_serves_one_page_not_the_whole_sheet(client):
    html = body(client, WORKSPACE)
    rows = html.count('<tr\n')  + html.count('<tr ')
    assert 'data-metric="workspace-more"' in html
    assert 'data-total-lines="400"' in html
    # Hàng dữ liệu nằm trong ngưỡng một trang, không phải cả 400 dòng.
    assert rows < wp.WORKSPACE_PAGE_LINES + 20, rows


def test_the_no_js_more_link_really_serves_a_different_page(client):
    import re
    html = body(client, WORKSPACE)
    cursor = re.search(r'data-next-cursor="([^"]+)"', html).group(1)
    first = re.findall(r'data-order="(BH\d+)"', html)
    second_html = body(client, WORKSPACE + f"&tu={cursor}")
    second = re.findall(r'data-order="(BH\d+)"', second_html)
    assert second[0] == cursor
    assert not set(first) & set(second)     # hai trang KHÔNG chồng nhau


def test_the_json_page_route_reuses_the_same_row_markup(client):
    import re
    html = body(client, WORKSPACE)
    cursor = re.search(r'data-next-cursor="([^"]+)"', html).group(1)
    payload = client.get(
        f"/api/v1/periods/2026-09/workspace?sheet=noi-thanh&cursor={cursor}"
    ).get_json()
    assert payload["schema_version"] == wp.WORKSPACE_SCHEMA_VERSION
    assert payload["cursor"] == cursor
    assert payload["total_lines"] == 400
    # ĐÚNG những `<tr>` mà trang đầy đủ dựng: cùng khoá ba phần trên hàng.
    assert 'data-product-key=' in payload["rows_html"]
    assert 'data-occurrence-index=' in payload["rows_html"]
    assert payload["rows_html"].count('data-metric="bh-head"') == \
        len(payload["order_keys"])


def test_the_json_page_route_never_exceeds_the_hard_limit(client):
    payload = client.get(
        "/api/v1/periods/2026-09/workspace?sheet=noi-thanh&limit=100000"
    ).get_json()
    assert payload["lines"] <= wp.WORKSPACE_PAGE_LINES_MAX


# --- `UI-03`: HAI câu trả lời cho CÙNG một đường ghi ---------------------

def line_keys(client) -> dict:
    import re
    html = body(client, WORKSPACE)
    match = re.search(
        r'data-order="(BH\d+)"\s*\n\s*data-product-key="([0-9a-f]+)"\s*\n\s*'
        r'data-occurrence-index="(\d+)"', html)
    assert match, "không tìm được một hàng dữ liệu nào trên bảng kê"
    return {"ky": "2026-09", "sheet": "noi-thanh",
            "order_key": match.group(1), "product_key": match.group(2),
            "occurrence_index": match.group(3)}


def test_the_browser_path_still_redirects_exactly_as_before(client):
    """Mệnh đề "lớp tăng cường không đổi hành vi cũ", canh bằng máy."""
    keys = line_keys(client)
    response = client.post("/kinh-doanh/nhan-vien/loai-dong", data=keys)
    assert response.status_code == 302
    assert "/kinh-doanh/nhan-vien" in response.headers["Location"]
    assert "da-luu=" in response.headers["Location"]


def test_the_json_path_writes_the_same_decision_and_returns_the_rows(client):
    keys = line_keys(client)
    response = client.post("/kinh-doanh/nhan-vien/loai-dong", data=keys,
                           headers={"Accept": "application/json"})
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["schema_version"] == wp.WORKSPACE_SCHEMA_VERSION
    assert keys["order_key"] in (
        payload["affected"]["order_keys"])
    # Dòng thật sự biến khỏi báo cáo — kiểm trên TRANG, không trên payload.
    html = body(client, WORKSPACE)
    assert f'data-metric="excluded-row" data-order="{keys["order_key"]}"' in html


def test_a_classification_answers_with_EVERY_affected_order(client, engine):
    """`INV-76`/`INV-87` — một quyết định phân loại áp cho MỌI dòng dùng
    chung khoá định danh, và payload phải trả đủ chúng.

    Fixture `workspace_scale` lặp tên hàng theo chu kỳ 40, nên với 400 dòng
    mỗi tên hàng có mặt ở nhiều BH — đúng hình dạng cần kiểm.
    """
    keys = line_keys(client)
    response = client.post("/kinh-doanh/nhan-vien/ngoai-bang", data=keys,
                           headers={"Accept": "application/json"})
    assert response.status_code == 200
    payload = response.get_json()
    orders = payload["affected"]["order_keys"]
    assert len(orders) > 1, orders
    assert keys["order_key"] in orders
    # Mỗi BH bị ảnh hưởng đi kèm HTML của chính nó + hai hàng xóm để chèn.
    for order in orders:
        assert set(payload["groups"][order]) == {"html", "after", "before"}
        assert f'data-order="{order}"' in payload["groups"][order]["html"]


def test_the_write_payload_carries_the_server_built_regions(client):
    keys = line_keys(client)
    payload = client.post(
        "/kinh-doanh/nhan-vien/loai-dong", data=keys,
        headers={"Accept": "application/json"}).get_json()
    regions = payload["regions"]
    # `identity-warning` KHÔNG có mặt: `TASK-OWNER-UIUX-009` (đã merge) bỏ
    # vùng hiển thị cảnh báo này khỏi trang — gửi HTML cho một vùng không
    # còn host DOM nào là dữ liệu chết (xem `_workspace_regions`).
    assert set(regions) == {"identify", "kpi-strip", "sheet-totals", "excluded"}
    # Nhãn CHÍNH THỨC/CHƯA HOÀN CHỈNH đi LIỀN con số trong cùng một mảnh —
    # đó là lý do vùng này trả HTML chứ không trả con số trần.
    assert 'data-metric="sales_revenue"' in regions["kpi-strip"]
    assert 'data-metric="totals-purchase"' in regions["sheet-totals"]
    # Phân loại xong ⟹ bảng chọn đóng lại, nên vùng của nó rỗng.
    assert regions["identify"].strip() == ""


def test_the_identify_route_returns_only_the_picker(client):
    keys = line_keys(client)
    response = client.get(
        "/api/v1/periods/2026-09/identify?sheet=noi-thanh&phan-loai=1"
        f"&order_key={keys['order_key']}&product_key={keys['product_key']}"
        f"&occurrence_index={keys['occurrence_index']}")
    assert response.status_code == 200
    payload = response.get_json()
    # `workspace_scale` dựng dòng PENDING vì THIẾU GIÁ
    # (`TRACKING_DAILY_MIN_MISSING`), không vì chưa phân loại — nên dòng này
    # KHÔNG mở được bảng chọn, và câu trả lời đúng là `found: False` + vùng
    # RỖNG, chứ không phải `404`: "không có gì để mở ở đây" là một trạng
    # thái hợp lệ của chính màn hình này (xem `_identify_panel`).
    #
    # Ca `found: True` (dòng chưa phân loại, dùng chung tên hàng với hai BH
    # khác) được kiểm ở `tests/playwright/workspace-inline.spec.mjs`, trên
    # fixture dựng riêng cho nó.
    assert payload["found"] is False
    assert payload["regions"]["identify"].strip() == ""
    # Và nó KHÔNG mang cả trang: không layout, không bảng kê. Đây là lý do
    # route tồn tại — mở bảng chọn trước `UI-03` dựng lại cả `#app-content`.
    assert 'id="app-content"' not in response.get_data(as_text=True)
    assert len(response.get_data()) < 20 * 1024


# --- `UI-05`: route phân rã không tự cộng -------------------------------

def test_the_breakdown_route_matches_dashboard_metrics_exactly(client, engine):
    """Mệnh đề trung tâm của `UI-05`: route phân rã KHÔNG tính lại gì.

    Tổng của một mốc phải bằng ĐÚNG cái mà `dashboard_metrics.totals()` trả
    cho chính lát dòng của mốc ấy — nếu không, cái chấm trên biểu đồ và cái
    tooltip giải thích nó đang nói hai con số.
    """
    from app.web import business_service, business_store, revenue_timeline
    service = business_service.BusinessReportService(
        engine=engine, store=business_store.BusinessDecisionStore(engine))
    data = service.period(date_from=date(2026, 9, 1), date_to=date(2026, 9, 30),
                          period=(2026, 9))
    key = "2026-09-10"
    bucket = [d for d in data.details
              if d.get("sale_date") is not None
              and revenue_timeline.bucket_of(d["sale_date"], "ngay")[0] == key]
    assert bucket, "mốc kiểm phải có dòng thật"
    expected = dashboard_metrics.totals(bucket)

    payload = client.get(
        f"/api/v1/analytics/chart-breakdown?ky=2026-09&muc=ngay&moc={key}"
    ).get_json()
    assert payload["orders"] == expected.orders
    assert payload["lines"] == expected.lines
    assert payload["revenue"] == dashboard_presentation.money_cell(
        expected.sales_revenue)
    # Và phần chia theo nhân viên CỘNG LẠI đúng bằng tổng của mốc.
    assert payload["hidden_employees"] == 0
    total = sum(Decimal(row["revenue"]["text"].replace(".", "") or 0)
                for row in payload["rows"])
    assert total == Decimal(payload["revenue"]["text"].replace(".", ""))


def test_the_breakdown_route_refuses_a_request_without_a_bucket(client):
    response = client.get("/api/v1/analytics/chart-breakdown?ky=2026-09&muc=ngay")
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "VALIDATION_ERROR"


def test_the_breakdown_route_never_writes(client):
    """R6 §: "không route GHI". Route này là GET, và nó không nhận POST."""
    assert client.post("/api/v1/analytics/chart-breakdown").status_code == 405
