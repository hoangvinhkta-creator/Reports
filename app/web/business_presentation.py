"""PHB-03 — trình bày Summary/Employee: định dạng và GẮN NHÃN, không tính toán.

Cùng kỷ luật với `analytics_presentation`, cộng một điều riêng của PHB-03:

1. Không phép tính nghiệp vụ nào ở đây. Mọi con số do
   `app/modules/reporting/business_metrics` tính; tầng này chỉ đổi cách VIẾT.
2. **`None` LUÔN thành `—`, không bao giờ thành `0`** (`R-S2`).
3. **CHÍNH THỨC và CHƯA HOÀN CHỈNH không bao giờ trông giống nhau** (`R-S7`).
   Một con số phụ thuộc coverage luôn đi kèm trạng thái của chính nó trong
   CÙNG một cấu trúc, nên không có đường nào render con số mà rơi mất nhãn.

## Ngôn ngữ hướng về Owner, không hướng về pipeline

Chỉ thị PHB-03 §5: *"Do not fill the page with technical provenance details by
default; make warnings understandable to Owner."* Vì vậy các nhãn ở đây nói
"Giá nhập tự động" / "Owner đã sửa" / "Owner đã nhập" thay vì `AUTO` /
`MANUAL_OVERRIDE` / `MANUAL`. Mã provenance vẫn được lưu và vẫn hiện ở đúng
một chỗ — bảng hoàn thiện giá nhập, nơi nó là thông tin cần thiết chứ không
phải nhiễu.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from app.modules.reporting import business_metrics as bm
from app.web.analytics_presentation import (
    ALL_DATA_LABEL, UNKNOWN_EMPLOYEE, count, money, period_label, period_options,
    period_value, previous_period,
)
from app.web.legacy_presentation import format_number

ORIGIN_BADGE = "SỐ MỚI"

# Nhãn trạng thái của mọi chỉ tiêu phụ thuộc coverage giá nhập.
STATE_LABELS = {
    bm.STATE_OFFICIAL: "CHÍNH THỨC",
    bm.STATE_INCOMPLETE: "CHƯA HOÀN CHỈNH",
}

OFFICIAL_NOTE = (
    "Đã có giá nhập cho toàn bộ dòng hàng của kỳ, nên lợi nhuận KPI và DS quy "
    "đổi dưới đây là số CHÍNH THỨC."
)
INCOMPLETE_NOTE = (
    "Chưa đủ giá nhập cho toàn bộ dòng hàng của kỳ. Các con số lợi nhuận KPI "
    "và DS quy đổi dưới đây CHƯA phải số chính thức — chúng chỉ cộng phần đã "
    "có giá nhập."
)
EMPTY_NOTE = "Kỳ này chưa có dòng hàng nào."

# Nhãn provenance hướng Owner (`DEC-PHB02-02` §3 vẫn phân biệt đủ ba trạng thái).
PROVENANCE_LABELS = {
    bm.PROVENANCE_AUTO: "Tự động",
    bm.PROVENANCE_MANUAL: "Owner đã nhập",
    bm.PROVENANCE_MANUAL_OVERRIDE: "Owner đã sửa",
    bm.PROVENANCE_PENDING: "Chưa có",
}

MOM_NO_PREVIOUS = "Chưa có dữ liệu tháng trước"
MOM_PREVIOUS_ZERO = "Tháng trước doanh thu 0 — không so được"
MOM_ALL_DATA = "Đang xem toàn bộ dữ liệu — không có tháng liền trước để so"

QUALIFYING_QUANTITY_LABEL = "Tổng số SP"
QUALIFYING_QUANTITY_NOTE = (
    "Tổng số SP chỉ cộng số lượng của những dòng có ĐƠN GIÁ BÁN trên "
    "1.000.000 đồng, để loại giá treo, chân kê và phụ kiện giá trị thấp."
)
CONVERTED_SALES_NOTE = (
    "DS quy đổi = lợi nhuận KPI CHIA cho tỉ lệ quy đổi của từng dòng, rồi "
    "cộng lại. Tỉ lệ có thể khác nhau ngay trong cùng một nhân viên."
)
ORDER_COLUMN_NOTE = (
    "Một đơn có nhiều nhân viên được đếm ở TỪNG dòng nhân viên liên quan, nên "
    "cột Đơn cộng lại có thể lớn hơn tổng đơn của kỳ."
)

EMPLOYEE_COLUMNS: tuple[str, ...] = (
    "Nhân viên", "Nhóm", "Đơn", QUALIFYING_QUANTITY_LABEL, "Doanh thu",
    "Lợi nhuận KPI", "DS quy đổi", "Giá nhập đã đủ",
)

MISSING_PRICE_COLUMNS: tuple[str, ...] = (
    "Ngày", "Mã đơn", "Mặt hàng", "SL", "Giá bán", "Giá nhập KPI", "Nguồn giá",
)

GIA_DUNG_COLUMNS: tuple[str, ...] = (
    "Mặt hàng", "Số dòng", "Doanh thu", "Phân loại hiện tại", "Tick Gia dụng",
)


def _decimal(value: Optional[Decimal]) -> str:
    return "—" if value is None else format_number(value)


def percent(value: Optional[Decimal], *, sign: bool = False) -> str:
    """`None` ⟹ `—`. KHÔNG BAO GIỜ in vô cực hay một phần trăm bịa."""
    if value is None:
        return "—"
    prefix = "+" if sign and value > 0 else ""
    return f"{prefix}{format_number(value)}%"


def coverage_cell(coverage: bm.Coverage) -> dict:
    """Coverage viết dạng `N / M dòng` KÈM phần trăm, không thay cho nhau.

    `N / M dòng` là con số Owner hành động được ("còn 11 dòng phải nhập"); phần
    trăm là con số Owner cảm nhận được. Gate thì không đọc cái nào trong hai —
    nó đọc `is_complete`, vì `350/351` làm tròn thành `99,72 %` và không phần
    trăm nào được phép đứng thay cho một phép so bằng (`DEC-PHB02-02` §4).
    """
    return {
        "text": f"{count(coverage.covered_lines)} / {count(coverage.total_lines)} dòng",
        "percent": percent(coverage.percent),
        "complete": coverage.is_complete,
        "missing_price_lines": coverage.missing_price_lines,
        "review_blocked_lines": coverage.review_blocked_lines,
    }


def gated_cell(
    value: Optional[Decimal], official: Optional[Decimal], state: str
) -> dict:
    """Một chỉ tiêu phụ thuộc coverage + trạng thái của chính nó.

    `value` là con số cộng được đến hôm nay; `official` là `None` cho tới khi
    coverage đạt 100 %. Cả hai nằm trong cùng một dict để template không thể
    lấy con số mà bỏ nhãn.
    """
    return {
        "text": _decimal(value),
        "official": official is not None,
        "state": state,
        "state_label": STATE_LABELS[state],
        "missing": value is None,
    }


def month_over_month(
    current: Optional[Decimal], previous: Optional[Decimal], *,
    has_period: bool, previous_has_lines: bool,
) -> dict:
    """`DEC-PHB02-07` — mọi nhánh "không so được" đều có CHỮ, không có số.

    Ba nhánh, cố ý không gộp: đang xem "Toàn bộ dữ liệu" (không có tháng liền
    trước), tháng trước không có dòng nào, và tháng trước có dòng nhưng doanh
    thu bằng 0. Owner đọc ba câu khác nhau vì ba tình huống đó dẫn tới ba hành
    động khác nhau.
    """
    if not has_period:
        return {"percent": "—", "note": MOM_ALL_DATA, "missing": True}
    if not previous_has_lines:
        return {"percent": "—", "note": MOM_NO_PREVIOUS, "missing": True}
    value = bm.month_over_month_percent(current, previous)
    if value is None:
        return {"percent": "—", "note": MOM_PREVIOUS_ZERO, "missing": True}
    return {"percent": percent(value, sign=True), "note": "", "missing": False}


def _metrics(totals: bm.BusinessTotals) -> dict:
    state = totals.state
    return {
        "orders": count(totals.orders),
        "lines": count(totals.lines),
        "sales_revenue": _decimal(totals.sales_revenue),
        "qualifying_quantity": _decimal(totals.qualifying_quantity),
        "kpi_profit": gated_cell(
            totals.kpi_profit, totals.official_kpi_profit, state),
        "converted_sales": gated_cell(
            totals.converted_sales, totals.official_converted_sales, state),
        "coverage": coverage_cell(totals.coverage),
        "state": state,
        "state_label": STATE_LABELS[state],
        "official": totals.coverage.is_complete,
    }


def summary(
    totals: bm.BusinessTotals, *, period, previous_totals, undated: int,
) -> dict:
    """Mô hình hiển thị của Summary V1 (`R-S1`…`R-S8`)."""
    return {
        **_metrics(totals),
        "period_label": period_label(period),
        "previous_label": (
            None if period is None else period_label(previous_period(period))),
        "mom": month_over_month(
            totals.sales_revenue,
            None if previous_totals is None else previous_totals.sales_revenue,
            has_period=period is not None,
            previous_has_lines=(
                previous_totals is not None and previous_totals.lines > 0),
        ),
        "note": _state_note(totals),
        "undated_lines": undated,
    }


def _state_note(totals: bm.BusinessTotals) -> str:
    if totals.lines == 0:
        return EMPTY_NOTE
    return OFFICIAL_NOTE if totals.coverage.is_complete else INCOMPLETE_NOTE


def employee_rows(by_employee: list[tuple], company: bm.BusinessTotals) -> list[dict]:
    """Bảng nhân viên + dòng `TỔNG`.

    Dòng TỔNG lấy từ tổng KỲ chứ không cộng các dòng phía trên: một đơn có hai
    nhân viên được đếm ở cả hai dòng nhân viên, và dòng TỔNG phải đếm mỗi đơn
    đúng MỘT lần (`R-E5`).
    """
    rows = [
        {"employee": name or UNKNOWN_EMPLOYEE, "employee_group": group or "—",
         "key": name or "", "total_row": False, **_metrics(totals)}
        for name, group, totals in by_employee
    ]
    rows.append({"employee": "TỔNG", "employee_group": "", "key": "",
                 "total_row": True, **_metrics(company)})
    return rows


def employee_detail(
    name: Optional[str], group: Optional[str], totals: bm.BusinessTotals, *,
    period, previous_totals, gia_dung: bool,
) -> dict:
    """Mô hình hiển thị của Employee V1 (`R-E1`…`R-E8`)."""
    return {
        **_metrics(totals),
        "employee": name or UNKNOWN_EMPLOYEE,
        "employee_group": group or "—",
        "period_label": period_label(period),
        "previous_label": (
            None if period is None else period_label(previous_period(period))),
        "mom": month_over_month(
            totals.sales_revenue,
            None if previous_totals is None else previous_totals.sales_revenue,
            has_period=period is not None,
            previous_has_lines=(
                previous_totals is not None and previous_totals.lines > 0),
        ),
        "note": _state_note(totals),
        "gia_dung_workflow": gia_dung,
    }


def employee_options(
    employees: list[tuple[Optional[str], Optional[str]]]
) -> list[dict]:
    return [{"value": name or "", "label": name or UNKNOWN_EMPLOYEE}
            for name, _group in employees]


def missing_price_rows(details: list[dict]) -> list[dict]:
    """Các dòng cần Owner hoàn thiện giá nhập, hoặc đã hoàn thiện rồi.

    Bao gồm CẢ dòng đã có giá tự động: `DEC-PHB02-02` §3 nói ô giá nhập phải
    sửa được kể cả khi đã AUTO-fill, nên một danh sách chỉ có dòng thiếu sẽ
    không có chỗ nào để thực hiện quyền đó.
    """
    rows = []
    for detail in details:
        line = detail["line"]
        provenance = line.purchase_provenance
        rows.append({
            "order_key": detail["order_key"],
            "product_key": detail["product_key"],
            "occurrence_index": detail["occurrence_index"],
            "sale_date": detail["sale_date"],
            "product_raw": detail["product_raw"] or "—",
            "quantity": _decimal(line.quantity),
            "sell_price": _decimal(line.sell_price),
            "purchase_price": _decimal(line.purchase_price),
            "purchase_price_input": (
                "" if line.purchase_price is None else format_number(line.purchase_price)),
            "provenance": provenance,
            "provenance_label": PROVENANCE_LABELS[provenance],
            "pending": line.purchase_price is None,
            "overridden": provenance in (
                bm.PROVENANCE_MANUAL, bm.PROVENANCE_MANUAL_OVERRIDE),
            "review_blocked": line.blocked_by_review,
        })
    return rows


def gia_dung_rows(products: list[dict]) -> list[dict]:
    """Một dòng cho mỗi MẶT HÀNG (không phải mỗi dòng chứng từ) để tick.

    Gộp theo `product_key` vì `DEC-PHB02-05` gọi Gia dụng là một
    *product-level override*: tick một lần cho mặt hàng, không phải tick lại
    cho từng lần bán của nó.
    """
    return [
        {
            "product_key": product["product_key"],
            "product_label": product["product_label"] or "—",
            "lines": count(product["lines"]),
            "sales": _decimal(product["sales"]),
            "current_group": product["current_group"],
            "current_label": (
                "Gia dụng" if product["current_group"] == "GIA_DUNG"
                else "Điện máy"),
            "classified": product["classified"],
            "gia_dung": product["current_group"] == "GIA_DUNG",
        }
        for product in products
    ]


__all__ = [
    "ALL_DATA_LABEL", "CONVERTED_SALES_NOTE", "EMPLOYEE_COLUMNS",
    "GIA_DUNG_COLUMNS", "INCOMPLETE_NOTE", "MISSING_PRICE_COLUMNS",
    "MOM_ALL_DATA", "MOM_NO_PREVIOUS", "MOM_PREVIOUS_ZERO", "OFFICIAL_NOTE",
    "ORDER_COLUMN_NOTE", "ORIGIN_BADGE", "PROVENANCE_LABELS",
    "QUALIFYING_QUANTITY_LABEL", "QUALIFYING_QUANTITY_NOTE", "STATE_LABELS",
    "coverage_cell", "employee_detail", "employee_options", "employee_rows",
    "gated_cell", "gia_dung_rows", "missing_price_rows", "month_over_month",
    "percent", "period_label", "period_options", "period_value", "summary",
]
