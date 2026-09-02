"""Từ kết quả pipeline authoritative → dòng nguồn + dòng kết quả của history.

Module này KHÔNG tính lại một business rule nào. Nó đọc đúng những gì
``export_report`` đã in ra XLSX (``present_lines`` → ``PresentedLine``) và
chép sang kiểu của tầng history. Nhờ vậy XLSX và database nói cùng một câu về
AUTO/PENDING — chỉ có MỘT nguồn sự thật, chứ không phải hai bản tính song song
rồi hy vọng chúng bằng nhau (TASK-PRA-002 mục 6).

Truy cập bằng thuộc tính, KHÔNG import ``app/modules/exporting`` — giữ cho
package ``app/history`` không phụ thuộc tầng xuất file.
"""

from __future__ import annotations

from typing import Optional, Sequence

from app.history.keys import bh_parts, line_fingerprint, product_key, result_fingerprint
from app.history.models import LineKey, ResultLine, SourceLine

# PII của khách hàng KHÔNG được rời khỏi tầng pipeline (mục 2 + mục 10):
# `customer`, `customer_code`, `phone`, `address`, `shipper_raw` không có mặt
# trong SourceLine/ResultLine, nên chúng không thể lọt vào bảng nào của
# PRA-002 kể cả do sơ ý sau này.


def build_source_lines(presented: Sequence) -> list[SourceLine]:
    """Dòng nguồn theo thứ tự ``source_row`` tăng dần, đã đánh occurrence_index.

    ``occurrence_index`` đếm theo (đơn, sản phẩm) trong PHẠM VI một snapshot:
    dữ liệu thật có đơn chứa hai dòng cùng tên hàng (ví dụ "Chi phí vận
    chuyển"), và nếu không có chỉ số này thì dòng thứ hai sẽ ghi đè dòng thứ
    nhất — mất một dòng bán trong im lặng.
    """
    ordered = sorted(presented, key=lambda view: view.line.raw.source_row)
    seen: dict[tuple[str, str], int] = {}
    lines: list[SourceLine] = []
    for view in ordered:
        raw = view.line.raw
        order_key = view.line.order_id
        pkey = product_key(raw.product_raw)
        occurrence = seen[(order_key, pkey)] = seen.get((order_key, pkey), 0) + 1
        number, year_hint = bh_parts(order_key, raw.date)
        values = (
            raw.date, raw.product_raw, raw.quantity, raw.sell_price, raw.discount,
            raw.total_sales_raw, raw.delivery_cost, raw.imei, raw.note_raw,
            raw.employee_raw, raw.source_profit,
        )
        lines.append(SourceLine(
            key=LineKey(order_key, pkey, occurrence),
            source_row=raw.source_row, row_hash=raw.row_hash,
            fingerprint=line_fingerprint(values),
            bh_number=number, bh_year_hint=year_hint,
            sale_date=raw.date, product_raw=raw.product_raw, quantity=raw.quantity,
            sell_price=raw.sell_price, discount=raw.discount,
            total_sales_raw=raw.total_sales_raw, delivery_cost=raw.delivery_cost,
            imei=raw.imei, note_raw=raw.note_raw, employee_raw=raw.employee_raw,
            source_profit=raw.source_profit,
        ))
    return lines


def build_result_lines(presented: Sequence, source_lines: Sequence[SourceLine]) -> list[ResultLine]:
    """Một ResultLine cho MỖI dòng nguồn, cùng thứ tự — kể cả dòng SAME.

    Dòng ``SAME`` vẫn có result version mới vì pipeline ĐÃ chạy lại thật với
    bằng chứng Tracking của lần này; "copy kết quả cũ sang" sẽ là một khẳng
    định không ai kiểm chứng được.
    """
    ordered = sorted(presented, key=lambda view: view.line.raw.source_row)
    results: list[ResultLine] = []
    for view, source in zip(ordered, source_lines):
        line = view.line
        record = view.record
        identity = getattr(record, "identity", None) if record is not None else None
        results.append(ResultLine(
            key=source.key,
            status=view.status,
            pending_reasons=tuple(view.reasons),
            total_sales=line.total_sales,
            employee_normalized=line.employee_normalized,
            employee_group=line.employee_group,
            lead_source_final=line.lead_source_final,
            identity_namespace=_namespace(identity),
            canonical_product_code=getattr(identity, "source_product_code", None),
            accounting_purchase_price=line.accounting_purchase_price,
            price_source=line.price_source,
            composition_rule=_rule(record),
            accounting_profit=line.accounting_profit,
            kpi_purchase_price=line.kpi_purchase_price,
            kpi_purchase_provenance=line.kpi_purchase_price_provenance,
            eligible_kpi_profit=line.eligible_kpi_profit,
            product_group_final=line.product_group_final,
            conversion_scheme_final=line.conversion_scheme_final,
            conversion_rate_final=line.conversion_rate_final,
            result_fingerprint=result_fingerprint(
                view.status, line.accounting_purchase_price, line.eligible_kpi_profit,
            ),
        ))
    return results


def _namespace(identity) -> Optional[str]:
    namespace = getattr(identity, "namespace", None)
    return getattr(namespace, "value", None) if namespace is not None else None


def _rule(record) -> Optional[str]:
    # `record` là None với dòng pre-cutover confirmed (exporter bỏ qua tra giá
    # cho nhánh đó) — không có rule để ghi, và bịa một nhãn ở đây sẽ tạo ra
    # provenance sai.
    rule = getattr(record, "rule", None) if record is not None else None
    return getattr(rule, "value", None) if rule is not None else None
