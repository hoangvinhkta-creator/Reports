# 00 — Session Orchestration

## Purpose
Define how a project is planned and executed across multiple AI coding sessions while preserving shared context, scope boundaries, progress, and verification.

## Core Model
One Major Task = One Primary Session.

Micro Tasks may be handled inline when eligible.
Spike/Exploratory Tasks may use a dedicated discovery session.

## Project Start Modes

### Small / New Project
S000 may combine:
- profile selection,
- project open,
- discovery,
- roadmap,
- task decomposition,
- preliminary gates.

### Large / Legacy Project
Prefer:
- S000 — Project Open + Profile Selection
- S001 — Discovery & Baseline
- S002 — Roadmap Finalization
- S003+ — Major Task Sessions

## S000 — PROJECT OPEN

S000 must execute in this order:

0. Select project profile using `governance/core/PROJECT_PROFILE_STANDARD.md`.
1. Write/update `PROJECT/PROJECT_PROFILE.md`.
2. Understand project objective and project type.
3. Determine project size and governance depth.
4. Inspect enough repository context to create an initial plan.
5. Decide whether work should begin in AUDIT mode.
6. Create major phases.
7. Create Major Tasks and identify eligible Micro/Spike tasks.
8. Create preliminary subtasks.
9. Create preliminary dependency graph.
10. Estimate Difficulty, Risk, and Blast Radius.
11. Recommend capability tier.
12. Create preliminary Completion Gates.
13. Initialize/update `PROJECT/PROJECT_PROGRESS.md`.
14. Record initial tactical decisions if needed.

For legacy/AUDIT work:
- use `governance/audit/DISCOVERY_BASELINE_TEMPLATE.md`;
- use `governance/audit/AUDIT_FINDINGS_TEMPLATE.md`;
- do not modify production feature code.

S000 must not modify production feature code unless explicitly required for bootstrap/governance.

## Roadmap Finalization

Before a future task becomes READY:

1. Re-check requirements using current project knowledge.
2. Confirm Task Mode.
3. Confirm dependencies.
4. Confirm Scope Lock.
5. Finalize Ready Gate.
6. Finalize Completion Gate.
7. Attach required evidence levels.
8. Freeze Completion Gate.
9. Assign primary and escalation capability tiers.

Do not freeze distant task details before discovery is sufficient.

## Major Task Requirements

Every Major Task must define:
- Task ID
- Name
- Task Mode
- Objective
- Scope
- Out of Scope
- Dependencies
- Blocks
- Parallel-safe tasks
- Expected touch area
- Difficulty
- Risk
- Blast Radius
- Primary Agent Tier
- Escalation Agent Tier
- Subtasks
- Ready Gate
- Completion Gate
- Evidence requirements
- Exit Criteria

## Micro Task Rule

Use `governance/templates/MICRO_TASK_CHECKLIST.md`.

A Micro Task does not require a separate task file or session handoff unless:
- scope expands,
- risk rises,
- the task is promoted to MAJOR.

## Spike / Exploratory Rule

The goal is to reduce uncertainty.

Completion is based on:
- hypothesis tested,
- alternatives compared,
- constraints discovered,
- evidence collected,
- recommendation documented.

Do not force premature production acceptance criteria.

## Session Open Protocol

At the beginning of every Major Task session:

1. Read `CLAUDE.md`.
2. Read `PROJECT/PROJECT_PROFILE.md`.
3. Read `PROJECT/PROJECT_PROGRESS.md`.
4. Read current task file.
5. Read relevant governance files.
6. Verify dependencies are DONE.
7. Verify Ready Gate passes.
8. Load Scope Lock.
9. Load frozen Completion Gate.
10. Load evidence requirements.
11. Begin implementation only after readiness is confirmed.

## Scope Lock

If work requires touching outside the approved scope:

SCOPE EXPANSION REQUIRED

Do not silently proceed.

Update impact analysis before expansion.

## Session Close Protocol

Before closing a Major Task session:

1. Run required verification.
2. Execute Completion Gate.
3. Record evidence with Evidence Level.
4. Update task status.
5. Update `PROJECT/PROJECT_PROGRESS.md`.
6. Record changed files.
7. Record new decisions.
8. Record blockers/risks.
9. Write session handoff.
10. Identify next recommended task.

## Roadmap Change Rule

Use:

ROADMAP CHANGE PROPOSAL

Reason:
...

Affected tasks:
...

Dependency impact:
...

Risk:
...

Recommended change:
...

Do not silently restructure the roadmap.

## Progress Questions

If the user asks:
- “đến đâu rồi?”
- “tiến độ thế nào?”
- “còn gì?”
- “bước tiếp theo?”
- “show checklist”

the agent must read `PROJECT/PROJECT_PROGRESS.md` first.

## Regression Invalidation

If a later change invalidates a guarantee of a completed task:
- keep the historical task DONE;
- create a regression item;
- link the affected gate;
- block release if the regression violates a release requirement.

## Evidence

Follow `governance/core/EVIDENCE_STANDARD.md`.

Do not fabricate command output, tests, HTTP results, screenshots, CI results, or approvals.
