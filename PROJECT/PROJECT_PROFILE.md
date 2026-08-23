# PROJECT PROFILE

Status:
INITIALIZED — S000 completed 2026-08-22

Selected Profile:
PRODUCT

Project:
Tín Phát — Business Report Automation Tool

## Profile Inputs

Team Size:
1 developer (AI-assisted) + 1 business owner acting as reviewer/approver.
Report consumers: the whole sales team (~6–10 people) plus management.

Production Data:
YES. The tool ingests the real accounting/ERP sales book and produces the
numbers that drive employee KPI, commission and payroll. Wrong output has
direct financial consequences for real people.

Personal/Customer Data:
YES. The raw sales book carries customer full name, mobile phone number and
delivery address on every line (11,765 lines in the current sample), plus
device IMEI/serial. Employee names and salary-related figures are also present.
`governance/product/17_DATA_GOVERNANCE_PRIVACY.md` therefore applies and is
mandatory, not optional.

Authentication:
REQUIRED. The tool is multi-user and every override must record `ChangedBy`
for the audit trail mandated by spec section 19. Roles: viewer / editor / admin.

External Users:
NO. Internal company use only. No customer-facing surface.

CI/CD:
NOT YET. No pipeline exists. Conditional — to be introduced if and when the
tool is deployed to a shared internal server.

Staging:
NOT YET. Local development environment only at MVP stage.

Backup:
REQUIRED once the database exists (Phase 2). The database becomes the system
of record for manual overrides that exist nowhere else — the raw ERP export can
be re-downloaded, but a month of manual KPI adjustments cannot be reconstructed.

Monitoring:
BASIC. Structured application logging plus the business-level audit log.
Full observability tooling is out of scope for the MVP.

Uncertainty Level:
MEDIUM.
- Business rules are well evidenced from the sample workbooks (LOW uncertainty).
- The ADS classification rule has ZERO supporting data in the current files —
  the keyword "ADS" appears 0 times across both workbooks — and depends on a
  future change in data-entry behaviour (HIGH uncertainty).
- Purchase price is absent from the raw file and depends on an external price
  tool that does not exist yet (MEDIUM uncertainty).

## Governance Depth

Mandatory Governance:
- CLAUDE.md
- governance/core/00_SESSION_ORCHESTRATION.md
- governance/core/01_PROJECT_ARCHITECTURE_RULES.md
- governance/core/02_ROUTING_RULES.md
- governance/core/03_DATA_MODEL_RULES.md
- governance/core/04_SECURITY_RULES.md
- governance/core/05_BUSINESS_LOGIC_RULES.md
- governance/core/06_DATABASE_API_RULES.md
- governance/core/07_CODING_RULES.md
- governance/core/08_CHANGE_MANAGEMENT_RULES.md
- governance/core/09_TESTING_RULES.md
- governance/core/10_AI_AGENT_EXECUTION_PROTOCOL.md
- governance/core/11_FORBIDDEN_ACTIONS.md
- governance/core/RULE_PRECEDENCE.md
- governance/core/EVIDENCE_STANDARD.md
- governance/core/TASK_MODE_STANDARD.md
- governance/core/TASK_READY_GATE_STANDARD.md
- governance/core/TASK_COMPLETION_GATE_STANDARD.md
- governance/core/PHASE_RELEASE_GATE_STANDARD.md
- governance/product/12_PRODUCT_REQUIREMENTS_RULES.md
- governance/product/13_ENVIRONMENT_CONFIGURATION.md
- governance/product/15_LOGGING_AUDIT_OBSERVABILITY.md
- governance/product/16_BACKUP_DISASTER_RECOVERY.md
- governance/product/17_DATA_GOVERNANCE_PRIVACY.md

Conditional Governance:
- governance/product/14_CI_CD_RELEASE_RULES.md — applies from the first shared
  deployment onward; NOT_APPLICABLE while development is local-only.
- governance/product/19_DEPENDENCY_MANAGEMENT.md — applies from Phase 2, when
  the dependency surface grows beyond the analysis toolchain.
- governance/product/20_API_VERSIONING_COMPATIBILITY.md — applies from Phase 2,
  when the HTTP API exists.
- governance/product/21_ACCESSIBILITY_UI_RULES.md — applies from Phase 3.
- governance/product/23_DOCUMENTATION_STANDARDS.md — applies from Phase 1.

Not Applicable:
- governance/product/18_INCIDENT_RESPONSE.md — no production deployment and no
  external users yet. Re-evaluate at the Phase 3 release gate.
- governance/product/22_CODE_OWNERSHIP_REVIEW.md — single-developer project;
  CODEOWNERS has no meaning with one contributor. Re-evaluate if the team grows.

## Justification

SOLO_LITE was rejected. This is not a low-risk single-file utility: it holds
customer personal data, it computes the figures behind employee pay, it needs
multi-user persistence with an audit trail, and it replaces a spreadsheet the
business already depends on.

TEAM_PRODUCTION was rejected as premature. There is no team, no CI, no staging
and no external user. Imposing CODEOWNERS, incident response and release
engineering now would be ceremony without a corresponding risk.

PRODUCT is the honest fit: full product/business/data governance, with the
delivery-and-operations layer promoted from Conditional to Mandatory at the
Phase 3 release gate rather than pretended into existence at Phase 0.

## Evidence Tier Rule for This Project

Per `governance/core/EVIDENCE_STANDARD.md` with Risk 4 on the calculation
engine: E1 is mandatory for every executable REQUIRED check, and the numeric
correctness checks in Phase 1 SHOULD reach E2. No CI and no second human
reviewer exist, so E2 is produced through the Solo Independent Review
Procedure and persisted under `docs/reviews/`.
