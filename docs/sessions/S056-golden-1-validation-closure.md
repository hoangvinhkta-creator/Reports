# S056 — GOLDEN #1 VALIDATION CLOSURE (B02 + B03)

Validation-contract repair cho hai finding BLOCKING còn lại sau independent
repair verification của `S055` (B01 = CLOSED). Nhánh riêng
`repair/golden-1-validation-closure`, cắt từ đúng HEAD của `S055`
(`ad9bd092189da82631bf0bd1839976d60d2254d6`). Không merge/rebase/squash,
không đổi default branch, không reopen B01.

## 1. Git target

```text
Base SHA (S055 HEAD) : ad9bd092189da82631bf0bd1839976d60d2254d6
Branch                : repair/golden-1-validation-closure
Upstream              : origin/repair/golden-1-validation-closure
```

`bash scripts/branch_authority_check.sh` (trước commit, working tree có
thay đổi chưa commit nên `WORKTREE: DIRTY`, không ảnh hưởng AUTHORITY):

```text
DEFAULT_BRANCH   : claude/extract-upload-repo-gq2ws4
DEFAULT_TIP      : 7464ccaa784f13d887b2d5441d86136ff7d9a61d
HEAD_SHA         : ad9bd092189da82631bf0bd1839976d60d2254d6
ahead default    : 14 commit    behind default : 0 commit
AUTHORITY        : BRANCH_WITH_UPSTREAM
RESULT           : AUTHORITY_OK
```

## 2. Finding còn BLOCKING (từ independent repair verification sau S055)

- **B02** — `load_eligible_costs_authority()` (`app/modules/kpi/kpi_profit_engine.py`)
  gọi `"eligible_cost_categories" not in data` sau khi `load_yaml()` trả về
  giá trị parse thành công nhưng KHÔNG kiểm tra `data` có phải `dict` trước.
  YAML top-level scalar hợp lệ về cú pháp (vd. `42`, hoặc bất kỳ số/bool nào
  khác 0/False) làm `"key" not in 42` raise `TypeError` — crash thay vì
  fail-closed có kiểm soát. (`null` top-level không crash vì `load_yaml()`
  đã coalesce `None` → `{}`, nhưng cùng lớp lỗi cấu trúc cần cùng một guard
  tường minh, không dựa vào tình cờ.)
- **B03** — `load_confirmed_adjustments_from_jsonl()`
  (`app/modules/adjustment/confirmed_adjustment_source.py`) chỉ kiểm tra
  PRESENCE của `confirmed_by`/`confirmed_at` qua `raw_record["..."]`
  (`KeyError` khi thiếu key) — nhưng key CÓ MẶT với giá trị `null` không
  raise, nên `confirmed_by=None, confirmed_at=None` đi thẳng vào
  `ConfirmedAdjustmentRecord`. Khi record này match một order, provenance
  phát sinh `Confirmed:None@None` — false confirmation, đơn hàng nhìn như
  đã CONFIRMED trong khi confirmation metadata không đầy đủ.

## 3. Repair — validation contract, không phải literal patch

Cả hai fix nhắm equivalence class, không phải hai ví dụ literal của
reviewer:

**B02** (`kpi_profit_engine.py::load_eligible_costs_authority`) — thêm
`if not isinstance(data, dict): return AUTHORITY_UNAVAILABLE` ngay sau
`load_yaml()`, TRƯỚC bất kỳ `in`/index nào trên `data`. Có kiểm soát toàn bộ
lớp "top-level không phải mapping": scalar (số/bool/string), sequence, null
(dù null qua `load_yaml()` coalesce về `{}` nên vẫn PASS check `isinstance`,
nhưng rơi đúng vào nhánh "thiếu key" fail-closed sẵn có).

**B03** (`confirmed_adjustment_source.py`) — hàm `_non_empty_str(value)`
(mới): trả về `None` (invalid) nếu `value` không phải `str`, hoặc là `str`
chỉ toàn whitespace sau `strip()`; ngược lại trả về giá trị đã strip.  Áp
dụng cho CẢ BA field định danh bắt buộc — `order_id`, `confirmed_by`,
`confirmed_at` — ngay sau khi đọc từ `raw_record`; bất kỳ field nào invalid
→ `return UNAVAILABLE` (toàn bộ nguồn, đúng fail-closed contract hiện có
cho field thiếu/dòng hỏng, không phải một exception mới).  `amount` không
finite (đã có từ B03/S055) và trùng `order_id` (đã có) không đổi.

Không sửa `load_yaml()` (dùng chung cho các config khác ngoài phạm vi B02) —
guard đặt cục bộ tại `load_eligible_costs_authority()`, đúng brief §3
("Do not invent a generic configuration framework").

## 4. Bằng chứng fail-closed (trước/sau fix)

```text
$ python3 -c "load_eligible_costs_authority(path chứa '42')"
TRƯỚC : TypeError: argument of type 'int' is not iterable   (CRASH)
SAU   : EligibleCostsAuthority(is_valid=False, categories=(), provenance='SOURCE_UNAVAILABLE')

$ python3 -c "load_confirmed_adjustments_from_jsonl(path có confirmed_by=null, confirmed_at=null)"
TRƯỚC : is_available=True, lookup(...) -> ConfirmedAdjustmentRecord(confirmed_by=None, confirmed_at=None, ...)
        f"Confirmed:{record.confirmed_by}@{record.confirmed_at}" == "Confirmed:None@None"   (FALSE PROVENANCE)
SAU   : is_available=False   (toàn bộ nguồn UNAVAILABLE, không record nào match)
```

Không class nào trong hai finding còn crash hoặc phát sinh provenance giả
sau fix — cả hai đều hội tụ về `Pending`/`SOURCE_UNAVAILABLE` (đúng brief
§7).

## 5. Test mới — equivalence classes, không chỉ literal

`tests/test_kpi_profit_engine.py` (+5 test):
`test_eligible_costs_authority_scalar_top_level_is_unavailable_not_crash`,
`test_eligible_costs_authority_null_top_level_is_unavailable`,
`test_eligible_costs_authority_sequence_top_level_is_unavailable`,
`test_eligible_costs_authority_wrong_type_for_categories_is_unavailable`
(3 case mới ứng với brief §3 + 1 case null top-level, cộng case sequence).

`tests/test_confirmed_adjustment_source.py` (+8 test):
null/empty/wrong-type `confirmed_by`, null/empty/wrong-type `confirmed_at`,
null `order_id` — đúng danh sách equivalence class brief §6.

Test có sẵn từ `S055` (missing key, invalid YAML, non-empty categories,
missing file cho B02; missing field, NaN/Infinity amount, duplicate
`order_id`, one-bad-line cho B03) giữ nguyên, không sửa — vẫn PASS.

## 6. Golden regression — `run_import_production()`, không manual DI

```text
$ python3 -c "run_import_production(Path('tests/fixtures/golden/period_2026_01.xlsx'), config_dir=Path('config'))"
AccountingPurchasePrice = 7000000
KpiPurchasePrice        = 7000000
KpiPurchasePrice provenance = Config:NoConfirmedAdjustment
EligibleKpiProfit       = 500000
EligibleCosts authority = EligibleCostsAuthority(is_valid=True, categories=(), provenance='Config:EmptySet(OD-108B-01)')
```

Khớp tuyệt đối oracle đã Owner phê duyệt (S049), qua ĐÚNG production entry
point (`app.composition.run_import_production`), không test/manual DI —
test đã có `test_bh62063_normal_production_composition_reaches_eligible_kpi_profit`
(`tests/test_golden_bh62063_kpi.py`, không sửa trong session này, PASS trước
và sau fix).

## 7. Tests — kết quả thật

```text
$ uv run pytest -q tests/test_confirmed_adjustment_source.py tests/test_kpi_profit_engine.py
42 passed

$ uv run pytest -q tests/test_golden_bh62063_kpi.py tests/test_golden_baseline.py tests/test_pipeline.py
86 passed, 2 skipped

$ uv run pytest -q
1028 passed, 11 skipped   (S055: 1015 passed, 11 skipped — delta +13 test mới, 0 failed, 0 regression)
```

Không regenerate fixture — không field mới trên `WorkingLine`, không đổi
Golden expected output (đúng brief §8/§11).

## 8. Production LOC / MEDIUM budget

```text
$ git diff --shortstat d16c3fae2c167c034af65a0adc5cd3b95b3b6a8e -- app/ config/  (đo sau commit)
GOLDEN_1_CUMULATIVE_PRODUCTION_DIFF (đo trực tiếp so với Golden baseline) = 671 LOC (652 ins + 19 del)
GOLDEN_1_CUMULATIVE_PRODUCTION_DIFF_MAX                                   = 1200 LOC → OK

SESSION_PRODUCTION_DIFF (chỉ 2 file sửa session này, so với S055 HEAD)    = 54 LOC (44 ins + 10 del)
```

MEDIUM: B02/B03 đã được tính vào 5/8 MEDIUM cumulative tại `S055` (là 2
trong 3 MEDIUM của `S055`: "EligibleCosts authority gating" + "confirmed-
adjustment integrity"). Session này REPAIR chính hai mục đó cho đủ điều
kiện validation contract closure (khép equivalence class còn thiếu), không
mở rộng capability mới hay chạm mục MEDIUM nào chưa từng tính — đánh giá
KHÔNG cộng thêm đơn vị MEDIUM mới. `MEDIUM cumulative giữ nguyên 5/8, 3
remaining`. Đây là judgment call, ghi rõ minh bạch thay vì tự ý quyết định
ngầm.

## 9. Scope

Không tạo task mới (không `TASK-105F/G`), không reopen B01, không sửa
`app/composition.py`/`app/pipeline.py` (production composition không đổi —
đã đúng từ S055, chỉ hai loader bị sửa), không đụng `TASK-105B/C/E`, không
mở rộng `TASK-108B`, không xây adjustment persistence/UI, không effective
dating, không migrate governance, không hardening ngoài phạm vi hai
finding. `PROJECT/PROJECT_PROGRESS.md`/`PROJECT/PROJECT_DECISIONS.md`/
`PROJECT/REVIEW_BUDGET_LEDGER.md` không sửa — cùng pattern hẹp `S049`–`S055`.

## 10. Kết luận S056

```text
S056 FINAL STATE : GOLDEN_PASS
  - B02 CLOSED — isinstance(data, dict) guard trước mọi in/index trên YAML
    đã parse; scalar/sequence/null top-level đều fail-closed, không crash
  - B03 CLOSED — order_id/confirmed_by/confirmed_at đều bắt buộc str
    non-empty; null/empty/wrong-type fail toàn bộ nguồn, không còn
    Confirmed:None@None
  - Golden BH62063 qua run_import_production(): KpiPurchasePrice=7.000.000,
    EligibleKpiProfit=500.000, EligibleCosts=Config:EmptySet(OD-108B-01) —
    khớp oracle, KHÔNG manual DI
  - 1028 passed / 11 skipped / 0 failed — 0 regression trên 1015 passed
    trước session (+13 test mới, equivalence class B02/B03)
  - Budget: 54 LOC session / 671 LOC cumulative (max 1200) / MEDIUM giữ
    nguyên 5/8 (judgment: repair của mục đã tính, không phải mục mới)

STOP_REASON : GOLDEN_PASS
```
