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


def normalize_text(value) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", str(value))).strip()


def line_contains_ads(note) -> bool:
    upper = normalize_text(note).upper()
    return any(keyword in upper for keyword in ADS_KEYWORDS)


def classify_order(notes: list, manual_override: str | None = None) -> tuple[str, str]:
    """Return (lead_source, source_of_value) for one OrderID.

    Priority per spec section 7: manual override, then the ADS rule, then the
    default. The rule matches on ANY line of the order.
    """
    if manual_override:
        return manual_override, "Manual"
    if any(line_contains_ads(note) for note in notes):
        return TINPHAT_ADS, "Auto:ADS Rule"
    return DEFAULT_LEAD_SOURCE, "Auto:Default"


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


def run_cases() -> int:
    failures = 0
    print("Spec section 29 — minimum test cases for the ADS rule")
    print("-" * 78)
    for label, notes, override, expected in CASES + EXTRA_CASES:
        actual, source = classify_order(notes, override)
        ok = actual == expected
        failures += not ok
        print(f"  [{'PASS' if ok else 'FAIL'}] {label:52} -> {actual:12} ({source})")
    print("-" * 78)
    print(f"  {len(CASES) + len(EXTRA_CASES) - failures}/"
          f"{len(CASES) + len(EXTRA_CASES)} passed\n")
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
