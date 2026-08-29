"""Reports History Reader V1 — dựng lại giá nhập công khai của Tracking.

Xem `snapshot.py` (hợp đồng dữ liệu) và `reader.py` (thuật toán + ngữ nghĩa
biên chính xác). `provider.py` là adapter `PriceProvider` để nối vào pipeline
một cách TƯỜNG MINH — nó không bao giờ là mặc định.
"""

from app.modules.pricing.tracking_history.provider import (
    TrackingHistoryPriceProvider,
)
from app.modules.pricing.tracking_history.reader import (
    DecisiveSource,
    PriceReconstruction,
    ReconstructionStatus,
    SaleInterval,
    TrackingPriceHistoryReader,
    TrackingPriceProvenance,
    UNIT_CONVERSION_LABEL,
    UnresolvedReason,
)
from app.modules.pricing.tracking_history.snapshot import (
    InvalidTrackingPriceSnapshotError,
    TimestampAuthority,
    TrackingPriceBaseline,
    TrackingPriceHistoryEvent,
    TrackingPriceHistorySnapshot,
)

__all__ = [
    "DecisiveSource",
    "InvalidTrackingPriceSnapshotError",
    "PriceReconstruction",
    "ReconstructionStatus",
    "SaleInterval",
    "TimestampAuthority",
    "TrackingHistoryPriceProvider",
    "TrackingPriceBaseline",
    "TrackingPriceHistoryEvent",
    "TrackingPriceHistorySnapshot",
    "TrackingPriceProvenance",
    "UNIT_CONVERSION_LABEL",
    "UnresolvedReason",
]
