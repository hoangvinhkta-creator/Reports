# 19 — Dependency Management Rules

## Objective
Prevent unnecessary, insecure, abandoned, or conflicting dependencies.

## Before Adding a Dependency
Check:
1. Is equivalent functionality already present?
2. Can the platform/native library solve it safely?
3. Is the package actively maintained?
4. Is its license acceptable?
5. Does it introduce known security risk?
6. Is its bundle/runtime cost reasonable?
7. Will it create vendor lock-in or architecture coupling?

## Rules

### 1. Use lockfiles
Commit the appropriate lockfile.

### 2. Avoid duplicate libraries
Do not install several packages solving the same problem without justification.

### 3. Pin/constraint versions appropriately
Follow ecosystem best practice.

### 4. Security updates
Regularly review dependency vulnerabilities.

### 5. Major upgrades
Major version upgrades require:
- compatibility review,
- migration notes,
- tests.

### 6. Remove unused dependencies
Do not keep packages that no longer have a valid consumer.

### 7. AI Agent Requirement
Before running an install command, report:
- package,
- purpose,
- existing alternatives checked,
- expected impact.

## Dependency Change Report
For significant dependency changes document:
- old version,
- new version,
- breaking changes,
- migration,
- verification.
