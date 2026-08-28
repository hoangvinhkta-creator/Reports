"""Hai khoá của một raw product identity — `TASK-105D` data contract §6.3.

Đây là file nhỏ nhất của module nhưng là nơi một sai lầm tốn kém nhất: mọi
thứ còn lại (mapping store, alias memory, rejection memory, registry lịch sử)
đều đánh khoá bằng `raw_identity_key`. Chuẩn hoá quá tay ở đây làm hai model
khác nhau gộp thành một identity, và hậu quả đi thẳng vào giá vốn rồi vào
lương — đúng đường lỗi mà `DEC-147` §4 đã ghi nhận một lần trên tài sản thật.

Vì thế contract tách làm HAI khoá, không phải một (`D-07`):

    raw_identity_key         = NFC → gộp khoảng trắng → trim
                               GIỮ NGUYÊN hoa/thường, dấu tiếng Việt, dấu câu,
                               và mọi model token. Đây là KHOÁ ĐỊNH DANH.

    normalized_matching_aid  = raw_identity_key + casefold, rồi NFC lại
                               Đây là AID TÌM CANDIDATE, không bao giờ là khoá
                               định danh (`INV-20`).

Nếu chỉ có một khoá, ta buộc phải chọn giữa "bỏ lỡ biến thể hoa/thường" và
"gộp nhầm hai model". Tách hai khoá là cách không phải chọn.

Hai hàm dưới đây cố ý **uỷ quyền** cho `app/modules/validation/text.py`
(`DEC-145` §2) thay vì cài lại phép chuẩn hoá: một bản sao thứ hai của
`fold()` là một nguồn drift, và `INV-05` tồn tại chính vì Tracking đã từng
gộp nhầm hai mã bằng một `normCode` viết riêng.
"""

from __future__ import annotations

from app.modules.validation.text import fold, normalize_text


class EmptyRawIdentityError(ValueError):
    """`product_raw` rỗng sau chuẩn hoá — không thể sinh khoá định danh.

    Cố ý là lỗi chứ không phải một khoá rỗng: một khoá rỗng sẽ gộp MỌI dòng
    thiếu tên hàng vào cùng một identity, và một `confirmation_action` duy
    nhất sẽ map sai toàn bộ chúng (`INV-30` + `INV-87` cộng lại thành một lỗi
    hàng loạt). Dòng thiếu tên hàng thuộc validation ở tầng import, không
    thuộc resolver.
    """


def raw_identity_key(product_raw) -> str:
    """Khoá định danh bền vững của một raw accounting product identity.

    KHÔNG bỏ dấu, KHÔNG bỏ dấu câu, KHÔNG rút gọn model token (`INV-26`).
    Chỉ mất thông tin ở đúng hai mức an toàn tuyệt đối: dạng Unicode (NFC) và
    khoảng trắng thừa — hai thứ không bao giờ phân biệt được hai model.
    """
    key = normalize_text(product_raw)
    if not key:
        raise EmptyRawIdentityError(
            "product_raw rỗng sau chuẩn hoá — không sinh được raw_identity_key"
        )
    return key


def normalized_matching_aid(product_raw) -> str:
    """Aid tìm candidate. KHÔNG phải canonical identity (`INV-20`).

    Mạnh hơn `raw_identity_key` đúng một bậc (casefold), đủ để thấy biến thể
    hoa/thường, và vì mạnh hơn nên nó **không** được trao quyền auto-resolve:
    `ALIAS_AID_UNIQUE` là candidate-only (`INV-28b`, `DEC-156`/`OR-02`).
    """
    aid = fold(product_raw)
    if not aid:
        raise EmptyRawIdentityError(
            "product_raw rỗng sau chuẩn hoá — không sinh được normalized_matching_aid"
        )
    return aid
