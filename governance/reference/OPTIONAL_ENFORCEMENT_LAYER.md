# Optional Enforcement Layer

## Included Validators

V3.2 Final ships executable validators:

```bash
python governance/scripts/governance/validate_structure.py
python governance/scripts/governance/validate_project_state.py
python governance/scripts/governance/validate_task_completion.py
python governance/scripts/governance/validate_evidence.py
```

## What They Enforce

### validate_structure.py
Checks mandatory governance paths exist.

### validate_project_state.py
Checks project profile values semantically:
- Selected Profile must be one of the allowed profiles.
- Progress Profile must be valid.
- Current Task Mode, when populated, must be MICRO / MAJOR / SPIKE.

### validate_task_completion.py
For task files with `Status: DONE`:
- REQUIRED checks cannot be FAIL / BLOCKED / NOT_TESTED.
- REQUIRED PASS checks must include Evidence Level.
- REQUIRED PASS checks must include concrete Evidence.

### validate_evidence.py
For REQUIRED PASS checks:
- Risk >= 3 requires E1/E2.
- E1/E2 requires Executed By.
- E1/E2 requires Timestamp.

## CI Integration

TEAM_PRODUCTION:
Run all validators in CI where practical.

PRODUCT:
Recommended at least before Phase/Release Gate.

SOLO_LITE:
Run manually when useful.

AUDIT:
Structure/state validation is useful; completion validators apply when remediation tasks begin.

## Principle

Machine enforcement supplements governance; it does not replace real tests or independent review.
