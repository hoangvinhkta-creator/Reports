"""`TrackingHistoryPriceProvider` — nối reader vào biên `PriceProvider`.

## Provider này KHÔNG BAO GIỜ là mặc định

Cùng tiền lệ `FilePriceProvider` (`TASK-105B`, `CHECK-105-04`): `app.pipeline`
vẫn mặc định `PendingPriceProvider`, và caller phải dựng provider này rồi
truyền vào một cách TƯỜNG MINH. Một provider giá tự bật lên là một thay đổi
giá vốn không ai quyết định.

## Provider này KHÔNG resolve identity — nó ĐƯỢC TRAO identity

`apply_prices()` gọi `provider.lookup(line.product_raw, line.date)`, tức là
thứ đi vào đây là **tên hàng kế toán thô**, không phải một Tracking code.
Biến tên hàng thành mã là việc của `TASK-105D` và nó có cả một data contract
để không làm sai; suy ra mã bằng chuỗi ở đây là đúng thứ `D-04`/`DEC-147` §4
đã cấm sau khi Tracking trả giá cho nó trên tài sản thật.

Nên provider nhận một `identity_index` do caller cung cấp — ánh xạ
`raw_identity_key → CanonicalProductIdentity` đã resolve. Không có entry →
`IDENTITY_UNRESOLVED` → Pending. Có entry nhưng namespace là
`PUBLIC_PURCHASE` → `IDENTITY_NOT_TRACKING` → Pending, và reader **không**
chạy: `PUBLIC_PURCHASE:<mã>` không tự chuyển sang Tracking, và một mã trùng
chuỗi ở hai namespace là hai identity khác nhau (`INV-18`).

## Vì sao có `audit_trail`

`WorkingLine` không có chỗ cho provenance, và mở rộng nó là ngoài phạm vi
phiên này. Nhưng "không trả một number trần không provenance" là yêu cầu
cứng — nên provider giữ lại `PriceReconstruction` đầy đủ của MỌI lần tra,
kể cả Pending, để người kiểm mở lại được từng dòng. `lookup()` trả một
`Decimal`; `audit_trail` giữ phần còn lại.
"""

from __future__ import annotations

import datetime as _dt
from decimal import Decimal
from typing import Mapping, Optional

from app.modules.domain.models import PRICE_SOURCE_TRACKING_PRICE_HISTORY
from app.modules.pricing.tracking_history.reader import (
    DecisiveSource,
    PriceReconstruction,
    ReconstructionStatus,
    SaleInterval,
    TrackingPriceHistoryReader,
    TrackingPriceProvenance,
    UnresolvedReason,
)
from app.modules.product.identity.identity import (
    CanonicalProductIdentity,
    Namespace,
)
from app.modules.product.identity.keys import (
    EmptyRawIdentityError,
    raw_identity_key,
)

__all__ = ["TrackingHistoryPriceProvider"]


class TrackingHistoryPriceProvider:
    """Thoả `PriceProvider`. Miss là Pending (`None`), không bao giờ là 0."""

    price_source = PRICE_SOURCE_TRACKING_PRICE_HISTORY
    """Nhãn provenance mà `apply_prices` sẽ gắn cho giá do provider này giải.

    Không để rơi vào `PriceMaster` mặc định: một giá dựng lại từ lịch sử
    Tracking mà mang nhãn "PriceMaster" là một lời khai SAI về nguồn, và
    nhãn nguồn chính là thứ người kiểm dùng để quyết có tin con số hay không.
    """

    def __init__(
        self,
        reader: TrackingPriceHistoryReader,
        *,
        identity_index: Mapping[str, CanonicalProductIdentity],
        business_tz: _dt.tzinfo,
    ) -> None:
        self._reader = reader
        self._identity_index = dict(identity_index)
        self._business_tz = business_tz
        self._audit: list[PriceReconstruction] = []

    @property
    def audit_trail(self) -> tuple[PriceReconstruction, ...]:
        """Mọi lần tra, theo đúng thứ tự đã tra — Resolved LẪN Pending."""
        return tuple(self._audit)

    # ------------------------------------------------------------------

    def resolve(
        self, product_raw: Optional[str], sale_date: Optional[_dt.date]
    ) -> PriceReconstruction:
        """Kết quả ĐẦY ĐỦ kèm provenance. `lookup()` là lớp mỏng trên hàm này."""
        result = self._resolve(product_raw, sale_date)
        self._audit.append(result)
        return result

    def lookup(
        self, product_raw: Optional[str], sale_date: Optional[_dt.date]
    ) -> Optional[Decimal]:
        result = self.resolve(product_raw, sale_date)
        return result.price_vnd if result.is_resolved else None

    # ------------------------------------------------------------------

    def _resolve(
        self, product_raw: Optional[str], sale_date: Optional[_dt.date]
    ) -> PriceReconstruction:
        if sale_date is None:
            return self._identity_stage_pending(
                product_raw,
                UnresolvedReason.SALE_DATE_MISSING,
                "Dòng không có ngày bán; không dựng được khoảng thời gian nào "
                "để hỏi trạng thái giá.",
            )

        interval = SaleInterval.for_sale_date(sale_date, self._business_tz)

        try:
            key = raw_identity_key(product_raw)
        except (EmptyRawIdentityError, TypeError, AttributeError):
            return self._identity_stage_pending(
                product_raw,
                UnresolvedReason.IDENTITY_UNRESOLVED,
                "product_raw rỗng sau chuẩn hoá — không sinh được khoá định "
                "danh, nên không có identity nào để tra.",
                interval=interval,
            )

        identity = self._identity_index.get(key)
        if identity is None:
            return self._identity_stage_pending(
                product_raw,
                UnresolvedReason.IDENTITY_UNRESOLVED,
                "Không có identity đã resolve cho khoá này. Reader KHÔNG suy ra "
                "mã Tracking từ tên hàng (D-04/DEC-147 §4).",
                interval=interval,
            )
        if identity.namespace is not Namespace.TRACKING:
            return self._identity_stage_pending(
                product_raw,
                UnresolvedReason.IDENTITY_NOT_TRACKING,
                f"Identity là {identity} (namespace "
                f"{identity.namespace.value}); Tracking History Reader chỉ áp "
                "cho namespace TRACKING và không tự chuyển namespace.",
                interval=interval,
            )

        return self._reader.price_at(identity.source_product_code, interval)

    def _identity_stage_pending(
        self,
        product_raw: Optional[str],
        reason: UnresolvedReason,
        detail: str,
        *,
        interval: Optional[SaleInterval] = None,
    ) -> PriceReconstruction:
        """Pending phát sinh TRƯỚC khi reader chạy — chưa có Tracking code nào.

        `product_code`/`namespace` để `None` chứ không điền chuỗi raw: xem
        docstring của `TrackingPriceProvenance.product_code`.
        """
        snap = self._reader.snapshot
        baseline = snap.baseline
        epoch = _dt.datetime.fromtimestamp(0, tz=_dt.timezone.utc)
        return PriceReconstruction(
            status=ReconstructionStatus.PENDING,
            reason=reason,
            provenance=TrackingPriceProvenance(
                product_code=None,
                namespace=None,
                sale_interval_start=interval.lo if interval else epoch,
                sale_interval_end=interval.hi if interval else epoch,
                snapshot_capture_id=snap.capture_id,
                baseline_cutover_id=baseline.cutover_id if baseline else None,
                baseline_captured_at=baseline.captured_at if baseline else None,
                baseline_timestamp_authority=(
                    baseline.timestamp_authority if baseline else None
                ),
                decisive_source=DecisiveSource.NONE,
                raw_product_identity=(
                    None if product_raw is None else str(product_raw)
                ),
                unresolved_reason=reason,
                unresolved_detail=detail,
            ),
        )
