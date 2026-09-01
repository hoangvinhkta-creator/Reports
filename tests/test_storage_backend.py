"""S071B — ``app.web.storage_backend``: chọn LocalRunStore/R2RunStore,
``R2RunStore`` end-to-end qua ``FakeR2Client``, fail-closed config.
"""

from __future__ import annotations

import pytest

from app.web import storage_backend
from tests.fixtures.fake_r2_client import FakeClientError, FakeR2Client
from tools.storage import r2_store

ENV = {
    r2_store.ACCOUNT_ID_ENV_VAR: "acct",
    r2_store.BUCKET_ENV_VAR: "bucket",
    r2_store.ACCESS_KEY_ID_ENV_VAR: "key",
    r2_store.SECRET_ACCESS_KEY_ENV_VAR: "secret",
}


def _run_store() -> storage_backend.R2RunStore:
    return storage_backend.R2RunStore(client=FakeR2Client(), env=ENV)


# --- build() backend selection ----------------------------------------------


def test_build_picks_local_when_r2_not_configured(monkeypatch, tmp_path):
    monkeypatch.delenv(storage_backend.REQUIRE_R2_ENV_VAR, raising=False)
    for name in r2_store._REQUIRED_ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    store = storage_backend.build(db_path=tmp_path / "runs.db", artifact_dir=tmp_path)
    assert isinstance(store, storage_backend.LocalRunStore)


def test_build_picks_r2_when_configured(monkeypatch, tmp_path):
    for name, value in ENV.items():
        monkeypatch.setenv(name, value)
    store = storage_backend.build(db_path=tmp_path / "runs.db", artifact_dir=tmp_path)
    assert isinstance(store, storage_backend.R2RunStore)


def test_build_fails_closed_when_require_r2_but_unconfigured(monkeypatch, tmp_path):
    monkeypatch.setenv(storage_backend.REQUIRE_R2_ENV_VAR, "1")
    for name in r2_store._REQUIRED_ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(storage_backend.StorageConfigurationError):
        storage_backend.build(db_path=tmp_path / "runs.db", artifact_dir=tmp_path)


def test_build_does_not_silently_fall_back_to_local_in_required_mode(monkeypatch, tmp_path):
    """Production không được âm thầm chạy bằng SQLite/đĩa ephemeral khi
    ``REPORTS_REQUIRE_R2=1`` — phải fail configuration validation ngay."""
    monkeypatch.setenv(storage_backend.REQUIRE_R2_ENV_VAR, "1")
    monkeypatch.delenv(r2_store.ACCESS_KEY_ID_ENV_VAR, raising=False)
    with pytest.raises(storage_backend.StorageConfigurationError):
        storage_backend.build(db_path=tmp_path / "runs.db", artifact_dir=tmp_path)


# --- R2RunStore: create/get/list --------------------------------------------


def test_create_then_get_round_trips_all_fields():
    store = _run_store()
    store.create_run(
        run_id="report-20260901T080000Z",
        created_at="2026-09-01T08:00:00+00:00",
        status="COMPLETE",
        workbook_display_name="So_ban_hang.xlsx",
        artifact_path="artifacts/report-20260901T080000Z.xlsx",
        view={"input_orders": 58},
        tracking_evidence={"catalog_capture_id": "LIVE-CAT-1"},
    )
    record = store.get_run("report-20260901T080000Z")
    assert record.status == "COMPLETE"
    assert record.workbook_display_name == "So_ban_hang.xlsx"
    assert record.view == {"input_orders": 58}
    assert record.tracking_evidence == {"catalog_capture_id": "LIVE-CAT-1"}


def test_unknown_run_id_returns_none_not_an_exception():
    store = _run_store()
    assert store.get_run("does-not-exist") is None


def test_invalid_run_id_returns_none_not_an_exception():
    store = _run_store()
    assert store.get_run("../../etc/passwd") is None


def test_list_runs_newest_first():
    store = _run_store()
    for run_id, created_at in [
        ("report-20260901T080000Z", "2026-09-01T08:00:00+00:00"),
        ("report-20260901T090000Z", "2026-09-01T09:00:00+00:00"),
    ]:
        store.create_run(run_id=run_id, created_at=created_at, status="COMPLETE")
    runs = store.list_runs(limit=10)
    assert [r.run_id for r in runs] == ["report-20260901T090000Z", "report-20260901T080000Z"]


def test_two_independent_r2_run_stores_share_state_multi_viewer():
    """Hai viewer = hai ``R2RunStore`` riêng biệt trỏ cùng client/bucket —
    không qua bất kỳ state process-local nào (S071B MULTI-VIEWER)."""
    client = FakeR2Client()
    viewer_a = storage_backend.R2RunStore(client=client, env=ENV)
    viewer_a.create_run(
        run_id="report-shared", created_at="2026-09-01T08:00:00+00:00", status="COMPLETE",
        view={"input_orders": 58},
    )
    viewer_b = storage_backend.R2RunStore(client=client, env=ENV)
    seen = viewer_b.get_run("report-shared")
    assert seen is not None
    assert seen.view == {"input_orders": 58}


def test_duplicate_run_id_raises_run_already_exists():
    from tools.storage.errors import RunAlreadyExistsError

    store = _run_store()
    store.create_run(run_id="dup", created_at="2026-09-01T08:00:00+00:00", status="COMPLETE")
    # Client dùng lại — cùng object store — mô phỏng ghi trùng thật.
    same_client_store = storage_backend.R2RunStore(client=store._client, env=ENV)
    with pytest.raises(RunAlreadyExistsError):
        same_client_store.create_run(
            run_id="dup", created_at="2026-09-01T09:00:00+00:00", status="COMPLETE",
        )


def test_list_runs_skips_one_corrupt_record_but_keeps_the_rest():
    client = FakeR2Client()
    store = storage_backend.R2RunStore(client=client, env=ENV)
    store.create_run(run_id="report-good", created_at="2026-09-01T08:00:00+00:00", status="COMPLETE")
    client.put_raw(r2_store.run_key("report-corrupt"), b"{not json")
    runs = store.list_runs(limit=10)
    assert [r.run_id for r in runs] == ["report-good"]


def test_list_runs_propagates_real_storage_failure_not_empty_history():
    client = FakeR2Client()
    store = storage_backend.R2RunStore(client=client, env=ENV)
    store.create_run(run_id="report-a", created_at="2026-09-01T08:00:00+00:00", status="COMPLETE")
    client.fail["get_object"] = FakeClientError("500")
    from tools.storage.errors import StorageUnavailableError

    with pytest.raises(StorageUnavailableError):
        store.list_runs(limit=10)


# --- R2RunStore: artifact ----------------------------------------------------


def test_save_artifact_uploads_verifies_and_deletes_temp_file(tmp_path):
    store = _run_store()
    temp_path = tmp_path / "report-x.xlsx"
    temp_path.write_bytes(b"fake xlsx bytes")

    ref = store.save_artifact(temp_path, "report-x")

    assert ref == r2_store.artifact_key("report-x")
    assert not temp_path.exists()
    record = _record(run_id="report-x", artifact_path=ref)
    response_bytes = _download_bytes(store, record)
    assert response_bytes == b"fake xlsx bytes"


def test_artifact_response_returns_none_for_missing_artifact():
    store = _run_store()
    record = _record(run_id="report-missing", artifact_path=r2_store.artifact_key("report-missing"))
    assert store.artifact_response(record) is None


def test_artifact_response_rejects_run_artifact_mismatch():
    """artifact_path không khớp key tự suy từ run_id (giả mạo/hỏng dữ liệu)
    — không bao giờ resolve theo artifact_path thô."""
    store = _run_store()
    record = _record(run_id="report-x", artifact_path="artifacts/someone-elses-run.xlsx")
    assert store.artifact_response(record) is None


def test_artifact_upload_failure_does_not_leave_a_dangling_reference(tmp_path):
    store = _run_store()
    store._client.fail["put_object"] = FakeClientError("503")
    temp_path = tmp_path / "report-x.xlsx"
    temp_path.write_bytes(b"data")
    from tools.storage.errors import StorageUnavailableError

    with pytest.raises(StorageUnavailableError):
        store.save_artifact(temp_path, "report-x")
    # save_artifact thất bại → caller (server.py) không được gọi create_run;
    # tự bản thân store không giữ state gì cho run này.
    assert store.get_run("report-x") is None


def _record(*, run_id: str, artifact_path: str):
    from app.web.run_registry import RunRecord

    return RunRecord(
        run_id=run_id, created_at="2026-09-01T08:00:00+00:00", status="COMPLETE",
        workbook_display_name=None, artifact_path=artifact_path, view=None,
        tracking_evidence=None, error_message=None,
    )


def _download_bytes(store: storage_backend.R2RunStore, record) -> bytes:
    from flask import Flask

    app = Flask(__name__)
    with app.test_request_context():
        response = store.artifact_response(record)
        response.direct_passthrough = False
        return response.get_data()
