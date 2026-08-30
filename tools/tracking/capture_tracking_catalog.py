"""Chụp danh mục sản phẩm Tracking (`board` + `alias.map`) ra file bất biến.

Đây là phía CÒN THIẾU của ranh giới đã được `TASK-105D` §4.1 vẽ ra:
`app/modules/pricing/resolution/sources.py` đã có
`load_tracking_catalog_capture()` và `PostCutoverPriceComposition` đã đọc
`sources.tracking_catalog`, nhưng không có công cụ nào GHI ra file đó. Hệ quả
quan sát được trên đơn thật `BH73804`: `tracking_catalog = None` →
`IDENTITY_SOURCES_UNAVAILABLE` → Review Queue. File này đóng đúng khoảng
trống ấy và không làm gì thêm.

## Vì sao ở `tools/`, không phải `app/modules/`

`ADR-101` + `DEC-152` §6: phần chạm mạng nằm NGOÀI `app/modules/`, được thi
hành bằng assertion import-graph (`CHECK-105D-17`). Cùng phía ranh giới với
`capture_purchase_price_history.py`, và dùng lại ĐÚNG hàm fetch của nó nên
credential chỉ có một đường đi duy nhất trong cả repo.

## Chỉ ĐỌC, và chỉ hai node — `inv` KHÔNG BAO GIỜ được hỏi tới

Nguồn là Tracking → Reports Data Contract V1, KHÔNG phải Firebase RTDB trực
tiếp (đường cũ đã bị rút khỏi operational path — xem docstring của công cụ
chị em):

```text
GET <source_url>/api/xuat/board    → khoá node = mã, cùng `name` và `alt[]`
GET <source_url>/api/xuat/alias    → `map`: <mã cũ> → <mã chính>
Header: X-Report-Key: <TRACKING_REPORT_API_KEY>
```

Hợp đồng đã chiếu (project) sẵn `board` xuống đúng `name` + `alt`, và đã
chuẩn hoá `alt` thành mảng — nên `_rows_from_board()` bên dưới không phải
tách chuỗi, và các nhánh giá riêng tư (`p`, `tp`, `_c`) không rời khỏi
Tracking. Bộ kiểm tra hình dạng vẫn giữ nguyên: hợp đồng là lời hứa của một
hệ thống khác, không phải một bất biến của repo này.

`DEC-147` §2 ghi rằng giá nhập kế toán nằm ở `inv.<cu|moi>.gia` / `.lo`. Công
cụ này KHÔNG phát một request nào tới `inv`, `phist`, `backup` hay `dnhap` —
`TrackingCatalogSnapshot` (`§4.4`) không có trường nào để chứa chúng, nên
đọc chúng về là thu thập dữ liệu không có chỗ dùng.

Riêng nếu một phiên bản nguồn nào đó vẫn trả cả cây — gồm `p/<NCC>`
(giá NCC báo) và `tp/ton` (giá nhập công khai) — thì chúng đi qua bộ nhớ tiến
trình nhưng KHÔNG BAO GIỜ được ghi ra: mỗi dòng chỉ được dựng từ hai trường
trắng `name` và `alt`, không phải từ một bản sao dict. `test_the_capture_never_
persists_private_pricing_fields` kiểm điều đó trên envelope đã serialize.

## Không tái phát minh identity logic

Khoá node đã là `normCode()` do chính Tracking ghi; công cụ này chép nguyên
văn, không chuẩn hoá lại (`D-04`). Nó cũng KHÔNG áp `aliasOf()` để gộp dòng:
`INV-16` đòi resolver tự thấy alias và sinh `MAPPING_STALE` thay vì tự dời
một mapping đã confirm — gộp sẵn ở tầng capture sẽ xoá mất tín hiệu đó. Vì
thế `rows` và `alias_map` đi ra song song, y như hợp đồng mô tả.

## `present_in_board` luôn `True`

Capture là ảnh chụp một thời điểm: cái gì có trong `board` thì present. Chiều
`false` của `INV-14` được biểu đạt bằng "vắng khỏi capture mới" — và
`ProductIdentityResolver._present_in_board()` đọc một mã vắng mặt thành
`False`, nên hai cách viết cho cùng một kết quả. Suy ra `present_in_board =
false` từ một nhánh khác (`dropped`) sẽ là mở rộng schema không có authority.

## Bốn kết cục, hai giá trị `capture_status`

`CaptureStatus` là enum ĐÓNG `{COMPLETE, FAILED}` (`§4.4`) và resolver treo
`INV-12` lên đúng nó. Nên phân biệt của §7 nằm ở `failure_reason` có tiền tố
máy đọc được, không phải ở một giá trị enum mới:

```text
COMPLETE                              capture thành công
FAILED  SOURCE_UNAVAILABLE:...        không với tới được nguồn (mạng/auth/parse)
FAILED  MALFORMED_SOURCE:...          với tới được nhưng sai hình dạng hợp đồng
FAILED  EMPTY_SOURCE_NOT_ASSERTABLE   `board` rỗng/vắng — xem ngay dưới
```

**Một `board` rỗng KHÔNG được ghi thành một danh mục rỗng.** Từ dây không
phân biệt được "danh mục thật sự trống" với "sai URL / sai node / sai key /
hợp đồng đang lỗi" — mọi trường hợp đều có thể về một payload trống. Một
danh mục rỗng COMPLETE sẽ làm MỌI sản phẩm Pending và trông y hệt một kết
luận nghiệp vụ — đúng lớp lỗi `INV-12` tồn tại để chặn. Nên fail closed: đó
là `FAILED`, và người vận hành phải xác nhận, không phải hệ thống đoán.

`alias` rỗng thì ngược lại — "chưa có mã nào bị gộp" là trạng thái khởi đầu
đúng, và `alias_map` là evidence phụ trợ chứ không phải bản thân danh mục.
"""

from __future__ import annotations

import argparse
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

# Dùng lại ĐÚNG client hợp đồng + đường credential của công cụ capture đã
# review, thay vì chép lại: một `method="GET"` duy nhất, một
# `TRACKING_REPORT_API_KEY` duy nhất, một quy tắc bất biến `INV-11` duy nhất
# trong cả repo.
from tools.tracking.capture_purchase_price_history import (
    API_KEY_ENV_VAR,
    CaptureError,
    Fetcher,
    _http_fetcher,
    write_capture,
)
from app.modules.product.identity.tracking_catalog import canonical_content_hash

BOARD_NODE = "board"
ALIAS_NODE = "alias"
ALIAS_MAP_CHILD = "map"

SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
MALFORMED_SOURCE = "MALFORMED_SOURCE"
EMPTY_SOURCE_NOT_ASSERTABLE = "EMPTY_SOURCE_NOT_ASSERTABLE"


class MalformedSourceError(RuntimeError):
    """Nguồn với tới được nhưng sai hợp đồng `§4.4`. Không phải mất mạng."""


def _rows_from_board(board: Any) -> list[dict[str, Any]]:
    """`board` → `rows` theo `§4.4`, chỉ giữ `name` và `alt`."""
    if not isinstance(board, dict):
        raise MalformedSourceError(
            f"nhánh {BOARD_NODE!r} phải là một ánh xạ mã → dòng, nhận "
            f"{type(board).__name__}"
        )
    rows: list[dict[str, Any]] = []
    for code, raw in board.items():
        if not isinstance(code, str) or not code.strip():
            raise MalformedSourceError(f"khoá node rỗng/không phải chuỗi: {code!r}")
        if not isinstance(raw, dict):
            raise MalformedSourceError(
                f"{BOARD_NODE}/{code} phải là một ánh xạ, nhận {type(raw).__name__}"
            )
        name = raw.get("name")
        if name is not None and not isinstance(name, str):
            raise MalformedSourceError(
                f"{BOARD_NODE}/{code}/name phải là chuỗi, nhận {type(name).__name__}"
            )
        alt = raw.get("alt")
        if alt is None:
            alt = []
        if not isinstance(alt, list) or any(not isinstance(a, str) for a in alt):
            raise MalformedSourceError(
                f"{BOARD_NODE}/{code}/alt phải là danh sách chuỗi"
            )
        row: dict[str, Any] = {"tracking_code": code, "present_in_board": True}
        if name is not None:
            row["name"] = name
        if alt:
            row["alt"] = list(alt)
        rows.append(row)
    # Thứ tự ổn định: `exact_match_codes()` trả hit theo thứ tự dòng và
    # `INV-64` đòi thứ tự ấy không phụ thuộc thứ tự khoá của một dict JSON.
    rows.sort(key=lambda r: r["tracking_code"])
    return rows


def _alias_map_from(alias: Any) -> dict[str, str]:
    """`alias` → `<mã cũ> → <mã chính>` (`DEC-147` §4). Vắng mặt = rỗng."""
    if alias is None:
        return {}
    if not isinstance(alias, dict):
        raise MalformedSourceError(
            f"nhánh {ALIAS_NODE!r} phải là một ánh xạ, nhận {type(alias).__name__}"
        )
    if ALIAS_MAP_CHILD not in alias:
        raise MalformedSourceError(
            f"nhánh {ALIAS_NODE!r} thiếu con {ALIAS_MAP_CHILD!r} — hình dạng "
            "nguồn khác với bằng chứng đã audit (DEC-147 §4); dừng thay vì "
            "đoán một bảng alias rỗng"
        )
    raw = alias[ALIAS_MAP_CHILD]
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise MalformedSourceError(
            f"{ALIAS_NODE}/{ALIAS_MAP_CHILD} phải là một ánh xạ, nhận "
            f"{type(raw).__name__}"
        )
    out: dict[str, str] = {}
    for old, primary in raw.items():
        if not isinstance(primary, str) or not primary.strip():
            raise MalformedSourceError(
                f"{ALIAS_NODE}/{ALIAS_MAP_CHILD}/{old} phải trỏ tới một mã chính "
                "dạng chuỗi không rỗng"
            )
        out[str(old)] = primary
    return dict(sorted(out.items()))


def build_capture(
    fetch: Fetcher,
    *,
    capture_id: str,
    captured_by: str,
    source_system_ref: str,
    captured_at: Optional[datetime] = None,
) -> dict[str, Any]:
    """Đọc hai nhánh và dựng envelope đúng hợp đồng `load_tracking_catalog_
    capture()`. Lỗi → envelope `FAILED` hợp lệ, không raise, không file rỗng."""
    moment = captured_at or datetime.now(timezone.utc)
    envelope: dict[str, Any] = {
        "capture_id": capture_id,
        "captured_at": moment.isoformat(),
        "captured_by": captured_by,
        "source_system_ref": source_system_ref,
    }

    def failed(reason: str) -> dict[str, Any]:
        # `content_hash` là REQUIRED kể cả ở nhánh FAILED (loader đọc nó trước
        # khi rẽ nhánh). Ở đây nó là hash của thứ ĐÃ chụp được — tức không có
        # gì — và `capture_status` mới là cổng, không phải hash.
        envelope["content_hash"] = canonical_content_hash([], {})
        envelope["capture_status"] = "FAILED"
        envelope["failure_reason"] = reason
        return envelope

    try:
        board = fetch(BOARD_NODE)
        alias = fetch(ALIAS_NODE)
    except CaptureError as exc:
        return failed(f"{SOURCE_UNAVAILABLE}: {exc}")

    if not board:
        return failed(
            f"{EMPTY_SOURCE_NOT_ASSERTABLE}: node {BOARD_NODE!r} rỗng hoặc "
            "vắng mặt. Một payload trống trông giống hệt nhau ở 'danh mục thật "
            "sự trống' và 'sai URL / sai node / hợp đồng đang lỗi', nên KHÔNG "
            "kết luận được — người vận hành phải xác nhận source-url/node/key."
        )
    try:
        rows = _rows_from_board(board)
        alias_map = _alias_map_from(alias)
    except MalformedSourceError as exc:
        return failed(f"{MALFORMED_SOURCE}: {exc}")

    envelope["content_hash"] = canonical_content_hash(rows, alias_map)
    envelope["capture_status"] = "COMPLETE"
    envelope["rows"] = rows
    envelope["alias_map"] = alias_map
    return envelope


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Chụp danh mục sản phẩm Tracking (board + alias.map) ra một file "
            "bất biến cho Reports (READ-ONLY). Không đọc giá, không đọc inv."
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
        "TRK-"
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
