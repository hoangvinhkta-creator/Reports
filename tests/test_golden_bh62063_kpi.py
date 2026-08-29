"""Golden #1 KPI vertical slice — BH62063, real production trace.

Không phải Golden Baseline (`test_golden_baseline.py`, đã frozen, hai kỳ
nghiệp vụ thật) — đây là regression lock riêng cho MỘT đơn hàng Golden #1 đã
Owner phê duyệt (S049), qua ĐÚNG production entry point, dùng CHÍNH ba file/
config dữ liệu thật đã commit (không phải bản sao tmp_path):
`data/historical_confirmed/registry.jsonl`,
`data/confirmed_adjustments/confirmed_adjustments.jsonl`,
`config/eligible_costs.yaml`.

`test_bh62063_real_trace_reaches_eligible_kpi_profit` giữ nguyên đường DI thủ
công (S051/S053/S054) làm regression lock ở tầng module.
`test_bh62063_normal_production_composition_reaches_eligible_kpi_profit`
(Golden #1 Repair Batch #1, B01) là phép kiểm THẬT: gọi
`app.composition.run_import_production()` — KHÔNG test/manual DI nào — và
phải ra cùng kết quả. Đây mới là bằng chứng "normal, non-test production
composition" mà cumulative review yêu cầu, không phải một test có thể tự
tay nạp DI rồi tự chứng minh chính nó.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from app.composition import run_import_production
from app.modules.adjustment.confirmed_adjustment_source import (
    load_confirmed_adjustments_from_jsonl,
)
from app.modules.domain.models import KPI_PURCHASE_NO_CONFIRMED_ADJUSTMENT
from app.modules.kpi.kpi_profit_engine import (
    PROVENANCE_ELIGIBLE_COSTS_EMPTY_SET,
    load_eligible_costs_authority,
)
from app.modules.product.identity.registry_store import load_registry_from_jsonl
from app.pipeline import run_import

GOLDEN_FIXTURE = Path("tests/fixtures/golden/period_2026_01.xlsx")
CONFIG_DIR = Path("config")
IDENTITY_REGISTRY_FILE = Path("data/historical_confirmed/registry.jsonl")
CONFIRMED_ADJUSTMENTS_FILE = Path(
    "data/confirmed_adjustments/confirmed_adjustments.jsonl"
)
ELIGIBLE_COSTS_FILE = Path("config/eligible_costs.yaml")


def _order(result, order_id):
    return next(o for o in result.orders if o.order_id == order_id)


def test_bh62063_real_trace_reaches_eligible_kpi_profit():
    """GOLDEN_PASS (session brief §4/§11): `KpiPurchasePrice = 7.000.000`,
    `EligibleKpiProfit = 500.000`, provenance trung thực. Regression lock ở
    tầng module — DI thủ công có chủ đích (đường thật là B01 dưới đây)."""
    registry = load_registry_from_jsonl(IDENTITY_REGISTRY_FILE)
    adjustment_source = load_confirmed_adjustments_from_jsonl(
        CONFIRMED_ADJUSTMENTS_FILE
    )
    eligible_costs_authority = load_eligible_costs_authority(ELIGIBLE_COSTS_FILE)
    assert adjustment_source.is_available is True  # file thật tồn tại, load được
    assert eligible_costs_authority.is_valid is True

    result = run_import(
        GOLDEN_FIXTURE,
        config_dir=CONFIG_DIR,
        identity_registry=registry,
        confirmed_adjustment_source=adjustment_source,
        eligible_costs_authority=eligible_costs_authority,
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


def test_bh62063_normal_production_composition_reaches_eligible_kpi_profit():
    """Golden #1 Repair Batch #1, B01 — REAL acceptance: `run_import_production()`
    KHÔNG nhận bất kỳ tham số DI thủ công nào (không `identity_registry=`,
    không `confirmed_adjustment_source=`, không `eligible_costs_authority=`),
    tự nạp ba nguồn canonical committed và chạy `run_import()` thật.

    Đây là caller mà một non-test entry point thật (CLI TASK-112 tương lai, v.v.)
    sẽ dùng — không stub/mock/bypass/Golden-specific branch."""
    result = run_import_production(GOLDEN_FIXTURE, config_dir=CONFIG_DIR)
    line = _order(result, "BH62063").lines[0]

    assert line.accounting_purchase_price == Decimal("7000000")
    assert line.kpi_purchase_price == Decimal("7000000")
    assert line.kpi_purchase_price_provenance == KPI_PURCHASE_NO_CONFIRMED_ADJUSTMENT
    assert line.eligible_kpi_profit == Decimal("500000")

    # Provenance của EligibleCosts authority thật sự được dùng (B02) — không
    # chỉ tồn tại trong config mà không ai đọc.
    authority = load_eligible_costs_authority(ELIGIBLE_COSTS_FILE)
    assert authority.is_valid is True
    assert authority.provenance == PROVENANCE_ELIGIBLE_COSTS_EMPTY_SET


def test_bh62063_default_run_import_without_kpi_wiring_is_still_pending():
    """0 blast radius: gọi `run_import()` PURE (thư viện, không phải
    composition) mà không truyền `confirmed_adjustment_source=`/
    `identity_registry=`/`eligible_costs_authority=` (hành vi mặc định của
    mọi lời gọi `run_import()` hiện có, bao gồm Golden Baseline) vẫn giữ
    nguyên Pending — không đổi."""
    result = run_import(GOLDEN_FIXTURE, config_dir=CONFIG_DIR)
    line = _order(result, "BH62063").lines[0]
    assert line.accounting_purchase_price is None
    assert line.kpi_purchase_price is None
    assert line.eligible_kpi_profit is None
