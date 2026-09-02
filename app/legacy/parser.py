"""Đọc workbook "Báo cáo Kinh doanh" cũ thành bản ghi bất biến.

Module thuần openpyxl: KHÔNG biết database tồn tại, KHÔNG gọi mạng, KHÔNG
tính lại bất kỳ con số nào. Giá trị ô đi thẳng vào bản ghi; công thức được
giữ nguyên văn ở ``formula_text`` để audit; chỗ công thức tự mâu thuẫn được
gắn mã ở ``known_defects`` (xem ``app/legacy/defects.py``) mà KHÔNG đụng tới
giá trị.

Phân loại dòng của Summary hoàn toàn theo cấu trúc công thức quan sát được
(``docs/analysis/02_FORMULA_MAPPING.md`` §3) chứ không theo vị trí dòng cố
định — số dòng người bán mỗi tháng thay đổi (tháng 03.2026 có thêm "Linh"),
nên mọi offset cứng đều sai ở kỳ nào đó.
"""

from __future__ import annotations

import hashlib
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable, Optional

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

from app.legacy import defects as defect_rules
from app.legacy.models import (
    SUMMARY_COLUMN_FIELDS, DailySales, LegacyWorkbook, MonthlyReference,
    SummaryRow,
)

# Phạm vi import production của PRA-001 — thẩm quyền Owner (DEC-169).
#
# `Summary 2026` và `DataChart 2026` là REQUIRED_IMPORT: nguồn dữ liệu
# production, phải nhập đủ và đúng.
#
# `Summary 2025` là REFERENCE_ONLY: trong workbook cũ nó tồn tại để làm số
# tham chiếu cho báo cáo 2026, KHÔNG phải nguồn dữ liệu production. Nó nằm
# NGOÀI authoritative import scope: không parse, không persist, không query.
#
# Đây là ranh giới scope do Owner xác lập, KHÔNG phải parser bug và cũng
# KHÔNG phải "nuốt lỗi". Real Data Acceptance trên workbook thật cho thấy
# `Summary 2025` đã bị dán cứng thành giá trị tĩnh (0 ô công thức trên toàn
# sheet, 99 dòng value-only), nên contract phân loại dòng theo cấu trúc
# công thức không áp dụng được cho nó — và Owner xác nhận không cần áp
# dụng. Guard DEC-168 vẫn nguyên vẹn cho các sheet REQUIRED_IMPORT: một
# dòng có giá trị nghiệp vụ mà contract không phân loại được vẫn FAIL TO.
SUMMARY_IMPORT_SHEETS = ("Summary 2026",)
SUMMARY_REFERENCE_ONLY_SHEETS = ("Summary 2025",)
DATACHART_SHEET = "DataChart 2026"
REQUIRED_SHEETS = SUMMARY_IMPORT_SHEETS + (DATACHART_SHEET,)

PRODUCTS_COLUMN = "D"
VS_PREV_MONTH_COLUMN = "I"
# Vùng nhãn nằm bên trái cột dữ liệu đầu tiên (C). Nhãn người bán được lấy
# NGUYÊN VĂN từ đây — không chuẩn hoá, không map sang tên nhân viên của
# pipeline (legacy và pipeline là hai origin tách biệt).
LABEL_COLUMNS = ("A", "B")

ROW_KIND_SELLER = "SELLER"
ROW_KIND_MONTH_TOTAL = "MONTH_TOTAL"
ROW_KIND_YEAR_TOTAL = "YEAR_TOTAL"
ROW_KIND_PROGRESS = "PROGRESS"

# Vùng DataChart 2026 theo docs/analysis/02_FORMULA_MAPPING.md §5.
DATACHART_FIRST_ROW = 3
DATACHART_MONTHS = 12
DATACHART_DAY_COLUMNS = tuple(get_column_letter(index) for index in range(2, 33))
DATACHART_MONTH_TOTAL = "AG"
DATACHART_PREV_YEAR = "AH"
DATACHART_VS_LAST_YEAR = "AI"
DATACHART_VS_TARGET = "AJ"
DATACHART_TARGET_YEAR_CELL = "J15"
DATACHART_TARGET_PER_DAY_CELL = "P15"

YEAR_IN_SHEET_NAME = re.compile(r"(20\d{2})")
SAME_SHEET_RATIO = re.compile(r"^=\s*[A-Z]+\$?\d+\s*/\s*\$?[A-Z]+\$?\d+\s*$")


class LegacyImportError(ValueError):
    """Workbook không đúng hình dạng đã freeze cho import legacy."""


def row_has_business_values(values: dict[str, object]) -> bool:
    """Dòng có ít nhất một số ở CỘT DỮ LIỆU đã freeze của Summary.

    Chỉ xét các cột trong ``SUMMARY_COLUMN_FIELDS`` — vùng nhãn (A–B) chứa
    chữ và đôi khi cả số điều hành (số ngày trong năm), không phải giá trị
    nghiệp vụ của một dòng người bán.
    """
    return any(
        isinstance(values.get(column), (int, float))
        and not isinstance(values.get(column), bool)
        for column in SUMMARY_COLUMN_FIELDS
    )


# Kích thước khối đọc file khi băm — hằng số I/O, không phải số nghiệp vụ.
# Viết thành hằng số để bất biến "không có phép tính nào trong app/legacy"
# kiểm chứng được bằng AST (xem tests/test_legacy_importer.py).
FINGERPRINT_CHUNK_BYTES = 1_048_576


def fingerprint_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(FINGERPRINT_CHUNK_BYTES), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _as_decimal(value) -> Optional[Decimal]:
    """Giữ nguyên giá trị ô dưới dạng Decimal; mọi thứ không phải số → None.

    Dùng ``str(value)`` để Decimal mang đúng con số Excel hiển thị, không
    kéo theo sai số nhị phân của float.
    """
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, (int, Decimal)):
        return Decimal(value)
    if isinstance(value, float):
        try:
            return Decimal(str(value))
        except InvalidOperation:
            return None
    return None


def _label(value_row: dict[str, object]) -> Optional[str]:
    """Nhãn = ô chữ gần cột dữ liệu nhất trong vùng nhãn, giữ nguyên văn."""
    for column in reversed(LABEL_COLUMNS):
        value = value_row.get(column)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _classify(formulas: dict[str, str]) -> Optional[str]:
    has_cross_sheet = any(defect_rules.sheet_reference(f) for f in formulas.values())
    if has_cross_sheet:
        return ROW_KIND_SELLER
    if any(defect_rules.is_halving_sum(f) for f in formulas.values()):
        return ROW_KIND_YEAR_TOTAL
    if any(defect_rules.sum_span(f) is not None for f in formulas.values()):
        return ROW_KIND_MONTH_TOTAL
    if any(SAME_SHEET_RATIO.match(f) for f in formulas.values()):
        return ROW_KIND_PROGRESS
    return None


def _period_from_formulas(formulas: dict[str, str]) -> Optional[tuple[int, int]]:
    """(year, month) suy từ tên sheet nguồn mà dòng người bán tham chiếu tới."""
    for formula in formulas.values():
        match = defect_rules.sheet_reference(formula)
        if match is None:
            continue
        sheet = match.group("sheet")
        parsed = defect_rules.split_sheet_label(sheet)
        if parsed is None:
            continue
        month_text = sheet.strip().split(".", 1)[0]
        try:
            return parsed[0], int(month_text)
        except ValueError:
            continue
    return None


def _sheet_year(sheet_name: str) -> Optional[int]:
    match = YEAR_IN_SHEET_NAME.search(sheet_name)
    return int(match.group(1)) if match else None


def _read_rows(value_sheet, formula_sheet, columns: Iterable[str]):
    columns = tuple(columns)
    for row_index in range(1, (value_sheet.max_row or 0) + 1):
        values = {c: value_sheet[f"{c}{row_index}"].value for c in columns}
        formulas = {}
        for column in columns:
            raw = formula_sheet[f"{column}{row_index}"].value
            if isinstance(raw, str) and raw.startswith("="):
                formulas[column] = raw
        yield row_index, values, formulas


def _parse_summary_sheet(value_sheet, formula_sheet) -> list[SummaryRow]:
    sheet_name = value_sheet.title
    sheet_year = _sheet_year(sheet_name)
    columns = LABEL_COLUMNS + tuple(SUMMARY_COLUMN_FIELDS)
    rows: list[SummaryRow] = []
    last_period: Optional[tuple[int, int]] = None
    unaccounted: list[int] = []

    for row_index, raw_values, formulas in _read_rows(value_sheet, formula_sheet, columns):
        row_kind = _classify(formulas)
        if row_kind is None:
            # Dòng KHÔNG khớp contract phân loại. Nếu nó vẫn mang giá trị
            # nghiệp vụ thì đây là dữ liệu của Owner mà importer không có
            # thẩm quyền diễn giải — ghi lại để báo to ở cuối sheet, TUYỆT
            # ĐỐI không đoán `row_kind` từ việc "dòng có số" (DEC-168).
            if row_has_business_values(raw_values):
                unaccounted.append(row_index)
            continue
        values = {
            field: _as_decimal(raw_values.get(column))
            for column, field in SUMMARY_COLUMN_FIELDS.items()
        }
        cell_values = {c: _as_decimal(raw_values.get(c)) for c in SUMMARY_COLUMN_FIELDS}
        seller_label = _label(raw_values)

        if row_kind == ROW_KIND_SELLER:
            period = _period_from_formulas(formulas)
            if period is not None:
                last_period = period
            year, month = period if period is not None else (sheet_year, None)
            row_defects = defect_rules.detect_seller_defects(
                seller_label=seller_label,
                values=cell_values,
                formulas=formulas,
                products_column=PRODUCTS_COLUMN,
                vs_prev_month_column=VS_PREV_MONTH_COLUMN,
            )
        elif row_kind == ROW_KIND_MONTH_TOTAL:
            # Dòng tổng đóng khối tháng ngay phía trên nó — kỳ của khối đó.
            year, month = last_period if last_period else (sheet_year, None)
            row_defects = defect_rules.detect_month_total_defects(formulas)
        else:
            # YEAR_TOTAL / PROGRESS: cấp năm, không thuộc một tháng nào.
            year, month, row_defects = sheet_year, None, {}

        if year is None:
            raise LegacyImportError(
                f"Không xác định được năm cho dòng {row_index} của sheet "
                f"'{sheet_name}' (tên sheet không chứa năm và dòng không tham "
                "chiếu sheet nguồn nào)."
            )
        rows.append(SummaryRow(
            year=year, month=month, seller_label=seller_label, row_kind=row_kind,
            sheet_name=sheet_name, sheet_row=row_index, values=values,
            formula_text=dict(formulas), known_defects=row_defects,
        ))

    if unaccounted:
        # FAIL LOUDLY (DEC-168). Bỏ qua im lặng một dòng có số nghĩa là báo
        # cáo hiển thị thiếu số của Owner mà không ai biết — đúng kiểu sai
        # âm thầm mà cả task này tồn tại để ngăn.
        preview = ", ".join(str(index) for index in unaccounted[:20])
        more = f" (và {len(unaccounted) - 20} dòng nữa)" if len(unaccounted) > 20 else ""
        raise LegacyImportError(
            f"Sheet '{sheet_name}': {len(unaccounted)} dòng có giá trị nghiệp vụ "
            f"nhưng không khớp contract phân loại dòng — dòng {preview}{more}. "
            "Importer KHÔNG đoán ý nghĩa dòng từ việc dòng có số. Đây là "
            "UNKNOWN / OWNER_DECISION_REQUIRED: cần Owner xác nhận ý nghĩa "
            "các dòng này trước khi mở rộng contract."
        )
    return rows


def _parse_datachart(value_sheet, formula_sheet):
    sheet_name = value_sheet.title
    year = _sheet_year(sheet_name)
    if year is None:
        raise LegacyImportError(f"Sheet '{sheet_name}' không chứa năm trong tên.")

    def _formula(cell: str) -> Optional[str]:
        raw = formula_sheet[cell].value
        return raw if isinstance(raw, str) and raw.startswith("=") else None

    target_year = _as_decimal(value_sheet[DATACHART_TARGET_YEAR_CELL].value)
    target_per_day = _as_decimal(value_sheet[DATACHART_TARGET_PER_DAY_CELL].value)

    daily: list[DailySales] = []
    monthly: list[MonthlyReference] = []
    for offset in range(DATACHART_MONTHS):
        row_index = DATACHART_FIRST_ROW + offset
        month = offset + 1
        for day_offset, column in enumerate(DATACHART_DAY_COLUMNS, start=1):
            amount = _as_decimal(value_sheet[f"{column}{row_index}"].value)
            # Ô trống = ngày chưa có số, KHÔNG phải doanh số 0. Không lưu
            # dòng rỗng để trạng thái rỗng trên UI vẫn trung thực.
            if amount is None:
                continue
            daily.append(DailySales(
                year=year, month=month, day=day_offset,
                sales_vnd=amount, source_sheet=sheet_name,
            ))
        formula_text = {
            column: formula
            for column in (DATACHART_MONTH_TOTAL, DATACHART_VS_LAST_YEAR, DATACHART_VS_TARGET)
            if (formula := _formula(f"{column}{row_index}")) is not None
        }
        monthly.append(MonthlyReference(
            year=year, month=month,
            sales_current_year_vnd=_as_decimal(value_sheet[f"{DATACHART_MONTH_TOTAL}{row_index}"].value),
            sales_prev_year_vnd=_as_decimal(value_sheet[f"{DATACHART_PREV_YEAR}{row_index}"].value),
            vs_last_year_ratio=_as_decimal(value_sheet[f"{DATACHART_VS_LAST_YEAR}{row_index}"].value),
            vs_target_ratio=_as_decimal(value_sheet[f"{DATACHART_VS_TARGET}{row_index}"].value),
            target_year=target_year, target_per_day=target_per_day,
            formula_text=formula_text,
        ))
    return daily, monthly


def parse_workbook(path: Path) -> LegacyWorkbook:
    """Đọc các sheet REQUIRED_IMPORT đã freeze. Thiếu sheet → lỗi rõ.

    Sheet REFERENCE_ONLY (``SUMMARY_REFERENCE_ONLY_SHEETS``) KHÔNG được đọc
    ở đây và KHÔNG xuất hiện trong ``sheets_imported`` — chúng nằm ngoài
    authoritative import scope theo DEC-169. Sự vắng mặt của chúng trong
    kết quả là có chủ đích và kiểm chứng được, không phải bỏ sót.
    """
    path = Path(path)
    values_wb = load_workbook(path, data_only=True, read_only=False)
    formulas_wb = load_workbook(path, data_only=False, read_only=False)
    try:
        missing = [name for name in REQUIRED_SHEETS if name not in values_wb.sheetnames]
        if missing:
            raise LegacyImportError(
                "Workbook thiếu sheet bắt buộc cho import legacy: "
                + ", ".join(missing)
            )
        summary_rows: list[SummaryRow] = []
        # Chỉ duyệt sheet REQUIRED_IMPORT. Sheet REFERENCE_ONLY không đi qua
        # đây, nên không có đường nào để nó lọt vào bản ghi production.
        for name in SUMMARY_IMPORT_SHEETS:
            summary_rows.extend(_parse_summary_sheet(values_wb[name], formulas_wb[name]))
        daily, monthly = _parse_datachart(
            values_wb[DATACHART_SHEET], formulas_wb[DATACHART_SHEET],
        )
        sheets_imported = [
            {"sheet_name": name, "state": values_wb[name].sheet_state}
            for name in REQUIRED_SHEETS
        ]
    finally:
        values_wb.close()
        formulas_wb.close()

    return LegacyWorkbook(
        source_file_name=path.name,
        file_fingerprint=fingerprint_file(path),
        file_size=path.stat().st_size,
        sheets_imported=sheets_imported,
        summary_rows=summary_rows,
        daily_sales=daily,
        monthly_reference=monthly,
    )
