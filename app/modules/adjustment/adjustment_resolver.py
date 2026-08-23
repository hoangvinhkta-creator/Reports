"""`AdjustmentResolver` — số tiền điều chỉnh KPI đề xuất mặc định (DEC-125).

Khác `PendingPriceProvider` (TASK-105): module này **không** nối vào
`app.pipeline.run_import()`. DEC-125 điểm 4: loại điều chỉnh (`Qua kho`,
`NCC giao`, `KHBH`, `Thợ lắp`) và phương tiện giao hàng là thứ người dùng
**chọn tay sau khi import** — không có cột nào trong 17 cột raw để tự động
quét (`docs/analysis/01_DATA_MAPPING.md` mục "Field trong Working Data không
có nguồn thô"). Resolver chỉ tính **số tiền đề xuất** khi đã biết loại điều
chỉnh + ngữ cảnh cần thiết (phương tiện giao, hoặc có phải điều hòa) — để
tầng override thủ công thật (Phase 2/3, TASK-202/302/305) gọi tới và điền
sẵn giá trị gợi ý, người dùng luôn ghi đè được, không bao giờ tự động áp.

`amount is None` nghĩa là "không có căn cứ để đề xuất, phải nhập tay" — không
bao giờ suy đoán hay coi 0 (DEC-103, `governance/core/03_DATA_MODEL_RULES.md`
§5).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Optional

from app.modules.config.loader import load_yaml


@dataclass(frozen=True)
class AdjustmentResolution:
    amount: Optional[Decimal]
    source_of_value: str


class AdjustmentResolver:
    def __init__(
        self,
        delivery_method_tiers: dict[str, dict[str, int]],
        air_conditioner_only_defaults: dict[str, int],
    ):
        self._delivery_method_tiers = delivery_method_tiers
        self._air_conditioner_only_defaults = air_conditioner_only_defaults

    @classmethod
    def from_yaml(cls, path: Path) -> "AdjustmentResolver":
        data = load_yaml(path)
        return cls(
            delivery_method_tiers=data.get("delivery_method_tiers", {}),
            air_conditioner_only_defaults=data.get(
                "air_conditioner_only_defaults", {}
            ),
        )

    def resolve_suggested_amount(
        self,
        adjustment_type: str,
        *,
        delivery_method: Optional[str] = None,
        is_air_conditioner: Optional[bool] = None,
    ) -> AdjustmentResolution:
        if adjustment_type in self._delivery_method_tiers:
            tiers = self._delivery_method_tiers[adjustment_type]
            if delivery_method is not None and delivery_method in tiers:
                return AdjustmentResolution(
                    Decimal(str(tiers[delivery_method])),
                    f"Auto:DeliveryMethod({delivery_method})",
                )
            return AdjustmentResolution(None, "Manual:NoDeliveryMethodMatch")

        if adjustment_type in self._air_conditioner_only_defaults:
            if is_air_conditioner:
                amount = self._air_conditioner_only_defaults[adjustment_type]
                return AdjustmentResolution(
                    Decimal(str(amount)), "Auto:AirConditionerDefault"
                )
            return AdjustmentResolution(None, "Manual:NotAirConditionerOrUnknown")

        return AdjustmentResolution(None, "Manual:UnknownAdjustmentType")
