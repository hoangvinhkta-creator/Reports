"""Chụp `purchase_price_baseline` + `purchase_price_history` của Tracking ra file.

## Vì sao công cụ này nằm ở `tools/`, không phải `app/modules/`

`ADR-101` + `DEC-152` §6: phần chạm mạng nằm NGOÀI `app/modules/`. Ranh giới
ấy được thi hành bằng một assertion import-graph (`CHECK-105D-17`) quét toàn
bộ `app/modules/**` tìm import mạng — không phải bằng một quy ước. Công cụ
này là phía bên kia của ranh giới: nó đọc nguồn Tracking READ-ONLY rồi ghi ra
một file bất biến; `app/modules/pricing/tracking_history/capture_file.py` đọc
file đó.

## Nguồn: Tracking → Reports Data Contract V1, KHÔNG phải Firebase RTDB

Reports KHÔNG còn đọc Firebase RTDB trực tiếp. Đường cũ
(`<database_url>/<node>.json` + `auth=<TRACKING_RTDB_TOKEN>`) đã bị rút khỏi
operational path: nó đòi Firebase Auth/App Check mà Reports không có và
không nên có. Nguồn hợp lệ duy nhất là hợp đồng do Tracking phát hành:

```text
GET <source_url>/api/xuat/purchase_price_baseline
GET <source_url>/api/xuat/purchase_price_history
GET <source_url>/api/xuat/board
GET <source_url>/api/xuat/alias
Header: X-Report-Key: <secret>
```

`ALLOWED_NODES` là danh sách ĐÓNG bốn node trên; hỏi một node ngoài danh sách
là lỗi ngay tại client, không phát request. Không có fallback Firebase: hợp
đồng lỗi thì capture `FAILED`, chứ không lặng lẽ rơi về một đường thứ hai —
hai đường nguồn song song chính là thứ `INV-12` tồn tại để chặn.

## Chỉ ĐỌC

Không `PUT`, không `PATCH`, không `POST`, không `DELETE` — Tracking là
read-only đối với Reports (`DEC-154` Preserves). Không có hàm ghi nào trong
file này để lỡ tay gọi.

## Credential

Không hardcode, không nhúng, không đoán, không đặt trong query string.
`--source-url` là tham số bắt buộc; secret đọc từ biến môi trường
`TRACKING_REPORT_API_KEY` và đi ra ngoài DUY NHẤT ở header `X-Report-Key`.
Nó KHÔNG BAO GIỜ được ghi vào file capture, vào thông điệp lỗi hay ra log —
file capture đi vào repo, còn secret thì không. Thiếu secret là fail-closed:
capture `FAILED`, không thử một request không key.

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
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

BASELINE_NODE = "purchase_price_baseline"
HISTORY_NODE = "purchase_price_history"
API_KEY_ENV_VAR = "TRACKING_REPORT_API_KEY"
API_KEY_HEADER = "X-Report-Key"
CONTRACT_PREFIX = "/api/xuat"
ALLOWED_NODES = frozenset({BASELINE_NODE, HISTORY_NODE, "board", "alias"})
JSON_CONTENT_TYPE = "application/json"
MISSING_API_KEY = "MISSING_API_KEY"

Fetcher = Callable[[str], Any]
"""`node_path -> JSON đã decode`. Được tiêm vào để test không cần mạng."""


class CaptureError(RuntimeError):
    """Lần capture thất bại. Không bao giờ trở thành một file COMPLETE rỗng."""


def _http_fetcher(source_url: str, api_key: Optional[str]) -> Fetcher:
    """Client DUY NHẤT của Tracking Data Contract V1 trong cả repo Reports.

    Thiếu key, node ngoài hợp đồng, không phải JSON → `CaptureError`. Mọi
    nhánh lỗi đều fail closed và KHÔNG có đường rơi về Firebase.
    """
    base = source_url.rstrip("/")

    def fetch(node: str) -> Any:
        # Kiểm tra ở trong `fetch` chứ không ở lúc dựng fetcher: `build_capture`
        # bắt `CaptureError` và ghi ra một artifact `FAILED` đọc lại được, thay
        # vì để CLI chết bằng traceback và không để lại bằng chứng nào.
        if not api_key:
            raise CaptureError(
                f"{MISSING_API_KEY}: thiếu biến môi trường {API_KEY_ENV_VAR} — "
                f"hợp đồng Tracking đòi header {API_KEY_HEADER}; không phát "
                "request không key."
            )
        if node not in ALLOWED_NODES:
            raise CaptureError(
                f"node {node!r} nằm ngoài hợp đồng V1 {sorted(ALLOWED_NODES)}"
            )
        url = f"{base}{CONTRACT_PREFIX}/{node}"
        request = urllib.request.Request(
            url, method="GET", headers={API_KEY_HEADER: api_key}
        )
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                content_type = (
                    (response.headers.get("Content-Type") or "").split(";")[0].strip()
                )
                if content_type != JSON_CONTENT_TYPE:
                    # Một trang HTML (login/redirect/error page) trả 200 là cách
                    # im lặng nhất để một "capture thành công" thành rác.
                    raise CaptureError(
                        f"node {node!r}: hợp đồng phải trả {JSON_CONTENT_TYPE}, "
                        f"nhận {content_type!r}"
                    )
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, OSError, json.JSONDecodeError) as exc:
            # Thông điệp mang `node`, KHÔNG mang header — secret không đi ra log.
            raise CaptureError(
                f"không đọc được node {node!r} qua hợp đồng Tracking: "
                f"{type(exc).__name__}: {exc}"
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
        "PPH-"
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
    print(f"{envelope['capture_status']} -> {path}")
    return 0 if envelope["capture_status"] == "COMPLETE" else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
