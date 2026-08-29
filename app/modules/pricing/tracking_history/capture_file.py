"""Nạp một ảnh chụp `purchase_price_*` đã export ra file — biên ĐỌC FILE.

## Vì sao file, không phải mạng

`ADR-101` + `DEC-152` §6: phần chạm RTDB nằm NGOÀI `app/modules/`
(`tools/tracking/capture_purchase_price_history.py`). Module này chỉ đọc kết
quả bất biến của công cụ đó và **không biết RTDB tồn tại** — không URL, không
client, không import mạng (`CHECK-105D-17` quét cả `app/modules/**`).

## Ba trạng thái KHÁC NHAU, không được gộp

```text
file KHÔNG tồn tại   → None            → nguồn CHƯA ĐƯỢC NỐI (source unavailable)
capture_status FAILED → snapshot FAILED → LỖI khi ai đó dựng reader (INV-12)
file hỏng            → InvalidTrackingPriceCaptureFileError (LỖI NẠP)
```

`None` và `FAILED` không được trộn: "chưa ai capture lần nào" là trạng thái
khởi đầu hợp lệ của một hệ thống chưa bật nguồn, còn "đã capture và capture
hỏng" là một sự cố. Nếu gộp chúng lại thì một lần mất mạng trông y hệt một
kết luận về dữ liệu — đúng cái lỗi `INV-12` sinh ra để chặn.

File hỏng cũng KHÔNG được rơi về `None`: một `capture_id` gõ sai sẽ lặng lẽ
biến toàn bộ nhánh TRACKING thành Pending và không ai biết nguồn chưa từng
được đọc.

## Hình dạng file

```json
{
  "capture_id": "...",              // do công cụ capture cấp, KHÔNG suy từ nội dung
  "captured_at": "2026-08-29T19:40:00+00:00",
  "captured_by": "...",
  "source_system_ref": "...",
  "capture_status": "COMPLETE",     // hoặc "FAILED" + "failure_reason"
  "data": {                          // đúng hình dạng cây RTDB đã export
    "purchase_price_baseline": {"cutover": {...}},
    "purchase_price_history": {"<mã>": {"<eid>": {...}}}
  }
}
```

Provenance của chính lần capture đến TỪ công cụ capture, không suy ra từ nội
dung — nội dung không tự chứng minh được nó được chụp lúc nào
(`TrackingPriceHistorySnapshot.from_export`).
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from app.modules.pricing.tracking_history.snapshot import (
    CaptureStatus,
    TrackingPriceHistorySnapshot,
)

__all__ = [
    "InvalidTrackingPriceCaptureFileError",
    "load_tracking_price_history_capture",
]


class InvalidTrackingPriceCaptureFileError(ValueError):
    """File capture tồn tại nhưng không đọc được thành một ảnh chụp hợp lệ.

    Cố ý là LỖI chứ không phải `None`: `None` nghĩa là "chưa có nguồn", và một
    file hỏng bị đọc thành "chưa có nguồn" sẽ biến một sự cố cấu hình thành
    một kết luận nghiệp vụ im lặng.
    """

    def __init__(self, message: str, *, reason: str) -> None:
        super().__init__(message)
        self.reason = reason


def _require_text(payload: dict[str, Any], key: str, path: Path) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise InvalidTrackingPriceCaptureFileError(
            f"{path}: trường {key!r} REQUIRED và phải là chuỗi không rỗng.",
            reason=f"missing_{key}",
        )
    return value


def _require_datetime(payload: dict[str, Any], key: str, path: Path) -> datetime:
    raw = _require_text(payload, key, path)
    try:
        moment = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise InvalidTrackingPriceCaptureFileError(
            f"{path}: trường {key!r} không phải ISO-8601 hợp lệ ({raw!r}): {exc}.",
            reason="invalid_datetime",
        ) from exc
    if moment.tzinfo is None or moment.tzinfo.utcoffset(moment) is None:
        raise InvalidTrackingPriceCaptureFileError(
            f"{path}: trường {key!r} phải AWARE (có múi giờ); nhận naive {raw!r}. "
            "Một mốc capture không múi giờ không so được với mốc cutover UTC.",
            reason="naive_datetime",
        )
    return moment


def load_tracking_price_history_capture(
    path: Path,
) -> Optional[TrackingPriceHistorySnapshot]:
    """Đọc file capture. File không tồn tại → `None` (nguồn chưa được nối).

    Mọi hư hỏng khác đều raise: xem docstring module.
    """
    if not path.exists():
        return None

    try:
        raw_text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise InvalidTrackingPriceCaptureFileError(
            f"{path}: không đọc được file capture: {exc}.", reason="unreadable"
        ) from exc

    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise InvalidTrackingPriceCaptureFileError(
            f"{path}: không phải JSON hợp lệ: {exc}.", reason="invalid_json"
        ) from exc

    if not isinstance(payload, dict):
        raise InvalidTrackingPriceCaptureFileError(
            f"{path}: nội dung phải là một ánh xạ khoá-giá trị.",
            reason="not_a_mapping",
        )

    capture_id = _require_text(payload, "capture_id", path)
    captured_at = _require_datetime(payload, "captured_at", path)
    captured_by = _require_text(payload, "captured_by", path)
    source_system_ref = _require_text(payload, "source_system_ref", path)

    raw_status = payload.get("capture_status")
    try:
        capture_status = CaptureStatus(raw_status)
    except ValueError as exc:
        raise InvalidTrackingPriceCaptureFileError(
            f"{path}: capture_status={raw_status!r} ngoài enum đóng "
            f"{[s.value for s in CaptureStatus]}.",
            reason="invalid_capture_status",
        ) from exc

    if capture_status is CaptureStatus.FAILED:
        # KHÔNG nuốt thành `None`. Snapshot FAILED được dựng đầy đủ để
        # `require_complete()` nổ đúng chỗ và đúng lý do (`INV-12`).
        return TrackingPriceHistorySnapshot.from_export(
            {},
            capture_id=capture_id,
            captured_at=captured_at,
            captured_by=captured_by,
            source_system_ref=source_system_ref,
            capture_status=capture_status,
            failure_reason=payload.get("failure_reason") or "không ghi lý do",
        )

    data = payload.get("data")
    if not isinstance(data, dict):
        raise InvalidTrackingPriceCaptureFileError(
            f"{path}: thiếu khối 'data' (cây RTDB đã export) hoặc nó không phải "
            "một ánh xạ — bỏ qua trong im lặng sẽ thành một danh mục rỗng giả.",
            reason="missing_data_block",
        )

    return TrackingPriceHistorySnapshot.from_export(
        data,
        capture_id=capture_id,
        captured_at=captured_at,
        captured_by=captured_by,
        source_system_ref=source_system_ref,
        capture_status=capture_status,
    )
