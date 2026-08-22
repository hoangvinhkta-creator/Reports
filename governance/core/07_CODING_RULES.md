# 07 — Coding Rules

## Objective
Produce readable, maintainable code that does not rely on hidden shortcuts.

## Rules

### 1. Prefer clarity over cleverness
Code should be understandable by another developer and future AI agent.

### 2. Functions should have clear responsibilities
Avoid large functions doing unrelated work.

### 3. Components should remain focused
Split large components when responsibilities become distinct.

### 4. No silent error swallowing
Avoid:

try {
  ...
} catch (e) {}

Errors must be handled, propagated, or intentionally recorded.

### 5. Do not suppress type errors as a default fix
Avoid:
- `@ts-ignore`
- unsafe casts
- disabling compiler checks

unless explicitly justified.

### 6. Avoid magic values
Do not hard-code:
- role names,
- statuses,
- route paths,
- limits,
- important durations,
- configuration values

throughout the codebase.

Use centralized constants/config/enums.

### 7. Reuse before duplicating
Before creating a new:
- helper,
- service,
- component,
- type,
- utility,

search for an existing equivalent.

### 8. Do not install dependencies unnecessarily
Before installing a package:
- inspect current dependencies,
- assess maintenance/security,
- confirm existing tools cannot solve the problem.

### 9. Follow existing conventions
Do not introduce a completely different style without architectural reason.

### 10. Comments explain why, not obvious syntax
Use comments for non-obvious decisions, constraints, or tradeoffs.

### 11. Naming
Names should communicate business meaning.

Prefer:
calculateQuoteTotal()

over:
calc()

### 12. No dead code
Remove obsolete code created by the same task when safe and scoped.

Do not perform unrelated cleanup.

### 13. Configuration separation
Environment-specific settings belong in configuration, not scattered implementation.

### 14. Production code must not depend on debug hacks
Temporary bypasses must not remain as permanent behavior.

## Code Review Questions
- Is this the smallest coherent solution?
- Is responsibility placed in the correct layer?
- Did we duplicate logic?
- Is there a hidden shortcut?
- Is failure behavior explicit?
- Will another developer understand this later?
