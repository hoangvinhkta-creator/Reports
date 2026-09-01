"""S071 — Tracking pull-on-run adapter (``tools.tracking.live_pull``).

Không gọi mạng thật: mọi test tiêm một ``fetch`` giả (cùng seam ``Fetcher``
mà các script capture đã dùng). Mục tiêu là chứng minh:

- Thành công: ba node fetch xong, ba file capture tạm được ghi, evidence
  đúng, ``cleanup()`` xoá sạch.
- REQUIRED (``purchase_price_history``, ``catalog``) fail → raise
  ``TrackingUnavailableError`` ngay, KHÔNG ghi report nào, KHÔNG rơi về một
  capture cũ nào (không có "cũ" ở đây — mỗi lần chạy live, không đọc đĩa
  trước).
- TUỲ CHỌN (``inv_map``) fail → không raise, chỉ ghi nhận status FAILED vào
  evidence, run vẫn tiếp tục với ``tracking_inv_map=None`` — cùng ngữ nghĩa
  "chưa nối" của S068 follow-up, không phải một lỗi bị nuốt.
- Timeout / 403 / 502 / malformed JSON đều là các hình dạng CỦA CÙNG MỘT
  loại lỗi (``CaptureError`` từ ``_http_fetcher``) — mô phỏng bằng fetch giả
  raise đúng loại lỗi đó, không cần dựng mạng thật.
- Sai schema (payload đọc được nhưng sai hợp đồng) là MỘT LOẠI LỖI KHÁC —
  build_capture bắt ``MalformedSourceError`` và tự chuyển envelope FAILED,
  không raise ở tầng fetch.
"""

from __future__ import annotations

import json

import pytest

from tools.tracking import live_pull
from tools.tracking.capture_purchase_price_history import (
    BASELINE_NODE, CaptureError, HISTORY_NODE,
)
from tools.tracking.capture_tracking_catalog import ALIAS_NODE, BOARD_NODE
from tools.tracking.capture_inv_map import INV_MAP_NODE

VALID_BOARD = {"BH001": {"name": "Máy lạnh 1HP", "alt": ["BH001-OLD"]}}
VALID_ALIAS = {"map": {"BH001-OLD": "BH001"}}
VALID_INV_MAP = {"map": {"máy lạnh 1hp": "BH001", "phí vận chuyển": "-"}}
VALID_BASELINE = {"cutover": {"BH001": 5_000_000}}
VALID_HISTORY = {"BH001": {"e1": {"t": "2026-01-01T00:00:00+00:00", "p": 5_000_000}}}


def _success_fetch(missing: frozenset[str] = frozenset()):
    payloads = {
        BASELINE_NODE: VALID_BASELINE,
        HISTORY_NODE: VALID_HISTORY,
        BOARD_NODE: VALID_BOARD,
        ALIAS_NODE: VALID_ALIAS,
        INV_MAP_NODE: VALID_INV_MAP,
    }

    def fetch(node: str):
        if node in missing:
            raise CaptureError(f"node {node!r} không đọc được: mô phỏng lỗi mạng")
        return payloads[node]

    return fetch


# --- Cấu hình --------------------------------------------------------------


def test_is_configured_requires_both_source_url_and_api_key():
    assert live_pull.is_configured({}) is False
    assert live_pull.is_configured({live_pull.SOURCE_URL_ENV_VAR: "https://x"}) is False
    assert live_pull.is_configured({live_pull.API_KEY_ENV_VAR: "secret"}) is False
    assert live_pull.is_configured(
        {live_pull.SOURCE_URL_ENV_VAR: "https://x", live_pull.API_KEY_ENV_VAR: "secret"}
    ) is True


def test_missing_source_url_raises_config_error_without_attempting_a_fetch(tmp_path):
    called = []

    def fetch(node):  # pragma: no cover - phải không bao giờ được gọi
        called.append(node)
        raise AssertionError("không được phát request khi thiếu source URL")

    with pytest.raises(live_pull.TrackingUnavailableError) as exc_info:
        live_pull.pull_live_captures(
            out_dir=tmp_path, source_url=None, api_key="secret", fetch=fetch,
        )
    assert exc_info.value.node == "config"
    assert exc_info.value.reason == "MISSING_SOURCE_URL"
    assert called == []


# --- Thành công --------------------------------------------------------------


def test_success_writes_three_capture_files_and_returns_evidence(tmp_path):
    result = live_pull.pull_live_captures(
        out_dir=tmp_path, source_url="https://tracking.example", api_key="secret",
        fetch=_success_fetch(),
    )
    assert result.tracking_capture.is_file()
    assert result.tracking_catalog.is_file()
    assert result.tracking_inv_map is not None
    assert result.tracking_inv_map.is_file()

    history_payload = json.loads(result.tracking_capture.read_text())
    assert history_payload["capture_status"] == "COMPLETE"
    catalog_payload = json.loads(result.tracking_catalog.read_text())
    assert catalog_payload["capture_status"] == "COMPLETE"
    inv_map_payload = json.loads(result.tracking_inv_map.read_text())
    assert inv_map_payload["capture_status"] == "COMPLETE"

    assert result.evidence["purchase_price_history_capture_id"]
    assert result.evidence["catalog_capture_id"]
    assert result.evidence["inv_map_capture_id"]
    assert result.evidence["inv_map_status"] == "COMPLETE"
    assert len(result.temp_paths) == 3


def test_cleanup_removes_every_temp_capture_file(tmp_path):
    result = live_pull.pull_live_captures(
        out_dir=tmp_path, source_url="https://tracking.example", api_key="secret",
        fetch=_success_fetch(),
    )
    for path in result.temp_paths:
        assert path.is_file()
    result.cleanup()
    for path in result.temp_paths:
        assert not path.is_file()


def test_cleanup_is_safe_to_call_twice(tmp_path):
    result = live_pull.pull_live_captures(
        out_dir=tmp_path, source_url="https://tracking.example", api_key="secret",
        fetch=_success_fetch(),
    )
    result.cleanup()
    result.cleanup()  # không raise


# --- REQUIRED: purchase_price_history / baseline ----------------------------


@pytest.mark.parametrize("failing_node", [BASELINE_NODE, HISTORY_NODE])
def test_purchase_price_history_failure_is_required_and_raises(tmp_path, failing_node):
    fetch = _success_fetch(missing=frozenset({failing_node}))
    with pytest.raises(live_pull.TrackingUnavailableError) as exc_info:
        live_pull.pull_live_captures(
            out_dir=tmp_path, source_url="https://tracking.example", api_key="secret",
            fetch=fetch,
        )
    assert exc_info.value.node == "purchase_price_history"
    # Không file capture nào được ghi khi REQUIRED fail — không có gì để
    # cleanup, và không report nào có thể được sinh ra từ trạng thái này.
    assert list(tmp_path.glob("*.json")) == []


def test_timeout_style_failure_on_history_node_is_reported_as_unavailable(tmp_path):
    def fetch(node):
        if node == HISTORY_NODE:
            raise CaptureError(
                f"không đọc được node {node!r} qua hợp đồng Tracking: "
                "URLError: <urlopen error timed out>"
            )
        return _success_fetch()(node)

    with pytest.raises(live_pull.TrackingUnavailableError) as exc_info:
        live_pull.pull_live_captures(
            out_dir=tmp_path, source_url="https://tracking.example", api_key="secret",
            fetch=fetch,
        )
    assert exc_info.value.node == "purchase_price_history"
    assert "timed out" in str(exc_info.value) or "URLError" in str(exc_info.value)


def test_403_style_failure_on_history_node_is_reported_as_unavailable(tmp_path):
    def fetch(node):
        if node == BASELINE_NODE:
            raise CaptureError(f"node {node!r}: hợp đồng phải trả application/json, nhận 'text/html'")
        return _success_fetch()(node)

    with pytest.raises(live_pull.TrackingUnavailableError) as exc_info:
        live_pull.pull_live_captures(
            out_dir=tmp_path, source_url="https://tracking.example", api_key="secret",
            fetch=fetch,
        )
    assert exc_info.value.node == "purchase_price_history"


# --- REQUIRED: catalog (board/alias) ----------------------------------------


@pytest.mark.parametrize("failing_node", [BOARD_NODE, ALIAS_NODE])
def test_catalog_failure_is_required_and_raises(tmp_path, failing_node):
    fetch = _success_fetch(missing=frozenset({failing_node}))
    with pytest.raises(live_pull.TrackingUnavailableError) as exc_info:
        live_pull.pull_live_captures(
            out_dir=tmp_path, source_url="https://tracking.example", api_key="secret",
            fetch=fetch,
        )
    assert exc_info.value.node == "catalog"
    assert list(tmp_path.glob("*.json")) == []


def test_502_style_failure_on_catalog_node_is_reported_as_unavailable(tmp_path):
    def fetch(node):
        if node == BOARD_NODE:
            raise CaptureError(f"không đọc được node {node!r}: OSError: 502 Bad Gateway")
        return _success_fetch()(node)

    with pytest.raises(live_pull.TrackingUnavailableError) as exc_info:
        live_pull.pull_live_captures(
            out_dir=tmp_path, source_url="https://tracking.example", api_key="secret",
            fetch=fetch,
        )
    assert exc_info.value.node == "catalog"


def test_malformed_catalog_schema_is_reported_as_unavailable_not_a_crash(tmp_path):
    """Payload đọc được (không phải lỗi mạng) nhưng sai hợp đồng (`board`
    không phải một ánh xạ) — `MalformedSourceError` bị `build_capture` bắt
    và chuyển thành envelope FAILED, KHÔNG raise thẳng ra ngoài."""

    def fetch(node):
        if node == BOARD_NODE:
            return ["không", "phải", "một", "ánh", "xạ"]
        return _success_fetch()(node)

    with pytest.raises(live_pull.TrackingUnavailableError) as exc_info:
        live_pull.pull_live_captures(
            out_dir=tmp_path, source_url="https://tracking.example", api_key="secret",
            fetch=fetch,
        )
    assert exc_info.value.node == "catalog"


def test_missing_endpoint_style_failure_is_reported_as_unavailable(tmp_path):
    """Node không tồn tại/404 đi qua cùng đường ``CaptureError`` với timeout
    và 403 — client không phân biệt hình dạng lỗi mạng, chỉ phân biệt
    node nào fail."""

    def fetch(node):
        if node == ALIAS_NODE:
            raise CaptureError(f"node {node!r}: HTTP 404 Not Found")
        return _success_fetch()(node)

    with pytest.raises(live_pull.TrackingUnavailableError) as exc_info:
        live_pull.pull_live_captures(
            out_dir=tmp_path, source_url="https://tracking.example", api_key="secret",
            fetch=fetch,
        )
    assert exc_info.value.node == "catalog"


# --- TUỲ CHỌN: inv_map -------------------------------------------------------


def test_inv_map_failure_does_not_block_the_run(tmp_path):
    fetch = _success_fetch(missing=frozenset({INV_MAP_NODE}))
    result = live_pull.pull_live_captures(
        out_dir=tmp_path, source_url="https://tracking.example", api_key="secret",
        fetch=fetch,
    )
    assert result.tracking_inv_map is None
    assert result.evidence["inv_map_capture_id"] is None
    assert result.evidence["inv_map_status"] == "FAILED"
    assert result.evidence["inv_map_failure_reason"]
    # Hai nguồn REQUIRED vẫn ghi được file bình thường.
    assert result.tracking_capture.is_file()
    assert result.tracking_catalog.is_file()


def test_malformed_inv_map_schema_does_not_block_the_run(tmp_path):
    def fetch(node):
        if node == INV_MAP_NODE:
            return {"unexpected_top_level_key": {}}
        return _success_fetch()(node)

    result = live_pull.pull_live_captures(
        out_dir=tmp_path, source_url="https://tracking.example", api_key="secret", fetch=fetch,
    )
    assert result.tracking_inv_map is None
    assert result.evidence["inv_map_status"] == "FAILED"
