"""Kiểu dữ liệu của tầng history — thuần dataclass, không I/O.

Ba nhóm, cố ý tách rời vì chúng trả lời ba câu hỏi khác nhau:

``SourceLine``   — sổ kế toán NÓI GÌ về một dòng bán (trục NGUỒN).
``ResultLine``   — pipeline authoritative TÍNH RA GÌ trên dòng đó (trục KẾT QUẢ).
``CurrentState`` — hiện trạng đang lưu của một khoá, đầu vào của reconciler.

Trục nguồn và trục kết quả KHÔNG BAO GIỜ gộp: kế toán sửa sổ và Reports chạy
lại với bằng chứng Tracking mới là hai sự kiện khác nhau, và gộp chúng lại sẽ
làm mất chính thông tin mà bảng version sinh ra để giữ (TASK-PRA-002 mục 5/6).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional

# Ba mức coverage (mục 7.1). Tầng thuần sở hữu từ vựng nghiệp vụ; CHECK
# constraint trong ``tools/db/schema.py`` là hình chiếu DDL của chính nó, và
# một test buộc hai bên khớp nhau (không import chéo: app/history phải sạch
# SQLAlchemy theo ADR-101).
DETECTED_ONLY = "DETECTED_ONLY"
HEADER_CONSISTENT = "HEADER_CONSISTENT"
CONFIRMED_COMPLETE = "CONFIRMED_COMPLETE"
COVERAGE_STATES = (DETECTED_ONLY, HEADER_CONSISTENT, CONFIRMED_COMPLETE)

OUTCOME_INSERT = "INSERT"
OUTCOME_SAME = "SAME"
OUTCOME_SOURCE_CHANGED = "SOURCE_CHANGED"
OUTCOME_COLLISION = "ORDER_KEY_COLLISION"

FLAG_SOURCE_CHANGED = "SOURCE_CHANGED"
FLAG_COLLISION = "ORDER_KEY_COLLISION"
FLAG_NOT_SEEN = "NOT_SEEN_IN_LATEST_SNAPSHOT"
FLAG_REMOVED_CANDIDATE = "REMOVED_IN_SOURCE_CANDIDATE"

# Hai loại cờ nói về sự VẮNG MẶT của một khoá trong snapshot mới. Chúng khác
# mọi cờ khác ở một điểm: một cờ vắng mặt có thể bị chính lịch sử phủ nhận —
# khoá xuất hiện trở lại ở snapshot sau. Bản ghi cờ là BẤT BIẾN (append-only);
# việc "còn hiệu lực hay không" được DẪN XUẤT khi đọc, không bao giờ bằng cách
# sửa hay xoá lịch sử (mục 11 của chỉ thị slice B).
ABSENCE_FLAG_KINDS = (FLAG_NOT_SEEN, FLAG_REMOVED_CANDIDATE)

# Toàn bộ tập giá trị hợp lệ của hai cột enum. Slice A chỉ DỰNG được hai loại
# cờ đầu; ba loại còn lại thuộc slice B/C nhưng phải có mặt trong từ vựng để
# schema không phải đổi CHECK constraint giữa các slice.
OUTCOMES_ALL = (OUTCOME_INSERT, OUTCOME_SAME, OUTCOME_SOURCE_CHANGED, OUTCOME_COLLISION)
FLAG_KINDS_ALL = (
    "SOURCE_CHANGED", "NOT_SEEN_IN_LATEST_SNAPSHOT",
    "REMOVED_IN_SOURCE_CANDIDATE", "RESULT_REVISED", "ORDER_KEY_COLLISION",
)

# Cùng Số BH mà ngày bán lệch quá ngưỡng này → KHÔNG reconcile (mục 8 bước 2).
# Đây là fail-safe cho UNKNOWN "BH có reset theo năm không" (D2): thà dừng lại
# và hiện một cờ còn hơn âm thầm coi hai đơn khác nhau là một.
COLLISION_DAY_THRESHOLD = 90


@dataclass(frozen=True)
class LineKey:
    order_key: str
    product_key: str
    occurrence_index: int


@dataclass(frozen=True)
class CurrentKey:
    """Một khoá ĐANG hiện hành, rút gọn về đúng ba thứ bước 4/R cần biết.

    Không mang tiền, không mang fingerprint: so sánh vắng mặt chỉ hỏi "khoá
    này có trong snapshot mới không" và "nó có nằm trong phạm vi mà snapshot
    đó thực sự đại diện không" — chứ không hỏi giá trị của nó có đổi không.
    """

    key: LineKey
    sale_date: Optional[date]
    order_key_collision: bool = False


@dataclass(frozen=True)
class SourceLine:
    """Một dòng nguồn của MỘT snapshot, đã tính khoá và fingerprint."""

    key: LineKey
    source_row: int
    row_hash: str
    fingerprint: str
    bh_number: Optional[int]
    bh_year_hint: Optional[int]

    sale_date: Optional[date]
    product_raw: Optional[str]
    quantity: Optional[Decimal]
    sell_price: Optional[Decimal]
    discount: Optional[Decimal]
    total_sales_raw: Optional[Decimal]
    delivery_cost: Optional[Decimal]
    imei: Optional[str]
    note_raw: Optional[str]
    employee_raw: Optional[str]
    source_profit: Optional[Decimal]

    @property
    def fingerprint_values(self) -> tuple:
        """Đúng thứ tự ``keys.FINGERPRINT_FIELDS`` — dùng cho diff changed_fields."""
        return (
            self.sale_date, self.product_raw, self.quantity, self.sell_price,
            self.discount, self.total_sales_raw, self.delivery_cost, self.imei,
            self.note_raw, self.employee_raw, self.source_profit,
        )


@dataclass(frozen=True)
class ResultLine:
    """Kết quả pipeline cho một khoá trong MỘT run. Không có PII."""

    key: LineKey
    status: str
    pending_reasons: tuple[str, ...]
    total_sales: Optional[Decimal]
    employee_normalized: Optional[str]
    employee_group: Optional[str]
    lead_source_final: Optional[str]
    identity_namespace: Optional[str]
    canonical_product_code: Optional[str]
    accounting_purchase_price: Optional[Decimal]
    price_source: str
    composition_rule: Optional[str]
    accounting_profit: Optional[Decimal]
    kpi_purchase_price: Optional[Decimal]
    kpi_purchase_provenance: str
    eligible_kpi_profit: Optional[Decimal]
    product_group_final: Optional[str]
    conversion_scheme_final: Optional[str]
    conversion_rate_final: Optional[Decimal]
    result_fingerprint: str


@dataclass(frozen=True)
class CurrentState:
    """Hiện trạng đã lưu của một khoá — đầu vào đọc-chỉ của reconciler.

    ``version_no`` là version ĐANG là hiện hành; ``max_version_no`` là version
    LỚN NHẤT đã từng ghi cho khoá này. Hai số đó KHÁC nhau sau một
    ``ORDER_KEY_COLLISION``: bản ghi collision được lưu nhưng không được làm
    hiện hành, nên hiện hành tụt lại phía sau. Version mới phải đánh số theo
    ``max`` (mục 5.3), nếu không lần ghi sau sẽ đụng UNIQUE
    ``(khoá, version_no)`` và cả lần chạy bị rollback.
    """

    source_version_id: int
    version_no: int
    fingerprint: str
    sale_date: Optional[date]
    fingerprint_values: tuple
    order_key_collision: bool = False
    first_seen_snapshot_id: Optional[str] = None
    max_version_no: Optional[int] = None

    @property
    def next_version_no(self) -> int:
        """Số version kế tiếp = max đã ghi + 1 (mục 5.3)."""
        highest = self.version_no if self.max_version_no is None else self.max_version_no
        return max(highest, self.version_no) + 1


@dataclass(frozen=True)
class Decision:
    """Quyết định reconcile cho MỘT khoá của snapshot mới.

    ``version_no`` là số version nguồn mà dòng này TRỎ TỚI sau khi ghi:
    version mới với INSERT/SOURCE_CHANGED/COLLISION, version hiện hành với
    SAME. ``becomes_current`` là False đúng ở nhánh COLLISION — bản ghi vẫn
    được lưu đầy đủ nhưng KHÔNG được phép thay thế hiện trạng.
    """

    line: SourceLine
    outcome: str
    version_no: int
    creates_version: bool
    becomes_current: bool
    previous_version_id: Optional[int] = None
    changed_fields: Optional[dict] = None
    collision_detail: Optional[dict] = None


@dataclass(frozen=True)
class ReconcileResult:
    decisions: tuple[Decision, ...]

    def counts(self) -> dict:
        totals = {name: 0 for name in
                  (OUTCOME_INSERT, OUTCOME_SAME, OUTCOME_SOURCE_CHANGED, OUTCOME_COLLISION)}
        for decision in self.decisions:
            totals[decision.outcome] += 1
        return totals
