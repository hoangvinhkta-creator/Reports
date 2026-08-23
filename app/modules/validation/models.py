"""Review Queue data model — mục §18 đặc tả, TASK-110.

Pure dataclasses, no I/O (ADR-101). A `ReviewItem` is a *finding about* data,
never a copy of it: it carries the back-reference needed to locate what it is
about, and nothing that identifies a customer.
`governance/core/04_SECURITY_RULES.md` §6 makes purchase price and margin
sensitive; `governance/product/17_DATA_GOVERNANCE_PRIVACY.md` makes customer
name/phone/address sensitive. A review queue that leaked either would be a new
exposure surface built by the very task meant to add safety (CHECK-110-17).

**Every item must be traceable.** Independent Review #1 Finding 1 found items
with no back-reference at all — a queue line nobody can act on is only
marginally better than silence. `scope` now makes the required reference
explicit and `__post_init__` enforces it, so an untraceable item cannot be
constructed at all:

    SCOPE_ROW    one raw row      -> `source_file` + `source_row` required
    SCOPE_ORDER  one OrderID      -> `source_file` + `order_id` required
    SCOPE_BATCH  the whole import -> `source_file` required

The queue is built in memory and returned alongside the processed data. It is
never persisted here — storage is TASK-201, audit trail TASK-202, the screen
TASK-305.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

# Severity is a READING ORDER label, not a gate. §18 đặc tả: "Không block toàn
# bộ import." `ERROR` means "read this first", never "stop" — CHECK-110-02
# pins that an import whose every row is flagged still returns full results.
SEVERITY_INFO = "INFO"
SEVERITY_WARNING = "WARNING"
SEVERITY_ERROR = "ERROR"
SEVERITIES = (SEVERITY_INFO, SEVERITY_WARNING, SEVERITY_ERROR)

_SEVERITY_ORDER = {SEVERITY_ERROR: 0, SEVERITY_WARNING: 1, SEVERITY_INFO: 2}

# What a finding is about, and therefore what reference it must carry.
SCOPE_ROW = "row"
SCOPE_ORDER = "order"
SCOPE_BATCH = "batch"
SCOPES = (SCOPE_ROW, SCOPE_ORDER, SCOPE_BATCH)

# The eight category codes of the frozen scope table. Seven *loại* in §18
# terms — `Missing` appears twice because DEC-128 §1 splits it by shape: the
# per-row fields stay per-row, the Pending purchase price collapses into one
# aggregate item.
CATEGORY_MISSING = "Missing"
CATEGORY_MISSING_PURCHASE_PRICE = "Missing.PurchasePrice"
CATEGORY_SUSPICIOUS = "Suspicious"
CATEGORY_SUSPICIOUS_ERP = "Suspicious.ERP"
CATEGORY_ORDER_INCONSISTENCY = "OrderInconsistency"
CATEGORY_SOURCE_CLASSIFICATION = "SourceClassification"
CATEGORY_DUPLICATE = "Duplicate"
CATEGORY_EMPLOYEE_MAPPING = "EmployeeMapping"

CATEGORIES = (
    CATEGORY_MISSING,
    CATEGORY_MISSING_PURCHASE_PRICE,
    CATEGORY_SUSPICIOUS,
    CATEGORY_SUSPICIOUS_ERP,
    CATEGORY_ORDER_INCONSISTENCY,
    CATEGORY_SOURCE_CLASSIFICATION,
    CATEGORY_DUPLICATE,
    CATEGORY_EMPLOYEE_MAPPING,
)

# Provenance keys for `CATEGORY_ORDER_INCONSISTENCY`, required verbatim by the
# project owner when freezing the gate. A multi-employee order is NOT resolved
# here — ownership stays an open business decision — so the finding has to
# carry everything a later decision would need:
#
#   employees_found  every distinct selling identity seen on the order
#   legacy_selected  who `order_builder` currently picks (first line's value),
#                    recorded as LEGACY BEHAVIOUR, not as verified ownership
#   source_rows      the raw rows those identities came from
DETAIL_EMPLOYEES_FOUND = "employees_found"
DETAIL_LEGACY_SELECTED = "legacy_selected"
DETAIL_SOURCE_ROWS = "source_rows"
DETAIL_DATES_FOUND = "dates_found"
DETAIL_ROW_HASH = "row_hash"
DETAIL_RULE = "rule"

# Provenance keys for `CATEGORY_EMPLOYEE_MAPPING` (F1–F6). Added by Independent
# Review #1 Finding 1: an F4 that cannot name the rows it is about leaves a
# reader with nothing to open.
DETAIL_CRITERION = "criterion"
DETAIL_EMPLOYEE = "employee"
DETAIL_RAW_VALUE = "raw_value"
DETAIL_RAW_PREFIX = "raw_prefix"
DETAIL_DECLARED_GROUP = "declared_group"
DETAIL_DATASET_RANGE = "dataset_range"
DETAIL_BATCH_ROWS = "batch_rows"

# Never allowed inside a `ReviewItem`. Kept as data so the guard is one list
# rather than a habit somebody has to remember (CHECK-110-17).
PII_FIELD_NAMES = ("customer", "customer_code", "phone", "address")


@dataclass(frozen=True)
class ReviewItem:
    """One finding.

    `affected_count` is how many raw rows sit behind this item: 1 for a
    per-row finding, N for an aggregate one (DEC-128 §1). It may legitimately
    be **0** — criterion F2 is precisely "a configured employee that matched
    no row", and reporting a fake 1 there would misstate the only fact the
    finding carries.
    """

    category: str
    severity: str
    message: str
    scope: str = SCOPE_ROW
    source_file: Optional[str] = None
    source_row: Optional[int] = None
    order_id: Optional[str] = None
    affected_count: int = 1
    details: dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.category not in CATEGORIES:
            raise ValueError(f"Unknown review category: {self.category!r}")
        if self.severity not in SEVERITIES:
            raise ValueError(f"Unknown review severity: {self.severity!r}")
        if self.scope not in SCOPES:
            raise ValueError(f"Unknown review scope: {self.scope!r}")
        if self.affected_count < 0:
            raise ValueError(f"affected_count cannot be negative: {self.affected_count}")

        # Traceability is structural, not a convention (Review #1, Finding 1).
        if not self.source_file:
            raise ValueError(
                f"ReviewItem({self.category}) needs source_file to be traceable"
            )
        if self.scope == SCOPE_ROW and self.source_row is None:
            raise ValueError(
                f"ReviewItem({self.category}) scope={SCOPE_ROW} needs source_row"
            )
        if self.scope == SCOPE_ORDER and not self.order_id:
            raise ValueError(
                f"ReviewItem({self.category}) scope={SCOPE_ORDER} needs order_id"
            )


@dataclass
class ReviewQueue:
    """The findings from one import, in reading order.

    Sorted by severity (ERROR first), then category, then source row — so the
    same input always produces the same queue, and the things worth a human's
    attention are not buried under a thousand INFO lines.
    """

    items: list[ReviewItem] = field(default_factory=list)

    def add(self, item: ReviewItem) -> None:
        self.items.append(item)

    def extend(self, items: list[ReviewItem]) -> None:
        self.items.extend(items)

    def sorted_items(self) -> list[ReviewItem]:
        return sorted(
            self.items,
            key=lambda i: (
                _SEVERITY_ORDER[i.severity],
                i.category,
                i.source_row if i.source_row is not None else -1,
                i.order_id or "",
                i.message,
            ),
        )

    def by_category(self, category: str) -> list[ReviewItem]:
        return [item for item in self.items if item.category == category]

    def by_severity(self, severity: str) -> list[ReviewItem]:
        return [item for item in self.items if item.severity == severity]

    def by_scope(self, scope: str) -> list[ReviewItem]:
        return [item for item in self.items if item.scope == scope]

    def counts_by_category(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for item in self.items:
            counts[item.category] = counts.get(item.category, 0) + 1
        return counts

    def affected_rows(self) -> int:
        """Total rows behind the queue, expanding aggregate items."""
        return sum(item.affected_count for item in self.items)

    def __len__(self) -> int:
        return len(self.items)

    def __iter__(self):
        return iter(self.sorted_items())
