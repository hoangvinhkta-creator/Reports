"""Production composition seam — Golden #1 Repair Batch #1, B01.

`app/pipeline.py` is deliberately a PURE library entry point (S051 §9, S054
§3): `identity_registry`, `confirmed_adjustment_source`,
`eligible_costs_authority` are optional DI parameters that default to
"nothing wired in" -> Pending, so every existing `run_import()` call (test or
production, past or future) keeps behaving exactly as it did before any of
them existed. That purity is correct architecture, but it also means a
NORMAL, NON-TEST caller that simply invokes `run_import(raw_path)` with
defaults gets 100% Pending — nothing in `app/pipeline.py` itself ever loads
the canonical committed sources.

This module is the smallest explicit seam that closes that gap: it loads the
three canonical committed sources from their fixed repository paths and calls
`run_import()` for real — no stub, no mock, no bypass, no Golden-specific
branch, no hard-coded order/BH62063. A future real caller (TASK-112 CLI, a
scheduler, etc.) should call `run_import_production()` instead of composing
these three loaders by hand each time.
"""

from __future__ import annotations

from pathlib import Path

from app.modules.adjustment.confirmed_adjustment_source import (
    load_confirmed_adjustments_from_jsonl,
)
from app.modules.kpi.kpi_profit_engine import load_eligible_costs_authority
from app.modules.product.identity.registry_store import load_registry_from_jsonl
from app.pipeline import DEFAULT_CONFIG_DIR, ImportResult, run_import

# Canonical committed sources, fixed repository paths — same footing as
# `DEFAULT_CONFIG_DIR` ("config/") in `app/pipeline.py`.
HISTORICAL_REGISTRY_PATH = Path("data/historical_confirmed/registry.jsonl")
CONFIRMED_ADJUSTMENTS_PATH = Path(
    "data/confirmed_adjustments/confirmed_adjustments.jsonl"
)
ELIGIBLE_COSTS_PATH = Path("config/eligible_costs.yaml")


def run_import_production(
    raw_path: Path, config_dir: Path = DEFAULT_CONFIG_DIR
) -> ImportResult:
    """The normal, non-test production entry point: loads the canonical
    committed historical-confirmed registry, confirmed-adjustment source, and
    eligible-cost authority, then runs the real `run_import()` pipeline.

    Any loader above failing closed (missing/invalid file) propagates as the
    corresponding `Pending`/`SOURCE_UNAVAILABLE` outcome inside `run_import()`
    — this function performs no extra error handling of its own.
    """
    return run_import(
        raw_path,
        config_dir=config_dir,
        identity_registry=load_registry_from_jsonl(HISTORICAL_REGISTRY_PATH),
        confirmed_adjustment_source=load_confirmed_adjustments_from_jsonl(
            CONFIRMED_ADJUSTMENTS_PATH
        ),
        eligible_costs_authority=load_eligible_costs_authority(ELIGIBLE_COSTS_PATH),
    )
