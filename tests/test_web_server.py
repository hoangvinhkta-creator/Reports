"""Reports Web Shared Online Beta (S071) — trust boundary, persistence,
multi-viewer, Tracking pull-on-run, upload safety, privacy, reuse.

Toàn bộ business logic bị monkeypatch ở boundary (``run_owner_report``,
``select_latest_valid_captures``, ``beta_feedback.save_feedback``,
``beta_telemetry.record_run``) — module này KHÔNG kiểm tra lại engine, chỉ
kiểm tra tầng web mỏng gọi đúng adapter, không rò rỉ dữ liệu, fail-safe đúng
trust boundary, VÀ (mới ở S071) registry persistent + đa viewer + Tracking
live pull.
"""

from __future__ import annotations

import io
import re
from pathlib import Path
from types import SimpleNamespace

import pytest

from app import beta_feedback, beta_telemetry
from app.modules.exporting.excel_exporter import ReportSummary
from app.owner_usability import OwnerUsabilityError
from app.web import run_registry, storage_backend
from app.web import server as web_server
from tests.fixtures.fake_r2_client import FakeClientError, FakeR2Client
from tools.storage import r2_store
from tools.tracking import live_pull


def _summary(**overrides) -> ReportSummary:
    base = dict(
        input_orders=58, accounted_orders=58, total_lines=83, auto_orders=22,
        review_orders=36, review_lines=47, error_count=3,
        review_reason_counts={"IDENTITY_UNRESOLVED": 31, "Suspicious": 3},
    )
    base.update(overrides)
    return ReportSummary(**base)


@pytest.fixture
def app(monkeypatch, tmp_path):
    monkeypatch.setattr(web_server, "UPLOAD_DIR", tmp_path / "uploads")
    monkeypatch.setattr(web_server, "ARTIFACT_DIR", (tmp_path / "outputs" / "reports").resolve())
    monkeypatch.setattr(web_server, "TRACKING_TEMP_DIR", tmp_path / "tracking_live_tmp")
    monkeypatch.setattr(web_server, "select_latest_valid_captures", lambda: None)
    # Mặc định test chạy ở chế độ "local" (S068–S070) — Tracking live pull
    # chỉ bật tường minh ở nhóm test riêng bên dưới.
    monkeypatch.setattr(live_pull, "is_configured", lambda env=None: False)
    application = web_server.create_app(db_path=tmp_path / "runs.db")
    application.testing = True
    yield application


@pytest.fixture
def client(app):
    return app.test_client()


def _fake_owner_run(tmp_path, *, summary=None, output_name="report-20260901T080000Z.xlsx",
                    unmapped_lines=()):
    output_dir = tmp_path / "outputs" / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / output_name
    output_path.write_bytes(b"fake xlsx bytes")
    return SimpleNamespace(
        output_path=output_path,
        demo_run=SimpleNamespace(
            summary=summary or _summary(),
            result=SimpleNamespace(unmapped_lines=list(unmapped_lines)),
        ),
    )


def _upload(filename: str, content: bytes = b"pretend workbook bytes"):
    return {"workbook": (io.BytesIO(content), filename)}


# --- Readiness / index -------------------------------------------------

def test_index_returns_200_and_shows_readiness(client, monkeypatch):
    monkeypatch.setattr(web_server, "select_latest_valid_captures", lambda: None)
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Có capture hợp lệ trên máy".encode() in resp.data


def test_index_shows_not_ready_when_no_complete_capture(client, monkeypatch):
    def _raise():
        raise OwnerUsabilityError("no capture")

    monkeypatch.setattr(web_server, "select_latest_valid_captures", _raise)
    resp = client.get("/")
    assert "Chưa sẵn sàng".encode() in resp.data


def test_index_shows_live_readiness_when_tracking_configured(client, monkeypatch):
    monkeypatch.setattr(live_pull, "is_configured", lambda env=None: True)
    resp = client.get("/")
    assert "live".encode() in resp.data.lower()


def test_unknown_run_id_in_query_is_fail_safe_not_found(client):
    resp = client.get("/?run_id=does-not-exist")
    assert resp.status_code == 200
    assert "Không tìm thấy kết quả chạy trước".encode() in resp.data


# --- Upload validation ---------------------------------------------------

def test_reject_non_xlsx_upload(client):
    resp = client.post("/run", data=_upload("notes.txt"), content_type="multipart/form-data")
    assert resp.status_code == 400
    assert "Chỉ chấp nhận file .xlsx.".encode() in resp.data


def test_reject_missing_upload(client):
    resp = client.post("/run", data={}, content_type="multipart/form-data")
    assert resp.status_code == 400


def test_upload_is_saved_under_a_server_generated_name_not_client_filename(
    client, monkeypatch, tmp_path
):
    captured = {}

    def fake_run_owner_report(*, sales, captures=None):
        captured["sales"] = sales
        raise OwnerUsabilityError("stop after capturing path")

    monkeypatch.setattr(web_server, "run_owner_report", fake_run_owner_report)

    client.post(
        "/run",
        data=_upload("../../../../etc/passwd.xlsx"),
        content_type="multipart/form-data",
    )

    saved = captured["sales"]
    assert saved.parent == (tmp_path / "uploads")
    assert re.fullmatch(r"[0-9a-f]{32}\.xlsx", saved.name)
    assert "passwd" not in saved.name
    assert ".." not in str(saved)


def test_temp_upload_is_deleted_after_run_regardless_of_outcome(client, monkeypatch, tmp_path):
    monkeypatch.setattr(
        web_server, "run_owner_report",
        lambda *, sales, captures=None: (_ for _ in ()).throw(OwnerUsabilityError("boom")),
    )
    client.post("/run", data=_upload("a.xlsx"), content_type="multipart/form-data")
    assert list((tmp_path / "uploads").glob("*.xlsx")) == []


def test_owner_usability_error_is_shown_verbatim_truthfully(client, monkeypatch):
    monkeypatch.setattr(
        web_server, "run_owner_report",
        lambda *, sales, captures=None: (_ for _ in ()).throw(
            OwnerUsabilityError("Báo cáo không đối chiếu đủ đơn hàng.")
        ),
    )
    resp = client.post("/run", data=_upload("a.xlsx"), content_type="multipart/form-data")
    assert resp.status_code == 400
    assert "Báo cáo không đối chiếu đủ đơn hàng.".encode() in resp.data


def test_generic_exception_never_leaks_traceback_or_message(client, monkeypatch):
    monkeypatch.setattr(
        web_server, "run_owner_report",
        lambda *, sales, captures=None: (_ for _ in ()).throw(RuntimeError("secret-internal-detail-9f3a")),
    )
    resp = client.post("/run", data=_upload("a.xlsx"), content_type="multipart/form-data")
    assert resp.status_code == 400
    body = resp.data.decode()
    assert "secret-internal-detail-9f3a" not in body
    assert "Traceback" not in body
    assert "RuntimeError" not in body
    assert "Không thể tạo báo cáo" in body


# --- Successful run + result rendering -----------------------------------

def test_successful_run_redirects_with_run_id_and_records_telemetry_once(
    client, monkeypatch, tmp_path
):
    owner_run = _fake_owner_run(tmp_path)
    monkeypatch.setattr(web_server, "run_owner_report", lambda *, sales, captures=None: owner_run)
    telemetry_calls = []
    monkeypatch.setattr(
        beta_telemetry, "record_run", lambda record, **kw: telemetry_calls.append(record)
    )

    resp = client.post("/run", data=_upload("real.xlsx"), content_type="multipart/form-data")

    assert resp.status_code == 302
    assert "run_id=report-20260901T080000Z" in resp.headers["Location"]
    assert len(telemetry_calls) == 1
    assert telemetry_calls[0].run_id == "report-20260901T080000Z"
    assert telemetry_calls[0].order_count == 58


def test_result_page_renders_authoritative_summary_and_reason_labels(
    client, monkeypatch, tmp_path
):
    owner_run = _fake_owner_run(tmp_path)
    monkeypatch.setattr(web_server, "run_owner_report", lambda *, sales, captures=None: owner_run)
    monkeypatch.setattr(beta_telemetry, "record_run", lambda record, **kw: None)
    client.post("/run", data=_upload("real.xlsx"), content_type="multipart/form-data")

    resp = client.get("/?run_id=report-20260901T080000Z")
    body = resp.data.decode()
    assert "58" in body  # Tổng đơn
    assert "22" in body  # AUTO
    assert "36" in body  # Cần xem lại
    assert "Ưu tiên xem ngay" in body and "3" in body
    assert "100%" in body
    assert "Bất thường" in body  # nhãn hiển thị của "Suspicious"
    assert "Chưa nhận diện sản phẩm" in body  # nhãn của IDENTITY_UNRESOLVED
    assert "real.xlsx" in body  # workbook display name (S071)
    assert "2026" in body  # created timestamp hiển thị (S071)


def test_business_severity_is_never_labelled_as_error(client, monkeypatch, tmp_path):
    owner_run = _fake_owner_run(tmp_path)
    monkeypatch.setattr(web_server, "run_owner_report", lambda *, sales, captures=None: owner_run)
    monkeypatch.setattr(beta_telemetry, "record_run", lambda record, **kw: None)
    client.post("/run", data=_upload("real.xlsx"), content_type="multipart/form-data")

    resp = client.get("/?run_id=report-20260901T080000Z")
    body = resp.data.decode()
    assert "Lỗi: 3" not in body
    assert "Ưu tiên xem ngay" in body


def test_dropped_lines_count_is_shown(client, monkeypatch, tmp_path):
    owner_run = _fake_owner_run(tmp_path, unmapped_lines=[object(), object()])
    monkeypatch.setattr(web_server, "run_owner_report", lambda *, sales, captures=None: owner_run)
    monkeypatch.setattr(beta_telemetry, "record_run", lambda record, **kw: None)
    client.post("/run", data=_upload("real.xlsx"), content_type="multipart/form-data")

    resp = client.get("/?run_id=report-20260901T080000Z")
    record = client.application.config["RUN_REGISTRY"].get_run("report-20260901T080000Z")
    assert record.view["dropped_lines"] == 2


# --- Artifact download security ------------------------------------------

def test_download_requires_a_known_run_id(client):
    resp = client.get("/artifact/never-ran")
    assert resp.status_code == 404


def test_download_serves_the_exact_artifact_of_that_run(client, monkeypatch, tmp_path):
    owner_run = _fake_owner_run(tmp_path)
    monkeypatch.setattr(web_server, "run_owner_report", lambda *, sales, captures=None: owner_run)
    monkeypatch.setattr(beta_telemetry, "record_run", lambda record, **kw: None)
    client.post("/run", data=_upload("real.xlsx"), content_type="multipart/form-data")

    resp = client.get("/artifact/report-20260901T080000Z")
    assert resp.status_code == 200
    assert resp.data == b"fake xlsx bytes"


def test_download_rejects_an_artifact_path_outside_the_registered_output_dir(
    client, app, tmp_path
):
    outside = tmp_path / "somewhere_else.xlsx"
    outside.write_bytes(b"should never be served")
    registry = app.config["RUN_REGISTRY"]
    registry.create_run(
        run_id="evil", created_at="2026-09-01T08:00:00+00:00",
        status=run_registry.STATUS_COMPLETE, artifact_path=str(outside), view={},
    )

    resp = client.get("/artifact/evil")
    assert resp.status_code == 404


def test_download_rejects_a_relative_traversal_artifact_path(client, app):
    registry = app.config["RUN_REGISTRY"]
    registry.create_run(
        run_id="evil-relative", created_at="2026-09-01T08:00:00+00:00",
        status=run_registry.STATUS_COMPLETE,
        artifact_path="../../etc/passwd", view={},
    )
    resp = client.get("/artifact/evil-relative")
    assert resp.status_code == 404


def test_browser_never_receives_an_absolute_filesystem_path(client, monkeypatch, tmp_path):
    owner_run = _fake_owner_run(tmp_path)
    monkeypatch.setattr(web_server, "run_owner_report", lambda *, sales, captures=None: owner_run)
    monkeypatch.setattr(beta_telemetry, "record_run", lambda record, **kw: None)
    client.post("/run", data=_upload("real.xlsx"), content_type="multipart/form-data")

    resp = client.get("/?run_id=report-20260901T080000Z")
    body = resp.data.decode()
    assert str(tmp_path) not in body
    assert str(owner_run.output_path) not in body


# --- Response privacy ------------------------------------------------------

FORBIDDEN_SUBSTRINGS = (
    "TRACKING_REPORT_API_KEY", "content_hash", "captured_by", "source_system_ref",
    "inv_map", "alias.map", "board.json", "purchase_price_baseline",
)


def test_index_response_contains_no_secret_or_authority_payload(client):
    resp = client.get("/")
    body = resp.data.decode()
    for token in FORBIDDEN_SUBSTRINGS:
        assert token not in body


def test_result_response_contains_no_secret_or_authority_payload(client, monkeypatch, tmp_path):
    owner_run = _fake_owner_run(tmp_path)
    monkeypatch.setattr(web_server, "run_owner_report", lambda *, sales, captures=None: owner_run)
    monkeypatch.setattr(beta_telemetry, "record_run", lambda record, **kw: None)
    client.post("/run", data=_upload("real.xlsx"), content_type="multipart/form-data")

    resp = client.get("/?run_id=report-20260901T080000Z")
    body = resp.data.decode()
    for token in FORBIDDEN_SUBSTRINGS:
        assert token not in body


def test_history_response_contains_no_secret_or_authority_payload(client, monkeypatch, tmp_path):
    owner_run = _fake_owner_run(tmp_path)
    monkeypatch.setattr(web_server, "run_owner_report", lambda *, sales, captures=None: owner_run)
    monkeypatch.setattr(beta_telemetry, "record_run", lambda record, **kw: None)
    client.post("/run", data=_upload("real.xlsx"), content_type="multipart/form-data")

    resp = client.get("/history")
    body = resp.data.decode()
    for token in FORBIDDEN_SUBSTRINGS:
        assert token not in body


# --- Feedback reuse (no second taxonomy) ----------------------------------

def test_feedback_categories_come_from_the_s069_reused_module(client):
    resp = client.get("/")
    body = resp.data.decode()
    for category in beta_feedback.FEEDBACK_CATEGORIES:
        assert category in body


def test_feedback_rejects_a_category_outside_the_reused_taxonomy(client):
    resp = client.post(
        "/feedback", data={"category": "Không có trong danh sách", "comment": "x"}
    )
    assert resp.status_code == 400


def test_feedback_saves_via_the_reused_s069_service(client, monkeypatch):
    saved = []
    monkeypatch.setattr(beta_feedback, "save_feedback", lambda record: saved.append(record))

    resp = client.post(
        "/feedback",
        data={"category": "Khác", "comment": "  ghi chú test  ", "run_id": "run-123"},
    )

    assert resp.status_code == 302
    assert "run_id=run-123" in resp.headers["Location"]
    assert "feedback=ok" in resp.headers["Location"]
    assert len(saved) == 1
    assert saved[0].category == "Khác"
    assert saved[0].run_id == "run-123"


def test_feedback_never_attaches_business_data_it_was_not_given(client, monkeypatch):
    saved = []
    monkeypatch.setattr(beta_feedback, "save_feedback", lambda record: saved.append(record))
    client.post("/feedback", data={"category": "Khác", "comment": "note"})
    fields = set(vars(saved[0]))
    assert fields == {"feedback_id", "timestamp", "run_id", "category", "comment"}


# --- Telemetry non-duplication --------------------------------------------

def test_refreshing_the_result_page_never_records_telemetry_again(
    client, monkeypatch, tmp_path
):
    owner_run = _fake_owner_run(tmp_path)
    monkeypatch.setattr(web_server, "run_owner_report", lambda *, sales, captures=None: owner_run)
    calls = []
    monkeypatch.setattr(beta_telemetry, "record_run", lambda record, **kw: calls.append(record))

    client.post("/run", data=_upload("real.xlsx"), content_type="multipart/form-data")
    client.get("/?run_id=report-20260901T080000Z")
    client.get("/?run_id=report-20260901T080000Z")

    assert len(calls) == 1


# --- Localhost-only / debug-off defaults ----------------------------------

def test_debug_mode_is_off_by_default(app):
    assert app.debug is False


def test_upload_size_limit_is_configured(app):
    assert app.config["MAX_CONTENT_LENGTH"] == web_server.MAX_UPLOAD_BYTES


def test_413_over_limit_response_is_short_and_actionable(client, app):
    app.config["MAX_CONTENT_LENGTH"] = 10
    resp = client.post(
        "/run", data=_upload("real.xlsx", content=b"x" * 100), content_type="multipart/form-data"
    )
    assert resp.status_code == 413
    assert "25MB".encode() in resp.data
    assert b"Traceback" not in resp.data


# --- History page (S071 §11) -----------------------------------------------

def test_history_page_lists_runs_newest_first(client, monkeypatch, tmp_path):
    monkeypatch.setattr(beta_telemetry, "record_run", lambda record, **kw: None)
    owner_run_a = _fake_owner_run(tmp_path, output_name="report-A.xlsx")
    monkeypatch.setattr(web_server, "run_owner_report", lambda *, sales, captures=None: owner_run_a)
    client.post("/run", data=_upload("first.xlsx"), content_type="multipart/form-data")

    owner_run_b = _fake_owner_run(tmp_path, output_name="report-B.xlsx")
    monkeypatch.setattr(web_server, "run_owner_report", lambda *, sales, captures=None: owner_run_b)
    client.post("/run", data=_upload("second.xlsx"), content_type="multipart/form-data")

    resp = client.get("/history")
    assert resp.status_code == 200
    body = resp.data.decode()
    assert "report-A" in body
    assert "report-B" in body
    assert body.index("report-B") < body.index("report-A")


def test_history_page_is_empty_state_safe_with_no_runs(client):
    resp = client.get("/history")
    assert resp.status_code == 200
    assert "Chưa có lần chạy nào".encode() in resp.data


# --- Persistence across restart (S071 §14) ----------------------------------

def test_run_and_artifact_survive_a_simulated_server_restart(monkeypatch, tmp_path):
    monkeypatch.setattr(web_server, "UPLOAD_DIR", tmp_path / "uploads")
    monkeypatch.setattr(web_server, "ARTIFACT_DIR", (tmp_path / "outputs" / "reports").resolve())
    monkeypatch.setattr(web_server, "select_latest_valid_captures", lambda: None)
    monkeypatch.setattr(live_pull, "is_configured", lambda env=None: False)
    monkeypatch.setattr(beta_telemetry, "record_run", lambda record, **kw: None)
    db_path = tmp_path / "runs.db"

    app1 = web_server.create_app(db_path=db_path)
    app1.testing = True
    owner_run = _fake_owner_run(tmp_path, output_name="report-restart.xlsx")
    monkeypatch.setattr(web_server, "run_owner_report", lambda *, sales, captures=None: owner_run)
    app1.test_client().post(
        "/run", data=_upload("real.xlsx"), content_type="multipart/form-data"
    )

    # "Restart application": app1 bị bỏ đi hoàn toàn, chỉ file DB + artifact
    # trên đĩa còn lại — app2 là một Flask app HOÀN TOÀN MỚI.
    del app1
    app2 = web_server.create_app(db_path=db_path)
    app2.testing = True
    client2 = app2.test_client()

    resp = client2.get("/?run_id=report-restart")
    assert resp.status_code == 200
    assert "Không tìm thấy" not in resp.data.decode()

    download = client2.get("/artifact/report-restart")
    assert download.status_code == 200
    assert download.data == b"fake xlsx bytes"

    history_resp = client2.get("/history")
    assert "report-restart" in history_resp.data.decode()


# --- Multi-viewer (S071 §15) ------------------------------------------------

def test_a_second_viewer_reads_the_same_persisted_run_not_a_process_local_copy(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(web_server, "UPLOAD_DIR", tmp_path / "uploads")
    monkeypatch.setattr(web_server, "ARTIFACT_DIR", (tmp_path / "outputs" / "reports").resolve())
    monkeypatch.setattr(web_server, "select_latest_valid_captures", lambda: None)
    monkeypatch.setattr(live_pull, "is_configured", lambda env=None: False)
    monkeypatch.setattr(beta_telemetry, "record_run", lambda record, **kw: None)
    db_path = tmp_path / "runs.db"

    # Viewer A: một Flask app + client riêng, tạo Run A.
    viewer_a_app = web_server.create_app(db_path=db_path)
    viewer_a_app.testing = True
    owner_run = _fake_owner_run(tmp_path, output_name="report-shared.xlsx")
    monkeypatch.setattr(web_server, "run_owner_report", lambda *, sales, captures=None: owner_run)
    viewer_a_app.test_client().post(
        "/run", data=_upload("real.xlsx"), content_type="multipart/form-data"
    )

    # Viewer B: một Flask app + client HOÀN TOÀN KHÁC, không chia sẻ object
    # Python nào với Viewer A ngoài cùng file DB trên đĩa.
    viewer_b_app = web_server.create_app(db_path=db_path)
    viewer_b_app.testing = True
    viewer_b_client = viewer_b_app.test_client()

    resp = viewer_b_client.get("/?run_id=report-shared")
    body = resp.data.decode()
    assert "58" in body  # cùng summary Viewer A vừa tạo
    assert "Không tìm thấy" not in body

    download = viewer_b_client.get("/artifact/report-shared")
    assert download.status_code == 200
    assert download.data == b"fake xlsx bytes"


# --- Storage failure (S071 §21) ---------------------------------------------

def test_registry_write_failure_after_report_generation_is_reported_not_hidden(
    client, app, monkeypatch, tmp_path
):
    owner_run = _fake_owner_run(tmp_path)
    monkeypatch.setattr(web_server, "run_owner_report", lambda *, sales, captures=None: owner_run)

    def _boom(**kwargs):
        raise sqlite3_error()

    def sqlite3_error():
        import sqlite3
        return sqlite3.OperationalError("disk I/O error (simulated)")

    monkeypatch.setattr(app.config["RUN_REGISTRY"], "create_run", _boom)
    app.config["PROPAGATE_EXCEPTIONS"] = False

    resp = client.post("/run", data=_upload("real.xlsx"), content_type="multipart/form-data")
    assert resp.status_code == 500
    body = resp.data.decode()
    assert "Traceback" not in body
    assert "OperationalError" not in body
    assert "disk I/O error" not in body


# --- Tracking pull-on-run integration (S071 §2/§3/§16) ----------------------

def test_run_uses_live_pull_captures_when_tracking_is_configured(
    client, monkeypatch, tmp_path
):
    monkeypatch.setattr(live_pull, "is_configured", lambda env=None: True)
    live_result = SimpleNamespace(
        tracking_capture=tmp_path / "live-history.json",
        tracking_catalog=tmp_path / "live-catalog.json",
        tracking_inv_map=None,
        evidence={"catalog_capture_id": "LIVE-CAT-1"},
        cleanup_called=[],
    )
    live_result.tracking_capture.write_text("{}")
    live_result.tracking_catalog.write_text("{}")

    def fake_cleanup():
        live_result.cleanup_called.append(True)

    live_result.cleanup = fake_cleanup
    monkeypatch.setattr(web_server.live_pull, "pull_live_captures", lambda **kw: live_result)

    captured = {}

    def fake_run_owner_report(*, sales, captures=None):
        captured["captures"] = captures
        owner_run = _fake_owner_run(tmp_path)
        return owner_run

    monkeypatch.setattr(web_server, "run_owner_report", fake_run_owner_report)
    monkeypatch.setattr(beta_telemetry, "record_run", lambda record, **kw: None)

    resp = client.post("/run", data=_upload("real.xlsx"), content_type="multipart/form-data")

    assert resp.status_code == 302
    assert captured["captures"] is not None
    assert captured["captures"].tracking_capture == live_result.tracking_capture
    assert live_result.cleanup_called == [True]

    record = client.application.config["RUN_REGISTRY"].get_run("report-20260901T080000Z")
    assert record.tracking_evidence == {"catalog_capture_id": "LIVE-CAT-1"}


def test_run_fails_clearly_and_does_not_silently_fall_back_when_tracking_unavailable(
    client, monkeypatch
):
    monkeypatch.setattr(live_pull, "is_configured", lambda env=None: True)

    def _raise(**kwargs):
        raise live_pull.TrackingUnavailableError(
            "mô phỏng lỗi mạng", node="purchase_price_history", reason="TIMEOUT",
        )

    monkeypatch.setattr(web_server.live_pull, "pull_live_captures", _raise)
    run_owner_report_called = []
    monkeypatch.setattr(
        web_server, "run_owner_report",
        lambda *, sales, captures=None: run_owner_report_called.append(True),
    )

    resp = client.post("/run", data=_upload("real.xlsx"), content_type="multipart/form-data")

    assert resp.status_code == 503
    assert "Tracking" in resp.data.decode()
    # KHÔNG được âm thầm tiếp tục chạy report bằng nguồn nào khác.
    assert run_owner_report_called == []


def test_cleanup_runs_even_when_owner_report_raises(client, monkeypatch, tmp_path):
    monkeypatch.setattr(live_pull, "is_configured", lambda env=None: True)
    live_result = SimpleNamespace(
        tracking_capture=tmp_path / "live-history.json",
        tracking_catalog=tmp_path / "live-catalog.json",
        tracking_inv_map=None,
        evidence={},
        cleanup_called=[],
    )
    live_result.cleanup = lambda: live_result.cleanup_called.append(True)
    monkeypatch.setattr(web_server.live_pull, "pull_live_captures", lambda **kw: live_result)
    monkeypatch.setattr(
        web_server, "run_owner_report",
        lambda *, sales, captures=None: (_ for _ in ()).throw(OwnerUsabilityError("boom")),
    )

    client.post("/run", data=_upload("real.xlsx"), content_type="multipart/form-data")

    assert live_result.cleanup_called == [True]


# --- R2 backend end-to-end (S071B) ------------------------------------------

R2_ENV = {
    r2_store.ACCOUNT_ID_ENV_VAR: "acct",
    r2_store.BUCKET_ENV_VAR: "bucket",
    r2_store.ACCESS_KEY_ID_ENV_VAR: "key",
    r2_store.SECRET_ACCESS_KEY_ENV_VAR: "secret",
}


def _r2_app(monkeypatch, tmp_path, *, r2_client=None):
    monkeypatch.setattr(web_server, "UPLOAD_DIR", tmp_path / "uploads")
    monkeypatch.setattr(web_server, "TRACKING_TEMP_DIR", tmp_path / "tracking_live_tmp")
    monkeypatch.setattr(web_server, "select_latest_valid_captures", lambda: None)
    monkeypatch.setattr(live_pull, "is_configured", lambda env=None: False)
    monkeypatch.setattr(beta_telemetry, "record_run", lambda record, **kw: None)
    store = storage_backend.R2RunStore(client=r2_client or FakeR2Client(), env=R2_ENV)
    application = web_server.create_app(store=store)
    application.testing = True
    return application


def test_r2_run_then_download_round_trips(monkeypatch, tmp_path):
    app = _r2_app(monkeypatch, tmp_path)
    client = app.test_client()
    owner_run = _fake_owner_run(tmp_path, output_name="report-r2.xlsx")
    monkeypatch.setattr(web_server, "run_owner_report", lambda *, sales, captures=None: owner_run)

    resp = client.post("/run", data=_upload("real.xlsx"), content_type="multipart/form-data")
    assert resp.status_code == 302

    result = client.get("/?run_id=report-r2")
    assert "58" in result.data.decode()

    download = client.get("/artifact/report-r2")
    assert download.status_code == 200
    assert download.data == b"fake xlsx bytes"
    # Temp local artifact đã bị xoá sau khi upload — không còn trên đĩa.
    assert not owner_run.output_path.exists()


def test_r2_second_viewer_reads_the_same_persisted_run(monkeypatch, tmp_path):
    shared_client = FakeR2Client()
    viewer_a = _r2_app(monkeypatch, tmp_path, r2_client=shared_client).test_client()
    owner_run = _fake_owner_run(tmp_path, output_name="report-shared-r2.xlsx")
    monkeypatch.setattr(web_server, "run_owner_report", lambda *, sales, captures=None: owner_run)
    viewer_a.post("/run", data=_upload("real.xlsx"), content_type="multipart/form-data")

    viewer_b = _r2_app(monkeypatch, tmp_path, r2_client=shared_client).test_client()
    resp = viewer_b.get("/?run_id=report-shared-r2")
    assert "58" in resp.data.decode()
    download = viewer_b.get("/artifact/report-shared-r2")
    assert download.status_code == 200
    assert download.data == b"fake xlsx bytes"


def test_r2_two_runs_created_close_together_both_land_independently(monkeypatch, tmp_path):
    shared_client = FakeR2Client()
    app = _r2_app(monkeypatch, tmp_path, r2_client=shared_client)
    client = app.test_client()

    owner_run_a = _fake_owner_run(tmp_path, output_name="report-conc-A.xlsx")
    monkeypatch.setattr(web_server, "run_owner_report", lambda *, sales, captures=None: owner_run_a)
    client.post("/run", data=_upload("first.xlsx"), content_type="multipart/form-data")

    owner_run_b = _fake_owner_run(tmp_path, output_name="report-conc-B.xlsx")
    monkeypatch.setattr(web_server, "run_owner_report", lambda *, sales, captures=None: owner_run_b)
    client.post("/run", data=_upload("second.xlsx"), content_type="multipart/form-data")

    runs = app.config["RUN_REGISTRY"].list_runs(limit=10)
    assert {r.run_id for r in runs} == {"report-conc-A", "report-conc-B"}


def test_r2_artifact_upload_failure_does_not_create_a_visible_run(monkeypatch, tmp_path):
    client_obj = FakeR2Client()
    app = _r2_app(monkeypatch, tmp_path, r2_client=client_obj)
    client = app.test_client()
    owner_run = _fake_owner_run(tmp_path, output_name="report-fail.xlsx")
    monkeypatch.setattr(web_server, "run_owner_report", lambda *, sales, captures=None: owner_run)
    client_obj.fail["put_object"] = FakeClientError("503", "R2 unavailable")

    resp = client.post("/run", data=_upload("real.xlsx"), content_type="multipart/form-data")

    assert resp.status_code == 500
    assert "Traceback" not in resp.data.decode()
    # Không được xuất hiện như một run thành công mà artifact không tồn tại.
    assert app.config["RUN_REGISTRY"].get_run("report-fail") is None


def test_r2_get_run_failure_returns_503_not_404(monkeypatch, tmp_path):
    client_obj = FakeR2Client()
    app = _r2_app(monkeypatch, tmp_path, r2_client=client_obj)
    client_obj.fail["get_object"] = FakeClientError("500", "unavailable")

    resp = app.test_client().get("/?run_id=report-anything")
    assert resp.status_code == 503
    assert "không khả dụng" in resp.data.decode()


def test_r2_history_list_failure_returns_503_not_empty_history(monkeypatch, tmp_path):
    client_obj = FakeR2Client()
    app = _r2_app(monkeypatch, tmp_path, r2_client=client_obj)
    client_obj.fail["list_objects_v2"] = FakeClientError("500")

    resp = app.test_client().get("/history")
    assert resp.status_code == 503


def test_r2_download_rejects_artifact_run_mismatch(monkeypatch, tmp_path):
    app = _r2_app(monkeypatch, tmp_path)
    store = app.config["RUN_REGISTRY"]
    store.create_run(
        run_id="evil-r2", created_at="2026-09-01T08:00:00+00:00",
        status=run_registry.STATUS_COMPLETE,
        artifact_path="artifacts/someone-elses-run.xlsx", view={},
    )
    resp = app.test_client().get("/artifact/evil-r2")
    assert resp.status_code == 404


def test_r2_download_unknown_run_id_is_404(monkeypatch, tmp_path):
    app = _r2_app(monkeypatch, tmp_path)
    resp = app.test_client().get("/artifact/never-ran")
    assert resp.status_code == 404


def test_require_r2_fails_app_startup_when_r2_unconfigured(monkeypatch, tmp_path):
    monkeypatch.setenv(storage_backend.REQUIRE_R2_ENV_VAR, "1")
    for name in r2_store._REQUIRED_ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    with pytest.raises(storage_backend.StorageConfigurationError):
        web_server.create_app(db_path=tmp_path / "runs.db")
