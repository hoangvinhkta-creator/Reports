# SESSION HANDOFF

Session ID:
S005

Task:
REM-T03 — Validator deployment-root và reference-integrity
REM-T07 — CI enforcement layer

Task Mode:
MAJOR (cả hai)

Project Profile:
PRODUCT

Status:
DONE (cả hai)

Date:
2026-08-23 (UTC)

Branch:
`claude/s001-discovery-pka3fu`

Commit lúc mở session:
`fb3838c`

## Kết Quả

Thực hiện cả REM-T03 và REM-T07 trong cùng session theo yêu cầu trực tiếp
của chủ dự án. Cả 4 task chính của PHASE-01 (REM-T02, REM-T03, REM-T04,
REM-T07) giờ đã DONE — bước tiếp theo là Phase Gate 01, không phải một task
REM-T mới.

### REM-T03

1. Mở rộng `validate_structure.py`: thêm `find_git_root()` (đi ngược lên tìm
   `.git`) và `check_deployment_root()`, assert gốc mà script tự resolve
   (`parents[3]`) trùng git root thật. FAIL nếu lệch, `NOT_APPLICABLE` (không
   phải PASS) nếu không có `.git` nào. Output PASS/FAIL gốc được giữ nguyên,
   chỉ thêm một dòng — evidence lịch sử trích dẫn output cũ vẫn là bản ghi
   đúng tại thời điểm nó được thu thập.
2. Viết `governance/scripts/governance/fixtures/regression_nested_layout.py`
   — regression test tự tạo layout lồng trong thư mục tạm, chạy subprocess,
   xác nhận FAIL đúng lý do (không lẫn với missing-path).
3. Viết `validate_reference_integrity.py` mới — quét mọi `.md` tìm reference
   `.md`/`.py`/`.svg` trong backtick, phân giải theo quy tắc S001 (root trước,
   rồi thư mục file đang tham chiếu).
4. **Thử mở rộng sang reference dạng thư mục** (để tái hiện đủ 3 finding gốc
   của S001, kể cả `templates/` của FIND-004) — **gây 20 false positive** trên
   HEAD hoàn toàn lành mạnh (ví dụ minh họa trong prose như `src/`, `shared/`,
   tên thư mục cũ trong tường thuật lịch sử). Đúng bài học của FIND-005: một
   validator kêu sai nhiều sẽ bị phớt lờ. Revert về phạm vi `.md`/`.py`/`.svg`
   như Objective/Scope gốc đã khai báo. Phát hành COMPLETION GATE CHANGE
   PROPOSAL (DEC-013) thu hẹp CHECK-T03-03 từ 3 xuống 2 reference tái hiện.
5. Cập nhật `governance/scripts/governance/README.md` — tài liệu hóa đủ 5
   validator + fixture.

### REM-T07

1. `.github/workflows/governance.yml` — trigger `push`/`pull_request`,
   `permissions: contents: read`, action pin theo full SHA (tra cứu thật qua
   `git ls-remote --tags` lên `actions/checkout`/`actions/setup-python`,
   không đoán).
2. Discovery bằng `find ... -path '*/governance/scripts/governance'`, không
   hard-code đường dẫn — đúng Critical Design Constraint. Required set theo
   TÊN file (không phải đếm số lượng), nên chịu được việc
   `validate_reference_integrity.py` (mới từ REM-T03 cùng session) xuất hiện
   thêm mà không cần sửa workflow.
3. **Push để CI chạy thật lần đầu → FAIL.** Không phải lỗi workflow — CI bắt
   được đúng 2 broken reference thật mà chính agent vừa đưa vào lúc soạn
   evidence text cho REM-T03 (một path thiếu prefix, một forward-reference
   tới file handoff chưa tồn tại — cũng lộ ra Status/Exit Criteria của REM-T03
   đã bị tick DONE quá sớm). Sửa, push lại → **PASS thật**.
4. Test CHECK-T07-03: tạo nhánh `scratch/ci-failure-test`, phá `Selected
   Profile` thành giá trị không hợp lệ, push, quan sát CI FAIL đúng tại
   `validate_project_state.py`. **Không xóa được nhánh remote** — cả
   `git push --delete` lẫn gọi GitHub API DELETE trực tiếp đều bị proxy chặn
   (403 "Write access to this GitHub API path is not permitted through this
   proxy"). Ghi nhận là DEC-014, cần owner xóa thủ công.
5. Ghi nhận CI là nguồn E2 hợp lệ vào `PROJECT/PROJECT_PROFILE.md` (subtask
   07.6) kèm branch protection là khuyến nghị cho owner (subtask 07.7, không
   tự thiết lập).

## Subtask Hoàn Thành

REM-T03: 03.1–03.6 (toàn bộ).
REM-T07: 07.1–07.7 (toàn bộ, 07.7 dưới dạng khuyến nghị ghi lại, không tự
thiết lập).

## Subtask Còn Lại

Không có cho cả hai task.

## Tóm Tắt Completion Gate

| Task | Required | PASS | FAIL | BLOCKED | NOT_TESTED |
|---|---|---|---|---|---|
| REM-T03 | 4 | 4 | 0 | 0 | 0 |
| REM-T07 | 6 REQUIRED + 1 RECOMMENDED | 7 | 0 | 0 | 0 |

## Bằng Chứng Xác Minh

### REM-T03

| Check ID | Status | Evidence Level | Tóm Tắt Evidence |
|---|---|---|---|
| CHECK-T03-01 | PASS | E1 | Fixture layout lồng → exit khác 0, thông báo rõ ràng, cô lập đúng failure mode |
| CHECK-T03-02 | PASS | E1 | Repo hiện tại → `GOVERNANCE STRUCTURE: PASS`, `Deployment root: PASS` |
| CHECK-T03-03 | PASS | E1 | Baseline `0394267` (git worktree) → tái hiện đúng 2/2 reference trong phạm vi `.md`, khớp CHK-S001-06 |
| CHECK-T03-04 | PASS | E1 | HEAD (post-REM-T04) → `REFERENCE INTEGRITY: PASS`, 0 hỏng |

### REM-T07

| Check ID | Status | Evidence Level | Tóm Tắt Evidence |
|---|---|---|---|
| CHECK-T07-01 | PASS | E1 | Run `32613467285` hoàn tất, thực thi 5 validator vô điều kiện |
| CHECK-T07-02 | PASS | E1 | Run `32613528195` → `conclusion: success`, tất cả bước `success` |
| CHECK-T07-03 | PASS | E1 | Run `32613562660` trên nhánh scratch → `conclusion: failure` đúng tại `validate_project_state.py` |
| CHECK-T07-04 | PASS | E1 | Mô phỏng layout lồng cục bộ → discovery vẫn tìm thấy đủ 6 script |
| CHECK-T07-05 | PASS | E1 | Log job có `::notice::` skip `validate_refactor_preservation.py` kèm lý do |
| CHECK-T07-06 | PASS | E1 | `permissions: contents: read`, không secret, action pin SHA đầy đủ |
| CHECK-T07-07 | PASS | E0 | `PROJECT/PROJECT_PROFILE.md` ghi nhận CI là nguồn E2 + khuyến nghị branch protection |

Trạng thái E2 của bản thân session này: KHÔNG THU THẬP riêng — cả hai task
Risk 2/3 chỉ yêu cầu E1 tối thiểu theo `governance/core/EVIDENCE_STANDARD.md`.
CI (REM-T07) giờ tồn tại như một nguồn E2 cho các task rủi ro cao *trong
tương lai*.

## File Đã Thay Đổi

Đã tạo:
- `governance/scripts/governance/validate_reference_integrity.py`
- `governance/scripts/governance/fixtures/regression_nested_layout.py`
- `.github/workflows/governance.yml`
- `docs/sessions/S005-ci-and-validators.md`

Đã sửa:
- `governance/scripts/governance/validate_structure.py` — deployment-root check
- `governance/scripts/governance/README.md` — tài liệu hóa 5 validator + fixture
- `docs/tasks/TASK-REM-T03-validator-hardening.md` — evidence, status DONE
- `docs/tasks/TASK-REM-T07-ci-enforcement.md` — evidence, status DONE
- `PROJECT/PROJECT_PROFILE.md` — mục CI/CD
- `PROJECT/PROJECT_DECISIONS.md` — DEC-013, DEC-014
- `PROJECT/PROJECT_PROGRESS.md` — roadmap, gate table, findings, session tiếp theo
- `docs/audit/REMEDIATION_ROADMAP.md` — REM-T03/T07 → DONE, traceability, dependency graph

Nhánh phụ (không nằm trong `claude/s001-discovery-pka3fu`):
- `scratch/ci-failure-test` — tạo để test CHECK-T07-03, xóa local, **KHÔNG
  xóa được trên remote** (DEC-014, cần owner xóa thủ công).

**Không đụng tới** `docs/audit/S001_*` — bản ghi audit bất biến.

## Quyết Định Chính

- DEC-013 — COMPLETION GATE CHANGE PROPOSAL cho CHECK-T03-03 (2/3 thay vì 3/3
  reference tái hiện; loại trừ reference dạng thư mục có chủ đích sau khi thử
  gây 20 false positive)
- DEC-014 — Ghi nhận giới hạn môi trường: không xóa được nhánh scratch trên
  GitHub qua session này (proxy chặn write tới path xóa ref)

## Rủi Ro / Blocker

Blocker:
- Không có.

Rủi ro:
- RSK-001, RSK-004, RSK-005 — **đã đóng** trong session này (xem
  `PROJECT/PROJECT_PROGRESS.md`).
- RSK-002 — chưa đổi, chờ REM-T05.
- RSK-006 — chưa đổi, vẫn là bài học đang áp dụng.
- RSK-008 (mới) — nhánh scratch không xóa được trên GitHub, cần owner xử lý.

## Hạng Mục Regression

- Không có.

## Chưa Được Thay Đổi

- `docs/audit/S001_*` — bản ghi audit bất biến.
- `governance/reference/history/` — kho lưu trữ đóng băng.
- Gate PHASE-02/03 (REM-T05, REM-T06) — vẫn PRELIMINARY, cố ý chưa freeze.
- Branch protection trên GitHub — chỉ khuyến nghị, không tự thiết lập (ngoài
  thẩm quyền agent).

## Session Tiếp Theo Được Đề Xuất

S006 — **Phase Gate 01**, không phải một REM-T task. Xác nhận cả 4 task
chính của PHASE-01 hoạt động cùng nhau đúng (checklist đầy đủ trong
`docs/audit/REMEDIATION_ROADMAP.md` → "Phase Gate 01" và
`PROJECT/PROJECT_PROGRESS.md` → "Session Tiếp Theo"), rồi merge nhánh làm
việc vào nhánh mặc định như thường lệ.

## File Agent Tiếp Theo Nên Đọc
1. `CLAUDE.md`
2. `PROJECT/PROJECT_PROFILE.md`
3. `PROJECT/PROJECT_PROGRESS.md`
4. `docs/sessions/S005-ci-and-validators.md`  ← file này
5. `docs/audit/REMEDIATION_ROADMAP.md` → mục "Phase Gate 01"
6. `governance/core/PHASE_RELEASE_GATE_STANDARD.md`

## Prompt Mở Session Tiếp Theo

```text
Đây là S006 — Phase Gate 01 cho PHASE-01 (Governance Foundation Repair).
Không phải một REM-T task riêng — là bước xác nhận cả 4 task chính
(REM-T02, REM-T03, REM-T04, REM-T07) hoạt động cùng nhau đúng, trước khi
mở PHASE-02.

Chạy Session Open Protocol:
1. Đọc CLAUDE.md
2. Đọc PROJECT/PROJECT_PROFILE.md
3. Đọc PROJECT/PROJECT_PROGRESS.md
4. Đọc docs/sessions/S005-ci-and-validators.md
5. Đọc docs/audit/REMEDIATION_ROADMAP.md mục "Phase Gate 01"
6. Đọc governance/core/PHASE_RELEASE_GATE_STANDARD.md

Chạy checklist Phase Gate 01 (đã liệt kê trong PROJECT_PROGRESS.md), tự xác
nhận lại bằng cách thực thi thật — không lấy lời khai của session trước làm
evidence. Sau khi Phase Gate 01 PASS, merge nhánh làm việc vào nhánh mặc
định, và báo owner xóa thủ công nhánh scratch/ci-failure-test còn sót lại
trên GitHub (DEC-014).
```
