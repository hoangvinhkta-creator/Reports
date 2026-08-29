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

## EligibleCosts authority gating (Golden #1 Repair Batch #1, B02)

`config/eligible_costs.yaml` là MỘT authority có thẩm quyền (DEC-143 §1),
không phải config trang trí — `EligibleKpiProfit` chỉ được tính khi authority
đó nạp + validate THÀNH CÔNG (`EligibleCostsAuthority.is_valid`). Thiếu file /
không đọc được / YAML hỏng / thiếu key `eligible_cost_categories` tường minh /
category khác rỗng (engine hiện tại KHÔNG tính category cost nào — semantically
non-authoritative cho slice này) đều fail-closed: `eligible_kpi_profit = None`.
`kpi_purchase_price` KHÔNG bị gate bởi authority này — nó chỉ phụ thuộc
`confirmed_adjustment_source` (capability khác, DEC-126 điểm 1).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Optional

import yaml

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


@dataclass(frozen=True)
class EligibleCostsAuthority:
    """Kết quả nạp + validate `config/eligible_costs.yaml`. `is_valid=False`
    là fail-closed — `EligibleKpiProfit` không được tính khi authority không
    hợp lệ, dù `kpi_purchase_price` vẫn resolve bình thường."""

    is_valid: bool
    categories: tuple[str, ...]
    provenance: str


AUTHORITY_UNAVAILABLE = EligibleCostsAuthority(
    is_valid=False, categories=(), provenance="SOURCE_UNAVAILABLE"
)


def load_eligible_costs_authority(path: Path) -> EligibleCostsAuthority:
    """File thiếu/không đọc được/YAML hỏng/top-level không phải mapping (scalar,
    sequence, null)/thiếu key tường minh/category khác rỗng ->
    `AUTHORITY_UNAVAILABLE` (fail-closed, KHÔNG suy đoán tập rỗng khi thiếu —
    đối xứng với `DEC-103`). Chỉ `eligible_cost_categories: []` tường minh mới
    là authority hợp lệ cho engine hiện tại (§B02 brief — không tự xây engine
    tính category cost nào).

    `data` phải là `dict` TRƯỚC khi kiểm tra `in`/index — YAML top-level scalar
    (vd. `42`) parse thành công (không raise `yaml.YAMLError`) nhưng
    `"key" not in 42` raise `TypeError`, không phải fail-closed có kiểm soát
    (Golden #1 Validation Closure, B02)."""
    try:
        data = load_yaml(path)
    except (OSError, yaml.YAMLError):
        return AUTHORITY_UNAVAILABLE
    if not isinstance(data, dict):
        return AUTHORITY_UNAVAILABLE
    if "eligible_cost_categories" not in data:
        return AUTHORITY_UNAVAILABLE
    raw_categories = data["eligible_cost_categories"]
    if not isinstance(raw_categories, list):
        return AUTHORITY_UNAVAILABLE
    categories = tuple(raw_categories)
    if categories:
        return AUTHORITY_UNAVAILABLE  # category chưa được engine này hỗ trợ
    return EligibleCostsAuthority(
        is_valid=True,
        categories=categories,
        provenance=PROVENANCE_ELIGIBLE_COSTS_EMPTY_SET,
    )


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
            f"Confirmed:{record.confirmed_by}@{record.confirmed_at}",
        )
    return line.accounting_purchase_price, KPI_PURCHASE_NO_CONFIRMED_ADJUSTMENT


def compute_eligible_kpi_profit(
    line: WorkingLine, authority: EligibleCostsAuthority
) -> Optional[Decimal]:
    if not authority.is_valid:
        return None  # EligibleCosts authority missing/invalid — fail closed (B02)
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
    eligible_costs_authority: Optional[EligibleCostsAuthority] = None,
) -> list[WorkingLine]:
    authority = eligible_costs_authority or AUTHORITY_UNAVAILABLE
    for line in lines:
        price, provenance = resolve_kpi_purchase_price(
            line, confirmed_adjustment_source
        )
        line.kpi_purchase_price = price
        line.kpi_purchase_price_provenance = provenance
        line.eligible_kpi_profit = compute_eligible_kpi_profit(line, authority)
    return lines
