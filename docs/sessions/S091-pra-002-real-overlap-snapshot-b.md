# S091 — TASK-PRA-002 Real Data Acceptance: real overlap A → B

Mode: REAL DATA ACCEPTANCE / EVIDENCE ONLY. Continuation của S090.
Không production code · không parser repair · không `make_snapshot_variants` ·
không migration · không schema · không sửa Tracking · không deploy ·
không POST `xac-nhan-du`.

## 1. Authority

```text
CANONICAL_EXPECTED_SHA = d7a1154a2892e5869e286e10da49f750aa0611df
CANONICAL_ACTUAL_SHA   = d7a1154a2892e5869e286e10da49f750aa0611df   → KHỚP, canonical KHÔNG moved
CANONICAL_BRANCH       = claude/extract-upload-repo-gq2ws4 (HEAD branch thật của origin)
SESSION_BRANCH         = claude/pra-002-rda-continuation-814n4h (docs-only, không phải production authority)
TRACKING               = READ-ONLY (không gọi, không sửa)
```

## 2. Owner Business Decision — nghĩa của period header

Owner xác nhận business semantics: **`Ngày D tháng M năm YYYY` = report chỉ
chứa dữ liệu bán hàng của đúng ngày D/M/YYYY** — KHÔNG phải ngày in báo cáo.

Owner cũng cung cấp evidence rằng phần mềm kế toán có thể hiển thị period theo
5 dạng: `Ngày D tháng M năm YYYY` · `Từ ngày dd/mm/yyyy đến ngày dd/mm/yyyy` ·
`Tháng M năm YYYY` · `Quý Q năm YYYY` · `Năm YYYY`.

Đây là **business evidence**, KHÔNG phải giấy phép mở parser cho cả 5 dạng.
Phiên này không sửa parser. Xem mục 11 (FIND-RDA-01).

## 3. Input — Snapshot B

```text
REAL_OR_GENERATED = REAL_OWNER_PROVIDED
FILENAME          = So_chi_tiet_ban_hang_8.xlsx  (attachment Owner upload trong phiên)
SHA256            = 7b421983a73210637d618806446e4a4e3a2d03e3b367694e7ee6ecb3207ce901
SIZE              = 18.209 bytes
SHEET             = "SỔ CHI TIẾT BÁN HÀNG" (1 sheet, 67 × 17)
HEADER_A2         = "Từ ngày 01/09/2026 đến ngày 03/09/2026"   ← đo từ file, khớp Owner
SHEET_DATA_ROWS   = 62  (61 dòng bán + 1 dòng "Tổng cộng")
LINE_COUNT        = 61
ORDER_COUNT       = 40
DETECTED_RANGE    = 2026-09-01 .. 2026-09-03
PHÂN BỐ NGÀY      = 2026-09-01: 54 dòng · 2026-09-03: 7 dòng · 2026-09-02: 0 dòng
BH                = 61/61 khớp `BH\d+` · 0 đơn nhiều ngày · occurrence_index > 1 = 0
FOOTER "Tổng cộng"= SL 71 · Doanh số bán 593.750.000 · Chiết khấu 200.000
SHA256 trước == sau mọi lần chạy
```

**Lệch so với expected trong chỉ thị:** chỉ thị mục 3 ghi "Expected business
period: 01/09/2026 → 02/09/2026". Header thật của file là **01/09/2026 →
03/09/2026** (khớp tiêu đề task và khớp lần Owner tự kiểm tra). Dữ liệu chỉ có
ngày 01/09 và 03/09; **không có dòng nào ngày 02/09**. Ghi evidence thật, không
ép expected value. Header vẫn BAO TRỌN dữ liệu đo được nên không phải cảnh báo.

Workbook KHÔNG sửa, KHÔNG cắt, KHÔNG anonymize, KHÔNG commit vào Git. Không
hiển thị PII.

## 4. Snapshot A — availability

Exact bytes của A **CÒN** trong environment; SHA256 verify lại:

```text
So_chi_tiet_ban_hang_7.xlsx = e1c6cec2e27e5fd831a818cda5fd538fee53e4b5a3e7cb7d9af3e729c40bfa56
                              (khớp S090; 16.196 bytes)
```

→ Chạy được **real A → B** trên DB cô lập bằng exact real bytes của cả hai.
Không reconstruct, không generate, không sửa B để tạo A. `OWNER_A_FILE_REQUIRED
= NO`.

## 5. PostgreSQL context

```text
SERVER  = PostgreSQL 16.13 (Ubuntu) — thật, isolated/non-production
DB1     = rda_ab      : A → B → B (exact reupload)   alembic_version = 0002_snapshots
DB2     = rda_bonly   : chỉ B trên DB sạch           alembic_version = 0002_snapshots
PATH    = route production `POST /run` (app/web/server.py), REPORTS_REQUIRE_HISTORY_DB=1
          → SnapshotRepository thật trên engine PostgreSQL. Không patch production code.
```

## 6. A ⊂ B — quan hệ đo từ file thật

Diff mức logical key `(Số BH, Tên hàng)` trực tiếp trên hai workbook:

```text
keys A = 48 · keys B = 61
KEY chỉ có ở A  = 0     ← A ⊂ B XÁC NHẬN
KEY chỉ có ở B  = 13    (6 dòng ngày 01/09 thuộc đơn BH73894 mới + 7 dòng ngày 03/09)
KEY chung       = 48
```

## 7. B FIRST IMPORT (sau A) — classification

```text
HTTP        = 302
SNAPSHOT_ID = SNAP-20260903021014-7b421983
header_text = Từ ngày 01/09/2026 đến ngày 03/09/2026
hdr_min/max = 2026-09-01 / 2026-09-03
det_min/max = 2026-09-01 / 2026-09-03
coverage    = HEADER_CONSISTENT      ← header BAO TRỌN khoảng đo được
sheet_rows  = 62 · rows_without_order_id = 1 · line_count = 61 · order_count = 40
```

| Phân loại | Số |
|---|---|
| `INSERT` | **13** |
| `SAME` | **35** |
| `SOURCE_CHANGED` | **13** |
| `COLLISION` | 0 |
| `NOT_SEEN` | 0 |
| `REMOVED_CANDIDATE` | 0 |
| `RESULT_REVISED` | 0 |

`35 + 13 = 48` = toàn bộ khoá của A vẫn còn trong B (0 `NOT_SEEN`), đúng A ⊂ B.
`INSERT = 13` khớp chính xác 13 key mới đo được ở mục 6.

## 8. REAL SOURCE_CHANGED — chứng minh bằng dữ liệu thật

13 dòng ngày 01/09 có source fingerprint đổi giữa hai lần export. `changed_fields`
nguyên văn, gộp nhóm:

```text
{"delivery_cost": {"new": "100000", "old": ""}}                      × 4
{"delivery_cost": {"new": "130000", "old": ""}}                      × 1
{"delivery_cost": {...}, "imei": {"new": "<serial>", "old": ""}}     × 8
                                                          tổng       = 13
```

Nguyên nhân nghiệp vụ: kế toán **bổ sung chi phí giao vận (60.000–130.000) và
IMEI/serial** sau lần export đầu. Đây là SOURCE_CHANGED **thật**, không phải
biến thể dựng ra.

Kiểm chứng đầy đủ:

```text
version cũ IMMUTABLE     : 13 bản version_no=1 vẫn đọc được, vẫn thuộc snapshot A
                           (e1c6cec2), delivery_cost vẫn NULL, imei vẫn rỗng — KHÔNG bị ghi đè
version mới APPENDED     : version_no=2 × 13 (tổng source version 48 → 74)
current → version MỚI    : 0 khoá trỏ sai; current dùng v1 × 48, v2 × 13
changed_fields đúng      : chỉ delivery_cost và imei — không trường tiền nào đổi
mọi trường tiền GIỮ NGUYÊN: quantity · sell_price · total_sales_raw · discount ·
                           source_profit · sale_date · note_raw · employee_raw = giống hệt
flag                     : SOURCE_CHANGED × 13, 13 from_version_id + 13 to_version_id
                           phân biệt, tất cả raised_by snapshot B
KHÔNG cờ loại khác phát sinh
trang snapshot B         : hiện cờ SOURCE (đúng); trang A và trang B-reupload: không cờ
```

PII: `changed_fields` chỉ chứa `delivery_cost` và `imei` (định danh thiết bị),
không có tên/SĐT/địa chỉ khách hàng. Schema source version cũng không có cột
khách hàng nào. Ghi nhận (không mở audit mới, ngoài phạm vi PRA-002): cột
`note_raw` là "Diễn giải" tự do và trong sổ thật có thể nhúng tên khách —
thiết kế sẵn có từ slice A, đã qua Independent Review E2.

## 9. NO DOUBLE COUNT + đẳng thức state(A,B) == state(B)

Kịch bản bắt buộc mục 3.1 của contract, tái lập bằng dữ liệu THẬT:

```text
DB rda_ab (A → B → B)                     CURRENT STATE
  T0     lines=0  orders=0  net=None
  T1_A   lines=48 orders=34 net=468.300.000 raw=468.500.000 qty=55 discount=200.000 collisions=0
  T2_B   lines=61 orders=40 net=593.550.000 raw=593.750.000 qty=71 discount=200.000 collisions=0
  T3_B   lines=61 orders=40 net=593.550.000 raw=593.750.000 qty=71 discount=200.000 collisions=0

DB rda_bonly (chỉ B, DB sạch)
  B      lines=61 orders=40 net=593.550.000 raw=593.750.000 qty=71 discount=200.000 collisions=0
```

**Đẳng thức frozen `state(A,B) == state(B)`:**

```text
current_state_tuple_identical  = True
key_set_identical              = True   (61 vs 61)
(khoá, line_fingerprint) ident = True   ← dạng mạnh nhất của đẳng thức
per_order_identical            = True   (40 đơn: số dòng + SUM(total_sales) từng đơn)
```

**Không double count:**

```text
net   : A=468.300.000  A→B=593.550.000  B=593.550.000  naive(A+B)=1.061.850.000
dòng  : A=48           A→B=61           B=61           naive=109
đơn   : A=34           A→B=40           B=40           naive=74
→ A→B == B, KHÁC naive A+B  ⇒ NO_DOUBLE_COUNT = PROVEN
```

Phần chồng nhau 01/09 KHÔNG bị tính hai lần, kể cả 13 dòng đã bị sửa nguồn.

## 10. EXACT REUPLOAD B

Upload lại **đúng bytes** B (SHA256 identical).

```text
SNAPSHOT_ID  = SNAP-20260903021014-7b421983-01
duplicate_of = SNAP-20260903021014-7b421983
INSERT 0 · SAME 61 (= line_count) · SOURCE_CHANGED 0 · mọi cờ khác 0
source version : 74 → 74   (version_no>1 giữ nguyên 13 — KHÔNG tăng)
result version : 109 → 170 (history observation, không phải business state)
reconciliation_flag : 13 → 13
current state / keyset / per_order : identical
trang snapshot B-reupload : không cờ SOURCE
```

## 11. RESULT_REVISED

```text
số khoá có result_fingerprint khác nhau giữa các run = 0
SUM(n_result_revised) trên mọi snapshot                = 0
→ RESULT_REVISED = NOT_OBSERVED_IN_REAL_DATA — kết quả ĐÚNG, không phải thiếu sót
```

Không tạo biến thể để ép case. C1 giữ nguyên E2 evidence riêng.

## 12. ACCOUNTING SAFETY (B)

Oracle độc lập `app.pipeline.run_import` (entry point đã khoá của Golden, GB-4):

| Đại lượng | Oracle | PostgreSQL current | Footer XLSX |
|---|---|---|---|
| Đơn | 40 | 40 | — |
| Dòng | 61 | 61 | — |
| `SUM(quantity)` | 71 | 71 | 71 |
| `SUM(discount)` | 200.000 | 200.000 | 200.000 |
| `SUM(total_sales_raw)` | — | 593.750.000 | 593.750.000 |
| Net `SUM(total_sales)` | 593.550.000 | 593.550.000 | 593.750.000 − 200.000 |
| `unmapped_lines` | 0 | — | — |

Khớp tuyệt đối cả ba nguồn. (`SUM(delivery_cost)` của B = 1.920.000 — trường
mới được kế toán bổ sung, không nằm trong `total_sales`.)

Golden: `tests/test_golden_baseline.py` → **58 passed, 2 skipped**.
Legacy không hồi quy: `/du-lieu` 200 (cả 3 snapshot hiện) · 3 trang snapshot 200 ·
`/nhan-vien` 200.

## 13. AUTO/PENDING safety + giới hạn Tracking

Claude Cloud vẫn KHÔNG có secret Tracking → capture giá rỗng (tiền lệ frozen
`tests/test_pipeline_history_vertical.py`). KHÔNG fake Tracking, KHÔNG thay
Tracking data để ép AUTO.

```text
status = PENDING × 61 · price_source = "Pending" × 61
accounting_purchase_price NOT NULL = 0 · accounting_profit NOT NULL = 0
```

```text
REAL ACCOUNTING/PERSISTENCE PATH = tested
REAL AUTO PATH                   = not tested in this environment
```

PENDING fail-safe KHÔNG phải production defect — hệ thống không bịa giá.

## 14. COVERAGE

```text
Snapshot B : HEADER_CONSISTENT
             header 2026-09-01..2026-09-03 ⊇ detected 2026-09-01..2026-09-03
Snapshot A : DETECTED_ONLY (giữ nguyên — KHÔNG sửa historical DB/parser để đổi trạng thái)
```

Owner Decision ở mục 2 đã xác định semantic của header A, nhưng semantic đó
KHÔNG được dùng để tự nâng trạng thái đã ghi.

Chưa POST `xac-nhan-du` cho bất kỳ snapshot nào. Chỉ Owner confirmation mới
nâng `CONFIRMED_COMPLETE`.

## 15. FIND-RDA-01 — cập nhật phân loại

```text
CŨ  : DATA_SHAPE_UNKNOWN
MỚI : OWNER_SEMANTIC_CONFIRMED
RULE: "Ngày D tháng M năm YYYY" = single-day report coverage (đúng ngày đó)
```

**Production có thực sự cần sửa parser để hỗ trợ an toàn việc xác nhận đủ cho
export một ngày không? → KHÔNG.**

Bằng chứng đọc mã: `SnapshotRepository.confirm_coverage` chỉ gọi
`coverage.confirmation_error`, và hàm đó kiểm đúng 5 điều — đã xác nhận trước
đó, đã tích ô, khoảng hợp lệ, khoảng ≤ `MAX_CONFIRMED_RANGE_DAYS`, và khoảng
xác nhận bao trọn `detected`. **Không nhánh nào đòi `HEADER_CONSISTENT`.** Một
snapshot `DETECTED_ONLY` như A vẫn được Owner xác nhận bình thường.

```text
→ DEFER. Không viết repair. Ước tính cũ ~8–12 LOC giữ nguyên là ước tính,
  không phải cam kết. Không mở rộng parser Tháng/Quý/Năm chỉ vì screenshot
  cho thấy các dạng đó tồn tại.
```

## 16. Đối chiếu EXACT frozen completion table (mục 15)

| Bước | Kết quả | Bằng chứng |
|---|---|---|
| RDA-1 | **PASS** | S090 + tái lập hôm nay: HTTP 302, INSERT 48 / SAME 0 / SOURCE_CHANGED 0, line_count 48, order_count 34, tổng current khớp oracle + footer |
| RDA-2 | **PASS** | S090 (A exact reupload) + hôm nay (B exact reupload): `duplicate_of` đúng, `n_same = line_count`, 0 source version mới, tổng current không đổi, không cờ SOURCE |
| RDA-3 | **PASS** (có sai lệch ghi rõ) | Export thật thứ hai; A ⊂ B (0 `NOT_SEEN`); phần mới `INSERT` 13; **đẳng thức state(A,B) == state(B) khớp tuyệt đối kể cả tập (khoá, fingerprint)**. Sai lệch so với chữ nghĩa bảng: `n_same` = 35 chứ không phải 48, vì 13 khoá A **thực sự bị kế toán sửa** → `SOURCE_CHANGED`. Không ép thành SAME (chỉ thị §7) |
| RDA-4 | **PARTIAL** | Cơ chế SOURCE_CHANGED chứng minh bằng **dữ liệu thật** (13 cờ, `changed_fields` nguyên văn, version cũ immutable, current → version mới, 0 cờ khác). CHƯA thoả assertion riêng của kịch bản `--edit-line`: không có thay đổi `sell_price`/`total_sales_raw` nào trong dữ liệu thật, nên phép kiểm "SUM(total_sales) đổi đúng bằng delta" `NOT_OBSERVED_IN_REAL_DATA` |
| RDA-5 | **BLOCKED** | Cần ĐỒNG THỜI: (a) một export thật trong đó một dòng đã có BIẾN MẤT (dữ liệu thật hiện có `NOT_SEEN = 0` vì B ⊃ A) và (b) Owner POST `xac-nhan-du` tường minh. Phiên không tự xác nhận, không tạo biến thể |
| RDA-6 | **PARTIAL** | Golden `58 passed, 2 skipped` PASS; cohort S068 không có trong môi trường → `NOT_TESTED` |

```text
CHECK-PRA002-14 = BLOCKED   (không còn NOT_TESTED — đã có E1 evidence thật cho
                             RDA-1/2/3; blocked trên Owner input cho RDA-4/5)
CHECK-PRA002-15 = NOT_TESTED (Owner deploy Render; phiên không có egress, không deploy)
```

## 17. Owner input còn cần

```text
1) COVERAGE CONFIRMATION cho snapshot B — chỉ Owner mới quyết:
     SNAPSHOT_ID             = SNAP-20260903021014-7b421983
     DETECTED_RANGE          = 2026-09-01 .. 2026-09-03
     MEASURED_RANGE          = 2026-09-01 .. 2026-09-03 (54 dòng 01/09, 7 dòng 03/09, 0 dòng 02/09)
     HEADER_RANGE            = 2026-09-01 .. 2026-09-03
     CURRENT_COVERAGE_STATE  = HEADER_CONSISTENT
   Câu hỏi: "Snapshot này có phải là export ĐẦY ĐỦ cho khoảng
   01/09/2026 → 03/09/2026 không?"

2) Để mở khoá RDA-5 (REMOVED_CANDIDATE): một export thật muộn hơn trong đó ít
   nhất một chứng từ đã có bị xoá/huỷ — HOẶC Owner cho phép đường controlled
   copy ASSUMPTION D14 mà hợp đồng frozen đã cho phép.

3) Để đóng assertion tiền của RDA-4: một export thật có sửa đơn giá/doanh số
   của một dòng đã tồn tại — hoặc chấp nhận evidence SOURCE_CHANGED thật hiện
   có là đủ (Owner quyết, không phải agent).
```

## 18. Ngân sách và phạm vi

```text
CODE_REQUIRED          = NO
PRODUCTION_CODE_ADDED  = 0 dòng
CHANGE_BUDGET_STATE    = 1.460 / 1.500   REMAINING = 40   (KHÔNG đổi)
CHANGE_BUDGET_REQUIRED = NO
TRACKING_CHANGED       = NO
SCOPE_CHECK            = tuân thủ hard exclusions mục 20 của chỉ thị
```
