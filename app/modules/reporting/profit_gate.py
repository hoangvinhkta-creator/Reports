"""PHB-03 REPAIR — cửa chặn lợi nhuận đọc ĐẦU VÀO KINH TẾ, không đọc nhãn.

Đây là toàn bộ ngữ nghĩa "dòng này có được tính lợi nhuận không" của vertical
Kinh doanh, tách riêng khỏi `business_metrics` vì nó là một QUYẾT ĐỊNH ĐÃ
ĐÓNG BĂNG, không phải một phép cộng.

## Vì sao module này tồn tại

Trước bản sửa này, cửa chặn là đúng một câu:

    if self.status != "AUTO": return None

`status` KHÔNG phải một lý do kinh tế. Nó là kết quả của một phép cộng ở
`excel_exporter.py`: *"dòng này có ít nhất một lý do nào đó"* thì đóng dấu
`PENDING`. Bản audit `docs/reviews/PHB-03-pending-reason-business-classification.md`
đã đếm hết: 19 mã lý do còn hiệu lực, che 31 tình huống thật, và **không mã
nào** là lý do kinh tế khiến không tính được lợi nhuận một khi đã có giá bán,
số lượng và giá nhập hợp lệ.

Tệ hơn, dấu `PENDING` được đóng LÚC CHẠY MÁY và lưu xuống; giá do Owner nhập
được hợp nhất LÚC ĐỌC. Nên cửa chặn cũ đọc một ảnh chụp của đúng cái điều kiện
mà thao tác của Owner vừa làm cho hết đúng — một vòng tự khoá. Với đúng tập
dòng mà luồng nhập giá tay sinh ra để cứu, luồng đó không bao giờ có tác dụng.

## Nguyên tắc thay thế (Owner Decisions OD-1…OD-6)

Cửa chặn mới hỏi những câu về CHÍNH DÒNG HÀNG, và mỗi câu trả lời "không" có
một tên gọi riêng mà Owner đọc được:

    CÓ_TÍNH_ĐƯỢC_LỢI_NHUẬN =
            có giá bán
        VÀ  có số lượng
        VÀ  số lượng > 0                      (OD-1, OD-2)
        VÀ  có giá nhập hiệu lực              (AUTO | MANUAL | MANUAL_OVERRIDE)
        VÀ  thẩm quyền KPI đọc được           (DEC-143 §1 — fail-closed)

Không có vế nào đọc `status`, và đó là toàn bộ điểm của bản sửa (OD-6:
*"Generic PENDING is NOT itself a business reason to block profit"*).

## Cảnh báo KHÔNG phải cửa chặn

Ba tình huống dưới đây từng làm mất lợi nhuận của dòng; nay chúng hiện thành
CẢNH BÁO và con số vẫn được tính:

`Duplicate` (OD-3)
    Trước: doanh thu cộng cả hai dòng, lợi nhuận bỏ cả hai — hai cách xử lý
    mâu thuẫn nhau trên cùng một dòng. Nay: cộng cả doanh thu lẫn lợi nhuận,
    và nói rõ "có dòng trùng, xem lại".

`Giá bán = 0` (OD-4)
    `0` là một giá bán THẬT (hàng tặng kèm), không phải một ô trống. Với
    số lượng 1 và giá nhập 500.000, lợi nhuận là **−500.000** — và con số âm
    đó phải hiện ra. Thay nó bằng `0` là làm báo cáo đẹp hơn sự thật.

`Giá nhập > giá bán`
    Bán lỗ là một sự thật kinh doanh. Giấu nó đi không làm nó biến mất.

## Số lượng ≤ 0 — vì sao nó CHẶN chứ không cảnh báo

`OD-1` viết thẳng: số lượng `0` *"is not zero profit. It is incomplete/
untrusted business data"* — nên dòng đó KHÔNG được chốt lợi nhuận, và cũng
KHÔNG được ghi `0` (một con số `0` bịa còn nguy hiểm hơn một ô trống, vì nó
trông như đã tính xong).

Số lượng ÂM: `OD-2` cấm cả hai chiều — không tự cộng vào KPI nhân viên, và
không được phát minh ngữ nghĩa trả hàng/hoàn tiền trong task này. Cộng
`−1 × biên lợi nhuận` vào tổng công ty CHÍNH LÀ phát minh ngữ nghĩa trả hàng
(nó khẳng định dấu âm nghĩa là hoàn lại). Nên dòng số lượng âm dừng ở mức
"cần xem lại", giữ nguyên vẹn cho tới khi Owner quyết. Xem mục
`OWNER_DECISIONS_REQUIRED` của báo cáo kèm theo.

## Thẩm quyền KPI — cái van phải giữ

`DEC-143` §1: khi `config/eligible_costs.yaml` hỏng, engine trả `None` cho
MỌI dòng — *thà không ra số còn hơn ra số sai*. Đường tính lại khi có giá tay
trước đây áp thẳng công thức mà không hỏi van này, nên nó đi vòng qua đúng
cái van an toàn. Ở đây thẩm quyền là một vế TƯỜNG MINH của cửa chặn, và nó
được kiểm TRƯỚC mọi vế khác.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

# --- Cửa chặn thật: mỗi mã là một câu Owner hành động được -----------------

BLOCK_KPI_AUTHORITY_UNAVAILABLE = "KPI_AUTHORITY_UNAVAILABLE"
BLOCK_SELL_PRICE_MISSING = "SELL_PRICE_MISSING"
BLOCK_QUANTITY_MISSING = "QUANTITY_MISSING"
BLOCK_QUANTITY_ZERO = "QUANTITY_ZERO"
BLOCK_QUANTITY_NEGATIVE = "QUANTITY_NEGATIVE"
BLOCK_PURCHASE_PRICE_MISSING = "PURCHASE_PRICE_MISSING"

#: Tập ĐÓNG. Thêm một mã vào đây là một quyết định nghiệp vụ, không phải một
#: lần refactor — mỗi mã phải chỉ tới một Owner Decision đã ký.
PROFIT_BLOCKERS: tuple[str, ...] = (
    BLOCK_KPI_AUTHORITY_UNAVAILABLE,
    BLOCK_SELL_PRICE_MISSING,
    BLOCK_QUANTITY_MISSING,
    BLOCK_QUANTITY_ZERO,
    BLOCK_QUANTITY_NEGATIVE,
    BLOCK_PURCHASE_PRICE_MISSING,
)

#: Cửa chặn DUY NHẤT mà Owner tự gỡ được ngay trên bảng kê, bằng cách gõ một
#: con số. Coverage tách riêng đúng nhóm này (B02/B03) để màn hình không hứa
#: "nhập giá là xong" cho những dòng mà nhập giá không cứu được.
OWNER_FIXABLE_BLOCKERS: tuple[str, ...] = (BLOCK_PURCHASE_PRICE_MISSING,)

# --- Cảnh báo: hiện ra, KHÔNG chặn ----------------------------------------

WARN_SELL_PRICE_ZERO = "SELL_PRICE_ZERO"
WARN_POSSIBLE_DUPLICATE = "POSSIBLE_DUPLICATE"
WARN_PURCHASE_ABOVE_SELL = "PURCHASE_ABOVE_SELL"
WARN_NEGATIVE_PROFIT = "NEGATIVE_PROFIT"
WARN_PIPELINE_REVIEW = "PIPELINE_REVIEW"

# --- Chặn GÁN KPI cho một nhân viên (KHÔNG chặn lợi nhuận) ----------------

BLOCK_EMPLOYEE_UNRESOLVED = "EMPLOYEE_UNRESOLVED"

#: Mã lý do của pipeline nói "dòng này có bản sao giống hệt trong sổ"
#: (`validation.models.CATEGORY_DUPLICATE`). Đọc để CẢNH BÁO, không để chặn.
PIPELINE_REASON_DUPLICATE = "Duplicate"

#: Mười ba mã chỉ nói MỘT chuyện: "máy đã đi tra giá nhập và không tra ra".
#: Bản audit xếp cả nhóm này là TRIỆU CHỨNG, không phải nguyên nhân độc lập.
#:
#: Chúng bị loại khỏi cảnh báo vì trên dữ liệu thật, `Missing.PurchasePrice`
#: gắn vào **100 % số dòng** của cả hai kỳ golden. Giữ chúng lại sẽ dán câu
#: "có ghi chú cần kiểm tra" lên mọi dòng của mọi báo cáo — kể cả những dòng
#: Owner vừa nhập giá xong — và một cảnh báo xuất hiện ở khắp nơi thì không
#: còn là cảnh báo.
#:
#: Không có thông tin nào bị giấu: khi giá nhập còn thiếu, cửa chặn
#: `PURCHASE_PRICE_MISSING` đã nói đúng điều đó bằng ngôn ngữ hành động được;
#: và bảng kê chi tiết vẫn liệt kê NGUYÊN VĂN mọi mã pipeline ở cột Ghi chú.
PIPELINE_REASONS_SUBSUMED_BY_PURCHASE_PRICE = frozenset({
    # 10 mã `PriceResolutionReason` (Nhóm A của bản audit).
    "SALE_DATE_MISSING", "RAW_PRODUCT_IDENTITY_EMPTY",
    "IDENTITY_SOURCES_UNAVAILABLE", "IDENTITY_UNRESOLVED",
    "IDENTITY_REQUIRES_CONFIRMATION", "TRACKING_HISTORY_SOURCE_UNAVAILABLE",
    "TRACKING_HISTORY_PENDING", "VENDOR_SOURCE_NOT_AUTHORIZED",
    "PUBLIC_PURCHASE_SOURCE_UNAVAILABLE",
    "PUBLIC_PURCHASE_NO_PRICE_AT_SALE_DATE",
    # Bản gộp của đúng 10 mã trên.
    "Missing.PurchasePrice",
    # Kết quả còn trống — hệ quả, không phải phát hiện độc lập. Khi thẩm quyền
    # KPI thật sự hỏng thì cửa chặn `KPI_AUTHORITY_UNAVAILABLE` mới là chỗ nói.
    "Pending.eligible_kpi_profit",
    # Hai mã đã nghỉ hưu (`DEC-PAN-001`), chỉ còn trong dữ liệu cũ.
    "Pending.accounting_purchase_price", "Pending.accounting_profit",
})

# Nhãn tiếng Việt cho từng mã, viết cho Owner chứ không cho lập trình viên.
BLOCKER_LABELS = {
    BLOCK_KPI_AUTHORITY_UNAVAILABLE: (
        "Bảng thẩm quyền chi phí KPI đang hỏng — hệ thống từ chối ra số cho "
        "MỌI dòng cho tới khi người quản trị sửa file cấu hình"),
    BLOCK_SELL_PRICE_MISSING: "Dòng chưa có giá bán",
    BLOCK_QUANTITY_MISSING: "Dòng chưa có số lượng",
    BLOCK_QUANTITY_ZERO: (
        "Số lượng bằng 0 — đây là dữ liệu chưa đủ tin, không phải lãi 0 đồng. "
        "Cần sửa số lượng trên sổ gốc"),
    BLOCK_QUANTITY_NEGATIVE: (
        "Số lượng âm — cần xem lại. Chưa có quy tắc nào của Owner nói dấu âm "
        "nghĩa là gì, nên hệ thống không tự diễn giải"),
    BLOCK_PURCHASE_PRICE_MISSING: "Chưa có giá nhập — Owner nhập được ngay tại đây",
}

WARNING_LABELS = {
    WARN_SELL_PRICE_ZERO: (
        "Giá bán bằng 0 (thường là hàng tặng kèm). Lợi nhuận vẫn được tính "
        "đúng theo phép trừ, nên nó có thể ra số âm"),
    WARN_POSSIBLE_DUPLICATE: (
        "Sổ có một dòng khác giống hệt dòng này. Doanh thu và lợi nhuận VẪN "
        "được tính — nếu đây thật sự là gõ nhầm hai lần thì cần sửa trên sổ gốc"),
    WARN_PURCHASE_ABOVE_SELL: "Giá nhập cao hơn giá bán — dòng này đang bán lỗ",
    WARN_NEGATIVE_PROFIT: "Lợi nhuận của dòng này là số âm",
    WARN_PIPELINE_REVIEW: (
        "Hệ thống có ghi chú cần kiểm tra cho dòng này. Ghi chú đó KHÔNG chặn "
        "việc tính lợi nhuận nữa — xem chi tiết ở cột Ghi chú"),
    BLOCK_EMPLOYEE_UNRESOLVED: (
        "Chưa biết dòng này của nhân viên nào. Lợi nhuận vẫn vào tổng của kỳ, "
        "nhưng chưa cộng cho ai — chọn nhân viên để gán"),
}


def profit_blockers(
    *,
    sell_price: Optional[Decimal],
    quantity: Optional[Decimal],
    purchase_price: Optional[Decimal],
    kpi_authority_valid: bool,
) -> tuple[str, ...]:
    """Mọi lý do THẬT khiến dòng này chưa chốt được lợi nhuận, đã sắp thứ tự.

    Trả về tuple RỖNG ⟺ tính được. Trả nhiều mã cùng lúc là cố ý: một dòng
    vừa thiếu giá nhập vừa có số lượng 0 thì Owner phải sửa cả hai, và một
    màn hình chỉ nói một nửa sẽ khiến họ nhập giá xong rồi ngơ ngác vì con số
    vẫn chưa lên.

    Thẩm quyền KPI đứng ĐẦU vì nó là lỗi cấu hình toàn hệ thống, không phải
    lỗi của dòng — Owner đọc nó xong thì biết ngay không cần sửa dòng nào cả.
    """
    blockers: list[str] = []
    if not kpi_authority_valid:
        blockers.append(BLOCK_KPI_AUTHORITY_UNAVAILABLE)
    if sell_price is None:
        blockers.append(BLOCK_SELL_PRICE_MISSING)
    if quantity is None:
        blockers.append(BLOCK_QUANTITY_MISSING)
    elif quantity == 0:
        blockers.append(BLOCK_QUANTITY_ZERO)
    elif quantity < 0:
        blockers.append(BLOCK_QUANTITY_NEGATIVE)
    if purchase_price is None:
        blockers.append(BLOCK_PURCHASE_PRICE_MISSING)
    return tuple(blockers)


def profit_warnings(
    *,
    sell_price: Optional[Decimal],
    purchase_price: Optional[Decimal],
    profit: Optional[Decimal],
    pending_reasons: tuple[str, ...],
) -> tuple[str, ...]:
    """Những điều Owner NÊN BIẾT về dòng này, không điều nào chặn con số.

    `pending_reasons` là danh sách mã pipeline đã lưu xuống database. Ở đây nó
    được dùng đúng một việc — dựng cảnh báo — chứ không quyết định gì.
    """
    warnings: list[str] = []
    if sell_price is not None and sell_price == 0:
        warnings.append(WARN_SELL_PRICE_ZERO)
    if PIPELINE_REASON_DUPLICATE in pending_reasons:
        warnings.append(WARN_POSSIBLE_DUPLICATE)
    if (sell_price is not None and purchase_price is not None
            and purchase_price > sell_price):
        warnings.append(WARN_PURCHASE_ABOVE_SELL)
    if profit is not None and profit < 0:
        warnings.append(WARN_NEGATIVE_PROFIT)
    # Ghi chú pipeline còn lại được gom thành MỘT cảnh báo: chi tiết từng mã
    # hiện ở cột Ghi chú, còn ở đây Owner chỉ cần biết "có ghi chú, không chặn".
    others = [reason for reason in pending_reasons
              if reason != PIPELINE_REASON_DUPLICATE
              and reason not in PIPELINE_REASONS_SUBSUMED_BY_PURCHASE_PRICE]
    if others:
        warnings.append(WARN_PIPELINE_REVIEW)
    return tuple(warnings)


def label(code: str) -> str:
    """Nhãn tiếng Việt của một mã; mã lạ hiện nguyên văn thay vì biến mất."""
    return BLOCKER_LABELS.get(code) or WARNING_LABELS.get(code) or code


__all__ = [
    "BLOCKER_LABELS", "BLOCK_EMPLOYEE_UNRESOLVED",
    "BLOCK_KPI_AUTHORITY_UNAVAILABLE", "BLOCK_PURCHASE_PRICE_MISSING",
    "BLOCK_QUANTITY_MISSING", "BLOCK_QUANTITY_NEGATIVE", "BLOCK_QUANTITY_ZERO",
    "BLOCK_SELL_PRICE_MISSING", "OWNER_FIXABLE_BLOCKERS",
    "PIPELINE_REASON_DUPLICATE",
    "PIPELINE_REASONS_SUBSUMED_BY_PURCHASE_PRICE",
    "PROFIT_BLOCKERS", "WARNING_LABELS",
    "WARN_NEGATIVE_PROFIT", "WARN_PIPELINE_REVIEW", "WARN_POSSIBLE_DUPLICATE",
    "WARN_PURCHASE_ABOVE_SELL", "WARN_SELL_PRICE_ZERO",
    "label", "profit_blockers", "profit_warnings",
]
