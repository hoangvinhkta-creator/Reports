# BÀN GIAO SESSION (SESSION HANDOFF)

Session ID:
S080

Task:
TASK-PRA-002 — Slice A (Persistence + Core Reconciliation)

Task Mode:
MAJOR (implementation)

Project Profile:
PRODUCT

Status:
IMPLEMENTED — slice A hoàn tất, chờ Independent Review E2 trước Controlled
Integration. `TASK-PRA-002` tổng thể VẪN đang implementation (slice B và C
chưa làm).

## Thẩm Quyền Git (Git Authority)

```
Repo                        : hoangvinhkta-creator/Reports
Nhánh canonical (origin HEAD): claude/extract-upload-repo-gq2ws4
IMPLEMENTATION_BASE_SHA     : 7fad3f76908d6d56114a5e2e947d83e15f8eda02
origin/canonical lúc mở phiên: 7fad3f76908d6d56114a5e2e947d83e15f8eda02  (KHỚP — canonical không dịch chuyển)
Nhánh làm việc              : claude/pra-002-slice-a-umygjq  (cắt từ đúng SHA trên)
Worktree lúc mở phiên       : CLEAN
scripts/branch_authority_check.sh : AUTHORITY_OK (BRANCH_WITH_UPSTREAM, DIVERGENCE = WITHIN_LIMITS)
Tracking                    : KHÔNG đọc, KHÔNG sửa — TRACKING_CHANGED = NO
```

Không dùng `main`. Không rebase. Không force push.

## Phạm Vi Đã Làm (Slice A) — và phạm vi CỐ Ý chưa làm

Vertical bắt buộc đã chạy end-to-end:

```
pipeline authoritative → structured output (DemoRun.presented_lines)
 → PostgreSQL/SQLite persistence → source reconciliation
 → INSERT / SAME / SOURCE_CHANGED / ORDER_KEY_COLLISION
 → result version → current pointer → query/reload
```

KHÔNG làm (đúng exclusion của chỉ thị phiên và mục 20 của task):

- Slice B: bước 4 `NOT_SEEN_IN_LATEST_SNAPSHOT`, bước R
  `REMOVED_IN_SOURCE_CANDIDATE`, `POST /du-lieu/snapshot/<id>/xac-nhan-du`,
  mọi đường nâng coverage lên `CONFIRMED_COMPLETE`. Cột và CHECK constraint
  của `CONFIRMED_COMPLETE` ĐÃ có trong schema (để slice B không phải đổi
  migration), nhưng slice A **không có đường nào** ghi ra giá trị đó — có
  test khẳng định điều này.
- Slice C: cờ `RESULT_REVISED`. `result_fingerprint` (3 trường theo F3) ĐÃ
  được tính và lưu trên mỗi result version — đó là dữ liệu slice C cần —
  nhưng KHÔNG có logic nào dựng cờ từ nó ở slice A.
- Không PRA-003/004/005, không legacy detail import.

## Migration

```
Chain      : 0001_legacy → 0002_snapshots        (down_revision = 0001_legacy)
ALEMBIC_HEAD: "0002_snapshots" (tools/db/__init__.py)
Tính chất  : ADDITIVE thuần — không đổi một cột nào của 4 bảng legacy_*, không backfill
Bảng thêm  : source_snapshot, order_line_source_version, snapshot_line,
             order_line_result_version, order_line_current, reconciliation_flag
DDL        : sinh từ chính schema.METADATA (nguồn DDL duy nhất, dùng chung với repository)
```

Bằng chứng SQLite (E1):

```
$ HISTORY_DATABASE_URL=sqlite:///$T/h.db python3 -m alembic upgrade head
$ python3 -c "... inspect ..."
['alembic_version', 'legacy_daily_sales', 'legacy_import', 'legacy_monthly_reference',
 'legacy_summary_row', 'order_line_current', 'order_line_result_version',
 'order_line_source_version', 'reconciliation_flag', 'snapshot_line', 'source_snapshot']
0002_snapshots
$ python3 -m alembic downgrade 0001_legacy
['alembic_version', 'legacy_daily_sales', 'legacy_import', 'legacy_monthly_reference',
 'legacy_summary_row']
0001_legacy
```

Bằng chứng PostgreSQL 16.13 local (E1) — nâng cấp trên database ĐANG CÓ dữ
liệu legacy:

```
$ python3 -m alembic upgrade 0001_legacy
$ psql -c "INSERT INTO legacy_import (...) VALUES ('LEG-PG-TEST','LEGACY_REFERENCE','pgfp1',false);"
INSERT 0 1
$ python3 -m alembic upgrade head
$ psql -tAc "SELECT version_num FROM alembic_version;"
0002_snapshots
$ psql -tAc "SELECT import_id, file_fingerprint FROM legacy_import;"
LEG-PG-TEST|pgfp1                      <-- dòng legacy NGUYÊN VẸN sau migration
$ psql -tAc "SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY 1;"
alembic_version, legacy_daily_sales, legacy_import, legacy_monthly_reference,
legacy_summary_row, order_line_current, order_line_result_version,
order_line_source_version, reconciliation_flag, snapshot_line, source_snapshot
```

`assert_schema_current` vẫn fail-closed theo revision (test
`test_schema_check_rejects_an_out_of_date_revision` PASS với head mới).
Không có đường auto-create schema ngoài Alembic (`create_all_for_test` chỉ
dùng trong test, không được app gọi).

## Bằng Chứng Vertical (E1)

### INSERT — một upload thật, fixture golden `period_2026_01.xlsx`

```
line_count = 351   order_count = 254   sheet_data_rows = 352   rows_without_order_id = 1
coverage_state = HEADER_CONSISTENT
header_text = "Nhân viên: Tín Phát 0869931931, Tháng 1 năm 2026"
detected 2026-01-02 → 2026-01-31   header 2026-01-01 → 2026-01-31
order_line_source_version = 351 (mọi dòng version_no = 1)
order_line_result_version = 351      order_line_current = 351
SUM(current total_sales) = 3.562.310.000
  == money.sales_normalized của tests/fixtures/golden/expected/period_2026_01.json
COUNT(status = 'PENDING') = 349 == ReportSummary.review_lines
```

`sheet_data_rows`/`rows_without_order_id` được đếm bằng một lượt đọc
`read_only` ĐỘC LẬP với `read_raw_rows` — trùng đúng con số của Golden
(`DOCUMENTED["01.2026"]`: 352 / 1).

### SAME — upload lại đúng file, KHÔNG double-count

```
snapshot #2: n_same = 351, n_insert = 0, duplicate_of_snapshot_id = snapshot #1
COUNT(order_line_source_version)        = 351   (KHÔNG tăng)
COUNT(version_no > 1)                   = 0
COUNT(order_line_current)               = 351   (KHÔNG tăng)
SUM(current total_sales)                = 3.562.310.000  (KHÔNG đổi, tới từng đồng)
COUNT(order_line_result_version)        = 702   (run mới ghi result mới — audit tăng, nghiệp vụ không)
COUNT(reconciliation_flag SOURCE_CHANGED) = 0
```

### Đẳng thức A→B == B (fixture cắt từ golden trong tmp, KHÔNG commit)

```
snapshot A = golden cắt tới <= 10/01  →  89 dòng / 61 đơn   (đo từ chính fixture)
snapshot B = golden nguyên bản        →  351 dòng / 254 đơn

A rồi B : n_insert = 262, n_same = 89, n_source_changed = 0, n_collision = 0
          COUNT(order_line_source_version) = 351
state(A rồi B) == state(B trên DB sạch):
          cùng current_totals (lines 351, orders 254, total_sales 3.562.310.000)
          cùng TẬP (khoá → line_fingerprint) — so bằng đẳng thức, không bằng con số tổng
Đảo thứ tự (B rồi A): n_same = 89, n_insert = 0, n_source_changed = 0, tổng KHÔNG đổi
```

Kiểm lại trên PostgreSQL 16 thật (A → A → B → B'):

```
pg-a1  a.xlsx               INSERT 89                current 89/61   804.980.000   sv=89  (v>1: 0) rv=89
pg-a2  a.xlsx               SAME 89, INSERT 0        current 89/61   804.980.000   sv=89  (v>1: 0) rv=178
pg-b1  period_2026_01.xlsx  INSERT 262, SAME 89      current 351/254 3.562.310.000 sv=351 (v>1: 0) rv=529
pg-b2  b_edited.xlsx        SAME 350, SOURCE_CHANGED 1
                                                     current 351/254 3.563.310.000 sv=352 (v>1: 1) rv=880
B một mình trên PG sạch   : current 351/254 3.562.310.000, 351 khoá   <-- đẳng thức khớp
```

### SOURCE_CHANGED — sửa đúng một dòng

```
n_source_changed = 1, n_insert = 0
version_no của khoá đó : [1, 2]   (version 1 đọc lại nguyên văn, changed_fields_json = NULL)
changed_fields_json v2 : {"sell_price": {"new": "8500000", "old": "7500000"},
                          "total_sales_raw": {"new": "8500000", "old": "7500000"}}
cờ SOURCE_CHANGED      : from_version_id → to_version_id đúng cặp version
current_source_version_id = version 2
SUM(total_sales) đổi ĐÚNG delta = +1.000.000; số dòng hiện hành KHÔNG đổi
Đổi PII (customer/phone/address/shipper) trên một dòng → SAME, 0 cờ (test tham số hoá)
```

### ORDER_KEY_COLLISION — fail-safe, không đoán

```
Cùng Số BH, ngày bán lệch 91 ngày (> ngưỡng 90):
  outcome = ORDER_KEY_COLLISION   snapshot_line.outcome = ORDER_KEY_COLLISION
  version mới ĐƯỢC ghi (không mất bản ghi) nhưng KHÔNG trở thành current
  order_line_current.sale_date giữ nguyên bản cũ; order_key_collision = TRUE
  KHÔNG có result version nào được gắn cho khoá tranh chấp
  cờ ORDER_KEY_COLLISION với detail_json {current_sale_date, incoming_sale_date,
                                          day_gap: 91, threshold_days: 90}
Đúng ngưỡng 90 ngày  → vẫn reconcile bình thường (SOURCE_CHANGED)
Một bên thiếu ngày   → KHÔNG bao giờ thành collision (thiếu ngày ≠ cách xa nhau)
```

### RESULT VERSION

Mỗi run ghi ĐÚNG một result version cho mỗi khoá của snapshot (trừ khoá
COLLISION), kể cả dòng `SAME` — pipeline đã chạy lại thật với bằng chứng của
lần đó, không "copy" kết quả cũ. `UNIQUE (run_id, khoá)` chặn một run ghi hai
result cho một khoá. `result_fingerprint` = sha256(status,
accounting_purchase_price, eligible_kpi_profit) — đúng 3 trường F3, đã lưu
nhưng CHƯA có logic sinh cờ (slice C).

### CURRENT POINTER

```
PK (order_key, product_key, occurrence_index) → hai current cho một khoá là
BẤT KHẢ THI ở tầng schema, không chỉ ở tầng query (có test khẳng định PK).
Analytics hiện hành = JOIN order_line_current ↔ current_result_version
  → mỗi khoá góp đúng MỘT lần theo cấu trúc bảng, không nhờ DISTINCT.
Query/reload proof: sau 2 version trên cùng một khoá →
  COUNT(order_line_source_version) = 2  (lịch sử)
  current_totals()["lines"]        = 1  (hiện hành)
  → lịch sử nguồn ≠ trạng thái hiện hành, đúng như hợp đồng đòi.
Repository dựng MỚI đọc lại đúng trạng thái đó từ database (không giữ state
trong tiến trình).
```

### FAIL-CLOSED / MỘT ĐƠN VỊ CÔNG VIỆC

```
(a) ghi lịch sử lỗi        → HTTP 500, 0 run trong store, 0 snapshot
(b) store.create_run lỗi   → rollback: 0 snapshot, 0 source version, 0 run
(c) dev không history store→ /run vẫn 302, trang kết quả nói thẳng
                             "Run này KHÔNG được lưu lịch sử — history store chưa cấu hình"
(d) run có mà snapshot không → tab Dữ liệu gắn nhãn "KHÔNG CÓ LỊCH SỬ (ghi lỗi)"
(e) REPORTS_REQUIRE_HISTORY_DB=1 thiếu URL → không khởi động (test cũ giữ PASS)
```

### APPEND-ONLY / CONCURRENCY

```
Tĩnh (AST, không grep chuỗi): 0 lời gọi delete() trong history_store.py và
  history_writer.py; `delete` thậm chí không được import từ sqlalchemy.
  update() chỉ trên {legacy_import (PRA-001), order_line_current}.
Hành vi : 3 snapshot liên tiếp trên cùng một khoá → version_no [1,2,3],
  đọc lại đủ [8.000.000, 9.000.000, 10.000.000]; đúng 1 dòng hiện hành.
Concurrency: INSERT thứ hai cùng (khoá, version_no=1) → IntegrityError,
  rollback, DB còn đúng 1 version. Fail-safe bằng UNIQUE + transaction,
  KHÔNG distributed locking.
```

### PII

```
Tập cột của 6 bảng PRA-002 ∩ {customer, customer_code, phone, address,
shipper_raw} = ∅ (test duyệt schema.METADATA).
SourceLine/ResultLine không mang trường PII nào (test repr).
changed_fields / detail_json không chứa khoá PII.
Trang /du-lieu/snapshot/<id> không render PII (test grep HTML response với 5
giá trị PII giả đặt trong fixture).
line_fingerprint bền với mọi thay đổi PII (test tham số hoá 8 trường).
```

## Kết Quả Test

```
$ python3 -m pytest -q
1710 passed, 11 skipped in 61.30s

$ python3 -m pytest -q tests/test_golden_baseline.py
58 passed, 2 skipped                      <-- KHÔNG đổi so với baseline

$ python3 -m pytest -q tests/test_legacy_repository.py tests/test_legacy_importer.py \
      tests/test_legacy_source_coverage.py tests/test_history_db.py
81 passed                                 <-- PRA-001 regression PASS
```

Baseline tại BASE_SHA: `1608 passed, 11 skipped`. Sau slice A: `1710 passed,
11 skipped` → **+102 test mới, 0 test bị xoá/làm yếu, số skip KHÔNG tăng**.

Bốn guard test của `tests/test_history_db.py` được CẬP NHẬT (không xoá) đúng
như task quy định, và thêm một test mới:

- `test_migration_chain_is_exactly_the_two_frozen_revisions` — chain = `0001_legacy`, `0002_snapshots`.
- `test_schema_declares_exactly_the_frozen_legacy_and_pipeline_tables` — METADATA = 4 legacy + 6 PRA-002.
- `test_migration_upgrade_then_downgrade_round_trips` — round-trip với 10 bảng.
- `test_schema_check_rejects_an_out_of_date_revision` — so với `ALEMBIC_HEAD` thay vì chuỗi cứng.
- MỚI: `test_migration_0002_is_additive_and_leaves_legacy_rows_untouched`.

`ru_maxrss` end-to-end `/run` (app boot + upload golden 351 dòng + writer,
SQLite): **75,6 MB** (app boot: 64,2 MB). Mục tiêu < 300 MB; baseline S078R
legacy 81,9 MB. Kịch bản A→A→B→B' trên PostgreSQL: 78,7 MB.

## Change Budget

```
PRODUCTION PYTHON (dòng logic, bỏ trống/comment/docstring)
  +177  tools/db/schema.py
    +0  tools/db/__init__.py                (đổi 1 hằng ALEMBIC_HEAD)
   +12  tools/db/migrations/versions/0002_snapshots.py
    +2  app/history/__init__.py
   +47  app/history/keys.py
  +102  app/history/models.py
   +72  app/history/coverage.py
   +45  app/history/reconciler.py
   +69  app/history/extraction.py
  +407  app/web/history_store.py
   +94  app/web/history_writer.py
   +47  app/web/server.py
    +4  app/demo.py
    +2  app/modules/exporting/excel_exporter.py
 +1080  TỔNG        → mục tiêu ≤ 1.200 ĐẠT; dừng cứng 1.500 KHÔNG chạm

TEMPLATE  +137 dòng không trống (≤ 250 ĐẠT)
TEST      +1.018 dòng logic, +102 test (yêu cầu ≥ 40 ĐẠT)
Dependency mới: KHÔNG (sqlalchemy/alembic/openpyxl đều đã có)
```

`app/demo.py`: +7/−2 dòng thô (net +5, mục tiêu ≤ 6 ĐẠT).
`app/modules/exporting/excel_exporter.py`: 5 dòng thêm, trong đó **3 dòng
không trống** (2 alias + 1 comment) và 2 dòng trống phân cách bắt buộc theo
PEP8. Phần alias thực = 2 dòng. Mục tiêu "≤ 4 dòng" ĐẠT theo dòng không
trống; ghi rõ con số thô ở đây để không phải suy đoán.

## Đăng Ký File Đã Thay Đổi

Created:
- `app/history/__init__.py`, `keys.py`, `models.py`, `coverage.py`, `reconciler.py`, `extraction.py`
- `app/web/history_writer.py`
- `app/web/templates/snapshot.html`
- `tools/db/migrations/versions/0002_snapshots.py`
- `tests/test_history_keys.py`, `test_history_reconciler.py`,
  `test_snapshot_repository.py`, `test_pipeline_history_vertical.py`,
  `test_web_history.py`
- `docs/sessions/S080-pra-002-slice-a-implementation.md`

Modified:
- `tools/db/schema.py` (+6 bảng), `tools/db/__init__.py` (`ALEMBIC_HEAD`)
- `app/web/history_store.py` (+`SnapshotRepository`, +`build_snapshots`, + property `engine`)
- `app/web/server.py` (`run_report` một đơn vị công việc, `/du-lieu` + snapshot list,
  `GET /du-lieu/snapshot/<id>`, `_build_snapshots`)
- `app/web/templates/du_lieu.html`, `app/web/templates/index.html`
- `app/demo.py` (+2 trường `DemoRun`), `app/modules/exporting/excel_exporter.py` (alias)
- `tests/test_history_db.py` (4 guard cập nhật + 1 test mới)
- `PROJECT/PROJECT_PROGRESS.md`, `PROJECT/REVIEW_BUDGET_LEDGER.md`,
  `docs/tasks/TASK-PRA-002-pipeline-persistence-reconciliation.md`,
  `docs/deployment/S071_DEPLOYMENT.md`

Deleted: (không)

## Kiểm Tra Phạm Vi (Scope Check)

`git diff --name-only BASE..HEAD` KHÔNG chứa: `app/pipeline.py`,
`app/composition.py`, `app/owner_usability.py`, `app/owner_launcher.py`,
`app/web/storage_backend.py`, `app/web/run_registry.py`, `tools/storage/**`,
`tools/tracking/**`, `config/**`, `data/**`, `tests/fixtures/**`,
`app/legacy/**`, `render.yaml`, `Dockerfile`. Bốn bảng `legacy_*` không đổi
một cột nào. `TRACKING_CHANGED = NO`.

`git diff` của `app/modules/**` = ĐÚNG 3 dòng thêm, toàn bộ là alias +
comment:

```
+# Alias public: cùng object đã in ra XLSX — không có nguồn sự thật thứ hai.
+PresentedLine = _PresentedLine
+present_lines = _present_lines
```

`git diff --check` = sạch.

**Một sai lệch nhỏ so với Expected Touch Area, ghi tường minh:**
`app/web/templates/index.html` (+3 dòng) KHÔNG có trong danh sách Allowed của
task, nhưng cũng KHÔNG nằm trong danh sách "Không được đụng". Nó cần thiết để
thoả CHECK-PRA002-10 (c) — "trang [kết quả] hiển thị *KHÔNG được lưu lịch
sử*". Ba dòng đó chỉ thêm một câu cảnh báo có điều kiện, không đổi luồng nào.
Đây là điều Independent Reviewer cần biết, nên nó được ghi ở đây thay vì im
lặng.

## Findings

Không có finding BLOCKING (production path + business consequence + evidence).

Đã DEFER, đúng chính sách finding của phiên:

- **3 vấn đề reference-integrity của REM-T06** — pre-existing, không thuộc
  slice này, KHÔNG sửa.
- **Phase D — public ingress `0.0.0.0/0` của `tinphat-reports-db`** —
  OPEN/PENDING, không thuộc implementation slice A, không chặn.
- **Thứ tự hiển thị snapshot cùng giây** — `list_snapshots` sắp xếp theo
  `(created_at DESC, snapshot_id DESC)`. Hai snapshot của HAI file khác nhau
  tạo trong CÙNG một giây có thứ tự hiển thị theo `snapshot_id`, không theo
  thứ tự chèn. Không ảnh hưởng số liệu (mọi phép tính đi qua khoá, không qua
  thứ tự); một lần upload của người thật cách nhau hơn một giây. DEFER —
  re-trigger nếu UI cần thứ tự chèn chính xác (PRA-003).
- **`scan_workbook` nuốt lỗi đọc header** → `(None, 0, 0)` và coverage rơi về
  `DETECTED_ONLY`. Cố ý: một lần chạy pipeline ĐÃ thành công không được hỏng
  vì đọc lại ô A2 lỗi. Trung thực (không đoán header), fail-safe, và
  `sheet_data_rows = 0` là dấu hiệu nhìn thấy được trên trang snapshot.

## Trạng Thái Completion Gate Sau Slice A

| Check | Trước | Sau slice A | Ghi chú |
|---|---|---|---|
| CHECK-PRA002-01 | NOT_TESTED | **PASS (E1)** | up/down SQLite + PG 16 thật + legacy nguyên vẹn + fail-closed revision |
| CHECK-PRA002-02 | NOT_TESTED | **PASS (E1)** | 351/254/1, tổng = 3.562.310.000, PENDING = review_lines |
| CHECK-PRA002-03 | NOT_TESTED | **PASS (E1)** | n_same = 351, 0 version mới, tổng không đổi, result = 702 |
| CHECK-PRA002-04 | NOT_TESTED | **PASS (E1)** | 89/262, đẳng thức state(A,B) == state(B), đảo thứ tự OK |
| CHECK-PRA002-05 | NOT_TESTED | **PASS (E1)** | changed_fields đúng 2 trường, version cũ nguyên vẹn, delta đúng |
| CHECK-PRA002-06 | NOT_TESTED | **PARTIAL** | DETECTED/HEADER + "không đường nào đặt CONFIRMED_COMPLETE" đã kiểm; phần xác nhận tường minh = slice B |
| CHECK-PRA002-07 | NOT_TESTED | NOT_TESTED | slice B |
| CHECK-PRA002-08 | NOT_TESTED | NOT_TESTED | slice C |
| CHECK-PRA002-09 | NOT_TESTED | **PASS (E1)** | AST append-only, 3 snapshot, UNIQUE concurrency |
| CHECK-PRA002-10 | NOT_TESTED | **PASS (E1)** | (a)–(e) đều có test |
| CHECK-PRA002-11 | NOT_TESTED | **PASS (E1)** | Golden 58/2; full 1710 (≥1608), skip không tăng; alias `is`; diff modules = 3 dòng |
| CHECK-PRA002-12 | NOT_TESTED | **PASS (E1)** | app/history sạch sqlalchemy/psycopg/alembic/flask; scope audit; AUTHORITY_OK |
| CHECK-PRA002-13 | NOT_TESTED | **PASS (E1)** | schema, changed_fields, HTML response |
| CHECK-PRA002-14 | NOT_TESTED | NOT_TESTED | Real Data Acceptance — không có workbook thật trong session; gate Owner |
| CHECK-PRA002-15 | NOT_TESTED | NOT_TESTED | Production Acceptance — Owner, sau Controlled Integration |
| CHECK-PRA002-16 | NOT_TESTED | **PASS (E1, RECOMMENDED)** | 75,6 MB < 300 MB |
| CHECK-PRA002-17 | NOT_TESTED | NOT_TESTED | Independent Review E2 — bước tiếp theo |

Không check REQUIRED nào bị xoá hay làm yếu. `TASK-PRA-002` KHÔNG được đánh
dấu DONE.

## Hành Động Tiếp Theo (NEXT_VERTICAL_ACTION)

**Independent Review E2 cho slice A trước Controlled Integration.** Reviewer
chạy lại độc lập CHECK-03/04/05/09 (và phần đã PASS của 01/02/10/11/12/13),
theo `governance/templates/E2_INDEPENDENT_REVIEW_TEMPLATE.md`, ghi vào
`docs/reviews/TASK-PRA-002-INDEPENDENT-REVIEW-RECORD`. Ngân sách repair: 2
cycle, đã dùng 0.

KHÔNG bắt đầu slice B trong phiên này.
