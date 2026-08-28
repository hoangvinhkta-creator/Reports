"""`FilePriceProvider` — the file-backed `PriceProvider` implementation (TASK-105B).

DEC-145 (`OD-105B-01`) freezes this contract; full text and Completion Gate
at `docs/tasks/TASK-105B-file-price-provider.md`. A price table is a list of
4-column records — `product_key`, `effective_from`, `effective_to`,
`purchase_price` (`source` optional) — keyed by a normalized product key
(§2) over a **closed** effective interval (§1). This module validates the
whole table when it is loaded, not one row at a time: a malformed table has
to be visible immediately (`InvalidPriceMasterError`), not discovered
lookup-by-lookup.

A lookup miss is `None` — Pending — never an error, and never coerced to
`0` (DEC-103, DEC-145 §5). There is no `latest`/`nearest`/`current`
fallback: a `sale_date` that does not fall inside a validated interval is
Pending, full stop.

This module never runs in the Golden path and is never the pipeline
default — `app/pipeline.py` still defaults to `PendingPriceProvider`
(TASK-105 `CHECK-105-04`). A caller must construct `FilePriceProvider`
explicitly and pass it in.

TASK-105B-Q3 (the supplementary/expense-line zero-price policy, DEC-145 §3)
is deliberately **out of scope here** — `OD-105B-01` §C forbids a new
substring matcher inside this provider; that policy is a layer above it,
driven by production classification, blocked on TASK-103. This module does
not import `app.modules.validation.rules` and carries no line-classification
keywords.
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable, Optional

from app.modules.config.loader import as_date, load_yaml
from app.modules.domain.money import to_decimal
from app.modules.validation.text import fold

_FAR_FUTURE = _dt.date(9999, 12, 31)


class InvalidPriceMasterError(ValueError):
    """The price table itself is malformed — refuses to load (DEC-145 §5).

    Deliberately fatal at load time: an overlap, a second open record, a
    negative/missing price, or an exact duplicate row is a defect in the
    table, not a per-row miss, and the engine never resolves it by picking
    one side (same principle as `AmbiguousSchemeConfigError`).

    `reason` is a short machine-checkable code (e.g. `"overlapping_periods"`,
    `"negative_price"`) for callers/tests that need to distinguish which
    DEC-145 §5 rule fired without parsing the message text.
    """

    def __init__(self, message: str, *, reason: str) -> None:
        super().__init__(message)
        self.reason = reason


@dataclass(frozen=True)
class PriceRecord:
    """One validated price-table row, with provenance intact (DEC-145 §2).

    `raw_product_key` is the literal value from the price file; the file's
    own normalized lookup key is `normalized_product_key`. Both stay
    attached to the record so a caller can always answer "which raw key,
    normalized how, matched this lookup" without re-deriving anything.
    """

    raw_product_key: str
    normalized_product_key: str
    effective_from: _dt.date
    effective_to: Optional[_dt.date]  # None = still in effect
    purchase_price: Decimal
    source: Optional[str] = None


class FilePriceProvider:
    """Satisfies `PriceProvider` (DEC-145 §4 schema, §1 closed intervals)."""

    def __init__(self, rows: Iterable[dict[str, Any]]):
        self._records: list[PriceRecord] = _parse_rows(list(rows))
        by_key: dict[str, list[PriceRecord]] = {}
        for record in self._records:
            by_key.setdefault(record.normalized_product_key, []).append(record)
        self._by_key = by_key

    @classmethod
    def from_yaml(cls, path: Path) -> "FilePriceProvider":
        data = load_yaml(path)
        return cls(data.get("prices", []))

    @property
    def records(self) -> tuple[PriceRecord, ...]:
        return tuple(self._records)

    def find_record(
        self, product_code: Optional[str], sale_date: Optional[_dt.date]
    ) -> Optional[PriceRecord]:
        """Return the matched `PriceRecord`, or `None` if this is Pending."""
        if product_code is None or sale_date is None:
            return None
        key = fold(product_code)
        for record in self._by_key.get(key, ()):
            end = record.effective_to or _FAR_FUTURE
            if record.effective_from <= sale_date <= end:
                return record
        return None

    def lookup(
        self, product_code: Optional[str], sale_date: Optional[_dt.date]
    ) -> Optional[Decimal]:
        record = self.find_record(product_code, sale_date)
        return record.purchase_price if record is not None else None


# ---------------------------------------------------------------------------
# Loading / validation (DEC-145 §5) — runs once, eagerly, in __init__.
# ---------------------------------------------------------------------------


def _parse_rows(rows: list[dict[str, Any]]) -> list[PriceRecord]:
    records = [_parse_one_row(row, i) for i, row in enumerate(rows, start=1)]
    _validate_master(records)
    return records


def _parse_one_row(row: dict[str, Any], row_number: int) -> PriceRecord:
    raw_key, normalized_key = _parse_product_key(row.get("product_key"), row_number)
    effective_from = _parse_required_date(
        row.get("effective_from"), row_number, "effective_from"
    )
    effective_to = _parse_optional_date(
        row.get("effective_to"), row_number, "effective_to"
    )
    if effective_to is not None and effective_to < effective_from:
        raise InvalidPriceMasterError(
            f"Dòng giá #{row_number}: effective_to ({effective_to}) < "
            f"effective_from ({effective_from}) — khoảng hiệu lực đảo ngược "
            "(DEC-145 §5).",
            reason="inverted_range",
        )
    price = _parse_price(row.get("purchase_price"), row_number)
    raw_source = row.get("source")
    source = str(raw_source) if raw_source not in (None, "") else None
    return PriceRecord(
        raw_product_key=raw_key,
        normalized_product_key=normalized_key,
        effective_from=effective_from,
        effective_to=effective_to,
        purchase_price=price,
        source=source,
    )


def _parse_product_key(value: Any, row_number: int) -> tuple[str, str]:
    raw = "" if value is None else str(value)
    normalized = fold(raw)
    if not normalized:
        raise InvalidPriceMasterError(
            f"Dòng giá #{row_number}: product_key rỗng — trường bắt buộc "
            "(DEC-145 §5).",
            reason="empty_key",
        )
    return raw, normalized


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def _parse_required_date(value: Any, row_number: int, field: str) -> _dt.date:
    if _is_blank(value):
        raise InvalidPriceMasterError(
            f"Dòng giá #{row_number}: trường '{field}' bắt buộc nhưng rỗng "
            "(DEC-145 §4/§5).",
            reason="invalid_date",
        )
    return _parse_date_value(value, row_number, field)


def _parse_optional_date(
    value: Any, row_number: int, field: str
) -> Optional[_dt.date]:
    if _is_blank(value):
        return None
    return _parse_date_value(value, row_number, field)


def _parse_date_value(value: Any, row_number: int, field: str) -> _dt.date:
    try:
        parsed = as_date(value)
    except (TypeError, ValueError) as exc:
        raise InvalidPriceMasterError(
            f"Dòng giá #{row_number}: trường '{field}' không parse được "
            f"thành ngày hợp lệ ({value!r}): {exc}.",
            reason="invalid_date",
        ) from exc
    if parsed is None:
        raise InvalidPriceMasterError(
            f"Dòng giá #{row_number}: trường '{field}' không parse được "
            f"thành ngày hợp lệ ({value!r}).",
            reason="invalid_date",
        )
    return parsed


def _parse_price(value: Any, row_number: int) -> Decimal:
    try:
        price = to_decimal(value)
    except (TypeError, InvalidOperation) as exc:
        raise InvalidPriceMasterError(
            f"Dòng giá #{row_number}: purchase_price không hợp lệ ({value!r}): "
            f"{exc}.",
            reason="invalid_price",
        ) from exc
    if price is None:
        raise InvalidPriceMasterError(
            f"Dòng giá #{row_number}: purchase_price rỗng — trường bắt buộc "
            "(DEC-145 §4). Ô trống không phải giá 0 (DEC-145 §5).",
            reason="missing_price",
        )
    if price < 0:
        raise InvalidPriceMasterError(
            f"Dòng giá #{row_number}: purchase_price âm ({price}) — không "
            "hợp lệ (DEC-145 §5).",
            reason="negative_price",
        )
    return price


def _validate_master(records: list[PriceRecord]) -> None:
    by_key: dict[str, list[PriceRecord]] = {}
    for record in records:
        by_key.setdefault(record.normalized_product_key, []).append(record)
    for key, group in by_key.items():
        _reject_exact_duplicates(key, group)
        _reject_multiple_open_records(key, group)
        _reject_overlaps(key, group)


def _reject_exact_duplicates(key: str, group: list[PriceRecord]) -> None:
    seen: set[tuple[Any, ...]] = set()
    for record in group:
        fingerprint = (
            record.raw_product_key,
            record.effective_from,
            record.effective_to,
            record.purchase_price,
            record.source,
        )
        if fingerprint in seen:
            raise InvalidPriceMasterError(
                f"Bảng giá có dòng trùng lặp hoàn toàn cho key {key!r}: "
                f"{fingerprint} — không có authority dedupe cho bảng giá "
                "(DEC-145 §5, Reason điểm 4), REJECT.",
                reason="exact_duplicate_row",
            )
        seen.add(fingerprint)


def _reject_multiple_open_records(key: str, group: list[PriceRecord]) -> None:
    open_records = [r for r in group if r.effective_to is None]
    if len(open_records) > 1:
        raise InvalidPriceMasterError(
            f"Có {len(open_records)} record 'effective_to' rỗng (còn hiệu "
            f"lực) cho cùng key {key!r} — chỉ được đúng một (DEC-145 §1).",
            reason="multiple_open_records",
        )


def _reject_overlaps(key: str, group: list[PriceRecord]) -> None:
    for i in range(len(group)):
        for j in range(i + 1, len(group)):
            a, b = group[i], group[j]
            a_end = a.effective_to or _FAR_FUTURE
            b_end = b.effective_to or _FAR_FUTURE
            if not (a.effective_from <= b_end and b.effective_from <= a_end):
                continue
            if a.purchase_price != b.purchase_price:
                raise InvalidPriceMasterError(
                    f"Khoảng hiệu lực chồng lấn cho key {key!r} với giá "
                    f"khác nhau: [{a.effective_from},{a.effective_to}]="
                    f"{a.purchase_price} vs [{b.effective_from},"
                    f"{b.effective_to}]={b.purchase_price} (DEC-145 §5 — "
                    "engine không tự chọn).",
                    reason="conflicting_price_same_period",
                )
            raise InvalidPriceMasterError(
                f"Khoảng hiệu lực chồng lấn cho key {key!r}: "
                f"[{a.effective_from},{a.effective_to}] và "
                f"[{b.effective_from},{b.effective_to}] (DEC-145 §1 — "
                "overlap CẤM).",
                reason="overlapping_periods",
            )
