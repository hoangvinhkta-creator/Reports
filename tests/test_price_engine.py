from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional

from app.modules.domain.models import PRICE_SOURCE_PENDING, PRICE_SOURCE_PRICE_MASTER
from app.modules.importing.normalizer import normalize_line
from app.modules.pricing.price_engine import apply_prices
from app.modules.pricing.provider import PendingPriceProvider
from tests.factories import make_raw_row


class StubPriceProvider:
    """Test double — returns a fixed price for one product_code, else None."""

    def __init__(self, prices: dict[str, Decimal]):
        self._prices = prices

    def lookup(
        self, product_code: Optional[str], sale_date: Optional[date]
    ) -> Optional[Decimal]:
        if product_code is None:
            return None
        return self._prices.get(product_code)


def test_pending_provider_leaves_price_none_not_zero():
    line = normalize_line(make_raw_row())
    apply_prices([line], PendingPriceProvider())
    assert line.accounting_purchase_price is None
    assert line.price_source == PRICE_SOURCE_PENDING


def test_matched_provider_sets_price_and_source():
    line = normalize_line(make_raw_row(product_raw="Máy giặt Test-1"))
    provider = StubPriceProvider({"Máy giặt Test-1": Decimal("5000000")})
    apply_prices([line], provider)
    assert line.accounting_purchase_price == Decimal("5000000")
    assert line.price_source == PRICE_SOURCE_PRICE_MASTER


def test_unmatched_product_stays_pending_even_with_a_real_provider():
    line = normalize_line(make_raw_row(product_raw="Sản phẩm không có trong bảng giá"))
    provider = StubPriceProvider({"Máy giặt Test-1": Decimal("5000000")})
    apply_prices([line], provider)
    assert line.accounting_purchase_price is None
    assert line.price_source == PRICE_SOURCE_PENDING


def test_applies_to_every_line_in_batch():
    lines = [
        normalize_line(make_raw_row(order_id="BH1", source_row=6)),
        normalize_line(make_raw_row(order_id="BH2", source_row=7)),
    ]
    apply_prices(lines, PendingPriceProvider())
    assert all(line.price_source == PRICE_SOURCE_PENDING for line in lines)
