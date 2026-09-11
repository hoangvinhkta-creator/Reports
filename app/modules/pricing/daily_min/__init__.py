"""Giá MIN theo NGÀY BÁN của Tracking — hợp đồng `daily-min-v1` (R1).

Nguồn giá nhập TỰ ĐỘNG duy nhất của R1. Tracking tính và lưu MIN theo ngày;
Reports đọc bản ghi của đúng ngày bán và không tính lại một MIN thứ hai.

- `snapshot.py`  hợp đồng + bất biến của dữ liệu (đơn vị, enum đóng, `null` ≠ 0)
- `capture_file.py` biên đọc file bất biến do `tools/tracking/capture_daily_min.py` ghi
- `provider.py`  tra bằng `sale_date`, không fallback sai ngày, giữ provenance

Nhánh cũ `pricing/tracking_history/` (lịch sử `board/<mã>/tp/ton`) KHÔNG bị
xoá và giữ nguyên nghĩa cũ, nhưng từ R1 nó không còn là nguồn MIN mặc định —
xem `pricing/resolution/composition.py`.
"""

from app.modules.pricing.daily_min.capture_file import (
    InvalidDailyMinCaptureFileError,
    load_daily_min_capture,
)
from app.modules.pricing.daily_min.planning import (
    DailyMinRequestPlan,
    MAX_CONTRACT_DAYS,
    plan_daily_min_request,
    plan_daily_min_request_for_workbook,
)
from app.modules.pricing.daily_min.provider import (
    DailyMinProvenance,
    DailyMinResolution,
    DailyMinStatus,
    DailyMinUnresolvedReason,
    THOUSAND_VND_TO_VND,
    TrackingDailyMinProvider,
    UNIT_CONVERSION_LABEL,
)
from app.modules.pricing.daily_min.snapshot import (
    CaptureStatus,
    DailyMinCaptureFailedError,
    DailyMinRecord,
    DailyMinSnapshot,
    DayStatus,
    ExcludedSource,
    InvalidDailyMinSnapshotError,
    MinSource,
    MissingReason,
    PriceStatus,
    SUPPORTED_BUSINESS_TIMEZONE,
    SUPPORTED_CURRENCY_UNIT,
    SUPPORTED_SCHEMA_VERSION,
    SourceType,
    UnsupportedDailyMinSchemaError,
)

__all__ = [
    "CaptureStatus",
    "DailyMinCaptureFailedError",
    "DailyMinRequestPlan",
    "DailyMinProvenance",
    "DailyMinRecord",
    "DailyMinResolution",
    "DailyMinSnapshot",
    "DailyMinStatus",
    "DailyMinUnresolvedReason",
    "DayStatus",
    "ExcludedSource",
    "InvalidDailyMinCaptureFileError",
    "InvalidDailyMinSnapshotError",
    "MinSource",
    "MissingReason",
    "PriceStatus",
    "MAX_CONTRACT_DAYS",
    "SUPPORTED_BUSINESS_TIMEZONE",
    "SUPPORTED_CURRENCY_UNIT",
    "SUPPORTED_SCHEMA_VERSION",
    "SourceType",
    "THOUSAND_VND_TO_VND",
    "TrackingDailyMinProvider",
    "UNIT_CONVERSION_LABEL",
    "UnsupportedDailyMinSchemaError",
    "load_daily_min_capture",
    "plan_daily_min_request",
    "plan_daily_min_request_for_workbook",
]
