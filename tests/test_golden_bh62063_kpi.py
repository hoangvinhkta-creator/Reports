"""Golden #1 KPI vertical slice — BH62063, real production trace.

Không phải Golden Baseline (`test_golden_baseline.py`, đã frozen, hai kỳ
nghiệp vụ thật) — đây là regression lock riêng cho MỘT đơn hàng Golden #1 đã
Owner phê duyệt (S049), qua ĐÚNG production entry point (`run_import`), dùng
CHÍNH hai file dữ liệu thật đã commit (không phải bản sao tmp_path):
`data/historical_confirmed/registry.jsonl` và
`data/confirmed_adjustments/confirmed_adjustments.jsonl`. Không
stub/mock/bypass/manual injection — `identity_registry=`/
`confirmed_adjustment_source=` là đúng cổng DI production (S051/S053, và
TASK-108B minimum B7/B8 slice này).
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from app.modules.adjustment.confirmed_adjustment_source import (
    load_confirmed_adjustments_from_jsonl,
)
from app.modules.domain.models import KPI_PURCHASE_NO_CONFIRMED_ADJUSTMENT
from app.modules.product.identity.registry_store import load_registry_from_jsonl
from app.pipeline import run_import

GOLDEN_FIXTURE = Path("tests/fixtures/golden/period_2026_01.xlsx")
CONFIG_DIR = Path("config")
IDENTITY_REGISTRY_FILE = Path("data/historical_confirmed/registry.jsonl")
CONFIRMED_ADJUSTMENTS_FILE = Path(
    "data/confirmed_adjustments/confirmed_adjustments.jsonl"
)


def _order(result, order_id):
    return next(o for o in result.orders if o.order_id == order_id)


def test_bh62063_real_trace_reaches_eligible_kpi_profit():
    """GOLDEN_PASS (session brief §4/§11): `KpiPurchasePrice = 7.000.000`,
    `EligibleKpiProfit = 500.000`, provenance trung thực."""
    registry = load_registry_from_jsonl(IDENTITY_REGISTRY_FILE)
    adjustment_source = load_confirmed_adjustments_from_jsonl(
        CONFIRMED_ADJUSTMENTS_FILE
    )
    assert adjustment_source.is_available is True  # file thật tồn tại, load được

    result = run_import(
        GOLDEN_FIXTURE,
        config_dir=CONFIG_DIR,
        identity_registry=registry,
        confirmed_adjustment_source=adjustment_source,
    )
    line = _order(result, "BH62063").lines[0]

    assert line.accounting_purchase_price == Decimal("7000000")
    assert line.kpi_purchase_price == Decimal("7000000")
    assert line.kpi_purchase_price_provenance == KPI_PURCHASE_NO_CONFIRMED_ADJUSTMENT
    assert line.sell_price == Decimal("7500000")
    assert line.quantity == Decimal("1")
    assert line.discount == Decimal("0")
    assert line.eligible_kpi_profit == Decimal("500000")

    # AccountingProfit và EligibleKpiProfit trùng số ở ĐÚNG đơn hàng này chỉ vì
    # Discount = 0 — trùng hợp số học riêng của BH62063 (S053 §6), không phải
    # bằng chứng hai capability giống nhau. Xem test_kpi_profit_engine.py cho
    # case Discount != 0 phân biệt được hai field.
    assert line.accounting_profit == Decimal("500000")


def test_bh62063_default_run_import_without_kpi_wiring_is_still_pending():
    """0 blast radius: không truyền `confirmed_adjustment_source`/
    `identity_registry` (hành vi mặc định của mọi lời gọi `run_import()` hiện
    có, bao gồm Golden Baseline) vẫn giữ nguyên Pending — không đổi."""
    result = run_import(GOLDEN_FIXTURE, config_dir=CONFIG_DIR)
    line = _order(result, "BH62063").lines[0]
    assert line.accounting_purchase_price is None
    assert line.kpi_purchase_price is None
    assert line.eligible_kpi_profit is None
