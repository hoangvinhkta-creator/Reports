"""R3 repair — `FIND-R3-IR-01` và `FIND-R3-IR-02` trên vân tay chốt kỳ.

Vân tay của một lần chốt kỳ có đúng MỘT việc: trả lời "bộ số hiện tại còn
đúng bằng bộ số đã được duyệt không". Independent Review tìm ra nó sai theo
CẢ HAI chiều, và hai chiều đó hỏng theo hai cách ngược nhau:

`FIND-R3-IR-01` — FALSE NEGATIVE. Payload thiếu phần lớn kết quả tài chính:
không tỉ lệ quy đổi, không DS quy đổi, không doanh thu, không số lượng/đơn
giá/chiết khấu, và không cả `product_key`/`occurrence_index` (nên hai dòng
khác nhau của cùng một đơn không phân biệt được). Hệ quả đo được: chuyển một
mặt hàng sang Gia dụng làm DS quy đổi rơi từ 150.000.000 xuống 37.500.000 mà
vân tay KHÔNG đổi — kỳ đã chốt báo "không có gì đổi".

`FIND-R3-IR-02` — FALSE POSITIVE. Payload cộng thêm
`len(store.purchase_price_overrides())`, tức số override của TOÀN DATABASE.
Owner gõ một giá tay cho tháng 02 làm tháng 01 đã chốt báo drift, dù không một
dòng nào của tháng 01 đổi.

Cả file này là bằng chứng tái hiện + nghiệm thu của bản repair.
"""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine

import tools.db as history_db
from app.history import keys
from app.modules.reporting import business_metrics as bm
from app.web import business_service, business_store, history_store
from app.web import server as web_server
from tests.test_business_vertical import pair, persist
from tools.tracking import live_pull

JANUARY = {"date_from": date(2026, 1, 1), "date_to": date(2026, 1, 31)}
FEBRUARY = {"date_from": date(2026, 2, 1), "date_to": date(2026, 2, 28)}
JAN, FEB = (2026, 1), (2026, 2)

PRODUCT = "Tủ lạnh Panasonic"


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


def product_key(product: str = PRODUCT) -> str:
    return keys.product_key(product)


def january(service):
    return service.period(**JANUARY, period=JAN)


def february(service):
    return service.period(**FEBRUARY, period=FEB)


def close_january(service):
    return service.close_period(period=JAN, data=january(service))


def _detail(*, order="BH1", product="pk-A", occurrence=1, **overrides) -> dict:
    """Một `detail` tối thiểu, dựng bằng tay — cho các bài đo hàm THUẦN."""
    values = dict(
        order_key=order, employee="Vinh", employee_group="NOI_THANH",
        status="AUTO", sell_price=Decimal("8000000"), quantity=Decimal("1"),
        discount=Decimal("0"), total_sales=Decimal("8000000"),
        auto_purchase_price=Decimal("5000000"),
        auto_kpi_profit=Decimal("3000000"), kpi_authority_valid=True,
        conversion_rate=Decimal("0.020"))
    values.update(overrides)
    return {"order_key": order, "product_key": product,
            "occurrence_index": occurrence, "sale_date": date(2026, 1, 5),
            "classified_product_group": None, "line": bm.BusinessLine(**values)}


#: Một dòng tháng 01 của nhân viên NỘI THÀNH, tỉ lệ quy đổi 2 %.
#: Lợi nhuận KPI 3.000.000 ⟹ DS quy đổi 150.000.000.
def january_line(**overrides):
    values = dict(order_key="BH1", product=PRODUCT, month=1, day=5,
                  employee="Vinh", group="NOI_THANH", sell="8000000",
                  kpi_purchase="5000000", kpi_profit="3000000", rate="0.020",
                  status="AUTO", row=6)
    values.update(overrides)
    order = values.pop("order_key")
    return pair(order, **values)


# --------------------------------------------------------------------------
# FIND-R3-IR-01 — false negative
# --------------------------------------------------------------------------

class TestTheFingerprintCoversTheWholeApprovedResult:
    def test_a_conversion_rate_change_is_drift(self, repository, service, store):
        """Ca tái hiện NGUYÊN VĂN của `FIND-R3-IR-01`.

        Cùng dòng, cùng giá nhập, cùng lợi nhuận, cùng nhân viên. Chỉ tỉ lệ
        quy đổi đổi 2 % → 8 % (Owner tick Gia dụng — một thao tác có thật trên
        giao diện, không phải một giá trị dựng tay).

        DS quy đổi rơi từ 150.000.000 xuống 37.500.000. Đó là một con số trên
        bảng lương; vân tay PHẢI thấy nó.
        """
        persist(repository, [january_line()])
        before = january(service)
        assert before.totals.converted_sales == Decimal("150000000")
        close_january(service)
        assert service.period_drift(period=JAN, data=january(service)) is False

        store.set_product_group(product_key=product_key(),
                                product_group="GIA_DUNG",
                                product_label=PRODUCT)
        after = january(service)
        assert after.totals.converted_sales == Decimal("37500000")
        # Lợi nhuận KPI KHÔNG đổi — đó chính là lý do payload cũ mù với ca này.
        assert after.totals.kpi_profit == before.totals.kpi_profit
        assert service.period_drift(period=JAN, data=after) is True

    def test_a_revenue_change_is_drift_even_when_the_old_fields_hold(
        self, repository, service
    ):
        """Doanh thu đổi trong khi MỌI trường của payload cũ giữ nguyên.

        `order_key`, giá nhập hiệu lực, provenance, lợi nhuận KPI, nhân viên,
        loại dòng — sáu trường của payload cũ — không đổi một chữ. Chỉ đơn giá
        và doanh thu đổi.
        """
        persist(repository, [january_line()], run_id="r1", fingerprint="fp-a")
        before = january(service)
        assert before.totals.sales_revenue == Decimal("8000000")
        close_january(service)

        persist(repository, [january_line(sell="9000000")],
                run_id="r2", at="2026-02-02T00:00:00", fingerprint="fp-b")
        after = january(service)
        assert after.totals.sales_revenue == Decimal("9000000")
        assert after.totals.kpi_profit == before.totals.kpi_profit
        assert service.period_drift(period=JAN, data=after) is True

    def test_swapping_two_prices_within_one_order_is_drift(
        self, repository, service, store
    ):
        """Hoán đổi giá nhập giữa hai dòng của CÙNG một đơn.

        Tổng giá nhập, tổng lợi nhuận và tập giá trị của cả kỳ đều KHÔNG đổi —
        chỉ "giá nào thuộc dòng nào". Đây đúng là hình dạng của lỗi gắn nhầm
        override mà R3 §1 tồn tại để chặn, nên vân tay phải thấy nó.

        Trung thực về mức độ đỏ: bài này ĐÃ xanh trên payload cũ, nhưng xanh
        một cách tình cờ — hai dòng khác giá nên thứ tự lặp làm chúng khác
        nhau. Nó không chứng minh danh tính dòng là đầy đủ; bài ngay dưới
        (`test_two_lines_differing_only_in_identity...`) mới chứng minh điều
        đó, và bài đó thì đỏ trên payload cũ.
        """
        persist(repository, [
            january_line(order_key="BH1", product="Tủ lạnh", row=6,
                         kpi_purchase="5000000", kpi_profit="3000000"),
            january_line(order_key="BH1", product="Máy giặt", row=7,
                         sell="6000000", kpi_purchase="4000000",
                         kpi_profit="2000000"),
        ])
        close_january(service)
        assert service.period_drift(period=JAN, data=january(service)) is False

        # HOÁN ĐỔI giá nhập tay giữa hai dòng: tổng giá nhập, tổng lợi nhuận
        # và tập giá trị của cả kỳ đều KHÔNG đổi — chỉ "giá nào của dòng nào".
        store.set_purchase_price(
            order_key="BH1", product_key=keys.product_key("Tủ lạnh"),
            occurrence_index=1, price=Decimal("4000000"),
            auto_price=Decimal("5000000"), entered_by="owner", reason="đổi")
        store.set_purchase_price(
            order_key="BH1", product_key=keys.product_key("Máy giặt"),
            occurrence_index=1, price=Decimal("5000000"),
            auto_price=Decimal("4000000"), entered_by="owner", reason="đổi")
        assert service.period_drift(period=JAN, data=january(service)) is True

    def test_two_lines_differing_only_in_identity_are_told_apart(self):
        """Danh tính dòng phải ĐẦY ĐỦ, đo trên hàm thuần.

        Hai dòng giống nhau ở MỌI trường kinh tế và chỉ khác `product_key` /
        `occurrence_index`. Payload cũ chỉ mang `order_key`, nên chúng cho ra
        hai khối byte GIỐNG HỆT — hai bộ dữ liệu khác nhau, một vân tay.

        Đây là phép đo trực tiếp của lỗ hổng danh tính, không phụ thuộc thứ tự
        lặp hay giá trị nào khác nhau một cách tình cờ.
        """
        from app.web import period_lock

        totals = business_service.snapshot_of(bm.totals([]))
        first = _detail(product="pk-A", occurrence=1)
        second = _detail(product="pk-B", occurrence=1)
        third = _detail(product="pk-A", occurrence=2)
        assert period_lock.content_fingerprint(
            details=[first], totals=totals) != period_lock.content_fingerprint(
            details=[second], totals=totals)
        assert period_lock.content_fingerprint(
            details=[first], totals=totals) != period_lock.content_fingerprint(
            details=[third], totals=totals)

    def test_the_totals_snapshot_is_part_of_the_fingerprint(self):
        """Cùng các dòng, KHÁC bản chụp chỉ tiêu ⟹ khác vân tay.

        Bản chụp và vân tay là hai cách viết của cùng một payload, nên chúng
        không thể trôi khỏi nhau.
        """
        from app.web import period_lock

        details = [_detail()]
        base = business_service.snapshot_of(bm.totals([]))
        assert period_lock.content_fingerprint(
            details=details, totals=base) != period_lock.content_fingerprint(
            details=details, totals={**base, "sales_revenue": "999"})

    def test_the_stored_snapshot_still_equals_the_screen(self, repository, service):
        """Yêu cầu 7 — bản chụp lưu lúc chốt vẫn đúng bằng màn hình."""
        persist(repository, [january_line()])
        data = january(service)
        close_january(service)
        closed = service.period_store.closed(year=2026, month=1)
        assert closed.totals["sales_revenue"] == str(data.totals.sales_revenue)
        assert closed.totals["kpi_profit"] == str(data.totals.kpi_profit)
        assert closed.totals["converted_sales"] == str(data.totals.converted_sales)
        assert closed.totals["state"] == data.totals.state
        assert closed.line_count == len(data.lines)


# --------------------------------------------------------------------------
# FIND-R3-IR-02 — false positive giữa các kỳ
# --------------------------------------------------------------------------

class TestTheFingerprintDependsOnlyOnItsOwnPeriod:
    def test_a_manual_price_in_february_never_drifts_january(
        self, repository, service, store
    ):
        """Ca tái hiện NGUYÊN VĂN của `FIND-R3-IR-02`, cả ba thao tác.

        Thêm · sửa · xoá một giá tay của tháng 02. Tháng 01 đã chốt không có
        một dòng nào đổi, nên nó KHÔNG được báo drift lần nào.
        """
        persist(repository, [
            january_line(row=6),
            january_line(order_key="BH2", month=2, day=10, row=7),
        ])
        close_january(service)
        assert service.period_drift(period=JAN, data=january(service)) is False

        february_keys = dict(order_key="BH2", product_key=product_key(),
                             occurrence_index=1)
        store.set_purchase_price(
            **february_keys, price=Decimal("4000000"),
            auto_price=Decimal("5000000"), entered_by="owner",
            reason="giá thật tháng 02")
        assert february(service).lines[0].purchase_price == Decimal("4000000")
        assert service.period_drift(period=JAN, data=january(service)) is False

        store.set_purchase_price(
            **february_keys, price=Decimal("4500000"),
            auto_price=Decimal("5000000"), entered_by="owner", reason="sửa lại")
        assert service.period_drift(period=JAN, data=january(service)) is False

        store.clear_purchase_price(**february_keys)
        assert service.period_drift(period=JAN, data=january(service)) is False

    def test_a_manual_price_in_january_is_drift(self, repository, service, store):
        """Chiều ngược lại (yêu cầu 4): sửa đúng dữ liệu của kỳ đã chốt."""
        persist(repository, [january_line()])
        close_january(service)
        store.set_purchase_price(
            order_key="BH1", product_key=product_key(), occurrence_index=1,
            price=Decimal("4000000"), auto_price=Decimal("5000000"),
            entered_by="owner", reason="giá thật")
        assert service.period_drift(period=JAN, data=january(service)) is True

    def test_an_employee_reassignment_in_february_never_drifts_january(
        self, repository, service, store
    ):
        """Cùng nguyên tắc, cho một loại quyết định KHÁC giá nhập."""
        persist(repository, [
            january_line(row=6),
            january_line(order_key="BH2", month=2, day=10, row=7),
        ])
        close_january(service)
        store.set_employee(order_key="BH2", product_key=product_key(),
                           occurrence_index=1, employee="Ly",
                           employee_group="LE", source_employee="Vinh")
        assert service.period_drift(period=JAN, data=january(service)) is False


# --------------------------------------------------------------------------
# Ổn định: cùng dữ liệu ⟹ cùng vân tay, bất kể thứ tự
# --------------------------------------------------------------------------

class TestTheFingerprintIsStable:
    def test_reimporting_the_same_data_is_not_drift(self, repository, service):
        """Yêu cầu 5 — nạp lại CÙNG dữ liệu không phải một thay đổi."""
        persist(repository, [january_line()], run_id="r1", fingerprint="fp-a")
        close_january(service)
        persist(repository, [january_line()], run_id="r2",
                at="2026-02-02T00:00:00", fingerprint="fp-a")
        assert service.period_drift(period=JAN, data=january(service)) is False

    def test_the_payload_does_not_depend_on_query_order(self, repository, service):
        """Thứ tự dòng trả về từ truy vấn KHÔNG được đổi vân tay.

        Đo trực tiếp trên hàm thuần: đảo ngược danh sách rồi tính lại. Nếu
        payload dựa vào thứ tự lặp thì hai giá trị sẽ khác nhau.
        """
        from app.web import period_lock

        persist(repository, [
            january_line(order_key="BH1", product="Tủ lạnh", row=6),
            january_line(order_key="BH2", product="Máy giặt", row=7,
                         sell="6000000", kpi_purchase="4000000",
                         kpi_profit="2000000"),
            january_line(order_key="BH3", product="Bếp từ", row=8,
                         sell="3000000", kpi_purchase="1000000",
                         kpi_profit="2000000"),
        ])
        data = january(service)
        forward = period_lock.content_fingerprint(
            details=data.details, totals=business_service.snapshot_of(data.totals))
        backward = period_lock.content_fingerprint(
            details=list(reversed(data.details)),
            totals=business_service.snapshot_of(data.totals))
        assert forward == backward


# --------------------------------------------------------------------------
# Yêu cầu 6 — qua route Flask THẬT
# --------------------------------------------------------------------------

@pytest.fixture
def client(engine, monkeypatch, tmp_path):
    monkeypatch.setattr(web_server, "select_latest_valid_captures", lambda: None)
    monkeypatch.setattr(live_pull, "is_configured", lambda env=None: False)
    monkeypatch.setattr(
        web_server.identity_gateway, "DEFAULT_LOG_PATH",
        tmp_path / "identity" / "mappings.jsonl")
    monkeypatch.setattr(
        web_server.identity_gateway, "DEFAULT_INDEX_PATH",
        tmp_path / "identity" / "index.json")
    application = web_server.create_app(
        db_path=tmp_path / "runs.db",
        history=history_store.LegacyRepository(engine),
        snapshots=history_store.SnapshotRepository(engine))
    application.testing = True
    return application.test_client()


def page(client, path: str) -> str:
    response = client.get(path)
    assert response.status_code == 200, f"{path} → {response.status_code}"
    return response.get_data(as_text=True)


def has_drift(html: str) -> bool:
    return 'data-metric="close-drift"' in html


def flat(html: str) -> str:
    """HTML đã gộp mọi chuỗi khoảng trắng — template xuống dòng giữa câu."""
    return re.sub(r"\s+", " ", html)


class TestTheDriftWarningThroughTheWeb:
    def test_the_close_page_warns_after_a_conversion_rate_change(
        self, repository, store, client
    ):
        """Chốt kỳ → tick Gia dụng → mở lại trang chốt kỳ và thấy cảnh báo."""
        persist(repository, [january_line()])
        assert client.post("/kinh-doanh/chot-ky",
                           data={"ky": "2026-01"}).status_code == 302
        assert not has_drift(page(client, "/kinh-doanh/chot-ky?ky=2026-01"))

        store.set_product_group(product_key=product_key(),
                                product_group="GIA_DUNG",
                                product_label=PRODUCT)
        html = page(client, "/kinh-doanh/chot-ky?ky=2026-01")
        assert has_drift(html)
        assert "Bộ số hiện tại đã KHÁC bộ số lúc chốt" in flat(html)

    def test_the_close_page_stays_quiet_for_another_period(
        self, repository, store, client
    ):
        persist(repository, [
            january_line(row=6),
            january_line(order_key="BH2", month=2, day=10, row=7),
        ])
        assert client.post("/kinh-doanh/chot-ky",
                           data={"ky": "2026-01"}).status_code == 302
        store.set_purchase_price(
            order_key="BH2", product_key=product_key(), occurrence_index=1,
            price=Decimal("4000000"), auto_price=Decimal("5000000"),
            entered_by="owner", reason="giá thật tháng 02")
        assert not has_drift(page(client, "/kinh-doanh/chot-ky?ky=2026-01"))
