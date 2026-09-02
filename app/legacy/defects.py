"""Nhận diện lỗi công thức ĐÃ BIẾT của workbook cũ — annotate, KHÔNG sửa.

Bốn mã dưới đây tham chiếu ``docs/analysis/05_EXCEPTIONS.md``. Mọi kiểm tra
đều là kiểm tra CẤU TRÚC công thức (hoặc dạng của giá trị), không bao giờ là
"tính lại rồi so xem lệch bao nhiêu" — công cụ không có thẩm quyền nói số cũ
đúng hay sai, chỉ có thẩm quyền chỉ ra chỗ công thức tự mâu thuẫn.

- A1: số SP không nguyên (E1 của sheet nguồn trừ đi một tỉ lệ phần trăm).
- A2: dòng tổng tháng có cột SUM trên khoảng hẹp hơn cột khác → bỏ sót người bán.
- A4: ô tham chiếu sang sheet của người bán KHÁC nhãn của chính dòng đó.
- A6: mẫu số là hằng số gõ tay thay vì tham chiếu ô kỳ trước.

Không có phép chia nào trong module này. Các chuỗi như "/2" chỉ xuất hiện
bên trong biểu thức chính quy dùng để SO KHỚP văn bản công thức.
"""

from __future__ import annotations

import re
from decimal import Decimal
from typing import Optional

A1_NON_INTEGER_PRODUCTS = "A1"
A2_MONTH_TOTAL_MISSING_ROWS = "A2"
A4_CROSS_SHEET_LABEL_MISMATCH = "A4"
A6_HARDCODED_DENOMINATOR = "A6"

# ='03.2026 Ly'!$E$1  hoặc  ='03.2026 Ly'!E1
CROSS_SHEET_REF = re.compile(r"'(?P<sheet>[^']+)'!\$?(?P<col>[A-Z]+)\$?(?P<row>\d+)")
# =SUM(E4:E9)  /  =SUM(E4:E902)/2
SUM_RANGE = re.compile(
    r"SUM\(\s*(?P<col>[A-Z]+)(?P<start>\d+)\s*:\s*[A-Z]+(?P<end>\d+)\s*\)",
    re.IGNORECASE,
)
HALVING_SUFFIX = re.compile(r"SUM\([^)]*\)\s*/\s*2\b", re.IGNORECASE)
# =F4/1571182 — mẫu số là hằng số, không phải ô. "%": =G4/5.5% là tỉ lệ quy
# đổi hợp lệ, không phải lỗi A6, nên bị loại trừ tường minh.
CONSTANT_DENOMINATOR = re.compile(r"^=\s*[A-Z]+\$?\d+\s*/\s*\d+(?:\.\d+)?\s*$")
# Tên sheet nguồn: "MM.YYYY <nhãn người bán>"
SHEET_LABEL = re.compile(r"^\s*\d{1,2}\.(?P<year>\d{4})\s+(?P<label>.+?)\s*$")


def sheet_reference(formula: str) -> Optional[re.Match]:
    return CROSS_SHEET_REF.search(formula or "")


def split_sheet_label(sheet_name: str) -> Optional[tuple[int, str]]:
    """``'03.2026 Fanpage'`` → ``(2026, 'Fanpage')``; None nếu không đúng mẫu."""
    match = SHEET_LABEL.match(sheet_name or "")
    if match is None:
        return None
    return int(match.group("year")), match.group("label")


def is_halving_sum(formula: str) -> bool:
    return bool(HALVING_SUFFIX.search(formula or ""))


def sum_span(formula: str) -> Optional[tuple[int, int]]:
    match = SUM_RANGE.search(formula or "")
    if match is None:
        return None
    return int(match.group("start")), int(match.group("end"))


def _add(defects: dict[str, list[str]], column: str, code: str) -> None:
    codes = defects.setdefault(column, [])
    if code not in codes:
        codes.append(code)


def detect_seller_defects(
    *,
    seller_label: Optional[str],
    values: dict[str, Optional[Decimal]],
    formulas: dict[str, str],
    products_column: str,
    vs_prev_month_column: str,
) -> dict[str, list[str]]:
    """Lỗi ở một dòng người bán của Summary."""
    defects: dict[str, list[str]] = {}

    products = values.get(products_column)
    # A1 — số lượng sản phẩm phải là số nguyên; phần lẻ là dấu vết của việc
    # trừ một tỉ lệ phần trăm khỏi một số đếm.
    if isinstance(products, Decimal) and products != products.to_integral_value():
        _add(defects, products_column, A1_NON_INTEGER_PRODUCTS)

    if seller_label:
        for column, formula in formulas.items():
            match = sheet_reference(formula)
            if match is None:
                continue
            parsed = split_sheet_label(match.group("sheet"))
            # A4 — nhãn dòng nói người này, ô lại lấy số của sheet người khác.
            if parsed is not None and parsed[1] != seller_label:
                _add(defects, column, A4_CROSS_SHEET_LABEL_MISMATCH)

    formula = formulas.get(vs_prev_month_column, "")
    # A6 — so kỳ trước bằng số cứng gõ tay, không truy ngược được về kỳ nào.
    if formula and CONSTANT_DENOMINATOR.match(formula):
        _add(defects, vs_prev_month_column, A6_HARDCODED_DENOMINATOR)

    return defects


def detect_month_total_defects(formulas: dict[str, str]) -> dict[str, list[str]]:
    """A2 — các cột của cùng một dòng tổng tháng cộng trên khoảng khác nhau."""
    spans = {
        column: span
        for column, formula in formulas.items()
        if (span := sum_span(formula)) is not None
    }
    if len(spans) < 2:
        return {}
    widest = max(span[1] - span[0] for span in spans.values())
    defects: dict[str, list[str]] = {}
    for column, span in spans.items():
        if span[1] - span[0] < widest:
            _add(defects, column, A2_MONTH_TOTAL_MISSING_ROWS)
    return defects
