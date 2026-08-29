"""Golden #3 — BH62439, real production trace: Quantity > 1 AND Discount != 0.

Không phải Golden Baseline (`test_golden_baseline.py`, đã frozen) và không
phải Golden #1 (`test_golden_bh62063_kpi.py`, BH62063 có Quantity=1,
Discount=0 — hai field đó trùng số ở Golden #1 chỉ vì Discount=0, một trùng
hợp số học riêng, không phải bằng chứng hai capability giống nhau).

BH62439 là một đơn hàng THẬT, 4 dòng (`source_row` 50-53), trong CHÍNH
`tests/fixtures/golden/period_2026_01.xlsx` đã dùng cho Golden Baseline.
Dòng thứ ba của đơn này (`Điều hòa Daikin FTHF25XVMV`, `source_row=52`) có
`Quantity=2` và `Discount=100.000` — case thật đầu tiên nơi cả hai điều kiện
cùng xảy ra trên một dòng có giá vốn ĐÃ resolve. Owner xác nhận giá vốn qua
CÙNG cơ chế `OWNER_MANUAL_LEGACY_CONFIRMATION` đã dùng cho BH62063 (Golden #1
session brief §2) — xem entry `HCR-BH62439-20260108-1` trong
`data/historical_confirmed/registry.jsonl`.

Ba dòng còn lại của CHÍNH đơn BH62439 KHÔNG có entry registry, nên vẫn phải
Pending — test này khoá luôn tính chất "order aggregation không làm rò rỉ giá
vốn từ dòng đã confirm sang dòng khác trong cùng đơn".
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from app.composition import run_import_production
from app.modules.domain.models import (
    KPI_PURCHASE_NO_CONFIRMED_ADJUSTMENT,
    PRICE_SOURCE_PENDING,
)

GOLDEN_FIXTURE = Path("tests/fixtures/golden/period_2026_01.xlsx")
CONFIG_DIR = Path("config")

TARGET_PRODUCT = "Điều hòa Daikin FTHF25XVMV"


def _order(result, order_id):
    return next(o for o in result.orders if o.order_id == order_id)


def _line(order, product_raw):
    return next(l for l in order.lines if l.product_raw == product_raw)


def test_bh62439_normal_production_composition_reaches_eligible_kpi_profit():
    """Golden #3 — REAL acceptance qua `run_import_production()`, KHÔNG DI/mock.

    Oracle độc lập được ghi TRƯỚC khi chạy (session brief §"ORACLE BEFORE
    CODE"):

        AccountingProfit    = (SellPrice - AccountingPurchasePrice) * Quantity
                            = (10.500.000 - 10.250.000) * 2 = 500.000
        EligibleKpiProfit   = (SellPrice - KpiPurchasePrice) * Quantity - Discount
                            = (10.500.000 - 10.250.000) * 2 - 100.000 = 400.000
    """
    result = run_import_production(GOLDEN_FIXTURE, config_dir=CONFIG_DIR)
    line = _line(_order(result, "BH62439"), TARGET_PRODUCT)

    assert line.quantity == Decimal("2")
    assert line.sell_price == Decimal("10500000")
    assert line.discount == Decimal("100000")
    assert line.price_source == "OWNER_MANUAL_LEGACY_CONFIRMATION"
    assert line.accounting_purchase_price == Decimal("10250000")
    assert line.kpi_purchase_price == Decimal("10250000")
    assert line.kpi_purchase_price_provenance == KPI_PURCHASE_NO_CONFIRMED_ADJUSTMENT

    assert line.accounting_profit == Decimal("500000")
    assert line.eligible_kpi_profit == Decimal("400000")


def test_bh62439_quantity_multiplication_is_applied_to_both_profit_fields():
    """1. Quantity > 1 multiplication — cả hai công thức đều nhân Quantity,
    không phải cộng dồn Quantity lần dòng hay bỏ sót thừa số."""
    result = run_import_production(GOLDEN_FIXTURE, config_dir=CONFIG_DIR)
    line = _line(_order(result, "BH62439"), TARGET_PRODUCT)

    unit_margin = line.sell_price - line.accounting_purchase_price
    assert line.accounting_profit == unit_margin * line.quantity
    kpi_unit_margin = line.sell_price - line.kpi_purchase_price
    assert line.eligible_kpi_profit == kpi_unit_margin * line.quantity - line.discount


def test_bh62439_discount_is_not_double_counted():
    """3. Discount != 0 chỉ trừ MỘT LẦN, và chỉ trong EligibleKpiProfit —
    AccountingProfit hoàn toàn không có số hạng Discount nào (DEC-126 điểm 1).

    Đây là "important new evidence" của Golden #3: `AccountingProfit` và
    `EligibleKpiProfit` phải LỆCH NHAU đúng bằng `Discount`, không trùng số
    như ở BH62063 (nơi Discount=0 làm chúng trùng một cách tình cờ)."""
    result = run_import_production(GOLDEN_FIXTURE, config_dir=CONFIG_DIR)
    line = _line(_order(result, "BH62439"), TARGET_PRODUCT)

    assert line.discount != Decimal("0")
    assert line.accounting_profit != line.eligible_kpi_profit
    assert line.accounting_profit - line.eligible_kpi_profit == line.discount


def test_bh62439_accounting_profit_is_independent_of_kpi_purchase_price():
    """4. AccountingProfit không phụ thuộc KpiPurchasePrice/KPI Adjustment —
    tính lại bằng ĐÚNG AccountingPurchasePrice (không phải KpiPurchasePrice,
    dù ở dòng này hai giá trị trùng số vì không có confirmed adjustment nào)."""
    result = run_import_production(GOLDEN_FIXTURE, config_dir=CONFIG_DIR)
    line = _line(_order(result, "BH62439"), TARGET_PRODUCT)

    assert line.accounting_profit == (
        (line.sell_price - line.accounting_purchase_price) * line.quantity
    )


def test_bh62439_eligible_kpi_profit_uses_canonical_formula():
    """5. EligibleKpiProfit = (SellPrice - KpiPurchasePrice) * Quantity - Discount
    (`app/modules/kpi/kpi_profit_engine.py::compute_eligible_kpi_profit`,
    DEC-143 + DEC-144 — EligibleCosts = {} và OtherKpiAdjustment = 0)."""
    result = run_import_production(GOLDEN_FIXTURE, config_dir=CONFIG_DIR)
    line = _line(_order(result, "BH62439"), TARGET_PRODUCT)

    assert line.eligible_kpi_profit == (
        (line.sell_price - line.kpi_purchase_price) * line.quantity - line.discount
    )


def test_bh62439_other_lines_in_same_order_stay_pending():
    """Order/line aggregation không rò rỉ giá vốn: 3 dòng khác của CHÍNH đơn
    BH62439 không có registry entry riêng nên vẫn phải Pending — một giá vốn
    đã confirm ở MỘT dòng không được lan sang các dòng khác cùng OrderID."""
    result = run_import_production(GOLDEN_FIXTURE, config_dir=CONFIG_DIR)
    order = _order(result, "BH62439")
    assert len(order.lines) == 4

    other_products = {
        "Tủ lạnh Panasonic NR-BX471GPKV",
        "Máy Giặt Sấy LG FV1414H3BA",
        "Máy lạnh Daikin Inverter 2 HP FTKB50ZVMV",
    }
    for line in order.lines:
        if line.product_raw in other_products:
            assert line.accounting_purchase_price is None
            assert line.price_source == PRICE_SOURCE_PENDING
            assert line.accounting_profit is None
            assert line.eligible_kpi_profit is None


def test_bh62439_default_run_import_without_kpi_wiring_is_still_pending():
    """0 blast radius: `run_import()` PURE (không DI, giống mọi lời gọi hiện có
    kể cả Golden Baseline) vẫn giữ nguyên Pending cho BH62439 — thêm entry
    registry KHÔNG đổi hành vi mặc định."""
    from app.pipeline import run_import

    result = run_import(GOLDEN_FIXTURE, config_dir=CONFIG_DIR)
    line = _line(_order(result, "BH62439"), TARGET_PRODUCT)
    assert line.accounting_purchase_price is None
    assert line.kpi_purchase_price is None
    assert line.eligible_kpi_profit is None
