"""Resolver identity sản phẩm — thứ tự phân giải, ranking, Pending.

## Resolve là một phép ĐỌC THUẦN

Đây là quyết định thiết kế quan trọng nhất của file, và nó đến thẳng từ gate:
`CHECK-105D-24` khẳng định `current_revision()` **không đổi** trước/sau cả một
batch, và `CHECK-105D-04` khẳng định resolve một alias đã confirm phát sinh 0
lệnh ghi — kể cả một lần "touch" `updated_at`. Cộng lại, chúng nói rằng
resolve không được ghi gì cả.

Hệ quả: `CATALOG_EXACT_UNIQUE` auto-resolve **không persist** một mapping. Nó
trả `RESOLVED` với `mapping_source = DETERMINISTIC_CATALOG_MATCH` và không có
`mapping_id`. Mapping chỉ ra đời từ một command (§ `commands.py`). Nhờ đó
`INV-70` — import lại cùng một file thì 0 mapping mới, 0 rejection mới, 0
audit event mới — đúng theo cấu trúc chứ không nhờ một phép so sánh cẩn thận.

## Thứ tự phân giải legacy/compatibility

```text
alias memory (ALIAS_EXACT)          → auto-resolve
catalog exact, CẢ HAI namespace     → CATALOG_EXACT_UNIQUE | CROSS_NAMESPACE_TIE
                                      | MULTIPLE_EXACT
candidate discovery (aid, alias.map, similarity)  → REQUIRES_CONFIRMATION
không gì cả                          → PENDING_PRODUCT
```

Production S068 dùng một contract riêng, hẹp hơn: deterministic normalized
code → Tracking `alias.map` (nếu có) → exact `board[canonical]`. Chế độ ấy
không consult Reports mapping store, `name`, `alt` hoặc candidate ranking;
không có `board` target là Pending. Đường legacy dưới đây chỉ được giữ khi
caller nêu rõ `tracking_identity_authority=False` cho fixture tương thích.

Hai điểm dễ làm sai, ghi rõ ở đây:

1. **Catalog exact phải quét CẢ HAI namespace trước khi kết luận.** Nếu dừng
   ngay khi Tracking khớp, `CROSS_NAMESPACE_TIE` (`INV-29`) không bao giờ bị
   phát hiện — và một mã trùng chuỗi giữa hai hệ thống sẽ được auto-resolve vào
   nhầm namespace. Đây cũng là lý do một MISS ở Tracking không được thành
   Pending (`CHECK-105D-27`): resolver bắt buộc đi tiếp qua Public Purchase.

2. **`ALIAS_AID_UNIQUE` nằm ở tầng candidate, không nằm ở tầng alias memory.**
   `normalized_matching_aid` là aid tìm candidate (`INV-20`), và `OR-02` đã
   tước quyền auto-resolve của nó (`INV-28b`). Đặt nó sau catalog exact giữ cho
   `CHECK-105D-05` chiều dương không bị một alias cũ cướp mất.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Optional, Sequence

from app.modules.product.identity.evidence import (
    Evidence,
    MatchedOn,
    RANKING_METHOD_ID,
    RankedCandidate,
    ResolutionMethod,
    evidence_fingerprint,
    is_auto_resolvable,
)
from app.modules.product.identity.identity import (
    AttemptedSource,
    CanonicalProductIdentity,
    Namespace,
    PendingProduct,
    PendingReason,
    Provenance,
    RequiresConfirmation,
    Resolved,
    ResolutionOutcome,
)
from app.modules.product.identity.keys import (
    normalized_matching_aid,
    raw_identity_key,
)
from app.modules.product.identity.mapping import (
    MappingSource,
    MappingStatus,
    SOURCE_SYSTEM_REPORTS_SALES,
)
from app.modules.product.identity.public_purchase import (
    PublicPurchaseIdentityRow,
    PublicPurchaseSourceVersion,
)
from app.modules.product.identity.store import StoreView
from app.modules.product.identity.tracking_catalog import TrackingCatalogSnapshot
from app.modules.product.identity.tracking_inv_map import (
    IGNORE_VALUE as TRACKING_INV_MAP_IGNORE_VALUE,
    TrackingInvMapSnapshot,
)

_MATCHED_ON_BY_FIELD = {
    "TRACKING_CODE": MatchedOn.TRACKING_CODE,
    "TRACKING_NAME": MatchedOn.TRACKING_NAME,
    "TRACKING_ALT": MatchedOn.TRACKING_ALT,
    "PP_PRODUCT_CODE": MatchedOn.PP_PRODUCT_CODE,
    "PP_ALIAS": MatchedOn.PP_ALIAS,
}

_METHOD_RANK = {
    ResolutionMethod.ALIAS_AID_UNIQUE: 0,
    ResolutionMethod.TRACKING_ALIAS_MAP: 1,
    ResolutionMethod.TRACKING_CONFIRMED_ALIAS: 1,
    ResolutionMethod.TRACKING_CANONICAL_EXACT: 2,
    ResolutionMethod.CATALOG_EXACT_UNIQUE: 2,
    ResolutionMethod.MULTIPLE_EXACT: 2,
    ResolutionMethod.CROSS_NAMESPACE_TIE: 2,
    ResolutionMethod.SIMILARITY_RANKED: 3,
}
"""Thứ tự ưu tiên xếp hạng candidate.

Bằng chứng người đã xác nhận (`ALIAS_AID_UNIQUE`) đứng trước bằng chứng người
của Tracking đã duyệt (`TRACKING_ALIAS_MAP`), rồi tới khớp exact catalog, rồi
mới tới similarity. Đây là thứ tự *hiển thị*, không phải thẩm quyền: không mục
nào trong bảng này được auto-resolve trừ khi `is_auto_resolvable()` nói có.
"""


@dataclass(frozen=True)
class DistinctIdentity:
    """Một phần tử của tập DISTINCT `D` (§15, `INV-30`).

    Khoá là `(source_system, raw_identity_key)` — đủ source-system context để
    hai model chính xác khác nhau không bị gộp (`INV-27`).
    """

    source_system: str
    raw_identity_key: str
    raw_product_identity: str
    normalized_matching_aid: str
    order_ids: tuple[str, ...] = ()
    line_count: int = 0

    @property
    def key(self) -> tuple[str, str]:
        return (self.source_system, self.raw_identity_key)


@dataclass(frozen=True)
class IdentityResolution:
    """Kết quả resolve của MỘT distinct identity, kèm candidate đã xếp hạng."""

    identity: DistinctIdentity
    outcome: ResolutionOutcome
    candidates: tuple[RankedCandidate, ...] = ()
    resolution_method: Optional[ResolutionMethod] = None
    evidence_fingerprint: Optional[str] = None


class ProductIdentityResolver:
    """Resolver post-cutover. KHÔNG ghi gì, KHÔNG chạm giá.

    Không import price provider nào (`CHECK-105D-16`): identity là toàn bộ
    trách nhiệm của lớp này, và giá là của `TASK-105B`/`105C`, còn việc ghép
    chúng lại là của `TASK-105E`.

    ## `pp_version` là TUỲ CHỌN (DEC-165)

    Trước đây `pp_version` bắt buộc, vì kiến trúc cũ coi Public Purchase là
    một nguồn giá ĐỘC LẬP do chủ dự án cấp bằng YAML (DEC-156 D-01/OR-01).
    Quyết định nghiệp vụ của Owner đã thay giả định ấy: Public Purchase là
    giá Owner tự quản trong Tracking (`inv.cong` → `board/<mã>/tp/ton`), có
    lịch sử effective-dated, và Reports đọc nó qua Data Contract. Xem
    `docs/adr/ADR-107-public-purchase-authority-in-tracking.md`.

    Hệ quả trực tiếp: catalog PUBLIC_PURCHASE trở thành một danh mục identity
    LEGACY/ngoại vi, không còn là điều kiện cần để resolve một mã Tracking.
    Bắt `TRACKING:<mã>` phải chờ một file YAML không liên quan là ghép hai
    trách nhiệm rời nhau vào một cổng AND — và cổng ấy trả Pending cho những
    dòng mà bằng chứng Tracking đã đủ để kết luận.

    `pp_version=None` nghĩa là "danh mục PP KHÔNG được nối", chứ không phải
    "danh mục PP rỗng". Hai câu ấy khác nhau và resolver nói đúng câu thứ
    nhất: `pp_version_id` trong provenance là `None`, nên mọi bản ghi audit
    đều đọc lại được rằng lần resolve này không có catalog PP nào tham gia.
    Đây KHÔNG phải một đường vòng qua bằng chứng: không có PP nghĩa là không
    có candidate PP nào, chứ không phải một candidate PP được đoán ra.
    """

    def __init__(
        self,
        *,
        tracking_snapshot: TrackingCatalogSnapshot,
        pp_version: Optional[PublicPurchaseSourceVersion] = None,
        store_view: StoreView,
        tracking_identity_authority: bool = False,
        now: Optional[datetime] = None,
        inv_map_snapshot: Optional[TrackingInvMapSnapshot] = None,
    ) -> None:
        self.tracking = tracking_snapshot.require_complete()
        self.pp_version = pp_version
        self.view = store_view
        self._tracking_identity_authority = tracking_identity_authority
        self._now = now or datetime.now(timezone.utc)
        # `inv.map` là nguồn TUỲ CHỌN, cùng khuôn `pp_version` (DEC-165): vắng
        # mặt nghĩa là "chưa nối", KHÔNG phải "danh mục rỗng" — resolver vẫn
        # chạy đúng đường alias.map/board cũ, không Pending hàng loạt vì thiếu
        # một nguồn phụ trợ. `require_complete()` áp `INV-12` khi nó CÓ mặt:
        # một inv.map FAILED phải nổ ngay, không lặng lẽ thành Pending.
        self.inv_map = (
            inv_map_snapshot.require_complete() if inv_map_snapshot is not None else None
        )

    # ---- truy cập catalog PP khi nó có thể vắng mặt ----------------------

    @property
    def _pp_version_id(self) -> Optional[str]:
        """`None` khi catalog PP không được nối — dùng cho provenance/fingerprint."""
        return self.pp_version.version_id if self.pp_version is not None else None

    @property
    def _pp_identity_rows(self) -> tuple[PublicPurchaseIdentityRow, ...]:
        return self.pp_version.identity_rows if self.pp_version is not None else ()

    def _pp_exact_hits(self, *, raw_key: str, aid: str) -> tuple[tuple[str, str], ...]:
        if self.pp_version is None:
            return ()
        return self.pp_version.exact_match_codes(raw_key=raw_key, aid=aid)

    # ---- API -------------------------------------------------------------

    def resolve(self, identity: DistinctIdentity) -> IdentityResolution:
        if self._tracking_identity_authority:
            return self._tracking_authoritative(identity)

        alias_hit = self._alias_exact(identity)
        if alias_hit is not None:
            return alias_hit

        exact = self._catalog_exact(identity)
        if exact is not None:
            return exact

        return self._candidate_stage(identity)

    def _tracking_authoritative(
        self, identity: DistinctIdentity
    ) -> IdentityResolution:
        """Đọc authority đã được Tracking xác nhận, không suy diễn identity.

        Owner xác định `alias.map` là bảng human-confirmed và khoá `board` là
        canonical identity. Chế độ production này cố ý KHÔNG hỏi Reports alias
        store, `name`, `alt` hay similarity: chúng không phải authority theo
        contract mới. Cùng một normalizer đang dùng ở `keys.py` tạo mã tra;
        không có extract-code hoặc quy tắc mới nào ở đây.

        `inv.map` (S068 follow-up) là đường THỨ HAI, cùng cấp authority: nó
        chỉ được hỏi khi đường `alias.map`/`board` (khoá bằng MÃ) đã MISS —
        `inv.map` khoá bằng CÂU TÊN HÀNG kế toán đầy đủ (`normCode()` khác
        hẳn phép chuẩn hoá mã), nên hai đường không tranh nhau: một identity
        chỉ có thể khớp cái này hoặc cái kia theo đúng hình dạng dữ liệu của
        chính nó, không phải theo một thứ tự ưu tiên áp đặt.
        """
        normalized_code = identity.normalized_matching_aid.upper()
        aliases = self.tracking.alias_map()
        canonical = aliases.get(normalized_code, normalized_code)
        row = self.tracking.row_for(canonical)

        if row is not None and row.present_in_board:
            target = CanonicalProductIdentity(
                namespace=Namespace.TRACKING, source_product_code=canonical
            )
            method = (
                ResolutionMethod.TRACKING_CONFIRMED_ALIAS
                if canonical != normalized_code
                else ResolutionMethod.TRACKING_CANONICAL_EXACT
            )
            return IdentityResolution(
                identity=identity,
                outcome=Resolved(
                    identity=target,
                    provenance=self._provenance(
                        identity,
                        method,
                        target=target,
                        mapping_source=method.value,
                    ),
                ),
                resolution_method=method,
            )

        inv_map_resolution = self._tracking_inv_map_authoritative(identity)
        if inv_map_resolution is not None:
            return inv_map_resolution

        return IdentityResolution(
            identity=identity,
            outcome=PendingProduct(
                reason_code=(
                    PendingReason.MAPPING_STALE_TARGET_ABSENT
                    if normalized_code in aliases
                    else PendingReason.NO_CANDIDATE_IN_ANY_CATALOG
                ),
                attempted_sources=(AttemptedSource.TRACKING_CATALOG,),
                provenance=self._provenance(
                    identity,
                    (
                        ResolutionMethod.TRACKING_CONFIRMED_ALIAS
                        if normalized_code in aliases
                        else ResolutionMethod.TRACKING_CANONICAL_EXACT
                    ),
                ),
            ),
            resolution_method=(
                ResolutionMethod.TRACKING_CONFIRMED_ALIAS
                if normalized_code in aliases
                else ResolutionMethod.TRACKING_CANONICAL_EXACT
            ),
        )

    def _tracking_inv_map_authoritative(
        self, identity: DistinctIdentity
    ) -> Optional["IdentityResolution"]:
        """`inv.map` — authority cho CÂU TÊN HÀNG kế toán đầy đủ (S068 follow-up).

        Trả `None` khi nguồn vắng mặt HOẶC khoá vắng mặt trong `inv.map`: cả
        hai đường đó phải rơi về đúng Pending reason mà nhánh `alias.map`/
        `board` MISS đã tính (`MAPPING_STALE_TARGET_ABSENT` nếu `alias.map`
        từng có mục cho mã này, ngược lại `NO_CANDIDATE_IN_ANY_CATALOG`) —
        không tạo một nhánh Pending song song mang cùng ý nghĩa.

        `"-"` và "target hết hợp lệ trong board" là hai sự kiện khác biệt đã
        được xác nhận qua `inv.map` (không phải "chưa ai xem"), nên chúng trả
        `IdentityResolution` trực tiếp ở đây, không rơi về nhánh MISS chung.
        """
        if self.inv_map is None:
            return None

        value = self.inv_map.lookup(identity.raw_product_identity)
        if value is None:
            return None

        if value == TRACKING_INV_MAP_IGNORE_VALUE:
            return IdentityResolution(
                identity=identity,
                outcome=PendingProduct(
                    reason_code=PendingReason.TRACKING_INV_MAP_EXPLICIT_IGNORE,
                    attempted_sources=(AttemptedSource.TRACKING_CATALOG,),
                    provenance=self._provenance(
                        identity, ResolutionMethod.TRACKING_INV_MAP_CONFIRMED
                    ),
                ),
                resolution_method=ResolutionMethod.TRACKING_INV_MAP_CONFIRMED,
            )

        row = self.tracking.row_for(value)
        if row is None or not row.present_in_board:
            return IdentityResolution(
                identity=identity,
                outcome=PendingProduct(
                    reason_code=PendingReason.MAPPING_STALE_TARGET_ABSENT,
                    attempted_sources=(AttemptedSource.TRACKING_CATALOG,),
                    provenance=self._provenance(
                        identity, ResolutionMethod.TRACKING_INV_MAP_CONFIRMED
                    ),
                ),
                resolution_method=ResolutionMethod.TRACKING_INV_MAP_CONFIRMED,
            )

        target = CanonicalProductIdentity(
            namespace=Namespace.TRACKING, source_product_code=value
        )
        return IdentityResolution(
            identity=identity,
            outcome=Resolved(
                identity=target,
                provenance=self._provenance(
                    identity,
                    ResolutionMethod.TRACKING_INV_MAP_CONFIRMED,
                    target=target,
                    mapping_source=ResolutionMethod.TRACKING_INV_MAP_CONFIRMED.value,
                ),
            ),
            resolution_method=ResolutionMethod.TRACKING_INV_MAP_CONFIRMED,
        )

    def resolve_all(
        self, identities: Sequence[DistinctIdentity]
    ) -> tuple[IdentityResolution, ...]:
        """`G13-d` — một identity Pending KHÔNG chặn các identity còn lại.

        Không có `raise` nào ở vòng lặp này: một batch hỗn hợp phải hoàn tất
        với một tập kết quả hỗn hợp.
        """
        return tuple(self.resolve(identity) for identity in identities)

    # ---- các tầng --------------------------------------------------------

    def _alias_exact(self, identity: DistinctIdentity) -> Optional[IdentityResolution]:
        """`ALIAS_EXACT` — khớp `raw_identity_key` với một mapping CONFIRMED.

        Đây là đường 0-thao-tác của `CHECK-105D-04`/`-10A`/`-24`. Nó chỉ đọc
        `view`, không chạm store, nên không có chỗ nào để lỡ tay ghi.
        """
        mapping = self.view.active_mapping(
            identity.source_system, identity.raw_identity_key
        )
        if mapping is None or mapping.status is not MappingStatus.CONFIRMED:
            return None
        target = CanonicalProductIdentity(
            namespace=mapping.namespace,
            source_product_code=mapping.source_product_code,
        )
        return IdentityResolution(
            identity=identity,
            outcome=Resolved(
                identity=target,
                provenance=self._provenance(
                    identity,
                    ResolutionMethod.ALIAS_EXACT,
                    target=target,
                    mapping_source=mapping.mapping_source.value,
                    mapping_id=mapping.mapping_id,
                    mapping_version=mapping.version,
                ),
            ),
            resolution_method=ResolutionMethod.ALIAS_EXACT,
        )

    def _catalog_exact(
        self, identity: DistinctIdentity
    ) -> Optional[IdentityResolution]:
        """Quét khớp exact ở CẢ HAI namespace trước khi kết luận (`INV-29`)."""
        raw_key = identity.raw_identity_key
        aid = identity.normalized_matching_aid

        tracking_hits = self.tracking.exact_match_codes(raw_key=raw_key, aid=aid)
        pp_hits = self._pp_exact_hits(raw_key=raw_key, aid=aid)
        if not tracking_hits and not pp_hits:
            return None

        present_tracking = tuple(
            hit for hit in tracking_hits if self._present_in_board(hit[0])
        )
        absent_tracking = tuple(
            hit for hit in tracking_hits if not self._present_in_board(hit[0])
        )

        if present_tracking and pp_hits:
            return self._ambiguous(
                identity,
                ResolutionMethod.CROSS_NAMESPACE_TIE,
                self._candidates_from_hits(identity, present_tracking, pp_hits),
                PendingReason.AMBIGUOUS_MULTIPLE_DETERMINISTIC_CANDIDATES,
            )

        if len(present_tracking) > 1 or len(pp_hits) > 1:
            return self._ambiguous(
                identity,
                ResolutionMethod.MULTIPLE_EXACT,
                self._candidates_from_hits(identity, present_tracking, pp_hits),
                PendingReason.AMBIGUOUS_MULTIPLE_DETERMINISTIC_CANDIDATES,
            )

        if len(present_tracking) == 1:
            code, field = present_tracking[0]
            return self._auto_resolved(identity, Namespace.TRACKING, code, field)

        if len(pp_hits) == 1:
            code, field = pp_hits[0]
            return self._auto_resolved(identity, Namespace.PUBLIC_PURCHASE, code, field)

        if absent_tracking:
            # `INV-14c` — một identity MỚI chỉ khớp một mã đã biến mất khỏi
            # board. Không auto-resolve; Pending mang đúng lý do để người xử lý
            # biết đây là drift danh mục chứ không phải "chưa có dữ liệu".
            return self._stale_target(identity, absent_tracking)

        return None

    def _candidate_stage(self, identity: DistinctIdentity) -> IdentityResolution:
        """Tầng candidate: aid, `alias.map` của Tracking, similarity."""
        candidates = self._discover_candidates(identity)
        if not candidates:
            return IdentityResolution(
                identity=identity,
                outcome=PendingProduct(
                    reason_code=PendingReason.NO_CANDIDATE_IN_ANY_CATALOG,
                    attempted_sources=_ALL_SOURCES,
                    provenance=self._provenance(
                        identity, ResolutionMethod.SIMILARITY_RANKED
                    ),
                ),
            )

        method = candidates[0].method
        fingerprint = self._fingerprint(candidates)
        surviving = self._apply_rejection_memory(identity, candidates, fingerprint)

        if not surviving:
            return IdentityResolution(
                identity=identity,
                outcome=PendingProduct(
                    reason_code=(
                        PendingReason.CANDIDATE_REJECTED_AND_EVIDENCE_UNCHANGED
                    ),
                    attempted_sources=_ALL_SOURCES,
                    provenance=self._provenance(identity, method),
                ),
                candidates=(),
                resolution_method=method,
                evidence_fingerprint=fingerprint,
            )

        only_similarity = all(
            c.method is ResolutionMethod.SIMILARITY_RANKED for c in surviving
        )
        if only_similarity:
            # `INV-01`/`G06(c)` — evidence chỉ có similarity thì không có
            # candidate nào đáng để người xác nhận "một phát"; nó vẫn được hiển
            # thị, nhưng kết cục mặc định là Pending có lý do rõ ràng.
            return IdentityResolution(
                identity=identity,
                outcome=PendingProduct(
                    reason_code=PendingReason.ONLY_SIMILARITY_EVIDENCE,
                    attempted_sources=_ALL_SOURCES,
                    provenance=self._provenance(
                        identity, ResolutionMethod.SIMILARITY_RANKED
                    ),
                ),
                candidates=surviving,
                resolution_method=ResolutionMethod.SIMILARITY_RANKED,
                evidence_fingerprint=fingerprint,
            )

        return IdentityResolution(
            identity=identity,
            outcome=RequiresConfirmation(
                candidates=surviving,
                provenance=self._provenance(identity, surviving[0].method),
            ),
            candidates=surviving,
            resolution_method=surviving[0].method,
            evidence_fingerprint=fingerprint,
        )

    # ---- candidate -------------------------------------------------------

    def _discover_candidates(
        self, identity: DistinctIdentity
    ) -> tuple[RankedCandidate, ...]:
        found: list[tuple[Namespace, str, ResolutionMethod, MatchedOn, str, bool, Optional[str]]] = []

        for mapping in self.view.alias_index().values():
            if (
                mapping.normalized_matching_aid == identity.normalized_matching_aid
                and mapping.raw_identity_key != identity.raw_identity_key
                and mapping.namespace is not None
            ):
                found.append(
                    (
                        mapping.namespace,
                        mapping.source_product_code,
                        ResolutionMethod.ALIAS_AID_UNIQUE,
                        MatchedOn.AID,
                        identity.normalized_matching_aid,
                        True,
                        mapping.mapping_id,
                    )
                )

        alias_map = self.tracking.alias_map()
        primary = alias_map.get(identity.raw_identity_key) or alias_map.get(
            identity.normalized_matching_aid.upper()
        )
        if primary:
            found.append(
                (
                    Namespace.TRACKING,
                    primary,
                    ResolutionMethod.TRACKING_ALIAS_MAP,
                    MatchedOn.TRACKING_ALIAS_MAP,
                    identity.raw_identity_key,
                    self._present_in_board(primary),
                    None,
                )
            )

        for namespace, code, value in self._similarity_hits(identity):
            found.append(
                (
                    namespace,
                    code,
                    ResolutionMethod.SIMILARITY_RANKED,
                    MatchedOn.AID,
                    value,
                    True,
                    None,
                )
            )

        return self._rank(found)

    def _similarity_hits(
        self, identity: DistinctIdentity
    ) -> tuple[tuple[Namespace, str, str], ...]:
        """Evidence similarity — token overlap bảo thủ, KHÔNG rút mã.

        `D-04` (`DEC-147` §4): Tracking đã thử rút mã từ câu tên hàng bằng máy
        và bỏ hẳn vì sai trên tài sản thật. Ở đây similarity chỉ dùng để **xếp
        hạng candidate cho người xem**, và `is_auto_resolvable()` không bao giờ
        trả `True` cho nó — nên dù thuật toán có tệ đến đâu, nó cũng không tự
        quyết được điều gì.
        """
        tokens = {t for t in identity.normalized_matching_aid.split() if len(t) >= 3}
        if not tokens:
            return ()
        hits: list[tuple[Namespace, str, str]] = []
        for row in self.tracking.rows:
            if not row.present_in_board:
                continue
            haystack = " ".join(
                filter(None, [row.tracking_code, row.name, *row.alt])
            ).casefold()
            if any(token in haystack for token in tokens):
                hits.append((Namespace.TRACKING, row.tracking_code, row.tracking_code))
        for row in self._pp_identity_rows:
            haystack = " ".join(
                filter(None, [row.product_code, row.product_name, *row.aliases])
            ).casefold()
            if any(token in haystack for token in tokens):
                hits.append(
                    (Namespace.PUBLIC_PURCHASE, row.product_code, row.product_code)
                )
        return tuple(hits)

    def _rank(self, found: list) -> tuple[RankedCandidate, ...]:
        """Xếp hạng ỔN ĐỊNH (`INV-64`).

        Khoá sắp xếp là `(ưu tiên phương thức, namespace, mã)` — toàn bộ là giá
        trị của dữ liệu, không có `hash()`, không có thứ tự dict, không có thời
        gian. Cùng input → cùng thứ tự, mọi lần chạy, mọi máy. Trùng lặp bị
        loại theo ĐỦ TUPLE `(namespace, code)`, không theo mã (`INV-18`).
        """
        deduped: dict[tuple[Namespace, str], tuple] = {}
        for item in found:
            key = (item[0], item[1])
            if key not in deduped or _METHOD_RANK[item[2]] < _METHOD_RANK[
                deduped[key][2]
            ]:
                deduped[key] = item

        ordered = sorted(
            deduped.values(),
            key=lambda item: (_METHOD_RANK[item[2]], item[0].value, item[1]),
        )
        candidate_ids = tuple(f"{item[0].value}:{item[1]}" for item in ordered)
        return tuple(
            RankedCandidate(
                namespace=item[0],
                source_product_code=item[1],
                method=item[2],
                evidence=Evidence(
                    matched_on=item[3],
                    matched_value=item[4],
                    candidate_set_ids=candidate_ids,
                    ranking_method_id=RANKING_METHOD_ID,
                    parent_mapping_id=item[6],
                ),
                rank=index + 1,
                target_present_in_board=item[5],
            )
            for index, item in enumerate(ordered)
        )

    def _fingerprint(self, candidates: tuple[RankedCandidate, ...]) -> str:
        """Fingerprint tính trên tập candidate TRƯỚC khi suppress.

        Nếu tính sau, mỗi lần từ chối một candidate sẽ làm tập thay đổi →
        fingerprint thay đổi → chính candidate vừa bị từ chối lại hiện ra. Tập
        "đã hiển thị lúc quyết định" (§6.7) là tập đầy đủ, nên nó là tập được
        hash.
        """
        return evidence_fingerprint(
            pp_version_id=self._pp_version_id,
            tracking_capture_id=self.tracking.capture_id,
            candidate_set_ids=tuple(c.candidate_id for c in candidates),
            ranking_method_id=RANKING_METHOD_ID,
        )

    def _apply_rejection_memory(
        self,
        identity: DistinctIdentity,
        candidates: tuple[RankedCandidate, ...],
        fingerprint: str,
    ) -> tuple[RankedCandidate, ...]:
        """`INV-34`/`INV-35` — suppress khi VÀ CHỈ KHI cùng khoá + cùng fingerprint."""
        suppressed = {
            (r.candidate_namespace, r.candidate_code)
            for r in self.view.rejections
            if r.raw_identity_key == identity.raw_identity_key
            and r.evidence_fingerprint == fingerprint
        }
        stale_rejections = {
            (r.candidate_namespace, r.candidate_code): r
            for r in self.view.rejections
            if r.raw_identity_key == identity.raw_identity_key
            and r.evidence_fingerprint != fingerprint
        }

        surviving: list[RankedCandidate] = []
        for candidate in candidates:
            key = (candidate.namespace, candidate.source_product_code)
            if key in suppressed:
                continue
            previous = stale_rejections.get(key)
            if previous is not None:
                # `INV-35` — bằng chứng đã đổi, candidate quay lại, kèm chú thích.
                candidate = RankedCandidate(
                    namespace=candidate.namespace,
                    source_product_code=candidate.source_product_code,
                    method=candidate.method,
                    evidence=candidate.evidence,
                    rank=candidate.rank,
                    target_present_in_board=candidate.target_present_in_board,
                    note=(
                        "đã từ chối tại pp_version="
                        f"{previous.pp_version_id}, capture="
                        f"{previous.tracking_capture_id}"
                    ),
                )
            surviving.append(candidate)

        return tuple(
            RankedCandidate(
                namespace=c.namespace,
                source_product_code=c.source_product_code,
                method=c.method,
                evidence=c.evidence,
                rank=index + 1,
                target_present_in_board=c.target_present_in_board,
                note=c.note,
            )
            for index, c in enumerate(surviving)
        )

    # ---- helper ----------------------------------------------------------

    def _present_in_board(self, tracking_code: str) -> bool:
        row = self.tracking.row_for(tracking_code)
        return bool(row and row.present_in_board)

    def _auto_resolved(
        self,
        identity: DistinctIdentity,
        namespace: Namespace,
        code: str,
        field: str,
    ) -> IdentityResolution:
        target = CanonicalProductIdentity(
            namespace=namespace, source_product_code=code
        )
        return IdentityResolution(
            identity=identity,
            outcome=Resolved(
                identity=target,
                provenance=self._provenance(
                    identity,
                    ResolutionMethod.CATALOG_EXACT_UNIQUE,
                    target=target,
                    mapping_source=MappingSource.DETERMINISTIC_CATALOG_MATCH.value,
                ),
            ),
            resolution_method=ResolutionMethod.CATALOG_EXACT_UNIQUE,
        )

    def _ambiguous(
        self,
        identity: DistinctIdentity,
        method: ResolutionMethod,
        candidates: tuple[RankedCandidate, ...],
        reason: PendingReason,
    ) -> IdentityResolution:
        fingerprint = self._fingerprint(candidates)
        surviving = self._apply_rejection_memory(identity, candidates, fingerprint)
        if not surviving:
            return IdentityResolution(
                identity=identity,
                outcome=PendingProduct(
                    reason_code=(
                        PendingReason.CANDIDATE_REJECTED_AND_EVIDENCE_UNCHANGED
                    ),
                    attempted_sources=_ALL_SOURCES,
                    provenance=self._provenance(identity, method),
                ),
                resolution_method=method,
                evidence_fingerprint=fingerprint,
            )
        return IdentityResolution(
            identity=identity,
            outcome=RequiresConfirmation(
                candidates=surviving,
                provenance=self._provenance(identity, method),
            ),
            candidates=surviving,
            resolution_method=method,
            evidence_fingerprint=fingerprint,
        )

    def _stale_target(
        self, identity: DistinctIdentity, absent: tuple[tuple[str, str], ...]
    ) -> IdentityResolution:
        candidates = self._candidates_from_hits(identity, absent, ())
        return IdentityResolution(
            identity=identity,
            outcome=PendingProduct(
                reason_code=PendingReason.MAPPING_STALE_TARGET_ABSENT,
                attempted_sources=_ALL_SOURCES,
                provenance=self._provenance(
                    identity, ResolutionMethod.CATALOG_EXACT_UNIQUE
                ),
            ),
            candidates=candidates,
            resolution_method=ResolutionMethod.CATALOG_EXACT_UNIQUE,
            evidence_fingerprint=self._fingerprint(candidates),
        )

    def _candidates_from_hits(
        self,
        identity: DistinctIdentity,
        tracking_hits: tuple[tuple[str, str], ...],
        pp_hits: tuple[tuple[str, str], ...],
    ) -> tuple[RankedCandidate, ...]:
        found = [
            (
                Namespace.TRACKING,
                code,
                ResolutionMethod.MULTIPLE_EXACT,
                _MATCHED_ON_BY_FIELD[field],
                identity.raw_identity_key,
                self._present_in_board(code),
                None,
            )
            for code, field in tracking_hits
        ] + [
            (
                Namespace.PUBLIC_PURCHASE,
                code,
                ResolutionMethod.MULTIPLE_EXACT,
                _MATCHED_ON_BY_FIELD[field],
                identity.raw_identity_key,
                True,
                None,
            )
            for code, field in pp_hits
        ]
        return self._rank(found)

    def _provenance(
        self,
        identity: DistinctIdentity,
        method: ResolutionMethod,
        *,
        target: Optional[CanonicalProductIdentity] = None,
        mapping_source: Optional[str] = None,
        mapping_id: Optional[str] = None,
        mapping_version: Optional[int] = None,
    ) -> Provenance:
        return Provenance(
            raw_product_identity=identity.raw_product_identity,
            resolution_method=method.value,
            resolved_at=self._now,
            mapping_source=mapping_source,
            namespace=target.namespace if target else None,
            source_product_code=target.source_product_code if target else None,
            mapping_id=mapping_id,
            mapping_version=mapping_version,
            pp_version_id=self._pp_version_id,
            tracking_capture_id=self.tracking.capture_id,
            price_provenance=(
                "PUBLIC_PURCHASE_NO_TRACKING"
                if target is not None and target.namespace is Namespace.PUBLIC_PURCHASE
                else None
            ),
        )


_ALL_SOURCES: tuple[AttemptedSource, ...] = (
    AttemptedSource.ALIAS_MEMORY,
    AttemptedSource.TRACKING_CATALOG,
    AttemptedSource.PUBLIC_PURCHASE_CATALOG,
    AttemptedSource.CANDIDATE_RANKING,
)
"""`CHECK-105D-27` — Pending phải chứng minh resolver đã đi qua CẢ HAI catalog."""


def distinct_identities(rows: Sequence["SalesRowRef"]) -> tuple[DistinctIdentity, ...]:
    """Lập tập DISTINCT `D` TRƯỚC khi hiển thị hay hỏi bất cứ điều gì.

    `CHECK-105D-03`: 10.000 dòng chứa 50 identity khác nhau ⇒ `|D| == 50`, và
    trần thao tác là `|D|`, không phải số dòng và không phải số order. Thứ tự
    trả về là thứ tự gặp lần đầu — ổn định, không phụ thuộc thứ tự dict.
    """
    order: list[tuple[str, str]] = []
    seen: dict[tuple[str, str], dict] = {}
    for row in rows:
        key = (row.source_system, row.raw_identity_key)
        if key not in seen:
            seen[key] = {
                "raw_product_identity": row.raw_product_identity,
                "normalized_matching_aid": row.normalized_matching_aid,
                "order_ids": [],
                # Tập song song chỉ để kiểm tra thành viên. Danh sách giữ thứ
                # tự gặp lần đầu (ổn định cho INV-64); một phép `in` trên danh
                # sách sẽ là O(số order) cho MỖI dòng, và batch quy phạm của
                # CHECK-105D-03 là 10.000 dòng.
                "order_seen": set(),
                "line_count": 0,
            }
            order.append(key)
        bucket = seen[key]
        bucket["line_count"] += 1
        if row.order_id not in bucket["order_seen"]:
            bucket["order_seen"].add(row.order_id)
            bucket["order_ids"].append(row.order_id)

    return tuple(
        DistinctIdentity(
            source_system=key[0],
            raw_identity_key=key[1],
            raw_product_identity=seen[key]["raw_product_identity"],
            normalized_matching_aid=seen[key]["normalized_matching_aid"],
            order_ids=tuple(seen[key]["order_ids"]),
            line_count=seen[key]["line_count"],
        )
        for key in order
    )


@dataclass(frozen=True)
class SalesRowRef:
    """Tham chiếu tối thiểu tới một dòng bán hàng mà resolver cần.

    Cố ý KHÔNG mang tên khách, số điện thoại, địa chỉ hay IMEI: resolver không
    cần chúng, và không mang thì không thể lỡ log ra
    (`17_DATA_GOVERNANCE_PRIVACY`, `INV-86`).
    """

    order_id: str
    sale_date: date
    raw_product_identity: str
    source_system: str = SOURCE_SYSTEM_REPORTS_SALES

    @property
    def raw_identity_key(self) -> str:
        return raw_identity_key(self.raw_product_identity)

    @property
    def normalized_matching_aid(self) -> str:
        return normalized_matching_aid(self.raw_product_identity)
