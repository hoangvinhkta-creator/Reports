# ACCEPTANCE CHECKLIST — V3.2

## A. Runtime Wiring
- [ ] Task Definition includes Task Mode.
- [ ] Task Definition includes Evidence Level.
- [ ] Task Definition includes Executed By and Timestamp.
- [ ] Session Handoff includes evidence table.
- [ ] Project Progress includes Profile.
- [ ] Project Progress includes Current Task Mode.
- [ ] Project Progress includes inline Micro Task section.

## B. Micro Task
- [ ] `governance/templates/MICRO_TASK_CHECKLIST.md` exists.
- [ ] Micro Ready Gate exists.
- [ ] Micro Completion Gate exists.
- [ ] Promotion to MAJOR is defined.

## C. Evidence
- [ ] Completion Gate directly references `governance/core/EVIDENCE_STANDARD.md`.
- [ ] Risk-based evidence requirements are explicit.
- [ ] Unexecuted checks become NOT_TESTED.
- [ ] Forbidden Actions prohibits fabricated evidence.
- [ ] Solo E2 independent review procedure exists.

## D. Integrated Governance
- [ ] `CLAUDE.md` has one integrated top-level structure.
- [ ] S000 begins with Profile Selection.
- [ ] `governance/core/00_SESSION_ORCHESTRATION.md` includes profile selection in the main ordered flow.
- [ ] Relevant Governance Files includes all new V3.1/V3.2 standards.

## E. Profiles
- [ ] SOLO_LITE inheritance is explicit.
- [ ] PRODUCT inheritance is explicit.
- [ ] TEAM_PRODUCTION inheritance is explicit.
- [ ] AUDIT required rules are explicitly listed.
- [ ] AUDIT defaults to READ ONLY.

## F. Enforcement
- [ ] `governance/scripts/governance/validate_structure.py` exists.
- [ ] `governance/scripts/governance/validate_project_state.py` exists.
- [ ] Both validators execute successfully on initialized package structure where applicable.

## G. Package
- [ ] No root/runtime template ambiguity.
- [ ] `docs/tasks/` exists.
- [ ] `docs/sessions/` exists.
- [ ] Manifest count matches package contents.

## Final Result
ACCEPTED / CHANGES_REQUIRED

Reviewer:
...

Date:
...

Notes:
...
