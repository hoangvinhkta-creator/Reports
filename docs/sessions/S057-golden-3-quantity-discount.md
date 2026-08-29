# S057 — GOLDEN #3 — QUANTITY + DISCOUNT

Session 1 / Maximum 2 (session brief "SESSION — GOLDEN #3 — QUANTITY +
DISCOUNT"). Branch `implementation/golden-3-quantity-discount`, base
`89c0a27a3455e2a67f3ef8fb1bbbaf6292c85502`.

## 1. Mục tiêu

Chứng minh, bằng MỘT đơn hàng thật, arithmetic đúng khi `Quantity > 1` VÀ
`Discount != 0` cùng xảy ra, qua production composition thật
(`app.composition.run_import_production`), không DI thủ công.

Golden #2 (`implementation/golden-2-historical-vendor`) KHÔNG bị đụng tới —
không reopen `TASK-105C`/`TASK-105E`.

## 2. Tìm case thật

Quét CẢ HAI kỳ nghiệp vụ thật (`tests/fixtures/golden/period_2026_01.xlsx` —
254 đơn, `period_2026_06.xlsx` — 146 đơn) qua `run_import_production()` thật,
lọc `Quantity > 1 AND Discount != 0`. Kết quả: đúng 3 dòng thật thoả điều
kiện (`BH62439`/Điều hòa Daikin, `BH63153`/Tivi LG, `BH63608`/Tivi Samsung),
tất cả `accounting_purchase_price = None` (Pending) TRƯỚC phiên này — vì
`data/historical_confirmed/registry.jsonl` (nguồn giá vốn DUY NHẤT cho mọi
dòng pre-cutover, `INV-47`) khi đó chỉ có ĐÚNG một entry, khoá riêng cho
`BH62063` (`INV-52`: khoá = `(order_id, raw_identity_key, sale_date)`, không
khớp chéo đơn/sản phẩm khác). Đây CHÍNH XÁC là lớp blocker đã khiến Golden #2
`WAITING_REAL_DATA` — không có entry Owner-confirmed thứ hai.

Do KHÔNG được bịa purchase price, phiên này hỏi trực tiếp Owner (qua
`AskUserQuestion`) chọn 1 trong 3 candidate và cung cấp giá vốn thật +
provenance. Owner chọn **BH62439 — Điều hòa Daikin FTHF25XVMV** (dòng
`source_row=52`, một trong 4 dòng của đơn BH62439), xác nhận giá vốn
**10.250.000 VND** qua CÙNG cơ chế `OWNER_MANUAL_LEGACY_CONFIRMATION` đã
dùng cho `BH62063` (Tracking "Tồn"/giá mua công khai tại thời điểm bán,
không có snapshot lịch sử reopenable cho ngày 2026-01-08 — LEGACY DATA GAP,
không phải historical replay đã verify).

## 3. Oracle (ghi TRƯỚC khi sửa code/data)

```text
OrderID              : BH62439
SaleDate             : 2026-01-08
RawProductName       : "Điều hòa Daikin FTHF25XVMV"
Quantity             : 2
SellPrice            : 10.500.000 VND
Discount             : 100.000 VND
Identity             : TRACKING:FTHF25XVMV
PurchasePrice        : 10.250.000 VND (Owner-confirmed, OWNER_MANUAL_LEGACY_CONFIRMATION)
PurchasePriceSource  : Tracking "Tồn"/giá mua công khai tại 2026-01-08

AccountingProfit     = (10.500.000 - 10.250.000) × 2       = 500.000 VND
EligibleKpiProfit    = (10.500.000 - 10.250.000) × 2 - 100.000 = 400.000 VND
```

Không có confirmed adjustment nào cho `BH62439` trong
`data/confirmed_adjustments/confirmed_adjustments.jsonl` (file rỗng) ⇒
`KpiPurchasePrice = AccountingPurchasePrice = 10.250.000`,
provenance `Config:NoConfirmedAdjustment`.

## 4. BEFORE trace (trước khi thêm registry entry)

`run_import_production()` trên `period_2026_01.xlsx`, dòng `BH62439` /
`Điều hòa Daikin FTHF25XVMV`:

```text
price_source               = Pending
accounting_purchase_price  = None
accounting_profit          = None
kpi_purchase_price         = None
eligible_kpi_profit        = None
```

Đúng hành vi THIẾT KẾ (registry MISS → Pending, `INV-51`/`INV-54`) — không
phải bug.

## 5. Complete blocking set

- **B01 (DATA, không phải code).** Không có `HistoricalConfirmedRegistryEntry`
  nào cho `BH62439` trong `data/historical_confirmed/registry.jsonl`. Đây là
  blocker DUY NHẤT ngăn Golden #3 — mọi arithmetic (`Quantity`/`Discount`
  trong `profit_engine.py`/`kpi_profit_engine.py`) đã đúng theo review code
  (không double-count Discount, `AccountingProfit` không phụ thuộc
  `KpiPurchasePrice`), chỉ chưa từng được đo trên dữ liệu thật có cả hai điều
  kiện vì chưa có đơn nào khác `BH62063` resolve được giá.

Không phát hiện blocker thứ hai nào (không mất giá vốn hợp lệ, không double
DI, không lỗi order/line aggregation — `resolve_batch`/`_historical_outcome`
tra cứu ĐỘC LẬP theo từng dòng, generic, không hard-code một entry duy nhất).

## 6. One-batch repair

1. Thêm MỘT entry mới vào `data/historical_confirmed/registry.jsonl`
   (`HCR-BH62439-20260108-1`), dựng qua chính
   `HistoricalConfirmedRegistryEntry` (validate `__post_init__` PASS) rồi
   `to_record()` — không viết tay JSON. Provenance
   `OWNER_MANUAL_LEGACY_CONFIRMATION`, `confirmation_authority=OWNER`,
   `confirmed_by=chu.du.an` (cùng quy ước `BH62063`), `confirmed_at
   =2026-08-29`. +1 dòng, 0 dòng sửa.
2. Thêm `tests/test_golden_bh62439_kpi.py` (7 test tập trung, không sửa test
   nào có sẵn).

**0 dòng `app/**` bị sửa** — không có bug code nào cần vá.

## 7. AFTER trace

```text
price_source               = OWNER_MANUAL_LEGACY_CONFIRMATION
accounting_purchase_price  = 10.250.000
accounting_profit          = 500.000
kpi_purchase_price         = 10.250.000
kpi_purchase_price_provenance = Config:NoConfirmedAdjustment
eligible_kpi_profit        = 400.000
```

Khớp TUYỆT ĐỐI oracle §3. Ba dòng còn lại của CHÍNH đơn `BH62439` (Tủ lạnh
Panasonic, Máy Giặt Sấy LG, Máy lạnh Daikin Inverter 2HP) vẫn `Pending` —
không rò rỉ giá vốn giữa các dòng cùng `OrderID`.

## 8. Tests

- `tests/test_golden_bh62439_kpi.py` — 7 passed (mới).
- `tests/test_golden_bh62063_kpi.py` + `tests/test_registry_store.py` — 8
  passed (không đổi, Golden #1 regression-safe).
- `tests/test_golden_baseline.py` — 58 passed, 2 skipped (không đổi — test
  này gọi `run_import()` KHÔNG truyền `identity_registry`, nên không đọc
  file registry; thêm entry không ảnh hưởng).
- Full `python3 -m pytest -q` — **1035 passed, 11 skipped, 0 failed**
  (trước phiên: 1028 passed — delta = đúng 7 test mới, 0 regression).
- Validators: `validate_structure`/`validate_project_state`/
  `validate_evidence`/`validate_task_completion` — PASS.
  `validate_reference_integrity` — FAIL đúng 3 issue tiền tồn
  `TASK-REM-T06` (baseline, không đổi, không liên quan Golden #3).
  `scripts/branch_authority_check.sh` → `AUTHORITY_OK`, `WITHIN_LIMITS`.

## 9. Production diff

```text
data/historical_confirmed/registry.jsonl   | 1 +
tests/test_golden_bh62439_kpi.py           | new file, 141 dòng
```

0 dòng `app/**`, `config/**` sửa. 0 dòng test có sẵn sửa.

## 10. Deferred (ngoài phạm vi, không mở)

- `BH63153`/`BH63608` (hai candidate thật còn lại thoả `Quantity>1 AND
  Discount!=0`) — không cần cho Golden #3 (một case thật là đủ theo brief).
  Không thêm registry entry cho chúng.
- `TASK-105C`/`TASK-105E`/`TASK-108B` — không chạm, không reopen.
- Golden #2 — không đọc, không sửa nhánh `implementation/golden-2-historical-vendor`.
- Không tạo task mới, không tạo Review Queue mới, không refactor
  `product/identity`/`pricing`/`kpi` ngoài việc thêm 1 dòng dữ liệu.

## 11. Kết luận

`GOLDEN_PASS`. Golden #3 hoàn tất trong Session 1/2 — không cần Session 2.
