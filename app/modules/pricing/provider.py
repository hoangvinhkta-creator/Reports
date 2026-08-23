"""`PriceProvider` — the stable interface between price lookup and its source.

DEC-103: an interface is defined now so an external Price Master can be
plugged in later (TASK-401, Phase 4) without touching `price_engine` or
`app.pipeline`. Today, no Price Master exists anywhere — `PendingPriceProvider`
is the correct implementation for every line, not a stand-in for a missing
data source.

`product_code` is typed for the real schema TASK-401 will use
(`docs/analysis/01_DATA_MAPPING.md` §2 — Price Master keyed by ProductCode +
SaleDate). Phase 1 has no `product_mapper` (TASK-402) yet, so callers pass
`product_raw` as an interim key — see `price_engine.apply_prices`.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional, Protocol


class PriceProvider(Protocol):
    def lookup(
        self, product_code: Optional[str], sale_date: Optional[date]
    ) -> Optional[Decimal]:
        """Return the accounting purchase price for this product on this
        date, in raw VND, or `None` if unknown. `None` means Pending — the
        caller must never substitute a guessed or zero value."""
        ...


class PendingPriceProvider:
    """No Price Master exists yet (DEC-103). Every lookup is Pending."""

    def lookup(
        self, product_code: Optional[str], sale_date: Optional[date]
    ) -> Optional[Decimal]:
        return None
