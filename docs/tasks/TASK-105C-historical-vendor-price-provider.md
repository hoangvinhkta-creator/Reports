# TASK-105C — HistoricalVendorPriceProvider

## Metadata

Status:
BLOCKED

Current Status Reason:
`DEC-154` reconciled business architecture sau Scope Lock `DEC-152`. Chưa
implementation; current Scope/Completion Gate cần refreeze bởi authority
riêng trước khi có thể READY.

Phase:
PHASE-01 — Engine tính toán

Task Mode:
MAJOR

Primary Agent Tier:
B

Escalation Tier:
C

Difficulty:
3/5

Risk:
3/5 (local — parsing/derivation logic, một script fetch mạng cô lập ngoài
`app/modules/`)

Blast Radius:
5/5 (V4.1 §4 — chấm theo data path, không theo tên module:
`Price → KpiPurchasePrice → EligibleKpiProfit → CR → KPI/lương`)

Effective Risk:
HIGH (Blast Radius quyết định, không phải Risk cục bộ — V4.1 §4.1: Golden
KHÔNG tự động hạ bậc)

Project Profile:
PRODUCT

Review Budget lineage:
`TASK-105B` (dùng chung — không mở lineage mới). Ngân sách hiện tại:
2 allowed / 1 used / 1 remaining (`PROJECT/REVIEW_BUDGET_LEDGER.md`
§"Root Task: TASK-105B"). Mở task này KHÔNG tiêu ngân sách; ngân sách chỉ
tiêu khi một vòng Independent Review sau implementation FAIL và cần repair.

Authority chain:
`DEC-145` (contract 4 cột, chuẩn hoá, validation — KHÔNG đổi) → `DEC-146`
(RTDB discovery) → `DEC-147` (audit repo, HYBRID + SOURCE MISMATCH) →
`DEC-148` (`inv.cong` audit, NO GUARANTEED DELAY WINDOW) → `DEC-149`
(`_c.min` path audit, `CONFLICT DETECTED`) → `DEC-150` (popup audit fact) →
`DEC-151` (Owner Decision: thu hẹp phạm vi về `phist`) → **`DEC-152`**
(Owner Decision: đóng Q1/Q2, Scope Lock, Completion Gate) → **`DEC-154`**
(Owner Decision: two-namespace identity + provider-branch reconciliation).

## Current Normative Reconciliation — DEC-154

Phần này là current authority và supersede các câu bên dưới nếu chúng còn
nói `TASK-105C = READY`, identity bắt buộc là Tracking cho mọi valid product,
`FilePriceProvider` là dependency cứng/composition seam, hoặc provider absence
đi thẳng final Pending. Historical decision/evidence vẫn giữ nguyên.

### Current input/output contract

```text
INPUT:
  resolved_product_identity.namespace = TRACKING
  resolved_product_identity.source_product_code = <MÃ> Tracking
  sale_date

OUTPUT:
  HistoricalVendorMin(value + vendor/capture provenance)
  HOẶC absence (không có valid candidate)
```

`PUBLIC_PURCHASE` identity bypass task này. `absence` không tự đổi thành final
Pending ở đây; price-resolution layer theo `DEC-154` P03 sẽ thử Public Purchase
fallback qua `CrossSystemProductMapping`, rồi mới Pending nếu fallback vắng.

### Semantics được bảo toàn

`DEC-151`/`DEC-152` vẫn nguyên authority:

```text
Price(NCC,D) = record gần nhất có ngày <= D
HistoricalVendorMin = MIN mọi candidate hợp lệ tại D
sentinel 0 = unavailable / HẾT HÀNG, bị loại
current NCC/config/outlier rule không áp ngược
phist snapshot/capture phải replay được
```

### Dependency/current role được supersede

- Không còn depend/compose `FilePriceProvider`; `TASK-105B` thuộc nhánh
  Public Purchase song song.
- Không yêu cầu toàn bộ historical catalog được map thủ công trước khi
  implementation/operation. Alias đã confirm được reuse; identity chưa resolve
  có thể Pending mà không chặn identities khác.
- `TASK-105D` cung cấp canonical identity contract, nhưng chưa READY/frozen.
- Tracking vẫn read-only; không sửa repo/catalog.

### COMPLETION GATE CHANGE PROPOSAL — OPEN, CHƯA FROZEN

Original gate `CHECK-105C-01..20` tại `DEC-152` vẫn là historical frozen
artifact. Trước implementation phải có phiên authority riêng refreeze gate,
giữ mọi check HistoricalVendorMin còn áp dụng và thay các assumption
composition/final-Pending bằng tối thiểu:

| ID dự thảo | Current required behavior | Status |
|---|---|---|
| CHECK-105C-R01 | Chỉ nhận resolved TRACKING identity + `sale_date` | NOT_TESTED |
| CHECK-105C-R02 | PUBLIC_PURCHASE identity bypass, không đọc `phist` | NOT_TESTED |
| CHECK-105C-R03 | Valid vendor candidates → HistoricalVendorMin + provenance | NOT_TESTED |
| CHECK-105C-R04 | sentinel 0 bị loại | NOT_TESTED |
| CHECK-105C-R05 | No candidate → explicit absence cho fallback, không giá 0 | NOT_TESTED |
| CHECK-105C-R06 | Không depend/import/compose `FilePriceProvider` | NOT_TESTED |
| CHECK-105C-R07 | Không yêu cầu pre-map toàn catalog; known aliases xử lý độc lập | NOT_TESTED |
| CHECK-105C-R08 | `HB-105B-06` boundary được resolve trước tools/tests | NOT_TESTED |

### Authorization state

```text
SEMANTIC_DEFINITION = RECONCILED
SCOPE_LOCK          = REOPENED_BY_DEC-154
COMPLETION_GATE     = CHANGE_PROPOSAL_OPEN, NOT FROZEN
IMPLEMENTATION      = BLOCKED / NOT AUTHORIZED
```

Blockers hiện hành:

1. `TASK-105D` interface/data contracts chưa READY/frozen.
2. Current Scope/Completion Gate của chính task này chưa refreeze.
3. `HB-105B-06` re-trigger phải được xử lý trước khi thêm
   `TASK-105C` tools/tests; `HB-105B-03/05/10` chuyển sang chặn real Public
   Purchase dataset/FilePriceProvider use, không còn là dependency của nhánh
   `phist` sau khi composition bị supersede.
4. Tracking capture credential/schema-drift checks từ spec cũ vẫn áp dụng.

Phiên reconciliation này không freeze gate, không implement và không cấp
READY.

## Mục Tiêu (Objective)

Implementation thứ ba của `PriceProvider` Protocol
(`app/modules/pricing/provider.py`, không đổi từ `TASK-105`/`DEC-103`):
`HistoricalVendorPriceProvider` — tra `AccountingPurchasePrice` cho một
đơn bán tại đúng ngày nghiệp vụ của nó, dựa **duy nhất** trên lịch sử giá
nhà cung cấp lưu trong Tracking (`phist/<mã>/<NCC>/<YYYY-MM-DD>`), theo
đúng nghiệp vụ Owner đã chốt ở `DEC-151`/`DEC-152`:

```
Price(NCC, D)                = record gần nhất có ngày <= D
HistoricalVendorPrice(mã, D) = MIN qua mọi NCC có Price(NCC,D) xác định
                                và > 0 (sentinel 0 = hết hàng, KHÔNG phải
                                candidate)
KpiPurchasePrice(mã, D)      = HistoricalVendorPrice(mã, D) nếu xác định
                                được, ngược lại Pending
```

`_c.min` (Min hiển thị trên board Tracking) và `inv.cong` (giá nhập công
khai) **không được đọc ở bất kỳ đâu** trong provider này — cả hai đã bị
loại khỏi vai trò nguồn ở `DEC-151` §3/§6.

## Business Semantics (đầy đủ — mục 2 của đề bài)

**Owner Decision Q1 — CLOSED (`DEC-152`, xem block "OWNER DECISION" bên
dưới).** Trạng thái NCC HIỆN TẠI (`NCC_RETIRED`, `NCC_MIN_LOAI`, hay bất kỳ
lý do gì khiến NCC không còn xuất hiện trên bảng giá hôm nay) **không được
áp ngược** để loại một historical price hợp lệ tại ngày D. Nếu
`phist/<mã>/<NCC>` có record hợp lệ tại D, giá đó **vẫn** là candidate của
`HistoricalVendorPrice(D)`, bất kể NCC đó hôm nay ra sao.

**Owner Decision Q2 — CLOSED (`DEC-152`).** `NGUONG_BAT_THUONG` (ngưỡng lọc
giá bất thường, thêm pe-6, 24/08/2026) **không được áp ngược** cho dữ liệu
trước khi rule đó có historical authority. Phase 1 dùng đúng:

```
candidates(D) = { Price(NCC, D) : NCC có Price(NCC,D) xác định, > 0 }
HistoricalVendorPrice(D) = MIN(candidates(D)) nếu candidates(D) khác rỗng,
                            ngược lại None
```

Không lọc gì thêm ngoài loại bỏ sentinel `0`. Đây là ranh giới đóng của
Phase 1 — không phải một giả định tạm chờ trả lời (khác với trạng thái ở
`DEC-151`), mà là **quyết định cuối** cho Phase 1 hiện hành.

## Historical Authority (mục 3, 12)

```
Canonical source : phist/<MÃ>/<NCC>/<YYYY-MM-DD>   (Tracking RTDB)
Khoá gốc         : <MÃ> = board product code trong Tracking (KHÔNG phải
                   tên hàng tự do — xác nhận lại DEC-147 §56: phist đã
                   khoá theo mã board, không theo tên)
Đơn vị lưu        : NGHÌN đồng (ADR-103 §2 — chuyển đổi bắt buộc PHẢI xảy ra
                   ở BIÊN xuất/nhập, KHÔNG BAO GIỜ trong app/modules/pricing/)
```

`_c.min`, `inv.cong` **không phải** historical authority — loại hẳn khỏi
scope (`DEC-151` §3/§6, xác nhận lại ở đây).

## Product Identity Contract (mục 4, 14) — KHÔNG fuzzy matching

```
Reports sale line (product_raw, text tự do trên chứng từ)
      │
      │  ??? — KHÔNG CÓ mapping production đáng tin cậy tồn tại hôm nay
      ▼
Canonical product identity (Tracking <MÃ>)
      │
      ▼
phist/<MÃ>/...
```

**Đây là một dependency chưa đóng, không phải việc TASK-105C tự phát
minh.** Đã audit kỹ ở `DEC-147` §56: Tracking **có** mã ổn định
(`normCode()` + `aliasOf()`), nhưng khoá đó là mã sản phẩm CỦA TRACKING,
không phải câu tên hàng của Reports. Không có bảng dịch `product_raw` (văn
bản chứng từ bán hàng của Reports) → `<MÃ>` (mã board của Tracking) tồn tại
sẵn ở bất kỳ đâu — `inv.map` bên Tracking dịch một loại tên hàng KHÁC (tên
trên file tồn kho MISA), không phải tên trên chứng từ bán hàng của Reports.

**Quyết định thiết kế cho Phase 1 (không đoán mã):**

```
HistoricalVendorPriceProvider.lookup(product_code, sale_date)

product_code Ở ĐÂY PHẢI LÀ MỘT <MÃ> TRACKING ĐÃ ĐƯỢC GIẢI QUYẾT.
Provider KHÔNG tự dịch product_raw → <MÃ>.
Nếu caller không có <MÃ> đã giải quyết chắc chắn (product_code = None,
hoặc không khớp bất kỳ mã nào trong snapshot) → lookup() trả None → Pending.
```

Vì Reports hiện tại **không có** một product_mapper sản xuất được `<MÃ>`
Tracking từ `product_raw` (đúng khoảng trống mà `TASK-402`/Phase 4 dự kiến
lấp cho Price Master thật, theo docstring gốc của `provider.py` từ
`TASK-105`), **mọi lookup ở Phase 1 sẽ trả Pending cho tới khi có một trong
hai:**

1. Một task mapping riêng (chưa mở, chưa có ID) xây bảng dịch
   `product_raw` ↔ `<MÃ>` — do con người duyệt, đúng tiền lệ `inv.map` bên
   Tracking (`DEC-147` §56: *"đã thử giải bằng máy, đã bỏ, thay bằng bảng
   người duyệt"* — tiền lệ production ủng hộ KHÔNG lặp lại `extractCode()`
   ở Reports).
2. Chủ dự án cung cấp trực tiếp một bảng mapping đã duyệt.

**KHÔNG được** phát minh fuzzy/nearest/substring matching để thu hẹp
khoảng trống này — `OD-105B-01` §B đã cấm, và `DEC-147` §56 đã chỉ ra tiền
lệ thất bại thật (`extractCode()`) trên đúng loại dữ liệu này.

## Date Lookup Semantics (mục 5)

```
Price(NCC, D) = value tại record có date = max(record_date <= D)
```

Last-observation-carried-forward, đúng khoảng đóng của `DEC-145` §1 và xác
nhận lại từ `DEC-150` §86 (chart trong popup "Lịch sử giá" đã minh hoạ đúng
ngữ nghĩa này — bảng số KHÔNG carry-forward, chỉ chart mới đúng; provider
implement theo NGỮ NGHĨA (chart), không theo cách hiển thị bảng).

Không có record nào với `date <= D` → `Price(NCC, D)` không xác định (loại
khỏi `candidates(D)`, không phải `0`).

## Sentinel Semantics (mục 6)

```
phist value == 0  →  NCC đó "hết hàng" tại ngày record đó — KHÔNG phải giá.
```

Loại tuyệt đối khỏi `candidates(D)`. Không bao giờ trở thành
`purchase_price = 0` ở bất kỳ tầng nào (`DEC-145` §5, tái xác nhận).

## Multi-NCC MIN Semantics (mục 7)

```
candidates(D) = { Price(NCC,D) : mọi NCC xuất hiện trong phist của mã đó,
                   Price(NCC,D) xác định, > 0 }
HistoricalVendorPrice(D) = min(candidates(D))
```

Không giới hạn tập NCC theo `_ANC`/`NCC_RETIRED`/`NCC_MIN_LOAI` hiện tại
(Q1, CLOSED). Ghi lại **tất cả** NCC đạt giá min (có thể hoà) vào
provenance (`contributing_ncc`), không chỉ một tên.

## Missing-Data / Pending Semantics (mục 8)

```
candidates(D) rỗng                          → HistoricalVendorPrice = None
product_code không giải quyết được          → lookup() trả None ngay,
                                               không tính candidates(D)
mã không có trong snapshot phist            → None
```

Mọi trường hợp `None` → `price_source = PRICE_SOURCE_PENDING`
(`price_engine.py`, không đổi từ `TASK-105`) → `KpiPurchasePrice = Pending`
ở `TASK-108B`. Không suy đoán, không lấy giá hiện tại, không
nearest/latest ngoài đúng semantics đã chốt.

## Reproducibility / Snapshot Contract (mục 9)

```
Tracking RTDB (phist)
      │  fetch (READ-ONLY REST, ngoài app/modules/, xem "RTDB Boundary")
      ▼
Raw vendor-price history (JSON, dạng y hệt phist)
      │  compute_historical_vendor_price_series()  — PURE, app/modules/pricing/
      ▼
Danh sách record { product_key, effective_from, effective_to,
                    purchase_price, source, contributing_ncc, captured_at }
      │  ghi FILE MỚI, KHÔNG GHI ĐÈ file cũ
      ▼
config/historical_vendor_prices/<capture_id>.csv   (BẤT BIẾN sau khi ghi)
      │
      ▼
HistoricalVendorPriceProvider(snapshot_path=<capture_id cụ thể>)
```

Mỗi lượt capture tạo **một file mới**, không ghi đè. Một report/pipeline
run cụ thể **ghim vào đúng một `capture_id`**, ghi lại `capture_id` đó
trong provenance đầu ra của chính report. Chạy lại CÙNG report sau này đọc
lại CÙNG file — không phụ thuộc `phist` có bị sửa/xoá sau đó hay không
(`DEC-147` §54 R4 vẫn đúng: `phist` sửa/xoá được; đây là cơ chế miễn nhiễm,
không phải phủ nhận rủi ro đó).

Không xây database mới — một file bất biến mỗi lần capture là đủ, đúng
tinh thần "chọn option ít thay đổi nhất" và đúng định dạng đã có thẩm quyền
từ `DEC-145` §4.

## Provenance Contract (mục 10)

Mỗi record trong snapshot mang:

```
product_key       (= <MÃ> Tracking)
effective_from / effective_to   (khoảng đóng, DEC-145 §1)
purchase_price    (VND nguyên, Decimal — đã chuyển đổi từ nghìn đồng TẠI
                   BƯỚC EXPORT, không phải trong app/modules/pricing/)
source            = "phist" (cố định)
contributing_ncc  = danh sách NCC đạt giá min trong khoảng đó (CSV trong ô,
                    hoặc cột lặp — chi tiết định dạng do implementation
                    quyết, không khoá cứng ở đây)
captured_at       = ISO 8601, thời điểm chạy export (không phải ngày hiệu
                    lực giá)
capture_id        = định danh lượt capture (để report ghim vào)
```

## Error Semantics (mục 11)

```
Missing history (mã có trong snapshot, không có candidate tại D)
    → HistoricalVendorPrice = None → Pending. KHÔNG phải lỗi.

Unresolved product mapping (không có <MÃ>)
    → lookup() trả None ngay → Pending. KHÔNG phải lỗi.

SOURCE_FAILURE (export tool fetch từ Tracking thất bại — mạng, auth, dữ
liệu trả về không đọc được)
    → export tool THẤT BẠI RÕ RÀNG (non-zero exit, log lỗi), KHÔNG ghi
      file mới, KHÔNG chạm vào snapshot cũ. Downstream tiếp tục dùng
      capture_id cũ nhất còn hợp lệ cho tới khi có người sửa và chạy lại.
      SOURCE_FAILURE không bao giờ trở thành "None" âm thầm ở tầng dữ
      liệu — nó dừng pipeline capture, không dừng pipeline tính giá.

File snapshot hỏng/mâu thuẫn (do lỗi trong chính export tool)
    → HistoricalVendorPriceProvider tái dùng đúng validation của
      FilePriceProvider (DEC-145 §5: overlap, >1 record mở, giá âm...) →
      raise lỗi tại thời điểm NẠP file, không phải khi tra từng dòng.
```

`Missing`/`Unresolved mapping` (DETERMINED — hệ thống biết chắc không có
dữ liệu) **khác hẳn** `SOURCE_FAILURE` (UNKNOWN — hệ thống không chạy được
lượt fetch) — không được gộp hai loại lại thành một tín hiệu.

## RTDB Boundary (mục 12)

```
app/modules/pricing/   → THUẦN PYTHON, KHÔNG mạng, KHÔNG SDK Firebase/
                          Google (ADR-101 giữ nguyên)
tools/pricing/          → NƠI DUY NHẤT được phép gọi mạng tới Tracking
                          RTDB, đọc read-only qua REST (<path>.json + auth
                          token), KHÔNG ghi bất cứ gì vào Tracking
```

Credential đọc (Firebase ID token của một tài khoản có ít nhất quyền
`edit` trong `profiles/<uid>/perms` bên Tracking, theo
`firebase-database.rules.json` nhánh `phist`) là **operational
dependency**, không phải việc TASK-105C tự cấp phát — chủ dự án phải tạo
một tài khoản đọc riêng bên Firebase Console (không phải sửa code Tracking)
và cấp secret cho môi trường chạy `tools/pricing/`. Ghi vào OUT_OF_SCOPE.

## Reports/Tracking Repo Boundary (mục 13)

Không phụ thuộc code hai chiều — tái xác nhận `DEC-147` §9/§10:

```
Reports KHÔNG import Tracking.
Tracking KHÔNG import Reports.
Giao tiếp DUY NHẤT: tools/pricing/ đọc REST public API của Firebase RTDB
(không phải mã nguồn Tracking) — cùng cơ chế mà chính Worker `tracking`
dùng nội bộ (src/firebase.js), không phải một cổng mới do TASK-105C mở.
```

Không sửa một file nào của repo B (`Tracking`) trong bất kỳ giai đoạn nào
của `TASK-105C`, kể cả implementation về sau.

## No-Fuzzy-Matching Rule (mục 14)

Đã nêu đủ ở "Product Identity Contract" — nhắc lại tường minh vì đề bài
yêu cầu một mục riêng: **cấm tuyệt đối** fuzzy/nearest/substring/AI matching
ở bất kỳ đâu trong `TASK-105C` — cho cả product identity lẫn NCC name
resolution. Chỉ dùng exact-match sau chuẩn hoá đã có thẩm quyền
(`normCode()`/`aliasOf()` bên Tracking cho khoá `<MÃ>`; `fold()`
NFC+casefold — `app/modules/validation/text.py` — cho bất kỳ so khớp text
nào bên Reports, đúng `DEC-145` §2, không phát minh chuẩn hoá mới).

## No-Current-Price-Backdating Rule (mục 15)

```
inv.cong HIỆN TẠI     → KHÔNG BAO GIỜ đọc trong TASK-105C (loại khỏi scope,
                         DEC-151 §3)
_c.min HIỆN TẠI        → KHÔNG BAO GIỜ đọc (DEC-151 §6)
Giá NCC HIỆN TẠI       → KHÔNG áp cho sale_date quá khứ; chỉ Price(NCC,D)
                         theo đúng semantics lookup ở trên
Trạng thái NCC HIỆN TẠI (retired/MIN_LOAI/ẩn) → KHÔNG áp ngược (Q1, CLOSED)
Config hiện tại (NGUONG_BAT_THUONG, danh sách loại trừ) → KHÔNG áp ngược
                         (Q2, CLOSED)
```

## Historical Scope — DEC-152 (REOPENED_BY_DEC-154)

- `app/modules/pricing/historical_vendor_price.py` (**MỚI**) — hàm thuần
  `compute_historical_vendor_price_series()`: nhận dữ liệu vendor-history
  thô (dạng tương đương `phist`), trả danh sách record theo contract 4
  cột + provenance ở trên. Không mạng, test được bằng fixture JSON tĩnh.
- `app/modules/pricing/historical_vendor_price_provider.py` (**MỚI**) —
  `HistoricalVendorPriceProvider`, implement `PriceProvider` Protocol bằng
  cách **compose** (không duplicate logic của) `FilePriceProvider` đọc file
  snapshot đã sinh — tái dùng nguyên vẹn validation/parsing đã có thẩm
  quyền từ `DEC-145`.
- `tools/pricing/export_historical_vendor_prices.py` (**MỚI**) — script
  fetch read-only từ Tracking RTDB (`phist`), gọi
  `compute_historical_vendor_price_series()`, ghi file snapshot mới, không
  bao giờ ghi đè.
- `tests/test_historical_vendor_price.py`,
  `tests/test_historical_vendor_price_provider.py` (**MỚI**) — test hàm
  thuần bằng fixture JSON tổng hợp (retired NCC, sentinel 0, multi-NCC tie,
  gap, mã không tồn tại) + test provider qua file snapshot tổng hợp.
- `tests/fixtures/historical_vendor_price/` (**MỚI**) — fixture JSON/CSV
  tổng hợp, KHÔNG chứa dữ liệu Tracking thật.
- Cập nhật `docs/tasks/TASK-105C-historical-vendor-price-provider.md`
  (file này, Completion Gate → PASS khi implementation xong).

## Historical Out of Scope — DEC-152 (đọc cùng DEC-154)

- **Product identity mapping** (`product_raw` ↔ `<MÃ>` Tracking) — dependency
  chưa đóng (xem "Product Identity Contract"), KHÔNG implement trong
  `TASK-105C`. Không có bảng mapping ⇒ mọi lookup thực tế trả Pending; đây
  là hành vi ĐÚNG theo thiết kế, không phải một khiếm khuyết cần vá bằng
  đoán mã.
- **Credential/tài khoản đọc RTDB** — operational dependency (chủ dự án
  cấp qua Firebase Console), không phải code.
- Sửa `FilePriceProvider`, `price_engine.py`, `pipeline.py`,
  `provider.py`, `models.py` — tất cả **KHÔNG ĐỔI** (đúng tiền lệ
  `TASK-105`/`DEC-145`).
- `RTDBPriceProvider` đọc trực tiếp `board`/`_c.min` — **loại hẳn**, không
  còn là hướng đi (`DEC-149`/`DEC-151`).
- Xây capture layer cho `inv.cong`/`_c.min`/`MarketMinHistory` — **không
  bắt buộc trong Phase 1** (`DEC-151` §3/§9).
- `TASK-105B-Q3` (dòng phụ, zero-price policy) — độc lập hoàn toàn, không
  đổi.
- `TASK-108B` implementation — chỉ mở khi `TASK-105C` DONE và product
  identity mapping có lời giải.
- Manual Pending resolution UI/workflow đầy đủ — chỉ cần xác định seam
  (dưới đây), không implement toàn bộ.
- Diagnostic/review-signal system cho historical outlier đáng ngờ — xem
  block "DATA QUALITY / OUTLIER" bên dưới; ghi HARDENING/BACKLOG, không mở
  rộng scope để xây ngay.

## DATA QUALITY / OUTLIER — HARDENING/BACKLOG (không mở rộng scope)

Một historical vendor price cực thấp (khả năng đọc nhầm, giống sự cố thật
đã xảy ra bên Tracking mà pe-6 vá — DEC-149 §72) **không được** âm thầm
loại bỏ bằng outlier rule hiện tại (Q2, CLOSED — cấm áp ngược). Nếu
implementation SAU NÀY phát hiện được một giá trị lịch sử đáng ngờ mà
không đổi kết quả nghiệp vụ (vd. so `min` với giá trị thứ nhì, log chênh
lệch lớn bất thường), **CÓ THỂ** tạo tín hiệu diagnostic/review — nhưng:

```
KHÔNG được tự thay HistoricalVendorPrice dựa trên tín hiệu đó.
KHÔNG được biến warning thành exclusion ngầm.
KHÔNG mở rộng scope TASK-105C để xây hẳn một review system.
```

Ghi nhận là **HARDENING/BACKLOG** — chưa có seam cụ thể trong Phase 1, để
lại cho một task riêng nếu cần.

## Historical Dependencies — DEC-152 (superseded nơi xung đột)

- `TASK-105` — DONE. `PriceProvider` Protocol, `PendingPriceProvider`,
  `price_engine.apply_prices()` — không đổi, tái dùng nguyên vẹn.
- `TASK-105B` (`FilePriceProvider`) — **BẮT BUỘC PHẢI IMPLEMENT TRƯỚC hoặc
  cùng lúc** — `HistoricalVendorPriceProvider` compose nó, không thể tồn
  tại độc lập nếu `FilePriceProvider` chưa có.
- `DEC-145` §2 — `fold()` (`app/modules/validation/text.py`) cho mọi chuẩn
  hoá text cần dùng.
- **Product identity mapping** (chưa mở, chưa có task ID) — BLOCKING cho
  kết quả không-Pending ở quy mô lớn, KHÔNG BLOCKING cho việc implement và
  test bản thân provider (test dùng `<MÃ>` tổng hợp, không cần mapping
  thật).
- Credential đọc Tracking RTDB (operational, chủ dự án cấp).

## Historical Blocks — DEC-152 (superseded nơi xung đột)

- `TASK-108B` — cần `HistoricalVendorPriceProvider` hoạt động (và mapping
  dependency đóng) để có `AccountingPurchasePrice` không-Pending ở quy mô.

## An Toàn Để Chạy Song Song Với (Parallel-Safe With)

- `TASK-105B-Q3` (dòng phụ) — độc lập hoàn toàn, không chạm chung file.
- `TASK-103` (nếu mở) — độc lập, phục vụ mục đích khác (classification).

## Historical Expected Touch Area — DEC-152 (cần refreeze)

Allowed:
- `app/modules/pricing/historical_vendor_price.py` (mới)
- `app/modules/pricing/historical_vendor_price_provider.py` (mới)
- `tools/pricing/export_historical_vendor_prices.py` (mới)
- `tests/test_historical_vendor_price.py`,
  `tests/test_historical_vendor_price_provider.py` (mới)
- `tests/fixtures/historical_vendor_price/` (mới, tổng hợp)
- `docs/tasks/TASK-105C-historical-vendor-price-provider.md` (file này)
- `PROJECT/PROJECT_PROGRESS.md`, `PROJECT/LO_TRINH_DE_HIEU.md`
- `docs/sessions/`

Không được đụng vào nếu chưa có Scope Expansion:
- `app/modules/pricing/provider.py`, `price_engine.py`,
  `file_price_provider.py` (khi đã tồn tại từ `TASK-105B`) — chỉ COMPOSE,
  không sửa.
- `app/pipeline.py`, `app/modules/domain/models.py`.
- Golden fixture/expected, `TASK-110`, `governance/**`.
- Bất kỳ file nào của repo `Tracking`.

## Subtask (Subtasks)

- [ ] 105C.1 `compute_historical_vendor_price_series()` — hàm thuần, đầy đủ
      test (retired NCC, sentinel, multi-NCC MIN, tie, gap, mã lạ)
- [ ] 105C.2 `HistoricalVendorPriceProvider` (compose `FilePriceProvider`)
- [ ] 105C.3 `tools/pricing/export_historical_vendor_prices.py` — fetch +
      gọi 105C.1 + ghi file bất biến
- [ ] 105C.4 Test suite đầy đủ, fixture tổng hợp
- [ ] 105C.5 Golden regression check (không đổi)
- [ ] 105C.6 `scripts/branch_authority_check.sh` = `AUTHORITY_OK` tại SHA
      giao nộp

## Historical Ready Gate — DEC-152 (SUPERSEDED cho current authorization)

Dùng `governance/core/TASK_READY_GATE_STANDARD.md`.

- [x] Objective rõ ràng.
- [x] Scope đã được xác định.
- [x] Out-of-scope đã được xác định (product mapping dependency, RTDBPriceProvider
      loại hẳn, capture layer inv.cong/_c.min không bắt buộc).
- [x] Dependency (`TASK-105`, `TASK-105B`) — `TASK-105` DONE;
      `TASK-105B` **chưa DONE**, ghi rõ là dependency phải implement
      trước/cùng lúc (không waived, không blocking cho việc MỞ file task
      này, nhưng blocking cho việc chạy implementation thật).
- [x] Vùng tác động dự kiến đã được xác định.
- [x] Yêu cầu liên quan đã hiểu rõ (`DEC-145`→`DEC-152`, `ADR-101`,
      `ADR-103`, `OD-105B-01`).
- [x] Tác động dữ liệu đã biết rõ: giá nhập là dữ liệu nghiệp vụ nhạy cảm,
      chưa lộ UI/API ở Phase 1; VND boundary conversion tại biên export.
- [x] Tác động bảo mật đã biết rõ: credential đọc RTDB là operational
      dependency, không code trong repo, không commit secret.
- [x] Không liên quan routing/API (Phase 1 thuần Python + một script batch
      ngoài `app/`).
- [x] Không có migration (chưa có DB).
- [x] Difficulty/Risk/Blast Radius đã chấm điểm (3/3/5).
- [x] Agent tier đã chỉ định (B, escalation C).
- [x] Escalation trigger đã xác định (xem bên dưới).
- [x] Completion Gate đã hoàn thiện và **frozen** trước khi implement.

## Historical Completion Gate — DEC-152 (cần refreeze theo DEC-154)

Dùng `governance/core/TASK_COMPLETION_GATE_STANDARD.md` và
`governance/core/EVIDENCE_STANDARD.md`. `Effective Risk = HIGH` (Blast
Radius theo data path) ⇒ E1 bắt buộc cho mọi REQUIRED check; các check
đụng tới tiền/backdating/Golden hướng tới **E2**.

Toàn bộ 20 check dưới đây map đúng A–T của đề bài, theo thứ tự. Trạng thái
`NOT_TESTED` vì implementation chưa chạy — đúng quy tắc `EVIDENCE_STANDARD`
("chưa thực thi → NOT_TESTED", không được khẳng định PASS mà không có
bằng chứng thật).

| ID | Check (A–T) | Priority | Status | Evidence Level mục tiêu |
|---|---|---|---|---|
| CHECK-105C-01 | (A) exact historical lookup — `Price(NCC,D)` đúng giá trị record | REQUIRED | NOT_TESTED | E1 |
| CHECK-105C-02 | (B) carry-forward: record có `date <= D` gần nhất được chọn đúng | REQUIRED | NOT_TESTED | E1 |
| CHECK-105C-03 | (C) không lấy record có `date > D` (future record bị loại tuyệt đối) | REQUIRED | NOT_TESTED | E1 |
| CHECK-105C-04 | (D) sentinel `0` bị loại khỏi `candidates(D)`, không thành giá | REQUIRED | NOT_TESTED | E1 |
| CHECK-105C-05 | (E) multi-NCC: chọn đúng MIN, ghi đúng `contributing_ncc` kể cả khi hoà | REQUIRED | NOT_TESTED | E1 |
| CHECK-105C-06 | (F) NCC hiện tại "retired" nhưng có giá hợp lệ tại D (trước ngày retired) — VẪN là candidate | REQUIRED | NOT_TESTED | **E2** |
| CHECK-105C-07 | (G) `NCC_RETIRED`/`NCC_MIN_LOAI` hiện tại KHÔNG rewrite kết quả lịch sử — test chạy với danh sách loại trừ giả định khác đi, kết quả không đổi | REQUIRED | NOT_TESTED | **E2** |
| CHECK-105C-08 | (H) `NGUONG_BAT_THUONG` hiện tại KHÔNG rewrite lịch sử — giá trị outlier cũ vẫn được tính, không bị lọc | REQUIRED | NOT_TESTED | **E2** |
| CHECK-105C-09 | (I) `_c.min` KHÔNG được đọc — grep `historical_vendor_price*.py` + `export_historical_vendor_prices.py` cho `_c`, `min` field access = 0 hit liên quan board | REQUIRED | NOT_TESTED | **E2** |
| CHECK-105C-10 | (J) `inv.cong` KHÔNG được dùng để backdate — grep cho `cong`/`inv.` trong toàn bộ module mới = 0 hit | REQUIRED | NOT_TESTED | **E2** |
| CHECK-105C-11 | (K) mã có trong snapshot nhưng không có candidate tại D → `None` → `Pending` | REQUIRED | NOT_TESTED | E1 |
| CHECK-105C-12 | (L) `product_code` không giải quyết được / không khớp mã nào → `Pending`, không đoán | REQUIRED | NOT_TESTED | E1 |
| CHECK-105C-13 | (M) không fuzzy matching — grep cho `difflib`, `fuzz`, `similarity`, `nearest`, `Levenshtein` trong module mới = 0 hit | REQUIRED | NOT_TESTED | E1 |
| CHECK-105C-14 | (N) VND boundary: phép ×1.000 (nghìn→VND) chỉ xảy ra trong `tools/pricing/`, **0 hit** trong `app/modules/pricing/historical_vendor_price*.py` | REQUIRED | NOT_TESTED | **E2** |
| CHECK-105C-15 | (O) deterministic snapshot/replay: chạy lại `HistoricalVendorPriceProvider` trên CÙNG file snapshot 2 lần → kết quả giống hệt (không phụ thuộc thời điểm gọi) | REQUIRED | NOT_TESTED | E1 |
| CHECK-105C-16 | (P) provenance đủ truy ngược: mỗi record có `product_key`/`effective_from`/`effective_to`/`source`/`contributing_ncc`/`captured_at`/`capture_id` | REQUIRED | NOT_TESTED | E1 |
| CHECK-105C-17 | (Q) SOURCE_FAILURE (fetch lỗi) khác `Pending` (determined absence) — test export tool: fetch lỗi → không ghi file mới, giữ nguyên snapshot cũ, exit code khác 0 | REQUIRED | NOT_TESTED | E1 |
| CHECK-105C-18 | (R) Tracking repo không bị sửa — `git -C <Tracking clone> status --short` = rỗng, `git -C <Tracking clone> rev-parse HEAD` không đổi trước/sau toàn bộ implementation | REQUIRED | NOT_TESTED | E1 |
| CHECK-105C-19 | (S) Golden baseline không bị rewrite — `pytest tests/test_golden_baseline.py` kết quả y hệt trước implementation, `lines_digest`/`_covered_digest_fields` không đổi | REQUIRED | NOT_TESTED | **E2** |
| CHECK-105C-20 | (T) full regression: `pytest -q` toàn bộ, 0 regression so với baseline trước `TASK-105C` | REQUIRED | NOT_TESTED | E1 |

**Exit Criteria:** 20/20 REQUIRED PASS; CHECK-105C-06/07/08/09/10/14/19 đạt
E2; Tracking repo diff = 0 tại mọi thời điểm kiểm tra trong suốt
implementation, không chỉ lúc kết thúc.

## Tiêu Chí Hoàn Thành (Exit Criteria)

- [ ] 100% REQUIRED check PASS — 20/20.
- [ ] Evidence level mục tiêu đạt cho mọi check (E1 tối thiểu, E2 cho 7
      check đã đánh dấu).
- [ ] 0 lỗi nghiêm trọng chưa xử lý.
- [ ] `pytest -q` toàn bộ PASS, 0 regression.
- [ ] `docs/tasks/TASK-105C-historical-vendor-price-provider.md` (file
      này) cập nhật Status → `DONE` kèm evidence thật.
- [ ] `PROJECT/PROJECT_PROGRESS.md` và `PROJECT/LO_TRINH_DE_HIEU.md` cập
      nhật.
- [ ] Session handoff viết đầy đủ (Task Mode MAJOR yêu cầu).

## TASK-108B Handoff Contract (mục 24)

```
HistoricalVendorPriceProvider implement đúng PriceProvider Protocol
(app/modules/pricing/provider.py, KHÔNG đổi):

    def lookup(self, product_code: Optional[str],
               sale_date: Optional[date]) -> Optional[Decimal]

TASK-108B sẽ:
  1. Cắm HistoricalVendorPriceProvider vào price_engine.apply_prices()
     qua đúng cơ chế dependency injection đã có (price_provider param của
     run_import(), TASK-105 CHECK-105-04) — KHÔNG sửa price_engine.py.
  2. Cần product identity mapping (dependency chưa đóng ở trên) để
     product_code truyền vào là <MÃ> Tracking hợp lệ, không phải
     product_raw thô.
  3. Nhận Pending cho MỌI dòng cho tới khi mapping tồn tại — đây là hành
     vi ĐÚNG, khớp Golden hiện tại (100% Pending), không phải lỗi.
  4. Provenance của mỗi report phải ghi lại capture_id đã dùng, để
     TASK-108B/TASK-109 (summary) có thể trích dẫn "giá này tính theo dữ
     liệu lịch sử chụp lúc nào".
```

## Golden Impact (mục 17)

**Không đổi.** `Golden Baseline` tiếp tục chạy `PendingPriceProvider` mặc
định — đúng tiền lệ `TASK-105`/`TASK-105B` (`CHECK-105B-12`).
`HistoricalVendorPriceProvider` KHÔNG BAO GIỜ trở thành default ở bất kỳ
đường chạy nào ngoài production thật đã cấu hình tường minh — nhắc lại
ràng buộc đã có từ `DEC-146` §4 (nguyên tắc `Golden` deterministic,
provider gọi mạng/đọc file ngoài không được lẫn vào test mặc định).
`app/pipeline.py`, `models.py` không đổi ⇒ `lines_digest`/
`_covered_digest_fields` không đổi.

## Review Budget (mục 19)

Dùng chung lineage `TASK-105B` (`PROJECT/REVIEW_BUDGET_LEDGER.md` §"Root
Task: TASK-105B"). `Effective Risk = HIGH` ⇒ tối đa **2 blocking repair
cycles** cho lineage này (V4.1 §2), hiện **1 used, 1 remaining** sau
`TASK-105B-RC-1`. Phiên reconciliation `DEC-154` không tiêu cycle, không mở
RC-2.

## Điều Kiện Kích Hoạt Leo Thang (Escalation Triggers)

- Phát hiện `phist` có schema khác với ghi nhận ở `DEC-147`/`DEC-150` khi
  bắt đầu implementation thật (schema drift kể từ audit) → dừng, không tự
  suy đoán, escalate.
- Không tìm được cách provision credential đọc RTDB an toàn (không commit
  secret) → dừng, hỏi chủ dự án.
- Bất kỳ REQUIRED check nào (đặc biệt CHECK-105C-18, Tracking repo không
  bị sửa) FAIL → dừng ngay, không tiếp tục vá.
- Golden regression (CHECK-105C-19) FAIL → dừng, không tự nới lỏng
  Completion Gate.

## Đăng Ký File Đã Thay Đổi (Changed Files Registry)

*(Trống — chưa implementation. Điền khi `TASK-105C` chuyển `IN_PROGRESS`.)*

## Ghi Chú (Notes)

- File này là **Scope Lock + Completion Gate đã frozen** cho
  `HistoricalVendorPriceProvider`, ghi tại `DEC-152`. Không sửa các mục
  Scope/Completion Gate ở trên mà không qua `COMPLETION GATE CHANGE
  PROPOSAL` (`governance/core/TASK_COMPLETION_GATE_STANDARD.md`).
- `DEC-154` đã mở một `COMPLETION GATE CHANGE PROPOSAL` additive ở đầu file
  do business architecture đổi. Vì proposal chưa refreeze, current status là
  `BLOCKED`, không phải `READY`; bảng 20 check bên trên được giữ làm historical
  artifact, không được dùng một mình để mở implementation.
- Kiến trúc "compose `FilePriceProvider`, không duplicate logic" là quyết
  định thiết kế của phiên này (không phải một Owner Decision riêng) —
  tái dùng toàn bộ validation đã có thẩm quyền từ `DEC-145`/`CHECK-105B-*`
  thay vì viết lại. Có thể điều chỉnh khi implementation thật cho thấy lý
  do kỹ thuật chính đáng, qua đúng cơ chế Scope Expansion.
