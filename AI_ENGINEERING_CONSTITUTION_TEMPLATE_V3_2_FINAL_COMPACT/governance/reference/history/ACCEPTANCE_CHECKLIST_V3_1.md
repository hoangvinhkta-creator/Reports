# ACCEPTANCE CHECKLIST — V3.1 FRAMEWORK

Use this file to review whether V3.1 resolves the identified design issues.

## A. Package Structure
- [ ] `docs/tasks/` exists in the package.
- [ ] `docs/sessions/` exists in the package.
- [ ] Runtime project files live under `/PROJECT`.
- [ ] Reusable templates live under `/templates`.
- [ ] Templates are not confused with runtime state files.

## B. Rule Conflict Handling
- [ ] `governance/core/RULE_PRECEDENCE.md` exists.
- [ ] Security is higher priority than style/convenience.
- [ ] Data integrity and privacy are explicitly ranked.
- [ ] Precedence only applies to real conflicts.

## C. Proportional Governance
- [ ] `governance/core/PROJECT_PROFILE_STANDARD.md` exists.
- [ ] SOLO_LITE profile exists.
- [ ] PRODUCT profile exists.
- [ ] TEAM_PRODUCTION profile exists.
- [ ] AUDIT profile exists.
- [ ] S000 selects a profile before detailed roadmap finalization.

## D. Task Ceremony Scaling
- [ ] `governance/core/TASK_MODE_STANDARD.md` exists.
- [ ] MICRO tasks are supported.
- [ ] MAJOR tasks retain full governance.
- [ ] SPIKE/EXPLORATORY tasks are supported.
- [ ] Micro tasks automatically promote if risk/scope grows.

## E. Evidence Integrity
- [ ] `governance/core/EVIDENCE_STANDARD.md` exists.
- [ ] E0, E1, E2 are defined.
- [ ] Risk 3 executable required checks require E1.
- [ ] Risk 4–5 security/data-critical checks seek E2.
- [ ] Agent is prohibited from inventing evidence.
- [ ] NOT_TESTED is used when checks were not executed.

## F. Completion Gates
- [ ] Preliminary gate is created during planning.
- [ ] Final gate is frozen only when task becomes READY.
- [ ] Agent cannot weaken gate to self-pass.
- [ ] CODE COMPLETE remains different from TASK COMPLETE.

## G. Audit / Existing Project Review
- [ ] `governance/audit/DISCOVERY_BASELINE_TEMPLATE.md` exists.
- [ ] `governance/audit/AUDIT_FINDINGS_TEMPLATE.md` exists.
- [ ] Severity supports Critical/High/Medium/Low/Info.
- [ ] Findings require evidence and remediation path.
- [ ] AUDIT profile defaults to read-only.

## H. Anti-Patching / Escalation
- [ ] Escalation protocol remains present.
- [ ] Repeated failed approaches trigger root-cause review.
- [ ] Scope expansion cannot happen silently.
- [ ] Completion criteria cannot be disabled to force PASS.

## I. Enforcement
- [ ] `governance/reference/OPTIONAL_ENFORCEMENT_LAYER.md` exists.
- [ ] Machine-checkable validation is described.
- [ ] Enforcement is optional/proportional by profile.
- [ ] TEAM_PRODUCTION recommends CI integration.

## J. Agent Mapping
- [ ] Capability tiers remain.
- [ ] Governance does not rely on Fable being a design-specialized model.
- [ ] Actual agent mapping is project/environment-specific.

## Final Acceptance

V3.1 is accepted when:
- [ ] Sections A–J are all satisfied.
- [ ] No duplicate runtime/template ambiguity remains.
- [ ] No required folder referenced by governance is missing.
- [ ] The framework can operate in both lightweight and strict modes.
- [ ] High-risk task completion cannot rely solely on unsupported self-claims.

Reviewer:
...

Date:
...

Result:
ACCEPTED / CHANGES_REQUIRED

Notes:
...
