# FINAL ACCEPTANCE CHECKLIST — V3.2 FINAL

## F-01 Project State Validator
- [ ] Selected Profile is validated against allowed profile values.
- [ ] Progress Profile is validated against allowed profile values.
- [ ] Current Task Mode is semantically validated when populated.

## F-02 Task / Evidence Enforcement
- [ ] validate_task_completion.py exists.
- [ ] DONE tasks cannot contain REQUIRED FAIL.
- [ ] DONE tasks cannot contain REQUIRED BLOCKED.
- [ ] DONE tasks cannot contain REQUIRED NOT_TESTED.
- [ ] REQUIRED PASS checks require Evidence Level and Evidence.
- [ ] validate_evidence.py exists.
- [ ] Risk >= 3 REQUIRED PASS requires E1/E2.
- [ ] E1/E2 requires Executed By and Timestamp.

## F-03 Manifest
- [ ] Manifest count equals actual packaged file count.

## F-04 Micro Task Source of Truth
- [ ] PROJECT_PROGRESS does not duplicate Micro Task gate criteria.
- [ ] Canonical Micro checklist is `governance/templates/MICRO_TASK_CHECKLIST.md`.

## F-05 S000 Source of Truth
- [ ] CLAUDE.md does not duplicate the full S000 procedure.
- [ ] governance/core/00_SESSION_ORCHESTRATION.md is canonical.

## F-06 Validation Evidence
- [ ] Validation report includes Executed By.
- [ ] Validation report includes Timestamp.
- [ ] Validation report includes E1 command output.

## F-07 E2 Storage
- [ ] docs/reviews/ exists.
- [ ] E2 review template exists.
- [ ] Evidence Standard specifies E2 artifact storage.

## F-08 Core Structure Validation
- [ ] validate_structure.py checks governance/core/04_SECURITY_RULES.md.
- [ ] validate_structure.py checks governance/core/11_FORBIDDEN_ACTIONS.md.

## F-09 Root Cleanup
- [ ] Historical changelogs/checklists are moved to docs/history/.
- [ ] Root contains one current governance/reference/CHANGELOG.md.

## Framework Freeze
After this checklist passes:
- Do not add more governance features before a real-project pilot.
- Pilot the framework on a known existing project.
- Open the next version only from observed pilot findings.
