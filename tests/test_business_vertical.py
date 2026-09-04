"""PHB-03 — vertical đầy đủ: quyết định của Owner → truy vấn → trang thật.

`tests/test_business_metrics.py` chứng minh NGỮ NGHĨA đúng trên giá trị thuần.
File này chứng minh cùng ngữ nghĩa đó SỐNG SÓT qua database, qua tầng ráp và
qua HTML — nghĩa là chứng minh vòng lặp mà PHB-03 §7 mô tả thật sự khép kín:

    NẠP SỔ → TÍNH → CẢNH BÁO THIẾU GIÁ → OWNER NHẬP → TÍNH LẠI
    → COVERAGE 100 % → LỢI NHUẬN KPI CHÍNH THỨC → DS QUY ĐỔI
"""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import create_engine

import tools.db as history_db
from app.modules.reporting import business_metrics as bm
from app.web import business_service, business_store, history_store
from app.web import server as web_server
from tests.test_snapshot_repository import result_line, source_line, write
from tools.tracking import live_pull

REPO_ROOT = Path(__file__).resolve().parents[1]

JANUARY = {"date_from": date(2026, 1, 1), "date_to": date(2026, 1, 31)}
DECEMBER = {"date_from": date(2025, 12, 1), "date_to": date(2025, 12, 31)}


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


def pair(order, *, product="Tủ lạnh Panasonic", occurrence=1, day=5, month=1,
         year=2026, employee="Vinh", group="NOI_THANH", lead="PERSONAL",
         status="AUTO", quantity="1", sell="8000000", discount="0",
         kpi_purchase="5000000", kpi_profit="3000000", rate="0.020",
         product_group="DIEN_MAY", row=6):
    """Một cặp (dòng nguồn, dòng kết quả) đã khớp khoá.

    `kpi_purchase=None` dựng đúng tình trạng của dữ liệu thật hôm nay: pipeline
    KHÔNG phân giải được giá nhập, nên cả giá lẫn lợi nhuận KPI đều `NULL`
    (mục 4.4 của hợp đồng — 100 % dòng golden ở trạng thái này).
    """
    source = source_line(order, product, occurrence, row=row,
                         sale_date=date(year, month, day), sell_price=sell,
                         quantity=Decimal(quantity), discount=Decimal(discount))
    base = result_line(source, status=status)
    result = type(base)(**{
        **{field: getattr(base, field) for field in base.__dataclass_fields__},
        "employee_normalized": employee, "employee_group": group,
        "lead_source_final": lead,
        "total_sales": Decimal(sell) * Decimal(quantity) - Decimal(discount),
        "kpi_purchase_price": None if kpi_purchase is None else Decimal(kpi_purchase),
        "eligible_kpi_profit": None if kpi_profit is None else Decimal(kpi_profit),
        "product_group_final": product_group,
        "conversion_rate_final": None if rate is None else Decimal(rate),
    })
    return source, result


def persist(repository, pairs, *, run_id="run-1", at="2026-02-01T00:00:00",
            fingerprint="fp-a"):
    return write(repository, [p[0] for p in pairs], run_id=run_id, created_at=at,
                 fingerprint=fingerprint, results=[p[1] for p in pairs])


# --- Vòng lặp hoàn thiện giá nhập, đi hết từ đầu đến cuối -----------------

def test_the_owner_workflow_closes_from_pending_to_official(repository, service):
    """PHB-03 §7 — một lần đi hết vòng, khẳng định TỪNG mốc.

    Đây là test quan trọng nhất của vertical: nó không hỏi "hàm này có chạy
    không" mà hỏi "Owner có thật sự đi được từ cảnh báo tới con số chính thức
    không", và nó chạy qua database thật.
    """
    persist(repository, [
        pair("BH1", kpi_purchase=None, kpi_profit=None),
        pair("BH2", product="Tivi Sony", kpi_purchase=None, kpi_profit=None),
    ])

    # Mốc 1 — chưa có giá nhập nào: không có số chính thức, và lý do nói rõ.
    data = service.period(**JANUARY)
    assert data.totals.coverage.covered_lines == 0
    assert data.totals.coverage.missing_price_lines == 2
    assert data.totals.official_kpi_profit is None
    assert data.totals.official_converted_sales is None
    assert data.totals.kpi_profit is None  # NULL, không phải 0

    # Mốc 2 — Owner nhập giá cho MỘT dòng: coverage nhích, vẫn chưa chính thức.
    first = data.details[0]
    exists, auto = service.auto_price_of(
        order_key=first["order_key"], product_key=first["product_key"],
        occurrence_index=first["occurrence_index"], data=data)
    assert exists and auto is None
    assert service.store.set_purchase_price(
        order_key=first["order_key"], product_key=first["product_key"],
        occurrence_index=first["occurrence_index"],
        price=Decimal("6000000"), auto_price=auto) == "MANUAL"

    data = service.period(**JANUARY)
    assert data.totals.coverage.covered_lines == 1
    assert data.totals.coverage.is_complete is False
    assert data.totals.official_kpi_profit is None
    assert data.totals.kpi_profit == Decimal("2000000")

    # Mốc 3 — nốt dòng còn lại: coverage 100 %, số trở thành CHÍNH THỨC.
    second = data.details[1]
    service.store.set_purchase_price(
        order_key=second["order_key"], product_key=second["product_key"],
        occurrence_index=second["occurrence_index"],
        price=Decimal("7000000"), auto_price=None)

    data = service.period(**JANUARY)
    assert data.totals.coverage.is_complete is True
    assert data.totals.state == bm.STATE_OFFICIAL
    assert data.totals.official_kpi_profit == Decimal("3000000")
    # Nhóm Nội thành, hàng thường ⟹ 2 %: 3.000.000 / 0,02 = 150.000.000
    assert data.totals.official_converted_sales == Decimal("150000000.00")


def test_editing_an_auto_price_records_override_and_moves_the_number(
    repository, service
):
    """Vector I qua database: AUTO → MANUAL_OVERRIDE → tính lại."""
    persist(repository, [pair("BH1", kpi_purchase="5000000", kpi_profit="3000000")])
    data = service.period(**JANUARY)
    assert data.lines[0].purchase_provenance == bm.PROVENANCE_AUTO
    assert data.totals.official_kpi_profit == Decimal("3000000")

    detail = data.details[0]
    _exists, auto = service.auto_price_of(
        order_key=detail["order_key"], product_key=detail["product_key"],
        occurrence_index=detail["occurrence_index"], data=data)
    assert auto == Decimal("5000000")
    assert service.store.set_purchase_price(
        order_key=detail["order_key"], product_key=detail["product_key"],
        occurrence_index=detail["occurrence_index"],
        price=Decimal("4000000"), auto_price=auto) == "MANUAL_OVERRIDE"

    data = service.period(**JANUARY)
    assert data.lines[0].purchase_provenance == bm.PROVENANCE_MANUAL_OVERRIDE
    # (8.000.000 − 4.000.000) × 1 − 0
    assert data.totals.official_kpi_profit == Decimal("4000000")


def test_the_stored_override_keeps_the_auto_price_it_replaced(repository, store):
    """Bằng chứng MỘT DÒNG cho chữ `MANUAL_OVERRIDE` — không có nó, "override"
    chỉ là một cái nhãn tự khai."""
    store.set_purchase_price(
        order_key="BH1", product_key="pk", occurrence_index=1,
        price=Decimal("4000000"), auto_price=Decimal("5000000"))
    row = store.purchase_price_overrides()[("BH1", "pk", 1)]
    assert row["provenance"] == "MANUAL_OVERRIDE"
    assert row["auto_price_at_entry"] == Decimal("5000000")


def test_clearing_an_override_returns_the_line_to_the_engine_number(
    repository, service
):
    persist(repository, [pair("BH1", kpi_purchase="5000000", kpi_profit="3000000")])
    keys = dict(order_key="BH1", product_key=service.period(**JANUARY)
                .details[0]["product_key"], occurrence_index=1)
    service.store.set_purchase_price(price=Decimal("1"), auto_price=Decimal("5000000"),
                                     **keys)
    assert service.period(**JANUARY).totals.kpi_profit == Decimal("7999999")

    service.store.clear_purchase_price(**keys)
    data = service.period(**JANUARY)
    assert data.lines[0].purchase_provenance == bm.PROVENANCE_AUTO
    assert data.totals.kpi_profit == Decimal("3000000")


def test_an_override_survives_a_re_import_of_the_same_book(repository, service):
    """Khoá NGHIỆP VỤ, không phải `id` của version.

    Kế toán gửi lại sổ ⟹ version mới, `id` mới. Nếu override khoá theo `id`,
    mỗi lần gửi lại sổ sẽ xoá sạch việc Owner đã làm — và không ai được báo.
    """
    persist(repository, [pair("BH1", sell="8000000", kpi_purchase=None,
                              kpi_profit=None)])
    detail = service.period(**JANUARY).details[0]
    service.store.set_purchase_price(
        order_key=detail["order_key"], product_key=detail["product_key"],
        occurrence_index=detail["occurrence_index"],
        price=Decimal("6000000"), auto_price=None)

    persist(repository, [pair("BH1", sell="9000000", kpi_purchase=None,
                              kpi_profit=None)],
            run_id="run-2", at="2026-02-02T00:00:00", fingerprint="fp-b")

    data = service.period(**JANUARY)
    assert data.lines[0].purchase_provenance == bm.PROVENANCE_MANUAL
    # Giá bán mới của lần nạp sau, giá nhập Owner đã nhập: 9.000.000 − 6.000.000
    assert data.totals.official_kpi_profit == Decimal("3000000")


@pytest.mark.parametrize("raw,expected", [
    ("6000000", Decimal("6000000")),
    ("6.000.000", Decimal("6000000")),
    ("6 000 000", Decimal("6000000")),
    ("6000000,5", Decimal("6000000.5")),
    ("0", Decimal(0)),
])
def test_the_owner_can_type_a_price_the_way_they_actually_write_numbers(
    raw, expected
):
    assert business_store.parse_purchase_price(raw) == expected


@pytest.mark.parametrize("raw", ["", "   ", "abc", "-1", "-1.000"])
def test_an_unusable_price_is_refused_instead_of_guessed(raw):
    """Giá nhập âm không phải sự thật nghiệp vụ nào; chấp nhận nó sẽ thổi
    phồng lợi nhuận KPI trong im lặng."""
    with pytest.raises(business_store.InvalidPurchasePriceError):
        business_store.parse_purchase_price(raw)


# --- Tick Gia dụng qua database ------------------------------------------

def test_ticking_gia_dung_reroutes_a_noi_thanh_line_from_two_to_eight_percent(
    repository, service
):
    """`DEC-PHB02-05` — và nó có hiệu lực NGAY, không cần nạp lại sổ."""
    persist(repository, [pair("BH1", product="Nồi chiên không dầu",
                              kpi_purchase="5000000", kpi_profit="3000000")])
    data = service.period(**JANUARY)
    assert data.totals.official_converted_sales == Decimal("150000000.00")

    service.store.set_product_group(
        product_key=data.details[0]["product_key"], product_group="GIA_DUNG")

    data = service.period(**JANUARY)
    assert data.lines[0].conversion_rate == Decimal("0.080")
    assert data.totals.official_converted_sales == Decimal("37500000.00")


def test_a_gia_dung_tick_does_not_move_a_retail_employee_to_eight_percent(
    repository, service
):
    """Vector L qua database — ranh giới là cấu trúc của bảng cấu hình."""
    persist(repository, [pair("BH1", employee="Ly", group="STANDARD_SALES",
                              rate="0.055", kpi_purchase="5000000",
                              kpi_profit="3000000")])
    service.store.set_product_group(
        product_key=service.period(**JANUARY).details[0]["product_key"],
        product_group="GIA_DUNG")
    assert service.period(**JANUARY).lines[0].conversion_rate == Decimal("0.055")


def test_a_classification_applies_to_the_product_in_every_later_period(
    repository, service
):
    """`DEC-PHB02-05`: tick MỘT LẦN cho mặt hàng, không tick lại mỗi kỳ."""
    persist(repository, [
        pair("BH1", month=1, day=5, product="Máy lọc không khí",
             kpi_purchase="5000000", kpi_profit="3000000"),
        pair("BH2", month=2, day=5, product="Máy lọc không khí", row=7,
             kpi_purchase="5000000", kpi_profit="3000000"),
    ])
    service.store.set_product_group(
        product_key=service.period(**JANUARY).details[0]["product_key"],
        product_group="GIA_DUNG")
    february = service.period(date_from=date(2026, 2, 1), date_to=date(2026, 2, 28))
    assert february.lines[0].conversion_rate == Decimal("0.080")


def test_an_invalid_product_group_is_refused(store):
    with pytest.raises(business_store.InvalidProductGroupError):
        store.set_product_group(product_key="pk", product_group="NOI_THAT")


# --- Trang thật ------------------------------------------------------------

@pytest.fixture
def app(monkeypatch, tmp_path, engine, repository):
    legacy = history_store.build(engine=engine)
    monkeypatch.setattr(web_server, "UPLOAD_DIR", tmp_path / "uploads")
    monkeypatch.setattr(web_server, "ARTIFACT_DIR", (tmp_path / "outputs").resolve())
    monkeypatch.setattr(web_server, "select_latest_valid_captures", lambda: None)
    monkeypatch.setattr(live_pull, "is_configured", lambda env=None: False)
    application = web_server.create_app(db_path=tmp_path / "runs.db", history=legacy,
                                        snapshots=repository)
    application.testing = True
    return application


@pytest.fixture
def client(app):
    return app.test_client()


def body(client, path: str) -> str:
    response = client.get(path)
    assert response.status_code == 200, f"{path} → {response.status_code}"
    return response.get_data(as_text=True)


def metric(html: str, name: str) -> str:
    match = re.search(rf'data-metric="{re.escape(name)}"[^>]*>(.*?)<', html, re.S)
    assert match is not None, f"không tìm thấy data-metric={name}"
    return match.group(1).strip()


def test_the_summary_page_never_presents_a_partial_profit_as_official(
    repository, client
):
    """`R-S7` — dưới 100 % coverage, trang phải NÓI RA rằng số chưa chính thức."""
    persist(repository, [
        pair("BH1", kpi_purchase="5000000", kpi_profit="3000000"),
        pair("BH2", product="Tivi Sony", kpi_purchase=None, kpi_profit=None),
    ])
    html = body(client, "/kinh-doanh?ky=2026-01")
    assert metric(html, "state") == "CHƯA HOÀN CHỈNH"
    assert metric(html, "coverage") == "1 / 2 dòng"
    assert metric(html, "missing-price-lines") == "1"
    assert "CHÍNH THỨC" not in metric(html, "coverage-note")


def test_the_summary_page_marks_the_numbers_official_at_full_coverage(
    repository, client
):
    persist(repository, [pair("BH1", kpi_purchase="5000000", kpi_profit="3000000")])
    html = body(client, "/kinh-doanh?ky=2026-01")
    assert metric(html, "state") == "CHÍNH THỨC"
    assert metric(html, "coverage") == "1 / 1 dòng"
    assert metric(html, "kpi_profit") == "3.000.000"
    assert metric(html, "converted_sales") == "150.000.000"


def test_the_summary_shows_the_qualifying_quantity_not_every_line(
    repository, client
):
    """`R-S8`/`DEC-PHB02-03` — giá treo và phụ kiện giá thấp bị loại."""
    persist(repository, [
        pair("BH1", sell="8000000", quantity="2"),
        pair("BH1", product="Giá treo Tivi", occurrence=1, row=7, sell="250000",
             quantity="9"),
    ])
    html = body(client, "/kinh-doanh?ky=2026-01")
    assert metric(html, "qualifying_quantity") == "2"


def test_month_over_month_compares_sales_revenue_and_says_so(repository, client):
    persist(repository, [
        pair("BH0", year=2025, month=12, sell="10000000"),
        pair("BH1", month=1, sell="12000000", row=7),
    ])
    html = body(client, "/kinh-doanh?ky=2026-01")
    assert metric(html, "mom") == "+20%"


def test_a_previous_month_with_no_data_never_shows_a_percentage(
    repository, client
):
    """`DEC-PHB02-07` — không vô cực, không `-100 %`, một câu chữ tường minh."""
    persist(repository, [pair("BH1", month=1)])
    html = body(client, "/kinh-doanh?ky=2026-01")
    assert metric(html, "mom") == "—"
    assert "Chưa có dữ liệu tháng trước" in metric(html, "mom-note")


def test_the_employee_page_is_one_page_with_a_picker_not_one_tab_each(
    repository, client
):
    """`R-E1`/`P1` — 56 sheet tay KHÔNG trở thành 56 trang web."""
    persist(repository, [
        pair("BH1", employee="Vinh"),
        pair("BH2", employee="Ly", group="STANDARD_SALES", rate="0.055", row=7),
    ])
    for name in ("Vinh", "Ly"):
        html = body(client, f"/kinh-doanh/nhan-vien?ky=2026-01&nhan-vien={name}")
        assert metric(html, "employee") == name
    # Không chọn ai ⟹ trang nói rõ, KHÔNG dựng một bảng toàn số 0.
    assert "Chưa chọn nhân viên" in body(client, "/kinh-doanh/nhan-vien?ky=2026-01")


def test_an_employee_who_did_not_sell_in_the_period_is_not_invented(
    repository, client
):
    persist(repository, [pair("BH1", employee="Vinh")])
    html = body(client, "/kinh-doanh/nhan-vien?ky=2026-01&nhan-vien=KhongCoAi")
    assert "Chưa chọn nhân viên" in html


def test_the_gia_dung_workflow_is_offered_to_noi_thanh_only(repository, client):
    """Vector M — bán lẻ thường KHÔNG thấy luồng này, và không vào được nó."""
    persist(repository, [
        pair("BH1", employee="Vinh", group="NOI_THANH"),
        pair("BH2", employee="Ly", group="STANDARD_SALES", rate="0.055", row=7),
    ])
    noi_thanh = body(client, "/kinh-doanh/nhan-vien?ky=2026-01&nhan-vien=Vinh")
    assert 'data-metric="gia-dung-available"' in noi_thanh
    retail = body(client, "/kinh-doanh/nhan-vien?ky=2026-01&nhan-vien=Ly")
    assert 'data-metric="gia-dung-available"' not in retail

    assert client.get("/kinh-doanh/gia-dung?ky=2026-01&nhan-vien=Vinh"
                      ).status_code == 200
    assert client.get("/kinh-doanh/gia-dung?ky=2026-01&nhan-vien=Ly"
                      ).status_code == 404
    assert client.post("/kinh-doanh/gia-dung?ky=2026-01",
                       data={"product_key": "x", "nhan-vien": "Ly",
                             "gia_dung": "1"}).status_code == 404


def test_posting_a_price_through_the_page_recalculates_the_report(
    repository, client
):
    """Vòng lặp §7 qua HTTP thật: cảnh báo → nhập → tính lại → chính thức."""
    persist(repository, [pair("BH1", kpi_purchase=None, kpi_profit=None)])
    html = body(client, "/kinh-doanh/gia-nhap?ky=2026-01")
    assert metric(html, "coverage") == "0 / 1 dòng"
    product_key = re.search(r'name="product_key" value="([0-9a-f]+)"', html).group(1)

    response = client.post("/kinh-doanh/gia-nhap?ky=2026-01", data={
        "order_key": "BH1", "product_key": product_key, "occurrence_index": "1",
        "ky": "2026-01", "gia_nhap": "6.000.000"})
    assert response.status_code == 302

    summary = body(client, "/kinh-doanh?ky=2026-01")
    assert metric(summary, "state") == "CHÍNH THỨC"
    assert metric(summary, "kpi_profit") == "2.000.000"


def test_the_page_refuses_a_bad_price_without_writing_anything(
    repository, client, store
):
    persist(repository, [pair("BH1", kpi_purchase=None, kpi_profit=None)])
    html = body(client, "/kinh-doanh/gia-nhap?ky=2026-01")
    product_key = re.search(r'name="product_key" value="([0-9a-f]+)"', html).group(1)
    response = client.post("/kinh-doanh/gia-nhap?ky=2026-01", data={
        "order_key": "BH1", "product_key": product_key, "occurrence_index": "1",
        "ky": "2026-01", "gia_nhap": "không phải số"}, follow_redirects=True)
    assert response.status_code == 200
    assert store.purchase_price_overrides() == {}


def test_a_price_post_for_a_line_that_does_not_exist_is_refused(
    repository, client, store
):
    """Khoá dòng đến TỪ TRÌNH DUYỆT, nên nó phải được xác thực lại ở server."""
    persist(repository, [pair("BH1", kpi_purchase=None, kpi_profit=None)])
    response = client.post("/kinh-doanh/gia-nhap?ky=2026-01", data={
        "order_key": "BH-KHONG-CO", "product_key": "deadbeef",
        "occurrence_index": "1", "ky": "2026-01", "gia_nhap": "1000"})
    assert response.status_code == 404
    assert store.purchase_price_overrides() == {}


def test_the_purchase_price_page_lets_the_owner_edit_an_auto_price(
    repository, client
):
    """`DEC-PHB02-02` §3 — ô giá nhập sửa được KỂ CẢ khi đã AUTO-fill."""
    persist(repository, [pair("BH1", kpi_purchase="5000000", kpi_profit="3000000")])
    missing_only = body(client, "/kinh-doanh/gia-nhap?ky=2026-01")
    assert "Mọi dòng của kỳ đã có giá nhập" in missing_only

    all_lines = body(client, "/kinh-doanh/gia-nhap?ky=2026-01&tat-ca=1")
    assert metric(all_lines, "provenance") == "Tự động"
    assert 'name="gia_nhap"' in all_lines


def test_the_business_pages_never_leak_pii(repository, client):
    """Hàng rào PII giống PRA-004: `product_raw` được phép, phần còn lại không.

    `employee_raw` ("Mr Vinh 0912…") và `imei` là dữ liệu cá nhân; chúng không
    có lý do gì xuất hiện trên một trang chỉ tiêu.
    """
    persist(repository, [pair("BH1", kpi_purchase=None, kpi_profit=None)])
    for path in ("/kinh-doanh?ky=2026-01",
                 "/kinh-doanh/nhan-vien?ky=2026-01&nhan-vien=Vinh",
                 "/kinh-doanh/gia-nhap?ky=2026-01&tat-ca=1"):
        html = body(client, path)
        assert "Vũ Hạnh Ly" not in html  # employee_raw của fixture
        assert "imei" not in html.lower()


def test_the_business_pages_return_503_when_there_is_no_history_store(
    monkeypatch, tmp_path
):
    """Lỗi hạ tầng KHÔNG BAO GIỜ được hiện thành "chưa có dữ liệu"."""
    monkeypatch.setattr(web_server, "select_latest_valid_captures", lambda: None)
    monkeypatch.setattr(live_pull, "is_configured", lambda env=None: False)
    application = web_server.create_app(db_path=tmp_path / "runs.db", history=None,
                                        snapshots=None)
    application.testing = True
    client = application.test_client()
    for path in ("/kinh-doanh", "/kinh-doanh/nhan-vien", "/kinh-doanh/gia-nhap",
                 "/kinh-doanh/gia-dung"):
        assert client.get(path).status_code == 503, path
