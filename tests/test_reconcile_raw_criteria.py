"""Unit tests for the raw employee-mapping criteria.

Independent Review #2 found `reconcile_raw()` returned 0 unconditionally.
Review #3 then split the criteria by certainty: invariants (F1, F3, F5) decide
the exit code; heuristics (F2, F4) are diagnostics that must never block on
their own.

These tests pin that split at the unit level. The end-to-end path — real
config file, production `EmployeeMapper`, real `.xlsx` — is covered separately
in `tests/test_reconcile_raw_integration.py`.
"""

from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "analysis"))

from reconcile_conversion import evaluate_raw_mapping  # noqa: E402

import pytest  # noqa: E402

from datetime import date  # noqa: E402

from app.modules.mapping.employee_mapper import (  # noqa: E402
    EmployeeMapper,
    InvalidEmployeeConfig,
    build_employee_master,
)
from app.modules.validation.employee_mapping import (  # noqa: E402
    MappingInput,
    collect_mapping_stats,
)

GROUP_ROWS = [{"code": "STANDARD_SALES"}, {"code": "NOI_THANH"}]

GROUPS = {"STANDARD_SALES", "NOI_THANH"}
SPAN_START = date(2026, 1, 1)
SPAN_END = date(2026, 9, 30)


def _employee(normalized, prefix, group="STANDARD_SALES", **extra):
    row = {
        "raw_prefix": prefix,
        "normalized": normalized,
        "group": group,
        "active": True,
        "effective_from": "2026-01-01",
        "effective_to": None,
    }
    row.update(extra)
    return row


EMPLOYEES = [
    _employee("Tín Phát", "Tín Phát"),
    _employee("Ly", "Vũ Hạnh Ly"),
    _employee("Thắng", "Phước Thắng"),
    _employee("Vinh", "Mr Vinh", group="NOI_THANH"),
]

HEALTHY_MAPPED = Counter({"Tín Phát": 1771, "Ly": 990, "Thắng": 411, "Vinh": 1814})
HEALTHY_GROUPS = {
    "Tín Phát": "STANDARD_SALES",
    "Ly": "STANDARD_SALES",
    "Thắng": "STANDARD_SALES",
    "Vinh": "NOI_THANH",
}
HEALTHY_UNMAPPED = Counter({"Thảo Linh": 83, "Nguyễn Thị Minh Bảo": 1})


# HD-110-16: 15 lời gọi `evaluate_raw_mapping(...)` 8-tham-số-vị-trí được
# chuyển sang **một** `MappingStats` canonical. Ý định từng test giữ nguyên;
# thứ đổi là cách nói ra cùng một tình huống. Trước đây bộ đếm và chỉ mục dòng
# là hai tham số rời, nên con số trong message và số dòng trong provenance có
# hai nguồn khác nhau và đo được là chúng bất đồng (RC-3).
#
# `_synth()` dựng đúng số dòng thô mà mỗi Counter mô tả, nên `MappingStats`
# thật sự mang provenance thay vì một con số trần.
_ROW = [0]


def _synth(mapped, unmapped, ambiguous_raw, employees, groups, start, end):
    mapper = EmployeeMapper(build_employee_master(employees, groups))
    inputs = []
    when = start or SPAN_START
    for name, count in mapped.items():
        record = next((e for e in employees if e["normalized"] == name), None)
        prefix = record["raw_prefix"] if record else name
        for _ in range(count):
            _ROW[0] += 1
            inputs.append(MappingInput(
                source_file="synthetic.xlsx", source_row=_ROW[0],
                employee_raw=prefix, when=when, normalized=name,
                group=HEALTHY_GROUPS.get(name),
            ))
    for raw_value, count in unmapped.items():
        for _ in range(count):
            _ROW[0] += 1
            inputs.append(MappingInput(
                source_file="synthetic.xlsx", source_row=_ROW[0],
                employee_raw=raw_value, when=when, normalized=None, group=None,
            ))
    stats = collect_mapping_stats(inputs, mapper)
    if ambiguous_raw:
        object.__setattr__(stats, "ambiguities", dict(ambiguous_raw))
    if start is not None:
        object.__setattr__(stats, "dataset_start", start)
    if end is not None:
        object.__setattr__(stats, "dataset_end", end)
    return stats


def _evaluate(mapped=None, unmapped=None, ambiguities=None, employees=None,
              groups=None, start=SPAN_START, end=SPAN_END):
    return evaluate_raw_mapping(_synth(
        mapped if mapped is not None else HEALTHY_MAPPED,
        unmapped if unmapped is not None else HEALTHY_UNMAPPED,
        ambiguities or {},
        employees if employees is not None else EMPLOYEES,
        GROUP_ROWS,
        start,
        end,
    ))


def test_healthy_master_data_has_no_failures_or_warnings():
    verdict = _evaluate()
    assert verdict.hard_failures == []
    assert verdict.warnings == []


# --- Hard failures: F1, F3, F5 ---------------------------------------------


# HD-110-17: F1 được THAY THẾ bởi fail-fast tại biên master, không bị bỏ.
# Ý định của hai test giữ nguyên — "master khai group không tồn tại KHÔNG được
# đi lọt" — nhưng nay nó bị chặn SỚM HƠN: master ấy không parse được, nên
# Review Queue không bao giờ nhận được trạng thái đó.
def test_f1_group_not_declared_is_rejected_at_the_master_boundary():
    broken = EMPLOYEES[:3] + [_employee("Vinh", "Mr Vinh", group="NOI_THAN")]
    with pytest.raises(InvalidEmployeeConfig, match="employee_groups"):
        build_employee_master(broken, GROUP_ROWS)


def test_f1_missing_group_field_is_rejected_at_the_master_boundary():
    row = {k: v for k, v in EMPLOYEES[3].items() if k != "group"}
    with pytest.raises(InvalidEmployeeConfig, match="group"):
        build_employee_master(EMPLOYEES[:3] + [row], GROUP_ROWS)


def test_f3_ambiguity_is_a_hard_failure():
    verdict = _evaluate(ambiguities={"Mr Vinh Anh": {"Vinh", "Ly"}})
    assert any(v.startswith("F3") for v in verdict.hard_failures)


def test_f5_nothing_mapped_at_all_is_a_hard_failure():
    verdict = _evaluate(mapped=Counter(), unmapped=Counter({"Ai Đó": 14496}))
    assert any(v.startswith("F5") for v in verdict.hard_failures)


# --- F2: effective-window aware, warning only (Review #3, Finding 1) --------


def test_f2_effective_employee_without_rows_is_a_warning_not_a_failure():
    mapped = Counter({k: v for k, v in HEALTHY_MAPPED.items() if k != "Vinh"})
    verdict = _evaluate(mapped=mapped)
    assert verdict.hard_failures == []
    assert any(v.startswith("F2") and "Vinh" in v for v in verdict.warnings)


def test_f2_employee_not_yet_effective_is_info():
    future = EMPLOYEES[:3] + [
        _employee("Vinh", "Mr Vinh", group="NOI_THANH",
                  effective_from="2030-01-01")
    ]
    mapped = Counter({k: v for k, v in HEALTHY_MAPPED.items() if k != "Vinh"})
    verdict = _evaluate(mapped=mapped, employees=future)
    assert verdict.hard_failures == []
    assert not any(v.startswith("F2") for v in verdict.warnings)
    assert any("Vinh" in i for i in verdict.info)


def test_f2_employee_no_longer_effective_is_info():
    left = EMPLOYEES[:3] + [
        _employee("Vinh", "Mr Vinh", group="NOI_THANH",
                  effective_from="2024-01-01", effective_to="2025-12-31")
    ]
    mapped = Counter({k: v for k, v in HEALTHY_MAPPED.items() if k != "Vinh"})
    verdict = _evaluate(mapped=mapped, employees=left)
    assert verdict.hard_failures == []
    assert not any(v.startswith("F2") for v in verdict.warnings)


def test_f2_inactive_employee_is_info():
    inactive = EMPLOYEES[:3] + [
        _employee("Vinh", "Mr Vinh", group="NOI_THANH", active=False)
    ]
    mapped = Counter({k: v for k, v in HEALTHY_MAPPED.items() if k != "Vinh"})
    verdict = _evaluate(mapped=mapped, employees=inactive)
    assert verdict.hard_failures == []
    assert not any(v.startswith("F2") for v in verdict.warnings)
    assert any("active: false" in i for i in verdict.info)


# --- F4: warning only, threshold from the data (Review #3, Finding 3) ------


def test_f4_is_a_warning_never_a_hard_failure():
    unmapped = Counter(HEALTHY_UNMAPPED) + Counter({"Mr Quý": 2810})
    verdict = _evaluate(unmapped=unmapped)
    assert verdict.hard_failures == [], "F4 không được tự làm FAIL"
    assert any(v.startswith("F4") and "Mr Quý" in v for v in verdict.warnings)


def test_f4_threshold_comes_from_the_data_not_a_constant():
    big = Counter({"Tín Phát": 5000, "Ly": 4000, "Thắng": 3000, "Vinh": 2000})
    assert _evaluate(mapped=big, unmapped=Counter({"Ai Đó": 500})).warnings == []

    small = Counter({"Tín Phát": 400, "Ly": 300, "Thắng": 200, "Vinh": 100})
    verdict = _evaluate(mapped=small, unmapped=Counter({"Ai Đó": 500}))
    assert any(v.startswith("F4") for v in verdict.warnings)


def test_f4_small_legacy_names_stay_below_the_boundary():
    # A criterion that fires on healthy data is as useless as one that never
    # fires: the real legacy tail (83, 1) must stay quiet.
    assert not any(v.startswith("F4") for v in _evaluate().warnings)


# --- The reviewer's own scenario -------------------------------------------


def test_review_2_scenario_still_surfaces_although_it_no_longer_hard_fails():
    """Review #2's falsification: break most prefixes so only a fraction maps.

    Under Review #3's rules this is diagnosed rather than hard-failed at the
    criteria level — the hard evidence for a broken mapping comes from the
    integration falsification instead (see the integration test module).
    """
    mapped = Counter({"Tín Phát": 1771, "Thắng": 411})
    unmapped = Counter(
        {"Đức Hiệp": 5328, "Mr Quý": 2810, "Mr Vinh": 1814,
         "Vũ Hạnh Ly": 990, "Thảo Linh": 83}
    )
    verdict = _evaluate(mapped=mapped, unmapped=unmapped)

    ratio = sum(mapped.values()) / (sum(mapped.values()) + sum(unmapped.values()))
    assert ratio < 0.20
    assert any(v.startswith("F2") for v in verdict.warnings)
    assert any(v.startswith("F4") for v in verdict.warnings)
