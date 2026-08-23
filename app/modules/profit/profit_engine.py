"""`AccountingProfit` — Universal formula, độc lập hoàn toàn với KPI Adjustment.

    AccountingProfit = (SellPrice - AccountingPurchasePrice) * Quantity

(`docs/analysis/03_RULE_CLASSIFICATION.md` §U). Không có số hạng nào liên
quan `KpiPurchaseAdjustment` — DEC-126 điểm 1 nhắc lại tường minh: hai luồng
số liệu kế toán và KPI tách biệt hoàn toàn, không chỉ ở công thức mà cả ở dữ
liệu. Module này không phụ thuộc `app.modules.adjustment` theo bất kỳ cách
nào.

Một input còn thiếu (`sell_price`/`quantity`/`accounting_purchase_price` là
`None` — ví dụ giá nhập còn Pending vì chưa có Price Master, TASK-105) khiến
`accounting_profit` là `None`, không bao giờ suy đoán thành `0` (DEC-103,
`governance/core/03_DATA_MODEL_RULES.md` §5).
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from app.modules.domain.models import WorkingLine


def compute_accounting_profit(line: WorkingLine) -> Optional[Decimal]:
    if (
        line.sell_price is None
        or line.accounting_purchase_price is None
        or line.quantity is None
    ):
        return None
    return (line.sell_price - line.accounting_purchase_price) * line.quantity


def apply_accounting_profit(lines: list[WorkingLine]) -> list[WorkingLine]:
    for line in lines:
        line.accounting_profit = compute_accounting_profit(line)
    return lines
