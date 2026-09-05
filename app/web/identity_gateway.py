"""`DEC-185` — CỬA DUY NHẤT từ giao diện Reports tới thẩm quyền Product Identity.

## Reports là bên TIÊU THỤ, và file này giữ cho điều đó đúng

`PHB-01` đã chốt: Tracking là thẩm quyền Product Identity, Reports là bên tiêu
thụ hợp đồng. Owner yêu cầu thêm MỘT bề mặt phân loại ngay trong bảng kê —
nhưng bề mặt đó không được biến Reports thành thẩm quyền thứ hai.

Ranh giới được giữ bằng CẤU TẠO, không bằng lời hứa, và ba điều dưới đây là
cách nó được giữ:

1. **Danh mục sản phẩm chuẩn đến TỪ Tracking.** Người dùng chọn trong danh
   mục Tracking đã capture; Reports không sinh ra, không đoán ra và không tự
   đặt tên một mã sản phẩm nào. Không có Tracking ⟹ KHÔNG có danh sách, và
   màn hình nói thẳng ra điều đó thay vì đưa ra một ô gõ tự do.

2. **Không ghi `inv.map`.** Module này không có một đường ghi nào ra
   Tracking. `inv.map` là bảng do người của Tracking duyệt
   (`tracking_inv_map.py` § Owner decision) và nó vẫn vậy sau bản thay đổi
   này. Quyết định của Owner ở đây được ghi vào ĐÚNG chỗ mà một quyết định
   của con người phía Reports vẫn luôn được ghi: log append-only
   `ProductIdentityStore`, với `mapping_source = HUMAN_CONFIRMATION`.

3. **Đúng một `confirmation_action` đã có sẵn.** Lệnh được gửi đi là
   `ConfirmMapping` — cùng lệnh mà CLI `app/modules/product/identity/cli.py`
   gửi, qua cùng `store.append()`, qua cùng cổng `INV-01`. Không có lệnh mới
   nào được phát minh, nên `CHECK-105D-22` (c) vẫn đúng: mọi
   `confirmation_action` vẫn tiếp cận được bằng CLI, và bề mặt mới này chỉ là
   một cách gọi thứ hai tới cùng một thẩm quyền, không phải một đường vòng
   qua nó.

## Vì sao xác nhận KHÔNG làm giá nhập xuất hiện

`ECONOMIC_ISOLATION` của `PHB-01` giữ nguyên. Nhận diện xong nghĩa là máy đã
biết dòng này là mặt hàng nào — nó KHÔNG có nghĩa là đã biết mua vào bao
nhiêu. Trên chính production, vector nghiệm thu của `PHB-01` kết thúc đúng ở
trạng thái đó: `IDENTITY_UNRESOLVED` biến mất, còn giá vẫn `PENDING`.

Vì thế kết quả đúng của một lần phân loại thành công là dòng chuyển từ
"Chưa phân loại" sang "Thiếu giá" — và `line_identity` là nơi phép chuyển đó
được viết ra.
"""

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from app.modules.product.identity.audit import AffectedScope
from app.modules.product.identity.commands import ConfirmMapping
from app.modules.product.identity.evidence import (
    Evidence, MatchedOn, ResolutionMethod,
)
from app.modules.product.identity.identity import CanonicalProductIdentity, Namespace
from app.modules.product.identity.keys import raw_identity_key
from app.modules.product.identity.mapping import (
    MappingStatus, SOURCE_SYSTEM_REPORTS_SALES,
)
from app.modules.product.identity.store import JsonlProductIdentityStore

#: Log quyết định Product Identity của Phase 1. Cùng đường dẫn mà CLI dùng —
#: một đường dẫn thứ hai sẽ là một store thứ hai, đúng thứ `D-06` cấm.
DEFAULT_LOG_PATH = Path("data/product_identity/mappings.jsonl")
DEFAULT_INDEX_PATH = Path("data/product_identity/index.json")

#: Số mặt hàng Tracking hiện ra trong bảng chọn. Đây là một giới hạn TRÌNH
#: BÀY: một danh sách vài nghìn dòng trong lòng một bảng kê không phải "tương
#: tác nhỏ nhất có thể" mà Owner yêu cầu. Người dùng thu hẹp bằng ô tìm.
CANDIDATE_LIMIT = 40

NO_TRACKING_NOTE = (
    "Chưa đọc được danh mục sản phẩm của Tracking, nên chưa chọn được mặt "
    "hàng chuẩn. Danh mục là thẩm quyền của Tracking — Reports không tự dựng "
    "một danh sách thay thế."
)

CONFIRM_OK_NOTE = (
    "Đã ghi nhận phân loại. Dòng này đã nhận diện được mặt hàng; giá nhập vẫn "
    "do Tracking quyết định, nên nếu chưa có giá thì dòng chuyển sang trạng "
    "thái Thiếu giá chứ không tự sinh ra một con số."
)


class IdentityGatewayError(RuntimeError):
    """Không thực hiện được thao tác phân loại, kèm câu nói rõ lý do."""


@dataclass(frozen=True)
class Candidate:
    """Một mặt hàng chuẩn của Tracking để Owner chọn."""

    code: str
    description: str

    @property
    def label(self) -> str:
        return f"{self.code} — {self.description}" if self.description else self.code


def build_store(
    log_path: Optional[Path] = None, index_path: Optional[Path] = None,
) -> JsonlProductIdentityStore:
    return JsonlProductIdentityStore(
        log_path=log_path or DEFAULT_LOG_PATH,
        index_path=index_path or DEFAULT_INDEX_PATH)


def confirmed_keys(store) -> frozenset[str]:
    """Các `raw_identity_key` đã có mapping `CONFIRMED` đang hiệu lực.

    Đây là thứ `line_identity.state_of` cần để biết một dòng đã được xác nhận
    sau lần chạy sổ gần nhất. Đọc qua `read_at_revision(current)` — tức chiếu
    lại log, không đọc index — vì `INV-63` nói LOG THẮNG, và một index cũ ở
    đây sẽ làm màn hình nói rằng một mặt hàng vừa được phân loại thì vẫn chưa.

    Store không đọc được (chưa có file, đĩa lỗi) ⟹ tập RỖNG, không phải một
    lỗi trang: hệ quả là màn hình hiện đúng trạng thái mà pipeline đã lưu —
    thận trọng theo hướng "chưa phân loại", không theo hướng ngược lại.
    """
    if store is None:
        return frozenset()
    try:
        view = store.read_at_revision(store.current_revision())
    except Exception:  # noqa: BLE001 — xem docstring
        return frozenset()
    return frozenset(
        mapping.raw_identity_key
        for mapping in view.alias_index().values()
        if mapping.status is MappingStatus.CONFIRMED
        and mapping.source_system == SOURCE_SYSTEM_REPORTS_SALES
    )


def candidates(snapshot, *, query: Optional[str] = None) -> list[Candidate]:
    """Mặt hàng chuẩn của Tracking, lọc theo `query`, giới hạn để đọc được.

    `snapshot is None` ⟹ danh sách RỖNG. Không có nhánh nào dựng candidate từ
    dữ liệu của Reports: nếu Tracking không nói được, câu trả lời đúng là
    "chưa biết", không phải một danh sách trông có vẻ hợp lý.

    Chỉ mã CÒN trên board hiện tại được đưa ra chọn (`present_in_board`).
    `INV-14c` cho phép HIỂN THỊ một mã đã biến mất khi nó là bằng chứng của
    một lần resolve cũ — nhưng đây không phải chỗ đó: đây là danh sách để
    Owner tạo một mapping MỚI, và trỏ một mapping mới vào một mã Tracking đã
    bỏ là dựng sẵn một bản ghi hỏng.
    """
    if snapshot is None:
        return []
    needle = (query or "").strip().casefold()
    found = []
    for row in snapshot.rows:
        if not row.present_in_board:
            continue
        name = row.name or ""
        if needle and needle not in row.tracking_code.casefold() \
                and needle not in name.casefold():
            continue
        found.append(Candidate(code=row.tracking_code, description=name))
        if len(found) >= CANDIDATE_LIMIT:
            break
    return found


def confirm_identity(
    store, *, product_raw: str, tracking_code: str, snapshot,
    actor_id: str, affected_orders: tuple[str, ...] = (),
    affected_lines: int = 0, client_request_id: Optional[str] = None,
) -> str:
    """Ghi quyết định phân loại của Owner qua thẩm quyền đã được nghiệm thu.

    Ba cửa, mỗi cửa đóng một cách sai khác nhau, và cả ba kiểm ở ĐÂY chứ
    không chỉ trên giao diện:

    1. `product_raw` phải dựng được khoá định danh. Không có tên hàng thì
       không có gì để xác nhận (`EmptyRawIdentityError` — `INV-30`/`INV-87`).
    2. `tracking_code` phải CÓ THẬT trong danh mục Tracking đang đọc được.
       Không kiểm điều này thì một mã gõ tay sẽ thành một mapping `CONFIRMED`
       trỏ tới hư không, và Reports vừa tự phong mình làm thẩm quyền.
    3. Lệnh gửi đi là `ConfirmMapping` — `store.append()` giữ nguyên `INV-01`
       (similarity không bao giờ tự thành `CONFIRMED`), `INV-59` (version) và
       `INV-68`/`INV-69` (idempotency). Không cửa nào trong số đó bị đi vòng.

    `matched_on = MANUAL_SEARCH` nói đúng bản chất bằng chứng: một người đã
    tự tìm trong danh mục Tracking và chọn, chứ không phải một phép so chuỗi
    nào khớp. `resolution_method` vẫn là `SIMILARITY_RANKED` — enum
    `ResolutionMethod` là ĐÓNG (thêm giá trị cần một quyết định Owner và một
    task riêng), và `SIMILARITY_RANKED` là giá trị NGOÀI tập auto-resolve, tức
    giá trị an toàn: một mapping mang nó không bao giờ tự trở thành CONFIRMED
    mà không có `confirmation_action` của người. Chiều "người chọn" không bị
    mất — nó nằm ở `matched_on` và ở `mapping_source = HUMAN_CONFIRMATION`.

    `affected_orders`/`affected_lines` là phạm vi THẬT mà tầng route đếm được
    từ chính kỳ đang xem: mọi dòng dùng chung khoá định danh này đều đổi trạng
    thái, không riêng dòng vừa bấm (`INV-76`/`INV-87`). Truyền số đếm thật
    thay vì `1` là điều làm bản ghi audit đọc lại được.
    """
    if store is None:
        raise IdentityGatewayError(
            "Chưa cấu hình nơi lưu quyết định Product Identity.")
    key = (product_raw or "").strip()
    if not key:
        raise IdentityGatewayError(
            "Dòng này không có tên hàng trên sổ, nên chưa có gì để phân loại.")
    code = (tracking_code or "").strip()
    if not code:
        raise IdentityGatewayError("Chưa chọn mặt hàng của Tracking.")
    if snapshot is None or snapshot.row_for(code) is None:
        raise IdentityGatewayError(
            f"Mã {code!r} không có trong danh mục Tracking đang đọc được. "
            "Danh mục là thẩm quyền của Tracking — Reports không tự thêm mã.")

    identity_key = raw_identity_key(key)
    command = ConfirmMapping(
        actor_id=actor_id,
        client_request_id=client_request_id or str(uuid.uuid4()),
        expected_version=store.current_revision(),
        tracking_capture_id=snapshot.capture_id,
        affected_scope=AffectedScope(
            distinct_identity_count=1,
            affected_order_ids=tuple(affected_orders),
            affected_line_count=affected_lines,
            computed_at_revision=store.current_revision(),
        ),
        raw_identity_key=identity_key,
        raw_product_identity=key,
        source_system=SOURCE_SYSTEM_REPORTS_SALES,
        target=CanonicalProductIdentity(
            namespace=Namespace.TRACKING, source_product_code=code),
        evidence=Evidence(
            matched_on=MatchedOn.MANUAL_SEARCH,
            matched_value=code,
            candidate_set_ids=(f"{Namespace.TRACKING.value}:{code}",),
        ),
        resolution_method=ResolutionMethod.SIMILARITY_RANKED,
    )
    store.append(command)
    return identity_key


def actor_of(env=None) -> str:
    """Ai đang xác nhận. `REPORTS_IDENTITY_ACTOR`, mặc định `owner-web`.

    Bản ghi audit bắt buộc có actor và không được để trống — `ACTOR_DISCLOSURE`
    của `audit.py` tồn tại vì một quyết định không biết ai ra là một quyết
    định không truy được về đâu.
    """
    values = os.environ if env is None else env
    return (values.get("REPORTS_IDENTITY_ACTOR") or "").strip() or "owner-web"


__all__ = [
    "CANDIDATE_LIMIT", "CONFIRM_OK_NOTE", "Candidate", "IdentityGatewayError",
    "NO_TRACKING_NOTE", "actor_of", "build_store", "candidates",
    "confirm_identity", "confirmed_keys",
]
