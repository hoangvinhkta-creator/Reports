from __future__ import annotations

from datetime import date

from app.modules.pricing.provider import PendingPriceProvider


def test_pending_provider_always_returns_none():
    provider = PendingPriceProvider()
    assert provider.lookup("SP001", date(2026, 1, 15)) is None


def test_pending_provider_handles_missing_key_and_date():
    provider = PendingPriceProvider()
    assert provider.lookup(None, None) is None
