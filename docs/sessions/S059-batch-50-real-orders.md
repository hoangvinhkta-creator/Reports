# S059 — BATCH 50 REAL ORDERS (Session 1/2)

Nhánh: `implementation/batch-50-real-orders`
Base SHA: `1425c06322b109509f4385d772f3639cca88b63e` (S058, "Golden #4 — SAFE
PENDING"). Lưu ý: chỉ thị mở phiên trích base SHA
`1425c06322105909f4385d772f3639cca88b063e` — hai chuỗi lệch nhau ở vài ký tự
giữa (hoán vị `10`↔`b1` và vài vị trí lân cận). Xác nhận bằng
`scripts/branch_authority_check.sh` (`HEAD_SHA` == `DEFAULT_TIP` ==
`1425c06322b109509f4385d772f3639cca88b63e`, `AUTHORITY_OK`) và bằng nội dung
commit thật (`S058: Golden #4 — SAFE PENDING`, khớp mọi mô tả trạng thái baseline
trong chỉ thị mở phiên). Kết luận: lỗi gõ trong chỉ thị, không phải
`DATA_INTEGRITY_RISK` — nhánh làm việc đứng đúng trên baseline được mô tả.

## Mục tiêu

Chạy một batch THẬT gồm 50 OrderID duy nhất qua production composition hiện
hành (`app.composition.run_import_production`), đo hệ thống đúng như nó hành
xử — không tối ưu cho một đơn PASS — rồi gom nhóm theo root cause và chỉ sửa
những gì thật sự là blocker chung, MỘT lần.

## Cohort đông lạnh (frozen)

- Nguồn: `tests/fixtures/golden/period_2026_01.xlsx` (kỳ 01.2026, 254 đơn thật
  đã ẩn danh — cùng file Golden #1/#3/#4 dùng).
- Quy tắc chọn: 50 OrderID DUY NHẤT đầu tiên theo thứ tự xuất hiện lần đầu
  trong file thô (KHÔNG sort lại theo số hiệu — dữ liệu gốc không đơn điệu
  theo `Số BH`, ví dụ `BH62072` xuất hiện ở vị trí 41 dù số hiệu nhỏ hơn nhiều
  đơn trước đó, và `BTL00296` — tiền tố khác `BH` — xuất hiện ở vị trí 40).
  Đây là một lát cắt liên tục (contiguous) thật của dữ liệu, không chọn tay.
- Script tái lập được: `tools/analysis/batch_50_real_orders.py` (mới, commit
  này). Chạy lại: `python3 tools/analysis/batch_50_real_orders.py
  tests/fixtures/golden/period_2026_01.xlsx --n 50`.
- OrderID đầu tiên (theo thứ tự xuất hiện): `BH62063`.
- OrderID thứ 50 (theo thứ tự xuất hiện): `BH62519`.
- Tổng số dòng thô của 50 đơn: 75 dòng (trên tổng 351 dòng/254 đơn của cả
  file).
- Khoảng ngày: `2026-01-02` .. `2026-01-10`.
- 50 OrderID (thứ tự xuất hiện): BH62063, BH62067, BH62171, BH62273, BH62314,
  BH62331, BH62342, BH62319, BH62337, BH62361, BH62366, BH62368, BH62372,
  BH62406, BH62408, BH62365, BH62377, BH62390, BH62410, BH62415, BH62430,
  BH62435, BH62436, BH62437, BH62445, BH62451, BH62460, BH62439, BH62447,
  BH62464, BH62486, BH62487, BH62489, BH62496, BH62497, BH62509, BH62511,
  BH62512, BH62517, BTL00296, BH62072, BH62537, BH62545, BH62548, BH62558,
  BH62559, BH62560, BH62586, BH62514, BH62519.

## Chạy lần 1 — TRƯỚC repair (không sửa production code)

Lệnh: `python3 tools/analysis/batch_50_real_orders.py
tests/fixtures/golden/period_2026_01.xlsx --n 50`. Output đầy đủ nằm ở cuối
file này (§Evidence).

```text
INPUT_ORDERS            = 50
AUTO_SUCCESS             = 1
REVIEW_QUEUE             = 49
PENDING_NOT_QUEUED       = 0
ERROR                    = 0
SILENTLY_DROPPED         = 0

AUTOMATION_RATE          = 1/50  = 2.0%
ORDER_ACCOUNTING_RATE    = 50/50 = 100.0%
```

### Root-cause Pareto (đơn trong cohort)

| Root Cause (canonical category) | Orders | Lines | % batch | Current safe behavior | Est. fix size | Classification |
|---|---|---|---|---|---|---|
| `Missing.PurchasePrice` (chỉ một mình) | 41 | 58 | 82% | Batch-scoped INFO item, `accounting_purchase_price=None`, không bịa 0 (DEC-103) | N/A — không phải code defect | Đã biết/đã chấp nhận, xem Golden #2 |
| `Missing.PurchasePrice` + `Suspicious.ERP` | 4 | 5 | 8% | ERP `Lợi nhuận` âm → tín hiệu INFO riêng (DEC-128 §2), không dùng để suy giá | N/A | Đã biết/đã chấp nhận |
| `Missing.PurchasePrice` + `Suspicious` + `Suspicious.ERP` | 2 | 9 | 4% | `sell_price_zero`/`quantity_not_positive` → WARNING đúng thiết kế (dòng phụ kiện tặng kèm giá 0, hoặc dòng `SL=0`) | N/A | Đã biết/đã chấp nhận |
| `Missing.PurchasePrice` + `Suspicious` | 2 | 2 | 4% | như trên | N/A | Đã biết/đã chấp nhận |
| (không chạm review queue nào) — `AUTO_SUCCESS` | 1 | 1 | 2% | `BH62063` — registry hit, không cần review | — | N/A |

100% root cause của 49/50 đơn REVIEW_QUEUE là **thiếu giá vốn thật** (chưa có
Price Master — DEC-103, cùng lớp blocker khiến Golden #2
`WAITING_REAL_DATA`), cộng thêm một số dòng bị flag `Suspicious`/
`Suspicious.ERP` ĐÚNG THEO THIẾT KẾ (giá 0 hợp lệ cho phụ kiện tặng kèm, `SL=0`
hợp lệ cho một dòng điều chỉnh, lợi nhuận ERP âm là tín hiệu chưa kiểm chứng
theo DEC-128 §2). Không tìm thấy causa nào khác (không `EmployeeMapping`,
không `OrderInconsistency`, không `Duplicate`, không `SourceClassification`
chạm bất kỳ đơn nào trong cohort — xác nhận bằng
`review_queue_category_totals` toàn file, xem Evidence).

## Xác minh thủ công (Manual Validation Sample)

Chọn theo đúng tiêu chí bắt buộc: tự động thành công, Review Queue/Pending,
Qty>1, Discount!=0, nhiều dòng/1 OrderID, Suspicious, Suspicious.ERP. **Không**
tìm được đơn nào có sản phẩm `GIA_DUNG` trong cohort này (100% dòng
`product_group_final=DIEN_MAY/DEFAULT` — TASK-103 Product Classification chưa
tồn tại ở Phase 1) nên tiêu chí "nhiều category sản phẩm" không thoả được
bằng dữ liệu hiện có — ghi nhận N/A, không suy diễn.

| OrderID | Vai trò trong sample | Kiểm tra | Kết quả |
|---|---|---|---|
| `BH62063` | AUTO_SUCCESS | `total_sales=SellPrice×Qty−Discount` (7.500.000×1−0=7.500.000, khớp `Doanh số bán` thô); `AccountingProfit=(7.500.000−7.000.000)×1=500.000`; `EligibleKpiProfit=500.000`; `ConversionScheme=ADS_7_5` (nhân viên Tín Phát, `default_lead_source=ADS`, DEC-109) | `CORRECT_AUTO` |
| `BH62439` (4 dòng) | multi-line + Qty>1 + Discount!=0 | dòng 52 (Qty=2,Discount=100.000): `total_sales=10.500.000×2−100.000=20.900.000` khớp thô; `AccountingProfit=500.000`; `EligibleKpiProfit=400.000` — khớp nguyên văn Golden #3/#4 đã ký; 3 dòng còn lại (50,51,53) Pending, KHÔNG mượn giá dòng 52 (no cross-line leakage, đã Golden #4 chứng minh lại) | dòng 52: `CORRECT_AUTO`; dòng 50/51/53: `CORRECT_PENDING` |
| `BH62067` | REVIEW_QUEUE (Missing.PurchasePrice đơn thuần) | 1 dòng, `accounting_purchase_price=None`, không bịa 0, `total_sales` khớp thô | `CORRECT_PENDING` |
| `BH62171` | Suspicious + Suspicious.ERP | dòng 13 "Giá treo Tivi" SellPrice=0 → phụ kiện tặng kèm thật (không phải fee/shipping nên không bị từ khoá non-product hạ cấp) → `sell_price_zero` WARNING ĐÚNG; ERP `Lợi nhuận=-9.045` → `Suspicious.ERP` INFO ĐÚNG (DEC-128 §2); `total_sales=0×1−0=0` khớp thô | `CORRECT_PENDING` |
| `BH62365` | Suspicious.ERP đơn thuần | ERP `Lợi nhuận` âm ở dòng 33, còn lại đúng công thức | `CORRECT_PENDING` |
| `BTL00296` | ID khác tiền tố `BH`, `Suspicious` (SL=0) | dòng 67 "Kệ máy giặt đa năng inox" `SL=0`, `SellPrice=1.300.000`, `total_sales=1.300.000×0−0=0` khớp thô — `quantity_not_positive` WARNING ĐÚNG (dữ liệu thật ghi SL=0, không phải lỗi tính toán) | `CORRECT_PENDING` |

Cross-check bổ sung (toàn cohort, không chỉ sample): `total_sales =
SellPrice×Quantity−Discount` được xác minh trên TOÀN BỘ 75 dòng của 50 đơn
(0 formula mismatch), và chênh lệch `raw.total_sales_raw − total_sales` bằng
đúng `Discount` trên toàn bộ 75 dòng (0 chênh lệch không giải thích được) —
cùng bất biến DEC-114 mà TASK-101 đã xác minh trên toàn file, lặp lại độc lập
ở đây cho đúng cohort.

```text
MANUALLY_VERIFIED_CASES = 6 order (9 dòng được kiểm cụ thể)
CORRECT_AUTO             = 2 dòng (BH62063, BH62439 dòng 52)
CORRECT_PENDING          = 7 dòng
SILENT_ERROR             = 0
UNVERIFIABLE             = 0
SILENT_ERROR_RATE        = 0 / 9 = 0%
```

## Complete Blocking Set

**Không tìm thấy BLOCKING finding nào** theo tiêu chí batch-50 (mục 11 chỉ
thị): không silent wrong monetary result, không silently dropped order,
không common-path crash, không sai order/line association, không sai Review
Queue accounting, không confident result thiếu bằng chứng. Mọi thứ Pending
đều Pending trung thực (`None`, chưa bao giờ suy đoán 0), mọi flag
Suspicious/Suspicious.ERP đều đúng dữ liệu thật, không phải nhiễu do thiếu
non-product keyword.

Một quan sát ĐÃ KIỂM TRA và loại trừ khỏi blocking set: `KpiPurchasePrice`/
`EligibleKpiProfit` (TASK-108B minimum slice) không có detector Review Queue
riêng — nhưng vì `confirmed_adjustments.jsonl` hiện `LOADED rỗng` (không phải
`UNAVAILABLE`) và `kpi_purchase_price` chỉ Pending khi
`accounting_purchase_price is None`, MỌI dòng KPI-Pending trong cohort này
đều là tập con của dòng đã có trong `Missing.PurchasePrice` — không có đơn
nào Pending-KPI mà không Pending-giá-vốn cùng lúc. Không phát sinh
`PENDING_NOT_QUEUED` mới từ góc này trên dữ liệu thật hiện có. Ghi nhận đây
là quan sát cấu trúc, không phải blocker — không mở lại `TASK-108B`.

## Exception Candidates

Không có candidate nào thoả cả BA điều kiện mục 9 (tần suất đo được + đã an
toàn qua Review Queue + ước tính sửa >100 LOC), vì không có blocker nào để
phân loại — tập blocking set rỗng.

## ONE-BATCH REPAIR

**Không sửa production code.** 0 dòng `app/**`, `config/**`, `data/**` thay
đổi. Đây là kết quả hợp lệ theo mục 12 của chỉ thị ("Nếu có zero legitimate
code blockers: make zero production changes. That is a valid result.").

Thay đổi duy nhất của phiên: `tools/analysis/batch_50_real_orders.py` (mới —
công cụ đo lường tái lập được, không phải business logic) và tài liệu
(session log này + status block `PROJECT/PROJECT_PROGRESS.md`).

## Chạy lại — SAU (cùng cohort đông lạnh, không đổi)

Vì không có repair, output SAU giống hệt output TRƯỚC theo thiết kế. Đã xác
nhận bằng `diff` byte-for-byte giữa hai lần chạy độc lập (trước khi viết tài
liệu này và sau khi hoàn tất toàn bộ phân tích) — không có drift.

```text
AUTO_SUCCESS             = 1   (không đổi)
REVIEW_QUEUE             = 49  (không đổi)
PENDING_NOT_QUEUED       = 0   (không đổi)
ERROR                    = 0   (không đổi)
SILENTLY_DROPPED         = 0   (không đổi)
AUTOMATION_RATE          = 2.0%   (không đổi)
ORDER_ACCOUNTING_RATE    = 100.0% (không đổi)
SILENT_ERROR_RATE        = 0%     (không đổi)
```

## Manual Work (mục 8 chỉ thị)

- Đơn cần xử lý tay: 49/50 (98%) — toàn bộ đơn `REVIEW_QUEUE`.
- Dòng cần xử lý tay: 74/75 (dòng duy nhất không cần là dòng `BH62063`).
- Lý do chiếm ưu thế: thiếu giá vốn kế toán (`Missing.PurchasePrice`,
  100% của 49 đơn), cộng thêm 8 dòng có tín hiệu `Suspicious`/`Suspicious.ERP`
  (5 đơn) — đều là tín hiệu ĐÚNG, không phải nhiễu.
- `MANUAL_WORK_REDUCTION`: **NOT_YET_MEASURABLE**. Không tìm thấy baseline
  thời gian xử lý tay cũ nào trong repo (`PROJECT/PROJECT_PROGRESS.md`,
  `PROJECT/PROJECT_DECISIONS.md`, `docs/analysis/`) — không bịa một con số.

## Review Queue (mục 14)

Dùng nguyên `TASK-110` Review Queue hiện có, không tạo queue mới, không thêm
category mới (`TASK-110` có `repair_cycles_remaining = 0`,
`EXHAUSTED_PRE_V4.1` — không có Owner Extension cho phiên này, xem
`PROJECT/REVIEW_BUDGET_LEDGER.md` và `governance/core/V4_1_POLICY_FREEZE.md`
§14 điểm 2). Mỗi item chạm cohort đều mang đủ category, severity,
provenance (source_rows/order_id) để một người soát mở đúng dòng — xác nhận
bằng dump chi tiết ở Evidence. Không tuyên bố `TASK-110 DONE` — batch này chỉ
là bằng chứng SỬ DỤNG, không phải Completion Gate của `TASK-110`.

## Regression

```text
Golden #1 (BH62063)              : PASS (test_golden_bh62063_kpi.py, 3 test)
Golden #3 (BH62439 dòng 52)      : PASS (test_golden_bh62439_kpi.py, 7 test)
Golden #4 (BH62439 dòng 53)      : PASS (test_golden_bh62439_safe_pending.py, 6 test)
Golden Baseline                  : PASS — 58 passed, 2 skipped (không đổi)
Golden #2                        : KHÔNG đọc, KHÔNG sửa, KHÔNG reopen TASK-105C/105E
Full pytest                      : 1041 passed, 11 skipped, 0 failed (không đổi so với S058)
Validators   : structure/project_state/evidence/task_completion PASS;
               reference_integrity FAIL đúng 3 issue baseline TASK-REM-T06
               (REG-01, không đổi, không phải do phiên này).
branch_authority_check.sh        : AUTHORITY_OK
```

## Kết luận

`BATCH_50_PASS`. 50 đơn thật được xử lý deterministic qua production
composition thật; 100% được accounted for; 0 silently dropped; sample xác
minh tay không tìm thấy silent error nào; phân bố outcome đã biết và trung
thực; nguyên nhân chiếm ưu thế (thiếu giá vốn) đã đo được và KHÔNG phải code
defect (cùng lớp với Golden #2); không có blocker hợp lệ nào để sửa — 0 thay
đổi production, đúng theo mục 12. Session 1/2: **không cần Session 2** cho
batch cohort này (không có finding nào cần validate/repair thêm) — nhưng
brief cho phép tối đa 2 phiên nếu Owner/reviewer độc lập muốn một vòng review
riêng trên cùng cohort đã đông lạnh này.

## Evidence — output đầy đủ của `tools/analysis/batch_50_real_orders.py`

```text
==============================================================================
BATCH 50 REAL ORDERS — tests/fixtures/golden/period_2026_01.xlsx
==============================================================================
cohort_size (unique OrderIDs)     : 50
first_order_id                    : BH62063
last_order_id                      : BH62519
total_lines_in_cohort              : 75
date_range                         : 2026-01-02..2026-01-10

-- Order Accounting --
  AUTO_SUCCESS        : 1
  REVIEW_QUEUE        : 49
  PENDING_NOT_QUEUED  : 0
  ERROR               : 0
  SILENTLY_DROPPED    : 0
  AUTOMATION_RATE          : 1/50 = 2.0%
  ORDER_ACCOUNTING_RATE    : 50/50 = 100.0%

-- Review Queue category totals (whole-file, for context) --
  EmployeeMapping              items=   7  affected_rows=0
  Missing.PurchasePrice        items=   1  affected_rows=349
  Suspicious                   items=  11  affected_rows=11
  Suspicious.ERP               items=  22  affected_rows=22
  TOTAL review_queue items: 41

-- Root-cause Pareto (cohort orders only) --
  reasons=['Missing.PurchasePrice']
    orders= 41  lines= 58  order_ids=['BH62067', 'BH62273', 'BH62314', 'BH62319', 'BH62331', 'BH62337', 'BH62342', 'BH62361', 'BH62366', 'BH62368', 'BH62372', 'BH62377', 'BH62390', 'BH62406', 'BH62408', 'BH62410', 'BH62415', 'BH62430', 'BH62435', 'BH62436', 'BH62439', 'BH62445', 'BH62447', 'BH62451', 'BH62460', 'BH62486', 'BH62487', 'BH62489', 'BH62496', 'BH62497', 'BH62509', 'BH62512', 'BH62514', 'BH62517', 'BH62519', 'BH62537', 'BH62545', 'BH62548', 'BH62559', 'BH62560', 'BH62586']
  reasons=['Missing.PurchasePrice', 'Suspicious.ERP']
    orders=  4  lines=  5  order_ids=['BH62072', 'BH62365', 'BH62437', 'BH62558']
  reasons=['Missing.PurchasePrice', 'Suspicious', 'Suspicious.ERP']
    orders=  2  lines=  9  order_ids=['BH62171', 'BH62464']
  reasons=['Missing.PurchasePrice', 'Suspicious']
    orders=  2  lines=  2  order_ids=['BH62511', 'BTL00296']
```

Đầy đủ tool: `tools/analysis/batch_50_real_orders.py` (mới, commit này) —
chạy lại được bất cứ lúc nào bằng lệnh ở §Cohort đông lạnh.
