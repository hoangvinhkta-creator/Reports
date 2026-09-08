"""R4 — báo cáo đánh giá, kiểm qua ỨNG DỤNG WEB THẬT.

`tests/test_r4_evaluation_metrics.py` kiểm ngữ nghĩa trên giá trị thuần. File
này hỏi câu Owner thật sự hỏi:

    tôi mở trang đánh giá → con số trên đó có mở ra đúng tập dòng sinh ra nó
    không, và trang có chịu im lặng công bố một kết quả một phần không?

Ba luồng nghiệm thu của brief §"Nghiệm thu Owner rút gọn" đều có mặt ở đây:
(A) một KPI/insight → drill-down đúng và tổng KHỚP; (B) tháng đang chạy +
target + so cùng ngày kỳ trước; (C) kỳ thiếu giá → KHÔNG công bố lợi nhuận
một phần. Toàn bộ dữ liệu là tổng hợp.
"""

from __future__ import annotations

import re
from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine

import tools.db as history_db
from app.web import business_service, business_store, history_store
from app.web import server as web_server
from tests.test_employee_workspace_ux import TODAY, line, persist
from tools.tracking import live_pull

#: `TODAY` = 03/09/2026 (dùng chung với bộ test không gian làm việc), nên
#: tháng 09/2026 là THÁNG ĐANG CHẠY và tháng 08/2026 là kỳ liền trước.
SEPTEMBER_QS = "ky=2026-09"
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
def client(engine, monkeypatch, tmp_path):
    monkeypatch.setattr(web_server, "select_latest_valid_captures", lambda: None)
    monkeypatch.setattr(live_pull, "is_configured", lambda env=None: False)
    monkeypatch.setattr(web_server, "_today", lambda: TODAY)
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


def body(client, path: str) -> str:
    response = client.get(path)
    assert response.status_code == 200, (path, response.status_code)
    return response.data.decode("utf-8")


def metric(html: str, name: str) -> str:
    """Giá trị của MỘT `data-metric` — cùng cách đọc các bộ test UI khác dùng."""
    found = re.search(
        r'data-metric="%s"[^>]*>\s*([^<]*)' % re.escape(name), html)
    assert found is not None, f"không thấy data-metric={name!r}"
    return found.group(1).strip()


def attr(html: str, name: str, attribute: str) -> str:
    found = re.search(
        r'data-metric="%s"([^>]*)>' % re.escape(name), html)
    assert found is not None, f"không thấy data-metric={name!r}"
    inner = re.search(r'%s="([^"]*)"' % re.escape(attribute), found.group(1))
    return "" if inner is None else inner.group(1)


def links(html: str) -> list[str]:
    return re.findall(r'href="([^"]*)"', html)


def detail_row_count(html: str) -> int:
    """Số DÒNG HÀNG THẬT của bảng kê chi tiết (`kinh_doanh_gia_nhap.html`).

    Mỗi hàng bảng có đúng một ô `purchase_price`; một dòng có chiết khấu sinh
    ra HAI hàng (`S121`), và hàng thứ hai mang `data-row-kind`. Trừ nó ra để
    phép đếm này nói về dòng hàng của sổ, không về hàng của HTML.
    """
    rows = len(re.findall(r'data-metric="purchase_price"', html))
    synthetic = len(re.findall(r'data-row-kind="', html))
    return rows - synthetic


# --- dữ liệu tổng hợp -----------------------------------------------------

def priced_period():
    """Tháng 09 đủ giá + tháng 08 để so, mọi dòng của nhóm Nội thành."""
    return [
        line("BH2001", "TV43", day=3, sell="8000000",
             kpi_purchase="5000000", kpi_profit="3000000"),
        line("BH2002", "TL200", day=5, sell="12000000",
             kpi_purchase="9000000", kpi_profit="3000000"),
        line("BH1901", "TV43", month=8, day=3, sell="6000000",
             kpi_purchase="4000000", kpi_profit="2000000"),
        line("BH1902", "TV43", month=8, day=25, sell="20000000",
             kpi_purchase="10000000", kpi_profit="10000000"),
    ]


def partly_priced_period():
    """Một dòng CHƯA có giá nhập — kỳ mất trạng thái CHÍNH THỨC."""
    return [
        line("BH2001", "TV43", day=3, sell="8000000",
             kpi_purchase="5000000", kpi_profit="3000000"),
        line("BH2003", "MG50", day=3, sell="3000000",
             kpi_purchase=None, kpi_profit=None, status="PENDING",
             reasons=("Missing.PurchasePrice",)),
    ]


# ==========================================================================
# LUỒNG A — một KPI/insight mở ra đúng tập dòng, và TỔNG KHỚP
# ==========================================================================

class TestDrillDownMatchesTheHeadline:
    def test_the_page_opens_on_the_selected_period(self, repository, client):
        persist(repository, priced_period())
        html = body(client, f"/kinh-doanh/danh-gia?{SEPTEMBER_QS}")
        assert "Tháng 09/2026" in html
        assert metric(html, "as-of") == "Số tính đến 03/09/2026"

    def test_revenue_drills_into_the_detail_table_of_the_same_period(
        self, repository, service, client
    ):
        """Bấm vào Doanh thu → bảng kê của ĐÚNG kỳ đó, đủ số dòng."""
        persist(repository, priced_period())
        html = body(client, f"/kinh-doanh/danh-gia?{SEPTEMBER_QS}")
        target = next(url for url in links(html)
                      if "/kinh-doanh/gia-nhap" in url and "loc=tat-ca" in url)
        assert "ky=2026-09" in target
        detail = body(client, target.replace("&amp;", "&"))
        assert detail_row_count(detail) == len(
            service.period(**SEPTEMBER).details) == 2

    def test_a_product_row_drills_into_exactly_that_product(
        self, repository, client
    ):
        persist(repository, priced_period())
        html = body(client, f"/kinh-doanh/danh-gia?{SEPTEMBER_QS}")
        target = next(url for url in links(html) if "mat-hang=" in url)
        detail = body(client, target.replace("&amp;", "&"))
        # Đúng MỘT mặt hàng, và bảng nói ra phạm vi nó đang thu hẹp về.
        assert detail_row_count(detail) == 1

    def test_every_product_drill_down_adds_back_to_the_headline(
        self, repository, service, client
    ):
        """Bất biến §5, chứng minh qua ROUTE THẬT: tổng detail == headline.

        Đi qua từng đường dẫn drill-down của bảng mặt hàng, đếm dòng trên
        chính bảng kê mà nó mở ra, rồi so tổng với số dòng của headline. Đây
        là phép đối soát mà brief đòi: dashboard và chi tiết không được nói
        hai câu khác nhau về cùng một kỳ.
        """
        persist(repository, priced_period())
        html = body(client, f"/kinh-doanh/danh-gia?{SEPTEMBER_QS}")
        product_urls = {url.replace("&amp;", "&") for url in links(html)
                        if "mat-hang=" in url}
        assert product_urls, "bảng mặt hàng phải có đường dẫn drill-down"
        drilled = sum(detail_row_count(body(client, url))
                      for url in product_urls)
        totals = service.period(**SEPTEMBER).totals
        assert drilled == totals.lines == 2

    def test_the_product_table_total_row_equals_the_headline_revenue(
        self, repository, service, client
    ):
        persist(repository, priced_period())
        html = body(client, f"/kinh-doanh/danh-gia?{SEPTEMBER_QS}")
        totals = service.period(**SEPTEMBER).totals
        headline = metric(html, "eval-sales_revenue")
        table_totals = re.findall(
            r'<tr class="row-total">.*?data-metric="revenue"[^>]*>\s*([^<]*)',
            html, flags=re.S)
        assert table_totals, "mỗi bảng đóng góp phải có một hàng TỔNG"
        assert set(table_totals) == {headline}
        assert totals.sales_revenue == Decimal("20000000")

    def test_the_loss_queue_opens_only_lines_that_actually_lose_money(
        self, repository, client
    ):
        persist(repository, [
            line("BH2001", "TV43", day=3, sell="8000000",
                 kpi_purchase="5000000", kpi_profit="3000000"),
            line("BH2004", "LO1", day=3, sell="1000000",
                 kpi_purchase="1500000", kpi_profit="-500000"),
        ])
        html = body(client, f"/kinh-doanh/danh-gia?{SEPTEMBER_QS}")
        assert metric(html, "loss-lines") == "1"
        detail = body(client, f"/kinh-doanh/gia-nhap?{SEPTEMBER_QS}&loc=lo")
        assert detail_row_count(detail) == 1

    def test_the_discount_queue_excludes_lines_without_a_discount(
        self, repository, client
    ):
        persist(repository, [
            line("BH2001", "TV43", day=3, sell="8000000",
                 kpi_purchase="5000000", kpi_profit="3000000"),
            line("BH2002", "TL200", day=5, sell="12000000", discount="500000",
                 kpi_purchase="9000000", kpi_profit="2500000"),
        ])
        html = body(client, f"/kinh-doanh/danh-gia?{SEPTEMBER_QS}")
        assert metric(html, "discount-lines") == "1"
        detail = body(client,
                      f"/kinh-doanh/gia-nhap?{SEPTEMBER_QS}&loc=co-chiet-khau")
        assert detail_row_count(detail) == 1

    def test_a_narrowing_key_that_matches_nothing_gives_an_empty_table(
        self, repository, client
    ):
        """Không im lặng mở rộng phạm vi — đó là cách đọc một tổng khác."""
        persist(repository, priced_period())
        detail = body(
            client,
            f"/kinh-doanh/gia-nhap?{SEPTEMBER_QS}&mat-hang=khong-ton-tai")
        assert detail_row_count(detail) == 0

    def test_the_sheet_table_reconciles_to_the_period_total(
        self, repository, service, client
    ):
        """Hàng TỔNG của bảng đơn vị báo cáo == tổng KỲ, không cộng dọc.

        Và hai ô target của hàng TỔNG để TRỐNG: không có target cấp công ty,
        nên cộng target các đơn vị lên là bịa một con số chưa ai đặt.
        """
        persist(repository, priced_period())
        html = body(client, f"/kinh-doanh/danh-gia?{SEPTEMBER_QS}")
        table = re.search(
            r'data-metric="eval-sheets".*?</table>', html, flags=re.S).group(0)
        total_row = re.search(r'<tr class="row-total">.*?</tr>', table,
                              flags=re.S).group(0)
        totals = service.period(**SEPTEMBER).totals
        assert metric(total_row, "revenue") == \
            metric(html, "eval-sales_revenue")
        assert metric(total_row, "orders") == str(totals.orders)
        assert metric(total_row, "row-target") == "—"
        assert metric(total_row, "row-target-percent") == "—"

    def test_the_sheet_table_says_it_always_covers_the_whole_period(
        self, repository, client
    ):
        persist(repository, priced_period())
        html = body(client, f"/kinh-doanh/danh-gia?{SEPTEMBER_QS}&nhom=noi-thanh")
        assert "LUÔN nói về CẢ KỲ" in metric(html, "eval-sheets-note")

    def test_the_report_page_links_to_the_evaluation_page(
        self, repository, client
    ):
        persist(repository, priced_period())
        html = body(client, f"/kinh-doanh?{SEPTEMBER_QS}")
        assert "/kinh-doanh/danh-gia" in html
        assert "ky=2026-09" in attr(html, "eval-entry", "href")


# ==========================================================================
# LUỒNG B — tháng đang chạy, target, so CÙNG NGÀY kỳ trước
# ==========================================================================

class TestRunningMonthTargetAndComparison:
    def test_the_running_month_shows_its_progress_and_as_of_date(
        self, repository, client
    ):
        persist(repository, priced_period())
        html = body(client, f"/kinh-doanh/danh-gia?{SEPTEMBER_QS}")
        assert metric(html, "elapsed-days") == "3"
        assert metric(html, "month-days") == "30"
        assert metric(html, "as-of") == "Số tính đến 03/09/2026"

    def test_the_previous_month_is_compared_on_the_same_calendar_days(
        self, repository, client
    ):
        """01–03/09 so 01–03/08 — dòng 25/08 KHÔNG được lọt vào mẫu số."""
        persist(repository, priced_period())
        html = body(client, f"/kinh-doanh/danh-gia?{SEPTEMBER_QS}")
        assert metric(html, "compare-window") == "ngày 01–03 của cả hai tháng"
        assert metric(html, "compare-current") == "8.000"    # chỉ ngày 3
        assert metric(html, "compare-previous") == "6.000"   # chỉ ngày 3
        assert metric(html, "compare-percent") == "+33,33%"

    def test_an_empty_previous_month_says_why_instead_of_printing_a_percent(
        self, repository, client
    ):
        persist(repository, [line("BH2001", "TV43", day=3, sell="8000000",
                                  kpi_purchase="5000000", kpi_profit="3000000")])
        html = body(client, f"/kinh-doanh/danh-gia?{SEPTEMBER_QS}")
        assert metric(html, "compare-percent") == "—"
        assert attr(html, "compare-reason", "data-reason") == \
            "COMPARE_PREVIOUS_NO_LINES"

    def test_a_scope_with_a_target_shows_percent_shortfall_and_per_day(
        self, repository, store, client
    ):
        persist(repository, priced_period())
        store.set_group_target(year=2026, month=9, group_key="NOI_THANH",
                               target_vnd=Decimal("600000000"))
        html = body(client,
                    f"/kinh-doanh/danh-gia?{SEPTEMBER_QS}&nhom=noi-thanh")
        # DS quy đổi = 6.000.000 / 0,02 = 300.000.000 ⟹ 50 % của 600 triệu.
        assert metric(html, "target-value") == "600.000"
        assert metric(html, "target-percent") == "50%"
        assert metric(html, "target-shortfall") == "300.000"
        assert metric(html, "target-days-remaining") == "còn 27 ngày"
        # 300.000.000 còn thiếu / 27 ngày = 11.111.111 VND/ngày.
        assert metric(html, "target-required-per-day") == "11.111"

    def test_a_scope_without_a_target_says_so_and_invents_nothing(
        self, repository, client
    ):
        persist(repository, priced_period())
        html = body(client,
                    f"/kinh-doanh/danh-gia?{SEPTEMBER_QS}&nhom=noi-thanh")
        assert metric(html, "target-percent") == "—"
        assert attr(html, "target-reason", "data-reason") == "TARGET_UNSET"

    def test_a_zero_target_is_not_the_same_as_an_unset_one(
        self, repository, store, client
    ):
        persist(repository, priced_period())
        store.set_group_target(year=2026, month=9, group_key="NOI_THANH",
                               target_vnd=Decimal("0"))
        html = body(client,
                    f"/kinh-doanh/danh-gia?{SEPTEMBER_QS}&nhom=noi-thanh")
        assert attr(html, "target-reason", "data-reason") == "TARGET_ZERO"

    def test_the_company_scope_never_sums_employee_targets(
        self, repository, store, client
    ):
        """Không có target cấp công ty, và trang nói ra điều đó."""
        persist(repository, priced_period())
        store.set_group_target(year=2026, month=9, group_key="NOI_THANH",
                               target_vnd=Decimal("600000000"))
        html = body(client, f"/kinh-doanh/danh-gia?{SEPTEMBER_QS}")
        assert "target-company-note" in html
        assert 'data-metric="target-value"' not in html

    def test_the_run_rate_is_labelled_an_estimate_and_scales_by_elapsed_days(
        self, repository, client
    ):
        persist(repository, priced_period())
        html = body(client, f"/kinh-doanh/danh-gia?{SEPTEMBER_QS}")
        # 20.000.000 doanh thu / 3 ngày × 30 ngày = 200.000.000.
        assert metric(html, "revenue-run-rate-value") == "200.000"
        assert "Ước tính nếu tốc độ hiện tại giữ nguyên" in html
        assert "KHÔNG phải dự báo" in html

    def test_a_finished_month_is_not_forecast_at_all(self, repository, client):
        persist(repository, priced_period())
        html = body(client, "/kinh-doanh/danh-gia?ky=2026-08")
        assert metric(html, "revenue-run-rate-value") == "—"
        assert attr(html, "revenue-run-rate", "data-reason") == \
            "RUNRATE_NOT_RUNNING"
        assert metric(html, "compare-window") == "trọn tháng"


# ==========================================================================
# LUỒNG C — coverage thiếu giá KHÔNG công bố lợi nhuận một phần
# ==========================================================================

class TestIncompleteCoverageNeverPublishesAPartialResult:
    def test_profit_margin_and_converted_sales_all_stay_blank(
        self, repository, client
    ):
        persist(repository, partly_priced_period())
        html = body(client, f"/kinh-doanh/danh-gia?{SEPTEMBER_QS}")
        for name in ("eval-kpi_profit", "eval-margin_percent",
                     "eval-profit_per_order", "eval-converted_sales"):
            assert metric(html, name) == "—", name
        assert metric(html, "quality-verdict") == "CHƯA ĐỦ"
        assert attr(html, "quality-verdict", "data-sufficient") == "no"

    def test_each_blank_metric_carries_the_reason_that_explains_it(
        self, repository, client
    ):
        persist(repository, partly_priced_period())
        html = body(client, f"/kinh-doanh/danh-gia?{SEPTEMBER_QS}")
        assert attr(html, "eval-kpi_profit-reason", "data-reason") == \
            "PROFIT_NOT_OFFICIAL"
        assert attr(html, "eval-converted_sales-reason", "data-reason") == \
            "CONVERTED_NOT_OFFICIAL"

    def test_the_partial_number_is_shown_as_evidence_not_as_the_result(
        self, repository, client
    ):
        persist(repository, partly_priced_period())
        html = body(client, f"/kinh-doanh/danh-gia?{SEPTEMBER_QS}")
        assert metric(html, "eval-kpi_profit") == "—"
        assert "3.000" in metric(html, "eval-kpi_profit-partial")
        assert "KHÔNG phải kết quả cả kỳ" in html

    def test_revenue_and_orders_still_have_numbers(self, repository, client):
        """Doanh thu không phụ thuộc giá nhập — nó không bị cổng chặn theo."""
        persist(repository, partly_priced_period())
        html = body(client, f"/kinh-doanh/danh-gia?{SEPTEMBER_QS}")
        assert metric(html, "eval-sales_revenue") == "11.000"
        assert metric(html, "eval-orders") == "2"

    def test_a_gated_metric_drills_into_the_lines_still_missing_a_price(
        self, repository, client
    ):
        persist(repository, partly_priced_period())
        html = body(client, f"/kinh-doanh/danh-gia?{SEPTEMBER_QS}")
        assert any("loc=thieu-gia" in url for url in links(html))
        detail = body(client, f"/kinh-doanh/gia-nhap?{SEPTEMBER_QS}&loc=thieu-gia")
        assert detail_row_count(detail) == 1

    def test_the_loss_table_labels_the_scope_it_actually_examined(
        self, repository, client
    ):
        persist(repository, partly_priced_period())
        html = body(client, f"/kinh-doanh/danh-gia?{SEPTEMBER_QS}")
        assert metric(html, "loss-scope") == "đã xét 1 / 2 dòng"
        assert "KHÔNG\n    phải toàn bộ đơn lỗ của kỳ" in html or \
            "phải toàn bộ đơn lỗ của kỳ" in html

    def test_a_target_cannot_be_scored_against_a_partial_converted_sales(
        self, repository, store, client
    ):
        persist(repository, partly_priced_period())
        store.set_group_target(year=2026, month=9, group_key="NOI_THANH",
                               target_vnd=Decimal("600000000"))
        html = body(client,
                    f"/kinh-doanh/danh-gia?{SEPTEMBER_QS}&nhom=noi-thanh")
        assert metric(html, "target-percent") == "—"
        assert attr(html, "target-reason", "data-reason") == \
            "TARGET_ACTUAL_NOT_OFFICIAL"


# ==========================================================================
# Khối chất lượng dữ liệu + trạng thái kỳ
# ==========================================================================

class TestDataQualityBlock:
    def test_the_provenance_table_accounts_for_every_line(
        self, repository, client
    ):
        persist(repository, partly_priced_period())
        html = body(client, f"/kinh-doanh/danh-gia?{SEPTEMBER_QS}")
        counts = [int(value) for value in re.findall(
            r'data-metric="provenance-lines">\s*(\d+)', html)]
        assert sum(counts) == 2

    def test_the_min_final_provisional_gap_is_stated_not_guessed(
        self, repository, client
    ):
        """R4 chỉ đọc dữ liệu hiệu lực — trạng thái MIN không nằm ở đó.

        Trang phải NÓI RA giới hạn ấy và đưa thứ thật sự đo được (thẩm quyền
        giá mà pipeline đã dùng) thay vì im lặng, hoặc tệ hơn là đoán một
        trạng thái FINAL/PROVISIONAL không có bằng chứng.
        """
        persist(repository, priced_period())
        html = body(client, f"/kinh-doanh/danh-gia?{SEPTEMBER_QS}")
        assert "FINAL/PROVISIONAL" in metric(html, "min-status-note")
        assert "ngoài phạm vi R4" in metric(html, "min-status-note")

    def test_the_price_source_table_accounts_for_every_line(
        self, repository, service, client
    ):
        persist(repository, partly_priced_period())
        html = body(client, f"/kinh-doanh/danh-gia?{SEPTEMBER_QS}")
        counts = [int(value) for value in re.findall(
            r'data-metric="price-source-lines">\s*(\d+)', html)]
        assert sum(counts) == service.period(**SEPTEMBER).totals.lines == 2

    def test_the_queues_and_the_latest_sale_date_are_shown(
        self, repository, client
    ):
        persist(repository, partly_priced_period())
        html = body(client, f"/kinh-doanh/danh-gia?{SEPTEMBER_QS}")
        assert metric(html, "quality-latest-sale") == "03/09/2026"
        assert metric(html, "queue-missing-price") == "1"

    def test_an_open_period_says_it_is_open(self, repository, client):
        persist(repository, priced_period())
        html = body(client, f"/kinh-doanh/danh-gia?{SEPTEMBER_QS}")
        assert attr(html, "quality-closed", "data-closed") == "no"

    def test_a_closed_period_is_shown_as_closed_with_no_drift(
        self, repository, service, client
    ):
        persist(repository, priced_period())
        data = service.period(**SEPTEMBER, period=(2026, 9))
        service.close_period(period=(2026, 9), data=data, closed_by="owner")
        html = body(client, f"/kinh-doanh/danh-gia?{SEPTEMBER_QS}")
        assert "Kỳ ĐÃ CHỐT" in metric(html, "quality-closed")
        assert attr(html, "quality-drift", "data-drift") == "no"

    def test_drift_after_a_close_is_reported_and_never_silent(
        self, repository, service, store, client
    ):
        """Số đã phát hành không tự đổi — nhưng trang phải NÓI ra là đã lệch."""
        persist(repository, priced_period())
        data = service.period(**SEPTEMBER, period=(2026, 9))
        service.close_period(period=(2026, 9), data=data, closed_by="owner")
        detail = data.details[0]
        store.set_purchase_price(
            order_key=detail["order_key"], product_key=detail["product_key"],
            occurrence_index=detail["occurrence_index"],
            price=Decimal("1000000"),
            auto_price=detail["line"].auto_purchase_price,
            entered_by="owner", reason="đối chiếu hoá đơn")
        html = body(client, f"/kinh-doanh/danh-gia?{SEPTEMBER_QS}")
        assert attr(html, "quality-drift", "data-drift") == "yes"
        assert "CẢNH BÁO" in html


class TestScopeAndEdgeCases:
    def test_an_unknown_scope_falls_back_to_the_whole_period(
        self, repository, client
    ):
        persist(repository, priced_period())
        html = body(client, f"/kinh-doanh/danh-gia?{SEPTEMBER_QS}&nhom=khong-co")
        assert "Cả kỳ" in html

    def test_a_period_with_no_lines_says_so_on_every_metric(
        self, repository, client
    ):
        persist(repository, priced_period())
        html = body(client, "/kinh-doanh/danh-gia?ky=2026-07")
        # Kỳ 07 không có trong dữ liệu ⟹ rơi về "Toàn bộ dữ liệu", vẫn 200.
        assert metric(html, "compare-percent") == "—"

    def test_the_page_never_writes_anything(self, repository, service, client):
        """Trang đánh giá là một trang ĐỌC — mở nó không đổi một con số nào."""
        persist(repository, priced_period())
        before = service.period(**SEPTEMBER).totals
        body(client, f"/kinh-doanh/danh-gia?{SEPTEMBER_QS}")
        body(client, f"/kinh-doanh/danh-gia?{SEPTEMBER_QS}&nhom=noi-thanh")
        after = service.period(**SEPTEMBER).totals
        assert before == after

    def test_the_evaluation_route_rejects_a_post(self, repository, client):
        persist(repository, priced_period())
        assert client.post("/kinh-doanh/danh-gia").status_code == 405
