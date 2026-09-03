"""Nhãn hiển thị Review reason cho Owner Launcher — S069, thuần presentation.

Chỉ đổi CÁCH GỌI TÊN cho người đọc; chuỗi reason authoritative gốc (đã ghi
trong Excel) không bị đổi, không bị gộp. Reason chưa có nhãn: hiện nguyên
văn, không che giấu.
"""

from __future__ import annotations

#: DEC-PAN-001 (PRICE_AUTHORITY_NORMALIZATION) — hai mã KHÔNG còn được sinh ra
#: cho kết quả MỚI (xem `excel_exporter._present_lines`), nhưng nhãn của chúng
#: PHẢI ở lại: `pending_reasons_json` của các result version đã persist trước
#: quyết định này vẫn chứa chúng, và kiến trúc hiện hành hiển thị trung thực
#: lịch sử đã lưu. KHÔNG backfill, KHÔNG migration, KHÔNG viết lại evidence cũ
#: — một lần chạy cũ là bằng chứng của luật đang hiệu lực LÚC ĐÓ. Bỏ nhãn ở
#: đây chỉ khiến màn hình lịch sử hiện mã tiếng Anh thô, không làm lịch sử
#: sạch hơn.
RETIRED_PENDING_REASONS = frozenset({
    "Pending.accounting_purchase_price",
    "Pending.accounting_profit",
})

REASON_DISPLAY_LABELS = {
    "IDENTITY_UNRESOLVED": "Chưa nhận diện sản phẩm",
    "TRACKING_HISTORY_PENDING": "Thiếu giá lịch sử Tracking",
    "Missing.PurchasePrice": "Thiếu giá mua tham chiếu",
    # Hai nhãn dưới đây là RETIRED_PENDING_REASONS — chỉ dùng để đọc lại lịch
    # sử đã persist, không còn là business status reason của kết quả mới.
    "Pending.accounting_purchase_price": "Thiếu giá nhập kế toán",
    "Pending.accounting_profit": "Thiếu lợi nhuận kế toán",
    "Pending.eligible_kpi_profit": "Thiếu lợi nhuận KPI",
    "Suspicious": "Bất thường",
    # TASK-PRA-004 — phần còn lại của vũ trụ mã ĐÓNG (10 giá trị
    # `PriceResolutionReason` ∪ 8 `validation.models.CATEGORIES` ∪ 3 chuỗi
    # `Pending.<field>`). KHÔNG phải taxonomy mới: tập mã đã đóng sẵn ở tầng
    # engine, đây chỉ là đặt tên tiếng Việt cho phần chưa có tên, để trang
    # Bán hàng không phải hiện một mã tiếng Anh cho người đọc nghiệp vụ.
    # Bảy nhãn phía trên GIỮ NGUYÊN TỪNG CHỮ — chúng đang chạy thật ở nơi khác.
    "SALE_DATE_MISSING": "Dòng chưa có ngày bán",
    "RAW_PRODUCT_IDENTITY_EMPTY": "Dòng chưa ghi tên sản phẩm",
    "IDENTITY_SOURCES_UNAVAILABLE": "Chưa có dữ liệu để nhận diện sản phẩm",
    "IDENTITY_REQUIRES_CONFIRMATION": "Sản phẩm cần người xác nhận trước khi lấy giá",
    "TRACKING_HISTORY_SOURCE_UNAVAILABLE": "Chưa có nguồn giá lịch sử Tracking",
    "VENDOR_SOURCE_NOT_AUTHORIZED": "Nguồn giá nhà cung cấp chưa được cho phép dùng",
    "PUBLIC_PURCHASE_SOURCE_UNAVAILABLE": "Chưa có bảng giá PP",
    "PUBLIC_PURCHASE_NO_PRICE_AT_SALE_DATE": "Thiếu giá PP tại ngày bán",
    "Missing": "Thiếu dữ liệu bắt buộc trên dòng",
    "Suspicious.ERP": "ERP báo lợi nhuận âm",
    "OrderInconsistency": "Đơn có thông tin không thống nhất giữa các dòng",
    "SourceClassification": "Nguồn khách ghi tay khác kết quả tự động",
    "Duplicate": "Có dòng trùng nội dung trong sổ",
    "EmployeeMapping": "Chưa khớp được nhân viên với danh sách",
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
