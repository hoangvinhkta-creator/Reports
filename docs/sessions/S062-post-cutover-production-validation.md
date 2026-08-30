# S062 — POST-CUTOVER PRODUCTION VALIDATION V1 (Session 1/2)

Nhánh: `claude/post-cutover-validation-reports-vjcbc7`
Base SHA: `b1eeadc171a837f96dbb6219c9bb0724bd84b70c` — merge đã tích hợp
`TASK-105E` (Claude implementation `c9de64236097e1bebc456cc48aaae474001a2ae6`
+ Codex independent repair `edd34d33992c02b625ee31e54a2276886cc13fdc`).
Lineage đã xác nhận: cả hai SHA là ancestor của `HEAD`, và `HEAD == DEFAULT_TIP`
của nhánh mặc định `claude/extract-upload-repo-gq2ws4` tại thời điểm mở phiên.
Không `TARGET_AMBIGUITY`.

## VERDICT

```text
VALIDATOR_IMPLEMENTATION_PASS      = YES
PRODUCTION_POST_CUTOVER_ACCEPTED   = NO
Trạng thái vận hành                = WAITING_REAL_POST_CUTOVER_DATA
```

Không có đơn bán thật nào `sale_date >= 2026-09-01` trong repo. Hôm nay là
`2026-08-30`; mốc Product Identity còn chưa tới. Đây là trạng thái vận hành
mong đợi theo §19 chỉ thị mở phiên, KHÔNG phải một thất bại quy trình — và
KHÔNG được nhảy sang `PRODUCTION_POST_CUTOVER_ACCEPTED` bằng fixture.

## Mục tiêu

Dựng một quy trình kiểm định production hậu-cutover chạy được ngay khi có đơn
thật, chứng minh nó hoạt động trên chính seam production
`app.composition.run_import_production()`, và KHÔNG bịa ra một cohort thật khi
chưa có.

## Kiến trúc validator

Một công cụ đo lường, đặt cạnh `tools/analysis/batch_50_real_orders.py`, KHÔNG
phải một pipeline thứ hai:

```text
tools/analysis/validate_post_cutover.py
  1. select_post_cutover_cohort()   đọc file thô, phân loại đơn theo mốc,
                                     đông lạnh N OrderID duy nhất đầu tiên
  2. freeze_sources()                load_price_resolution_sources() —
                                     ĐÚNG loader production, đọc MỘT lần,
                                     ghi lại đường dẫn + sha256 từng nguồn
  3. PostCutoverPriceComposition()   chính lớp composition của TASK-105E
  4. run_import_production()         seam production THẬT, không stub/mock
  5. build_queue_coverage()          Review Queue canonical TASK-110
  6. detect_silent_errors()          đối chiếu con số với bằng chứng của nó
  7. build_manual_sample()           bảng cho người kiểm điền
  8. write_artifacts()               CSV/JSON/Markdown
```

0 dòng business logic mới. Không giá nào được tính, không identity nào được
resolve, không công thức KPI nào được dựng lại — mọi con số đến từ pipeline
thật, công cụ chỉ ĐỌC và ĐỐI CHIẾU.

### Production entry point tái sử dụng

`app.composition.run_import_production(raw_path, config_dir, price_composition)`
— đúng hàm mà `TASK-105E`/S061 đã nối, và đúng hàm mà
`batch_50_real_orders.py` dùng. `price_composition` được truyền vào để công cụ
giữ tham chiếu tới CHÍNH instance đã chạy và đọc `records`/`evidence` của nó
(đường đã có sẵn từ S061, không phải một API mới).

### Quy tắc chọn cohort

- Đọc `read_raw_rows()` MỘT lần, phân loại từng `OrderID` theo ngày của mọi
  dòng thuộc đơn đó:
  - `POST_CUTOVER` — mọi dòng có ngày đều `>= CUTOVER_DATE` (2026-09-01).
  - `PRE_CUTOVER` — mọi dòng có ngày đều `< CUTOVER_DATE`.
  - `MIXED_CUTOVER` — đơn có dòng ở CẢ HAI phía mốc.
  - `UNDATED` — đơn không có dòng nào có ngày.
- Cohort = N `OrderID` DUY NHẤT ĐẦU TIÊN theo **thứ tự xuất hiện lần đầu**
  trong số các đơn `POST_CUTOVER`. N mặc định 50.
- `MIXED_CUTOVER`/`UNDATED` bị loại khỏi cohort nhưng **đếm riêng và in ra** —
  một đơn hai bên mốc là chính thứ `OrderInconsistency` của `TASK-110` phát
  hiện, và nuốt nó lặng lẽ theo hướng nào cũng là một quyết định giấu đi.
- Phép đếm khép kín, có test:
  `cohort + pre + mixed + undated == total_orders_in_file`.
- Không sort lại, không lọc trước theo khả năng resolve, không bỏ đơn Pending.
- `< 50` đơn → cờ `SAMPLE_NOT_YET_50 = true` in cạnh mọi tỉ lệ. Không tự chờ
  tới 200.

Cohort ghi lại: đường dẫn nguồn, `sha256` nội dung file, `first_order_id`,
`last_order_id`, số đơn duy nhất, số dòng thô, khoảng ngày bán, `frozen_at`,
`reports_commit` (đọc thẳng `.git/`, không gọi tiến trình con), `cutover_date`,
và bốn con số loại trừ ở trên.

### Cơ chế đông lạnh nguồn

`load_price_resolution_sources()` của `TASK-105E` đã bảo đảm "đọc đúng một
lần"; phiên này thêm lớp ghi **đường dẫn + `sha256` + trạng thái** của từng
file, thứ mà bản thân snapshot không mang:

```text
file tồn tại          → PRESENT             + sha256
file không tồn tại    → SOURCE_NOT_CAPTURED + "ABSENT"
file hỏng             → LOADER RAISE        → KHÔNG report nào được sinh
capture_status FAILED → LỖI CỨNG (INV-12)   → không bao giờ thành Pending
```

Mọi `PriceResolutionRecord` của một lần chạy mang cùng một
`PriceEvidenceSnapshot`; artifact ghi `capture_id`/`version_id`/
`content_hash`/`identity_store_revision`/múi giờ + provenance của nó. Không
đơn nào đọc lại nguồn giữa chừng.

### Cơ chế capture Tracking

**Tái sử dụng, không chép lại**: `tools/tracking/capture_purchase_price_history.py`
(`TASK-105E`) vẫn là công cụ capture duy nhất. Validator KHÔNG chạm mạng,
KHÔNG đọc RTDB, KHÔNG nhận token — nó chỉ nhận một đường dẫn file capture.
Không có capture thì trạng thái là `SOURCE_NOT_CAPTURED` và mọi dòng
post-cutover Pending kèm lý do riêng, KHÔNG phải một lịch sử rỗng. Credential
vẫn chỉ đi qua biến môi trường `TRACKING_RTDB_TOKEN` của công cụ capture; không
có secret nào trong repo, trong prompt, hay trong artifact.

### Nguồn identity / Public Purchase

Cả hai đi qua đúng loader production đã review:
`load_tracking_catalog_capture()`, `PublicPurchaseSourceLoader.load()`,
`JsonlProductIdentityStore`. Định tuyến namespace do chính
`PostCutoverPriceComposition` quyết định; validator không resolve identity.

### Múi giờ

KHÔNG có cờ `--timezone`. Múi giờ nghiệp vụ là một authority nạp từ
`config/price_resolution.yaml` (`load_business_timezone`); thêm một cờ CLI ghi
đè nó chỉ là chuyển chỗ giấu một hằng số — đúng thứ mà
`app/modules/pricing/resolution/sources.py` đã từ chối làm. Giá trị thật hiện
hành: `Asia/Ho_Chi_Minh (UTC+07:00)`, provenance `config/price_resolution.yaml`.

## Metrics

Mỗi lần chạy xuất tối thiểu:

```text
INPUT_ORDERS  INPUT_LINES  AUTO_ORDERS  REVIEW_QUEUE_ORDERS  ERROR_ORDERS
PENDING_NOT_QUEUED  SILENTLY_DROPPED  SILENTLY_DROPPED_LINES
ORDER_ACCOUNTING_RATE  AUTOMATION_RATE
LINES_CHECKED_FOR_SILENT_ERRORS  SILENT_ERROR_FINDINGS
SILENT_ERROR_FINDINGS_OUTSIDE_COHORT  SILENT_ERROR_RATE
SAMPLE_NOT_YET_50  MANUAL_SAMPLE_SIZE
```

```text
ORDER_ACCOUNTING_RATE = (AUTO + REVIEW_QUEUE + ERROR) / INPUT_ORDERS
AUTOMATION_RATE       = AUTO / INPUT_ORDERS
SILENT_ERROR_RATE     = SILENT_ERROR / MANUALLY_VALIDATED   (chỉ khi có người chấm)
```

Bốn quyết định đo lường đáng ghi:

1. **`INPUT_ORDERS` đếm `OrderID` DUY NHẤT**, không đếm dòng. Số dòng đo song
   song (`INPUT_LINES`, `SILENTLY_DROPPED_LINES`), không thay thế.
2. **`PENDING_NOT_QUEUED` được chấm THEO CHIỀU, không theo đơn.** Một đơn có
   thể đã vào Review Queue vì `EmployeeMapping` mà giá Pending của nó vẫn
   không ai biết. Bảng `UNRESOLVED_DIMENSIONS` khai báo chiều nào phải được
   category `TASK-110` nào phủ; chiều nào chưa có detector là `None` và
   **không bao giờ được coi là đã phủ**. `PENDING_NOT_QUEUED` được ưu tiên
   hơn `REVIEW_QUEUE` khi cả hai cùng đúng — khoảng trống là thứ phải nổi lên.
3. **Tỉ lệ trên tập rỗng là `None`, không phải `0%`.** In `0%` cho một cohort
   rỗng là bịa một kết luận.
4. **`SILENT_ERROR_FINDINGS = 0` luôn đi kèm
   `LINES_CHECKED_FOR_SILENT_ERRORS`** — nếu không, số 0 ấy đọc giống hệt
   "chưa kiểm dòng nào".

## Review Queue accounting

Hàng chờ canonical DUY NHẤT là `TASK-110`; không tạo queue mới. Phủ được chấm
ở mức **dòng**: một dòng Pending giá phải nằm trong `provenance.source_rows`
của một mục `Missing.PurchasePrice` (item cấp lô, `DEC-128` §1) hoặc thuộc một
item cấp đơn gọi đúng tên đơn ấy. Mỗi chiều chưa resolve mà không có mục nào
phủ sinh một finding `UNRESOLVED_NOT_IN_REVIEW_QUEUE` kèm số dòng cụ thể — đủ
để biết dòng nào, không chỉ đơn nào. Không đòi hỏi D-04 enrichment.

## Cơ chế phát hiện silent error

Hai lớp, không gộp:

**A. Mâu thuẫn cấu trúc (máy chấm) — 26 code.** Mỗi finding là hai phát biểu
của chính hệ thống không đứng cùng nhau được. Chạy trên **mọi dòng của file**, không chỉ
cohort — hai loại rò thẩm quyền qua mốc chỉ quan sát được ở phần ngoài cohort:

| Code | Mâu thuẫn |
|---|---|
| `SILENTLY_DROPPED_ORDER` / `SILENTLY_DROPPED_LINE` | đơn/dòng có trong file, không có trong kết quả |
| `UNRESOLVED_NOT_IN_REVIEW_QUEUE` | chưa resolve mà không mục Review Queue nào phủ |
| `PENDING_LINE_CARRIES_PRICE` | `price_source='Pending'` mà vẫn mang số (`INV-25`) |
| `PRICED_LABEL_WITHOUT_PRICE` | nhãn nguồn thật mà giá `None` |
| `UNKNOWN_PRICE_SOURCE_LABEL` | nhãn ngoài tập đã review |
| `CROSS_CUTOVER_LEGACY_AUTHORITY_LEAK` | đơn `>= 01/09` dùng thẩm quyền P00 |
| `CROSS_CUTOVER_POST_AUTHORITY_LEAK` | đơn `< 01/09` dùng thẩm quyền `P01–P11` (§14) |
| `ACCOUNTING_PROFIT_MISMATCH` / `_FABRICATED` | tính lại độc lập `(Sell − Purchase) × Qty` |
| `ELIGIBLE_KPI_PROFIT_MISMATCH` / `_FABRICATED` | tính lại độc lập `DEC-143` |
| `RESOLUTION_RECORD_MISSING` / `_AMBIGUOUS` | con số không mở lại được |
| `LINE_PRICE_NOT_FROM_RECORD` | dòng mang số mà bản ghi của CHÍNH NÓ không nói (rò dòng anh em) |
| `LINE_PRICE_SOURCE_NOT_FROM_RECORD` | nhãn nguồn của dòng khác nhãn của bản ghi |
| `RESOLVED_WITHOUT_IDENTITY` | có giá mà không biết của sản phẩm nào |
| `SOURCE_UNAVAILABLE_BUT_PRICED` | nguồn không tồn tại mà vẫn trả giá |
| `TRACKING_PRICE_WITHOUT_RECONSTRUCTION` | nhánh Tracking RESOLVED không có bằng chứng tái dựng |
| `UNIT_CONVERSION_MISMATCH` | `resolved ≠ raw × 1000` |
| `RECONSTRUCTION_PRICE_MISMATCH` | provenance và bản ghi bất đồng |
| `PRICE_AFTER_SALE_USED_FOR_HISTORICAL_STATE` | sự kiện quyết định nằm SAU đầu khoảng bán |
| `TRACKING_PROVENANCE_WRONG_NAMESPACE` | namespace của provenance sai nhánh |
| `PUBLIC_PURCHASE_PRICE_NOT_EFFECTIVE_AT_SALE_DATE` | tra lại độc lập bảng giá: không có khoảng hiệu lực nào phủ ngày bán |
| `PUBLIC_PURCHASE_PRICE_MISMATCH` | tra lại độc lập ra số khác |
| `VENDOR_FALLBACK_REACHED_WHILE_BLOCKED` | `P03`/`P09` chạy trong khi `TASK-105C` chưa được cấp phép |

Cả 26 code đều có một test làm nó đỏ (§Test) — và "đã phủ hết" là thứ dễ mục
nhất trong một tài liệu, nên chính bất biến ấy được kiểm bằng máy
(`test_silent_every_detector_code_has_a_test_that_makes_it_red`), không bằng
trí nhớ.

**B. Kiểm tay (người chấm).** Không máy nào chấm được "giá này có đúng không".
Công cụ sinh `manual_sample.csv` với cột `outcome` để trống. Chừng nào chưa ai
điền, `SILENT_ERROR_RATE = NOT_YET_MEASURED` — **không phải `0%`**. Một
`SILENT_ERROR` duy nhất đưa trạng thái về `BLOCKED_BY_SILENT_ERROR`.

Pending an toàn KHÔNG bao giờ là silent error — nó là `CORRECT_PENDING`.

## Quy trình kiểm tay

```text
1. chạy validator            → manual_sample.csv (cột outcome trống)
2. người kiểm điền outcome   ∈ {CORRECT_AUTO, CORRECT_PENDING,
                                SILENT_ERROR, UNVERIFIABLE}
3. chạy lại với --manual-verdicts <file đã điền>
4. SILENT_ERROR_RATE = SILENT_ERROR / MANUALLY_VALIDATED
```

Mẫu ưu tiên bao phủ, deterministic theo `source_row`, mười nhóm: `AUTO_TRACKING`,
`AUTO_PUBLIC_PURCHASE`, `REVIEW_QUEUE_TRACKING`, `REVIEW_QUEUE_PUBLIC_PURCHASE`,
`REVIEW_QUEUE_NO_IDENTITY`, `MULTI_LINE`, `DISCOUNT`, `QUANTITY_GT_1`,
`PRICE_CHANGE_NEAR_SALE`, `IDENTITY_AMBIGUITY`. Cohort nhỏ thì nhóm rỗng được
**in ra kèm số ứng viên**, không bị ép cho đủ.

Hai bảo vệ:
- Giá trị `outcome` ngoài enum đóng → `invalid_entries`, mẫu KHÔNG hoàn tất.
- `manual_sample.csv` đã có verdict **không bao giờ bị ghi đè** bởi một lần
  chạy lại; công cụ ghi `manual_sample.SKIPPED_EXISTING_VERDICTS` thay vì xoá
  công sức kiểm tay.

Mẫu không mang dữ liệu cá nhân: không tên khách, số điện thoại, địa chỉ, IMEI,
tên nhân viên (`governance/product/17_DATA_GOVERNANCE_PRIVACY.md`) — có test
khẳng định header.

## KPI

`DEC-143`/`DEC-144` KHÔNG đổi một byte. Validator không dựng lại engine KPI;
nó tính lại công thức MỘT lần để **đối chiếu** và xuất đủ trường để người kiểm
mở lại: `sell_price`, `accounting_purchase_price`, `quantity`, `discount`,
`accounting_profit`, `kpi_purchase_price`, `kpi_purchase_price_provenance`,
`eligible_kpi_profit`, `price_source`, `composition_rule`, `identity`,
`tracking_capture_id`, `tracking_decisive_source`, `tracking_decisive_event_id`,
`tracking_decisive_timestamp`, `tracking_raw_thousand_vnd`,
`tracking_unit_conversion`.

## Artifact

`--output <dir>` sinh 8 file, không Dashboard, không frontend:

```text
summary.md                  bản đọc cho người: verdict, metrics, cohort, nguồn
metrics.json                metrics + provenance nguồn + lệnh đã chạy
cohort.json                 định nghĩa cohort đông lạnh
orders.csv                  một dòng / đơn: outcome, số dòng, chiều chưa resolve
lines.csv                   một dòng / dòng bán: đủ trường giá + KPI + provenance
review_queue.csv            các mục TASK-110, kèm dòng thuộc cohort
silent_error_findings.json  mọi mâu thuẫn cấu trúc
manual_sample.csv           bảng cho người kiểm điền
```

## Owner experience — một lệnh

```text
python3 tools/analysis/validate_post_cutover.py \
    --sales <so_chi_tiet_ban_hang.xlsx> \
    --output <thư_mục_kết_quả>
```

Nguồn thật nằm ngoài đường dẫn canonical thì thêm `--tracking-capture`,
`--tracking-catalog`, `--public-purchase`, `--identity-store`. Operator KHÔNG
phải sửa code để chạy trên dữ liệu mới.

## Kết quả đo — dữ liệu THẬT hiện có

Cả hai kỳ nghiệp vụ thật trong repo đều PRE-cutover, nên cohort hậu-cutover
rỗng. Nhưng bộ phát hiện silent error vẫn chạy trên TOÀN BỘ dòng của mỗi file —
và đó chính là phép kiểm §14 (Batch 50 không được tự động hoá bằng dữ liệu
Tracking 08/2026):

```text
tests/fixtures/golden/period_2026_01.xlsx
  STATUS                              = WAITING_REAL_POST_CUTOVER_DATA
  total_orders_in_file                = 254
  excluded_pre_cutover_orders         = 254
  excluded_mixed_cutover_orders       = 0
  excluded_undated_orders             = 0
  INPUT_ORDERS                        = 0
  ORDER_ACCOUNTING_RATE               = N/A   (tập rỗng, không phải 0%)
  LINES_CHECKED_FOR_SILENT_ERRORS     = 351
  SILENT_ERROR_FINDINGS               = 0
  SILENT_ERROR_FINDINGS_OUTSIDE_COHORT= 0
  source_sha256 = 73b519aa930c59fda8b06f0763951b0d1859b53a53f8bde8069b20af76e7adcb

tests/fixtures/golden/period_2026_06.xlsx
  STATUS                              = WAITING_REAL_POST_CUTOVER_DATA
  total_orders_in_file                = 146
  excluded_pre_cutover_orders         = 146
  LINES_CHECKED_FOR_SILENT_ERRORS     = 180
  SILENT_ERROR_FINDINGS               = 0
```

531 dòng thật đã đi qua toàn bộ bộ phát hiện: **không rò thẩm quyền qua mốc
cutover theo cả hai chiều, không sai số học `AccountingProfit`/
`EligibleKpiProfit`, không dòng nào mang giá khi input còn Pending, không nhãn
nguồn lạ.** Đây là kết quả trên dữ liệu THẬT, và nó KHÔNG phải một tuyên bố về
nhánh post-cutover — nhánh ấy chưa có đơn nào để đo.

Nguồn giá post-cutover trên đĩa hôm nay: cả bốn `SOURCE_NOT_CAPTURED`
(`data/tracking_price_history/capture.json`, `data/tracking_catalog/capture.json`,
`data/public_purchase/source_version.yaml`, `data/product_identity/mappings.jsonl`).

## Kết quả đo — fixture hậu-cutover

Fixture (KHÔNG phải dữ liệu thật, KHÔNG được đọc thành bằng chứng production)
chạy qua `run_import_production()` thật với ba nguồn giá là file fixture:

```text
INPUT_ORDERS            = 4      INPUT_LINES = 5
AUTO_ORDERS             = 2      (TRACKING A1, PUBLIC_PURCHASE C1)
REVIEW_QUEUE_ORDERS     = 2      (giá bị xoá; identity không resolve được)
ERROR_ORDERS            = 0      PENDING_NOT_QUEUED = 0
SILENTLY_DROPPED        = 0      SILENTLY_DROPPED_LINES = 0
ORDER_ACCOUNTING_RATE   = 100%   AUTOMATION_RATE = 50%
SILENT_ERROR_FINDINGS   = 0      SILENT_ERROR_RATE = NOT_YET_MEASURED
SAMPLE_NOT_YET_50       = true
```

Đơn hai dòng `BH9004` giữ đủ 2/2 dòng: dòng resolve được mang `4.200.000`,
dòng Pending mang `None` — giá không chảy sang dòng anh em.

## Test

Focused: `tests/test_post_cutover_validation.py` — **58 test**, phủ đủ 20 mục
§20 của chỉ thị:

```text
 1 cohort deterministic            11 AUTOMATION_RATE (+ tỉ lệ trên tập rỗng)
 2 đếm OrderID duy nhất            12 đơn nhiều dòng giữ nguyên
 3 không lọc bỏ đơn Pending        13 mẫu kiểm tay (7 test: bao phủ, xác định,
 4 nguồn đông lạnh 1 lần/run          không PII, chưa chấm ≠ 0%, đã chấm,
 5 phân loại AUTO                     enum đóng, không ghi đè verdict)
 6 phân loại REVIEW_QUEUE          14 provenance giá đi vào artifact
 7 phân loại ERROR                 15 không chạm mạng (app/** + validator)
 8 PENDING_NOT_QUEUED              16 thiếu capture → fail-safe
 9 SILENTLY_DROPPED đơn + dòng     17 capture hỏng / FAILED → lỗi cứng
10 ORDER_ACCOUNTING_RATE           18 loại đơn pre-01/09  19 nhận đơn 01/09
                                   20 hai lần chạy ra cùng artifact
```

Cộng **27 test riêng cho §11**: 26 test — mỗi code silent error một test làm nó
đỏ; một **kiểm soát âm**
(`test_silent_a_clean_production_run_yields_no_findings`) khẳng định một lần
chạy sạch cho 0 finding; và một **meta-test** quét chính mã nguồn công cụ,
liệt kê mọi code nó có thể phát ra, rồi bắt buộc mỗi code phải xuất hiện trong
một assertion của file test.

Hai test (`test_9`, `test_9b`) dùng `monkeypatch` thay pipeline bằng một bản
đánh rơi đơn/dòng. Nói rõ: đó là test của **công cụ đo**, không phải của
production — production hiện tại không đánh rơi (Batch 50 và Golden #4 đã đo).
Một detector chưa từng thấy trường hợp nó đi tìm là một detector chưa được kiểm.

`test_8` KHÔNG dùng test double: nó tắt detector `missing_purchase_price` trong
một bản sao `config/validation.yaml` hợp lệ, nên production THẬT ngừng sinh
`Missing.PurchasePrice`, và công cụ phải gọi tên khoảng trống ấy
(`ORDER_ACCOUNTING_RATE` tụt xuống 50%, đúng như định nghĩa).

## Regression

```text
Golden Baseline        : 58 passed, 2 skipped        — KHÔNG ĐỔI
Golden #1 / #3 / #4    : 16 passed                   — KHÔNG ĐỔI
TASK-110 / TASK-105E / Tracking Reader / TASK-108B (KPI engine):
                         146 passed                  — KHÔNG ĐỔI
Batch 50 (01/2026)     : INPUT 50, AUTO 1, REVIEW_QUEUE 49,
                         PENDING_NOT_QUEUED 0, ERROR 0, SILENTLY_DROPPED 0,
                         AUTOMATION_RATE 2,0%, ORDER_ACCOUNTING_RATE 100,0%
                         — GIỐNG HỆT baseline S059/S061
FULL pytest            : 1213 passed, 11 skipped, 0 failed
                         (base b1eeadc: 1155 passed, 11 skipped — +58, 0 hồi quy)
Validators             : validate_structure / validate_project_state /
                         validate_evidence / validate_task_completion = PASS;
                         validate_reference_integrity = FAIL đúng 3 issue tiền
                         tồn TASK-REM-T06 (REG-01), không đổi
```

## Files changed

```text
tools/analysis/validate_post_cutover.py   MỚI  1.937 dòng (công cụ đo lường)
tests/test_post_cutover_validation.py     MỚI  1.180 dòng (58 test)
docs/sessions/S062-...md                  MỚI  (file này)
PROJECT/PROJECT_PROGRESS.md               +ghi trạng thái

app/**      0 dòng thay đổi
config/**   0 dòng thay đổi
data/**     0 dòng thay đổi
```

Business-logic LOC production: **0**. Toàn bộ 1.937 dòng mới là công cụ đo
lường dưới `tools/`, cùng hạng với `tools/analysis/batch_50_real_orders.py` —
không nằm trong đường chạy của `run_import()`.

Repo `Tracking` KHÔNG bị sửa.

## Blockers

Complete Blocking Set: **RỖNG**. Không blocker hợp lệ nào cần sửa production.
Ba quan sát đã kiểm và loại trừ:

1. **`OWNER_DECISION_REQUIRED` của S061 vẫn mở, vẫn không chặn.** Không artifact
   frozen nào đặt Reports History Reader V1 vào một ô của bảng `P00–P11`. Phiên
   này KHÔNG chạm vào lựa chọn ấy và không làm nó quan sát được sớm hơn.
2. **`P01`/`P03` vẫn bị chặn có chủ đích** (`TASK-105C` NOT AUTHORIZED).
   Validator có detector `VENDOR_FALLBACK_REACHED_WHILE_BLOCKED` cho ngày nhánh
   ấy vô tình mở ra.
3. **Chiều `ConversionScheme.Unresolved` chưa có detector Review Queue nào.**
   Bảng `UNRESOLVED_DIMENSIONS` khai báo nó là `None` và tính nó vào
   `PENDING_NOT_QUEUED` nếu xảy ra — trên dữ liệu thật hiện có nó không xảy ra
   (Batch 50: `PENDING_NOT_QUEUED = 0`). KHÔNG mở lại `TASK-108A-1`; ghi lại để
   không ai đọc "chưa có detector" thành "đã phủ".

## Deferred scope

Không làm, đúng §18: Batch 200, Dashboard, frontend, pricing engine mới,
Product Identity redesign, Tracking redesign, Review Queue mới, công thức
nghiệp vụ mới, price authority mới, historical backfill, sửa repo Tracking,
refactor không liên quan. `MANUAL_WORK_REDUCTION` vẫn `NOT_YET_MEASURABLE` —
không có baseline thời gian xử lý tay thật nào trong repo để so; không bịa số.

## Acceptance state

```text
A. VALIDATOR_IMPLEMENTATION_PASS    = YES
   - validator nối vào production pipeline thật (run_import_production)
   - cohort deterministic, có test
   - evidence tái lập được (sha256 nguồn + evidence snapshot + commit)
   - metrics đúng công thức, tỉ lệ trên tập rỗng là None
   - queue accounting theo TASK-110, chấm theo chiều
   - quy trình kiểm tay có, kèm bảo vệ không ghi đè verdict
   - 58 focused test + regression đầy đủ PASS

B. PRODUCTION_POST_CUTOVER_ACCEPTED = NO
   - chưa có cohort thật hậu 01/09/2026
   - chưa có capture production nào
   - mẫu kiểm tay chưa chạy được (cohort rỗng)
   → WAITING_REAL_POST_CUTOVER_DATA
```

Trạng thái cao nhất công cụ được phép in ra là
`ELIGIBLE_FOR_PRODUCTION_ACCEPTANCE_REVIEW`: nó không phân biệt được một sổ bán
hàng THẬT với một fixture cùng hình dạng, nên nó không được tự tuyên Production
Acceptance. Quyết định ấy là quyết định governance, ghi ở
`PROJECT/PROJECT_PROGRESS.md`.
