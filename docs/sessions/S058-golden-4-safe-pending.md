# S058 — GOLDEN #4 — SAFE PENDING

Session 1 / Maximum 2 (session brief "SESSION — GOLDEN #4 — SAFE PENDING").
Branch `implementation/golden-4-safe-pending`, base
`5abd8697c6ea139b1a60491058a5ee5546b9d966` (= Golden #3 integrated SHA, tip
của nhánh mặc định `claude/extract-upload-repo-gq2ws4` tại thời điểm mở
phiên).

## 1. Mục tiêu

Chứng minh, bằng MỘT dòng bán hàng THẬT, đường SAFE FAILURE: khi hệ thống
không đủ bằng chứng để resolve giá vốn tự động, nó dừng ở `Pending` một cách
trung thực — không bịa giá, không rơi rớt dòng, không rò rỉ giá vốn giữa các
dòng cùng đơn — qua ĐÚNG production composition thật
(`app.composition.run_import_production`), không DI thủ công, không stub.

Golden #4 KHÔNG chứng minh case này resolve được. Mục tiêu NGƯỢC LẠI với
Golden #1/#3: "khi hệ thống không biết, nó không giả vờ biết."

## 2. Tìm case thật

Golden #3 (`docs/sessions/S057-golden-3-quantity-discount.md` §2/§7) đã ghi
lại: 3 trong 4 dòng của đơn `BH62439` (`tests/fixtures/golden/period_2026_01.xlsx`,
`source_row` 50-53) vẫn `Pending` sau khi Golden #3 chỉ thêm registry entry
cho ĐÚNG MỘT dòng (`source_row=52`, Điều hòa Daikin FTHF25XVMV). Ba dòng còn
lại là candidate có sẵn, KHÔNG tự động là Golden.

Đã kiểm tra `data/historical_confirmed/registry.jsonl` (2 entry, khoá
`(order_id, raw_identity_key, sale_date)` theo `INV-52`) — không entry nào
khớp 3 dòng còn lại của BH62439, cũng không khớp hai candidate khác từng được
quét ở Golden #3 (`BH63153`, `BH63608` — vẫn 100% Pending, xác nhận lại bằng
`run_import_production()` thật trong phiên này).

**Case được chọn: `BH62439`, `source_row=53`, "Máy lạnh Daikin Inverter 2 HP
FTKB50ZVMV".** Lý do chọn dòng này thay vì `BH63153`/`BH63608` (cũng là case
thật hợp lệ): dòng 53 nằm CÙNG đơn `BH62439` với dòng 52 ĐÃ resolve (Golden
#3) — đây là bằng chứng cross-line-leakage MẠNH NHẤT sẵn có trong dữ liệu
thật (một giá vốn đã confirm ở dòng khác, cùng đơn, có rò rỉ sang dòng chưa
confirm hay không), và dòng 53 CHƯA từng có oracle/pre-code trace/Review
Queue verification riêng của nó (`test_bh62439_other_lines_in_same_order_stay_pending`
ở Golden #3 chỉ kiểm 4 trường gộp cho cả 3 dòng, không kiểm
`kpi_purchase_price`/Review Queue/provenance chi tiết cho từng dòng).

Không bịa order, không bịa product, không bịa identity mismatch, không bịa
missing data, không bịa giá vốn, không bịa provenance — toàn bộ dữ liệu là
dữ liệu thật đã có sẵn trong fixture đã anonymize, không sửa bất kỳ byte nào
của nó.

## 3. Pre-code Pending oracle

```text
OrderID              : BH62439
SaleDate             : 2026-01-08
SourceRow            : 53
RawProductName       : "Máy lạnh Daikin Inverter 2 HP FTKB50ZVMV"
Quantity              : 1
SellPrice             : 16.300.000 VND
Discount              : 50.000 VND

Identity              : "Máy lạnh Daikin Inverter 2 HP FTKB50ZVMV" (= product_raw,
                        PHẢI giữ nguyên — không bị xoá/thay). TASK-105D identity
                        resolver KHÔNG được wiring vào app.pipeline
                        (_post_cutover_resolver_not_wired, PROJECT_PROGRESS.md
                        "Current Price Architecture"), nên "Identity" ở tầng
                        production hiện tại CHÍNH LÀ product_raw — không có
                        namespace TRACKING/PUBLIC_PURCHASE nào được resolve
                        thêm để có thể "unresolved" theo nghĩa đó.

AccountingPurchasePrice : None  — PURCHASE_PRICE_UNRESOLVED
AccountingProfit        : None
KpiPurchasePrice         : None
KpiPurchasePriceProvenance : "Pending" (KPI_PURCHASE_PENDING)
EligibleKpiProfit         : None
```

Phân loại: **PURCHASE_PRICE_UNRESOLVED**, KHÔNG PHẢI IDENTITY_UNRESOLVED —
`product_raw` là chuỗi rõ ràng, không rỗng, không mơ hồ; cái duy nhất thiếu
là entry registry giá vốn đã confirm khớp đúng
`(BH62439, "Máy lạnh Daikin Inverter 2 HP FTKB50ZVMV", 2026-01-08)`.

## 4. BEFORE trace (production thật, không sửa gì)

`run_import_production()` trên `period_2026_01.xlsx`, dòng `BH62439` /
`source_row=53`:

```text
price_source               = Pending
accounting_purchase_price  = None
accounting_profit          = None
kpi_purchase_price         = None
kpi_purchase_price_provenance = Pending
eligible_kpi_profit        = None
```

Đúng khớp oracle §3 — TRƯỚC khi viết bất kỳ dòng test/code nào.

## 5. Complete finding pass (toàn bộ safe-failure path)

Kiểm tra từng mục A-J của session brief §7 trên dữ liệu thật:

```text
A. Không fabricate identity        → product_raw giữ nguyên, không bị thay
B. Không fabricate purchase price  → accounting_purchase_price = None
C. Không fabricate AccountingProfit → None (phụ thuộc B, đúng thiết kế)
D. Không fabricate KpiPurchasePrice → None, provenance = "Pending" trung thực
E. Không fabricate EligibleKpiProfit → None
F. Dòng KHÔNG bị rơi rớt            → order.line_count == 4, dòng có mặt
G. Trường raw/accounting hợp lệ giữ nguyên → product_raw/quantity/sell_price/
   discount/date khớp oracle nguyên văn
H. Pending reason đủ cụ thể         → Review Queue message: "349 dòng chưa
   có giá nhập kế toán (price_source = Pending). Phase 1 chưa có Price
   Master nên đây là trạng thái đúng, không phải lỗi dữ liệu — nhưng lợi
   nhuận của các dòng này chưa tính được." — trung thực, không claim lỗi dữ
   liệu, không giấu bản chất hệ thống (DEC-128 §1)
I. Không rò rỉ identity/giá vốn từ dòng khác cùng OrderID → dòng 52 (cùng
   đơn) đã resolve = 10.250.000, dòng 53 vẫn None — không mượn
J. Vẫn traceable/accounted for      → có mặt trong result.orders VÀ trong
   Review Queue (mục 6)
```

**Không tìm thấy blocker nào.** Không có defect trực tiếp đe doạ tính đúng
đắn của Golden #4: không crash, không rơi rớt dòng, không zero-substitution,
không rò rỉ chéo dòng, không Pending reason sai/gây hiểu lầm, không wiring
Review Queue bị bypass, không mất dòng Pending khi serialize (`result.orders`
+ `result.review_queue` đều phản ánh đúng dòng 53).

Đường tính riêng của `WorkingLine.price_source` (một string hằng `"Pending"`)
KHÔNG mang theo enum `PendingReason` giàu ngữ nghĩa hơn (`PENDING_HISTORICAL_
CONFIRMATION`, `attempted_sources`) mà tầng `product/identity` đã tính ra rồi
bỏ (`app/pipeline.py::_apply_pre_cutover_identity`). Đây LÀ MỘT KHOẢNG TRỐNG
CÓ THẬT nhưng KHÔNG được xếp là blocker của Golden #4: (1) nó không vi phạm
mục H — message Review Queue hiện tại đã trung thực và đủ cụ thể ("thiếu giá
nhập", không phải một lời nói dối hay một lỗi chẩn đoán sai); (2) sửa nó đòi
hỏi thêm field vào `WorkingLine`/thay đổi hợp đồng giữa `app.pipeline` và
tầng `product/identity` — đúng loại "redesign product identity"/"architecture
change" mà session brief §10/§14 cấm mở rộng phạm vi cho Golden #4. Ghi lại ở
§9 Deferred, không mở task mới.

## 6. One-batch repair

**Không có repair nào — 0 dòng `app/**`, `config/**`, `data/**` bị sửa.**
Hành vi production đã đúng theo thiết kế (Golden #3 đã xác nhận điều này ở
cấp arithmetic; Golden #4 xác nhận thêm ở cấp safe-failure/Review Queue).

## 7. AFTER trace

Không đổi so với §4 (không có repair) — cùng một giá trị, giờ được khoá lại
bằng test mới:

```text
price_source               = Pending
accounting_purchase_price  = None
accounting_profit          = None
kpi_purchase_price         = None
kpi_purchase_price_provenance = Pending
eligible_kpi_profit        = None
```

## 8. Tests

File mới: `tests/test_golden_bh62439_safe_pending.py` (6 test):

1. `test_bh62439_row53_reaches_production_composition_and_is_present` (F/J)
2. `test_bh62439_row53_known_raw_fields_are_preserved_not_erased` (G)
3. `test_bh62439_row53_purchase_price_stays_pending_no_zero_substitution` (A-E)
4. `test_bh62439_row53_does_not_borrow_confirmed_sibling_price_same_order` (I)
5. `test_bh62439_row53_reaches_existing_review_queue_missing_purchase_price` (H, §9 session brief)
6. `test_bh62439_row53_default_run_import_without_wiring_is_still_pending` (0 blast radius, mẫu Golden #3)

```text
tests/test_golden_bh62439_safe_pending.py       : 6 passed (mới)
tests/test_golden_baseline.py                    : 58 passed, 2 skipped (không đổi)
tests/test_golden_bh62063_kpi.py                 : 3 passed (không đổi, Golden #1)
tests/test_golden_bh62439_kpi.py                 : 7 passed (không đổi, Golden #3)
Full python3 -m pytest -q                        : 1041 passed, 11 skipped
                                                    (trước phiên: 1035 passed —
                                                    delta = đúng 6 test mới, 0
                                                    regression, 0 skip mới)
```

Validators:

```text
validate_structure          : PASS (21 required paths)
validate_project_state      : PASS
validate_evidence           : PASS (88 REQUIRED PASS evidence record)
validate_task_completion    : PASS (7 DONE task)
validate_reference_integrity: FAIL — đúng 3 issue tiền tồn TASK-REM-T06
                               (baseline, không đổi, không liên quan Golden #4)
scripts/branch_authority_check.sh : AUTHORITY_OK, DIVERGENCE = WITHIN_LIMITS
                               (ahead default = 0 trước commit phiên này)
```

## 9. Review Queue

**Đã tới, xác nhận bằng test.** `app/modules/validation/rules.py::detect_missing_purchase_price`
+ `config/validation.yaml` (`missing_purchase_price.enabled: true`,
`aggregate: true`, `severity: INFO`) đã wiring sẵn trong `run_import`/
`run_import_production` (bước 11, luôn chạy, không skip — TASK-110). Với
`aggregate: true` (DEC-128 §1), mọi dòng Pending trong TOÀN BỘ kỳ nén thành
ĐÚNG MỘT `ReviewItem` cấp batch (`CATEGORY_MISSING_PURCHASE_PRICE`,
`severity=INFO`) — không phải một item riêng cho `source_row=53`. Item đó
(`period_2026_01.xlsx`) có `provenance.source_rows` chứa 349 dòng, bao gồm
`50, 51, 53` (KHÔNG bao gồm `52` — dòng đã resolve, đúng như kỳ vọng) —
`source_row=53` xác nhận có mặt trong `item.provenance.source_rows`.

Message trung thực: "349 dòng chưa có giá nhập kế toán (`price_source` =
Pending). Phase 1 chưa có Price Master nên đây là trạng thái đúng, không
phải lỗi dữ liệu — nhưng lợi nhuận của các dòng này chưa tính được."

Đây là hành vi HIỆN CÓ của `TASK-110` (aggregate theo thiết kế DEC-128 §1,
KHÔNG phải một queue mới) — session này CHỈ verify bằng test, không sửa
`rules.py`/`validator.py`/`config/validation.yaml`. `TASK-110` tự thân vẫn
`NOT DONE` (`CHECK-110-16` `BLOCKED`, budget `EXHAUSTED_PRE_V4.1` —
`PROJECT/PROJECT_PROGRESS.md`) — Golden #4 KHÔNG tuyên bố `TASK-110 DONE`,
chỉ xác nhận riêng detector `missing_purchase_price` đã hoạt động đúng trên
dữ liệu thật cho case này.

## 10. Regression

```text
Golden #1 (BH62063)  : không đổi, `tests/test_golden_bh62063_kpi.py` 3 passed
Golden #3 (BH62439)  : không đổi, `tests/test_golden_bh62439_kpi.py` 7 passed
                       — dòng 52 (resolved) vẫn 10.250.000/500.000/400.000
Golden #2            : KHÔNG đọc, KHÔNG sửa, không reopen TASK-105C/105E
Golden Baseline       : 58 passed, 2 skipped, không đổi
```

## 11. Production diff

```text
tests/test_golden_bh62439_safe_pending.py   | new file, 6 test
docs/sessions/S058-golden-4-safe-pending.md | new file (session log)
PROJECT/PROJECT_PROGRESS.md                 | +ghi trạng thái Golden #4
```

**0 dòng `app/**`, `config/**`, `data/**` sửa.** Không có repair batch —
production đã đúng theo thiết kế từ trước.

## 12. Deferred (ngoài phạm vi, không mở)

- Plumbing `PendingReason`/`attempted_sources` (tầng `product/identity`) lên
  `WorkingLine` để Review Queue message có thể nói chi tiết hơn "thiếu giá
  nhập" (vd. phân biệt "chưa từng thử nguồn nào" / "đã thử registry, miss").
  Không mở vì: (a) không vi phạm mục H hiện hành (đã trung thực và đủ cụ
  thể); (b) đây là thay đổi hợp đồng giữa `app.pipeline` và tầng
  `product/identity`, thuộc phạm vi kiến trúc TASK-105D (hiện `BLOCKED /
  NOT AUTHORIZED` — xem §5). Không tạo task mới cho việc này theo đúng
  session brief §10 ("không tạo TASK-105F etc.").
- `BH63153`/`BH63608` — hai candidate thật khác cũng 100% Pending, đã quét
  lại và xác nhận vẫn hợp lệ, nhưng KHÔNG cần cho Golden #4 (một case thật
  là đủ). Không thêm test/registry entry cho chúng.
- `TASK-105C`/`TASK-105E`/`TASK-108B`/`TASK-110` (R1-A2→R8) — không chạm,
  không reopen, không tuyên bố DONE.
- Golden #2 — không đọc, không sửa nhánh
  `implementation/golden-2-historical-vendor`.
- Không tạo Review Queue mới, không refactor `product/identity`/`pricing`/
  `kpi`/`validation` ngoài việc thêm 1 file test + 1 session log.

## 13. Kết luận

`GOLDEN_PASS`. Golden #4 hoàn tất trong Session 1/2 — không cần Session 2
(không có blocker nào cần repair).
