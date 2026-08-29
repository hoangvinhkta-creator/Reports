# S054 — GOLDEN #1 (BH62063) KPI VERTICAL SLICE

GOLDEN #1 VERTICAL DELIVERY LOOP #1, session #2 trên nhánh implementation
riêng của session này (`implementation/golden-bh62063-kpi-vertical-slice-1`,
tạo từ chính HEAD của `S053`). Kế tiếp `S053` (B0–B6 PASS, B7/B8/B9
NOT_REACHED, `STOP_REASON = ARCHITECTURE_CHANGE_REQUIRED`). Session brief lần
này mang authority mới: Codex architecture review kết luận full
`TASK-105B`/`105C`/`105E`/P01–P11 KHÔNG cần thiết cho path B7/B8 hiện tại —
một minimum slice ≤300 LOC là khả thi, dùng DEC-143 + DEC-144 đã APPROVED sẵn.

Mục tiêu duy nhất: đưa `BH62063` qua B7/B8/B9 bằng minimum implementation
được authorize, không mở `TASK-105E`/composition P00–P11, không xây workflow
xác nhận adjustment có persistence/UI.

## 1. Git target

```text
Required base SHA : 527b0abcd60d347d5efb5d05ee267dd21b461f71
HEAD trước session  : 527b0abcd60d347d5efb5d05ee267dd21b461f71 (khớp)
Branch              : implementation/golden-bh62063-kpi-vertical-slice-1
Upstream            : origin/implementation/golden-bh62063-kpi-vertical-slice-1
                       (0 ahead / 0 behind trước session)
Working tree trước session : clean
```

`git remote show origin` → HEAD branch thật = `claude/extract-upload-repo-gq2ws4`
(KHÔNG phải "main"). Nhánh của session này KHÔNG fork trực tiếp từ đó — nó
kế tục chuỗi `implementation/golden-bh62063-vertical-delivery-1` (S049–S053)
tại đúng SHA `527b0ab` mà session brief §0 yêu cầu.

`bash scripts/branch_authority_check.sh` (chạy trước commit, WORKTREE dirty
đúng — có thay đổi thật chưa commit):

```text
DEFAULT_BRANCH       : claude/extract-upload-repo-gq2ws4
DEFAULT_TIP          : 7464ccaa784f13d887b2d5441d86136ff7d9a61d
HEAD_SHA             : 527b0abcd60d347d5efb5d05ee267dd21b461f71
CURRENT_BRANCH       : implementation/golden-bh62063-kpi-vertical-slice-1
UPSTREAM             : origin/implementation/golden-bh62063-kpi-vertical-slice-1
ahead default        : 11 commit    behind default : 0 commit
cumulative LOC        : 6917
DIVERGENCE           : INTEGRATION_DECISION_REQUIRED [ ahead>10 loc>5000 ]
AUTHORITY            : BRANCH_WITH_UPSTREAM
RESULT               : AUTHORITY_OK
```

`INTEGRATION_DECISION_REQUIRED` (ghi nhận từ S053, nay kèm `ahead>10`) giữ
nguyên, không tự giải quyết — đúng chỉ thị brief §0: không merge/rebase/
squash, không đổi default branch. Đây là quyết định tích hợp của Owner,
không phải việc của session này.

## 2. Business authority — không phải suy diễn

`DEC-143` (`OD-108B-01`): `EligibleCosts = {}` CLOSED EMPTY SET có thẩm quyền;
`DeliveryCost` NOT ELIGIBLE FOR NOW; `OtherKpiAdjustment = 0` BY DEFINITION;
canonical `EligibleKpiProfit = (SellPrice − KpiPurchasePrice) × Quantity −
Discount` (đã chuẩn hoá số học, xác nhận lại ở `DEC-144` §1).

`DEC-144` (`OD-108B-02`): confirmed `KpiPurchaseAdjustment`, ba trạng thái
không được gộp — DETERMINED_ABSENCE (source loaded, 0 record khớp) ≠
SOURCE_UNAVAILABLE/UNKNOWN (source thiếu/hỏng/parse lỗi) ≠ ZERO. `DEC-144` §5
xác nhận tường minh: cơ chế confirmed-adjustment source là "deliverable cơ chế
nhỏ, thuộc phạm vi implementation của `TASK-108B`... KHÔNG cần thêm Owner
Decision".

Cả hai đã `APPROVED` từ 2026-08-27, trước session này — session brief chỉ
trích dẫn lại, không tạo authority mới.

## 3. Thiết kế

**`app/modules/adjustment/confirmed_adjustment_source.py`** (mới) —
`ConfirmedAdjustmentSource`/`ConfirmedAdjustmentRecord`/
`load_confirmed_adjustments_from_jsonl()`. Tách biệt HOÀN TOÀN khỏi
`AdjustmentResolver` (TASK-106, chỉ `suggested_amount`) — không import, không
gọi lẫn nhau. `is_available` phân biệt UNAVAILABLE (`records=None`: file
thiếu/không đọc được/một dòng bất kỳ parse lỗi — fail-closed) khỏi LOADED-rỗng
(`records={}`: DETERMINED_ABSENCE). File thiếu → UNAVAILABLE, KHÔNG "loaded
rỗng" (DEC-144 §3, xác nhận bằng test).

**`app/modules/domain/models.py`** — 3 field mới trên `WorkingLine`:
`kpi_purchase_price`, `kpi_purchase_price_provenance` (default `Pending`,
cùng pattern `price_source`), `eligible_kpi_profit`. Cùng 2 hằng
`KPI_PURCHASE_PENDING`/`KPI_PURCHASE_NO_CONFIRMED_ADJUSTMENT`. Không đụng
`accounting_purchase_price`/`price_source`/`accounting_profit` — capability
khác (DEC-126 điểm 1).

**`app/modules/kpi/kpi_profit_engine.py`** (mới, module mới) —
`resolve_kpi_purchase_price()` (3 nhánh: AccountingPurchasePrice Pending →
Pending; source None/unavailable → Pending; loaded → confirmed record hoặc
`Config:NoConfirmedAdjustment`), `compute_eligible_kpi_profit()` (công thức
canonical, `SUM(EligibleCosts)=0` + `OtherKpiAdjustment=0` theo DEC-143),
`load_eligible_cost_categories()` (đọc tường minh từ YAML, không hardcode
Python). `apply_kpi_profit()` set cả 3 field cùng lúc.

**`config/eligible_costs.yaml`** (mới) — `eligible_cost_categories: []` tường
minh + `excluded_by_authority` (DeliveryCost, KpiPurchaseAdjustment) ghi lại
lý do loại trừ theo DEC-143 Reason §1/§2 — giảm nhẹ rủi ro "tập rỗng bị đọc
nhầm thành fallback" mà chính DEC-143 đã cảnh báo.

**`data/confirmed_adjustments/confirmed_adjustments.jsonl`** (mới, thật, hiện
RỖNG — brief §3.A cho phép nội dung production ban đầu rỗng). File tồn tại
vật lý (không phải "chưa ai nghĩ tới"), loader xác nhận `is_available = True`
cho file rỗng này (DETERMINED_ABSENCE cho mọi order) — khớp đúng nhánh
Golden #1: "Matching confirmed adjustment: none".

**`app/pipeline.py`** — thêm bước 9b, ngay sau `apply_accounting_profit`
(bước 9), gọi `apply_kpi_profit(lines, confirmed_adjustment_source)`. Tham số
DI mới `confirmed_adjustment_source: ConfirmedAdjustmentSource | None = None`
trên cả `build_working_data()` và `run_import()` — optional, cùng vị trí
cuối cùng như `identity_registry`/`identity_resolver_factory` (S051). Mặc
định `None` → không nguồn nào wiring → toàn bộ KPI Pending, hành vi mặc định
của MỌI lời gọi `run_import()` hiện có (kể cả Golden Baseline) không đổi —
xác nhận bằng test `test_bh62063_default_run_import_without_kpi_wiring_is_still_pending`.

**Không có `BH62063` hard-code trong 5 file production trên** — xác nhận
bằng grep:

```text
$ grep -n "BH62063" app/modules/adjustment/confirmed_adjustment_source.py \
    app/modules/kpi/kpi_profit_engine.py app/modules/domain/models.py \
    app/pipeline.py config/eligible_costs.yaml
(không có kết quả)
```

## 4. Golden BH62063 — REAL trace qua production entry point

```text
$ python3 -c "
from pathlib import Path
from app.pipeline import run_import
from app.modules.product.identity.registry_store import load_registry_from_jsonl
from app.modules.adjustment.confirmed_adjustment_source import load_confirmed_adjustments_from_jsonl

registry = load_registry_from_jsonl(Path('data/historical_confirmed/registry.jsonl'))
adj_source = load_confirmed_adjustments_from_jsonl(Path('data/confirmed_adjustments/confirmed_adjustments.jsonl'))
print('adj_source.is_available:', adj_source.is_available)

result = run_import(Path('tests/fixtures/golden/period_2026_01.xlsx'), config_dir=Path('config'),
                     identity_registry=registry, confirmed_adjustment_source=adj_source)
order = next(o for o in result.orders if o.order_id == 'BH62063')
line = order.lines[0]
print('accounting_purchase_price:', line.accounting_purchase_price)
print('price_source:', line.price_source)
print('accounting_profit:', line.accounting_profit)
print('kpi_purchase_price:', line.kpi_purchase_price)
print('kpi_purchase_price_provenance:', line.kpi_purchase_price_provenance)
print('eligible_kpi_profit:', line.eligible_kpi_profit)
print('sell_price:', line.sell_price, 'discount:', line.discount, 'quantity:', line.quantity)
"
adj_source.is_available: True
accounting_purchase_price: 7000000
price_source: OWNER_MANUAL_LEGACY_CONFIRMATION
accounting_profit: 500000
kpi_purchase_price: 7000000
kpi_purchase_price_provenance: Config:NoConfirmedAdjustment
eligible_kpi_profit: 500000
sell_price: 7500000 discount: 0 quantity: 1
```

Khớp TUYỆT ĐỐI oracle (`KpiPurchasePrice = 7.000.000`, `EligibleKpiProfit =
500.000`, S049/DEC-163). Provenance trung thực: `Config:NoConfirmedAdjustment`
đúng nhánh DETERMINED_ABSENCE (source loaded thật, 0 record khớp BH62063).

**Mặc định (không truyền `confirmed_adjustment_source`/`identity_registry`)**
— xác nhận KHÔNG đổi so với `S053`: `None Pending None Pending None` cho cả
`accounting_purchase_price`/`price_source`/`accounting_profit`/
`kpi_purchase_price_provenance`/`eligible_kpi_profit` — 0 blast radius.

**Quan trọng — `accounting_profit` (500.000) trùng `eligible_kpi_profit`
(500.000) CHỈ vì `Discount = 0`, `Quantity = 1` ở đúng đơn hàng này** (S053
§6 đã cảnh báo trước). `tests/test_kpi_profit_engine.py` và
`tests/test_pipeline.py` (BH0004, `Quantity=2`, `Discount=50000`) chứng minh
hai field phân kỳ thật: `AccountingProfit = 200.000` nhưng
`EligibleKpiProfit = 150.000` trên cùng input.

## 5. Bảng boundary B0–B9 (cập nhật so với S053)

| Boundary | Status | Ghi chú |
|---|---|---|
| B0 Sales Input | PASS | Không đổi |
| B1 Identity Input | PASS | Không đổi |
| B2 Product Identity Resolution | PASS | Không đổi (S053) |
| B3 Price Request | N/A — BYPASSED_BY_DESIGN | Không đổi (S053, DEC-154 P00) |
| B4 Preferred Source "Tồn" | N/A — BYPASSED_BY_DESIGN | Không đổi (S053) |
| B5 Purchase Price | PASS (gộp vào B2) | Không đổi |
| B6 Provenance | PASS (gộp vào B2) | Không đổi |
| B7 KPI Input | **PASS (mới)** | `confirmed_adjustment_source` load thật từ file thật, wiring vào `run_import()` bước 9b — không stub/mock/bypass. |
| B8 KPI Calculation | **PASS (mới)** | `KpiPurchasePrice = 7.000.000` (`Config:NoConfirmedAdjustment`), `EligibleKpiProfit = 500.000` — khớp oracle. |
| B9 E2E Result | **PASS (mới)** | `SYSTEM_RESULT` = `KpiPurchasePrice=7.000.000, EligibleKpiProfit=500.000` — real trace, real production entry point. |

```text
VERTICAL_PROGRESS (CONFIRMED boundaries, real trace)

BEFORE (đầu session, = cuối S053) : 6 CONFIRMED / 10 trong map (B0–B9)
  B0 PASS, B1 PASS, B2 PASS, B3 N/A-BYPASSED, B4 N/A-BYPASSED,
  B5 PASS (gộp B2), B6 PASS (gộp B2); B7–B9 NOT_REACHED (3)

AFTER (cuối session)              : 10 CONFIRMED / 10 trong map (B0–B9)
  B0–B6 không đổi; B7 PASS, B8 PASS, B9 PASS

GOLDEN #1 END-TO-END: PASS. Không còn boundary NOT_REACHED nào.
```

## 6. Test changes (chứng minh wiring thật, không mock)

```text
tests/test_confirmed_adjustment_source.py (mới, 8 test)
  missing file -> UNAVAILABLE (không phải "loaded rỗng"); empty file ->
  LOADED DETERMINED_ABSENCE; invalid JSON / field thiếu / amount không parse
  được -> UNAVAILABLE; một dòng hỏng giữa các dòng tốt -> fail-closed toàn bộ
  UNAVAILABLE; confirmed record tra đúng theo order_id, order khác vẫn
  DETERMINED_ABSENCE; construction trực tiếp phân biệt records={} khỏi None.

tests/test_kpi_profit_engine.py (mới, 12 test)
  4 nhánh resolve_kpi_purchase_price (AccountingPurchasePrice Pending; source
  None; source unavailable; loaded rỗng = DETERMINED_ABSENCE; confirmed
  record); discount trừ đúng một lần + quantity nhân đúng unit-price diff
  (BH0004-shape: 300000/200000/qty2/discount50000 -> 150000, KHÁC đọc
  nguyên văn dạng prose sai theo DEC-143 Reason §4); Golden #1 shape
  (qty1/discount0 -> 500000); Pending khi kpi_purchase_price None;
  AccountingProfit vs EligibleKpiProfit phân kỳ khi Discount != 0;
  apply_kpi_profit set cả 3 field cùng lúc; EligibleCosts closed empty set
  (cả fixture tự tạo lẫn file thật đã commit).

tests/test_pipeline.py (+3 test, dùng BH0004: Quantity=2, Discount=50000)
  wired end-to-end qua run_import() thật: xác định-không-có (nguồn loaded
  rỗng); confirmed adjustment record (nguồn từ file JSONL thật ghi tạm);
  nguồn UNAVAILABLE (file thiếu) -> Pending toàn bộ, KHÔNG suy đoán absence.

tests/test_golden_bh62063_kpi.py (mới, 2 test)
  real trace BH62063 qua CHÍNH hai file dữ liệu thật đã commit (không phải
  bản sao tmp_path) -> KpiPurchasePrice=7000000, EligibleKpiProfit=500000,
  provenance Config:NoConfirmedAdjustment; và test mặc định (không wiring)
  vẫn Pending -> 0 blast radius.
```

Không mock `run_import`/`ConfirmedAdjustmentSource`/`resolve_kpi_purchase_price`
ở bất kỳ test end-to-end nào — toàn bộ đi qua API thật, cùng pattern S051/S053.

## 7. Baseline fixture regeneration — bắt buộc, đã xác minh KHÔNG chạm giá trị nghiệp vụ nào

Thêm field vào `WorkingLine` làm hai ảnh chụp cấu trúc (dẫn xuất bằng
`dataclasses.fields()`, cố ý — "một trường thêm vào sau này tự động được
canh") lệch khỏi baseline đã commit:

- `tests/fixtures/golden/expected/period_{2026_01,2026_06}.json`
  (`test_golden_baseline.py`, maintenance action đã tài liệu hoá:
  `python3 -m tests.fixtures.golden.build_expected`).
- `tests/fixtures/baseline/business_output.json` (L2, `test_task110_non_regression.py`
  + `test_provenance_invariant.py`, sinh bằng `tests.fixtures.baseline_snapshot`).

Cả hai đã được regenerate và xác nhận bằng diff tự động: **CHỈ** 3 key mới
(`kpi_purchase_price`, `kpi_purchase_price_provenance`, `eligible_kpi_profit`,
giá trị `null`/`"Pending"` đồng nhất trên mọi dòng) xuất hiện thêm ở
`_covered_fields`/`_covered_digest_fields` + `lines_digest`; **0** giá trị
field nào khác (kể cả `footer`, mọi provenance anchor, mọi aggregate đã có
trước) thay đổi. Xác nhận bằng script so sánh trước/sau key-by-key, không chỉ
đọc mắt diff.

**KHÔNG regenerate `tests/fixtures/baseline/employee_resolve_matrix*.json`
(L1)** — thử một lần rồi phát hiện `snapshot_id` (một property dẫn xuất từ
`EmployeeMapper`, không phải input session này đụng tới) đổi giữa bản committed
và bản tính lại trong môi trường này. Điều tra xác nhận đây là một
**representation exception đã được biết và đã có cơ chế dung sai riêng**
trong chính test (`_without_representation_exception()`, `test_check_110_18_snapshot_id_semantic_equivalence`)
— KHÔNG liên quan gì tới session này, và `git log` xác nhận `employees.yaml`
không đổi từ commit `e221924` (lúc chụp baseline) tới nay. Đã `git checkout --`
khôi phục hai file L1 về đúng bản committed, không đưa thay đổi không cần
thiết đó vào diff của session.

`test_golden_pipeline_entry_point_signature_is_locked` (`test_golden_baseline.py`)
cập nhật thêm `confirmed_adjustment_source` vào danh sách tham số khoá cứng —
cùng pattern comment mà S051 để lại khi thêm `identity_registry`/
`identity_resolver_factory`.

## 8. Validation

```text
$ bash scripts/branch_authority_check.sh          → AUTHORITY_OK

$ python3 governance/scripts/governance/validate_structure.py
GOVERNANCE STRUCTURE: PASS — 21 required paths.

$ python3 governance/scripts/governance/validate_project_state.py
PROJECT STATE: PASS

$ python3 governance/scripts/governance/validate_evidence.py
EVIDENCE VALIDATION: PASS — 88 REQUIRED PASS evidence record(s).

$ python3 governance/scripts/governance/validate_task_completion.py
TASK COMPLETION: PASS — 7 DONE task(s).

$ python3 governance/scripts/governance/validate_reference_integrity.py
REFERENCE INTEGRITY: FAIL — 3 reference (TASK-REM-T06, PRE-EXISTING
  baseline, không đổi bởi session này — đã ghi nhận từ S053)

$ python3 -m pytest tests/test_confirmed_adjustment_source.py \
    tests/test_kpi_profit_engine.py tests/test_golden_bh62063_kpi.py -q
22 passed

$ python3 -m pytest tests/test_pipeline.py tests/test_golden_baseline.py -q
78 passed, 2 skipped

$ python3 -m pytest -q   (TRƯỚC commit — working tree có thay đổi chưa
    commit, hai guard `git diff HEAD` của TASK-105D tự dirty, đúng pattern
    "Nhóm A" S053 §9 đã ghi nhận)
998 passed, 11 skipped, 2 failed
  (2 failed = TestG25GoldenBaselineUnchanged::test_task_105d_does_not_touch_app_pipeline
   + test_no_golden_fixture_or_expected_file_was_modified — cả hai so
   `git diff HEAD`, tự resolve sau commit)

$ python3 -m pytest -q   (SAU commit)
1000 passed, 11 skipped, 0 failed
```

Baseline trước session (S053 §9, SAU commit của S053): `975 passed, 11
skipped, 0 failed`. Delta: `1000 − 975 = 25`, khớp CHÍNH XÁC 25 test mới
(8 + 12 + 3 + 2, §6). 0 test nào chuyển PASS → FAIL ở bất kỳ bước nào — 0
regression.

## 9. Task Registry — bằng chứng BEFORE/AFTER

```text
SET A (REGISTERED_TASK_SET, PROJECT_PROGRESS.md) BEFORE = 13   AFTER = 13
SET B (TASK_SPEC_SET, docs/tasks/*.md)            BEFORE = 22   AFTER = 22
new_registered_task_ids = 0
```

Không tạo task mới, không mở `TASK-105E`, không adopt `V4.2`. Cập nhật duy
nhất `docs/tasks/TASK-108B-eligible-costs-owner-definition.md` (Phần XIII,
DEFERRED_BY_MINIMAL_FIX, §12 brief) — không sửa `PROJECT/PROJECT_PROGRESS.md`
hay `PROJECT/PROJECT_DECISIONS.md`, cùng pattern S050–S053: session hẹp, ghi
bàn giao dưới `docs/sessions/`.

## 10. Budget

```text
$ git diff --shortstat d16c3fae2c167c034af65a0adc5cd3b95b3b6a8e..HEAD \
    -- app/ config/
 (đo sau khi commit)

SESSION_PRODUCTION_DIFF (app/+config/, insertions+deletions)  = 255 LOC
SESSION_PRODUCTION_DIFF_MAX                                    = 300 LOC  → OK
GOLDEN_1_CUMULATIVE_PRODUCTION_DIFF (từ GOLDEN_1_LOC_BASELINE_SHA
  d16c3fae2c167c034af65a0adc5cd3b95b3b6a8e)                     = 233 + 255 = 488 LOC
GOLDEN_1_CUMULATIVE_PRODUCTION_DIFF_MAX                        = 1200 LOC → OK

MEDIUM change này session : 1
  — "KpiPurchasePrice + EligibleKpiProfit minimum B7/B8 slice" (money/KPI,
    đúng brief §8: nhỏ về code nhưng risk cao vì chạm KPI/lương).
MEDIUM_CHANGE_MAX_PER_SESSION       = 3   → 1 used / 2 remaining
MEDIUM change cumulative (Golden #1, từ S053) = 1 + 1 = 2
MEDIUM_CHANGE_MAX_GOLDEN_1_CUMULATIVE = 8  → 2 used / 6 remaining
```

## 11. Exceptions / Deferred (brief §6/§12)

Không `EXCEPTION_CANDIDATE` mới — `EXCEPTION_CANDIDATE` classification bị
DISABLE tường minh cho Golden #1–#4 theo brief §6. Deferred: xem §9 ở trên và
`docs/tasks/TASK-108B-eligible-costs-owner-definition.md` Phần XIII.

## 12. Kết luận S054

```text
S054 FINAL STATE : GOLDEN_PASS
  - ConfirmedAdjustmentSource + 3 field WorkingLine mới +
    kpi_profit_engine.py + config/eligible_costs.yaml — minimum B7/B8 slice
    đúng authority DEC-143 + DEC-144 đã APPROVED trước session
  - Real trace qua run_import() (production entry point thật, hai file dữ
    liệu thật, KHÔNG mock/stub/bypass/Golden-specific branch):
    KpiPurchasePrice = 7.000.000, EligibleKpiProfit = 500.000 — khớp oracle
    tuyệt đối (§4)
  - AccountingProfit và EligibleKpiProfit CHỨNG MINH tách biệt thật (không
    chỉ trùng hợp Golden #1) bằng case BH0004 (Quantity=2, Discount=50000):
    200.000 vs 150.000
  - B7/B8/B9 chuyển NOT_REACHED → PASS (§5) — Golden #1 END-TO-END PASS
  - 25 test mới, 0 regression (§8); 2 baseline structural fixture
    (Golden expected + L2 business_output) regenerate có xác minh, chỉ thêm
    3 field mới giá trị Pending/None, không đổi bất kỳ giá trị nghiệp vụ nào
    khác (§7); baseline L1 (employee_resolve_matrix) KHÔNG bị đụng, revert
    một regeneration thử nghiệm sau khi xác nhận nó không liên quan (§7)
  - TASK-108B artifact cập nhật DEFERRED_BY_MINIMAL_FIX (§9, Phần XIII) —
    không sửa PROJECT_PROGRESS.md/PROJECT_DECISIONS.md
  - Budget: 255/300 LOC session, 488/1200 LOC cumulative, 1/3 MEDIUM
    session, 2/8 MEDIUM cumulative — trong ngân sách (§10)
  - Không tạo task mới, không mở TASK-105E/composition P00–P11, không xây
    writer/UI cho KpiPurchaseAdjustment, không hard-code BH62063 trong bất
    kỳ file production nào (§3, xác nhận bằng grep)

STOP_REASON : GOLDEN_PASS
  Không còn boundary B0–B9 nào NOT_REACHED cho path thật của BH62063.
  Không phải OWNER_DECISION_REQUIRED (không có case nghiệp vụ mơ hồ nào),
  không phải ARCHITECTURE_CHANGE_REQUIRED (đúng dự đoán của session brief —
  Codex review đã xác nhận minimum slice khả thi, không cần TASK-105E), và
  không phải CHANGE_BUDGET_EXCEEDED (còn nhiều ngân sách, §10).
```

### Explicit answers

```text
B7/B8/B9 PASS bằng real trace?                YES
BH62063 end-to-end PASS?                      YES (GOLDEN_PASS)
KpiPurchasePrice = 7.000.000?                  YES
EligibleKpiProfit = 500.000?                   YES
AccountingProfit dùng làm KPI profit?          NO (tách biệt, chứng minh
                                                bằng case BH0004)
Production KPI algorithm hard-coded cho
  BH62063?                                     NO (§3, xác nhận bằng grep)
TASK-105E/composition P00–P11 implemented?     NO
KpiPurchaseAdjustment writer/UI xây dựng?      NO
New task registered?                           NO
V4.2 started?                                  NO
PROJECT_PROGRESS.md/PROJECT_DECISIONS.md sửa?  NO
Merge/rebase/squash performed?                 NO
Default branch changed?                        NO
```
