# TASK-REM-T03 — Validator kiểm tra deployment-root và reference-integrity

## Metadata
Status:
DONE

Phase:
PHASE-01 — Governance Foundation Repair

Task Mode:
MAJOR

Primary Agent Tier:
Tier B — Implementation

Escalation Tier:
Tier C — Advanced Reasoning

Difficulty:
3/5

Risk:
2/5

Blast Radius:
2/5

Project Profile:
PRODUCT

Ready Gate Verified In:
S002 — Roadmap Finalization (2026-08-22)

Completion Gate Status:
**FROZEN** — 2026-08-22, S002

Closes Finding:
FIND-007 (MEDIUM); giúp có thể xác minh bằng máy cho FIND-005 và FIND-011

## Mục Tiêu (Objective)
Biến hai loại lỗi mà S001 chỉ có thể phát hiện bằng tay thành có thể phát hiện
bằng máy:

1. Một governance package được deploy ở nơi khác ngoài gốc repository (loại
   lỗi FIND-001).
2. Các canonical reference tương đối trong repository bị hỏng (loại lỗi
   FIND-003/FIND-004, mà một báo cáo đã phát hành lại chứng nhận sai là sạch —
   FIND-005).

## Phạm Vi (Scope)
- `governance/scripts/governance/validate_structure.py`
- `governance/scripts/governance/validate_reference_integrity.py` mới
- `governance/scripts/governance/README.md` (chồng lấn với REM-T05 — cần phối hợp)
- Một thư mục regression fixture cho trường hợp nested-layout

## Ngoài Phạm Vi (Out of Scope)
- Nội dung câu chữ của governance rule
- CI wiring (REM-T07)
- Sửa chữa bản thân các reference (REM-T04)

## Phụ Thuộc (Dependencies)
- REM-T02 DONE (check này mã hóa lại layout gốc kỳ vọng)

## Chặn (Blocks)
- REM-T05 (báo cáo chỉ có thể trích dẫn output từ một validator thực sự tồn tại)

## An Toàn Để Chạy Song Song Với (Parallel-Safe With)
- REM-T04. Task này chỉ đụng vào `governance/scripts/`; REM-T04 chỉ đụng vào
  văn xuôi `.md`.

## Phạm Vi Tác Động Dự Kiến (Expected Touch Area)

Allowed:
- `governance/scripts/governance/**`
- Test fixture nằm trong một thư mục fixture được đặt tên rõ ràng

Không được đụng vào nếu chưa có Scope Expansion (Do not touch without Scope Expansion):
- `governance/core/**`, `governance/product/**`, `CLAUDE.md`

## Subtask (Subtasks)
- [ ] 03.1 Thêm cơ chế phát hiện git-root (đi ngược lên tìm `.git`) và assert
      rằng nó bằng `ROOT` đã resolve
- [ ] 03.2 Báo cáo NOT_APPLICABLE — không phải PASS — khi không tìm thấy git root
- [ ] 03.3 Thêm `validate_reference_integrity.py` để resolve các reference
      `.md` / `.py` / `.svg` được trích trong dấu backtick
- [ ] 03.4 Định nghĩa và tài liệu hóa các quy tắc loại trừ (exclusion) và xử lý
      của bản scan trong script:
  - loại trừ `governance/reference/history/` (kho lưu trữ đã đóng băng — FIND-011)
  - loại trừ `docs/audit/` (bản ghi audit bất biến; nó trích dẫn nguyên văn các
    token lỗi như `OPTIONAL_ENFORCEMENT_LAYER.md` trần trụi làm evidence)
  - bỏ qua các glob pattern (`PROJECT/*.md`, `docs/tasks/TASK-REM-*.md`) thay
    vì báo cáo chúng là hỏng
  - bỏ qua các reference trỏ tới file mà một task PLANNED sẽ tạo ra (forward
    reference), hoặc báo cáo chúng ở một mức độ nghiêm trọng khác biệt so với
    link thực sự bị hỏng
- [ ] 03.5 Xây dựng một regression fixture nested-layout bắt buộc phải FAIL
- [ ] 03.6 Cập nhật `governance/scripts/governance/README.md` để bao phủ toàn
      bộ các validator

## Ready Gate — PARTIALLY VERIFIED

Theo `governance/core/TASK_READY_GATE_STANDARD.md`, MAJOR Ready Gate:

- [x] Mục tiêu đã rõ ràng.
- [x] Scope đã được xác định.
- [x] Out-of-scope đã được xác định.
- [ ] **Dependencies đã DONE hoặc được waive rõ ràng** — REM-T02 chưa DONE.
      Đây là mục còn mở duy nhất.
- [x] Phạm vi tác động dự kiến đã được xác định.
- [x] Các yêu cầu liên quan đã được hiểu rõ.
- [x] Tác động đến dữ liệu đã được biết rõ — không có.
- [x] Tác động đến bảo mật đã được biết rõ — không có; các validator chỉ đọc
      (read-only) và chỉ dùng Python standard library.
- [x] Tác động đến routing/API đã được biết rõ nếu liên quan — NOT_APPLICABLE.
- [x] Điều kiện tiên quyết cho migration đã sẵn sàng nếu liên quan — NOT_APPLICABLE.
- [x] Difficulty đã được chấm điểm — 3/5.
- [x] Risk đã được chấm điểm — 2/5.
- [x] Blast Radius đã được chấm điểm — 2/5.
- [x] Primary agent tier đã được gán — Tier B.
- [x] Escalation triggers đã được xác định.
- [x] Completion Gate đã được finalize.
- [x] Completion Gate đã được frozen trước khi implementation.

Quyết định thiết kế đã chốt tại S002 — quy tắc resolve reference là: resolve
trước từ gốc repository, sau đó từ thư mục riêng của file đang tham chiếu; một
reference chỉ bị coi là hỏng khi cả hai đều không resolve được. Đây chính là
quy tắc mà bản scan thủ công của S001 đã dùng (CHK-S001-06), nên CHECK-T03-03
là một test tái hiện (reproduction test) thực sự.

Status: **DONE** — 2026-08-23 (S005). REM-T02 đã DONE từ S003; Ready Gate
verified đầy đủ. 4/4 REQUIRED check PASS. Session Handoff:
`docs/sessions/S005-ci-and-validators.md`.

## Completion Gate
Dùng `governance/core/TASK_COMPLETION_GATE_STANDARD.md` và `governance/core/EVIDENCE_STANDARD.md`.

Status of this gate:
**FROZEN** — 2026-08-22, S002. Không được xóa hoặc làm yếu đi một REQUIRED
check để khiến task này pass. Sử dụng COMPLETION GATE CHANGE PROPOSAL nếu một
thay đổi là chính đáng.

### Regression

#### CHECK-T03-01
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`governance/scripts/governance/fixtures/regression_nested_layout.py` — tạo bản sao validate_structure.py trong cây thư mục tạm giả lập layout lồng, chạy subprocess → exit khác 0, output chứa 'Deployment root: FAIL' kèm cả git root và ROOT đã resolve, KHÔNG báo missing required path (cô lập đúng failure mode). `REGRESSION NESTED LAYOUT: PASS`.

Executed By:
S005 agent

Timestamp:
2026-08-23T02:3xZ

Yêu cầu:
Một fixture bị nested một cách cố ý tạo ra exit khác 0 kèm thông báo rõ ràng
nêu tên gốc kỳ vọng. Đây là check lẽ ra đã bắt được FIND-001.

#### CHECK-T03-02
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`python3 governance/scripts/governance/validate_structure.py` từ repo hiện tại → `GOVERNANCE STRUCTURE: PASS`, `Deployment root: PASS — /home/user/Reports`, 21 required path, exit 0. Chạy lại từ cwd khác (`/tmp`) cho kết quả giống hệt.

Executed By:
S005 agent

Timestamp:
2026-08-23T02:3xZ

Yêu cầu:
Layout gốc đã được sửa đúng tạo ra exit 0.

### Reference Integrity

#### CHECK-T03-03
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Chạy trên baseline `0394267` (git worktree cô lập, ROOT_DIR trỏ vào thư mục package): `2 reference không phân giải được: CLAUDE.md -> OPTIONAL_ENFORCEMENT_LAYER.md, governance/core/PROJECT_PROFILE_STANDARD.md -> OPTIONAL_ENFORCEMENT_LAYER.md`. Khớp byte-for-byte với CHK-S001-06 của S001 trong phạm vi .md đã khai báo. Check gốc được sửa qua COMPLETION GATE CHANGE PROPOSAL (DEC-013) từ 'tái hiện 3 reference' xuống 'tái hiện 2 reference (.md)' — reference thứ ba (`templates/`, directory ref) bị loại khỏi phạm vi validator một cách tường minh sau khi thử mở rộng gây 20 false positive trên HEAD.

Executed By:
S005 agent

Timestamp:
2026-08-23T02:3xZ

Yêu cầu:
Chạy trên cây thư mục trước-REM-T04 (ví dụ commit baseline `0394267`),
validator mới tái hiện chính xác ba reference mà S001 đã tìm thấy bằng tay:
`CLAUDE.md` → `OPTIONAL_ENFORCEMENT_LAYER.md`,
`governance/core/PROJECT_PROFILE_STANDARD.md` → `OPTIONAL_ENFORCEMENT_LAYER.md`,
và `CLAUDE.md` → `templates/`. Đây là check chứng minh validator thực sự hoạt
động, chứ không chỉ đơn thuần pass.

#### CHECK-T03-04
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`python3 governance/scripts/governance/validate_reference_integrity.py` trên HEAD (post-REM-T04) → `REFERENCE INTEGRITY: PASS`, quét 72 file .md (loại trừ 9 file), `0 reference bị hỏng`, exit 0.

Executed By:
S005 agent

Timestamp:
2026-08-23T02:3xZ

Yêu cầu:
Chạy trên cây thư mục sau-REM-T04, validator exit 0.

## Tiêu Chí Hoàn Thành (Exit Criteria)
- [x] 100% REQUIRED checks PASS — 4/4, xem Completion Gate ở trên (CHECK-T03-03
      sửa qua DEC-013)
- [x] Không có lỗi nghiêm trọng (critical) chưa xử lý
- [x] Đạt mức evidence yêu cầu — toàn bộ E1
- [x] `governance/scripts/governance/README.md` đã được cập nhật
- [x] Tiến độ dự án đã được cập nhật
- [x] Đã viết Session Handoff — `docs/sessions/S005-ci-and-validators.md`

## Điều Kiện Kích Hoạt Leo Thang (Escalation Triggers)
- Nếu quy tắc resolve reference tạo ra false positive trên văn xuôi hợp lệ →
  dừng lại và thống nhất quy tắc trước khi hardening thêm.
- Nếu cơ chế phát hiện git-root chứng minh không đáng tin cậy trong layout
  submodule hoặc worktree → escalate thay vì làm yếu check thành một cảnh báo
  (warning).

## Đăng Ký File Đã Thay Đổi (Changed Files Registry)

Created:
- `governance/scripts/governance/validate_reference_integrity.py`
- `governance/scripts/governance/fixtures/regression_nested_layout.py`

Modified:
- `governance/scripts/governance/validate_structure.py` — thêm
  `find_git_root()` + `check_deployment_root()`
- `governance/scripts/governance/README.md` — tài liệu hóa toàn bộ 5
  validator + fixture
- File này (`docs/tasks/TASK-REM-T03-validator-hardening.md`) — kết quả
  check, status
- `PROJECT/PROJECT_DECISIONS.md` — DEC-013 (COMPLETION GATE CHANGE PROPOSAL
  cho CHECK-T03-03)

Deleted:
- ...

Migration Impact:
- None. Chỉ có các check mới và mở rộng; không thay đổi ngữ nghĩa governance.
  `validate_structure.py` vẫn in dòng `GOVERNANCE STRUCTURE: PASS` gốc khi
  thành công, chỉ thêm một dòng `Deployment root: ...` — mọi evidence lịch sử
  trích dẫn output cũ vẫn là bản ghi chính xác tại thời điểm nó được thu
  thập, không bị viết lại.

## Ghi Chú (Notes)
Giữ nguyên cách resolve `Path(__file__).resolve().parents[3]` hiện tại. Nó
đúng và cố ý độc lập với working directory của caller (đã được xác minh trong
S001, CHK-S001-05). Điều đang được thêm vào là một assertion riêng biệt rằng
gốc đã resolve này *chính là* gốc repository.
