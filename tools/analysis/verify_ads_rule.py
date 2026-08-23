"""Verify LeadSource classification and ConversionScheme resolution.

Spec sections 5, 7, 12, 13 and 29, as amended by DEC-119, DEC-120, DEC-121 and
DEC-127.

    LeadSource        answers "where did this order come from?"  -> PERSONAL | ADS
    ProductGroup      answers "what kind of goods is this line?" -> DIEN_MAY | GIA_DUNG
    ConversionScheme  answers "which rate converts it?"          -> a config row

PERSONAL does NOT imply 5.5%. The Noi thanh group sells PERSONAL orders at 2%,
and that same group's Gia dung lines convert at 8%.

**This script exercises the PRODUCTION code path.** It imports
`EmployeeMapper`, `LeadSourceClassifier` and `ConversionSchemeResolver` from
`app.modules` and loads the real files in `config/`. It deliberately contains
no employee table, no keyword list, no rate table and no resolution algorithm
of its own — an earlier version did, and a second implementation living inside
a verification script is an oracle that can agree with itself while production
is wrong.

Only the EXPECTED OUTPUTS are written here. Inputs are raw `NVBH` strings
exactly as they appear in the sales book, so the mapping step is verified too.

Usage:
    python tools/analysis/verify_ads_rule.py [--raw path/to/So_chi_tiet_ban_hang.xlsx]
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.modules.conversion.scheme_resolver import ConversionSchemeResolver  # noqa: E402
from app.modules.domain.models import ADS, DIEN_MAY, GIA_DUNG, PERSONAL  # noqa: E402
from app.modules.lead_source.classifier import LeadSourceClassifier  # noqa: E402
from app.modules.mapping.employee_mapper import EmployeeMapper  # noqa: E402

CONFIG = Path(__file__).resolve().parents[2] / "config"
DEFAULT_AS_OF = date(2026, 6, 30)

MAPPER = EmployeeMapper.from_yaml(CONFIG / "employees.yaml")
CLASSIFIER = LeadSourceClassifier.from_yaml(CONFIG / "lead_source.yaml")
RESOLVER = ConversionSchemeResolver.from_yaml(CONFIG / "conversion_rates.yaml")

# Raw NVBH strings exactly as the sales book writes them. Using raw values
# means the production mapping step is part of what gets verified.
RAW_TIN_PHAT = "Tín Phát 0869931931"
RAW_LY = "Vũ Hạnh Ly 0868345633"
RAW_HOANG = "Lê Mạnh Hoàng 0865111533"
RAW_KIEN = "Đức Kiên - Tân Á 0867666533"
RAW_VINH = "Mr Vinh"
RAW_QUY = "Mr Quý"
RAW_HIEP = "Đức Hiệp"


def classify(notes, manual_override=None, employee_raw=None, as_of=DEFAULT_AS_OF):
    """Run the production classification chain for one order."""
    mapping = MAPPER.resolve(employee_raw, as_of) if employee_raw else None
    auto = CLASSIFIER.classify_auto(
        notes,
        mapping.default_lead_source if mapping else None,
        mapping.normalized if mapping else None,
    )
    final = CLASSIFIER.resolve_final(auto, manual_override)
    return final.lead_source, final.source_of_value, mapping


def resolve(employee_raw, lead_source, product_group=DIEN_MAY, as_of=DEFAULT_AS_OF):
    """Run the production scheme resolution for one product line."""
    mapping = MAPPER.resolve(employee_raw, as_of)
    return RESOLVER.resolve_auto(
        employee=mapping.normalized,
        employee_group=mapping.group,
        lead_source=lead_source,
        product_group=product_group,
        as_of=as_of,
    )


# --------------------------------------------------------------------------
# Expected outputs. These are the assertions; everything they run against is
# production code reading production config.
# --------------------------------------------------------------------------

# (label, notes, manual_override, expected_lead_source)
CASES = [
    ("1  Một order 1 dòng, ghi chú 'ADS'", ["ADS"], None, ADS),
    ("2  Ghi chú 'ads facebook'", ["ads facebook"], None, ADS),
    ("3  Ghi chú 'Đơn Ads web'", ["Đơn Ads web"], None, ADS),
    ("4  Order 4 dòng, dòng 3 có 'ADS', còn lại trống",
     ["", "", "ADS", ""], None, ADS),
    ("5  Không dòng nào có ADS",
     ["Giao lắp sáng mai", "Chi phí vận chuyển"], None, PERSONAL),
    ("6  Rule auto = ADS nhưng user override PERSONAL",
     ["KH ADS"], PERSONAL, PERSONAL),
    ("7  User reset override", ["KH ADS"], None, ADS),
    ("8a Nhân viên có đơn ADS trong tháng", ["  ADS  "], None, ADS),
    ("8b Cùng nhân viên, đơn không ADS", ["Bán hàng Vanoka"], None, PERSONAL),
    ("9  Chữ thường hoàn toàn", ["đơn ads"], None, ADS),
    ("10 Khoảng trắng thừa", ["ĐƠN    ADS    WEB"], None, ADS),
    ("11 Ghi chú None", [None, None], None, PERSONAL),
    ("12 Override sang ADS khi auto = PERSONAL", ["Bán hàng"], ADS, ADS),
]

# DEC-109 employee-level default. Fourth element is the RAW NVBH value.
EMPLOYEE_CASES = [
    ("13 Tín Phát, ghi chú mặc định ERP, không có ADS",
     ["Bán hàng Vanoka"], None, RAW_TIN_PHAT, ADS),
    ("14 Tín Phát, ghi chú có ADS", ["Đơn ADS web"], None, RAW_TIN_PHAT, ADS),
    ("15 Tín Phát, quản lý override về PERSONAL",
     ["Bán hàng Vanoka"], PERSONAL, RAW_TIN_PHAT, PERSONAL),
    ("16 Ly, ghi chú mặc định ERP — không ăn theo Tín Phát",
     ["Bán hàng Vanoka"], None, RAW_LY, PERSONAL),
    ("17 Ly, ghi chú có ADS", ["KH ADS"], None, RAW_LY, ADS),
]

# DEC-119 cases A-G, expressed in the DEC-127 model. Expected scheme and rate
# are UNCHANGED from before the EmployeeGroup/ProductGroup split — that
# equality is the regression proof.
#
# (label, notes, raw_employee, exp_lead_source, exp_scheme, exp_rate)
SCHEME_CASES = [
    ("A  Tín Phát, không có chữ ADS",
     ["Bán hàng Vanoka"], RAW_TIN_PHAT, ADS, "ADS_7_5", Decimal("0.075")),
    ("B  Kiên, không có ADS",
     ["Bán hàng Vanoka"], RAW_KIEN, PERSONAL, "PERSONAL_5_5", Decimal("0.055")),
    ("C  Kiên, một dòng trong OrderID có ADS",
     ["", "KH ADS", ""], RAW_KIEN, ADS, "ADS_7_5", Decimal("0.075")),
    ("D  Hoàng, order nhiều SP, chỉ 1 dòng có ADS",
     ["", "", "Đơn ads", ""], RAW_HOANG, ADS, "ADS_7_5", Decimal("0.075")),
    ("E  Vinh (NOI_THANH), không ADS",
     ["Bán hàng Vanoka"], RAW_VINH, PERSONAL, "NOI_THANH_2", Decimal("0.020")),
    ("F  Quý/Hiệp (NOI_THANH), không ADS",
     ["Giao lắp chiều nay"], RAW_QUY, PERSONAL, "NOI_THANH_2", Decimal("0.020")),
    ("G1 Kiên trong tháng — phần PERSONAL",
     ["Bán hàng Vanoka"], RAW_KIEN, PERSONAL, "PERSONAL_5_5", Decimal("0.055")),
    ("G2 Kiên trong tháng — phần ADS",
     ["Đơn ADS"], RAW_KIEN, ADS, "ADS_7_5", Decimal("0.075")),
]

# DEC-127 ProductGroup cases, plus the one that pins down why GIA_DUNG_8 is
# keyed on NOI_THANH rather than on "*", and the unmapped guard of DEC-127 §8.
#
# (label, raw_employee, product_group, lead_source, exp_scheme, exp_rate)
PRODUCT_GROUP_CASES = [
    ("H  Vinh + Điện máy",
     RAW_VINH, DIEN_MAY, PERSONAL, "NOI_THANH_2", Decimal("0.020")),
    ("I  Vinh + Gia dụng",
     RAW_VINH, GIA_DUNG, PERSONAL, "GIA_DUNG_8", Decimal("0.080")),
    ("J  Hiệp + Gia dụng — cùng group, cùng kết quả",
     RAW_HIEP, GIA_DUNG, PERSONAL, "GIA_DUNG_8", Decimal("0.080")),
    ("K  Ly + Gia dụng — STANDARD_SALES giữ 5,5%, KHÔNG nhảy lên 8%",
     RAW_LY, GIA_DUNG, PERSONAL, "PERSONAL_5_5", Decimal("0.055")),
    ("L  Nhân viên chưa map — KHÔNG được tỉ lệ nào (DEC-127 §8)",
     "Người Lạ 0900000000", DIEN_MAY, PERSONAL, "Unresolved", None),
]


def run_cases() -> int:
    failures = 0
    lead_cases = [
        (label, notes, override, None, expected)
        for label, notes, override, expected in CASES
    ] + EMPLOYEE_CASES

    print("LeadSource — spec section 29 + section 13 edge cases + DEC-109")
    print("-" * 90)
    for label, notes, override, employee_raw, expected in lead_cases:
        actual, source, _ = classify(notes, override, employee_raw)
        ok = actual == expected
        failures += not ok
        print(f"  [{'PASS' if ok else 'FAIL'}] {label:52} -> {actual:8} ({source})")
    print("-" * 90)
    print(f"  {len(lead_cases) - failures}/{len(lead_cases)} passed\n")

    scheme_failures = 0
    print("LeadSource + ConversionScheme — DEC-119 cases A–G (DEC-127 model)")
    print("-" * 90)
    for label, notes, raw, exp_source, exp_scheme, exp_rate in SCHEME_CASES:
        lead_source, _, _ = classify(notes, None, raw)
        got = resolve(raw, lead_source)
        ok = (lead_source == exp_source
              and got.scheme == exp_scheme
              and got.rate == exp_rate)
        scheme_failures += not ok
        shown = (f"{lead_source} / {got.scheme} / {got.rate:.3%}"
                 if got.rate is not None else f"{lead_source} / {got.scheme}")
        print(f"  [{'PASS' if ok else 'FAIL'}] {label:44} -> {shown:34} "
              f"({got.source_of_value})")
    print("-" * 90)
    print(f"  {len(SCHEME_CASES) - scheme_failures}/{len(SCHEME_CASES)} passed\n")

    pg_failures = 0
    print("ProductGroup + unmapped guard — DEC-127 cases H–L")
    print("-" * 90)
    for label, raw, pg, lead_source, exp_scheme, exp_rate in PRODUCT_GROUP_CASES:
        got = resolve(raw, lead_source, product_group=pg)
        ok = got.scheme == exp_scheme and got.rate == exp_rate
        pg_failures += not ok
        shown = f"{got.scheme} / {got.rate:.3%}" if got.rate is not None else got.scheme
        print(f"  [{'PASS' if ok else 'FAIL'}] {label:58} -> {shown:22} "
              f"({got.source_of_value})")
    print("-" * 90)
    print(f"  {len(PRODUCT_GROUP_CASES) - pg_failures}/{len(PRODUCT_GROUP_CASES)} passed\n")

    return failures + scheme_failures + pg_failures


def run_two_bucket_check() -> int:
    """Case G end to end: two buckets converted separately, then summed.

    Guards the invariant TASK-108B will have to hold:
        TotalConvertedRevenue == PersonalConvertedRevenue + AdsConvertedRevenue
    with no single blended rate anywhere in the path.
    """
    personal_profit = Decimal("30000")
    ads_profit = Decimal("7565")

    personal_rate = resolve(RAW_KIEN, PERSONAL).rate
    ads_rate = resolve(RAW_KIEN, ADS).rate

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

    got = resolve(RAW_KIEN, ADS, as_of=date(2026, 3, 15))
    ok = got.scheme == "ADS_7_5" and got.rate == Decimal("0.075")
    failures += not ok
    print(f"  [{'PASS' if ok else 'FAIL'}] 15/03/2026 -> {got.scheme} {got.rate:.1%}")

    got = resolve(RAW_KIEN, ADS, as_of=date(2027, 6, 1))
    ok = got.scheme == "ADS_7_5" and got.rate == Decimal("0.075")
    failures += not ok
    print(f"  [{'PASS' if ok else 'FAIL'}] 01/06/2027 -> {got.scheme} {got.rate:.1%} "
          "(chưa có chính sách mới nào hiệu lực)")

    got = resolve(RAW_KIEN, ADS, as_of=date(2025, 12, 31))
    ok = got.rate is None
    failures += not ok
    print(f"  [{'PASS' if ok else 'FAIL'}] 31/12/2025 -> {got.scheme} "
          "(trước effective_from, không đoán tỉ lệ)")
    print("-" * 90)
    print(f"  {3 - failures}/3 passed\n")
    return failures


def scan_raw(path: Path) -> None:
    """Report how often each rule actually fires on a real sales book."""
    import openpyxl

    workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    sheet = workbook.active
    orders: dict[str, list] = defaultdict(list)
    order_employee: dict[str, str] = {}
    order_date: dict[str, date] = {}
    for row in sheet.iter_rows(min_row=6, values_only=True):
        if not row[1]:
            continue
        order_id = str(row[1]).strip()
        orders[order_id].append(row[2])
        if len(row) > 12 and row[12]:
            order_employee.setdefault(order_id, str(row[12]).strip())
        if row[0] is not None and hasattr(row[0], "year"):
            order_date.setdefault(
                order_id, row[0].date() if hasattr(row[0], "date") else row[0]
            )
    workbook.close()

    by_keyword: list[str] = []
    by_default: list[str] = []
    for order_id, notes in orders.items():
        raw = order_employee.get(order_id)
        as_of = order_date.get(order_id, DEFAULT_AS_OF)
        lead_source, source, _ = classify(notes, None, raw, as_of)
        if lead_source != ADS:
            continue
        (by_keyword if "ADS Rule" in source else by_default).append(order_id)

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
