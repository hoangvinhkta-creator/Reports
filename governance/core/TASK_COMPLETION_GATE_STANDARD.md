# Task Completion Gate Standard

## Purpose
Define how each task proves it is correctly completed.

## Core Rule
CODE COMPLETE ≠ TASK COMPLETE.

A task is DONE only when:
- all REQUIRED checks PASS,
- the required evidence level is satisfied,
- Exit Criteria are satisfied.

## Mandatory Evidence Link
Every Completion Gate check must follow `governance/core/EVIDENCE_STANDARD.md`.

A PASS without the required evidence level is not a valid PASS.

If a check was not actually executed:
Status = NOT_TESTED.

## Gate Creation Timing

### During S000 / Planning
Create preliminary Completion Gates for future tasks.

### Before Task Becomes READY
Review and finalize the gate using current project knowledge.

### After Freeze
The agent must not remove or weaken REQUIRED checks simply to make the task pass.

## Task Mode

### MICRO
Use `governance/templates/MICRO_TASK_CHECKLIST.md`.

### MAJOR
Use the full gate structure below.

### SPIKE / EXPLORATORY
Gate focuses on learning outcomes, evidence, constraints discovered, alternatives compared, and recommendation produced.

## Check Categories
Use only categories relevant to the task:

- Functional
- Architecture
- Data
- Security
- Routing
- API
- UI/UX
- Accessibility
- Performance
- Reliability
- Error Handling
- Migration
- Backward Compatibility
- Testing
- Regression
- Documentation
- Observability
- Deployment
- Audit
- Backup / Rollback

## Check Priority
Each check is:

- REQUIRED
- RECOMMENDED
- OPTIONAL

Any REQUIRED check that is FAIL, BLOCKED, or NOT_TESTED prevents DONE unless explicitly NOT_APPLICABLE with valid justification.

## Check Status
- NOT_TESTED
- PASS
- FAIL
- BLOCKED
- NOT_APPLICABLE

## Evidence Record
Each important check must include:

Check ID:
...

Priority:
...

Status:
...

Evidence Level:
E0 / E1 / E2

Evidence:
...

Executed By:
...

Timestamp:
...

## Risk-Based Evidence
Follow `governance/core/EVIDENCE_STANDARD.md`.

Summary:
- Risk 1–2: E0/E1 depending on check.
- Risk 3: E1 mandatory for executable REQUIRED checks.
- Risk 4–5: E1 mandatory; security/data-critical checks should seek E2.

## Exit Criteria
Typical exit criteria:

1. 100% REQUIRED checks PASS.
2. Required evidence levels are satisfied.
3. 0 critical unresolved defects.
4. 0 unresolved required security failures.
5. Relevant build/type/lint checks PASS.
6. Relevant regression checks PASS.
7. Required documentation is updated.
8. `PROJECT/PROJECT_PROGRESS.md` is updated.
9. Session handoff is written when required by task mode.

## Gate Change Control
Use:

COMPLETION GATE CHANGE PROPOSAL

Original check:
...

Proposed change:
...

Reason:
...

Risk:
...

Impact:
...

Do not silently lower quality criteria.
