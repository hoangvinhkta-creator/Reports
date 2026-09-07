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
fallback stale authority"). ``inv_map`` giữ nguyên bán chất TUỲ CHỌN đã có
từ S068 follow-up: FAILED/lỗi mạng ở riêng nhánh này không chặn lần chạy,
chỉ làm ``tracking_inv_map=None`` cho lần đó — cùng ngữ nghĩa "chưa nối" sẵn
có, không phải "bỏ qua lỗi im lặng".
"""

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

from tools.tracking import capture_daily_min, capture_inv_map, capture_tracking_catalog
from tools.tracking.capture_purchase_price_history import (
    API_KEY_ENV_VAR,
    _http_fetcher,
    build_capture as _build_history_capture,
    write_capture,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
"""Gốc repo Reports. Các đường dẫn canonical (`data/...`) là TƯƠNG ĐỐI với nó,
và máy chủ web không chạy từ thư mục ấy — nên chúng được nối tường minh ở đây
thay vì dựa vào thư mục làm việc hiện hành."""

SOURCE_URL_ENV_VAR = "TRACKING_REPORT_SOURCE_URL"
DEFAULT_CAPTURED_BY = "reports-web-shared-beta"

Fetcher = Callable[[str], Any]
Poster = Callable[[dict[str, Any]], Any]


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
    #: R1 — ảnh chụp MIN theo NGÀY BÁN, đóng băng cho ĐÚNG lần chạy này.
    #: ``None`` khi lần chạy không có dòng nào mang identity Tracking (không
    #: có gì để hỏi), hoặc khi kỳ rộng hơn một lượt gọi hợp đồng — hai cảnh
    #: đều được ghi lý do vào ``evidence``, không cảnh nào im lặng.
    tracking_daily_min: Optional[Path] = None

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
    sales: Optional[Path] = None,
    post: Optional[Poster] = None,
) -> LiveSelectedCaptures:
    """Fetch các node Tracking LIVE cho đúng một lần chạy report.

    ``fetch`` cho phép test tiêm một fetcher giả (timeout/403/502/malformed
    JSON) mà không cần mạng thật — cùng seam ``Fetcher`` mà các script capture
    dùng, không phát minh cơ chế test thứ hai. ``post`` là seam tương ứng cho
    hợp đồng ``daily-min-v1``, vốn là một POST có tham số.

    ``sales`` (R1) là workbook của CHÍNH lần chạy này. Có nó thì hàm này lập kế
    hoạch hỏi giá (tập mã Tracking đã resolve + khoảng ngày bán thật) rồi gọi
    ``daily-min-v1`` MỘT lượt. Không có nó thì không có ảnh chụp MIN — và mọi
    dòng Tracking sẽ Pending với đúng lý do "chưa nối nguồn", chứ không mượn
    một nguồn giá khác.
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

    # inv_map: TUỲ CHỌN — lỗi ở đây không raise, chỉ ghi lại status để đưa
    # vào evidence; server tiếp tục chạy với `tracking_inv_map=None`.
    inv_map_envelope = capture_inv_map.build_capture(
        fetch,
        capture_id=f"LIVE-INV-{token}",
        captured_by=captured_by,
        source_system_ref="tracking/api/xuat (live pull-on-run)",
        captured_at=moment,
    )

    temp_paths: list[Path] = []
    history_path = out_dir / f"{token}-purchase-price-history.json"
    write_capture(history_envelope, history_path)
    temp_paths.append(history_path)

    catalog_path = out_dir / f"{token}-catalog.json"
    write_capture(catalog_envelope, catalog_path)
    temp_paths.append(catalog_path)

    inv_map_path: Optional[Path] = None
    if inv_map_envelope.get("capture_status") == "COMPLETE":
        inv_map_path = out_dir / f"{token}-inv-map.json"
        write_capture(inv_map_envelope, inv_map_path)
        temp_paths.append(inv_map_path)

    # --- R1: MIN theo ngày bán ------------------------------------------
    # Phải chạy SAU catalog: kế hoạch hỏi giá cần identity đã resolve, và
    # identity cần danh mục Tracking của CHÍNH lần chạy này.
    daily_min_path, daily_min_evidence = _pull_daily_min(
        sales=sales,
        catalog_path=catalog_path,
        inv_map_path=inv_map_path,
        out_dir=out_dir,
        token=token,
        source_url=source_url,
        api_key=api_key,
        captured_by=captured_by,
        moment=moment,
        post=post,
    )
    if daily_min_path is not None:
        temp_paths.append(daily_min_path)

    evidence = {
        **daily_min_evidence,
        "purchase_price_history_capture_id": history_envelope["capture_id"],
        "purchase_price_history_captured_at": history_envelope["captured_at"],
        "catalog_capture_id": catalog_envelope["capture_id"],
        "inv_map_capture_id": inv_map_envelope.get("capture_id") if inv_map_path else None,
        "inv_map_status": inv_map_envelope.get("capture_status"),
        "inv_map_failure_reason": (
            inv_map_envelope.get("failure_reason") if inv_map_path is None else None
        ),
        "pulled_at": moment.isoformat(),
        "source_system_ref": "tracking/api/xuat (live pull-on-run)",
    }
    return LiveSelectedCaptures(
        tracking_capture=history_path,
        tracking_catalog=catalog_path,
        tracking_inv_map=inv_map_path,
        evidence=evidence,
        temp_paths=tuple(temp_paths),
        tracking_daily_min=daily_min_path,
    )


def _pull_daily_min(
    *,
    sales: Optional[Path],
    catalog_path: Path,
    inv_map_path: Optional[Path],
    out_dir: Path,
    token: str,
    source_url: Optional[str],
    api_key: Optional[str],
    captured_by: str,
    moment: datetime,
    post: Optional[Poster],
) -> tuple[Optional[Path], dict[str, Any]]:
    """Lập kế hoạch từ sổ rồi gọi ``daily-min-v1`` MỘT lượt cho lần chạy này.

    Ba kết cục, ba lý do KHÁC NHAU, không cái nào im lặng:

    * ``sales=None`` — không ai đưa sổ vào, nên không có kế hoạch nào để lập.
    * kế hoạch RỖNG — lần chạy này không có dòng nào mang identity Tracking,
      nên không có câu hỏi nào để đặt ra. Không phải lỗi.
    * kỳ RỘNG hơn một lượt gọi hợp đồng — đây là tính chất của SỔ, không phải
      của Tracking, nên nó không được biến thành "Tracking hỏng": lần chạy đi
      tiếp, mọi dòng Tracking Pending với lý do nguồn chưa nối, và lý do thật
      nằm trong bằng chứng.

    Còn lại — hợp đồng trả FAILED — là REQUIRED và ném ``TrackingUnavailable
    Error``: từ R1, MIN theo ngày bán LÀ nguồn giá nhập tự động, nên một báo
    cáo mà mọi dòng Tracking đều Pending không phải một báo cáo "gần đúng", nó
    là một báo cáo không có giá vốn. Thà dừng và nói ra.
    """
    if sales is None:
        return None, {"daily_min_status": "NOT_PLANNED",
                      "daily_min_skip_reason": "NO_SALES_WORKBOOK"}

    # Import muộn: `app.modules` là phía KHÔNG chạm mạng của ranh giới
    # `ADR-101`, và giữ import ở đây làm rõ rằng module này gọi sang đó chứ
    # không phải ngược lại.
    from app.modules.pricing.daily_min.planning import (
        MAX_CONTRACT_DAYS, UnreadableSalesWorkbookError,
        plan_daily_min_request_for_workbook,
    )
    from app.modules.pricing.resolution.sources import (
        IDENTITY_STORE_LOG_PATH, load_tracking_catalog_capture,
        load_tracking_inv_map_capture,
    )
    from app.modules.product.identity.store import JsonlProductIdentityStore

    store = JsonlProductIdentityStore(log_path=REPO_ROOT / IDENTITY_STORE_LOG_PATH)
    try:
        plan = plan_daily_min_request_for_workbook(
            Path(sales),
            tracking_catalog=load_tracking_catalog_capture(catalog_path),
            identity_store_view=store.read_at_revision(store.current_revision()),
            tracking_inv_map=(
                load_tracking_inv_map_capture(inv_map_path)
                if inv_map_path is not None else None
            ),
            tracking_identity_authority=True,
        )
    except UnreadableSalesWorkbookError:
        # KHÔNG phải lỗi của Tracking, nên không dựng thành `TrackingUnavailable
        # Error`: đường nhập sổ ngay sau đây đọc lại đúng file này và báo lỗi ở
        # nơi người dùng hiểu được ("kiểm tra workbook và thử lại").
        return None, {"daily_min_status": "NOT_PLANNED",
                      "daily_min_skip_reason": "UNREADABLE_SALES_WORKBOOK"}
    if plan is None:
        return None, {"daily_min_status": "NOT_PLANNED",
                      "daily_min_skip_reason": "NO_TRACKING_IDENTITY_LINES"}
    if not plan.fits_one_contract_call:
        return None, {
            "daily_min_status": "NOT_PLANNED",
            "daily_min_skip_reason": "PERIOD_WIDER_THAN_CONTRACT",
            "daily_min_day_span": plan.day_span,
            "daily_min_max_days": MAX_CONTRACT_DAYS,
        }

    if post is None:
        post = capture_daily_min._http_poster(source_url or "", api_key)
    envelope = capture_daily_min.build_capture(
        post,
        product_codes=plan.product_codes,
        date_from=plan.date_from.isoformat(),
        date_to=plan.date_to.isoformat(),
        capture_id=f"LIVE-DMIN-{token}",
        captured_by=captured_by,
        source_system_ref="tracking/api/min-ngay (live pull-on-run)",
        captured_at=moment,
    )
    _raise_if_failed(envelope, node="daily_min")

    path = Path(out_dir) / f"{token}-daily-min.json"
    write_capture(envelope, path)
    return path, {
        "daily_min_status": "COMPLETE",
        "daily_min_capture_id": envelope["capture_id"],
        "daily_min_date_from": plan.date_from.isoformat(),
        "daily_min_date_to": plan.date_to.isoformat(),
        "daily_min_product_codes": len(plan.product_codes),
        "daily_min_query_revision": envelope["data"].get("query_revision"),
    }


def _raise_if_failed(envelope: dict[str, Any], *, node: str) -> None:
    if envelope.get("capture_status") != "COMPLETE":
        raise TrackingUnavailableError(
            f"Tracking pull-on-run thất bại ở node {node!r}: "
            f"{envelope.get('failure_reason', 'không rõ lý do')}",
            node=node,
            reason=str(envelope.get("failure_reason", "UNKNOWN")),
        )
