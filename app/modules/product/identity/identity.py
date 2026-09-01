"""`CanonicalProductIdentity` (E-E) và `ResolutionOutcome` — data contract §5.

## Vì sao union ở đây là một union ĐÓNG THẬT SỰ

`CHECK-105D-02` không yêu cầu "resolver trả về một trong bốn giá trị". Nó yêu
cầu một **assertion kiểu chứng minh không tồn tại nhánh trả về ngoài union**.
Một `Union[...]` của typing không làm được điều đó: nó là chú thích, không ai
thi hành lúc chạy, và một biến thể thứ năm được thêm ở file khác vẫn chạy
bình thường cho tới khi nó rơi vào một `else` nào đó ở tầng giá.

Nên `ResolutionOutcome` tự đóng chính nó: `__init_subclass__` từ chối mọi lớp
con khai báo sau khi bốn biến thể hợp lệ đã đăng ký. Đây là cùng cơ chế mà
`app/modules/domain/canonical.py` đã dùng cho seal — "giữ được object chính là
bằng chứng object hợp lệ" — chứ không phải một quy ước đặt tên.

## Vì sao Pending là một KIỂU, không phải một giá trị rỗng

`INV-25` cấm `None`/`""`/`0` biểu diễn Pending. Lý do không phải thẩm mỹ:
`None` hợp nhất "chưa biết" với "không có", và ở tầng trên `None` là đầu vào
hợp lệ của rất nhiều phép toán — nó lặng lẽ trở thành 0 đồng. `PENDING_PRODUCT`
là một trạng thái nghiệp vụ hợp lệ (`DEC-103`), nên nó phải có kiểu riêng,
mang `reason_code` và `attempted_sources` để người đọc report biết resolver đã
thử những gì.
"""

from __future__ import annotations

from dataclasses import dataclass, fields
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional


class Namespace(str, Enum):
    """Enum ĐÓNG (`INV-17`). Thêm giá trị = quyết định Owner + task riêng."""

    TRACKING = "TRACKING"
    PUBLIC_PURCHASE = "PUBLIC_PURCHASE"


class PendingReason(str, Enum):
    """`reason_code` của `PENDING_PRODUCT` — enum đóng, data contract §5."""

    NO_CANDIDATE_IN_ANY_CATALOG = "NO_CANDIDATE_IN_ANY_CATALOG"
    AMBIGUOUS_MULTIPLE_DETERMINISTIC_CANDIDATES = (
        "AMBIGUOUS_MULTIPLE_DETERMINISTIC_CANDIDATES"
    )
    ONLY_SIMILARITY_EVIDENCE = "ONLY_SIMILARITY_EVIDENCE"
    CANDIDATE_REJECTED_AND_EVIDENCE_UNCHANGED = (
        "CANDIDATE_REJECTED_AND_EVIDENCE_UNCHANGED"
    )
    MAPPING_STALE_TARGET_ABSENT = "MAPPING_STALE_TARGET_ABSENT"
    AWAITING_HUMAN_CONFIRMATION = "AWAITING_HUMAN_CONFIRMATION"
    PENDING_HISTORICAL_CONFIRMATION = "PENDING_HISTORICAL_CONFIRMATION"
    TRACKING_INV_MAP_EXPLICIT_IGNORE = "TRACKING_INV_MAP_EXPLICIT_IGNORE"
    """`inv.map[key] == "-"` — người của Tracking đã xem và xác nhận đây
    KHÔNG phải một sản phẩm cần map (S068 follow-up). Khác `NO_CANDIDATE_IN_
    ANY_CATALOG` (chưa ai xem): đây là một sự kiện đã người quyết định."""


class AttemptedSource(str, Enum):
    """Nguồn mà resolver đã thực sự tra trước khi kết luận Pending.

    `CHECK-105D-27` assert `attempted_sources` của một Pending liệt kê CẢ HAI
    catalog — đó là bằng chứng resolver không dừng ở Tracking MISS.
    """

    ALIAS_MEMORY = "ALIAS_MEMORY"
    TRACKING_CATALOG = "TRACKING_CATALOG"
    PUBLIC_PURCHASE_CATALOG = "PUBLIC_PURCHASE_CATALOG"
    CANDIDATE_RANKING = "CANDIDATE_RANKING"
    HISTORICAL_CONFIRMED_REGISTRY = "HISTORICAL_CONFIRMED_REGISTRY"


class IdentityValueError(ValueError):
    """Một giá trị identity không hợp lệ về cấu trúc."""


@dataclass(frozen=True)
class CanonicalProductIdentity:
    """E-E — value object. So sánh LUÔN bằng ĐỦ TUPLE (`INV-18`).

    `TRACKING:X` và `PUBLIC_PURCHASE:X` là hai identity khác nhau. Vì đây là
    một frozen dataclass hai trường, `==` và `hash()` đã dùng đủ tuple; không
    có đường nào so sánh chỉ bằng `source_product_code` mà không viết ra
    tường minh — đó là điều `CHECK-105D-30` đi tìm.
    """

    namespace: Namespace
    source_product_code: str

    def __post_init__(self) -> None:
        if not isinstance(self.namespace, Namespace):
            raise IdentityValueError(f"namespace ngoài enum đóng: {self.namespace!r}")
        if not self.source_product_code or not self.source_product_code.strip():
            raise IdentityValueError("source_product_code REQUIRED, không được rỗng")

    def __str__(self) -> str:
        return f"{self.namespace.value}:{self.source_product_code}"


@dataclass(frozen=True)
class Provenance:
    """Provenance của một kết quả resolve — task §"Provenance Contract", `G21` A.

    KHÔNG có trường giá dưới bất kỳ tên nào: `CHECK-105D-16` quét đúng tập
    trường này. Giá của nhánh pre-cutover nằm trên `HistoricalConfirmed`, nơi
    nó đến TỪ registry chứ không do resolver tính (`INV-46`).
    """

    raw_product_identity: str
    resolution_method: str
    resolved_at: datetime
    mapping_source: Optional[str] = None
    namespace: Optional[Namespace] = None
    source_product_code: Optional[str] = None
    mapping_id: Optional[str] = None
    mapping_version: Optional[int] = None
    pp_version_id: Optional[str] = None
    tracking_capture_id: Optional[str] = None
    price_provenance: Optional[str] = None
    """Nhãn `DEC-154` §10 — chỉ dùng ở nhánh lịch sử và ở fallback cross-system.

    Nó ghi *đường đi* của giá, không phải một con số giá; `CHECK-105D-32` cần
    nó để phân biệt `PUBLIC_PURCHASE_NO_VENDOR_PRICE` (identity TRACKING lấy
    giá công khai qua mapping) với `PUBLIC_PURCHASE_NO_TRACKING` (identity
    Public Purchase trực tiếp).
    """


class ResolutionOutcome:
    """Union ĐÓNG. Bốn biến thể, không có biến thể thứ năm (`INV-24`/`INV-25`).

    `_sealed` bật lên sau khi bốn biến thể hợp lệ đã khai báo; từ đó mọi lớp
    con mới nổ ngay lúc định nghĩa lớp, không đợi tới lúc chạy.
    """

    _sealed = False
    _variants: tuple[type, ...] = ()

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        if ResolutionOutcome._sealed:
            raise TypeError(
                f"ResolutionOutcome là union ĐÓNG (INV-24/INV-25); "
                f"không thêm được biến thể {cls.__name__!r}"
            )
        ResolutionOutcome._variants += (cls,)


@dataclass(frozen=True)
class Resolved(ResolutionOutcome):
    """Resolve chắc chắn. Luôn mang ĐỦ tuple identity (`CHECK-105D-02`)."""

    identity: CanonicalProductIdentity
    provenance: Provenance


@dataclass(frozen=True)
class RequiresConfirmation(ResolutionOutcome):
    """AMBIGUOUS — cần đúng một quyết định của người (`CHECK-105D-23`)."""

    candidates: tuple = ()
    provenance: Optional[Provenance] = None


@dataclass(frozen=True)
class PendingProduct(ResolutionOutcome):
    """Trạng thái nghiệp vụ HỢP LỆ, không phải lỗi (`DEC-103`).

    Không mang `namespace`, không mang `source_product_code` (`INV-24`) — kiểm
    ngay tại `__post_init__` để một provenance mang identity không lọt được
    vào một Pending.
    """

    reason_code: PendingReason
    attempted_sources: tuple[AttemptedSource, ...] = ()
    provenance: Optional[Provenance] = None

    def __post_init__(self) -> None:
        if not isinstance(self.reason_code, PendingReason):
            raise IdentityValueError(
                f"reason_code ngoài enum đóng: {self.reason_code!r}"
            )
        prov = self.provenance
        if prov is not None and (
            prov.namespace is not None or prov.source_product_code is not None
        ):
            raise IdentityValueError(
                "INV-24: PENDING_PRODUCT không bao giờ mang namespace/"
                "source_product_code"
            )


@dataclass(frozen=True)
class HistoricalConfirmed(ResolutionOutcome):
    """Nhánh pre-cutover. `identity` OPTIONAL theo `INV-50`.

    Đây là biến thể DUY NHẤT mang giá, và giá đó đến từ
    `HistoricalConfirmedRegistry` — resolver không tính nó (`INV-46`,
    `CHECK-105D-16`).
    """

    price: Decimal
    provenance: Provenance
    identity: Optional[CanonicalProductIdentity] = None


ResolutionOutcome._sealed = True

POST_CUTOVER_VARIANTS: tuple[type, ...] = (
    Resolved,
    RequiresConfirmation,
    PendingProduct,
)
"""Ba biến thể hợp lệ sau cutover. `HISTORICAL_CONFIRMED` không được rò sang."""


def outcome_field_names(variant: type) -> frozenset[str]:
    """Tập tên trường của một biến thể — dùng cho assertion cấu trúc `G16`."""
    return frozenset(f.name for f in fields(variant))
