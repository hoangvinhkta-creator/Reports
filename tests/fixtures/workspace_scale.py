"""Fixture QUY MÔ cho không gian làm việc — 100 / 3.000 / 5.000 dòng.

Vì sao file này tồn tại: mọi ngân sách của brief (payload, số DOM row, thời
gian mở panel) chỉ có nghĩa trên một khối lượng dữ liệu ĐẠI DIỆN. Một test
dựng ba dòng sẽ xanh với mọi kiến trúc, kể cả kiến trúc dựng 6,37 MB HTML
cho một lần mở đơn.

Fixture này KHÔNG phải một bộ số nghiệp vụ mới. Nó gọi đúng
`tests.test_snapshot_repository.source_line`/`result_line`/`write` mà bộ
test hiện có đã dùng, nên mọi ràng buộc của tầng lưu (khoá dòng, fingerprint,
provenance) vẫn được thi hành y nguyên — chỉ số lượng là khác.

## Những hình dạng dữ liệu được cài sẵn có chủ đích

Brief §10 "Dữ liệu" liệt kê các ca phải có mặt, nên chúng được cài vào
chính fixture này thay vì để mỗi test tự dựng lại:

    đơn nhiều dòng        `LINES_PER_ORDER_CYCLE` — 1, 2, 3 rồi lặp lại
    dòng lặp              cùng `product_key`, `occurrence_index` tăng
    giá bằng 0            mỗi đơn thứ 17 có một dòng `sell_price = 0`
    giá null              mỗi đơn thứ 23 có `kpi_purchase_price = None`
    thiếu Daily MIN       mỗi đơn thứ 29 mang `status = "PENDING"` +
                          `pending_reasons` nói rõ thiếu nguồn giá
    hai nhân viên/sheet   xen kẽ theo đơn, để bảng có nhiều hơn một sheet

Các con số trên là số NGUYÊN TỐ khác nhau một cách có chủ đích: chúng
không chia hết cho nhau, nên hai hình dạng không âm thầm luôn rơi vào cùng
một đơn và che nhau.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from tests.test_snapshot_repository import result_line, source_line, write

#: Kỳ của mọi fixture ở đây. Cố định để expected totals không đổi theo ngày
#: chạy test — xem `TODAY` của `tests/test_employee_workspace_ux.py`.
YEAR, MONTH = 2026, 9
PERIOD = {"date_from": date(YEAR, MONTH, 1), "date_to": date(YEAR, MONTH, 30)}
PERIOD_TEXT = f"{YEAR}-{MONTH:02d}"

#: Hai nhân viên ⟹ hai sheet nhân viên trên màn hình.
EMPLOYEES = ("Vinh", "Ly")

#: Số dòng của các đơn, lặp theo chu kỳ này.
LINES_PER_ORDER_CYCLE = (1, 2, 3)

#: Chu kỳ cài các ca dữ liệu đặc biệt (xem docstring).
ZERO_PRICE_EVERY = 17
NULL_PURCHASE_EVERY = 23
PENDING_SOURCE_EVERY = 29


def _order_key(index: int) -> str:
    """Mã đơn ỔN ĐỊNH theo chỉ số — cùng chỉ số cho cùng mã, mọi lần chạy."""
    return f"BH{70000 + index}"


def build_pairs(total_lines: int) -> list[tuple]:
    """`total_lines` cặp `(dòng nguồn, dòng kết quả)`, gộp thành các đơn.

    Trả về ĐÚNG `total_lines` dòng: đơn cuối bị cắt ngắn nếu chu kỳ vượt
    quá — số dòng là con số mà ngân sách nói về, nên nó phải khớp chính
    xác chứ không "khoảng chừng".
    """
    pairs: list[tuple] = []
    order_index = 0
    while len(pairs) < total_lines:
        order_index += 1
        order = _order_key(order_index)
        employee = EMPLOYEES[order_index % len(EMPLOYEES)]
        lines = LINES_PER_ORDER_CYCLE[order_index % len(LINES_PER_ORDER_CYCLE)]
        # Ngày bán trải đều trong tháng để biểu đồ/nền xen kẽ theo ngày có
        # dữ liệu thật ở mọi ngày, không dồn hết vào một ngày.
        day = 1 + (order_index % 28)
        zero_price = order_index % ZERO_PRICE_EVERY == 0
        null_purchase = order_index % NULL_PURCHASE_EVERY == 0
        pending = order_index % PENDING_SOURCE_EVERY == 0
        for line_index in range(lines):
            if len(pairs) >= total_lines:
                break
            # Dòng LẶP: cùng mặt hàng, `occurrence_index` tăng. Đây là ca
            # `(order_key, product_key, occurrence_index)` tồn tại để mô tả.
            product = f"SP-{(order_index % 40):02d}"
            occurrence = line_index + 1
            sell = "0" if (zero_price and line_index == 0) else str(
                1_000_000 + (order_index % 9) * 500_000)
            pairs.append(_pair(
                order=order, product=product, occurrence=occurrence,
                day=day, employee=employee, sell=sell,
                row=6 + len(pairs),
                null_purchase=null_purchase and line_index == 0,
                pending=pending and line_index == 0,
            ))
    return pairs


def _pair(*, order, product, occurrence, day, employee, sell, row,
          null_purchase, pending):
    source = source_line(
        order, product, occurrence, row=row,
        sale_date=date(YEAR, MONTH, day), sell_price=sell,
        quantity=Decimal("1"), discount=Decimal("0"),
        customer_name=f"Khách {order}", customer_phone="0912000111",
        customer_address="12 Lê Lợi, Quận 1, TP.HCM",
    )
    base = result_line(source, status="PENDING" if pending else "AUTO")
    fields = {name: getattr(base, name) for name in base.__dataclass_fields__}
    total = Decimal(sell)
    # Giá nhập `None` ⟹ KPI profit cũng `None`: thiếu giá vốn không phải
    # giá vốn bằng 0, nên lợi nhuận của dòng đó là CHƯA BIẾT, không phải
    # bằng doanh thu. Đây chính là ranh giới `null` ≠ `0` của brief §8.
    purchase = None if null_purchase else Decimal("600000")
    fields.update({
        "status": "PENDING" if pending else "AUTO",
        "pending_reasons": (
            ("TRACKING_DAILY_MIN_MISSING",) if pending else ()),
        "employee_normalized": employee,
        "employee_group": "NOI_THANH",
        "lead_source_final": "PERSONAL",
        "total_sales": total,
        "kpi_purchase_price": purchase,
        "eligible_kpi_profit": (
            None if purchase is None else max(Decimal(0), total - purchase)),
        "product_group_final": "DIEN_MAY",
        "conversion_rate_final": Decimal("0.020"),
    })
    return source, type(base)(**fields)


def persist(repository, pairs, *, run_id="run-scale",
            at="2026-10-01T00:00:00", fingerprint="fp-scale"):
    """Ghi fixture vào snapshot repo qua ĐÚNG đường ghi production."""
    return write(repository, [pair[0] for pair in pairs], run_id=run_id,
                 created_at=at, fingerprint=fingerprint,
                 results=[pair[1] for pair in pairs])


def install(repository, total_lines: int) -> list[tuple]:
    """Dựng + ghi `total_lines` dòng, trả lại các cặp đã ghi."""
    pairs = build_pairs(total_lines)
    persist(repository, pairs)
    return pairs


def order_keys(pairs) -> list[str]:
    """Các mã đơn có trong fixture, đúng thứ tự xuất hiện, không lặp."""
    seen: list[str] = []
    for source, _ in pairs:
        key = source.key.order_key
        if key not in seen:
            seen.append(key)
    return seen
