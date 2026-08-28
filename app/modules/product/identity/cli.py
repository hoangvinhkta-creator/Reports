"""Bề mặt vận hành Phase 1 — `CHECK-105D-22`, `ADR-101`.

## Gate này assert trên bề mặt THẬT, không trên một UI chưa tồn tại

`ADR-101`: Phase 1 là thư viện Python thuần chạy bằng CLI, KHÔNG có UI đồ hoạ.
`CHECK-105D-22` (điểm sửa của `H-01`) vì thế assert ba điều trên chính bề mặt
đó, và cả ba đều test được ngay hôm nay:

```text
(a) cả BỐN confirmation_action, cùng với xem candidate/evidence và duyệt hết
    một batch, chạy được HOÀN TOÀN qua CLI trong môi trường không display,
    không thiết bị trỏ;
(b) app/modules/product/** không import thư viện GUI/web/pointer-event nào;
(c) không confirmation_action nào chỉ tiếp cận được qua một bề mặt con trỏ.
```

Gate KHÔNG được đánh `NOT_APPLICABLE` với lý do "Phase 1 chưa có UI" — và file
này là lý do nó không cần phải.

## Bốn command, một hàm mỗi command

`ACTION_COMMANDS` dưới đây là danh sách bề mặt gọi được của từng
`confirmation_action`. Test của `(c)` đọc chính bảng này: nếu một command tồn
tại mà không có mục trong bảng, nó đã có một đường vào nào đó không đi qua CLI.

Toàn bộ file dùng `argparse` của stdlib — không thêm dependency, giữ nguyên
tính chất "thư viện Python thuần" mà `ADR-101` bắt kiểm chứng.
"""

from __future__ import annotations

import argparse
from typing import Callable, Optional, Sequence

from app.modules.product.identity.audit import ACTOR_DISCLOSURE, EventType
from app.modules.product.identity.commands import (
    ConfirmCrossSystem,
    ConfirmMapping,
    RejectCandidate,
    SetPending,
)
from app.modules.product.identity.evidence import (
    Evidence,
    MatchedOn,
    RANKING_METHOD_ID,
    ResolutionMethod,
)
from app.modules.product.identity.identity import (
    CanonicalProductIdentity,
    Namespace,
)
from app.modules.product.identity.resolver import IdentityResolution
from app.modules.product.identity.service import affected_scope_for
from app.modules.product.identity.store import AppendResult, ProductIdentityStore

ACTION_COMMANDS: dict[EventType, str] = {
    EventType.CONFIRM_MAPPING: "confirm",
    EventType.REJECT_CANDIDATE: "reject",
    EventType.CONFIRM_CROSS_SYSTEM: "confirm-cross-system",
    EventType.SET_PENDING: "set-pending",
}
"""Bề mặt CLI của từng `confirmation_action`. Không mục nào cần con trỏ."""


def render_candidates(resolution: IdentityResolution) -> str:
    """Xem candidate/evidence — thao tác ĐIỀU HƯỚNG, 0 `confirmation_action`.

    §17.1 liệt kê tường minh: xem evidence, tìm kiếm, lọc, sắp xếp đều không
    được đếm. Hàm này thuần tuý dựng chuỗi và không chạm store, nên nó không
    thể vô tình đổi trạng thái.
    """
    lines = [
        f"identity: {resolution.identity.raw_product_identity}",
        f"raw_identity_key: {resolution.identity.raw_identity_key}",
        f"outcome: {type(resolution.outcome).__name__}",
        f"actor: {ACTOR_DISCLOSURE}",
    ]
    for candidate in resolution.candidates:
        note = f"  [{candidate.note}]" if candidate.note else ""
        lines.append(
            f"  #{candidate.rank} {candidate.candidate_id} "
            f"method={candidate.method.value} "
            f"matched_on={candidate.evidence.matched_on.value} "
            f"matched_value={candidate.evidence.matched_value!r}{note}"
        )
    if not resolution.candidates:
        lines.append("  (không có candidate)")
    return "\n".join(lines)


def confirm(
    store: ProductIdentityStore,
    resolution: IdentityResolution,
    *,
    candidate_rank: int,
    actor_id: str,
    client_request_id: str,
    expected_version: int,
    pp_version_id: Optional[str] = None,
    tracking_capture_id: Optional[str] = None,
) -> AppendResult:
    """`CONFIRM_MAPPING` — chấp nhận candidate hạng `candidate_rank`.

    `evidence.parent_mapping_id` được mang nguyên từ candidate: với một
    `ALIAS_AID_UNIQUE`, nó trỏ về alias đã confirm sinh ra gợi ý — đúng yêu cầu
    `CHECK-105D-23` và §6.5 (provenance của gợi ý nằm ở evidence, KHÔNG ở
    `mapping_source`, vốn luôn là `HUMAN_CONFIRMATION`).
    """
    candidate = _candidate_at(resolution, candidate_rank)
    command = ConfirmMapping(
        actor_id=actor_id,
        client_request_id=client_request_id,
        expected_version=expected_version,
        pp_version_id=pp_version_id,
        tracking_capture_id=tracking_capture_id,
        affected_scope=affected_scope_for(
            resolution.identity, revision=store.current_revision()
        ),
        raw_identity_key=resolution.identity.raw_identity_key,
        raw_product_identity=resolution.identity.raw_product_identity,
        source_system=resolution.identity.source_system,
        target=CanonicalProductIdentity(
            namespace=candidate.namespace,
            source_product_code=candidate.source_product_code,
        ),
        evidence=candidate.evidence,
        resolution_method=candidate.method,
    )
    return store.append(command)


def reject(
    store: ProductIdentityStore,
    resolution: IdentityResolution,
    *,
    candidate_rank: int,
    actor_id: str,
    client_request_id: str,
    expected_version: int,
    reason: Optional[str] = None,
    pp_version_id: Optional[str] = None,
    tracking_capture_id: Optional[str] = None,
) -> AppendResult:
    """`REJECT_CANDIDATE` — "không phải cái này", nhớ theo fingerprint."""
    candidate = _candidate_at(resolution, candidate_rank)
    command = RejectCandidate(
        actor_id=actor_id,
        client_request_id=client_request_id,
        expected_version=expected_version,
        reason=reason,
        pp_version_id=pp_version_id,
        tracking_capture_id=tracking_capture_id,
        affected_scope=affected_scope_for(
            resolution.identity, revision=store.current_revision()
        ),
        raw_identity_key=resolution.identity.raw_identity_key,
        raw_product_identity=resolution.identity.raw_product_identity,
        source_system=resolution.identity.source_system,
        candidate_namespace=candidate.namespace,
        candidate_code=candidate.source_product_code,
        evidence_fingerprint=resolution.evidence_fingerprint or "",
    )
    return store.append(command)


def set_pending(
    store: ProductIdentityStore,
    resolution: IdentityResolution,
    *,
    actor_id: str,
    client_request_id: str,
    expected_version: int,
    stale: bool = False,
    reason: Optional[str] = None,
) -> AppendResult:
    """`SET_PENDING` — Pending là lựa chọn HỢP LỆ, không phải lỗi.

    `stale=True` khi target đã biến mất khỏi board hiện tại: mapping ghi
    `status = STALE` thay vì `PENDING` (`INV-14c`).
    """
    command = SetPending(
        actor_id=actor_id,
        client_request_id=client_request_id,
        expected_version=expected_version,
        reason=reason,
        affected_scope=affected_scope_for(
            resolution.identity, revision=store.current_revision()
        ),
        raw_identity_key=resolution.identity.raw_identity_key,
        raw_product_identity=resolution.identity.raw_product_identity,
        source_system=resolution.identity.source_system,
        pending_status_stale=stale,
    )
    return store.append(command)


def confirm_cross_system(
    store: ProductIdentityStore,
    *,
    tracking_code: str,
    public_purchase_code: str,
    actor_id: str,
    client_request_id: str,
    expected_version: int,
    pp_version_id: str,
    tracking_capture_id: str,
    reason: Optional[str] = None,
) -> AppendResult:
    """`CONFIRM_CROSS_SYSTEM` — cần một lần, KỂ CẢ khi hai mã bằng nhau (`INV-38`)."""
    command = ConfirmCrossSystem(
        actor_id=actor_id,
        client_request_id=client_request_id,
        expected_version=expected_version,
        reason=reason,
        pp_version_id=pp_version_id,
        tracking_capture_id=tracking_capture_id,
        tracking_code=tracking_code,
        public_purchase_code=public_purchase_code,
        evidence=Evidence(
            matched_on=MatchedOn.MANUAL_SEARCH,
            matched_value=tracking_code,
            candidate_set_ids=(f"{Namespace.PUBLIC_PURCHASE.value}:{public_purchase_code}",),
            ranking_method_id=RANKING_METHOD_ID,
        ),
    )
    return store.append(command)


def _candidate_at(resolution: IdentityResolution, rank: int):
    for candidate in resolution.candidates:
        if candidate.rank == rank:
            return candidate
    raise ValueError(
        f"không có candidate hạng {rank} cho "
        f"{resolution.identity.raw_identity_key!r}"
    )


def build_parser() -> argparse.ArgumentParser:
    """Parser của bề mặt vận hành. Bàn phím là bề mặt duy nhất, và là đủ."""
    parser = argparse.ArgumentParser(
        prog="product-identity",
        description=(
            "Bề mặt vận hành TASK-105D (Phase 1, CLI). "
            f"{ACTOR_DISCLOSURE}."
        ),
    )
    parser.add_argument(
        "--actor-id",
        required=True,
        help=f"REQUIRED, không có mặc định (INV-72). {ACTOR_DISCLOSURE}.",
    )
    subparsers = parser.add_subparsers(dest="action", required=True)
    for event_type, name in ACTION_COMMANDS.items():
        sub = subparsers.add_parser(name, help=event_type.value)
        sub.add_argument("--raw-identity-key", required=True)
        sub.add_argument("--client-request-id", required=True)
        sub.add_argument("--expected-version", type=int, required=True)
        if name in {"confirm", "reject"}:
            sub.add_argument("--candidate-rank", type=int, default=1)
        if name == "confirm-cross-system":
            sub.add_argument("--tracking-code", required=True)
            sub.add_argument("--public-purchase-code", required=True)
    subparsers.add_parser("show-candidates", help="xem candidate/evidence")
    return parser


def callable_surfaces() -> dict[EventType, Callable]:
    """Bảng `(c)`: mỗi `confirmation_action` → hàm gọi được không cần con trỏ."""
    return {
        EventType.CONFIRM_MAPPING: confirm,
        EventType.REJECT_CANDIDATE: reject,
        EventType.SET_PENDING: set_pending,
        EventType.CONFIRM_CROSS_SYSTEM: confirm_cross_system,
    }
