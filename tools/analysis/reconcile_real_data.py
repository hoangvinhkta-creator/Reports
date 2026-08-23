"""CHECK-101-08 reconciliation against real Tín Phát raw data (01.2026, 06.2026).

Runs the actual production pipeline (`app.pipeline.run_import`) against real
files — not a synthetic fixture — and reports every metric the reviewer
asked for. This script only reads and reports; it never changes a business
rule to make a number match. Any mismatch is printed with enough detail to
diagnose the cause, per the instruction not to silently round or adjust.

Usage:
    python tools/analysis/reconcile_real_data.py <path.xlsx> [--label "01.2026"]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import openpyxl

from app.modules.domain.models import ADS, MAPPING_STATUS_MAPPED, PERSONAL
from app.modules.importing.raw_reader import HEADER_ROW, COLUMNS
from app.pipeline import run_import


def count_raw_sheet_rows(path: Path) -> dict:
    """Independent count straight from the sheet, bypassing read_raw_rows,
    to detect anything the reader might have silently skipped."""
    workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    sheet = workbook.active
    total_data_rows = 0
    missing_order_id = 0
    for row in sheet.iter_rows(min_row=6, values_only=True):
        if all(v is None for v in row):
            continue
        total_data_rows += 1
        if not row[COLUMNS["order_id"]]:
            missing_order_id += 1
    workbook.close()
    return {
        "total_data_rows": total_data_rows,
        "missing_order_id": missing_order_id,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--label", default="")
    parser.add_argument("--expected-orders", type=int, default=None)
    args = parser.parse_args()

    print(f"{'=' * 78}")
    print(f"RECONCILIATION — {args.label or args.path.name}")
    print(f"{'=' * 78}")

    sheet_stats = count_raw_sheet_rows(args.path)
    result = run_import(args.path, config_dir=Path("config"))

    orders = result.orders
    all_lines = [line for order in orders for line in order.lines]

    # --- raw rows / OrderID ---
    print("\n-- Raw rows & OrderID --")
    print(f"  Dòng dữ liệu trong sheet (kể cả không có OrderID): {sheet_stats['total_data_rows']}")
    print(f"  Dòng thiếu OrderID (bị raw_reader bỏ qua):         {sheet_stats['missing_order_id']}")
    print(f"  Dòng có OrderID, được đọc vào RawRow:              {result.preview.row_count}")
    print(f"  Số OrderID duy nhất:                               {result.preview.distinct_order_count}")
    if args.expected_orders is not None:
        delta = result.preview.distinct_order_count - args.expected_orders
        status = "PASS" if delta == 0 else f"LỆCH {delta:+d}"
        print(f"  Kỳ vọng: {args.expected_orders} đơn -> {status}")

    # --- employee mapping ---
    print("\n-- Employee mapping --")
    mapped = sum(1 for line in all_lines if line.employee_mapping_status == MAPPING_STATUS_MAPPED)
    unmapped = len(all_lines) - mapped
    print(f"  Dòng employee mapped:   {mapped}")
    print(f"  Dòng employee unmapped: {unmapped}")
    if unmapped:
        raw_names = sorted({line.employee_raw for line in all_lines if line.employee_mapping_status != MAPPING_STATUS_MAPPED})
        print(f"  Tên chưa map: {raw_names}")

    # --- OrderID with more than one distinct raw employee ---
    print("\n-- OrderID có nhiều employee khác nhau --")
    mixed_employee_orders = []
    for order in orders:
        raw_employees = {line.employee_raw for line in order.lines}
        if len(raw_employees) > 1:
            mixed_employee_orders.append((order.order_id, raw_employees))
    print(f"  Số đơn có >1 employee_raw trong cùng OrderID: {len(mixed_employee_orders)}")
    for order_id, names in mixed_employee_orders[:10]:
        print(f"    {order_id}: {names}")

    # --- sales / discount / normalized ---
    print("\n-- Doanh số / Chiết khấu (VND nguyên) --")
    total_sales_raw = result.preview.total_sales_raw
    total_discount = sum((line.discount or 0) for line in all_lines)
    total_normalized = sum((line.total_sales or 0) for line in all_lines)
    print(f"  Tổng 'Doanh số bán' (raw, cột J):        {total_sales_raw:,}")
    print(f"  Tổng Chiết khấu (cột L):                 {total_discount:,}")
    print(f"  Tổng doanh số normalized (SellPrice*Qty-Discount): {total_normalized:,}")
    print(f"  Chênh (raw - normalized):                {total_sales_raw - total_normalized:,}")

    # --- LeadSource breakdown ---
    print("\n-- Phân loại LeadSource --")
    personal = [o for o in orders if o.lead_source_final == PERSONAL]
    ads_default = [o for o in orders if o.lead_source_final == ADS and o.lead_source_source_of_value and "Employee Default" in o.lead_source_source_of_value]
    ads_keyword = [o for o in orders if o.lead_source_final == ADS and o.lead_source_source_of_value == "Auto:ADS Rule"]
    ads_other = [o for o in orders if o.lead_source_final == ADS and o not in ads_default and o not in ads_keyword]
    print(f"  PERSONAL:                          {len(personal)}")
    print(f"  ADS qua mặc định Tín Phát:          {len(ads_default)}")
    print(f"  ADS qua từ khóa 'ADS' trong ghi chú: {len(ads_keyword)}")
    print(f"  ADS khác (không rơi vào 2 nhóm trên): {len(ads_other)}")
    for o in ads_keyword[:10]:
        notes = [line.note_raw for line in o.lines]
        print(f"    {o.order_id}: notes={notes}")

    # --- Discrepancy: raw total_sales vs SellPrice*Qty-Discount ---
    print("\n-- So sánh Doanh số bán (raw) vs SellPrice x Qty - Discount --")
    mismatches = []
    for line in all_lines:
        raw_value = line.raw.total_sales_raw
        computed = line.total_sales
        if raw_value is None or computed is None:
            continue
        if raw_value != computed:
            mismatches.append((line, raw_value, computed))
    print(f"  Tổng số dòng so sánh được: {sum(1 for l in all_lines if l.raw.total_sales_raw is not None and l.total_sales is not None)}")
    print(f"  Số dòng lệch:              {len(mismatches)}")
    if mismatches:
        print("  Chi tiết (tối đa 20 dòng đầu):")
        for line, raw_value, computed in mismatches[:20]:
            delta = raw_value - computed
            print(
                f"    order={line.order_id} source_row={line.raw.source_row} "
                f"qty={line.quantity} price={line.sell_price} discount={line.discount} "
                f"raw={raw_value:,} computed={computed:,} delta={delta:,} "
                f"note={line.note_raw!r}"
            )
        deltas = [raw_value - computed for _, raw_value, computed in mismatches]
        print(f"  Tổng delta: {sum(deltas):,}")
        print(f"  Delta min/max: {min(deltas):,} / {max(deltas):,}")

    print()


if __name__ == "__main__":
    main()
