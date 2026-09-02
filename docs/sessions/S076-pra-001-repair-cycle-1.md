# BÀN GIAO SESSION (SESSION HANDOFF)

Session ID:
S076

Task:
`TASK-PRA-001` — repair cycle **1/1** sau Independent Review
(`REVIEW_RESULT = CHANGES_REQUIRED` trên
`7d84072765288b7a9dc28679a09325fce7860b48`)

Task Mode:
MAJOR (repair cycle, không phải feature session)

Project Profile:
PRODUCT

Status:
IMPLEMENTED — hai blocking finding đã sửa; chờ re-review.

Nhánh: `claude/reports-pipeline-architecture-gj8bji`.
Repair base: `7d84072765288b7a9dc28679a09325fce7860b48` (KHÔNG rewrite).

## Kết Quả (Result)

Hai blocking finding đều là cùng một loại lỗi, ở hai tầng khác nhau: **một
sự cố được trình bày như một trạng thái bình thường.** Đó đúng là loại sai
mà cả TASK-PRA-001 tồn tại để ngăn, nên review bắt được chúng là đúng.

### FIND-PRA001-R01 — thiếu dòng nguồn vẫn báo "khớp 100%"

Verifier duyệt từ DB → Excel, nên nó chỉ trả lời được *"những gì đã nhập có
đúng không"*, không bao giờ trả lời được *"có gì chưa được nhập không"*. Tái
tạo trước repair (giữ nguyên giá trị nghiệp vụ, bỏ dấu hiệu công thức khỏi
`Summary 2025`):

```
Summary 2025 imported rows = 0
Source rows có giá trị nghiệp vụ: [4, 5, 6]
VERIFIER: matched=372 mismatched=0     ← mất trọn một kỳ mà vẫn PASS
```

Sửa theo chính sách Owner (DEC-168) — **không** đoán `row_kind` từ việc dòng
có số, và **không** bỏ qua im lặng:

1. `app/legacy/parser.py` — dòng có giá trị nghiệp vụ ở cột dữ liệu đã
   freeze nhưng không khớp contract phân loại → `LegacyImportError` nêu đích
   danh sheet và số dòng, kèm `UNKNOWN / OWNER_DECISION_REQUIRED`.
2. `tools/analysis/verify_legacy_import.py` — vòng lặp Summary đổi chiều
   thành EXCEL → DB, thêm ba con số coverage, và thiếu dòng nguồn = FAIL
   (exit khác 0) ngang hàng với lệch giá trị.

Sau repair, đúng case reviewer:

```
UNACCOUNTED Summary 2025!4
UNACCOUNTED Summary 2025!5
UNACCOUNTED Summary 2025!6
SUMMARY_SOURCE_ROWS_WITH_VALUES = 16
SUMMARY_IMPORTED_ROWS           = 13
SUMMARY_UNACCOUNTED_ROWS        = 3
matched=580 mismatched=0
exit=1                                  ← mismatched=0 KHÔNG còn cứu được
```

### FIND-PRA001-R02 — sự cố database bị đổ lỗi cho file của Owner

`_guarded` biến lỗi history store thành `abort(503)`, mà `abort` ném
`HTTPException` — và `except Exception` trong route import đã nuốt nó, trả
về redirect 302 kèm "Không đọc được workbook legacy". Owner sẽ đi sửa
workbook cho một lỗi hạ tầng, và `CHECK-PRA001-06` bị phá trong im lặng.

Sửa tối thiểu, đúng hướng review đề xuất: thêm `except HTTPException: raise`
trước `except Exception` trong đúng route đó. Không redesign error handling
của web app.

Cả hai test repair đã được chứng minh là **fail trên code trước repair**:

```
$ pytest -k "write_path_is_503_not_a_blamed"     # sau khi gỡ repair R02
FAILED ... assert 302 == 503
$ pytest -k "fails_loudly"                       # sau khi gỡ repair R01
FAILED ... DID NOT RAISE LegacyImportError
```

## Subtask Đã Hoàn Thành (Subtasks Completed)
- R01: parser guard + verifier source coverage + 11 test hồi quy.
- R02: `except HTTPException: raise` + 3 test đường ghi.
- N03: bổ sung `Expected Touch Area` hai file frozen gate thực sự cần.
- DEC-168 (change budget exception + hợp đồng nghiệp vụ R01).
- Cập nhật evidence `CHECK-PRA001-01`, `CHECK-PRA001-06`.

## Subtask Còn Lại (Subtasks Remaining)
- Re-review độc lập.
- `REAL_DATA_ACCEPTANCE` — vẫn `WAITING_OWNER_INPUT`.
- `CHECK-PRA001-09` — vẫn `BLOCKED` (cần PostgreSQL thật).

## Tóm Tắt Completion Gate (Completion Gate Summary)

Required:
8 check REQUIRED (01–08) + CHECK-10; CHECK-09 RECOMMENDED.

PASS:
CHECK-PRA001-02, -03, -04, -05, -06, -07, -08, -10.
`CHECK-06` mở rộng: nay bao gồm cả DB failure trên đường GHI/import.

FAIL:
(không)

BLOCKED:
CHECK-PRA001-09 — cần PostgreSQL thật, gate deploy Owner.

NOT_TESTED:
CHECK-PRA001-01 — cần file Excel THẬT. Evidence đã viết lại: fidelity gồm
`VALUE MATCH` + `SOURCE COVERAGE`; `628/0` không còn dùng một mình.

## Evidence Xác Minh (Verification Evidence)

| Check ID | Status | Evidence Level | Evidence | Executed By | Timestamp |
|---|---|---|---|---|---|
| S076-V1 | PASS | E1 | R01 tái tạo trước repair: `Summary 2025 imported rows = 0`, verifier `matched=372 mismatched=0` | Claude (S076) | 2026-09-02 |
| S076-V2 | PASS | E1 | R01 sau repair: parser raise `LegacyImportError`; verifier `SUMMARY_UNACCOUNTED_ROWS = 3`, exit=1 | Claude (S076) | 2026-09-02 |
| S076-V3 | PASS | E1 | R02 trước repair: `assert 302 == 503` FAIL; sau repair: HTTP 503, body không chứa "Không đọc được workbook" | Claude (S076) | 2026-09-02 |
| S076-V4 | PASS | E1 | PRA-001 focused suite: `106 passed` | Claude (S076) | 2026-09-02 |
| S076-V5 | PASS | E1 | Full regression: `1600 passed, 11 skipped` (từ `1586` ở S075, +14, 0 mất) | Claude (S076) | 2026-09-02 |
| S076-V6 | PASS | E1 | Validator 4/5 PASS; reference integrity chỉ còn 3 finding PRE_EXISTING của REM-T06 | Claude (S076) | 2026-09-02 |
| S076-V7 | PASS | E1 | Production logic LOC = 1.045 / ngân sách mới ~1.050 (DEC-168) | Claude (S076) | 2026-09-02 |

## File Đã Thay Đổi (Files Changed)

Xem khối "Repair cycle 1 (S076)" trong "Đăng Ký File Đã Thay Đổi" của
`docs/tasks/TASK-PRA-001-legacy-reference-vertical.md`.

## Quyết Định Chính (Key Decisions)

DEC-168 (Owner) — hai phần:
1. `PRA-001_CHANGE_BUDGET_EXCEPTION = APPROVED`, ngân sách ~1.050 dòng
   logic. Không cắt capability, không nén code để đạt chỉ tiêu 600.
2. Dòng Summary có giá trị nghiệp vụ mà contract không nhận ra → **FAIL
   TO**. Không auto-guess `row_kind` từ numeric values.

## Rủi Ro / Vướng Mắc (Risks / Blockers)

- Guard mới **có thể** làm workbook THẬT fail import nếu nó chứa dòng
  value-only hợp lệ mà contract chưa biết. Đây là hành vi Owner đã chọn:
  `REAL DATA ACCEPTANCE` phải DỪNG, ghi `UNKNOWN / OWNER_DECISION_REQUIRED`,
  bổ sung contract bằng một quyết định riêng dựa trên evidence thật —
  KHÔNG tự mở rộng parser semantics.
- `CHECK-01` / `CHECK-09` vẫn phụ thuộc file Excel thật và PostgreSQL thật.

## Hạng Mục Regression (Regression Items)

- `verify()` đổi kiểu trả về từ `tuple[int, list[str]]` sang
  `VerificationResult` (có `matched`, `mismatches`, ba trường coverage, và
  `ok`). Hai test cũ trong `tests/test_legacy_repository.py` đã cập nhật.
  Không có caller nào khác.
- Không có thay đổi hành vi nào ở `/`, `/run`, `/artifact/<run_id>`,
  `/feedback`, `/du-lieu`, `/nhan-vien`, `/doanh-so-ngay` cho đường đi bình
  thường (workbook đúng hình dạng, database khoẻ).

## Chưa Được Thay Đổi (Do Not Change Yet)

- Protected core, R2, Tracking, schema PRA-002 — KHÔNG bị chạm.
- N01/N02: không mở cleanup sweep. N04/N05/N06: DEFER theo chỉ thị review.

## Session Tiếp Theo Được Khuyến Nghị (Next Recommended Session)

1. Re-review độc lập trên SHA repair.
2. Owner deploy PostgreSQL → đóng CHECK-09.
3. Owner chạy `verify_legacy_import` trên workbook thật → đóng CHECK-01.
   Đọc CẢ hai phần: `mismatched` VÀ `SUMMARY_UNACCOUNTED_ROWS`.

## Validator run cuối (nguyên văn, 2026-09-02, S076)

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
Checked 99 REQUIRED PASS evidence record(s).
exit=0
REFERENCE INTEGRITY: FAIL
3 reference không phân giải được: 3 issue PRE_EXISTING của TASK-REM-T06.
exit=1
```

## Test run cuối (nguyên văn, 2026-09-02, S076)

```
$ python3 -m pytest -q
1600 passed, 11 skipped

$ python3 -m pytest tests/test_history_db.py tests/test_legacy_importer.py \
    tests/test_legacy_repository.py tests/test_web_legacy_routes.py \
    tests/test_legacy_source_coverage.py -q
106 passed

$ python3 -m tools.analysis.verify_legacy_import <fixture>.xlsx
SUMMARY_SOURCE_ROWS_WITH_VALUES = 16
SUMMARY_IMPORTED_ROWS           = 16
SUMMARY_UNACCOUNTED_ROWS        = 0
matched=628 mismatched=0
exit=0
```
