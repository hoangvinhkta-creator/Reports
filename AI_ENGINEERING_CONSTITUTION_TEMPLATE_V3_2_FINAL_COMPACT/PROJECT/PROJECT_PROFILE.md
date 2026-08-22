# PROJECT PROFILE

Status:
INITIALIZED

Selected Profile:
AUDIT

Selected In:
S001 — Discovery & Baseline (2026-08-22), as an S000 bootstrap.
See DEC-001 in `PROJECT/PROJECT_DECISIONS.md` and FIND-002 in
`docs/audit/S001_AUDIT_FINDINGS.md`.

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
NONE — no `.github/` workflows. See FIND-008; the decision is deferred to
REM-T07 pending the post-audit profile transition.

Staging:
NONE.

Backup:
Git remote `origin` → `https://github.com/hoangvinhkta-creator/Reports`.
No additional backup mechanism.

Monitoring:
NONE — nothing running to monitor.

Uncertainty Level:
LOW for the audited surface (governance package integrity, deployment layout).
HIGH for the eventual application scope, which does not yet exist.

Mandatory Governance:
Per `governance/core/PROJECT_PROFILE_STANDARD.md`, PROFILE D — AUDIT requires:
- `governance/core/01_PROJECT_ARCHITECTURE_RULES.md`
- `governance/core/03_DATA_MODEL_RULES.md`
- `governance/core/04_SECURITY_RULES.md`
- `governance/core/06_DATABASE_API_RULES.md`
- `governance/core/11_FORBIDDEN_ACTIONS.md`
- `governance/product/17_DATA_GOVERNANCE_PRIVACY.md`
- `governance/core/RULE_PRECEDENCE.md`
- `governance/core/EVIDENCE_STANDARD.md`
- `governance/audit/DISCOVERY_BASELINE_TEMPLATE.md`
- `governance/audit/AUDIT_FINDINGS_TEMPLATE.md`

Also loaded in S001 because the audited subject is the governance system itself:
- `CLAUDE.md`
- `governance/core/00_SESSION_ORCHESTRATION.md`
- `governance/core/PROJECT_PROFILE_STANDARD.md`
- `governance/core/TASK_MODE_STANDARD.md`

Conditional Governance:
- `governance/product/14_CI_CD_RELEASE_RULES.md` — becomes applicable only if
  the post-audit profile is TEAM_PRODUCTION.
- `governance/product/23_DOCUMENTATION_STANDARDS.md` — applicable now in spirit
  (this repository's product *is* documentation), formally required only at
  TEAM_PRODUCTION.
- `governance/core/PHASE_RELEASE_GATE_STANDARD.md` — applies from PRODUCT
  upward; used advisorily for the Phase Gates in the remediation roadmap.

Not Applicable:
- `governance/core/02_ROUTING_RULES.md` — no application routing exists.
- `governance/core/05_BUSINESS_LOGIC_RULES.md` — no business logic implemented.
- `governance/product/12_PRODUCT_REQUIREMENTS_RULES.md` — no product surface.
- `governance/product/13_ENVIRONMENT_CONFIGURATION.md` — no environments.
- `governance/product/15_LOGGING_AUDIT_OBSERVABILITY.md` — nothing to observe.
- `governance/product/16_BACKUP_DISASTER_RECOVERY.md` — beyond the git remote,
  no data at risk.
- `governance/product/18_INCIDENT_RESPONSE.md` — no production service.
- `governance/product/19_DEPENDENCY_MANAGEMENT.md` — zero third-party
  dependencies; validators use the Python standard library only.
- `governance/product/20_API_VERSIONING_COMPATIBILITY.md` — no API.
- `governance/product/21_ACCESSIBILITY_UI_RULES.md` — no UI.
- `governance/product/22_CODE_OWNERSHIP_REVIEW.md` — single owner.

Each NOT_APPLICABLE above is recorded with its reason, as
`governance/core/PROJECT_PROFILE_STANDARD.md` requires. Re-evaluate all of them
at the AUDIT → PRODUCT transition; do not carry them forward unexamined.

Justification:
AUDIT was selected because the repository is a pre-existing artifact of unknown
integrity that had never been assessed, and the governing standard makes AUDIT
read-only by default with Discovery Baseline, Findings, Severity, Evidence and
Remediation Roadmap as its primary outputs — exactly the S001 deliverables.
`governance/reference/START_HERE_USAGE_GUIDE_V3_2.md` PHẦN 5 further directs that an existing system
should begin under AUDIT.

Profile Transition:
AUDIT remains in force until the remediation roadmap is finalized and the
transition is explicitly confirmed, per `governance/reference/START_HERE_USAGE_GUIDE_V3_2.md`
PHẦN 7. No production code changes are permitted under AUDIT.
