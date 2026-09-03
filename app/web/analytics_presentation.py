"""TASK-PRA-003 — trình bày SỐ MỚI: định dạng và GẮN NHÃN, không tính toán.

Cùng hai kỷ luật với ``legacy_presentation`` (TASK-PRA-001 §8), thêm một điều
riêng của PRA-003:

1. Không phép tính nghiệp vụ nào ở đây. Mọi con số đã do
   ``analytics_queries`` tổng hợp; tầng này chỉ đổi cách VIẾT nó ra. Ngoại lệ
   DUY NHẤT là Δ so kỳ trước — một phép trừ và một tỉ lệ giữa HAI con số đã
   tổng hợp sẵn, được frozen contract mục 5.1 yêu cầu tường minh.
2. Không con số nào hiển thị mà thiếu nhãn nguồn. SỐ MỚI = ``PIPELINE_GENERATED``.
3. **``None`` LUÔN thành ``—``, không bao giờ thành ``0``.** Đây là lý do tầng
   này tồn tại tách khỏi template: một ``{{ value or 0 }}`` lỡ tay trong Jinja
   sẽ biến "chưa biết" thành "bằng không" mà không test nào của tầng truy vấn
   bắt được.

``format_number`` được TÁI DỤNG từ ``legacy_presentation`` thay vì nhân bản:
nó thuần định dạng vi-VN (dấu chấm phân cách nghìn) và trung lập với nguồn dữ
liệu — quy ước viết số của Owner không đổi theo việc số đến từ đâu. Tái dụng
ở đây KHÔNG kéo theo ngữ nghĩa legacy nào: nhãn, đơn vị và badge của SỐ MỚI
đều định nghĩa riêng bên dưới.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from app.web.analytics_queries import previous_month
from app.web.legacy_presentation import format_number, format_ratio

ORIGIN_BADGE = "SỐ MỚI"
ORIGIN_TITLE = "Số do Reports tính từ sổ kế toán đã nạp"
ORIGIN_NOTE = "Số do Reports tính từ sổ kế toán đã nạp."
BOTH_SOURCES_NOTE = (
    "SỐ CŨ = số cũ trong Excel. SỐ MỚI = số Reports tính từ sổ kế toán đã nạp. "
    "Hai loại số không bao giờ được cộng chung."
)
NO_PREVIOUS_PERIOD = "chưa có dữ liệu kỳ trước"
ALL_DATA_LABEL = "Toàn bộ dữ liệu"

# D3: nhãn ô số lượng là "Tổng số lượng" và KHÔNG được gọi là "Số lượng sản
# phẩm"/"Tổng số SP" — chưa có quy tắc phân loại product-line có thẩm quyền
# (N.7). Con số đếm MỌI dòng, kể cả phí vận chuyển / công lắp đặt / chiết khấu.
QUANTITY_LABEL = "Tổng số lượng"
QUANTITY_NOTE = (
    "Tổng số lượng đếm MỌI dòng của sổ, kể cả phí vận chuyển, công lắp đặt, "
    "chiết khấu và voucher — nên KHÔNG khớp cột \"Tổng số SP\" của báo cáo cũ."
)
ORDER_COLUMN_NOTE = (
    "Một đơn có nhiều nhân viên được đếm ở TỪNG dòng nhân viên liên quan, nên "
    "cột Đơn cộng lại có thể lớn hơn tổng đơn của kỳ. Dòng TỔNG đếm mỗi đơn "
    "đúng một lần."
)
UNKNOWN_EMPLOYEE = "Chưa xác định nhân viên"

# 8 cột SỐ MỚI của trang Nhân viên (mục 4 của task file). Không thêm cột nào:
# top-nhân-viên và so-kỳ-trước-theo-nhân-viên là USEFUL_BUT_DEFER.
EMPLOYEE_COLUMNS: tuple[str, ...] = (
    "Nhân viên", "Nhóm", "Đơn", "Dòng hàng", QUANTITY_LABEL, "Doanh thu",
    "LN KPI", "LN kế toán",
)


def money(value: Optional[Decimal]) -> str:
    """Tiền/số lượng. ``None`` ⟹ ``—``; KHÔNG BAO GIỜ ``0``."""
    return format_number(value)


def count(value: Optional[int]) -> str:
    return "—" if value is None else format_number(Decimal(value))


def coverage(covered: int, total: int) -> str:
    """Coverage viết dạng ``N / M dòng``, cố ý KHÔNG viết dạng phần trăm.

    Hai lý do: (a) ``0 / 351 dòng`` nói thẳng "chưa dòng nào chắc chắn" trong
    khi ``0%`` dễ bị đọc nhầm thành "lãi bằng không"; (b) hai coverage của D1
    có TỬ SỐ khác nhau, và viết ra cả tử lẫn mẫu buộc người đọc thấy điều đó
    thay vì so hai phần trăm như thể chúng cùng nghĩa.
    """
    return f"{count(covered)} / {count(total)} dòng"


def profit(value: Optional[Decimal], covered: int, total: int) -> dict:
    """Một ô lợi nhuận LUÔN đi kèm coverage (quy tắc P4) — không có đường nào
    render con số lợi nhuận mà thiếu mẫu số của nó."""
    return {"text": money(value), "coverage": coverage(covered, total),
            "missing": value is None}


def delta(current: Optional[Decimal], previous: Optional[Decimal]) -> dict:
    """Δ tuyệt đối + Δ % so kỳ trước.

    Thiếu một trong hai vế ⟹ cả hai ô là ``—``. TUYỆT ĐỐI KHÔNG quy kỳ trước
    vắng mặt về ``0`` rồi in ``-100%``: đó là câu "sụt 100%" cho một kỳ chưa
    bao giờ có dữ liệu, và là nhánh sai kinh điển của mọi dashboard.
    """
    if current is None or previous is None:
        return {"delta": "—", "ratio": "—", "missing": True}
    difference = Decimal(current) - Decimal(previous)
    sign = "+" if difference > 0 else ""
    # Kỳ trước bằng 0 mà kỳ này khác 0: tỉ lệ không xác định. Viết ``—`` chứ
    # không viết một phần trăm vô nghĩa hay chia cho không.
    ratio = "—" if previous == 0 else f"{sign}{format_ratio(difference / Decimal(previous))}"
    return {"delta": f"{sign}{format_number(difference)}", "ratio": ratio,
            "missing": False}


def period_label(period: Optional[tuple[int, int]]) -> str:
    return ALL_DATA_LABEL if period is None else f"Tháng {period[1]:02d}/{period[0]}"


def period_value(period: Optional[tuple[int, int]]) -> str:
    """Giá trị của tham số ``ky`` — ``tat-ca`` cho "Toàn bộ dữ liệu"."""
    return "tat-ca" if period is None else f"{period[0]}-{period[1]:02d}"


def period_options(periods: list[tuple[int, int]]) -> list[dict]:
    """Bộ chọn kỳ: MỌI tuỳ chọn dẫn xuất từ ``sale_date`` đã lưu. Không quý,
    không năm, không khoảng ngày tự do — chúng đã DEFER khỏi slice này."""
    return [{"value": period_value(period), "label": period_label(period)}
            for period in [None, *periods]]


def overview(totals: dict, previous: Optional[dict], *, period, undated: int) -> dict:
    """Mô hình hiển thị của Tổng quan — đúng 10 ô đã qua Minimum-Value Filter.

    ``previous is None`` mang HAI nghĩa và cả hai đều dẫn tới ô so sánh trống:
    đang xem "Toàn bộ dữ liệu" (không bịa kỳ trước cho một khoảng tuỳ ý), hoặc
    tháng liền trước không có dòng pipeline nào.
    """
    lines = totals["lines"]
    return {
        "period_label": period_label(period),
        "orders": count(totals["orders"]),
        "lines": count(lines),
        "quantity": money(totals["quantity"]),
        "total_sales": money(totals["total_sales"]),
        "kpi_profit": profit(totals["kpi_profit"], totals["kpi_lines"], lines),
        "accounting_profit": profit(
            totals["accounting_profit"], totals["accounting_lines"], lines),
        "auto_orders": count(totals["auto_orders"]),
        "review_orders": count(totals["review_orders"]),
        "comparison": None if previous is None else _comparison(totals, previous, period),
        "undated_lines": undated,
    }


def _comparison(totals: dict, previous: dict, period) -> dict:
    """Kỳ trước không có DÒNG NÀO ⟹ MỌI ô so sánh để trống.

    Không được đọc ``previous["orders"] == 0`` như thể đó là "kỳ trước bán
    được 0 đơn": một kỳ CHƯA CÓ DỮ LIỆU và một kỳ bán được không đồng nào là
    hai điều khác nhau, và chỉ một trong hai cho phép nói "tăng 40 đơn".
    """
    empty = previous["lines"] == 0
    prior = {"orders": None, "total_sales": None} if empty else previous
    return {
        "label": period_label(previous_period(period)),
        "orders": delta(totals["orders"], prior["orders"]),
        "total_sales": delta(totals["total_sales"], prior["total_sales"]),
        "empty": empty,
    }


def previous_period(period: Optional[tuple[int, int]]) -> Optional[tuple[int, int]]:
    return None if period is None else previous_month(*period)


def employee_rows(rows: list[dict], totals: dict) -> list[dict]:
    """Bảng nhân viên + dòng ``TỔNG``.

    Dòng TỔNG lấy thẳng từ ``period_totals`` chứ KHÔNG cộng các dòng phía
    trên: với cột Đơn hai cách cho kết quả KHÁC nhau một cách hợp lệ (một đơn
    có thể liên quan nhiều nhân viên) và dòng TỔNG phải đếm mỗi đơn đúng MỘT
    lần.
    """
    return [*(_employee_row(row) for row in rows),
            {**_employee_row({**totals, "employee": "TỔNG", "employee_group": ""}),
             "total_row": True}]


def _employee_row(row: dict) -> dict:
    lines = row["lines"]
    return {
        "employee": row["employee"] or UNKNOWN_EMPLOYEE,
        "employee_group": row["employee_group"] or "—",
        "orders": count(row["orders"]),
        "lines": count(lines),
        "quantity": money(row["quantity"]),
        "total_sales": money(row["total_sales"]),
        "kpi_profit": profit(row["kpi_profit"], row["kpi_lines"], lines),
        "accounting_profit": profit(
            row["accounting_profit"], row["accounting_lines"], lines),
        "total_row": False,
    }


__all__ = [
    "ALL_DATA_LABEL", "BOTH_SOURCES_NOTE", "EMPLOYEE_COLUMNS", "NO_PREVIOUS_PERIOD",
    "ORDER_COLUMN_NOTE", "ORIGIN_BADGE", "ORIGIN_NOTE", "ORIGIN_TITLE",
    "QUANTITY_LABEL", "QUANTITY_NOTE", "UNKNOWN_EMPLOYEE", "count", "coverage",
    "delta", "employee_rows", "money", "overview", "period_label", "period_options",
    "period_value", "previous_period", "profit",
]
