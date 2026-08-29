"""E-J `HistoricalConfirmedRegistry` — nhánh pre-cutover, data contract §9.

```text
CUTOVER_DATE = 2026-09-01
```

Phân loại bằng `sale_date`, **KHÔNG BAO GIỜ** bằng `import_date` (`INV-48`).
Một bản ghi nhập muộn vào tháng sau vẫn là một giao dịch của tháng trước; nếu
phân loại bằng ngày nhập, cùng một đơn hàng sẽ đi hai nhánh khác nhau tuỳ lúc
ai bấm nút import — và hai nhánh đó cho hai giá vốn khác nhau.

## Vì sao nhánh này bypass HOÀN TOÀN resolver

`INV-47`: với `sale_date < CUTOVER_DATE`, resolver/catalog/price-provider
KHÔNG được gọi **dù registry có entry hay không**. Chỉ có hai kết cục:
`HISTORICAL_CONFIRMED` hoặc `PENDING_HISTORICAL_CONFIRMATION`.

Cám dỗ ở đây rất cụ thể và rất sai: registry rỗng trông giống một "chỗ trống
cần điền", và catalog hiện tại thì đang nằm sẵn trong tay. Điền vào chỗ trống
đó là dùng danh mục HÔM NAY viết lại lịch sử (`INV-15`) — một sản phẩm đổi mã
từ năm ngoái sẽ nhận giá vốn của mã mới. Registry rỗng là trạng thái khởi đầu
ĐÚNG, và Pending là kết quả ĐÚNG (`§14.3`, `DEC-103`).

`INV-50`: `confirmed_identity` là OPTIONAL. Một report lịch sử đã xác nhận giá
mà không xác nhận identity vẫn là authority CHO GIÁ; identity vắng KHÔNG kích
hoạt resolver để "điền vào chỗ trống".
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Optional

from app.modules.product.identity.audit import (
    AffectedScope,
    AggregateType,
    EventType,
    MappingAuditEvent,
)
from app.modules.product.identity.commands import (
    ConfirmHistoricalEntry,
    CorrectHistoricalEntry,
    RegistryCommand,
)
from app.modules.product.identity.identity import CanonicalProductIdentity

CUTOVER_DATE = date(2026, 9, 1)
"""`DEC-154` §1. Hằng số này là ranh giới nghiệp vụ, không phải cấu hình."""

PROVENANCE_HISTORICAL = "HISTORICAL_CONFIRMED_REPORT"

PROVENANCE_OWNER_MANUAL_LEGACY_CONFIRMATION = "OWNER_MANUAL_LEGACY_CONFIRMATION"
"""Golden #1 vertical delivery (session brief §2): dùng CHỈ khi hệ thống gốc
(vd. Tracking "Tồn"/public purchase) đã ghi đè giá trị hiện tại và không giữ
lại một snapshot lịch sử có thể mở lại — một LEGACY DATA GAP, không phải bằng
chứng "chủ dự án đã xác nhận" cho một report còn tồn tại mà `INV-51` cấm.
Provenance này tự khai đúng bản chất của nó (`ManualLegacyConfirmationRef`):
KHÔNG claim verified historical replay. `INV-51` không bị nới lỏng cho
trường hợp report thật sự reopenable — nó chỉ không còn là con đường DUY
NHẤT để một entry E-J hợp lệ."""


class RegistryEntryStatus(str, Enum):
    CONFIRMED = "CONFIRMED"
    SUPERSEDED = "SUPERSEDED"


class ConfirmationAuthority(str, Enum):
    OWNER = "OWNER"
    DELEGATED_ADMIN = "DELEGATED_ADMIN"


class InvalidSourceReportRefError(ValueError):
    """`INV-51` — bằng chứng phải MỞ LẠI ĐƯỢC.

    `EVIDENCE_STANDARD` cấm bịa evidence, và "chủ dự án đã xác nhận" viết dưới
    dạng văn xuôi không phải bằng chứng: không ai kiểm lại được nó. Một entry
    registry đặt giá vốn cho một đơn hàng thật, nên nó phải trỏ tới một file có
    `content_hash` mở ra đối chiếu được.
    """


@dataclass(frozen=True)
class SourceReportRef:
    """§9.3 — bằng chứng bất biến của một entry lịch sử."""

    report_id: str
    file_name: str
    content_hash: str
    sheet_name: Optional[str] = None
    source_row: Optional[int] = None

    def __post_init__(self) -> None:
        for field_name in ("report_id", "file_name", "content_hash"):
            value = getattr(self, field_name)
            if not value or not str(value).strip():
                raise InvalidSourceReportRefError(
                    f"source_report_ref.{field_name} REQUIRED và không được rỗng "
                    "(INV-51) — một xác nhận không mở lại được thì không phải "
                    "bằng chứng"
                )

    def to_record(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "file_name": self.file_name,
            "content_hash": self.content_hash,
            "sheet_name": self.sheet_name,
            "source_row": self.source_row,
        }


class InvalidManualLegacyConfirmationError(ValueError):
    """Một xác nhận legacy không tự khai rõ hệ thống gốc/lý do thì không
    trung thực — và một provenance không trung thực không phải bằng chứng."""


@dataclass(frozen=True)
class ManualLegacyConfirmationRef:
    """Provenance cho `PROVENANCE_OWNER_MANUAL_LEGACY_CONFIRMATION`.

    KHÔNG phải một biến thể "nhẹ hơn" của `SourceReportRef` — đây là một loại
    bằng chứng khác, dùng khi hệ thống gốc thật sự không giữ lại snapshot
    reopenable (LEGACY DATA GAP). Ba trường REQUIRED tồn tại để entry tự khai
    đúng bản chất của nó thay vì im lặng trông giống một report đã verify.
    """

    original_system: str
    reason: str
    confirmed_note: Optional[str] = None

    def __post_init__(self) -> None:
        for field_name in ("original_system", "reason"):
            value = getattr(self, field_name)
            if not value or not str(value).strip():
                raise InvalidManualLegacyConfirmationError(
                    f"manual_legacy_confirmation_ref.{field_name} REQUIRED và "
                    "không được rỗng — một xác nhận không nói rõ hệ thống gốc/"
                    "lý do thiếu snapshot lịch sử thì không trung thực"
                )

    def to_record(self) -> dict[str, Any]:
        return {
            "original_system": self.original_system,
            "reason": self.reason,
            "confirmed_note": self.confirmed_note,
        }


@dataclass(frozen=True)
class HistoricalConfirmedRegistryEntry:
    """E-J. `confirmed_purchase_price` là `Decimal`, VND thô (`ADR-103`).

    Bằng chứng của một entry là ĐÚNG MỘT trong hai loại (`__post_init__`
    thi hành): `source_report_ref` (`SourceReportRef`, `INV-51` — report
    reopenable thật) hoặc `manual_legacy_confirmation_ref`
    (`ManualLegacyConfirmationRef` — Golden #1 session brief §2, LEGACY DATA
    GAP). `provenance` phải khớp loại nào đang có — không được gắn nhãn
    `HISTORICAL_CONFIRMED_REPORT` cho một entry không có report thật.
    """

    entry_id: str
    sale_date: date
    order_id: str
    raw_product_identity: str
    raw_identity_key: str
    confirmed_purchase_price: Decimal
    confirmed_by: str
    confirmed_at: datetime
    confirmation_authority: ConfirmationAuthority
    status: RegistryEntryStatus = RegistryEntryStatus.CONFIRMED
    version: int = 1
    confirmed_identity: Optional[CanonicalProductIdentity] = None
    price_unit_note: Optional[str] = None
    source_report_ref: Optional[SourceReportRef] = None
    manual_legacy_confirmation_ref: Optional[ManualLegacyConfirmationRef] = None
    source_row_hash: Optional[str] = None
    provenance: str = PROVENANCE_HISTORICAL
    supersedes: Optional[str] = None
    superseded_by: Optional[str] = None
    audit_event_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.sale_date >= CUTOVER_DATE:
            raise ValueError(
                f"entry registry phải có sale_date < CUTOVER_DATE ({CUTOVER_DATE}); "
                f"nhận {self.sale_date}"
            )
        if not isinstance(self.confirmed_purchase_price, Decimal):
            raise ValueError(
                "confirmed_purchase_price phải là Decimal (ADR-103) — float làm "
                "tròn sai trên tiền"
            )
        has_report = self.source_report_ref is not None
        has_manual = self.manual_legacy_confirmation_ref is not None
        if has_report == has_manual:
            raise ValueError(
                "entry phải có ĐÚNG MỘT trong source_report_ref/"
                "manual_legacy_confirmation_ref — không cả hai (hai loại bằng "
                "chứng khác nhau cho cùng một entry), không thiếu cả hai "
                "(INV-51/INV-54: không có bằng chứng thì không được CONFIRMED)"
            )
        if has_report and self.provenance != PROVENANCE_HISTORICAL:
            raise ValueError(
                f"provenance phải = {PROVENANCE_HISTORICAL!r} khi có "
                f"source_report_ref (nhận {self.provenance!r})"
            )
        if has_manual and self.provenance != PROVENANCE_OWNER_MANUAL_LEGACY_CONFIRMATION:
            raise ValueError(
                f"provenance phải = {PROVENANCE_OWNER_MANUAL_LEGACY_CONFIRMATION!r} "
                f"khi có manual_legacy_confirmation_ref (nhận {self.provenance!r}) "
                "— không được gắn nhãn HISTORICAL_CONFIRMED_REPORT cho một xác "
                "nhận không có report reopenable"
            )

    @property
    def lookup_key(self) -> tuple[str, str, date]:
        """`INV-52` — `(order_id, raw_identity_key, sale_date)`."""
        return (self.order_id, self.raw_identity_key, self.sale_date)

    def to_record(self) -> dict[str, Any]:
        identity = self.confirmed_identity
        return {
            "entry_id": self.entry_id,
            "sale_date": self.sale_date.isoformat(),
            "order_id": self.order_id,
            "raw_product_identity": self.raw_product_identity,
            "raw_identity_key": self.raw_identity_key,
            "confirmed_purchase_price": str(self.confirmed_purchase_price),
            "price_unit_note": self.price_unit_note,
            "source_report_ref": (
                self.source_report_ref.to_record()
                if self.source_report_ref is not None
                else None
            ),
            "manual_legacy_confirmation_ref": (
                self.manual_legacy_confirmation_ref.to_record()
                if self.manual_legacy_confirmation_ref is not None
                else None
            ),
            "source_row_hash": self.source_row_hash,
            "provenance": self.provenance,
            "confirmed_by": self.confirmed_by,
            "confirmed_at": self.confirmed_at.isoformat(),
            "confirmation_authority": self.confirmation_authority.value,
            "status": self.status.value,
            "version": self.version,
            "confirmed_identity": (
                {
                    "namespace": identity.namespace.value,
                    "source_product_code": identity.source_product_code,
                }
                if identity is not None
                else None
            ),
            "supersedes": self.supersedes,
            "superseded_by": self.superseded_by,
        }


class HistoricalConfirmedRegistry:
    """Store append-only riêng, có `registry_revision` riêng.

    Vì sao riêng và không dùng chung log với mapping store: `ResolutionBinding`
    (`INV-55`) ghim `mapping_store_revision` **và** `registry_revision` như hai
    thành phần độc lập. Gộp một bộ đếm là làm cho hai thứ đó không thể ghim
    riêng — và replay của một report pre-cutover sẽ lệch mỗi khi ai đó confirm
    một mapping post-cutover không liên quan.
    """

    def __init__(self) -> None:
        self._events: list[MappingAuditEvent] = []
        self._entries: dict[str, HistoricalConfirmedRegistryEntry] = {}
        self._results_by_request: dict[str, str] = {}

    def current_revision(self) -> int:
        return len(self._events)

    def events(self) -> tuple[MappingAuditEvent, ...]:
        return tuple(self._events)

    def append(self, command: RegistryCommand) -> HistoricalConfirmedRegistryEntry:
        """Đường ghi duy nhất vào registry. Correction = supersede (`INV-53`)."""
        if command.client_request_id in self._results_by_request:
            return self._entries[self._results_by_request[command.client_request_id]]

        current = self._entries.get(command.entry_id)
        current_version = current.version if current is not None else 0
        if command.expected_version != current_version:
            from app.modules.product.identity.store import MappingVersionConflict

            raise MappingVersionConflict(
                f"expected_version={command.expected_version} nhưng version hiện "
                f"tại={current_version} cho entry {command.entry_id}",
                current_state=current,
            )

        if isinstance(command, ConfirmHistoricalEntry):
            entry = command.entry
            event_type = EventType.CONFIRM_HISTORICAL_ENTRY
        elif isinstance(command, CorrectHistoricalEntry):
            if current is None:
                raise ValueError("CORRECT_HISTORICAL_ENTRY cần một entry đang tồn tại")
            entry = command.entry
            event_type = EventType.CORRECT_HISTORICAL_ENTRY
        else:
            raise TypeError(f"command không được hỗ trợ: {type(command).__name__}")

        revision = self.current_revision() + 1
        event = MappingAuditEvent(
            event_id=str(uuid.uuid4()),
            revision=revision,
            event_type=event_type,
            aggregate_type=AggregateType.HISTORICAL_REGISTRY_ENTRY,
            aggregate_id=command.entry_id,
            actor_id=command.actor_id,
            occurred_at=datetime.now(timezone.utc),
            old_value=current.to_record() if current is not None else None,
            new_value=entry.to_record(),
            affected_scope=AffectedScope(
                distinct_identity_count=1,
                affected_order_ids=(entry.order_id,),
                affected_line_count=command.affected_scope.affected_line_count,
                computed_at_revision=revision - 1,
            ),
            client_request_id=command.client_request_id,
            resulting_version=entry.version,
            reason=command.reason,
        )
        self._events.append(event)
        self._entries[command.entry_id] = entry
        self._results_by_request[command.client_request_id] = command.entry_id
        return entry

    def superseded_entries(self) -> tuple[dict[str, Any], ...]:
        """Bản ghi cũ đọc lại TỪ LOG — bằng chứng `INV-53` "không DELETE"."""
        return tuple(
            event.old_value for event in self._events if event.old_value is not None
        )

    def lookup(
        self, order_id: str, raw_identity_key: str, sale_date: date
    ) -> Optional[HistoricalConfirmedRegistryEntry]:
        """`INV-52` — khoá đủ ba phần.

        Cố ý KHÔNG khớp theo catalog hiện tại (`INV-49`): một entry hợp lệ dù
        mã của nó không còn tồn tại ở đâu.
        """
        for entry in self._entries.values():
            if (
                entry.status is RegistryEntryStatus.CONFIRMED
                and entry.lookup_key == (order_id, raw_identity_key, sale_date)
            ):
                return entry
        return None

    def read_at_revision(self, revision: int) -> "HistoricalConfirmedRegistry":
        """Point-in-time read cho replay (`INV-56`)."""
        if revision < 0 or revision > len(self._events):
            raise ValueError(f"registry_revision {revision} ngoài khoảng")
        view = HistoricalConfirmedRegistry()
        for event in self._events[:revision]:
            view._events.append(event)
        for event in self._events[:revision]:
            entry = entry_from_record(event.new_value)
            if entry is not None:
                view._entries[event.aggregate_id] = entry
        return view


def entry_from_record(
    record: Optional[dict[str, Any]]
) -> Optional[HistoricalConfirmedRegistryEntry]:
    """Deserialize một `HistoricalConfirmedRegistryEntry` từ record §9.2.

    Public (không còn `_`-prefixed): dùng lại bởi `registry_store.py`
    (loader JSONL, Golden #1 vertical delivery) ngoài `read_at_revision` nội
    bộ — cùng một logic deserialize, không nhân bản.
    """
    if not record or "entry_id" not in record:
        return None
    identity_record = record.get("confirmed_identity")
    from app.modules.product.identity.identity import Namespace

    report_record = record.get("source_report_ref")
    manual_record = record.get("manual_legacy_confirmation_ref")
    return HistoricalConfirmedRegistryEntry(
        entry_id=record["entry_id"],
        sale_date=date.fromisoformat(record["sale_date"]),
        order_id=record["order_id"],
        raw_product_identity=record["raw_product_identity"],
        raw_identity_key=record["raw_identity_key"],
        confirmed_purchase_price=Decimal(record["confirmed_purchase_price"]),
        source_report_ref=(
            SourceReportRef(**report_record) if report_record else None
        ),
        manual_legacy_confirmation_ref=(
            ManualLegacyConfirmationRef(**manual_record) if manual_record else None
        ),
        confirmed_by=record["confirmed_by"],
        confirmed_at=datetime.fromisoformat(record["confirmed_at"]),
        confirmation_authority=ConfirmationAuthority(record["confirmation_authority"]),
        status=RegistryEntryStatus(record["status"]),
        version=record["version"],
        confirmed_identity=(
            CanonicalProductIdentity(
                namespace=Namespace(identity_record["namespace"]),
                source_product_code=identity_record["source_product_code"],
            )
            if identity_record
            else None
        ),
        price_unit_note=record.get("price_unit_note"),
        source_row_hash=record.get("source_row_hash"),
        provenance=record.get("provenance", PROVENANCE_HISTORICAL),
        supersedes=record.get("supersedes"),
        superseded_by=record.get("superseded_by"),
    )
