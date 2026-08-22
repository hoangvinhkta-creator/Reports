# Governance Directory

This directory contains STATIC governance.

## Structure

```text
governance/
├── core/       # session control, engineering rules, gates, evidence
├── product/    # product/production/operations rules
├── audit/      # discovery and audit templates
├── templates/  # runtime artifact templates
├── scripts/    # machine validators
└── reference/  # guide, changelog, history, acceptance material
```

## Important

Do not move these files back to repository root.

The root entry point is:
`CLAUDE.md`

Every session should start from `CLAUDE.md`, then load only the files required for the selected project profile and current task.


## Content-preservation rule

Directory refactors MUST NOT rewrite, summarize, shorten, or delete governance semantics.

Allowed during a pure structure refactor:
- move files,
- update canonical paths,
- update validator path resolution.

Any semantic edit must be separately identified, justified, and tested.
