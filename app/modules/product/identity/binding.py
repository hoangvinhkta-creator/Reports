"""E-L `ResolutionBinding` và replay — data contract §10.1.

Một report đã phát hành phải chạy lại ra **kết quả giống hệt**, bất kể store,
catalog hay giá đã đổi thế nào sau đó (`INV-56`). Cơ chế là ghim: report giữ
lại số hiệu của đúng bốn thứ mà kết quả của nó phụ thuộc vào.

```text
pp_version_id           version Public Purchase (identity + price, D-01)
tracking_capture_id     capture Tracking
mapping_store_revision  §10.2 — chiếu log tới đúng event đó
registry_revision       nhánh pre-cutover
```

## Ghim CẢ BỐN, không ghim từng phần

`INV-55`. Ghim giá mà không ghim catalog là đúng lỗ hổng replay mà `HB-154-02`
đã nêu; ghim mapping mà không ghim registry làm một report pre-cutover lệch
mỗi khi ai đó sửa một entry lịch sử. `ResolutionBinding.__post_init__` từ chối
một binding thiếu bất kỳ thành phần nào — nên "ghim từng phần" không phải một
trạng thái biểu diễn được.

**Ghi chú divergence (`HB-105D-F2-01`, vẫn OPEN).** Data contract §3.3 câu 8
gọi `ResolutionBinding` là "bộ ba". Schema `E-L` (§10.1) và `INV-55` nói "CẢ
BỐN". `V4.1` §11 (ARTIFACT INTERNAL PRECEDENCE) giải xung đột này một cách cơ
học: trong cùng một artifact, schema thắng văn xuôi giải thích. Bốn trường là
đúng, và `CHECK-105D-21` Phần C assert đúng bốn. Phiên implementation không sửa
data contract; divergence được báo cáo, không tự dàn xếp.

## Thiếu binding là LỖI CỨNG

`INV-57`. Không fallback "mới nhất", không trả Pending. Lý do: một report
replay bằng dữ liệu mới nhất trông vẫn *ra số*, và không ai phát hiện được nó
đã trả lời một câu hỏi khác với câu hỏi đã hỏi. Một lỗi ồn ào tốn một phút;
một con số sai im lặng tốn một kỳ lương.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Sequence

from app.modules.product.identity.public_purchase import (
    PublicPurchaseSourceRepository,
)
from app.modules.product.identity.registry import HistoricalConfirmedRegistry
from app.modules.product.identity.resolver import (
    ProductIdentityResolver,
    SalesRowRef,
)
from app.modules.product.identity.service import BatchResolution, resolve_batch
from app.modules.product.identity.store import JsonlProductIdentityStore
from app.modules.product.identity.tracking_catalog import (
    TrackingSnapshotRepository,
)


class IncompleteBindingError(RuntimeError):
    """`INV-55`/`INV-57` — binding thiếu thành phần. LỖI CỨNG."""


@dataclass(frozen=True)
class ResolutionBinding:
    """E-L. Bốn revision + siêu dữ liệu ghim."""

    binding_id: str
    report_run_id: str
    pp_version_id: str
    tracking_capture_id: str
    mapping_store_revision: int
    registry_revision: int
    bound_at: datetime
    bound_by: str

    def __post_init__(self) -> None:
        missing = [
            name
            for name in (
                "pp_version_id",
                "tracking_capture_id",
                "mapping_store_revision",
                "registry_revision",
            )
            if getattr(self, name) is None or getattr(self, name) == ""
        ]
        if missing:
            raise IncompleteBindingError(
                f"INV-55: ResolutionBinding thiếu {missing}; ghim CẢ BỐN hoặc "
                "không ghim — KHÔNG fallback 'mới nhất', KHÔNG Pending (INV-57)"
            )


class ReportReplay:
    """Chạy lại một report theo đúng bộ binding của nó (`INV-56`).

    Toàn bộ đầu vào của `resolve_batch` được lấy lại **theo binding**, không
    theo trạng thái hiện tại: catalog theo `capture_id`, nguồn PP theo
    `version_id`, store theo `mapping_store_revision`, registry theo
    `registry_revision`. Không có tham số nào ở đây đọc "mới nhất".
    """

    def __init__(
        self,
        *,
        store: JsonlProductIdentityStore,
        registry: HistoricalConfirmedRegistry,
        tracking_repository: TrackingSnapshotRepository,
        pp_repository: PublicPurchaseSourceRepository,
    ) -> None:
        self.store = store
        self.registry = registry
        self.tracking_repository = tracking_repository
        self.pp_repository = pp_repository

    def replay(
        self, rows: Sequence[SalesRowRef], binding: ResolutionBinding
    ) -> BatchResolution:
        snapshot = self.tracking_repository.get(binding.tracking_capture_id)
        pp_version = self.pp_repository.get(binding.pp_version_id)
        view = self.store.read_at_revision(binding.mapping_store_revision)
        registry_view = self.registry.read_at_revision(binding.registry_revision)

        return resolve_batch(
            rows,
            registry=registry_view,
            resolver_factory=lambda: ProductIdentityResolver(
                tracking_snapshot=snapshot,
                pp_version=pp_version,
                store_view=view,
                now=binding.bound_at,
            ),
        )


def replay_signature(result: BatchResolution) -> tuple:
    """Chữ ký so sánh được của một lần chạy — dùng cho assertion "giống hệt".

    So khớp ĐẦY ĐỦ chứ không chỉ một trường (`CHECK-105D-21` fixture 5): với
    mỗi identity, cả outcome, phương thức, và toàn bộ tập candidate theo đúng
    thứ tự. Một replay đổi thứ tự candidate cũng là một replay đã đổi.
    """
    return (
        tuple(
            (
                row.order_id,
                row.raw_identity_key,
                type(outcome).__name__,
                getattr(outcome, "price", None),
                getattr(getattr(outcome, "identity", None), "namespace", None),
                getattr(getattr(outcome, "identity", None), "source_product_code", None),
                getattr(outcome, "reason_code", None),
            )
            for row, outcome in result.historical
        ),
        tuple(
            (
                resolution.identity.raw_identity_key,
                type(resolution.outcome).__name__,
                resolution.resolution_method,
                getattr(
                    getattr(resolution.outcome, "identity", None), "namespace", None
                ),
                getattr(
                    getattr(resolution.outcome, "identity", None),
                    "source_product_code",
                    None,
                ),
                getattr(resolution.outcome, "reason_code", None),
                tuple(
                    (c.candidate_id, c.rank, c.method.value, c.note)
                    for c in resolution.candidates
                ),
            )
            for resolution in result.resolutions
        ),
    )


def require_binding(binding: Optional[ResolutionBinding]) -> ResolutionBinding:
    """Cổng cho caller: không có binding thì KHÔNG chạy, không đoán."""
    if binding is None:
        raise IncompleteBindingError(
            "INV-57: report không có ResolutionBinding; KHÔNG fallback sang "
            "'mới nhất', KHÔNG trả Pending"
        )
    return binding
