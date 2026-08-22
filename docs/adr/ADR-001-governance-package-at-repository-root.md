# ADR-001 — Governance package lives at the repository root

## Status
Accepted

## Date
2026-08-22

## Context

The AI Engineering Constitution V3.2 FINAL COMPACT package was committed to
this repository as an extracted archive directory,
`AI_ENGINEERING_CONSTITUTION_TEMPLATE_V3_2_FINAL_COMPACT/`. The repository root
therefore contains only `.git` and that one directory, and `CLAUDE.md` — the
single governance entry point — is one level below root.

S001 recorded this as FIND-001 (HIGH). Three properties of the current layout
drive the decision:

1. An agent or human opening the repository does not land on `CLAUDE.md` and
   receives no signal that governance exists. The mandatory read-before-work
   ordering in `governance/core/00_SESSION_ORCHESTRATION.md` is skipped
   silently rather than failing loudly.
2. The package's own guide,
   `governance/reference/START_HERE_USAGE_GUIDE_V3_2.md` PHẦN 1, marks exactly
   this nested layout under a "Không nên" heading, with the stated reason that
   the framework must sit at the same level as project code for an agent to
   treat it as governance of that repository.
3. Every validator resolves its root from `Path(__file__).resolve().parents[3]`,
   which is the package directory. They therefore validate the package rather
   than the repository, and `validate_structure.py` returns PASS on the
   mis-deployed tree (FIND-007, evidence CHK-S001-05). The defect is invisible
   to the tooling meant to catch it.

A decision is required now rather than later because every subsequent
remediation task edits files whose paths this decision changes.

## Decision

The four package entries — `CLAUDE.md`, `PROJECT/`, `docs/`, `governance/` —
are moved to the repository root, and the wrapper directory is removed.

The move is executed as REM-T02 and is **path-only**: `git mv` with zero
content change, per the content-preservation rule in `governance/README.md`.
Repairing the broken canonical references that the move does not fix is a
separate task (REM-T04), so that the move's diff can be verified as renames
only.

## Alternatives Considered

**A — Keep the nested layout and document it.**
Rejected. It contradicts the package's own installation guidance, and no amount
of documentation makes an agent read a `CLAUDE.md` it never sees. It would also
require every future consumer of this repository to learn a local exception.

**B — Keep the nested layout and change the validators to accept it.**
Rejected. This inverts the problem: it would make the tooling certify a layout
the framework defines as incorrect, deepening FIND-007 rather than closing it.

**C — Move the files and repair references in the same task.**
Rejected. It would make REM-T02's diff a mixture of renames and content edits,
so `git diff -M` could no longer prove that no governance semantics changed.
For a Blast Radius 5/5 change touching the agent read path, that proof is the
main safety mechanism. Separating the tasks costs one extra session and buys a
verifiable diff.

**D — Restructure into a `.governance/` hidden directory or similar.**
Rejected. It is a novel layout the framework does not define, and it would
diverge this repository from every other consumer of the same package.

## Rationale

Option C was the closest alternative and the reason for rejecting it is worth
stating plainly: the value of this move is not just the end state but the
ability to prove nothing else changed while reaching it. A pure rename diff is
mechanically verifiable; a mixed diff requires human judgement over 73 files.

Aligning with the framework's documented layout also means future upgrades of
the package apply cleanly, and the existing `parents[3]` root resolution stays
correct — the scripts' depth below the package root is unchanged by the move.

## Consequences

### Positive
- `CLAUDE.md` becomes the first thing seen at the repository root.
- The layout matches the framework's documented install, so package upgrades
  and any future application code sit where the guide expects.
- Validators begin validating the repository rather than a subdirectory.
- Closes FIND-001 and removes the precondition behind RSK-001.

### Negative / Tradeoffs
- All 73 tracked file paths change at once. Any external bookmark or link into
  the old path breaks. Nothing inside the repository breaks, because paths
  relative to `CLAUDE.md` are unchanged.
- The move must be sequenced ahead of REM-T03, REM-T04, REM-T05 and REM-T06,
  which serializes work that could otherwise proceed in parallel.
- `git log` without `--follow` shows a discontinuity at the move commit.

## Migration / Implementation Notes

Executed as REM-T02. See `docs/tasks/TASK-REM-T02-root-promotion.md` for the
frozen Completion Gate. The load-bearing checks:

- CHECK-T02-03 — `git diff --stat HEAD~1 -M` must show renames only, with zero
  content lines added or removed.
- CHECK-T02-04 — `git log --follow` must return pre-move history for at least
  three sampled files, including `CLAUDE.md`.
- CHECK-T02-05 — independent (E2) confirmation that no semantic edit occurred.

Preconditions: a pushed backup ref, and explicit owner confirmation given the
Blast Radius.

REM-T07 (CI) is sequenced before this task so that CHECK-T02-05 has an E2
source, and its workflow must discover validators at runtime rather than
hard-code paths — otherwise this move would break CI and force a content edit
that CHECK-T02-03 forbids.

## Supersedes
None

## Superseded By
None
