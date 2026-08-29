"""`kpi_profit_engine` — TASK-108B minimum B7/B8 slice (DEC-143 + DEC-144,
Golden #1 KPI vertical slice).

Golden #1 tự nó có `Quantity = 1`, `Discount = 0` — không đủ để phân biệt
`EligibleKpiProfit` khỏi `AccountingProfit` (S053 §6 đã cảnh báo đúng điều
này). Các test dưới đây CỐ Ý dùng quantity > 1 và discount > 0.
"""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

from app.modules.adjustment.confirmed_adjustment_source import (
    ConfirmedAdjustmentRecord,
    ConfirmedAdjustmentSource,
)
from app.modules.domain.models import (
    KPI_PURCHASE_NO_CONFIRMED_ADJUSTMENT,
    KPI_PURCHASE_PENDING,
    RawRow,
    WorkingLine,
)
from app.modules.kpi.kpi_profit_engine import (
    apply_kpi_profit,
    compute_eligible_kpi_profit,
    load_eligible_cost_categories,
    resolve_kpi_purchase_price,
)
from app.modules.profit.profit_engine import compute_accounting_profit

_RAW = RawRow(
    source_file="f.xlsx", source_sheet="s", source_row=1, row_hash="h",
    date=None, order_id="BH0001", note_raw=None, product_raw=None,
    customer_code=None, customer=None, address=None, phone=None,
    quantity=None, sell_price=None, total_sales_raw=None, discount=None,
    employee_raw=None, shipper_raw=None, delivery_cost=None, imei=None,
    source_profit=None,
)


def _line(**overrides) -> WorkingLine:
    base = WorkingLine(
        raw=_RAW,
        order_id="BH0001",
        date=None,
        month=None,
        note_raw=None,
        product_raw=None,
        customer_code=None,
        customer=None,
        address=None,
        phone=None,
        quantity=Decimal("2"),
        sell_price=Decimal("300000"),
        discount=Decimal("50000"),
        total_sales=Decimal("550000"),
        employee_raw=None,
        accounting_purchase_price=Decimal("200000"),
    )
    return replace(base, **overrides)


_EMPTY_LOADED = ConfirmedAdjustmentSource(records={})
_UNAVAILABLE = ConfirmedAdjustmentSource(records=None)
_WITH_RECORD = ConfirmedAdjustmentSource(
    records={
        "BH0001": ConfirmedAdjustmentRecord(
            order_id="BH0001", amount=Decimal("10000"),
            confirmed_by="chu.du.an", reason="test",
        )
    }
)


# ------------------------------------------------- resolve_kpi_purchase_price

def test_accounting_purchase_price_pending_propagates_to_kpi_pending():
    line = _line(accounting_purchase_price=None)
    price, provenance = resolve_kpi_purchase_price(line, _EMPTY_LOADED)
    assert price is None
    assert provenance == KPI_PURCHASE_PENDING


def test_missing_source_is_pending():
    line = _line()
    price, provenance = resolve_kpi_purchase_price(line, None)
    assert price is None
    assert provenance == KPI_PURCHASE_PENDING


def test_unavailable_source_is_pending():
    line = _line()
    price, provenance = resolve_kpi_purchase_price(line, _UNAVAILABLE)
    assert price is None
    assert provenance == KPI_PURCHASE_PENDING


def test_loaded_empty_source_is_determined_absence():
    line = _line()
    price, provenance = resolve_kpi_purchase_price(line, _EMPTY_LOADED)
    assert price == line.accounting_purchase_price
    assert provenance == KPI_PURCHASE_NO_CONFIRMED_ADJUSTMENT


def test_confirmed_record_adds_amount_to_accounting_purchase_price():
    line = _line()
    price, provenance = resolve_kpi_purchase_price(line, _WITH_RECORD)
    assert price == Decimal("200000") + Decimal("10000")
    assert provenance == "Confirmed:chu.du.an"


# ---------------------------------------------------- compute_eligible_kpi_profit

def test_discount_subtracted_exactly_once_and_quantity_multiplies_unit_diff():
    """SellPrice=300000, KpiPurchasePrice=200000, Quantity=2, Discount=50000.

    (300000 - 200000) * 2 - 50000 = 150000. Đọc nguyên văn dạng prose sai
    (DEC-143 Reason §4) sẽ cho một số khác hẳn."""
    line = _line(kpi_purchase_price=Decimal("200000"))
    assert compute_eligible_kpi_profit(line) == Decimal("150000")


def test_quantity_one_discount_zero_matches_golden_1_shape():
    line = _line(
        quantity=Decimal("1"), discount=Decimal("0"),
        sell_price=Decimal("7500000"),
        accounting_purchase_price=Decimal("7000000"),
        kpi_purchase_price=Decimal("7000000"),
    )
    assert compute_eligible_kpi_profit(line) == Decimal("500000")


def test_eligible_kpi_profit_none_when_kpi_purchase_price_pending():
    line = _line(kpi_purchase_price=None)
    assert compute_eligible_kpi_profit(line) is None


def test_eligible_kpi_profit_diverges_from_accounting_profit_when_discount_nonzero():
    """Accounting profit và KPI profit là hai field tách biệt (DEC-126 điểm
    1) — khi Discount != 0, hai con số PHẢI khác nhau, không được trùng."""
    line = _line(kpi_purchase_price=Decimal("200000"))
    accounting_profit = compute_accounting_profit(line)
    eligible_kpi_profit = compute_eligible_kpi_profit(line)
    assert accounting_profit == Decimal("200000")  # (300000-200000)*2, no discount
    assert eligible_kpi_profit == Decimal("150000")  # cùng, trừ thêm 50000 discount
    assert accounting_profit != eligible_kpi_profit


# ------------------------------------------------------------ apply_kpi_profit

def test_apply_kpi_profit_sets_all_three_fields_together():
    line = _line()
    apply_kpi_profit([line], _WITH_RECORD)
    assert line.kpi_purchase_price == Decimal("210000")
    assert line.kpi_purchase_price_provenance == "Confirmed:chu.du.an"
    assert line.eligible_kpi_profit == (Decimal("300000") - Decimal("210000")) * 2 - Decimal("50000")


# ------------------------------------------------------- EligibleCosts (DEC-143)

def test_eligible_cost_categories_closed_empty_set(tmp_path):
    path = tmp_path / "eligible_costs.yaml"
    path.write_text("eligible_cost_categories: []\n", encoding="utf-8")
    assert load_eligible_cost_categories(path) == ()


def test_real_eligible_costs_config_is_closed_empty_set():
    """`config/eligible_costs.yaml` thật đã commit — tập rỗng có thẩm quyền
    (DEC-143 §1), không phải absence của file."""
    from pathlib import Path

    assert load_eligible_cost_categories(Path("config/eligible_costs.yaml")) == ()
