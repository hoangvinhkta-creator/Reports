"""PHB-06 — gộp KẾT QUẢ NGHIỆP VỤ CHÍNH THỨC theo THƯƠNG HIỆU.

Module này THUẦN: không SQL, không Flask, không đọc file, và — điều quan
trọng nhất — **không biết thương hiệu của một dòng đến từ đâu**. Nó nhận sẵn
một `BrandBucket` cho từng dòng và chỉ làm đúng một việc: phân hoạch tập dòng
rồi cộng.

## Vì sao thẩm quyền thương hiệu KHÔNG nằm ở đây

Chỉ thị PHB-06 §3 cấm Reports dựng một thẩm quyền thương hiệu thứ hai. Cách
bảo đảm điều đó mạnh nhất không phải một lời hứa trong tài liệu mà là một
ranh giới cấu tạo: file này không có một nhánh nào đọc tên hàng, đọc mã máy,
so chuỗi con hay tra một bảng ánh xạ. Nó nhận nhãn đã quyết định từ bên ngoài
(`app/web/brand_identity.py`, nơi DUY NHẤT đọc hợp đồng Product Identity), và
vì thế một lần "suy thương hiệu từ mô tả sản phẩm" không thể lọt vào đây mà
không phải sửa chữ ký hàm.

Đây đúng hình dạng mà `group_by_employee` đã nghiệm thu: `business_metrics`
gộp theo `line.employee`, còn việc `line.employee` là ai thì `business_queries`
đã quyết định từ trước bằng thẩm quyền của nó.

## Phân hoạch, không phải bộ lọc

`group_by_brand` là một PHÂN HOẠCH của đúng tập dòng được truyền vào: mỗi
dòng thuộc đúng MỘT bucket, không dòng nào rơi ra ngoài và không dòng nào có
mặt ở hai chỗ. Đó là lý do mọi chỉ tiêu cộng được (doanh thu, số lượng đủ
điều kiện, lợi nhuận KPI, DS quy đổi) cộng lại đúng bằng tổng kỳ — và
`reconciliation()` dưới đây biến tính chất đó thành một phép so chạy được,
chứ không để nó là một niềm tin.

Cột `orders` thì KHÔNG cộng lại được, và điều đó phải được NÓI RA: một đơn có
hai mặt hàng của hai thương hiệu được đếm ở cả hai dòng. Đây là cùng sự thật
nghiệp vụ `R-E5` mà bảng nhân viên đã phải nói ra, không phải một lỗi.

## Ba loại bucket, và vì sao "chưa xác định" là HAI chứ không phải MỘT

PHB-06 §10 cấm gộp hai trạng thái khác nhau:

    A. chưa nhận diện được sản phẩm      → chưa có gì để hỏi thương hiệu
    B. đã nhận diện, nhưng không có thương hiệu

Gộp chúng lại sẽ nói với Owner rằng cách sửa là như nhau — trong khi (A) sửa
được bằng luồng phân loại đã có ở bảng kê Nhân viên, còn (B) thì không: nó là
một khoảng trống của chính hợp đồng danh tính, và không thao tác nào trong
Reports lấp được. Đây cùng ranh giới mà `app/web/line_identity.py` đã dựng
cho cặp "Chưa phân loại" / "Thiếu giá", và vì cùng một lý do.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, Sequence

from app.modules.reporting.business_metrics import (
    BusinessLine, BusinessTotals, totals,
)

# --- Ba loại bucket -------------------------------------------------------

KIND_BRAND = "BRAND"
"""Thương hiệu chính danh, đọc từ hợp đồng Product Identity."""

KIND_IDENTITY_UNRESOLVED = "IDENTITY_UNRESOLVED"
"""Chưa nhận diện được sản phẩm ⟹ chưa có gì để hỏi thương hiệu (§10 A)."""

KIND_BRAND_ABSENT = "BRAND_ABSENT"
"""Đã nhận diện sản phẩm, nhưng danh tính đó không mang thương hiệu (§10 B)."""

UNKNOWN_KINDS: frozenset[str] = frozenset(
    {KIND_IDENTITY_UNRESOLVED, KIND_BRAND_ABSENT})

#: Khoá sentinel của hai bucket "chưa xác định". Chúng cố ý KHÔNG phải chuỗi
#: rỗng hay `None`: một khoá rỗng sẽ trộn lẫn với một thương hiệu tên rỗng, và
#: `None` sẽ trộn lẫn với "chưa tra". Cùng kỷ luật `INV-25` của `PendingProduct`.
KEY_IDENTITY_UNRESOLVED = "\x1fBRAND_IDENTITY_UNRESOLVED"
KEY_BRAND_ABSENT = "\x1fBRAND_ABSENT"

LABEL_IDENTITY_UNRESOLVED = "Chưa xác định thương hiệu — chưa nhận diện sản phẩm"
LABEL_BRAND_ABSENT = "Chưa xác định thương hiệu — danh tính không có thương hiệu"

#: Thứ tự CỐ ĐỊNH của hai bucket "chưa xác định" ở cuối bảng. Viết ra thay vì
#: để phụ thuộc thứ tự chèn của dict: một bảng đổi thứ tự dòng giữa hai lần
#: tải trang mà số không đổi làm người đọc mất niềm tin vào cả trang.
UNKNOWN_ORDER: tuple[str, ...] = (KEY_IDENTITY_UNRESOLVED, KEY_BRAND_ABSENT)


@dataclass(frozen=True)
class BrandBucket:
    """Ô mà MỘT dòng hàng rơi vào trên bảng thương hiệu.

    `key` là khoá phân hoạch (tên thương hiệu, hoặc một trong hai sentinel);
    `label` là chữ hiện trên bảng; `kind` là loại bucket. Ba trường đi cùng
    nhau trong một value object chứ không tách rời, để không có đường nào
    render nhãn "chưa xác định" mà rơi mất chiều "chưa xác định VÌ SAO".
    """

    key: str
    label: str
    kind: str

    def __post_init__(self) -> None:
        if not self.key:
            raise ValueError("BrandBucket.key REQUIRED, không được rỗng")
        if self.kind not in (KIND_BRAND, *UNKNOWN_KINDS):
            raise ValueError(f"kind ngoài tập đóng: {self.kind!r}")

    @property
    def known(self) -> bool:
        return self.kind == KIND_BRAND


IDENTITY_UNRESOLVED_BUCKET = BrandBucket(
    key=KEY_IDENTITY_UNRESOLVED, label=LABEL_IDENTITY_UNRESOLVED,
    kind=KIND_IDENTITY_UNRESOLVED)

BRAND_ABSENT_BUCKET = BrandBucket(
    key=KEY_BRAND_ABSENT, label=LABEL_BRAND_ABSENT, kind=KIND_BRAND_ABSENT)


def brand_bucket(name: str) -> BrandBucket:
    """Bucket của một thương hiệu CHÍNH DANH đã đọc được từ hợp đồng danh tính.

    Tên rỗng/toàn khoảng trắng KHÔNG phải một thương hiệu — nó là sự vắng mặt,
    và nó phải rơi về `BRAND_ABSENT_BUCKET` ở tầng gọi chứ không thành một ô
    tên rỗng trên bảng. Hàm này từ chối thay vì âm thầm nhận.
    """
    text = (name or "").strip()
    if not text:
        raise ValueError(
            "thương hiệu rỗng không phải một thương hiệu; dùng "
            "BRAND_ABSENT_BUCKET cho sự vắng mặt")
    return BrandBucket(key=text, label=text, kind=KIND_BRAND)


# --- Phân hoạch -----------------------------------------------------------

def group_by_brand(
    lines: Sequence[BusinessLine], buckets: Sequence[BrandBucket],
) -> list[tuple[BrandBucket, BusinessTotals]]:
    """Phân hoạch `lines` theo `buckets` (hai dãy ĐI SONG SONG), sắp doanh thu
    giảm dần, hai bucket "chưa xác định" luôn ở CUỐI.

    Hai dãy song song thay vì một trường trên `BusinessLine`: `BusinessLine`
    là ngữ nghĩa nghiệp vụ thuần và cố ý không mang danh tính sản phẩm (cùng
    lý do nó không mang `product_raw` — xem `business_queries.line_details`).
    Nhồi `brand` vào đó sẽ bắt mọi test nghiệp vụ phải dựng một trường chúng
    không quan tâm, và sẽ mở một đường ghi thương hiệu ngay giữa tầng gộp.

    Độ dài lệch nhau là LỖI CỨNG, không phải một lần `zip` cắt ngắn im lặng:
    cắt ngắn ở đây nghĩa là một số dòng biến mất khỏi mọi bucket, và tổng vẫn
    trông hợp lệ — đúng lớp lỗi mà `reconciliation()` được dựng để bắt, nên nó
    không được phép xảy ra ở tầng dưới nó.
    """
    if len(lines) != len(buckets):
        raise ValueError(
            f"lines ({len(lines)}) và buckets ({len(buckets)}) phải cùng độ "
            "dài — mỗi dòng đúng một bucket, không dòng nào rơi ra ngoài")
    grouped: dict[str, tuple[BrandBucket, list[BusinessLine]]] = {}
    for line, bucket in zip(lines, buckets):
        _, members = grouped.setdefault(bucket.key, (bucket, []))
        members.append(line)
    rows = [(bucket, totals(members)) for bucket, members in grouped.values()]
    rows.sort(key=lambda item: (
        # Hai bucket "chưa xác định" xuống cuối, theo thứ tự đã viết ra.
        1 if not item[0].known else 0,
        UNKNOWN_ORDER.index(item[0].key) if not item[0].known else 0,
        -(item[1].sales_revenue or Decimal(0)),
        item[0].key,
    ))
    return rows


# --- Đối soát về tổng công ty --------------------------------------------

def _sum_optional(values) -> Optional[Decimal]:
    """Cùng kỷ luật `NULL ≠ 0` của `business_metrics._sum`.

    Viết lại ở đây thay vì import một hàm private: `_sum` là chi tiết cài đặt
    của module kia, và cột được cộng ở đây là kết quả ĐÃ GỘP của từng bucket,
    không phải giá trị thô của từng dòng.
    """
    present = [value for value in values if value is not None]
    return sum(present, Decimal(0)) if present else None


@dataclass(frozen=True)
class BrandReconciliation:
    """Kết quả đối soát bảng thương hiệu về tổng công ty (PHB-06 §9).

    Bốn cờ, mỗi cờ một chỉ tiêu, thay vì một cờ gộp: khi một cột lệch, Owner —
    và người đọc test — cần biết ĐÚNG cột nào, chứ không phải "có gì đó sai".
    `orders` cố ý VẮNG MẶT: một đơn có hàng của hai thương hiệu được đếm ở cả
    hai dòng, nên nó không phải một chỉ tiêu cộng được và không có gì để đối
    soát (cùng `R-E5` của bảng nhân viên).
    """

    sales_revenue: bool
    qualifying_quantity: bool
    kpi_profit: bool
    converted_sales: bool
    lines: bool

    @property
    def is_exact(self) -> bool:
        return all((self.sales_revenue, self.qualifying_quantity,
                    self.kpi_profit, self.converted_sales, self.lines))


def reconciliation(
    grouped: Sequence[tuple[BrandBucket, BusinessTotals]],
    company: BusinessTotals,
) -> BrandReconciliation:
    """So từng chỉ tiêu cộng được của bảng thương hiệu với tổng kỳ.

    Phép so là BẰNG ĐÚNG (`==` trên `Decimal`), không phải "gần bằng": các con
    số này là số kế toán chính xác (`ExactNumeric`), và một ngưỡng dung sai ở
    đây sẽ giấu đúng loại lỗi mà hàm này tồn tại để bắt — một dòng bị bỏ rơi
    hoặc bị đếm hai lần.

    `None == None` là ĐÚNG và có nghĩa: cả hai bên đều nói "chưa có giá trị
    nào", không phải "bằng nhau ở số 0".
    """
    per_bucket = [item[1] for item in grouped]
    return BrandReconciliation(
        sales_revenue=(
            _sum_optional(t.sales_revenue for t in per_bucket)
            == company.sales_revenue),
        qualifying_quantity=(
            sum((t.qualifying_quantity for t in per_bucket), Decimal(0))
            == company.qualifying_quantity),
        kpi_profit=(
            _sum_optional(t.kpi_profit for t in per_bucket)
            == company.kpi_profit),
        converted_sales=(
            _sum_optional(t.converted_sales for t in per_bucket)
            == company.converted_sales),
        lines=sum(t.lines for t in per_bucket) == company.lines,
    )


__all__ = [
    "BRAND_ABSENT_BUCKET", "BrandBucket", "BrandReconciliation",
    "IDENTITY_UNRESOLVED_BUCKET", "KEY_BRAND_ABSENT",
    "KEY_IDENTITY_UNRESOLVED", "KIND_BRAND", "KIND_BRAND_ABSENT",
    "KIND_IDENTITY_UNRESOLVED", "LABEL_BRAND_ABSENT",
    "LABEL_IDENTITY_UNRESOLVED", "UNKNOWN_KINDS", "UNKNOWN_ORDER",
    "brand_bucket", "group_by_brand", "reconciliation",
]
