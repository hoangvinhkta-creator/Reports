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

from app.beta_presentation import REASON_DISPLAY_LABELS
from app.modules.reporting import business_metrics as bm
from app.modules.reporting import profit_gate
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

# `B03` — hai câu này TỪNG quy mọi thiếu sót về "thiếu giá nhập", trong khi
# một dòng có thể chưa tính được vì số lượng bằng 0, thiếu giá bán, hoặc file
# thẩm quyền KPI hỏng. Nói sai nguyên nhân là đẩy Owner đi sửa nhầm chỗ, nên
# câu chung chỉ nói CÓ THIẾU; phần "thiếu cái gì" nằm ở bảng liệt kê bên dưới,
# nơi mỗi cửa chặn tự nói tên mình.
OFFICIAL_NOTE = (
    "Mọi dòng hàng của kỳ đều đã tính được lợi nhuận, nên lợi nhuận KPI và DS "
    "quy đổi dưới đây là số CHÍNH THỨC."
)
INCOMPLETE_NOTE = (
    "Còn dòng hàng của kỳ chưa tính được lợi nhuận. Các con số lợi nhuận KPI "
    "và DS quy đổi dưới đây CHƯA phải số chính thức — chúng chỉ cộng phần đã "
    "tính được. Danh sách ngay dưới nói rõ thiếu cái gì và sửa ở đâu."
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
    "Lợi nhuận KPI", "DS quy đổi", "Đã tính được lợi nhuận",
)

# Bảng kê chi tiết — mỗi dòng hàng là MỘT dòng bảng, ô nhập được nằm ngay
# trong dòng đó, và các ô tiền suy ra tự cập nhật sau khi lưu (chỉ thị
# `ORDER DETAIL TABLE`). Bốn cột cuối là SUY RA, không gõ tay được.
DETAIL_COLUMNS: tuple[str, ...] = (
    "Ngày", "Mã đơn", "Mặt hàng", "SL", "Giá bán", "Giá nhập KPI", "Nguồn giá",
    "Doanh thu", "Lợi nhuận KPI", "DS quy đổi", "Nhân viên",
)
# Tên cũ, giữ lại để không phá vỡ nơi nào còn tham chiếu.
MISSING_PRICE_COLUMNS = DETAIL_COLUMNS

DERIVED_COLUMNS_NOTE = (
    "Ba cột Doanh thu · Lợi nhuận KPI · DS quy đổi là số SUY RA — không gõ "
    "trực tiếp được. Sửa Số lượng/Giá bán trên sổ gốc, hoặc sửa Giá nhập ngay "
    "tại đây, rồi bấm LƯU: các con số đó tự tính lại trên chính trang này."
)
UNRESOLVED_EMPLOYEE_NOTE = (
    "Những dòng chưa biết của ai VẪN được cộng vào lợi nhuận của cả kỳ. "
    "Chúng chỉ chưa được cộng cho một nhân viên cụ thể — chọn tên rồi bấm LƯU "
    "là chúng chuyển sang bảng của người đó."
)
NET_SALES_NOTE = (
    "Cột Doanh thu lấy đúng con số kế toán mà hệ thống đã ghi khi nạp sổ, "
    "KHÔNG phải phép nhân Số lượng × Giá bán làm lại."
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
        "owner_fixable_lines": coverage.owner_fixable_lines,
        "unresolved_employee_lines": coverage.unresolved_employee_lines,
        # Mỗi mục là một VIỆC CỤ THỂ, kèm chỗ phải sửa — thay cho ô đếm gộp cũ
        # vốn nói "nhập giá không cứu được" cho gần như mọi dòng (`B03`).
        "blockers": [
            {"code": code, "lines": lines, "label": profit_gate.label(code)}
            for code, lines in coverage.blocked_lines
        ],
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
        # `OD-5` — hai con số này luôn cộng lại bằng `kpi_profit`. Hiện cả hai
        # cạnh nhau để phần đang treo không biến mất không dấu vết.
        "employee_attributed_profit": _decimal(totals.employee_attributed_profit),
        "unattributed_profit": _decimal(totals.unattributed_profit),
        "unattributed_lines": totals.coverage.unresolved_employee_lines,
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


def _derived_cell(value: Optional[Decimal], blockers: tuple[str, ...]) -> dict:
    """Một ô tiền SUY RA: có số, hoặc `—` KÈM lý do — không bao giờ bịa `0`.

    Chỉ thị `ORDER DETAIL TABLE`: *"Missing required inputs: show blank/N/A +
    reason rather than fabricate 0."* Một ô `0` trông như đã tính xong và ra
    kết quả bằng không; một ô `—` kèm câu "chưa có giá nhập" nói đúng sự thật
    và chỉ luôn việc phải làm.
    """
    if value is not None:
        return {"text": _decimal(value), "missing": False, "reason": ""}
    reason = profit_gate.label(blockers[0]) if blockers else ""
    return {"text": "—", "missing": True, "reason": reason}


def detail_rows(details: list[dict]) -> list[dict]:
    """Bảng kê chi tiết — một dòng hàng là một dòng, sửa được ngay tại chỗ.

    Đây là "trang tính" mà chỉ thị `ORDER DETAIL TABLE` mô tả, và nó cố ý
    KHÔNG phải một Excel trong trình duyệt:

    - Ô nhập được: **giá nhập** (`DEC-PHB02-02` §3 — sửa được kể cả khi đã
      AUTO-fill) và **nhân viên** (`OD-5`).
    - Ô suy ra: doanh thu, lợi nhuận KPI, DS quy đổi. Chúng không gõ được, và
      tự tính lại từ đầu vào hiện tại sau mỗi lần lưu. Không có nút "tính".
    - Doanh thu lấy NGUYÊN `total_sales` kế toán đã ghi, không thay bằng
      `số lượng × đơn giá` (chỉ thị: *"Do NOT casually replace authoritative
      net sales"*).

    Danh sách gồm CẢ dòng đã đủ giá: quyền sửa một giá tự động phải có chỗ
    thực hiện, và Owner cần nhìn thấy cả kỳ chứ không chỉ phần lỗi.
    """
    rows = []
    for detail in details:
        line = detail["line"]
        provenance = line.purchase_provenance
        blockers = line.profit_blockers
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
            # --- ba ô SUY RA -------------------------------------------
            "total_sales": _derived_cell(line.total_sales, ()),
            "kpi_profit": _derived_cell(line.kpi_profit, blockers),
            "converted_sales": _derived_cell(line.converted_sales, blockers),
            # --- nhân viên, sửa được ------------------------------------
            "employee": line.employee or UNKNOWN_EMPLOYEE,
            "employee_value": line.employee or "",
            "employee_resolved": line.employee_resolved,
            "employee_reassigned": line.employee_provenance == "MANUAL",
            "source_employee": line.source_employee,
            # --- cửa chặn và cảnh báo -----------------------------------
            "blockers": [{"code": code, "label": profit_gate.label(code)}
                         for code in blockers],
            "warnings": [{"code": code, "label": profit_gate.label(code)}
                         for code in line.warnings],
            # Mã pipeline hiện NGUYÊN VĂN dưới nhãn tiếng Việt: chúng là bằng
            # chứng lịch sử của lần chạy máy, không còn là cửa chặn.
            "pipeline_reasons": [REASON_DISPLAY_LABELS.get(code, code)
                                 for code in line.pending_reasons],
            "pipeline_status": line.status,
        })
    return rows


def missing_price_rows(details: list[dict]) -> list[dict]:
    """Tên cũ của `detail_rows`, giữ lại cho các nơi còn gọi theo tên cũ."""
    return detail_rows(details)


def assignable_employee_options(
    employees: list[tuple[str, Optional[str]]]
) -> list[dict]:
    """Danh sách nhân viên trong ô chọn của bảng kê (`OD-5`).

    KHÔNG có mục trống: ô này để GÁN một dòng cho ai đó. Muốn trả dòng về
    trạng thái chưa xác định thì dùng nút GỠ, và nút đó nói rõ nó làm gì —
    một mục trống lẫn giữa các tên người thì không.
    """
    return [{"value": name, "label": name, "group": group}
            for name, group in employees]


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
    "ALL_DATA_LABEL", "CONVERTED_SALES_NOTE", "DERIVED_COLUMNS_NOTE",
    "DETAIL_COLUMNS", "EMPLOYEE_COLUMNS", "GIA_DUNG_COLUMNS", "INCOMPLETE_NOTE",
    "MISSING_PRICE_COLUMNS", "MOM_ALL_DATA", "MOM_NO_PREVIOUS",
    "MOM_PREVIOUS_ZERO", "NET_SALES_NOTE", "OFFICIAL_NOTE", "ORDER_COLUMN_NOTE",
    "ORIGIN_BADGE", "PROVENANCE_LABELS", "QUALIFYING_QUANTITY_LABEL",
    "QUALIFYING_QUANTITY_NOTE", "STATE_LABELS", "UNKNOWN_EMPLOYEE",
    "UNRESOLVED_EMPLOYEE_NOTE",
    "assignable_employee_options", "coverage_cell", "detail_rows",
    "employee_detail", "employee_options", "employee_rows", "gated_cell",
    "gia_dung_rows", "missing_price_rows", "month_over_month", "percent",
    "period_label", "period_options", "period_value", "summary",
]
