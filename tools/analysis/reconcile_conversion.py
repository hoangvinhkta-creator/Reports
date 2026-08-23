"""Reconcile ConversionScheme resolution against the real reference workbook.

CHECK-108A1-14 and CHECK-108A1-15. Two independent checks:

1. **Column F of `Summary 2026`.** Every cell that applies a rate is a formula
   the report author wrote by hand. We parse the rate(s) out of each formula
   and ask the engine what rate it would resolve for that (employee, group,
   lead_source, product_group, period). The engine must agree.

   This works TODAY even though TASK-108B is blocked: `G` (profit) and `X`
   (the ADS share) come straight out of the workbook, so nothing here needs
   `EligibleKpiProfit`.

2. **Employee mapping on the full company raw export.** Every NVBH value must
   either map to a configured employee or come back flagged `unmapped`.

Real data files are never committed and are deleted after use (DEC-108).

Usage:
    python tools/analysis/reconcile_conversion.py --workbook <path> [--raw <path>]
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path

import openpyxl

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.modules.conversion.scheme_resolver import ConversionSchemeResolver  # noqa: E402
from app.modules.domain.models import ADS, DIEN_MAY, GIA_DUNG, PERSONAL  # noqa: E402
from app.modules.mapping.employee_mapper import EmployeeMapper  # noqa: E402

CONFIG = Path(__file__).resolve().parents[2] / "config"

# How each Summary row maps onto the engine's dimensions. The two channel rows
# are aggregates in the report, not people: "Nội thành" is the group's Điện máy
# side, "Gia dụng" its Gia dụng side. Linh and Fanpage are legacy names absent
# from master data on purpose (DEC-127 §8).
SUMMARY_ROWS = {
    "Ly":        ("Ly",       "STANDARD_SALES", DIEN_MAY),
    "Thắng":     ("Thắng",    "STANDARD_SALES", DIEN_MAY),
    "Tín Phát":  ("Tín Phát", "STANDARD_SALES", DIEN_MAY),
    "Hoàng":     ("Hoàng",    "STANDARD_SALES", DIEN_MAY),
    "Kiên":      ("Kiên",     "STANDARD_SALES", DIEN_MAY),
    "Nội thành": ("Vinh",     "NOI_THANH",      DIEN_MAY),
    "Gia dụng":  ("Vinh",     "NOI_THANH",      GIA_DUNG),
    "Linh":      (None,       None,             DIEN_MAY),
    "Fanpage":   (None,       None,             DIEN_MAY),
}


def norm(value) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", str(value))).strip()


def reconcile_summary(workbook: Path, resolver: ConversionSchemeResolver) -> int:
    wb = openpyxl.load_workbook(workbook, data_only=False)
    ws = wb["Summary 2026"]

    employee_at_row: dict[int, str] = {}
    period_at_row: dict[int, date] = {}
    current: date | None = None
    for row in ws.iter_rows(min_col=1, max_col=2):
        a, b = row[0].value, row[1].value
        if hasattr(a, "year"):
            current = a.date() if hasattr(a, "date") else a
        name = norm(b)
        if name and name != "Tiến độ":
            employee_at_row[row[1].row] = name
            if current:
                period_at_row[row[1].row] = current

    matched = unresolved_expected = mismatched = 0
    details: list[str] = []

    for cell in (c for r in ws.iter_rows(min_col=6, max_col=6) for c in r):
        formula = cell.value
        if not isinstance(formula, str) or not formula.startswith("="):
            continue
        if "SUM" in formula or "%" not in formula:
            continue
        name = employee_at_row.get(cell.row)
        as_of = period_at_row.get(cell.row)
        if not name or not as_of or name not in SUMMARY_ROWS:
            continue

        wanted = {Decimal(r) / 100 for r in re.findall(r"(\d+(?:\.\d+)?)%", formula)}
        employee, group, product_group = SUMMARY_ROWS[name]

        got: dict[str, Decimal] = {}
        for lead_source in (PERSONAL, ADS):
            res = resolver.resolve_auto(
                employee, group, lead_source, product_group, as_of
            )
            if res.rate is not None:
                got[lead_source] = res.rate

        label = f"{as_of:%m.%Y} {name:10} {cell.coordinate:5}"
        if employee is None:
            # Legacy name: absent from master data by decision. Whatever the
            # engine returns must come from the universal "*" row, never from
            # another employee's or group's row.
            reachable = set(got.values())
            if wanted <= reachable:
                unresolved_expected += 1
                details.append(
                    f"  [LEGACY] {label} formula={sorted(wanted)} "
                    f"-> engine trả {sorted(reachable)} qua dòng '*' "
                    "(không có master data, không mượn tỉ lệ của ai)"
                )
            else:
                mismatched += 1
                details.append(f"  [LỆCH ] {label} muốn {sorted(wanted)} "
                               f"nhưng engine cho {sorted(reachable)}")
            continue

        if wanted <= set(got.values()):
            matched += 1
        else:
            mismatched += 1
            details.append(
                f"  [LỆCH ] {label} workbook dùng {sorted(wanted)} "
                f"nhưng engine phân giải {got}"
            )

    wb.close()

    total = matched + unresolved_expected + mismatched
    print("=" * 78)
    print("CHECK-108A1-14 — Đối chiếu cột F, Summary 2026")
    print("=" * 78)
    print(f"  Tổng ô áp tỉ lệ            : {total}")
    print(f"  Khớp chính xác             : {matched}")
    print(f"  Legacy (ngoài master data) : {unresolved_expected}")
    print(f"  LỆCH                       : {mismatched}")
    if details:
        print()
        for line in details:
            print(line)
    print()
    return mismatched


def reconcile_raw(raw: Path, mapper: EmployeeMapper) -> int:
    wb = openpyxl.load_workbook(raw, read_only=True, data_only=True)
    mapped: Counter = Counter()
    groups: dict[str, str] = {}
    unmapped: Counter = Counter()
    for row in wb.active.iter_rows(min_row=6, values_only=True):
        if not row[1] or len(row) < 13 or not row[12]:
            continue
        when = row[0].date() if hasattr(row[0], "date") else row[0]
        result = mapper.resolve(norm(row[12]), when if isinstance(when, date) else None)
        if result.normalized:
            mapped[result.normalized] += 1
            groups[result.normalized] = result.group or "—"
        else:
            unmapped[norm(row[12])] += 1
    wb.close()

    print("=" * 78)
    print("CHECK-108A1-15 — Employee mapping trên file thô toàn công ty")
    print("=" * 78)
    print(f"  Dòng map được   : {sum(mapped.values())}")
    for name, count in mapped.most_common():
        print(f"      {name:10} {groups[name]:16} {count:6}")
    print(f"  Dòng KHÔNG map  : {sum(unmapped.values())}  -> Review Queue (C11)")
    for name, count in unmapped.most_common():
        print(f"      {name:34} {count}")
    print()
    # Not a failure: unmapped rows are the documented, intended outcome.
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workbook", type=Path, required=True)
    parser.add_argument("--raw", type=Path, default=None)
    args = parser.parse_args()

    resolver = ConversionSchemeResolver.from_yaml(CONFIG / "conversion_rates.yaml")
    failures = reconcile_summary(args.workbook, resolver)

    if args.raw and args.raw.exists():
        mapper = EmployeeMapper.from_yaml(CONFIG / "employees.yaml")
        failures += reconcile_raw(args.raw, mapper)

    print("KẾT QUẢ:", "PASS" if failures == 0 else f"FAIL ({failures} ô lệch)")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
