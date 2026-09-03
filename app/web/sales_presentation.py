"""TASK-PRA-004 — trình bày Bán hàng: định dạng và GẮN NHÃN, không tính toán.

Tầng này TÁI DỤNG ``analytics_presentation`` thay vì nhân bản nó: ``money``,
``count``, ``coverage``, ``profit``, ``period_label``, ``period_options``,
``period_value`` và ``UNKNOWN_EMPLOYEE`` đều đã có thẩm quyền ở PRA-003 và
đang chạy production. Chép lại một trong số đó là dựng một nguồn sự thật thứ
hai cho cùng một quy ước hiển thị — hai bản sao sẽ lệch nhau ở đúng lần sửa
đầu tiên.

Ba kỷ luật riêng của PRA-004:

1. **``None`` LUÔN thành ``—``, không bao giờ thành ``0``.** Ba dòng PENDING
   của một đơn không có giá vốn nào; in ``0đ`` ở đó là nói với Owner rằng
   chúng lãi bằng không.
2. **Mọi ô lợi nhuận cấp ĐƠN mang coverage của chính nó.** Đây là failure path
   nghiêm trọng nhất của slice này: một đơn 66 triệu hiện "lợi nhuận 500.000"
   trần trụi khiến Owner tin đó là lãi của cả đơn, trong khi nó là lãi của
   1/4 dòng. Không có đường nào ở đây render lợi nhuận mà thiếu mẫu số.
3. **Không phát minh trạng thái.** Đúng hai nhãn: ``AUTO`` và
   ``CẦN KIỂM TRA``. Không ``PARTIAL``, không ``WARNING``, không ``APPROVED``
   — PRA-004 CHỈ-ĐỌC, nó không có gì để duyệt.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from app.beta_presentation import REASON_DISPLAY_LABELS
from app.web.analytics_presentation import (
    UNKNOWN_EMPLOYEE, count, money, profit,
)

STATUS_AUTO = "AUTO"
STATUS_REVIEW = "CẦN KIỂM TRA"

# Ngăn cách nhiều nhân viên trên MỘT đơn. Dấu chấm giữa dòng, không phải dấu
# phẩy: tên nhân viên đã chuẩn hoá có thể chứa dấu phẩy.
EMPLOYEE_SEPARATOR = " · "

MULTI_EMPLOYEE_NOTE = (
    "Đơn này có nhiều nhân viên trên các dòng. Reports KHÔNG tự chọn chủ đơn."
)
MULTI_DATE_NOTE = (
    "Đơn này có nhiều ngày bán trên các dòng, nên ngày hiện ở dạng khoảng."
)
PARTIAL_COVERAGE_NOTE = (
    "Lợi nhuận của đơn này chỉ tổng hợp các dòng ĐÃ có giá trị — nó KHÔNG phải "
    "lợi nhuận của toàn đơn. Các dòng còn lại chưa đủ căn cứ nên để trống, và "
    "ô trống nghĩa là chưa biết, không phải bằng không."
)
NO_ORDERS_NOTE = "Kỳ này chưa có đơn nào trên số mới."
REASON_LABEL = "Lý do cần kiểm tra"

# 9 cột của danh sách đơn (mục 12.A). Không thêm cột nào: lọc, sắp xếp tuỳ ý,
# tìm kiếm mã đơn và nhóm nhân viên đều là USEFUL_BUT_DEFER.
ORDER_COLUMNS: tuple[str, ...] = (
    "Mã đơn", "Ngày bán", "Nhân viên", "Dòng hàng", "Tổng số lượng",
    "Doanh thu", "LN KPI", "LN kế toán", "Trạng thái",
)

# 10 cột bảng dòng hàng (mục 12.B). Lý do KHÔNG phải cột thứ 11: một dòng có
# tới 6 lý do, nhét vào một ô bảng là không đọc được — nó xuống dòng phụ.
LINE_COLUMNS: tuple[str, ...] = (
    "Sản phẩm", "Số lượng", "Đơn giá bán", "Chiết khấu", "Doanh thu dòng",
    "Giá vốn (kế toán)", "Giá vốn (KPI)", "LN kế toán", "LN KPI", "Trạng thái",
)


def status(review: bool) -> str:
    """Đơn/dòng có ≥1 phần PENDING ⟹ CẦN KIỂM TRA. Không có trạng thái thứ ba."""
    return STATUS_REVIEW if review else STATUS_AUTO


def day(value: Optional[date]) -> str:
    return "—" if value is None else f"{value.day:02d}/{value.month:02d}/{value.year}"


def sale_dates(row: dict) -> str:
    """Một ngày khi mọi dòng cùng ngày; KHOẢNG khi không.

    KHÔNG chọn một ngày làm đại diện cho đơn: "đơn này bán ngày nào" là câu
    hỏi mà dữ liệu đôi khi không có một câu trả lời duy nhất, và bịa ra một
    câu trả lời duy nhất là làm mất chính thông tin Owner cần thấy.
    """
    first, last = row["sale_date_from"], row["sale_date_to"]
    return day(first) if first == last else f"{day(first)} – {day(last)}"


def employees(names: list) -> str:
    """Tất cả nhân viên của đơn, đã khử trùng lặp ở tầng truy vấn."""
    labelled = [name or UNKNOWN_EMPLOYEE for name in names] or [UNKNOWN_EMPLOYEE]
    return EMPLOYEE_SEPARATOR.join(labelled)


def order_row(row: dict) -> dict:
    """Một dòng của danh sách đơn — đúng 9 ô của mục 12.A."""
    lines = row["lines"]
    return {
        "order_key": row["order_key"],
        "sale_date": sale_dates(row),
        "employees": employees(row["employees"]),
        "multi_employee": len(row["employees"]) > 1,
        "multi_date": row["sale_date_from"] != row["sale_date_to"],
        "lines": count(lines),
        "quantity": money(row["quantity"]),
        "total_sales": money(row["total_sales"]),
        "kpi_profit": profit(row["kpi_profit"], row["kpi_lines"], lines),
        "accounting_profit": profit(
            row["accounting_profit"], row["accounting_lines"], lines),
        "status": status(row["review"]),
        "review": row["review"],
    }


def order_rows(rows: list[dict]) -> list[dict]:
    return [order_row(row) for row in rows]


def reason_labels(codes: list[str]) -> list[str]:
    """Mã lý do → nhãn tiếng Việt, GIỮ NGUYÊN thứ tự đã persist.

    Mã chưa có nhãn hiện NGUYÊN VĂN (hành vi sẵn có của
    ``REASON_DISPLAY_LABELS.get``): một lý do khó đọc vẫn là một lý do, còn bỏ
    im lặng thì dòng đó mất luôn câu trả lời cho "tại sao cần kiểm tra".
    """
    return [REASON_DISPLAY_LABELS.get(code, code) for code in codes]


def line_row(row: dict) -> dict:
    """Một dòng hàng — 10 ô của mục 12.B cộng danh sách lý do.

    ``Doanh thu dòng`` lấy thẳng ``total_sales`` đã lưu. Trang KHÔNG in công
    thức và KHÔNG tuyên bố tự dẫn xuất lại lợi nhuận: nó đặt các số ĐÃ LƯU
    cạnh nhau để Owner tự đối chiếu (FIND-PRA004-01).
    """
    review = row["status"] == "PENDING"
    return {
        "product": row["product_raw"] or "—",
        "quantity": money(row["quantity"]),
        "sell_price": money(row["sell_price"]),
        "discount": money(row["discount"]),
        "total_sales": money(row["total_sales"]),
        "accounting_purchase_price": money(row["accounting_purchase_price"]),
        "kpi_purchase_price": money(row["kpi_purchase_price"]),
        "accounting_profit": money(row["accounting_profit"]),
        "kpi_profit": money(row["eligible_kpi_profit"]),
        "status": status(review),
        "review": review,
        "reasons": reason_labels(row["reasons"]),
    }


def order_detail(detail: dict) -> dict:
    """Khối tổng hợp của MỘT đơn + bảng dòng hàng của nó.

    ``partial_coverage`` bật khi ít nhất một trong hai lợi nhuận có tử số nhỏ
    hơn số dòng. Nó là điều kiện để trang nói thẳng rằng con số kia không phải
    lợi nhuận của toàn đơn — cảnh báo này KHÔNG phụ thuộc vào việc người đọc
    có nhìn xuống mẫu số hay không.
    """
    lines = detail["lines"]
    return {
        **order_row(detail),
        "line_count": lines,
        "partial_coverage": min(detail["kpi_lines"], detail["accounting_lines"]) < lines,
        "coverage_note": PARTIAL_COVERAGE_NOTE,
        "lines_detail": [line_row(row) for row in detail["lines_detail"]],
    }


__all__ = [
    "EMPLOYEE_SEPARATOR", "LINE_COLUMNS", "MULTI_DATE_NOTE", "MULTI_EMPLOYEE_NOTE",
    "NO_ORDERS_NOTE", "ORDER_COLUMNS", "PARTIAL_COVERAGE_NOTE", "REASON_LABEL",
    "STATUS_AUTO", "STATUS_REVIEW", "day", "employees", "line_row",
    "order_detail", "order_row", "order_rows", "reason_labels", "sale_dates", "status",
]
