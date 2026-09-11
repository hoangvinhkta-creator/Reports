"""R4 — ngữ nghĩa của BÁO CÁO ĐÁNH GIÁ tháng.

Module này THUẦN: không SQL, không Flask, không I/O, không đọc file cấu hình.
Nó nhận các dòng hàng ĐÃ HỢP NHẤT của R3 (`business_metrics.BusinessLine`) và
các bản ghi hiển thị đi kèm (`business_queries.line_details`), rồi trả lời bốn
câu hỏi của một kỳ đánh giá:

    1. Kết quả bán hàng kỳ này ra sao?          `headline`
    2. Đạt bao nhiêu phần target, còn thiếu gì?  `target_progress`, `run_rate`
    3. Phần nào tạo ra kết quả đó?               `by_product`, `discounts`, …
    4. Dữ liệu đã đủ để kết luận chưa?           (tầng trên đọc `Coverage`)

## R4 KHÔNG tính lại bất cứ con số nào của R1–R3

Đây là ràng buộc quan trọng nhất của file này, và nó được giữ bằng cấu tạo chứ
không bằng lời hứa: mọi chỉ tiêu CỘNG ĐƯỢC ở đây đều đi qua
`business_metrics.totals`, mọi phép chia target đi qua
`business_metrics.vs_target_percent`, và mọi phép so tháng đi qua
`business_metrics.month_over_month_percent`. Không có công thức MIN, không có
resolver sản phẩm, không có phép trừ chiết khấu thứ hai.

Ba chỉ tiêu DẪN XUẤT mà R4 thêm (`Doanh thu/đơn`, `Biên KPI`, `Lãi/đơn`) là ba
phép CHIA hai con số đã có, và cả ba nằm ở một chỗ duy nhất (`_ratio`) để
không nơi nào tự viết lại một phép chia có mẫu số bằng 0.

## `None` là một câu trả lời, không phải một con số chưa điền

Toàn bộ file này giữ đúng kỷ luật đã freeze từ PHB-02: "chưa xác định" KHÁC
"bằng không". Một chỉ tiêu không có số luôn đi kèm MỘT MÃ LÝ DO thuộc tập
đóng, và tầng trình bày biến mã đó thành một câu tiếng Việt — không bao giờ
thành `0`, `0 %`, vô cực hay `-100 %`.

## Lợi nhuận CHƯA CHÍNH THỨC không được lên đầu trang

`R-S7`/`R-E8` đã freeze rằng lợi nhuận KPI và DS quy đổi chỉ CHÍNH THỨC khi
coverage đạt 100 %. R4 áp thêm đúng một hệ quả, và đó là hệ quả mà brief gọi
tên: ba chỉ tiêu dẫn xuất từ lợi nhuận (Biên KPI, Lãi/đơn, và cả % target)
KHÔNG được tính từ con số một phần. Lấy tổng phần đã biết chia cho doanh thu
CẢ KỲ cho ra một biên thấp giả tạo, và nó trông giống hệt một biên thật.

Vì vậy `headline` đọc `official_kpi_profit`/`official_converted_sales` chứ
không đọc `kpi_profit`/`converted_sales`. Con số một phần KHÔNG bị giấu — nó
đi kèm trong `partial_value` để màn hình nói được "đã tính được bao nhiêu trên
bao nhiêu dòng" — nhưng nó không bao giờ là `value`.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Sequence

from app.modules.reporting import business_metrics as bm
from app.modules.reporting import line_type as line_type_module

_CENT = Decimal("0.01")
#: Tiền VND làm tròn tới ĐỒNG. `Doanh thu/đơn` và `Lãi/đơn` là tiền, không
#: phải tỉ lệ — viết chúng với hai chữ số thập phân sẽ gợi ý một độ chính xác
#: mà sổ kế toán không có.
_DONG = Decimal("1")


# --------------------------------------------------------------------------
# Mã lý do — tập ĐÓNG. Mỗi mã dẫn tới một câu khác nhau và một việc khác nhau.
# --------------------------------------------------------------------------

REASON_NO_LINES = "NO_LINES"
"""Phạm vi đang xem chưa có dòng hàng nào."""

REASON_NO_ORDERS = "NO_ORDERS"
"""Mẫu số `số đơn` bằng 0 — không chia được."""

REASON_NO_REVENUE = "NO_REVENUE"
"""Mẫu số `doanh thu` chưa xác định hoặc bằng 0 — không chia được."""

REASON_PROFIT_NOT_OFFICIAL = "PROFIT_NOT_OFFICIAL"
"""Coverage giá/LN chưa đạt 100 % — lợi nhuận KPI chưa CHÍNH THỨC."""

REASON_CONVERTED_NOT_OFFICIAL = "CONVERTED_NOT_OFFICIAL"
"""DS quy đổi chưa CHÍNH THỨC (nền lợi nhuận chưa đủ, hoặc tỉ lệ chưa cho)."""

#: Thứ tự cố định để màn hình không đổi thứ tự giữa hai lần tải trang.
KPI_REASONS = (
    REASON_NO_LINES, REASON_NO_ORDERS, REASON_NO_REVENUE,
    REASON_PROFIT_NOT_OFFICIAL, REASON_CONVERTED_NOT_OFFICIAL,
)


# --- Lý do RIÊNG của "So target" -----------------------------------------
#
# Ba mã của `business_metrics` được GIỮ NGUYÊN, không gộp và không đổi nghĩa
# (`TARGET_UNSET` · `TARGET_ZERO` · `TARGET_NO_ACTUAL`). R4 thêm ĐÚNG MỘT mã,
# và nó không lấy chỗ của mã nào:

TARGET_ACTUAL_NOT_OFFICIAL = "TARGET_ACTUAL_NOT_OFFICIAL"
"""Có target, và có DS quy đổi MỘT PHẦN — nhưng phần đó chưa chính thức.

Tách khỏi `TARGET_NO_ACTUAL` vì hai tình huống dẫn tới hai việc khác nhau:
`TARGET_NO_ACTUAL` là "chưa bán được gì / chưa tính ra đồng nào", còn mã này
là "đã bán, đã tính được một phần, nhưng còn dòng thiếu giá nên chưa được
phép công bố". Gộp chúng lại sẽ nói với Owner rằng chưa có doanh số, trong
khi việc phải làm là đi nhập nốt mấy dòng giá.
"""

TARGET_NO_DAYS_REMAINING = "TARGET_NO_DAYS_REMAINING"
"""Không còn ngày nào sau ngày đang xét — không có "cần đạt mỗi ngày".

Đây là nhánh thay cho một phép chia cho 0. Nó KHÔNG có nghĩa là đã đạt: đã
đạt hay chưa nằm ở `achieved`, và hai câu đó độc lập với nhau.
"""

TARGET_REASONS = (
    bm.TARGET_UNSET, bm.TARGET_ZERO, bm.TARGET_NO_ACTUAL,
    TARGET_ACTUAL_NOT_OFFICIAL, TARGET_NO_DAYS_REMAINING,
)


# --- Lý do RIÊNG của phép so kỳ trước ------------------------------------

COMPARE_NO_PERIOD = "COMPARE_NO_PERIOD"
"""Đang xem "Toàn bộ dữ liệu" — không có kỳ liền trước để so."""

COMPARE_PREVIOUS_NO_LINES = "COMPARE_PREVIOUS_NO_LINES"
"""Kỳ trước (trong cùng phạm vi ngày) không có dòng nào."""

COMPARE_PREVIOUS_ZERO = "COMPARE_PREVIOUS_ZERO"
"""Kỳ trước có dòng nhưng doanh thu bằng 0 — không có tỉ lệ nào đúng để nói."""

COMPARE_CURRENT_NO_REVENUE = "COMPARE_CURRENT_NO_REVENUE"
"""Kỳ NÀY chưa có doanh thu nào trong khoảng ngày đang so.

Tách khỏi ba mã trên vì vế thiếu là vế KHÁC: ba mã kia nói kỳ trước không
dùng làm mốc được, mã này nói chính kỳ đang xem chưa có gì để đem đi so. Gộp
chúng lại sẽ chỉ Owner đi kiểm tra sai tháng."""

COMPARE_REASONS = (
    COMPARE_NO_PERIOD, COMPARE_PREVIOUS_NO_LINES, COMPARE_PREVIOUS_ZERO,
    COMPARE_CURRENT_NO_REVENUE,
)


# --- Lý do RIÊNG của run-rate --------------------------------------------

RUNRATE_NO_ELAPSED_DAYS = "RUNRATE_NO_ELAPSED_DAYS"
"""Chưa có ngày nào trôi qua trong kỳ — không có tốc độ để nhân lên."""

RUNRATE_NO_DAILY_DATA = "RUNRATE_NO_DAILY_DATA"
"""Không có dòng nào mang ngày bán — không đo được tốc độ theo ngày."""

RUNRATE_NOT_RUNNING = "RUNRATE_NOT_RUNNING"
"""Kỳ đã kết thúc — không còn gì để ước tính, con số thật đã có."""

RUNRATE_VALUE_NOT_OFFICIAL = "RUNRATE_VALUE_NOT_OFFICIAL"
"""Chỉ tiêu nền chưa chính thức — không ước tính từ một con số một phần."""

RUNRATE_REASONS = (
    RUNRATE_NO_ELAPSED_DAYS, RUNRATE_NO_DAILY_DATA, RUNRATE_NOT_RUNNING,
    RUNRATE_VALUE_NOT_OFFICIAL,
)


# --------------------------------------------------------------------------
# Đơn vị — nói ra ở tầng ngữ nghĩa, không để tầng trình bày tự đoán.
# --------------------------------------------------------------------------

UNIT_VND = "VND"
UNIT_COUNT = "COUNT"
UNIT_PERCENT = "PERCENT"


# --------------------------------------------------------------------------
# Ba phép chia — MỘT chỗ duy nhất.
# --------------------------------------------------------------------------

def _ratio(
    numerator: Optional[Decimal], denominator: Optional[Decimal], *,
    quantum: Decimal, factor: Decimal = Decimal(1),
) -> Optional[Decimal]:
    """`numerator / denominator × factor`, hoặc `None`.

    `None` cho cả ba nhánh không chia được, và không nhánh nào ra `0`: tử số
    chưa xác định, mẫu số chưa xác định, mẫu số bằng 0. Đây là chỗ DUY NHẤT
    của R4 có một dấu chia, nên không có nơi thứ hai để quên một nhánh.
    """
    if numerator is None or denominator is None or denominator == 0:
        return None
    return (Decimal(numerator) / Decimal(denominator) * factor).quantize(
        quantum, rounding=ROUND_HALF_UP)


def revenue_per_order(
    sales_revenue: Optional[Decimal], orders: int
) -> Optional[Decimal]:
    """`Doanh thu / Số đơn` — VND, làm tròn tới đồng. `None` khi không chia được."""
    return _ratio(sales_revenue, Decimal(orders), quantum=_DONG)


def profit_per_order(
    official_profit: Optional[Decimal], orders: int
) -> Optional[Decimal]:
    """`Lợi nhuận KPI CHÍNH THỨC / Số đơn` — VND.

    Tử số BẮT BUỘC là con số chính thức. Truyền vào tổng một phần sẽ cho ra
    một "lãi/đơn" thấp hơn sự thật mà không có gì trên màn hình nói tại sao.
    """
    return _ratio(official_profit, Decimal(orders), quantum=_DONG)


def margin_percent(
    official_profit: Optional[Decimal], sales_revenue: Optional[Decimal]
) -> Optional[Decimal]:
    """`Biên KPI % = Lợi nhuận KPI CHÍNH THỨC / Doanh thu × 100`.

    Không cap, không kẹp về 0: một biên âm là một sự thật kế toán và giấu nó
    đi là nói dối về chính con số đang nằm trong tổng.
    """
    return _ratio(official_profit, sales_revenue,
                  quantum=_CENT, factor=Decimal(100))


# --------------------------------------------------------------------------
# Bộ chỉ tiêu đầu trang.
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Kpi:
    """MỘT ô chỉ tiêu của báo cáo đánh giá.

    Con số, đơn vị và lý do vắng số nằm trong CÙNG một value object, nên
    không có đường nào lấy được `value` mà bỏ mất `reason` — đó là toàn bộ
    lớp lỗi mà `gated_cell` của PHB-03 đã đóng lại ở tầng trình bày, ở đây
    được đóng sớm hơn một tầng.

    `partial_value` chỉ có mặt với chỉ tiêu bị cổng coverage chặn. Nó KHÔNG
    phải một con số dự phòng để hiện thay khi `value` rỗng: nó là bằng chứng
    "đã tính được đến đâu", và tầng trình bày chỉ được dùng nó cạnh coverage,
    không bao giờ ở vị trí của một kết luận cả kỳ.
    """

    key: str
    value: Optional[Decimal]
    unit: str
    #: `None` ⟺ `value is not None`. Bất biến này được `__post_init__` canh.
    reason: Optional[str] = None
    #: Chỉ tiêu này có bị cổng coverage 100 % chi phối không.
    gated: bool = False
    #: Con số MỘT PHẦN của một chỉ tiêu bị cổng chặn (`None` nếu không có).
    partial_value: Optional[Decimal] = None
    #: Khoá drill-down: tầng route biến nó thành một URL giữ nguyên kỳ + scope.
    drill: Optional[str] = None

    def __post_init__(self) -> None:
        if (self.value is None) != (self.reason is not None):
            raise ValueError(
                f"Kpi {self.key!r}: có số thì KHÔNG được có lý do, và không có "
                "số thì BẮT BUỘC có lý do — một ô trống không giải thích được "
                "là đúng thứ R4 tồn tại để loại bỏ")

    @property
    def available(self) -> bool:
        return self.value is not None


def _count_kpi(key: str, value: int, *, lines: int, drill: str) -> Kpi:
    """Ô ĐẾM. Một phạm vi rỗng cho ra `—` kèm lý do, không phải `0`.

    `0 đơn` trên một kỳ đã có dòng là một sự thật (mọi dòng đều thiếu số
    chứng từ); `0 đơn` trên một kỳ chưa nạp sổ là một câu khác hẳn. Hai câu
    đó không được viết giống nhau.
    """
    if lines == 0:
        return Kpi(key=key, value=None, unit=UNIT_COUNT,
                   reason=REASON_NO_LINES, drill=drill)
    return Kpi(key=key, value=Decimal(value), unit=UNIT_COUNT, drill=drill)


def headline(totals: bm.BusinessTotals) -> dict[str, Kpi]:
    """Tám chỉ tiêu đầu trang của MỘT phạm vi, khoá theo tên chỉ tiêu.

    Bốn chỉ tiêu đầu đọc thẳng `BusinessTotals`; bốn chỉ tiêu sau đi qua cổng
    coverage 100 %. Không chỉ tiêu nào ở đây tính lại một con số cộng được:
    `totals` đã là kết quả của `business_metrics.totals`.
    """
    revenue = totals.sales_revenue
    orders = totals.orders
    official_profit = totals.official_kpi_profit
    official_converted = totals.official_converted_sales
    empty = totals.lines == 0

    def _gated(key: str, value, partial, *, converted: bool) -> Kpi:
        """Một ô bị cổng coverage chặn — và lý do nói ĐÚNG cửa nào đang đóng."""
        if value is not None:
            return Kpi(key=key, value=value, unit=UNIT_VND, gated=True,
                       partial_value=partial, drill=key)
        if empty:
            reason = REASON_NO_LINES
        elif converted:
            reason = REASON_CONVERTED_NOT_OFFICIAL
        else:
            reason = REASON_PROFIT_NOT_OFFICIAL
        return Kpi(key=key, value=None, unit=UNIT_VND, reason=reason,
                   gated=True, partial_value=partial, drill=key)

    def _derived(key: str, value, *, needs_orders: bool) -> Kpi:
        """Một ô CHIA từ lợi nhuận chính thức — ba nhánh vắng số, ba lý do."""
        if value is not None:
            return Kpi(key=key, value=value,
                       unit=UNIT_PERCENT if key == "margin_percent" else UNIT_VND,
                       gated=True, drill=key)
        if empty:
            reason = REASON_NO_LINES
        elif official_profit is None:
            reason = REASON_PROFIT_NOT_OFFICIAL
        elif needs_orders and orders == 0:
            reason = REASON_NO_ORDERS
        else:
            reason = REASON_NO_REVENUE
        return Kpi(key=key, value=None,
                   unit=UNIT_PERCENT if key == "margin_percent" else UNIT_VND,
                   reason=reason, gated=True, drill=key)

    sales = (
        Kpi(key="sales_revenue", value=revenue, unit=UNIT_VND,
            drill="sales_revenue")
        if revenue is not None else
        Kpi(key="sales_revenue", value=None, unit=UNIT_VND,
            reason=REASON_NO_LINES if empty else REASON_NO_REVENUE,
            drill="sales_revenue"))

    per_order = revenue_per_order(revenue, orders)
    return {
        "sales_revenue": sales,
        "orders": _count_kpi("orders", orders, lines=totals.lines,
                             drill="orders"),
        "qualifying_quantity": (
            Kpi(key="qualifying_quantity", value=totals.qualifying_quantity,
                unit=UNIT_COUNT, drill="qualifying_quantity")
            if not empty else
            Kpi(key="qualifying_quantity", value=None, unit=UNIT_COUNT,
                reason=REASON_NO_LINES, drill="qualifying_quantity")),
        "revenue_per_order": (
            Kpi(key="revenue_per_order", value=per_order, unit=UNIT_VND,
                drill="revenue_per_order")
            if per_order is not None else
            Kpi(key="revenue_per_order", value=None, unit=UNIT_VND,
                reason=(REASON_NO_LINES if empty else
                        REASON_NO_ORDERS if orders == 0 else REASON_NO_REVENUE),
                drill="revenue_per_order")),
        "kpi_profit": _gated("kpi_profit", official_profit, totals.kpi_profit,
                             converted=False),
        "margin_percent": _derived(
            "margin_percent", margin_percent(official_profit, revenue),
            needs_orders=False),
        "profit_per_order": _derived(
            "profit_per_order", profit_per_order(official_profit, orders),
            needs_orders=True),
        "converted_sales": _gated(
            "converted_sales", official_converted, totals.converted_sales,
            converted=True),
    }


#: Thứ tự hiển thị đã freeze của đầu trang (brief §1). Cố định ở đây để mọi
#: bề mặt — trang web, test, tài liệu — đọc cùng một thứ tự.
HEADLINE_ORDER = (
    "sales_revenue", "orders", "qualifying_quantity", "revenue_per_order",
    "kpi_profit", "margin_percent", "profit_per_order", "converted_sales",
)


# --------------------------------------------------------------------------
# Lịch — mọi câu hỏi về "đến hôm nay" quy về đúng ba hàm này.
# --------------------------------------------------------------------------

def days_in_month(period: tuple[int, int]) -> int:
    return calendar.monthrange(period[0], period[1])[1]


def is_running(period: Optional[tuple[int, int]], *, today: date) -> bool:
    """Kỳ đang xem CÓ PHẢI tháng dương lịch hiện tại không."""
    return period is not None and period == (today.year, today.month)


def as_of(period: Optional[tuple[int, int]], *, today: date) -> Optional[date]:
    """Ngày mà mọi con số "đến nay" của kỳ được cắt tới.

        tháng đang chạy   ⟹ HÔM NAY (tính cả hôm nay, đúng quy ước
                             `reporting_sheets.month_progress_percent`)
        tháng đã qua      ⟹ ngày cuối tháng
        tháng chưa tới    ⟹ `None` — chưa có ngày nào để cắt tới
        không có kỳ       ⟹ `None`

    `today` được TRUYỀN VÀO, không đọc đồng hồ: một hàm đọc đồng hồ bên trong
    thì không kiểm được "giả sử hôm nay là ngày 8" mà không đợi tới ngày 8.
    """
    if period is None:
        return None
    current = (today.year, today.month)
    if period > current:
        return None
    if period == current:
        return today
    return date(period[0], period[1], days_in_month(period))


def days_elapsed(period: Optional[tuple[int, int]], *, today: date) -> int:
    """Số ngày lịch ĐÃ TRÔI QUA của kỳ, TÍNH CẢ ngày đang xét.

    Ngày hôm nay là một ngày bán hàng đang diễn ra, không phải một ngày chưa
    bắt đầu — cùng quy ước `§15` mà `month_progress_percent` đã freeze, và
    dùng lại nó là cách bảo đảm hai chỉ báo tiến độ trên cùng một màn hình
    không nói hai câu khác nhau về cùng một tháng.
    """
    moment = as_of(period, today=today)
    return 0 if moment is None else moment.day


def days_remaining(period: Optional[tuple[int, int]], *, today: date) -> int:
    """Số ngày lịch SAU ngày đang xét, trong cùng tháng.

    Kỳ đã kết thúc ⟹ `0`, và `0` ở đây KHÔNG được đem đi chia (xem
    `target_progress`). Kỳ chưa tới ⟹ trọn tháng.
    """
    if period is None:
        return 0
    moment = as_of(period, today=today)
    if moment is None:
        return days_in_month(period)
    return days_in_month(period) - moment.day


# --------------------------------------------------------------------------
# Run-rate — một phép NHÂN, có nhãn, và không bao giờ tự gọi là dự báo.
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class RunRate:
    """Ước tính cả tháng NẾU tốc độ hiện tại giữ nguyên.

    Không phải một dự báo: không mô hình, không mùa vụ, không nguyên nhân.
    Đúng một phép nhân trên chính con số đang hiển thị, và tầng trình bày
    BẮT BUỘC gắn nhãn đó (`RUN_RATE_LABEL`).
    """

    value: Optional[Decimal]
    reason: Optional[str] = None
    elapsed_days: int = 0
    month_days: int = 0

    def __post_init__(self) -> None:
        if (self.value is None) != (self.reason is not None):
            raise ValueError("RunRate: có số thì không có lý do, và ngược lại")


def run_rate(
    value: Optional[Decimal], *, period: Optional[tuple[int, int]], today: date,
    dated_lines: int, official: bool = True,
) -> RunRate:
    """`giá trị đến as_of / số ngày đã trôi qua × số ngày trong tháng`.

    Bốn cửa từ chối, theo đúng thứ tự brief §2 đặt ra:

    1. Kỳ KHÔNG đang chạy ⟹ không ước tính. Tháng đã xong thì con số thật đã
       nằm ngay đó, và một "ước tính" cạnh nó chỉ tạo ra một con số thứ hai để
       nhầm lẫn.
    2. Chỉ tiêu nền chưa CHÍNH THỨC ⟹ không ước tính. Nhân một con số một
       phần lên cả tháng là nhân cả phần thiếu lên theo.
    3. Không có dòng nào mang ngày bán ⟹ không đo được tốc độ theo ngày.
    4. Chưa có ngày nào trôi qua ⟹ không chia cho 0.
    """
    month_days = 0 if period is None else days_in_month(period)
    elapsed = days_elapsed(period, today=today)
    if not is_running(period, today=today):
        return RunRate(value=None, reason=RUNRATE_NOT_RUNNING,
                       elapsed_days=elapsed, month_days=month_days)
    if not official or value is None:
        return RunRate(value=None, reason=RUNRATE_VALUE_NOT_OFFICIAL,
                       elapsed_days=elapsed, month_days=month_days)
    if dated_lines <= 0:
        return RunRate(value=None, reason=RUNRATE_NO_DAILY_DATA,
                       elapsed_days=elapsed, month_days=month_days)
    if elapsed <= 0:
        return RunRate(value=None, reason=RUNRATE_NO_ELAPSED_DAYS,
                       elapsed_days=elapsed, month_days=month_days)
    projected = (Decimal(value) / Decimal(elapsed) * Decimal(month_days)
                 ).quantize(_DONG, rounding=ROUND_HALF_UP)
    return RunRate(value=projected, elapsed_days=elapsed, month_days=month_days)


# --------------------------------------------------------------------------
# Target và tiến độ.
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class TargetProgress:
    """Tiến độ của MỘT phạm vi có target (nhân viên hoặc sheet nhóm).

    KHÔNG có target cấp công ty ở bất kỳ đâu trong file này, và không có phép
    cộng target nào: `DEC-PHB02-08` §7 nói rõ target của Nội thành là con số
    Owner tự đặt chứ không phải tổng target của ba người trong đó, nên cộng
    lên để lấp chỗ trống sẽ cho ra một con số Owner chưa từng đặt.
    """

    #: Target VND của phạm vi, `None` = Owner chưa thiết lập.
    target: Optional[Decimal]
    #: DS quy đổi CHÍNH THỨC của phạm vi, `None` = chưa được phép công bố.
    actual: Optional[Decimal]
    #: DS quy đổi một phần (bằng chứng, không phải kết luận).
    partial_actual: Optional[Decimal]
    percent: Optional[Decimal]
    reason: Optional[str]
    #: Còn thiếu bao nhiêu VND để chạm target. `0` khi đã đạt/vượt.
    shortfall: Optional[Decimal]
    achieved: Optional[bool]
    days_remaining: int
    #: Mức DS quy đổi cần đạt MỖI NGÀY còn lại. `0` khi đã đạt.
    required_per_day: Optional[Decimal]
    required_reason: Optional[str]

    @property
    def has_target(self) -> bool:
        return self.target is not None


def target_progress(
    *, target: Optional[Decimal], totals: bm.BusinessTotals,
    period: Optional[tuple[int, int]], today: date,
) -> TargetProgress:
    """Tiến độ target của một phạm vi — đọc DS quy đổi CHÍNH THỨC.

    `% target` đi qua `business_metrics.vs_target_percent` nguyên vẹn: không
    cap ở 100 %, không in `0 %` khi chưa có số. Ba mã lý do của hàm đó được
    giữ nguyên; R4 chỉ chèn thêm `TARGET_ACTUAL_NOT_OFFICIAL` vào ĐÚNG khe mà
    trước đây bị `TARGET_NO_ACTUAL` nuốt mất (xem hằng số đó).
    """
    actual = totals.official_converted_sales
    partial = totals.converted_sales
    remaining_days = days_remaining(period, today=today)

    if target is None:
        reason = bm.TARGET_UNSET
    elif target == 0:
        reason = bm.TARGET_ZERO
    elif actual is None:
        reason = (TARGET_ACTUAL_NOT_OFFICIAL if partial is not None
                  else bm.TARGET_NO_ACTUAL)
    else:
        reason = None

    percent = (None if reason is not None
               else bm.vs_target_percent(actual, target))
    if reason is not None:
        return TargetProgress(
            target=target, actual=actual, partial_actual=partial,
            percent=None, reason=reason, shortfall=None, achieved=None,
            days_remaining=remaining_days, required_per_day=None,
            required_reason=reason)

    gap = Decimal(target) - Decimal(actual)
    achieved = gap <= 0
    shortfall = Decimal(0) if achieved else gap
    if achieved:
        # "Đã đạt/vượt" ⟹ mức cần đạt mỗi ngày là 0, và đó là một con số
        # THẬT, không phải một ô trống: brief §2 yêu cầu nói ra điều đó.
        required, required_reason = Decimal(0), None
    elif remaining_days <= 0:
        required, required_reason = None, TARGET_NO_DAYS_REMAINING
    else:
        required = (shortfall / Decimal(remaining_days)).quantize(
            _DONG, rounding=ROUND_HALF_UP)
        required_reason = None
    return TargetProgress(
        target=target, actual=actual, partial_actual=partial,
        percent=percent, reason=None, shortfall=shortfall, achieved=achieved,
        days_remaining=remaining_days, required_per_day=required,
        required_reason=required_reason)


# --------------------------------------------------------------------------
# So kỳ trước theo CÙNG SỐ NGÀY LỊCH.
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class SameDaysComparison:
    """Doanh thu 01..N của kỳ này so với 01..N của kỳ liền trước.

    `day_cutoff` là N THẬT ĐÃ DÙNG cho CẢ HAI vế. Nó có thể nhỏ hơn ngày đang
    xét khi tháng trước ngắn hơn (31/03 so với tháng 02): cắt hai vế ở hai
    con số ngày khác nhau thì phép so không còn là "cùng số ngày lịch" nữa,
    và một tháng 02 sẽ luôn trông kém hơn vì nó bị so bằng ít ngày hơn.
    """

    current: Optional[Decimal]
    previous: Optional[Decimal]
    percent: Optional[Decimal]
    reason: Optional[str]
    day_cutoff: int
    #: Ngày đang xét — khác `day_cutoff` khi tháng trước ngắn hơn.
    as_of_day: int
    #: Dòng bị loại khỏi phép so vì KHÔNG có ngày bán. Phải báo ra, không giấu.
    excluded_undated_lines: int
    #: Phép so chạy trên toàn bộ hai tháng (kỳ đã kết thúc), không cắt ngày.
    full_month: bool


def _lines_up_to_day(
    details: Sequence[dict], day: Optional[int]
) -> tuple[list[bm.BusinessLine], int]:
    """`(các dòng có ngày bán <= day, số dòng KHÔNG có ngày bán)`.

    `day is None` ⟹ không cắt, chỉ tách dòng không ngày ra. Dòng không ngày
    KHÔNG bao giờ lọt vào vế nào của phép so: nó không thuộc ngày nào nên
    không thuộc "01..N" của bất kỳ tháng nào, và đưa nó vào một vế sẽ làm
    chính vế đó lớn lên không lý do.
    """
    kept: list[bm.BusinessLine] = []
    undated = 0
    for detail in details:
        sale_date = detail.get("sale_date")
        if sale_date is None:
            undated += 1
            continue
        if day is None or sale_date.day <= day:
            kept.append(detail["line"])
    return kept, undated


def same_days_comparison(
    *, period: Optional[tuple[int, int]],
    current_details: Sequence[dict], previous_details: Sequence[dict],
    today: date,
) -> SameDaysComparison:
    """So doanh thu bán hàng của hai kỳ trên CÙNG một khoảng ngày lịch.

    Kỳ đã kết thúc thì không cắt gì cả — hai tháng trọn vẹn so với nhau là
    phép so đúng, và cắt chúng theo "hôm nay" sẽ vứt đi phần cuối tháng của
    cả hai vế mà không ai yêu cầu.
    """
    if period is None:
        return SameDaysComparison(
            current=None, previous=None, percent=None,
            reason=COMPARE_NO_PERIOD, day_cutoff=0, as_of_day=0,
            excluded_undated_lines=0, full_month=False)

    running = is_running(period, today=today)
    previous_period_ = previous_month(period)
    if running:
        as_of_day = today.day
        cutoff = min(as_of_day, days_in_month(previous_period_))
    else:
        as_of_day = days_in_month(period)
        cutoff = as_of_day

    cut = None if not running else cutoff
    current_lines, current_undated = _lines_up_to_day(current_details, cut)
    previous_lines, previous_undated = _lines_up_to_day(previous_details, cut)

    current_totals = bm.totals(current_lines)
    previous_totals = bm.totals(previous_lines)
    current_value = current_totals.sales_revenue

    if previous_totals.lines == 0:
        reason = COMPARE_PREVIOUS_NO_LINES
    elif previous_totals.sales_revenue in (None, Decimal(0)):
        reason = COMPARE_PREVIOUS_ZERO
    else:
        reason = None

    percent = (None if reason is not None else bm.month_over_month_percent(
        current_value, previous_totals.sales_revenue))
    # `month_over_month_percent` vẫn trả `None` khi vế HIỆN TẠI chưa có doanh
    # thu nào. Đó không phải một vấn đề của kỳ trước, nên lý do phải nói đúng
    # vế đang thiếu thay vì đổ sang tháng kia.
    if reason is None and percent is None:
        reason = COMPARE_CURRENT_NO_REVENUE

    return SameDaysComparison(
        current=current_value, previous=previous_totals.sales_revenue,
        percent=percent, reason=reason,
        day_cutoff=cutoff if running else as_of_day, as_of_day=as_of_day,
        excluded_undated_lines=current_undated + previous_undated,
        full_month=not running)


def previous_month(period: tuple[int, int]) -> tuple[int, int]:
    """Tháng liền trước. Viết ở đây để module THUẦN không phải import tầng web."""
    year, month = period
    return (year - 1, 12) if month == 1 else (year, month - 1)


# --------------------------------------------------------------------------
# Phân tích đóng góp.
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class GroupRow:
    """Một hàng của bảng đóng góp — mặt hàng, nhóm hàng, hay nguồn đơn.

    `orders` là `COUNT DISTINCT order_key` TRONG chính hàng này. Nó KHÔNG
    cộng dọc được: một đơn có hai mặt hàng được đếm ở cả hai hàng. Đây đúng
    cùng sự thật `R-E5` mà bảng nhân viên đã phải nói ra, chỉ đổi chiều gộp —
    và tầng trình bày BẮT BUỘC lấy dòng TỔNG từ tổng kỳ, không cộng cột này.
    """

    key: str
    label: str
    totals: bm.BusinessTotals
    #: Tỉ trọng doanh thu trong phạm vi đang xem (`None` khi không chia được).
    revenue_share: Optional[Decimal]
    #: Biên KPI của hàng — CHỈ khi hàng đó đủ coverage 100 % của chính nó.
    margin: Optional[Decimal]
    margin_reason: Optional[str]


def row_for(
    key: str, label: str, totals: bm.BusinessTotals, *,
    whole_revenue: Optional[Decimal],
) -> GroupRow:
    """Một hàng đóng góp dựng từ MỘT `BusinessTotals` đã có.

    Tách ra khỏi `_group_row` để tầng ráp dùng lại được cho những phân hoạch
    mà nó — chứ không phải module này — sở hữu: phân hoạch theo SHEET nằm ở
    `business_service.PeriodData.for_sheet`, và dựng lại nó ở đây sẽ là một
    định nghĩa thứ hai của "dòng này thuộc đơn vị báo cáo nào".

    Dùng hàm này thay vì tự dựng `GroupRow` bằng tay là cách bảo đảm mọi hàng
    của mọi bảng đóng góp tính biên bằng CÙNG một công thức và mang CÙNG một
    mã lý do khi biên chưa tồn tại — một hàng dựng tay rất dễ quên `margin_
    reason`, và khi đó ô "—" của nó là một ô trống không giải thích được.
    """
    official = totals.official_kpi_profit
    margin = margin_percent(official, totals.sales_revenue)
    if margin is not None:
        reason = None
    elif totals.lines == 0:
        reason = REASON_NO_LINES
    elif official is None:
        reason = REASON_PROFIT_NOT_OFFICIAL
    else:
        reason = REASON_NO_REVENUE
    return GroupRow(
        key=key, label=label, totals=totals,
        revenue_share=_ratio(totals.sales_revenue, whole_revenue,
                             quantum=_CENT, factor=Decimal(100)),
        margin=margin, margin_reason=reason)


def _group_row(
    key: str, label: str, lines: list[bm.BusinessLine],
    whole_revenue: Optional[Decimal],
) -> GroupRow:
    """Cùng một hàng, dựng từ một TẬP DÒNG — gộp trước rồi giao cho `row_for`."""
    return row_for(key, label, bm.totals(lines), whole_revenue=whole_revenue)


def by_product(
    details: Sequence[dict], *, whole: bm.BusinessTotals,
) -> list[GroupRow]:
    """Đóng góp theo MẶT HÀNG, gộp bằng `product_key`.

    `product_key` là khoá gộp DUY NHẤT được repo công nhận cho mặt hàng —
    cùng khoá mà `BusinessReportService.products` và `sales_queries.
    product_totals` dùng, và nhãn cũng lấy `min(product_raw)` theo đúng quy
    ước đã nghiệm thu ở đó. R4 KHÔNG dựng một khoá gộp thứ hai: hai bảng cùng
    tên "theo mặt hàng" mà gộp bằng hai khoá khác nhau là hai câu trả lời cho
    cùng một câu hỏi, và không ai nói được bản nào đúng.
    """
    buckets: dict[str, list[bm.BusinessLine]] = {}
    labels: dict[str, Optional[str]] = {}
    for detail in details:
        key = detail["product_key"]
        buckets.setdefault(key, []).append(detail["line"])
        label = detail.get("product_raw")
        if label and (labels.get(key) is None or label < labels[key]):
            labels[key] = label
    rows = [_group_row(key, labels.get(key) or key, lines, whole.sales_revenue)
            for key, lines in buckets.items()]
    return _sorted_by_revenue(rows)


def by_product_group(
    details: Sequence[dict], *, whole: bm.BusinessTotals,
    unknown_label: str = "Chưa phân nhóm",
) -> list[GroupRow]:
    """Đóng góp theo NHÓM HÀNG hiệu lực (`classified_product_group` → pipeline).

    Đọc ĐÚNG cùng thứ tự thẩm quyền mà `business_queries.
    effective_product_group` đã freeze, qua chính hai trường mà tầng truy vấn
    đã tính sẵn — không phân loại lại lần thứ hai ở đây.
    """
    buckets: dict[str, list[bm.BusinessLine]] = {}
    for detail in details:
        key = (detail.get("classified_product_group")
               or detail.get("pipeline_product_group") or "")
        buckets.setdefault(key, []).append(detail["line"])
    rows = [_group_row(key or "KHONG_XAC_DINH", key or unknown_label, lines,
                       whole.sales_revenue)
            for key, lines in buckets.items()]
    return _sorted_by_revenue(rows)


def by_lead_source(
    details: Sequence[dict], *, whole: bm.BusinessTotals,
    unknown_label: str = "Chưa phân loại nguồn",
) -> list[GroupRow]:
    """Đóng góp theo NGUỒN ĐƠN (`lead_source_final` của pipeline).

    Dòng không có nguồn rơi vào MỘT bucket có tên, không bị bỏ khỏi bảng: một
    bảng nguồn đơn thiếu mất phần "chưa phân loại" sẽ khiến các tỉ trọng cộng
    lại không bằng 100 % mà không có gì giải thích. Đây là một phép ĐẾM trên
    dữ liệu đã có, KHÔNG phải một phép suy ra nguyên nhân.
    """
    buckets: dict[str, list[bm.BusinessLine]] = {}
    for detail in details:
        key = (detail.get("lead_source") or "") or ""
        buckets.setdefault(key, []).append(detail["line"])
    rows = [_group_row(key or "KHONG_XAC_DINH", key or unknown_label, lines,
                       whole.sales_revenue)
            for key, lines in buckets.items()]
    return _sorted_by_revenue(rows)


def _sorted_by_revenue(rows: list[GroupRow]) -> list[GroupRow]:
    """Sắp doanh thu giảm dần. Đây CHỈ là trình bày.

    Không hàng nào được dán nhãn `top`, `tốt` hay `kém`: mọi nhãn kiểu đó cần
    một công thức và một quyết định Owner chưa tồn tại (`TASK-PRA-005` §17),
    và một thứ tự sắp xếp không phải một kết luận về nguyên nhân.
    """
    return sorted(rows, key=lambda row: (
        -(row.totals.sales_revenue or Decimal(0)), row.label, row.key))


def lowest_margin_rows(rows: Sequence[GroupRow], *, limit: int) -> list[GroupRow]:
    """Các hàng ĐÃ CÓ biên KPI, sắp biên tăng dần, cắt `limit` hàng đầu.

    Chỉ nhận hàng có `margin is not None`, tức hàng đã đủ coverage của chính
    nó. Một hàng chưa đủ coverage KHÔNG được xếp vào danh sách "biên thấp
    nhất": biên của nó chưa tồn tại, và xếp nó ở đó là kết luận từ một con số
    chưa được phép công bố.

    Đây là một PHÉP SẮP XẾP, không phải một phán quyết: không có ngưỡng "biên
    thấp" nào được phát minh ở đây, vì ngưỡng đó là một quyết định của Owner
    mà không phiên nào được tự chọn giúp.
    """
    ranked = [row for row in rows if row.margin is not None]
    ranked.sort(key=lambda row: (row.margin, row.label, row.key))
    return ranked[:limit]


# --------------------------------------------------------------------------
# Chiết khấu.
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class DiscountSummary:
    """Chiết khấu của một phạm vi — KHÔNG trừ thêm lần nào.

    `total_sales` mà pipeline ghi đã là số NET (`DEC-114`): chiết khấu đã
    được trừ một lần rồi. Khối này vì vậy chỉ CỘNG NGƯỢC phần đã trừ để nói
    ra quy mô của nó, đúng cách `business_metrics.display_contributions` tách
    một dòng làm hai:

        gross = net + discount      ⟹  tỉ lệ = discount / gross

    Mẫu số là doanh thu TRƯỚC chiết khấu, và tên trường nói ra điều đó. Chia
    cho doanh thu net sẽ cho một tỉ lệ lớn hơn sự thật, và không nhãn nào
    trên màn hình phân biệt được hai cách chia ấy.
    """

    discount_total: Decimal
    net_revenue: Optional[Decimal]
    gross_revenue: Optional[Decimal]
    #: `discount / gross × 100`, `None` khi không chia được.
    percent_of_gross: Optional[Decimal]
    #: Số DÒNG có chiết khấu > 0.
    lines_with_discount: int
    #: Số ĐƠN phân biệt có chiết khấu > 0.
    orders_with_discount: int
    #: `DEC-180`/R3 §2 — đơn có NGUY CƠ trừ chiết khấu hai lần.
    double_count_orders: tuple[str, ...]


def discounts(
    lines: Sequence[bm.BusinessLine], *, whole: bm.BusinessTotals,
) -> DiscountSummary:
    """Tổng chiết khấu của phạm vi, dựng từ CHÍNH các dòng đang được báo cáo.

    Dòng hiển thị "Chiết khấu" của sổ tay cũ (`line_type` = `DISCOUNT`)
    KHÔNG được cộng vào `discount_total`: số tiền của nó nằm ở
    `total_sales` âm của chính nó, không ở cột `discount`. Cộng cả hai là
    đúng phép trừ hai lần mà `discount_double_count_orders` được dựng để nêu
    tên — và các đơn ấy được liệt kê ra thay vì bị hệ thống tự chọn một cách
    hiểu.
    """
    total = Decimal(0)
    with_discount = 0
    orders: set[str] = set()
    for line in lines:
        if line.line_type == line_type_module.TYPE_DISCOUNT:
            continue
        value = Decimal(line.discount or 0)
        if value <= 0:
            continue
        total += value
        with_discount += 1
        orders.add(line.order_key)
    net = whole.sales_revenue
    gross = None if net is None else Decimal(net) + total
    return DiscountSummary(
        discount_total=total, net_revenue=net, gross_revenue=gross,
        percent_of_gross=_ratio(total, gross, quantum=_CENT,
                                factor=Decimal(100)),
        lines_with_discount=with_discount,
        orders_with_discount=len(orders),
        double_count_orders=bm.discount_double_count_orders(list(lines)))


# --------------------------------------------------------------------------
# Đơn/dòng lỗ — một phép LỌC, trên đúng tập đã tính được lợi nhuận.
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class LossScope:
    """Các dòng có lợi nhuận KPI ÂM, kèm PHẠM VI đã xét.

    `examined_lines`/`total_lines` là phần bắt buộc, không phải phần trang
    trí: khi coverage chưa đủ, danh sách này chỉ nói về những dòng đã tính
    được lợi nhuận, và trình bày nó như "toàn bộ đơn lỗ của kỳ" là một kết
    luận rộng hơn bằng chứng.
    """

    lines: tuple[bm.BusinessLine, ...]
    loss_total: Optional[Decimal]
    orders: tuple[str, ...]
    examined_lines: int
    total_lines: int

    @property
    def complete_scope(self) -> bool:
        """Đã xét được HẾT mọi dòng của phạm vi chưa."""
        return self.total_lines > 0 and self.examined_lines == self.total_lines


def loss_lines(lines: Sequence[bm.BusinessLine]) -> LossScope:
    """Dòng có `kpi_profit < 0`, chỉ trong tập đã tính được lợi nhuận.

    Không có ngưỡng "biên thấp" nào ở đây: `< 0` là một mệnh đề khách quan
    trên chính con số đã tính, còn "thấp" cần một ngưỡng mà chỉ Owner đặt
    được.
    """
    losing = tuple(line for line in lines
                   if line.kpi_profit is not None and line.kpi_profit < 0)
    examined = sum(1 for line in lines if line.contributes_profit)
    total = sum(line.kpi_profit for line in losing) if losing else None
    return LossScope(
        lines=losing, loss_total=total,
        orders=tuple(sorted({line.order_key for line in losing})),
        examined_lines=examined, total_lines=len(lines))


# --------------------------------------------------------------------------
# Chất lượng dữ liệu — phân bố provenance giá nhập.
# --------------------------------------------------------------------------

#: Thứ tự cố định của bảng phân bố. `POLICY_ZERO` đứng TÁCH khỏi `PENDING`:
#: một giá 0 do chính sách quy định là một câu trả lời HOÀN TẤT
#: (`OD-105B-01` §3), còn `PENDING` là chưa có câu trả lời nào. Gộp hai thứ
#: đó lại chính là điều `business_metrics` đã tách ra ở R3.
PROVENANCE_ORDER = (
    bm.PROVENANCE_AUTO, bm.PROVENANCE_MANUAL, bm.PROVENANCE_MANUAL_OVERRIDE,
    bm.PROVENANCE_POLICY_ZERO, bm.PROVENANCE_PENDING,
)


def provenance_breakdown(
    lines: Sequence[bm.BusinessLine],
) -> list[tuple[str, int]]:
    """`[(provenance, số dòng)]` theo thứ tự cố định; bỏ nhóm rỗng.

    Tổng các nhóm LUÔN bằng số dòng của phạm vi — `purchase_provenance` là
    một hàm toàn phần trên năm giá trị, nên không dòng nào rơi ra ngoài.
    """
    counts: dict[str, int] = {}
    for line in lines:
        code = line.purchase_provenance
        counts[code] = counts.get(code, 0) + 1
    ordered = [(code, counts[code]) for code in PROVENANCE_ORDER
               if code in counts]
    # Một provenance lạ (hợp đồng đổi mà đây chưa biết) vẫn phải hiện ra,
    # đứng cuối — im lặng bỏ nó đi sẽ làm tổng không còn khớp số dòng.
    ordered += [(code, count) for code, count in sorted(counts.items())
                if code not in PROVENANCE_ORDER]
    return ordered


def price_source_breakdown(
    details: Sequence[dict], *, unknown_key: str = "",
) -> list[tuple[str, int]]:
    """`[(thẩm quyền giá, số dòng)]` — NGUỒN mà pipeline đã dùng cho từng dòng.

    Khác `provenance_breakdown`, và cả hai đều cần thiết vì chúng trả lời hai
    câu:

        provenance_breakdown  con số giá nhập KPI HIỆU LỰC đến từ đâu
                              (giá tay · giá tự động · chính sách · chưa có)
        price_source_breakdown  lần chạy pipeline đã HỎI nguồn nào
                              (`TRACKING_DAILY_MIN`, `Pending`, …)

    Đây là thứ gần nhất với câu hỏi "giá MIN theo ngày đã trả lời được bao
    nhiêu dòng" mà dữ liệu hiệu lực CÓ THỂ trả lời: `day_status`
    (`FINAL`/`PROVISIONAL`) của hợp đồng `daily-min-v1` sống trong ảnh chụp
    lúc chạy và KHÔNG được ghi xuống `order_line_result_version`, nên R4 —
    vốn chỉ đọc dữ liệu hiệu lực — không dựng lại được nó. Nói ra giới hạn
    ấy là việc của tầng trình bày (`MIN_STATUS_UNAVAILABLE_NOTE`); ở đây chỉ
    đếm những gì thật sự có.

    Sắp theo số dòng giảm dần rồi theo tên, nên bảng không đổi thứ tự giữa
    hai lần tải trang.
    """
    counts: dict[str, int] = {}
    for detail in details:
        key = detail.get("price_source") or unknown_key
        counts[key] = counts.get(key, 0) + 1
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))


def latest_sale_date(details: Sequence[dict]) -> Optional[date]:
    """Ngày bán MỚI NHẤT trong phạm vi, hoặc `None` khi không dòng nào có ngày."""
    dates = [detail["sale_date"] for detail in details
             if detail.get("sale_date") is not None]
    return max(dates) if dates else None


def dated_line_count(details: Sequence[dict]) -> int:
    """Số dòng CÓ ngày bán — điều kiện để đo được bất kỳ tốc độ theo ngày nào."""
    return sum(1 for detail in details if detail.get("sale_date") is not None)


__all__ = [
    "COMPARE_CURRENT_NO_REVENUE", "COMPARE_NO_PERIOD",
    "COMPARE_PREVIOUS_NO_LINES", "COMPARE_PREVIOUS_ZERO",
    "COMPARE_REASONS", "DiscountSummary", "GroupRow", "HEADLINE_ORDER", "Kpi",
    "KPI_REASONS", "LossScope", "PROVENANCE_ORDER",
    "REASON_CONVERTED_NOT_OFFICIAL", "REASON_NO_LINES", "REASON_NO_ORDERS",
    "REASON_NO_REVENUE", "REASON_PROFIT_NOT_OFFICIAL", "RUNRATE_REASONS",
    "RUNRATE_NOT_RUNNING", "RUNRATE_NO_DAILY_DATA",
    "RUNRATE_NO_ELAPSED_DAYS", "RUNRATE_VALUE_NOT_OFFICIAL", "RunRate",
    "SameDaysComparison", "TARGET_ACTUAL_NOT_OFFICIAL",
    "TARGET_NO_DAYS_REMAINING", "TARGET_REASONS", "TargetProgress",
    "UNIT_COUNT", "UNIT_PERCENT", "UNIT_VND", "as_of", "by_lead_source",
    "by_product", "by_product_group", "dated_line_count", "days_elapsed",
    "days_in_month", "days_remaining", "discounts", "headline", "is_running",
    "latest_sale_date", "loss_lines", "lowest_margin_rows", "margin_percent",
    "previous_month", "price_source_breakdown", "profit_per_order",
    "provenance_breakdown",
    "revenue_per_order", "row_for", "run_rate", "same_days_comparison",
    "target_progress",
]
