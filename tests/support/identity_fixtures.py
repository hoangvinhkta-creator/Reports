"""Fixture tổng hợp cho TASK-105D.

Toàn bộ dữ liệu ở đây là **tổng hợp**. Không mapping production nào, không dữ
liệu khách hàng/kế toán thật, không bí mật Tracking, không credential Firebase
(`§29` của brief implementation, `§14.3` của data contract). Mã sản phẩm là mã
bịa có dạng dễ nhận ra (`TRK-*`, `PPC-*`).
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Optional, Sequence

from app.modules.product.identity.public_purchase import (
    PublicPurchaseSourceLoader,
    PublicPurchaseSourceVersion,
)
from app.modules.product.identity.registry import (
    ConfirmationAuthority,
    HistoricalConfirmedRegistryEntry,
    ManualLegacyConfirmationRef,
    PROVENANCE_OWNER_MANUAL_LEGACY_CONFIRMATION,
    SourceReportRef,
)
from app.modules.product.identity.resolver import (
    ProductIdentityResolver,
    SalesRowRef,
)
from app.modules.product.identity.store import JsonlProductIdentityStore
from app.modules.product.identity.tracking_catalog import (
    CaptureStatus,
    TrackingCatalogRow,
    TrackingCatalogSnapshot,
)

PRE_CUTOVER = date(2026, 8, 20)
POST_CUTOVER = date(2026, 9, 15)
ACTOR = "nv.kho.01"

CAPTURE_A = "TRK-20260901T000000Z-aaaaaaaa"
CAPTURE_B = "TRK-20260930T000000Z-bbbbbbbb"
PP_V1 = "PP-20260901-01"
PP_V2 = "PP-20260930-01"


def tracking_snapshot(
    rows: Sequence[tuple] = (),
    *,
    capture_id: str = CAPTURE_A,
    alias_map_rows: Sequence[tuple[str, str]] = (),
    status: CaptureStatus = CaptureStatus.COMPLETE,
    failure_reason: Optional[str] = None,
) -> TrackingCatalogSnapshot:
    """`rows` là các tuple `(tracking_code, name, alt, present_in_board)`."""
    return TrackingCatalogSnapshot(
        capture_id=capture_id,
        captured_at=datetime(2026, 9, 1, tzinfo=timezone.utc),
        captured_by=ACTOR,
        source_system_ref="tracking-fake/board",
        content_hash="hash-" + capture_id,
        capture_status=status,
        rows=tuple(
            TrackingCatalogRow(
                tracking_code=code,
                name=name,
                alt=tuple(alt),
                present_in_board=present,
            )
            for code, name, alt, present in rows
        ),
        alias_map_rows=tuple(alias_map_rows),
        failure_reason=failure_reason,
    )


def pp_version(
    products: Sequence[dict[str, Any]] = (),
    *,
    prices: Optional[Sequence[dict[str, Any]]] = None,
    version_id: str = PP_V1,
    rollback_of: Optional[str] = None,
) -> PublicPurchaseSourceVersion:
    """Nạp qua loader thật, không dựng tắt.

    Cố ý đi qua `PublicPurchaseSourceLoader.load()` để mọi fixture của bộ test
    đều là một version đã qua `INV-04`…`INV-09` — nếu một fixture vi phạm
    invariant, nó nổ ngay ở đây thay vì làm sai lệch một assertion khác.
    `rollback_of` (nếu truyền) đi qua đúng khoá top-level mà loader thật đọc
    (`data.get("rollback_of")`, `public_purchase.py:219`) — không có
    `object.__setattr__` nào bên ngoài đường nạp sản xuất (`INV-81`).
    """
    products = list(products) or [
        {"product_code": "PPC-1000", "product_name": "Sản phẩm tổng hợp 1000"}
    ]
    if prices is None:
        prices = [
            {
                "product_key": products[0]["product_code"],
                "effective_from": date(2026, 9, 1),
                "effective_to": date(2026, 12, 31),
                "purchase_price": "1000000",
            }
        ]
    payload: dict[str, Any] = {
        "source_id": "PUBLIC_PURCHASE",
        "version_id": version_id,
        "status": "PUBLISHED",
        "products": products,
        "prices": list(prices),
    }
    if rollback_of is not None:
        payload["rollback_of"] = rollback_of
    return PublicPurchaseSourceLoader.load(payload)


def store(tmp_path=None) -> JsonlProductIdentityStore:
    if tmp_path is None:
        return JsonlProductIdentityStore()
    return JsonlProductIdentityStore(
        log_path=tmp_path / "identity.log.jsonl",
        index_path=tmp_path / "identity.index.json",
    )


def resolver(
    a_store: JsonlProductIdentityStore,
    snapshot: Optional[TrackingCatalogSnapshot] = None,
    version: Optional[PublicPurchaseSourceVersion] = None,
) -> ProductIdentityResolver:
    return ProductIdentityResolver(
        tracking_snapshot=snapshot or tracking_snapshot(),
        pp_version=version or pp_version(),
        store_view=a_store.read_at_revision(a_store.current_revision()),
        now=datetime(2026, 9, 15, tzinfo=timezone.utc),
    )


def row(
    product_raw: str,
    *,
    order_id: str = "ORD-1",
    sale_date: date = POST_CUTOVER,
) -> SalesRowRef:
    return SalesRowRef(
        order_id=order_id, sale_date=sale_date, raw_product_identity=product_raw
    )


def registry_entry(
    *,
    entry_id: str = "HCR-1",
    order_id: str = "ORD-H1",
    product_raw: str = "Máy lọc nước tổng hợp X1",
    price: str = "2500000",
    sale_date: date = PRE_CUTOVER,
    identity=None,
) -> HistoricalConfirmedRegistryEntry:
    from app.modules.product.identity.keys import raw_identity_key

    return HistoricalConfirmedRegistryEntry(
        entry_id=entry_id,
        sale_date=sale_date,
        order_id=order_id,
        raw_product_identity=product_raw,
        raw_identity_key=raw_identity_key(product_raw),
        confirmed_purchase_price=Decimal(price),
        source_report_ref=SourceReportRef(
            report_id="RPT-2026-08",
            file_name="bao-cao-thang-08-tong-hop.xlsx",
            content_hash="0" * 64,
        ),
        confirmed_by="chu.du.an",
        confirmed_at=datetime(2026, 8, 31, tzinfo=timezone.utc),
        confirmation_authority=ConfirmationAuthority.OWNER,
        confirmed_identity=identity,
    )


def registry_entry_manual_legacy(
    *,
    entry_id: str = "HCR-LEGACY-1",
    order_id: str = "ORD-H1",
    product_raw: str = "Máy lọc nước tổng hợp X1",
    price: str = "2500000",
    sale_date: date = PRE_CUTOVER,
    identity=None,
) -> HistoricalConfirmedRegistryEntry:
    """Biến thể `registry_entry()` dùng `ManualLegacyConfirmationRef` thay vì
    `SourceReportRef` — Golden #1 vertical delivery session brief §2 (LEGACY
    DATA GAP): hệ thống gốc không giữ lại snapshot lịch sử reopenable."""
    from app.modules.product.identity.keys import raw_identity_key

    return HistoricalConfirmedRegistryEntry(
        entry_id=entry_id,
        sale_date=sale_date,
        order_id=order_id,
        raw_product_identity=product_raw,
        raw_identity_key=raw_identity_key(product_raw),
        confirmed_purchase_price=Decimal(price),
        manual_legacy_confirmation_ref=ManualLegacyConfirmationRef(
            original_system="Tracking",
            reason="hệ thống gốc không giữ lại snapshot lịch sử reopenable",
        ),
        provenance=PROVENANCE_OWNER_MANUAL_LEGACY_CONFIRMATION,
        confirmed_by="chu.du.an",
        confirmed_at=datetime(2026, 8, 31, tzinfo=timezone.utc),
        confirmation_authority=ConfirmationAuthority.OWNER,
        confirmed_identity=identity,
    )


class CallSpy:
    """Đếm số lời gọi — nền của assertion `spy_call_count == 0` ở `G01`/`G17`."""

    def __init__(self, wrapped=None) -> None:
        self.calls = 0
        self._wrapped = wrapped

    def __call__(self, *args, **kwargs):
        self.calls += 1
        if self._wrapped is None:
            raise AssertionError(
                "spy này KHÔNG được gọi trên nhánh đang test (INV-47/INV-11)"
            )
        return self._wrapped(*args, **kwargs)
