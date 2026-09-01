"""S068 — Tracking alias/map + board là authority identity production."""

from __future__ import annotations

from app.modules.product.identity.identity import PendingProduct, Resolved
from app.modules.product.identity.resolver import ProductIdentityResolver, distinct_identities
from tests.support import identity_fixtures as fx
from tools.tracking.capture_tracking_catalog import build_capture


def _resolve(raw: str, *, rows, alias_map_rows=()):
    store = fx.store()
    resolver = ProductIdentityResolver(
        tracking_snapshot=fx.tracking_snapshot(rows, alias_map_rows=alias_map_rows),
        store_view=store.read_at_revision(store.current_revision()),
        tracking_identity_authority=True,
    )
    identity = distinct_identities((fx.row(raw),))[0]
    return resolver.resolve(identity)


def test_confirmed_tracking_alias_resolves_to_canonical_board_code():
    result = _resolve(
        "FX1412S3B",
        rows=(("FV1412S3B", "Máy giặt", (), True),),
        alias_map_rows=(("FX1412S3B", "FV1412S3B"),),
    )
    assert isinstance(result.outcome, Resolved)
    assert result.outcome.identity.source_product_code == "FV1412S3B"
    assert result.resolution_method.value == "TRACKING_CONFIRMED_ALIAS"


def test_canonical_tracking_code_resolves_directly():
    result = _resolve("FV1412S3B", rows=(("FV1412S3B", "Máy giặt", (), True),))
    assert isinstance(result.outcome, Resolved)
    assert result.outcome.identity.source_product_code == "FV1412S3B"
    assert result.resolution_method.value == "TRACKING_CANONICAL_EXACT"


def test_unknown_identity_stays_pending_without_similarity_fallback():
    result = _resolve("UNKNOWN-1", rows=(("KNOWN-1", "UNKNOWN-1", (), True),))
    assert isinstance(result.outcome, PendingProduct)


def test_similar_but_different_codes_never_collapse():
    rows = (("65C6K", "Tivi", (), True), ("65C6KS", "Tivi", (), True))
    first = _resolve("65C6K", rows=rows)
    second = _resolve("65C6KS", rows=rows)
    assert first.outcome.identity.source_product_code == "65C6K"
    assert second.outcome.identity.source_product_code == "65C6KS"


def test_alias_target_absent_from_board_stays_pending():
    result = _resolve(
        "FX1412S3B", rows=(), alias_map_rows=(("FX1412S3B", "FV1412S3B"),)
    )
    assert isinstance(result.outcome, PendingProduct)
    assert result.outcome.reason_code.value == "MAPPING_STALE_TARGET_ABSENT"


def test_malformed_alias_payload_fails_closed_at_capture_boundary():
    def fetch(node):
        if node == "board":
            return {"FV1412S3B": {"name": "Máy giặt"}}
        if node == "alias":
            return {"map": ["FX1412S3B"]}
        raise AssertionError(node)

    capture = build_capture(
        fetch,
        capture_id="TRK-test",
        captured_by="test",
        source_system_ref="tracking/test",
    )
    assert capture["capture_status"] == "FAILED"
    assert capture["failure_reason"].startswith("MALFORMED_SOURCE:")
