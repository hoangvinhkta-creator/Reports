"""
TASK-105D H-07 validator alignment (DEC-159 two-layer model).

Focused tests for governance/scripts/governance/validate_task_completion.py
proving the Gate Execution Record fallback path (Layer 2) is recognized
correctly and fails closed on every malformed/ambiguous/adversarial input,
while the pre-existing literal-Status path (Layer 1, legacy) is untouched.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
VALIDATOR_PATH = (
    REPO_ROOT / "governance/scripts/governance/validate_task_completion.py"
)

_spec = importlib.util.spec_from_file_location(
    "validate_task_completion", VALIDATOR_PATH
)
vtc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vtc)  # type: ignore[union-attr]

FROZEN_HASH = "a" * 64
OTHER_HASH = "b" * 64


def _task_text(*, check_status: str, gate_hash: str = FROZEN_HASH,
               check_id: str = "CHECK-TEST-01",
               evidence_level: str = "E1",
               evidence: str = "concrete evidence text") -> str:
    return f"""# TASK-TEST — Fixture

Status: DONE

## Completion Gate (FROZEN)

> GATE_SET_SHA256   : {gate_hash}

#### {check_id}

Priority: REQUIRED
Status: {check_status}
Evidence Level: {evidence_level}
Evidence:
{evidence}
Executed By:
tester
Timestamp:
2026-01-01
"""


def _record_text(*, gate_hash: str, rows: list[str], executed_by: str = "S999 tester") -> str:
    header = f"""# Fixture Gate Execution Record

Executed By:
{executed_by}

GATE_SET_SHA256 (recomputed):
`{gate_hash}`

## Table

| CHECK | Status | Evidence Level | Run Result | Test reference |
|---|---|---|---|---|
"""
    return header + "\n".join(rows) + "\n"


def _write(task_dir: Path, review_dir: Path, task_text: str, record_text: str | None,
           task_id: str = "TEST") -> None:
    task_dir.mkdir(parents=True, exist_ok=True)
    review_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / f"TASK-{task_id}-fixture.md").write_text(task_text, encoding="utf-8")
    if record_text is not None:
        (review_dir / f"TASK-{task_id}-GATE-EXECUTION-RECORD.md").write_text(
            record_text, encoding="utf-8"
        )


def test_a_legacy_embedded_pass_still_works(tmp_path):
    """A. A DONE task with a literal Status: PASS embedded in the REQUIRED
    check block keeps passing with no Gate Execution Record involved at
    all — the pre-existing Layer 1 path is untouched."""
    task_dir = tmp_path / "tasks"
    review_dir = tmp_path / "reviews"
    _write(task_dir, review_dir, _task_text(check_status="PASS"), record_text=None)

    errors, checked = vtc.run_validation(task_dir=task_dir, gate_exec_dir=review_dir)

    assert errors == []
    assert checked == 1


def test_b_valid_two_layer_pass_works(tmp_path):
    """B. Frozen embedded Status stays NOT_TESTED (byte-identical freeze);
    a canonical Gate Execution Record binds the exact GATE_SET_SHA256 +
    exact check ID with an authoritative PASS + Evidence Level + lineage.
    This must be accepted as effectively satisfied."""
    task_dir = tmp_path / "tasks"
    review_dir = tmp_path / "reviews"
    _write(
        task_dir, review_dir,
        _task_text(check_status="NOT_TESTED"),
        _record_text(
            gate_hash=FROZEN_HASH,
            rows=["| CHECK-TEST-01 | PASS | E2 | 5 passed | tests/test_x.py::TestY |"],
        ),
    )

    errors, checked = vtc.run_validation(task_dir=task_dir, gate_exec_dir=review_dir)

    assert errors == []
    assert checked == 1


def test_c_wrong_hash_fails(tmp_path):
    """C. The Gate Execution Record's declared GATE_SET_SHA256 does not
    match the frozen gate's declared hash — must fail closed even though
    the check ID and PASS result are otherwise present."""
    task_dir = tmp_path / "tasks"
    review_dir = tmp_path / "reviews"
    _write(
        task_dir, review_dir,
        _task_text(check_status="NOT_TESTED", gate_hash=FROZEN_HASH),
        _record_text(
            gate_hash=OTHER_HASH,
            rows=["| CHECK-TEST-01 | PASS | E2 | 5 passed | tests/test_x.py::TestY |"],
        ),
    )

    errors, checked = vtc.run_validation(task_dir=task_dir, gate_exec_dir=review_dir)

    assert checked == 1
    assert len(errors) == 1
    assert "CHECK-TEST-01" in errors[0]
    assert "does not match frozen gate" in errors[0]


def test_d_missing_check_fails(tmp_path):
    """D. The Gate Execution Record exists and binds the right hash, but
    has no row at all for this exact REQUIRED check ID — must fail
    closed rather than silently ignoring the gap."""
    task_dir = tmp_path / "tasks"
    review_dir = tmp_path / "reviews"
    _write(
        task_dir, review_dir,
        _task_text(check_status="NOT_TESTED", check_id="CHECK-TEST-01"),
        _record_text(
            gate_hash=FROZEN_HASH,
            rows=["| CHECK-TEST-02 | PASS | E2 | 5 passed | tests/test_x.py::TestOther |"],
        ),
    )

    errors, checked = vtc.run_validation(task_dir=task_dir, gate_exec_dir=review_dir)

    assert checked == 1
    assert len(errors) == 1
    assert "CHECK-TEST-01" in errors[0]
    assert "not present in any Gate Execution Record" in errors[0]


def test_e_fail_result_fails(tmp_path):
    """E. The authoritative Gate Execution Record binds the right hash and
    check ID but records the execution result as FAIL — must surface as a
    failure, never as an effective PASS."""
    task_dir = tmp_path / "tasks"
    review_dir = tmp_path / "reviews"
    _write(
        task_dir, review_dir,
        _task_text(check_status="NOT_TESTED"),
        _record_text(
            gate_hash=FROZEN_HASH,
            rows=["| CHECK-TEST-01 | FAIL | E2 | 1 failed | tests/test_x.py::TestY |"],
        ),
    )

    errors, checked = vtc.run_validation(task_dir=task_dir, gate_exec_dir=review_dir)

    assert checked == 1
    assert len(errors) == 1
    assert "reports FAIL" in errors[0]


def test_f_not_tested_without_execution_record_fails(tmp_path):
    """F. Frozen embedded Status is NOT_TESTED and there is no Gate
    Execution Record at all for this task — this must still fail (the
    original, pre-DEC-159 behavior for a bare NOT_TESTED REQUIRED check
    under a DONE task)."""
    task_dir = tmp_path / "tasks"
    review_dir = tmp_path / "reviews"
    _write(task_dir, review_dir, _task_text(check_status="NOT_TESTED"), record_text=None)

    errors, checked = vtc.run_validation(task_dir=task_dir, gate_exec_dir=review_dir)

    assert checked == 1
    assert len(errors) == 1
    assert "no Gate Execution Record found" in errors[0]


def test_duplicate_ambiguous_records_fail_closed(tmp_path):
    """MUST fail closed: two Gate Execution Records both bind the exact
    frozen GATE_SET_SHA256 and the exact check ID but disagree on the
    result. The validator must never guess which one is authoritative."""
    task_dir = tmp_path / "tasks"
    review_dir = tmp_path / "reviews"
    task_dir.mkdir(parents=True, exist_ok=True)
    review_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "TASK-TEST-fixture.md").write_text(
        _task_text(check_status="NOT_TESTED"), encoding="utf-8"
    )
    (review_dir / "TASK-TEST-GATE-EXECUTION-RECORD.md").write_text(
        _record_text(
            gate_hash=FROZEN_HASH,
            rows=["| CHECK-TEST-01 | PASS | E2 | 5 passed | tests/test_x.py::TestY |"],
        ),
        encoding="utf-8",
    )
    (review_dir / "TASK-TEST-GATE-EXECUTION-RECORD-2.md").write_text(
        _record_text(
            gate_hash=FROZEN_HASH,
            rows=["| CHECK-TEST-01 | FAIL | E2 | 1 failed | tests/test_x.py::TestY |"],
            executed_by="S999b tester",
        ),
        encoding="utf-8",
    )

    errors, checked = vtc.run_validation(task_dir=task_dir, gate_exec_dir=review_dir)

    assert checked == 1
    assert len(errors) == 1
    assert "ambiguous" in errors[0]


def test_malformed_binding_missing_lineage_fails(tmp_path):
    """MUST fail closed: the Gate Execution Record binds hash + check ID +
    PASS but has no Executed By lineage at all — malformed binding."""
    task_dir = tmp_path / "tasks"
    review_dir = tmp_path / "reviews"
    task_dir.mkdir(parents=True, exist_ok=True)
    review_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "TASK-TEST-fixture.md").write_text(
        _task_text(check_status="NOT_TESTED"), encoding="utf-8"
    )
    (review_dir / "TASK-TEST-GATE-EXECUTION-RECORD.md").write_text(
        f"""# Fixture Gate Execution Record (no lineage)

GATE_SET_SHA256 (recomputed):
`{FROZEN_HASH}`

## Table

| CHECK | Status | Evidence Level | Run Result | Test reference |
|---|---|---|---|---|
| CHECK-TEST-01 | PASS | E2 | 5 passed | tests/test_x.py::TestY |
""",
        encoding="utf-8",
    )

    errors, checked = vtc.run_validation(task_dir=task_dir, gate_exec_dir=review_dir)

    assert checked == 1
    assert len(errors) == 1
    assert "lineage" in errors[0]


def test_check_heading_with_trailing_description_resolves(tmp_path):
    """Regression: real Completion Gate headings look like
    'CHECK-105D-01 (G01) — description text', not a bare ID. The Layer 2
    lookup must key on the leading CHECK-<id> token, not the full heading
    line, or every real check silently fails to resolve."""
    task_dir = tmp_path / "tasks"
    review_dir = tmp_path / "reviews"
    task_text = f"""# TASK-TEST — Fixture

Status: DONE

## Completion Gate (FROZEN)

> GATE_SET_SHA256   : {FROZEN_HASH}

#### CHECK-TEST-01 (G01) — a human-readable description after the ID

Priority: REQUIRED
Status: NOT_TESTED
Evidence Level: E1
Evidence:
placeholder
Executed By:
tester
Timestamp:
2026-01-01
"""
    _write(
        task_dir, review_dir, task_text,
        _record_text(
            gate_hash=FROZEN_HASH,
            rows=["| CHECK-TEST-01 | PASS | E2 | 5 passed | tests/test_x.py::TestY |"],
        ),
    )

    errors, checked = vtc.run_validation(task_dir=task_dir, gate_exec_dir=review_dir)

    assert errors == []
    assert checked == 1


def test_real_repo_cli_output_is_unchanged():
    """Sanity: running the validator against the real repo tree still
    produces its normal top-level PASS/FAIL contract (checked as a smoke
    test, not asserting a specific count that would rot over time)."""
    errors, checked = vtc.run_validation()
    assert isinstance(errors, list)
    assert checked >= 1
