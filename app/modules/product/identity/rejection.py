"""E-H `RejectedCandidate` — bộ nhớ từ chối, data contract §7.

Người dùng đã nói "không phải cái này" một lần thì hệ thống không được hỏi lại
**cùng một câu**. Nhưng nó cũng không được chặn vĩnh viễn khi bằng chứng đã
đổi — một mã mới xuất hiện trong version Public Purchase tiếp theo có thể làm
candidate cũ trở nên đúng.

Cơ chế cân bằng hai vế đó là `evidence_fingerprint` (§7.3): suppress khi và
chỉ khi cùng khoá VÀ cùng fingerprint (`INV-34`). Đổi `pp_version_id`,
`tracking_capture_id`, tập candidate, hay thuật toán xếp hạng → fingerprint
đổi → candidate được đề xuất lại kèm chú thích (`INV-35`).

`reason` là OPTIONAL (`D-09`) và đó là một quyết định có chủ đích: bắt buộc lý
do cho mọi lần từ chối biến một thao tác đáng lẽ một phím thành một biểu mẫu,
phá thẳng mục tiêu `<= 1 confirmation_action`. `rejected_by` và `rejected_at`
REQUIRED là đủ để truy trách nhiệm.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from app.modules.product.identity.identity import Namespace


@dataclass(frozen=True)
class RejectedCandidate:
    """E-H. Mọi trường IMMUTABLE."""

    rejection_id: str
    source_system: str
    raw_identity_key: str
    candidate_namespace: Namespace
    candidate_code: str
    evidence_fingerprint: str
    rejected_by: str
    rejected_at: datetime
    pp_version_id: Optional[str]
    tracking_capture_id: Optional[str]
    audit_event_id: str
    reason: Optional[str] = None

    @property
    def suppression_key(self) -> tuple[str, Namespace, str, str]:
        """Khoá `INV-34`: ĐỦ bốn phần, gồm cả fingerprint.

        Bỏ fingerprint ra khỏi khoá này là biến rejection memory thành một
        blacklist vĩnh viễn — đúng điều `INV-35` cấm.
        """
        return (
            self.raw_identity_key,
            self.candidate_namespace,
            self.candidate_code,
            self.evidence_fingerprint,
        )

    def to_record(self) -> dict[str, Any]:
        return {
            "rejection_id": self.rejection_id,
            "source_system": self.source_system,
            "raw_identity_key": self.raw_identity_key,
            "candidate_namespace": self.candidate_namespace.value,
            "candidate_code": self.candidate_code,
            "evidence_fingerprint": self.evidence_fingerprint,
            "rejected_by": self.rejected_by,
            "rejected_at": self.rejected_at.isoformat(),
            "pp_version_id": self.pp_version_id,
            "tracking_capture_id": self.tracking_capture_id,
            "audit_event_id": self.audit_event_id,
            "reason": self.reason,
        }
