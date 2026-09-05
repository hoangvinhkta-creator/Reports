"""`DEC-185` — điều hướng, biểu đồ hợp nhất, nhận diện tại chỗ, F-02, F-03.

File này là bằng chứng cho toàn bộ các CASE nghiệm thu của quyết định:

    NAV-01…NAV-03    thanh tab chính còn ba mục, route cũ vẫn sống
    CHART-01…CHART-11 MỘT biểu đồ · năm mức gộp · số nghiệp vụ chính thức
    PI-01…PI-12      hai trạng thái nhận diện · phân loại tại chỗ · một cảnh báo
    F02-01…F02-06    gán lại BH phủ cả dòng đã bị loại
    F03-01…F03-06    loại dòng là loại khỏi BÁO CÁO CHÍNH THỨC

Cùng nguyên tắc với `test_employee_workspace_ux.py`: mỗi test hỏi một câu
NGHIỆP VỤ và trả lời bằng HTML thật do Flask dựng, hoặc bằng con số thật do
tầng ráp tính. Không test nào chỉ hỏi "hàm này có chạy không".

Ba bất biến được lặp lại có chủ đích, vì chúng là thứ phân biệt một bản sửa
giao diện với một bản sửa làm hỏng sổ sách:

    MỌI MỨC GỘP CỘNG RA CÙNG MỘT TỔNG            (`§CHART-05`…`§CHART-08`)
    BÁO CÁO VÀ NHÂN VIÊN KHÔNG BAO GIỜ LỆCH NHAU (`§F03-02`/`§F03-03`)
    TRACKING VẪN LÀ THẨM QUYỀN PRODUCT IDENTITY  (`§PI-05`/`§PI-06`)
"""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine

import tools.db as history_db
from app.modules.product.identity.mapping import MappingSource, MappingStatus
from app.web import (
    business_service, business_store, history_store, identity_gateway,
    line_identity, revenue_timeline as rt,
)
from app.web import server as web_server
from tests.support import identity_fixtures as fx
from tests.test_employee_workspace_ux import (
    TODAY, body, line, metric, metrics, persist,
)
from app.legacy.models import SOURCE_AUTHORITY_YEAR
from tools.tracking import live_pull

SEPTEMBER = {"date_from": date(2026, 9, 1), "date_to": date(2026, 9, 30)}

#: Mã lý do mà pipeline THẬT ghi xuống khi chưa nhận diện được mặt hàng.
#: Dùng nguyên văn chuỗi đã lưu, không dùng enum: `line_identity` đọc những
#: gì ĐANG nằm trong database, và test phải nói cùng thứ tiếng đó.
UNRESOLVED = ("IDENTITY_UNRESOLVED", "Missing.PurchasePrice")


# --- Dựng dữ liệu ---------------------------------------------------------

@pytest.fixture
def engine():
    engine = create_engine("sqlite://")
    history_db.create_all_for_test(engine)
    return engine


@pytest.fixture
def repository(engine):
    return history_store.SnapshotRepository(engine)


@pytest.fixture
def legacy(engine):
    return history_store.LegacyRepository(engine)


@pytest.fixture
def store(engine):
    return business_store.BusinessDecisionStore(engine)


@pytest.fixture
def service(engine, store):
    return business_service.BusinessReportService(engine=engine, store=store)


@pytest.fixture
def identity_store(tmp_path):
    return fx.store(tmp_path)


@pytest.fixture
def snapshot():
    """Danh mục Tracking đang đọc được — thẩm quyền của các mã bên dưới."""
    return fx.tracking_snapshot((
        ("EWF1143R7SC", "Máy giặt Electrolux EWF1143R7SC", (), True),
        ("43F6000", "Tivi TCL 43F6000", (), True),
        ("DA-BO", "Mã đã bỏ khỏi board", (), False),
    ))


@pytest.fixture
def client(engine, monkeypatch, tmp_path, identity_store, snapshot):
    monkeypatch.setattr(web_server, "select_latest_valid_captures", lambda: None)
    monkeypatch.setattr(live_pull, "is_configured", lambda env=None: False)
    monkeypatch.setattr(web_server, "_today", lambda: TODAY)
    # Thẩm quyền Product Identity của test nằm trong `tmp_path`, không phải
    # `data/product_identity/` của repo: một test ghi vào log thật sẽ để lại
    # quyết định giả trong dữ liệu vận hành.
    monkeypatch.setattr(identity_gateway, "build_store", lambda: identity_store)
    application = web_server.create_app(
        db_path=tmp_path / "runs.db",
        history=history_store.LegacyRepository(engine),
        snapshots=history_store.SnapshotRepository(engine))
    application.testing = True
    # Danh mục Tracking: tiêm ở đúng chỗ route hỏi nó, nên mọi cửa kiểm mã
    # trong `identity_gateway` vẫn chạy thật.
    monkeypatch.setitem(application.view_functions, "_noop", lambda: None)
    return application.test_client()


@pytest.fixture
def tracking_on(monkeypatch, snapshot, tmp_path):
    """Bật danh mục Tracking cho các test phân loại.

    Trả về một `SelectedCaptures` THẬT chứ không phải một `object()` rỗng:
    một stub thiếu thuộc tính sẽ ném `AttributeError` bên trong
    `_tracking_snapshot`, bị nuốt bởi nhánh "danh mục hỏng ⟹ chưa đọc được",
    và mọi test phân loại sẽ chạy trên nhánh KHÔNG có Tracking mà vẫn xanh.
    """
    import app.web.server as srv
    from app.owner_usability import SelectedCaptures
    captures = SelectedCaptures(
        tracking_capture=tmp_path / "history.json",
        tracking_catalog=tmp_path / "catalog.json",
        tracking_inv_map=tmp_path / "inv_map.json")
    monkeypatch.setattr(
        srv, "load_tracking_catalog_capture", lambda path: snapshot)
    monkeypatch.setattr(
        srv, "_select_captures_for_run", lambda: (captures, None, None))
    return snapshot


def seed_legacy(engine, rows, *, import_id="imp-2025", year=2025):
    """Ghi một bản nhập lịch sử tối thiểu: tổng tháng + doanh số từng ngày.

    Dùng chính các `Table` của `tools.db.schema` chứ không viết SQL tay: tên
    cột viết tay sẽ trôi khỏi lược đồ mà không test nào đỏ, và một fixture
    trôi khỏi lược đồ sẽ chứng minh một hệ thống KHÁC với hệ thống đang chạy.

    `sales` của Summary lưu theo NGHÌN ĐỒNG (`unit='kVND'`), nên nó được
    chia 1.000 ở đây — đúng hệ số mà `legacy_reference.to_vnd` nhân lại. Hai
    phía cùng biết về hệ số đó là điều làm test này kiểm được cả phép đổi
    đơn vị, chứ không chỉ phép cộng.
    """
    from tools.db import schema
    with engine.begin() as conn:
        conn.execute(schema.legacy_import.insert().values(
            import_id=import_id, origin=schema.ORIGIN_LEGACY,
            source_file_name="so-cu.xlsx", file_fingerprint=f"fp-{import_id}",
            imported_at="2026-01-01T00:00:00", is_current=True,
            source_authority=SOURCE_AUTHORITY_YEAR))
        for index, (month, day, vnd) in enumerate(rows):
            conn.execute(schema.legacy_daily_sales.insert().values(
                import_id=import_id, origin=schema.ORIGIN_LEGACY,
                year=year, month=month, day=day,
                sales_vnd=Decimal(vnd), source_sheet="DataChart"))
        for index, month in enumerate(sorted({month for month, _, _ in rows})):
            total = sum(value for m, _, value in rows if m == month)
            conn.execute(schema.legacy_summary_row.insert().values(
                import_id=import_id, origin=schema.ORIGIN_LEGACY,
                year=year, month=month, row_kind="MONTH_TOTAL",
                sheet_name="Summary", sheet_row=index + 1, unit="kVND",
                sales=Decimal(total) / 1000))


def seed_legacy_month_total_only(engine, *, year, month, vnd,
                                 import_id="imp-month-only"):
    """Một kỳ lịch sử CHỈ có tổng tháng — không một dòng `DataChart` nào.

    Đây là hình dạng dữ liệu mà `CHART-10` nói về: bằng chứng dừng ở mức
    THÁNG, nên mức Ngày/Tuần không được sinh ra điểm nào từ nó.
    """
    from tools.db import schema
    with engine.begin() as conn:
        conn.execute(schema.legacy_import.insert().values(
            import_id=import_id, origin=schema.ORIGIN_LEGACY,
            source_file_name="so-cu-thang.xlsx",
            file_fingerprint=f"fp-{import_id}",
            imported_at="2026-01-01T00:00:00", is_current=True,
            source_authority=SOURCE_AUTHORITY_YEAR))
        conn.execute(schema.legacy_summary_row.insert().values(
            import_id=import_id, origin=schema.ORIGIN_LEGACY,
            year=year, month=month, row_kind="MONTH_TOTAL",
            sheet_name="Summary", sheet_row=1, unit="kVND",
            sales=Decimal(vnd) / 1000))


# ==========================================================================
# NAV-01 · NAV-02 · NAV-03 — thanh tab chính còn ba mục
# ==========================================================================

def test_nav_01_the_primary_nav_is_exactly_bao_cao_nhan_vien_du_lieu(client):
    nav = re.search(r'<nav class="ncc-tabs">(.*?)</nav>',
                    body(client, "/kinh-doanh"), re.S).group(1)
    assert [label.strip() for label in re.findall(r'>([^<>]+)</a>', nav)] == [
        "Báo cáo", "Nhân viên", "Dữ liệu"]


def test_nav_02_daily_sales_is_not_a_primary_destination_anywhere(client):
    """Không MỘT trang nào còn trỏ "Doanh số ngày" từ thanh tab chính.

    Kiểm trên nhiều trang chứ không riêng một trang: bỏ tab ở `layout.html`
    mà để sót một bản sao thanh tab ở đâu đó sẽ làm mục này sống lại ở đúng
    những trang không ai mở khi review.
    """
    for path in ("/kinh-doanh", "/kinh-doanh/nhan-vien", "/du-lieu",
                 "/doanh-so-ngay", "/tong-quan"):
        nav = re.search(r'<nav class="ncc-tabs">(.*?)</nav>',
                        body(client, path), re.S).group(1)
        assert "Doanh số ngày" not in nav, path
        assert 'href="/doanh-so-ngay"' not in nav, path


def test_nav_03_the_old_route_still_answers_for_compatibility(client):
    """Rời thanh tab KHÔNG phải bị xoá — đường dẫn cũ vẫn mở được."""
    assert client.get("/doanh-so-ngay").status_code == 200


# ==========================================================================
# CHART-01…CHART-11 — MỘT biểu đồ, năm mức gộp
# ==========================================================================

def test_chart_01_and_03_bao_cao_has_exactly_one_revenue_chart(repository, client):
    persist(repository, [line("BH1", "43F6000", day=5)])
    html = body(client, "/kinh-doanh")
    assert html.count('data-metric="chart"') == 1, (
        "phải có ĐÚNG MỘT biểu đồ — không phải một cái cho mỗi mức gộp")


def test_chart_02_the_selector_offers_five_granularities(repository, client):
    persist(repository, [line("BH1", "43F6000", day=5)])
    html = body(client, "/kinh-doanh")
    grans = re.findall(r'class="ghost btn-mini[^"]*"\s*\n?\s*data-gran="([^"]+)"', html)
    assert grans == ["ngay", "tuan", "thang", "quy", "nam"]


def test_chart_03_one_chart_changes_grouping_instead_of_duplicating(
    repository, client
):
    """Đổi mức gộp đổi SỐ CỘT của cùng một biểu đồ, không thêm biểu đồ."""
    persist(repository, [
        line("BH1", "43F6000", day=1, sell="1000000", kpi_profit="100000"),
        line("BH2", "XP352", day=2, sell="2000000", kpi_profit="100000"),
    ])
    by_gran = {}
    for gran in ("ngay", "thang"):
        html = body(client, f"/kinh-doanh?muc={gran}")
        assert html.count('data-metric="chart"') == 1
        by_gran[gran] = re.findall(r'data-metric="chart-bar"', html)
    assert len(by_gran["ngay"]) == 2
    assert len(by_gran["thang"]) == 1


def chart_bars(html: str) -> dict[str, Decimal]:
    """Doanh thu của từng cột, đọc từ giá trị MÁY chứ không từ nhãn.

    `data-revenue` cố ý không định dạng theo vi-VN: đọc lại một con số đã
    chèn dấu phân nhóm buộc test phải gỡ định dạng, và phép gỡ đó sẽ hỏng
    ngay khi một dòng có phần thập phân — nghĩa là test sẽ vỡ vì một lý do
    không liên quan gì tới điều nó đang khẳng định.
    """
    return {
        key: Decimal(value)
        for key, value in re.findall(
            r'data-metric="chart-bar" data-key="([^"]+)"[^>]*'
            r'data-revenue="([^"]+)"', html)
    }


def test_chart_04_day_values_equal_the_authoritative_daily_revenue(
    repository, service, client
):
    """`CHART-04` — cột NGÀY bằng đúng doanh thu nghiệp vụ của chính ngày đó."""
    persist(repository, [
        line("BH1", "43F6000", day=5, sell="8000000"),
        line("BH2", "XP352", day=5, sell="2000000"),
        line("BH3", "Giá treo", day=7, sell="500000"),
    ])
    bars = chart_bars(body(client, "/kinh-doanh?muc=ngay"))
    assert bars["2026-09-05"] == Decimal("10000000")
    assert bars["2026-09-07"] == Decimal("500000")
    # Và tổng của mọi cột đúng bằng chỉ tiêu "Doanh thu bán hàng" của kỳ.
    assert sum(bars.values()) == service.period(**SEPTEMBER).totals.sales_revenue


@pytest.mark.parametrize("coarse,fine", [
    ("tuan", "ngay"), ("thang", "ngay"), ("quy", "thang"), ("nam", "thang"),
])
def test_chart_05_to_08_every_granularity_sums_to_the_same_total(
    repository, client, coarse, fine
):
    """`CHART-05`…`CHART-08` — gộp thô hơn KHÔNG được làm đổi tổng.

    Đây là bất biến quan trọng nhất của biểu đồ: năm cái nút phải là năm cách
    NHÌN cùng một sự thật, không phải năm phép tính khác nhau. Một bản sửa
    làm rơi hoặc nhân đôi một mốc sẽ đỏ ở đây trước khi ai kịp tin vào một
    đường xu hướng sai.
    """
    persist(repository, [
        line("BH1", "43F6000", day=1, month=9, sell="1000000"),
        line("BH2", "XP352", day=15, month=9, sell="2000000"),
        line("BH3", "Giá treo", day=28, month=9, sell="4000000"),
    ])
    assert sum(chart_bars(body(client, f"/kinh-doanh?muc={coarse}")).values()) == \
        sum(chart_bars(body(client, f"/kinh-doanh?muc={fine}")).values())


def test_chart_09_an_excluded_line_leaves_the_official_chart(
    repository, service, store, client
):
    """`CHART-09` — dòng bị loại biến khỏi biểu đồ, đúng như khỏi mọi chỉ tiêu."""
    persist(repository, [
        line("BH1", "43F6000", day=5, sell="8000000"),
        line("BH2", "XP352", day=5, sell="2000000"),
    ])
    before = chart_bars(body(client, "/kinh-doanh?muc=ngay"))["2026-09-05"]
    detail = next(item for item in service.period(**SEPTEMBER).details
                  if item["order_key"] == "BH2")
    store.exclude_line(order_key="BH2", product_key=detail["product_key"],
                       occurrence_index=detail["occurrence_index"])
    after = chart_bars(body(client, "/kinh-doanh?muc=ngay"))["2026-09-05"]
    assert before - after == Decimal("2000000"), (
        "biểu đồ phải giảm ĐÚNG phần đóng góp của dòng bị loại")


def test_chart_10_a_legacy_month_without_daily_evidence_invents_no_days(
    engine, repository, client
):
    """`CHART-10` — chỉ có tổng tháng ⟹ KHÔNG có cột ngày nào được bịa ra."""
    persist(repository, [line("BH1", "43F6000", day=5)])
    seed_legacy_month_total_only(engine, year=2025, month=6, vnd=30000000)

    days = chart_bars(body(client, "/kinh-doanh?muc=ngay"))
    assert not any(key.startswith("2025-06") for key in days), (
        "một tổng tháng KHÔNG được chia đều thành 30 ngày")
    # Nhưng ở mức THÁNG nó xuất hiện — bằng chứng có thật thì không bị giấu.
    months = chart_bars(body(client, "/kinh-doanh?muc=thang"))
    assert months["2025-06"] == Decimal("30000000")


def test_chart_11_legacy_and_current_share_one_timeline_without_a_source_toggle(
    engine, repository, client
):
    """`CHART-11` + `§7` — một dòng thời gian, KHÔNG bộ chọn nguồn.

    Và `DEC-166 E` vẫn đúng: mỗi cột chỉ đến từ MỘT origin, và origin đó đọc
    lại được — nó chỉ không còn là một cái nút bấm.
    """
    persist(repository, [line("BH1", "43F6000", day=5, month=9, sell="8000000")])
    seed_legacy(engine, [(6, 10, 30000000)], year=2025)

    html = body(client, "/kinh-doanh?muc=thang")
    bars = chart_bars(html)
    assert "2025-06" in bars and "2026-09" in bars, "một dòng thời gian liên tục"

    origins = dict(re.findall(
        r'data-metric="chart-bar" data-key="([^"]+)"[^>]*data-origin="([^"]+)"',
        html))
    assert origins["2025-06"] == "LEGACY_REFERENCE"
    assert origins["2026-09"] == "PIPELINE_GENERATED"

    chart = re.search(r'id="bieu-do-doanh-thu".*?(?=<div class="module")',
                      html, re.S).group(0)
    for forbidden in ("Số cũ", "Số mới", "SỐ CŨ", "SỐ MỚI"):
        assert forbidden not in chart, (
            f"{forbidden!r} là một nhãn nguồn — biểu đồ nói về THỜI GIAN")


def test_chart_never_adds_two_origins_into_one_bucket(engine, repository, client):
    """`DEC-180` §9 — MỘT kỳ ⟹ MỘT nguồn. Số mới thắng ở kỳ nó có dòng."""
    persist(repository, [line("BH1", "43F6000", day=5, month=9, sell="8000000")])
    seed_legacy(engine, [(9, 10, 999000000)], year=2026, import_id="imp-2026")
    bars = chart_bars(body(client, "/kinh-doanh?muc=thang"))
    assert bars["2026-09"] == Decimal("8000000"), (
        "kỳ đã có dòng số mới KHÔNG được cộng thêm bản ghi lịch sử")


# ==========================================================================
# PI-01…PI-12 — nhận diện sản phẩm, tại chỗ
# ==========================================================================

def unresolved_line(order="BH73877", product="Máy giặt Electrolux EWF1143R7SC"):
    return line(order, product, day=5, kpi_purchase=None, kpi_profit=None,
                status="PENDING", reasons=UNRESOLVED)


def test_pi_01_an_unresolved_line_reads_chua_phan_loai(repository, client):
    persist(repository, [unresolved_line()])
    html = body(client, "/kinh-doanh/nhan-vien?ky=2026-09")
    assert line_identity.LABEL_UNRESOLVED in metrics(html, "identity-label")


def test_pi_02_identified_but_priceless_reads_thieu_gia(repository, client):
    """Đã nhận diện (không có mã identity nào) nhưng chưa có giá nhập."""
    persist(repository, [line("BH1", "43F6000", day=5, kpi_purchase=None,
                              kpi_profit=None, status="PENDING",
                              reasons=("Missing.PurchasePrice",))])
    html = body(client, "/kinh-doanh/nhan-vien?ky=2026-09")
    assert line_identity.LABEL_MISSING_PRICE in metrics(html, "identity-label")
    assert line_identity.LABEL_UNRESOLVED not in metrics(html, "identity-label")


def test_pi_03_the_two_states_are_never_conflated(repository, client):
    """`PI-03` — hai dòng, hai trạng thái, hai nhãn KHÁC nhau trên cùng bảng.

    Cả hai dòng đều thiếu giá nhập. Nếu ai đó cài lại trạng thái bằng
    `purchase_price is None`, cả hai sẽ mang cùng một nhãn và test này đỏ.
    """
    persist(repository, [
        unresolved_line("BH1"),
        line("BH2", "43F6000", day=5, kpi_purchase=None, kpi_profit=None,
             status="PENDING", reasons=("Missing.PurchasePrice",)),
    ])
    labels = metrics(body(client, "/kinh-doanh/nhan-vien?ky=2026-09"),
                     "identity-label")
    assert line_identity.LABEL_UNRESOLVED in labels
    assert line_identity.LABEL_MISSING_PRICE in labels


def test_pi_12_no_new_product_identity_page_is_created(client):
    """`PI-12` — không có trang/sheet/tab "Mã chưa nhận diện" nào được thêm."""
    rules = {str(rule) for rule in client.application.url_map.iter_rules()}
    for forbidden in ("/ma-chua-nhan-dien", "/product-identity", "/nhan-dien",
                      "/du-lieu/nhan-dien", "/kinh-doanh/nhan-dien"):
        assert forbidden not in rules, forbidden
    # Và luồng phân loại nằm DƯỚI route của chính không gian làm việc.
    assert "/kinh-doanh/nhan-vien/phan-loai" in rules


def test_pi_04_and_07_to_09_classifying_flips_the_line_to_thieu_gia(
    repository, service, client, tracking_on, identity_store
):
    """`PI-04`·`PI-05`·`PI-07`·`PI-08`·`PI-09` — một vòng đi hết từ đầu đến cuối.

    Đây là test quan trọng nhất của phần nhận diện: nó không hỏi "route có
    200 không" mà hỏi "Owner có đi được từ Chưa phân loại sang trạng thái
    đúng tiếp theo không", và nó đi qua thẩm quyền Product Identity thật.
    """
    persist(repository, [unresolved_line()])
    detail = next(iter(service.period(**SEPTEMBER).details))

    # `PI-04` — bấm vào mã mở bảng chọn NGAY trong sheet.
    panel = body(client, "/kinh-doanh/nhan-vien?ky=2026-09&phan-loai=1"
                 f"&order_key=BH73877&product_key={detail['product_key']}"
                 f"&occurrence_index={detail['occurrence_index']}")
    assert 'data-metric="identify-panel"' in panel
    # Khẳng định trên chính Ô CHỌN, không trên cả trang: tên hàng thô của
    # dòng này CHỨA mã "EWF1143R7SC", nên một phép tìm trên cả trang sẽ xanh
    # ngay cả khi danh mục Tracking hoàn toàn không đọc được.
    options = re.search(r'data-metric="identify-select".*?</select>',
                        panel, re.S)
    assert options is not None, "phải có ô chọn mặt hàng Tracking"
    assert 'value="EWF1143R7SC"' in options.group(0)

    # `PI-05` — xác nhận đi qua thẩm quyền Tracking.
    response = client.post("/kinh-doanh/nhan-vien/phan-loai", data={
        "ky": "2026-09", "order_key": "BH73877",
        "product_key": detail["product_key"],
        "occurrence_index": str(detail["occurrence_index"]),
        "ma_tracking": "EWF1143R7SC"})
    assert response.status_code == 302

    mappings = list(identity_store.read_at_revision(
        identity_store.current_revision()).alias_index().values())
    assert len(mappings) == 1
    assert mappings[0].status is MappingStatus.CONFIRMED
    assert mappings[0].mapping_source is MappingSource.HUMAN_CONFIRMATION
    assert mappings[0].source_product_code == "EWF1143R7SC"

    # `PI-07`/`PI-09` — dòng tự tính lại trạng thái, và vì giá vẫn chưa có
    # nó dừng ở "Thiếu giá". `PI-08` là mặt kia của cùng bất biến: giá KHÔNG
    # được bịa ra chỉ vì đã nhận diện xong (`ECONOMIC_ISOLATION`).
    labels = metrics(body(client, "/kinh-doanh/nhan-vien?ky=2026-09"),
                     "identity-label")
    assert labels == [line_identity.LABEL_MISSING_PRICE]


def test_pi_06_reports_never_writes_inv_map_as_a_second_authority():
    """`PI-06` — không đường ghi nào ra `inv.map` tồn tại trong tầng web.

    Một phủ định TOÀN CỤC trên chính mã nguồn, không phải hành vi của một
    case: nó chặn cả những đường ghi mà chưa ai viết.
    """
    import pathlib
    forbidden = re.compile(
        r"inv_map\w*\s*\[|write_inv_map|put_inv_map|set_inv_map|"
        r"inv\.map.*=\s*[^=]", re.IGNORECASE)
    for path in pathlib.Path("app/web").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert not forbidden.search(text), path


def test_pi_05_an_invented_tracking_code_is_refused(
    repository, service, client, tracking_on, identity_store
):
    """Mã không có trong danh mục Tracking KHÔNG tạo được mapping.

    Không có cửa này, một mã gõ tay sẽ thành một mapping `CONFIRMED` trỏ tới
    hư không — và Reports vừa tự phong mình làm thẩm quyền identity.
    """
    persist(repository, [unresolved_line()])
    detail = next(iter(service.period(**SEPTEMBER).details))
    client.post("/kinh-doanh/nhan-vien/phan-loai", data={
        "ky": "2026-09", "order_key": "BH73877",
        "product_key": detail["product_key"],
        "occurrence_index": str(detail["occurrence_index"]),
        "ma_tracking": "MA-BIA-RA"})
    assert identity_store.current_revision() == 0, "không được ghi gì"


def test_a_code_missing_from_the_board_is_not_offered(snapshot):
    """`INV-14c` — mã đã bỏ khỏi board không được đưa ra để tạo mapping MỚI."""
    codes = {item.code for item in identity_gateway.candidates(snapshot)}
    assert "EWF1143R7SC" in codes
    assert "DA-BO" not in codes


def test_pi_10_and_11_one_compact_warning_points_into_the_same_sheet(
    repository, client
):
    """`PI-10`/`PI-11` — MỘT dòng cảnh báo, và nó dẫn vào chính bảng này."""
    persist(repository, [unresolved_line("BH1"), unresolved_line("BH2"),
                         line("BH3", "43F6000", day=5)])
    html = body(client, "/kinh-doanh/nhan-vien?ky=2026-09")
    assert html.count('data-metric="identity-warning"') == 1, (
        "đúng MỘT cảnh báo, không phải một danh sách")
    warning = metric(html, "identity-warning-link")
    assert "BH1" in warning and "BH2" in warning
    # `PI-11` — đích của đường dẫn là một khối BH của CHÍNH bảng này.
    target = re.search(r'data-metric="identity-warning-link"[^>]*', html).group(0)
    anchor = re.search(r'href="#(bh-[^"]+)"',
                       re.search(r'data-metric="identity-warning".*?</p>',
                                 html, re.S).group(0)).group(1)
    assert f'id="{anchor}"' in html, "đường dẫn phải trỏ tới một khối có thật"
    assert target


def test_the_warning_counts_bh_and_stays_one_line_when_there_are_many(
    repository, client
):
    """`§13` — nhiều BH ⟹ ĐẾM, không liệt kê. Cảnh báo vẫn là một dòng."""
    persist(repository, [unresolved_line(f"BH{index}") for index in range(1, 8)])
    html = body(client, "/kinh-doanh/nhan-vien?ky=2026-09")
    assert "Có 7 BH chứa mã chưa được phân loại." in html
    assert html.count('data-metric="identity-warning"') == 1


def test_no_warning_at_all_when_every_line_is_identified(repository, client):
    """Trạng thái BÌNH THƯỜNG không chiếm một dòng trên đầu mọi sheet."""
    persist(repository, [line("BH1", "43F6000", day=5)])
    assert 'data-metric="identity-warning"' not in body(
        client, "/kinh-doanh/nhan-vien?ky=2026-09")


# ==========================================================================
# F02-01…F02-06 — gán lại BH phủ CẢ dòng đã bị loại
# ==========================================================================

def test_f02_the_mandatory_end_to_end_case(repository, service, store, client):
    """`F02-01`…`F02-06` — đúng kịch bản Owner đã viết ra, từng bước một.

        BH ba dòng, tất cả của Vinh
        loại dòng 2
        gán lại cả BH:  Vinh → Ly
        khôi phục dòng 2
        ⟹ cả ba dòng là của Ly. KHÔNG có gán tách đôi.
    """
    persist(repository, [
        line("BH9", "43F6000", occurrence=1, day=5, employee="Vinh", row=6),
        line("BH9", "XP352AE", occurrence=1, day=5, employee="Vinh", row=7),
        line("BH9", "Giá treo", occurrence=1, day=5, employee="Vinh", row=8),
    ])
    details = service.period(**SEPTEMBER).details
    assert len(details) == 3
    second = next(item for item in details if item["product_raw"] == "XP352AE")

    # F02-01 — loại dòng 2.
    store.exclude_line(order_key="BH9", product_key=second["product_key"],
                       occurrence_index=second["occurrence_index"])
    assert len(service.period(**SEPTEMBER).details) == 2

    # F02-02 — gán lại cả BH qua chính màn hình thật.
    response = client.post("/kinh-doanh/nhan-vien/don", data={
        "ky": "2026-09", "order_key": "BH9", "nhan_vien_moi": "Ly"})
    assert response.status_code == 302

    # F02-03 — dòng ĐANG BỊ LOẠI cũng đã đổi nhân viên.
    assignments = store.employee_overrides()
    assert len(assignments) == 3, (
        "cả ba dòng của BH phải có quyết định gán, kể cả dòng đang bị loại")
    assert {row["employee_normalized"] for row in assignments.values()} == {"Ly"}

    # F02-04 — khôi phục dòng 2.
    store.restore_line(order_key="BH9", product_key=second["product_key"],
                       occurrence_index=second["occurrence_index"])

    # F02-05/F02-06 — cả ba dòng là của Ly, một thẩm quyền duy nhất.
    restored = service.period(**SEPTEMBER)
    assert len(restored.details) == 3
    assert {item["line"].employee for item in restored.details} == {"Ly"}


def test_f02_the_screen_says_how_many_hidden_lines_were_reassigned(
    repository, service, store, client
):
    """Thao tác chạm tới những dòng KHÔNG hiện trên màn hình, nên nó nói ra.

    Một thao tác âm thầm sửa dữ liệu người dùng không nhìn thấy là đúng thứ
    làm mất lòng tin vào một nút bấm, kể cả khi nó làm điều đúng.
    """
    persist(repository, [
        line("BH9", "43F6000", occurrence=1, day=5, employee="Vinh", row=6),
        line("BH9", "XP352AE", occurrence=1, day=5, employee="Vinh", row=7),
    ])
    hidden = next(item for item in service.period(**SEPTEMBER).details
                  if item["product_raw"] == "XP352AE")
    store.exclude_line(order_key="BH9", product_key=hidden["product_key"],
                       occurrence_index=hidden["occurrence_index"])
    response = client.post("/kinh-doanh/nhan-vien/don", data={
        "ky": "2026-09", "order_key": "BH9", "nhan_vien_moi": "Ly"},
        follow_redirects=True)
    assert "đang bị loại khỏi báo cáo" in response.get_data(as_text=True)


def test_f02_reassignment_creates_no_second_attribution_table(engine):
    """`§14` — bản sửa dùng LẠI thẩm quyền gán đã có, không dựng bảng mới."""
    from sqlalchemy import inspect
    tables = set(inspect(engine).get_table_names())
    assert "employee_attribution_override" in tables
    for invented in ("bh_employee_override", "order_employee_override",
                     "employee_attribution_v2"):
        assert invented not in tables


# ==========================================================================
# F03-01…F03-06 — loại dòng = loại khỏi BÁO CÁO CHÍNH THỨC
# ==========================================================================

def kpi(html: str, name: str) -> str:
    return metric(html, name)


def test_f03_01_to_04_every_official_surface_drops_by_the_same_amount(
    repository, service, store, client
):
    """`F03-01`…`F03-04` — Báo cáo, Nhân viên và biểu đồ cùng giảm, cùng lượng.

    Đây là bất biến mà `F-03` sinh ra để canh: hai màn hình nghiệp vụ chính
    KHÔNG BAO GIỜ được nói hai con số doanh thu chính thức khác nhau.
    """
    persist(repository, [
        line("BH1", "43F6000", day=5, sell="8000000"),
        line("BH2", "XP352", day=5, sell="2000000"),
    ])
    summary_before = kpi(body(client, "/kinh-doanh?ky=2026-09"), "sales_revenue")
    sheet_before = kpi(body(client, "/kinh-doanh/nhan-vien?ky=2026-09"),
                       "sales_revenue")
    chart_before = chart_bars(body(client, "/kinh-doanh?muc=ngay"))["2026-09-05"]
    assert summary_before == sheet_before, (
        "trước khi loại, hai màn hình đã phải nói cùng một con số")

    detail = next(item for item in service.period(**SEPTEMBER).details
                  if item["order_key"] == "BH2")
    store.exclude_line(order_key="BH2", product_key=detail["product_key"],
                       occurrence_index=detail["occurrence_index"])

    summary_after = kpi(body(client, "/kinh-doanh?ky=2026-09"), "sales_revenue")
    sheet_after = kpi(body(client, "/kinh-doanh/nhan-vien?ky=2026-09"),
                      "sales_revenue")
    chart_after = chart_bars(body(client, "/kinh-doanh?muc=ngay"))["2026-09-05"]

    assert summary_after == sheet_after, "hai màn hình vẫn phải khớp nhau"
    assert summary_after != summary_before, "Báo cáo phải giảm"
    assert chart_before - chart_after == Decimal("2000000")


def test_f03_05_the_raw_accounting_record_is_untouched(
    engine, repository, service, store
):
    """`F03-05` — loại một dòng KHÔNG xoá một dòng kế toán nào."""
    from sqlalchemy import func, select
    from tools.db.schema import order_line_current, order_line_source_version
    persist(repository, [line("BH1", "43F6000", day=5),
                         line("BH2", "XP352", day=5)])

    def counts():
        with engine.connect() as conn:
            return (
                conn.execute(select(func.count()).select_from(
                    order_line_current)).scalar_one(),
                conn.execute(select(func.count()).select_from(
                    order_line_source_version)).scalar_one())

    before = counts()
    detail = next(item for item in service.period(**SEPTEMBER).details
                  if item["order_key"] == "BH2")
    store.exclude_line(order_key="BH2", product_key=detail["product_key"],
                       occurrence_index=detail["occurrence_index"])
    assert counts() == before, "bản ghi append-only phải nguyên vẹn"


def test_f03_06_surviving_raw_revenue_screens_declare_themselves(
    repository, client
):
    """`F03-06` — trang thô còn sống phải TỰ NÓI RA rằng nó là bằng chứng.

    Chúng đọc thẳng sổ đã nạp nên không trừ dòng bị loại. Chúng được phép
    tồn tại (`§17` cấm phá bằng chứng kế toán) và đã rời thanh tab chính —
    điều còn lại là chúng không được trông như một màn hình chỉ tiêu.
    """
    persist(repository, [line("BH1", "43F6000", day=5)])
    for path in ("/tong-quan?ky=2026-09", "/ban-hang?ky=2026-09",
                 "/san-pham?ky=2026-09", "/nhan-vien?nguon=moi"):
        html = body(client, path)
        assert 'data-metric="raw-surface"' in html, path


def test_f03_06_the_old_sellers_page_no_longer_lights_the_nhan_vien_tab(
    repository, client
):
    """Hai màn hình khác nhau không được cùng làm sáng một tab.

    Trang `/nhan-vien` đọc sổ THÔ; tab "Nhân viên" trỏ tới không gian làm
    việc nghiệp vụ. Trước bản sửa này cả hai dùng chung khoá `active_tab`,
    nên thanh tab nói rằng đang ở cùng một chỗ trong khi hai con số doanh
    thu khác nhau.
    """
    persist(repository, [line("BH1", "43F6000", day=5)])
    nav = re.search(r'<nav class="ncc-tabs">(.*?)</nav>',
                    body(client, "/nhan-vien?nguon=moi"), re.S).group(1)
    on = re.findall(r'class="ncc-tab on"[^>]*>([^<]+)<', nav)
    assert on == [], "trang sổ thô không làm sáng tab nghiệp vụ nào"


def test_the_official_business_screens_are_all_exclusion_aware(
    repository, service, store, client
):
    """Mọi trang thuộc tab Nhân viên đọc CÙNG một kết quả đã trừ dòng loại."""
    persist(repository, [line("BH1", "43F6000", day=5, sell="8000000"),
                         line("BH2", "XP352", day=5, sell="2000000")])
    detail = next(item for item in service.period(**SEPTEMBER).details
                  if item["order_key"] == "BH2")
    store.exclude_line(order_key="BH2", product_key=detail["product_key"],
                       occurrence_index=detail["occurrence_index"])
    for path in ("/kinh-doanh/gia-nhap?ky=2026-09&loc=tat-ca",
                 "/kinh-doanh/target?ky=2026-09"):
        assert "XP352" not in body(client, path), path


# ==========================================================================
# Bất biến của module thuần — kiểm trên giá trị, không qua HTML
# ==========================================================================

def test_the_timeline_module_never_puts_one_line_in_two_buckets():
    """Mỗi mức gộp là một PHÂN HOẠCH của cùng một tập dòng."""
    class L:
        total_sales = Decimal("1000")
        pending_reasons = ()
        purchase_price = Decimal("1")
    details = [{"sale_date": date(2026, 1, day), "line": L()}
               for day in (1, 15, 31)]
    totals = {
        gran: rt.totals_of(rt.series(details, granularity=gran))
        for gran in rt.GRANULARITY_KEYS
    }
    assert set(totals.values()) == {Decimal("3000")}


def test_an_undated_line_lands_in_no_bucket_at_all():
    """`R-S5` — dòng không có ngày bán không được nhét vào một ngày nào đó."""
    class L:
        total_sales = Decimal("500")
        pending_reasons = ()
        purchase_price = Decimal("1")
    details = [{"sale_date": None, "line": L()},
               {"sale_date": date(2026, 1, 5), "line": L()}]
    points = rt.series(details, granularity=rt.DAY)
    assert len(points) == 1
    assert rt.undated_count(details) == 1


def test_a_bad_granularity_falls_back_without_pretending_to_understand():
    assert rt.parse_granularity("khong-co-that") == rt.DEFAULT_GRANULARITY
    assert rt.parse_granularity(None) == rt.DEFAULT_GRANULARITY
    assert rt.parse_granularity("quy") == rt.QUARTER


def test_a_quarter_built_from_fewer_months_says_so():
    """`CHART-08` — "theo bằng chứng có được" phải NHÌN THẤY được."""
    class L:
        total_sales = Decimal("1000")
        pending_reasons = ()
        purchase_price = Decimal("1")
    points = rt.series([{"sale_date": date(2026, 1, 5), "line": L()}],
                       granularity=rt.QUARTER)
    assert points[0].partial is True
    assert points[0].covered_months == 1 and points[0].span_months == 3


# ==========================================================================
# E2E — MỘT lần đi hết, qua ứng dụng Flask THẬT
#
# Bốn đoạn của `§33`, nối liền trong một phiên: đổi mức gộp biểu đồ, phân
# loại một mã ngay trong sheet, loại → gán lại BH → khôi phục, rồi kiểm ba
# bề mặt nghiệp vụ nói cùng một con số.
#
# Test này cố ý DÀI. Bốn đoạn ấy chỉ chứng minh được điều cần chứng minh khi
# chúng chạy trên CÙNG một trạng thái: tách thành bốn test độc lập sẽ để lọt
# đúng lớp lỗi mà nó tồn tại để bắt — một thao tác làm hỏng kết quả của thao
# tác trước đó.
# ==========================================================================

def test_e2e_the_owner_walks_the_whole_slice_in_one_session(
    engine, repository, service, store, client, tracking_on, identity_store
):
    persist(repository, [
        line("BH50", "43F6000", occurrence=1, day=5, employee="Vinh",
             row=6, sell="8000000"),
        line("BH50", "Máy giặt Electrolux EWF1143R7SC", occurrence=1, day=5,
             employee="Vinh", row=7, sell="2000000", kpi_purchase=None,
             kpi_profit=None, status="PENDING", reasons=UNRESOLVED),
        line("BH50", "Giá treo", occurrence=1, day=5, employee="Vinh",
             row=8, sell="500000"),
    ])
    seed_legacy(engine, [(6, 10, 30000000)], year=2025)

    # --- 1. Báo cáo: đổi mức gộp Ngày → Tuần → Tháng → Quý → Năm ---------
    totals = {}
    for gran in ("ngay", "tuan", "thang", "quy", "nam"):
        html = body(client, f"/kinh-doanh?muc={gran}")
        assert html.count('data-metric="chart"') == 1, gran
        assert f'data-gran="{gran}"' in html
        totals[gran] = sum(chart_bars(html).values())
    assert len(set(totals.values())) == 1, (
        f"năm mức gộp phải cộng ra CÙNG một tổng: {totals}")

    # --- 2. Nhân viên: tháng hiện tại, dòng chưa phân loại, phân loại ----
    sheet = body(client, "/kinh-doanh/nhan-vien")
    assert "Tháng 09/2026" in sheet or "09/2026" in sheet
    assert line_identity.LABEL_UNRESOLVED in metrics(sheet, "identity-label")
    assert 'data-metric="identity-warning"' in sheet

    target = next(item for item in service.period(**SEPTEMBER).details
                  if item["product_raw"].startswith("Máy giặt"))
    panel = body(client, "/kinh-doanh/nhan-vien?ky=2026-09&phan-loai=1"
                 f"&order_key=BH50&product_key={target['product_key']}"
                 f"&occurrence_index={target['occurrence_index']}")
    assert 'value="EWF1143R7SC"' in panel

    assert client.post("/kinh-doanh/nhan-vien/phan-loai", data={
        "ky": "2026-09", "order_key": "BH50",
        "product_key": target["product_key"],
        "occurrence_index": str(target["occurrence_index"]),
        "ma_tracking": "EWF1143R7SC"}).status_code == 302

    after = body(client, "/kinh-doanh/nhan-vien?ky=2026-09")
    assert line_identity.LABEL_UNRESOLVED not in metrics(after, "identity-label")
    assert line_identity.LABEL_MISSING_PRICE in metrics(after, "identity-label")
    assert 'data-metric="identity-warning"' not in after, (
        "hết dòng chưa phân loại ⟹ cảnh báo biến mất")

    # --- 3. Cùng BH: loại dòng → gán lại BH → khôi phục ------------------
    hidden = next(item for item in service.period(**SEPTEMBER).details
                  if item["product_raw"] == "Giá treo")
    assert client.post("/kinh-doanh/nhan-vien/loai-dong", data={
        "ky": "2026-09", "order_key": "BH50",
        "product_key": hidden["product_key"],
        "occurrence_index": str(hidden["occurrence_index"])}).status_code == 302

    assert client.post("/kinh-doanh/nhan-vien/don", data={
        "ky": "2026-09", "order_key": "BH50",
        "nhan_vien_moi": "Ly"}).status_code == 302

    assert client.post("/kinh-doanh/nhan-vien/loai-dong", data={
        "ky": "2026-09", "order_key": "BH50", "hanh-dong": "khoi-phuc",
        "product_key": hidden["product_key"],
        "occurrence_index": str(hidden["occurrence_index"])}).status_code == 302

    restored = service.period(**SEPTEMBER)
    assert len(restored.details) == 3
    assert {item["line"].employee for item in restored.details} == {"Ly"}, (
        "dòng khôi phục phải mang nhân viên MỚI — không có gán tách đôi")

    # --- 4. Loại một dòng: ba bề mặt nghiệp vụ cùng nói một con số -------
    dropped = next(item for item in restored.details
                   if item["product_raw"] == "43F6000")
    assert client.post("/kinh-doanh/nhan-vien/loai-dong", data={
        "ky": "2026-09", "order_key": "BH50",
        "product_key": dropped["product_key"],
        "occurrence_index": str(dropped["occurrence_index"])}).status_code == 302

    summary = metric(body(client, "/kinh-doanh?ky=2026-09"), "sales_revenue")
    # Trang Nhân viên hiện chỉ tiêu của MỘT SHEET, nên phép so đúng là so với
    # sheet đang giữ các dòng — sau lần gán lại, đó là sheet của Ly. So tổng
    # kỳ với một sheet bất kỳ là một phép so sai, và `§42` đã nói vì sao:
    # sheet là một PHÂN HOẠCH, tổng của CHÚNG mới bằng tổng kỳ.
    employee = metric(
        body(client, "/kinh-doanh/nhan-vien?ky=2026-09&nhan-vien=Ly"),
        "sales_revenue")
    chart = chart_bars(body(client, "/kinh-doanh?muc=ngay"))["2026-09-05"]
    assert summary == employee, "Báo cáo và Nhân viên phải khớp"

    # Và bất biến phân hoạch của `§42` vẫn đúng sau mọi thao tác ở trên:
    # tổng của mọi sheet bằng đúng tổng kỳ.
    final = service.period(**SEPTEMBER)
    by_sheet = sum(
        (final.for_sheet(sheet).totals.sales_revenue or Decimal(0))
        for sheet in service.sheets(final))
    assert by_sheet == final.totals.sales_revenue
    assert chart == Decimal("2500000"), (
        "biểu đồ phải bỏ đúng dòng 8.000.000 vừa bị loại")

    # Và bản ghi kế toán gốc vẫn nguyên vẹn (`F03-05`).
    from sqlalchemy import func, select
    from tools.db.schema import order_line_current
    with engine.connect() as conn:
        assert conn.execute(select(func.count()).select_from(
            order_line_current)).scalar_one() == 3


def test_a_fractional_revenue_survives_the_round_trip_through_html(
    repository, client
):
    """Doanh thu có phần thập phân đọc lại được NGUYÊN VẸN từ biểu đồ.

    Chiết khấu làm `total_sales` lẻ, và một cột mang giá trị đã định dạng
    theo vi-VN (`1.000.000,50`) sẽ không đọc lại được bằng một phép gỡ dấu
    chấm — nhãn cho người đọc và giá trị cho máy đọc vì thế là HAI thuộc
    tính khác nhau, và test này là thứ giữ chúng khác nhau.
    """
    persist(repository, [line("BH1", "43F6000", day=5, sell="8000000",
                              discount="0.50")])
    bars = chart_bars(body(client, "/kinh-doanh?muc=ngay"))
    assert bars["2026-09-05"] == Decimal("7999999.50")
