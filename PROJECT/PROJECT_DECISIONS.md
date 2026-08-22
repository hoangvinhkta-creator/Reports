# PROJECT DECISIONS

Use this file for tactical project decisions that are important across sessions
but are not significant enough for a full ADR.

## DEC-001

Date:
2026-08-22

Task:
S001 — Discovery & Baseline

Decision:
Perform the minimum S000 bootstrap (profile selection + project state
initialization) inside S001, rather than refusing to open S001.

Reason:
`governance/core/00_SESSION_ORCHESTRATION.md` Session Open Protocol requires
reading `PROJECT/PROJECT_PROFILE.md` and `PROJECT/PROJECT_PROGRESS.md` and
identifying a current task. Both files were unmodified templates
(`Status: UNINITIALIZED`), so S001 could not legitimately open. The two options
were to stop with nothing delivered, or to perform the bootstrap explicitly and
record it. The bootstrap is governance-only work, which S000 permits
("S000 must not modify production feature code unless explicitly required for
bootstrap/governance"), and there is no production code in this repository at
all.

Impact:
`PROJECT/PROJECT_PROFILE.md`, `PROJECT/PROJECT_PROGRESS.md` and this file were
written during S001. This is **not** a substitute for a full S000: phase/task
decomposition, dependency graphing, difficulty/risk estimation across the
future project and preliminary gates for non-remediation work remain owed. That
remaining work is tracked as REM-T01, and FIND-002 stays OPEN rather than being
closed by this decision.

Can Revisit After:
REM-T01 completes.

## DEC-002

Date:
2026-08-22

Task:
S001 — Discovery & Baseline

Decision:
Scope the S001 audit to (a) governance deployment integrity and (b) governance
package internal consistency. Record sections 1–8 of the Discovery Baseline
template as NOT_APPLICABLE_AT_BASELINE rather than leaving them blank.

Reason:
The repository contains no application code, no runtime, no data store, no
authentication and no external integration — 73 tracked files, all of them the
governance package (FIND-010, E1). The template's architecture/routing/data/
auth/security/logic/API/environment sections have no subject. Leaving them
blank would be indistinguishable from an incomplete audit; marking them
explicitly preserves that distinction for future sessions.

Impact:
The finding set is dominated by governance-integrity issues rather than product
risk. Sections 1–8 must be re-baselined in a new discovery session when
application code is first introduced.

Can Revisit After:
First application code lands in the repository.

## DEC-003

Date:
2026-08-22

Task:
S001 — Discovery & Baseline

Decision:
Store audit artifacts under `docs/audit/` — a new directory — rather than in
`docs/tasks/`, `docs/sessions/` or `docs/reviews/`.

Reason:
`CLAUDE.md` assigns `docs/` to runtime tasks, sessions, reviews and ADRs, and
the existing subdirectories each have a declared, different purpose per their
READMEs. Discovery baselines and audit findings are a fourth runtime artifact
class with no designated home. Putting them in `docs/reviews/` would collide
with the E2 independent-review artifacts that
`governance/core/EVIDENCE_STANDARD.md` reserves that directory for.

Impact:
New directory `docs/audit/` containing `docs/audit/S001_DISCOVERY_BASELINE.md`,
`docs/audit/S001_AUDIT_FINDINGS.md` and `docs/audit/REMEDIATION_ROADMAP.md`. This is an additive
convention, not a change to any governance rule; no file under `governance/`
was modified. If a future version of the framework designates an official
location for audit artifacts, migrate to it.

Can Revisit After:
Any framework upgrade that defines an official audit artifact path.

## DEC-004

Date:
2026-08-22

Task:
S001 — Discovery & Baseline

Decision:
Write S001 artifacts inside the nested package directory
(`AI_ENGINEERING_CONSTITUTION_TEMPLATE_V3_2_FINAL_COMPACT/`) rather than at the
git repository root, despite FIND-001 identifying that nesting as a defect.

Reason:
All five validators resolve their ROOT from their own file location
(`Path(__file__).resolve().parents[3]`), which is the package directory. Writing
project state or audit artifacts at the git root would place them outside every
validator's view and make `validate_project_state.py` unfixable. Correcting the
layout is itself a finding with Blast Radius 5/5 (FIND-001 → REM-T02) and must
not be done as a side effect of an audit session, which is read-only.

Impact:
Artifacts move with everything else when REM-T02 promotes the package to the
repository root. Their paths relative to `CLAUDE.md` do not change, so no
reference in any artifact needs rewriting at that point.

Can Revisit After:
REM-T02 completes.

## DEC-005

Date:
2026-08-22

Task:
S002 — Roadmap Finalization

Decision:
Transition the project profile from AUDIT to PRODUCT.

Reason:
Owner instruction, taken after S001 completed the audit and produced findings
with severity, evidence and a remediation roadmap — the precondition
`governance/reference/START_HERE_USAGE_GUIDE_V3_2.md` PHẦN 7 sets for the
transition.

AUDIT is read-only by default and cannot execute remediation, so remaining
there would block all remediation tasks indefinitely. Between the two
realistic alternatives, SOLO_LITE would drop `PHASE_RELEASE_GATE_STANDARD` and
the architecture/data rule groups, and the remediation set contains a
repository-wide move with Blast Radius 5/5 (REM-T02) that warrants phase-level
verification. TEAM_PRODUCTION would add CODEOWNERS, incident response and API
versioning ceremony a single-owner documentation repository cannot meaningfully
satisfy.

Impact:
Eleven additional rule groups become mandatory. Most have no subject today and
are recorded as DORMANT in the Profile Compliance Matrix in
`PROJECT/PROJECT_PROFILE.md` — mandatory, but with nothing to govern yet.
DORMANT is not a waiver. One genuine gap surfaced: GAP-01 (Backup / DR), where
the GitHub remote is the only copy of the repository.

Production code changes are now permitted; the AUDIT read-only restriction is
lifted. Scope Lock still applies per task.

Can Revisit After:
Application code lands, at which point every DORMANT row must be re-checked and
TEAM_PRODUCTION reconsidered if the team grows.

## DEC-006

Date:
2026-08-22

Task:
S002 — Roadmap Finalization

Decision:
Map every remediation task to the Tier A–D vocabulary in
`governance/core/AGENT_CAPABILITY_MATRIX.md`, and record Tier D as
NOT_APPLICABLE for this project.

Reason:
S001 assigned tiers using invented labels ("standard", "senior") that do not
exist in the capability matrix. The matrix exists precisely so planning is not
hard-coded to ad-hoc names. `governance/core/AGENT_CAPABILITY_MATRIX.md` also requires Tier D
to be defined per project rather than assumed.

Impact:
REM-T02 is Tier C (repository-wide move, Blast Radius 5/5). REM-T03, REM-T05
and REM-T07 are Tier B. REM-T04 and REM-T06 are Tier A. Tier D is
NOT_APPLICABLE — this project has no UI, visual design or content-presentation
work. Re-define Tier D if an application with a user interface is added.

Can Revisit After:
Any change to the available agent roster, or the addition of UI work.

## DEC-007

Date:
2026-08-22

Task:
S002 — Roadmap Finalization

Decision:
Adopt CI voluntarily (REM-T07) even though
`governance/core/PROJECT_PROFILE_STANDARD.md` does not make
`governance/product/14_CI_CD_RELEASE_RULES.md` mandatory at PRODUCT, and
sequence it first in PHASE-01. Separately, confirm REM-T04 stays MICRO.

Reason:
Two separate calls, recorded together because both were made while finalizing
PHASE-01.

CI first: `governance/core/EVIDENCE_STANDARD.md` lists CI results as an E2
source. REM-T02's CHECK-T02-05 requires E2, and the project currently has no E2
path at all (RSK-004). Building CI before the highest-blast-radius task means
that task has independent evidence available when it needs it, rather than
depending solely on a reviewer session that may not happen.

REM-T04 stays MICRO: it satisfies every eligibility condition in
`governance/core/TASK_MODE_STANDARD.md` — Difficulty 1, Risk 2, Blast Radius 2,
no architecture, auth, schema, destructive-data or cross-module change. It
touches `CLAUDE.md`, which is the agent read path, but the change repairs three
broken path tokens rather than redesigning anything. The promotion rule stands:
if the repair needs more than those three lines, stop and promote to MAJOR.

Impact:
REM-T07 moves PHASE-03 → PHASE-01 position 1 (ROADMAP CHANGE CH-02). REM-T02
gains a dependency on it. REM-T07 carries a Critical Design Constraint — the
workflow must discover validators at runtime rather than hard-code paths —
because a hard-coded path would break at REM-T02's move and force a content
edit inside a Scope Lock that forbids one.

Can Revisit After:
REM-T07 completes, or if CI proves impractical on the available runner.

## DEC-008

Date:
2026-08-22

Task:
S002 — Roadmap Finalization

Decision:
Cancel REM-T01 as ABSORBED and mark FIND-002 RESOLVED.

Reason:
REM-T01 existed to complete the S000 procedure FIND-002 showed had never run.
Re-checking requirements with current project knowledge — step 1 of Roadmap
Finalization in `governance/core/00_SESSION_ORCHESTRATION.md` — showed that all
fifteen steps of the canonical S000 procedure have now been executed across S001
and S002. The step-by-step mapping is recorded in
`docs/tasks/TASK-REM-T01-project-state-init.md`.

FIND-002's stated Verification Required is met:
`validate_project_state.py` exits 0 (E1), and `PROJECT/PROJECT_PROGRESS.md`
carries a non-placeholder roadmap with a named Current Task (E1). E2 was not
obtained and is recorded as a limitation, not asserted.

Keeping the task open would create work whose entire Completion Gate is already
satisfiable at creation time.

Impact:
PHASE-01 loses its head node; REM-T07 becomes the entry point. The task file is
retained with a full Cancellation Record rather than deleted, so a later session
can see that S000 was executed rather than skipped. Issued formally as ROADMAP
CHANGE CH-01 in `docs/audit/REMEDIATION_ROADMAP.md`.

Reversal is documented in the task file: restore `Status: PLANNED`, set FIND-002
back to OPEN in the progress file and the traceability table, and re-insert
REM-T01 at the head of PHASE-01.

Can Revisit After:
Owner review of this session. This is the one S002 decision that changes the
roadmap's shape rather than only its metadata.
