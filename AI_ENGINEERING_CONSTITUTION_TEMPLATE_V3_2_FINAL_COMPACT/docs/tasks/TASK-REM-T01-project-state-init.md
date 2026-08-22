# TASK-REM-T01 — Initialize project state (complete S000)

## Metadata
Status:
PLANNED

Phase:
PHASE-01 — Governance Foundation Repair

Task Mode:
MAJOR

Primary Agent Tier:
standard

Escalation Tier:
senior

Difficulty:
2/5

Risk:
2/5

Blast Radius:
2/5

Project Profile:
AUDIT (transitions during this task)

Closes Finding:
FIND-002 (HIGH)

## Objective
Complete the S000 — PROJECT OPEN procedure that was never executed against this
repository, so that Session Open Protocol works for every later session and a
real profile governs the remediation work.

S001 performed a minimum bootstrap only (DEC-001). This task finishes the job.

## Scope
- `PROJECT/PROJECT_PROFILE.md`
- `PROJECT/PROJECT_PROGRESS.md`
- `PROJECT/PROJECT_DECISIONS.md`

## Out of Scope
- Any file under `governance/`
- Any remediation of another finding
- Any application code

## Dependencies
- S002 — Roadmap Finalization must mark this task READY.

## Blocks
- REM-T02, REM-T03, REM-T04, REM-T05, REM-T06, REM-T07 (all gated on a real
  profile and a real progress file).
- REM-T07 specifically depends on subtask 01.1's profile decision.

## Parallel-Safe With
- None. This is the first task.

## Expected Touch Area

Allowed:
- `PROJECT/*.md`

Do not touch without Scope Expansion:
- `governance/**`
- `docs/audit/**` (S001 artifacts are the audit record; do not rewrite them)

## Subtasks
- [ ] 01.1 Confirm or revise the post-audit profile (AUDIT → PRODUCT or SOLO_LITE), with written justification
- [ ] 01.2 Record mandatory / conditional / not-applicable rule groups for the chosen profile
- [ ] 01.3 Complete phase and task decomposition in `PROJECT/PROJECT_PROGRESS.md`
- [ ] 01.4 Record preliminary Completion Gates for Phase-01 tasks
- [ ] 01.5 Re-run `validate_project_state.py`
- [ ] 01.6 Record the profile-transition decision as DEC-005

## Ready Gate
Use `governance/core/TASK_READY_GATE_STANDARD.md`.

- [ ] S002 has run and this task's Completion Gate is frozen
- [ ] Profile transition question has been put to the owner
- [ ] Scope Lock loaded

## Completion Gate
Use `governance/core/TASK_COMPLETION_GATE_STANDARD.md` and `governance/core/EVIDENCE_STANDARD.md`.

Status of this gate:
PRELIMINARY — NOT FROZEN. Freeze in S002.

### Governance

#### CHECK-T01-01
Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E1

Evidence:
...

Executed By:
...

Timestamp:
...

Requirement:
`python3 governance/scripts/governance/validate_project_state.py` exits 0.

#### CHECK-T01-02
Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E1

Evidence:
...

Executed By:
...

Timestamp:
...

Requirement:
No `...` placeholder value remains in `PROJECT/PROJECT_PROFILE.md`.

#### CHECK-T01-03
Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E1

Evidence:
...

Executed By:
...

Timestamp:
...

Requirement:
`PROJECT/PROJECT_PROGRESS.md` names a Current Task and a Next Recommended Task,
and its roadmap contains no placeholder entries.

#### CHECK-T01-04
Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E0

Evidence:
...

Executed By:
...

Timestamp:
...

Requirement:
The profile transition decision is recorded in `PROJECT/PROJECT_DECISIONS.md`
with a justification. E0 is acceptable here because this is a recorded human
decision, not an executable check.

## Exit Criteria
- [ ] 100% REQUIRED checks PASS
- [ ] No critical unresolved defect
- [ ] Required evidence level satisfied
- [ ] Required documentation updated
- [ ] Project progress updated
- [ ] Session handoff written

## Escalation Triggers
- The owner declines to choose a post-audit profile → task BLOCKED, do not guess.
- Decomposition reveals application scope not covered by the S001 baseline →
  ROADMAP CHANGE PROPOSAL before continuing.

## Changed Files Registry

Created:
- ...

Modified:
- ...

Deleted:
- ...

Migration Impact:
- None.

## Notes
FIND-002 remains OPEN until this task is DONE. The S001 bootstrap (DEC-001)
mitigated it enough to run discovery; it did not close it.
