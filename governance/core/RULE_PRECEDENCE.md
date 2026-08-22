# Rule Precedence

## Purpose
Resolve genuine conflicts between governance rules without silent improvisation.

## Precedence Order

1. Safety / Security
2. Data Integrity
3. Legal / Privacy / Compliance
4. Explicit Business Requirements
5. Backward Compatibility
6. Architecture Contracts
7. Reliability / Operations
8. Accessibility / UX Correctness
9. Performance
10. Code Style / Developer Convenience

## Important Rule

Precedence is used ONLY when two requirements genuinely cannot both be satisfied.

A higher-priority rule does not grant permission to ignore a lower-priority rule when both can coexist.

## Conflict Procedure

When a real conflict exists, record:

RULE CONFLICT

Higher-priority rule:
...

Lower-priority rule:
...

Why both cannot be satisfied:
...

Risk:
...

Proposed resolution:
...

Required decision:
...

Do not resolve material conflicts silently.
