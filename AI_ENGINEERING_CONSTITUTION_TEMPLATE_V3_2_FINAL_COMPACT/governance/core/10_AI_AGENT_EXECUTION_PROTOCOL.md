# 10 — AI Agent Execution Protocol

## Objective
Force a disciplined workflow for Claude Code or another AI coding agent.

# PHASE 1 — DISCOVER

Read relevant:
- repository instructions,
- architecture,
- routes,
- schemas,
- security rules,
- business rules,
- existing implementation,
- tests.

Do NOT modify code yet.

Output internally or in task report:
- relevant files,
- current behavior,
- existing pattern.

# PHASE 2 — ANALYZE

Determine:

- owning module,
- affected modules,
- affected routes,
- data impact,
- schema impact,
- security impact,
- API impact,
- dependency impact,
- migration requirement,
- regression risk.

Do not assume.

# PHASE 3 — DESIGN

Choose the smallest coherent implementation compatible with the existing architecture.

Define:
- files to change,
- interfaces/contracts,
- validation,
- authorization,
- error behavior,
- test plan.

Do not invent a new architecture without necessity.

# PHASE 4 — IMPLEMENT

Rules:
- stay within defined scope,
- reuse existing patterns,
- maintain layer boundaries,
- preserve compatibility where required,
- do not bypass security,
- do not add unrelated refactors.

# PHASE 5 — VERIFY

Run applicable:
- build,
- lint,
- typecheck,
- tests.

Manually/automatically verify:
- route,
- auth,
- permission,
- data behavior,
- error states,
- regression.

# PHASE 6 — REPORT

Final report must contain:

## Summary
What changed.

## Files Changed
File + reason.

## Architecture Impact
None / describe.

## Routing Impact
None / describe.

## Data Impact
None / describe.

## Security Impact
None / describe.

## Migration
None / required steps.

## Verification
Checks performed and results.

## Remaining Risks
Known unresolved concerns.

## Follow-up
Optional future work, clearly separated from current task.

# Important
Never claim completion only because code was written.
Verification is part of implementation.
