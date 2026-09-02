# TASK-PRA-001 — Legacy Reference Vertical (Excel cũ → Import → Persist → Query → Hiển thị)

## Metadata
Status:
IMPLEMENTED

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
`docs/adr/ADR-108-persistent-history-store.md` (Accepted — DEC-167),
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
- Owner đã approve `ADR-108` (DEC-167, 2026-09-02): Production DB =
  Managed PostgreSQL; Artifacts/run JSON/XLSX = R2; Local/test = SQLite;
  PRA-001 = minimum legacy schema only; schema PRA-002 = out of scope.
- Owner tạo Render Postgres + dán `HISTORY_DATABASE_URL` khi deploy.
- File Excel "Báo cáo Kinh doanh 2026.xlsx" có mặt lúc chạy acceptance
  thật (không commit).
- (DEC-169) Production import scope = `Summary 2026` + `DataChart 2026`.
  `Summary 2025` = REFERENCE_ONLY, không import/persist/query.

## Vai Trò Sheet — Production Import Scope (DEC-169)

Thẩm quyền Owner, xác lập trong Real Data Acceptance S075. Đây là ranh giới
scope, không phải kết quả của một repair.

| Sheet | Vai trò | Import | Persist | Query / Display |
|---|---|---|---|---|
| `Summary 2026` | `REQUIRED_IMPORT` | CÓ | CÓ | CÓ |
| `DataChart 2026` | `REQUIRED_IMPORT` | CÓ | CÓ | CÓ |
| `Summary 2025` | `REFERENCE_ONLY` | KHÔNG | KHÔNG | KHÔNG |

`Summary 2025` tồn tại trong workbook cũ để làm số tham chiếu cho báo cáo
2026. Trên file thật nó là sheet đã dán cứng: 0 ô công thức, 99 dòng
value-only. Nó nằm NGOÀI authoritative import scope — loại trừ tường minh
bằng `SUMMARY_REFERENCE_ONLY_SHEETS` trong `app/legacy/parser.py`, không
phải bằng cách bắt rồi bỏ qua lỗi.

Guard DEC-168 giữ nguyên hiệu lực trên các sheet `REQUIRED_IMPORT`: dòng có
giá trị nghiệp vụ mà contract phân loại không nhận ra vẫn phải FAIL TO.

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
- (Bổ sung S076, N03 — hai file frozen gate THỰC SỰ cần, thiếu trong bản
  liệt kê ban đầu; không phải scope mới) `app/web/legacy_presentation.py`
  (mới — nơi DUY NHẤT gắn badge LEGACY + đơn vị + dấu nhắc lỗi công thức,
  điều kiện để CHECK-PRA001-04 có thể đạt) và
  `tools/analysis/verify_legacy_import.py` (mới — script đối chiếu ô mà
  CHECK-PRA001-01 chỉ đích danh trong Evidence đã freeze).

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
- [x] PRA-001.1 Nền DB: `tools/db/` engine builder + fail-closed + Alembic `0001_legacy` (SQLite up/down PASS).
- [x] PRA-001.2 Importer thuần + fixture Excel legacy tổng hợp (anonymized, cố ý chứa A1/A2/A4/A6) + test fidelity/no-recalc/defect-annotation.
- [x] PRA-001.3 `LegacyRepository` + test round-trip, is_current, fingerprint trùng.
- [x] PRA-001.4 Route upload + `/du-lieu` + `/nhan-vien` + `/doanh-so-ngay` + layout/CSS token + test Flask.
- [ ] PRA-001.5 Chạy file Excel thật → script `tools/analysis/verify_legacy_import.py` ĐÃ VIẾT và chạy PASS trên fixture (`matched=628 mismatched=0`); file thật KHÔNG có trong Claude Cloud (`.gitignore: data/samples/`) → `WAITING_OWNER_INPUT`.
- [x] PRA-001.6 `render.yaml` + `Dockerfile` + deployment doc + handoff + PROGRESS/LO_TRINH; full regression; validators.

## Ready Gate
Dùng `governance/core/TASK_READY_GATE_STANDARD.md`.

- [x] Kế hoạch gốc đã được Owner review (`PLANNING_REVIEW = PASS`, S073).
- [x] Decision A/B/C/D/E đã chốt (DEC-166); Decision B/C/D không ảnh hưởng PRA-001.
- [x] Scope Lock ở trên; Out of Scope tường minh; Change Budget đã đặt.
- [x] Completion Gate bên dưới đã FROZEN (S073).
- [x] Owner approve `ADR-108` (DEC-167, 2026-09-02).
- [ ] File Excel legacy có trên máy chạy acceptance (PRA-001.5) — điều kiện vận hành, không phải quyết định; nếu thiếu, CHECK-PRA001-01 ghi NOT_TESTED và thành gate Owner.
- [ ] Đồng bộ nhánh đầu session (`git remote show origin` → HEAD branch, fetch, so HEAD) — thực hiện ở bước 0 của session implement.

## Completion Gate
Dùng `governance/core/TASK_COMPLETION_GATE_STANDARD.md` và `governance/core/EVIDENCE_STANDARD.md`.
FROZEN tại S073 (2026-09-02). Risk 3 → mọi REQUIRED phải E1.

### Functional

#### CHECK-PRA001-01 — Importer fidelity 100 % trên file thật
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
**Phạm vi (sửa đổi theo DEC-169, 2026-09-02).** Gate này FROZEN tại S073 với giả định `Summary 2025` phải được production-import. Owner bác bỏ giả định đó: production import scope = `Summary 2026` + `DataChart 2026`; `Summary 2025` = REFERENCE_ONLY (không import/persist/query). Sửa đổi này là `OWNER_SCOPE_CLARIFICATION`, KHÔNG phải repair — repair budget PRA-001 vẫn `0 remaining`, không bị tiêu. Ghi ở đây để việc đổi một frozen gate là auditable, không âm thầm.

**Fidelity gồm HAI phần** — `VALUE MATCH` + `SOURCE COVERAGE` (DEC-168, sau FIND-PRA001-R01). `matched=... mismatched=0` một mình KHÔNG được dùng làm bằng chứng completeness: verifier bản cũ duyệt DB → Excel nên không thể thấy dòng chưa từng được nhập. Verifier hiện tại duyệt Summary từ EXCEL → DB và in các con số coverage.

**Chạy thật trên FILE THẬT.** Workbook Owner cung cấp trong Claude Cloud session S075: `Báo cáo Kinh doanh 2026.xlsx`, SHA256 `4ffe51983306a16f507d3fe5fad6b0f2acf9bfe8b0486f30c83cb64398d11f72`, 3.022.121 bytes, 59 sheets. Workbook KHÔNG commit vào repo, KHÔNG sửa (SHA256 trước và sau khi chạy giống hệt nhau). DB acceptance = SQLite dùng một lần, ngoài repo, đã `alembic upgrade head`.

Import production tại `5bea87a` + scope DEC-169: `sheets_imported = ['Summary 2026', 'DataChart 2026']`, `summary_rows = 71` (toàn bộ từ `Summary 2026`), `daily_sales = 174`, `monthly_reference = 12`, `import_id = LEG-20260902-4ffe5198`.

Output `python3 -m tools.analysis.verify_legacy_import` trên chính file thật đó:

```text
SUMMARY_SOURCE_ROWS_WITH_VALUES = 71
SUMMARY_IMPORTED_ROWS           = 71
SUMMARY_UNACCOUNTED_ROWS        = 0
SUMMARY_REFERENCE_ONLY_PERSISTED = 0
matched=1508 mismatched=0
exit=0
```

`SUMMARY_SOURCE_ROWS_WITH_VALUES == SUMMARY_IMPORTED_ROWS == 71` → SOURCE COVERAGE đầy đủ trên `Summary 2026`. `mismatched=0` trên 1508 ô → VALUE MATCH. `SUMMARY_REFERENCE_ONLY_PERSISTED = 0` → `Summary 2025` không để lại bản ghi nào trong bảng production; kiểm chéo trực tiếp ở DB: `SELECT count(*) FROM legacy_summary_row WHERE sheet_name='Summary 2025'` = 0, `WHERE year=2025` = 0.

**N09 / N10 trên file thật.** N09 (dòng được phân loại nhưng toàn bộ vùng dữ liệu rỗng): KHÔNG xảy ra — 71/71 dòng classified của `Summary 2026` đều có giá trị số. N10 (số lưu dạng TEXT trong frozen region): KHÔNG xảy ra — quét `Summary 2026` C–S, `Summary 2025` C–S và `DataChart 2026` B–AJ dòng 3–14 → 0 ô numeric-as-text. Không normalize gì.

**Guard không bị nới lỏng.** `tests/test_legacy_source_coverage.py` giữ nguyên toàn bộ bài test R01/DEC-168, chĩa sang `Summary 2026`: sheet REQUIRED_IMPORT bị bóc hết công thức vẫn FAIL TO và kể tên đúng dòng; mất một dòng khỏi DB → `UNACCOUNTED`, exit 1; thêm bài test mới bắt trường hợp `Summary 2025` bị persist trở lại → verifier phải trượt. Full regression: `1608 passed, 11 skipped`.
Executed By:
Claude (S075) — Real Data Acceptance trên workbook thật Owner cung cấp
Timestamp:
2026-09-02

#### CHECK-PRA001-02 — Không tính lại số cũ
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Fixture cố ý có ô `Summary 2026!F9 = 999` trong khi công thức là `=G9/5.5%` (giá trị đúng công thức sẽ là ~547.272). DB lưu `Decimal('999')`, `formula_text['F'] = '=G9/5.5%'` — `tests/test_legacy_importer.py::test_a_value_that_contradicts_its_own_formula_is_stored_verbatim` và `tests/test_legacy_repository.py::test_a_value_contradicting_its_formula_survives_the_database` PASS. Dòng tổng tháng cũng lưu nguyên số Excel đã ghi, không cộng lại (`::test_month_total_is_stored_as_written_not_resummed`). Quét mã: `::test_recalculation_tokens_appear_only_inside_matching_strings` xoá mọi chuỗi/chú thích bằng `tokenize` rồi khẳng định `/2`, `/ 2`, `5.5%` KHÔNG xuất hiện trong phần logic của `app/legacy/`; `::test_importer_never_divides_or_multiplies_anything` quét AST, không có `ast.Div`/`ast.Mult`/`ast.FloorDiv` nào trong `app/legacy/`.

Executed By:
Claude (S075)
Timestamp:
2026-09-02

#### CHECK-PRA001-03 — Known defects được annotate, không sửa
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Fixture cài đủ bốn mẫu: A1 (`Summary 2026!D5 = 87,6` — số SP không nguyên), A2 (`F7 = SUM(F4:F5)` hẹp hơn `E7 = SUM(E4:E6)`), A4 (dòng 10 nhãn `Kênh-1` nhưng `D10 = '02.2026 NV-A'!$E$1`), A6 (`I4 = F4/1571182`). `known_defects` gắn ĐÚNG mã trên ĐÚNG cột: `{'D': ['A1']}`, `{'F': ['A2']}`, `{'D': ['A4'], ...}`, `{'I': ['A6']}` — 6 test trong `tests/test_legacy_importer.py` PASS. Giá trị ô KHÔNG đổi (`::test_a1_flags_a_non_integer_product_count_without_changing_it` khẳng định vẫn là `Decimal('87.6')`). Hai test âm chứng minh không báo lỗi bừa: `::test_a6_does_not_fire_when_the_previous_period_is_a_real_cell` và `::test_a_conversion_rate_divisor_is_not_mistaken_for_a_defect` (tỉ lệ `=G4/5.5%` hợp lệ, không phải A6). UI hiện dấu nhắc đúng ô: `tests/test_web_legacy_routes.py::test_defective_cells_show_their_defect_code` PASS.

Executed By:
Claude (S075)
Timestamp:
2026-09-02

#### CHECK-PRA001-04 — Origin và badge LEGACY
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Cả bốn bảng `legacy_*` có cột `origin` tường minh + CHECK constraint — `tests/test_history_db.py::test_every_fact_table_carries_an_explicit_origin_column` PASS, và `tests/test_legacy_repository.py::test_the_origin_check_constraint_rejects_a_foreign_origin` chứng minh constraint CHẶN THẬT khi chèn `PIPELINE_GENERATED`. Trên UI, mọi giá trị số đi qua đúng một macro `legacy_cell()` gắn badge + đơn vị, nên không có đường nào hiển thị số thiếu nhãn: `tests/test_web_legacy_routes.py::test_every_number_on_the_seller_page_carries_the_legacy_label` và `::test_every_number_on_the_daily_page_carries_the_legacy_label` trích mọi `<td class="num">` từ HTML và khẳng định TẤT CẢ chứa `LEGACY`; `::test_the_page_states_the_unit_of_the_legacy_numbers` khẳng định có "nghìn đồng (số cũ)".

Executed By:
Claude (S075)
Timestamp:
2026-09-02

#### CHECK-PRA001-05 — Bộ chọn kỳ và trang hiển thị đúng
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Flask test client: `/nhan-vien?ky=2026-01` cho ra đúng khối tháng 01 của fixture (3 dòng người bán/kênh + 1 dòng `Tổng T01`, giá trị `1.240.500` và `14.452.000` đúng số fixture); `?ky=2026-02` đổi sang khối tháng 02 (4 dòng người bán, `15.100.000`) và KHÔNG còn số của tháng 01 — `tests/test_web_legacy_routes.py::test_the_seller_matrix_shows_the_legacy_numbers_of_the_chosen_period`, `::test_the_period_picker_switches_periods` PASS. Kỳ không có dữ liệu (`?ky=2019-01`) ra trạng thái rỗng trung thực, không phải bảng số 0 — `::test_a_period_without_data_shows_an_honest_empty_state_not_zeros`; chưa nhập gì thì nói "Chưa nhập bản báo cáo cũ nào" (`::test_the_seller_page_is_empty_state_safe_before_any_import`). Bộ chọn chỉ nhận kỳ THỰC SỰ có dữ liệu (`app/web/server.py::_selected_period`), nên kỳ gõ tay không tạo ra bảng rỗng giả. Lưu ý: con số "7 dòng người bán/kênh" trong bản gate frozen là của FILE THẬT; fixture anonymized có 3/4/2 dòng theo tháng, cố ý khác nhau giữa các tháng để chứng minh importer không dùng offset dòng cố định.

Executed By:
Claude (S075)
Timestamp:
2026-09-02

### Security / Data / API / Regression

#### CHECK-PRA001-06 — Fail-closed cấu hình DB
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Bốn nhánh fail-closed đều có test PASS. (1) `REPORTS_REQUIRE_HISTORY_DB=1` thiếu `HISTORY_DATABASE_URL` → `HistoryConfigurationError`, app không khởi động: `tests/test_history_db.py::test_production_without_a_database_url_fails_closed`, `::test_empty_database_url_in_production_is_treated_as_missing`, `tests/test_web_legacy_routes.py::test_production_mode_refuses_to_start_without_a_database_url`. Không có fallback ngầm sang SQLite: `::test_production_never_silently_falls_back_to_sqlite`. (2) Schema chưa `upgrade head` → không khởi động: `::test_schema_check_rejects_a_database_with_no_schema`, `::test_schema_check_rejects_an_out_of_date_revision`, `tests/test_legacy_repository.py::test_build_refuses_an_unmigrated_database`. (3) DB lỗi trên đường ĐỌC → HTTP 503, KHÔNG phải trang rỗng: `tests/test_web_legacy_routes.py::test_a_database_failure_returns_503_not_an_empty_page`, `::test_an_unconfigured_history_store_says_so_instead_of_showing_no_data`, `::test_importing_without_a_history_store_is_503_not_a_silent_success`; ở tầng repository `tests/test_legacy_repository.py::test_a_broken_database_raises_unavailable_not_an_empty_result`. (4) **MỚI sau FIND-PRA001-R02** — DB lỗi trên đường GHI (`repository.create_import` raise `HistoryUnavailableError`) → HTTP **503**, không còn bị `except Exception` nuốt thành redirect 302 đổ lỗi cho workbook của Owner: `tests/test_web_legacy_routes.py::test_a_database_failure_on_the_write_path_is_503_not_a_blamed_workbook` (khẳng định `status_code == 503` và chuỗi "Không đọc được workbook" KHÔNG có trong body), `::test_a_write_path_database_failure_still_deletes_the_uploaded_file` (fail-closed không đánh đổi bằng bỏ quên file trên đĩa), và test đối ngẫu `::test_a_workbook_error_is_still_reported_as_a_workbook_error` chứng minh repair KHÔNG biến mọi lỗi thành 503. Ở production, `Dockerfile` chạy `alembic upgrade head && gunicorn` nên migration lỗi = container không start.

Executed By:
Claude (S075)
Timestamp:
2026-09-02

#### CHECK-PRA001-07 — Upload an toàn, không lưu file, không PII
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`tests/test_web_legacy_routes.py`: từ chối non-xlsx (`::test_a_non_xlsx_upload_is_rejected`) và upload rỗng (`::test_a_missing_upload_is_rejected`); giới hạn 25 MB dùng chung `MAX_CONTENT_LENGTH` đã có (`::test_the_oversize_limit_still_applies_to_legacy_uploads`); tên file client KHÔNG bao giờ chạm filesystem — tên trên đĩa luôn là `uuid4().hex` do server sinh (`::test_a_path_traversal_filename_never_reaches_the_filesystem`); file tạm bị xoá trong `finally` cả khi import THÀNH CÔNG (`::test_the_uploaded_workbook_is_deleted_after_a_successful_import`) lẫn khi import LỖI (`::test_the_uploaded_workbook_is_deleted_even_when_the_import_fails`); upload lại cùng fingerprint không tạo bản mới và nói rõ ra (`::test_reimporting_the_same_file_says_so_and_adds_no_version`, `tests/test_legacy_repository.py::test_reimporting_the_same_file_does_not_create_a_second_version`). Không cột PII nào trong schema: `tests/test_legacy_repository.py::test_no_legacy_table_stores_customer_personal_data` quét tên cột với danh sách cấm (customer/phone/address/khach/dien_thoai/dia_chi) — chỉ ba sheet tổng hợp được nhập, 56 sheet chi tiết chứa tên/SĐT/địa chỉ nằm ngoài scope.

Executed By:
Claude (S075)
Timestamp:
2026-09-02

#### CHECK-PRA001-08 — Ranh giới kiến trúc và regression
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`test_no_module_under_app_reaches_the_network` PASS (không đổi). Không module nào dưới `app/` import `psycopg`/`alembic`: `tests/test_history_db.py::test_no_module_under_app_imports_a_database_driver_or_alembic` quét toàn bộ `app/**/*.py`. `tests/test_golden_baseline.py` không đổi kết quả. Full suite: baseline đầu phiên `1494 passed, 11 skipped, 0 failed`; sau implementation `1600 passed, 11 skipped, 0 failed` (+106 test mới, 0 test mất, 0 skip mới; +14 test của repair cycle 1). Bốn test trong `tests/test_web_server.py` được sửa endpoint `/history` → `/du-lieu` vì scope item 4 của chính task này yêu cầu mở rộng `/history` thành tab "Dữ liệu"; nội dung assertion giữ nguyên, và redirect `/history` → `/du-lieu` có test riêng (`tests/test_web_legacy_routes.py::test_the_old_history_url_still_leads_to_the_data_tab`). `git diff --check` sạch. `app/modules/**`, `app/pipeline.py`, `app/composition.py`, `app/web/storage_backend.py`, `app/web/run_registry.py`, `tools/storage/**`, `tools/tracking/**`, `config/**`, `data/**`, `tests/fixtures/golden/**` KHÔNG bị chạm (xem Changed Files Registry).

Executed By:
Claude (S075)
Timestamp:
2026-09-02

#### CHECK-PRA001-09 — DDL tương thích PostgreSQL
Priority:
RECOMMENDED

Status:
BLOCKED

Evidence Level:
E1

Evidence:
Claude Cloud session này KHÔNG có PostgreSQL (không được tự tạo dịch vụ trả phí — xem §27 của prompt phiên). Đã làm những gì kiểm chứng được mà không cần Postgres: mọi kiểu cột nằm trong tập giao SQLite ↔ PostgreSQL (`Text`, `Integer`, `Numeric`, `Boolean`; JSON lưu TEXT); `tools/db/schema.py::ExactNumeric` render `NUMERIC` trên PostgreSQL và `TEXT` trên SQLite để fidelity thập phân đúng trên CẢ HAI dialect; migration `0001_legacy` sinh DDL từ cùng một `MetaData` nên không có SQL viết tay riêng cho dialect nào; `alembic upgrade head` + `downgrade base` PASS trên SQLite thật (`tests/test_history_db.py::test_migration_upgrade_then_downgrade_round_trips`). Việc chạy `alembic upgrade head` trên PostgreSQL thật và render `/nhan-vien` từ Postgres trở thành GATE DEPLOY của Owner — quy trình đã viết ở `docs/deployment/S071_DEPLOYMENT.md` bước 8–12.

Executed By:
Claude (S075) — gate deploy Owner
Timestamp:
2026-09-02

#### CHECK-PRA001-10 — Governance validators
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Chạy lại cuối phiên: `validate_structure` PASS, `validate_project_state` PASS, `validate_task_completion` PASS, `validate_evidence` PASS. `validate_reference_integrity` FAIL với ĐÚNG 3 reference có sẵn của REM-T06 (ba file gốc repo mà REM-T06 sẽ tạo: README, CODE_OF_CONDUCT, CONTRIBUTING — cố ý viết không kèm phần mở rộng ở đây để chính dòng evidence này không tự tạo thêm reference hỏng) — giống hệt baseline S073; session này thêm 0 reference hỏng (quét 203 file .md so với 199 ở S073, tức 3 file mới đều sạch). Output nguyên văn ở mục "Validator run cuối" của `docs/sessions/S075-pra-001-legacy-reference-vertical.md`.

Executed By:
Claude (S075)
Timestamp:
2026-09-02

## CHANGE_BUDGET

> **CẬP NHẬT 2026-09-02 (DEC-168, Owner approved sau Independent Review):**
> `PRA-001_CHANGE_BUDGET_EXCEPTION = APPROVED`.
> **Ngân sách production logic mới = ~1.050 dòng** (thay ngưỡng cứng 600
> bên dưới, CHỈ cho `TASK-PRA-001`). Review xác minh: `ESSENTIAL ≈ 950`,
> `REASONABLE_HARDENING ≈ 60`, `OUT_OF_SCOPE = 0 material`,
> `SPECULATIVE ≈ 15` → không cắt capability, không nén code để đạt chỉ tiêu.
> Đo sau repair cycle 1: **1.045 dòng logic** (`tools/db` 209 + `app/legacy`
> 384 + `history_store` 223 + `legacy_presentation` 94 + delta `server.py`
> 135) — **trong ngân sách**.
> Ngân sách mới KHÔNG được dùng để mở thêm scope: mọi capability mới vẫn là
> `SCOPE EXPANSION REQUIRED`.

- (LỊCH SỬ, đã được DEC-168 thay) Production Python mới: mục tiêu ≤ 450
  dòng, ngưỡng dừng cứng 600 dòng (`tools/db` + `app/legacy` +
  `app/web/history_store` + delta `server.py`).
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
- Bất kỳ đề xuất nào tạo bảng ngoài bốn bảng `legacy_*` (ví dụ snapshot/version của PRA-002) → `SCOPE EXPANSION REQUIRED`, dừng: Owner chốt "không prebuild schema PRA-002".

## Đăng Ký File Đã Thay Đổi (Changed Files Registry)

Created:
- `alembic.ini`
- `tools/db/__init__.py`, `tools/db/schema.py`
- `tools/db/migrations/env.py`, `tools/db/migrations/script.py.mako`
- `tools/db/migrations/versions/0001_legacy.py`
- `app/legacy/__init__.py`, `app/legacy/models.py`, `app/legacy/defects.py`,
  `app/legacy/parser.py`
- `app/web/history_store.py`, `app/web/legacy_presentation.py`
- `app/web/static/css/tinphat-ui.css`
- `app/web/templates/layout.html`, `_legacy_bits.html`, `du_lieu.html`,
  `nhan_vien.html`, `doanh_so_ngay.html`
- `tools/analysis/verify_legacy_import.py`
- `tests/fixtures/legacy/__init__.py`, `tests/fixtures/legacy/build_legacy_workbook.py`
- `tests/test_history_db.py`, `tests/test_legacy_importer.py`,
  `tests/test_legacy_repository.py`, `tests/test_web_legacy_routes.py`
- `docs/sessions/S075-pra-001-legacy-reference-vertical.md`
- `tests/test_legacy_source_coverage.py` (repair cycle 1, FIND-PRA001-R01)
- `docs/sessions/S076-pra-001-repair-cycle-1.md` (repair cycle 1)

Modified:
- `app/web/server.py` (khởi tạo history store tiêm được + 5 route legacy;
  không đổi hành vi `/`, `/run`, `/artifact/<run_id>`, `/feedback`)
- `app/web/templates/index.html` (chuyển sang `layout.html`)
- `pyproject.toml` (extra `history`; gộp vào `web-prod`; `dev` thêm
  SQLAlchemy/alembic để chạy test)
- `render.yaml` (`REPORTS_REQUIRE_HISTORY_DB`, `HISTORY_DATABASE_URL`)
- `Dockerfile` (COPY `alembic.ini`; CMD chạy `alembic upgrade head` trước gunicorn)
- `.gitignore` (`data/history/`)
- `tests/conftest.py` (fixture `legacy_workbook_path`, `history_engine`,
  `legacy_repository`)
- `tests/test_web_server.py` (4 test đổi `/history` → `/du-lieu` theo scope
  item 4 của chính task này)
- `docs/deployment/S071_DEPLOYMENT.md` (bước 8–12: Render PostgreSQL)
- `PROJECT/PROJECT_PROGRESS.md`, `PROJECT/LO_TRINH_DE_HIEU.md`
- `docs/tasks/TASK-PRA-001-legacy-reference-vertical.md` (chính file này)

Repair cycle 1 (S076) — sửa thêm:
- `app/legacy/parser.py` (guard FAIL TO cho dòng có giá trị nghiệp vụ nhưng
  không khớp contract phân loại — FIND-PRA001-R01)
- `tools/analysis/verify_legacy_import.py` (kiểm SOURCE COVERAGE từ phía
  Excel + in ba con số coverage + exit khác 0 khi thiếu dòng — R01)
- `app/web/server.py` (`except HTTPException: raise` trong route import, để
  abort(503) của `_guarded` không bị nuốt thành redirect — FIND-PRA001-R02)
- `tests/fixtures/legacy/build_legacy_workbook.py` (`strip_formula_markers`
  — tái tạo đúng case reviewer)
- `tests/test_legacy_repository.py`, `tests/test_web_legacy_routes.py`
  (cập nhật theo kết quả verifier mới + test đường ghi)
- `PROJECT/PROJECT_DECISIONS.md` (DEC-168)

Deleted:
- `app/web/templates/history.html` (nội dung chuyển vào `du_lieu.html`;
  đường `/history` giữ dưới dạng redirect)

KHÔNG bị chạm (xác nhận bằng `git diff --stat`): `app/modules/**`,
`app/pipeline.py`, `app/composition.py`, `app/owner_usability.py`,
`app/demo.py`, `app/web/storage_backend.py`, `app/web/run_registry.py`,
`tools/storage/**`, `tools/tracking/**`, `config/**`, `data/**`,
`tests/fixtures/golden/**`, và toàn bộ Tracking.

Migration Impact:
- Thêm schema history (migration `0001_legacy`) trên DB MỚI; không đụng dữ liệu R2/run hiện có.

## ESCALATION — CHANGE_BUDGET_EXCEEDED (2026-09-02, S075) — ĐÃ GIẢI QUYẾT

> **ĐÓNG 2026-09-02 (DEC-168):** Owner approve
> `PRA-001_CHANGE_BUDGET_EXCEPTION`, ngân sách mới ~1.050 dòng logic;
> đo sau repair cycle 1 = **1.045** → trong ngân sách. Không cắt
> capability, không nén code. Phần bên dưới giữ nguyên làm bản ghi
> lịch sử của lúc escalation được nêu.

Trạng thái (lúc nêu, S075): **CẦN OWNER PHÂN XỬ.** Implementation đã xong và PASS, nhưng
vượt ngân sách thay đổi đã freeze. Ghi ra đây thay vì âm thầm bỏ qua.

Đo bằng **dòng logic** (bỏ dòng trống, comment, docstring — script đo:
AST + đếm dòng, chạy trên đúng tập file mà CHANGE_BUDGET liệt kê):

| Thành phần | Dòng logic | Dòng thô |
|---|---:|---:|
| `tools/db/` (4 file) | 209 | 345 |
| `app/legacy/` (4 file) | 365 | 520 |
| `app/web/history_store.py` | 223 | 290 |
| delta `app/web/server.py` | 133 | 181 |
| **Tổng đúng tập CHANGE_BUDGET liệt kê** | **930** | **1.336** |
| `app/web/legacy_presentation.py` (thêm, ngoài danh sách) | 94 | 139 |
| **Tổng production Python mới** | **1.024** | **1.475** |

Mục tiêu 450 · ngưỡng dừng cứng **600** → **vượt 1,7 lần** ngưỡng cứng dù
tính theo cách đo có lợi nhất (chỉ dòng logic, chỉ tập file được liệt kê).

Ngân sách KHÁC vẫn trong hạn: template mới 284/300 dòng; CSS 200/450 dòng;
test mới 92 (yêu cầu ≥ 25); dependency đúng ba gói đã cho phép
(`sqlalchemy`, `alembic`, `psycopg[binary]`), không thêm framework nào.

Vì sao vượt (đánh giá trung thực, KHÔNG phải để xin thông qua):
1. `DATA_MODEL_MINIMUM` đã freeze có 4 bảng và ~30 cột. Riêng khai báo
   schema + migration + ánh xạ cột khi ghi/đọc đã là ~330 dòng logic mà
   không có cách viết nào ngắn hơn đáng kể nếu vẫn giữ một nguồn DDL duy nhất.
2. Yêu cầu "phân loại dòng theo CẤU TRÚC công thức" (không dùng offset dòng
   cố định) đắt hơn nhiều so với đọc theo vị trí — nhưng bắt buộc, vì số
   dòng người bán mỗi tháng thay đổi (tháng 03.2026 có thêm "Linh").
3. Ràng buộc fidelity buộc thêm `ExactNumeric` (~25 dòng): cột `NUMERIC`
   trên SQLite mang affinity số và biến `87,6` thành số thực nhị phân — tức
   là sửa một con số mà công cụ không có thẩm quyền sửa.
4. Ước lượng 450/600 ở S073 được đặt khi chưa viết dòng nào; nhìn lại, nó
   là ước lượng lạc quan cho một vertical đi hết từ Excel tới UI.

Ba lựa chọn cho Owner (session này KHÔNG tự chọn):
- **A.** Chấp nhận thực tế, chỉnh CHANGE_BUDGET của PRA-001 lên đúng số đã
  đo và ghi một DEC — code đang PASS, không phải sửa gì.
- **B.** Giữ ngưỡng 600, tách PRA-001 thành hai slice (nền DB + importer /
  repository + web) và chia lại ngân sách theo từng slice.
- **C.** Yêu cầu cắt bớt. Cần biết cắt gì: bỏ trang "Doanh số ngày" tiết
  kiệm ~60 dòng; bỏ annotate known_defects ~80 dòng — nhưng cả hai đều nằm
  trong Completion Gate đã freeze (CHECK-03, CHECK-05), nên cắt là đổi
  acceptance chứ không phải tối ưu mã.

Không có dòng nào được viết cho PRA-002: không bảng snapshot/version/
reconciliation, không order identity, không engine INSERT/SAME/
SOURCE_CHANGED/REMOVED_CANDIDATE — `tests/test_history_db.py::
test_migration_chain_contains_only_the_legacy_revision` và
`::test_schema_declares_exactly_the_four_frozen_legacy_tables` khoá điều này.

## Ghi Chú (Notes)
- Đơn vị: legacy lưu nguyên `kVND`; presentation hiển thị kèm nhãn; KHÔNG
  quy đổi trong DB.
- `Summary 2026` dòng 3 (`YEAR_TOTAL`, `SUM(E4:E902)/2`) và dòng "Tiến độ"
  lưu với `row_kind` riêng, không cộng vào ma trận.
- DataChart cột "Doanh số" khác Summary "Tổng bán" → lưu cả hai nguyên
  trạng, hiển thị ở hai trang khác nhau, KHÔNG đối chiếu hai số này với
  nhau (UNKNOWN).
