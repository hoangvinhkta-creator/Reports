# 11 — Forbidden Actions

The AI coding agent MUST NOT:

1. Start coding before inspecting relevant existing implementation.
2. Put secrets or private credentials into frontend code.
3. Treat hidden UI as authorization.
4. Bypass security rules to make a feature work.
5. Trust client-provided role, permission, owner, price, or approval data.
6. Access the database directly from UI components when an application data layer exists or should exist.
7. Duplicate established business rules without justification.
8. Rename/delete persisted production fields without migration analysis.
9. Change unrelated modules outside the task scope.
10. Perform a large rewrite merely because it prefers another architecture.
11. Disable tests, lint, compiler checks, or security controls to obtain a passing build.
12. Use `@ts-ignore`, broad `any`, unsafe casts, or equivalent as the default way to resolve type problems.
13. Swallow exceptions silently.
14. Hard-code secrets, permissions, critical role rules, or environment-specific values throughout application code.
15. Install a new library before checking whether the project already has an appropriate solution.
16. Introduce circular dependencies.
17. Make destructive data changes without rollback consideration.
18. Assume existing data matches a new schema.
19. Return more sensitive data to the client than necessary.
20. Expose internal stack traces/secrets to end users.
21. Mix major refactoring and feature work without explicit reason.
22. Mark work complete while relevant build/tests are failing.
23. Ignore a detected conflict between documentation and implementation.
24. Fix unrelated issues opportunistically unless required for the requested task.
25. Replace stable working code solely to make it stylistically different.

26. Invent, fabricate, or falsely claim command output, test results, HTTP status codes, screenshots, CI results, execution evidence, reviewer approval, or human approval. If a check was not actually executed, mark it `NOT_TESTED`.

## Required Response to a Blocker
If one of these rules prevents implementation, report:

BLOCKER

Reason:
...

Affected requirement:
...

Safe options:
...

Recommended option:
...

Do not silently bypass the rule.
