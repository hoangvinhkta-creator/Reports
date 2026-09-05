"""Vertical legacy trên web (TASK-PRA-001.4): nhập → lưu → truy vấn → hiển thị.

Nhóm test này chứng minh KẾT QUẢ NGƯỜI DÙNG THẤY, không chỉ là "có route":
Owner chọn kỳ lịch sử và nhìn thấy số cũ, mọi số đeo nhãn LEGACY kèm đơn vị,
ô có lỗi công thức đã biết có dấu nhắc, và không có đường nào biến sự cố
database thành một trang "chưa có dữ liệu".
"""

from __future__ import annotations

import io
import re

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
def loaded(client, repository, legacy_workbook_path):
    """Nạp một bản legacy để các test đọc-trang dùng chung.

    `POST /du-lieu/legacy` đã khóa vĩnh viễn (`DEC-181`, repair R2-B01) —
    route không còn tạo import nào, kể cả trong test. Seed đi thẳng qua
    `repository.create_import()`, dùng đúng bộ nhận dạng hình dạng workbook
    (`_looks_like_year_workbook`) mà route từng dùng, để hành vi seed không
    lệch khỏi hành vi nhập thật trước đây.
    """
    from dataclasses import replace

    from app.legacy import parse_workbook, parse_year_workbook

    workbook = (
        parse_year_workbook(legacy_workbook_path)
        if web_server._looks_like_year_workbook(legacy_workbook_path)
        else parse_workbook(legacy_workbook_path)
    )
    # Tên hiển thị cũ do form upload gán ("bao_cao.xlsx"), khác tên file tạm
    # của fixture — giữ nguyên để không lệch các assertion đã có trên tên này.
    repository.create_import(replace(workbook, source_file_name="bao_cao.xlsx"))
    return client


def _upload(filename: str, content: bytes = b"khong phai xlsx"):
    return {"workbook": (io.BytesIO(content), filename)}


# --- Nhập workbook legacy — route ĐÃ KHÓA (`DEC-181`, repair R2-B01) -----
#
# LEGACY_HISTORY chỉ gồm đúng hai nguồn provenance đã chốt (2025 độc lập +
# 01–08/2026); route GIỮ ĐĂNG KÝ cho tương thích nhưng từ chối MỌI request
# TRƯỚC khi đọc file/parse/chạm repository — kể cả file hợp lệ, kể cả file
# đã nhập trước đó, kể cả file rác. Các test "nhập thành công"/"báo lỗi định
# dạng" cũ của route này không còn đúng hành vi thật; nhóm dưới đây thay thế
# chúng bằng đúng bất biến mới.

def _import_count(repository) -> int:
    return len(repository.list_imports())


def test_post_legacy_is_refused_with_the_lock_message_before_any_side_effect(
    client, repository, legacy_workbook_path,
):
    before = _import_count(repository)
    response = client.post(
        "/du-lieu/legacy",
        data={"workbook": (io.BytesIO(legacy_workbook_path.read_bytes()), "bao_cao.xlsx")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 409
    assert "Dữ liệu lịch sử đã khóa" in response.get_data(as_text=True)
    assert _import_count(repository) == before


def test_post_legacy_refuses_even_a_bit_for_bit_identical_reupload(
    loaded, repository, legacy_workbook_path,
):
    """Trước repair, tải lại đúng file đã nhập là thao tác vô hại (trả về
    bản cũ, không tạo bản mới). Sau `DEC-181`, "vô hại" không còn là lý do
    cho phép — refuse vẫn refuse, bất kể fingerprint đã tồn tại hay chưa."""
    before = _import_count(repository)
    response = loaded.post(
        "/du-lieu/legacy",
        data={"workbook": (io.BytesIO(legacy_workbook_path.read_bytes()), "bao_cao.xlsx")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 409
    assert _import_count(repository) == before


def test_post_legacy_refuses_a_non_xlsx_upload_with_the_lock_message_not_a_format_error(client):
    """Refusal chạy TRƯỚC kiểm tra định dạng file — file rác cũng nhận đúng
    thông điệp khóa, không phải một lỗi "sai định dạng"."""
    response = client.post("/du-lieu/legacy", data=_upload("hack.php"),
                           content_type="multipart/form-data")
    assert response.status_code == 409
    assert "Dữ liệu lịch sử đã khóa" in response.get_data(as_text=True)


def test_post_legacy_refuses_a_request_with_no_file_at_all(client):
    response = client.post("/du-lieu/legacy", data={}, content_type="multipart/form-data")
    assert response.status_code == 409
    assert "Dữ liệu lịch sử đã khóa" in response.get_data(as_text=True)


def test_post_legacy_never_touches_the_upload_directory(client, tmp_path, legacy_workbook_path):
    upload_dir = tmp_path / "uploads"
    client.post(
        "/du-lieu/legacy",
        data={"workbook": (io.BytesIO(legacy_workbook_path.read_bytes()), "bao_cao.xlsx")},
        content_type="multipart/form-data",
    )
    assert not upload_dir.exists() or list(upload_dir.glob("*")) == []


def test_the_oversize_limit_still_applies_at_the_app_level(app):
    """`MAX_CONTENT_LENGTH` là cấu hình Flask toàn app (mọi route), không
    phụ thuộc hành vi của riêng `/du-lieu/legacy` — vẫn còn nguyên."""
    assert app.config["MAX_CONTENT_LENGTH"] == web_server.MAX_UPLOAD_BYTES


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
    assert "không có trong dữ liệu lịch sử" in body
    assert "0" not in re.findall(r'<td class="num[^"]*">(.*?)</td>', body, re.S)


def test_the_seller_page_is_empty_state_safe_before_any_import(client):
    body = client.get("/nhan-vien").get_data(as_text=True)
    assert "Chưa nhập bản báo cáo cũ nào" in body


def test_the_page_names_the_single_locked_history_source(loaded):
    """`DEC-181` — trang nói MỘT nguồn lịch sử đã khoá + file provenance.

    Không còn "Bản đang xem": khái niệm đó đã bị chủ dự án bác bỏ. Tên file
    vẫn hiện ra, nhưng với vai trò ĐỐI CHIẾU, không phải một bản để chọn.
    """
    body = loaded.get("/nhan-vien?ky=2026-01").get_data(as_text=True)
    assert "Bản đang xem" not in body
    assert "DỮ LIỆU LỊCH SỬ" in body
    assert "ĐÃ KHÓA" in body
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

def test_the_data_tab_keeps_pipeline_runs_and_legacy_history_apart(loaded):
    body = loaded.get("/du-lieu").get_data(as_text=True)
    assert "DỮ LIỆU LỊCH SỬ" in body
    assert "Các lần chạy pipeline" in body
    assert body.index("DỮ LIỆU LỊCH SỬ") < body.index("Các lần chạy pipeline")


def test_the_old_history_url_still_leads_to_the_data_tab(client):
    response = client.get("/history")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/du-lieu")


def test_the_legacy_source_selection_route_no_longer_exists(loaded, repository):
    """`DEC-181` §2 — chọn "bản đang xem" là quy trình chủ dự án bác bỏ.

    Không còn route nào thực hiện nó, nên cũng không còn cách nào (kể cả gõ
    tay URL) để một bản nhập legacy trở thành "nguồn đang xem".
    """
    import_id = repository.list_imports()[0]["import_id"]
    assert loaded.post(f"/du-lieu/legacy/{import_id}/chon").status_code == 404


def test_the_data_tab_offers_no_way_to_add_or_select_a_legacy_source(loaded):
    """`DEC-181` §8 · §9 — không nút chọn bản, không ô tải Legacy mới."""
    body = loaded.get("/du-lieu").get_data(as_text=True)
    for forbidden in ("CHỌN BẢN NÀY", "ĐANG XEM", "Bản đang xem", "NHẬP BẢN LEGACY"):
        assert forbidden not in body, forbidden
    assert "/du-lieu/legacy" not in body
    # Luồng SỐ MỚI không bị đụng tới.
    assert "CHẠY BÁO CÁO MỚI" in body


def test_every_page_links_the_tabs_that_actually_exist(loaded):
    """R1 (`GỠ TRÙNG UX`) rút thanh tab chính còn 4 mục: BÁO CÁO · NHÂN VIÊN ·
    DOANH SỐ NGÀY · DỮ LIỆU. `/` và `/nhan-vien` không còn là tab chính."""
    body = loaded.get("/du-lieu").get_data(as_text=True)
    for path in ("/kinh-doanh", "/kinh-doanh/nhan-vien", "/doanh-so-ngay", "/du-lieu"):
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


def test_post_legacy_is_refused_even_when_the_old_write_path_would_have_failed(
    monkeypatch, tmp_path, repository, legacy_workbook_path,
):
    """FIND-PRA001-R02/CHECK-PRA001-06 bảo vệ đường GHI cũ
    (`_guarded(repository.create_import, ...)`) khỏi lộ lỗi hạ tầng thành lỗi
    file của Owner. Đường GHI đó không còn tồn tại trong route (repair
    R2-B01 — refusal chạy TRƯỚC nó), nên `create_import` có nổ cũng không
    còn cơ hội được gọi tới: response luôn là 409 khóa, không phải 503,
    không phải "Không đọc được workbook"."""
    monkeypatch.setattr(live_pull, "is_configured", lambda env=None: False)
    monkeypatch.setattr(web_server, "select_latest_valid_captures", lambda: None)
    monkeypatch.setattr(web_server, "UPLOAD_DIR", tmp_path / "uploads")

    def _explode(*args, **kwargs):
        raise history_store.HistoryUnavailableError("mất kết nối lúc ghi")

    monkeypatch.setattr(repository, "create_import", _explode)
    application = web_server.create_app(db_path=tmp_path / "runs.db", history=repository)
    application.testing = False
    response = application.test_client().post(
        "/du-lieu/legacy",
        data={"workbook": (io.BytesIO(legacy_workbook_path.read_bytes()), "bao_cao.xlsx")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 409
    assert "Dữ liệu lịch sử đã khóa" in response.get_data(as_text=True)


def test_post_legacy_is_refused_even_without_a_history_store_configured(
    monkeypatch, tmp_path, legacy_workbook_path,
):
    """Refusal là bất biến NGHIỆP VỤ, không phụ thuộc hạ tầng — chưa cấu
    hình history store vẫn nhận đúng 409 khóa, không phải 503."""
    monkeypatch.setattr(live_pull, "is_configured", lambda env=None: False)
    monkeypatch.setattr(web_server, "select_latest_valid_captures", lambda: None)
    monkeypatch.setattr(web_server, "_build_history", lambda env=None: None)
    application = web_server.create_app(db_path=tmp_path / "runs.db")
    application.testing = False
    response = application.test_client().post(
        "/du-lieu/legacy",
        data={"workbook": (io.BytesIO(legacy_workbook_path.read_bytes()), "a.xlsx")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 409


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
