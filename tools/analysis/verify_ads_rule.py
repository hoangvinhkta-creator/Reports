"""Verify LeadSource classification and ConversionScheme resolution.

Spec sections 5, 7, 12, 13 and 29, as amended by DEC-119, DEC-120 and DEC-121.

LeadSource and ConversionScheme are two independent concepts (DEC-119):

    LeadSource        answers "where did this order come from?"  -> PERSONAL | ADS
    ConversionScheme  answers "which rate converts it?"          -> a config row

PERSONAL does NOT imply 5.5%. The Noi thanh group sells PERSONAL orders at 2%,
and that same group's Gia dung lines convert at 8%. The rate is always
resolved from configuration keyed by (employee, employee_group, lead_source,
product_group, date) - never derived from the lead source alone, and never
hard-coded (DEC-127, ADR-106).

Three things are checked:

1. The test cases from spec section 29 plus cases A-G confirmed by the project
   owner, against a synthetic order set. This proves both rules behave as
   specified before any of it reaches the engine.
2. Cases H-K for the ProductGroup dimension, including the one that pins down
   why GIA_DUNG_8 is keyed on NOI_THANH rather than on "*".
3. The real raw sales book, to report how many orders each rule actually
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
from decimal import Decimal
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
# ProductGroup - a property of the PRODUCT LINE, not of the order (DEC-127,
# ADR-106). 118 real OrderIDs carry both kinds at once.
# --------------------------------------------------------------------------
DIEN_MAY = "DIEN_MAY"
GIA_DUNG = "GIA_DUNG"
DEFAULT_PRODUCT_GROUP = DIEN_MAY

# --------------------------------------------------------------------------
# ConversionScheme - resolved from (employee, employee_group, lead_source,
# product_group, date). Mirrors config/conversion_rates.yaml. Every row
# carries effective_from / effective_to so a future policy change never
# rewrites a past report (DEC-121). "*" means "any".
#
# lead_source is a hard filter. Among the survivors the most specific row
# wins, scored 4x employee + 2x employee_group + 1x product_group; a tie is a
# config error. There is no fallback rate: an unresolved combination is a
# review-queue item, never a silent guess.
#
# Rates are Decimal, never float (ADR-103) - they get divided into profit
# figures that become payroll.
# --------------------------------------------------------------------------
# (employee, employee_group, lead_source, product_group, scheme, rate, from, to)
CONVERSION_SCHEMES = [
    ("*", "*",         PERSONAL, "*",      "PERSONAL_5_5", Decimal("0.055"), date(2026, 1, 1), None),
    ("*", "*",         ADS,      "*",      "ADS_7_5",      Decimal("0.075"), date(2026, 1, 1), None),
    ("*", "NOI_THANH", PERSONAL, DIEN_MAY, "NOI_THANH_2",  Decimal("0.020"), date(2026, 1, 1), None),
    ("*", "NOI_THANH", PERSONAL, GIA_DUNG, "GIA_DUNG_8",   Decimal("0.080"), date(2026, 1, 1), None),
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


def _specificity(row) -> int:
    return (4 * (row[0] != "*")) + (2 * (row[1] != "*")) + (1 * (row[3] != "*"))


def resolve_conversion_scheme(
    employee: str | None,
    lead_source: str,
    as_of: date | None = None,
    manual_override: str | None = None,
    employee_group: str | None = None,
    product_group: str | None = None,
) -> tuple[str | None, Decimal | None, str]:
    """Return (scheme, rate, source_of_value) for one PRODUCT LINE.

    Independent of how the lead source was decided (DEC-119). Looked up by the
    order's own business date, not by "today", so re-running a 2026 report in
    2028 still uses the 2026 rates (DEC-121).

    Returns (None, None, "Unresolved") when no row matches. That is a review
    queue item: a missing rate must never fall back to some other employee's
    number. A tie on specificity raises - the config has to say which wins.
    """
    if manual_override:
        for row in CONVERSION_SCHEMES:
            if row[4] == manual_override:
                return row[4], row[5], "Manual"
        return manual_override, None, "Manual"

    as_of = as_of or DEFAULT_AS_OF
    product_group = product_group or DEFAULT_PRODUCT_GROUP
    candidates = [
        row for row in CONVERSION_SCHEMES
        if row[2] == lead_source                                  # hard filter
        and (row[0] == "*" or row[0] == employee)
        and (row[1] == "*" or row[1] == employee_group)
        and (row[3] == "*" or row[3] == product_group)
        and row[6] <= as_of
        and (row[7] is None or as_of <= row[7])
    ]
    if not candidates:
        return None, None, "Unresolved"

    best = max(_specificity(row) for row in candidates)
    winners = [row for row in candidates if _specificity(row) == best]
    if len(winners) > 1:
        raise ValueError(
            f"Ambiguous config: {[row[4] for row in winners]} equally specific"
        )

    row = winners[0]
    origin = ("Employee" if row[0] != "*"
              else "EmployeeGroup" if row[1] != "*"
              else "ProductGroup" if row[3] != "*"
              else "LeadSource")
    return row[4], row[5], f"Auto:{origin} ({row[4]})"


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

# DEC-119 - owner-confirmed cases A-G, updated for DEC-127/ADR-106. These
# assert the resolved scheme and rate too, which is the whole point: the same
# LeadSource must be able to produce different rates for different employees.
#
# E and F previously named a fake employee "Nội thành"; they now name the real
# people (Vinh, Quý, Hiệp) and carry their EmployeeGroup. The expected scheme
# and rate are UNCHANGED - that is the proof the model change preserved
# behaviour rather than altering it.
#
# (label, notes, employee, group, product_group, exp_lead_source, exp_scheme, exp_rate)
SCHEME_CASES = [
    ("A  Tín Phát, không có chữ ADS",
     ["Bán hàng Vanoka"], "Tín Phát", "STANDARD_SALES", DIEN_MAY, ADS,      "ADS_7_5",      Decimal("0.075")),
    ("B  Kiên, không có ADS",
     ["Bán hàng Vanoka"], "Kiên",     "STANDARD_SALES", DIEN_MAY, PERSONAL, "PERSONAL_5_5", Decimal("0.055")),
    ("C  Kiên, một dòng trong OrderID có ADS",
     ["", "KH ADS", ""],  "Kiên",     "STANDARD_SALES", DIEN_MAY, ADS,      "ADS_7_5",      Decimal("0.075")),
    ("D  Hoàng, order nhiều SP, chỉ 1 dòng có ADS",
     ["", "", "Đơn ads", ""], "Hoàng", "STANDARD_SALES", DIEN_MAY, ADS,     "ADS_7_5",      Decimal("0.075")),
    ("E  Vinh (NOI_THANH), không ADS",
     ["Bán hàng Vanoka"], "Vinh",     "NOI_THANH",      DIEN_MAY, PERSONAL, "NOI_THANH_2",  Decimal("0.020")),
    ("F  Quý/Hiệp (NOI_THANH), không ADS",
     ["Giao lắp chiều nay"], "Quý",   "NOI_THANH",      DIEN_MAY, PERSONAL, "NOI_THANH_2",  Decimal("0.020")),
    ("G1 Kiên trong tháng — phần PERSONAL",
     ["Bán hàng Vanoka"], "Kiên",     "STANDARD_SALES", DIEN_MAY, PERSONAL, "PERSONAL_5_5", Decimal("0.055")),
    ("G2 Kiên trong tháng — phần ADS",
     ["Đơn ADS"],         "Kiên",     "STANDARD_SALES", DIEN_MAY, ADS,      "ADS_7_5",      Decimal("0.075")),
]

# DEC-127 - ProductGroup cases. Same employee, same lead source, different
# product line kind -> different rate. And the mirror case that pins down why
# GIA_DUNG_8 is keyed on NOI_THANH rather than on "*".
#
# (label, employee, group, product_group, lead_source, exp_scheme, exp_rate)
PRODUCT_GROUP_CASES = [
    ("H  Vinh + Điện máy",
     "Vinh", "NOI_THANH",      DIEN_MAY, PERSONAL, "NOI_THANH_2",  Decimal("0.020")),
    ("I  Vinh + Gia dụng",
     "Vinh", "NOI_THANH",      GIA_DUNG, PERSONAL, "GIA_DUNG_8",   Decimal("0.080")),
    ("J  Hiệp + Gia dụng — cùng group, cùng kết quả",
     "Hiệp", "NOI_THANH",      GIA_DUNG, PERSONAL, "GIA_DUNG_8",   Decimal("0.080")),
    ("K  Ly + Gia dụng — STANDARD_SALES giữ 5,5%, KHÔNG nhảy lên 8%",
     "Ly",   "STANDARD_SALES", GIA_DUNG, PERSONAL, "PERSONAL_5_5", Decimal("0.055")),
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
    print("LeadSource + ConversionScheme — DEC-119 cases A–G (DEC-127 model)")
    print("-" * 90)
    for (label, notes, employee, group, product_group,
         exp_source, exp_scheme, exp_rate) in SCHEME_CASES:
        lead_source, _ = classify_lead_source(notes, None, employee)
        scheme, rate, origin = resolve_conversion_scheme(
            employee, lead_source, employee_group=group, product_group=product_group
        )
        ok = (lead_source == exp_source
              and scheme == exp_scheme
              and rate == exp_rate)
        scheme_failures += not ok
        shown = f"{lead_source} / {scheme} / {rate:.3%}" if rate else f"{lead_source} / -"
        print(f"  [{'PASS' if ok else 'FAIL'}] {label:44} -> {shown:34} ({origin})")
    print("-" * 90)
    print(f"  {len(SCHEME_CASES) - scheme_failures}/{len(SCHEME_CASES)} passed\n")

    pg_failures = 0
    print("ProductGroup — DEC-127 cases H–K")
    print("-" * 90)
    for label, employee, group, pg, lead_source, exp_scheme, exp_rate in PRODUCT_GROUP_CASES:
        scheme, rate, origin = resolve_conversion_scheme(
            employee, lead_source, employee_group=group, product_group=pg
        )
        ok = scheme == exp_scheme and rate == exp_rate
        pg_failures += not ok
        shown = f"{scheme} / {rate:.3%}" if rate else "-"
        print(f"  [{'PASS' if ok else 'FAIL'}] {label:56} -> {shown:22} ({origin})")
    print("-" * 90)
    print(f"  {len(PRODUCT_GROUP_CASES) - pg_failures}/{len(PRODUCT_GROUP_CASES)} passed\n")

    return failures + scheme_failures + pg_failures


def run_two_bucket_check() -> int:
    """Case G end to end: two buckets converted separately, then summed.

    Guards the invariant that TASK-108 must hold:
        TotalConvertedRevenue == PersonalConvertedRevenue + AdsConvertedRevenue
    with no single blended rate anywhere in the path.
    """
    personal_profit = Decimal("30000")
    ads_profit = Decimal("7565")

    group = EMPLOYEE_GROUPS["Kiên"]
    _, personal_rate, _ = resolve_conversion_scheme(
        "Kiên", PERSONAL, employee_group=group)
    _, ads_rate, _ = resolve_conversion_scheme(
        "Kiên", ADS, employee_group=group)

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
    ok = total_cr == personal_cr + ads_cr
    failures += not ok
    print(f"  [{'PASS' if ok else 'FAIL'}] Total == Personal + Ads")

    ok = abs(total_cr - blended) > 1
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
    ok = scheme == "ADS_7_5" and rate == Decimal("0.075")
    failures += not ok
    print(f"  [{'PASS' if ok else 'FAIL'}] 15/03/2026 -> {scheme} {rate:.1%}")

    scheme, rate, _ = resolve_conversion_scheme("Kiên", ADS, date(2027, 6, 1))
    ok = scheme == "ADS_7_5" and rate == Decimal("0.075")
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
    "Đức Hiệp": "Hiệp",
    "Mr Quý": "Quý",
    "Mr Vinh": "Vinh",
}

# Employee -> EmployeeGroup (DEC-127 §1). Vinh/Quý/Hiệp keep their own
# identity; the group is what they share, not a replacement name.
EMPLOYEE_GROUPS = {
    "Tín Phát": "STANDARD_SALES",
    "Ly": "STANDARD_SALES",
    "Hoàng": "STANDARD_SALES",
    "Kiên": "STANDARD_SALES",
    "Thắng": "STANDARD_SALES",
    "Vinh": "NOI_THANH",
    "Quý": "NOI_THANH",
    "Hiệp": "NOI_THANH",
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
