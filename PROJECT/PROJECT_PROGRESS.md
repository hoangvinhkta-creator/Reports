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
GATE-00 — awaiting owner approval of `docs/analysis/`

Current Task Mode:
MAJOR

Next Recommended Task:
TASK-101 — importer + normalizer (blocked by GATE-00)

## Overall Roadmap

- [x] PHASE-00 — Governance bootstrap and source analysis
  - [x] TASK-000 — Promote governance package to repository root (MICRO)
  - [x] TASK-001 — S000: profile selection and project state initialization (MAJOR)
  - [x] TASK-002 — Source workbook analysis, 6 documents per spec section 27 (MAJOR)
  - [x] TASK-003 — ADR-001/002/003 (MICRO)
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
GATE-00 — owner approval of the source analysis

Task Mode:
MAJOR

Status:
VERIFYING — waiting on owner approval of `docs/analysis/`

Required Gate Progress:
6 / 6 analysis documents written; 3 / 3 ADRs written; 0 / 1 approvals

Primary Agent Tier:
C

Escalation Tier:
—

### What GATE-00 is waiting for

One thing only: the owner reads `docs/analysis/` and confirms the mapping and
the business rules are right. Phase 1 starts on that approval.

### Open questions and when each is actually needed

None of these block the start of Phase 1. Each has a stated default so work
proceeds, and each has a point beyond which the default stops being safe.

### Answered 2026-08-22

| # | Question | Answer |
|---|---|---|
| C1 | Should Tín Phát default to `TINPHAT_ADS`? | **Yes** — every Tín Phát order converts at 7.5% regardless of the note. DEC-009. Its historical figures now need no migration. |
| C5 | Which line types count toward products, sales, profit, order count? | Money-bearing non-product lines **do** count toward sales and profit, not toward product count, and every one goes to a manual review queue where it is kept or excluded. DEC-010. |
| C6 | Can staff edit `Diễn giải`? | **Yes.** ERP default stays; staff edit only for ADS orders. DEC-011. |

### Still open

| # | Question | Default while unanswered | Needed by |
|---|---|---|---|
| C7 | Historical ADS profit for **Hoàng and Kiên only** (C1 removed Tín Phát from scope): ignore it, or enter the 14 monthly figures as migration data? Ignoring credits them 837,503 thousand VND (6.0%) more converted revenue over 8 months, ≈3.0 million VND in bonus. | Nothing applied; the reconciliation report states the difference rather than hiding it | **GATE-01** |
| C4 | 408 raw rows carry a non-zero `Chiết khấu` with no matching report column. Deduct from sales or from profit? | Carried through untouched and surfaced in the review queue — not silently applied either way | TASK-107 |
| C2 | Why do the Nội thành / Gia dụng sheets divide every total by 2? | Sum once; report the difference against the sample | TASK-404 (Phase 4 channel sheets) |
| C3 | Commission rule — the note says a target-based tier, the numbers say per-employee-per-month. | Load the observed table as data | TASK-403 |
| C8 | Does product count exclude money-bearing non-product lines? DEC-010 kept the sample workbook's behaviour without separate confirmation. | Excluded, as the sample does | GATE-01 |

Also flagged, not blocking: the monthly total in the sample Summary omits 60.0%
of converted revenue (`05 §A2`), and Kiên carries the identical hand-typed ADS
figure `7565` across three consecutive months (`05 §B2`).

## Micro Tasks (Inline)

Canonical checklist:
`governance/templates/MICRO_TASK_CHECKLIST.md`

### MICRO-003 — Architecture Decision Records
Status:
DONE

Checklist Reference:
`governance/templates/MICRO_TASK_CHECKLIST.md`

Evidence Summary:
E1 — `docs/adr/ADR-001-architecture-and-stack.md`,
`ADR-002-three-layer-data-model-and-audit.md`,
`ADR-003-currency-unit-standard.md` exist and follow `docs/adr/README.md`
naming and section structure.

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

- **RISK-01 — The ADS keyword has no data to stand on.** The string "ADS"
  occurs 0 times in the raw sales book and 0 times in the report workbook. The
  keyword rule is built to specification, but it only starts matching once data
  entry changes. DEC-009 covers the largest share — Tín Phát's 1,108 orders
  (12.7%) classify as ADS from the employee default rather than the keyword —
  so what remains unmarked is ADS work done by the other salespeople.
  Mitigation: manual override at OrderID level with audit trail; the tool
  reports how many orders matched the rule on each import so a month of silent
  zeroes is visible rather than assumed correct.

- **RISK-02 — RESOLVED 2026-08-22.** Tín Phát defaults to `TINPHAT_ADS`
  (DEC-009), so its 7.5% is preserved and no figure moves. Residual: marking an
  order ADS *lowers* converted revenue (5.5% divides into a larger number than
  7.5%), so an over-eager ADS marker costs a salesperson money. The review
  queue must surface newly-ADS orders, not just newly-PERSONAL ones.

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
  recorded 8 tactical decisions and 4 active risks. Then completed TASK-002
  (six analysis documents, backed by a re-runnable evidence extractor) and
  TASK-003 (three ADRs). Held at GATE-00.

## Next Session

Recommended Session:
S001 — Phase 1, TASK-101 onward

Purpose:
Begin the calculation engine, once GATE-00 is approved. The open questions run
alongside on the defaults recorded above; C1, C5 and C7 must be answered before
GATE-01 closes, because that is the point where the numbers become publishable.

Files to read first:
- `PROJECT/PROJECT_PROGRESS.md`
- `PROJECT/PROJECT_PROFILE.md`
- `PROJECT/PROJECT_DECISIONS.md`
- `docs/spec/Dac_ta_cong_cu_bao_cao_kinh_doanh.docx`
- `docs/analysis/`
