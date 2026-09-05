"""`DEC-180` — chiết khấu trình bày kiểu sổ cũ, và MoM bắc qua ranh giới bàn giao.

Chủ dự án đã làm rõ một điều mà bản audit trước đó suy sai: sổ tay cũ KHÔNG
báo cáo doanh số gộp. Nó trừ chiết khấu bằng MỘT DÒNG ÂM đứng ngay sau dòng
hàng:

    Tủ lạnh      SL 1   giá bán 5.000.000   Tổng bán  5.000.000
    Chiết khấu   SL 1   giá bán 0           Tổng bán   -100.000
    ---------------------------------------------------------
                                            còn lại   4.900.000

Sổ kế toán hiện hành ghi cùng nghiệp vụ đó bằng một CỘT `discount`, và
pipeline đã trừ nó rồi. HAI CÁCH GHI, MỘT chỉ tiêu nghiệp vụ. Ba hệ quả, và
file này canh cả ba:

    A. Bảng kê hiện lại đúng hình dạng sổ cũ — mà KHÔNG trừ chiết khấu lần
       thứ hai. Bất biến: Σ(dòng hiển thị) == số canonical.
    B. `Tổng bán` cũ và `Doanh thu bán hàng` mới là cùng một chỉ tiêu, nên
       cổng so sánh liên-origin mở đúng cặp đó — và KHÔNG mở lây cặp nào khác.
    C. Tháng liền trước không có dòng số mới nhưng CÓ Tổng bán trong sổ cũ ⟹
       "So tháng trước" lấy mốc từ sổ cũ, kèm nhãn nguồn, sau khi chuẩn hoá
       đơn vị kVND → VND.

Đơn vị là chỗ hỏng im lặng nguy hiểm nhất của cả bản sửa (`Summary` = kVND,
số mới = VND), nên nó có khẳng định riêng: quên hệ số 1.000 cho ra một tỉ lệ
TRÔNG NHƯ THẬT, không như một lỗi.
"""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine

import tools.db as history_db
from app.legacy.models import LegacyWorkbook, MonthlyReference, SummaryRow
from app.modules.reporting import business_metrics as bm
from app.web import (
    business_presentation, business_service, business_store, history_store,
    legacy_reference,
)
from app.web import server as web_server
from tests.test_business_vertical import pair, persist
from tests.test_snapshot_repository import write  # noqa: F401 — dùng qua persist
from tools.tracking import live_pull

AUGUST = {"date_from": date(2026, 8, 1), "date_to": date(2026, 8, 31)}
SEPTEMBER = {"date_from": date(2026, 9, 1), "date_to": date(2026, 9, 30)}


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
def legacy(engine):
    return history_store.build(engine=engine)


@pytest.fixture
def app(monkeypatch, tmp_path, engine, repository, legacy):
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


# --------------------------------------------------------------------------
# Ca của chủ dự án, viết một lần và dùng lại ở mọi khẳng định bên dưới.
# --------------------------------------------------------------------------

SELL = Decimal("5000000")
DISCOUNT = Decimal("100000")
PURCHASE = Decimal("3000000")
RATE = Decimal("0.020")

CANONICAL_SALES = SELL - DISCOUNT                      # 4.900.000
CANONICAL_PROFIT = (SELL - PURCHASE) * 1 - DISCOUNT    # 1.900.000
CANONICAL_CONVERTED = bm.converted_sales(CANONICAL_PROFIT, RATE)


def owner_line(**kwargs) -> bm.BusinessLine:
    """Đúng ca chủ dự án mô tả, dựng thẳng ở tầng ngữ nghĩa."""
    base = dict(
        order_key="BH1", employee="Vinh", employee_group="NOI_THANH",
        status="AUTO", sell_price=SELL, quantity=Decimal(1), discount=DISCOUNT,
        total_sales=CANONICAL_SALES, auto_purchase_price=PURCHASE,
        auto_kpi_profit=CANONICAL_PROFIT, kpi_authority_valid=True,
        conversion_rate=RATE,
    )
    base.update(kwargs)
    return bm.BusinessLine(**base)


def discounted_pair(order="BH-CK", **kwargs):
    """Cặp (dòng nguồn, dòng kết quả) mang chiết khấu, cho đường đi qua DB."""
    defaults = dict(
        sell=str(SELL), discount=str(DISCOUNT), kpi_purchase=str(PURCHASE),
        kpi_profit=str(CANONICAL_PROFIT), rate=str(RATE),
    )
    defaults.update(kwargs)
    return pair(order, **defaults)


# ==========================================================================
# A. Phân rã hiển thị — CASE 1 · 2 · 3 · 5 · 6
# ==========================================================================

class TestDiscountDisplayDecomposition:
    def test_case_1_the_product_line_shows_the_amount_before_discount(self):
        """`CASE 1` — đúng ba con số chủ dự án viết ra."""
        product, discount = bm.display_contributions(owner_line())
        assert product.total_sales == Decimal("5000000")
        assert discount.total_sales == Decimal("-100000")
        assert product.total_sales + discount.total_sales == Decimal("4900000")
        assert CANONICAL_SALES == Decimal("4900000")

    def test_case_1_the_discount_line_wears_the_legacy_shape(self):
        """Sổ cũ ghi dòng chiết khấu là: SL 1 · giá bán 0 · giá nhập = chiết khấu."""
        _product, discount = bm.display_contributions(owner_line())
        assert discount.kind == bm.CONTRIBUTION_DISCOUNT
        assert discount.quantity == Decimal(1)
        assert discount.sell_price == Decimal(0)
        assert discount.purchase_price == DISCOUNT

    def test_case_2_the_kpi_profit_decomposition_sums_to_the_canonical_number(self):
        line = owner_line()
        parts = bm.display_contributions(line)
        assert sum(part.kpi_profit for part in parts) == line.kpi_profit
        assert line.kpi_profit == CANONICAL_PROFIT
        assert parts[1].kpi_profit == -DISCOUNT

    def test_case_3_the_converted_sales_decomposition_sums_exactly(self):
        line = owner_line()
        parts = bm.display_contributions(line)
        assert sum(part.converted_sales for part in parts) == line.converted_sales
        assert line.converted_sales == CANONICAL_CONVERTED

    @pytest.mark.parametrize("rate,discount", [
        ("0.075", "33333"), ("0.023", "7"), ("0.081", "999999"), ("0.02", "1"),
    ])
    def test_case_3_rounding_never_leaks_a_dong_out_of_the_total(self, rate, discount):
        """DS quy đổi là chỗ DUY NHẤT có làm tròn — bất biến phải TUYỆT ĐỐI.

        `1.000.000 / 7,5 %` là số thập phân vô hạn tuần hoàn, nên hai phép
        chia độc lập rồi cộng lại có thể lệch 0,01 VND so với một phép chia
        trên tổng. Bản sửa đặt phần dư vào dòng cha thay vì để nó rơi ra
        ngoài tổng; những tỉ lệ dưới đây là các ca hostile của quy ước đó.
        """
        line = owner_line(discount=Decimal(discount),
                          conversion_rate=Decimal(rate),
                          total_sales=SELL - Decimal(discount),
                          auto_kpi_profit=(SELL - PURCHASE) - Decimal(discount))
        parts = bm.display_contributions(line)
        assert sum(part.converted_sales for part in parts) == line.converted_sales

    def test_case_5_no_discount_means_no_synthetic_row(self):
        line = owner_line(discount=Decimal(0), total_sales=SELL,
                          auto_kpi_profit=SELL - PURCHASE)
        parts = bm.display_contributions(line)
        assert len(parts) == 1
        assert parts[0].kind == bm.CONTRIBUTION_PRODUCT
        assert parts[0].total_sales == line.total_sales

    def test_a_zero_discount_column_is_treated_as_no_discount(self):
        """Cột `discount` mặc định coalesce về 0 — 0 KHÔNG được đẻ ra một dòng."""
        assert len(bm.display_contributions(
            owner_line(discount=Decimal("0.00"), total_sales=SELL,
                       auto_kpi_profit=SELL - PURCHASE))) == 1

    def test_a_blocked_line_never_invents_a_negative_profit_out_of_nothing(self):
        """Dòng chưa tính được lợi nhuận ⟹ dòng chiết khấu cũng KHÔNG có số.

        Nếu dòng chiết khấu vẫn hiện `-100.000` trong khi dòng cha hiện `—`,
        tổng hiển thị sẽ vượt khỏi tổng canonical đúng bằng khoản chiết khấu.
        """
        line = owner_line(auto_purchase_price=None, auto_kpi_profit=None)
        assert line.kpi_profit is None
        parts = bm.display_contributions(line)
        assert [part.kpi_profit for part in parts] == [None, None]
        assert [part.converted_sales for part in parts] == [None, None]
        # Doanh thu kế toán vẫn có, nên nó VẪN được tách đôi.
        assert sum(part.total_sales for part in parts) == line.total_sales

    def test_case_6_each_discount_row_follows_its_own_parent(self):
        """`CASE 6` — nhiều dòng có chiết khấu ⟹ không có gán chéo."""
        details = [
            {"order_key": "BH1", "product_key": "k1", "occurrence_index": 1,
             "product_raw": "Tủ lạnh", "sale_date": date(2026, 9, 5),
             "line": owner_line(order_key="BH1", discount=Decimal("100000"),
                                total_sales=Decimal("4900000"),
                                auto_kpi_profit=Decimal("1900000"))},
            {"order_key": "BH2", "product_key": "k2", "occurrence_index": 1,
             "product_raw": "Máy giặt", "sale_date": date(2026, 9, 6),
             "line": owner_line(order_key="BH2", discount=Decimal("250000"),
                                total_sales=Decimal("4750000"),
                                auto_kpi_profit=Decimal("1750000"))},
        ]
        rows = business_presentation.detail_rows(details)
        assert [(row["order_key"], row["synthetic"]) for row in rows] == [
            ("BH1", False), ("BH1", True), ("BH2", False), ("BH2", True)]
        assert rows[1]["total_sales"]["text"] == "-100.000"
        assert rows[3]["total_sales"]["text"] == "-250.000"

    def test_the_discount_row_sits_immediately_after_its_parent(self):
        details = [
            {"order_key": "BH1", "product_key": "k1", "occurrence_index": 1,
             "product_raw": "Tủ lạnh", "sale_date": date(2026, 9, 5),
             "line": owner_line()},
            {"order_key": "BH2", "product_key": "k2", "occurrence_index": 1,
             "product_raw": "Không giảm giá", "sale_date": date(2026, 9, 6),
             "line": owner_line(order_key="BH2", discount=Decimal(0),
                                total_sales=SELL,
                                auto_kpi_profit=SELL - PURCHASE)},
        ]
        rows = business_presentation.detail_rows(details)
        assert len(rows) == 3
        assert rows[1]["synthetic"] is True
        assert rows[1]["product_raw"] == business_presentation.DISCOUNT_ROW_LABEL
        assert rows[2]["synthetic"] is False, "dòng không chiết khấu vẫn một dòng"


# ==========================================================================
# B. Dòng chiết khấu KHÔNG được làm hỏng ngữ nghĩa PHB-03 — CASE 4 · 7
# ==========================================================================

class TestDiscountRowsNeverContaminatePHB03:
    @pytest.fixture
    def period(self, repository, service):
        persist(repository, [
            discounted_pair("BH-CK", month=9, day=5),
            pair("BH-THUONG", month=9, day=6, sell="8000000", discount="0",
                 kpi_purchase="5000000", kpi_profit="3000000"),
        ])
        return service.period(**SEPTEMBER)

    def test_case_4_the_line_count_counts_business_lines_not_table_rows(self, period):
        assert period.totals.lines == 2
        assert len(business_presentation.detail_rows(period.details)) == 3

    def test_case_4_the_order_count_does_not_grow(self, period):
        assert period.totals.orders == 2, "hai đơn, không phải ba"

    def test_case_4_purchase_price_coverage_is_untouched(self, period):
        coverage = period.totals.coverage
        assert (coverage.covered_lines, coverage.total_lines) == (2, 2)
        assert coverage.missing_price_lines == 0
        assert coverage.is_complete is True

    def test_case_4_the_qualifying_quantity_does_not_count_a_discount(self, period):
        """Dòng chiết khấu có "SL 1" trên màn hình — nhưng nó KHÔNG phải một SP.

        Nó cũng có "giá bán 0", nằm dưới ngưỡng 1.000.000 của
        `DEC-PHB02-03`, nên kể cả khi ai đó lỡ đưa nó vào phép cộng thì nó
        vẫn không đủ điều kiện. Khẳng định này canh con số thật.
        """
        assert period.totals.qualifying_quantity == Decimal(2)

    def test_case_4_a_discount_row_is_never_a_missing_price_row(self, period):
        rows = business_presentation.detail_rows(period.details)
        synthetic = [row for row in rows if row["synthetic"]]
        assert len(synthetic) == 1
        assert synthetic[0]["pending"] is False
        assert synthetic[0]["blockers"] == []
        assert synthetic[0]["purchase_price"] == "100.000", "là TIỀN chiết khấu"

    def test_case_4_the_pending_filter_never_selects_a_discount_row(
        self, repository, client
    ):
        """Bộ lọc chạy trên DÒNG HÀNG, trước khi phân rã hiển thị.

        Vì vậy một dòng chiết khấu không thể tự lọt vào "CHƯA CÓ GIÁ NHẬP":
        nó không tồn tại ở tầng mà bộ lọc đọc.
        """
        persist(repository, [
            discounted_pair("BH-CK", month=9, day=5),
            pair("BH-THIEU", month=9, day=6, product="Tivi Sony",
                 discount="400000", kpi_purchase=None, kpi_profit=None),
        ])
        html = body(client, "/kinh-doanh/gia-nhap?ky=2026-09&loc=thieu-gia")
        assert metric(html, "coverage") == "1 / 2 dòng"
        # Dòng còn thiếu giá VẪN kéo theo dòng chiết khấu của chính nó, nhưng
        # dòng chiết khấu đó không có ô nhập và không đếm vào coverage.
        assert html.count('data-metric="discount-readonly"') == 1
        assert 'name="gia_nhap"' in html
        assert html.count('name="gia_nhap"') == 1, "chỉ dòng cha có ô nhập"

    def test_a_discount_row_offers_no_write_path_at_all(self, repository, client):
        """Không form ⟹ không đường ghi. Đây là ranh giới CẤU TRÚC, không phải
        một lời dặn: dòng chiết khấu không render `line_keys` nào."""
        persist(repository, [discounted_pair("BH-CK", month=9, day=5)])
        html = body(client, "/kinh-doanh/gia-nhap?ky=2026-09")
        assert html.count('name="order_key" value="BH-CK"') == 2, \
            "đúng hai form của DÒNG CHA (giá nhập + nhân viên), không thêm form nào"
        assert 'data-metric="discount-readonly"' in html

    def test_case_7_the_discount_row_stays_under_the_same_employee(
        self, repository, service
    ):
        persist(repository, [
            discounted_pair("BH-VINH", month=9, day=5, employee="Vinh"),
            discounted_pair("BH-LY", month=9, day=6, employee="Ly",
                            group="STANDARD_SALES"),
        ])
        scoped = service.period(**SEPTEMBER).for_employee("Vinh")
        rows = business_presentation.detail_rows(scoped.details)
        assert len(rows) == 2
        assert {row["employee"] for row in rows} == {"Vinh"}
        assert rows[1]["synthetic"] is True

    def test_case_7_the_employee_page_shows_both_lines_of_the_transaction(
        self, repository, client
    ):
        persist(repository, [discounted_pair("BH-VINH", month=9, day=5,
                                             employee="Vinh")])
        html = body(client,
                    "/kinh-doanh/gia-nhap?ky=2026-09&nhan-vien=Vinh&loc=tat-ca")
        assert business_presentation.DISCOUNT_ROW_LABEL in html
        assert "-100.000" in html


# ==========================================================================
# CHỐNG TRỪ HAI LẦN — bất biến trung tâm của cả bản sửa
# ==========================================================================

class TestTheDisplayNeverSubtractsTheDiscountTwice:
    @pytest.fixture
    def period(self, repository, service):
        persist(repository, [
            discounted_pair("BH1", month=9, day=5, employee="Vinh"),
            discounted_pair("BH2", month=9, day=6, employee="Ly",
                            group="STANDARD_SALES", discount="250000",
                            kpi_profit=str((SELL - PURCHASE) - Decimal("250000"))),
            pair("BH3", month=9, day=7, employee="Vinh", sell="8000000",
                 discount="0", kpi_purchase="5000000", kpi_profit="3000000"),
        ])
        return service.period(**SEPTEMBER)

    @staticmethod
    def _displayed(details, key):
        """Cộng lại đúng những con số MÀN HÌNH đang hiện, đọc ngược từ text."""
        total = Decimal(0)
        for row in business_presentation.detail_rows(details):
            text = row[key]["text"]
            if text == "—":
                continue
            total += Decimal(text.replace(".", "").replace(",", "."))
        return total

    def test_displayed_total_sales_sum_to_the_canonical_total(self, period):
        assert self._displayed(period.details, "total_sales") == \
            period.totals.sales_revenue

    def test_displayed_kpi_profit_sums_to_the_canonical_total(self, period):
        assert self._displayed(period.details, "kpi_profit") == \
            period.totals.kpi_profit

    def test_displayed_converted_sales_sum_to_the_canonical_total(self, period):
        assert self._displayed(period.details, "converted_sales") == \
            period.totals.converted_sales

    def test_the_canonical_totals_are_the_accounting_numbers_not_gross_ones(
        self, period
    ):
        """Bằng chứng số học rằng chiết khấu bị trừ ĐÚNG MỘT LẦN.

        Ba dòng: hai có chiết khấu (100.000 và 250.000), một không.
        Doanh thu gộp `5.000.000 + 5.000.000 + 8.000.000 = 18.000.000`;
        trừ đúng một lần `350.000` ⟹ `17.650.000`. Trừ hai lần sẽ ra
        `17.300.000`, trừ không lần nào ra `18.000.000` — cả hai đều sai và
        cả hai đều bị khẳng định này bắt.
        """
        assert period.totals.sales_revenue == Decimal("17650000")
        assert period.totals.kpi_profit == Decimal("6650000")

    def test_the_aggregate_path_never_calls_the_display_decomposition(self):
        """Ranh giới CẤU TRÚC: phép cộng của kỳ không đi qua phần trình bày.

        Chừng nào `totals()` không gọi `display_contributions()`, không có
        đường nào để một dòng hiển thị lọt vào một chỉ tiêu của kỳ — bất kể
        tầng trình bày sau này đổi thế nào.
        """
        import inspect

        from app.web import business_queries, business_service as bs

        for module in (bm, business_queries, bs):
            source = inspect.getsource(module)
            if module is bm:
                source = inspect.getsource(bm.totals) + inspect.getsource(
                    bm.group_by_employee)
            assert "display_contributions" not in source, module.__name__


# ==========================================================================
# C. Hợp đồng liên-origin — CASE 11 · 12
# ==========================================================================

class TestCrossOriginContract:
    def test_case_11_total_sales_may_now_be_compared(self):
        for legacy_key in ("sales", "sales_vnd"):
            result = legacy_reference.compare(
                Decimal("1000000"), Decimal("1200000"),
                legacy_key=legacy_key, current_key="sales_revenue")
            assert result.allowed is True, legacy_key
            assert result.percent == Decimal("20"), legacy_key

    @pytest.mark.parametrize("legacy_key,current_key", [
        ("profit", "kpi_profit"),
        ("converted_revenue", "converted_sales"),
        ("orders", "orders"),
        ("products", "qualifying_quantity"),
    ])
    def test_case_12_every_unproven_pair_stays_blocked(self, legacy_key, current_key):
        """`DEC-180` chứng minh MỘT chỉ tiêu, không mở một chiều dọc mới."""
        result = legacy_reference.compare(
            Decimal("1000"), Decimal("1500"),
            legacy_key=legacy_key, current_key=current_key)
        assert result.allowed is False
        assert result.percent is None

    def test_a_pair_the_contract_never_heard_of_is_still_refused(self):
        result = legacy_reference.compare(
            Decimal("1000"), Decimal("1500"),
            legacy_key="bonus", current_key="sales_revenue")
        assert result.allowed is False
        assert "chưa xét cặp chỉ tiêu này" in result.note


# ==========================================================================
# AN TOÀN ĐƠN VỊ — `DEC-180` §10
# ==========================================================================

class TestUnitSafety:
    def test_a_summary_amount_is_thousands_of_dong(self):
        assert legacy_reference.to_vnd(Decimal("1000"), "kvnd") == Decimal("1000000")

    def test_a_datachart_amount_is_already_dong(self):
        assert legacy_reference.to_vnd(Decimal("1000"), "vnd") == Decimal("1000")

    def test_an_empty_cell_stays_empty_and_never_becomes_zero(self):
        assert legacy_reference.to_vnd(None, "kvnd") is None

    def test_an_unknown_unit_stops_instead_of_guessing_a_factor(self):
        """Hệ số mặc định `1` chính là cách quên nhân 1.000 sống sót."""
        with pytest.raises(legacy_reference.UnknownUnitError):
            legacy_reference.to_vnd(Decimal("1000"), "usd")

    def test_the_resolver_normalises_a_summary_month_total_to_dong(self):
        """Khẳng định này FAIL nếu ai đó bỏ phép nhân 1.000.

        `1.000 kVND` là `1.000.000 VND`. Bỏ chuẩn hoá thì giá trị trả về là
        `1.000`, và một MoM so `4.900.000 VND` với `1.000` ra `+489.900 %` —
        một con số trông như một con số.
        """
        resolved = legacy_reference.authoritative_period_sales(
            year=2026, month=8,
            summary_rows=[{"year": 2026, "month": 8, "row_kind": "MONTH_TOTAL",
                           "unit": "kVND", "sales": Decimal("1000")}])
        assert resolved is not None
        assert resolved.raw_value == Decimal("1000")
        assert resolved.unit_kind == "kvnd"
        assert resolved.sales_vnd == Decimal("1000000")


# ==========================================================================
# D. Nguồn chuẩn của một kỳ lịch sử
# ==========================================================================

class TestAuthoritativePeriodResolution:
    def test_the_summary_month_total_row_wins_over_the_datachart_cell(self):
        """MỘT kỳ ⟹ MỘT nguồn. Không cộng, không trung bình, không lấy cả hai."""
        resolved = legacy_reference.authoritative_period_sales(
            year=2026, month=8,
            summary_rows=[{"year": 2026, "month": 8, "row_kind": "MONTH_TOTAL",
                           "unit": "kVND", "sales": Decimal("1000")}],
            monthly_rows=[{"year": 2026, "month": 8,
                           "sales_current_year_vnd": Decimal("7777777")}])
        assert resolved.source == legacy_reference.PERIOD_SOURCE_SUMMARY_MONTH_TOTAL
        assert resolved.sales_vnd == Decimal("1000000")

    def test_the_datachart_cell_is_used_when_no_summary_month_total_exists(self):
        resolved = legacy_reference.authoritative_period_sales(
            year=2026, month=8, summary_rows=[],
            monthly_rows=[{"year": 2026, "month": 8,
                           "sales_current_year_vnd": Decimal("7777777")}])
        assert resolved.source == legacy_reference.PERIOD_SOURCE_DATACHART_MONTH
        assert resolved.sales_vnd == Decimal("7777777")

    def test_a_seller_row_is_never_mistaken_for_the_month_total(self):
        assert legacy_reference.authoritative_period_sales(
            year=2026, month=8,
            summary_rows=[{"year": 2026, "month": 8, "row_kind": "SELLER",
                           "unit": "kVND", "sales": Decimal("600")}]) is None

    def test_seller_rows_are_never_summed_into_a_month_total(self):
        """Tự cộng lại các dòng người bán là CÔNG CỤ TÍNH LẠI SỐ CŨ.

        `TASK-PRA-001` §20 cấm điều đó, kể cả để "sửa" lỗi `A2` đã biết của
        dòng tổng tháng. Lỗi được NÓI RA, không được vá lén.
        """
        resolved = legacy_reference.authoritative_period_sales(
            year=2026, month=8,
            summary_rows=[
                {"year": 2026, "month": 8, "row_kind": "SELLER",
                 "unit": "kVND", "sales": Decimal("600")},
                {"year": 2026, "month": 8, "row_kind": "SELLER",
                 "unit": "kVND", "sales": Decimal("500")},
                {"year": 2026, "month": 8, "row_kind": "MONTH_TOTAL",
                 "unit": "kVND", "sales": Decimal("1000")},
            ])
        assert resolved.sales_vnd == Decimal("1000000"), "KHÔNG phải 1.100.000"

    def test_a_known_defect_on_the_month_total_travels_with_the_number(self):
        resolved = legacy_reference.authoritative_period_sales(
            year=2026, month=8,
            summary_rows=[{"year": 2026, "month": 8, "row_kind": "MONTH_TOTAL",
                           "unit": "kVND", "sales": Decimal("1000"),
                           "known_defects": {"E": ["A2"]}}])
        assert resolved.defects == ("A2",)

    def test_an_empty_source_cell_is_not_evidence(self):
        assert legacy_reference.authoritative_period_sales(
            year=2026, month=8,
            summary_rows=[{"year": 2026, "month": 8, "row_kind": "MONTH_TOTAL",
                           "unit": "kVND", "sales": None}],
            monthly_rows=[{"year": 2026, "month": 8,
                           "sales_current_year_vnd": None}]) is None

    def test_another_month_is_never_borrowed(self):
        assert legacy_reference.authoritative_period_sales(
            year=2026, month=8,
            summary_rows=[{"year": 2026, "month": 7, "row_kind": "MONTH_TOTAL",
                           "unit": "kVND", "sales": Decimal("1000")}]) is None


# ==========================================================================
# E. MoM bắc qua ranh giới bàn giao — CASE 8 · 9 · 10
# ==========================================================================

def load_august_legacy(legacy, *, sales_kvnd="1000"):
    """Tháng 08/2026 có Tổng bán trong sổ cũ, ĐƠN VỊ kVND."""
    legacy.create_import(LegacyWorkbook(
        source_file_name="Báo cáo Kinh doanh 2026.xlsx",
        file_fingerprint="fp-legacy-2026", file_size=1,
        sheets_imported=[{"sheet_name": "Summary 2026", "scope": "SUMMARY"}],
        summary_rows=[SummaryRow(
            year=2026, month=8, seller_label="Tổng T08", row_kind="MONTH_TOTAL",
            sheet_name="Summary 2026", sheet_row=20,
            values={"sales": Decimal(sales_kvnd)})],
        daily_sales=[], monthly_reference=[],
    ))


class TestCrossBoundaryMonthOverMonth:
    def test_case_8_september_current_compares_against_august_legacy(
        self, legacy, repository, client
    ):
        """`CASE 8` — đúng ca bàn giao chủ dự án mô tả.

        Tháng 08/2026 = số cũ có thẩm quyền (`1.000 kVND = 1.000.000 VND`).
        Tháng 09/2026 = số mới (`4.900.000 VND` sau chiết khấu).
        `(4.900.000 − 1.000.000) / 1.000.000 = +390 %`.
        """
        load_august_legacy(legacy)
        persist(repository, [discounted_pair("BH-CK", month=9, day=5)])
        html = body(client, "/kinh-doanh?ky=2026-09")
        assert metric(html, "sales_revenue") == "4.900.000"
        assert metric(html, "mom") == "+390%"

    def test_case_8_the_borrowed_month_says_where_its_number_came_from(
        self, legacy, repository, client
    ):
        """`DEC-180` §8 — origin phải HIỆN RA, không được ẩn đi."""
        load_august_legacy(legacy)
        persist(repository, [discounted_pair("BH-CK", month=9, day=5)])
        html = body(client, "/kinh-doanh?ky=2026-09")
        assert metric(html, "mom-origin") == "SỐ CŨ"
        assert "Summary" in metric(html, "mom-source")
        assert metric(html, "mom-note") == \
            business_presentation.MOM_LEGACY_PREVIOUS_NOTE

    def test_case_8_forgetting_the_thousand_factor_would_change_the_answer(
        self, legacy, repository, client
    ):
        """Khẳng định canh CHÍNH lỗi im lặng của mục 10.

        `1.000 kVND` chưa chuẩn hoá là `1.000`, và MoM khi đó ra `+489.900 %`.
        Con số đó phải KHÔNG BAO GIỜ xuất hiện.
        """
        load_august_legacy(legacy)
        persist(repository, [discounted_pair("BH-CK", month=9, day=5)])
        html = body(client, "/kinh-doanh?ky=2026-09")
        assert metric(html, "mom") != "+489.900%"
        assert metric(html, "mom") == "+390%"

    def test_case_9_a_previous_current_month_is_never_replaced_by_the_old_book(
        self, legacy, repository, client
    ):
        """`CASE 9` — tháng trước ĐÃ có số mới ⟹ hành vi cũ y nguyên."""
        load_august_legacy(legacy, sales_kvnd="999999")
        persist(repository, [
            pair("BH-T8", month=8, day=5, sell="10000000", discount="0",
                 kpi_purchase="1000000", kpi_profit="9000000"),
        ])
        persist(repository, [
            pair("BH-T9", month=9, day=5, sell="15000000", discount="0",
                 kpi_purchase="1000000", kpi_profit="14000000"),
        ], run_id="run-2", at="2026-10-01T00:00:00", fingerprint="fp-b")
        html = body(client, "/kinh-doanh?ky=2026-09")
        assert metric(html, "mom") == "+50%", "so với 10.000.000 của SỐ MỚI"
        # Không nhãn origin, không câu chú thích: đây là so cùng-engine, y
        # như trước bản sửa. `999.999 kVND` của sổ cũ không được đụng tới.
        assert 'data-metric="mom-origin"' not in html
        assert 'data-metric="mom-note"' not in html

    def test_case_10_absent_in_both_sources_keeps_the_old_wording(
        self, repository, client
    ):
        """`CASE 10` — không nguồn nào có tháng trước ⟹ câu chữ cũ y nguyên."""
        persist(repository, [discounted_pair("BH-CK", month=9, day=5)])
        html = body(client, "/kinh-doanh?ky=2026-09")
        assert metric(html, "mom") == "—"
        assert metric(html, "mom-note") == business_presentation.MOM_NO_PREVIOUS

    def test_the_two_periods_are_never_summed_into_one_number(
        self, legacy, repository, client
    ):
        """`DEC-166 E` vẫn nguyên: doanh thu của kỳ là của MỘT origin."""
        load_august_legacy(legacy)
        persist(repository, [discounted_pair("BH-CK", month=9, day=5)])
        html = body(client, "/kinh-doanh?ky=2026-09")
        assert metric(html, "sales_revenue") == "4.900.000"
        assert "5.900.000" not in html, "không có phép cộng hai origin"

    def test_the_datachart_source_also_bridges_the_boundary(
        self, legacy, repository, client
    ):
        """Workbook chỉ có DataChart vẫn cấp được mốc so — đã là VND sẵn."""
        legacy.create_import(LegacyWorkbook(
            source_file_name="Báo cáo Kinh doanh 2026.xlsx",
            file_fingerprint="fp-dc", file_size=1,
            sheets_imported=[{"sheet_name": "DataChart", "scope": "MONTHLY_REFERENCE"}],
            summary_rows=[], daily_sales=[],
            monthly_reference=[MonthlyReference(
                year=2026, month=8, sales_current_year_vnd=Decimal("1000000"))],
        ))
        persist(repository, [discounted_pair("BH-CK", month=9, day=5)])
        html = body(client, "/kinh-doanh?ky=2026-09")
        assert metric(html, "mom") == "+390%"
        assert "DataChart" in metric(html, "mom-source")

    def test_viewing_all_data_still_refuses_to_compare(self, legacy, repository, client):
        load_august_legacy(legacy)
        persist(repository, [discounted_pair("BH-CK", month=9, day=5)])
        html = body(client, "/kinh-doanh?ky=tat-ca")
        assert metric(html, "mom") == "—"
        assert metric(html, "mom-note") == business_presentation.MOM_ALL_DATA

    def test_the_employee_page_never_compares_one_person_to_a_company_total(
        self, legacy, repository, client
    ):
        """Số cũ của một tháng là tổng của CẢ CÔNG TY.

        Đem nó làm mẫu số cho doanh thu của MỘT người là một phép so sai, và
        ghép tên người bán trong sổ cũ với nhân viên hiện hành là một bài toán
        ánh xạ chưa có quyết định nào cho phép. Trang nhân viên vì vậy giữ
        nguyên câu "chưa có dữ liệu tháng trước".
        """
        load_august_legacy(legacy)
        persist(repository, [discounted_pair("BH-CK", month=9, day=5,
                                             employee="Vinh")])
        html = body(client, "/kinh-doanh/nhan-vien?ky=2026-09&nhan-vien=Vinh")
        assert metric(html, "mom") == "—"
        assert metric(html, "mom-note") == business_presentation.MOM_NO_PREVIOUS


class TestTheFallbackIsOptOutNotOptIn:
    def test_the_presentation_layer_keeps_its_old_behaviour_without_a_fallback(self):
        """`summary()` gọi không kèm nguồn dự phòng ⟹ y hệt trước bản sửa."""
        totals = bm.totals([owner_line()])
        empty = bm.totals([])
        view = business_presentation.summary(
            totals, period=(2026, 9), previous_totals=empty, undated=0)
        assert view["mom"]["percent"] == "—"
        assert view["mom"]["note"] == business_presentation.MOM_NO_PREVIOUS
        assert view["mom"]["origin"] == ""

    def test_a_malformed_defect_record_never_takes_down_the_page(self):
        """Mất một chú thích ≠ mất con số. Bản ghi lỗi hình dạng ⟹ tuple rỗng."""
        for defects in ('{"E": ["A2"]}', ["A2"], {"E": "A2"}, None):
            resolved = legacy_reference.authoritative_period_sales(
                year=2026, month=8,
                summary_rows=[{"year": 2026, "month": 8,
                               "row_kind": "MONTH_TOTAL", "unit": "kVND",
                               "sales": Decimal("1000"),
                               "known_defects": defects}])
            assert resolved.sales_vnd == Decimal("1000000")
            assert resolved.defects == ()

    def test_a_row_without_a_unit_column_is_read_as_thousands_of_dong(self):
        """`unit` rỗng = bản nhập cũ trước khi cột đó có mặc định.

        `Summary` LUÔN là kVND (`app/legacy/models.UNIT_SUMMARY`), nên mặc
        định phải là kVND — mặc định VND ở đây là chia nhầm 1.000 lần.
        """
        resolved = legacy_reference.authoritative_period_sales(
            year=2026, month=8,
            summary_rows=[{"year": 2026, "month": 8, "row_kind": "MONTH_TOTAL",
                           "unit": None, "sales": Decimal("1000")}])
        assert resolved.unit_kind == legacy_reference.SUMMARY_ROW_UNIT == "kvnd"
        assert resolved.sales_vnd == Decimal("1000000")
