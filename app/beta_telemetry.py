"""Beta telemetry cục bộ — S069: ghi aggregate evidence mỗi lần chạy thành công.

Chỉ đọc từ ``ReportSummary`` (đã authoritative). Không đọc lại workbook, không
tính lại số, không lưu bất kỳ trường nghiệp vụ nào (khách hàng, mã sản phẩm,
giá, doanh thu, payload Tracking). Ghi JSONL append-only cục bộ, không mạng.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.modules.exporting.excel_exporter import ReportSummary

REPO_ROOT = Path(__file__).resolve().parents[1]
TELEMETRY_LOG_PATH = REPO_ROOT / "data" / "beta_feedback" / "runs.jsonl"


@dataclass(frozen=True)
class RunTelemetryRecord:
    run_id: str
    timestamp: str
    app_version: Optional[str]
    order_count: int
    line_count: int
    auto_orders: int
    review_orders: int
    error_count: int
    accounting_rate: float
    review_reason_counts: dict[str, int]
    processing_duration_ms: Optional[int]


def _git_sha(repo_root: Path) -> Optional[str]:
    """Best-effort; không dừng luồng Owner nếu không đọc được."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repo_root, capture_output=True, text=True, timeout=2, check=True,
        )
        return result.stdout.strip() or None
    except Exception:
        return None


def build_run_record(
    *,
    run_id: str,
    summary: ReportSummary,
    processing_duration_ms: Optional[int] = None,
    repo_root: Path = REPO_ROOT,
    now: Optional[datetime] = None,
) -> RunTelemetryRecord:
    """Dựng record chỉ từ ``ReportSummary`` — không nguồn nào khác."""
    moment = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    return RunTelemetryRecord(
        run_id=run_id,
        timestamp=moment.isoformat(timespec="seconds"),
        app_version=_git_sha(repo_root),
        order_count=summary.input_orders,
        line_count=summary.total_lines,
        auto_orders=summary.auto_orders,
        review_orders=summary.review_orders,
        error_count=summary.error_count,
        accounting_rate=summary.order_accounting_rate,
        review_reason_counts=dict(summary.review_reason_counts),
        processing_duration_ms=processing_duration_ms,
    )


def record_run(
    record: RunTelemetryRecord, *, log_path: Path = TELEMETRY_LOG_PATH,
) -> Path:
    """Append một dòng JSON; không đọc, không viết lại các dòng cũ."""
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(record), ensure_ascii=False))
        handle.write("\n")
    return log_path
