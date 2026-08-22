# Phase & Release Gate Standard

## Purpose
Individual task success does not prove the integrated system is healthy.

## Gate Levels

### 1. Task Gate
Validates one Major Task.

### 2. Phase Gate
Validates that all tasks in a phase work together.

### 3. Release Gate
Validates production readiness.

## Phase Gate
Run after a defined set of related tasks.

Typical checks:
- all required tasks DONE;
- cross-module integration works;
- routes remain valid;
- authentication/authorization regressions absent;
- data contracts remain compatible;
- build passes;
- integration/regression suite passes;
- no critical open regression item.

## Release Gate
Before production, verify as relevant:
- required phases passed;
- migrations ready;
- backup/rollback prepared;
- production environment verified;
- secrets/config verified;
- critical security checks passed;
- release notes prepared;
- observability available;
- deployment plan clear;
- post-deploy checks defined.

## Rule
Task DONE does not imply Phase DONE.
Phase DONE does not imply RELEASE READY.
