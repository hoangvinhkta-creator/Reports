# TASK-REM-T07 — CI enforcement layer

## Metadata
Status:
READY

Phase:
PHASE-01 — Governance Foundation Repair

Task Mode:
MAJOR

Primary Agent Tier:
Tier B — Implementation

Escalation Tier:
Tier C — Advanced Reasoning

Difficulty:
2/5

Risk:
2/5

Blast Radius:
2/5

Project Profile:
PRODUCT

Closes Finding:
FIND-008 (LOW)

Resolves Risk:
RSK-004 (no E2 evidence path exists)

Ready Gate Verified In:
S002 — Roadmap Finalization (2026-08-22)

Completion Gate Status:
**FROZEN** — 2026-08-22, S002

## Objective
Wire the five governance validators into GitHub Actions so that governance
violations are caught automatically, and so the project gains its first
independent (E2) evidence source.

This task was DEFERRED in S001 pending the profile decision. The AUDIT →
PRODUCT transition (DEC-005) resolved that: `governance/core/PROJECT_PROFILE_STANDARD.md`
does not make CI mandatory at PRODUCT, but it is judged practical here, and it
is the only realistic E2 path for a single-owner repository (DEC-007).

Sequenced first in PHASE-01 — ahead of REM-T02 — specifically so that
REM-T02's CHECK-T02-05 (E2 REQUIRED) has a source to draw on.

## Scope
- `.github/workflows/governance.yml` at the **git repository root**
- Nothing else

## Out of Scope
- Any file under `governance/`
- Any change to validator logic (that is REM-T03)
- Branch protection rules and repository settings — these are owner-controlled
  and outside an agent's authority. Raise them; do not attempt to set them.

## Dependencies
- None. This task is independent of the repository layout.

## Blocks
- REM-T02 (supplies the E2 evidence source for CHECK-T02-05)

## Parallel-Safe With
- Nothing else is in flight; this is the first PHASE-01 task.

## Expected Touch Area

Allowed:
- `.github/workflows/` at the git repository root

Do not touch without Scope Expansion:
- Everything else in the repository

## Critical Design Constraint

REM-T02 will move all 73 tracked files to the repository root and must remain a
**path-only** move with zero content change. A workflow that hard-codes
`AI_ENGINEERING_CONSTITUTION_TEMPLATE_V3_2_FINAL_COMPACT/governance/scripts/...`
would break at that move and force REM-T02 to edit content, violating its
Scope Lock.

Therefore the workflow **must locate the validators by discovery**, not by a
hard-coded path — for example resolving them via `find` from the repository
root and failing loudly if the expected count is not found.

This constraint exists to protect REM-T02's purity. Do not "simplify" it away.

## Subtasks
- [ ] 07.1 Read `governance/product/14_CI_CD_RELEASE_RULES.md` before writing the workflow
- [ ] 07.2 Create `.github/workflows/governance.yml` triggering on push and pull_request
- [ ] 07.3 Discover validator scripts at runtime; fail the job if the expected count is not found
- [ ] 07.4 Run all five validators; `validate_refactor_preservation.py` is skipped unless a comparison directory is supplied, and the skip must be reported, not silent
- [ ] 07.5 Verify the workflow still resolves after a simulated directory move
- [ ] 07.6 Record that CI results are now an accepted E2 source in `PROJECT/PROJECT_PROFILE.md`
- [ ] 07.7 Raise branch protection with the owner as a recommendation

## Ready Gate — VERIFIED

Per `governance/core/TASK_READY_GATE_STANDARD.md`, MAJOR Ready Gate:

- [x] Objective is clear.
- [x] Scope is defined.
- [x] Out-of-scope is defined.
- [x] Dependencies are DONE or explicitly waived — none exist.
- [x] Expected touch area is identified.
- [x] Relevant requirements are understood.
- [x] Data impact is known — none.
- [x] Security impact is known — the workflow needs no secrets and no write permissions; it must declare `permissions: contents: read`.
- [x] Routing/API impact is known where relevant — NOT_APPLICABLE.
- [x] Migration prerequisites are available where relevant — NOT_APPLICABLE.
- [x] Difficulty is scored — 2/5.
- [x] Risk is scored — 2/5.
- [x] Blast Radius is scored — 2/5.
- [x] Primary agent tier is assigned — Tier B.
- [x] Escalation triggers are defined.
- [x] Completion Gate is finalized.
- [x] Completion Gate is frozen before implementation.

Status: **READY**

## Completion Gate — FROZEN

Frozen 2026-08-22 in S002. Do not remove or weaken a REQUIRED check to make
this task pass. Use COMPLETION GATE CHANGE PROPOSAL
(`governance/core/TASK_COMPLETION_GATE_STANDARD.md`) if a change is genuinely
warranted.

### Functional

#### CHECK-T07-01
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
A workflow run completes on the branch and executes all four unconditional
validators. Link the run.

#### CHECK-T07-02
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
The run is green — every validator exits 0.

#### CHECK-T07-03
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
The workflow FAILS when a validator fails. Prove it with a deliberate temporary
breakage on a scratch branch — a workflow that has never been observed failing
is not known to work. Do not merge the breakage.

### Reliability

#### CHECK-T07-04
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
Validator discovery survives a directory move. Simulate the REM-T02 layout
locally and confirm the discovery step still finds exactly five scripts.

#### CHECK-T07-05
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
The skip of `validate_refactor_preservation.py` is reported in the job log with
an explicit reason. A silent skip reads as a pass and is not acceptable.

### Security

#### CHECK-T07-06
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
The workflow declares least privilege (`permissions: contents: read`), consumes
no secrets, and pins actions to a specific version rather than a floating tag.

### Documentation

#### CHECK-T07-07
Priority:
RECOMMENDED

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
`PROJECT/PROJECT_PROFILE.md` records that CI results are an accepted E2 source,
and branch protection has been raised with the owner.

## Exit Criteria
- [ ] 100% REQUIRED checks PASS
- [ ] No critical unresolved defect
- [ ] Required evidence level satisfied
- [ ] `PROJECT/PROJECT_PROGRESS.md` updated
- [ ] Session handoff written

## Escalation Triggers
- The runner cannot execute the validators (Python version, permissions) →
  escalate to Tier C rather than weakening the checks.
- CI cannot be made to fail on a deliberate breakage → stop. A CI that cannot
  fail is worse than no CI, because it manufactures false E2 evidence.

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
Once this task is DONE, CI output becomes a legitimate E2 source under
`governance/core/EVIDENCE_STANDARD.md` ("Independent Evidence — CI result").
That directly unblocks REM-T02's CHECK-T02-05 and closes RSK-004.

Until CHECK-T07-03 passes, do not treat any CI green as evidence of anything.
