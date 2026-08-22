# 17 — Data Governance & Privacy Rules

## Objective
Define how business and personal data is collected, accessed, retained, exported, shared, and removed.

## Data Inventory
For important datasets document:
- owner,
- purpose,
- sensitivity,
- storage location,
- permitted users,
- retention,
- deletion method,
- export behavior.

## Data Minimization
Collect and retain only data needed for a defined business purpose.

## Purpose Limitation
Do not reuse sensitive/customer data for unrelated purposes without an appropriate decision/process.

## Access
Access should follow:
- role,
- business need,
- least privilege.

## Production Data in Development
Default rule:

DO NOT use unsanitized production customer data in development or testing.

Use:
- fake data,
- masked data,
- anonymized/sanitized subsets.

## Export Controls
Bulk export may expose more risk than normal viewing.

Define:
- allowed roles,
- fields permitted,
- audit requirements,
- rate/volume controls where appropriate.

## Data Retention
Define:
- how long records are retained,
- what happens to inactive data,
- legal/business retention constraints,
- backup retention implications.

## Deletion
Clarify:
- hard delete,
- soft delete,
- anonymization,
- archival.

Do not implement deletion without understanding related records and compliance/business requirements.

## Employee Offboarding
When a user leaves:
- revoke account access,
- revoke active sessions/tokens where supported,
- transfer ownership if needed,
- review elevated privileges.

## Third Parties
Before sending data to external services consider:
- fields transmitted,
- purpose,
- credentials,
- retention,
- vendor risk,
- whether sensitive fields are necessary.

## Privacy by Design
New features should ask:
- Do we need this field?
- Does this user need this field?
- Does the client need to receive it?
- How long should it exist?
