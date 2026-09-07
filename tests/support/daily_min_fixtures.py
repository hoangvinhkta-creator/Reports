"""Fixture tổng hợp cho hợp đồng `daily-min-v1` (R1 — MIN theo ngày bán).

Toàn bộ dữ liệu ở đây là **tổng hợp**: không mã sản phẩm production, không dữ
liệu kế toán thật, không bí mật Tracking, không credential.

Mọi bài kiểm đi qua ĐÚNG các loader production (`load_daily_min_capture` →
`DailyMinSnapshot.from_contract`), không dựng thẳng dataclass: một fixture đi
đường tắt sẽ xanh trên một hình dạng dữ liệu mà production không bao giờ nhận
được, và khi ấy bài kiểm không còn nói gì về production nữa.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Optional, Sequence

CAPTURE_ID = "DMIN-20260930T120000Z-aaaabbbb"
CAPTURED_BY = "reports-capture-tool"
SOURCE_SYSTEM_REF = "tracking/api/min-ngay"
SCHEMA = "daily-min-v1"
CURRENCY = "VND_THOUSAND"
BUSINESS_TZ = "Asia/Ho_Chi_Minh"

RECORDED_AT = "2026-09-05T04:00:00+00:00"


def supplier(source_id: str) -> dict[str, str]:
    return {"source_type": "SUPPLIER", "source_id": source_id}


def inventory() -> dict[str, str]:
    """Ô Tồn Tín Phát — mã nguồn cố định của hợp đồng, không phải tên một NCC."""
    return {"source_type": "INVENTORY", "source_id": "TON_KHO"}


def record(
    product_code: str,
    effective_date: date | str,
    *,
    min_price: Optional[float] = None,
    price_status: str = "AVAILABLE",
    day_status: str = "FINAL",
    min_sources: Optional[Sequence[dict]] = None,
    observed_on: Optional[date | str] = None,
    carried_from: Optional[date | str] = None,
    rule_version: str = "min-1",
    source_fingerprint: str = "0123456789abcdef",
    revision: Optional[str] = None,
    recorded_at: Optional[str] = RECORDED_AT,
    recorded_by: str = "cron",
    excluded_sources: Optional[Sequence[dict]] = None,
    correction_of: Optional[str] = None,
    correction_reason: str = "",
) -> dict[str, Any]:
    """Một bản ghi hợp đồng, mặc định là một ngày ĐÃ CHỐT và CÓ giá.

    `min_sources` mặc định đúng một nhà cung cấp khi trạng thái là
    `AVAILABLE`, và RỖNG ở hai trạng thái còn lại — bất biến ấy được
    `DailyMinRecord.__post_init__` ép, nên một fixture vi phạm nó sẽ nổ ngay
    lúc nạp chứ không đi tiếp vào bài kiểm.
    """
    day = effective_date if isinstance(effective_date, str) else effective_date.isoformat()
    seen = observed_on if observed_on is not None else day
    seen = seen if isinstance(seen, str) else seen.isoformat()
    if min_sources is None:
        min_sources = [supplier("Tuấn Ngoan")] if price_status == "AVAILABLE" else []
    carried = carried_from
    if carried is not None and not isinstance(carried, str):
        carried = carried.isoformat()
    payload: dict[str, Any] = {
        "schema_version": SCHEMA,
        "product_code": product_code,
        "effective_date": day,
        "min_price": min_price,
        "currency_unit": CURRENCY,
        "min_sources": list(min_sources),
        "price_status": price_status,
        "day_status": day_status,
        "rule_version": rule_version,
        "source_fingerprint": source_fingerprint,
        "recorded_at": recorded_at,
        "recorded_by": recorded_by,
        "revision": revision or f"R-{day}-{source_fingerprint}",
        "observed_on": seen,
        "carried_from": carried,
    }
    if excluded_sources:
        payload["excluded_sources"] = list(excluded_sources)
    if correction_of:
        payload["correction_of"] = correction_of
        payload["correction_reason"] = correction_reason
    return payload


def error(product_code: str, effective_date: date | str, reason: str) -> dict[str, str]:
    day = effective_date if isinstance(effective_date, str) else effective_date.isoformat()
    return {"product_code": product_code, "effective_date": day, "reason": reason}


def contract(
    *,
    records: Sequence[dict] = (),
    errors: Sequence[dict] = (),
    date_from: date | str = "2026-09-01",
    date_to: date | str = "2026-09-30",
    schema_version: str = SCHEMA,
    currency_unit: str = CURRENCY,
    business_timezone: str = BUSINESS_TZ,
) -> dict[str, Any]:
    """Phong bì hợp đồng đã gộp trang — đúng thứ công cụ capture ghi ra."""
    return {
        "schema_version": schema_version,
        "business_timezone": business_timezone,
        "currency_unit": currency_unit,
        "date_from": date_from if isinstance(date_from, str) else date_from.isoformat(),
        "date_to": date_to if isinstance(date_to, str) else date_to.isoformat(),
        "generated_at": "2026-09-30T12:00:00+00:00",
        "pages": 1,
        "records": list(records),
        "errors": list(errors),
    }


def write_capture(
    tmp_path: Path,
    data: Optional[dict[str, Any]] = None,
    *,
    name: str = "tracking_daily_min.json",
    capture_id: str = CAPTURE_ID,
    captured_at: Optional[datetime] = None,
    capture_status: str = "COMPLETE",
    failure_reason: Optional[str] = None,
) -> Path:
    """Ghi một file capture đúng hình dạng `tools/tracking/capture_daily_min.py`."""
    path = Path(tmp_path) / name
    payload: dict[str, Any] = {
        "capture_id": capture_id,
        "captured_at": (
            captured_at or datetime(2026, 9, 30, 12, tzinfo=timezone.utc)
        ).isoformat(),
        "captured_by": CAPTURED_BY,
        "source_system_ref": SOURCE_SYSTEM_REF,
        "capture_status": capture_status,
    }
    if failure_reason is not None:
        payload["failure_reason"] = failure_reason
    if capture_status == "COMPLETE":
        payload["data"] = data if data is not None else contract()
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path
