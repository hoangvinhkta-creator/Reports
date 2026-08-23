"""Falsification tests for the raw employee-mapping failure criteria.

Independent Review #2 found that `reconcile_raw()` printed a tidy table and
returned 0 unconditionally: a badly broken `employees.yaml` still produced a
PASS. These tests pin the criteria that now make it fail, using synthetic
counts so they run without the real (uncommitted) sales export.

Each test breaks production master data in one specific way and asserts the
criteria catch it. A test that only checked the healthy case would prove
nothing — the whole defect was that the healthy-looking output was
unfalsifiable.
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "analysis"))

from reconcile_conversion import evaluate_raw_mapping  # noqa: E402

GROUPS = {"STANDARD_SALES", "NOI_THANH"}

EMPLOYEES = [
    {"raw_prefix": "Tín Phát", "normalized": "Tín Phát", "group": "STANDARD_SALES"},
    {"raw_prefix": "Vũ Hạnh Ly", "normalized": "Ly", "group": "STANDARD_SALES"},
    {"raw_prefix": "Phước Thắng", "normalized": "Thắng", "group": "STANDARD_SALES"},
    {"raw_prefix": "Mr Vinh", "normalized": "Vinh", "group": "NOI_THANH"},
]

HEALTHY_MAPPED = Counter({"Tín Phát": 1771, "Ly": 990, "Thắng": 411, "Vinh": 1814})
HEALTHY_GROUPS = {
    "Tín Phát": "STANDARD_SALES",
    "Ly": "STANDARD_SALES",
    "Thắng": "STANDARD_SALES",
    "Vinh": "NOI_THANH",
}
HEALTHY_UNMAPPED = Counter({"Thảo Linh": 83, "Nguyễn Thị Minh Bảo": 1})


def _evaluate(mapped=None, unmapped=None, collisions=None, employees=None,
              groups=None):
    return evaluate_raw_mapping(
        mapped if mapped is not None else HEALTHY_MAPPED,
        HEALTHY_GROUPS,
        unmapped if unmapped is not None else HEALTHY_UNMAPPED,
        collisions or {},
        employees if employees is not None else EMPLOYEES,
        groups if groups is not None else GROUPS,
    )


def test_healthy_master_data_produces_no_violations():
    assert _evaluate() == []


# --- F1: referential integrity of employee_group ---------------------------


def test_f1_group_not_declared_is_a_violation():
    broken = [dict(EMPLOYEES[3], group="NOI_THAN")]  # typo
    violations = _evaluate(employees=EMPLOYEES[:3] + broken)
    assert any(v.startswith("F1") for v in violations)


def test_f1_missing_group_field_is_a_violation():
    broken = [{k: v for k, v in EMPLOYEES[3].items() if k != "group"}]
    violations = _evaluate(employees=EMPLOYEES[:3] + broken)
    assert any(v.startswith("F1") for v in violations)


# --- F2: no dead master data ------------------------------------------------


def test_f2_configured_employee_matching_nothing_is_a_violation():
    # A garbled raw_prefix: the employee stays in config but matches no row.
    mapped = Counter({k: v for k, v in HEALTHY_MAPPED.items() if k != "Vinh"})
    violations = _evaluate(mapped=mapped)
    assert any(v.startswith("F2") and "Vinh" in v for v in violations)


# --- F3: unambiguous mapping ------------------------------------------------


def test_f3_prefix_collision_is_a_violation():
    violations = _evaluate(collisions={"Mr Vinh Anh": {"Vinh", "Ly"}})
    assert any(v.startswith("F3") for v in violations)


# --- F4: volume boundary ----------------------------------------------------


def test_f4_unmapped_name_outweighing_smallest_mapped_is_a_violation():
    # Deleting an employee from config: their rows land in `unmapped` and
    # dwarf the smallest configured seller.
    unmapped = Counter(HEALTHY_UNMAPPED) + Counter({"Mr Quý": 2810})
    violations = _evaluate(unmapped=unmapped)
    assert any(v.startswith("F4") and "Mr Quý" in v for v in violations)


def test_f4_threshold_comes_from_the_data_not_a_constant():
    # Same unmapped volume, but every configured seller is bigger than it —
    # so the same 500 rows are a violation in one dataset and not in another.
    big = Counter({"Tín Phát": 5000, "Ly": 4000, "Thắng": 3000, "Vinh": 2000})
    assert _evaluate(mapped=big, unmapped=Counter({"Ai Đó": 500})) == []

    small = Counter({"Tín Phát": 400, "Ly": 300, "Thắng": 200, "Vinh": 100})
    violations = _evaluate(mapped=small, unmapped=Counter({"Ai Đó": 500}))
    assert any(v.startswith("F4") for v in violations)


def test_f4_small_legacy_names_stay_below_the_boundary():
    # The real unmapped set (83, 14, 7, 2, 1) must NOT trip F4 — otherwise the
    # criterion would just fail everything and prove nothing either.
    assert not any(v.startswith("F4") for v in _evaluate())


# --- F5: degenerate case ----------------------------------------------------


def test_f5_nothing_mapped_at_all_is_a_violation():
    violations = _evaluate(mapped=Counter(), unmapped=Counter({"Ai Đó": 14496}))
    assert any(v.startswith("F5") for v in violations)


# --- The reviewer's own scenario -------------------------------------------


def test_reviewer_scenario_mapped_ratio_collapses_to_about_fifteen_percent():
    """Independent Review #2's falsification: break most prefixes so only a
    small fraction still maps. The old code returned 0 here."""
    mapped = Counter({"Tín Phát": 1771, "Thắng": 411})
    unmapped = Counter(
        {"Đức Hiệp": 5328, "Mr Quý": 2810, "Mr Vinh": 1814,
         "Vũ Hạnh Ly": 990, "Đức Kiên": 733, "Lê Mạnh Hoàng": 532,
         "Thảo Linh": 83}
    )
    violations = _evaluate(mapped=mapped, unmapped=unmapped)

    ratio = sum(mapped.values()) / (sum(mapped.values()) + sum(unmapped.values()))
    assert ratio < 0.20, "kịch bản phải làm mapped ratio sụp xuống"
    assert violations, "mapping hỏng nặng BẮT BUỘC phải FAIL"
    assert any(v.startswith("F2") for v in violations)  # Ly, Vinh dead in config
    assert any(v.startswith("F4") for v in violations)  # big unmapped names
