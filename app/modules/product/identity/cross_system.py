"""E-I `CrossSystemProductMapping` — data contract §8.

    TRACKING:<tracking_code>  ↔  PUBLIC_PURCHASE:<public_purchase_code>

Đây **không** phải đổi namespace của sản phẩm. Một sản phẩm mang identity
`TRACKING:X` vẫn là `TRACKING:X` sau khi lấy giá từ Public Purchase
(`INV-45`, `DEC-154` §7/`P10`). Mapping này trả lời đúng MỘT câu hỏi: "khi
hàng Tracking này không có giá NCC hợp lệ, tra giá công khai dưới mã nào?"

## Vì sao lookup ở đây từ chối "đoán" một cách hung hăng như vậy

`INV-38` cấm suy ra mapping chỉ vì hai mã giống chuỗi nhau — **kể cả khi bằng
nhau tuyệt đối**. Điều đó nghe cực đoan cho tới khi nhìn vào hậu quả: hai hệ
thống khác nhau đặt mã độc lập, nên một trùng chuỗi là một trùng hợp, và một
trùng hợp được đọc thành mapping sẽ lấy giá của một sản phẩm khác đưa vào giá
vốn. `lookup_public_purchase_code()` vì thế chỉ có đúng hai kết cục: mã CỦA
CHÍNH một mapping `CONFIRMED` đang active, hoặc absence. Không có kết cục thứ
ba nào trả về một mã dẫn xuất (`INV-43c`, `INV-44`).

Điều kiện (a) của `INV-43` — "không có valid vendor candidate tại `sale_date`"
— thuộc lớp composition `TASK-105E` và cố ý KHÔNG nằm ở đây (`CHECK-105D-31`
RANH GIỚI PHẠM VI).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from app.modules.product.identity.evidence import Evidence


class CrossSystemStatus(str, Enum):
    CONFIRMED = "CONFIRMED"
    SUPERSEDED = "SUPERSEDED"
    CONFLICT = "CONFLICT"


class CrossSystemConflictError(RuntimeError):
    """`INV-40` — vi phạm 1:1 của `INV-39`.

    Lỗi tường minh + `status = CONFLICT`, KHÔNG silent last-write-wins: N:1 làm
    giá fallback mơ hồ, và "mơ hồ" ở đây nghĩa là hai sản phẩm khác nhau có thể
    nhận cùng một giá vốn.
    """


@dataclass(frozen=True)
class CrossSystemProductMapping:
    """E-I. Correction theo khuôn §13: supersede, KHÔNG DELETE (`INV-41`)."""

    mapping_id: str
    tracking_code: str
    public_purchase_code: str
    status: CrossSystemStatus
    confirmed_by: str
    confirmed_at: datetime
    evidence: Evidence
    version: int
    pp_version_id: str
    tracking_capture_id: str
    audit_event_ids: tuple[str, ...] = ()
    reason: Optional[str] = None
    supersedes: Optional[str] = None
    superseded_by: Optional[str] = None

    def to_record(self) -> dict[str, Any]:
        return {
            "mapping_id": self.mapping_id,
            "tracking_code": self.tracking_code,
            "public_purchase_code": self.public_purchase_code,
            "status": self.status.value,
            "confirmed_by": self.confirmed_by,
            "confirmed_at": self.confirmed_at.isoformat(),
            "evidence": {
                "matched_on": self.evidence.matched_on.value,
                "matched_value": self.evidence.matched_value,
                "candidate_set_ids": list(self.evidence.candidate_set_ids),
                "ranking_method_id": self.evidence.ranking_method_id,
                "parent_mapping_id": self.evidence.parent_mapping_id,
            },
            "version": self.version,
            "pp_version_id": self.pp_version_id,
            "tracking_capture_id": self.tracking_capture_id,
            "audit_event_ids": list(self.audit_event_ids),
            "reason": self.reason,
            "supersedes": self.supersedes,
            "superseded_by": self.superseded_by,
        }
