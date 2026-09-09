"""R6 §1 — AGGREGATE NỀN của dashboard phân tích kinh doanh.

Module này THUẦN: không SQL, không Flask, không đọc file, không migration,
không warehouse, không materialized view, không API ngoài. Đầu vào là
`PeriodData.details` — tức các dòng ĐANG ĐƯỢC BÁO CÁO, đã hợp nhất mọi quyết
định của Owner và đã TRỪ những dòng bị loại/tạm loại (`business_service.
PeriodData`). Đầu ra là giá trị thuần, nên mọi mệnh đề dưới đây kiểm được
bằng một test đơn vị dựng dataclass bằng tay.

## Vì sao đọc `details` chứ không đọc lại database

`PeriodData` là "effective data" duy nhất của vertical này: override giá nhập,
gán lại nhân viên, tick Gia dụng, dòng Owner loại, dòng tạm loại vì không còn
trong sổ đã xác nhận đầy đủ — tất cả đã được giải xong TRƯỚC khi tới đây. Một
câu SQL thứ hai cho dashboard sẽ đi vòng qua đúng những lớp phủ đó, và cách
lỗi ấy biểu hiện là một trang phân tích cộng đúng số tiền mà trang Báo cáo
vừa trừ ra — không màn hình nào cảnh báo, vì cả hai đều "đúng" theo nguồn của
chính nó.

## Ba chỉ tiêu KHÔNG được lẫn với nhau

```text
BusinessTotals.qualifying_quantity   SL của dòng có ĐƠN GIÁ > 1.000.000
                                     (DEC-PHB02-03 — mẫu số KPI/quy đổi)
DashboardTotals.total_quantity       SL của MỌI dòng có SL
DashboardTotals.lines_missing_quantity   số dòng KHÔNG có SL
```

`qualifying_quantity` KHÔNG bị đổi nghĩa và KHÔNG bị thay thế — R6 thêm một
chỉ tiêu thứ hai bên cạnh nó. Nếu R6 dùng lại `qualifying_quantity` làm "tổng
số lượng bán", con số trên dashboard sẽ nhỏ hơn số lượng thật đúng bằng phần
hàng dưới một triệu, và không ai đi tìm số lượng mình không biết là mình đang
thiếu.

## Doanh thu và chiết khấu — mỗi thứ đọc đúng một trường, đúng một lần

```text
sales_revenue           Σ BusinessLine.total_sales   (= BusinessTotals.sales_revenue)
discount_total          Σ BusinessLine.discount
gross_before_discount   sales_revenue + discount_total   (DẪN XUẤT, chỉ đối soát)
```

`total_sales` là doanh thu SAU chiết khấu mà pipeline đã ghi (`DEC-114`:
`SellPrice × Quantity − Discount`). R6 KHÔNG tính lại nó từ `sell_price ×
quantity − discount`: một phép tính thứ hai sẽ trôi khỏi phép tính thứ nhất ở
đúng những dòng khó nhất (thiếu SL, thiếu đơn giá, chiết khấu ghi thành dòng
riêng) và cho ra hai con số doanh thu trong cùng một sản phẩm.

`gross_before_discount` là DẪN XUẤT và chỉ tồn tại để đối soát với cột
"Doanh số bán" của sổ kế toán. Nó KHÔNG phải một định nghĩa doanh thu thứ
hai: không bảng nào, không biểu đồ nào, không bucket nào của R6 cộng theo nó,
và `None` khi `sales_revenue` là `None` — cộng một chiết khấu vào một doanh
thu chưa biết không cho ra một doanh số.

`discount` được cộng ĐÚNG MỘT LẦN, ở cấp DÒNG. Nguy cơ trừ hai lần (chiết
khấu vừa ghi thành cột vừa ghi thành dòng riêng) KHÔNG được xử lý ở đây bằng
một luật mới — nó đã có bề mặt riêng từ R3 (`business_metrics.
discount_double_count_orders`, `PeriodData.discount_double_count`), và R6 chở
đúng cảnh báo đó lên màn hình thay vì tự phát minh một cách khử trùng lặp.

## Một đơn thuộc ĐÚNG MỘT mốc thời gian

Một `order_key` có thể có nhiều dòng ở nhiều ngày. Nếu đếm đơn theo từng dòng,
tổng số đơn của biểu đồ sẽ LỚN HƠN tổng số đơn của kỳ, và một biểu đồ vượt
tổng của chính nó là một biểu đồ không dùng được để ra quyết định.

Quy tắc: một đơn được gán vào NGÀY NHỎ NHẤT trong các dòng HIỆU LỰC của nó.
Ngày nhỏ nhất chứ không phải ngày lớn nhất, vì một đơn được ghi nhận từ lúc
nó phát sinh. Bất biến kiểm được, và `orders_by_bucket` giữ nó ở MỌI mức gộp:

    Σ(số đơn của mọi mốc)  +  orders_without_date  ==  DashboardTotals.orders

Các đơn có dòng ở nhiều ngày KHÔNG bị bỏ đi và KHÔNG bị chia đôi — chúng được
ĐẾM RIÊNG ở `orders_with_multiple_sale_dates` để trang nói ra rằng con số theo
thời gian của chúng là một quy ước, không phải một phép đo.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Iterable, Optional

from app.modules.reporting import line_type as line_type_module

#: Hai chữ số thập phân — cùng đơn vị nhỏ nhất mà `business_metrics` đã freeze
#: cho DS quy đổi và phần trăm, để hai trang không làm tròn khác nhau.
_CENT = Decimal("0.01")

#: Loại dòng mang HÀNG HOÁ. Viết MỘT LẦN ở đây và tham chiếu từ mọi nơi của
#: R6: đây là ranh giới quyết định `multi_product_orders`,
#: `multi_merchandise_category_orders` và giá bán bình quân, nên một bản sao
#: thứ hai của danh sách này là một nguồn drift trực tiếp vào ba chỉ tiêu.
#:
#: `FEE`/`DISCOUNT` ngoài tập vì chúng không phải mặt hàng (`OD-105B-01` §3);
#: `RETURN_CANCEL`/`UNDECIDED_DOCUMENT` ngoài tập vì hệ thống chưa có thẩm
#: quyền nói chúng là gì (`OD-2`, `line_type.UNDECIDED_TYPES`) — và đoán rằng
#: một chứng từ chưa định nghĩa là hàng hoá là đúng việc `OD-2` cấm.
MERCHANDISE_TYPES: frozenset = frozenset({
    line_type_module.TYPE_SALE, line_type_module.TYPE_ACCESSORY_GIFT,
})

#: Loại dòng là DỊCH VỤ/PHÍ — vế thứ hai của `service_attachment_orders`.
SERVICE_TYPES: frozenset = frozenset({line_type_module.TYPE_FEE})

MULTI_DATE_NOTE = (
    "Một đơn có dòng bán ở nhiều ngày được gán vào NGÀY NHỎ NHẤT trong các "
    "dòng hiệu lực của nó, và chỉ được đếm ĐÚNG MỘT LẦN trên biểu đồ. Ô "
    "\"đơn có nhiều ngày bán\" đếm riêng những đơn như vậy để con số theo thời "
    "gian của chúng đọc được là một quy ước, không phải một phép đo."
)

GROSS_DERIVED_NOTE = (
    "\"Doanh số bán\" là con số DẪN XUẤT = doanh thu sau CK + chiết khấu, và "
    "chỉ dùng để đối soát với cột cùng tên trên sổ kế toán. Không bảng, biểu "
    "đồ hay bucket nào của trang này cộng theo nó — mọi chỉ tiêu tiền đều đọc "
    "doanh thu sau CK."
)

QUANTITY_NOTE = (
    "\"Tổng SL\" đếm số lượng của MỌI dòng có số lượng. Nó KHÁC \"SL tính KPI\" "
    "trên trang Báo cáo — ô đó chỉ đếm dòng có đơn giá trên 1.000.000 đồng "
    "theo DEC-PHB02-03, và hai con số trả lời hai câu hỏi khác nhau."
)


def sum_optional(values) -> Optional[Decimal]:
    """Tổng của các giá trị KHÔNG `None`; tập rỗng ⟹ `None`, không phải `0`.

    Cùng kỷ luật `NULL ≠ 0` mà `business_metrics._sum` và
    `brand_metrics._sum_optional` đã freeze. Viết lại ở đây vì cả hai hàm kia
    là chi tiết cài đặt private của module khác, và một `import` xuyên qua dấu
    gạch dưới là một phụ thuộc mà không ai thấy khi sửa module bên kia.

    CÔNG KHAI (không gạch dưới) vì `product_metrics` và `basket_metrics` gọi
    nó: nếu nó private, hai module ấy sẽ phải làm đúng cái việc mà đoạn trên
    vừa nói là không nên làm.
    """
    present = [Decimal(value) for value in values if value is not None]
    return sum(present, Decimal(0)) if present else None


def _ratio(numerator: Optional[Decimal], denominator: int) -> Optional[Decimal]:
    """`numerator / denominator` làm tròn 2 chữ số, hoặc `None`.

    `None` ở tử số và `0` ở mẫu số cho ra cùng một kết quả `None`, và cả hai
    đều là "chưa nói được" chứ không phải "bằng không": một kỳ chưa có đơn nào
    không có "doanh thu trên mỗi đơn" bằng 0.
    """
    if numerator is None or denominator == 0:
        return None
    return (Decimal(numerator) / Decimal(denominator)).quantize(
        _CENT, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class OrderFacts:
    """Sự thật CỘNG ĐƯỢC của MỘT đơn, gộp từ các dòng hiệu lực của nó.

    Đây là đơn vị trung gian duy nhất của R6 ở cấp đơn, và mọi chỉ tiêu cấp
    đơn (số đơn theo thời gian, đơn nhiều dòng, đơn có doanh thu dương, giỏ
    hàng) đọc lại từ đây thay vì tự gom `details` một lần nữa. Gom hai lần là
    cách hai chỉ tiêu cùng trang đếm hai tập đơn khác nhau.
    """

    order_key: str
    lines: int
    revenue: Optional[Decimal]
    discount: Decimal
    quantity: Decimal
    #: Các ngày bán KHÁC NHAU trong các dòng hiệu lực của đơn. Rỗng = không
    #: dòng nào của đơn có ngày bán.
    sale_dates: frozenset
    #: Số dòng mang hàng hoá (`MERCHANDISE_TYPES`).
    merchandise_lines: int
    #: Các loại dòng có mặt trong đơn — để trả lời câu "đơn này có phí/dịch vụ
    #: kèm theo hay không" mà không phải giữ lại toàn bộ dòng.
    line_types: frozenset

    @property
    def bucket_date(self) -> Optional[date]:
        """NGÀY NHỎ NHẤT trong các dòng hiệu lực — mốc thời gian của đơn.

        `None` khi không dòng nào có ngày bán; đơn ấy không rơi vào mốc nào,
        đúng như những dòng thiếu ngày bán đã không rơi vào kỳ nào (`R-S5`).
        """
        return min(self.sale_dates) if self.sale_dates else None

    @property
    def multi_line(self) -> bool:
        return self.lines >= 2

    @property
    def multi_date(self) -> bool:
        return len(self.sale_dates) >= 2

    @property
    def positive_revenue(self) -> bool:
        """Doanh thu sau CK của đơn LỚN HƠN 0.

        `None` (chưa biết doanh thu) KHÔNG được coi là dương: một đơn chưa
        tính được doanh thu chưa chứng minh được điều gì, và đếm nó vào nhóm
        "có doanh thu dương" là một lời khẳng định chưa có bằng chứng.
        """
        return self.revenue is not None and self.revenue > 0

    @property
    def has_service(self) -> bool:
        return bool(self.line_types & SERVICE_TYPES)


def order_facts(details: Iterable[dict]) -> dict[str, OrderFacts]:
    """`{order_key: OrderFacts}` của một lát dữ liệu, gom ĐÚNG một lần.

    Thứ tự khoá là thứ tự XUẤT HIỆN đầu tiên trong `details` (dict giữ thứ tự
    chèn từ Python 3.7), nên hai lần gọi trên cùng một lát cho ra cùng một thứ
    tự — điều kiện để mọi bảng/cặp sinh ra bên trên nó sắp xếp ổn định.
    """
    facts: dict[str, dict] = {}
    for detail in details:
        line = detail["line"]
        slot = facts.setdefault(line.order_key, {
            "lines": 0, "revenue": [], "discount": Decimal(0),
            "quantity": Decimal(0), "sale_dates": set(),
            "merchandise_lines": 0, "line_types": set()})
        slot["lines"] += 1
        slot["revenue"].append(line.total_sales)
        slot["discount"] += Decimal(line.discount)
        if line.quantity is not None:
            slot["quantity"] += Decimal(line.quantity)
        sale_date = detail.get("sale_date")
        if sale_date is not None:
            slot["sale_dates"].add(sale_date)
        slot["line_types"].add(line.line_type)
        if line.line_type in MERCHANDISE_TYPES:
            slot["merchandise_lines"] += 1
    return {
        order_key: OrderFacts(
            order_key=order_key, lines=slot["lines"],
            revenue=sum_optional(slot["revenue"]), discount=slot["discount"],
            quantity=slot["quantity"],
            sale_dates=frozenset(slot["sale_dates"]),
            merchandise_lines=slot["merchandise_lines"],
            line_types=frozenset(slot["line_types"]))
        for order_key, slot in facts.items()
    }


@dataclass(frozen=True)
class DashboardTotals:
    """Bộ chỉ tiêu nền của MỘT lát dữ liệu.

    Mọi trường ở đây được tính TRỰC TIẾP từ chính lát dữ liệu được truyền vào,
    KHÔNG cộng lại từ các hàng của một bảng đang hiển thị. Đó là điều kiện để
    hàng TỔNG của mọi bảng R6 vẫn đúng khi bảng đó lọc, phân trang, hay chỉ
    hiện các bucket có support ≥ 2 — một hàng tổng cộng từ các hàng hiển thị
    sẽ tụt xuống theo đúng những dòng vừa bị ẩn, và không ai thấy.
    """

    lines: int
    orders: int
    sales_revenue: Optional[Decimal]
    discount_total: Decimal
    total_quantity: Decimal
    positive_revenue_orders: int
    multi_line_orders: int
    orders_with_multiple_sale_dates: int
    orders_without_date: int
    undated_lines: int
    lines_missing_revenue: int
    lines_missing_quantity: int

    @property
    def gross_before_discount(self) -> Optional[Decimal]:
        """DẪN XUẤT — chỉ để đối soát với cột "Doanh số bán" của sổ kế toán.

        Xem `GROSS_DERIVED_NOTE`. `None` khi chưa biết doanh thu sau CK.
        """
        if self.sales_revenue is None:
            return None
        return self.sales_revenue + self.discount_total

    @property
    def lines_per_order(self) -> Optional[Decimal]:
        return _ratio(Decimal(self.lines), self.orders)

    @property
    def revenue_per_order(self) -> Optional[Decimal]:
        """Doanh thu sau CK chia cho TỔNG số đơn của lát.

        Mẫu số là mọi đơn, KHÔNG phải riêng các đơn có doanh thu dương: đổi
        mẫu số sẽ làm con số này lớn hơn thực tế đúng bằng phần đơn chưa có
        doanh thu, và trang không có chỗ nào nói ra sự thay đổi ấy. Số đơn có
        doanh thu dương đứng riêng ở `positive_revenue_orders` để đọc cạnh nó.
        """
        return _ratio(self.sales_revenue, self.orders)


def totals(details: Iterable[dict]) -> DashboardTotals:
    """Gộp một lát dữ liệu thành `DashboardTotals`. Lát rỗng cho ra 0/`None`."""
    details = list(details)
    facts = order_facts(details)
    lines = [detail["line"] for detail in details]
    return DashboardTotals(
        lines=len(lines),
        orders=len(facts),
        sales_revenue=sum_optional(line.total_sales for line in lines),
        discount_total=sum((Decimal(line.discount) for line in lines),
                           Decimal(0)),
        total_quantity=sum((Decimal(line.quantity) for line in lines
                            if line.quantity is not None), Decimal(0)),
        positive_revenue_orders=sum(
            1 for fact in facts.values() if fact.positive_revenue),
        multi_line_orders=sum(1 for fact in facts.values() if fact.multi_line),
        orders_with_multiple_sale_dates=sum(
            1 for fact in facts.values() if fact.multi_date),
        orders_without_date=sum(
            1 for fact in facts.values() if fact.bucket_date is None),
        undated_lines=sum(1 for detail in details
                          if detail.get("sale_date") is None),
        lines_missing_revenue=sum(1 for line in lines
                                  if line.total_sales is None),
        lines_missing_quantity=sum(1 for line in lines if line.quantity is None),
    )


def orders_by_bucket(
    details: Iterable[dict], *, bucket_of, granularity: str,
) -> dict[str, dict]:
    """`{khoá mốc: {"label", "orders", "order_keys"}}` — đơn theo thời gian.

    `bucket_of` được TRUYỀN VÀO chứ không import: engine thời gian của dự án
    là `app.web.revenue_timeline`, và nó nằm ở tầng web. Nhận nó làm tham số
    giữ module này thuần VÀ — quan trọng hơn — bảo đảm bằng cấu tạo rằng R6
    không dựng một engine thời gian thứ hai: nếu ai đó muốn đổi cách chia mốc,
    họ phải sửa `revenue_timeline`, và diff sẽ cho thấy điều đó.

    Đơn không có ngày bán nào KHÔNG rơi vào mốc nào — `DashboardTotals.
    orders_without_date` đếm chúng, và bất biến ở đầu file giữ hai con số ăn
    khớp.
    """
    buckets: dict[str, dict] = {}
    for fact in order_facts(details).values():
        bucket_date = fact.bucket_date
        if bucket_date is None:
            continue
        key, label = bucket_of(bucket_date, granularity)
        slot = buckets.setdefault(key, {"label": label, "orders": 0,
                                        "order_keys": []})
        slot["orders"] += 1
        slot["order_keys"].append(fact.order_key)
    for slot in buckets.values():
        slot["order_keys"] = tuple(sorted(slot["order_keys"]))
    return buckets


@dataclass(frozen=True)
class TotalsReconciliation:
    """Đối soát `DashboardTotals` với `BusinessTotals` của CÙNG lát dữ liệu.

    Bốn cờ riêng biệt thay vì một cờ gộp, cùng lý do mà
    `brand_metrics.BrandReconciliation` đã ghi: khi một cột lệch, người đọc
    cần biết ĐÚNG cột nào.

    Đây là phép kiểm rằng R6 KHÔNG dựng một định nghĩa doanh thu/số đơn/số
    dòng thứ hai: nếu `dashboard_metrics` và `business_metrics` cho hai con số
    khác nhau trên cùng một lát, một trong hai đang tính sai và trang phải nói
    ra ngay.
    """

    lines: bool
    orders: bool
    sales_revenue: bool
    #: `qualifying_quantity` KHÔNG có mặt: nó là một chỉ tiêu KHÁC
    #: `total_quantity` (xem đầu file), nên so hai con số ấy với nhau là so
    #: hai câu hỏi khác nhau và sẽ luôn "lệch" trên dữ liệu thật.
    quantity_is_separate_metric: bool = True

    @property
    def is_exact(self) -> bool:
        return all((self.lines, self.orders, self.sales_revenue))


def reconciliation(dashboard: DashboardTotals, business) -> TotalsReconciliation:
    """So ba chỉ tiêu mà HAI module cùng tính, trên cùng một lát dữ liệu."""
    return TotalsReconciliation(
        lines=dashboard.lines == business.lines,
        orders=dashboard.orders == business.orders,
        sales_revenue=dashboard.sales_revenue == business.sales_revenue,
    )


__all__ = [
    "DashboardTotals", "GROSS_DERIVED_NOTE", "MERCHANDISE_TYPES",
    "MULTI_DATE_NOTE", "OrderFacts", "QUANTITY_NOTE", "SERVICE_TYPES",
    "TotalsReconciliation", "order_facts", "orders_by_bucket",
    "sum_optional",
    "reconciliation", "totals",
]
