# Micro Task Checklist

Use only when the task satisfies `governance/core/TASK_MODE_STANDARD.md` eligibility for MICRO mode.

## Compact Ready Gate
- [ ] Requirement/bug is clear enough to act on.
- [ ] Risk <= 2.
- [ ] Blast Radius <= 2.
- [ ] No architecture/auth/schema/destructive-data change.
- [ ] Expected touch area is narrow and known.
- [ ] Relevant verification method is known.

## Compact Completion Gate
- [ ] Intended behavior is implemented.
- [ ] Relevant build/test/manual verification was actually executed.
- [ ] Evidence is recorded according to `governance/core/EVIDENCE_STANDARD.md`.
- [ ] No unexpected scope expansion occurred.
- [ ] Relevant regression check passed.
- [ ] `PROJECT/PROJECT_PROGRESS.md` inline Micro Task entry is updated.

## Exit Rule
If any of the following appears, STOP treating the work as MICRO and promote to MAJOR:
- Risk > 2
- Blast Radius > 2
- architecture impact
- authorization/security impact
- persisted schema migration
- destructive data operation
- cross-module redesign
