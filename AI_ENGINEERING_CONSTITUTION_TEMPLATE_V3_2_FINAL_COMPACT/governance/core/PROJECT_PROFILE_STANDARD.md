# Project Profile Standard

## Purpose
Select governance depth proportional to project size, business risk, team size, production exposure, and uncertainty.

Profile MUST be selected during S000 before detailed roadmap finalization.

## Inheritance Model

### CORE
Core governance:
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

### PROFILE A — SOLO_LITE
SOLO_LITE = CORE + essential security.

Add:
- `governance/core/04_SECURITY_RULES.md`

Use for:
- prototype,
- single-file tool,
- small internal utility,
- low-risk automation,
- project without sensitive production data.

Ceremony:
- Micro Tasks allowed.
- ADR not mandatory for small decisions.
- CI/CD, CODEOWNERS, DR may be NOT_APPLICABLE when profile explicitly records why.

### PROFILE B — PRODUCT
PRODUCT = SOLO_LITE + product/business/data governance.

Add:
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

Use for:
- CRM,
- business tools,
- Firebase/Supabase apps,
- multi-module internal applications,
- systems containing real customer/business data.

### PROFILE C — TEAM_PRODUCTION
TEAM_PRODUCTION = PRODUCT + formal delivery/operations governance.

Add:
- `governance/product/14_CI_CD_RELEASE_RULES.md`
- `governance/product/18_INCIDENT_RESPONSE.md`
- `governance/product/19_DEPENDENCY_MANAGEMENT.md`
- `governance/product/20_API_VERSIONING_COMPATIBILITY.md`
- `governance/product/21_ACCESSIBILITY_UI_RULES.md`
- `governance/product/22_CODE_OWNERSHIP_REVIEW.md`
- `governance/product/23_DOCUMENTATION_STANDARDS.md`
- `OPTIONAL_ENFORCEMENT_LAYER.md` with CI integration where practical.

Use for:
- customer-facing SaaS,
- multiple developers,
- formal release flow,
- high-value/regulated production environments.

### PROFILE D — AUDIT
AUDIT is READ-ONLY by default.

Required audit rules:
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

Primary outputs:
- Discovery Baseline
- Findings
- Severity
- Evidence
- Remediation Roadmap

No production code changes until AUDIT is explicitly closed and remediation begins under another profile, commonly PRODUCT.

## Profile Selection Inputs

Assess:
- Team size
- Project maturity
- Production data
- Personal/customer data
- Authentication
- Financial/pricing sensitivity
- External users
- Compliance/legal constraints
- CI/CD
- Staging
- Backup
- Monitoring
- Uncertainty
- Expected lifespan

## Runtime Record

Write:

`PROJECT/PROJECT_PROFILE.md`

Record:
- selected profile,
- mandatory rule groups,
- conditional groups,
- not-applicable groups,
- justification.

Do not re-decide applicability from scratch every session.
