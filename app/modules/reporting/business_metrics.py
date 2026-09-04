"""PHB-03 — ngữ nghĩa nghiệp vụ đã freeze của Summary + Employee V1.

Module này THUẦN: không SQL, không Flask, không I/O. Nó nhận các dòng hàng đã
được tầng truy vấn đọc ra và trả về đúng những chỉ tiêu mà
`docs/tasks/PHB-02-business-parity-contract.md` mục 10 đã freeze. Tách ra như
vậy vì mọi vector nghiệm thu của PHB-03 (`1.000.000 / 7,5 % ≈ 13.333.333,33`
…) là mệnh đề về NGỮ NGHĨA, không phải về HTML — chúng phải kiểm được mà
không dựng database hay browser.

Sáu chỉ tiêu, mỗi cái chỉ tới đúng một quyết định Owner:

    Doanh thu bán hàng      DEC-114 — `Σ(sell_price × quantity − discount)`,
                            đọc thẳng `total_sales` mà pipeline đã ghi
    Số đơn                  M1 — `COUNT DISTINCT order_key`
    Tổng số SP              DEC-PHB02-03 — `SUM(quantity)` khi ĐƠN GIÁ BÁN
                            > 1.000.000 VND
    Lợi nhuận KPI           DEC-143 + gate 100 % của DEC-PHB02-02
    DS quy đổi              DEC-PHB02-04 (CHIA) + DEC-PHB02-05 (ma trận tỉ lệ)
    So tháng trước          DEC-PHB02-07 — % thay đổi DOANH THU BÁN HÀNG

## PROFIT_COVERAGE — vì sao tử số đúng bằng tập được cộng

`DEC-PHB02-02` §4 chỉ chấp nhận một mốc: **100 %**, và cấm phát minh ngưỡng
khác. Nhưng "100 % của cái gì" phải nói ra, nếu không con số "chính thức" vẫn
có thể bỏ sót dòng trong im lặng. Ở đây coverage được định nghĩa để KHÔNG thể
nói dối:

    PROFIT_COVERAGE = (số dòng THỰC SỰ góp một giá trị lợi nhuận KPI)
                    / (tổng số dòng hiện hành của kỳ)

Tử số đúng bằng tập dòng nằm trong tổng lợi nhuận. Vì vậy `coverage = 100 %`
tương đương "mọi dòng của kỳ đều đã có mặt trong con số này" — đó chính là
điều kiện để gọi nó là CHÍNH THỨC, không phải một cách viết khác của nó.

Một dòng góp giá trị khi CẢ HAI điều kiện đúng:

1. `status = "AUTO"` — `D1/P1` của `TASK-PRA-003` đã freeze: một dòng
   `PENDING` KHÔNG bao giờ vào tổng lợi nhuận KPI, kể cả khi nó có sẵn một
   giá trị. PHB-03 không nới điều đó; giá nhập do Owner nhập bù đúng MỘT
   input còn thiếu, nó không phải một lượt duyệt Review Queue.
2. Có giá nhập KPI phân giải được — tự động (`AUTO`) hoặc do Owner nhập
   (`MANUAL` / `MANUAL_OVERRIDE`) — cùng với `sell_price` và `quantity`.

Hai lý do "chưa đủ" vì thế được đếm RIÊNG (`missing_price_lines` và
`review_blocked_lines`): chỉ lý do thứ nhất hoàn thiện được bằng luồng nhập
tay của PHB-03; lý do thứ hai thuộc Review Queue đã có. Gộp chúng lại sẽ hứa
với Owner rằng nhập nốt giá là xong, trong khi không phải.

## DS quy đổi — chia theo TỪNG DÒNG, không bao giờ một tỉ lệ pha trộn

`R-E6`: `CONVERTED_SALES = EligibleKpiProfit ÷ rate`. Tỉ lệ thay đổi ngay
BÊN TRONG một nhân viên (một dòng Gia dụng của Vinh là 8 %, dòng Điện máy kế
bên là 2 %), nên phép chia phải xảy ra ở cấp dòng rồi mới cộng. Chia tổng lợi
nhuận cho một tỉ lệ trung bình là đúng cái sai mà `R-E6` gọi tên.

`profit × rate` là công thức SAI và không tồn tại ở bất kỳ đâu trong file này.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

# `DEC-PHB02-03` — ngưỡng GIÁ, cố ý không phải một taxonomy sản phẩm. Hệ quả
# đã được Owner chấp nhận tường minh (`FIND-PHB02-N08`): vài sản phẩm thật giá
# thấp cũng bị loại. Đó là đánh đổi có chủ đích, không phải defect.
QUALIFYING_SALE_PRICE_THRESHOLD = Decimal("1000000")

# Provenance của giá nhập KPI dùng cho báo cáo (`DEC-PHB02-02` §3).
PROVENANCE_AUTO = "AUTO"
PROVENANCE_MANUAL = "MANUAL"
PROVENANCE_MANUAL_OVERRIDE = "MANUAL_OVERRIDE"
PROVENANCE_PENDING = "PENDING"

# `R-S7`/`R-E8`: hai trạng thái, không có trạng thái thứ ba "gần đủ".
STATE_OFFICIAL = "OFFICIAL"
STATE_INCOMPLETE = "INCOMPLETE"

# Đơn vị tiền nhỏ nhất mà DS quy đổi được viết ra. `1.000.000 / 7,5 %` là một
# số thập phân vô hạn tuần hoàn; vector nghiệm thu của `DEC-PHB02-05` viết nó
# là `13.333.333,33`, nên hai chữ số thập phân là hợp đồng, không phải sở thích.
_CENT = Decimal("0.01")


@dataclass(frozen=True)
class BusinessLine:
    """Một dòng hàng hiện hành, đã hợp nhất quyết định của Owner.

    Đây là RANH GIỚI giữa tầng truy vấn và ngữ nghĩa nghiệp vụ: mọi trường ở
    đây là giá trị thuần, nên toàn bộ mục 8 của PHB-03 kiểm được bằng cách
    dựng dataclass này bằng tay.
    """

    order_key: str
    employee: Optional[str]
    employee_group: Optional[str]
    status: str
    sell_price: Optional[Decimal]
    quantity: Optional[Decimal]
    discount: Decimal
    total_sales: Optional[Decimal]
    # Giá nhập KPI do pipeline phân giải (`None` = chưa phân giải được).
    auto_purchase_price: Optional[Decimal]
    # Lợi nhuận KPI do pipeline tính, dùng NGUYÊN VẸN khi không có override.
    auto_kpi_profit: Optional[Decimal]
    # Giá nhập do Owner nhập/ghi đè, `None` = Owner chưa động vào dòng này.
    manual_purchase_price: Optional[Decimal] = None
    manual_provenance: Optional[str] = None
    # Tỉ lệ quy đổi hiệu lực của dòng (đã tính cả tick Gia dụng nếu có).
    conversion_rate: Optional[Decimal] = None

    @property
    def purchase_price(self) -> Optional[Decimal]:
        """Giá nhập KPI HIỆU LỰC: quyết định của người thắng giá trị tự động."""
        if self.manual_purchase_price is not None:
            return self.manual_purchase_price
        return self.auto_purchase_price

    @property
    def purchase_provenance(self) -> str:
        """`AUTO` | `MANUAL` | `MANUAL_OVERRIDE` | `PENDING`.

        `DEC-PHB02-02` §3 cấm âm thầm coi một override là AUTO, nên provenance
        do người nhập luôn thắng — kể cả khi giá trị nhập bằng đúng giá AUTO.
        """
        if self.manual_purchase_price is not None:
            return self.manual_provenance or PROVENANCE_MANUAL
        if self.auto_purchase_price is not None:
            return PROVENANCE_AUTO
        return PROVENANCE_PENDING

    @property
    def kpi_profit(self) -> Optional[Decimal]:
        """`EligibleKpiProfit` hiệu lực của dòng — `None` = chưa xác định.

        Không override ⟹ dùng NGUYÊN con số pipeline đã ghi. Không tính lại,
        vì `compute_eligible_kpi_profit` fail-closed khi authority
        `config/eligible_costs.yaml` hỏng (`DEC-143` §1); tính lại ở đây sẽ
        "sửa" một `None` cố ý thành một con số mà engine đã từ chối tạo ra.

        Có override ⟹ áp đúng công thức đã freeze của `DEC-143`/`OD-108B-01`
        lên giá mới (`FIND-PHB02-N06`):

            (SellPrice − KpiPurchasePrice) × Quantity − Discount

        `EligibleCosts = {}` (tập rỗng có thẩm quyền) và
        `OtherKpiAdjustment = 0` nên hai số hạng đó vắng mặt — không phải bị
        bỏ quên.
        """
        if self.status != "AUTO":
            return None  # D1/P1 — dòng cần kiểm tra không vào tổng
        if self.manual_purchase_price is None:
            return self.auto_kpi_profit
        if self.sell_price is None or self.quantity is None:
            return None
        return ((self.sell_price - self.manual_purchase_price) * self.quantity
                - self.discount)

    @property
    def qualifying_quantity(self) -> Decimal:
        """`DEC-PHB02-03` — số lượng của dòng, chỉ khi ĐƠN GIÁ > 1.000.000.

        So sánh trên `sell_price` (đơn giá), đúng cách đọc canonical đã đo ở
        mục 4.6 của hợp đồng. Ngưỡng là `>` chứ không phải `>=`: Owner viết
        "giá bán sản phẩm > 1.000.000 VND", và một dòng đúng 1.000.000 nằm ở
        phía BỊ LOẠI.
        """
        if self.sell_price is None or self.quantity is None:
            return Decimal(0)
        if self.sell_price <= QUALIFYING_SALE_PRICE_THRESHOLD:
            return Decimal(0)
        return self.quantity

    @property
    def converted_sales(self) -> Optional[Decimal]:
        """`R-E6` — lợi nhuận KPI của dòng CHIA cho tỉ lệ của chính dòng đó."""
        return converted_sales(self.kpi_profit, self.conversion_rate)

    @property
    def contributes_profit(self) -> bool:
        return self.kpi_profit is not None

    @property
    def blocked_by_missing_price(self) -> bool:
        """Dòng thiếu ĐÚNG một thứ: giá nhập. Luồng PHB-03 hoàn thiện được."""
        return self.status == "AUTO" and self.purchase_price is None

    @property
    def blocked_by_review(self) -> bool:
        """Dòng đang chờ kiểm tra — luồng nhập giá KHÔNG mở khoá được nó."""
        return self.status != "AUTO"


def converted_sales(
    profit: Optional[Decimal], rate: Optional[Decimal]
) -> Optional[Decimal]:
    """`CONVERTED_SALES = profit / rate`, làm tròn tới 0,01 VND.

    `DEC-PHB02-04` viết hoa dòng "TUYỆT ĐỐI KHÔNG implement profit * rate".
    Phép chia ở đây là toàn bộ lý do hàm này tồn tại riêng thay vì nằm inline.

    `rate = 0` trả `None` chứ không raise: một tỉ lệ 0 trong cấu hình là lỗi
    cấu hình, và một trang báo cáo không được sập vì nó — nhưng cũng không
    được in ra một con số vô nghĩa.
    """
    if profit is None or rate is None or rate == 0:
        return None
    return (Decimal(profit) / Decimal(rate)).quantize(_CENT, rounding=ROUND_HALF_UP)


def month_over_month_percent(
    current: Optional[Decimal], previous: Optional[Decimal]
) -> Optional[Decimal]:
    """`DEC-PHB02-07` — % thay đổi DOANH THU BÁN HÀNG so tháng liền trước.

    Trả `None` cho cả hai tình huống mà Owner yêu cầu xử lý tường minh: thiếu
    dữ liệu kỳ trước, và kỳ trước bằng 0. `None` ở đây nghĩa là "không có phần
    trăm nào đúng để nói" — tầng trình bày viết nó thành một trạng thái chữ,
    KHÔNG BAO GIỜ thành vô cực, `-100 %`, hay `0 %`.
    """
    if current is None or previous is None or previous == 0:
        return None
    return ((Decimal(current) - Decimal(previous)) / Decimal(previous)
            * Decimal(100)).quantize(_CENT, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class Coverage:
    """Coverage giá nhập/lợi nhuận của một tập dòng + gate 100 % của nó."""

    covered_lines: int
    total_lines: int
    missing_price_lines: int
    review_blocked_lines: int

    @property
    def is_complete(self) -> bool:
        """`DEC-PHB02-02` §4 — gate, KHÔNG phải ngưỡng.

        Một kỳ không có dòng nào KHÔNG được coi là "đủ 100 %": `0/0` là chưa
        có gì để công nhận, không phải một lời khẳng định đã đầy đủ.
        """
        return self.total_lines > 0 and self.covered_lines == self.total_lines

    @property
    def percent(self) -> Optional[Decimal]:
        """Chỉ để HIỂN THỊ. Gate luôn đọc `is_complete`, không đọc số này —
        `350/351` làm tròn ra `99,72 %`, và không phần trăm nào được phép
        đứng ra thay cho phép so bằng."""
        if self.total_lines == 0:
            return None
        return (Decimal(self.covered_lines) / Decimal(self.total_lines)
                * Decimal(100)).quantize(_CENT, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class BusinessTotals:
    """Bộ chỉ tiêu nghiệp vụ của MỘT phạm vi (cả kỳ, hoặc một nhân viên)."""

    lines: int
    orders: int
    sales_revenue: Optional[Decimal]
    qualifying_quantity: Decimal
    kpi_profit: Optional[Decimal]
    converted_sales: Optional[Decimal]
    coverage: Coverage

    @property
    def state(self) -> str:
        return STATE_OFFICIAL if self.coverage.is_complete else STATE_INCOMPLETE

    @property
    def official_kpi_profit(self) -> Optional[Decimal]:
        """`R-S7` — lợi nhuận KPI CHÍNH THỨC, hoặc `None`.

        Dưới 100 % coverage hàm này trả `None` để không có đường nào trình bày
        một kết quả một phần như số chính thức. Con số một phần vẫn tồn tại ở
        `kpi_profit` và tầng trình bày dán nhãn CHƯA HOÀN CHỈNH lên nó.
        """
        return self.kpi_profit if self.coverage.is_complete else None

    @property
    def official_converted_sales(self) -> Optional[Decimal]:
        """`R-E8` — DS quy đổi chỉ chính thức khi lợi nhuận nền đã đủ."""
        return self.converted_sales if self.coverage.is_complete else None


def _sum(values) -> Optional[Decimal]:
    """Tổng của các giá trị KHÔNG `None`; tập rỗng ⟹ `None`, không phải `0`.

    Đây là cùng kỷ luật `NULL ≠ 0` mà `analytics_queries` đã freeze: "chưa có
    giá trị nào" và "bằng không" là hai câu khác nhau, và chỉ một trong hai
    cho phép Owner ra quyết định.
    """
    present = [Decimal(value) for value in values if value is not None]
    return sum(present, Decimal(0)) if present else None


def totals(lines: list[BusinessLine]) -> BusinessTotals:
    """Gộp một tập dòng thành bộ chỉ tiêu nghiệp vụ.

    `orders` đếm `COUNT DISTINCT order_key` TRONG tập được truyền vào (M1).
    Khi tập là các dòng của một nhân viên, một đơn có hai nhân viên vì thế
    được đếm ở cả hai — đúng sự thật nghiệp vụ `R-E5`, và trang phải nói ra
    điều đó thay vì giấu đi.
    """
    return BusinessTotals(
        lines=len(lines),
        orders=len({line.order_key for line in lines}),
        sales_revenue=_sum(line.total_sales for line in lines),
        qualifying_quantity=sum(
            (line.qualifying_quantity for line in lines), Decimal(0)),
        kpi_profit=_sum(line.kpi_profit for line in lines),
        converted_sales=_sum(line.converted_sales for line in lines),
        coverage=Coverage(
            covered_lines=sum(1 for line in lines if line.contributes_profit),
            total_lines=len(lines),
            missing_price_lines=sum(
                1 for line in lines if line.blocked_by_missing_price),
            review_blocked_lines=sum(
                1 for line in lines if line.blocked_by_review),
        ),
    )




def group_by_employee(
    lines: list[BusinessLine],
) -> list[tuple[Optional[str], Optional[str], BusinessTotals]]:
    """Phân hoạch theo `(nhân viên, nhóm)`, sắp theo doanh thu giảm dần.

    Đây là một PHÂN HOẠCH của cùng tập dòng, nên mọi chỉ tiêu cộng được (doanh
    thu, số lượng đủ điều kiện, lợi nhuận, DS quy đổi, coverage) cộng lại đúng
    bằng tổng kỳ. Cột `orders` thì KHÔNG — một đơn có hai nhân viên được đếm ở
    cả hai dòng. Đó là sự thật nghiệp vụ `R-E5`, và trang phải nói ra nó thay
    vì che đi bằng một phép đếm sai.

    Nhân viên chưa map (`employee is None`) KHÔNG bị bỏ im lặng (`R-E4`) — họ
    là một dòng như mọi người khác, và luôn nằm CUỐI bảng.
    """
    buckets: dict[tuple[Optional[str], Optional[str]], list[BusinessLine]] = {}
    for line in lines:
        buckets.setdefault((line.employee, line.employee_group), []).append(line)
    grouped = [(name, group, totals(bucket))
               for (name, group), bucket in buckets.items()]
    grouped.sort(key=lambda item: (
        item[0] is None,
        -(item[2].sales_revenue or Decimal(0)),
        item[0] or "",
    ))
    return grouped


def for_employee(
    lines: list[BusinessLine], employee: Optional[str]
) -> list[BusinessLine]:
    """Các dòng của MỘT nhân viên. `None` = nhóm "chưa xác định nhân viên"."""
    return [line for line in lines if line.employee == employee]


__all__ = [
    "BusinessLine", "BusinessTotals", "Coverage",
    "PROVENANCE_AUTO", "PROVENANCE_MANUAL", "PROVENANCE_MANUAL_OVERRIDE",
    "PROVENANCE_PENDING", "QUALIFYING_SALE_PRICE_THRESHOLD",
    "STATE_INCOMPLETE", "STATE_OFFICIAL",
    "converted_sales", "for_employee", "group_by_employee",
    "month_over_month_percent", "totals",
]
