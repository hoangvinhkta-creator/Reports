"""Nạp MỘT LẦN toàn bộ bằng chứng giá của một lần import — `TASK-105E` §15.

## Vì sao phải là một ảnh chụp, không phải một loạt lời gọi

Một report phải tái lập được. Nếu đơn A hỏi nguồn ở trạng thái `T1`, đơn B ở
`T2` và đơn C ở `T3`, thì "chạy lại và ra cùng kết quả" là một lời hứa không
ai giữ được, và hai bản cùng tên của cùng một report sẽ khác nhau mà không có
chỗ nào ghi vì sao. Nên mọi nguồn được đọc ĐÚNG MỘT LẦN, đóng băng thành các
object bất biến, và `PriceEvidenceSnapshot` mang định danh của từng nguồn để
người kiểm mở lại được chính bộ bằng chứng đã dùng.

## Vắng mặt KHÁC hỏng KHÁC thất bại

```text
file không tồn tại   → nguồn CHƯA ĐƯỢC NỐI  → Pending có lý do "source unavailable"
file hỏng            → LỖI NẠP (raise)      → không có report giả nào được sinh
capture_status FAILED → LỖI khi dựng reader  → INV-12, không bao giờ thành Pending
```

Ba trạng thái này không được gộp. Gộp "chưa có nguồn" với "nguồn hỏng" biến
một sự cố hạ tầng thành một kết luận nghiệp vụ im lặng — chính lớp lỗi mà cả
capability này tồn tại để chặn.

## Không có nguồn nào là mặc định bật

Mọi đường dẫn dưới đây là **committed repository path**, cùng hạng với
`config/` và `data/historical_confirmed/registry.jsonl` (`app/composition.py`).
Không có URL, không có credential, không có network — công cụ capture nằm ở
`tools/tracking/`, ngoài `app/modules/` (`ADR-101`, `DEC-152` §6).
"""

from __future__ import annotations

import datetime as _dt
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

import yaml

from app.modules.config.loader import load_yaml
from app.modules.pricing.tracking_history.capture_file import (
    load_tracking_price_history_capture,
)
from app.modules.pricing.tracking_history.snapshot import (
    TrackingPriceHistorySnapshot,
)
from app.modules.product.identity.public_purchase import (
    PublicPurchaseSourceLoader,
    PublicPurchaseSourceVersion,
)
from app.modules.product.identity.store import (
    JsonlProductIdentityStore,
    StoreView,
)
from app.modules.product.identity.tracking_catalog import (
    CaptureStatus,
    TrackingCatalogRow,
    TrackingCatalogSnapshot,
    canonical_content_hash,
)
from app.modules.product.identity.tracking_inv_map import (
    TrackingInvMapSnapshot,
    canonical_content_hash as inv_map_canonical_content_hash,
)

__all__ = [
    "BusinessTimezone",
    "InvalidTrackingCatalogCaptureFileError",
    "InvalidTrackingInvMapCaptureFileError",
    "PriceEvidenceSnapshot",
    "PriceResolutionSources",
    "PUBLIC_PURCHASE_SOURCE_PATH",
    "TRACKING_CATALOG_CAPTURE_PATH",
    "TRACKING_INV_MAP_CAPTURE_PATH",
    "TRACKING_PRICE_HISTORY_CAPTURE_PATH",
    "IDENTITY_STORE_LOG_PATH",
    "BUSINESS_TIMEZONE_CONFIG",
    "load_business_timezone",
    "load_price_resolution_sources",
    "load_tracking_catalog_capture",
    "load_tracking_inv_map_capture",
]

# Canonical committed paths — cùng hạng `DEFAULT_CONFIG_DIR` của `app/pipeline.py`.
TRACKING_PRICE_HISTORY_CAPTURE_PATH = Path(
    "data/tracking_price_history/capture.json"
)
TRACKING_CATALOG_CAPTURE_PATH = Path("data/tracking_catalog/capture.json")
TRACKING_INV_MAP_CAPTURE_PATH = Path("data/tracking_inv_map/capture.json")
PUBLIC_PURCHASE_SOURCE_PATH = Path("data/public_purchase/source_version.yaml")
IDENTITY_STORE_LOG_PATH = Path("data/product_identity/mappings.jsonl")

BUSINESS_TIMEZONE_CONFIG = "price_resolution.yaml"


class InvalidTrackingCatalogCaptureFileError(ValueError):
    def __init__(self, message: str, *, reason: str) -> None:
        super().__init__(message)
        self.reason = reason


# ---------------------------------------------------------------------------
# Múi giờ nghiệp vụ
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class BusinessTimezone:
    """Múi giờ nghiệp vụ, nạp từ config — KHÔNG có mặc định ngầm.

    `SaleInterval.for_sale_date` bắt buộc truyền `tzinfo` vì một mặc định sai
    dịch biên ngày đi vài giờ và đẩy nó qua bên kia một sự kiện giá. Cấm mặc
    định ở thư viện mà lại chôn một hằng số trong lớp composition thì chỉ là
    chuyển chỗ giấu. Nên nó là một authority nạp từ file, và thiếu/hỏng file là
    `is_valid=False` (fail-closed) chứ không phải "thôi dùng UTC+7 cho nhanh".
    """

    is_valid: bool
    tzinfo: Optional[_dt.tzinfo]
    label: str
    provenance: str


TIMEZONE_UNAVAILABLE = BusinessTimezone(
    is_valid=False, tzinfo=None, label="", provenance="SOURCE_UNAVAILABLE"
)


def load_business_timezone(config_dir: Path) -> BusinessTimezone:
    """`<config_dir>/price_resolution.yaml` → múi giờ nghiệp vụ.

    Chỉ chấp nhận một offset cố định tính bằng giờ (Việt Nam không có DST nên
    một offset cố định là biểu diễn ĐÚNG; một tên IANA sẽ kéo theo một cơ sở
    dữ liệu múi giờ và một lớp phụ thuộc không cần thiết cho bài toán này).
    """
    path = Path(config_dir) / BUSINESS_TIMEZONE_CONFIG
    try:
        data = load_yaml(path)
    except (OSError, yaml.YAMLError):
        return TIMEZONE_UNAVAILABLE
    if not isinstance(data, dict):
        return TIMEZONE_UNAVAILABLE
    if "business_timezone_offset_hours" not in data:
        return TIMEZONE_UNAVAILABLE
    offset = data["business_timezone_offset_hours"]
    if isinstance(offset, bool) or not isinstance(offset, (int, float)):
        return TIMEZONE_UNAVAILABLE
    if not -14 <= float(offset) <= 14:
        return TIMEZONE_UNAVAILABLE
    label = data.get("business_timezone_label")
    return BusinessTimezone(
        is_valid=True,
        tzinfo=_dt.timezone(_dt.timedelta(hours=float(offset))),
        label=str(label) if label else f"UTC{float(offset):+03.0f}:00",
        provenance=f"{path}",
    )


# ---------------------------------------------------------------------------
# Ảnh chụp danh mục Tracking (E-D) — cần cho resolve identity post-cutover
# ---------------------------------------------------------------------------


def _text(payload: dict[str, Any], key: str, path: Path) -> str:
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise InvalidTrackingCatalogCaptureFileError(
            f"{path}: trường {key!r} REQUIRED và phải là chuỗi không rỗng.",
            reason=f"missing_{key}",
        )
    return value


def load_tracking_catalog_capture(
    path: Path,
) -> Optional[TrackingCatalogSnapshot]:
    """File không tồn tại → `None` (danh mục chưa được capture lần nào).

    Mọi hư hỏng khác raise — cùng lý do với `capture_file.py`: một danh mục
    rỗng im lặng làm mọi sản phẩm Pending và trông y hệt "chưa ai nhập dữ liệu".
    """
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InvalidTrackingCatalogCaptureFileError(
            f"{path}: không đọc/parse được file capture danh mục: {exc}.",
            reason="unreadable",
        ) from exc
    if not isinstance(payload, dict):
        raise InvalidTrackingCatalogCaptureFileError(
            f"{path}: nội dung phải là một ánh xạ khoá-giá trị.",
            reason="not_a_mapping",
        )

    capture_id = _text(payload, "capture_id", path)
    captured_by = _text(payload, "captured_by", path)
    source_system_ref = _text(payload, "source_system_ref", path)
    content_hash = _text(payload, "content_hash", path)
    raw_at = _text(payload, "captured_at", path)
    try:
        captured_at = _dt.datetime.fromisoformat(raw_at)
    except ValueError as exc:
        raise InvalidTrackingCatalogCaptureFileError(
            f"{path}: captured_at không phải ISO-8601 hợp lệ ({raw_at!r}).",
            reason="invalid_datetime",
        ) from exc

    try:
        capture_status = CaptureStatus(payload.get("capture_status"))
    except ValueError as exc:
        raise InvalidTrackingCatalogCaptureFileError(
            f"{path}: capture_status={payload.get('capture_status')!r} ngoài "
            f"enum đóng {[s.value for s in CaptureStatus]}.",
            reason="invalid_capture_status",
        ) from exc

    if capture_status is CaptureStatus.FAILED:
        return TrackingCatalogSnapshot(
            capture_id=capture_id,
            captured_at=captured_at,
            captured_by=captured_by,
            source_system_ref=source_system_ref,
            content_hash=content_hash,
            capture_status=capture_status,
            failure_reason=payload.get("failure_reason") or "không ghi lý do",
        )

    raw_rows = payload.get("rows")
    if not isinstance(raw_rows, list):
        raise InvalidTrackingCatalogCaptureFileError(
            f"{path}: thiếu khối 'rows' hoặc nó không phải một danh sách.",
            reason="missing_rows_block",
        )
    rows: list[TrackingCatalogRow] = []
    for number, raw in enumerate(raw_rows, start=1):
        if not isinstance(raw, dict):
            raise InvalidTrackingCatalogCaptureFileError(
                f"{path}: dòng danh mục #{number} phải là một ánh xạ.",
                reason="malformed_row",
            )
        code = raw.get("tracking_code")
        if not isinstance(code, str) or not code.strip():
            raise InvalidTrackingCatalogCaptureFileError(
                f"{path}: dòng danh mục #{number} thiếu 'tracking_code'.",
                reason="missing_tracking_code",
            )
        present = raw.get("present_in_board")
        if not isinstance(present, bool):
            raise InvalidTrackingCatalogCaptureFileError(
                f"{path}: dòng #{number} 'present_in_board' phải là bool tường "
                "minh — vắng mặt không được đọc thành True.",
                reason="missing_present_in_board",
            )
        alt = raw.get("alt") or []
        if not isinstance(alt, list):
            raise InvalidTrackingCatalogCaptureFileError(
                f"{path}: dòng #{number} 'alt' phải là một danh sách.",
                reason="malformed_alt",
            )
        rows.append(
            TrackingCatalogRow(
                tracking_code=code,
                present_in_board=present,
                name=raw.get("name"),
                alt=tuple(str(a) for a in alt),
            )
        )

    raw_alias = payload.get("alias_map") or {}
    if not isinstance(raw_alias, dict):
        raise InvalidTrackingCatalogCaptureFileError(
            f"{path}: 'alias_map' phải là một ánh xạ old_code → primary_code.",
            reason="malformed_alias_map",
        )

    # Capture tool hiện hành ghi SHA-256 của đúng payload identity canonical.
    # So sánh lại ở consumer giúp phát hiện file đã bị sửa sau immutable write.
    # Các artifact trước khi acquisition tool tồn tại dùng hash opaque, nên giữ
    # tương thích đọc cho đến khi chúng được recapture/migrate có chủ đích.
    if content_hash.startswith("sha256:"):
        expected_hash = canonical_content_hash(raw_rows, raw_alias)
        if content_hash != expected_hash:
            raise InvalidTrackingCatalogCaptureFileError(
                f"{path}: content_hash không khớp rows/alias_map; capture có thể "
                "đã bị sửa sau khi ghi bất biến.",
                reason="content_hash_mismatch",
            )

    return TrackingCatalogSnapshot(
        capture_id=capture_id,
        captured_at=captured_at,
        captured_by=captured_by,
        source_system_ref=source_system_ref,
        content_hash=content_hash,
        capture_status=capture_status,
        rows=tuple(rows),
        alias_map_rows=tuple(
            (str(old), str(primary)) for old, primary in raw_alias.items()
        ),
    )


# ---------------------------------------------------------------------------
# Ảnh chụp `inv.map` (E-D2) — authority cho câu tên hàng kế toán đầy đủ
# ---------------------------------------------------------------------------


class InvalidTrackingInvMapCaptureFileError(ValueError):
    def __init__(self, message: str, *, reason: str) -> None:
        super().__init__(message)
        self.reason = reason


def load_tracking_inv_map_capture(
    path: Path,
) -> Optional[TrackingInvMapSnapshot]:
    """File không tồn tại → `None` (`inv.map` chưa được capture lần nào —
    nguồn TUỲ CHỌN, cùng khuôn `load_tracking_catalog_capture`).

    Mọi hư hỏng khác raise: một `inv.map` rỗng/sai hình dạng im lặng đọc
    thành "không có mục nào" sẽ làm mọi khoá tra ra `None` — trông y hệt
    "chưa ai duyệt dòng này", trong khi thật ra là capture hỏng.
    """
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise InvalidTrackingInvMapCaptureFileError(
            f"{path}: không đọc/parse được file capture inv.map: {exc}.",
            reason="unreadable",
        ) from exc
    if not isinstance(payload, dict):
        raise InvalidTrackingInvMapCaptureFileError(
            f"{path}: nội dung phải là một ánh xạ khoá-giá trị.",
            reason="not_a_mapping",
        )

    capture_id = _text(payload, "capture_id", path)
    captured_by = _text(payload, "captured_by", path)
    source_system_ref = _text(payload, "source_system_ref", path)
    content_hash = _text(payload, "content_hash", path)
    raw_at = _text(payload, "captured_at", path)
    try:
        captured_at = _dt.datetime.fromisoformat(raw_at)
    except ValueError as exc:
        raise InvalidTrackingInvMapCaptureFileError(
            f"{path}: captured_at không phải ISO-8601 hợp lệ ({raw_at!r}).",
            reason="invalid_datetime",
        ) from exc

    try:
        capture_status = CaptureStatus(payload.get("capture_status"))
    except ValueError as exc:
        raise InvalidTrackingInvMapCaptureFileError(
            f"{path}: capture_status={payload.get('capture_status')!r} ngoài "
            f"enum đóng {[s.value for s in CaptureStatus]}.",
            reason="invalid_capture_status",
        ) from exc

    if capture_status is CaptureStatus.FAILED:
        return TrackingInvMapSnapshot(
            capture_id=capture_id,
            captured_at=captured_at,
            captured_by=captured_by,
            source_system_ref=source_system_ref,
            content_hash=content_hash,
            capture_status=capture_status,
            failure_reason=payload.get("failure_reason") or "không ghi lý do",
        )

    raw_entries = payload.get("entries")
    if not isinstance(raw_entries, dict):
        raise InvalidTrackingInvMapCaptureFileError(
            f"{path}: thiếu khối 'entries' hoặc nó không phải một ánh xạ.",
            reason="missing_entries_block",
        )
    entries: list[tuple[str, str]] = []
    for key, value in raw_entries.items():
        if not isinstance(key, str) or not key.strip():
            raise InvalidTrackingInvMapCaptureFileError(
                f"{path}: khoá 'entries' rỗng/không phải chuỗi: {key!r}.",
                reason="malformed_entry_key",
            )
        if not isinstance(value, str) or not value.strip():
            raise InvalidTrackingInvMapCaptureFileError(
                f"{path}: entries[{key!r}] phải là chuỗi không rỗng, nhận "
                f"{value!r}.",
                reason="malformed_entry_value",
            )
        entries.append((key, value))
    entries.sort(key=lambda item: item[0])

    if content_hash.startswith("sha256:"):
        expected_hash = inv_map_canonical_content_hash(dict(entries))
        if content_hash != expected_hash:
            raise InvalidTrackingInvMapCaptureFileError(
                f"{path}: content_hash không khớp entries; capture có thể đã "
                "bị sửa sau khi ghi bất biến.",
                reason="content_hash_mismatch",
            )

    return TrackingInvMapSnapshot(
        capture_id=capture_id,
        captured_at=captured_at,
        captured_by=captured_by,
        source_system_ref=source_system_ref,
        content_hash=content_hash,
        capture_status=capture_status,
        entries=tuple(entries),
    )


# ---------------------------------------------------------------------------
# Nguồn Public Purchase (E-A)
# ---------------------------------------------------------------------------


def load_public_purchase_source(
    path: Path,
) -> Optional[PublicPurchaseSourceVersion]:
    """File không tồn tại → `None`. File tồn tại → loader STRICT của `INV-02`
    quyết định; mọi lỗi cấu trúc raise `PublicPurchaseSourceError`."""
    if not path.exists():
        return None
    return PublicPurchaseSourceLoader.load(load_yaml(path))


# ---------------------------------------------------------------------------
# Ảnh chụp bằng chứng của MỘT lần import
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PriceEvidenceSnapshot:
    """Định danh của MỌI nguồn đã dùng cho một lần import — để mở lại được.

    Mỗi `PriceResolutionRecord` mang chính object này (cùng một instance cho
    cả lần import), nên "hai dòng cùng report có dùng chung bộ bằng chứng
    không" là một câu hỏi trả lời được bằng `is`, không phải bằng niềm tin.
    """

    tracking_price_history_capture_id: Optional[str]
    tracking_price_history_captured_at: Optional[_dt.datetime]
    tracking_catalog_capture_id: Optional[str]
    tracking_inv_map_capture_id: Optional[str]
    public_purchase_version_id: Optional[str]
    public_purchase_content_hash: Optional[str]
    identity_store_revision: Optional[int]
    business_timezone_label: str
    business_timezone_provenance: str
    vendor_price_source: str
    """`TASK-105C HistoricalVendorMin` (P01). Chuỗi này KHÔNG BAO GIỜ là một
    absence đã xác định — xem `composition.py`, mục "P01/P03"."""


VENDOR_SOURCE_NOT_AUTHORIZED = "NOT_AUTHORIZED:TASK-105C"


@dataclass(frozen=True)
class PriceResolutionSources:
    """Toàn bộ bằng chứng giá của MỘT lần import, đã đóng băng."""

    business_timezone: BusinessTimezone
    tracking_price_history: Optional[TrackingPriceHistorySnapshot]
    tracking_catalog: Optional[TrackingCatalogSnapshot]
    public_purchase: Optional[PublicPurchaseSourceVersion]
    identity_store_view: Optional[StoreView]
    tracking_inv_map: Optional[TrackingInvMapSnapshot] = None
    """`inv.map` — authority cho câu tên hàng kế toán đầy đủ (S068 follow-up).

    TUỲ CHỌN, cùng khuôn `pp_version` (DEC-165): vắng mặt = "chưa nối",
    resolver vẫn chạy đúng đường `alias.map`/`board` cũ, không Pending hàng
    loạt vì thiếu nguồn phụ trợ này.
    """
    tracking_identity_authority: bool = True
    """Production dùng `alias.map` + khoá `board` của Tracking làm authority.

    `False` chỉ giữ đường legacy cho fixture/compatibility đã được dựng tường
    minh; loader production và Owner workflow luôn dùng mặc định `True`.
    """

    @property
    def evidence_snapshot(self) -> PriceEvidenceSnapshot:
        history = self.tracking_price_history
        catalog = self.tracking_catalog
        inv_map = self.tracking_inv_map
        pp = self.public_purchase
        return PriceEvidenceSnapshot(
            tracking_price_history_capture_id=(
                history.capture_id if history else None
            ),
            tracking_price_history_captured_at=(
                history.captured_at if history else None
            ),
            tracking_catalog_capture_id=catalog.capture_id if catalog else None,
            tracking_inv_map_capture_id=inv_map.capture_id if inv_map else None,
            public_purchase_version_id=pp.version_id if pp else None,
            public_purchase_content_hash=pp.content_hash if pp else None,
            identity_store_revision=(
                self.identity_store_view.revision
                if self.identity_store_view is not None
                else None
            ),
            business_timezone_label=self.business_timezone.label,
            business_timezone_provenance=self.business_timezone.provenance,
            vendor_price_source=VENDOR_SOURCE_NOT_AUTHORIZED,
        )


def load_price_resolution_sources(
    *,
    config_dir: Path,
    tracking_price_history_path: Path = TRACKING_PRICE_HISTORY_CAPTURE_PATH,
    tracking_catalog_path: Path = TRACKING_CATALOG_CAPTURE_PATH,
    tracking_inv_map_path: Path = TRACKING_INV_MAP_CAPTURE_PATH,
    public_purchase_path: Path = PUBLIC_PURCHASE_SOURCE_PATH,
    identity_store_log_path: Path = IDENTITY_STORE_LOG_PATH,
) -> PriceResolutionSources:
    """Đọc mọi nguồn ĐÚNG MỘT LẦN và đóng băng chúng.

    Store identity luôn dựng được (log vắng mặt = store rỗng, `INV-79`: "một
    store rỗng là trạng thái khởi đầu ĐÚNG"), khác với các nguồn capture khác
    — vắng mặt ở đó nghĩa là chưa capture lần nào.
    """
    store = JsonlProductIdentityStore(
        log_path=identity_store_log_path,
        index_path=identity_store_log_path.with_suffix(".index.json"),
    )
    return PriceResolutionSources(
        business_timezone=load_business_timezone(config_dir),
        tracking_price_history=load_tracking_price_history_capture(
            tracking_price_history_path
        ),
        tracking_catalog=load_tracking_catalog_capture(tracking_catalog_path),
        tracking_inv_map=load_tracking_inv_map_capture(tracking_inv_map_path),
        public_purchase=load_public_purchase_source(public_purchase_path),
        identity_store_view=store.read_at_revision(store.current_revision()),
    )
