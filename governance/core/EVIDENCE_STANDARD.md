# Evidence Standard

## Purpose
Prevent an AI agent from marking gates PASS using unsupported narrative claims.

## Evidence Levels

### E0 — Claim
Agent-written description only.

Example:
"Permission test passed."

Use:
- informational notes,
- low-risk non-critical checks only.

E0 MUST NOT be accepted as sole evidence for high-risk required gates.

### E1 — Execution Evidence
Output from an actual executed check.

Examples:
- test command output,
- build/lint/typecheck output,
- HTTP response code,
- database rule emulator output,
- generated artifact checksum,
- screenshot of actual result,
- browser/devtool verification result when appropriate.

### E2 — Independent Evidence
Verification independent from the implementing claim.

Examples:
- CI result,
- external security scanner,
- staging check,
- second agent review,
- human reviewer,
- independent test run.

## Minimum Evidence by Risk

### Risk 1–2
Required checks:
- E0 or E1 depending on check type.
- Functional correctness should prefer E1 where executable.

### Risk 3
Required checks:
- E1 mandatory for executable verification.

### Risk 4–5
Required checks:
- E1 mandatory.
- Security/data-critical checks SHOULD have E2.
- If E2 is unavailable, record the limitation and prevent production release where independent verification is required by profile.

## Evidence Integrity

Do not invent:
- command output,
- test results,
- HTTP status,
- screenshots,
- CI results,
- human approvals.

If not executed:
Status = NOT_TESTED.

## Evidence Record

Check ID:
...

Status:
PASS / FAIL / BLOCKED / NOT_TESTED

Evidence Level:
E0 / E1 / E2

Evidence:
...

Executed By:
...

Timestamp:
...

## Solo Independent Review Procedure

For a solo developer without CI/staging/another human reviewer, E2 may be produced by a separate reviewer-agent session.

The reviewer session must:
1. Start from repository state, not from implementer claims.
2. Read the frozen task gate.
3. Inspect the actual diff/code.
4. Re-run the required checks independently where possible.
5. Record its own evidence.
6. Treat implementer-written PASS statements as untrusted narrative.

The reviewer must see the code/diff being reviewed; independence means independent verification, not blindness to the implementation.

If no credible E2 path exists:
- record the limitation;
- do not pretend E2 exists;
- follow the project profile's release rule.


## E2 Artifact Storage

Independent review output must be persisted under:

`docs/reviews/`

Use:

`governance/templates/E2_INDEPENDENT_REVIEW_TEMPLATE.md`

Do not leave E2 results only in chat history.
