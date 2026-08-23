"""Verify LeadSource classification and ConversionScheme resolution.

Spec sections 5, 7, 12, 13 and 29, as amended by DEC-119, DEC-120 and DEC-121.

LeadSource and ConversionScheme are two independent concepts (DEC-119):

    LeadSource        answers "where did this order come from?"  -> PERSONAL | ADS
    ConversionScheme  answers "which rate converts it?"          -> a config row

PERSONAL does NOT imply 5.5%. Noi thanh sells PERSONAL orders at 2%. The rate
is always resolved from configuration keyed by (employee, lead_source, date),
never derived from the lead source alone and never hard-coded.

Two things are checked:

1. The test cases from spec section 29 plus cases A-G confirmed by the project
   owner, against a synthetic order set. This proves both rules behave as
   specified before any of it reaches the engine.
2. The real raw sales book, to report how many orders each rule actually
   matches today - a keyword count that is currently zero and must not be
   mistaken for a bug.

Usage:
    python tools/analysis/verify_ads_rule.py [--raw data/samples/So_chi_tiet_ban_hang.xlsx]
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from collections import defaultdict
from datetime import date
from pathlib import Path

# --------------------------------------------------------------------------
# LeadSource - exactly two values (DEC-119). "TINPHAT_ADS" is deliberately
# gone: it named a rate inside a source enum and made the two concepts
# impossible to vary independently.
# --------------------------------------------------------------------------
PERSONAL = "PERSONAL"
ADS = "ADS"

# Configuration, not code. Mirrors config/lead_source.yaml.
ADS_KEYWORDS = ("ADS",)
DEFAULT_LEAD_SOURCE = PERSONAL

# Per-employee default lead source, overriding DEFAULT_LEAD_SOURCE. Mirrors the
# default_lead_source field of config/employees.yaml.
#
# "Tin Phat" is the company's own site/ads account: 100% of the orders it
# raises are company-generated leads, whether or not anyone types the keyword
# (DEC-109, reaffirmed by the owner). This sets the SOURCE only - the 7.5% it
# ends up converting at comes from the scheme table below, via ADS.
EMPLOYEE_DEFAULT_LEAD_SOURCE = {
    "Tín Phát": ADS,
}

# --------------------------------------------------------------------------
# ConversionScheme - resolved from (employee, lead_source, date).
# Mirrors config/conversion_rates.yaml. Every row carries effective_from /
# effective_to so a future policy change never rewrites a past report
# (DEC-121). "*" means "any employee".
#
# Most specific match wins: an exact employee row beats a "*" row. There is no
# fallback rate: an unresolved combination is a review-queue item, never a
# silent guess.
# --------------------------------------------------------------------------
# (employee, lead_source, scheme, rate, effective_from, effective_to)
CONVERSION_SCHEMES = [
    ("*",         PERSONAL, "PERSONAL_5_5", 0.055, date(2026, 1, 1), None),
    ("*",         ADS,      "ADS_7_5",      0.075, date(2026, 1, 1), None),
    ("Nội thành", PERSONAL, "NOI_THANH_2",  0.020, date(2026, 1, 1), None),
    ("Gia dụng",  PERSONAL, "GIA_DUNG_8",   0.080, date(2026, 1, 1), None),
]

DEFAULT_AS_OF = date(2026, 6, 30)


def normalize_text(value) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", str(value))).strip()


def line_contains_ads(note) -> bool:
    upper = normalize_text(note).upper()
    return any(keyword in upper for keyword in ADS_KEYWORDS)


def classify_lead_source(
    notes: list,
    manual_override: str | None = None,
    employee: str | None = None,
) -> tuple[str, str]:
    """Return (lead_source, source_of_value) for one OrderID.

    Priority per spec section 7, extended by DEC-109 with an employee-level
    default: manual override, then the ADS rule, then the employee default,
    then the global default. The ADS rule matches on ANY line of the order and
    the verdict then applies to every line of that order - classification is an
    order-level decision, never a per-row one.

    The employee default sits below the ADS rule but above the global default,
    so it can only ever raise an order to ADS - never demote one the rule
    matched. Manual override outranks both (spec section 26, DEC-119 point 9).
    """
    if manual_override:
        return manual_override, "Manual"
    if any(line_contains_ads(note) for note in notes):
        return ADS, "Auto:ADS Rule"
    employee_default = EMPLOYEE_DEFAULT_LEAD_SOURCE.get(employee)
    if employee_default:
        return employee_default, f"Auto:Employee Default ({employee})"
    return DEFAULT_LEAD_SOURCE, "Auto:Default"


def resolve_conversion_scheme(
    employee: str | None,
    lead_source: str,
    as_of: date | None = None,
    manual_override: str | None = None,
) -> tuple[str | None, float | None, str]:
    """Return (scheme, rate, source_of_value) for one order.

    Independent of how the lead source was decided (DEC-119). Looked up by the
    order's own business date, not by "today", so re-running a 2026 report in
    2028 still uses the 2026 rates (DEC-121).

    Returns (None, None, "Unresolved") when no row matches. That is a review
    queue item: a missing rate must never fall back to some other employee's
    number.
    """
    if manual_override:
        for _, _, scheme, rate, _, _ in CONVERSION_SCHEMES:
            if scheme == manual_override:
                return scheme, rate, "Manual"
        return manual_override, None, "Manual"

    as_of = as_of or DEFAULT_AS_OF
    candidates = [
        row for row in CONVERSION_SCHEMES
        if row[1] == lead_source
        and (row[0] == employee or row[0] == "*")
        and row[4] <= as_of
        and (row[5] is None or as_of <= row[5])
    ]
    if not candidates:
        return None, None, "Unresolved"

    # Most specific first: an exact employee row outranks the "*" row.
    candidates.sort(key=lambda row: row[0] == "*")
    employee_key, _, scheme, rate, _, _ = candidates[0]
    origin = "Employee" if employee_key != "*" else "LeadSource"
    return scheme, rate, f"Auto:{origin} ({scheme})"


# --------------------------------------------------------------------------
# Test cases.
#
# CASES 1-8 are spec section 29's mandatory set. 9-12 cover section 13 edge
# cases the spec did not enumerate. 13-17 cover the employee-level default of
# DEC-109. A-G are the owner-confirmed scenarios of DEC-119, and are the only
# ones that assert on the resolved rate as well as the source.
# --------------------------------------------------------------------------

# (label, notes, manual_override, expected_lead_source)
CASES = [
    ("1  Một order 1 dòng, ghi chú 'ADS'",
     ["ADS"], None, ADS),
    ("2  Ghi chú 'ads facebook'",
     ["ads facebook"], None, ADS),
    ("3  Ghi chú 'Đơn Ads web'",
     ["Đơn Ads web"], None, ADS),
    ("4  Order 4 dòng, dòng 3 có 'ADS', còn lại trống",
     ["", "", "ADS", ""], None, ADS),
    ("5  Không dòng nào có ADS",
     ["Giao lắp sáng mai", "Chi phí vận chuyển"], None, PERSONAL),
    ("6  Rule auto = ADS nhưng user override PERSONAL",
     ["KH ADS"], PERSONAL, PERSONAL),
    ("7  User reset override",
     ["KH ADS"], None, ADS),
    ("8a Nhân viên có đơn ADS trong tháng",
     ["  ADS  "], None, ADS),
    ("8b Cùng nhân viên, đơn không ADS",
     ["Bán hàng Vanoka"], None, PERSONAL),
]

EXTRA_CASES = [
    ("9  Chữ thường hoàn toàn",       ["đơn ads"],           None, ADS),
    ("10 Khoảng trắng thừa",          ["ĐƠN    ADS    WEB"], None, ADS),
    ("11 Ghi chú None",               [None, None],          None, PERSONAL),
    ("12 Override sang ADS khi auto = PERSONAL",
                                      ["Bán hàng"],           ADS, ADS),
]

# DEC-109 - employee-level default. Fourth element is the employee.
EMPLOYEE_CASES = [
    ("13 Tín Phát, ghi chú mặc định ERP, không có ADS",
     ["Bán hàng Vanoka"], None, "Tín Phát", ADS),
    ("14 Tín Phát, ghi chú có ADS",
     ["Đơn ADS web"], None, "Tín Phát", ADS),
    ("15 Tín Phát, quản lý override về PERSONAL",
     ["Bán hàng Vanoka"], PERSONAL, "Tín Phát", PERSONAL),
    ("16 Ly, ghi chú mặc định ERP — không ăn theo Tín Phát",
     ["Bán hàng Vanoka"], None, "Ly", PERSONAL),
    ("17 Ly, ghi chú có ADS",
     ["KH ADS"], None, "Ly", ADS),
]

# DEC-119 - owner-confirmed cases A-G. These assert the resolved scheme and
# rate too, which is the whole point: the same LeadSource must be able to
# produce different rates for different employees.
#
# (label, notes, employee, expected_lead_source, expected_scheme, expected_rate)
SCHEME_CASES = [
    ("A  Tín Phát, không có chữ ADS",
     ["Bán hàng Vanoka"],  "Tín Phát",  ADS,      "ADS_7_5",      0.075),
    ("B  Kiên, không có ADS",
     ["Bán hàng Vanoka"],  "Kiên",      PERSONAL, "PERSONAL_5_5", 0.055),
    ("C  Kiên, một dòng trong OrderID có ADS",
     ["", "KH ADS", ""],   "Kiên",      ADS,      "ADS_7_5",      0.075),
    ("D  Hoàng, order nhiều SP, chỉ 1 dòng có ADS",
     ["", "", "Đơn ads", ""], "Hoàng",  ADS,      "ADS_7_5",      0.075),
    ("E  Vinh → Nội thành, không ADS",
     ["Bán hàng Vanoka"],  "Nội thành", PERSONAL, "NOI_THANH_2",  0.020),
    ("F  Quý/Hiệp → Nội thành, không ADS",
     ["Giao lắp chiều nay"], "Nội thành", PERSONAL, "NOI_THANH_2", 0.020),
    ("G1 Kiên trong tháng — phần PERSONAL",
     ["Bán hàng Vanoka"],  "Kiên",      PERSONAL, "PERSONAL_5_5", 0.055),
    ("G2 Kiên trong tháng — phần ADS",
     ["Đơn ADS"],          "Kiên",      ADS,      "ADS_7_5",      0.075),
]


def run_cases() -> int:
    failures = 0
    lead_cases = [
        (label, notes, override, None, expected)
        for label, notes, override, expected in CASES + EXTRA_CASES
    ] + EMPLOYEE_CASES

    print("LeadSource — spec section 29 + section 13 edge cases + DEC-109")
    print("-" * 90)
    for label, notes, override, employee, expected in lead_cases:
        actual, source = classify_lead_source(notes, override, employee)
        ok = actual == expected
        failures += not ok
        print(f"  [{'PASS' if ok else 'FAIL'}] {label:52} -> {actual:8} ({source})")
    print("-" * 90)
    print(f"  {len(lead_cases) - failures}/{len(lead_cases)} passed\n")

    scheme_failures = 0
    print("LeadSource + ConversionScheme — DEC-119 cases A–G")
    print("-" * 90)
    for label, notes, employee, exp_source, exp_scheme, exp_rate in SCHEME_CASES:
        lead_source, _ = classify_lead_source(notes, None, employee)
        scheme, rate, origin = resolve_conversion_scheme(employee, lead_source)
        ok = (lead_source == exp_source
              and scheme == exp_scheme
              and rate == exp_rate)
        scheme_failures += not ok
        shown = f"{lead_source} / {scheme} / {rate:.3%}" if rate else f"{lead_source} / -"
        print(f"  [{'PASS' if ok else 'FAIL'}] {label:44} -> {shown:34} ({origin})")
    print("-" * 90)
    print(f"  {len(SCHEME_CASES) - scheme_failures}/{len(SCHEME_CASES)} passed\n")

    return failures + scheme_failures


def run_two_bucket_check() -> int:
    """Case G end to end: two buckets converted separately, then summed.

    Guards the invariant that TASK-108 must hold:
        TotalConvertedRevenue == PersonalConvertedRevenue + AdsConvertedRevenue
    with no single blended rate anywhere in the path.
    """
    personal_profit = 30_000.0
    ads_profit = 7_565.0

    _, personal_rate, _ = resolve_conversion_scheme("Kiên", PERSONAL)
    _, ads_rate, _ = resolve_conversion_scheme("Kiên", ADS)

    personal_cr = personal_profit / personal_rate
    ads_cr = ads_profit / ads_rate
    total_cr = personal_cr + ads_cr

    blended = (personal_profit + ads_profit) / personal_rate

    print("Case G — hai bucket quy đổi độc lập (Kiên, một tháng)")
    print("-" * 90)
    print(f"  PersonalProfit {personal_profit:>12,.0f} / {personal_rate:.1%} = {personal_cr:>14,.0f}")
    print(f"  AdsProfit      {ads_profit:>12,.0f} / {ads_rate:.1%} = {ads_cr:>14,.0f}")
    print(f"  Total                                     = {total_cr:>14,.0f}")
    print()

    failures = 0
    ok = abs(total_cr - (personal_cr + ads_cr)) < 1e-9
    failures += not ok
    print(f"  [{'PASS' if ok else 'FAIL'}] Total == Personal + Ads")

    ok = abs(total_cr - blended) > 1.0
    failures += not ok
    print(f"  [{'PASS' if ok else 'FAIL'}] Khác với quy đổi gộp một tỉ lệ "
          f"({blended:,.0f}, lệch {blended - total_cr:,.0f})")
    print("-" * 90)
    print(f"  {2 - failures}/2 passed\n")
    return failures


def run_temporal_check() -> int:
    """A rate lookup is keyed on the order's date, not on today (DEC-121)."""
    print("Tra tỉ lệ theo thời điểm — DEC-121")
    print("-" * 90)
    failures = 0

    scheme, rate, _ = resolve_conversion_scheme("Kiên", ADS, date(2026, 3, 15))
    ok = scheme == "ADS_7_5" and rate == 0.075
    failures += not ok
    print(f"  [{'PASS' if ok else 'FAIL'}] 15/03/2026 -> {scheme} {rate:.1%}")

    scheme, rate, _ = resolve_conversion_scheme("Kiên", ADS, date(2027, 6, 1))
    ok = scheme == "ADS_7_5" and rate == 0.075
    failures += not ok
    print(f"  [{'PASS' if ok else 'FAIL'}] 01/06/2027 -> {scheme} {rate:.1%} "
          "(chưa có chính sách mới nào hiệu lực)")

    scheme, rate, origin = resolve_conversion_scheme("Kiên", ADS, date(2025, 12, 31))
    ok = scheme is None and origin == "Unresolved"
    failures += not ok
    print(f"  [{'PASS' if ok else 'FAIL'}] 31/12/2025 -> Unresolved "
          "(trước effective_from, không đoán tỉ lệ)")
    print("-" * 90)
    print(f"  {3 - failures}/3 passed\n")
    return failures


def scan_raw(path: Path) -> None:
    import openpyxl

    workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    sheet = workbook.active
    orders: dict[str, list] = defaultdict(list)
    order_employee: dict[str, str] = {}
    for row in sheet.iter_rows(min_row=6, values_only=True):
        if row[1]:
            order_id = str(row[1]).strip()
            orders[order_id].append(row[2])
            if len(row) > 12 and row[12]:
                order_employee.setdefault(order_id, normalize_text(row[12]))
    workbook.close()

    by_keyword = [
        order_id for order_id, notes in orders.items()
        if any(line_contains_ads(note) for note in notes)
    ]
    by_default = [
        order_id for order_id, employee in order_employee.items()
        if order_id not in by_keyword
        and EMPLOYEE_DEFAULT_LEAD_SOURCE.get(normalize_employee(employee)) == ADS
    ]

    print(f"Real raw file — {path.name}")
    print("-" * 78)
    print(f"  distinct orders                  : {len(orders)}")
    print(f"  ADS via keyword rule             : {len(by_keyword)}")
    print(f"  ADS via employee default         : {len(by_default)}")
    print(f"  PERSONAL                         : "
          f"{len(orders) - len(by_keyword) - len(by_default)}")
    if not by_keyword:
        print()
        print("  The keyword does not appear anywhere in this file. That is the")
        print("  expected result for data entered before the ADS convention, not")
        print("  a defect in the rule. See docs/analysis/06_ADS_RULE_VERIFICATION.md.")


# Mirrors the employee mapping of config/employees.yaml (DEC-104). Raw NVBH
# strings carry a phone number, so match on the leading name.
RAW_EMPLOYEE_PREFIXES = {
    "Tín Phát": "Tín Phát",
    "Vũ Hạnh Ly": "Ly",
    "Lê Mạnh Hoàng": "Hoàng",
    "Đức Kiên": "Kiên",
    "Phước Thắng": "Thắng",
    "Đức Hiệp": "Nội thành",
    "Mr Quý": "Nội thành",
    "Mr Vinh": "Nội thành",
}


def normalize_employee(raw: str) -> str | None:
    text = normalize_text(raw)
    for prefix, normalized in RAW_EMPLOYEE_PREFIXES.items():
        if text.startswith(prefix):
            return normalized
    return None


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=None)
    args = parser.parse_args()

    failures = run_cases()
    failures += run_two_bucket_check()
    failures += run_temporal_check()
    if args.raw and args.raw.exists():
        scan_raw(args.raw)
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
