# 16 — Backup & Disaster Recovery Rules

## Objective
Protect the business from accidental deletion, corruption, failed migrations, account compromise, and infrastructure failure.

## Core Principle
A backup is only useful if it can be restored.

## Required Decisions

### RPO — Recovery Point Objective
Maximum acceptable amount of data loss measured in time.

Example:
RPO = 24 hours.

### RTO — Recovery Time Objective
Target maximum time to restore critical service.

Example:
RTO = 4 hours.

Project-specific values must be defined based on business importance.

## Backup Rules

### 1. Identify critical data
Examples:
- customers,
- orders,
- quotes,
- configuration,
- audit records,
- critical files.

### 2. Define backup frequency
Based on RPO and change rate.

### 3. Define retention
Examples:
- daily,
- weekly,
- monthly retention.

### 4. Protect backups
Backup access should follow least privilege.

### 5. Separate failure domains
Where practical, avoid keeping the only backup in the same logical failure domain as production.

### 6. Test restoration
Periodically test:
- backup integrity,
- restore process,
- credentials,
- documented steps.

### 7. Schema migrations
Take appropriate backup/snapshot before risky destructive migrations.

### 8. Bulk destructive operations
Before mass delete/update:
- validate target scope,
- require appropriate authorization,
- consider snapshot/backup,
- provide dry-run where practical.

## Disaster Recovery Runbook
Document:
1. incident declaration,
2. service containment,
3. identify last known good state,
4. select recovery point,
5. restore,
6. validate integrity,
7. restore application traffic,
8. monitor,
9. document incident.

## AI Agent Rule
An AI coding agent must not assume a backup exists.
Before recommending destructive migration, explicitly identify backup/rollback requirements.
