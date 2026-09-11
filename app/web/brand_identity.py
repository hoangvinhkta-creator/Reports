"""PHB-06 — CỬA DUY NHẤT từ báo cáo thương hiệu tới thẩm quyền Product Identity.

Reports là bên TIÊU THỤ thương hiệu, không phải nơi sinh ra nó (`PHB-06 §3`).
File này là chỗ duy nhất của cả vertical đọc "dòng này thuộc thương hiệu nào",
và nó cố ý nhỏ tới mức đọc hết trong một lần.

## Điều file này KHÔNG làm, và không được lớn thành

Không bảng ánh xạ thương hiệu của riêng Reports. Không so chuỗi con, không
so gần đúng, không rút thương hiệu từ mã máy, không đọc `product_raw` để đoán.
Bốn điều đó là bốn cách khác nhau để dựng một thẩm quyền thương hiệu thứ hai,
và `PHB-06 §3`/`BR-02`/`BR-10` cấm cả bốn. Ranh giới được giữ bằng CẤU TẠO:
`canonical_brand()` chỉ đọc một trường của `CanonicalProductIdentity`, và
`bucket_for()` không nhận `product_raw` làm tham số nên không có gì để đoán.

Tiền lệ là `app/web/identity_gateway.py`: cùng lý do, cùng hình dạng — một
file nhỏ giữ cho "Reports là bên tiêu thụ" đúng theo cấu tạo chứ không theo
lời hứa.

## TRẠNG THÁI ĐO ĐƯỢC TẠI PHB-06 — thương hiệu CHƯA CÓ NGUỒN

Đây là kết quả audit của PHB-06, không phải một suy đoán, và nó phải nằm ngay
đây vì nó giải thích vì sao bảng thương hiệu hôm nay chưa có dòng nào chính
danh:

    CanonicalProductIdentity   = (namespace, source_product_code) — KHÔNG có
                                 trường thương hiệu
    TrackingCatalogRow         = (tracking_code, present_in_board, name, alt)
                                 — KHÔNG có trường thương hiệu
    PublicPurchaseIdentityRow  = (product_code, product_name, aliases,
                                 active_from, active_to) — KHÔNG có
    order_line_result_version  = KHÔNG có cột thương hiệu
    Sổ cũ (LEGACY_HISTORY)     = KHÔNG có sheet/cột thương hiệu

Kết luận này đã từng được ghi nhận và freeze một lần trước đó:
`docs/tasks/TASK-PRA-005-san-pham.md` §19 — `BRAND = NOT_AVAILABLE (không cột
nào ở bất kỳ bảng nào)`, `DEFERRED`, *"KHÔNG suy luận từ tên sản phẩm"*.
PHB-06 đo lại và ra cùng kết quả.

Vì vậy `canonical_brand()` hôm nay trả `None` cho MỌI danh tính, và mọi dòng
đã nhận diện rơi vào `BRAND_ABSENT`. Đó là câu trả lời ĐÚNG cho câu hỏi
"doanh thu theo thương hiệu là bao nhiêu": *hệ thống chưa có nguồn thương
hiệu, và đây là chính xác bao nhiêu tiền đang nằm trong khoảng trống đó* —
khác hẳn một bảng trông như thật dựng từ tên hàng.

Ngày hợp đồng danh tính có trường thương hiệu, hàm này đọc được nó mà không
cần sửa một dòng nào ở đây; `tests/test_phb06_brand_reporting.py` giữ một
test canh đúng thời điểm đó để PHB-06 được mở lại có chủ đích.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Optional

from app.modules.reporting import brand_metrics as bmx
from app.web import line_identity

#: Nhãn thẩm quyền — đi vào bằng chứng và lên màn hình, để không ai phải đoán
#: bảng thương hiệu đang tin vào đâu.
BRAND_AUTHORITY = "PRODUCT_IDENTITY_CANONICAL"

#: Tên trường thương hiệu TRÊN HỢP ĐỒNG Product Identity. Reports không định
#: nghĩa trường này và không được phép định nghĩa nó ở đâu khác: hằng số này
#: chỉ nói "nếu hợp đồng có thương hiệu thì nó tên như vậy".
CANONICAL_BRAND_FIELD = "brand"

BRAND_SOURCE_NOTE = (
    "Thương hiệu chỉ đọc từ danh tính sản phẩm đã được xác nhận (thẩm quyền "
    "Product Identity). Báo cáo KHÔNG suy thương hiệu từ tên hàng, mã máy hay "
    "bất kỳ phép so chuỗi nào — một thương hiệu đoán ra sẽ cộng tiền thật vào "
    "sai chỗ mà không ai nhìn thấy."
)

BRAND_UNAVAILABLE_NOTE = (
    "Danh tính sản phẩm hiện hành KHÔNG mang trường thương hiệu, nên chưa "
    "dòng nào có thương hiệu chính danh. Số dưới đây vẫn là số CHÍNH THỨC của "
    "kỳ — chúng chỉ chưa tách được theo thương hiệu. Thêm thương hiệu là một "
    "quyết định về nguồn danh tính, không phải một thao tác trong Reports."
)


def canonical_brand(identity) -> Optional[str]:
    """Thương hiệu của MỘT canonical identity — ĐỌC, không suy luận.

    `None` khi không có danh tính, khi hợp đồng danh tính không mang trường
    thương hiệu, hoặc khi trường đó rỗng. Ba nguyên nhân cho ra cùng một kết
    quả ở đây vì chúng cho ra cùng một sự thật nghiệp vụ: *không có thương
    hiệu để cộng vào*. Chiều "vì sao" nằm ở `bucket_for`, nơi nó còn phân biệt
    được với "chưa nhận diện sản phẩm".
    """
    if identity is None:
        return None
    value = getattr(identity, CANONICAL_BRAND_FIELD, None)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


#: Chữ ký của một nguồn thương hiệu: `CanonicalProductIdentity → tên | None`.
BrandSource = Callable[[object], Optional[str]]


def bucket_for(
    detail: dict, *, confirmed_keys: frozenset[str],
    identities: dict, brand_source: BrandSource = canonical_brand,
) -> bmx.BrandBucket:
    """Ô thương hiệu của MỘT dòng đã hợp nhất. Thứ tự kiểm là hợp đồng:

    1. Chưa nhận diện được sản phẩm ⟹ `IDENTITY_UNRESOLVED`. Chưa biết dòng
       này là mặt hàng nào thì cũng chưa có danh tính nào để hỏi thương hiệu;
       gán cho nó một thương hiệu là bịa (`BR-09`).
    2. Đã nhận diện, danh tính có thương hiệu ⟹ bucket thương hiệu đó.
    3. Đã nhận diện, không có thương hiệu ⟹ `BRAND_ABSENT`.

    Bước 1 đứng TRƯỚC bước 3 vì hai trạng thái đó cần hai hành động khác nhau
    và chỉ một trong hai sửa được từ trong Reports (`PHB-06 §10`).

    `brand_source` có mặt để test dựng được một kỳ NHIỀU thương hiệu và kiểm
    phép đối soát trên đó — hôm nay dữ liệu thật chỉ cho ra một bucket, và một
    phép đối soát chỉ từng chạy trên một bucket thì chưa chứng minh được gì.
    Đường production wire ĐÚNG `canonical_brand`, và
    `tests/test_phb06_brand_reporting.py` canh điều đó bằng chính mã nguồn
    `server.py` — nên tham số này không mở ra một thẩm quyền thứ hai, nó chỉ
    mở ra một đầu vào cho test.
    """
    state = line_identity.state_of(detail, confirmed_keys=confirmed_keys)
    if state.unresolved:
        return bmx.IDENTITY_UNRESOLVED_BUCKET
    # `R5.4` — mapping CONFIRMED thắng; không có thì mã LẦN CHẠY đã phân
    # giải cho chính dòng này (`line_identity.tracking_identity_of`). Bước 1
    # ở trên vẫn chặn dòng chưa nhận diện trước khi tới đây.
    name = brand_source(
        line_identity.tracking_identity_of(detail, identities=identities))
    if name is None:
        return bmx.BRAND_ABSENT_BUCKET
    return bmx.brand_bucket(name)


def buckets_for(
    details: Iterable[dict], *, confirmed_keys: Optional[frozenset[str]] = None,
    identities: Optional[dict] = None,
    brand_source: BrandSource = canonical_brand,
) -> list[bmx.BrandBucket]:
    """Bucket của TỪNG dòng, cùng thứ tự với `details`.

    Trả về một dãy song song chứ không một dict theo khoá dòng: `group_by_brand`
    ghép nó với `lines` bằng vị trí, đúng cách `business_queries.line_details`
    đã ghép `rows` với `lines`. Một dict sẽ mở ra khả năng thiếu khoá, và
    thiếu khoá ở đây nghĩa là một dòng biến mất khỏi mọi thương hiệu.
    """
    confirmed_keys = confirmed_keys or frozenset()
    identities = identities or {}
    return [bucket_for(detail, confirmed_keys=confirmed_keys,
                       identities=identities, brand_source=brand_source)
            for detail in details]


@dataclass(frozen=True)
class BrandCoverage:
    """Bao nhiêu dòng của kỳ đã có thương hiệu chính danh, và phần còn lại
    đang mắc ở đâu.

    Ba con số thay vì một tỉ lệ: `PHB-06 §10` đòi hai nguyên nhân "chưa xác
    định" phải phân biệt được, và một phần trăm gộp sẽ xoá đúng chiều đó.
    """

    branded_lines: int
    identity_unresolved_lines: int
    brand_absent_lines: int

    @property
    def total_lines(self) -> int:
        return (self.branded_lines + self.identity_unresolved_lines
                + self.brand_absent_lines)

    @property
    def is_complete(self) -> bool:
        """MỌI dòng của kỳ đều có thương hiệu chính danh.

        Kỳ RỖNG ⟹ `False`: không có dòng nào thì cũng không có bằng chứng nào
        cho một lời khẳng định "đã đủ" (cùng kỷ luật fail-closed của
        `DEC-143` §1).
        """
        return self.total_lines > 0 and self.branded_lines == self.total_lines


def coverage(buckets: Iterable[bmx.BrandBucket]) -> BrandCoverage:
    counts = {bmx.KIND_BRAND: 0, bmx.KIND_IDENTITY_UNRESOLVED: 0,
              bmx.KIND_BRAND_ABSENT: 0}
    for bucket in buckets:
        counts[bucket.kind] += 1
    return BrandCoverage(
        branded_lines=counts[bmx.KIND_BRAND],
        identity_unresolved_lines=counts[bmx.KIND_IDENTITY_UNRESOLVED],
        brand_absent_lines=counts[bmx.KIND_BRAND_ABSENT])


__all__ = [
    "BRAND_AUTHORITY", "BRAND_SOURCE_NOTE", "BRAND_UNAVAILABLE_NOTE",
    "BrandCoverage", "BrandSource", "CANONICAL_BRAND_FIELD", "bucket_for",
    "buckets_for", "canonical_brand", "coverage",
]
