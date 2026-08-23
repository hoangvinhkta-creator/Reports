"""Domain models for the Tín Phát reporting engine.

Pure dataclasses only — no I/O, no ORM, no framework imports (ADR-101). Money
is always `Decimal` in raw VND (ADR-103); no field here ever holds a
thousand-đồng value. Three-layer separation follows ADR-102: `RawRow` is the
immutable RAW layer, `WorkingLine`/`Order` are the WORKING layer built from it
in memory (Phase 1 has no database yet).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Optional

# LeadSource has exactly two values (DEC-119, ADR-104). This is a structural
# invariant of the model, not a business rule value — it does not belong in
# config the way a keyword list or a rate does.
PERSONAL = "PERSONAL"
ADS = "ADS"
LEAD_SOURCES = (PERSONAL, ADS)

# Employee-mapping outcome, per DEC-104: an unmapped raw employee name is
# never silently dropped — it is flagged so the caller can route it to review.
MAPPING_STATUS_MAPPED = "mapped"
MAPPING_STATUS_UNMAPPED = "unmapped"
MAPPING_STATUS_INACTIVE = "inactive"

# Provenance of accounting_purchase_price (DEC-103, TASK-105). "Pending" is
# the correct value for every line in Phase 1 — no Price Master exists yet,
# not a test-environment limitation. "PriceMaster" is reserved for TASK-401's
# real integration; "Manual" for when override/audit trail exists (TASK-202).
PRICE_SOURCE_PENDING = "Pending"
PRICE_SOURCE_PRICE_MASTER = "PriceMaster"
PRICE_SOURCE_MANUAL = "Manual"

# ProductGroup has exactly two values (DEC-127, ADR-106). Like LEAD_SOURCES,
# this is a structural invariant of the model, not a tunable business value.
# It is a property of the PRODUCT LINE, never of the order: 118 real OrderIDs
# carry both kinds at once, so one scheme per order would misprice them.
DIEN_MAY = "DIEN_MAY"
GIA_DUNG = "GIA_DUNG"
PRODUCT_GROUPS = (DIEN_MAY, GIA_DUNG)

# Provenance of product_group_final (ADR-106 §5). "DEFAULT" must stay
# distinguishable from "MANUAL": in Phase 1 every line falls back to
# DIEN_MAY, and that fallback has to be visible rather than look like a
# decision somebody made.
PRODUCT_GROUP_SOURCE_DEFAULT = "DEFAULT"
PRODUCT_GROUP_SOURCE_MANUAL = "MANUAL"
PRODUCT_GROUP_SOURCE_AUTO = "AUTO"

# A conversion scheme that resolved to no configured row. Never a rate.
CONVERSION_UNRESOLVED = "Unresolved"


@dataclass(frozen=True)
class RawRow:
    """One physical data row from `So_chi_tiet_ban_hang.xlsx`, unmodified.

    Never updated or deleted after import (ADR-102). `source_row` is the
    1-based row number in the sheet, kept for traceability back to the
    original file (spec section 4.1). `row_hash` is used to detect a
    duplicate re-import of the same file without creating a second record.
    """

    source_file: str
    source_sheet: str
    source_row: int
    row_hash: str

    date: Optional[date]
    order_id: str
    note_raw: Optional[str]
    product_raw: Optional[str]
    customer_code: Optional[str]
    customer: Optional[str]
    address: Optional[str]
    phone: Optional[str]
    quantity: Optional[Decimal]
    sell_price: Optional[Decimal]
    total_sales_raw: Optional[Decimal]
    discount: Optional[Decimal]
    employee_raw: Optional[str]
    shipper_raw: Optional[str]
    delivery_cost: Optional[Decimal]
    imei: Optional[str]
    source_profit: Optional[Decimal]


@dataclass
class WorkingLine:
    """One normalized sales line, derived from a `RawRow`.

    Built progressively by the import pipeline: `normalizer` fills the base
    fields; `employee_mapper` fills `employee_normalized`/`employee_mapping_status`;
    `lead_source` classification fills `lead_source_final` after order
    grouping, by propagating the order's verdict down to every line that
    shares its `order_id` (DEC-119 — classification is an order-level
    decision, never a per-row one).
    """

    raw: RawRow
    order_id: str
    date: Optional[date]
    month: Optional[str]  # "YYYY-MM", derived from date

    note_raw: Optional[str]
    product_raw: Optional[str]
    customer_code: Optional[str]
    customer: Optional[str]
    address: Optional[str]
    phone: Optional[str]

    quantity: Optional[Decimal]
    sell_price: Optional[Decimal]
    discount: Decimal
    total_sales: Optional[Decimal]  # SellPrice * Quantity - Discount (DEC-114)

    employee_raw: Optional[str]
    employee_normalized: Optional[str] = None
    employee_mapping_status: str = MAPPING_STATUS_UNMAPPED
    employee_group: Optional[str] = None

    shipper_raw: Optional[str] = None
    delivery_cost: Optional[Decimal] = None
    imei: Optional[str] = None
    source_profit: Optional[Decimal] = None

    lead_source_final: Optional[str] = None

    # Bước 8 §22 đặc tả (TASK-105). `None` means Pending — never coerced to
    # 0, per DEC-103 and 03_DATA_MODEL_RULES §5 (missing/null/0 are distinct
    # facts). `price_source` names where the value came from, mirroring the
    # SourceOfValue pattern already used for LeadSource.
    accounting_purchase_price: Optional[Decimal] = None
    price_source: str = PRICE_SOURCE_PENDING

    # Bước 9 §22 đặc tả (TASK-107). Universal formula, độc lập hoàn toàn với
    # KpiAdjustment (DEC-126 điểm 1) — `AccountingProfit = (SellPrice -
    # AccountingPurchasePrice) * Quantity`. `None` khi bất kỳ input nào còn
    # Pending/thiếu — không bao giờ suy đoán 0 (DEC-103).
    accounting_profit: Optional[Decimal] = None

    # Bước 10 §22 đặc tả (TASK-108A-1, ADR-106). ProductGroup và
    # ConversionScheme đều ở cấp LINE, không phải cấp Order — một OrderID có
    # thể chứa cả Điện máy lẫn Gia dụng. `LeadSource` vẫn ở cấp Order
    # (DEC-119 không đổi).
    product_group_auto: Optional[str] = None  # Phase 1 luôn None
    product_group_manual: Optional[str] = None  # checkbox "Gia dụng" ghi vào đây
    product_group_final: Optional[str] = None
    product_group_source_of_value: Optional[str] = None

    # `conversion_rate_final is None` cùng với scheme `Unresolved` nghĩa là
    # không tra được tỉ lệ — vào Review Queue, không bao giờ mượn tỉ lệ của
    # nhân viên khác và không bao giờ có tỉ lệ mặc định cuối cùng (ADR-104).
    conversion_scheme_auto: Optional[str] = None
    conversion_scheme_manual: Optional[str] = None
    conversion_scheme_final: Optional[str] = None
    conversion_rate_final: Optional[Decimal] = None
    conversion_scheme_source_of_value: Optional[str] = None


@dataclass
class Order:
    """A group of `WorkingLine`s sharing one `OrderID` (Số BH).

    `lead_source_final` is decided once per order and propagated to every
    line — never decided independently per line (DEC-119).
    """

    order_id: str
    date: Optional[date]
    employee_raw: Optional[str]
    employee_normalized: Optional[str]
    employee_mapping_status: str
    lines: list[WorkingLine] = field(default_factory=list)
    employee_group: Optional[str] = None

    lead_source_auto: Optional[str] = None
    lead_source_manual: Optional[str] = None
    lead_source_final: Optional[str] = None
    lead_source_source_of_value: Optional[str] = None

    @property
    def total_sales(self) -> Decimal:
        return sum((line.total_sales or Decimal("0")) for line in self.lines)

    @property
    def line_count(self) -> int:
        return len(self.lines)
