"""E-D2 — `TrackingInvMapSnapshot`: `inv.map` là authority CHO FULL ACCOUNTING
DESCRIPTION, không phải candidate-tier.

## Vì sao file này tách khỏi `tracking_catalog.py`

`board`/`alias.map` (`tracking_catalog.py`) khoá bằng MÃ sản phẩm — cùng
namespace với chính accounting code khi nó trùng khớp. `inv.map` khoá bằng
CÂU TÊN HÀNG kế toán đã qua `normCode()` của Tracking — một phép biến đổi
khác hẳn (`§ normCode`, dưới đây). Trộn hai bảng vào một schema sẽ làm mất
chiều "khoá này là mã hay là câu tên hàng", đúng lớp lỗi mà hai khoá tách rời
của `keys.py` (`raw_identity_key` vs `normalized_matching_aid`) đã tồn tại để
chặn — nên `inv.map` được một loader/schema RIÊNG.

## Owner decision (S068 follow-up, sau `docs/sessions/S068-first-real-post-authority-cohort-blocked.md`)

`inv.map` là bảng do NGƯỜI của Tracking duyệt — cùng tiền lệ `alias.map` mà
Owner đã chấp nhận làm authority production (không candidate-tier D-05 của
`docs/spec/TASK-105D-DATA-CONTRACT.md` §4.3). Một khớp `inv.map` hợp lệ (khoá
tồn tại, giá trị khác `"-"`, target còn hợp lệ trong `board`) là authoritative
identity — KHÔNG cần một `confirmation_action` thứ hai từ Reports.

## `normCode()` — port nguyên văn, không xấp xỉ

Bằng chứng đã audit (`docs/tasks/TASK-108B-eligible-costs-owner-definition.md`
§56, dẫn `public/index.html:8906`; xác nhận lại ở
`docs/spec/TASK-105D-DATA-CONTRACT.md` §4.2):

```text
normCode(s) = s.toUpperCase() rồi bỏ MỌI ký tự ngoài [A-Z0-9]  (JS regex,
              KHÔNG unicode-aware — dấu tiếng Việt bị XOÁ HẲN, không chuyển
              về chữ cái gốc không dấu)
inv.map key = "N_" + normCode(full_description)[:80]
```

Đây KHÔNG phải suy luận identity: nó chỉ định vị một khoá `inv.map` đã có sẵn
và đã được người duyệt (`D-04`/`DEC-147` §4 vẫn cấm tuyệt đối `extractCode()`
— hàm này không rút mã từ câu tên hàng, nó chỉ tính lại đúng cái khoá mà
Tracking đã tự tính khi ghi `inv.map`).

## `"-"` là Ignore đã người xác nhận, không phải "chưa biết"

Một khoá tồn tại với giá trị `"-"` nghĩa là một người của Tracking ĐÃ xem
dòng này và kết luận nó không phải một sản phẩm cần map (`§ lookup`). Đây là
một sự kiện khác hẳn "khoá vắng mặt" (chưa ai xem), nên `lookup()` phân biệt
tường minh ba kết cục: mã, `"-"`, hoặc `None`.

## Ranh giới kiến trúc giữ nguyên (`ADR-101`, `DEC-152` §6)

File này KHÔNG import mạng, không biết RTDB hay Data Contract V1 tồn tại —
đúng ranh giới `CHECK-105D-17` đã thi hành cho `tracking_catalog.py`. Phần
chạm mạng nằm ở `tools/tracking/capture_inv_map.py`.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from app.modules.product.identity.tracking_catalog import (
    CaptureStatus,
    TrackingCaptureFailedError,
)

IGNORE_VALUE = "-"
"""`inv.map[key] == "-"` — Ignore đã người xác nhận (`§ "-" là Ignore`)."""

_KEY_PREFIX = "N_"
_KEY_MAX_LEN = 80
_NON_ALNUM = re.compile(r"[^A-Z0-9]")


def norm_code(text: str) -> str:
    """`normCode()` của Tracking, port nguyên văn (`§ normCode()` ở trên).

    CỐ Ý không dùng `fold()`/`normalize_text()` của Reports (`validation/text.py`):
    đó là chuẩn hoá Unicode-aware, giữ dấu tiếng Việt — khác hẳn ngữ nghĩa ASCII
    strip-only của `normCode()`. Hai phép biến đổi phục vụ hai mục đích khác
    nhau (tìm candidate cho Reports vs định vị khoá `inv.map` của Tracking) và
    không được gộp làm một, kể cả khi trông giống nhau trên phần lớn input.
    """
    return _NON_ALNUM.sub("", text.upper())


def inv_map_key(full_description: str) -> str:
    """`"N_" + normCode(full_description)[:80]` — đúng khoá `inv.map` của Tracking."""
    return _KEY_PREFIX + norm_code(full_description)[:_KEY_MAX_LEN]


def canonical_content_hash(entries: dict[str, str]) -> str:
    """Hash canonical trên đúng nội dung `entries` — cùng khuôn với
    `tracking_catalog.canonical_content_hash()` (provenance không thuộc payload)."""
    payload = json.dumps(
        {"entries": entries}, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    )
    return "sha256:" + hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class TrackingInvMapSnapshot:
    """Ảnh chụp bất biến của `inv.map` tại một thời điểm — `E-D2`.

    `entries` là `<khoá inv.map> -> <mã board> | "-"`, ĐÚNG NHƯ Tracking trả
    về; không lọc, không rút gọn, không chuẩn hoá lại giá trị.
    """

    capture_id: str
    captured_at: datetime
    captured_by: str
    source_system_ref: str
    content_hash: str
    capture_status: CaptureStatus
    entries: tuple[tuple[str, str], ...] = ()
    failure_reason: Optional[str] = None

    def __post_init__(self) -> None:
        if self.capture_status is CaptureStatus.FAILED and not self.failure_reason:
            raise ValueError("capture_status = FAILED bắt buộc có failure_reason")

    def require_complete(self) -> "TrackingInvMapSnapshot":
        """`INV-12` cùng khuôn — snapshot FAILED là LỖI, không phải Pending."""
        if self.capture_status is not CaptureStatus.COMPLETE:
            raise TrackingCaptureFailedError(
                f"inv_map capture {self.capture_id} có capture_status="
                f"{self.capture_status.value} ({self.failure_reason}); resolver "
                "từ chối chạy — đây là LỖI, không phải Pending (INV-12)"
            )
        return self

    def lookup(self, full_description: str) -> Optional[str]:
        """`None` = khoá vắng mặt (chưa classify). `"-"` = Ignore đã xác nhận.
        Chuỗi khác = mã board đã người xác nhận — CHƯA chắc còn hợp lệ trong
        board hiện tại, caller (resolver) tự kiểm `present_in_board`."""
        key = inv_map_key(full_description)
        for entry_key, value in self.entries:
            if entry_key == key:
                return value
        return None

    def as_dict(self) -> dict[str, str]:
        return dict(self.entries)
