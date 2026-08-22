# 14 — CI/CD & Release Rules

## Objective
Make production changes repeatable, testable, reviewable, and reversible.

## Recommended Delivery Flow

feature branch
→ pull request
→ automated checks
→ review
→ preview/staging
→ approval
→ production
→ post-deploy verification

## Mandatory Rules

### 1. Do not treat local success as release readiness
Production deployment requires relevant verification.

### 2. Automated checks
Where supported, CI should run:
- dependency install using lockfile,
- lint,
- typecheck,
- unit/integration tests,
- production build,
- security/dependency checks where configured.

### 3. Protect production branch
Avoid uncontrolled direct commits to the production branch.

### 4. Production deployment
High-risk changes should not be deployed directly by an AI agent without the project's required approval process.

### 5. Database migrations
Migrations must be coordinated with deployment order.

Prefer backward-compatible deployment sequences.

### 6. Release notes
Material releases should document:
- features,
- fixes,
- migrations,
- security changes,
- known limitations.

### 7. Rollback
Before high-risk release identify:
- code rollback method,
- database compatibility,
- irreversible operations,
- feature flag fallback if available.

### 8. Post-deployment verification
Verify critical paths after deployment.

Examples:
- login,
- main dashboard,
- critical CRUD,
- permissions,
- key integrations.

### 9. Failed deployment
Do not repeatedly patch production blindly.

Stop, inspect the failing stage, and determine whether to:
- rollback,
- fix forward,
- disable affected feature.

## Release Risk Levels

### Low
UI/text change without data/security impact.

### Medium
Normal feature with bounded data/API impact.

### High
Includes:
- auth,
- authorization,
- billing,
- pricing,
- bulk mutation,
- schema migration,
- deletion,
- production infrastructure.

High-risk changes require stronger review and rollback preparation.
