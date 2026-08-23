"""Group `WorkingLine`s into `Order`s by `OrderID` (Số BH).

Grouping only — this module does not decide `LeadSource` (that is
`app.modules.lead_source.classifier`, applied afterward once every line of
an order is known) and does not validate that every line of an order agrees
on date/employee. A real order with mismatched lines is a data-quality
finding for TASK-110's "Order inconsistency" review-queue category, not a
crash here: the builder deterministically takes the first line's values.
"""

from __future__ import annotations

from app.modules.domain.models import Order, WorkingLine


def build_orders(lines: list[WorkingLine]) -> list[Order]:
    grouped: dict[str, list[WorkingLine]] = {}
    for line in lines:
        grouped.setdefault(line.order_id, []).append(line)

    orders = []
    for order_id, order_lines in grouped.items():
        first = order_lines[0]
        orders.append(
            Order(
                order_id=order_id,
                date=first.date,
                employee_raw=first.employee_raw,
                employee_normalized=first.employee_normalized,
                employee_mapping_status=first.employee_mapping_status,
                lines=order_lines,
            )
        )
    return orders
