"""Khoá và fingerprint cấp dòng — thuần Python, không I/O, không DB.

Toàn bộ module này là hàm thuần trên giá trị nguồn. Nó KHÔNG biết database,
không biết Flask, và không import ``app/modules/**``: nhờ vậy "hai lần chạy
cùng dữ liệu có ra cùng khoá không" kiểm được bằng một test đơn vị chứ không
phải bằng một lần chạy end-to-end.

Hợp đồng khoá (TASK-PRA-002 mục 5.1, DEC-166/DEC-171):

    ORDER_KEY        = order_id của engine (Số BH, đã NFC + strip) — chuỗi opaque
    product_key      = sha256(NFC(product_raw).strip()); product_raw None → sha256("")
    occurrence_index = 1..n theo source_row tăng dần trong (snapshot, ORDER_KEY, product_key)
    ORDER_LINE_KEY   = (ORDER_KEY, product_key, occurrence_index)

KHÔNG chuẩn hoá thêm (upper/casefold/bỏ dấu) trên ORDER_KEY: engine nhóm đơn
bằng đúng chuỗi đó, nên chuẩn hoá khác đi sẽ tạo ra một khoá lưu trữ KHÁC khoá
nghiệp vụ và dự án có hai "sự thật" về cùng một đơn.
"""

from __future__ import annotations

import hashlib
import re
import unicodedata
from datetime import date
from decimal import Decimal
from typing import Optional, Sequence

# Các trường nguồn nghiệp vụ tạo nên ``line_fingerprint`` (mục 5.2). PII
# (`customer`, `customer_code`, `phone`, `address`, `shipper_raw`) và vị trí
# dòng (`source_row`, `source_file`, `row_hash`) KHÔNG nằm trong đây: kế toán
# đổi tên khách hay chèn thêm một dòng phía trên KHÔNG phải là "dòng bán này
# đã bị sửa".
FINGERPRINT_FIELDS = (
    "sale_date", "product_raw", "quantity", "sell_price", "discount",
    "total_sales_raw", "delivery_cost", "imei", "note_raw", "employee_raw",
    "source_profit",
)

# Đúng ba trường F3 của ``result_fingerprint``, theo ĐÚNG thứ tự tham số của
# hàm đó. Tên nằm ở đây để diff RESULT_REVISED và fingerprint không bao giờ nói
# về hai tập trường khác nhau.
RESULT_FIELDS = ("status", "accounting_purchase_price", "eligible_kpi_profit")

_BH_NUMBER = re.compile(r"^BH(\d+)$")

_SEPARATOR = "\x1f"


def canon(value) -> str:
    """Dạng chuẩn của MỘT giá trị nguồn, dùng chung cho fingerprint và diff.

    ``Decimal`` được chuẩn hoá về cùng một chuỗi khi bằng nhau về giá trị:
    ``1000``, ``1000.0`` và ``1E+3`` là cùng một số tiền, và một lần export
    khác định dạng số KHÔNG được biến thành "kế toán đã sửa dòng này".
    """
    if value is None:
        return ""
    if isinstance(value, bool):  # trước int — bool là int trong Python
        return "1" if value else "0"
    if isinstance(value, Decimal):
        return format(value.normalize(), "f")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str):
        return unicodedata.normalize("NFC", value).strip()
    return str(value)


def product_key(product_raw: Optional[str]) -> str:
    """sha256 của tên hàng đã NFC+strip. ``None`` → sha256 của chuỗi rỗng.

    KHÔNG casefold, KHÔNG bỏ dấu (D9 DEFER): hoa/thường là một khác biệt có
    thể có nghĩa trong sổ kế toán, và gộp chúng lại là một quyết định nghiệp
    vụ chưa có bằng chứng nào yêu cầu.
    """
    return hashlib.sha256(canon(product_raw).encode("utf-8")).hexdigest()


def bh_parts(order_key: str, sale_date: Optional[date]) -> tuple[Optional[int], Optional[int]]:
    """``(bh_number, bh_year_hint)`` — chỉ để GIỮ ĐƯỜNG NÂNG CẤP (F4).

    Hai giá trị này không tham gia reconcile ở PRA-002. Chúng tồn tại để, nếu
    sau này chứng minh được BH reset theo năm, có sẵn dữ liệu tách namespace
    mà không phải đọc lại toàn bộ workbook lịch sử. Số BH không đúng dạng
    ``BH<digits>`` → ``None``, không đoán.
    """
    match = _BH_NUMBER.match(order_key or "")
    number = int(match.group(1)) if match else None
    return number, (sale_date.year if sale_date is not None else None)


def line_fingerprint(values: Sequence) -> str:
    """sha256 của bộ trường nguồn nghiệp vụ, theo đúng thứ tự FINGERPRINT_FIELDS."""
    return hashlib.sha256(
        _SEPARATOR.join(canon(value) for value in values).encode("utf-8")
    ).hexdigest()


def result_fingerprint(status: str, accounting_purchase_price, eligible_kpi_profit) -> str:
    """Đúng BA trường mà F3 dùng để phát hiện RESULT_REVISED — không hơn.

    ``price_source`` đổi nhãn trong khi con số không đổi KHÔNG phải là "kết
    quả đã sửa"; đưa nó vào đây sẽ tạo ra cờ nhiễu mà người kiểm học cách bỏ
    qua (PRA-000 mục O).
    """
    return hashlib.sha256(_SEPARATOR.join((
        canon(status), canon(accounting_purchase_price), canon(eligible_kpi_profit),
    )).encode("utf-8")).hexdigest()


def changed_fields(before: Sequence, after: Sequence,
                   fields: Sequence[str] = FINGERPRINT_FIELDS) -> dict:
    """``{field: {"old": ..., "new": ...}}`` cho mọi trường có ``canon`` khác.

    Giá trị ghi ra là dạng ``canon`` — chính thứ đã quyết định fingerprint —
    nên "vì sao hệ thống coi đây là thay đổi" đọc được trực tiếp từ bản ghi,
    không phải suy đoán lại.
    """
    diff = {}
    for name, old, new in zip(fields, before, after):
        old_text, new_text = canon(old), canon(new)
        if old_text != new_text:
            diff[name] = {"old": old_text, "new": new_text}
    return diff
