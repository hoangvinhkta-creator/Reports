"""R6 §1 — aggregate nền: ngữ nghĩa đúng trên giá trị thuần.

Mọi bài dựng `BusinessLine` bằng tay. Đó là toàn bộ điểm của việc
`dashboard_metrics` thuần: một mệnh đề về tiền phải kiểm được mà không cần
database, Flask hay một lần nạp sổ.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from app.modules.reporting import business_metrics as bm
from app.modules.reporting import dashboard_metrics as dmx
from app.modules.reporting import line_type as lt
from app.web import revenue_timeline


def line(order="BH1", *, sell="1000000", qty="1", discount="0",
         total=None, line_type=lt.TYPE_SALE, employee="Ly"):
    """Một `BusinessLine` tối thiểu. `total` mặc định `sell × qty − discount`
    ĐÚNG như pipeline đã ghi (`DEC-114`) — nhưng bài kiểm nào cần một
    `total_sales` KHÁC đều truyền thẳng, vì R6 đọc trường đó chứ không tính
    lại nó."""
    quantity = None if qty is None else Decimal(qty)
    sell_price = None if sell is None else Decimal(sell)
    if total is None and quantity is not None and sell_price is not None:
        total = sell_price * quantity - Decimal(discount)
    return bm.BusinessLine(
        order_key=order, employee=employee, employee_group="G1", status="AUTO",
        sell_price=sell_price, quantity=quantity, discount=Decimal(discount),
        total_sales=None if total is None else Decimal(total),
        auto_purchase_price=Decimal("500000"), auto_kpi_profit=Decimal("100000"),
        kpi_authority_valid=True, line_type=line_type)


def detail(business_line, *, sale_date=date(2026, 1, 5), product_key="pk",
           product_raw="Tủ lạnh"):
    return {"order_key": business_line.order_key, "product_key": product_key,
            "occurrence_index": 1, "product_raw": product_raw,
            "sale_date": sale_date, "line": business_line}


# --- Doanh thu đọc `total_sales`, KHÔNG tính lại ----------------------------

def test_revenue_reads_total_sales_and_never_recomputes_it():
    """Một dòng mà `total_sales` KHÁC `sell × qty − discount` vẫn được đọc
    NGUYÊN VẸN.

    Đây là bài canh trực tiếp mệnh đề "không tính lại doanh thu": nếu R6 tự
    nhân lại, con số dưới đây sẽ là 1.000.000 thay vì 777.
    """
    odd = line(total="777", sell="1000000", qty="1")
    assert dmx.totals([detail(odd)]).sales_revenue == Decimal("777")


def test_revenue_matches_business_metrics_on_the_same_slice():
    lines = [line("BH1"), line("BH2", sell="2000000"),
             line("BH3", sell="3000000", discount="50000")]
    details = [detail(item) for item in lines]
    assert dmx.totals(details).sales_revenue == bm.totals(lines).sales_revenue


def test_an_empty_slice_gives_none_revenue_not_zero():
    """`NULL ≠ 0` — "chưa có giá trị nào" và "bằng không" là hai câu khác nhau."""
    assert dmx.totals([]).sales_revenue is None
    assert dmx.totals([]).discount_total == Decimal(0)


def test_a_line_without_revenue_is_not_counted_as_zero():
    totals = dmx.totals([detail(line("BH1", total=None, sell=None)),
                         detail(line("BH2", sell="1000000"))])
    assert totals.sales_revenue == Decimal("1000000")
    assert totals.lines_missing_revenue == 1


# --- Chiết khấu cộng ĐÚNG MỘT LẦN -------------------------------------------

def test_discount_is_summed_exactly_once_per_line():
    details = [detail(line("BH1", discount="50000")),
               detail(line("BH1", discount="30000"), product_key="pk2")]
    assert dmx.totals(details).discount_total == Decimal("80000")


def test_gross_is_derived_and_never_a_second_revenue_definition():
    details = [detail(line("BH1", sell="1000000", discount="50000"))]
    totals = dmx.totals(details)
    assert totals.sales_revenue == Decimal("950000")
    assert totals.gross_before_discount == Decimal("1000000")


def test_gross_is_none_when_revenue_is_unknown():
    """Cộng một chiết khấu vào một doanh thu chưa biết không cho ra một doanh
    số — nó cho ra một con số bịa."""
    assert dmx.totals([detail(line(total=None, sell=None,
                                   discount="50000"))]).gross_before_discount is None


# --- Số lượng KHÁC `qualifying_quantity` ------------------------------------

def test_total_quantity_counts_every_line_unlike_qualifying_quantity():
    """`qualifying_quantity` chỉ đếm dòng có ĐƠN GIÁ > 1.000.000
    (`DEC-PHB02-03`). R6 thêm một chỉ tiêu thứ hai bên cạnh, KHÔNG đổi nghĩa
    cái cũ."""
    cheap = line("BH1", sell="200000", qty="3")
    rich = line("BH2", sell="5000000", qty="2")
    lines, details = [cheap, rich], [detail(cheap), detail(rich)]
    assert dmx.totals(details).total_quantity == Decimal("5")
    assert bm.totals(lines).qualifying_quantity == Decimal("2")


def test_a_line_without_quantity_is_counted_separately_not_as_zero():
    totals = dmx.totals([detail(line("BH1", qty=None, total="900000")),
                         detail(line("BH2", qty="2"))])
    assert totals.total_quantity == Decimal("2")
    assert totals.lines_missing_quantity == 1


# --- Đơn ---------------------------------------------------------------------

def test_orders_count_distinct_order_keys():
    details = [detail(line("BH1")), detail(line("BH1"), product_key="pk2"),
               detail(line("BH2"))]
    assert dmx.totals(details).orders == 2


def test_multi_line_orders_count_orders_with_two_or_more_lines():
    details = [detail(line("BH1")), detail(line("BH1"), product_key="pk2"),
               detail(line("BH2"))]
    assert dmx.totals(details).multi_line_orders == 1


def test_positive_revenue_orders_exclude_zero_and_unknown():
    details = [detail(line("BH1", sell="1000000")),
               detail(line("BH2", sell="0", qty="1", total="0")),
               detail(line("BH3", total=None, sell=None))]
    assert dmx.totals(details).positive_revenue_orders == 1


def test_an_orders_revenue_is_the_sum_of_its_lines_before_the_positive_test():
    """Một đơn có dòng âm và dòng dương được xét theo TỔNG của đơn, không theo
    từng dòng — nếu không, một đơn bị chiết khấu hết sạch vẫn đếm là dương."""
    details = [detail(line("BH1", total="1000000")),
               detail(line("BH1", total="-1000000"), product_key="pk2")]
    assert dmx.totals(details).positive_revenue_orders == 0


def test_revenue_per_order_uses_every_order_as_denominator():
    details = [detail(line("BH1", sell="1000000")),
               detail(line("BH2", total=None, sell=None))]
    totals = dmx.totals(details)
    assert totals.orders == 2
    assert totals.revenue_per_order == Decimal("500000.00")


def test_lines_per_order_is_none_when_there_are_no_orders():
    assert dmx.totals([]).lines_per_order is None
    assert dmx.totals([]).revenue_per_order is None


# --- Một đơn thuộc ĐÚNG MỘT mốc ---------------------------------------------

def test_an_order_spanning_two_days_lands_on_its_earliest_day():
    details = [detail(line("BH1"), sale_date=date(2026, 1, 9)),
               detail(line("BH1"), sale_date=date(2026, 1, 5),
                      product_key="pk2")]
    buckets = dmx.orders_by_bucket(
        details, bucket_of=revenue_timeline.bucket_of,
        granularity=revenue_timeline.DAY)
    assert set(buckets) == {"2026-01-05"}
    assert buckets["2026-01-05"]["orders"] == 1


def test_multi_date_orders_are_counted_separately():
    details = [detail(line("BH1"), sale_date=date(2026, 1, 9)),
               detail(line("BH1"), sale_date=date(2026, 1, 5),
                      product_key="pk2"),
               detail(line("BH2"), sale_date=date(2026, 1, 7))]
    assert dmx.totals(details).orders_with_multiple_sale_dates == 1


@pytest.mark.parametrize("granularity", [revenue_timeline.DAY,
                                         revenue_timeline.WEEK,
                                         revenue_timeline.MONTH,
                                         revenue_timeline.QUARTER,
                                         revenue_timeline.YEAR])
def test_the_chart_never_counts_more_orders_than_the_slice_has(granularity):
    """Bất biến của R6 §1, đúng ở CẢ NĂM mức gộp:

        Σ(số đơn của mọi mốc) + orders_without_date == tổng số đơn

    Một biểu đồ vượt tổng của chính nó là một biểu đồ không dùng được để ra
    quyết định, và đây là chỗ điều đó không xảy ra được.
    """
    details = [
        detail(line("BH1"), sale_date=date(2026, 1, 5)),
        detail(line("BH1"), sale_date=date(2026, 3, 20), product_key="pk2"),
        detail(line("BH2"), sale_date=date(2026, 1, 6)),
        detail(line("BH3"), sale_date=date(2026, 7, 1)),
        detail(line("BH4"), sale_date=None),
    ]
    totals = dmx.totals(details)
    buckets = dmx.orders_by_bucket(
        details, bucket_of=revenue_timeline.bucket_of, granularity=granularity)
    charted = sum(slot["orders"] for slot in buckets.values())
    assert charted + totals.orders_without_date == totals.orders == 4


def test_an_order_with_no_dated_line_is_counted_but_never_charted():
    details = [detail(line("BH1"), sale_date=None)]
    totals = dmx.totals(details)
    assert (totals.orders, totals.orders_without_date, totals.undated_lines) == (1, 1, 1)
    assert dmx.orders_by_bucket(
        details, bucket_of=revenue_timeline.bucket_of,
        granularity=revenue_timeline.DAY) == {}


# --- Đối soát với `business_metrics` ----------------------------------------

def test_reconciliation_is_exact_on_the_same_slice():
    lines = [line("BH1"), line("BH1", sell="2000000"), line("BH2")]
    details = [detail(item, product_key=f"pk{index}")
               for index, item in enumerate(lines)]
    assert dmx.reconciliation(dmx.totals(details), bm.totals(lines)).is_exact


def test_reconciliation_fails_loudly_when_a_line_is_dropped():
    """Bài này canh chính phép đối soát: nếu nó không bắt được một dòng bị bỏ
    rơi thì nó không có tác dụng gì."""
    lines = [line("BH1"), line("BH2")]
    details = [detail(lines[0])]
    assert not dmx.reconciliation(dmx.totals(details), bm.totals(lines)).is_exact


# --- Tập hàng hoá là tập ĐÓNG, viết đúng một chỗ -----------------------------

def test_merchandise_types_are_exactly_sale_and_accessory_gift():
    assert dmx.MERCHANDISE_TYPES == frozenset({lt.TYPE_SALE,
                                               lt.TYPE_ACCESSORY_GIFT})


def test_fee_and_discount_and_undecided_are_not_merchandise():
    for name in (lt.TYPE_FEE, lt.TYPE_DISCOUNT, lt.TYPE_RETURN_CANCEL,
                 lt.TYPE_UNDECIDED_DOCUMENT):
        assert name not in dmx.MERCHANDISE_TYPES


def test_service_types_are_exactly_fee():
    assert dmx.SERVICE_TYPES == frozenset({lt.TYPE_FEE})
