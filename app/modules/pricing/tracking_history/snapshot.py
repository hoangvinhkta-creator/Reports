"""Hợp đồng dữ liệu CHỈ ĐỌC của ảnh chụp giá nhập Tracking — Reader V1.

## Ranh giới kiến trúc

`ADR-101` + `DEC-152` §6, y hệt `TrackingCatalogSnapshot`: phần chạm mạng nằm
NGOÀI `app/modules/` (một công cụ dưới `tools/` đọc RTDB read-only rồi ghi ra
một file bất biến). File này chỉ đọc cấu trúc export đó và **không biết RTDB
tồn tại** — không URL, không client, không import mạng.

## Hai nguồn, hai thẩm quyền thời gian KHÁC NHAU

```text
purchase_price_baseline/cutover     t = Firebase ServerValue.TIMESTAMP
purchase_price_history/<mã>/<eid>   t = ??? (xem dưới)
```

Đây là điểm chết người của cả capability. Mốc cutover được máy chủ đóng dấu.
Sự kiện lịch sử V1 thì **không**: Tracking ghi `Date.now()` của máy trạm. So
`event.t <= sale_time` trên hai thẩm quyền khác nhau là một phép so sai lặng
lẽ — một máy lệch giờ đẩy sự kiện sang phía sai của mốc và cho ra một giá vốn
SAI mà không có gì đỏ lên. Đồng hồ máy trạm không bị chặn trên, nên "thường
chỉ lệch vài giây" KHÔNG phải một bảo đảm và không được dùng làm luận cứ.

Vì thế thẩm quyền là một **thuộc tính có kiểu của từng sự kiện**, không phải
một giả định của thuật toán:

    ta = "SERVER"   → `TimestampAuthority.SERVER`
    thiếu / khác    → `TimestampAuthority.UNVERIFIED_CLIENT`

Nhãn `ta` được Tracking ghi kèm `ServerValue.TIMESTAMP` và được rules
(`purchase_price_history/$ma/$eid/.validate`: `t === now && ta === 'SERVER'`)
kiểm ở phía máy chủ, nên client không tự dán được. Sự kiện ghi TRƯỚC thay đổi
đó không có `ta` và **không được nâng thẩm quyền ngược** — chúng vào
`UNVERIFIED_CLIENT` và reader fail-safe sang Pending. Suy ngược thẩm quyền cho
quá khứ chính là loại "bịa bằng chứng" mà `EVIDENCE_STANDARD` cấm.

## `prices` KHÔNG phải giá hôm nay

`purchase_price_baseline/cutover.prices` là ảnh chụp `board/<mã>/tp/ton` ĐỌC
TRỰC TIẾP từ Firebase tại đúng thời điểm cutover. Nó chỉ chứng minh giá quan
sát được TẠI cutover — không suy ra giá trước đó, và không bao giờ được dùng
làm giá hiện tại backfill ngược cho lịch sử.

## Đơn vị

Mọi con số trong file này là **nghìn VND** (đơn vị gốc của Tracking), giữ
NGUYÊN không đổi. Quy đổi sang VND xảy ra đúng một chỗ, tường minh, ở
`reader.py`. Quy đổi sớm ở đây sẽ làm hai đơn vị trộn vào nhau mà không ai
thấy.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from enum import Enum
from math import isfinite
from typing import Any, Mapping, Optional

from app.modules.product.identity.tracking_catalog import (
    CaptureStatus,
    TrackingCaptureFailedError,
)

__all__ = [
    "CaptureStatus",
    "InvalidTrackingPriceSnapshotError",
    "TimestampAuthority",
    "TrackingCaptureFailedError",
    "TrackingPriceBaseline",
    "TrackingPriceHistoryEvent",
    "TrackingPriceHistorySnapshot",
]

BASELINE_SOURCE_CUTOVER_SNAPSHOT = "cutover_snapshot"
HISTORY_SOURCE_SYNC = "sync"

SERVER_AUTHORITY_MARKER = "SERVER"
"""Giá trị `ta` mà Tracking rules đã kiểm. Chỉ đúng chuỗi này là thẩm quyền."""

MIN_MODERN_EPOCH_MILLIS = 1_000_000_000_000
"""Giới hạn thấp cho timestamp V1 (2001-09-09) để chặn nhầm seconds thành ms.

Mọi dữ liệu của Tracking Price History V1 đều thuộc thời kỳ hiện đại. Một số
epoch theo *seconds* (ví dụ ``1720000000``) vẫn là số hợp lệ về kiểu, nhưng
nếu đem chia 1000 sẽ thành năm 1970 và bị reader bỏ qua như một event trước
cutover — một silent error. Timestamp Firebase ở miền dữ liệu này luôn là
epoch milliseconds, tức ít nhất 13 chữ số.
"""


class TimestampAuthority(str, Enum):
    """Thẩm quyền của MỘT dấu thời gian. Enum ĐÓNG — không có bậc ở giữa.

    Cố ý chỉ hai giá trị. Một bậc thứ ba kiểu `PROBABLY_SERVER` sẽ lập tức
    trở thành chỗ để một phép suy diễn lọt vào: "khoá push() của Firebase có
    nhúng thời gian đã hiệu chỉnh theo máy chủ" là ĐÚNG về mặt SDK nhưng
    KHÔNG được rules kiểm, nên nó là bằng chứng chẩn đoán, không phải thẩm
    quyền. Một dấu thời gian hoặc được máy chủ đóng dấu và kiểm được, hoặc
    không.
    """

    SERVER = "SERVER"
    UNVERIFIED_CLIENT = "UNVERIFIED_CLIENT"


class InvalidTrackingPriceSnapshotError(ValueError):
    """Ảnh chụp tự nó hỏng — TỪ CHỐI nạp, không phải một miss từng dòng.

    Cùng nguyên tắc `InvalidPriceMasterError` (`DEC-145` §5): một ảnh chụp
    mâu thuẫn là khuyết tật của dữ liệu, và engine không giải quyết nó bằng
    cách chọn một bên. `reason` là mã ngắn máy đọc được để test phân biệt
    được luật nào đã nổ mà không phải parse câu văn.
    """

    def __init__(self, message: str, *, reason: str) -> None:
        super().__init__(message)
        self.reason = reason


def _to_utc(millis: Any, *, field: str) -> datetime:
    if isinstance(millis, bool) or not isinstance(millis, (int, float)):
        raise InvalidTrackingPriceSnapshotError(
            f"Trường '{field}' phải là số mili-giây epoch, nhận {millis!r}.",
            reason="invalid_timestamp",
        )
    if isinstance(millis, float) and (
        not isfinite(millis) or not millis.is_integer()
    ):
        raise InvalidTrackingPriceSnapshotError(
            f"Trường '{field}' phải là số nguyên mili-giây epoch, nhận {millis!r}.",
            reason="invalid_timestamp",
        )

    millis_int = int(millis)
    if millis_int < MIN_MODERN_EPOCH_MILLIS:
        raise InvalidTrackingPriceSnapshotError(
            f"Trường '{field}'={millis!r} không nằm trong miền epoch milliseconds "
            "của Tracking Price History V1; có thể dữ liệu seconds bị đọc nhầm "
            "thành milliseconds.",
            reason="invalid_timestamp_unit",
        )
    try:
        return datetime.fromtimestamp(millis_int / 1000, tz=timezone.utc)
    except (OverflowError, OSError, ValueError) as exc:
        raise InvalidTrackingPriceSnapshotError(
            f"Trường '{field}' có epoch milliseconds ngoài miền datetime: {millis!r}.",
            reason="invalid_timestamp",
        ) from exc


def _thousand_vnd(value: Any, *, field: str) -> Decimal:
    """Một con số giá NGHÌN VND. Không chấp nhận chuỗi rỗng, NaN, âm.

    Tracking đã chuẩn hoá `tp/ton` về số qua `numOf()` trước khi ghi, nên một
    giá trị không phải số ở đây là dấu hiệu ảnh chụp hỏng, không phải một
    biến thể định dạng cần đoán.
    """
    if isinstance(value, bool):
        raise InvalidTrackingPriceSnapshotError(
            f"Trường '{field}' là bool ({value!r}) — không phải giá.",
            reason="invalid_price",
        )
    try:
        price = Decimal(str(value))
    except (TypeError, ValueError, InvalidOperation) as exc:
        raise InvalidTrackingPriceSnapshotError(
            f"Trường '{field}' không phải số hợp lệ ({value!r}): {exc}.",
            reason="invalid_price",
        ) from exc
    if not price.is_finite():
        raise InvalidTrackingPriceSnapshotError(
            f"Trường '{field}' không hữu hạn ({price}) — NaN/Infinity không "
            "phải giá.",
            reason="non_finite_price",
        )
    if price < 0:
        raise InvalidTrackingPriceSnapshotError(
            f"Trường '{field}' âm ({price}) — không phải giá hợp lệ.",
            reason="negative_price",
        )
    return price


def _authority_of(raw: Any) -> TimestampAuthority:
    """`ta` → thẩm quyền. Mọi thứ KHÁC `"SERVER"` đều không đủ thẩm quyền.

    Viết theo lối allow-list có chủ đích: một giá trị lạ (`"server"`, `True`,
    một enum mới của Tracking mai này) phải rơi về phía an toàn, không phải
    phía tin tưởng.
    """
    if raw == SERVER_AUTHORITY_MARKER and isinstance(raw, str):
        return TimestampAuthority.SERVER
    return TimestampAuthority.UNVERIFIED_CLIENT


@dataclass(frozen=True)
class TrackingPriceBaseline:
    """`purchase_price_baseline/cutover` — mốc BẤT BIẾN, đúng MỘT bản."""

    cutover_id: str
    captured_at: datetime
    timestamp_authority: TimestampAuthority
    captured_by: str
    source: str
    codes_checked: int
    n_captured: int
    n_absent: int
    n_invalid: int
    prices: Mapping[str, Decimal]
    """`mã → giá NGHÌN VND` quan sát được tại cutover. Vắng mặt = KHÔNG có giá
    hợp lệ được chụp; đó là một sự kiện, không phải giá 0 (`INV-25`)."""

    @property
    def has_invalid_entries(self) -> bool:
        """Có mã nào bị bỏ qua vì giá hỏng không.

        Quan trọng: nếu có, thì "vắng mặt trong `prices`" trở nên NHẬP NHẰNG —
        không phân biệt được "board không có giá" với "board có giá nhưng
        hỏng". Reader phải fail-safe cho MỌI mã vắng mặt khi cờ này bật.
        """
        return self.n_invalid > 0


@dataclass(frozen=True)
class TrackingPriceHistoryEvent:
    """`purchase_price_history/<mã>/<eid>` — một sự kiện append-only.

    `next = None` nghĩa là giá bị XOÁ (mã hết hàng, cột Tồn bị gỡ), KHÔNG
    phải giá 0 và KHÔNG phải "giữ giá cũ".
    """

    product_code: str
    event_id: str
    previous_value: Optional[Decimal]  # nghìn VND
    next_value: Optional[Decimal]  # nghìn VND
    occurred_at: datetime
    timestamp_authority: TimestampAuthority
    written_by: str
    source: str

    @property
    def is_authoritative(self) -> bool:
        return self.timestamp_authority is TimestampAuthority.SERVER


@dataclass(frozen=True)
class TrackingPriceHistorySnapshot:
    """Ảnh chụp bất biến: mốc cutover + toàn bộ sự kiện lịch sử.

    `capture_status = FAILED` là LỖI CỨNG, không phải "không có dữ liệu"
    (`INV-12`): một lần capture hỏng và một lịch sử thật sự rỗng là hai sự
    kiện khác nhau, và trộn chúng lại thì mọi sản phẩm trở thành Pending sau
    một lần mất mạng — tệ hơn nữa là nó trông y hệt một kết luận về dữ liệu.
    """

    capture_id: str
    captured_at: datetime
    captured_by: str
    source_system_ref: str
    capture_status: CaptureStatus
    baseline: Optional[TrackingPriceBaseline] = None
    events: tuple[TrackingPriceHistoryEvent, ...] = ()
    failure_reason: Optional[str] = None

    def __post_init__(self) -> None:
        if self.capture_status is CaptureStatus.FAILED and not self.failure_reason:
            raise InvalidTrackingPriceSnapshotError(
                "capture_status = FAILED bắt buộc có failure_reason.",
                reason="failed_without_reason",
            )

    def require_complete(self) -> "TrackingPriceHistorySnapshot":
        """`INV-12` — cổng vào DUY NHẤT cho mọi đường đọc ảnh chụp."""
        if self.capture_status is not CaptureStatus.COMPLETE:
            raise TrackingCaptureFailedError(
                f"capture {self.capture_id} có capture_status="
                f"{self.capture_status.value} ({self.failure_reason}); reader "
                "từ chối chạy — đây là LỖI, không phải Pending (INV-12)"
            )
        return self

    def events_for(self, product_code: str) -> tuple[TrackingPriceHistoryEvent, ...]:
        """Mọi sự kiện của MỘT mã, giữ nguyên thứ tự dòng của ảnh chụp.

        KHÔNG sắp xếp ở đây: sắp xếp là một quyết định ngữ nghĩa của reader
        (và reader phải xử lý trùng dấu thời gian một cách tường minh chứ
        không để một `sorted()` ổn định âm thầm chọn hộ).
        """
        return tuple(e for e in self.events if e.product_code == product_code)

    # -----------------------------------------------------------------
    # Nạp từ export (JSON dump của cây RTDB). Kiểm toàn bộ MỘT LẦN, sớm.
    # -----------------------------------------------------------------

    @classmethod
    def from_export(
        cls,
        data: Mapping[str, Any],
        *,
        capture_id: str,
        captured_at: datetime,
        captured_by: str,
        source_system_ref: str,
        capture_status: CaptureStatus = CaptureStatus.COMPLETE,
        failure_reason: Optional[str] = None,
    ) -> "TrackingPriceHistorySnapshot":
        """Dựng ảnh chụp từ hai nhánh RTDB đã export.

        `data` mang đúng hình dạng của cây: `purchase_price_baseline` và
        `purchase_price_history`. Provenance của chính lần capture
        (`capture_id`, `captured_at`, ...) đến TỪ công cụ capture, không suy
        ra từ nội dung — nội dung không tự chứng minh được nó được chụp lúc
        nào.
        """
        if capture_status is CaptureStatus.FAILED:
            return cls(
                capture_id=capture_id,
                captured_at=captured_at,
                captured_by=captured_by,
                source_system_ref=source_system_ref,
                capture_status=capture_status,
                failure_reason=failure_reason,
            )

        baseline_node = (data.get("purchase_price_baseline") or {}).get("cutover")
        baseline = _parse_baseline(baseline_node) if baseline_node else None
        events = _parse_events(data.get("purchase_price_history") or {})
        return cls(
            capture_id=capture_id,
            captured_at=captured_at,
            captured_by=captured_by,
            source_system_ref=source_system_ref,
            capture_status=capture_status,
            baseline=baseline,
            events=events,
        )


def _parse_baseline(node: Mapping[str, Any]) -> TrackingPriceBaseline:
    captured_at = _to_utc(node.get("t"), field="purchase_price_baseline/cutover.t")
    raw_prices = node.get("prices") or {}
    prices = {
        str(code): _thousand_vnd(value, field=f"prices/{code}")
        for code, value in raw_prices.items()
    }

    n = node.get("n")
    n_cap = node.get("nCap")
    n_absent = node.get("nAbsent")
    n_invalid = node.get("nInvalid")
    for name, value in (
        ("n", n), ("nCap", n_cap), ("nAbsent", n_absent), ("nInvalid", n_invalid)
    ):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise InvalidTrackingPriceSnapshotError(
                f"Mốc cutover: '{name}' phải là số nguyên >= 0, nhận {value!r}.",
                reason="invalid_counter",
            )

    # Ba con số phải cộng đúng bằng tổng. Nếu không, ảnh chụp mâu thuẫn với
    # chính nó và ta không biết mã vắng mặt thuộc nhóm nào — chính xác cái
    # nhập nhằng sẽ biến thành một giá sai ở tầng dưới.
    if n_cap + n_absent + n_invalid != n:
        raise InvalidTrackingPriceSnapshotError(
            f"Mốc cutover mâu thuẫn: nCap({n_cap}) + nAbsent({n_absent}) + "
            f"nInvalid({n_invalid}) != n({n}).",
            reason="counter_mismatch",
        )
    if len(prices) != n_cap:
        raise InvalidTrackingPriceSnapshotError(
            f"Mốc cutover mâu thuẫn: số giá thật ({len(prices)}) != nCap "
            f"({n_cap}).",
            reason="price_count_mismatch",
        )

    return TrackingPriceBaseline(
        cutover_id="cutover",
        captured_at=captured_at,
        # Mốc cutover được ghi bằng `ServerValue.TIMESTAMP` và rules chỉ cho
        # tạo MỘT lần khi chưa tồn tại; `admBaselineSnapshot()` còn đọc lại và
        # từ chối nếu máy chủ chưa xác nhận `t` là số. Đó là thẩm quyền máy chủ
        # đã được chứng minh tại nguồn — khác hẳn `t` của history V1.
        timestamp_authority=TimestampAuthority.SERVER,
        captured_by=str(node.get("by") or "?"),
        source=str(node.get("src") or ""),
        codes_checked=n,
        n_captured=n_cap,
        n_absent=n_absent,
        n_invalid=n_invalid,
        prices=prices,
    )


def _parse_events(
    node: Mapping[str, Any],
) -> tuple[TrackingPriceHistoryEvent, ...]:
    events: list[TrackingPriceHistoryEvent] = []
    for code, by_event in (node or {}).items():
        for event_id, raw in (by_event or {}).items():
            field = f"purchase_price_history/{code}/{event_id}"
            prev = raw.get("prev")
            nxt = raw.get("next")
            events.append(
                TrackingPriceHistoryEvent(
                    product_code=str(code),
                    event_id=str(event_id),
                    previous_value=(
                        None if prev is None
                        else _thousand_vnd(prev, field=field + ".prev")
                    ),
                    next_value=(
                        None if nxt is None
                        else _thousand_vnd(nxt, field=field + ".next")
                    ),
                    occurred_at=_to_utc(raw.get("t"), field=field + ".t"),
                    timestamp_authority=_authority_of(raw.get("ta")),
                    written_by=str(raw.get("by") or "?"),
                    source=str(raw.get("src") or ""),
                )
            )
    return tuple(events)
