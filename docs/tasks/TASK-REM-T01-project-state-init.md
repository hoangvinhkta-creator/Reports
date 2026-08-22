# TASK-REM-T01 — Khởi tạo trạng thái project (hoàn tất S000)

## Metadata
Status:
CANCELLED

Cancelled In:
S002 — Roadmap Finalization (2026-08-22)

Cancellation Reason:
ABSORBED. Quy trình S000 mà task này tồn tại để hoàn tất đã được thực thi đầy
đủ xuyên suốt S001 và S002. Xem phần "Cancellation Record" ở cuối file này,
ROADMAP CHANGE CH-01 trong `PROJECT/PROJECT_DECISIONS.md` (DEC-008), và bản
handoff của S002.

Original Status:
PLANNED

Phase:
PHASE-01 — Governance Foundation Repair

Task Mode:
MAJOR

Primary Agent Tier:
standard

Escalation Tier:
senior

Difficulty:
2/5

Risk:
2/5

Blast Radius:
2/5

Project Profile:
AUDIT (chuyển đổi trong quá trình thực hiện task này)

Closes Finding:
FIND-002 (HIGH)

## Mục Tiêu (Objective)
Hoàn tất quy trình S000 — PROJECT OPEN chưa từng được thực thi đối với
repository này, để Session Open Protocol hoạt động đúng cho mọi session sau
này và để một profile thực sự chi phối công việc remediation.

S001 chỉ thực hiện một bootstrap tối thiểu (DEC-001). Task này hoàn tất phần
việc còn lại.

## Phạm Vi (Scope)
- `PROJECT/PROJECT_PROFILE.md`
- `PROJECT/PROJECT_PROGRESS.md`
- `PROJECT/PROJECT_DECISIONS.md`

## Ngoài Phạm Vi (Out of Scope)
- Bất kỳ file nào nằm trong `governance/`
- Bất kỳ hoạt động remediation nào cho finding khác
- Bất kỳ application code nào

## Phụ Thuộc (Dependencies)
- S002 — Roadmap Finalization phải đánh dấu task này là READY.

## Chặn (Blocks)
- REM-T02, REM-T03, REM-T04, REM-T05, REM-T06, REM-T07 (tất cả đều bị gate bởi
  yêu cầu phải có một profile thực sự và một progress file thực sự).
- REM-T07 cụ thể phụ thuộc vào quyết định profile của subtask 01.1.

## An Toàn Để Chạy Song Song Với (Parallel-Safe With)
- Không có. Đây là task đầu tiên.

## Phạm Vi Tác Động Dự Kiến (Expected Touch Area)

Allowed:
- `PROJECT/*.md`

Không được đụng vào nếu chưa có Scope Expansion (Do not touch without Scope Expansion):
- `governance/**`
- `docs/audit/**` (các artifact của S001 là bản ghi audit; không được viết lại chúng)

## Subtask (Subtasks)
- [ ] 01.1 Xác nhận hoặc điều chỉnh profile hậu-audit (AUDIT → PRODUCT hoặc SOLO_LITE), kèm giải trình bằng văn bản
- [ ] 01.2 Ghi nhận các nhóm rule mandatory / conditional / not-applicable cho profile đã chọn
- [ ] 01.3 Hoàn tất việc phân rã phase và task trong `PROJECT/PROJECT_PROGRESS.md`
- [ ] 01.4 Ghi nhận các Completion Gate sơ bộ (preliminary) cho các task của Phase-01
- [ ] 01.5 Chạy lại `validate_project_state.py`
- [ ] 01.6 Ghi nhận quyết định chuyển đổi profile dưới dạng DEC-005

## Ready Gate
Dùng `governance/core/TASK_READY_GATE_STANDARD.md`.

- [ ] S002 đã chạy và Completion Gate của task này đã được frozen
- [ ] Câu hỏi về chuyển đổi profile đã được đặt ra cho owner
- [ ] Scope Lock đã được load

## Completion Gate
Dùng `governance/core/TASK_COMPLETION_GATE_STANDARD.md` và `governance/core/EVIDENCE_STANDARD.md`.

Status of this gate:
PRELIMINARY — NOT FROZEN. Sẽ được freeze trong S002.

### Governance

#### CHECK-T01-01
Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E1

Evidence:
...

Executed By:
...

Timestamp:
...

Yêu cầu:
`python3 governance/scripts/governance/validate_project_state.py` thoát với exit code 0.

#### CHECK-T01-02
Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E1

Evidence:
...

Executed By:
...

Timestamp:
...

Yêu cầu:
Không còn giá trị placeholder `...` nào trong `PROJECT/PROJECT_PROFILE.md`.

#### CHECK-T01-03
Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E1

Evidence:
...

Executed By:
...

Timestamp:
...

Yêu cầu:
`PROJECT/PROJECT_PROGRESS.md` nêu tên một Current Task và một Next Recommended
Task, và roadmap của nó không còn mục nào là placeholder.

#### CHECK-T01-04
Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E0

Evidence:
...

Executed By:
...

Timestamp:
...

Yêu cầu:
Quyết định chuyển đổi profile được ghi nhận trong `PROJECT/PROJECT_DECISIONS.md`
kèm giải trình. E0 được chấp nhận ở đây vì đây là một quyết định của con người
đã được ghi lại, không phải một executable check.

## Tiêu Chí Hoàn Thành (Exit Criteria)
- [ ] 100% REQUIRED checks PASS
- [ ] Không có lỗi nghiêm trọng (critical) chưa xử lý
- [ ] Đạt mức evidence yêu cầu
- [ ] Tài liệu bắt buộc đã được cập nhật
- [ ] Tiến độ dự án đã được cập nhật
- [ ] Đã viết Session Handoff

## Điều Kiện Kích Hoạt Leo Thang (Escalation Triggers)
- Owner từ chối chọn một profile hậu-audit → task BLOCKED, không được đoán mò.
- Việc phân rã phát hiện ra phạm vi application không nằm trong baseline của
  S001 → cần ROADMAP CHANGE PROPOSAL trước khi tiếp tục.

## Đăng Ký File Đã Thay Đổi (Changed Files Registry)

Created:
- ...

Modified:
- ...

Deleted:
- ...

Migration Impact:
- None.

## Ghi Chú (Notes)
FIND-002 vẫn ở trạng thái OPEN cho đến khi task này DONE. Bootstrap của S001
(DEC-001) đã giảm nhẹ đủ để chạy discovery; nó không đóng finding này.


---

# Bản Ghi Hủy (Cancellation Record) — S002

## Vì Sao Task Này Không Còn Việc Cần Làm (Why This Task No Longer Has Work)

REM-T01 được tạo trong S001 để hoàn tất quy trình S000 — PROJECT OPEN mà
FIND-002 cho thấy chưa từng được chạy. Giữa bootstrap của S001 (DEC-001) và
việc chuyển đổi profile cùng hoàn thiện roadmap của S002, mọi bước của quy
trình S000 chuẩn trong `governance/core/00_SESSION_ORCHESTRATION.md` đã được
thực thi:

| Bước S000 | Thực Thi Tại | Artifact |
|---|---|---|
| 0. Chọn project profile | S001 (AUDIT), S002 (→ PRODUCT) | `PROJECT/PROJECT_PROFILE.md`, DEC-001, DEC-005 |
| 1. Viết/cập nhật PROJECT_PROFILE.md | S001, S002 | `PROJECT/PROJECT_PROFILE.md` |
| 2. Hiểu mục tiêu và loại project | S001 | Baseline §Executive Summary |
| 3. Xác định quy mô và độ sâu governance | S002 | Profile Compliance Matrix |
| 4. Khảo sát bối cảnh repository | S001 | Baseline §1–§9, CHK-S001-01…09 |
| 5. Quyết định có bắt đầu ở chế độ AUDIT hay không | S001 | DEC-001 (có), DEC-005 (thoát) |
| 6. Tạo các phase chính | S001 | PHASE-01/02/03 |
| 7. Tạo các task Major/Micro/Spike | S001, S002 | REM-T02…T07 |
| 8. Tạo các subtask sơ bộ | S001 | Theo từng task file |
| 9. Tạo sơ đồ phụ thuộc sơ bộ | S001, sửa lại tại S002 | `docs/audit/REMEDIATION_ROADMAP.md` |
| 10. Ước tính Difficulty / Risk / Blast Radius | S001 | Theo từng task file |
| 11. Đề xuất capability tier | S002 | Ánh xạ Tier A–D, DEC-006 |
| 12. Tạo các Completion Gate sơ bộ | S001 | Theo từng task file |
| 13. Khởi tạo/cập nhật PROJECT_PROGRESS.md | S001, S002 | `PROJECT/PROJECT_PROGRESS.md` |
| 14. Ghi nhận các quyết định chiến thuật ban đầu | S001, S002 | DEC-001…DEC-008 |

Không còn bước nào tồn đọng. Việc giữ REM-T01 ở trạng thái mở sẽ tạo ra một
task mà toàn bộ Completion Gate của nó đã có thể thỏa mãn ngay tại thời điểm
tạo ra, đó là việc làm hình thức chứ không phải governance thực sự.

## Xử Lý FIND-002 (FIND-002 Disposition)

FIND-002 là RESOLVED, không phải waived. Verification Required đã nêu của nó
đã được đáp ứng:

| Yêu Cầu | Kết Quả | Evidence Level | Timestamp |
|---|---|---|---|
| `validate_project_state.py` → PASS | `PROJECT STATE: PASS`, exit 0 | E1 | 2026-08-22T14:2xZ (S002) |
| `PROJECT/PROJECT_PROGRESS.md` có roadmap không phải placeholder và có Current Task | Xác nhận qua kiểm tra thực tế | E1 | 2026-08-22 (S002) |

E2 chưa đạt được — chưa có reviewer độc lập nào chạy đối chiếu việc này. Được
ghi nhận là một hạn chế theo `governance/core/EVIDENCE_STANDARD.md`, không
được khẳng định là đã thỏa mãn.

## Những Gì KHÔNG Được Đóng Bởi Việc Hủy Này (What Is NOT Closed By This Cancellation)

- Các domain governance ở trạng thái DORMANT trong Profile Compliance Matrix.
  Chúng là bắt buộc dưới PRODUCT và đơn giản là chưa có đối tượng để áp dụng.
- GAP-01 (Backup / DR), vẫn còn mở đối với một domain bắt buộc.

## Đảo Ngược (Reversal)

File này được giữ lại thay vì xóa. Nếu owner không đồng ý, khôi phục
`Status: PLANNED`, đặt lại FIND-002 về OPEN trong `PROJECT/PROJECT_PROGRESS.md`
và trong bảng truy vết (traceability table) của roadmap, và chèn lại REM-T01
vào đầu PHASE-01.
