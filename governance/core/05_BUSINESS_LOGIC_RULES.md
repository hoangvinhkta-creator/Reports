# 05 — Business Logic Rules

## Objective
Business rules must be centralized, reusable, testable, and independent from UI implementation.

## Rules

### 1. Do not bury business logic in UI components
Components should primarily handle:
- rendering,
- user interaction,
- local presentation state.

### 2. Business rules belong in use cases/services/domain logic
Examples:
- quotation calculations,
- discount limits,
- order state transitions,
- follow-up scheduling,
- customer assignment rules.

### 3. One business rule = one authoritative implementation
Do not independently reimplement the same calculation in several pages.

### 4. Avoid giant handlers
Do not create handlers that combine:
- validation,
- calculation,
- database access,
- authorization,
- audit logging,
- notifications,
- UI state.

Break responsibilities apart.

### 5. State transitions must be explicit
Example:

DRAFT
→ SENT
→ ACCEPTED
→ ORDERED

Define allowed and forbidden transitions.

### 6. Business rules must be deterministic where possible
Pure calculation logic should avoid hidden external dependencies.

### 7. Side effects must be visible
Examples:
Creating an order may also:
- create follow-up tasks,
- update customer state,
- write audit history.

These effects must be explicit in the use case.

### 8. Domain validation differs from form validation
UI validation improves user experience.
Business validation protects system correctness.

Both may be required.

### 9. Do not silently change business behavior while refactoring
Behavior changes must be intentional and documented.

## Recommended Flow

UI
↓
Use Case
↓
Business Rules
↓
Repository/API
↓
Persistence

## Example
Instead of:

handleSaveQuote()

performing everything, prefer:

createQuote(input)
calculateQuoteTotals(items)
validateDiscount(user, discount)
quoteRepository.save(quote)
careService.scheduleFollowUps(order)
auditService.record(...)
