"""`UI-01`/`UI-02` — chạy bộ kiểm Playwright (`tests/playwright/`) từ pytest.

Cùng lý do `tests/test_browser_dom_suite.py` tồn tại cho `tests/browser/`
(jsdom): một bộ kiểm chỉ chạy khi ai đó nhớ gõ `npx playwright test` sẽ đi
đúng con đường "tồn tại một thời gian rồi lặng lẽ không còn được chạy". Nối
nó vào pytest làm nó thành một phần của cùng một lệnh mà mọi người đã chạy.

`tests/browser/` (jsdom) kiểm LOGIC của `app.js` (response nào vào DOM,
response cũ có bị chặn không). Bộ này kiểm những gì jsdom khai rõ mình
KHÔNG làm được (xem đầu `tests/browser/harness.mjs`): thời gian parse/
render/paint thật, `<dialog>.showModal()` có thật sự bẫy focus không, vị
trí cuộn thật sau khi layout chạy, Back/Forward thật của trình duyệt.

## Bỏ qua khi nào

Không có `node`, chưa `npm install` (thiếu `@playwright/test`), hoặc không
tìm thấy Chromium đã cài sẵn (biến `PLAYWRIGHT_CHROMIUM_PATH`, mặc định
`/opt/pw-browsers/chromium` — xem `playwright.config.mjs`) ⟹ `pytest.skip`
với câu nói rõ phải làm gì. Không có `.venv/bin/python` (máy chủ fixture
của Playwright cần các gói `web`/`history`, xem `tests/playwright/
fixture_server.py`) cũng bỏ qua theo cùng lý do.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def _chromium_path() -> Path:
    return Path(os.environ.get("PLAYWRIGHT_CHROMIUM_PATH",
                                "/opt/pw-browsers/chromium"))


def _python_path() -> Path:
    candidate = REPO_ROOT / ".venv" / "bin" / "python"
    return candidate if candidate.is_file() else Path("python3")


def test_playwright_ui_suite_passes():
    """Chạy `npx playwright test` và bắt buộc nó xanh.

    Output đầy đủ được in khi đỏ, cùng kỷ luật `test_browser_dom_suite.py`
    đã dùng: một dòng "exit code 1" không nói cho ai biết mệnh đề nào hỏng.
    """
    npx = shutil.which("npx")
    if npx is None:
        pytest.skip("Cần Node.js/npm (lệnh `npx`) để chạy bộ kiểm Playwright.")
    if not (REPO_ROOT / "node_modules" / "@playwright" / "test").is_dir():
        pytest.skip(
            "Cần @playwright/test: chạy `npm install` ở gốc repo. Bộ kiểm "
            "Playwright (tests/playwright/) là bằng chứng browser THẬT cho "
            "UI-01/UI-02 — không có nó, các mệnh đề đó KHÔNG được kiểm.")
    if not _chromium_path().exists():
        pytest.skip(
            f"Không thấy Chromium tại {_chromium_path()}. Đặt biến môi "
            "trường PLAYWRIGHT_CHROMIUM_PATH trỏ tới một Chromium đã cài, "
            "hoặc chạy `npx playwright install chromium` một lần rồi bỏ "
            "`launchOptions.executablePath` khỏi playwright.config.mjs.")
    python = _python_path()
    if python.name != "python3" and not python.is_file():
        pytest.skip(
            f"Không thấy {python} — máy chủ fixture của Playwright "
            "(tests/playwright/fixture_server.py) cần một venv có cài "
            "`pip install -e '.[dev,web,history]'`.")

    env = dict(os.environ)
    env.setdefault("PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD", "1")
    env.setdefault("REPORTS_PYTHON", str(python))

    result = subprocess.run(
        [npx, "playwright", "test"],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=300, env=env)
    assert result.returncode == 0, (
        "bộ kiểm Playwright đỏ:\n" + result.stdout[-8000:] + "\n"
        + result.stderr[-3000:])
