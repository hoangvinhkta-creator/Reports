"""Trình bày số cũ trên web — định dạng và GẮN NHÃN, không tính toán.

Hai quy tắc bất di bất dịch của tầng này (TASK-PRA-001 §8, §19):

1. Không có phép tính nào trên giá trị nghiệp vụ. Số hiển thị là số đã lưu;
   hàm ở đây chỉ đổi cách VIẾT nó ra (dấu phân cách nghìn kiểu vi-VN, tỉ lệ
   viết dạng phần trăm) chứ không đổi số.
2. Không có con số legacy nào được phép xuất hiện mà thiếu nhãn nguồn và
   đơn vị. Ô có lỗi công thức đã biết mang thêm dấu nhắc mã A1/A2/A4/A6.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from app.legacy.models import SUMMARY_COLUMN_FIELDS

ORIGIN_BADGE = "LEGACY"
ORIGIN_TITLE = "Số cũ từ workbook Excel, giữ nguyên trạng — không do pipeline tính lại"

UNIT_LABELS = {
    "kvnd": "nghìn đồng (số cũ)",
    "vnd": "đồng (số cũ)",
    "count": "số lượng (số cũ)",
    "ratio": "tỉ lệ (số cũ)",
}

DEFECT_LABELS = {
    "A1": "A1 — số SP bị trừ nhầm một tỉ lệ phần trăm nên không nguyên",
    "A2": "A2 — dòng tổng tháng cộng thiếu người bán so với cột khác",
    "A4": "A4 — ô lấy số từ sheet của người bán khác",
    "A6": "A6 — so kỳ trước bằng số cứng gõ tay, không truy ngược được",
}

ROW_KIND_LABELS = {
    "SELLER": "Người bán",
    "MONTH_TOTAL": "Tổng tháng",
    "YEAR_TOTAL": "Tổng năm",
    "PROGRESS": "Tiến độ",
}

# Ma trận Nhân viên: (trường, nhãn cột, kiểu đơn vị).
MATRIX_COLUMNS: tuple[tuple[str, str, str], ...] = (
    ("orders", "Tổng đơn", "count"),
    ("products", "Tổng số SP", "count"),
    ("sales", "Tổng bán", "kvnd"),
    ("converted_revenue", "DS quy đổi", "kvnd"),
    ("profit", "Tổng lợi nhuận", "kvnd"),
    ("vs_prev_month_ratio", "So tháng trước", "ratio"),
    ("target", "Target", "kvnd"),
    ("vs_target_ratio", "So target", "ratio"),
)

# Ngược ánh xạ cột Excel → trường, để tra lỗi công thức đã annotate theo ĐÚNG ô.
FIELD_TO_COLUMN = {field: column for column, field in SUMMARY_COLUMN_FIELDS.items()}


def format_number(value: Optional[Decimal]) -> str:
    """1.240.500 · 87,6 — quy ước vi-VN. Ô trống hiện dấu gạch, không hiện 0."""
    if value is None:
        return "—"
    text = format(value.normalize() if isinstance(value, Decimal) else value, "f")
    negative = text.startswith("-")
    text = text.lstrip("-")
    whole, _, fraction = text.partition(".")
    grouped = f"{int(whole):,}".replace(",", ".")
    result = f"{grouped},{fraction}" if fraction else grouped
    return f"-{result}" if negative else result


def format_ratio(value: Optional[Decimal]) -> str:
    """Tỉ lệ viết dạng phần trăm. ``Decimal.scaleb(2)`` là dịch dấu phẩy —
    cách VIẾT khác của cùng con số, không phải một phép tính nghiệp vụ."""
    if value is None:
        return "—"
    return f"{format_number(value.scaleb(2))}%"


def format_cell(value: Optional[Decimal], unit_kind: str) -> str:
    return format_ratio(value) if unit_kind == "ratio" else format_number(value)


def cell(row: dict, field: str, unit_kind: str) -> dict:
    """Một ô hiển thị: giá trị đã định dạng + đơn vị + mã lỗi của đúng ô đó."""
    defects = (row.get("known_defects") or {}).get(FIELD_TO_COLUMN.get(field, ""), [])
    return {
        "text": format_cell(row.get(field), unit_kind),
        "empty": row.get(field) is None,
        "unit": UNIT_LABELS[unit_kind],
        "defects": [{"code": code, "label": DEFECT_LABELS.get(code, code)} for code in defects],
    }


def matrix(rows: list[dict]) -> list[dict]:
    """Ma trận người bán × chỉ tiêu cho một kỳ, giữ nguyên thứ tự dòng Excel."""
    return [
        {
            "seller_label": row.get("seller_label") or "—",
            "row_kind": row.get("row_kind"),
            "row_kind_label": ROW_KIND_LABELS.get(row.get("row_kind"), row.get("row_kind")),
            "sheet_name": row.get("sheet_name"),
            "sheet_row": row.get("sheet_row"),
            "cells": [cell(row, field, unit_kind) for field, _, unit_kind in MATRIX_COLUMNS],
        }
        for row in rows
    ]


def daily_grid(rows: list[dict]) -> list[dict]:
    return [
        {
            "day": row["day"],
            "cell": cell({"sales_vnd": row.get("sales_vnd")}, "sales_vnd", "vnd"),
        }
        for row in rows
    ]


def period_label(year: int, month: Optional[int]) -> str:
    return f"Tháng {month:02d}/{year}" if month else f"Năm {year}"


# Tham chiếu tháng của DataChart: (trường, kiểu đơn vị).
MONTHLY_FIELDS: tuple[tuple[str, str], ...] = (
    ("sales_current_year_vnd", "vnd"),
    ("sales_prev_year_vnd", "vnd"),
    ("vs_last_year_ratio", "ratio"),
    ("vs_target_ratio", "ratio"),
    ("target_year", "vnd"),
    ("average_per_day", "vnd"),
    ("target_per_day", "vnd"),
)


def monthly_cells(row: Optional[dict]) -> dict[str, dict]:
    if row is None:
        return {}
    return {field: cell(row, field, unit_kind) for field, unit_kind in MONTHLY_FIELDS}


# ---------------------------------------------------------------------------
# PHB-04 — Legacy Reference V1.
#
# Kỳ tham chiếu năm trước đi qua ĐÚNG hàm ``cell()`` như mọi số cũ khác, nên
# nó thừa hưởng cùng một bảo đảm: không có con số nào hiện ra mà thiếu nhãn
# nguồn và đơn vị, và ô trống hiện dấu gạch chứ không phải ``0``.
# ---------------------------------------------------------------------------

def reference_rows(periods: list) -> list[dict]:
    """Bảng kỳ tham chiếu (một dòng mỗi tháng của năm trước)."""
    return [
        {
            "year": item.year,
            "month": item.month,
            "period_label": period_label(item.year, item.month),
            "available": item.available,
            "source": item.source,
            "derived_from": period_label(item.derived_from_year, item.derived_from_month),
            "cell": cell({item.metric_key: item.value}, item.metric_key, item.unit_kind),
        }
        for item in periods
    ]


def contract_rows(rules: tuple) -> list[dict]:
    """Bảng hợp đồng chỉ tiêu, viết ra nguyên văn cho chủ dự án đọc."""
    return [
        {
            "key": rule.key,
            "label": rule.label,
            "metric_class": rule.metric_class,
            "class_label": rule.class_label,
            "displayable": rule.displayable,
            "reason": rule.reason,
            "evidence": rule.evidence,
        }
        for rule in rules
    ]


def summary_year_rows(years: list, all_summary_rows: list[dict],
                      authority_by_year: dict = None,
                      current_import: dict = None) -> list[dict]:
    """Một khối cho mỗi NĂM lịch sử: kỳ nào có, ai có số, chỉ tiêu nào có.

    Tình trạng chỉ tiêu được đo trên chính dòng của năm đó (`DEC-177`), nên
    một năm nghèo dữ liệu không mượn được vẻ đầy đủ của năm khác. Mỗi năm
    cũng ghi rõ đang đọc từ NGUỒN NÀO (`DEC-178`).
    """
    from app.web import legacy_reference

    authority_by_year = authority_by_year or {}
    rows = []
    for year in years:
        year_rows = [r for r in all_summary_rows if r.get("year") == year.year]
        authority = authority_by_year.get(year.year)
        source = authority or current_import or {}
        rows.append({
            "source_file": source.get("source_file_name") or "—",
            "source_import_id": source.get("import_id") or "—",
            "source_authority": source.get("source_authority"),
            "source_authority_label": legacy_reference.source_authority_label(
                source.get("source_authority")),
            "is_authoritative": authority is not None,
            "deferred_detail_sheets": legacy_reference.deferred_detail_sheets(
                source.get("sheets_imported")),
            "year": year.year,
            "months": list(year.months),
            "sellers": list(year.sellers),
            "seller_rows": year.seller_rows,
            "total_rows": year.total_rows,
            "has_employee_detail": year.has_employee_detail,
            "metrics": [
                {
                    "label": item.rule.label,
                    "availability": item.availability,
                    "availability_label": item.availability_label,
                    "class_label": item.rule.class_label,
                    "filled_rows": item.filled_rows,
                }
                for item in legacy_reference.summary_year_availability(year_rows)
            ],
        })
    return rows
