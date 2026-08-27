"""Helper TEST-ONLY để dựng provenance — ngoài production API.

`AffectedRow` là sealed: đường duy nhất tạo nó là `AffectedRow.from_line()`,
tức là từ một dòng thô có thật. Đó chính là điều đóng lớp lỗi "provenance bịa
được" (Audit P5).

Test vẫn cần dựng dòng theo ý muốn, nên helper này dựng một `WorkingLine`
**thật** rồi đi qua đúng factory đó. Nó KHÔNG phá seal và KHÔNG mở bypass
production — nó chỉ cung cấp đầu vào hợp lệ.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from app.modules.importing.normalizer import normalize_line
from app.modules.validation.models import AffectedRow, RowProvenance
from tests.factories import make_raw_row


def line_for(
    source_row: int,
    employee_raw: Optional[str] = "Vũ Hạnh Ly 0868345633",
    when: Optional[date] = date(2026, 1, 15),
    source_file: str = "synthetic_raw_sample.xlsx",
):
    line = normalize_line(
        make_raw_row(source_row=source_row, employee_raw=employee_raw, date_=when)
    )
    object.__setattr__(line.raw, "source_file", source_file)
    return line


def affected(source_row: int, employee_raw: Optional[str] = "Ly",
             when: Optional[date] = None,
             source_file: str = "synthetic_raw_sample.xlsx") -> AffectedRow:
    return AffectedRow.from_line(line_for(source_row, employee_raw, when, source_file))


def provenance(*source_rows: int, batch_scoped: bool = False) -> RowProvenance:
    rows = tuple(affected(r) for r in source_rows)
    return RowProvenance.batch(rows) if batch_scoped else RowProvenance.of(rows)
