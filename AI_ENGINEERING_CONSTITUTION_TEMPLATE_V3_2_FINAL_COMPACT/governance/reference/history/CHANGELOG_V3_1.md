# CHANGELOG — V3.1

## Fixed
- Added actual `docs/tasks/` and `docs/sessions/` files so folders are included in ZIP.
- Moved reusable templates into `/templates`.
- Reduced runtime/template ambiguity.
- Removed governance assumption that Fable is inherently a design-specialized model.

## Added
- Project Profiles: SOLO_LITE, PRODUCT, TEAM_PRODUCTION, AUDIT.
- Rule precedence.
- Evidence Levels E0/E1/E2.
- Risk-based evidence requirements.
- Micro Task mode.
- Spike/Exploratory mode.
- Discovery Baseline template.
- Audit Findings template with severity.
- Optional machine enforcement layer.
- Runtime `PROJECT_PROFILE.md`.
- Acceptance checklist for framework review.

## Changed
- S000 now selects project profile before detailed roadmap finalization.
- Completion Gates are preliminary during early planning, finalized/frozen at READY.
- Governance depth is proportional to project risk/size.
- AUDIT profile defaults to read-only.
