"""`STAB-02` — tải file KHÔNG bao giờ đi qua lớp điều hướng mảnh.

Lỗi được đóng ở đây, đúng như audit tái hiện được trên UI: `app.js` chặn
mọi link cùng origin, đọc MỌI response thành text và đưa vào DOM. Link xuất
Excel là một GET thường, nên các byte `PK…` của file .xlsx được ghi vào
trang thay vì tải về.

Ba lớp chặn, và file này canh cả ba ở phía server — phần browser thật nằm
ở `tests/browser/`:

    1. Response tải file KHAI ĐÚNG mình là file (`Content-Disposition:
       attachment`, `Content-Type` của xlsx). Đây là điều kiện để cửa kiểm
       trong `app.js` nhận ra nó; một response khai `text/html` sẽ vượt cửa
       và không lớp JS nào cứu được.
    2. Link tải file trong template mang `download`.
    3. Danh sách route tải file trong `app.js` KHỚP với tập route thật sự
       trả `attachment`. Đây là test chống TRÔI: một route tải file thêm
       về sau mà quên tên trong danh sách sẽ được test này chỉ ra.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from tests.fixtures import workspace_scale as ws
from tests.support import web_client

REPO = Path(__file__).resolve().parents[1]
APP_JS = REPO / "app" / "web" / "static" / "js" / "app.js"

#: Các route trả `Content-Disposition: attachment`. Danh sách này là bản
#: ghi của "tập route tải file" ở phía Python; `app.js` giữ bản của nó, và
#: `test_app_js_download_list_matches_server` canh hai bản khớp nhau.
ATTACHMENT_ROUTES = (
    "/kinh-doanh/xuat-excel",
    "/artifact/",
)

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


def test_app_js_download_list_matches_server():
    """Danh sách route tải file trong `app.js` KHỚP tập route thật.

    Test chống TRÔI. Nó không kiểm JS chạy đúng (việc đó ở
    `tests/browser/`) — nó kiểm rằng hai bản ghi của cùng một sự thật
    không lệch nhau, vì một route tải file thêm về sau sẽ không tự có tên
    trong file JS.
    """
    source = APP_JS.read_text()
    block = re.search(r"var DOWNLOAD_PATHS = \[(.*?)\];", source, re.S)
    assert block is not None, "không tìm thấy DOWNLOAD_PATHS trong app.js"
    listed = set(re.findall(r'"([^"]+)"', block.group(1)))
    assert listed == set(ATTACHMENT_ROUTES), (
        f"app.js liệt kê {sorted(listed)} nhưng server có "
        f"{sorted(ATTACHMENT_ROUTES)}")


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
