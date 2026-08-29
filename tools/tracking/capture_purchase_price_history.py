"""Chụp `purchase_price_baseline` + `purchase_price_history` của Tracking ra file.

## Vì sao công cụ này nằm ở `tools/`, không phải `app/modules/`

`ADR-101` + `DEC-152` §6: phần chạm mạng nằm NGOÀI `app/modules/`. Ranh giới
ấy được thi hành bằng một assertion import-graph (`CHECK-105D-17`) quét toàn
bộ `app/modules/**` tìm import mạng — không phải bằng một quy ước. Công cụ
này là phía bên kia của ranh giới: nó đọc RTDB READ-ONLY rồi ghi ra một file
bất biến; `app/modules/pricing/tracking_history/capture_file.py` đọc file đó.

## Chỉ ĐỌC, và chỉ hai nhánh

```text
GET <database_url>/purchase_price_baseline.json
GET <database_url>/purchase_price_history.json
```

Không `PUT`, không `PATCH`, không `POST`, không `DELETE` — repo Tracking là
read-only đối với Reports (`DEC-154` Preserves). Không có hàm ghi nào trong
file này để lỡ tay gọi.

## Credential

Không hardcode, không nhúng, không đoán. `--database-url` là tham số bắt
buộc; token (nếu database yêu cầu) đọc từ biến môi trường
`TRACKING_RTDB_TOKEN` và KHÔNG BAO GIỜ được ghi vào file capture hay in ra
log — file capture đi vào repo, còn token thì không.

## Capture hỏng ghi ra `capture_status = FAILED`, không ghi file rỗng

`INV-12`: một lần capture hỏng và một lịch sử thật sự rỗng là hai sự kiện
khác nhau. Nếu gộp lại, một lần mất mạng trông y hệt một kết luận về dữ liệu.
Nên khi lỗi, công cụ vẫn ghi một file HỢP LỆ mang `FAILED` + `failure_reason`,
và reader sẽ TỪ CHỐI chạy trên nó thay vì trả Pending.

## `capture_id` do công cụ cấp

Nội dung không tự chứng minh được nó được chụp lúc nào, nên provenance của
lần capture (`capture_id`, `captured_at`, `captured_by`) đến TỪ đây.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

BASELINE_NODE = "purchase_price_baseline"
HISTORY_NODE = "purchase_price_history"
TOKEN_ENV_VAR = "TRACKING_RTDB_TOKEN"

Fetcher = Callable[[str], Any]
"""`node_path -> JSON đã decode`. Được tiêm vào để test không cần mạng."""


class CaptureError(RuntimeError):
    """Lần capture thất bại. Không bao giờ trở thành một file COMPLETE rỗng."""


def _http_fetcher(database_url: str, token: Optional[str]) -> Fetcher:
    base = database_url.rstrip("/")

    def fetch(node: str) -> Any:
        url = f"{base}/{node}.json"
        if token:
            url += "?" + urllib.parse.urlencode({"auth": token})
        request = urllib.request.Request(url, method="GET")
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, OSError, json.JSONDecodeError) as exc:
            # Thông điệp KHÔNG chứa `url` (nó mang token trong query string).
            raise CaptureError(
                f"không đọc được node {node!r} từ RTDB: {type(exc).__name__}: {exc}"
            ) from exc

    return fetch


def build_capture(
    fetch: Fetcher,
    *,
    capture_id: str,
    captured_by: str,
    source_system_ref: str,
    captured_at: Optional[datetime] = None,
) -> dict[str, Any]:
    """Đọc hai nhánh và dựng envelope. Lỗi → envelope `FAILED`, không raise.

    Trả về một dict đúng hợp đồng mà
    `app.modules.pricing.tracking_history.capture_file` đọc.
    """
    moment = captured_at or datetime.now(timezone.utc)
    envelope: dict[str, Any] = {
        "capture_id": capture_id,
        "captured_at": moment.isoformat(),
        "captured_by": captured_by,
        "source_system_ref": source_system_ref,
    }
    try:
        baseline = fetch(BASELINE_NODE)
        history = fetch(HISTORY_NODE)
    except CaptureError as exc:
        envelope["capture_status"] = "FAILED"
        envelope["failure_reason"] = str(exc)
        return envelope

    envelope["capture_status"] = "COMPLETE"
    envelope["data"] = {
        BASELINE_NODE: baseline or {},
        HISTORY_NODE: history or {},
    }
    return envelope


def write_capture(envelope: dict[str, Any], out_path: Path) -> Path:
    """Ghi file capture. TỪ CHỐI ghi đè: capture là bất biến (`INV-11`)."""
    if out_path.exists():
        raise CaptureError(
            f"{out_path} đã tồn tại — capture là BẤT BIẾN, không ghi đè "
            "(INV-11). Ghi ra một đường dẫn mới rồi thay thế có chủ đích."
        )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(envelope, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return out_path


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Chụp purchase_price_baseline + purchase_price_history của Tracking "
            "ra một file bất biến cho Reports (READ-ONLY)."
        )
    )
    parser.add_argument(
        "--database-url",
        required=True,
        help="URL gốc của Firebase RTDB. KHÔNG có mặc định và không nhúng sẵn.",
    )
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument(
        "--captured-by", required=True, help="Ai/cái gì chạy lần capture này."
    )
    parser.add_argument("--source-system-ref", default="tracking/rtdb")
    parser.add_argument("--capture-id", default=None)
    args = parser.parse_args(argv)

    capture_id = args.capture_id or (
        "PPH-"
        + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        + "-"
        + uuid.uuid4().hex[:8]
    )
    envelope = build_capture(
        _http_fetcher(args.database_url, os.environ.get(TOKEN_ENV_VAR)),
        capture_id=capture_id,
        captured_by=args.captured_by,
        source_system_ref=args.source_system_ref,
    )
    path = write_capture(envelope, args.out)
    print(f"{envelope['capture_status']} -> {path}")
    return 0 if envelope["capture_status"] == "COMPLETE" else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
