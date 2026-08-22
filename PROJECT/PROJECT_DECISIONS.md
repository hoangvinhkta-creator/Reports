# PROJECT DECISIONS

Use this file for tactical project decisions that are important across sessions
but are not significant enough for a full ADR.

## DEC-001

Date:
2026-08-22

Task:
TASK-000

Decision:
Move `CLAUDE.md`, `PROJECT/`, `docs/` and `governance/` from
`AI_ENGINEERING_CONSTITUTION_TEMPLATE_V3_2_FINAL_COMPACT/` to the repository
root using `git mv`.

Reason:
The V3.2 compact layout defines `CLAUDE.md` as the governance entry point at
root and every governance path as `governance/...` relative to root. Nested one
level deep, none of those canonical paths resolved.

Impact:
74 file renames, no content change. All governance cross-references now resolve.

Can Revisit After:
Never — this is the framework's own required layout.

## DEC-002

Date:
2026-08-22

Task:
TASK-001

Decision:
ADS lead source is identified by the keyword "ADS" appearing in the
`Diễn giải` column, exactly as specification section 5 defines. Staff will
begin typing "ADS" into that column from now on.

Reason:
Owner's decision. The raw file has no separate `Ghi chú` column, so
`Diễn giải` is the only note field available — which is the fallback the
specification itself names in section 13.

Impact:
Historical data for 01.2026 through 06.2026 contains zero ADS markers and will
classify entirely as PERSONAL. Historical ADS orders must be corrected through
manual override. The keyword list is configuration, not code, so adding a
second marker later costs no development.

Can Revisit After:
The first month of data entered under the new convention.

## DEC-003

Date:
2026-08-22

Task:
TASK-001

Decision:
Purchase price stays empty (Pending) on import. It is never inferred from the
ERP profit column. A `PriceProvider` interface is defined now so an external
price-list tool can fill it later; manual entry stays available on every line
regardless of what the provider returns.

Reason:
Owner's decision. Specification section 10 is explicit: if there is no purchase
price, mark it Missing/Pending and do not guess.

Impact:
KPI profit and converted revenue are incomplete until prices arrive. The tool
must render Pending as Pending — a missing price must never be treated as zero,
because zero silently produces a profit equal to the full sale price.

Can Revisit After:
The external price tool exists.

## DEC-004

Date:
2026-08-22

Task:
TASK-001

Decision:
Raw sales staff `Mr Quý`, `Mr Vinh` and `Đức Hiệp` map to a single normalized
unit, `Nội thành`. `Gia dụng` is a product grouping inside `Nội thành`, not a
separate salesperson. `Fanpage` is out of scope.

Reason:
Owner's decision, consistent with the sample report: those three names carry
the highest raw line counts and never appear as employee sheets, while the
`Nội thành` sheet's monthly sales are of the same order as their combined total.

Impact:
Employee mapping is many-to-one and must live in configuration, with `active`
and effective dates, so joiners and leavers never require a code change. Any
raw NVBH value with no mapping goes to the review queue — never silently
dropped, never silently invented.

Can Revisit After:
Anytime — this is configuration by construction.

## DEC-005

Date:
2026-08-22

Task:
TASK-001

Decision:
The MVP is a multi-user web application with central persistence, not a local
script or a single-session Streamlit app.

Reason:
Owner's decision: used daily, by several people, viewing and editing together,
"like a Google Sheet".

Impact:
Authentication and roles become mandatory at Phase 2 rather than optional —
the audit trail required by specification section 19 needs a real `ChangedBy`.
Backup becomes mandatory once the database holds overrides that exist nowhere
else.

Can Revisit After:
GATE-03.

## DEC-006

Date:
2026-08-22

Task:
TASK-001

Decision:
Money is stored canonically in whole VND as `Decimal`. Display unit is
configuration, defaulting to thousands of VND to match the existing report.

Reason:
The raw file uses full VND (8000000) and the report workbook uses thousands
(11770). Mixing the two in storage is how a report ends up a thousand times
wrong. Float is unacceptable for money that determines pay.

Impact:
Every import and export crosses an explicit unit boundary that must be tested.

Can Revisit After:
Never — this is a correctness constraint.

## DEC-007

Date:
2026-08-22

Task:
TASK-002

Decision:
The six formula defects found in the sample workbook are documented and
reported, but not reproduced. The tool computes the correct figure and, where
the result differs from the sample report, states why.

Reason:
The tool's purpose is a correct report, not a faithful copy of a spreadsheet
that miscounts. Silently reproducing a known defect would make the defect
permanent and untraceable.

Impact:
Product counts will not match the sample report exactly — the sample subtracts
a percentage from a quantity and yields fractional products (387.6). Every such
difference is listed in `docs/analysis/05_EXCEPTIONS.md` for owner review.

Can Revisit After:
Owner review at GATE-00. If the owner wants bug-for-bug parity for a specific
figure, that becomes a configuration flag, not a silent default.

## DEC-008

Date:
2026-08-22

Task:
TASK-001

Decision:
Real sample data stays out of version control (`.gitignore` excludes
`data/samples/`). Tests run against anonymized fixtures derived from it.

Reason:
Both workbooks carry customer names, mobile numbers, delivery addresses and
device serial numbers, plus employee salary figures. Once committed, that is
permanent in git history.

Impact:
Anyone cloning the repository must supply their own copy of the source
workbooks. Test fixtures must be generated with personal fields replaced, and
that generator is itself part of the deliverable.

Can Revisit After:
Never while the files contain personal data.
