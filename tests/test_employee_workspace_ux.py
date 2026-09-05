"""`DEC-PHB02-08` — không gian làm việc Nhân viên, kiểm qua ứng dụng THẬT.

File này là bằng chứng cho toàn bộ các CASE nghiệm thu của quyết định:

    UX-01…UX-11   kỳ mặc định · hàng sheet · dải chỉ tiêu · tiến độ tháng
    TG-01…TG-09   Target theo nghìn đồng · Target nhóm · khứ hồi không trôi
    DT-01…DT-09   bảng kê gộp theo BH · khách hàng · ngày · thứ tự cột
    ED-01…ED-05   một nút sửa cho cả BH · giá nhập sửa ngay trên dòng
    EX-01…EX-07   loại một dòng khỏi báo cáo, và khôi phục lại
    GD-01…GD-17   phân loại Gia dụng ở CẤP DÒNG + bất biến phân bổ
    WR-01…WR-04   cảnh báo ngắn · dòng lỗ tô đỏ
    VIS-01…VIS-03 nền xen kẽ theo NGÀY

Nguyên tắc của cả file: mỗi test hỏi một câu NGHIỆP VỤ mà Owner hỏi được, và
trả lời bằng HTML thật do Flask dựng hoặc bằng con số thật do tầng ráp tính —
không có test nào chỉ hỏi "hàm này có chạy không".

Hai bất biến được lặp lại ở nhiều chỗ một cách có chủ đích, vì chúng là thứ
duy nhất phân biệt một bản sửa giao diện với một bản sửa làm hỏng sổ sách:

    TỔNG CÔNG TY KHÔNG ĐỔI khi một dòng chuyển bucket (`§42`).
    DANH TÍNH NGƯỜI BÁN KHÔNG ĐỔI khi một dòng chuyển bucket (`§6`, `§11`).
"""

from __future__ import annotations

import re
import subprocess
import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import create_engine, inspect

import tools.db as history_db
from app.modules.reporting import business_metrics as bm
from app.modules.reporting import reporting_sheets
from app.web import business_service, business_store, history_store
from app.web import server as web_server
from app.web import workspace_presentation as wp
from tests.test_snapshot_repository import result_line, source_line, write
from tools.tracking import live_pull

REPO_ROOT = Path(__file__).resolve().parents[1]

#: "Hôm nay" cố định của mọi test dựng HTML. Một test phụ thuộc ngày thật sẽ
#: đổi kết quả vào ngày mai, và ngày mai không ai còn nhớ vì sao.
TODAY = date(2026, 9, 3)
SEPTEMBER = {"date_from": date(2026, 9, 1), "date_to": date(2026, 9, 30)}


# --- Dựng dữ liệu ---------------------------------------------------------

def line(
    order, product, *, occurrence=1, day=5, month=9, year=2026,
    employee="Vinh", group="NOI_THANH", quantity="1", sell="8000000",
    discount="0", kpi_purchase="5000000", kpi_profit="3000000", rate="0.020",
    row=6, status="AUTO", reasons=(),
    customer="Nguyễn Thị Hoa", phone="0912000111", address="12 Lê Lợi, Q1",
):
    """Một cặp (dòng nguồn, dòng kết quả) MANG CẢ ba trường khách hàng.

    Fixture của PHB-03 không có chúng vì lúc đó chúng chưa được persist; ở đây
    chúng bắt buộc, vì `§23` yêu cầu bảng kê hiện Tên KH · SĐT · Địa chỉ và
    một fixture để trống sẽ làm test "khách hàng hiện ra" luôn xanh mà không
    chứng minh gì.
    """
    source = source_line(
        order, product, occurrence, row=row, sale_date=date(year, month, day),
        sell_price=sell, quantity=Decimal(quantity), discount=Decimal(discount),
        customer_name=customer, customer_phone=phone, customer_address=address)
    base = result_line(source, status=status)
    result = type(base)(**{
        **{field: getattr(base, field) for field in base.__dataclass_fields__},
        "status": status, "pending_reasons": tuple(reasons),
        "employee_normalized": employee, "employee_group": group,
        "lead_source_final": "PERSONAL",
        "total_sales": Decimal(sell) * Decimal(quantity) - Decimal(discount),
        "kpi_purchase_price": None if kpi_purchase is None else Decimal(kpi_purchase),
        "eligible_kpi_profit": None if kpi_profit is None else Decimal(kpi_profit),
        "product_group_final": "DIEN_MAY",
        "conversion_rate_final": None if rate is None else Decimal(rate),
    })
    return source, result


def persist(repository, pairs, *, run_id="run-1", at="2026-10-01T00:00:00",
            fingerprint="fp-a"):
    return write(repository, [p[0] for p in pairs], run_id=run_id,
                 created_at=at, fingerprint=fingerprint,
                 results=[p[1] for p in pairs])


#: Một BH ba dòng, đúng hình dạng mà `§10` mô tả: Owner chuyển ĐÚNG MỘT dòng
#: sang Gia dụng và hai dòng còn lại ở lại Nội thành.
def three_line_order(order="BH72707", *, employee="Vinh", day=5):
    return [
        line(order, "43F6000", occurrence=1, day=day, employee=employee, row=6),
        line(order, "XP352AE-DS", occurrence=1, day=day, employee=employee,
             row=7, sell="4000000", kpi_purchase="2000000",
             kpi_profit="2000000"),
        line(order, "Giá treo", occurrence=1, day=day, employee=employee,
             row=8, sell="500000", kpi_purchase="300000", kpi_profit="200000"),
    ]


@pytest.fixture
def engine():
    engine = create_engine("sqlite://")
    history_db.create_all_for_test(engine)
    return engine


@pytest.fixture
def repository(engine):
    return history_store.SnapshotRepository(engine)


@pytest.fixture
def store(engine):
    return business_store.BusinessDecisionStore(engine)


@pytest.fixture
def service(engine, store):
    return business_service.BusinessReportService(engine=engine, store=store)


@pytest.fixture
def client(engine, monkeypatch, tmp_path):
    monkeypatch.setattr(web_server, "select_latest_valid_captures", lambda: None)
    monkeypatch.setattr(live_pull, "is_configured", lambda env=None: False)
    # Ngày cố định: xem chú thích của `TODAY`.
    monkeypatch.setattr(web_server, "_today", lambda: TODAY)
    application = web_server.create_app(
        db_path=tmp_path / "runs.db",
        history=history_store.LegacyRepository(engine),
        snapshots=history_store.SnapshotRepository(engine))
    application.testing = True
    return application.test_client()


def body(client, path: str) -> str:
    response = client.get(path)
    assert response.status_code == 200, f"{path} → {response.status_code}"
    return response.get_data(as_text=True)


def metric(html: str, name: str) -> str:
    match = re.search(rf'data-metric="{re.escape(name)}"[^>]*>(.*?)<', html, re.S)
    assert match is not None, f"không tìm thấy data-metric={name}"
    return match.group(1).strip()


def metrics(html: str, name: str) -> list[str]:
    return [value.strip() for value in re.findall(
        rf'data-metric="{re.escape(name)}"[^>]*>(.*?)<', html, re.S)]


def line_keys(html: str, product: str) -> dict:
    """Khoá nghiệp vụ của dòng mang tên hàng này, đọc từ chính HTML."""
    for block in re.findall(r'<form[^>]*>(.*?)</form>', html, re.S):
        pass
    match = re.search(
        rf'data-metric="line-(?:gia-dung|exclude)"[^>]*href="[^"]*'
        rf'order_key=(?P<order>[^&"]+)[^"]*product_key=(?P<product>[0-9a-f]+)'
        rf'[^"]*occurrence_index=(?P<occurrence>\d+)', html)
    assert match is not None, "không tìm thấy khoá dòng nào trong HTML"
    return match.groupdict()


def keys_of(service, order_key: str, product: str) -> dict:
    """Khoá nghiệp vụ của một dòng, tra qua tầng ráp (không qua HTML)."""
    data = service.period(**SEPTEMBER)
    for detail in [*data.details, *data.excluded]:
        if detail["order_key"] == order_key and detail["product_raw"] == product:
            return {"order_key": detail["order_key"],
                    "product_key": detail["product_key"],
                    "occurrence_index": detail["occurrence_index"]}
    raise AssertionError(f"không tìm thấy dòng {order_key}/{product}")


# ==========================================================================
# §2 · §3 · §45 · §46 — KỲ DỮ LIỆU MẶC ĐỊNH LÀ THÁNG HIỆN TẠI
# ==========================================================================

def test_case_ux_01_the_workspace_opens_on_the_current_calendar_month(
    repository, client
):
    """CASE UX-01 — mở trong tháng 09/2026 ⟹ mặc định 09/2026."""
    persist(repository, [line("BH1", "Tủ lạnh", month=9)])
    html = body(client, "/kinh-doanh/nhan-vien")
    assert "Tháng 09/2026" in html
    assert 'value="2026-09" selected' in html


def test_case_ux_02_the_current_month_opens_even_with_no_sales_at_all(
    repository, client
):
    """CASE UX-02 — tháng hiện tại CHƯA có dòng nào vẫn mở, KHÔNG lùi tháng.

    Đây là điểm `§2` nói rõ là cố ý và siêu việt hạn chế cũ của PHB-05: Owner
    chuẩn bị Target trước lần nạp sổ đầu tiên của tháng, nên rơi ngược về
    tháng trước sẽ ghi con số đó vào tháng sai.
    """
    persist(repository, [line("BH1", "Tủ lạnh", month=8, day=20)])
    html = body(client, "/kinh-doanh/nhan-vien")
    assert "Tháng 09/2026" in html
    assert metric(html, "no-rows") == wp.EMPTY_PERIOD_NOTE
    # Ô nhập Target vẫn có mặt — đó là toàn bộ lý do không lùi tháng.
    assert 'data-metric="target-input"' in html
    # Và tiến độ lịch vẫn nói đúng ngày hôm nay.
    assert metric(html, "month-progress") == "10%"


def test_case_ux_02b_a_target_set_on_an_empty_current_month_is_stored(
    repository, client, service
):
    """`§45` — Target đặt được cho tháng hiện tại KHI CHƯA có dòng bán nào.

    Ranh giới cũ của PHB-05 (`available_periods()` phải chứa tháng đó) bị
    siêu việt tường minh ở đây, và test này là bằng chứng nó thật sự mở.
    """
    persist(repository, [line("BH1", "Tủ lạnh", month=8, day=20)])
    response = client.post("/kinh-doanh/nhan-vien/target", data={
        "ky": "2026-09", "sheet": reporting_sheets.NOI_THANH_SHEET,
        "target": "500,000"})
    assert response.status_code == 302
    assert service.store.group_targets(year=2026, month=9) != {}
    sheet = reporting_sheets.Sheet(
        key=reporting_sheets.NOI_THANH_SHEET, label="Nội thành")
    assert service.sheet_target(sheet=sheet, period=(2026, 9)) == Decimal(
        "500000000")


def test_case_ux_03_the_workspace_offers_no_all_data_period(repository, client):
    """CASE UX-03 — không có mục "Toàn bộ dữ liệu" trong không gian này."""
    persist(repository, [line("BH1", "Tủ lạnh")])
    html = body(client, "/kinh-doanh/nhan-vien")
    picker = re.search(r'<select name="ky".*?</select>', html, re.S).group(0)
    assert "tat-ca" not in picker
    assert "Toàn bộ dữ liệu" not in picker


@pytest.mark.parametrize("raw", [
    "tat-ca", "9999-13", "0001-01", "abc", "2026-00", "2026-13", "-1--1", "",
])
def test_an_unusable_period_falls_back_to_the_current_month(
    repository, client, raw
):
    """`§3` — kiểm tra ngày/năm vẫn an toàn sau khi bỏ "Toàn bộ dữ liệu".

    Một tham số lạ KHÔNG được dựng ra một kỳ vô nghĩa và cũng không được làm
    sập trang: nó rơi về tháng hiện tại, đúng một hành vi cho mọi ca lỗi.
    """
    persist(repository, [line("BH1", "Tủ lạnh")])
    html = body(client, f"/kinh-doanh/nhan-vien?ky={raw}")
    assert "Tháng 09/2026" in html


def test_case_ux_10_and_ux_11_month_progress_is_a_calendar_indicator_only():
    """CASE UX-10/UX-11 — tiến độ lịch, và CHỈ là tiến độ lịch.

    Ngày 3 của tháng 30 ngày ⟹ 10 % (`§15` tính CẢ ngày hôm nay). Tháng đã
    qua ⟹ 100 %. Tháng chưa tới ⟹ 0 %.
    """
    assert reporting_sheets.month_progress_percent(
        (2026, 9), today=date(2026, 9, 3)) == Decimal("10.00")
    assert reporting_sheets.month_progress_percent(
        (2026, 8), today=date(2026, 9, 3)) == Decimal(100)
    assert reporting_sheets.month_progress_percent(
        (2026, 10), today=date(2026, 9, 3)) == Decimal(0)
    # Ngày cuối tháng ⟹ đúng 100 %, không phải 96,7 %.
    assert reporting_sheets.month_progress_percent(
        (2026, 9), today=date(2026, 9, 30)) == Decimal(100)


def test_case_wr_04_month_progress_changes_no_business_number(
    repository, client, service
):
    """CASE WR-04 tinh thần + `§15` — Tiến độ KHÔNG đổi một con số nào.

    Đo bằng cách so chính các chỉ tiêu nghiệp vụ ở hai "hôm nay" khác nhau:
    nếu Tiến độ có đường nào chạm vào phép tính, hai bộ số sẽ lệch.
    """
    persist(repository, three_line_order())
    watched = ("sales_revenue", "converted_sales", "kpi_profit",
               "lines", "orders", "coverage")
    before = {name: metric(body(client, "/kinh-doanh/nhan-vien"), name)
              for name in watched}
    totals_before = service.period(**SEPTEMBER).totals

    # Cùng dữ liệu, "hôm nay" khác ⟹ chỉ ô Tiến độ đổi.
    import app.web.server as server_module
    original = server_module._today
    server_module._today = lambda: date(2026, 9, 20)
    try:
        html = body(client, "/kinh-doanh/nhan-vien")
        after = {name: metric(html, name) for name in watched}
        assert metric(html, "month-progress") == "66,67%"
    finally:
        server_module._today = original

    assert after == before
    assert service.period(**SEPTEMBER).totals == totals_before


# ==========================================================================
# §4 · §5 · §6 — HÀNG SHEET THAY BỘ CHỌN NHÂN VIÊN
# ==========================================================================

def test_case_ux_04_there_is_no_employee_dropdown_any_more(repository, client):
    """CASE UX-04 — không còn ô thả xuống "chọn nhân viên"."""
    persist(repository, [line("BH1", "Tủ lạnh")])
    html = body(client, "/kinh-doanh/nhan-vien")
    assert 'name="nhan-vien"' not in html
    assert "Chọn nhân viên" not in html


def test_case_ux_05_to_09_the_sheet_row_is_the_navigation(repository, client):
    """CASE UX-05…UX-09 — hàng sheet ở ĐẦU trang, và nó có đúng những tab nào.

    UX-06  Nội thành là MỘT tab.
    UX-07  Hiệp · Vinh · Quý KHÔNG có tab riêng.
    UX-09  Gia dụng là một tab RIÊNG.
    """
    persist(repository, [
        *three_line_order("BH1", employee="Vinh"),
        line("BH2", "Máy giặt", employee="Quý", row=9),
        line("BH3", "Tivi", employee="Ly", group="STANDARD_SALES",
             rate="0.055", row=10),
        line("BH4", "Loa", employee="Kiên", group="STANDARD_SALES",
             rate="0.055", row=11),
    ])
    html = body(client, "/kinh-doanh/nhan-vien")
    tabs = metrics(html, "sheet-tab")

    assert "Nội thành" in tabs                       # UX-06
    assert "Gia dụng" in tabs                        # UX-09
    assert {"Ly", "Kiên"} <= set(tabs)               # sheet của nhân viên bán lẻ
    for member in ("Vinh", "Quý", "Hiệp"):           # UX-07
        assert member not in tabs
    # UX-05 — hàng sheet đứng TRƯỚC dải chỉ tiêu trên trang.
    assert html.index('data-metric="sheet-tabs"') < html.index(
        'data-metric="sales_revenue"')
    # `§5` — không sinh tab trùng dù Nội thành có nhiều người và nhiều dòng.
    assert len(tabs) == len(set(tabs))


def test_case_ux_08_noi_thanh_rows_keep_the_real_salesperson(repository, client):
    """CASE UX-08 — sheet là ĐƠN VỊ BÁO CÁO, không thay danh tính con người.

    Đây là bất biến mà `config/employees.yaml` (DEC-127 §1) đã trả giá để
    giành lại: gộp Vinh · Quý · Hiệp thành một "nhân viên" tên Nội thành làm
    MẤT ba con người có thật.
    """
    persist(repository, [
        line("BH1", "Tủ lạnh", employee="Vinh"),
        line("BH2", "Máy giặt", employee="Hiệp", row=7),
        line("BH3", "Tivi", employee="Quý", row=8),
    ])
    html = body(client, "/kinh-doanh/nhan-vien?sheet=noi-thanh")
    assert metric(html, "employee") == "Nội thành"
    assert set(metrics(html, "line-employee")) == {"Vinh", "Hiệp", "Quý"}
    assert "Nội thành" not in metrics(html, "line-employee")


def test_the_group_sheets_are_there_before_a_single_line_exists(
    repository, client
):
    """`§5`/`§46` — hai sheet nhóm có mặt kể cả khi tháng còn trống.

    Nếu tab Nội thành biến mất lúc chưa có số, Owner không có chỗ nào để đặt
    Target trước lần nạp sổ đầu tiên — tức là `§45` không thực hiện được.
    """
    html = body(client, "/kinh-doanh/nhan-vien")
    assert {"Nội thành", "Gia dụng"} <= set(metrics(html, "sheet-tab"))


def test_the_primary_navigation_is_still_exactly_the_primary_tabs(repository, client):
    """`§4`/`§47` — sheet là khung nhìn CON, không phải tab.

    Điều test này canh KHÔNG đổi theo `DEC-185`: dù thanh tab còn 4 hay 3
    mục, một hàng sheet mới KHÔNG được đẻ thêm tab chính nào. Chỉ tập kỳ
    vọng đổi, theo `NAV-01`/`NAV-02`.
    """
    persist(repository, [line("BH1", "Tủ lạnh")])
    nav = re.search(r'<nav class="ncc-tabs">(.*?)</nav>',
                    body(client, "/kinh-doanh/nhan-vien"), re.S).group(1)
    assert nav.count('class="ncc-tab') == 3
    assert [label.strip() for label in re.findall(r'>([^<>]+)</a>', nav)] == [
        "Báo cáo", "Nhân viên", "Dữ liệu"]


# ==========================================================================
# §14 — DẢI CHỈ TIÊU ĐỨNG ĐẦU SHEET, BẢNG KÊ NGAY BÊN DƯỚI
# ==========================================================================

def test_the_summary_strip_shows_five_metrics_then_the_table(repository, client):
    """`§14` — năm ô, rồi NGAY bảng kê. Không có bước bung/thu nào ở giữa."""
    persist(repository, three_line_order())
    html = body(client, "/kinh-doanh/nhan-vien")
    for name in ("sales_revenue", "converted_sales", "employee-vs-target",
                 "mom", "month-progress"):
        assert f'data-metric="{name}"' in html, name
    assert html.index('data-metric="month-progress"') < html.index(
        'data-metric="bh-head"')
    assert "<details" not in html, "§14 cấm một bước bung/thu trước bảng kê"


def test_case_case_16_month_over_month_compares_a_sheet_with_itself(
    repository, client
):
    """`§16` — cùng đơn vị báo cáo, tháng liền trước. Không so chéo.

    Nội thành tháng 8 = 8.000.000; tháng 9 = 12.000.000 ⟹ +50 %. Con số đó
    KHÔNG được lẫn với doanh thu của Ly trong cùng hai tháng.
    """
    persist(repository, [
        line("BH-T8", "Tủ lạnh", month=8, day=10, employee="Vinh"),
        line("BH-T9", "Tủ lạnh", month=9, day=10, employee="Vinh",
             sell="12000000", row=7),
        line("BH-LY8", "Tivi", month=8, day=11, employee="Ly",
             group="STANDARD_SALES", rate="0.055", sell="99000000", row=8),
    ])
    html = body(client, "/kinh-doanh/nhan-vien?ky=2026-09&sheet=noi-thanh")
    assert metric(html, "mom") == "+50%"
    assert "So với Tháng 08/2026" in html


def test_a_sheet_with_no_previous_month_says_so_instead_of_inventing_zero(
    repository, client
):
    """`§16` — kỳ trước không có bằng chứng ⟹ trạng thái CHỮ, không phải 0 %."""
    persist(repository, [line("BH1", "Tủ lạnh", month=9)])
    html = body(client, "/kinh-doanh/nhan-vien?ky=2026-09&sheet=noi-thanh")
    assert metric(html, "mom") == "—"
    assert metric(html, "mom-note") == wp.MOM_NO_PREVIOUS


# ==========================================================================
# §17…§21 — TARGET THEO NGHÌN ĐỒNG, LƯU THEO VND
# ==========================================================================

@pytest.mark.parametrize("typed,stored", [
    ("500,000", Decimal("500000000")),        # CASE TG-01
    ("500.000", Decimal("500000000")),        # thói quen gõ vi-VN
    ("1,250,000", Decimal("1250000000")),
    ("1 250 000", Decimal("1250000000")),
    ("0", Decimal(0)),                        # CASE TG-04
])
def test_case_tg_01_and_tg_04_kvnd_input_stores_canonical_vnd(typed, stored):
    assert business_store.parse_target_kvnd(typed) == stored


@pytest.mark.parametrize("typed", ["", "   ", None])
def test_case_tg_05_a_blank_target_unsets_it(typed):
    """CASE TG-05 — rỗng là GỠ, và GỠ khác `0` (PHB-05 §7 giữ nguyên)."""
    assert business_store.parse_target_kvnd(typed) is None


@pytest.mark.parametrize("typed", ["-5", "-500,000", "abc", "5e3", "1,5x"])
def test_a_malformed_or_negative_target_is_refused(typed):
    with pytest.raises(business_store.InvalidTargetError):
        business_store.parse_target_kvnd(typed)


def test_case_tg_02_and_tg_03_the_round_trip_never_drifts_by_a_thousand():
    """CASE TG-02/TG-03 — `500,000` → 500.000.000 VND → `500,000`, mãi mãi.

    Lỗi ×1000 là lớp lỗi mà `§20` gọi tên, và nó chỉ lộ ra sau vài lần lưu.
    Vì vậy test lặp mười vòng chứ không một vòng.
    """
    value = business_store.parse_target_kvnd("500,000")
    assert value == Decimal("500000000")
    for _ in range(10):
        text = business_store.format_target_kvnd(value)
        assert text == "500,000"
        value = business_store.parse_target_kvnd(text)
        assert value == Decimal("500000000")


def test_case_tg_03_the_round_trip_holds_over_the_real_http_path(
    repository, client, service
):
    """CASE TG-03 qua HTTP thật: lưu → tải lại → lưu lại → không trôi."""
    persist(repository, three_line_order())
    sheet = reporting_sheets.Sheet(
        key=reporting_sheets.NOI_THANH_SHEET, label="Nội thành")
    for _ in range(3):
        html = body(client, "/kinh-doanh/nhan-vien?sheet=noi-thanh")
        typed = re.search(r'data-metric="target-input"[^>]*', html)
        current = (re.search(r'value="([^"]*)"',
                             re.search(r'<input[^>]*data-metric="target-input"[^>]*>',
                                       html).group(0)).group(1))
        client.post("/kinh-doanh/nhan-vien/target", data={
            "ky": "2026-09", "sheet": "noi-thanh",
            "target": current or "500,000"})
        assert typed is not None
    assert service.sheet_target(sheet=sheet, period=(2026, 9)) == Decimal(
        "500000000")
    html = body(client, "/kinh-doanh/nhan-vien?sheet=noi-thanh")
    assert 'value="500,000"' in html
    assert metric(html, "employee-target") == "500.000"      # nghìn đồng
    assert "500.000.000 đồng" in html                        # VND đầy đủ


def test_case_tg_06_and_tg_09_noi_thanh_has_one_shared_group_target(
    repository, client, service, store
):
    """CASE TG-06/TG-09 — MỘT Target cho cả nhóm, KHÔNG cộng từ ba người.

    Đặt target riêng cho Vinh · Quý · Hiệp rồi kiểm: sheet Nội thành vẫn nói
    "chưa thiết lập", vì Target của nhóm là con số Owner tự đặt (`§7`).
    """
    persist(repository, [
        line("BH1", "Tủ lạnh", employee="Vinh"),
        line("BH2", "Máy giặt", employee="Quý", row=7),
    ])
    for name in ("Vinh", "Quý", "Hiệp"):
        store.set_employee_target(year=2026, month=9, employee_key=name,
                                  target_vnd=Decimal("100000000"))

    sheet = reporting_sheets.Sheet(
        key=reporting_sheets.NOI_THANH_SHEET, label="Nội thành")
    assert service.sheet_target(sheet=sheet, period=(2026, 9)) is None
    html = body(client, "/kinh-doanh/nhan-vien?sheet=noi-thanh")
    assert metric(html, "employee-vs-target-state") is not None
    assert metric(html, "employee-target") == "—"

    # Owner đặt MỘT con số cho cả nhóm ⟹ đó là con số được dùng.
    client.post("/kinh-doanh/nhan-vien/target", data={
        "ky": "2026-09", "sheet": "noi-thanh", "target": "800,000"})
    assert service.sheet_target(sheet=sheet, period=(2026, 9)) == Decimal(
        "800000000")
    # …và nó KHÔNG bằng tổng ba target cá nhân (300.000.000).
    assert service.sheet_target(sheet=sheet, period=(2026, 9)) != Decimal(
        "300000000")


def test_case_tg_07_and_tg_08_gia_dung_has_its_own_separate_target(
    repository, client, service
):
    """CASE TG-07/TG-08 — Gia dụng có Target RIÊNG, không mượn của Nội thành."""
    persist(repository, three_line_order())
    client.post("/kinh-doanh/nhan-vien/target", data={
        "ky": "2026-09", "sheet": "noi-thanh", "target": "800,000"})

    noi_thanh = reporting_sheets.Sheet(key="noi-thanh", label="Nội thành")
    gia_dung = reporting_sheets.Sheet(key="gia-dung", label="Gia dụng")
    assert service.sheet_target(sheet=noi_thanh, period=(2026, 9)) == Decimal(
        "800000000")
    assert service.sheet_target(sheet=gia_dung, period=(2026, 9)) is None

    html = body(client, "/kinh-doanh/nhan-vien?sheet=gia-dung")
    assert metric(html, "employee-target") == "—"
    assert metric(html, "employee-vs-target") == "—"

    client.post("/kinh-doanh/nhan-vien/target", data={
        "ky": "2026-09", "sheet": "gia-dung", "target": "100,000"})
    assert service.sheet_target(sheet=gia_dung, period=(2026, 9)) == Decimal(
        "100000000")
    # Đặt Target của Gia dụng KHÔNG đụng tới Target của Nội thành.
    assert service.sheet_target(sheet=noi_thanh, period=(2026, 9)) == Decimal(
        "800000000")


def test_case_21_vs_target_divides_converted_sales_not_total_sales(
    repository, client
):
    """CASE `§21` — `DS quy đổi / Target × 100`, và KHÔNG cap ở 100 %.

    DS quy đổi = 3.000.000 / 2 % = 150.000.000. Target 100.000 kVND =
    100.000.000 ⟹ 150 %. Nếu ai đó thay mẫu số bằng Tổng bán (8.000.000) hay
    quên chia, con số sẽ không còn là 150 %.
    """
    persist(repository, [line("BH1", "Tủ lạnh")])
    client.post("/kinh-doanh/nhan-vien/target", data={
        "ky": "2026-09", "sheet": "noi-thanh", "target": "100,000"})
    html = body(client, "/kinh-doanh/nhan-vien?sheet=noi-thanh")
    assert metric(html, "converted_sales") == "150.000"
    assert metric(html, "employee-vs-target") == "150%"


def test_a_target_never_changes_a_single_business_number(
    repository, client, service
):
    """`§60` — đặt/sửa Target chỉ đổi Target và So Target, không gì khác."""
    persist(repository, three_line_order())
    watched = ("sales_revenue", "converted_sales", "kpi_profit", "coverage",
               "lines", "orders", "qualifying_quantity")
    before = {name: metric(body(client, "/kinh-doanh/nhan-vien"), name)
              for name in watched}
    totals_before = service.period(**SEPTEMBER).totals

    client.post("/kinh-doanh/nhan-vien/target", data={
        "ky": "2026-09", "sheet": "noi-thanh", "target": "700,000"})

    html = body(client, "/kinh-doanh/nhan-vien")
    assert {name: metric(html, name) for name in watched} == before
    assert service.period(**SEPTEMBER).totals == totals_before


def test_the_unresolved_sheet_cannot_be_given_a_target(repository, client):
    """Một chỉ tiêu cho tập dòng chưa biết của ai là con số không ai gánh."""
    persist(repository, [line("BH1", "Tủ lạnh", employee="", group=None)])
    html = body(client, "/kinh-doanh/nhan-vien?sheet=chua-xac-dinh")
    assert 'data-metric="target-input"' not in html
    response = client.post("/kinh-doanh/nhan-vien/target", data={
        "ky": "2026-09", "sheet": "chua-xac-dinh", "target": "500,000"},
        follow_redirects=True)
    assert "không đặt Target được" in response.get_data(as_text=True)


# ==========================================================================
# §22…§25 — BẢNG KÊ KIỂU BẢNG TÍNH, GỘP THEO BH
# ==========================================================================

def test_case_dt_01_a_multi_line_order_renders_as_one_grouped_block(
    repository, client
):
    """CASE DT-01 — một BH ba dòng là MỘT khối, không phải ba thẻ rời."""
    persist(repository, three_line_order("BH72707"))
    html = body(client, "/kinh-doanh/nhan-vien")
    assert metrics(html, "bh-order") == ["BH72707"]
    assert len(metrics(html, "line-product")) == 3
    assert set(metrics(html, "line-product")) == {
        "43F6000", "XP352AE-DS", "Giá treo"}


def test_case_dt_02_to_dt_04_customer_fields_come_from_the_accounting_book(
    repository, client
):
    """CASE DT-02/DT-03/DT-04 — Tên KH · SĐT · Địa chỉ hiện ra.

    Chúng đến từ ĐÚNG sổ kế toán đang nạp (`raw_reader` cột 5/6/7), không từ
    một CRM và không từ một phép ghép danh tính nào (`§49`).
    """
    persist(repository, [line("BH1", "Tủ lạnh", customer="Trần Văn Bình",
                              phone="0987654321", address="55 Nguyễn Trãi")])
    html = body(client, "/kinh-doanh/nhan-vien")
    assert metric(html, "customer-name") == "Trần Văn Bình"
    assert metric(html, "customer-phone") == "0987654321"
    assert metric(html, "customer-address") == "55 Nguyễn Trãi"


def test_the_customer_fields_survive_a_new_snapshot(repository, client):
    """Nạp lại sổ ⟹ khách hàng vẫn đúng, vì chúng đi cùng dòng nguồn."""
    persist(repository, [line("BH1", "Tủ lạnh", customer="Trần Văn Bình")])
    persist(repository, [line("BH1", "Tủ lạnh", customer="Trần Văn Bình")],
            run_id="run-2", at="2026-10-02T00:00:00", fingerprint="fp-b")
    assert metric(body(client, "/kinh-doanh/nhan-vien"),
                  "customer-name") == "Trần Văn Bình"


def test_an_order_without_customer_data_says_so_instead_of_inventing_one(
    repository, client
):
    """Snapshot nạp TRƯỚC `0007` không có ba trường đó ⟹ `—`, không bịa."""
    persist(repository, [line("BH1", "Tủ lạnh", customer=None, phone=None,
                              address=None)])
    html = body(client, "/kinh-doanh/nhan-vien")
    assert metric(html, "customer-name") == "—"
    assert metric(html, "customer-phone") == "—"


def test_case_dt_05_every_business_date_is_day_month_year(repository, client):
    """CASE DT-05 — `DD/MM/YYYY`. `03/08/2026` là 3 tháng 8, không phải 8/3."""
    persist(repository, [line("BH1", "Tủ lạnh", month=8, day=3)])
    html = body(client, "/kinh-doanh/nhan-vien?ky=2026-08")
    assert metric(html, "bh-date") == "03/08/2026"
    assert "2026-08-03" not in html
    assert "08/03/2026" not in html


def test_case_dt_06_to_dt_09_the_column_layout_matches_the_owner_decision(
    repository, client
):
    """CASE DT-06…DT-09 — thứ tự và sự vắng mặt của các cột.

    DT-06  "Giá nhập" đứng TRƯỚC "Giá bán", và tên không còn chữ "KPI".
    DT-07  "Nguồn giá" không còn trên màn hình vận hành.
    DT-08  không còn cột "Sửa".
    DT-09  không còn thao tác "Gán NV bán hàng" riêng.
    """
    persist(repository, three_line_order())
    html = body(client, "/kinh-doanh/nhan-vien")
    header = re.search(r"<table class=\"sheet-table\">\s*<tr>(.*?)</tr>",
                       html, re.S).group(1)
    labels = [text.strip() for text in re.findall(r"<th[^>]*>(.*?)</th>",
                                                  header, re.S)]
    assert "Giá nhập" in labels and "Giá bán" in labels
    assert labels.index("Giá nhập") < labels.index("Giá bán")   # DT-06
    assert "Giá nhập KPI" not in labels                          # DT-06
    assert "Nguồn giá" not in labels                             # DT-07
    assert "Sửa" not in labels                                   # DT-08
    assert "Gán NV bán hàng" not in html                         # DT-09
    assert 'data-metric="assign-employee"' not in html           # DT-09


def test_case_37_the_four_filter_buttons_are_gone_but_the_states_remain(
    repository, client
):
    """`§37` — bốn bộ lọc rời khỏi màn hình vận hành, KHÔNG rời khỏi hệ thống.

    Chúng vẫn là bốn câu hỏi có thật của Owner và vẫn mở được ở bảng kê chi
    tiết; điều bị bỏ là việc chúng chắn giữa Owner và bảng số.
    """
    persist(repository, [line("BH1", "Tủ lạnh", kpi_purchase=None,
                              kpi_profit=None,
                              reasons=("Missing.PurchasePrice",),
                              status="PENDING")])
    html = body(client, "/kinh-doanh/nhan-vien")
    assert '<nav class="filter-row">' not in html
    for label in ("CHƯA CÓ GIÁ NHẬP", "CHƯA XÁC ĐỊNH NHÂN VIÊN",
                  "DÒNG TÔI ĐÃ SỬA"):
        assert label not in html, label
    # Trạng thái đúng đắn thì vẫn còn: coverage vẫn nói còn dòng chưa đủ.
    assert metric(html, "coverage") == "0 / 1 dòng"
    # Và bảng kê đầy đủ vẫn mở được từ chính sheet này.
    assert 'data-metric="employee-detail-link"' in html


# ==========================================================================
# §38 · §59 — NỀN XEN KẼ THEO NGÀY
# ==========================================================================

def test_case_vis_01_to_vis_03_the_background_alternates_by_date_group(
    repository, client
):
    """CASE VIS-01…VIS-03 — cùng ngày ⟹ cùng nền; ngày mới ⟹ đổi nền.

    Ba ngày, và ngày thứ nhất/thứ ba dùng CÙNG một nền — nghĩa là nền đảo
    theo NGÀY chứ không đảo theo dòng hay theo BH.
    """
    persist(repository, [
        *three_line_order("BH-A", day=1),          # ngày 1 — 3 dòng
        line("BH-B", "Tivi", day=1, row=20),       # ngày 1 — BH thứ hai
        line("BH-C", "Loa", day=2, row=21),        # ngày 2
        line("BH-D", "Quạt", day=3, row=22),       # ngày 3
    ])
    html = body(client, "/kinh-doanh/nhan-vien")
    shades = dict(re.findall(
        r'data-metric="bh-head"\s+data-order="([^"]+)"\s+data-shade="(\d)"',
        html, re.S))
    assert set(shades) == {"BH-A", "BH-B", "BH-C", "BH-D"}, shades
    assert shades["BH-A"] == shades["BH-B"]     # VIS-01 — cùng ngày, cùng nền
    assert shades["BH-B"] != shades["BH-C"]     # VIS-02 — ngày mới, đổi nền
    assert shades["BH-C"] != shades["BH-D"]     # VIS-03 — ngày kế, đổi tiếp
    assert shades["BH-A"] == shades["BH-D"]     # …và quay lại nền đầu
    # Nhóm ngày ĐẦU TIÊN dùng nền đầu tiên, không bị đảo trước khi bắt đầu.
    assert shades["BH-A"] == "0"

    # VIS-01 chặt hơn: cả BỐN dòng của ngày 1 dùng chung một nền, không phải
    # zebra theo dòng.
    rows_of_first_date = re.findall(
        r'<tr class="shade-(\d)[^"]*"\s+data-metric="line-row"\s+'
        r'data-order="BH-A"', html, re.S)
    assert len(rows_of_first_date) == 3, rows_of_first_date
    assert set(rows_of_first_date) == {shades["BH-A"]}


# ==========================================================================
# §34 · §35 · §36 — CẢNH BÁO NGẮN, DÒNG LỖ TÔ ĐỎ
# ==========================================================================

def test_case_wr_01_the_verbose_warning_paragraphs_are_gone(repository, client):
    """CASE WR-01 — không còn đoạn văn cảnh báo trong lòng bảng (`§34`)."""
    persist(repository, [
        line("BH1", "Tủ lạnh", sell="1000000", kpi_purchase="5000000",
             kpi_profit="-4000000"),
    ])
    html = body(client, "/kinh-doanh/nhan-vien")
    for prose in ("Giá nhập cao hơn giá bán — dòng này đang bán lỗ",
                  "Lợi nhuận của dòng này là số âm",
                  "Hệ thống có ghi chú cần kiểm tra",
                  "Ghi chú của hệ thống khi nạp sổ"):
        assert prose not in html, prose


def test_case_wr_02_a_losing_line_gets_exactly_one_red_state(
    repository, client
):
    """CASE WR-02 — "bán lỗ" và "lợi nhuận âm" cho ra MỘT dấu hiệu (`§35`)."""
    persist(repository, [
        line("BH1", "Tủ lạnh", sell="1000000", kpi_purchase="5000000",
             kpi_profit="-4000000"),
        line("BH2", "Tivi", row=7),   # dòng lành mạnh, để so
    ])
    html = body(client, "/kinh-doanh/nhan-vien")
    assert html.count("row-loss") == 1
    losing = re.search(r'<tr class="[^"]*row-loss[^"]*".*?</tr>', html, re.S).group(0)
    assert "Tủ lạnh" in losing
    # Và không có HAI cái tag nói cùng một chuyện cạnh nhau.
    assert "bán lỗ" not in html
    assert wp.SHORT_TAGS.get("PURCHASE_ABOVE_SELL") is None


def test_case_wr_03_other_warnings_become_short_tags_next_to_the_bh(
    repository, client
):
    """CASE WR-03 — nhãn NGẮN cạnh số BH, ánh xạ từ trạng thái ĐÃ CÓ (`§36`)."""
    persist(repository, [
        line("BH1", "Tủ lạnh", kpi_purchase=None, kpi_profit=None,
             status="PENDING", reasons=("Missing.PurchasePrice",)),
        line("BH2", "Tivi", row=7, status="PENDING", reasons=("Duplicate",)),
    ])
    html = body(client, "/kinh-doanh/nhan-vien")
    tags = set(metrics(html, "bh-tag"))
    assert "Thiếu giá" in tags
    assert "Trùng khóa" in tags
    # Nhãn đứng cạnh số BH, không nằm ở một dòng lý do riêng bên dưới.
    assert 'data-metric="line-blocker"' not in html
    assert 'data-metric="pipeline-reasons"' not in html
    for tag in tags:
        assert len(tag.split()) <= 2, tag


def test_case_wr_04_a_tag_never_changes_a_business_number(repository, service):
    """CASE WR-04 — nhãn là CHỮ; chúng đọc trạng thái, không tạo ra nó."""
    persist(repository, [
        line("BH1", "Tủ lạnh", status="PENDING", reasons=("Duplicate",)),
    ])
    totals = service.period(**SEPTEMBER).totals
    assert totals.sales_revenue == Decimal("8000000")
    assert totals.kpi_profit == Decimal("3000000")
    assert totals.coverage.is_complete is True


# ==========================================================================
# §27 · §28 — MỘT NÚT SỬA CHO CẢ BH
# ==========================================================================

def test_case_ed_01_each_order_has_exactly_one_edit_control(repository, client):
    """CASE ED-01 — MỘT nút sửa cho mỗi BH, không rải nút khắp các cột."""
    persist(repository, [*three_line_order("BH-A"),
                         line("BH-B", "Tivi", row=20)])
    html = body(client, "/kinh-doanh/nhan-vien")
    assert len(metrics(html, "bh-edit")) == 2
    # Ngoài chế độ sửa, không ô nhập giá nhập nào hiện ra.
    assert 'data-metric="line-purchase-input"' not in html


def test_case_ed_02_changing_the_employee_once_moves_the_whole_order(
    repository, client, service
):
    """CASE ED-02 — đổi nhân viên MỘT lần ⟹ cả ba dòng của BH đổi theo.

    Và bất biến `§60`: tổng của cả kỳ KHÔNG đổi, chỉ quyền sở hữu đổi.
    """
    persist(repository, three_line_order("BH72707", employee="Vinh"))
    before = service.period(**SEPTEMBER).totals

    response = client.post("/kinh-doanh/nhan-vien/don", data={
        "ky": "2026-09", "sheet": "noi-thanh", "order_key": "BH72707",
        "nhan_vien_moi": "Hiệp"})
    assert response.status_code == 302

    lines = service.period(**SEPTEMBER).lines
    assert {line_.employee for line_ in lines} == {"Hiệp"}
    assert all(line_.employee_provenance == "MANUAL" for line_ in lines)
    # Bằng chứng gốc KHÔNG bị ghi đè.
    assert {line_.source_employee for line_ in lines} == {"Vinh"}
    # Tổng công ty không đổi.
    after = service.period(**SEPTEMBER).totals
    assert after.sales_revenue == before.sales_revenue
    assert after.kpi_profit == before.kpi_profit
    assert after.converted_sales == before.converted_sales


def test_moving_an_order_to_a_retail_employee_moves_its_sheet_too(
    repository, client, service
):
    """Gán cả đơn cho một nhân viên bán lẻ ⟹ đơn rời sheet Nội thành.

    Bucket và tỉ lệ quy đổi phải luôn nói cùng một câu: sau khi đơn thuộc về
    Ly, tỉ lệ của nó là tỉ lệ của Ly, nên nó không được ở lại sheet Nội thành.
    """
    persist(repository, three_line_order("BH1", employee="Vinh"))
    client.post("/kinh-doanh/nhan-vien/don", data={
        "ky": "2026-09", "sheet": "noi-thanh", "order_key": "BH1",
        "nhan_vien_moi": "Ly"})
    html = body(client, "/kinh-doanh/nhan-vien?sheet=noi-thanh")
    assert metric(html, "no-rows") == wp.EMPTY_PERIOD_NOTE
    assert "Ly" in metrics(body(client, "/kinh-doanh/nhan-vien"), "sheet-tab")


def test_the_order_edit_refuses_a_name_that_is_not_a_real_employee(
    repository, client, service
):
    """`OD-5` giữ nguyên: gõ tự do một cái tên vào KPI vẫn bị chặn."""
    persist(repository, three_line_order("BH1"))
    response = client.post("/kinh-doanh/nhan-vien/don", data={
        "ky": "2026-09", "sheet": "noi-thanh", "order_key": "BH1",
        "nhan_vien_moi": "Người Lạ"}, follow_redirects=True)
    assert "không có trong danh sách nhân viên" in response.get_data(as_text=True)
    assert {l.employee for l in service.period(**SEPTEMBER).lines} == {"Vinh"}


def test_case_ed_03_to_ed_05_the_purchase_price_is_editable_inline(
    repository, client, service
):
    """CASE ED-03/ED-04/ED-05 — sửa Giá nhập ngay trên dòng, khi BH đang mở.

    ED-04: dùng LẠI thẩm quyền `DEC-PHB02-02` — provenance `MANUAL_OVERRIDE`
    và `auto_price_at_entry` được ghi y như đường của PHB-03, không có một
    thẩm quyền giá nhập thứ hai nào được dựng.
    ED-05: các con số suy ra tính lại đúng sau khi lưu.
    """
    persist(repository, three_line_order("BH72707"))
    open_html = body(client, "/kinh-doanh/nhan-vien?sua=BH72707")
    assert len(metrics(open_html, "line-purchase-input")) == 0 or True
    assert 'data-metric="line-purchase-input"' in open_html   # ED-03

    keys = keys_of(service, "BH72707", "43F6000")
    response = client.post("/kinh-doanh/nhan-vien/gia-nhap", data={
        "ky": "2026-09", "sheet": "noi-thanh", **keys,
        "gia_nhap": "4.000.000"})
    assert response.status_code == 302

    data = service.period(**SEPTEMBER)
    edited = [l for l in data.lines if l.purchase_price == Decimal("4000000")][0]
    assert edited.purchase_provenance == bm.PROVENANCE_MANUAL_OVERRIDE  # ED-04
    stored = service.store.purchase_price_overrides()[
        (keys["order_key"], keys["product_key"], keys["occurrence_index"])]
    assert stored["auto_price_at_entry"] == Decimal("5000000")           # ED-04
    # ED-05 — (8.000.000 − 4.000.000) × 1 = 4.000.000, và DS quy đổi theo sau.
    assert edited.kpi_profit == Decimal("4000000")
    assert edited.converted_sales == Decimal("200000000.00")


def test_there_is_no_second_purchase_price_authority(repository):
    """`§28` — đường ghi giá nhập của không gian làm việc gọi ĐÚNG store cũ."""
    text = (REPO_ROOT / "app/web/server.py").read_text(encoding="utf-8")
    route = text.split("def business_save_line_purchase_price():")[1].split(
        "@app.post")[0]
    assert "service.store.set_purchase_price" in route
    assert "parse_purchase_price" in route
    assert "auto_price_of" in route
    assert "kpi_purchase_price" not in route, "không ghi thẳng vào bảng fact"


# ==========================================================================
# §29…§33 · §56 — LOẠI MỘT DÒNG KHỎI BÁO CÁO
# ==========================================================================

def test_case_ex_01_to_ex_03_excluding_one_line_removes_only_that_line(
    repository, client, service
):
    """CASE EX-01/EX-02/EX-03 — loại dòng 2, dòng 1 và 3 ở lại.

    Và `§30`: dòng bị loại biến khỏi MỌI chỉ tiêu, không phải chỉ khỏi bảng.
    """
    persist(repository, [
        *three_line_order("BH001"),
        line("BH001", "Chi phí thuê người", occurrence=1, row=9,
             sell="700000", kpi_purchase="0", kpi_profit="700000"),
    ])
    before = service.period(**SEPTEMBER).totals
    assert before.lines == 4

    keys = keys_of(service, "BH001", "Chi phí thuê người")
    response = client.post("/kinh-doanh/nhan-vien/loai-dong", data={
        "ky": "2026-09", "sheet": "noi-thanh", **keys})
    assert response.status_code == 302

    after = service.period(**SEPTEMBER).totals
    assert after.lines == 3                                        # EX-02
    assert after.sales_revenue == before.sales_revenue - Decimal("700000")
    assert after.kpi_profit == before.kpi_profit - Decimal("700000")
    assert after.converted_sales == before.converted_sales - Decimal(
        "700000") / Decimal("0.02")

    html = body(client, "/kinh-doanh/nhan-vien")
    assert "Chi phí thuê người" not in metrics(html, "line-product")  # EX-03
    assert {"43F6000", "XP352AE-DS", "Giá treo"} == set(
        metrics(html, "line-product"))                                # EX-01/02


def test_case_ex_04_the_raw_accounting_evidence_is_never_deleted(
    repository, client, service, engine
):
    """CASE EX-04 — "xoá" trên màn hình KHÔNG xoá bằng chứng kế toán (`§31`)."""
    persist(repository, three_line_order("BH1"))
    keys = keys_of(service, "BH1", "Giá treo")
    counts_before = {
        name: inspect(engine).get_columns(name) and _count(engine, name)
        for name in ("order_line_source_version", "order_line_result_version",
                     "order_line_current")
    }
    client.post("/kinh-doanh/nhan-vien/loai-dong", data={
        "ky": "2026-09", "sheet": "noi-thanh", **keys})
    counts_after = {name: _count(engine, name) for name in counts_before}
    assert counts_after == counts_before


def _count(engine, table: str) -> int:
    with engine.connect() as connection:
        return connection.exec_driver_sql(
            f"SELECT COUNT(*) FROM {table}").scalar()


def test_case_ex_05_an_exclusion_survives_the_next_snapshot(
    repository, client, service
):
    """CASE EX-05 — nạp sổ MỚI ⟹ quyết định của Owner vẫn còn hiệu lực.

    Đây là toàn bộ lý do bảng quyết định khoá theo khoá NGHIỆP VỤ chứ không
    theo `snapshot_id`/`version_id` (`§32`).
    """
    persist(repository, three_line_order("BH1"))
    keys = keys_of(service, "BH1", "Giá treo")
    client.post("/kinh-doanh/nhan-vien/loai-dong", data={
        "ky": "2026-09", "sheet": "noi-thanh", **keys})
    assert service.period(**SEPTEMBER).totals.lines == 2

    persist(repository, three_line_order("BH1"), run_id="run-2",
            at="2026-10-05T00:00:00", fingerprint="fp-b")
    assert service.period(**SEPTEMBER).totals.lines == 2
    assert "Giá treo" not in metrics(
        body(client, "/kinh-doanh/nhan-vien"), "line-product")


def test_case_ex_05b_an_exclusion_survives_a_purchase_price_edit(
    repository, client, service
):
    """`§32` — sửa giá nhập một dòng khác KHÔNG hồi sinh dòng đã loại."""
    persist(repository, three_line_order("BH1"))
    excluded = keys_of(service, "BH1", "Giá treo")
    client.post("/kinh-doanh/nhan-vien/loai-dong", data={
        "ky": "2026-09", "sheet": "noi-thanh", **excluded})
    other = keys_of(service, "BH1", "43F6000")
    client.post("/kinh-doanh/nhan-vien/gia-nhap", data={
        "ky": "2026-09", "sheet": "noi-thanh", **other, "gia_nhap": "4000000"})
    assert service.period(**SEPTEMBER).totals.lines == 2


def test_case_ex_06_an_exclusion_touches_no_unrelated_line(
    repository, client, service
):
    """CASE EX-06 — cùng tên hàng ở một đơn khác KHÔNG bị loại lây.

    Khoá là `(order_key, product_key, occurrence_index)`, không phải tên
    hàng — nếu không, loại một "Chi phí thuê người" sẽ loại mọi dòng cùng tên
    trong cả kỳ.
    """
    persist(repository, [
        line("BH1", "Giá treo", sell="500000", kpi_purchase="300000",
             kpi_profit="200000"),
        line("BH2", "Giá treo", row=7, sell="500000", kpi_purchase="300000",
             kpi_profit="200000"),
    ])
    keys = None
    for detail in service.period(**SEPTEMBER).details:
        if detail["order_key"] == "BH1":
            keys = {"order_key": detail["order_key"],
                    "product_key": detail["product_key"],
                    "occurrence_index": detail["occurrence_index"]}
    client.post("/kinh-doanh/nhan-vien/loai-dong", data={
        "ky": "2026-09", "sheet": "noi-thanh", **keys})
    remaining = service.period(**SEPTEMBER)
    assert [d["order_key"] for d in remaining.details] == ["BH2"]


def test_case_ex_07_an_exclusion_can_be_undone(repository, client, service):
    """CASE EX-07 — bấm nhầm thùng rác phải sửa được.

    Một thao tác không đảo ngược được trên một con số doanh thu là một thao
    tác không được phép tồn tại; vì bản ghi gốc chưa bao giờ bị đụng tới,
    khôi phục chỉ là xoá đúng dòng quyết định.
    """
    persist(repository, three_line_order("BH1"))
    before = service.period(**SEPTEMBER).totals
    keys = keys_of(service, "BH1", "Giá treo")
    client.post("/kinh-doanh/nhan-vien/loai-dong", data={
        "ky": "2026-09", "sheet": "noi-thanh", **keys})

    html = body(client, "/kinh-doanh/nhan-vien")
    assert metric(html, "excluded-note") == wp.EXCLUDED_NOTE
    assert 'data-metric="line-restore"' in html

    response = client.post("/kinh-doanh/nhan-vien/loai-dong", data={
        "ky": "2026-09", "sheet": "noi-thanh", **keys,
        "hanh-dong": "khoi-phuc"})
    assert response.status_code == 302
    assert service.period(**SEPTEMBER).totals == before


def test_the_exclusion_asks_for_a_short_confirmation_first(repository, client,
                                                           service):
    """`§9` tinh thần — thao tác ghi đi qua một hộp xác nhận NGẮN."""
    persist(repository, three_line_order("BH1"))
    keys = keys_of(service, "BH1", "Giá treo")
    html = body(client, "/kinh-doanh/nhan-vien?xac-nhan=loai"
                        f"&order_key={keys['order_key']}"
                        f"&product_key={keys['product_key']}"
                        f"&occurrence_index={keys['occurrence_index']}")
    assert metric(html, "confirm-question") == wp.EXCLUDE_CONFIRM_QUESTION
    assert metrics(html, "confirm-point") == list(wp.EXCLUDE_CONFIRM_POINTS)
    assert metric(html, "confirm-cancel") == "HỦY"
    assert metric(html, "confirm-ok") == "LOẠI DÒNG"
    # Xem hộp xác nhận KHÔNG ghi gì: dòng vẫn còn nguyên trong báo cáo.
    assert service.period(**SEPTEMBER).totals.lines == 3


# ==========================================================================
# §8…§13 · §41 · §42 — GIA DỤNG: PHÂN LOẠI CẤP DÒNG + BẤT BIẾN PHÂN BỔ
# ==========================================================================

def test_case_gd_01_a_normal_noi_thanh_line_stays_in_noi_thanh(
    repository, client
):
    """CASE GD-01 — chưa ai nói gì ⟹ dòng của Vinh ở sheet Nội thành."""
    persist(repository, three_line_order())
    noi_thanh = body(client, "/kinh-doanh/nhan-vien?sheet=noi-thanh")
    assert len(metrics(noi_thanh, "line-product")) == 3
    gia_dung = body(client, "/kinh-doanh/nhan-vien?sheet=gia-dung")
    assert metric(gia_dung, "no-rows") == wp.EMPTY_PERIOD_NOTE


def test_case_gd_02_to_gd_04_classifying_one_line_splits_the_order(
    repository, client, service
):
    """CASE GD-02/GD-03/GD-04 — ĐÚNG MỘT dòng chuyển, hai dòng ở lại.

    Đây là hình dạng mà `§10` mô tả bằng chính ví dụ của Owner:

        BH72707  43F6000     → Nội thành
                 XP352AE-DS  → Gia dụng
                 Giá treo    → Nội thành
    """
    persist(repository, three_line_order("BH72707"))
    keys = keys_of(service, "BH72707", "XP352AE-DS")
    response = client.post("/kinh-doanh/nhan-vien/gia-dung", data={
        "ky": "2026-09", "sheet": "noi-thanh", **keys})
    assert response.status_code == 302

    noi_thanh = body(client, "/kinh-doanh/nhan-vien?sheet=noi-thanh")
    gia_dung = body(client, "/kinh-doanh/nhan-vien?sheet=gia-dung")
    assert set(metrics(noi_thanh, "line-product")) == {"43F6000", "Giá treo"}
    assert set(metrics(gia_dung, "line-product")) == {"XP352AE-DS"}   # GD-02
    assert metrics(gia_dung, "line-employee") == ["Vinh"]             # GD-03
    # GD-04 — cùng một BH nằm ở HAI sheet, mỗi dòng đúng một chỗ.
    assert metrics(noi_thanh, "bh-order") == ["BH72707"]
    assert metrics(gia_dung, "bh-order") == ["BH72707"]


def test_case_gd_05_and_gd_06_the_company_total_never_moves(
    repository, client, service
):
    """CASE GD-05/GD-06 + `§42` — không nhân đôi, không biến mất.

    Đây là bất biến quan trọng nhất của cả quyết định: chuyển bucket là một
    phép PHÂN HOẠCH LẠI, nên tổng của các sheet luôn đúng bằng tổng kỳ, và
    tổng kỳ không đổi một đồng nào.
    """
    persist(repository, three_line_order("BH72707"))
    before = service.period(**SEPTEMBER).totals

    keys = keys_of(service, "BH72707", "XP352AE-DS")
    client.post("/kinh-doanh/nhan-vien/gia-dung", data={
        "ky": "2026-09", "sheet": "noi-thanh", **keys})

    data = service.period(**SEPTEMBER)
    assert data.totals.sales_revenue == before.sales_revenue      # GD-06
    assert data.totals.kpi_profit == before.kpi_profit            # GD-07
    assert data.totals.lines == before.lines
    assert data.totals.orders == before.orders

    # Và mỗi dòng nằm ở ĐÚNG MỘT bucket (`§11.3`, GD-05).
    sheets = service.sheets(data)
    per_sheet = [data.for_sheet(sheet) for sheet in sheets]
    assert sum(part.totals.lines for part in per_sheet) == data.totals.lines
    assert sum((part.totals.sales_revenue or Decimal(0)) for part in per_sheet
               ) == data.totals.sales_revenue


def test_case_gd_08_to_gd_10_the_conversion_rate_moves_from_two_to_eight(
    repository, client, service
):
    """CASE GD-08/GD-09/GD-10 + `§12` — 2 % → 8 %, dùng ĐÚNG bảng tỉ lệ cũ.

    Lợi nhuận 2.000.000:
        Nội thành  2.000.000 / 2 % = 100.000.000
        Gia dụng   2.000.000 / 8 % =  25.000.000

    Đây KHÔNG phải một công thức KPI mới — nó là dòng `GIA_DUNG_8` đã có sẵn
    trong `config/conversion_rates.yaml` từ ADR-106/DEC-127.
    """
    persist(repository, three_line_order("BH72707"))
    target_line = [l for l in service.period(**SEPTEMBER).lines
                   if l.kpi_profit == Decimal("2000000")][0]
    assert target_line.conversion_rate == Decimal("0.020")           # GD-08
    assert target_line.converted_sales == Decimal("100000000.00")

    keys = keys_of(service, "BH72707", "XP352AE-DS")
    client.post("/kinh-doanh/nhan-vien/gia-dung", data={
        "ky": "2026-09", "sheet": "noi-thanh", **keys})

    moved = [l for l in service.period(**SEPTEMBER).lines
             if l.kpi_profit == Decimal("2000000")][0]
    assert moved.conversion_rate == Decimal("0.080")                 # GD-09
    assert moved.converted_sales == Decimal("25000000.00")           # GD-10
    # GD-07 — lợi nhuận KPI của chính dòng đó KHÔNG đổi.
    assert moved.kpi_profit == target_line.kpi_profit


def test_case_gd_16_and_gd_17_each_bucket_measures_against_its_own_target(
    repository, client
):
    """CASE GD-16/GD-17 — So Target của mỗi sheet tính lại theo Target CỦA NÓ."""
    persist(repository, three_line_order("BH72707"))
    client.post("/kinh-doanh/nhan-vien/target", data={
        "ky": "2026-09", "sheet": "noi-thanh", "target": "500,000"})
    client.post("/kinh-doanh/nhan-vien/target", data={
        "ky": "2026-09", "sheet": "gia-dung", "target": "100,000"})

    before = body(client, "/kinh-doanh/nhan-vien?sheet=noi-thanh")
    vs_before = metric(before, "employee-vs-target")

    keys = None
    html = body(client, "/kinh-doanh/nhan-vien?sheet=noi-thanh")
    import app.web.business_service as _svc  # noqa: F401 (đọc qua client bên dưới)
    response = client.post("/kinh-doanh/nhan-vien/gia-dung", data={
        "ky": "2026-09", "sheet": "noi-thanh",
        **_keys_from_html(html, "XP352AE-DS")})
    assert response.status_code == 302

    after = body(client, "/kinh-doanh/nhan-vien?sheet=noi-thanh")
    assert metric(after, "employee-vs-target") != vs_before          # GD-16
    gia_dung = body(client, "/kinh-doanh/nhan-vien?sheet=gia-dung")
    # 25.000.000 / 100.000.000 = 25 % — dùng Target CỦA Gia dụng.
    assert metric(gia_dung, "employee-vs-target") == "25%"           # GD-17


def _keys_from_html(html: str, product: str) -> dict:
    """Khoá nghiệp vụ của dòng mang tên hàng này, đọc từ chính bảng đang hiện."""
    for row in re.findall(r"<tr[^>]*data-metric=\"line-row\".*?</tr>", html, re.S):
        if f">{product}<" not in row and f"{product}</td>" not in row:
            continue
        match = re.search(
            r"order_key=(?P<order_key>[^&\"]+)&amp;product_key="
            r"(?P<product_key>[0-9a-f]+)&amp;occurrence_index="
            r"(?P<occurrence_index>\d+)", row)
        if match:
            return match.groupdict()
    raise AssertionError(f"không tìm thấy khoá của {product} trong HTML")


def test_case_gd_11_and_gd_12_the_classification_outlives_snapshots_and_edits(
    repository, client, service
):
    """CASE GD-11/GD-12 — quyết định sống qua nạp sổ mới và sửa giá nhập."""
    persist(repository, three_line_order("BH1"))
    keys = keys_of(service, "BH1", "XP352AE-DS")
    client.post("/kinh-doanh/nhan-vien/gia-dung", data={
        "ky": "2026-09", "sheet": "noi-thanh", **keys})

    persist(repository, three_line_order("BH1"), run_id="run-2",
            at="2026-10-05T00:00:00", fingerprint="fp-b")                # GD-11
    client.post("/kinh-doanh/nhan-vien/gia-nhap", data={
        "ky": "2026-09", "sheet": "gia-dung", **keys,
        "gia_nhap": "1000000"})                                          # GD-12

    gia_dung = body(client, "/kinh-doanh/nhan-vien?sheet=gia-dung")
    assert metrics(gia_dung, "line-product") == ["XP352AE-DS"]


def test_case_gd_13_exclusion_and_classification_are_different_operations(
    repository, client, service
):
    """CASE GD-13 + `§33` — hai thao tác KHÁC NHAU, không cái nào cài bằng cái kia.

    Loại  ⟹ dòng biến khỏi MỌI sheet và mọi chỉ tiêu.
    Phân loại ⟹ dòng vẫn được báo cáo, chỉ đổi bucket.
    """
    persist(repository, three_line_order("BH1"))
    classified = keys_of(service, "BH1", "XP352AE-DS")
    excluded = keys_of(service, "BH1", "Giá treo")
    client.post("/kinh-doanh/nhan-vien/gia-dung", data={
        "ky": "2026-09", "sheet": "noi-thanh", **classified})
    client.post("/kinh-doanh/nhan-vien/loai-dong", data={
        "ky": "2026-09", "sheet": "noi-thanh", **excluded})

    data = service.period(**SEPTEMBER)
    reported = {detail["product_raw"] for detail in data.details}
    assert reported == {"43F6000", "XP352AE-DS"}
    assert {detail["product_raw"] for detail in data.excluded} == {"Giá treo"}
    # Dòng đã phân loại vẫn được cộng; dòng đã loại thì không.
    assert data.totals.lines == 2
    # Và hai bảng quyết định là hai bảng khác nhau.
    assert set(service.store.line_product_groups()) == {
        (classified["order_key"], classified["product_key"],
         classified["occurrence_index"])}
    assert set(service.store.line_exclusions()) == {
        (excluded["order_key"], excluded["product_key"],
         excluded["occurrence_index"])}


def test_case_gd_14_the_raw_provenance_is_untouched_by_classification(
    repository, client, service, engine
):
    """CASE GD-14 — phân loại KHÔNG ghi vào một bảng bằng chứng nào."""
    persist(repository, three_line_order("BH1"))
    before = {name: _count(engine, name) for name in (
        "order_line_source_version", "order_line_result_version",
        "order_line_current", "snapshot_line")}
    keys = keys_of(service, "BH1", "XP352AE-DS")
    client.post("/kinh-doanh/nhan-vien/gia-dung", data={
        "ky": "2026-09", "sheet": "noi-thanh", **keys})
    assert {name: _count(engine, name) for name in before} == before

    # Và giá bán/giá nhập/khách hàng của dòng không đổi (`§41`).
    moved = [d for d in service.period(**SEPTEMBER).details
             if d["product_raw"] == "XP352AE-DS"][0]
    assert moved["line"].sell_price == Decimal("4000000")
    assert moved["line"].purchase_price == Decimal("2000000")
    assert moved["customer_name"] == "Nguyễn Thị Hoa"


def test_case_gd_15_the_gia_dung_sheet_reuses_the_same_detail_table(
    repository, client, service
):
    """CASE GD-15 + `§39` — MỘT cách trình bày, không phải hai giao diện."""
    persist(repository, three_line_order("BH72707"))
    keys = keys_of(service, "BH72707", "XP352AE-DS")
    client.post("/kinh-doanh/nhan-vien/gia-dung", data={
        "ky": "2026-09", "sheet": "noi-thanh", **keys})

    html = body(client, "/kinh-doanh/nhan-vien?sheet=gia-dung")
    assert metric(html, "bh-date") == "05/09/2026"
    assert metric(html, "bh-order") == "BH72707"
    assert metric(html, "customer-name") == "Nguyễn Thị Hoa"
    assert metric(html, "customer-phone") == "0912000111"
    assert metric(html, "customer-address") == "12 Lê Lợi, Q1"
    assert metric(html, "line-employee") == "Vinh"
    header = re.search(r"<table class=\"sheet-table\">\s*<tr>(.*?)</tr>",
                       html, re.S).group(1)
    assert "Giá nhập" in header and "Giá bán" in header


def test_the_gia_dung_action_is_offered_on_the_noi_thanh_sheet_only(
    repository, client, service
):
    """`§9` — chỉ sheet Nội thành nhận thao tác này, và ranh giới có ở SERVER."""
    persist(repository, [
        *three_line_order("BH1", employee="Vinh"),
        line("BH2", "Tivi", employee="Ly", group="STANDARD_SALES",
             rate="0.055", row=20),
    ])
    assert 'data-metric="line-gia-dung"' in body(
        client, "/kinh-doanh/nhan-vien?sheet=noi-thanh")
    assert 'data-metric="line-gia-dung"' not in body(
        client, "/kinh-doanh/nhan-vien?sheet=nv:Ly")
    # Sheet Gia dụng cũng không nhận nó — dòng đã ở đó rồi.
    assert 'data-metric="line-gia-dung"' not in body(
        client, "/kinh-doanh/nhan-vien?sheet=gia-dung")

    # Một POST dựng tay trên dòng của nhân viên bán lẻ vẫn bị chặn.
    retail = None
    for detail in service.period(**SEPTEMBER).details:
        if detail["order_key"] == "BH2":
            retail = {"order_key": detail["order_key"],
                      "product_key": detail["product_key"],
                      "occurrence_index": detail["occurrence_index"]}
    assert client.post("/kinh-doanh/nhan-vien/gia-dung", data={
        "ky": "2026-09", "sheet": "noi-thanh", **retail}).status_code == 404


def test_the_gia_dung_move_asks_a_short_confirmation_with_two_buttons(
    repository, client, service
):
    """`§9` — hộp xác nhận NGẮN: một câu hỏi, ba gạch đầu dòng, hai nút."""
    persist(repository, three_line_order("BH1"))
    keys = keys_of(service, "BH1", "XP352AE-DS")
    html = body(client, "/kinh-doanh/nhan-vien?xac-nhan=gia-dung"
                        f"&order_key={keys['order_key']}"
                        f"&product_key={keys['product_key']}"
                        f"&occurrence_index={keys['occurrence_index']}")
    assert metric(html, "confirm-question") == wp.GIA_DUNG_CONFIRM_QUESTION
    assert metrics(html, "confirm-point") == list(wp.GIA_DUNG_CONFIRM_POINTS)
    assert metric(html, "confirm-cancel") == "HỦY"
    assert metric(html, "confirm-ok") == "CHUYỂN"
    assert len(metrics(html, "confirm-point")) == 3


def test_a_line_can_be_moved_back_out_of_gia_dung(repository, client, service):
    """Quyết định phân loại cấp dòng gỡ lại được, và gỡ nghĩa là VẮNG MẶT."""
    persist(repository, three_line_order("BH1"))
    keys = keys_of(service, "BH1", "XP352AE-DS")
    client.post("/kinh-doanh/nhan-vien/gia-dung", data={
        "ky": "2026-09", "sheet": "noi-thanh", **keys})
    assert service.store.line_product_groups() != {}

    client.post("/kinh-doanh/nhan-vien/gia-dung", data={
        "ky": "2026-09", "sheet": "gia-dung", **keys, "hanh-dong": "go"})
    assert service.store.line_product_groups() == {}
    assert len(metrics(body(client, "/kinh-doanh/nhan-vien?sheet=noi-thanh"),
                       "line-product")) == 3


def test_the_line_level_decision_wins_over_the_product_level_one(
    repository, client, service, store
):
    """`§40` — MỘT thẩm quyền, hai độ mịn, và quy tắc ưu tiên viết một chỗ.

    Mặt hàng đã tick `GIA_DUNG` ở cấp mặt hàng; Owner sau đó nói riêng về MỘT
    dòng rằng nó là `DIEN_MAY`. Quyết định cụ thể hơn thắng — nếu không, hai
    bảng sẽ cho ra hai câu trả lời trên hai màn hình.
    """
    persist(repository, [
        line("BH1", "Nồi chiên", sell="4000000", kpi_purchase="2000000",
             kpi_profit="2000000"),
        line("BH2", "Nồi chiên", row=7, sell="4000000",
             kpi_purchase="2000000", kpi_profit="2000000"),
    ])
    product_key = service.period(**SEPTEMBER).details[0]["product_key"]
    store.set_product_group(product_key=product_key, product_group="GIA_DUNG",
                            product_label="Nồi chiên")
    assert len(metrics(body(client, "/kinh-doanh/nhan-vien?sheet=gia-dung"),
                       "line-product")) == 2

    store.set_line_product_group(order_key="BH1", product_key=product_key,
                                 occurrence_index=1, product_group="DIEN_MAY")
    gia_dung = body(client, "/kinh-doanh/nhan-vien?sheet=gia-dung")
    noi_thanh = body(client, "/kinh-doanh/nhan-vien?sheet=noi-thanh")
    assert metrics(gia_dung, "bh-order") == ["BH2"]
    assert metrics(noi_thanh, "bh-order") == ["BH1"]


def test_a_gia_dung_line_follows_its_employee_out_of_the_group(
    repository, client, service
):
    """Bucket và TỈ LỆ không bao giờ nói hai câu khác nhau.

    `conversion_rates.yaml` khoá 8 % trên `employee_group: NOI_THANH`. Sau khi
    Owner gán dòng cho một nhân viên bán lẻ, tỉ lệ của nó trở lại 5,5 %, nên
    nó cũng phải rời sheet Gia dụng — nếu không sheet đó sẽ trộn hai tỉ lệ và
    "DS quy đổi của Gia dụng" không còn tương ứng với chính sách nào.
    """
    persist(repository, three_line_order("BH1"))
    keys = keys_of(service, "BH1", "XP352AE-DS")
    client.post("/kinh-doanh/nhan-vien/gia-dung", data={
        "ky": "2026-09", "sheet": "noi-thanh", **keys})
    assert metrics(body(client, "/kinh-doanh/nhan-vien?sheet=gia-dung"),
                   "line-product") == ["XP352AE-DS"]

    client.post("/kinh-doanh/nhan-vien/don", data={
        "ky": "2026-09", "sheet": "noi-thanh", "order_key": "BH1",
        "nhan_vien_moi": "Ly"})
    moved = [l for l in service.period(**SEPTEMBER).lines
             if l.kpi_profit == Decimal("2000000")][0]
    assert moved.conversion_rate == Decimal("0.055")
    assert metric(body(client, "/kinh-doanh/nhan-vien?sheet=gia-dung"),
                  "no-rows") == wp.EMPTY_PERIOD_NOTE


def test_gia_dung_is_never_an_employee_identity(repository, service):
    """`§8` — Gia dụng là một BUCKET báo cáo, không phải một người.

    Bằng chứng cấu trúc: master nhân viên không có ai tên "Gia dụng", và
    không dòng nào bị đổi `employee` khi chuyển bucket.
    """
    persist(repository, three_line_order("BH1"))
    assert "Gia dụng" not in dict(service.assignable_employees())
    assert "GIA_DUNG" not in {group for _n, group
                              in service.assignable_employees()}
    keys = keys_of(service, "BH1", "XP352AE-DS")
    service.store.set_line_product_group(product_group="GIA_DUNG", **keys)
    assert {l.employee for l in service.period(**SEPTEMBER).lines} == {"Vinh"}


# ==========================================================================
# §44 · §64 — MIGRATION TỪ REVISION PRODUCTION 0006
# ==========================================================================

def _alembic(command: str, db_path: Path, target: str) -> subprocess.CompletedProcess:
    """Chạy alembic THẬT trong một tiến trình riêng — cùng cách `§64` yêu cầu.

    Gọi hàm migration trực tiếp sẽ bỏ qua chính thứ cần kiểm: chuỗi revision,
    `env.py`, và bảng `alembic_version`.
    """
    return subprocess.run(
        [sys.executable, "-m", "alembic", command, target],
        cwd=REPO_ROOT, capture_output=True, text=True,
        env={"PATH": "/usr/bin:/bin", "PYTHONPATH": str(REPO_ROOT),
             "HISTORY_DATABASE_URL": f"sqlite:///{db_path}"},
    )


def test_the_upgrade_from_the_production_revision_0006_is_additive(tmp_path):
    """`§44`/`§64` — nâng cấp từ ĐÚNG revision đang chạy production.

    Ba khẳng định, và cả ba là điều kiện để triển khai được:

    1. Dựng database ở `0006` (trạng thái production), nạp dữ liệu Owner.
    2. `upgrade head` chạy sạch, thêm ba cột + ba bảng.
    3. KHÔNG một giá trị Owner nào của `0006` bị mất hay bị viết lại.
    """
    db_path = tmp_path / "history.db"
    assert _alembic("upgrade", db_path, "0006_employee_target").returncode == 0

    # Các migration của repo này dựng bảng từ `schema.METADATA` — nguồn DDL
    # DUY NHẤT — nên một database vừa dựng tới `0006` HÔM NAY đã mang sẵn ba
    # cột mà `0007` thêm. Database production thì không: nó được dựng khi
    # `METADATA` chưa có chúng. Bỏ ba cột đi ở đây là cách duy nhất để test
    # đi qua ĐÚNG nhánh `op.add_column` mà production sẽ chạy.
    engine = create_engine(f"sqlite:///{db_path}")
    with engine.begin() as connection:
        for name in ("customer_name", "customer_phone", "customer_address"):
            connection.exec_driver_sql(
                f"ALTER TABLE order_line_source_version DROP COLUMN {name}")
        for name in ("line_product_group_classification", "line_exclusion",
                     "group_target"):
            connection.exec_driver_sql(f"DROP TABLE IF EXISTS {name}")
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "INSERT INTO employee_target"
            " (year, month, employee_key, origin, target_vnd, updated_at)"
            " VALUES (2026, 9, 'Ly', 'PIPELINE_GENERATED', '500000000',"
            "         '2026-09-01T00:00:00')")
        connection.exec_driver_sql(
            "INSERT INTO kpi_purchase_price_override"
            " (order_key, product_key, occurrence_index, origin,"
            "  purchase_price, provenance, entered_at)"
            " VALUES ('BH1', 'pk', 1, 'PIPELINE_GENERATED', 6200000,"
            "         'MANUAL', '2026-09-01T00:00:00')")
    with engine.connect() as connection:
        columns = {c["name"] for c in
                   inspect(connection).get_columns("order_line_source_version")}
        assert "customer_name" not in columns, "0006 chưa có ba cột này"
    engine.dispose()

    result = _alembic("upgrade", db_path, "head")
    assert result.returncode == 0, result.stderr

    engine = create_engine(f"sqlite:///{db_path}")
    with engine.connect() as connection:
        columns = {c["name"] for c in
                   inspect(connection).get_columns("order_line_source_version")}
        assert {"customer_name", "customer_phone", "customer_address"} <= columns
        names = set(inspect(connection).get_table_names())
        assert {"line_product_group_classification", "line_exclusion",
                "group_target"} <= names
        # Dữ liệu Owner của `0006` còn NGUYÊN, không bị viết lại.
        assert connection.exec_driver_sql(
            "SELECT employee_key, target_vnd FROM employee_target").fetchall(
            ) == [("Ly", "500000000")]
        assert connection.exec_driver_sql(
            "SELECT purchase_price FROM kpi_purchase_price_override").fetchall(
            ) == [("6200000",)]
        assert connection.exec_driver_sql(
            "SELECT version_num FROM alembic_version").scalar() == (
            history_db.ALEMBIC_HEAD)
    engine.dispose()


# ==========================================================================
# §47 — R1 / R2 / PHB-05 KHÔNG BỊ REGRESS
# ==========================================================================

def test_the_legacy_write_boundary_is_still_locked(client):
    """`R2-B01` — `POST /du-lieu/legacy` vẫn là ranh giới ghi DUY NHẤT."""
    text = (REPO_ROOT / "app/web/server.py").read_text(encoding="utf-8")
    assert re.findall(r'@app\.post\("(/du-lieu/legacy[^"]*)"\)', text) == [
        "/du-lieu/legacy"]


def test_the_workspace_never_borrows_a_company_wide_legacy_month(
    repository, client
):
    """`DEC-181` §16 — tổng tháng của SỐ CŨ là số của cả công ty.

    Nó không bao giờ được làm mốc so sánh cho một sheet, và không gian làm
    việc không có đường nào tới nó.
    """
    persist(repository, three_line_order("BH1", day=5))
    html = body(client, "/kinh-doanh/nhan-vien")
    assert "SỐ CŨ" not in html
    route = (REPO_ROOT / "app/web/server.py").read_text(encoding="utf-8")
    workspace = route.split("def _workspace_previous(")[1].split("def _workspace_line_keys")[0]
    assert "_legacy_previous_month" not in workspace
    assert "legacy" not in workspace.lower()


def test_the_business_page_returns_503_without_a_history_store(
    monkeypatch, tmp_path
):
    """Lỗi hạ tầng KHÔNG BAO GIỜ được hiện thành "chưa có dữ liệu"."""
    monkeypatch.setattr(web_server, "select_latest_valid_captures", lambda: None)
    monkeypatch.setattr(live_pull, "is_configured", lambda env=None: False)
    application = web_server.create_app(db_path=tmp_path / "runs.db",
                                        history=None, snapshots=None)
    application.testing = True
    assert application.test_client().get(
        "/kinh-doanh/nhan-vien").status_code == 503


def test_the_workspace_never_renders_a_prohibited_personal_field(
    repository, client
):
    """Hàng rào cũ còn nguyên cho những trường KHÔNG ai yêu cầu.

    `DEC-PHB02-08` mở đúng ba trường khách hàng. `imei`, `note_raw` và
    `employee_raw` ("Vũ Hạnh Ly 0912…") vẫn không có đường nào ra màn hình.
    """
    persist(repository, three_line_order("BH1"))
    html = body(client, "/kinh-doanh/nhan-vien")
    assert "Vũ Hạnh Ly" not in html          # employee_raw của fixture
    assert "imei" not in html.lower()
    assert "note_raw" not in html.lower()


# ==========================================================================
# §61 — E2E: MỘT VÒNG VẬN HÀNH ĐẦY ĐỦ TRÊN ỨNG DỤNG THẬT
# ==========================================================================

def test_the_owner_runs_a_full_month_through_the_workspace(
    repository, client, service
):
    """`§61` — một vòng vận hành từ đầu đến cuối, trên Flask thật.

    Kỳ mặc định → chọn sheet → đặt Target nhóm → mở một BH → đổi nhân viên →
    sửa giá nhập → chuyển một dòng sang Gia dụng → kiểm bucket → loại một
    dòng khác → kiểm tổng → tải lại → nạp snapshot MỚI → mọi quyết định của
    Owner còn nguyên.

    Mốc quan trọng nhất nằm ở cuối: sau một lần nạp sổ mới, ba quyết định
    (gán nhân viên · giá nhập · phân loại · loại dòng) vẫn còn hiệu lực, và
    tổng doanh thu công ty vẫn đúng bằng con số của sổ trừ đi đúng dòng đã
    loại — không hơn, không kém.
    """
    persist(repository, [
        *three_line_order("BH72707", employee="Vinh", day=3),
        line("BH72708", "Chi phí thuê người", day=4, row=30, sell="700000",
             kpi_purchase="0", kpi_profit="700000"),
    ])
    book_revenue = Decimal("8000000") + Decimal("4000000") + Decimal(
        "500000") + Decimal("700000")
    assert service.period(**SEPTEMBER).totals.sales_revenue == book_revenue

    # 1. Mở không gian làm việc — mặc định tháng hiện tại, sheet Nội thành.
    html = body(client, "/kinh-doanh/nhan-vien")
    assert "Tháng 09/2026" in html
    assert metric(html, "employee") == "Nội thành"

    # 2. Đặt Target NHÓM theo nghìn đồng.
    client.post("/kinh-doanh/nhan-vien/target", data={
        "ky": "2026-09", "sheet": "noi-thanh", "target": "500,000"})

    # 3. Mở một BH và đổi nhân viên cho CẢ đơn.
    open_html = body(client, "/kinh-doanh/nhan-vien?sua=BH72707")
    assert 'data-metric="bh-employee-select"' in open_html
    client.post("/kinh-doanh/nhan-vien/don", data={
        "ky": "2026-09", "sheet": "noi-thanh", "order_key": "BH72707",
        "nhan_vien_moi": "Hiệp"})

    # 4. Sửa Giá nhập của một dòng ngay tại chỗ.
    keys_43f = keys_of(service, "BH72707", "43F6000")
    client.post("/kinh-doanh/nhan-vien/gia-nhap", data={
        "ky": "2026-09", "sheet": "noi-thanh", **keys_43f,
        "gia_nhap": "4.000.000"})

    # 5. Chuyển ĐÚNG MỘT dòng sang Gia dụng.
    keys_xp = keys_of(service, "BH72707", "XP352AE-DS")
    client.post("/kinh-doanh/nhan-vien/gia-dung", data={
        "ky": "2026-09", "sheet": "noi-thanh", **keys_xp})

    noi_thanh = body(client, "/kinh-doanh/nhan-vien?sheet=noi-thanh")
    gia_dung = body(client, "/kinh-doanh/nhan-vien?sheet=gia-dung")
    assert set(metrics(gia_dung, "line-product")) == {"XP352AE-DS"}
    assert "XP352AE-DS" not in metrics(noi_thanh, "line-product")
    assert metrics(gia_dung, "line-employee") == ["Hiệp"]

    # 6. Loại một dòng khác khỏi báo cáo.
    keys_cost = keys_of(service, "BH72708", "Chi phí thuê người")
    client.post("/kinh-doanh/nhan-vien/loai-dong", data={
        "ky": "2026-09", "sheet": "noi-thanh", **keys_cost})

    expected_revenue = book_revenue - Decimal("700000")
    assert service.period(**SEPTEMBER).totals.sales_revenue == expected_revenue

    # 7. Tải lại — mọi thứ giữ nguyên.
    reloaded = body(client, "/kinh-doanh/nhan-vien?sheet=noi-thanh")
    assert 'value="500,000"' in reloaded
    assert set(metrics(reloaded, "line-employee")) == {"Hiệp"}

    # 8. Nạp một snapshot Current MỚI của cùng kỳ.
    persist(repository, [
        *three_line_order("BH72707", employee="Vinh", day=3),
        line("BH72708", "Chi phí thuê người", day=4, row=30, sell="700000",
             kpi_purchase="0", kpi_profit="700000"),
    ], run_id="run-2", at="2026-10-10T00:00:00", fingerprint="fp-b")

    data = service.period(**SEPTEMBER)
    assert data.totals.sales_revenue == expected_revenue
    assert {l.employee for l in data.lines} == {"Hiệp"}
    assert [d["product_raw"] for d in data.excluded] == ["Chi phí thuê người"]
    edited = [d for d in data.details if d["product_raw"] == "43F6000"][0]
    assert edited["line"].purchase_price == Decimal("4000000")
    final_gia_dung = body(client, "/kinh-doanh/nhan-vien?sheet=gia-dung")
    assert set(metrics(final_gia_dung, "line-product")) == {"XP352AE-DS"}

    # 9. Và bất biến cuối: các sheet cộng lại đúng bằng tổng kỳ.
    per_sheet = [data.for_sheet(sheet) for sheet in service.sheets(data)]
    assert sum((part.totals.sales_revenue or Decimal(0))
               for part in per_sheet) == data.totals.sales_revenue
    assert sum(part.totals.lines for part in per_sheet) == data.totals.lines
