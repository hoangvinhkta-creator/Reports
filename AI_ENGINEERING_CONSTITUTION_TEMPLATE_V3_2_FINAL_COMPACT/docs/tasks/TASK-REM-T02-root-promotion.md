# TASK-REM-T02 — Promote governance package to repository root

## Metadata
Status:
PLANNED

Phase:
PHASE-01 — Governance Foundation Repair

Task Mode:
MAJOR

Primary Agent Tier:
senior

Escalation Tier:
senior + human confirmation

Difficulty:
2/5

Risk:
3/5

Blast Radius:
5/5

Project Profile:
Set by REM-T01.1

Closes Finding:
FIND-001 (HIGH)

## Objective
Move `CLAUDE.md`, `PROJECT/`, `docs/` and `governance/` from
`AI_ENGINEERING_CONSTITUTION_TEMPLATE_V3_2_FINAL_COMPACT/` to the repository
root, so that `CLAUDE.md` is the root governance entry point as
`governance/reference/START_HERE_USAGE_GUIDE_V3_2.md` PHẦN 1 requires.

## Scope
- `git mv` of the four top-level package entries to the repository root
- Removal of the emptied wrapper directory

## Out of Scope
**Any content edit whatsoever.** This is a path-only move, per the
content-preservation rule in `governance/README.md`:

> Directory refactors MUST NOT rewrite, summarize, shorten, or delete
> governance semantics.

Reference repairs belong to REM-T04. Validator changes belong to REM-T03.

## Dependencies
- REM-T01 DONE

## Blocks
- REM-T03, REM-T04, REM-T05, REM-T06

## Parallel-Safe With
- None. Every other task touches files this task moves.

## Expected Touch Area

Allowed:
- File paths only, repository-wide

Do not touch without Scope Expansion:
- File contents, repository-wide

## Subtasks
- [ ] 02.1 Confirm a clean working tree and push a backup ref before starting
- [ ] 02.2 `git mv` the four entries to the repository root
- [ ] 02.3 Remove the emptied wrapper directory
- [ ] 02.4 Re-run all five validators from the new root
- [ ] 02.5 Verify git history follows for a sample of moved files
- [ ] 02.6 Obtain E2 independent review

## Ready Gate
Use `governance/core/TASK_READY_GATE_STANDARD.md`.

- [ ] REM-T01 DONE
- [ ] Completion Gate frozen in S002
- [ ] Backup ref pushed to `origin`
- [ ] Owner has confirmed the move (Blast Radius 5/5)

## Completion Gate
Use `governance/core/TASK_COMPLETION_GATE_STANDARD.md` and `governance/core/EVIDENCE_STANDARD.md`.

Status of this gate:
PRELIMINARY — NOT FROZEN. Freeze in S002.

### Structural

#### CHECK-T02-01
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
`ls -A` at the repository root shows exactly `.git`, `CLAUDE.md`, `PROJECT/`,
`docs/`, `governance/` (plus any files added by REM-T06).

#### CHECK-T02-02
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
`validate_structure.py` PASS when run from the new root.

### Preservation

#### CHECK-T02-03
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
`git diff --stat HEAD~1 -M` shows renames only, with zero content lines added
or removed.

#### CHECK-T02-04
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
`git log --follow` returns pre-move history for at least three sampled moved
files, including `CLAUDE.md`.

### Independent Review

#### CHECK-T02-05
Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E2

Evidence:
...

Executed By:
...

Timestamp:
...

Requirement:
An independent reviewer session confirms no semantic edit occurred. Per
`governance/core/EVIDENCE_STANDARD.md`, Risk 3 combined with Blast Radius 5
touching the agent read path warrants E2. Use the Solo Independent Review
Procedure (`governance/reference/START_HERE_USAGE_GUIDE_V3_2.md` PHẦN 20) and store the artifact in
`docs/reviews/` using `governance/templates/E2_INDEPENDENT_REVIEW_TEMPLATE.md`.

If no E2 path exists, record the limitation — do not mark this check PASS.

## Exit Criteria
- [ ] 100% REQUIRED checks PASS
- [ ] No critical unresolved defect
- [ ] Required evidence level satisfied, including E2 on CHECK-T02-05
- [ ] Project progress updated
- [ ] Session handoff written

## Escalation Triggers
- Any content diff appears in the move → stop, revert, escalate. The move must
  be path-only.
- `git log --follow` loses history → stop and re-plan the move strategy.

## Changed Files Registry

Created:
- ...

Modified:
- ...

Deleted:
- ...

Migration Impact:
- All 73 tracked file paths change. Any external reference to a path under
  `AI_ENGINEERING_CONSTITUTION_TEMPLATE_V3_2_FINAL_COMPACT/` breaks. Paths
  *relative to* `CLAUDE.md` are unchanged, so no in-repository reference needs
  rewriting for this reason.

## Notes
Validators resolve ROOT from `Path(__file__).resolve().parents[3]`. That
expression stays correct after the move, because the script's depth below the
package root is unchanged. Confirm this in 02.4 rather than assuming it.
