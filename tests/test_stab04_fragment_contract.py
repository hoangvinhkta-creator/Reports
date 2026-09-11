"""`STAB-04` — hợp đồng của response MẢNH so với response ĐẦY ĐỦ.

Lỗi được đóng ở đây, đúng như audit mô tả và như phép đo cục bộ tái hiện:
template trả cả `<main id="app-content">` trong response mảnh, `app.js` gán
chuỗi đó vào `innerHTML` của wrapper đang có, và DOM có HAI phần tử cùng
`id`. `document.getElementById()` trả phần tử ĐẦU TIÊN, nên mỗi lần điều
hướng kế tiếp bọc thêm một tầng.

Hai mệnh đề của hợp đồng, và file này canh cả hai trên MỌI route dựng
`layout.html`:

    response ĐẦY ĐỦ  → ĐÚNG MỘT `id="app-content"`
    response MẢNH    → KHÔNG `id="app-content"` nào

Vì sao là một test chứ không một lần sửa im lặng: cái wrapper ấy nằm ở
`layout.html` và mọi trang đều thừa hưởng nó. Một lần thêm lại vô tình
(dời một khối `{% if %}`, thêm một layout thứ hai) sẽ không hiện ra ở bất
kỳ màn hình nào cho tới khi ai đó điều hướng ba lần trong cùng một tab.
"""

from __future__ import annotations

import re

import pytest

from tests.fixtures import workspace_scale as ws
from tests.support import web_client


@pytest.fixture
def engine():
    return web_client.make_engine()


@pytest.fixture
def client(engine, monkeypatch, tmp_path):
    """App thật + 100 dòng: đủ để mọi route dựng bảng có nội dung.

    100 chứ không 5.000: file này kiểm HÌNH DẠNG của response, và hình dạng
    không đổi theo số dòng. Số đo quy mô nằm ở `scripts/stab01_baseline.py`.
    """
    from app.web import history_store
    ws.install(history_store.SnapshotRepository(engine), 100)
    return web_client.make_client(engine, monkeypatch, tmp_path)


#: Mọi route GET dựng `layout.html` mà một người dùng có thể tới bằng cách
#: bấm trong tab. Danh sách này là danh sách các trạng thái điều hướng mà
#: brief §STAB-04 nói "sau mọi fragment navigation chỉ có đúng một
#: `#app-content`".
NAV_ROUTES = (
    "/kinh-doanh",
    "/kinh-doanh/nhan-vien",
    "/kinh-doanh/chot-ky",
    "/kinh-doanh/co-cau",
    "/kinh-doanh/danh-gia",
    "/kinh-doanh/thuong-hieu",
    "/kinh-doanh/target",
    "/du-lieu",
    "/tong-quan",
    "/san-pham",
    "/nhan-vien",
    "/lich-su",
    "/doanh-so-ngay",
    "/giai-thich",
)

APP_CONTENT = re.compile(r'id="app-content"')


@pytest.mark.parametrize("path", NAV_ROUTES)
def test_full_response_has_exactly_one_app_content(client, path):
    """Trang tải THẬT phải có đúng một wrapper — không zero, không hai."""
    response = client.get(path)
    assert response.status_code in (200, 302), f"{path} → {response.status_code}"
    if response.status_code != 200:
        pytest.skip(f"{path} chuyển hướng ({response.status_code})")
    html = response.get_data(as_text=True)
    assert len(APP_CONTENT.findall(html)) == 1, (
        f"{path}: response đầy đủ phải có ĐÚNG MỘT id=\"app-content\"")


@pytest.mark.parametrize("path", NAV_ROUTES)
def test_fragment_response_has_no_app_content(client, path):
    """Response mảnh KHÔNG được mang wrapper — nó sẽ bị lồng vào wrapper cũ."""
    response = client.get(path, headers={"X-Fragment": "1"})
    assert response.status_code in (200, 302), f"{path} → {response.status_code}"
    if response.status_code != 200:
        pytest.skip(f"{path} chuyển hướng ({response.status_code})")
    html = response.get_data(as_text=True)
    assert APP_CONTENT.findall(html) == [], (
        f"{path}: response mảnh KHÔNG được chứa id=\"app-content\" — "
        "app.js gán nó vào innerHTML của wrapper đang có, tạo hai phần tử "
        "cùng id")


@pytest.mark.parametrize("path", NAV_ROUTES)
def test_fragment_response_has_no_page_shell(client, path):
    """Mảnh cũng không được mang doctype/head/nav — đó là khung của cả trang.

    Kiểm cùng chỗ với wrapper vì chúng cùng một lớp lỗi: một khối `{% if
    not partial %}` bị dời sai chỗ sẽ để lọt cả nhóm này, và một `<script
    src="app.js">` lọt vào mảnh sẽ đăng ký listener lần thứ hai — mỗi lần
    điều hướng thêm một bản sao, và một cú bấm phát ra n request.
    """
    response = client.get(path, headers={"X-Fragment": "1"})
    if response.status_code != 200:
        pytest.skip(f"{path} chuyển hướng ({response.status_code})")
    html = response.get_data(as_text=True)
    for forbidden in ("<!doctype", "<html", "<head", "</body>",
                      'class="ncc-tabs"', "js/app.js"):
        assert forbidden not in html.lower(), (
            f"{path}: response mảnh chứa {forbidden!r} — đó là khung trang, "
            "chỉ được dựng ở lần tải thật")


def test_simulated_double_navigation_keeps_one_wrapper(client):
    """Mô phỏng ĐÚNG việc `app.js` làm: dựng trang rồi thay mảnh hai lần.

    Đây là test nói ra hậu quả THẬT của lỗi thay vì chỉ đếm chuỗi trong một
    response: nó ghép trang đầy đủ với hai lần thay mảnh nối tiếp, đúng cách
    `swapContent()` ghép, rồi đếm lại. Với bản lỗi, con số là 3.
    """
    full = client.get("/kinh-doanh").get_data(as_text=True)
    assert len(APP_CONTENT.findall(full)) == 1

    dom = full
    for path in ("/kinh-doanh/nhan-vien", "/kinh-doanh/chot-ky"):
        fragment = client.get(path, headers={"X-Fragment": "1"}).get_data(
            as_text=True)
        # `swapContent()` thay NỘI DUNG BÊN TRONG wrapper. Ở đây ta thay
        # phần giữa hai thẻ `<main …>` / `</main>` của DOM đang có bằng
        # mảnh mới — cùng phép toán, trên chuỗi.
        dom = re.sub(
            r'(<main class="tp-main" id="app-content">).*?(</main>)',
            lambda m: m.group(1) + fragment + m.group(2), dom, count=1,
            flags=re.S)
        assert len(APP_CONTENT.findall(dom)) == 1, (
            f"sau khi thay mảnh {path}: DOM có "
            f"{len(APP_CONTENT.findall(dom))} phần tử id=\"app-content\"")
