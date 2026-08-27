"""Integration falsification for the raw employee-mapping reconciliation.

Independent Review #3, Finding 2: feeding synthetic `Counter`s straight into
the evaluator tests the criteria but skips everything that actually reads
master data. These tests run the real path end to end —

    temporary modified `employees.yaml`
        -> production `EmployeeMapper`
        -> real `.xlsx` raw fixture (openpyxl, same reader shape as production)
        -> `reconcile_raw()`
        -> exit code

— and assert that a broken production mapping cannot come back zero.

The fixture is the same synthetic workbook the pipeline tests use: no real
customer data is committed (DEC-108).
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

import pytest
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools" / "analysis"))

import reconcile_conversion  # noqa: E402
from reconcile_conversion import reconcile_raw  # noqa: E402

from app.modules.mapping.employee_mapper import (  # noqa: E402
    EmployeeMapper,
    InvalidEmployeeConfig,
)

REPO = Path(__file__).resolve().parents[1]
PROD_CONFIG = REPO / "config"


@pytest.fixture
def config_copy(tmp_path, monkeypatch):
    """A writable copy of production config, wired into the module under test."""
    target = tmp_path / "config"
    shutil.copytree(PROD_CONFIG, target)
    monkeypatch.setattr(reconcile_conversion, "CONFIG", target)
    return target


def _edit_employees(config_dir: Path, mutate):
    path = config_dir / "employees.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    mutate(data)
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8"
    )
    return path


def _run(config_dir: Path, raw_path: Path) -> int:
    """Production mapper built from the (possibly broken) config, then the
    real reconciliation over a real .xlsx."""
    mapper = EmployeeMapper.from_yaml(config_dir / "employees.yaml")
    return reconcile_raw(raw_path, mapper)


# --- Healthy baseline -------------------------------------------------------


def test_unmodified_config_passes_on_the_fixture(config_copy, synthetic_raw_path):
    # The fixture only contains 4 of the 8 configured employees. Under the
    # Review #3 rules that is a WARNING (they may simply have had no sales),
    # never a hard failure — so the run must still come back zero.
    assert _run(config_copy, synthetic_raw_path) == 0


def test_employees_absent_from_the_fixture_do_not_hard_fail(
    config_copy, synthetic_raw_path, capsys
):
    _run(config_copy, synthetic_raw_path)
    out = capsys.readouterr().out
    assert "HARD FAILURE" in out
    assert "WARNING / REVIEW SIGNAL" in out
    # Kiên sells nothing in this fixture: diagnosed, not failed.
    assert "F2" in out and "Kiên" in out


# --- F1: invalid group reference (HARD) -------------------------------------
#
# **Canonical migration of the expected failure mode (HD-110-09, DEC-133).**
# The intent of these two tests is unchanged and still the whole point: an
# employee master carrying a broken `group` reference MUST NOT get through.
# What changed is WHERE the system stops it.
#
#     before   detected AFTER reconciliation   -> `reconcile_raw()` exit code > 0
#     after    rejected BEFORE reconciliation  -> `InvalidEmployeeConfig` at the
#                                                 canonical employee master loader
#
# The new mechanism is strictly stronger: the run is refused before a single
# transaction is read, rather than reported once the whole reconciliation has
# already been computed. `employee_group` is a lookup dimension of
# `config/conversion_rates.yaml`, so a typo silently moves the conversion rate
# (measured: `NOI_THANH` 2.0% -> `NOI_THAN` 5.5%). A non-blocking queue line
# was never a proportionate answer to that.
#
# Only these two tests migrate. Every other TASK-108A-1 reconciliation test is
# untouched, and behaviour on VALID config is byte-identical (L3).


def test_group_renamed_out_of_existence_fails(config_copy, synthetic_raw_path):
    def mutate(data):
        for row in data["employees"]:
            if row["normalized"] == "Vinh":
                row["group"] = "NOI_THAN"  # typo, not declared

    _edit_employees(config_copy, mutate)
    with pytest.raises(InvalidEmployeeConfig, match="employee_groups"):
        _run(config_copy, synthetic_raw_path)


def test_declared_group_deleted_fails(config_copy, synthetic_raw_path):
    def mutate(data):
        data["employee_groups"] = [
            g for g in data["employee_groups"] if g["code"] != "STANDARD_SALES"
        ]

    _edit_employees(config_copy, mutate)
    with pytest.raises(InvalidEmployeeConfig, match="employee_groups"):
        _run(config_copy, synthetic_raw_path)


# --- F3: real ambiguity inside one effective window (HARD) ------------------


def test_overlapping_prefixes_in_the_same_window_fail(
    config_copy, synthetic_raw_path
):
    def mutate(data):
        twin = dict(data["employees"][0])
        twin["raw_prefix"] = "Vũ Hạnh"  # overlaps "Vũ Hạnh Ly", same period
        twin["normalized"] = "Ly Bản Sao"
        data["employees"].append(twin)

    _edit_employees(config_copy, mutate)
    assert _run(config_copy, synthetic_raw_path) > 0


def test_same_prefixes_in_disjoint_windows_do_not_fail(
    config_copy, synthetic_raw_path
):
    # Review #3, Finding 1: a handover — the same person's rows re-keyed to a
    # successor from a later date — is NOT an ambiguity. The fixture is all
    # January 2026, so the 2027 row can never collide with it.
    def mutate(data):
        successor = dict(data["employees"][0])
        successor["raw_prefix"] = "Vũ Hạnh"
        successor["normalized"] = "Ly Kế Nhiệm"
        successor["effective_from"] = "2027-01-01"
        successor["effective_to"] = None
        data["employees"].append(successor)

    _edit_employees(config_copy, mutate)
    assert _run(config_copy, synthetic_raw_path) == 0


# --- F5: mapping produces nothing (HARD) ------------------------------------


def test_every_prefix_broken_fails(config_copy, synthetic_raw_path):
    def mutate(data):
        for row in data["employees"]:
            row["raw_prefix"] = "ZZZ " + row["raw_prefix"]

    _edit_employees(config_copy, mutate)
    assert _run(config_copy, synthetic_raw_path) > 0


def test_all_employees_removed_fails(config_copy, synthetic_raw_path):
    _edit_employees(config_copy, lambda data: data.update({"employees": []}))
    assert _run(config_copy, synthetic_raw_path) > 0


# --- Effective-window handling for F2 (Review #3, Finding 1) ----------------


def test_employee_not_yet_effective_is_info_not_warning(
    config_copy, synthetic_raw_path, capsys
):
    def mutate(data):
        for row in data["employees"]:
            if row["normalized"] == "Kiên":
                row["effective_from"] = "2030-01-01"

    _edit_employees(config_copy, mutate)
    assert _run(config_copy, synthetic_raw_path) == 0
    out = capsys.readouterr().out
    assert "INFO" in out
    assert "ngoài phạm vi dữ liệu" in out


def test_inactive_employee_is_info_not_warning(
    config_copy, synthetic_raw_path, capsys
):
    def mutate(data):
        for row in data["employees"]:
            if row["normalized"] == "Kiên":
                row["active"] = False

    _edit_employees(config_copy, mutate)
    assert _run(config_copy, synthetic_raw_path) == 0
    out = capsys.readouterr().out
    assert "active: false" in out


# --- F4 is a signal, never a blocker (Review #3, Finding 3) -----------------


def test_f4_volume_signal_warns_but_does_not_fail(
    config_copy, synthetic_raw_path, capsys
):
    # Drop Ly from master data. Her fixture rows outnumber the smallest
    # remaining mapped employee, so F4 fires — as a warning only.
    def mutate(data):
        data["employees"] = [
            r for r in data["employees"] if r["normalized"] != "Ly"
        ]

    _edit_employees(config_copy, mutate)
    assert _run(config_copy, synthetic_raw_path) == 0, "F4 không được tự làm FAIL"
    out = capsys.readouterr().out
    warning_block = out.split("WARNING / REVIEW SIGNAL")[1]
    assert "F4" in warning_block
    assert "Vũ Hạnh Ly" in warning_block
