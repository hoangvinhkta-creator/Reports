# TASK-REM-T03 — Deployment-root and reference-integrity validators

## Metadata
Status:
PLANNED

Phase:
PHASE-01 — Governance Foundation Repair

Task Mode:
MAJOR

Primary Agent Tier:
Tier B — Implementation

Escalation Tier:
Tier C — Advanced Reasoning

Difficulty:
3/5

Risk:
2/5

Blast Radius:
2/5

Project Profile:
PRODUCT

Ready Gate Verified In:
S002 — Roadmap Finalization (2026-08-22)

Completion Gate Status:
**FROZEN** — 2026-08-22, S002

Closes Finding:
FIND-007 (MEDIUM); enables machine verification for FIND-005 and FIND-011

## Objective
Make two defect classes machine-detectable that S001 could only find by hand:

1. A governance package deployed somewhere other than the repository root
   (the FIND-001 class).
2. Broken canonical repository-relative references (the FIND-003/FIND-004
   class, which a shipped report wrongly certified as clean — FIND-005).

## Scope
- `governance/scripts/governance/validate_structure.py`
- New `governance/scripts/governance/validate_reference_integrity.py`
- `governance/scripts/governance/README.md` (overlaps REM-T05 — coordinate)
- A regression fixture directory for the nested-layout case

## Out of Scope
- Governance rule text
- CI wiring (REM-T07)
- Repairing the references themselves (REM-T04)

## Dependencies
- REM-T02 DONE (the check encodes the expected root layout)

## Blocks
- REM-T05 (the report can only cite output from a validator that exists)

## Parallel-Safe With
- REM-T04. This task touches only `governance/scripts/`; REM-T04 touches only
  `.md` prose.

## Expected Touch Area

Allowed:
- `governance/scripts/governance/**`
- Test fixtures under a clearly named fixture directory

Do not touch without Scope Expansion:
- `governance/core/**`, `governance/product/**`, `CLAUDE.md`

## Subtasks
- [ ] 03.1 Add git-root discovery (walk upward for `.git`) and assert it equals the resolved `ROOT`
- [ ] 03.2 Report NOT_APPLICABLE — not PASS — when no git root is found
- [ ] 03.3 Add `validate_reference_integrity.py` resolving backtick-quoted `.md` / `.py` / `.svg` references
- [ ] 03.4 Define and document the scan's exclusion and handling rules in the script:
  - exclude `governance/reference/history/` (frozen archive — FIND-011)
  - exclude `docs/audit/` (immutable audit record; it quotes defect tokens such
    as the bare `OPTIONAL_ENFORCEMENT_LAYER.md` verbatim as evidence)
  - skip glob patterns (`PROJECT/*.md`, `docs/tasks/TASK-REM-*.md`) rather than
    reporting them broken
  - skip references to files a PLANNED task will create (forward references),
    or report them at a distinct severity from genuinely broken links
- [ ] 03.5 Build a nested-layout regression fixture that must FAIL
- [ ] 03.6 Update `governance/scripts/governance/README.md` to cover all validators

## Ready Gate — PARTIALLY VERIFIED

Per `governance/core/TASK_READY_GATE_STANDARD.md`, MAJOR Ready Gate:

- [x] Objective is clear.
- [x] Scope is defined.
- [x] Out-of-scope is defined.
- [ ] **Dependencies are DONE or explicitly waived** — REM-T02 is not yet DONE.
      This is the one open item.
- [x] Expected touch area is identified.
- [x] Relevant requirements are understood.
- [x] Data impact is known — none.
- [x] Security impact is known — none; validators are read-only and use only
      the Python standard library.
- [x] Routing/API impact is known where relevant — NOT_APPLICABLE.
- [x] Migration prerequisites are available where relevant — NOT_APPLICABLE.
- [x] Difficulty is scored — 3/5.
- [x] Risk is scored — 2/5.
- [x] Blast Radius is scored — 2/5.
- [x] Primary agent tier is assigned — Tier B.
- [x] Escalation triggers are defined.
- [x] Completion Gate is finalized.
- [x] Completion Gate is frozen before implementation.

Design decision fixed in S002 — the reference resolution rule is: resolve from
the repository root first, then from the referencing file's own directory; a
reference is broken only when neither resolves. This is the rule S001's manual
scan used (CHK-S001-06), so CHECK-T03-03 is a genuine reproduction test.

Status: **PLANNED** — becomes READY when REM-T02 is DONE.

## Completion Gate
Use `governance/core/TASK_COMPLETION_GATE_STANDARD.md` and `governance/core/EVIDENCE_STANDARD.md`.

Status of this gate:
**FROZEN** — 2026-08-22, S002. Do not remove or weaken a REQUIRED check to make
this task pass. Use COMPLETION GATE CHANGE PROPOSAL if a change is warranted.

### Regression

#### CHECK-T03-01
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
A deliberately nested fixture produces a non-zero exit with an explicit message
naming the expected root. This is the check that would have caught FIND-001.

#### CHECK-T03-02
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
The corrected root layout produces exit 0.

### Reference Integrity

#### CHECK-T03-03
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
Run against the pre-REM-T04 tree (e.g. baseline commit `0394267`), the new
validator reproduces exactly the three references S001 found by hand:
`CLAUDE.md` → `OPTIONAL_ENFORCEMENT_LAYER.md`,
`governance/core/PROJECT_PROFILE_STANDARD.md` → `OPTIONAL_ENFORCEMENT_LAYER.md`,
and `CLAUDE.md` → `templates/`. This is the check that proves the validator
works, rather than merely passing.

#### CHECK-T03-04
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
Run against the post-REM-T04 tree, the validator exits 0.

## Exit Criteria
- [ ] 100% REQUIRED checks PASS
- [ ] No critical unresolved defect
- [ ] Required evidence level satisfied
- [ ] `governance/scripts/governance/README.md` updated
- [ ] Project progress updated
- [ ] Session handoff written

## Escalation Triggers
- The reference resolution rule produces false positives on legitimate prose →
  stop and agree the rule before hardening further.
- Git-root discovery proves unreliable in a submodule or worktree layout →
  escalate rather than weakening the check to a warning.

## Changed Files Registry

Created:
- ...

Modified:
- ...

Deleted:
- ...

Migration Impact:
- None. New and extended checks only; no governance semantics change.

## Notes
Keep the existing `Path(__file__).resolve().parents[3]` resolution. It is
correct and deliberately independent of the caller's working directory
(verified in S001, CHK-S001-05). What is being added is a separate assertion
that this resolved root *is* the repository root.
