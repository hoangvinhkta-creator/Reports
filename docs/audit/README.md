# Audit Artifacts

Runtime audit outputs produced under the AUDIT profile.

Established by DEC-003 in `PROJECT/PROJECT_DECISIONS.md`, because discovery
baselines and findings are a runtime artifact class with no designated home in
the shipped `docs/` layout, and `docs/reviews/` is reserved for E2 independent
review artifacts by `governance/core/EVIDENCE_STANDARD.md`.

## Contents

- `S001_DISCOVERY_BASELINE.md` — baseline from `governance/audit/DISCOVERY_BASELINE_TEMPLATE.md`
- `S001_AUDIT_FINDINGS.md` — findings from `governance/audit/AUDIT_FINDINGS_TEMPLATE.md`
- `REMEDIATION_ROADMAP.md` — detailed remediation plan derived from those findings

## Naming

`S<NNN>_DISCOVERY_BASELINE.md` and `S<NNN>_AUDIT_FINDINGS.md`, one pair per
discovery session.

## Rules

Findings are an immutable record. Do not edit finding text in later sessions.
Track a finding's changing state in `PROJECT/PROJECT_PROGRESS.md` (Findings
Register) and in the roadmap's traceability table.

`PROJECT/PROJECT_PROGRESS.md` is the canonical live checklist. If it and
`docs/audit/REMEDIATION_ROADMAP.md` disagree, the progress file wins and the roadmap is
corrected to match.
