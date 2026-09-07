"""Hợp đồng `daily-min-v1` — ảnh chụp giá MIN theo NGÀY BÁN của Tracking.

## Reports KHÔNG tính một MIN thứ hai

Tracking sở hữu luật MIN (nhà cung cấp nào còn hàng, ai bị loại, ô Tồn có tham
gia không, ngưỡng giá bất thường). Module này chỉ ĐỌC kết quả đã được Tracking
tính và đóng dấu. Dựng lại phép tính ấy ở đây là tạo ra bản thứ hai của một
luật đang sống, và hai bản sẽ trôi khỏi nhau — lúc đó bảng giá hiện một con số,
báo cáo hiện con số khác, và không ai nói được bên nào đúng.

## Ba enum ĐÓNG, và vì sao chúng phải đóng

```text
price_status   AVAILABLE | OUT_OF_STOCK | NO_DATA
day_status     PROVISIONAL | FINAL
source_type    SUPPLIER | INVENTORY
```

Một giá trị lạ ở bất kỳ enum nào là LỖI NẠP, không phải một dòng bị bỏ qua. Lý
do: mọi giá trị lạ đều đến từ một phiên bản hợp đồng mà Reports chưa hiểu, và
"bỏ qua thứ không hiểu" trong một luồng định giá nghĩa là im lặng đánh rơi đúng
những dòng mới nhất. Thà không ra báo cáo còn hơn ra một báo cáo thiếu.

## `min_price = null` KHÔNG BAO GIỜ là `0`

`OUT_OF_STOCK` và `NO_DATA` mang `min_price = null`. Đây là bất biến được
`__post_init__` kiểm, không phải một lời hứa trong tài liệu: một `0` lọt vào
đây là giá vốn bằng không, tức lợi nhuận bằng đúng doanh thu, trên mọi dòng của
mặt hàng đó — một con số sai trông hoàn toàn bình thường.

## Đơn vị tiền: quy đổi ĐÚNG MỘT LẦN, và không ở đây

Tracking lưu nghìn VND, Reports lưu VND thô (`ADR-103`). Ảnh chụp giữ NGUYÊN
đơn vị của nguồn (`min_price_thousand_vnd`) và từ chối một `currency_unit`
khác `VND_THOUSAND`. Phép nhân 1000 nằm ở `provider.py`, đúng một chỗ, cùng
tiền lệ `THOUSAND_VND_TO_VND` của Reports History Reader V1. Hai chỗ quy đổi là
hai chỗ để quên một chỗ.

## `errors` không phải phần phụ

Hợp đồng trả về `records` và `errors`; mỗi cặp (mặt hàng, ngày) đã hỏi nằm ở
đúng một trong hai. Ảnh chụp giữ CẢ HAI, vì "vì sao dòng này không có giá"
chính là câu người kiểm hỏi — và một `errors` bị vứt đi biến "Tracking nói
không có bằng chứng" thành "Reports không tìm thấy gì", hai câu rất khác nhau.
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from enum import Enum
from typing import Any, Mapping, Optional

__all__ = [
    "CaptureStatus",
    "DailyMinCaptureFailedError",
    "DailyMinRecord",
    "DailyMinSnapshot",
    "DayStatus",
    "ExcludedSource",
    "InvalidDailyMinSnapshotError",
    "MinSource",
    "MissingReason",
    "PriceStatus",
    "SUPPORTED_CURRENCY_UNIT",
    "SUPPORTED_SCHEMA_VERSION",
    "SourceType",
    "UnsupportedDailyMinSchemaError",
]

SUPPORTED_SCHEMA_VERSION = "daily-min-v1"
"""Phiên bản hợp đồng DUY NHẤT mà bản này hiểu.

Từ chối bản khác là một yêu cầu tường minh của R1. Đọc một schema lạ "cho đến
khi gặp trường không nhận ra" là cách chắc chắn nhất để một thay đổi ngữ nghĩa
phía Tracking đi thẳng vào giá vốn mà không ai thấy."""

SUPPORTED_CURRENCY_UNIT = "VND_THOUSAND"
"""Đơn vị tiền DUY NHẤT được chấp nhận. Xem docstring module."""


class PriceStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    OUT_OF_STOCK = "OUT_OF_STOCK"
    NO_DATA = "NO_DATA"


class DayStatus(str, Enum):
    PROVISIONAL = "PROVISIONAL"
    FINAL = "FINAL"


class SourceType(str, Enum):
    SUPPLIER = "SUPPLIER"
    INVENTORY = "INVENTORY"


class MissingReason(str, Enum):
    """Lý do Tracking KHÔNG trả được một cặp (mặt hàng, ngày). Enum ĐÓNG.

    Ba lý do này nói ba chuyện khác nhau và không được gộp: `NO_DATA` là kết
    luận về DỮ LIỆU (mặt hàng ấy chưa từng có bản ghi nào tới ngày ấy);
    `SOURCE_UNAVAILABLE` là kết luận về HỆ THỐNG (hôm ấy Tracking không quan
    sát được bảng giá, nên không ai biết giá là bao nhiêu);
    `INVALID_PRODUCT_CODE` là kết luận về CÂU HỎI (chuỗi hỏi không thể là một
    khoá hợp lệ). Gộp chúng lại là để một sự cố hạ tầng phát biểu thay cho dữ
    liệu.
    """

    NO_DATA = "NO_DATA"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"
    INVALID_PRODUCT_CODE = "INVALID_PRODUCT_CODE"


class CaptureStatus(str, Enum):
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


class InvalidDailyMinSnapshotError(ValueError):
    """Payload tồn tại nhưng không đọc được thành một ảnh chụp hợp lệ."""

    def __init__(self, message: str, *, reason: str) -> None:
        super().__init__(message)
        self.reason = reason


class UnsupportedDailyMinSchemaError(InvalidDailyMinSnapshotError):
    """Hợp đồng ở một phiên bản bản này không hiểu — TỪ CHỐI, không đọc bừa."""


class DailyMinCaptureFailedError(RuntimeError):
    """Ảnh chụp mang `capture_status = FAILED`.

    LỖI CỨNG ngay lúc dựng provider, không phải Pending ở tầng dưới — cùng ngữ
    nghĩa `INV-12` mà `TrackingPriceHistorySnapshot.require_complete()` đã lập:
    một lần capture hỏng và một lịch sử thật sự rỗng là hai sự kiện khác nhau,
    và gộp chúng làm một lần mất mạng trông y hệt một kết luận dữ liệu.
    """


@dataclass(frozen=True)
class MinSource:
    """Một nguồn ĐANG GIỮ đúng con số MIN của ngày đó."""

    source_type: SourceType
    source_id: str


@dataclass(frozen=True)
class ExcludedSource:
    """Một nguồn bị luật của Tracking LOẠI khỏi MIN, kèm lý do đo được.

    Giữ lại vì nó là bằng chứng luật lọc đã chạy. Không có nó thì "vì sao giá
    200 nghìn của nhà cung cấp kia không thành MIN" không trả lời được từ dữ
    liệu.
    """

    source_type: SourceType
    source_id: str
    price_thousand_vnd: Optional[Decimal]
    reference_price_thousand_vnd: Optional[Decimal]
    rule: str


@dataclass(frozen=True)
class DailyMinRecord:
    """MIN của MỘT mặt hàng tại MỘT ngày bán, kèm đủ dấu vết để mở lại."""

    product_code: str
    effective_date: _dt.date
    price_status: PriceStatus
    day_status: DayStatus
    min_price_thousand_vnd: Optional[Decimal]
    min_sources: tuple[MinSource, ...]
    rule_version: str
    source_fingerprint: str
    revision: str
    recorded_at: Optional[_dt.datetime]
    recorded_by: str
    observed_on: _dt.date
    carried_from: Optional[_dt.date]
    excluded_sources: tuple[ExcludedSource, ...] = ()
    correction_of: Optional[str] = None
    correction_reason: str = ""

    def __post_init__(self) -> None:
        priced = self.min_price_thousand_vnd is not None
        if self.price_status is PriceStatus.AVAILABLE:
            if not priced or self.min_price_thousand_vnd <= 0:
                raise InvalidDailyMinSnapshotError(
                    f"{self.product_code}@{self.effective_date}: AVAILABLE bắt "
                    "buộc có min_price DƯƠNG.",
                    reason="available_without_price",
                )
        else:
            if priced:
                raise InvalidDailyMinSnapshotError(
                    f"{self.product_code}@{self.effective_date}: "
                    f"{self.price_status.value} KHÔNG BAO GIỜ mang một con số — "
                    "0 không phải giá vốn, và giá cũ đã hết hiệu lực.",
                    reason="missing_status_with_price",
                )
            if self.min_sources:
                raise InvalidDailyMinSnapshotError(
                    f"{self.product_code}@{self.effective_date}: "
                    f"{self.price_status.value} không thể có nguồn giữ MIN.",
                    reason="missing_status_with_sources",
                )
        if self.carried_from is not None and self.carried_from != self.observed_on:
            raise InvalidDailyMinSnapshotError(
                f"{self.product_code}@{self.effective_date}: carried_from "
                f"({self.carried_from}) phải trùng observed_on "
                f"({self.observed_on}) — hai trường nói cùng một sự thật.",
                reason="carried_from_mismatch",
            )
        if self.observed_on > self.effective_date:
            raise InvalidDailyMinSnapshotError(
                f"{self.product_code}@{self.effective_date}: quan sát ngày "
                f"{self.observed_on} nằm SAU ngày hiệu lực — một bản ghi của "
                "tương lai không nói được gì về quá khứ.",
                reason="observed_after_effective",
            )

    @property
    def is_available(self) -> bool:
        return self.price_status is PriceStatus.AVAILABLE

    @property
    def is_provisional(self) -> bool:
        return self.day_status is DayStatus.PROVISIONAL

    @property
    def is_carried(self) -> bool:
        return self.carried_from is not None


@dataclass(frozen=True)
class DailyMinSnapshot:
    """Toàn bộ nội dung MỘT lần capture hợp đồng `daily-min-v1`."""

    capture_id: str
    captured_at: _dt.datetime
    captured_by: str
    source_system_ref: str
    capture_status: CaptureStatus
    failure_reason: Optional[str] = None
    schema_version: str = SUPPORTED_SCHEMA_VERSION
    currency_unit: str = SUPPORTED_CURRENCY_UNIT
    business_timezone: str = ""
    date_from: Optional[_dt.date] = None
    date_to: Optional[_dt.date] = None
    records: Mapping[tuple[str, _dt.date], DailyMinRecord] = None  # type: ignore[assignment]
    errors: Mapping[tuple[str, _dt.date], MissingReason] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        object.__setattr__(self, "records", dict(self.records or {}))
        object.__setattr__(self, "errors", dict(self.errors or {}))
        if self.capture_status is CaptureStatus.FAILED and not self.failure_reason:
            raise InvalidDailyMinSnapshotError(
                "capture_status = FAILED bắt buộc có failure_reason.",
                reason="failed_without_reason",
            )

    def require_complete(self) -> "DailyMinSnapshot":
        """Cổng vào DUY NHẤT cho mọi đường đọc ảnh chụp (`INV-12`)."""
        if self.capture_status is not CaptureStatus.COMPLETE:
            raise DailyMinCaptureFailedError(
                f"capture {self.capture_id} có capture_status="
                f"{self.capture_status.value} ({self.failure_reason}); provider "
                "từ chối chạy — đây là LỖI, không phải Pending (INV-12)"
            )
        return self

    def covers(self, sale_date: _dt.date) -> bool:
        """Ngày bán có nằm trong khoảng ĐÃ HỎI Tracking không.

        Ngoài khoảng thì ảnh chụp KHÔNG nói gì về ngày ấy — khác hẳn "đã hỏi và
        Tracking bảo không có". Trả `False` ở đây để provider dựng một lý do
        Pending riêng, thay vì để một khoảng chụp quá hẹp trông như một mặt
        hàng chưa từng có giá.
        """
        if self.date_from is None or self.date_to is None:
            return False
        return self.date_from <= sale_date <= self.date_to

    def record_for(
        self, product_code: str, sale_date: _dt.date
    ) -> Optional[DailyMinRecord]:
        return self.records.get((product_code, sale_date))

    def error_for(
        self, product_code: str, sale_date: _dt.date
    ) -> Optional[MissingReason]:
        return self.errors.get((product_code, sale_date))

    # -----------------------------------------------------------------

    @classmethod
    def from_contract(
        cls,
        data: Mapping[str, Any],
        *,
        capture_id: str,
        captured_at: _dt.datetime,
        captured_by: str,
        source_system_ref: str,
        capture_status: CaptureStatus = CaptureStatus.COMPLETE,
        failure_reason: Optional[str] = None,
    ) -> "DailyMinSnapshot":
        """Dựng ảnh chụp từ phong bì hợp đồng đã gộp trang.

        Provenance của chính lần capture đến TỪ công cụ capture, không suy ra từ
        nội dung — nội dung không tự chứng minh được nó được chụp lúc nào.
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

        schema = data.get("schema_version")
        if schema != SUPPORTED_SCHEMA_VERSION:
            raise UnsupportedDailyMinSchemaError(
                f"schema_version={schema!r} không phải "
                f"{SUPPORTED_SCHEMA_VERSION!r}. Bản này TỪ CHỐI đọc một hợp "
                "đồng nó không hiểu, thay vì đọc sai một phần và im lặng bỏ "
                "phần còn lại.",
                reason="unsupported_schema",
            )
        unit = data.get("currency_unit")
        if unit != SUPPORTED_CURRENCY_UNIT:
            raise InvalidDailyMinSnapshotError(
                f"currency_unit={unit!r} không phải {SUPPORTED_CURRENCY_UNIT!r}. "
                "Đơn vị tiền là thứ KHÔNG được đoán: đoán sai một lần là sai "
                "đúng 1.000 lần, và sai đều nên nhìn bảng không phát hiện ra.",
                reason="unsupported_currency_unit",
            )

        first_day = _date(data.get("date_from"), "date_from")
        last_day = _date(data.get("date_to"), "date_to")
        if first_day is None or last_day is None:
            raise InvalidDailyMinSnapshotError(
                "Thiếu date_from/date_to — không có khoảng chụp thì không phân "
                "biệt được 'ngoài phạm vi đã hỏi' với 'đã hỏi và không có'.",
                reason="missing_date_range",
            )
        if first_day > last_day:
            raise InvalidDailyMinSnapshotError(
                f"Khoảng chụp ngược: {first_day} > {last_day}.",
                reason="inverted_date_range",
            )

        raw_records = data.get("records")
        if not isinstance(raw_records, list):
            raise InvalidDailyMinSnapshotError(
                "Thiếu khối 'records' hoặc nó không phải một danh sách.",
                reason="missing_records_block",
            )
        raw_errors = data.get("errors")
        if raw_errors is None:
            raw_errors = []
        if not isinstance(raw_errors, list):
            raise InvalidDailyMinSnapshotError(
                "'errors' phải là một danh sách. Nó KHÔNG phải phần phụ: mỗi "
                "cặp (mặt hàng, ngày) không trả lời được đều nằm ở đó, và vứt "
                "nó đi là biến 'Tracking nói không có bằng chứng' thành "
                "'Reports không tìm thấy gì'.",
                reason="malformed_errors_block",
            )

        records: dict[tuple[str, _dt.date], DailyMinRecord] = {}
        for index, raw in enumerate(raw_records, start=1):
            record = _record(raw, index)
            key = (record.product_code, record.effective_date)
            if key in records:
                raise InvalidDailyMinSnapshotError(
                    f"Trùng bản ghi cho {record.product_code}@"
                    f"{record.effective_date}. Hai bản ghi cho cùng một cặp là "
                    "hai câu trả lời cho cùng một câu hỏi; chọn hộ một cái là "
                    "đoán.",
                    reason="duplicate_record",
                )
            records[key] = record

        errors: dict[tuple[str, _dt.date], MissingReason] = {}
        for index, raw in enumerate(raw_errors, start=1):
            if not isinstance(raw, dict):
                raise InvalidDailyMinSnapshotError(
                    f"errors[{index}] phải là một ánh xạ.", reason="malformed_error"
                )
            code = _text(raw.get("product_code"), f"errors[{index}].product_code")
            day = _date(raw.get("effective_date"), f"errors[{index}].effective_date")
            if day is None:
                raise InvalidDailyMinSnapshotError(
                    f"errors[{index}] thiếu effective_date.",
                    reason="malformed_error",
                )
            try:
                missing = MissingReason(raw.get("reason"))
            except ValueError as exc:
                raise InvalidDailyMinSnapshotError(
                    f"errors[{index}]: reason={raw.get('reason')!r} ngoài enum "
                    f"đóng {[r.value for r in MissingReason]}.",
                    reason="unknown_error_reason",
                ) from exc
            key = (code, day)
            if key in records:
                raise InvalidDailyMinSnapshotError(
                    f"{code}@{day} vừa có bản ghi vừa có lỗi. Hợp đồng nói mỗi "
                    "cặp nằm ở ĐÚNG MỘT bên; nhận cả hai là nhận một mâu thuẫn.",
                    reason="record_and_error_conflict",
                )
            errors[key] = missing

        return cls(
            capture_id=capture_id,
            captured_at=captured_at,
            captured_by=captured_by,
            source_system_ref=source_system_ref,
            capture_status=capture_status,
            schema_version=str(schema),
            currency_unit=str(unit),
            business_timezone=str(data.get("business_timezone") or ""),
            date_from=first_day,
            date_to=last_day,
            records=records,
            errors=errors,
        )


# ---------------------------------------------------------------------------
# Đọc từng trường — mọi lỗi hình dạng đều RAISE, không có nhánh "bỏ qua"
# ---------------------------------------------------------------------------


def _text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InvalidDailyMinSnapshotError(
            f"{name} REQUIRED và phải là chuỗi không rỗng; nhận {value!r}.",
            reason="missing_text_field",
        )
    return value


def _date(value: Any, name: str) -> Optional[_dt.date]:
    if value is None:
        return None
    if not isinstance(value, str):
        raise InvalidDailyMinSnapshotError(
            f"{name} phải là chuỗi `YYYY-MM-DD`; nhận {value!r}.",
            reason="invalid_date",
        )
    try:
        return _dt.date.fromisoformat(value)
    except ValueError as exc:
        raise InvalidDailyMinSnapshotError(
            f"{name}={value!r} không phải một ngày lịch hợp lệ.",
            reason="invalid_date",
        ) from exc


def _money(value: Any, name: str) -> Optional[Decimal]:
    """Số tiền → `Decimal`. Chặn `bool`, chặn `NaN`/vô cực.

    `bool` là `int` trong Python, nên `True` sẽ lặng lẽ thành giá 1 nghìn đồng.
    `NaN`/`Infinity` thì lọt qua mọi phép so sánh rồi đi thẳng vào một phép
    nhân — tiền lệ `TASK-105B-RC-1` đã vá đúng lớp lỗi này ở
    `FilePriceProvider`, và không có lý do gì để nó mở lại ở đây.
    """
    if value is None:
        return None
    if isinstance(value, bool):
        raise InvalidDailyMinSnapshotError(
            f"{name} là bool ({value!r}), không phải một số tiền.",
            reason="bool_as_price",
        )
    if not isinstance(value, (int, float, str)):
        raise InvalidDailyMinSnapshotError(
            f"{name} phải là số; nhận {type(value).__name__}.",
            reason="invalid_price_type",
        )
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise InvalidDailyMinSnapshotError(
            f"{name}={value!r} không đọc được thành số.", reason="invalid_price"
        ) from exc
    if not amount.is_finite():
        raise InvalidDailyMinSnapshotError(
            f"{name}={value!r} không hữu hạn — `NaN`/vô cực không phải giá.",
            reason="non_finite_price",
        )
    return amount


def _moment(value: Any, name: str) -> Optional[_dt.datetime]:
    if value is None:
        return None
    if not isinstance(value, str):
        raise InvalidDailyMinSnapshotError(
            f"{name} phải là chuỗi ISO-8601; nhận {value!r}.",
            reason="invalid_datetime",
        )
    try:
        moment = _dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise InvalidDailyMinSnapshotError(
            f"{name}={value!r} không phải ISO-8601 hợp lệ.",
            reason="invalid_datetime",
        ) from exc
    if moment.tzinfo is None or moment.tzinfo.utcoffset(moment) is None:
        raise InvalidDailyMinSnapshotError(
            f"{name}={value!r} phải AWARE (có múi giờ). Một dấu thời gian "
            "không múi giờ không so được với bất cứ mốc nào.",
            reason="naive_datetime",
        )
    return moment


def _source(raw: Any, name: str) -> MinSource:
    if not isinstance(raw, dict):
        raise InvalidDailyMinSnapshotError(
            f"{name} phải là một ánh xạ.", reason="malformed_source"
        )
    try:
        kind = SourceType(raw.get("source_type"))
    except ValueError as exc:
        raise InvalidDailyMinSnapshotError(
            f"{name}: source_type={raw.get('source_type')!r} ngoài enum đóng "
            f"{[s.value for s in SourceType]}.",
            reason="unknown_source_type",
        ) from exc
    return MinSource(
        source_type=kind,
        source_id=_text(raw.get("source_id"), name + ".source_id"),
    )


def _record(raw: Any, index: int) -> DailyMinRecord:
    name = f"records[{index}]"
    if not isinstance(raw, dict):
        raise InvalidDailyMinSnapshotError(
            f"{name} phải là một ánh xạ.", reason="malformed_record"
        )
    if raw.get("schema_version") not in (None, SUPPORTED_SCHEMA_VERSION):
        raise UnsupportedDailyMinSchemaError(
            f"{name}: schema_version={raw.get('schema_version')!r} khác phong bì.",
            reason="unsupported_schema",
        )
    if raw.get("currency_unit") not in (None, SUPPORTED_CURRENCY_UNIT):
        raise InvalidDailyMinSnapshotError(
            f"{name}: currency_unit={raw.get('currency_unit')!r} khác phong bì. "
            "Hai đơn vị tiền trong cùng một ảnh chụp là một phép nhân giấu ở "
            "giữa.",
            reason="unsupported_currency_unit",
        )

    code = _text(raw.get("product_code"), name + ".product_code")
    day = _date(raw.get("effective_date"), name + ".effective_date")
    if day is None:
        raise InvalidDailyMinSnapshotError(
            f"{name} thiếu effective_date.", reason="missing_effective_date"
        )
    try:
        price_status = PriceStatus(raw.get("price_status"))
    except ValueError as exc:
        raise InvalidDailyMinSnapshotError(
            f"{name}: price_status={raw.get('price_status')!r} ngoài enum đóng "
            f"{[s.value for s in PriceStatus]}.",
            reason="unknown_price_status",
        ) from exc
    try:
        day_status = DayStatus(raw.get("day_status"))
    except ValueError as exc:
        raise InvalidDailyMinSnapshotError(
            f"{name}: day_status={raw.get('day_status')!r} ngoài enum đóng "
            f"{[s.value for s in DayStatus]}.",
            reason="unknown_day_status",
        ) from exc

    raw_sources = raw.get("min_sources") or []
    if not isinstance(raw_sources, list):
        raise InvalidDailyMinSnapshotError(
            f"{name}.min_sources phải là một danh sách.", reason="malformed_sources"
        )
    sources = tuple(
        _source(item, f"{name}.min_sources[{i}]")
        for i, item in enumerate(raw_sources, start=1)
    )

    raw_excluded = raw.get("excluded_sources") or []
    if not isinstance(raw_excluded, list):
        raise InvalidDailyMinSnapshotError(
            f"{name}.excluded_sources phải là một danh sách.",
            reason="malformed_excluded_sources",
        )
    excluded = []
    for i, item in enumerate(raw_excluded, start=1):
        base = _source(item, f"{name}.excluded_sources[{i}]")
        excluded.append(
            ExcludedSource(
                source_type=base.source_type,
                source_id=base.source_id,
                price_thousand_vnd=_money(
                    item.get("price"), f"{name}.excluded_sources[{i}].price"
                ),
                reference_price_thousand_vnd=_money(
                    item.get("reference_price"),
                    f"{name}.excluded_sources[{i}].reference_price",
                ),
                rule=str(item.get("rule") or ""),
            )
        )

    observed = _date(raw.get("observed_on"), name + ".observed_on") or day
    return DailyMinRecord(
        product_code=code,
        effective_date=day,
        price_status=price_status,
        day_status=day_status,
        min_price_thousand_vnd=_money(raw.get("min_price"), name + ".min_price"),
        min_sources=sources,
        rule_version=str(raw.get("rule_version") or ""),
        source_fingerprint=str(raw.get("source_fingerprint") or ""),
        revision=str(raw.get("revision") or ""),
        recorded_at=_moment(raw.get("recorded_at"), name + ".recorded_at"),
        recorded_by=str(raw.get("recorded_by") or ""),
        observed_on=observed,
        carried_from=_date(raw.get("carried_from"), name + ".carried_from"),
        excluded_sources=tuple(excluded),
        correction_of=raw.get("correction_of") or None,
        correction_reason=str(raw.get("correction_reason") or ""),
    )
