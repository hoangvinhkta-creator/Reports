# S061 — TASK-105E: Production Price Composition (Session 1/2)

Ngày: 2026-08-29
Task Mode: MAJOR
Task: `TASK-105E` — Price Resolution Composition (`P00–P11`)
Nhánh: `claude/task-105e-price-composition-sjk4ee`
Base SHA: `740f396acb11cf279f303f09ea22dffd0ca95462`

> Chỉ thị mở phiên ghi base SHA là `740f396acb11cf279f303f090ea22dffd0ca95462`
> (41 ký tự — thừa một `0` ở vị trí 25). SHA thật của `HEAD` lúc mở phiên là
> `740f396acb11cf279f303f09ea22dffd0ca95462` (40 ký tự); tiền tố
> `740f396acb11cf279f303f09` và hậu tố `ea22dffd0ca95462` khớp chính xác. Đây
> là lỗi chép trong chỉ thị, không phải lineage khác — `git rev-parse HEAD`
> trả đúng SHA 40 ký tự trên, worktree sạch, nhánh là nhánh session được cấp.

## 1. Vấn đề thật mà phiên này đóng

`Reports History Reader V1` đã được review độc lập và tích hợp (S060,
`740f396`), nhưng nó **chưa từng được production gọi một lần nào**:

```text
TRƯỚC S061
  run_import_production()
    ├─ pre-cutover  (sale_date < 2026-09-01) → HistoricalConfirmedRegistry (P00)
    └─ phần còn lại                          → PendingPriceProvider  ← 100% Pending
                                                (reader KHÔNG nằm trên đường này)
```

`app/composition.py` nạp ba nguồn canonical của nhánh pre-cutover và không nạp
nguồn nào cho nhánh post-cutover. Reader là một `PriceProvider` phải được
caller dựng và truyền TƯỜNG MINH; caller duy nhất từng làm việc đó là test.
`TrackingCatalogSnapshot`/`PublicPurchaseSourceVersion`/`StoreView` cũng không
được nạp ở đâu cả, nên identity post-cutover chưa bao giờ được resolve trong
production.

Nói cách khác: cutover Product Identity `01/09/2026` cách phiên này ba ngày,
và tại thời điểm đó pipeline production chưa có đường nào để trả lời câu hỏi
"giá vốn của một đơn sau cutover là bao nhiêu" ngoài `Pending`.

```text
SAU S061
  run_import_production()
    ├─ pre-cutover  → HistoricalConfirmedRegistry (P00)  — KHÔNG ĐỔI
    └─ post-cutover → PostCutoverPriceComposition (TASK-105E)
                        ├─ TASK-105D resolve identity (catalog + PP + store)
                        ├─ TRACKING:<mã>        → Reports History Reader V1
                        └─ PUBLIC_PURCHASE:<mã> → bảng giá Public Purchase (105B)
                        └─ mọi kết cục khác     → Pending → Missing.PurchasePrice
```

## 2. Trace production TRƯỚC khi code (không code theo sơ đồ giả định)

Đường đi thật đã đọc, không phải suy ra:

```text
app/composition.py::run_import_production
  → app/pipeline.py::run_import → build_working_data
      1 raw_reader → 2 preview → 3 normalizer → 4 employee_mapper
      5 order_builder → 6 lead_source
      8 _apply_pre_cutover_identity   (chỉ dòng date < CUTOVER_DATE)
           → service.resolve_batch(registry=…, resolver_factory=…)
        apply_prices(remaining_lines, price_provider or PendingPriceProvider())
      9 profit_engine → 9b kpi_profit_engine → 10 conversion_engine
      11 Validator.build_queue_for → ReviewQueue (TASK-110)
```

Ba phát hiện quyết định thiết kế:

1. `_post_cutover_resolver_not_wired` **chưa từng được gọi**. Nó là default
   của `identity_resolver_factory`, nhưng `_apply_pre_cutover_identity` chỉ đưa
   dòng pre-cutover vào `resolve_batch`, nên nhánh post-cutover của
   `resolve_batch` luôn rỗng và factory không bao giờ chạy (`INV-47`). Docstring
   cũ của nó nói "TASK-105E chưa được authorize" — nay không còn đúng, đã sửa
   thành đúng vai trò thật: guard của nhánh **pre**-cutover.
2. `apply_prices` gắn `price_source` từ MỘT thuộc tính lớp của provider. Một
   composition trả giá từ nhiều nguồn khác nhau không biểu diễn được qua biên
   đó, nên nhánh post-cutover tự đặt `accounting_purchase_price` +
   `price_source`, y hệt cách `_apply_pre_cutover_identity` đã làm cho P00.
   Không tạo abstraction mới khi abstraction cũ đủ; tạo khi nó không đủ.
3. Kiến trúc adapter hiện hành là **file đã commit → loader → DI vào
   `run_import`** (`load_registry_from_jsonl`,
   `load_confirmed_adjustments_from_jsonl`, `load_eligible_costs_authority`).
   Nguồn giá post-cutover tái sử dụng đúng kiến trúc đó, không phát minh cơ chế
   thứ hai.

## 3. Thứ tự ưu tiên nguồn giá THẬT (và một khoảng trống phải báo)

`DEC-154` §7 quy phạm:

```text
TRACKING identity        : 1. HistoricalVendorMin (105C)  2. Public Purchase qua
                           cross-map (105B)               3. Pending
PUBLIC_PURCHASE identity : 1. Public Purchase (105B)      2. Pending
```

Trạng thái thật của hai nguồn ấy:

```text
TASK-105C  HistoricalVendorMin        = BLOCKED / NOT AUTHORIZED (PROJECT_PROGRESS)
TASK-105B  FilePriceProvider          = FROZEN, NOT ACTIVATED, chưa có dataset thật
Reports History Reader V1 (S060)      = ACCEPT_AFTER_REPAIR + INTEGRATED
```

**`P03` không thể chạy, và đó là kết luận chứ không phải một lối tắt.** `P03`
đòi "không có valid vendor candidate tại `sale_date`" — một *absence đã xác
định*: phải hỏi nguồn vendor rồi nhận về "không có". Nguồn ấy chưa tồn tại,
nên câu hỏi chưa từng được đặt. "Chưa hỏi" không phải "đã hỏi và không có";
biến cái thứ nhất thành cái thứ hai chính là phép suy diễn mà Scope của
`TASK-105E` cấm (source failure ≠ determined absence, tiền lệ
`CHECK-105C-17`). Hệ quả: một identity TRACKING **không** mượn giá công khai,
kể cả khi có `CrossSystemProductMapping` CONFIRMED và bảng giá công khai có
đúng mã ấy — có test khẳng định điều này
(`test_a_tracking_identity_never_borrows_a_public_purchase_price`).

**Khoảng trống phải báo (`F-01`, xem §10).** Không artifact frozen nào đặt
Reports History Reader V1 vào một ô của bảng `P00–P11`: `DEC-154` §7 viết
trước khi reader tồn tại, và S060 tự tuyên bố "bổ sung một NGUỒN cho nhánh
TRACKING" mà không định vị nó so với `P01`. Phiên này đặt reader làm nguồn
Tracking duy nhất được nối, theo đúng luồng mà chỉ thị mở phiên §5 mô tả
(`TRACKING → Tracking History Reader → resolved → price resolution`).
Hôm nay lựa chọn ấy **không quan sát được**: `P01` không có nguồn, `P03` bị
chặn, nên mọi cách đặt reader vào bảng đều cho cùng một hành vi
(reader → Pending). Nó **trở nên quan sát được** ngay khi `TASK-105C` được cấp
phép, và đó là lúc Owner phải quyết định thứ tự — không phải một phiên
implementation.

## 4. Điểm tích hợp

| Thành phần | Vị trí | Vai trò |
|---|---|---|
| `PostCutoverPriceComposition` | `app/modules/pricing/resolution/composition.py` | Chủ sở hữu `P00–P11` |
| `PriceResolutionSources` | `app/modules/pricing/resolution/sources.py` | Nạp + đóng băng bằng chứng MỘT LẦN/import |
| `load_tracking_price_history_capture` | `app/modules/pricing/tracking_history/capture_file.py` | File capture → `TrackingPriceHistorySnapshot` |
| `capture_purchase_price_history.py` | `tools/tracking/` | RTDB read-only → file bất biến (ngoài `app/modules/`) |
| `build_price_composition` | `app/composition.py` | Seam production; trả instance để audit |
| tham số `price_composition` | `app/pipeline.py` | DI, mặc định `None` = hành vi cũ y nguyên |

Reader được gọi **qua `TrackingHistoryPriceProvider`**, không gọi thẳng: không
dòng logic nào của reader bị chép lại, và provider tự chặn
`PUBLIC_PURCHASE:<mã>` lần thứ hai bằng `identity_index` của chính nó — hai
lớp độc lập cùng khẳng định namespace không tráo chỗ.

`price_provider` và `price_composition` **loại trừ lẫn nhau**: truyền cả hai
là `ValueError`. Hai nguồn cùng quyền ghi `accounting_purchase_price` thì
"giá này đến từ đâu" không còn trả lời được từ output, và đó đúng là câu hỏi
`price_source` sinh ra để trả lời.

## 5. Cơ chế thu thập nguồn + snapshot/freeze

Một lần import đọc mọi nguồn **đúng một lần**, đóng băng thành object bất biến,
và mọi `PriceResolutionRecord` mang **cùng một instance** `PriceEvidenceSnapshot`
— kiểm được bằng `is`, không phải bằng niềm tin
(`test_one_import_uses_exactly_one_frozen_evidence_snapshot`).

```text
PriceEvidenceSnapshot
  tracking_price_history_capture_id / captured_at
  tracking_catalog_capture_id
  public_purchase_version_id / content_hash
  identity_store_revision
  business_timezone_label / provenance
  vendor_price_source = "NOT_AUTHORIZED:TASK-105C"
```

Ba trạng thái của một nguồn KHÔNG được gộp:

```text
file không tồn tại    → None      → nguồn CHƯA ĐƯỢC NỐI   → Pending có lý do riêng
file hỏng             → raise     → LỖI NẠP               → không sinh report giả
capture_status FAILED → raise      → INV-12, LỖI CỨNG      → không bao giờ thành Pending
```

Múi giờ nghiệp vụ nằm ở `config/price_resolution.yaml` (UTC+07:00), fail-closed:
thiếu/sai → nhánh TRACKING Pending, **không** có mặc định UTC+7 thầm lặng. Đây
là biên duy nhất nơi `SaleInterval.for_sale_date` nhận `tzinfo`.

## 6. Hai cutover — không gộp, không dời

```text
Tracking price-history data cutover : 2026-08-29 19:35:37 Firebase server time
                                      (một datetime có múi giờ)
Product Identity architecture cutover: 2026-09-01  (CUTOVER_DATE, một date)
```

`CUTOVER_DATE` không đổi một byte. Test khẳng định Python **từ chối** so sánh
trực tiếp hai giá trị ấy (`TypeError`), và một đơn ngày `30/08/2026` — sau mốc
dữ liệu, trước mốc identity — vẫn đi nhánh lịch sử và composition **không ghi
bản ghi nào** cho nó.

## 7. Kết quả

### Golden / Batch 50

| Chạy | Kết quả | So với base |
|---|---|---|
| `tests/test_golden_baseline.py` | 58 passed, 2 skipped | KHÔNG ĐỔI |
| Golden #1 `BH62063` | `AccountingPurchasePrice = 7.000.000`, `EligibleKpiProfit = 500.000` | KHÔNG ĐỔI |
| Golden #3 `BH62439` dòng 52 | `AccountingProfit = 500.000`, `EligibleKpiProfit = 400.000` | KHÔNG ĐỔI |
| Golden #4 `BH62439` dòng 53 | SAFE PENDING, `Missing.PurchasePrice` | KHÔNG ĐỔI |
| Golden #1/#3/#4 focused | 16 passed | KHÔNG ĐỔI |

Batch 50 (`tools/analysis/batch_50_real_orders.py tests/fixtures/golden/period_2026_01.xlsx`):

```text
INPUT = 50   AUTO = 1   REVIEW_QUEUE = 49
PENDING_NOT_QUEUED = 0   ERROR = 0   SILENTLY_DROPPED = 0
AUTOMATION_RATE = 2,0%   ORDER_ACCOUNTING_RATE = 100,0%
```

Giống hệt baseline S059. Batch 50 nằm trong tháng 01/2026, tức **trước** mốc
dữ liệu Tracking 29/08/2026, nên `TASK-105E` không được phép và không hề làm
nó tự động hơn. Baseline tháng 8/2026 không được dùng để giải đơn tháng 1/2026.

### Test

```text
tests/test_105e_price_composition.py     43 passed   (mới)
tests/test_golden_baseline.py            58 passed, 2 skipped
Golden #1/#3/#4                          16 passed
FULL pytest                            1155 passed, 11 skipped, 0 failed
                                       (base: 1112 passed, 11 skipped — +43, 0 hồi quy)
                                       (đo SAU commit; trước commit là 1153 + 2 test
                                        `git diff HEAD` đỏ do worktree dirty — xem F-03)
```

Hai test `TestG25GoldenBaselineUnchanged` chạy `git diff HEAD -- <file>` và đỏ
khi worktree còn dirty; chúng xanh trở lại sau commit. Xem `F-03`.

### Validator

```text
validate_structure          PASS
validate_project_state      PASS
validate_evidence           PASS   (88 record)
validate_task_completion    PASS   (7 task DONE)
validate_reference_integrity FAIL  — đúng 3 issue tiền tồn TASK-REM-T06
                                     (REG-01), không đổi so với base
```

## 8. Files changed

Production:
- `app/modules/pricing/resolution/__init__.py` (mới)
- `app/modules/pricing/resolution/sources.py` (mới)
- `app/modules/pricing/resolution/composition.py` (mới)
- `app/modules/pricing/tracking_history/capture_file.py` (mới)
- `tools/tracking/__init__.py` (mới)
- `tools/tracking/capture_purchase_price_history.py` (mới)
- `config/price_resolution.yaml` (mới)
- `app/composition.py` (+64 / −21)
- `app/pipeline.py` (+45 / −16)
- `app/modules/domain/models.py` (+8)

Test/doc:
- `tests/test_105e_price_composition.py` (mới, 43 test)
- `tests/test_golden_baseline.py` (+8 / −1 — khoá chữ ký `run_import`, thêm
  đúng một tham số optional)
- `docs/sessions/S061-task-105e-production-price-composition.md` (file này)
- `docs/tasks/TASK-105E-price-resolution-composition.md`
- `PROJECT/PROJECT_PROGRESS.md`, `PROJECT/REVIEW_BUDGET_LEDGER.md`

Không sửa: Golden fixture, expected file, `data/**`, repo `Tracking`,
`file_price_provider.py`, `app/modules/product/identity/**`,
`app/modules/pricing/tracking_history/{reader,provider,snapshot}.py`.

## 9. Business rule / architecture

Không thay đổi business rule nào. `DEC-143` (`EligibleCosts = {}` closed empty
set, `OtherKpiAdjustment = 0`), `DEC-144` (confirmed adjustment / determined
absence / unknown), `CUTOVER_DATE = 2026-09-01`, ngữ nghĩa `HistoricalVendorMin`,
`sentinel 0`, và toàn bộ fail-safe của reader đều giữ nguyên.

Thay đổi kiến trúc: **có, và nằm đúng trong ownership của `TASK-105E`** —
`DEC-156` §5 cấp cho task này quyền là "nơi DUY NHẤT được phép wire provider
vào pipeline". Cụ thể: một tham số DI optional mới trên `run_import`/
`build_working_data`, và một package composition mới. Không đổi biên
`PriceProvider`, không đổi `TASK-105D`, không đổi `TASK-105B`.

## 10. Finding

### BLOCKING (cho phiên này): 0

### OWNER_DECISION_REQUIRED — không chặn phiên này

- **`F-01` — vị trí của Reports History Reader V1 trong bảng `P00–P11` chưa
  được quyết định.** `DEC-154` §7 không có ô cho nó; S060 không định vị nó so
  với `P01`. Phiên này đặt nó làm nguồn Tracking duy nhất được nối, theo luồng
  của chỉ thị mở phiên §5. Hôm nay không quan sát được (P01 không có nguồn,
  P03 bị chặn). **Retrigger: trước khi `TASK-105C` được cấp phép implementation.**
- **`F-05` — credential/vận hành của công cụ capture.** `tools/tracking/
  capture_purchase_price_history.py` nhận `--database-url` và đọc token từ
  `TRACKING_RTDB_TOKEN`; không có credential nào được bịa hay nhúng. Ai chạy
  nó, ở đâu, với quyền gì, và file capture có được commit vào repo hay không
  là quyết định vận hành của Owner. Phiên này không chạy nó (không có mạng tới
  Firebase, không có credential) — hợp đồng dữ liệu giữa công cụ và loader
  được kiểm bằng vòng khép kín có `fetch` tiêm vào.

### HARDENING

- **`F-02` — `P03`/`P09` không có đường tới.** Có test khẳng định; nhãn
  `PUBLIC_PURCHASE_NO_VENDOR_PRICE` đã định nghĩa đầy đủ và tách khỏi
  `PUBLIC_PURCHASE_NO_TRACKING` (`DEC-154` §10). Mở khi `TASK-105C` được cấp phép.
- **`F-03` — hai gate `TestG25GoldenBaselineUnchanged` là gate RỖNG sau commit.**
  Chúng so `git diff HEAD`, nên một thay đổi nằm TRONG chính commit đang xét thì
  chúng không thấy. Đây là khiếm khuyết tiền tồn của `CHECK-105D-25`, không phải
  do phiên này gây ra, và sửa nó là đổi gate đã freeze của `TASK-105D` — ngoài
  phạm vi. Ghi lại để Session 2 biết chúng không phải bằng chứng Golden bất biến;
  bằng chứng thật là `tests/test_golden_baseline.py` chạy PASS 58/2 và diff của
  `tests/fixtures/golden/` là rỗng (đã kiểm bằng `git status`).
- **`F-04` — `WAITING_REAL_POST_CUTOVER_DATA`.** Repo không có đơn thật nào
  `sale_date >= 2026-09-01`, và không có file capture production nào cho cả ba
  nguồn post-cutover. Wiring được chứng minh bằng focused integration fixture
  chạy qua `run_import()` thật với ba nguồn canonical thật; nhánh production
  seam (`run_import_production`) được chứng minh trên dữ liệu post-cutover với
  nguồn giá đúng như trên đĩa hôm nay (chưa capture) — kết quả: 0 crash,
  0 đơn mất, 0 giá bịa, 100% Pending vào Review Queue.
- Theo chỉ thị mở phiên §2, repair thẩm quyền dấu thời gian phía Tracking
  (`1821af06…` → `fd3c048a…`) **đã** merge, deploy và nhận 100% traffic, và
  RTDB Rules đã deploy. Điều đó đóng `B-02` của S060 (độ phủ chỉ mở sau deploy).
  Phiên này không tự xác minh được sự kiện ấy từ repo Reports — ghi lại theo
  đúng nguồn là chỉ thị Owner, không phải quan sát của phiên.

### EXCEPTION_CANDIDATE: 0

Không finding nào thoả cả ba điều kiện (`frequency count` thật từ batch ≥ 50 +
fail-safe route vào canonical Review Queue + ước tính > 100 LOC production).
Batch 50 không phát sinh case post-cutover nào (cohort tháng 01/2026).

### DEFERRED_BY_MINIMAL_FIX

| ID | Nội dung | Lý do | Fail-safe hiện tại | Retrigger |
|---|---|---|---|---|
| `D-01` | Không có công cụ capture cho `TrackingCatalogSnapshot` (chỉ có cho price history) | Hình dạng export danh mục thuộc `TASK-105D`/vận hành Tracking; nạp file đã có loader strict | Catalog vắng → `IDENTITY_SOURCES_UNAVAILABLE` → Pending → Review Queue | Lần import post-cutover thật đầu tiên |
| `D-02` | Chưa có `PublicPurchaseSourceVersion` production | Là DONE blocker của `TASK-105B`; `HB-105B-03/05/10` phải đóng TRƯỚC lần nạp dataset thật đầu tiên | PP vắng → `PUBLIC_PURCHASE_SOURCE_UNAVAILABLE` → Pending | Khi Owner cấp dataset Public Purchase thật |
| `D-03` | `P03`/`P09` chưa có đường tới | `TASK-105C` `BLOCKED / NOT AUTHORIZED` | TRACKING unresolved → Pending, không mượn giá công khai | `TASK-105C` được cấp phép |
| `D-04` | `PriceResolutionRecord` chưa đi vào `ReviewItem` | Mở rộng shape `ReviewItem`/`WorkingLine` thuộc `TASK-110`/`TASK-201`, ngoài Scope Lock phiên này | Bản ghi đầy đủ đi BÊN CẠNH kết quả (`composition.records`), Review Queue vẫn phủ 100% dòng Pending | Màn hình review (`TASK-305`) hoặc persistence (`TASK-201`) |

## 11. Trạng thái

`SESSION 1 = PASS`.

Composition production đã được nối và chứng minh; Reports History Reader V1
không còn là mã đứng riêng. **KHÔNG tuyên bố `TASK-105E = DONE`**: Completion
Gate của task chưa được soạn/freeze bởi một authority riêng, và capability cần
Independent Review (Session 2) + dữ liệu post-cutover thật.
