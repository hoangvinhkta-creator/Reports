# 13 — Environment & Configuration Management

## Objective
Prevent accidental mixing of development, staging, and production systems.

## Required Environments
At minimum, production must be logically separated from development.

Recommended:
- local
- development
- staging
- production

## Rules

### 1. Production resources must be identifiable
Production databases, projects, buckets, queues, API credentials, and domains must not be ambiguous.

### 2. Development must not casually use production data
Development/testing should use:
- synthetic data,
- test data,
- sanitized data.

Do not copy real production customer data into development without an explicit, controlled process.

### 3. Secrets are environment-specific
DEV credentials must not equal PROD credentials where separation is supported.

### 4. Do not commit secrets
Files such as `.env` containing real secrets must not be committed.

A safe `.env.example` may be committed with placeholders only.

### 5. Centralize configuration
Do not scatter:
- API base URLs,
- environment names,
- feature switches,
- important limits

throughout implementation.

### 6. Fail safely on missing critical configuration
Do not silently fall back to production or an unsafe default.

### 7. Environment checks
Production-only operations should explicitly validate the active environment where appropriate.

### 8. Feature flags
If feature flags are used:
- define ownership,
- define default behavior,
- remove stale flags,
- do not use flags as permanent architecture.

### 9. Firebase / cloud projects
When applicable, prefer separate projects/resources for:
- development/staging,
- production.

### 10. Configuration documentation
Document:
- required environment variables,
- purpose,
- whether client/server,
- example format,
- secret/non-secret classification.

## Deployment Safety Check
Before production deployment verify:
- target project/account,
- environment variables,
- database target,
- storage target,
- callback URLs,
- API base URL,
- feature flags,
- migrations.
