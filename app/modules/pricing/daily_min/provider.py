"""`TrackingDailyMinProvider` — tra giá MIN bằng NGÀY BÁN, không bằng ngày chạy.

## Đây là toàn bộ lý do capability này tồn tại

Owner nạp sổ kế toán vào cuối tháng. Một đơn bán ngày 03/09 phải được tính
bằng giá vốn của ĐÚNG ngày 03/09, kể cả khi file được nạp ngày 30/09 và kể cả
khi bảng giá đã đổi mười lần ở giữa. Provider này không có bất kỳ nhánh nào
đọc "giá hiện tại", "giá mới nhất", hay "giá gần nhất còn tìm thấy": nó tra
đúng một khoá `(mã Tracking, ngày bán)` trong ảnh chụp, và không có khoá thì
Pending.

## Không fallback — và đây là danh sách những thứ CỐ Ý không tồn tại

```text
KHÔNG lấy bản của ngày sau ngày bán
KHÔNG lấy bản mới nhất tại thời điểm chạy
KHÔNG rơi về `TrackingPriceHistory` (lịch sử `board/<mã>/tp/ton`)
KHÔNG rơi về bảng giá Public Purchase
KHÔNG coi `OUT_OF_STOCK` là giá 0
```

Việc MANG MỘT MỐC QUA các ngày không đổi giá có tồn tại, nhưng nó xảy ra ở
PHÍA TRACKING và chỉ khi Tracking chứng minh được đã quan sát bảng giá mọi
ngày ở giữa (`carried_from` trong hợp đồng). Reports không tự suy ra điều đó
và không có mã nào ở đây làm việc ấy — nếu có, một khoảng thời gian hệ thống
ngừng chạy sẽ được lấp bằng giá cũ và không ai biết.

## Provider KHÔNG resolve identity — nó ĐƯỢC TRAO identity

Cùng ranh giới đã lập ở `TrackingHistoryPriceProvider`: thứ đi vào từ
`WorkingLine` là **tên hàng kế toán thô**, không phải một mã Tracking. Biến
tên hàng thành mã là việc của `TASK-105D` và nó có cả một data contract để
không làm sai; suy ra mã bằng chuỗi ở đây là đúng thứ `D-04`/`DEC-147` §4 đã
cấm sau khi Tracking trả giá cho nó trên tài sản thật.

Nên provider nhận một `identity_index` do caller cung cấp. Không có entry →
`IDENTITY_UNRESOLVED`. Có entry nhưng namespace là `PUBLIC_PURCHASE` →
`IDENTITY_NOT_TRACKING`, và ảnh chụp **không** được hỏi: một mã trùng chuỗi ở
hai namespace là hai identity khác nhau (`INV-18`).

## Quy đổi nghìn VND → VND đúng MỘT lần, ở đây

`THOUSAND_VND_TO_VND` được dùng đúng một lần trong package này. Hợp đồng giữ
nguyên đơn vị của Tracking; phép nhân nằm ở `_resolved()`. Hai chỗ quy đổi là
hai chỗ để quên một chỗ — và quên một chỗ là sai đúng 1.000 lần, sai đều nên
nhìn bảng không phát hiện ra.

## Vì sao có `audit_trail`

`WorkingLine` không có chỗ cho provenance. Provider giữ lại `DailyMinResolution`
đầy đủ của MỌI lần tra, kể cả Pending, để người kiểm mở lại được từng dòng:
nguồn nào giữ MIN, revision nào, luật phiên bản nào, ngày đó đã chốt chưa.
`lookup()` trả một `Decimal`; `audit_trail` giữ phần còn lại.
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
from typing import Mapping, Optional

from app.modules.domain.models import PRICE_SOURCE_TRACKING_DAILY_MIN
from app.modules.pricing.daily_min.snapshot import (
    DailyMinRecord,
    DailyMinSnapshot,
    DayStatus,
    MissingReason,
    PriceStatus,
)
from app.modules.product.identity.identity import (
    CanonicalProductIdentity,
    Namespace,
)
from app.modules.product.identity.keys import (
    EmptyRawIdentityError,
    raw_identity_key,
)

__all__ = [
    "DailyMinResolution",
    "DailyMinStatus",
    "DailyMinProvenance",
    "DailyMinUnresolvedReason",
    "THOUSAND_VND_TO_VND",
    "TrackingDailyMinProvider",
    "UNIT_CONVERSION_LABEL",
]

THOUSAND_VND_TO_VND = Decimal(1000)
"""Giá Tracking tính bằng NGHÌN VND; Reports lưu VND thô (`ADR-103`).

Hằng số đứng riêng, có tên, dùng đúng MỘT lần trong package này."""

UNIT_CONVERSION_LABEL = "thousand_VND × 1000 → VND"


class DailyMinStatus(str, Enum):
    RESOLVED = "RESOLVED"
    PENDING = "PENDING"


class DailyMinUnresolvedReason(str, Enum):
    """Enum ĐÓNG. Mỗi lý do là một CÂU KHẲNG ĐỊNH kiểm được.

    Không có giá trị `UNKNOWN`: một nhánh không gọi được tên mình là một nhánh
    chưa ai nghĩ tới, và nó phải làm test đỏ chứ không được trôi qua.
    """

    SALE_DATE_MISSING = "SALE_DATE_MISSING"
    RAW_PRODUCT_IDENTITY_EMPTY = "RAW_PRODUCT_IDENTITY_EMPTY"
    IDENTITY_UNRESOLVED = "IDENTITY_UNRESOLVED"
    IDENTITY_NOT_TRACKING = "IDENTITY_NOT_TRACKING"
    #: Ngày bán nằm NGOÀI khoảng đã hỏi Tracking. Khác hẳn "đã hỏi và không
    #: có": ảnh chụp không nói gì về ngày ấy, nên đây là một khoảng trống của
    #: chính lần capture, sửa được bằng cách chụp lại rộng hơn.
    SALE_DATE_OUTSIDE_CAPTURE = "SALE_DATE_OUTSIDE_CAPTURE"
    #: Trong khoảng đã hỏi, nhưng hợp đồng không trả cặp này ở cả `records`
    #: lẫn `errors`. Đó là một ảnh chụp KHÔNG CÂN SỔ — không được đọc thành
    #: "không có giá".
    NOT_IN_CAPTURE = "NOT_IN_CAPTURE"
    #: Tracking nói: mã ấy chưa từng có bản ghi nào tính tới ngày ấy.
    TRACKING_NO_DATA = "TRACKING_NO_DATA"
    #: Tracking nói: ĐÚNG ngày ấy không có bản ngày — hôm ấy không quan sát
    #: được bảng giá. KHÔNG được đọc thành "giá giữ nguyên như hôm trước".
    TRACKING_SOURCE_UNAVAILABLE = "TRACKING_SOURCE_UNAVAILABLE"
    #: Tracking nói: chuỗi hỏi không phải một mã hợp lệ.
    TRACKING_INVALID_PRODUCT_CODE = "TRACKING_INVALID_PRODUCT_CODE"
    #: Có bản ghi, nhưng hôm ấy mã đã hết hàng hoàn toàn. KHÔNG phải giá 0.
    OUT_OF_STOCK = "OUT_OF_STOCK"
    #: Có bản ghi, nhưng bản ghi tự khai là không có dữ liệu giá.
    NO_DATA = "NO_DATA"


@dataclass(frozen=True)
class DailyMinProvenance:
    """Đủ để một người mở lại và kiểm từng bước — không phải một nhãn.

    Cố ý mang CẢ `raw_value_thousand_vnd` lẫn `resolved_price_vnd`: người đọc
    thấy được phép quy đổi đã xảy ra, chứ không phải tin rằng nó đã xảy ra.
    """

    product_code: Optional[str]
    namespace: Optional[str]
    sale_date: Optional[_dt.date]
    capture_id: str
    capture_captured_at: Optional[_dt.datetime]
    schema_version: str
    #: Ngày Tracking THẬT SỰ quan sát trạng thái này. Khác `sale_date` khi mốc
    #: được mang qua các ngày không đổi giá — và khi ấy `carried_from` nói ra.
    observed_on: Optional[_dt.date] = None
    carried_from: Optional[_dt.date] = None
    day_status: Optional[DayStatus] = None
    price_status: Optional[PriceStatus] = None
    min_sources: tuple[str, ...] = ()
    rule_version: str = ""
    source_fingerprint: str = ""
    revision: str = ""
    recorded_at: Optional[_dt.datetime] = None
    recorded_by: str = ""
    raw_value_thousand_vnd: Optional[Decimal] = None
    unit_conversion: str = UNIT_CONVERSION_LABEL
    resolved_price_vnd: Optional[Decimal] = None
    correction_of: Optional[str] = None
    raw_product_identity: Optional[str] = None
    unresolved_reason: Optional[DailyMinUnresolvedReason] = None
    unresolved_detail: Optional[str] = None


@dataclass(frozen=True)
class DailyMinResolution:
    """Kết quả một lần tra. Một con số KHÔNG bao giờ đi một mình.

    `price_vnd` chỉ khác `None` khi `status is RESOLVED`; và `RESOLVED` chỉ tồn
    tại khi có một con số. Bất biến ấy được `__post_init__` kiểm, không phải
    được hứa trong tài liệu.
    """

    status: DailyMinStatus
    provenance: DailyMinProvenance
    price_vnd: Optional[Decimal] = None
    reason: Optional[DailyMinUnresolvedReason] = None

    def __post_init__(self) -> None:
        if self.status is DailyMinStatus.RESOLVED:
            if self.price_vnd is None or self.reason is not None:
                raise ValueError("RESOLVED bắt buộc có price_vnd và KHÔNG có reason")
        else:
            if self.price_vnd is not None or self.reason is None:
                raise ValueError(
                    "PENDING bắt buộc có reason và KHÔNG BAO GIỜ mang price_vnd "
                    "(INV-25: Pending không phải 0, không phải giá cũ)"
                )

    @property
    def is_resolved(self) -> bool:
        return self.status is DailyMinStatus.RESOLVED

    @property
    def is_provisional(self) -> bool:
        """Giá này đến từ một ngày CHƯA CHỐT.

        Dùng được, nhưng kỳ báo cáo còn chứa nó thì chưa được gọi là chốt: bản
        cuối cùng của ngày ấy có thể còn đổi. Đây là lý do trạng thái đi kèm
        con số thay vì bị bỏ đi sau khi đọc.
        """
        return self.provenance.day_status is DayStatus.PROVISIONAL


_LY_DO_THEO_HOP_DONG = {
    MissingReason.NO_DATA: DailyMinUnresolvedReason.TRACKING_NO_DATA,
    MissingReason.SOURCE_UNAVAILABLE: (
        DailyMinUnresolvedReason.TRACKING_SOURCE_UNAVAILABLE
    ),
    MissingReason.INVALID_PRODUCT_CODE: (
        DailyMinUnresolvedReason.TRACKING_INVALID_PRODUCT_CODE
    ),
}
"""Mỗi lý do của Tracking ánh xạ sang ĐÚNG MỘT lý do của Reports.

Bảng chứ không phải một chuỗi `if`: "mọi lý do hợp đồng đều có ảnh" là một
tính chất kiểm được bằng một assertion trên chính bảng này, thay vì phải đọc
từng nhánh và tin rằng không ai quên một nhánh."""


class TrackingDailyMinProvider:
    """Adapter `PriceProvider` cho hợp đồng `daily-min-v1`.

    Thuần đọc: không lệnh, không ghi, không trạng thái tích luỹ ngoài
    `audit_trail`. Cùng ảnh chụp + cùng đầu vào ⇒ cùng đầu ra, mọi lần.
    """

    price_source = PRICE_SOURCE_TRACKING_DAILY_MIN

    def __init__(
        self,
        snapshot: DailyMinSnapshot,
        *,
        identity_index: Mapping[str, CanonicalProductIdentity],
    ) -> None:
        self._snapshot = snapshot.require_complete()
        self._identity_index = dict(identity_index)
        self._audit: list[DailyMinResolution] = []

    @property
    def snapshot(self) -> DailyMinSnapshot:
        return self._snapshot

    @property
    def audit_trail(self) -> tuple[DailyMinResolution, ...]:
        return tuple(self._audit)

    # ------------------------------------------------------------------

    def lookup(
        self, product_code: Optional[str], sale_date: Optional[_dt.date]
    ) -> Optional[Decimal]:
        """Biên `PriceProvider`: một `Decimal` hoặc `None` (Pending).

        `product_code` ở đây là **tên hàng kế toán thô** — xem docstring module.
        """
        return self.resolve(product_code, sale_date).price_vnd

    def resolve(
        self, raw_product_identity: Optional[str], sale_date: Optional[_dt.date]
    ) -> DailyMinResolution:
        """Bản đầy đủ của `lookup()`: kết quả kèm toàn bộ provenance."""
        resolution = self._resolve(raw_product_identity, sale_date)
        self._audit.append(resolution)
        return resolution

    # ------------------------------------------------------------------

    def _prov(self, **kw) -> DailyMinProvenance:
        snap = self._snapshot
        base = {
            "capture_id": snap.capture_id,
            "capture_captured_at": snap.captured_at,
            "schema_version": snap.schema_version,
        }
        base.update(kw)
        return DailyMinProvenance(**base)

    def _pending(
        self,
        reason: DailyMinUnresolvedReason,
        detail: str,
        **kw,
    ) -> DailyMinResolution:
        return DailyMinResolution(
            status=DailyMinStatus.PENDING,
            reason=reason,
            provenance=self._prov(
                unresolved_reason=reason, unresolved_detail=detail, **kw
            ),
        )

    def _resolve(
        self, raw_product_identity: Optional[str], sale_date: Optional[_dt.date]
    ) -> DailyMinResolution:
        if sale_date is None:
            return self._pending(
                DailyMinUnresolvedReason.SALE_DATE_MISSING,
                "Dòng không có ngày bán; không có ngày thì không có giá của "
                "ngày ấy để tra.",
                product_code=None,
                namespace=None,
                sale_date=None,
                raw_product_identity=raw_product_identity,
            )

        try:
            key = raw_identity_key(raw_product_identity)
        except (EmptyRawIdentityError, TypeError, AttributeError):
            return self._pending(
                DailyMinUnresolvedReason.RAW_PRODUCT_IDENTITY_EMPTY,
                "Tên hàng rỗng sau chuẩn hoá — không sinh được khoá định danh.",
                product_code=None,
                namespace=None,
                sale_date=sale_date,
                raw_product_identity=raw_product_identity,
            )

        identity = self._identity_index.get(key)
        if identity is None:
            return self._pending(
                DailyMinUnresolvedReason.IDENTITY_UNRESOLVED,
                "Chưa nhận diện được mặt hàng này thành một mã Tracking; "
                "không có mã thì không có gì để tra giá.",
                product_code=None,
                namespace=None,
                sale_date=sale_date,
                raw_product_identity=raw_product_identity,
            )
        if identity.namespace is not Namespace.TRACKING:
            # Ảnh chụp KHÔNG được hỏi ở đây: `PUBLIC_PURCHASE:<mã>` không tự
            # chuyển sang Tracking, và một mã trùng chuỗi ở hai namespace là
            # hai identity khác nhau (`INV-18`).
            return self._pending(
                DailyMinUnresolvedReason.IDENTITY_NOT_TRACKING,
                f"Identity là {identity.namespace.value}, không phải TRACKING. "
                "MIN theo ngày chỉ tồn tại cho danh mục Tracking.",
                product_code=identity.source_product_code,
                namespace=identity.namespace.value,
                sale_date=sale_date,
                raw_product_identity=raw_product_identity,
            )

        code = identity.source_product_code
        common = {
            "product_code": code,
            "namespace": Namespace.TRACKING.value,
            "sale_date": sale_date,
            "raw_product_identity": raw_product_identity,
        }

        snap = self._snapshot
        if not snap.covers(sale_date):
            return self._pending(
                DailyMinUnresolvedReason.SALE_DATE_OUTSIDE_CAPTURE,
                f"Ngày bán {sale_date.isoformat()} nằm ngoài khoảng đã chụp "
                f"[{snap.date_from}, {snap.date_to}]; ảnh chụp không nói gì về "
                "ngày ấy. Đây là khoảng trống của lần capture, không phải kết "
                "luận về giá.",
                **common,
            )

        record = snap.record_for(code, sale_date)
        if record is None:
            missing = snap.error_for(code, sale_date)
            if missing is None:
                # Ảnh chụp không cân sổ: hợp đồng cam kết mỗi cặp đã hỏi nằm ở
                # `records` hoặc `errors`. Không ở đâu cả nghĩa là mã này chưa
                # từng được hỏi — và đọc nó thành "không có giá" là để một lỗi
                # phạm vi capture phát biểu thay cho dữ liệu.
                return self._pending(
                    DailyMinUnresolvedReason.NOT_IN_CAPTURE,
                    f"Cặp ({code}, {sale_date.isoformat()}) không có mặt ở cả "
                    "`records` lẫn `errors` của ảnh chụp — mã này chưa được "
                    "hỏi trong lần capture ấy.",
                    **common,
                )
            return self._pending(
                _LY_DO_THEO_HOP_DONG[missing],
                f"Tracking trả {missing.value} cho ({code}, "
                f"{sale_date.isoformat()}).",
                **common,
            )

        if record.price_status is PriceStatus.OUT_OF_STOCK:
            return self._pending(
                DailyMinUnresolvedReason.OUT_OF_STOCK,
                f"Ngày {sale_date.isoformat()} mã {code} đã hết hàng hoàn toàn. "
                "Đây KHÔNG phải giá vốn bằng 0 — không nguồn nào bán được thì "
                "không có giá mua nào để ghi.",
                **self._prov_from(record, common),
            )
        if record.price_status is PriceStatus.NO_DATA:
            return self._pending(
                DailyMinUnresolvedReason.NO_DATA,
                f"Ngày {sale_date.isoformat()} mã {code} chưa có dữ liệu giá "
                "nào từ nhà cung cấp lẫn tồn kho.",
                **self._prov_from(record, common),
            )

        return self._resolved(record, common)

    # ------------------------------------------------------------------

    @staticmethod
    def _prov_from(record: DailyMinRecord, common: dict) -> dict:
        """Phần provenance đọc thẳng từ bản ghi — dùng cho CẢ Pending.

        Pending cũng mang revision/luật/ngày quan sát: câu hỏi người kiểm hỏi
        về một dòng không có giá là "Tracking đã nói gì, ở bản ghi nào", và
        không có mấy trường này thì không trả lời được.
        """
        return {
            **common,
            "observed_on": record.observed_on,
            "carried_from": record.carried_from,
            "day_status": record.day_status,
            "price_status": record.price_status,
            "min_sources": tuple(
                f"{s.source_type.value}:{s.source_id}" for s in record.min_sources
            ),
            "rule_version": record.rule_version,
            "source_fingerprint": record.source_fingerprint,
            "revision": record.revision,
            "recorded_at": record.recorded_at,
            "recorded_by": record.recorded_by,
            "correction_of": record.correction_of,
        }

    def _resolved(self, record: DailyMinRecord, common: dict) -> DailyMinResolution:
        """CHỖ DUY NHẤT quy đổi nghìn VND → VND trong toàn package."""
        raw = record.min_price_thousand_vnd
        price_vnd = raw * THOUSAND_VND_TO_VND
        return DailyMinResolution(
            status=DailyMinStatus.RESOLVED,
            price_vnd=price_vnd,
            provenance=self._prov(
                **self._prov_from(record, common),
                raw_value_thousand_vnd=raw,
                resolved_price_vnd=price_vnd,
            ),
        )
