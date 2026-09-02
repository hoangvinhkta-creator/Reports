"""Điều phối MỘT đơn vị công việc: một lần chạy pipeline → lịch sử + R2.

Module này là chỗ duy nhất nối ba thứ lại: kết quả pipeline authoritative
(``DemoRun``), tầng reconcile thuần (``app/history``), và tầng lưu
(``SnapshotRepository`` + ``RunStore``). Nó KHÔNG quyết định business rule
nào — mọi con số nó ghi đều đến từ engine, và mọi quyết định
INSERT/SAME/SOURCE_CHANGED/COLLISION đều đến từ ``app/history/reconciler``.

Fail-closed là hợp đồng (TASK-PRA-002 mục 11–12): lịch sử ghi hỏng thì cả lần
chạy được coi là KHÔNG hoàn tất — không có run "thành công" mà không có
snapshot, và không có snapshot trỏ tới một artifact chưa lưu được.
"""

from __future__ import annotations

import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from app.history import coverage as history_coverage
from app.history import extraction
from app.web import history_store

# Đọc một lần cho cả tiến trình: danh tính master nhân viên dẫn xuất từ NỘI
# DUNG file config, nên nó không đổi giữa hai lần chạy cùng một deploy.
_EMPLOYEE_MASTER_SNAPSHOT_ID: list = []

REPO_ROOT = Path(__file__).resolve().parents[2]


def file_fingerprint(path: Path) -> str:
    """sha256 của CHÍNH bytes workbook đã upload — không phải của nội dung đã parse.

    Dùng để nhận ra "đúng file này đã chạy rồi" (``duplicate_of_snapshot_id``).
    Đọc theo khối để không nạp cả file vào RAM (mục 19).
    """
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def scan_workbook(path: Path) -> tuple[Optional[str], int, int]:
    """Header A2 + số dòng dữ liệu + số dòng thiếu Số BH; lỗi đọc → không đoán."""
    try:
        return history_coverage.scan_sheet(path)
    except Exception:
        # Một workbook đã chạy pipeline thành công mà không đọc lại được header
        # là chuyện lạ nhưng KHÔNG được làm hỏng lần chạy đó. Trả về "không
        # biết" và để coverage rơi về DETECTED_ONLY — trung thực, không đoán.
        return None, 0, 0


def build_evidence(demo_run, tracking_evidence: Optional[dict]) -> dict:
    """Mọi định danh cần để MỞ LẠI lần chạy này — chỉ id/revision/hash.

    Không mirror payload nào của Tracking (ADR-107): thẩm quyền vẫn nằm ở
    Tracking, ở đây chỉ là con trỏ tới đúng bản đã dùng.
    """
    records = getattr(demo_run, "price_records", ()) or ()
    snapshot = getattr(records[0], "evidence", None) if records else None
    evidence = {
        "tracking_price_history_capture_id": _text(
            getattr(snapshot, "tracking_price_history_capture_id", None)),
        "tracking_price_history_captured_at": _text(
            getattr(snapshot, "tracking_price_history_captured_at", None)),
        "tracking_catalog_capture_id": _text(
            getattr(snapshot, "tracking_catalog_capture_id", None)),
        "tracking_inv_map_capture_id": _text(
            getattr(snapshot, "tracking_inv_map_capture_id", None)),
        "public_purchase_version_id": _text(
            getattr(snapshot, "public_purchase_version_id", None)),
        "public_purchase_content_hash": _text(
            getattr(snapshot, "public_purchase_content_hash", None)),
        "identity_store_revision": getattr(snapshot, "identity_store_revision", None),
        "business_timezone_label": _text(
            getattr(snapshot, "business_timezone_label", None)),
        "business_timezone_provenance": _text(
            getattr(snapshot, "business_timezone_provenance", None)),
        "vendor_price_source": _text(getattr(snapshot, "vendor_price_source", None)),
        "employee_master_snapshot_id": employee_master_snapshot_id(),
        "app_commit": os.environ.get("RENDER_GIT_COMMIT") or None,
        "tracking_evidence": tracking_evidence,
    }
    return evidence


def build_summary(summary) -> dict:
    return {
        "input_orders": summary.input_orders,
        "accounted_orders": summary.accounted_orders,
        "total_lines": summary.total_lines,
        "auto_orders": summary.auto_orders,
        "review_orders": summary.review_orders,
        "review_lines": summary.review_lines,
        "error_count": summary.error_count,
        "review_reason_counts": dict(summary.review_reason_counts),
    }


def employee_master_snapshot_id() -> Optional[str]:
    if not _EMPLOYEE_MASTER_SNAPSHOT_ID:
        _EMPLOYEE_MASTER_SNAPSHOT_ID.append(_load_employee_master_snapshot_id())
    return _EMPLOYEE_MASTER_SNAPSHOT_ID[0]


def _load_employee_master_snapshot_id() -> Optional[str]:
    try:
        from app.modules.mapping.employee_mapper import EmployeeMapper

        return EmployeeMapper.from_yaml(REPO_ROOT / "config" / "employees.yaml").snapshot_id
    except Exception:
        # Bằng chứng thiếu một định danh vẫn tốt hơn một định danh bịa ra.
        return None


def _text(value) -> Optional[str]:
    return None if value is None else str(value)


def write_run_history(
    repository: history_store.SnapshotRepository, *, demo_run, run_id: str,
    workbook_path: Path, display_name: str, tracking_evidence: Optional[dict] = None,
    on_persisted=None, created_at: Optional[str] = None,
) -> history_store.SnapshotWriteResult:
    """Ghi lịch sử của MỘT lần chạy. Ném ra ngoài khi hỏng — không nuốt lỗi."""
    presented = tuple(demo_run.presented_lines)
    source_lines = extraction.build_source_lines(presented)
    result_lines = extraction.build_result_lines(presented, source_lines)
    header_text, sheet_data_rows, rows_without_order_id = scan_workbook(workbook_path)
    return repository.write_snapshot(
        run_id=run_id,
        created_at=created_at or datetime.now(timezone.utc).isoformat(timespec="seconds"),
        source_file_name=display_name,
        file_fingerprint=file_fingerprint(workbook_path),
        file_size=workbook_path.stat().st_size,
        header_text=header_text, sheet_data_rows=sheet_data_rows,
        rows_without_order_id=rows_without_order_id,
        source_lines=source_lines, result_lines=result_lines,
        evidence=build_evidence(demo_run, tracking_evidence),
        summary=build_summary(demo_run.summary),
        on_persisted=on_persisted,
    )
