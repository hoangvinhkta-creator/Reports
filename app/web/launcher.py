"""Local launch experience cho Reports Web (S070).

Double-click ``Open Reports Web.command`` → khởi động server localhost →
mở trình duyệt. Không daemon, không launchd, không production process
manager — chạy foreground, đóng terminal/Ctrl+C là dừng server.

Dùng ``werkzeug.serving.make_server`` trực tiếp (thay vì tự pre-check port
bằng module ``socket``): việc bind xảy ra ngay khi tạo server, đồng bộ, và
raise ``OSError`` nếu cổng đã bận — không có race giữa bước kiểm tra và bước
bind. Server dựng bằng cách này cũng không kèm Werkzeug debugger/reloader,
nên "debug mode off" là bất biến theo cấu trúc, không chỉ một cờ có thể quên
truyền.

``threaded=True`` là bắt buộc, không phải tối ưu: ``make_server`` mặc định
dựng ``BaseWSGIServer`` (single-threaded) — khi launcher tự mở trình duyệt
(``webbrowser.open`` bên dưới), tab đó giữ một kết nối HTTP keep-alive, và
server single-threaded sẽ treo BẤT KỲ request nào khác (upload lần 2,
refresh, download, feedback) vô thời hạn cho đến khi tab đó đóng kết nối —
đã verify trực tiếp bằng repro (giữ một keep-alive connection mở, request
độc lập thứ hai timeout 100% cho tới khi connection đầu đóng). ``threaded``
chỉ đổi model I/O (mỗi connection một thread) chứ không bật debugger/
reloader — "debug off" ở trên vẫn đúng nguyên.
"""

from __future__ import annotations

import sys
import threading
import webbrowser
from pathlib import Path

from werkzeug.serving import make_server

REPO_ROOT = Path(__file__).resolve().parents[2]
if __package__ in (None, ""):
    sys.path.insert(0, str(REPO_ROOT))

from app.web.server import create_app  # noqa: E402

HOST = "127.0.0.1"
PORT = 8765


def main() -> int:
    url = f"http://{HOST}:{PORT}/"
    app = create_app()
    try:
        httpd = make_server(HOST, PORT, app, threaded=True)
    except OSError:
        print(f"REPORTS_WEB_ALREADY_RUNNING\nMở trình duyệt vào: {url}")
        webbrowser.open(url)
        return 0

    threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    httpd.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
