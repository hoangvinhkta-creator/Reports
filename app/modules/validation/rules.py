"""The seven Review Queue detectors — mục §18 đặc tả, TASK-110, DEC-128.

Every function here READS `WorkingLine`/`Order` and returns findings. None of
them writes to a line, changes a rate, or decides who owns an order. That
separation is the point of the task: validation makes a problem visible, it
never quietly resolves one. DEC-128 §4 and the owner's freeze note make this
explicit for multi-employee orders, and it holds for every rule here.

Thresholds, severities and the non-product keyword list all come from
`config/validation.yaml` (CHECK-110-08) — nothing in this file hardcodes a
business value.
"""

from __future__ import annotations

from collections import defaultdict
from decimal import Decimal
from typing import Optional, Pattern

from app.modules.domain.models import (
    MAPPING_STATUS_UNMAPPED,
    Order,
    PRICE_SOURCE_PENDING,
    WorkingLine,
)
from app.modules.validation.models import (
    CATEGORY_DUPLICATE,
    CATEGORY_MISSING,
    CATEGORY_MISSING_PURCHASE_PRICE,
    CATEGORY_ORDER_INCONSISTENCY,
    CATEGORY_SOURCE_CLASSIFICATION,
    CATEGORY_SUSPICIOUS,
    CATEGORY_SUSPICIOUS_ERP,
    DETAIL_DATES_FOUND,
    DETAIL_EMPLOYEES_FOUND,
    DETAIL_LEGACY_SELECTED,
    DETAIL_ROW_HASH,
    DETAIL_RULE,
    DETAIL_SOURCE_ROWS,
    ReviewItem,
    SCOPE_BATCH,
    SCOPE_ORDER,
    SCOPE_ROW,
)
from app.modules.validation.text import matches_any

_ZERO = Decimal("0")


def is_non_product_line(line: WorkingLine, patterns: list[Pattern[str]]) -> bool:
    """Does this line look like a money-carrying non-product row (DEC-110)?

    Shipping, installation, VAT difference, discount and voucher lines legally
    carry `Quantity = 0` or `SellPrice = 0` — flagging them as suspicious
    would bury the real findings under a mass of normal business (DEC-128 §3).
    This is noise reduction only: deciding what such a line counts toward is
    Product/Transaction Classification, TASK-103.

    Matching goes through `text.matches_any`, so both sides are NFC-normalized,
    whitespace-collapsed and case-folded, and a keyword only matches as a whole
    word or phrase (Review #1, Findings 4 and 5; HD-110-02). The boundary is
    what keeps `phí` off `bàn phím`.

    **Temporary by decision (HD-110-02).** This heuristic exists only because
    TASK-103 does not, and it must never be tuned to reproduce a historical
    count.
    """
    return matches_any(line.product_raw, patterns)


def _severity_for(line: WorkingLine, configured: str, downgrade_to: str,
                  patterns: list[Pattern[str]]) -> str:
    if is_non_product_line(line, patterns):
        return downgrade_to
    return configured


# ---------------------------------------------------------------- V1 Missing

_MISSING_LABELS = {
    "date": "ngày",
    "order_id": "OrderID",
    "employee": "nhân viên",
    "quantity": "số lượng",
    "total_sales": "doanh số",
}


def _is_missing(line: WorkingLine, field: str) -> bool:
    if field == "date":
        return line.date is None
    if field == "order_id":
        return not (line.order_id or "").strip()
    if field == "employee":
        # ONLY `unmapped` (DEC-104, C11). An `inactive` mapping named a real
        # person — the seller is known, so nothing is missing. Reporting it
        # here was Independent Review #1, Finding 3.
        #
        # An inactive employee that still has rows is contradictory master
        # data and is NOT dropped in silence: criterion F6 reports it under
        # `EmployeeMapping` (HD-110-03).
        return line.employee_mapping_status == MAPPING_STATUS_UNMAPPED
    if field == "quantity":
        return line.quantity is None
    if field == "total_sales":
        return line.total_sales is None
    raise ValueError(f"Unknown missing-field rule: {field!r}")


def detect_missing(
    lines: list[WorkingLine], fields: dict[str, str]
) -> list[ReviewItem]:
    items: list[ReviewItem] = []
    for line in lines:
        for field, severity in fields.items():
            if not _is_missing(line, field):
                continue
            items.append(
                ReviewItem(
                    category=CATEGORY_MISSING,
                    severity=severity,
                    message=f"Thiếu {_MISSING_LABELS[field]}.",
                    scope=SCOPE_ROW,
                    source_file=line.raw.source_file,
                    source_row=line.raw.source_row,
                    order_id=line.order_id or None,
                    details={DETAIL_RULE: field},
                )
            )
    return items


def detect_missing_purchase_price(
    lines: list[WorkingLine], severity: str, aggregate: bool
) -> list[ReviewItem]:
    """DEC-128 §1 — one aggregate item, not one per row.

    Every Phase 1 line is `Pending` by design (DEC-103, no Price Master
    exists). Emitting 11.765 identical findings would make the queue unusable
    and take the real warnings down with it. `aggregate: false` in config
    restores per-row behaviour for when TASK-401 makes a missing price
    genuinely abnormal.
    """
    pending = [
        line for line in lines if line.price_source == PRICE_SOURCE_PENDING
    ]
    if not pending:
        return []

    if not aggregate:
        return [
            ReviewItem(
                category=CATEGORY_MISSING_PURCHASE_PRICE,
                severity=severity,
                message="Thiếu giá nhập (chờ Price Master).",
                scope=SCOPE_ROW,
                source_file=line.raw.source_file,
                source_row=line.raw.source_row,
                order_id=line.order_id or None,
            )
            for line in pending
        ]

    return [
        ReviewItem(
            category=CATEGORY_MISSING_PURCHASE_PRICE,
            severity=severity,
            message=(
                f"{len(pending)} dòng đang chờ giá nhập — chưa có Price Master "
                "(DEC-103). Đây là trạng thái đã biết của hệ thống, không phải "
                "lỗi dữ liệu của từng dòng."
            ),
            scope=SCOPE_BATCH,
            source_file=pending[0].raw.source_file,
            affected_count=len(pending),
        )
    ]


# ------------------------------------------------------------- V2 Suspicious

def _suspicious_checks(line: WorkingLine) -> list[tuple[str, str]]:
    """`(rule name, message)` for each computed-basis anomaly on this line."""
    found: list[tuple[str, str]] = []

    if line.quantity is not None and line.quantity <= _ZERO:
        found.append(("quantity_not_positive", f"Số lượng ≤ 0 ({line.quantity})."))

    if line.sell_price is not None and line.sell_price == _ZERO:
        found.append(("sell_price_zero", "Giá bán = 0."))

    # Both of the following stay silent through Phase 1: with no Price Master,
    # `accounting_purchase_price` is None on every line, so neither comparison
    # has an operand. That is the rule written correctly and dormant, not the
    # rule forgotten — CHECK-110-05 pins both halves.
    if (
        line.accounting_purchase_price is not None
        and line.sell_price is not None
        and line.accounting_purchase_price > line.sell_price
    ):
        found.append((
            "purchase_price_above_sell_price",
            "Giá nhập lớn hơn giá bán.",
        ))

    if line.accounting_profit is not None and line.accounting_profit < _ZERO:
        found.append((
            "accounting_profit_negative",
            f"Lợi nhuận kế toán âm ({line.accounting_profit}).",
        ))

    return found


def detect_suspicious(
    lines: list[WorkingLine],
    rules: dict[str, str],
    downgrade_to: str,
    patterns: list[Pattern[str]],
) -> list[ReviewItem]:
    items: list[ReviewItem] = []
    for line in lines:
        for rule, message in _suspicious_checks(line):
            severity = rules.get(rule)
            if severity is None:
                continue
            items.append(
                ReviewItem(
                    category=CATEGORY_SUSPICIOUS,
                    severity=_severity_for(line, severity, downgrade_to, patterns),
                    message=message,
                    scope=SCOPE_ROW,
                    source_file=line.raw.source_file,
                    source_row=line.raw.source_row,
                    order_id=line.order_id or None,
                    details={DETAIL_RULE: rule},
                )
            )
    return items


# --------------------------------------------------------- V3 Suspicious ERP

def detect_suspicious_erp(
    lines: list[WorkingLine],
    severity: str,
    downgrade_to: str,
    patterns: list[Pattern[str]],
) -> list[ReviewItem]:
    """DEC-128 §2 — a separate category, explicitly labelled as unverified.

    `docs/analysis/01_DATA_MAPPING.md` §3 decided the ERP `Lợi nhuận` column is
    not trustworthy as accounting data — it already contains components the
    tool cannot account for. It is still worth a human's eyes, so it goes to
    the queue under its own name. It must never be mixed into the computed
    category, and never be used to derive a purchase price (CHECK-110-06).
    """
    items: list[ReviewItem] = []
    for line in lines:
        if line.source_profit is None or line.source_profit >= _ZERO:
            continue
        items.append(
            ReviewItem(
                category=CATEGORY_SUSPICIOUS_ERP,
                severity=_severity_for(line, severity, downgrade_to, patterns),
                message=(
                    f"ERP báo lợi nhuận âm ({line.source_profit}). Tín hiệu từ "
                    "ERP, CHƯA kiểm chứng — không dùng để suy ra giá nhập "
                    "(DEC-103)."
                ),
                scope=SCOPE_ROW,
                source_file=line.raw.source_file,
                source_row=line.raw.source_row,
                order_id=line.order_id or None,
            )
        )
    return items


# ------------------------------------------------- V4 Order inconsistency

def _selling_identity(line: WorkingLine) -> str:
    """Who this line says sold it.

    The mapped name when there is one, otherwise the raw string. Comparing
    only mapped names would hide the worst case — a mapped line and an
    unmapped line on the same order, where the unmapped person's revenue
    silently lands on whoever `order_builder` picked first.
    """
    if line.employee_normalized:
        return line.employee_normalized
    raw = (line.employee_raw or "").strip()
    return f"<chưa map: {raw}>" if raw else "<không có nhân viên>"


def detect_order_inconsistency(
    orders: list[Order], employee_severity: str, date_severity: str
) -> list[ReviewItem]:
    """DEC-128 §4 + the owner's freeze note: DETECT ONLY.

    This does not touch `order_builder`, does not reassign an employee, does
    not split KPI, and does not pick who gets the revenue. Changing how a
    multi-employee order is handled is a separate business decision.

    Because nothing is resolved here, the finding carries the full provenance a
    later decision would need: the OrderID, every distinct selling identity
    found, the raw rows they came from, and — labelled as LEGACY BEHAVIOUR,
    not as verified ownership — whoever `order_builder` currently selects.
    """
    items: list[ReviewItem] = []
    for order in orders:
        if not order.lines:
            continue  # nothing to compare, and no row to point a reader at
        identities: dict[str, list[int]] = defaultdict(list)
        for line in order.lines:
            identities[_selling_identity(line)].append(line.raw.source_row)

        if len(identities) > 1:
            legacy = (
                order.employee_normalized
                or (order.employee_raw or "").strip()
                or "—"
            )
            rows = sorted(
                row for row_list in identities.values() for row in row_list
            )
            items.append(
                ReviewItem(
                    category=CATEGORY_ORDER_INCONSISTENCY,
                    severity=employee_severity,
                    message=(
                        f"Đơn {order.order_id} có {len(identities)} nhân viên "
                        "khác nhau trên các dòng. Công cụ KHÔNG tự chọn chủ "
                        "đơn — hiện `order_builder` lấy nhân viên của dòng đầu "
                        "tiên, đó là hành vi legacy, KHÔNG phải quyền sở hữu "
                        "đã được xác minh. Cần người quyết định."
                    ),
                    scope=SCOPE_ORDER,
                    source_file=order.lines[0].raw.source_file,
                    order_id=order.order_id,
                    affected_count=len(order.lines),
                    details={
                        DETAIL_EMPLOYEES_FOUND: " | ".join(sorted(identities)),
                        DETAIL_LEGACY_SELECTED: legacy,
                        DETAIL_SOURCE_ROWS: ", ".join(str(r) for r in rows),
                    },
                )
            )

        dates = {line.date for line in order.lines if line.date is not None}
        if len(dates) > 1:
            items.append(
                ReviewItem(
                    category=CATEGORY_ORDER_INCONSISTENCY,
                    severity=date_severity,
                    message=(
                        f"Đơn {order.order_id} có {len(dates)} ngày khác nhau "
                        "trên các dòng."
                    ),
                    scope=SCOPE_ORDER,
                    source_file=order.lines[0].raw.source_file,
                    order_id=order.order_id,
                    affected_count=len(order.lines),
                    details={
                        DETAIL_DATES_FOUND: ", ".join(
                            d.isoformat() for d in sorted(dates)
                        ),
                        DETAIL_SOURCE_ROWS: ", ".join(
                            str(line.raw.source_row) for line in order.lines
                        ),
                    },
                )
            )
    return items


# ----------------------------------------------------- V5 Source classification

def detect_source_classification(
    orders: list[Order], severity: str
) -> list[ReviewItem]:
    """A manual override that disagrees with the automatic ADS rule.

    Phase 1 has nothing that writes `lead_source_manual` — no override UI, no
    persistence (TASK-202/302). So this yields zero findings on real data BY
    CONSTRUCTION, not because the rule is broken. CHECK-110-10 proves the rule
    works by feeding it a fixture that does carry an override.
    """
    items: list[ReviewItem] = []
    for order in orders:
        manual = order.lead_source_manual
        if not order.lines or not manual or manual == order.lead_source_auto:
            continue
        items.append(
            ReviewItem(
                category=CATEGORY_SOURCE_CLASSIFICATION,
                severity=severity,
                message=(
                    f"Đơn {order.order_id}: override tay `{manual}` khác kết "
                    f"quả rule tự động `{order.lead_source_auto}`."
                ),
                scope=SCOPE_ORDER,
                source_file=order.lines[0].raw.source_file,
                order_id=order.order_id,
            )
        )
    return items


# -------------------------------------------------------------- V6 Duplicate

def detect_duplicates(
    lines: list[WorkingLine], severity: str
) -> list[ReviewItem]:
    """DEC-128 §3 — same `row_hash` twice inside ONE import.

    The spec's wording (`cùng source_file + source_row`) cannot fire: that pair
    is unique by construction within a single read. Content equality can fire,
    and it is a WARNING rather than an error because two identical accessory
    lines on one order are legitimate. Detecting a re-import of the same file
    needs persistence and belongs to TASK-201.
    """
    by_hash: dict[str, list[WorkingLine]] = defaultdict(list)
    for line in lines:
        by_hash[line.raw.row_hash].append(line)

    items: list[ReviewItem] = []
    for row_hash, group in by_hash.items():
        if len(group) < 2:
            continue
        rows = sorted(line.raw.source_row for line in group)
        items.append(
            ReviewItem(
                category=CATEGORY_DUPLICATE,
                severity=severity,
                message=(
                    f"{len(group)} dòng có nội dung giống hệt nhau (dòng "
                    f"{', '.join(str(r) for r in rows)}). Có thể hợp lệ — hai "
                    "dòng phụ kiện giống nhau trong một đơn — cần người xem."
                ),
                scope=SCOPE_ROW,
                source_file=group[0].raw.source_file,
                source_row=rows[0],
                order_id=group[0].order_id or None,
                affected_count=len(group),
                details={
                    DETAIL_ROW_HASH: row_hash,
                    DETAIL_SOURCE_ROWS: ", ".join(str(r) for r in rows),
                },
            )
        )
    return items
