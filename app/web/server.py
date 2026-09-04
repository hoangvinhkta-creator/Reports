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

import os
import time
import uuid
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from flask import Flask, abort, redirect, render_template, request, url_for
from werkzeug.exceptions import HTTPException, RequestEntityTooLarge

from app import beta_feedback, beta_telemetry
from app.beta_presentation import REASON_DISPLAY_LABELS
from app.legacy import LegacyImportError, parse_workbook
from app.owner_usability import (
    OwnerUsabilityError, run_owner_report, select_latest_valid_captures,
)
from app.owner_usability import SelectedCaptures
from app.history import coverage as history_coverage
from app.history import models as history_models
from app.web import (
    analytics_presentation, analytics_queries, history_store, history_writer,
    legacy_presentation, run_registry, sales_presentation, sales_queries,
    storage_backend,
)
import tools.db as history_db
from tools.db import HistoryConfigurationError
from tools.storage.errors import CorruptRunRecordError, StorageUnavailableError
from tools.tracking import live_pull

REPO_ROOT = Path(__file__).resolve().parents[2]

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

LEGACY_IMPORT_PAGE_LIMIT = 50


def _guarded(fn, *args, **kwargs):
    """Gọi ``fn`` (một lời gọi store) và biến lỗi storage (R2 unavailable/
    JSON hỏng) thành HTTP 503 rõ ràng — KHÔNG âm thầm coi như "không tìm
    thấy"/"lịch sử rỗng" (S071B: phải phân biệt lỗi storage với dữ liệu
    thật sự rỗng)."""
    try:
        return fn(*args, **kwargs)
    except (StorageUnavailableError, CorruptRunRecordError,
            history_store.HistoryUnavailableError):
        abort(503)


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
        # PHB-01 — đếm theo KHOÁ inv.map, tức số lần Owner phải bấm ở màn phân
        # loại bên Tracking; chi tiết nằm ở sheet "Chưa định danh" của file.
        "unresolved_descriptions": summary.unresolved_description_count,
    }


def _tracking_unavailable_message(exc: "live_pull.TrackingUnavailableError") -> str:
    """PHB-01/D1 — nói ĐÚNG loại sự cố, và nói rõ nó KHÔNG phải kết luận nghiệp vụ.

    Node `inv_map` là authority định danh sản phẩm. Khi nó hỏng, thứ người vận
    hành nhìn thấy nếu ta cứ chạy tiếp sẽ là "mọi mặt hàng chưa được phân
    loại" — một câu sai, và sai theo hướng khiến họ đi phân loại lại những thứ
    đã phân loại xong. Nên nhánh này có câu RIÊNG, không dùng chung câu với hai
    node giá (QUY-CHUAN.md L3 của Tracking: mỗi nguyên nhân một câu khác nhau,
    không thì ảnh chụp màn hình của người dùng trở nên vô dụng).

    Không in `exc.reason` ra màn hình: nó chở nguyên văn thông điệp lỗi tầng
    dưới (URL, tên node, mã HTTP). Người vận hành cần biết PHẢI LÀM GÌ; chi
    tiết chẩn đoán đã nằm trong log.
    """
    if exc.node == "inv_map":
        return (
            "Không đọc được bảng phân loại sản phẩm (inv.map) từ Tracking — "
            "authority định danh đang KHÔNG khả dụng. Báo cáo đã dừng có chủ "
            "đích: chạy tiếp sẽ hiện mọi mặt hàng như 'chưa được phân loại', "
            "trong khi thật ra chỉ là không lấy được dữ liệu. Đây KHÔNG phải "
            "lỗi của workbook. Kiểm tra Tracking rồi chạy lại."
        )
    return (
        f"Không lấy được dữ liệu Tracking trực tiếp (nguồn: {exc.node}). "
        "Đây KHÔNG phải lỗi của workbook — vui lòng thử lại sau."
    )


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


def _select_captures_for_run() -> tuple[Optional[SelectedCaptures], Optional[dict], Optional[live_pull.LiveSelectedCaptures]]:
    """Trả về ``(captures, tracking_evidence, live_handle)``.

    ``live_handle`` khác ``None`` khi captures đến từ live pull — caller phải
    gọi ``live_handle.cleanup()`` sau khi dùng xong (finally), bất kể thành
    công hay lỗi, để không giữ authority thô của Tracking lâu hơn một lần
    chạy trên đĩa máy chủ (S071 §10).
    """
    if not live_pull.is_configured():
        return None, None, None
    live = live_pull.pull_live_captures(out_dir=TRACKING_TEMP_DIR)
    captures = SelectedCaptures(
        tracking_capture=live.tracking_capture,
        tracking_catalog=live.tracking_catalog,
        tracking_inv_map=live.tracking_inv_map,
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
    app.jinja_env.globals["LEGACY_BADGE"] = legacy_presentation.ORIGIN_BADGE
    app.jinja_env.globals["LEGACY_BADGE_TITLE"] = legacy_presentation.ORIGIN_TITLE
    app.jinja_env.globals["PIPELINE_BADGE"] = analytics_presentation.ORIGIN_BADGE
    app.jinja_env.globals["PIPELINE_BADGE_TITLE"] = analytics_presentation.ORIGIN_TITLE
    app.jinja_env.globals["QUANTITY_NOTE"] = analytics_presentation.QUANTITY_NOTE
    app.jinja_env.globals["ORDER_COLUMN_NOTE"] = analytics_presentation.ORDER_COLUMN_NOTE
    app.jinja_env.globals["BOTH_SOURCES_NOTE"] = analytics_presentation.BOTH_SOURCES_NOTE
    for _name in ("MULTI_DATE_NOTE", "MULTI_EMPLOYEE_NOTE", "NO_ORDERS_NOTE",
                  "PRODUCT_GROUPING_NOTE", "PRODUCT_ITEM_COUNT_LABEL",
                  "PRODUCT_ORDER_COUNT_NOTE", "REASON_LABEL"):
        app.jinja_env.globals[_name] = getattr(sales_presentation, _name)

    def _require_history() -> history_store.LegacyRepository:
        if history_repo is None:
            # Không phải "chưa có dữ liệu" — là chưa có nơi lưu dữ liệu.
            abort(503)
        return history_repo

    def _legacy_page(template: str, **context):
        return render_template(
            template,
            history_configured=history_repo is not None,
            legacy_import=_guarded(history_repo.current_import) if history_repo else None,
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
    def index():
        run_id = request.args.get("run_id") or None
        found = run_id is not None and _guarded(store.get_run, run_id) is not None
        return _page(
            run_id=run_id if found else None,
            not_found=run_id is not None and not found,
            feedback_ok=request.args.get("feedback") == "ok",
        )

    @app.get("/du-lieu")
    def data_tab():
        """Tab "Dữ liệu": các lần chạy pipeline VÀ các bản nhập legacy.

        Hai origin nằm trong hai bảng tách biệt trên trang, mỗi bảng ghi rõ
        nguồn — không bao giờ trộn số pipeline với số cũ vào một danh sách.
        """
        runs = _guarded(store.list_runs, limit=HISTORY_PAGE_LIMIT)
        imports = (
            _guarded(history_repo.list_imports, limit=LEGACY_IMPORT_PAGE_LIMIT)
            if history_repo else []
        )
        snapshots, runs_with_snapshot = [], set()
        if snapshot_repo is not None:
            snapshots = _guarded(snapshot_repo.list_snapshots, limit=SNAPSHOT_PAGE_LIMIT)
            # Một run có trên store mà KHÔNG có snapshot nghĩa là lần ghi lịch
            # sử đó đã hỏng. Trang phải nói ra, không im lặng bỏ qua.
            runs_with_snapshot = _guarded(
                snapshot_repo.run_ids_with_snapshot, [run.run_id for run in runs],
            )
        return _legacy_page(
            "du_lieu.html", runs=runs, imports=imports, snapshots=snapshots,
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
        repository = _require_history()
        upload = request.files.get("workbook")
        if upload is None or not upload.filename:
            return redirect(url_for("data_tab", loi="Hãy chọn workbook legacy .xlsx."))
        if not upload.filename.lower().endswith(".xlsx"):
            return redirect(url_for("data_tab", loi="Chỉ chấp nhận file .xlsx."))

        UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
        # Tên file lưu trên đĩa LUÔN do server sinh — tên client gửi lên chỉ
        # dùng để hiển thị, nên không có chuỗi đường dẫn nào của client chạm
        # tới filesystem (chống path traversal).
        temp_path = UPLOAD_DIR / f"{uuid.uuid4().hex}.xlsx"
        upload.save(temp_path)
        try:
            workbook = parse_workbook(temp_path)
            workbook = replace(
                workbook, source_file_name=_safe_display_name(upload.filename),
            )
            result = _guarded(
                repository.create_import, workbook,
                version_label=(request.form.get("version_label") or "").strip()[:120],
            )
        except LegacyImportError as exc:
            return redirect(url_for("data_tab", loi=str(exc)))
        except HTTPException:
            # `_guarded` biến lỗi history store thành abort(503) — mà abort
            # ném HTTPException. Không cho `except Exception` bên dưới nuốt
            # nó, nếu không sự cố DB sẽ hiện ra thành "không đọc được
            # workbook": đổ lỗi cho file của Owner vì một lỗi hạ tầng, và
            # phá đúng CHECK-PRA001-06 (FIND-PRA001-R02).
            raise
        except Exception:
            return redirect(url_for(
                "data_tab",
                loi="Không đọc được workbook legacy. Kiểm tra file và thử lại.",
            ))
        finally:
            # Workbook cũ chứa dữ liệu kinh doanh: không giữ lại trên đĩa
            # máy chủ quá một lần import, kể cả khi import lỗi.
            temp_path.unlink(missing_ok=True)
        message = (
            f"Đã nhập bản legacy {result.import_id}." if result.created
            else f"File này đã được nhập trước đó ({result.import_id}) — không tạo bản mới."
        )
        return redirect(url_for("data_tab", imported=message))

    @app.post("/du-lieu/legacy/<import_id>/chon")
    def choose_legacy(import_id: str):
        repository = _require_history()
        try:
            _guarded(repository.set_current, import_id)
        except KeyError:
            abort(404)
        return redirect(url_for("data_tab", imported=f"Đang xem bản {import_id}."))

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
        try:
            try:
                captures, tracking_evidence, live_handle = _select_captures_for_run()
            except live_pull.TrackingUnavailableError as exc:
                return _page(error=_tracking_unavailable_message(exc), status=503)
            try:
                owner_run = run_owner_report(sales=temp_path, captures=captures)
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

    @app.errorhandler(503)
    def _storage_unavailable(_exc):
        return _page(
            error="Lưu trữ tạm thời không khả dụng. Vui lòng thử lại.", status=503,
        )

    return app
