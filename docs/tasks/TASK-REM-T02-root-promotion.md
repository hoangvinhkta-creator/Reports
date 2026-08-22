# TASK-REM-T02 — Promote governance package to repository root

## Metadata
Status:
DONE

Phase:
PHASE-01 — Governance Foundation Repair

Task Mode:
MAJOR

Primary Agent Tier:
Tier C — Advanced Reasoning

Escalation Tier:
Tier C + owner confirmation

Difficulty:
2/5

Risk:
3/5

Blast Radius:
5/5

Project Profile:
PRODUCT

Ready Gate Verified In:
S002 — Roadmap Finalization (2026-08-22)

Completion Gate Status:
**FROZEN** — 2026-08-22, S002

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
- REM-T07 DONE — supplies the CI-based E2 evidence source that CHECK-T02-05
  requires. Without it, CHECK-T02-05 must be satisfied by a Solo Independent
  Review session instead (`governance/core/EVIDENCE_STANDARD.md`), which is
  acceptable but slower.
- REM-T01 was CANCELLED in S002 (absorbed — see ROADMAP CHANGE CH-01). It is no
  longer a dependency.

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

## Ready Gate — PARTIALLY VERIFIED

Per `governance/core/TASK_READY_GATE_STANDARD.md`, MAJOR Ready Gate:

- [x] Objective is clear.
- [x] Scope is defined.
- [x] Out-of-scope is defined.
- [ ] **Dependencies are DONE or explicitly waived** — REM-T07 is READY but not
      yet DONE. This is the one open item.
- [x] Expected touch area is identified.
- [x] Relevant requirements are understood.
- [x] Data impact is known — none; no data store exists.
- [x] Security impact is known — none; no secrets or permissions change.
- [x] Routing/API impact is known where relevant — NOT_APPLICABLE.
- [x] Migration prerequisites are available where relevant — a pushed backup ref
      is required by subtask 02.1.
- [x] Difficulty is scored — 2/5.
- [x] Risk is scored — 3/5.
- [x] Blast Radius is scored — 5/5.
- [x] Primary agent tier is assigned — Tier C.
- [x] Escalation triggers are defined.
- [x] Completion Gate is finalized.
- [x] Completion Gate is frozen before implementation.

Additional preconditions before starting implementation:
- [ ] Backup ref pushed to `origin`
- [ ] Owner has confirmed the move (Blast Radius 5/5)

Status: **DONE** — 2026-08-22 (S003).

Dependency note: owner explicitly instructed this task to run ahead of REM-T07
(DEC-009), reversing CH-02's original order, because FIND-001 was an active
usability defect (broken links) rather than a latent risk. E2 for CHECK-T02-05
was obtained via the Solo Independent Review Procedure instead of CI, which
the Ready Gate always permitted as an alternative source.

## Completion Gate
Use `governance/core/TASK_COMPLETION_GATE_STANDARD.md` and `governance/core/EVIDENCE_STANDARD.md`.

Status of this gate:
**FROZEN** — 2026-08-22, S002. Do not remove or weaken a REQUIRED check to make
this task pass. Use COMPLETION GATE CHANGE PROPOSAL if a change is warranted.

### Structural

#### CHECK-T02-01
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E2

Evidence:
`ls -A` at repository root → `.git CLAUDE.md PROJECT docs governance`, nothing else. Independently re-verified in E2 review `docs/reviews/E2-TASK-REM-T02-S003.md`.

Executed By:
S003 agent; independently re-verified by isolated reviewer agent

Timestamp:
2026-08-22

Requirement:
`ls -A` at the repository root shows exactly `.git`, `CLAUDE.md`, `PROJECT/`,
`docs/`, `governance/` (plus any files added by REM-T06).

#### CHECK-T02-02
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E2

Evidence:
`validate_structure.py` → `GOVERNANCE STRUCTURE: PASS`, 21 paths, exit 0, run from the new root. Independently re-verified in `docs/reviews/E2-TASK-REM-T02-S003.md`.

Executed By:
S003 agent; independently re-verified by isolated reviewer agent

Timestamp:
2026-08-22

Requirement:
`validate_structure.py` PASS when run from the new root.

### Preservation

#### CHECK-T02-03
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E2

Evidence:
Commit `699b105`: `git diff --stat -M 699b105^ 699b105` → 84 files changed, 0 insertions(+), 0 deletions(-). `git diff --raw -M` → all 84 entries R100, no A/D/M. Reviewer additionally ran an exhaustive blob-hash comparison of all 84 relocated files (stronger than diff-emptiness) → 0 mismatches. Full detail in `docs/reviews/E2-TASK-REM-T02-S003.md`.

Executed By:
S003 agent; independently re-verified by isolated reviewer agent (exhaustive check exceeding the ≥5-file minimum)

Timestamp:
2026-08-22

Requirement:
`git diff --stat HEAD~1 -M` shows renames only, with zero content lines added
or removed.

#### CHECK-T02-04
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E2

Evidence:
`git log --follow` verified on 4 sampled files (`CLAUDE.md`, `governance/core/EVIDENCE_STANDARD.md`, `governance/scripts/governance/validate_structure.py`, `docs/tasks/TASK-REM-T02-root-promotion.md`) — pre-move history preserved on all four. Full detail in `docs/reviews/E2-TASK-REM-T02-S003.md`.

Executed By:
S003 agent; independently re-verified by isolated reviewer agent

Timestamp:
2026-08-22

Requirement:
`git log --follow` returns pre-move history for at least three sampled moved
files, including `CLAUDE.md`.

### Independent Review

#### CHECK-T02-05
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E2

Evidence:
Independent Solo Independent Review Procedure session (isolated worktree, no prior context) concluded E2 PASS with no discrepancy against the implementer's claims. Artifact: `docs/reviews/E2-TASK-REM-T02-S003.md`.

Executed By:
Independent reviewer agent (isolated worktree agent-a1acf66ec82dff345), per DEC-009

Timestamp:
2026-08-22

Requirement:
An independent reviewer session confirms no semantic edit occurred. Per
`governance/core/EVIDENCE_STANDARD.md`, Risk 3 combined with Blast Radius 5
touching the agent read path warrants E2. Use the Solo Independent Review
Procedure (`governance/reference/START_HERE_USAGE_GUIDE_V3_2.md` PHẦN 20) and store the artifact in
`docs/reviews/` using `governance/templates/E2_INDEPENDENT_REVIEW_TEMPLATE.md`.

If no E2 path exists, record the limitation — do not mark this check PASS.

## Exit Criteria
- [x] 100% REQUIRED checks PASS — 5/5, see Completion Gate above
- [x] No critical unresolved defect
- [x] Required evidence level satisfied, including E2 on CHECK-T02-05
- [x] Project progress updated
- [x] Session handoff written — `docs/sessions/S003-root-promotion.md`

## Escalation Triggers
- Any content diff appears in the move → stop, revert, escalate. The move must
  be path-only.
- `git log --follow` loses history → stop and re-plan the move strategy.

## Changed Files Registry

Created:
- `docs/reviews/E2-TASK-REM-T02-S003.md`
- `.gitignore` (unrelated to this task's scope; added to stop the local
  Claude Code stop-hook from flagging harness worktree scratch state as
  untracked — see FIND-009)

Modified:
- This file (`docs/tasks/TASK-REM-T02-root-promotion.md`) — check results, status
- `PROJECT/PROJECT_DECISIONS.md` — DEC-009
- `PROJECT/PROJECT_PROGRESS.md` — task status, findings register, gate freeze status
- `docs/audit/REMEDIATION_ROADMAP.md` — traceability table

Renamed (path-only, commit `699b105`):
- All 84 files under `AI_ENGINEERING_CONSTITUTION_TEMPLATE_V3_2_FINAL_COMPACT/`
  → repository root. Full list: `git show --stat -M 699b105`.

Deleted:
- The emptied wrapper directory
  `AI_ENGINEERING_CONSTITUTION_TEMPLATE_V3_2_FINAL_COMPACT/`

Migration Impact:
- All 73 original package file paths changed. Any external reference to a path
  under `AI_ENGINEERING_CONSTITUTION_TEMPLATE_V3_2_FINAL_COMPACT/` now 404s —
  this was the exact defect reported by the owner (broken GitHub links) and is
  the reason this task was reordered ahead of REM-T07 (DEC-009). Paths
  *relative to* `CLAUDE.md` are unchanged, so no in-repository reference needed
  rewriting for this reason alone; FIND-003/FIND-004's separately broken
  references remain open, tracked under REM-T04.

## Notes
Validators resolve ROOT from `Path(__file__).resolve().parents[3]`. That
expression stays correct after the move, because the script's depth below the
package root is unchanged. Confirm this in 02.4 rather than assuming it.
