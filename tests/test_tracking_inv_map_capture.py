"""`tools/tracking/capture_inv_map.py` + schema/loader — S068 follow-up.

Cùng khuôn `tests/test_tracking_catalog_capture.py`: phần lớn test dưới đây
kết thúc bằng `load_tracking_inv_map_capture()` hoặc `ProductIdentityResolver`
thật, không phải một assertion trên dict do chính test dựng.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.modules.pricing.resolution.sources import (
    InvalidTrackingInvMapCaptureFileError,
    load_tracking_inv_map_capture,
)
from app.modules.product.identity.tracking_catalog import (
    CaptureStatus,
    TrackingCaptureFailedError,
)
from app.modules.product.identity.tracking_inv_map import inv_map_key, norm_code
from tools.tracking.capture_inv_map import (
    EMPTY_SOURCE_NOT_ASSERTABLE,
    MALFORMED_SOURCE,
    SOURCE_UNAVAILABLE,
    build_capture,
    write_capture,
)
from tools.tracking.capture_purchase_price_history import CaptureError, INV_MAP_NODE

MOMENT = datetime(2026, 9, 1, 3, 0, tzinfo=timezone.utc)

RAW_PAYLOAD = {
    "map": {
        "N_MYGITSAMSUNGWW10DB7U34GBSV": "WW10DB7U34GB",
        "N_CHIPHVNCHUYN": "-",
    }
}


def fetcher(payload=RAW_PAYLOAD):
    def fetch(node):
        if node == INV_MAP_NODE:
            return payload
        raise AssertionError(f"công cụ không được đọc nhánh {node!r}")

    return fetch


def capture(fetch=None, **kw):
    return build_capture(
        fetch or fetcher(),
        capture_id=kw.pop("capture_id", "INVMAP-20260901T030000Z-deadbeef"),
        captured_by=kw.pop("captured_by", "operator@tinphat"),
        source_system_ref=kw.pop("source_system_ref", "tracking/api/xuat"),
        captured_at=kw.pop("captured_at", MOMENT),
        **kw,
    )


# ======================================================================
# normCode() / inv_map_key() — port nguyên văn
# ======================================================================


def test_norm_code_strips_everything_outside_ascii_alnum_after_uppercasing():
    assert norm_code("Máy giặt Samsung WW10DB7U34GBSV") == "MYGITSAMSUNGWW10DB7U34GBSV"
    assert norm_code("Chi phí vận chuyển") == "CHIPHVNCHUYN"


def test_inv_map_key_adds_prefix_and_truncates_at_80():
    long_desc = "A" * 200
    key = inv_map_key(long_desc)
    assert key.startswith("N_")
    assert len(key) == len("N_") + 80


# ======================================================================
# 1. Capture hợp lệ + hợp đồng
# ======================================================================


def test_a_valid_capture_matches_the_frozen_contract():
    envelope = capture()
    assert envelope["capture_status"] == "COMPLETE"
    assert set(envelope) == {
        "capture_id",
        "captured_at",
        "captured_by",
        "source_system_ref",
        "content_hash",
        "capture_status",
        "entries",
    }
    assert envelope["entries"] == RAW_PAYLOAD["map"]
    assert envelope["content_hash"].startswith("sha256:")


def test_the_tool_only_reads_the_inv_map_node():
    asked: list[str] = []

    def fetch(node):
        asked.append(node)
        return fetcher()(node)

    capture(fetch)
    assert asked == [INV_MAP_NODE]


def test_the_same_source_yields_the_same_content_hash_across_runs():
    a = capture(capture_id="INVMAP-A", captured_at=MOMENT)
    b = capture(
        capture_id="INVMAP-B",
        captured_at=datetime(2026, 12, 25, tzinfo=timezone.utc),
    )
    assert a["content_hash"] == b["content_hash"]
    assert a["entries"] == b["entries"]


# ======================================================================
# 2. Fail-safe / malformed
# ======================================================================


def test_a_network_or_auth_failure_is_source_unavailable_not_an_empty_map():
    def fetch(node):
        raise CaptureError("HTTP Error 401: Unauthorized")

    envelope = capture(fetch)
    assert envelope["capture_status"] == "FAILED"
    assert envelope["failure_reason"].startswith(SOURCE_UNAVAILABLE)
    assert "entries" not in envelope


@pytest.mark.parametrize("payload", [None, {}])
def test_an_empty_payload_is_refused_not_recorded_as_an_empty_map(payload):
    envelope = capture(fetcher(payload))
    assert envelope["capture_status"] == "FAILED"
    assert envelope["failure_reason"].startswith(EMPTY_SOURCE_NOT_ASSERTABLE)


@pytest.mark.parametrize(
    "payload",
    [
        {"map": {}},
        ["not", "a", "map"],
        {"map": "không phải một ánh xạ"},
        {"map": {"N_X": ""}},
        {"map": {"N_X": 7}},
        {"map": {"": "CODE1"}},
        {"map": {"N_X": "CODE1"}, "meta": "extra top-level key"},
        {"unexpected_key": {}},
    ],
)
def test_malformed_or_metadata_carrying_payload_fails_closed(payload):
    envelope = capture(fetcher(payload))
    assert envelope["capture_status"] == "FAILED"
    assert envelope["failure_reason"].startswith(
        (MALFORMED_SOURCE, EMPTY_SOURCE_NOT_ASSERTABLE)
    )


def test_a_failed_capture_still_satisfies_the_loader_required_fields(tmp_path):
    def fetch(node):
        raise CaptureError("mất mạng giữa chừng")

    path = write_capture(capture(fetch), tmp_path / "failed.json")
    snapshot = load_tracking_inv_map_capture(path)
    assert snapshot.capture_status is CaptureStatus.FAILED
    assert snapshot.failure_reason.startswith(SOURCE_UNAVAILABLE)
    with pytest.raises(TrackingCaptureFailedError):
        snapshot.require_complete()


def test_loader_rejects_a_capture_whose_content_hash_was_tampered_with(tmp_path):
    path = write_capture(capture(), tmp_path / "capture.json")
    tampered = path.read_text(encoding="utf-8").replace(
        "WW10DB7U34GB", "SOMETHING-ELSE"
    )
    path.write_text(tampered, encoding="utf-8")
    with pytest.raises(InvalidTrackingInvMapCaptureFileError):
        load_tracking_inv_map_capture(path)


def test_a_missing_capture_file_is_none_not_an_error(tmp_path):
    """`inv.map` là nguồn TUỲ CHỌN (DEC-165-style) — vắng mặt nghĩa là 'chưa
    capture lần nào', không phải lỗi tải."""
    assert load_tracking_inv_map_capture(tmp_path / "does-not-exist.json") is None


# ======================================================================
# 3. Không rò secret
# ======================================================================


def test_no_api_key_is_persisted_or_printed(tmp_path, monkeypatch, capsys):
    import tools.tracking.capture_inv_map as tool

    secret = "s3cr3t-report-key-value"
    monkeypatch.setenv("TRACKING_REPORT_API_KEY", secret)
    seen: list[str] = []

    def fake_http_fetcher(source_url, key):
        seen.append(key)
        return fetcher()

    monkeypatch.setattr(tool, "_http_fetcher", fake_http_fetcher)
    out = tmp_path / "capture.json"
    code = tool.main(
        [
            "--source-url", "https://tracking.example",
            "--captured-by", "operator@tinphat",
            "--out", str(out),
        ]
    )
    assert code == 0
    assert seen == [secret]
    assert secret not in out.read_text(encoding="utf-8")
    streams = capsys.readouterr()
    assert secret not in streams.out and secret not in streams.err


def test_the_cli_exits_non_zero_and_writes_a_failed_artifact_on_failure(
    tmp_path, monkeypatch, capsys
):
    import tools.tracking.capture_inv_map as tool

    def boom(source_url, key):
        def fetch(node):
            raise CaptureError("mất mạng")

        return fetch

    monkeypatch.setattr(tool, "_http_fetcher", boom)
    out = tmp_path / "capture.json"
    code = tool.main(
        [
            "--source-url", "https://tracking.example",
            "--captured-by", "operator@tinphat",
            "--out", str(out),
        ]
    )
    assert code == 1
    snapshot = load_tracking_inv_map_capture(out)
    assert snapshot.capture_status is CaptureStatus.FAILED
