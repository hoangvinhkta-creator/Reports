"""R5 §5 — `model_label`/`brand` đi từ Tracking tới màn hình nhân viên.

Hai mệnh đề, và cả hai đều là mệnh đề về việc KHÔNG làm gì:

1. Reports không SINH RA hãng hay model. Nó chỉ đọc hai trường mà Tracking
   đã chuẩn hoá. `PHB-06 §3`/`BR-02`/`BR-10` cấm bốn cách dựng một thẩm
   quyền thương hiệu thứ hai — bảng ánh xạ riêng, so chuỗi con, so gần đúng,
   và rút hãng từ tên hàng — và R5 không mở cái nào trong bốn.

2. Artifact CŨ (không có hai trường) vẫn đọc được. Một hợp đồng mở rộng mà
   làm hỏng những file đã ghi là một lần mất dữ liệu, không phải một lần
   nâng cấp.

Chiều thứ ba, và là chiều PHB-06 đã dành sẵn chỗ: ngày hợp đồng danh tính
có thương hiệu, `brand_identity` phải mở ra mà không cần một bảng brand nào
của riêng Reports.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from app.modules.pricing.resolution.sources import (
    InvalidTrackingCatalogCaptureFileError, load_tracking_catalog_capture,
)
from app.modules.product.identity.tracking_catalog import (
    CaptureStatus, TrackingCatalogRow, TrackingCatalogSnapshot,
    canonical_content_hash,
)
from tools.tracking import capture_tracking_catalog as capture


def write_capture(path: Path, rows: list[dict], alias: dict | None = None) -> Path:
    alias = alias or {}
    payload = {
        "capture_id": "cap-1",
        "captured_at": "2026-09-08T00:00:00+00:00",
        "captured_by": "test",
        "source_system_ref": "tracking",
        "capture_status": "COMPLETE",
        "content_hash": canonical_content_hash(rows, alias),
        "rows": rows,
        "alias_map": alias,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


# --- 1. Capture đọc được hợp đồng MỚI --------------------------------------

def test_the_capture_carries_the_two_new_fields_when_tracking_sends_them():
    rows = capture._rows_from_board({
        "65S20M2": {"name": "Tivi Sony K-65S20M2", "alt": ["KD65S20"],
                    "model_label": "K-65S20M2", "brand": "Sony"},
    })
    assert rows == [{
        "tracking_code": "65S20M2", "present_in_board": True,
        "name": "Tivi Sony K-65S20M2", "alt": ["KD65S20"],
        "model_label": "K-65S20M2", "brand": "Sony",
    }]


def test_a_null_from_tracking_is_kept_out_of_the_row_entirely():
    """`null` nghĩa là Tracking KHÔNG khẳng định — không ghi một khoá rỗng.

    Một khoá mang `None` và một khoá vắng mặt đọc lên đều thành "chưa xác
    định", nhưng khoá vắng mặt còn giữ được điều thứ hai: hash của một dòng
    Tracking không biết hãng bằng đúng hash của cùng dòng đó ở hợp đồng cũ.
    """
    rows = capture._rows_from_board({
        "X": {"name": "Hàng lạ", "model_label": None, "brand": None},
    })
    assert rows == [{"tracking_code": "X", "present_in_board": True,
                     "name": "Hàng lạ"}]


def test_a_wrong_type_from_tracking_is_a_malformed_source_not_a_guess():
    with pytest.raises(capture.MalformedSourceError):
        capture._rows_from_board({"X": {"name": "A", "brand": 7}})
    with pytest.raises(capture.MalformedSourceError):
        capture._rows_from_board({"X": {"name": "A", "model_label": ["a"]}})


def test_the_content_hash_covers_the_two_new_fields():
    """Đổi hãng mà hash không đổi là một lần đổi danh mục không dấu vết."""
    without = capture._rows_from_board({"X": {"name": "A"}})
    with_brand = capture._rows_from_board({"X": {"name": "A", "brand": "Sony"}})
    assert canonical_content_hash(without, {}) != canonical_content_hash(
        with_brand, {})


# --- 2. Loader đọc được CẢ hợp đồng cũ lẫn mới ---------------------------

def test_an_old_artifact_without_the_fields_still_loads(tmp_path):
    path = write_capture(tmp_path / "cap.json", [
        {"tracking_code": "X", "present_in_board": True, "name": "Hàng cũ"},
    ])
    snapshot = load_tracking_catalog_capture(path)
    row = snapshot.row_for("X")
    assert row.name == "Hàng cũ"
    assert row.model_label is None
    assert row.brand is None


def test_a_new_artifact_loads_both_fields(tmp_path):
    path = write_capture(tmp_path / "cap.json", [
        {"tracking_code": "65S20M2", "present_in_board": True,
         "name": "Tivi Sony K-65S20M2", "model_label": "K-65S20M2",
         "brand": "Sony"},
    ])
    row = load_tracking_catalog_capture(path).row_for("65S20M2")
    assert (row.model_label, row.brand) == ("K-65S20M2", "Sony")


def test_a_wrong_type_in_the_artifact_is_refused_not_coerced(tmp_path):
    path = write_capture(tmp_path / "cap.json", [
        {"tracking_code": "X", "present_in_board": True, "brand": 7},
    ])
    with pytest.raises(InvalidTrackingCatalogCaptureFileError):
        load_tracking_catalog_capture(path)


# --- 3. Hai trường mới KHÔNG tham gia nhận diện --------------------------

def test_identity_matching_never_reads_brand_or_model(tmp_path):
    """`INV-13`/`INV-21` — chỉ mã, tên và alt được ghép EXACT.

    Ghép thêm bằng hãng sẽ làm mọi dòng Sony khớp với nhau, và một mapping
    đã confirm có thể bị dời sang một mặt hàng khác cùng hãng.
    """
    snapshot = TrackingCatalogSnapshot(
        capture_id="c", captured_at=datetime(2026, 9, 8),
        captured_by="t", source_system_ref="s", content_hash="h",
        capture_status=CaptureStatus.COMPLETE,
        rows=(TrackingCatalogRow(
            tracking_code="65S20M2", present_in_board=True,
            name="Tivi Sony K-65S20M2", model_label="K-65S20M2", brand="Sony"),))
    assert snapshot.exact_match_codes(raw_key="Sony", aid="sony") == ()
    assert snapshot.exact_match_codes(raw_key="K-65S20M2", aid="k-65s20m2") == ()
    assert snapshot.exact_match_codes(
        raw_key="Tivi Sony K-65S20M2", aid="tivi sony k-65s20m2") == (
            ("65S20M2", "TRACKING_NAME"),)
