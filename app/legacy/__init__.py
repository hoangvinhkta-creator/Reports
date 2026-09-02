"""Import dữ liệu báo cáo cũ (origin = LEGACY_REFERENCE).

Ranh giới: module này chỉ ĐỌC Excel và trả về bản ghi bất biến. Không kết
nối database, không gọi mạng, không tính lại số cũ.
"""

from app.legacy.models import (
    DailySales, LegacyWorkbook, MonthlyReference, SummaryRow,
)
from app.legacy.parser import LegacyImportError, fingerprint_file, parse_workbook

__all__ = [
    "DailySales", "LegacyImportError", "LegacyWorkbook", "MonthlyReference",
    "SummaryRow", "fingerprint_file", "parse_workbook",
]
