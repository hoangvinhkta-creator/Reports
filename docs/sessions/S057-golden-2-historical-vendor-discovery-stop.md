# S057 — GOLDEN #2 (HISTORICAL VENDOR PRICE) — DISCOVERY, ARCHITECTURE_CHANGE_REQUIRED

SESSION 1 / MAXIMUM 2 của Golden #2. Mục tiêu theo brief: tìm MỘT đơn hàng
thật mà purchase-price resolution đi qua nhánh historical NCC/vendor-price
(`TRACKING:<mã>` → `HistoricalVendorMin` từ `phist`) thay vì nhánh "Tồn"/
`OwnerManualLegacyConfirmation` mà Golden #1 (`BH62063`) đã dùng. Kết luận
phiên này: **không tìm được, và không thể tìm được từ dữ liệu/kiến trúc
hiện có** — đây là một giới hạn kiến trúc + dữ liệu đã biết trước, không
phải một boundary trực tiếp có thể sửa trong một batch.

## 1. Git target

```text
Base SHA (task brief)     : 89c0a27a3455e2a67f3ef8fb1bbbaf6292c85502
HEAD trước phiên          : 89c0a27a3455e2a67f3ef8fb1bbbaf6292c85502 (khớp)
Branch                    : implementation/golden-2-historical-vendor
Upstream                  : origin/implementation/golden-2-historical-vendor
Working tree trước phiên  : clean
```

`bash scripts/branch_authority_check.sh` trước thay đổi:

```text
DEFAULT_BRANCH   : claude/extract-upload-repo-gq2ws4
DEFAULT_TIP      : 89c0a27a3455e2a67f3ef8fb1bbbaf6292c85502
HEAD_SHA         : 89c0a27a3455e2a67f3ef8fb1bbbaf6292c85502
ahead default    : 0 commit    behind default : 0 commit
cumulative LOC   : 0
DIVERGENCE       : WITHIN_LIMITS
AUTHORITY        : BRANCH_WITH_UPSTREAM
RESULT           : AUTHORITY_OK
```

`git remote show origin` xác nhận nhánh mặc định thật là
`claude/extract-upload-repo-gq2ws4`; nhánh session đứng đúng tại
`DEFAULT_TIP`, 0 ahead / 0 behind — không có track song song, không có công
việc trùng lặp kiểu `DEC-118`. Golden #1 (`89c0a27`) xác nhận `GOLDEN_PASS`
tại `S056`, FROZEN, không bị đụng tới trong phiên này.

## 2. Phạm vi điều tra (§3–§6 của brief)

Điều tra đầy đủ trước khi viết bất kỳ oracle hay code nào, theo đúng thứ tự
brief yêu cầu — tìm đơn hàng thật, tìm dữ liệu NCC lịch sử thật, chạy qua
production entry point thật.

### 2.1 Đơn hàng bán thật khả dụng

`data/samples/` không tồn tại trên đĩa (`.gitignore` theo `DEC-108`). Dữ
liệu bán hàng thật duy nhất còn trong repo là hai fixture Golden đã anonymize
PII (`tests/fixtures/golden/period_2026_01.xlsx` — 256 đơn,
`period_2026_06.xlsx` — 148 đơn). Theo `tests/fixtures/golden/anonymize.py`,
chỉ PII khách hàng (địa chỉ, SĐT, người giao, IMEI) bị ẩn danh —
`date`/`order_id`/`product`/`qty`/`unit_price`/`sales`/`discount` là giá trị
production thật, verbatim. Nhiều đơn thật khác ngoài `BH62063` có mặt (ví
dụ `BH62067`, `BH62171`, `BH62273`, `BH62314`, `BH62331`, `BH62337`,
`BH62361`…, và dải `BH70xxx`/`BH69064` ở kỳ 06). Toàn bộ ngày bán trong cả
hai file đều **trước** `CUTOVER_DATE` — xem §2.3.

### 2.2 Dữ liệu giá NCC lịch sử (`phist`) thật

Tìm kiếm toàn repo/môi trường (`phist`, `NCC`, `historical vendor`, `.csv`,
`config/historical_vendor_prices/`): **0 kết quả**. Không có file dữ liệu
nào, ở bất kỳ định dạng nào, chứa lịch sử giá nhà cung cấp. Duy nhất một
bản ghi tồn tại trong `data/historical_confirmed/registry.jsonl` — chính là
entry `HCR-BH62063-20260102-1` của Golden #1, có `provenance =
OWNER_MANUAL_LEGACY_CONFIRMATION` (không phải một historical-vendor-min đã
tính từ dữ liệu NCC). `data/confirmed_adjustments/confirmed_adjustments.jsonl`
rỗng (0 byte). Không có `tools/pricing/` (nơi DUY NHẤT được phép fetch
Tracking RTDB theo `docs/tasks/TASK-105C-historical-vendor-price-provider.md`
mục "RTDB Boundary") — môi trường phiên này không có credential/network tới
Tracking RTDB.

### 2.3 Đường composition thật — tại sao KHÔNG đơn thật nào có thể chạm nhánh historical-vendor

Đọc trực tiếp `app/pipeline.py` (không suy diễn):

```text
CUTOVER_DATE = date(2026, 9, 1)     (app/modules/product/identity/registry.py)
Hôm nay (session)                    = 2026-08-29
```

`build_working_data()` (`app/pipeline.py:170-226`) tách dòng theo
`sale_date` TRƯỚC khi chạm bất kỳ resolver nào:

```text
_apply_pre_cutover_identity(lines, ...)   — dòng sale_date < CUTOVER_DATE
apply_prices(remaining_lines, ...)        — dòng date is None hoặc >= CUTOVER_DATE
```

`_apply_pre_cutover_identity()` (`app/pipeline.py:92-138`) gọi
`resolve_batch(rows, registry=..., resolver_factory=...)` mà với dòng
pre-cutover **không bao giờ** chạm `ProductIdentityResolver`
(`INV-47`, trích nguyên văn docstring `registry.py:12-16`) — outcome chỉ
có thể là `HistoricalConfirmed` (tra `HistoricalConfirmedRegistry`, đúng cơ
chế Golden #1) hoặc `PendingProduct`. Nhánh còn lại,
`_post_cutover_resolver_not_wired()` (`app/pipeline.py:76-89`), **raise
`NotImplementedError`** một cách tường minh nếu bị gọi thật — đây là factory
mặc định khi `identity_resolver_factory` không được truyền, và
`app/composition.py` (`run_import_production`) không truyền tham số đó.

Kết luận: **mọi đơn hàng thật hiện có (cả hai fixture Golden) đều
pre-cutover, và theo đúng kiến trúc đã Owner chốt (`DEC-154` §2/P00,
`INV-47`), một dòng pre-cutover KHÔNG BAO GIỜ đi qua `ProductIdentityResolver`
hay bất kỳ `HistoricalVendorMin` nào — dù `TASK-105C` có được implement hôm
nay hay không.** Đây không phải một bug "chưa wiring" có thể vá — đó là
đúng ngữ nghĩa đã được Owner xác nhận cho pre-cutover data (registry lookup
là authority duy nhất cho dữ liệu trước cutover). Chỉ một đơn hàng thật có
`sale_date >= 2026-09-01` mới có cơ hội chạm nhánh `TRACKING →
HistoricalVendorMin` — và không đơn hàng nào như vậy tồn tại trong
repo/môi trường tại thời điểm phiên này (hôm nay còn cách cutover 3 ngày).

### 2.4 `TASK-105C` (chủ sở hữu `HistoricalVendorMin`) — 0 code, BLOCKED

`docs/tasks/TASK-105C-historical-vendor-price-provider.md`:
`Status: BLOCKED`, `IMPLEMENTATION = BLOCKED / NOT AUTHORIZED`
(dòng 145). Đặc tả đầy đủ ngữ nghĩa (`Price(NCC,D)` = record gần nhất
`<= D`, `HistoricalVendorMin` = MIN mọi candidate hợp lệ `> 0`, sentinel `0`
bị loại) nhưng **0 file production tồn tại**:
`app/modules/pricing/historical_vendor_price*.py`,
`tools/pricing/export_historical_vendor_prices.py`,
`tests/test_historical_vendor_price*.py` — không file nào có mặt (`Glob
app/modules/pricing/**` chỉ có `provider.py`, `file_price_provider.py`,
`price_engine.py`, `__init__.py`). Blocker liệt kê tại chính task file
(dòng 148-156): `TASK-105D` contract, gate của chính `TASK-105C` chưa
refreeze, và quan trọng nhất — **mapping `product_raw` → `<MÃ>` Tracking
chưa có task ID nào mở**, nghĩa là ngay cả khi có `phist` thật, provider
cũng không có cách nào tự dịch tên hàng trên chứng từ Reports sang mã board
Tracking (đặc tả cấm tuyệt đối fuzzy/nearest matching, mục "Product
Identity Contract").

### 2.5 `TASK-105E` (composition wiring `TASK-105C` vào `app/pipeline.py`) — PLANNED, chưa cấp phép

`docs/tasks/TASK-105E-price-resolution-composition.md`: `Status: PLANNED`,
Scope Lock **chưa soạn**, Completion Gate **chưa soạn**, implementation
**chưa cấp phép**. Đây là "nơi DUY NHẤT được phép wire provider vào
pipeline" theo chính đặc tả `TASK-105C`. Retrigger điều kiện đã ghi sẵn tại
`docs/tasks/TASK-108B-eligible-costs-owner-definition.md` dòng 2685-2686 và
2758-2759: *"một Golden #2–#4 hoặc một batch thật ≥ 50 đơn **chạm nhánh
post-cutover**"* — tức chính governance đã dự đoán trước: Golden #2-4 chỉ
mở lại `TASK-105E`/`TASK-105C` implementation NẾU nó thực sự chạm dữ liệu
post-cutover. Phiên này xác nhận: chưa có dữ liệu thật nào chạm được nhánh
đó.

## 3. Vì sao đây là STOP, không phải REPAIR BATCH

Brief §13 cấm "voluntary stop" khi boundary "đã hiểu và có thể sửa trong
phiên này". Boundary ở đây **đã hiểu đầy đủ** nhưng **không** sửa được
trong ngân sách một phiên, vì ba lý do độc lập, mỗi lý do đã đủ để chặn:

1. **Không có dữ liệu NCC lịch sử thật** ở bất kỳ đâu (repo, môi trường,
   session brief) — khác Golden #1, nơi Owner cung cấp trực tiếp một điểm
   giá cụ thể (7.000.000 VND) trong session brief của `S053`. Viết một
   `phist` giả để "chứng minh cơ chế" sẽ vi phạm trực tiếp brief §9
   (PROVISIONAL DISCOVERY) + §10 (FAIL-SAFE — không biến uncertainty thành
   giá trị tiền tự tin) + `EVIDENCE_STANDARD` (không bịa bằng chứng).
2. **Không đơn hàng thật nào có thể chạm nhánh này về mặt kiến trúc** — mọi
   dữ liệu thật hiện có đều pre-cutover, và pre-cutover bị khoá cứng
   (`INV-47`, Owner-confirmed `DEC-154` §2) vào đúng nhánh
   `HistoricalConfirmedRegistry` mà Golden #1 đã dùng. Đây không phải một
   "direct blocker" kiểu thiếu wiring — sửa nó nghĩa là đổi chính ngữ nghĩa
   `INV-47` đã Owner chốt, tức `ARCHITECTURE_CHANGE_REQUIRED`/
   `OWNER_DECISION_REQUIRED`, không phải một fix cục bộ.
3. **`TASK-105C` và `TASK-105E` đều đang `BLOCKED`/`PLANNED`, `NOT
   AUTHORIZED`, 0 dòng code** — implement đầy đủ một trong hai (chưa nói cả
   hai) là mở một task MAJOR, Risk 4-5/Blast Radius 5 mới, cần Scope
   Lock/Completion Gate/Independent Review riêng. Brief §7 cấm chính xác
   điều này ("Do NOT implement full TASK-105B/C/E/108B unless the CURRENT
   REAL GOLDEN path genuinely requires the specific piece") — và §3 lại
   không có "current real Golden path" nào thật sự cần nó, vì §2.3 đã
   chứng minh không đơn nào chạm được nhánh đó dù có implement.

Không có finding nào ở đây là "một blocker trực tiếp, cục bộ, sửa được
bằng một batch nhỏ" — brief §13 liệt kê đúng bốn stop reason cho tình huống
này; `OWNER_DECISION_REQUIRED` khớp nhất: cần Owner cung cấp MỘT trong hai
— (a) dữ liệu `phist` thật + một đơn hàng thật post-cutover khi tồn tại,
hoặc (b) một quyết định tường minh mở implementation `TASK-105C`/`TASK-105E`
qua đúng quy trình Ready Gate/Scope Lock/Completion Gate riêng của chúng
(ngoài phạm vi ngân sách Golden #2).

## 4. Không có thay đổi production/test/config/data/governance

Phiên này thuần điều tra (Explore, đọc file, chạy lệnh không mutate). Xác
nhận:

```text
$ git status --short
(rỗng)

$ wc -c data/historical_confirmed/registry.jsonl data/confirmed_adjustments/confirmed_adjustments.jsonl
1281 registry.jsonl
   0 confirmed_adjustments.jsonl
(không đổi so với trước phiên)
```

Không tạo `app/modules/pricing/historical_vendor_price*.py`, không tạo
`tools/pricing/`, không thêm entry giả vào
`data/historical_confirmed/registry.jsonl`, không sửa
`PROJECT/PROJECT_PROGRESS.md`/`PROJECT/PROJECT_DECISIONS.md`/
`PROJECT/REVIEW_BUDGET_LEDGER.md` — cùng pattern hẹp đã dùng ở `S050`–`S052`
khi kết luận là evidence/architecture gap, không phải implementation.

## 5. Validation (bằng chứng KHÔNG regression — E1)

```text
$ uv run pytest -q
1028 passed, 11 skipped   (khớp tuyệt đối S056 — 0 thay đổi)

$ uv run pytest -q tests/test_golden_baseline.py tests/test_golden_bh62063_kpi.py
61 passed, 2 skipped      (Golden #1 KHÔNG regression)

$ python3 governance/scripts/governance/validate_structure.py
GOVERNANCE STRUCTURE: PASS — 21 required paths

$ python3 governance/scripts/governance/validate_project_state.py
PROJECT STATE: PASS

$ python3 governance/scripts/governance/validate_evidence.py
EVIDENCE VALIDATION: PASS — 88 REQUIRED PASS evidence record(s)

$ python3 governance/scripts/governance/validate_task_completion.py
TASK COMPLETION: PASS — 7 DONE task(s)

$ python3 governance/scripts/governance/validate_reference_integrity.py
FAIL — đúng 3 issue tiền tồn của TASK-REM-T06 (không đổi, không liên quan)

$ bash scripts/branch_authority_check.sh
AUTHORITY_OK, DIVERGENCE = WITHIN_LIMITS (0 ahead / 0 behind default)
```

## 6. Task Registry — bằng chứng BEFORE/AFTER

```text
SET B (docs/tasks/*.md)  BEFORE = 22   AFTER = 22
new_registered_task_ids = 0
```

Không tạo task mới (`TASK-105F/G` không mở), không reopen `TASK-105C`/
`TASK-105E`/`TASK-105D`/`TASK-108B`, không đổi trạng thái bất kỳ task nào.

## 7. Kết luận S057

```text
S057 FINAL STATE : STOP — no repairable direct blocker found
  - Real order data: CÓ (hai fixture Golden, PII-anonymized, giá trị nghiệp
    vụ verbatim), nhưng 100% pre-cutover.
  - Real phist/historical-vendor data: KHÔNG tồn tại, ở bất kỳ đâu trong
    repo/môi trường.
  - Production path cho HistoricalVendorMin: KHÔNG tồn tại
    (TASK-105C = 0 code, BLOCKED), KHÔNG có composition seam để wire nó
    (TASK-105E = PLANNED, chưa cấp phép).
  - Ngay cả nếu TASK-105C có code hôm nay: KHÔNG đơn hàng thật nào (trong
    dữ liệu hiện có) có thể chạm nhánh đó, vì INV-47 khoá cứng mọi dòng
    pre-cutover vào HistoricalConfirmedRegistry — đúng kiến trúc Owner đã
    chốt ở DEC-154 §2, không phải lỗi/thiếu wiring.
  - 0 byte production/test/config/data thay đổi; 0 regression
    (1028 passed/11 skipped khớp tuyệt đối S056; Golden #1 = PASS).

STOP_REASON : OWNER_DECISION_REQUIRED
  Cần Owner một trong hai:
  (a) cung cấp trực tiếp dữ liệu phist thật (nhiều NCC, có ngày, cho một
      <MÃ> Tracking cụ thể) GẮN VỚI một đơn hàng thật có sale_date >=
      CUTOVER_DATE (2026-09-01) khi dữ liệu đó xuất hiện — đúng cách Golden
      #1 nhận giá 7.000.000 VND trực tiếp từ Owner ở S053; HOẶC
  (b) một quyết định tường minh mở implementation TASK-105C và TASK-105E
      qua đúng quy trình Ready Gate/Scope Lock/Completion Gate riêng của
      từng task — ngoài phạm vi ngân sách/session Golden #2, cần phiên
      authority riêng theo đúng CLAUDE.md/governance/core/00_SESSION_ORCHESTRATION.md.

Không có phương án nào trong hai lựa chọn trên nằm trong quyền quyết định
của một session Golden #2 đơn lẻ.
```
