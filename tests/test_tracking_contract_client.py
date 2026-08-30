"""`_http_fetcher` — client của Tracking → Reports Data Contract V1.

Bộ test này chấm đúng **biên truyền tải**: URL nào được gọi, header nào được
gửi, và những gì trả về bị TỪ CHỐI. Nó cố ý không chạm mạng thật — `urlopen`
được thay tại chỗ — vì thứ cần chứng minh ở đây là hình dạng của request và
tính fail-closed của mọi nhánh lỗi, chứ không phải endpoint production đang
sống hay chết.

Vì sao cần bộ test này: trước đây Reports đọc thẳng Firebase RTDB
(`<database_url>/<node>.json?auth=<token>`), đường đó đòi Firebase Auth/App
Check và đã hỏng trên production. Đường mới KHÔNG có fallback về Firebase —
nếu hợp đồng lỗi thì capture `FAILED`. Hai nguồn song song chính là thứ
`INV-12` tồn tại để chặn, nên "không còn đường Firebase nào" cũng là một
assertion, không phải một lời hứa trong tài liệu.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.modules.pricing.resolution.sources import load_tracking_catalog_capture
from app.modules.product.identity.tracking_catalog import (
    CaptureStatus,
    canonical_content_hash,
)
from tools.tracking import capture_purchase_price_history as pph
from tools.tracking import capture_tracking_catalog as cat
from tools.tracking.capture_purchase_price_history import (
    API_KEY_ENV_VAR,
    API_KEY_HEADER,
    BASELINE_NODE,
    HISTORY_NODE,
    MISSING_API_KEY,
    CaptureError,
    _http_fetcher,
    write_capture,
)

SOURCE_URL = "https://price.tinphatcrm.com"
SECRET = "test-report-key-DO-NOT-LOG"
MOMENT = datetime(2026, 9, 1, 3, 0, tzinfo=timezone.utc)

BOARD = {
    "T2109NT1G": {"name": "Máy giặt LG T2109NT1G", "alt": ["T2109NT1G-DG"]},
    "SJX198VDG": {"name": "SJ-X198V-DG", "alt": []},
}
ALIAS = {"map": {"OLDCODE9": "SJX198VDG"}}
BASELINE = {"prices": {"T2109NT1G": 4100000}}
HISTORY = {"evt1": {"code": "T2109NT1G", "v": 4100000}}

CONTRACT = {
    "board": BOARD,
    "alias": ALIAS,
    BASELINE_NODE: BASELINE,
    HISTORY_NODE: HISTORY,
}


class FakeResponse:
    """Đủ giao diện mà `_http_fetcher` dùng: context manager, headers, read."""

    def __init__(self, body: bytes, content_type: str = "application/json"):
        self._body = body
        self.headers = {"Content-Type": content_type}

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self) -> bytes:
        return self._body


def install_transport(monkeypatch, handler):
    """Thay `urlopen` và ghi lại mọi `Request` đã phát."""
    sent: list = []

    def fake_urlopen(request, timeout=None):
        sent.append(request)
        return handler(request)

    monkeypatch.setattr(pph.urllib.request, "urlopen", fake_urlopen)
    return sent


def contract_handler(request):
    node = request.full_url.rsplit("/", 1)[-1]
    return FakeResponse(json.dumps(CONTRACT[node]).encode("utf-8"))


# ======================================================================
# 1. Hình dạng request — URL và header
# ======================================================================


def test_the_client_calls_the_contract_endpoint_not_a_firebase_node(monkeypatch):
    sent = install_transport(monkeypatch, contract_handler)
    assert _http_fetcher(SOURCE_URL, SECRET)("board") == BOARD
    assert sent[0].full_url == "https://price.tinphatcrm.com/api/xuat/board"
    # Không còn hậu tố `.json` của RTDB, không còn secret trong query string.
    assert ".json" not in sent[0].full_url
    assert "auth=" not in sent[0].full_url
    assert "?" not in sent[0].full_url
    assert sent[0].get_method() == "GET"


def test_the_secret_travels_only_in_the_report_key_header(monkeypatch):
    sent = install_transport(monkeypatch, contract_handler)
    _http_fetcher(SOURCE_URL, SECRET)(BASELINE_NODE)
    # `Request` viết hoa-thường lại tên header, nên so khớp không phân biệt hoa.
    headers = {k.lower(): v for k, v in sent[0].header_items()}
    assert headers[API_KEY_HEADER.lower()] == SECRET
    assert SECRET not in sent[0].full_url


def test_a_trailing_slash_on_the_source_url_does_not_double_up(monkeypatch):
    sent = install_transport(monkeypatch, contract_handler)
    _http_fetcher(SOURCE_URL + "/", SECRET)("alias")
    assert sent[0].full_url == "https://price.tinphatcrm.com/api/xuat/alias"


def test_all_four_contract_nodes_are_reachable_and_nothing_else(monkeypatch):
    install_transport(monkeypatch, contract_handler)
    fetch = _http_fetcher(SOURCE_URL, SECRET)
    for node in ("board", "alias", BASELINE_NODE, HISTORY_NODE):
        assert fetch(node) == CONTRACT[node]
    # `inv`, `phist`, `p/<NCC>` không nằm trong hợp đồng — chặn tại client,
    # không phát request rồi mới nhận 404.
    for forbidden in ("inv", "phist", "backup", "dnhap"):
        with pytest.raises(CaptureError, match="ngoài hợp đồng"):
            fetch(forbidden)


# ======================================================================
# 2. Fail closed — mọi nhánh lỗi
# ======================================================================


def test_a_missing_secret_fails_closed_without_sending_a_request(monkeypatch):
    sent = install_transport(monkeypatch, contract_handler)
    for absent in (None, ""):
        with pytest.raises(CaptureError, match=MISSING_API_KEY):
            _http_fetcher(SOURCE_URL, absent)("board")
    assert sent == []  # không hề thử một request không key


@pytest.mark.parametrize("code", [401, 403, 404, 500])
def test_an_http_error_fails_closed(monkeypatch, code):
    import urllib.error

    def handler(request):
        raise urllib.error.HTTPError(
            request.full_url, code, "Forbidden", {}, None
        )

    install_transport(monkeypatch, handler)
    with pytest.raises(CaptureError) as error:
        _http_fetcher(SOURCE_URL, SECRET)("board")
    assert str(code) in str(error.value)


def test_an_html_response_is_rejected_even_with_status_200(monkeypatch):
    """Một trang login/redirect trả 200 là cách im lặng nhất để rác thành
    'capture thành công'."""
    install_transport(
        monkeypatch,
        lambda request: FakeResponse(b"<!doctype html><html>...", "text/html"),
    )
    with pytest.raises(CaptureError, match="application/json"):
        _http_fetcher(SOURCE_URL, SECRET)("board")


def test_a_json_content_type_with_charset_is_still_accepted(monkeypatch):
    install_transport(
        monkeypatch,
        lambda request: FakeResponse(b"{}", "application/json; charset=utf-8"),
    )
    assert _http_fetcher(SOURCE_URL, SECRET)("board") == {}


def test_a_malformed_json_body_is_rejected(monkeypatch):
    install_transport(monkeypatch, lambda request: FakeResponse(b"{not json"))
    with pytest.raises(CaptureError, match="JSONDecodeError"):
        _http_fetcher(SOURCE_URL, SECRET)("board")


def test_no_error_message_ever_carries_the_secret(monkeypatch):
    """Thông điệp lỗi đi vào `failure_reason` của artifact — artifact vào repo."""
    import urllib.error

    def handler(request):
        raise urllib.error.HTTPError(request.full_url, 403, "Forbidden", {}, None)

    install_transport(monkeypatch, handler)
    with pytest.raises(CaptureError) as error:
        _http_fetcher(SOURCE_URL, SECRET)("board")
    assert SECRET not in str(error.value)


# ======================================================================
# 3. Không còn phụ thuộc Firebase trong operational path
# ======================================================================


def test_the_capture_tools_hold_no_firebase_transport_left():
    for path in (
        "tools/tracking/capture_purchase_price_history.py",
        "tools/tracking/capture_tracking_catalog.py",
    ):
        code = "\n".join(
            line
            for line in Path(path).read_text(encoding="utf-8").splitlines()
            if not line.lstrip().startswith("#")
        )
        # Bỏ docstring module (nó GIẢI THÍCH đường cũ đã bị rút — điều đó là
        # tài liệu đúng, không phải một đường mạng còn sống).
        body = code.split('"""', 2)[-1]
        for leak in (".json?", "auth=", "TRACKING_RTDB_TOKEN", "firebaseio",
                     "firebasedatabase", "App Check", "appCheck"):
            assert leak not in body, f"{path}: {leak}"


def test_the_rtdb_token_env_var_is_no_longer_an_operational_input(
    tmp_path, monkeypatch, capsys
):
    """Đặt TRACKING_RTDB_TOKEN mà KHÔNG đặt key hợp đồng → vẫn FAIL closed."""
    assert not hasattr(pph, "TOKEN_ENV_VAR")
    monkeypatch.setenv("TRACKING_RTDB_TOKEN", "một-token-rtdb-cũ")
    monkeypatch.delenv(API_KEY_ENV_VAR, raising=False)
    out = tmp_path / "capture.json"
    assert cat.main(
        ["--source-url", SOURCE_URL, "--captured-by", "op", "--out", str(out)]
    ) == 1
    snapshot = load_tracking_catalog_capture(out)
    assert snapshot.capture_status is CaptureStatus.FAILED
    assert MISSING_API_KEY in capsys.readouterr().err


def test_no_module_under_app_reaches_the_network():
    """`CHECK-105D-17` — ranh giới `ADR-101` không đổi sau lần sửa transport."""
    import re

    forbidden = re.compile(
        r"^\s*(?:import|from)\s+"
        r"(requests|urllib|http|httpx|socket|firebase\w*|google\.cloud"
        r"|boto3|aiohttp|websocket\w*|pyrebase)\b",
        re.MULTILINE,
    )
    for path in Path("app").rglob("*.py"):
        assert not forbidden.search(path.read_text(encoding="utf-8")), path


# ======================================================================
# 4. Từ hợp đồng tới artifact production — vòng khép kín
# ======================================================================


def test_a_catalog_capture_over_the_contract_is_complete_and_loadable(
    tmp_path, monkeypatch
):
    install_transport(monkeypatch, contract_handler)
    envelope = cat.build_capture(
        _http_fetcher(SOURCE_URL, SECRET),
        capture_id="TRK-CONTRACT-0001",
        captured_by="test",
        source_system_ref="tracking/api/xuat",
        captured_at=MOMENT,
    )
    assert envelope["capture_status"] == "COMPLETE"
    assert envelope["content_hash"] == canonical_content_hash(
        envelope["rows"], envelope["alias_map"]
    )
    assert [r["tracking_code"] for r in envelope["rows"]] == [
        "SJX198VDG",
        "T2109NT1G",
    ]
    # `alt` về từ hợp đồng đã là mảng — không tách chuỗi lại.
    assert envelope["rows"][1]["alt"] == ["T2109NT1G-DG"]
    assert envelope["alias_map"] == {"OLDCODE9": "SJX198VDG"}

    snapshot = load_tracking_catalog_capture(
        write_capture(envelope, tmp_path / "catalog.json")
    )
    snapshot.require_complete()
    assert snapshot.alias_map() == {"OLDCODE9": "SJX198VDG"}
    assert snapshot.row_for("T2109NT1G").alt == ("T2109NT1G-DG",)


def test_an_empty_board_over_the_contract_is_failed_not_an_empty_catalog(
    monkeypatch,
):
    install_transport(
        monkeypatch,
        lambda request: FakeResponse(b"{}")
        if request.full_url.endswith("/board")
        else FakeResponse(json.dumps(ALIAS).encode("utf-8")),
    )
    envelope = cat.build_capture(
        _http_fetcher(SOURCE_URL, SECRET),
        capture_id="TRK-CONTRACT-0002",
        captured_by="test",
        source_system_ref="tracking/api/xuat",
        captured_at=MOMENT,
    )
    assert envelope["capture_status"] == "FAILED"
    assert cat.EMPTY_SOURCE_NOT_ASSERTABLE in envelope["failure_reason"]


def test_a_price_history_capture_over_the_contract_carries_both_nodes(
    monkeypatch,
):
    install_transport(monkeypatch, contract_handler)
    envelope = pph.build_capture(
        _http_fetcher(SOURCE_URL, SECRET),
        capture_id="PPH-CONTRACT-0001",
        captured_by="test",
        source_system_ref="tracking/api/xuat",
        captured_at=MOMENT,
    )
    assert envelope["capture_status"] == "COMPLETE"
    assert envelope["data"][BASELINE_NODE] == BASELINE
    assert envelope["data"][HISTORY_NODE] == HISTORY


def test_a_failed_artifact_is_never_overwritten_by_a_later_success(
    tmp_path, monkeypatch
):
    """`INV-11` + §VIII: lần thử hỏng trước KHÔNG bị viết đè thành COMPLETE.
    Lần capture mới phải là một FILE MỚI, provenance cũ còn nguyên."""
    failed = pph.build_capture(
        _http_fetcher(SOURCE_URL, None),  # thiếu key → FAILED
        capture_id="PPH-OLD-FAILED",
        captured_by="test",
        source_system_ref="tracking/api/xuat",
        captured_at=MOMENT,
    )
    path = write_capture(failed, tmp_path / "capture.json")
    assert failed["capture_status"] == "FAILED"

    install_transport(monkeypatch, contract_handler)
    later = pph.build_capture(
        _http_fetcher(SOURCE_URL, SECRET),
        capture_id="PPH-NEW-COMPLETE",
        captured_by="test",
        source_system_ref="tracking/api/xuat",
        captured_at=MOMENT,
    )
    with pytest.raises(CaptureError, match="BẤT BIẾN"):
        write_capture(later, path)
    on_disk = json.loads(path.read_text(encoding="utf-8"))
    assert on_disk["capture_status"] == "FAILED"
    assert on_disk["capture_id"] == "PPH-OLD-FAILED"
    write_capture(later, tmp_path / "capture-2.json")  # đường đúng: file mới


def test_the_secret_never_lands_in_a_capture_artifact(tmp_path, monkeypatch):
    install_transport(monkeypatch, contract_handler)
    monkeypatch.setenv(API_KEY_ENV_VAR, SECRET)
    out = tmp_path / "catalog.json"
    assert cat.main(
        ["--source-url", SOURCE_URL, "--captured-by", "op", "--out", str(out)]
    ) == 0
    text = out.read_text(encoding="utf-8")
    assert SECRET not in text and API_KEY_HEADER not in text
