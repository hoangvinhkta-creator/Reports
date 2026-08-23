"""Decimal conversion helpers for money fields (ADR-103).

Storage is always raw VND as `Decimal`. `float` never appears on a money
field anywhere in this codebase. Converting through `str(value)` for a
`float` cell avoids importing the float's binary-representation error into
the `Decimal` — the standard safe path recommended by the `decimal` docs.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Optional


def to_decimal(value: object) -> Optional[Decimal]:
    """Convert a raw Excel cell value to `Decimal`, or `None` if empty.

    A blank cell and a cell holding `0` are different facts (03_DATA_MODEL_RULES
    §5) — this function preserves that distinction by returning `None` for
    blank/whitespace-only cells rather than `Decimal("0")`.
    """
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    if isinstance(value, bool):
        # bool is a subclass of int in Python; a checkbox-like cell is not a
        # money value we ever expect here, so refuse rather than silently
        # coerce True/False to 1/0.
        raise TypeError(f"Refusing to convert bool to Decimal: {value!r}")
    if isinstance(value, int):
        return Decimal(value)
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        return Decimal(text)
    raise TypeError(f"Cannot convert {type(value).__name__} to Decimal: {value!r}")
