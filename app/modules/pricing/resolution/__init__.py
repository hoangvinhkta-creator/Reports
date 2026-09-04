"""`TASK-105E` — Price Resolution Composition (`P00–P11`, `DEC-154` §7/§11).

`sources.py` = nạp và đóng băng bằng chứng của MỘT lần import.
`composition.py` = thứ tự ưu tiên nguồn giá và provenance.

Lớp này không sở hữu nguồn dữ liệu nào; nó điều phối các provider đã được
review riêng (`TASK-105B`, `TASK-105D`, Reports History Reader V1).
"""

from app.modules.pricing.resolution.composition import (
    CompositionRule,
    PRICE_SOURCE_BY_RULE,
    PostCutoverPriceComposition,
    PriceResolutionReason,
    PriceResolutionRecord,
    PriceResolutionReport,
    PriceResolutionStatus,
)
from app.modules.pricing.resolution.unresolved_descriptions import (
    UnresolvedDescriptionGroup,
    aggregate_unresolved_descriptions,
    is_unresolved_identity_record,
)
from app.modules.pricing.resolution.sources import (
    BusinessTimezone,
    PriceEvidenceSnapshot,
    PriceResolutionSources,
    load_business_timezone,
    load_price_resolution_sources,
)

__all__ = [
    "BusinessTimezone",
    "CompositionRule",
    "PRICE_SOURCE_BY_RULE",
    "PostCutoverPriceComposition",
    "PriceEvidenceSnapshot",
    "PriceResolutionReason",
    "PriceResolutionRecord",
    "PriceResolutionReport",
    "PriceResolutionSources",
    "PriceResolutionStatus",
    "UnresolvedDescriptionGroup",
    "aggregate_unresolved_descriptions",
    "is_unresolved_identity_record",
    "load_business_timezone",
    "load_price_resolution_sources",
]
