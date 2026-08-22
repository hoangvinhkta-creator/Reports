# 09 — Testing Rules

## Objective
A feature is complete only when relevant behavior and failure modes have been verified.

## Minimum Verification Where Applicable

- build
- lint
- type check
- unit tests
- integration tests
- route behavior
- authentication
- authorization
- CRUD behavior
- error handling
- regression checks

## Feature Test Cases
For important features consider:

### Happy path
Valid authorized user completes normal workflow.

### Invalid input
Incorrect or incomplete input is rejected safely.

### Unauthorized
Authenticated user without permission cannot perform the action.

### Unauthenticated
Protected operations reject unauthenticated access.

### Missing data
Missing/deleted related records do not crash the application.

### Duplicate/retry
Repeated request does not produce dangerous duplicate side effects.

### Backend failure
Failure produces a controlled error state.

### Boundary values
Check important:
- zero,
- max/min,
- empty arrays,
- large values,
- date boundaries.

## Security Testing
Test access by modifying:
- URL IDs,
- request body IDs,
- owner IDs,
- roles,
- hidden fields.

Do not assume UI restrictions are sufficient.

## Regression
Verify adjacent existing behavior likely affected by the change.

## Completion Rule
Do not report “done” if:
- build is broken,
- tests fail,
- known permission issue remains,
- schema migration is incomplete,
- critical path was not verified.

If a check cannot be executed, clearly report:
- what was not tested,
- why,
- resulting risk.
