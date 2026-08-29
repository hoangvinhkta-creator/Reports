# S050 — GOLDEN ORDER #1 (BH62063) AS-IS VERTICAL TRACE

Phiên DIAGNOSTIC/TRACE, không phải implementation session. Mục tiêu duy
nhất: chạy/trace Golden Order #1 (`BH62063`) qua hệ thống hiện tại AS-IS để
xác định `FIRST_FAILING_BOUNDARY` trên đường tới oracle
`KpiPurchasePrice = 7.000.000 VND`, `EligibleKpiProfit = 500.000 VND`.
Không sửa blocker, không hoàn thiện `TASK-105C`/`TASK-105E`/`TASK-108B`,
không thay đổi architecture, không V4.2 adoption, không tạo task mới.

## 1. Git target

```text
Repository        : Reports
Branch (expected)  : trace/golden-order-1-as-is
Branch (thực tế)   : trace/golden-order-1-as-is
Base SHA (expected): 07e54a1d648bacae315eae45b5250a444bf9dd3e
HEAD (trước trace) : 07e54a1d648bacae315eae45b5250a444bf9dd3e  (khớp)
Upstream           : origin/trace/golden-order-1-as-is (0 ahead/0 behind)
Working tree        : clean
```

`bash scripts/branch_authority_check.sh` (chạy trước khi trace):

```text
DEFAULT_BRANCH  : claude/extract-upload-repo-gq2ws4
DEFAULT_TIP     : 7464ccaa784f13d887b2d5441d86136ff7d9a61d
HEAD_SHA        : 07e54a1d648bacae315eae45b5250a444bf9dd3e
WORKTREE        : CLEAN
CURRENT_BRANCH  : trace/golden-order-1-as-is
UPSTREAM        : origin/trace/golden-order-1-as-is
ahead default   : 6 commit   behind default : 0 commit
DIVERGENCE      : WITHIN_LIMITS
AUTHORITY       : BRANCH_WITH_UPSTREAM
RESULT          : AUTHORITY_OK
```

`git show --stat HEAD` xác nhận `HEAD` là commit S049
(`S049: Golden Order #1 (BH62063) Canonical Acceptance —
END_TO_END_ACCEPTANCE = DEFINED`), khớp brief.

## 2. Canonical entry state (đọc từ repo, không reopen)

```text
TASK-105D            = DONE                       (PROJECT_PROGRESS.md dòng 567; DEC-162)
DEC-162               = preserved, không sửa
DEC-163               = tồn tại (PROJECT_DECISIONS.md dòng 7336) — Owner Decision
                        chuyển END_TO_END_ACCEPTANCE: PENDING_OWNER_DATA → DEFINED
END_TO_END_ACCEPTANCE = DEFINED                    (PROJECT_PROGRESS.md dòng 512)
S049                   = ghi tại docs/sessions/S049-golden-order-1-canonical-acceptance.md
```

Không review lại INV-01..87 hay H-07 trong phiên này.

## 3. Golden business oracle (canonical, đọc từ
`docs/sessions/S049-golden-order-1-canonical-acceptance.md`)

```text
OrderID                        : BH62063
SaleDate                       : 2026-01-02
RawProductName                 : Máy giặt LG 10kg FV1410S4W1
TrackingCode                   : FV1410S4W1
PublicPurchaseCode              : FV1410S4W1
CrossSystemIdentityConfirmed    : YES
ExpectedCanonicalIdentity       : TRACKING:FV1410S4W1
ExpectedPriceSource              : "Tồn"  (TECHNICAL_SOURCE_MAPPING = UNRESOLVED tại S049)
ApplicablePriceDate              : 2026-01-02
ExpectedPurchasePrice            : 7.000.000 VND
PublicPurchaseFallbackIfUnavailable : AUTHORIZED (fallback-only, không phải preferred)
Quantity                          : 1
SellPrice                          : 7.500.000 VND
Discount                            : 0 VND
ExpectedKpiPurchasePrice            : 7.000.000 VND
ExpectedEligibleKpiProfit           : 500.000 VND
```

Oracle canonical, khớp prompt task, không có discrepancy.

## 4. RUNTIME_SOURCE_AVAILABLE

Repo chứa raw sales record thật cho `BH62063` trong fixture Golden Baseline
(không phải dữ liệu tự bịa):

```text
tests/fixtures/golden/period_2026_01.xlsx   (sheet "SỔ CHI TIẾT BÁN HÀNG",
                                             hàng 6, đã dùng để build Golden
                                             Baseline TASK-GOLDEN-BASELINE-001)
tests/fixtures/golden/expected/period_2026_01.json (orders_detail[0])
```

Nội dung hàng thật (đọc bằng `openpyxl`, cột theo header workbook):

```text
date         = 2026-01-02
order_id     = BH62063
note_raw     = BAN_HANG
product_raw  = Máy giặt LG 10kg FV1410S4W1
quantity     = 1
sell_price   = 7500000
total_sales  = 7500000
discount     = 0
employee_raw = Tín Phát 0869931931
```

Khớp tuyệt đối tọa độ oracle §3. `RUNTIME_SOURCE_AVAILABLE = YES`.

## 5. Actual execution (existing path, không sửa production)

```text
$ python3 -c "
from pathlib import Path
from app.pipeline import run_import
result = run_import(Path('tests/fixtures/golden/period_2026_01.xlsx'), config_dir=Path('config'))
order = next(o for o in result.orders if o.order_id == 'BH62063')
print(order.lines[0])
"
```

Kết quả thật (rút gọn, trường liên quan):

```text
order_id='BH62063'  date=2026-01-02  product_raw='Máy giặt LG 10kg FV1410S4W1'
quantity=Decimal('1')  sell_price=Decimal('7500000')  discount=Decimal('0')
accounting_purchase_price=None
price_source='Pending'
accounting_profit=None
```

Đây là kết quả thật từ `app.pipeline.run_import()` — production entry point
duy nhất tìm thấy trong repo (không có `pipeline_v2`/orchestrator khác;
`find app -iname "*pipeline*"` chỉ trả về `app/pipeline.py`).

### Diagnostic bổ sung (DIAGNOSTIC_ONLY, không tính là production PASS)

Gọi trực tiếp module `app/modules/product/identity/service.resolve_batch`
(module API, không qua `app.pipeline`) để quan sát hành vi hạ nguồn của
boundary identity khi được nối thủ công với registry rỗng:

```text
$ python3 -c "
from datetime import date
from app.modules.product.identity.registry import HistoricalConfirmedRegistry
from app.modules.product.identity.resolver import SalesRowRef
from app.modules.product.identity.service import resolve_batch
row = SalesRowRef(order_id='BH62063', sale_date=date(2026,1,2),
                   raw_product_identity='Máy giặt LG 10kg FV1410S4W1')
registry = HistoricalConfirmedRegistry()
def resolver_factory(): raise AssertionError('phải KHÔNG bao giờ được gọi cho batch toàn pre-cutover (INV-47)')
result = resolve_batch([row], registry=registry, resolver_factory=resolver_factory)
print(result.historical[0][1])
"
```

Kết quả:

```text
resolver_factory: KHÔNG bị gọi (đúng INV-47 — xác nhận bằng AssertionError
                   guard không kích hoạt)
outcome = PendingProduct(reason_code=PendingReason.PENDING_HISTORICAL_CONFIRMATION,
                          attempted_sources=(AttemptedSource.HISTORICAL_CONFIRMED_REGISTRY,))
```

`DIAGNOSTIC_ONLY` — module capability tồn tại và hoạt động đúng spec
(`INV-46`, `INV-47`, `INV-50`), nhưng đây KHÔNG phải một lời gọi từ
production path; `app.pipeline` không bao giờ tạo `SalesRowRef` hay gọi
`resolve_batch`.

## 6. Bảng boundary B0–B9

| Boundary | Expected | Actual | Status | Evidence |
|---|---|---|---|---|
| B0 Sales Input | OrderID/sale_date/raw product/qty/sell price/discount đọc được | `run_import()` trả `WorkingLine` đầy đủ 6 trường, khớp tuyệt đối oracle | **PASS** | §5 (execution thật) |
| B1 Identity Input | Raw product string là input hợp lệ cho identity-resolution boundary | Chuỗi `"Máy giặt LG 10kg FV1410S4W1"` là input hợp lệ về mặt cấu trúc cho `SalesRowRef.raw_product_identity` (xác nhận bằng diagnostic call §5) | **PASS** (chỉ ở mức data-shape/capability — không suy ra runtime đã nối, xem B2) | §5 diagnostic; `app/modules/product/identity/resolver.py:724-743` |
| B2 Identity Resolution | `TRACKING:FV1410S4W1` | `app/pipeline.py` (production entry point duy nhất) KHÔNG BAO GIỜ import/gọi `app.modules.product.identity.service.resolve_batch` hay bất kỳ resolver nào — xác nhận bằng `grep -rln "resolve_batch" app/` chỉ trả về chính module identity và test files. `apply_prices()` (`price_engine.py`) dùng thẳng `line.product_raw` làm "interim key" (TASK-402 product_mapper chưa tồn tại) — bỏ qua hoàn toàn nhánh cutover của `DEC-154`/`TASK-105D`. | **NOT_WIRED** ← **FIRST_FAILING_BOUNDARY** | §7 grep evidence; `app/modules/pricing/price_engine.py:17-28`; `app/modules/pricing/provider.py:9-12` |
| B3 Price Request | Request cho `2026-01-02` được tạo | NOT_REACHED (runtime). Static: `TASK-105E` (chủ sở hữu composition P00–P11, `DEC-156` §5) = `PLANNED / OUTLINE / READY GATE BLOCKED / NOT AUTHORIZED`; không có thư mục implementation nào dưới `app/` (`find app -iname "*105e*" -o -iname "*composition*"` rỗng) | NOT_REACHED (downstream: NOT_IMPLEMENTED) | PROJECT_PROGRESS.md dòng 428 |
| B4 Preferred Source "Tồn" | `"Tồn"` có technical mapping | NOT_REACHED (runtime). Static: `grep -rn "Tồn" app/ config/ tests/ --include="*.py"` = 0 kết quả (ngoại trừ "tồn tại" — không liên quan). Không có định nghĩa kỹ thuật nào của `"Tồn"` trong code | NOT_REACHED (downstream: `TECHNICAL_SOURCE_MAPPING = UNRESOLVED`, xem §8) | §8 |
| B5 Purchase Price | `7.000.000 VND` cho `2026-01-02` | NOT_REACHED qua nhánh oracle (`TASK-105D`→`105C/105E`). Static/thực thi song song: pipeline hiện tại (bước 8, `PendingPriceProvider`) trả `accounting_purchase_price=None`, `price_source='Pending'` cho MỌI dòng — không phụ thuộc `sale_date`/cutover; `config/` không có file price nào (`find config -iname "*price*"` rỗng); `FilePriceProvider` (`TASK-105B`) tồn tại nhưng "never runs in the Golden path and is never the pipeline default" (docstring `file_price_provider.py:17-20`), và dù có cũng chỉ phục vụ `PUBLIC_PURCHASE`, không phải nhánh `"Tồn"` | NOT_REACHED (theo path oracle); DOWNSTREAM_OBSERVATION: path song song hiện có luôn trả Pending | §5 execution; `app/modules/pricing/provider.py:32-38`; `app/modules/pricing/file_price_provider.py:17-20` |
| B6 Provenance | `"Tồn" + date + identity` | NOT_REACHED | NOT_REACHED | — |
| B7 KPI Input | Resolved purchase price tới KPI boundary | NOT_REACHED. Static: không tìm thấy wiring nào truyền `accounting_purchase_price`/identity resolved tới một module KPI | NOT_REACHED (downstream: NOT_IMPLEMENTED) | `app/pipeline.py:18-24` (docstring: "Adjustment persistence + EligibleKpiProfit ... TASK-202/302/305 ... Out of scope here") |
| B8 KPI Calculation | `EligibleKpiProfit = (SellPrice−KpiPurchasePrice)×Quantity−Discount` | NOT_REACHED (runtime). Static: `grep -rln "EligibleKpiProfit\|KpiPurchasePrice" app/` chỉ khớp `app/pipeline.py` (docstring liệt kê "out of scope"). Module `profit_engine.py` chỉ có `AccountingProfit = (SellPrice−AccountingPurchasePrice)×Quantity` — công thức khác, không có số hạng Discount, tách biệt hoàn toàn KPI (DEC-126) | NOT_REACHED (downstream: NOT_IMPLEMENTED) | `app/modules/profit/profit_engine.py:1-13` |
| B9 E2E Result | `500.000 VND` + provenance đúng | NOT_REACHED | NOT_REACHED — `SYSTEM_RESULT = unavailable` | — |

Toàn bộ trạng thái B3–B9 là `NOT_REACHED` ở tầng runtime vì `FIRST_FAILING_BOUNDARY = B2`
đã chặn dòng chảy thật; các quan sát "static/downstream" ghi ở cột Actual
KHÔNG được dùng để đổi `FIRST_FAILING_BOUNDARY`.

## 7. B2 — chi tiết NOT_WIRED

```text
$ grep -rln "resolve_batch" app/ tests/ --include="*.py"
app/modules/product/identity/service.py     (định nghĩa)
app/modules/product/identity/__init__.py    (re-export)
app/modules/product/identity/binding.py     (nội bộ module)
tests/test_105d_persistence.py
tests/test_105d_cutover_registry.py
tests/test_105d_boundaries.py
tests/test_105d_resolution.py

$ find app -iname "*pipeline*" -o -iname "*orchestrat*" -o -iname "*entrypoint*"
app/pipeline.py     ← DUY NHẤT

$ grep -n "product.identity\|resolve_batch" app/pipeline.py
(không có kết quả)
```

`app/pipeline.py` bước 8 gọi thẳng `apply_prices(lines, provider)` với
`provider = PendingPriceProvider()` mặc định (`price_engine.py:17-28`,
`provider.py:9-12,32-38`) — dùng `line.product_raw` làm key trực tiếp,
không hề đi qua `CUTOVER_DATE`/`HistoricalConfirmedRegistry`/
`ProductIdentityResolver` của `DEC-154`. Đây là hai đường hoàn toàn tách
biệt trong cùng repo: (a) module `product/identity/*` — implementation đầy
đủ, có test riêng, `TASK-105D = DONE`; (b) `app.pipeline` production path —
không biết đến (a) tồn tại. `TASK-105D = DONE` là DONE của module đơn lẻ
theo Completion Gate của chính nó — không đồng nghĩa runtime pipeline đã
gọi module đó.

Ngoài `NOT_WIRED`, một phát hiện phụ (compounding, không đổi
`FIRST_FAILING_BOUNDARY`): dù wiring có tồn tại, `HistoricalConfirmedRegistry`
hiện KHÔNG có entry nào cho `BH62063` (hay bất kỳ order nào) trong repo —
`grep -rln "ConfirmHistoricalEntry" .` chỉ khớp định nghĩa module và 2 file
test; không có data file/seed nào populate registry với dữ liệu thật. Gọi
diagnostic `resolve_batch` với registry rỗng (§5) xác nhận trả về
`PendingProduct(PENDING_HISTORICAL_CONFIRMATION)` — tức là ngay cả sau khi
wiring được thêm, boundary này sẽ dừng lại ở `DATA_MISSING` cho tới khi có
entry `CONFIRMED` thật cho `BH62063`.

## 8. "Tồn" investigation (§13 brief)

```text
$ grep -rn "Tồn" app/ config/ tests/ --include="*.py" | grep -v "tồn tại"
(không có kết quả)
```

```text
OWNER BUSINESS TRUTH  : "Tồn" = confirmed expected source cho BH62063
                         (Owner-confirmed, DEC-163, S049).
TECHNICAL IMPLEMENTATION : không tồn tại — không một hằng số, enum, comment
                         hay identifier nào trong app/ chứa "Tồn". Tài liệu
                         (`S049`, `DEC-163`, `PROJECT/PROJECT_PROGRESS.md`) tự ghi
                         nhận rõ TECHNICAL_SOURCE_MAPPING = UNRESOLVED và
                         cấm tự suy diễn "Tồn" → phist NCC / inv.cong /
                         Public Purchase / vendor — không có mapping nào bị
                         bịa trong S050 này.
```

`TECHNICAL_SOURCE_MAPPING = UNRESOLVED` xuất hiện SAU `FIRST_FAILING_BOUNDARY`
thật (`B2`, tại `B4` trong bảng) — không phải nguyên nhân dừng đầu tiên,
dù cả hai đều cần giải quyết trước khi `BH62063` đi hết được path.

## 9. Identity trace — cutover semantics (§11 brief)

```text
CUTOVER_DATE (DEC-154, registry.py:51) = 2026-09-01
BH62063.sale_date                       = 2026-01-02   → PRE-CUTOVER
```

Theo `DEC-154`/`INV-47`: pre-cutover phải bypass HOÀN TOÀN
resolver/catalog/price-provider, chỉ có hai kết cục
(`HISTORICAL_CONFIRMED_REPORT` hoặc `PENDING_HISTORICAL_CONFIRMATION`) từ
`HistoricalConfirmedRegistry`. Diagnostic §5 xác nhận đúng ngữ nghĩa này ở
mức module (resolver_factory không bị gọi). Nhưng `app.pipeline` không đi
qua cổng định tuyến này chút nào (§7) — nên trong runtime thật, BH62063
không hưởng cả bypass đúng lẫn kết cục Pending đúng của `INV-47`; nó chỉ
đi qua `PendingPriceProvider` không điều kiện, không phân biệt
pre/post-cutover.

## 10. Price value/unit (§15 brief)

Raw fixture lưu giá trị VND thô (`sell_price=7500000`, không phải `7500`
nghìn) — khớp `ADR-103`/`DEC-145` (Decimal, VND thô). Vì `B5` chưa reached
qua path oracle, chưa có boundary conversion nào để trace unit cho
`KpiPurchasePrice`; ghi lại làm điểm cần xác minh khi implement boundary
này (không nhân đôi ×1000 một cách suy diễn).

## 11. KPI trace (§16 brief)

```text
MANUAL_ORACLE = (7.500.000 − 7.000.000) × 1 − 0 = 500.000 VND   (tính tay,
                 KHÔNG phải system result)
SYSTEM_RESULT = unavailable — B8 NOT_REACHED, và ngay cả module `profit_engine.py`
                cũng chỉ implement `AccountingProfit` (công thức khác, không
                Discount) — `EligibleKpiProfit` NOT_IMPLEMENTED trong toàn bộ
                `app/`.
```

## 12. FIRST_FAILING_BOUNDARY

```text
FIRST_FAILING_BOUNDARY : B2 — Product Identity Resolution

FAILURE_TYPE            : NOT_WIRED
                          (implementation tồn tại đầy đủ ở
                          app/modules/product/identity/*, TASK-105D = DONE
                          theo Completion Gate riêng — nhưng app/pipeline.py,
                          production entry point duy nhất, không bao giờ gọi
                          nó)

ROOT_CAUSE               : app.pipeline.run_import() → step 8 (apply_prices)
                          dùng thẳng line.product_raw làm price-lookup key
                          qua PendingPriceProvider, hoàn toàn không biết tới
                          CUTOVER_DATE / HistoricalConfirmedRegistry /
                          ProductIdentityResolver của DEC-154/TASK-105D.
                          Hai hệ thống — module identity (đã DONE, có test)
                          và pipeline sản xuất — tồn tại song song, chưa
                          từng được nối với nhau.
```

## 13. MINIMUM_NEXT_CHANGE (chỉ đề xuất, không thực hiện)

```text
MINIMUM_NEXT_CHANGE:
Nối một bước mới vào app.pipeline (sau step 7, trước/thay step 8 hiện tại)
gọi app.modules.product.identity.service.resolve_batch() cho các dòng có
sale_date < CUTOVER_DATE (2026-09-01), dùng kết quả HistoricalConfirmed/
PendingProduct để set accounting_purchase_price/price_source thay vì gọi
thẳng PendingPriceProvider cho nhánh pre-cutover. Đây là vertical slice nhỏ
nhất di chuyển được BH62063 qua B2 — KHÔNG cần TASK-105C/105E/108B đầy đủ.

Lưu ý: chỉ riêng thay đổi wiring này CHƯA đủ để BH62063 đạt PASS toàn phần
— vẫn cần một entry CONFIRMED thật trong HistoricalConfirmedRegistry cho
(order_id=BH62063, raw_identity_key="Máy giặt LG 10kg FV1410S4W1",
sale_date=2026-01-02) với confirmed_purchase_price=7.000.000 (DATA_MISSING,
§7), và vẫn cần giải quyết TECHNICAL_SOURCE_MAPPING của "Tồn" (§8) trước
khi provenance đúng oracle. Cả hai việc đó là phạm vi của (các) session sau,
không phải phần của MINIMUM_NEXT_CHANGE này.

EXPECTED_VERTICAL_IMPACT:

Before : BH62063 dừng ở B2 (NOT_WIRED) — accounting_purchase_price luôn
         None/Pending bất kể registry.
After  : BH62063 tới được B2 thật (resolver được gọi đúng cổng), dừng ở
         DATA_MISSING (registry rỗng) thay vì NOT_WIRED — boundary tiếp
         theo cần giải quyết đổi từ "chưa nối" sang "thiếu dữ liệu xác
         nhận" — một loại việc khác (DATA SESSION), không phải WIRING nữa.
```

## 14. Changes / no-op guarantees

```text
Production diff (app/**, config/**, Tracking) : 0
Test implementation diff                        : 0
Fixture diff                                     : 0
New task IDs registered                          : 0
RC opened                                         : NO
V4.2 adopted                                      : NO
TASK-105C implementation started                  : NO
TASK-105E implementation started                  : NO
TASK-108B implementation started                  : NO
Synthetic success used                             : NO (mọi lệnh gọi module
                                                    trực tiếp trong §5 đánh
                                                    dấu DIAGNOSTIC_ONLY,
                                                    không tính production PASS)
```

## 15. Validation

```text
$ bash scripts/branch_authority_check.sh          → AUTHORITY_OK
$ python3 governance/scripts/governance/validate_structure.py
GOVERNANCE STRUCTURE: PASS — 21 required paths.

$ python3 governance/scripts/governance/validate_project_state.py
PROJECT STATE: PASS

$ python3 governance/scripts/governance/validate_evidence.py
EVIDENCE VALIDATION: PASS — 88 REQUIRED PASS evidence record(s).

$ python3 governance/scripts/governance/validate_task_completion.py
TASK COMPLETION: PASS — Checked 7 DONE task(s).

$ python3 governance/scripts/governance/validate_reference_integrity.py
REFERENCE INTEGRITY: FAIL — 3 reference không phân giải được
  (docs/tasks/TASK-REM-T06-repository-root-hygiene.md → /README.md,
  CODE_OF_CONDUCT.md, CONTRIBUTING.md)
  — PRE-EXISTING BASELINE (TASK-REM-T06, không đổi bởi S050), khớp đúng
  reference integrity trước phiên này.

$ python3 -m pytest tests/test_golden_baseline.py -q
58 passed, 2 skipped                    — khớp reference (58 passed, 2 skipped)

$ python3 -m pytest -q
965 passed, 11 skipped                  — khớp reference (965 passed, 11 skipped)
```

0 regression. `app/**`, `config/**`, `Tracking`, mọi file test — 0 byte đổi
trong phiên này; toàn bộ thay đổi giới hạn ở artifact này.

## 16. Kết luận S050

```text
S050 FINAL STATE            : PASS (FIRST_FAILING_BOUNDARY xác định đủ evidence)
NEXT SESSION CLASSIFICATION : WIRING SESSION
                               (nối app.pipeline với product/identity
                               service cho nhánh pre-cutover — sau đó lộ ra
                               DATA SESSION kế tiếp cho HistoricalConfirmedRegistry
                               entry thật + OWNER DECISION cho "Tồn" mapping)
```

### Explicit answers

```text
FIRST_FAILING_BOUNDARY identified? YES  (B2, NOT_WIRED)
BH62063 end-to-end PASS?           NO
Production changed?                NO
Synthetic success used?            NO
New task registered?               NO
V4.2 started?                      NO
Default changed?                   NO
Merge performed?                   NO
```
