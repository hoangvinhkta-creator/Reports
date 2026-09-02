"""Đối chiếu từng ô Excel legacy với bản ghi trong history DB (CHECK-PRA001-01).

Đây là bằng chứng E1 cho fidelity trên FILE THẬT: script đọc lại workbook
bằng openpyxl ``data_only=True`` và so từng ô số của ``Summary 2026``,
``Summary 2025``, ``DataChart 2026`` với giá trị đã lưu, rồi in
``matched=N mismatched=0``. Script KHÔNG sửa gì — nó chỉ đọc.

Cách chạy (workbook thật KHÔNG commit vào repo):

    HISTORY_DATABASE_URL=... python3 -m tools.analysis.verify_legacy_import \\
        "/duong/dan/Bao cao Kinh doanh 2026.xlsx" [LEG-...]

Thoát 0 khi mismatched = 0; thoát 1 khi có bất kỳ ô nào lệch.
"""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

from openpyxl import load_workbook

import tools.db as history_db
from app.legacy.models import SUMMARY_COLUMN_FIELDS
from app.legacy.parser import (
    DATACHART_DAY_COLUMNS, DATACHART_FIRST_ROW, DATACHART_SHEET, SUMMARY_SHEETS,
)
from app.web import history_store


def _decimal(value):
    if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
        return None
    return Decimal(str(value))


def verify(workbook_path: Path, repository, import_id=None) -> tuple[int, list[str]]:
    sheets = load_workbook(workbook_path, data_only=True)
    matched, mismatches = 0, []

    stored_summary = {}
    for year in {int(name.split()[-1]) for name in SUMMARY_SHEETS}:
        for row in repository.query_summary(year, import_id=import_id):
            stored_summary[(row["sheet_name"], row["sheet_row"])] = row
    for key, row in stored_summary.items():
        sheet_name, sheet_row = key
        sheet = sheets[sheet_name]
        for column, field in SUMMARY_COLUMN_FIELDS.items():
            expected = _decimal(sheet[f"{column}{sheet_row}"].value)
            actual = row[field]
            if actual == expected:
                matched += 1
            else:
                mismatches.append(f"{sheet_name}!{column}{sheet_row}: excel={expected} db={actual}")

    chart = sheets[DATACHART_SHEET]
    year = int(DATACHART_SHEET.split()[-1])
    for month in range(1, 13):
        sheet_row = DATACHART_FIRST_ROW + month - 1
        stored = {row["day"]: row["sales_vnd"]
                  for row in repository.query_daily(year, month, import_id=import_id)}
        for day, column in enumerate(DATACHART_DAY_COLUMNS, start=1):
            expected = _decimal(chart[f"{column}{sheet_row}"].value)
            actual = stored.get(day)
            if actual == expected:
                matched += 1
            else:
                mismatches.append(f"{DATACHART_SHEET}!{column}{sheet_row}: excel={expected} db={actual}")
    return matched, mismatches


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    workbook_path = Path(argv[0])
    import_id = argv[1] if len(argv) > 1 else None
    repository = history_store.build(engine=history_db.build_engine())
    matched, mismatches = verify(workbook_path, repository, import_id)
    for line in mismatches:
        print(f"MISMATCH {line}")
    print(f"matched={matched} mismatched={len(mismatches)}")
    return 0 if not mismatches else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
