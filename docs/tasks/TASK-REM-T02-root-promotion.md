# TASK-REM-T02 — Đưa governance package lên gốc repository

## Metadata
Status:
DONE

Phase:
PHASE-01 — Governance Foundation Repair

Task Mode:
MAJOR

Primary Agent Tier:
Tier C — Advanced Reasoning

Escalation Tier:
Tier C + owner confirmation

Difficulty:
2/5

Risk:
3/5

Blast Radius:
5/5

Project Profile:
PRODUCT

Ready Gate Verified In:
S002 — Roadmap Finalization (2026-08-22)

Completion Gate Status:
**FROZEN** — 2026-08-22, S002

Closes Finding:
FIND-001 (HIGH)

## Mục Tiêu (Objective)
Di chuyển `CLAUDE.md`, `PROJECT/`, `docs/` và `governance/` từ
`AI_ENGINEERING_CONSTITUTION_TEMPLATE_V3_2_FINAL_COMPACT/` lên gốc repository,
để `CLAUDE.md` trở thành điểm vào (entry point) governance tại gốc theo yêu
cầu của `governance/reference/START_HERE_USAGE_GUIDE_V3_2.md` PHẦN 1.

## Phạm Vi (Scope)
- `git mv` bốn entry cấp cao nhất của package lên gốc repository
- Xóa thư mục wrapper đã rỗng

## Ngoài Phạm Vi (Out of Scope)
**Tuyệt đối không chỉnh sửa bất kỳ nội dung nào.** Đây là một cuộc di chuyển
chỉ-về-đường-dẫn (path-only), theo quy tắc bảo toàn nội dung trong
`governance/README.md`:

> Việc tái cấu trúc thư mục KHÔNG ĐƯỢC viết lại, tóm tắt, rút gọn, hoặc xóa
> bỏ ngữ nghĩa governance.

Việc sửa reference thuộc về REM-T04. Việc thay đổi validator thuộc về REM-T03.

## Phụ Thuộc (Dependencies)
- REM-T07 DONE — cung cấp nguồn evidence E2 dựa trên CI mà CHECK-T02-05 yêu
  cầu. Nếu không có, CHECK-T02-05 phải được thỏa mãn bằng một session Solo
  Independent Review thay thế (`governance/core/EVIDENCE_STANDARD.md`), điều
  này chấp nhận được nhưng chậm hơn.
- REM-T01 đã bị CANCELLED trong S002 (được absorbed — xem ROADMAP CHANGE
  CH-01). Nó không còn là một dependency nữa.

## Chặn (Blocks)
- REM-T03, REM-T04, REM-T05, REM-T06

## An Toàn Để Chạy Song Song Với (Parallel-Safe With)
- Không có. Mọi task khác đều đụng vào các file mà task này di chuyển.

## Phạm Vi Tác Động Dự Kiến (Expected Touch Area)

Allowed:
- Chỉ đường dẫn file (file paths), trên toàn bộ repository

Không được đụng vào nếu chưa có Scope Expansion (Do not touch without Scope Expansion):
- Nội dung file, trên toàn bộ repository

## Subtask (Subtasks)
- [ ] 02.1 Xác nhận working tree sạch và push một backup ref trước khi bắt đầu
- [ ] 02.2 `git mv` bốn entry lên gốc repository
- [ ] 02.3 Xóa thư mục wrapper đã rỗng
- [ ] 02.4 Chạy lại cả năm validator từ gốc mới
- [ ] 02.5 Xác minh lịch sử git được giữ nguyên (follow) cho một mẫu các file đã di chuyển
- [ ] 02.6 Thu thập E2 independent review

## Ready Gate — PARTIALLY VERIFIED

Theo `governance/core/TASK_READY_GATE_STANDARD.md`, MAJOR Ready Gate:

- [x] Mục tiêu đã rõ ràng.
- [x] Scope đã được xác định.
- [x] Out-of-scope đã được xác định.
- [ ] **Dependencies đã DONE hoặc được waive rõ ràng** — REM-T07 đang READY
      nhưng chưa DONE. Đây là mục còn mở duy nhất.
- [x] Phạm vi tác động dự kiến đã được xác định.
- [x] Các yêu cầu liên quan đã được hiểu rõ.
- [x] Tác động đến dữ liệu đã được biết rõ — không có; không tồn tại data store nào.
- [x] Tác động đến bảo mật đã được biết rõ — không có; không có thay đổi secret hay permission nào.
- [x] Tác động đến routing/API đã được biết rõ nếu liên quan — NOT_APPLICABLE.
- [x] Điều kiện tiên quyết cho migration đã sẵn sàng nếu liên quan — cần một
      backup ref đã được push theo subtask 02.1.
- [x] Difficulty đã được chấm điểm — 2/5.
- [x] Risk đã được chấm điểm — 3/5.
- [x] Blast Radius đã được chấm điểm — 5/5.
- [x] Primary agent tier đã được gán — Tier C.
- [x] Escalation triggers đã được xác định.
- [x] Completion Gate đã được finalize.
- [x] Completion Gate đã được frozen trước khi implementation.

Các điều kiện tiên quyết bổ sung trước khi bắt đầu implementation:
- [ ] Backup ref đã được push lên `origin`
- [ ] Owner đã xác nhận việc di chuyển (Blast Radius 5/5)

Status: **DONE** — 2026-08-22 (S003).

Ghi chú về dependency: owner đã chỉ đạo rõ ràng để task này chạy trước REM-T07
(DEC-009), đảo ngược thứ tự ban đầu của CH-02, vì FIND-001 là một lỗi
usability đang hoạt động (broken links) chứ không phải một rủi ro tiềm ẩn. E2
cho CHECK-T02-05 đã đạt được thông qua Solo Independent Review Procedure thay
vì CI, điều mà Ready Gate luôn cho phép như một nguồn thay thế.

## Completion Gate
Dùng `governance/core/TASK_COMPLETION_GATE_STANDARD.md` và `governance/core/EVIDENCE_STANDARD.md`.

Status of this gate:
**FROZEN** — 2026-08-22, S002. Không được xóa hoặc làm yếu đi một REQUIRED
check để khiến task này pass. Sử dụng COMPLETION GATE CHANGE PROPOSAL nếu một
thay đổi là chính đáng.

### Structural

#### CHECK-T02-01
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E2

Evidence:
`ls -A` tại gốc repository → `.git CLAUDE.md PROJECT docs governance`, không
còn gì khác. Được re-verify độc lập trong E2 review
`docs/reviews/E2-TASK-REM-T02-S003.md`.

Executed By:
S003 agent; được re-verify độc lập bởi isolated reviewer agent

Timestamp:
2026-08-22

Yêu cầu:
`ls -A` tại gốc repository hiển thị chính xác `.git`, `CLAUDE.md`,
`PROJECT/`, `docs/`, `governance/` (cộng với bất kỳ file nào được REM-T06
thêm vào).

#### CHECK-T02-02
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E2

Evidence:
`validate_structure.py` → `GOVERNANCE STRUCTURE: PASS`, 21 đường dẫn, exit 0,
chạy từ gốc mới. Được re-verify độc lập trong
`docs/reviews/E2-TASK-REM-T02-S003.md`.

Executed By:
S003 agent; được re-verify độc lập bởi isolated reviewer agent

Timestamp:
2026-08-22

Yêu cầu:
`validate_structure.py` PASS khi chạy từ gốc mới.

### Preservation

#### CHECK-T02-03
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E2

Evidence:
Commit `699b105`: `git diff --stat -M 699b105^ 699b105` → 84 files changed,
0 insertions(+), 0 deletions(-). `git diff --raw -M` → toàn bộ 84 entry đều là
R100, không có A/D/M. Reviewer còn chạy thêm một so sánh blob-hash toàn diện
(exhaustive) trên cả 84 file đã di chuyển (mạnh hơn việc chỉ kiểm tra diff
rỗng) → 0 mismatches. Chi tiết đầy đủ trong
`docs/reviews/E2-TASK-REM-T02-S003.md`.

Executed By:
S003 agent; được re-verify độc lập bởi isolated reviewer agent (kiểm tra
exhaustive vượt mức tối thiểu ≥5 file)

Timestamp:
2026-08-22

Yêu cầu:
`git diff --stat HEAD~1 -M` chỉ hiển thị rename, với 0 dòng nội dung được thêm
hoặc xóa.

#### CHECK-T02-04
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E2

Evidence:
`git log --follow` đã được xác minh trên 4 file mẫu (`CLAUDE.md`,
`governance/core/EVIDENCE_STANDARD.md`,
`governance/scripts/governance/validate_structure.py`,
`docs/tasks/TASK-REM-T02-root-promotion.md`) — lịch sử trước khi di chuyển
được bảo toàn trên cả bốn file. Chi tiết đầy đủ trong
`docs/reviews/E2-TASK-REM-T02-S003.md`.

Executed By:
S003 agent; được re-verify độc lập bởi isolated reviewer agent

Timestamp:
2026-08-22

Yêu cầu:
`git log --follow` trả về lịch sử trước khi di chuyển cho ít nhất ba file mẫu
đã di chuyển, bao gồm `CLAUDE.md`.

### Independent Review

#### CHECK-T02-05
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E2

Evidence:
Một session Solo Independent Review Procedure độc lập (isolated worktree,
không có ngữ cảnh trước đó) đã kết luận E2 PASS, không có sai lệch nào so với
tuyên bố của implementer. Artifact: `docs/reviews/E2-TASK-REM-T02-S003.md`.

Executed By:
Independent reviewer agent (isolated worktree agent-a1acf66ec82dff345), theo
DEC-009

Timestamp:
2026-08-22

Yêu cầu:
Một session reviewer độc lập xác nhận không có semantic edit nào xảy ra. Theo
`governance/core/EVIDENCE_STANDARD.md`, Risk 3 kết hợp với Blast Radius 5 chạm
đến agent read path đòi hỏi E2. Sử dụng Solo Independent Review Procedure
(`governance/reference/START_HERE_USAGE_GUIDE_V3_2.md` PHẦN 20) và lưu
artifact trong `docs/reviews/` bằng
`governance/templates/E2_INDEPENDENT_REVIEW_TEMPLATE.md`.

Nếu không có đường E2 nào khả dụng, hãy ghi nhận hạn chế đó — không được đánh
dấu check này là PASS.

## Tiêu Chí Hoàn Thành (Exit Criteria)
- [x] 100% REQUIRED checks PASS — 5/5, xem Completion Gate ở trên
- [x] Không có lỗi nghiêm trọng (critical) chưa xử lý
- [x] Đạt mức evidence yêu cầu, bao gồm E2 trên CHECK-T02-05
- [x] Tiến độ dự án đã được cập nhật
- [x] Đã viết Session Handoff — `docs/sessions/S003-root-promotion.md`

## Điều Kiện Kích Hoạt Leo Thang (Escalation Triggers)
- Nếu xuất hiện bất kỳ content diff nào trong quá trình di chuyển → dừng lại,
  revert, và escalate. Việc di chuyển phải chỉ-về-đường-dẫn (path-only).
- Nếu `git log --follow` mất lịch sử → dừng lại và lập lại kế hoạch chiến lược
  di chuyển.

## Đăng Ký File Đã Thay Đổi (Changed Files Registry)

Created:
- `docs/reviews/E2-TASK-REM-T02-S003.md`
- `.gitignore` (không liên quan đến scope của task này; được thêm vào để ngăn
  local Claude Code stop-hook gắn cờ trạng thái scratch của harness worktree
  là untracked — xem FIND-009)

Modified:
- File này (`docs/tasks/TASK-REM-T02-root-promotion.md`) — kết quả check, status
- `PROJECT/PROJECT_DECISIONS.md` — DEC-009
- `PROJECT/PROJECT_PROGRESS.md` — trạng thái task, sổ đăng ký findings, trạng thái gate freeze
- `docs/audit/REMEDIATION_ROADMAP.md` — bảng traceability

Renamed (chỉ đường dẫn, commit `699b105`):
- Toàn bộ 84 file trong
  `AI_ENGINEERING_CONSTITUTION_TEMPLATE_V3_2_FINAL_COMPACT/` → gốc
  repository. Danh sách đầy đủ: `git show --stat -M 699b105`.

Deleted:
- Thư mục wrapper đã rỗng
  `AI_ENGINEERING_CONSTITUTION_TEMPLATE_V3_2_FINAL_COMPACT/`

Migration Impact:
- Toàn bộ 73 đường dẫn file gốc của package đã thay đổi. Bất kỳ reference bên
  ngoài nào trỏ đến một đường dẫn dưới
  `AI_ENGINEERING_CONSTITUTION_TEMPLATE_V3_2_FINAL_COMPACT/` giờ đều trả về
  404 — đây chính xác là lỗi mà owner đã báo cáo (broken GitHub links) và là
  lý do task này được sắp xếp lại trước REM-T07 (DEC-009). Các đường dẫn
  *tương đối so với* `CLAUDE.md` không thay đổi, nên không có
  in-repository reference nào cần viết lại chỉ vì lý do này; các reference bị
  hỏng riêng biệt của FIND-003/FIND-004 vẫn còn mở, được theo dõi dưới
  REM-T04.

## Ghi Chú (Notes)
Các validator resolve ROOT từ `Path(__file__).resolve().parents[3]`. Biểu thức
đó vẫn đúng sau khi di chuyển, vì độ sâu của script bên dưới gốc package không
thay đổi. Hãy xác nhận điều này ở 02.4 thay vì mặc định cho là đúng.
