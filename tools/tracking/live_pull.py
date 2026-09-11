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
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

from tools.tracking import capture_daily_min, capture_inv_map, capture_tracking_catalog
from tools.tracking.capture_purchase_price_history import (
    API_KEY_ENV_VAR,
    CaptureError,
    _http_fetcher,
    build_capture as _build_history_capture,
    write_capture,
)

MAX_CONTRACT_WINDOWS = 12
"""Trần số ĐOẠN hỏi giá cho một lần chạy — 12 × 62 ngày ≈ hai năm.

Không phải một giới hạn kỹ thuật mà là một ranh giới nghiệp vụ: một lần chạy
phải kết thúc trong thời gian người ta còn ngồi đợi, và một sổ trải hơn hai năm
thì việc đúng là tách kỳ chứ không phải hỏi Tracking 60 lượt."""

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


class DailyMinPeriodTooWideError(RuntimeError):
    """Kỳ của workbook rộng hơn mức một lần chạy hỏi được.

    KHÔNG phải lỗi Tracking, nên nó KHÔNG dùng ``TrackingUnavailableError``:
    "vui lòng thử lại sau" là một lời khuyên sai — thử lại bao nhiêu lần cũng
    thế. Đây là một tính chất của SỔ, và việc cần làm là tách kỳ.
    """

    def __init__(self, message: str, *, day_span: int, windows: int) -> None:
        super().__init__(message)
        self.day_span = day_span
        self.windows = windows


@dataclass(frozen=True)
class LiveSelectedCaptures:
    """Cùng hình dạng ``app.owner_usability.SelectedCaptures`` — bên gọi
    (``run_owner_report``) không cần biết captures đến từ local hay live."""

    #: ``None`` khi lịch sử `tp/ton` không lấy được. Từ R1 nó KHÔNG còn quyết
    #: định giá nào (xem `_pull_daily_min` và `ADR-110` §6), nên một sự cố ở
    #: nhánh ấy không được phép chặn cả báo cáo.
    tracking_capture: Optional[Path]
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
    identity_store_view: Any = None,
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

    ``identity_store_view`` (R2) là ảnh chụp ĐÃ ĐÓNG BĂNG của log quyết định
    Product Identity, do bên gọi đọc MỘT lần cho cả lần chạy. Nó phải được
    truyền vào chứ không được tự dựng ở đây, và lý do là một lỗi thật:

        trên production, log quyết định nằm ở R2 (object store dùng chung),
        còn hàm này trước đây tự mở một ``JsonlProductIdentityStore`` trên
        ``data/product_identity/mappings.jsonl`` — tức đĩa ephemeral của
        container. Nó luôn đọc ra một store RỖNG. Hệ quả: mọi mã mà Owner vừa
        chọn trên giao diện KHÔNG lọt vào tập mã đi hỏi ``daily-min``, nên
        dòng đó thiếu giá ở đúng lần chạy mà việc phân loại lẽ ra đã cứu.

    ``None`` giữ nguyên hành vi cũ (đọc log cục bộ) cho máy Owner và cho test:
    ở đó đĩa là thật, một tiến trình, và log cục bộ ĐÚNG là nơi lưu.
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

    temp_paths: list[Path] = []
    try:
        return _pull(
            fetch=fetch, post=post, sales=sales, out_dir=out_dir, token=token,
            moment=moment, captured_by=captured_by, source_url=source_url,
            api_key=api_key, temp_paths=temp_paths,
            identity_store_view=identity_store_view,
        )
    except BaseException:
        # Một lần chạy hỏng KHÔNG được để lại authority thô của Tracking trên
        # đĩa máy chủ. `cleanup()` của bên gọi chỉ chạy khi hàm này TRẢ VỀ một
        # handle; ném ra thì bên gọi không có gì để dọn, và mỗi lần hỏng lại
        # bỏ lại thêm vài file (`S071 §10`). Dọn ở đây, cạnh chỗ ghi.
        for path in temp_paths:
            Path(path).unlink(missing_ok=True)
        raise


def _pull(
    *,
    fetch: Fetcher,
    post: Optional[Poster],
    sales: Optional[Path],
    out_dir: Path,
    token: str,
    moment: datetime,
    captured_by: str,
    source_url: Optional[str],
    api_key: Optional[str],
    temp_paths: list[Path],
    identity_store_view: Any = None,
) -> LiveSelectedCaptures:
    """Thân của ``pull_live_captures``. Tách ra để mọi đường thoát — kể cả
    ``raise`` từ tận trong kế hoạch hỏi giá — đi qua đúng một chỗ dọn dẹp."""
    # `purchase_price_history` là nguồn TUỲ CHỌN kể từ R1: nhánh giá của một
    # mã Tracking đi qua `_daily_min_branch`, và lịch sử `tp/ton` chỉ chạy khi
    # caller NÊU RÕ `legacy_tracking_history_authority=True`. Nó vẫn được chụp
    # và vẫn vào bằng chứng — để đối chiếu kết quả sinh trước R1 — nhưng để
    # một sự cố ở nhánh ấy chặn cả báo cáo là bắt hôm nay phụ thuộc vào một
    # nguồn hôm nay không dùng.
    history_envelope = _build_history_capture(
        fetch,
        capture_id=f"LIVE-PPH-{token}",
        captured_by=captured_by,
        source_system_ref="tracking/api/xuat (live pull-on-run)",
        captured_at=moment,
    )

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

    history_path: Optional[Path] = None
    if history_envelope.get("capture_status") == "COMPLETE":
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
        identity_store_view=identity_store_view,
    )
    if daily_min_path is not None:
        temp_paths.append(daily_min_path)

    evidence = {
        **daily_min_evidence,
        "purchase_price_history_capture_id": history_envelope["capture_id"],
        "purchase_price_history_captured_at": history_envelope["captured_at"],
        "purchase_price_history_status": history_envelope.get("capture_status"),
        "purchase_price_history_failure_reason": (
            history_envelope.get("failure_reason") if history_path is None else None
        ),
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
    identity_store_view: Any = None,
) -> tuple[Optional[Path], dict[str, Any]]:
    """Lập kế hoạch từ sổ rồi gọi ``daily-min-v1`` MỘT lượt cho lần chạy này.

    Ba kết cục, ba lý do KHÁC NHAU, không cái nào im lặng:

    * ``sales=None`` — không ai đưa sổ vào, nên không có kế hoạch nào để lập.
    * kế hoạch RỖNG — lần chạy này không có dòng nào mang identity Tracking,
      nên không có câu hỏi nào để đặt ra. Không phải lỗi.
    Kỳ rộng hơn 62 ngày KHÔNG còn là một trong ba kết cục ấy. Trước đây nó bỏ
    qua lượt hỏi giá và lần chạy vẫn ra một báo cáo — đầy đủ hình thức, không
    một giá vốn nào. Nay kỳ được chia thành các đoạn ≤ 62 ngày, hỏi từng đoạn,
    và chỉ gộp khi mọi đoạn cùng ``query_revision``. Rộng quá mức gộp được thì
    ném ``DailyMinPeriodTooWideError`` để bên gọi bảo người dùng TÁCH KỲ —
    không phải "thử lại sau", vì thử lại không giúp gì.

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
        UnreadableSalesWorkbookError, plan_daily_min_request_for_workbook,
    )
    from app.modules.pricing.resolution.sources import (
        IDENTITY_STORE_LOG_PATH, load_tracking_catalog_capture,
        load_tracking_inv_map_capture,
    )
    from app.modules.product.identity.store import JsonlProductIdentityStore

    view = identity_store_view
    if view is None:
        store = JsonlProductIdentityStore(
            log_path=REPO_ROOT / IDENTITY_STORE_LOG_PATH)
        view = store.read_at_revision(store.current_revision())
    try:
        plan = plan_daily_min_request_for_workbook(
            Path(sales),
            tracking_catalog=load_tracking_catalog_capture(catalog_path),
            identity_store_view=view,
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
    windows = plan.contract_windows()
    if len(windows) > MAX_CONTRACT_WINDOWS:
        # KHÔNG trả None ở đây. Trả None nghĩa là "chưa nối nguồn", và lần chạy
        # sẽ cho ra một báo cáo đầy đủ hình thức mà KHÔNG có lấy một giá vốn
        # nào — đúng thứ trông giống một báo cáo bình thường nhất.
        raise DailyMinPeriodTooWideError(
            f"Kỳ của sổ trải {plan.day_span} ngày, cần {len(windows)} lượt hỏi "
            f"giá (tối đa {MAX_CONTRACT_WINDOWS} mỗi lần chạy). Hãy tách sổ "
            "theo tháng hoặc quý rồi chạy lại từng kỳ.",
            day_span=plan.day_span, windows=len(windows),
        )

    if post is None:
        post = capture_daily_min._http_poster(source_url or "", api_key)

    # MỘT lượt gọi cho mỗi đoạn ≤ 62 ngày; mỗi đoạn tự đi hết các trang của nó.
    parts: list[dict[str, Any]] = []
    for dau, cuoi in windows:
        envelope = capture_daily_min.build_capture(
            post,
            product_codes=plan.product_codes,
            date_from=dau.isoformat(),
            date_to=cuoi.isoformat(),
            capture_id=f"LIVE-DMIN-{token}",
            captured_by=captured_by,
            source_system_ref="tracking/api/min-ngay (live pull-on-run)",
            captured_at=moment,
        )
        _raise_if_failed(envelope, node="daily_min")
        parts.append(envelope["data"])

    if len(parts) == 1:
        data = parts[0]
    else:
        # Gộp CHỈ khi mọi đoạn cùng `query_revision`. Lệch = database đã đổi
        # giữa các lượt, và ghép lại thì kỳ báo cáo mang giá của hai thời điểm
        # khác nhau. Đây là sự cố THOÁNG QUA (một lượt cron chạy đúng lúc), nên
        # nó đi đường `TrackingUnavailableError`: thử lại thật sự có tác dụng.
        try:
            data = capture_daily_min.gop_khoang(parts)
        except CaptureError as exc:
            raise TrackingUnavailableError(
                f"Tracking đổi trạng thái giữa các lượt hỏi giá của cùng một "
                f"kỳ: {exc}",
                node="daily_min", reason="REVISION_CHANGED_MID_CAPTURE",
            ) from exc

    envelope = {
        "capture_id": f"LIVE-DMIN-{token}",
        "captured_at": moment.isoformat(),
        "captured_by": captured_by,
        "source_system_ref": "tracking/api/min-ngay (live pull-on-run)",
        "capture_status": "COMPLETE",
        "data": data,
    }
    path = Path(out_dir) / f"{token}-daily-min.json"
    write_capture(envelope, path)
    return path, {
        "daily_min_status": "COMPLETE",
        "daily_min_capture_id": envelope["capture_id"],
        "daily_min_date_from": plan.date_from.isoformat(),
        "daily_min_date_to": plan.date_to.isoformat(),
        "daily_min_product_codes": len(plan.product_codes),
        "daily_min_windows": len(parts),
        "daily_min_query_revision": data.get("query_revision"),
        **tom_tat_tra_loi(data, so_ma=len(plan.product_codes)),
    }


def tom_tat_tra_loi(data: dict[str, Any], *, so_ma: int) -> dict[str, Any]:
    """Tóm tắt hợp đồng đã TRẢ LỜI gì — để một báo cáo đủ hình thức mà không có
    giá vốn tự nói ra vì sao.

    File capture bị xoá ngay sau lần chạy (`S071 §10`), còn `pending_reasons`
    trên từng dòng chỉ ghi `TRACKING_DAILY_MIN_PENDING` cho CẢ hai trường hợp
    khác hẳn nhau: Tracking không có bản ngày cho ngày ấy (`SOURCE_UNAVAILABLE`
    — cron chưa chụp/chưa dựng lại ngày đó) và Tracking có bản ngày nhưng mã
    ấy không có mốc giá (`NO_DATA`). Hai chuyện ấy cần hai hành động khác
    nhau, và không cái nào đọc ra được từ màn hình. Ghi thẳng vào bằng chứng
    của lần chạy: bao nhiêu bản ghi, bao nhiêu lỗi theo từng lý do, và những
    NGÀY mà mọi mã đều `SOURCE_UNAVAILABLE` — đó chính là danh sách ngày
    Tracking chưa quan sát.
    """
    records = data.get("records") or []
    errors = [e for e in (data.get("errors") or []) if isinstance(e, dict)]
    ly_do: Counter = Counter(str(e.get("reason") or "?") for e in errors)
    chua_quan_sat: Counter = Counter(
        str(e.get("effective_date"))
        for e in errors if e.get("reason") == "SOURCE_UNAVAILABLE"
    )
    return {
        "daily_min_records": len(records),
        "daily_min_errors": len(errors),
        "daily_min_error_reasons": dict(sorted(ly_do.items())),
        "daily_min_unobserved_dates": sorted(
            ngay for ngay, n in chua_quan_sat.items() if so_ma and n >= so_ma
        ),
    }


def _raise_if_failed(envelope: dict[str, Any], *, node: str) -> None:
    if envelope.get("capture_status") != "COMPLETE":
        raise TrackingUnavailableError(
            f"Tracking pull-on-run thất bại ở node {node!r}: "
            f"{envelope.get('failure_reason', 'không rõ lý do')}",
            node=node,
            reason=str(envelope.get("failure_reason", "UNKNOWN")),
        )
