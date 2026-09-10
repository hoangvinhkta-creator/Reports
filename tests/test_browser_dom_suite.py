"""`P1-6` — chạy bộ kiểm DOM (`tests/browser/`) từ trong pytest.

Vì sao có file này thay vì chỉ một dòng trong tài liệu: review độc lập
chỉ ra rằng ba chỗ trong repo trỏ tới `tests/browser/` — một thư mục
KHÔNG TỒN TẠI. Một bộ kiểm chỉ chạy khi ai đó nhớ gõ `node --test` sẽ
đi đúng con đường ấy: nó tồn tại một thời gian rồi lặng lẽ không còn
được chạy.

Nối vào pytest làm bộ kiểm DOM thành một phần của cùng một lệnh mà mọi
người đã chạy, và một lần `app.js` hỏng sẽ đỏ ở cùng chỗ với mọi lần
hỏng khác.

## Bỏ qua khi nào

Không có `node` hoặc chưa `npm install` ⟹ `pytest.skip` với câu nói rõ
phải làm gì. Đó là đánh đổi có ý thức: một test bị bỏ qua trông y hệt một
test đã đạt trong dòng tổng kết, nên câu skip phải nói ra chính xác lệnh
cần chạy. CI phải cài `node_modules` để bộ này thật sự chạy.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
BROWSER_DIR = REPO_ROOT / "tests" / "browser"

#: Cùng dạng glob mà `node --test` nhận. KHÔNG dùng đường dẫn thư mục
#: trần: Node 22 coi `node --test tests/browser/` là một module và báo
#: `MODULE_NOT_FOUND` — một lỗi trông như bộ kiểm hỏng chứ như một lệnh
#: sai.
TEST_GLOB = "tests/browser/*.test.mjs"


def test_the_browser_directory_exists_and_has_tests():
    """Thư mục mà ba file khác trỏ tới PHẢI tồn tại và phải có test.

    Đây là test rẻ nhất trong file, và nó là test đã thiếu: bản trước
    tham chiếu `tests/browser/` từ `scripts/stab01_baseline.py` và
    `tests/test_stab02_download_contract.py` trong khi thư mục không có.
    """
    assert BROWSER_DIR.is_dir(), (
        f"{BROWSER_DIR} không tồn tại, nhưng nhiều file trong repo trỏ tới nó")
    files = sorted(path.name for path in BROWSER_DIR.glob("*.test.mjs"))
    assert files, "tests/browser/ không có file test nào"
    assert (BROWSER_DIR / "harness.mjs").is_file()


def test_the_dom_suite_passes():
    """Chạy `node --test` và bắt buộc nó xanh.

    Output của Node được in nguyên văn khi đỏ: nó nói chính xác mệnh đề
    nào hỏng, và một dòng "exit code 1" thì không.
    """
    node = shutil.which("node")
    if node is None:
        pytest.skip("Cần Node.js để chạy bộ kiểm DOM (tests/browser/).")
    if not (REPO_ROOT / "node_modules" / "jsdom").is_dir():
        pytest.skip(
            "Cần jsdom: chạy `npm install` ở gốc repo. Bộ kiểm DOM "
            "(tests/browser/) là bằng chứng cho STAB-02/03/04/05 ở phía "
            "client — không có nó, các mệnh đề đó KHÔNG được kiểm.")

    result = subprocess.run(
        [node, "--test", TEST_GLOB],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=300)
    assert result.returncode == 0, (
        "bộ kiểm DOM đỏ:\n" + result.stdout[-6000:] + "\n" + result.stderr[-2000:])
    # `# fail 0` phải có mặt: một lần `node --test` không tìm thấy file
    # nào cũng trả về 0, và khi đó "xanh" không nói gì.
    assert "# fail 0" in result.stdout, result.stdout[-3000:]
    assert "# pass 0" not in result.stdout, (
        "bộ kiểm DOM không chạy test nào — glob có thể đã sai:\n"
        + result.stdout[-2000:])


#: Byte điều khiển ASCII, TRỪ tab/LF/CR — ba byte hợp lệ trong mã nguồn.
CONTROL_BYTES = (bytes(range(0x00, 0x09)) + b"\x0b\x0c"
                 + bytes(range(0x0e, 0x20)))


def test_no_browser_test_file_contains_raw_control_bytes():
    """Không file nào trong `tests/browser/` được chứa byte điều khiển THÔ.

    Vì sao đây là một cửa chặn chứ một chuyện thẩm mỹ. `stab02_download`
    nói về những byte mở đầu của một file .xlsx (`PK\\x03\\x04`), và cách
    tự nhiên nhất để viết chúng là dán thẳng vào mã nguồn. Làm thế thì
    file có một byte NUL, và git chuyển sang chế độ BINARY cho nó:

        tests/browser/stab02_download.test.mjs | Bin 5344 -> 9901 bytes

    Từ lúc đó không ai review được diff của chính file mang bằng chứng
    `STAB-02`, và một thay đổi làm yếu bài kiểm sẽ đi qua mà không ai
    thấy. Lỗi này đã xảy ra HAI lần trong đợt này — lần thứ hai vì công
    cụ đọc file hiện byte điều khiển thành khoảng trắng, nên nó được dán
    lại mà không ai nhận ra.

    Cách viết đúng là escape của JavaScript (`"\\u0003"`): chuỗi lúc chạy
    vẫn chứa đúng những byte ấy, nên bài kiểm vẫn nói về đúng thứ nó
    định nói, mà file vẫn là text.
    """
    guilty = {}
    for path in sorted(BROWSER_DIR.glob("*.mjs")):
        raw = path.read_bytes()
        found = sorted({byte for byte in CONTROL_BYTES if bytes([byte]) in raw})
        if found:
            guilty[path.name] = [f"0x{byte:02x}" for byte in found]
    assert guilty == {}, (
        f"byte điều khiển thô trong bộ kiểm DOM: {guilty}. git sẽ coi file "
        "là binary và diff của nó thành không đọc được — hãy viết bằng "
        "escape (\\uXXXX) thay vì dán byte thô.")
