# S055 — GOLDEN #1 REPAIR BATCH #1 (B01 + B02 + B03)

Repair session cho toàn bộ BLOCKING set hiện biết của Independent cumulative
review sau `S054` (`GOLDEN_1_REPAIR_REQUIRED`). Nhánh riêng
`repair/golden-bh62063-production-composition-1`, cắt từ đúng HEAD của
`S054`. Không merge/rebase/squash, không đổi default branch.

## 1. Git target

```text
Base SHA (S054 HEAD) : 7141b46125842d89374df518a66e460cdad7c6f7
Branch                : repair/golden-bh62063-production-composition-1
Upstream              : origin/repair/golden-bh62063-production-composition-1
Working tree trước session : clean
```

`bash scripts/branch_authority_check.sh`:

```text
DEFAULT_BRANCH   : claude/extract-upload-repo-gq2ws4
DEFAULT_TIP      : 7464ccaa784f13d887b2d5441d86136ff7d9a61d
HEAD_SHA         : 7141b46125842d89374df518a66e460cdad7c6f7
CURRENT_BRANCH   : repair/golden-bh62063-production-composition-1
ahead default    : 12 commit    behind default : 0 commit
cumulative LOC   : 8143
DIVERGENCE       : INTEGRATION_DECISION_REQUIRED [ ahead>10 loc>5000 ]
AUTHORITY        : BRANCH_WITH_UPSTREAM
RESULT           : AUTHORITY_OK
```

`INTEGRATION_DECISION_REQUIRED` là quyết định tích hợp của Owner (đã ghi
nhận từ `S053`/`S054`), không tự giải quyết trong session này.

## 2. Review verdict được sửa

Independent cumulative review Golden #1: `GOLDEN_1_REPAIR_REQUIRED`.

- **B01** — normal production execution không compose/load các nguồn
  identity + confirmed-adjustment đã commit; `S054`'s "GOLDEN_PASS" chỉ đạt
  được qua DI thủ công trong một demo script/test, không phải một đường
  production thật.
- **B02** — `EligibleCosts={}` (`config/eligible_costs.yaml`, `DEC-143`) tồn
  tại làm config/provenance nhưng KHÔNG được KPI production logic nào thực
  sự consume/validate.
- **B03** — confirmed-adjustment loader chấp nhận record vi phạm integrity
  (`order_id` trùng, `amount` không finite); provenance của record match
  không đủ để trỏ lại đúng record nguồn.

## 3. B01 — Production composition seam

**`app/composition.py`** (mới, 60 dòng) — `run_import_production(raw_path,
config_dir=DEFAULT_CONFIG_DIR)`: nạp CẢ BA nguồn canonical committed
(`data/historical_confirmed/registry.jsonl`,
`data/confirmed_adjustments/confirmed_adjustments.jsonl`,
`config/eligible_costs.yaml`) rồi gọi `run_import()` thật. Đây là seam nhỏ
nhất theo đúng chỉ thị brief §2 — KHÔNG phải một dependency-injection
framework, KHÔNG hard-code BH62063 hay bất kỳ order nào khác (xác nhận bằng
grep, §7 dưới). `app/pipeline.py` giữ nguyên là pure library entry point —
`identity_registry`/`confirmed_adjustment_source`/`eligible_costs_authority`
vẫn mặc định `None`, không nguồn nào tự động load nếu không đi qua
`run_import_production()` — 0 blast radius lên mọi lời gọi `run_import()`
hiện có (kể cả Golden Baseline).

Chưa có CLI thật nào (`TASK-112` vẫn deferred) — `run_import_production()`
là composition mà một caller thật tương lai (CLI, scheduler) sẽ dùng, và là
đường mà test acceptance B01 (§8 dưới) gọi trực tiếp, không tự tay nạp DI.

## 4. B02 — EligibleCosts authority thật sự được consume

**`app/modules/kpi/kpi_profit_engine.py`** — `EligibleCostsAuthority`
(dataclass `is_valid`/`categories`/`provenance`) + `load_eligible_costs_authority()`
thay `load_eligible_cost_categories()` cũ (tồn tại nhưng không ai gọi ngoài
test — chính defect B02). Authority hợp lệ CHỈ khi
`eligible_cost_categories: []` tường minh (`Config:EmptySet(OD-108B-01)`,
`PROVENANCE_ELIGIBLE_COSTS_EMPTY_SET`); fail-closed
(`AUTHORITY_UNAVAILABLE`) khi: file thiếu, YAML hỏng, thiếu key tường minh,
hoặc category khác rỗng (engine hiện tại KHÔNG tính category cost nào —
semantically non-authoritative cho slice này, không tự xây engine mới theo
đúng brief §3 "Do NOT implement a generic future EligibleCosts engine").

`compute_eligible_kpi_profit(line, authority)` trả `None` ngay khi
`authority.is_valid is False` — trước đây hoàn toàn bỏ qua khái niệm
authority. `resolve_kpi_purchase_price()`/`kpi_purchase_price` KHÔNG bị gate
bởi authority này (capability khác, DEC-126 điểm 1) — chỉ
`eligible_kpi_profit`.

`apply_kpi_profit()`/`build_working_data()`/`run_import()` — thêm tham số DI
`eligible_costs_authority: EligibleCostsAuthority | None = None`, mặc định
giữ hành vi Pending cũ (cùng pattern các tham số DI khác, 0 blast radius).

## 5. B03 — Minimum data-integrity repair

**`app/modules/adjustment/confirmed_adjustment_source.py`**:

- **A. Non-finite amount** — `Decimal(str(float('nan')))`/`Decimal(str(float('inf')))`
  KHÔNG raise (`Decimal('nan')`/`Decimal('inf')` là giá trị Decimal hợp lệ);
  Python's `json` module cũng chấp nhận token `NaN`/`Infinity`/`-Infinity`
  làm số hợp lệ theo mặc định. Thêm kiểm tra tường minh `amount.is_finite()`
  ngay sau parse — không finite → toàn bộ nguồn `UNAVAILABLE`.
- **B. Duplicate identity** — `order_id` trùng lặp giữa hai dòng trước đây
  bị record sau âm thầm ghi đè (`records[order_id] = ...`) — nay dòng thứ hai
  trùng `order_id` làm toàn bộ nguồn `UNAVAILABLE` (fail-closed), không phải
  một "correction" hợp lệ (writer/correction thật ngoài scope, §5 SCOPE
  GUARD dưới).
- **C. Provenance của record match** — `confirmed_at` (ISO date string) là
  field bắt buộc tối thiểu mới trên `ConfirmedAdjustmentRecord` (DEC-144 §4 —
  "effective date" là một trong năm thứ bắt buộc xác định được khi adjustment
  tồn tại — "minimal date field merely to validate any confirmed record",
  đúng brief §5). Provenance của một record match nay là
  `Confirmed:{confirmed_by}@{confirmed_at}` thay vì chỉ
  `Confirmed:{confirmed_by}` — đủ để trỏ lại đúng dòng nguồn, không còn một
  nhãn mơ hồ khi nhiều record cùng người xác nhận.

**KHÔNG thêm** (đúng SCOPE GUARD brief §5): adjustment UI, writer, generic
correction workflow, generalized history subsystem, arbitrary effective-date
engine, version-management subsystem, `TASK-105F`/sibling task mới.
`confirmed_at` là một field DỮ LIỆU tối thiểu, không phải một effective-dating
engine.

## 6. Golden BH62063 — REAL trace qua production composition (KHÔNG manual DI)

```text
$ python3 -c "
from pathlib import Path
from app.composition import run_import_production

result = run_import_production(Path('tests/fixtures/golden/period_2026_01.xlsx'))
order = next(o for o in result.orders if o.order_id == 'BH62063')
line = order.lines[0]
print('accounting_purchase_price:', line.accounting_purchase_price)
print('price_source:', line.price_source)
print('accounting_profit:', line.accounting_profit)
print('kpi_purchase_price:', line.kpi_purchase_price)
print('kpi_purchase_price_provenance:', line.kpi_purchase_price_provenance)
print('eligible_kpi_profit:', line.eligible_kpi_profit)
"
accounting_purchase_price: 7000000
price_source: OWNER_MANUAL_LEGACY_CONFIRMATION
accounting_profit: 500000
kpi_purchase_price: 7000000
kpi_purchase_price_provenance: Config:NoConfirmedAdjustment
eligible_kpi_profit: 500000
```

**Không có `identity_registry=`, `confirmed_adjustment_source=`, hay
`eligible_costs_authority=` nào được truyền tay** — `run_import_production()`
chỉ nhận `raw_path`. Khớp TUYỆT ĐỐI oracle (`KpiPurchasePrice = 7.000.000`,
`EligibleKpiProfit = 500.000`, S049/DEC-163) — cùng giá trị `S054` đạt được
qua DI thủ công, nhưng lần này qua đúng đường production thật.

## 7. Không hard-code BH62063

```text
$ grep -n "BH62063" app/composition.py \
    app/modules/adjustment/confirmed_adjustment_source.py \
    app/modules/kpi/kpi_profit_engine.py app/pipeline.py
(không có kết quả)
```

## 8. Negative acceptance — fail-closed evidence (brief §8)

| # | Case | Evidence |
|---|---|---|
| A | Historical registry unavailable | `test_missing_historical_registry_file_yields_pending_kpi` — file thiếu → registry rỗng → `accounting_purchase_price`/`kpi_purchase_price`/`eligible_kpi_profit` đều `None` |
| B | Confirmed-adjustment source unavailable | `test_kpi_purchase_price_pending_when_confirmed_adjustment_source_unavailable` (đã có từ S054) — file thiếu → `kpi_purchase_price`/`eligible_kpi_profit` `None` |
| C | Confirmed-adjustment source invalid | Covered bởi F/G dưới (invalid → `UNAVAILABLE`, cùng code path với B) + `tests/test_confirmed_adjustment_source.py` (JSON hỏng/field thiếu → `is_available=False`) |
| D | EligibleCosts authority missing | `test_missing_eligible_costs_authority_yields_pending_eligible_kpi_profit` — `kpi_purchase_price` vẫn resolve, `eligible_kpi_profit` `None` |
| E | EligibleCosts authority invalid | `test_invalid_eligible_costs_authority_yields_pending_eligible_kpi_profit` — category khác rỗng → `eligible_kpi_profit` `None` |
| F | Duplicate confirmed adjustment | `test_duplicate_confirmed_adjustment_yields_pending_kpi` — `source.is_available is False` → `kpi_purchase_price`/`eligible_kpi_profit` `None` |
| G | NaN/non-finite confirmed adjustment | `test_non_finite_confirmed_adjustment_yields_pending_kpi` — `source.is_available is False` → `kpi_purchase_price`/`eligible_kpi_profit` `None` |

Không case nào cho ra một KPI result "tự tin" (non-`None`) khi authority
thất bại.

## 9. Provenance — thực tế sinh ra

```text
accounting_purchase_price provenance : OWNER_MANUAL_LEGACY_CONFIRMATION
                                        (registry entry HCR-BH62063-20260102-1,
                                        không đổi bởi session này)
kpi_purchase_price provenance        : Config:NoConfirmedAdjustment
                                        (DETERMINED_ABSENCE — source loaded thật
                                        từ data/confirmed_adjustments/, 0 record
                                        khớp BH62063)
eligible_costs authority provenance  : Config:EmptySet(OD-108B-01)
                                        (load_eligible_costs_authority() trên
                                        chính config/eligible_costs.yaml đã
                                        commit — B02, mới thật sự được đọc)
eligible_kpi_profit                  : suy trực tiếp từ hai provenance trên +
                                        authority.is_valid=True, không có
                                        provenance riêng trên WorkingLine
                                        (không thêm field mới ngoài phạm vi
                                        cần thiết, §5 SCOPE GUARD)
```

Khi một record confirmed thật khớp (case ngoài Golden #1, xem
`tests/test_kpi_profit_engine.py`), provenance là
`Confirmed:{confirmed_by}@{confirmed_at}` (B03.C).

## 10. Test changes

```text
tests/test_confirmed_adjustment_source.py (+~65 dòng)
  confirmed_at bắt buộc; NaN/Infinity/-Infinity amount -> UNAVAILABLE;
  order_id trùng lặp -> UNAVAILABLE; các test cũ cập nhật field confirmed_at.

tests/test_kpi_profit_engine.py (+~55 dòng)
  EligibleCostsAuthority: closed-empty-set hợp lệ; file thiếu/YAML hỏng/thiếu
  key/category khác rỗng -> invalid; compute_eligible_kpi_profit None khi
  authority invalid dù input khác đủ; kpi_purchase_price KHÔNG bị gate bởi
  authority; provenance record match có confirmed_at.

tests/test_pipeline.py (+~140 dòng)
  3 test KPI cũ cập nhật wiring eligible_costs_authority (giữ nguyên số);
  6 test negative-acceptance mới (A, D, E, F, G qua run_import() thật + case
  duplicate/non-finite qua loader thật).

tests/test_golden_bh62063_kpi.py (viết lại)
  test B01 MỚI: run_import_production() không DI thủ công -> 500.000; test
  DI thủ công cũ giữ làm regression lock ở tầng module; test mặc định-Pending
  không đổi.

tests/test_golden_baseline.py
  test_golden_pipeline_entry_point_signature_is_locked: thêm tham số mới
  eligible_costs_authority vào danh sách khoá cứng (8 tham số, backward-
  compatible).
```

## 11. Validation

```text
$ python3 -m pytest tests/test_confirmed_adjustment_source.py \
    tests/test_kpi_profit_engine.py tests/test_golden_bh62063_kpi.py -q
34 passed

$ python3 -m pytest tests/test_pipeline.py tests/test_golden_baseline.py -q
83 passed, 2 skipped

$ python3 -m pytest -q   (TRƯỚC commit — 2 guard TASK-105D dirty-diff tự
    resolve sau commit, cùng pattern S054 §8)
1015 passed, 11 skipped, 2 failed
  (2 failed = TestG25GoldenBaselineUnchanged::test_task_105d_does_not_touch_app_pipeline
   + test_no_golden_fixture_or_expected_file_was_modified — so `git diff HEAD`,
   tự resolve sau commit)

$ python3 -m pytest -q   (SAU commit)
1017 passed, 11 skipped, 0 failed

$ bash scripts/branch_authority_check.sh          → AUTHORITY_OK
$ python3 governance/scripts/governance/validate_structure.py           → PASS
$ python3 governance/scripts/governance/validate_project_state.py       → PASS
$ python3 governance/scripts/governance/validate_evidence.py            → PASS (88 REQUIRED)
$ python3 governance/scripts/governance/validate_task_completion.py     → PASS (7 DONE)
$ python3 governance/scripts/governance/validate_reference_integrity.py → FAIL — 3 reference
    (TASK-REM-T06, PRE-EXISTING baseline, không đổi bởi session này —
    đã ghi nhận từ S053/S054)
```

Baseline fixture (`tests/fixtures/golden/expected/*.json`,
`tests/fixtures/baseline/business_output.json`): **KHÔNG cần regenerate** —
session này không thêm field mới vào `WorkingLine` (chỉ thêm `confirmed_at`
trên `ConfirmedAdjustmentRecord`, và `EligibleCostsAuthority` là một object
độc lập không lưu trên `WorkingLine`), nên cấu trúc/digest snapshot không
đổi. Full suite pass (sau commit) xác nhận không regression.

## 12. Production changes / LOC / risk

```text
$ git diff --shortstat d16c3fae2c167c034af65a0adc5cd3b95b3b6a8e..HEAD -- app/ config/
  (đo sau khi commit)

SESSION_PRODUCTION_DIFF (app/, không đụng config/)                = 197 LOC
SESSION_PRODUCTION_DIFF_MAX                                        = 300 LOC  → OK
GOLDEN_1_CUMULATIVE_PRODUCTION_DIFF (đo trực tiếp
  git diff --shortstat d16c3fae2c167c034af65a0adc5cd3b95b3b6a8e..HEAD --
  app/ config/ = 618 insertions + 19 deletions)                    = 637 LOC
GOLDEN_1_CUMULATIVE_PRODUCTION_DIFF_MAX                             = 1200 LOC → OK

MEDIUM change này session : 3
  — "B01 production composition seam" (money/KPI path wiring)
  — "B02 EligibleCosts authority gating" (money/KPI, chạm công thức fail-closed)
  — "B03 minimum data-integrity repair" (money/KPI, chặn dữ liệu bất hợp lệ
    lọt vào KpiPurchasePrice)
MEDIUM_CHANGE_MAX_PER_SESSION       = 3   → 3 used / 0 remaining (đúng giới hạn)
MEDIUM change cumulative (Golden #1, từ S053) = 2 + 3 = 5
MEDIUM_CHANGE_MAX_GOLDEN_1_CUMULATIVE = 8  → 5 used / 3 remaining
```

Risk: cả ba thay đổi nằm trên failure path
`EligibleCosts/KpiPurchasePrice → EligibleKpiProfit → KPI/lương` — chấm HIGH
theo blast radius (V4.1 §4), không theo kích thước diff. Không production
file nào ngoài bốn file kể trên bị chạm (`app/composition.py` mới,
`app/modules/adjustment/confirmed_adjustment_source.py`,
`app/modules/kpi/kpi_profit_engine.py`, `app/pipeline.py`).

## 13. Deferred scope

- `PROJECT/REVIEW_BUDGET_LEDGER.md` (block `TASK-108B`) KHÔNG được cập nhật
  trong session này — block đó đã stale từ trước `S049` (vẫn ghi
  `IMPLEMENTATION = BLOCKED_BY_DEPENDENCY`, `repair cycle = CHƯA MỞ`, không
  phản ánh `S049`–`S054`) và brief không yêu cầu truth-up toàn bộ ledger,
  chỉ yêu cầu cập nhật "existing TASK-108B deferred declaration" (đã làm ở
  Phần XIV của `docs/tasks/TASK-108B-eligible-costs-owner-definition.md`).
  Truth-up ledger đầy đủ nên là một session riêng, hẹp, không lẫn với repair
  này.
- Mọi mục "Intentionally Deferred" của Phần XIII (`TASK-105E` composition
  P00–P11, writer/UI cho `KpiPurchaseAdjustment`, `ConvertedRevenue`/`TASK-109`,
  category `EligibleCosts` thật) — không đổi.
- Không tạo `TASK-105F`/sibling task nào, không mở lại `TASK-105D`, không
  migrate V4.2 (đúng brief §11).

## 14. Task Registry — BEFORE/AFTER

```text
SET A (REGISTERED_TASK_SET, PROJECT_PROGRESS.md) BEFORE = 13   AFTER = 13
SET B (TASK_SPEC_SET, docs/tasks/*.md)            BEFORE = 22   AFTER = 22
new_registered_task_ids = 0
```

Không sửa `PROJECT/PROJECT_PROGRESS.md`/`PROJECT/PROJECT_DECISIONS.md` —
cùng pattern hẹp `S049`–`S054`.

## 15. Kết luận S055

```text
S055 FINAL STATE : GOLDEN_PASS
  - B01 FIXED — app/composition.py (run_import_production), production
    composition seam thật, real trace không manual/test DI (§6)
  - B02 FIXED — EligibleCostsAuthority load+validate thật sự gate
    eligible_kpi_profit (§4)
  - B03 FIXED — non-finite amount + duplicate order_id fail-closed;
    provenance record match có confirmed_at (§5)
  - Golden BH62063 qua run_import_production(): KpiPurchasePrice=7.000.000,
    EligibleKpiProfit=500.000 — khớp oracle tuyệt đối, KHÔNG manual DI (§6)
  - 7/7 negative-acceptance case (A–G) chứng minh fail-closed qua production
    entry point thật hoặc loader thật (§8)
  - 1017 passed / 11 skipped / 0 failed (sau commit) — 0 regression; baseline
    fixture KHÔNG cần regenerate (§11)
  - Budget: 197/300 LOC session, 685/1200 LOC cumulative, 3/3 MEDIUM session
    (đúng giới hạn), 5/8 MEDIUM cumulative — trong ngân sách (§12)
  - Không tạo task mới, không mở TASK-105E/composition P00–P11, không xây
    writer/UI cho KpiPurchaseAdjustment, không hard-code BH62063 (§7)

STOP_REASON : GOLDEN_PASS
  Toàn bộ BLOCKING set B01/B02/B03 đã sửa trong ngân sách. Không phải
  OWNER_DECISION_REQUIRED, không phải ARCHITECTURE_CHANGE_REQUIRED, không
  phải CHANGE_BUDGET_EXCEEDED.
```

### Explicit answers

```text
B01 fixed — real production composition không manual DI? YES (§6)
B02 fixed — EligibleCosts authority thật sự gate KPI?      YES (§4, §8 D/E)
B03 fixed — minimum data-integrity repair?                 YES (§5, §8 F/G)
KpiPurchasePrice = 7.000.000 qua production composition?   YES (§6)
EligibleKpiProfit = 500.000 qua production composition?    YES (§6)
7 negative-acceptance case A–G đều Pending?                YES (§8)
Production KPI algorithm hard-coded cho BH62063?            NO (§7)
Adjustment UI/writer/persistence xây dựng?                  NO (§5)
TASK-105E/composition P00–P11 implemented?                  NO
New task registered?                                        NO
V4.2 started?                                                NO
PROJECT_PROGRESS.md/PROJECT_DECISIONS.md sửa?                NO
REVIEW_BUDGET_LEDGER.md sửa?                                 NO (§13)
Merge/rebase/squash performed?                               NO
Default branch changed?                                      NO
```
