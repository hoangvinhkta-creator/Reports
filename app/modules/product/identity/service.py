"""Biên ứng dụng — định tuyến cutover, batch, và tra cứu cross-system.

## Định tuyến cutover là một cái CỔNG, không phải một nhánh `if` bên trong

`INV-47` yêu cầu resolver, catalog snapshot và price provider **không được gọi
lần nào** trên nhánh pre-cutover — dù registry có entry hay không.

Một `if sale_date < CUTOVER_DATE` đặt *bên trong* resolver không thoả được điều
đó: để vào tới cái `if`, resolver đã được dựng, và dựng resolver là đã đọc
catalog. Nên `resolve_batch()` nhận một **factory** và chỉ gọi factory khi tồn
tại ít nhất một dòng post-cutover. Với một batch toàn pre-cutover, số lời gọi
tới factory là 0 — và đó chính là điều `CHECK-105D-01` đếm bằng spy.

## `sale_date`, không bao giờ `import_date`

`INV-48`. `SalesRowRef` cố ý **không có** trường `import_date`: một trường
không tồn tại thì không ai phân loại nhầm bằng nó. Bản ghi đến muộn đi nhánh
lịch sử vì `sale_date` của nó nói vậy.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Sequence

from app.modules.product.identity.audit import AffectedScope
from app.modules.product.identity.cross_system import CrossSystemStatus
from app.modules.product.identity.identity import (
    AttemptedSource,
    HistoricalConfirmed,
    PendingProduct,
    PendingReason,
    Provenance,
    ResolutionOutcome,
)
from app.modules.product.identity.registry import (
    CUTOVER_DATE,
    HistoricalConfirmedRegistry,
    PROVENANCE_HISTORICAL,
    RegistryEntryStatus,
)
from app.modules.product.identity.resolver import (
    DistinctIdentity,
    IdentityResolution,
    ProductIdentityResolver,
    SalesRowRef,
    distinct_identities,
)
from app.modules.product.identity.store import StoreView

ResolverFactory = Callable[[], ProductIdentityResolver]


@dataclass(frozen=True)
class BatchResolution:
    """Kết quả của một batch: nhánh lịch sử + nhánh post-cutover, tách bạch."""

    historical: tuple[tuple[SalesRowRef, ResolutionOutcome], ...]
    resolutions: tuple[IdentityResolution, ...]
    distinct: tuple[DistinctIdentity, ...]

    def outcome_for(self, raw_identity_key: str) -> Optional[ResolutionOutcome]:
        for resolution in self.resolutions:
            if resolution.identity.raw_identity_key == raw_identity_key:
                return resolution.outcome
        return None

    def resolution_for(self, raw_identity_key: str) -> Optional[IdentityResolution]:
        for resolution in self.resolutions:
            if resolution.identity.raw_identity_key == raw_identity_key:
                return resolution
        return None

    @property
    def distinct_count(self) -> int:
        """`|D|` — mẫu số chung của §15, ĐÃ loại nhánh pre-cutover (`INV-46`)."""
        return len(self.distinct)


def resolve_batch(
    rows: Sequence[SalesRowRef],
    *,
    registry: HistoricalConfirmedRegistry,
    resolver_factory: ResolverFactory,
) -> BatchResolution:
    """Định tuyến theo `sale_date`, rồi resolve tập DISTINCT post-cutover.

    Toàn bộ phép này là ĐỌC THUẦN: không command nào được phát, nên
    `current_revision()` của store không đổi sau một batch (`INV-70`,
    `CHECK-105D-24`).
    """
    historical: list[tuple[SalesRowRef, ResolutionOutcome]] = []
    post_cutover: list[SalesRowRef] = []

    for row in rows:
        if row.sale_date < CUTOVER_DATE:
            historical.append((row, _historical_outcome(row, registry)))
        else:
            post_cutover.append(row)

    if not post_cutover:
        return BatchResolution(
            historical=tuple(historical), resolutions=(), distinct=()
        )

    distinct = distinct_identities(post_cutover)
    resolver = resolver_factory()
    return BatchResolution(
        historical=tuple(historical),
        resolutions=resolver.resolve_all(distinct),
        distinct=distinct,
    )


def _historical_outcome(
    row: SalesRowRef, registry: HistoricalConfirmedRegistry
) -> ResolutionOutcome:
    """`INV-46` — đúng hai kết cục, không có kết cục thứ ba.

    Giá đến TỪ registry; resolver không tính nó (`CHECK-105D-16` ngoại lệ duy
    nhất). Entry thiếu `confirmed_identity` vẫn là `HISTORICAL_CONFIRMED`
    (`INV-50`) — vắng identity KHÔNG kích hoạt resolver để điền vào chỗ trống.
    """
    entry = registry.lookup(row.order_id, row.raw_identity_key, row.sale_date)
    if entry is not None and entry.status is RegistryEntryStatus.CONFIRMED:
        # `entry.provenance` — không hardcode `PROVENANCE_HISTORICAL`: một
        # entry `OWNER_MANUAL_LEGACY_CONFIRMATION` (Golden #1 §2) phải giữ
        # đúng nhãn của nó xuống tới `WorkingLine.price_source` — gắn nhãn
        # HISTORICAL_CONFIRMED_REPORT cho nó là claim sai một report reopenable
        # không tồn tại.
        provenance = Provenance(
            raw_product_identity=row.raw_product_identity,
            resolution_method=entry.provenance,
            resolved_at=_midnight(row),
            mapping_source=entry.provenance,
            price_provenance=entry.provenance,
        )
        return HistoricalConfirmed(
            price=entry.confirmed_purchase_price,
            provenance=provenance,
            identity=entry.confirmed_identity,
        )
    provenance = Provenance(
        raw_product_identity=row.raw_product_identity,
        resolution_method=PROVENANCE_HISTORICAL,
        resolved_at=_midnight(row),
        mapping_source=PROVENANCE_HISTORICAL,
        price_provenance=PROVENANCE_HISTORICAL,
    )
    return PendingProduct(
        reason_code=PendingReason.PENDING_HISTORICAL_CONFIRMATION,
        attempted_sources=(AttemptedSource.HISTORICAL_CONFIRMED_REGISTRY,),
        provenance=provenance,
    )


def _midnight(row: SalesRowRef):
    from datetime import datetime, time, timezone

    return datetime.combine(row.sale_date, time.min, tzinfo=timezone.utc)


def lookup_public_purchase_code(
    view: StoreView, tracking_code: str
) -> Optional[str]:
    """`INV-43c`/`INV-44` — trả mã CỦA CHÍNH mapping `CONFIRMED`, hoặc absence.

    Không có nhánh nào trả một mã dẫn xuất: không `tracking_code`, không một
    biến thể chuẩn hoá của nó, không một mã suy ra — kể cả khi tồn tại một PP
    product có `product_code` trùng chuỗi. Thiếu mapping → `None`, và caller
    **không có mã nào để đoán**.

    Điều kiện (a) của `INV-43` ("không có valid vendor candidate tại
    `sale_date`") thuộc `TASK-105E` và cố ý không ở đây.
    """
    mapping = view.confirmed_cross_system(tracking_code)
    if mapping is None or mapping.status is not CrossSystemStatus.CONFIRMED:
        return None
    return mapping.public_purchase_code


def affected_scope_for(
    identity: DistinctIdentity, *, revision: int
) -> AffectedScope:
    """`INV-76`/`INV-87` — phạm vi TÍNH LẠI từ dữ liệu, không cộng dồn.

    Một `confirmation_action` áp cho MỌI dòng và MỌI order chia sẻ cùng distinct
    identity, nên phạm vi của nó là chính tập đó — và vì nó được tính lại từ
    `identity`, một retry cho ra đúng con số cũ thay vì con số gấp đôi
    (`INV-71`).
    """
    return AffectedScope(
        distinct_identity_count=1,
        affected_order_ids=identity.order_ids,
        affected_line_count=identity.line_count,
        computed_at_revision=revision,
    )
