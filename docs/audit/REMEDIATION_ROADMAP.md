# Remediation Roadmap — from S001 Discovery

Project:
`hoangvinhkta-creator/Reports`

Produced by:
S001 — Discovery & Baseline (2026-08-22)

Finalized by:
S002 — Roadmap Finalization (2026-08-22)

Source findings:
`docs/audit/S001_AUDIT_FINDINGS.md`

Source baseline:
`docs/audit/S001_DISCOVERY_BASELINE.md`

Profile:
PRODUCT (transitioned from AUDIT in S002 — DEC-005)

Status of this roadmap:
**FINALIZED for PHASE-01.** PHASE-02 and PHASE-03 gates remain PRELIMINARY, per
`governance/core/00_SESSION_ORCHESTRATION.md`: "Do not freeze distant task
details before discovery is sufficient."

## Revision History

| Rev | Session | Change |
|---|---|---|
| 1 | S001 | Initial roadmap — 3 phases, 7 tasks, preliminary gates |
| 2 | S002 | Profile → PRODUCT; CH-01 and CH-02 applied; PHASE-01 gates frozen; agent tiers mapped to A–D |
| 3 | S003 | CH-03 applied — REM-T02 executed ahead of REM-T07; REM-T02 DONE; FIND-001 RESOLVED; REM-T03/REM-T04 unblocked |

### ROADMAP CHANGE CH-01 — REM-T01 cancelled (absorbed)

Reason:
The S000 procedure REM-T01 existed to complete was fully executed across S001
(bootstrap, DEC-001) and S002 (profile transition, tier mapping, gate freeze).
No step of the canonical 15-step S000 procedure remains. See the step-by-step
table in `docs/tasks/TASK-REM-T01-project-state-init.md`.

Affected tasks:
REM-T01 → CANCELLED. It was a dependency of every other task; that dependency
edge is removed.

Dependency impact:
PHASE-01 loses its head node. REM-T07 becomes the entry point.

Risk:
Low. FIND-002's stated Verification Required is met with E1 evidence. The risk
is that a future session assumes S000 was skipped; mitigated by retaining the
task file with a full Cancellation Record rather than deleting it.

Recommended change:
Applied. FIND-002 → RESOLVED (E1, E2 not obtained).

### ROADMAP CHANGE CH-02 — REM-T07 un-deferred and moved to PHASE-01

Reason:
S001 deferred REM-T07 pending the profile decision. PRODUCT resolves it: CI is
not mandatory at this profile but is judged practical, and it is the only
realistic E2 evidence source for a single-owner repository. REM-T02's
CHECK-T02-05 requires E2. Sequencing CI first gives that check a source and
closes RSK-004 before the highest-blast-radius task runs.

Affected tasks:
REM-T07 moves PHASE-03 → PHASE-01, position 1. REM-T02 gains a dependency on it.

Dependency impact:
REM-T07 → REM-T02 → (REM-T03 ∥ REM-T04). PHASE-03 now contains REM-T06 only.

Risk:
REM-T07 creates a file (`.github/workflows/governance.yml`) that hard-codes
paths REM-T02 will change — which would force REM-T02 to edit content and break
its path-only Scope Lock. Mitigated by a Critical Design Constraint on REM-T07:
the workflow must discover validators at runtime rather than hard-code paths,
verified by CHECK-T07-04.

Recommended change:
Applied.

### ROADMAP CHANGE CH-03 — REM-T02 executed ahead of REM-T07

Reason:
CH-02 sequenced REM-T07 (CI) before REM-T02 (root promotion) so REM-T02 would
have a CI-based E2 source. Between S002 and this task's execution, the owner
reported — with a screenshot — that GitHub links into `docs/tasks/`,
`docs/audit/`, `PROJECT/`, etc. returned 404, because those paths existed only
under the nested `AI_ENGINEERING_CONSTITUTION_TEMPLATE_V3_2_FINAL_COMPACT/`
directory, not at the repository root. This is exactly FIND-001, now manifest
as an active usability defect rather than a documented risk. Asked directly
whether to hold the frozen order or fix it immediately, the owner chose to fix
it immediately.

Affected tasks:
REM-T02 executed as the first task of PHASE-01, ahead of REM-T07. REM-T07's
Ready Gate and Scope Lock are unaffected; it remains READY.

Dependency impact:
REM-T02 → (REM-T07 ∥ REM-T03 ∥ REM-T04). All three are now independently
runnable, since they only depended on REM-T02, not on each other or on
REM-T07.

Risk:
CHECK-T02-05 requires E2 evidence. With no CI yet available, E2 was obtained
via the Solo Independent Review Procedure instead
(`docs/reviews/E2-TASK-REM-T02-S003.md`) — a path the frozen gate always
permitted as an alternative to CI. No REQUIRED check was weakened; the same
5-check gate was executed, only the evidence *source* for one check differed
from the originally anticipated one.

Recommended change:
Applied. See DEC-009 in `PROJECT/PROJECT_DECISIONS.md`.

## How To Use This File

This file is the **detailed** remediation plan: task definitions, dependencies,
gates, severity mapping.

`PROJECT/PROJECT_PROGRESS.md` is the **canonical live checklist**. It is what
every session reads first and what gets ticked as work completes.

Rule: tick a box **here** and in `PROJECT/PROJECT_PROGRESS.md` together, in the
same session, with evidence recorded in the task file under `docs/tasks/`.
If the two files disagree, `PROJECT/PROJECT_PROGRESS.md` wins and this file is
corrected to match.

## Severity → Priority Mapping

| Severity | Priority | Target |
|---|---|---|
| CRITICAL | P0 | Immediate; blocks all other work |
| HIGH | P1 | Phase 1 |
| MEDIUM | P2 | Phase 1–2 depending on dependency |
| LOW | P3 | Phase 3, or earlier when it unblocks a higher-priority task |
| INFO | — | No task |

REM-T07 closes a LOW finding but sits in PHASE-01, because its value here is
not the finding it closes — it is the E2 path it creates for REM-T02.

## Phase Overview

| Phase | Name | Tasks | Findings Closed | Gate |
|---|---|---|---|---|
| PHASE-01 | Governance Foundation Repair | REM-T07, REM-T02, REM-T03, REM-T04 | 001, 003, 004, 007, 008 | Phase Gate 01 |
| PHASE-02 | Documentation & Evidence Truth-Up | REM-T05 | 005, 006, 011, 012 | Phase Gate 02 |
| PHASE-03 | Repository Hygiene | REM-T06 | 009 | Phase Gate 03 |

FIND-002 was resolved in S002 (CH-01). FIND-010 is INFO and closes with no task.

## Dependency Graph

As executed (post-S003, per CH-03 — REM-T02 ran ahead of REM-T07):

```text
REM-T02 (promote package to repo root)   [DONE — Blast Radius 5/5]
    │
    ├──> REM-T07 (CI enforcement — creates the durable E2 path)   [READY]
    │
    ├──> REM-T03 (deployment-root + reference validators)   [READY]
    │        │
    ├──> REM-T04 (repair canonical path references)   [READY]
    │        │
    │        └──> REM-T05 (documentation & evidence truth-up)
    │
    └──> REM-T06 (root README / .gitignore)
```

REM-T07, REM-T03 and REM-T04 depended only on REM-T02, not on each other — so
all three are independently runnable now that REM-T02 is DONE.
REM-T03 touches only `governance/scripts/`; REM-T04 touches only `.md` prose;
REM-T07 touches only `.github/workflows/`. Any one, or all three in parallel.

## Agent Tier Assignment

Per `governance/core/AGENT_CAPABILITY_MATRIX.md`. See DEC-006.

| Task | Difficulty | Risk | Blast | Primary | Escalation |
|---|---|---|---|---|---|
| REM-T07 | 2 | 2 | 2 | Tier B | Tier C |
| REM-T02 | 2 | 3 | **5** | **Tier C** | Tier C + owner |
| REM-T03 | 3 | 2 | 2 | Tier B | Tier C |
| REM-T04 | 1 | 2 | 2 | Tier A | Tier B |
| REM-T05 | 2 | 2 | 3 | Tier B | Tier C |
| REM-T06 | 1 | 1 | 1 | Tier A | Tier B |

Tier D — Design / Creative is NOT_APPLICABLE to this project.

---

# PHASE-01 — Governance Foundation Repair

Objective: make the governance system actually loadable, actually verifiable,
and backed by independent evidence.

Gate status: **FROZEN** for all four tasks as of 2026-08-22 (S002).

## REM-T07 — CI enforcement layer  ·  READY

- [ ] REM-T07 complete

Closes:
FIND-008 (LOW) · Resolves RSK-004

Status:
**READY** — Ready Gate verified in S002; no open dependency.

Task Mode:
MAJOR · Tier B / escalate Tier C

Difficulty: 2/5 · Risk: 2/5 · Blast Radius: 2/5

Scope:
`.github/workflows/governance.yml` at the git repository root. Nothing else.

Critical design constraint:
The workflow must **discover** validator scripts at runtime, not hard-code
their paths — otherwise REM-T02's path-only move would break it and force a
content edit inside a Scope Lock that forbids one.

Frozen Completion Gate — 7 checks (6 REQUIRED, 1 RECOMMENDED):
CHECK-T07-01 … CHECK-T07-07. Full text in
`docs/tasks/TASK-REM-T07-ci-enforcement.md`.

Non-negotiable among them: **CHECK-T07-03** — the workflow must be observed
FAILING on a deliberate breakage. A CI that has never been seen to fail
manufactures false E2 evidence.

Task file:
`docs/tasks/TASK-REM-T07-ci-enforcement.md`

## REM-T02 — Promote governance package to repository root  ·  DONE

- [x] REM-T02 complete — 2026-08-22 (S003)

Closes:
FIND-001 (HIGH) — **RESOLVED**

Status:
**DONE.** Executed ahead of REM-T07 on explicit owner instruction (DEC-009,
ROADMAP CHANGE CH-03 above), because FIND-001 had become an active usability
defect (broken GitHub links into `docs/`, `PROJECT/`, etc.) rather than a
latent risk. E2 for CHECK-T02-05 was obtained via the Solo Independent Review
Procedure instead of CI. Backup ref `backup/pre-root-promotion-s003` was
pushed before the move, per the Ready Gate precondition.

Task Mode:
MAJOR · **Tier C** / escalate Tier C + owner

Difficulty: 2/5 · Risk: 3/5 · **Blast Radius: 5/5**

Scope:
`git mv` of `CLAUDE.md`, `PROJECT/`, `docs/`, `governance/` to the repository
root; removal of the emptied wrapper directory.

Out of scope:
**Any content edit whatsoever.** Path-only move, per the content-preservation
rule in `governance/README.md`. Reference repairs are REM-T04's job.

Frozen Completion Gate — 5/5 REQUIRED checks PASS:
- CHECK-T02-01 — root listing shows the four entries — **PASS, E2**
- CHECK-T02-02 — `validate_structure.py` PASS from new root — **PASS, E2**
- CHECK-T02-03 — `git diff --stat HEAD~1 -M` shows renames only, zero content lines — **PASS, E2** (commit `699b105`: 84 files, 0 insertions, 0 deletions; independently verified at the blob-hash level for all 84 files)
- CHECK-T02-04 — `git log --follow` returns pre-move history for ≥3 sampled files — **PASS, E2** (4 sampled)
- CHECK-T02-05 — independent review confirms no semantic edit — **PASS, E2**

E2 source used: a Solo Independent Review session in an isolated git worktree
with no prior conversation context (`docs/reviews/E2-TASK-REM-T02-S003.md`),
not CI — CI (REM-T07) had not yet run when this task executed.

Task file:
`docs/tasks/TASK-REM-T02-root-promotion.md`

## REM-T03 — Deployment-root and reference-integrity validators

- [ ] REM-T03 complete

Closes:
FIND-007 (MEDIUM); enables machine verification for FIND-005 and FIND-011

Status:
**READY** — REM-T02 is DONE (S003).

Task Mode:
MAJOR · Tier B / escalate Tier C

Difficulty: 3/5 · Risk: 2/5 · Blast Radius: 2/5

Reference resolution rule fixed in S002:
Resolve from the repository root first, then from the referencing file's own
directory. A reference is broken only when neither resolves. This is the rule
S001's manual scan used, which makes CHECK-T03-03 a genuine reproduction test.

Exclusions the validator must implement:
- `governance/reference/history/` — frozen archive (FIND-011)
- `docs/audit/` — immutable audit record; it quotes defect tokens verbatim
- glob patterns and forward references to files a PLANNED task will create

Frozen Completion Gate — 4 REQUIRED checks:
- CHECK-T03-01 — nested fixture FAILs with an explicit message — E1
- CHECK-T03-02 — corrected root layout exits 0 — E1
- CHECK-T03-03 — reproduces exactly the three S001 references on the pre-REM-T04 tree — E1
- CHECK-T03-04 — exits 0 on the post-REM-T04 tree — E1

Task file:
`docs/tasks/TASK-REM-T03-validator-hardening.md`

## REM-T04 — Repair broken canonical path references

- [ ] REM-T04 complete

Closes:
FIND-003 (MEDIUM), FIND-004 (MEDIUM)

Status:
**READY** — REM-T02 is DONE (S003).

Task Mode:
MICRO · Tier A / escalate Tier B

Confirmed MICRO in S002 (DEC-007): Difficulty 1, Risk 2, Blast Radius 2, no
architecture, auth, schema or destructive change. Tracked inline in
`PROJECT/PROJECT_PROGRESS.md` as MICRO-001.

Scope — exactly three lines:
- [ ] `CLAUDE.md:215` — `OPTIONAL_ENFORCEMENT_LAYER.md` → `governance/reference/OPTIONAL_ENFORCEMENT_LAYER.md`
- [ ] `governance/core/PROJECT_PROFILE_STANDARD.md:77` — same substitution
- [ ] `CLAUDE.md:27` — `templates/` → `governance/templates/`

Out of scope:
`governance/reference/history/` (frozen archive — FIND-011). Any rewording
beyond the path token.

Frozen compact Completion Gate — see MICRO-001 in
`PROJECT/PROJECT_PROGRESS.md`; canonical checklist is
`governance/templates/MICRO_TASK_CHECKLIST.md`.

Promotion rule:
If the repair needs more than these three lines, STOP treating it as MICRO and
promote to MAJOR per `governance/core/TASK_MODE_STANDARD.md`.

Note:
Line numbers are as of baseline commit `0394267`. Re-locate by content, not by
line number.

## Phase Gate 01

Per `governance/core/PHASE_RELEASE_GATE_STANDARD.md`.

- [ ] REM-T07, REM-T02, REM-T03, REM-T04 all DONE with REQUIRED checks PASS
- [ ] `validate_structure.py` PASS from the repository root
- [ ] `validate_project_state.py` PASS
- [ ] `validate_task_completion.py` PASS
- [ ] `validate_evidence.py` PASS
- [ ] New reference-integrity validator PASS
- [ ] CI green on the head commit
- [ ] E2 evidence recorded for REM-T02 CHECK-T02-05
- [ ] `CLAUDE.md` is at the repository root and every canonical reference in it resolves
- [ ] No open regression item introduced by PHASE-01

---

# PHASE-02 — Documentation & Evidence Truth-Up

Objective: make every shipped claim re-derivable from the repository.

Gate status: PRELIMINARY — freeze before REM-T05 becomes READY.

## REM-T05 — Correct documentation and validation artifacts

- [ ] REM-T05 complete

Closes:
FIND-005 (MEDIUM), FIND-006 (MEDIUM), FIND-011 (LOW), FIND-012 (LOW)

Task Mode:
MAJOR · Tier B / escalate Tier C

Difficulty: 2/5 · Risk: 2/5 · Blast Radius: 3/5

Depends on:
REM-T02, REM-T03, REM-T04 — the claims can only be re-asserted once they are
true and machine-checkable.

Subtasks:
- [ ] REM-T05.1 Re-run the reference-integrity validator and replace the bare assertion in `governance/reference/COMPACT_STRUCTURE_VALIDATION.md` with the actual command and output
- [ ] REM-T05.2 State the `history/` and `docs/audit/` exclusions explicitly in that report
- [ ] REM-T05.3 Reconcile `governance/reference/START_HERE_USAGE_GUIDE_V3_2.md` PHẦN 1/2/3 to the compact layout (lines 83, 85, 144, 146, 179 at baseline)
- [ ] REM-T05.4 Make the PHẦN 2 verification block match `validate_structure.py`'s required paths
- [ ] REM-T05.5 Document all validators in `governance/scripts/governance/README.md`, including `validate_refactor_preservation.py`'s positional argument
- [ ] REM-T05.6 Leave `governance/reference/history/` unmodified

Preliminary Completion Gate (NOT FROZEN):
- CHECK-T05-01 REQUIRED — every validator result quoted in the report reproduces byte-for-byte when re-run — E1
- CHECK-T05-02 REQUIRED — no `templates/` or `scripts/` root-level entry remains in the START_HERE guide — E1
- CHECK-T05-03 REQUIRED — validator README lists exactly the scripts present — E1
- CHECK-T05-04 REQUIRED — `git diff` confirms `governance/reference/history/` untouched — E1
- CHECK-T05-05 RECOMMENDED — independent reviewer re-derives the report's claims — E2

Task file:
Create from `governance/templates/TASK_DEFINITION_TEMPLATE.md` when PHASE-02 is
finalized.

## Phase Gate 02

- [ ] REM-T05 DONE with REQUIRED checks PASS
- [ ] Every claim in `governance/reference/` re-derivable from repository state
- [ ] Documentation set internally consistent
- [ ] CI green

---

# PHASE-03 — Repository Hygiene

Objective: close the remaining LOW finding.

Gate status: PRELIMINARY — freeze before REM-T06 becomes READY.

## REM-T06 — Repository root hygiene

- [ ] REM-T06 complete

Closes:
FIND-009 (LOW)

Task Mode:
MICRO · Tier A / escalate Tier B

Difficulty: 1/5 · Risk: 1/5 · Blast Radius: 1/5

Depends on:
REM-T02

Subtasks:
- [ ] REM-T06.1 Add root `README.md` pointing to `CLAUDE.md` as the entry point
- [ ] REM-T06.2 Add `.gitignore` covering `__pycache__/` and `*.pyc`
- [ ] REM-T06.3 Raise the `LICENSE` question with the owner — do not choose one unilaterally

Preliminary Completion Gate (NOT FROZEN):
- CHECK-T06-01 REQUIRED — `README.md` and `.gitignore` present at repository root — E1
- CHECK-T06-02 REQUIRED — `git status` clean after a full validator run — E1

## Phase Gate 03

- [ ] REM-T06 DONE
- [ ] GAP-01 (Backup / DR) re-assessed and either closed or formally accepted
- [ ] All S001 findings RESOLVED, ACCEPTED_RISK or DEFERRED — none left OPEN without a state
- [ ] CI green

---

# Finding → Task Traceability

| Finding | Severity | Task | Phase | Status |
|---|---|---|---|---|
| FIND-001 | HIGH | REM-T02 | 01 | **RESOLVED** (S003, E2) |
| FIND-002 | HIGH | — (absorbed, CH-01) | — | **RESOLVED** (S002, E1) |
| FIND-003 | MEDIUM | REM-T04 | 01 | OPEN |
| FIND-004 | MEDIUM | REM-T04 | 01 | OPEN |
| FIND-005 | MEDIUM | REM-T05 (+REM-T03) | 02 | OPEN |
| FIND-006 | MEDIUM | REM-T05 | 02 | OPEN |
| FIND-007 | MEDIUM | REM-T03 | 01 | OPEN |
| FIND-008 | LOW | REM-T07 | 01 | OPEN |
| FIND-009 | LOW | REM-T06 | 03 | OPEN |
| FIND-010 | INFO | — | — | No action |
| FIND-011 | LOW | REM-T03 + REM-T05 | 02 | OPEN |
| FIND-012 | LOW | REM-T05 | 02 | OPEN |

Resolved: 2 / 12. Every remaining finding maps to a task or is explicitly
marked no-action. No finding is silently dropped.

# Open Items Not Tied To A Finding

- **GAP-01** — Backup / DR. `governance/product/16_BACKUP_DISASTER_RECOVERY.md`
  is mandatory at PRODUCT; the GitHub remote is the only copy. Not scheduled
  into PHASE-01; re-assess at Phase Gate 03. Recorded in
  `PROJECT/PROJECT_PROFILE.md`.
- **DORMANT domains** — several PRODUCT-mandatory rule groups have no subject
  because no application code exists. Listed in the Profile Compliance Matrix.
  Re-check when application code lands; do not treat DORMANT as a waiver.

# Roadmap Change Rule

Do not restructure this roadmap silently. Use the ROADMAP CHANGE PROPOSAL
format in `governance/core/00_SESSION_ORCHESTRATION.md`, record the outcome in
`PROJECT/PROJECT_DECISIONS.md`, and add a row to the Revision History above.
