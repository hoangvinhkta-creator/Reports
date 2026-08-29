"""Batch 50 Real Orders — Session 1/2 (see PROJECT/PROJECT_PROGRESS.md).

Runs a frozen, deterministic slice of N real OrderIDs (default 50) through
`app.composition.run_import_production` — the same seam a real caller would
use — and classifies every order's outcome using ONLY the canonical
category/field names that already exist in `app/modules/domain/models.py`
and `app/modules/validation/models.py`. It invents no parallel taxonomy.

Selection rule (deterministic, reproducible): read the raw rows of the given
period workbook in file order, take the first N *unique* OrderIDs in order of
first appearance. This is a contiguous slice of the real dataset, not a
hand-picked sample.

Classification per order (Order Accounting, spec section 5 of the Batch 50
brief):

    AUTO_SUCCESS       — every line fully resolved (price, employee mapping,
                          conversion scheme, date/quantity/total_sales all
                          present) AND no Review Queue item touches this
                          order at all.
    REVIEW_QUEUE       — at least one Review Queue item touches this order
                          (row-level intersection with the item's provenance,
                          or an order-scoped item naming this order_id).
    PENDING_NOT_QUEUED — the order has an unresolved dimension (Pending price,
                          unmapped employee, Unresolved conversion scheme,
                          missing date/quantity/total_sales) but NO Review
                          Queue item touches it. This is the gap the Batch 50
                          brief requires reporting separately rather than
                          folding into REVIEW_QUEUE.
    ERROR              — the whole import raised (production runs one file at
                          a time; an exception is not attributable to a single
                          order in isolation, so this counts all cohort orders
                          as ERROR and the exception is reported verbatim).
    SILENTLY_DROPPED   — a cohort OrderID that does not appear in
                          `ImportResult.orders` at all.

Root-cause aggregation groups by the *set* of canonical Review Queue
categories (or, for orders with no queue item, by the specific Pending
dimension) touching each order — never by hand-picked reason strings.

Usage:
    python3 tools/analysis/batch_50_real_orders.py <path.xlsx> [--n 50]
"""

from __future__ import annotations

import argparse
import sys
import traceback
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.composition import run_import_production
from app.modules.domain.models import (
    CONVERSION_UNRESOLVED,
    MAPPING_STATUS_MAPPED,
    PRICE_SOURCE_PENDING,
)
from app.modules.importing.raw_reader import read_raw_rows
from app.modules.validation.models import ReviewItem


def select_frozen_cohort(raw_path: Path, n: int) -> list[str]:
    """First N unique OrderIDs in order of first appearance in the raw file."""
    seen: list[str] = []
    seen_set: set[str] = set()
    for row in read_raw_rows(raw_path):
        if row.order_id not in seen_set:
            seen_set.add(row.order_id)
            seen.append(row.order_id)
        if len(seen) >= n:
            break
    return seen


def _line_pending_reasons(line) -> list[str]:
    """Which known-Pending dimensions this line still carries, named after
    the exact domain-model constants — never a parallel taxonomy."""
    reasons = []
    if line.date is None:
        reasons.append("Missing.date")
    if line.employee_mapping_status != MAPPING_STATUS_MAPPED:
        reasons.append("Missing.employee (" + line.employee_mapping_status + ")")
    if line.quantity is None:
        reasons.append("Missing.quantity")
    if line.total_sales is None:
        reasons.append("Missing.total_sales")
    if line.price_source == PRICE_SOURCE_PENDING:
        reasons.append("Missing.PurchasePrice")
    if line.conversion_scheme_final == CONVERSION_UNRESOLVED:
        reasons.append("ConversionScheme.Unresolved")
    return reasons


def _item_covered_rows(item: ReviewItem) -> set[int]:
    return set(item.provenance.source_rows)


def analyze(raw_path: Path, n: int) -> dict:
    cohort = select_frozen_cohort(raw_path, n)
    cohort_set = set(cohort)

    report: dict = {
        "source_file": str(raw_path),
        "cohort": cohort,
        "cohort_size": len(cohort),
    }

    try:
        result = run_import_production(raw_path)
    except Exception:  # noqa: BLE001 - deliberately broad: this IS the ERROR bucket
        report["pipeline_error"] = traceback.format_exc()
        report["orders"] = {
            oid: {"outcome": "ERROR", "reasons": ["pipeline_exception"]}
            for oid in cohort
        }
        return report

    orders_by_id = {o.order_id: o for o in result.orders}

    # Which raw source_rows does each Review Queue item cover, and which
    # order_ids does that translate to?
    item_rows_by_category: dict[str, list[set[int]]] = defaultdict(list)
    order_id_hits_by_category: dict[str, set[str]] = defaultdict(set)
    for item in result.review_queue.items:
        rows = _item_covered_rows(item)
        item_rows_by_category[item.category].append(rows)
        if item.order_id:
            order_id_hits_by_category[item.category].add(item.order_id)

    # Build order_id -> set(source_row) for the whole result, so a row-level
    # item can be attributed back to the order it belongs to even when the
    # item itself carries no order_id (batch-scoped aggregate items).
    rows_to_order: dict[int, str] = {}
    for order in result.orders:
        for line in order.lines:
            rows_to_order[line.raw.source_row] = order.order_id

    order_categories: dict[str, set[str]] = defaultdict(set)
    for item in result.review_queue.items:
        rows = _item_covered_rows(item)
        touched_orders = {rows_to_order[r] for r in rows if r in rows_to_order}
        if item.order_id:
            touched_orders.add(item.order_id)
        for oid in touched_orders:
            order_categories[oid].add(item.category)

    per_order: dict[str, dict] = {}
    line_count = 0
    date_min = date_max = None
    for oid in cohort:
        order = orders_by_id.get(oid)
        if order is None:
            per_order[oid] = {"outcome": "SILENTLY_DROPPED", "reasons": []}
            continue

        lines = order.lines
        line_count += len(lines)
        for ln in lines:
            if ln.date is not None:
                date_min = ln.date if date_min is None else min(date_min, ln.date)
                date_max = ln.date if date_max is None else max(date_max, ln.date)

        pending_by_line = {ln.raw.source_row: _line_pending_reasons(ln) for ln in lines}
        any_pending = any(pending_by_line.values())
        categories_touching = order_categories.get(oid, set())
        is_queued = bool(categories_touching)

        if is_queued:
            outcome = "REVIEW_QUEUE"
        elif any_pending:
            outcome = "PENDING_NOT_QUEUED"
        else:
            outcome = "AUTO_SUCCESS"

        reasons = sorted(categories_touching) if categories_touching else sorted(
            {r.split(" (")[0] for reasons in pending_by_line.values() for r in reasons}
        )

        per_order[oid] = {
            "outcome": outcome,
            "reasons": reasons,
            "line_count": len(lines),
            "source_rows": sorted(ln.raw.source_row for ln in lines),
            "pending_by_line": pending_by_line,
        }

    report["orders"] = per_order
    report["total_lines_in_cohort"] = line_count
    report["date_range"] = (
        f"{date_min.isoformat()}..{date_max.isoformat()}" if date_min else None
    )
    report["first_order_id"] = cohort[0] if cohort else None
    report["last_order_id"] = cohort[-1] if cohort else None

    outcome_counts = Counter(o["outcome"] for o in per_order.values())
    report["outcome_counts"] = dict(outcome_counts)

    # Pareto: group ORDERS by the frozenset of reasons touching them.
    pareto: dict[frozenset, dict] = defaultdict(lambda: {"orders": set(), "lines": 0})
    for oid, info in per_order.items():
        if info["outcome"] == "SILENTLY_DROPPED":
            key = frozenset({"SILENTLY_DROPPED"})
        elif info["outcome"] == "AUTO_SUCCESS":
            continue
        else:
            key = frozenset(info["reasons"]) or frozenset({"UNKNOWN"})
        pareto[key]["orders"].add(oid)
        pareto[key]["lines"] += info.get("line_count", 0)

    report["pareto"] = [
        {
            "reasons": sorted(key),
            "order_count": len(v["orders"]),
            "orders": sorted(v["orders"]),
            "line_count": v["lines"],
        }
        for key, v in sorted(pareto.items(), key=lambda kv: -len(kv[1]["orders"]))
    ]

    review_queue_category_totals = {
        cat: {
            "item_count": len(rows_list),
            "affected_rows": len({r for rows in rows_list for r in rows}),
        }
        for cat, rows_list in item_rows_by_category.items()
    }
    report["review_queue_category_totals"] = review_queue_category_totals
    report["review_queue_total_items"] = len(result.review_queue.items)

    return report


def _print_report(report: dict) -> None:
    print("=" * 78)
    print(f"BATCH 50 REAL ORDERS — {report['source_file']}")
    print("=" * 78)
    print(f"cohort_size (unique OrderIDs)     : {report['cohort_size']}")
    print(f"first_order_id                    : {report.get('first_order_id')}")
    print(f"last_order_id                      : {report.get('last_order_id')}")
    print(f"total_lines_in_cohort              : {report.get('total_lines_in_cohort')}")
    print(f"date_range                         : {report.get('date_range')}")
    print()
    if "pipeline_error" in report:
        print("PIPELINE RAISED — every cohort order counted as ERROR")
        print(report["pipeline_error"])
        return

    print("-- Order Accounting --")
    input_n = report["cohort_size"]
    counts = report["outcome_counts"]
    accounted = counts.get("AUTO_SUCCESS", 0) + counts.get("REVIEW_QUEUE", 0)
    for key in ("AUTO_SUCCESS", "REVIEW_QUEUE", "PENDING_NOT_QUEUED", "ERROR", "SILENTLY_DROPPED"):
        print(f"  {key:20s}: {counts.get(key, 0)}")
    print(f"  AUTOMATION_RATE          : {counts.get('AUTO_SUCCESS', 0)}/{input_n} = "
          f"{counts.get('AUTO_SUCCESS', 0) / input_n:.1%}")
    print(f"  ORDER_ACCOUNTING_RATE    : {accounted}/{input_n} = {accounted / input_n:.1%}")
    print()

    print("-- Review Queue category totals (whole-file, for context) --")
    for cat, totals in sorted(report["review_queue_category_totals"].items()):
        print(f"  {cat:28s} items={totals['item_count']:4d}  affected_rows={totals['affected_rows']}")
    print(f"  TOTAL review_queue items: {report['review_queue_total_items']}")
    print()

    print("-- Root-cause Pareto (cohort orders only) --")
    for row in report["pareto"]:
        print(f"  reasons={row['reasons']}")
        print(f"    orders={row['order_count']:3d}  lines={row['line_count']:3d}  "
              f"order_ids={row['orders']}")
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path)
    parser.add_argument("--n", type=int, default=50)
    args = parser.parse_args()

    report = analyze(args.path, args.n)
    _print_report(report)


if __name__ == "__main__":
    main()
