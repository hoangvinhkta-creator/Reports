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

import hashlib
import io
import os
import time
import uuid
from dataclasses import replace
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Optional
from zoneinfo import ZoneInfo

from flask import (
    Flask, abort, redirect, render_template, request, send_file, url_for,
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
    brand_metrics, business_metrics, contribution, line_type, reporting_sheets,
)
from app.modules.reporting.rate_routing import GIA_DUNG, gia_dung_workflow_applies
from app.modules.exporting import business_export
from app.modules.reporting import evaluation
from app.web import evaluation_presentation
from app.web import (
    analytics_presentation, analytics_queries, brand_identity,
    business_presentation, business_service, business_store, history_store,
    history_writer, identity_gateway, legacy_presentation, legacy_reference,
    line_identity, period_lock, revenue_timeline, run_registry,
    sales_presentation, sales_queries, storage_backend, workspace_presentation,
)
import tools.db as history_db
from tools.db import HistoryConfigurationError
from tools.storage.errors import CorruptRunRecordError, StorageUnavailableError
from tools.tracking import live_pull

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

        Không hiển thị PII: bảng cờ chỉ mang khoá đơn/dòng, loại cờ và các
        trường nghiệp vụ đã đổi — tên/SĐT/địa chỉ khách không có mặt trong bất
        kỳ bảng nào của PRA-002 nên cũng không có đường nào ra tới đây.
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
            "snapshot.html", snapshot=snapshot, flags=flags, totals=totals,
            coverage_label=history_coverage.coverage_label(snapshot["coverage_state"]),
            can_confirm=snapshot["coverage_state"] != history_models.CONFIRMED_COMPLETE,
            confirm_message=message, confirm_error=error,
        ), status

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
            xac_nhan=(
                f"Đã ghi nhận xác nhận đầy đủ cho {confirmation.confirmed_range_start} "
                f"→ {confirmation.confirmed_range_end}. "
                f"{confirmation.removed_candidates} dòng hiện hành trong khoảng này không "
                "có trong sổ vừa xác nhận — đã đưa vào Review, KHÔNG xoá và VẪN tính."
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
        if granularity in (revenue_timeline.DAY, revenue_timeline.WEEK):
            legacy_days = _legacy_daily_rows(
                [(item["year"], item["month"]) for item in legacy_months])
        points = revenue_timeline.series(
            data.details, granularity=granularity,
            legacy_months=legacy_months, legacy_days=legacy_days)
        # `TASK-OWNER-UIUX-003` §2 — `series()` ở trên vẫn tính TOÀN BỘ điểm
        # (bất biến Σ = totals và mọi kiểm chứng origin không đổi); chỉ phần
        # VẼ được khoanh lại quanh kỳ đang chọn ở ba mức mịn nhất, để "Ngày"
        # không dàn trải hết lịch sử thành một hàng chấm không đọc nổi.
        points = revenue_timeline.window_points(
            points, granularity=granularity, period=view["period"])
        return business_presentation.revenue_chart(
            points, granularity=granularity,
            has_legacy_months=bool(legacy_months),
            undated=revenue_timeline.undated_count(data.details),
            window_label=revenue_timeline.window_label(
                granularity, view["period"]),
            period=view["period"])

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

    def _workspace_period() -> tuple[int, int]:
        """Tháng đang xem của không gian làm việc. LUÔN là một tháng thật.

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
        raw = request.values.get("ky") or ""
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

    def _workspace_view() -> dict:
        """Mọi thứ một màn hình không gian làm việc cần, đọc đúng một lần."""
        service = _require_business()
        period = _workspace_period()
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
            return load_tracking_catalog_capture(captures.tracking_catalog)
        except Exception:  # noqa: BLE001 — danh mục hỏng = "chưa đọc được"
            return None
        finally:
            if live is not None:
                live.cleanup()

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
        # Phạm vi THẬT của lần xác nhận này: mọi dòng của kỳ dùng chung khoá
        # định danh, không riêng dòng vừa bấm (`INV-76`/`INV-87`).
        shared = [item for item in view["data"].details
                  if line_identity.identity_key_of(item.get("product_raw"))
                  == state.identity_key]
        return {
            **keys,
            "product_raw": detail["product_raw"] or "",
            "query": query,
            "candidates": [
                {"code": item.code, "label": item.label}
                for item in identity_gateway.candidates(snapshot, query=query)],
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
            return _workspace_redirect(loi=line_identity.UNCLASSIFIABLE_NOTE)
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
            return _workspace_redirect(loi=str(exc), **{
                "phan-loai": "1", "order_key": keys["order_key"],
                "product_key": keys["product_key"],
                "occurrence_index": keys["occurrence_index"]})
        except Exception as exc:  # noqa: BLE001 — xung đột version/log hỏng
            return _workspace_redirect(loi=(
                f"Chưa ghi được phân loại: {exc}"))
        if state.conflict:
            note = identity_gateway.CONFLICT_OK_NOTE
        elif state.out_of_catalog:
            note = identity_gateway.RELINK_OK_NOTE
        else:
            note = identity_gateway.CONFIRM_OK_NOTE
        return _workspace_redirect(**{"da-luu": note})

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
            return _workspace_redirect(loi=line_identity.UNCLASSIFIABLE_NOTE)
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
            return _workspace_redirect(loi=str(exc))
        except Exception as exc:  # noqa: BLE001 — xung đột version/log hỏng
            return _workspace_redirect(loi=(
                f"Chưa ghi được quyết định ngoài bảng giá: {exc}"))
        return _workspace_redirect(
            **{"da-luu": identity_gateway.OUT_OF_CATALOG_OK_NOTE})

    @app.get("/kinh-doanh/nhan-vien")
    def business_employee():
        """Không gian làm việc theo SHEET — `DEC-PHB02-08` §4/§5/§14/§22."""
        view = _workspace_view()
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

        return render_template(
            "kinh_doanh_nhan_vien.html",
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
            groups=workspace_presentation.sheet_detail_groups(
                scoped.details, sheet=sheet, decisions=decisions),
            detail_totals=workspace_presentation.sheet_detail_totals(
                scoped.details),
            # `§13`/`§PI-10` — ĐÚNG MỘT dòng cảnh báo cho cả sheet, hoặc
            # `None`. Không có khối thứ hai, không có trang thứ hai.
            identity_warning=line_identity.sheet_warning(
                scoped.details, decisions=decisions),
            identify=identify,
            unclassifiable_note=line_identity.UNCLASSIFIABLE_NOTE,
            excluded=workspace_presentation.excluded_rows(view["data"].excluded),
            assignable=business_presentation.assignable_employee_options(
                view["service"].assignable_employees()),
            editing=request.args.get("sua") or "",
            editing_target=bool(request.args.get("sua-target")),
            confirm=confirm,
            message=request.args.get("da-luu") or None,
            error=request.args.get("loi") or None,
        )

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

    @app.post("/kinh-doanh/nhan-vien/gia-nhap")
    def business_save_line_purchase_price():
        """`§28` — sửa Giá nhập ngay trong ô của dòng, khi BH đang mở sửa.

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
            return _workspace_redirect(**{"da-luu": (
                "Đã khôi phục dòng. Nó được tính lại vào báo cáo từ bây giờ.")})
        detail = service.detail_of(data=view["data"], **keys)
        if detail is None:
            abort(404)
        _guard_lines(service, detail)
        _guarded(service.store.exclude_line, **keys)
        return _workspace_redirect(**{"da-luu": (
            "Đã loại dòng này khỏi báo cáo. Sổ kế toán gốc giữ nguyên — bấm "
            "KHÔI PHỤC ở cuối trang là dòng trở lại.")})

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

        3. **Thương hiệu chỉ ĐỌC từ thẩm quyền Product Identity.** Nguồn được
           wire ở đây là `brand_identity.canonical_brand` và không gì khác —
           không bảng ánh xạ của Reports, không phép so chuỗi con (`BR-02`,
           `BR-10`).

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
            brand_source=brand_identity.canonical_brand)
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

            duration_ms = int((time.monotonic() - started) * 1000)
            summary = owner_run.demo_run.summary
            dropped_lines = len(owner_run.demo_run.result.unmapped_lines)
            run_id = owner_run.output_path.stem

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

    @app.errorhandler(RequestEntityTooLarge)
    def _too_large(_exc):
        return _page(
            error="Workbook vượt quá giới hạn 25MB cho bản Beta. Hãy chọn file nhỏ hơn.",
            status=413,
        )

    @app.errorhandler(404)
    def _not_found(_exc):
        return _page(error="Không tìm thấy tài nguyên yêu cầu.", status=404)

    @app.errorhandler(500)
    def _server_error(_exc):
        return _page(error="Có lỗi xử lý phía máy chủ. Vui lòng thử lại.", status=500)

    @app.errorhandler(409)
    def _history_source_conflict(exc):
        """Mâu thuẫn nguồn lịch sử — nói ĐÚNG cái đang mâu thuẫn."""
        return _page(error=getattr(exc, "description", None)
                     or "Nguồn lịch sử đang mâu thuẫn.", status=409)

    @app.errorhandler(503)
    def _storage_unavailable(_exc):
        return _page(
            error="Lưu trữ tạm thời không khả dụng. Vui lòng thử lại.", status=503,
        )

    return app
