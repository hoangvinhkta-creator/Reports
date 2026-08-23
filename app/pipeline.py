"""Import pipeline entrypoint: the first 9 steps of spec §22.

    1. Read `.xlsx`                         -> raw_reader.read_raw_rows
    2. Metadata preview before normalizing   -> preview.build_preview
    3. Normalize columns, deduct Chiết khấu  -> normalizer.normalize_lines
    4. Employee mapping                      -> mapping.EmployeeMapper
    5. Group by OrderID                      -> orders.build_orders
    6. LeadSource rule at order level        -> lead_source.LeadSourceClassifier
    7. Propagate LeadSourceFinal to lines    -> (done inside step 6's apply())
    8. Price lookup (Pending if no Price Master) -> pricing.price_engine
    9. AccountingProfit (Universal formula, no KPI Adjustment) -> profit.profit_engine
   10. ProductGroup + ConversionScheme, PER LINE -> conversion.conversion_engine
   11. Validation + Review Queue (spec section 18) -> validation.Validator

Step 11 never blocks: it reports, it does not gate. An import whose every row
is defective still returns a full `ImportResult` (spec section 18, DEC-128).

Out of scope here (later tasks): product/transaction classification
(TASK-103), Adjustment persistence + EligibleKpiProfit (TASK-202/302/305,
DEC-126 — needs confirmed Adjustment records, not just the suggested-amount
resolver from TASK-106), Converted Revenue (TASK-108B — blocked, see C15
`EligibleCosts`), Review Queue persistence (TASK-201), audit trail and real
overrides (TASK-202), the review screen (TASK-305), export (TASK-111),
CLI (TASK-112).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.modules.conversion.conversion_engine import apply_conversion_schemes
from app.modules.conversion.scheme_resolver import ConversionSchemeResolver
from app.modules.domain.models import MAPPING_STATUS_MAPPED, Order, WorkingLine
from app.modules.importing.normalizer import normalize_lines
from app.modules.importing.preview import ImportPreview, build_preview
from app.modules.importing.raw_reader import read_raw_rows
from app.modules.lead_source.classifier import LeadSourceClassifier
from app.modules.mapping.employee_mapper import EmployeeMapper
from app.modules.orders.order_builder import build_orders
from app.modules.pricing.price_engine import apply_prices
from app.modules.pricing.provider import PendingPriceProvider, PriceProvider
from app.modules.product.product_group import (
    DefaultProductGroupProvider,
    ProductGroupProvider,
)
from app.modules.profit.profit_engine import apply_accounting_profit
from app.modules.validation.models import ReviewQueue
from app.modules.validation.validator import Validator

DEFAULT_CONFIG_DIR = Path("config")


@dataclass(frozen=True)
class WorkingData:
    """Everything steps 1–10 produce, before validation ever runs.

    Extracted so a test can hold the state as it exists at the moment BEFORE
    the Review Queue is built (Independent Review #2, Finding 4). Snapshotting
    the output of `run_import()` proved nothing about mutation: validation had
    already run once inside it, so the "before" picture was really an "after"
    one, and any mutation would have been baked into both sides.
    """

    preview: ImportPreview
    lines: list[WorkingLine]
    orders: list[Order]


@dataclass(frozen=True)
class ImportResult:
    preview: ImportPreview
    orders: list[Order]
    unmapped_lines: list[WorkingLine]
    review_queue: ReviewQueue


def build_working_data(
    raw_path: Path,
    config_dir: Path = DEFAULT_CONFIG_DIR,
    price_provider: PriceProvider | None = None,
    product_group_provider: ProductGroupProvider | None = None,
) -> WorkingData:
    """Steps 1–10 of spec section 22 — everything except the Review Queue."""
    raw_rows = read_raw_rows(raw_path)
    preview = build_preview(raw_rows)

    lines = normalize_lines(raw_rows)

    employee_mapper = EmployeeMapper.from_yaml(config_dir / "employees.yaml")
    employee_mapper.apply(lines)

    orders = build_orders(lines)

    classifier = LeadSourceClassifier.from_yaml(config_dir / "lead_source.yaml")
    classifier.apply(orders, employee_mapper)

    apply_prices(lines, price_provider or PendingPriceProvider())

    apply_accounting_profit(lines)

    resolver = ConversionSchemeResolver.from_yaml(
        config_dir / "conversion_rates.yaml"
    )
    apply_conversion_schemes(
        orders, resolver, product_group_provider or DefaultProductGroupProvider()
    )

    return WorkingData(preview=preview, lines=lines, orders=orders)


def run_import(
    raw_path: Path,
    config_dir: Path = DEFAULT_CONFIG_DIR,
    price_provider: PriceProvider | None = None,
    product_group_provider: ProductGroupProvider | None = None,
) -> ImportResult:
    working = build_working_data(
        raw_path, config_dir, price_provider, product_group_provider
    )

    # Step 11. Runs exactly once, last, and only reads: the Review Queue is a
    # report that travels beside the data, never a stage that edits it.
    review_queue = Validator.from_config_dir(config_dir).build_queue(
        working.lines, working.orders
    )

    unmapped_lines = [
        line
        for line in working.lines
        if line.employee_mapping_status != MAPPING_STATUS_MAPPED
    ]

    return ImportResult(
        preview=working.preview,
        orders=working.orders,
        unmapped_lines=unmapped_lines,
        review_queue=review_queue,
    )
