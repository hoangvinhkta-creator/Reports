"""S071 — Run registry persistent qua restart + đa tiến trình/viewer.

``RunRegistry`` thay ``_RUNS: dict`` process-local của S070. Test ở đây
chứng minh đúng hai acceptance criteria bắt buộc của S071: PERSISTENCE
(§14 — "restart" mô phỏng bằng việc mở một ``RunRegistry`` MỚI trỏ cùng
``db_path``) và MULTI-VIEWER (§15 — hai ``RunRegistry`` instance riêng biệt,
cùng đọc một run do cái kia ghi, không qua bất kỳ state process-local nào).
"""

from __future__ import annotations

import sqlite3
import threading

import pytest

from app.web import run_registry


def _make(tmp_path, name="runs.db"):
    return run_registry.RunRegistry(db_path=tmp_path / name)


def test_unknown_run_id_returns_none_not_an_exception(tmp_path):
    registry = _make(tmp_path)
    assert registry.get_run("does-not-exist") is None


def test_create_then_get_round_trips_all_fields(tmp_path):
    registry = _make(tmp_path)
    registry.create_run(
        run_id="run-a",
        created_at="2026-09-01T08:00:00+00:00",
        status=run_registry.STATUS_COMPLETE,
        workbook_display_name="So_ban_hang.xlsx",
        artifact_path="report-a.xlsx",
        view={"input_orders": 58, "auto_orders": 22},
        tracking_evidence={"catalog_capture_id": "LIVE-CAT-1"},
        error_message=None,
    )
    record = registry.get_run("run-a")
    assert record.run_id == "run-a"
    assert record.status == run_registry.STATUS_COMPLETE
    assert record.workbook_display_name == "So_ban_hang.xlsx"
    assert record.artifact_path == "report-a.xlsx"
    assert record.view == {"input_orders": 58, "auto_orders": 22}
    assert record.tracking_evidence == {"catalog_capture_id": "LIVE-CAT-1"}
    assert record.error_message is None


# --- PERSISTENCE ACROSS RESTART (S071 §14) ---------------------------------


def test_run_survives_reopening_the_registry_from_the_same_db_file(tmp_path):
    """Mô phỏng "restart application": đóng registry A, mở registry B MỚI
    trỏ cùng file — B phải thấy đúng run A đã ghi, không phụ thuộc bất kỳ
    object Python nào còn sống trong bộ nhớ."""
    db_path = tmp_path / "runs.db"
    registry_a = run_registry.RunRegistry(db_path=db_path)
    registry_a.create_run(
        run_id="run-persisted", created_at="2026-09-01T08:00:00+00:00",
        status=run_registry.STATUS_COMPLETE, artifact_path="report-persisted.xlsx",
        view={"input_orders": 10},
    )
    del registry_a  # không còn tham chiếu Python nào — chỉ file trên đĩa còn lại

    registry_b = run_registry.RunRegistry(db_path=db_path)
    record = registry_b.get_run("run-persisted")
    assert record is not None
    assert record.artifact_path == "report-persisted.xlsx"
    assert record.view == {"input_orders": 10}


def test_two_runs_persist_independently_and_history_lists_both(tmp_path):
    db_path = tmp_path / "runs.db"
    registry_a = run_registry.RunRegistry(db_path=db_path)
    registry_a.create_run(
        run_id="run-A", created_at="2026-09-01T08:00:00+00:00",
        status=run_registry.STATUS_COMPLETE, artifact_path="A.xlsx", view={"n": 1},
    )
    registry_a.create_run(
        run_id="run-B", created_at="2026-09-01T09:00:00+00:00",
        status=run_registry.STATUS_COMPLETE, artifact_path="B.xlsx", view={"n": 2},
    )
    del registry_a

    registry_b = run_registry.RunRegistry(db_path=db_path)
    runs = registry_b.list_runs(limit=10)
    run_ids = {r.run_id for r in runs}
    assert run_ids == {"run-A", "run-B"}
    # run-B (mới hơn) đứng trước run-A — mới nhất trước.
    assert [r.run_id for r in runs] == ["run-B", "run-A"]
    assert registry_b.get_run("run-A").artifact_path == "A.xlsx"
    assert registry_b.get_run("run-B").artifact_path == "B.xlsx"
    # Hai artifact khác nhau, mỗi run_id resolve đúng cái của nó.
    assert registry_b.get_run("run-A").artifact_path != registry_b.get_run("run-B").artifact_path


# --- MULTI-VIEWER (S071 §15) ------------------------------------------------


def test_a_second_independent_registry_instance_reads_the_same_run(tmp_path):
    """Viewer A tạo/đọc Run A qua registry instance của riêng nó; Viewer B
    (một ``RunRegistry`` instance khác, KHÔNG chia sẻ Python object nào với
    A) đọc đúng cùng Run A đã persist — không phụ thuộc session process-local
    của Viewer A."""
    db_path = tmp_path / "runs.db"
    viewer_a = run_registry.RunRegistry(db_path=db_path)
    viewer_a.create_run(
        run_id="run-shared", created_at="2026-09-01T08:00:00+00:00",
        status=run_registry.STATUS_COMPLETE, artifact_path="shared.xlsx",
        view={"input_orders": 58, "auto_orders": 22, "review_orders": 36},
    )

    viewer_b = run_registry.RunRegistry(db_path=db_path)
    seen_by_b = viewer_b.get_run("run-shared")
    assert seen_by_b is not None
    assert seen_by_b.view == {"input_orders": 58, "auto_orders": 22, "review_orders": 36}
    assert seen_by_b.artifact_path == "shared.xlsx"


def test_concurrent_reads_from_multiple_registry_instances_do_not_error(tmp_path):
    db_path = tmp_path / "runs.db"
    seed = run_registry.RunRegistry(db_path=db_path)
    for i in range(5):
        seed.create_run(
            run_id=f"run-{i}", created_at=f"2026-09-01T0{i}:00:00+00:00",
            status=run_registry.STATUS_COMPLETE, artifact_path=f"{i}.xlsx", view={"n": i},
        )

    errors: list[Exception] = []

    def _reader(reader_index: int) -> None:
        try:
            reg = run_registry.RunRegistry(db_path=db_path)
            for _ in range(20):
                reg.list_runs(limit=10)
                reg.get_run(f"run-{reader_index % 5}")
        except Exception as exc:  # pragma: no cover - failure path
            errors.append(exc)

    threads = [threading.Thread(target=_reader, args=(i,)) for i in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)

    assert errors == []


def test_concurrent_writes_from_multiple_registry_instances_all_land(tmp_path):
    """Mô phỏng nhiều upload/run song song (một hình thức multi-viewer khác):
    nhiều ``RunRegistry`` instance ghi đồng thời vào cùng file DB — WAL +
    busy_timeout phải hấp thụ tranh chấp, không mất run nào, không lỗi."""
    db_path = tmp_path / "runs.db"
    run_registry.RunRegistry(db_path=db_path)  # đảm bảo schema đã tạo trước

    errors: list[Exception] = []

    def _writer(index: int) -> None:
        try:
            reg = run_registry.RunRegistry(db_path=db_path)
            reg.create_run(
                run_id=f"concurrent-{index}",
                created_at=f"2026-09-01T10:00:{index:02d}+00:00",
                status=run_registry.STATUS_COMPLETE,
                artifact_path=f"concurrent-{index}.xlsx",
                view={"n": index},
            )
        except Exception as exc:  # pragma: no cover - failure path
            errors.append(exc)

    threads = [threading.Thread(target=_writer, args=(i,)) for i in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=10)

    assert errors == []
    final = run_registry.RunRegistry(db_path=db_path)
    run_ids = {r.run_id for r in final.list_runs(limit=50)}
    assert run_ids == {f"concurrent-{i}" for i in range(10)}


def test_duplicate_run_id_raises_instead_of_silently_overwriting(tmp_path):
    registry = _make(tmp_path)
    registry.create_run(
        run_id="dup", created_at="2026-09-01T08:00:00+00:00",
        status=run_registry.STATUS_COMPLETE, artifact_path="a.xlsx", view={},
    )
    with pytest.raises(sqlite3.IntegrityError):
        registry.create_run(
            run_id="dup", created_at="2026-09-01T09:00:00+00:00",
            status=run_registry.STATUS_COMPLETE, artifact_path="b.xlsx", view={},
        )
