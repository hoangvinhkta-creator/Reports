"""TASK-PRA-002 — tầng web: một đơn vị công việc, fail-closed, trang trung thực.

Business logic bị monkeypatch ở đúng boundary (`run_owner_report`) như
`tests/test_web_server.py` đã làm: module này KHÔNG kiểm lại engine, nó kiểm
rằng `/run` ghi lịch sử và artifact trong CÙNG một cam kết, rằng khi ghi hỏng
thì không còn dấu vết nửa vời, và rằng các trang nói đúng sự thật về những gì
đã (không) được lưu.
"""

from __future__ import annotations

import io
import itertools
from datetime import date
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine, func, select

import tools.db as history_db
from app.modules.exporting.excel_exporter import ReportSummary
from app.web import history_store, history_writer
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


# --- slice B: xác nhận coverage tường minh --------------------------------

def _snapshot_id(snapshots) -> str:
    snapshot, = snapshots.list_snapshots()
    return snapshot["snapshot_id"]


@pytest.fixture
def sequential_clock(monkeypatch):
    """Mỗi lần chạy nhận một ``created_at`` KHÁC nhau.

    Trong đời thật hai lần upload sổ kế toán không rơi vào cùng một giây; trong
    test thì có. Trạng thái "cờ vắng mặt còn hiệu lực không" được suy ra từ
    thứ tự thời gian của snapshot, nên test nào nói về thứ tự phải điều khiển
    đồng hồ thay vì trông chờ vào tốc độ máy chạy test.
    """
    real = history_writer.write_run_history
    day = itertools.count(1)

    def with_clock(*args, **kwargs):
        kwargs["created_at"] = f"2026-02-{next(day):02d}T00:00:00+00:00"
        return real(*args, **kwargs)

    monkeypatch.setattr(history_writer, "write_run_history", with_clock)


def _run(client, monkeypatch, tmp_path, *, name, lines, content):
    monkeypatch.setattr(web_server, "run_owner_report",
                        lambda **_: _owner_run(tmp_path, name=name, lines=lines))
    return client.post("/run", data=_upload(content), content_type="multipart/form-data")


def test_the_confirmation_form_is_offered_with_the_box_unticked(
    client, monkeypatch, tmp_path, snapshots,
):
    """Mặc định KHÔNG tick: hệ thống không bao giờ mở sẵn một lời khẳng định."""
    _run(client, monkeypatch, tmp_path, name="report-1.xlsx",
         lines=(_presented("BH1", row=6),), content=b"a")
    page = client.get(f"/du-lieu/snapshot/{_snapshot_id(snapshots)}")

    body = page.get_data(as_text=True)
    assert page.status_code == 200
    assert 'name="xac_nhan"' in body and "checked" not in body
    assert "Tôi xác nhận" in body


def test_the_form_shows_the_detected_range_that_is_actually_stored(
    client, monkeypatch, tmp_path, snapshots,
):
    """Người dùng phải thấy ĐÚNG phạm vi họ đang xác nhận — không phải một mô tả."""
    lines = (_presented("BH1", row=6, sale_date=date(2026, 1, 5)),
             _presented("BH2", row=7, sale_date=date(2026, 1, 20)))
    _run(client, monkeypatch, tmp_path, name="report-1.xlsx", lines=lines, content=b"a")
    snapshot, = snapshots.list_snapshots()

    body = client.get(f"/du-lieu/snapshot/{snapshot['snapshot_id']}").get_data(as_text=True)

    assert str(snapshot["detected_date_min"]) == "2026-01-05"
    assert str(snapshot["detected_date_max"]) == "2026-01-20"
    assert 'value="2026-01-05"' in body and 'value="2026-01-20"' in body


def test_posting_without_ticking_the_box_is_refused_and_stores_nothing(
    client, monkeypatch, tmp_path, snapshots,
):
    _run(client, monkeypatch, tmp_path, name="report-1.xlsx",
         lines=(_presented("BH1", row=6),), content=b"a")
    snapshot_id = _snapshot_id(snapshots)

    response = client.post(f"/du-lieu/snapshot/{snapshot_id}/xac-nhan-du",
                           data={"tu_ngay": "2026-01-01", "den_ngay": "2026-01-31"})

    assert response.status_code == 400
    assert "Chưa tích ô xác nhận" in response.get_data(as_text=True)
    assert snapshots.get_snapshot(snapshot_id)["coverage_state"] != "CONFIRMED_COMPLETE"


def test_a_declared_range_that_leaves_data_outside_is_refused(
    client, monkeypatch, tmp_path, snapshots,
):
    lines = (_presented("BH1", row=6, sale_date=date(2026, 1, 20)),)
    _run(client, monkeypatch, tmp_path, name="report-1.xlsx", lines=lines, content=b"a")
    snapshot_id = _snapshot_id(snapshots)

    response = client.post(
        f"/du-lieu/snapshot/{snapshot_id}/xac-nhan-du",
        data={"tu_ngay": "2026-01-01", "den_ngay": "2026-01-10", "xac_nhan": "1"},
    )

    assert response.status_code == 400
    assert "2026-01-20" in response.get_data(as_text=True)
    assert snapshots.get_snapshot(snapshot_id)["confirmed_at"] is None


def test_an_over_long_range_is_refused_as_a_year_typo(
    client, monkeypatch, tmp_path, snapshots,
):
    _run(client, monkeypatch, tmp_path, name="report-1.xlsx",
         lines=(_presented("BH1", row=6),), content=b"a")
    snapshot_id = _snapshot_id(snapshots)

    response = client.post(
        f"/du-lieu/snapshot/{snapshot_id}/xac-nhan-du",
        data={"tu_ngay": "2026-01-01", "den_ngay": "2030-01-31", "xac_nhan": "1"},
    )

    assert response.status_code == 400
    assert snapshots.get_snapshot(snapshot_id)["coverage_state"] != "CONFIRMED_COMPLETE"


def test_an_explicit_confirmation_reaches_the_store_and_shows_the_new_label(
    client, monkeypatch, tmp_path, snapshots,
):
    """Đường hạnh phúc: tick ô → CONFIRMED_COMPLETE + PRG, nhãn đổi theo trạng thái."""
    _run(client, monkeypatch, tmp_path, name="report-1.xlsx",
         lines=(_presented("BH1", row=6),), content=b"a")
    snapshot_id = _snapshot_id(snapshots)

    response = client.post(
        f"/du-lieu/snapshot/{snapshot_id}/xac-nhan-du",
        data={"tu_ngay": "2026-01-01", "den_ngay": "2026-01-31", "xac_nhan": "1"},
    )

    assert response.status_code == 302
    stored = snapshots.get_snapshot(snapshot_id)
    assert stored["coverage_state"] == "CONFIRMED_COMPLETE"
    assert (str(stored["confirmed_range_start"]), str(stored["confirmed_range_end"])) == (
        "2026-01-01", "2026-01-31"
    )
    body = client.get(f"/du-lieu/snapshot/{snapshot_id}").get_data(as_text=True)
    assert "ĐÃ XÁC NHẬN ĐẦY ĐỦ" in body
    assert "2026-01-01" in body and "2026-01-31" in body
    assert 'name="xac_nhan"' not in body, "đã xác nhận thì không mời xác nhận lại"


def test_confirming_a_second_time_is_refused_with_409(
    client, monkeypatch, tmp_path, snapshots,
):
    _run(client, monkeypatch, tmp_path, name="report-1.xlsx",
         lines=(_presented("BH1", row=6),), content=b"a")
    snapshot_id = _snapshot_id(snapshots)
    form = {"tu_ngay": "2026-01-01", "den_ngay": "2026-01-31", "xac_nhan": "1"}
    client.post(f"/du-lieu/snapshot/{snapshot_id}/xac-nhan-du", data=form)
    before = snapshots.get_snapshot(snapshot_id)

    response = client.post(f"/du-lieu/snapshot/{snapshot_id}/xac-nhan-du", data=form)

    assert response.status_code == 409
    assert snapshots.get_snapshot(snapshot_id) == before


def test_confirming_an_unknown_snapshot_is_a_404(client):
    response = client.post("/du-lieu/snapshot/SNAP-khong-co/xac-nhan-du",
                           data={"tu_ngay": "2026-01-01", "den_ngay": "2026-01-31",
                                 "xac_nhan": "1"})
    assert response.status_code == 404


@pytest.mark.parametrize("header,expected", [
    ("Nhân viên: Tín Phát, Tháng 1 năm 2026", "header khớp phạm vi dữ liệu"),
    ("Sổ chi tiết bán hàng quý 1", "chỉ phát hiện phạm vi từ dữ liệu"),
])
def test_the_page_label_follows_the_stored_coverage_state(
    client, monkeypatch, tmp_path, snapshots, header, expected,
):
    """FIND-PRA002-A4: câu trên trang phải đến từ `coverage_state`, không cố định."""
    monkeypatch.setattr(web_server.history_writer, "scan_workbook",
                        lambda path: (header, 2, 0))
    _run(client, monkeypatch, tmp_path, name="report-1.xlsx",
         lines=(_presented("BH1", row=6),), content=b"a")

    body = client.get(f"/du-lieu/snapshot/{_snapshot_id(snapshots)}").get_data(as_text=True)

    assert expected in body


def test_the_page_reports_absence_without_ever_calling_it_a_deletion(
    client, monkeypatch, tmp_path, snapshots,
):
    """Cờ vắng mặt hiện ra, kèm câu nói rõ dòng đó VẪN được tính."""
    both = (_presented("BH1", row=6), _presented("BH2", row=7))
    _run(client, monkeypatch, tmp_path, name="report-1.xlsx", lines=both, content=b"a")
    totals_before = snapshots.current_totals()
    _run(client, monkeypatch, tmp_path, name="report-2.xlsx", lines=both[:1], content=b"b")

    second, = [row for row in snapshots.list_snapshots() if row["n_not_seen"] == 1]
    body = client.get(f"/du-lieu/snapshot/{second['snapshot_id']}").get_data(as_text=True)

    assert "NOT_SEEN_IN_LATEST_SNAPSHOT" in body
    assert "Còn hiệu lực" in body
    assert snapshots.current_totals() == totals_before, "tổng hiện hành KHÔNG đổi"


def test_a_line_that_returns_is_shown_as_no_longer_absent(
    client, monkeypatch, tmp_path, snapshots, sequential_clock,
):
    both = (_presented("BH1", row=6), _presented("BH2", row=7))
    _run(client, monkeypatch, tmp_path, name="report-1.xlsx", lines=both, content=b"a")
    _run(client, monkeypatch, tmp_path, name="report-2.xlsx", lines=both[:1], content=b"b")
    second, = [row for row in snapshots.list_snapshots() if row["n_not_seen"] == 1]
    _run(client, monkeypatch, tmp_path, name="report-3.xlsx", lines=both, content=b"c")

    body = client.get(f"/du-lieu/snapshot/{second['snapshot_id']}").get_data(as_text=True)

    assert "Đã xuất hiện lại ở" in body
    assert snapshots.count_flags(kind="NOT_SEEN_IN_LATEST_SNAPSHOT") == 1, (
        "cờ cũ vẫn còn nguyên — trạng thái hiệu lực là dẫn xuất, không phải xoá"
    )


def test_no_route_other_than_the_confirmation_one_can_confirm_coverage(
    client, monkeypatch, tmp_path, snapshots,
):
    """Chạy lại, xem trang, upload legacy — không đường nào nâng coverage."""
    _run(client, monkeypatch, tmp_path, name="report-1.xlsx",
         lines=(_presented("BH1", row=6),), content=b"a")
    _run(client, monkeypatch, tmp_path, name="report-2.xlsx",
         lines=(_presented("BH1", row=6),), content=b"a")
    client.get("/du-lieu")
    for snapshot in snapshots.list_snapshots():
        client.get(f"/du-lieu/snapshot/{snapshot['snapshot_id']}")

    assert all(row["coverage_state"] != "CONFIRMED_COMPLETE"
               for row in snapshots.list_snapshots())
