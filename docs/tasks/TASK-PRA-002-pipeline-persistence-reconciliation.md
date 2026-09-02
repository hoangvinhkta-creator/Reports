# TASK-PRA-002 — Pipeline Persistence + Overlapping Snapshot Reconciliation

## Metadata
Status:
IN_PROGRESS

Phase:
PHASE-PRA — Slice 2 (nền dữ liệu cho PRA-003/004/005)

Task Mode:
MAJOR

Primary Agent Tier:
Tier C (data integrity; blast radius theo failure path = sai tổng doanh
thu/đơn → sai KPI/lương)

Escalation Tier:
Owner (mọi business semantics: ý nghĩa huỷ/hoàn, BH reset theo năm, PII
drill-down); Independent Reviewer E2 theo
`governance/templates/E2_INDEPENDENT_REVIEW_TEMPLATE.md`

Difficulty:
4/5

Risk:
4/5

Blast Radius:
4/5 — failure path: (a) một dòng bán được đếm hai lần vì upload hai
snapshot chồng kỳ → doanh thu/đơn/LN KPI tháng sai → lương/thưởng sai;
(b) một dòng bị âm thầm mất khi snapshot mới thiếu nó → thiếu doanh thu;
(c) source version bị ghi đè tại chỗ → mất bằng chứng kế toán đã sửa gì.
Không chạm business rule của pipeline (Product Identity, PP,
PricingEffectiveDate, Accounting reconciliation, AUTO/Pending) — tầng lưu
chỉ ghi lại engine đã quyết gì, với evidence nào.

Project Profile:
PRODUCT

Root task lineage (V4.1): `TASK-PRA-002` (root mới, không kế thừa ngân
sách lineage nào). Review budget: **HIGH = 2 blocking repair cycles**
(`governance/core/V4_1_POLICY_FREEZE.md` §2). Ledger:
`PROJECT/REVIEW_BUDGET_LEDGER.md` → "Root Task: TASK-PRA-002".

Kế hoạch gốc: `docs/tasks/TASK-PRA-000-persistent-reporting-analytics-plan.md`
(mục H, I, J, K; phụ lục F3 FINALIZED_RECONCILIATION_POLICY, F4, F6).
Quyết định nền: DEC-166 (B/C/D), DEC-167 + `docs/adr/ADR-108-persistent-history-store.md`
(Accepted), DEC-170 (`HISTORY_DATABASE_URL`), DEC-171 (quyết định chiến
thuật của phiên finalization S079). Nền kỹ thuật kế thừa:
`docs/tasks/TASK-PRA-001-legacy-reference-vertical.md` (DONE).

Finalization session: S079 (2026-09-02) —
`docs/sessions/S079-pra-002-roadmap-finalization.md`.
`BASE_SHA = 553d8a36f578b082128a6e45d2748da2bc371e70` (HEAD nhánh canonical
`claude/extract-upload-repo-gq2ws4` lúc freeze).

Quy ước: file DỰ KIẾN tạo được viết KHÔNG kèm phần mở rộng (ví dụ
`app/history/reconciler`); file đã tồn tại viết đủ đường dẫn (ví dụ
`app/web/history_store.py`).

Quy ước phân loại mọi rule quan trọng trong tài liệu này:
`FACT` (đo được trong repo/dữ liệu) · `OWNER_DECISION` (Owner đã chốt, có
DEC) · `INFERENCE` (suy từ code/evidence, là implementation evidence chứ
không phải business authority) · `ASSUMPTION` (chưa verify) · `UNKNOWN`.

---

## Mục Tiêu (Objective) — (1) Goal

Owner upload sổ kế toán thô (`So_chi_tiet_ban_hang.xlsx`) nhiều lần với
khoảng ngày chồng nhau (ví dụ 01/09–10/09 rồi 01/09–30/09); Reports chạy
đúng pipeline authoritative hiện có, **ghi lại kết quả vào PostgreSQL**
(origin `PIPELINE_GENERATED`), **đối chiếu với các snapshot trước theo
khoá đơn/dòng**, và trả lời được:

- trạng thái hiện hành của từng đơn/dòng là gì (một khoá → đúng một source
  version current, đúng một result version current);
- dòng nào mới, dòng nào không đổi, dòng nào kế toán đã sửa (sửa trường
  nào, từ gì sang gì, ở snapshot nào), dòng nào không còn thấy;
- tổng đơn/doanh thu/LN KPI theo kỳ **không đếm trùng** dù upload bao
  nhiêu lần;
- lịch sử truy ngược được tới snapshot nguồn, run, evidence Tracking.

Không xây dashboard (PRA-003), không xây màn Bán hàng/Review Ops (PRA-004),
không xây Product analytics (PRA-005).

## Ngoài Phạm Vi (Out of Scope) — (2) Non-goals

- Tổng quan/KPI kỳ/so kỳ trước/target (PRA-003). Bán hàng drill-down,
  Review Queue trên web, nút "đã xem"/acknowledge, phân xử
  `REMOVED_CANDIDATE` (PRA-004). Sản phẩm canonical (PRA-005).
- Persist PII: `customer`, `phone`, `address`, `shipper_raw`, `customer_code`
  KHÔNG vào bất kỳ bảng PRA-002 nào (xem mục "Provenance & PII"; N.5 của
  PRA-000 DEFER sang PRA-004 khi drill-down thực sự cần).
- `order_source_version` cấp đơn, `review_item` persist, coverage calendar
  UI, diff UI giữa hai snapshot, retention/xoá snapshot, `uploaded_by`,
  multi-file batch upload, `pg_dump` lên R2, dark mode/mobile.
- Namespace `order_key` theo năm (F4): chỉ giữ đường nâng cấp bằng cột
  `bh_number` + `bh_year_hint`; KHÔNG investigation, KHÔNG migration
  namespace, KHÔNG reconcile xuyên năm.
- Anomaly detection, realtime, payroll, inventory, rare identity discovery,
  speculative refactor, generic data platform, event-sourcing framework,
  queue/microservice/Firebase/hạ tầng mới, database trả phí mới, nâng
  compute Render (512 MB đủ — Owner đã chốt sau S078R).
- Mọi thay đổi business rule trong `app/modules/**` (trừ đúng một alias
  public trong exporter — xem Touch Area), `app/pipeline.py`,
  `app/composition.py`, `RunStore`/R2, Tracking.

---

## (3) Owner Business Contract

### 3.1 Kịch bản bắt buộc (OWNER_DECISION — chỉ thị S079, khớp DEC-166 B/C/D)

```text
Ngày 10/09: Owner upload workbook chứa 01/09–10/09  → SNAP-A
Ngày 30/09: Owner upload workbook chứa 01/09–30/09  → SNAP-B
Hệ thống KHÔNG được tính 01/09–10/09 hai lần.
```

### 3.2 Bảng contract reconcile (OWNER_DECISION — Owner chấp nhận nguyên văn tại S079)

| Kết quả | Điều kiện | Hành vi bắt buộc |
|---|---|---|
| `INSERT` | khoá chưa tồn tại | source version 1; current trỏ tới |
| `SAME` | cùng khoá, `line_fingerprint` không đổi | KHÔNG tạo source version mới; KHÔNG double-count; ghi membership snapshot |
| `SOURCE_CHANGED` | cùng khoá, fingerprint đổi | source version n+1; ghi `changed_fields` + provenance; giữ version cũ; version mới = current candidate |
| `REMOVED_CANDIDATE` | snapshot mới `CONFIRMED_COMPLETE` VÀ khoá current có ngày ∈ coverage đã xác nhận KHÔNG xuất hiện trong snapshot mới | vào Review (cờ); KHÔNG xoá historical record; VẪN current, VẪN tính analytics cho tới khi được xử lý |
| `NOT_SEEN_IN_LATEST_SNAPSHOT` | như trên nhưng snapshot mới CHƯA `CONFIRMED_COMPLETE` | chỉ thông tin; KHÔNG suy diễn đơn bị xoá/huỷ |
| `RESULT_REVISED` | source version không đổi, evidence Reports đổi → status AUTO/PENDING, `accounting_purchase_price` hoặc `eligible_kpi_profit` khác run trước | result version mới; KHÔNG phải source conflict |

SOURCE VERSION và RESULT VERSION là hai trục **tách riêng** (bảng riêng,
khoá riêng, cờ riêng).

### 3.3 Coverage (OWNER_DECISION — DEC-166 B + chỉ thị S079)

Ba mức: `DETECTED_ONLY` → `HEADER_CONSISTENT` → `CONFIRMED_COMPLETE`.
Chỉ **explicit user confirmation** mới nâng lên `CONFIRMED_COMPLETE`.
min/max ngày hoặc "nhìn thấy ngày cuối tháng" KHÔNG đủ để chứng minh
complete.

### 3.4 Data origin & authority (OWNER_DECISION — DEC-166 E, ADR-107/108, chỉ thị S079)

- `LEGACY_REFERENCE` (PRA-001) và `PIPELINE_GENERATED` (PRA-002) không bao
  giờ trộn; không view nào `UNION` hai origin thành một con số không nhãn.
- Raw accounting workbook = authoritative sales source; sale date = cột
  `Ngày`; `PricingEffectiveDate` = sale date (đã là hành vi engine —
  FACT). Tracking = Product Identity Authority + Public Purchase authority
  (chỉ tham chiếu bằng capture id/revision — không mirror).
- Không backfill/extrapolate PP; không fuzzy identity; không sửa protected
  core.

### 3.5 Phân loại các rule còn lại

| Rule | Loại | Căn cứ |
|---|---|---|
| `ORDER_KEY` = `order_id` của engine (Số BH sau `NFC + strip`, KHÔNG upper/bỏ khoảng trắng thêm) | INFERENCE (đồng nhất với engine) + OWNER_DECISION (candidate `normalize(BH)`, DEC-166) | `app/modules/importing/raw_reader.py::_normalize_text`, `app/modules/orders/order_builder.py` nhóm theo `order_id`. Chuẩn hoá thêm sẽ tạo khoá lưu trữ KHÁC khoá engine → hai "sự thật". Ghi ở DEC-171 |
| `ORDER_LINE_KEY = (ORDER_KEY, product_key, occurrence_index)` | OWNER_DECISION (candidate, DEC-166) + FACT (exporter đã ghép record theo `(order_id, product_raw, date)` + thứ tự xuất hiện) | `app/modules/exporting/excel_exporter.py::_present_lines` dùng `deque.popleft` |
| `product_key = sha256(product_raw đã NFC+strip; "" nếu None)` — không casefold | INFERENCE | cùng lý do với ORDER_KEY; casefold DEFER |
| `occurrence_index` = thứ tự xuất hiện (1..n) của `product_key` trong đơn, theo `source_row` tăng dần | INFERENCE | fixture golden: 0 cặp `(order, product)` lặp (đo S079); dữ liệu thật 6 tháng có dòng "Chi phí vận chuyển" lặp (PRA-000 I.1) → cần index |
| `line_fingerprint` = sha256 của bộ trường nguồn nghiệp vụ (xem 5.2) | INFERENCE | PRA-000 I.2 + bổ sung `source_profit` (trường nguồn của kế toán) |
| Guard `ORDER_KEY_COLLISION` (cùng BH, lệch ngày > 90) | INFERENCE (fail-safe) | PRA-000 I.2/F3; bảo vệ khỏi UNKNOWN BH reset — không SAME/CHANGED nhầm |
| BH reset theo năm | UNKNOWN | N.13; `OWNER_CONFIRMATION_REQUIRED_BEFORE = reconcile xuyên năm` |
| Export ERP cho kỳ ngắn hơn chứa ĐÚNG tập dòng con của export kỳ dài hơn (khi kế toán không sửa) | ASSUMPTION | chỉ có fixture export theo tháng; RDA-3 kiểm bằng hai export thật của Owner |
| Header dòng 2 có hai dạng đã biết: `Từ ngày dd/mm/yyyy đến ngày dd/mm/yyyy` (file production, `docs/analysis/01_DATA_MAPPING.md` §1) và `Nhân viên: <tên>, Tháng M năm YYYY` (fixture golden, đo S079) | FACT | ngoài hai dạng này → `HEADER` = không có (không đoán) |
| Ý nghĩa nghiệp vụ "huỷ/hoàn" của REMOVED | UNKNOWN → DEFER (PRA-004, OWNER_DECISION_REQUIRED trước khi phân xử) | F3 |

---

## CURRENT STATE — reverse-engineering (S079, HEAD `553d8a3`)

### A. Pipeline hiện tạo ra business objects nào (FACT)

```text
/run (app/web/server.py::run_report)
 → live_pull (Tracking) → run_owner_report → demo.run_demo
    raw_rows   = read_raw_rows(sales)                           list[RawRow]   (app/modules/importing/raw_reader.py)
    result     = run_import_production(sales, composition)     ImportResult(preview, orders: list[Order], unmapped_lines, review_queue: ReviewQueue)
    records    = composition.records                           tuple[PriceResolutionRecord]  (mỗi record mang cùng PriceEvidenceSnapshot)
    summary    = export_report(result, records, raw_rows, …)   ReportSummary  — bên trong: _present_lines(...) → list[_PresentedLine]
 → DemoRun(result, price_records, summary, output_path)        (app/demo.py)  — KHÔNG có raw_rows, KHÔNG có presented lines
 → store.save_artifact + store.create_run(run_id, view=6 số, tracking_evidence)  (R2 / SQLite local)
```

- `WorkingLine` (38 trường, `app/modules/domain/models.py`): mọi trường
  nguồn + `accounting_purchase_price/price_source/accounting_profit/
  kpi_purchase_price/kpi_purchase_price_provenance/eligible_kpi_profit/
  lead_source_final/product_group_final/conversion_*`.
- `Order`: nhóm theo `order_id`; `date/employee_*` lấy dòng đầu.
- AUTO/PENDING **chỉ** tồn tại trong `_PresentedLine.status`
  (`"PENDING" if reasons else "AUTO"`) — private trong exporter.
- `ReviewItem` typed payload (`app/modules/validation/models.py`): category,
  severity, scope, provenance rows, order_id.

### B. Key/provenance hiện có (FACT)

- `RawRow.row_hash` = sha256 của TOÀN BỘ ô dòng (kể cả PII, kể cả thứ tự
  cột) — dùng dedup trong-lần-nhập; KHÔNG bền qua hai export nếu PII đổi
  → không dùng làm `line_fingerprint`, chỉ lưu tham chiếu.
- `RawRow.source_file/source_sheet/source_row`; `order_id` = Số BH
  (`NFC + strip`); dòng không có Số BH bị `read_raw_rows` bỏ (fixture: 1
  dòng) — snapshot đếm `rows_without_order_id` độc lập.
- `PriceEvidenceSnapshot` (`app/modules/pricing/resolution/sources.py`):
  `tracking_price_history_capture_id/_captured_at`,
  `tracking_catalog_capture_id`, `tracking_inv_map_capture_id`,
  `public_purchase_version_id/_content_hash`, `identity_store_revision`,
  `business_timezone_label/_provenance`, `vendor_price_source`.
- `EmployeeMaster.snapshot_id` (`app/modules/mapping/employee_mapper.py`,
  16 hex từ nội dung master) — chính là `config_snapshot_id` golden dùng.
- `tracking_evidence` dict từ live pull (đã persist trong RunRecord).
- `RunRecord`: `run_id, created_at, status, workbook_display_name,
  artifact_path, view, tracking_evidence, error_message` — không có
  đơn/dòng/fingerprint/coverage.

### C. PostgreSQL schema hiện tại (FACT)

`tools/db/schema.py` = 4 bảng `legacy_import`, `legacy_summary_row`,
`legacy_daily_sales`, `legacy_monthly_reference` (origin CHECK
`LEGACY_REFERENCE`, `ExactNumeric` = NUMERIC/PG, TEXT/SQLite, JSON lưu TEXT).
Alembic head `0001_legacy` (`tools/db/__init__.py::ALEMBIC_HEAD`), migration
sinh DDL từ `schema.METADATA`. `assert_schema_current` fail-closed theo
revision. Production: Render PostgreSQL 18 (Virginia), `HISTORY_DATABASE_URL`
+ `postgresql+psycopg://` (DEC-170), `Dockerfile` CMD `alembic upgrade head
&& gunicorn --workers 2`. Hai test guard "không prebuild PRA-002":
`tests/test_history_db.py::test_migration_chain_contains_only_the_legacy_revision`
và `::test_schema_declares_exactly_the_four_frozen_legacy_tables`.

### D. Khoảng cách nhỏ nhất để persist PIPELINE_GENERATED (INFERENCE)

1. `DemoRun` cần mang thêm `raw_rows` và `presented_lines` (đã tính trong
   `run_demo`/exporter, chỉ chưa trả ra) — 2 trường, không tính lại gì.
2. Exporter chỉ cần **alias public** `present_lines = _present_lines`,
   `PresentedLine = _PresentedLine` — không đổi hành vi, không đổi XLSX.
3. `run_report` gọi một **history writer** sau `run_owner_report`, TRƯỚC
   khi `finally` xoá file tạm (writer không cần file, chỉ cần `DemoRun` +
   header dòng 2 đã đọc — đọc header bằng openpyxl `read_only` trong
   `app/history`, KHÔNG sửa `raw_reader`).
4. Migration `0002_snapshots` + `SnapshotRepository` cạnh
   `LegacyRepository` dùng chung `Engine`.

### E. Boundary phải thêm để reconciliation chạy được (INFERENCE)

- `app/history/` (package MỚI, thuần Python, không I/O DB, không import
  `app/modules/**` ngoài domain models đã có): `keys` (ORDER_KEY,
  product_key, occurrence_index, line_fingerprint), `coverage` (header
  parse hai dạng, DETECTED, coverage_state), `reconciler` (thuần: nhập
  "hiện trạng theo khoá" + "snapshot mới" → danh sách quyết định
  INSERT/SAME/SOURCE_CHANGED/COLLISION, NOT_SEEN/REMOVED, RESULT_REVISED),
  `models` (dataclass kết quả).
- `app/web/history_writer` (MỚI): điều phối một đơn vị công việc: đọc
  hiện trạng qua repository → reconciler → ghi qua repository trong MỘT
  transaction.
- `app/web/history_store.py`: thêm `SnapshotRepository`.
- Không boundary mới nào ở `app/modules/**`.

---

## Phạm Vi (Scope)

IN_SCOPE:
1. Migration `0002_snapshots` (6 bảng mục 4), `ALEMBIC_HEAD` → `0002_snapshots`.
2. `app/history/` thuần: keys/fingerprint/coverage/reconciler.
3. `SnapshotRepository` + `history_writer`: ghi snapshot, source version,
   membership, result version, current, flag — trong một transaction;
   đọc hiện trạng theo khoá; truy vấn tổng hiện hành theo kỳ (đơn, dòng,
   `total_sales`, số cờ) để chứng minh no-double-count và phục vụ acceptance.
4. `run_report`: ghi history trong cùng đơn vị công việc với `create_run`
   (fail-closed — xem mục 11).
5. Coverage confirmation contract tối thiểu: `POST
   /du-lieu/snapshot/<snapshot_id>/xac-nhan-du` (mục 7.3).
6. Tab "Dữ liệu" (template `app/web/templates/du_lieu.html` đã có): thêm
   module "Snapshot kế toán" — danh sách snapshot (coverage_state, DETECTED
   range, header, run_id, đơn/dòng, tóm tắt reconcile INSERT/SAME/CHANGED/
   NOT_SEEN/REMOVED/COLLISION/RESULT_REVISED), form xác nhận đủ, và
   `GET /du-lieu/snapshot/<snapshot_id>` (read-only): bảng cờ của snapshot
   với khoá, loại, `changed_fields`, snapshot/run liên quan; bảng "Hiện
   hành theo kỳ" (đơn/dòng/doanh thu current + số cờ). Không chart, không
   bộ lọc, không tab mới.
7. Test: unit reconciler, integration hai snapshot, fail-closed, PII, append-only.
8. `tools/analysis/make_snapshot_variants` (CLI chạy trên máy Owner, output
   không commit) để tạo controlled copy cho Real Data Acceptance (mục 15).
9. Tài liệu: task file này, DEC-171, ledger, PROGRESS/LO_TRINH, handoff,
   `docs/deployment/S071_DEPLOYMENT.md` (thêm ghi chú migration 0002 khi deploy).

## Phụ Thuộc (Dependencies)
- `TASK-PRA-001` = DONE (engine/migration chain/`history_store`/tab Dữ liệu).
- ADR-108 Accepted (DEC-167); DEC-170 contract env.
- Production PostgreSQL đã activation (S078, DEC-170 OWNER_ACCEPTED) và —
  cập nhật S079 close-out — Owner **đã deploy canonical**, đã import
  workbook legacy thật thành công, dữ liệu persist/đọc lại được trên
  production, không còn OOM ở 512 MB (bằng chứng: quan sát production của
  Owner; xem `PROJECT/PROJECT_PROGRESS.md` → "PRODUCTION STATE
  RECONCILIATION — S079 CLOSE-OUT"). Dependency hạ tầng vì vậy ĐÃ THOẢ.
  `CHECK-PRA002-15` vẫn là gate riêng: cần một lần deploy SHA mang
  migration `0002_snapshots` SAU khi implement — KHÔNG phải điều kiện của
  implementation/test local (SQLite).
- Phase D bảo mật (`0.0.0.0/0` của `tinphat-reports-db`) còn OPEN/PENDING —
  không chặn task này; không mở repair S078/S078R mới.
- Real Data Acceptance cần workbook kế toán thật (Owner cung cấp lúc chạy,
  không commit — `.gitignore` `data/samples/`).

## Chặn (Blocks)
- TASK-PRA-003, TASK-PRA-004, TASK-PRA-005 (đều đọc từ current/version của PRA-002).

## An Toàn Để Chạy Song Song Với (Parallel-Safe With)
- TASK-REM-T06. KHÔNG song song với task nào chạm `app/web/server.py`,
  `tools/db/**`, `app/web/history_store.py`, `app/demo.py`.

## Phạm Vi Tác Động Dự Kiến (Expected Touch Area)

Allowed:
- `tools/db/schema.py` (+6 bảng), `tools/db/__init__.py` (`ALEMBIC_HEAD`),
  `tools/db/migrations/versions/0002_snapshots` (mới).
- `app/history/` (mới): `keys`, `coverage`, `reconciler`, `models`, `__init__`.
- `app/web/history_store.py` (+`SnapshotRepository`, +hàm dựng dùng chung engine),
  `app/web/history_writer` (mới), `app/web/server.py` (run_report + 2 route + data tab),
  `app/web/templates/du_lieu.html`, template chi tiết snapshot (mới),
  `app/web/static/css/tinphat-ui.css` (chỉ thêm class nếu cần).
- `app/demo.py`: CHỈ thêm 2 trường vào `DemoRun` (`raw_rows`,
  `presented_lines`) và gán chúng — không đổi luồng.
- `app/modules/exporting/excel_exporter.py`: CHỈ thêm alias public
  `present_lines`/`PresentedLine` — không đổi thân hàm, không đổi XLSX.
- `tests/`: mới + cập nhật đúng hai guard trong `tests/test_history_db.py`
  (chain gồm `0001_legacy`, `0002_snapshots`; METADATA = 4 legacy + 6 PRA-002).
- `tools/analysis/make_snapshot_variants` (mới, CLI ngoài container).
- `docs/**`, `PROJECT/**`, `docs/deployment/S071_DEPLOYMENT.md`.

Không được đụng vào nếu chưa có Scope Expansion (Do not touch without Scope Expansion):
- `app/modules/**` (ngoài alias exporter nêu trên), `app/pipeline.py`,
  `app/composition.py`, `app/owner_usability.py`, `app/owner_launcher.py`,
  `app/web/storage_backend.py`, `app/web/run_registry.py`, `tools/storage/**`,
  `tools/tracking/**`, `config/**`, `data/**`, `tests/fixtures/golden/**`
  (không sửa fixture; fixture hai-snapshot được SINH từ golden bằng script
  test, không commit bản cắt), `app/legacy/**`, 4 bảng `legacy_*`,
  `render.yaml`, `Dockerfile`, mọi thứ ở Tracking.

---

## (4) DATA_MODEL_MINIMUM — migration `0002_snapshots`

Nguyên tắc: cột `origin` tường minh (CHECK `= 'PIPELINE_GENERATED'`) trên
mọi bảng fact; tiền `ExactNumeric`; JSON lưu TEXT; timestamp ISO-8601 UTC
dạng TEXT (cùng quy ước `legacy_import.imported_at`); ngày `Date`
(SQLite/PG đều hỗ trợ qua SQLAlchemy `Date`). Mọi bảng dưới đây là
**append-only** trừ `order_line_current` và các cột xác nhận coverage trên
`source_snapshot` (xem mục 9, 7.3).

```text
source_snapshot                       -- một lần upload workbook kế toán chạy thành công
  snapshot_id            TEXT PK        ('SNAP-' + created_at UTC compact + '-' + fingerprint[:8])
  origin                 TEXT NOT NULL CHECK = 'PIPELINE_GENERATED'
  run_id                 TEXT NOT NULL UNIQUE   (= RunRecord.run_id; liên kết R2 runs/<id>.json, artifacts/<id>.xlsx)
  created_at             TEXT NOT NULL          (UTC ISO-8601)
  source_file_name       TEXT                   (basename hiển thị, đã _safe_display_name)
  file_fingerprint       TEXT NOT NULL          (sha256 bytes workbook upload)
  file_size              INTEGER
  duplicate_of_snapshot_id TEXT NULL FK source_snapshot   (snapshot đầu tiên có cùng fingerprint — RE_UPLOAD, thông tin)
  header_text            TEXT NULL              (nguyên văn ô A2)
  header_date_min        DATE NULL              (chỉ khi header khớp một trong hai dạng đã biết)
  header_date_max        DATE NULL
  detected_date_min      DATE NOT NULL
  detected_date_max      DATE NOT NULL
  coverage_state         TEXT NOT NULL CHECK IN ('DETECTED_ONLY','HEADER_CONSISTENT','CONFIRMED_COMPLETE')
  confirmed_range_start  DATE NULL              -- chỉ có khi CONFIRMED_COMPLETE
  confirmed_range_end    DATE NULL
  confirmed_at           TEXT NULL
  confirmed_by           TEXT NULL              -- luôn NULL ở PRA-002 (uploaded_by DEFER)
  sheet_data_rows        INTEGER NOT NULL       -- đếm độc lập từ sheet (dòng không rỗng từ dòng 6)
  rows_without_order_id  INTEGER NOT NULL
  line_count             INTEGER NOT NULL       -- = số presented lines = số RawRow có BH
  order_count            INTEGER NOT NULL
  n_insert / n_same / n_source_changed / n_collision   INTEGER NOT NULL
  n_not_seen / n_removed_candidate / n_result_revised INTEGER NOT NULL DEFAULT 0
  evidence_json          TEXT NOT NULL          -- PriceEvidenceSnapshot (mọi id/revision/hash) + tracking_evidence live pull
                                                --   + employee_master_snapshot_id + app_commit (env RENDER_GIT_COMMIT nếu có, else NULL)
  summary_json           TEXT NOT NULL          -- ReportSummary (input_orders, auto_orders, review_orders, error_count, review_reason_counts)

order_line_source_version             -- TRỤC NGUỒN, cấp dòng; append-only
  id                     INTEGER PK autoincrement
  origin                 TEXT NOT NULL CHECK = 'PIPELINE_GENERATED'
  order_key              TEXT NOT NULL          -- = engine order_id (NFC+strip), chuỗi opaque
  product_key            TEXT NOT NULL          -- sha256(product_raw NFC+strip | "")
  occurrence_index       INTEGER NOT NULL       -- 1..n
  version_no             INTEGER NOT NULL       -- 1 = INSERT; n+1 mỗi SOURCE_CHANGED
  snapshot_id            TEXT NOT NULL FK source_snapshot   -- snapshot TẠO version này
  bh_number              INTEGER NULL           -- ^BH(\d+)$ → số; khác → NULL (F4)
  bh_year_hint           INTEGER NULL           -- year(sale_date) (F4)
  sale_date              DATE NULL
  product_raw            TEXT NULL
  quantity / sell_price / discount / total_sales_raw / delivery_cost / source_profit   ExactNumeric NULL
  imei                   TEXT NULL
  note_raw               TEXT NULL
  employee_raw           TEXT NULL
  row_hash               TEXT NOT NULL          -- RawRow.row_hash (tham chiếu, KHÔNG dùng so khớp)
  line_fingerprint       TEXT NOT NULL          -- mục 5.2
  changed_fields_json    TEXT NULL              -- {field: {"old": ..., "new": ...}} khi version_no > 1
  created_at             TEXT NOT NULL
  UNIQUE (order_key, product_key, occurrence_index, version_no)     -- chặn double-insert dưới concurrency
  INDEX  (order_key), INDEX (sale_date)

snapshot_line                         -- membership: dòng nào xuất hiện trong snapshot nào, kết quả reconcile là gì; append-only
  snapshot_id            TEXT NOT NULL FK source_snapshot
  order_key, product_key, occurrence_index      (ORDER_LINE_KEY)
  source_version_id      INTEGER NOT NULL FK order_line_source_version   -- version mà dòng này khớp/tạo
  source_row             INTEGER NOT NULL       -- dòng trong sheet của snapshot này
  outcome                TEXT NOT NULL CHECK IN ('INSERT','SAME','SOURCE_CHANGED','ORDER_KEY_COLLISION')
  PK (snapshot_id, order_key, product_key, occurrence_index)

order_line_result_version             -- TRỤC KẾT QUẢ (pipeline authoritative), 1 dòng/run/khoá; append-only
  id                     INTEGER PK autoincrement
  origin                 TEXT NOT NULL CHECK = 'PIPELINE_GENERATED'
  run_id                 TEXT NOT NULL
  snapshot_id            TEXT NOT NULL FK source_snapshot
  order_key, product_key, occurrence_index
  source_version_id      INTEGER NOT NULL FK order_line_source_version   -- kết quả này tính trên source version nào
  status                 TEXT NOT NULL CHECK IN ('AUTO','PENDING')       -- từ PresentedLine.status — MỘT nguồn sự thật
  pending_reasons_json   TEXT NULL              -- PresentedLine.reasons (typed strings: PriceResolutionReason.value / category / Pending.<field>)
  total_sales            ExactNumeric NULL      -- WorkingLine.total_sales (đã trừ chiết khấu, DEC-114)
  employee_normalized    TEXT NULL
  employee_group         TEXT NULL
  lead_source_final      TEXT NULL
  identity_namespace     TEXT NULL
  canonical_product_code TEXT NULL
  accounting_purchase_price ExactNumeric NULL
  price_source           TEXT NOT NULL
  composition_rule       TEXT NULL              -- PriceResolutionRecord.rule.value (NULL cho pre-cutover confirmed)
  accounting_profit      ExactNumeric NULL
  kpi_purchase_price     ExactNumeric NULL
  kpi_purchase_provenance TEXT NOT NULL
  eligible_kpi_profit    ExactNumeric NULL
  product_group_final    TEXT NULL
  conversion_scheme_final TEXT NULL
  conversion_rate_final  ExactNumeric NULL
  result_fingerprint     TEXT NOT NULL          -- sha256(status, accounting_purchase_price, eligible_kpi_profit) — đúng 3 trường F3 dùng để phát hiện RESULT_REVISED
  created_at             TEXT NOT NULL
  UNIQUE (run_id, order_key, product_key, occurrence_index)

order_line_current                    -- MỘT dòng cho MỘT khoá; bảng con trỏ (được UPDATE có kiểm soát — mục 9)
  order_key, product_key, occurrence_index      PK
  origin                 TEXT NOT NULL CHECK = 'PIPELINE_GENERATED'
  current_source_version_id INTEGER NOT NULL FK order_line_source_version
  current_result_version_id INTEGER NOT NULL FK order_line_result_version
  first_seen_snapshot_id TEXT NOT NULL FK source_snapshot
  last_seen_snapshot_id  TEXT NOT NULL FK source_snapshot
  sale_date              DATE NULL              -- denormalize từ current source version để lọc theo kỳ
  order_key_collision    BOOLEAN NOT NULL DEFAULT FALSE
  updated_at             TEXT NOT NULL

reconciliation_flag                   -- mọi điều người dùng cần nhìn thấy; append-only (acknowledged_at luôn NULL ở PRA-002)
  id                     INTEGER PK autoincrement
  kind                   TEXT NOT NULL CHECK IN ('SOURCE_CHANGED','NOT_SEEN_IN_LATEST_SNAPSHOT','REMOVED_IN_SOURCE_CANDIDATE','RESULT_REVISED','ORDER_KEY_COLLISION')
  order_key, product_key, occurrence_index
  raised_by_snapshot_id  TEXT NOT NULL FK source_snapshot
  run_id                 TEXT NULL
  from_version_id        INTEGER NULL           -- source hoặc result version cũ (theo kind)
  to_version_id          INTEGER NULL
  detail_json            TEXT NULL              -- changed_fields / (old,new) của 3 trường result / khoảng ngày lệch (COLLISION)
  created_at             TEXT NOT NULL
  acknowledged_at        TEXT NULL
  INDEX (kind), INDEX (order_key)
```

Không tạo: `order_source_version`, `review_item`, `acknowledgement`,
coverage calendar, bảng target. Cấp đơn là `GROUP BY order_key` trên
current — không bảng riêng.

Phân loại field (03_DATA_MODEL_RULES): `order_key/bh_number/product_raw/
số tiền/employee_raw/imei/note_raw` = Internal business data (`note_raw`
có thể chứa tên/SĐT khách do người nhập gõ tự do — FACT từ
`tests/fixtures/golden/anonymize.py`; PRA-002 vẫn lưu vì engine ĐỌC nó để
phân loại ADS và nó nằm trong fingerprint; DB có access control + không
phơi ra browser ngoài trang Dữ liệu nội bộ; ghi rõ ở 17_DATA_GOVERNANCE
phần Sensitive); `evidence_json` = System data; không có Public, không có
Secret.

---

## (5) Source-version contract

### 5.1 Khoá
```text
ORDER_KEY        = WorkingLine.order_id   (engine; NFC+strip; opaque)
product_key      = sha256(NFC(product_raw).strip()) ; product_raw None → sha256("")
occurrence_index = 1..n theo source_row tăng dần trong (snapshot, ORDER_KEY, product_key)
ORDER_LINE_KEY   = (ORDER_KEY, product_key, occurrence_index)
```

### 5.2 `line_fingerprint`
```text
sha256( "\x1f".join(canon(x) for x in (
   sale_date (ISO), product_raw, quantity, sell_price, discount, total_sales_raw,
   delivery_cost, imei, note_raw, employee_raw, source_profit )) )
canon(None) = "" ; canon(Decimal) = str(Decimal.normalize()) (1000 ≡ 1000.0 ≡ 1E+3 → "1000") ;
canon(str) = NFC + strip ; canon(date) = YYYY-MM-DD
```
KHÔNG gồm: `source_row`, `source_file`, `source_sheet`, `row_hash`,
`customer_code`, `customer`, `address`, `phone`, `shipper_raw`. Đổi PII hay
đổi vị trí dòng KHÔNG tạo SOURCE_CHANGED.

### 5.3 Version
- `INSERT` → version 1. `SOURCE_CHANGED` → `version_no = max + 1`,
  `changed_fields_json` = mọi trường 5.2 có `canon` khác, giá trị cũ/mới
  nguyên văn. `SAME` → không version mới; `snapshot_line` ghi
  `outcome=SAME` trỏ `source_version_id` hiện hành.
- Không `UPDATE` version; không `DELETE`. Một version thuộc ĐÚNG một
  snapshot tạo nó.

---

## (6) Result-version contract

- Mỗi run (mỗi snapshot) ghi ĐÚNG một result version cho MỖI khoá của
  snapshot đó, kể cả dòng `SAME` (pipeline đã chạy lại thật với evidence
  mới) — không "copy" result cũ.
- `status`/`pending_reasons` lấy từ `PresentedLine` (nguồn sự thật duy
  nhất, chính là thứ XLSX in). Các trường nghiệp vụ lấy từ `WorkingLine`
  và `PriceResolutionRecord` tương ứng (record có thể None với dòng
  pre-cutover confirmed — FACT exporter).
- `RESULT_REVISED` phát sinh khi: khoá đã có `current_result_version` VÀ
  `source_version_id` của kết quả mới == `current_source_version_id` VÀ
  `result_fingerprint` khác. Khi source đổi cùng lúc (SOURCE_CHANGED) thì
  KHÔNG gắn RESULT_REVISED (kết quả đổi là hệ quả của nguồn đổi).
- `result_fingerprint` chỉ gồm `status`, `accounting_purchase_price`,
  `eligible_kpi_profit` (F3). Các trường khác đổi (ví dụ `price_source`
  đổi nhãn nhưng giá bằng nhau) vẫn được lưu đầy đủ ở version mới, chỉ
  không sinh cờ — tránh nhiễu (PRA-000 O).

---

## (7) Snapshot coverage contract

### 7.1 Ba mức và cách tính (FACT/OWNER_DECISION)
```text
DETECTED    = [min(sale_date), max(sale_date)] trên RawRow có BH (luôn có; nếu mọi sale_date None → run FAIL trước đó bởi pipeline/exporter)
HEADER      = parse ô A2 CHỈ theo hai dạng đã biết:
              (1) r"^Từ ngày (\d{2}/\d{2}/\d{4}) đến ngày (\d{2}/\d{2}/\d{4})"          → [d1, d2]
              (2) r"^Nhân viên: .*?, Tháng (\d{1,2}) năm (\d{4})$"                        → [1/M/YYYY, cuối tháng M/YYYY]
              không khớp → HEADER = None, header_text vẫn lưu nguyên văn
coverage_state:
  DETECTED_ONLY        khi HEADER None hoặc HEADER ⊉ DETECTED (DETECTED có ngày ngoài header → cảnh báo, không chặn)
  HEADER_CONSISTENT    khi HEADER ⊇ DETECTED
  CONFIRMED_COMPLETE   CHỈ qua 7.3
```
Cảnh báo (thông tin, không chặn, hiển thị ở trang snapshot): DETECTED hẹp
hơn HEADER; `rows_without_order_id > 0`; DETECTED chồng một snapshot
`CONFIRMED_COMPLETE` trước đó mà `line_count` nhỏ hơn.

### 7.2 Điều KHÔNG được làm
Không suy diễn complete từ min/max, từ "thấy ngày cuối tháng", từ header,
từ số dòng, từ thứ tự upload. Không tự động nâng cấp trạng thái.

### 7.3 UX/contract tối thiểu cho xác nhận (INFERENCE — quyết định chiến thuật DEC-171, không phải UI PRA-004)

Xác nhận là hành động **riêng, sau upload**, trên bản ghi snapshot trong
tab Dữ liệu (người dùng đã nhìn thấy DETECTED, header, cảnh báo trước khi
xác nhận — đúng tinh thần F3 "chỉ đề nghị khi HEADER_CONSISTENT hoặc có
REMOVED tiềm năng"; form chỉ hiển thị khi snapshot chưa CONFIRMED):

```text
POST /du-lieu/snapshot/<snapshot_id>/xac-nhan-du
  input : tu_ngay (YYYY-MM-DD), den_ngay (YYYY-MM-DD), xac_nhan = "1" (checkbox bắt buộc)
          câu chữ trên form: "Tôi xác nhận sổ này là ĐẦY ĐỦ mọi chứng từ bán hàng cho khoảng [tu_ngay, den_ngay]"
  validate (server, fail-closed 400 nếu sai): snapshot tồn tại; chưa CONFIRMED_COMPLETE (không xác nhận lại — bất biến);
          tu_ngay ≤ den_ngay; DETECTED ⊆ [tu_ngay, den_ngay] (dữ liệu có ngày ngoài khoảng khai báo → từ chối, nói rõ ngày lệch);
          không nhận khoảng > 366 ngày (fail-safe chống gõ nhầm năm)
  side effects (MỘT transaction): source_snapshot.coverage_state = CONFIRMED_COMPLETE, confirmed_range_*, confirmed_at;
          chạy bước REMOVED (mục 8, bước R) cho đúng snapshot này; cập nhật n_removed_candidate
  idempotency: lần 2 → 409 (đã xác nhận); không thay đổi gì
  output: redirect PRG về /du-lieu/snapshot/<id> với thông điệp
```
`confirmed_by` để NULL (không có danh tính trong app — DEFER N.11). Không
có "huỷ xác nhận" ở PRA-002 (DEFER; nếu cần, một xác nhận sai được xử lý
bằng snapshot mới + Owner quyết).

---

## (8) Reconciliation state machine

Đầu vào một lần chạy: `S_new` (snapshot mới với tập khoá + fingerprint +
kết quả) và `CUR` (hiện trạng theo khoá từ `order_line_current` + version
current). Toàn bộ chạy trong **một transaction** cùng với ghi
snapshot/version/result/current/flag.

```text
Bước 0  Fingerprint file: nếu đã có snapshot cùng file_fingerprint → duplicate_of_snapshot_id = snapshot đầu; KHÔNG rẽ nhánh khác
        (nội dung y hệt → mọi khoá sẽ ra SAME ở bước 2 — không cần đường riêng; run vẫn tạo result version mới)
Bước 1  Tính ORDER_LINE_KEY + line_fingerprint cho mọi presented line của S_new (occurrence_index theo source_row)
Bước 2  Với mỗi khoá k ∈ S_new:
          k ∉ CUR                                             → INSERT             (version 1; current ← v1)
          k ∈ CUR và |sale_date_new − sale_date_cur| > 90 ngày → ORDER_KEY_COLLISION
                                                                 (ghi version mới KHÔNG current; snapshot_line.outcome=COLLISION; flag;
                                                                  current giữ nguyên; order_line_current.order_key_collision = TRUE;
                                                                  KHÔNG SAME/CHANGED — không đoán hai đơn là một)
          k ∈ CUR, fingerprint == current                      → SAME               (không version; membership; last_seen ← S_new)
          k ∈ CUR, fingerprint != current                      → SOURCE_CHANGED     (version n+1 + changed_fields; current ← n+1; flag SOURCE_CHANGED)
Bước 3  Result: với mỗi khoá k ∈ S_new (trừ COLLISION) ghi result version (run_id, source_version_id = version current sau bước 2);
          nếu k đã có current_result và source_version không đổi (SAME) và result_fingerprint khác → flag RESULT_REVISED
          current_result ← result version mới (run mới nhất trên khoá)
Bước 4  NOT_SEEN: với mỗi khoá c ∈ CUR có sale_date ∈ DETECTED(S_new) và c ∉ S_new và không COLLISION
          → flag NOT_SEEN_IN_LATEST_SNAPSHOT (thông tin; current không đổi; vẫn tính analytics)
Bước 5  Ghi source_snapshot với n_* ; commit.

Bước R (chỉ khi 7.3 xác nhận CONFIRMED_COMPLETE cho snapshot S):
        với mỗi khoá c ∈ CUR có sale_date ∈ [confirmed_start, confirmed_end] và c ∉ snapshot_line(S) và không COLLISION
          → flag REMOVED_IN_SOURCE_CANDIDATE (raised_by S); current KHÔNG đổi; VẪN tính analytics; KHÔNG DELETE
        (NOT_SEEN của cùng khoá do S tạo trước đó giữ nguyên làm lịch sử; UI hiển thị cờ REMOVED là cờ mạnh hơn)
```

Trạng thái của một khoá (dẫn xuất, không lưu enum riêng): `CURRENT` (mặc
định) · `CURRENT + SOURCE_CHANGED` · `CURRENT + NOT_SEEN` ·
`CURRENT + REMOVED_CANDIDATE` · `CURRENT + RESULT_REVISED` ·
`CURRENT + ORDER_KEY_COLLISION`. Mọi trạng thái đều **vẫn CURRENT** ở
PRA-002 — phân xử (loại khỏi analytics, huỷ, gộp) là PRA-004 + Owner rule.

---

## (9) Current-state selection rule

```text
current_source_version(k) = version_no lớn nhất KHÔNG phải COLLISION   (policy LATEST_SNAPSHOT_IS_CURRENT_CANDIDATE — hằng số, không khẳng định giá trị nào "đúng")
current_result_version(k) = result version của run MỚI NHẤT (created_at) có chứa k
analytics hiện hành kỳ P     = mọi khoá trong order_line_current có sale_date ∈ P  (kể cả có cờ; COLLISION dùng bản current cũ)
  Số đơn      = COUNT(DISTINCT order_key)
  Doanh thu   = SUM(result_current.total_sales)      -- mỗi khoá đúng một lần theo cấu trúc bảng (PK), không phải theo DISTINCT ở query
  LN KPI      = SUM(result_current.eligible_kpi_profit WHERE status='AUTO')   (kèm coverage = dòng AUTO / tổng dòng — không dùng ở PRA-002 UI ngoài trang snapshot)
```
Bất biến: `order_line_current` có PK theo khoá → **không thể** có hai
current cho một khoá ở tầng schema, không chỉ ở tầng query. Chỉ hai cột
được UPDATE trên bảng con trỏ: `current_*_version_id`,
`last_seen_snapshot_id/sale_date/order_key_collision/updated_at`; mọi
UPDATE đều đi kèm một bản ghi `snapshot_line`/`reconciliation_flag` giải
thích vì sao (mục 10).

---

## (10) Provenance requirements

Mỗi bản ghi fact trả lời được "từ đâu":
- source version → `snapshot_id` (→ `run_id` → R2 `runs/<id>.json`,
  `artifacts/<id>.xlsx`, `file_fingerprint`, `source_file_name`) +
  `source_row` qua `snapshot_line` + `row_hash`.
- result version → `run_id`, `snapshot_id.evidence_json`
  (`tracking_price_history_capture_id/_captured_at`,
  `tracking_catalog_capture_id`, `tracking_inv_map_capture_id`,
  `public_purchase_version_id/_content_hash`, `identity_store_revision`,
  `business_timezone_*`, `vendor_price_source`, `tracking_evidence` live
  pull, `employee_master_snapshot_id`, `app_commit`), `source_version_id`,
  `price_source`, `composition_rule`, `kpi_purchase_provenance`.
- mọi thay đổi current → `reconciliation_flag`/`snapshot_line` với
  `raised_by_snapshot_id` + `from/to_version_id`.
- `changed_fields_json` ghi cả cũ và mới, nguyên văn `canon`.
- Không mirror payload Tracking; chỉ id/revision/hash.
- Không PII trong bất kỳ bảng PRA-002 (kiểm bằng test: tập cột của 6 bảng
  ∩ {`customer`, `customer_code`, `phone`, `address`, `shipper_raw`} = ∅).

---

## (11) Idempotency / no-double-count rule

1. **Cấu trúc trước, query sau:** PK `order_line_current` + UNIQUE
   `(khoá, version_no)` + UNIQUE `(run_id, khoá)` + PK `snapshot_line` →
   một khoá không thể có hai current, một snapshot không thể ghi một khoá
   hai lần, một run không thể ghi hai result cho một khoá.
2. **Một đơn vị công việc:** `history_writer.write(demo_run, upload_meta,
   run_id)` mở `engine.begin()`; bên trong: đọc CUR → reconciler → insert
   snapshot/version/membership/result/flag → update current →
   `store.save_artifact` + `store.create_run` (R2) → commit. R2 lỗi →
   rollback → trang lỗi 500 hiện có ("không lưu được vào lịch sử run") →
   KHÔNG có run COMPLETE, KHÔNG có snapshot. Commit lỗi SAU khi R2 đã ghi
   (hiếm) → run tồn tại không có snapshot → tab Dữ liệu hiển thị run đó
   với nhãn "KHÔNG CÓ LỊCH SỬ (ghi lỗi)" (join run ↔ snapshot theo
   `run_id`) — fail-visible, không im lặng (residual risk ghi ở mục 12).
3. **Upload lại cùng file** → mọi khoá SAME, 0 version mới, tổng hiện hành
   không đổi; snapshot vẫn được ghi (là sự kiện thật) với
   `duplicate_of_snapshot_id`.
4. **Hai upload gần nhau cùng khoá** (S071B đã có test race cho R2): hai
   transaction cùng INSERT version 1 → UNIQUE chặn cái sau → rollback →
   500 → người dùng chạy lại → SAME. Không bao giờ có hai version 1.
5. **Oracle bằng đẳng thức, không bằng niềm tin:** với mọi cặp snapshot
   A ⊂ B (cùng nội dung phần chung), `state(A rồi B) == state(B một
   mình)` trên (số khoá current, số đơn, `SUM(total_sales)`, tập
   `(khoá, fingerprint)` current). Đây là check REQUIRED (CHECK-PRA002-04).

---

## (12) Fail-safe behavior

| Tình huống | Hành vi |
|---|---|
| History store chưa cấu hình (dev, `REPORTS_REQUIRE_HISTORY_DB` ≠ 1, không có SQLite đã migrate) | `/run` vẫn chạy như S071B nhưng trang kết quả và tab Dữ liệu nói thẳng "Run này KHÔNG được lưu lịch sử — history store chưa cấu hình". Production (`=1`) không bao giờ rơi vào nhánh này (fail-closed lúc khởi động — đã có) |
| Schema ở revision cũ | app không khởi động (`assert_schema_current`, đã có) |
| DB lỗi giữa transaction | rollback toàn bộ; 500; không run COMPLETE |
| Header không khớp hai dạng | `HEADER = None`, `DETECTED_ONLY`, lưu `header_text` |
| DETECTED có ngày ngoài HEADER | `DETECTED_ONLY` + cảnh báo |
| Cùng BH lệch > 90 ngày | `ORDER_KEY_COLLISION`: không SAME/CHANGED, current cũ giữ nguyên, version mới không current, cờ; lần đầu xuất hiện trên production → `OWNER_DECISION_REQUIRED` N.13 (re-trigger tường minh) |
| Kế toán đổi tên hàng trên một dòng | thấy là `INSERT` (khoá mới) + `NOT_SEEN` (khoá cũ) — không đoán ghép; DEFER cải thiện bằng IMEI |
| Kế toán xoá dòng thứ 1 trong hai dòng cùng sản phẩm | `occurrence_index` dịch → `SOURCE_CHANGED` #1 + `NOT_SEEN` #2 — hiển thị, không đoán |
| Xác nhận đủ với khoảng ngày không bao DETECTED | 400, nêu ngày lệch; trạng thái không đổi |
| Xác nhận lần 2 | 409, không đổi |
| `REMOVED_CANDIDATE` | vẫn current, vẫn tính; không xoá; chờ PRA-004 + Owner rule |
| Lỗi ghi history đúng 1 dòng (constraint) | cả snapshot rollback — không snapshot "một nửa" |
| Peak RAM | writer chỉ dùng dữ liệu đã có trong RAM (DemoRun) + đọc lại ô A2 bằng `read_only`; insert theo batch; không giữ workbook thứ hai |

---

## (13) Migration strategy

```text
Schema hiện tại : 0001_legacy — 4 bảng legacy_* (không đổi một cột nào)
Schema mục tiêu : 0002_snapshots — +6 bảng mục 4 (source_snapshot, order_line_source_version, snapshot_line,
                  order_line_result_version, order_line_current, reconciliation_flag); ALEMBIC_HEAD = '0002_snapshots'
Migration       : alembic revision 0002_snapshots (down_revision = 0001_legacy); DDL sinh từ schema.METADATA (tables=6 bảng mới, checkfirst=False);
                  chạy tự động trong Dockerfile CMD `alembic upgrade head` trước gunicorn (đã có) — không auto-migrate trong request
Tương thích ngược: LegacyRepository/route legacy không đổi; RunStore/R2 không đổi; RunRecord không đổi (liên kết run ↔ snapshot qua run_id ở bảng mới)
Validation      : test up/down trên SQLite tmp; DDL Postgres-compatible verify trên PostgreSQL 16 local (psql/initdb có trong môi trường session — như CHECK-PRA001-09)
Rollback        : `alembic downgrade 0001_legacy` xoá 6 bảng PRA-002 (mất dữ liệu snapshot — chấp nhận ở giai đoạn trước production acceptance;
                  sau production acceptance rollback = giữ bảng, deploy lại SHA cũ CHỈ nếu SHA cũ không fail-closed vì revision — SHA PRA-001 sẽ FAIL vì
                  ALEMBIC_HEAD khác → rollback production = downgrade + deploy cũ, ghi rõ trong S071_DEPLOYMENT)
Dữ liệu cũ      : không có dữ liệu PIPELINE_GENERATED trước PRA-002 → không backfill; run cũ trên R2 giữ nguyên, hiển thị "trước PRA-002, không có snapshot"
```

---

## (14) Test strategy

- **Unit reconciler (thuần, không DB)** — fixture synthetic hai snapshot
  (từ `tests/fixtures/synthetic_workbook.py` pattern): INSERT / SAME /
  SOURCE_CHANGED (đúng `changed_fields`) / COLLISION (lệch 91 ngày) /
  NOT_SEEN / REMOVED (chỉ khi confirmed) / RESULT_REVISED (đổi đúng 1 trong
  3 trường; đổi trường khác → không cờ) / occurrence_index ≥ 2 (hai dòng
  cùng sản phẩm trong đơn) / fingerprint bền với `Decimal("1000")` vs
  `Decimal("1000.0")` và PII đổi / thứ tự upload đảo (15–30 trước, 01–30
  sau) / header hai dạng + dạng lạ.
- **Integration qua Flask test client** (pattern `tests/test_web_server.py`
  + capture synthetic của `tests/test_demo.py`): dựng fixture A = golden
  `period_2026_01.xlsx` cắt ≤ 10/01 (89 dòng / 61 đơn — đo S079) và B =
  nguyên bản (351 dòng / 254 đơn) — cắt bằng script trong test, không
  commit bản cắt, không sửa `tests/fixtures/golden/**`; chạy A rồi B →
  đẳng thức `state(A,B) == state(B)`; số đơn = 254; `n_same` = 89; 0
  version > 1. Biến thể B' = B + sửa 1 dòng (`sell_price` + `total_sales_raw`
  nhất quán) + xoá 1 dòng → 1 SOURCE_CHANGED, 1 NOT_SEEN; xác nhận đủ →
  1 REMOVED_CANDIDATE; tổng hiện hành vẫn gồm dòng bị xoá.
- **Fail-closed**: engine lỗi (DB gãy) → 500, không run trong store;
  R2 fake client lỗi → rollback, không snapshot; dev không history →
  thông điệp trung thực.
- **Append-only**: grep tĩnh trong `app/web/history_store.py` /
  `history_writer`: không `delete(` và chỉ `update(order_line_current)`,
  `update(source_snapshot)` (cột confirm); test hành vi: sau 3 snapshot,
  số version chỉ tăng, version cũ đọc lại nguyên văn.
- **Concurrency**: hai transaction chen nhau trên cùng khoá → UNIQUE lỗi
  → cái sau rollback (test trên SQLite bằng hai engine/connection; ghi rõ
  giới hạn dialect).
- **PII**: tập cột 6 bảng không chứa cột PII; `changed_fields`/`detail_json`
  không chứa khoá PII.
- **Boundary**: `tests/test_history_db.py::test_no_module_under_app_imports_a_database_driver_or_alembic`
  giữ PASS; `app/history/**` không import `sqlalchemy`; `app/modules/**`
  diff chỉ là alias; XLSX parity: `export_report` dùng đúng hàm
  `present_lines` (test `is`), `test_demo.py` giữ PASS.
- **Golden**: `tests/test_golden_baseline.py` `58 passed, 2 skipped` không đổi.
- **Memory (RECOMMENDED)**: `ru_maxrss` end-to-end `/run` với writer trên
  fixture golden < 300 MB một worker (baseline S078R: 81.9 MB cho legacy).
- **PostgreSQL thật** (local 16, như CHECK-PRA001-09): migration + kịch bản
  A→B→B' chạy trên PG để bắt lệch dialect (`Date`, `ExactNumeric`, UNIQUE).

---

## (15) Real Data Acceptance

Dùng **workbook kế toán thật** (`So_chi_tiet_ban_hang*.xlsx` — không
commit, SHA256 ghi lại trước/sau, file không bị sửa). Đường ưu tiên: **hai
export thật** của Owner cho cùng tháng (giữa tháng + cuối tháng, đúng kịch
bản 3.1). Đường dự phòng khi chưa có hai export: **controlled copy** từ
một workbook thật bằng `tools/analysis/make_snapshot_variants` — chỉ hai
phép biến đổi giữ nguyên business semantics: (i) `--cut-until YYYY-MM-DD`
giữ nguyên dòng 1–5 và mọi dòng có `Ngày` ≤ mốc, không sửa một ô nào của
dòng giữ lại; (ii) `--edit-line <BH> <product_raw> --sell-price <mới>`
sửa đúng một dòng: `Đơn giá` và `Doanh số bán` (= đơn giá × SL − chiết
khấu theo đúng cách kế toán) — CLI in SHA256 input/output và mô tả phép
sửa nguyên văn; (iii) `--drop-line <BH> <product_raw>`. Mọi biến thể là
ASSUMPTION "export ngắn hơn = tập con" — ghi rõ khi báo cáo; hai export
thật thắng khi có.

| Bước | Hành động | Phải chứng minh (E1: output CLI/HTTP + SQL count) |
|---|---|---|
| RDA-1 | Snapshot A (thật) → `/run` | HTTP 302; `source_snapshot` 1 dòng; `line_count`/`order_count` = XLSX Summary (`Tổng dòng`, `Đơn đã đối chiếu`); mọi khoá `INSERT`; `n_same=0`; tổng `total_sales` current = "Tổng doanh thu đã xác định" của XLSX |
| RDA-2 | Upload lại đúng file A | snapshot #2 với `duplicate_of_snapshot_id` = #1; `n_same = line_count`; 0 version mới (`COUNT(version_no>1)=0`); tổng current KHÔNG đổi (bằng RDA-1 tới từng đồng); result version mới = `line_count` (run mới) và `n_result_revised` ≥ 0 được liệt kê, KHÔNG cờ SOURCE |
| RDA-3 | Snapshot B ⊃ A (export thật thứ hai, hoặc `--cut-until` ngược lại: A = cắt của B) | phần cũ `SAME` (`n_same` = số khoá A vẫn còn), phần mới `INSERT`; **đẳng thức**: current sau (A,B) == current khi chỉ upload B trên DB sạch (số khoá, số đơn, `SUM(total_sales)`, tập `(khoá, fingerprint)`); nếu export thật có dòng A không còn trong B → `NOT_SEEN` được liệt kê (không phải lỗi) |
| RDA-4 | B' = B + `--edit-line` 1 dòng | đúng 1 `SOURCE_CHANGED`; `changed_fields` nêu đúng `sell_price` và `total_sales_raw` (cũ → mới nguyên văn); version cũ vẫn đọc được; current = version mới; `SUM(total_sales)` đổi đúng bằng delta; 0 cờ khác phát sinh từ phép sửa |
| RDA-5 | B'' = B' + `--drop-line` 1 dòng; xác nhận đủ cho tháng đó | trước xác nhận: 1 `NOT_SEEN`; sau `POST xac-nhan-du`: 1 `REMOVED_IN_SOURCE_CANDIDATE`; dòng vẫn current, vẫn trong `SUM`; `COUNT(*)` mọi bảng fact không giảm |
| RDA-6 | Golden/cohort không đổi | `tests/test_golden_baseline.py` `58 passed, 2 skipped`; nếu cohort S068 (58 đơn/83 dòng, 22 AUTO/36 Review) có trong máy: chạy → history ghi đúng 83 khoá, 22 đơn AUTO theo `status` |

Nếu workbook thật không có trong session → CHECK-PRA002-14 `NOT_TESTED`,
gate Owner chạy trên máy Owner theo bảng trên (giống PRA-001 S075).
Nếu RDA phát hiện hình dạng dữ liệu thật mà contract không nhận ra (ví dụ
header dạng thứ ba, BH không dạng `BH\d+`, đơn nhiều ngày) → DỪNG, ghi
`UNKNOWN / OWNER_DECISION_REQUIRED`, không mở rộng parser/thuật toán.

---

## (16) Production Acceptance

Sau Independent Review E2 ACCEPT + Controlled Integration vào
`claude/extract-upload-repo-gq2ws4`:

1. Owner Manual Deploy HEAD canonical (fast-forward; không `main`; không
   force). `alembic upgrade head` tự chạy → `alembic_version = 0002_snapshots`
   trên Render PostgreSQL 18. Service Live; không `HistoryConfigurationError`.
2. `/du-lieu` → 200, có module "Snapshot kế toán" trống + legacy import hiện có
   không đổi; `/nhan-vien` legacy vẫn 200 (PRA-001 không hồi quy).
3. Upload sổ kế toán thật tháng hiện hành qua `reports.tinphatcrm.com/run`
   → 302, run xuất hiện ở lịch sử run (R2) VÀ snapshot xuất hiện ở tab
   Dữ liệu với `DETECTED_ONLY`/`HEADER_CONSISTENT` đúng header thật.
4. Upload lại đúng file → snapshot #2 `n_same = line_count`, 0 version mới,
   trang snapshot #2 không có cờ SOURCE.
5. Render Metrics: RAM đỉnh lúc upload < 512 MB, không "Instance failed".
6. Ghi kết quả (số đơn/dòng/n_same, SHA deploy, thời điểm) vào
   `PROJECT/PROJECT_PROGRESS.md`; `CHECK-PRA002-15 = PASS`. Session không
   có egress tới Render (403) → bước này do Owner thực hiện.

---

## (17) CHANGE_BUDGET

Rút kinh nghiệm PRA-001 (kế hoạch 450/600 → thực tế 1.045, cần DEC-168):
đặt ngân sách theo hình dạng thật của công việc, không theo mong muốn.

- Production Python mới/sửa (`tools/db` delta + `app/history` +
  `history_store` delta + `history_writer` + `server.py` delta + `demo.py`
  delta + exporter alias): **mục tiêu ≤ 1.200 dòng logic, dừng cứng
  1.500** → vượt = `CHANGE_BUDGET_EXCEEDED`, dừng, Owner quyết.
- `app/demo.py` ≤ 6 dòng; `app/modules/exporting/excel_exporter.py` ≤ 4
  dòng (alias). Vượt = `SCOPE EXPANSION REQUIRED`.
- Template mới/sửa ≤ 250 dòng; CSS ≤ 60 dòng thêm.
- Test mới ≥ 40; không skip mới; hai guard `test_history_db` được cập nhật
  (không xoá).
- Không dependency mới (đã có `sqlalchemy`, `alembic`, `psycopg`, `openpyxl`).
- Hardening ≤ 10 %: chỉ khi CHECK-01…13 PASS; ứng viên duy nhất: cảnh báo
  "snapshot CONFIRMED trước đó nhiều dòng hơn", `pg_dump` lên R2 (DEFER
  nếu không kịp).
- Effort: 3 session MAJOR (A, B, C theo mục 20) + 1 Independent Review E2
  + repair ≤ 2 cycle + 1 close-out/integration + Real Data Acceptance.

---

## (18) Explicit deferred items / UNKNOWN

| # | Mục | Loại | Re-trigger |
|---|---|---|---|
| D1 | Phân xử `REMOVED_CANDIDATE`, ý nghĩa huỷ/hoàn, loại khỏi analytics | UNKNOWN → OWNER_DECISION_REQUIRED (trước PRA-004) | mở PRA-004 |
| D2 | BH reset theo năm; namespace `order_key = year:bh`; reconcile xuyên năm | UNKNOWN (N.13) | cờ `ORDER_KEY_COLLISION` đầu tiên trên production, hoặc snapshot đầu tiên có ngày năm mới khi DB đã có khoá năm trước |
| D3 | PII drill-down (`customer`, `customer_code`) | DEFER (N.5) | PRA-004 cần hiển thị khách |
| D4 | `uploaded_by`/`confirmed_by` từ Cloudflare Access | DEFER (N.11) | hardening PRA-004 |
| D5 | Acknowledge cờ (UI + `acknowledged_at`) | DEFER | PRA-004 |
| D6 | `order_source_version`, `review_item` persist, batch-level finding | DEFER | PRA-004 Review Ops |
| D7 | Coverage calendar, diff UI hai snapshot | DEFER | PRA-003 |
| D8 | Ghép dòng đổi tên hàng bằng IMEI | DEFER | thực tế có ≥ 3 trường hợp/tháng |
| D9 | `product_key` casefold/bỏ dấu | DEFER | bằng chứng kế toán đổi hoa/thường cùng một hàng |
| D10 | Huỷ xác nhận coverage | DEFER | Owner yêu cầu |
| D11 | Retention/xoá snapshot, `pg_dump` lên R2 | DEFER (hardening) | dung lượng > 100 MB hoặc release gate |
| D12 | `beta_feedback`/`beta_telemetry` ghi REPO_ROOT (mất trên Render) | DEFER (PRA-000 P.1) | không chặn |
| D13 | `tools/analysis/verify_legacy_import.py` mở workbook không read-only (S078R finding) | DEFER | công cụ CLI ngoài container |
| D14 | Export kỳ ngắn = tập con export kỳ dài | ASSUMPTION | RDA-3 với hai export thật |
| D15 | Đơn nhiều ngày / nhiều nhân viên trong một BH | UNKNOWN (fixture: 0) | RDA phát hiện → OWNER_DECISION_REQUIRED |

---

## (20) Implementation slices

Ba slice dọc (gộp A+B+C của chỉ thị S079 vì cùng một thuật toán reconcile
— tách sẽ là chia nhỏ để tạo task, không phải để kiểm chứng):

### PRA-002.A — Persistence + reconcile trục NGUỒN (INSERT / SAME / SOURCE_CHANGED / COLLISION) + result version + current
```text
GOAL                  = một upload ghi snapshot + source v1 + result v1 + current; upload lại → SAME 0 double-count; sửa 1 dòng → SOURCE_CHANGED giữ version cũ, current mới
DELIVERABLE           = 0002_snapshots; app/history (keys, coverage DETECTED/HEADER, reconciler bước 0–3, 5); SnapshotRepository; history_writer; run_report một transaction; tab Dữ liệu danh sách snapshot + trang snapshot (cờ)
VERIFY                = CHECK-PRA002-01/02/03/04/05/09/10/11/12/13
EFFORT                = 1–2 session
```
### PRA-002.B — Coverage semantics: HEADER_CONSISTENT / xác nhận đủ / NOT_SEEN / REMOVED_CANDIDATE
```text
GOAL                  = fail-safe đúng contract: không confirmed → chỉ NOT_SEEN; confirmed → REMOVED_CANDIDATE vẫn current, vẫn tính
DELIVERABLE           = reconciler bước 4 + R; POST xac-nhan-du; validate; UI form + cảnh báo
VERIFY                = CHECK-PRA002-06/07
EFFORT                = 1 session
```
### PRA-002.C — RESULT_REVISED + Real Data Acceptance + Postgres thật
```text
GOAL                  = cùng source, evidence mới → result version mới, source không đổi, cờ đúng; RDA-1..6 trên workbook thật; kịch bản chạy trên PostgreSQL 16 local
DELIVERABLE           = result_fingerprint + cờ; tools/analysis/make_snapshot_variants; evidence RDA; CHECK-16 memory
VERIFY                = CHECK-PRA002-08/14/16; sau đó Independent Review E2 (CHECK-17) → repair ≤ 2 → Controlled Integration → CHECK-15 Owner
EFFORT                = 1 session (+ review + integration)
```

## Subtask (Subtasks)
- [x] PRA-002.A1 `tools/db/schema.py` + `0002_snapshots` + `ALEMBIC_HEAD`; up/down SQLite; DDL trên PostgreSQL 16 local; cập nhật 2 guard test.
- [x] PRA-002.A2 `app/history/keys` + `coverage` (DETECTED, header 2 dạng) + unit test fingerprint/occurrence.
- [x] PRA-002.A3 `app/history/reconciler` bước 0–3, 5 + unit test 4 case + COLLISION + thứ tự đảo.
- [x] PRA-002.A4 `app/demo.py` (+2 trường) + exporter alias + test `is`.
- [x] PRA-002.A5 `SnapshotRepository` + `history_writer` (một transaction, R2 trong cửa sổ transaction) + test fail-closed/append-only/concurrency.
- [x] PRA-002.A6 `run_report` + tab Dữ liệu (danh sách + trang snapshot) + test Flask; integration golden A(≤10)→B đẳng thức.
- [x] PRA-002.B1 reconciler bước 4 + R; `POST xac-nhan-du` + validate + 409; test NOT_SEEN/REMOVED. (S083; không cần migration — schema 0002 đã đủ; FIND-PRA002-A4 đã sửa)
- [ ] PRA-002.C1 `result_fingerprint` + RESULT_REVISED + test hai capture.
- [ ] PRA-002.C2 `tools/analysis/make_snapshot_variants` + RDA-1..6 (hoặc `NOT_TESTED` + gate Owner).
- [ ] PRA-002.C3 Kịch bản A→B→B'→B'' trên PostgreSQL 16 local; đo `ru_maxrss`.
- [ ] PRA-002.R Independent Review E2 (`docs/reviews/TASK-PRA-002-INDEPENDENT-REVIEW-RECORD`), repair ≤ 2 cycle, Controlled Integration, deployment doc, PROGRESS/LO_TRINH/handoff.

## Ready Gate
Dùng `governance/core/TASK_READY_GATE_STANDARD.md`.

- [x] Objective/Scope/Out-of-scope rõ (mục 1, 2, Phạm Vi).
- [x] Dependency DONE: TASK-PRA-001 = DONE (S077); ADR-108 Accepted; DEC-170 OWNER_ACCEPTED.
- [x] Touch area + Do-not-touch xác định; data/security/routing impact biết rõ (mục 4, 10, 7.3).
- [x] Điều kiện migration sẵn: chain Alembic + fail-closed revision đã có (PRA-001).
- [x] Difficulty/Risk/Blast Radius chấm theo failure path; Tier C; escalation triggers (bên dưới).
- [x] Completion Gate hoàn thiện và **FROZEN tại S079 (2026-09-02)**.
- [x] Owner business contract có DEC (DEC-166 B/C/D, chỉ thị S079); quyết định chiến thuật ghi DEC-171.
- [x] Baseline đo tại BASE_SHA: Golden `58 passed, 2 skipped`; full suite `1608 passed, 11 skipped`.
- [ ] Đồng bộ nhánh đầu session implement (bước 0 Session Open Protocol) — điều kiện vận hành.
- [ ] Workbook kế toán thật có trên máy chạy RDA — điều kiện vận hành; thiếu → CHECK-14 `NOT_TESTED` + gate Owner.

## Completion Gate — (19)
Dùng `governance/core/TASK_COMPLETION_GATE_STANDARD.md` và `governance/core/EVIDENCE_STANDARD.md`.
FROZEN tại S079 (2026-09-02). Risk 4 → mọi REQUIRED phải E1; check dữ liệu
(04, 05, 07, 09) phải có E2 qua Independent Review (CHECK-17). Không xoá/làm
yếu REQUIRED check; thay đổi gate → `COMPLETION GATE CHANGE PROPOSAL`.

### Migration / Data

#### CHECK-PRA002-01 — Migration `0002_snapshots` up/down + DDL Postgres-compatible
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Yêu cầu: `alembic upgrade head` rồi `downgrade 0001_legacy` trên SQLite tmp PASS (6 bảng xuất hiện/biến mất, 4 bảng legacy nguyên vẹn); `alembic upgrade head` trên PostgreSQL 16 local PASS, `SELECT version_num FROM alembic_version` = `0002_snapshots`; `assert_schema_current` FAIL-closed trên DB còn ở `0001_legacy`. Output nguyên văn.


Đã chạy: Slice A (S080): up/down trên SQLite tmp PASS (6 bảng xuất hiện/biến mất, 4 bảng legacy nguyên vẹn); `alembic upgrade head` trên PostgreSQL 16.13 local PASS, `alembic_version = 0002_snapshots`, dòng `legacy_import` chèn ở revision 0001 còn nguyên sau nâng cấp; `assert_schema_current` fail-closed theo `ALEMBIC_HEAD`. Không auto-create schema ngoài Alembic. Output nguyên văn: `docs/sessions/S080-pra-002-slice-a-implementation.md` → Migration.
Executed By:
S080 — PRA-002 Slice A Implementation (2026-09-02)

Timestamp:
2026-09-02

### Functional

#### CHECK-PRA002-02 — Một upload → snapshot + source v1 + result v1 + current, khớp exporter
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Yêu cầu: qua Flask test client `/run` với golden `period_2026_01.xlsx` + capture synthetic: `source_snapshot` 1 dòng; `line_count = 351`, `order_count = 254`, `rows_without_order_id = 1`; `order_line_source_version` 351 dòng version 1; `order_line_result_version` 351; `order_line_current` 351; `SUM(result.total_sales)` = `money.sales_normalized` của `tests/fixtures/golden/expected/period_2026_01.json` (3.562.310.000); số `status='PENDING'` khớp `review_lines` của `ReportSummary`; `evidence_json` chứa đủ capture id. Output test nguyên văn.


Đã chạy: Slice A (S080): `line_count = 351`, `order_count = 254`, `rows_without_order_id = 1`, `sheet_data_rows = 352`; 351 source version (mọi dòng `version_no = 1`), 351 result version, 351 current; `SUM(current total_sales) = 3.562.310.000` == `money.sales_normalized` của golden expected; `COUNT(status='PENDING') = 349` == `ReportSummary.review_lines`; `evidence_json` đủ capture id + `employee_master_snapshot_id`. Test: `tests/test_pipeline_history_vertical.py`.
Executed By:
S080 — PRA-002 Slice A Implementation (2026-09-02)

Timestamp:
2026-09-02

#### CHECK-PRA002-03 — Upload lại cùng file → SAME toàn bộ, 0 double-count
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Yêu cầu: upload lần 2 cùng file → snapshot #2 `duplicate_of_snapshot_id` = #1, `n_same = 351`, `n_insert = 0`; `COUNT(order_line_source_version) = 351` (không tăng); `order_line_current` 351, `last_seen_snapshot_id` = #2; `SUM(total_sales)` không đổi tới từng đồng; `order_line_result_version` = 702 (run mới ghi result mới); 0 cờ SOURCE_CHANGED.


Đã chạy: Slice A (S080): snapshot #2 `duplicate_of_snapshot_id` = #1, `n_same = 351`, `n_insert = 0`; `COUNT(order_line_source_version) = 351` (không tăng), `COUNT(version_no > 1) = 0`; `order_line_current` = 351, `SUM(total_sales)` không đổi tới từng đồng; `order_line_result_version = 702`; 0 cờ SOURCE_CHANGED. Kiểm lại trên PostgreSQL 16 thật (pg-a1 → pg-a2).
Executed By:
S080 — PRA-002 Slice A Implementation (2026-09-02)

Timestamp:
2026-09-02

#### CHECK-PRA002-04 — Overlap A(≤10/01) → B(cả tháng): đẳng thức với B-một-mình
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Yêu cầu: fixture A cắt từ golden 01 (89 dòng/61 đơn) rồi B (351/254): `n_same = 89`, `n_insert = 262`, `n_source_changed = 0`; `state(A,B)` == `state(B)` trên DB sạch: cùng 351 khoá current, 254 đơn, cùng `SUM(total_sales)`, cùng tập `(khoá, line_fingerprint)`; đảo thứ tự (B rồi A) → `n_same = 89`, `n_insert = 0`, `NOT_SEEN` = 262 (thông tin, current không đổi), tổng không đổi. Output test nguyên văn.


Đã chạy: Slice A (S080): fixture A cắt từ golden 01 trong `tmp_path` (KHÔNG commit, KHÔNG sửa `tests/fixtures/golden/**`) đo được 89 dòng / 61 đơn; B = 351 / 254. `n_same = 89`, `n_insert = 262`, `n_source_changed = 0`. `state(A,B) == state(B)` trên DB sạch: cùng `current_totals` VÀ cùng tập `(khoá, line_fingerprint)`. Đảo thứ tự (B rồi A): `n_same = 89`, `n_insert = 0`, tổng không đổi — phần `NOT_SEEN = 262` thuộc bước 4 (slice B), chưa hiện thực. Kiểm lại trên PostgreSQL 16 thật.
Executed By:
S080 — PRA-002 Slice A Implementation (2026-09-02)

Timestamp:
2026-09-02

#### CHECK-PRA002-05 — SOURCE_CHANGED: version cũ giữ, changed_fields đúng, current = mới
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Yêu cầu: B' = B + sửa 1 dòng (`sell_price`, `total_sales_raw` nhất quán) → đúng 1 version_no = 2; `changed_fields_json` = {`sell_price`: {old,new}, `total_sales_raw`: {old,new}} nguyên văn; version 1 đọc lại nguyên vẹn; `current_source_version_id` = version 2; 1 cờ `SOURCE_CHANGED` với `from/to_version_id` đúng; `SUM(total_sales)` đổi đúng delta; đổi PII (customer/phone) trên một dòng khác → `SAME`, không cờ.


Đã chạy: Slice A (S080): B' = B + sửa 1 dòng (`sell_price` + `total_sales_raw` nhất quán) → đúng 1 `version_no = 2`; `changed_fields_json` = `{"sell_price": {old,new}, "total_sales_raw": {old,new}}` nguyên văn; version 1 đọc lại nguyên vẹn (`changed_fields_json = NULL`); `current_source_version_id` = version 2; 1 cờ SOURCE_CHANGED với `from/to_version_id` đúng; `SUM(total_sales)` đổi đúng delta (+1.000.000), số dòng hiện hành không đổi. Đổi PII trên một dòng → `SAME`, 0 cờ (test tham số hoá 8 trường PII/vị trí dòng).
Executed By:
S080 — PRA-002 Slice A Implementation (2026-09-02)

Timestamp:
2026-09-02

#### CHECK-PRA002-06 — Coverage state machine + xác nhận tường minh
Priority:
REQUIRED

Status:
PASS

Slice A (S080) đã chạy PHẦN ĐẦU: header dạng (1) và (2) parse đúng
`header_date_*`; `HEADER_CONSISTENT` khi header bao trọn DETECTED; 6 dạng lạ
(kể cả `1/9/2026` thiếu số 0 và ngày 31/02) → `DETECTED_ONLY` + `header_text`
vẫn lưu nguyên văn; test khẳng định slice A KHÔNG có đường nào ghi ra
`CONFIRMED_COMPLETE`. Phần `POST xac-nhan-du` đã chạy ở **slice B (S083)** —
check đóng ở phiên đó, không phải dựa trên phần đầu.

Evidence Level:
E1

Evidence:
Yêu cầu: header dạng (1) và (2) → `header_date_*` đúng, `HEADER_CONSISTENT` khi bao DETECTED; header lạ → `DETECTED_ONLY`, `header_text` lưu; không API/route nào khác đặt `CONFIRMED_COMPLETE`; `POST xac-nhan-du` với khoảng không bao DETECTED → 400 và trạng thái không đổi; khoảng > 366 ngày → 400; hợp lệ → `CONFIRMED_COMPLETE` + `confirmed_*`; lần 2 → 409. Test tĩnh: chuỗi `'CONFIRMED_COMPLETE'` chỉ được gán trong đúng một hàm repository do route xác nhận gọi.

Kết quả S083 (chi tiết: `docs/sessions/S083-pra-002-slice-b-coverage-semantics.md`):
GET trang chưa xác nhận → 200, `<input name="xac_nhan">` KHÔNG có `checked` (mặc định không tick);
POST thiếu `xac_nhan` → 400 "Chưa tích ô xác nhận", `coverage_state` KHÔNG đổi;
POST khoảng không bao DETECTED → 400, nêu đúng ngày lệch (`2026-01-20`), `confirmed_at` = NULL;
POST khoảng > 366 ngày → 400 (đúng 366 ngày ĐƯỢC nhận, 367 thì không — test ranh giới);
POST hợp lệ → 302 PRG, `coverage_state = CONFIRMED_COMPLETE`, `confirmed_range_* = 2026-01-01 → 2026-01-31`, `confirmed_by = NULL`;
POST lần 2 → 409, bản ghi snapshot y hệt trước đó, cờ REMOVED không nhân đôi;
POST snapshot không tồn tại → 404.
Khoảng hiển thị trên form == khoảng đã lưu (`value="2026-01-05"`/`value="2026-01-20"` == `detected_date_min`/`max`).
Test tĩnh AST (`tests/test_snapshot_repository.py`):
`test_confirmed_complete_is_written_by_exactly_one_function` — duyệt toàn bộ `app/**/*.py`, chuỗi `CONFIRMED_COMPLETE` chỉ được gán cho `coverage_state` tại `{app/web/history_store.py}`, trong hàm `confirm_coverage`;
`test_only_the_confirmation_function_updates_the_snapshot_row` — mọi `update(source_snapshot)` nằm trong `confirm_coverage` và tập cột ghi == `{coverage_state, confirmed_range_start, confirmed_range_end, confirmed_at, n_removed_candidate}`.
Tầng thuần không bao giờ trả `CONFIRMED_COMPLETE` (test tích 3 header × 3 khoảng, gồm "đúng trọn tháng" và "thấy ngày cuối tháng").
Chạy trên PostgreSQL 16.13 thật với fixture golden qua pipeline authoritative.

Executed By:
S083 — PRA-002 Slice B Implementation (nhánh `claude/pra-002-slice-b-snapshot-8rbwip`, BASE_SHA `27b9d1c5`)

Timestamp:
2026-09-02

#### CHECK-PRA002-07 — NOT_SEEN vs REMOVED_CANDIDATE, không xoá, vẫn tính
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Yêu cầu: B'' = B' bỏ 1 dòng → trước xác nhận: 1 cờ `NOT_SEEN_IN_LATEST_SNAPSHOT`, 0 `REMOVED`; sau xác nhận đủ tháng 01/2026: 1 cờ `REMOVED_IN_SOURCE_CANDIDATE`; dòng đó vẫn trong `order_line_current`, vẫn trong `SUM(total_sales)` và `COUNT(order_key)`; `COUNT(*)` mọi bảng fact không giảm; xác nhận với snapshot không chồng khoá → 0 REMOVED.

Kết quả S083 trên PostgreSQL 16.13 thật, fixture golden `period_2026_01.xlsx` qua pipeline authoritative
(chi tiết: `docs/sessions/S083-pra-002-slice-b-coverage-semantics.md`):
B (351 dòng / 254 đơn / 3.562.310.000 VND) → B'' (bỏ đúng 1 dòng, khoá `BH64081`, 20.900.000 VND):
`n_same = 350`, `n_not_seen = 1`, `n_removed_candidate = 0`; cờ NOT_SEEN = 1, REMOVED = 0;
hiện hành 351 dòng / 254 đơn / 3.562.310.000 VND — KHÔNG ĐỔI.
Sau `POST xac-nhan-du` 01–31/01: `coverage_state = CONFIRMED_COMPLETE`, REMOVED = 1 (đúng khoá `BH64081`);
hiện hành 351 dòng / 254 đơn / 3.562.310.000 VND — KHÔNG ĐỔI tới từng đồng;
bảng fact trước → sau: `order_line_source_version` 351 → 351, `order_line_current` 351 → 351,
`snapshot_line` 351 → 701, `order_line_result_version` 351 → 701, `reconciliation_flag` 0 → 2 — KHÔNG bảng nào giảm;
cờ NOT_SEEN cũ của cùng khoá giữ nguyên bên cạnh cờ REMOVED (append-only); `acknowledged_at` = NULL.
Lịch sử `order_line_source_version` so nguyên văn từng dòng trước/sau: bằng nhau.
NOT_SEEN được dựng ở CẢ HAI mức chưa xác nhận (`DETECTED_ONLY` và `HEADER_CONSISTENT`) — test tham số hoá.
Ranh giới phạm vi (mục 8 bước 4 và bước R): B đã lưu rồi upload A (cắt ≤ 10/01, 89 dòng) →
`n_not_seen = 0`; xác nhận A cho ĐÚNG 01–10/01 → REMOVED = 0 (đơn 11–31/01 KHÔNG là ứng viên);
xác nhận A cho cả tháng 01–31 → REMOVED = 262 (= 351 − 89); cả hai: hiện hành KHÔNG đổi.
Chồng kỳ A ⊂ B: `n_same = 89`, `n_insert = 262`, `n_not_seen = 0`, 0 cờ; xác nhận B → REMOVED = 0.
Xuất hiện trở lại: cờ BẤT BIẾN (2 → 2, không cờ nào bị xoá/sửa), trạng thái "còn hiệu lực" DẪN XUẤT lúc đọc.
Loại trừ fail-safe có test riêng: `sale_date` NULL, ngày ngoài phạm vi, khoá `ORDER_KEY_COLLISION`, phạm vi mở.

Executed By:
S083 — PRA-002 Slice B Implementation (nhánh `claude/pra-002-slice-b-snapshot-8rbwip`, BASE_SHA `27b9d1c5`)

Timestamp:
2026-09-02

#### CHECK-PRA002-08 — RESULT_REVISED: source version không đổi, result version mới
Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E1

Evidence:
Yêu cầu: cùng file, capture Tracking thứ hai làm ≥ 1 dòng PENDING → AUTO (hoặc đổi `accounting_purchase_price`) → `n_source_changed = 0`, `COUNT(version_no > 1) = 0`, cờ `RESULT_REVISED` đúng số dòng đổi với `detail_json` (old,new) 3 trường; `current_result_version_id` trỏ run mới; dòng đổi trường ngoài 3 trường (ví dụ `price_source` nhãn) → 0 cờ nhưng result version vẫn ghi đủ.

Executed By:
...

Timestamp:
...

### Security / Data / API / Regression

#### CHECK-PRA002-09 — Append-only fact + UNIQUE chặn double-insert
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Yêu cầu: grep `app/web/history_store.py` + `history_writer`: 0 `delete(`; `update(` chỉ trên `order_line_current` và cột confirm của `source_snapshot`; test hành vi 3 snapshot → version chỉ tăng; test hai connection chen nhau INSERT version 1 cùng khoá → `IntegrityError` ở cái sau, rollback, DB còn đúng 1 version.


Đã chạy: Slice A (S080): kiểm tĩnh bằng AST (không grep chuỗi) — 0 lời gọi `delete()` trong `history_store.py`/`history_writer.py`, `delete` không được import từ sqlalchemy; `update()` chỉ trên `legacy_import` (PRA-001) và `order_line_current`. Hành vi: 3 snapshot liên tiếp → `version_no [1,2,3]`, đọc lại đủ giá trị cũ, đúng 1 dòng hiện hành. Concurrency: INSERT thứ hai cùng `(khoá, version_no=1)` → `IntegrityError`, rollback, DB còn đúng 1 version.
Executed By:
S080 — PRA-002 Slice A Implementation (2026-09-02)

Timestamp:
2026-09-02

#### CHECK-PRA002-10 — Fail-closed một đơn vị công việc
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Yêu cầu: (a) DB lỗi khi ghi → HTTP 500 thông điệp hiện có, `store.list_runs()` không có run mới, 0 snapshot; (b) R2 fake client lỗi ở `create_run` → rollback, 0 snapshot, 0 run; (c) dev không history → `/run` 302 và trang hiển thị "KHÔNG được lưu lịch sử"; (d) run có trên store nhưng không có snapshot → tab Dữ liệu gắn nhãn "KHÔNG CÓ LỊCH SỬ (ghi lỗi)"; (e) production `REPORTS_REQUIRE_HISTORY_DB=1` thiếu URL → không khởi động (test đã có giữ PASS).


Đã chạy: Slice A (S080): (a) ghi lịch sử lỗi → HTTP 500, `list_runs()` rỗng, 0 snapshot; (b) `store.create_run` lỗi → rollback, 0 snapshot, 0 source version, 0 run; (c) dev không history → `/run` 302 và trang kết quả hiện "Run này KHÔNG được lưu lịch sử — history store chưa cấu hình"; (d) run có mà snapshot không → tab Dữ liệu gắn nhãn "KHÔNG CÓ LỊCH SỬ (ghi lỗi)"; (e) `REPORTS_REQUIRE_HISTORY_DB=1` thiếu URL → không khởi động (test cũ giữ PASS). Test: `tests/test_web_history.py`.
Executed By:
S080 — PRA-002 Slice A Implementation (2026-09-02)

Timestamp:
2026-09-02

#### CHECK-PRA002-11 — Golden Baseline + regression + exporter parity
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Yêu cầu: `tests/test_golden_baseline.py` = `58 passed, 2 skipped`; full suite ≥ `1608 passed`, `11 skipped` không tăng; `tests/test_demo.py` PASS; test `excel_exporter.present_lines is excel_exporter._present_lines`; `git diff` của `app/modules/**` chỉ gồm alias (đếm dòng ≤ 4); `git diff --check` sạch.


Đã chạy: Slice A (S080): `tests/test_golden_baseline.py` = `58 passed, 2 skipped` (không đổi); full suite `1710 passed, 11 skipped` (baseline `1608 passed, 11 skipped` — +102 test mới, số skip KHÔNG tăng); `tests/test_demo.py` PASS; `excel_exporter.present_lines is excel_exporter._present_lines` (và `PresentedLine is _PresentedLine`); `git diff` của `app/modules/**` = đúng 3 dòng thêm (2 alias + 1 comment); `git diff --check` sạch.
Executed By:
S080 — PRA-002 Slice A Implementation (2026-09-02)

Timestamp:
2026-09-02

#### CHECK-PRA002-12 — Ranh giới ADR-101 / protected core
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Yêu cầu: `tests/test_history_db.py::test_no_module_under_app_imports_a_database_driver_or_alembic` PASS; `app/history/**` không import `sqlalchemy`/`psycopg`/`alembic`/`flask`; không file nào ngoài Touch Area thay đổi (`git diff --name-only BASE..HEAD` liệt kê nguyên văn); Tracking không đổi; `scripts/branch_authority_check.sh` = `AUTHORITY_OK`.


Đã chạy: Slice A (S080): `test_no_module_under_app_imports_a_database_driver_or_alembic` PASS; test riêng duyệt `app/history/**` khẳng định không import `sqlalchemy`/`psycopg`/`alembic`/`flask`; scope audit `git diff --name-only BASE..HEAD` không chạm protected core/Tracking/config/data/fixture/render/Dockerfile (danh sách nguyên văn ở handoff S080, kèm ghi chú tường minh về `app/web/templates/index.html` +3 dòng nằm ngoài Allowed nhưng không thuộc do-not-touch); `scripts/branch_authority_check.sh` = `AUTHORITY_OK`.
Executed By:
S080 — PRA-002 Slice A Implementation (2026-09-02)

Timestamp:
2026-09-02

#### CHECK-PRA002-13 — Không PII trong bảng PRA-002
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Yêu cầu: test duyệt `schema.METADATA` 6 bảng mới: không cột nào trong {`customer`, `customer_code`, `phone`, `address`, `shipper_raw`}; sau kịch bản CHECK-05 (đổi PII) `changed_fields_json` không chứa khoá PII; trang snapshot không render PII (grep HTML response).


Đã chạy: Slice A (S080): test duyệt `schema.METADATA` 6 bảng mới — không cột nào trong {`customer`, `customer_code`, `phone`, `address`, `shipper_raw`}; `SourceLine`/`ResultLine` không mang trường PII (test `repr`); `changed_fields`/`detail_json` không chứa khoá PII; trang `/du-lieu/snapshot/<id>` không render 5 giá trị PII giả cài trong fixture (grep HTML response).
Executed By:
S080 — PRA-002 Slice A Implementation (2026-09-02)

Timestamp:
2026-09-02

#### CHECK-PRA002-14 — Real Data Acceptance RDA-1..6 trên workbook thật
Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E1

Evidence:
Yêu cầu: bảng mục 15, mỗi bước có output HTTP/CLI + SQL count nguyên văn; SHA256 workbook trước/sau không đổi; ghi rõ đường ưu tiên (hai export thật) hay controlled copy (ASSUMPTION D14). Thiếu file → `NOT_TESTED` + gate Owner.

Executed By:
...

Timestamp:
...

#### CHECK-PRA002-15 — Production Acceptance trên Render PostgreSQL
Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E1

Evidence:
Yêu cầu: mục 16 bước 1–6; SHA deploy = HEAD canonical sau Controlled Integration; `alembic_version = 0002_snapshots`; upload thật 302 + snapshot hiện; upload lại `n_same = line_count`; không OOM. Do Owner thực hiện (session không có egress). Nếu quá 30 ngày chưa deploy → V4.1 §9 `OWNER DECISION REQUIRED` (A cung cấp / B `POST_MERGE_PRODUCTION_ACCEPTANCE` / C gỡ khỏi gate).

Executed By:
...

Timestamp:
...

#### CHECK-PRA002-16 — Bộ nhớ end-to-end với writer
Priority:
RECOMMENDED

Status:
PASS

Evidence Level:
E1

Evidence:
Yêu cầu: `ru_maxrss` route `/run` (app boot + upload golden 351 dòng + writer, SQLite hoặc PG) < 300 MB một worker; so với baseline S078R (81.9 MB legacy) — ghi số đo.


Đã chạy: Slice A (S080): `ru_maxrss` end-to-end `/run` (app boot + upload golden 351 dòng + writer, SQLite) = **75,6 MB** (app boot 64,2 MB); kịch bản A→A→B→B' trên PostgreSQL 16 = 78,7 MB. Mục tiêu < 300 MB ĐẠT; baseline S078R legacy 81,9 MB.
Executed By:
S080 — PRA-002 Slice A Implementation (2026-09-02)

Timestamp:
2026-09-02

#### CHECK-PRA002-17 — Independent Review E2
Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E2

Evidence:
Yêu cầu: `docs/reviews/TASK-PRA-002-INDEPENDENT-REVIEW-RECORD` theo `governance/templates/E2_INDEPENDENT_REVIEW_TEMPLATE.md`; reviewer chạy lại CHECK-03/04/05/07/09 độc lập; `BLOCKING_FINDINGS = 0` sau ≤ 2 repair cycle; ledger cập nhật `base_sha/head_sha` từng cycle.


Đã chạy MỘT PHẦN (slice A, S081): `docs/reviews/TASK-PRA-002-SLICE-A-INDEPENDENT-REVIEW-RECORD.md`. Reviewer tự chạy lại CHECK-03/04/05/09 (E2) trên lineage `7fad3f7..80c6fe1`, cộng migration up/down trên PostgreSQL 16.13 thật. Một finding BLOCKING (FIND-PRA002-A1 — version mới đánh số theo hiện hành thay vì max, mục 5.3; sau `ORDER_KEY_COLLISION` mọi upload sau trên khoá đó vi phạm UNIQUE và `/run` trả 500) đã sửa trong repair cycle 1/2; sau repair `BLOCKING_FINDINGS = 0`, full suite `1711 passed, 11 skipped`, Golden `58 passed, 2 skipped`. Check TOÀN TASK vẫn `NOT_TESTED` vì CHECK-07 (slice B) và CHECK-08 (slice C) chưa tồn tại để chạy lại.
Executed By:
S081 — PRA-002 Slice A Independent Review (2026-09-02) — phần slice A

Timestamp:
2026-09-02

## Tiêu Chí Hoàn Thành (Exit Criteria)
- [ ] 100% REQUIRED checks PASS (01–15, 17); 16 RECOMMENDED có số đo.
- [ ] Không có lỗi nghiêm trọng (critical) chưa xử lý; `BLOCKING_FINDINGS = 0`.
- [ ] Đạt mức evidence yêu cầu (Risk 4 → E1; 04/05/07/09 có E2 qua CHECK-17).
- [ ] Tài liệu bắt buộc đã được cập nhật (DEC, ledger, review record, `docs/deployment/S071_DEPLOYMENT.md`).
- [ ] Tiến độ dự án đã được cập nhật (`PROJECT/PROJECT_PROGRESS.md`, `PROJECT/LO_TRINH_DE_HIEU.md`).
- [ ] Đã viết Session Handoff cho từng session A/B/C/review/close-out.

## Điều Kiện Kích Hoạt Leo Thang (Escalation Triggers)
- Cần chạm file trong "Không được đụng" → `SCOPE EXPANSION REQUIRED`, dừng.
- Production Python > 1.500 dòng → `CHANGE_BUDGET_EXCEEDED`, dừng.
- RDA gặp hình dạng dữ liệu thật ngoài contract (header dạng 3, BH không `BH\d+`, đơn nhiều ngày/nhiều NV, dòng cùng sản phẩm dịch chuyển hàng loạt) → `UNKNOWN / OWNER_DECISION_REQUIRED`, không mở rộng thuật toán.
- Cờ `ORDER_KEY_COLLISION` đầu tiên trên production → `OWNER_DECISION_REQUIRED` (N.13).
- Cần đổi `RunStore`/R2/Dockerfile/render.yaml → `ARCHITECTURE_CHANGE_REQUIRED`.
- Bất kỳ đề xuất `DELETE`/`UPDATE` fact, "merge" hai dòng, hay tự chọn giá trị đúng giữa cũ/mới → `DATA_INTEGRITY_RISK`, dừng.
- Independent Review > 2 blocking repair cycle → `OWNER_EXTENSION REQUIRED`.

## Đăng Ký File Đã Thay Đổi (Changed Files Registry)

Created (S079 — finalization):
- `docs/tasks/TASK-PRA-002-pipeline-persistence-reconciliation.md`
- `docs/sessions/S079-pra-002-roadmap-finalization.md`

Modified (S079):
- `PROJECT/PROJECT_PROGRESS.md`
- `PROJECT/LO_TRINH_DE_HIEU.md`
- `PROJECT/PROJECT_DECISIONS.md` (DEC-171)
- `PROJECT/REVIEW_BUDGET_LEDGER.md` (Root Task: TASK-PRA-002)

Created (S083 — slice B):
- `tests/test_history_coverage_confirmation.py`
- `tests/test_snapshot_absence.py`
- `docs/sessions/S083-pra-002-slice-b-coverage-semantics.md`

Modified (S083 — slice B):
- `app/history/coverage.py` (nhãn coverage, `parse_iso_date`, `confirmation_error`)
- `app/history/models.py` (`FLAG_NOT_SEEN`, `FLAG_REMOVED_CANDIDATE`, `ABSENCE_FLAG_KINDS`, `CurrentKey`)
- `app/history/reconciler.py` (`absent_keys` — hàm thuần dùng chung bước 4 và bước R)
- `app/web/history_store.py` (bước 4, `confirm_coverage`/bước R, dẫn xuất `is_active`)
- `app/web/server.py` (`POST /du-lieu/snapshot/<id>/xac-nhan-du`, `_snapshot_page`)
- `app/web/templates/snapshot.html`, `app/web/templates/du_lieu.html`
- `tests/test_snapshot_repository.py`, `tests/test_web_history.py`,
  `tests/test_pipeline_history_vertical.py`
- `PROJECT/PROJECT_PROGRESS.md`, `PROJECT/REVIEW_BUDGET_LEDGER.md`

Deleted:
- (không)

Migration Impact:
- S079: không. Slice A: `0002_snapshots` (+6 bảng, không đổi bảng cũ) — mục 13.
- S083 (slice B): **KHÔNG có migration mới**. `0002_snapshots` đã có sẵn
  `coverage_state` CHECK gồm `CONFIRMED_COMPLETE`, bốn cột `confirmed_*`,
  `n_not_seen`/`n_removed_candidate`, và `reconciliation_flag.kind` CHECK gồm
  `NOT_SEEN_IN_LATEST_SNAPSHOT`/`REMOVED_IN_SOURCE_CANDIDATE`. `ALEMBIC_HEAD`
  giữ nguyên `0002_snapshots`; `tools/db/**` không có một thay đổi nào.

## Ghi Chú (Notes)
- Code hiện tại là implementation evidence, không phải business authority:
  mọi rule ở mục 3.5 ghi loại; `INFERENCE` có thể bị Owner bác bỏ bằng
  một DEC mới mà không đổi kiến trúc (ví dụ đổi tập trường fingerprint).
- `PRA002_READY_FOR_IMPLEMENTATION = YES` — không có OWNER_DECISION_REQUIRED
  chặn vertical tháng 09/2026; các UNKNOWN đều có fail-safe + re-trigger.
- Nếu Owner cung cấp được HAI export thật (giữa tháng + cuối tháng) trước
  slice C, RDA-3 dùng chúng và ASSUMPTION D14 được đóng bằng bằng chứng.
