"""Rà soát drift danh mục Tracking — `INV-13`…`INV-16`, `CHECK-105D-10` Phần B.

Một capture Tracking mới có thể khác capture cũ theo bốn kiểu, và ba trong bốn
kiểu đó KHÔNG được đụng tới một mapping đã confirm:

```text
đổi tên (name/alt đổi, code giữ)   → mapping VẪN hợp lệ. Tên không phải
                                     identity (INV-13/INV-21).
biến mất khỏi board                → mapping lịch sử KHÔNG bị vô hiệu, KHÔNG
                                     bị xoá, KHÔNG tự chuyển Pending (INV-14a).
gộp mã qua alias.map               → resolver KHÔNG tự chuyển sang mã chính;
                                     nó ĐỀ XUẤT và chờ người (INV-16).
capture FAILED                     → lỗi cứng, không phải "không tồn tại"
                                     (INV-12).
```

## Vì sao module này chỉ ĐỀ XUẤT chứ không ghi

`detect()` là một hàm thuần trên `(view, snapshot)`. Nó không nhận store, nên
nó không thể ghi — đó là cách rẻ nhất để bảo đảm rằng việc rà soát drift không
bao giờ tự động hoá một quyết định.

Lý do nghiệp vụ nằm ở `D-05`: `inv.map`/`alias.map` là bảng do **người của
Tracking** duyệt. Chúng là evidence rất mạnh, nhưng phê duyệt của Tracking
không phải phê duyệt của Reports. Một mã gộp ở Tracking có thể đúng cho kho của
họ và sai cho giá vốn của mình. Nên kết quả là một `StaleProposal` với mã chính
ở candidate #1, và một người phải phát `MarkStale`.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.modules.product.identity.mapping import (
    MappingStatus,
    ProductIdentityMapping,
)
from app.modules.product.identity.identity import Namespace
from app.modules.product.identity.store import StoreView
from app.modules.product.identity.tracking_catalog import TrackingCatalogSnapshot


@dataclass(frozen=True)
class StaleProposal:
    """Một đề xuất — KHÔNG phải một thay đổi đã thực hiện."""

    mapping: ProductIdentityMapping
    reason: str
    proposed_primary_code: str = ""

    @property
    def candidate_1(self) -> str:
        """Mã chính được đề xuất làm candidate #1 (`INV-16`/`D-05`)."""
        return self.proposed_primary_code


def detect(
    view: StoreView, snapshot: TrackingCatalogSnapshot
) -> tuple[StaleProposal, ...]:
    """Rà soát mọi mapping `TRACKING` đang active trên một capture mới.

    Trả về đề xuất theo thứ tự `raw_identity_key` để kết quả ổn định giữa các
    lần chạy (`INV-64`).
    """
    snapshot.require_complete()
    alias_map = snapshot.alias_map()
    proposals: list[StaleProposal] = []

    for mapping in sorted(
        view.alias_index().values(), key=lambda m: m.raw_identity_key
    ):
        if (
            mapping.status is not MappingStatus.CONFIRMED
            or mapping.namespace is not Namespace.TRACKING
        ):
            continue

        code = mapping.source_product_code
        primary = alias_map.get(code)
        if primary and primary != code:
            proposals.append(
                StaleProposal(
                    mapping=mapping,
                    reason=(
                        f"alias.map của Tracking gộp {code!r} vào {primary!r}; "
                        "cần một quyết định của Reports (INV-16, D-05)"
                    ),
                    proposed_primary_code=primary,
                )
            )

    return tuple(proposals)


def mapping_still_valid(
    mapping: ProductIdentityMapping, snapshot: TrackingCatalogSnapshot
) -> bool:
    """`INV-13`/`INV-14a` — một mapping đã confirm còn hợp lệ hay không.

    Trả `True` cả khi sản phẩm đã đổi tên **và** cả khi nó đã biến mất khỏi
    board hiện tại. Đó không phải sự khoan dung: mapping ghi lại một quyết định
    đã có của con người tại một thời điểm, và catalog HÔM NAY không có thẩm
    quyền viết lại lịch sử (`INV-15`). Chỉ correction có authority tường minh
    (§13) mới đổi được nó.
    """
    if mapping.namespace is not Namespace.TRACKING:
        return True
    return mapping.status is MappingStatus.CONFIRMED
