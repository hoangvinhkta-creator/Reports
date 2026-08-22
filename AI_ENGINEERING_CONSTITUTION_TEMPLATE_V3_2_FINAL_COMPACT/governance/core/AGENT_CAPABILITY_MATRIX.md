# Agent Capability Matrix

## Purpose
Avoid hard-coding project planning to model names that may change over time.

Tasks should be assigned to capability tiers first, then mapped to currently available agents/models.

## Tier A — Lightweight
Best for:
- trivial edits,
- documentation updates,
- repetitive bounded changes,
- simple test additions,
- low-risk UI corrections.

Typical current mapping:
Haiku.

## Tier B — Implementation
Best default for:
- CRUD,
- forms,
- routes,
- service implementation,
- standard API work,
- bounded refactors,
- normal test work.

Typical current mapping:
Sonnet.

## Tier C — Advanced Reasoning
Use for:
- architecture,
- authentication/authorization,
- complex migrations,
- high-risk data changes,
- cross-module refactors,
- difficult debugging,
- root-cause analysis,
- production incidents.

Typical current mapping:
Opus.

## Tier D — Design / Creative
Use where the available agent is optimized for:
- UX exploration,
- visual design,
- interface concepts,
- design-system ideation,
- content-heavy presentation work.

Current mapping:
Project-specific. Define during S000 based on the actual available agent capabilities.

Do not use a design-focused tier as final authority for security/data architecture.

## Scoring Inputs
Agent assignment should consider:

- Difficulty: 1–5
- Risk: 1–5
- Blast Radius: 1–5
- Ambiguity
- Security impact
- Data impact
- Architecture impact

## Escalation
Every task should define:
- Primary Tier
- Escalation Tier
- Escalation triggers
