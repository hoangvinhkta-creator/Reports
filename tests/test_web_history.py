"""TASK-PRA-002 — tầng web: một đơn vị công việc, fail-closed, trang trung thực.

Business logic bị monkeypatch ở đúng boundary (`run_owner_report`) như
`tests/test_web_server.py` đã làm: module này KHÔNG kiểm lại engine, nó kiểm
rằng `/run` ghi lịch sử và artifact trong CÙNG một cam kết, rằng khi ghi hỏng
thì không còn dấu vết nửa vời, và rằng các trang nói đúng sự thật về những gì
đã (không) được lưu.
"""

from __future__ import annotations

import io
from datetime import date
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine, func, select

import tools.db as history_db
from app.modules.exporting.excel_exporter import ReportSummary
from app.web import history_store
from app.web import server as web_server
from tools.db import schema
from tools.tracking import live_pull


def _presented(order="BH1", *, row=6, product="Tủ lạnh", price="8000000",
               sale_date=date(2026, 1, 5)):
    raw = SimpleNamespace(
        source_file="so.xlsx", source_sheet="Sheet1", source_row=row, row_hash=f"h{row}",
        date=sale_date, order_id=order, note_raw=None, product_raw=product,
        customer_code="KH-BI-MAT", customer="Nguyễn Văn A", address="1 Lê Lợi",
        phone="0900000000", quantity=Decimal("1"), sell_price=Decimal(price),
        total_sales_raw=Decimal(price), discount=Decimal("0"),
        employee_raw="Vũ Hạnh Ly", shipper_raw="Shipper X", delivery_cost=None,
        imei=None, source_profit=Decimal("100000"),
    )
    line = SimpleNamespace(
        raw=raw, order_id=order, total_sales=Decimal(price),
        employee_normalized="VuHanhLy", employee_group="G1", lead_source_final="PERSONAL",
        accounting_purchase_price=None, price_source="Pending", accounting_profit=None,
        kpi_purchase_price=None, kpi_purchase_price_provenance="Pending",
        eligible_kpi_profit=None, product_group_final="DIEN_MAY",
        conversion_scheme_final=None, conversion_rate_final=None,
    )
    return SimpleNamespace(line=line, record=None, reasons=("Pending.x",),
                           details=(), status="PENDING")


def _summary() -> ReportSummary:
    return ReportSummary(
        input_orders=2, accounted_orders=2, total_lines=2, auto_orders=0,
        review_orders=2, review_lines=2, error_count=0, review_reason_counts={},
    )


def _owner_run(tmp_path, *, name="report-20260901T080000Z.xlsx", lines=None):
    output_dir = tmp_path / "outputs" / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / name
    output_path.write_bytes(b"fake xlsx bytes")
    presented = lines if lines is not None else (
        _presented("BH1", row=6), _presented("BH2", row=7),
    )
    return SimpleNamespace(
        output_path=output_path,
        demo_run=SimpleNamespace(
            summary=_summary(), result=SimpleNamespace(unmapped_lines=[]),
            price_records=(), raw_rows=(), presented_lines=presented,
        ),
    )


def _upload(content: bytes = b"pretend workbook bytes"):
    return {"workbook": (io.BytesIO(content), "so_ke_toan.xlsx")}


@pytest.fixture
def snapshots():
    engine = create_engine("sqlite://")
    history_db.create_all_for_test(engine)
    return history_store.SnapshotRepository(engine)


@pytest.fixture
def app(monkeypatch, tmp_path, snapshots):
    monkeypatch.setattr(web_server, "UPLOAD_DIR", tmp_path / "uploads")
    monkeypatch.setattr(web_server, "ARTIFACT_DIR", (tmp_path / "outputs" / "reports").resolve())
    monkeypatch.setattr(web_server, "TRACKING_TEMP_DIR", tmp_path / "tracking_live_tmp")
    monkeypatch.setattr(web_server, "select_latest_valid_captures", lambda: None)
    monkeypatch.setattr(live_pull, "is_configured", lambda env=None: False)
    application = web_server.create_app(db_path=tmp_path / "runs.db", snapshots=snapshots)
    application.testing = True
    return application


@pytest.fixture
def client(app):
    return app.test_client()


def _by_run(repository, run_id: str) -> dict:
    match, = [row for row in repository.list_snapshots() if row["run_id"] == run_id]
    return match


def _count(repository, table) -> int:
    with repository.engine.connect() as connection:
        return connection.execute(select(func.count()).select_from(table)).scalar()


# --- một đơn vị công việc -------------------------------------------------

def test_a_successful_run_writes_the_run_and_the_snapshot_together(
    client, monkeypatch, tmp_path, snapshots, app,
):
    monkeypatch.setattr(web_server, "run_owner_report",
                        lambda **_: _owner_run(tmp_path))
    response = client.post("/run", data=_upload(), content_type="multipart/form-data")

    assert response.status_code == 302
    store = app.config["RUN_REGISTRY"]
    assert len(store.list_runs()) == 1
    snapshot, = snapshots.list_snapshots()
    assert snapshot["run_id"] == store.list_runs()[0].run_id
    assert (snapshot["n_insert"], snapshot["line_count"]) == (2, 2)
    assert snapshots.current_totals()["orders"] == 2


def test_running_the_same_workbook_twice_leaves_the_current_state_alone(
    client, monkeypatch, tmp_path, snapshots,
):
    monkeypatch.setattr(web_server, "run_owner_report", lambda **_: _owner_run(tmp_path))
    client.post("/run", data=_upload(), content_type="multipart/form-data")
    before = snapshots.current_totals()

    monkeypatch.setattr(web_server, "run_owner_report",
                        lambda **_: _owner_run(tmp_path, name="report-20260901T090000Z.xlsx"))
    client.post("/run", data=_upload(), content_type="multipart/form-data")

    # Chọn theo run_id, không theo thứ tự: hai lần chạy trong CÙNG một giây có
    # `created_at` bằng nhau, nên thứ tự hiển thị không phải là danh tính.
    first = _by_run(snapshots, "report-20260901T080000Z")
    second = _by_run(snapshots, "report-20260901T090000Z")
    assert second["n_same"] == 2 and second["n_insert"] == 0
    assert second["duplicate_of_snapshot_id"] == first["snapshot_id"]
    assert _count(snapshots, schema.order_line_source_version) == 2
    assert snapshots.current_totals() == before


def test_a_broken_history_write_leaves_neither_a_run_nor_a_snapshot(
    client, monkeypatch, tmp_path, snapshots, app,
):
    """Fail-closed: không có run "thành công" mà lịch sử không ghi được."""
    monkeypatch.setattr(web_server, "run_owner_report", lambda **_: _owner_run(tmp_path))

    def explode(*args, **kwargs):
        raise history_store.HistoryUnavailableError("database gãy")

    monkeypatch.setattr(snapshots, "write_snapshot", explode)
    response = client.post("/run", data=_upload(), content_type="multipart/form-data")

    assert response.status_code == 500
    assert "không lưu được vào lịch sử run" in response.get_data(as_text=True)
    assert app.config["RUN_REGISTRY"].list_runs() == []
    assert snapshots.list_snapshots() == []


def test_a_broken_run_store_rolls_the_snapshot_back_too(
    client, monkeypatch, tmp_path, snapshots, app,
):
    """Chiều ngược lại: R2/registry lỗi → snapshot cũng không được commit."""
    monkeypatch.setattr(web_server, "run_owner_report", lambda **_: _owner_run(tmp_path))

    def explode(**kwargs):
        raise RuntimeError("R2 không khả dụng")

    monkeypatch.setattr(app.config["RUN_REGISTRY"], "create_run", explode)
    response = client.post("/run", data=_upload(), content_type="multipart/form-data")

    assert response.status_code == 500
    assert snapshots.list_snapshots() == []
    assert _count(snapshots, schema.order_line_source_version) == 0
    assert app.config["RUN_REGISTRY"].list_runs() == []


def test_without_a_history_store_the_run_still_works_and_says_it_was_not_saved(
    monkeypatch, tmp_path,
):
    monkeypatch.setattr(web_server, "UPLOAD_DIR", tmp_path / "uploads")
    monkeypatch.setattr(web_server, "ARTIFACT_DIR", (tmp_path / "outputs" / "reports").resolve())
    monkeypatch.setattr(web_server, "select_latest_valid_captures", lambda: None)
    monkeypatch.setattr(live_pull, "is_configured", lambda env=None: False)
    monkeypatch.setattr(web_server, "_build_history", lambda env=None: None)
    monkeypatch.setattr(web_server, "run_owner_report", lambda **_: _owner_run(tmp_path))
    application = web_server.create_app(db_path=tmp_path / "runs.db")
    application.testing = True
    client = application.test_client()

    response = client.post("/run", data=_upload(), content_type="multipart/form-data")
    assert response.status_code == 302
    page = client.get(response.headers["Location"]).get_data(as_text=True)
    assert "KHÔNG được lưu lịch sử" in page


# --- các trang ------------------------------------------------------------

def test_the_data_tab_lists_snapshots_next_to_the_runs(client, monkeypatch, tmp_path):
    monkeypatch.setattr(web_server, "run_owner_report", lambda **_: _owner_run(tmp_path))
    client.post("/run", data=_upload(), content_type="multipart/form-data")

    page = client.get("/du-lieu").get_data(as_text=True)
    assert "Snapshot kế toán" in page
    assert "CÓ SNAPSHOT" in page
    assert "KHÔNG CÓ LỊCH SỬ (ghi lỗi)" not in page


def test_a_run_without_a_snapshot_is_labelled_instead_of_passed_over(
    client, monkeypatch, tmp_path, app,
):
    """Ghi lịch sử hỏng ở lần hiếm hoi sau khi R2 đã ghi → phải NHÌN THẤY."""
    app.config["RUN_REGISTRY"].create_run(
        run_id="run-mo-coi", created_at="2026-02-01T00:00:00", status="COMPLETE",
        workbook_display_name="so.xlsx", artifact_path=None, view=None,
        tracking_evidence=None,
    )
    page = client.get("/du-lieu").get_data(as_text=True)
    assert "KHÔNG CÓ LỊCH SỬ (ghi lỗi)" in page


def test_the_snapshot_page_shows_the_reconcile_counts_and_never_a_customer(
    client, monkeypatch, tmp_path, snapshots,
):
    monkeypatch.setattr(web_server, "run_owner_report", lambda **_: _owner_run(tmp_path))
    client.post("/run", data=_upload(), content_type="multipart/form-data")
    snapshot, = snapshots.list_snapshots()

    response = client.get(f"/du-lieu/snapshot/{snapshot['snapshot_id']}")
    page = response.get_data(as_text=True)
    assert response.status_code == 200
    assert snapshot["snapshot_id"] in page
    assert "Không đổi (SAME)" in page
    assert "CHƯA XÁC NHẬN ĐỦ" in page
    for secret in ("Nguyễn Văn A", "0900000000", "1 Lê Lợi", "KH-BI-MAT", "Shipper X"):
        assert secret not in page


def test_the_snapshot_page_shows_the_source_changed_flag_with_both_values(
    client, monkeypatch, tmp_path, snapshots,
):
    monkeypatch.setattr(web_server, "run_owner_report", lambda **_: _owner_run(tmp_path))
    client.post("/run", data=_upload(), content_type="multipart/form-data")

    edited = (_presented("BH1", row=6, price="9000000"), _presented("BH2", row=7))
    monkeypatch.setattr(
        web_server, "run_owner_report",
        lambda **_: _owner_run(tmp_path, name="report-20260901T090000Z.xlsx", lines=edited),
    )
    client.post("/run", data=_upload(b"khac"), content_type="multipart/form-data")

    latest = _by_run(snapshots, "report-20260901T090000Z")
    assert latest["n_source_changed"] == 1
    page = client.get(f"/du-lieu/snapshot/{latest['snapshot_id']}").get_data(as_text=True)
    assert "SOURCE_CHANGED" in page
    assert "8000000" in page and "9000000" in page


def test_an_unknown_snapshot_is_a_404_not_an_empty_page(client):
    assert client.get("/du-lieu/snapshot/SNAP-khong-co").status_code == 404


def test_the_snapshot_page_is_unavailable_rather_than_empty_without_a_store(
    monkeypatch, tmp_path,
):
    monkeypatch.setattr(web_server, "_build_history", lambda env=None: None)
    application = web_server.create_app(db_path=tmp_path / "runs.db")
    application.testing = True
    assert application.test_client().get("/du-lieu/snapshot/SNAP-x").status_code == 503
