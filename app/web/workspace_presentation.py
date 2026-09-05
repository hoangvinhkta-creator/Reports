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
    coverage_cell, gated_cell, month_over_month, percent, period_label,
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
SHEET_DETAIL_COLUMNS: tuple[str, ...] = (
    "Ngày", "Mã đơn", "Khách hàng", "Mặt hàng", "Nhân viên", "SL",
    "Giá nhập", "Giá bán", "Lợi nhuận", "DS quy đổi",
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


def business_date(value: Optional[date]) -> str:
    """`§24` — mọi ngày nghiệp vụ của màn hình này viết `DD/MM/YYYY`."""
    return "—" if value is None else value.strftime("%d/%m/%Y")


def sheet_tabs(
    sheets: list, selected_key: Optional[str]
) -> list[dict]:
    """Thanh tab kiểu bảng tính, đặt TRÊN báo cáo (`§4`).

    Đây là các KHUNG NHÌN CON của một trang, không phải điều hướng cấp một:
    thanh `R1` bốn mục (Báo cáo · Nhân viên · Doanh số ngày · Dữ liệu) không
    bị đụng tới, và `§4` nói rõ điều đó.
    """
    return [
        {"key": sheet.key, "label": sheet.label or UNKNOWN_EMPLOYEE,
         "selected": sheet.key == selected_key,
         "group": sheet.is_group}
        for sheet in sheets
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
    return [{"code": code, "label": label} for code, label in seen.items()]


def _is_loss(line: bm.BusinessLine) -> bool:
    """`§35` — dòng đang bán lỗ hoặc lợi nhuận âm, MỘT trạng thái duy nhất."""
    return bool(LOSS_CODES.intersection(line.warnings))


def _line_row(detail: dict, *, sheet, part, synthetic: bool,
              confirmed_keys=None) -> dict:
    line = detail["line"]
    # `DEC-185` §PI-01/§PI-02 — trạng thái nhận diện của DÒNG THẬT.
    #
    # Dòng "Chiết khấu" là số suy ra từ sổ, không phải một mặt hàng, nên nó
    # không có trạng thái nhận diện nào và không được mời Owner phân loại.
    identity = (None if synthetic
                else line_identity.state_of(detail, confirmed_keys=confirmed_keys))
    return {
        "kind": part.kind,
        "synthetic": synthetic,
        "order_key": detail["order_key"],
        "product_key": detail["product_key"],
        "occurrence_index": detail["occurrence_index"],
        "product_raw": (bm.DISCOUNT_DISPLAY_LABEL if synthetic
                        else (detail["product_raw"] or "—")),
        "employee": line.employee or UNKNOWN_EMPLOYEE,
        "employee_resolved": line.employee_resolved,
        "quantity": _decimal(part.quantity),
        # `§25` — "Giá nhập", đứng TRƯỚC "Giá bán".
        "purchase_price": _decimal(part.purchase_price),
        "purchase_price_input": (
            "" if line.purchase_price is None
            else format_number(line.purchase_price)),
        "sell_price": _decimal(part.sell_price),
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
    }


#: Không có ngày nào đã thấy. Một sentinel dùng chung — xem `sheet_detail_groups`.
_NO_DATE_YET = object()


def sheet_detail_groups(details: list[dict], *, sheet,
                        confirmed_keys=None) -> list[dict]:
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
                "loss": False,
                # Nhân viên ở cấp BH (`§27`): đổi một lần là cả đơn đổi theo.
                # Khi các dòng của một BH đang thuộc nhiều người khác nhau, ô
                # chọn để TRỐNG thay vì tự chọn hộ một người — gợi ý sai ở đây
                # là dời KPI của người khác chỉ vì Owner bấm LƯU.
                "employees": [],
            }
        product, *discount_parts = bm.display_contributions(line)
        group["rows"].append(_line_row(detail, sheet=sheet, part=product,
                                       synthetic=False,
                                       confirmed_keys=confirmed_keys))
        for part in discount_parts:
            group["rows"].append(_line_row(detail, sheet=sheet, part=part,
                                           synthetic=True,
                                           confirmed_keys=confirmed_keys))
        if line.employee and line.employee not in group["employees"]:
            group["employees"].append(line.employee)
        for tag in _short_tags(line):
            if tag["code"] not in {item["code"] for item in group["tags"]}:
                group["tags"].append(tag)
        group["loss"] = group["loss"] or _is_loss(line)
        # `§PI-11` — BH này có dòng chưa phân loại nào không. Cờ ở cấp BH chứ
        # không cấp dòng vì cảnh báo đầu sheet đếm BH, và cái nó cuộn tới cũng
        # là một khối BH.
        group["unresolved_identity"] = group.get("unresolved_identity", False) or any(
            row.get("identity_state") == line_identity.STATE_UNRESOLVED
            for row in group["rows"])

    ordered = sorted(
        groups.values(),
        key=lambda item: (item["sale_date"] is None, item["sale_date"],
                          item["order_key"]))
    # `_NO_DATE_YET` là một sentinel DÙNG CHUNG, không phải một `object()`
    # dựng mới ở mỗi vòng: `x is not object()` luôn đúng (mỗi lời gọi tạo một
    # đối tượng khác), nên viết như vậy sẽ đảo nền ngay ở nhóm ngày ĐẦU TIÊN
    # và cả bảng lệch một nhịp.
    shade, previous_date = 0, _NO_DATE_YET
    for group in ordered:
        if group["sale_date"] != previous_date:
            if previous_date is not _NO_DATE_YET:
                shade = 1 - shade
            previous_date = group["sale_date"]
        group["shade"] = shade
        group["employee_value"] = (
            group["employees"][0] if len(group["employees"]) == 1 else "")
        group["lines"] = len(group["rows"])
    return ordered


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
    "EXCLUDE_CONFIRM_QUESTION", "GIA_DUNG_CONFIRM_POINTS",
    "GIA_DUNG_CONFIRM_QUESTION", "LOSS_CODES", "MOM_NO_PREVIOUS",
    "PROGRESS_NOTE", "SHEET_DETAIL_COLUMNS", "SHORT_TAGS",
    "TARGET_KVND_NOTE", "TARGET_NOT_KVND_NOTE", "TARGET_UNIT_LABEL",
    "business_date", "excluded_rows", "period_options", "progress_cell",
    "sheet_detail_groups", "sheet_tabs", "sheet_view", "summary_strip",
    "target_cell", "vs_target_cell",
]
