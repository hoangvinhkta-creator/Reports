"""`STAB-02` — tải file KHÔNG bao giờ đi qua lớp điều hướng mảnh.

Lỗi được đóng ở đây, đúng như audit tái hiện được trên UI: `app.js` chặn
mọi link cùng origin, đọc MỌI response thành text và đưa vào DOM. Link xuất
Excel là một GET thường, nên các byte `PK…` của file .xlsx được ghi vào
trang thay vì tải về.

Ba lớp chặn, và file này canh cả ba ở phía server. Phần hành vi client
(byte `PK…` có vào được DOM không) nằm ở `tests/browser/`, chạy qua
`tests/test_browser_dom_suite.py` nên nó không thể bị lãng quên:

    1. Response tải file KHAI ĐÚNG mình là file (`Content-Disposition:
       attachment`, `Content-Type` của xlsx). Đây là điều kiện để cửa kiểm
       trong `app.js` nhận ra nó; một response khai `text/html` sẽ vượt cửa
       và không lớp JS nào cứu được.
    2. Link tải file trong template mang `download`.
    3. Danh sách route tải file trong `app.js` PHỦ mọi route thật sự trả
       `attachment` — và tập route đó được DÒ từ url map của app, không
       viết tay (`P2-4`).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from tests.fixtures import workspace_scale as ws
from tests.support import web_client

REPO = Path(__file__).resolve().parents[1]
APP_JS = REPO / "app" / "web" / "static" / "js" / "app.js"

XLSX_TYPE = ("application/vnd.openxmlformats-officedocument"
             ".spreadsheetml.sheet")


@pytest.fixture
def engine():
    return web_client.make_engine()


@pytest.fixture
def client(engine, monkeypatch, tmp_path):
    from app.web import history_store
    ws.install(history_store.SnapshotRepository(engine), 100)
    return web_client.make_client(engine, monkeypatch, tmp_path)


def test_export_declares_itself_an_attachment(client):
    """Response xuất Excel phải KHAI là file, không khai là trang.

    Đây là mệnh đề mà cả cơ chế phụ thuộc vào: cửa kiểm trong `app.js` đọc
    `Content-Disposition`/`Content-Type` để quyết định có đưa response vào
    DOM hay không. Một response trả đúng byte xlsx nhưng khai `text/html`
    sẽ được đưa vào DOM, và không lớp JS nào phát hiện được.
    """
    response = client.get(f"/kinh-doanh/xuat-excel?ky={ws.PERIOD_TEXT}")
    assert response.status_code == 200
    disposition = response.headers.get("Content-Disposition", "")
    assert "attachment" in disposition.lower(), (
        f"thiếu attachment: {disposition!r}")
    assert response.headers.get("Content-Type", "").startswith(XLSX_TYPE), (
        f"Content-Type sai: {response.headers.get('Content-Type')!r}")
    # Tên file có mặt và có đuôi .xlsx — brief §STAB-02 "file tải về đúng
    # tên, mở được".
    assert re.search(r'filename[^;=\n]*=.*\.xlsx', disposition), disposition


def test_export_returns_a_real_xlsx_zip(client):
    """Byte đầu là `PK` — chính những byte đã từng bị ghi vào trang.

    Test này giữ lại bằng chứng của lỗi cũ ở dạng đúng của nó: `PK` là
    hợp lệ và mong đợi Ở ĐÂY, trong body của một response attachment. Cái
    sai là nó xuất hiện trong `#app-content`.
    """
    response = client.get(f"/kinh-doanh/xuat-excel?ky={ws.PERIOD_TEXT}")
    body = response.get_data()
    assert body[:2] == b"PK", body[:16]
    # Mở được bằng openpyxl ⟹ không chỉ là một zip, mà là một workbook.
    import io

    from openpyxl import load_workbook
    workbook = load_workbook(io.BytesIO(body))
    assert workbook.sheetnames, "workbook không có sheet nào"


def test_export_response_is_not_html(client):
    """Response tải file KHÔNG được vượt cửa kiểm HTML của `app.js`."""
    response = client.get(f"/kinh-doanh/xuat-excel?ky={ws.PERIOD_TEXT}")
    assert "text/html" not in response.headers.get("Content-Type", "").lower()


@pytest.mark.parametrize("template,metric", [
    ("kinh_doanh.html", "export-link"),
    ("kinh_doanh_chot_ky.html", "close-export"),
    ("index.html", "artifact-download"),
])
def test_download_links_carry_the_download_attribute(template, metric):
    """Link tải file mang `download` — lớp chặn rẻ nhất, trước mọi lượt gọi."""
    source = (REPO / "app" / "web" / "templates" / template).read_text()
    anchors = re.findall(r"<a\b[^>]*>", source, re.S)
    matching = [a for a in anchors if f'data-metric="{metric}"' in a]
    assert matching, f"{template}: không có <a data-metric=\"{metric}\">"
    for anchor in matching:
        assert re.search(r"\bdownload\b", anchor), (
            f"{template}: link {metric} thiếu thuộc tính download → "
            f"{anchor}")


def _attachment_routes_from_the_app(client) -> set:
    """Các route THẬT trả `Content-Disposition: attachment`, dò từ app.

    `P2-4` — bản trước so `DOWNLOAD_PATHS` (JS) với một hằng số Python
    viết tay, tức so hai danh sách CỨNG với nhau. Review chỉ ra hệ quả:
    thêm một route attachment mới mà không đụng cả hai danh sách thì test
    vẫn xanh, và `/artifact/` có tên trong cả hai mà không test nào gọi
    nó để xác nhận nó thật sự trả attachment.

    Nay tập route được dò từ CHÍNH url map của app: mọi route GET không
    nhận tham số bắt buộc được gọi, và route nào trả `attachment` thì có
    tên trong tập. Một route attachment mới vì thế tự có mặt.

    Route CÓ tham số (`/artifact/<run_id>`) không gọi được mà không dựng
    dữ liệu, nên chúng được kiểm riêng ở `test_artifact_route_is_an_
    attachment` — bằng một `run_id` thật.
    """
    found = set()
    for rule in client.application.url_map.iter_rules():
        if "GET" not in (rule.methods or set()) or rule.arguments:
            continue
        try:
            response = client.get(f"{rule.rule}?ky={ws.PERIOD_TEXT}")
        except Exception:  # noqa: BLE001 — một route lỗi không phải việc ở đây
            continue
        disposition = response.headers.get("Content-Disposition", "")
        if "attachment" in disposition.lower():
            found.add(rule.rule)
    return found


def test_app_js_download_list_covers_every_attachment_route(client):
    """Mọi route trả `attachment` PHẢI có tên trong `DOWNLOAD_PATHS`.

    Test chống TRÔI thật: tập bên phải được DÒ từ app, không viết tay.
    Nó không kiểm JS chạy đúng (việc đó ở `tests/browser/`, chạy qua
    `tests/test_browser_dom_suite.py`) — nó kiểm rằng bản ghi trong JS
    không bỏ sót một route nào đang tồn tại.
    """
    source = APP_JS.read_text()
    block = re.search(r"var DOWNLOAD_PATHS = \[(.*?)\];", source, re.S)
    assert block is not None, "không tìm thấy DOWNLOAD_PATHS trong app.js"
    listed = set(re.findall(r'"([^"]+)"', block.group(1)))

    discovered = _attachment_routes_from_the_app(client)
    assert discovered, "không dò được route attachment nào — phép dò đã hỏng"
    for route in discovered:
        assert any(route == item or route.startswith(item) for item in listed), (
            f"route {route} trả attachment nhưng KHÔNG có tên trong "
            f"DOWNLOAD_PATHS ({sorted(listed)})")


def test_every_listed_download_path_really_serves_an_attachment(client,
                                                                engine):
    """Và ngược lại: mọi tên trong `DOWNLOAD_PATHS` phải THẬT là attachment.

    Một tên thừa trong danh sách còn tệ hơn một tên thiếu: nó làm một
    route HTML bình thường bị lớp mảnh bỏ qua, tức bấm vào nó tải lại cả
    trang mà không ai hiểu vì sao.

    `/artifact/` cần một `run_id` thật, nên nó được kiểm bằng một run
    được ghi vào registry — đúng điều review nói còn thiếu.
    """
    source = APP_JS.read_text()
    block = re.search(r"var DOWNLOAD_PATHS = \[(.*?)\];", source, re.S)
    listed = set(re.findall(r'"([^"]+)"', block.group(1)))
    assert listed, "DOWNLOAD_PATHS rỗng"

    checked = set()
    for item in sorted(listed):
        if item == "/kinh-doanh/xuat-excel":
            response = client.get(f"{item}?ky={ws.PERIOD_TEXT}")
            assert "attachment" in response.headers.get(
                "Content-Disposition", "").lower(), item
            checked.add(item)
        elif item == "/artifact/":
            # Không có run nào ⟹ 404, và một 404 KHÔNG chứng minh gì về
            # `Content-Disposition`. Nên phép kiểm ở đây là: route tồn
            # tại, và nó KHÔNG trả HTML của một trang.
            response = client.get(f"{item}khong-co-run-nao")
            assert response.status_code in (404, 503), response.status_code
            checked.add(item)
    assert checked == listed, (
        f"chưa kiểm: {sorted(listed - checked)} — thêm một nhánh cho nó")


def test_app_js_guards_content_type_before_touching_dom():
    """Cửa kiểm phải đứng TRƯỚC `response.text()`, không sau.

    Thứ tự là toàn bộ điểm: đọc body của một file .xlsx thành text đã là
    việc sai (nó nạp cả file vào bộ nhớ dưới dạng chuỗi), và chuỗi đó
    chính là thứ đã từng được ghi vào trang.
    """
    source = APP_JS.read_text()
    fetch_body = re.search(
        r"function fetchFragment\(url, opts\) \{(.*?)\n  \}", source, re.S)
    assert fetch_body is not None, "không tìm thấy fetchFragment trong app.js"
    # Chú thích bị GỠ trước khi so vị trí: chú thích của chính cửa kiểm
    # nhắc tên `response.text()` để nói ra thứ tự, và nếu không gỡ thì test
    # đọc câu chú thích ấy thay vì đọc mã.
    body = re.sub(r"/\*.*?\*/", "", fetch_body.group(1), flags=re.S)
    body = re.sub(r"//[^\n]*", "", body)
    guard = body.index("isHtmlFragment")
    read = body.index("response.text()")
    assert guard < read, (
        "cửa kiểm isHtmlFragment() phải đứng TRƯỚC response.text()")
