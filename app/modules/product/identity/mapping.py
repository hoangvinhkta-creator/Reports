"""E-F `ProductIdentityMapping` và E-G `AliasMemory` — data contract §6.

## Một store, hai cách nhìn

`D-06`: `AliasMemory` **không phải** một store thứ hai. Nó là một *index tra
cứu* trên các bản ghi `ProductIdentityMapping` đang ACTIVE. Hai store song song
là hai nguồn sự thật — đúng lỗi mà `S021`/`DEC-132` đã phải sửa bằng một vòng
architecture repair. Vì thế trong package này không có lớp `AliasMemory` giữ
dữ liệu riêng: alias memory là `ProductIdentityStore.read_active_mapping()`,
và `alias_index()` chỉ dựng lại một dict từ chính log.

## Mapping KHÔNG chứa giá

`INV-23` / `CHECK-105D-15`. Assertion của gate là **cấu trúc**, và nó chạy
trên cả bản ghi đã persist trong log chứ không chỉ trên dataclass — nên
`to_record()` dưới đây là bề mặt thật mà gate kiểm. Không thêm một trường giá
"để tiện", kể cả nullable, kể cả chỉ dùng cho cache.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from app.modules.product.identity.evidence import Evidence, ResolutionMethod
from app.modules.product.identity.identity import Namespace

SOURCE_SYSTEM_REPORTS_SALES = "REPORTS_SALES"
"""Phase 1 có đúng một `source_system` (§6.2)."""


class MappingStatus(str, Enum):
    """Enum đóng, §6.4.

    `OUT_OF_CATALOG` thêm ở R2 theo `R2 Execution Brief` §4.1/§4.3. Nó là một
    KẾT QUẢ PHÂN LOẠI HOÀN TẤT, không phải một biến thể của `PENDING`, và ba
    thứ dưới đây là những gì nó KHÔNG có nghĩa (§4.1):

        hết hàng (`OUT_OF_STOCK`)         — đó là trạng thái của một NGÀY
        Tracking chưa trả được giá        — đó là `SOURCE_UNAVAILABLE`/`NO_DATA`
        loại dòng khỏi báo cáo            — đó là `line_exclusion`

    Gộp nó vào `PENDING` sẽ làm màn hình hỏi Owner phân loại lại một thứ họ đã
    phân loại xong; gộp nó vào `CONFIRMED` sẽ đòi một `source_product_code`
    không tồn tại. Nên nó là một trạng thái riêng.
    """

    CONFIRMED = "CONFIRMED"
    PENDING = "PENDING"
    SUPERSEDED = "SUPERSEDED"
    CONFLICT = "CONFLICT"
    STALE = "STALE"
    OUT_OF_CATALOG = "OUT_OF_CATALOG"


class MappingSource(str, Enum):
    """Enum đóng, §6.5.

    `HUMAN_CONFLICT_RESOLUTION` thêm ở R2 (§4.2). Nó KHÔNG phải một cách nói
    khác của `HUMAN_CONFIRMATION`: nó ghi rằng người dùng đã được cho xem một
    mâu thuẫn giữa quyết định của Reports và authority của Tracking, và vẫn
    chọn. Không có nhãn đó thì lần chạy sau lại phát hiện đúng mâu thuẫn ấy và
    lại hỏi lại — một vòng lặp không bao giờ kết thúc, vì mâu thuẫn được suy ra
    từ dữ liệu chứ không được lưu.
    """

    HUMAN_CONFIRMATION = "HUMAN_CONFIRMATION"
    HUMAN_CONFLICT_RESOLUTION = "HUMAN_CONFLICT_RESOLUTION"
    DETERMINISTIC_CATALOG_MATCH = "DETERMINISTIC_CATALOG_MATCH"
    OWNER_BOOTSTRAP = "OWNER_BOOTSTRAP"
    HISTORICAL_CONFIRMED_REPORT = "HISTORICAL_CONFIRMED_REPORT"


#: Các `mapping_source` nói rằng bản ghi đến từ một quyết định của NGƯỜI phía
#: Reports. Dùng ở resolver để trả lời "đây có phải quyết định người không",
#: thay vì so chuỗi rải rác ở nhiều nơi.
HUMAN_MAPPING_SOURCES: frozenset[MappingSource] = frozenset(
    {MappingSource.HUMAN_CONFIRMATION, MappingSource.HUMAN_CONFLICT_RESOLUTION}
)


PRICE_LIKE_FIELD_NAMES = frozenset(
    {
        "price",
        "purchase_price",
        "unit_price",
        "cost",
        "amount",
        "currency",
        "money",
        "vnd",
        "gia",
        "gia_von",
        "price_unit",
    }
)
"""Tập tên trường mà `CHECK-105D-15` khẳng định KHÔNG giao với schema E-F."""


class MappingIntegrityError(RuntimeError):
    """`INV-33` — store chứa nhiều hơn một `CONFIRMED` cho cùng một khoá.

    Cố ý fatal và cố ý KHÔNG tự chọn một bản ghi: chọn bừa một trong hai
    mapping xung đột là một phép tung đồng xu rơi thẳng vào giá vốn. Cùng
    nguyên tắc với `AmbiguousSchemeConfigError`.
    """


@dataclass(frozen=True)
class ProductIdentityMapping:
    """E-F. Mọi trường IMMUTABLE trừ `status`/`superseded_by`/`audit_event_ids`,
    và cách đổi chúng là **ghi một bản ghi mới**, không phải sửa tại chỗ."""

    mapping_id: str
    source_system: str
    raw_product_identity: str
    raw_identity_key: str
    normalized_matching_aid: str
    status: MappingStatus
    mapping_source: MappingSource
    resolution_method: ResolutionMethod
    evidence: Evidence
    version: int
    created_at: datetime
    created_by: str
    namespace: Optional[Namespace] = None
    source_product_code: Optional[str] = None
    supersedes: Optional[str] = None
    superseded_by: Optional[str] = None
    pp_version_id: Optional[str] = None
    tracking_capture_id: Optional[str] = None
    confirmed_at: Optional[datetime] = None
    confirmed_by: Optional[str] = None
    audit_event_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.status is MappingStatus.CONFIRMED:
            if self.namespace is None or self.source_product_code is None:
                raise ValueError(
                    "status=CONFIRMED bắt buộc có namespace và source_product_code "
                    "(§6.2)"
                )
            if self.confirmed_at is None or not self.confirmed_by:
                raise ValueError(
                    "status=CONFIRMED bắt buộc có confirmed_at/confirmed_by (§6.2)"
                )

    @property
    def identity_tuple(self) -> Optional[tuple[Namespace, str]]:
        if self.namespace is None or self.source_product_code is None:
            return None
        return (self.namespace, self.source_product_code)

    def to_record(self) -> dict[str, Any]:
        """Biểu diễn persist được — bề mặt mà `CHECK-105D-15` quét."""
        record = asdict(self)
        record["status"] = self.status.value
        record["mapping_source"] = self.mapping_source.value
        record["resolution_method"] = self.resolution_method.value
        record["namespace"] = self.namespace.value if self.namespace else None
        record["evidence"] = _evidence_record(self.evidence)
        record["created_at"] = self.created_at.isoformat()
        record["confirmed_at"] = (
            self.confirmed_at.isoformat() if self.confirmed_at else None
        )
        # JSON không có tuple. Ép sang list ngay tại đây để bản ghi trong bộ
        # nhớ và bản ghi đọc lại từ log so sánh được bằng `==` — `INV-65` yêu
        # cầu import lại cho ra một store TƯƠNG ĐƯƠNG BIT, và một tuple còn sót
        # làm phép so sánh đó thất bại vì lý do không liên quan tới dữ liệu.
        record["audit_event_ids"] = list(self.audit_event_ids)
        return record


def _evidence_record(evidence: Evidence) -> dict[str, Any]:
    return {
        "matched_on": evidence.matched_on.value,
        "matched_value": evidence.matched_value,
        "candidate_set_ids": list(evidence.candidate_set_ids),
        "ranking_method_id": evidence.ranking_method_id,
        "parent_mapping_id": evidence.parent_mapping_id,
    }


def mapping_field_names() -> frozenset[str]:
    """Tên trường của E-F — dùng cho assertion cấu trúc của `CHECK-105D-15`."""
    return frozenset(f.name for f in fields(ProductIdentityMapping))
