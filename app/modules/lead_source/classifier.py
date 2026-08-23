"""LeadSource classification at OrderID level (DEC-109, DEC-119, ADR-104).

Priority chain (spec section 7, extended by DEC-109's employee default and
narrowed to two values by DEC-119):

    1. Manual Override                  -> "Manual"
    2. ADS keyword on ANY line's note   -> "Auto:ADS Rule"
    3. Employee-level default           -> "Auto:Employee Default (<name>)"
    4. System default (PERSONAL)        -> "Auto:Default"

Classification happens once per order and is then propagated to every line
of that order — never decided independently per line. This is the same
algorithm verified case-by-case in `tools/analysis/verify_ads_rule.py`
(31/31 PASS as of DEC-119); this module is its config-driven production
counterpart, reading rates and keywords from `config/`, not from Python
constants.

This module classifies LeadSource ONLY. It does not resolve ConversionScheme
(TASK-108, ADR-104 step 2) — PERSONAL does not imply a rate.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from app.modules.config.loader import load_yaml
from app.modules.domain.models import Order


def _normalize_note(value: Optional[str]) -> str:
    if value is None:
        return ""
    text = unicodedata.normalize("NFC", str(value))
    return re.sub(r"\s+", " ", text).strip()


@dataclass(frozen=True)
class ClassificationResult:
    lead_source: str
    source_of_value: str


class LeadSourceClassifier:
    def __init__(self, ads_keywords: tuple[str, ...], default_lead_source: str):
        self._ads_keywords = tuple(keyword.upper() for keyword in ads_keywords)
        self._default_lead_source = default_lead_source

    @classmethod
    def from_yaml(cls, path: Path) -> "LeadSourceClassifier":
        data = load_yaml(path)
        return cls(
            ads_keywords=tuple(data.get("ads_keywords", [])),
            default_lead_source=data.get("default_lead_source", "PERSONAL"),
        )

    def _note_matches_ads(self, note: Optional[str]) -> bool:
        upper = _normalize_note(note).upper()
        return any(keyword in upper for keyword in self._ads_keywords)

    def classify_auto(
        self,
        notes: list[Optional[str]],
        employee_default_lead_source: Optional[str],
        employee_normalized: Optional[str],
    ) -> ClassificationResult:
        """Automatic verdict only — ignores manual override.

        Kept separate from the manual-aware resolution so "reset to auto" is
        always possible without recomputing the keyword scan (ADR-102).
        """
        if any(self._note_matches_ads(note) for note in notes):
            return ClassificationResult("ADS", "Auto:ADS Rule")
        if employee_default_lead_source:
            label = f"Auto:Employee Default ({employee_normalized})"
            return ClassificationResult(employee_default_lead_source, label)
        return ClassificationResult(self._default_lead_source, "Auto:Default")

    def resolve_final(
        self, auto: ClassificationResult, manual_override: Optional[str]
    ) -> ClassificationResult:
        if manual_override:
            return ClassificationResult(manual_override, "Manual")
        return auto

    def apply(self, orders: list[Order], employee_mapper) -> list[Order]:
        """Classify every order and propagate the verdict to its lines.

        `employee_mapper` supplies each order's employee-level default via
        its already-resolved mapping (DEC-104) — the classifier does not
        re-implement employee lookup.
        """
        for order in orders:
            mapping = employee_mapper.resolve(order.employee_raw, order.date)
            notes = [line.note_raw for line in order.lines]

            auto = self.classify_auto(
                notes, mapping.default_lead_source, order.employee_normalized
            )
            order.lead_source_auto = auto.lead_source

            final = self.resolve_final(auto, order.lead_source_manual)
            order.lead_source_final = final.lead_source
            order.lead_source_source_of_value = final.source_of_value

            for line in order.lines:
                line.lead_source_final = final.lead_source
        return orders
