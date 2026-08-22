# Audit Findings — S001

Project:
`hoangvinhkta-creator/Reports`

Session:
S001 — Discovery & Baseline

Date:
2026-08-22 (UTC)

Profile:
AUDIT (read-only)

Baseline commit:
`0394267`

Severity standard:
`governance/audit/AUDIT_FINDINGS_TEMPLATE.md`

Evidence standard:
`governance/core/EVIDENCE_STANDARD.md`

All paths below are relative to
`AI_ENGINEERING_CONSTITUTION_TEMPLATE_V3_2_FINAL_COMPACT/` unless a path is
explicitly described as repository-root relative.

## Summary Table

| ID | Severity | Category | Affected Area | Status |
|---|---|---|---|---|
| FIND-001 | HIGH | Architecture | Repository deployment layout | OPEN |
| FIND-002 | HIGH | Operations | `PROJECT/` state files | OPEN |
| FIND-003 | MEDIUM | Documentation | `CLAUDE.md`, `governance/core/PROJECT_PROFILE_STANDARD.md` | OPEN |
| FIND-004 | MEDIUM | Documentation | `CLAUDE.md` | OPEN |
| FIND-005 | MEDIUM | Operations | `governance/reference/COMPACT_STRUCTURE_VALIDATION.md` | OPEN |
| FIND-006 | MEDIUM | Documentation | `governance/reference/START_HERE_USAGE_GUIDE_V3_2.md` | OPEN |
| FIND-007 | MEDIUM | Operations | `governance/scripts/governance/*.py` | OPEN |
| FIND-008 | LOW | Operations | CI / enforcement layer | OPEN |
| FIND-009 | LOW | Operations | Repository root hygiene | OPEN |
| FIND-010 | INFO | Architecture | Application surface | OPEN |
| FIND-011 | LOW | Documentation | `governance/reference/history/CHANGELOG_V3_1.md` | OPEN |
| FIND-012 | LOW | Documentation | `governance/scripts/governance/README.md` | OPEN |

Counts — CRITICAL 0 / HIGH 2 / MEDIUM 5 / LOW 4 / INFO 1. Total 12.

---

## FIND-001

Finding ID:
FIND-001

Severity:
HIGH

Category:
Architecture

Affected Area:
Repository deployment layout (repository root)

Current Behavior:
The entire governance package is nested one directory below the repository
root, inside `AI_ENGINEERING_CONSTITUTION_TEMPLATE_V3_2_FINAL_COMPACT/`.
The repository root contains only `.git` and that one directory. `CLAUDE.md`
is therefore not at the repository root.

Expected Behavior:
`governance/reference/START_HERE_USAGE_GUIDE_V3_2.md` (PHẦN 1) requires the
four entries `CLAUDE.md`, `PROJECT/`, `docs/`, `governance/` to be merged into
the repository root, and explicitly marks the nested-folder layout under a
"Không nên" (should not do) heading, with the stated reason: "Framework phải
nằm cùng cấp với code của project để agent coi nó là governance của chính repo."

Evidence:
Repository root listing, executed 2026-08-22T14:05Z:

```text
$ ls -A /home/user/Reports
.git
AI_ENGINEERING_CONSTITUTION_TEMPLATE_V3_2_FINAL_COMPACT
```

Source of the expected layout — `governance/reference/START_HERE_USAGE_GUIDE_V3_2.md`,
"### Không nên" block:

```text
CRM/
└── AI_ENGINEERING_CONSTITUTION_TEMPLATE_V3_2/
    ├── CLAUDE.md
    ├── PROJECT/
    └── ...
```

Evidence Level:
E1

Risk:
An agent or human opening the repository does not land on `CLAUDE.md` and has
no signal that governance exists. The mandatory read-before-work ordering
defined in `governance/core/00_SESSION_ORCHESTRATION.md` is silently skipped
rather than loudly failed. Every subsequent session inherits the omission.
The defect is invisible to the shipped validators (see FIND-007).

Likely Cause:
The package was committed as an extracted archive directory rather than merged
into the repository root.

Recommended Fix:
`git mv` all four top-level entries of the package to the repository root and
remove the now-empty wrapper directory. Path-only move; no content edit, per
the content-preservation rule in `governance/README.md`. Re-run all validators
after the move to confirm ROOT resolution is unchanged.

Suggested Task:
REM-T02

Dependencies:
Should land before REM-T04 so canonical path references are repaired once, not
twice.

Status:
OPEN

Verification Required:
- `ls -A` at repository root shows `CLAUDE.md`, `PROJECT/`, `docs/`, `governance/`.
- `validate_structure.py` PASS after the move (E1).
- `git log --follow` confirms history preserved for a sample moved file (E1).

---

## FIND-002

Finding ID:
FIND-002

Severity:
HIGH

Category:
Operations

Affected Area:
`PROJECT/PROJECT_PROFILE.md`, `PROJECT/PROJECT_PROGRESS.md`,
`PROJECT/PROJECT_DECISIONS.md`

Current Behavior:
At the S001 baseline all three project state files were unmodified templates.
`PROJECT/PROJECT_PROFILE.md` carried `Status: UNINITIALIZED` and
`Selected Profile: TO_BE_SELECTED_IN_S000`. `PROJECT/PROJECT_PROGRESS.md`
contained only placeholder `...` values and an empty roadmap skeleton.
S000 — PROJECT OPEN was never executed against this repository.

Expected Behavior:
`governance/core/00_SESSION_ORCHESTRATION.md` requires S000 to select a profile
and initialize `PROJECT/PROJECT_PROFILE.md` and `PROJECT/PROJECT_PROGRESS.md`
before any discovery or task session. `CLAUDE.md` requires every implementation
session to read those files and determine the current task from them.

Evidence:
`validate_project_state.py`, executed 2026-08-22T14:03Z, Python 3.11.15:

```text
PROJECT STATE: FAIL
- PROJECT/PROJECT_PROFILE.md must contain a valid Selected Profile: AUDIT, PRODUCT, SOLO_LITE, TEAM_PRODUCTION
- PROJECT_PROGRESS.md must contain a valid Profile value: AUDIT, PRODUCT, SOLO_LITE, TEAM_PRODUCTION
exit=1
```

Evidence Level:
E1

Risk:
Session Open Protocol cannot complete. No profile means no defined governance
depth, so no rule set is authoritative and no Ready Gate can be evaluated. Any
session that proceeds does so on conversational memory, which
`CLAUDE.md` ("Progress Questions") explicitly forbids as a basis for answering
progress questions.

Likely Cause:
The package was committed without running S000.

Recommended Fix:
Execute S000 properly: select and justify a profile, populate the progress file
with a real roadmap, and record the initial decisions. S001 performed the
minimum bootstrap needed to run discovery at all (profile selection + state
initialization, recorded as DEC-001); a full S000 pass should still confirm
phase/task decomposition and preliminary gates for the post-audit profile.

Suggested Task:
REM-T01

Dependencies:
None.

Status:
OPEN — partially mitigated in S001 by the DEC-001 bootstrap; the full S000
decomposition remains outstanding.

Verification Required:
- `validate_project_state.py` → `PROJECT STATE: PASS` (E1).
- `PROJECT/PROJECT_PROGRESS.md` contains a non-placeholder roadmap and a
  Current Task (E1, file inspection).

---

## FIND-003

Finding ID:
FIND-003

Severity:
MEDIUM

Category:
Documentation

Affected Area:
`CLAUDE.md` line 215; `governance/core/PROJECT_PROFILE_STANDARD.md` line 77

Current Behavior:
Both files reference `OPTIONAL_ENFORCEMENT_LAYER.md` as a repository-root
relative path. The file does not exist at that path. Its actual location is
`governance/reference/OPTIONAL_ENFORCEMENT_LAYER.md`.

Expected Behavior:
The compact refactor rule in `governance/README.md` permits moving files and
updating canonical paths, and `governance/reference/PACKAGE_MANIFEST.md`
correctly lists the file at `governance/reference/OPTIONAL_ENFORCEMENT_LAYER.md`.
Both references should use that canonical path.

Evidence:
Repository-relative reference resolution scan over all 67 tracked `.md` files (67 md + 5 py + 1 svg = 73),
executed 2026-08-22T14:04Z. A reference was reported broken only when it
resolved from neither the package root nor the referencing file's own
directory:

```text
CLAUDE.md
   -> OPTIONAL_ENFORCEMENT_LAYER.md
governance/core/PROJECT_PROFILE_STANDARD.md
   -> OPTIONAL_ENFORCEMENT_LAYER.md
governance/reference/history/CHANGELOG_V3_1.md
   -> PROJECT_PROFILE.md
```

Corroborating grep, same session:

```text
$ grep -rn 'OPTIONAL_ENFORCEMENT_LAYER' --include=*.md .
./governance/reference/PACKAGE_MANIFEST.md:56:- `governance/reference/OPTIONAL_ENFORCEMENT_LAYER.md`
./governance/reference/history/ACCEPTANCE_CHECKLIST_V3_1.md:61:- [ ] `governance/reference/OPTIONAL_ENFORCEMENT_LAYER.md` exists.
./governance/core/PROJECT_PROFILE_STANDARD.md:77:- `OPTIONAL_ENFORCEMENT_LAYER.md` with CI integration where practical.
./CLAUDE.md:215:- `OPTIONAL_ENFORCEMENT_LAYER.md`
```

Evidence Level:
E1

Risk:
`CLAUDE.md` is the single agent entry point and
`governance/core/PROJECT_PROFILE_STANDARD.md` defines the TEAM_PRODUCTION rule set. An agent
following either reference gets a missing file. The likely failure mode is
silent: the agent treats the enforcement layer as absent and proceeds without
it, which is precisely the rule group intended to add CI enforcement.

Likely Cause:
Path substitution during the compact refactor missed these two occurrences.

Recommended Fix:
Update both references to `governance/reference/OPTIONAL_ENFORCEMENT_LAYER.md`.
Text-only edit; no semantic change.

Suggested Task:
REM-T04

Dependencies:
REM-T02 (perform after the root promotion so paths are repaired once).

Status:
OPEN

Verification Required:
- Reference resolution scan reports 0 broken canonical references (E1).
- `grep -rn 'OPTIONAL_ENFORCEMENT_LAYER'` shows no bare-root reference (E1).

---

## FIND-004

Finding ID:
FIND-004

Severity:
MEDIUM

Category:
Documentation

Affected Area:
`CLAUDE.md` line 27

Current Behavior:
The "Core Principle" section maps "Reusable forms" to `templates/`. That
directory does not exist. The templates live at `governance/templates/`.

Expected Behavior:
The same file's "Compact Directory Layout" section (lines 3–14) states that
static governance is stored under `governance/`, and every other reference in
`CLAUDE.md` uses the `governance/templates/...` form. Line 27 should match.

Evidence:
```text
$ grep -rn '`\(templates\|scripts\)/' --include=*.md . | grep -v 'governance/'
./CLAUDE.md:27:- Reusable forms → `templates/`
```

Directory check, same session:

```text
$ ls templates
ls: cannot access 'templates': No such file or directory
$ ls governance/templates
E2_INDEPENDENT_REVIEW_TEMPLATE.md
MICRO_TASK_CHECKLIST.md
PROJECT_DECISIONS_TEMPLATE.md
PROJECT_PROGRESS_TEMPLATE.md
SESSION_HANDOFF_TEMPLATE.md
TASK_DEFINITION_TEMPLATE.md
```

Evidence Level:
E1

Risk:
Lower than FIND-003 because the correct path appears elsewhere in the same
file, so an agent is likely to recover. Still a contradiction inside the single
canonical entry point, and it is the kind of drift that accumulates.

Likely Cause:
Same incomplete path substitution as FIND-003.

Recommended Fix:
Change line 27 to `governance/templates/`.

Suggested Task:
REM-T04

Dependencies:
REM-T02.

Status:
OPEN

Verification Required:
- Reference resolution scan reports 0 broken canonical references (E1).

---

## FIND-005

Finding ID:
FIND-005

Severity:
MEDIUM

Category:
Operations

Affected Area:
`governance/reference/COMPACT_STRUCTURE_VALIDATION.md` line 75

Current Behavior:
The shipped validation report asserts:

```text
## Repository-relative Reference Integrity

Broken canonical path references: 0

PASS — no broken canonical repository-relative `.md`/`.py`/`.svg` references detected.
```

The repository state contradicts this. FIND-003 and FIND-004 document three
unresolvable canonical references in the same package the report validates.

Expected Behavior:
Per `governance/core/EVIDENCE_STANDARD.md` ("Evidence Integrity"), a recorded
result must correspond to an actual executed check. A shipped artifact
asserting PASS must be re-derivable from the repository as shipped.

Evidence:
The report's claim:

```text
$ grep -n 'Broken canonical path references' governance/reference/COMPACT_STRUCTURE_VALIDATION.md
75:Broken canonical path references: 0
```

Contradicting scan output from this session is reproduced in full under
FIND-003 (three broken references across two current files and one historical
file).

Evidence Level:
E1

Risk:
This is the highest-order concern in the MEDIUM band. The package's central
promise is that gates pass on evidence rather than narrative. A shipped
validation artifact that asserts a false PASS is exactly the failure mode
`governance/core/EVIDENCE_STANDARD.md` exists to prevent, and it teaches future sessions to
trust reference reports without re-derivation.

Likely Cause:
The reference-integrity check was either not executed, or executed with a
matcher that did not resolve backtick-quoted bare filenames.

Recommended Fix:
Two-part. (1) After REM-T04 repairs the references, re-run the check and update
the report with the actual command and output rather than a bare assertion.
(2) Implement the check as a script under `governance/scripts/governance/` so
the claim is machine-reproducible instead of hand-written.

Suggested Task:
REM-T05 (report truth-up), REM-T03 (script implementation)

Dependencies:
REM-T02, REM-T04.

Status:
OPEN

Verification Required:
- New reference-integrity validator exits 0 (E1).
- Report content matches that validator's actual output (E1).
- E2 re-derivation by an independent reviewer session, per
  `governance/core/EVIDENCE_STANDARD.md` "Solo Independent Review Procedure".

---

## FIND-006

Finding ID:
FIND-006

Severity:
MEDIUM

Category:
Documentation

Affected Area:
`governance/reference/START_HERE_USAGE_GUIDE_V3_2.md` lines 83, 85, 144, 146, 179

Current Behavior:
The file opens with the compact layout ("Bản Compact KHÔNG đổ 60+ file
governance ra root", four root entries only), but PHẦN 1, PHẦN 2 and PHẦN 3
lower in the same file still present the pre-compact V3.2 layout with
`templates/` and `scripts/` as repository-root entries.

Expected Behavior:
The whole guide should describe one layout. Under the compact structure the
root entries are `CLAUDE.md`, `PROJECT/`, `docs/`, `governance/`.

Evidence:
```text
$ grep -n '├── templates/\|├── scripts/\|- `templates/`' governance/reference/START_HERE_USAGE_GUIDE_V3_2.md
83:├── templates/
85:├── scripts/
179:- `templates/`,

$ grep -n -E '^(templates|scripts)/$' governance/reference/START_HERE_USAGE_GUIDE_V3_2.md
144:templates/
146:scripts/
```

Line 144/146 sit inside the PHẦN 2 "structure check after install" block, i.e.
a human following the guide's own verification step would look for two
directories that must not exist in a compact deployment.

Evidence Level:
E1

Risk:
The onboarding document is self-contradictory at the exact step where a user
verifies deployment correctness. This is plausibly a contributing cause of
FIND-001: a reader working from an inconsistent guide is more likely to get
the layout wrong.

Likely Cause:
The compact section was prepended to the V3.2 guide without reconciling the
body.

Recommended Fix:
Update PHẦN 1, PHẦN 2 and PHẦN 3 to the compact layout, and change the PHẦN 2
verification block to list the four compact root entries.

Suggested Task:
REM-T05

Dependencies:
REM-T02 (so the guide documents the layout the repository actually has).

Status:
OPEN

Verification Required:
- No occurrence of `templates/` or `scripts/` as a root-level entry remains in
  the guide (E1, grep).
- The guide's verification block matches `validate_structure.py`'s required
  paths (E1).

---

## FIND-007

Finding ID:
FIND-007

Severity:
MEDIUM

Category:
Operations

Affected Area:
`governance/scripts/governance/validate_structure.py`,
`validate_project_state.py`, `validate_evidence.py`,
`validate_task_completion.py`, `validate_refactor_preservation.py`

Current Behavior:
Every validator resolves its ROOT from its own file location:

```python
ROOT = Path(__file__).resolve().parents[3]
```

`parents[3]` from `governance/scripts/governance/<script>.py` is the package
directory. Consequently the validators always validate the package directory,
regardless of where the repository root actually is or where the command is
invoked from. `validate_structure.py` returns PASS on this repository even
though the deployment layout is wrong (FIND-001).

Expected Behavior:
The validators correctly ignore the caller's working directory — that part is
sound and should be kept. What is missing is any check that the package root
*is* the repository root. No shipped validator can detect the FIND-001 class of
defect.

Evidence:
Executed from the actual git repository root, 2026-08-22T14:03Z:

```text
$ cd /home/user/Reports
$ python3 AI_ENGINEERING_CONSTITUTION_TEMPLATE_V3_2_FINAL_COMPACT/governance/scripts/governance/validate_structure.py
GOVERNANCE STRUCTURE: PASS
Checked 21 required paths.
exit=0
```

A PASS was returned while `CLAUDE.md` was absent from the repository root.

Source, `validate_structure.py` line 5:

```python
ROOT = Path(__file__).resolve().parents[3]
```

Evidence Level:
E1

Risk:
False assurance. `validate_structure.py` is the check the START_HERE guide
tells users to run to confirm a correct install, and it passes on an install
the same guide marks as wrong. Any deployment defect at this level goes
undetected and is inherited by every session.

Likely Cause:
The validators were written to be robust to the caller's working directory, and
deployment-root correctness was treated as a human responsibility.

Recommended Fix:
Add a deployment-root assertion: locate the git root (e.g. `.git` discovered by
walking upward) and verify it equals the resolved ROOT; FAIL with an explicit
message when it does not. Where no git root exists, report the check as
NOT_APPLICABLE rather than silently passing. Keep the existing `__file__`-based
resolution.

Suggested Task:
REM-T03

Dependencies:
REM-T02 should be decided first, since the check encodes the expected layout.

Status:
OPEN

Verification Required:
- New check FAILs against a deliberately nested fixture (E1, regression fixture).
- New check PASSes against the corrected root layout (E1).

---

## FIND-008

Finding ID:
FIND-008

Severity:
LOW

Category:
Operations

Affected Area:
CI / enforcement layer (repository-root `.github/`)

Current Behavior:
No `.github/` directory exists. The five validators are runnable only by hand.
`governance/reference/OPTIONAL_ENFORCEMENT_LAYER.md` is shipped but not wired
to any pipeline.

Expected Behavior:
`governance/core/PROJECT_PROFILE_STANDARD.md` requires the optional enforcement
layer "with CI integration where practical" only for TEAM_PRODUCTION. Under
AUDIT or SOLO_LITE, CI may legitimately be recorded NOT_APPLICABLE with a
justification.

Evidence:
```text
$ ls -A /home/user/Reports/.github
ls: cannot access '/home/user/Reports/.github': No such file or directory
```

Evidence Level:
E1

Risk:
Low at the current profile. Manual validator runs are acceptable for AUDIT
work. The risk is that manual-only enforcement degrades: FIND-002 and FIND-005
are both instances of a check that was supposed to be run and was not.

Likely Cause:
Profile-appropriate omission; no profile was ever recorded, so the omission was
never justified either.

Recommended Fix:
Deferred. Decide when the post-audit profile is selected. If PRODUCT or
TEAM_PRODUCTION is chosen, add a workflow running all five validators on push
and pull request. If SOLO_LITE, record CI as NOT_APPLICABLE with justification
in `PROJECT/PROJECT_PROFILE.md` as that standard permits.

Suggested Task:
REM-T07

Dependencies:
Post-audit profile transition (see `governance/reference/START_HERE_USAGE_GUIDE_V3_2.md` PHẦN 7).

Status:
OPEN — DEFERRED pending profile decision.

Verification Required:
- Either a green CI run executing all five validators (E2), or an explicit
  NOT_APPLICABLE justification recorded in the profile (E0 is sufficient for a
  recorded profile decision).

---

## FIND-009

Finding ID:
FIND-009

Severity:
LOW

Category:
Operations

Affected Area:
Repository root

Current Behavior:
The repository root has no `README.md`, no `LICENSE`, and no `.gitignore`.

Expected Behavior:
`governance/product/23_DOCUMENTATION_STANDARDS.md` applies at TEAM_PRODUCTION.
Independent of profile, a repository whose sole content is a reusable
governance package benefits from a root README stating what it is and how to
deploy it, and from a `.gitignore` preventing `__pycache__/` from the validator
runs being committed.

Evidence:
```text
$ ls -A /home/user/Reports
.git
AI_ENGINEERING_CONSTITUTION_TEMPLATE_V3_2_FINAL_COMPACT
```

Evidence Level:
E1

Risk:
Minor. A newcomer has no orientation at the repository root — which compounds
FIND-001, since there is currently nothing at root pointing to the governance
package either. Absent `.gitignore`, Python bytecode caches produced by
validator runs can be committed accidentally.

Likely Cause:
Repository created solely to hold the uploaded package.

Recommended Fix:
Add a short root `README.md` pointing to `CLAUDE.md`, and a `.gitignore`
covering `__pycache__/` and `*.pyc`. `LICENSE` is a business decision, not an
engineering one — raise it, do not choose it.

Suggested Task:
REM-T06

Dependencies:
REM-T02 (add the README after the root layout is settled).

Status:
OPEN

Verification Required:
- Files present at repository root (E1).
- `git status` clean after a full validator run (E1).

---

## FIND-010

Finding ID:
FIND-010

Severity:
INFO

Category:
Architecture

Affected Area:
Application surface (whole repository)

Current Behavior:
The repository contains no application code, no runtime, no dependency
manifest, no database, no authentication surface and no external integration.
All 73 tracked files are the governance package.

Expected Behavior:
Not a defect. Recorded so that sections 1–8 of the Discovery Baseline are
explicitly NOT_APPLICABLE_AT_BASELINE rather than silently blank, and so a
future session can tell "not audited" apart from "nothing to audit".

Evidence:
```text
$ git ls-files | wc -l
73
$ find AI_ENGINEERING_CONSTITUTION_TEMPLATE_V3_2_FINAL_COMPACT -type f | wc -l
73
$ grep -n "Total files" .../governance/reference/PACKAGE_MANIFEST.md
3:Total files: 73
$ find . -path ./.git -prune -o -type f \( -name '*.js' -o -name '*.ts' -o -name '*.json' -o -name '*.html' -o -name '*.yml' -o -name '*.yaml' \) -print
(no output)
```

Tracked file count, filesystem count, and the shipped manifest's declared
count all agree at 73. Package inventory integrity: PASS.

Evidence Level:
E1

Risk:
None at baseline. The note exists to prevent a future session misreading the
empty inventory sections as an incomplete audit.

Likely Cause:
N/A — expected state for a governance-only repository.

Recommended Fix:
No action. Re-run discovery for sections 1–8 when application code is first
introduced.

Suggested Task:
None.

Dependencies:
None.

Status:
OPEN — informational, no remediation intended.

Verification Required:
None.

---

## FIND-011

Finding ID:
FIND-011

Severity:
LOW

Category:
Documentation

Affected Area:
`governance/reference/history/CHANGELOG_V3_1.md` line 19

Current Behavior:
References `PROJECT_PROFILE.md` as a bare filename. It does not resolve from
the package root; the file is at `PROJECT/PROJECT_PROFILE.md`.

Expected Behavior:
Historical archive files are frozen records and are not expected to carry
current canonical paths. However, the reference-integrity claim in
`governance/reference/COMPACT_STRUCTURE_VALIDATION.md` (FIND-005) does not exclude `history/`, so
either the reference or the claim's scope should be corrected.

Evidence:
```text
$ grep -n 'PROJECT_PROFILE.md' governance/reference/history/CHANGELOG_V3_1.md
19:- Runtime `PROJECT_PROFILE.md`.
```

Evidence Level:
E1

Risk:
Negligible operationally. Relevant only because it is one of the three
references contradicting the shipped 0-broken-references claim.

Likely Cause:
Archived pre-compact content retained verbatim, which is correct behavior for
a historical record.

Recommended Fix:
Do not rewrite the historical file. Instead scope the reference-integrity
validator to exclude `governance/reference/history/`, and state that exclusion
explicitly in the validation report so the claim is precise.

Suggested Task:
REM-T03 (validator scope), REM-T05 (report wording)

Dependencies:
None.

Status:
OPEN

Verification Required:
- Validator's exclusion list is documented in the report (E1).

---

## FIND-012

Finding ID:
FIND-012

Severity:
LOW

Category:
Documentation

Affected Area:
`governance/scripts/governance/README.md`

Current Behavior:
The validator README documents two of the five validators
(`validate_structure.py`, `validate_project_state.py`).
`validate_task_completion.py`, `validate_evidence.py` and
`validate_refactor_preservation.py` are not mentioned, including
`validate_refactor_preservation.py`'s required positional argument.

Expected Behavior:
The README is the discovery surface for the enforcement tooling. The START_HERE
guide (PHẦN 2) already tells users to run four of the five; the README should
at minimum match that, and document the fifth script's argument.

Evidence:
```text
$ cat governance/scripts/governance/README.md
... documents only:
python governance/scripts/governance/validate_structure.py
python governance/scripts/governance/validate_project_state.py
```

Undocumented invocation contract, observed 2026-08-22T14:03Z:

```text
$ python3 governance/scripts/governance/validate_refactor_preservation.py
USAGE: validate_refactor_preservation.py <non-compact-v3.2-final-dir>
exit=2
```

Evidence Level:
E1

Risk:
Low. Two enforcement checks that exist are less likely to be run, which
weakens the same manual-discipline assumption noted in FIND-008.

Likely Cause:
README written before the later validators were added.

Recommended Fix:
List all five validators with purpose, invocation and expected exit codes; note
that `validate_refactor_preservation.py` requires a comparison directory and is
only meaningful during a structure refactor.

Suggested Task:
REM-T05

Dependencies:
None.

Status:
OPEN

Verification Required:
- README lists all five scripts present in the directory (E1, diff against
  `ls governance/scripts/governance/*.py`).

---

## Evidence Ledger

| Check | Command | Result | Level | Executed By | Timestamp |
|---|---|---|---|---|---|
| CHK-S001-01 | `python3 governance/scripts/governance/validate_structure.py` | PASS (21 paths) | E1 | S001 agent | 2026-08-22T14:03Z |
| CHK-S001-02 | `python3 governance/scripts/governance/validate_project_state.py` | FAIL (2 errors) | E1 | S001 agent | 2026-08-22T14:03Z |
| CHK-S001-03 | `python3 governance/scripts/governance/validate_task_completion.py` | PASS (0 DONE) | E1 | S001 agent | 2026-08-22T14:03Z |
| CHK-S001-04 | `python3 governance/scripts/governance/validate_evidence.py` | PASS (0 records) | E1 | S001 agent | 2026-08-22T14:03Z |
| CHK-S001-05 | `validate_structure.py` invoked from git root | PASS despite wrong layout | E1 | S001 agent | 2026-08-22T14:03Z |
| CHK-S001-06 | Repository-relative reference resolution scan (67 `.md` files) | 3 broken references | E1 | S001 agent | 2026-08-22T14:04Z |
| CHK-S001-07 | `git ls-files \| wc -l` vs `find \| wc -l` vs manifest count | 73 / 73 / 73 — consistent | E1 | S001 agent | 2026-08-22T14:05Z |
| CHK-S001-08 | Root inventory `ls -A /home/user/Reports` | Only `.git` + package dir | E1 | S001 agent | 2026-08-22T14:05Z |
| CHK-S001-09 | Application-code sweep (`*.js`,`*.ts`,`*.json`,`*.html`,`*.yml`,`*.yaml`) | 0 matches | E1 | S001 agent | 2026-08-22T14:05Z |

E2 status:
NOT_OBTAINED. No CI, no staging and no independent reviewer session ran against
these findings. Per `governance/core/EVIDENCE_STANDARD.md`, this limitation is
recorded rather than papered over. Findings whose remediation touches the agent
read path (FIND-001, FIND-003, FIND-005, FIND-007) should obtain E2 via an
independent reviewer session before their tasks are marked DONE.
