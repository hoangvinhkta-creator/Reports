# Task Ready Gate Standard

## Purpose
Define when a task is allowed to enter implementation.

## Principle
A task must not start merely because it exists on the roadmap.

## MICRO Ready Gate
For eligible MICRO tasks use `governance/templates/MICRO_TASK_CHECKLIST.md`.

Do not force the full Major Task Ready Gate onto Micro Tasks.

## MAJOR Ready Gate

Required before READY:

- [ ] Objective is clear.
- [ ] Scope is defined.
- [ ] Out-of-scope is defined.
- [ ] Dependencies are DONE or explicitly waived.
- [ ] Expected touch area is identified.
- [ ] Relevant requirements are understood.
- [ ] Data impact is known.
- [ ] Security impact is known.
- [ ] Routing/API impact is known where relevant.
- [ ] Migration prerequisites are available where relevant.
- [ ] Difficulty is scored.
- [ ] Risk is scored.
- [ ] Blast Radius is scored.
- [ ] Primary agent tier is assigned.
- [ ] Escalation triggers are defined.
- [ ] Completion Gate is finalized.
- [ ] Completion Gate is frozen before implementation.

## SPIKE / EXPLORATORY Ready Gate
Required:
- [ ] Unknown/question is clearly stated.
- [ ] Hypothesis or learning objective is defined.
- [ ] Scope/time-box is defined.
- [ ] Evidence method is defined.
- [ ] No premature production acceptance criteria are forced.
- [ ] Output format for findings/recommendation is defined.

## Ready Status
- `PLANNED`
- `READY`
- `BLOCKED`

## Rule
A task cannot transition:

PLANNED
→ IN_PROGRESS

It must transition:

PLANNED
→ READY
→ IN_PROGRESS
