"""`KpiPurchasePrice` + `EligibleKpiProfit` — TASK-108B minimum B7/B8 slice
(DEC-143 + DEC-144, Golden #1 KPI vertical slice).

Tách biệt HOÀN TOÀN khỏi `AccountingProfit` (`profit_engine.py`, TASK-107,
DEC-126 điểm 1) — hai capability khác nhau, chỉ dùng chung
`accounting_purchase_price` làm input, không chia sẻ field/công thức nào khác.

    KpiPurchasePrice:
      confirmed adjustment có hiệu lực       : AccountingPurchasePrice + amount
      xác định KHÔNG có (source loaded, 0 record khớp)
                                              : AccountingPurchasePrice,
                                                provenance Config:NoConfirmedAdjustment
      source unavailable/invalid/parse-failed: None (Pending) — DEC-144 §3,
                                                tuyệt đối không suy đoán absence/0

    EligibleKpiProfit = (SellPrice − KpiPurchasePrice) × Quantity − Discount
                        − SUM(EligibleCosts) + OtherKpiAdjustment

Theo DEC-143 (`OD-108B-01`): `EligibleCosts = {}` là một CLOSED EMPTY SET có
thẩm quyền (`config/eligible_costs.yaml`, KHÔNG phải fallback khi thiếu dữ
liệu — DEC-103), và `OtherKpiAdjustment = 0` là định nghĩa nghiệp vụ tường
minh. Dạng rút gọn hiện hành:

    EligibleKpiProfit = (SellPrice − KpiPurchasePrice) × Quantity − Discount

Bất kỳ input Pending/thiếu nào (accounting_purchase_price, sell_price,
quantity, hoặc confirmed-adjustment source unavailable) khiến CẢ HAI
`kpi_purchase_price`/`eligible_kpi_profit` là `None` — không bao giờ suy đoán
0 (DEC-103).
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
from typing import Optional

from app.modules.adjustment.confirmed_adjustment_source import (
    ConfirmedAdjustmentSource,
)
from app.modules.config.loader import load_yaml
from app.modules.domain.models import (
    KPI_PURCHASE_NO_CONFIRMED_ADJUSTMENT,
    KPI_PURCHASE_PENDING,
    WorkingLine,
)

# DEC-143 §1 (`OD-108B-01`) — tập rỗng có thẩm quyền, không phải giá trị mặc
# định khi thiếu dữ liệu. `SUM(EligibleCosts) = 0` vì tập category luôn rỗng
# trong Phase 1 (không có nguồn cost per-line nào tồn tại) — thêm một category
# tương lai đòi hỏi Owner Decision riêng (source/scope/sign/ownership/
# effective date/no-double-count, DEC-143 điểm 5), không phải hardcode ở đây.
PROVENANCE_ELIGIBLE_COSTS_EMPTY_SET = "Config:EmptySet(OD-108B-01)"
# DEC-143 §3 — định nghĩa nghiệp vụ tường minh, không phải fallback kỹ thuật.
OTHER_KPI_ADJUSTMENT = Decimal("0")


def load_eligible_cost_categories(path: Path) -> tuple[str, ...]:
    """Chính sự hiện diện tường minh của `eligible_cost_categories: []` trong
    file (không phải absence của file) là bằng chứng cho tập rỗng có thẩm
    quyền (DEC-143 §1) — khác một fallback kỹ thuật khi thiếu config."""
    return tuple(load_yaml(path).get("eligible_cost_categories", []))


def resolve_kpi_purchase_price(
    line: WorkingLine, source: Optional[ConfirmedAdjustmentSource]
) -> tuple[Optional[Decimal], str]:
    if line.accounting_purchase_price is None:
        return None, KPI_PURCHASE_PENDING  # AccountingPurchasePrice unavailable
    if source is None or not source.is_available:
        return None, KPI_PURCHASE_PENDING  # SOURCE_UNAVAILABLE (DEC-144 §3)
    record = source.lookup(line.order_id)
    if record is not None:
        return (
            line.accounting_purchase_price + record.amount,
            f"Confirmed:{record.confirmed_by}",
        )
    return line.accounting_purchase_price, KPI_PURCHASE_NO_CONFIRMED_ADJUSTMENT


def compute_eligible_kpi_profit(line: WorkingLine) -> Optional[Decimal]:
    if (
        line.sell_price is None
        or line.kpi_purchase_price is None
        or line.quantity is None
    ):
        return None
    return (
        (line.sell_price - line.kpi_purchase_price) * line.quantity
        - line.discount
        + OTHER_KPI_ADJUSTMENT
    )


def apply_kpi_profit(
    lines: list[WorkingLine],
    confirmed_adjustment_source: Optional[ConfirmedAdjustmentSource],
) -> list[WorkingLine]:
    for line in lines:
        price, provenance = resolve_kpi_purchase_price(
            line, confirmed_adjustment_source
        )
        line.kpi_purchase_price = price
        line.kpi_purchase_price_provenance = provenance
        line.eligible_kpi_profit = compute_eligible_kpi_profit(line)
    return lines
