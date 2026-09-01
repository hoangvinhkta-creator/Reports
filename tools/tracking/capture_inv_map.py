"""Chụp `inv.map` của Tracking ra file bất biến — S068 follow-up.

Đối xứng với `capture_tracking_catalog.py` (`board` + `alias.map`): đây là
capture tool cho nguồn identity THỨ HAI mà Owner đã cấp authority — `inv.map`,
khoá bằng câu tên hàng kế toán đầy đủ thay vì mã.

## Vì sao ở `tools/`, không phải `app/modules/`

`ADR-101` + `DEC-152` §6: phần chạm mạng nằm NGOÀI `app/modules/`. Dùng lại
ĐÚNG client hợp đồng của `capture_purchase_price_history.py` (một
`TRACKING_REPORT_API_KEY`, một `X-Report-Key`, một `INV-11` immutable-write)
thay vì cài một đường credential thứ hai.

## Chỉ đúng MỘT node — `inv_map`, KHÔNG resurrect `/api/xuat/inv`

```text
GET <source_url>/api/xuat/inv_map    → {"map": {"<khoá>": "<mã>" | "-"}}
Header: X-Report-Key: <TRACKING_REPORT_API_KEY>
```

`inv_map` là hợp đồng đã chiếu (project) sẵn xuống đúng nhánh `map` của `inv`
— KHÔNG mang `cu`/`moi`/`pend` (thẻ ngày, giá thực nhập bình quân gia quyền,
hàng chờ xử lý — xem `docs/tasks/TASK-108B-eligible-costs-owner-definition.md`
§52). Công cụ này KHÔNG BAO GIỜ hỏi node `inv` thô: nhánh đó mang dữ liệu giá
riêng tư (`gia`, `lo`, `cong`) mà `TrackingInvMapSnapshot` không có trường
nào để chứa, và đọc chúng về là thu thập dữ liệu không có chỗ dùng — đúng lý
do `capture_tracking_catalog.py` đã từ chối hỏi `inv` từ trước.

## Không tái phát minh identity logic

Khoá đã là `"N_" + normCode(tên hàng)[:80]` do chính Tracking ghi
(`app/modules/product/identity/tracking_inv_map.py`); công cụ này chép
nguyên văn payload `map`, không tính lại khoá, không lọc, không gộp `"-"`.
"""

from __future__ import annotations

import argparse
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from tools.tracking.capture_purchase_price_history import (
    API_KEY_ENV_VAR,
    CaptureError,
    Fetcher,
    INV_MAP_NODE,
    _http_fetcher,
    write_capture,
)
from app.modules.product.identity.tracking_inv_map import canonical_content_hash

SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
MALFORMED_SOURCE = "MALFORMED_SOURCE"
EMPTY_SOURCE_NOT_ASSERTABLE = "EMPTY_SOURCE_NOT_ASSERTABLE"


class MalformedSourceError(RuntimeError):
    """Nguồn với tới được nhưng sai hợp đồng. Không phải mất mạng."""


def _entries_from_payload(payload: Any) -> dict[str, str]:
    """`{"map": {...}}` → `entries`. Khoá top-level lạ = LỖI (`INV-02` cùng
    khuôn `public_purchase.py`): một `inv.map` trộn thêm metadata mà công cụ
    này lặng lẽ bỏ qua sẽ trông y hệt một capture sạch."""
    if not isinstance(payload, dict):
        raise MalformedSourceError(
            f"payload node {INV_MAP_NODE!r} phải là một ánh xạ, nhận "
            f"{type(payload).__name__}"
        )
    unknown = sorted(set(payload) - {"map"})
    if unknown:
        raise MalformedSourceError(
            f"payload node {INV_MAP_NODE!r} có khoá top-level lạ: {unknown} — "
            "hợp đồng chỉ có đúng 'map'"
        )
    if "map" not in payload:
        raise MalformedSourceError(
            f"payload node {INV_MAP_NODE!r} thiếu con 'map'"
        )
    raw_map = payload["map"]
    if not isinstance(raw_map, dict):
        raise MalformedSourceError(
            f"{INV_MAP_NODE}/map phải là một ánh xạ, nhận {type(raw_map).__name__}"
        )
    entries: dict[str, str] = {}
    for key, value in raw_map.items():
        if not isinstance(key, str) or not key.strip():
            raise MalformedSourceError(f"khoá 'map' rỗng/không phải chuỗi: {key!r}")
        if not isinstance(value, str) or not value.strip():
            raise MalformedSourceError(
                f"map[{key!r}] phải là chuỗi không rỗng (mã board hoặc '-'), "
                f"nhận {value!r}"
            )
        entries[key] = value
    return entries


def build_capture(
    fetch: Fetcher,
    *,
    capture_id: str,
    captured_by: str,
    source_system_ref: str,
    captured_at: Optional[datetime] = None,
) -> dict[str, Any]:
    """Đọc `inv_map` và dựng envelope. Lỗi → envelope `FAILED`, không raise,
    không file rỗng (`INV-12`, cùng khuôn `capture_tracking_catalog.py`)."""
    moment = captured_at or datetime.now(timezone.utc)
    envelope: dict[str, Any] = {
        "capture_id": capture_id,
        "captured_at": moment.isoformat(),
        "captured_by": captured_by,
        "source_system_ref": source_system_ref,
    }

    def failed(reason: str) -> dict[str, Any]:
        envelope["content_hash"] = canonical_content_hash({})
        envelope["capture_status"] = "FAILED"
        envelope["failure_reason"] = reason
        return envelope

    try:
        payload = fetch(INV_MAP_NODE)
    except CaptureError as exc:
        return failed(f"{SOURCE_UNAVAILABLE}: {exc}")

    if not payload:
        return failed(
            f"{EMPTY_SOURCE_NOT_ASSERTABLE}: node {INV_MAP_NODE!r} rỗng hoặc "
            "vắng mặt. Một payload trống trông giống hệt nhau ở 'inv.map thật "
            "sự chưa có mục nào' và 'sai URL / sai node / hợp đồng đang lỗi', "
            "nên KHÔNG kết luận được — người vận hành phải xác nhận "
            "source-url/node/key."
        )
    try:
        entries = _entries_from_payload(payload)
    except MalformedSourceError as exc:
        return failed(f"{MALFORMED_SOURCE}: {exc}")

    if not entries:
        return failed(
            f"{EMPTY_SOURCE_NOT_ASSERTABLE}: node {INV_MAP_NODE!r}/map rỗng."
        )

    envelope["content_hash"] = canonical_content_hash(entries)
    envelope["capture_status"] = "COMPLETE"
    envelope["entries"] = entries
    return envelope


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Chụp inv.map của Tracking (authority cho câu tên hàng kế toán "
            "đầy đủ) ra một file bất biến cho Reports (READ-ONLY)."
        )
    )
    parser.add_argument(
        "--source-url",
        required=True,
        help=(
            "URL gốc của Tracking Data Contract V1 (vd https://price.tinphatcrm"
            ".com). KHÔNG có mặc định và không nhúng sẵn."
        ),
    )
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument(
        "--captured-by", required=True, help="Ai/cái gì chạy lần capture này."
    )
    parser.add_argument(
        "--source-system-ref", default="tracking/api/xuat"
    )
    parser.add_argument("--capture-id", default=None)
    args = parser.parse_args(argv)

    capture_id = args.capture_id or (
        "INVMAP-"
        + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        + "-"
        + uuid.uuid4().hex[:8]
    )
    envelope = build_capture(
        _http_fetcher(args.source_url, os.environ.get(API_KEY_ENV_VAR)),
        capture_id=capture_id,
        captured_by=args.captured_by,
        source_system_ref=args.source_system_ref,
    )
    path = write_capture(envelope, args.out)
    status = envelope["capture_status"]
    print(f"{status} -> {path}")
    if status != "COMPLETE":
        print(f"failure_reason: {envelope['failure_reason']}", file=sys.stderr)
    return 0 if status == "COMPLETE" else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
