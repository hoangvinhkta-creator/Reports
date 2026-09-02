# TASK-PRA-001 — Legacy Reference Vertical (Excel cũ → Import → Persist → Query → Hiển thị)

## Metadata
Status:
PLANNED

Phase:
PHASE-PRA — Slice 1

Task Mode:
MAJOR

Primary Agent Tier:
Tier B (implementation)

Escalation Tier:
Tier C (schema/migration, fail-closed startup); Owner (mọi business semantics)

Difficulty:
3/5

Risk:
3/5

Blast Radius:
3/5 — failure path: số cũ hiển thị sai/thiếu nhãn LEGACY khiến Owner đọc nhầm số cũ thành số pipeline; DB history sai cấu hình làm production không khởi động. Không chạm pipeline, không chạm KPI/lương.

Project Profile:
PRODUCT

Root task lineage (V4.1): `TASK-PRA-001` (root mới). Review budget: MEDIUM =
1 blocking repair cycle (`governance/core/V4_1_POLICY_FREEZE.md` §2).

Kế hoạch gốc: `docs/tasks/TASK-PRA-000-persistent-reporting-analytics-plan.md`
(mục G, M — Slice 1; phụ lục Finalization S073). Quyết định nền:
`docs/adr/ADR-108-persistent-history-store.md` (Proposed — chờ Owner),
`docs/adr/ADR-109-web-layer-flask-jinja.md` (Accepted).

Quy ước: file DỰ KIẾN tạo được viết không kèm phần mở rộng; file đã tồn tại
viết đủ đường dẫn.

## Mục Tiêu (Objective)

Owner mở Reports → vào tab "Dữ liệu" hoặc "Nhân viên" → chọn kỳ lịch sử
(tháng/năm) → nhìn được số liệu Summary cũ (tháng × người bán) và doanh số
theo ngày (DataChart) đúng như Excel, mọi số đeo badge LEGACY, ô có lỗi
công thức đã biết có dấu nhắc — không cần mở workbook Excel để xem summary
cơ bản. Đồng thời tạo **nền persistence tối thiểu** (engine + migration +
repository interface) mà PRA-002 mở rộng được không phá.

## Phạm Vi (Scope)

IN_SCOPE:
1. **Nền history DB tối thiểu**: `tools/db/` (mới — engine builder từ
   `HISTORY_DATABASE_URL`; SQLite mặc định cho local/test; fail-closed
   `REPORTS_REQUIRE_HISTORY_DB=1`), Alembic env + migration `0001_legacy`
   (bốn bảng mục "DATA_MODEL_MINIMUM"). Dependency mới: extra `history`
   (`sqlalchemy>=2.0`, `alembic>=1.13`, `psycopg[binary]>=3.1`) gộp vào
   `web-prod`.
2. **Legacy importer** (`app/legacy/` mới, thuần openpyxl, không I/O DB):
   đọc `Summary 2026`, `Summary 2025`, `DataChart 2026` → record bất biến;
   giữ giá trị nguyên trạng + `formula_text`; annotate `known_defects` bằng
   kiểm tra CẤU TRÚC công thức (số SP không nguyên, tổng tháng có range
   loại dòng người bán, tham chiếu sheet không khớp `seller_label`, mẫu
   số là hằng số) — tham chiếu A1/A2/A4/A6 của
   `docs/analysis/05_EXCEPTIONS.md`; **không** sửa giá trị.
3. **Repository** `app/web/history_store` (mới): `LegacyRepository`
   (create_import / list_imports / set_current / query_summary(year, month|None)
   / query_daily(year, month)) dùng SQLAlchemy Core, engine tiêm được.
4. **Web**: route `POST /du-lieu/legacy` (upload workbook legacy — tái dùng
   validation `.xlsx` ≤ 25 MB, tên file server sinh, file tạm xoá sau
   import); `GET /du-lieu` (mở rộng `/history` hiện có thành tab "Dữ liệu":
   danh sách run hiện có + danh sách legacy import/version); `GET /nhan-vien`
   (ma trận tháng × người bán từ legacy, bộ chọn năm/tháng, badge LEGACY,
   dấu nhắc known_defect, đơn vị "nghìn đồng (số cũ)"); `GET /doanh-so-ngay`
   (bảng ngày × tháng từ DataChart, VND).
5. **Base layout + CSS token** (`app/web/static/css/` mới, chép token
   `--tp-*` và class bảng/tab/badge từ Tracking theo mục E của TASK-PRA-000;
   không hot-link, không JS Tracking); template `layout` với tab bar cho các
   trang ĐÃ có (Chạy báo cáo, Dữ liệu, Nhân viên, Doanh số ngày). Không dựng
   tab trống "sắp có".
6. Tài liệu: cập nhật `docs/deployment/S071_DEPLOYMENT.md` (bước tạo
   Postgres + dán `HISTORY_DATABASE_URL`), `render.yaml` (2 biến mới),
   session handoff, PROGRESS/LO_TRINH.

## Ngoài Phạm Vi (Out of Scope)
- Import 56 sheet chi tiết `MM.2026 <tên>` (`legacy_detail_line`) — chỉ khi
  slice sau cần đối chiếu theo ngày; PII legacy không import.
- Mọi bảng `source_snapshot` / version / reconciliation (PRA-002).
- Tổng quan, so kỳ trước, target, KPI pipeline trên web (PRA-003).
- Diff giữa hai bản legacy trên UI (chỉ ghi version + is_current).
- Biểu đồ; dark mode; mobile polish; retention; `uploaded_by`.
- Bất kỳ thay đổi nào ở `app/modules/**`, `app/pipeline.py`,
  `app/composition.py`, exporter, `RunStore`/R2, Tracking.
- Backup `pg_dump` lên R2 (PRA-002 hardening).

## Phụ Thuộc (Dependencies)
- Owner approve `ADR-108` (Postgres hybrid) — **BLOCKING cho production
  deploy**, không chặn implement + test local (SQLite).
- Owner tạo Render Postgres + dán `HISTORY_DATABASE_URL` khi deploy.
- File Excel "Báo cáo Kinh doanh 2026.xlsx" có mặt lúc chạy acceptance
  thật (không commit).

## Chặn (Blocks)
- TASK-PRA-002 (dùng chung engine/migration chain/`history_store`/tab Dữ liệu).

## An Toàn Để Chạy Song Song Với (Parallel-Safe With)
- TASK-REM-T06 (root hygiene). Không song song với bất kỳ task nào chạm
  `app/web/server.py`.

## Phạm Vi Tác Động Dự Kiến (Expected Touch Area)

Allowed:
- `tools/db/` (mới), `alembic.ini` + thư mục migration (mới), `app/legacy/` (mới),
  `app/web/history_store` (mới), `app/web/server.py` (+ route, + khởi tạo
  engine qua `history_store.build()` với tham số tiêm cho test),
  `app/web/templates/` (layout + 3 template mới, sửa `history.html`),
  `app/web/static/css/` (mới), `pyproject.toml` (extra `history`),
  `render.yaml`, `Dockerfile` (chỉ nếu cần `alembic upgrade` ở entrypoint),
  `tests/` (mới), `docs/`, `PROJECT/`.

Không được đụng vào nếu chưa có Scope Expansion:
- `app/modules/**`, `app/pipeline.py`, `app/composition.py`,
  `app/owner_usability.py`, `app/demo.py`, `app/web/storage_backend.py`,
  `app/web/run_registry.py`, `tools/storage/**`, `tools/tracking/**`,
  `config/**`, `data/**`, `tests/fixtures/golden/**`, mọi thứ ở Tracking.

## DATA_MODEL_MINIMUM (migration 0001_legacy)

```
legacy_import
  import_id TEXT PK · origin TEXT NOT NULL CHECK = 'LEGACY_REFERENCE' · source_file_name TEXT ·
  file_fingerprint TEXT NOT NULL · file_size INT · imported_at TIMESTAMP · imported_by TEXT NULL ·
  version_label TEXT · sheets_imported JSON(text) · is_current BOOL · notes TEXT
  UNIQUE(file_fingerprint)  -- upload lại đúng file → không tạo import mới (báo "đã có")

legacy_summary_row
  id PK · import_id FK · year INT · month INT · seller_label TEXT · row_kind TEXT CHECK IN ('SELLER','MONTH_TOTAL','PROGRESS','YEAR_TOTAL') ·
  sheet_name TEXT · sheet_row INT · unit TEXT NOT NULL DEFAULT 'kVND' ·
  orders NUMERIC · products NUMERIC · sales NUMERIC · converted_revenue NUMERIC · profit NUMERIC · margin_ratio NUMERIC ·
  vs_prev_month_ratio NUMERIC · stock_ratio NUMERIC · actual_profit NUMERIC · per_day NUMERIC · target NUMERIC · vs_target_ratio NUMERIC ·
  bonus NUMERIC · workdays NUMERIC · base_salary NUMERIC · allowance NUMERIC · total_salary NUMERIC ·
  formula_text JSON(text) · known_defects JSON(text)
  UNIQUE(import_id, sheet_name, sheet_row)

legacy_daily_sales
  id PK · import_id FK · year INT · month INT · day INT · sales_vnd NUMERIC · source_sheet TEXT
  UNIQUE(import_id, year, month, day)

legacy_monthly_reference
  id PK · import_id FK · year INT · month INT · sales_current_year_vnd NUMERIC · sales_prev_year_vnd NUMERIC ·
  vs_last_year_ratio NUMERIC · vs_target_ratio NUMERIC · target_year NUMERIC · average_per_day NUMERIC · target_per_day NUMERIC · formula_text JSON(text)
  UNIQUE(import_id, year, month)
```

Extension point cho PRA-002 (không tạo ở PRA-001, chỉ đảm bảo không dead-end):
cùng engine/migration chain (`0002_snapshots`), cùng quy ước cột `origin`
tường minh trên mọi bảng fact, `history_store` thêm `SnapshotRepository`
cạnh `LegacyRepository`, tab "Dữ liệu" đã có khung danh sách để thêm
snapshot, bộ chọn kỳ dùng lại. Khoá đơn ở PRA-002 là chuỗi opaque
`order_key` + cột riêng `bh_number`, `bh_year_hint` để namespace theo năm
chỉ bằng một migration nếu Owner xác nhận BH reset (không áp business rule
ở PRA-001).

## Subtask (Subtasks)
- [ ] PRA-001.1 Nền DB: `tools/db/` engine builder + fail-closed + Alembic `0001_legacy` (SQLite up/down PASS).
- [ ] PRA-001.2 Importer thuần + fixture Excel legacy tổng hợp (anonymized, cố ý chứa A1/A2/A4/A6) + test fidelity/no-recalc/defect-annotation.
- [ ] PRA-001.3 `LegacyRepository` + test round-trip, is_current, fingerprint trùng.
- [ ] PRA-001.4 Route upload + `/du-lieu` + `/nhan-vien` + `/doanh-so-ngay` + layout/CSS token + test Flask.
- [ ] PRA-001.5 Chạy file Excel thật (máy Owner hoặc session có file) → script đối chiếu ô → E1.
- [ ] PRA-001.6 `render.yaml` + deployment doc + handoff + PROGRESS/LO_TRINH; full regression; validators.

## Ready Gate
Dùng `governance/core/TASK_READY_GATE_STANDARD.md`.

- [x] Kế hoạch gốc đã được Owner review (`PLANNING_REVIEW = PASS`, S073).
- [x] Decision A/B/C/D/E đã chốt (DEC-166); Decision B/C/D không ảnh hưởng PRA-001.
- [x] Scope Lock ở trên; Out of Scope tường minh; Change Budget đã đặt.
- [x] Completion Gate bên dưới đã FROZEN (S073).
- [ ] Owner approve `ADR-108` (ghi DEC) — cần trước khi **deploy** production; implement local không chờ.
- [ ] File Excel legacy có trên máy chạy acceptance (PRA-001.5).
- [ ] Đồng bộ nhánh đầu session (`git remote show origin` → HEAD branch, fetch, so HEAD).

## Completion Gate
Dùng `governance/core/TASK_COMPLETION_GATE_STANDARD.md` và `governance/core/EVIDENCE_STANDARD.md`.
FROZEN tại S073 (2026-09-02). Risk 3 → mọi REQUIRED phải E1.

### Functional

#### CHECK-PRA001-01 — Importer fidelity 100 % trên file thật
Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E1

Evidence:
Script đối chiếu (đọc lại Excel bằng openpyxl `data_only=True`, so từng ô với bản ghi DB) in `matched=N mismatched=0` cho toàn bộ ô số của `Summary 2026`, `Summary 2025`, `DataChart 2026`.

Executed By:
...

Timestamp:
...

#### CHECK-PRA001-02 — Không tính lại số cũ
Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E1

Evidence:
Test: fixture có ô giá trị cố ý KHÔNG khớp công thức (ví dụ `F = 999` với công thức `=G/5.5%`) → DB lưu `999`, `formula_text` lưu công thức; grep `/2`, `/ 2`, `5.5%` trong `app/legacy/` = 0 kết quả trong logic (chỉ được xuất hiện trong chuỗi so khớp defect).

Executed By:
...

Timestamp:
...

#### CHECK-PRA001-03 — Known defects được annotate, không sửa
Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E1

Evidence:
Fixture chứa 4 mẫu A1/A2/A4/A6 → `known_defects` đúng mã trên đúng dòng; giá trị ô không đổi; UI hiện dấu nhắc trên đúng ô.

Executed By:
...

Timestamp:
...

#### CHECK-PRA001-04 — Origin và badge LEGACY
Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E1

Evidence:
Mọi bảng legacy có cột `origin` với CHECK constraint; test render `/nhan-vien` và `/doanh-so-ngay`: mọi giá trị số nằm trong phần tử mang badge/nhãn LEGACY và đơn vị; không có số nào hiển thị thiếu nhãn (assert trên HTML).

Executed By:
...

Timestamp:
...

#### CHECK-PRA001-05 — Bộ chọn kỳ và trang hiển thị đúng
Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E1

Evidence:
Flask test client: chọn (2026, 03) → ma trận đúng 7 dòng người bán/kênh + tổng tháng đúng số fixture; chọn kỳ không có dữ liệu → trạng thái rỗng trung thực, không 0.

Executed By:
...

Timestamp:
...

### Security / Data / API / Regression

#### CHECK-PRA001-06 — Fail-closed cấu hình DB
Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E1

Evidence:
`REPORTS_REQUIRE_HISTORY_DB=1` thiếu `HISTORY_DATABASE_URL` → app không khởi động (lỗi rõ); schema chưa `upgrade head` → không khởi động; DB lỗi khi request → HTTP 503, KHÔNG phải trang rỗng/"chưa có dữ liệu".

Executed By:
...

Timestamp:
...

#### CHECK-PRA001-07 — Upload an toàn, không lưu file, không PII
Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E1

Evidence:
Test: từ chối non-xlsx, > 25 MB, path traversal trong tên; file tạm bị xoá sau import (kể cả khi import lỗi); upload lại cùng fingerprint → không tạo import mới; bảng legacy không có cột tên khách/SĐT/địa chỉ.

Executed By:
...

Timestamp:
...

#### CHECK-PRA001-08 — Ranh giới kiến trúc và regression
Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E1

Evidence:
`test_no_module_under_app_reaches_the_network` PASS; không import `psycopg`/`alembic` dưới `app/`; `tests/test_golden_baseline.py` không đổi kết quả; full suite passed không giảm so với baseline lúc mở session (ghi số cụ thể); `git diff --check` sạch.

Executed By:
...

Timestamp:
...

#### CHECK-PRA001-09 — DDL tương thích PostgreSQL
Priority:
RECOMMENDED

Status:
NOT_TESTED

Evidence Level:
E1

Evidence:
`alembic upgrade head` trên một PostgreSQL thật (Render hoặc local) và `/nhan-vien` render từ Postgres. Nếu session không có Postgres → `BLOCKED` kèm lý do, và trở thành gate deploy của Owner.

Executed By:
...

Timestamp:
...

#### CHECK-PRA001-10 — Governance validators
Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E1

Evidence:
5 validator `governance/scripts/governance/*.py`: PASS, trừ 3 reference có sẵn của REM-T06 (ghi rõ nếu còn).

Executed By:
...

Timestamp:
...

## CHANGE_BUDGET
- Production Python mới: mục tiêu ≤ 450 dòng, ngưỡng dừng cứng 600 dòng
  (`tools/db` + `app/legacy` + `app/web/history_store` + delta `server.py`).
  Vượt → `CHANGE_BUDGET_EXCEEDED`, dừng, báo Owner.
- Template mới ≤ 300 dòng; CSS ≤ 450 dòng (token + class chép có chọn lọc).
- Test mới ≥ 25; không skip mới.
- Không thêm dependency ngoài `sqlalchemy`, `alembic`, `psycopg[binary]`.
- Hardening ≤ 10 % effort (ví dụ dark mode, retention) — chỉ khi 01–08 PASS.

## Tiêu Chí Hoàn Thành (Exit Criteria)
- [ ] 100% REQUIRED checks PASS
- [ ] Không có lỗi nghiêm trọng (critical) chưa xử lý
- [ ] Đạt mức evidence yêu cầu (E1)
- [ ] Tài liệu bắt buộc đã được cập nhật
- [ ] Tiến độ dự án đã được cập nhật (`PROJECT/PROJECT_PROGRESS.md`, `PROJECT/LO_TRINH_DE_HIEU.md`)
- [ ] Đã viết Session Handoff

## Điều Kiện Kích Hoạt Leo Thang (Escalation Triggers)
- Cần chạm bất kỳ file nào trong "Không được đụng" → `SCOPE EXPANSION REQUIRED`, dừng.
- Phát hiện ô Summary/DataChart mà ý nghĩa nghiệp vụ không rõ và ảnh hưởng cách lưu → `UNKNOWN / OWNER_DECISION_REQUIRED`, lưu nguyên trạng, không diễn giải.
- Vượt Change Budget → `CHANGE_BUDGET_EXCEEDED`.
- Owner từ chối ADR-108 → dừng trước bước deploy; implement local vẫn hợp lệ nhưng không merge canonical cho tới khi có nơi lưu production.

## Đăng Ký File Đã Thay Đổi (Changed Files Registry)

Created:
- (điền khi implement)

Modified:
- (điền khi implement)

Deleted:
- (không dự kiến)

Migration Impact:
- Thêm schema history (migration `0001_legacy`) trên DB MỚI; không đụng dữ liệu R2/run hiện có.

## Ghi Chú (Notes)
- Đơn vị: legacy lưu nguyên `kVND`; presentation hiển thị kèm nhãn; KHÔNG
  quy đổi trong DB.
- `Summary 2026` dòng 3 (`YEAR_TOTAL`, `SUM(E4:E902)/2`) và dòng "Tiến độ"
  lưu với `row_kind` riêng, không cộng vào ma trận.
- DataChart cột "Doanh số" khác Summary "Tổng bán" → lưu cả hai nguyên
  trạng, hiển thị ở hai trang khác nhau, KHÔNG đối chiếu hai số này với
  nhau (UNKNOWN).
