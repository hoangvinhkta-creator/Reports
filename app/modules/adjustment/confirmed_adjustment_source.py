"""Confirmed `KpiPurchaseAdjustment` source (DEC-144 §5, `OD-108B-02`).

Tách biệt HOÀN TOÀN khỏi `AdjustmentResolver` (TASK-106,
`adjustment_resolver.py`) — module đó chỉ tính `suggested_amount`, KHÔNG bao
giờ được coi là confirmed (DEC-125 điểm 4, DEC-126 điểm 5). Nguồn này chỉ chứa
record đã CONFIRMED thật, đọc read-only từ một file JSONL.

Ba trạng thái, không được gộp (DEC-144 §3 — "absence ≠ unknown ≠ zero"):

- UNAVAILABLE      — file thiếu / không đọc được / một dòng bất kỳ parse lỗi
  / vi phạm data-integrity (amount không finite, `order_id` trùng lặp).
  Fail-closed: một dòng hỏng không cho biết nó lẽ ra khớp order nào, nên
  không order nào trong file được coi là "đã xác định vắng mặt".
- LOADED, rỗng     — file tồn tại, mọi dòng hợp lệ, 0 record khớp một order
  cho trước -> DETERMINED_ABSENCE cho order đó (`lookup()` trả `None`, nhưng
  `is_available` là `True`).
- LOADED, có record — order đó có `ConfirmedAdjustmentRecord`.

`caller` (kpi_profit_engine) phân biệt UNAVAILABLE với LOADED-rỗng qua
`is_available` — KHÔNG suy từ `lookup()` trả `None` một mình, vì đó là kết quả
chung của cả hai trạng thái LOADED (không khớp) lẫn UNAVAILABLE.

## Data-integrity tối thiểu (Golden #1 Repair Batch #1, B03)

Hai vi phạm cheap-to-detect fail-closed toàn bộ nguồn, không chỉ dòng hỏng:

- `amount` không phải số hữu hạn (`NaN`/`Infinity`/`-Infinity`) — Python's
  `json` module chấp nhận các token này làm float hợp lệ, và `Decimal(str(x))`
  KHÔNG raise cho chúng (`Decimal("nan")`/`Decimal("inf")` là giá trị Decimal
  hợp lệ) — phải kiểm tra tường minh bằng `is_finite()`.
- `order_id` trùng lặp giữa hai dòng — record thứ hai KHÔNG được âm thầm ghi
  đè record thứ nhất; đây là dấu hiệu nguồn dữ liệu mâu thuẫn, không phải một
  correction hợp lệ (correction thật thuộc phạm vi persistence/writer, ngoài
  scope của loader read-only này — DEC-144 §5, brief §5 SCOPE GUARD).

`confirmed_at` là field bắt buộc tối thiểu (DEC-144 §4 — "effective date" là
một trong năm thứ bắt buộc xác định được khi adjustment tồn tại) — dùng để
làm provenance của một record đã match đủ để trỏ lại đúng dòng nguồn, không
chỉ một nhãn "Confirmed:<ai đó>" mơ hồ khi nhiều record cùng người xác nhận.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class ConfirmedAdjustmentRecord:
    order_id: str
    amount: Decimal
    confirmed_by: str
    confirmed_at: str
    reason: str = ""


class ConfirmedAdjustmentSource:
    """`records is None` nghĩa là UNAVAILABLE; `{}` nghĩa là LOADED rỗng."""

    def __init__(self, records: Optional[dict[str, ConfirmedAdjustmentRecord]]):
        self._records = records

    @property
    def is_available(self) -> bool:
        return self._records is not None

    def lookup(self, order_id: str) -> Optional[ConfirmedAdjustmentRecord]:
        if self._records is None:
            return None
        return self._records.get(order_id)


UNAVAILABLE = ConfirmedAdjustmentSource(records=None)


def load_confirmed_adjustments_from_jsonl(path: Path) -> ConfirmedAdjustmentSource:
    """File thiếu -> UNAVAILABLE (KHÔNG "loaded rỗng" — thiếu nguồn phải khác
    xác-định-không-có, DEC-144 §3). Một dòng hỏng, một `amount` không finite,
    hoặc một `order_id` trùng lặp bất kỳ -> toàn bộ nguồn UNAVAILABLE
    (fail-closed, xem docstring module)."""
    if not path.exists():
        return UNAVAILABLE
    try:
        raw_text = path.read_text(encoding="utf-8")
    except OSError:
        return UNAVAILABLE

    records: dict[str, ConfirmedAdjustmentRecord] = {}
    for raw_line in raw_text.splitlines():
        raw_line = raw_line.strip()
        if not raw_line:
            continue
        try:
            raw_record = json.loads(raw_line)
            order_id = raw_record["order_id"]
            amount = Decimal(str(raw_record["amount"]))
            if not amount.is_finite():
                return UNAVAILABLE
            if order_id in records:
                return UNAVAILABLE  # duplicate identity — fail closed, no silent overwrite
            records[order_id] = ConfirmedAdjustmentRecord(
                order_id=order_id,
                amount=amount,
                confirmed_by=raw_record["confirmed_by"],
                confirmed_at=raw_record["confirmed_at"],
                reason=raw_record.get("reason", ""),
            )
        except (json.JSONDecodeError, KeyError, InvalidOperation, TypeError):
            return UNAVAILABLE
    return ConfirmedAdjustmentSource(records=records)
