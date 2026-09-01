"""Persistent run registry cho Reports Web Shared Beta (S071).

S070 giữ ``_RUNS: dict[str, dict]`` sống trong process — đúng cho một Owner
double-click cục bộ, nhưng sai cho Shared Online Beta: mất khi server
restart (S071 §14 đòi hỏi ngược lại) và không chia sẻ được giữa nhiều viewer/
nhiều worker process cùng phục vụ ``reports.tinphatcrm.com`` (S071 §15).

Module này thay ``_RUNS`` bằng một file SQLite trên đĩa persistent. Một file
DB nhiều tiến trình cùng đọc/ghi (WAL mode) là đủ cho quy mô Beta — một node,
một đội bán hàng nhỏ — và không thêm hạ tầng (Postgres/Redis) nào cả (S071
§8: ưu tiên giải pháp managed nhỏ nhất). Mỗi lời gọi mở một connection ngắn
hạn rồi đóng lại ngay — không giữ connection sống qua nhiều request, nên
nhiều worker/nhiều viewer đọc cùng một trạng thái "canonical" duy nhất, đúng
kiến trúc "REPORTS OWNS ONLY REPORTS STATE" (§9): registry, không phải bộ nhớ
riêng của từng tiến trình, là nguồn sự thật.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = REPO_ROOT / "data" / "web_runs" / "runs.db"

STATUS_COMPLETE = "COMPLETE"
STATUS_FAILED = "FAILED"
STATUS_TRACKING_UNAVAILABLE = "TRACKING_UNAVAILABLE"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    status TEXT NOT NULL,
    workbook_display_name TEXT,
    artifact_path TEXT,
    view_json TEXT,
    tracking_evidence_json TEXT,
    error_message TEXT
);
CREATE INDEX IF NOT EXISTS idx_runs_created_at ON runs (created_at DESC);
"""


@dataclass(frozen=True)
class RunRecord:
    run_id: str
    created_at: str
    status: str
    workbook_display_name: Optional[str]
    artifact_path: Optional[str]
    view: Optional[dict]
    tracking_evidence: Optional[dict]
    error_message: Optional[str]


class RunNotFoundError(LookupError):
    """``run_id`` không tồn tại trong registry — fail-safe 404, không đoán."""


class RunRegistry:
    """SQLite-backed run registry. An toàn cho nhiều tiến trình cùng dùng
    chung một file ``db_path`` (WAL + ``busy_timeout``, xem ``_connect``)."""

    def __init__(self, db_path: Path = DEFAULT_DB_PATH) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as conn:
            conn.executescript(_SCHEMA)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        conn = sqlite3.connect(str(self.db_path), timeout=30)
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=30000")
            yield conn
            conn.commit()
        finally:
            conn.close()

    def create_run(
        self,
        *,
        run_id: str,
        created_at: str,
        status: str,
        workbook_display_name: Optional[str] = None,
        artifact_path: Optional[str] = None,
        view: Optional[dict[str, Any]] = None,
        tracking_evidence: Optional[dict[str, Any]] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """Ghi một run mới. ``run_id`` phải duy nhất (PRIMARY KEY) — một
        run_id trùng là lỗi lập trình (server luôn sinh run_id mới), không
        phải một tình huống cần xử lý êm."""
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO runs (run_id, created_at, status, workbook_display_name, "
                "artifact_path, view_json, tracking_evidence_json, error_message) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    run_id,
                    created_at,
                    status,
                    workbook_display_name,
                    artifact_path,
                    json.dumps(view, ensure_ascii=False) if view is not None else None,
                    json.dumps(tracking_evidence, ensure_ascii=False)
                    if tracking_evidence is not None
                    else None,
                    error_message,
                ),
            )

    def get_run(self, run_id: str) -> Optional[RunRecord]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT run_id, created_at, status, workbook_display_name, "
                "artifact_path, view_json, tracking_evidence_json, error_message "
                "FROM runs WHERE run_id = ?",
                (run_id,),
            ).fetchone()
        return _row_to_record(row) if row is not None else None

    def list_runs(self, *, limit: int = 50) -> list[RunRecord]:
        """Mới nhất trước — dùng cho trang lịch sử (S071 §11)."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT run_id, created_at, status, workbook_display_name, "
                "artifact_path, view_json, tracking_evidence_json, error_message "
                "FROM runs ORDER BY created_at DESC, run_id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [_row_to_record(row) for row in rows]


def _row_to_record(row: tuple) -> RunRecord:
    (
        run_id, created_at, status, workbook_display_name, artifact_path,
        view_json, tracking_evidence_json, error_message,
    ) = row
    return RunRecord(
        run_id=run_id,
        created_at=created_at,
        status=status,
        workbook_display_name=workbook_display_name,
        artifact_path=artifact_path,
        view=json.loads(view_json) if view_json else None,
        tracking_evidence=json.loads(tracking_evidence_json) if tracking_evidence_json else None,
        error_message=error_message,
    )
