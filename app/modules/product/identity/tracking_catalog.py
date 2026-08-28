"""E-D `TrackingCatalogSnapshot` — hợp đồng CHỈ ĐỌC, data contract §4.

## Ranh giới kiến trúc là một phần của hợp đồng, không phải một lời hứa

`ADR-101` + `DEC-152` §6: phần chạm mạng nằm NGOÀI `app/modules/`
(ví dụ `tools/tracking/`), đọc RTDB read-only rồi ghi ra một file snapshot bất
biến. `app/modules/product/**` chỉ đọc snapshot đó và **không biết RTDB tồn
tại**. Vì thế trong file này không có URL, không có client, không có import
mạng — và `CHECK-105D-17` khẳng định điều đó bằng một assertion import-graph
chứ không bằng câu văn này.

## `capture_status = FAILED` là LỖI, không phải "sản phẩm không tồn tại"

`INV-12` là chỗ dễ sai nhất của cả file. Một lần capture hỏng và một danh mục
thật sự rỗng là hai sự kiện khác nhau: cái đầu là hệ thống hỏng, cái sau là
kết luận về dữ liệu. Trộn hai thứ đó lại thì mọi sản phẩm trên đời trở thành
Pending sau một lần mất mạng — và tệ hơn, một mapping đã confirm có thể bị đọc
thành "target biến mất". Nên resolver TỪ CHỐI chạy trên một snapshot FAILED.

## Tên không phải identity

`INV-13`/`INV-21`: `tracking_code` (khoá node `board/<MÃ>` sau `aliasOf()`) là
canonical code. `name` và `alt[]` chỉ là evidence khớp. Đổi tên hiển thị không
được làm mất một mapping đã confirm — đó là `CHECK-105D-10` Phần B1.

`D-04` (`DEC-147` §4): tuyệt đối không tái phát minh `extractCode()`. Tracking
đã thử rút mã từ câu tên hàng bằng máy và bỏ hẳn vì sai trên tài sản thật.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

from app.modules.validation.text import fold


class CaptureStatus(str, Enum):
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


class TrackingCaptureFailedError(RuntimeError):
    """`INV-12` — snapshot FAILED. Lỗi cứng, KHÔNG BAO GIỜ chuyển thành Pending."""


class TrackingCaptureNotFoundError(LookupError):
    """Không tìm thấy `capture_id` được ghim. Lỗi cứng, không fallback "mới nhất"."""


class ImmutableCaptureError(RuntimeError):
    """`INV-11` — cấm ghi đè một `capture_id` đã tồn tại."""


@dataclass(frozen=True)
class TrackingCatalogRow:
    tracking_code: str
    present_in_board: bool
    name: Optional[str] = None
    alt: tuple[str, ...] = ()


@dataclass(frozen=True)
class TrackingCatalogSnapshot:
    """Ảnh chụp bất biến của danh mục Tracking tại một thời điểm."""

    capture_id: str
    captured_at: datetime
    captured_by: str
    source_system_ref: str
    content_hash: str
    capture_status: CaptureStatus
    rows: tuple[TrackingCatalogRow, ...] = ()
    alias_map_rows: tuple[tuple[str, str], ...] = ()
    failure_reason: Optional[str] = None

    def __post_init__(self) -> None:
        if self.capture_status is CaptureStatus.FAILED and not self.failure_reason:
            raise ValueError("capture_status = FAILED bắt buộc có failure_reason")

    def require_complete(self) -> "TrackingCatalogSnapshot":
        """`INV-12` — cổng vào duy nhất cho mọi đường đọc snapshot."""
        if self.capture_status is not CaptureStatus.COMPLETE:
            raise TrackingCaptureFailedError(
                f"capture {self.capture_id} có capture_status="
                f"{self.capture_status.value} ({self.failure_reason}); "
                "resolver từ chối chạy — đây là LỖI, không phải Pending (INV-12)"
            )
        return self

    def row_for(self, tracking_code: str) -> Optional[TrackingCatalogRow]:
        for row in self.rows:
            if row.tracking_code == tracking_code:
                return row
        return None

    def alias_map(self) -> dict[str, str]:
        """`old_code → primary_code` của `alias.map` (`INV-16`).

        Bảng này do người của Tracking duyệt — evidence rất mạnh, nhưng phê
        duyệt của Tracking không phải phê duyệt của Reports (`D-05`). Nó chỉ
        sinh candidate #1, không bao giờ tự di chuyển một mapping đã confirm.
        """
        return {old: primary for old, primary in self.alias_map_rows}

    def exact_match_codes(self, *, raw_key: str, aid: str) -> tuple[tuple[str, str], ...]:
        """Mọi `tracking_code` khớp EXACT với raw identity, kèm trường đã khớp.

        "Exact" ở đây là exact sau đúng phép chuẩn hoá đã được canonical
        authorize (`fold`, `DEC-145` §2) — không similarity, không edit
        distance, không token overlap (`§4.3`, `INV-01`).

        Trả về tuple `(tracking_code, matched_on)`, thứ tự ổn định theo thứ tự
        dòng trong snapshot để `INV-64` không phụ thuộc thứ tự dict.
        """
        hits: list[tuple[str, str]] = []
        for row in self.rows:
            matched = _match_field(row, raw_key=raw_key, aid=aid)
            if matched is not None:
                hits.append((row.tracking_code, matched))
        return tuple(hits)


def _match_field(row: TrackingCatalogRow, *, raw_key: str, aid: str) -> Optional[str]:
    """Trường nào của dòng này khớp exact — theo đúng thứ tự ưu tiên §4.3."""
    if row.tracking_code == raw_key or fold(row.tracking_code) == aid:
        return "TRACKING_CODE"
    if row.name and (row.name == raw_key or fold(row.name) == aid):
        return "TRACKING_NAME"
    for alt in row.alt:
        if alt == raw_key or fold(alt) == aid:
            return "TRACKING_ALT"
    return None


class TrackingSnapshotRepository:
    """Kho snapshot bất biến, tra theo `capture_id`.

    Không có `delete`, không có `update` (`INV-11`, `INV-67`). `register()` từ
    chối một `capture_id` đã tồn tại thay vì ghi đè — `CHECK-105D-17` fixture
    (2) đi đúng đường đó.
    """

    def __init__(self) -> None:
        self._by_id: dict[str, TrackingCatalogSnapshot] = {}

    def register(self, snapshot: TrackingCatalogSnapshot) -> None:
        if snapshot.capture_id in self._by_id:
            raise ImmutableCaptureError(
                f"INV-11: capture_id {snapshot.capture_id} đã tồn tại; "
                "snapshot là bất biến, không ghi đè"
            )
        self._by_id[snapshot.capture_id] = snapshot

    def get(self, capture_id: str) -> TrackingCatalogSnapshot:
        try:
            return self._by_id[capture_id]
        except KeyError:
            raise TrackingCaptureNotFoundError(
                f"không có tracking_capture_id {capture_id!r}; "
                "KHÔNG fallback sang capture mới nhất (INV-57)"
            ) from None
