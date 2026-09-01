"""Nhãn hiển thị Review reason cho Owner Launcher — S069, thuần presentation.

Chỉ đổi CÁCH GỌI TÊN cho người đọc; chuỗi reason authoritative gốc (đã ghi
trong Excel) không bị đổi, không bị gộp. Reason chưa có nhãn: hiện nguyên
văn, không che giấu.
"""

from __future__ import annotations

REASON_DISPLAY_LABELS = {
    "IDENTITY_UNRESOLVED": "Chưa nhận diện sản phẩm",
    "TRACKING_HISTORY_PENDING": "Thiếu giá lịch sử Tracking",
    "Missing.PurchasePrice": "Thiếu giá mua tham chiếu",
    "Pending.accounting_purchase_price": "Thiếu giá nhập kế toán",
    "Pending.accounting_profit": "Thiếu lợi nhuận kế toán",
    "Pending.eligible_kpi_profit": "Thiếu lợi nhuận KPI",
    "Suspicious": "Bất thường",
}


def format_review_reasons(review_reason_counts: dict[str, int]) -> str:
    """Nhiều nhất tới ít nhất; hoà thì theo thứ tự chữ cái reason gốc."""
    if not review_reason_counts:
        return ""
    lines = ["Lý do cần xem lại (đếm theo dòng, một dòng có thể có nhiều lý do):"]
    for reason, count in sorted(
        review_reason_counts.items(), key=lambda item: (-item[1], item[0])
    ):
        label = REASON_DISPLAY_LABELS.get(reason, reason)
        lines.append(f"  {label}    {count}")
    return "\n".join(lines)
