"""Evidence, `resolution_method` và candidate ranking — data contract §6.6/§6.7.

## Tập auto-resolve là một TẬP ĐÓNG

`INV-28` (sửa theo `DEC-156`/`OR-02`): chỉ `ALIAS_EXACT` và
`CATALOG_EXACT_UNIQUE` được auto-resolve. `ALIAS_AID_UNIQUE` — khớp duy nhất
sau casefold với một alias đã confirm — **không** nằm trong tập đó
(`INV-28b`): Owner chọn trả một xác nhận cho mỗi *cách viết mới* thay vì để hệ
thống tự tạo một mapping `CONFIRMED` mà chưa có thao tác người nào cho chính
identity ấy. Chi phí là một lần cho mỗi biến thể, không phải lặp lại: từ lần
thứ hai nó đã là `ALIAS_EXACT`.

Tập này được viết thành một `frozenset` ở cấp module, và mọi câu hỏi
"có được auto-resolve không?" trong toàn bộ package đều đi qua
`is_auto_resolvable()`. Không có nơi thứ hai để một phương thức lọt vào tập.

## `H-05` — `ranking_method_id`

Freeze Review #2 để mở `H-05`: `ranking_method_id` là `OPTIONAL` ở §6.7 nhưng
lại là một input được hash vào `evidence_fingerprint` (§7.3). Nếu nó vắng,
chiều "thuật toán xếp hạng đã đổi" của `INV-35` im lặng biến mất.

Phiên implementation **không** có thẩm quyền đổi `OPTIONAL → REQUIRED` trong
data contract, nên trường giữ nguyên `OPTIONAL`. Hai việc được làm ở đây, cả
hai đều nằm trong thẩm quyền implementation và không đụng tới contract:

1. Resolver của package này LUÔN gắn `RANKING_METHOD_ID` cho mọi candidate nó
   sinh ra, nên trên đường đi thật trường không bao giờ vắng.
2. `evidence_fingerprint()` thay `None` bằng một sentinel tường minh
   (`_ABSENT_RANKING_METHOD`) thay vì bỏ trường ra khỏi hash. Nhờ đó fingerprint
   vẫn xác định, và một producer bên ngoài quên gắn `ranking_method_id` vẫn
   phân biệt được với một producer gắn nó — chiều `INV-35` không biến mất.

Trạng thái contract-level của `H-05` **vẫn OPEN**: đóng nó cần một phiên có
thẩm quyền sửa data contract. Ghi ở đây để phiên sau không đọc nhầm rằng nó đã
được đóng bằng code.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from enum import Enum
from typing import Optional

RANKING_METHOD_ID = "identity-candidate-rank/v1"
"""Định danh + version của thuật toán xếp hạng ở `rank_candidates()`.

Đổi thuật toán = đổi hằng số này. Đó là điều làm cho chiều "thuật toán xếp
hạng đã đổi" của `INV-35` thành một sự kiện quan sát được, không phải một giả
định.
"""

_ABSENT_RANKING_METHOD = "\x00<absent>"
"""Sentinel cho `ranking_method_id` vắng — xem ghi chú `H-05` ở đầu file."""


class ResolutionMethod(str, Enum):
    """Enum đóng, data contract §6.6."""

    ALIAS_EXACT = "ALIAS_EXACT"
    CATALOG_EXACT_UNIQUE = "CATALOG_EXACT_UNIQUE"
    ALIAS_AID_UNIQUE = "ALIAS_AID_UNIQUE"
    TRACKING_ALIAS_MAP = "TRACKING_ALIAS_MAP"
    TRACKING_CONFIRMED_ALIAS = "TRACKING_CONFIRMED_ALIAS"
    TRACKING_CANONICAL_EXACT = "TRACKING_CANONICAL_EXACT"
    SIMILARITY_RANKED = "SIMILARITY_RANKED"
    CROSS_NAMESPACE_TIE = "CROSS_NAMESPACE_TIE"
    MULTIPLE_EXACT = "MULTIPLE_EXACT"


AUTO_RESOLVE_METHODS: frozenset[ResolutionMethod] = frozenset(
    {
        ResolutionMethod.ALIAS_EXACT,
        ResolutionMethod.CATALOG_EXACT_UNIQUE,
        ResolutionMethod.TRACKING_CONFIRMED_ALIAS,
        ResolutionMethod.TRACKING_CANONICAL_EXACT,
    }
)
"""TẬP ĐÓNG — mỗi phần tử được Owner cấp authority tường minh.

Thêm một phần tử vào đây là một quyết định Owner, không phải một quyết định
implementation.
"""


def is_auto_resolvable(method: ResolutionMethod) -> bool:
    """Đường DUY NHẤT trong package để hỏi "có được auto-resolve không?"."""
    return method in AUTO_RESOLVE_METHODS


def is_ambiguous(method: ResolutionMethod) -> bool:
    """AMBIGUOUS = KHÔNG thuộc tập auto-resolve đóng (§17.2)."""
    return not is_auto_resolvable(method)


class MatchedOn(str, Enum):
    """Enum đóng, data contract §6.7."""

    RAW_KEY = "RAW_KEY"
    AID = "AID"
    TRACKING_CODE = "TRACKING_CODE"
    TRACKING_NAME = "TRACKING_NAME"
    TRACKING_ALT = "TRACKING_ALT"
    TRACKING_ALIAS_MAP = "TRACKING_ALIAS_MAP"
    PP_PRODUCT_CODE = "PP_PRODUCT_CODE"
    PP_ALIAS = "PP_ALIAS"
    MANUAL_SEARCH = "MANUAL_SEARCH"


class EvidenceError(ValueError):
    """Evidence thiếu một trường REQUIRED của §6.7."""


@dataclass(frozen=True)
class Evidence:
    """Evidence §6.7. Ba trường đầu REQUIRED — `CHECK-105D-08` đếm đúng chúng."""

    matched_on: MatchedOn
    matched_value: str
    candidate_set_ids: tuple[str, ...]
    ranking_method_id: Optional[str] = None
    parent_mapping_id: Optional[str] = None

    def __post_init__(self) -> None:
        if not isinstance(self.matched_on, MatchedOn):
            raise EvidenceError(f"matched_on ngoài enum đóng: {self.matched_on!r}")
        if self.matched_value is None or self.matched_value == "":
            raise EvidenceError("matched_value REQUIRED — giá trị đã khớp, nguyên văn")
        if self.candidate_set_ids is None:
            raise EvidenceError("candidate_set_ids REQUIRED (có thể là tuple rỗng)")


@dataclass(frozen=True)
class RankedCandidate:
    """Một candidate đã xếp hạng, kèm evidence đầy đủ.

    `target_present_in_board` mang chiều `INV-14c`: một candidate trỏ tới một
    mã đã biến mất khỏi board hiện tại vẫn được hiển thị (nó là bằng chứng
    thật), nhưng nó không bao giờ được auto-resolve.
    """

    namespace: "object"
    source_product_code: str
    method: ResolutionMethod
    evidence: Evidence
    rank: int
    target_present_in_board: bool = True
    note: Optional[str] = None
    """Chú thích hiển thị, ví dụ "đã từ chối tại <version cũ>" (`INV-35`)."""

    @property
    def candidate_id(self) -> str:
        """Định danh ổn định của candidate — ĐỦ TUPLE, không chỉ mã (`INV-18`)."""
        return f"{self.namespace.value}:{self.source_product_code}"


def evidence_fingerprint(
    *,
    pp_version_id: Optional[str],
    tracking_capture_id: Optional[str],
    candidate_set_ids: tuple[str, ...],
    ranking_method_id: Optional[str],
) -> str:
    """Fingerprint của bằng chứng tại thời điểm một candidate bị từ chối (§7.3).

    Bốn input đúng như contract. `sorted()` trên `candidate_set_ids` để thứ tự
    hiển thị không làm đổi fingerprint — cùng một tập candidate là cùng một
    bằng chứng, dù xếp hạng có hoán vị.

    Trả về hex SHA-256: một chuỗi so sánh được, in ra được trong audit log, và
    không phụ thuộc `hash()` của Python (vốn đổi theo `PYTHONHASHSEED` — đúng
    thứ `INV-64` cấm).
    """
    parts = [
        pp_version_id or "",
        tracking_capture_id or "",
        "\x1f".join(sorted(candidate_set_ids)),
        ranking_method_id if ranking_method_id is not None else _ABSENT_RANKING_METHOD,
    ]
    payload = "\x1e".join(parts).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()
