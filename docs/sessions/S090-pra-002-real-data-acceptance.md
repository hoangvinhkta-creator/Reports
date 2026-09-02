# S090 — TASK-PRA-002 Real Data Acceptance (continuation sau S089)

Mode: REAL DATA ACCEPTANCE / EVIDENCE ONLY.
Không production code. Không migration. Không schema. Không sửa Tracking.
Không `make_snapshot_variants`. Không deploy.

## 1. Authority

```text
CANONICAL_EXPECTED_SHA = d7a1154a2892e5869e286e10da49f750aa0611df
CANONICAL_BRANCH       = claude/extract-upload-repo-gq2ws4  (HEAD branch thật của origin)
LOCAL_HEAD             = d7a1154a2892e5869e286e10da49f750aa0611df  → KHỚP EXPECTED
BRANCH_AUTHORITY       = 0 ahead / 0 behind origin/claude/extract-upload-repo-gq2ws4
SESSION_BRANCH         = claude/pra-002-rda-continuation-814n4h
TRACKING               = READ-ONLY (không gọi, không sửa — xem mục 5)
```

S089 không phát hiện production defect; RDA bị `BLOCKED_OWNER_INPUT` chỉ vì
Claude Cloud không có workbook kế toán thật. Phiên này Owner đã upload trực
tiếp MỘT workbook thật.

## 2. Input — workbook thật

```text
REAL_OR_GENERATED   = REAL_OWNER_PROVIDED
FILENAME            = So_chi_tiet_ban_hang_7.xlsx  (upload attachment của Owner)
SHA256              = e1c6cec2e27e5fd831a818cda5fd538fee53e4b5a3e7cb7d9af3e729c40bfa56
SIZE                = 16.196 bytes
SHEET               = "SỔ CHI TIẾT BÁN HÀNG" (1 sheet, 54 × 17)
HEADER_A2           = "Ngày 01 tháng 9 năm 2026"
DETECTED_DATE_RANGE = 2026-09-01 .. 2026-09-01  (một ngày duy nhất)
SHEET_DATA_ROWS     = 49   (48 dòng bán + 1 dòng "Tổng cộng")
LINE_COUNT          = 48
ORDER_COUNT         = 34
SHA256_SAU_MỌI_LẦN_CHẠY = e1c6cec2e27e5fd831a818cda5fd538fee53e4b5a3e7cb7d9af3e729c40bfa56 (KHÔNG ĐỔI)
```

Workbook KHÔNG được copy vào git, KHÔNG commit, KHÔNG sửa. Không hiển thị PII
(tên/SĐT/địa chỉ khách hàng) trong bản ghi này.

Hình dạng dữ liệu đo được (không PII):

```text
BH format            = 48/48 khớp `BH\d+` (73692 .. 73920), bh_year_hint duy nhất 2026
Đơn nhiều ngày       = 0
occurrence_index > 1 = 0
Phân bố dòng/đơn     = 25 đơn 1 dòng · 4 đơn 2 dòng · 5 đơn 3 dòng
Footer "Tổng cộng"   = SL 55 · Doanh số bán 468.500.000 · Chiết khấu 200.000
```

## 3. PostgreSQL context

PostgreSQL 16 THẬT, database cô lập/non-production. Không thao tác nào chạm
production DB.

```text
SERVER          = PostgreSQL 16.13 (Ubuntu 16.13-0ubuntu0.24.04.1) x86_64-pc-linux-gnu
DATABASE        = rda_pra002 (isolated, tạo mới trong phiên; drop + create lại trước lần đo cuối)
URL             = postgresql+psycopg://rda:***@127.0.0.1:5432/rda_pra002
MIGRATION       = `alembic upgrade head`
alembic_version = 0002_snapshots        ← xác minh bằng SELECT
TABLES          = alembic_version, legacy_daily_sales, legacy_import,
                  legacy_monthly_reference, legacy_summary_row,
                  order_line_current, order_line_result_version,
                  order_line_source_version, reconciliation_flag,
                  snapshot_line, source_snapshot   (11 bảng)
```

## 4. Production-equivalent path

Đường chạy là ĐÚNG route production `POST /run` của `app/web/server.py`
(Flask test client, không patch production code), với
`REPORTS_REQUIRE_HISTORY_DB=1` và `HISTORY_DATABASE_URL` trỏ PostgreSQL ở trên
→ `create_app()` dựng `SnapshotRepository` thật trên engine PostgreSQL.

## 5. Giới hạn đã biết — Tracking price authority rỗng

Claude Cloud KHÔNG có secret Tracking (`live_pull.is_configured()` = False),
nên phiên này dùng capture Tracking TỐI THIỂU giá rỗng — đúng tiền lệ frozen
`tests/test_pipeline_history_vertical.py`. Hệ quả: mọi dòng ra `PENDING`,
`auto_orders = 0`. Đây KHÔNG phải defect; nó chứng minh chiều an toàn (hệ
thống không bịa giá), nhưng đường AUTO **không được thực thi trên dữ liệu
thật** trong phiên này. Tracking hoàn toàn READ-ONLY: không gọi, không sửa.

## 6. RDA-1 — FIRST REAL IMPORT

```text
HTTP        = 302  → Location: /?run_id=report-20260902T154531Z
SNAPSHOT_ID = SNAP-20260902154531-e1c6cec2
RUN_ID      = report-20260902T154531Z
FINGERPRINT = e1c6cec2e27e5fd831a818cda5fd538fee53e4b5a3e7cb7d9af3e729c40bfa56
FILE_SIZE   = 16196
```

Trên DB sạch (T0: mọi bảng = 0):

| Trường | Giá trị |
|---|---|
| `line_count` | 48 |
| `order_count` | 34 |
| `sheet_data_rows` | 49 |
| `rows_without_order_id` | 1 (đúng dòng "Tổng cộng", không mang dòng bán) |
| `coverage_state` | `DETECTED_ONLY` |
| `detected_date_min/max` | 2026-09-01 / 2026-09-01 |
| `header_date_min/max` | NULL / NULL |
| `duplicate_of_snapshot_id` | NULL |
| `n_insert` | **48** |
| `n_same` | **0** |
| `n_source_changed` | **0** |
| `n_collision` | 0 |
| `n_not_seen` | 0 |
| `n_removed_candidate` | 0 |
| `n_result_revised` | 0 |

Khớp expectation "DB sạch → INSERT = applicable logical lines, SAME = 0,
SOURCE_CHANGED = 0". Không cần điều tra.

## 7. RDA-2 — EXACT REUPLOAD (đúng bytes)

```text
HTTP        = 302  → Location: /?run_id=report-20260902T154531Z-01
SNAPSHOT_ID = SNAP-20260902154531-e1c6cec2-01
FINGERPRINT = e1c6cec2e27e5fd831a818cda5fd538fee53e4b5a3e7cb7d9af3e729c40bfa56  (giống RDA-1)
duplicate_of_snapshot_id = SNAP-20260902154531-e1c6cec2   ← trỏ đúng snapshot #1
```

| Trường | Giá trị |
|---|---|
| `n_insert` | 0 |
| `n_same` | **48 = line_count** |
| `n_source_changed` | **0** |
| `n_collision` / `n_not_seen` / `n_removed_candidate` / `n_result_revised` | 0 / 0 / 0 / 0 |

Trang snapshot #2 (`GET /du-lieu/snapshot/...-01` → 200) KHÔNG có cờ SOURCE.

## 8. Bằng chứng version

```text
SOURCE VERSIONS
  tổng                       = 48
  version_no > 1             = 0        ← exact reupload KHÔNG tạo source version mới
  MAX(version_no)            = 1
  distinct (order,product,occ)= 48
  phân theo snapshot         = SNAP-...154531-e1c6cec2 : 48   (snapshot #2 : 0)

RESULT VERSIONS
  tổng                       = 96
  report-20260902T154531Z    → 48
  report-20260902T154531Z-01 → 48   ← history result observation tăng đúng frozen Slice A contract
  số khoá có result_fingerprint KHÁC NHAU giữa hai run = 0
                                → RESULT_REVISED = 0 là kết quả ĐÚNG, không phải thiếu sót

SNAPSHOT_LINE                = 48 + 48 = 96 (mỗi snapshot ghi đủ 48 dòng đã quan sát)
RECONCILIATION_FLAG          = 0 (không kind nào)
```

## 9. NO-DOUBLE-COUNT — chứng minh bằng database state

Chụp current state XEN GIỮA hai lần import (T1 = sau RDA-1, T2 = sau RDA-2):

```text
T1_AFTER_RDA1 CURRENT_STATE: lines=48 orders=34 total_sales=468300000
                             raw_sales=468500000 qty=55 discount=200000 collisions=0
T2_AFTER_RDA2 CURRENT_STATE: lines=48 orders=34 total_sales=468300000
                             raw_sales=468500000 qty=55 discount=200000 collisions=0

current_state_identical  = True
keyset_identical         = True   (48 bộ (order_key, product_key, occurrence_index, line_fingerprint))
per_order_identical      = True   (34 đơn: số dòng + SUM(total_sales) từng đơn)
order_line_current       = 48 → 48
source_version           = 48 → 48   (version_no>1: 0 → 0)
result_version           = 48 → 96   (history observation — KHÔNG phải business state)
reconciliation_flag      = 0 → 0
fact_table_rows_never_decrease = True
```

Phân biệt rõ: **historical version count** (result_version 48 → 96) tăng theo
hợp đồng lịch sử; **current business state** (dòng, đơn, mọi tổng tiền) KHÔNG
đổi tới từng đồng. Không double count.

## 10. ACCOUNTING SAFETY

Oracle độc lập: `app.pipeline.run_import` — đúng entry point đã khoá của Golden
(GB-4) — chạy trên CHÍNH workbook thật đó.

| Đại lượng | Oracle pipeline | Current state trong PostgreSQL | Footer XLSX |
|---|---|---|---|
| Số đơn | 34 | 34 | — |
| Số dòng | 48 | 48 | — |
| `SUM(quantity)` | 55 | 55 | 55 |
| `SUM(discount)` | 200.000 | 200.000 | 200.000 |
| `SUM(total_sales_raw)` | — | 468.500.000 | 468.500.000 |
| `SUM(total_sales)` (net) | 468.300.000 | 468.300.000 | 468.500.000 − 200.000 |
| `unmapped_lines` | 0 | — | — |

Khớp tuyệt đối cả ba nguồn. Tầng lưu tái lập đúng kết quả pipeline
authoritative, không sai lệch một đồng.

AUTO/PENDING safety (`summary_json` của cả hai snapshot, giống hệt nhau):

```json
{"accounted_orders": 34, "auto_orders": 0, "error_count": 0, "input_orders": 34,
 "review_lines": 48, "review_orders": 34, "total_lines": 48,
 "review_reason_counts": {"IDENTITY_UNRESOLVED": 48, "Missing.PurchasePrice": 48,
  "Pending.accounting_profit": 48, "Pending.accounting_purchase_price": 48,
  "Pending.eligible_kpi_profit": 48, "Suspicious": 1}}
```

```text
input_orders == accounted_orders = 34   → không mất đơn nào
status                = PENDING × 48 (duy nhất một status)
price_source          = "Pending" × 48
kpi_purchase_provenance = "Pending" × 48
accounting_purchase_price NOT NULL = 0
accounting_profit         NOT NULL = 0
```

Với price authority rỗng, hệ thống KHÔNG bịa một giá nhập hay một khoản lợi
nhuận nào. Đó là chiều an toàn cần chứng minh. Xem giới hạn ở mục 5.

## 11. COVERAGE

```text
COVERAGE_STATE = DETECTED_ONLY   (KHÔNG tự nâng CONFIRMED_COMPLETE)
detected       = 2026-09-01 .. 2026-09-01   (đo từ dữ liệu)
header         = NULL .. NULL               (không parse được — xem FIND-RDA-01)
```

Không suy luận "đủ" từ tên file, từ ngày cuối tháng, hay từ row count.

## 12. Trang dữ liệu (production path)

```text
GET /du-lieu                                  → 200; cả hai snapshot đều hiện
GET /du-lieu/snapshot/SNAP-...-e1c6cec2       → 200; không cờ SOURCE
GET /du-lieu/snapshot/SNAP-...-e1c6cec2-01    → 200; không cờ SOURCE
GET /nhan-vien  (legacy PRA-001)              → 200  (không hồi quy)
```

## 13. RDA-6 — Golden

```text
python3 -m pytest tests/test_golden_baseline.py -q
58 passed, 2 skipped in 7.30s
```

Cohort S068 (58 đơn/83 dòng) KHÔNG có trong môi trường này → phần cohort của
RDA-6 vẫn `NOT_TESTED`.

## 14. FINDINGS

### FIND-RDA-01 — Header dạng thứ ba trong dữ liệu thật
Classification: `DATA_SHAPE_UNKNOWN` + `OWNER_DECISION_REQUIRED` — **NON_BLOCKING**.

Ô A2 của workbook thật là `Ngày 01 tháng 9 năm 2026`. `app/history/coverage.py`
chỉ nhận HAI dạng đã đo được: `Từ ngày dd/mm/yyyy đến ngày dd/mm/yyyy` và
`Nhân viên: ..., Tháng M năm YYYY`. Đây đúng là "header dạng thứ ba" mà
TASK-PRA-002 mục 794–796 nêu làm escalation trigger.

Hệ thống đã hành xử ĐÚNG và fail-safe: `parse_header` trả `None`,
`header_date_min/max` = NULL, coverage rơi về `DETECTED_ONLY`. Không mất dữ
liệu, không phân loại sai, không đoán. RDA-1/RDA-2 vẫn PASS đầy đủ.

Câu hỏi cho Owner (KHÔNG tự quyết): chuỗi `Ngày 01 tháng 9 năm 2026` trong
phần mềm kế toán mang nghĩa **khoảng dữ liệu của sổ** (một ngày) hay **ngày
in/kết xuất báo cáo**? Nếu là ngày in, việc nới regex để coi nó là khoảng
coverage sẽ SAI VÀ NGUY HIỂM. Vì vậy KHÔNG mở rộng parser trong phiên này.

Ước lượng nếu Owner xác định đó là khoảng dữ liệu và duyệt sửa: ~8–12 dòng
logic production (1 regex + 1 nhánh trong `parse_header`) — nằm trong 40 LOC
còn lại, nhưng vẫn là quyết định của Owner, không phải của phiên này.

### FIND-RDA-02 — Một dòng mang review reason `Suspicious`
Classification: `NON_BLOCKING`. Xuất hiện đồng nhất ở cả oracle pipeline lẫn
kết quả đã lưu; là tín hiệu review nghiệp vụ bình thường, không phải vấn đề
của tầng persistence. Không mở audit mới.

### Không có defect production
Workbook thật KHÔNG làm production-equivalent path fail ở bất kỳ bước nào.
`BLOCKING_PRODUCTION_DEFECT` = KHÔNG CÓ.

## 15. CODE_REQUIRED

```text
CODE_REQUIRED         = NO
PRODUCTION_CODE_ADDED = 0 dòng
CHANGE_BUDGET_STATE   = 1.460 / 1.500  REMAINING = 40  (KHÔNG đổi)
CHANGE_BUDGET_REQUIRED = NO
```

## 16. Trạng thái check

```text
CHECK-PRA002-14 = NOT_TESTED (giữ nguyên — hợp đồng frozen đòi ĐỦ bảng mục 15)
                  RDA-1 = PASS (E1, dữ liệu thật, PostgreSQL 16.13)
                  RDA-2 = PASS (E1, dữ liệu thật, PostgreSQL 16.13)
                  RDA-3 = BLOCKED_OWNER_INPUT (cần export thật thứ hai; đường
                          controlled copy bị loại khỏi phạm vi phiên này)
                  RDA-4 = BLOCKED_OWNER_INPUT — SOURCE_CHANGED
                          NOT_OBSERVED_IN_REAL_DATA (một workbook không đổi
                          không thể tự sinh SOURCE_CHANGED thật)
                  RDA-5 = BLOCKED_OWNER_INPUT (cần drop-line + xác nhận đủ)
                  RDA-6 = PARTIAL — Golden 58 passed/2 skipped PASS;
                          cohort S068 NOT_TESTED (không có trong môi trường)

CHECK-PRA002-15 = NOT_TESTED (không đổi — Owner deploy Render; phiên không có
                  egress tới Render; phiên này KHÔNG deploy)
```

## 17. Owner input còn cần

```text
OWNER_CONFIRMATION_REQUIRED = YES (chỉ khi Owner muốn đóng RDA-5)
  SNAPSHOT_ID = SNAP-20260902154531-e1c6cec2
  RANGE       = 2026-09-01 .. 2026-09-01
  Phiên này KHÔNG POST xac-nhan-du. Không tự xác nhận thay Owner.

OWNER_SECOND_FILE_REQUIRED = YES (cho RDA-3, đường ưu tiên của mục 15)
  REQUIREMENT = một export THẬT khác của cùng phần mềm kế toán, chứa TRỌN
  ngày 2026-09-01 và rộng hơn — ví dụ export nhiều ngày (2026-09-01 .. 2026-09-05)
  hoặc cả tháng 9/2026 — sao cho A ⊂ B. Một export cùng phạm vi một ngày
  nhưng lấy ở thời điểm muộn hơn cũng dùng được nếu trong khoảng đó có
  phát sinh/sửa chứng từ.
  Thay thế: Owner cho phép đường controlled copy (ASSUMPTION D14,
  `tools/analysis/make_snapshot_variants`) mà hợp đồng frozen đã cho phép —
  phiên này bị chỉ thị loại trừ nên không dùng.
```

## 18. Không làm trong phiên này

Không production code · không migration · không schema · không sửa Tracking ·
không `make_snapshot_variants` · không parser expansion · không refactor ·
không hardening · không PRA-003+ · không A2/A3/B2/B3/B4 · không REM-T06 ·
không deploy production · không POST `xac-nhan-du`.
