# COMPACT REGRESSION FIX REPORT

## F-14 — PROJECT_PROFILE_STANDARD

Source words: 358
Compact words: 358

Status:
PASS

The Compact file is restored from the V3.2 Final source-of-truth and only canonical paths are changed.

Required restored sections checked manually/source-preservation:
- Profile Selection Inputs
- Use for
- Ceremony
- Runtime Record fields / justification

## F-15 — CLAUDE.md

Source words: 531
Compact words: 600

The difference is the intentional `Compact Directory Layout` note.
Original semantic content is retained with path substitutions.

Verified mechanisms:
- Full Task Lifecycle present
- BLOCKED / DEFERRED / CANCELLED present
- CONFLICT DETECTED present

## F-10 — Empty Completion Gate Fixture

Fixture:
- Status: DONE
- Risk: 5/5
- Completion Gate: empty

Expected:
FAIL

Actual:
```text
TASK COMPLETION: FAIL
- TASK-F10-FIXTURE.md: Status=DONE but no REQUIRED Completion Gate checks were found.
```

Regression test result:
PASS

## Validators

### Structure
```text
GOVERNANCE STRUCTURE: PASS
Checked 21 required paths.
```

### Project State
Expected FAIL before S000:
```text
PROJECT STATE: FAIL
- PROJECT/PROJECT_PROFILE.md must contain a valid Selected Profile: AUDIT, PRODUCT, SOLO_LITE, TEAM_PRODUCTION
- PROJECT_PROGRESS.md must contain a valid Profile value: AUDIT, PRODUCT, SOLO_LITE, TEAM_PRODUCTION
```

### Task Completion (normal package)
```text
TASK COMPLETION: PASS
Checked 0 DONE task(s).
```

### Evidence
```text
EVIDENCE VALIDATION: PASS
Checked 0 REQUIRED PASS evidence record(s).
```

### Refactor Preservation
```text
PRESERVATION: PASS
Profile selection content preserved; lifecycle/conflict mechanisms present.
```

## Refactor Rule Going Forward

Pure directory restructuring must be path-only.

Do not summarize or rewrite governance content during a move.
Semantic changes require a separately declared change and regression test.
