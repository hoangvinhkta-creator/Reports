"""R6 §5 — GIỎ HÀNG: bốn chỉ tiêu tách rời, cặp xác định, và attachment.

Module này THUẦN. Nó dựng một index in-memory `order_key → tập sản phẩm / tập
nhóm hàng / tập loại dòng` từ chính `PeriodData.details`, rồi trả lời bốn câu
hỏi KHÁC NHAU về giỏ hàng. Không bảng mới, không migration, không cache trên
đĩa: index sống đúng một lần tải trang, và một kỳ của sổ này là vài trăm dòng.

## Bốn chỉ tiêu, KHÔNG gộp

Gộp chúng thành một ô "đơn nhiều mặt hàng" là cách nhanh nhất để một quyết
định bán chéo dựa trên một con số không mô tả điều người đọc nghĩ:

```text
multi_line_orders                    >= 2 DÒNG hiệu lực
multi_product_orders                 >= 2 product_key KHÁC NHAU, chỉ dòng
                                     SALE + ACCESSORY_GIFT
multi_merchandise_category_orders    >= 2 BUCKET nhóm hàng khác nhau, chỉ dòng
                                     hàng hoá (loại FEE, DISCOUNT,
                                     RETURN_CANCEL, UNDECIDED_DOCUMENT)
service_attachment_orders            có hàng hoá VÀ có phí/dịch vụ
```

Bốn con số này KHÔNG suy ra được từ nhau, và trên dữ liệu thật chúng lệch nhau
theo những hướng có ý nghĩa nghiệp vụ riêng:

- Một đơn hai dòng CÙNG một mã (mua hai chiếc, ghi hai dòng) là
  `multi_line` nhưng KHÔNG `multi_product` — nó không phải một lần bán chéo.
- Một đơn có một cái tivi và một khoản phí lắp đặt là `multi_line` và
  `service_attachment`, nhưng KHÔNG `multi_merchandise_category`: phí không
  phải một nhóm hàng hoá, và để nó làm tăng ô ấy sẽ biến mọi đơn có phí thành
  một lần bán chéo nhóm hàng.

## Cặp — SET, không phải danh sách dòng

Cặp sản phẩm dựng từ `set(product_key)` của TỪNG đơn. Một mã lặp ở hai dòng
của cùng đơn chỉ tính MỘT lần, nên nó không tự tạo cặp với chính nó và không
làm phồng `pair_orders`. Cặp nhóm hàng dựng từ `set` bucket nhóm hàng theo
đúng cách ấy.

Cặp là KHÔNG CÓ THỨ TỰ: `{A, B}` và `{B, A}` là một cặp, ghi bằng `left < right`
để hai lần chạy cho ra cùng một danh sách và cùng một thứ tự (`sort` ổn định
theo `(-pair_orders, left, right)`).

## Attachment có HAI mẫu số, không một

```text
attachment A→B = pair_orders / orders_with_A
attachment B→A = pair_orders / orders_with_B
```

Hai con số này khác nhau, và dùng một mẫu số cho cả hai chiều là một lỗi đọc
trực tiếp thành quyết định bán hàng: nếu 100 đơn có A và 10 đơn có B, và cả 10
đơn có B đều có A, thì "mua B thì 100 % mua A" nhưng "mua A thì chỉ 10 % mua
B". Gợi ý bán kèm cho hai nhóm khách ấy phải khác nhau.

## Doanh thu của cặp — cộng TOÀN BỘ đơn, đúng MỘT LẦN

`pair_revenue` là tổng doanh thu hiệu lực của các đơn chứa CẢ HAI, cộng mỗi
đơn đúng một lần — kể cả phần doanh thu của những mặt hàng khác trong đơn đó.
Đó là câu trả lời cho "những đơn có cặp này lớn cỡ nào", vốn là câu hỏi người
đọc thật sự hỏi khi họ nhìn một bảng cặp.

Nó KHÔNG phải "doanh thu của A cộng doanh thu của B", và trang phải nói ra
điều đó: cộng `pair_revenue` của mọi cặp KHÔNG cho ra doanh thu kỳ, vì một đơn
ba mặt hàng góp mặt ở ba cặp. `PAIR_REVENUE_NOTE` là câu đó, và nó có mặt trên
chính bảng cặp chứ không nằm trong tài liệu.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Iterable, Optional, Sequence

from app.modules.reporting import dashboard_metrics as dmx

_CENT = Decimal("0.01")

#: Support tối thiểu MẶC ĐỊNH của bảng cặp SẢN PHẨM. Hai đơn chứ không một:
#: một cặp xuất hiện đúng một lần là một sự trùng hợp, và một bảng đầy những
#: sự trùng hợp che mất vài cặp thật.
DEFAULT_PRODUCT_MIN_SUPPORT = 2

#: Bảng cặp NHÓM HÀNG được phép hiện toàn bộ (support 1 trở lên) vì số nhóm
#: hàng nhỏ và một cặp nhóm hàng xuất hiện một lần vẫn là một thông tin đọc
#: được — nhưng support PHẢI được ghi ra cột, không được ẩn đi.
DEFAULT_CATEGORY_MIN_SUPPORT = 1

PAIR_REVENUE_NOTE = (
    "\"Doanh thu đơn chứa cặp\" cộng TOÀN BỘ doanh thu hiệu lực của những đơn "
    "chứa cả hai mặt hàng — mỗi đơn đúng một lần, kể cả phần tiền của các mặt "
    "hàng khác trong cùng đơn. Vì một đơn ba mặt hàng góp mặt ở ba cặp, KHÔNG "
    "được cộng cột này lại để lấy doanh thu kỳ."
)

ATTACHMENT_NOTE = (
    "Hai cột attachment dùng HAI mẫu số khác nhau: A→B chia cho số đơn có A, "
    "B→A chia cho số đơn có B. Chúng gần như luôn khác nhau, và đó là điều "
    "cần đọc — \"mua B thì hay mua A\" không có nghĩa \"mua A thì hay mua B\"."
)

SUPPORT_NOTE = (
    "Support là SỐ ĐƠN chứa cả hai. Bảng cặp sản phẩm mặc định chỉ hiện cặp có "
    "support từ 2 trở lên; bảng cặp nhóm hàng hiện toàn bộ và vẫn ghi support "
    "ở cột riêng."
)

MULTI_METRIC_NOTE = (
    "Bốn ô giỏ hàng đếm bốn tập đơn KHÁC NHAU và không suy ra được từ nhau. "
    "Đơn hai dòng cùng một mã là \"nhiều dòng\" nhưng KHÔNG phải \"nhiều mặt "
    "hàng\"; đơn có phí lắp đặt là \"có dịch vụ kèm\" nhưng phí KHÔNG làm tăng "
    "ô \"nhiều nhóm hàng hoá\"."
)


@dataclass(frozen=True)
class OrderBasket:
    """Giỏ hàng của MỘT đơn — index in-memory của R6 §5.

    `products`/`categories` là SET, và đó là toàn bộ lý do lớp này tồn tại:
    mọi chỉ tiêu giỏ hàng đọc lại từ đây, nên không có đường nào để một mã lặp
    hai dòng thành hai thành viên của giỏ.
    """

    order_key: str
    products: frozenset
    categories: frozenset
    line_types: frozenset
    lines: int
    merchandise_lines: int
    revenue: Optional[Decimal]
    #: Nhãn hiển thị của từng thành viên, để bảng cặp không phải tra lại tầng
    #: taxonomy: `{khoá thành viên: nhãn}`.
    product_labels: dict
    category_labels: dict

    @property
    def multi_line(self) -> bool:
        return self.lines >= 2

    @property
    def multi_product(self) -> bool:
        return len(self.products) >= 2

    @property
    def multi_category(self) -> bool:
        return len(self.categories) >= 2

    @property
    def service_attachment(self) -> bool:
        """Đơn có HÀNG HOÁ và có PHÍ/DỊCH VỤ.

        Hai vế, không một: một đơn chỉ có phí (không mặt hàng nào) KHÔNG phải
        một lần bán kèm dịch vụ — nó là một chứng từ phí, và đếm nó vào đây sẽ
        làm tỉ lệ "bán kèm dịch vụ" cao hơn thực tế.
        """
        return (self.merchandise_lines > 0
                and bool(self.line_types & dmx.SERVICE_TYPES))


def build_index(
    details: Iterable[dict], *, product_buckets: Sequence,
    category_buckets: Sequence,
) -> dict[str, OrderBasket]:
    """`{order_key: OrderBasket}` — dựng index ĐÚNG MỘT LẦN cho cả trang.

    Ba dãy ĐI SONG SONG (`details`, `product_buckets`, `category_buckets`),
    cùng hợp đồng mà `product_metrics.group_rows` dùng và cùng lý do: lệch độ
    dài là LỖI CỨNG, vì cắt ngắn im lặng làm một số dòng biến mất khỏi mọi giỏ
    trong khi các ô đếm vẫn trông hợp lệ.

    Chỉ dòng HÀNG HOÁ góp thành viên vào `products`/`categories`. Dòng phí,
    chiết khấu, hoàn/hủy và chứng từ chưa định nghĩa vẫn góp vào `lines`,
    `line_types` và `revenue` — chúng là tiền thật và là bằng chứng thật, chỉ
    không phải mặt hàng.
    """
    details = list(details)
    if not (len(details) == len(product_buckets) == len(category_buckets)):
        raise ValueError(
            f"details ({len(details)}), product_buckets ({len(product_buckets)})"
            f" và category_buckets ({len(category_buckets)}) phải cùng độ dài")
    slots: dict[str, dict] = {}
    for detail, product, category in zip(details, product_buckets,
                                         category_buckets):
        line = detail["line"]
        slot = slots.setdefault(line.order_key, {
            "products": set(), "categories": set(), "line_types": set(),
            "lines": 0, "merchandise_lines": 0, "revenue": [],
            "product_labels": {}, "category_labels": {}})
        slot["lines"] += 1
        slot["line_types"].add(line.line_type)
        slot["revenue"].append(line.total_sales)
        if line.line_type in dmx.MERCHANDISE_TYPES:
            slot["merchandise_lines"] += 1
            slot["products"].add(product.key)
            slot["product_labels"][product.key] = product.label
            slot["categories"].add(category.key)
            slot["category_labels"][category.key] = category.label
    return {
        order_key: OrderBasket(
            order_key=order_key,
            products=frozenset(slot["products"]),
            categories=frozenset(slot["categories"]),
            line_types=frozenset(slot["line_types"]),
            lines=slot["lines"],
            merchandise_lines=slot["merchandise_lines"],
            revenue=dmx._sum_optional(slot["revenue"]),
            product_labels=dict(slot["product_labels"]),
            category_labels=dict(slot["category_labels"]))
        for order_key, slot in slots.items()
    }


@dataclass(frozen=True)
class BasketCounts:
    """Bốn ô giỏ hàng của một lát dữ liệu — xem `MULTI_METRIC_NOTE`."""

    orders: int
    multi_line_orders: int
    multi_product_orders: int
    multi_merchandise_category_orders: int
    service_attachment_orders: int

    def _rate(self, part: int) -> Optional[Decimal]:
        if self.orders == 0:
            return None
        return (Decimal(part) / Decimal(self.orders) * Decimal(100)).quantize(
            _CENT, rounding=ROUND_HALF_UP)

    @property
    def multi_line_rate(self) -> Optional[Decimal]:
        return self._rate(self.multi_line_orders)

    @property
    def multi_product_rate(self) -> Optional[Decimal]:
        return self._rate(self.multi_product_orders)

    @property
    def multi_category_rate(self) -> Optional[Decimal]:
        return self._rate(self.multi_merchandise_category_orders)

    @property
    def service_attachment_rate(self) -> Optional[Decimal]:
        return self._rate(self.service_attachment_orders)


def counts(index: dict) -> BasketCounts:
    baskets = list(index.values())
    return BasketCounts(
        orders=len(baskets),
        multi_line_orders=sum(1 for b in baskets if b.multi_line),
        multi_product_orders=sum(1 for b in baskets if b.multi_product),
        multi_merchandise_category_orders=sum(
            1 for b in baskets if b.multi_category),
        service_attachment_orders=sum(
            1 for b in baskets if b.service_attachment),
    )


@dataclass(frozen=True)
class Pair:
    """Một cặp KHÔNG CÓ THỨ TỰ, cùng hai chiều attachment của nó."""

    left: str
    right: str
    left_label: str
    right_label: str
    pair_orders: int
    orders_with_left: int
    orders_with_right: int
    pair_revenue: Optional[Decimal]
    #: Các `order_key` chứa cả hai, đã sắp — đầu vào của drill-down. Giữ khoá
    #: chứ không giữ dòng: drill-down đọc lại đúng lát dữ liệu của trang, nên
    #: nó không thể hiện một dòng mà trang đang không tính.
    order_keys: tuple = ()

    @property
    def support(self) -> int:
        """Bằng `pair_orders`. Tên thứ hai vì bảng gọi nó là "support" còn
        công thức attachment gọi nó là tử số — cùng một con số, hai cách đọc."""
        return self.pair_orders

    def _attachment(self, denominator: int) -> Optional[Decimal]:
        if denominator == 0:
            return None
        return (Decimal(self.pair_orders) / Decimal(denominator)
                * Decimal(100)).quantize(_CENT, rounding=ROUND_HALF_UP)

    @property
    def attachment_left_to_right(self) -> Optional[Decimal]:
        """"Mua LEFT thì bao nhiêu % cũng mua RIGHT" — mẫu số là đơn có LEFT."""
        return self._attachment(self.orders_with_left)

    @property
    def attachment_right_to_left(self) -> Optional[Decimal]:
        """"Mua RIGHT thì bao nhiêu % cũng mua LEFT" — mẫu số là đơn có RIGHT."""
        return self._attachment(self.orders_with_right)


def _pairs(
    index: dict, *, members_of, labels_of, min_support: int,
) -> list[Pair]:
    """Bộ khung dùng chung của cặp sản phẩm và cặp nhóm hàng.

    Viết một lần cho cả hai chiều: mỗi bản sao thứ hai của phép đếm cặp là một
    chỗ để `pair_orders` và mẫu số attachment trôi khỏi nhau.
    """
    member_orders: dict[str, int] = {}
    labels: dict[str, str] = {}
    pair_orders: dict[tuple[str, str], list[str]] = {}
    pair_revenue: dict[tuple[str, str], list] = {}
    for basket in index.values():
        members = sorted(members_of(basket))
        for member in members:
            member_orders[member] = member_orders.get(member, 0) + 1
            labels.setdefault(member, labels_of(basket).get(member, member))
        for position, left in enumerate(members):
            for right in members[position + 1:]:
                key = (left, right)
                pair_orders.setdefault(key, []).append(basket.order_key)
                pair_revenue.setdefault(key, []).append(basket.revenue)
    pairs = [
        Pair(left=left, right=right,
             left_label=labels.get(left, left),
             right_label=labels.get(right, right),
             pair_orders=len(order_keys),
             orders_with_left=member_orders.get(left, 0),
             orders_with_right=member_orders.get(right, 0),
             pair_revenue=dmx._sum_optional(pair_revenue[(left, right)]),
             order_keys=tuple(sorted(order_keys)))
        for (left, right), order_keys in pair_orders.items()
        if len(order_keys) >= min_support
    ]
    pairs.sort(key=lambda pair: (-pair.pair_orders, pair.left, pair.right))
    return pairs


def product_pairs(
    index: dict, *, min_support: int = DEFAULT_PRODUCT_MIN_SUPPORT,
) -> list[Pair]:
    """Cặp SẢN PHẨM (`product_key`), mặc định chỉ support >= 2."""
    return _pairs(index, members_of=lambda b: b.products,
                  labels_of=lambda b: b.product_labels,
                  min_support=min_support)


def category_pairs(
    index: dict, *, min_support: int = DEFAULT_CATEGORY_MIN_SUPPORT,
) -> list[Pair]:
    """Cặp NHÓM HÀNG, mặc định hiện toàn bộ nhưng luôn ghi support."""
    return _pairs(index, members_of=lambda b: b.categories,
                  labels_of=lambda b: b.category_labels,
                  min_support=min_support)


def orders_containing(index: dict, *, member: str, dimension: str) -> tuple:
    """`order_key` của các đơn chứa MỘT thành viên — đầu vào của drill-down.

    `dimension` là `"product"` hoặc `"category"`. Một giá trị khác là LỖI CỨNG
    chứ không rơi về một chiều mặc định: rơi về mặc định ở đây sẽ trả về danh
    sách đơn của một chiều KHÁC cái người dùng bấm, và trang không có cách nào
    biết để nói ra.
    """
    if dimension == "product":
        select = lambda basket: basket.products  # noqa: E731
    elif dimension == "category":
        select = lambda basket: basket.categories  # noqa: E731
    else:
        raise ValueError(f"chiều giỏ hàng ngoài tập đóng: {dimension!r}")
    return tuple(sorted(basket.order_key for basket in index.values()
                        if member in select(basket)))


def orders_with_pair(index: dict, *, left: str, right: str,
                     dimension: str) -> tuple:
    """`order_key` của các đơn chứa CẢ HAI thành viên."""
    left_orders = set(orders_containing(index, member=left,
                                        dimension=dimension))
    right_orders = set(orders_containing(index, member=right,
                                         dimension=dimension))
    return tuple(sorted(left_orders & right_orders))


__all__ = [
    "ATTACHMENT_NOTE", "BasketCounts", "DEFAULT_CATEGORY_MIN_SUPPORT",
    "DEFAULT_PRODUCT_MIN_SUPPORT", "MULTI_METRIC_NOTE", "OrderBasket",
    "PAIR_REVENUE_NOTE", "Pair", "SUPPORT_NOTE", "build_index",
    "category_pairs", "counts", "orders_containing", "orders_with_pair",
    "product_pairs",
]
