# 06 — Database & API Rules

## Objective
Prevent uncontrolled database access and create explicit boundaries between application logic and persistence.

## Required Flow
Prefer:

UI
→ Use Case / Service
→ Repository / API
→ Database

## Rules

### 1. UI components should not directly access the database
Avoid database SDK calls scattered across pages/components.

### 2. Centralize persistence
Use repositories/services/API clients.

### 3. Validate all external input
Validate:
- types,
- required fields,
- formats,
- allowed ranges,
- enum values,
- ownership,
- permission.

### 4. Server authority
Sensitive calculations and authorization decisions should use trusted server-side information.

### 5. API contracts must be explicit
Define:
- request,
- response,
- errors,
- authorization,
- validation,
- side effects.

### 6. Do not expose internal implementation unnecessarily
Frontend should not depend tightly on raw storage structure.

### 7. Idempotency
For operations likely to be retried, evaluate whether repeated requests could:
- create duplicates,
- charge twice,
- send twice,
- create duplicate tasks.

Use idempotency controls where appropriate.

### 8. Transactions
Use transactional behavior when multiple writes must succeed or fail together.

### 9. Pagination
Large datasets should not be loaded entirely without reason.

### 10. Query access boundaries
Queries must respect permission filters and ownership rules.

### 11. Error handling
Differentiate:
- validation errors,
- authorization errors,
- not found,
- conflicts,
- infrastructure failures.

### 12. Destructive operations
Delete operations should consider:
- dependencies,
- soft delete,
- audit trail,
- restoration,
- permission.

## API Contract Template

Endpoint / Function:
...

Purpose:
...

Authentication:
...

Authorization:
...

Input:
...

Validation:
...

Output:
...

Errors:
...

Side effects:
...

Idempotency:
...
