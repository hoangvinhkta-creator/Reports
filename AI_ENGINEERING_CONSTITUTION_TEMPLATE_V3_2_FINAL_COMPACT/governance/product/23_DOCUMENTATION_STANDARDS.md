# 23 — Documentation Standards

## Objective
Keep documentation useful as a real source of truth rather than stale decoration.

## Required Documentation Categories
Depending on project size:
- README,
- architecture,
- routes,
- data model,
- permissions/security,
- API contracts,
- environment setup,
- deployment,
- backup/restore,
- incident runbook,
- ADRs.

## Rules

### 1. Documentation changes with behavior
If code intentionally changes:
- schema,
- route,
- API,
- permission,
- architecture,
- deployment process,

update corresponding documentation in the same change.

### 2. Prefer current truth
Remove or mark obsolete instructions.

### 3. Examples must be safe
Never place real secrets, customer data, or production credentials in documentation.

### 4. Commands
Operational commands should state:
- environment,
- prerequisites,
- destructive risk where relevant.

### 5. Source-of-truth ownership
Avoid duplicating authoritative definitions in many files.

Reference the authoritative document instead.

### 6. ADRs
Use Architecture Decision Records for durable architectural choices.

### 7. Runbooks
Operational procedures should be executable by someone other than the original author.

## Documentation Quality Test
A new developer/AI agent should be able to determine:
- how to run the project,
- how it is structured,
- where data lives,
- how permissions work,
- how to test,
- how to deploy safely,
- what not to change casually.
