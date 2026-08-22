# 18 — Incident Response Rules

## Objective
Respond to production incidents systematically instead of applying uncontrolled patches.

## Incident Examples
- production outage,
- unauthorized access,
- data exposure,
- incorrect bulk update,
- failed migration,
- severe performance degradation,
- critical integration failure.

## Incident Workflow

INCIDENT DETECTED
↓
ASSESS
↓
CONTAIN
↓
PRESERVE EVIDENCE
↓
DIAGNOSE
↓
RECOVER
↓
VERIFY
↓
POSTMORTEM

## 1. Assess
Determine:
- affected users,
- affected systems,
- data risk,
- security risk,
- business severity,
- start time.

## 2. Contain
Examples:
- disable affected feature,
- revoke compromised credential,
- block dangerous mutation,
- roll back release.

Prefer containment over speculative rewrites.

## 3. Preserve Evidence
Do not destroy useful:
- logs,
- audit records,
- request IDs,
- deployment details,
- timestamps.

## 4. Diagnose
Identify the actual root cause or the narrowest confirmed failure.

## 5. Recovery
Choose:
- rollback,
- restore,
- configuration correction,
- minimal hotfix,
- controlled fix-forward.

## 6. Verify
Confirm:
- service restored,
- security restored,
- data integrity,
- no ongoing errors,
- affected flows work.

## 7. Postmortem
Document:
- timeline,
- impact,
- root cause,
- why defenses failed,
- corrective actions,
- prevention.

## AI Agent Incident Rule
During an incident:
- do not perform unrelated refactoring,
- do not make several speculative fixes at once,
- do not erase evidence,
- prefer minimal reversible changes,
- clearly report assumptions.

## Security Incident
If credential/data compromise is suspected:
- rotate/revoke credentials,
- restrict access,
- preserve logs,
- assess exposed data,
- follow applicable organizational/legal notification process.
