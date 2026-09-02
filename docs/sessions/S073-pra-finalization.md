# BÀN GIAO SESSION (SESSION HANDOFF)

Session ID:
S073

Task:
TASK-PRA-000 finalization → TASK-PRA-001 chuẩn bị (gate FROZEN)

Task Mode:
SPIKE (finalization/planning; không code feature)

Project Profile:
PRODUCT

Status:
DONE — planning finalization. Không thay đổi code production, không sửa
Tracking, không deploy.

Nhánh: `claude/reports-pipeline-architecture-gj8bji`, base = nhánh mặc định
`claude/extract-upload-repo-gq2ws4` tại `596564b` (fetch đầu phiên, 0 commit
mới trên nhánh mặc định).

## Kết Quả (Result)

- Owner decisions A–E ghi thành DEC-166 (`PROJECT/PROJECT_DECISIONS.md`).
- Amendment Flask/Jinja: `docs/adr/ADR-109-web-layer-flask-jinja.md`
  (Accepted) + dòng Superseded By trong `docs/adr/ADR-101-architecture-and-stack.md`.
- Decision audit persistence: `docs/adr/ADR-108-persistent-history-store.md`
  (Proposed) — ma trận R2 vs D1 vs PostgreSQL theo 20 tiêu chí Owner nêu,
  trả lời 4 câu hỏi A–D, đề xuất HYBRID.
- Policy reconciliation finalized + PRA-002 preview + roadmap FROZEN: phụ lục
  F1–F8 trong `docs/tasks/TASK-PRA-000-persistent-reporting-analytics-plan.md`.
- `docs/tasks/TASK-PRA-001-legacy-reference-vertical.md`: scope hẹp, Data
  Model Minimum, Change Budget, Completion Gate FROZEN (10 check).
- PROGRESS + LO_TRINH cập nhật cùng checkpoint.

## Subtask Đã Hoàn Thành (Subtasks Completed)
- Đồng bộ nhánh; đọc quy ước ADR/DEC hiện có.
- Decision audit persistence theo workload thực (số liệu từ evidence.json và
  audit S072).
- Finalize policy INSERT / SAME / SOURCE_CHANGED / REMOVED_CANDIDATE /
  RESULT_REVISED theo Decision B/C/D (coverage_state ba mức; REMOVED_CANDIDATE
  chỉ khi CONFIRMED_COMPLETE; không tự loại khỏi analytics).
- Namespace năm cho order_key: cột `bh_number` + `bh_year_hint`, khoá opaque,
  migration path một bước; không áp business rule.
- Freeze roadmap 5 slice; viết PRA-001; PRA-002 chỉ preview.

## Subtask Còn Lại (Subtasks Remaining)
- (ĐÃ XONG ở close-out S074, 2026-09-02) Owner approve ADR-108 → DEC-167, ADR-108 Accepted, TASK-PRA-001 READY.
- Session tiếp theo implement PRA-001 theo handoff bên dưới.

## Tóm Tắt Completion Gate (Completion Gate Summary)

Required:
Không có Completion Gate riêng cho session finalization (SPIKE); tiêu chí
học hỏi: quyết định đã chốt được ghi thành DEC, policy có bảng, task kế
tiếp có gate frozen — đều đạt. Validator governance chạy lại sau khi viết
(mục Evidence).

PASS:
Validator 4/5 PASS; reference integrity chỉ còn 3 reference có sẵn của
REM-T06 (như baseline S072).

FAIL:
(không)

BLOCKED:
(không)

NOT_TESTED:
Full test suite không chạy (không chạm code).

## Evidence Xác Minh (Verification Evidence)

| Check ID | Status | Evidence Level | Evidence | Executed By | Timestamp |
|---|---|---|---|---|---|
| S073-V1 | PASS | E1 | Validator governance output (mục "Validator run cuối") | Claude (S073) | 2026-09-02 |
| S073-V2 | PASS | E1 | `git diff --check` sạch; `git status` chỉ docs/PROJECT | Claude (S073) | 2026-09-02 |

## File Đã Thay Đổi (Files Changed)

Created:
- `docs/adr/ADR-108-persistent-history-store.md`
- `docs/adr/ADR-109-web-layer-flask-jinja.md`
- `docs/tasks/TASK-PRA-001-legacy-reference-vertical.md`
- `docs/sessions/S073-pra-finalization.md`

Modified:
- `docs/adr/ADR-101-architecture-and-stack.md` (chỉ mục Superseded By)
- `docs/tasks/TASK-PRA-000-persistent-reporting-analytics-plan.md` (phụ lục F1–F8)
- `PROJECT/PROJECT_DECISIONS.md` (DEC-166)
- `PROJECT/PROJECT_PROGRESS.md`
- `PROJECT/LO_TRINH_DE_HIEU.md`

Deleted:
- (không)

## Quyết Định Chính (Key Decisions)
- DEC-166 (Owner): A–E. Persistence: ADR-108 Accepted (DEC-167, close-out S074).
- Policy: `LATEST_SNAPSHOT_IS_CURRENT_CANDIDATE` cho SOURCE_CHANGED (hằng số
  policy, có cờ tới khi acknowledged); REMOVED_CANDIDATE vẫn tính vào
  analytics cho tới khi phân xử; NOT_SEEN_IN_LATEST_SNAPSHOT khi coverage
  chưa CONFIRMED_COMPLETE.

## Rủi Ro / Vướng Mắc (Risks / Blockers)
- (Đã đóng ở S074) Blocking duy nhất là approve ADR-108 — nay Accepted; không còn blocker cho PRA-001.
- Ước tính chi phí Render Postgres cần xác minh giá hiện hành khi tạo.
- Hai dialect SQLite/Postgres: giữ SQL Core trong tập giao; CHECK-PRA001-09
  có thể BLOCKED trong session không có Postgres → thành gate deploy Owner.

## Hạng Mục Regression (Regression Items)
- Không.

## Chưa Được Thay Đổi (Do Not Change Yet)
- Protected core; `app/modules/**`; exporter (chỉ PRA-002 mới expose
  `present_lines()`); `RunStore`/R2; Tracking.

## Session Tiếp Theo Được Khuyến Nghị (Next Recommended Session)

### IMPLEMENTATION HANDOFF — TASK-PRA-001 (đi thẳng vào implement)

Điều kiện mở: ĐÃ THOẢ — ADR-108 Accepted (DEC-167, 2026-09-02):
Production DB = Managed PostgreSQL; Artifacts/run JSON/XLSX = R2;
Local/test = SQLite; PRA-001 = minimum legacy schema only (4 bảng
`legacy_*`); KHÔNG prebuild schema PRA-002; Tracking READ-ONLY, không đổi.
IMPLEMENTATION_BASE_SHA = HEAD của nhánh
`claude/reports-pipeline-architecture-gj8bji` sau commit close-out S074
(xem `PROJECT/PROJECT_PROGRESS.md` khối S074).

Thứ tự thực hiện (mỗi bước có test trước khi sang bước sau):
1. Đồng bộ nhánh (bước 0 Session Open Protocol). Ghi baseline full suite
   (`python3 -m pytest -q`) — số passed/skipped để so ở CHECK-PRA001-08.
2. (Đã làm ở S074 — bỏ qua) DEC-167 đã ghi, ADR-108 đã Accepted.
3. `pyproject.toml`: extra `history = ["SQLAlchemy>=2.0", "alembic>=1.13", "psycopg[binary]>=3.1"]`, gộp vào `web-prod`.
4. `tools/db/`: `build_engine(env) -> Engine` (`HISTORY_DATABASE_URL`; mặc định
   `sqlite:///<REPORTS_DATA_ROOT|REPO_ROOT>/data/history/history.db`; `REPORTS_REQUIRE_HISTORY_DB=1`
   → thiếu URL raise `HistoryConfigurationError`); `assert_schema_current(engine)` so Alembic head;
   Alembic env + `0001_legacy` (DDL mục DATA_MODEL_MINIMUM của task; kiểu `Numeric`, JSON lưu TEXT, CHECK origin).
   Test: up/down trên SQLite tmp; fail-closed 3 nhánh.
5. `app/legacy/`: `parse_workbook(path) -> LegacyWorkbook` (Summary 2026/2025, DataChart 2026; `formula_text`;
   `known_defects` bằng kiểm tra cấu trúc công thức; `row_kind`). Fixture Excel tổng hợp tạo bằng openpyxl trong
   `tests/fixtures/legacy/` (anonymized: 2026 tháng 01–03, người bán "NV-A/NV-B/NV-C", kênh "Kênh-1"; cố ý cài A1/A2/A4/A6).
   Test: fidelity, no-recalc, defect annotation, sheet thiếu → lỗi rõ.
6. `app/web/history_store`: `LegacyRepository(engine)`; test round-trip, fingerprint trùng, is_current chuyển đổi.
7. `app/web/server.py`: khởi tạo `history = history_store.build(env, engine=None)` (tiêm cho test); route
   `POST /du-lieu/legacy`, `GET /du-lieu` (thay `/history`, giữ redirect `/history` → `/du-lieu`), `GET /nhan-vien`,
   `GET /doanh-so-ngay`; lỗi DB → 503 qua `_guarded()` hiện có. Test Flask client cho từng route + 7 test upload adversarial
   (tái dùng battery của S070).
8. Templates: `layout` (tab bar: Chạy báo cáo · Dữ liệu · Nhân viên · Doanh số ngày), chuyển `index.html`/`history.html`
   sang layout; `app/web/static/css/tinphat-ui` (token `--tp-*`, `.ncc-tabs`, table, badge, chips — chép có chọn lọc, đặt nền `--tp-bg`).
   Badge LEGACY + đơn vị trên mọi số; dấu (i) known_defect với tooltip mã A1/A2/A4/A6.
9. Chạy file Excel thật (nếu có trong session/máy Owner) → script `tools/analysis/verify_legacy_import` in `matched=N mismatched=0` (CHECK-01).
   Nếu không có file → CHECK-01 NOT_TESTED + ghi gate Owner chạy.
10. `render.yaml` (+ `HISTORY_DATABASE_URL` sync:false, `REPORTS_REQUIRE_HISTORY_DB=1`), `Dockerfile` CMD chạy `alembic upgrade head`
    trước gunicorn (fail-closed), `docs/deployment/S071_DEPLOYMENT.md` bước tạo Postgres. Full regression; validators; handoff S074;
    PROGRESS/LO_TRINH; commit theo nhóm bước; push `-u`.

Giữ trong đầu: ≤450 LOC Python (dừng cứng 600); không chạm
`app/modules/**`; không import driver DB dưới `app/`; không tính lại số
cũ; không hiển thị số legacy thiếu nhãn.

## File Agent Tiếp Theo Cần Đọc (Files Next Agent Should Read)
- `CLAUDE.md`
- `PROJECT/PROJECT_PROGRESS.md` (khối "PLANNED — PHASE-PRA finalization (S073)")
- `docs/tasks/TASK-PRA-001-legacy-reference-vertical.md`
- `docs/tasks/TASK-PRA-000-persistent-reporting-analytics-plan.md` (mục E, G; phụ lục F2, F3, F6)
- `docs/adr/ADR-108-persistent-history-store.md`, `docs/adr/ADR-109-web-layer-flask-jinja.md`
- `app/web/server.py`, `app/web/storage_backend.py`, `tools/storage/r2_store.py` (pattern adapter/driver)
- `docs/analysis/05_EXCEPTIONS.md` (A1–A6), `docs/analysis/01_DATA_MAPPING.md` §4 (layout sheet)
- `tests/test_web_server.py` (battery upload adversarial để tái dùng)

## Validator run cuối (nguyên văn, 2026-09-02, S073)

```
$ git diff --check && echo diff-check clean
diff-check clean
$ for s in validate_structure validate_project_state validate_task_completion validate_evidence validate_reference_integrity; do python3 governance/scripts/governance/$s.py; echo "exit=$?"; done
GOVERNANCE STRUCTURE: PASS
Deployment root: PASS — /home/user/Reports
Checked 21 required paths.
exit=0
PROJECT STATE: PASS
exit=0
TASK COMPLETION: PASS
Checked 8 DONE task(s).
exit=0
EVIDENCE VALIDATION: PASS
Checked 91 REQUIRED PASS evidence record(s).
exit=0
REFERENCE INTEGRITY: FAIL
Quét 199 file .md (loại trừ 10 file trong governance/reference/history/, docs/audit/).
3 reference không phân giải được:
- docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> /README.md
- docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> CODE_OF_CONDUCT.md
- docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> CONTRIBUTING.md
exit=1
# 3 reference hỏng là có sẵn từ trước (REM-T06 DO_WHEN_IDLE), giống baseline S072; S073 thêm 0 reference hỏng.
```
