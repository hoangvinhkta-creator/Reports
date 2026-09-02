# BÀN GIAO SESSION (SESSION HANDOFF)

Session ID:
S075

Task:
TASK-PRA-001 — Legacy Reference Vertical (Excel cũ → Import → Persist →
Query → Reports Web)

Task Mode:
MAJOR

Project Profile:
PRODUCT

Status:
IMPLEMENTED — chờ Independent Review VÀ chờ Owner phân xử
`CHANGE_BUDGET_EXCEEDED`. KHÔNG merge canonical trong phiên này.

Nhánh: `claude/reports-pipeline-architecture-gj8bji`.
Base authority: `b50e8bc29b92e8f5199675cfc8574332970fe1b9` (close-out S074) —
đã xác minh commit tồn tại, nhánh chứa nó, worktree sạch, 0 commit behind
nhánh mặc định `claude/extract-upload-repo-gq2ws4`.

## Kết Quả (Result)

Vertical hoàn chỉnh chạy được đầu-cuối:

```
Workbook "Báo cáo Kinh doanh" (Excel cũ)
   → app/legacy/parser.py      (đọc, giữ nguyên trạng, annotate lỗi)
   → app/web/history_store.py  (SQLAlchemy Core, engine tiêm được)
   → migration 0001_legacy     (SQLite local/test · PostgreSQL production)
   → LegacyRepository.query_*  (theo năm/tháng, theo bản import)
   → /nhan-vien · /doanh-so-ngay · /du-lieu
   → Owner thấy số cũ, mọi số đeo nhãn LEGACY + đơn vị, ô lỗi có dấu nhắc
```

Ba điều quan trọng nhất đã được chứng minh bằng test, không phải bằng lời:

1. **Không tính lại số cũ.** Fixture có ô mang giá trị `999` trong khi công
   thức của chính nó là `=G9/5.5%` (kết quả đúng công thức ~547.272). Hệ
   thống lưu và hiển thị `999`. Quét AST: không có phép chia/nhân nào trong
   `app/legacy/`; quét mã sau khi xoá mọi chuỗi/chú thích: `/2`, `/ 2`,
   `5.5%` không xuất hiện trong logic.
2. **Số cũ không bao giờ hiển thị thiếu nhãn.** Mọi giá trị đi qua đúng một
   macro Jinja; test trích TẤT CẢ ô số từ HTML và khẳng định ô nào cũng
   mang `LEGACY` + đơn vị.
3. **Không có đường nào biến sự cố thành "chưa có dữ liệu".** Thiếu cấu
   hình → app không khởi động; schema cũ → app không khởi động; DB lỗi lúc
   request → HTTP 503. Trang rỗng chỉ xuất hiện khi dữ liệu THẬT SỰ rỗng.

## Subtask Đã Hoàn Thành (Subtasks Completed)
- PRA-001.1 `tools/db/` + Alembic `0001_legacy` (up/down PASS trên SQLite thật).
- PRA-001.2 Importer thuần + fixture Excel anonymized cài sẵn A1/A2/A4/A6.
- PRA-001.3 `LegacyRepository` + versioning (fingerprint, `is_current`).
- PRA-001.4 5 route + layout/tab bar + CSS token `--tp-*`.
- PRA-001.6 `render.yaml`, `Dockerfile`, deployment doc, PROGRESS/LO_TRINH.

## Subtask Còn Lại (Subtasks Remaining)
- PRA-001.5 — chạy `tools/analysis/verify_legacy_import.py` trên FILE THẬT.
  Script đã viết và chạy PASS trên fixture (`matched=628 mismatched=0`);
  file thật không có trong Claude Cloud và KHÔNG được commit (chứa PII).
- Owner phân xử `CHANGE_BUDGET_EXCEEDED` (xem mục cùng tên trong file task).
- Independent Review.

## Tóm Tắt Completion Gate (Completion Gate Summary)

Required:
8 check REQUIRED (01–08) + CHECK-10; CHECK-09 là RECOMMENDED.

PASS:
CHECK-PRA001-02, -03, -04, -05, -06, -07, -08, -10 (8 check, đều E1).

FAIL:
(không)

BLOCKED:
CHECK-PRA001-09 (DDL trên PostgreSQL thật) — session không có PostgreSQL và
không được tự tạo dịch vụ trả phí; trở thành gate deploy của Owner, quy
trình đã viết ở `docs/deployment/S071_DEPLOYMENT.md` bước 8–12.

NOT_TESTED:
CHECK-PRA001-01 (fidelity trên file Excel THẬT) — đúng điều khoản Ready Gate
đã lường trước: thiếu file thật thì ghi NOT_TESTED và thành gate Owner.

## Evidence Xác Minh (Verification Evidence)

| Check ID | Status | Evidence Level | Evidence | Executed By | Timestamp |
|---|---|---|---|---|---|
| S075-V1 | PASS | E1 | Baseline full suite đầu phiên: `1494 passed, 11 skipped` | Claude (S075) | 2026-09-02 |
| S075-V2 | PASS | E1 | Full regression cuối phiên: `1586 passed, 11 skipped` (+92, 0 mất, 0 skip mới) | Claude (S075) | 2026-09-02 |
| S075-V3 | PASS | E1 | `alembic upgrade head` → 4 bảng + `version_num='0001_legacy'`; `downgrade base` → xoá sạch 4 bảng | Claude (S075) | 2026-09-02 |
| S075-V4 | PASS | E1 | `verify_legacy_import` trên fixture + SQLite đã migrate: `matched=628 mismatched=0` (exit=0) | Claude (S075) | 2026-09-02 |
| S075-V5 | PASS | E1 | Validator governance 4/5 PASS; reference integrity chỉ còn 3 finding có sẵn của REM-T06 | Claude (S075) | 2026-09-02 |
| S075-V6 | PASS | E1 | `git diff --check` sạch | Claude (S075) | 2026-09-02 |

## File Đã Thay Đổi (Files Changed)

Xem "Đăng Ký File Đã Thay Đổi" trong
`docs/tasks/TASK-PRA-001-legacy-reference-vertical.md` (danh sách đầy đủ).

## Quyết Định Chính (Key Decisions)

Không có quyết định nghiệp vụ mới nào được tạo trong phiên này — đó là chủ
ý. Ba lựa chọn KỸ THUẬT sau nằm trong ngữ nghĩa đã freeze, ghi lại để
reviewer không phải đoán:

1. **`ExactNumeric` (`tools/db/schema.py`).** Cột `NUMERIC` trên SQLite mang
   affinity số: chuỗi `87.6` bị biến thành số thực nhị phân. Với một hệ
   thống mà fidelity là ranh giới chấp nhận cứng, đó là sửa một con số mà
   công cụ không có thẩm quyền sửa. Nên: PostgreSQL (production) giữ đúng
   kiểu `NUMERIC` như DATA_MODEL_MINIMUM freeze, SQLite (local/test) lưu
   chuỗi thập phân nguyên văn và dựng lại `Decimal` khi đọc.
2. **Phân loại dòng Summary theo cấu trúc công thức, không theo offset dòng.**
   Số dòng người bán mỗi tháng thay đổi (tháng 03.2026 có thêm "Linh"), nên
   mọi offset cứng sẽ sai ở kỳ nào đó. Dòng có tham chiếu chéo sheet =
   `SELLER`; `SUM(...)/2` = `YEAR_TOTAL`; `SUM(...)` = `MONTH_TOTAL`; tỉ lệ
   cùng sheet = `PROGRESS`.
3. **`seller_label` lấy nguyên văn từ ô chữ gần cột dữ liệu nhất trong vùng
   nhãn (A–B).** Không chuẩn hoá, không map sang tên nhân viên của pipeline
   — legacy và pipeline là hai origin tách biệt và không được trộn.

## Rủi Ro / Vướng Mắc (Risks / Blockers)

- **`CHANGE_BUDGET_EXCEEDED` — cần Owner phân xử.** 1.024 dòng logic
  production Python so với ngưỡng cứng 600 (930 nếu chỉ tính đúng tập file
  mà CHANGE_BUDGET liệt kê). Ba phương án A/B/C đã viết trong file task;
  session này KHÔNG tự chọn phương án nào.
- CHECK-01 và CHECK-09 phụ thuộc hai thứ session không thể có: file Excel
  thật và một PostgreSQL thật. Cả hai đã có quy trình viết sẵn cho Owner.
- `average_per_day` của `legacy_monthly_reference` luôn `NULL`:
  `docs/analysis/02_FORMULA_MAPPING.md` §5 không xác định ô nào trong
  DataChart mang ý nghĩa đó. Tính từ tổng tháng = tạo một con số mới, nên
  không làm. `UNKNOWN` — chờ Owner chỉ đúng ô, hoặc bỏ cột ở slice sau.

## Hạng Mục Regression (Regression Items)

- `/history` không còn render trang riêng; nó redirect (302) sang `/du-lieu`
  theo scope item 4 của task. Bốn test trong `tests/test_web_server.py` đã
  đổi endpoint tương ứng, assertion giữ nguyên; redirect có test riêng.
- `app/web/templates/history.html` bị xoá, nội dung chuyển vào `du_lieu.html`.

## Chưa Được Thay Đổi (Do Not Change Yet)

- Protected core: `app/modules/**`, `app/pipeline.py`, `app/composition.py`,
  exporter, `RunStore`/R2 — KHÔNG bị chạm trong phiên này.
- Tracking: KHÔNG đọc, KHÔNG ghi, KHÔNG deploy. Design token `--tp-*` được
  chép từ ĐẶC TẢ ở mục E của TASK-PRA-000, không hot-link file nào.
- Schema PRA-002: không prebuild. Hai test khoá điều này.

## Session Tiếp Theo Được Khuyến Nghị (Next Recommended Session)

1. Owner phân xử `CHANGE_BUDGET_EXCEEDED` (A / B / C) → ghi DEC.
2. Independent Review TASK-PRA-001 trên SHA chính xác của phiên này.
3. Owner deploy: tạo Render PostgreSQL, dán `HISTORY_DATABASE_URL`
   (`docs/deployment/S071_DEPLOYMENT.md` bước 8–12) → đóng CHECK-09.
4. Owner chạy `verify_legacy_import` trên "Báo cáo Kinh doanh 2026.xlsx"
   → đóng CHECK-01. Nếu có ô lệch: KHÔNG sửa số, mà xem lại giả định phân
   loại dòng của parser và báo lại.
5. Chỉ sau khi 1–4 xong mới tính tới TASK-PRA-002.

## File Agent Tiếp Theo Cần Đọc (Files Next Agent Should Read)
- `docs/tasks/TASK-PRA-001-legacy-reference-vertical.md` (Completion Gate đã
  điền + mục ESCALATION)
- `app/legacy/parser.py`, `app/legacy/defects.py`
- `tools/db/schema.py` (đặc biệt `ExactNumeric`)
- `app/web/history_store.py`, `app/web/server.py` (5 route mới)
- `tests/fixtures/legacy/build_legacy_workbook.py` (hình dạng fixture)
- `docs/analysis/05_EXCEPTIONS.md` (A1–A6), `docs/analysis/02_FORMULA_MAPPING.md` §3, §5

## Validator run cuối (nguyên văn, 2026-09-02, S075)

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
Quét 203 file .md (loại trừ 10 file trong governance/reference/history/, docs/audit/).
3 reference không phân giải được:
- docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> /README.md
- docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> CODE_OF_CONDUCT.md
- docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> CONTRIBUTING.md
exit=1
# 3 reference hỏng là PRE_EXISTING (REM-T06 DO_WHEN_IDLE), giống baseline
# S073; S075 thêm 0 reference hỏng (203 file quét so với 199 ở S073).
```

## Test run cuối (nguyên văn, 2026-09-02, S075)

```
$ python3 -m pytest -q          # BASELINE, đầu phiên, trước mọi thay đổi
1494 passed, 11 skipped in 32.19s

$ python3 -m pytest -q          # CUỐI PHIÊN
1586 passed, 11 skipped in 38.24s

$ alembic upgrade head && alembic downgrade base
UP OK
['alembic_version', 'legacy_daily_sales', 'legacy_import', 'legacy_monthly_reference', 'legacy_summary_row']
version [('0001_legacy',)]
DOWN OK
after down: ['alembic_version']

$ python3 -m tools.analysis.verify_legacy_import <fixture>.xlsx
matched=628 mismatched=0
exit=0
```
