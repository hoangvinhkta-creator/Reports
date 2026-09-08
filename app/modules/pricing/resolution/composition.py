"""`TASK-105E` — chủ sở hữu composition `P00–P11` (`DEC-154` §7/§11).

## Lớp này KHÔNG sở hữu một nguồn dữ liệu nào

Nó nhận identity đã resolve (`TASK-105D`), hỏi đúng nguồn giá theo đúng thứ
tự, và giữ nguyên provenance. Không matching, không parsing, không suy ra mã,
không tính giá. Mọi con số đều đến từ một nguồn đã được review riêng.

## Bản đồ nhánh (áp cho mọi ngày bán mà không có entry lịch sử đã xác nhận)

```text
identity TRACKING:<mã>
    ---  Tracking Daily MIN (R1)              → giá của ĐÚNG ngày bán, hoặc Pending
    P01  HistoricalVendorMin (TASK-105C)      → NGUỒN CHƯA ĐƯỢC CẤP PHÉP
    P03  fallback Public Purchase             → BỊ CHẶN (xem dưới)
    P11  Pending

identity PUBLIC_PURCHASE:<mã>
    P04/P05  bảng giá Public Purchase theo `sale_date`  → giá
    P06      không có giá hợp lệ tại ngày bán           → Pending
```

## R1 (2026-09-07) — nhánh TRACKING đổi thẩm quyền

Nguồn giá nhập tự động của một mã Tracking nay là **MIN của ngày bán**, do
Tracking tính và lưu (`pricing/daily_min/`). Trước R1, nhánh này đọc lịch sử
`board/<mã>/tp/ton` (`pricing/tracking_history/`) — tức **giá nhập công khai**
Owner đặt tay, một đại lượng khác. Owner đã chốt rằng giá nhập tự động là MIN.

Đường cũ KHÔNG bị xoá và giữ nguyên nghĩa cũ, nhưng chỉ chạy khi caller nêu rõ
`legacy_tracking_history_authority=True`. Không có nhánh nào rơi từ MIN sang
nó: hai đại lượng đều là số tiền hợp lệ, nên một lần rơi nhầm sẽ trông hoàn
toàn bình thường trên mọi bảng.

## P01/P03 — vì sao fallback Public Purchase KHÔNG được chạy hôm nay

`P03` chỉ được phép khi **không có valid vendor candidate tại `sale_date`**
(`DEC-154` §7). Đó là một *absence đã xác định*: phải hỏi nguồn vendor rồi
nhận về "không có". `TASK-105C` hiện `BLOCKED / NOT AUTHORIZED` — nguồn ấy
chưa tồn tại, nên câu hỏi chưa từng được đặt ra. "Chưa hỏi" không phải "đã
hỏi và không có", và biến cái thứ nhất thành cái thứ hai là đúng phép suy
diễn mà Scope của `TASK-105E` cấm (source failure ≠ determined absence,
tiền lệ `CHECK-105C-17`).

Hệ quả là một identity TRACKING không lấy giá công khai, kể cả khi có
`CrossSystemProductMapping` CONFIRMED và bảng giá công khai có đúng mã ấy.
Đó là kết quả ĐÚNG theo fail-safe, không phải một khiếm khuyết: giá vendor
đứng TRÊN giá công khai trong thứ tự ưu tiên, và trả về giá hạng hai khi
hạng nhất chưa được hỏi là một con số sai lặng lẽ đi thẳng vào KPI.
`P09`/`PUBLIC_PURCHASE_NO_VENDOR_PRICE` vì thế được định nghĩa đầy đủ nhưng
chưa có đường tới — nhánh này mở khi và chỉ khi `TASK-105C` được cấp phép.

## Vì sao nhánh TRACKING dùng lại provider, không gọi thẳng reader

`TrackingHistoryPriceProvider` đã qua independent review và tự nó chặn
`PUBLIC_PURCHASE:<mã>` (`IDENTITY_NOT_TRACKING`). Composition định tuyến theo
namespace MỘT lần, rồi provider kiểm lại lần nữa từ `identity_index` của
chính nó — hai lớp độc lập cùng khẳng định một điều. Không có dòng logic nào
của reader được chép lại ở đây.

## Pending không bao giờ là 0, và không bao giờ biến mất

Mọi kết cục Pending đặt `accounting_purchase_price = None` và
`price_source = "Pending"` — đúng khoá mà `detect_missing_purchase_price`
(`TASK-110`) đọc để sinh `Missing.PurchasePrice`. Không có hàng chờ thứ hai,
không dòng nào bị bỏ, không giá nào bị đoán.
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Optional

from app.modules.domain.models import (
    PRICE_SOURCE_PENDING,
    PRICE_SOURCE_PUBLIC_PURCHASE_NO_TRACKING,
    PRICE_SOURCE_PUBLIC_PURCHASE_NO_VENDOR_PRICE,
    PRICE_SOURCE_TRACKING_DAILY_MIN,
    PRICE_SOURCE_TRACKING_PRICE_HISTORY,
    WorkingLine,
)
from app.modules.pricing.daily_min.provider import (
    DailyMinResolution,
    TrackingDailyMinProvider,
)
from app.modules.pricing.daily_min.snapshot import DayStatus
from app.modules.pricing.file_price_provider import FilePriceProvider
from app.modules.pricing.resolution.sources import (
    PriceEvidenceSnapshot,
    PriceResolutionSources,
)
from app.modules.pricing.tracking_history.provider import (
    TrackingHistoryPriceProvider,
)
from app.modules.pricing.tracking_history.reader import (
    PriceReconstruction,
    TrackingPriceHistoryReader,
)
from app.modules.product.identity.identity import (
    CanonicalProductIdentity,
    Namespace,
    PendingProduct,
    PendingReason,
    RequiresConfirmation,
    Resolved,
)
from app.modules.product.identity.keys import (
    EmptyRawIdentityError,
    raw_identity_key,
)
from app.modules.product.identity.resolver import (
    CONFLICT_MAPPING_SOURCE,
    ProductIdentityResolver,
    SalesRowRef,
)
from app.modules.product.identity.tracking_catalog import CaptureStatus

__all__ = [
    "CompositionRule",
    "PRICE_SOURCE_BY_RULE",
    "PostCutoverPriceComposition",
    "PriceResolutionReason",
    "PriceResolutionRecord",
    "PriceResolutionReport",
    "PriceResolutionStatus",
    "VENDOR_SOURCE_NOT_AUTHORIZED_DETAIL",
]

TRACKING_DAILY_MIN_HINT = "tools/tracking/capture_daily_min.py"
"""Nhắc đúng công cụ phải chạy khi nguồn chưa nối.

Một thông điệp Pending chỉ nói "nguồn chưa có" bắt người đọc đi tìm; nói luôn
tên công cụ thì nó thành một việc làm được ngay."""

VENDOR_SOURCE_NOT_AUTHORIZED_DETAIL = (
    "P01 `HistoricalVendorMin` (TASK-105C) = BLOCKED / NOT AUTHORIZED — nguồn "
    "vendor chưa tồn tại, nên 'không có valid vendor candidate' CHƯA BAO GIỜ "
    "được xác định và điều kiện của P03 không thoả. Fallback Public Purchase "
    "cho identity TRACKING bị chặn có chủ đích."
)


PRICE_SOURCE_BY_RULE: dict["CompositionRule", str] = {}
"""Nhãn `price_source` của mỗi nhánh — bảng, không phải chuỗi rải rác.

`DEC-154` §10 cấm collapse hai provenance Public Purchase. Một bảng khiến
"hai nhánh khác nhau có hai nhãn khác nhau" là một tính chất kiểm được bằng
một assertion trên chính bảng, thay vì phải đi đọc từng nhánh và tin rằng
không ai copy-paste nhầm."""


class PriceResolutionStatus(str, Enum):
    RESOLVED = "RESOLVED"
    PENDING = "PENDING"


class CompositionRule(str, Enum):
    """Nhánh nào của `DEC-154` §7 đã quyết định dòng này."""

    TRACKING_DAILY_MIN = "TRACKING_DAILY_MIN"
    TRACKING_HISTORY_AUTHORITY = "TRACKING_HISTORY_AUTHORITY"
    PUBLIC_PURCHASE_DIRECT = "PUBLIC_PURCHASE_DIRECT"  # P04/P05/P08
    PUBLIC_PURCHASE_VENDOR_FALLBACK = "PUBLIC_PURCHASE_VENDOR_FALLBACK"  # P03/P09
    NOT_RESOLVED = "NOT_RESOLVED"


PRICE_SOURCE_BY_RULE.update(
    {
        CompositionRule.TRACKING_DAILY_MIN: PRICE_SOURCE_TRACKING_DAILY_MIN,
        CompositionRule.TRACKING_HISTORY_AUTHORITY: (
            PRICE_SOURCE_TRACKING_PRICE_HISTORY
        ),
        CompositionRule.PUBLIC_PURCHASE_DIRECT: (
            PRICE_SOURCE_PUBLIC_PURCHASE_NO_TRACKING  # P08
        ),
        CompositionRule.PUBLIC_PURCHASE_VENDOR_FALLBACK: (
            PRICE_SOURCE_PUBLIC_PURCHASE_NO_VENDOR_PRICE  # P09 — chưa có đường tới
        ),
    }
)


class PriceResolutionReason(str, Enum):
    """Enum ĐÓNG. Không có `UNKNOWN`: một nhánh không gọi được tên mình là một
    nhánh chưa ai nghĩ tới, và nó phải làm test đỏ chứ không được trôi qua."""

    SALE_DATE_MISSING = "SALE_DATE_MISSING"
    RAW_PRODUCT_IDENTITY_EMPTY = "RAW_PRODUCT_IDENTITY_EMPTY"
    IDENTITY_SOURCES_UNAVAILABLE = "IDENTITY_SOURCES_UNAVAILABLE"
    IDENTITY_UNRESOLVED = "IDENTITY_UNRESOLVED"
    IDENTITY_REQUIRES_CONFIRMATION = "IDENTITY_REQUIRES_CONFIRMATION"
    #: R2 §4.3 — người dùng đã xác nhận hàng KHÔNG có trên bảng giá Tracking.
    #: Phân loại ĐÃ XONG; dòng chỉ còn thiếu GIÁ, và giá đó nhập tay được.
    #: Tách khỏi `IDENTITY_UNRESOLVED` là toàn bộ điểm của trạng thái này:
    #: gộp lại sẽ đẩy dòng về hàng đợi "chưa phân loại" mãi mãi.
    IDENTITY_OUT_OF_CATALOG = "IDENTITY_OUT_OF_CATALOG"
    #: R2 §4.2 — mapping đã xác nhận của Reports và authority của Tracking
    #: chỉ về hai mã khác nhau. Không bên nào tự thắng.
    IDENTITY_CONFLICT = "IDENTITY_CONFLICT"
    TRACKING_DAILY_MIN_SOURCE_UNAVAILABLE = "TRACKING_DAILY_MIN_SOURCE_UNAVAILABLE"
    TRACKING_DAILY_MIN_PENDING = "TRACKING_DAILY_MIN_PENDING"
    TRACKING_HISTORY_SOURCE_UNAVAILABLE = "TRACKING_HISTORY_SOURCE_UNAVAILABLE"
    TRACKING_HISTORY_PENDING = "TRACKING_HISTORY_PENDING"
    VENDOR_SOURCE_NOT_AUTHORIZED = "VENDOR_SOURCE_NOT_AUTHORIZED"
    PUBLIC_PURCHASE_SOURCE_UNAVAILABLE = "PUBLIC_PURCHASE_SOURCE_UNAVAILABLE"
    PUBLIC_PURCHASE_NO_PRICE_AT_SALE_DATE = "PUBLIC_PURCHASE_NO_PRICE_AT_SALE_DATE"


@dataclass(frozen=True)
class PriceResolutionRecord:
    """Một quyết định giá, đủ để mở lại — Resolved LẪN Pending.

    `WorkingLine` chỉ có chỗ cho một con số và một nhãn nguồn; mở rộng nó nằm
    ngoài phạm vi phiên này. Nên bản ghi đầy đủ đi BÊN CẠNH dữ liệu, giống
    `TrackingHistoryPriceProvider.audit_trail` — và nó ghi CẢ những dòng
    Pending, vì "vì sao dòng này không có giá" mới là câu hỏi người kiểm hỏi.
    """

    order_id: str
    raw_product_identity: Optional[str]
    raw_identity_key: Optional[str]
    sale_date: Optional[_dt.date]
    identity: Optional[CanonicalProductIdentity]
    status: PriceResolutionStatus
    rule: CompositionRule
    price_vnd: Optional[Decimal]
    price_source: str
    evidence: PriceEvidenceSnapshot
    reason: Optional[PriceResolutionReason] = None
    detail: str = ""
    fallback_blocked_by: Optional[PriceResolutionReason] = None
    fallback_blocked_detail: str = ""
    tracking_reconstruction: Optional[PriceReconstruction] = None
    #: R1 — kết quả đầy đủ của lần tra MIN theo ngày, kể cả khi Pending.
    #: `WorkingLine` chỉ có chỗ cho một con số và một nhãn nguồn, nên nguồn
    #: giữ MIN, revision, phiên bản luật và trạng thái chốt của ngày đi BÊN
    #: CẠNH dữ liệu — đúng khuôn `tracking_reconstruction` ngay trên.
    daily_min_resolution: Optional[DailyMinResolution] = None

    def __post_init__(self) -> None:
        if self.status is PriceResolutionStatus.RESOLVED:
            if self.price_vnd is None or self.reason is not None:
                raise ValueError(
                    "RESOLVED bắt buộc có price_vnd và KHÔNG có reason"
                )
            if self.price_source == PRICE_SOURCE_PENDING:
                raise ValueError("RESOLVED không bao giờ mang price_source Pending")
        else:
            if self.price_vnd is not None or self.reason is None:
                raise ValueError(
                    "PENDING bắt buộc có reason và KHÔNG BAO GIỜ mang price_vnd "
                    "(INV-25: Pending không phải 0, không phải giá cũ)"
                )
            if self.price_source != PRICE_SOURCE_PENDING:
                raise ValueError(
                    "PENDING phải mang đúng nhãn 'Pending' — đó là khoá mà "
                    "detect_missing_purchase_price (TASK-110) đọc"
                )

    @property
    def is_resolved(self) -> bool:
        return self.status is PriceResolutionStatus.RESOLVED


@dataclass(frozen=True)
class PriceResolutionReport:
    """Kết quả của một lần `apply()` — một bộ bằng chứng, nhiều bản ghi."""

    evidence: PriceEvidenceSnapshot
    records: tuple[PriceResolutionRecord, ...] = ()
    skipped_pre_cutover_lines: int = 0

    @property
    def resolved_count(self) -> int:
        return sum(1 for r in self.records if r.is_resolved)

    @property
    def pending_count(self) -> int:
        return sum(1 for r in self.records if not r.is_resolved)

    @property
    def provisional_records(self) -> tuple[PriceResolutionRecord, ...]:
        """Những dòng lấy giá từ một NGÀY CHƯA CHỐT.

        Ngày chưa chốt nghĩa là Tracking còn có thể ghi thêm một mốc giá cho
        ngày ấy trước khi nó kết thúc. Con số hiện tại DÙNG ĐƯỢC — nó là trạng
        thái quan sát được mới nhất, và bắt người ta chờ hết ngày mới xem được
        báo cáo là vô ích. Nhưng nó chưa phải con số cuối cùng.
        """
        return tuple(
            r
            for r in self.records
            if r.daily_min_resolution is not None
            and r.daily_min_resolution.is_resolved
            and r.daily_min_resolution.provenance.day_status is DayStatus.PROVISIONAL
        )

    @property
    def provisional_count(self) -> int:
        return len(self.provisional_records)

    @property
    def resolved_prices_are_final(self) -> bool:
        """Mọi giá ĐÃ RESOLVE của lần import này có đến từ ngày đã chốt không.

        Cố ý chỉ nói về những dòng CÓ giá, và tên của nó nói đúng điều đó. Một
        report rỗng hay một report toàn Pending đều trả `True` ở đây — hoàn
        toàn đúng theo nghĩa hẹp này ("không có giá nào đến từ ngày chưa
        chốt"), và hoàn toàn SAI nếu ai đó đọc nó thành "kỳ đã chốt".

        Bản trước tên là `prices_are_final`, và cái tên ấy mời đúng cách đọc
        sai kia: một kỳ chưa nối nguồn giá — mọi dòng Pending — sẽ trả `True`
        và một cổng "kỳ đã chốt" xây trên nó sẽ mở ra cho một kỳ chưa có lấy
        một giá vốn nào. Cổng đúng là `period_is_final` ngay bên dưới.
        """
        return self.provisional_count == 0

    @property
    def has_priceable_lines(self) -> bool:
        """Lần import này có dòng nào để chốt không.

        Một report RỖNG không phải một kỳ đã hoàn tất; nó là một kỳ chưa có gì.
        Hai chuyện ấy dẫn tới hai việc khác nhau (trình bày kết quả, hay đi tìm
        xem sổ bán hàng đâu), nên chúng không được gộp.
        """
        return bool(self.records)

    @property
    def period_is_final(self) -> bool:
        """CỔNG HOÀN TẤT CẤP KỲ — ba điều kiện, không phải một.

        Một kỳ chỉ được gọi là đã chốt khi:

        1. CÓ dữ liệu cần chốt (`has_priceable_lines`) — kỳ rỗng không phải kỳ
           đã xong;
        2. KHÔNG còn dòng Pending (`pending_count == 0`) — một dòng chưa có giá
           vốn là một con số còn thiếu trong lợi nhuận của kỳ, và nó sẽ xuất
           hiện SAU khi ai đó đã chốt sổ;
        3. KHÔNG còn giá đến từ ngày `PROVISIONAL` (`provisional_count == 0`) —
           Tracking còn có thể ghi thêm một mốc cho ngày ấy.

        Cờ này vẫn KHÔNG chặn việc xem báo cáo và cố ý không tự gắn vào một
        cổng UI nào ở đây: `PriceResolutionReport` là bản ghi bằng chứng, không
        phải nơi ra quyết định trình bày.
        """
        return (
            self.has_priceable_lines
            and self.pending_count == 0
            and self.provisional_count == 0
        )


class PostCutoverPriceComposition:
    """Áp composition giá cho các dòng không có registry đã xác nhận.

    Dựng MỘT LẦN cho MỘT lần import (`app/composition.py`), từ một
    `PriceResolutionSources` đã đóng băng. Một `capture_status = FAILED` nổ
    NGAY tại đây (`INV-12`) — trước khi bất kỳ dòng nào được chạm tới — chứ
    không biến thành Pending ở tầng dưới.
    """

    def __init__(self, sources: PriceResolutionSources) -> None:
        self._sources = sources
        self._evidence = sources.evidence_snapshot
        self._records: list[PriceResolutionRecord] = []

        history = sources.tracking_price_history
        tz = sources.business_timezone
        # `TrackingPriceHistoryReader.__init__` gọi `require_complete()`:
        # FAILED = LỖI CỨNG ngay lúc dựng, không phải Pending (`INV-12`).
        self._reader: Optional[TrackingPriceHistoryReader] = (
            TrackingPriceHistoryReader(history) if history is not None else None
        )
        self._business_tz: Optional[_dt.tzinfo] = tz.tzinfo if tz.is_valid else None

        pp = sources.public_purchase
        self._public_purchase_prices: Optional[FilePriceProvider] = (
            FilePriceProvider(pp.validated_price_rows()) if pp is not None else None
        )

        # `require_complete()` chạy NGAY tại đây: một ảnh chụp FAILED là LỖI
        # CỨNG lúc dựng, không phải Pending ở tầng dưới (`INV-12`) — cùng cách
        # `TrackingPriceHistoryReader` đã làm ngay trên.
        self._daily_min_snapshot = (
            sources.tracking_daily_min.require_complete()
            if sources.tracking_daily_min is not None
            else None
        )

    # ------------------------------------------------------------------

    @property
    def evidence(self) -> PriceEvidenceSnapshot:
        return self._evidence

    @property
    def records(self) -> tuple[PriceResolutionRecord, ...]:
        return tuple(self._records)

    @property
    def report(self) -> PriceResolutionReport:
        """Toàn bộ bằng chứng đã tích luỹ của lần import này.

        `apply()` trả report của ĐÚNG lượt gọi ấy; pipeline gọi nó một lần rồi
        bỏ, và thứ còn lại là `records`. Nhưng câu hỏi vận hành ("kỳ này còn
        dùng giá của ngày chưa chốt không") hỏi về CẢ lần import, không phải
        về một lượt gọi. Dựng ở đây để không ai phải tự gom lại — tự gom là
        chỗ để quên một lượt.
        """
        return PriceResolutionReport(
            evidence=self._evidence, records=tuple(self._records)
        )

    # ------------------------------------------------------------------

    def apply(self, lines: list[WorkingLine]) -> PriceResolutionReport:
        """Đặt `accounting_purchase_price`/`price_source` theo evidence.

        Caller loại các dòng `HistoricalConfirmed` trước khi gọi. Với dòng
        pre-cutover còn lại, reader vẫn tự kiểm mốc baseline, capture cuối và
        chuỗi sự kiện; thiếu bất kỳ điều kiện nào thì Pending, không backfill.
        """
        records: list[PriceResolutionRecord] = []
        eligible: list[tuple[WorkingLine, str]] = []

        for line in lines:
            if line.date is None:
                records.append(
                    self._pending(
                        line,
                        None,
                        None,
                        PriceResolutionReason.SALE_DATE_MISSING,
                        "Dòng không có ngày bán; không phân loại được cutover và "
                        "không dựng được khoảng thời gian nào để hỏi giá.",
                    )
                )
                continue
            try:
                key = raw_identity_key(line.product_raw)
            except (EmptyRawIdentityError, TypeError, AttributeError):
                records.append(
                    self._pending(
                        line,
                        None,
                        None,
                        PriceResolutionReason.RAW_PRODUCT_IDENTITY_EMPTY,
                        "product_raw rỗng sau chuẩn hoá — không sinh được khoá "
                        "định danh, nên không có identity nào để tra giá.",
                    )
                )
                continue
            eligible.append((line, key))

        if eligible:
            records.extend(self._resolve_eligible(eligible))

        for record in records:
            self._records.append(record)

        report = PriceResolutionReport(
            evidence=self._evidence,
            records=tuple(records),
            skipped_pre_cutover_lines=0,
        )
        return report

    # ------------------------------------------------------------------

    def _resolve_eligible(
        self, eligible: list[tuple[WorkingLine, str]]
    ) -> list[PriceResolutionRecord]:
        catalog = self._sources.tracking_catalog
        pp_version = self._sources.public_purchase
        view = self._sources.identity_store_view

        # `pp_version` KHÔNG còn nằm trong cổng này (DEC-165). Public Purchase
        # là giá Owner quản trong Tracking, hiệu lực theo thời gian, và Reports
        # đọc nó qua `purchase_price_baseline`/`purchase_price_history` — cùng
        # một đường với nhánh TRACKING bên dưới. Catalog PP YAML chỉ còn là
        # danh mục identity LEGACY: nó cần cho các mã `PUBLIC_PURCHASE:<mã>`,
        # và nhánh `_public_purchase_branch` đã tự trả Pending
        # (`PUBLIC_PURCHASE_SOURCE_UNAVAILABLE`) khi nó vắng mặt. Để nó trong
        # cổng AND là bắt một mã Tracking có đủ bằng chứng phải Pending vì một
        # file không liên quan — một Pending KHÔNG trung thực.
        if (
            catalog is None
            or catalog.capture_status is not CaptureStatus.COMPLETE
            or view is None
        ):
            missing = [
                name
                for name, value in (
                    ("TrackingCatalogSnapshot", catalog),
                    ("ProductIdentityStore view", view),
                )
                if value is None
            ]
            if catalog is not None and catalog.capture_status is not CaptureStatus.COMPLETE:
                missing.append("TrackingCatalogSnapshot COMPLETE")
            detail = (
                "Chưa nối được nguồn identity post-cutover: "
                f"{', '.join(missing)} vắng mặt. Đây là NGUỒN CHƯA CÓ, không "
                "phải kết luận 'sản phẩm không tồn tại' — không mã nào được "
                "đoán và không giá nào được dựng."
            )
            return [
                self._pending(
                    line,
                    key,
                    None,
                    PriceResolutionReason.IDENTITY_SOURCES_UNAVAILABLE,
                    detail,
                )
                for line, key in eligible
            ]

        # Owner đã cho phép consult Public Purchase trước 01/09/2026 khi
        # evidence phủ ngày bán. `resolve_batch()` cũ có gate kỹ thuật theo
        # cutover, nên composition gọi resolver trực tiếp cho tập đã được
        # pipeline loại entry lịch sử xác nhận. Identity vẫn phải exact hoặc
        # confirmed; không có nhánh đoán mã.
        resolutions = ProductIdentityResolver(
            tracking_snapshot=catalog,
            pp_version=pp_version,
            store_view=view,
            tracking_identity_authority=self._sources.tracking_identity_authority,
            inv_map_snapshot=self._sources.tracking_inv_map,
        ).resolve_all(
            tuple(
                SalesRowRef(
                    order_id=line.order_id,
                    sale_date=line.date,
                    raw_product_identity=line.product_raw or "",
                )
                for line, _ in eligible
            )
        )

        identity_index: dict[str, CanonicalProductIdentity] = {}
        by_key = {}
        for resolution in resolutions:
            outcome = resolution.outcome
            by_key[resolution.identity.raw_identity_key] = outcome
            if isinstance(outcome, Resolved):
                identity_index[resolution.identity.raw_identity_key] = outcome.identity

        tracking_provider = self._build_tracking_provider(identity_index)
        daily_min_provider = self._build_daily_min_provider(identity_index)

        records: list[PriceResolutionRecord] = []
        for line, key in eligible:
            outcome = by_key[key]
            if isinstance(outcome, Resolved):
                identity = outcome.identity
                if identity.namespace is Namespace.TRACKING:
                    records.append(
                        self._tracking_branch(
                            line, key, identity, daily_min_provider, tracking_provider
                        )
                    )
                else:
                    records.append(self._public_purchase_branch(line, key, identity))
            elif isinstance(outcome, RequiresConfirmation):
                # R2 §4.2 — hai lý do KHÁC NHAU cùng đi qua `RequiresConfirmation`
                # (union `ResolutionOutcome` ĐÓNG, không có biến thể thứ năm),
                # và chúng cần hai câu khác nhau trên màn hình: "chưa đủ căn cứ,
                # hãy chọn" so với "hai nguồn đã xác nhận đang chỏi nhau, hãy
                # chọn lại". Nhãn nằm ở provenance, nên union vẫn đóng.
                conflict = (
                    outcome.provenance is not None
                    and outcome.provenance.mapping_source == CONFLICT_MAPPING_SOURCE
                )
                records.append(
                    self._pending(
                        line,
                        key,
                        None,
                        (
                            PriceResolutionReason.IDENTITY_CONFLICT
                            if conflict
                            else PriceResolutionReason.IDENTITY_REQUIRES_CONFIRMATION
                        ),
                        (
                            "Mapping đã xác nhận của Reports và authority của "
                            "Tracking chỉ về hai mã khác nhau. Composition KHÔNG "
                            "chọn bên thắng — người dùng phải chọn lại."
                            if conflict
                            else "Identity còn AMBIGUOUS — cần đúng một quyết định "
                            "của người. Composition không chọn hộ giữa các "
                            "candidate."
                        ),
                    )
                )
            elif isinstance(outcome, PendingProduct):
                # `OUT_OF_CATALOG_CONFIRMED` là một Pending về GIÁ, không phải
                # về NHẬN DIỆN. Trộn nó vào `IDENTITY_UNRESOLVED` sẽ làm màn
                # hình hỏi Owner phân loại lại đúng thứ họ vừa phân loại xong.
                out_of_catalog = (
                    outcome.reason_code is PendingReason.OUT_OF_CATALOG_CONFIRMED
                )
                records.append(
                    self._pending(
                        line,
                        key,
                        None,
                        (
                            PriceResolutionReason.IDENTITY_OUT_OF_CATALOG
                            if out_of_catalog
                            else PriceResolutionReason.IDENTITY_UNRESOLVED
                        ),
                        (
                            "Người dùng đã xác nhận mặt hàng này KHÔNG có trên "
                            "bảng giá Tracking. Phân loại đã xong; dòng vẫn nằm "
                            "trong báo cáo và chờ một giá nhập tay."
                            if out_of_catalog
                            else f"TASK-105D trả PENDING_PRODUCT "
                            f"({outcome.reason_code.value}); không có identity "
                            "nào để hỏi giá."
                        ),
                    )
                )
            else:  # pragma: no cover — union ĐÓNG, nhánh này không tồn tại
                raise TypeError(
                    f"ResolutionOutcome ngoài union đóng cho khoá {key!r}: "
                    f"{type(outcome).__name__}"
                )
        return records

    def _build_daily_min_provider(
        self, identity_index: dict[str, CanonicalProductIdentity]
    ) -> Optional[TrackingDailyMinProvider]:
        if self._daily_min_snapshot is None:
            return None
        return TrackingDailyMinProvider(
            self._daily_min_snapshot, identity_index=identity_index
        )

    def _build_tracking_provider(
        self, identity_index: dict[str, CanonicalProductIdentity]
    ) -> Optional[TrackingHistoryPriceProvider]:
        if self._reader is None or self._business_tz is None:
            return None
        return TrackingHistoryPriceProvider(
            self._reader,
            identity_index=identity_index,
            business_tz=self._business_tz,
        )

    # ------------------------------------------------------------------

    def _tracking_branch(
        self,
        line: WorkingLine,
        key: str,
        identity: CanonicalProductIdentity,
        daily_min: Optional[TrackingDailyMinProvider],
        provider: Optional[TrackingHistoryPriceProvider],
    ) -> PriceResolutionRecord:
        """R1 — giá nhập tự động của một mã Tracking là MIN CỦA NGÀY BÁN.

        Đây là điểm thay đổi thẩm quyền của R1, và nó cố ý KHÔNG có nhánh dự
        phòng. Khi nguồn MIN theo ngày chưa được nối, dòng này Pending với đúng
        lý do ấy — nó KHÔNG rơi về lịch sử `board/<mã>/tp/ton`, không rơi về
        bảng giá công khai, không lấy giá hiện tại, không lấy giá của một ngày
        khác. Mỗi nhánh dự phòng như vậy đều trả về một con số tiền hợp lệ cho
        một câu hỏi chưa được trả lời, và một giá vốn sai thì không có gì đỏ
        lên — nó chỉ đi thẳng vào lợi nhuận rồi vào lương.

        Đường lịch sử `tp/ton` chỉ còn chạy khi caller NÊU RÕ
        `legacy_tracking_history_authority=True` (fixture/đối chiếu kết quả
        cũ). Xem `PriceResolutionSources.legacy_tracking_history_authority`.
        """
        if not self._sources.legacy_tracking_history_authority:
            return self._daily_min_branch(line, key, identity, daily_min)
        if provider is None:
            missing = []
            if self._reader is None:
                missing.append("ảnh chụp purchase_price_baseline/history")
            if self._business_tz is None:
                missing.append("múi giờ nghiệp vụ (config/price_resolution.yaml)")
            return self._pending(
                line,
                key,
                identity,
                PriceResolutionReason.TRACKING_HISTORY_SOURCE_UNAVAILABLE,
                "Nguồn lịch sử giá Tracking chưa được nối: "
                f"{', '.join(missing)} vắng mặt. Nguồn chưa có KHÁC 'sản phẩm "
                "không có giá' — không dùng giá hiện tại thay thế.",
            )

        reconstruction = provider.resolve(line.product_raw, line.date)
        if reconstruction.is_resolved:
            # `price_vnd` ĐÃ được reader quy đổi nghìn VND → VND đúng một lần
            # (`THOUSAND_VND_TO_VND`). Composition KHÔNG nhân lại.
            return self._resolved(
                line,
                key,
                identity,
                CompositionRule.TRACKING_HISTORY_AUTHORITY,
                reconstruction.price_vnd,
                reconstruction=reconstruction,
            )

        reason = reconstruction.reason
        return self._pending(
            line,
            key,
            identity,
            PriceResolutionReason.TRACKING_HISTORY_PENDING,
            "Reader lịch sử giá Tracking trả Pending "
            f"({reason.value if reason else '?'}): "
            f"{reconstruction.provenance.unresolved_detail or ''}",
            reconstruction=reconstruction,
            fallback_blocked_by=PriceResolutionReason.VENDOR_SOURCE_NOT_AUTHORIZED,
            fallback_blocked_detail=VENDOR_SOURCE_NOT_AUTHORIZED_DETAIL,
        )

    def _daily_min_branch(
        self,
        line: WorkingLine,
        key: str,
        identity: CanonicalProductIdentity,
        provider: Optional[TrackingDailyMinProvider],
    ) -> PriceResolutionRecord:
        if provider is None:
            return self._pending(
                line,
                key,
                identity,
                PriceResolutionReason.TRACKING_DAILY_MIN_SOURCE_UNAVAILABLE,
                "Chưa nối ảnh chụp MIN theo ngày của Tracking "
                f"({TRACKING_DAILY_MIN_HINT}). Nguồn CHƯA CÓ khác 'mặt hàng "
                "không có giá' — không giá nào được dựng và không nguồn nào "
                "khác được hỏi thay.",
            )

        resolution = provider.resolve(line.product_raw, line.date)
        if resolution.is_resolved:
            # `price_vnd` ĐÃ được provider quy đổi nghìn VND → VND đúng một lần
            # (`THOUSAND_VND_TO_VND`). Composition KHÔNG nhân lại.
            return self._resolved(
                line,
                key,
                identity,
                CompositionRule.TRACKING_DAILY_MIN,
                resolution.price_vnd,
                daily_min=resolution,
            )

        reason = resolution.reason
        return self._pending(
            line,
            key,
            identity,
            PriceResolutionReason.TRACKING_DAILY_MIN_PENDING,
            "MIN theo ngày bán trả Pending "
            f"({reason.value if reason else '?'}): "
            f"{resolution.provenance.unresolved_detail or ''}",
            daily_min=resolution,
        )

    def _public_purchase_branch(
        self,
        line: WorkingLine,
        key: str,
        identity: CanonicalProductIdentity,
    ) -> PriceResolutionRecord:
        prices = self._public_purchase_prices
        if prices is None:
            return self._pending(
                line,
                key,
                identity,
                PriceResolutionReason.PUBLIC_PURCHASE_SOURCE_UNAVAILABLE,
                "Chưa nối được bảng giá Public Purchase; nguồn chưa có KHÁC "
                "'không có giá tại ngày bán'.",
            )

        # P05 — tra bằng `sale_date`, và bằng `source_product_code` CỦA IDENTITY
        # đã resolve, không phải tên hàng thô (`D-04`/`DEC-147` §4).
        record = prices.find_record(identity.source_product_code, line.date)
        if record is None:
            # P06/P07 — không có khoảng hiệu lực nào phủ ngày bán. Giá hôm nay
            # KHÔNG được kéo ngược về một đơn cũ; `FilePriceProvider` không có
            # nhánh `latest`/`nearest` nào để làm việc đó.
            return self._pending(
                line,
                key,
                identity,
                PriceResolutionReason.PUBLIC_PURCHASE_NO_PRICE_AT_SALE_DATE,
                f"Không có bản ghi giá Public Purchase nào hiệu lực tại "
                f"{line.date.isoformat()} cho {identity}.",
            )
        return self._resolved(
            line,
            key,
            identity,
            CompositionRule.PUBLIC_PURCHASE_DIRECT,
            record.purchase_price,
        )

    # ------------------------------------------------------------------

    def _resolved(
        self,
        line: WorkingLine,
        key: Optional[str],
        identity: Optional[CanonicalProductIdentity],
        rule: CompositionRule,
        price: Decimal,
        *,
        reconstruction: Optional[PriceReconstruction] = None,
        daily_min: Optional[DailyMinResolution] = None,
    ) -> PriceResolutionRecord:
        price_source = PRICE_SOURCE_BY_RULE[rule]
        line.accounting_purchase_price = price
        line.price_source = price_source
        return PriceResolutionRecord(
            order_id=line.order_id,
            raw_product_identity=line.product_raw,
            raw_identity_key=key,
            sale_date=line.date,
            identity=identity,
            status=PriceResolutionStatus.RESOLVED,
            rule=rule,
            price_vnd=price,
            price_source=price_source,
            evidence=self._evidence,
            tracking_reconstruction=reconstruction,
            daily_min_resolution=daily_min,
        )

    def _pending(
        self,
        line: WorkingLine,
        key: Optional[str],
        identity: Optional[CanonicalProductIdentity],
        reason: PriceResolutionReason,
        detail: str,
        *,
        reconstruction: Optional[PriceReconstruction] = None,
        fallback_blocked_by: Optional[PriceResolutionReason] = None,
        fallback_blocked_detail: str = "",
        daily_min: Optional[DailyMinResolution] = None,
    ) -> PriceResolutionRecord:
        line.accounting_purchase_price = None
        line.price_source = PRICE_SOURCE_PENDING
        return PriceResolutionRecord(
            order_id=line.order_id,
            raw_product_identity=line.product_raw,
            raw_identity_key=key,
            sale_date=line.date,
            identity=identity,
            status=PriceResolutionStatus.PENDING,
            rule=CompositionRule.NOT_RESOLVED,
            price_vnd=None,
            price_source=PRICE_SOURCE_PENDING,
            evidence=self._evidence,
            reason=reason,
            detail=detail,
            fallback_blocked_by=fallback_blocked_by,
            fallback_blocked_detail=fallback_blocked_detail,
            tracking_reconstruction=reconstruction,
            daily_min_resolution=daily_min,
        )
