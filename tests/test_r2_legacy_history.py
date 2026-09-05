"""R2 (`DEC-181`) — LEGACY_HISTORY: MỘT nguồn lịch sử, hai file provenance.

Chủ dự án đã bỏ hẳn mô hình "nhiều bản legacy để chọn". Hệ thống có ĐÚNG một
nguồn lịch sử logic, ghép từ hai file provenance CỐ ĐỊNH:

    2025-01 .. 2025-12   →  workbook 2025 độc lập  (nguồn chuẩn của 2025)
    2026-01 .. 2026-08   →  workbook 2026          (nguồn của 01–08/2026)

Sự cố production được tái hiện ở đây, không phải kể lại: khi cờ `is_current`
trỏ vào workbook 2025 thì mọi kỳ 2026 biến mất khỏi báo cáo. Đó là một lỗi
ĐƯỜNG MÃ (`CODE_PATH_FAILURE`) — dữ liệu vẫn nằm đủ trong store — nên bài
test phải bắt được nó ở tầng chọn nguồn, đúng chỗ mà bộ test `DEC-180` trước
đây bắt đầu bên DƯỚI (nó dựng thẳng `SummaryRow`, nên tầng chọn bản nhập
không bao giờ được chạy).

Vì vậy mọi khẳng định dưới đây đi qua ĐƯỜNG THẬT:

    parser thật → bản nhập được lưu → bộ giải nguồn của repository
    → truy vấn lịch sử / MoM của nghiệp vụ

Số kiểm chứng nằm ở hai fixture cố ý LỆCH NHAU cho cùng kỳ 01/2025, nên quy
tắc "bản nhúng không ghi đè nguồn chuẩn" đo được thật chứ không trùng hợp.
"""

from __future__ import annotations

import re
from decimal import Decimal

import pytest
from sqlalchemy import create_engine

import tools.db as history_db
from app.legacy import parse_workbook, parse_year_workbook
from app.web import (
    business_store, history_store, legacy_reference,
)
from app.web import server as web_server
from tests.fixtures.legacy.build_handover_workbook import (
    EMBEDDED_2025_NVA_SALES, MONTH_TOTAL_SALES_KVND, build_handover_workbook,
)
from tests.fixtures.legacy.build_year_workbook import build_year_workbook
from tests.test_dec180_discount_parity import discounted_pair
from tests.test_business_vertical import persist
from tools.tracking import live_pull

# Nguồn chuẩn 01/2025 NV-A của `build_year_workbook()` — lệch hẳn bản nhúng.
AUTHORITATIVE_2025_NVA_SALES = Decimal("1180000")
AUGUST_2026_SALES_KVND = Decimal(MONTH_TOTAL_SALES_KVND[8])
AUGUST_2026_SALES_VND = AUGUST_2026_SALES_KVND * 1000

FILE_2025 = "Báo cáo Kinh doanh 2025.xlsx"
FILE_2026 = "Báo cáo Kinh doanh 2026.xlsx"


# --------------------------------------------------------------------------
# Đường nạp THẬT — parser → bản nhập được lưu (`DEC-181` §21).
# --------------------------------------------------------------------------

@pytest.fixture
def engine():
    engine = create_engine("sqlite://")
    history_db.create_all_for_test(engine)
    return engine


@pytest.fixture
def legacy(engine):
    return history_store.build(engine=engine)


@pytest.fixture
def snapshots(engine):
    return history_store.SnapshotRepository(engine)


@pytest.fixture
def store(engine):
    return business_store.BusinessDecisionStore(engine)


@pytest.fixture
def app(monkeypatch, tmp_path, legacy, snapshots):
    monkeypatch.setattr(web_server, "UPLOAD_DIR", tmp_path / "uploads")
    monkeypatch.setattr(web_server, "ARTIFACT_DIR", (tmp_path / "outputs").resolve())
    monkeypatch.setattr(web_server, "select_latest_valid_captures", lambda: None)
    monkeypatch.setattr(live_pull, "is_configured", lambda env=None: False)
    application = web_server.create_app(db_path=tmp_path / "runs.db", history=legacy,
                                        snapshots=snapshots)
    application.testing = True
    return application


@pytest.fixture
def client(app):
    return app.test_client()


def _import_2026(legacy, tmp_path, **kwargs) -> str:
    """Nạp workbook provenance 2026 qua PARSER THẬT."""
    path = build_handover_workbook(tmp_path / "bc_2026.xlsx", **kwargs)
    workbook = parse_workbook(path)
    object.__setattr__(workbook, "source_file_name", FILE_2026)
    return legacy.create_import(workbook).import_id


def _import_2025(legacy, tmp_path) -> str:
    """Nạp workbook provenance 2025 độc lập qua PARSER THẬT."""
    path = build_year_workbook(tmp_path / "bc_2025.xlsx")
    workbook = parse_year_workbook(path)
    object.__setattr__(workbook, "source_file_name", FILE_2025)
    return legacy.create_import(workbook).import_id


@pytest.fixture
def history(legacy, tmp_path):
    """Đúng hình dạng production: CẢ HAI bản nhập lịch sử cùng có mặt."""
    return {
        "2026": _import_2026(legacy, tmp_path),
        "2025": _import_2025(legacy, tmp_path),
    }


def body(client, path: str) -> str:
    response = client.get(path)
    assert response.status_code == 200, f"{path} → {response.status_code}"
    return response.get_data(as_text=True)


def metric(html: str, name: str) -> str:
    match = re.search(rf'data-metric="{re.escape(name)}"[^>]*>(.*?)<', html, re.S)
    assert match is not None, f"không tìm thấy data-metric={name}"
    return match.group(1).strip()


def sales_of(rows, label):
    return next(row["sales"] for row in rows if row["seller_label"] == label)


# ==========================================================================
# CASE 1 — HAI BẢN NHẬP, MỘT LỊCH SỬ
# ==========================================================================

def test_case_1_both_years_are_available_at_the_same_time(legacy, history):
    """Đây là chính sự cố production, viết thành khẳng định."""
    periods = legacy.available_periods()
    assert (2025, 1) in periods and (2025, 2) in periods
    assert {month for year, month in periods if year == 2026} == set(range(1, 9))
    assert {year for year, _ in periods} == {2025, 2026}


def test_case_1_the_history_is_one_logical_source_over_two_files(legacy, history):
    sources = legacy.history_sources()
    assert len(sources) == 2, "đúng HAI file provenance"
    by_years = {tuple(item["years"]): item["source_file_name"] for item in sources}
    assert by_years == {(2025,): FILE_2025, (2026,): FILE_2026}


# ==========================================================================
# CASE 2 · 3 — MỘT KỲ ⟹ MỘT NGUỒN
# ==========================================================================

def test_case_2_a_2025_period_resolves_from_the_standalone_2025_workbook(
    legacy, history,
):
    source = legacy.history_source_for_year(2025)
    assert source["source_file_name"] == FILE_2025
    rows = legacy.query_summary(2025, 1)
    assert rows
    assert {row["import_id"] for row in rows} == {history["2025"]}
    assert {row["sheet_name"] for row in rows} == {"Summary"}


def test_case_3_august_2026_resolves_from_the_2026_workbook(legacy, history):
    source = legacy.history_source_for_year(2026)
    assert source["source_file_name"] == FILE_2026
    rows = legacy.query_summary(2026, 8)
    assert rows
    assert {row["import_id"] for row in rows} == {history["2026"]}
    assert sales_of(rows, "Tổng T08") == AUGUST_2026_SALES_KVND


# ==========================================================================
# CASE 4 — BẢN `Summary 2025` NHÚNG KHÔNG PHẢI THẨM QUYỀN
# ==========================================================================

def test_case_4_the_embedded_2025_snapshot_never_overrides_the_standalone(
    legacy, history,
):
    """Hai nguồn nói khác nhau về cùng ô: 1.180.000 (chuẩn) vs 1.120.000."""
    rows = legacy.query_summary(2025, 1)
    assert sales_of(rows, "NV-A") == AUTHORITATIVE_2025_NVA_SALES
    assert sales_of(rows, "NV-A") != Decimal(EMBEDDED_2025_NVA_SALES)
    # Bản nhúng KHÔNG bị xoá — vẫn tra được khi chỉ đích danh (audit).
    embedded = legacy.query_summary(2025, 1, import_id=history["2026"])
    assert sales_of(embedded, "NV-A") == Decimal(EMBEDDED_2025_NVA_SALES)


def test_case_4_the_order_of_import_does_not_decide_the_authority(legacy, tmp_path):
    """Nạp bản chuẩn TRƯỚC rồi bản nhúng SAU — kết quả không đổi."""
    _import_2025(legacy, tmp_path)
    _import_2026(legacy, tmp_path)
    rows = legacy.query_summary(2025, 1)
    assert sales_of(rows, "NV-A") == AUTHORITATIVE_2025_NVA_SALES


# ==========================================================================
# CASE 5 · 6 · 7 — CỜ `is_current` KHÔNG CÒN LÀ THẨM QUYỀN NGHIỆP VỤ
# ==========================================================================

def test_case_5_august_2026_resolves_even_when_the_old_flag_points_at_2025(
    legacy, history,
):
    """Đây là ĐÚNG cấu hình đã làm hỏng production trước R2."""
    legacy.set_current(history["2025"])
    rows = legacy.query_summary(2026, 8)
    assert sales_of(rows, "Tổng T08") == AUGUST_2026_SALES_KVND
    assert (2026, 8) in legacy.available_periods()


def test_case_6_2025_resolves_even_when_the_old_flag_points_at_2026(
    legacy, history,
):
    legacy.set_current(history["2026"])
    rows = legacy.query_summary(2025, 1)
    assert sales_of(rows, "NV-A") == AUTHORITATIVE_2025_NVA_SALES
    assert (2025, 1) in legacy.available_periods()


def _history_fingerprint(legacy) -> tuple:
    """Toàn bộ thứ mà cờ `is_current` TỪNG điều khiển, gom vào một giá trị."""
    def key(row, *fields):
        return tuple(str(row.get(field)) for field in fields)

    return (
        tuple(legacy.available_periods()),
        tuple(sorted(key(row, "seller_label", "sales")
                     for row in legacy.query_summary(2025, 1))),
        tuple(sorted(key(row, "seller_label", "sales")
                     for row in legacy.query_summary(2026, 8))),
        tuple(sorted(key(row, "year", "month", "sales_current_year_vnd")
                     for row in legacy.query_monthly_reference(2026))),
        tuple(sorted(key(row, "year", "seller_label", "sheet_name", "sales")
                     for row in legacy.query_all_summary())),
    )


def test_case_7_flipping_the_old_current_flag_changes_nothing_at_all(
    legacy, history,
):
    legacy.set_current(history["2026"])
    with_2026 = _history_fingerprint(legacy)
    legacy.set_current(history["2025"])
    with_2025 = _history_fingerprint(legacy)
    assert with_2025 == with_2026


def test_case_7_flipping_the_old_current_flag_does_not_move_the_mom(
    legacy, snapshots, client, history,
):
    persist(snapshots, [discounted_pair("BH-CK", month=9, day=5)])
    legacy.set_current(history["2026"])
    first = metric(body(client, "/kinh-doanh?ky=2026-09"), "mom")
    legacy.set_current(history["2025"])
    second = metric(body(client, "/kinh-doanh?ky=2026-09"), "mom")
    assert first == second


# ==========================================================================
# CASE 8 · 9 — HAI NGUỒN BẰNG CHỨNG CỦA CÙNG MỘT FILE 2026 (`DEC-180` §13)
# ==========================================================================

def test_case_8_a_2026_month_resolves_through_summary_month_total(legacy, history):
    resolved = legacy_reference.authoritative_period_sales(
        year=2026, month=8,
        summary_rows=legacy.query_summary(2026, 8),
        monthly_rows=legacy.query_monthly_reference(2026),
    )
    assert resolved.source == legacy_reference.PERIOD_SOURCE_SUMMARY_MONTH_TOTAL
    assert resolved.sales_vnd == AUGUST_2026_SALES_VND


def test_case_9_datachart_carries_the_month_when_summary_has_no_total(
    legacy, tmp_path,
):
    """Cùng MỘT file provenance 2026 — Summary im lặng, DataChart có bằng chứng."""
    from tests.fixtures.legacy.build_handover_workbook import DATACHART_DAILY_VND

    _import_2026(legacy, tmp_path, summary_months=tuple(range(1, 8)))
    _import_2025(legacy, tmp_path)
    assert legacy.query_summary(2026, 8) == []
    resolved = legacy_reference.authoritative_period_sales(
        year=2026, month=8,
        summary_rows=legacy.query_summary(2026, 8),
        monthly_rows=legacy.query_monthly_reference(2026),
    )
    assert resolved.source == legacy_reference.PERIOD_SOURCE_DATACHART_MONTH
    assert resolved.sales_vnd == Decimal(sum(DATACHART_DAILY_VND[8]))


# ==========================================================================
# CASE 10 · 11 — BÀN GIAO 08/2026 (SỐ CŨ) → 09/2026 (SỐ MỚI)
# ==========================================================================

def test_case_11_september_current_compares_against_august_legacy(
    legacy, snapshots, client, history,
):
    """`1.000 kVND` = `1.000.000 VND`; số mới 09/2026 = `4.900.000 VND`.

    `(4.900.000 − 1.000.000) / 1.000.000 = +390 %` — và mốc so đó đi ra từ
    workbook provenance 2026 qua parser thật, không phải từ một `SummaryRow`
    dựng tay.
    """
    persist(snapshots, [discounted_pair("BH-CK", month=9, day=5)])
    html = body(client, "/kinh-doanh?ky=2026-09")
    assert metric(html, "sales_revenue") == "4.900"
    assert metric(html, "mom") == "+390%"
    assert metric(html, "mom-origin") == "SỐ CŨ"


def test_case_10_the_kvnd_factor_of_one_thousand_is_still_applied(
    legacy, snapshots, client, history,
):
    """Quên hệ số 1.000 cho ra `+489.900 %` — một tỉ lệ TRÔNG NHƯ THẬT."""
    persist(snapshots, [discounted_pair("BH-CK", month=9, day=5)])
    html = body(client, "/kinh-doanh?ky=2026-09")
    assert metric(html, "mom") != "+489.900%"
    assert metric(html, "mom") == "+390%"


def test_case_12_the_two_sources_are_never_added_together(legacy, history):
    """`DEC-166 E` — một kỳ là số của MỘT nguồn, không bao giờ là tổng hai."""
    for year in (2025, 2026):
        rows = legacy.query_summary(year)
        assert len({row["import_id"] for row in rows}) == 1, year
    # Không kỳ nào xuất hiện hai lần trong danh mục kỳ.
    periods = legacy.available_periods()
    assert len(periods) == len(set(periods))
    # 01/2025 chỉ có MỘT dòng tổng tháng, không phải tổng của hai nguồn.
    totals = [row for row in legacy.query_summary(2025, 1)
              if row["row_kind"] == "MONTH_TOTAL"]
    assert len(totals) == 1
    assert totals[0]["sales"] != (
        Decimal(EMBEDDED_2025_NVA_SALES) + totals[0]["sales"])


def test_case_12_current_and_legacy_are_never_summed_for_one_period(
    legacy, snapshots, client, history,
):
    persist(snapshots, [discounted_pair("BH-CK", month=9, day=5)])
    html = body(client, "/kinh-doanh?ky=2026-09")
    assert metric(html, "sales_revenue") == "4.900"
    assert "5.900.000" not in html


# ==========================================================================
# CASE 13 — HAI ỨNG VIÊN NGANG NHAU ⟹ NỔ RA, KHÔNG ĐOÁN
# ==========================================================================

def test_case_13_two_eligible_2026_imports_fail_loud(legacy, tmp_path):
    _import_2026(legacy, tmp_path)
    second = build_handover_workbook(tmp_path / "bc_2026_khac.xlsx",
                                     summary_months=(1, 2, 3))
    other = parse_workbook(second)
    object.__setattr__(other, "source_file_name", "Bản 2026 thứ hai.xlsx")
    legacy.create_import(other)

    with pytest.raises(history_store.LegacyHistoryAmbiguityError) as raised:
        legacy.available_periods()
    message = str(raised.value)
    assert "2026" in message
    assert FILE_2026 in message and "Bản 2026 thứ hai.xlsx" in message


def test_case_13_the_web_says_what_is_ambiguous_instead_of_showing_nothing(
    legacy, client, tmp_path,
):
    """Không được biến mâu thuẫn nguồn thành một trang rỗng, và cũng không
    được đổ cho hạ tầng ("lưu trữ tạm thời không khả dụng")."""
    _import_2026(legacy, tmp_path)
    other = parse_workbook(build_handover_workbook(tmp_path / "khac.xlsx",
                                                   summary_months=(1, 2)))
    object.__setattr__(other, "source_file_name", "Bản 2026 thứ hai.xlsx")
    legacy.create_import(other)

    response = client.get("/nhan-vien")
    assert response.status_code == 409
    text = response.get_data(as_text=True)
    assert "cùng đủ tư cách làm nguồn" in text
    assert "Lưu trữ tạm thời không khả dụng" not in text


# ==========================================================================
# CASE 14 · 15 · 16 · 17 — GIAO DIỆN
# ==========================================================================

SELECTOR_WORDS = ("CHỌN BẢN NÀY", "ĐANG XEM", "Bản đang xem")


@pytest.mark.parametrize("path", [
    "/du-lieu", "/lich-su", "/nhan-vien", "/doanh-so-ngay",
])
def test_case_14_no_normal_page_offers_a_legacy_version_selector(
    client, history, path,
):
    html = body(client, path)
    for word in SELECTOR_WORDS:
        assert word not in html, f"{path} còn '{word}'"
    assert "/chon" not in html


def test_case_14_the_history_area_states_one_locked_source(client, history):
    html = body(client, "/du-lieu")
    assert "DỮ LIỆU LỊCH SỬ" in html
    assert "01/2025 → 08/2026" in html
    assert "ĐÃ KHÓA" in html


def test_case_15_both_provenance_files_stay_visible_for_audit(client, history):
    html = body(client, "/du-lieu")
    assert FILE_2025 in html and FILE_2026 in html
    assert "Nguồn 2025" in html and "Nguồn 2026" in html


def test_case_15_each_year_on_the_history_page_names_its_own_file(client, history):
    html = body(client, "/lich-su")
    assert FILE_2025 in html and FILE_2026 in html


def test_case_16_no_normal_ui_offers_creating_another_legacy_source(
    client, history,
):
    for path in ("/du-lieu", "/lich-su", "/nhan-vien", "/doanh-so-ngay"):
        html = body(client, path)
        assert "NHẬP BẢN LEGACY" not in html, path
        assert 'action="/du-lieu/legacy"' not in html, path
        assert 'name="workbook"' not in html, path


def test_case_17_the_current_engine_upload_flow_is_untouched(client, history):
    html = body(client, "/du-lieu")
    assert "CHẠY BÁO CÁO MỚI" in html
    assert 'href="/du-lieu/chay-bao-cao"' in html
    assert body(client, "/du-lieu/chay-bao-cao")


def test_case_18_the_primary_nav_is_unchanged(client, history):
    html = body(client, "/du-lieu")
    nav = re.search(r'<nav class="ncc-tabs">(.*?)</nav>', html, re.S)
    assert nav is not None
    labels = re.findall(r">([^<>]+)</a>", nav.group(1))
    assert [label.strip() for label in labels] == [
        "Báo cáo", "Nhân viên", "Doanh số ngày", "Dữ liệu"]


# ==========================================================================
# §10 — `/lich-su` là MỘT dòng thời gian, không phải "bản đang xem"
# ==========================================================================

def test_the_history_page_lists_one_timeline_across_both_years(client, history):
    html = body(client, "/lich-su")
    assert "Năm 2025" in html and "Năm 2026" in html
    assert "Tháng 08/2026" in html
    assert "Tháng 01/2025" in html


def test_the_history_page_is_identical_whichever_import_holds_the_old_flag(
    legacy, client, history,
):
    legacy.set_current(history["2026"])
    first = body(client, "/lich-su")
    legacy.set_current(history["2025"])
    assert body(client, "/lich-su") == first


# ==========================================================================
# §17 — `/` mở kỳ mới nhất của dòng thời gian báo cáo
# ==========================================================================

def test_root_still_prefers_the_latest_current_engine_period(
    snapshots, client, history,
):
    persist(snapshots, [discounted_pair("BH-CK", month=9, day=5)])
    response = client.get("/", follow_redirects=False)
    assert response.headers["Location"] == "/kinh-doanh?ky=2026-09"


def test_root_falls_back_to_the_latest_legacy_period_when_there_is_no_current(
    client, history,
):
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["Location"] == "/nhan-vien?ky=2026-08"


# ==========================================================================
# §15 — R2 KHÔNG đụng tới công thức nghiệp vụ
# ==========================================================================

def test_the_current_engine_total_is_untouched_by_the_history_change(
    snapshots, client, history,
):
    persist(snapshots, [discounted_pair("BH-CK", month=9, day=5)])
    html = body(client, "/kinh-doanh?ky=2026-09")
    assert metric(html, "sales_revenue") == "4.900"


def test_an_employee_page_never_borrows_a_company_wide_legacy_month(
    snapshots, client, history,
):
    """`DEC-181` §16 — R2 sửa NGUỒN lịch sử, không mở ra ánh xạ nhân viên.

    Tổng tháng của sổ cũ là số của CẢ CÔNG TY, nên nó không bao giờ được làm
    mẫu số cho doanh thu của một người.
    """
    persist(snapshots, [discounted_pair("BH-CK", month=9, day=5)])
    html = body(client, "/kinh-doanh/nhan-vien?ky=2026-09&nv=Vinh")
    assert "SỐ CŨ" not in html
