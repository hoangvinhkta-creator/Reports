"""R6 §3 — CỬA DUY NHẤT từ một dòng tới nhãn sản phẩm / hãng / nhóm hàng.

Reports là bên TIÊU THỤ metadata sản phẩm, không phải nơi sinh ra nó
(`PHB-06 §3`, `ADR-111` §3, `DEC-204`/`DEC-205`/`DEC-206`). File này là chỗ duy
nhất của R6 trả lời "dòng này là mặt hàng nào, của hãng nào, thuộc nhóm hàng
nào", và nó nhỏ đúng bằng câu hỏi đó.

Tiền lệ trực tiếp là `app/web/brand_identity.py`: cùng lý do, cùng hình dạng —
một dãy bucket ĐI SONG SONG với `details`, dựng từ hai nguồn ĐÃ CÓ, không đọc
mạng, không bảng ánh xạ của riêng Reports.

## Ba nguồn, và chỉ ba

```text
line_identity.state_of      dòng đã khớp mã Tracking nào chưa, hay đang mắc gì
identity_gateway.confirmed_identities   khoá dòng → mã Tracking (CHỈ CONFIRMED)
catalog_display.read        mã Tracking → model_label · brand · category_label
```

Không nguồn thứ tư. Không so chuỗi con, không so gần đúng, không rút hãng/nhóm
hàng từ `product_raw`, không suy từ mã máy. Ranh giới giữ bằng CẤU TẠO:
`buckets_for` không nhận `product_raw` như một đầu vào để PHÂN LOẠI — nó chỉ
dùng chuỗi đó làm NHÃN ĐỐI CHIẾU của một bucket đã được xếp là "chưa xác định",
và `tests/test_r6_product_taxonomy.py` canh điều đó bằng chính mã nguồn.

## `product_key` là khoá phân tích DUY NHẤT

R6 KHÔNG tạo một khoá normalize thứ hai. Mọi bảng theo mặt hàng gộp theo
`product_key` hiện hành — cùng khoá mà `order_line_current` dùng làm PK và
cùng khoá mà `business_service.products` đã gộp. Nhãn thì đến từ metadata:
`model_label` của Tracking, fallback mã Tracking, và chỉ khi cả hai vắng mới
tới tên trên sổ kế toán (đã dán nhãn "chưa xác định" ở `kind`).

Thứ tự fallback ấy có hệ quả thật: một mã đối chiếu được vẫn hơn một ô trống
(R5 §5), nhưng một cái tên trên sổ kế toán KHÔNG được đứng ra như một model
canonical — nên nó chỉ xuất hiện trên hàng ĐÃ tự khai là chưa xác định.

## Năm lý do "chưa xác định", tách rời

Gộp chúng thành một ô là gộp năm hành động sửa khác nhau vào một câu:

```text
UNRESOLVED      chưa ai khớp mã cho dòng này        → mở bảng chọn, phân loại
CONFLICT        hai nguồn mapping đang chỏi nhau     → chọn lại (R2 §4.2)
OUT_OF_CATALOG  đã xác nhận nằm ngoài bảng giá       → không phải việc phải sửa
STALE_TARGET    mã đã khớp NAY không còn trong danh mục Tracking → khớp lại
METADATA_ABSENT đã khớp, nhưng Tracking chưa xếp hãng/nhóm hàng cho mã đó
                → sửa BÊN TRACKING, rồi lần capture kế tiếp chở giá trị sang
```

`STALE_TARGET` không phải một trạng thái mà `line_identity` trả về: `state_of`
xếp một dòng như vậy là `MATCHED_TRACKING` (mã lý do
`MAPPING_STALE_TARGET_ABSENT` không nằm trong `IDENTITY_UNRESOLVED_REASONS`,
và đúng như vậy — dòng ĐÃ từng được khớp). Nhưng ở R6 nó phải nhìn ra được:
một mã đã biến mất khỏi danh mục sẽ không có metadata, và nếu nó rơi chung vào
ô `METADATA_ABSENT` thì Owner sẽ đi sửa ngành hàng cho một mã không còn tồn
tại. R6 vì thế ĐỌC mã lý do đó trực tiếp — không sửa `line_identity`, không
thêm một trạng thái thứ hai vào đó.

## Tiền KHÔNG BAO GIỜ biến mất khỏi một bucket

Mọi dòng rơi vào ĐÚNG MỘT bucket ở cả ba chiều — kể cả dòng phí, dòng chiết
khấu, dòng chứng từ chưa định nghĩa và dòng chưa khớp mã. Đó là điều kiện để
`product_metrics.reconciliation` khớp tuyệt đối với tổng của lát dữ liệu, và
là lý do không chiều nào có nhánh "bỏ qua dòng này".
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from app.modules.reporting.product_metrics import (
    KIND_KNOWN, KIND_UNDECIDED, GroupBucket,
)
from app.web import catalog_display, line_identity

#: Mã lý do "mapping đã confirm nhưng target không còn trên board" (`INV-16`,
#: `identity.PendingReason.MAPPING_STALE_TARGET_ABSENT`). Viết bằng CHUỖI vì nó
#: đến từ `pending_reasons_json` ĐÃ nằm trên đĩa — cùng lý do mà
#: `line_identity.IDENTITY_UNRESOLVED_REASONS` đã ghi.
STALE_TARGET_REASONS: frozenset = frozenset({"MAPPING_STALE_TARGET_ABSENT"})

STATE_MATCHED = "MATCHED"
STATE_UNRESOLVED = "UNRESOLVED"
STATE_CONFLICT = "CONFLICT"
STATE_OUT_OF_CATALOG = "OUT_OF_CATALOG"
STATE_STALE_TARGET = "STALE_TARGET"
STATE_METADATA_ABSENT = "METADATA_ABSENT"

#: Thứ tự CỐ ĐỊNH của các bucket "chưa xác định" ở cuối mọi bảng R6. Viết ra
#: thay vì phụ thuộc thứ tự chèn của dict — cùng lý do `brand_metrics.
#: UNKNOWN_ORDER` đã ghi.
UNDECIDED_ORDER: tuple[str, ...] = (
    STATE_UNRESOLVED, STATE_CONFLICT, STATE_STALE_TARGET,
    STATE_OUT_OF_CATALOG, STATE_METADATA_ABSENT,
)

#: Nhãn và LỜI GIẢI THÍCH SỬA Ở ĐÂU của từng lý do. Nhãn đi lên cột đầu bảng,
#: lời giải thích đi vào chú thích của chính hàng đó.
UNDECIDED_LABELS = {
    STATE_UNRESOLVED: "Chưa xác định — chưa khớp mã Tracking",
    STATE_CONFLICT: "Chưa xác định — xung đột mã",
    STATE_STALE_TARGET: "Chưa xác định — mã đã khớp không còn trong danh mục",
    STATE_OUT_OF_CATALOG: "Chưa xác định — ngoài bảng giá",
    STATE_METADATA_ABSENT: "Chưa xác định — Tracking chưa xếp",
}

UNDECIDED_REASONS = {
    STATE_UNRESOLVED: (
        "Chưa ai khớp dòng này với một mã Tracking, nên chưa có danh tính nào "
        "để hỏi hãng hay nhóm hàng. Sửa bằng cách mở bảng chọn mặt hàng trên "
        "bảng kê nhân viên và phân loại dòng."
    ),
    STATE_CONFLICT: (
        "Hai nguồn mapping đã xác nhận đang chỏi nhau về mã của dòng này "
        "(R2 §4.2). Sửa bằng cách CHỌN LẠI mã trên bảng kê nhân viên — không "
        "phải bằng cách xếp lại ngành hàng."
    ),
    STATE_STALE_TARGET: (
        "Dòng đã từng được khớp, nhưng mã Tracking đó KHÔNG còn trong danh mục "
        "hiện hành. Xếp ngành hàng cho nó bên Tracking sẽ không có tác dụng — "
        "cần khớp lại dòng với một mã đang tồn tại."
    ),
    STATE_OUT_OF_CATALOG: (
        "Dòng đã được xác nhận nằm NGOÀI bảng giá Tracking. Đây là một trạng "
        "thái hợp lệ, không phải việc phải sửa: tiền của nó vẫn nằm đủ trong "
        "tổng kỳ, chỉ không thuộc một hãng hay nhóm hàng nào của danh mục."
    ),
    STATE_METADATA_ABSENT: (
        "Dòng đã khớp mã Tracking, nhưng danh mục Tracking chưa xếp hãng/nhóm "
        "hàng cho mã đó. Sửa BÊN TRACKING; lần capture danh mục kế tiếp chở "
        "giá trị mới sang mà không ai phải phân loại lại dòng."
    ),
}

TAXONOMY_SOURCE_NOTE = (
    "Hãng và nhóm hàng chỉ ĐỌC từ hợp đồng metadata của Tracking, qua một mã "
    "sản phẩm đã được xác nhận. Reports KHÔNG suy hãng hay nhóm hàng từ tên "
    "hàng trên sổ kế toán, từ mã máy, hay từ bất kỳ phép so chuỗi nào — một "
    "nhãn đoán ra sẽ cộng tiền thật vào sai nhóm mà không ai nhìn thấy."
)

CATEGORY_TAXONOMY_NOTE = (
    "Nhóm hàng do Tracking CHỌN từ một từ điển đóng (DEC-205, DEC-206): "
    "Máy lạnh / Điều hòa / Điều hoà → Điều hoà; TV / Ti vi / Tivi → Tivi; "
    "Máy giặt sấy → Máy giặt. Reports không giữ từ điển ấy và không sửa được "
    "nó — sửa ngành hàng xảy ra bên Tracking."
)

ORDERS_COLUMN_NOTE = (
    "Cột \"Số đơn\" đếm số BH KHÁC NHAU có mặt trong hàng. Một đơn chứa hàng "
    "của hai hàng khác nhau được đếm ở CẢ HAI, nên cột này KHÔNG cộng lại "
    "thành tổng số đơn của kỳ — và vì vậy nó cố ý không tham gia phép đối soát."
)


@dataclass(frozen=True)
class LineMetadata:
    """Metadata HIỆU LỰC của một dòng, cùng lý do khi nó chưa có.

    `state` là một trong sáu hằng `STATE_*`. Nó KHÔNG phải một trạng thái nhận
    diện thứ hai bên cạnh `line_identity.IdentityState`: năm giá trị đầu được
    DẪN từ chính `IdentityState` (cộng thêm mã lý do stale target đã lưu), và
    giá trị thứ sáu nói về sự vắng mặt của metadata chứ không về nhận diện.
    """

    state: str
    #: Mã Tracking của dòng, `None` khi chưa khớp hoặc mapping không có mã.
    tracking_code: Optional[str]
    model_label: Optional[str]
    brand: Optional[str]
    category_label: Optional[str]

    @property
    def matched(self) -> bool:
        return self.state == STATE_MATCHED


def _identity_state_name(state: line_identity.IdentityState,
                         pending_reasons: Iterable[str]) -> str:
    """Trạng thái R6 dẫn từ `IdentityState` + mã lý do stale target.

    Thứ tự kiểm là hợp đồng, và nó THEO SAU thứ tự của `line_identity.state_of`
    thay vì phát minh lại: `CONFLICT` và `OUT_OF_CATALOG` là hai phân loại
    riêng của R2, `unresolved` là trạng thái R2, và stale target chỉ được hỏi
    tới khi ba cái trước đã nói "không".
    """
    if state.conflict:
        return STATE_CONFLICT
    if state.out_of_catalog:
        return STATE_OUT_OF_CATALOG
    if state.unresolved:
        return STATE_UNRESOLVED
    if set(pending_reasons or ()) & STALE_TARGET_REASONS:
        return STATE_STALE_TARGET
    return STATE_MATCHED


def metadata_of(
    detail: dict, *, decisions: line_identity.Decisions,
    identities: dict, display: dict,
) -> LineMetadata:
    """Metadata của MỘT dòng — ĐỌC, không suy luận.

    `identities` là `{raw_identity_key: CanonicalProductIdentity}` của
    `identity_gateway.confirmed_identities`; `display` là bản chiếu
    `catalog_display.read()`. Cả hai đã được đọc MỘT LẦN cho cả trang bởi tầng
    gọi — tra lại ở từng dòng sẽ mở đúng một file cho mỗi dòng của kỳ.
    """
    state = line_identity.state_of(detail, decisions=decisions)
    line = detail["line"]
    name = _identity_state_name(state, line.pending_reasons)
    if name != STATE_MATCHED:
        return LineMetadata(state=name, tracking_code=None, model_label=None,
                            brand=None, category_label=None)
    identity = identities.get(state.identity_key)
    code = getattr(identity, "source_product_code", None) or None
    row = (display.get(code) or {}) if code else {}
    model_label = row.get("model_label")
    brand = row.get("brand")
    category_label = row.get("category_label")
    if code is None or (model_label is None and brand is None
                        and category_label is None):
        # Đã khớp nhưng KHÔNG có gì để nói: hoặc mapping không mang mã, hoặc
        # bản chiếu hiển thị chưa có dòng nào cho mã đó (chưa capture lần nào
        # sau khi Tracking xếp ngành hàng — `AR-R5.1-04`, trạng thái ĐÚNG chứ
        # không phải lỗi).
        return LineMetadata(state=STATE_METADATA_ABSENT, tracking_code=code,
                            model_label=None, brand=None, category_label=None)
    return LineMetadata(state=STATE_MATCHED, tracking_code=code,
                        model_label=model_label, brand=brand,
                        category_label=category_label)


def metadata_for(
    details: Iterable[dict], *, decisions: line_identity.Decisions,
    identities: dict, display: dict,
) -> list[LineMetadata]:
    """`LineMetadata` của TỪNG dòng, cùng thứ tự với `details`.

    Một dãy song song chứ không một dict theo khoá dòng — cùng hợp đồng mà
    `brand_identity.buckets_for` đã dựng, và cùng lý do: một dict mở ra khả
    năng thiếu khoá, và thiếu khoá ở đây nghĩa là một dòng biến mất khỏi mọi
    bucket trong khi hàng tổng vẫn trông hợp lệ.
    """
    return [metadata_of(detail, decisions=decisions, identities=identities,
                        display=display) for detail in details]


def _undecided_bucket(state: str) -> GroupBucket:
    return GroupBucket(
        key=f"__{state}__", label=UNDECIDED_LABELS[state],
        kind=KIND_UNDECIDED, reason=UNDECIDED_REASONS[state],
        sort_hint=UNDECIDED_ORDER.index(state))


def product_bucket(detail: dict, metadata: LineMetadata) -> GroupBucket:
    """Bucket MẶT HÀNG của một dòng — khoá LUÔN là `product_key`.

    Khoá không phụ thuộc metadata: `product_key` là khoá phân tích duy nhất và
    nó tồn tại cho mọi dòng, nên bảng mặt hàng không bao giờ dồn nhiều mặt hàng
    khác nhau vào một ô "chưa xác định" và làm mất chiều mặt hàng.

    Nhãn thì phụ thuộc metadata, và `kind` NÓI RA điều đó: một hàng chưa khớp
    mã vẫn hiện tên trên sổ kế toán để đối chiếu được, nhưng nó tự khai là
    chưa xác định và mang đúng lý do của mình. Đây KHÔNG phải suy metadata từ
    tên thô — tên thô không quyết định bucket nào, không quyết định hãng, không
    quyết định nhóm hàng; nó chỉ là chữ hiện trên một hàng đã tự khai.
    """
    key = detail["product_key"]
    raw = detail.get("product_raw") or key
    if metadata.matched:
        # R5 §5 — fallback về chính mã Tracking: một mã đối chiếu được vẫn hơn
        # một ô trống. Tên trên sổ kế toán là bậc CUỐI, và chỉ khi cả hai bậc
        # trên đều vắng.
        label = metadata.model_label or metadata.tracking_code or raw
        return GroupBucket(key=key, label=label, kind=KIND_KNOWN)
    return GroupBucket(
        key=key, label=raw, kind=KIND_UNDECIDED,
        reason=UNDECIDED_REASONS[metadata.state],
        sort_hint=UNDECIDED_ORDER.index(metadata.state))


def brand_bucket(metadata: LineMetadata) -> GroupBucket:
    """Bucket HÃNG của một dòng."""
    if metadata.matched and metadata.brand:
        return GroupBucket(key=metadata.brand, label=metadata.brand,
                           kind=KIND_KNOWN)
    state = (STATE_METADATA_ABSENT if metadata.matched else metadata.state)
    return _undecided_bucket(state)


def category_bucket(metadata: LineMetadata) -> GroupBucket:
    """Bucket NHÓM HÀNG của một dòng.

    `category_label` đến từ từ điển đóng của Tracking (`DEC-205`/`DEC-206`).
    Reports KHÔNG chuẩn hoá lại chuỗi ấy và KHÔNG có nhánh nào cắt/lọc nó — nếu
    Tracking gửi sang một nhãn, nhãn đó đi thẳng lên bảng.
    """
    if metadata.matched and metadata.category_label:
        return GroupBucket(key=metadata.category_label,
                           label=metadata.category_label, kind=KIND_KNOWN)
    state = (STATE_METADATA_ABSENT if metadata.matched else metadata.state)
    return _undecided_bucket(state)


#: Ba chiều gộp của R6 §3, và chỉ ba. Tập ĐÓNG — thêm một chiều là một quyết
#: định nghiệp vụ, không phải một lần refactor.
DIMENSION_PRODUCT = "san-pham"
DIMENSION_CATEGORY = "nhom-hang"
DIMENSION_BRAND = "hang"

DIMENSIONS: tuple[tuple[str, str], ...] = (
    (DIMENSION_PRODUCT, "Mặt hàng"),
    (DIMENSION_CATEGORY, "Nhóm hàng"),
    (DIMENSION_BRAND, "Hãng"),
)

DIMENSION_KEYS: frozenset = frozenset(key for key, _label in DIMENSIONS)


def parse_dimension(raw: Optional[str]) -> str:
    """Chiều gộp đang chọn. Giá trị lạ rơi về `Mặt hàng`, không báo lỗi.

    Cùng kỷ luật mà `revenue_timeline.parse_granularity` đã freeze: một tham số
    URL gõ sai không đáng làm hỏng cả trang, nhưng nó cũng không được âm thầm
    thành một chiều KHÁC cái người dùng gõ — nút của chiều mặc định sẽ sáng lên
    như trạng thái thật.
    """
    value = (raw or "").strip().lower()
    return value if value in DIMENSION_KEYS else DIMENSION_PRODUCT


def dimension_label(dimension: str) -> str:
    return dict(DIMENSIONS).get(dimension, dict(DIMENSIONS)[DIMENSION_PRODUCT])


def buckets_for(
    details: Iterable[dict], metadata: list[LineMetadata], *, dimension: str,
) -> list[GroupBucket]:
    """Bucket của TỪNG dòng theo MỘT chiều gộp, cùng thứ tự với `details`."""
    details = list(details)
    if len(details) != len(metadata):
        raise ValueError(
            f"details ({len(details)}) và metadata ({len(metadata)}) phải cùng "
            "độ dài — mỗi dòng đúng một metadata")
    if dimension == DIMENSION_PRODUCT:
        return [product_bucket(detail, item)
                for detail, item in zip(details, metadata)]
    if dimension == DIMENSION_CATEGORY:
        return [category_bucket(item) for item in metadata]
    if dimension == DIMENSION_BRAND:
        return [brand_bucket(item) for item in metadata]
    raise ValueError(f"chiều gộp ngoài tập đóng: {dimension!r}")


@dataclass(frozen=True)
class MetadataCoverage:
    """Bao nhiêu dòng của lát đã có metadata, và phần còn lại mắc ở đâu.

    Một ô đếm cho MỖI lý do thay vì một tỉ lệ gộp: năm lý do cần năm hành động
    khác nhau, và một phần trăm gộp xoá đúng chiều đó (`PHB-06 §10`).
    """

    matched_lines: int
    by_state: tuple[tuple[str, int], ...]

    @property
    def total_lines(self) -> int:
        return self.matched_lines + sum(count for _state, count in self.by_state)

    def count(self, state: str) -> int:
        return dict(self.by_state).get(state, 0)

    @property
    def is_complete(self) -> bool:
        """MỌI dòng của lát đều đã khớp mã Tracking.

        Lát RỖNG ⟹ `False`: không có dòng nào thì cũng không có bằng chứng nào
        cho một lời khẳng định "đã đủ" — cùng kỷ luật fail-closed của
        `DEC-143` §1 và `brand_identity.BrandCoverage.is_complete`.
        """
        return self.total_lines > 0 and self.matched_lines == self.total_lines


def coverage(metadata: Iterable[LineMetadata]) -> MetadataCoverage:
    counts: dict[str, int] = {}
    matched = 0
    for item in metadata:
        if item.matched:
            matched += 1
        else:
            counts[item.state] = counts.get(item.state, 0) + 1
    return MetadataCoverage(
        matched_lines=matched,
        by_state=tuple((state, counts[state]) for state in UNDECIDED_ORDER
                       if state in counts))


__all__ = [
    "CATEGORY_TAXONOMY_NOTE", "DIMENSIONS", "DIMENSION_BRAND",
    "DIMENSION_CATEGORY", "DIMENSION_KEYS", "DIMENSION_PRODUCT",
    "LineMetadata", "MetadataCoverage", "ORDERS_COLUMN_NOTE",
    "STALE_TARGET_REASONS", "STATE_CONFLICT", "STATE_MATCHED",
    "STATE_METADATA_ABSENT", "STATE_OUT_OF_CATALOG", "STATE_STALE_TARGET",
    "STATE_UNRESOLVED", "TAXONOMY_SOURCE_NOTE", "UNDECIDED_LABELS",
    "UNDECIDED_ORDER", "UNDECIDED_REASONS", "brand_bucket", "buckets_for",
    "category_bucket", "coverage", "dimension_label", "metadata_for",
    "metadata_of", "parse_dimension", "product_bucket",
]
