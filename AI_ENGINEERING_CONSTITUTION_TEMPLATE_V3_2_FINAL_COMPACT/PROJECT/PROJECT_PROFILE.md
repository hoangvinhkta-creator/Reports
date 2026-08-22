# PROJECT PROFILE

Status:
INITIALIZED

Selected Profile:
PRODUCT

Profile History:
- S001 (2026-08-22) — AUDIT selected as an S000 bootstrap. See DEC-001.
- S002 (2026-08-22) — transitioned AUDIT → PRODUCT on owner instruction. See DEC-005.

Transition Basis:
`governance/reference/START_HERE_USAGE_GUIDE_V3_2.md` PHẦN 7 — the audit is
complete, findings exist with severity and evidence, and a remediation roadmap
has been produced. AUDIT is read-only by default and cannot execute
remediation; PRODUCT can.

Team Size:
1 (solo owner/operator)

Production Data:
NONE — repository contains no application, no database, no runtime.

Personal/Customer Data:
NONE — no personal or customer data is stored or processed.

Authentication:
NOT_APPLICABLE — no authentication surface exists.

External Users:
NONE — no deployed system, no external consumers.

CI/CD:
NONE today. Under PRODUCT, `governance/product/14_CI_CD_RELEASE_RULES.md` is
not mandatory, but CI is now judged practical and is scheduled as REM-T07 in
PHASE-01 — it is the project's only viable E2 evidence source (resolves
RSK-004). See DEC-007.

Staging:
NONE. Not required at PRODUCT for a repository with no deployable artifact.

Backup:
Git remote `origin` → `https://github.com/hoangvinhkta-creator/Reports`.
No additional backup mechanism. Recorded as GAP-01 below.

Monitoring:
NONE — nothing running to monitor.

Uncertainty Level:
LOW for the current surface (governance package integrity, deployment layout).
HIGH for the eventual application scope, which does not yet exist.

## Mandatory Governance — PROFILE B (PRODUCT)

PRODUCT = SOLO_LITE + product/business/data governance, per
`governance/core/PROJECT_PROFILE_STANDARD.md`.

### CORE (inherited)
- `CLAUDE.md`
- `governance/core/00_SESSION_ORCHESTRATION.md`
- `governance/core/07_CODING_RULES.md`
- `governance/core/08_CHANGE_MANAGEMENT_RULES.md`
- `governance/core/09_TESTING_RULES.md`
- `governance/core/10_AI_AGENT_EXECUTION_PROTOCOL.md`
- `governance/core/11_FORBIDDEN_ACTIONS.md`
- `governance/core/RULE_PRECEDENCE.md`
- `governance/core/EVIDENCE_STANDARD.md`
- `governance/core/TASK_MODE_STANDARD.md`
- `governance/core/TASK_READY_GATE_STANDARD.md`
- `governance/core/TASK_COMPLETION_GATE_STANDARD.md`

### SOLO_LITE (inherited)
- `governance/core/04_SECURITY_RULES.md`

### PRODUCT (added at this transition)
- `governance/core/01_PROJECT_ARCHITECTURE_RULES.md`
- `governance/core/02_ROUTING_RULES.md`
- `governance/core/03_DATA_MODEL_RULES.md`
- `governance/core/05_BUSINESS_LOGIC_RULES.md`
- `governance/core/06_DATABASE_API_RULES.md`
- `governance/product/12_PRODUCT_REQUIREMENTS_RULES.md`
- `governance/product/13_ENVIRONMENT_CONFIGURATION.md`
- `governance/product/15_LOGGING_AUDIT_OBSERVABILITY.md`
- `governance/product/16_BACKUP_DISASTER_RECOVERY.md`
- `governance/product/17_DATA_GOVERNANCE_PRIVACY.md`
- `governance/core/PHASE_RELEASE_GATE_STANDARD.md`

## Profile Compliance Matrix

Produced per `governance/reference/START_HERE_USAGE_GUIDE_V3_2.md` PHẦN 19.

"Mandatory by profile" and "has a subject today" are different questions. A
domain with no surface is recorded as DORMANT — mandatory, but with nothing to
govern yet. DORMANT is not a waiver; it must be re-checked when application
code lands.

| Governance Domain | Profile Requirement | Applicable Now | Covered By Task | Status | Gap |
|---|---|---|---|---|---|
| 00 Session Orchestration | MANDATORY | Yes | S001, S002 | ACTIVE | — |
| 01 Architecture | MANDATORY | Yes (repo layout) | REM-T02, ADR-001 | ACTIVE | — |
| 02 Routing | MANDATORY | No — no app routing | — | DORMANT | — |
| 03 Data Model | MANDATORY | No — no data store | — | DORMANT | — |
| 04 Security | MANDATORY | Partially — no secrets, no auth surface | — | DORMANT | — |
| 05 Business Logic | MANDATORY | No — no business logic | — | DORMANT | — |
| 06 Database / API | MANDATORY | No — no database or API | — | DORMANT | — |
| 07 Coding Rules | MANDATORY | Yes — validator scripts | REM-T03 | ACTIVE | — |
| 08 Change Management | MANDATORY | Yes | All REM-T* | ACTIVE | — |
| 09 Testing | MANDATORY | Yes — validator regression fixtures | REM-T03 | ACTIVE | — |
| 10 AI Agent Execution | MANDATORY | Yes | All sessions | ACTIVE | — |
| 11 Forbidden Actions | MANDATORY | Yes | All sessions | ACTIVE | — |
| 12 Product Requirements | MANDATORY | No — no product surface | — | DORMANT | — |
| 13 Environment Config | MANDATORY | No — no environments | — | DORMANT | — |
| 15 Logging / Observability | MANDATORY | No — nothing running | — | DORMANT | — |
| 16 Backup / DR | MANDATORY | Yes — git remote is the only copy | — | **GAP** | GAP-01 |
| 17 Data Governance / Privacy | MANDATORY | No — no personal data | — | DORMANT | — |
| Phase / Release Gate | MANDATORY | Yes | Phase Gates 01–03 | ACTIVE | — |
| Evidence Standard | MANDATORY | Yes | All gates | ACTIVE | E2 path missing until REM-T07 |
| 14 CI/CD | NOT required at PRODUCT | Yes — judged practical | REM-T07 | SCHEDULED | — |

### GAP-01 — Backup / Disaster Recovery

Requirement:
`governance/product/16_BACKUP_DISASTER_RECOVERY.md` is mandatory at PRODUCT.

Current state:
The GitHub remote is the only copy of this repository. There is no second
backup and no documented recovery procedure.

Assessment:
Impact is bounded — the content is versioned text with no production data, and
every contributor clone is a full copy. It is nonetheless a real gap against a
mandatory domain and is recorded rather than waived.

Decision:
Not scheduled into PHASE-01. Re-assess at Phase Gate 03. Do not close this gap
by deleting the row.

## Conditional Governance
- `governance/product/14_CI_CD_RELEASE_RULES.md` — not mandatory at PRODUCT,
  but adopted voluntarily via REM-T07 because CI is the project's E2 path.
  Read this file when implementing REM-T07.
- `governance/product/23_DOCUMENTATION_STANDARDS.md` — mandatory only at
  TEAM_PRODUCTION. Applied advisorily, since this repository's product *is*
  documentation. Relevant to REM-T05 and REM-T06.

## Not Applicable
- `governance/product/18_INCIDENT_RESPONSE.md` — no production service to have
  an incident.
- `governance/product/19_DEPENDENCY_MANAGEMENT.md` — zero third-party
  dependencies; the five validators use only the Python standard library.
- `governance/product/20_API_VERSIONING_COMPATIBILITY.md` — no API.
- `governance/product/21_ACCESSIBILITY_UI_RULES.md` — no UI.
- `governance/product/22_CODE_OWNERSHIP_REVIEW.md` — single owner, no review
  rota to define.

Each NOT_APPLICABLE is recorded with its reason, as
`governance/core/PROJECT_PROFILE_STANDARD.md` requires. Re-evaluate all of them
— and every DORMANT row above — when application code first lands.

## Agent Capability Tiers

Mapped per `governance/core/AGENT_CAPABILITY_MATRIX.md`. See DEC-006.

- **Tier A — Lightweight**: documentation edits, bounded path fixes. → REM-T04, REM-T06
- **Tier B — Implementation**: validator scripts, CI workflow, bounded refactors. → REM-T03, REM-T05, REM-T07
- **Tier C — Advanced Reasoning**: repository-wide moves, gate design, root-cause analysis. → REM-T02
- **Tier D — Design / Creative**: NOT_APPLICABLE. This project has no UI, visual
  design or content-presentation work. Re-define if an application with a user
  interface is added.

## Justification

PRODUCT was selected on owner instruction after S001 completed the audit.

It fits the standard's stated use ("multi-module internal applications",
"business tools") only loosely today, because there is no application yet.
The decisive factors are procedural rather than product-shaped:

1. AUDIT is read-only by default and cannot execute the remediation roadmap.
   Remaining under AUDIT would block all seven REM-T* tasks indefinitely.
2. SOLO_LITE would be the lighter alternative, but it drops
   `PHASE_RELEASE_GATE_STANDARD` and the data/architecture rule groups. The
   remediation set includes a repository-wide move with Blast Radius 5/5
   (REM-T02) that warrants phase-level verification, so the heavier profile is
   the safer choice.
3. TEAM_PRODUCTION would add CODEOWNERS, incident response and API versioning
   ceremony that a single-owner documentation repository cannot meaningfully
   satisfy.

Recorded honestly: several PRODUCT domains are DORMANT because the repository
has no application surface. That is a known, documented consequence of the
choice, not an oversight.

## Release Rule

`governance/core/PHASE_RELEASE_GATE_STANDARD.md` applies.
Task DONE ≠ Phase DONE. Phase DONE ≠ Release Ready.

Production code changes are now permitted — the AUDIT read-only restriction is
lifted. Scope Lock still applies to every task.
