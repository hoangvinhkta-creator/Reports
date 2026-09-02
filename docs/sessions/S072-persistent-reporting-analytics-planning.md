# BÀN GIAO SESSION (SESSION HANDOFF)

Session ID:
S072

Task:
TASK-PRA-000 — Kế hoạch kiến trúc Persistent Reporting & Analytics

Task Mode:
SPIKE

Project Profile:
PRODUCT

Status:
DONE (planning only — không code feature, không refactor, không migration, không deploy, không sửa Tracking)

Nhánh làm việc: `claude/reports-pipeline-architecture-gj8bji`, mở từ HEAD
`596564b` = origin/`claude/extract-upload-repo-gq2ws4` (nhánh mặc định, đã
`git fetch` và xác nhận không lệch trước khi đọc governance).

Quyền hạn session: WRITE SCOPE = repo Reports duy nhất. Tracking
(`/home/user/Tracking`) chỉ được đọc làm design reference; không tạo thay
đổi, commit, branch, config hay PR nào ở Tracking.

## Kết Quả (Result)

Một tài liệu kế hoạch đầy đủ 18 mục A–R tại
`docs/tasks/TASK-PRA-000-persistent-reporting-analytics-plan.md`, gồm:
audit Reports hiện tại, audit Excel cũ, audit file MD kiến trúc UI, data
model tối thiểu cho hai origin (`LEGACY_REFERENCE`, `PIPELINE_GENERATED`),
khoá đơn/dòng có bằng chứng, mô hình snapshot/version/reconciliation với
ví dụ 01–10/09 vs 01–30/09, information architecture 6 khu vực, tham chiếu
design Tracking (reuse / Reports-specific / do-not-couple), analytics phân
loại NOW/LATER/DEFER, roadmap 5 vertical slice (mỗi slice 11 trường), 13
quyết định Owner, rủi ro, deferred findings, `SCOPE_DRIFT = NO`, hành động
tiếp theo.

Không thay đổi nào ở `app/`, `tools/`, `config/`, `tests/`, `governance/`,
`Dockerfile`, `render.yaml`.

## Subtask Đã Hoàn Thành (Subtasks Completed)
- Đồng bộ nhánh + đọc S000 (PROJECT_PROFILE_STANDARD, RULE_PRECEDENCE,
  TASK_MODE_STANDARD, 00_SESSION_ORCHESTRATION, V4_1_POLICY_FREEZE).
- Audit Reports: web layer, persistence (`RunStore`, R2, SQLite), pipeline
  output (`ImportResult`, `WorkingLine`, `PriceResolutionRecord`), import
  (`raw_reader`, `order_builder`), export (3 sheet), validation taxonomy,
  Tracking integration (capture/live pull, ranh giới `CHECK-105D-17`),
  tests/golden, deployment topology.
- Audit Excel cũ bằng script openpyxl (59 sheet; cấu trúc, KPI, drill-down,
  BH, Trans, dòng âm/0, kênh Nội thành/Gia dụng, công thức) — đối chiếu với
  `docs/analysis/` đã có, không làm lại phần đã có.
- Audit file MD kiến trúc UI (KIEN_TRUC_GIAO_DIEN_REPORTS_ANALYTICS, do Owner cung cấp, không commit) và kiểm tra lại từng đề
  xuất với dữ liệu thật (ví dụ: bộ chọn "hôm nay/tuần" không phù hợp nguồn
  batch → DEFER; sidebar → thay bằng tab ngang theo Tracking).
- Audit design Tracking (chỉ đọc `public/index.html`, `public/kpi-demo.css`).
- Viết kế hoạch, cập nhật `PROJECT/PROJECT_PROGRESS.md` (khối PLANNED —
  PHASE-PRA + pointer "Session tiếp theo") và `PROJECT/LO_TRINH_DE_HIEU.md`
  (mục "KẾ HOẠCH MỚI") trong cùng checkpoint.

## Subtask Còn Lại (Subtasks Remaining)
- Không còn cho TASK-PRA-000. Các slice TASK-PRA-001…005 ở trạng thái
  PLANNED (chưa có task file riêng, chưa READY — cố ý, theo "không đóng
  băng chi tiết task còn xa trước khi discovery đủ").

## Tóm Tắt Completion Gate (Completion Gate Summary)

Required:
CHECK-PRA000-01, CHECK-PRA000-02, CHECK-PRA000-03

PASS:
CHECK-PRA000-01, CHECK-PRA000-02, CHECK-PRA000-03

FAIL:
(không)

BLOCKED:
(không)

NOT_TESTED:
(không)

## Evidence Xác Minh (Verification Evidence)

| Check ID | Status | Evidence Level | Evidence | Executed By | Timestamp |
|---|---|---|---|---|---|
| CHECK-PRA000-01 | PASS | E1 | `grep -c "^## [A-R]\. "` → `18`; `grep -c "^GOAL "` → `5`; `grep -c "^RECOMMENDED_EFFORT "` → `5` (mục E1 bên dưới) | Claude (S072) | 2026-09-02 |
| CHECK-PRA000-02 | PASS | E1 | Output script audit Excel + fixture golden (mục E2 bên dưới) | Claude (S072) | 2026-09-02 |
| CHECK-PRA000-03 | PASS | E1 | `git diff --stat`, validator governance, `git diff --check` (mục E3 bên dưới) | Claude (S072) | 2026-09-02 |

### E1 — cấu trúc tài liệu
```
$ wc -l docs/tasks/TASK-PRA-000-persistent-reporting-analytics-plan.md
932 docs/tasks/TASK-PRA-000-persistent-reporting-analytics-plan.md
$ grep -c "^## [A-R]\. " docs/tasks/TASK-PRA-000-persistent-reporting-analytics-plan.md
18
$ grep -c "^GOAL " docs/tasks/TASK-PRA-000-persistent-reporting-analytics-plan.md
5
$ grep -c "^RECOMMENDED_EFFORT " docs/tasks/TASK-PRA-000-persistent-reporting-analytics-plan.md
5
```

### E2 — audit dữ liệu thật (trích nguyên văn output script, file Excel do Owner cung cấp trong session, không commit)
```
=== SHEET 'Summary 2025' ... state=hidden | 'Summary 2026' state=visible | 'DataChart 2026' state=visible
(59 sheet; visible: Summary 2026, DataChart 2026, 08.2026 Tín Phát/Ly/Kiên/Gia dụng/Nội thành)

sheet                   rows trans  cont bhrows uniqBH dupBH transNoBH  q0  neg days cust   B1
08.2026 Tín Phát         126    82    44     86     84     2         3   2   12   16   88   82
08.2026 Ly               131    79    52     57     56     1        24   1   18    9   80   79
08.2026 Kiên              75    54    21     58     54     3         2   1    3    9   60   54
(mọi sheet 01–07.2026 và mọi sheet kênh: bhrows = 0)
BH appearing in >1 sheet: 0
BH duplicated within same sheet: 6
[('BH73320', ['08.2026 Tín Phát', '08.2026 Tín Phát']), ('BH73379', ...), ('BH73340', ['08.2026 Ly', '08.2026 Ly']),
 ('BH73368', ['08.2026 Kiên', '08.2026 Kiên']), ('BH73350', ['08.2026 Kiên', '08.2026 Kiên', '08.2026 Kiên']), ('BH73387', ...)]
→ kiểm tra từng cặp dòng: đều là đơn nhiều dòng cùng khách (ví dụ BH73320 r133 '7000A2' + r134 '2800AL', cùng 'Anh Kiên').
Nơi nhập top: [('Kho', 2417), ('Việt Hải', 348), ('179.0', 318), ('Trung Xuân', 184), ...]
Giao hàng col samples: [('Kích', 487), ('KHBH -50', 169), ('Thợ lắp -200, KHBH -50', 109), ..., ('Trả hàng', 2), ('Huỷ', 1), ('Hoàn', 1)]
BH range: 66731 82897 count 194
Nội thành rows with G but no product (subtotal?): 15 [43, 71, 92, 125, 155, 199, 227, 260, 304, 344]
Nội thành SUM(G)= 12770800.0  product-only sum= 6385400.0  G1= 6385400
Summary 2026!D64 = '07.2026 Tín Phát'!$E$1 ; D71 = '08.2026 Tín Phát'!$E$1  (dòng Nội thành — lỗi A4 còn ở bản hiện tại)
DataChart 2026!AG3 = 25474886000 (tháng 01, VND) vs Summary 2026!E11 = 24775990 (nghìn đồng) → hai nguồn khác nhau, UNKNOWN
```
```
tests/fixtures/golden/period_2026_01.xlsx sheet SỔ CHI TIẾT BÁN HÀNG rows 357
 lines=351 orders=254 orders_multi_date=0 orders_multi_employee=0 orders_with_identical_line_sig=0
tests/fixtures/golden/period_2026_06.xlsx sheet SỔ CHI TIẾT BÁN HÀNG rows 186
 lines=180 orders=146 orders_multi_date=0 orders_multi_employee=0 orders_with_identical_line_sig=0
docs/analysis/_evidence/evidence.json: /raw/line_count 11765 · /raw/distinct_order_count 8714 · /raw/multi_line_order_count 2139 · lines_per_order max 10
```

### E3 — không đổi code; validator governance
(Output nguyên văn được nối vào cuối file này sau lần chạy cuối — xem mục
"Validator run cuối".)

## File Đã Thay Đổi (Files Changed)

Created:
- `docs/tasks/TASK-PRA-000-persistent-reporting-analytics-plan.md`
- `docs/sessions/S072-persistent-reporting-analytics-planning.md`

Modified:
- `PROJECT/PROJECT_PROGRESS.md` (khối PLANNED — PHASE-PRA; pointer đầu mục "Session tiếp theo")
- `PROJECT/LO_TRINH_DE_HIEU.md` (ghi chú đầu file; mục "KẾ HOẠCH MỚI")

Deleted:
- (không)

## Quyết Định Chính (Key Decisions)
- Đây là quyết định **đề xuất** của session, chưa phải DEC được Owner
  ratify; không thêm entry vào `PROJECT/PROJECT_DECISIONS.md` cho tới khi
  Owner trả lời mục N của kế hoạch.
- Hai origin lịch sử tách bảng, tách cột `origin`, không UNION không nhãn.
- `ORDER_KEY = Số BH chuẩn hoá` + guard 90 ngày; `ORDER_LINE_KEY =
  (ORDER_KEY, product_key, occurrence_index)` + `line_fingerprint`.
- Hai trục phiên bản (nguồn / kết quả) tách biệt; RESULT_REVISED không phải
  conflict nguồn.
- Persistence đặt **bên cạnh** pipeline (đọc `ImportResult` +
  `PriceResolutionRecord[]` + presented lines), không sửa pipeline; Golden
  Baseline là gate.
- Điều hướng tab ngang + ctx-bar theo Tracking; không sidebar.
- Driver DB chỉ ở `tools/db/` (mới) hoặc `app/web/`; `app/modules/` không
  biết DB (ADR-101, `CHECK-105D-17`).

## Rủi Ro / Vướng Mắc (Risks / Blockers)
- Chặn mở slice 1–2: Owner chưa trả lời N.1 (DB production), N.2 (coverage),
  N.3 (CHANGED), N.4 (REMOVED), N.12 (ratify amendment ADR-101).
- `CONFLICT DETECTED` ADR-101 (FastAPI/React) ↔ implementation (Flask/Jinja)
  — ghi nhận, đề xuất amendment, không tự giải quyết.
- Xem mục O của kế hoạch cho bảng rủi ro đầy đủ.

## Hạng Mục Regression (Regression Items)
- Không. Không chạm code; không chạy full test suite (không cần cho tài
  liệu; môi trường session không cài Flask). Golden Baseline không bị ảnh
  hưởng.

## Chưa Được Thay Đổi (Do Not Change Yet)
- Protected core: Product Identity Authority, PP/PP History/Baseline,
  PricingEffectiveDate/temporal semantics, Accounting reconciliation,
  AUTO/Pending safety.
- `app/modules/exporting/excel_exporter.py` — chỉ được tách hàm
  `present_lines()` ở slice 2 với test parity byte-identical.
- `RunStore`/R2 object model — giữ nguyên; history DB là lớp thêm.
- Tracking — mọi thứ.

## Session Tiếp Theo Được Khuyến Nghị (Next Recommended Session)
Owner trả lời N.1–N.4 + N.12 (một tin nhắn là đủ) → mở **TASK-PRA-001
(Slice 1 — Legacy reference + nền DB)**: Roadmap Finalization 9 bước, tạo
task file từ `governance/templates/TASK_DEFINITION_TEMPLATE.md`, freeze
Completion Gate từ ACCEPTANCE_CRITERIA của slice 1 trong kế hoạch, Ready
Gate gồm N.1 đã chốt + file Excel cũ có trên máy chạy (không commit) + ADR
amendment đã ghi. Chuẩn bị luôn fixture hai-snapshot cho slice 2.

## File Agent Tiếp Theo Cần Đọc (Files Next Agent Should Read)
- `CLAUDE.md`
- `PROJECT/PROJECT_PROGRESS.md` (khối "PLANNED — PHASE-PRA")
- `docs/tasks/TASK-PRA-000-persistent-reporting-analytics-plan.md` (đặc biệt mục F, G, H, I, J, M, N)
- `docs/analysis/01_DATA_MAPPING.md`, `docs/analysis/05_EXCEPTIONS.md`
- `app/web/storage_backend.py`, `app/web/run_registry.py`, `tools/storage/r2_store.py`
- `app/modules/domain/models.py`, `app/modules/exporting/excel_exporter.py`
- `tests/fixtures/golden/expected/period_2026_01.json` (hình dạng analytics de-facto)
- `docs/adr/ADR-101-architecture-and-stack.md` (để viết amendment)

## Validator run cuối (E3, nguyên văn, 2026-09-02)

```
$ git diff --check && echo diff-check clean
diff-check clean
$ git status --short
 M PROJECT/LO_TRINH_DE_HIEU.md
 M PROJECT/PROJECT_PROGRESS.md
?? docs/sessions/S072-persistent-reporting-analytics-planning.md
?? docs/tasks/TASK-PRA-000-persistent-reporting-analytics-plan.md
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
Quét 195 file .md (loại trừ 10 file trong governance/reference/history/, docs/audit/).
3 reference không phân giải được:
- docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> /README.md
- docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> CODE_OF_CONDUCT.md
- docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> CONTRIBUTING.md
exit=1

# Đối chiếu baseline (git stash -u, chạy lại validate_reference_integrity.py trên cây làm việc KHÔNG có thay đổi S072):
Quét 193 file .md (loại trừ 10 file trong governance/reference/history/, docs/audit/).
3 reference không phân giải được:
- docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> /README.md
- docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> CODE_OF_CONDUCT.md
- docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> CONTRIBUTING.md
# → 3 reference hỏng là có sẵn từ trước (task REM-T06 DO_WHEN_IDLE), không do S072; S072 thêm 0 reference hỏng.
```
