"""Apply a `PriceProvider` to every `WorkingLine` — bước 8, spec §22.

Sets `accounting_purchase_price` and `price_source`. Never coerces a missing
price to `0` (DEC-103) — a provider miss stays `None`/Pending.

A provider MAY declare its own provenance label via a `price_source` class
attribute. A provider that declares nothing keeps the historical
`PriceMaster` label, so `PendingPriceProvider`/`FilePriceProvider` — and
every Golden run built on them — behave exactly as before. The reason the
hook exists at all: `TrackingHistoryPriceProvider` reconstructs a price from
a point-in-time replay, which carries one failure mode no price table has
(timestamp authority), and labelling it "PriceMaster" would be a false
statement about where the number came from.
"""

from __future__ import annotations

from app.modules.domain.models import (
    PRICE_SOURCE_PENDING,
    PRICE_SOURCE_PRICE_MASTER,
    WorkingLine,
)
from app.modules.pricing.provider import PriceProvider


def apply_prices(
    lines: list[WorkingLine], provider: PriceProvider
) -> list[WorkingLine]:
    resolved_source = getattr(provider, "price_source", PRICE_SOURCE_PRICE_MASTER)
    for line in lines:
        # product_raw is a placeholder key until TASK-402 (product_mapper)
        # produces a real ProductCode — see provider.py.
        price = provider.lookup(line.product_raw, line.date)
        line.accounting_purchase_price = price
        line.price_source = (
            PRICE_SOURCE_PENDING if price is None else resolved_source
        )
    return lines
