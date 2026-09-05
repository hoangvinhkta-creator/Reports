"""`DEC-185` — TRẠNG THÁI NHẬN DIỆN SẢN PHẨM của một dòng, đọc tại chỗ.

Module này THUẦN: không SQL, không Flask, không mạng. Nó trả lời đúng một câu
hỏi, và câu hỏi đó cố ý HẸP:

    dòng này đang ở trạng thái nhận diện nào — và vì thế ô mã hàng của nó
    phải hiện chữ gì?

## Hai trạng thái KHÁC NHAU, và việc gộp chúng là một lời nói dối

Owner nói thẳng ranh giới này (`§10`):

    A. chưa nhận diện được mặt hàng        → "Chưa phân loại"
    B. đã nhận diện, nhưng chưa có giá nhập → "Thiếu giá"

Cám dỗ ở đây rất cụ thể: cả hai trạng thái đều làm ô Giá nhập trống, nên một
câu `if purchase_price is None: "Chưa phân loại"` chạy đúng trên phần lớn dữ
liệu và SAI về bản chất. Nó sai theo hướng tốn tiền: một dòng đã nhận diện
xong mà bị dán nhãn "Chưa phân loại" sẽ đẩy Owner đi phân loại lại một thứ đã
phân loại rồi, và việc đó không bao giờ làm giá nhập xuất hiện.

Vì thế trạng thái ở đây đọc từ MÃ LÝ DO THẬT mà pipeline đã ghi xuống cùng
dòng (`pending_reasons`), chứ không suy từ chỗ trống của giá nhập.

## Vì sao đọc `pending_reasons` là đọc trạng thái THẬT

`PriceResolutionReason` là một enum ĐÓNG, và bốn mã dưới đây là bốn cách khác
nhau để nói cùng một chuyện: *máy chưa biết dòng này là mặt hàng nào*. Chúng
được pipeline ghi vào `pending_reasons_json` tại lần chạy đó và đi cùng dòng
qua database, nên chúng là bằng chứng, không phải suy đoán.

`profit_gate` cố ý GỘP cả bốn mã này vào nhóm "triệu chứng của thiếu giá" khi
dựng cảnh báo — đúng cho mục đích của nó (đừng dán cảnh báo lên 100 % số
dòng). Nhưng chính vì đã gộp ở đó, chiều "chưa nhận diện" không còn nhìn thấy
được ở đâu cả, và `§PI-03` đòi nó phải nhìn thấy được. Đó là lý do file này
tồn tại thay vì thêm một nhánh vào `profit_gate`.

## Xác nhận của Owner có hiệu lực NGAY, không chờ chạy lại sổ

Sau khi Owner xác nhận một mặt hàng qua thẩm quyền Product Identity, mã lý do
đã LƯU của dòng vẫn nói "chưa nhận diện" — nó là bằng chứng của lần chạy đó
và không được sửa lại (cùng kỷ luật `rate_routing`: không viết đè
`conversion_rate_final`). Trạng thái HIỆU LỰC vì thế được tính lúc ĐỌC: một
`raw_identity_key` đã có mapping `CONFIRMED` thì dòng mang khoá đó đã nhận
diện xong, kể cả khi sổ chưa chạy lại.

Đây đúng là hình dạng mà `PHB-01` đã nghiệm thu trên production:

    IDENTITY_BEFORE       = IDENTITY_UNRESOLVED
    IDENTITY_AFTER        = IDENTITY_UNRESOLVED đã biến mất
    ECONOMIC_STATE_AFTER  = PENDING  (giá vẫn chưa có)

Nhận diện xong KHÔNG kéo theo giá — `ECONOMIC_ISOLATION` giữ nguyên. Nên kết
quả đúng của một lần phân loại thành công là dòng chuyển từ "Chưa phân loại"
sang "Thiếu giá", chứ không phải sang một con số. Bịa ra một con số ở đây là
đúng thứ mà cả `INV-15` lẫn `INV-51` cấm.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional

from app.modules.product.identity.keys import raw_identity_key

#: Bốn mã của `PriceResolutionReason`/`TrackingHistoryReason` nói rằng máy
#: chưa biết dòng này là mặt hàng nào. Cố ý viết bằng CHUỖI: chúng đến từ
#: `pending_reasons_json` đã lưu trong database, nên tập này phải khớp với
#: những gì ĐANG nằm trên đĩa, không phải với enum của phiên bản hôm nay.
IDENTITY_UNRESOLVED_REASONS = frozenset({
    "IDENTITY_UNRESOLVED",
    "IDENTITY_REQUIRES_CONFIRMATION",
    "IDENTITY_SOURCES_UNAVAILABLE",
    "RAW_PRODUCT_IDENTITY_EMPTY",
})

STATE_UNRESOLVED = "IDENTITY_UNRESOLVED"
STATE_MISSING_PRICE = "MISSING_PURCHASE_PRICE"
STATE_OK = "OK"

LABEL_UNRESOLVED = "Chưa phân loại"
LABEL_MISSING_PRICE = "Thiếu giá"

LABEL_TITLES = {
    STATE_UNRESOLVED: (
        "Chưa nhận diện được mặt hàng này — bấm để chọn sản phẩm tương ứng "
        "bên Tracking"),
    STATE_MISSING_PRICE: (
        "Đã nhận diện được mặt hàng, nhưng chưa có giá nhập cho ngày bán này"),
}

#: `RAW_PRODUCT_IDENTITY_EMPTY` là trường hợp DUY NHẤT không phân loại được
#: bằng màn hình này: không có tên hàng thì không có khoá định danh để xác
#: nhận (`EmptyRawIdentityError`). Nó vẫn hiện "Chưa phân loại" — đó là sự
#: thật — nhưng nút bấm sẽ không mở ra được gì, nên trang nói lý do thay vì
#: đưa ra một nút hỏng.
UNCLASSIFIABLE_NOTE = (
    "Dòng này không có tên hàng trên sổ, nên chưa có gì để phân loại. Cần sửa "
    "trên sổ gốc rồi nạp lại."
)


@dataclass(frozen=True)
class IdentityState:
    """Trạng thái nhận diện HIỆU LỰC của một dòng."""

    state: str
    #: Khoá định danh của mặt hàng trên dòng, `None` khi không dựng được.
    identity_key: Optional[str] = None

    @property
    def unresolved(self) -> bool:
        return self.state == STATE_UNRESOLVED

    @property
    def missing_price(self) -> bool:
        return self.state == STATE_MISSING_PRICE

    @property
    def label(self) -> Optional[str]:
        if self.state == STATE_UNRESOLVED:
            return LABEL_UNRESOLVED
        if self.state == STATE_MISSING_PRICE:
            return LABEL_MISSING_PRICE
        return None

    @property
    def title(self) -> Optional[str]:
        return LABEL_TITLES.get(self.state)

    @property
    def classifiable(self) -> bool:
        """Có mở được luồng phân loại cho dòng này không (`§PI-04`)."""
        return self.unresolved and self.identity_key is not None


def identity_key_of(product_raw: Optional[str]) -> Optional[str]:
    """Khoá định danh của một câu tên hàng, `None` khi không dựng được.

    Uỷ quyền cho `identity.keys` chứ không chuẩn hoá lại: một bản sao thứ hai
    của phép chuẩn hoá là một nguồn drift, và `INV-05` tồn tại vì chuyện đó
    đã xảy ra một lần trên tài sản thật.
    """
    if not (product_raw or "").strip():
        return None
    try:
        return raw_identity_key(product_raw)
    except Exception:  # noqa: BLE001 — tên hàng rỗng sau chuẩn hoá
        return None


def state_of(
    detail: dict, *, confirmed_keys: Optional[frozenset[str]] = None,
) -> IdentityState:
    """Trạng thái nhận diện hiệu lực của một dòng đã hợp nhất.

    `confirmed_keys` là tập `raw_identity_key` đã có mapping `CONFIRMED` trong
    thẩm quyền Product Identity. Một khoá nằm trong tập đó ⟹ dòng ĐÃ nhận
    diện, dù mã lý do đã lưu còn nói ngược lại (`§ Xác nhận có hiệu lực ngay`).

    Thứ tự kiểm là một phần của hợp đồng:

    1. chưa nhận diện (và chưa ai xác nhận) ⟹ `Chưa phân loại`;
    2. đã nhận diện nhưng chưa chốt được giá nhập ⟹ `Thiếu giá`;
    3. còn lại ⟹ không nhãn nào — ô mã hàng hiện đúng tên hàng, không thêm gì.

    Bước 1 đứng TRƯỚC bước 2 vì một dòng chưa nhận diện thì đương nhiên cũng
    chưa có giá; dán "Thiếu giá" lên nó sẽ chỉ Owner đi nhập tay một con số
    mà lẽ ra Tracking đã trả lời được sau khi phân loại.
    """
    confirmed_keys = confirmed_keys or frozenset()
    line = detail["line"]
    key = identity_key_of(detail.get("product_raw"))
    reasons = set(line.pending_reasons or ())
    unresolved = bool(reasons & IDENTITY_UNRESOLVED_REASONS)
    if unresolved and (key is None or key not in confirmed_keys):
        return IdentityState(STATE_UNRESOLVED, identity_key=key)
    if line.purchase_price is None:
        return IdentityState(STATE_MISSING_PRICE, identity_key=key)
    return IdentityState(STATE_OK, identity_key=key)


# --- Cảnh báo GỌN của một sheet (`§13`, `§PI-10`) -------------------------

#: Số BH tối đa được gọi TÊN trong câu cảnh báo. Quá ngưỡng này thì câu nói
#: bao nhiêu BH thay vì liệt kê — Owner yêu cầu MỘT dòng gọn, không phải một
#: danh sách (`§13`).
_NAME_LIMIT = 3


def unresolved_orders(
    details: Iterable[dict], *, confirmed_keys: Optional[frozenset[str]] = None,
) -> list[str]:
    """Các BH của sheet còn chứa mã chưa phân loại, theo thứ tự xuất hiện.

    Trả về BH chứ không phải dòng: Owner đọc bảng kê theo BH, và một cảnh báo
    đếm "17 dòng" trong khi bảng chỉ có 7 khối BH sẽ không dẫn được mắt tới
    chỗ nào.
    """
    seen: list[str] = []
    for detail in details:
        if not state_of(detail, confirmed_keys=confirmed_keys).unresolved:
            continue
        order_key = detail["order_key"]
        if order_key not in seen:
            seen.append(order_key)
    return seen


def sheet_warning(
    details: Iterable[dict], *, confirmed_keys: Optional[frozenset[str]] = None,
) -> Optional[dict]:
    """MỘT dòng cảnh báo cho cả sheet, hoặc `None` khi không có gì để báo.

    `None` chứ không phải một câu "không có dòng nào chưa phân loại": một
    trạng thái BÌNH THƯỜNG không đáng chiếm một dòng trên đầu mọi sheet.
    """
    orders = unresolved_orders(details, confirmed_keys=confirmed_keys)
    if not orders:
        return None
    if len(orders) <= _NAME_LIMIT:
        text = f"{', '.join(orders)} có mã chưa được phân loại."
    else:
        text = f"Có {len(orders)} BH chứa mã chưa được phân loại."
    return {"orders": tuple(orders), "count": len(orders), "text": text}


__all__ = [
    "IDENTITY_UNRESOLVED_REASONS", "IdentityState", "LABEL_MISSING_PRICE",
    "LABEL_UNRESOLVED", "STATE_MISSING_PRICE", "STATE_OK", "STATE_UNRESOLVED",
    "UNCLASSIFIABLE_NOTE", "identity_key_of", "sheet_warning", "state_of",
    "unresolved_orders",
]
