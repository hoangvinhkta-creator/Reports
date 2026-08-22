# 12 — Product Requirements Rules

## Objective
Ensure the team and AI agent understand what must be built, why it matters, who may use it, and what “done” means before implementation begins.

## Core Rule
Do not implement a non-trivial feature from an informal sentence alone when important business behavior remains undefined.

A feature specification should be created or confirmed before code changes.

## Minimum Feature Specification

### 1. Problem
What user/business problem is being solved?

### 2. Business Goal
What outcome should improve?

Examples:
- reduce manual follow-up,
- reduce pricing errors,
- increase response speed,
- prevent unauthorized data exposure.

### 3. Users / Roles
Who uses the feature?

Examples:
- sales,
- sales_manager,
- admin,
- customer_service.

### 4. User Flow
Describe the expected main workflow.

### 5. Functional Requirements
Clearly state required system behavior.

### 6. Acceptance Criteria
Use testable statements.

Example:
- Sales Manager can export assigned customer data.
- Sales role cannot export the full customer database.
- Every export creates an audit event.

### 7. Out of Scope
Explicitly state what this task does NOT include.

### 8. Data Requirements
Identify:
- entities read,
- entities written,
- fields displayed,
- sensitive fields,
- retention implications.

### 9. Permission Requirements
Define who can:
- view,
- create,
- update,
- delete,
- export,
- approve.

### 10. Edge Cases
Examples:
- empty data,
- missing linked record,
- duplicate action,
- expired session,
- user loses permission mid-flow,
- network/API failure.

### 11. Success Metric
When relevant, define how success is measured.

## Requirement Ambiguity Rule
If implementation requires guessing a business rule that could materially change behavior, flag it as:

REQUIREMENT GAP

Missing decision:
...

Possible options:
...

Risk of guessing:
...

Recommended default:
...

For low-risk implementation details, use the safest architecture-compatible default and document it.

## Change Rule
If requirements change after implementation begins:
- update the specification,
- re-run impact analysis,
- identify data/security/test impact,
- do not silently alter behavior.
