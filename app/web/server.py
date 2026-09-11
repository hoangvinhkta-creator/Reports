"""Reports Web Shared Online Beta (S071) — thin server-side adapter.

Kiến trúc bắt buộc: Browser → tầng này → ``app.owner_usability``/``app.demo``
(đường production đã accepted) → artifact. Module này KHÔNG tính lại business
rule, KHÔNG tự phân loại AUTO/Review/Product Identity/PP — chỉ gọi đúng
adapter đã có (``run_owner_report``, cùng đường ``owner_launcher.py`` Tkinter
dùng) và trình bày lại ``ReportSummary`` đã authoritative.

S071 thay đổi so với S070 (Web Beta V1, local-only):

1. Run registry đổi từ ``dict`` process-local sang SQLite persistent
   (``app.web.run_registry``) — sống qua restart, chia sẻ được giữa nhiều
   viewer/nhiều worker process cùng phục vụ ``reports.tinphatcrm.com``.
2. Khi ``TRACKING_REPORT_SOURCE_URL``/``TRACKING_REPORT_API_KEY`` được cấu
   hình (triển khai cloud), mỗi lần chạy PULL LIVE từ Tracking
   (``tools.tracking.live_pull``) thay vì đọc capture cục bộ trên máy Owner —
   Owner Mac không còn nằm trên critical path. Khi CHƯA cấu hình (môi trường
   phát triển/local Owner), hành vi local S068–S070 giữ nguyên không đổi.
3. Thêm trang lịch sử run (``/history``) — sếp mở web thấy cùng run mới nhất
   và lịch sử mà Owner thấy, không phụ thuộc session trình duyệt của ai.

S071B thay tiếp SQLite + đĩa persistent bằng Cloudflare R2 khi đã cấu hình
(``app.web.storage_backend``, ``tools.storage.r2_store``) để runtime STATELESS
— xem ``docs/deployment/S071_DEPLOYMENT.md``. Module này KHÔNG biết đang chạy
trên backend nào; toàn bộ đọc/ghi đi qua ``store`` (``storage_backend.RunStore``).

Trust boundary: browser chỉ gửi workbook + lựa chọn feedback; browser không
bao giờ nhận secret, raw Tracking payload, hay đường dẫn filesystem tuyệt đối.
Download chỉ được resolve từ ``run_id`` qua registry do chính server tạo.
"""

from __future__ import annotations

import calendar
import hashlib
import io
import os
import re
import time
import uuid
from dataclasses import replace
from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

from flask import (
    Flask, abort, g, redirect, render_template, request, send_file, url_for,
)
from werkzeug.exceptions import HTTPException, RequestEntityTooLarge

from app import beta_feedback, beta_telemetry
from app.beta_presentation import REASON_DISPLAY_LABELS
from app.legacy import (
    LegacyImportError, is_standalone_year_workbook, parse_workbook,
    parse_year_workbook,
)
from app.legacy.models import SOURCE_AUTHORITY_YEAR
from app.owner_usability import (
    OwnerUsabilityError, run_owner_report, select_latest_valid_captures,
)
from app.owner_usability import SelectedCaptures
from app.modules.pricing.daily_min.snapshot import SUPPORTED_BUSINESS_TIMEZONE
from app.modules.pricing.resolution.sources import (
    load_tracking_catalog_capture, load_tracking_inv_map_capture,
)
from app.history import coverage as history_coverage
from app.history import models as history_models
from app.modules.reporting import (
    analysis_range, basket_metrics, brand_metrics, business_metrics,
    contribution, dashboard_metrics, line_type, product_metrics,
    reporting_sheets,
)
from app.modules.reporting.rate_routing import GIA_DUNG, gia_dung_workflow_applies
from app.modules.exporting import business_export
from app.modules.reporting import evaluation
from app.web import evaluation_presentation
from app.web import (
    analytics_presentation, analytics_queries, brand_identity,
    business_presentation, business_service, business_store,
    chart_gapfill, dashboard_presentation, history_store,
    history_writer, identity_gateway, legacy_presentation, legacy_reference,
    line_identity, mutation_guard, order_api, order_revision, period_lock,
    product_taxonomy, request_timing, revenue_timeline, run_registry,
    catalog_display, sales_presentation, sales_queries, snapshot_presentation,
    storage_backend, workspace_imei, workspace_presentation,
)
import tools.db as history_db
from tools.db import HistoryConfigurationError
from tools.storage.errors import CorruptRunRecordError, StorageUnavailableError
from tools.tracking import live_pull

#: `abort(<mã>)` trên đường `/api/` → mã lỗi ổn định của hợp đồng. Mã HTTP
#: nào không có tên riêng ở đây rơi về `VALIDATION_ERROR`: client vẫn bật
#: được nhánh, và mã HTTP thật vẫn có mặt trong trường `status`.
_API_STATUS_CODES = {
    400: mutation_guard.VALIDATION_ERROR,
    403: mutation_guard.PERMISSION_DENIED,
    404: mutation_guard.NOT_FOUND,
    409: mutation_guard.PERIOD_CLOSED,
    422: mutation_guard.VALIDATION_ERROR,
    503: mutation_guard.SOURCE_PENDING,
}

REPO_ROOT = Path(__file__).resolve().parents[2]

#: MIME của `.xlsx`. Viết ra ở đây một lần thay vì rải chuỗi qua các route —
#: gõ sai nó làm trình duyệt mở file như văn bản thay vì tải về.
XLSX_MIMETYPE = (
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


def _export_file_name(period_value: str, scope: str) -> str:
    """Tên file tải về: nói rõ KỲ nào và LÁT nào, không có ký tự lạ.

    Tên file đi ra khỏi hệ thống và thường được lưu cạnh nhau hàng chục cái;
    một tên không nói kỳ và phạm vi là một tên sẽ bị mở nhầm.
    """
    safe = "".join(
        char if char.isalnum() or char in "-_" else "-" for char in scope)
    safe = "-".join(part for part in safe.split("-") if part) or "toan-ky"
    return f"bao-cao-{period_value or 'toan-bo'}-{safe}.xlsx"

# S071 Deployment Gate: một số nhà cung cấp hosting managed (vd Render Web
# Service) chỉ cho gắn ĐÚNG MỘT persistent disk trên mỗi service — registry
# SQLite và artifact/upload/tracking-tạm phải cùng nằm dưới một gốc mount
# duy nhất để cả hai sống qua restart/redeploy. `REPORTS_DATA_ROOT` cho phép
# production trỏ toàn bộ state runtime vào gốc disk đó; mặc định (không đặt
# biến này) giữ NGUYÊN các đường dẫn tương đối REPO_ROOT đã dùng từ S070 —
# không đổi hành vi local/test nào.
DATA_ROOT = Path(os.environ.get("REPORTS_DATA_ROOT") or REPO_ROOT)
UPLOAD_DIR = DATA_ROOT / "data" / "uploads"
ARTIFACT_DIR = (DATA_ROOT / "outputs" / "reports").resolve()
TRACKING_TEMP_DIR = DATA_ROOT / "data" / "tracking_live_tmp"

# Beta technical safety limit — không phải quyết định nghiệp vụ của Owner.
# Workbook kế toán thật (mẫu đã audit) nằm dưới vài MB; 25MB để dư biên độ.
MAX_UPLOAD_BYTES = 25 * 1024 * 1024

HISTORY_PAGE_LIMIT = 50

# `R3` — hai provenance có nghĩa "chính Owner đã quyết con số này". Đọc thẳng
# từ `business_metrics` để bộ lọc không bao giờ lệch với ngữ nghĩa đã freeze.
_OWNER_EDITED_PROVENANCE = (
    business_metrics.PROVENANCE_MANUAL,
    business_metrics.PROVENANCE_MANUAL_OVERRIDE,
)


# `DEC-PHB02-08` §2 — "hôm nay" của không gian làm việc, đọc qua MỘT hàm.
#
# Kỳ mặc định là THÁNG DƯƠNG LỊCH HIỆN TẠI, kể cả khi tháng đó chưa có dòng
# bán nào (`§45`: Owner đặt Target trước lần nạp sổ đầu tiên). Một hằng số
# ngày tháng nằm rải rác trong route sẽ khiến hành vi đó không kiểm được mà
#: Múi giờ NGHIỆP VỤ — cùng vùng mà hợp đồng `daily-min-v1` đã freeze cho
#: ranh giới ngày của giá MIN (`daily_min.snapshot.SUPPORTED_BUSINESS_
#: TIMEZONE`). Dùng lại đúng chuỗi đó thay vì một `timedelta(hours=7)` viết
#: cứng: chuỗi vùng đi qua cơ sở dữ liệu múi giờ của hệ thống, nên nó vẫn
#: đúng nếu quy ước giờ của Việt Nam đổi, còn một hằng số +7 thì không.
BUSINESS_TIMEZONE = ZoneInfo(SUPPORTED_BUSINESS_TIMEZONE)


# không đợi sang tháng sau; gom về một hàm là cách test nói được "giả sử hôm
# nay là ngày 3".
def _today() -> date:
    """NGÀY NGHIỆP VỤ hôm nay, theo múi giờ Việt Nam.

    R4 — trước bản này hàm trả `date.today()`, tức ngày theo đồng hồ của MÁY
    CHỦ. Container production chạy UTC, nên từ 17:00 giờ Việt Nam tới nửa đêm
    hàm trả về NGÀY HÔM TRƯỚC: tháng mặc định của không gian làm việc sai vào
    tối ngày cuối tháng, và `as_of` của báo cáo đánh giá lệch một ngày mỗi
    tối — làm "còn thiếu mỗi ngày" chia cho số ngày còn lại sai, mỗi buổi
    tối, mà không có gì trên màn hình báo.

    `Asia/Ho_Chi_Minh` là múi giờ nghiệp vụ DUY NHẤT của hệ thống này, đã
    được `daily_min.snapshot.SUPPORTED_BUSINESS_TIMEZONE` freeze cho ranh
    giới ngày của giá MIN. Ngày bán và ngày báo cáo phải cắt theo CÙNG một
    ranh giới, nếu không một đơn bán tối muộn sẽ nhận giá của một ngày và
    được đếm vào một ngày khác.
    """
    return datetime.now(BUSINESS_TIMEZONE).date()



# Biên kiểm tra của tham số `ky` (`§3`: "Date/year validation must remain
# safe"). Một năm ngoài khoảng này không phải một kỳ báo cáo của doanh nghiệp
# này; nhận nó chỉ để rồi dựng một trang rỗng là mời gọi URL rác.
_MIN_WORKSPACE_YEAR = 2000
_MAX_WORKSPACE_YEAR = 2100


def _guarded(fn, *args, **kwargs):
    """Gọi ``fn`` (một lời gọi store) và biến lỗi storage (R2 unavailable/
    JSON hỏng) thành HTTP 503 rõ ràng — KHÔNG âm thầm coi như "không tìm
    thấy"/"lịch sử rỗng" (S071B: phải phân biệt lỗi storage với dữ liệu
    thật sự rỗng)."""
    try:
        return fn(*args, **kwargs)
    except history_store.LegacyHistoryAmbiguityError as exc:
        # `DEC-181` §6 — nguồn lịch sử mâu thuẫn KHÔNG được nói thành "lưu
        # trữ tạm thời không khả dụng": đổ lỗi cho hạ tầng vì một mâu thuẫn
        # dữ liệu là cách chắc chắn nhất để không ai đi sửa nó. 409 mang
        # theo đúng câu giải thích của tầng repository.
        abort(409, description=str(exc))
    except period_lock.PeriodClosedError as exc:
        # R3 §5 — kỳ đã chốt. 409 (mâu thuẫn trạng thái), KHÔNG phải 503:
        # đây không phải lỗi hạ tầng và "thử lại sau" là một câu sai — thao
        # tác này sẽ hỏng y hệt cho tới khi Owner MỞ LẠI kỳ kèm lý do.
        abort(409, description=str(exc))
    except (StorageUnavailableError, CorruptRunRecordError,
            history_store.HistoryUnavailableError):
        abort(503)


def _guard_lines(service, *details) -> None:
    """Chặn một lần ghi quyết định rơi vào KỲ ĐÃ CHỐT (R3 §5).

    Chặn theo NGÀY BÁN của chính dòng, không theo kỳ đang xem: khung nhìn
    "toàn bộ dữ liệu" không có kỳ, và sửa một dòng của tháng đã chốt từ màn
    hình đó vẫn phải bị chặn.

    Dòng không có ngày bán rơi ngoài mọi kỳ — đúng ngữ nghĩa kỳ đã freeze ở
    PRA-003 — nên nó không bị chốt kỳ nào khoá.
    """
    _guarded(lambda: [service.guard_line_open(detail) for detail in details])


def _readiness_text() -> str:
    """Đúng nguyên semantics/wording đã review truthful ở owner_launcher.py.

    Chế độ cloud (live pull cấu hình xong) luôn "sẵn sàng" theo nghĩa cục bộ
    — sẵn sàng thật hay không quyết định LÚC CHẠY (mỗi lần fetch Tracking),
    không phải bằng cách quét capture cũ trên đĩa máy chủ.
    """
    if live_pull.is_configured():
        return "Sẵn sàng — dữ liệu Tracking lấy trực tiếp (live) mỗi lần chạy"
    try:
        select_latest_valid_captures()
    except Exception:
        return "Chưa sẵn sàng"
    return "Có capture hợp lệ trên máy"


def _review_reason_lines(counts: dict[str, int]) -> list[tuple[str, int]]:
    return [
        (REASON_DISPLAY_LABELS.get(reason, reason), count)
        for reason, count in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    ]


def _build_view(summary, *, dropped_lines: int = 0) -> dict:
    return {
        "input_orders": summary.input_orders,
        "auto_orders": summary.auto_orders,
        "review_orders": summary.review_orders,
        "error_count": summary.error_count,
        "dropped_lines": dropped_lines,
        "accounting_rate": f"{summary.order_accounting_rate:.0%}",
        "review_reason_lines": _review_reason_lines(summary.review_reason_counts),
    }


def _record_telemetry(run_id: str, summary, duration_ms: int) -> None:
    # Byproduct vận hành, không phải core path — không chặn Owner nếu ghi lỗi.
    try:
        record = beta_telemetry.build_run_record(
            run_id=run_id, summary=summary, processing_duration_ms=duration_ms,
        )
        beta_telemetry.record_run(record)
    except Exception:
        pass


def _safe_display_name(filename: str) -> str:
    """Chỉ giữ basename để hiển thị — không bao giờ đường dẫn client gửi lên
    (chống lộ cấu trúc thư mục máy khách, không liên quan tên file lưu trên
    đĩa server — tên đó luôn do server sinh, xem ``/run``)."""
    name = Path(filename).name or "workbook.xlsx"
    return name[:120]


def _selected_period(periods: list[tuple[int, Optional[int]]]) -> Optional[tuple[int, Optional[int]]]:
    """Kỳ đang xem: lấy từ query string nếu hợp lệ, nếu không thì kỳ mới nhất.

    Chỉ chấp nhận kỳ THỰC SỰ có trong dữ liệu đã nhập — một kỳ do người dùng
    gõ tay mà không có dữ liệu sẽ rơi về ``None`` để trang hiện trạng thái
    rỗng trung thực, thay vì một bảng toàn số 0.
    """
    raw = request.args.get("ky") or ""
    if not raw:
        return periods[0] if periods else None
    year_text, _, month_text = raw.partition("-")
    try:
        chosen = (int(year_text), int(month_text) if month_text else None)
    except ValueError:
        return None
    return chosen if chosen in periods else None


def _select_captures_for_run(
    sales: Optional[Path] = None, identity_store_view=None,
) -> tuple[Optional[SelectedCaptures], Optional[dict], Optional[live_pull.LiveSelectedCaptures]]:
    """Trả về ``(captures, tracking_evidence, live_handle)``.

    ``live_handle`` khác ``None`` khi captures đến từ live pull — caller phải
    gọi ``live_handle.cleanup()`` sau khi dùng xong (finally), bất kể thành
    công hay lỗi, để không giữ authority thô của Tracking lâu hơn một lần
    chạy trên đĩa máy chủ (S071 §10).

    ``sales`` (R1) là workbook của chính lần chạy này. Nó BẮT BUỘC có mặt trên
    đường chạy báo cáo: ảnh chụp MIN theo ngày bán phụ thuộc tập mã và khoảng
    ngày của kỳ, nên không có sổ thì không lập được kế hoạch hỏi giá và mọi
    dòng Tracking sẽ Pending. Những nơi gọi hàm này KHÔNG để chạy báo cáo (ví
    dụ đọc danh mục cho bảng chọn mặt hàng) truyền ``None`` một cách có chủ ý:
    chúng không cần giá, và bắt chúng gọi hợp đồng giá là gọi mạng cho một câu
    hỏi không ai đặt ra.

    ``identity_store_view`` (R2) là ảnh chụp đã đóng băng của log quyết định
    Product Identity — xem ``run_report``. Nó quyết định TẬP MÃ đi hỏi
    ``daily-min``, nên bỏ trống nó nghĩa là mọi mặt hàng Owner vừa phân loại
    trên giao diện KHÔNG được hỏi giá ở chính lần chạy đó.
    """
    if not live_pull.is_configured():
        return None, None, None
    # `STAB-01` — đây là ĐÚNG một cửa duy nhất ra Tracking trên đường
    # request (mọi caller đi qua hàm này), nên span `tracking` đặt ở đây
    # đo đủ mà không cần rải mã đo khắp các route.
    with request_timing.span("tracking"):
        live = live_pull.pull_live_captures(
            out_dir=TRACKING_TEMP_DIR, sales=sales,
            identity_store_view=identity_store_view)
    captures = SelectedCaptures(
        tracking_capture=live.tracking_capture,
        tracking_catalog=live.tracking_catalog,
        tracking_inv_map=live.tracking_inv_map,
        tracking_daily_min=live.tracking_daily_min,
    )
    return captures, live.evidence, live


def _build_history(env=None) -> Optional[history_store.LegacyRepository]:
    """Dựng repository history nếu môi trường đã sẵn sàng.

    ``REPORTS_REQUIRE_HISTORY_DB=1`` (production) → lỗi cấu hình được ném
    tiếp ra ngoài và app KHÔNG khởi động: thà chết lúc khởi động còn hơn
    chạy lên rồi hiển thị lịch sử rỗng trong khi thật ra không có database.
    Ngoài chế độ đó (máy dev chưa `alembic upgrade head`), trả ``None`` và
    các trang legacy nói thẳng là history store CHƯA cấu hình — vẫn không
    bao giờ giả vờ "chưa có dữ liệu".
    """
    values = os.environ if env is None else env
    required = (values.get("REPORTS_REQUIRE_HISTORY_DB") or "").strip() == "1"
    if not required and not (values.get("HISTORY_DATABASE_URL") or "").strip():
        # Chưa cấu hình gì: chỉ dùng SQLite mặc định nếu database ĐÃ được
        # tạo bằng `alembic upgrade head`. Không tự tạo file/thư mục database
        # khi khởi động — một database rỗng do app tự sinh ra sẽ khiến trang
        # legacy trông như "chưa nhập gì" trong khi thật ra chưa ai migrate.
        if not history_db.default_sqlite_path(values).exists():
            return None
    try:
        return history_store.build(values)
    except HistoryConfigurationError:
        if required:
            raise
        return None


SNAPSHOT_PAGE_LIMIT = 50

FLAG_PAGE_LIMIT = 200


def _build_snapshots(
    legacy: Optional[history_store.LegacyRepository],
) -> Optional[history_store.SnapshotRepository]:
    """Repository PRA-002 trên ĐÚNG engine mà LegacyRepository đang dùng.

    Dùng chung một ``Engine`` là điều kiện để lịch sử snapshot và bản nhập
    legacy nằm trong cùng một database — hai origin tách bảng, không tách nơi
    lưu. Không có history store thì cũng không có snapshot: ``None``, và tầng
    trên nói thẳng là run không được lưu lịch sử.
    """
    if legacy is None:
        return None
    return history_store.build_snapshots(engine=legacy.engine, verify_schema=False)


def _looks_like_year_workbook(path: Path) -> bool:
    """Workbook có phải bản lịch sử MỘT NĂM độc lập không.

    Chỉ đọc DANH SÁCH TÊN SHEET (``read_only``), không phân tích ô nào — nên
    phép thử này rẻ và không thể làm hỏng đường nhập hiện có: file nào không
    khớp hình dạng đó vẫn đi đúng nhánh cũ.
    """
    from openpyxl import load_workbook

    book = load_workbook(path, read_only=True)
    try:
        return is_standalone_year_workbook(book.sheetnames)
    finally:
        book.close()


def _workbook_year(workbook) -> str:
    for entry in workbook.sheets_imported:
        if entry.get("year"):
            return entry["year"]
    return "?"


def create_app(
    *,
    db_path: Path = run_registry.DEFAULT_DB_PATH,
    store: Optional[storage_backend.RunStore] = None,
    history: Optional[history_store.LegacyRepository] = None,
    snapshots: Optional[history_store.SnapshotRepository] = None,
) -> Flask:
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES
    if store is None:
        store = storage_backend.build(db_path=db_path, artifact_dir=ARTIFACT_DIR)
    app.config["RUN_REGISTRY"] = store
    # Tên cục bộ khác tên endpoint: một view function tên ``history`` sẽ che
    # mất biến này trong closure của create_app.
    history_repo = history if history is not None else _build_history()
    app.config["HISTORY_STORE"] = history_repo
    snapshot_repo = snapshots if snapshots is not None else _build_snapshots(history_repo)
    app.config["SNAPSHOT_STORE"] = snapshot_repo
    # PHB-03 — Summary/Employee nghiệp vụ. Dùng CHUNG engine với snapshot repo:
    # quyết định của Owner về một dòng hàng chỉ có nghĩa cạnh chính dòng đó,
    # nên chúng phải sống trong cùng một database, cùng một transaction domain.
    business = (
        None if snapshot_repo is None
        else business_service.BusinessReportService(
            engine=snapshot_repo.engine,
            store=business_store.BusinessDecisionStore(snapshot_repo.engine),
        )
    )
    app.config["BUSINESS_SERVICE"] = business
    # `DEC-185` — thẩm quyền Product Identity của Phase 1. Dựng MỘT lần cho
    # cả app: `JsonlProductIdentityStore` giữ khoá liên-tiến-trình trên chính
    # file log, nên hai instance trong cùng một tiến trình chỉ tổ nạp lại
    # cùng một log hai lần. Store không dựng được (thư mục chỉ-đọc) ⟹ `None`,
    # và màn hình nói "chưa phân loại được từ đây" thay vì sập.
    try:
        identity_store = identity_gateway.build_store()
    except Exception:  # noqa: BLE001 — xem chú thích trên
        identity_store = None
    app.config["IDENTITY_STORE"] = identity_store
    # Cache-bust CSS bằng vân tay NỘI DUNG, tính một lần lúc khởi động tiến
    # trình. `url_for('static', ...)` của Flask không tự thêm phiên bản vào
    # URL — phía trước production có Cloudflare cache theo phần mở rộng
    # `.css`, nên một lần deploy đổi NỘI DUNG file mà giữ NGUYÊN URL sẽ bị
    # trình duyệt/CDN tiếp tục phục vụ bản CŨ, trong khi HTML (không cache
    # dài) đã đổi — hai tầng lệch nhau đúng như sự cố "HTML mới, CSS cũ".
    # Thêm `?v=<hash 10 ký tự>` vào URL khiến mỗi lần nội dung CSS đổi trở
    # thành một URL MỚI hoàn toàn, buộc phải tải lại — nội dung không đổi
    # thì hash không đổi, không xả cache một cách không cần thiết.
    _css_path = Path(__file__).parent / "static" / "css" / "tinphat-ui.css"
    app.jinja_env.globals["ASSET_VERSION"] = hashlib.sha256(
        _css_path.read_bytes()).hexdigest()[:10]
    # `TASK-OWNER-UIUX-004` — cùng cơ chế cache-bust cho file JS mới
    # (`app.js`), lý do giống hệt CSS ở trên.
    _js_path = Path(__file__).parent / "static" / "js" / "app.js"
    app.jinja_env.globals["JS_ASSET_VERSION"] = hashlib.sha256(
        _js_path.read_bytes()).hexdigest()[:10]

    @app.context_processor
    def _inject_fragment_flag():
        """`TASK-OWNER-UIUX-004` §6 — điều hướng TRONG một tab không tải lại
        trang; chuyển TAB vẫn tải lại (`§4`/`§5` — nav chính đứng ngoài
        `#app-content`, xem `layout.html`).

        Lớp tăng cường ở `app.js` gắn header `X-Fragment: 1` vào mọi
        fetch() nó tự phát ra; `layout.html` đọc `partial` từ đây để quyết
        định có dựng lại khung trang (doctype/head/nav) hay chỉ trả đúng
        nội dung bên trong `#app-content`. Route KHÔNG cần biết gì về việc
        này — không route nào phải tự thêm tham số `partial` vào
        `render_template`, nên không có chỗ nào quên làm điều đó.
        """
        return {"partial": request.headers.get("X-Fragment") == "1"}
    app.jinja_env.globals["LEGACY_BADGE"] = legacy_presentation.ORIGIN_BADGE
    app.jinja_env.globals["LEGACY_BADGE_TITLE"] = legacy_presentation.ORIGIN_TITLE
    app.jinja_env.globals["LEGACY_PROVENANCE"] = legacy_reference.PROVENANCE
    app.jinja_env.globals["LEGACY_PROVENANCE_LABEL"] = legacy_reference.PROVENANCE_LABEL
    app.jinja_env.globals["LEGACY_PROVENANCE_NOTE"] = legacy_reference.PROVENANCE_NOTE
    app.jinja_env.globals["LEGACY_HISTORY_LABEL"] = legacy_presentation.HISTORY_LABEL
    app.jinja_env.globals["LEGACY_HISTORY_LOCKED_LABEL"] = \
        legacy_presentation.HISTORY_LOCKED_LABEL
    app.jinja_env.globals["LEGACY_HISTORY_NOTE"] = legacy_presentation.HISTORY_NOTE
    app.jinja_env.globals["PIPELINE_BADGE"] = analytics_presentation.ORIGIN_BADGE
    # `DEC-185` §F-03 — dấu "sổ thô" của các trang không phải chỉ tiêu chính.
    for _name in ("RAW_SURFACE_BADGE", "RAW_SURFACE_NOTE", "RAW_SURFACE_TITLE"):
        app.jinja_env.globals[_name] = getattr(analytics_presentation, _name)
    app.jinja_env.globals["PIPELINE_BADGE_TITLE"] = analytics_presentation.ORIGIN_TITLE
    app.jinja_env.globals["QUANTITY_NOTE"] = analytics_presentation.QUANTITY_NOTE
    app.jinja_env.globals["ORDER_COLUMN_NOTE"] = analytics_presentation.ORDER_COLUMN_NOTE
    app.jinja_env.globals["BOTH_SOURCES_NOTE"] = analytics_presentation.BOTH_SOURCES_NOTE
    for _name in ("MULTI_DATE_NOTE", "MULTI_EMPLOYEE_NOTE", "NO_ORDERS_NOTE",
                  "PRODUCT_GROUPING_NOTE", "PRODUCT_ITEM_COUNT_LABEL",
                  "PRODUCT_ORDER_COUNT_NOTE", "REASON_LABEL"):
        app.jinja_env.globals[_name] = getattr(sales_presentation, _name)
    for _name in ("CONVERTED_SALES_NOTE", "DERIVED_COLUMNS_NOTE",
                  "DISCOUNT_ROW_NOTE",
                  "INCOMPLETE_NOTE",
                  # TASK-OWNER-UIUX-002 — chú giải (?) của bốn thẻ chỉ tiêu.
                  "KPI_PROFIT_NOTE",
                  "NET_SALES_NOTE", "OFFICIAL_NOTE",
                  # TASK-UIUX-001 — nhãn của thẻ "Tổng số SP" trên Báo cáo
                  # từng KHÔNG được đăng ký, nên thẻ đó hiện một con số
                  # không tên (Jinja render biến chưa định nghĩa thành rỗng).
                  "QUALIFYING_QUANTITY_LABEL",
                  "QUALIFYING_QUANTITY_NOTE", "UNKNOWN_EMPLOYEE",
                  "UNRESOLVED_EMPLOYEE_NOTE",
                  # PHB-05 — chú thích của Target: viết MỘT lần ở tầng trình
                  # bày, dùng lại ở cả trang Target lẫn trang Nhân viên.
                  "TARGET_COMPANY_DEFERRED_NOTE", "TARGET_FORMULA_NOTE",
                  "TARGET_LEGACY_READ_ONLY_NOTE", "TARGET_NOTE",
                  "TARGET_NO_PERIOD_NOTE", "TARGET_UNIT_NOTE",
                  "TARGET_ZERO_VS_BLANK_NOTE"):
        app.jinja_env.globals[_name] = getattr(business_presentation, _name)
    # R4 — chú giải của báo cáo đánh giá. Cùng kỷ luật đã dùng cho PHB-05/06:
    # câu chữ viết MỘT lần ở tầng trình bày (kiểm được bằng test giá trị
    # thuần), template chỉ in ra. Một `_name` viết sai ở đây làm Jinja render
    # ra CHUỖI RỖNG chứ không báo lỗi — đúng lỗi đã xảy ra một lần với
    # `QUALIFYING_QUANTITY_LABEL` — nên `tests/test_r4_evaluation_web.py`
    # kiểm rằng từng câu này thật sự có mặt trên trang.
    for _name in ("LOSS_NOTE", "LOWEST_MARGIN_NOTE", "MONEY_UNIT_NOTE",
                  "ORDERS_NOT_ADDITIVE_NOTE", "PAGE_TITLE", "RUN_RATE_NOTE",
                  "SAME_DAYS_NOTE", "TARGET_SCOPE_NOTE"):
        app.jinja_env.globals[_name] = getattr(evaluation_presentation, _name)
    app.jinja_env.globals["BUSINESS_ORDER_COLUMN_NOTE"] = \
        business_presentation.ORDER_COLUMN_NOTE
    # PHB-06 — chú thích của bảng thương hiệu. Cùng kỷ luật: viết MỘT lần ở
    # tầng trình bày, template chỉ hiện ra.
    for _name in ("BRAND_EXCLUDED_NOTE", "BRAND_NO_TARGET_NOTE",
                  "BRAND_ORDER_COLUMN_NOTE"):
        app.jinja_env.globals[_name] = getattr(business_presentation, _name)
    for _name in ("BRAND_SOURCE_NOTE", "BRAND_UNAVAILABLE_NOTE"):
        app.jinja_env.globals[_name] = getattr(brand_identity, _name)
    # TASK-UIUX-001 — trạng thái coverage của snapshot viết bằng CHỮ trên tab
    # Dữ liệu (mã enum giữ ở tooltip), dùng lại đúng nhãn của trang snapshot.
    app.jinja_env.globals["coverage_label"] = history_coverage.coverage_label
    app.jinja_env.globals["coverage_short_label"] = history_coverage.coverage_short_label
    # PHB-07 — chú thích của bảng cơ cấu. Cùng kỷ luật: viết MỘT lần ở tầng
    # trình bày, template chỉ hiện ra.
    for _name in ("COMPOSITION_EXCLUDED_NOTE", "COMPOSITION_NO_PROFIT_SHARE_NOTE",
                  "COMPOSITION_ONE_PERIOD_NOTE", "COMPOSITION_ORDER_COLUMN_NOTE",
                  "COMPOSITION_SHARE_NOTE", "COMPOSITION_UNIT_NOTE",
                  "COMPOSITION_UNRESOLVED_NOTE"):
        app.jinja_env.globals[_name] = getattr(business_presentation, _name)
    # `DEC-PHB02-08` — chú thích của không gian làm việc. Cùng kỷ luật: viết
    # MỘT lần ở tầng trình bày, template chỉ hiện ra.
    for _name in ("EMPTY_PERIOD_NOTE", "EXCLUDED_NOTE",
                  "EXCLUDE_CONFIRM_POINTS", "EXCLUDE_CONFIRM_QUESTION",
                  "GIA_DUNG_CONFIRM_POINTS", "GIA_DUNG_CONFIRM_QUESTION",
                  "REMOVED_IN_SOURCE_NOTE",
                  "RESTORE_CONFIRM_POINTS", "RESTORE_CONFIRM_QUESTION",
                  "PROGRESS_NOTE", "TARGET_KVND_NOTE",
                  "TARGET_NOT_KVND_NOTE", "TARGET_UNIT_LABEL"):
        app.jinja_env.globals[_name] = getattr(workspace_presentation, _name)

    def _require_history() -> history_store.LegacyRepository:
        if history_repo is None:
            # Không phải "chưa có dữ liệu" — là chưa có nơi lưu dữ liệu.
            abort(503)
        return history_repo

    def _legacy_history_context():
        """Ngữ cảnh LEGACY_HISTORY dùng chung — MỘT nguồn, hai file provenance.

        `DEC-181`: trang bình thường không còn "bản đang xem". Cái thay chỗ
        nó là khoảng kỳ đã khoá cộng danh sách file provenance — thông tin
        để ĐỐI CHIẾU, không phải một bộ chọn nguồn.
        """
        if history_repo is None:
            return None
        return legacy_presentation.history_overview(
            _guarded(history_repo.available_periods),
            _guarded(history_repo.history_sources),
        )

    def _legacy_page(template: str, **context):
        return render_template(
            template,
            history_configured=history_repo is not None,
            legacy_history=_legacy_history_context(),
            **context,
        )

    def _page(*, error: Optional[str] = None, run_id: Optional[str] = None,
             not_found: bool = False, feedback_ok: bool = False, status: int = 200):
        record = _guarded(store.get_run, run_id) if run_id else None
        return render_template(
            "index.html",
            readiness=_readiness_text(),
            error=error,
            result=record.view if record and record.view else None,
            run_id=run_id if record else None,
            run_created_at=record.created_at if record else None,
            workbook_display_name=record.workbook_display_name if record else None,
            not_found=not_found,
            feedback_ok=feedback_ok,
            history_configured=snapshot_repo is not None,
            feedback_categories=beta_feedback.FEEDBACK_CATEGORIES,
        ), status

    @app.get("/")
    def landing():
        """R1 (`GỠ TRÙNG UX`) — `/` mở BÁO CÁO, không còn màn hình upload.

        Kỳ mới nhất của Current Engine (`analytics_queries`, cùng nguồn
        `/kinh-doanh` đã dùng) LUÔN thắng — trong production các kỳ số mới
        đều mới hơn 08/2026, nên hành vi R1 giữ nguyên.

        `DEC-181` §17 nới đúng một bước: KHÔNG có kỳ số mới nào mà
        LEGACY_HISTORY lại có kỳ ⟹ mở kỳ lịch sử mới nhất, dùng LẠI bộ giải
        nguồn của R2. Không có engine hợp nhất hai nguồn nào được dựng ở
        đây: hai nhánh vẫn tách hẳn, chỉ chọn nhánh nào có kỳ để mở.
        Không nguồn nào có kỳ ⟹ về thẳng `/kinh-doanh` không kèm `ky`, để
        trang đó tự nói tình trạng của nó (503/rỗng).
        """
        ky = None
        if snapshot_repo is not None:
            periods = _guarded(analytics_queries.available_periods, snapshot_repo.engine)
            if periods:
                ky = business_presentation.period_value(periods[0])
        if ky is None and history_repo is not None:
            legacy_periods = _guarded(history_repo.available_periods)
            if legacy_periods:
                year, month = legacy_periods[0]
                return redirect(url_for("sellers", ky=f"{year}-{month:02d}"))
        return redirect(url_for("business_summary", **({"ky": ky} if ky else {})))

    @app.get("/du-lieu/chay-bao-cao")
    def index():
        """Chạy báo cáo (upload workbook, xem kết quả) — dời từ `/` sang đây
        dưới DỮ LIỆU (R1 §3): đây là công cụ vận hành, không phải màn hình
        Owner/Director đọc báo cáo. Tên hàm ``index`` giữ nguyên để mọi
        ``url_for("index", ...)`` hiện có (trang Dữ liệu, POST /run, feedback)
        tự trỏ đúng đường mới, không phải sửa từng nơi gọi.
        """
        run_id = request.args.get("run_id") or None
        found = run_id is not None and _guarded(store.get_run, run_id) is not None
        return _page(
            run_id=run_id if found else None,
            not_found=run_id is not None and not found,
            feedback_ok=request.args.get("feedback") == "ok",
        )

    @app.get("/du-lieu")
    def data_tab():
        """Tab "Dữ liệu": các lần chạy pipeline VÀ nguồn lịch sử đã khoá.

        Hai origin nằm trong hai bảng tách biệt trên trang, mỗi bảng ghi rõ
        nguồn — không bao giờ trộn số pipeline với số cũ vào một danh sách.

        `DEC-181`: phần lịch sử là MỘT nguồn đã khoá, nên trang không còn
        liệt kê "các bản nhập legacy để chọn" — nó liệt kê các file
        PROVENANCE của nguồn đó. Ô tải workbook legacy cũng đã gỡ: chủ dự án
        chốt không thêm nguồn lịch sử nào nữa. "CHẠY BÁO CÁO MỚI" (luồng số
        mới) KHÔNG bị đụng tới.
        """
        runs = _guarded(store.list_runs, limit=HISTORY_PAGE_LIMIT)
        snapshots, runs_with_snapshot = [], set()
        if snapshot_repo is not None:
            snapshots = _guarded(snapshot_repo.list_snapshots, limit=SNAPSHOT_PAGE_LIMIT)
            # Một run có trên store mà KHÔNG có snapshot nghĩa là lần ghi lịch
            # sử đó đã hỏng. Trang phải nói ra, không im lặng bỏ qua.
            runs_with_snapshot = _guarded(
                snapshot_repo.run_ids_with_snapshot, [run.run_id for run in runs],
            )
        return _legacy_page(
            "du_lieu.html", runs=runs, snapshots=snapshots,
            snapshots_configured=snapshot_repo is not None,
            runs_with_snapshot=runs_with_snapshot,
            imported=request.args.get("imported") or None,
            error=request.args.get("loi") or None,
        )

    def _snapshot_page(snapshot_id: str, *, message=None, error=None, status=200):
        """Trang chỉ-đọc của MỘT snapshot: coverage, số đếm reconcile, cờ.

        Không hiển thị PII: bảng cờ chỉ mang khoá đơn/dòng, loại cờ, các
        trường nghiệp vụ đã đổi và TÊN NHÂN VIÊN bán hàng — tên/SĐT/địa chỉ
        khách không có mặt trong bất kỳ bảng nào của PRA-002 nên cũng không có
        đường nào ra tới đây.

        R5 §2 — `imei` cũng KHÔNG ra tới đây, dù nó nằm trong `detail_json`
        của cờ dưới database: `snapshot_presentation.NOISE_FIELDS` cắt nó ở
        tầng trình bày, và đó là một trong hai lý do danh sách trường ấy tồn
        tại (lý do kia là nhiễu). `DEC-211` mở IMEI ở ĐÚNG workspace nhân
        viên, và trang này không nằm trong phạm vi đó.
        """
        if snapshot_repo is None:
            abort(503)
        snapshot = _guarded(snapshot_repo.get_snapshot, snapshot_id)
        if snapshot is None:
            abort(404)
        flags = _guarded(snapshot_repo.list_flags, snapshot_id=snapshot_id,
                         limit=FLAG_PAGE_LIMIT)
        totals = _guarded(
            snapshot_repo.current_totals,
            date_from=snapshot["detected_date_min"], date_to=snapshot["detected_date_max"],
        )
        return _legacy_page(
            "snapshot.html", snapshot=snapshot, totals=totals,
            review_rows=snapshot_presentation.review_rows(
                flags, _flag_locations(flags)),
            review_count=snapshot_presentation.review_count(flags),
            review_note=snapshot_presentation.REVIEW_NOTE,
            coverage_label=history_coverage.coverage_label(snapshot["coverage_state"]),
            can_confirm=snapshot["coverage_state"] != history_models.CONFIRMED_COMPLETE,
            confirm_message=message, confirm_error=error,
        ), status

    def _flag_locations(flags: list[dict]) -> dict:
        """Vị trí hiện hành của các dòng mà bảng cờ nói tới (R5 §2).

        Trả về `{}` khi vertical nghiệp vụ chưa dựng được — trang snapshot là
        một trang ĐỐI CHIẾU và phải mở được kể cả khi phần báo cáo đang hỏng;
        khi đó mỗi cờ hiện "không còn dòng hiện hành để mở", đúng câu mà tầng
        trình bày dành sẵn cho trường hợp không tra được.
        """
        if business is None:
            return {}
        service = business
        keys = [(flag["order_key"], flag["product_key"],
                 flag["occurrence_index"])
                for flag in flags
                if not snapshot_presentation.is_noise_only(flag)]
        return _guarded(service.locate_lines, keys)

    @app.get("/du-lieu/snapshot/<snapshot_id>")
    def snapshot_detail(snapshot_id: str):
        return _snapshot_page(
            snapshot_id, message=request.args.get("xac_nhan") or None,
        )

    @app.post("/du-lieu/snapshot/<snapshot_id>/xac-nhan-du")
    def confirm_snapshot(snapshot_id: str):
        """Xác nhận TƯỜNG MINH rằng sổ này đầy đủ cho một khoảng ngày.

        Đây là hành động DUY NHẤT nâng coverage lên ``CONFIRMED_COMPLETE``, và
        nó luôn là một hành động riêng của con người sau khi đã nhìn thấy phạm
        vi hệ thống đo được (mục 7.3, DEC-171 #4). Không có suy diễn nào ở đây:
        không tick ô → 400; khoảng ngày không bao trọn dữ liệu → 400; xác nhận
        lần hai → 409. Mọi nhánh từ chối đều KHÔNG ghi gì.
        """
        if snapshot_repo is None:
            abort(503)
        try:
            confirmation = _guarded(
                snapshot_repo.confirm_coverage, snapshot_id,
                start=history_coverage.parse_iso_date(request.form.get("tu_ngay")),
                end=history_coverage.parse_iso_date(request.form.get("den_ngay")),
                confirmed=request.form.get("xac_nhan") == "1",
                confirmed_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            )
        except KeyError:
            abort(404)
        except history_store.CoverageAlreadyConfirmedError as exc:
            return _snapshot_page(snapshot_id, error=str(exc), status=409)
        except history_store.CoverageRangeError as exc:
            return _snapshot_page(snapshot_id, error=str(exc), status=400)
        return redirect(url_for(
            "snapshot_detail", snapshot_id=snapshot_id,
            # R5 §1 — câu này phải nói ra HỆ QUẢ THẬT của cái nút vừa bấm.
            # Câu cũ ("đã đưa vào Review, KHÔNG xoá và VẪN tính") mô tả đúng
            # hành vi trước R5 và nay đã sai theo chiều nguy hiểm nhất: người
            # dùng đọc nó rồi tin rằng tổng không đổi, trong khi tổng vừa
            # giảm đúng số tiền của những dòng ấy.
            xac_nhan=(
                f"Đã xác nhận sổ này đầy đủ cho {confirmation.confirmed_range_start} "
                f"→ {confirmation.confirmed_range_end}. "
                + (
                    f"{confirmation.removed_candidates} dòng cũ trong khoảng này không "
                    "còn trong sổ vừa xác nhận nên đã được TẠM LOẠI khỏi mọi con số "
                    "kinh doanh; xem danh sách “Không còn trong file đầy đủ” trên tab "
                    "nhân viên. Lịch sử KHÔNG bị xoá — nạp lại một sổ có chứa dòng đó "
                    "thì cảnh báo tự mất và các con số tự khôi phục."
                    if confirmation.removed_candidates
                    else "Mọi dòng cũ trong khoảng này đều có mặt trong sổ vừa xác "
                         "nhận — không dòng nào bị loại và không con số nào đổi."
                )
            ),
        ))

    @app.get("/history")
    def history_redirect():
        # Đường cũ của S071 — giữ để link/bookmark đã phát ra không gãy.
        return redirect(url_for("data_tab"), code=302)

    @app.post("/du-lieu/legacy")
    def import_legacy():
        """LEGACY_HISTORY đã khoá vĩnh viễn ở đúng hai nguồn provenance —
        workbook 2025 độc lập + workbook 01–08/2026 (`DEC-181`, phần bổ sung
        thẩm quyền chủ dự án). Đây là một RÀNG BUỘC NGHIỆP VỤ, không phải
        access-control: không nguồn Legacy thứ ba, dù hợp lệ định dạng đến
        đâu. Route GIỮ ĐĂNG KÝ (tương thích liên kết/vận hành cũ) nhưng từ
        chối MỌI request ở đây, TRƯỚC khi đọc file, parse workbook, hay chạm
        `repository` — không `create_import()`, không DB write, không đổi
        `is_current`, không side effect nào khác.
        """
        abort(409, description=(
            "Dữ liệu lịch sử đã khóa. Hệ thống chỉ sử dụng nguồn lịch sử "
            "2025 và 01-08/2026 đã được chốt."
        ))

    # `POST /du-lieu/legacy/<id>/chon` ĐÃ GỠ (`DEC-181` §2): chọn "bản đang
    # xem" là chính quy trình chủ dự án bác bỏ. Không có route nào thay thế
    # nó — lịch sử đã khoá ở MỘT nguồn logic, nên không còn gì để chọn.
    # `LegacyRepository.set_current()` vẫn còn ở tầng repository như metadata
    # tương thích ngược (§7), nhưng không còn đường nào từ web gọi tới nó.

    def _pipeline_period(periods: list[tuple[int, int]]) -> Optional[tuple[int, int]]:
        """Kỳ SỐ MỚI đang xem. Mặc định "Toàn bộ dữ liệu" (``None``).

        Mặc định đó là lựa chọn có chủ đích: nó là kỳ DUY NHẤT không bao giờ
        giấu bớt dòng nào và không cần một kỳ so sánh, nên trang mở ra lần đầu
        không thể nói sai. Một ``ky`` không có trong dữ liệu cũng rơi về đây —
        trang hiện tổng thật, thay vì một bảng toàn số 0 cho một tháng bịa.
        """
        raw = request.args.get("ky") or ""
        year_text, _, month_text = raw.partition("-")
        try:
            chosen = (int(year_text), int(month_text))
        except ValueError:
            return None
        return chosen if chosen in periods else None

    def _pipeline_view(engine) -> dict:
        """Kỳ + tổng kỳ + tổng kỳ trước, dùng chung cho Tổng quan và Nhân viên."""
        periods = _guarded(analytics_queries.available_periods, engine)
        period = _pipeline_period(periods)
        bounds = analytics_queries.month_bounds(*period) if period else (None, None)
        previous = None
        if period is not None:
            # Kỳ so sánh LUÔN được truy vấn khi đang xem một tháng: chính kết
            # quả "kỳ trước không có dòng nào" là thứ trang phải nói ra, nên
            # không được bỏ qua truy vấn đó.
            previous = _guarded(analytics_queries.period_totals, engine,
                                **dict(zip(("date_from", "date_to"),
                                           analytics_queries.month_bounds(
                                               *analytics_presentation.previous_period(period)))))
        return {
            "periods": analytics_presentation.period_options(periods),
            "period": period, "bounds": bounds,
            "selected_period": analytics_presentation.period_value(period),
            "totals": _guarded(analytics_queries.period_totals, engine,
                               date_from=bounds[0], date_to=bounds[1]),
            "previous": previous,
        }

    @app.get("/tong-quan")
    def overview():
        """Tổng quan SỐ MỚI — 10 ô đã qua Minimum-Value Filter, không hơn."""
        if snapshot_repo is None:
            abort(503)
        view = _pipeline_view(snapshot_repo.engine)
        return render_template(
            "tong_quan.html", periods=view["periods"],
            selected_period=view["selected_period"],
            overview=analytics_presentation.overview(
                view["totals"], view["previous"], period=view["period"],
                undated=_guarded(analytics_queries.undated_lines, snapshot_repo.engine),
            ),
        )

    @app.get("/ban-hang")
    def sales():
        """Danh sách đơn của kỳ — bậc đầu tiên của đường truy vết.

        Cùng bộ chọn kỳ, cùng ngữ nghĩa kỳ với Tổng quan: Owner chọn "Tháng
        09/2026" ở cả hai trang và phải thấy CÙNG một tập đơn. Không có kho dữ
        liệu ⟹ 503 giống hệt ``/tong-quan`` — lỗi database không bao giờ được
        hiện thành "chưa có dữ liệu".
        """
        if snapshot_repo is None:
            abort(503)
        view = _pipeline_view(snapshot_repo.engine)
        return render_template(
            "ban_hang.html", periods=view["periods"],
            selected_period=view["selected_period"],
            period_label=analytics_presentation.period_label(view["period"]),
            columns=sales_presentation.ORDER_COLUMNS,
            orders=sales_presentation.order_rows(
                _guarded(sales_queries.order_list, snapshot_repo.engine,
                         date_from=view["bounds"][0], date_to=view["bounds"][1])),
        )

    @app.get("/ban-hang/<order_key>")
    def sales_order(order_key: str):
        """Chi tiết MỘT đơn: khối tổng hợp, các dòng hiện hành, lý do kiểm tra.

        Mã đơn không có dòng hiện hành nào trong kỳ ⟹ 404. KHÔNG dựng một
        trang rỗng trông như "đơn này không có dòng nào": hai tình huống đó
        khác nhau, và chỉ một trong hai là sự thật.
        """
        if snapshot_repo is None:
            abort(503)
        view = _pipeline_view(snapshot_repo.engine)
        detail = _guarded(sales_queries.order_detail, snapshot_repo.engine, order_key,
                          date_from=view["bounds"][0], date_to=view["bounds"][1])
        if detail is None:
            abort(404)
        return render_template(
            "ban_hang_chi_tiet.html", periods=view["periods"],
            selected_period=view["selected_period"],
            period_label=analytics_presentation.period_label(view["period"]),
            line_columns=sales_presentation.LINE_COLUMNS,
            order=sales_presentation.order_detail(detail),
        )

    @app.get("/san-pham")
    def products():
        """SẢN PHẨM — mặt hàng trên chứng từ (TASK-PRA-005), mặc định sắp
        Doanh thu giảm dần. Gộp theo mô tả thô đã chuẩn hoá trên chứng từ
        (OD-PRA005-01, DEC-173) — KHÔNG phải canonical Product Identity.
        Bao gồm TẤT CẢ dòng chứng từ, kể cả dịch vụ/phí (OD-PRA005-02) —
        KHÔNG lọc bằng ``is_non_product_line()``. Không có kho dữ liệu ⟹ 503
        giống hệt ``/tong-quan``/``/ban-hang``.
        """
        if snapshot_repo is None:
            abort(503)
        view = _pipeline_view(snapshot_repo.engine)
        rows = _guarded(sales_queries.product_totals, snapshot_repo.engine,
                        date_from=view["bounds"][0], date_to=view["bounds"][1])
        return render_template(
            "san_pham.html", periods=view["periods"],
            selected_period=view["selected_period"],
            period_label=analytics_presentation.period_label(view["period"]),
            columns=sales_presentation.PRODUCT_COLUMNS,
            summary=sales_presentation.product_summary(rows, view["totals"]),
            products=sales_presentation.product_rows(rows),
        )

    @app.get("/nhan-vien")
    def sellers():
        """Ma trận tháng × người bán từ Summary cũ (đơn vị nghìn đồng).

        ``?nguon=moi`` chuyển sang bảng SỐ MỚI. MỌI giá trị khác — kể cả không
        có tham số và các giá trị lạ — giữ NGUYÊN VẸN đường legacy: bảo toàn
        bằng chứng non-regression của TASK-PRA-001 quan trọng hơn sự đối xứng
        của route, và một tham số gõ sai không được phép thành HTTP 500.
        """
        if request.args.get("nguon") == "moi" and snapshot_repo is not None:
            view = _pipeline_view(snapshot_repo.engine)
            return render_template(
                "nhan_vien.html", pipeline_view=True,
                periods=view["periods"], selected_period=view["selected_period"],
                columns=analytics_presentation.EMPLOYEE_COLUMNS,
                period_label=analytics_presentation.period_label(view["period"]),
                rows=analytics_presentation.employee_rows(
                    _guarded(analytics_queries.employee_totals, snapshot_repo.engine,
                             date_from=view["bounds"][0], date_to=view["bounds"][1]),
                    view["totals"],
                ),
            )
        if history_repo is None:
            return _legacy_page("nhan_vien.html", periods=[], selected=None,
                                rows=[], columns=legacy_presentation.MATRIX_COLUMNS,
                                pipeline_view=False), 503
        periods = _guarded(history_repo.available_periods)
        selected = _selected_period(periods)
        rows = (
            _guarded(history_repo.query_summary, selected[0], selected[1])
            if selected else []
        )
        return _legacy_page(
            "nhan_vien.html", periods=periods, selected=selected,
            rows=legacy_presentation.matrix(rows),
            columns=legacy_presentation.MATRIX_COLUMNS,
            pipeline_view=False,
        )

    @app.get("/doanh-so-ngay")
    def daily_sales():
        """Doanh số theo ngày từ DataChart cũ (đơn vị VND nguyên)."""
        if history_repo is None:
            return _legacy_page("doanh_so_ngay.html", periods=[], selected=None,
                                days=[], monthly=None, monthly_cells={}), 503
        periods = _guarded(history_repo.available_periods)
        selected = _selected_period(periods)
        days, monthly = [], None
        if selected and selected[1]:
            days = legacy_presentation.daily_grid(
                _guarded(history_repo.query_daily, selected[0], selected[1])
            )
            monthly = next(
                (row for row in _guarded(history_repo.query_monthly_reference, selected[0])
                 if row["month"] == selected[1]),
                None,
            )
        return _legacy_page(
            "doanh_so_ngay.html", periods=periods, selected=selected, days=days,
            monthly=monthly, monthly_cells=legacy_presentation.monthly_cells(monthly),
        )

    @app.get("/lich-su")
    def legacy_reference_page():
        """PHB-04 — Tham chiếu lịch sử: kỳ legacy, hợp đồng, điều hướng.

        Trang này KHÔNG ghi gì và KHÔNG gọi pipeline. Nó đọc đúng ba thứ đã
        có: kỳ Summary cũ, dòng tham chiếu tháng của DataChart, và danh mục kỳ
        của số mới — rồi xếp cạnh nhau với nhãn origin. Không kỳ nào bị hợp
        nhất thành một con số duy nhất: `DEC-166 E` cấm cộng chung số cũ với
        số mới, và PHB-04 không xin ngoại lệ nào cho điều đó.

        Danh mục kỳ số mới chỉ có khi snapshot store đã cấu hình. Thiếu nó,
        trang vẫn hiện đầy đủ phần legacy và nói rõ phần số mới chưa đọc được
        — KHÔNG im lặng hiện một danh sách chỉ có legacy như thể đó là tất cả.
        """
        if history_repo is None:
            return _legacy_page(
                "lich_su.html", reference_rows=[], reference_years=[],
                reference_has_value=False, navigation=[], pipeline_configured=False,
                summary_periods=[], summary_years=[], unread=[],
                comparison=legacy_reference.comparison_summary(),
                reference_contract=legacy_presentation.contract_rows(
                    legacy_reference.REFERENCE_YEAR_CONTRACT),
                workbook_contract=legacy_presentation.contract_rows(
                    legacy_reference.SUMMARY_SHEET_CONTRACT),
            ), 503

        monthly = _guarded(history_repo.query_monthly_reference)
        periods = legacy_reference.reference_periods(monthly)
        summary_periods = _guarded(history_repo.available_periods)
        pipeline_periods = (
            _guarded(analytics_queries.available_periods, snapshot_repo.engine)
            if snapshot_repo is not None else []
        )
        # Mọi dòng Summary đã nhập, MỌI năm. `DEC-177`: chi tiết theo nhân
        # viên của một năm lịch sử sống ở đây, nên trang phải đọc cả năm
        # lịch sử chứ không chỉ năm workbook.
        all_summary = _guarded(history_repo.query_all_summary)
        years = legacy_reference.summary_years(all_summary)
        # `DEC-178` + `DEC-181` — mỗi năm ghi rõ nó đọc từ FILE nào. Đây là
        # chỗ quy tắc "một kỳ ⟹ một nguồn" trở thành thứ chủ dự án NHÌN
        # THẤY, không chỉ là một dòng trong tài liệu. Không còn năm nào rơi
        # về "bản đang xem".
        source_by_year = {
            year.year: _guarded(history_repo.history_source_for_year, year.year)
            for year in years
        }
        return _legacy_page(
            "lich_su.html",
            reference_rows=legacy_presentation.reference_rows(periods),
            reference_years=legacy_reference.reference_years(periods),
            reference_has_value=legacy_reference.has_any_value(periods),
            summary_periods=summary_periods,
            summary_years=legacy_presentation.summary_year_rows(
                years, all_summary, source_by_year),
            # Phần "chưa đọc được" đo trên MỌI file provenance đang phục vụ
            # lịch sử, không riêng một bản: bỏ sót của workbook 2025 phải
            # hiện ra kể cả khi trang đang nói về 2026.
            unread=[
                sheet
                for source in _guarded(history_repo.history_sources)
                for sheet in legacy_reference.unread_sheets(
                    source.get("sheets_imported"))
            ],
            navigation=legacy_reference.period_navigation(
                legacy_summary_periods=summary_periods,
                legacy_reference_periods=periods,
                pipeline_periods=pipeline_periods,
            ),
            pipeline_configured=snapshot_repo is not None,
            comparison=legacy_reference.comparison_summary(),
            reference_contract=legacy_presentation.contract_rows(
                legacy_reference.REFERENCE_YEAR_CONTRACT),
            workbook_contract=legacy_presentation.contract_rows(
                legacy_reference.SUMMARY_SHEET_CONTRACT),
        )

    @app.get("/giai-thich")
    def giai_thich():
        """R1 §7 — một nơi DUY NHẤT cho định nghĩa KPI lặp lại trên nhiều
        trang báo cáo (Tổng số SP, DS quy đổi, tiền hiển thị nghìn đồng,
        huy hiệu SỐ MỚI). Trang này KHÔNG đọc dữ liệu, không có kỳ, không
        có nhân viên — chỉ prose tĩnh, nên không cần snapshot/history store.
        """
        return render_template("giai_thich.html")

    # ------------------------------------------------------------------
    # PHB-03 — Summary + Employee Business Parity V1.
    #
    # Bốn trang, MỘT vertical: Tổng hợp (kỳ) · Nhân viên (nhân viên + kỳ) ·
    # Hoàn thiện giá nhập · Phân loại Gia dụng. Cố ý KHÔNG dựng một tab cho mỗi
    # nhân viên (`R-E1`, `P1`) — 56 sheet tay trở thành MỘT trang có bộ chọn.
    # ------------------------------------------------------------------

    def _require_business():
        if business is None:
            # Không phải "chưa có dữ liệu" — là chưa có nơi lưu dữ liệu.
            abort(503)
        return business

    def _business_period_choice(periods: list[tuple[int, int]]):
        """Kỳ đang xem, đọc từ `request.values` chứ không riêng query string.

        Các trang này có FORM POST (ghi giá nhập, tick Gia dụng) mang `ky`
        trong BODY. Đọc riêng query string ở đó sẽ âm thầm rơi về "Toàn bộ dữ
        liệu" và chuyển hướng người dùng sang một kỳ họ không chọn. Ngoài
        nguồn đọc, ngữ nghĩa giữ đúng `_pipeline_period`: giá trị lạ hoặc kỳ
        không có trong dữ liệu đều rơi về `None` ("Toàn bộ dữ liệu"), vì đó là
        kỳ DUY NHẤT không giấu bớt dòng nào.
        """
        raw = request.values.get("ky") or ""
        year_text, _, month_text = raw.partition("-")
        try:
            chosen = (int(year_text), int(month_text))
        except ValueError:
            return None
        return chosen if chosen in periods else None

    def _legacy_previous_month(period, previous) -> Optional[dict]:
        """Mốc "So tháng trước" lấy từ SỐ CŨ — `DEC-180` §9.

        Đây là chỗ DUY NHẤT của vertical nghiệp vụ chạm tới hai origin, và nó
        cố ý nằm ở tầng RÁP chứ không trong `business_*`: ba module kia phải
        tiếp tục không biết gì về số cũ, nếu không một ngày nào đó cổng so
        sánh liên-origin sẽ chặn nhầm một phép so cùng-engine.

        Bốn cửa, mỗi cửa đóng một cách sai khác nhau:

        1. Chỉ chạy khi đang xem MỘT tháng. "Toàn bộ dữ liệu" không có tháng
           liền trước nào để so.
        2. Chỉ chạy khi tháng trước KHÔNG có dòng số mới nào. Một tháng đã có
           số mới không bao giờ bị số cũ thay chỗ.
        3. Đi qua `authoritative_period_sales`: MỘT kỳ ⟹ MỘT nguồn ⟹ MỘT giá
           trị. Không cộng hai nguồn, không trộn dòng thô.
        4. Giá trị trả về đã chuẩn hoá về VND bằng `to_vnd()` trong chính hàm
           đó — `Summary` là kVND, số mới là VND, và quên hệ số 1.000 ở đây
           cho ra một tỉ lệ trông như thật.

        Trang NHÂN VIÊN cố ý KHÔNG dùng đường này: số cũ của một tháng là
        tổng của CẢ CÔNG TY, nên đem nó làm mẫu số cho doanh thu của một người
        là một phép so sai. Ghép tên người bán trong sổ cũ với nhân viên hiện
        hành là một bài toán ánh xạ riêng, chưa có quyết định nào cho phép.
        """
        if period is None or history_repo is None:
            return None
        if previous is not None and previous.totals.lines > 0:
            return None
        year, month = analytics_presentation.previous_period(period)
        summary_rows = _guarded(history_repo.query_summary, year, month)
        monthly_rows = _guarded(history_repo.query_monthly_reference, year)
        resolved = legacy_reference.authoritative_period_sales(
            year=year, month=month,
            summary_rows=summary_rows, monthly_rows=monthly_rows)
        if resolved is None:
            return None
        return {
            "sales_revenue": resolved.sales_vnd,
            "origin_label": resolved.origin_label,
            "source_label": resolved.source_label,
        }

    def _summary_period_default(periods: list[tuple[int, int]]):
        """Kỳ mở đầu của trang BÁO CÁO khi Owner chưa chọn gì.

        `TASK-OWNER-UIUX-002` — Owner mở tab Báo cáo để xem THÁNG NÀY, không
        phải để bấm thêm một lần nữa vào bộ chọn kỳ. Ba ràng buộc giữ cho
        việc này chỉ là một MẶC ĐỊNH chứ không phải một ngữ nghĩa mới:

        1. Chỉ áp dụng khi tham số `ky` VẮNG MẶT hoàn toàn. `ky=` rỗng là
           Owner đã chủ động chọn "Toàn bộ dữ liệu" — mặc định không được
           ghi đè một lựa chọn.
        2. Chỉ chọn tháng hiện tại khi tháng đó THẬT SỰ có trong dữ liệu.
           Mở sẵn một tháng rỗng ngay đầu tháng, trước lần nạp sổ đầu tiên,
           sẽ cho Owner một trang trắng thay vì tình hình kinh doanh.
        3. Không có tháng hiện tại ⟹ giữ nguyên hành vi cũ ("Toàn bộ dữ
           liệu"), tức là vẫn có số để đọc ngay.

        Mọi trang khác (`gia-nhap`, `gia-dung`, `target`…) KHÔNG đi qua đây:
        chúng có form POST mang `ky` trong body và ngữ nghĩa kỳ của chúng
        không đổi.
        """
        if "ky" in request.values:
            return None
        current = (_today().year, _today().month)
        return current if current in periods else None

    def _business_period(*, default_period=None) -> dict:
        """Kỳ đang xem + số của kỳ đó + số của kỳ liền trước.

        Kỳ so sánh LUÔN được truy vấn khi đang xem một tháng: chính kết quả
        "tháng trước không có dòng nào" là thứ `DEC-PHB02-07` bắt phải nói ra,
        nên không được bỏ qua truy vấn đó.
        """
        service = _require_business()
        periods = _guarded(analytics_queries.available_periods, snapshot_repo.engine)
        period = _business_period_choice(periods)
        if period is None and default_period is not None:
            period = default_period(periods)
        bounds = analytics_queries.month_bounds(*period) if period else (None, None)
        data = _guarded(service.period, date_from=bounds[0], date_to=bounds[1],
                        period=period)
        previous = None
        if period is not None:
            previous_bounds = analytics_queries.month_bounds(
                *analytics_presentation.previous_period(period))
            previous = _guarded(service.period, date_from=previous_bounds[0],
                                date_to=previous_bounds[1])
        return {
            "service": service, "period": period, "bounds": bounds, "data": data,
            "previous": previous,
            "previous_fallback": _legacy_previous_month(period, previous),
            "periods": business_presentation.period_options(periods),
            "selected_period": business_presentation.period_value(period),
        }

    def _legacy_month_totals() -> list[dict]:
        """Tổng bán VND của MỌI kỳ số cũ, mỗi kỳ đúng MỘT nguồn.

        Đi qua `legacy_reference.authoritative_period_sales` chứ không đọc
        thẳng bảng: hàm đó là nơi `DEC-180` §9 sống ("MỘT kỳ ⟹ MỘT nguồn ⟹
        MỘT giá trị"), và nó cũng là nơi đơn vị được đổi về VND đúng MỘT lần.
        Đọc thẳng `legacy_summary_row` ở đây sẽ vừa cộng hai nguồn vừa bỏ
        quên hệ số 1.000 của Summary — hai lỗi cùng cho ra một đường cong
        trông hoàn toàn hợp lý.

        Hai câu truy vấn cho TOÀN BỘ lịch sử, không phải một câu mỗi kỳ.
        """
        if history_repo is None:
            return []
        periods = _guarded(history_repo.available_periods)
        if not periods:
            return []
        summary_rows = _guarded(history_repo.query_all_summary)
        monthly_rows = _guarded(history_repo.query_monthly_reference)
        totals = []
        for year, month in periods:
            if month is None:
                continue
            resolved = legacy_reference.authoritative_period_sales(
                year=year, month=month,
                summary_rows=summary_rows, monthly_rows=monthly_rows)
            if resolved is None or resolved.sales_vnd is None:
                continue
            totals.append({"year": year, "month": month,
                           "sales_vnd": resolved.sales_vnd})
        return totals

    def _legacy_daily_rows(months: list[tuple[int, int]]) -> list[dict]:
        """Dòng `legacy_daily_sales` của các kỳ số cũ — bằng chứng TỪNG NGÀY.

        Chỉ được gọi ở mức gộp Ngày/Tuần: ở mức Tháng trở lên nó không thêm
        thông tin nào mà vẫn tốn đúng bấy nhiêu câu truy vấn.
        """
        if history_repo is None:
            return []
        rows = []
        for year, month in months:
            rows.extend(_guarded(history_repo.query_daily, year, month))
        return rows

    def _chart_anchor(period, details, legacy_months: list[dict]):
        """Mép phải của biểu đồ — ngày MUỘN NHẤT có bằng chứng, bất kỳ nguồn nào.

        `revenue_timeline.anchor_date` trả lời câu này cho sổ NẠP. Ở đây câu
        hỏi rộng hơn đúng một vế: nếu tháng có bằng chứng muộn nhất chỉ còn
        bản ghi lịch sử, mép phải vẫn phải là tháng đó — nếu không, một sổ
        chưa nạp dòng nào sẽ vẽ ra một cửa sổ trống trơn.

        Ngày đại diện của một tháng lịch sử là ngày CUỐI tháng: bằng chứng
        tháng chỉ nói tổng của cả tháng, nên mọi ngày trong đó đều đúng như
        nhau, và ngày cuối là ngày giữ trọn mốc tháng ấy trong cửa sổ.
        """
        anchor = revenue_timeline.anchor_date(period, details)
        candidates = [anchor] if anchor is not None else []
        for entry in legacy_months:
            year, month = int(entry["year"]), int(entry["month"])
            candidates.append(
                date(year, month, calendar.monthrange(year, month)[1]))
        return max(candidates) if candidates else None

    def _revenue_chart(view: dict) -> dict:
        """`DEC-185` — MỘT biểu đồ doanh thu theo thời gian cho trang Báo cáo.

        ## Biểu đồ nhìn TOÀN BỘ dòng thời gian, không theo kỳ đang chọn

        Đây là một quyết định, không phải một sự bỏ sót. Bộ chọn kỳ ở trên
        trả lời "tháng này ra sao"; biểu đồ trả lời "xu hướng đi thế nào" —
        và hai mức gộp Quý/Năm mà Owner yêu cầu KHÔNG có nghĩa gì bên trong
        một tháng. Ràng biểu đồ vào kỳ đang chọn sẽ khiến ba trong năm cái
        nút luôn vẽ ra đúng một cột.

        Khi kỳ đang chọn là "Toàn bộ dữ liệu", tập dòng của biểu đồ CHÍNH LÀ
        tập đã dựng cho trang — không truy vấn lại lần thứ hai.
        """
        service = view["service"]
        # `TASK-OWNER-UIUX-002` — trang Báo cáo mở ở mức NGÀY: câu hỏi đầu
        # tiên của Owner là "tháng này đang đi thế nào", và một biểu đồ mở ở
        # mức Tháng trả lời câu đó bằng đúng một điểm. Bốn mức còn lại giữ
        # nguyên và vẫn đổi được bằng chính các nút cũ.
        granularity = revenue_timeline.parse_granularity(
            request.args.get("muc"), default=revenue_timeline.DAY)
        data = (view["data"] if view["period"] is None
                else _guarded(service.period))
        legacy_months = _legacy_month_totals()
        legacy_days = []
        gapfill_days = ()
        if granularity in (revenue_timeline.DAY, revenue_timeline.WEEK):
            legacy_days = _legacy_daily_rows(
                [(item["year"], item["month"]) for item in legacy_months])
            # `DEC-216` — nguồn lấp lỗ hổng CHỈ được nối ở đây, ở mức
            # Ngày/Tuần, và chỉ cho biểu đồ doanh thu. Ở mức Tháng trở lên
            # tổng tháng chính thức đã có mặt; nối thêm nó vào đó là cộng hai
            # nguồn cho cùng một tháng.
            gapfill_days = chart_gapfill.daily_rows()
        points = revenue_timeline.series(
            data.details, granularity=granularity,
            legacy_months=legacy_months, legacy_days=legacy_days,
            gapfill_days=gapfill_days)
        # R5 §3 (`DEC-R5-02`) — Ngày/Tuần/Tháng/Quý vẽ HAI cửa sổ liền kề
        # cùng độ dài. `series()` ở trên vẫn tính TOÀN BỘ điểm bằng đúng
        # engine doanh thu cũ (bất biến Σ = totals và mọi kiểm chứng origin
        # không đổi); phần dưới đây chỉ CHỌN và XẾP các điểm đó vào hai cửa
        # sổ — không một phép cộng doanh thu nào được viết lần thứ hai.
        # `DEC-211` — mép phải là ngày có dữ liệu MỚI NHẤT của cả dòng thời
        # gian, kể cả khi ngày đó chỉ có bản ghi lịch sử. `anchor_date` chỉ
        # nhìn được `details` (sổ nạp); một sổ mới hoàn toàn chưa nạp gì thì
        # nó trả về đường lui theo kỳ, và biểu đồ sẽ neo vào một tháng KHÔNG
        # có mốc nào — đúng cái dải trống mà quyết định này bỏ đi. Nên mốc
        # cuối của lịch sử được đưa vào cùng phép `max` ở đây, chứ không phải
        # bằng một quy tắc neo thứ hai bên trong `revenue_timeline`.
        anchor = _chart_anchor(view["period"], data.details, legacy_months)
        paired = revenue_timeline.paired_series(
            points, granularity=granularity, anchor=anchor,
            confirmed_ranges=_guarded(snapshot_repo.confirmed_ranges)
            if snapshot_repo is not None else ())
        if paired is not None:
            return business_presentation.paired_revenue_chart(
                paired, granularity=granularity,
                has_legacy_months=bool(legacy_months),
                undated=revenue_timeline.undated_count(data.details))
        # Mức NĂM giữ nguyên đường một chuỗi của `TASK-OWNER-UIUX-003` §2:
        # Owner không yêu cầu cửa sổ so sánh ở mức đó, và "8 năm so với 8 năm
        # trước" là một câu hỏi sổ này chưa có bằng chứng để trả lời.
        points = revenue_timeline.window_points(
            points, granularity=granularity, period=view["period"])
        return business_presentation.revenue_chart(
            points, granularity=granularity,
            has_legacy_months=bool(legacy_months),
            undated=revenue_timeline.undated_count(data.details),
            window_label=revenue_timeline.window_label(
                granularity, view["period"]),
            period=view["period"])

    def _orders_chart_summary(view: dict) -> Optional[dict]:
        """`DEC-214` — biểu đồ SỐ ĐƠN cho card "Biểu đồ khác" của trang Báo
        cáo, cùng engine với `_revenue_chart` ngay trên.

        R6 đã có ĐÚNG bài toán này cho trang phân tích (`_orders_chart`), và
        docstring của nó nói thẳng lý do dùng lại: *"không một dòng nào của
        `revenue_timeline` bị sửa cho việc này, và vì thế hai biểu đồ trên
        trang luôn cắt cùng những mốc thời gian"*. Hàm này KHÔNG gọi thẳng
        `_orders_chart` vì hai trang dựng `view` khác hình dạng nhau (trang
        phân tích có `view["anchor"]`/`view["range"]` sẵn từ
        `_analysis_view`; trang Báo cáo dùng `_business_period`, không có
        hai khoá đó) — nhưng cùng MỘT phép tính `data`/`anchor` mà
        `_revenue_chart` dùng, để hai biểu đồ trên CHÍNH trang Báo cáo cũng
        cắt cùng mốc thời gian với nhau.

        KHÔNG merge sổ cũ: `legacy_summary`/`legacy_daily_sales` chỉ lưu
        DOANH THU, không lưu SỐ ĐƠN — không có bằng chứng nào để vẽ thêm cho
        những tháng chỉ còn bản ghi lịch sử. Mọi điểm ở đây là
        `ORIGIN_CURRENT` (sổ nạp).
        """
        service = view["service"]
        granularity = revenue_timeline.parse_granularity(
            request.args.get("muc"), default=revenue_timeline.DAY)
        # Cùng lát dữ liệu mà `_revenue_chart` dùng — TOÀN BỘ dòng thời
        # gian, không riêng kỳ đang chọn — để hai biểu đồ luôn nói về cùng
        # một phạm vi.
        data = (view["data"] if view["period"] is None
                else _guarded(service.period))
        legacy_months = _legacy_month_totals()
        # `R7 §D` — số đơn của sổ nạp + nguồn lấp lỗ hổng số đơn cho những
        # ngày sổ nạp không nói tới (`data/chart_gapfill/daily_orders.jsonl`),
        # ở MỌI mức gộp — xem `revenue_timeline.count_series`.
        points = revenue_timeline.count_series(
            data.details, granularity=granularity,
            gapfill_days=chart_gapfill.daily_order_rows())
        # Cùng `anchor` mà `_revenue_chart` tính cho ĐÚNG `data` này — mép
        # phải của hai biểu đồ khớp nhau bằng cấu tạo, không phải trùng hợp.
        anchor = _chart_anchor(view["period"], data.details, legacy_months)
        paired = revenue_timeline.paired_series(
            points, granularity=granularity, anchor=anchor,
            confirmed_ranges=_guarded(snapshot_repo.confirmed_ranges)
            if snapshot_repo is not None else ())
        if paired is None:
            return None
        return business_presentation.paired_count_chart(
            paired, granularity=granularity,
            undated_orders=dashboard_metrics.totals(
                data.details).orders_without_date)

    def _period_employees(view: dict):
        """Bộ chọn nhân viên của kỳ, ĐÃ tính cả những lần Owner gán lại.

        Truyền `data` vào là điều kiện để `OD-5` khép kín: ngay sau khi Owner
        gán một dòng cho "Vinh", tên đó phải chọn được — nếu bộ chọn vẫn là
        danh sách thô của pipeline thì trang nhân viên trả 404 đúng lúc thao
        tác vừa thành công.
        """
        return _guarded(view["service"].employees,
                        date_from=view["bounds"][0], date_to=view["bounds"][1],
                        data=view["data"])

    def _selected_employee(view: dict) -> tuple[Optional[str], Optional[str], bool]:
        """`(tên, nhóm, đã chọn hợp lệ)` từ tham số `nhan-vien`.

        Một tên không có trong kỳ KHÔNG được dựng thành một trang toàn số 0 —
        đó là một nhân viên bịa. Trang rơi về "chưa chọn ai" và nói rõ.
        """
        employees = _period_employees(view)
        # `request.values`, không phải `request.args`: form POST của trang tick
        # Gia dụng mang `nhan-vien` trong BODY, và đọc thiếu nó ở đó sẽ biến
        # một thao tác hợp lệ thành 404.
        raw = request.values.get("nhan-vien")
        if raw is None:
            return None, None, False
        for name, group in employees:
            if (name or "") == raw:
                return name, group, True
        return None, None, False

    def _employee_context(view: dict) -> dict:
        employees = _period_employees(view)
        name, group, chosen = _selected_employee(view)
        return {
            "employees": business_presentation.employee_options(employees),
            "selected_employee": request.values.get("nhan-vien") or "",
            "employee": name, "employee_group": group, "chosen": chosen,
        }

    @app.get("/kinh-doanh")
    def business_summary():
        """SUMMARY V1 — `R-S1`…`R-S8`. Một kỳ, sáu chỉ tiêu đã freeze.

        `R1` cộng thêm ĐÚNG một cảnh báo: sổ nạp gần nhất không thấy lại một
        số dòng đang được tính vào các con số trên trang này. Cảnh báo đó
        KHÔNG sửa, không gộp và không loại bất kỳ dòng nào — nó chỉ dẫn Owner
        sang trang snapshot để tự soi.
        """
        view = _business_period(default_period=_summary_period_default)
        data = view["data"]
        totals = data.totals
        absence = (None if snapshot_repo is None
                   else _guarded(snapshot_repo.latest_snapshot_absence))
        summary = business_presentation.summary(
            totals, period=view["period"],
            previous_totals=None if view["previous"] is None
                            else view["previous"].totals,
            undated=_guarded(view["service"].undated_lines),
            previous_fallback=view["previous_fallback"],
        )
        not_seen = business_presentation.not_seen_warning(absence)
        # `TASK-OWNER-UIUX-002` — bảng "Theo nhân viên" đọc CHÍNH phân hoạch
        # sheet của `DEC-PHB02-08`, nên Vinh · Quý · Hiệp gộp thành MỘT hàng
        # Nội thành và Gia dụng là một hàng riêng, mà không có phép cộng nào
        # mới ở tầng này: `for_sheet` là phép chiếu duy nhất, và nó là một
        # phân hoạch nên tổng các hàng luôn đúng bằng tổng kỳ (`§42`).
        sheets = view["service"].sheets(data)
        sheet_totals = [(sheet, data.for_sheet(sheet).totals) for sheet in sheets]
        return render_template(
            "kinh_doanh.html", periods=view["periods"],
            selected_period=view["selected_period"],
            chart=_revenue_chart(view),
            orders_chart=_orders_chart_summary(view),
            not_seen=not_seen,
            summary=summary,
            pending=business_presentation.pending_items(
                not_seen=not_seen, coverage=summary["coverage"],
                coverage_url=url_for(
                    "business_purchase_price", ky=view["selected_period"],
                    **{"loc": "tat-ca" if summary["coverage"]["complete"]
                       else "thieu-gia"})),
            columns=business_presentation.EMPLOYEE_COLUMNS,
            rows=business_presentation.reporting_rows(
                sheet_totals, totals,
                groups=dict(_guarded(view["service"].assignable_employees))),
        )

    # ------------------------------------------------------------------
    # R4 — BÁO CÁO ĐÁNH GIÁ THÁNG.
    #
    # Một trang ĐỌC, dựng trên ĐÚNG một `PeriodData` của R3. Nó không có route
    # POST nào, không chạm `business_store`, và không thêm một thẩm quyền nào:
    # mọi con số ở đây đến từ `business_metrics.totals` của cùng lát dữ liệu
    # mà trang Báo cáo và không gian làm việc đang hiển thị.
    #
    # KHÔNG thêm tab top-level: thanh tab đã được `DEC-185` rút còn ba mục có
    # chủ đích, và trang này mở từ chính trang Báo cáo. Đổi thanh tab là một
    # quyết định điều hướng riêng, không phải hệ quả của R4.
    # ------------------------------------------------------------------

    def _evaluation_scope(view: dict):
        """`(sheet đang xem hoặc None, lát dữ liệu, nhãn phạm vi)`.

        `None` = phạm vi CẢ KỲ. Cả kỳ KHÔNG có target, và đó không phải một
        thiếu sót cần lấp: `DEC-PHB02-08` §7 nói target của một nhóm là con
        số Owner tự đặt, nên cộng target các nhân viên lên thành "target công
        ty" sẽ cho ra một con số chưa ai đặt và không ai chịu trách nhiệm.
        """
        data = view["data"]
        raw = request.args.get("nhom")
        if not raw:
            return None, data, "Cả kỳ"
        sheet = reporting_sheets.find_sheet(
            view["service"].sheets(data), raw)
        if sheet is None:
            # Khoá lạ ⟹ về cả kỳ VÀ nói ra, thay vì dựng một trang toàn số 0
            # cho một sheet không tồn tại.
            return None, data, "Cả kỳ"
        return sheet, data.for_sheet(sheet), (
            sheet.label or business_presentation.UNKNOWN_EMPLOYEE)

    def _identity_counts(details: list[dict], decisions) -> dict:
        """Bốn hàng đợi nhận diện của R2/R3, đếm trên ĐÚNG lát đang xem."""
        counts = {"needs_review": 0, "out_of_catalog": 0, "conflict": 0,
                  "missing_price": 0}
        for detail in details:
            state = line_identity.state_of(detail, decisions=decisions)
            if state.needs_review:
                counts["needs_review"] += 1
            if state.out_of_catalog:
                counts["out_of_catalog"] += 1
            if state.conflict:
                counts["conflict"] += 1
            if detail["line"].purchase_price is None:
                counts["missing_price"] += 1
        return counts

    @app.get("/kinh-doanh/danh-gia")
    def business_evaluation():
        """R4 — báo cáo đánh giá của MỘT kỳ, trên MỘT phạm vi.

        Bốn câu hỏi, theo đúng thứ tự Owner hỏi: kết quả ra sao · đạt bao
        nhiêu phần target · phần nào tạo ra kết quả · dữ liệu đã đủ để kết
        luận chưa.
        """
        view = _business_period(default_period=_summary_period_default)
        service, period = view["service"], view["period"]
        sheet, data, scope_label = _evaluation_scope(view)
        totals = data.totals
        today = _today()

        def drill(*, loc: str = "tat-ca", **extra) -> str:
            """Đường dẫn mở ĐÚNG tập dòng đứng sau một con số.

            Kỳ và phạm vi luôn đi kèm, nên tổng của bảng kê mở ra khớp con số
            vừa bấm — trừ cột Đơn, vốn không cộng được giữa các phạm vi và
            trang đã nói ra điều đó ở `ORDERS_NOT_ADDITIVE_NOTE`.
            """
            params = {"ky": view["selected_period"], "loc": loc}
            if sheet is not None:
                params["nhom"] = sheet.key
            params.update(extra)
            return url_for("business_purchase_price", **params)

        official = totals.coverage.is_complete
        # Một chỉ tiêu bị cổng coverage chặn dẫn Owner tới VIỆC PHẢI LÀM (các
        # dòng còn thiếu giá), không tới một bảng kê đầy đủ mà họ không tìm
        # được chỗ nào đang thiếu.
        gated_loc = "tat-ca" if official else "thieu-gia"
        kpis = evaluation.headline(totals)
        cells = evaluation_presentation.headline_cells(
            kpis, drill=lambda key: drill(
                loc=gated_loc if kpis[key].gated else "tat-ca"))

        dated = evaluation.dated_line_count(data.details)
        previous_details = (
            [] if view["previous"] is None else
            (view["previous"].for_sheet(sheet).details if sheet is not None
             else view["previous"].details))
        comparison = evaluation.same_days_comparison(
            period=period, current_details=data.details,
            previous_details=previous_details, today=today)

        target = (None if sheet is None
                  else _guarded(service.sheet_target, sheet=sheet, period=period))
        progress = evaluation.target_progress(
            target=target, totals=totals, period=period, today=today)
        target_run = evaluation.run_rate(
            totals.official_converted_sales, period=period, today=today,
            dated_lines=dated,
            official=totals.official_converted_sales is not None)
        revenue_run = evaluation.run_rate(
            totals.sales_revenue, period=period, today=today,
            dated_lines=dated, official=totals.sales_revenue is not None)

        # --- Bảng đóng góp ------------------------------------------------
        #
        # Bảng "theo đơn vị báo cáo" LUÔN nói về CẢ KỲ, kể cả khi trang đang
        # thu hẹp về một sheet: nó trả lời "kết quả của kỳ đến từ những đơn vị
        # nào", và một bảng chỉ có đúng đơn vị đang xem không trả lời được câu
        # đó. Vì vậy mẫu số tỉ trọng và hàng TỔNG của riêng bảng này lấy từ
        # tổng KỲ (`view["data"].totals`) — trang nói ra điều đó ngay dưới
        # bảng, thay vì để hai con số cùng tên "TỔNG" mang hai nghĩa.
        period_totals = view["data"].totals
        sheets = service.sheets(view["data"])
        sheet_targets = {}
        sheet_units = []
        for item in sheets:
            item_totals = view["data"].for_sheet(item).totals
            item_target = _guarded(service.sheet_target, sheet=item,
                                   period=period)
            sheet_targets[item.key] = evaluation.target_progress(
                target=item_target, totals=item_totals, period=period,
                today=today)
            sheet_units.append(evaluation.row_for(
                item.key,
                item.label or business_presentation.UNKNOWN_EMPLOYEE,
                item_totals, whole_revenue=period_totals.sales_revenue))

        products = evaluation.by_product(data.details, whole=totals)
        product_groups = evaluation.by_product_group(data.details, whole=totals)
        lead_sources = evaluation.by_lead_source(data.details, whole=totals)
        decisions = _identity_decisions()

        return render_template(
            "kinh_doanh_danh_gia.html",
            periods=view["periods"], selected_period=view["selected_period"],
            period_label=business_presentation.period_label(period),
            has_period=period is not None,
            scope_label=scope_label, selected_sheet=(sheet.key if sheet else ""),
            sheets=sheets,
            as_of=evaluation_presentation.business_date(
                evaluation.as_of(period, today=today)),
            running=evaluation.is_running(period, today=today),
            elapsed_days=evaluation.days_elapsed(period, today=today),
            month_days=(0 if period is None
                        else evaluation.days_in_month(period)),
            cells=cells,
            target=evaluation_presentation.target_block(
                progress, scope_label=scope_label, run=target_run),
            has_target_scope=sheet is not None,
            revenue_run_rate=evaluation_presentation.run_rate_cell(revenue_run),
            comparison=evaluation_presentation.same_days_block(
                comparison, period=period),
            sheet_rows=[
                {**row,
                 "target": (None if row["total_row"] else
                            evaluation_presentation.target_block(
                                sheet_targets[row["key"]],
                                scope_label=row["label"]))}
                for row in evaluation_presentation.group_rows(
                    sheet_units, period_totals,
                    drill=lambda unit: drill(nhom=unit.key))],
            sheet_scope_note=evaluation_presentation.SHEET_TABLE_SCOPE_NOTE,
            product_rows=evaluation_presentation.group_rows(
                products, totals,
                drill=lambda row: drill(**{"mat-hang": row.key})),
            product_group_rows=evaluation_presentation.group_rows(
                product_groups, totals,
                drill=lambda row: drill(**{"nhom-hang": (
                    "" if row.key == "KHONG_XAC_DINH" else row.key)})),
            lead_source_rows=evaluation_presentation.group_rows(
                lead_sources, totals,
                drill=lambda row: drill(**{"nguon": (
                    "" if row.key == "KHONG_XAC_DINH" else row.key)})),
            lowest_margin=[
                evaluation_presentation.group_row(
                    row, drill=lambda item: drill(**{"mat-hang": item.key}))
                for row in evaluation.lowest_margin_rows(products, limit=5)],
            discount=evaluation_presentation.discount_block(
                evaluation.discounts(data.lines, whole=totals),
                drill=drill(loc="co-chiet-khau")),
            loss=evaluation_presentation.loss_block(
                evaluation.loss_lines(data.lines), drill=drill(loc="lo")),
            quality=evaluation_presentation.data_quality_block(
                totals=totals,
                provenance=evaluation.provenance_breakdown(data.lines),
                price_sources=evaluation.price_source_breakdown(data.details),
                latest_sale=evaluation.latest_sale_date(data.details),
                undated_lines=_guarded(service.undated_lines),
                identity_counts=_identity_counts(data.details, decisions),
                binding_exceptions=len(data.binding_exceptions),
                closed=data.closed,
                drift=_guarded(service.period_drift, period=period,
                               data=view["data"]),
                period=period,
                coverage_url=drill(loc="thieu-gia")),
        )

    # ------------------------------------------------------------------
    # KHÔNG GIAN LÀM VIỆC NHÂN VIÊN (`DEC-PHB02-08`).
    #
    # Đây là bản KẾ THỪA của trang Nhân viên PHB-03, không phải một tab mới:
    # `R1` vẫn đúng bốn mục và mục "Nhân viên" vẫn trỏ vào chính route này.
    # Khác biệt là cách Owner chọn phạm vi — thay vì một ô thả xuống "chọn
    # nhân viên", màn hình có một hàng SHEET kiểu bảng tính ở trên cùng, và
    # sheet đang chọn hiện ngay năm chỉ tiêu rồi tới bảng kê chi tiết.
    #
    # Bốn màn hình cũ (`/kinh-doanh`, `/kinh-doanh/gia-nhap`,
    # `/kinh-doanh/gia-dung`, `/kinh-doanh/target`) KHÔNG bị gỡ: chúng vẫn là
    # nơi làm những việc mà không gian làm việc cố ý không làm — lọc bảng kê
    # theo bốn chế độ, phân loại Gia dụng ở cấp MẶT HÀNG, và đặt Target theo
    # đồng cho toàn bộ nhân viên trong một bảng.
    # ------------------------------------------------------------------

    def _workspace_period(raw: Optional[str] = None) -> tuple[int, int]:
        """Tháng đang xem của không gian làm việc. LUÔN là một tháng thật.

        `raw` cho phép người gọi đưa thẳng chuỗi `YYYY-MM` vào (route JSON
        `UI-04` mang kỳ trong ĐƯỜNG DẪN, không trong query `ky`). Không truyền
        ⟹ đọc `ky` như trước. Một tham số chứ không một hàm phân tích thứ hai:
        hai chỗ đọc cùng một định dạng theo hai cách là hai chỗ để một tháng
        hợp lệ ở đường này bị từ chối ở đường kia.

        Khác `_business_period_choice` ở đúng hai điểm, và cả hai là quyết
        định của Owner:

        1. Không có/không hợp lệ ⟹ THÁNG DƯƠNG LỊCH HIỆN TẠI, không phải
           "Toàn bộ dữ liệu" (`§2`, `§3`).
        2. Một tháng CHƯA CÓ dòng bán nào vẫn mở được (`§2`, `§45`). Owner
           chuẩn bị Target trước lần nạp sổ đầu tiên của tháng, và rơi ngược
           về tháng trước sẽ làm con số đó ghi vào tháng sai.

        Ranh giới an toàn giữ nguyên: tháng phải là `1..12` và năm phải nằm
        trong khoảng có nghĩa, nếu không rơi về tháng hiện tại.
        """
        raw = (request.values.get("ky") or "") if raw is None else raw
        year_text, _, month_text = raw.partition("-")
        try:
            year, month = int(year_text), int(month_text)
        except ValueError:
            return (_today().year, _today().month)
        if not 1 <= month <= 12:
            return (_today().year, _today().month)
        if not _MIN_WORKSPACE_YEAR <= year <= _MAX_WORKSPACE_YEAR:
            return (_today().year, _today().month)
        return (year, month)

    def _workspace_sheet_key(sheets: list) -> Optional[str]:
        """Khoá sheet Owner đang xem, đọc từ `sheet` hoặc từ `nhan-vien`.

        `nhan-vien` là bí danh KẾ THỪA, và nó có ngữ nghĩa rõ ràng chứ không
        phải một phép đoán: một cái tên thuộc nhóm Nội thành dẫn tới sheet
        NỘI THÀNH (Vinh · Quý · Hiệp không có tab riêng — `§6`), tên rỗng dẫn
        tới nhóm "chưa xác định", tên khác dẫn tới sheet của chính người đó.
        Nhờ vậy mọi đường dẫn và bookmark cũ vẫn mở đúng phạm vi.
        """
        chosen = request.values.get("sheet")
        if chosen and reporting_sheets.find_sheet(sheets, chosen) is not None:
            return chosen
        raw = request.values.get("nhan-vien")
        if raw is None:
            return None
        alias = reporting_sheets.employee_sheet_key(raw)
        if reporting_sheets.find_sheet(sheets, alias) is not None:
            return alias
        # Tên thuộc nhóm Nội thành ⟹ sheet Nội thành. Tra trong master, không
        # trong dữ liệu của kỳ: một nhân viên Nội thành chưa bán gì tháng này
        # vẫn phải mở ra sheet Nội thành chứ không rơi về sheet mặc định.
        groups = dict(_require_business().assignable_employees())
        if groups.get(raw) == reporting_sheets.GIA_DUNG_ELIGIBLE_GROUP:
            return reporting_sheets.NOI_THANH_SHEET
        return None

    def _workspace_view(period_text: Optional[str] = None) -> dict:
        """Mọi thứ một màn hình không gian làm việc cần, đọc đúng một lần."""
        service = _require_business()
        period = _workspace_period(period_text)
        bounds = analytics_queries.month_bounds(*period)
        data = _guarded(service.period, date_from=bounds[0], date_to=bounds[1],
                        period=period)
        sheets = service.sheets(data)
        key = _workspace_sheet_key(sheets)
        sheet = (reporting_sheets.find_sheet(sheets, key) if key
                 else None) or sheets[0]
        return {
            "service": service, "period": period, "data": data,
            "sheets": sheets, "sheet": sheet,
            "selected_period": f"{period[0]}-{period[1]:02d}",
        }

    def _workspace_previous(view: dict):
        """Chỉ tiêu của CHÍNH sheet này ở tháng liền trước (`§16`).

        So sánh cùng ĐƠN VỊ BÁO CÁO với chính nó: Nội thành so Nội thành, Gia
        dụng so Gia dụng. Không so Nội thành với một nhân viên, không so Gia
        dụng với Nội thành, và không mượn tổng tháng của cả công ty từ sổ cũ —
        tổng đó là số của công ty, và dùng nó làm mẫu số cho một nhóm là một
        phép so sai (`DEC-181` §16).
        """
        previous = analytics_presentation.previous_period(view["period"])
        bounds = analytics_queries.month_bounds(*previous)
        data = _guarded(view["service"].period,
                        date_from=bounds[0], date_to=bounds[1])
        return data.for_sheet(view["sheet"]).totals

    def _workspace_line_keys():
        """Khoá nghiệp vụ của MỘT dòng, đọc từ form/query. `None` nếu thiếu."""
        try:
            occurrence = int(request.values.get("occurrence_index") or "")
        except ValueError:
            return None
        order_key = request.values.get("order_key") or ""
        product_key = request.values.get("product_key") or ""
        if not order_key or not product_key:
            return None
        return {"order_key": order_key, "product_key": product_key,
                "occurrence_index": occurrence}

    def _confirmed_identity_keys() -> frozenset[str]:
        """Các mặt hàng Owner đã xác nhận — đọc lại ở MỖI lần tải trang.

        Không nhớ vào bộ nhớ: một lần xác nhận vừa xảy ra phải đổi màn hình
        NGAY (`§PI-07`), và một cache ở đây sẽ khiến dòng vừa phân loại xong
        vẫn hiện "Chưa phân loại" cho tới lần khởi động lại tiếp theo. Chi phí
        là một lần đọc log nhỏ cho mỗi lần tải trang — cùng đánh đổi mà
        `kpi_authority_valid` đã chấp nhận vì cùng một lý do.
        """
        return identity_gateway.confirmed_keys(identity_store)

    def _identity_decisions() -> line_identity.Decisions:
        """BA loại quyết định phân loại đã lưu (R2 §4.1).

        Đọc log ĐÚNG MỘT LẦN cho cả trang rồi chiếu ra ba tập, thay vì gọi
        `confirmed_keys` và `out_of_catalog_keys` nối tiếp — hai lần đọc là
        hai ảnh chụp, và một thao tác xảy ra giữa chúng sẽ làm một dòng hiện
        đồng thời "đã khớp" ở chỗ này và "chưa phân loại" ở chỗ kia.

        `conflict_resolved` (repair `FIND-R2-IR-01`, siết lại ở
        `FIND-R2-IR-03`) là `{raw_identity_key: confirmed_at}` — KHÔNG phải
        một tập khoá trần. `mapping.confirmed_at` (đã là `datetime`, ép buộc
        có mặt ở mọi mapping CONFIRMED — `ProductIdentityMapping.__post_init__`)
        là mốc "quyết định giải mâu thuẫn này được ghi lúc nào". `line_identity.
        state_of` so nó với mốc lần chạy đã tính ra dòng đang hiển thị, để
        không cho một quyết định giải A-vs-B CŨ che mất một `IDENTITY_CONFLICT`
        MỚI (A-vs-C) mà một lần chạy SAU đó đã đúng đắn phát hiện lại — một
        tập khoá trần không phân biệt được hai việc này (xem `Decisions`).
        """
        view = identity_gateway.store_view(identity_store)
        if view is None:
            return line_identity.Decisions()
        confirmed, out_of_catalog = set(), set()
        conflict_resolved: dict = {}
        for mapping in view.alias_index().values():
            if mapping.source_system != identity_gateway.SOURCE_SYSTEM_REPORTS_SALES:
                continue
            if mapping.status is identity_gateway.MappingStatus.CONFIRMED:
                confirmed.add(mapping.raw_identity_key)
                if (mapping.mapping_source
                        is identity_gateway.MappingSource.HUMAN_CONFLICT_RESOLUTION):
                    conflict_resolved[mapping.raw_identity_key] = mapping.confirmed_at
            elif mapping.status is identity_gateway.MappingStatus.OUT_OF_CATALOG:
                out_of_catalog.add(mapping.raw_identity_key)
        return line_identity.Decisions.of(
            confirmed=confirmed, out_of_catalog=out_of_catalog,
            conflict_resolved=conflict_resolved)

    def _durable_tracking_display() -> Optional[dict]:
        """Bản chiếu nhãn BỀN của lần chạy gần nhất, hoặc `None`.

        `R5.3` — nơi lưu bền là `tracking_display_snapshot`, CÙNG database với
        con số của kỳ. Không lời gọi Tracking nào ở đây: hàng đã nằm sẵn trong
        database từ lần chạy đã ghi nó.

        Mọi lỗi đọc đều cho `None`, và nó KHÔNG đi qua `_guarded`: `_guarded`
        biến một lỗi storage thành `503`, đúng cho một trang mất TIỀN, sai cho
        một cái NHÃN. Một database vừa chớp mất không được phép làm cả bảng kê
        không mở được — nó chỉ được phép làm ba cột hiển thị bớt nội dung.
        """
        if snapshot_repo is None:
            return None
        try:
            return snapshot_repo.latest_tracking_display()
        except Exception:  # noqa: BLE001 — xem docstring
            return None

    def _tracking_display() -> dict:
        """Bản chiếu nhãn HIỆN HÀNH — cache đĩa trước, bản BỀN dựng lại sau.

        ## Lỗi production mà hàm này đóng (`R5.3`)

        `R5.1 REPAIR-2` đã bắt `POST /run` ghi bản chiếu từ capture của chính
        lần chạy đó. Nhưng nó ghi ra một FILE trên đĩa máy chủ, và trên Render
        đĩa ấy là EPHEMERAL: mỗi lần deploy/restart file biến mất. Con số của
        kỳ thì không — chúng nằm trong database. Đo trực tiếp trên đường thật:
        chạy báo cáo ⟹ tab Nhân viên hiện model ngắn + Hãng + Nhóm hàng; xoá
        đĩa ephemeral (đúng việc Render làm) ⟹ CÙNG lần chạy ấy hiện `—` ở cả
        ba ô, VĨNH VIỄN, vì không đường nào dựng lại được bản chiếu.

        ## Thứ tự đọc, và vì sao nó là thứ tự này

        1. **Cache đĩa.** Còn đọc được thì nó ĐÚNG là bản chiếu của lần chạy
           gần nhất — chính `_refresh_catalog_display` vừa ghi nó từ capture
           của lần chạy ấy. Đọc một file nhỏ rẻ hơn một lượt truy vấn.
        2. **Bản BỀN của lần chạy.** Cache trống (deploy mới, đĩa bị dọn,
           file hỏng) ⟹ dựng lại từ `tracking_display_snapshot`, rồi ghi lại
           cache để lần tải trang sau không phải hỏi database nữa.

        Cache RỖNG là điều kiện kích hoạt duy nhất, và nó hẹp có chủ ý. Một
        cache CÓ dữ liệu nhưng thiếu vài mã mới xác nhận là một câu chuyện
        KHÁC — `_catalog_projection_warning` hình dạng 2 đã đo và nói ra nó
        bằng LỊCH SỬ ghi, không phải bằng nội dung. Dựng lại đè lên một cache
        đang có sẽ xoá mất chính bằng chứng ấy.

        Không nhánh nào ở đây gọi Tracking, và không nhánh nào suy một chữ từ
        tên trên sổ kế toán (`ADR-111` §3).
        """
        display = catalog_display.read()
        if display:
            return display
        durable = _durable_tracking_display()
        if durable is None:
            return {}
        rows = catalog_display.normalise(durable.get("rows") or {})
        # Ghi lại cache là best-effort THUẦN: hỏng thì lần sau dựng lại tiếp.
        catalog_display.restore(rows)
        return rows

    def _catalog_labels(details) -> dict:
        """`{raw_identity_key: {tracking_code, model_label, brand,
        category_label}}` (R5 §5 + R5.1 §5, mở rộng `R5.4`).

        Ghép các nguồn ĐÃ CÓ, không đọc mạng: `line_identity.tracking_
        identity_of` nói dòng nào trỏ tới mã Tracking nào (mapping đã
        CONFIRMED trong Reports THẮNG; không có thì mã mà LẦN CHẠY đã phân
        giải và lưu trên dòng — `R5.4`), và bản chiếu hiển thị nói mã đó là
        model gì, của hãng nào, thuộc nhóm hàng nào. Bản chiếu vắng mặt ⟹ mỗi
        khoá vẫn có mã Tracking để làm nhãn dự phòng, còn hãng và nhóm hàng là
        `None` — đúng trạng thái "chưa xác định", không phải một cái tên đoán
        ra.

        Trước `R5.4` bảng này CHỈ có khoá của mapping CONFIRMED, nên mọi dòng
        khớp TỰ ĐỘNG với Tracking (đường sản xuất chính) hiện tên dài và `—`
        dù đã có mã và có giá MIN. Cổng `§5.4` KHÔNG nới: `workspace_
        presentation._catalog_field` vẫn chỉ tra bảng này cho dòng
        `MATCHED_TRACKING`, nên một dòng đang tranh chấp, trỏ tới target đã
        cũ, OUT_OF_CATALOG hay chưa phân loại vẫn không nhận nhãn nào — kể cả
        khi cột đã lưu của nó còn mang một mã.
        """
        display = _tracking_display()
        identities = identity_gateway.confirmed_identities(identity_store)
        labels = {}
        for detail in details:
            key = line_identity.identity_key_of(detail.get("product_raw"))
            if key is None or key in labels:
                continue
            identity = line_identity.tracking_identity_of(
                detail, identities=identities)
            code = getattr(identity, "source_product_code", None)
            if not code:
                continue
            row = display.get(code) or {}
            labels[key] = {"tracking_code": code,
                           **{field: row.get(field)
                              for field in catalog_display.FIELDS}}
        return labels

    def _tracking_snapshot():
        """Danh mục Tracking để CHỌN mặt hàng, hoặc `None` nếu không đọc được.

        Chỉ được gọi khi Owner thật sự mở bảng chọn của MỘT dòng — không phải
        ở mỗi lần tải trang. Một lần pull live giữ authority thô của Tracking
        trên đĩa máy chủ, và `S071` §10 nói rõ nó phải được dọn ngay sau khi
        dùng; gọi nó cho mọi lần render bảng kê là biến một ngoại lệ có kiểm
        soát thành thói quen.
        """
        captures, _, live = _select_captures_for_run()
        if captures is None:
            return None
        try:
            snapshot = load_tracking_catalog_capture(captures.tracking_catalog)
            # R5 §5 + R5.1 §5 — lần pull này đã được cho phép xảy ra vì một lý
            # do khác (Owner vừa mở bảng chọn). Ghi lại ĐÚNG các trường hiển
            # thị để bảng kê không phải gọi mạng ở mỗi lần tải trang.
            catalog_display.write(snapshot)
            return snapshot
        except Exception:  # noqa: BLE001 — danh mục hỏng = "chưa đọc được"
            return None
        finally:
            if live is not None:
                live.cleanup()

    def _catalog_projection_warning(details) -> Optional[dict]:
        """`R5.1 REPAIR-2` — cảnh báo khi bản chiếu KHÔNG nói đủ những gì nó
        đáng ra phải nói, ở HAI hình dạng khác nhau.

        ## Hình dạng 1 — VẮNG hoàn toàn (bản sửa lần đầu)

        Điều kiện kích hoạt hẹp có chủ ý, và nó là điều làm cảnh báo này đáng
        đọc: nó chỉ hiện khi CẢ HAI điều đúng cùng lúc —

        1. có ít nhất một dòng trên sheet đang xem đã có mapping `CONFIRMED`
           trỏ tới một mã Tracking (tức có thứ để hiển thị), VÀ
        2. bản chiếu không nói được gì về BẤT KỲ mã nào trong số đó.

        Nếu chưa ai xác nhận mapping nào, cột `Hãng` là dấu gạch vì một lý do
        HOÀN TOÀN KHÁC (chưa phân loại), và một cảnh báo về bản chiếu ở đó sẽ
        chỉ người đọc đi sai chỗ.

        ## Hình dạng 2 — CŨ một phần (Owner báo lỗi lần 2)

        Hình dạng 1 một mình có một lỗ hổng: nếu bản chiếu ĐÃ có dữ liệu từ
        một lần chạy CŨ (nên `matched > 0`), phiên bản trước coi nó "đang hoạt
        động" và im lặng — kể cả khi lần chạy GẦN NHẤT đã không làm mới được
        nó (`NO_METADATA`/`WRITE_FAILED`, `DEC-208` §5) và một mapping MỚI
        CONFIRMED sau lần ghi cuối cùng vẫn đang thiếu nhãn. Đó chính là "vẫn
        còn — hiện dấu gạch mà không lời nào giải thích" tái diễn dưới một
        hình dạng khác: lần đầu là vắng TOÀN BỘ, lần này là vắng MỘT PHẦN.

        `read()` một mình không phân biệt được "Tracking đơn giản chưa phân
        loại mã này" (hợp lệ, `AR-R5.1-01`, im lặng đúng) khỏi "bản chiếu
        đang STALE vì lần chạy gần nhất hỏng" (lỗi, cần cảnh báo) — cả hai cho
        `display.get(code)` falsy y hệt nhau. Chỉ `catalog_display.
        last_write_status()` — LỊCH SỬ ghi, không phải NỘI DUNG đang có — tách
        được hai câu đó, nên cảnh báo hình dạng 2 CHỈ nổi lên khi có bằng
        chứng ghi thất bại, không suy đoán từ việc thiếu nhãn một mình.

        `None` = không có gì phải nói, ở cả hai hình dạng.
        """
        identities = identity_gateway.confirmed_identities(identity_store)
        decisions = _identity_decisions()
        wanted, matched, unmatched = set(), 0, set()
        display = _tracking_display()
        for detail in details:
            state = line_identity.state_of(detail, decisions=decisions)
            if state.classification != line_identity.CLASS_MATCHED_TRACKING:
                continue
            # `R5.4` — cùng nguồn mã với `_catalog_labels`: dòng khớp TỰ ĐỘNG
            # cũng "có thứ để hiển thị", nên cảnh báo phải đo cả chúng.
            identity = line_identity.tracking_identity_of(
                detail, identities=identities)
            code = getattr(identity, "source_product_code", None)
            if not code:
                continue
            wanted.add(code)
            if display.get(code):
                matched += 1
            else:
                unmatched.add(code)
        if not wanted:
            return None
        if not matched:
            # Hình dạng 1 — GIỮ NGUYÊN hành vi đã nghiệm thu: không cần bằng
            # chứng ghi thất bại, vắng toàn bộ là đủ để cảnh báo.
            return {
                "codes": len(wanted),
                "note": catalog_display.MISSING_PROJECTION_NOTE,
                "kind": "vang",
            }
        if not unmatched:
            return None
        # Hình dạng 2 — CHỈ cảnh báo khi có BẰNG CHỨNG lần ghi gần nhất hỏng
        # vì một lý do có thể ảnh hưởng đúng những mã còn thiếu này.
        status = catalog_display.last_write_status()
        if status is None or status.written:
            return None
        if status.reason not in (catalog_display.REASON_NO_METADATA,
                                 catalog_display.REASON_WRITE_FAILED):
            return None
        return {
            "codes": len(unmatched),
            "note": catalog_display.stale_metadata_note(status.reason),
            "kind": "cu",
        }

    def _refresh_catalog_display(
        captures, *, run_id: Optional[str] = None,
    ) -> tuple[catalog_display.WriteResult, Optional[dict]]:
        """`R5.1 REPAIR-2` — làm mới bản chiếu hiển thị từ capture CỦA LẦN CHẠY.

        ## Lỗi production mà hàm này đóng lại

        Trước bản sửa, `catalog_display` CHỈ được ghi trong
        `_tracking_snapshot()`, tức chỉ khi Owner mở bảng chọn phân loại của
        MỘT dòng. Luồng chính — upload sổ rồi bấm chạy — không ghi và không làm
        mới nó. Trên đĩa ephemeral của Render, bản chiếu biến mất sau mỗi lần
        deploy và KHÔNG có gì dựng lại nó, nên tab Nhân viên hiện tên dài trên
        sổ kế toán và cột Hãng chỉ có dấu gạch — kể cả với những dòng đã có
        mapping `CONFIRMED`.

        Đây KHÔNG phải `AR-R5.1-04`. Rủi ro đã ghi nhận ấy nói về việc *chờ lần
        capture danh mục MỚI đầu tiên*; một lần chạy báo cáo THÀNH CÔNG chính
        là một lần capture danh mục mới — nó chỉ không được dùng.

        ## Không gọi Tracking lần thứ hai

        Hàm nhận `captures` ĐÃ CÓ của lần chạy đó (`OwnerRun.captures`) và đọc
        lại đúng file capture trên đĩa. Nó KHÔNG gọi `_select_captures_for_run`
        và KHÔNG gọi `live_pull`: một lần pull thứ hai chỉ để lấy nhãn hiển thị
        sẽ giữ authority thô của Tracking trên đĩa lâu hơn cần thiết (`S071`
        §10) và thêm một lần gọi mạng cho mỗi lần chạy.

        Nó phải chạy TRONG `try` của `run_report`, trước khi `finally` gọi
        `live_handle.cleanup()` — sau đó file capture không còn.

        Trả về `(WriteResult, bằng chứng ghi BỀN)` để `run_report` ghi cả hai
        vào `tracking_evidence`. Mọi thất bại đều là `written=False` KÈM LÝ
        DO, không bao giờ một ngoại lệ: bản chiếu là NHÃN, và làm hỏng một
        lần chạy báo cáo vì một cái nhãn là đánh đổi sai chiều.

        `R5.3` — vế thứ hai là bản lưu BỀN theo `run_id` (`tracking_display_
        snapshot`). Nó là thứ dựng lại được ba cột hiển thị sau một lần
        deploy/restart của Render, khi cache trên đĩa ephemeral đã biến mất.
        `None` khi lần chạy không có capture nào để lưu.
        """
        catalog_path = getattr(captures, "tracking_catalog", None)
        if catalog_path is None:
            # `write(None)` thay vì tự dựng `WriteResult` tay: cả hai cho ra
            # cùng giá trị, nhưng đi qua `write()` thì lần "không có gì để
            # ghi" này CŨNG được `_record_status` lưu lại — nên `last_write_
            # status()` phản ánh đúng lần chạy gần nhất, kể cả khi nó không
            # có capture nào.
            return catalog_display.write(None), None
        try:
            snapshot = load_tracking_catalog_capture(catalog_path)
        except Exception:  # noqa: BLE001 — danh mục hỏng = "chưa đọc được"
            return catalog_display.write(None), None
        result = catalog_display.write(snapshot)
        durable = (None if run_id is None
                   else _persist_tracking_display(snapshot, run_id=run_id))
        return result, durable

    def _persist_tracking_display(snapshot, *, run_id: str) -> dict:
        """`R5.3` — lưu BỀN bản chiếu nhãn của ĐÚNG lần chạy này.

        ## Vì sao cần một nơi thứ hai, khi đã có file trên đĩa

        File trên đĩa là một CACHE trên đĩa EPHEMERAL của Render: nó biến mất
        ở mỗi lần deploy/restart, trong khi con số của kỳ nằm trong database
        và sống tiếp. Sau một lần restart, mọi dòng đã `CONFIRMED` hiện `—` ở
        cả Hãng lẫn Nhóm hàng và KHÔNG có gì dựng lại chúng — đó là triệu
        chứng production của `R5.3`. Hàng ghi ở đây là thứ `_tracking_display`
        dựng lại từ đó.

        ## Nó KHÔNG được phép làm hỏng lần chạy

        Cùng kỷ luật đã nghiệm thu cho `catalog_display.write()`: đây là một
        tác dụng phụ mang NHÃN, không mang tiền. Mọi thất bại đều trả về một
        lý do trong bằng chứng của run, KHÔNG BAO GIỜ một ngoại lệ.

        ## Capture KHÔNG mang nhãn nào ⟹ KHÔNG ghi đè

        Cùng đúng luật mà `catalog_display.write()` đã nghiệm thu ở `R5.1
        REPAIR-2`: một capture đời cũ (không trường hiển thị nào) không được
        phép XOÁ nhãn mà một lần chạy trước đã đọc được — làm màn hình nói ÍT
        hơn vì một artifact cũ là một hồi quy, không phải một phép thận trọng.
        Hai nơi lưu phải theo CÙNG một luật ở đây; lệch nhau thì cùng một lần
        chạy cho hai màn hình khác nhau tuỳ vào việc đĩa còn hay mất.

        `REASON_NO_METADATA` được trả về (không phải một ngoại lệ), nên bằng
        chứng của run vẫn nói ra rằng lần chạy này không đóng góp nhãn nào.

        `captured_at` là mốc của CAPTURE (bằng chứng nhãn này đến từ đâu);
        `created_at` là mốc Reports ghi hàng (khoá sắp xếp "lần chạy gần
        nhất"). Hai mốc khác nhau và trộn chúng sẽ làm một capture cũ chụp
        lại hôm nay trông như bản mới nhất.
        """
        if snapshot_repo is None:
            return {"written": False, "rows": 0,
                    "reason": catalog_display.REASON_NO_STORE}
        rows = catalog_display.rows_of(snapshot)
        if not rows:
            return {"written": False, "rows": 0,
                    "reason": catalog_display.REASON_NO_METADATA}
        captured_at = getattr(snapshot, "captured_at", None)
        try:
            snapshot_repo.write_tracking_display(
                run_id=run_id, rows=rows,
                capture_id=getattr(snapshot, "capture_id", None),
                captured_at=(captured_at.isoformat()
                             if captured_at is not None else None),
                created_at=datetime.now(timezone.utc).isoformat(
                    timespec="seconds"))
        except Exception:  # noqa: BLE001 — xem docstring
            return {"written": False, "rows": len(rows),
                    "reason": catalog_display.REASON_WRITE_FAILED}
        return {"written": True, "rows": len(rows), "reason": None}

    def _tracking_inv_map_snapshot():
        """`inv.map` hiện tại, hoặc `None` — dùng CHỈ khi giải mâu thuẫn.

        Repair `FIND-R2-IR-02`: ghi lại đúng mã Tracking đang chỏi tại thời
        điểm người dùng chọn đòi hỏi CẢ `alias.map`/`board` LẪN `inv.map`
        (`tracking_authority_code()` đọc cả hai) — thiếu `inv.map` thì một
        mâu thuẫn chỉ giải được qua đường đó sẽ không có mã đối lập nào để
        ghi, và `identity_gateway.confirm_identity` đã tự xử lý `None` theo
        hướng AN TOÀN (không miễn trừ nhầm — sẽ hỏi lại ở lần chạy sau).

        Tách khỏi `_tracking_snapshot()` (chỉ catalog) để đường xác nhận
        BÌNH THƯỜNG — không phải giải mâu thuẫn — không phải trả thêm một
        lần đọc `inv.map` mà nó không cần.
        """
        captures, _, live = _select_captures_for_run()
        if captures is None or captures.tracking_inv_map is None:
            if live is not None:
                live.cleanup()
            return None
        try:
            return load_tracking_inv_map_capture(captures.tracking_inv_map)
        except Exception:  # noqa: BLE001 — đọc `inv.map` lỗi ⟹ coi là chưa đọc được
            return None
        finally:
            if live is not None:
                live.cleanup()

    def _workspace_redirect(**extra):
        args = {"ky": request.values.get("ky") or None,
                "sheet": request.values.get("sheet") or None,
                "nhan-vien": request.values.get("nhan-vien") or None}
        return redirect(url_for(
            "business_employee",
            **{k: v for k, v in args.items() if v}, **extra))

    # ==================================================================
    # `UI-03` — CÙNG những đường ghi, HAI cách trả lời.
    #
    # Không có route ghi mới nào ở đây, và đó là điểm chính: một route JSON
    # song song sẽ là một bản thứ hai của cùng một quyết định nghiệp vụ, và
    # hai bản sẽ lệch nhau ở đúng cái nhánh mà không ai chạy thử. Ba đường
    # ghi của bảng kê (`phan-loai`, `ngoai-bang`, `loai-dong`) giữ NGUYÊN
    # thân hàm, gọi NGUYÊN `identity_gateway`/`store` như trước; chỉ CÂU TRẢ
    # LỜI là rẽ đôi ở dòng cuối:
    #
    #     trình duyệt (form thật, không JS) → `_workspace_redirect` như cũ
    #     client JS (`Accept: application/json`) → payload dưới đây
    #
    # Tắt JavaScript thì không một byte nào của trang đổi khác so với trước
    # `UI-03` — đó là điều kiện để gọi đây là một lớp TĂNG CƯỜNG.
    # ==================================================================

    def _workspace_wants_json() -> bool:
        """Người gọi có muốn JSON hơn HTML không.

        So SÁNH hai mức ưu tiên thay vì tìm chuỗi `"application/json"` trong
        header: trình duyệt gửi `Accept: text/html,…,*/*;q=0.8` cho một form
        POST thật, và `*/*` khớp cả JSON. Tìm chuỗi thì đúng, so mức ưu tiên
        thì đúng VÀ không phụ thuộc vào việc trình duyệt nào viết header ra
        sao.
        """
        accept = request.accept_mimetypes
        return (accept["application/json"] > accept["text/html"])

    def _workspace_macros():
        """Bộ macro dựng các vùng của không gian làm việc.

        ĐÚNG những macro mà `kinh_doanh_nhan_vien.html` gọi — xem chú thích
        đầu `_workspace_table.html`. Không có bản dựng thứ hai nào ở đây, và
        client không ghép một thẻ `<tr>` nào.
        """
        return app.jinja_env.get_template("_workspace_table.html").module

    def _workspace_group_html(context: dict) -> dict:
        """`{mã BH: {html, after, before}}` cho lát đang dựng.

        `after`/`before` là mã BH ĐỨNG NGAY TRƯỚC và NGAY SAU nó trong thứ
        tự hiển thị của CẢ sheet, hoặc `None` ở hai đầu. Client cần chúng cho
        một ca có thật: khôi phục một dòng mà BH của nó KHÔNG còn hàng nào
        trong bảng (dòng cuối của đơn vừa bị loại ⟹ cả khối đã biến mất). Khi
        ấy không có hàng cũ nào để thay — phải CHÈN, và chỗ chèn đúng là một
        tính chất của thứ tự toàn sheet, không phải thứ client suy ra được từ
        những hàng nó đang giữ.

        Không gửi cả danh sách thứ tự: với 5.000 dòng đó là vài nghìn mã cho
        một lần ghi chạm một dòng. Hai hàng xóm là đủ, và khi cả hai đều
        không nằm trong cửa sổ đang tải thì BH ấy cũng không nằm trong cửa
        sổ — client bỏ qua, đúng như nó bỏ qua mọi hàng chưa tải.
        """
        macros = _workspace_macros()
        order = list(context["page"]["shades"])
        position = {key: index for index, key in enumerate(order)}
        payload = {}
        for group in context["groups"]:
            key = group["order_key"]
            index = position.get(key)
            payload[key] = {
                "html": str(macros.detail_rows(
                    [group], context["selected_period"], context["sheet"],
                    context["editing"], context["assignable"],
                    context["unclassifiable_note"])),
                "after": (order[index - 1]
                          if index is not None and index > 0 else None),
                "before": (order[index + 1]
                           if index is not None and index + 1 < len(order)
                           else None),
            }
        return payload

    def _workspace_regions(context: dict) -> dict:
        """Các vùng NGOÀI bảng kê mà một lần ghi có thể làm đổi.

        Vì sao trả HTML chứ không trả con số: ô `DS quy đổi`/`Lợi nhuận KPI`
        mang một NHÃN (`CHÍNH THỨC`/`CHƯA HOÀN CHỈNH`) do server quyết định
        cùng lúc với con số (`R-S7`). Gửi riêng con số rồi để client tự ghép
        lại cái nhãn là dựng một thẩm quyền thứ hai cho đúng câu hỏi khó
        nhất của sản phẩm này — và nó sẽ nói sai đúng vào lúc dữ liệu thiếu.

        KHÔNG có khoá `"identity-warning"` — `TASK-OWNER-UIUX-009` bỏ vùng
        `data-region="identity-warning"` khỏi `kinh_doanh_nhan_vien.html`
        (tích hợp lại ở đây sau khi lineage đó merge). Gửi HTML cho một
        vùng không còn host DOM nào là dữ liệu chết, không phải markup thừa
        vô hại — client sẽ không tìm thấy chỗ để vá vào (`applyRegions()`
        no-op khi thiếu host), nhưng gửi nó vẫn là gửi sai ý định. Macro
        `identity_warning_block` vẫn còn trong `_workspace_table.html`
        (không xoá) cho một trang khác cần lại.
        """
        macros = _workspace_macros()
        return {
            "identify": str(macros.identify_panel(
                context["identify"], context["selected_period"],
                context["sheet"])),
            "kpi-strip": str(macros.kpi_strip(
                context["strip"], context["sheet"])),
            "sheet-totals": str(macros.totals_row(
                context["detail_totals"], context["sheet"], context["strip"])),
            "excluded": str(macros.excluded_block(
                context["excluded"], context["selected_period"],
                context["sheet"])),
        }

    def _workspace_write_payload(*, note: str, order_keys) -> dict:
        """Payload JSON của MỘT lần ghi trên bảng kê.

        `_workspace_view()` được gọi LẠI ở đây, sau khi ghi: payload phải
        mang trạng thái SAU quyết định, và dùng lại bản đọc trước khi ghi sẽ
        trả về đúng màn hình cũ kèm một câu "đã lưu".

        `order_keys` là phạm vi THẬT của quyết định, không phải dòng vừa bấm.
        Một lần xác nhận phân loại áp cho MỌI dòng của kỳ dùng chung khoá
        định danh (`INV-76`/`INV-87`), nên payload trả về đủ các BH ấy và
        client vá hết — vá mỗi dòng vừa bấm sẽ để những dòng còn lại hiện
        "Chưa phân loại" cho tới lần tải trang sau.

        `removed_order_keys` là những BH KHÔNG còn dòng nào trong sheet sau
        lần ghi (loại nốt dòng cuối của một đơn). Chúng khác hẳn "không đổi":
        client phải GỠ chúng khỏi bảng, không phải để nguyên.
        """
        order_keys = list(dict.fromkeys(order_keys))
        view = _workspace_view()
        context = _workspace_context(view, only_orders=order_keys)
        groups = _workspace_group_html(context)
        return {
            "schema_version": workspace_presentation.WORKSPACE_SCHEMA_VERSION,
            "message": note,
            "affected": {
                "order_keys": order_keys,
                "lines": sum(group["lines"] for group in context["groups"]),
            },
            "groups": groups,
            "removed_order_keys": [key for key in order_keys
                                   if key not in groups],
            "regions": _workspace_regions(context),
            "trace_id": request_timing.trace_id(),
        }

    def _workspace_answer(*, note: Optional[str] = None,
                          error: Optional[str] = None,
                          order_keys=(), status: int = 422, **extra):
        """Câu trả lời của một đường ghi — HTML redirect HOẶC JSON.

        Một hàm chứ hai `return` rải khắp ba route: cửa phân biệt client
        phải giống hệt nhau ở mọi đường ghi, nếu không sẽ có đúng một route
        trả HTML cho một lượt fetch và panel treo im lặng.
        """
        if not _workspace_wants_json():
            if error is not None:
                return _workspace_redirect(loi=error, **extra)
            return _workspace_redirect(**{"da-luu": note}, **extra)
        if error is not None:
            return _api_error(mutation_guard.VALIDATION_ERROR, error,
                              status=status)
        return _workspace_write_payload(note=note, order_keys=order_keys)

    def _identify_panel(view: dict, scoped, decisions) -> Optional[dict]:
        """Bảng chọn mặt hàng Tracking cho ĐÚNG MỘT dòng (`§PI-04`).

        Trả `None` khi dòng không tồn tại hoặc không ở trạng thái chưa phân
        loại: một bảng chọn mở trên một dòng đã nhận diện xong sẽ mời Owner
        ghi đè một quyết định mà không ai hỏi họ có muốn không.

        Danh mục RỖNG không bị giấu đi. Nó là một trong hai câu trả lời thật
        của màn hình này — "Tracking đang không nói được" — và nó khác hẳn
        "không có mặt hàng nào khớp".
        """
        keys = _workspace_line_keys()
        if keys is None:
            return None
        detail = view["service"].detail_of(data=view["data"], **keys)
        if detail is None:
            return None
        state = line_identity.state_of(detail, decisions=decisions)
        if not (state.classifiable or state.out_of_catalog):
            return None
        query = request.args.get("tim") or ""
        snapshot = _tracking_snapshot()
        suggestion = identity_gateway.best_candidate(snapshot, query=query)
        # Phạm vi THẬT của lần xác nhận này: mọi dòng của kỳ dùng chung khoá
        # định danh, không riêng dòng vừa bấm (`INV-76`/`INV-87`).
        shared = [item for item in view["data"].details
                  if line_identity.identity_key_of(item.get("product_raw"))
                  == state.identity_key]
        return {
            **keys,
            "product_raw": detail["product_raw"] or "",
            "query": query,
            # R5 §5 — TỐI ĐA MỘT gợi ý. Danh sách bốn mươi mã trong lòng
            # một popover không phải "tương tác nhỏ nhất có thể", và Owner
            # chỉ chọn được đúng một mã. Gợi ý là GỢI Ý: nó chỉ trở thành
            # một quyết định khi Owner bấm vào nó (`§PI-05`, `BR-10`).
            "suggestion": (
                None if suggestion is None
                else {"code": suggestion.code, "label": suggestion.label}),
            "tracking_available": snapshot is not None,
            "no_tracking_note": identity_gateway.NO_TRACKING_NOTE,
            "shared_lines": len(shared),
            "shared_orders": sorted({item["order_key"] for item in shared}),
            # R2 §4.1 — bảng chọn phải nói ĐANG ở trạng thái nào, vì ba trạng
            # thái mở được nó cần ba câu khác nhau: chọn mã lần đầu, chọn LẠI
            # giữa hai mã đang chỏi nhau, và nối lại một mặt hàng đã xác nhận
            # ngoài bảng giá.
            "classification": state.classification,
            "conflict": state.conflict,
            "out_of_catalog": state.out_of_catalog,
            "can_mark_out_of_catalog": not state.out_of_catalog,
        }

    @app.post("/kinh-doanh/nhan-vien/phan-loai")
    def business_confirm_identity():
        """`§PI-05`/`§PI-06` — gửi quyết định phân loại qua thẩm quyền Tracking.

        Route này KHÔNG ghi `inv.map` và không dựng một thẩm quyền identity
        thứ hai. Nó làm đúng ba việc: xác định dòng, đếm phạm vi ảnh hưởng
        thật, rồi gọi `identity_gateway.confirm_identity` — vốn gửi đúng lệnh
        `ConfirmMapping` mà CLI đã dùng, qua đúng `store.append()` với đủ cửa
        `INV-01`/`INV-59`/`INV-68`.

        Không có bước "tính lại giá" nào ở đây, và đó là chủ ý:
        `ECONOMIC_ISOLATION` của `PHB-01` giữ nguyên (`§PI-09`).
        """
        view = _workspace_view()
        keys = _workspace_line_keys()
        if keys is None:
            abort(400)
        detail = view["service"].detail_of(data=view["data"], **keys)
        if detail is None:
            abort(404)
        product_raw = detail["product_raw"] or ""
        identity_key = line_identity.identity_key_of(product_raw)
        if identity_key is None:
            return _workspace_answer(error=line_identity.UNCLASSIFIABLE_NOTE)
        shared = [item for item in view["data"].details
                  if line_identity.identity_key_of(item.get("product_raw"))
                  == identity_key]
        # R2 §4.2/§4.3 — trạng thái HIỆN TẠI của dòng quyết định câu trả lời
        # đúng, và nó được đọc lại ở server chứ không nhận từ form: một form
        # dựng tay không được tự khai rằng nó đang giải quyết một mâu thuẫn,
        # vì đúng lời khai đó là thứ làm hệ thống thôi hỏi lại.
        decisions = _identity_decisions()
        state = line_identity.state_of(detail, decisions=decisions)
        try:
            identity_gateway.confirm_identity(
                identity_store,
                product_raw=product_raw,
                tracking_code=request.form.get("ma_tracking") or "",
                snapshot=_tracking_snapshot(),
                actor_id=identity_gateway.actor_of(),
                affected_orders=tuple(sorted({item["order_key"] for item in shared})),
                affected_lines=len(shared),
                resolves_conflict=state.conflict,
                reason=(request.form.get("ly_do") or None),
                # repair `FIND-R2-IR-02` — chỉ đọc `inv.map` khi thật sự giải
                # mâu thuẫn: đường xác nhận thường không cần, và mỗi lần đọc
                # thêm là một lần pull sống giữ authority thô của Tracking
                # trên đĩa máy chủ lâu hơn cần thiết (`S071 §10`).
                inv_map_snapshot=(
                    _tracking_inv_map_snapshot() if state.conflict else None),
            )
        except identity_gateway.IdentityGatewayError as exc:
            # Bảng chọn mở LẠI ở đúng dòng đó trên đường HTML (người dùng
            # còn việc phải làm ở đây); đường JSON giữ popover đang mở y
            # nguyên và chỉ hiện câu lỗi — `UI-03` §5: không tự gửi lại,
            # không tự đóng, người dùng bấm lại bằng tay.
            return _workspace_answer(error=str(exc), **{
                "phan-loai": "1", "order_key": keys["order_key"],
                "product_key": keys["product_key"],
                "occurrence_index": keys["occurrence_index"]})
        except Exception as exc:  # noqa: BLE001 — xung đột version/log hỏng
            return _workspace_answer(
                error=f"Chưa ghi được phân loại: {exc}", status=500)
        if state.conflict:
            note = identity_gateway.CONFLICT_OK_NOTE
        elif state.out_of_catalog:
            note = identity_gateway.RELINK_OK_NOTE
        else:
            note = identity_gateway.CONFIRM_OK_NOTE
        # `UI-03` §2 — phạm vi THẬT của quyết định này là MỌI BH có dòng dùng
        # chung khoá định danh, không riêng BH vừa bấm. `shared` đã được đếm
        # ở trên cho chính `affected_orders` mà gateway ghi vào log; payload
        # trả về đúng tập ấy nên client vá đủ, không sót dòng nào.
        return _workspace_answer(
            note=note,
            order_keys=sorted({item["order_key"] for item in shared}))

    @app.post("/kinh-doanh/nhan-vien/ngoai-bang")
    def business_mark_out_of_catalog():
        """R2 §4.3 — "mặt hàng này KHÔNG có trên bảng giá Tracking".

        Đây là một KẾT QUẢ PHÂN LOẠI HOÀN TẤT, và route này giữ cho điều đó
        đúng ở cả bốn chỗ mà nó có thể sai:

        1. **Không phải loại dòng.** Nó KHÔNG gọi `exclude_line`. Dòng vẫn góp
           doanh thu, số lượng và chiết khấu y như trước (`§4.3`); thứ duy nhất
           đổi là dòng thôi nằm trong danh sách "chưa phân loại".
        2. **Không phải hết hàng.** `OUT_OF_STOCK` là trạng thái của một NGÀY
           bên Tracking; đây là một khẳng định về MẶT HÀNG.
        3. **Không sinh ra giá.** Không có nhánh nào ghi `0`. Dòng chuyển sang
           "Ngoài bảng giá" và chờ một giá tay — `§4.3` nói thẳng là lợi nhuận
           vẫn Pending cho tới lúc đó.
        4. **Không cần danh mục Tracking.** Bắt pull được danh mục trước khi
           cho phép nói "không có trong danh mục" sẽ khoá đúng thao tác mà
           trạng thái này tồn tại để mở.
        """
        view = _workspace_view()
        keys = _workspace_line_keys()
        if keys is None:
            abort(400)
        detail = view["service"].detail_of(data=view["data"], **keys)
        if detail is None:
            abort(404)
        product_raw = detail["product_raw"] or ""
        identity_key = line_identity.identity_key_of(product_raw)
        if identity_key is None:
            return _workspace_answer(error=line_identity.UNCLASSIFIABLE_NOTE)
        shared = [item for item in view["data"].details
                  if line_identity.identity_key_of(item.get("product_raw"))
                  == identity_key]
        try:
            identity_gateway.mark_out_of_catalog(
                identity_store,
                product_raw=product_raw,
                actor_id=identity_gateway.actor_of(),
                affected_orders=tuple(sorted({item["order_key"] for item in shared})),
                affected_lines=len(shared),
                reason=(request.form.get("ly_do") or None),
            )
        except identity_gateway.IdentityGatewayError as exc:
            return _workspace_answer(error=str(exc))
        except Exception as exc:  # noqa: BLE001 — xung đột version/log hỏng
            return _workspace_answer(
                error=f"Chưa ghi được quyết định ngoài bảng giá: {exc}",
                status=500)
        return _workspace_answer(
            note=identity_gateway.OUT_OF_CATALOG_OK_NOTE,
            order_keys=sorted({item["order_key"] for item in shared}))

    def _workspace_groups(view: dict, scoped, decisions, page: dict) -> list:
        """Các nhóm BH của ĐÚNG một trang bảng kê.

        Đây là lời gọi `sheet_detail_groups` DUY NHẤT của sản phẩm cho bảng
        kê nhân viên — trang đầy đủ, trang kế (`UI-04`) và các lượt vá sau một
        lần ghi (`UI-03`) đều đi qua đây. `catalog`/`imeis` được tra cho đúng
        các dòng của TRANG, không cho cả sheet: chúng chỉ phục vụ những ô sắp
        được vẽ, và tra cả sheet cho một trang trăm dòng là trả lại đúng chi
        phí mà `UI-04` tồn tại để bỏ đi.

        `shades` thì NGƯỢC LẠI — nó là bảng nền của CẢ sheet (xem
        `workspace_presentation.group_shades`): nền xen kẽ theo ngày chỉ đúng
        khi biết BH đứng TRƯỚC lát này rơi vào ngày nào.
        """
        details = page["details"]
        return workspace_presentation.sheet_detail_groups(
            details, sheet=view["sheet"], decisions=decisions,
            catalog=_catalog_labels(details),
            # `DEC-211` — mã máy CHỈ được truy vấn ở đây, trên đúng
            # route này. `workspace_imei` là cánh cửa duy nhất, và
            # `tests/test_r5_imei_boundary.py` canh rằng chỉ file này
            # mở nó.
            imeis=_guarded(
                workspace_imei.imei_of, snapshot_repo.engine,
                [(d["order_key"], d["product_key"], d["occurrence_index"])
                 for d in details]),
            shades=page["shades"])

    def _workspace_context(view: dict, *, cursor: Optional[str] = None,
                           limit: Optional[int] = None,
                           only_orders=None) -> dict:
        """Ngữ cảnh ĐẦY ĐỦ của trang không gian làm việc.

        Tách khỏi `business_employee` vì `UI-03` cần dựng lại MỘT SỐ vùng của
        chính trang này sau một lần ghi, bằng CHÍNH những giá trị mà lần
        render đầy đủ dùng. Một hàm dựng ngữ cảnh riêng cho đường JSON sẽ là
        một bản thứ hai của trang — và bản thứ hai sẽ lệch ở đúng cái ô mà
        không ai nhìn.
        """
        sheet, period = view["sheet"], view["period"]
        scoped = view["data"].for_sheet(sheet)
        target = view["service"].sheet_target(sheet=sheet, period=period)
        today = _today()

        pending = _workspace_line_keys() if request.args.get("xac-nhan") else None
        confirm = None
        if pending is not None:
            kind = request.args.get("xac-nhan")
            if kind in ("gia-dung", "loai"):
                confirm = {"kind": kind, **pending}

        decisions = _identity_decisions()

        # `DEC-185` §PI-04 — bảng chọn mặt hàng của ĐÚNG MỘT dòng, mở ngay
        # trong bảng kê. Nó chỉ được dựng khi Owner đã bấm vào một dòng cụ
        # thể (`phan-loai`), nên danh mục Tracking không bị đọc ở mỗi lần
        # tải trang.
        identify = None
        if request.args.get("phan-loai"):
            identify = _identify_panel(view, scoped, decisions)

        # `UI-04` — MỘT TRANG của bảng kê, cắt theo ranh giới BH.
        # `only_orders` (`UI-03`) là một lát KHÁC: chỉ những BH vừa bị một
        # lần ghi làm đổi, để vá tại chỗ thay vì dựng lại cả trang.
        if only_orders is None:
            page = workspace_presentation.page_of_groups(
                scoped.details, cursor=cursor,
                limit=(workspace_presentation.WORKSPACE_PAGE_LINES
                       if limit is None else limit))
        else:
            page = workspace_presentation.groups_slice(
                scoped.details, only_orders)

        # `§13`/`§PI-10` — ĐÚNG MỘT dòng cảnh báo cho cả sheet, hoặc `None`.
        # Nó đếm trên CẢ sheet, không trên trang đang mở: một cảnh báo im đi
        # vì Owner chưa cuộn tới chỗ có vấn đề là một cảnh báo nói dối.
        identity_warning = line_identity.sheet_warning(
            scoped.details, decisions=decisions)
        # …nên neo `#bh-…` của nó có thể nằm ở một trang khác. Liên kết mang
        # theo con trỏ của ĐÚNG trang chứa BH ấy, nếu không nó là một neo trỏ
        # vào một phần tử không tồn tại trên màn hình (`UI-04`).
        warning_cursor = (
            workspace_presentation.cursor_for_order(
                scoped.details, identity_warning["orders"][0])
            if identity_warning and identity_warning.get("orders") else None)

        return dict(
            periods=workspace_presentation.period_options(
                _guarded(analytics_queries.available_periods,
                         snapshot_repo.engine),
                selected=period, today=today),
            selected_period=view["selected_period"],
            tabs=workspace_presentation.sheet_tabs(view["sheets"], sheet.key),
            sheet=workspace_presentation.sheet_view(
                sheet, scoped.totals, period=period),
            strip=workspace_presentation.summary_strip(
                scoped.totals, period=period,
                previous_totals=_workspace_previous(view),
                target=target, today=today),
            target=workspace_presentation.target_cell(target),
            columns=workspace_presentation.SHEET_DETAIL_COLUMNS,
            groups=_workspace_groups(view, scoped, decisions, page),
            page=page,
            warning_cursor=warning_cursor,
            optional_columns=workspace_presentation.OPTIONAL_COLUMN_INDEXES,
            show_optional_label=workspace_presentation.SHOW_OPTIONAL_LABEL,
            hide_optional_label=workspace_presentation.HIDE_OPTIONAL_LABEL,
            optional_columns_note=workspace_presentation.OPTIONAL_COLUMNS_NOTE,
            # `UI-04` — hàng TỔNG vẫn cộng trên CẢ sheet (`scoped.details`),
            # không trên trang đang tải. Một hàng tổng cộng theo những dòng
            # đã tải sẽ nhỏ dần theo đúng phần người dùng chưa cuộn tới, và
            # không có ô nào trên màn hình nói ra điều đó.
            detail_totals=workspace_presentation.sheet_detail_totals(
                scoped.details),
            identity_warning=identity_warning,
            # `R5.1 REPAIR-2` — bản chiếu hiển thị vắng mặt trong khi CÓ mapping
            # đã xác nhận. Không có dòng này thì cột Hãng/Nhóm hàng chỉ có dấu
            # gạch mà không gì trên màn hình giải thích vì sao — đúng triệu
            # chứng production đã gặp.
            catalog_projection_warning=_catalog_projection_warning(
                scoped.details),
            identify=identify,
            unclassifiable_note=line_identity.UNCLASSIFIABLE_NOTE,
            excluded=workspace_presentation.excluded_rows(view["data"].excluded),
            # R5 §1 — danh sách RIÊNG cho các dòng đã tạm loại vì không còn
            # trong sổ đã xác nhận đầy đủ. Lọc theo đúng sheet đang xem, cùng
            # cách `scoped` lọc mọi thứ khác: một cảnh báo của sheet khác nằm
            # trên màn hình này là một việc không phải của người đang đọc.
            removed_in_source=workspace_presentation.removed_in_source_rows(
                view["data"].removed_for_sheet(sheet)),
            # `FIND-R5-IR-01` — `keep_option=True` BẮT BUỘC ở đây và chỉ ở
            # đây: đây là màn hình duy nhất mà ô chọn nhân viên đi cùng một
            # nút gửi DÙNG CHUNG (`XONG` lưu cả giá lẫn nhân viên). Bảng kê
            # chi tiết (route dưới) vẫn có nút gửi riêng nên vẫn không có
            # mục trống, đúng `OD-5`.
            assignable=business_presentation.assignable_employee_options(
                view["service"].assignable_employees(), keep_option=True),
            editing=request.args.get("sua") or "",
            editing_target=bool(request.args.get("sua-target")),
            confirm=confirm,
            message=request.args.get("da-luu") or None,
            error=request.args.get("loi") or None,
        )

    @app.get("/kinh-doanh/nhan-vien")
    def business_employee():
        """Không gian làm việc theo SHEET — `DEC-PHB02-08` §4/§5/§14/§22.

        `UI-04` — trang này dựng MỘT TRANG của bảng kê, vẫn hoàn toàn ở
        server. Không JavaScript, `XEM TIẾP` ở cuối bảng là một liên kết
        THẬT (`?tu=<mã BH>`) và mọi dòng của sheet vẫn tới được. Có
        JavaScript, `app.js` chặn liên kết đó, gọi route JSON
        `/api/v1/periods/<kỳ>/workspace` và NỐI thêm các hàng vào bảng —
        không tải lại trang, không dựng lại `#app-content`.
        """
        view = _workspace_view()
        return render_template(
            "kinh_doanh_nhan_vien.html",
            **_workspace_context(view, cursor=request.args.get("tu") or None))
    @app.post("/kinh-doanh/nhan-vien/target")
    def business_save_sheet_target():
        """Đặt/gỡ Target của SHEET đang xem, nhập theo NGHÌN ĐỒNG (`§17`).

        Ba ranh giới, kiểm ở đây chứ không chỉ trên form:

        1. Sheet phải tồn tại VÀ phải có chủ thể chịu trách nhiệm. Nhóm "chưa
           xác định nhân viên" không đặt Target được — một chỉ tiêu cho tập
           dòng chưa biết của ai là con số không ai chịu trách nhiệm.
        2. Giá trị đi qua `parse_target_kvnd`: rỗng = GỠ, `>= 0` = ĐẶT (kể cả
           `0`), âm/không phải số nguyên = TỪ CHỐI kèm câu nói rõ.
        3. Kho lưu vẫn là VND. Việc đổi đơn vị xảy ra ĐÚNG MỘT LẦN, ở
           `parse_target_kvnd`, nên không có đường nào nhân 1.000 hai lần
           (`§20`).
        """
        view = _workspace_view()
        sheet, period = view["sheet"], view["period"]
        # `TASK-OWNER-UIUX-003` §6 — ô nhập Target giờ ẩn sau icon sửa
        # (`sua-target=1`); LƯU xong phải quay lại đúng trạng thái đang mở
        # đó, không thì Owner bấm LƯU xong lại thấy ô nhập biến mất.
        reopen = {"sua-target": "1"}
        if sheet.unresolved or (not sheet.is_group and not sheet.employee):
            return _workspace_redirect(loi=(
                "Nhóm chưa xác định nhân viên không đặt Target được."),
                **reopen)
        try:
            target = business_store.parse_target_kvnd(request.form.get("target"))
        except business_store.InvalidTargetError as exc:
            return _workspace_redirect(loi=str(exc), **reopen)
        # Target là con số CỦA MỘT THÁNG, nên cửa chặn hỏi thẳng tháng đó.
        _guarded(view["service"].guard_period_open, period)
        label = sheet.label or business_presentation.UNKNOWN_EMPLOYEE
        if target is None:
            _guarded(view["service"].clear_sheet_target,
                     sheet=sheet, period=period)
            return _workspace_redirect(**{"da-luu": (
                f"Đã gỡ Target của {label} trong "
                f"{business_presentation.period_label(period)}."), **reopen})
        _guarded(view["service"].set_sheet_target,
                 sheet=sheet, period=period, target_vnd=target)
        return _workspace_redirect(**{"da-luu": (
            f"Đã lưu Target của {label} trong "
            f"{business_presentation.period_label(period)}."), **reopen})

    @app.post("/kinh-doanh/nhan-vien/don")
    def business_save_order_employee():
        """`§27` — đổi nhân viên cho TOÀN BỘ một BH bằng một thao tác.

        R5 §4 — không gian làm việc KHÔNG còn nút `GÁN CẢ ĐƠN` gọi route
        này: nhân viên nay đi cùng giá nhập qua một lần gửi duy nhất
        (`business_save_order`). Route ở lại vì nó là bề mặt đã nghiệm thu
        của `§27` và mang bằng chứng test của `DEC-185` §F-02. Nó KHÔNG phải
        một thẩm quyền thứ hai: cả hai đường vào đều gọi đúng
        `store.set_employee` trên đúng khoá nghiệp vụ của từng dòng, và cùng
        đọc master `config/employees.yaml` để biết tên nào có thật.

        Đây KHÔNG phải một thẩm quyền gán nhân viên thứ hai: nó gọi đúng
        `BusinessDecisionStore.set_employee` mà `OD-5` đã nghiệm thu, một lần
        cho mỗi dòng của đơn. Ranh giới của `OD-5` vì thế còn nguyên — tên
        phải nằm trong master `config/employees.yaml`, và bằng chứng gốc
        (`source_employee_at_entry`) vẫn được ghi lại trên từng dòng.

        Vì sao lặp ở tầng route thay vì thêm một hàm "gán cả đơn" vào store:
        store là nơi giữ MỘT quyết định trên MỘT khoá nghiệp vụ. Một phương
        thức nhận `order_key` và tự đi tìm các dòng của nó sẽ là một quyết
        định trên một tập dòng mà khoá của nó không có trong bảng — và lần
        sau ai đó sẽ hỏi tập đó được chốt lúc nào.
        """
        view = _workspace_view()
        service = view["service"]
        order_key = request.form.get("order_key") or ""
        chosen = (request.form.get("nhan_vien_moi") or "").strip()
        groups = dict(service.assignable_employees())
        if chosen not in groups:
            return _workspace_redirect(loi=(
                f"{chosen!r} không có trong danh sách nhân viên. Hãy chọn một "
                "tên trong danh sách."))
        # `DEC-185` §F-02 — "cả BH" nghĩa là CẢ BH, kể cả dòng đã bị loại.
        #
        # `PeriodData.details` cố ý chỉ chứa các dòng CÒN được báo cáo, và đó
        # là điều đúng cho mọi phép gộp. Nhưng ở đây nó là tập sai: loại một
        # dòng nghĩa là "không tính vào báo cáo" (`§30`), KHÔNG phải "dòng này
        # không còn thuộc BH". Đọc riêng `details` làm một lần gán BH bỏ sót
        # đúng những dòng đang ẩn, và sự bỏ sót đó chỉ lộ ra sau khi Owner
        # khôi phục — lúc dòng quay lại mang tên nhân viên CŨ, cạnh các dòng
        # anh em đã mang tên mới.
        #
        # Không có thẩm quyền gán nào thứ hai được dựng: vẫn đúng
        # `store.set_employee` trên đúng khoá nghiệp vụ của từng dòng.
        details = [detail for detail in
                   (*view["data"].details, *view["data"].excluded)
                   if detail["order_key"] == order_key]
        if not details:
            abort(404)
        _guard_lines(service, *details)
        for detail in details:
            _guarded(service.store.set_employee,
                     order_key=detail["order_key"],
                     product_key=detail["product_key"],
                     occurrence_index=detail["occurrence_index"],
                     employee=chosen, employee_group=groups[chosen],
                     source_employee=detail["line"].source_employee)
        hidden = sum(1 for detail in details if "exclusion" in detail)
        note = ("" if not hidden else
                f" (gồm {hidden} dòng đang bị loại khỏi báo cáo — khôi phục "
                "lúc nào chúng cũng mang tên mới)")
        return _workspace_redirect(**{"da-luu": (
            f"Đã gán {len(details)} dòng của {order_key} cho {chosen}{note}. "
            "Tổng của cả kỳ không đổi.")})

    _PRICE_FIELD = re.compile(r"^gia_nhap__([0-9a-f]+)__(\d+)$")

    def _submitted_prices(order_key: str) -> dict:
        """`{khoá dòng: chuỗi người gõ}` đọc từ form sửa BH (R5 §4).

        Tên ô mang ĐỦ khoá dòng (`gia_nhap__<product_key>__<occurrence>`) chứ
        không mang một chỉ số hàng: một chỉ số hàng chỉ đúng cho đến khi thứ
        tự dòng đổi, và R3 §1 đã trả giá một lần cho việc để vị trí làm danh
        tính. `order_key` đến từ chính trường ẩn của form, nên ba thành phần
        khoá luôn đi cùng nhau.

        Tên ô sai dạng bị BỎ QUA chứ không đoán: một trường lạ trong form là
        một trường không ai hứa gì về nó.
        """
        prices = {}
        for name, value in request.form.items():
            match = _PRICE_FIELD.match(name)
            if match is None:
                continue
            prices[(order_key, match.group(1), int(match.group(2)))] = value
        return prices

    @app.post("/kinh-doanh/nhan-vien/sua-bh")
    def business_save_order():
        """R5 §4 — lưu TOÀN BỘ một BH bằng đúng một lần gửi.

        Route này KHÔNG dựng một thẩm quyền nào mới. Nó gọi đúng
        `store.set_purchase_price` / `clear_purchase_price` / `set_employee`
        mà `DEC-PHB02-02` và `OD-5` đã nghiệm thu, và mọi ràng buộc của R2
        §4.4 (giá AUTO đọc lại từ server, override phải có lý do, actor đọc
        từ môi trường chứ không từ form) còn nguyên — chúng chỉ được kiểm
        MỘT LƯỢT cho cả đơn thay vì từng ô một.

        Hai bước, và thứ tự là hợp đồng: kiểm hết (`plan_order_edit`), rồi
        mới ghi (`apply_order_edit`). Không có nhánh nào ghi một phần rồi
        báo lỗi — đó chính là lớp lỗi mà `§4` sinh ra để đóng.
        """
        view = _workspace_view()
        service = view["service"]
        order_key = request.form.get("order_key") or ""
        chosen = (request.form.get("nhan_vien_moi") or "").strip()
        try:
            plan = service.plan_order_edit(
                data=view["data"], order_key=order_key,
                employee=chosen or None,
                prices=_submitted_prices(order_key),
                reason=(request.form.get("ly_do") or None))
        except business_service.OrderNotFoundError:
            abort(404)
        if not plan.ok:
            # Giữ chế độ sửa MỞ: người dùng vừa gõ một màn hình dữ liệu, và
            # đóng nó lại cùng lúc với việc báo lỗi là bắt họ gõ lại từ đầu.
            return _workspace_redirect(sua=order_key,
                                       loi=" ".join(plan.errors))
        # Cửa kỳ đã chốt đứng SAU khi kiểm form và TRƯỚC khi ghi: một kỳ đã
        # chốt phải chặn cả lần sửa hợp lệ, và chặn nó bằng cùng một câu mà
        # mọi đường ghi khác của vertical đang dùng.
        _guard_lines(service, *plan.details)
        if plan.changes_nothing:
            return _workspace_redirect(**{"da-luu": plan.summary()})
        message = _guarded(service.apply_order_edit, plan,
                           entered_by=identity_gateway.actor_of())
        return _workspace_redirect(**{"da-luu": message})

    @app.post("/kinh-doanh/nhan-vien/gia-nhap")
    def business_save_line_purchase_price():
        """`§28` — sửa Giá nhập ngay trong ô của dòng, khi BH đang mở sửa.

        R5 §4 — không gian làm việc KHÔNG còn nút `LƯU` từng ô gọi route
        này; giá nhập nay đi qua form cấp BH (`business_save_order`). Route
        ở lại vì nó là bề mặt đã nghiệm thu của R2 §4.4 và mang bằng chứng
        test của cả vertical đó. Không có thẩm quyền giá nhập thứ hai nào
        được dựng: cả hai đường vào đều đọc lại giá AUTO từ server rồi gọi
        đúng `store.set_purchase_price`, nơi ràng buộc "override phải có lý
        do" được thi hành MỘT lần cho mọi người gọi.

        Dùng LẠI nguyên vẹn thẩm quyền giá nhập của `DEC-PHB02-02`/PHB-03:
        cùng `parse_purchase_price`, cùng `auto_price_of` (giá AUTO luôn đọc
        lại từ server, không nhận từ trình duyệt), cùng `set_purchase_price`.
        `§28` cấm dựng một thẩm quyền giá nhập thứ hai, và ở đây không có cái
        nào được dựng — chỉ có một ô nhập ở một chỗ khác.
        """
        view = _workspace_view()
        service = view["service"]
        keys = _workspace_line_keys()
        if keys is None:
            abort(400)
        exists, auto_price = service.auto_price_of(data=view["data"], **keys)
        if not exists:
            abort(404)
        _guard_lines(service, service.detail_of(data=view["data"], **keys))
        if request.form.get("hanh-dong") == "go":
            _guarded(service.store.clear_purchase_price, **keys)
            return _workspace_redirect(sua=keys["order_key"], **{"da-luu": (
                "Đã gỡ giá nhập do Owner nhập. Dòng trở lại giá tự động.")})
        try:
            price = business_store.parse_purchase_price(
                request.form.get("gia_nhap"))
        except business_store.InvalidPurchasePriceError as exc:
            return _workspace_redirect(sua=keys["order_key"], loi=str(exc))
        try:
            # R2 §4.4 — `entered_by`/`reason` là hai nửa còn thiếu của
            # provenance. Actor đọc từ môi trường, KHÔNG từ form: một form dựng
            # tay không được tự khai ai đã quyết định.
            provenance = _guarded(
                service.store.set_purchase_price,
                price=price, auto_price=auto_price,
                entered_by=identity_gateway.actor_of(),
                reason=(request.form.get("ly_do") or None), **keys)
        except business_store.MissingPriceReasonError as exc:
            return _workspace_redirect(sua=keys["order_key"], loi=str(exc))
        return _workspace_redirect(sua=keys["order_key"], **{"da-luu": (
            "Đã ghi giá nhập Owner sửa (thay giá tự động)."
            if provenance == business_metrics.PROVENANCE_MANUAL_OVERRIDE
            else "Đã ghi giá nhập Owner nhập.")})

    @app.post("/kinh-doanh/nhan-vien/gia-dung")
    def business_classify_line_gia_dung():
        """`§9`–`§11` — chuyển ĐÚNG MỘT DÒNG sang Gia dụng, hoặc gỡ lại.

        Ranh giới, kiểm ở đây chứ không chỉ ở giao diện:

        - Chỉ dòng của nhóm NỘI THÀNH mới chuyển được. `DEC-PHB02-05` giới hạn
          tỉ lệ 8 % cho riêng nhóm này, và một dòng của nhân viên bán lẻ mang
          nhãn `GIA_DUNG` vẫn quy đổi 5,5 % — nút bấm sẽ không có tác dụng
          kinh tế nào, tức là một nút nói dối.
        - Đúng MỘT dòng, không phải cả BH và không phải mọi lần bán của mặt
          hàng (`§10`). Khoá là `(order_key, product_key, occurrence_index)`.
        - Nhân viên bán, khách hàng, đơn giá và bằng chứng gốc KHÔNG đổi
          (`§11`): route này chỉ ghi vào bảng phân loại cấp dòng.
        """
        view = _workspace_view()
        service = view["service"]
        keys = _workspace_line_keys()
        if keys is None:
            abort(400)
        detail = service.detail_of(data=view["data"], **keys)
        if detail is None:
            abort(404)
        if not gia_dung_workflow_applies(detail["line"].employee_group):
            abort(404)
        _guard_lines(service, detail)
        if request.form.get("hanh-dong") == "go":
            _guarded(service.store.clear_line_product_group, **keys)
            return _workspace_redirect(**{"da-luu": (
                "Đã trả dòng này về Nội thành.")})
        _guarded(service.store.set_line_product_group,
                 product_group=GIA_DUNG, **keys)
        return _workspace_redirect(**{"da-luu": (
            "Đã chuyển dòng này sang Gia dụng. Nhân viên bán và số liệu kế "
            "toán của dòng giữ nguyên; doanh thu công ty không đổi.")})

    @app.post("/kinh-doanh/nhan-vien/loai-dong")
    def business_exclude_line():
        """`§29`–`§32` — loại MỘT dòng khỏi báo cáo, hoặc khôi phục nó.

        "Xoá" ở đây là một QUYẾT ĐỊNH có thể đảo ngược, không phải một lệnh
        xoá dữ liệu: bản ghi kế toán gốc không bị đụng tới (`§31`), và dòng
        khôi phục lại được từ chính màn hình này (`§56` CASE EX-07).

        Nó KHÁC hẳn phân loại Gia dụng và không được cài bằng nhau (`§33`):
        loại ⟹ dòng biến khỏi MỌI chỉ tiêu; phân loại ⟹ dòng vẫn được báo
        cáo, chỉ đổi bucket và tỉ lệ.
        """
        view = _workspace_view()
        service = view["service"]
        keys = _workspace_line_keys()
        if keys is None:
            abort(400)
        if request.form.get("hanh-dong") == "khoi-phuc":
            dropped = {(item["order_key"], item["product_key"],
                        item["occurrence_index"]): item
                       for item in view["data"].excluded}
            item = dropped.get((keys["order_key"], keys["product_key"],
                                keys["occurrence_index"]))
            if item is None:
                abort(404)
            _guard_lines(service, item)
            _guarded(service.store.restore_line, **keys)
            return _workspace_answer(
                note="Đã khôi phục dòng. Nó được tính lại vào báo cáo từ bây giờ.",
                order_keys=[keys["order_key"]])
        detail = service.detail_of(data=view["data"], **keys)
        if detail is None:
            abort(404)
        _guard_lines(service, detail)
        _guarded(service.store.exclude_line, **keys)
        # Một BH có thể MẤT HẲN khỏi bảng khi đây là dòng cuối của nó —
        # `_workspace_write_payload` phát hiện điều đó bằng cách dựng lại lát
        # và thấy BH không còn nhóm nào, rồi trả `removed_order_keys`.
        return _workspace_answer(
            note=("Đã loại dòng này khỏi báo cáo. Sổ kế toán gốc giữ nguyên — "
                  "bấm KHÔI PHỤC ở cuối trang là dòng trở lại."),
            order_keys=[keys["order_key"]])

    # --- PHB-05: Target tháng của nhân viên (DEC-PHB02-06) ---------------

    # ------------------------------------------------------------------
    # PHB-06 — BÁO CÁO THEO THƯƠNG HIỆU.
    #
    # Một KHUNG NHÌN CON của Báo cáo, mở từ trang `/kinh-doanh`. Nó KHÔNG là
    # một tab chính mới: `DEC-185` giữ thanh điều hướng đúng BA mục (Báo cáo ·
    # Nhân viên · Dữ liệu), và một chiều gộp mới không phải một lý do đủ để
    # đổi điều hướng chính (`PHB-06 §6`, `BR-12`).
    #
    # Kỳ đi qua `_workspace_period()` — mặc định THÁNG DƯƠNG LỊCH HIỆN TẠI,
    # luôn là một tháng thật (`PHB-06 §5`, `BR-03`). Đây là mô hình kỳ đã
    # nghiệm thu của không gian làm việc, dùng lại nguyên vẹn; không có khung
    # lọc mới và không có mục "Toàn bộ dữ liệu" nào được thêm.
    # ------------------------------------------------------------------

    @app.get("/kinh-doanh/thuong-hieu")
    def business_brand():
        """Kết quả nghiệp vụ CHÍNH THỨC của kỳ, gộp theo thương hiệu.

        Ba tính chất được giữ bằng CẤU TẠO chứ không bằng lời hứa:

        1. **Cùng một kết quả chính thức.** Trang đọc `service.period(...)` —
           đúng lời gọi mà Báo cáo, Nhân viên và dòng thời gian doanh thu đã
           dùng. Dòng Owner đã loại không có mặt trong `data.lines` (xem
           `business_service.PeriodData`), nên chúng không thể lọt vào một
           bucket thương hiệu nào (`BR-05`).

        2. **Chỉ PHÂN HOẠCH, không tính lại.** `group_by_brand` chia đúng tập
           `data.lines` rồi gọi lại `business_metrics.totals` trên từng phần.
           Không có công thức doanh thu/lợi nhuận/quy đổi thứ hai ở đâu trong
           đường này, nên gán lại nhân viên hay tick Gia dụng không thể làm
           đổi doanh thu của một thương hiệu (`BR-06`, `BR-07`).

        3. **Thương hiệu chỉ ĐỌC từ thẩm quyền Product Identity.** R5 §5
           (`DEC-R5-04`) mở lại PHB-06 CÓ CHỦ ĐÍCH: nguồn nay là
           `catalog_display.brand_source`, tức chính hai trường mà TRACKING
           đã chuẩn hoá và trả về qua `/api/xuat/board`. Đây là đường thứ hai
           mà `PHB-06 §4` đã để ngỏ — một read model canonical tương đương —
           chứ không phải một bảng ánh xạ của Reports: nó chỉ tra
           `source_product_code` của một danh tính ĐÃ CONFIRM, và không có
           nhánh nào suy thương hiệu từ tên hàng, mã máy hay một phép so
           chuỗi nào (`BR-02`, `BR-10`).

           `brand_identity.canonical_brand` KHÔNG bị xoá: nó vẫn là đường
           đọc đúng nếu hợp đồng danh tính có ngày mang trường `brand` trên
           chính nó, và `tests/test_phb06_brand_reporting.py` vẫn canh nó.

        Phép đối soát về tổng kỳ CHẠY THẬT ở mỗi lần tải trang và kết quả của
        nó lên màn hình. Một bảng cộng không khớp là lỗi hệ thống, và trang
        phải nói ra ngay thay vì để Owner phát hiện bằng máy tính tay.
        """
        service = _require_business()
        period = _workspace_period()
        bounds = analytics_queries.month_bounds(*period)
        data = _guarded(service.period, date_from=bounds[0], date_to=bounds[1])
        buckets = brand_identity.buckets_for(
            data.details, confirmed_keys=_confirmed_identity_keys(),
            identities=identity_gateway.confirmed_identities(identity_store),
            brand_source=catalog_display.brand_source(_tracking_display()))
        grouped = brand_metrics.group_by_brand(data.lines, buckets)
        return render_template(
            "kinh_doanh_thuong_hieu.html",
            periods=workspace_presentation.period_options(
                _guarded(analytics_queries.available_periods,
                         snapshot_repo.engine),
                selected=period, today=_today()),
            selected_period=f"{period[0]}-{period[1]:02d}",
            columns=business_presentation.BRAND_COLUMNS,
            rows=business_presentation.brand_rows(grouped, data.totals),
            summary=business_presentation.brand_summary(
                brand_identity.coverage(buckets),
                brand_metrics.reconciliation(grouped, data.totals),
                period=period, totals=data.totals))

    # ------------------------------------------------------------------
    # PHB-07 — CƠ CẤU DOANH THU THEO ĐƠN VỊ BÁO CÁO.
    #
    # Một KHUNG NHÌN CON nữa của Báo cáo, mở từ trang `/kinh-doanh` — KHÔNG
    # một tab chính mới (`DEC-185` giữ thanh điều hướng đúng BA mục).
    #
    # Câu hỏi nghiệp vụ: *"doanh thu của kỳ này đến từ những đơn vị báo cáo
    # nào, mỗi đơn vị chiếm bao nhiêu phần trăm?"* — đúng hình dạng khối tháng
    # của sổ cũ (`TASK-PRA-000` §C.1: 5–7 dòng người bán/kênh + một dòng tổng
    # tháng), và đúng chỉ tiêu đã được phân loại `NOW` ở §L của cùng tài liệu
    # (*"Employee contribution (share) — doanh thu NV / tổng"*).
    #
    # Reports hôm nay đã có đủ số của TỪNG đơn vị, nhưng chỉ xem được mỗi lần
    # MỘT đơn vị qua hàng tab của không gian làm việc. Trang này không thêm
    # một chỉ tiêu nào — nó đặt cùng những con số ấy cạnh nhau.
    # ------------------------------------------------------------------

    @app.get("/kinh-doanh/co-cau")
    def business_composition():
        """Kết quả nghiệp vụ CHÍNH THỨC của kỳ, gộp theo đơn vị báo cáo.

        Bốn tính chất được giữ bằng CẤU TẠO chứ không bằng lời hứa:

        1. **Cùng một kết quả chính thức.** Trang đọc `service.period(...)` —
           đúng lời gọi mà Báo cáo, Nhân viên, bảng thương hiệu và dòng thời
           gian doanh thu đã dùng. Dòng Owner đã loại không có mặt trong
           `data.lines`, nên chúng không thể lọt vào một đơn vị nào.

        2. **Chỉ PHÂN HOẠCH, không tính lại.** `group_by_unit` chia đúng tập
           `data.lines` rồi gọi lại `business_metrics.totals` trên từng phần.
           Không có công thức doanh thu/lợi nhuận/quy đổi thứ hai ở đâu trong
           đường này.

        3. **Không có phân loại thứ hai.** Một dòng thuộc đơn vị nào là câu
           hỏi mà `reporting_sheets.sheet_key_of` đã trả lời cho không gian
           làm việc; trang này đọc lại đúng câu trả lời đó qua
           `PeriodData.sheet_assignments()`. Vì vậy hàng tab và bảng cơ cấu
           không thể nói hai câu khác nhau.

        4. **Không đếm hai lần.** Vinh · Quý · Hiệp KHÔNG có dòng riêng: các
           dòng của họ nằm trong đơn vị Nội thành hoặc Gia dụng. Đó là hệ quả
           của việc chỉ có MỘT phân hoạch, không phải một quy tắc phải nhớ.

        Phép đối soát về tổng kỳ CHẠY THẬT ở mỗi lần tải trang và kết quả của
        nó lên màn hình.
        """
        service = _require_business()
        period = _workspace_period()
        bounds = analytics_queries.month_bounds(*period)
        data = _guarded(service.period, date_from=bounds[0], date_to=bounds[1])
        units = [contribution.unit_for(sheet_key, employee)
                 for sheet_key, employee in data.sheet_assignments()]
        grouped = contribution.group_by_unit(data.lines, units)
        return render_template(
            "kinh_doanh_co_cau.html",
            periods=workspace_presentation.period_options(
                _guarded(analytics_queries.available_periods,
                         snapshot_repo.engine),
                selected=period, today=_today()),
            selected_period=f"{period[0]}-{period[1]:02d}",
            columns=business_presentation.COMPOSITION_COLUMNS,
            rows=business_presentation.composition_rows(grouped, data.totals),
            summary=business_presentation.composition_summary(
                contribution.reconciliation(grouped, data.totals),
                period=period, totals=data.totals, units=len(grouped)))

    @app.get("/kinh-doanh/target")
    def business_target():
        """Đặt/sửa Target tháng cho từng nhân viên — bảng kiểu bảng tính.

        Đây là MỘT khung nhìn con của vertical NGHIỆP VỤ, mở từ trang Nhân
        viên; nó KHÔNG là một tab chính mới (`R1` giữ nguyên bốn tab). Nội
        dung đúng những gì Owner cần để ra quyết định trên một dòng:

            Nhân viên · DS quy đổi hiện tại · Target · So target · Sửa

        Kỳ `Toàn bộ dữ liệu` KHÔNG sửa được Target: Target là con số của một
        THÁNG (`DEC-PHB02-06`), và một ô nhập không biết mình đang ghi vào
        tháng nào là một ô nhập ghi vào tháng sai.
        """
        view = _business_period()
        period = view["period"]
        return render_template(
            "kinh_doanh_target.html", periods=view["periods"],
            selected_period=view["selected_period"],
            period_label=business_presentation.period_label(period),
            has_period=period is not None,
            columns=business_presentation.TARGET_COLUMNS,
            rows=business_presentation.target_rows(
                view["service"].target_rows(period=period, data=view["data"]),
                editable=period is not None),
            message=request.args.get("da-luu") or None,
            error=request.args.get("loi") or None)

    @app.post("/kinh-doanh/target")
    def business_save_target():
        """Ghi hoặc gỡ Target của MỘT nhân viên trong MỘT tháng.

        Ba ranh giới được kiểm ở đây, không chỉ ở trang GET — một POST dựng
        tay vẫn phải đi qua đủ cả ba:

        1. Phải có KỲ cụ thể. `Toàn bộ dữ liệu` ⟹ 404: không có tháng nào để
           ghi vào, và đoán hộ một tháng là ghi vào tháng sai.
        2. Tên nhân viên phải nằm trong master `config/employees.yaml` — cùng
           thẩm quyền mà `OD-5` đã dùng. Gõ tự do một cái tên vào bảng Target
           sẽ dựng ra một "nhân viên" chỉ tồn tại trong cột Target.
        3. Giá trị phải hợp lệ. Rỗng = GỠ; `>= 0` = ĐẶT (kể cả `0`); âm hoặc
           không phải số = TỪ CHỐI kèm câu nói rõ vì sao.

        Route này KHÔNG chạm vào một bảng số liệu nào: nó chỉ ghi
        `employee_target`. Không có đường nào từ đây tới snapshot, tới dòng
        chứng từ, hay tới bảng Legacy.
        """
        view = _business_period()
        service = view["service"]
        period = view["period"]
        redirect_args = {"ky": request.values.get("ky") or "tat-ca"}

        def _back(**extra):
            return redirect(url_for("business_target", **redirect_args, **extra))

        if period is None:
            abort(404)
        chosen = (request.form.get("nhan_vien") or "").strip()
        if chosen not in dict(service.assignable_employees()):
            return _back(loi=(
                f"{chosen!r} không có trong danh sách nhân viên. Target chỉ "
                "đặt được cho một nhân viên trong master."))
        try:
            target = business_store.parse_target(request.form.get("target"))
        except business_store.InvalidTargetError as exc:
            return _back(loi=str(exc))
        _guarded(service.guard_period_open, period)
        if target is None:
            _guarded(service.clear_employee_target,
                     period=period, employee_key=chosen)
            return _back(**{"da-luu": (
                f"Đã gỡ Target của {chosen} trong "
                f"{business_presentation.period_label(period)}. "
                "Người này trở lại trạng thái chưa thiết lập target.")})
        _guarded(service.set_employee_target,
                 period=period, employee_key=chosen, target_vnd=target)
        return _back(**{"da-luu": (
            f"Đã lưu Target của {chosen} trong "
            f"{business_presentation.period_label(period)}.")})

    # Bốn chế độ lọc của bảng kê. Chúng KHÔNG chồng lên nhau và mỗi cái trả
    # lời một câu hỏi khác của Owner — gộp lại thành một danh sách "còn thiếu"
    # chung chính là cái đã khiến `B03` xảy ra.
    #
    # `S120`: MẶC ĐỊNH là `tat-ca`, không còn là `thieu-gia`. Bảng kê chi tiết
    # là KHUNG NHÌN BÁO CÁO của một nhân viên/kỳ, không phải hàng đợi việc
    # tồn: mặc định lọc bỏ mọi dòng đã đủ giá khiến Owner mở trang ra và thấy
    # một tập con mà trang không nói là tập con — và khi coverage đã 100 %,
    # cùng đường dẫn đó cho ra một bảng RỖNG. Ba bộ lọc thu hẹp vẫn còn
    # nguyên, chỉ khác là Owner phải chọn chúng một cách tường minh.
    # Bộ lọc nhận `(line, state)` — `state` là trạng thái phân loại HIỆU LỰC
    # của chính dòng đó (`line_identity`). Bốn bộ lọc của R2 (`§Gói 4`) cần nó:
    # "thiếu giá" gộp bốn tình huống có bốn hành động khác nhau, và một hàng
    # đợi xử lý mà không tách được chúng thì không giúp ai xử lý được gì.
    _DETAIL_FILTERS = {
        "tat-ca": lambda line, state, flagged: True,
        # Việc Owner gõ được ngay bây giờ.
        "thieu-gia": lambda line, state, flagged: line.purchase_price is None,
        # Dòng đã có lãi nhưng chưa biết của ai (`OD-5`).
        "chua-ro-nv": lambda line, state, flagged: (line.contributes_profit
                                           and not line.employee_resolved),
        # `R3` — "dòng tôi đã sửa": CHỈ đọc lại provenance đã lưu (giá nhập
        # Owner nhập/sửa, hoặc nhân viên Owner gán lại). Không trạng thái mới,
        # không workflow mới, không ghi gì.
        "owner-sua": lambda line, state, flagged: (
            line.purchase_provenance in _OWNER_EDITED_PROVENANCE
            or line.employee_provenance == "MANUAL"),
        # --- R2 §Gói 4 — bốn hàng đợi, bốn hành động ---------------------
        # 1. Chưa phân loại ⟹ chọn mã Tracking, hoặc đánh dấu ngoài bảng giá.
        "chua-phan-loai": lambda line, state, flagged: state.needs_review,
        # 2. Ngoài bảng giá mà chưa có giá tay ⟹ gõ một con số.
        "ngoai-bang-thieu-gia": lambda line, state, flagged: (
            state.out_of_catalog and line.purchase_price is None),
        # 3. Đã khớp Tracking nhưng chưa có MIN cho ngày bán ⟹ vẫn gõ tay
        #    được, và đó là điểm khác biệt so với (1): ở đây KHÔNG cần phân
        #    loại thêm gì cả, chỉ là Tracking chưa trả được giá của ngày ấy.
        "thieu-min": lambda line, state, flagged: (
            state.classification == line_identity.CLASS_MATCHED_TRACKING
            and line.purchase_price is None),
        # 4. Mâu thuẫn ⟹ chọn LẠI. Không tự chọn bên thắng (`§4.2`).
        "xung-dot": lambda line, state, flagged: state.conflict,
        # --- R3 §2/§1 — hai hàng đợi ngoại lệ mới -----------------------
        # 5. Dòng thuộc loại chứng từ chưa ai định nghĩa (hoàn/hủy, hoặc một
        #    tiền tố Số BH chưa khai). Hành động: Owner quyết nghĩa của nó,
        #    hoặc loại dòng khỏi báo cáo. KHÔNG phải việc gõ một con số.
        "loai-chua-ro": lambda line, state, flagged: (
            line.line_type in line_type.UNDECIDED_TYPES),
        # 6. Dòng phụ đã được chính sách cho giá nhập 0 (`OD-105B-01` §3) —
        #    ở đây để Owner ĐỐI CHIẾU, không phải để sửa: một dòng phí bị
        #    nhận nhầm thành hàng bán (hoặc ngược lại) chỉ nhìn ra được khi
        #    chúng đứng cạnh nhau.
        "gia-theo-chinh-sach": lambda line, state, flagged: (
            line.purchase_provenance == business_metrics.PROVENANCE_POLICY_ZERO),
        # 7. `R3 §1` — dòng mà lần nạp lại KHÔNG ghép chắc chắn được vào khoá
        #    cũ, trong khi một quyết định của Owner đang treo ở đó. Hành động:
        #    kiểm tra rồi bấm ĐÃ XỬ LÝ — hệ thống KHÔNG tự chuyển quyết định
        #    sang khoá mới, vì đó chính là phép đoán nó vừa từ chối.
        "gan-dong": lambda line, state, flagged: flagged,
        # --- R4 §3/§5 — hai hàng đợi ĐỌC, đích đến của drill-down ---------
        # Chúng không mở thêm thao tác ghi nào: bảng kê vẫn là bảng kê, chỉ
        # thu hẹp về đúng tập dòng mà một con số trên trang đánh giá nói tới.
        # Không có chúng thì "đơn lỗ: 3 dòng" là một con số không mở ra được,
        # tức đúng thứ brief §5 cấm.
        #
        # 8. Dòng có lợi nhuận KPI ÂM. `is not None` là phần bắt buộc: một
        #    dòng CHƯA tính được lợi nhuận không phải một dòng lỗ, và gộp hai
        #    thứ đó lại sẽ báo lỗ cho những dòng chỉ đang thiếu giá nhập.
        "lo": lambda line, state, flagged: (
            line.kpi_profit is not None and line.kpi_profit < 0),
        # 9. Dòng có chiết khấu trên cột `discount`. Dòng "Chiết khấu" của sổ
        #    tay cũ (`line_type` = DISCOUNT) KHÔNG nằm ở đây — số tiền của nó
        #    nằm ở doanh thu âm của chính nó, không ở cột này.
        "co-chiet-khau": lambda line, state, flagged: (
            line.line_type != line_type.TYPE_DISCOUNT
            and line.discount is not None and line.discount > 0),
    }
    _DEFAULT_DETAIL_FILTER = "tat-ca"

    #: Nhãn của từng hàng đợi, đúng thứ tự hiện trên thanh lọc.
    _DETAIL_FILTER_LABELS = (
        ("tat-ca", "Tất cả dòng"),
        ("chua-phan-loai", "Chưa phân loại"),
        ("xung-dot", "Xung đột mã"),
        ("ngoai-bang-thieu-gia", "Ngoài bảng — thiếu giá"),
        ("thieu-min", "Đã khớp — thiếu MIN"),
        ("thieu-gia", "Thiếu giá (tất cả)"),
        ("chua-ro-nv", "Chưa rõ nhân viên"),
        ("gan-dong", "Ngoại lệ gắn dòng"),
        ("loai-chua-ro", "Loại dòng chưa rõ"),
        ("gia-theo-chinh-sach", "Giá theo chính sách"),
        ("owner-sua", "Dòng tôi đã sửa"),
        ("lo", "Dòng lỗ"),
        ("co-chiet-khau", "Có chiết khấu"),
    )

    def _narrow_details(details: list[dict]) -> tuple[list[dict], dict]:
        """Thu hẹp bảng kê về MỘT mặt hàng / nhóm hàng / nguồn đơn.

        Ba tham số ĐỌC (`mat-hang`, `nhom-hang`, `nguon`) là đích đến của
        drill-down từ trang đánh giá. Chúng dùng ĐÚNG những khoá mà bảng đóng
        góp đã gộp theo — `product_key`, nhóm hàng hiệu lực, `lead_source` —
        nên tổng của bảng kê mở ra luôn khớp con số vừa bấm vào.

        `nhom-hang`/`nguon` chấp nhận chuỗi RỖNG có nghĩa: đó là bucket "chưa
        phân nhóm"/"chưa phân loại nguồn". Một tham số vắng mặt và một tham số
        rỗng vì thế KHÁC nhau, và `request.args.get` phân biệt được hai thứ đó
        bằng `None`.

        Giá trị không khớp dòng nào cho ra một bảng RỖNG kèm nhãn phạm vi —
        không rơi về "tất cả": im lặng mở rộng phạm vi là cách chắc chắn nhất
        để Owner đọc một tổng khác với con số họ vừa bấm.
        """
        product_key = request.args.get("mat-hang")
        group_key = request.args.get("nhom-hang")
        lead_source = request.args.get("nguon")
        narrow = {"product_key": product_key or "", "product_label": "",
                  "product_group": group_key, "lead_source": lead_source,
                  "active": False}
        if product_key:
            narrow["active"] = True
            labels = sorted(
                d["product_raw"] for d in details
                if d["product_key"] == product_key and d["product_raw"])
            narrow["product_label"] = labels[0] if labels else product_key
            details = [d for d in details if d["product_key"] == product_key]
        if group_key is not None:
            narrow["active"] = True
            details = [
                d for d in details
                if (d.get("classified_product_group")
                    or d.get("pipeline_product_group") or "") == group_key]
        if lead_source is not None:
            narrow["active"] = True
            details = [d for d in details
                       if (d.get("lead_source") or "") == lead_source]
        return details, narrow

    @app.get("/kinh-doanh/gia-nhap")
    def business_purchase_price():
        """BẢNG KÊ CHI TIẾT — một dòng hàng một dòng bảng, sửa ngay tại chỗ.

        Trang này vừa là nơi hoàn thiện giá nhập (`R-P1`…`R-P4`) vừa là "trang
        tính" mà chỉ thị `ORDER DETAIL TABLE` mô tả: giá nhập và nhân viên sửa
        được ngay trên dòng, còn doanh thu · lợi nhuận KPI · DS quy đổi là ba
        ô SUY RA tự tính lại sau mỗi lần lưu. Không có bước "tính" riêng.

        Bộ lọc mặc định là TẤT CẢ DÒNG của kỳ/nhân viên đang xem (`S120`):
        một khung nhìn báo cáo không được âm thầm giấu bớt dòng. Ba chế độ thu
        hẹp — còn thiếu giá, chưa rõ nhân viên, dòng Owner đã sửa — nằm ngay
        trên bảng và Owner chọn tường minh.
        """
        view = _business_period()
        context = _employee_context(view)
        data = (view["data"].for_employee(context["employee"])
                if context["chosen"] else view["data"])
        # `DEC-PHB02-08` — `nhom` thu hẹp bảng kê về ĐÚNG MỘT sheet của không
        # gian làm việc. Nó tồn tại để đường dẫn "xem tất cả dòng của sheet
        # này" nói đúng sự thật với sheet NHÓM: `nhan-vien` chỉ khoanh được
        # một người, nên dùng nó cho Nội thành sẽ mở ra một danh sách rộng
        # hơn hoặc hẹp hơn cái mà đường dẫn hứa.
        sheet_key = request.args.get("nhom")
        if sheet_key and not context["chosen"]:
            sheet = reporting_sheets.find_sheet(
                view["service"].sheets(view["data"]), sheet_key)
            if sheet is not None:
                data = view["data"].for_sheet(sheet)
        # `tat-ca=1` là cách viết cũ còn nằm trong bookmark/redirect — giữ nó
        # tương đương chế độ "tất cả" thay vì âm thầm rơi về danh sách khác.
        mode = request.args.get("loc") or _DEFAULT_DETAIL_FILTER
        if mode not in _DETAIL_FILTERS:
            mode = _DEFAULT_DETAIL_FILTER
        keep = _DETAIL_FILTERS[mode]
        # ĐỌC MỘT LẦN cho cả trang, rồi dùng cho CẢ phép lọc lẫn phép dựng
        # dòng: lọc bằng một ảnh chụp và hiển thị bằng một ảnh chụp khác sẽ
        # cho ra một bảng mà số dòng không khớp với bộ lọc đang chọn.
        decisions = _identity_decisions()
        raised = data.binding_exceptions
        details = [
            d for d in data.details
            if keep(d["line"], line_identity.state_of(d, decisions=decisions),
                    (d["order_key"], d["product_key"],
                     d["occurrence_index"]) in raised)]
        # R4 §5 — ba lát cắt ĐỌC thêm, để mỗi hàng của báo cáo đánh giá mở ra
        # đúng tập dòng đã sinh ra con số của nó. Chúng THU HẸP tập đã lọc ở
        # trên chứ không thay nó: kỳ, sheet/nhân viên và chế độ lọc vẫn có
        # hiệu lực, nên một đường dẫn drill-down không bao giờ âm thầm mở
        # rộng phạm vi mà nó hứa.
        details, narrow = _narrow_details(details)
        return render_template(
            "kinh_doanh_gia_nhap.html", periods=view["periods"],
            selected_period=view["selected_period"],
            period_label=business_presentation.period_label(view["period"]),
            columns=business_presentation.DETAIL_COLUMNS,
            filters=_DETAIL_FILTER_LABELS,
            rows=business_presentation.detail_rows(
                details, decisions=decisions, binding_exceptions=raised),
            coverage=business_presentation.coverage_cell(data.totals.coverage),
            assignable=business_presentation.assignable_employee_options(
                view["service"].assignable_employees()),
            mode=mode, show_all=(mode == "tat-ca"),
            selected_sheet=sheet_key or "", narrow=narrow,
            message=request.args.get("da-luu") or None,
            error=request.args.get("loi") or None, **context)

    @app.post("/kinh-doanh/gia-nhap")
    def business_save_purchase_price():
        """Ghi MỘT giá nhập. Provenance do server quyết, không do form khai."""
        view = _business_period()
        service = view["service"]
        try:
            occurrence = int(request.form.get("occurrence_index") or "")
        except ValueError:
            abort(400)
        keys = {
            "order_key": request.form.get("order_key") or "",
            "product_key": request.form.get("product_key") or "",
            "occurrence_index": occurrence,
        }
        exists, auto_price = service.auto_price_of(data=view["data"], **keys)
        if not exists:
            abort(404)
        _guard_lines(service, service.detail_of(data=view["data"], **keys))
        redirect_args = {
            "ky": request.values.get("ky") or "tat-ca",
            "nhan-vien": request.form.get("nhan-vien") or None,
            "nhom": request.form.get("nhom") or None,
            "loc": request.form.get("loc") or None,
        }
        if request.form.get("hanh-dong") == "go":
            _guarded(service.store.clear_purchase_price, **keys)
            return redirect(url_for(
                "business_purchase_price",
                **{k: v for k, v in redirect_args.items() if v},
                **{"da-luu": "Đã gỡ giá nhập do Owner nhập. Dòng trở lại giá "
                             "tự động của hệ thống."}))
        try:
            price = business_store.parse_purchase_price(request.form.get("gia_nhap"))
        except business_store.InvalidPurchasePriceError as exc:
            return redirect(url_for(
                "business_purchase_price",
                **{k: v for k, v in redirect_args.items() if v}, loi=str(exc)))
        try:
            # R2 §4.4 — xem chú thích ở `business_save_line_purchase_price`.
            provenance = _guarded(
                service.store.set_purchase_price,
                price=price, auto_price=auto_price,
                entered_by=identity_gateway.actor_of(),
                reason=(request.form.get("ly_do") or None), **keys)
        except business_store.MissingPriceReasonError as exc:
            return redirect(url_for(
                "business_purchase_price",
                **{k: v for k, v in redirect_args.items() if v}, loi=str(exc)))
        return redirect(url_for(
            "business_purchase_price",
            **{k: v for k, v in redirect_args.items() if v},
            **{"da-luu": (
                "Đã ghi giá nhập Owner sửa (thay giá tự động)."
                if provenance == "MANUAL_OVERRIDE"
                else "Đã ghi giá nhập Owner nhập.")}))

    @app.post("/kinh-doanh/nhan-vien-dong")
    def business_save_employee():
        """`OD-5` — gán MỘT dòng hàng cho một nhân viên, hoặc gỡ việc gán đó.

        Ranh giới cố ý hẹp: đây KHÔNG phải một trình sửa đơn hàng. Nó ghi đúng
        một trường, trên đúng một dòng đã tồn tại trong kỳ đang xem, và tên
        nhân viên phải nằm trong master `config/employees.yaml` — gõ tự do một
        cái tên vào KPI là mở lại đúng lớp lỗi mà `HD-110-06` đã đóng.

        Bằng chứng gốc không bị đụng: `order_line_result_version` vẫn giữ
        nguyên tên mà sổ ghi, và bảng override lưu lại tên đó ở cột
        `source_employee_at_entry`.
        """
        view = _business_period()
        service = view["service"]
        try:
            occurrence = int(request.form.get("occurrence_index") or "")
        except ValueError:
            abort(400)
        keys = {
            "order_key": request.form.get("order_key") or "",
            "product_key": request.form.get("product_key") or "",
            "occurrence_index": occurrence,
        }
        detail = service.detail_of(data=view["data"], **keys)
        if detail is None:
            abort(404)
        redirect_args = {
            "ky": request.values.get("ky") or "tat-ca",
            "nhan-vien": request.form.get("nhan-vien") or None,
            "nhom": request.form.get("nhom") or None,
            "loc": request.form.get("loc") or None,
        }

        def _back(**extra):
            return redirect(url_for(
                "business_purchase_price",
                **{k: v for k, v in redirect_args.items() if v}, **extra))

        _guard_lines(service, detail)
        if request.form.get("hanh-dong") == "go":
            _guarded(service.store.clear_employee, **keys)
            return _back(**{"da-luu": (
                "Đã gỡ việc gán nhân viên. Dòng trở lại đúng tên mà sổ ghi.")})

        chosen = (request.form.get("nhan_vien_moi") or "").strip()
        groups = dict(service.assignable_employees())
        if chosen not in groups:
            # Không đoán hộ, và không im lặng: một tên lạ nghĩa là master chưa
            # có người đó, và đó là việc sửa master chứ không phải việc của
            # trang này.
            return _back(loi=(
                f"{chosen!r} không có trong danh sách nhân viên. Hãy chọn một "
                "tên trong danh sách."))
        _guarded(service.store.set_employee,
                 employee=chosen, employee_group=groups[chosen],
                 source_employee=detail["line"].source_employee, **keys)
        return _back(**{"da-luu": (
            f"Đã gán dòng này cho {chosen}. Lợi nhuận của dòng đã chuyển sang "
            f"bảng của {chosen}; tổng của cả kỳ không đổi.")})

    # ------------------------------------------------------------------
    # R3 §4 — XUẤT EXCEL, và R3 §5 — CHỐT KỲ.
    #
    # Cả hai đọc ĐÚNG `PeriodData` mà các trang khác đang hiển thị. Không có
    # đường nào từ đây tới `ImportResult` hay tới `excel_exporter`: file xuất
    # từ kết quả pipeline là ảnh chụp trạng thái TRƯỚC mọi quyết định của
    # Owner — nó trông đầy đủ, nó cân, và nó nói một bộ số khác màn hình.
    # ------------------------------------------------------------------

    @app.post("/kinh-doanh/ngoai-le-gan-dong")
    def business_resolve_binding_exception():
        """`R3 §1` — đánh dấu MỘT ngoại lệ gắn dòng là ĐÃ XỬ LÝ.

        Nó KHÔNG sửa một khoá nào và KHÔNG di chuyển một quyết định nào. Nó chỉ
        ghi rằng người đã nhìn và đã quyết — bằng chính các thao tác sẵn có
        (gõ lại giá nhập cho khoá mới, loại dòng cũ khỏi báo cáo, hoặc không
        làm gì vì dòng cũ đúng là đã biến mất khỏi sổ).

        Tự động "chuyển quyết định sang khoá mới" chính là phép đoán mà cả cơ
        chế này sinh ra để từ chối — nên nó không có ở đây, và sẽ không có.
        """
        view = _business_period()
        try:
            exception_id = int(request.form.get("ngoai_le_id") or "")
        except ValueError:
            abort(400)
        if exception_id not in {
                item.id for item in view["data"].binding_exceptions.values()}:
            # Chỉ đóng được ngoại lệ CÒN MỞ và thuộc đúng kỳ đang xem — một id
            # gõ tay không được đóng một việc ở kỳ khác.
            abort(404)
        _guarded(view["service"].binding_store.resolve,
                 exception_id=exception_id,
                 resolved_by=identity_gateway.actor_of(),
                 note=(request.form.get("ghi_chu") or None))
        return redirect(url_for(
            "business_purchase_price", ky=view["selected_period"],
            loc=request.form.get("loc") or "gan-dong",
            **{"da-luu": ("Đã đánh dấu ngoại lệ gắn dòng là đã xử lý. Không "
                          "khoá nào bị đổi và không quyết định nào bị di "
                          "chuyển — bản ghi chỉ nói rằng bạn đã xem xong.")}))

    @app.get("/kinh-doanh/xuat-excel")
    def business_export_excel():
        """Tải file Excel của kỳ đang xem (tuỳ chọn: một nhân viên/một sheet).

        Ba tham số, đúng ba lát cắt mà màn hình có: `ky` (kỳ), `nhan-vien`
        (một người), `nhom` (một sheet báo cáo). Không tham số nào tạo ra một
        phép gộp mới — chúng chỉ chọn lát nào của cùng một `PeriodData`.
        """
        view = _business_period()
        service = view["service"]
        context = _employee_context(view)
        data = view["data"]
        scope = "toan-ky"
        if context["chosen"]:
            data = data.for_employee(context["employee"])
            scope = context["employee"] or "chua-xac-dinh"
        else:
            sheet_key = request.args.get("nhom")
            if sheet_key:
                sheet = reporting_sheets.find_sheet(
                    service.sheets(view["data"]), sheet_key)
                if sheet is None:
                    abort(404)
                data = view["data"].for_sheet(sheet)
                scope = sheet.key
        label = business_presentation.period_label(view["period"])
        try:
            workbook = service.export_workbook(data=data, period_label=label)
        except business_export.ExportIntegrityError as exc:
            # File lệch KHÔNG được ghi ra: nó sẽ được gửi đi và được tin.
            abort(409, description=str(exc))
        stream = io.BytesIO()
        workbook.save(stream)
        stream.seek(0)
        return send_file(
            stream, mimetype=XLSX_MIMETYPE, as_attachment=True,
            download_name=_export_file_name(view["selected_period"], scope))

    @app.get("/kinh-doanh/chot-ky")
    def business_period_close():
        """Trang CHỐT KỲ — bộ số sắp được duyệt, và lịch sử các lần chốt."""
        view = _business_period()
        service, period = view["service"], view["period"]
        data = view["data"]
        history = ([] if period is None
                   else _guarded(service.period_store.history,
                                 year=period[0], month=period[1]))
        return render_template(
            "kinh_doanh_chot_ky.html", periods=view["periods"],
            selected_period=view["selected_period"],
            period_label=business_presentation.period_label(period),
            has_period=period is not None,
            summary=business_presentation.close_summary(data.totals),
            closed=data.closed,
            drift=_guarded(service.period_drift, period=period, data=data),
            history=history,
            open_exceptions=len(data.binding_exceptions),
            discount_double_count=list(data.discount_double_count),
            message=request.args.get("da-luu") or None,
            error=request.args.get("loi") or None)

    @app.post("/kinh-doanh/chot-ky")
    def business_close_period():
        """Chốt kỳ, hoặc mở lại một kỳ đã chốt (kèm LÝ DO bắt buộc)."""
        view = _business_period()
        service, period = view["service"], view["period"]
        if period is None:
            # "Toàn bộ dữ liệu" không phải một kỳ. Chốt một khoảng không có
            # tháng nghĩa là chốt một thứ không ai đặt tên được.
            abort(404)

        def _back(**extra):
            return redirect(url_for(
                "business_period_close", ky=view["selected_period"], **extra))

        if request.form.get("hanh-dong") == "mo-lai":
            try:
                _guarded(service.reopen_period, period=period,
                         reason=request.form.get("ly_do") or "",
                         reopened_by=identity_gateway.actor_of())
            except (period_lock.MissingReopenReasonError,
                    period_lock.PeriodNotClosedError) as exc:
                return _back(loi=str(exc))
            return _back(**{"da-luu": (
                f"Đã mở lại kỳ {business_presentation.period_label(period)}. "
                "Các thao tác sửa số của kỳ này đã mở lại.")})
        try:
            closed = _guarded(
                service.close_period, period=period, data=view["data"],
                closed_by=identity_gateway.actor_of(),
                note=request.form.get("ghi_chu") or None)
        except period_lock.InvalidPeriodError as exc:
            return _back(loi=str(exc))
        return _back(**{"da-luu": (
            f"Đã chốt kỳ {business_presentation.period_label(period)} "
            f"(lần {closed.version_no}). Mọi thay đổi số của kỳ này từ giờ "
            "phải MỞ LẠI kỳ trước, và lần mở lại đó được ghi kèm lý do.")})

    @app.get("/kinh-doanh/gia-dung")
    def business_gia_dung():
        """Tick Gia dụng — CHỈ nhóm Nội thành (`DEC-PHB02-05`).

        Nhân viên bán lẻ thường không được thấy luồng này: chỉ thị PHB-03 §2E
        nói rõ "Do not expose the Gia dụng workflow to ordinary retail
        employees". Chọn sai nhân viên ⟹ 404, không phải một trang tick không
        có tác dụng gì.
        """
        view = _business_period()
        context = _employee_context(view)
        if not context["chosen"]:
            abort(404)
        if not gia_dung_workflow_applies(context["employee_group"]):
            abort(404)
        data = view["data"].for_employee(context["employee"])
        return render_template(
            "kinh_doanh_gia_dung.html", periods=view["periods"],
            selected_period=view["selected_period"],
            period_label=business_presentation.period_label(view["period"]),
            columns=business_presentation.GIA_DUNG_COLUMNS,
            rows=business_presentation.gia_dung_rows(
                view["service"].products(data)),
            message=request.args.get("da-luu") or None, **context)

    @app.post("/kinh-doanh/gia-dung")
    def business_save_gia_dung():
        """Ghi/gỡ phân loại Gia dụng của MỘT mặt hàng.

        Quyền tick được kiểm lại ở đây, không chỉ ở trang GET: một POST dựng
        tay vẫn phải đi qua đúng ranh giới `DEC-PHB02-05`.
        """
        view = _business_period()
        context = _employee_context(view)
        if not context["chosen"] or not gia_dung_workflow_applies(
                context["employee_group"]):
            abort(404)
        product_key = request.form.get("product_key") or ""
        products = {item["product_key"]: item for item in view["service"].products(
            view["data"].for_employee(context["employee"]))}
        product = products.get(product_key)
        if product is None:
            abort(404)
        # Quyết định cấp MẶT HÀNG chạm mọi kỳ có dòng của mã đó, nên cửa chặn
        # phải hỏi mọi kỳ ấy — không chỉ kỳ đang xem.
        _guarded(view["service"].guard_product_open, product_key)
        if request.form.get("gia_dung") == "1":
            _guarded(view["service"].store.set_product_group,
                     product_key=product_key, product_group="GIA_DUNG",
                     product_label=product["product_label"])
            saved = "Đã đánh dấu mặt hàng này là Gia dụng (tỉ lệ quy đổi 8%)."
        else:
            _guarded(view["service"].store.clear_product_group,
                     product_key=product_key)
            saved = "Đã bỏ đánh dấu Gia dụng. Mặt hàng trở lại tỉ lệ mặc định."
        return redirect(url_for(
            "business_gia_dung", ky=request.values.get("ky") or "tat-ca",
            **{"nhan-vien": context["selected_employee"], "da-luu": saved}))

    # ------------------------------------------------------------------
    # R6 — DASHBOARD PHÂN TÍCH KINH DOANH.
    #
    # Năm khung nhìn con nữa của Báo cáo, mở từ trang `/kinh-doanh` — KHÔNG
    # một tab chính mới (`DEC-185` giữ thanh điều hướng đúng BA mục, và R6
    # không xin mở lại quyết định đó).
    #
    # Bốn ranh giới được giữ bằng CẤU TẠO ở mọi route dưới đây:
    #
    # 1. **Một nguồn.** Mọi trang đọc `service.period(...)` — đúng lời gọi mà
    #    Báo cáo, Nhân viên, bảng thương hiệu và biểu đồ doanh thu đã dùng.
    #    Dòng Owner đã loại và dòng tạm loại KHÔNG có mặt trong `data.lines`,
    #    nên chúng không thể lọt vào một tổng, một mốc, một bucket hay một giỏ
    #    hàng nào của R6.
    # 2. **Một phạm vi.** `analysis_range.resolve` trả về ĐÚNG một phạm vi cho
    #    cả trang; mọi khối trên trang dùng chung `view["range"]`.
    # 3. **Một engine thời gian.** Biểu đồ số đơn dựng `Point`/`PairedSeries`
    #    bằng chính `revenue_timeline` của R5 — không hàm chia mốc thứ hai.
    # 4. **Một thẩm quyền metadata.** Hãng/nhóm hàng/nhãn model chỉ đi qua
    #    `product_taxonomy`, vốn chỉ đọc `line_identity` + log quyết định đã
    #    CONFIRMED + bản chiếu danh mục Tracking.
    #
    # VỊ TRÍ của khối này trong file KHÔNG tuỳ ý. Khối mở đầu bằng các HÀM
    # PHỤ chưa decorate, và `tests/test_phb07_advanced_analytics.py::
    # route_source` cắt mã của một route bằng cách đọc tới `@app.` KẾ TIẾP —
    # nên đặt khối này ngay sau `business_composition` sẽ làm mã của R6 bị
    # đọc thành mã của route PHB-07 và làm đỏ một bài kiểm ranh giới của
    # vertical khác. `tests/test_r6_dashboard_vertical.py::
    # test_the_r6_block_never_sits_between_a_route_and_its_next_decorator`
    # canh ràng buộc này để một lần dời khối về sau không âm thầm phá nó.
    # ------------------------------------------------------------------

    def _analysis_range() -> analysis_range.AnalysisRange:
        """Phạm vi HIỆU LỰC của một trang phân tích — đọc MỘT LẦN cho cả trang.

        `fallback_period` là tháng dương lịch hiện tại, cùng quyết định mà
        `_workspace_period` đã ghi (`§2`, `§3`): một trang phân tích mở ra
        trước lần nạp sổ đầu tiên của tháng vẫn phải mở đúng tháng ấy chứ
        không rơi ngược về tháng trước.
        """
        return analysis_range.resolve(
            period_raw=request.values.get("ky"),
            from_raw=request.values.get("tu-ngay"),
            to_raw=request.values.get("den-ngay"),
            fallback_period=(_today().year, _today().month))

    def _analysis_view() -> dict:
        """Mọi thứ một trang phân tích cần, đọc ĐÚNG MỘT LẦN.

        `metadata` là dãy song song với `data.details` (`product_taxonomy.
        metadata_for`). Nó được giải ở đây — một lần cho cả trang — chứ không
        ở từng bảng: ba chiều gộp, bảng giỏ hàng và bảng kê drill-down đều đọc
        lại đúng dãy này, nên không có đường nào để hai khối cùng trang xếp
        một dòng vào hai mặt hàng khác nhau.
        """
        service = _require_business()
        scope = _analysis_range()
        data = _guarded(service.period, date_from=scope.date_from,
                        date_to=scope.date_to, period=scope.period)
        metadata = product_taxonomy.metadata_for(
            data.details, decisions=_identity_decisions(),
            identities=identity_gateway.confirmed_identities(identity_store),
            display=_tracking_display())
        return {
            "service": service, "range": scope, "data": data,
            "metadata": metadata,
            # Repair `FIND-R6-IR-01` — NEO của cả hai biểu đồ, nói ra TƯỜNG
            # MINH ở đây thay vì để mỗi biểu đồ tự gọi `anchor_date()`.
            #
            # `anchor_date(period, details)` rơi về "ngày bán MUỘN NHẤT thực sự
            # có" khi `period is None`, và với R6 thì `period is None` nghĩa là
            # phạm vi TỰ CHỌN — nên cửa sổ sẽ trôi theo dữ liệu: cùng một
            # khoảng ngày người dùng gõ cho ra hai cửa sổ khác nhau ở hai lần
            # nạp sổ khác nhau. `scope.date_to` là câu trả lời đúng cho CẢ HAI
            # phạm vi: với `PERIOD` nó đúng bằng ngày cuối tháng — tức đúng
            # giá trị `anchor_date()` trả về — còn với `CUSTOM` nó là chính
            # `Đến ngày` người dùng gõ.
            # `DEC-211` — mép phải của hai biểu đồ. Một KỲ (`ky=2026-09`)
            # là lối viết tắt cho "tháng ấy", nên mép phải của nó là chỗ sổ
            # thật sự dừng lại: neo vào 30/09 khi sổ mới ghi tới 25/09 vẽ ra
            # năm ngày trắng ở mép phải, đúng thứ Owner gọi là biểu đồ bị cụt.
            # Một PHẠM VI TỰ GÕ thì ngược lại: hai cận ngày là chỉ thị tường
            # minh của người dùng, và để dữ liệu kéo mép phải đi sẽ làm cùng
            # một khoảng ngày cho ra hai cửa sổ khác nhau ở hai lần nạp sổ.
            #
            # Cùng quy tắc này giữ trang Báo cáo và trang phân tích nói CÙNG
            # một con số cho cùng một mốc khi cả hai đang xem cùng một kỳ —
            # bất biến mà `test_r5_and_r6_agree_on_every_comparison_bucket`
            # canh.
            "anchor": (revenue_timeline.anchor_date(scope.period, data.details)
                       if scope.period is not None else scope.date_to),
            "totals": dashboard_metrics.totals(data.details),
            "periods": workspace_presentation.period_options(
                _guarded(analytics_queries.available_periods,
                         snapshot_repo.engine),
                selected=scope.period or (_today().year, _today().month),
                today=_today()),
        }

    def _analysis_scope_block(view: dict) -> dict:
        """Mô hình hiển thị của bộ chọn phạm vi, dùng chung mọi trang R6."""
        scope = view["range"]
        return {
            "label": scope.label,
            "kind": scope.kind,
            "is_custom": scope.is_custom,
            "days": scope.days,
            "period_value": scope.period_value,
            "date_from": scope.date_from.isoformat(),
            "date_to": scope.date_to.isoformat(),
            "note": scope.note,
            "scope_note": analysis_range.SCOPE_NOTE,
        }

    def _chart_details(view: dict, granularity: str) -> tuple[list, bool]:
        """Lát dữ liệu hiệu lực PHỦ ĐỦ hai cửa sổ của biểu đồ, và cờ "đã mở rộng".

        Repair `FIND-R6-IR-01`. Đây là chỗ DUY NHẤT của R6 đọc thêm dữ liệu
        ngoài phạm vi đang xem, và nó đọc đúng bằng khoảng mà
        `revenue_timeline.paired_window_span` nói là cần — không phải toàn bộ
        dòng thời gian như trang Báo cáo `R5` đang làm.

        Ba ràng buộc được giữ bằng CẤU TẠO:

        1. **Chỉ biểu đồ.** Hàm này trả về một danh sách `details` và không
           chạm `view`. Ô chỉ tiêu, bảng gộp, giỏ hàng và bảng kê vẫn đọc
           `view["data"]` của phạm vi đang xem, nên chúng không thể lặng lẽ
           nói về một khoảng thời gian khác cái người dùng vừa chọn.
        2. **Vẫn là effective data.** Nó gọi ĐÚNG `service.period(...)` — cùng
           lời gọi mà mọi trang nghiệp vụ dùng — nên dòng Owner đã loại và
           dòng R5 tạm loại vẫn không có mặt, và giá nhập/nhân viên vẫn là
           giá trị đã hợp nhất. Không đường nào ở đây đọc Excel, `ImportResult`
           hay một giá "hiện tại" nào.
        3. **KHÔNG mượn chốt kỳ.** `period=` cố ý KHÔNG được truyền: khoảng
           hai cửa sổ hầu như không bao giờ là một tháng dương lịch, và mượn
           trạng thái chốt của tháng chứa nó sẽ gán một `ClosedPeriod` cho một
           khoảng chưa ai chốt. Biểu đồ không đọc `closed`, nên `None` ở đây
           không mất thông tin nào.

        Khi phạm vi đang xem ĐÃ phủ đủ khoảng cần thiết, hàm trả về chính lát
        đã đọc — không có câu truy vấn thứ hai nào chạy.
        """
        span = revenue_timeline.paired_window_span(granularity, view["anchor"])
        if span is None:
            # Mức NĂM: không có cửa sổ so sánh, nên không có gì phải phủ thêm.
            return view["data"].details, False
        low, high = span
        scope = view["range"]
        if low >= scope.date_from and high <= scope.date_to:
            return view["data"].details, False
        return _guarded(view["service"].period,
                        date_from=low, date_to=high).details, True

    def _orders_chart(view: dict) -> Optional[dict]:
        """Biểu đồ SỐ ĐƠN, hai cửa sổ liền kề — cùng engine với doanh thu.

        Nó dựng `revenue_timeline.Point` mà trường `revenue` mang SỐ ĐƠN, rồi
        gọi đúng `paired_series()` của R5. Không một dòng nào của
        `revenue_timeline` bị sửa cho việc này, và vì thế hai biểu đồ trên
        trang luôn cắt cùng những mốc thời gian.

        `None` ở mức gộp Năm — R5 cố ý không có cửa sổ so sánh ở mức đó, và R6
        không mở một quy ước riêng để lấp chỗ ấy.
        """
        granularity = revenue_timeline.parse_granularity(
            request.args.get("muc"), default=revenue_timeline.DAY)
        details, _widened = _chart_details(view, granularity)
        # `R7 §D` — cùng nguồn lấp lỗ hổng số đơn với trang Báo cáo, để hai
        # trang vẽ cùng một đường "Cùng kỳ năm trước" (`FIND-R6-IR-01`).
        points = revenue_timeline.count_series(
            details, granularity=granularity,
            gapfill_days=chart_gapfill.daily_order_rows())
        paired = revenue_timeline.paired_series(
            points, granularity=granularity, anchor=view["anchor"],
            confirmed_ranges=_guarded(snapshot_repo.confirmed_ranges)
            if snapshot_repo is not None else ())
        if paired is None:
            return None
        return business_presentation.paired_count_chart(
            paired, granularity=granularity,
            undated_orders=view["totals"].orders_without_date)

    def _revenue_chart_for_scope(view: dict) -> Optional[dict]:
        """Biểu đồ DOANH THU của phạm vi đang xem, hai cửa sổ liền kề.

        Đi qua đúng `revenue_timeline.series()` mà trang Báo cáo dùng, trên
        đúng `data.details` của phạm vi này. Nguồn lịch sử (`legacy_months`/
        `legacy_days`) KHÔNG được nối vào đây có chủ ý: trang phân tích trả
        lời câu hỏi về SỔ ĐANG NẠP trong một phạm vi người dùng vừa chọn, và
        trộn thêm các tháng chỉ có bản ghi lịch sử vào cửa sổ đó sẽ đặt hai
        loại bằng chứng cạnh nhau trong cùng một phép so sánh mà không ô nào
        trên trang nói ra. Dòng thời gian có lịch sử vẫn ở nguyên trang Báo
        cáo, không bị xoá.

        ## Vì sao nguồn LẤP LỖ HỔNG lại được nối, trong khi lịch sử thì không

        `DEC-216`, và đây là chỗ hai luật gặp nhau nên nó được nói ra hết.
        `FIND-R6-IR-01` để lại một bất biến đã nghiệm thu: hai trang cùng sản
        phẩm, cùng sổ, cùng kỳ, CÙNG MỨC GỘP không được cho hai con số ở cửa
        sổ so sánh. Ở mức Ngày/Tuần bất biến ấy đo được đúng nghĩa, vì bản ghi
        lịch sử KHÔNG có điểm nào ở đó — nó chỉ lưu tổng tháng. Nói cách khác,
        đoạn văn trên loại một thứ vốn đã vắng mặt ở mức này.

        Nguồn lấp lỗ hổng thì CÓ điểm ở mức Ngày/Tuần. Nối nó vào trang Báo
        cáo mà không nối vào đây sẽ làm hai trang vẽ hai đường "Cùng kỳ năm
        trước" khác nhau cho cùng một câu hỏi — đúng thứ bất biến kia cấm, và
        người đọc không có cách nào biết trang nào đang nói thật.

        Ở mức Tháng trở lên nó không được truyền (`gapfill_days` chỉ nối ở
        nhánh Ngày/Tuần), nên khác biệt lịch sử giữa hai trang ở các mức thô
        vẫn nguyên như trước, không rộng thêm một chút nào.
        """
        granularity = revenue_timeline.parse_granularity(
            request.args.get("muc"), default=revenue_timeline.DAY)
        details, _widened = _chart_details(view, granularity)
        gapfill_days = (
            chart_gapfill.daily_rows()
            if granularity in (revenue_timeline.DAY, revenue_timeline.WEEK)
            else ())
        points = revenue_timeline.series(details, granularity=granularity,
                                         gapfill_days=gapfill_days)
        paired = revenue_timeline.paired_series(
            points, granularity=granularity, anchor=view["anchor"],
            confirmed_ranges=_guarded(snapshot_repo.confirmed_ranges)
            if snapshot_repo is not None else ())
        if paired is None:
            return None
        # `undated` vẫn đếm trên lát của PHẠM VI ĐANG XEM: nó là một tín hiệu
        # chất lượng dữ liệu về cái người dùng đang xem, không về hai cửa sổ.
        return business_presentation.paired_revenue_chart(
            paired, granularity=granularity,
            undated=revenue_timeline.undated_count(view["data"].details))

    # ==================================================================
    # `UI-05` — PHÂN RÃ một mốc của biểu đồ, khi người dùng GHIM nó.
    #
    # Route GET, chỉ đọc. `R6` tự đặt cho mình luật "không API ngoài, không
    # route GHI" (`docs/tasks/R6-dashboard-phan-tich-kinh-doanh.md`) — một
    # route ĐỌC nội bộ không chạm luật đó, nhưng nó chạm một luật khác và
    # luật ấy được giữ bằng cấu tạo: KHÔNG một phép tính nào ở đây.
    #
    # `dashboard_metrics.totals()` cộng; `dashboard_presentation.money_cell()`
    # định dạng; `revenue_timeline.bucket_of()` chia mốc. Cả ba là ĐÚNG những
    # hàm mà trang phân tích gọi cho chính con số đang hiện trên biểu đồ, nên
    # phần phân rã không thể cộng ra một tổng khác với cái chấm mà người dùng
    # vừa bấm vào. Nếu ai đó viết một phép cộng ở đây, đó là lúc hai con số
    # bắt đầu trôi khỏi nhau.
    # ==================================================================

    #: Số nhân viên hiện trong một lần phân rã. Đây là một TOOLTIP, không
    #: phải một bảng: quá năm dòng thì nó che mất chính biểu đồ đang giải
    #: thích. Phần còn lại được gộp thành một dòng "còn lại", không bị giấu.
    BREAKDOWN_ROWS = 5

    @app.get("/api/v1/analytics/chart-breakdown")
    def api_chart_breakdown():
        """`UI-05` — ai đóng góp vào MỘT mốc của biểu đồ.

        Phạm vi (kỳ/khoảng ngày) đọc từ CHÍNH những tham số mà trang phân
        tích đang mang trên URL, qua `_analysis_view()` — không có phép phân
        tích phạm vi thứ hai ở đây, nên một mốc được phân rã trong đúng phạm
        vi mà người dùng đang nhìn.

        `muc` là mức gộp, `moc` là khoá mốc — cùng hai giá trị mà chính điểm
        dữ liệu mang trong `data-gran`/`data-key`, do server dựng ở
        `_r6_bits.html`. Client không tự dựng khoá mốc nào.
        """
        granularity = revenue_timeline.parse_granularity(
            request.args.get("muc"), default=revenue_timeline.DAY)
        key = (request.args.get("moc") or "").strip()
        if not key:
            return _api_error(
                mutation_guard.VALIDATION_ERROR,
                "Thiếu `moc` — khoá mốc của điểm dữ liệu.", status=400,
                field="moc")
        view = _analysis_view()
        # ĐÚNG lát mà biểu đồ vẽ, kể cả cửa sổ so sánh của năm trước: một
        # điểm `chart-bar-prev` nằm ngoài phạm vi đang xem, và đọc
        # `view["data"]` sẽ trả về một phân rã RỖNG cho một cái chấm đang
        # hiện một con số khác 0.
        details, _widened = _chart_details(view, granularity)
        bucket = [detail for detail in details
                  if detail.get("sale_date") is not None
                  and revenue_timeline.bucket_of(
                      detail["sale_date"], granularity)[0] == key]

        by_employee: dict = {}
        for detail in bucket:
            by_employee.setdefault(detail["line"].employee, []).append(detail)

        rows = []
        for name, slice_details in by_employee.items():
            slice_totals = dashboard_metrics.totals(slice_details)
            rows.append({
                "employee": name or business_presentation.UNKNOWN_EMPLOYEE,
                "resolved": name is not None,
                "revenue": dashboard_presentation.money_cell(
                    slice_totals.sales_revenue),
                "orders": slice_totals.orders,
                "lines": slice_totals.lines,
                # Khoá SẮP XẾP giữ nguyên `Decimal`, không đọc ngược từ chuỗi
                # đã định dạng — cùng lý do `analytics_employee` nêu: `"1.234"`
                # là hai con số khác nhau ở hai cách viết.
                "_sort": (slice_totals.sales_revenue
                          if slice_totals.sales_revenue is not None
                          else Decimal(0)),
            })
        rows.sort(key=lambda row: (-row["_sort"], row["employee"]))
        shown = rows[:BREAKDOWN_ROWS]
        for row in shown:
            row.pop("_sort")
        totals = dashboard_metrics.totals(bucket)
        return {
            "schema_version": workspace_presentation.WORKSPACE_SCHEMA_VERSION,
            "granularity": granularity,
            "key": key,
            "label": (revenue_timeline.bucket_of(
                bucket[0]["sale_date"], granularity)[1] if bucket else key),
            "revenue": dashboard_presentation.money_cell(totals.sales_revenue),
            "orders": totals.orders,
            "lines": totals.lines,
            "rows": shown,
            # Số nhân viên KHÔNG hiện, nói ra chứ không giấu: một tooltip cắt
            # bớt mà không nói là một tooltip khiến người đọc cộng thiếu.
            "hidden_employees": max(0, len(rows) - len(shown)),
            "trace_id": request_timing.trace_id(),
        }

    @app.get("/kinh-doanh/phan-tich")
    def analytics_overview():
        """R6 §2 — Tổng quan: chỉ tiêu nền, hai biểu đồ, bốn ô giỏ hàng.

        Phép đối soát giữa `dashboard_metrics` và `business_metrics` CHẠY THẬT
        ở mỗi lần tải trang và kết quả lên màn hình: hai module tính số dòng,
        số đơn và doanh thu bằng hai đường độc lập, nên chúng gặp nhau ở cùng
        con số là bằng chứng R6 không dựng một định nghĩa doanh thu thứ hai.
        """
        view = _analysis_view()
        data = view["data"]
        index = _basket_index(view)
        return render_template(
            "kinh_doanh_phan_tich.html",
            periods=view["periods"],
            scope=_analysis_scope_block(view),
            cards=dashboard_presentation.totals_cards(view["totals"]),
            quality=dashboard_presentation.data_quality(view["totals"]),
            basket_cards=dashboard_presentation.basket_cards(
                basket_metrics.counts(index)),
            revenue_chart=_revenue_chart_for_scope(view),
            orders_chart=_orders_chart(view),
            reconciliation=dashboard_metrics.reconciliation(
                view["totals"], data.totals),
            empty=data.totals.lines == 0)

    def _basket_index(view: dict) -> dict:
        """Index giỏ hàng của phạm vi đang xem, dựng từ đúng lát dữ liệu."""
        details = view["data"].details
        metadata = view["metadata"]
        return basket_metrics.build_index(
            details,
            product_buckets=product_taxonomy.buckets_for(
                details, metadata,
                dimension=product_taxonomy.DIMENSION_PRODUCT),
            category_buckets=product_taxonomy.buckets_for(
                details, metadata,
                dimension=product_taxonomy.DIMENSION_CATEGORY))

    def _group_block(view: dict, *, dimension: str, data=None,
                     metadata=None) -> dict:
        """Bảng gộp theo MỘT chiều, trên MỘT lát dữ liệu.

        `data`/`metadata` mặc định là lát của cả phạm vi; trang Nhân viên
        truyền vào lát `for_employee` của chính nó. Cùng một hàm cho cả hai là
        điều kiện để bảng của một nhân viên và bảng của cả công ty không bao
        giờ dùng hai phép gộp khác nhau (`R6 §4`).
        """
        data = view["data"] if data is None else data
        metadata = view["metadata"] if metadata is None else metadata
        buckets = product_taxonomy.buckets_for(
            data.details, metadata, dimension=dimension)
        rows = product_metrics.group_rows(data.lines, data.details, buckets)
        company = dashboard_metrics.totals(data.details)
        reconciled = product_metrics.reconciliation(rows, company)
        return {
            "rows": dashboard_presentation.group_rows(rows, company),
            "summary": dashboard_presentation.group_summary(
                reconciled, product_taxonomy.coverage(metadata),
                dimension=dimension, scope_label=view["range"].label,
                totals=company),
        }

    @app.get("/kinh-doanh/phan-tich/co-cau")
    def analytics_structure():
        """R6 §3 — Mặt hàng · Nhóm hàng · Hãng, MỘT engine gộp, ba chiều.

        Ba chiều nằm trên MỘT trang với một nút chuyển, không phải ba trang:
        ba trang gần giống nhau là ba chỗ để một cột được sửa ở hai chỗ và
        quên ở chỗ thứ ba.
        """
        view = _analysis_view()
        dimension = product_taxonomy.parse_dimension(request.args.get("chieu"))
        block = _group_block(view, dimension=dimension)
        return render_template(
            "kinh_doanh_phan_tich_co_cau.html",
            periods=view["periods"],
            scope=_analysis_scope_block(view),
            columns=dashboard_presentation.GROUP_COLUMNS,
            dimensions=[
                {"key": key, "label": label, "on": key == dimension}
                for key, label in product_taxonomy.DIMENSIONS
            ],
            rows=block["rows"], summary=block["summary"])

    @app.get("/kinh-doanh/phan-tich/nhan-vien")
    def analytics_employee():
        """R6 §4 — Nhân viên: cùng aggregate, trên lát `for_employee`.

        KHÔNG có employee score, KHÔNG có xếp hạng quản trị, KHÔNG có một KPI
        nào được suy ra ở đây. Trang chỉ đặt cạnh nhau những con số mà
        `dashboard_metrics` đã tính cho từng lát — và cơ cấu theo mặt
        hàng/hãng/nhóm hàng của một nhân viên đi qua ĐÚNG `_group_block` mà
        trang cơ cấu dùng.
        """
        view = _analysis_view()
        data = view["data"]
        company = view["totals"]
        # Thứ tự tên CỐ ĐỊNH (doanh thu giảm dần, rồi tên) để hai lần tải
        # trang không đổi thứ tự hàng khi số không đổi.
        names = sorted({line.employee for line in data.lines},
                       key=lambda value: (value is None, value or ""))
        rows = []
        for name in names:
            slice_data = data.for_employee(name)
            slice_totals = dashboard_metrics.totals(slice_data.details)
            rows.append({
                "employee": name or business_service.bm_unknown_employee_label(),
                "key": name or "",
                "resolved": name is not None,
                "revenue": dashboard_presentation.money_cell(
                    slice_totals.sales_revenue),
                "share": {
                    "text": business_presentation.percent(
                        product_metrics.share_percent(
                            slice_totals.sales_revenue, company.sales_revenue)),
                    "missing": product_metrics.share_percent(
                        slice_totals.sales_revenue,
                        company.sales_revenue) is None},
                "quantity": legacy_presentation.format_number(
                    slice_totals.total_quantity),
                "discount": dashboard_presentation.money_cell(
                    slice_totals.discount_total),
                "orders": slice_totals.orders,
                "lines": slice_totals.lines,
                "lines_per_order": (
                    "—" if slice_totals.lines_per_order is None
                    else legacy_presentation.format_number(
                        slice_totals.lines_per_order)),
                # Khoá SẮP XẾP giữ nguyên `Decimal`, không đọc ngược từ chuỗi
                # đã định dạng: `"1.234"` là một nghìn hai trăm ba tư ở cách
                # viết của trang này và là một phẩy hai ba tư ở cách viết
                # khác, và một bảng sắp sai thứ tự vì chuyện đó thì không ai
                # nhìn ra bằng mắt.
                "_revenue_sort": (slice_totals.sales_revenue
                                  if slice_totals.sales_revenue is not None
                                  else Decimal(0)),
            })
        rows.sort(key=lambda row: (row["resolved"] is False,
                                   -row["_revenue_sort"], row["employee"]))
        selected = request.args.get("nhan-vien")
        block = None
        if selected is not None:
            chosen = selected or None
            keep = [index for index, line in enumerate(data.lines)
                    if line.employee == chosen]
            slice_data = data.for_employee(chosen)
            slice_metadata = [view["metadata"][index] for index in keep]
            dimension = product_taxonomy.parse_dimension(
                request.args.get("chieu"))
            block = _group_block(view, dimension=dimension, data=slice_data,
                                 metadata=slice_metadata)
            block["dimension"] = dimension
            block["employee"] = (
                chosen or business_service.bm_unknown_employee_label())
        return render_template(
            "kinh_doanh_phan_tich_nhan_vien.html",
            periods=view["periods"],
            scope=_analysis_scope_block(view),
            columns=dashboard_presentation.GROUP_COLUMNS,
            dimensions=[
                {"key": key, "label": label,
                 "on": key == (block or {}).get("dimension")}
                for key, label in product_taxonomy.DIMENSIONS
            ],
            rows=rows, block=block,
            selected_employee=selected,
            company=dashboard_presentation.totals_cards(company),
            empty=data.totals.lines == 0)

    @app.get("/kinh-doanh/phan-tich/gio-hang")
    def analytics_basket():
        """R6 §5 — Giỏ hàng: bốn ô tách rời, cặp xác định, attachment hai chiều."""
        view = _analysis_view()
        index = _basket_index(view)
        dimension = request.args.get("chieu")
        dimension = (product_taxonomy.DIMENSION_CATEGORY
                     if dimension == product_taxonomy.DIMENSION_CATEGORY
                     else product_taxonomy.DIMENSION_PRODUCT)
        if dimension == product_taxonomy.DIMENSION_CATEGORY:
            min_support = basket_metrics.DEFAULT_CATEGORY_MIN_SUPPORT
            pairs = basket_metrics.category_pairs(index,
                                                  min_support=min_support)
        else:
            min_support = basket_metrics.DEFAULT_PRODUCT_MIN_SUPPORT
            pairs = basket_metrics.product_pairs(index, min_support=min_support)
        counts = basket_metrics.counts(index)
        return render_template(
            "kinh_doanh_phan_tich_gio_hang.html",
            periods=view["periods"],
            scope=_analysis_scope_block(view),
            columns=dashboard_presentation.PAIR_COLUMNS,
            dimensions=[
                {"key": key, "label": label, "on": key == dimension}
                for key, label in product_taxonomy.DIMENSIONS
                if key != product_taxonomy.DIMENSION_BRAND
            ],
            cards=dashboard_presentation.basket_cards(counts),
            rows=dashboard_presentation.pair_rows(pairs),
            summary=dashboard_presentation.basket_summary(
                counts, dimension=dimension, scope_label=view["range"].label,
                min_support=min_support, shown_pairs=len(pairs)),
            dimension=dimension)

    @app.get("/kinh-doanh/phan-tich/don-hang")
    def analytics_drilldown():
        """R6 §5 — Bảng kê drill-down của một bucket hoặc một cặp.

        Nó đọc lại ĐÚNG lát dữ liệu của phạm vi đang xem rồi lọc theo
        `order_key`, nên nó không thể hiện một dòng mà trang cha đang không
        tính. Bốn cột, không một trường khách hàng nào — xem
        `dashboard_presentation.drilldown_rows`.
        """
        view = _analysis_view()
        index = _basket_index(view)
        dimension = (product_taxonomy.DIMENSION_CATEGORY
                     if request.args.get("chieu")
                     == product_taxonomy.DIMENSION_CATEGORY
                     else product_taxonomy.DIMENSION_PRODUCT)
        left = request.args.get("a") or ""
        right = request.args.get("b") or ""
        basket_dimension = ("category"
                            if dimension == product_taxonomy.DIMENSION_CATEGORY
                            else "product")
        if left and right:
            order_keys = set(basket_metrics.orders_with_pair(
                index, left=left, right=right, dimension=basket_dimension))
            filter_label = f"Đơn chứa CẢ HAI: {left} · {right}"
        elif left:
            order_keys = set(basket_metrics.orders_containing(
                index, member=left, dimension=basket_dimension))
            filter_label = f"Đơn chứa: {left}"
        else:
            order_keys = {line.order_key for line in view["data"].lines}
            filter_label = "Toàn bộ đơn của phạm vi"
        keep = [index_ for index_, detail
                in enumerate(view["data"].details)
                if detail["order_key"] in order_keys]
        details = [view["data"].details[index_] for index_ in keep]
        metadata = [view["metadata"][index_] for index_ in keep]
        return render_template(
            "kinh_doanh_phan_tich_don_hang.html",
            periods=view["periods"],
            scope=_analysis_scope_block(view),
            columns=dashboard_presentation.DRILLDOWN_COLUMNS,
            rows=dashboard_presentation.drilldown_rows(details, metadata),
            orders=len(order_keys),
            filter_label=filter_label,
            scope_note=dashboard_presentation.DRILLDOWN_SCOPE_NOTE)

    @app.post("/run")
    def run_report():
        upload = request.files.get("workbook")
        if upload is None or not upload.filename:
            return _page(error="Hãy chọn một workbook .xlsx trước khi chạy.", status=400)
        if not upload.filename.lower().endswith(".xlsx"):
            return _page(error="Chỉ chấp nhận file .xlsx.", status=400)
        display_name = _safe_display_name(upload.filename)

        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        temp_path = UPLOAD_DIR / f"{uuid.uuid4().hex}.xlsx"
        upload.save(temp_path)
        started = time.monotonic()
        live_handle = None
        # R2 Gói 1 — ĐỌC MỘT LẦN, DÙNG HAI CHỖ.
        #
        # Đây là mối nối mà R2 phải sửa. Trước bản này, `live_pull` và
        # `demo.run_demo` mỗi bên tự mở một `JsonlProductIdentityStore` trên
        # `data/product_identity/mappings.jsonl` — tức đĩa EPHEMERAL của
        # container, trong khi log thật của bản Web nằm ở R2. Cả hai luôn đọc
        # ra một store RỖNG, nên mọi mặt hàng Owner đã chọn trên giao diện
        # không lọt vào tập mã hỏi `daily-min` VÀ không được resolver dùng.
        # Bảng chọn vẫn chạy, log vẫn ghi, và báo cáo không đổi một chữ.
        #
        # Một ảnh chụp DUY NHẤT cho cả lần chạy, không phải hai: kế hoạch hỏi
        # giá và phép phân giải phải nhìn cùng một trạng thái, nếu không một
        # xác nhận xảy ra giữa hai lần đọc sẽ làm tập mã được hỏi khác tập mã
        # được phân giải — và dòng đó thiếu giá mà không lý do nào giải thích.
        identity_view = identity_gateway.store_view(identity_store)
        try:
            try:
                captures, tracking_evidence, live_handle = _select_captures_for_run(
                    sales=temp_path, identity_store_view=identity_view
                )
            except live_pull.DailyMinPeriodTooWideError as exc:
                # KHÔNG phải lỗi Tracking, nên KHÔNG nói "thử lại sau" — thử
                # lại bao nhiêu lần cũng thế. Và tuyệt đối không chạy tiếp để
                # ra một báo cáo đầy đủ hình thức mà không có giá vốn nào.
                return _page(
                    error=(
                        f"Sổ này trải {exc.day_span} ngày — rộng hơn mức một "
                        "lần chạy hỏi được giá theo ngày bán. Hãy tách sổ theo "
                        "tháng (hoặc quý) rồi chạy lại từng kỳ."
                    ),
                    status=400,
                )
            except live_pull.TrackingUnavailableError as exc:
                return _page(
                    error=(
                        "Không lấy được dữ liệu Tracking trực tiếp (nguồn: "
                        f"{exc.node}). Đây KHÔNG phải lỗi của workbook — vui "
                        "lòng thử lại sau."
                    ),
                    status=503,
                )
            try:
                owner_run = run_owner_report(
                    sales=temp_path, captures=captures,
                    identity_store_view=identity_view)
            except OwnerUsabilityError as exc:
                return _page(error=str(exc), status=400)
            except Exception:
                return _page(
                    error="Không thể tạo báo cáo. Kiểm tra workbook và thử lại.",
                    status=400,
                )

            # `R5.1 REPAIR-2` — làm mới bản chiếu hiển thị NGAY trên luồng
            # chính, từ capture danh mục CỦA CHÍNH lần chạy này.
            #
            # Ưu tiên `owner_run.captures`, KHÔNG phải biến `captures` của
            # route: khi `live_pull` chưa cấu hình (máy Owner), route truyền
            # `None` và `run_owner_report` tự chọn capture cục bộ —
            # `owner_run.captures` là nơi duy nhất biết capture nào ĐÃ THẬT SỰ
            # được dùng.
            #
            # `getattr(...) or captures` là một hàng rào có chủ ý, không phải
            # phòng thủ mù: hợp đồng của `run_owner_report` là một điểm nối mà
            # nhiều bài kiểm thay bằng một đối tượng giả gọn hơn, và một tính
            # năng NHÃN không được phép làm sập cả lần chạy báo cáo chỉ vì đối
            # tượng ấy thiếu một trường. Cả hai vế `None` ⟹ `NO_SNAPSHOT`, và
            # bằng chứng của run nói ra điều đó.
            #
            # Kết quả đi vào `tracking_evidence`, nên một lần ghi thất bại có
            # mặt trong bằng chứng của run thay vì biến mất.
            #
            # `R5.3` — `run_id` được tính TRƯỚC lời gọi này (nó chỉ là
            # `output_path.stem`, không phụ thuộc gì ở dưới), vì bản lưu BỀN
            # của nhãn được khoá theo chính lần chạy ấy: nhãn của một lần
            # chạy phải sống đúng bằng vòng đời dữ liệu mà nó chú thích.
            run_id = owner_run.output_path.stem
            catalog_status, catalog_durable = _refresh_catalog_display(
                getattr(owner_run, "captures", None) or captures,
                run_id=run_id)
            tracking_evidence = {
                **(tracking_evidence or {}),
                "catalog_display": {
                    **catalog_status.as_evidence(),
                    # `R5.3` — bằng chứng của NHÁNH BỀN, tách khỏi bằng chứng
                    # của cache trên đĩa. Hai nơi lưu có thể thành công/thất
                    # bại độc lập, và gộp chúng thành một cờ sẽ giấu đúng cái
                    # nửa đang hỏng.
                    "durable": catalog_durable,
                },
            }

            duration_ms = int((time.monotonic() - started) * 1000)
            summary = owner_run.demo_run.summary
            dropped_lines = len(owner_run.demo_run.result.unmapped_lines)

            def _persist_run() -> None:
                # save_artifact (R2: upload + verify + xoá temp; local: chỉ
                # tính path tương đối, file đã nằm sẵn dưới ARTIFACT_DIR) PHẢI
                # thành công trước khi ghi run — không được để lộ một run
                # "thành công" mà artifact không thực sự tồn tại ở nơi lưu.
                artifact_ref = store.save_artifact(owner_run.output_path, run_id)
                store.create_run(
                    run_id=run_id,
                    created_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    status=run_registry.STATUS_COMPLETE,
                    workbook_display_name=display_name,
                    artifact_path=artifact_ref,
                    view=_build_view(summary, dropped_lines=dropped_lines),
                    tracking_evidence=tracking_evidence,
                )

            try:
                if snapshot_repo is None:
                    # Dev chưa cấu hình history store: vẫn chạy như S071B,
                    # nhưng trang kết quả nói thẳng là run này KHÔNG có lịch sử
                    # — không bao giờ để người dùng tin là đã lưu.
                    _persist_run()
                else:
                    # MỘT đơn vị công việc: lịch sử + artifact + run cùng cam
                    # kết hoặc cùng rollback (TASK-PRA-002 mục 11.2).
                    history_writer.write_run_history(
                        snapshot_repo, demo_run=owner_run.demo_run, run_id=run_id,
                        workbook_path=temp_path, display_name=display_name,
                        tracking_evidence=tracking_evidence, on_persisted=_persist_run,
                    )
            except Exception:
                # Report ĐÃ được tạo trên đĩa tạm, nhưng không lưu được vào
                # nơi lưu trữ (artifact upload lỗi, ghi metadata lỗi, hoặc ghi
                # lịch sử lỗi) — không được trả về như thể mọi thứ thành công
                # (không có run_id để Owner tra lại). Fail rõ, không giả.
                return _page(
                    error=(
                        "Báo cáo đã tạo nhưng không lưu được vào lịch sử run. "
                        "Vui lòng thử lại."
                    ),
                    status=500,
                )
        finally:
            # Workbook chỉ được xoá SAU khi history writer đã đọc xong header
            # và fingerprint của chính bytes đã upload.
            temp_path.unlink(missing_ok=True)
            if live_handle is not None:
                live_handle.cleanup()

        _record_telemetry(run_id, summary, duration_ms)
        # Post-Redirect-Get: tránh chạy lại báo cáo khi Owner bấm refresh.
        return redirect(url_for("index", run_id=run_id))

    @app.get("/artifact/<run_id>")
    def download_artifact(run_id: str):
        record = _guarded(store.get_run, run_id)
        if record is None or not record.artifact_path:
            abort(404)
        # store.artifact_response() tự resolve artifact_path CHỈ qua đúng
        # record authoritative này — browser không bao giờ cung cấp key/path
        # trực tiếp (local: chặn path traversal dưới ARTIFACT_DIR; R2: key
        # luôn tự suy từ run_id, xem app/web/storage_backend.py).
        response = _guarded(store.artifact_response, record)
        if response is None:
            abort(404)
        return response

    @app.post("/feedback")
    def submit_feedback():
        category = request.form.get("category", "")
        comment = request.form.get("comment", "")
        run_id = request.form.get("run_id") or None
        try:
            record = beta_feedback.build_feedback_record(
                category=category, comment=comment, run_id=run_id,
            )
        except beta_feedback.InvalidFeedbackError:
            return _page(error="Loại phản hồi không hợp lệ.", run_id=run_id, status=400)
        beta_feedback.save_feedback(record)
        return redirect(url_for("index", run_id=run_id, feedback="ok"))

    # ==================================================================
    # `API-01`/`API-02` — chi tiết MỘT đơn, và một lần PATCH của nó.
    #
    # Vì sao hai route này tồn tại, bằng con số đo được ở
    # `scripts/stab01_baseline.py`: mở chế độ sửa một đơn trên fixture
    # 5.000 dòng trả ~14,5 MB HTML và 5.002 hàng `<tr>`, vì nó dựng lại CẢ
    # bảng kê. Ngân sách của brief §6 cho chi tiết một đơn là dưới 50 KB.
    #
    # Chúng KHÔNG thay các route HTML. Route `?sua=` cũ còn nguyên, và đó
    # là điều kiện của "lớp tăng cường": tắt JavaScript thì luồng sửa đơn
    # vẫn chạy y như trước, qua form và POST thật.
    #
    # Cả hai KHÔNG dựng một thẩm quyền nghiệp vụ nào mới. Chúng gọi đúng
    # `plan_order_edit`/`apply_order_edit` mà form HTML gọi, và đọc đúng
    # `PeriodData` mà bảng HTML đọc — xem `app/web/order_api.py`
    # § "Ranh giới cứng".
    # ==================================================================

    def _api_period_choice(periods: list[tuple[int, int]]):
        """Kỳ của một request API — `period` trước, `ky` sau.

        Không viết lại phép phân tích: `_business_period_choice` đọc
        `request.values`, nên chỉ cần đảm bảo có một khoá `ky` để nó đọc.
        Đường ngắn nhất làm được điều đó mà không sửa hàm cũ là phân tích
        `period` ở đây theo CÙNG một câu, và trả về `None` cho cùng những
        đầu vào mà hàm kia trả `None`.
        """
        raw = (request.values.get("period") or "").strip()
        if not raw:
            return _business_period_choice(periods)
        year_text, _, month_text = raw.partition("-")
        try:
            chosen = (int(year_text), int(month_text))
        except ValueError:
            return None
        return chosen if chosen in periods else None

    def _api_error(code: str, message: str, *, status: int, **extra):
        """Lỗi JSON có MÃ ỔN ĐỊNH, theo MỘT schema cho mọi đường `/api/`.

            {"error": {"code": …, "message": …, "request_id": …, …}}

        `request_id` nằm TRONG `error` (không cạnh nó) vì `P1-3` đòi một
        schema duy nhất, và một client bắt lỗi chỉ phải đọc đúng một chỗ.
        Giá trị của nó là `trace_id` do server sinh — không phải
        `idempotency_key` của client (`P1-2`/`P1-4`).

        Câu chữ tiếng Việt được phép sửa cho dễ đọc; `code` thì không, vì
        nó là hợp đồng (brief §API-02 liệt kê tập mã).
        """
        return {"error": {"code": code, "message": message,
                          "request_id": request_timing.trace_id(),
                          **extra}}, status

    def _api_order_view(order_key: str):
        """`(view, lỗi)` — kỳ + dữ liệu cho một request API CHỈ ĐỌC.

        Chỉ `api_order_detail` dùng hàm này. `api_patch_order` KHÔNG dùng:
        nó phải đọc bên trong transaction ghi, qua `service.bind()` — xem
        docstring của nó. Một hàm dựng dữ liệu ngoài transaction rồi cho
        đường ghi mượn lại là đúng cách `P0-3` phát sinh.
        """
        service = _require_business()
        periods = _guarded(analytics_queries.available_periods,
                           snapshot_repo.engine)
        period = _api_period_choice(periods)
        if period is None:
            return None, _api_error(
                mutation_guard.NOT_FOUND,
                "Không đọc được kỳ. Hãy gửi `period=YYYY-MM` của một kỳ đã "
                "có dữ liệu.", status=404)
        bounds = analytics_queries.month_bounds(*period)
        data = _guarded(service.period, date_from=bounds[0],
                        date_to=bounds[1], period=period)
        return {"service": service, "period": period, "data": data}, None

    @app.get("/api/v1/orders/<order_key>")
    def api_order_detail(order_key: str):
        """`API-01` — chi tiết của ĐÚNG một đơn, JSON gọn.

        Không dựng workspace, không trả HTML của bảng, không đọc IMEI
        (`DEC-R5-03`). Quyền và validation vẫn ở server: `can_edit` phản
        ánh trạng thái chốt kỳ thật, và một client bỏ qua nó vẫn bị
        `PATCH` từ chối.
        """
        view, failure = _api_order_view(order_key)
        if failure is not None:
            return failure
        payload = order_api.detail_payload(
            data=view["data"], order_key=order_key, period=view["period"],
            service=view["service"],
            # Quyền sửa = kỳ chưa chốt. Đây là cùng cửa mà `_guard_lines`
            # áp lúc ghi, đọc trước để panel hiện đúng trạng thái ngay —
            # nhưng cửa THẬT vẫn là `_guard_lines`, không phải cờ này.
            can_edit=not view["service"].period_store.is_closed(view["period"]))
        if payload is None:
            return _api_error(
                mutation_guard.NOT_FOUND,
                f"Không có đơn {order_key} trong kỳ này.", status=404)
        payload["trace_id"] = request_timing.trace_id()
        return payload

    @app.patch("/api/v1/orders/<order_key>")
    def api_patch_order(order_key: str):
        """`API-02` — lưu phần thay đổi của MỘT đơn, có CAS revision + at-most-once.

        ## Bản trước SAI ở đâu

        Bản trước xếp bốn cửa nối tiếp, mỗi cửa một transaction riêng:
        `replay_of()` → kiểm revision → `apply_order_edit` → `remember()`.
        Review độc lập chứng minh bằng probe trên PostgreSQL 16 rằng cách
        xếp đó KHÔNG cho at-most-once: hai request đồng thời cùng
        `request_id` gọi `set_purchase_price()` HAI lần, và một crash trước
        `remember()` để lại lần ghi trong database với sổ chống lặp rỗng.

        Vấn đề không phải thứ tự — nó là việc CÓ những khoảng giữa các cửa.

        ## Bản này

        MỘT transaction bao tất cả, mở bởi `guard.transaction()`. Bên
        trong nó, theo đúng thứ tự mà `mutation_guard` thi hành:

            INSERT sổ (khoá chính = cửa loại trừ)
            → khoá theo đơn
            → TÍNH LẠI revision trong khoá, so với `base_revision`  (CAS)
            → validate + ghi nghiệp vụ qua store đã BIND vào transaction
            → UPDATE sổ thành `applied` + payload

        `service.bind(connection)` là mảnh làm cho "đọc để kiểm" và "ghi"
        dùng CÙNG kết nối. Không có nó, phép kiểm revision đọc một ảnh
        chụp ngoài transaction và mọi thứ khác chỉ là hình thức.

        ## `period` được dựng MỘT lần, không hai

        `P2-3` — bản trước dựng `PeriodData` hai lần (một để kiểm, một để
        trả revision mới). Nay kỳ được dựng bên trong transaction, dùng
        cho CẢ phép kiểm; và sau khi ghi, dựng lại đúng một lần nữa để
        payload mang revision MỚI. Đọc lại là bắt buộc và không thay được
        bằng tính nhẩm: trả về revision cũ sẽ làm panel gửi lần sau với
        một `base_revision` lỗi thời ngay từ lúc nó nhận được.
        """
        body = request.get_json(silent=True) or {}
        # `P1-4` — client gửi `idempotency_key`. Tên `request_id` vẫn được
        # NHẬN để không phá client cũ, nhưng nó không còn là tên chính:
        # bản trước dùng cùng một tên cho cả mã truy vết và mã chống lặp ở
        # hai nhánh khác nhau của cùng một response.
        try:
            idempotency_key = mutation_guard.clean_idempotency_key(
                body.get("idempotency_key") or body.get("request_id"))
        except mutation_guard.MissingIdempotencyKeyError as exc:
            return _api_error(mutation_guard.VALIDATION_ERROR, str(exc),
                              status=400, field="idempotency_key")

        service = _require_business()
        guard = mutation_guard.MutationGuard(snapshot_repo.engine)

        # Đường NGẮN cho một lần thử lại đã có kết quả. Đây là một phép
        # ĐỌC, và nó KHÔNG phải cửa an toàn — cửa an toàn là khoá chính
        # bên trong transaction. Nó chỉ tránh mở một transaction ghi cho
        # một câu trả lời đã có sẵn.
        settled = guard.applied(idempotency_key)
        if settled is not None:
            return _replayed(settled)

        periods = _guarded(analytics_queries.available_periods,
                           snapshot_repo.engine)
        period = _api_period_choice(periods)
        if period is None:
            return _api_error(
                mutation_guard.NOT_FOUND,
                "Không đọc được kỳ. Hãy gửi `period=YYYY-MM` của một kỳ đã "
                "có dữ liệu.", status=404)
        bounds = analytics_queries.month_bounds(*period)
        base_revision = body.get("base_revision")

        changes = body.get("changes") or {}
        if not isinstance(changes, dict):
            return _api_error(
                mutation_guard.VALIDATION_ERROR,
                "`changes` phải là một đối tượng.", status=400, field="changes")
        try:
            prices = _api_submitted_prices(order_key, changes.get("prices"))
        except ValueError as exc:
            return _api_error(mutation_guard.VALIDATION_ERROR, str(exc),
                              status=400, field="changes.prices")
        employee = changes.get("employee")
        actor = identity_gateway.actor_of()

        # `outcome` được đặt bên trong transaction và đọc lại sau khi nó
        # commit. Một biến chứ một `return` bên trong khối: `return` từ
        # trong thân `with` sẽ bỏ qua bước chốt sổ ở `transaction()`.
        outcome: dict = {}

        def revision_inside(connection):
            """Revision hiện tại, đọc qua CHÍNH kết nối của transaction.

            Đây là nửa "read" của compare-and-swap, và nó phải đọc trong
            transaction: một phép đọc ngoài sẽ trả ảnh chụp cũ và làm cả
            cơ chế vô nghĩa (`P0-3`).
            """
            bound = service.bind(connection)
            data = bound.period(date_from=bounds[0], date_to=bounds[1],
                                period=period)
            outcome["data"] = data
            outcome["bound"] = bound
            return order_revision.of_order(data, order_key)

        try:
            with guard.transaction(
                idempotency_key=idempotency_key, route="api_patch_order",
                subject=order_key, base_revision=base_revision,
                revision_of=revision_inside, entered_by=actor,
            ) as ctx:
                bound, data = outcome["bound"], outcome["data"]
                if ctx["current_revision"] is None:
                    raise _ApiFailure(_api_error(
                        mutation_guard.NOT_FOUND,
                        f"Không có đơn {order_key} trong kỳ này.", status=404))

                # Validate TOÀN BỘ rồi mới ghi — `plan_order_edit` không
                # ghi gì, và nó đọc qua store đã bind.
                try:
                    plan = bound.plan_order_edit(
                        data=data, order_key=order_key,
                        employee=((employee or None) if employee is not None
                                  else None),
                        prices=prices, reason=(body.get("reason") or None))
                except business_service.OrderNotFoundError:
                    raise _ApiFailure(_api_error(
                        mutation_guard.NOT_FOUND,
                        f"Không có đơn {order_key} trong kỳ này.",
                        status=404)) from None
                if not plan.ok:
                    raise _ApiFailure(_api_error(
                        mutation_guard.VALIDATION_ERROR,
                        " ".join(plan.errors), status=422,
                        order_revision=ctx["current_revision"]))

                # Kỳ đã chốt chặn cả một lần sửa hợp lệ (R3 §5). Gọi
                # `guard_line_open` trực tiếp chứ không qua `_guard_lines`:
                # hàm đó bọc `_guarded`, và `_guarded` biến
                # `PeriodClosedError` thành `abort(409)` — một trang HTML,
                # sai cho một endpoint JSON.
                try:
                    for detail in plan.details:
                        bound.guard_line_open(detail)
                except period_lock.PeriodClosedError as exc:
                    raise _ApiFailure(_api_error(
                        mutation_guard.PERIOD_CLOSED, str(exc), status=409,
                        order_revision=ctx["current_revision"])) from None

                sheet = _api_sheet_of(bound, data)
                if plan.changes_nothing:
                    # KHÔNG ghi gì. Sổ vẫn được chốt `applied` với payload
                    # này, và đó là đúng: mã đã được dùng, nên một lần gửi
                    # sau mang cùng mã phải nhận lại chính câu trả lời này
                    # thay vì được ghi như một quyết định mới.
                    ctx["response"] = {
                        **order_api.patch_payload(
                            data=data, order_key=order_key, period=period,
                            service=bound, plan=plan, message=plan.summary(),
                            sheet=sheet),
                        "changed_nothing": True,
                    }
                    outcome["payload"] = ctx["response"]
                    return _applied_response(ctx, outcome["payload"])

                message = bound.apply_order_edit(plan, entered_by=actor)

                # ĐỌC LẠI kỳ, vẫn TRONG transaction: revision mới phải
                # phản ánh lần ghi vừa rồi, và lần ghi đó chưa commit nên
                # chỉ kết nối này thấy được nó.
                fresh = bound.period(date_from=bounds[0], date_to=bounds[1],
                                     period=period)
                ctx["response"] = order_api.patch_payload(
                    data=fresh, order_key=order_key, period=period,
                    service=bound, plan=plan, message=message,
                    sheet=_api_sheet_of(bound, fresh))
                outcome["payload"] = ctx["response"]
                outcome["ctx"] = {"audit_id": ctx["audit_id"],
                                  "entered_at": ctx["entered_at"],
                                  "entered_by": ctx["entered_by"]}
        except _ApiFailure as failure:
            return failure.response
        except mutation_guard.AlreadyApplied as hit:
            # Một request khác mang cùng mã đã commit trong lúc ta đang
            # chạy. Đây là cơ chế ĐANG HOẠT ĐỘNG, không phải lỗi.
            return _replayed(hit.applied)
        except mutation_guard.RequestInFlightError as exc:
            # Cùng mã, request kia CHƯA commit. Không có kết quả để trả,
            # và ghi lần thứ hai là đúng điều bị cấm. 409 + mã ổn định để
            # client thử lại có kiểm soát.
            return _api_error(mutation_guard.REQUEST_IN_FLIGHT, str(exc),
                              status=409, retry_after_seconds=1)
        except mutation_guard.RevisionConflict as conflict:
            # Phát hiện BÊN TRONG transaction, sau khi đã giữ khoá đơn —
            # nên `current_revision` là bản THẬT tại thời điểm từ chối.
            # Transaction đã rollback, nên KHÔNG có gì được ghi.
            return _revision_conflict_response(
                order_key=order_key, period=period, bounds=bounds,
                service=service, current_revision=conflict.current_revision)

        return _applied_response(outcome.get("ctx", {}), outcome["payload"])

    # ==================================================================
    # `UI-04` — MỘT TRANG của bảng kê, và `UI-03` — bảng chọn phân loại.
    #
    # Cả hai là route CHỈ ĐỌC, và cả hai trả về HTML do CHÍNH những macro
    # mà trang đầy đủ dùng dựng ra (`_workspace_table.html`), gói trong một
    # phong bì JSON. Đây là một quyết định có chủ ý và nó đi ngược một trực
    # giác phổ biến ("API thì phải trả dữ liệu, không trả HTML"), nên lý do
    # được viết ra ở đây:
    #
    # Một hàng bảng kê mang `rowspan` theo số dòng của BH, ba cột tuỳ chọn
    # ẩn bằng CSS, bốn loại nhãn trạng thái, hai đường vào phân loại, một ô
    # nhập thuộc về một `<form>` đứng ngoài bảng. Trả dữ liệu thô rồi để
    # `app.js` ghép lại tất cả những thứ đó = một BẢN DỰNG THỨ HAI của bảng
    # kê, bằng một ngôn ngữ khác, không có test template nào soi tới. Bản
    # thứ hai ấy sẽ lệch khỏi bản thứ nhất ở lần đầu tiên ai đó thêm một
    # cột — và cả hai sẽ "đúng" theo chính nó.
    #
    # Con SỐ thì vẫn là JSON thật (`total_lines`, `next_cursor`, `lines`):
    # client cần chúng để quyết định tải tiếp hay dừng, và chúng không phải
    # markup.
    # ==================================================================

    def _api_page_limit() -> int:
        """`limit` client gửi, đã kẹp về khoảng dùng được."""
        try:
            value = int(request.args.get("limit") or "")
        except ValueError:
            return workspace_presentation.WORKSPACE_PAGE_LINES
        return max(1, min(value, workspace_presentation.WORKSPACE_PAGE_LINES_MAX))

    @app.get("/api/v1/periods/<period>/workspace")
    def api_workspace_page(period: str):
        """`UI-04` — trang kế của bảng kê, theo con trỏ BH.

        Kỳ nằm trong ĐƯỜNG DẪN (`/api/v1/periods/2026-09/workspace`), sheet
        và con trỏ trong query — cùng hình dạng `/api/v1/orders/<order_key>`
        đã dùng: thứ định danh tài nguyên đi vào path, thứ lọc/phân trang đi
        vào query.

        Route này KHÔNG ghi gì và KHÔNG tính lại một con số nào: nó gọi đúng
        `_workspace_context` mà trang đầy đủ gọi, chỉ với một con trỏ khác.
        """
        view = _workspace_view(period)
        context = _workspace_context(
            view, cursor=(request.args.get("cursor") or None),
            limit=_api_page_limit())
        page = context["page"]
        macros = _workspace_macros()
        return {
            "schema_version": workspace_presentation.WORKSPACE_SCHEMA_VERSION,
            "period": view["selected_period"],
            "sheet": view["sheet"].key,
            "cursor": page["cursor"],
            "next_cursor": page["next_cursor"],
            "order_keys": page["order_keys"],
            "lines": len(page["details"]),
            # Hai con số của CẢ sheet, không của trang: client dùng chúng để
            # biết còn bao nhiêu mà không phải đếm thứ nó chưa tải.
            "total_lines": page["total_lines"],
            "total_orders": page["total_orders"],
            "rows_html": str(macros.detail_rows(
                context["groups"], context["selected_period"],
                context["sheet"], context["editing"], context["assignable"],
                context["unclassifiable_note"])),
            "regions": {
                "page-more": str(macros.page_more(
                    page, context["selected_period"], context["sheet"])),
            },
            "trace_id": request_timing.trace_id(),
        }

    @app.get("/api/v1/periods/<period>/identify")
    def api_identify_panel(period: str):
        """`UI-03` — bảng chọn mặt hàng của ĐÚNG MỘT dòng, không dựng lại trang.

        Trước `UI-03`, mở bảng chọn đi qua lớp mảnh (`X-Fragment`) và thay
        CẢ `#app-content` — tức dựng lại toàn bộ bảng kê để hiện một hộp nhỏ
        cạnh con trỏ chuột. Route này trả về đúng khối ấy và không gì khác.

        `None` (dòng đã phân loại xong, hoặc không tồn tại) trả về chuỗi
        rỗng chứ không 404: "không có gì để mở ở đây" là một câu trả lời
        hợp lệ của chính màn hình này (xem `_identify_panel`), không phải
        một lỗi.
        """
        view = _workspace_view(period)
        scoped = view["data"].for_sheet(view["sheet"])
        decisions = _identity_decisions()
        identify = _identify_panel(view, scoped, decisions)
        macros = _workspace_macros()
        return {
            "schema_version": workspace_presentation.WORKSPACE_SCHEMA_VERSION,
            "found": identify is not None,
            "regions": {
                "identify": str(macros.identify_panel(
                    identify, view["selected_period"], view["sheet"])),
            },
            "trace_id": request_timing.trace_id(),
        }

    class _ApiFailure(Exception):
        """Một lỗi API phát sinh BÊN TRONG transaction.

        Ném thay vì `return`: `return` từ trong thân `with` của
        `guard.transaction()` sẽ chạy tiếp bước chốt sổ và ghi nhận một
        lần ghi chưa xảy ra. Ném thì transaction rollback — cả hàng sổ lẫn
        mọi thứ khác — và route trả về response đã dựng sẵn.
        """

        def __init__(self, response) -> None:
            super().__init__("api failure")
            self.response = response

    def _api_sheet_of(bound_service, data):
        """Sheet đang xem, đọc qua service ĐÃ BIND. `None` khi không nói sheet.

        `None` là câu trả lời hợp lệ: PATCH từ khung nhìn toàn kỳ vẫn ghi
        được, chỉ là response không kèm tổng của sheet nào. Đoán một sheet
        ở đây sẽ trả về tổng của một đơn vị báo cáo mà người gọi không hỏi.
        """
        key = request.values.get("sheet")
        if not key:
            return None
        return reporting_sheets.find_sheet(bound_service.sheets(data), key)

    def _applied_response(ctx: dict, payload: dict):
        """Response thành công, mang đủ BA loại mã đúng nghĩa của chúng."""
        return {
            **payload,
            # `P1-4` — ba tên, ba nghĩa. `audit_id` là mã LẦN GHI và nó có
            # mặt ở CẢ nhánh này lẫn nhánh replay; `trace_id` là mã của
            # REQUEST này và nó khác nhau ở hai lần thử lại.
            "audit_id": ctx.get("audit_id"),
            "applied_at": ctx.get("entered_at"),
            "applied_by": ctx.get("entered_by"),
            "trace_id": request_timing.trace_id(),
        }

    def _replayed(settled):
        """Response của một lần THỬ LẠI đã có kết quả đã commit.

        `P1-4` — `audit_id` được lấy từ payload đã lưu, nên nó có mặt ở
        đây y như ở lần ghi gốc. Bản trước ghi sổ TRƯỚC khi gắn `audit_id`
        vào payload, nên nhánh này trả về `audit_id: None` — và UI sẽ đọc
        sai đúng chỗ đó.
        """
        return {
            **settled.response,
            "already_applied": True,
            "audit_id": settled.audit_id or None,
            "applied_at": settled.entered_at,
            "applied_by": settled.entered_by,
            "trace_id": request_timing.trace_id(),
        }

    def _revision_conflict_response(*, order_key, period, bounds, service,
                                    current_revision):
        """`REVISION_CONFLICT` kèm bản HIỆN TẠI của đơn.

        Brief §UI-03: "khi revision cũ, trả bản hiện tại và trường đã thay
        đổi… không âm thầm last-write-wins". Bản hiện tại được đọc SAU khi
        transaction đã rollback, nên nó là một transaction đọc riêng —
        đúng, vì lúc này không còn gì phải bảo vệ: ta đã từ chối ghi.
        """
        data = _guarded(service.period, date_from=bounds[0],
                        date_to=bounds[1], period=period)
        return _api_error(
            mutation_guard.REVISION_CONFLICT,
            "Đơn này đã được thay đổi từ lúc bạn mở nó. Bản nháp của bạn "
            "vẫn còn — hãy so với bản mới rồi quyết định gửi lại hay lấy "
            "giá trị mới.",
            status=409,
            order_revision=current_revision,
            period_revision=order_revision.of_period(data, period),
            current=order_api.detail_payload(
                data=data, order_key=order_key, period=period,
                service=service,
                can_edit=not service.period_store.is_closed(period)))

    def _api_submitted_prices(order_key: str, raw) -> dict:
        """`changes.prices` của JSON → `{khoá dòng: chuỗi người gõ}`.

        Cùng hình dạng `_submitted_prices` trả về từ form HTML, nên
        `plan_order_edit` nhận đúng một loại đầu vào từ cả hai đường. Đó là
        điều giữ cho không có đường ghi thứ hai với luật riêng của nó.

        Mỗi phần tử phải mang ĐỦ `product_key` + `occurrence_index`. Thiếu
        một phần là TỪ CHỐI, không đoán: đoán ở đây nghĩa là ghi một giá
        lên một dòng mà người gửi không chỉ định.

        `value` là CHUỖI người gõ, không phải số — chuỗi rỗng nghĩa là GỠ
        giá tay, và một `0` là một giá bằng không. `null`/số bị từ chối để
        hai ý nghĩa đó không bị trộn ở tầng JSON.
        """
        if raw is None:
            return {}
        if not isinstance(raw, list):
            raise ValueError("`changes.prices` phải là một danh sách.")
        prices = {}
        for index, item in enumerate(raw):
            if not isinstance(item, dict):
                raise ValueError(f"`changes.prices[{index}]` phải là đối tượng.")
            product_key = item.get("product_key")
            occurrence = item.get("occurrence_index")
            if not product_key or occurrence is None:
                raise ValueError(
                    f"`changes.prices[{index}]` thiếu product_key hoặc "
                    "occurrence_index — khoá dòng phải đủ ba phần.")
            try:
                occurrence = int(occurrence)
            except (TypeError, ValueError):
                raise ValueError(
                    f"`changes.prices[{index}].occurrence_index` phải là số "
                    "nguyên.") from None
            value = item.get("value")
            if not isinstance(value, str):
                raise ValueError(
                    f"`changes.prices[{index}].value` phải là CHUỖI. Chuỗi "
                    "rỗng nghĩa là gỡ giá tay; một số 0 là giá bằng không — "
                    "hai ý nghĩa đó không được trộn.")
            prices[(order_key, str(product_key), occurrence)] = value
        return prices

    # --- `P1-3`: mọi lỗi trên `/api/` trả JSON, không trả TRANG --------
    #
    # Bản trước đăng ký MỘT handler cho `HTTPException` và tin rằng nó bắt
    # được mọi mã. Review chứng minh nó không: Flask chọn handler theo mã
    # CỤ THỂ trước, nên `@errorhandler(404)`/`(500)`/`(409)`/`(503)` bên
    # dưới thắng nó — và đúng ba ca quan trọng nhất (`404` Flask, `500`
    # exception, `abort(503)` từ `_guarded`) trả về một trang HTML cho một
    # `fetch()` đang chờ `{"error": {"code": …}}`.
    #
    # Cách đóng: cửa kiểm `/api/` nằm TRONG TỪNG handler, không ở một
    # handler bao ngoài. `_error_response()` là chỗ duy nhất quyết định
    # JSON hay trang, nên không handler nào có thể quên — thêm một
    # `errorhandler` mới mà gọi hàm này là đã đúng.
    def _error_response(*, code: str, message: str, status: int):
        """Lỗi cho CẢ hai loại người gọi, phân biệt bằng đường dẫn.

        `/api/` → JSON theo đúng schema của `_api_error`:

            {"error": {"code": …, "message": …, "request_id": …}}

        Còn lại → trang HTML như trước, không đổi một chữ.
        """
        if request.path.startswith("/api/"):
            return {"error": {"code": code, "message": message,
                              "request_id": request_timing.trace_id()}}, status
        return _page(error=message, status=status)

    @app.errorhandler(HTTPException)
    def _http_error(exc):  # noqa: C901 — một nhánh, hai loại người gọi
        """Các mã KHÔNG có handler riêng (405, 400, 422…).

        Đường không phải API rơi về `exc.get_response()` — chính response
        mặc định của Werkzeug, tức đúng hành vi trước bản này. KHÔNG `raise
        exc` ở đây: một ngoại lệ ném ra từ trong error handler không quay
        lại danh sách handler, nó đi thẳng lên `handle_exception` và (khi
        `PROPAGATE_EXCEPTIONS` bật, như trong test) nổ ra ngoài — biến một
        405 bình thường thành một lỗi không bắt được.
        """
        if not request.path.startswith("/api/"):
            return exc.get_response()
        return _error_response(
            code=_API_STATUS_CODES.get(exc.code,
                                       mutation_guard.VALIDATION_ERROR),
            message=(exc.description or "Yêu cầu không thực hiện được."),
            status=exc.code or 500)

    @app.errorhandler(RequestEntityTooLarge)
    def _too_large(_exc):
        return _error_response(
            code=mutation_guard.VALIDATION_ERROR,
            message=("Workbook vượt quá giới hạn 25MB cho bản Beta. Hãy "
                     "chọn file nhỏ hơn."),
            status=413)

    @app.errorhandler(404)
    def _not_found(_exc):
        return _error_response(
            code=mutation_guard.NOT_FOUND,
            message="Không tìm thấy tài nguyên yêu cầu.", status=404)

    @app.errorhandler(500)
    def _server_error(_exc):
        """500 KHÔNG bao giờ nói ra nội dung exception.

        Câu chữ là một hằng số, không phải `str(exc)`: một exception của
        SQLAlchemy mang cả câu SQL và DSN (gồm mật khẩu) trong `str()` của
        nó. Truy vết đi qua `trace_id` trong response và dòng log cùng mã
        — đó là đường đúng để nối một lỗi người dùng thấy với nguyên nhân
        trong log.
        """
        return _error_response(
            code=mutation_guard.INTERNAL_ERROR,
            message="Có lỗi xử lý phía máy chủ. Vui lòng thử lại.",
            status=500)

    @app.errorhandler(409)
    def _history_source_conflict(exc):
        """Mâu thuẫn nguồn lịch sử — nói ĐÚNG cái đang mâu thuẫn."""
        return _error_response(
            code=mutation_guard.REVISION_CONFLICT,
            message=(getattr(exc, "description", None)
                     or "Nguồn lịch sử đang mâu thuẫn."), status=409)

    @app.errorhandler(503)
    def _storage_unavailable(_exc):
        return _error_response(
            code=mutation_guard.SOURCE_PENDING,
            message="Lưu trữ tạm thời không khả dụng. Vui lòng thử lại.",
            status=503)

    # --- `STAB-01`: đo và truy vết thời gian ---------------------------
    #
    # Đặt CUỐI `create_app` để hai `after_request` hook không cần biết thứ
    # tự đăng ký của nhau: Flask chạy `after_request` theo thứ tự NGƯỢC lại
    # thứ tự đăng ký, nên hook đăng ký cuối cùng chạy TRƯỚC — và cái ta
    # muốn là đo được cả những gì hook khác làm với response.
    #
    # `install_sql_counter` gắn vào đúng `Engine` mà app này dùng. Không có
    # snapshot repo (môi trường chưa cấu hình database) thì không có SQL để
    # đếm, và hàm tự im lặng.
    if snapshot_repo is not None:
        request_timing.install_sql_counter(snapshot_repo.engine)

    # Chia đôi thời gian của một route bằng đúng cái mốc mà nó tự nhiên có:
    # trước khi Jinja bắt đầu render, mọi thứ route làm là DỰNG view model
    # (`presentation`); từ mốc đó tới khi render xong là `template`. Đo bằng
    # signal của Flask nên không route nào phải tự bọc mã đo — và vì thế
    # không route nào có thể quên.
    #
    # Template lồng nhau (`{% include %}`, `{% import %}`) KHÔNG phát signal
    # này, chỉ template cấp cao nhất phát — nên `template` không bị cộng
    # trùng.
    from flask import before_render_template, template_rendered

    @before_render_template.connect_via(app)
    def _mark_render_start(_sender, **_extra):
        """`P2-5` — `presentation` là thời gian RIÊNG, không phải tổng đã trôi.

        Bản trước cộng "toàn bộ thời gian tới lúc bắt đầu render", tức nó
        BAO GỒM cả `sql`, `r2` và `tracking`. Trong `Server-Timing` nó hiện
        như một cột song song với những cột kia, nên dễ đọc thành các khoản
        riêng — và phép đo 5.000 dòng cho thấy `pres 437,2 + tpl 793,9 =
        1231 > total 1114`, một tổng lớn hơn cả tổng.

        Nay trừ đi các span I/O đã đo, nên `presentation` là thời gian CPU
        dựng view model và `pres + tpl + sql + r2 + tracking ≤ total`.
        `tests/test_p2_5_timing_spans.py` canh chính bất đẳng thức đó.
        """
        data = request_timing.snapshot()
        if data:
            spans = data["spans"]
            already = (spans["presentation"] + spans["sql"] + spans["r2"]
                       + spans["tracking"] + spans["template"])
            request_timing.add("presentation",
                               max(0.0, data["total"] - already), count=1)
            g._render_started = time.monotonic()

    @template_rendered.connect_via(app)
    def _mark_render_end(_sender, **_extra):
        started = getattr(g, "_render_started", None)
        if started is not None:
            request_timing.add("template", time.monotonic() - started)
            g._render_started = None

    @app.after_request
    def _emit_timing(response):
        """Gắn `X-Request-Id` + `Server-Timing` và ghi MỘT dòng log.

        `response.calculate_content_length()` chỉ đọc được độ dài khi
        response không phải streaming (`direct_passthrough`) — file Excel
        tải về đi đường đó, và ép đọc độ dài của nó sẽ nạp cả file vào bộ
        nhớ. Nên bytes ở đó là `None`, và dòng log ghi `-` thay vì một số
        bịa ra.
        """
        size = None
        if not response.direct_passthrough:
            try:
                size = response.calculate_content_length()
            except Exception:  # noqa: BLE001 — đo lường không được làm sập
                size = None
        data = request_timing.snapshot(response_bytes=size)
        if not data:
            return response
        # `P1-2` — trả về `trace_id` do SERVER sinh, KHÔNG phải chuỗi
        # client gửi. Trả lại chuỗi của client sẽ làm mọi công cụ tin rằng
        # server đã chấp nhận nó làm mã truy vết.
        response.headers[request_timing.REQUEST_ID_HEADER] = data["trace_id"]
        response.headers["Server-Timing"] = \
            request_timing.server_timing_header(data)
        # `print` chứ không `logging`: gunicorn trên Render gom stdout của
        # worker vào log của service, và một dòng ở đó là chỗ Owner đọc
        # được ngay. Không thêm một cấu hình logging thứ hai vào hệ.
        line = request_timing.log_line(
            data, method=request.method, path=request.path,
            status=response.status_code)
        if data["total"] >= request_timing.SLOW_REQUEST_SECONDS:
            line += " slow=1"
        print(line, flush=True)
        return response

    return app
