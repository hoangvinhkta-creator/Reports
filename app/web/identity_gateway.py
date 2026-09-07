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
from app.modules.product.identity.commands import (
    ConfirmMapping, MarkOutOfCatalog,
)
from app.modules.product.identity.evidence import (
    Evidence, MatchedOn, ResolutionMethod,
)
from app.modules.product.identity.identity import CanonicalProductIdentity, Namespace
from app.modules.product.identity.keys import (
    normalized_matching_aid, raw_identity_key,
)
from app.modules.product.identity.mapping import (
    MappingSource, MappingStatus, SOURCE_SYSTEM_REPORTS_SALES,
)
from app.modules.product.identity.resolver import (
    CONFLICT_OPPOSING_CODE_PREFIX, tracking_authority_code,
)
from app.modules.product.identity.store import JsonlProductIdentityStore
from app.web import identity_journal

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

OUT_OF_CATALOG_OK_NOTE = (
    "Đã ghi nhận: mặt hàng này KHÔNG có trên bảng giá Tracking. Đây là một "
    "phân loại HOÀN TẤT — dòng không còn nằm trong danh sách chưa phân loại, "
    "vẫn giữ nguyên doanh thu và số lượng, và chờ một giá nhập tay. Không có "
    "giá 0 nào được dựng ra."
)

RELINK_OK_NOTE = (
    "Đã nối lại mặt hàng này với một mã Tracking. Quyết định ngoài bảng giá cũ "
    "được thay thế theo đúng cơ chế supersede của log — nó vẫn nằm lại trong "
    "lịch sử, không bị xoá."
)

CONFLICT_OK_NOTE = (
    "Đã ghi nhận lựa chọn cho mâu thuẫn mã Tracking. Từ nay hệ thống dùng mã "
    "bạn chọn và KHÔNG hỏi lại mâu thuẫn này nữa."
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


class DurableStoreUnavailableError(RuntimeError):
    """Môi trường đòi nơi lưu bền nhưng không có — `F-B`, fail closed."""


def build_store(
    log_path: Optional[Path] = None, index_path: Optional[Path] = None,
    *, env=None,
) -> JsonlProductIdentityStore:
    """Store quyết định Product Identity, lưu ở nơi BỀN nếu có (`F-B`).

    Thứ tự chọn, và lý do của từng nhánh:

    1. **Journal dùng chung (R2) nếu đã cấu hình.** Đây là nhánh của bản Web:
       nhiều worker cùng đọc một log, và log sống qua redeploy. Xem
       `app/web/identity_journal.py` § Vì sao là R2.
    2. **`REPORTS_REQUIRE_R2` bật mà R2 chưa cấu hình ⟹ LỖI.** Rơi về file
       cục bộ ở đây là rơi về đúng `F-B`: mọi phân loại của Owner biến mất
       lặng lẽ ở lần deploy kế tiếp. Thà không có bề mặt phân loại còn hơn
       có một bề mặt hứa hão.
    3. **File cục bộ.** Máy Owner (`Open Reports.command`), dev, test — đĩa
       thật, một tiến trình, bền qua khởi động lại. Nhánh này KHÔNG đổi hành
       vi so với trước bản sửa.
    """
    journal = identity_journal.build(env)
    if journal is not None:
        return JsonlProductIdentityStore(journal=journal)
    if identity_journal.requires_durable_store(env):
        raise DurableStoreUnavailableError(
            "REPORTS_REQUIRE_R2 yêu cầu nơi lưu bền cho quyết định Product "
            "Identity, nhưng R2 chưa cấu hình đủ; KHÔNG rơi về log trên đĩa "
            "ephemeral của container — nó biến mất ở lần deploy kế tiếp.")
    return JsonlProductIdentityStore(
        log_path=log_path or DEFAULT_LOG_PATH,
        index_path=index_path or DEFAULT_INDEX_PATH)


def store_view(store):
    """Ảnh chụp ĐÃ ĐÓNG BĂNG của log quyết định, hoặc `None`.

    Đây là thứ mà đường CHẠY BÁO CÁO cần, và nó khác `confirmed_keys` ở một
    điểm quyết định: nó mang CẢ log, nên `ProductIdentityResolver` đọc được
    mọi trạng thái (`CONFIRMED`, `OUT_OF_CATALOG`, `PENDING`) chứ không chỉ
    một tập khoá đã lọc sẵn.

    `refresh()` chứ không `current_revision()`, vì cùng lý do đã nghiệm thu ở
    `confirmed_keys`: với `gunicorn --workers 2`, worker đang chạy báo cáo
    KHÔNG nhất thiết là worker đã ghi xác nhận.

    Đọc MỘT lần cho cả lần chạy là có chủ ý. Kế hoạch hỏi giá `daily-min` và
    phép phân giải giá phải nhìn CÙNG một trạng thái; đọc lại giữa chừng thì
    một xác nhận xảy ra đúng lúc đó sẽ làm tập mã được hỏi khác tập mã được
    phân giải, và dòng đó thiếu giá mà không có lý do nào nói được vì sao.

    Store không đọc được ⟹ `None`, và mọi tầng dưới đã có nhánh "chưa nối
    nguồn identity" mang tên riêng (`IDENTITY_SOURCES_UNAVAILABLE`). Không có
    nhánh nào đoán mã.
    """
    if store is None:
        return None
    try:
        return store.read_at_revision(store.refresh())
    except Exception:  # noqa: BLE001 — xem docstring
        return None


def confirmed_keys(store) -> frozenset[str]:
    """Các `raw_identity_key` đã có mapping `CONFIRMED` đang hiệu lực.

    Đây là thứ `line_identity.state_of` cần để biết một dòng đã được xác nhận
    sau lần chạy sổ gần nhất. Đọc qua `read_at_revision(current)` — tức chiếu
    lại log, không đọc index — vì `INV-63` nói LOG THẮNG, và một index cũ ở
    đây sẽ làm màn hình nói rằng một mặt hàng vừa được phân loại thì vẫn chưa.

    `refresh()` chứ không `current_revision()` — đây là sửa `F-A`. Với
    `gunicorn --workers 2`, worker đang render trang KHÔNG nhất thiết là
    worker đã ghi xác nhận; `current_revision()` chỉ đếm event trong bộ nhớ
    của CHÍNH tiến trình này, nên nó sẽ trả lời câu hỏi "đã phân loại chưa"
    bằng ảnh chụp riêng của một worker thay vì bằng log dùng chung. Chi phí
    là một lần chạm nơi lưu cho mỗi lần tải trang — đúng đánh đổi mà
    `_confirmed_identity_keys` đã tuyên bố là chấp nhận, chỉ nay nó mới thật
    sự được thực hiện qua biên tiến trình.

    Store không đọc được (chưa có file, đĩa lỗi, R2 không tới được) ⟹ tập
    RỖNG, không phải một lỗi trang: hệ quả là màn hình hiện đúng trạng thái
    mà pipeline đã lưu — thận trọng theo hướng "chưa phân loại", không theo
    hướng ngược lại.
    """
    if store is None:
        return frozenset()
    try:
        view = store.read_at_revision(store.refresh())
    except Exception:  # noqa: BLE001 — xem docstring
        return frozenset()
    return frozenset(
        mapping.raw_identity_key
        for mapping in view.alias_index().values()
        if mapping.status is MappingStatus.CONFIRMED
        and mapping.source_system == SOURCE_SYSTEM_REPORTS_SALES
    )


def confirmed_identities(store) -> dict:
    """`{raw_identity_key: CanonicalProductIdentity}` của các mapping CONFIRMED.

    Cùng đường đọc, cùng bộ lọc và cùng cách xử lý lỗi như `confirmed_keys` —
    khác đúng một điều: nó giữ lại DANH TÍNH chứ không chỉ khoá. PHB-06 cần
    danh tính vì thương hiệu (nếu có) là một thuộc tính CỦA DANH TÍNH, không
    phải của khoá thô; `confirmed_keys` chỉ trả lời "đã nhận diện chưa".

    Viết thành hàm riêng thay vì đổi kiểu trả về của `confirmed_keys`: hàm kia
    là đầu vào của `line_identity.state_of` ở mọi màn hình nghiệp vụ, và một
    lần đổi kiểu ở đó có bán kính ảnh hưởng lớn hơn hẳn thứ PHB-06 cần.

    Store không đọc được ⟹ dict RỖNG, không phải một lỗi trang: hệ quả là mọi
    dòng hiện "chưa xác định thương hiệu" — thận trọng đúng hướng, cùng lựa
    chọn mà `confirmed_keys` đã nghiệm thu.
    """
    if store is None:
        return {}
    try:
        view = store.read_at_revision(store.refresh())
    except Exception:  # noqa: BLE001 — xem docstring
        return {}
    resolved = {}
    for mapping in view.alias_index().values():
        if mapping.status is not MappingStatus.CONFIRMED:
            continue
        if mapping.source_system != SOURCE_SYSTEM_REPORTS_SALES:
            continue
        if mapping.namespace is None or mapping.source_product_code is None:
            continue
        resolved[mapping.raw_identity_key] = CanonicalProductIdentity(
            namespace=mapping.namespace,
            source_product_code=mapping.source_product_code)
    return resolved


def out_of_catalog_keys(store) -> frozenset[str]:
    """Các `raw_identity_key` mà người dùng đã xác nhận NGOÀI BẢNG GIÁ (R2 §4.3).

    Tách hẳn khỏi `confirmed_keys`, và đó là toàn bộ điểm: hai tập này dẫn tới
    hai câu khác nhau trên màn hình ("đã khớp mã X" và "ngoài bảng giá"), và
    một dòng thuộc tập nào cũng đều là ĐÃ PHÂN LOẠI XONG — không tập nào được
    đẩy dòng về hàng đợi "chưa phân loại".

    Cùng đường đọc và cùng cách xử lý lỗi như `confirmed_keys`: store không đọc
    được ⟹ tập RỖNG, tức màn hình thận trọng theo hướng "chưa phân loại" chứ
    không theo hướng ngược lại.
    """
    if store is None:
        return frozenset()
    try:
        view = store.read_at_revision(store.refresh())
    except Exception:  # noqa: BLE001 — xem `confirmed_keys`
        return frozenset()
    return frozenset(
        mapping.raw_identity_key
        for mapping in view.alias_index().values()
        if mapping.status is MappingStatus.OUT_OF_CATALOG
        and mapping.source_system == SOURCE_SYSTEM_REPORTS_SALES
    )


def mark_out_of_catalog(
    store, *, product_raw: str, actor_id: str,
    affected_orders: tuple[str, ...] = (), affected_lines: int = 0,
    client_request_id: Optional[str] = None, reason: Optional[str] = None,
) -> str:
    """Ghi quyết định "hàng này KHÔNG có trên bảng giá" (R2 §4.3).

    KHÔNG cần danh mục Tracking, và đó là chủ ý: đây chính là câu trả lời cho
    trường hợp danh mục KHÔNG chứa mặt hàng ấy. Bắt màn hình phải pull được
    danh mục trước khi cho phép nói "không có trong danh mục" sẽ khoá đúng
    thao tác mà `§4.3` tồn tại để mở.

    Đi qua cùng `store.append()` với mọi quyết định khác, nên `INV-59`
    (version), `INV-68`/`INV-69` (idempotency) và audit event đều giữ nguyên.
    """
    if store is None:
        raise IdentityGatewayError(
            "Chưa cấu hình nơi lưu quyết định Product Identity.")
    key = (product_raw or "").strip()
    if not key:
        raise IdentityGatewayError(
            "Dòng này không có tên hàng trên sổ, nên chưa có gì để phân loại.")
    identity_key = raw_identity_key(key)
    revision = store.refresh()
    current = store.read_at_revision(revision).active_mapping(
        SOURCE_SYSTEM_REPORTS_SALES, identity_key)
    store.append(MarkOutOfCatalog(
        actor_id=actor_id,
        client_request_id=client_request_id or str(uuid.uuid4()),
        expected_version=current.version if current is not None else 0,
        reason=reason,
        affected_scope=AffectedScope(
            distinct_identity_count=1,
            affected_order_ids=tuple(affected_orders),
            affected_line_count=affected_lines,
            computed_at_revision=revision,
        ),
        raw_identity_key=identity_key,
        raw_product_identity=key,
        source_system=SOURCE_SYSTEM_REPORTS_SALES,
    ))
    return identity_key


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
    resolves_conflict: bool = False, reason: Optional[str] = None,
    inv_map_snapshot=None,
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

    `resolves_conflict` (R2 §4.2) ghi `mapping_source =
    HUMAN_CONFLICT_RESOLUTION` thay vì `HUMAN_CONFIRMATION`. Nó KHÔNG phải một
    nhãn trang trí: mâu thuẫn giữa quyết định của Reports và authority của
    Tracking được SUY RA từ dữ liệu ở mỗi lần chạy, nên nếu lựa chọn của người
    dùng không mang dấu vết rằng họ đã nhìn thấy đúng mâu thuẫn ấy, lần chạy
    sau lại phát hiện lại và lại hỏi lại — mãi mãi. Vẫn là `ConfirmMapping`,
    tức vẫn đúng một `confirmation_action` đã có, không phải một lệnh mới.

    Khi `resolves_conflict=True`, hàm này CŨNG ghi lại mã Tracking đang chỏi
    NGAY TẠI THỜI ĐIỂM này (repair `FIND-R2-IR-02`) — dùng `snapshot`/
    `inv_map_snapshot` vừa được tầng route đọc cho chính lần bấm này, qua
    ĐÚNG một phép tra `tracking_authority_code()` mà resolver production
    dùng. Không có bước này, `HUMAN_CONFLICT_RESOLUTION` sẽ miễn trừ MỌI mâu
    thuẫn về sau bất kể mã đối lập là gì — kể cả khi Tracking đổi tiếp sang
    một mã thứ ba mà người dùng chưa từng thấy. Không xác định được mã đối
    lập (ví dụ chưa nối `inv.map`) thì không ghi gì thêm — an toàn theo hướng
    hỏi lại, không theo hướng miễn trừ nhầm.
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
    # Hai con số KHÁC NHAU, và trộn chúng là cách sinh ra đúng câu lỗi mà
    # `§5` cấm ("expected_version=0 nhưng version hiện tại=1"):
    #
    #   revision      số thứ tự của event CUỐI trong log — thuộc về cả store.
    #   version       số phiên bản của CHÍNH mapping mang khoá này — thuộc về
    #                 một aggregate, và `_append_mapping_command` so
    #                 `expected_version` với đúng con số này (`INV-59`).
    #
    # Một mapping chưa tồn tại có version 0 dù log đã dài bao nhiêu. Truyền
    # revision vào chỗ của version vì thế chỉ đúng cho lần xác nhận ĐẦU TIÊN
    # của cả hệ thống, rồi từ lần thứ hai trở đi từ chối mọi mặt hàng mới
    # bằng một xung đột không có thật.
    #
    # `refresh()` đứng trước cả hai — sửa `F-A` ở đường GHI: cả revision lẫn
    # version đều phải đọc từ log DÙNG CHUNG, không từ ảnh chụp trong bộ nhớ
    # của một worker.
    revision = store.refresh()
    current = store.read_at_revision(revision).active_mapping(
        SOURCE_SYSTEM_REPORTS_SALES, identity_key)

    candidate_ids = [f"{Namespace.TRACKING.value}:{code}"]
    if resolves_conflict:
        # repair `FIND-R2-IR-02` — ghi lại mã Tracking đang chỏi NGAY LÚC
        # người dùng chọn, để lần tra cứu sau phân biệt được "vẫn cùng một
        # mâu thuẫn đã giải" (mã đối lập trùng khớp) với "một mâu thuẫn MỚI"
        # (Tracking đổi tiếp sang một mã thứ ba). Xem
        # `resolver.CONFLICT_OPPOSING_CODE_PREFIX`.
        opposing_code = None
        try:
            opposing_code = tracking_authority_code(
                snapshot, inv_map_snapshot,
                raw_product_identity=key,
                normalized_matching_aid=normalized_matching_aid(key),
            )
        except Exception:  # noqa: BLE001 — không xác định được ⟹ không ghi gì
            opposing_code = None
        if opposing_code is not None:
            candidate_ids.append(
                f"{CONFLICT_OPPOSING_CODE_PREFIX}{opposing_code}")

    command = ConfirmMapping(
        actor_id=actor_id,
        client_request_id=client_request_id or str(uuid.uuid4()),
        expected_version=current.version if current is not None else 0,
        reason=reason,
        mapping_source=(
            MappingSource.HUMAN_CONFLICT_RESOLUTION if resolves_conflict
            else MappingSource.HUMAN_CONFIRMATION),
        tracking_capture_id=snapshot.capture_id,
        affected_scope=AffectedScope(
            distinct_identity_count=1,
            affected_order_ids=tuple(affected_orders),
            affected_line_count=affected_lines,
            computed_at_revision=revision,
        ),
        raw_identity_key=identity_key,
        raw_product_identity=key,
        source_system=SOURCE_SYSTEM_REPORTS_SALES,
        target=CanonicalProductIdentity(
            namespace=Namespace.TRACKING, source_product_code=code),
        evidence=Evidence(
            matched_on=MatchedOn.MANUAL_SEARCH,
            matched_value=code,
            candidate_set_ids=tuple(candidate_ids),
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
    "CANDIDATE_LIMIT", "CONFIRM_OK_NOTE", "Candidate",
    "DurableStoreUnavailableError", "IdentityGatewayError", "NO_TRACKING_NOTE",
    "actor_of", "build_store", "candidates", "confirm_identity",
    "MappingSource", "MappingStatus", "SOURCE_SYSTEM_REPORTS_SALES",
    "confirmed_identities", "confirmed_keys", "out_of_catalog_keys",
    "mark_out_of_catalog", "store_view",
]
