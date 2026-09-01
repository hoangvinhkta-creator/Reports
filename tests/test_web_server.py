"""Reports Web Beta V1 (S070) — trust boundary, upload safety, privacy, reuse.

Toàn bộ business logic bị monkeypatch ở boundary (``run_owner_report``,
``select_latest_valid_captures``, ``beta_feedback.save_feedback``,
``beta_telemetry.record_run``) — module này KHÔNG kiểm tra lại engine, chỉ
kiểm tra tầng web mỏng gọi đúng adapter, không rò rỉ dữ liệu, và fail-safe
đúng trust boundary.
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
from app.web import server as web_server


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
    web_server._RUNS.clear()
    monkeypatch.setattr(web_server, "UPLOAD_DIR", tmp_path / "uploads")
    monkeypatch.setattr(web_server, "ARTIFACT_DIR", (tmp_path / "outputs" / "reports").resolve())
    monkeypatch.setattr(web_server, "select_latest_valid_captures", lambda: None)
    application = web_server.create_app()
    application.testing = True
    yield application
    web_server._RUNS.clear()


@pytest.fixture
def client(app):
    return app.test_client()


def _fake_owner_run(tmp_path, *, summary=None, output_name="report-20260901T080000Z.xlsx"):
    output_dir = tmp_path / "outputs" / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / output_name
    output_path.write_bytes(b"fake xlsx bytes")
    return SimpleNamespace(
        output_path=output_path,
        demo_run=SimpleNamespace(summary=summary or _summary()),
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

    def fake_run_owner_report(*, sales):
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
        lambda *, sales: (_ for _ in ()).throw(OwnerUsabilityError("boom")),
    )
    client.post("/run", data=_upload("a.xlsx"), content_type="multipart/form-data")
    assert list((tmp_path / "uploads").glob("*.xlsx")) == []


def test_owner_usability_error_is_shown_verbatim_truthfully(client, monkeypatch):
    monkeypatch.setattr(
        web_server, "run_owner_report",
        lambda *, sales: (_ for _ in ()).throw(
            OwnerUsabilityError("Báo cáo không đối chiếu đủ đơn hàng.")
        ),
    )
    resp = client.post("/run", data=_upload("a.xlsx"), content_type="multipart/form-data")
    assert resp.status_code == 400
    assert "Báo cáo không đối chiếu đủ đơn hàng.".encode() in resp.data


def test_generic_exception_never_leaks_traceback_or_message(client, monkeypatch):
    monkeypatch.setattr(
        web_server, "run_owner_report",
        lambda *, sales: (_ for _ in ()).throw(RuntimeError("secret-internal-detail-9f3a")),
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
    monkeypatch.setattr(web_server, "run_owner_report", lambda *, sales: owner_run)
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
    monkeypatch.setattr(web_server, "run_owner_report", lambda *, sales: owner_run)
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


def test_business_severity_is_never_labelled_as_error(client, monkeypatch, tmp_path):
    owner_run = _fake_owner_run(tmp_path)
    monkeypatch.setattr(web_server, "run_owner_report", lambda *, sales: owner_run)
    monkeypatch.setattr(beta_telemetry, "record_run", lambda record, **kw: None)
    client.post("/run", data=_upload("real.xlsx"), content_type="multipart/form-data")

    resp = client.get("/?run_id=report-20260901T080000Z")
    body = resp.data.decode()
    assert "Lỗi: 3" not in body
    assert "Ưu tiên xem ngay" in body


# --- Artifact download security ------------------------------------------

def test_download_requires_a_known_run_id(client):
    resp = client.get("/artifact/never-ran")
    assert resp.status_code == 404


def test_download_serves_the_exact_artifact_of_that_run(client, monkeypatch, tmp_path):
    owner_run = _fake_owner_run(tmp_path)
    monkeypatch.setattr(web_server, "run_owner_report", lambda *, sales: owner_run)
    monkeypatch.setattr(beta_telemetry, "record_run", lambda record, **kw: None)
    client.post("/run", data=_upload("real.xlsx"), content_type="multipart/form-data")

    resp = client.get("/artifact/report-20260901T080000Z")
    assert resp.status_code == 200
    assert resp.data == b"fake xlsx bytes"


def test_download_rejects_an_artifact_path_outside_the_registered_output_dir(client, tmp_path):
    outside = tmp_path / "somewhere_else.xlsx"
    outside.write_bytes(b"should never be served")
    web_server._RUNS["evil"] = {"output_path": outside, "view": {}}

    resp = client.get("/artifact/evil")
    assert resp.status_code == 404


def test_browser_never_receives_an_absolute_filesystem_path(client, monkeypatch, tmp_path):
    owner_run = _fake_owner_run(tmp_path)
    monkeypatch.setattr(web_server, "run_owner_report", lambda *, sales: owner_run)
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
    monkeypatch.setattr(web_server, "run_owner_report", lambda *, sales: owner_run)
    monkeypatch.setattr(beta_telemetry, "record_run", lambda record, **kw: None)
    client.post("/run", data=_upload("real.xlsx"), content_type="multipart/form-data")

    resp = client.get("/?run_id=report-20260901T080000Z")
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
    monkeypatch.setattr(web_server, "run_owner_report", lambda *, sales: owner_run)
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
