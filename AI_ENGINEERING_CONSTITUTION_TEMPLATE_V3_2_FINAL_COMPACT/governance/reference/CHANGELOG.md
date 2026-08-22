# CHANGELOG

## V3.2 Final

### Enforcement
- `governance/scripts/governance/validate_project_state.py` now validates actual profile/task-mode values instead of only checking labels.
- Added `governance/scripts/governance/validate_task_completion.py`.
- Added `governance/scripts/governance/validate_evidence.py`.
- Structure validator now includes `governance/core/11_FORBIDDEN_ACTIONS.md` and `governance/core/04_SECURITY_RULES.md`.

### Runtime consistency
- Micro Task inline tracking now references the canonical Micro Task checklist rather than duplicating it.
- `CLAUDE.md` no longer duplicates the full S000 procedure; `governance/core/00_SESSION_ORCHESTRATION.md` is the single source of truth.
- Added E2 review output location and template.
- Validation report now includes Executed By and Timestamp.
- Package manifest generation fixed.

### Cleanup
- Historical changelogs/checklists moved to `docs/history/`.

## V3.2
See `governance/reference/history/CHANGELOG_V3_2.md`.

## V3.1
See `governance/reference/history/CHANGELOG_V3_1.md`.
