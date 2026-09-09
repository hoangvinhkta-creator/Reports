"""R6 — TẦNG TRÌNH BÀY của dashboard phân tích kinh doanh.

Không phép tính nghiệp vụ nào ở đây. Module này nhận kết quả đã gộp
(`dashboard_metrics`, `product_metrics`, `basket_metrics`) và biến nó thành
dict cho template — cùng ranh giới mà `business_presentation` đã giữ, và vì
cùng lý do: một phép cộng tiền nằm trong tầng trình bày là một phép cộng không
test nghiệp vụ nào nhìn thấy.

Cách VIẾT số dùng lại nguyên vẹn `business_presentation.money_text` /
`money_kvnd` / `percent`. R6 không có cách viết tiền của riêng nó — hai trang
cùng dự án làm tròn khác nhau là một lỗi người đọc phát hiện trước hệ thống.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional

from app.modules.reporting import basket_metrics as bkm
from app.modules.reporting import dashboard_metrics as dmx
from app.modules.reporting import product_metrics as pmx
from app.web import product_taxonomy
from app.web.business_presentation import (
    business_date, money_kvnd, money_text, percent,
)
from app.web.legacy_presentation import format_number

EMPTY = "—"

RECONCILED_NOTE = (
    "Bảng dưới đây đã được ĐỐI SOÁT với tổng của chính phạm vi đang xem: số "
    "dòng, doanh thu, số lượng và chiết khấu cộng lại khớp TUYỆT ĐỐI. Hàng "
    "TỔNG được tính trực tiếp từ lát dữ liệu, không cộng lại từ các hàng đang "
    "hiển thị — nên nó vẫn đúng kể cả khi bảng đang lọc."
)

RECONCILE_FAILED_NOTE = (
    "ĐỐI SOÁT KHÔNG KHỚP: các hàng của bảng cộng lại KHÁC tổng của phạm vi "
    "đang xem. Đây là lỗi hệ thống, không phải một sai số làm tròn — đừng dùng "
    "bảng này để ra quyết định cho tới khi nó khớp lại."
)

TOTAL_ROW_NOTE = (
    "Hàng TỔNG truy trực tiếp từ lát dữ liệu của phạm vi đang xem, KHÔNG cộng "
    "dọc các hàng phía trên. Nhờ vậy nó không tụt xuống theo những hàng bị ẩn "
    "bởi bộ lọc support, và một hàng bị bỏ rơi sẽ lộ ra ở phép đối soát thay "
    "vì biến mất im lặng."
)

TOTAL_ROW_NO_PRICE_NOTE = (
    "Hàng TỔNG cố ý không có giá bán bình quân: gộp giá của mọi nhóm lại cho ra "
    "một con số không mô tả bất cứ mặt hàng nào."
)

UNKNOWN_CATEGORY_NOTE = (
    "Phân tích CẶP NHÓM HÀNG chỉ dùng những dòng đã đọc được nhóm hàng từ "
    "Tracking. Dòng chưa xác định nhóm hàng (chưa khớp mã, xung đột mã, mã đã "
    "biến mất, ngoài bảng giá, hoặc Tracking chưa xếp) KHÔNG được coi là một "
    "nhóm hàng hoá — nên chúng không tạo cặp, không làm tăng ô \"đơn nhiều nhóm "
    "hàng hoá\", và không sinh ra attachment hay support giả. Tiền của chúng vẫn "
    "nằm ĐỦ trong mọi ô doanh thu và trong bảng cơ cấu theo nhóm hàng."
)

UNKNOWN_CATEGORY_COVERAGE_NOTE = (
    "Vì vậy phần phân tích bán chéo theo nhóm hàng CHƯA phủ hết phạm vi đang "
    "xem. Cách mở rộng độ phủ nằm ở đúng nơi có thẩm quyền: phân loại mã sản "
    "phẩm trên bảng kê nhân viên, hoặc xếp ngành hàng bên Tracking."
)

UNKNOWN_CATEGORY_COMPLETE_NOTE = (
    "Mọi đơn của phạm vi đang xem đều đã đọc được nhóm hàng cho toàn bộ dòng "
    "hàng hoá, nên phân tích cặp nhóm hàng phủ đủ phạm vi này."
)

DRILLDOWN_SCOPE_NOTE = (
    "Bảng kê này chỉ hiện Số BH, ngày bán, nhân viên, mặt hàng và phạm vi lọc "
    "đang áp dụng. Nó KHÔNG mở thêm một trường dữ liệu khách hàng nào — tên, "
    "số điện thoại và địa chỉ không đi qua trang này."
)

GROUP_COLUMNS: tuple[str, ...] = (
    "Nhóm", "Doanh thu (nghìn)", "Tỉ trọng", "SL", "Chiết khấu (nghìn)",
    "Số đơn", "Số dòng", "Giá BQ", "Giá thấp nhất", "Giá cao nhất",
)

PAIR_COLUMNS: tuple[str, ...] = (
    "Mặt hàng A", "Mặt hàng B", "Số đơn có cả hai", "A→B", "B→A",
    "Đơn có A", "Đơn có B", "Doanh thu đơn chứa cặp (nghìn)",
)

DRILLDOWN_COLUMNS: tuple[str, ...] = (
    "Số BH", "Ngày bán", "Nhân viên", "Mặt hàng",
)

#: Nhãn của bốn ô giỏ hàng, kèm câu nói ĐÚNG cái mỗi ô đếm. Viết cạnh nhau ở
#: đây để không ô nào bị đặt một cái tên gần giống ô bên cạnh.
BASKET_LABELS: tuple[tuple[str, str, str], ...] = (
    ("multi_line_orders", "Đơn nhiều dòng",
     "Đơn có từ HAI DÒNG hiệu lực trở lên — kể cả hai dòng cùng một mã."),
    ("multi_product_orders", "Đơn nhiều mặt hàng",
     "Đơn có từ HAI MÃ HÀNG KHÁC NHAU trở lên, chỉ tính dòng hàng bán và phụ "
     "kiện/quà tặng. Hai dòng cùng một mã KHÔNG làm đơn thành nhiều mặt hàng."),
    ("multi_merchandise_category_orders", "Đơn nhiều nhóm hàng hoá",
     "Đơn có từ HAI NHÓM HÀNG HOÁ KHÁC NHAU trở lên. Phí, chiết khấu, hoàn/hủy "
     "và chứng từ chưa định nghĩa KHÔNG được tính là một nhóm hàng hoá."),
    ("service_attachment_orders", "Đơn có dịch vụ kèm",
     "Đơn vừa có hàng hoá vừa có phí/dịch vụ. Một chứng từ chỉ gồm phí KHÔNG "
     "được tính vào đây."),
)


def _quantity(value: Optional[Decimal]) -> str:
    """Số lượng viết như một con số đếm, không phải một con số tiền."""
    if value is None:
        return EMPTY
    return format_number(value)


def money_cell(value: Optional[Decimal]) -> dict:
    """Một ô tiền: bản nghìn đồng để đọc, bản VND đầy đủ để đối chiếu.

    Hai bản trong CÙNG một dict để template không thể lấy bản rút gọn mà bỏ
    mất đường xem lại số gốc — cùng hợp đồng mà `gated_cell` đã dựng.
    """
    return {"text": money_text(value), "text_kvnd": money_kvnd(value),
            "missing": value is None}


def price_cell(value: Optional[Decimal], reason: Optional[str] = None) -> dict:
    """Một ô GIÁ. `None` ⟹ `—`, và `—` ở đây có nghĩa "không có giá bán hàng
    hoá để tính", KHÔNG có nghĩa "bằng 0". Một dòng phí hiện `—`; một nhóm có
    hàng tặng giá 0 hiện `0`, vì `0` là giá bán THẬT của nó (`OD-4`).

    `reason` là câu giải thích của CHÍNH ô ấy khi nó trống (repair
    `AR-R6-IR-03`): "không có hàng hoá" và "chưa đủ dữ liệu để chia" là hai
    trạng thái khác nhau, và chỉ một trong hai có chỗ sửa.
    """
    # `DEC-212` — bản NGHÌN ĐỒNG để đọc, bản VND đầy đủ để đối chiếu, cùng
    # hợp đồng hai-bản mà `money_cell` ngay trên đã dựng. Một ô GIÁ trước đây
    # chỉ có bản đầy đủ, nên nó là cột duy nhất trong bảng còn viết đủ sáu số
    # 0 cạnh những cột đã rút gọn.
    return {"text": money_kvnd(value), "text_full": money_text(value),
            "missing": value is None, "reason": reason}


def totals_cards(totals: dmx.DashboardTotals) -> list[dict]:
    """Các ô chỉ tiêu đầu trang Tổng quan (`R6 §2`).

    Mỗi ô mang sẵn câu giải thích của CHÍNH nó. `None` luôn đi kèm lý do —
    một ô trống không lý do là một ô người đọc tự điền lý do vào.
    """
    return [
        {"key": "sales_revenue", "label": "Doanh thu sau CK",
         "value": money_kvnd(totals.sales_revenue),
         "raw": money_text(totals.sales_revenue),
         "unit": "nghìn đồng",
         "missing": totals.sales_revenue is None,
         "note": ("Tổng doanh thu sau chiết khấu của các dòng đang được báo "
                  "cáo. Dòng Owner đã loại và dòng tạm loại KHÔNG có mặt.")},
        {"key": "gross_before_discount", "label": "Doanh số bán",
         "value": money_kvnd(totals.gross_before_discount),
         "raw": money_text(totals.gross_before_discount),
         "unit": "nghìn đồng",
         "missing": totals.gross_before_discount is None,
         "note": dmx.GROSS_DERIVED_NOTE},
        {"key": "discount_total", "label": "Chiết khấu",
         "value": money_kvnd(totals.discount_total),
         "raw": money_text(totals.discount_total),
         "unit": "nghìn đồng", "missing": False,
         "note": ("Tổng chiết khấu trên sổ, cộng ĐÚNG MỘT LẦN ở cấp dòng.")},
        {"key": "orders", "label": "Số đơn",
         "value": format_number(Decimal(totals.orders)), "raw": "",
         "unit": "đơn", "missing": False,
         "note": ("Số BH KHÁC NHAU trong phạm vi đang xem.")},
        {"key": "positive_revenue_orders", "label": "Đơn có doanh thu dương",
         "value": format_number(Decimal(totals.positive_revenue_orders)),
         "raw": "", "unit": "đơn", "missing": False,
         "note": ("Đơn có doanh thu sau CK lớn hơn 0. Đơn chưa tính được "
                  "doanh thu KHÔNG được đếm vào đây.")},
        {"key": "total_quantity", "label": "Tổng SL",
         "value": _quantity(totals.total_quantity), "raw": "",
         "unit": "", "missing": False, "note": dmx.QUANTITY_NOTE},
        {"key": "revenue_per_order", "label": "Doanh thu / đơn",
         "value": money_kvnd(totals.revenue_per_order),
         "raw": money_text(totals.revenue_per_order),
         "unit": "nghìn đồng",
         "missing": totals.revenue_per_order is None,
         "note": ("Doanh thu sau CK chia cho TỔNG số đơn — mẫu số là mọi đơn, "
                  "không riêng đơn có doanh thu dương.")},
        {"key": "lines_per_order", "label": "Dòng / đơn",
         "value": (EMPTY if totals.lines_per_order is None
                   else format_number(totals.lines_per_order)),
         "raw": "", "unit": "", "missing": totals.lines_per_order is None,
         "note": ("Số dòng hiệu lực chia cho số đơn.")},
        {"key": "multi_line_orders", "label": "Đơn nhiều dòng",
         "value": format_number(Decimal(totals.multi_line_orders)), "raw": "",
         "unit": "đơn", "missing": False,
         "note": BASKET_LABELS[0][2]},
        {"key": "orders_with_multiple_sale_dates",
         "label": "Đơn có nhiều ngày bán",
         "value": format_number(
             Decimal(totals.orders_with_multiple_sale_dates)),
         "raw": "", "unit": "đơn", "missing": False,
         "note": dmx.MULTI_DATE_NOTE},
    ]


def data_quality(totals: dmx.DashboardTotals) -> list[dict]:
    """Những chỗ phạm vi này CHƯA nói được, kèm số dòng/đơn cụ thể.

    Chỉ trả về các mục KHÁC 0: một danh sách toàn số 0 làm người đọc lướt qua
    cả khối, và khi một con số khác 0 xuất hiện thì nó cũng bị lướt qua.
    """
    items = [
        (totals.undated_lines, "dòng không có ngày bán",
         "Chúng không rơi vào mốc nào của biểu đồ, đúng như chúng đã không "
         "thuộc kỳ nào. Tiền của chúng vẫn nằm đủ trong tổng của phạm vi."),
        (totals.orders_without_date, "đơn không có ngày bán nào",
         "Không dòng nào của đơn có ngày bán, nên đơn không rơi vào mốc nào "
         "của biểu đồ số đơn."),
        (totals.lines_missing_revenue, "dòng chưa có doanh thu",
         "Chưa biết doanh thu KHÁC doanh thu bằng 0 — chúng không được cộng "
         "như số 0 vào bất kỳ ô nào, và cũng không tham gia MỘT VẾ NÀO của "
         "phép chia giá bán bình quân (repair AR-R6-IR-03)."),
        (totals.lines_missing_quantity, "dòng chưa có số lượng",
         "Chúng không góp vào Tổng SL, và không góp vào tử số lẫn mẫu số của "
         "giá bán bình quân."),
        (totals.orders_with_multiple_sale_dates, "đơn có nhiều ngày bán",
         dmx.MULTI_DATE_NOTE),
    ]
    return [{"count": value, "label": label, "note": note}
            for value, label, note in items if value]


def group_rows(
    rows: list[pmx.GroupRow], company: dmx.DashboardTotals,
) -> list[dict]:
    """Bảng gộp theo một chiều + hàng `TỔNG` (`R6 §3`).

    Hàng TỔNG đọc `company` — kết quả `dashboard_metrics.totals` trên CHÍNH lát
    dữ liệu — chứ không cộng dọc các hàng phía trên. Xem `TOTAL_ROW_NOTE`.
    """
    whole = company.sales_revenue
    out = [
        {"key": row.bucket.key, "label": row.bucket.label,
         "known": row.bucket.known, "reason": row.bucket.reason,
         "total_row": False,
         "revenue": money_cell(row.revenue),
         "share": {"text": percent(pmx.share_percent(row.revenue, whole)),
                   "missing": pmx.share_percent(row.revenue, whole) is None},
         "quantity": _quantity(row.quantity),
         "discount": money_cell(row.discount),
         "orders": format_number(Decimal(row.orders)),
         "lines": format_number(Decimal(row.lines)),
         "average_price": price_cell(row.prices.average,
                                     row.prices.average_reason),
         "min_price": price_cell(row.prices.minimum),
         "max_price": price_cell(row.prices.maximum),
         "priced_lines": row.prices.priced_lines,
         "has_merchandise": row.prices.has_merchandise}
        for row in rows
    ]
    out.append({
        "key": "", "label": "TỔNG", "known": True, "reason": None,
        "total_row": True,
        "revenue": money_cell(company.sales_revenue),
        "share": {"text": percent(pmx.share_percent(whole, whole)),
                  "missing": pmx.share_percent(whole, whole) is None},
        "quantity": _quantity(company.total_quantity),
        "discount": money_cell(company.discount_total),
        "orders": format_number(Decimal(company.orders)),
        "lines": format_number(Decimal(company.lines)),
        # Hàng TỔNG KHÔNG có giá bán bình quân của riêng nó: gộp giá của mọi
        # nhóm lại cho ra một con số không mô tả bất cứ mặt hàng nào. Ba ô giá
        # ở hàng này cố ý để trống.
        "average_price": price_cell(None, TOTAL_ROW_NO_PRICE_NOTE),
        "min_price": price_cell(None),
        "max_price": price_cell(None),
        "priced_lines": 0,
        "has_merchandise": False,
    })
    return out


def group_summary(
    reconciliation: pmx.GroupReconciliation, coverage, *,
    dimension: str, scope_label: str, totals: dmx.DashboardTotals,
) -> dict:
    """Đầu trang bảng gộp — phép đối soát ĐÃ CHẠY, không phải lời hứa."""
    return {
        "dimension": dimension,
        "dimension_label": product_taxonomy.dimension_label(dimension),
        "scope_label": scope_label,
        "reconciled": reconciliation.is_exact,
        "reconcile_note": (RECONCILED_NOTE if reconciliation.is_exact
                           else RECONCILE_FAILED_NOTE),
        "reconcile_detail": [
            {"metric": "Số dòng", "ok": reconciliation.lines},
            {"metric": "Doanh thu", "ok": reconciliation.sales_revenue},
            {"metric": "Số lượng", "ok": reconciliation.quantity},
            {"metric": "Chiết khấu", "ok": reconciliation.discount},
        ],
        "matched_lines": coverage.matched_lines,
        "total_lines": coverage.total_lines,
        "metadata_complete": coverage.is_complete,
        "undecided": [
            {"state": state, "count": value,
             "label": product_taxonomy.UNDECIDED_LABELS[state],
             "reason": product_taxonomy.UNDECIDED_REASONS[state]}
            for state, value in coverage.by_state
        ],
        "empty": totals.lines == 0,
        "source_note": product_taxonomy.TAXONOMY_SOURCE_NOTE,
        "taxonomy_note": product_taxonomy.CATEGORY_TAXONOMY_NOTE,
        "orders_note": product_taxonomy.ORDERS_COLUMN_NOTE,
        "total_row_note": TOTAL_ROW_NOTE,
    }


def basket_cards(counts: bkm.BasketCounts) -> list[dict]:
    """Bốn ô giỏ hàng — bốn tập đơn khác nhau, bốn câu giải thích khác nhau."""
    rates = {
        "multi_line_orders": counts.multi_line_rate,
        "multi_product_orders": counts.multi_product_rate,
        "multi_merchandise_category_orders": counts.multi_category_rate,
        "service_attachment_orders": counts.service_attachment_rate,
    }
    return [
        {"key": key, "label": label, "note": note,
         "value": format_number(Decimal(getattr(counts, key))),
         "rate": percent(rates[key]),
         "rate_missing": rates[key] is None}
        for key, label, note in BASKET_LABELS
    ]


def pair_rows(pairs: list[bkm.Pair]) -> list[dict]:
    """Bảng cặp — support ghi thành CỘT, hai chiều attachment tách rời.

    `left_known`/`right_known` đi kèm (repair `FIND-R6-IR-02`): ở chiều NHÓM
    HÀNG chúng luôn `True` theo cấu tạo, còn ở chiều SẢN PHẨM chúng cho template
    nói ra rằng một ô là tên thô CHƯA XÁC ĐỊNH thay vì để nó trông y hệt một
    model canonical của Tracking. Hai cờ này KHÔNG tham gia một phép đếm nào.
    """
    return [
        {"left": pair.left, "right": pair.right,
         "left_label": pair.left_label, "right_label": pair.right_label,
         "left_known": pair.left_known, "right_known": pair.right_known,
         "pair_orders": format_number(Decimal(pair.pair_orders)),
         "support": pair.support,
         "attachment_left": percent(pair.attachment_left_to_right),
         "attachment_right": percent(pair.attachment_right_to_left),
         "orders_with_left": format_number(Decimal(pair.orders_with_left)),
         "orders_with_right": format_number(Decimal(pair.orders_with_right)),
         "pair_revenue": money_cell(pair.pair_revenue)}
        for pair in pairs
    ]


def basket_summary(counts: bkm.BasketCounts, *, dimension: str,
                   scope_label: str, min_support: int,
                   shown_pairs: int) -> dict:
    return {
        "dimension": dimension,
        "dimension_label": product_taxonomy.dimension_label(dimension),
        "scope_label": scope_label,
        "orders": counts.orders,
        "min_support": min_support,
        "shown_pairs": shown_pairs,
        "empty": counts.orders == 0,
        "metric_note": bkm.MULTI_METRIC_NOTE,
        "pair_revenue_note": bkm.PAIR_REVENUE_NOTE,
        "attachment_note": bkm.ATTACHMENT_NOTE,
        "support_note": bkm.SUPPORT_NOTE,
        # Repair `FIND-R6-IR-02` — độ phủ của chiều nhóm hàng, nói bằng CON SỐ.
        # Không một trường nào ở đây đến từ dữ liệu khách hàng: chúng là hai
        # phép đếm trên khoá đơn và số dòng.
        "unknown_category_orders": counts.orders_with_unknown_category,
        "unknown_category_lines": counts.unknown_category_lines,
        "unknown_category_rate": percent(counts.unknown_category_order_rate),
        "category_coverage_complete": counts.category_coverage_complete,
        "unknown_category_note": UNKNOWN_CATEGORY_NOTE,
        "unknown_category_coverage_note": (
            UNKNOWN_CATEGORY_COMPLETE_NOTE if counts.category_coverage_complete
            else UNKNOWN_CATEGORY_COVERAGE_NOTE),
    }


def drilldown_rows(details: list[dict], metadata: list) -> list[dict]:
    """Bảng kê drill-down — ĐÚNG bốn cột, không một trường nào khác.

    Hàm này là chỗ hàng rào dữ liệu cá nhân của R6 được thi hành, và nó được
    thi hành bằng CẤU TẠO: dict trả về chỉ có bốn khoá, nên không template nào
    render được `customer_name`/`customer_phone`/`customer_address` — kể cả khi
    `details` mang sẵn ba trường đó (`business_queries` đọc chúng cho bảng kê
    nghiệp vụ, `DEC-PHB02-08`).

    Bài canh thật là `tests/test_r6_dashboard_vertical.py::
    test_the_drilldown_never_renders_a_customer_field`, và nó đo trên chính
    HTML đã render chứ trên kết quả của hàm này (đính chính `COR-R6-IR-01`:
    chú thích cũ dẫn một file `tests/test_r6_drilldown_boundary.py` KHÔNG tồn
    tại).

    Nhãn mặt hàng đọc từ `LineMetadata` đã giải sẵn — không tra lại tầng
    taxonomy ở đây, vì một phép tra thứ hai là chỗ hai màn hình gọi cùng một
    mặt hàng bằng hai cái tên.
    """
    if len(details) != len(metadata):
        raise ValueError(
            f"details ({len(details)}) và metadata ({len(metadata)}) phải cùng "
            "độ dài")
    rows = []
    for detail, item in zip(details, metadata):
        label = (item.model_label or item.tracking_code
                 or detail.get("product_raw") or detail["product_key"])
        rows.append({
            "order_key": detail["order_key"],
            "sale_date": business_date(detail.get("sale_date")),
            "employee": detail["line"].employee or "Chưa xác định nhân viên",
            "product": label,
        })
    rows.sort(key=lambda row: (row["order_key"], row["product"]))
    return rows


__all__ = [
    "BASKET_LABELS", "DRILLDOWN_COLUMNS", "DRILLDOWN_SCOPE_NOTE",
    "GROUP_COLUMNS", "PAIR_COLUMNS", "RECONCILED_NOTE",
    "RECONCILE_FAILED_NOTE", "TOTAL_ROW_NOTE", "TOTAL_ROW_NO_PRICE_NOTE",
    "UNKNOWN_CATEGORY_COMPLETE_NOTE", "UNKNOWN_CATEGORY_COVERAGE_NOTE",
    "UNKNOWN_CATEGORY_NOTE", "basket_cards",
    "basket_summary", "data_quality", "drilldown_rows", "group_rows",
    "group_summary", "money_cell", "pair_rows", "price_cell", "totals_cards",
]
