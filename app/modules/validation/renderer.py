"""Render văn bản cho người đọc — HÀM THUẦN, đầu vào chỉ có payload + provenance.

**Vì sao module này tồn tại (DEC-134, RC-2).** Architecture Closure Audit đo
được tại `2d1da98`:

    ReviewItem(message="Nhân viên X có vấn đề ở dòng 7777",
               provenance=rows(6))            -> dựng được

Item sở hữu dòng 6 nhưng khẳng định dòng 7777, và object vẫn hợp lệ. Review
Queue là sản phẩm cho **con người** duyệt; một message nói sai dòng vẫn là sai
provenance đối với người duyệt, bất kể có ai parse nó hay không.

Cách đóng **không** phải là cấm từ "dòng", cũng không phải regex quét text —
cả hai đều là kiểm soát văn bản, và văn bản thì luôn viết được câu thứ N+1.
Cách đóng là: **không ai truyền message vào nữa**. Message được SINH ra ở đây,
từ đúng hai thứ:

    - `Diagnostics` — payload có kiểu của chính finding;
    - `RowProvenance` — tập dòng canonical của chính finding.

Renderer không có đầu vào nào khác, nên nó **không thể** nêu một dòng nằm
ngoài provenance: nó không có cách nào biết tới dòng đó.

Mọi con số nói về "bao nhiêu dòng" đều đọc từ `provenance`, không đọc từ một
counter song song — đó là RC-3 áp cho tầng văn bản.
"""

from __future__ import annotations

from app.modules.validation.models import (
    CATEGORY_DUPLICATE,
    CATEGORY_EMPLOYEE_MAPPING,
    CATEGORY_MISSING,
    CATEGORY_MISSING_PURCHASE_PRICE,
    CATEGORY_ORDER_INCONSISTENCY,
    CATEGORY_SOURCE_CLASSIFICATION,
    CATEGORY_SUSPICIOUS,
    CATEGORY_SUSPICIOUS_ERP,
    Diagnostics,
    RowProvenance,
)


def _rows(provenance: RowProvenance) -> str:
    return ", ".join(str(row) for row in provenance.source_rows)


def _employee_mapping(diag: Diagnostics, prov: RowProvenance) -> str:
    """F2–F6. Chuỗi phải giống hệt bản đã ký ở CHECK-108A1-15.

    F1 không còn ở đây: master có group hỏng nay bị từ chối tại biên loader,
    nên trạng thái đó không tới được Review Queue (HD-110-17).
    """
    criterion = diag.criterion

    if criterion == "F2":
        if diag.f2_reason == "inactive":
            return f"F2 — {diag.employee!r} `active: false`, không có dòng nào: đúng kỳ vọng"
        if diag.f2_reason == "out_of_range":
            return (
                f"F2 — {diag.employee!r} hiệu lực {diag.window_start}..{diag.window_end}, "
                "ngoài phạm vi dữ liệu: đúng kỳ vọng, không phải lỗi"
            )
        return (
            f"F2 — {diag.employee!r} (raw_prefix {diag.raw_prefix!r}) đang hiệu lực "
            "trong kỳ nhưng không khớp dòng nào. Có thể là sai prefix, cũng có thể "
            "chỉ là không có doanh số — cần người xem."
        )

    if criterion == "F3":
        return (
            f"F3 — {diag.raw_value!r} khớp nhiều nhân viên cùng hiệu lực tại ngày "
            f"của dòng đó: {sorted(diag.matched_employees)}"
        )

    if criterion == "F4":
        # `provenance.affected_count`, KHÔNG phải một counter song song: đây
        # chính là chỗ Audit đo được message nói "50 dòng" trong khi provenance
        # nói 0 (RC-3).
        return (
            f"F4 — {diag.raw_value!r} chưa map nhưng có {prov.affected_count} dòng, "
            f"≥ nhân viên nhỏ nhất đã map ({diag.smallest_employee}: "
            f"{diag.smallest_count}). Dấu hiệu master data thiếu người đáng kể — "
            "chẩn đoán, không phải kết luận."
        )

    if criterion == "F5":
        return (
            "F5 — KHÔNG nhân viên nào map được dòng nào. Mapping production hỏng "
            "hoàn toàn."
        )

    if criterion == "F6":
        return (
            f"F6 — bản ghi {diag.employee!r} (raw_prefix {diag.raw_prefix!r}, hiệu "
            f"lực {diag.window_start}..{diag.window_end}) khai `active: false` nhưng "
            f"có {prov.affected_count} dòng rơi đúng vào cửa sổ hiệu lực của nó. "
            "Master data mâu thuẫn: nếu người này đã nghỉ thì `effective_to` phải "
            "đóng trước các dòng đó. Doanh số vẫn đang tính cho họ — cần người xem."
        )

    raise ValueError(f"Không có renderer cho criterion {criterion!r}")


_MISSING_LABELS = {
    "date": "ngày",
    "order_id": "OrderID",
    "employee": "nhân viên",
    "quantity": "số lượng",
    "total_sales": "doanh số",
}


def _missing(diag: Diagnostics, prov: RowProvenance) -> str:
    return f"Thiếu {_MISSING_LABELS.get(diag.rule, diag.rule)}."


def _missing_purchase_price(diag: Diagnostics, prov: RowProvenance) -> str:
    return (
        f"{prov.affected_count} dòng chưa có giá nhập kế toán (`price_source` = "
        "Pending). Phase 1 chưa có Price Master nên đây là trạng thái đúng, "
        "không phải lỗi dữ liệu — nhưng lợi nhuận của các dòng này chưa tính được."
    )


_SUSPICIOUS_TEXT = {
    "quantity_not_positive": lambda v: f"Số lượng ≤ 0 ({v}).",
    "sell_price_zero": lambda v: "Giá bán = 0.",
    "purchase_price_above_sell_price": lambda v: "Giá nhập lớn hơn giá bán.",
    "accounting_profit_negative": lambda v: f"Lợi nhuận kế toán âm ({v}).",
}


def _suspicious(diag: Diagnostics, prov: RowProvenance) -> str:
    render = _SUSPICIOUS_TEXT.get(diag.rule)
    if render is None:
        raise ValueError(f"Không có renderer cho rule {diag.rule!r}")
    return render(diag.observed_value)


def _suspicious_erp(diag: Diagnostics, prov: RowProvenance) -> str:
    return (
        f"ERP báo lợi nhuận âm ({diag.observed_value}). Tín hiệu từ ERP, CHƯA "
        "kiểm chứng — không dùng để suy ra giá nhập (DEC-103)."
    )


def _order_inconsistency(diag: Diagnostics, prov: RowProvenance) -> str:
    if diag.employees_found:
        return (
            f"Đơn {diag.order_id} có {len(diag.employees_found)} nhân viên khác nhau "
            "trên các dòng. Công cụ KHÔNG tự chọn chủ đơn — hiện `order_builder` lấy "
            "nhân viên của dòng đầu tiên, đó là hành vi legacy, KHÔNG phải quyền sở "
            "hữu đã được xác minh. Cần người quyết định."
        )
    return f"Đơn {diag.order_id} có {len(diag.dates_found)} ngày khác nhau trên các dòng."


def _source_classification(diag: Diagnostics, prov: RowProvenance) -> str:
    return (
        f"Đơn {diag.order_id}: override tay `{diag.manual_value}` khác kết quả rule "
        f"tự động `{diag.auto_value}`."
    )


def _duplicate(diag: Diagnostics, prov: RowProvenance) -> str:
    return (
        f"{prov.affected_count} dòng có nội dung giống hệt nhau (dòng {_rows(prov)}). "
        "Có thể hợp lệ — hai dòng phụ kiện giống nhau trong một đơn — cần người xem."
    )


_RENDERERS = {
    CATEGORY_EMPLOYEE_MAPPING: _employee_mapping,
    CATEGORY_MISSING: _missing,
    CATEGORY_MISSING_PURCHASE_PRICE: _missing_purchase_price,
    CATEGORY_SUSPICIOUS: _suspicious,
    CATEGORY_SUSPICIOUS_ERP: _suspicious_erp,
    CATEGORY_ORDER_INCONSISTENCY: _order_inconsistency,
    CATEGORY_SOURCE_CLASSIFICATION: _source_classification,
    CATEGORY_DUPLICATE: _duplicate,
}


def render_message(category: str, diagnostics: Diagnostics, provenance: RowProvenance) -> str:
    """Điểm vào duy nhất. Không nhận gì ngoài payload có kiểu và provenance."""
    try:
        renderer = _RENDERERS[category]
    except KeyError:
        raise ValueError(f"Không có renderer cho category {category!r}") from None
    return renderer(diagnostics, provenance)
