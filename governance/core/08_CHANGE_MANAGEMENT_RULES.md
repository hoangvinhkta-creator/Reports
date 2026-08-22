# 08 — Change Management Rules

## Objective
Keep AI-generated modifications bounded, reviewable, reversible, and understandable.

## Mandatory Impact Analysis
Before code changes identify:

- requested outcome,
- files likely affected,
- modules affected,
- routes affected,
- data/schema affected,
- API affected,
- permissions/security affected,
- migration requirement,
- regression risks,
- tests required.

## Scope Rule
Do not change unrelated code because it could be improved.

A request to add a feature is not permission for a codebase-wide cleanup.

## Separate Concerns Across Changes
Avoid combining:
- architecture refactor,
- database migration,
- unrelated cleanup,
- new feature,
- UI redesign

in a single uncontrolled change.

Prefer staged changes when risk is meaningful.

## Example

Bad:

Add customer export
+ rewrite customer module
+ rename schema
+ replace router
+ install state library

Good:

1. Add export contract/service.
2. Add permission checks.
3. Add UI entry point.
4. Add tests.
5. Separately propose larger refactor if needed.

## Migration Rule
Persisted data changes require:
- migration plan,
- compatibility plan,
- validation,
- rollback consideration.

## Backward Compatibility
Consider current:
- URLs,
- data,
- APIs,
- users,
- saved bookmarks,
- integrations.

## Change Report
At completion report:

Files changed:
...

Why:
...

Behavior changed:
...

Security impact:
...

Data impact:
...

Migration:
...

Tests:
...

Known risks / follow-up:
...

## Rollback Mindset
Prefer changes that can be reverted without damaging unrelated parts of the system.
