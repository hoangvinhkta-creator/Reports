"""Reports History Reader V1 — dựng lại giá nhập Tracking tại thời điểm bán.

## Mục tiêu KHÔNG phải là độ phủ

Ưu tiên duy nhất là `SILENT_ERROR_RATE = 0`. Khi bằng chứng không đủ, kết quả
là `PENDING` kèm lý do có kiểu — không bao giờ là một con số "gần đúng". Một
Pending làm người ta phải xem lại một đơn; một giá vốn sai lặng lẽ đi thẳng
vào lương và không ai biết. Reader này luôn chọn cái thứ nhất.

## Hai trục thời gian không cùng độ phân giải — và vì sao đó là một CỔNG

Tracking đóng dấu sự kiện theo **mili-giây**. Reports chỉ biết `sale_date`
theo **NGÀY** (`WorkingLine.date` là `datetime.date`, không có giờ). Ép một
ngày thành một thời điểm là phát minh dữ liệu: chọn 00:00 hay 23:59 đều đổi
kết quả khi có một sự kiện giá rơi vào giữa ngày ấy.

Nên reader **không** nhận một thời điểm, nó nhận một `SaleInterval` — khoảng
bất định thật của lần bán. Một ngày bán là `[00:00 ngày đó, 00:00 hôm sau)`
theo múi giờ nghiệp vụ; một thời điểm chính xác là khoảng suy biến `lo == hi`.
Reader chỉ trả giá khi trạng thái giá **hằng trên TOÀN khoảng**. Có sự kiện
rơi vào trong khoảng → Pending. Đây là cách duy nhất trả lời đúng mà không
phải đoán giờ trong ngày.

Múi giờ nghiệp vụ **không có giá trị mặc định** ở đây (`SaleInterval.for_sale_date`
bắt buộc truyền `tzinfo`). Một mặc định là một giả định thầm lặng, và lệch múi
giờ đúng bằng cách đẩy biên ngày qua một sự kiện.

## Vì sao một sự kiện KHÔNG đủ thẩm quyền làm hỏng cả mã, không chỉ chính nó

Dấu thời gian của một sự kiện `UNVERIFIED_CLIENT` là đồng hồ máy trạm — không
bị chặn trên và không bị chặn dưới. Ta không biết nó THẬT SỰ xảy ra lúc nào,
nên nó có thể nằm ở BẤT KỲ đâu trên trục, kể cả bên trong khoảng bán đang hỏi.
Không có cách nào loại trừ nó mà không giả định về sai số đồng hồ — điều bị
cấm tường minh. Vì thế: mã nào có dù chỉ một sự kiện không đủ thẩm quyền thì
toàn bộ đường tái dựng của mã đó là Pending.

Hệ quả là mọi sự kiện ghi TRƯỚC bản vá thẩm quyền phía Tracking đều không đủ
thẩm quyền, vĩnh viễn. Đó là đáp án ĐÚNG, không phải một hạn chế cần lách:
nâng thẩm quyền ngược cho quá khứ là bịa bằng chứng.

## Khoá chuỗi `prev` — cái bẫy im lặng cuối cùng

Mỗi sự kiện mang `prev` = giá trị `tp/ton` mà Tracking QUAN SÁT được ngay
trước khi ghi. Nếu `prev` của một sự kiện không khớp trạng thái ta dựng được,
thì đã có một lần đổi giá KHÔNG đi qua lịch sử (sửa board bằng đường khác).
Khi đó đường tái dựng có một lỗ hổng — và đó đúng là loại lỗ hổng sinh ra một
con số sai trông rất bình thường. Reader khoá chuỗi và trả Pending.

Phạm vi khoá chuỗi được cắt đúng bằng phạm vi ảnh hưởng: từ mốc cutover tới
**sự kiện đầu tiên sau khoảng bán**. Sự kiện ấy xác nhận trạng thái đã giữ
nguyên xuyên qua khoảng bán. Một chuỗi gãy ở tháng 12 không nói gì về một đơn
tháng 9, nên nó không được làm hỏng đơn tháng 9.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date as _date, datetime, time as _time, timedelta, tzinfo
from decimal import Decimal
from enum import Enum
from typing import Optional

from app.modules.pricing.tracking_history.snapshot import (
    TimestampAuthority,
    TrackingPriceBaseline,
    TrackingPriceHistoryEvent,
    TrackingPriceHistorySnapshot,
)

__all__ = [
    "DecisiveSource",
    "PriceReconstruction",
    "ReconstructionStatus",
    "SaleInterval",
    "THOUSAND_VND_TO_VND",
    "TrackingPriceHistoryReader",
    "TrackingPriceProvenance",
    "UNIT_CONVERSION_LABEL",
    "UnresolvedReason",
]

THOUSAND_VND_TO_VND = Decimal(1000)
"""Giá Tracking tính bằng NGHÌN VND; Reports lưu VND thô (`ADR-103`).

Hằng số đứng riêng, có tên, dùng đúng MỘT lần trong `reader.py`. Không có
phép nhân 1000 thứ hai ở bất kỳ đâu trong package này — hai chỗ quy đổi là
hai chỗ để quên một chỗ.
"""

UNIT_CONVERSION_LABEL = "thousand_VND × 1000 → VND"

TRACKING_NAMESPACE = "TRACKING"


class ReconstructionStatus(str, Enum):
    RESOLVED = "RESOLVED"
    PENDING = "PENDING"


class DecisiveSource(str, Enum):
    """Nguồn ĐÃ QUYẾT ĐỊNH con số trả về (hoặc quyết định là không có số)."""

    BASELINE = "BASELINE"
    HISTORY_EVENT = "HISTORY_EVENT"
    NONE = "NONE"


class UnresolvedReason(str, Enum):
    """Enum ĐÓNG. Mỗi lý do là một CÂU KHẲNG ĐỊNH kiểm được, không phải câu văn.

    Không có giá trị `UNKNOWN`: một nhánh không biết gọi tên mình là một nhánh
    chưa được nghĩ tới, và nó phải làm test đỏ chứ không được trôi qua.
    """

    SNAPSHOT_HAS_NO_BASELINE = "SNAPSHOT_HAS_NO_BASELINE"
    BASELINE_NOT_AUTHORITATIVE = "BASELINE_NOT_AUTHORITATIVE"
    SALE_BEFORE_CUTOVER = "SALE_BEFORE_CUTOVER"
    HISTORY_PROVENANCE_NOT_AUTHORITATIVE = "HISTORY_PROVENANCE_NOT_AUTHORITATIVE"
    EVENT_AT_CUTOVER_INSTANT = "EVENT_AT_CUTOVER_INSTANT"
    NON_DETERMINISTIC_EVENT_ORDER = "NON_DETERMINISTIC_EVENT_ORDER"
    PRICE_CHANGED_WITHIN_SALE_INTERVAL = "PRICE_CHANGED_WITHIN_SALE_INTERVAL"
    HISTORY_CHAIN_INCONSISTENT = "HISTORY_CHAIN_INCONSISTENT"
    SNAPSHOT_DOES_NOT_COVER_SALE_INTERVAL = (
        "SNAPSHOT_DOES_NOT_COVER_SALE_INTERVAL"
    )
    PRICE_CLEARED = "PRICE_CLEARED"
    NO_BASELINE_PRICE_AT_CUTOVER = "NO_BASELINE_PRICE_AT_CUTOVER"
    BASELINE_ABSENCE_AMBIGUOUS = "BASELINE_ABSENCE_AMBIGUOUS"
    IDENTITY_NOT_TRACKING = "IDENTITY_NOT_TRACKING"
    IDENTITY_UNRESOLVED = "IDENTITY_UNRESOLVED"
    SALE_DATE_MISSING = "SALE_DATE_MISSING"


@dataclass(frozen=True)
class SaleInterval:
    """Khoảng bất định `[lo, hi)` chứa thời điểm bán thật.

    `hi == lo` là khoảng suy biến — một thời điểm biết chính xác. Hai đầu bắt
    buộc **aware** (có múi giờ): so một datetime naive với một mốc UTC là đúng
    kiểu lỗi mà cả capability này sinh ra để chặn.
    """

    lo: datetime
    hi: datetime

    def __post_init__(self) -> None:
        for name, value in (("lo", self.lo), ("hi", self.hi)):
            if value.tzinfo is None or value.tzinfo.utcoffset(value) is None:
                raise ValueError(
                    f"SaleInterval.{name} phải là datetime AWARE (có múi giờ); "
                    f"nhận naive {value!r}"
                )
        if self.hi < self.lo:
            raise ValueError(f"SaleInterval đảo ngược: hi({self.hi}) < lo({self.lo})")

    @classmethod
    def at_instant(cls, moment: datetime) -> "SaleInterval":
        """Thời điểm bán biết chính xác tới mili-giây."""
        return cls(lo=moment, hi=moment)

    @classmethod
    def for_sale_date(cls, sale_date: _date, business_tz: tzinfo) -> "SaleInterval":
        """Một NGÀY bán → khoảng `[00:00, 00:00 hôm sau)` theo múi giờ nghiệp vụ.

        `business_tz` là tham số BẮT BUỘC, không có mặc định: một mặc định sai
        dịch biên ngày đi vài giờ và đẩy nó qua bên kia một sự kiện giá.
        """
        lo = datetime.combine(sale_date, _time.min, tzinfo=business_tz)
        hi = datetime.combine(sale_date + timedelta(days=1), _time.min, tzinfo=business_tz)
        return cls(lo=lo, hi=hi)

    @property
    def is_instant(self) -> bool:
        return self.lo == self.hi


@dataclass(frozen=True)
class TrackingPriceProvenance:
    """Đủ để một người mở lại và kiểm từng bước — không phải một nhãn.

    Cố ý mang CẢ `raw_value_thousand_vnd` lẫn `resolved_price_vnd`: người đọc
    thấy được phép quy đổi đã xảy ra, chứ không phải tin rằng nó đã xảy ra.
    """

    product_code: Optional[str]
    """Mã Tracking đã quyết định giá. `None` khi chưa resolve được identity —
    và khi đó KHÔNG được điền chuỗi raw vào đây: raw product name không phải
    một Tracking code, và một trường tên `product_code` chứa tên hàng sẽ bị
    đọc như một mã ở tầng dưới."""

    namespace: Optional[str]
    sale_interval_start: datetime
    sale_interval_end: datetime
    snapshot_capture_id: str
    baseline_cutover_id: Optional[str]
    baseline_captured_at: Optional[datetime]
    baseline_timestamp_authority: Optional[TimestampAuthority]
    decisive_source: DecisiveSource
    decisive_event_id: Optional[str] = None
    decisive_source_timestamp: Optional[datetime] = None
    decisive_timestamp_authority: Optional[TimestampAuthority] = None
    raw_value_thousand_vnd: Optional[Decimal] = None
    unit_conversion: str = UNIT_CONVERSION_LABEL
    resolved_price_vnd: Optional[Decimal] = None
    events_seen_for_code: int = 0
    raw_product_identity: Optional[str] = None
    unresolved_reason: Optional[UnresolvedReason] = None
    unresolved_detail: Optional[str] = None


@dataclass(frozen=True)
class PriceReconstruction:
    """Kết quả reader. Một con số KHÔNG bao giờ đi một mình.

    `price_vnd` chỉ khác `None` khi `status is RESOLVED`; và `RESOLVED` chỉ
    tồn tại khi có một con số. Bất biến ấy được `__post_init__` kiểm, không
    phải được hứa trong tài liệu.
    """

    status: ReconstructionStatus
    provenance: TrackingPriceProvenance
    price_vnd: Optional[Decimal] = None
    reason: Optional[UnresolvedReason] = None

    def __post_init__(self) -> None:
        if self.status is ReconstructionStatus.RESOLVED:
            if self.price_vnd is None or self.reason is not None:
                raise ValueError(
                    "RESOLVED bắt buộc có price_vnd và KHÔNG có reason"
                )
        else:
            if self.price_vnd is not None or self.reason is None:
                raise ValueError(
                    "PENDING bắt buộc có reason và KHÔNG BAO GIỜ mang price_vnd "
                    "(INV-25: Pending không phải 0, không phải giá cũ)"
                )

    @property
    def is_resolved(self) -> bool:
        return self.status is ReconstructionStatus.RESOLVED


class TrackingPriceHistoryReader:
    """Tái dựng `board/<mã>/tp/ton` tại một khoảng bán, hoặc Pending.

    Thuần đọc: không lệnh, không ghi, không trạng thái tích luỹ. Cùng ảnh chụp
    + cùng đầu vào ⇒ cùng đầu ra, mọi lần.
    """

    def __init__(self, snapshot: TrackingPriceHistorySnapshot) -> None:
        self._snapshot = snapshot.require_complete()

    @property
    def snapshot(self) -> TrackingPriceHistorySnapshot:
        return self._snapshot

    # ------------------------------------------------------------------

    def price_at(self, product_code: str, interval: SaleInterval) -> PriceReconstruction:
        snap = self._snapshot
        baseline = snap.baseline
        events = snap.events_for(product_code)

        def prov(
            decisive_source: DecisiveSource = DecisiveSource.NONE,
            **kw,
        ) -> TrackingPriceProvenance:
            return TrackingPriceProvenance(
                product_code=product_code,
                namespace=TRACKING_NAMESPACE,
                sale_interval_start=interval.lo,
                sale_interval_end=interval.hi,
                snapshot_capture_id=snap.capture_id,
                baseline_cutover_id=baseline.cutover_id if baseline else None,
                baseline_captured_at=baseline.captured_at if baseline else None,
                baseline_timestamp_authority=(
                    baseline.timestamp_authority if baseline else None
                ),
                decisive_source=decisive_source,
                events_seen_for_code=len(events),
                **kw,
            )

        def pending(reason: UnresolvedReason, detail: str, **kw) -> PriceReconstruction:
            return PriceReconstruction(
                status=ReconstructionStatus.PENDING,
                reason=reason,
                provenance=prov(
                    unresolved_reason=reason, unresolved_detail=detail, **kw
                ),
            )

        # --- 1. Mốc cutover phải tồn tại và phải đủ thẩm quyền -------------
        if baseline is None:
            return pending(
                UnresolvedReason.SNAPSHOT_HAS_NO_BASELINE,
                "Ảnh chụp không có purchase_price_baseline/cutover — không có "
                "điểm neo nào để dựng lại lịch sử.",
            )
        if baseline.timestamp_authority is not TimestampAuthority.SERVER:
            return pending(
                UnresolvedReason.BASELINE_NOT_AUTHORITATIVE,
                f"Mốc cutover có thẩm quyền {baseline.timestamp_authority.value}; "
                "chỉ SERVER mới đủ để làm gốc trục thời gian.",
            )

        t0 = baseline.captured_at

        # --- 2. CASE A — bán TRƯỚC cutover ---------------------------------
        # Biên chính xác: `sale_time == baseline.t` KHÔNG rơi vào nhánh này.
        # Mốc cutover là ảnh chụp CÓ HIỆU LỰC TẠI chính thời điểm của nó, nên
        # nó phủ được đúng thời điểm ấy. Chỉ phần TRƯỚC nó là vùng mà baseline
        # không chứng minh được gì (`INV-15`: không viết lại lịch sử bằng danh
        # mục hôm nay). Với một khoảng bán theo NGÀY, chỉ cần MỘT phần của
        # ngày nằm trước cutover là cả ngày mất thẩm quyền — ta không biết đơn
        # rơi vào nửa nào.
        if interval.lo < t0:
            return pending(
                UnresolvedReason.SALE_BEFORE_CUTOVER,
                f"Khoảng bán bắt đầu {interval.lo.isoformat()} < mốc cutover "
                f"{t0.isoformat()}; trước cutover baseline/history V1 không "
                "chứng minh được giá lịch sử.",
            )

        # Capture là biên thẩm quyền trên của chính export. Dù baseline hay
        # history nói trạng thái nào trước đó, một capture kết thúc trước `hi`
        # không loại trừ một thay đổi chưa được quan sát trong phần còn lại của
        # khoảng bán. `hi` là đầu mở, nên capture tại đúng `hi` là đủ.
        if snap.captured_at < interval.hi:
            return pending(
                UnresolvedReason.SNAPSHOT_DOES_NOT_COVER_SALE_INTERVAL,
                f"Capture {snap.capture_id} lúc {snap.captured_at.isoformat()} "
                f"kết thúc trước cuối khoảng bán {interval.hi.isoformat()}; "
                "không được ngoại suy giá qua terminal authority gap.",
            )

        # --- 3. CASE F — thẩm quyền thời gian của lịch sử ------------------
        unverified = [e for e in events if not e.is_authoritative]
        if unverified:
            return pending(
                UnresolvedReason.HISTORY_PROVENANCE_NOT_AUTHORITATIVE,
                f"{len(unverified)}/{len(events)} sự kiện của mã có thẩm quyền "
                "thời gian không phải SERVER (thiếu nhãn ta='SERVER'). Dấu thời "
                "gian máy trạm không bị chặn nên sự kiện có thể rơi vào bất kỳ "
                "đâu, kể cả trong khoảng bán.",
            )

        # --- 4. Biên chính xác: sự kiện ĐÚNG TẠI thời điểm cutover ---------
        # Ảnh chụp cutover đọc `board` một lần; một sự kiện mang đúng dấu thời
        # gian ấy có thể đã hoặc chưa nằm trong lần đọc đó. Không có bằng
        # chứng nào phân định, nên không đoán.
        at_cutover = [e for e in events if e.occurred_at == t0]
        if at_cutover:
            return pending(
                UnresolvedReason.EVENT_AT_CUTOVER_INSTANT,
                f"{len(at_cutover)} sự kiện có dấu thời gian TRÙNG KHÍT mốc "
                f"cutover {t0.isoformat()}; không xác định được ảnh chụp đã "
                "gồm hay chưa gồm thay đổi đó.",
            )

        # Sự kiện TRƯỚC cutover bị chính ảnh chụp cutover thay thế: baseline là
        # một lần đọc THẲNG board tại t0, nên nó đã bao gồm mọi thay đổi trước
        # đó. Chúng không tham gia chuỗi.
        after = sorted(
            (e for e in events if e.occurred_at > t0), key=lambda e: e.occurred_at
        )

        # --- 5. Biên chính xác: nhiều sự kiện TRÙNG dấu thời gian ----------
        # Chỉ bằng dấu thời gian thì không có thứ tự xác định giữa chúng, và
        # `sorted()` sẽ âm thầm chọn hộ theo thứ tự dòng của ảnh chụp — đúng
        # loại heuristic bị cấm. Không có bằng chứng thứ tự nào khác trong
        # schema V1, nên fail-safe.
        for earlier, later in zip(after, after[1:]):
            if earlier.occurred_at == later.occurred_at:
                return pending(
                    UnresolvedReason.NON_DETERMINISTIC_EVENT_ORDER,
                    f"Hai sự kiện ({earlier.event_id}, {later.event_id}) cùng mã "
                    f"trùng dấu thời gian {later.occurred_at.isoformat()}; "
                    "schema V1 không mang bằng chứng thứ tự nào khác.",
                )

        # --- 6. Có thay đổi giá RƠI VÀO TRONG khoảng bán -------------------
        # Biên chính xác: `event.t == interval.lo` KHÔNG nằm trong nhánh này —
        # sự kiện có hiệu lực TẠI chính thời điểm của nó (cùng quy ước với
        # baseline ở bước 2), nên trạng thái vẫn hằng trên [lo, hi).
        # `event.t == interval.hi` cũng không: `hi` là đầu MỞ.
        inside = [e for e in after if interval.lo < e.occurred_at < interval.hi]
        if inside:
            return pending(
                UnresolvedReason.PRICE_CHANGED_WITHIN_SALE_INTERVAL,
                f"{len(inside)} thay đổi giá xảy ra TRONG khoảng bán "
                f"[{interval.lo.isoformat()}, {interval.hi.isoformat()}); "
                "Reports chỉ biết ngày bán, không biết giờ, nên không xác định "
                "được đơn nằm bên nào của thay đổi.",
            )

        # --- 7. Trạng thái gốc tại cutover --------------------------------
        state = baseline.prices.get(product_code)
        if state is None and baseline.has_invalid_entries:
            # Mã vắng mặt trong `prices` có thể vì board không có giá, hoặc vì
            # giá ở board hỏng và bị bỏ qua. `nInvalid > 0` làm hai khả năng ấy
            # không phân biệt được, và một "coi như chưa có giá" ở đây là một
            # suy diễn. (Ảnh chụp production có nInvalid = 0.)
            return pending(
                UnresolvedReason.BASELINE_ABSENCE_AMBIGUOUS,
                f"Mã vắng mặt trong baseline.prices và mốc cutover có "
                f"nInvalid={baseline.n_invalid} > 0; không phân biệt được "
                "'không có giá' với 'giá hỏng bị bỏ qua'.",
            )

        # --- 8. Khoá chuỗi `prev`, đúng phạm vi ảnh hưởng ------------------
        # Duyệt tới sự kiện ĐẦU TIÊN sau `interval.lo` (đã chắc chắn nằm ở
        # >= hi nhờ bước 6): sự kiện ấy xác nhận trạng thái đã giữ nguyên
        # xuyên qua khoảng bán. Xa hơn nữa không nói gì về khoảng này.
        decisive: Optional[TrackingPriceHistoryEvent] = None
        for event in after:
            if event.previous_value != state:
                return pending(
                    UnresolvedReason.HISTORY_CHAIN_INCONSISTENT,
                    f"Sự kiện {event.event_id} khai prev={event.previous_value} "
                    f"nhưng trạng thái dựng được là {state}; đã có một lần đổi "
                    "giá KHÔNG đi qua lịch sử — đường tái dựng có lỗ hổng.",
                )
            if event.occurred_at > interval.lo:
                break  # đã xác nhận xuyên khoảng bán; không áp vào trạng thái
            state = event.next_value
            decisive = event

        # --- 9. Kết luận ---------------------------------------------------
        if decisive is None:
            # CASE B — baseline quyết định. CASE E (mã không có baseline và
            # chưa có sự kiện nào tạo trạng thái hợp lệ) rơi vào đây.
            if state is None:
                return pending(
                    UnresolvedReason.NO_BASELINE_PRICE_AT_CUTOVER,
                    "Mã không có giá tại mốc cutover và chưa có sự kiện đủ "
                    "thẩm quyền nào tạo ra trạng thái giá trước khoảng bán.",
                )
            return self._resolved(
                prov,
                raw=state,
                source=DecisiveSource.BASELINE,
                event=None,
                baseline_at=t0,
            )

        # CASE C / CASE E sau sự kiện đầu tiên — sự kiện quyết định.
        if state is None:
            # CASE D — trạng thái cuối cùng trước khoảng bán là `next = null`
            # (giá bị XOÁ). KHÔNG dùng giá cũ, KHÔNG dùng 0.
            return pending(
                UnresolvedReason.PRICE_CLEARED,
                f"Sự kiện {decisive.event_id} lúc "
                f"{decisive.occurred_at.isoformat()} xoá giá (next=null); giá "
                "cũ đã hết hiệu lực và 0 không phải một giá.",
                decisive_source=DecisiveSource.HISTORY_EVENT,
                decisive_event_id=decisive.event_id,
                decisive_source_timestamp=decisive.occurred_at,
                decisive_timestamp_authority=decisive.timestamp_authority,
            )
        return self._resolved(
            prov,
            raw=state,
            source=DecisiveSource.HISTORY_EVENT,
            event=decisive,
            baseline_at=t0,
        )

    # ------------------------------------------------------------------

    @staticmethod
    def _resolved(
        prov,
        *,
        raw: Decimal,
        source: DecisiveSource,
        event: Optional[TrackingPriceHistoryEvent],
        baseline_at: datetime,
    ) -> PriceReconstruction:
        """CHỖ DUY NHẤT quy đổi nghìn VND → VND trong toàn package."""
        price_vnd = raw * THOUSAND_VND_TO_VND
        return PriceReconstruction(
            status=ReconstructionStatus.RESOLVED,
            price_vnd=price_vnd,
            provenance=prov(
                decisive_source=source,
                decisive_event_id=event.event_id if event else None,
                decisive_source_timestamp=(
                    event.occurred_at if event else baseline_at
                ),
                decisive_timestamp_authority=(
                    event.timestamp_authority if event else TimestampAuthority.SERVER
                ),
                raw_value_thousand_vnd=raw,
                resolved_price_vnd=price_vnd,
            ),
        )
