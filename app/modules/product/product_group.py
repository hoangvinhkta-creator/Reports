"""`ProductGroupProvider` — the stable seam between a line and its ProductGroup.

ADR-106 §6 / DEC-127 §5: Phase 1 classifies ProductGroup **manually, 100%**.
`DefaultProductGroupProvider` returns `None` for every line, so every line
falls back to `DIEN_MAY` with provenance `DEFAULT` — a visible fallback, not
a decision anyone made.

Why no automatic classifier here, deliberately:

- The 155 model codes appearing in the historical Gia dụng sheets are **not**
  business truth. 50 of them also appear in individual sellers' sheets, where
  the same physical model converts at a different rate. A classifier keyed on
  model code would learn the wrong thing from its first row.
- Product names do carry a category prefix ("Lò vi sóng", "Máy lọc không
  khí"), but nobody has defined which prefixes mean GIA_DUNG. Guessing that
  mapping would put an invented business rule straight into payroll.

So the interface is defined now and left unimplemented on purpose. When the
UI checkbox exists (Phase 2/3) and there are user-confirmed classifications to
learn from, a `LearnedProductGroupProvider` plugs in here without touching
`ConversionSchemeResolver` — the same move that let `PriceProvider` (TASK-105)
wait for a real Price Master.
"""

from __future__ import annotations

from datetime import date
from typing import Optional, Protocol


class ProductGroupProvider(Protocol):
    def lookup(
        self, product_raw: Optional[str], sale_date: Optional[date]
    ) -> Optional[str]:
        """Return `DIEN_MAY` / `GIA_DUNG` for this product line, or `None`
        when unknown. `None` means "no automatic verdict" — the caller
        applies the configured default and records the provenance; it must
        never invent a group."""
        ...


class DefaultProductGroupProvider:
    """Phase 1: no automatic classification exists (DEC-127 §5)."""

    def lookup(
        self, product_raw: Optional[str], sale_date: Optional[date]
    ) -> Optional[str]:
        return None
