"""Coverage của một snapshot: khoảng ngày ĐO ĐƯỢC và khoảng ngày KHAI BÁO.

Nguyên tắc bất di dịch (TASK-PRA-002 mục 7.2): hệ thống KHÔNG BAO GIỜ tự suy
ra "sổ này đã đầy đủ". min/max ngày, header, số dòng, thứ tự upload — không
thứ nào chứng minh được rằng kế toán đã xuất hết chứng từ của một khoảng. Chỉ
một hành động xác nhận tường minh của người dùng mới nâng lên
``CONFIRMED_COMPLETE`` (mục 7.3, slice B) — module này KHÔNG bao giờ trả về
giá trị đó.

Header chỉ được parse theo HAI dạng đã đo được trong dữ liệu thật/fixture.
Dạng thứ ba xuất hiện → ``None`` và ``DETECTED_ONLY``; không đoán, không nới
regex (escalation trigger của task).
"""

from __future__ import annotations

import re
from calendar import monthrange
from datetime import date
from pathlib import Path
from typing import Iterable, Optional

import openpyxl

from app.history.models import (
    CONFIRMED_COMPLETE, DETECTED_ONLY, HEADER_CONSISTENT,
)

HEADER_CELL_ROW = 2
FIRST_DATA_ROW = 6
_ORDER_ID_COLUMN = 1  # 0-based, khớp raw_reader.COLUMNS["order_id"]

# Dạng (1): file production thật (docs/analysis/01_DATA_MAPPING.md §1).
_RANGE_HEADER = re.compile(
    r"^Từ ngày\s+(\d{2}/\d{2}/\d{4})\s+đến ngày\s+(\d{2}/\d{2}/\d{4})"
)
# Dạng (2): fixture golden theo tháng (đo ở S079).
_MONTH_HEADER = re.compile(r"^Nhân viên:\s*.*?,\s*Tháng\s+(\d{1,2})\s+năm\s+(\d{4})\s*$")


def parse_header(header_text: Optional[str]) -> Optional[tuple[date, date]]:
    """Khoảng ngày KHAI BÁO ở ô A2, hoặc ``None`` nếu không khớp dạng đã biết."""
    text = (header_text or "").strip()
    match = _RANGE_HEADER.match(text)
    if match:
        try:
            start = _from_dmy(match.group(1))
            end = _from_dmy(match.group(2))
        except ValueError:
            return None
        return (start, end) if start <= end else None
    match = _MONTH_HEADER.match(text)
    if match:
        month, year = int(match.group(1)), int(match.group(2))
        if not 1 <= month <= 12:
            return None
        return date(year, month, 1), date(year, month, monthrange(year, month)[1])
    return None


def _from_dmy(text: str) -> date:
    day, month, year = (int(part) for part in text.split("/"))
    return date(year, month, day)


def detected_range(dates: Iterable[Optional[date]]) -> tuple[Optional[date], Optional[date]]:
    """[min, max] trên các ngày bán THỰC SỰ có. Dòng thiếu ngày không bị bịa."""
    known = sorted(value for value in dates if value is not None)
    return (known[0], known[-1]) if known else (None, None)


def coverage_state(
    header: Optional[tuple[date, date]],
    detected: tuple[Optional[date], Optional[date]],
) -> str:
    """``HEADER_CONSISTENT`` chỉ khi header BAO TRỌN khoảng đo được.

    Header hẹp hơn dữ liệu (có ngày nằm ngoài khoảng khai báo) là một cảnh
    báo, không phải một sự đầy đủ — nên nó rơi về ``DETECTED_ONLY``.
    """
    detected_min, detected_max = detected
    if header is None or detected_min is None or detected_max is None:
        return DETECTED_ONLY
    return (HEADER_CONSISTENT
            if header[0] <= detected_min and detected_max <= header[1]
            else DETECTED_ONLY)


def scan_sheet(path: Path) -> tuple[Optional[str], int, int]:
    """Một lượt đọc streaming: ``(header_text, sheet_data_rows, rows_without_order_id)``.

    Đọc ``read_only=True`` và KHÔNG giữ workbook thứ hai trong RAM — số dòng
    thật của sheet phải được đếm ĐỘC LẬP với ``read_raw_rows``, nếu không thì
    "bao nhiêu dòng bị bỏ vì thiếu Số BH" là con số do chính bên bỏ dòng tự
    khai. Lỗi đọc không bao giờ được làm hỏng một lần chạy đã thành công —
    caller nhận ``(None, 0, 0)`` và trang snapshot nói thẳng là không đọc được.
    """
    workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        sheet = workbook.active
        header_text = None
        data_rows = 0
        without_order_id = 0
        for row_number, values in enumerate(sheet.iter_rows(values_only=True), start=1):
            if row_number == HEADER_CELL_ROW:
                header_text = values[0] if values else None
                header_text = None if header_text is None else str(header_text).strip() or None
            if row_number < FIRST_DATA_ROW:
                continue
            if not any(value is not None and str(value).strip() for value in values):
                continue
            data_rows += 1
            order_id = values[_ORDER_ID_COLUMN] if len(values) > _ORDER_ID_COLUMN else None
            if order_id is None or not str(order_id).strip():
                without_order_id += 1
        return header_text, data_rows, without_order_id
    finally:
        workbook.close()
