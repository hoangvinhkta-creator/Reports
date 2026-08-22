# PROJECT PROGRESS

## Project Summary

Project:
Tín Phát — Business Report Automation Tool

Objective:
Replace the manual monthly assembly of `Báo cáo Kinh doanh 2026.xlsx` with a
tool that ingests the raw ERP sales book, classifies each order's lead source,
computes accounting profit and KPI profit separately, converts revenue through
two independent PERSONAL/ADS buckets, produces month and year summaries, and
lets several people view and correct the data daily before exporting .xlsx.

Project Type:
NEW (greenfield application, replacing a spreadsheet-based process)

Profile:
PRODUCT

Last Updated:
2026-08-22 (S000)

Overall Status:
IN_PROGRESS

Current Phase:
PHASE-00 — Governance bootstrap and source analysis

Current Task:
TASK-002 — Source workbook analysis documents

Current Task Mode:
MAJOR

Next Recommended Task:
TASK-003 — Architecture Decision Records

## Overall Roadmap

- [x] PHASE-00 — Governance bootstrap and source analysis
  - [x] TASK-000 — Promote governance package to repository root (MICRO)
  - [x] TASK-001 — S000: profile selection and project state initialization (MAJOR)
  - [ ] TASK-002 — Source workbook analysis, 6 documents per spec section 27 (MAJOR)
  - [ ] TASK-003 — ADR-001/002/003 (MICRO)
  - [ ] GATE-00 — Owner approves `docs/analysis/` before any application code

- [ ] PHASE-01 — Calculation engine (pure Python, no UI, no database)
  - [ ] TASK-101 — importer + normalizer
  - [ ] TASK-102 — employee_mapper
  - [ ] TASK-103 — order_builder
  - [ ] TASK-104 — lead_source_engine (ADS rule)
  - [ ] TASK-105 — price_engine + PriceProvider interface
  - [ ] TASK-106 — adjustment_engine
  - [ ] TASK-107 — profit_engine
  - [ ] TASK-108 — conversion_engine (PERSONAL/ADS buckets)
  - [ ] TASK-109 — summary_engine
  - [ ] TASK-110 — validation + Review Queue
  - [ ] TASK-111 — excel_exporter
  - [ ] TASK-112 — CLI
  - [ ] GATE-01 — Reconciliation against the real raw file; owner confirms C1

- [ ] PHASE-02 — Persistence and API
  - [ ] TASK-201 — database schema + migrations
  - [ ] TASK-202 — audit_service
  - [ ] TASK-203 — HTTP API
  - [ ] TASK-204 — authentication and roles
  - [ ] TASK-205 — incremental recalculation

- [ ] PHASE-03 — Web interface
  - [ ] TASK-301 — upload and import preview
  - [ ] TASK-302 — employee-month detail grid with inline editing
  - [ ] TASK-303 — month summary and year dashboard
  - [ ] TASK-304 — configuration screens
  - [ ] TASK-305 — review queue and audit screens
  - [ ] TASK-306 — Excel export
  - [ ] GATE-03 — MVP acceptance, spec section 28, all 14 criteria

- [ ] PHASE-04 — Completion
  - [ ] TASK-401 — PriceMasterProvider integration
  - [ ] TASK-402 — product_mapper
  - [ ] TASK-403 — target and commission formalization
  - [ ] TASK-404 — channel sheets and split conversion

## Preliminary Dependency Graph

```
TASK-000 → TASK-001 → TASK-002 → TASK-003 → GATE-00
GATE-00  → TASK-101 → TASK-102 → TASK-103 → TASK-104
                                   ↓          ↓
                        TASK-105 → TASK-106 → TASK-107 → TASK-108 → TASK-109
                                                                       ↓
                                              TASK-110 ─────────────→ TASK-111 → TASK-112 → GATE-01
GATE-01  → TASK-201 → TASK-202 → TASK-203 → TASK-204 → TASK-205
TASK-205 → TASK-301 … TASK-306 → GATE-03 → PHASE-04
```

Parallel-safe: TASK-105 may proceed alongside TASK-103/TASK-104; TASK-110 may
proceed alongside TASK-108/TASK-109.

## Preliminary Scoring

| Task | Difficulty | Risk | Blast Radius | Mode | Primary Tier | Escalation |
|---|---|---|---|---|---|---|
| TASK-000 | 1 | 1 | 2 | MICRO | A | B |
| TASK-001 | 2 | 2 | 1 | MAJOR | C | — |
| TASK-002 | 3 | 2 | 1 | MAJOR | C | — |
| TASK-003 | 2 | 2 | 2 | MICRO | C | — |
| TASK-101 | 3 | 3 | 3 | MAJOR | B | C |
| TASK-102 | 2 | 3 | 3 | MAJOR | B | C |
| TASK-103 | 2 | 4 | 4 | MAJOR | B | C |
| TASK-104 | 3 | 4 | 5 | MAJOR | C | — |
| TASK-105 | 3 | 3 | 3 | MAJOR | B | C |
| TASK-106 | 4 | 4 | 4 | MAJOR | C | — |
| TASK-107 | 2 | 4 | 4 | MAJOR | B | C |
| TASK-108 | 3 | 5 | 5 | MAJOR | C | — |
| TASK-109 | 3 | 4 | 4 | MAJOR | B | C |
| TASK-110 | 2 | 2 | 2 | MAJOR | B | C |
| TASK-111 | 3 | 2 | 2 | MAJOR | B | C |
| TASK-112 | 1 | 2 | 2 | MICRO | A | B |
| TASK-201 | 3 | 4 | 5 | MAJOR | C | — |
| TASK-202 | 3 | 4 | 4 | MAJOR | C | — |
| TASK-203 | 3 | 3 | 4 | MAJOR | B | C |
| TASK-204 | 3 | 5 | 5 | MAJOR | C | — |
| TASK-205 | 4 | 4 | 4 | MAJOR | C | — |
| TASK-301…306 | 3 | 2 | 3 | MAJOR | B | C |

Risk 4–5 concentrates on TASK-104, TASK-106, TASK-108, TASK-201, TASK-204 and
TASK-205 — the tasks where a silent error becomes a wrong number on someone's
pay, or a leak of customer personal data. These carry E1 mandatory and E2
recommended per the profile's evidence rule.

## Preliminary Completion Gates

Finalized and frozen per task before it becomes READY. Preliminary REQUIRED
checks recorded now:

- PHASE-01 overall: distinct order count for Tín Phát must equal 254 for
  01.2026 and 146 for 06.2026 against the real raw file (E1). Every remaining
  difference against the sample report must be explained in writing, not
  averaged away.
- TASK-104: all 8 ADS test cases from spec section 29 PASS (E1).
- TASK-108: `TotalConvertedRevenue == PersonalConvertedRevenue + AdsConvertedRevenue`
  holds for every employee-month, and no code path divides a combined profit by
  a single rate (E1).
- TASK-201/204: no customer personal data in application logs; role checks
  enforced server-side (E1, seek E2).
- Every phase: no employee name, conversion rate, target, adjustment amount or
  ADS keyword appears as a literal in application source (E1, grep-verifiable).

## Current Task Snapshot

Task:
TASK-002 — Source workbook analysis documents

Task Mode:
MAJOR

Status:
IN_PROGRESS

Required Gate Progress:
0 / 6 documents complete

Primary Agent Tier:
C

Escalation Tier:
—

## Micro Tasks (Inline)

Canonical checklist:
`governance/templates/MICRO_TASK_CHECKLIST.md`

### MICRO-000 — Promote governance package to repository root
Status:
DONE

Checklist Reference:
`governance/templates/MICRO_TASK_CHECKLIST.md`

Evidence Summary:
E1 — `git mv` executed, `ls` confirms `CLAUDE.md`, `PROJECT/`, `docs/`,
`governance/` at repository root; `git status` shows 74 pure renames with no
content change. Commit `8f77e20`.

## Active Blockers
- None.

## Active Risks

- **RISK-01 — The ADS rule has no data to stand on.** The string "ADS" occurs
  0 times in the raw sales book and 0 times in the report workbook. The rule is
  built to specification, but it only starts producing non-default output once
  data entry changes. Until then every historical order classifies PERSONAL.
  Mitigation: manual override at OrderID level with audit trail; the tool
  reports how many orders matched the rule on each import so a month of silent
  zeroes is visible rather than assumed correct.

- **RISK-02 — Tín Phát's conversion rate changes meaning under the new rule.**
  Tín Phát currently converts at 7.5% for every order, which equals the ADS
  rate. Under the ADS rule an unmarked Tín Phát order falls to PERSONAL 5.5%
  and the reported figure moves. Open item C1, to be confirmed by the owner at
  GATE-01 before any number is published.

- **RISK-03 — Purchase price is absent at source.** The raw file carries no
  purchase price, only an ERP-computed profit. By the owner's decision the
  field stays Pending rather than being inferred. Consequence: KPI profit and
  converted revenue are incomplete until either the price tool is connected or
  prices are entered by hand. The tool must show Pending explicitly and must
  never silently treat a missing price as zero.

- **RISK-04 — Customer personal data.** Names, phone numbers and addresses on
  every line. Sample data is git-ignored; anonymized fixtures are required for
  tests; personal fields must not reach application logs.

## Open Regression Items
- None yet — no application code exists.

## Recent Decisions
- See `PROJECT/PROJECT_DECISIONS.md` — DEC-001 through DEC-008.

## Session History
- S000 — PROJECT OPEN — 2026-08-22 — Read the specification and both sample
  workbooks; verified business rules against real data; selected the PRODUCT
  profile; created the roadmap, dependency graph, scoring and preliminary gates;
  recorded 8 tactical decisions and 4 active risks.

## Next Session

Recommended Session:
S001 — TASK-002 completion and TASK-003

Purpose:
Finish the six analysis documents required by specification section 27, write
the three ADRs, then hold at GATE-00 for owner approval before writing any
application code.

Files to read first:
- `PROJECT/PROJECT_PROGRESS.md`
- `PROJECT/PROJECT_PROFILE.md`
- `PROJECT/PROJECT_DECISIONS.md`
- `docs/spec/Dac_ta_cong_cu_bao_cao_kinh_doanh.docx`
- `docs/analysis/`
