"""S068 — Tracking alias/map + board là authority identity production."""

from __future__ import annotations

import pytest

from app.modules.product.identity.identity import PendingProduct, Resolved
from app.modules.product.identity.resolver import ProductIdentityResolver, distinct_identities
from app.modules.product.identity.tracking_catalog import (
    CaptureStatus,
    TrackingCaptureFailedError,
)
from app.modules.product.identity.tracking_inv_map import inv_map_key
from tests.support import identity_fixtures as fx
from tools.tracking.capture_tracking_catalog import build_capture


def _resolve(raw: str, *, rows, alias_map_rows=(), inv_map_entries=None):
    store = fx.store()
    resolver = ProductIdentityResolver(
        tracking_snapshot=fx.tracking_snapshot(rows, alias_map_rows=alias_map_rows),
        store_view=store.read_at_revision(store.current_revision()),
        tracking_identity_authority=True,
        inv_map_snapshot=(
            fx.inv_map_snapshot(inv_map_entries) if inv_map_entries is not None else None
        ),
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


# ======================================================================
# `inv.map` — authority CHO CÂU TÊN HÀNG kế toán đầy đủ (S068 follow-up)
# ======================================================================

FULL_DESCRIPTION = "Máy giặt Samsung WW10DB7U34GBSV"


def test_valid_inv_map_entry_resolves_to_the_canonical_board_code():
    result = _resolve(
        FULL_DESCRIPTION,
        rows=(("WW10DB7U34GB", "Máy giặt", (), True),),
        inv_map_entries=((inv_map_key(FULL_DESCRIPTION), "WW10DB7U34GB"),),
    )
    assert isinstance(result.outcome, Resolved)
    assert result.outcome.identity.source_product_code == "WW10DB7U34GB"
    assert result.resolution_method.value == "TRACKING_INV_MAP_CONFIRMED"
    # Authoritative — không mang mapping_id (không phải một `confirmation_
    # action` thứ hai của Reports; xem OWNER decision ở docstring resolver).
    assert result.outcome.provenance.mapping_id is None


def test_absent_inv_map_key_stays_pending_as_not_yet_classified():
    result = _resolve(
        "Sản phẩm chưa từng được Tracking hoặc Reports biết tới",
        rows=(),
        inv_map_entries=(),
    )
    assert isinstance(result.outcome, PendingProduct)
    assert result.outcome.reason_code.value == "NO_CANDIDATE_IN_ANY_CATALOG"


def test_inv_map_explicit_ignore_value_is_a_distinct_safe_pending_reason():
    raw = "Chi phí vận chuyển"
    result = _resolve(
        raw,
        rows=(),
        inv_map_entries=((inv_map_key(raw), "-"),),
    )
    assert isinstance(result.outcome, PendingProduct)
    assert result.outcome.reason_code.value == "TRACKING_INV_MAP_EXPLICIT_IGNORE"
    # KHÔNG BAO GIỜ mang identity — Ignore là một Pending hợp lệ, không phải
    # một Resolved trá hình (`INV-24`, cùng khuôn mọi PendingProduct khác).
    assert result.outcome.provenance.source_product_code is None


def test_inv_map_target_missing_from_board_is_pending_not_resolved():
    raw = "Tủ đông Denver DMF7699WS2"
    result = _resolve(
        raw,
        rows=(),  # "7699WS2" không tồn tại trong board hiện tại
        inv_map_entries=((inv_map_key(raw), "7699WS2"),),
    )
    assert isinstance(result.outcome, PendingProduct)
    assert result.outcome.reason_code.value == "MAPPING_STALE_TARGET_ABSENT"


def test_inv_map_target_present_but_not_present_in_board_is_pending():
    raw = "Tủ đông Denver DMF7699WS2"
    result = _resolve(
        raw,
        rows=(("7699WS2", "cũ", (), False),),  # từng có, nay đã rời board
        inv_map_entries=((inv_map_key(raw), "7699WS2"),),
    )
    assert isinstance(result.outcome, PendingProduct)
    assert result.outcome.reason_code.value == "MAPPING_STALE_TARGET_ABSENT"


def test_inv_map_lookup_is_exact_no_fuzzy_or_substring_fallback():
    """Một mô tả khác đúng MỘT ký tự (model khác) không được khớp — `inv.map`
    tra bằng khoá đã tính đúng `normCode()`, không phải khoảng cách chuỗi."""
    known = "Tivi Samsung 65QN70F"
    different_model = "Tivi Samsung 65QN70FA"
    result = _resolve(
        different_model,
        rows=(),
        inv_map_entries=((inv_map_key(known), "65QN70F"),),
    )
    assert isinstance(result.outcome, PendingProduct)
    assert result.outcome.reason_code.value == "NO_CANDIDATE_IN_ANY_CATALOG"


def test_inv_map_never_consults_board_name_or_alt_as_authority():
    """`inv.map` chỉ khớp câu tên hàng với KHOÁ `inv.map` đã tính; một `board
    row` có `name` trùng nguyên văn câu tên hàng không được dùng làm lối tắt."""
    result = _resolve(
        FULL_DESCRIPTION,
        rows=(("SOME-OTHER-CODE", FULL_DESCRIPTION, (), True),),
        inv_map_entries=(),  # không có mục inv.map nào cho mô tả này
    )
    assert isinstance(result.outcome, PendingProduct)
    assert result.outcome.reason_code.value == "NO_CANDIDATE_IN_ANY_CATALOG"


def test_existing_alias_and_board_exact_authority_still_wins_before_inv_map():
    """`alias.map`/`board` (khoá bằng MÃ) vẫn được thử TRƯỚC; khi nó đã khớp,
    `inv.map` không quyết định kết quả — kể cả khi nó có một mục (khác) cho
    cùng khoá tra chuẩn hoá."""
    result = _resolve(
        "FV1412S3B",
        rows=(("FV1412S3B", "Máy giặt", (), True),),
        inv_map_entries=((inv_map_key("FV1412S3B"), "SOME-DIFFERENT-CODE"),),
    )
    assert isinstance(result.outcome, Resolved)
    assert result.outcome.identity.source_product_code == "FV1412S3B"
    assert result.resolution_method.value == "TRACKING_CANONICAL_EXACT"


def test_inv_map_source_absent_behaves_exactly_like_before_this_change():
    """Không truyền `inv_map_snapshot` (mặc định `None`) — hành vi giống hệt
    trước khi vertical này tồn tại: không Pending hàng loạt vì thiếu nguồn
    phụ trợ tuỳ chọn."""
    result = _resolve(FULL_DESCRIPTION, rows=())
    assert isinstance(result.outcome, PendingProduct)
    assert result.outcome.reason_code.value == "NO_CANDIDATE_IN_ANY_CATALOG"


def test_a_failed_inv_map_snapshot_is_a_hard_error_not_a_pending():
    """`INV-12` áp dụng cho `inv.map` giống hệt `board`/`alias`: một capture
    FAILED phải nổ ngay lúc dựng resolver, không lặng lẽ thành Pending."""
    store = fx.store()
    with pytest.raises(TrackingCaptureFailedError):
        ProductIdentityResolver(
            tracking_snapshot=fx.tracking_snapshot(()),
            store_view=store.read_at_revision(store.current_revision()),
            tracking_identity_authority=True,
            inv_map_snapshot=fx.inv_map_snapshot(
                (),
                status=CaptureStatus.FAILED,
                failure_reason="mất mạng giữa chừng",
            ),
        )
