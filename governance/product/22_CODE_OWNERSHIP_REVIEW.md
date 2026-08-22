# 22 — Code Ownership & Review Rules

## Objective
Clarify accountability for high-risk areas and prevent unreviewed changes.

## Ownership
Projects should identify owners for critical domains when the team size supports it.

Examples:
- authentication/security,
- data model/migrations,
- pricing,
- infrastructure,
- integrations.

## Review Levels

### Standard Review
Normal bounded changes.

### Elevated Review
Recommended for:
- authentication,
- authorization,
- customer data export,
- pricing logic,
- destructive operations,
- migrations,
- production infrastructure,
- secrets/configuration.

## Review Questions
Reviewer should confirm:
- requirement is correct,
- scope is bounded,
- architecture is respected,
- data migration is safe,
- permissions are enforced,
- tests are sufficient,
- rollback is possible.

## AI-Generated Code
AI-generated changes are not exempt from review.

For high-risk code, review the resulting implementation rather than trusting the generated explanation.

## CODEOWNERS
Where supported, use repository ownership rules for critical paths.

Example conceptual ownership:
- `/security/**`
- `/migrations/**`
- `/infra/**`
- `/modules/pricing/**`

## Separation of Duties
For highly sensitive operations, consider requiring a second human approval instead of allowing one person/tool to both author and approve.
