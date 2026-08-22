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
