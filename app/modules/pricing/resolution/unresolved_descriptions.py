"""PHB-01 §4A — gộp các CÂU MÔ TẢ hàng bán chưa được định danh.

## Vì sao gộp theo khoá `inv.map`, không theo câu chữ nguyên văn

Đơn vị công việc thật của Owner KHÔNG phải một dòng đơn hàng, cũng không phải
một cách viết. Một quyết định phân loại bên Tracking được ghi tại
`/inv/map/<khoá>` với `khoá = "N_" + normCode(câu mô tả)[:80]`
(`app/modules/product/identity/tracking_inv_map.py`). Hai câu mô tả khác nhau
mà cùng khoá là MỘT quyết định duy nhất — phân loại một câu là phân loại cả
hai. Gộp theo khoá nên đếm đúng số lần Owner phải bấm; gộp theo câu nguyên văn
sẽ thổi phồng khối lượng bằng những dòng mà một thao tác đã xử lý xong.

Đây KHÔNG phải fuzzy matching hay suy luận identity: khoá được tính bằng đúng
`normCode()` mà Tracking dùng để GHI, không so sánh gần đúng, không rút mã,
không xếp hạng. Cùng khoá = cùng ô dữ liệu bên Tracking, đúng theo định nghĩa.

## Cái gì được xuất và cái gì KHÔNG

Chỉ Pending do IDENTITY (`IDENTITY_UNRESOLVED`). Cố ý loại:

- `IDENTITY_SOURCES_UNAVAILABLE` — nguồn authority CHƯA NỐI/HỎNG. Đưa nó vào
  danh sách "chờ phân loại" là biến một sự cố hạ tầng thành một việc thủ công
  cho Owner làm — đúng cái D1 cấm ("failure MUST NOT masquerade as ordinary
  unresolved identity state").
- `TRACKING_INV_MAP_EXPLICIT_IGNORE` — `inv.map[khoá] == "-"`, tức MỘT NGƯỜI
  của Tracking đã xem và kết luận đây không phải sản phẩm cần map. Đã có
  quyết định thì không hỏi lại; xuất tiếp là bắt Owner trả lời mãi một câu
  hỏi họ đã trả lời rồi.
- `IDENTITY_REQUIRES_CONFIRMATION` — AMBIGUOUS, thuộc luồng xác nhận
  candidate của Reports, không phải "chưa ai phân loại". Nó không đi qua
  đường description-only intake nên không nằm trong bản xuất này.

Mọi lý do Pending identity còn lại (chưa ai xem, hoặc mapping trỏ tới một mã
đã biến mất khỏi board) đều CẦN một quyết định phân loại của Owner, nên đều
được xuất, kèm nguyên văn `reason_code` để người đọc biết vì sao.

## Không có analytics subsystem nào ở đây

Số dòng/số đơn/doanh thu đều lấy từ dữ liệu ĐÃ tính của chính lần chạy này
(bản ghi giá + dòng đã đối chiếu 1-1 với workbook nguồn). Không truy vấn thêm,
không nguồn thứ hai, không cache.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable, Optional

from app.modules.pricing.resolution.composition import (
    PriceResolutionRecord,
    PriceResolutionReason,
)
from app.modules.product.identity.identity import PendingReason
from app.modules.product.identity.tracking_inv_map import inv_map_key

__all__ = [
    "ALREADY_DECIDED_PENDING_REASONS",
    "UnresolvedDescriptionGroup",
    "aggregate_unresolved_descriptions",
    "is_unresolved_identity_record",
]


ALREADY_DECIDED_PENDING_REASONS: frozenset[PendingReason] = frozenset(
    {PendingReason.TRACKING_INV_MAP_EXPLICIT_IGNORE}
)
"""Lý do Pending mà MỘT NGƯỜI đã quyết định rồi — không hỏi lại (`§ Cái gì`)."""


@dataclass(frozen=True)
class UnresolvedDescriptionGroup:
    """Một câu mô tả (một khoá `inv.map`) đang chờ Owner phân loại.

    `raw_description` là cách viết ĐẠI DIỆN, chọn xác định (xem
    `aggregate_unresolved_descriptions`); `description_variants` cho biết có
    bao nhiêu cách viết khác nhau cùng rơi vào khoá này, để con số 1 dòng
    không che mất việc file nguồn viết nó bằng nhiều kiểu.

    `revenue_vnd = None` nghĩa là KHÔNG dòng nào trong nhóm có doanh thu xác
    định — khác hẳn `Decimal(0)`. Ô trống giữ nguyên nghĩa "chưa xác định",
    cùng quy ước với báo cáo Excel.
    """

    inv_map_key: str
    raw_description: str
    description_variants: int
    line_count: int
    order_count: int
    revenue_vnd: Optional[Decimal]
    pending_reasons: tuple[str, ...]


def is_unresolved_identity_record(record: PriceResolutionRecord) -> bool:
    """Bản ghi này có phải một câu mô tả CHỜ PHÂN LOẠI không (`§ Cái gì`)?

    Đường DUY NHẤT trong repo để hỏi câu này — không có nơi thứ hai để một lý
    do lọt vào hay rơi ra khỏi bản xuất.
    """
    if record.reason is not PriceResolutionReason.IDENTITY_UNRESOLVED:
        return False
    if record.identity_pending_reason in ALREADY_DECIDED_PENDING_REASONS:
        return False
    return bool((record.raw_product_identity or "").strip())


def aggregate_unresolved_descriptions(
    entries: Iterable[tuple[PriceResolutionRecord, Optional[Decimal]]],
) -> tuple[UnresolvedDescriptionGroup, ...]:
    """Gộp `(bản ghi giá, doanh thu của dòng)` thành một nhóm cho mỗi khoá.

    Doanh thu đi kèm THEO THAM SỐ chứ không đọc từ `record`: `PriceResolution
    Record` là bản ghi một quyết định GIÁ NHẬP, nó không mang doanh thu, và
    dựng một đường đọc doanh thu bên trong đây sẽ tạo nguồn sự thật thứ hai
    cạnh chính con số đã in ra báo cáo. Bên gọi (trình xuất Excel) đang giữ
    sẵn cặp dòng-bản ghi đã đối chiếu 1-1 với workbook nguồn.

    Thứ tự trả về XÁC ĐỊNH và không phụ thuộc thứ tự đầu vào: nhiều dòng
    trước, rồi tới khoá tăng dần. Cùng một lần chạy trên cùng dữ liệu luôn cho
    ra cùng một file — điều kiện để bản xuất dùng được làm bằng chứng.
    """
    buckets: dict[str, dict] = {}
    for record, revenue in entries:
        if not is_unresolved_identity_record(record):
            continue
        description = (record.raw_product_identity or "").strip()
        key = inv_map_key(description)
        bucket = buckets.get(key)
        if bucket is None:
            bucket = buckets[key] = {
                "descriptions": set(),
                "orders": set(),
                "lines": 0,
                "revenue": None,
                "reasons": set(),
            }
        bucket["descriptions"].add(description)
        bucket["orders"].add(record.order_id)
        bucket["lines"] += 1
        if revenue is not None:
            bucket["revenue"] = (
                revenue if bucket["revenue"] is None else bucket["revenue"] + revenue
            )
        if record.identity_pending_reason is not None:
            bucket["reasons"].add(record.identity_pending_reason.value)

    groups = [
        UnresolvedDescriptionGroup(
            inv_map_key=key,
            # Đại diện = cách viết nhỏ nhất theo thứ tự chuỗi. Không phải "phổ
            # biến nhất": tần suất bằng nhau thì lại phải phá hoà bằng một luật
            # thứ hai, và bản xuất sẽ đổi khi dữ liệu đổi tần suất chứ không
            # đổi nội dung.
            raw_description=min(bucket["descriptions"]),
            description_variants=len(bucket["descriptions"]),
            line_count=bucket["lines"],
            order_count=len(bucket["orders"]),
            revenue_vnd=bucket["revenue"],
            pending_reasons=tuple(sorted(bucket["reasons"])),
        )
        for key, bucket in buckets.items()
    ]
    groups.sort(key=lambda group: (-group.line_count, group.inv_map_key))
    return tuple(groups)
