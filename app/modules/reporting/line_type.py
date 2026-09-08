"""R3 §2 — LOẠI DÒNG hiệu lực, và luật giá nhập KPI đi kèm từng loại.

Module này THUẦN: không SQL, không Flask, không I/O. Nó nhận từ vựng đã nạp và
những giá trị của một dòng, rồi trả lời đúng hai câu:

    1. Dòng này là loại gì?                       `classify`
    2. Loại đó nói gì về giá nhập KPI của nó?     `policy_purchase_price`

## Vì sao loại dòng phải tồn tại như một khái niệm riêng

Sổ kế toán ghi bốn thứ RẤT khác nhau vào cùng một bảng, cùng một hình dạng
dòng: một chiếc tủ lạnh bán ra, một khoản chiết khấu, một khoản phí vận
chuyển, và một món phụ kiện tặng kèm. Cho tới R3, đường báo cáo đối xử với cả
bốn như nhau — đi hỏi giá nhập, không tra ra, rồi dán `Missing.PurchasePrice`.

Hệ quả đo được trên dữ liệu thật: `Chi phí vận chuyển` (19 dòng kỳ 01/2026,
10 dòng kỳ 06/2026), `Chi phí lắp đặt`, `Chênh VAT`, `Phụ Phí` — không dòng
nào trong số đó CÓ một giá nhập để tra, và không dòng nào sẽ bao giờ có. Chúng
khoá `PROFIT_COVERAGE` ở dưới 100 % vĩnh viễn, tức khoá luôn cả trạng thái
`OFFICIAL` của cả kỳ, vì một lý do không ai sửa được bằng bất kỳ thao tác nào.

`OD-105B-01` §3 đã ký đúng câu trả lời cho nhóm đó, từ lâu:

    AccountingPurchasePrice = 0 BY DEFINITION
    provenance = Policy:SupplementaryExpenseZeroPurchasePrice

Điều còn thiếu là một tầng phân loại có thẩm quyền để BIẾT dòng nào thuộc
nhóm đó — đúng thứ mà `TASK-105B-Q3` bị `BLOCKED_BY [TASK-103]` chờ. Module
này là tầng đó, ở đúng chỗ `OD-105B-01` §C yêu cầu: BÊN TRÊN provider, không
nằm trong `FilePriceProvider`.

## Ranh giới không được vượt: `0` chính sách ≠ `0` thay cho thiếu

`OD-105B-01` §3 viết liền hai câu, và câu thứ hai quan trọng ngang câu đầu:

    Product line **thông thường** không có price record: lookup = None → Pending.
    **Không** dùng purchase_price = 0 thay cho missing.

Vì vậy `policy_purchase_price` trả `Decimal(0)` cho ĐÚNG hai loại đã có thẩm
quyền (`FEE`, `DISCOUNT`) và trả `None` cho mọi loại khác — kể cả
`ACCESSORY_GIFT`, vốn LÀ một món hàng thật có giá vốn thật, chỉ là bán giá 0.
Một chiếc giá treo tivi tặng kèm vẫn tốn tiền mua; ghi giá nhập của nó là 0 sẽ
biến một khoản lỗ có thật thành lãi 0 đồng.

## `RETURN_CANCEL` và `UNDECIDED_DOCUMENT` — hai chỗ hệ thống DỪNG LẠI

`OD-2` (`profit_gate`) đã ghi thẳng ranh giới: *"không được phát minh ngữ nghĩa
trả hàng/hoàn tiền trong task này"*. R3 KHÔNG đảo lại điều đó. Nó chỉ làm cho
sự thiếu vắng ấy NHÌN THẤY ĐƯỢC: một dòng thuộc chứng từ hoàn/hủy, hay thuộc
một loại chứng từ chưa ai định nghĩa, không còn lặng lẽ đi vào đường tính lãi
như một dòng bán bình thường — nó nhận một mã chặn có tên và một chỗ trong
hàng đợi ngoại lệ.

Đó là lý do từ vựng loại chứng từ nằm trong `config/line_types.yaml` và ra
đời RỖNG ở phần hoàn/hủy: repo này không có một quyết định nào của Owner nói
`BTL` nghĩa là gì. Tự điền vào đó chính là phát minh ngữ nghĩa mà `OD-2` cấm.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from decimal import Decimal
from typing import Iterable, Optional

from app.modules.validation.text import compile_keyword_patterns, matches_any

TYPE_SALE = "SALE"
TYPE_DISCOUNT = "DISCOUNT"
TYPE_ACCESSORY_GIFT = "ACCESSORY_GIFT"
TYPE_FEE = "FEE"
TYPE_RETURN_CANCEL = "RETURN_CANCEL"
TYPE_UNDECIDED_DOCUMENT = "UNDECIDED_DOCUMENT"

#: Tập ĐÓNG. Thêm một loại là một quyết định nghiệp vụ, không phải một lần
#: refactor — mỗi loại phải chỉ tới một Owner Decision đã ký.
LINE_TYPES: tuple[str, ...] = (
    TYPE_SALE, TYPE_DISCOUNT, TYPE_ACCESSORY_GIFT, TYPE_FEE,
    TYPE_RETURN_CANCEL, TYPE_UNDECIDED_DOCUMENT,
)

#: Hai loại có thẩm quyền `OD-105B-01` §3 cho giá nhập bằng 0. Không loại nào
#: khác được thêm vào đây mà không có một Owner Decision mới.
POLICY_ZERO_TYPES: frozenset = frozenset({TYPE_FEE, TYPE_DISCOUNT})

#: Provenance của con số 0 ấy — nguyên văn `OD-105B-01` §3, để một lần đọc lại
#: bằng chứng chỉ đúng tới quyết định đã ký chứ không tới file này.
POLICY_ZERO_PROVENANCE = "Policy:SupplementaryExpenseZeroPurchasePrice"

#: Hai loại mà hệ thống KHÔNG có thẩm quyền để tính lãi (`OD-2`).
UNDECIDED_TYPES: frozenset = frozenset(
    {TYPE_RETURN_CANCEL, TYPE_UNDECIDED_DOCUMENT})

LINE_TYPE_LABELS = {
    TYPE_SALE: "Hàng bán",
    TYPE_DISCOUNT: "Chiết khấu",
    TYPE_ACCESSORY_GIFT: "Phụ kiện / quà tặng",
    TYPE_FEE: "Phí",
    TYPE_RETURN_CANCEL: "Hoàn / hủy",
    TYPE_UNDECIDED_DOCUMENT: "Chứng từ chưa định nghĩa",
}


@dataclass(frozen=True)
class LineTypeVocabulary:
    """Từ vựng đã biên dịch. Dựng bằng `of()`, không bằng constructor trần."""

    #: ``tiền tố chứng từ (đã casefold) → loại dòng``. Tiền tố KHÔNG có trong
    #: bảng này ⟹ `UNDECIDED_DOCUMENT`, không phải `SALE`.
    document_prefixes: dict
    fee_patterns: tuple = ()
    discount_patterns: tuple = ()
    #: Bảng rỗng ⟹ mọi tiền tố đều chưa định nghĩa. Đó là một cấu hình HỎNG,
    #: không phải một mặc định — `of()` từ chối nó.
    @classmethod
    def of(
        cls, *, document_prefixes: dict,
        fee_keywords: Iterable[str] = (),
        discount_keywords: Iterable[str] = (),
    ) -> "LineTypeVocabulary":
        prefixes = {}
        for prefix, line_type in (document_prefixes or {}).items():
            folded = _fold_prefix(prefix)
            if not folded:
                continue
            if line_type not in LINE_TYPES:
                raise ValueError(
                    f"Loại dòng {line_type!r} của tiền tố {prefix!r} không thuộc "
                    f"tập đã freeze {LINE_TYPES}.")
            prefixes[folded] = line_type
        if not prefixes:
            raise ValueError(
                "config/line_types.yaml không khai một tiền tố chứng từ nào — "
                "mọi dòng sẽ thành UNDECIDED_DOCUMENT. Đây là cấu hình hỏng, "
                "không phải một mặc định an toàn.")
        return cls(
            document_prefixes=prefixes,
            fee_patterns=tuple(compile_keyword_patterns(fee_keywords)),
            discount_patterns=tuple(compile_keyword_patterns(discount_keywords)),
        )

    def document_type(self, order_key: Optional[str]) -> Optional[str]:
        """Loại của CHỨNG TỪ mang dòng này, `None` khi là chứng từ bán hàng.

        Khớp theo tiền tố CHỮ CÁI đứng đầu số chứng từ (`BH62171` → `bh`).
        Không đoán: một số chứng từ không bắt đầu bằng chữ cái nào, hay bắt
        đầu bằng một tiền tố chưa khai, đều ra `UNDECIDED_DOCUMENT`.
        """
        prefix = _letter_prefix(order_key)
        if prefix is None:
            return TYPE_UNDECIDED_DOCUMENT
        line_type = self.document_prefixes.get(prefix)
        if line_type is None:
            return TYPE_UNDECIDED_DOCUMENT
        return None if line_type == TYPE_SALE else line_type


def _fold_prefix(value: Optional[str]) -> str:
    if value is None:
        return ""
    return unicodedata.normalize("NFC", str(value)).strip().casefold()


def _letter_prefix(order_key: Optional[str]) -> Optional[str]:
    text = _fold_prefix(order_key)
    letters = []
    for char in text:
        if char.isalpha():
            letters.append(char)
        else:
            break
    return "".join(letters) or None


def classify(
    *, vocabulary: Optional[LineTypeVocabulary], order_key: Optional[str],
    product_raw: Optional[str], sell_price: Optional[Decimal],
    quantity: Optional[Decimal],
) -> str:
    """Loại HIỆU LỰC của một dòng. Thứ tự các bước là một hợp đồng.

    1. **Chứng từ trước dòng.** Nếu cả chứng từ là hoàn/hủy, thì một dòng
       "Chi phí vận chuyển" bên trong nó cũng là một khoản hoàn/hủy — không
       phải một khoản phí mới phát sinh. Đọc dòng trước chứng từ sẽ cho ra
       đúng cái sai đó.
    2. **Chiết khấu trước phí.** "Chiết khấu" và "voucher" là một khoản GIẢM
       DOANH THU; phí là một khoản THU THÊM. Hai luật giá nhập giống nhau
       (`0` theo chính sách) nhưng hai ngữ nghĩa doanh thu khác nhau, nên
       chúng không được gộp làm một loại.
    3. **Phí.**
    4. **Quà tặng kèm** — một mặt hàng THẬT bán giá 0 với số lượng dương
       (`OD-4`: *"`0` là một giá bán THẬT (hàng tặng kèm), không phải một ô
       trống"*). Số lượng `0`/âm KHÔNG vào đây: `OD-1`/`OD-2` đã nói chúng là
       dữ liệu chưa đủ tin, và dán nhãn "quà tặng" lên chúng sẽ là một khẳng
       định mà không ai đưa ra.
    5. Còn lại là hàng bán.

    `vocabulary` là `None` ⟹ MỌI dòng là `SALE`, tức đúng hành vi trước R3.
    Đó là mặc định của mọi nơi dựng một dòng bằng tay trong test cũ, và nó
    phải giữ nguyên nghĩa.
    """
    if vocabulary is None:
        return TYPE_SALE

    document = vocabulary.document_type(order_key)
    if document is not None:
        return document

    if matches_any(product_raw, list(vocabulary.discount_patterns)):
        return TYPE_DISCOUNT
    if matches_any(product_raw, list(vocabulary.fee_patterns)):
        return TYPE_FEE
    if (sell_price is not None and sell_price == 0
            and quantity is not None and quantity > 0):
        return TYPE_ACCESSORY_GIFT
    return TYPE_SALE


def policy_purchase_price(line_type: str) -> Optional[Decimal]:
    """Giá nhập KPI mà CHÍNH SÁCH quy định cho loại này, hoặc `None`.

    `None` KHÔNG có nghĩa "bằng 0". Nó có nghĩa "chính sách không nói gì, hãy
    đi hỏi các nguồn giá thật" — và nếu không nguồn nào trả lời thì dòng ở
    `PENDING`. Đây là ranh giới mà `OD-105B-01` §3 câu thứ hai đặt ra.
    """
    return Decimal(0) if line_type in POLICY_ZERO_TYPES else None


def label(line_type: str) -> str:
    return LINE_TYPE_LABELS.get(line_type, line_type)


__all__ = [
    "LINE_TYPES", "LINE_TYPE_LABELS", "LineTypeVocabulary",
    "POLICY_ZERO_PROVENANCE", "POLICY_ZERO_TYPES", "TYPE_ACCESSORY_GIFT",
    "TYPE_DISCOUNT", "TYPE_FEE", "TYPE_RETURN_CANCEL", "TYPE_SALE",
    "TYPE_UNDECIDED_DOCUMENT", "UNDECIDED_TYPES", "classify", "label",
    "policy_purchase_price",
]
