"""Vertical legacy trên web (TASK-PRA-001.4): nhập → lưu → truy vấn → hiển thị.

Nhóm test này chứng minh KẾT QUẢ NGƯỜI DÙNG THẤY, không chỉ là "có route":
Owner chọn kỳ lịch sử và nhìn thấy số cũ, mọi số đeo nhãn LEGACY kèm đơn vị,
ô có lỗi công thức đã biết có dấu nhắc, và không có đường nào biến sự cố
database thành một trang "chưa có dữ liệu".
"""

from __future__ import annotations

import io
import re
from pathlib import Path

import pytest
from sqlalchemy import create_engine

import tools.db as history_db
from app.web import history_store, legacy_presentation
from app.web import server as web_server
from tools.tracking import live_pull


@pytest.fixture
def repository():
    engine = create_engine("sqlite://")
    history_db.create_all_for_test(engine)
    return history_store.build(engine=engine)


@pytest.fixture
def app(monkeypatch, tmp_path, repository):
    monkeypatch.setattr(web_server, "UPLOAD_DIR", tmp_path / "uploads")
    monkeypatch.setattr(web_server, "ARTIFACT_DIR", (tmp_path / "outputs").resolve())
    monkeypatch.setattr(web_server, "select_latest_valid_captures", lambda: None)
    monkeypatch.setattr(live_pull, "is_configured", lambda env=None: False)
    application = web_server.create_app(db_path=tmp_path / "runs.db", history=repository)
    application.testing = True
    return application


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def loaded(client, legacy_workbook_path):
    client.post(
        "/du-lieu/legacy",
        data={"workbook": (io.BytesIO(legacy_workbook_path.read_bytes()), "bao_cao.xlsx")},
        content_type="multipart/form-data",
    )
    return client


def _upload(filename: str, content: bytes = b"khong phai xlsx"):
    return {"workbook": (io.BytesIO(content), filename)}


# --- Nhập workbook legacy -------------------------------------------------

def test_importing_a_legacy_workbook_makes_it_visible_in_the_data_tab(
    client, legacy_workbook_path,
):
    response = client.post(
        "/du-lieu/legacy",
        data={"workbook": (io.BytesIO(legacy_workbook_path.read_bytes()), "bao_cao.xlsx")},
        content_type="multipart/form-data", follow_redirects=True,
    )
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "LEG-" in body
    assert "LEGACY_REFERENCE" in body


def test_reimporting_the_same_file_says_so_and_adds_no_version(loaded, legacy_workbook_path):
    response = loaded.post(
        "/du-lieu/legacy",
        data={"workbook": (io.BytesIO(legacy_workbook_path.read_bytes()), "bao_cao.xlsx")},
        content_type="multipart/form-data", follow_redirects=True,
    )
    body = response.get_data(as_text=True)
    assert "đã được nhập trước đó" in body
    assert body.count("LEGACY_REFERENCE") == 1


def test_a_non_xlsx_upload_is_rejected(client):
    response = client.post("/du-lieu/legacy", data=_upload("hack.php"),
                           content_type="multipart/form-data", follow_redirects=True)
    assert "Chỉ chấp nhận file .xlsx" in response.get_data(as_text=True)


def test_a_missing_upload_is_rejected(client):
    response = client.post("/du-lieu/legacy", data={},
                           content_type="multipart/form-data", follow_redirects=True)
    assert "Hãy chọn workbook legacy" in response.get_data(as_text=True)


def test_a_path_traversal_filename_never_reaches_the_filesystem(client, legacy_workbook_path):
    client.post(
        "/du-lieu/legacy",
        data={"workbook": (io.BytesIO(legacy_workbook_path.read_bytes()),
                           "../../../etc/passwd.xlsx")},
        content_type="multipart/form-data", follow_redirects=True,
    )
    assert not (Path("/tmp") / "passwd.xlsx").exists()


def test_the_uploaded_workbook_is_deleted_even_when_the_import_fails(client, tmp_path):
    upload_dir = tmp_path / "uploads"
    response = client.post("/du-lieu/legacy", data=_upload("hong.xlsx", b"khong phai zip"),
                           content_type="multipart/form-data", follow_redirects=True)
    assert "Không đọc được workbook legacy" in response.get_data(as_text=True)
    assert list(upload_dir.glob("*")) == []


def test_the_uploaded_workbook_is_deleted_after_a_successful_import(loaded, tmp_path):
    assert list((tmp_path / "uploads").glob("*")) == []


def test_the_oversize_limit_still_applies_to_legacy_uploads(app):
    assert app.config["MAX_CONTENT_LENGTH"] == web_server.MAX_UPLOAD_BYTES


def test_a_workbook_missing_frozen_sheets_reports_the_missing_sheets(client, synthetic_raw_path):
    response = client.post(
        "/du-lieu/legacy",
        data={"workbook": (io.BytesIO(synthetic_raw_path.read_bytes()), "sai.xlsx")},
        content_type="multipart/form-data", follow_redirects=True,
    )
    assert "Summary 2026" in response.get_data(as_text=True)


# --- Trang Nhân viên ------------------------------------------------------

def test_the_seller_matrix_shows_the_legacy_numbers_of_the_chosen_period(loaded):
    body = loaded.get("/nhan-vien?ky=2026-01").get_data(as_text=True)
    assert "Tháng 01/2026" in body
    assert "1.240.500" in body          # Tổng bán NV-A, nghìn đồng
    assert "14.452.000" in body         # Tổng bán Kênh-1
    assert "Tổng T01" in body


def test_the_period_picker_switches_periods(loaded):
    body = loaded.get("/nhan-vien?ky=2026-02").get_data(as_text=True)
    assert "15.100.000" in body
    assert "1.240.500" not in body


def test_every_number_on_the_seller_page_carries_the_legacy_label(loaded):
    """CHECK-PRA001-04: không một số cũ nào được hiển thị thiếu nhãn nguồn."""
    body = loaded.get("/nhan-vien?ky=2026-01").get_data(as_text=True)
    cells = re.findall(r'<td class="num[^"]*"[^>]*>(.*?)</td>', body, re.S)
    assert cells
    assert all(legacy_presentation.ORIGIN_BADGE in cell for cell in cells)


def test_the_page_states_the_unit_of_the_legacy_numbers(loaded):
    body = loaded.get("/nhan-vien?ky=2026-01").get_data(as_text=True)
    assert "nghìn đồng (số cũ)" in body


def test_defective_cells_show_their_defect_code(loaded):
    body = loaded.get("/nhan-vien?ky=2026-01").get_data(as_text=True)
    assert "A1" in body and "A6" in body and "A2" in body
    assert "87,6" in body               # giá trị lỗi vẫn hiện nguyên trạng
    body_february = loaded.get("/nhan-vien?ky=2026-02").get_data(as_text=True)
    assert "A4" in body_february


def test_a_period_without_data_shows_an_honest_empty_state_not_zeros(loaded):
    body = loaded.get("/nhan-vien?ky=2019-01").get_data(as_text=True)
    assert "không có trong bản legacy" in body
    assert "0" not in re.findall(r'<td class="num[^"]*">(.*?)</td>', body, re.S)


def test_the_seller_page_is_empty_state_safe_before_any_import(client):
    body = client.get("/nhan-vien").get_data(as_text=True)
    assert "Chưa nhập bản báo cáo cũ nào" in body


def test_the_page_names_the_legacy_version_being_viewed(loaded):
    body = loaded.get("/nhan-vien?ky=2026-01").get_data(as_text=True)
    assert "Bản đang xem" in body
    assert "bao_cao.xlsx" in body


# --- Trang Doanh số theo ngày --------------------------------------------

def test_the_daily_page_shows_datachart_values_in_plain_vnd(loaded):
    body = loaded.get("/doanh-so-ngay?ky=2026-01").get_data(as_text=True)
    assert "820.000.000" in body
    assert "đồng (số cũ)" in body


def test_the_daily_page_shows_the_monthly_reference_row(loaded):
    body = loaded.get("/doanh-so-ngay?ky=2026-01").get_data(as_text=True)
    assert "2.780.000.000" in body      # tổng tháng từ DataChart
    assert "2.410.000.000" in body      # cùng kỳ năm trước


def test_the_daily_page_warns_that_datachart_is_a_different_source(loaded):
    """Summary "Tổng bán" và DataChart "Doanh số" là hai nguồn khác nhau —
    trang không được để Owner tưởng hai số này phải khớp."""
    body = loaded.get("/doanh-so-ngay?ky=2026-01").get_data(as_text=True)
    assert "không được đối chiếu với nhau" in body


def test_every_number_on_the_daily_page_carries_the_legacy_label(loaded):
    body = loaded.get("/doanh-so-ngay?ky=2026-01").get_data(as_text=True)
    cells = re.findall(r'<td class="num[^"]*"[^>]*>(.*?)</td>', body, re.S)
    assert cells
    assert all(legacy_presentation.ORIGIN_BADGE in cell for cell in cells)


# --- Tab Dữ liệu và điều hướng -------------------------------------------

def test_the_data_tab_keeps_pipeline_runs_and_legacy_imports_apart(loaded):
    body = loaded.get("/du-lieu").get_data(as_text=True)
    assert "Báo cáo cũ (Excel)" in body
    assert "Các lần chạy pipeline" in body
    assert body.index("Báo cáo cũ") < body.index("Các lần chạy pipeline")


def test_the_old_history_url_still_leads_to_the_data_tab(client):
    response = client.get("/history")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/du-lieu")


def test_choosing_another_legacy_version_changes_what_the_pages_show(
    loaded, legacy_workbook_path, repository, tmp_path,
):
    from app.legacy import parse_workbook
    from tests.fixtures.legacy.build_legacy_workbook import build_legacy_workbook

    other = parse_workbook(build_legacy_workbook(tmp_path / "ban_khac.xlsx"))
    object.__setattr__(other, "file_fingerprint", "fingerprint-khac")
    object.__setattr__(other, "source_file_name", "ban_khac.xlsx")
    second = repository.create_import(other)

    assert "ban_khac.xlsx" in loaded.get("/nhan-vien").get_data(as_text=True)
    first = next(i for i in repository.list_imports() if i["import_id"] != second.import_id)
    loaded.post(f"/du-lieu/legacy/{first['import_id']}/chon", follow_redirects=True)
    assert "bao_cao.xlsx" in loaded.get("/nhan-vien").get_data(as_text=True)


def test_choosing_an_unknown_legacy_version_is_404(loaded):
    assert loaded.post("/du-lieu/legacy/LEG-khong-co/chon").status_code == 404


def test_every_page_links_the_tabs_that_actually_exist(loaded):
    body = loaded.get("/du-lieu").get_data(as_text=True)
    for path in ("/", "/du-lieu", "/nhan-vien", "/doanh-so-ngay"):
        assert f'href="{path}"' in body


# --- Fail-closed khi database hỏng ---------------------------------------

def test_a_database_failure_returns_503_not_an_empty_page(monkeypatch, tmp_path, repository):
    monkeypatch.setattr(live_pull, "is_configured", lambda env=None: False)
    monkeypatch.setattr(web_server, "select_latest_valid_captures", lambda: None)

    def _explode(*args, **kwargs):
        raise history_store.HistoryUnavailableError("mất kết nối")

    monkeypatch.setattr(repository, "available_periods", _explode)
    application = web_server.create_app(db_path=tmp_path / "runs.db", history=repository)
    application.testing = True
    response = application.test_client().get("/nhan-vien")
    assert response.status_code == 503


def test_a_database_failure_on_the_write_path_is_503_not_a_blamed_workbook(
    monkeypatch, tmp_path, repository, legacy_workbook_path,
):
    """Repair FIND-PRA001-R02 — đường GHI cũng phải fail-closed như đường ĐỌC.

    `_guarded` biến lỗi history store thành `abort(503)`, nhưng `abort` ném
    `HTTPException`; trước repair, `except Exception` trong route import đã
    nuốt nó và trả về redirect "Không đọc được workbook legacy". Tức là một
    sự cố DATABASE bị hiển thị thành LỖI FILE CỦA OWNER — Owner sẽ đi sửa
    workbook cho một lỗi hạ tầng, và CHECK-PRA001-06 bị phá trong im lặng.
    """
    monkeypatch.setattr(live_pull, "is_configured", lambda env=None: False)
    monkeypatch.setattr(web_server, "select_latest_valid_captures", lambda: None)
    monkeypatch.setattr(web_server, "UPLOAD_DIR", tmp_path / "uploads")

    def _explode(*args, **kwargs):
        raise history_store.HistoryUnavailableError("mất kết nối lúc ghi")

    monkeypatch.setattr(repository, "create_import", _explode)
    application = web_server.create_app(db_path=tmp_path / "runs.db", history=repository)
    application.testing = False          # để errorhandler 503 chạy thật
    response = application.test_client().post(
        "/du-lieu/legacy",
        data={"workbook": (io.BytesIO(legacy_workbook_path.read_bytes()), "bao_cao.xlsx")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 503
    assert response.status_code != 302
    assert "Không đọc được workbook" not in response.get_data(as_text=True)


def test_a_write_path_database_failure_still_deletes_the_uploaded_file(
    monkeypatch, tmp_path, repository, legacy_workbook_path,
):
    """Fail-closed không được đánh đổi bằng việc bỏ quên file trên đĩa."""
    monkeypatch.setattr(live_pull, "is_configured", lambda env=None: False)
    monkeypatch.setattr(web_server, "select_latest_valid_captures", lambda: None)
    upload_dir = tmp_path / "uploads"
    monkeypatch.setattr(web_server, "UPLOAD_DIR", upload_dir)

    def _explode(*args, **kwargs):
        raise history_store.HistoryUnavailableError("mất kết nối lúc ghi")

    monkeypatch.setattr(repository, "create_import", _explode)
    application = web_server.create_app(db_path=tmp_path / "runs.db", history=repository)
    application.testing = False
    application.test_client().post(
        "/du-lieu/legacy",
        data={"workbook": (io.BytesIO(legacy_workbook_path.read_bytes()), "bao_cao.xlsx")},
        content_type="multipart/form-data",
    )
    assert list(upload_dir.glob("*")) == []


def test_a_workbook_error_is_still_reported_as_a_workbook_error(client):
    """Repair R02 không được biến MỌI lỗi thành 503 — lỗi file vẫn là lỗi file."""
    response = client.post("/du-lieu/legacy", data=_upload("hong.xlsx", b"khong phai zip"),
                           content_type="multipart/form-data", follow_redirects=True)
    assert response.status_code == 200
    assert "Không đọc được workbook legacy" in response.get_data(as_text=True)


def test_an_unconfigured_history_store_says_so_instead_of_showing_no_data(
    monkeypatch, tmp_path,
):
    monkeypatch.setattr(live_pull, "is_configured", lambda env=None: False)
    monkeypatch.setattr(web_server, "select_latest_valid_captures", lambda: None)
    monkeypatch.setattr(web_server, "_build_history", lambda env=None: None)
    application = web_server.create_app(db_path=tmp_path / "runs.db")
    application.testing = True
    response = application.test_client().get("/nhan-vien")
    assert response.status_code == 503
    assert "History store chưa cấu hình" in response.get_data(as_text=True)


def test_importing_without_a_history_store_is_503_not_a_silent_success(
    monkeypatch, tmp_path, legacy_workbook_path,
):
    monkeypatch.setattr(live_pull, "is_configured", lambda env=None: False)
    monkeypatch.setattr(web_server, "select_latest_valid_captures", lambda: None)
    monkeypatch.setattr(web_server, "_build_history", lambda env=None: None)
    application = web_server.create_app(db_path=tmp_path / "runs.db")
    application.testing = True
    response = application.test_client().post(
        "/du-lieu/legacy",
        data={"workbook": (io.BytesIO(legacy_workbook_path.read_bytes()), "a.xlsx")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 503


def test_production_mode_refuses_to_start_without_a_database_url(monkeypatch):
    monkeypatch.setenv("REPORTS_REQUIRE_HISTORY_DB", "1")
    monkeypatch.delenv("HISTORY_DATABASE_URL", raising=False)
    with pytest.raises(history_db.HistoryConfigurationError):
        web_server._build_history()


def test_development_without_a_database_does_not_create_one(monkeypatch, tmp_path):
    monkeypatch.delenv("REPORTS_REQUIRE_HISTORY_DB", raising=False)
    monkeypatch.delenv("HISTORY_DATABASE_URL", raising=False)
    monkeypatch.setenv("REPORTS_DATA_ROOT", str(tmp_path))
    assert web_server._build_history() is None
    assert not (tmp_path / "data").exists()
