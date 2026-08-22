# Task Mode Standard

## Purpose
Scale process overhead to the actual size, risk, and uncertainty of the work.

## Mode 1 — MICRO TASK

Eligible only if ALL are true:
- Difficulty <= 2
- Risk <= 2
- Blast Radius <= 2
- No architecture change
- No auth/authorization change
- No persisted schema migration
- No destructive data operation
- No high-risk security impact
- No cross-module redesign

Examples:
- small UI bug,
- label/text correction,
- isolated calculation bug,
- small CSS fix,
- simple test correction.

Process:
- Track inline in `PROJECT/PROJECT_PROGRESS.md`.
- Use a compact Ready/Completion checklist.
- Separate task file and separate session handoff are optional unless work expands.

If scope/risk grows, promote to MAJOR TASK.

## Mode 2 — MAJOR TASK

Use for:
- normal feature,
- module change,
- bounded refactor,
- routing change,
- database/API change,
- moderate/high-risk work.

Requires:
- task definition file,
- dedicated session,
- Ready Gate,
- frozen Completion Gate,
- session handoff.

## Mode 3 — SPIKE / EXPLORATORY

Use when the correct solution or acceptance target is not yet known.

Examples:
- technical feasibility,
- prototype,
- game mechanic exploration,
- UX experiment,
- unknown library/integration behavior.

Goal:
Reduce uncertainty, not deliver production completeness.

Completion Gate should validate learning:
- hypothesis tested,
- alternatives compared,
- constraints discovered,
- prototype produced if useful,
- evidence recorded,
- recommendation documented,
- next implementation task defined if appropriate.

Do NOT force final implementation acceptance criteria before discovery is complete.

## Promotion Rules

MICRO → MAJOR if:
- Risk > 2,
- Blast Radius > 2,
- architecture/security/data impact appears,
- unexpected dependencies emerge.

SPIKE → MAJOR after:
- uncertainty reduced,
- implementation direction selected,
- requirements can be finalized.
