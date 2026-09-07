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

#: R2 §4.2 — mã lý do nói rằng hai nguồn mapping đã xác nhận đang CHỎI NHAU.
#: Không nằm trong `IDENTITY_UNRESOLVED_REASONS`: "chưa ai xem" và "hai bên đã
#: xem và không khớp" là hai tình huống khác nhau, cần hai câu khác nhau.
IDENTITY_CONFLICT_REASONS = frozenset({"IDENTITY_CONFLICT"})

#: R2 §4.3 — mã lý do của một dòng ĐÃ được xác nhận là ngoài bảng giá. Nguồn
#: SỐNG của trạng thái này là log quyết định (xem `Decisions`); mã dưới đây là
#: bằng chứng mà lần chạy gần nhất đã ghi lại, dùng khi log không đọc được.
IDENTITY_OUT_OF_CATALOG_REASONS = frozenset({"IDENTITY_OUT_OF_CATALOG"})

STATE_UNRESOLVED = "IDENTITY_UNRESOLVED"
STATE_MISSING_PRICE = "MISSING_PURCHASE_PRICE"
STATE_OK = "OK"

# --- R2 §4.1 — BỐN trạng thái nhận diện hiệu lực --------------------------
#
# `state` ở trên trả lời câu hỏi TRÌNH BÀY ("ô mã hàng hiện chữ gì") và nó có
# ba giá trị. `classification` dưới đây trả lời câu hỏi NGHIỆP VỤ ("dòng này
# đang ở đâu trong luồng phân loại") và nó có bốn. Hai câu hỏi khác nhau, nên
# hai trường — gộp chúng lại sẽ buộc một trong hai phải nói dối:
#
#     OUT_OF_CATALOG thiếu giá  → trình bày "Thiếu giá", nghiệp vụ "ngoài bảng"
#     MATCHED_TRACKING thiếu giá → trình bày "Thiếu giá", nghiệp vụ "đã khớp"
#
# Hai dòng đó hiện CÙNG một chữ và cần HAI hành động khác nhau.
CLASS_MATCHED_TRACKING = "MATCHED_TRACKING"
CLASS_NEEDS_REVIEW = "NEEDS_REVIEW"
CLASS_OUT_OF_CATALOG = "OUT_OF_CATALOG"
CLASS_CONFLICT = "CONFLICT"

CLASSIFICATIONS = (
    CLASS_MATCHED_TRACKING, CLASS_NEEDS_REVIEW, CLASS_OUT_OF_CATALOG,
    CLASS_CONFLICT,
)

LABEL_UNRESOLVED = "Chưa phân loại"
LABEL_MISSING_PRICE = "Thiếu giá"
LABEL_OUT_OF_CATALOG = "Ngoài bảng giá"
LABEL_CONFLICT = "Xung đột mã"

CLASSIFICATION_LABELS = {
    CLASS_MATCHED_TRACKING: "Đã khớp Tracking",
    CLASS_NEEDS_REVIEW: LABEL_UNRESOLVED,
    CLASS_OUT_OF_CATALOG: LABEL_OUT_OF_CATALOG,
    CLASS_CONFLICT: LABEL_CONFLICT,
}

CLASSIFICATION_TITLES = {
    CLASS_MATCHED_TRACKING: "Đã khớp một mã sản phẩm của Tracking",
    CLASS_NEEDS_REVIEW: (
        "Chưa nhận diện được mặt hàng này — bấm để chọn sản phẩm tương ứng "
        "bên Tracking, hoặc đánh dấu là hàng ngoài bảng giá"),
    CLASS_OUT_OF_CATALOG: (
        "Đã xác nhận mặt hàng này KHÔNG có trên bảng giá Tracking. Phân loại "
        "đã xong; dòng vẫn nằm trong báo cáo và cần một giá nhập tay"),
    CLASS_CONFLICT: (
        "Mã đã xác nhận của Reports và mã do Tracking trả về đang khác nhau — "
        "bấm để chọn lại. Hệ thống KHÔNG tự chọn bên thắng"),
}

LABEL_TITLES = {
    STATE_UNRESOLVED: CLASSIFICATION_TITLES[CLASS_NEEDS_REVIEW],
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
class Decisions:
    """Các quyết định phân loại ĐÃ LƯU, đọc một lần cho cả trang (R2).

    Gói hai tập vào một object thay vì thêm dần tham số vào `state_of`: mọi
    màn hình nghiệp vụ gọi hàm đó, và mỗi lần thêm một tham số là một lần phải
    sửa mọi nơi gọi — chính là cách một trong số chúng bị bỏ quên và hiện sai
    trạng thái.

    RỖNG là mặc định ĐÚNG: nó cho ra chính xác hành vi trước R2.
    """

    confirmed: frozenset = frozenset()
    out_of_catalog: frozenset = frozenset()

    @classmethod
    def of(cls, confirmed=None, out_of_catalog=None) -> "Decisions":
        return cls(
            confirmed=frozenset(confirmed or ()),
            out_of_catalog=frozenset(out_of_catalog or ()),
        )


@dataclass(frozen=True)
class IdentityState:
    """Trạng thái nhận diện HIỆU LỰC của một dòng."""

    state: str
    #: Khoá định danh của mặt hàng trên dòng, `None` khi không dựng được.
    identity_key: Optional[str] = None
    #: R2 §4.1 — một trong bốn `CLASSIFICATIONS`. Mặc định `MATCHED_TRACKING`
    #: giữ nguyên ngữ nghĩa cũ cho mọi nơi dựng object này bằng tay.
    classification: str = CLASS_MATCHED_TRACKING

    @property
    def unresolved(self) -> bool:
        return self.state == STATE_UNRESOLVED

    @property
    def missing_price(self) -> bool:
        return self.state == STATE_MISSING_PRICE

    @property
    def out_of_catalog(self) -> bool:
        return self.classification == CLASS_OUT_OF_CATALOG

    @property
    def conflict(self) -> bool:
        return self.classification == CLASS_CONFLICT

    @property
    def needs_review(self) -> bool:
        return self.classification == CLASS_NEEDS_REVIEW

    @property
    def label(self) -> Optional[str]:
        """Chữ hiện cạnh mã đơn. `None` = không có gì đáng nói.

        `CONFLICT` và `OUT_OF_CATALOG` có chữ RIÊNG: dán "Chưa phân loại" lên
        một dòng đã xác nhận ngoài bảng giá sẽ mời Owner đi phân loại lại đúng
        thứ họ vừa phân loại xong, còn dán nó lên một mâu thuẫn sẽ giấu mất
        chuyện có hai mã đang chỏi nhau.
        """
        if self.classification == CLASS_CONFLICT:
            return LABEL_CONFLICT
        if self.classification == CLASS_OUT_OF_CATALOG:
            return (LABEL_OUT_OF_CATALOG if self.state == STATE_MISSING_PRICE
                    else None)
        if self.state == STATE_UNRESOLVED:
            return LABEL_UNRESOLVED
        if self.state == STATE_MISSING_PRICE:
            return LABEL_MISSING_PRICE
        return None

    @property
    def title(self) -> Optional[str]:
        if self.classification in (CLASS_CONFLICT, CLASS_OUT_OF_CATALOG):
            return CLASSIFICATION_TITLES[self.classification]
        return LABEL_TITLES.get(self.state)

    @property
    def classifiable(self) -> bool:
        """Có mở được luồng phân loại cho dòng này không (`§PI-04`).

        `CONFLICT` cũng mở được, và bắt buộc phải mở được: §4.2 nói cách thoát
        khỏi mâu thuẫn là người dùng CHỌN LẠI, nên một dòng mâu thuẫn mà không
        bấm vào được là một dòng không có đường ra.
        """
        return (self.unresolved or self.conflict) and self.identity_key is not None


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
    decisions: Optional[Decisions] = None,
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
    if decisions is None:
        decisions = Decisions.of(confirmed=confirmed_keys)
    line = detail["line"]
    key = identity_key_of(detail.get("product_raw"))
    reasons = set(line.pending_reasons or ())

    # Thứ tự dưới đây là hợp đồng, không phải sở thích. Quyết định ĐÃ LƯU của
    # người đứng TRƯỚC mọi mã lý do của pipeline, vì mã lý do là bằng chứng
    # của lần chạy TRƯỚC ĐÓ còn quyết định là điều mới nhất người dùng nói.
    if key is not None and key in decisions.out_of_catalog:
        return _priced(CLASS_OUT_OF_CATALOG, line, key)
    if key is not None and key in decisions.confirmed:
        return _priced(CLASS_MATCHED_TRACKING, line, key)

    # Không có quyết định nào đè lên: đọc bằng chứng mà lần chạy đã ghi.
    if reasons & IDENTITY_OUT_OF_CATALOG_REASONS:
        return _priced(CLASS_OUT_OF_CATALOG, line, key)
    if reasons & IDENTITY_CONFLICT_REASONS:
        return IdentityState(STATE_UNRESOLVED, identity_key=key,
                             classification=CLASS_CONFLICT)
    if reasons & IDENTITY_UNRESOLVED_REASONS:
        return IdentityState(STATE_UNRESOLVED, identity_key=key,
                             classification=CLASS_NEEDS_REVIEW)
    return _priced(CLASS_MATCHED_TRACKING, line, key)


def _priced(classification: str, line, key) -> IdentityState:
    """Chiều GIÁ của một dòng đã phân loại xong — `Thiếu giá` hay không.

    Tách ra một hàm vì cả ba nhánh "đã phân loại" của `state_of` cần đúng phép
    này, và ba bản sao của nó là ba cơ hội để một bản quên mất `None`.
    """
    if line.purchase_price is None:
        return IdentityState(STATE_MISSING_PRICE, identity_key=key,
                             classification=classification)
    return IdentityState(STATE_OK, identity_key=key,
                         classification=classification)


# --- Cảnh báo GỌN của một sheet (`§13`, `§PI-10`) -------------------------

#: Số BH tối đa được gọi TÊN trong câu cảnh báo. Quá ngưỡng này thì câu nói
#: bao nhiêu BH thay vì liệt kê — Owner yêu cầu MỘT dòng gọn, không phải một
#: danh sách (`§13`).
_NAME_LIMIT = 3


def unresolved_orders(
    details: Iterable[dict], *, confirmed_keys: Optional[frozenset[str]] = None,
    decisions: Optional[Decisions] = None,
) -> list[str]:
    """Các BH của sheet còn chứa mã chưa phân loại, theo thứ tự xuất hiện.

    Trả về BH chứ không phải dòng: Owner đọc bảng kê theo BH, và một cảnh báo
    đếm "17 dòng" trong khi bảng chỉ có 7 khối BH sẽ không dẫn được mắt tới
    chỗ nào.
    """
    seen: list[str] = []
    for detail in details:
        state = state_of(detail, confirmed_keys=confirmed_keys,
                         decisions=decisions)
        # `CONFLICT` KHÔNG được đếm vào "chưa phân loại": nó đã có câu cảnh
        # báo riêng và một hàng đợi riêng. Gộp lại sẽ nói với Owner rằng còn
        # việc phân loại chưa làm, trong khi việc thật là chọn lại giữa hai mã.
        if not (state.unresolved and state.needs_review):
            continue
        order_key = detail["order_key"]
        if order_key not in seen:
            seen.append(order_key)
    return seen


def sheet_warning(
    details: Iterable[dict], *, confirmed_keys: Optional[frozenset[str]] = None,
    decisions: Optional[Decisions] = None,
) -> Optional[dict]:
    """MỘT dòng cảnh báo cho cả sheet, hoặc `None` khi không có gì để báo.

    `None` chứ không phải một câu "không có dòng nào chưa phân loại": một
    trạng thái BÌNH THƯỜNG không đáng chiếm một dòng trên đầu mọi sheet.
    """
    orders = unresolved_orders(details, confirmed_keys=confirmed_keys,
                               decisions=decisions)
    if not orders:
        return None
    if len(orders) <= _NAME_LIMIT:
        text = f"{', '.join(orders)} có mã chưa được phân loại."
    else:
        text = f"Có {len(orders)} BH chứa mã chưa được phân loại."
    return {"orders": tuple(orders), "count": len(orders), "text": text}


__all__ = [
    "CLASSIFICATIONS", "CLASSIFICATION_LABELS", "CLASSIFICATION_TITLES",
    "CLASS_CONFLICT", "CLASS_MATCHED_TRACKING", "CLASS_NEEDS_REVIEW",
    "CLASS_OUT_OF_CATALOG", "Decisions", "IDENTITY_CONFLICT_REASONS",
    "IDENTITY_OUT_OF_CATALOG_REASONS", "IDENTITY_UNRESOLVED_REASONS",
    "IdentityState", "LABEL_CONFLICT", "LABEL_MISSING_PRICE",
    "LABEL_OUT_OF_CATALOG", "LABEL_UNRESOLVED", "STATE_MISSING_PRICE",
    "STATE_OK", "STATE_UNRESOLVED", "UNCLASSIFIABLE_NOTE", "identity_key_of",
    "sheet_warning", "state_of", "unresolved_orders",
]
