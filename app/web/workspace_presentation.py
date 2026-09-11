"""`DEC-PHB02-08` — mô hình hiển thị của KHÔNG GIAN LÀM VIỆC Nhân viên.

Module này chỉ đổi CÁCH VIẾT những con số mà `business_metrics` đã tính xong.
Nó không có một phép tính nghiệp vụ nào của riêng nó, và đó là điều kiện để
`§60` đúng: một thay đổi thuần giao diện không được làm đổi một con số nào.

Nó nằm TÁCH khỏi `business_presentation` một cách có chủ đích. Bốn màn hình
của PHB-03/PHB-05 (Tổng hợp · Nhân viên cũ · Bảng kê giá nhập · Target) đã
được nghiệm thu và vẫn đang chạy; nhồi cách trình bày mới vào cùng file sẽ
khiến mỗi lần sửa không gian làm việc là một lần chạm vào mã của chúng. Cái gì
dùng chung thì IMPORT LẠI từ `business_presentation` — `gated_cell`,
`month_over_month`, `percent` — chứ không chép lại: hai bản sao của cùng một
quy tắc trình bày là hai câu trả lời chờ lệch nhau.

## Ba quy ước hiển thị mà Owner yêu cầu tường minh

    NGÀY        `DD/MM/YYYY` (`§24`). Không bao giờ `MM/DD/YYYY` — `03/08` là
                một ngày khác nhau ở hai quy ước, và không có gì trên màn hình
                nói cho người đọc biết đang dùng quy ước nào.
    CẢNH BÁO    Nhãn NGẮN cạnh số BH (`§36`), thay cho những đoạn văn dài
                trong lòng bảng. Chúng ánh xạ từ trạng thái ĐÃ CÓ của hệ
                thống — không mã nào ở đây được phát minh ra một cảnh báo mới.
    LỖ / ÂM     MỘT trạng thái đỏ cho cả "giá nhập cao hơn giá bán" và "lợi
                nhuận âm" (`§35`). Hai câu đó mô tả cùng một vấn đề vận hành,
                nên chúng cho ra một dấu hiệu, không phải hai.

## Nền xen kẽ theo NGÀY, không theo dòng

`§38`: hai mươi dòng cùng ngày 01/09 dùng CÙNG một nền; ngày kế tiếp đổi nền.
Đây không phải trang trí — nó là thứ cho phép Owner nhìn một bảng dài và thấy
ranh giới ngày mà không phải đọc cột Ngày. Xen kẽ theo dòng (kiểu zebra thông
thường) phá đúng thông tin đó.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional

from app.modules.reporting import business_metrics as bm
from app.modules.reporting import profit_gate, reporting_sheets
from app.web import business_store, line_identity
from app.web.analytics_presentation import UNKNOWN_EMPLOYEE, count
from app.web.business_presentation import (
    MOM_NO_PREVIOUS, STATE_LABELS, _decimal, _derived_cell, _thousand_vnd,
    business_date, coverage_cell, gated_cell, month_over_month, percent,
    period_label, price_pair, sheet_display_order,
)
from app.web.legacy_presentation import format_number

# --- Cột của bảng kê trong không gian làm việc ----------------------------
#
# `§25`: "Giá nhập KPI" đổi tên thành "Giá nhập" và đứng TRƯỚC "Giá bán";
# "Nguồn giá" biến mất khỏi màn hình. Provenance KHÔNG bị xoá khỏi hệ thống —
# nó vẫn được lưu, vẫn quyết định `MANUAL` vs `MANUAL_OVERRIDE`, và vẫn hiện
# ở bảng kê chi tiết của PHB-03. Chỉ cột trong báo cáo vận hành là bỏ đi
# (`§25`: *"Only remove the visible column"*).
#
# `§26`: không có cột "Sửa" và không có thao tác "Gán NV bán hàng" riêng —
# mỗi BH có ĐÚNG MỘT nút sửa (`§27`).
#: `TASK-OWNER-UIUX-004` §5 — Khách hàng dời ra SAU DS quy đổi (chủ dự án
#: yêu cầu trực tiếp): cụm cột nghiệp vụ của dòng hàng (Mặt hàng…DS quy đổi)
#: đọc liền mạch trước, thông tin khách hàng đọc SAU cùng, ngay trước cột
#: thao tác — thay vì chen giữa Mã đơn và Mặt hàng như trước.
#: `TASK-OWNER-UIUX-008` §2 — "Khách hàng" tách thành HAI cột bằng nhau
#: (chủ dự án yêu cầu trực tiếp): tên riêng, liên hệ (SĐT · địa chỉ)
#: riêng — trước đây là hai DÒNG chồng trong CÙNG một ô.
#: R5 §5 — hai cột `Hãng` và `IMEI` chen vào NGAY SAU `Mặt hàng`, và
#: `Mặt hàng` thu hẹp lại: khi một dòng đã phân loại, tên hiển thị là model
#: canonical ngắn ("K-65S20M2") chứ không còn cả câu tên hàng trên sổ.
#:
#: Các cột này MẶC ĐỊNH ẨN và dùng chung một nút mở/đóng — chúng là thông tin
#: đối chiếu, không phải thông tin vận hành hằng ngày, và bắt cả bảng hẹp lại
#: vì mấy cột ít dùng là đánh đổi sai. Trạng thái mở/đóng nằm ở trình duyệt
#: (`localStorage`), nên nó không đi qua server và không thành một thiết lập
#: cần lưu ở đâu cả.
#: R5.1 §5 — "Nhóm hàng" đứng CẠNH "Hãng", dưới cùng một nút ẩn/hiện. Nó là
#: thông tin đối chiếu cùng loại: do Tracking khẳng định, chỉ để đọc, và
#: không có đường sửa nào từ màn hình này.
SHEET_DETAIL_COLUMNS: tuple[str, ...] = (
    "Ngày", "Mã đơn", "Mặt hàng", "Nhóm hàng", "Hãng", "IMEI", "Nhân viên",
    "SL", "Giá nhập", "Giá bán", "Lợi nhuận", "DS quy đổi", "Khách hàng",
    "Liên hệ",
)

#: Các cột ẩn/hiện chung một nút, theo VỊ TRÍ (0-based) trong bảng trên.
OPTIONAL_COLUMN_INDEXES: tuple[int, ...] = (3, 4, 5)

SHOW_OPTIONAL_LABEL = "HIỆN NHÓM HÀNG, HÃNG & IMEI"
HIDE_OPTIONAL_LABEL = "ẨN NHÓM HÀNG, HÃNG & IMEI"

OPTIONAL_COLUMNS_NOTE = (
    "Nhóm hàng, hãng và mã máy (IMEI) chỉ hiện trên trang này. Chúng không đi "
    "vào bất kỳ trang chỉ tiêu, bản xuất hay bản ghi nhật ký nào."
)

# --- Nhãn ngắn của cảnh báo (`§36`) ---------------------------------------
#
# Mỗi nhãn ánh xạ từ MỘT trạng thái đã tồn tại của hệ thống. `§36` cấm phát
# minh nhãn mới: một cái tag không có trạng thái tương ứng phía sau là một
# lời khẳng định mà không gì kiểm chứng được.
SHORT_TAGS = {
    profit_gate.BLOCK_PURCHASE_PRICE_MISSING: "Thiếu giá",
    profit_gate.WARN_POSSIBLE_DUPLICATE: "Trùng khóa",
    profit_gate.WARN_PIPELINE_REVIEW: "Bất thường",
    profit_gate.BLOCK_EMPLOYEE_UNRESOLVED: "Chưa rõ NV",
    profit_gate.BLOCK_SELL_PRICE_MISSING: "Thiếu giá bán",
    profit_gate.BLOCK_QUANTITY_MISSING: "Thiếu SL",
    profit_gate.BLOCK_QUANTITY_ZERO: "SL bằng 0",
    profit_gate.BLOCK_QUANTITY_NEGATIVE: "SL âm",
    profit_gate.BLOCK_KPI_AUTHORITY_UNAVAILABLE: "Cấu hình hỏng",
}

# `TASK-OWNER-UIUX-007` — chủ dự án chỉ định trực tiếp bốn màu chấm cạnh số
# BH (thay pill chữ trước đây): VÀNG = thiếu giá, ĐỎ = bất thường (gồm nghi
# trùng — cùng nhóm "vấn đề vận hành cần Owner xem"), ĐEN = mọi cảnh báo
# BLOCK còn lại (thiếu SL/thiếu giá bán/chưa rõ NV/cấu hình hỏng — Owner
# chọn "tất cả các mã còn lại dùng màu đen" khi được hỏi lại). "Chưa phân
# loại" (`line_identity`, xanh) map riêng ở nơi dựng `identity_tags`.
TAG_COLORS = {
    profit_gate.BLOCK_PURCHASE_PRICE_MISSING: "yellow",
    profit_gate.WARN_PIPELINE_REVIEW: "red",
    profit_gate.WARN_POSSIBLE_DUPLICATE: "black",
    profit_gate.BLOCK_EMPLOYEE_UNRESOLVED: "black",
    profit_gate.BLOCK_SELL_PRICE_MISSING: "black",
    profit_gate.BLOCK_QUANTITY_MISSING: "black",
    profit_gate.BLOCK_QUANTITY_ZERO: "black",
    profit_gate.BLOCK_QUANTITY_NEGATIVE: "black",
    profit_gate.BLOCK_KPI_AUTHORITY_UNAVAILABLE: "black",
}

# Hai mã KHÔNG có nhãn ngắn, và cả hai đều cố ý:
#
#   WARN_PURCHASE_ABOVE_SELL / WARN_NEGATIVE_PROFIT — `§35` nói rõ chúng là
#   CÙNG một vấn đề vận hành và phải cho ra MỘT dấu hiệu. Dấu hiệu đó là màu
#   ĐỎ trên chính dòng, không phải hai cái tag cạnh nhau nói hai lần.
#
#   WARN_SELL_PRICE_ZERO — hàng tặng kèm là chuyện bình thường của sổ này;
#   nó không phải một việc Owner phải làm gì.
LOSS_CODES = frozenset({
    profit_gate.WARN_PURCHASE_ABOVE_SELL, profit_gate.WARN_NEGATIVE_PROFIT,
})

TARGET_UNIT_LABEL = "TARGET (NGHÌN ĐỒNG)"

# `§18` — đơn vị phải hiện ngay tại ô nhập, không chỉ trong một câu giải
# thích. Người ta gõ vào ô, không gõ vào đoạn văn.
TARGET_KVND_NOTE = (
    "Nhập theo NGHÌN ĐỒNG: gõ 500,000 nghĩa là 500.000.000 đồng. Để trống rồi "
    "LƯU là gỡ target; gõ 0 là đặt target bằng không."
)
TARGET_NOT_KVND_NOTE = (
    "Target này không phải bội số của 1.000 đồng nên không viết được theo "
    "nghìn đồng. Sửa nó ở màn hình Target theo đồng."
)

PROGRESS_NOTE = (
    "Tiến độ là phần trăm thời gian đã trôi qua của tháng đang xem — một chỉ "
    "báo lịch. Nó KHÔNG tham gia Target, KPI hay bất kỳ con số kinh doanh nào."
)

EMPTY_PERIOD_NOTE = "Chưa có đơn"

EXCLUDED_NOTE = (
    "Những dòng dưới đây đã được loại khỏi báo cáo: chúng không còn góp vào "
    "doanh thu, lợi nhuận hay DS quy đổi của bất kỳ sheet nào. Bản ghi kế "
    "toán gốc KHÔNG bị xoá — bấm KHÔI PHỤC là dòng trở lại đúng chỗ cũ."
)

# R5 §1 — câu chữ của danh sách "Không còn trong file đầy đủ". Viết bằng
# NGÔN NGỮ HÀNH ĐỘNG: nó phải trả lời được hai câu người dùng thật sự hỏi khi
# nhìn thấy một cái tên đơn biến mất khỏi báo cáo — "vì sao nó rơi ra" và
# "tôi phải làm gì để nó quay lại". Câu cũ ("ứng viên đã xoá khỏi nguồn, đưa
# vào Review") trả lời cả hai bằng từ vựng của hệ thống, không của kế toán.
REMOVED_IN_SOURCE_NOTE = (
    "Những dòng dưới đây KHÔNG còn trong sổ mà bạn đã xác nhận là đầy đủ cho "
    "khoảng ngày của chúng, nên chúng đã được TẠM LOẠI: không góp vào doanh "
    "thu, lợi nhuận, DS quy đổi, Target hay file Excel của bất kỳ sheet nào. "
    "Lịch sử KHÔNG bị xoá — nạp lại một sổ có chứa dòng đó là cảnh báo tự mất "
    "và các con số tự khôi phục."
)

GIA_DUNG_CONFIRM_QUESTION = "Chuyển dòng này sang Gia dụng?"
GIA_DUNG_CONFIRM_POINTS = (
    "Gỡ khỏi Nội thành",
    "Tính sang Gia dụng",
    "Giữ nguyên nhân viên bán",
)
EXCLUDE_CONFIRM_QUESTION = "Loại dòng này khỏi báo cáo?"
EXCLUDE_CONFIRM_POINTS = (
    "Không còn tính vào doanh thu",
    "Không còn tính vào lợi nhuận",
    "Sổ kế toán gốc giữ nguyên",
)


# `§24` — mọi ngày nghiệp vụ của màn hình này viết `DD/MM/YYYY`. Hàm
# `business_date` nay sống ở `business_presentation` (TASK-UIUX-001) để bảng
# kê chi tiết của PHB-03 viết ngày y hệt; tên vẫn được xuất từ đây.


def sheet_tabs(
    sheets: list, selected_key: Optional[str]
) -> list[dict]:
    """Thanh tab kiểu bảng tính, đặt TRÊN báo cáo (`§4`).

    Đây là các KHUNG NHÌN CON của một trang, không phải điều hướng cấp một:
    thanh `R1` bốn mục (Báo cáo · Nhân viên · Doanh số ngày · Dữ liệu) không
    bị đụng tới, và `§4` nói rõ điều đó.

    `TASK-OWNER-UIUX-003` §4 — thứ tự các tab nay khớp ĐÚNG thứ tự hàng của
    bảng "Theo nhân viên" trên trang Báo cáo (`sheet_display_order`): nhân
    viên theo thứ tự master trước, rồi "chưa xác định", Nội thành, Gia dụng
    cuối cùng. Trước bản sửa, `sheets` (từ `reporting_sheets.sheets_for`)
    đặt hai sheet NHÓM lên đầu — đúng cho URL bookmark cũ nhưng khác thứ tự
    Owner đã quen đọc ở trang kia.
    """
    return [
        {"key": sheet.key, "label": sheet.label or UNKNOWN_EMPLOYEE,
         "selected": sheet.key == selected_key,
         "group": sheet.is_group}
        for sheet in sorted(sheets, key=sheet_display_order)
    ]


def target_cell(target: Optional[Decimal]) -> dict:
    """Ô Target của sheet — giá trị đã lưu, viết theo hai đơn vị.

    `text_kvnd` là con số Owner đọc; `text` là VND đầy đủ và luôn đi kèm qua
    tooltip. Kho lưu vẫn là VND (PHB-05 §7) — không có gì ở đây đổi điều đó,
    và `input_value` là bằng chứng: nó luôn khứ hồi qua
    `business_store.parse_target_kvnd` về đúng `target` ban đầu (`§20`).
    """
    return {
        "unset": target is None,
        "text": _decimal(target),
        "text_kvnd": _thousand_vnd(target),
        "input_value": business_store.format_target_kvnd(target),
        "kvnd_editable": business_store.target_is_kvnd_editable(target),
    }


def vs_target_cell(totals: bm.BusinessTotals, target: Optional[Decimal]) -> dict:
    """"So Target" của sheet — `DS quy đổi / Target × 100` (`§21`).

    Dùng NGUYÊN công thức và nguyên trạng thái của PHB-05: mẫu số là DS quy
    đổi (không phải Tổng bán), không cap ở 100 %, và ô này thừa hưởng đúng
    nhãn CHÍNH THỨC / CHƯA HOÀN CHỈNH của con số DS quy đổi mà nó chia — không
    có hệ trạng thái thứ hai.
    """
    converted = totals.converted_sales
    value = bm.vs_target_percent(converted, target)
    reason = bm.vs_target_reason(converted, target)
    official = totals.coverage.is_complete
    return {
        "text": percent(value),
        "missing": value is None,
        "reason_code": reason or "",
        "official": official,
        "state_label": STATE_LABELS[
            bm.STATE_OFFICIAL if official else bm.STATE_INCOMPLETE],
    }


def progress_cell(period: tuple[int, int], *, today: date) -> dict:
    """Ô "Tiến độ" (`§15`) — chỉ báo LỊCH, không phải một chỉ tiêu kinh doanh."""
    value = reporting_sheets.month_progress_percent(period, today=today)
    return {"text": percent(value), "value": value, "note": PROGRESS_NOTE}


def summary_strip(
    totals: bm.BusinessTotals, *, period: tuple[int, int],
    previous_totals: Optional[bm.BusinessTotals], target: Optional[Decimal],
    today: date,
) -> dict:
    """`§14` — DÒNG THÔNG TIN ĐẦU TIÊN của một sheet, năm ô, không gấp khúc.

    Ngay bên dưới nó là bảng chi tiết; `§14` cấm chèn thêm một bước bung/thu
    nào ở giữa. Owner mở sheet ra là thấy cả hai.

    "So tháng trước" so ĐÚNG sheet này với CHÍNH nó ở tháng liền trước
    (`§16`): tầng ráp đã cắt `previous_totals` theo cùng khoá sheet trước khi
    gọi vào đây. Không có đường nào ở màn hình này mượn tổng tháng của cả
    công ty từ sổ cũ — tổng đó là số của công ty, và dùng nó làm mẫu số cho
    một nhóm là một phép so sai (cùng lý do đã nghiệm thu ở `DEC-181` §16).
    """
    return {
        "sales_revenue": _decimal(totals.sales_revenue),
        "sales_revenue_kvnd": _thousand_vnd(totals.sales_revenue),
        "converted_sales": gated_cell(
            totals.converted_sales, totals.official_converted_sales,
            totals.state),
        "vs_target": vs_target_cell(totals, target),
        "mom": month_over_month(
            totals.sales_revenue,
            None if previous_totals is None else previous_totals.sales_revenue,
            has_period=True,
            previous_has_lines=(
                previous_totals is not None and previous_totals.lines > 0)),
        "progress": progress_cell(period, today=today),
        "previous_label": period_label(
            (period[0] - 1, 12) if period[1] == 1 else (period[0], period[1] - 1)),
    }


def _short_tags(line: bm.BusinessLine) -> list[dict]:
    """Nhãn ngắn của MỘT dòng, khử trùng lặp và giữ thứ tự (`§36`)."""
    seen: dict[str, str] = {}
    for code in (*line.profit_blockers, *line.warnings):
        label = SHORT_TAGS.get(code)
        if label is not None:
            seen.setdefault(code, label)
    return [{"code": code, "label": label, "color": TAG_COLORS.get(code, "black")}
            for code, label in seen.items()]


def _is_loss(line: bm.BusinessLine) -> bool:
    """`§35` — dòng đang bán lỗ hoặc lợi nhuận âm, MỘT trạng thái duy nhất."""
    return bool(LOSS_CODES.intersection(line.warnings))


def _catalog_field(identity, catalog, field: str) -> Optional[str]:
    """Một trường HIỂN THỊ của danh mục Tracking cho dòng này, hoặc `None`.

    `catalog` là `{raw_identity_key: {"tracking_code", "model_label",
    "brand", "category_label"}}` — bản chiếu mà tầng route đã dựng từ log
    quyết định đã CONFIRMED cộng với bản chiếu hiển thị của Tracking.

    Chỉ dòng `MATCHED_TRACKING` mới được tra. Một dòng chưa phân loại chưa có
    mã Tracking nào; một dòng đang tranh chấp thì có hai; một dòng ngoài bảng
    giá thì cố ý không có. Cả ba phải giữ TÊN THÔ để người dùng còn biết mình
    cần xử lý gì (`§8`).

    R5.1 §5.4 treo lên đúng cổng này: một dòng tranh chấp hay có target đã cũ
    KHÔNG được nhận nhóm hàng của một candidate, và nó không nhận được vì nó
    không đi qua được dòng `classification` ngay dưới — cùng một phép chặn đã
    giữ `brand`, không phải một phép chặn thứ hai viết riêng cho nhóm hàng.
    """
    if not catalog or identity is None:
        return None
    if identity.classification != line_identity.CLASS_MATCHED_TRACKING:
        return None
    return (catalog.get(identity.identity_key) or {}).get(field)


def _product_display(detail: dict, identity, catalog) -> str:
    """Tên hàng như màn hình hiện nó (R5 §5).

        đã xác nhận + danh mục có model  ⟹  model canonical ("K-65S20M2")
        đã xác nhận, danh mục chưa nói   ⟹  mã Tracking
        chưa xác nhận / tranh chấp / ngoài bảng giá ⟹ TÊN THÔ

    Nhánh cuối là nhánh quan trọng nhất, và nó cố ý không "gọn gàng" hơn: tên
    thô là thứ duy nhất cho người dùng biết dòng này chưa được xử lý. Thay nó
    bằng một cái nhãn đẹp sẽ làm một việc còn treo trông như đã xong.
    """
    label = _catalog_field(identity, catalog, "model_label")
    if label:
        return label
    code = _catalog_field(identity, catalog, "tracking_code")
    if code:
        return code
    return detail["product_raw"] or "—"


def _product_title(detail: dict, shown: str, *, synthetic: bool) -> Optional[str]:
    """Tooltip của ô `Mặt hàng`: TÊN TRÊN SỔ, khi màn hình đang hiện tên khác.

    `R5.3` §UI — ba cột đối chiếu phải đọc đủ được, và ô này là ô duy nhất
    trong ba ô mà nội dung hiển thị có thể KHÁC nội dung nguồn: khi một dòng
    đã xác nhận mã, `_product_display` thay tên dài trên sổ kế toán bằng model
    canonical của Tracking. Đó là việc đúng (`R5` §5) nhưng nó lấy đi thứ
    Owner dùng để đối chiếu với đơn thật, nên tên gốc phải còn đọc được ở đâu
    đó — và `title` là chỗ không tốn một pixel nào của bảng kê.

    `None` khi không có gì để nói thêm: dòng suy ra (chiết khấu), hoặc màn
    hình đang hiện CHÍNH tên trên sổ. Một tooltip lặp lại đúng chữ đang hiện
    là một tooltip dạy người đọc bỏ qua mọi tooltip khác.
    """
    if synthetic:
        return None
    raw = (detail.get("product_raw") or "").strip()
    return raw if raw and raw != shown else None


def _line_row(detail: dict, *, sheet, part, synthetic: bool,
              confirmed_keys=None, decisions=None,
              catalog=None, imeis=None) -> dict:
    line = detail["line"]
    # `DEC-185` §PI-01/§PI-02 — trạng thái nhận diện của DÒNG THẬT.
    #
    # Dòng "Chiết khấu" là số suy ra từ sổ, không phải một mặt hàng, nên nó
    # không có trạng thái nhận diện nào và không được mời Owner phân loại.
    identity = (None if synthetic
                else line_identity.state_of(
                    detail, confirmed_keys=confirmed_keys, decisions=decisions))
    shown_product = (bm.DISCOUNT_DISPLAY_LABEL if synthetic
                     else _product_display(detail, identity, catalog))
    return {
        "kind": part.kind,
        "synthetic": synthetic,
        "order_key": detail["order_key"],
        "product_key": detail["product_key"],
        "occurrence_index": detail["occurrence_index"],
        "product_raw": shown_product,
        # `R5.3` §UI — tên TRÊN SỔ, để đọc đủ qua tooltip khi ô đang hiện
        # model canonical thay cho nó. Xem `_product_title`.
        "product_title": _product_title(detail, shown_product,
                                        synthetic=synthetic),
        # R5 §5 + R5.1 §5 — ba cột đối chiếu. `None` ⟹ ô hiện dấu gạch: một
        # dòng chưa phân loại không có hãng và không có nhóm hàng, và một dòng
        # sổ không ghi mã máy thì không có mã máy. Không nhánh nào đoán bù —
        # đặc biệt KHÔNG đọc `product_raw` để suy nhóm hàng khi metadata
        # thiếu (`ADR-111` §3, `R5.1` §5.9).
        "brand": (None if synthetic
                  else _catalog_field(identity, catalog, "brand")),
        # R5.1 §5.6 — nhóm hàng đi CÙNG dòng ở tầng read model, để R6 dựng
        # được các phép gộp theo nhóm mà không phải mở lại đường đọc danh mục.
        "category_label": (None if synthetic
                           else _catalog_field(identity, catalog,
                                               "category_label")),
        "imei": (None if synthetic or imeis is None
                 else imeis.get((detail["order_key"], detail["product_key"],
                                 detail["occurrence_index"]))),
        "employee": line.employee or UNKNOWN_EMPLOYEE,
        "employee_resolved": line.employee_resolved,
        "quantity": _decimal(part.quantity),
        # `§25` — "Giá nhập", đứng TRƯỚC "Giá bán".
        **price_pair(part.purchase_price, "purchase_price"),
        # Ô NHẬP giữ VND ĐẦY ĐỦ — `business_presentation.PRICE_INPUT_NOTE`.
        "purchase_price_input": (
            "" if line.purchase_price is None
            else format_number(line.purchase_price)),
        **price_pair(part.sell_price, "sell_price"),
        "kpi_profit": _derived_cell(part.kpi_profit,
                                    () if synthetic else line.profit_blockers),
        "converted_sales": _derived_cell(part.converted_sales,
                                         () if synthetic else line.profit_blockers),
        "loss": (not synthetic) and _is_loss(line),
        "tags": [] if synthetic else _short_tags(line),
        # Thao tác phân loại Gia dụng CHỈ có trên sheet Nội thành (`§9`), và
        # KHÔNG BAO GIỜ trên dòng "Chiết khấu" — dòng đó là số suy ra từ sổ,
        # không phải một dòng hàng để phân loại.
        "can_classify": (not synthetic) and sheet.accepts_gia_dung_classification,
        # Gỡ phân loại chỉ mở với dòng có quyết định RIÊNG của chính nó: một
        # dòng đang ở Gia dụng vì quyết định cấp MẶT HÀNG phải gỡ ở màn hình
        # phân loại mặt hàng, nếu không Owner sẽ tưởng đã gỡ mà mọi lần bán
        # khác của mặt hàng đó vẫn nguyên.
        "line_classified": detail.get("line_product_group") is not None,
        "can_exclude": not synthetic,
        # `§PI-03` — hai trạng thái KHÁC NHAU, hai nhãn khác nhau, và tầng
        # trình bày không được gộp lại. `identity_label` là `None` khi dòng
        # bình thường: ô mã hàng khi đó hiện đúng tên hàng, không thêm gì.
        "identity_state": None if identity is None else identity.state,
        # R2 §4.1 — trạng thái NGHIỆP VỤ (bốn giá trị), tách khỏi trạng thái
        # TRÌNH BÀY ở ngay trên (ba giá trị). Xem `line_identity`.
        "identity_classification": (
            None if identity is None else identity.classification),
        "identity_label": None if identity is None else identity.label,
        "identity_title": None if identity is None else identity.title,
        "identity_key": None if identity is None else identity.identity_key,
        # `§PI-04` — chỉ dòng CHƯA nhận diện và CÓ khoá định danh mới mở được
        # luồng phân loại. Dòng thiếu hẳn tên hàng vẫn hiện "Chưa phân loại"
        # (đó là sự thật) nhưng không có nút — xem `UNCLASSIFIABLE_NOTE`.
        "can_identify": bool(identity is not None and identity.classifiable),
        "identity_blocked": bool(
            identity is not None and identity.unresolved
            and identity.identity_key is None),
        # R2 §4.3 — "không có trên bảng giá" mở được cho mọi dòng CHƯA phân
        # loại xong và có khoá định danh. Nó KHÔNG cần danh mục Tracking: đây
        # chính là câu trả lời cho trường hợp danh mục không chứa mặt hàng ấy.
        "can_mark_out_of_catalog": bool(
            identity is not None
            and identity.identity_key is not None
            and identity.classification in (
                line_identity.CLASS_NEEDS_REVIEW, line_identity.CLASS_CONFLICT)),
        # §4.3 — "Nối lại Tracking" chỉ có nghĩa với một dòng ĐANG ngoài bảng
        # giá. Trên dòng khác nó sẽ là một nút mời ghi đè một quyết định mà
        # không ai hỏi Owner có muốn không.
        "can_relink_tracking": bool(
            identity is not None
            and identity.identity_key is not None
            and identity.out_of_catalog),
    }


#: Không có ngày nào đã thấy. Một sentinel dùng chung — xem `sheet_detail_groups`.
_NO_DATE_YET = object()


def group_shades(details: list[dict]) -> dict[str, int]:
    """`{order_key: shade}` theo ĐÚNG thứ tự hiển thị của bảng kê.

    Nền xen kẽ tính theo NGÀY (`§38`, `§59`): mọi BH cùng một ngày dùng chung
    một nền, ngày kế tiếp đổi nền. Đó là một tính chất của CẢ SHEET — nền của
    một BH phụ thuộc vào ngày của BH đứng trước nó — chứ không của riêng nó.

    Hàm này được TÁCH RA khỏi `sheet_detail_groups` vì `UI-03` (ghi tại chỗ)
    và `UI-04` (tải thêm trang) dựng lại MỘT PHẦN của bảng: tính lại nền trên
    một lát sẽ cho BH đầu lát nền `0` và cả phần vừa dựng lệch nhịp so với
    phần đã nằm trên màn hình. `sheet_detail_groups` gọi CHÍNH hàm này, nên
    chỉ tồn tại MỘT luật xen kẽ, không phải hai bản chép nhau.

    Thứ tự khoá trả về LÀ thứ tự hiển thị (dict giữ thứ tự chèn), nên phân
    trang đọc ranh giới BH từ đây thay vì tự sắp xếp lại một lần nữa.
    """
    first_date: dict[str, object] = {}
    for detail in details:
        first_date.setdefault(detail["order_key"], detail["sale_date"])
    ordered_keys = sorted(
        first_date,
        key=lambda key: (first_date[key] is None, first_date[key], key))
    # `_NO_DATE_YET` là một sentinel DÙNG CHUNG, không phải một `object()`
    # dựng mới ở mỗi vòng: `x is not object()` luôn đúng (mỗi lời gọi tạo một
    # đối tượng khác), nên viết như vậy sẽ đảo nền ngay ở nhóm ngày ĐẦU TIÊN
    # và cả bảng lệch một nhịp.
    shades: dict[str, int] = {}
    shade, previous_date = 0, _NO_DATE_YET
    for key in ordered_keys:
        if first_date[key] != previous_date:
            if previous_date is not _NO_DATE_YET:
                shade = 1 - shade
            previous_date = first_date[key]
        shades[key] = shade
    return shades


def sheet_detail_groups(details: list[dict], *, sheet,
                        confirmed_keys=None, decisions=None,
                        catalog=None, imeis=None,
                        shades=None) -> list[dict]:
    """Bảng kê của một sheet, GỘP THEO BH và tô nền theo NGÀY (`§22`, `§38`).

    Cấu trúc phản chiếu chính sổ kế toán: một BH là một KHỐI, khách hàng thuộc
    về khối đó, và các dòng hàng nằm bên trong. `§22` nói rõ vì sao — biến mỗi
    dòng thành một thẻ rời làm mất quan hệ "ba dòng này là một đơn".

    Nền xen kẽ tính theo NGÀY, không theo dòng và cũng không theo BH: mọi BH
    của cùng một ngày dùng chung một nền, và ngày kế tiếp đổi nền (`§38`,
    `§59`). Nhờ vậy Owner đọc được ranh giới ngày mà không phải dò cột Ngày.

    Dòng "Chiết khấu" của `DEC-180` đi theo đúng dòng cha của nó và giữ nguyên
    ngữ nghĩa đã nghiệm thu: không ô nhập, không tag, không thao tác nào.
    """
    groups: dict[str, dict] = {}
    for detail in details:
        order_key = detail["order_key"]
        line = detail["line"]
        group = groups.get(order_key)
        if group is None:
            group = groups[order_key] = {
                "order_key": order_key,
                "sale_date": detail["sale_date"],
                "date_text": business_date(detail["sale_date"]),
                # `§23` — khách hàng thuộc về ĐƠN, không về từng dòng hàng.
                "customer_name": detail.get("customer_name") or "—",
                "customer_phone": detail.get("customer_phone") or "—",
                "customer_address": detail.get("customer_address") or "—",
                "rows": [],
                "tags": [],
                "identity_tags": [],
                "loss": False,
                # Nhân viên ở cấp BH (`§27`): đổi một lần là cả đơn đổi theo.
                # Khi các dòng của một BH đang thuộc nhiều người khác nhau, ô
                # chọn để TRỐNG thay vì tự chọn hộ một người — gợi ý sai ở đây
                # là dời KPI của người khác chỉ vì Owner bấm LƯU.
                "employees": [],
            }
        product, *discount_parts = bm.display_contributions(line)
        new_rows = [_line_row(detail, sheet=sheet, part=product, synthetic=False,
                              confirmed_keys=confirmed_keys, decisions=decisions,
                              catalog=catalog, imeis=imeis)]
        for part in discount_parts:
            new_rows.append(_line_row(detail, sheet=sheet, part=part, synthetic=True,
                                      confirmed_keys=confirmed_keys,
                                      decisions=decisions,
                                      catalog=catalog, imeis=imeis))
        group["rows"].extend(new_rows)
        if line.employee and line.employee not in group["employees"]:
            group["employees"].append(line.employee)
        for tag in _short_tags(line):
            if tag["code"] not in {item["code"] for item in group["tags"]}:
                group["tags"].append(tag)
        # `TASK-OWNER-UIUX-004` §5 — "Thiếu giá"/"Chưa phân loại" dồn về ô Mã
        # đơn (chủ dự án yêu cầu trực tiếp), thay vì đứng cạnh tên hàng ở ô
        # Mặt hàng của TỪNG dòng — Mặt hàng vì thế đọc được trên một dòng,
        # không phải xuống hàng vì một cái tag. Gộp DUY NHẤT một tag cho mỗi
        # NHÃN khác nhau (không phải mỗi dòng): một BH ba dòng cùng "Chưa
        # phân loại" chỉ cần nói một lần, đúng cách `group["tags"]` ở trên
        # đã làm cho `SHORT_TAGS`. Bấm vào tag vẫn mở đúng dòng ĐẦU TIÊN
        # mang trạng thái đó (`§PI-04`) — không mất khả năng phân loại tại
        # chỗ, chỉ đổi CHỖ ĐỨNG của lối vào.
        #
        # `LABEL_MISSING_PRICE` ("Thiếu giá") trùng CHỮ với
        # `SHORT_TAGS[BLOCK_PURCHASE_PRICE_MISSING]` — cùng sự thật, hai
        # module tính (`line_identity`, bộ test PI-01…PI-12 bảo vệ, và
        # `profit_gate`) khác nhau. `identity-label` VẪN phải render đủ —
        # PI-02/PI-03 đọc đúng `data-metric` này bất kể `bh-tag` có nói gì —
        # nên KHÔNG được bỏ qua nó; chỉ đánh dấu `duplicate_text` để
        # template ẩn viền pill trùng chữ khỏi mắt Owner (`aria-hidden`,
        # `sr-only` — vẫn ở trong DOM cho test và trình đọc màn hình), tránh
        # "THIẾU GIÁ · THIẾU GIÁ" hai lần liền nhau khi cả hai cùng đúng.
        existing_identity_labels = {item["label"] for item in group["identity_tags"]}
        short_tag_labels = {item["label"] for item in group["tags"]}
        for row in new_rows:
            label = row.get("identity_label")
            if label and label not in existing_identity_labels:
                existing_identity_labels.add(label)
                group["identity_tags"].append({
                    "label": label,
                    "title": row.get("identity_title"),
                    "can_identify": row.get("can_identify"),
                    # R2 §4.3 — nhãn "Ngoài bảng giá" cũng phải là một cửa:
                    # xem chú thích trong `kinh_doanh_nhan_vien.html`.
                    "can_relink": row.get("can_relink_tracking"),
                    "order_key": row["order_key"],
                    "product_key": row["product_key"],
                    "occurrence_index": row["occurrence_index"],
                    "duplicate_text": label in short_tag_labels,
                    # `TASK-OWNER-UIUX-007` — CHỈ hai nhãn có thể ra từ
                    # `line_identity` (`LABEL_UNRESOLVED`/`LABEL_MISSING_
                    # PRICE`); xanh cho "Chưa phân loại", còn lại ("Thiếu
                    # giá") dùng ĐÚNG màu vàng của `TAG_COLORS` — cùng một
                    # sự thật với `bh-tag`, không có màu thứ ba.
                    # R2 thêm hai nhãn (`Ngoài bảng giá`, `Xung đột mã`).
                    # Xanh = "cần Owner phân loại"; vàng = "đã phân loại, còn
                    # thiếu giá". `Xung đột mã` là việc phân loại chưa xong nên
                    # nó xanh; `Ngoài bảng giá` đã xong nên nó vàng — cùng một
                    # quy ước màu, không có màu thứ ba.
                    "color": (
                        "green" if label in (line_identity.LABEL_UNRESOLVED,
                                             line_identity.LABEL_CONFLICT)
                        else "yellow"),
                })
        group["loss"] = group["loss"] or _is_loss(line)
        # `§PI-11` — BH này có dòng chưa phân loại nào không. Cờ ở cấp BH chứ
        # không cấp dòng vì cảnh báo đầu sheet đếm BH, và cái nó cuộn tới cũng
        # là một khối BH.
        group["unresolved_identity"] = group.get("unresolved_identity", False) or any(
            row.get("identity_classification") == line_identity.CLASS_NEEDS_REVIEW
            for row in group["rows"])

    # Nền xen kẽ: `shades` được TRUYỀN VÀO khi người gọi chỉ dựng một LÁT của
    # sheet (`UI-03`/`UI-04`) — nó phải là bảng nền của CẢ sheet, nếu không
    # lát vừa dựng sẽ lệch nhịp với phần đang nằm trên màn hình. Không truyền
    # ⟹ `details` chính là cả sheet, và hàm tự tính bằng ĐÚNG hàm đó.
    shade_index = group_shades(details) if shades is None else shades
    ordered = sorted(
        groups.values(),
        key=lambda item: (item["sale_date"] is None, item["sale_date"],
                          item["order_key"]))
    for group in ordered:
        group["shade"] = shade_index.get(group["order_key"], 0)
        group["employee_value"] = (
            group["employees"][0] if len(group["employees"]) == 1 else "")
        group["lines"] = len(group["rows"])
    return ordered


#: `UI-04` — số DÒNG của một trang bảng kê. Đây là kích thước của một lần
#: TẢI, không phải ngân sách DOM: ngân sách DOM (`~200–300` hàng) được giữ ở
#: client bằng cách GỠ các nhóm cũ nhất, và nó là một con số khác, lớn hơn.
#:
#: 100 chứ không phải "cả sheet": trên fixture 5.000 dòng, dựng cả bảng kê
#: trả ~15 MB HTML và hơn 5.000 hàng `<tr>` cho một màn hình cao chừng bốn
#: mươi hàng (`scripts/stab01_baseline.py`).
WORKSPACE_PAGE_LINES = 100

#: Trần cứng cho `limit` mà client gửi lên. Không có nó, một `limit=999999`
#: biến route phân trang trở lại thành đúng cái nó tồn tại để thay thế.
WORKSPACE_PAGE_LINES_MAX = 500


def page_of_groups(details: list[dict], *, cursor: Optional[str] = None,
                   limit: int = WORKSPACE_PAGE_LINES) -> dict:
    """MỘT trang của bảng kê, cắt theo RANH GIỚI BH.

    Trả về::

        {"details": [...],        # các dòng thuộc trang này, đúng thứ tự gốc
         "order_keys": [...],     # mã BH của trang, đúng thứ tự hiển thị
         "shades": {...},         # nền của CẢ sheet (xem `group_shades`)
         "cursor": str|None,      # con trỏ ĐÃ DÙNG để lấy trang này
         "next_cursor": str|None, # con trỏ của trang kế, `None` khi hết
         "total_orders": int, "total_lines": int}

    ## Vì sao cắt theo BH chứ không theo dòng

    Một BH là MỘT khối trên màn hình: khách hàng, ngày và mã đơn trải xuống
    (`rowspan`) qua mọi dòng hàng của nó. Cắt giữa hai dòng của cùng một BH
    sẽ để lại nửa khối mang `rowspan` trỏ vào những hàng không có mặt, và
    người đọc mất đúng quan hệ "ba dòng này là một đơn" mà `§22` dựng cả cấu
    trúc bảng để giữ. Nên `limit` là một NGƯỠNG, không phải một con số chính
    xác: trang dừng ở BH đầu tiên khiến tổng số dòng CHẠM hoặc VƯỢT ngưỡng, và
    một BH lớn hơn cả ngưỡng vẫn đi trọn trong một trang.

    ## Con trỏ là mã BH, không phải chỉ số

    `cursor` = mã của BH ĐẦU TIÊN của trang cần lấy. Một chỉ số (offset) sẽ
    trỏ sai ngay khi một dòng bị loại/khôi phục giữa hai lần tải — đúng thao
    tác mà `UI-03` làm trên cùng màn hình này. Mã BH không tồn tại (đã bị loại
    hết dòng) ⟹ trang bắt đầu lại từ đầu sheet, chứ không ném lỗi vào mặt
    người đang cuộn.
    """
    shades = group_shades(details)
    order_keys = list(shades)
    lines_of: dict[str, int] = {}
    for detail in details:
        lines_of[detail["order_key"]] = lines_of.get(detail["order_key"], 0) + 1

    start = 0
    if cursor:
        try:
            start = order_keys.index(cursor)
        except ValueError:
            start = 0

    limit = max(1, min(int(limit), WORKSPACE_PAGE_LINES_MAX))
    taken: list[str] = []
    counted = 0
    for key in order_keys[start:]:
        taken.append(key)
        counted += lines_of[key]
        if counted >= limit:
            break
    end = start + len(taken)
    chosen = set(taken)
    return {
        "details": [d for d in details if d["order_key"] in chosen],
        "order_keys": taken,
        "shades": shades,
        "cursor": order_keys[start] if order_keys else None,
        "next_cursor": order_keys[end] if end < len(order_keys) else None,
        "total_orders": len(order_keys),
        "total_lines": len(details),
    }


def cursor_for_order(details: list[dict], order_key: str, *,
                     limit: int = WORKSPACE_PAGE_LINES) -> Optional[str]:
    """Con trỏ của TRANG CHỨA `order_key`, hoặc `None` nếu nó ở trang đầu.

    Dùng cho những liên kết trỏ tới một BH cụ thể (`#bh-…` của cảnh báo chưa
    phân loại): sau `UI-04`, BH ấy có thể không nằm trên trang đang mở, và một
    neo trỏ vào một phần tử không tồn tại là một liên kết chết. Phép đi tới là
    CHÍNH `page_of_groups`, lặp trang này sang trang khác — không một phép
    chia offset thứ hai nào, vì kích thước trang phụ thuộc số dòng của từng
    BH chứ không cố định.
    """
    cursor = None
    while True:
        page = page_of_groups(details, cursor=cursor, limit=limit)
        if order_key in page["order_keys"]:
            return cursor
        if page["next_cursor"] is None:
            return None
        cursor = page["next_cursor"]


def sheet_detail_totals(details: list[dict]) -> dict:
    """Tổng Giá nhập/Giá bán của TOÀN sheet — một hàng ngay dưới tiêu đề cột
    của bảng kê (`TASK-OWNER-UIUX-004` §5, chủ dự án yêu cầu trực tiếp).

    Cộng thẳng từ CÙNG tập dòng mà `sheet_detail_groups` hiển thị (kể cả dòng
    Chiết khấu suy ra — nó cũng đứng trong cột Giá nhập/Giá bán của chính
    bảng này), nên hàng tổng luôn khớp với những gì Owner đang nhìn thấy phía
    dưới nó, không phải một phép cộng dựng riêng có thể lệch đi.

    Lợi nhuận KPI và DS quy đổi KHÔNG được cộng lại ở đây: hai con số đó đã
    có một tổng CHÍNH THỨC, có gate (`sheet.kpi_profit`/`strip.converted_
    sales`, hiện trong dải KPI của chính trang này) — cộng thẳng từ dòng sẽ
    bỏ qua gate và có thể ra một con số KHÁC cho CÙNG một khái niệm. Template
    dùng lại đúng hai giá trị đó cho hàng tổng, không tính hai lần.
    """
    purchase = Decimal(0)
    sell = Decimal(0)
    for detail in details:
        for part in bm.display_contributions(detail["line"]):
            if part.purchase_price is not None:
                purchase += part.purchase_price
            if part.sell_price is not None:
                sell += part.sell_price
    # `DEC-212` — hàng tổng viết theo NGHÌN ĐỒNG như mọi ô tiền khác, và phải
    # dùng ĐÚNG hàm của tầng trình bày nghiệp vụ: viết lại phép chia 1.000 ở
    # đây là cách hàng tổng làm tròn lệch đi so với chính các dòng nó cộng.
    return {
        **price_pair(purchase, "purchase_price"),
        **price_pair(sell, "sell_price"),
    }


def excluded_rows(excluded: list[dict]) -> list[dict]:
    """Các dòng Owner đã loại khỏi báo cáo, để khôi phục được (`§56` EX-07).

    Chúng KHÔNG mang một ô tiền suy ra nào: một dòng đã bị loại không góp vào
    chỉ tiêu nào, nên hiện lợi nhuận của nó cạnh các con số của kỳ chỉ mời gọi
    người đọc cộng nhầm.
    """
    return [
        {
            "order_key": detail["order_key"],
            "product_key": detail["product_key"],
            "occurrence_index": detail["occurrence_index"],
            "date_text": business_date(detail["sale_date"]),
            "product_raw": detail["product_raw"] or "—",
            "employee": detail["line"].employee or UNKNOWN_EMPLOYEE,
            "excluded_at": detail["exclusion"]["excluded_at"],
        }
        for detail in sorted(
            excluded,
            key=lambda item: (item["sale_date"] is None, item["sale_date"],
                              item["order_key"], item["occurrence_index"]))
    ]


def removed_in_source_rows(removed: list[dict]) -> list[dict]:
    """Dòng đang bị TẠM LOẠI vì không còn trong sổ đã xác nhận đầy đủ (R5 §1).

    Cùng hình dạng và cùng kỷ luật với `excluded_rows`: Số BH · ngày cũ ·
    sản phẩm · nhân viên, và KHÔNG một ô tiền nào. Ở đây kỷ luật ấy còn chặt
    hơn một bậc — các con số của những dòng này VỪA bị trừ khỏi mọi chỉ tiêu
    của kỳ, nên in lại chúng ngay bên dưới là đặt đúng số vừa trừ cạnh đúng
    cái tổng vừa giảm.

    Khác `excluded_rows` ở một chỗ, và chỗ đó là lý do không gộp hai hàm: ở
    đây KHÔNG có nút khôi phục. Owner không "bỏ loại" được một dòng mà sổ kế
    toán không còn chứa — đường quay lại duy nhất là nạp một sổ có nó, và
    câu chữ phải nói đúng như vậy chứ không mời bấm một nút không tồn tại.
    """
    return [
        {
            "order_key": detail["order_key"],
            "product_key": detail["product_key"],
            "occurrence_index": detail["occurrence_index"],
            "date_text": business_date(detail["sale_date"]),
            "product_raw": detail["product_raw"] or "—",
            "employee": detail["line"].employee or UNKNOWN_EMPLOYEE,
            "snapshot_id": detail["removed"]["raised_by_snapshot_id"],
            "range_text": _confirmed_range_text(detail["removed"]),
        }
        for detail in sorted(
            removed,
            key=lambda item: (item["sale_date"] is None, item["sale_date"],
                              item["order_key"], item["occurrence_index"]))
    ]


def _confirmed_range_text(removed: dict) -> str:
    """Khoảng ngày mà sổ kia đã được xác nhận là đầy đủ, viết ra thành lời.

    Thiếu một trong hai đầu ⟹ chuỗi rỗng, không đoán: một khoảng nửa vời in
    ra màn hình đọc như một sự thật, và người đọc sẽ dùng nó để kết luận sổ
    nào đã phủ ngày nào.
    """
    start, end = removed.get("range_start"), removed.get("range_end")
    if not start or not end:
        return ""
    return f"{business_date(date.fromisoformat(start))} → {business_date(date.fromisoformat(end))}"


def period_options(
    periods: list[tuple[int, int]], *, selected: tuple[int, int], today: date,
) -> list[dict]:
    """Bộ chọn kỳ của không gian làm việc — CHỈ các tháng (`§3`).

    KHÔNG có mục "Toàn bộ dữ liệu" (`§50` CASE UX-03): đây là màn hình vận
    hành theo tháng, và một Target không biết mình thuộc tháng nào là một
    Target ghi vào tháng sai (PHB-05 §4).

    Tháng HIỆN TẠI và tháng ĐANG XEM luôn có mặt kể cả khi chưa có dòng bán
    nào (`§2`, `§45`): Owner được phép mở tháng hiện tại để đặt Target TRƯỚC
    lần nạp sổ đầu tiên của tháng đó, và một bộ chọn không chứa tháng đang xem
    sẽ tự nhảy về một tháng khác ngay khi tải lại trang.
    """
    months = {*periods, selected, (today.year, today.month)}
    return [{"value": f"{year}-{month:02d}", "label": f"Tháng {month:02d}/{year}",
             "selected": (year, month) == selected}
            for year, month in sorted(months, reverse=True)]


def sheet_view(
    sheet, totals: bm.BusinessTotals, *, period: tuple[int, int],
) -> dict:
    """Nhận diện + các chỉ tiêu phụ của sheet đang xem.

    Năm ô chính nằm ở `summary_strip`; những con số dưới đây là bối cảnh mà
    các màn hình đã nghiệm thu của PHB-03/PHB-05 vẫn đọc (số đơn, số dòng,
    coverage, lợi nhuận KPI). Giữ chúng ở đây là cách bảo đảm không gian làm
    việc mới KHÔNG làm mất một chỉ tiêu nào đã có.
    """
    return {
        "key": sheet.key,
        "label": sheet.label or UNKNOWN_EMPLOYEE,
        "is_group": sheet.is_group,
        "employee": sheet.employee,
        "unresolved": sheet.unresolved,
        "accepts_gia_dung": sheet.accepts_gia_dung_classification,
        "period_label": period_label(period),
        "orders": count(totals.orders),
        "lines": count(totals.lines),
        "qualifying_quantity": _decimal(totals.qualifying_quantity),
        "kpi_profit": gated_cell(
            totals.kpi_profit, totals.official_kpi_profit, totals.state),
        "coverage": coverage_cell(totals.coverage),
        "state": totals.state,
        "state_label": STATE_LABELS[totals.state],
    }


__all__ = [
    "EMPTY_PERIOD_NOTE", "EXCLUDED_NOTE", "EXCLUDE_CONFIRM_POINTS",
    "REMOVED_IN_SOURCE_NOTE", "removed_in_source_rows",
    "HIDE_OPTIONAL_LABEL", "OPTIONAL_COLUMNS_NOTE", "OPTIONAL_COLUMN_INDEXES",
    "SHOW_OPTIONAL_LABEL",
    "EXCLUDE_CONFIRM_QUESTION", "GIA_DUNG_CONFIRM_POINTS",
    "GIA_DUNG_CONFIRM_QUESTION", "LOSS_CODES", "MOM_NO_PREVIOUS",
    "PROGRESS_NOTE", "SHEET_DETAIL_COLUMNS", "SHORT_TAGS",
    "WORKSPACE_PAGE_LINES", "WORKSPACE_PAGE_LINES_MAX",
    "cursor_for_order",
    "TARGET_KVND_NOTE", "TARGET_NOT_KVND_NOTE", "TARGET_UNIT_LABEL",
    "business_date", "excluded_rows", "group_shades", "period_options",
    "page_of_groups", "progress_cell",
    "sheet_detail_groups", "sheet_detail_totals", "sheet_tabs", "sheet_view",
    "summary_strip", "target_cell", "vs_target_cell",
]
