"""TASK-105D — nhánh pre-cutover và `HistoricalConfirmedRegistry`.

Gate: `CHECK-105D-01` (G01).
Adversarial: `Q` (pre-cutover), `R` (late import).
HARDENING `HB-105D-F2-03`: `INV-51`, `INV-52`, `INV-53` — ba invariant không
có gate riêng, phủ ở đây theo đúng ghi chú của Freeze Review #2.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from app.modules.product.identity.commands import (
    ConfirmHistoricalEntry,
    CorrectHistoricalEntry,
)
from app.modules.product.identity.identity import (
    HistoricalConfirmed,
    PendingProduct,
    PendingReason,
)
from app.modules.product.identity.keys import raw_identity_key
from app.modules.product.identity.registry import (
    CUTOVER_DATE,
    ConfirmationAuthority,
    HistoricalConfirmedRegistry,
    InvalidManualLegacyConfirmationError,
    InvalidSourceReportRefError,
    ManualLegacyConfirmationRef,
    PROVENANCE_HISTORICAL,
    PROVENANCE_OWNER_MANUAL_LEGACY_CONFIRMATION,
    RegistryEntryStatus,
    SourceReportRef,
)
from app.modules.product.identity.service import resolve_batch
from tests.support import identity_fixtures as fx


def _registry(*entries) -> HistoricalConfirmedRegistry:
    registry = HistoricalConfirmedRegistry()
    for index, entry in enumerate(entries):
        registry.append(
            ConfirmHistoricalEntry(
                actor_id=fx.ACTOR,
                client_request_id=f"req-hcr-{index}",
                expected_version=0,
                entry_id=entry.entry_id,
                entry=entry,
            )
        )
    return registry


class TestG01PreCutoverBypass:
    """`CHECK-105D-01` — resolver/catalog/price-provider KHÔNG được gọi."""

    def test_fixture_1_confirmed_entry_bypasses_everything(self):
        entry = fx.registry_entry()
        spy = fx.CallSpy()

        result = resolve_batch(
            [
                fx.row(
                    entry.raw_product_identity,
                    order_id=entry.order_id,
                    sale_date=fx.PRE_CUTOVER,
                )
            ],
            registry=_registry(entry),
            resolver_factory=spy,
        )

        (_, outcome), = result.historical
        assert isinstance(outcome, HistoricalConfirmed)
        assert outcome.price == Decimal("2500000")
        assert outcome.provenance.mapping_source == "HISTORICAL_CONFIRMED_REPORT"
        assert spy.calls == 0

    def test_fixture_2_empty_registry_is_pending_not_error(self):
        spy = fx.CallSpy()

        result = resolve_batch(
            [fx.row("Sản phẩm chưa từng thấy", sale_date=fx.PRE_CUTOVER)],
            registry=HistoricalConfirmedRegistry(),
            resolver_factory=spy,
        )

        (_, outcome), = result.historical
        assert isinstance(outcome, PendingProduct)
        assert outcome.reason_code is PendingReason.PENDING_HISTORICAL_CONFIRMATION
        assert spy.calls == 0

    def test_fixture_3_late_arrival_uses_sale_date_not_import_date(self):
        """`INV-48` — nhập tháng 1/2027, bán tháng 8/2026 ⇒ vẫn nhánh lịch sử.

        `SalesRowRef` cố ý không có trường `import_date`: một trường không tồn
        tại thì không ai phân loại nhầm bằng nó.
        """
        entry = fx.registry_entry()
        spy = fx.CallSpy()

        result = resolve_batch(
            [
                fx.row(
                    entry.raw_product_identity,
                    order_id=entry.order_id,
                    sale_date=fx.PRE_CUTOVER,
                )
            ],
            registry=_registry(entry),
            resolver_factory=spy,
        )

        assert isinstance(result.historical[0][1], HistoricalConfirmed)
        assert spy.calls == 0
        assert not hasattr(fx.row("x"), "import_date")

    def test_fixture_4_entry_without_identity_still_historical_confirmed(self):
        """`INV-50` — vắng `confirmed_identity` KHÔNG kích hoạt resolver."""
        entry = fx.registry_entry(identity=None)
        spy = fx.CallSpy()

        result = resolve_batch(
            [
                fx.row(
                    entry.raw_product_identity,
                    order_id=entry.order_id,
                    sale_date=fx.PRE_CUTOVER,
                )
            ],
            registry=_registry(entry),
            resolver_factory=spy,
        )

        outcome = result.historical[0][1]
        assert isinstance(outcome, HistoricalConfirmed)
        assert outcome.identity is None
        assert spy.calls == 0

    def test_fixture_5_code_absent_from_current_catalog_still_valid(self):
        """`INV-49` — registry KHÔNG bắt buộc khớp catalog hiện tại."""
        from app.modules.product.identity.identity import (
            CanonicalProductIdentity,
            Namespace,
        )

        entry = fx.registry_entry(
            identity=CanonicalProductIdentity(
                namespace=Namespace.TRACKING, source_product_code="TRK-DA-BIEN-MAT"
            )
        )
        spy = fx.CallSpy()

        result = resolve_batch(
            [
                fx.row(
                    entry.raw_product_identity,
                    order_id=entry.order_id,
                    sale_date=fx.PRE_CUTOVER,
                )
            ],
            registry=_registry(entry),
            resolver_factory=spy,
        )

        outcome = result.historical[0][1]
        assert isinstance(outcome, HistoricalConfirmed)
        assert outcome.identity.source_product_code == "TRK-DA-BIEN-MAT"
        assert spy.calls == 0

    def test_pre_cutover_rows_are_excluded_from_distinct_set(self):
        """`INV-46` — mẫu số `D` của §15 loại nhánh pre-cutover trước khi tính."""
        entry = fx.registry_entry()
        result = resolve_batch(
            [
                fx.row(
                    entry.raw_product_identity,
                    order_id=entry.order_id,
                    sale_date=fx.PRE_CUTOVER,
                )
            ],
            registry=_registry(entry),
            resolver_factory=fx.CallSpy(),
        )
        assert result.distinct_count == 0

    def test_cutover_date_is_the_frozen_business_boundary(self):
        assert CUTOVER_DATE == date(2026, 9, 1)


class TestRegistryIntegrityHardening:
    """`HB-105D-F2-03` — `INV-51`/`INV-52`/`INV-53` không có gate riêng."""

    def test_inv51_prose_only_confirmation_is_rejected(self):
        """Bằng chứng phải MỞ LẠI ĐƯỢC — không chấp nhận văn xuôi."""
        for missing in ("report_id", "file_name", "content_hash"):
            kwargs = {
                "report_id": "RPT-1",
                "file_name": "f.xlsx",
                "content_hash": "0" * 64,
            }
            kwargs[missing] = "   "
            with pytest.raises(InvalidSourceReportRefError):
                SourceReportRef(**kwargs)

    def test_inv52_lookup_key_is_order_identity_and_sale_date(self):
        entry = fx.registry_entry()
        registry = _registry(entry)
        key = raw_identity_key(entry.raw_product_identity)

        assert registry.lookup(entry.order_id, key, fx.PRE_CUTOVER) is entry
        assert registry.lookup("ORD-KHAC", key, fx.PRE_CUTOVER) is None
        assert registry.lookup(entry.order_id, "khoá khác", fx.PRE_CUTOVER) is None
        assert registry.lookup(entry.order_id, key, date(2026, 8, 19)) is None

    def test_inv53_correction_supersedes_and_keeps_the_old_record(self):
        entry = fx.registry_entry(price="2500000")
        registry = _registry(entry)
        revision_before = registry.current_revision()

        corrected = fx.registry_entry(price="2600000")
        object.__setattr__(corrected, "version", 2)
        object.__setattr__(corrected, "supersedes", entry.entry_id)
        registry.append(
            CorrectHistoricalEntry(
                actor_id=fx.ACTOR,
                client_request_id="req-correct-1",
                expected_version=1,
                entry_id=entry.entry_id,
                entry=corrected,
                reason="đối chiếu lại hoá đơn gốc",
            )
        )

        assert registry.current_revision() == revision_before + 1
        old_records = registry.superseded_entries()
        assert any(
            record["confirmed_purchase_price"] == "2500000" for record in old_records
        ), "bản ghi cũ phải còn trong log — INV-53 cấm DELETE"

    def test_inv53_correction_requires_a_reason(self):
        entry = fx.registry_entry()
        _registry(entry)
        from app.modules.product.identity.audit import MissingReasonError

        with pytest.raises(MissingReasonError):
            CorrectHistoricalEntry(
                actor_id=fx.ACTOR,
                client_request_id="req-no-reason",
                expected_version=1,
                entry_id=entry.entry_id,
                entry=entry,
            )

    def test_entry_after_cutover_is_refused(self):
        with pytest.raises(ValueError, match="CUTOVER_DATE"):
            fx.registry_entry(sale_date=date(2026, 9, 2))

    def test_price_must_be_decimal_not_float(self):
        """`ADR-103` — float làm tròn sai trên tiền, và tiền này thành lương."""
        entry = fx.registry_entry()
        assert isinstance(entry.confirmed_purchase_price, Decimal)
        with pytest.raises(ValueError, match="Decimal"):
            type(entry)(
                entry_id="X",
                sale_date=fx.PRE_CUTOVER,
                order_id="O",
                raw_product_identity="p",
                raw_identity_key="p",
                confirmed_purchase_price=2500000.0,
                source_report_ref=entry.source_report_ref,
                confirmed_by="a",
                confirmed_at=datetime.now(timezone.utc),
                confirmation_authority=entry.confirmation_authority,
            )

    def test_registry_status_enum_is_closed(self):
        assert {s.value for s in RegistryEntryStatus} == {"CONFIRMED", "SUPERSEDED"}


class TestManualLegacyConfirmationProvenance:
    """Golden #1 vertical delivery session brief §2 — LEGACY DATA GAP: hệ
    thống gốc không giữ lại snapshot lịch sử reopenable. `INV-51` không nới
    lỏng cho report thật sự reopenable; nó chỉ không còn là đường DUY NHẤT."""

    def test_manual_ref_requires_truthful_non_empty_fields(self):
        for missing in ("original_system", "reason"):
            kwargs = {"original_system": "Tracking", "reason": "không rõ lý do"}
            kwargs[missing] = "   "
            with pytest.raises(InvalidManualLegacyConfirmationError):
                ManualLegacyConfirmationRef(**kwargs)

    def test_entry_needs_exactly_one_evidence_type(self):
        """Không cả hai (hai loại bằng chứng khác nhau), không thiếu cả hai."""
        base = fx.registry_entry()
        with pytest.raises(ValueError, match="ĐÚNG MỘT"):
            type(base)(
                entry_id="X1",
                sale_date=fx.PRE_CUTOVER,
                order_id="O",
                raw_product_identity="p",
                raw_identity_key="p",
                confirmed_purchase_price=Decimal("1000000"),
                confirmed_by="a",
                confirmed_at=datetime.now(timezone.utc),
                confirmation_authority=ConfirmationAuthority.OWNER,
                # thiếu cả source_report_ref lẫn manual_legacy_confirmation_ref
            )
        with pytest.raises(ValueError, match="ĐÚNG MỘT"):
            type(base)(
                entry_id="X2",
                sale_date=fx.PRE_CUTOVER,
                order_id="O",
                raw_product_identity="p",
                raw_identity_key="p",
                confirmed_purchase_price=Decimal("1000000"),
                source_report_ref=base.source_report_ref,
                manual_legacy_confirmation_ref=ManualLegacyConfirmationRef(
                    original_system="Tracking", reason="lý do"
                ),
                confirmed_by="a",
                confirmed_at=datetime.now(timezone.utc),
                confirmation_authority=ConfirmationAuthority.OWNER,
                provenance=PROVENANCE_HISTORICAL,
                # cả hai cùng có mặt — cũng phải bị từ chối
            )

    def test_provenance_label_must_match_evidence_type(self):
        """Không được gắn nhãn HISTORICAL_CONFIRMED_REPORT cho một xác nhận
        không có report reopenable, và ngược lại."""
        entry = fx.registry_entry()
        with pytest.raises(ValueError, match="OWNER_MANUAL_LEGACY_CONFIRMATION"):
            type(entry)(
                entry_id="X3",
                sale_date=fx.PRE_CUTOVER,
                order_id="O",
                raw_product_identity="p",
                raw_identity_key="p",
                confirmed_purchase_price=Decimal("1000000"),
                source_report_ref=entry.source_report_ref,
                confirmed_by="a",
                confirmed_at=datetime.now(timezone.utc),
                confirmation_authority=ConfirmationAuthority.OWNER,
                provenance=PROVENANCE_OWNER_MANUAL_LEGACY_CONFIRMATION,
            )

    def test_resolve_batch_propagates_manual_legacy_provenance_honestly(self):
        """`price_source` hạ nguồn phải nói đúng loại bằng chứng — không được
        đọc như một report đã verify khi thực ra là xác nhận thủ công."""
        entry = fx.registry_entry_manual_legacy()
        spy = fx.CallSpy()

        result = resolve_batch(
            [
                fx.row(
                    entry.raw_product_identity,
                    order_id=entry.order_id,
                    sale_date=fx.PRE_CUTOVER,
                )
            ],
            registry=_registry(entry),
            resolver_factory=spy,
        )

        outcome = result.historical[0][1]
        assert isinstance(outcome, HistoricalConfirmed)
        assert outcome.price == Decimal("2500000")
        assert outcome.provenance.price_provenance == (
            "OWNER_MANUAL_LEGACY_CONFIRMATION"
        )
        assert outcome.provenance.mapping_source == "OWNER_MANUAL_LEGACY_CONFIRMATION"
        assert spy.calls == 0
