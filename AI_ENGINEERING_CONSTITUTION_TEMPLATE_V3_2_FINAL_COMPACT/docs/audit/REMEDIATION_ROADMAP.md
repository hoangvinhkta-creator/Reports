# Remediation Roadmap — from S001 Discovery

Project:
`hoangvinhkta-creator/Reports`

Produced by:
S001 — Discovery & Baseline (2026-08-22)

Source findings:
`docs/audit/S001_AUDIT_FINDINGS.md`

Source baseline:
`docs/audit/S001_DISCOVERY_BASELINE.md`

Status of this roadmap:
PROPOSED — not yet finalized.

Per `governance/core/00_SESSION_ORCHESTRATION.md` ("Roadmap Finalization") and
`governance/reference/START_HERE_USAGE_GUIDE_V3_2.md` PHẦN 7, a remediation roadmap produced during
AUDIT becomes executable only after S002 confirms the profile transition,
freezes Completion Gates and passes Ready Gates. **No task below is READY.**

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
| LOW | P3 | Phase 3 or deferred with recorded justification |
| INFO | — | No task |

## Phase Overview

| Phase | Name | Tasks | Findings Closed | Gate |
|---|---|---|---|---|
| PHASE-01 | Governance Foundation Repair | REM-T01, REM-T02, REM-T03, REM-T04 | 001, 002, 003, 004, 007 | Phase Gate 01 |
| PHASE-02 | Documentation & Evidence Truth-Up | REM-T05 | 005, 006, 011, 012 | Phase Gate 02 |
| PHASE-03 | Repository Hygiene & Enforcement | REM-T06, REM-T07 | 008, 009 | Phase Gate 03 |

FIND-010 is INFO and closes with no task.

## Dependency Graph

```text
REM-T01 (project state init)
    │
    ├──> REM-T02 (promote package to repo root)
    │        │
    │        ├──> REM-T03 (deployment-root + reference validators)
    │        │        │
    │        ├──> REM-T04 (repair canonical path references)
    │        │        │
    │        │        └──> REM-T05 (documentation & evidence truth-up)
    │        │
    │        └──> REM-T06 (root README / .gitignore)
    │
    └──> REM-T07 (CI enforcement)   [DEFERRED — needs profile decision]
```

Parallel-safe: REM-T03 and REM-T04 may run in parallel after REM-T02, since
REM-T03 touches only `governance/scripts/`, and REM-T04 touches only `.md`
prose. REM-T05 requires both.

---

# PHASE-01 — Governance Foundation Repair

Objective: make the governance system actually loadable and actually
verifiable in this repository.

## REM-T01 — Initialize project state (complete S000)

- [ ] REM-T01 complete

Closes:
FIND-002 (HIGH)

Task Mode:
MAJOR

Difficulty: 2/5 · Risk: 2/5 · Blast Radius: 2/5

Primary Agent Tier: standard · Escalation Tier: senior

Scope:
`PROJECT/PROJECT_PROFILE.md`, `PROJECT/PROJECT_PROGRESS.md`,
`PROJECT/PROJECT_DECISIONS.md`

Out of scope:
Any file under `governance/`. Any application code.

Subtasks:
- [ ] REM-T01.1 Confirm or revise the post-audit profile (AUDIT → PRODUCT or SOLO_LITE)
- [ ] REM-T01.2 Record mandatory / conditional / not-applicable rule groups with justification
- [ ] REM-T01.3 Complete phase and task decomposition in `PROJECT/PROJECT_PROGRESS.md`
- [ ] REM-T01.4 Record preliminary Completion Gates for Phase-01 tasks
- [ ] REM-T01.5 Re-run `validate_project_state.py`

Preliminary Completion Gate (NOT FROZEN):
- CHECK-T01-01 REQUIRED — `validate_project_state.py` exits 0 — Evidence Level E1
- CHECK-T01-02 REQUIRED — no `...` placeholder remains in `PROJECT/PROJECT_PROFILE.md` — Evidence Level E1
- CHECK-T01-03 REQUIRED — `PROJECT/PROJECT_PROGRESS.md` names a Current Task and a Next Recommended Task — Evidence Level E1

Task file:
`docs/tasks/TASK-REM-T01-project-state-init.md`

## REM-T02 — Promote governance package to repository root

- [ ] REM-T02 complete

Closes:
FIND-001 (HIGH)

Task Mode:
MAJOR

Difficulty: 2/5 · Risk: 3/5 · **Blast Radius: 5/5**

Primary Agent Tier: senior · Escalation Tier: senior + human confirmation

Scope:
`git mv` of `CLAUDE.md`, `PROJECT/`, `docs/`, `governance/` from
`AI_ENGINEERING_CONSTITUTION_TEMPLATE_V3_2_FINAL_COMPACT/` to the repository
root; removal of the emptied wrapper directory.

Out of scope:
**Any content edit whatsoever.** This is a path-only move, per the
content-preservation rule in `governance/README.md`. Reference repairs belong
to REM-T04, not here.

Subtasks:
- [ ] REM-T02.1 Confirm a clean working tree and a pushed backup ref
- [ ] REM-T02.2 `git mv` the four entries to repository root
- [ ] REM-T02.3 Remove the emptied wrapper directory
- [ ] REM-T02.4 Re-run all five validators from the new root
- [ ] REM-T02.5 Verify git history follows for a sample of moved files

Preliminary Completion Gate (NOT FROZEN):
- CHECK-T02-01 REQUIRED — `ls -A` at repo root shows exactly `.git`, `CLAUDE.md`, `PROJECT/`, `docs/`, `governance/` — Evidence Level E1
- CHECK-T02-02 REQUIRED — `validate_structure.py` PASS from new root — Evidence Level E1
- CHECK-T02-03 REQUIRED — `git diff --stat HEAD~1 -M` shows renames only, zero content lines changed — Evidence Level E1
- CHECK-T02-04 REQUIRED — `git log --follow` returns pre-move history for a sample moved file — Evidence Level E1
- CHECK-T02-05 REQUIRED — independent reviewer confirms no semantic edit — Evidence Level **E2**

Why E2: Risk 3 with Blast Radius 5 touching the agent read path. Per
`governance/core/EVIDENCE_STANDARD.md`, security/data-critical and high-blast
work should seek E2. Use the Solo Independent Review Procedure
(`governance/reference/START_HERE_USAGE_GUIDE_V3_2.md` PHẦN 20) and store the result in
`docs/reviews/`.

Task file:
`docs/tasks/TASK-REM-T02-root-promotion.md`

## REM-T03 — Add deployment-root and reference-integrity validators

- [ ] REM-T03 complete

Closes:
FIND-007 (MEDIUM); enables machine verification for FIND-005 and FIND-011

Task Mode:
MAJOR

Difficulty: 3/5 · Risk: 2/5 · Blast Radius: 2/5

Primary Agent Tier: standard · Escalation Tier: senior

Scope:
`governance/scripts/governance/` — extend `validate_structure.py` with a
deployment-root assertion, and add a new reference-integrity validator.

Out of scope:
Governance rule text. CI wiring (that is REM-T07).

Subtasks:
- [ ] REM-T03.1 Add git-root discovery and assert it equals the resolved `ROOT`
- [ ] REM-T03.2 Report NOT_APPLICABLE (not PASS) when no git root is found
- [ ] REM-T03.3 Add `validate_reference_integrity.py` resolving backtick-quoted `.md`/`.py`/`.svg` references
- [ ] REM-T03.4 Exclude `governance/reference/history/` and document the exclusion
- [ ] REM-T03.5 Build a nested-layout regression fixture that must FAIL
- [ ] REM-T03.6 Update `governance/scripts/governance/README.md` (overlaps REM-T05 — coordinate)

Preliminary Completion Gate (NOT FROZEN):
- CHECK-T03-01 REQUIRED — nested fixture produces a non-zero exit with an explicit message — Evidence Level E1
- CHECK-T03-02 REQUIRED — corrected root layout produces exit 0 — Evidence Level E1
- CHECK-T03-03 REQUIRED — reference validator reproduces the three S001 findings on the pre-REM-T04 tree — Evidence Level E1
- CHECK-T03-04 REQUIRED — reference validator exits 0 on the post-REM-T04 tree — Evidence Level E1

Task file:
`docs/tasks/TASK-REM-T03-validator-hardening.md`

## REM-T04 — Repair broken canonical path references

- [ ] REM-T04 complete

Closes:
FIND-003 (MEDIUM), FIND-004 (MEDIUM)

Task Mode:
MICRO — eligible: Difficulty 1, Risk 2, Blast Radius 2, no architecture,
auth, schema or destructive change. Promote to MAJOR if the repair turns out
to require more than the three line edits below.

Difficulty: 1/5 · Risk: 2/5 · Blast Radius: 2/5

Scope (exactly three lines):
- [ ] `CLAUDE.md:215` — `OPTIONAL_ENFORCEMENT_LAYER.md` → `governance/reference/OPTIONAL_ENFORCEMENT_LAYER.md`
- [ ] `governance/core/PROJECT_PROFILE_STANDARD.md:77` — same substitution
- [ ] `CLAUDE.md:27` — `templates/` → `governance/templates/`

Out of scope:
`governance/reference/history/` (frozen archive — see FIND-011).
Any rewording beyond the path token.

Checklist reference:
`governance/templates/MICRO_TASK_CHECKLIST.md`

Preliminary Completion Gate (NOT FROZEN):
- CHECK-T04-01 REQUIRED — reference-integrity scan reports 0 broken references outside `history/` — Evidence Level E1
- CHECK-T04-02 REQUIRED — `git diff` shows only path-token changes on three lines — Evidence Level E1

Note:
Line numbers are as of baseline commit `0394267`. Re-locate by content, not by
line number, if REM-T02 or any other edit lands first.

## Phase Gate 01

- [ ] All four Phase-01 tasks DONE with REQUIRED checks PASS
- [ ] `validate_structure.py` PASS from repository root
- [ ] `validate_project_state.py` PASS
- [ ] `validate_task_completion.py` PASS
- [ ] `validate_evidence.py` PASS
- [ ] Reference-integrity validator PASS
- [ ] E2 review recorded in `docs/reviews/` for REM-T02
- [ ] No open regression item introduced by Phase-01

Run per `governance/core/PHASE_RELEASE_GATE_STANDARD.md`.

---

# PHASE-02 — Documentation & Evidence Truth-Up

Objective: make every shipped claim re-derivable from the repository.

## REM-T05 — Correct documentation and validation artifacts

- [ ] REM-T05 complete

Closes:
FIND-005 (MEDIUM), FIND-006 (MEDIUM), FIND-011 (LOW), FIND-012 (LOW)

Task Mode:
MAJOR

Difficulty: 2/5 · Risk: 2/5 · Blast Radius: 3/5

Primary Agent Tier: standard · Escalation Tier: senior

Depends on:
REM-T02, REM-T03, REM-T04 — the claims can only be re-asserted once they are
true and machine-checkable.

Subtasks:
- [ ] REM-T05.1 Re-run the reference-integrity validator and replace the bare assertion in `governance/reference/COMPACT_STRUCTURE_VALIDATION.md` with the actual command and output
- [ ] REM-T05.2 State the `history/` exclusion explicitly in that report
- [ ] REM-T05.3 Reconcile `governance/reference/START_HERE_USAGE_GUIDE_V3_2.md` PHẦN 1/2/3 to the compact layout (lines 83, 85, 144, 146, 179 at baseline)
- [ ] REM-T05.4 Make the PHẦN 2 verification block match `validate_structure.py`'s required paths
- [ ] REM-T05.5 Document all five validators in `governance/scripts/governance/README.md`, including `validate_refactor_preservation.py`'s positional argument
- [ ] REM-T05.6 Leave `governance/reference/history/` unmodified

Preliminary Completion Gate (NOT FROZEN):
- CHECK-T05-01 REQUIRED — every validator result quoted in `governance/reference/COMPACT_STRUCTURE_VALIDATION.md` reproduces byte-for-byte when re-run — Evidence Level E1
- CHECK-T05-02 REQUIRED — no `templates/` or `scripts/` root-level entry remains in the START_HERE guide — Evidence Level E1
- CHECK-T05-03 REQUIRED — validator README lists exactly the five scripts present — Evidence Level E1
- CHECK-T05-04 REQUIRED — `git diff` confirms `governance/reference/history/` untouched — Evidence Level E1
- CHECK-T05-05 RECOMMENDED — independent reviewer re-derives the report's claims — Evidence Level E2

Task file:
Create in S002+ from `governance/templates/TASK_DEFINITION_TEMPLATE.md`.

## Phase Gate 02

- [ ] REM-T05 DONE with REQUIRED checks PASS
- [ ] Every claim in `governance/reference/` re-derivable from repository state
- [ ] Documentation set internally consistent

---

# PHASE-03 — Repository Hygiene & Enforcement

Objective: close the remaining LOW findings and decide the enforcement posture.

## REM-T06 — Repository root hygiene

- [ ] REM-T06 complete

Closes:
FIND-009 (LOW)

Task Mode:
MICRO

Difficulty: 1/5 · Risk: 1/5 · Blast Radius: 1/5

Subtasks:
- [ ] REM-T06.1 Add root `README.md` pointing to `CLAUDE.md` as the entry point
- [ ] REM-T06.2 Add `.gitignore` covering `__pycache__/` and `*.pyc`
- [ ] REM-T06.3 Raise the `LICENSE` question with the owner — do not choose one unilaterally

Preliminary Completion Gate (NOT FROZEN):
- CHECK-T06-01 REQUIRED — `README.md` and `.gitignore` present at repository root — Evidence Level E1
- CHECK-T06-02 REQUIRED — `git status` clean after a full validator run — Evidence Level E1

## REM-T07 — CI enforcement decision

- [ ] REM-T07 complete (or formally deferred)

Closes:
FIND-008 (LOW)

Task Mode:
MAJOR if implemented; MICRO if formally recorded as NOT_APPLICABLE

Status:
**DEFERRED** — blocked on the post-audit profile decision in REM-T01.1.

Decision rule (from `governance/core/PROJECT_PROFILE_STANDARD.md`):
- TEAM_PRODUCTION → implement CI running all five validators on push and PR
- PRODUCT → implement CI if practical
- SOLO_LITE or AUDIT → record CI as NOT_APPLICABLE **with written justification**
  in `PROJECT/PROJECT_PROFILE.md`; the standard permits this, silence does not

Subtasks:
- [ ] REM-T07.1 Read the finalized profile
- [ ] REM-T07.2 Apply the decision rule above
- [ ] REM-T07.3 Either add `.github/workflows/governance.yml` or record the justification
- [ ] REM-T07.4 If CI is added, capture a green run as the project's first E2 evidence source

Preliminary Completion Gate (NOT FROZEN):
- CHECK-T07-01 REQUIRED — either a green CI run executing all five validators (E2), or a recorded NOT_APPLICABLE justification in the profile (E0 acceptable for a profile decision)

## Phase Gate 03

- [ ] REM-T06 DONE
- [ ] REM-T07 DONE or formally DEFERRED with recorded justification
- [ ] All 12 S001 findings RESOLVED, ACCEPTED_RISK or DEFERRED — none left OPEN without a state

---

# Finding → Task Traceability

| Finding | Severity | Task | Phase | Status |
|---|---|---|---|---|
| FIND-001 | HIGH | REM-T02 | 01 | OPEN |
| FIND-002 | HIGH | REM-T01 | 01 | OPEN (partially mitigated by DEC-001) |
| FIND-003 | MEDIUM | REM-T04 | 01 | OPEN |
| FIND-004 | MEDIUM | REM-T04 | 01 | OPEN |
| FIND-005 | MEDIUM | REM-T05 (+REM-T03) | 02 | OPEN |
| FIND-006 | MEDIUM | REM-T05 | 02 | OPEN |
| FIND-007 | MEDIUM | REM-T03 | 01 | OPEN |
| FIND-008 | LOW | REM-T07 | 03 | OPEN — DEFERRED |
| FIND-009 | LOW | REM-T06 | 03 | OPEN |
| FIND-010 | INFO | — | — | No action |
| FIND-011 | LOW | REM-T03 + REM-T05 | 02 | OPEN |
| FIND-012 | LOW | REM-T05 | 02 | OPEN |

Every finding maps to a task or is explicitly marked no-action. No finding is
silently dropped.

# Roadmap Change Rule

Do not restructure this roadmap silently. Use the ROADMAP CHANGE PROPOSAL
format in `governance/core/00_SESSION_ORCHESTRATION.md` and record the outcome
in `PROJECT/PROJECT_DECISIONS.md`.
