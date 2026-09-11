"""R4 — ngữ nghĩa của báo cáo đánh giá, kiểm trên giá trị THUẦN.

Không database, không Flask, không HTML: mọi mệnh đề ở đây là mệnh đề về
NGỮ NGHĨA, nên chúng phải kiểm được mà không dựng gì cả. Bài kiểm qua route
web thật nằm ở `tests/test_r4_evaluation_web.py`.

Sợi chỉ đỏ xuyên suốt file: **`None` không bao giờ được thành `0`**, và một ô
không có số luôn nói được vì sao nó không có số.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from app.modules.reporting import business_metrics as bm
from app.modules.reporting import evaluation as ev
from app.modules.reporting import line_type as line_type_module

SEPT = (2026, 9)
AUG = (2026, 8)
MAR = (2026, 3)


def line(**kwargs) -> bm.BusinessLine:
    """Một dòng hàng mặc định LÀNH — cùng khuôn `tests/test_business_metrics`.

    Mặc định lành có chủ đích: mỗi bài chỉ hỏng đúng một thứ nó đang nói về,
    nên "vì sao ô này trống" luôn có đúng một câu trả lời.
    """
    defaults = dict(
        order_key="BH1", employee="Ly", employee_group="STANDARD_SALES",
        status="AUTO", sell_price=Decimal("8000000"), quantity=Decimal("1"),
        discount=Decimal("0"), total_sales=Decimal("8000000"),
        auto_purchase_price=Decimal("6000000"),
        auto_kpi_profit=Decimal("2000000"),
        kpi_authority_valid=True, conversion_rate=Decimal("0.05"),
    )
    return bm.BusinessLine(**{**defaults, **kwargs})


def pending(**kwargs) -> bm.BusinessLine:
    """Dòng CHƯA có giá nhập — trạng thái mà production thật sự tạo ra."""
    return line(**{**dict(status="PENDING", auto_purchase_price=None,
                          auto_kpi_profit=None), **kwargs})


def detail(product="TV43", *, day=5, month=9, group="DIEN_MAY",
           lead="PERSONAL", **kwargs) -> dict:
    """Bản ghi hiển thị đi kèm một dòng — đúng hình dạng `line_details` trả về."""
    return {
        "order_key": kwargs.get("order_key", "BH1"),
        "product_key": kwargs.pop("product_key", product.lower()),
        "occurrence_index": 1,
        "product_raw": product,
        "sale_date": None if day is None else date(2026, month, day),
        "classified_product_group": None,
        "pipeline_product_group": group,
        "lead_source": lead,
        "line": line(**kwargs),
    }


# ==========================================================================
# §1 — Bộ chỉ tiêu đầu trang
# ==========================================================================

class TestHeadlineArithmetic:
    def test_the_three_derived_metrics_divide_the_numbers_already_agreed(self):
        """`Doanh thu/đơn`, `Biên KPI`, `Lãi/đơn` là ba phép CHIA, không hơn."""
        totals = bm.totals([line(order_key="BH1"),
                            line(order_key="BH2", total_sales=Decimal("2000000"),
                                 sell_price=Decimal("2000000"),
                                 auto_purchase_price=Decimal("1000000"),
                                 auto_kpi_profit=Decimal("1000000"))])
        kpis = ev.headline(totals)
        assert totals.sales_revenue == Decimal("10000000")
        assert totals.orders == 2
        assert totals.official_kpi_profit == Decimal("3000000")
        assert kpis["revenue_per_order"].value == Decimal("5000000")
        assert kpis["profit_per_order"].value == Decimal("1500000")
        assert kpis["margin_percent"].value == Decimal("30.00")

    def test_a_zero_denominator_never_becomes_a_number(self):
        """Không đơn nào ⟹ `—` kèm `NO_ORDERS`, không phải `0 đồng/đơn`."""
        totals = bm.totals([])
        kpis = ev.headline(totals)
        assert kpis["revenue_per_order"].value is None
        assert kpis["revenue_per_order"].reason == ev.REASON_NO_LINES
        assert kpis["orders"].value is None
        assert kpis["orders"].reason == ev.REASON_NO_LINES

    def test_a_negative_margin_is_reported_as_it_is(self):
        """Biên âm là một sự thật kế toán — không kẹp về 0, không giấu."""
        losing = line(sell_price=Decimal("1000000"),
                      total_sales=Decimal("1000000"),
                      auto_purchase_price=Decimal("1500000"),
                      auto_kpi_profit=Decimal("-500000"))
        kpis = ev.headline(bm.totals([losing]))
        assert kpis["margin_percent"].value == Decimal("-50.00")
        assert kpis["kpi_profit"].value == Decimal("-500000")

    def test_margin_is_not_capped_above_one_hundred(self):
        free = line(auto_purchase_price=Decimal("0"),
                    auto_kpi_profit=Decimal("8000000"))
        kpis = ev.headline(bm.totals([free]))
        assert kpis["margin_percent"].value == Decimal("100.00")

    def test_every_kpi_without_a_number_carries_a_reason(self):
        """Bất biến trung tâm của R4, kiểm trên MỌI ô của MỌI tình huống."""
        for totals in (bm.totals([]), bm.totals([pending()]),
                       bm.totals([line(), pending(order_key="BH2")])):
            for key, kpi in ev.headline(totals).items():
                assert (kpi.value is None) == (kpi.reason is not None), key
                if kpi.reason is not None:
                    assert kpi.reason in (ev.KPI_REASONS), (key, kpi.reason)

    def test_the_headline_order_is_the_frozen_eight(self):
        assert set(ev.HEADLINE_ORDER) == set(ev.headline(bm.totals([])))
        assert len(ev.HEADLINE_ORDER) == 8

    def test_a_kpi_cannot_be_built_with_both_a_value_and_a_reason(self):
        """Bất biến được canh ở constructor, không chỉ ở nơi gọi."""
        with pytest.raises(ValueError):
            ev.Kpi(key="x", value=Decimal(1), unit=ev.UNIT_VND,
                   reason=ev.REASON_NO_LINES)
        with pytest.raises(ValueError):
            ev.Kpi(key="x", value=None, unit=ev.UNIT_VND)


class TestCoverageGate:
    """Cổng 100 % — một phần lợi nhuận KHÔNG BAO GIỜ là kết luận cả kỳ."""

    def test_a_partial_period_publishes_no_profit_margin_or_converted_sales(self):
        totals = bm.totals([line(), pending(order_key="BH2")])
        kpis = ev.headline(totals)
        assert not totals.coverage.is_complete
        for key in ("kpi_profit", "margin_percent", "profit_per_order",
                    "converted_sales"):
            assert kpis[key].value is None, key
        assert kpis["kpi_profit"].reason == ev.REASON_PROFIT_NOT_OFFICIAL
        assert kpis["converted_sales"].reason == ev.REASON_CONVERTED_NOT_OFFICIAL

    def test_the_partial_number_is_kept_as_evidence_but_never_as_the_value(self):
        """Con số một phần vẫn đọc được — ở `partial_value`, không ở `value`."""
        totals = bm.totals([line(), pending(order_key="BH2")])
        kpi = ev.headline(totals)["kpi_profit"]
        assert kpi.value is None
        assert kpi.partial_value == Decimal("2000000")

    def test_revenue_is_never_gated_by_coverage(self):
        """Doanh thu không phụ thuộc giá nhập, nên nó vẫn có số."""
        kpis = ev.headline(bm.totals([line(), pending(order_key="BH2")]))
        assert kpis["sales_revenue"].value == Decimal("16000000")
        assert kpis["orders"].value == Decimal(2)

    def test_full_coverage_unlocks_every_gated_metric(self):
        kpis = ev.headline(bm.totals([line(), line(order_key="BH2")]))
        for key in ("kpi_profit", "margin_percent", "profit_per_order",
                    "converted_sales"):
            assert kpis[key].value is not None, key


# ==========================================================================
# §2 — Lịch, target, run-rate
# ==========================================================================

class TestCalendar:
    def test_elapsed_days_include_today(self):
        """`§15` — ngày hôm nay là một ngày bán đang diễn ra."""
        assert ev.days_elapsed(SEPT, today=date(2026, 9, 8)) == 8
        assert ev.days_remaining(SEPT, today=date(2026, 9, 8)) == 22

    def test_a_finished_month_is_measured_to_its_last_day(self):
        assert ev.as_of(AUG, today=date(2026, 9, 8)) == date(2026, 8, 31)
        assert ev.days_elapsed(AUG, today=date(2026, 9, 8)) == 31
        assert ev.days_remaining(AUG, today=date(2026, 9, 8)) == 0

    def test_a_future_month_has_no_as_of_date(self):
        assert ev.as_of((2026, 12), today=date(2026, 9, 8)) is None
        assert ev.days_elapsed((2026, 12), today=date(2026, 9, 8)) == 0

    def test_the_last_day_of_a_month_leaves_no_days_remaining(self):
        assert ev.days_remaining(SEPT, today=date(2026, 9, 30)) == 0


class TestTargetProgress:
    def _totals(self, converted_ok=True):
        return bm.totals([line()] if converted_ok
                         else [line(), pending(order_key="BH2")])

    def test_percent_uses_converted_sales_and_is_not_capped(self):
        totals = self._totals()
        assert totals.official_converted_sales == Decimal("40000000")
        progress = ev.target_progress(
            target=Decimal("20000000"), totals=totals, period=SEPT,
            today=date(2026, 9, 8))
        assert progress.percent == Decimal("200.00")
        assert progress.achieved is True
        assert progress.shortfall == Decimal(0)
        assert progress.required_per_day == Decimal(0)

    def test_an_unset_target_is_not_a_zero_target(self):
        unset = ev.target_progress(target=None, totals=self._totals(),
                                   period=SEPT, today=date(2026, 9, 8))
        zero = ev.target_progress(target=Decimal(0), totals=self._totals(),
                                  period=SEPT, today=date(2026, 9, 8))
        assert unset.reason == bm.TARGET_UNSET
        assert zero.reason == bm.TARGET_ZERO
        assert unset.percent is None and zero.percent is None

    def test_a_partial_converted_sales_is_told_apart_from_having_none(self):
        """Hai tình huống, hai việc phải làm — không được gộp."""
        partial = ev.target_progress(
            target=Decimal("20000000"), totals=self._totals(converted_ok=False),
            period=SEPT, today=date(2026, 9, 8))
        assert partial.reason == ev.TARGET_ACTUAL_NOT_OFFICIAL
        assert partial.partial_actual == Decimal("40000000")
        assert partial.actual is None
        assert partial.percent is None

        nothing = ev.target_progress(
            target=Decimal("20000000"), totals=bm.totals([]),
            period=SEPT, today=date(2026, 9, 8))
        assert nothing.reason == bm.TARGET_NO_ACTUAL
        assert nothing.partial_actual is None

    def test_required_per_day_divides_the_gap_by_the_days_left(self):
        progress = ev.target_progress(
            target=Decimal("100000000"), totals=self._totals(), period=SEPT,
            today=date(2026, 9, 10))
        assert progress.shortfall == Decimal("60000000")
        assert progress.days_remaining == 20
        assert progress.required_per_day == Decimal("3000000")
        assert progress.achieved is False

    def test_the_last_day_of_the_month_never_divides_by_zero(self):
        progress = ev.target_progress(
            target=Decimal("100000000"), totals=self._totals(), period=SEPT,
            today=date(2026, 9, 30))
        assert progress.days_remaining == 0
        assert progress.required_per_day is None
        assert progress.required_reason == ev.TARGET_NO_DAYS_REMAINING
        # Cửa "hết ngày" KHÔNG được nói thành "đã đạt".
        assert progress.achieved is False
        assert progress.shortfall == Decimal("60000000")


class TestRunRate:
    def _totals(self):
        return bm.totals([line()])

    def test_run_rate_scales_the_value_to_the_whole_month(self):
        run = ev.run_rate(Decimal("8000000"), period=SEPT,
                          today=date(2026, 9, 8), dated_lines=1)
        assert run.value == Decimal("30000000")  # 8tr / 8 ngày × 30 ngày
        assert run.elapsed_days == 8 and run.month_days == 30
        assert run.reason is None

    def test_a_finished_month_is_not_forecast(self):
        run = ev.run_rate(Decimal("8000000"), period=AUG,
                          today=date(2026, 9, 8), dated_lines=1)
        assert run.value is None
        assert run.reason == ev.RUNRATE_NOT_RUNNING

    def test_a_value_that_is_not_official_is_never_scaled_up(self):
        """Nhân một con số một phần lên cả tháng là nhân cả phần thiếu lên."""
        run = ev.run_rate(Decimal("8000000"), period=SEPT,
                          today=date(2026, 9, 8), dated_lines=1, official=False)
        assert run.value is None
        assert run.reason == ev.RUNRATE_VALUE_NOT_OFFICIAL

    def test_without_dated_lines_there_is_no_speed_to_measure(self):
        run = ev.run_rate(Decimal("8000000"), period=SEPT,
                          today=date(2026, 9, 8), dated_lines=0)
        assert run.value is None
        assert run.reason == ev.RUNRATE_NO_DAILY_DATA

    def test_every_run_rate_reason_is_from_the_closed_set(self):
        for run in (ev.run_rate(None, period=SEPT, today=date(2026, 9, 8),
                                dated_lines=1),
                    ev.run_rate(Decimal(1), period=None,
                                today=date(2026, 9, 8), dated_lines=1)):
            assert run.reason in ev.RUNRATE_REASONS


# ==========================================================================
# §2 — So kỳ trước theo CÙNG SỐ NGÀY LỊCH
# ==========================================================================

class TestSameDaysComparison:
    def test_a_running_month_is_cut_at_the_same_calendar_day_on_both_sides(self):
        """01–08/09 so với 01–08/08 — không phải cả tháng 8 so với 8 ngày."""
        current = [detail(day=3, order_key="BH1"),
                   detail(day=20, order_key="BH2")]
        previous = [detail(day=3, month=8, order_key="BH9"),
                    detail(day=25, month=8, order_key="BH8")]
        result = ev.same_days_comparison(
            period=SEPT, current_details=current, previous_details=previous,
            today=date(2026, 9, 8))
        assert result.day_cutoff == 8
        assert result.current == Decimal("8000000")   # chỉ ngày 3
        assert result.previous == Decimal("8000000")  # chỉ ngày 3
        assert result.percent == Decimal("0.00")
        assert result.full_month is False

    def test_a_finished_month_compares_the_two_whole_months(self):
        current = [detail(day=3), detail(day=20, order_key="BH2")]
        previous = [detail(day=3, month=7, order_key="BH9")]
        result = ev.same_days_comparison(
            period=AUG, current_details=current, previous_details=previous,
            today=date(2026, 9, 8))
        assert result.full_month is True
        assert result.current == Decimal("16000000")

    def test_a_shorter_previous_month_shortens_both_sides(self):
        """31/03 so tháng 02: cắt CẢ HAI ở ngày 28, không phải 31 vs 28."""
        current = [detail(day=30, month=3, order_key="BH1")]
        previous = [detail(day=27, month=2, order_key="BH9")]
        result = ev.same_days_comparison(
            period=MAR, current_details=current, previous_details=previous,
            today=date(2026, 3, 31))
        assert result.as_of_day == 31
        assert result.day_cutoff == 28
        # Dòng ngày 30/03 nằm NGOÀI cửa sổ 01–28, nên nó không vào vế nào.
        assert result.current is None
        assert result.previous == Decimal("8000000")

    def test_an_empty_previous_period_is_said_in_words_not_in_a_percent(self):
        result = ev.same_days_comparison(
            period=SEPT, current_details=[detail(day=3)], previous_details=[],
            today=date(2026, 9, 8))
        assert result.percent is None
        assert result.reason == ev.COMPARE_PREVIOUS_NO_LINES

    def test_a_previous_period_with_zero_revenue_prints_no_percent(self):
        zero = detail(day=3, month=8, order_key="BH9",
                      total_sales=Decimal("0"), sell_price=Decimal("0"),
                      auto_purchase_price=Decimal("0"),
                      auto_kpi_profit=Decimal("0"))
        result = ev.same_days_comparison(
            period=SEPT, current_details=[detail(day=3)],
            previous_details=[zero], today=date(2026, 9, 8))
        assert result.percent is None
        assert result.reason == ev.COMPARE_PREVIOUS_ZERO

    def test_undated_lines_never_enter_either_side_and_are_counted(self):
        current = [detail(day=3), detail(day=None, order_key="BH2")]
        previous = [detail(day=3, month=8, order_key="BH9")]
        result = ev.same_days_comparison(
            period=SEPT, current_details=current, previous_details=previous,
            today=date(2026, 9, 8))
        assert result.excluded_undated_lines == 1
        assert result.current == Decimal("8000000")

    def test_all_data_view_has_no_previous_period(self):
        result = ev.same_days_comparison(
            period=None, current_details=[detail()], previous_details=[],
            today=date(2026, 9, 8))
        assert result.reason == ev.COMPARE_NO_PERIOD

    def test_every_comparison_reason_is_from_the_closed_set(self):
        empty_current = ev.same_days_comparison(
            period=SEPT, current_details=[],
            previous_details=[detail(day=3, month=8)],
            today=date(2026, 9, 8))
        assert empty_current.reason == ev.COMPARE_CURRENT_NO_REVENUE
        assert empty_current.reason in ev.COMPARE_REASONS


# ==========================================================================
# §3 — Phân tích đóng góp
# ==========================================================================

class TestContributionTables:
    def _details(self):
        return [
            detail("TV43", product_key="tv43", day=3, order_key="BH1"),
            detail("TV43", product_key="tv43", day=4, order_key="BH2"),
            detail("Tủ lạnh", product_key="tl200", day=5, order_key="BH1",
                   total_sales=Decimal("2000000"),
                   sell_price=Decimal("2000000"),
                   auto_purchase_price=Decimal("1500000"),
                   auto_kpi_profit=Decimal("500000")),
        ]

    def test_the_partition_adds_back_to_the_period_total(self):
        details = self._details()
        whole = bm.totals([d["line"] for d in details])
        rows = ev.by_product(details, whole=whole)
        assert sum((row.totals.sales_revenue for row in rows),
                   Decimal(0)) == whole.sales_revenue
        assert sum(row.totals.lines for row in rows) == whole.lines

    def test_orders_are_distinct_inside_a_row_and_do_not_add_up(self):
        """BH1 có mặt ở CẢ HAI mặt hàng — cộng cột Đơn sẽ ra 3, tổng thật là 2."""
        details = self._details()
        whole = bm.totals([d["line"] for d in details])
        rows = ev.by_product(details, whole=whole)
        assert whole.orders == 2
        assert sum(row.totals.orders for row in rows) == 3

    def test_rows_are_sorted_by_revenue_and_carry_a_share(self):
        details = self._details()
        whole = bm.totals([d["line"] for d in details])
        rows = ev.by_product(details, whole=whole)
        assert [row.label for row in rows] == ["TV43", "Tủ lạnh"]
        assert rows[0].revenue_share == Decimal("88.89")

    def test_a_row_without_full_coverage_has_no_margin_only_a_reason(self):
        details = [detail("TV43", product_key="tv43"),
                   detail("TV43", product_key="tv43", order_key="BH2",
                          status="PENDING", auto_purchase_price=None,
                          auto_kpi_profit=None)]
        whole = bm.totals([d["line"] for d in details])
        row = ev.by_product(details, whole=whole)[0]
        assert row.margin is None
        assert row.margin_reason == ev.REASON_PROFIT_NOT_OFFICIAL

    def test_lowest_margin_only_ranks_rows_that_actually_have_a_margin(self):
        details = self._details() + [
            detail("Máy giặt", product_key="mg50", order_key="BH3",
                   status="PENDING", auto_purchase_price=None,
                   auto_kpi_profit=None)]
        whole = bm.totals([d["line"] for d in details])
        rows = ev.by_product(details, whole=whole)
        ranked = ev.lowest_margin_rows(rows, limit=5)
        assert "mg50" not in [row.key for row in ranked]
        assert [row.margin for row in ranked] == sorted(
            row.margin for row in ranked)

    def test_lead_source_keeps_an_explicit_bucket_for_lines_without_one(self):
        details = [detail(lead="PERSONAL"),
                   detail(lead=None, order_key="BH2")]
        whole = bm.totals([d["line"] for d in details])
        rows = ev.by_lead_source(details, whole=whole)
        assert {row.key for row in rows} == {"PERSONAL", "KHONG_XAC_DINH"}
        assert sum(row.totals.lines for row in rows) == 2

    def test_product_group_falls_back_to_the_pipeline_value(self):
        details = [detail(group="DIEN_MAY"),
                   detail(group=None, order_key="BH2")]
        whole = bm.totals([d["line"] for d in details])
        rows = ev.by_product_group(details, whole=whole)
        assert {row.key for row in rows} == {"DIEN_MAY", "KHONG_XAC_DINH"}


class TestDiscounts:
    def test_the_discount_is_added_back_once_and_never_subtracted_twice(self):
        """`total_sales` đã là NET; khối này chỉ CỘNG NGƯỢC để nói ra quy mô."""
        discounted = line(discount=Decimal("500000"),
                          total_sales=Decimal("7500000"),
                          auto_kpi_profit=Decimal("1500000"))
        whole = bm.totals([discounted])
        summary = ev.discounts([discounted], whole=whole)
        assert summary.discount_total == Decimal("500000")
        assert summary.net_revenue == Decimal("7500000")
        assert summary.gross_revenue == Decimal("8000000")
        assert summary.percent_of_gross == Decimal("6.25")
        assert summary.lines_with_discount == 1
        assert summary.orders_with_discount == 1

    def test_a_legacy_discount_row_is_not_counted_as_a_discount_column(self):
        """Hai CÁCH GHI của cùng một nghiệp vụ — cộng cả hai là trừ hai lần."""
        legacy_row = line(order_key="BH1", line_type=line_type_module.TYPE_DISCOUNT,
                          discount=Decimal("0"),
                          total_sales=Decimal("-100000"),
                          sell_price=Decimal("0"),
                          auto_purchase_price=Decimal("0"),
                          auto_kpi_profit=Decimal("-100000"))
        lines = [line(order_key="BH1"), legacy_row]
        summary = ev.discounts(lines, whole=bm.totals(lines))
        assert summary.discount_total == Decimal(0)

    def test_an_order_written_both_ways_is_named_not_silently_fixed(self):
        both = [line(order_key="BH1", discount=Decimal("100000"),
                     total_sales=Decimal("7900000"),
                     auto_kpi_profit=Decimal("1900000")),
                line(order_key="BH1", line_type=line_type_module.TYPE_DISCOUNT,
                     discount=Decimal("0"), total_sales=Decimal("-100000"),
                     sell_price=Decimal("0"),
                     auto_purchase_price=Decimal("0"),
                     auto_kpi_profit=Decimal("-100000"))]
        summary = ev.discounts(both, whole=bm.totals(both))
        assert summary.double_count_orders == ("BH1",)

    def test_no_discount_gives_a_zero_total_and_no_percent_of_nothing(self):
        summary = ev.discounts([], whole=bm.totals([]))
        assert summary.discount_total == Decimal(0)
        assert summary.percent_of_gross is None
        assert summary.net_revenue is None


class TestLossLines:
    def test_a_line_without_a_profit_is_not_a_losing_line(self):
        """Thiếu giá nhập KHÁC bán lỗ — gộp hai thứ đó là báo lỗ oan."""
        lines = [line(), pending(order_key="BH2")]
        scope = ev.loss_lines(lines)
        assert scope.lines == ()
        assert scope.loss_total is None
        assert scope.examined_lines == 1
        assert scope.total_lines == 2
        assert scope.complete_scope is False

    def test_losing_lines_are_summed_and_their_orders_named(self):
        losing = line(order_key="BH2", sell_price=Decimal("1000000"),
                      total_sales=Decimal("1000000"),
                      auto_purchase_price=Decimal("1500000"),
                      auto_kpi_profit=Decimal("-500000"))
        scope = ev.loss_lines([line(), losing])
        assert scope.loss_total == Decimal("-500000")
        assert scope.orders == ("BH2",)
        assert scope.complete_scope is True


class TestDataQualityInputs:
    def test_the_provenance_breakdown_accounts_for_every_line(self):
        lines = [line(), pending(order_key="BH2"),
                 line(order_key="BH3", manual_purchase_price=Decimal("100"),
                      manual_provenance=bm.PROVENANCE_MANUAL_OVERRIDE)]
        breakdown = ev.provenance_breakdown(lines)
        assert sum(count for _code, count in breakdown) == len(lines)
        assert dict(breakdown)[bm.PROVENANCE_PENDING] == 1
        assert dict(breakdown)[bm.PROVENANCE_MANUAL_OVERRIDE] == 1

    def test_policy_zero_is_never_folded_into_pending(self):
        fee = line(line_type=line_type_module.TYPE_FEE,
                   auto_purchase_price=None, auto_kpi_profit=None)
        breakdown = dict(ev.provenance_breakdown([fee]))
        assert breakdown.get(bm.PROVENANCE_POLICY_ZERO) == 1
        assert bm.PROVENANCE_PENDING not in breakdown

    def test_the_latest_sale_date_ignores_undated_lines(self):
        details = [detail(day=3), detail(day=None, order_key="BH2"),
                   detail(day=20, order_key="BH3")]
        assert ev.latest_sale_date(details) == date(2026, 9, 20)
        assert ev.dated_line_count(details) == 2

    def test_a_period_with_no_dated_line_reports_none_not_a_guess(self):
        assert ev.latest_sale_date([detail(day=None)]) is None
        assert ev.dated_line_count([detail(day=None)]) == 0
