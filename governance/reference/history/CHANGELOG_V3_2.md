# CHANGELOG — V3.2

## Runtime Wiring
- Added Task Mode to Task Definition template.
- Added Evidence Level, Evidence, Executed By, Timestamp to gate records.
- Added evidence table to Session Handoff.
- Added Profile and Current Task Mode to Project Progress.
- Added inline Micro Task tracking.

## Micro Task
- Added real `governance/templates/MICRO_TASK_CHECKLIST.md`.
- Added separate MICRO / MAJOR / SPIKE Ready Gates.

## Evidence
- Completion Gate now directly references Evidence Standard.
- Added risk-based evidence requirements to Completion Gate.
- Added explicit prohibition on fabricated evidence to Forbidden Actions.
- Added Solo Independent Review Procedure for E2.

## Integration
- Rewrote CLAUDE.md instead of using an appended addendum.
- Rewrote Session Orchestration so Profile Selection is step 0 in the actual S000 flow.
- Added new standards to the main governance index.

## Profiles
- Made profile inheritance explicit.
- Added explicit AUDIT ruleset.
- AUDIT remains read-only by default.

## Enforcement
- Added executable Python validators:
  - `governance/scripts/governance/validate_structure.py`
  - `governance/scripts/governance/validate_project_state.py`

## Acceptance
- Added `ACCEPTANCE_CHECKLIST_V3_2.md`.
