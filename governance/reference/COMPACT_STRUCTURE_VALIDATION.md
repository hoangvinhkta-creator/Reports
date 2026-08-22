# COMPACT STRUCTURE VALIDATION

## Root Design

Governance-related root entries:
- `CLAUDE.md`
- `PROJECT/`
- `docs/`
- `governance/`

Root-level governance standards:
0

Only `CLAUDE.md` remains as the root governance entry point.

## Read-before-work Safety

The compact structure preserves the mandatory reading behavior.

### S000
`CLAUDE.md` routes the agent to:
1. `governance/core/PROJECT_PROFILE_STANDARD.md`
2. `governance/core/RULE_PRECEDENCE.md`
3. `governance/core/TASK_MODE_STANDARD.md`
4. `governance/core/00_SESSION_ORCHESTRATION.md`

### Normal Major Task Session
The agent reads:
1. `PROJECT/PROJECT_PROFILE.md`
2. `PROJECT/PROJECT_PROGRESS.md`
3. current task under `docs/tasks/`
4. only applicable governance files
5. Ready Gate before coding

### Progress-only Question
The agent reads:
`PROJECT/PROJECT_PROGRESS.md`
first.

### Audit
The selected AUDIT profile explicitly routes to the required core/product/audit rules.

Therefore moving static rules under `governance/` does not weaken the read-before-work requirements.

## Validator Results

### Structure
```text
GOVERNANCE STRUCTURE: PASS
Checked 21 required paths.
```

### Project State
Expected to fail before S000 because no real profile is selected yet.
```text
PROJECT STATE: FAIL
- PROJECT/PROJECT_PROFILE.md must contain a valid Selected Profile: AUDIT, PRODUCT, SOLO_LITE, TEAM_PRODUCTION
- PROJECT_PROGRESS.md must contain a valid Profile value: AUDIT, PRODUCT, SOLO_LITE, TEAM_PRODUCTION
```

### Task Completion
```text
TASK COMPLETION: PASS
Checked 0 DONE task(s).
```

### Evidence
```text
EVIDENCE VALIDATION: PASS
Checked 0 REQUIRED PASS evidence record(s).
```

## Repository-relative Reference Integrity

Broken canonical path references: 0

PASS — no broken canonical repository-relative `.md`/`.py`/`.svg` references detected.
