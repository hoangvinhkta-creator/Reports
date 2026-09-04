"""Pull-on-run Tracking adapter — Reports Web Shared Beta (S071 §2/§3).

Kiến trúc bắt buộc: mỗi lần ai đó chạy báo cáo trên bản Web Shared Beta,
backend fetch LIVE từ Tracking Data Contract V1 ngay lúc đó — không đọc lại
capture cũ trên đĩa máy Owner, không giữ mirror database, không đồng bộ định
kỳ (S071 §3: "PULL ON REPORT RUN", không "periodic synchronization"). Đây là
điểm khác biệt DUY NHẤT so với luồng local Owner (S068–S070), vốn vẫn đọc
capture đã chụp tay trước đó qua ``app.owner_usability.select_latest_valid_
captures`` — luồng đó GIỮ NGUYÊN, không đổi hành vi.

Ba capture builder (``purchase_price_history``+baseline, ``catalog``
board+alias, ``inv_map``) đã tồn tại ở ``tools/tracking/capture_*.py`` và
dùng chung một client HTTP duy nhất
(``capture_purchase_price_history._http_fetcher``). Module này chỉ ĐIỀU PHỐI
live: gọi lại đúng ba ``build_capture()`` đó trong một lần chạy, ghi từng
capture ra một file tạm CHO LẦN CHẠY NÀY (bất biến theo ``write_capture``,
INV-11 — mỗi file một tên duy nhất), nạp qua đúng loader hiện có
(``app.owner_usability.SelectedCaptures`` cùng hình dạng luồng local), rồi
gọi ``cleanup()`` XOÁ file tạm ngay sau khi dùng — không giữ authority thô
của Tracking lâu hơn một lần chạy trên đĩa máy chủ (S071 §10: minimize
retention áp dụng ngang với workbook upload).

Fail-closed: ``purchase_price_history``(+baseline) và ``catalog`` là
REQUIRED — FAILED ở một trong hai raise ``TrackingUnavailableError`` ngay,
KHÔNG rơi về bất kỳ capture cũ nào trên đĩa (S071 §3: "KHÔNG silently
fallback stale authority").

## PHB-01/D1 — ``inv_map`` cũng fail-closed KHI FETCH HỎNG

Trước PHB-01, một ``inv_map`` FAILED (mất mạng, 403, 502, payload sai hợp
đồng) chỉ làm ``tracking_inv_map=None`` cho lần chạy đó. Hệ quả không dừng ở
"thiếu một nguồn phụ": resolver không có ``inv.map`` thì MỌI câu tên hàng kế
toán đều trả ``PENDING_PRODUCT``, và người vận hành đọc được đúng một câu —
"sản phẩm chưa được phân loại". Một sự cố hạ tầng mặc lốt một kết luận nghiệp
vụ, và bản xuất "chờ phân loại" sẽ liệt kê cả những mặt hàng Owner ĐÃ phân
loại xong từ lâu. Đó chính là điều D1 cấm.

Nay tách đúng hai trạng thái:

* **fetch HỎNG** (``capture_status != "COMPLETE"``) → ``TrackingUnavailable
  Error`` ngay, không report nào được sinh. Cùng luật với hai node REQUIRED,
  và đúng ``INV-12`` mà resolver đã áp cho một snapshot FAILED có mặt
  (``require_complete()``) — chỗ DUY NHẤT còn nuốt nó là đây.
* **authority rỗng HỢP LỆ** (``{"map": {}}`` → ``COMPLETE``, 0 mục) → chạy
  tiếp bình thường. "Chưa ai phân loại dòng nào" là một câu trả lời thật của
  authority, không phải sự cố.

``inv_map_status``/``inv_map_entries`` vẫn đi vào evidence của lần chạy để
đọc lại được về sau.
"""

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

from tools.tracking import capture_inv_map, capture_tracking_catalog
from tools.tracking.capture_purchase_price_history import (
    API_KEY_ENV_VAR,
    _http_fetcher,
    build_capture as _build_history_capture,
    write_capture,
)

SOURCE_URL_ENV_VAR = "TRACKING_REPORT_SOURCE_URL"
DEFAULT_CAPTURED_BY = "reports-web-shared-beta"

Fetcher = Callable[[str], Any]


class TrackingUnavailableError(RuntimeError):
    """Live pull thất bại trên một nguồn REQUIRED (``purchase_price_history``
    hoặc ``catalog``). Không report nào được sinh khi lỗi này raise — không
    bao giờ âm thầm dùng một capture cũ."""

    def __init__(self, message: str, *, node: str, reason: str) -> None:
        super().__init__(message)
        self.node = node
        self.reason = reason


@dataclass(frozen=True)
class LiveSelectedCaptures:
    """Cùng hình dạng ``app.owner_usability.SelectedCaptures`` — bên gọi
    (``run_owner_report``) không cần biết captures đến từ local hay live."""

    tracking_capture: Path
    tracking_catalog: Path
    tracking_inv_map: Optional[Path]
    evidence: dict[str, Any]
    temp_paths: tuple[Path, ...]

    def cleanup(self) -> None:
        """Xoá mọi file capture tạm của lần chạy này — best-effort, không
        raise nếu file đã bị dọn trước đó."""
        for path in self.temp_paths:
            Path(path).unlink(missing_ok=True)


def is_configured(env: Optional[dict[str, str]] = None) -> bool:
    """``True`` khi cả nguồn và secret Tracking đã được cấu hình ở môi
    trường này. Cloud environment có thể chưa có secret (S071 §7) — đây
    KHÔNG phải lỗi kiến trúc, chỉ là tín hiệu để server chọn nhánh xử lý."""
    source = env if env is not None else os.environ
    return bool(source.get(SOURCE_URL_ENV_VAR)) and bool(source.get(API_KEY_ENV_VAR))


def pull_live_captures(
    *,
    out_dir: Path,
    source_url: Optional[str] = None,
    api_key: Optional[str] = None,
    captured_by: str = DEFAULT_CAPTURED_BY,
    now: Optional[datetime] = None,
    fetch: Optional[Fetcher] = None,
) -> LiveSelectedCaptures:
    """Fetch cả ba node Tracking LIVE cho đúng một lần chạy report.

    ``fetch`` cho phép test tiêm một fetcher giả (timeout/403/502/malformed
    JSON) mà không cần mạng thật — cùng seam ``Fetcher`` mà các script capture
    dùng, không phát minh cơ chế test thứ hai.
    """
    source_url = source_url or os.environ.get(SOURCE_URL_ENV_VAR)
    api_key = api_key or os.environ.get(API_KEY_ENV_VAR)
    if not source_url:
        raise TrackingUnavailableError(
            f"Thiếu biến môi trường {SOURCE_URL_ENV_VAR} — chưa cấu hình nguồn "
            "Tracking Data Contract V1 cho môi trường này.",
            node="config", reason="MISSING_SOURCE_URL",
        )
    if fetch is None:
        fetch = _http_fetcher(source_url, api_key)

    moment = now or datetime.now(timezone.utc)
    token = uuid.uuid4().hex
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    history_envelope = _build_history_capture(
        fetch,
        capture_id=f"LIVE-PPH-{token}",
        captured_by=captured_by,
        source_system_ref="tracking/api/xuat (live pull-on-run)",
        captured_at=moment,
    )
    _raise_if_failed(history_envelope, node="purchase_price_history")

    catalog_envelope = capture_tracking_catalog.build_capture(
        fetch,
        capture_id=f"LIVE-CAT-{token}",
        captured_by=captured_by,
        source_system_ref="tracking/api/xuat (live pull-on-run)",
        captured_at=moment,
    )
    _raise_if_failed(catalog_envelope, node="catalog")

    # inv_map: fetch hỏng là LỖI AUTHORITY, không phải "chưa nối" (§ PHB-01/D1).
    inv_map_envelope = capture_inv_map.build_capture(
        fetch,
        capture_id=f"LIVE-INV-{token}",
        captured_by=captured_by,
        source_system_ref="tracking/api/xuat (live pull-on-run)",
        captured_at=moment,
    )
    _raise_if_failed(inv_map_envelope, node="inv_map")

    temp_paths: list[Path] = []
    history_path = out_dir / f"{token}-purchase-price-history.json"
    write_capture(history_envelope, history_path)
    temp_paths.append(history_path)

    catalog_path = out_dir / f"{token}-catalog.json"
    write_capture(catalog_envelope, catalog_path)
    temp_paths.append(catalog_path)

    # Tới đây `inv_map` chắc chắn COMPLETE — `_raise_if_failed` ở trên đã
    # chặn mọi nhánh khác, nên không còn đường nào ghi ra một lần chạy "thành
    # công" mà authority định danh thì không có.
    inv_map_path = out_dir / f"{token}-inv-map.json"
    write_capture(inv_map_envelope, inv_map_path)
    temp_paths.append(inv_map_path)

    evidence = {
        "purchase_price_history_capture_id": history_envelope["capture_id"],
        "purchase_price_history_captured_at": history_envelope["captured_at"],
        "catalog_capture_id": catalog_envelope["capture_id"],
        "inv_map_capture_id": inv_map_envelope["capture_id"],
        "inv_map_status": inv_map_envelope["capture_status"],
        # 0 mục = authority rỗng HỢP LỆ, đọc lại được từ evidence mà không
        # phải mở lại file capture tạm (đã bị xoá sau lần chạy).
        "inv_map_entries": len(inv_map_envelope.get("entries") or {}),
        "inv_map_empty_reason": inv_map_envelope.get("empty_reason"),
        "pulled_at": moment.isoformat(),
        "source_system_ref": "tracking/api/xuat (live pull-on-run)",
    }
    return LiveSelectedCaptures(
        tracking_capture=history_path,
        tracking_catalog=catalog_path,
        tracking_inv_map=inv_map_path,
        evidence=evidence,
        temp_paths=tuple(temp_paths),
    )


def _raise_if_failed(envelope: dict[str, Any], *, node: str) -> None:
    if envelope.get("capture_status") != "COMPLETE":
        raise TrackingUnavailableError(
            f"Tracking pull-on-run thất bại ở node {node!r}: "
            f"{envelope.get('failure_reason', 'không rõ lý do')}",
            node=node,
            reason=str(envelope.get("failure_reason", "UNKNOWN")),
        )
