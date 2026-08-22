# 15 — Logging, Audit & Observability Rules

## Objective
Make production behavior diagnosable without leaking sensitive data.

## Three Different Concepts

### Application Logs
Technical events used to troubleshoot the system.

### Metrics / Monitoring
Aggregated signals such as:
- error rate,
- latency,
- failed requests,
- job failure count.

### Audit Log
Business/security record of who changed what.

Do not confuse these systems.

## Logging Rules

### 1. Log meaningful failures
Include enough context to diagnose the issue without exposing secrets.

### 2. Use structured context
When possible include:
- event name,
- request/correlation ID,
- module,
- safe entity ID,
- user ID where appropriate,
- environment.

### 3. Never log secrets
Do not log:
- passwords,
- access tokens,
- refresh tokens,
- private keys,
- secret API credentials.

### 4. Minimize sensitive personal data
Do not log full customer data unless absolutely necessary.

### 5. Error visibility
Critical backend failures should not disappear silently.

## Monitoring
Consider alerts for:
- elevated error rate,
- auth failures,
- database failures,
- queue/job failures,
- unusual latency,
- storage capacity,
- failed integrations.

## Audit Logging

High-value actions should consider an immutable or protected audit record.

Typical events:
- login security events,
- role/permission changes,
- customer export,
- record deletion,
- quote/price override,
- approval/rejection,
- configuration changes.

Recommended fields:
- auditEventId,
- timestamp,
- actorUserId,
- action,
- resourceType,
- resourceId,
- safe before/after values where appropriate,
- source/request ID.

## Audit Security
Normal users must not be able to alter historical audit records.

## Privacy
Audit logging does not justify storing unnecessary sensitive data.

## Diagnostic Correlation
Where practical, propagate a request/correlation ID across:
frontend → API → backend → external integration.
