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

Trust boundary: browser chỉ gửi workbook + lựa chọn feedback; browser không
bao giờ nhận secret, raw Tracking payload, hay đường dẫn filesystem tuyệt đối.
Download chỉ được resolve từ ``run_id`` qua registry do chính server tạo.
"""

from __future__ import annotations

import tempfile
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from flask import Flask, abort, redirect, render_template, request, send_file, url_for
from werkzeug.exceptions import RequestEntityTooLarge

from app import beta_feedback, beta_telemetry
from app.beta_presentation import REASON_DISPLAY_LABELS
from app.owner_usability import (
    OwnerUsabilityError, run_owner_report, select_latest_valid_captures,
)
from app.owner_usability import SelectedCaptures
from app.web import run_registry
from tools.tracking import live_pull

REPO_ROOT = Path(__file__).resolve().parents[2]
UPLOAD_DIR = REPO_ROOT / "data" / "uploads"
ARTIFACT_DIR = (REPO_ROOT / "outputs" / "reports").resolve()
TRACKING_TEMP_DIR = REPO_ROOT / "data" / "tracking_live_tmp"

# Beta technical safety limit — không phải quyết định nghiệp vụ của Owner.
# Workbook kế toán thật (mẫu đã audit) nằm dưới vài MB; 25MB để dư biên độ.
MAX_UPLOAD_BYTES = 25 * 1024 * 1024

HISTORY_PAGE_LIMIT = 50


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


def create_app(*, db_path: Path = run_registry.DEFAULT_DB_PATH) -> Flask:
    app = Flask(__name__)
    app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES
    registry = run_registry.RunRegistry(db_path=db_path)
    app.config["RUN_REGISTRY"] = registry

    def _page(*, error: Optional[str] = None, run_id: Optional[str] = None,
             not_found: bool = False, feedback_ok: bool = False, status: int = 200):
        record = registry.get_run(run_id) if run_id else None
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
            feedback_categories=beta_feedback.FEEDBACK_CATEGORIES,
        ), status

    @app.get("/")
    def index():
        run_id = request.args.get("run_id") or None
        found = run_id is not None and registry.get_run(run_id) is not None
        return _page(
            run_id=run_id if found else None,
            not_found=run_id is not None and not found,
            feedback_ok=request.args.get("feedback") == "ok",
        )

    @app.get("/history")
    def history():
        runs = registry.list_runs(limit=HISTORY_PAGE_LIMIT)
        return render_template("history.html", runs=runs)

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
                return _page(
                    error=(
                        "Không lấy được dữ liệu Tracking trực tiếp (nguồn: "
                        f"{exc.node}). Đây KHÔNG phải lỗi của workbook — vui "
                        "lòng thử lại sau."
                    ),
                    status=503,
                )
            try:
                owner_run = run_owner_report(sales=temp_path, captures=captures)
            except OwnerUsabilityError as exc:
                return _page(error=str(exc), status=400)
            except Exception:
                return _page(
                    error="Không thể tạo báo cáo. Kiểm tra workbook và thử lại.",
                    status=400,
                )
        finally:
            temp_path.unlink(missing_ok=True)
            if live_handle is not None:
                live_handle.cleanup()

        duration_ms = int((time.monotonic() - started) * 1000)
        summary = owner_run.demo_run.summary
        dropped_lines = len(owner_run.demo_run.result.unmapped_lines)
        run_id = owner_run.output_path.stem
        artifact_path = owner_run.output_path.relative_to(ARTIFACT_DIR)
        try:
            registry.create_run(
                run_id=run_id,
                created_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
                status=run_registry.STATUS_COMPLETE,
                workbook_display_name=display_name,
                artifact_path=str(artifact_path),
                view=_build_view(summary, dropped_lines=dropped_lines),
                tracking_evidence=tracking_evidence,
            )
        except Exception:
            # Report ĐÃ được tạo trên đĩa, nhưng không ghi được vào registry
            # (vd: storage lỗi) — không được trả về như thể mọi thứ thành
            # công (không có run_id để Owner tra lại). Fail rõ, không giả.
            return _page(
                error=(
                    "Báo cáo đã tạo nhưng không lưu được vào lịch sử run. "
                    "Vui lòng thử lại."
                ),
                status=500,
            )
        _record_telemetry(run_id, summary, duration_ms)
        # Post-Redirect-Get: tránh chạy lại báo cáo khi Owner bấm refresh.
        return redirect(url_for("index", run_id=run_id))

    @app.get("/artifact/<run_id>")
    def download_artifact(run_id: str):
        record = registry.get_run(run_id)
        if record is None or not record.artifact_path:
            abort(404)
        # `artifact_path` được lưu dạng tương đối, luôn được join lại dưới
        # ARTIFACT_DIR ở đây — không bao giờ tin một đường dẫn tuyệt đối từ
        # registry lẫn từ browser (chống path traversal đằng nào cũng chặn).
        candidate = (ARTIFACT_DIR / record.artifact_path).resolve()
        try:
            candidate.relative_to(ARTIFACT_DIR)
        except ValueError:
            abort(404)
        if not candidate.is_file():
            abort(404)
        return send_file(candidate, as_attachment=True, download_name=candidate.name)

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

    return app
