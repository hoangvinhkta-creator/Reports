# Escalation Protocol

## Purpose
Prevent repeated patching and force root-cause review when a task exceeds the current agent/session capability.

## Escalation Triggers
Escalate when any of the following occurs:

- two materially different implementation attempts fail;
- architecture conflict is discovered;
- security behavior is ambiguous;
- unexpected migration/data-loss risk appears;
- scope must expand across major modules;
- required completion gate cannot be satisfied safely;
- regression spreads beyond expected Blast Radius;
- production behavior differs materially from documented assumptions.

## Required Action

STOP IMPLEMENTATION
→ preserve evidence
→ document blocker
→ perform root-cause review
→ escalate agent tier / architecture review
→ update plan if needed

## Prohibited Behavior
Do not:
- continue stacking speculative fixes;
- disable failing checks;
- weaken Completion Gate;
- broaden scope silently;
- perform unrelated refactors.

## Escalation Record

Reason:
...

Attempts made:
...

Observed evidence:
...

Suspected root cause:
...

Affected scope:
...

Recommended agent tier:
...

Recommended next action:
...
