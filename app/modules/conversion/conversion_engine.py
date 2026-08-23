"""Apply ProductGroup and ConversionScheme to every product line (ADR-106).

Runs at LINE level, not order level: 118 real OrderIDs carry both Điện máy and
Gia dụng lines at once, so a single scheme per order would misprice them.
`LeadSource` still comes from the order — it is decided once per order and
propagated (DEC-119) — but the scheme lookup then happens per line, because
`ProductGroup` varies within the order.
"""

from __future__ import annotations

from typing import Optional

from app.modules.domain.models import (
    PRODUCT_GROUP_SOURCE_AUTO,
    PRODUCT_GROUP_SOURCE_DEFAULT,
    PRODUCT_GROUP_SOURCE_MANUAL,
    Order,
)
from app.modules.conversion.scheme_resolver import ConversionSchemeResolver
from app.modules.product.product_group import ProductGroupProvider


def resolve_product_group(
    line, provider: ProductGroupProvider, default_product_group: str
) -> tuple[Optional[str], str]:
    """Return `(product_group_final, source_of_value)` for one line.

    Precedence: a person's confirmed choice, then an automatic verdict, then
    the configured default. `DEFAULT` must stay distinguishable from `MANUAL`
    (ADR-106 §5) — in Phase 1 every line lands on the default, and that has to
    look like a fallback rather than like a decision somebody made.
    """
    if line.product_group_manual:
        return line.product_group_manual, PRODUCT_GROUP_SOURCE_MANUAL

    auto = provider.lookup(line.product_raw, line.date)
    line.product_group_auto = auto
    if auto:
        return auto, PRODUCT_GROUP_SOURCE_AUTO

    return default_product_group, PRODUCT_GROUP_SOURCE_DEFAULT


def apply_conversion_schemes(
    orders: list[Order],
    resolver: ConversionSchemeResolver,
    product_group_provider: ProductGroupProvider,
) -> list[Order]:
    for order in orders:
        for line in order.lines:
            group, group_source = resolve_product_group(
                line, product_group_provider, resolver.default_product_group
            )
            line.product_group_final = group
            line.product_group_source_of_value = group_source

            auto = resolver.resolve_auto(
                employee=line.employee_normalized,
                employee_group=line.employee_group,
                lead_source=line.lead_source_final,
                product_group=group,
                as_of=line.date,
            )
            line.conversion_scheme_auto = auto.scheme

            final = resolver.resolve_final(auto, line.conversion_scheme_manual)
            line.conversion_scheme_final = final.scheme
            line.conversion_rate_final = final.rate
            line.conversion_scheme_source_of_value = final.source_of_value
    return orders
