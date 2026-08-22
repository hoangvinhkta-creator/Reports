"""Verify the ADS lead-source rule at OrderID level, spec sections 5, 13 and 29.

Two things are checked:

1. The 8 test cases from spec section 29, against a synthetic order set. This
   proves the rule behaves as specified before any of it reaches the engine.
2. The real raw sales book, to report how many orders the rule actually matches
   today — a number that is currently zero and must not be mistaken for a bug.

Usage:
    python tools/analysis/verify_ads_rule.py [--raw data/samples/So_chi_tiet_ban_hang.xlsx]
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from collections import defaultdict
from pathlib import Path

PERSONAL = "PERSONAL"
TINPHAT_ADS = "TINPHAT_ADS"

# Configuration, not code. Mirrors config/lead_source.yaml.
ADS_KEYWORDS = ("ADS",)
DEFAULT_LEAD_SOURCE = PERSONAL

# Per-employee default, overriding DEFAULT_LEAD_SOURCE. Mirrors the
# default_lead_source field of config/employees.yaml.
#
# "Tín Phát" is the company's own site/ads account: every order it raises is a
# company-generated lead and converts at the ADS rate whether or not anyone
# types the keyword (DEC-009).
EMPLOYEE_DEFAULT_LEAD_SOURCE = {
    "Tín Phát": TINPHAT_ADS,
}


def normalize_text(value) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", str(value))).strip()


def line_contains_ads(note) -> bool:
    upper = normalize_text(note).upper()
    return any(keyword in upper for keyword in ADS_KEYWORDS)


def classify_order(
    notes: list,
    manual_override: str | None = None,
    employee: str | None = None,
) -> tuple[str, str]:
    """Return (lead_source, source_of_value) for one OrderID.

    Priority per spec section 7, extended by DEC-009 with an employee-level
    default: manual override, then the ADS rule, then the employee default,
    then the global default. The ADS rule matches on ANY line of the order.

    The employee default sits below the ADS rule but above the global default,
    so it can only ever raise an order to ADS — never demote one the rule
    matched.
    """
    if manual_override:
        return manual_override, "Manual"
    if any(line_contains_ads(note) for note in notes):
        return TINPHAT_ADS, "Auto:ADS Rule"
    employee_default = EMPLOYEE_DEFAULT_LEAD_SOURCE.get(employee)
    if employee_default:
        return employee_default, f"Auto:Employee Default ({employee})"
    return DEFAULT_LEAD_SOURCE, "Auto:Default"


# (label, notes, manual_override, employee, expected)
CASES = [
    ("1  Một order 1 dòng, ghi chú 'ADS'",
     ["ADS"], None, TINPHAT_ADS),
    ("2  Ghi chú 'ads facebook'",
     ["ads facebook"], None, TINPHAT_ADS),
    ("3  Ghi chú 'Đơn Ads web'",
     ["Đơn Ads web"], None, TINPHAT_ADS),
    ("4  Order 4 dòng, dòng 3 có 'ADS', còn lại trống",
     ["", "", "ADS", ""], None, TINPHAT_ADS),
    ("5  Không dòng nào có ADS",
     ["Giao lắp sáng mai", "Chi phí vận chuyển"], None, PERSONAL),
    ("6  Rule auto = ADS nhưng user override PERSONAL",
     ["KH ADS"], PERSONAL, PERSONAL),
    ("7  User reset override",
     ["KH ADS"], None, TINPHAT_ADS),
    ("8a Nhân viên có đơn ADS trong tháng",
     ["  ADS  "], None, TINPHAT_ADS),
    ("8b Cùng nhân viên, đơn không ADS",
     ["Bán hàng Vanoka"], None, PERSONAL),
]

EXTRA_CASES = [
    ("9  Chữ thường hoàn toàn",       ["đơn ads"],            None, TINPHAT_ADS),
    ("10 Khoảng trắng thừa",          ["ĐƠN    ADS    WEB"],  None, TINPHAT_ADS),
    ("11 Ghi chú None",               [None, None],           None, PERSONAL),
    ("12 Override sang ADS khi auto = PERSONAL",
                                      ["Bán hàng"],   TINPHAT_ADS, TINPHAT_ADS),
]

# DEC-009 — employee-level default. Fifth element is the employee.
EMPLOYEE_CASES = [
    ("13 Tín Phát, ghi chú mặc định ERP, không có ADS",
     ["Bán hàng Vanoka"], None, "Tín Phát", TINPHAT_ADS),
    ("14 Tín Phát, ghi chú có ADS",
     ["Đơn ADS web"], None, "Tín Phát", TINPHAT_ADS),
    ("15 Tín Phát, quản lý override về PERSONAL",
     ["Bán hàng Vanoka"], PERSONAL, "Tín Phát", PERSONAL),
    ("16 Ly, ghi chú mặc định ERP — không ăn theo Tín Phát",
     ["Bán hàng Vanoka"], None, "Ly", PERSONAL),
    ("17 Ly, ghi chú có ADS",
     ["KH ADS"], None, "Ly", TINPHAT_ADS),
]


def run_cases() -> int:
    failures = 0
    cases = [(*case, None) for case in CASES + EXTRA_CASES]
    cases = [
        (label, notes, override, employee, expected)
        for label, notes, override, expected, employee in cases
    ] + EMPLOYEE_CASES

    print("Spec section 29 — minimum test cases for the ADS rule")
    print("-" * 90)
    for label, notes, override, employee, expected in cases:
        actual, source = classify_order(notes, override, employee)
        ok = actual == expected
        failures += not ok
        print(f"  [{'PASS' if ok else 'FAIL'}] {label:52} -> {actual:12} ({source})")
    print("-" * 90)
    print(f"  {len(cases) - failures}/{len(cases)} passed\n")
    return failures


def scan_raw(path: Path) -> None:
    import openpyxl

    workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    sheet = workbook.active
    orders: dict[str, list] = defaultdict(list)
    for row in sheet.iter_rows(min_row=6, values_only=True):
        if row[1]:
            orders[str(row[1]).strip()].append(row[2])
    workbook.close()

    matched = [
        order_id for order_id, notes in orders.items()
        if classify_order(notes)[0] == TINPHAT_ADS
    ]
    # Scanned without employee context: this counts keyword matches only, not
    # the employee-level default from DEC-009.
    print(f"Real raw file — {path.name}")
    print("-" * 78)
    print(f"  distinct orders           : {len(orders)}")
    print(f"  classified TINPHAT_ADS    : {len(matched)}")
    print(f"  classified PERSONAL       : {len(orders) - len(matched)}")
    if not matched:
        print()
        print("  The keyword does not appear anywhere in this file. That is the")
        print("  expected result for data entered before the ADS convention, not")
        print("  a defect in the rule. See docs/analysis/06_ADS_RULE_VERIFICATION.md.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=None)
    args = parser.parse_args()

    failures = run_cases()
    if args.raw and args.raw.exists():
        scan_raw(args.raw)
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
