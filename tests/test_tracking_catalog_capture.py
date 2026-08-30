"""`tools/tracking/capture_tracking_catalog.py` — biên thu thập danh mục.

Bộ test này chấm đúng một câu hỏi: **file mà công cụ ghi ra có đi thẳng vào
production loader và production resolver được không** — chứ không phải "công
cụ có chạy không". Vì thế phần lớn test dưới đây kết thúc bằng một lời gọi
`load_tracking_catalog_capture()` hoặc `ProductIdentityResolver` thật, không
phải bằng một assertion trên dict do chính test dựng.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from app.modules.pricing.resolution.sources import (
    InvalidTrackingCatalogCaptureFileError,
    load_tracking_catalog_capture,
)
from app.modules.product.identity.identity import Namespace, Resolved
from app.modules.product.identity.keys import (
    normalized_matching_aid,
    raw_identity_key,
)
from app.modules.product.identity.resolver import DistinctIdentity
from app.modules.product.identity.tracking_catalog import (
    CaptureStatus,
    TrackingCaptureFailedError,
)
from tests.support import identity_fixtures as fx
from tools.tracking.capture_purchase_price_history import CaptureError
from tools.tracking.capture_tracking_catalog import (
    ALIAS_NODE,
    BOARD_NODE,
    EMPTY_SOURCE_NOT_ASSERTABLE,
    MALFORMED_SOURCE,
    SOURCE_UNAVAILABLE,
    build_capture,
    write_capture,
)

MOMENT = datetime(2026, 9, 1, 3, 0, tzinfo=timezone.utc)

# Một nhánh `board` như nó thật sự về từ RTDB: khoá đã `normCode`, kèm ĐẦY ĐỦ
# các nhánh giá riêng tư mà `DEC-147` §2 mô tả (`p` = giá NCC báo, `tp.ton` =
# giá nhập công khai, `tp.chot` = giá bán nội bộ, `_c` = min/đề xuất).
BOARD = {
    "T2109NT1G": {
        "name": "T2109NT1G",
        "alt": ["T2109NT1G-DG"],
        "p": {"NCC1": {"v": 4100}},
        "tp": {"ton": 4050, "chot": 4300},
        "_c": {"min": 4050, "dx": 4600},
    },
    "SJX198VDG": {
        "name": "SJ-X198V-DG",
        "p": {"NCC2": {"v": 7700}},
        "tp": {"ton": 7650},
    },
    "OLDCODE9": {"name": "OLDCODE9"},
}
ALIAS = {"map": {"OLDCODE9": "SJX198VDG"}}

PRIVATE_MARKERS = ("4100", "4050", "4300", "4600", "7700", "7650")


def fetcher(board=BOARD, alias=ALIAS):
    def fetch(node):
        if node == BOARD_NODE:
            return board
        if node == ALIAS_NODE:
            return alias
        raise AssertionError(f"công cụ không được đọc nhánh {node!r}")

    return fetch


def capture(fetch=None, **kw):
    return build_capture(
        fetch or fetcher(),
        capture_id=kw.pop("capture_id", "TRK-20260901T030000Z-deadbeef"),
        captured_by=kw.pop("captured_by", "operator@tinphat"),
        source_system_ref=kw.pop("source_system_ref", "tracking/rtdb"),
        captured_at=kw.pop("captured_at", MOMENT),
        **kw,
    )


# ======================================================================
# 1. Capture hợp lệ + hợp đồng §4.4
# ======================================================================


def test_a_valid_capture_matches_the_frozen_source_contract():
    envelope = capture()
    assert envelope["capture_status"] == "COMPLETE"
    assert set(envelope) == {
        "capture_id",
        "captured_at",
        "captured_by",
        "source_system_ref",
        "content_hash",
        "capture_status",
        "rows",
        "alias_map",
    }
    # Thứ tự dòng ổn định theo `tracking_code` — `INV-64` không được phụ thuộc
    # thứ tự khoá của một dict JSON.
    assert [r["tracking_code"] for r in envelope["rows"]] == [
        "OLDCODE9",
        "SJX198VDG",
        "T2109NT1G",
    ]
    row = envelope["rows"][2]
    assert row == {
        "tracking_code": "T2109NT1G",
        "present_in_board": True,
        "name": "T2109NT1G",
        "alt": ["T2109NT1G-DG"],
    }
    assert envelope["alias_map"] == {"OLDCODE9": "SJX198VDG"}
    assert envelope["content_hash"].startswith("sha256:")


def test_present_in_board_is_an_explicit_bool_on_every_row():
    """Loader từ chối một dòng thiếu `present_in_board` — vắng mặt KHÔNG được
    đọc thành `True`. Producer vì thế phải ghi nó tường minh."""
    for row in capture()["rows"]:
        assert row["present_in_board"] is True


# ======================================================================
# 2. Xác định (deterministic)
# ======================================================================


def test_the_same_source_yields_the_same_content_hash_across_runs():
    a = capture(capture_id="TRK-A", captured_at=MOMENT)
    b = capture(
        capture_id="TRK-B",
        captured_at=datetime(2026, 12, 25, tzinfo=timezone.utc),
    )
    # Hash trả lời "nguồn có đổi không", không phải "đã chạy lại chưa".
    assert a["content_hash"] == b["content_hash"]
    assert a["rows"] == b["rows"] and a["alias_map"] == b["alias_map"]


def test_key_order_of_the_rtdb_payload_does_not_change_the_capture():
    shuffled = {k: BOARD[k] for k in ("SJX198VDG", "OLDCODE9", "T2109NT1G")}
    assert capture(fetcher(board=shuffled)) == capture()


def test_a_changed_source_changes_the_content_hash():
    changed = dict(BOARD)
    changed["NEWCODE1"] = {"name": "NEWCODE1"}
    assert capture(fetcher(board=changed))["content_hash"] != capture()["content_hash"]


# ======================================================================
# 3. Bốn kết cục — và ba loại "không COMPLETE" không được gộp
# ======================================================================


def test_a_network_or_auth_failure_is_source_unavailable_not_an_empty_catalog():
    def fetch(node):
        raise CaptureError("HTTP Error 401: Unauthorized")

    envelope = capture(fetch)
    assert envelope["capture_status"] == "FAILED"
    assert envelope["failure_reason"].startswith(SOURCE_UNAVAILABLE)
    assert "rows" not in envelope and "alias_map" not in envelope


def test_an_empty_board_is_refused_not_recorded_as_an_empty_catalog():
    """`§7` — "danh mục rỗng" và "không với tới được nguồn" không đồng nghĩa,
    và RTDB không cho phép khẳng định cái thứ nhất: `null` phục vụ cả hai."""
    for empty in (None, {}):
        envelope = capture(fetcher(board=empty))
        assert envelope["capture_status"] == "FAILED"
        assert envelope["failure_reason"].startswith(EMPTY_SOURCE_NOT_ASSERTABLE)
        assert envelope["failure_reason"] != SOURCE_UNAVAILABLE


def test_the_three_failure_vocabularies_are_distinguishable_from_each_other():
    def unavailable(node):
        raise CaptureError("mất mạng")

    reasons = {
        capture(unavailable)["failure_reason"].split(":")[0],
        capture(fetcher(board={}))["failure_reason"].split(":")[0],
        capture(fetcher(board=["not", "a", "map"]))["failure_reason"].split(":")[0],
    }
    assert reasons == {SOURCE_UNAVAILABLE, EMPTY_SOURCE_NOT_ASSERTABLE, MALFORMED_SOURCE}


@pytest.mark.parametrize(
    "board",
    [
        ["not", "a", "map"],
        {"CODE1": "không phải một ánh xạ"},
        {"CODE1": {"name": 12345}},
        {"CODE1": {"alt": "không phải danh sách"}},
        {"CODE1": {"alt": [1, 2]}},
        {"": {"name": "khoá rỗng"}},
    ],
)
def test_a_malformed_board_fails_closed(board):
    envelope = capture(fetcher(board=board))
    assert envelope["capture_status"] == "FAILED"
    assert envelope["failure_reason"].startswith(MALFORMED_SOURCE)


@pytest.mark.parametrize(
    "alias",
    [
        "không phải một ánh xạ",
        {"không có khoá map": {}},
        {"map": "không phải một ánh xạ"},
        {"map": {"OLD": ""}},
        {"map": {"OLD": 7}},
    ],
)
def test_a_malformed_alias_branch_fails_closed(alias):
    envelope = capture(fetcher(alias=alias))
    assert envelope["capture_status"] == "FAILED"
    assert envelope["failure_reason"].startswith(MALFORMED_SOURCE)


def test_an_absent_alias_branch_is_a_legitimate_empty_alias_map():
    """Ngược chiều với `board`: "chưa mã nào bị gộp" là trạng thái khởi đầu
    ĐÚNG, và `alias_map` là evidence phụ trợ chứ không phải danh mục."""
    envelope = capture(fetcher(alias=None))
    assert envelope["capture_status"] == "COMPLETE"
    assert envelope["alias_map"] == {}


def test_a_failed_capture_still_satisfies_the_loader_required_fields(tmp_path):
    """`load_tracking_catalog_capture()` đọc `content_hash` TRƯỚC khi rẽ nhánh
    FAILED — một envelope FAILED thiếu nó sẽ là file hỏng, không phải một lần
    capture thất bại đọc lại được."""

    def fetch(node):
        raise CaptureError("mất mạng giữa chừng")

    path = write_capture(capture(fetch), tmp_path / "failed.json")
    snapshot = load_tracking_catalog_capture(path)
    assert snapshot.capture_status is CaptureStatus.FAILED
    assert snapshot.failure_reason.startswith(SOURCE_UNAVAILABLE)
    with pytest.raises(TrackingCaptureFailedError):
        snapshot.require_complete()


# ======================================================================
# 4. Không rò trường riêng tư / secret
# ======================================================================


def test_the_capture_never_persists_private_pricing_fields(tmp_path):
    """`inv.gia`, `board/<mã>/p`, `tp.ton`, `_c` là giá — không có chỗ trong
    `TrackingCatalogSnapshot` và không được đi vào artifact."""
    path = write_capture(capture(), tmp_path / "capture.json")
    text = path.read_text(encoding="utf-8")
    for forbidden in ("\"p\"", "\"tp\"", "\"_c\"", "ton", "chot", "gia", "min", "dx"):
        assert forbidden not in text, forbidden
    for marker in PRIVATE_MARKERS:
        assert marker not in text, marker


def test_the_capture_never_reads_a_branch_that_holds_accounting_prices():
    """`inv`/`phist`/`backup` không được hỏi tới — fetcher của test nổ nếu có."""
    asked: list[str] = []

    def fetch(node):
        asked.append(node)
        return fetcher()(node)

    capture(fetch)
    assert asked == [BOARD_NODE, ALIAS_NODE]


def test_no_api_key_is_persisted_or_printed(tmp_path, monkeypatch, capsys):
    """Chạy CẢ đường CLI với một secret thật trong môi trường — secret phải đi
    tới client hợp đồng và dừng ở đó, không vào artifact, không ra stdout/stderr."""
    import tools.tracking.capture_tracking_catalog as tool

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
    assert seen == [secret]  # credential ĐI qua biến môi trường, đúng đường
    assert secret not in out.read_text(encoding="utf-8")
    streams = capsys.readouterr()
    assert secret not in streams.out and secret not in streams.err


def test_the_cli_exits_non_zero_and_writes_a_failed_artifact_on_failure(
    tmp_path, monkeypatch, capsys
):
    """Fail closed: exit code khác 0, và vẫn có một file FAILED đọc lại được —
    không phải một file rỗng, cũng không phải không có file nào."""
    import tools.tracking.capture_tracking_catalog as tool

    def boom(source_url, key):
        def fetch(node):
            raise CaptureError("HTTP Error 401: Unauthorized")

        return fetch

    monkeypatch.setattr(tool, "_http_fetcher", boom)
    out = tmp_path / "capture.json"
    assert tool.main(
        ["--source-url", "https://x", "--captured-by", "op", "--out", str(out)]
    ) == 1
    assert load_tracking_catalog_capture(out).capture_status is CaptureStatus.FAILED
    assert SOURCE_UNAVAILABLE in capsys.readouterr().err


def test_the_tool_never_embeds_a_credential_or_a_source_url():
    source = Path("tools/tracking/capture_tracking_catalog.py").read_text("utf-8")
    for leak in ("firebaseio.com", "firebasedatabase.app", "auth=", "Bearer "):
        assert leak not in source, leak


# ======================================================================
# 5. Read-only — là tính chất của MÃ
# ======================================================================


def test_the_catalog_capture_tool_has_no_write_surface_to_tracking():
    source = Path("tools/tracking/capture_tracking_catalog.py").read_text("utf-8")
    for verb in ('method="PUT"', 'method="POST"', 'method="PATCH"',
                 'method="DELETE"', ".set(", ".update(", ".remove(", "urlopen"):
        assert verb not in source, verb
    # Đường mạng DUY NHẤT là fetcher đã review của công cụ chị em — không có
    # một client thứ hai nào được dựng trong file này.
    assert "_http_fetcher" in source


def test_a_capture_file_is_never_overwritten(tmp_path):
    path = write_capture(capture(), tmp_path / "once.json")
    with pytest.raises(CaptureError, match="BẤT BIẾN"):
        write_capture(capture(), path)


# ======================================================================
# 6. Mã trùng / mã bị gộp — theo hợp đồng, không tự quyết
# ======================================================================


def test_an_aliased_old_code_stays_a_row_and_an_alias_entry_at_once():
    """`INV-16` — công cụ KHÔNG áp `aliasOf()` để gộp dòng. Gộp sẵn ở tầng
    capture sẽ xoá tín hiệu mà resolver cần để sinh `MAPPING_STALE`."""
    envelope = capture()
    codes = [r["tracking_code"] for r in envelope["rows"]]
    assert "OLDCODE9" in codes and "SJX198VDG" in codes
    assert envelope["alias_map"]["OLDCODE9"] == "SJX198VDG"


def test_alias_entries_are_sorted_so_the_map_is_reproducible():
    alias = {"map": {"ZOLD": "AAA", "AOLD": "BBB"}}
    assert list(capture(fetcher(alias=alias))["alias_map"]) == ["AOLD", "ZOLD"]


# ======================================================================
# 7. Loader + resolver production nuốt được artifact
# ======================================================================


def test_the_production_loader_accepts_the_produced_artifact(tmp_path):
    path = write_capture(capture(), tmp_path / "capture.json")
    snapshot = load_tracking_catalog_capture(path)
    snapshot.require_complete()
    assert snapshot.capture_id == "TRK-20260901T030000Z-deadbeef"
    assert snapshot.captured_at == MOMENT
    assert snapshot.row_for("T2109NT1G").alt == ("T2109NT1G-DG",)
    assert snapshot.alias_map() == {"OLDCODE9": "SJX198VDG"}
    # Không dòng nào mang một trường ngoài hợp đồng.
    assert snapshot.row_for("SJX198VDG").name == "SJ-X198V-DG"


def test_the_production_loader_detects_mutation_after_capture_write(tmp_path):
    """`content_hash` SHA-256 của tool không chỉ là metadata trang trí."""
    path = write_capture(capture(), tmp_path / "capture.json")
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["rows"][0]["name"] = "đã bị sửa"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    with pytest.raises(InvalidTrackingCatalogCaptureFileError) as error:
        load_tracking_catalog_capture(path)
    assert error.value.reason == "content_hash_mismatch"


def test_the_production_resolver_consumes_the_produced_snapshot(tmp_path):
    """Từ file capture tới một `Resolved` thật — không fixture trung gian."""
    path = write_capture(capture(), tmp_path / "capture.json")
    snapshot = load_tracking_catalog_capture(path)
    resolver = fx.resolver(fx.store(tmp_path), snapshot=snapshot)
    raw = "T2109NT1G"
    outcome = resolver.resolve(
        DistinctIdentity(
            source_system="REPORTS_SALES",
            raw_identity_key=raw_identity_key(raw),
            raw_product_identity=raw,
            normalized_matching_aid=normalized_matching_aid(raw),
        )
    ).outcome
    assert isinstance(outcome, Resolved)
    assert outcome.identity.namespace is Namespace.TRACKING
    assert str(outcome.identity) == "TRACKING:T2109NT1G"


def test_a_failed_capture_stops_the_resolver_instead_of_emptying_the_catalog(tmp_path):
    """`INV-12` end-to-end: capture hỏng → resolver TỪ CHỐI chạy, chứ không
    trả "sản phẩm không tồn tại" cho mọi mã trên đời."""

    def fetch(node):
        raise CaptureError("mất mạng")

    path = write_capture(capture(fetch), tmp_path / "failed.json")
    with pytest.raises(TrackingCaptureFailedError):
        fx.resolver(fx.store(tmp_path), snapshot=load_tracking_catalog_capture(path))


def test_an_absent_capture_file_is_still_none_not_an_empty_snapshot(tmp_path):
    assert load_tracking_catalog_capture(tmp_path / "chưa-capture.json") is None
