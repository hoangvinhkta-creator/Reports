"""TASK-PRA-003 — tầng trình bày SỐ MỚI (CHECK-PRA003-03/04/05/08).

Tầng này là chốt chặn CUỐI trước khi một giá trị ``None`` chạm vào template.
Vì vậy test ở đây hỏi đúng một câu, lặp đi lặp lại dưới nhiều hình dạng:
*"giá trị chưa biết có bị viết thành `0` ở đâu không?"*
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.web import analytics_presentation as ap

# Mọi trường mà tầng truy vấn có thể trả ``None``. Danh sách này là bản hợp
# đồng giữa hai tầng — thêm một chỉ tiêu tiền mới mà quên nó là quên luôn
# nhánh "chưa biết" của chỉ tiêu đó.
NULLABLE_MONEY = ("quantity", "total_sales", "kpi_profit", "accounting_profit")

EMPTY = {
    "lines": 0, "orders": 0, "quantity": None, "total_sales": None,
    "kpi_profit": None, "kpi_lines": 0, "accounting_profit": None,
    "accounting_lines": 0, "auto_orders": 0, "review_orders": 0,
}


def totals(**overrides):
    return {**EMPTY, **overrides}


# --- CHECK-PRA003-03 · None ⟹ "—", không bao giờ 0 -----------------------

@pytest.mark.parametrize("value", [None])
def test_every_money_formatter_turns_a_missing_value_into_a_dash(value):
    assert ap.money(value) == "—"
    assert ap.count(value) == "—"
    assert ap.profit(value, 0, 10)["text"] == "—"


def test_no_field_of_an_empty_overview_is_ever_rendered_as_zero_money():
    """Quét TOÀN BỘ mô hình hiển thị, không chỉ vài ô đã nghĩ tới: không ô
    tiền nào của một kỳ rỗng được phép là ``0`` hay ``0đ``."""
    view = ap.overview(totals(), None, period=(2026, 1), undated=0)
    for field in NULLABLE_MONEY:
        rendered = view[field] if isinstance(view[field], str) else view[field]["text"]
        assert rendered == "—", field
        assert rendered not in {"0", "0đ", "0%"}, field


def test_a_zero_profit_is_written_differently_from_a_missing_profit():
    """Bất biến trung tâm của D1: "lãi bằng không" và "chưa biết lãi bao
    nhiêu" KHÔNG được viết giống nhau."""
    known_zero = ap.profit(Decimal("0"), 10, 10)
    unknown = ap.profit(None, 0, 10)
    assert known_zero["text"] == "0"
    assert unknown["text"] == "—"
    assert known_zero["text"] != unknown["text"]
    assert known_zero["missing"] is False and unknown["missing"] is True


# --- CHECK-PRA003-04 · coverage tường minh -------------------------------

def test_a_profit_cell_always_carries_its_coverage():
    """Quy tắc P4: không có đường nào render con số lợi nhuận mà thiếu mẫu số."""
    for value in (None, Decimal("0"), Decimal("5000000")):
        cell = ap.profit(value, 3, 10)
        assert cell["coverage"], "ô lợi nhuận thiếu coverage"
        assert "dòng" in cell["coverage"]


def test_zero_coverage_over_many_lines_is_rendered_not_hidden():
    """Quy tắc P5: ``0 / 351 dòng`` là câu trả lời HỢP LỆ và phải hiển thị."""
    assert ap.coverage(0, 351) == "0 / 351 dòng"


def test_the_two_coverages_are_rendered_as_separate_cells_with_their_own_numerators():
    view = ap.overview(totals(lines=10, kpi_lines=2, accounting_lines=7,
                              kpi_profit=Decimal("1"), accounting_profit=Decimal("2")),
                       None, period=(2026, 1), undated=0)
    assert view["kpi_profit"]["coverage"] == "2 / 10 dòng"
    assert view["accounting_profit"]["coverage"] == "7 / 10 dòng"
    assert view["kpi_profit"]["coverage"] != view["accounting_profit"]["coverage"]


# --- CHECK-PRA003-08 · so kỳ trước ---------------------------------------

def test_a_previous_period_with_no_lines_blanks_every_comparison_cell():
    """Nhánh dễ sai nhất của mọi dashboard. Kỳ trước KHÔNG có dòng nào ⟹ cả
    Δ lẫn Δ% để trống; TUYỆT ĐỐI không ``0``, ``0%`` hay ``-100%``."""
    view = ap.overview(totals(lines=61, orders=40, total_sales=Decimal("100")),
                       totals(), period=(2026, 9), undated=0)
    comparison = view["comparison"]

    assert comparison["empty"] is True
    for metric in ("orders", "total_sales"):
        assert comparison[metric]["delta"] == "—", metric
        assert comparison[metric]["ratio"] == "—", metric
        assert comparison[metric]["delta"] not in {"0", "+40", "-100%"}
    assert comparison["label"] == "Tháng 08/2026"


def test_a_previous_period_with_data_shows_the_delta_with_the_right_sign():
    view = ap.overview(totals(lines=10, orders=12, total_sales=Decimal("80")),
                       totals(lines=8, orders=10, total_sales=Decimal("100")),
                       period=(2026, 2), undated=0)
    comparison = view["comparison"]

    assert comparison["empty"] is False
    assert comparison["orders"]["delta"] == "+2"
    assert comparison["orders"]["ratio"] == "+20%"
    assert comparison["total_sales"]["delta"] == "-20"
    assert comparison["total_sales"]["ratio"] == "-20%"


def test_the_whole_dataset_view_has_no_comparison_at_all():
    """Không bịa một "kỳ trước" cho một khoảng tuỳ ý."""
    view = ap.overview(totals(lines=10), None, period=None, undated=0)
    assert view["comparison"] is None
    assert view["period_label"] == ap.ALL_DATA_LABEL


def test_a_delta_against_a_previous_value_of_zero_never_divides_by_zero():
    assert ap.delta(Decimal("5"), Decimal("0"))["ratio"] == "—"
    assert ap.delta(Decimal("5"), Decimal("0"))["delta"] == "+5"


def test_the_period_options_offer_the_whole_dataset_first_then_real_months_only():
    options = ap.period_options([(2026, 9), (2026, 1)])
    assert [option["label"] for option in options] == [
        "Toàn bộ dữ liệu", "Tháng 09/2026", "Tháng 01/2026"]
    assert [option["value"] for option in options] == ["tat-ca", "2026-09", "2026-01"]


def test_the_period_options_of_an_empty_database_still_offer_the_whole_dataset():
    assert [option["value"] for option in ap.period_options([])] == ["tat-ca"]


def test_the_previous_period_of_january_is_december_of_the_year_before():
    assert ap.previous_period((2026, 1)) == (2025, 12)
    assert ap.previous_period(None) is None


# --- CHECK-PRA003-05 · bảng nhân viên ------------------------------------

def employee(name, **overrides):
    return {**EMPTY, "employee": name, "employee_group": "G1", **overrides}


def test_the_total_row_counts_each_order_once_not_the_sum_of_the_employee_rows():
    """O-D′ ở tầng trình bày: cột Đơn của dòng TỔNG đến từ ``period_totals``,
    KHÔNG từ việc cộng các dòng phía trên."""
    rows = ap.employee_rows(
        [employee("A", orders=1, lines=1), employee("B", orders=1, lines=1)],
        totals(orders=1, lines=2),
    )
    assert rows[-1]["total_row"] is True
    assert rows[-1]["employee"] == "TỔNG"
    assert rows[-1]["orders"] == "1", "dòng TỔNG đã cộng các dòng nhân viên"
    assert sum(int(row["orders"]) for row in rows[:-1]) == 2


def test_a_row_without_an_employee_is_labelled_not_dropped():
    rows = ap.employee_rows([employee(None, lines=3)], totals(lines=3))
    assert rows[0]["employee"] == ap.UNKNOWN_EMPLOYEE
    assert rows[0]["lines"] == "3"


def test_an_employee_row_carries_both_profit_cells_with_coverage():
    rows = ap.employee_rows([employee("A", lines=4, kpi_lines=1,
                                      kpi_profit=Decimal("10"))], totals(lines=4))
    assert rows[0]["kpi_profit"]["coverage"] == "1 / 4 dòng"
    assert rows[0]["accounting_profit"]["text"] == "—"


def test_the_employee_table_has_exactly_the_eight_frozen_columns():
    """Minimum-Value Filter đã cắt cột AUTO/Review theo dòng và cột so kỳ
    trước. Test này chặn việc chúng lặng lẽ quay lại."""
    assert len(ap.EMPLOYEE_COLUMNS) == 8
    assert ap.QUANTITY_LABEL in ap.EMPLOYEE_COLUMNS


# --- Owner Decision D3 ---------------------------------------------------

def test_the_quantity_label_is_the_one_the_owner_locked():
    assert ap.QUANTITY_LABEL == "Tổng số lượng"
    for forbidden in ("Số lượng sản phẩm", "Tổng số SP"):
        assert forbidden not in ap.QUANTITY_LABEL
        assert forbidden not in " ".join(ap.EMPLOYEE_COLUMNS)


def test_the_quantity_note_warns_that_it_does_not_match_the_old_report():
    assert "Tổng số SP" in ap.QUANTITY_NOTE, "chú thích phải nói rõ nó KHÁC báo cáo cũ"


def test_the_new_number_badge_explains_itself_without_internal_vocabulary():
    assert ap.ORIGIN_BADGE == "SỐ MỚI"
    assert ap.ORIGIN_NOTE == "Số do Reports tính từ sổ kế toán đã nạp."
    for internal in ("snapshot", "run_id", "coverage_state", "PIPELINE_GENERATED"):
        assert internal not in ap.ORIGIN_NOTE + ap.ORIGIN_TITLE + ap.BOTH_SOURCES_NOTE
