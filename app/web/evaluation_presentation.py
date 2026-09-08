"""R4 — tầng TRÌNH BÀY của báo cáo đánh giá.

Module này THUẦN theo đúng nghĩa mà `business_presentation` đã đặt: không SQL,
không truy vấn, không `url_for`. Nó nhận các value object của
`reporting.evaluation` và trả về dict cho template.

## Vì sao đường dẫn drill-down do TẦNG ROUTE truyền vào

`url_for` là một hàm của Flask và nó cần application context. Gọi nó ở đây sẽ
biến một module kiểm được bằng giá trị thuần thành một module phải dựng app
mới test được — chính điều mà `pending_items` của PHB-03 đã tránh bằng cách
nhận `coverage_url` từ route. R4 giữ nguyên khuôn đó, chỉ tổng quát hoá thành
MỘT hàm `drill(key)` do route cung cấp.

## Một ô không có số thì BẮT BUỘC nói vì sao

`evaluation.Kpi` đã canh bất biến "có số ⟺ không có lý do" ở tầng ngữ nghĩa.
Ở đây nó được canh lần nữa theo chiều hiển thị: mọi ô đều mang `text` và
`reason_label`, và `text` của một ô vắng số là `—` — không bao giờ `0`,
`0 %`, `0 đồng` hay một ô trống không chú thích.

## Đơn vị luôn đi cùng con số

Tiền hiển thị theo NGHÌN ĐỒNG (`R1` §9, đúng quy ước trang Báo cáo đang
dùng), và LUÔN kèm bản VND đầy đủ ở `full` để không đường nào mất khả năng
xem lại số gốc. Mọi phép tính vẫn chạy trên VND canonical ở tầng ngữ nghĩa —
không hàm nào trong file này được gọi từ một đường TÍNH.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Callable, Optional, Sequence

from app.modules.reporting import business_metrics as bm
from app.modules.reporting import evaluation as ev
from app.web.analytics_presentation import count, period_label
from app.web.business_presentation import coverage_cell
from app.web.legacy_presentation import format_number

EM_DASH = "—"

#: Ô tiền hiển thị theo nghìn đồng; nhãn này đi kèm mọi cột tiền của trang.
MONEY_UNIT_NOTE = (
    "Mọi ô tiền trên trang này viết theo NGHÌN ĐỒNG. Số VND đầy đủ nằm trong "
    "chú thích của chính ô đó; mọi phép tính đều chạy trên VND đầy đủ.")

PAGE_TITLE = "BÁO CÁO ĐÁNH GIÁ"

# --------------------------------------------------------------------------
# Nhãn — mỗi mã lý do đúng MỘT câu, và câu đó nói việc phải làm.
# --------------------------------------------------------------------------

KPI_LABELS = {
    "sales_revenue": "Doanh thu bán hàng",
    "orders": "Số đơn",
    "qualifying_quantity": "SL đủ điều kiện KPI",
    "revenue_per_order": "Doanh thu/đơn",
    "kpi_profit": "Lợi nhuận KPI",
    "margin_percent": "Biên KPI",
    "profit_per_order": "Lãi/đơn",
    "converted_sales": "DS quy đổi",
}

KPI_NOTES = {
    "sales_revenue": (
        "Σ(giá bán × số lượng − chiết khấu) của các dòng đang được báo cáo. "
        "Đây là số NET — chiết khấu đã trừ một lần và chỉ một lần."),
    "orders": (
        "Số chứng từ PHÂN BIỆT trong phạm vi đang xem. KHÔNG cộng được giữa "
        "các nhân viên/sheet: một đơn có hai người bán được đếm ở cả hai, nên "
        "dòng TỔNG luôn lấy từ tổng kỳ chứ không cộng cột này."),
    "qualifying_quantity": (
        "Tổng SỐ LƯỢNG của các dòng có ĐƠN GIÁ BÁN > 1.000.000 VND. Đây là số "
        "lượng, không phải số mã hàng (SKU)."),
    "revenue_per_order": (
        "Doanh thu bán hàng ÷ Số đơn, trong cùng một phạm vi. Không có số khi "
        "phạm vi chưa có đơn nào."),
    "kpi_profit": (
        "Lợi nhuận KPI CHÍNH THỨC của kỳ. Chỉ có số khi 100 % số dòng đã tính "
        "được lợi nhuận; còn thiếu một dòng thì tổng phần đã biết KHÔNG được "
        "công bố như kết quả cả kỳ."),
    "margin_percent": (
        "Lợi nhuận KPI CHÍNH THỨC ÷ Doanh thu bán hàng × 100. Không cap ở "
        "100 %, không kẹp về 0 — biên âm là một sự thật kế toán."),
    "profit_per_order": (
        "Lợi nhuận KPI CHÍNH THỨC ÷ Số đơn, trong cùng một phạm vi."),
    "converted_sales": (
        "Σ(lợi nhuận KPI của TỪNG DÒNG ÷ tỉ lệ quy đổi của chính dòng đó). "
        "Phép chia xảy ra ở cấp dòng rồi mới cộng — không bao giờ chia tổng "
        "cho một tỉ lệ trung bình."),
}

KPI_REASON_LABELS = {
    ev.REASON_NO_LINES: "Phạm vi này chưa có dòng hàng nào",
    ev.REASON_NO_ORDERS: "Chưa có đơn nào — không có mẫu số để chia",
    ev.REASON_NO_REVENUE: "Chưa có doanh thu — không có mẫu số để chia",
    ev.REASON_PROFIT_NOT_OFFICIAL: (
        "Lợi nhuận KPI chưa chính thức — còn dòng chưa tính được lợi nhuận"),
    ev.REASON_CONVERTED_NOT_OFFICIAL: (
        "DS quy đổi chưa chính thức — còn dòng chưa tính được lợi nhuận"),
}

TARGET_REASON_LABELS = {
    bm.TARGET_UNSET: "Chưa đặt target cho phạm vi này",
    bm.TARGET_ZERO: "Target đang đặt bằng 0 — không chia được",
    bm.TARGET_NO_ACTUAL: "Chưa có DS quy đổi nào để so",
    ev.TARGET_ACTUAL_NOT_OFFICIAL: (
        "DS quy đổi mới tính được một phần — chưa được phép so target. "
        "Hoàn thiện giá nhập cho các dòng còn thiếu là xong."),
    ev.TARGET_NO_DAYS_REMAINING: (
        "Đã hết tháng — không còn ngày nào để chia phần còn thiếu"),
}

COMPARE_REASON_LABELS = {
    ev.COMPARE_NO_PERIOD: (
        "Đang xem toàn bộ dữ liệu — không có kỳ liền trước để so"),
    ev.COMPARE_PREVIOUS_NO_LINES: (
        "Kỳ trước không có dòng nào trong cùng khoảng ngày — không có tỉ lệ "
        "nào đúng để nói"),
    ev.COMPARE_PREVIOUS_ZERO: (
        "Kỳ trước doanh thu bằng 0 — không có tỉ lệ nào đúng để nói"),
    ev.COMPARE_CURRENT_NO_REVENUE: (
        "Kỳ này chưa có doanh thu nào trong khoảng ngày đang so"),
}

RUN_RATE_LABEL = "Ước tính nếu tốc độ hiện tại giữ nguyên"
RUN_RATE_NOTE = (
    "Đây KHÔNG phải dự báo và KHÔNG phải cam kết: nó là "
    "(giá trị đến ngày đang xét ÷ số ngày đã trôi qua) × số ngày trong tháng. "
    "Không mô hình, không mùa vụ, không nguyên nhân.")

RUN_RATE_REASON_LABELS = {
    ev.RUNRATE_NOT_RUNNING: "Kỳ đã kết thúc — con số thật đã có, không ước tính",
    ev.RUNRATE_VALUE_NOT_OFFICIAL: (
        "Chỉ tiêu nền chưa chính thức — không ước tính từ một con số một phần"),
    ev.RUNRATE_NO_DAILY_DATA: (
        "Không có dòng nào mang ngày bán — không đo được tốc độ theo ngày"),
    ev.RUNRATE_NO_ELAPSED_DAYS: "Kỳ chưa bắt đầu — chưa có ngày nào để đo",
}

TARGET_SCOPE_NOTE = (
    "Target chỉ tồn tại ở phạm vi NHÂN VIÊN hoặc SHEET NHÓM. Không có target "
    "cấp công ty, và target của một nhóm KHÔNG phải tổng target của những "
    "người trong nhóm — cộng lên sẽ cho ra một con số chưa ai đặt.")

SAME_DAYS_NOTE = (
    "Tháng đang chạy được so với tháng trước trên CÙNG số ngày lịch "
    "(ví dụ 01–08/09 so với 01–08/08). Dòng không có ngày bán bị loại khỏi "
    "cả hai vế và được đếm riêng.")

SHEET_TABLE_SCOPE_NOTE = (
    "Bảng này LUÔN nói về CẢ KỲ, kể cả khi trang đang thu hẹp về một đơn vị: "
    "nó trả lời \"kết quả của kỳ đến từ những đơn vị nào\". Vì vậy hàng TỔNG "
    "và cột Tỉ trọng của riêng bảng này lấy mẫu số là doanh thu CẢ KỲ, không "
    "phải doanh thu của phạm vi đang chọn.")

ORDERS_NOT_ADDITIVE_NOTE = (
    "Cột Đơn KHÔNG cộng dọc được: một đơn có nhiều mặt hàng/nhân viên được "
    "đếm ở nhiều hàng. Dòng TỔNG lấy từ tổng của phạm vi, không cộng cột.")

LOSS_NOTE = (
    "Chỉ xét những dòng ĐÃ tính được lợi nhuận KPI. Khi coverage chưa đủ, "
    "đây không phải toàn bộ đơn lỗ của kỳ — phạm vi đã xét ghi ngay bên cạnh.")

LOWEST_MARGIN_NOTE = (
    "Đây là một THỨ TỰ SẮP XẾP theo biên KPI tăng dần, không phải một phán "
    "quyết: không có ngưỡng \"biên thấp\" nào được đặt ra ở đây. Chỉ những "
    "hàng đã đủ coverage của chính nó mới có biên để xếp.")

DISCOUNT_NOTE = (
    "Doanh thu bán hàng đã là số NET — chiết khấu đã được trừ một lần. Khối "
    "này CỘNG NGƯỢC phần đã trừ để nói ra quy mô của nó, nên tỉ lệ được chia "
    "cho doanh thu TRƯỚC chiết khấu. Không có phép trừ thứ hai ở đâu cả.")

MIN_STATUS_UNAVAILABLE_NOTE = (
    "Trạng thái FINAL/PROVISIONAL của giá MIN theo ngày KHÔNG được lưu lại "
    "trên từng dòng: hợp đồng daily-min-v1 mang day_status trong ảnh chụp lúc "
    "chạy, và ảnh chụp đó không được ghi vào dữ liệu hiệu lực. R4 chỉ ĐỌC dữ "
    "liệu hiệu lực nên nó KHÔNG dựng lại con số đó và cũng không đoán — thay "
    "vào đó là bảng THẨM QUYỀN GIÁ ngay dưới, tức nguồn mà lần chạy pipeline "
    "đã dùng cho từng dòng. Muốn có FINAL/PROVISIONAL theo dòng thì phải lưu "
    "thêm nó lúc nạp sổ; đó là một thay đổi ở đường nhập, ngoài phạm vi R4.")

PRICE_SOURCE_LABELS = {
    "TRACKING_DAILY_MIN": "MIN theo ngày bán (Tracking)",
    "TRACKING_PRICE_HISTORY": "Lịch sử giá Tracking",
    "PriceMaster": "Bảng giá (PriceMaster)",
    "Pending": "Pipeline chưa tra được giá",
}

PROVENANCE_LABELS = {
    bm.PROVENANCE_AUTO: "Tự động (MIN theo ngày bán)",
    bm.PROVENANCE_MANUAL: "Owner nhập tay",
    bm.PROVENANCE_MANUAL_OVERRIDE: "Owner ghi đè giá tự động",
    bm.PROVENANCE_POLICY_ZERO: "Giá 0 theo chính sách loại dòng",
    bm.PROVENANCE_PENDING: "Chưa có giá nhập",
}


# --------------------------------------------------------------------------
# Định dạng.
# --------------------------------------------------------------------------

def money(value: Optional[Decimal]) -> str:
    """VND đầy đủ. `None` ⟹ `—`, không bao giờ `0`."""
    return EM_DASH if value is None else format_number(value)


def thousand_vnd(value: Optional[Decimal]) -> str:
    """Cùng con số, viết theo NGHÌN ĐỒNG. Chỉ để hiển thị."""
    if value is None:
        return EM_DASH
    return format_number(
        (Decimal(value) / Decimal(1000)).quantize(Decimal("1")))


def percent(value: Optional[Decimal], *, sign: bool = False) -> str:
    """`None` ⟹ `—`. KHÔNG BAO GIỜ in vô cực hay một phần trăm bịa."""
    if value is None:
        return EM_DASH
    prefix = "+" if sign and value > 0 else ""
    return f"{prefix}{format_number(value)}%"


def business_date(value: Optional[date]) -> str:
    """`DD/MM/YYYY` (`DEC-184` §24) — không bao giờ ISO trên màn hình."""
    return EM_DASH if value is None else value.strftime("%d/%m/%Y")


def _formatted(kpi: ev.Kpi) -> tuple[str, str]:
    """`(chữ hiển thị, chữ đầy đủ)` theo đúng ĐƠN VỊ của chỉ tiêu."""
    if kpi.value is None:
        return EM_DASH, ""
    if kpi.unit == ev.UNIT_VND:
        return thousand_vnd(kpi.value), f"{money(kpi.value)} đồng"
    if kpi.unit == ev.UNIT_PERCENT:
        return percent(kpi.value), ""
    return format_number(kpi.value), ""


def kpi_cell(kpi: ev.Kpi, *, drill: Optional[Callable[[str], str]] = None) -> dict:
    """Một ô chỉ tiêu, sẵn sàng cho template.

    `partial` chỉ có mặt khi chỉ tiêu bị cổng coverage chặn VÀ đã tính được
    một phần. Template được yêu cầu đặt nó cạnh coverage, không bao giờ ở vị
    trí của `text` — đó là toàn bộ khác biệt giữa "đã tính được đến đâu" và
    "kết quả của kỳ".
    """
    text, full = _formatted(kpi)
    return {
        "key": kpi.key,
        "label": KPI_LABELS.get(kpi.key, kpi.key),
        "text": text,
        "full": full,
        "unit": kpi.unit,
        "available": kpi.available,
        "gated": kpi.gated,
        "reason": kpi.reason or "",
        "reason_label": KPI_REASON_LABELS.get(kpi.reason, "") if kpi.reason else "",
        "note": KPI_NOTES.get(kpi.key, ""),
        "partial": (thousand_vnd(kpi.partial_value)
                    if (not kpi.available and kpi.partial_value is not None)
                    else ""),
        "partial_full": (f"{money(kpi.partial_value)} đồng"
                         if (not kpi.available and kpi.partial_value is not None)
                         else ""),
        "url": (drill(kpi.drill) if drill and kpi.drill else ""),
    }


def headline_cells(
    kpis: dict[str, ev.Kpi], *, drill: Optional[Callable[[str], str]] = None,
) -> list[dict]:
    """Tám ô đầu trang, ĐÚNG thứ tự đã freeze ở `evaluation.HEADLINE_ORDER`."""
    return [kpi_cell(kpis[key], drill=drill) for key in ev.HEADLINE_ORDER]


# --------------------------------------------------------------------------
# Target · run-rate · so kỳ trước.
# --------------------------------------------------------------------------

def target_block(
    progress: ev.TargetProgress, *, scope_label: str,
    run: Optional[ev.RunRate] = None,
) -> dict:
    """Khối tiến độ target của MỘT phạm vi có target.

    `run` là TUỲ CHỌN vì một HÀNG của bảng sheet cũng dùng khối này, và ở đó
    không có chỗ cho một ô run-rate. `None` ⟹ không có ô nào, chứ KHÔNG phải
    một `RunRate` giả mang lý do "kỳ đã kết thúc" — một lý do sai còn tệ hơn
    không có lý do, vì nó đọc được và nó nói dối.
    """
    return {
        "scope_label": scope_label,
        "has_target": progress.has_target,
        "target": thousand_vnd(progress.target),
        "target_full": (f"{money(progress.target)} đồng"
                        if progress.target is not None else ""),
        "actual": thousand_vnd(progress.actual),
        "actual_full": (f"{money(progress.actual)} đồng"
                        if progress.actual is not None else ""),
        "partial_actual": (
            thousand_vnd(progress.partial_actual)
            if progress.actual is None and progress.partial_actual is not None
            else ""),
        "percent": percent(progress.percent),
        "reason": progress.reason or "",
        "reason_label": (TARGET_REASON_LABELS.get(progress.reason, "")
                         if progress.reason else ""),
        "shortfall": thousand_vnd(progress.shortfall),
        "shortfall_full": (f"{money(progress.shortfall)} đồng"
                           if progress.shortfall is not None else ""),
        "achieved": progress.achieved,
        "days_remaining": progress.days_remaining,
        "required_per_day": thousand_vnd(progress.required_per_day),
        "required_per_day_full": (
            f"{money(progress.required_per_day)} đồng"
            if progress.required_per_day is not None else ""),
        "required_reason": progress.required_reason or "",
        "required_reason_label": (
            TARGET_REASON_LABELS.get(progress.required_reason, "")
            if progress.required_reason else ""),
        "run_rate": None if run is None else run_rate_cell(run),
        "note": TARGET_SCOPE_NOTE,
    }


def run_rate_cell(run: ev.RunRate) -> dict:
    """Ô run-rate. Nhãn "ước tính" là BẮT BUỘC và không tắt được."""
    return {
        "label": RUN_RATE_LABEL,
        "text": thousand_vnd(run.value),
        "full": f"{money(run.value)} đồng" if run.value is not None else "",
        "available": run.value is not None,
        "reason": run.reason or "",
        "reason_label": (RUN_RATE_REASON_LABELS.get(run.reason, "")
                         if run.reason else ""),
        "elapsed_days": run.elapsed_days,
        "month_days": run.month_days,
        "note": RUN_RATE_NOTE,
    }


def same_days_block(comparison: ev.SameDaysComparison, *, period) -> dict:
    """Khối "so cùng số ngày lịch với tháng trước"."""
    previous = (None if period is None else ev.previous_month(period))
    return {
        "percent": percent(comparison.percent, sign=True),
        "available": comparison.percent is not None,
        "reason": comparison.reason or "",
        "reason_label": (COMPARE_REASON_LABELS.get(comparison.reason, "")
                         if comparison.reason else ""),
        "current": thousand_vnd(comparison.current),
        "current_full": (f"{money(comparison.current)} đồng"
                         if comparison.current is not None else ""),
        "previous": thousand_vnd(comparison.previous),
        "previous_full": (f"{money(comparison.previous)} đồng"
                          if comparison.previous is not None else ""),
        "previous_label": period_label(previous),
        "day_cutoff": comparison.day_cutoff,
        # Ngày viết hai chữ số, cùng quy ước `DD/MM/YYYY` của `business_date`:
        # "01–3" đọc lệch nhịp cạnh một trang mà mọi ngày khác đều hai chữ số.
        "day_cutoff_label": f"{comparison.day_cutoff:02d}",
        "as_of_day": comparison.as_of_day,
        "as_of_day_label": f"{comparison.as_of_day:02d}",
        "shortened": (not comparison.full_month
                      and comparison.day_cutoff < comparison.as_of_day),
        "full_month": comparison.full_month,
        "excluded_undated_lines": comparison.excluded_undated_lines,
        "note": SAME_DAYS_NOTE,
    }


# --------------------------------------------------------------------------
# Bảng đóng góp.
# --------------------------------------------------------------------------

def group_rows(
    rows: Sequence[ev.GroupRow], whole: bm.BusinessTotals, *,
    drill: Optional[Callable[[ev.GroupRow], str]] = None,
    total_label: str = "TỔNG",
) -> list[dict]:
    """Bảng đóng góp + hàng TỔNG.

    Hàng TỔNG lấy từ `whole` — tổng của PHẠM VI — chứ không cộng các hàng
    phía trên. Cùng kỷ luật `employee_rows`/`brand_rows`/`composition_rows`
    đã nghiệm thu: cột Đơn cộng dọc lên có thể lớn hơn tổng thật, nên một
    dòng TỔNG cộng dọc sẽ hiện một con số sai.
    """
    out = [group_row(row, drill=drill) for row in rows]
    out.append({
        "key": "", "label": total_label, "total_row": True, "url": "",
        "revenue": thousand_vnd(whole.sales_revenue),
        "revenue_full": f"{money(whole.sales_revenue)} đồng",
        "orders": count(whole.orders),
        "lines": count(whole.lines),
        "quantity": money(whole.qualifying_quantity),
        "share": percent(
            None if whole.sales_revenue is None else Decimal(100)
            if whole.sales_revenue != 0 else None),
        "profit": thousand_vnd(whole.official_kpi_profit),
        "profit_full": (f"{money(whole.official_kpi_profit)} đồng"
                        if whole.official_kpi_profit is not None else ""),
        "profit_available": whole.official_kpi_profit is not None,
        "margin": percent(ev.margin_percent(whole.official_kpi_profit,
                                            whole.sales_revenue)),
        "margin_reason_label": "",
        "coverage": coverage_cell(whole.coverage),
    })
    return out


def group_row(
    row: ev.GroupRow, *, drill: Optional[Callable[[ev.GroupRow], str]] = None,
) -> dict:
    totals = row.totals
    return {
        "key": row.key,
        "label": row.label,
        "total_row": False,
        "revenue": thousand_vnd(totals.sales_revenue),
        "revenue_full": f"{money(totals.sales_revenue)} đồng",
        "orders": count(totals.orders),
        "lines": count(totals.lines),
        "quantity": money(totals.qualifying_quantity),
        "share": percent(row.revenue_share),
        "profit": thousand_vnd(totals.official_kpi_profit),
        "profit_full": (f"{money(totals.official_kpi_profit)} đồng"
                        if totals.official_kpi_profit is not None else ""),
        "profit_available": totals.official_kpi_profit is not None,
        "margin": percent(row.margin),
        "margin_reason_label": (KPI_REASON_LABELS.get(row.margin_reason, "")
                                if row.margin_reason else ""),
        "coverage": coverage_cell(totals.coverage),
        "url": drill(row) if drill else "",
    }


def discount_block(summary: ev.DiscountSummary, *, drill: str = "") -> dict:
    return {
        "total": thousand_vnd(summary.discount_total),
        "total_full": f"{money(summary.discount_total)} đồng",
        "percent_of_gross": percent(summary.percent_of_gross),
        "percent_available": summary.percent_of_gross is not None,
        "gross": thousand_vnd(summary.gross_revenue),
        "gross_full": (f"{money(summary.gross_revenue)} đồng"
                       if summary.gross_revenue is not None else ""),
        "net": thousand_vnd(summary.net_revenue),
        "lines_with_discount": summary.lines_with_discount,
        "orders_with_discount": summary.orders_with_discount,
        "double_count_orders": list(summary.double_count_orders),
        "note": DISCOUNT_NOTE,
        "url": drill,
    }


def loss_block(scope: ev.LossScope, *, drill: str = "") -> dict:
    return {
        "lines": len(scope.lines),
        "orders": len(scope.orders),
        "order_keys": list(scope.orders),
        "total": thousand_vnd(scope.loss_total),
        "total_full": (f"{money(scope.loss_total)} đồng"
                       if scope.loss_total is not None else ""),
        "examined_lines": scope.examined_lines,
        "total_lines": scope.total_lines,
        "scope_text": (
            f"{count(scope.examined_lines)} / {count(scope.total_lines)} dòng"),
        "complete_scope": scope.complete_scope,
        "note": LOSS_NOTE,
        "url": drill,
    }


# --------------------------------------------------------------------------
# Khối "Đủ dữ liệu để kết luận?".
# --------------------------------------------------------------------------

def data_quality_block(
    *, totals: bm.BusinessTotals, provenance: Sequence[tuple[str, int]],
    price_sources: Sequence[tuple[str, int]],
    latest_sale: Optional[date], undated_lines: int,
    identity_counts: dict, binding_exceptions: int,
    closed, drift: bool, period, coverage_url: str = "",
) -> dict:
    """Một khối trả lời ĐÚNG câu "đã đủ dữ liệu để kết luận chưa?".

    Không có badge "đủ" nào bật lên khi mới chỉ một phần lợi nhuận được tính:
    `sufficient` đọc thẳng `coverage.is_complete`, tức phép SO BẰNG của
    `DEC-PHB02-02` §4, chứ không đọc phần trăm đã làm tròn.
    """
    return {
        "sufficient": totals.coverage.is_complete,
        "coverage": coverage_cell(totals.coverage),
        "coverage_url": coverage_url,
        "provenance": [
            {"code": code, "label": PROVENANCE_LABELS.get(code, code),
             "lines": lines}
            for code, lines in provenance
        ],
        "price_sources": [
            {"code": code or "KHONG_GHI_NHAN",
             "label": PRICE_SOURCE_LABELS.get(code, code or "Không ghi nhận"),
             "lines": lines}
            for code, lines in price_sources
        ],
        "min_status_note": MIN_STATUS_UNAVAILABLE_NOTE,
        "latest_sale_date": business_date(latest_sale),
        "has_latest_sale": latest_sale is not None,
        "undated_lines": undated_lines,
        "identity": identity_counts,
        "binding_exceptions": binding_exceptions,
        "closed": closed,
        "drift": bool(drift),
        "period_label": period_label(period),
    }


__all__ = [
    "COMPARE_REASON_LABELS", "DISCOUNT_NOTE", "EM_DASH", "KPI_LABELS",
    "KPI_NOTES", "KPI_REASON_LABELS", "LOSS_NOTE", "LOWEST_MARGIN_NOTE",
    "MIN_STATUS_UNAVAILABLE_NOTE", "MONEY_UNIT_NOTE",
    "ORDERS_NOT_ADDITIVE_NOTE", "PAGE_TITLE", "PRICE_SOURCE_LABELS",
    "PROVENANCE_LABELS",
    "RUN_RATE_LABEL", "RUN_RATE_NOTE", "RUN_RATE_REASON_LABELS",
    "SAME_DAYS_NOTE", "SHEET_TABLE_SCOPE_NOTE", "TARGET_REASON_LABELS",
    "TARGET_SCOPE_NOTE",
    "business_date", "data_quality_block", "discount_block", "group_row",
    "group_rows",
    "headline_cells", "kpi_cell", "loss_block", "money", "percent",
    "run_rate_cell", "same_days_block", "target_block", "thousand_vnd",
]
