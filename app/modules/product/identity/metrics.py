"""Metrics vận hành — data contract §15.

## Metric là READ-ONLY, và điều đó được thi hành bằng đồ thị import

`INV-85` cấm mọi vòng phản hồi kiểu "hạ ngưỡng để tăng `AUTO_RESOLUTION_RATE`".
Cách rẻ nhất để bảo đảm điều đó không xảy ra là làm cho nó không biểu diễn
được: `resolver.py` **không import** file này. Metric đọc kết quả của resolver;
resolver không bao giờ đọc metric. `CHECK-105D-08`/`INV-85` kiểm bằng một
assertion import-graph, không bằng một lời hứa.

## Không có dữ liệu khách hàng ở đây

`INV-86`: mọi trường dưới đây là số đếm và số hiệu version. Không tên, không
SĐT, không địa chỉ, không IMEI — kể cả `raw_product_identity`, vốn là dữ liệu
kế toán chứ không phải PII nhưng cũng không cần thiết cho một metric.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from app.modules.product.identity.evidence import (
    ResolutionMethod,
    is_auto_resolvable,
)
from app.modules.product.identity.identity import (
    PendingProduct,
    RequiresConfirmation,
    Resolved,
)
from app.modules.product.identity.service import BatchResolution


@dataclass(frozen=True)
class ResolutionMetrics:
    """Sáu metric §15 + ba số hiệu bắt buộc của `INV-84`.

    `INV-84` không phải hình thức: hai tỉ lệ đo trên hai `pp_version_id` khác
    nhau không so sánh được với nhau, và ghi kèm số hiệu là cách duy nhất để
    một người đọc biểu đồ sáu tháng sau biết điều đó.
    """

    distinct_count: int
    auto_resolution_rate: Decimal
    manual_confirmation_rate: Decimal
    pending_rate: Decimal
    reuse_rate: Decimal
    manual_confirmation_actions_per_100_orders: Decimal
    mapping_store_revision: int
    pp_version_id: Optional[str]
    tracking_capture_id: Optional[str]

    def sums_to_one(self) -> bool:
        """`INV-83` — ba tập rời nhau và phủ kín `D`."""
        return (
            self.auto_resolution_rate
            + self.manual_confirmation_rate
            + self.pending_rate
        ) == Decimal(1)


def compute(
    result: BatchResolution,
    *,
    mapping_store_revision: int,
    pp_version_id: Optional[str] = None,
    tracking_capture_id: Optional[str] = None,
    confirmation_action_count: int = 0,
) -> ResolutionMetrics:
    """Mẫu số `D` = số DISTINCT identity SAU khi loại nhánh pre-cutover.

    `BatchResolution.distinct` đã loại sẵn nhánh pre-cutover (`INV-46`), nên
    không có chỗ nào ở đây phải nhớ làm điều đó — cấu trúc dữ liệu mang luật.
    """
    total = result.distinct_count
    if total == 0:
        zero = Decimal(0)
        return ResolutionMetrics(
            distinct_count=0,
            auto_resolution_rate=zero,
            manual_confirmation_rate=zero,
            pending_rate=zero,
            reuse_rate=zero,
            manual_confirmation_actions_per_100_orders=zero,
            mapping_store_revision=mapping_store_revision,
            pp_version_id=pp_version_id,
            tracking_capture_id=tracking_capture_id,
        )

    auto = manual = pending = reuse = 0
    for resolution in result.resolutions:
        outcome = resolution.outcome
        method = resolution.resolution_method
        if isinstance(outcome, Resolved) and method is not None and is_auto_resolvable(
            method
        ):
            auto += 1
            if method is ResolutionMethod.ALIAS_EXACT:
                reuse += 1
        elif isinstance(outcome, RequiresConfirmation):
            manual += 1
        elif isinstance(outcome, PendingProduct):
            pending += 1

    denominator = Decimal(total)
    order_ids = {
        order_id
        for identity in result.distinct
        for order_id in identity.order_ids
    }
    orders = Decimal(len(order_ids)) if order_ids else Decimal(1)

    return ResolutionMetrics(
        distinct_count=total,
        auto_resolution_rate=Decimal(auto) / denominator,
        manual_confirmation_rate=Decimal(manual) / denominator,
        pending_rate=Decimal(pending) / denominator,
        reuse_rate=Decimal(reuse) / denominator,
        manual_confirmation_actions_per_100_orders=(
            Decimal(100) * Decimal(confirmation_action_count) / orders
        ),
        mapping_store_revision=mapping_store_revision,
        pp_version_id=pp_version_id,
        tracking_capture_id=tracking_capture_id,
    )


def wrong_mapping_correction_rate(
    *, correction_events: int, active_confirmed_at_window_start: int
) -> Decimal:
    """Metric thứ năm — mẫu số RIÊNG, không dùng `D` (§15).

    Cửa sổ thời gian `W` phải do caller ghi rõ; hàm này cố ý không tự chọn một
    cửa sổ mặc định, vì một tỉ lệ sửa mapping không nói lên điều gì nếu không
    biết nó đo trong bao lâu.
    """
    if active_confirmed_at_window_start == 0:
        return Decimal(0)
    return Decimal(correction_events) / Decimal(active_confirmed_at_window_start)
