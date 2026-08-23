"""Generic YAML config loading with effective-dating (DEC-121).

Every business-rule config file lists rows carrying `effective_from` /
`effective_to`, and a lookup always happens by an `as_of` date — the business
date the row belongs to, never "today" (spec section 12; DEC-121). This
module owns only the generic mechanics: reading the YAML and filtering rows
by date range. Domain-specific matching (which row counts as *the* match for
a given employee or scheme) lives in each config's own consumer module.
"""

from __future__ import annotations

import datetime as _dt
from pathlib import Path
from typing import Any, Optional

import yaml

_FAR_FUTURE = _dt.date(9999, 12, 31)


def load_yaml(path: Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    return data or {}


def as_date(value: Any) -> Optional[_dt.date]:
    """Parse a YAML date/datetime/ISO-string value into `date`, or `None`."""
    if value is None:
        return None
    if isinstance(value, _dt.datetime):
        return value.date()
    if isinstance(value, _dt.date):
        return value
    if isinstance(value, str):
        text = value.strip()
        return _dt.date.fromisoformat(text) if text else None
    raise TypeError(f"Cannot parse date from {value!r}")


def effective_rows(
    rows: list[dict[str, Any]], as_of: _dt.date
) -> list[dict[str, Any]]:
    """Return the rows whose [effective_from, effective_to] window covers `as_of`.

    A row missing `effective_from` is treated as always-effective from the
    start of time; a missing/`None` `effective_to` means still in effect.
    Order of the returned list matches the input order — callers decide how
    to break ties (e.g. "most specific row wins" for scheme lookups).
    """
    matches = []
    for row in rows:
        starts = as_date(row.get("effective_from")) or _dt.date.min
        ends = as_date(row.get("effective_to")) or _FAR_FUTURE
        if starts <= as_of <= ends:
            matches.append(row)
    return matches
