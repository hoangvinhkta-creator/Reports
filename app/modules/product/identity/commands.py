"""Command shape — data contract §10.3, §11.3, §12, §13.

Mọi thay đổi trạng thái của package này đi qua đúng một trong các command
dưới đây. Không có đường ghi nào khác (`INV-66`): không UI, không script,
không notebook ghi thẳng vào file store.

Ba điều kiện tiên quyết chung, kiểm ngay lúc dựng command chứ không đợi tới
lúc ghi:

- `actor_id` REQUIRED, non-empty, non-whitespace (`INV-72`);
- `client_request_id` REQUIRED — nền của idempotency lớp 1 (`INV-68`);
- `expected_version` REQUIRED — nền của optimistic concurrency (`INV-58`);
  `0` nghĩa là "tôi tin chưa có bản ghi nào".

Kiểm sớm là có chủ đích: một command dựng được nhưng ghi không được sẽ để lại
cho caller một object trông hợp lệ, và cái bẫy đó chỉ sập ở tầng ghi.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional

from app.modules.product.identity.audit import (
    AffectedScope,
    EventType,
    MissingReasonError,
    REASON_REQUIRED_TYPES,
    require_actor,
)
from app.modules.product.identity.evidence import Evidence, ResolutionMethod
from app.modules.product.identity.identity import CanonicalProductIdentity, Namespace
from app.modules.product.identity.mapping import (
    MappingSource,
    SOURCE_SYSTEM_REPORTS_SALES,
)

_EMPTY_SCOPE = AffectedScope(
    distinct_identity_count=1,
    affected_order_ids=(),
    affected_line_count=0,
    computed_at_revision=0,
)


class MissingClientRequestIdError(ValueError):
    """`INV-68` — không có `client_request_id` thì không phân biệt được retry
    với một quyết định mới, và một retry sau lỗi mạng sẽ áp mapping hai lần."""


@dataclass(frozen=True)
class Command:
    """Phần chung của mọi command đổi state."""

    actor_id: str
    client_request_id: str
    expected_version: int
    pp_version_id: Optional[str] = None
    tracking_capture_id: Optional[str] = None
    reason: Optional[str] = None
    affected_scope: AffectedScope = _EMPTY_SCOPE

    #: Loại event mà command này sinh ra. Lớp con ghi đè.
    event_type: EventType = EventType.SET_PENDING

    def __post_init__(self) -> None:
        require_actor(self.actor_id)
        if not self.client_request_id or not str(self.client_request_id).strip():
            raise MissingClientRequestIdError(
                "client_request_id REQUIRED trên mọi command đổi state (§11.2)"
            )
        if self.expected_version is None or self.expected_version < 0:
            raise ValueError("expected_version REQUIRED, >= 0 (INV-58)")
        if self.event_type in REASON_REQUIRED_TYPES and not (
            self.reason and self.reason.strip()
        ):
            raise MissingReasonError(
                f"reason REQUIRED cho {self.event_type.value} (§13.2 / D-13)"
            )


@dataclass(frozen=True)
class MappingCommand(Command):
    """Command trên aggregate E-F — biên là `(source_system, raw_identity_key)`
    (`INV-61`)."""

    source_system: str = SOURCE_SYSTEM_REPORTS_SALES
    raw_identity_key: str = ""
    raw_product_identity: str = ""

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.raw_identity_key:
            raise ValueError("raw_identity_key REQUIRED")

    @property
    def aggregate_id(self) -> str:
        return f"{self.source_system}\x1f{self.raw_identity_key}"


@dataclass(frozen=True)
class ConfirmMapping(MappingCommand):
    """`confirmation_action`. Người xác nhận một identity cho một alias."""

    target: Optional[CanonicalProductIdentity] = None
    evidence: Optional[Evidence] = None
    resolution_method: ResolutionMethod = ResolutionMethod.SIMILARITY_RANKED
    mapping_source: MappingSource = MappingSource.HUMAN_CONFIRMATION
    event_type: EventType = EventType.CONFIRM_MAPPING

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.target is None:
            raise ValueError("ConfirmMapping bắt buộc có target (E-E)")
        if self.evidence is None:
            raise ValueError("ConfirmMapping bắt buộc có evidence (§6.7)")


@dataclass(frozen=True)
class CorrectMapping(ConfirmMapping):
    """Sửa một mapping đã CONFIRMED. `reason` REQUIRED (`D-13`).

    KHÔNG phải `confirmation_action`: correction là mức authority riêng
    (`AUTHORIZED_CORRECTION`, §12), không phải một quyết định thường ngày trong
    batch, nên nó không được tính vào ngân sách thao tác của `G23`/`G24`.
    """

    event_type: EventType = EventType.CORRECT_MAPPING


@dataclass(frozen=True)
class RejectCandidate(MappingCommand):
    """`confirmation_action`. "Không phải cái này" — nhớ theo fingerprint §7.3."""

    candidate_namespace: Optional[Namespace] = None
    candidate_code: str = ""
    evidence_fingerprint: str = ""
    event_type: EventType = EventType.REJECT_CANDIDATE

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.candidate_namespace is None or not self.candidate_code:
            raise ValueError("RejectCandidate bắt buộc có candidate đủ tuple")
        if not self.evidence_fingerprint:
            raise ValueError("evidence_fingerprint REQUIRED (INV-34)")


@dataclass(frozen=True)
class SetPending(MappingCommand):
    """`confirmation_action`. Pending là lựa chọn HỢP LỆ, không phải lỗi UI."""

    pending_status_stale: bool = False
    """`True` khi target đã biến mất khỏi board hiện tại — mapping ghi
    `status = STALE` thay vì `PENDING` (`INV-14c`)."""

    evidence: Optional[Evidence] = None
    event_type: EventType = EventType.SET_PENDING


@dataclass(frozen=True)
class BootstrapMapping(MappingCommand):
    """Nạp bảng mapping do Owner cung cấp lúc migration (§14 `M1`).

    KHÔNG phải `confirmation_action`. Vì thế nó KHÔNG được tạo một mapping
    `CONFIRMED` từ một `resolution_method` ngoài tập auto-resolve — store thi
    hành điều đó cho MỌI đường ghi, không riêng đường này (`INV-01`, `G07`).
    """

    target: Optional[CanonicalProductIdentity] = None
    evidence: Optional[Evidence] = None
    resolution_method: ResolutionMethod = ResolutionMethod.CATALOG_EXACT_UNIQUE
    mapping_source: MappingSource = MappingSource.OWNER_BOOTSTRAP
    event_type: EventType = EventType.BOOTSTRAP_MAPPING

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.target is None or self.evidence is None:
            raise ValueError("BootstrapMapping bắt buộc có target và evidence")


@dataclass(frozen=True)
class MarkStale(MappingCommand):
    """Đánh dấu một mapping đã confirm là STALE (`INV-16`).

    KHÔNG phải `confirmation_action` và cố ý KHÔNG tự động: resolver không bao
    giờ phát command này. Một người phải quyết định, vì `alias.map` của
    Tracking là phê duyệt của Tracking, không phải phê duyệt của Reports
    (`D-05`).
    """

    proposed_primary_code: str = ""
    event_type: EventType = EventType.MARK_STALE


@dataclass(frozen=True)
class CrossSystemCommand(Command):
    """Command trên aggregate E-I — biên là `tracking_code` (`INV-61`)."""

    tracking_code: str = ""
    public_purchase_code: str = ""
    evidence: Optional[Evidence] = None

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.tracking_code or not self.public_purchase_code:
            raise ValueError(
                "CrossSystemCommand bắt buộc có tracking_code và public_purchase_code"
            )
        if self.evidence is None:
            raise ValueError("CrossSystemCommand bắt buộc có evidence (§6.7)")

    @property
    def aggregate_id(self) -> str:
        return self.tracking_code


@dataclass(frozen=True)
class ConfirmCrossSystem(CrossSystemCommand):
    """`confirmation_action`. Cần một lần, KỂ CẢ khi hai mã bằng nhau
    (`INV-38`)."""

    event_type: EventType = EventType.CONFIRM_CROSS_SYSTEM


@dataclass(frozen=True)
class CorrectCrossSystem(CrossSystemCommand):
    """Sửa một cross-system mapping. `reason` REQUIRED."""

    event_type: EventType = EventType.CORRECT_CROSS_SYSTEM


@dataclass(frozen=True)
class RegistryCommand(Command):
    """Command trên aggregate E-J — biên là `entry_id` (`INV-61`)."""

    entry_id: str = ""

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.entry_id:
            raise ValueError("entry_id REQUIRED")

    @property
    def aggregate_id(self) -> str:
        return self.entry_id


@dataclass(frozen=True)
class ConfirmHistoricalEntry(RegistryCommand):
    """Nạp một entry từ báo cáo lịch sử Owner-confirmed (§9, `M2`)."""

    entry: object = None
    event_type: EventType = EventType.CONFIRM_HISTORICAL_ENTRY

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.entry is None:
            raise ValueError("ConfirmHistoricalEntry bắt buộc có entry (E-J)")


@dataclass(frozen=True)
class CorrectHistoricalEntry(RegistryCommand):
    """Sửa một entry lịch sử = supersede. `reason` REQUIRED (`INV-53`)."""

    entry: object = None
    corrected_price: Optional[Decimal] = None
    event_type: EventType = EventType.CORRECT_HISTORICAL_ENTRY

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.entry is None:
            raise ValueError("CorrectHistoricalEntry bắt buộc có entry thay thế")
