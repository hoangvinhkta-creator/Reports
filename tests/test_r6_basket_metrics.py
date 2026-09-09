"""R6 §5 — giỏ hàng: bốn chỉ tiêu tách rời, cặp xác định, attachment hai mẫu số."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.modules.reporting import basket_metrics as bkm
from app.modules.reporting import line_type as lt
from app.modules.reporting import product_metrics as pmx
from tests.test_r6_dashboard_metrics import detail, line


def bucket(key):
    return pmx.GroupBucket(key=key, label=key)


def index_of(rows):
    """`rows` = `[(BusinessLine, product_key, category_key)]`."""
    details = [detail(item[0], product_key=item[1]) for item in rows]
    return bkm.build_index(
        details,
        product_buckets=[bucket(item[1]) for item in rows],
        category_buckets=[bucket(item[2]) for item in rows])


# --- Bốn chỉ tiêu KHÔNG suy ra được từ nhau ---------------------------------

def test_two_lines_of_the_same_product_are_multi_line_but_not_multi_product():
    """Mua hai chiếc cùng một mã, ghi hai dòng: đó KHÔNG phải một lần bán chéo,
    và ô "nhiều mặt hàng" phải nói đúng điều đó."""
    index = index_of([(line("BH1"), "pk1", "Tivi"),
                      (line("BH1"), "pk1", "Tivi")])
    counts = bkm.counts(index)
    assert counts.multi_line_orders == 1
    assert counts.multi_product_orders == 0
    assert counts.multi_merchandise_category_orders == 0


def test_a_repeated_product_never_pairs_with_itself():
    index = index_of([(line("BH1"), "pk1", "Tivi"),
                      (line("BH1"), "pk1", "Tivi")])
    assert bkm.product_pairs(index, min_support=1) == []


def test_a_fee_line_never_raises_the_merchandise_category_count():
    """Một tivi + một khoản phí lắp đặt: `service_attachment` ĐÚNG,
    `multi_merchandise_category` SAI. Để phí làm tăng ô ấy sẽ biến mọi đơn có
    phí thành một lần bán chéo nhóm hàng."""
    index = index_of([
        (line("BH1"), "pk1", "Tivi"),
        (line("BH1", line_type=lt.TYPE_FEE), "pk-phi", "__PHI__"),
    ])
    counts = bkm.counts(index)
    assert counts.multi_line_orders == 1
    assert counts.multi_merchandise_category_orders == 0
    assert counts.multi_product_orders == 0
    assert counts.service_attachment_orders == 1


def test_an_order_of_only_fees_is_not_a_service_attachment():
    """Hai vế, không một: một chứng từ chỉ gồm phí không phải một lần bán kèm
    dịch vụ, và đếm nó vào đây làm tỉ lệ cao hơn thực tế."""
    index = index_of([(line("BH1", line_type=lt.TYPE_FEE), "pk-phi", "__PHI__")])
    assert bkm.counts(index).service_attachment_orders == 0


def test_discount_and_undecided_lines_are_not_merchandise_either():
    index = index_of([
        (line("BH1", line_type=lt.TYPE_DISCOUNT), "pk-ck", "__CK__"),
        (line("BH1", line_type=lt.TYPE_UNDECIDED_DOCUMENT), "pk-cd", "__CD__"),
    ])
    counts = bkm.counts(index)
    assert counts.multi_product_orders == 0
    assert counts.multi_merchandise_category_orders == 0


def test_an_undecided_category_is_still_an_explicit_bucket_that_keeps_its_money():
    """Nhóm chưa xác định vẫn phải có bucket rõ ràng — tiền của nó không được
    biến mất, và nó được tính là MỘT nhóm khi so hai nhóm."""
    index = index_of([(line("BH1", sell="1000000"), "pk1", "Tivi"),
                      (line("BH1", sell="2000000"), "pk2", "__CHUA_XAC_DINH__")])
    counts = bkm.counts(index)
    assert counts.multi_merchandise_category_orders == 1
    assert index["BH1"].revenue == Decimal("3000000")
    assert "__CHUA_XAC_DINH__" in index["BH1"].categories


def test_gifts_count_as_merchandise():
    index = index_of([
        (line("BH1"), "pk1", "Tivi"),
        (line("BH1", sell="0", total="0", line_type=lt.TYPE_ACCESSORY_GIFT),
         "pk2", "Phụ kiện"),
    ])
    assert bkm.counts(index).multi_product_orders == 1


# --- Attachment hai mẫu số ----------------------------------------------------

def test_attachment_uses_two_different_denominators():
    """100 đơn có A, 10 đơn có B, cả 10 đơn có B đều có A.

    "Mua B thì 100 % mua A" nhưng "mua A thì chỉ 10 % mua B" — gợi ý bán kèm
    cho hai nhóm khách ấy phải khác nhau, nên hai con số phải khác nhau.
    """
    rows = []
    for number in range(100):
        rows.append((line(f"BH{number}"), "A", "catA"))
        if number < 10:
            rows.append((line(f"BH{number}"), "B", "catB"))
    index = index_of(rows)
    pair = bkm.product_pairs(index)[0]
    assert (pair.left, pair.right) == ("A", "B")
    assert pair.pair_orders == 10
    assert pair.orders_with_left == 100
    assert pair.orders_with_right == 10
    assert pair.attachment_left_to_right == Decimal("10.00")
    assert pair.attachment_right_to_left == Decimal("100.00")


def test_support_equals_pair_orders():
    index = index_of([(line("BH1"), "A", "c"), (line("BH1"), "B", "c"),
                      (line("BH2"), "A", "c"), (line("BH2"), "B", "c")])
    pair = bkm.product_pairs(index)[0]
    assert pair.support == pair.pair_orders == 2


# --- Doanh thu của cặp --------------------------------------------------------

def test_pair_revenue_counts_the_whole_order_exactly_once():
    """Doanh thu đơn chứa cặp cộng TOÀN BỘ doanh thu của đơn — kể cả phần của
    mặt hàng thứ ba — và mỗi đơn đúng một lần."""
    index = index_of([
        (line("BH1", sell="1000000"), "A", "c1"),
        (line("BH1", sell="2000000"), "B", "c2"),
        (line("BH1", sell="4000000"), "C", "c3"),
        (line("BH2", sell="1000000"), "A", "c1"),
        (line("BH2", sell="2000000"), "B", "c2"),
    ])
    pairs = {(p.left, p.right): p for p in bkm.product_pairs(index)}
    assert pairs[("A", "B")].pair_revenue == Decimal("10000000")
    # …và cộng doanh thu của MỌI cặp KHÔNG cho ra doanh thu kỳ, đúng như
    # `PAIR_REVENUE_NOTE` nói ra trên chính bảng.
    every_pair = sum((p.pair_revenue for p in bkm.product_pairs(index, min_support=1)),
                     Decimal(0))
    assert every_pair > Decimal("10000000")


# --- Support và sắp xếp ổn định -----------------------------------------------

def test_product_pairs_default_to_support_two():
    index = index_of([(line("BH1"), "A", "c"), (line("BH1"), "B", "c")])
    assert bkm.product_pairs(index) == []
    assert len(bkm.product_pairs(index, min_support=1)) == 1


def test_category_pairs_show_everything_by_default_but_record_support():
    index = index_of([(line("BH1"), "pk1", "Tivi"),
                      (line("BH1"), "pk2", "Điều hoà")])
    pairs = bkm.category_pairs(index)
    assert len(pairs) == 1
    assert pairs[0].support == 1


def test_pairs_are_unordered_and_sorted_stably():
    index = index_of([
        (line("BH1"), "Z", "c"), (line("BH1"), "A", "c"),
        (line("BH2"), "A", "c"), (line("BH2"), "Z", "c"),
        (line("BH3"), "A", "c"), (line("BH3"), "M", "c"),
    ])
    pairs = bkm.product_pairs(index, min_support=1)
    assert [(p.left, p.right) for p in pairs] == [("A", "Z"), ("A", "M")]
    assert bkm.product_pairs(index, min_support=1) == pairs


# --- Drill-down ---------------------------------------------------------------

def test_orders_with_pair_returns_the_orders_containing_both():
    index = index_of([
        (line("BH1"), "A", "c"), (line("BH1"), "B", "c"),
        (line("BH2"), "A", "c"),
    ])
    assert bkm.orders_with_pair(index, left="A", right="B",
                                dimension="product") == ("BH1",)
    assert bkm.orders_containing(index, member="A",
                                 dimension="product") == ("BH1", "BH2")


def test_an_unknown_drilldown_dimension_is_a_hard_error():
    """Rơi về một chiều mặc định ở đây sẽ trả về danh sách đơn của một chiều
    KHÁC cái người dùng bấm, và trang không có cách nào biết để nói ra."""
    index = index_of([(line("BH1"), "A", "c")])
    with pytest.raises(ValueError, match="chiều giỏ hàng"):
        bkm.orders_containing(index, member="A", dimension="brand")


def test_mismatched_lengths_are_a_hard_error():
    one = line("BH1")
    with pytest.raises(ValueError, match="cùng độ dài"):
        bkm.build_index([detail(one)], product_buckets=[bucket("A")],
                        category_buckets=[])
