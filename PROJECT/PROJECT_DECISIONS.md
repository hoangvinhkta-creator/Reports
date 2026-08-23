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

## DEC-009

Date:
2026-08-22

Task:
GATE-00 — resolves open question C1

Decision:
Every order raised by `Tín Phát` converts at the ADS rate (7,5 %), whether or
not the note contains "ADS". Implemented as `default_lead_source: TINPHAT_ADS`
on that employee in `config/employees.yaml`, not as a hard-coded rate.

Reason:
Owner's decision. `Tín Phát` is the company's own site/ads account — every lead
it handles is company-generated by definition, so there is nothing for a
salesperson to mark. This also matches the sample workbook, where `Tín Phát`
has always converted at 7,5 % with no split formula.

Impact:
The employee default sits **below** the ADS keyword rule and **above** the
global default in the priority chain, so it can only raise an order to ADS and
never demote one the keyword matched. Manual override still wins over both.

`Tín Phát` will show as 100 % ADS in the Personal/ADS split — which is the
accurate picture, not a distortion. Historical figures for `Tín Phát` need no
migration: they were already 7,5 %.

Nothing about this is specific to `Tín Phát` in code. Any employee or channel
can be given a default source in configuration.

Can Revisit After:
Anytime — it is one line of configuration.

## DEC-010

Date:
2026-08-22

Task:
GATE-00 — resolves open question C5

Decision:
Non-product lines that carry money — `Chi phí vận chuyển`, `Chi phí lắp đặt`,
`Chênh VAT`, `Chi phí giao hộ`, `Phí đổi trả` — **do** count toward the
salesperson's sales and profit. They do not count as products and do not create
a separate order. Every such line is surfaced for manual review, where the
reviewer either keeps it or removes it from the report.

Reason:
Owner's decision: *"tất cả dòng phụ nếu có liên quan đến giá trị tiền hàng vẫn
thêm vào doanh số từng nhân viên nhưng sẽ được duyệt thủ công bằng cách xoá
dòng hoặc giữ lại dòng"*.

Impact:
"Removing a line" is a soft exclusion, never a delete: RAW is immutable per
ADR-002. It sets `excluded_from_report` with a reason and an audit entry, and
is reversible. Roughly 1.250 lines in the six-month sample fall into this
category, so the review screen must handle them in bulk — line by line would
be unusable.

Product count keeps the sample workbook's existing behaviour of excluding these
lines. Not separately confirmed by the owner; flagged for GATE-01.

Can Revisit After:
GATE-01.

## DEC-011

Date:
2026-08-22

Task:
GATE-00 — resolves open question C6

Decision:
`Diễn giải` stays as the ERP writes it by default (`"Bán hàng " + Tên KH`).
Staff edit it only when an order is ADS. The field is editable — confirmed by
the owner — so the keyword rule is workable.

Reason:
Owner's decision. This removes RISK-01's main unknown: whether the marker could
be written at all.

Impact:
Most orders keep an auto-generated note, so an empty or template note is the
normal case and must never be treated as suspicious. Only a note edited to
contain the keyword changes anything.

Because marking is an opt-in action a person must remember, a month with zero
ADS orders stays a review-queue warning (RISK-01): with `Tín Phát` now defaulted
to ADS by DEC-009, a zero count means no *other* salesperson marked anything,
which is possible but worth seeing rather than assuming.

Can Revisit After:
The first month under the new convention.

## DEC-012

Date:
2026-08-22

Task:
GATE-00 — resolves open question C7

Decision:
Historical ADS profit for Hoàng and Kiên (01–08.2026) is entered as 14
per-employee-per-month figures, flagged as migration data and clearly separated
from figures the ADS rule produced. The values are the ones already recorded in
`docs/analysis/04_HARDCODED_VALUES.md` §2 and `docs/analysis/06_ADS_RULE_VERIFICATION.md` §8.

Reason:
Owner's decision. Per-order recovery is impossible — nothing in either workbook
records which orders were ADS, and `3770+16190` in Hoàng's May formula shows the
figures were summed by hand from a source outside the system. Entering the
monthly totals costs 14 cells once and makes the tool's output match the
existing report exactly, so nobody has to explain a 6.0% jump in two people's
converted revenue.

Impact:
- `conversion_engine` needs a migration input path: a per-(employee, month)
  ADS profit amount that bypasses order-level classification.
- Migration figures must be visibly distinct from rule-derived ones in the UI
  and in the export. They are an assertion about the past, not a computation,
  and must never be mistaken for one.
- The two paths must be mutually exclusive per employee-month. If a month has
  both a migration figure and orders classified ADS by the rule, that is a
  conflict for the review queue, not a sum.
- A cut-over month must be recorded in configuration: migration applies before
  it, the rule after it.
- Reconciliation target: with the 14 values loaded, total converted revenue for
  Hoàng and Kiên across 01–08.2026 must equal **13.883.242** thousand VND. This
  becomes a REQUIRED check on TASK-108.

Can Revisit After:
Once the ADS convention has been running long enough that 2026 history stops
mattering.

## DEC-013

Date:
2026-08-22

Task:
GATE-00 — resolves open question C8

Decision:
Money-bearing non-product lines are excluded from the product count, confirming
the assumption DEC-010 carried. `Tổng số SP` is kept as a Summary column to
match the existing report, but it is demoted: no feature is built on it and it
is not a reconciliation criterion at any gate.

Reason:
Owner's decision — *"loại số SP ra. có vẻ dữ liệu này không cần thiết"*.

Impact:
Removes the sample workbook's fractional product counts (387,6 / 178,8 / 62,6),
which came from subtracting a percentage from a quantity — see
`docs/analysis/05_EXCEPTIONS.md` §A1. The tool's product count will be a whole
number and slightly higher than the sample's.

Because the metric is low value, that difference does not need explaining
line by line at GATE-01. Every other reconciliation difference still does.

Can Revisit After:
Anytime — dropping the column later costs nothing.

## DEC-014

Date:
2026-08-22

Task:
GATE-00 — resolves open question C4

Decision:
`Chiết khấu` is deducted from sales:

```
TotalSales = SellPrice × Quantity − Discount
```

Reason:
Owner's decision. Verified against the raw file: in all 408 discounted rows
`Doanh số bán` equals `Đơn giá × SL` exactly and never the discounted figure, so
the ERP column is gross and the discount has not already been applied. Deducting
it is a real correction, not a double count.

Impact:
Six-month total: 36.750 thousand VND across 408 rows — 0,03 % of company sales.
Concentrated on one person: Ly has 302 of the 408 rows and 26.300 thousand,
0,39 % of her sales. Nobody else exceeds 0,07 %.

**Open assumption, flagged for GATE-01:** the discount is also deducted from
profit by the same amount, so
`EligibleKpiProfit = (SellPrice − KpiPurchasePrice) × Quantity − Discount − EligibleCosts + OtherKpiAdjustment`.
The owner said "deduct from sales" and did not speak to profit. Reducing sales
without reducing profit would report a margin higher than the business actually
earned, which is the reading this project cannot take silently — a discount is
money given away. Stated here rather than assumed.

Can Revisit After:
GATE-01, on the profit half only.

## DEC-015

Date:
2026-08-22

Task:
GATE-00 — resolves open question C2

Decision:
The `/2` in the Nội thành and Gia dụng sheets is explained: those sheets carry a
per-day subtotal row **inside** the data region, so a plain `SUM` counts every
figure twice. Halving the total is a correct workaround for that layout.

The tool does not reproduce either the embedded subtotal rows or the halving.
Data rows stay data; subtotals are computed separately and, in the export,
emitted as Excel outline/group rows carrying an explicit `RowType` marker that
keeps them outside every `SUM` range.

Reason:
Owner explained the cause and asked for a better representation:
*"nếu có cách thể hiện khoa học hơn, hãy làm"*.

Impact:
- `docs/analysis/05_EXCEPTIONS.md` §A3 moves from "unexplained, needs investigation" to
  "explained, deliberately not reproduced".
- The halving was never wrong for the layout it lives in — but it is invisible.
  Anyone adding a row in the wrong place, or reading the sheet without knowing,
  gets a figure that is out by 2×. A `RowType` column makes the distinction
  something you can see and filter rather than something you have to know.
- Every total in the tool sums each figure exactly once, with no compensating
  divisor anywhere in the codebase. A `/2` appearing in aggregation logic is to
  be treated as a defect.

Can Revisit After:
Never — a hidden compensating divisor is not a design this project adopts.

## DEC-016

Date:
2026-08-22

Task:
GATE-00 — resolves open question C3

Decision:
Commission is driven by target achievement — paid on reaching and exceeding KPI.
Formalizing it is deferred to a later phase, as planned in TASK-403.

Reason:
Owner's decision. The observed rates (0,15 %–0,5 %, varying by person and month)
do not derive from any single tiered rule, so the policy has to be stated in
full before it can be encoded.

Impact:
Phase 1 loads the observed per-employee-per-month rate table as data, exactly as
it appears in the sample workbook. No tier logic is inferred or invented.
Commission figures the tool produces before TASK-403 reproduce history; they do
not predict what a new month should pay.

Can Revisit After:
TASK-403, once the full policy is stated.
