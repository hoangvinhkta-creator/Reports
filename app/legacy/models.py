"""Bản ghi bất biến của một lần đọc workbook legacy.

Không có phương thức nào ở đây tính toán lại số: mọi giá trị đi thẳng từ ô
Excel vào thuộc tính, giữ nguyên trạng (xem TASK-PRA-001 §20 "no
recalculation"). Đơn vị KHÔNG được quy đổi — Summary là ``kVND``, DataChart
là VND nguyên; việc gắn nhãn đơn vị là chuyện của tầng trình bày.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional

# Ánh xạ cột Summary → tên trường, theo docs/analysis/02_FORMULA_MAPPING.md §3.
# Cột L và mọi cột không có trong bảng đó KHÔNG được đoán ý nghĩa — chúng
# đơn giản không được nhập (trường tương ứng để None).
SUMMARY_COLUMN_FIELDS: dict[str, str] = {
    "C": "orders",
    "D": "products",
    "E": "sales",
    "F": "converted_revenue",
    "G": "profit",
    "H": "margin_ratio",
    "I": "vs_prev_month_ratio",
    "J": "stock_ratio",
    "K": "actual_profit",
    "M": "target",
    "N": "vs_target_ratio",
    "O": "bonus",
    "P": "workdays",
    "Q": "base_salary",
    "R": "allowance",
    "S": "total_salary",
}

UNIT_SUMMARY = "kVND"


@dataclass(frozen=True)
class SummaryRow:
    year: int
    month: Optional[int]
    seller_label: Optional[str]
    row_kind: str
    sheet_name: str
    sheet_row: int
    values: dict[str, Optional[Decimal]] = field(default_factory=dict)
    formula_text: dict[str, str] = field(default_factory=dict)
    known_defects: dict[str, list[str]] = field(default_factory=dict)
    unit: str = UNIT_SUMMARY

    @property
    def defect_codes(self) -> list[str]:
        codes: list[str] = []
        for column_codes in self.known_defects.values():
            for code in column_codes:
                if code not in codes:
                    codes.append(code)
        return sorted(codes)


@dataclass(frozen=True)
class DailySales:
    year: int
    month: int
    day: int
    sales_vnd: Optional[Decimal]
    source_sheet: str


@dataclass(frozen=True)
class MonthlyReference:
    year: int
    month: int
    sales_current_year_vnd: Optional[Decimal] = None
    sales_prev_year_vnd: Optional[Decimal] = None
    vs_last_year_ratio: Optional[Decimal] = None
    vs_target_ratio: Optional[Decimal] = None
    target_year: Optional[Decimal] = None
    # Không có ô nào trong docs/analysis/02_FORMULA_MAPPING.md §5 được xác
    # định là "doanh số trung bình/ngày"; để None thay vì tự tính từ tổng
    # tháng (tính = tạo số mới, vi phạm §20 của task).
    average_per_day: Optional[Decimal] = None
    target_per_day: Optional[Decimal] = None
    formula_text: dict[str, str] = field(default_factory=dict)


# Thẩm quyền nguồn của một lần nhập (`DEC-178`).
#
# ``AUTHORITATIVE_YEAR``  — workbook lịch sử MỘT NĂM độc lập. Đây là nguồn
#                           CHUẨN cho năm đó; không nguồn nào ghi đè nó.
# ``WORKBOOK_SNAPSHOT``   — bản sao Summary của một năm khác nằm nhúng trong
#                           workbook của năm hiện hành. Bằng chứng thứ cấp.
#
# Vì sao là một trường TƯỜNG MINH chứ không suy từ tên sheet: quy tắc "nguồn
# nào thắng" là một quyết định của chủ dự án, và một quyết định như thế không
# được phép phụ thuộc vào việc ai đó có nhớ đặt tên sheet đúng hay không.
SOURCE_AUTHORITY_YEAR = "AUTHORITATIVE_YEAR"
SOURCE_AUTHORITY_SNAPSHOT = "WORKBOOK_SNAPSHOT"


@dataclass(frozen=True)
class LegacyWorkbook:
    source_file_name: str
    file_fingerprint: str
    file_size: int
    sheets_imported: list[dict[str, str]]
    summary_rows: list[SummaryRow]
    daily_sales: list[DailySales]
    monthly_reference: list[MonthlyReference]
    source_authority: str = SOURCE_AUTHORITY_SNAPSHOT
