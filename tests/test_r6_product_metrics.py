"""R6 §3 — gộp theo bucket: giá bình quân, min/max, và đối soát TUYỆT ĐỐI."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.modules.reporting import dashboard_metrics as dmx
from app.modules.reporting import line_type as lt
from app.modules.reporting import product_metrics as pmx
from tests.test_r6_dashboard_metrics import detail, line


def bucket(key, *, known=True, hint=0):
    if known:
        return pmx.GroupBucket(key=key, label=key)
    return pmx.GroupBucket(key=key, label=key, kind=pmx.KIND_UNDECIDED,
                           reason="chưa xác định vì test nói vậy",
                           sort_hint=hint)


def rows_of(pairs):
    """`[(BusinessLine, GroupBucket)]` → `[GroupRow]`, dựng details tự động."""
    lines = [item[0] for item in pairs]
    details = [detail(item[0], product_key=f"pk{index}")
               for index, item in enumerate(pairs)]
    buckets = [item[1] for item in pairs]
    return pmx.group_rows(lines, details, buckets), details


# --- Bucket ------------------------------------------------------------------

def test_an_undecided_bucket_must_carry_a_reason():
    with pytest.raises(ValueError, match="LÝ DO"):
        pmx.GroupBucket(key="x", label="x", kind=pmx.KIND_UNDECIDED)


def test_an_empty_key_is_refused():
    with pytest.raises(ValueError, match="REQUIRED"):
        pmx.GroupBucket(key="", label="x")


# --- Phân hoạch --------------------------------------------------------------

def test_mismatched_lengths_are_a_hard_error_not_a_silent_truncation():
    """`zip` cắt ngắn im lặng nghĩa là một số dòng biến mất khỏi mọi bucket
    trong khi hàng tổng vẫn trông hợp lệ — đúng lớp lỗi mà phép đối soát tồn
    tại để bắt, nên nó không được phép xảy ra ở tầng dưới nó."""
    one = line("BH1")
    with pytest.raises(ValueError, match="cùng độ dài"):
        pmx.group_rows([one, one], [detail(one)], [bucket("A")])


def test_undecided_buckets_sort_to_the_bottom_in_a_fixed_order():
    rows, _ = rows_of([
        (line("BH1", sell="1000"), bucket("Z-thấp")),
        (line("BH2", sell="9000000"), bucket("__B__", known=False, hint=1)),
        (line("BH3", sell="9000000"), bucket("__A__", known=False, hint=0)),
        (line("BH4", sell="5000000"), bucket("A-cao")),
    ])
    assert [row.bucket.key for row in rows] == ["A-cao", "Z-thấp", "__A__", "__B__"]


def test_known_buckets_sort_by_revenue_descending():
    rows, _ = rows_of([(line("BH1", sell="1000"), bucket("nhỏ")),
                       (line("BH2", sell="9000000"), bucket("lớn"))])
    assert [row.bucket.key for row in rows] == ["lớn", "nhỏ"]


# --- Giá bán bình quân GIA QUYỀN ---------------------------------------------

def test_average_price_is_revenue_over_quantity_not_the_mean_of_unit_prices():
    """Một dòng 1 chiếc 30 triệu + một dòng 100 chiếc 200 nghìn.

    Trung bình đơn giá là 15,1 triệu — một con số không mô tả bất cứ thứ gì đã
    xảy ra. Phép chia gia quyền cho ra số tiền trung bình THẬT trên mỗi chiếc.
    """
    rows, _ = rows_of([
        (line("BH1", sell="30000000", qty="1"), bucket("A")),
        (line("BH2", sell="200000", qty="100"), bucket("A")),
    ])
    stats = rows[0].prices
    assert stats.merchandise_quantity == Decimal("101")
    assert stats.merchandise_revenue == Decimal("50000000")
    assert stats.average == Decimal("495049.50")


def test_average_price_is_none_when_quantity_is_zero_not_zero_dong():
    rows, _ = rows_of([(line("BH1", sell="1000000", qty="0", total="0"),
                        bucket("A"))])
    assert rows[0].prices.average is None


def test_fee_lines_have_no_merchandise_price_but_keep_their_revenue():
    rows, _ = rows_of([(line("BH1", sell="500000", qty="1",
                             line_type=lt.TYPE_FEE), bucket("Phí"))])
    row = rows[0]
    assert row.prices.average is None
    assert row.prices.minimum is None and row.prices.maximum is None
    assert not row.prices.has_merchandise
    assert row.revenue == Decimal("500000")


def test_a_gift_priced_zero_is_a_real_price_and_stays_in_the_minimum():
    """`OD-4` — giá 0 của hàng tặng là giá bán THẬT. Lọc nó ra để min "trông
    hợp lý" là sửa dữ liệu cho khớp trực giác."""
    rows, _ = rows_of([
        (line("BH1", sell="5000000", qty="1"), bucket("A")),
        (line("BH2", sell="0", qty="1", total="0",
              line_type=lt.TYPE_ACCESSORY_GIFT), bucket("A")),
    ])
    assert rows[0].prices.minimum == Decimal("0")
    assert rows[0].prices.maximum == Decimal("5000000")


def test_a_line_without_a_unit_price_does_not_drag_the_minimum_to_zero():
    """Vắng mặt KHÁC 0 — một `None` kéo min xuống 0 sẽ bịa ra một lần bán giá
    0 chưa hề xảy ra."""
    rows, _ = rows_of([
        (line("BH1", sell="5000000", qty="1"), bucket("A")),
        (line("BH2", sell=None, qty="1", total=None), bucket("A")),
    ])
    assert rows[0].prices.minimum == Decimal("5000000")


# --- Số đơn không cộng dọc ---------------------------------------------------

def test_one_order_spanning_two_buckets_is_counted_in_both():
    rows, details = rows_of([(line("BH1"), bucket("A")),
                             (line("BH1"), bucket("B"))])
    assert [row.orders for row in rows] == [1, 1]
    assert dmx.totals(details).orders == 1


# --- Đối soát TUYỆT ĐỐI ------------------------------------------------------

def test_reconciliation_is_exact_across_every_additive_column():
    rows, details = rows_of([
        (line("BH1", sell="1000000", discount="10000"), bucket("A")),
        (line("BH1", sell="2000000", qty="2"), bucket("B")),
        (line("BH2", sell="500000", line_type=lt.TYPE_FEE), bucket("Phí")),
        (line("BH3", sell=None, qty=None, total=None),
         bucket("__X__", known=False)),
    ])
    company = dmx.totals(details)
    result = pmx.reconciliation(rows, company)
    assert result.is_exact
    assert (result.lines, result.sales_revenue, result.quantity,
            result.discount) == (True, True, True, True)


def test_reconciliation_reports_the_exact_column_that_drifted():
    rows, details = rows_of([(line("BH1", sell="1000000"), bucket("A")),
                             (line("BH2", sell="2000000"), bucket("B"))])
    company = dmx.totals(details)
    result = pmx.reconciliation(rows[:1], company)
    assert not result.is_exact
    assert result.lines is False and result.sales_revenue is False


def test_changing_a_bucket_moves_no_money_at_the_company_level():
    """Mệnh đề trung tâm của R6 §3: đổi hãng/nhóm hàng/mapping chỉ ĐỔI BUCKET,
    không đổi một đồng nào của tổng."""
    pairs_a = [(line("BH1", sell="1000000"), bucket("Samsung")),
               (line("BH2", sell="2000000"), bucket("LG"))]
    pairs_b = [(line("BH1", sell="1000000"), bucket("LG")),
               (line("BH2", sell="2000000"), bucket("Samsung"))]
    rows_a, details_a = rows_of(pairs_a)
    rows_b, details_b = rows_of(pairs_b)
    company_a, company_b = dmx.totals(details_a), dmx.totals(details_b)
    assert company_a.sales_revenue == company_b.sales_revenue
    assert company_a.total_quantity == company_b.total_quantity
    assert company_a.discount_total == company_b.discount_total
    assert company_a.orders == company_b.orders
    assert pmx.reconciliation(rows_a, company_a).is_exact
    assert pmx.reconciliation(rows_b, company_b).is_exact
    # …và bucket thì ĐỔI THẬT, nếu không bài này không chứng minh gì.
    assert ({row.bucket.key: row.revenue for row in rows_a}
            != {row.bucket.key: row.revenue for row in rows_b})


def test_share_percent_delegates_to_the_existing_implementation():
    from app.modules.reporting.contribution import share_percent as canonical
    assert (pmx.share_percent(Decimal("1"), Decimal("3"))
            == canonical(Decimal("1"), Decimal("3")))
    assert pmx.share_percent(Decimal("1"), Decimal(0)) is None
    assert pmx.share_percent(None, Decimal("3")) is None
