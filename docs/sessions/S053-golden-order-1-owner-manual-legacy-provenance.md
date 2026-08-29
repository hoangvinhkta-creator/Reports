# S053 — GOLDEN ORDER #1 (BH62063) OWNER MANUAL LEGACY PROVENANCE

GOLDEN #1 VERTICAL DELIVERY LOOP #1, session #1. Kế tiếp `S052`
(`SOURCE_EVIDENCE_MISSING` — không có `source_report_ref` reopenable nào cho
`BH62063`). Session brief lần này (Owner, §2) cung cấp đúng OWNER DATA mà
`S052` §9 xác định là bước kế tiếp cần: một xác nhận trực tiếp, bằng lời
nhưng có cấu trúc, rằng giá trị `7.000.000 VND` đến từ nguồn "Tồn"/giá mua
công khai của Tracking, rằng Tracking lịch sử ghi đè giá trị này và không
giữ lại snapshot lịch sử reopenable cho `2026-01-02` — một LEGACY DATA GAP,
không phải bằng chứng phủ nhận giá trị đó. Brief cho phép dùng "explicit
manual legacy-confirmation provenance" cho trường hợp này, với điều kiện
KHÔNG claim verified historical replay.

Mục tiêu duy nhất của session: dựng đúng cơ chế đó (một provenance mới,
trung thực, phân biệt được với `HISTORICAL_CONFIRMED_REPORT`), dùng nó để
đưa `BH62063` qua `B2`, và chạy lại vertical trace thật.

## 1. Git target

```text
Base SHA (GOLDEN_1_LOC_BASELINE_SHA) : d16c3fae2c167c034af65a0adc5cd3b95b3b6a8e
HEAD trước session                    : d16c3fae2c167c034af65a0adc5cd3b95b3b6a8e (khớp)
Branch                                 : implementation/golden-bh62063-vertical-delivery-1
Upstream                               : origin/implementation/golden-bh62063-vertical-delivery-1
                                          (0 ahead / 0 behind trước session)
Working tree trước session             : clean
```

`bash scripts/branch_authority_check.sh` trước thay đổi:

```text
DEFAULT_BRANCH  : claude/extract-upload-repo-gq2ws4
DEFAULT_TIP     : 7464ccaa784f13d887b2d5441d86136ff7d9a61d
HEAD_SHA        : d16c3fae2c167c034af65a0adc5cd3b95b3b6a8e
WORKTREE        : CLEAN
CURRENT_BRANCH  : implementation/golden-bh62063-vertical-delivery-1
UPSTREAM        : origin/implementation/golden-bh62063-vertical-delivery-1
ahead default   : 9 commit    behind default : 0 commit
cumulative LOC  : 5887
DIVERGENCE      : INTEGRATION_DECISION_REQUIRED [loc>5000]
AUTHORITY       : BRANCH_WITH_UPSTREAM
RESULT          : AUTHORITY_OK
```

`git merge-base HEAD origin/claude/extract-upload-repo-gq2ws4` = `7464ccaa…`
= chính `DEFAULT_TIP` — nhánh này là một fast-forward sạch 9 commit phía
trước default, không phải một nhánh phân kỳ xung đột. `DIVERGENCE =
INTEGRATION_DECISION_REQUIRED [loc>5000]` được **giữ nguyên, không tự giải
quyết** — đúng chỉ thị brief §0: không merge/rebase/squash, không đổi default
branch. Cảnh báo này là quyết định tích hợp của Owner, không phải việc của
vòng lặp vertical delivery.

## 2. Business authority (Owner, session brief §2) — không phải suy diễn

Trích nguyên văn phần quyết định nghiệp vụ mà session brief cung cấp, vì đây
chính là bằng chứng ủy quyền cho thay đổi production dưới đây:

```text
The 7,000,000 VND value was obtained from Tracking's "Tồn" / public
purchase price. Tracking historically overwrote this current public
purchase price and did not retain a reopenable historical inv.cong
snapshot for 2026-01-02. Therefore the absence of a historical snapshot is
a LEGACY DATA GAP, not evidence that the Owner value is false.

For pre-existing legacy data where the original system did not retain
historical replay, this Golden may use an explicit manual
legacy-confirmation provenance. It MUST NOT falsely claim VERIFIED
historical replay. The provenance must remain truthful about:
Owner/manual confirmation; original system = Tracking; historical replay
unavailable; reason = historical public-purchase snapshot was not retained.
```

Đây KHÔNG phải là nới lỏng `INV-51` cho trường hợp một report reopenable
đáng lẽ phải tồn tại — `S052` đã xác nhận bằng cách tìm kiếm hết mọi nguồn
trong repo rằng không có report nào như vậy, và nguyên nhân (Tracking ghi đè
+ không giữ snapshot) là một sự kiện lịch sử có thật, không phải một lựa
chọn tiện lợi để né `INV-51`. `INV-51` vẫn cấm tuyệt đối "chủ dự án đã xác
nhận" dưới dạng văn xuôi không có cấu trúc đứng thay cho một report thật.
Điều mới ở đây là: khi report reopenable KHÔNG THỂ tồn tại (không phải "chưa
tìm thấy"), một loại bằng chứng THỨ HAI — tự khai đúng bản chất của nó — là
hợp lệ. Đây đúng ý `INV-54`: "nhập từ báo cáo Owner-confirmed thật, **hoặc**
để trống" — provenance mới này vẫn là "Owner-confirmed thật", chỉ khác hình
dạng bằng chứng.

## 3. Thiết kế — `ManualLegacyConfirmationRef`, phân biệt khỏi `SourceReportRef`

`app/modules/product/identity/registry.py`:

- `PROVENANCE_OWNER_MANUAL_LEGACY_CONFIRMATION =
  "OWNER_MANUAL_LEGACY_CONFIRMATION"` — nhãn mới, tách biệt hoàn toàn khỏi
  `PROVENANCE_HISTORICAL = "HISTORICAL_CONFIRMED_REPORT"`.
- `ManualLegacyConfirmationRef` (frozen dataclass mới): `original_system`,
  `reason` (cả hai REQUIRED, non-empty — `InvalidManualLegacyConfirmationError`
  nếu rỗng, cùng pattern `InvalidSourceReportRefError`), `confirmed_note`
  (optional). Đây KHÔNG phải "phiên bản nhẹ" của `SourceReportRef` — nó là
  một loại bằng chứng khác, không có `report_id`/`content_hash`/`file_name`
  vì không có file nào đứng sau nó.
- `HistoricalConfirmedRegistryEntry.source_report_ref` chuyển từ REQUIRED
  sang `Optional[SourceReportRef] = None`; trường mới
  `manual_legacy_confirmation_ref: Optional[ManualLegacyConfirmationRef] =
  None`. `__post_init__` thi hành TRUNG THỰC bằng code, không chỉ bằng convention:
  - đúng MỘT trong hai trường được set (không cả hai, không thiếu cả hai);
  - `provenance` PHẢI khớp loại bằng chứng đang có (`source_report_ref` →
    bắt buộc `provenance == PROVENANCE_HISTORICAL`;
    `manual_legacy_confirmation_ref` → bắt buộc
    `provenance == PROVENANCE_OWNER_MANUAL_LEGACY_CONFIRMATION`).

  Điều kiện thứ hai chính là cơ chế thi hành "MUST NOT falsely claim VERIFIED
  historical replay" của brief: không ai gọi được constructor với
  `manual_legacy_confirmation_ref` set nhưng `provenance =
  HISTORICAL_CONFIRMED_REPORT` — nó raise ngay lúc dựng object, không đợi
  tới lúc đọc lại.
- `to_record()`/`entry_from_record()` (đổi tên từ `_entry_from_record`,
  public vì `registry_store.py` mới cần dùng lại) cập nhật cho cả hai loại
  ref, round-trip test ở `tests/test_registry_store.py`.

`app/modules/product/identity/service.py` (`_historical_outcome`): trước đây
hardcode `PROVENANCE_HISTORICAL` cho MỌI entry `CONFIRMED` — kể cả đã có sẵn
trường `entry.provenance` không được đọc. Sửa: khi có entry, dùng
`entry.provenance` thật (không hardcode) cho `resolution_method`/
`mapping_source`/`price_provenance` của `Provenance`. Đây là bug tiềm ẩn có
sẵn từ `S051` (chỉ không lộ ra vì tới nay chỉ có một loại provenance) — sửa
nó là điều kiện cần để loại provenance thứ hai không bị "rửa" thành loại thứ
nhất khi đi qua `resolve_batch()`.

`app/pipeline.py` (`_apply_pre_cutover_identity`): trước đây hardcode
`line.price_source = PRICE_SOURCE_HISTORICAL_CONFIRMED_REPORT` cho MỌI
`HistoricalConfirmed`. Sửa: `line.price_source =
outcome.provenance.price_provenance or PRICE_SOURCE_HISTORICAL_CONFIRMED_REPORT`
— đọc nhãn thật đã đi qua `service.py`, giữ fallback an toàn nếu
`price_provenance` vắng (không xảy ra trong thực tế, chỉ là defensive).

`app/modules/domain/models.py`: thêm hằng số
`PRICE_SOURCE_OWNER_MANUAL_LEGACY_CONFIRMATION =
"OWNER_MANUAL_LEGACY_CONFIRMATION"` cạnh `PRICE_SOURCE_HISTORICAL_CONFIRMED_REPORT`
đã có — cho downstream code so sánh bằng tên thay vì chuỗi rời rạc.

**Không có BH62063 nào bị hard-code trong bốn file production trên** — toàn
bộ thay đổi là cơ chế chung (một loại provenance mới trong registry, một chỗ
sửa hai dòng đọc field có sẵn thay vì hardcode). Xác nhận bằng grep:

```text
$ grep -n "BH62063" app/modules/product/identity/registry.py \
    app/modules/product/identity/service.py app/pipeline.py \
    app/modules/domain/models.py app/modules/product/identity/registry_store.py
(không có kết quả)
```

## 4. Persistence — loader read-only mới, KHÔNG đổi default của `run_import()`

`S051`/`S052` đều để ngỏ "cơ chế persistence cho registry" cho một DATA
SESSION sau. `HistoricalConfirmedRegistry` production vẫn thuần bộ nhớ
(không đổi ở đây) — `run_import()`/`build_working_data()` vẫn nhận
`identity_registry` qua DI, mặc định registry RỖNG (chữ ký không đổi, hành
vi mặc định không đổi — xác nhận ở §6).

`app/modules/product/identity/registry_store.py` (mới,
`load_registry_from_jsonl(path) -> HistoricalConfirmedRegistry`): đọc một
file JSONL (một entry mỗi dòng, đúng schema §9.2 của `to_record()`), replay
từng dòng qua ĐÚNG đường ghi production (`registry.append(ConfirmHistoricalEntry(...))`,
`INV-66` — không viết tắt bằng cách gán field trực tiếp). File không tồn tại
→ registry rỗng (không phải lỗi). Đây là loader READ-ONLY, một lần — không
làm lại hạ tầng khoá file nhiều tiến trình của `store.py`/E-F (`B-01`,
Independent Review #1/#2): E-J chưa có correction/multi-writer workflow
production nào cần tới nó; khi có, đó là phạm vi của một session riêng, như
`S051 §9` đã dự đoán.

`data/historical_confirmed/registry.jsonl` (mới, thư mục `data/` mới ở gốc
repo — không có trong `.gitignore`, không chứa dữ liệu cá nhân khách hàng,
`DEC-108` không áp): MỘT dòng, entry `BH62063` với
`manual_legacy_confirmation_ref` (`original_system="Tracking"`, `reason`
theo đúng nguyên văn Owner ở §2, `confirmed_note` diễn giải thêm),
`confirmed_identity=TRACKING:FV1410S4W1`, `confirmed_purchase_price=7000000`,
`confirmed_by="chu.du.an"`, `confirmation_authority=OWNER`. Đây LÀ nơi hợp
lệ để dữ liệu riêng của `BH62063` sống — một data file, không phải code —
đúng ranh giới `INV-54` ("nhập từ báo cáo Owner-confirmed thật").

Caller (Golden trace, §6 dưới) tự load file này rồi truyền qua
`identity_registry=` — không có thay đổi default nào trong `run_import()`
tự động đọc file này. Lý do: đổi default sẽ ảnh hưởng MỌI lời gọi
`run_import()` hiện có không truyền `identity_registry`, bao gồm
`tests/test_golden_baseline.py` — vốn dùng CHÍNH fixture chứa `BH62063`
(`period_2026_01.xlsx`) làm một phần của bộ 58 test đã frozen. Xác nhận
bằng chạy lại KHÔNG truyền `identity_registry` (§6) — kết quả BH62063 y hệt
trước session (`None`/`Pending`) — 0 blast radius lên Golden Baseline.

## 5. Test changes (chứng minh wiring thật, không mock)

```text
tests/support/identity_fixtures.py
  + registry_entry_manual_legacy() — biến thể registry_entry() dùng
    ManualLegacyConfirmationRef.

tests/test_105d_cutover_registry.py
  + TestManualLegacyConfirmationProvenance (4 test): truthful field
    validation, "đúng một trong hai" ref, provenance phải khớp loại ref,
    và resolve_batch() thật (không mock) xác nhận price_provenance hạ nguồn
    = "OWNER_MANUAL_LEGACY_CONFIRMATION" — không bị rửa thành
    HISTORICAL_CONFIRMED_REPORT.

tests/test_pipeline.py
  + _historical_registry_manual_legacy() helper (cùng pattern
    _historical_registry() của S051).
  + test_manual_legacy_confirmation_wired_end_to_end_through_run_import —
    BH0001 (2026-01-15, pre-cutover, synthetic fixture) qua run_import()
    thật: accounting_purchase_price + price_source đúng, KHÁC
    PRICE_SOURCE_HISTORICAL_CONFIRMED_REPORT, accounting_profit tính đúng.

tests/test_registry_store.py (mới, 5 test)
  missing file → registry rỗng; load 1 entry manual-legacy + lookup khớp;
  nhiều dòng + dòng trống bị bỏ qua; JSON hỏng raise (không âm thầm bỏ qua);
  và một test đọc THẲNG file thật đã commit
  (data/historical_confirmed/registry.jsonl) — không phải bản sao tmp_path —
  xác nhận entry BH62063 thật load được, giá đúng, provenance đúng, identity
  đúng TRACKING:FV1410S4W1.
```

Không mock `resolve_batch`/`registry.lookup`/`run_import` ở bất kỳ test nào
trên — toàn bộ đi qua API thật, cùng pattern `S051 §5` yêu cầu.

## 6. Golden BH62063 — REAL trace qua production entry point

**Mặc định (không truyền `identity_registry`)** — xác nhận KHÔNG đổi so với
`S052`:

```text
$ python3 -c "
from pathlib import Path
from app.pipeline import run_import
result = run_import(Path('tests/fixtures/golden/period_2026_01.xlsx'), config_dir=Path('config'))
order = next(o for o in result.orders if o.order_id == 'BH62063')
line = order.lines[0]
print(line.accounting_purchase_price, line.price_source, line.accounting_profit)
"
None Pending None
```

**Với registry nạp từ file thật đã commit** (production entry point thật,
registry thật từ file thật, KHÔNG stub/mock/bypass/manual injection trong
lời gọi này — `identity_registry=` là đúng cổng DI mà `S051` dựng cho chính
mục đích này):

```text
$ python3 -c "
from pathlib import Path
from app.pipeline import run_import
from app.modules.product.identity.registry_store import load_registry_from_jsonl

registry = load_registry_from_jsonl(Path('data/historical_confirmed/registry.jsonl'))
result = run_import(Path('tests/fixtures/golden/period_2026_01.xlsx'), config_dir=Path('config'), identity_registry=registry)
order = next(o for o in result.orders if o.order_id == 'BH62063')
line = order.lines[0]
print('accounting_purchase_price:', line.accounting_purchase_price)
print('price_source:', line.price_source)
print('accounting_profit:', line.accounting_profit)
print('sell_price:', line.sell_price, 'discount:', line.discount, 'quantity:', line.quantity)
"
accounting_purchase_price: 7000000
price_source: OWNER_MANUAL_LEGACY_CONFIRMATION
accounting_profit: 500000
sell_price: 7500000 discount: 0 quantity: 1
```

Khớp tuyệt đối oracle giá vốn (`7.000.000 VND`, `S049`/`DEC-163`).
`price_source` trung thực — KHÔNG claim `HISTORICAL_CONFIRMED_REPORT`.

**Quan trọng — `accounting_profit` (500.000) KHÔNG phải `EligibleKpiProfit`.**
Hai con số trùng nhau ở đơn hàng này CHỈ vì `Discount = 0` — đây là trùng hợp
số học của riêng `BH62063`, không phải bằng chứng hai khái niệm giống nhau.
`AccountingProfit = (SellPrice − AccountingPurchasePrice) × Quantity`
(`profit_engine.py`, `TASK-107`, tự động, không có số hạng Discount).
`EligibleKpiProfit = (SellPrice − KpiPurchasePrice) × Quantity − Discount`
(oracle, `S049`) là một capability KHÁC, tách biệt hoàn toàn theo `DEC-126`
— chưa có module nào implement nó trong `app/` (xác nhận lại, §8 dưới).

## 7. Bảng boundary B0–B9 (cập nhật so với S052)

| Boundary | Status | Ghi chú |
|---|---|---|
| B0 Sales Input | PASS | Không đổi |
| B1 Identity Input | PASS | Không đổi |
| B2 Product Identity Resolution | **PASS (mới)** | `resolve_batch()` thật qua registry nạp từ file thật → `HistoricalConfirmed(price=7.000.000, identity=TRACKING:FV1410S4W1, provenance=OWNER_MANUAL_LEGACY_CONFIRMATION)`. Trước: `DATA_MISSING` (S052). |
| B3 Price Request | **N/A — BYPASSED_BY_DESIGN** | `DEC-154` P00: một entry `CONFIRMED` pre-cutover bypass TOÀN BỘ P01–P11 (composition `TASK-105E`, chưa authorize). Không phải "chưa tới", mà "không áp dụng cho đơn hàng này" — production thật xác nhận đúng ngữ nghĩa P00 (không gọi `resolver_factory`, xem test `spy.calls == 0`). |
| B4 Preferred Source "Tồn" | **N/A — BYPASSED_BY_DESIGN** | Cùng lý do B3. `"Tồn"` `TECHNICAL_SOURCE_MAPPING` vẫn `UNRESOLVED` (S050 §8, không đổi) nhưng KHÔNG chặn `BH62063` — provenance của giá không đến từ việc giải "Tồn" thành production mapping, mà từ xác nhận thủ công trực tiếp giá trị đã biết. |
| B5 Purchase Price | **PASS (gộp vào B2)** | `7.000.000 VND` — khớp oracle, đến từ registry, không qua PriceProvider. |
| B6 Provenance | **PASS (gộp vào B2)** | `price_source = OWNER_MANUAL_LEGACY_CONFIRMATION` — trung thực, có cấu trúc (`ManualLegacyConfirmationRef`), không claim verified replay. |
| B7 KPI Input | NOT_REACHED | Không đổi. `app/pipeline.py` không truyền `accounting_purchase_price`/identity resolved tới module KPI nào — vẫn đúng quan sát S050 §11. |
| B8 KPI Calculation | NOT_REACHED / NOT_IMPLEMENTED | Không đổi. `profit_engine.py` vẫn chỉ có `AccountingProfit` (không Discount) — `EligibleKpiProfit` không tồn tại ở đâu trong `app/` (xác nhận lại §8). Owner của capability này là `TASK-108B` = `BLOCKED_BY_DEPENDENCY`. |
| B9 E2E Result | NOT_REACHED | `SYSTEM_RESULT = unavailable` — không đổi, phụ thuộc B8. |

```text
VERTICAL_PROGRESS (CONFIRMED boundaries, real trace)

BEFORE (đầu session, = cuối S052) : 3 CONFIRMED / 10 trong map (B0–B9)
  B0 PASS, B1 PASS, B2 FAIL(DATA_MISSING); B3–B9 NOT_REACHED (7)

AFTER (cuối session)              : 6 CONFIRMED / 10 trong map (B0–B9)
  B0 PASS, B1 PASS, B2 PASS, B3 N/A-BYPASSED, B4 N/A-BYPASSED,
  B5 PASS (gộp B2), B6 PASS (gộp B2); B7–B9 NOT_REACHED (3)

NEW_FIRST_FAILING_BOUNDARY (thứ tiếp theo cần giải quyết) : B7/B8
  — không phải một FAIL runtime, mà một capability chưa tồn tại
  (EligibleKpiProfit, chủ sở hữu TASK-108B, BLOCKED_BY_DEPENDENCY)
```

B3/B4 được tính là CONFIRMED (không phải PROVISIONAL/loại khỏi mẫu số) vì
trạng thái "N/A — BYPASSED_BY_DESIGN" của chúng được xác nhận bằng chính real
trace của session này (spy xác nhận `resolver_factory` không bị gọi, đúng
`INV-47`), không phải suy diễn tĩnh.

## 8. Xác nhận lại B8 — EligibleKpiProfit vẫn NOT_IMPLEMENTED (không đổi bởi session)

```text
$ grep -rln "EligibleKpiProfit\|KpiPurchasePrice" app/
app/pipeline.py    (chỉ trong docstring, liệt kê "Out of scope here")

$ grep -n "class \|^def " app/modules/profit/profit_engine.py
(chỉ compute_accounting_profit/apply_accounting_profit — không có
EligibleKpiProfit)
```

`TASK-108B` (chủ sở hữu capability này theo `DEC-126`) =
`BLOCKED_BY_DEPENDENCY` tại `PROJECT/PROJECT_PROGRESS.md`: chờ `TASK-105C`
(`BLOCKED / NOT AUTHORIZED`), `TASK-105B` (`NOT DONE`), `TASK-105E`
(`NOT STARTED / NOT AUTHORIZED`), và `TASK-105B-Q3`. Không cái nào trong số
này được giải quyết bởi session này (đúng brief §14 — không tự implement
đầy đủ `TASK-105B/C/E` chỉ vì chúng tồn tại). Đây KHÔNG phải "wiring nhỏ
kiểu ordinary" (brief §10): implement `EligibleKpiProfit` thật đòi hỏi (a)
một workflow xác nhận `KpiAdjustment` có persistence (`DEC-125`, hiện chưa
có — `AdjustmentResolver` chỉ tính `suggested_amount`, chưa có
`final_amount` xác nhận nào được lưu), và (b) đứng lên một trong các nhánh
composition `P00–P11` mà `TASK-105E` sở hữu và chưa được authorize. Cả hai
đều là ranh giới kiến trúc/authority thật, không phải một tham số/adapter
cục bộ.

## 9. Validation

```text
$ bash scripts/branch_authority_check.sh          → AUTHORITY_OK (WORKTREE
    dirty trước commit, đúng — có thay đổi thật)

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
  baseline, không đổi bởi session này)

$ python3 -m pytest tests/test_105d_cutover_registry.py tests/test_pipeline.py \
    tests/test_registry_store.py -q
40 passed

$ python3 -m pytest tests/ -k "105d" -q
203 passed   (199 baseline + 4 test mới trong test_105d_cutover_registry.py)

$ python3 -m pytest tests/test_golden_baseline.py -q
58 passed, 2 skipped                    — khớp reference tuyệt đối

$ python3 -m pytest -q   (ngay sau khi sửa app/**, TRƯỚC khi thêm test mới)
1 failed, 964 passed, 11 skipped
  (1 failed = TestG25GoldenBaselineUnchanged::test_task_105d_does_not_touch_app_pipeline
   — so `git diff HEAD` KHÔNG phải một SHA đóng băng; guard nhất thời cho
   working tree đang có thay đổi CHƯA commit, đúng pattern "Nhóm A" đã ghi
   nhận ở S051 §4. 964 passed + 1 self-resolving = 965 — khớp TUYỆT ĐỐI
   baseline 965 passed/11 skipped trước session này. 0 regression từ riêng
   thay đổi production.)

$ python3 -m pytest -q   (SAU khi thêm 10 test mới — §5 — TRƯỚC commit)
1 failed, 974 passed, 11 skipped
  (974 = 964 + 10 test mới; cùng 1 failed tự khớp ở trên, chưa resolve vì
  chưa commit)

$ python3 -m pytest -q   (SAU commit)
975 passed, 11 skipped, 0 failed
  (974 + 1 = 975 — test tự PASS lại đúng như dự đoán, không sửa gì thêm)
```

Delta so với baseline (965 passed/11 skipped/0 failed trước session):
`975 − 965 = 10`, khớp CHÍNH XÁC 10 test mới (4 `test_105d_cutover_registry.py`
+ 1 `test_pipeline.py` + 5 `test_registry_store.py`, §5). 0 test nào chuyển
PASS → FAIL ở bất kỳ bước nào trên — 0 regression.

## 10. Task Registry — bằng chứng BEFORE/AFTER

```text
SET A (REGISTERED_TASK_SET, PROJECT_PROGRESS.md) BEFORE = 13   AFTER = 13
SET B (TASK_SPEC_SET, docs/tasks/*.md)            BEFORE = 22   AFTER = 22
new_registered_task_ids = 0
```

Không tạo task mới, không mở lại `TASK-105D`, không mở `RC-2`, không adopt
`V4.2`, không sửa `PROJECT/PROJECT_PROGRESS.md` hay `PROJECT/PROJECT_DECISIONS.md`
— đúng pattern `S050`/`S051`/`S052`: session hẹp, chỉ ghi bàn giao dưới
`docs/sessions/`.

## 11. Budget (Golden #1 vertical delivery framework, session brief §3/§4)

```text
$ git diff --shortstat d16c3fae2c167c034af65a0adc5cd3b95b3b6a8e..HEAD -- app/ config/
 5 files changed, 220 insertions(+), 13 deletions(-)

SESSION_PRODUCTION_DIFF (app/+config/, insertions+deletions) = 233 LOC
SESSION_PRODUCTION_DIFF_MAX                                   = 300 LOC   → OK
GOLDEN_1_CUMULATIVE_PRODUCTION_DIFF (từ GOLDEN_1_LOC_BASELINE_SHA)
                                                                = 233 LOC
GOLDEN_1_CUMULATIVE_PRODUCTION_DIFF_MAX                        = 1200 LOC → OK
  (GOLDEN_1_LOC_BASELINE_SHA == HEAD trước session này — session #1 của
  vòng lặp, cumulative = session diff)

MEDIUM change này session : 1
  — "Product Identity & Purchase Price provenance mechanism" (money/
    identity/KPI-path, đúng brief §8: nhỏ về code nhưng risk cao vì chạm
    tới giá vốn/nhãn provenance downstream).
MEDIUM_CHANGE_MAX_PER_SESSION       = 3   → 1 used / 2 remaining
MEDIUM change cumulative (Golden #1) = 1
  (khung ngân sách MEDIUM theo brief §4 mới xuất hiện từ chính session này
  — S049–S052 không ghi nhận theo khung này; đếm bắt đầu từ đây, ghi rõ để
  session sau không hiểu nhầm là đã có lịch sử trước đó)
MEDIUM_CHANGE_MAX_GOLDEN_1_CUMULATIVE = 8  → 1 used / 7 remaining
```

## 12. Exceptions (brief §7)

Không có `EXCEPTION_CANDIDATE` mới trong session này — thay đổi ở đây là một
cơ chế provenance chung (áp dụng cho MỌI order rơi vào đúng tình huống LEGACY
DATA GAP, không riêng `BH62063`), được ủy quyền trực tiếp bằng business
authority tường minh trong session brief, không phải một case lạ cần Owner
phân loại AUTOMATE/MANUAL EXCEPTION.

## 13. Deferred (brief §11)

Không có `DEFERRED_BY_MINIMAL_FIX` mới — session này không implement một
phần tối thiểu của một task/capability đã có Task Spec đang chờ; nó dựng một
cơ chế mới (provenance) mà brief §2 ủy quyền trực tiếp, đầy đủ trong phạm vi
của chính nó (không có phần "còn thiếu" nào của CHÍNH cơ chế này bị bỏ lại —
B3/B4 N/A không phải phần thiếu của provenance mechanism, mà là ranh giới
kiến trúc khác, `TASK-105E`, đã ghi nhận từ trước).

## 14. Kết luận S053

```text
S053 FINAL STATE : PASS
  - ManualLegacyConfirmationRef + PROVENANCE_OWNER_MANUAL_LEGACY_CONFIRMATION
    dựng đúng business authority của session brief §2, thi hành trung thực
    bằng code (__post_init__ tại registry.py), không nới lỏng INV-51 cho
    trường hợp report reopenable thật sự tồn tại
  - service.py sửa một bug tiềm ẩn (hardcode PROVENANCE_HISTORICAL, bỏ qua
    entry.provenance thật) — điều kiện cần để provenance mới không bị "rửa"
  - Loader read-only mới (registry_store.py) + data file thật
    (data/historical_confirmed/registry.jsonl, một entry BH62063) — KHÔNG
    đổi default identity_registry của run_import(), 0 blast radius lên
    Golden Baseline (xác nhận §6)
  - Real trace qua run_import() (production entry point thật, registry thật
    từ file thật, KHÔNG mock/stub/bypass): B2 chuyển DATA_MISSING → PASS;
    accounting_purchase_price = 7.000.000 (khớp oracle); price_source =
    OWNER_MANUAL_LEGACY_CONFIRMATION (trung thực, không claim report)
  - B3/B4 xác nhận N/A — BYPASSED_BY_DESIGN (DEC-154 P00), không phải một
    boundary còn thiếu cho riêng đơn hàng này
  - B7/B8/B9 KHÔNG đổi — EligibleKpiProfit thật sự chưa tồn tại, chủ sở hữu
    TASK-108B vẫn BLOCKED_BY_DEPENDENCY trên nhiều task NOT AUTHORIZED/NOT
    DONE khác — ngoài phạm vi "ordinary wiring" của vòng lặp này
  - 10 test mới, 0 regression (§9); validator khớp baseline tuyệt đối
    (chỉ 3 reference_integrity issue TASK-REM-T06 tiền tồn tại)
  - Không tạo task mới, không mở TASK-105D/RC-2, không adopt V4.2, không
    hard-code BH62063 trong bất kỳ file production nào (§3 xác nhận bằng grep)
  - Budget: 233/300 LOC session, 233/1200 LOC cumulative, 1/3 MEDIUM session,
    1/8 MEDIUM cumulative — trong ngân sách

STOP_REASON : ARCHITECTURE_CHANGE_REQUIRED
  B7/B8 (KPI Input/Calculation, EligibleKpiProfit) đòi hỏi đứng lên composition
  P00–P11 (chủ sở hữu TASK-105E, PLANNED/NOT AUTHORIZED) và một workflow xác
  nhận KpiAdjustment có persistence (chưa tồn tại) — cả hai là ranh giới kiến
  trúc/authority thật do chính project governance đánh dấu NOT AUTHORIZED/
  BLOCKED, không phải một "ordinary wiring/parameter/adapter/local
  deterministic problem" mà vòng lặp này được phép tự ý tiếp tục (brief §10).
  Không phải OWNER_DECISION_REQUIRED (không có case nghiệp vụ mơ hồ nào cần
  phân loại AUTOMATE/MANUAL EXCEPTION ở đây) và không phải
  CHANGE_BUDGET_EXCEEDED (còn nhiều ngân sách, §11) — đúng là một khoảng
  trống kiến trúc thật, do các task khác (TASK-105B/C/E/108B) chưa được
  Owner cấp phép implementation.
```

### Explicit answers

```text
B2 PASS bằng real trace?                     YES
BH62063 end-to-end PASS?                     NO (B7/B8/B9 vẫn NOT_REACHED)
Golden expectation dùng làm production
  authority duy nhất?                        NO (bằng chứng có cấu trúc,
                                              thi hành bằng code, không phải
                                              chép trực tiếp oracle)
Production identity/price algorithm changed? NO (chỉ thêm một provenance
                                              type + đọc field có sẵn thay vì
                                              hardcode)
"Tồn" technical mapping invented?             NO (vẫn UNRESOLVED, không cần
                                              cho path này — N/A qua P00)
BH62063 hard-coded trong app/?                NO (§3, xác nhận bằng grep)
New task registered?                          NO
V4.2 started?                                 NO
TASK-105D reopened?                           NO
RC-2 opened?                                  NO
Merge/rebase/squash performed?                NO
Default branch changed?                       NO
```
