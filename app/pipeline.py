"""Import pipeline entrypoint: the first 8 steps of spec §22.

    1. Read `.xlsx`                         -> raw_reader.read_raw_rows
    2. Metadata preview before normalizing   -> preview.build_preview
    3. Normalize columns, deduct Chiết khấu  -> normalizer.normalize_lines
    4. Employee mapping                      -> mapping.EmployeeMapper
    5. Group by OrderID                      -> orders.build_orders
    6. LeadSource rule at order level        -> lead_source.LeadSourceClassifier
    7. Propagate LeadSourceFinal to lines    -> (done inside step 6's apply())
    8. Price lookup (Pending if no Price Master) -> pricing.price_engine

Out of scope here (later tasks): product/transaction classification
(TASK-103), adjustments/profit/conversion (TASK-106–108), Review Queue
persistence (TASK-110), export (TASK-111), CLI (TASK-112).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.modules.domain.models import MAPPING_STATUS_MAPPED, Order, WorkingLine
from app.modules.importing.normalizer import normalize_lines
from app.modules.importing.preview import ImportPreview, build_preview
from app.modules.importing.raw_reader import read_raw_rows
from app.modules.lead_source.classifier import LeadSourceClassifier
from app.modules.mapping.employee_mapper import EmployeeMapper
from app.modules.orders.order_builder import build_orders
from app.modules.pricing.price_engine import apply_prices
from app.modules.pricing.provider import PendingPriceProvider, PriceProvider

DEFAULT_CONFIG_DIR = Path("config")


@dataclass(frozen=True)
class ImportResult:
    preview: ImportPreview
    orders: list[Order]
    unmapped_lines: list[WorkingLine]


def run_import(
    raw_path: Path,
    config_dir: Path = DEFAULT_CONFIG_DIR,
    price_provider: PriceProvider | None = None,
) -> ImportResult:
    raw_rows = read_raw_rows(raw_path)
    preview = build_preview(raw_rows)

    lines = normalize_lines(raw_rows)

    employee_mapper = EmployeeMapper.from_yaml(config_dir / "employees.yaml")
    employee_mapper.apply(lines)

    orders = build_orders(lines)

    classifier = LeadSourceClassifier.from_yaml(config_dir / "lead_source.yaml")
    classifier.apply(orders, employee_mapper)

    apply_prices(lines, price_provider or PendingPriceProvider())

    unmapped_lines = [
        line
        for line in lines
        if line.employee_mapping_status != MAPPING_STATUS_MAPPED
    ]

    return ImportResult(preview=preview, orders=orders, unmapped_lines=unmapped_lines)
