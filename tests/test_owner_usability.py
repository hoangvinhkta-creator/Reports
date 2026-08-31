"""Luồng Owner chỉ chọn capture hợp lệ và ủy quyền nguyên Demo V1."""

from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace

import pytest

from app import owner_usability
from tests.test_105e_price_composition import write_history_capture
from tests.test_tracking_history_reader import CUTOVER, build_export


def write_catalog(path: Path, *, captured_at: datetime,
                  status: str = "COMPLETE") -> Path:
    payload = {
        "capture_id": f"catalog-{captured_at:%H%M%S}-{status}",
        "captured_at": captured_at.isoformat(),
        "captured_by": "test",
        "source_system_ref": "tracking/test",
        "content_hash": "test-catalog",
        "capture_status": status,
        "rows": [],
    }
    if status == "FAILED":
        payload["failure_reason"] = "capture failed"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def add_valid_captures(repo: Path, *, history_at: datetime,
                       catalog_at: datetime) -> tuple[Path, Path]:
    history_dir = repo / "data" / "captures"
    catalog_dir = repo / "data" / "tracking_catalog"
    history_dir.mkdir(parents=True)
    catalog_dir.mkdir(parents=True)
    history_source = write_history_capture(
        repo,
        build_export(prices={"A1": 7000}),
        captured_at=history_at,
    )
    history = history_dir / "history.json"
    history_source.replace(history)
    catalog = write_catalog(catalog_dir / "catalog.json", captured_at=catalog_at)
    return history, catalog


def test_selects_latest_complete_capture_by_metadata_not_filename_or_mtime(tmp_path):
    older_history, catalog = add_valid_captures(
        tmp_path,
        history_at=CUTOVER + timedelta(days=1),
        catalog_at=datetime(2026, 9, 1, tzinfo=timezone.utc),
    )
    newer_history_source = write_history_capture(
        tmp_path,
        build_export(prices={"A1": 7000}),
        captured_at=CUTOVER + timedelta(days=2),
        capture_id="newest-by-metadata",
    )
    newer_history = tmp_path / "data" / "tracking_price_history" / "older-name.json"
    newer_history.parent.mkdir(parents=True)
    newer_history_source.replace(newer_history)
    # Mtime ngược lại không được dùng để chọn capture.
    os.utime(older_history, (older_history.stat().st_atime, datetime.now().timestamp()))

    selected = owner_usability.select_latest_valid_captures(repo_root=tmp_path)

    assert selected.tracking_capture == newer_history
    assert selected.tracking_catalog == catalog


def test_failed_capture_is_rejected_even_when_its_metadata_is_newer(tmp_path):
    valid_history, valid_catalog = add_valid_captures(
        tmp_path,
        history_at=CUTOVER + timedelta(days=1),
        catalog_at=datetime(2026, 9, 1, tzinfo=timezone.utc),
    )
    failed = tmp_path / "data" / "captures" / "newest.json"
    write_history_capture(
        failed.parent,
        build_export(prices={"A1": 7000}),
        captured_at=CUTOVER + timedelta(days=5),
        capture_status="FAILED",
        failure_reason="network failure",
    ).replace(failed)
    failed_catalog = tmp_path / "data" / "tracking_catalog" / "newest.json"
    write_catalog(
        failed_catalog,
        captured_at=datetime(2026, 9, 5, tzinfo=timezone.utc),
        status="FAILED",
    )

    selected = owner_usability.select_latest_valid_captures(repo_root=tmp_path)

    assert selected.tracking_capture == valid_history
    assert selected.tracking_catalog == valid_catalog


def test_no_complete_capture_has_an_actionable_failure(tmp_path):
    with pytest.raises(owner_usability.OwnerUsabilityError, match="capture.*COMPLETE"):
        owner_usability.select_latest_valid_captures(repo_root=tmp_path)


def test_owner_run_delegates_to_demo_generates_new_output_and_preserves_sales(
    tmp_path, monkeypatch
):
    history, catalog = add_valid_captures(
        tmp_path,
        history_at=CUTOVER + timedelta(days=1),
        catalog_at=datetime(2026, 9, 1, tzinfo=timezone.utc),
    )
    sales = tmp_path / "accounting.xlsx"
    sales.write_bytes(b"original workbook bytes")
    called = {}

    def fake_run_demo(**kwargs):
        called.update(kwargs)
        kwargs["output"].write_bytes(b"new report")
        return SimpleNamespace(
            output_path=kwargs["output"],
            summary=SimpleNamespace(
                input_orders=3, accounted_orders=3, auto_orders=1, review_orders=2
            ),
        )

    monkeypatch.setattr(owner_usability.demo, "run_demo", fake_run_demo)
    owner_run = owner_usability.run_owner_report(
        sales=sales,
        repo_root=tmp_path,
        now=datetime(2026, 9, 2, 3, 4, 5, tzinfo=timezone.utc),
    )

    assert called["sales"] == sales.resolve()
    assert called["tracking_capture"] == history
    assert called["tracking_catalog"] == catalog
    assert owner_run.output_path == tmp_path / "outputs" / "reports" / "report-20260902T030405Z.xlsx"
    assert owner_run.output_path.read_bytes() == b"new report"
    assert sales.read_bytes() == b"original workbook bytes"
    assert owner_run.demo_run.summary.input_orders == owner_run.demo_run.summary.accounted_orders
