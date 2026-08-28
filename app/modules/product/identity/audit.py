"""E-K `MappingAuditEvent` — append-only, data contract §13.

## Actor ở Phase 1 là KHAI BÁO, không phải danh tính đã xác thực

`OR-03` (`DEC-156` §3, APPROVED FOR PHASE 1) + `INV-72`/`INV-73`. Ba ràng buộc
giữ nguyên hiệu lực và cả ba đều được thi hành bằng code chứ không bằng quy ước:

- `actor_id` REQUIRED trên mọi command đổi state — `require_actor()` dưới đây
  là cổng duy nhất;
- KHÔNG có giá trị mặc định: cấm `"system"`, cấm anonymous, cấm suy ra từ biến
  môi trường / OS user / config / hằng số trong mã;
- CẤM mô tả actor Phase 1 là "authenticated".

Điều audit trail Phase 1 chứng minh được là "bản ghi này **khai** actor X".
Điều nó KHÔNG chứng minh được là "người thật sự thao tác là X". Đó là một
CAPABILITY BOUNDARY có thật (`§12.1`) và `ACTOR_DISCLOSURE` dưới đây là câu
nói ra sự thật đó ở mọi nơi actor được hiển thị — không phải một lời phủ nhận
lịch sự.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional

ACTOR_DISCLOSURE = "actor do người vận hành khai báo (Phase 1 — chưa có xác thực)"
"""Câu công bố bắt buộc ở mọi bề mặt hiển thị actor (`INV-73`).

Cố ý KHÔNG chứa các cụm bị cấm ("authenticated", "authenticated user", "danh
tính đã xác thực") — `CHECK-105D-21` Phần B quét đúng các cụm đó trên toàn bộ
artifact/chuỗi hiển thị do task sinh ra.
"""

FORBIDDEN_ACTOR_PHRASES: tuple[str, ...] = (
    "authenticated user",
    "authenticated",
    "danh tính đã xác thực",
    "đã xác thực danh tính",
)
"""Cụm từ bị `INV-73` cấm gắn với actor Phase 1."""


class MissingActorError(ValueError):
    """`INV-72` — command đổi state thiếu `actor_id`.

    Rỗng và chỉ-khoảng-trắng đều tính là THIẾU. Không có nhánh nào điền giá
    trị thay: một audit trail mà hệ thống tự ký tên hộ thì không phải audit
    trail.
    """


class MissingReasonError(ValueError):
    """`D-13` — `reason` REQUIRED cho mọi `CORRECT_*` và cho `REPIN_REPORT`."""


def require_actor(actor_id: Optional[str]) -> str:
    """Cổng DUY NHẤT nhận `actor_id` vào hệ thống (`INV-72`)."""
    if actor_id is None or not str(actor_id).strip():
        raise MissingActorError(
            "actor_id REQUIRED, non-empty, non-whitespace; không có giá trị mặc "
            "định, không suy ra từ OS/env/config (INV-72, OR-03)"
        )
    return str(actor_id)


class EventType(str, Enum):
    """Enum đóng, §13.2."""

    CONFIRM_MAPPING = "CONFIRM_MAPPING"
    CORRECT_MAPPING = "CORRECT_MAPPING"
    REJECT_CANDIDATE = "REJECT_CANDIDATE"
    SET_PENDING = "SET_PENDING"
    CONFIRM_CROSS_SYSTEM = "CONFIRM_CROSS_SYSTEM"
    CORRECT_CROSS_SYSTEM = "CORRECT_CROSS_SYSTEM"
    CONFIRM_HISTORICAL_ENTRY = "CONFIRM_HISTORICAL_ENTRY"
    CORRECT_HISTORICAL_ENTRY = "CORRECT_HISTORICAL_ENTRY"
    BOOTSTRAP_MAPPING = "BOOTSTRAP_MAPPING"
    MARK_STALE = "MARK_STALE"
    REPIN_REPORT = "REPIN_REPORT"


CONFIRMATION_ACTION_TYPES: frozenset[EventType] = frozenset(
    {
        EventType.CONFIRM_MAPPING,
        EventType.REJECT_CANDIDATE,
        EventType.CONFIRM_CROSS_SYSTEM,
        EventType.SET_PENDING,
    }
)
"""ĐÚNG BỐN loại được đếm là `confirmation_action` (§17.1, `D-14`).

Đếm command ở tầng domain, KHÔNG đếm phím/click. Lý do là nghiệp vụ chứ không
phải kỹ thuật: đếm keystroke biến một gate nghiệp vụ thành một gate của thư
viện UI — cùng một hành động sẽ "đạt" hay "trượt" tuỳ bàn phím hay chuột. Cái
nghiệp vụ quan tâm là **số lần con người phải quyết định**.

Điều hướng, cuộn, đổi focus, mở/đóng panel, xem evidence, tìm kiếm, lọc, sắp
xếp: 0 `confirmation_action`. Chúng không xuất hiện ở đây vì chúng không đổi
trạng thái persistent — nên chúng không thể xuất hiện ở đây.
"""

REASON_REQUIRED_TYPES: frozenset[EventType] = frozenset(
    {
        EventType.CORRECT_MAPPING,
        EventType.CORRECT_CROSS_SYSTEM,
        EventType.CORRECT_HISTORICAL_ENTRY,
        EventType.REPIN_REPORT,
    }
)
"""`D-13` — sửa một sự thật đã xác nhận thì phải nói vì sao."""


class AggregateType(str, Enum):
    PRODUCT_IDENTITY_MAPPING = "PRODUCT_IDENTITY_MAPPING"
    CROSS_SYSTEM_MAPPING = "CROSS_SYSTEM_MAPPING"
    REJECTED_CANDIDATE = "REJECTED_CANDIDATE"
    HISTORICAL_REGISTRY_ENTRY = "HISTORICAL_REGISTRY_ENTRY"


@dataclass(frozen=True)
class AffectedScope:
    """§13.3 / `INV-76`.

    `computed_at_revision` là điều làm cho `INV-71` thành sự thật chứ không
    phải lời hứa: phạm vi được TÍNH LẠI từ dữ liệu tại revision đó, nên một
    retry không cộng dồn được — nó tính lại ra cùng con số.
    """

    distinct_identity_count: int
    affected_order_ids: tuple[str, ...]
    affected_line_count: int
    computed_at_revision: int

    def to_record(self) -> dict[str, Any]:
        return {
            "distinct_identity_count": self.distinct_identity_count,
            "affected_order_ids": list(self.affected_order_ids),
            "affected_line_count": self.affected_line_count,
            "computed_at_revision": self.computed_at_revision,
        }


@dataclass(frozen=True)
class MappingAuditEvent:
    """E-K. Append-only: không sửa, không xoá (`INV-32`, `INV-67`)."""

    event_id: str
    revision: int
    event_type: EventType
    aggregate_type: AggregateType
    aggregate_id: str
    actor_id: str
    occurred_at: datetime
    old_value: Optional[dict[str, Any]]
    new_value: Optional[dict[str, Any]]
    affected_scope: AffectedScope
    client_request_id: str
    resulting_version: int
    pp_version_id: Optional[str] = None
    tracking_capture_id: Optional[str] = None
    reason: Optional[str] = None

    def __post_init__(self) -> None:
        require_actor(self.actor_id)
        if self.event_type in REASON_REQUIRED_TYPES and not (
            self.reason and self.reason.strip()
        ):
            raise MissingReasonError(
                f"reason REQUIRED cho {self.event_type.value} (§13.2 / D-13)"
            )

    @property
    def is_confirmation_action(self) -> bool:
        return self.event_type in CONFIRMATION_ACTION_TYPES

    def to_record(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "revision": self.revision,
            "event_type": self.event_type.value,
            "aggregate_type": self.aggregate_type.value,
            "aggregate_id": self.aggregate_id,
            "actor_id": self.actor_id,
            "actor_disclosure": ACTOR_DISCLOSURE,
            "occurred_at": self.occurred_at.isoformat(),
            "old_value": self.old_value,
            "new_value": self.new_value,
            "affected_scope": self.affected_scope.to_record(),
            "client_request_id": self.client_request_id,
            "resulting_version": self.resulting_version,
            "pp_version_id": self.pp_version_id,
            "tracking_capture_id": self.tracking_capture_id,
            "reason": self.reason,
        }
