"""Nạp một ảnh chụp `daily-min-v1` đã export ra file — biên ĐỌC FILE.

## Vì sao file, không phải mạng

`ADR-101` + `DEC-152` §6: phần chạm mạng nằm NGOÀI `app/modules/`
(`tools/tracking/capture_daily_min.py`). Module này chỉ đọc kết quả bất biến
của công cụ đó và **không biết hợp đồng HTTP tồn tại** — không URL, không
client, không import mạng (`CHECK-105D-17` quét cả `app/modules/**`).

## Ba trạng thái KHÁC NHAU, không được gộp

```text
file KHÔNG tồn tại   → None            → nguồn CHƯA ĐƯỢC NỐI (source unavailable)
capture_status FAILED → snapshot FAILED → LỖI khi ai đó dựng provider (INV-12)
file hỏng            → InvalidDailyMinCaptureFileError (LỖI NẠP)
```

Ba nhánh này là bản sao có chủ đích của `tracking_history/capture_file.py`, và
lý do giống hệt: "chưa ai capture lần nào" là trạng thái khởi đầu hợp lệ của
một hệ thống chưa bật nguồn, còn "đã capture và capture hỏng" là một sự cố.
Gộp lại thì một lần mất mạng trông y hệt một kết luận về dữ liệu.

## Hình dạng file

```json
{
  "capture_id": "...",
  "captured_at": "2026-09-30T12:00:00+00:00",
  "captured_by": "...",
  "source_system_ref": "tracking/api/min-ngay",
  "capture_status": "COMPLETE",
  "data": {
    "schema_version": "daily-min-v1",
    "business_timezone": "Asia/Ho_Chi_Minh",
    "currency_unit": "VND_THOUSAND",
    "date_from": "2026-09-01",
    "date_to": "2026-09-30",
    "records": [...],
    "errors": [...]
  }
}
```

`data` là phong bì hợp đồng ĐÃ GỘP TRANG: công cụ capture đọc hết các trang
rồi nối `records`/`errors` lại. Gộp ở công cụ chứ không ở đây, vì "đã đọc đủ
trang chưa" là một câu hỏi về lần gọi mạng, và module này không được biết có
mạng.
"""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any, Optional

from app.modules.pricing.daily_min.snapshot import (
    CaptureStatus,
    DailyMinSnapshot,
)

__all__ = [
    "InvalidDailyMinCaptureFileError",
    "load_daily_min_capture",
]


class InvalidDailyMinCaptureFileError(ValueError):
    """File capture tồn tại nhưng không đọc được thành một ảnh chụp hợp lệ.

    Cố ý là LỖI chứ không phải `None`: `None` nghĩa là "chưa có nguồn", và một
    file hỏng bị đọc thành "chưa có nguồn" sẽ biến toàn bộ nhánh giá thành
    Pending trong im lặng — không ai biết nguồn chưa từng được đọc.
    """

    def __init__(self, message: str, *, reason: str) -> None:
        super().__init__(message)
        self.reason = reason


def _require_text(payload: dict[str, Any], key: str, path: Path) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise InvalidDailyMinCaptureFileError(
            f"{path}: trường {key!r} REQUIRED và phải là chuỗi không rỗng.",
            reason=f"missing_{key}",
        )
    return value


def _require_datetime(payload: dict[str, Any], key: str, path: Path) -> _dt.datetime:
    raw = _require_text(payload, key, path)
    try:
        moment = _dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise InvalidDailyMinCaptureFileError(
            f"{path}: trường {key!r} không phải ISO-8601 hợp lệ ({raw!r}): {exc}.",
            reason="invalid_datetime",
        ) from exc
    if moment.tzinfo is None or moment.tzinfo.utcoffset(moment) is None:
        raise InvalidDailyMinCaptureFileError(
            f"{path}: trường {key!r} phải AWARE (có múi giờ); nhận naive {raw!r}.",
            reason="naive_datetime",
        )
    return moment


def load_daily_min_capture(path: Path) -> Optional[DailyMinSnapshot]:
    """Đọc file capture. File không tồn tại → `None` (nguồn chưa được nối).

    Mọi hư hỏng khác đều raise — xem docstring module.
    """
    if not path.exists():
        return None

    try:
        raw_text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise InvalidDailyMinCaptureFileError(
            f"{path}: không đọc được file capture: {exc}.", reason="unreadable"
        ) from exc

    try:
        payload = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise InvalidDailyMinCaptureFileError(
            f"{path}: không phải JSON hợp lệ: {exc}.", reason="invalid_json"
        ) from exc

    if not isinstance(payload, dict):
        raise InvalidDailyMinCaptureFileError(
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
        raise InvalidDailyMinCaptureFileError(
            f"{path}: capture_status={raw_status!r} ngoài enum đóng "
            f"{[s.value for s in CaptureStatus]}.",
            reason="invalid_capture_status",
        ) from exc

    if capture_status is CaptureStatus.FAILED:
        # KHÔNG nuốt thành `None`. Snapshot FAILED được dựng đầy đủ để
        # `require_complete()` nổ đúng chỗ và đúng lý do (`INV-12`).
        return DailyMinSnapshot.from_contract(
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
        raise InvalidDailyMinCaptureFileError(
            f"{path}: thiếu khối 'data' (phong bì hợp đồng đã gộp trang) hoặc "
            "nó không phải một ánh xạ — bỏ qua trong im lặng sẽ thành một ảnh "
            "chụp rỗng giả.",
            reason="missing_data_block",
        )

    return DailyMinSnapshot.from_contract(
        data,
        capture_id=capture_id,
        captured_at=captured_at,
        captured_by=captured_by,
        source_system_ref=source_system_ref,
        capture_status=capture_status,
    )
