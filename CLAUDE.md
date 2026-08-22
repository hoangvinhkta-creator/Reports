# CLAUDE.md — Project Governance Entry Point

## Compact Directory Layout

This package stores static governance under `governance/` to keep repository root thin.

- `CLAUDE.md` = governance entry point at root.
- `PROJECT/` = current project state.
- `docs/` = runtime tasks, sessions, reviews, ADRs.
- `governance/` = static rules, templates, validators, references.

Do not move governance files back to root.
The mandatory read order and all original governance mechanisms remain unchanged; only canonical paths differ.


## Core Principle
Do not code first and organize later.

The repository is the shared memory:
- Rules → governance files
- Current state → `PROJECT/PROJECT_PROGRESS.md`
- Project profile → `PROJECT/PROJECT_PROFILE.md`
- Tactical decisions → `PROJECT/PROJECT_DECISIONS.md`
- Architecture decisions → `docs/adr/`
- Task definitions → `docs/tasks/`
- Session history/handoffs → `docs/sessions/`
- Reusable forms → `templates/`

## S000 — First Actions

S000 has ONE canonical procedure.

1. Read `governance/core/PROJECT_PROFILE_STANDARD.md`.
2. Read `governance/core/RULE_PRECEDENCE.md`.
3. Read `governance/core/TASK_MODE_STANDARD.md`.
4. Then execute the full ordered S000 procedure in `governance/core/00_SESSION_ORCHESTRATION.md`.

Do not maintain a second S000 checklist in this file.

## Project Profiles

Use `governance/core/PROJECT_PROFILE_STANDARD.md`.

Profiles:
- SOLO_LITE
- PRODUCT
- TEAM_PRODUCTION
- AUDIT

Profile selection determines governance depth; it does not dictate a specific technical stack.

## Rule Conflicts

Use `governance/core/RULE_PRECEDENCE.md`.

Do not resolve material rule conflicts silently.

## Every Implementation Session

1. Read `PROJECT/PROJECT_PROGRESS.md`.
2. Read `PROJECT/PROJECT_PROFILE.md`.
3. Identify current task and Task Mode.
4. For MAJOR tasks, read the task file under `docs/tasks/`.
5. Verify the appropriate Ready Gate.
6. Load Scope Lock.
7. Load the finalized/frozen Completion Gate.
8. Read relevant governance files.
9. Begin implementation only when READY.

## Task Modes

Use `governance/core/TASK_MODE_STANDARD.md`.

- MICRO — low-risk bounded work with compact checklist.
- MAJOR — full task file + dedicated session + gates + handoff.
- SPIKE / EXPLORATORY — reduces uncertainty before implementation.

## Task Lifecycle

NOT_PLANNED
→ PLANNED
→ READY
→ IN_PROGRESS
→ IMPLEMENTED
→ VERIFYING
→ DONE

Alternative states:
BLOCKED / DEFERRED / CANCELLED

## Evidence

Use `governance/core/EVIDENCE_STANDARD.md`.

Never invent evidence.

For executable checks:
- Risk 3 → E1 required for REQUIRED checks.
- Risk 4–5 → E1 required; security/data-critical checks should seek E2.

If not executed:
Status = NOT_TESTED.

## Completion

Use `governance/core/TASK_COMPLETION_GATE_STANDARD.md`.

CODE COMPLETE ≠ TASK COMPLETE.

A task is DONE only when:
- all REQUIRED checks PASS,
- required evidence levels are satisfied,
- Exit Criteria are satisfied.

## Integration

Use `governance/core/PHASE_RELEASE_GATE_STANDARD.md`.

Task DONE ≠ Phase DONE.
Phase DONE ≠ Release Ready.

## Escalation

Use `governance/core/ESCALATION_PROTOCOL.md`.

Do not repeatedly patch a failing implementation.

## Progress Questions

If the user asks:
- current progress,
- current step,
- remaining work,
- next step,
- checklist,

READ `PROJECT/PROJECT_PROGRESS.md` FIRST.

Do not answer from conversational memory.

## Scope Expansion

Do not silently edit outside a task's Scope Lock.

If required:

SCOPE EXPANSION REQUIRED

Then reassess impact before continuing.

## Conflict Rule

If documentation, implementation, data, security, or current behavior conflict:

CONFLICT DETECTED

Documentation:
...

Implementation:
...

Risk:
...

Recommended resolution:
...

Do not guess silently.

## Relevant Governance Files

### Session / Planning
- `governance/core/00_SESSION_ORCHESTRATION.md`
- `governance/core/PROJECT_PROFILE_STANDARD.md`
- `governance/core/TASK_MODE_STANDARD.md`
- `governance/core/TASK_READY_GATE_STANDARD.md`
- `governance/core/TASK_COMPLETION_GATE_STANDARD.md`
- `governance/core/PHASE_RELEASE_GATE_STANDARD.md`
- `governance/core/AGENT_CAPABILITY_MATRIX.md`
- `governance/core/ESCALATION_PROTOCOL.md`
- `governance/core/RULE_PRECEDENCE.md`
- `governance/core/EVIDENCE_STANDARD.md`

### Engineering
- `governance/core/01_PROJECT_ARCHITECTURE_RULES.md`
- `governance/core/02_ROUTING_RULES.md`
- `governance/core/03_DATA_MODEL_RULES.md`
- `governance/core/04_SECURITY_RULES.md`
- `governance/core/05_BUSINESS_LOGIC_RULES.md`
- `governance/core/06_DATABASE_API_RULES.md`
- `governance/core/07_CODING_RULES.md`
- `governance/core/08_CHANGE_MANAGEMENT_RULES.md`
- `governance/core/09_TESTING_RULES.md`
- `governance/core/10_AI_AGENT_EXECUTION_PROTOCOL.md`
- `governance/core/11_FORBIDDEN_ACTIONS.md`

### Product / Operations
- `governance/product/12_PRODUCT_REQUIREMENTS_RULES.md`
- `governance/product/13_ENVIRONMENT_CONFIGURATION.md`
- `governance/product/14_CI_CD_RELEASE_RULES.md`
- `governance/product/15_LOGGING_AUDIT_OBSERVABILITY.md`
- `governance/product/16_BACKUP_DISASTER_RECOVERY.md`
- `governance/product/17_DATA_GOVERNANCE_PRIVACY.md`
- `governance/product/18_INCIDENT_RESPONSE.md`
- `governance/product/19_DEPENDENCY_MANAGEMENT.md`
- `governance/product/20_API_VERSIONING_COMPATIBILITY.md`
- `governance/product/21_ACCESSIBILITY_UI_RULES.md`
- `governance/product/22_CODE_OWNERSHIP_REVIEW.md`
- `governance/product/23_DOCUMENTATION_STANDARDS.md`

### Audit / Enforcement
- `governance/audit/DISCOVERY_BASELINE_TEMPLATE.md`
- `governance/audit/AUDIT_FINDINGS_TEMPLATE.md`
- `OPTIONAL_ENFORCEMENT_LAYER.md`

## Final Rule

The agent must prove completion through artifacts and evidence, not through narrative confidence.