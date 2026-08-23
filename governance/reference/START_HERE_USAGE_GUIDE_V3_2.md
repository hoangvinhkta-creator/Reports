# START HERE — V3.2 FINAL COMPACT STRUCTURE

## Quan trọng

Bản Compact KHÔNG đổ 60+ file governance ra root.

Sau khi cài, root project chỉ cần thấy thêm:

```text
CLAUDE.md
PROJECT/
docs/
governance/
```

Trong đó:
- `CLAUDE.md` = cửa vào duy nhất cho agent.
- `PROJECT/` = trạng thái hiện tại của project.
- `docs/` = task/session/review runtime.
- `governance/` = toàn bộ luật tĩnh, template, validator và tài liệu tham khảo.

Agent không cần đọc toàn bộ `governance/` mỗi session.
Nó phải đọc `CLAUDE.md` trước và chỉ load những rule phù hợp Profile/Task.

---

## Cấu trúc upload chuẩn của bản Compact

Khi đưa vào repo hiện có, merge bốn entry sau vào root:

```text
CLAUDE.md
PROJECT/
docs/
governance/
```

Không bung các file bên trong `governance/` ngược ra root.

`CLAUDE.md` là file duy nhất ở root dùng để định tuyến việc đọc governance.


# START HERE — HƯỚNG DẪN SỬ DỤNG AI ENGINEERING CONSTITUTION V3.2

## Mục tiêu

Tài liệu này hướng dẫn cách sử dụng bộ V3.2 từ lúc đưa vào GitHub cho đến khi:
- khởi tạo dự án bằng `S000 — PROJECT OPEN`,
- kiểm tra tiến độ,
- chạy audit,
- thực hiện từng task theo session,
- đóng session,
- bàn giao,
- mở session mới mà không mất context.

---

# PHẦN 1 — ĐƯA V3.2 VÀO REPO GITHUB

## Trường hợp A — Repo đã tồn tại trên GitHub

Ví dụ:
`CRM`

Repo root là cấp ngoài cùng nơi bạn đang thấy các file/thư mục như:
- `package.json`
- `index.html`
- `src/`
- `.github/`
- `wrangler.jsonc`
- v.v.

### Cách đúng

Copy toàn bộ nội dung bên trong bộ V3.2 vào root repo:

```text
CRM/
├── CLAUDE.md
├── governance/core/00_SESSION_ORCHESTRATION.md
├── ...
├── PROJECT/
├── governance/templates/
├── docs/
├── governance/scripts/
├── src/
├── package.json
└── ...
```

### Không nên

```text
CRM/
└── AI_ENGINEERING_CONSTITUTION_TEMPLATE_V3_2/
    ├── CLAUDE.md
    ├── PROJECT/
    └── ...
```

Framework phải nằm cùng cấp với code của project để agent coi nó là governance của chính repo.

---

## Nếu bạn chỉ dùng trình duyệt GitHub

GitHub cho phép upload file trực tiếp từ giao diện repository:

1. Mở repo.
2. Chọn `Add file`.
3. Chọn `Upload files`.
4. Kéo thả nội dung V3.2 vào repository.
5. Kiểm tra lại cây thư mục trước khi commit.
6. Commit thay đổi.

Lưu ý:
- Không overwrite file cùng tên nếu chưa đọc nội dung cũ.
- Nếu repo đã có thư mục `docs/`, hãy merge thay vì xóa nội dung cũ.
- Nên commit riêng lần thêm governance.

Commit gợi ý:

```text
chore: add AI engineering governance V3.2
```

---

# PHẦN 2 — KIỂM TRA CẤU TRÚC SAU KHI THÊM

Danh sách đầy đủ các required path (21 file, gồm `governance/core/`,
`PROJECT/`, `docs/*/README.md`, `governance/templates/`) không được liệt kê
tay ở đây — một danh sách tay là một nguồn sự thật thứ hai, dễ lệch khỏi
validator thật khi có path mới được thêm (đây chính là drift đã gây ra
FIND-006). Nguồn sự thật duy nhất là chính script:

```bash
python3 governance/scripts/governance/validate_structure.py
```

Kỳ vọng đầu ra dạng:

```text
GOVERNANCE STRUCTURE: PASS
Deployment root: PASS — <đường dẫn repo>
Checked N required paths.
```

Nếu dùng terminal trong Claude Code, có thể chạy đủ 5 validator:

```bash
python3 governance/scripts/governance/validate_structure.py
python3 governance/scripts/governance/validate_project_state.py
python3 governance/scripts/governance/validate_task_completion.py
python3 governance/scripts/governance/validate_evidence.py
python3 governance/scripts/governance/validate_reference_integrity.py
```

`governance/scripts/governance/validate_project_state.py` có thể FAIL trước S000 vì profile chưa được khởi tạo. Đây là bình thường.

---

# PHẦN 3 — MỞ CLAUDE CODE

Mở Claude Code tại chính repo project.

Không mở riêng folder governance.

Agent phải nhìn thấy cùng lúc:
- code,
- `CLAUDE.md`,
- `PROJECT/`,
- `docs/`,
- `governance/templates/`,
- governance rules.

---

# PHẦN 4 — PROMPT ĐẦU TIÊN: S000 — PROJECT OPEN

Đây là prompt khuyến nghị dùng cho dự án mới hoặc repo cũ chưa được V3.2 quản lý.

## Prompt S000 chuẩn

```text
Đây là S000 — PROJECT OPEN.

Hãy đọc CLAUDE.md và thực hiện đúng governance V3.2.

Yêu cầu:
1. Chưa sửa source code.
2. Phân loại dự án theo governance/core/PROJECT_PROFILE_STANDARD.md.
3. Chọn Project Profile phù hợp và cập nhật PROJECT/PROJECT_PROFILE.md.
4. Xác định Task Mode phù hợp cho các nhóm công việc.
5. Đánh giá dự án hiện tại ở mức cần thiết để tạo roadmap ban đầu.
6. Tạo các Phase.
7. Chia thành Major Task / Micro Task / Spike nếu phù hợp.
8. Chia tiếp Major Task thành các subtask.
9. Xác định dependency giữa các task.
10. Đánh giá Difficulty / Risk / Blast Radius.
11. Đề xuất capability tier/agent cho từng Major Task.
12. Tạo Preliminary Completion Gate cho từng task.
13. Khởi tạo hoặc cập nhật PROJECT/PROJECT_PROGRESS.md.
14. Ghi các quyết định ban đầu cần thiết vào PROJECT/PROJECT_DECISIONS.md.
15. Chưa implement bất kỳ feature nào.

Cuối session hãy trả:
- Project Profile đã chọn
- lý do
- roadmap
- task checklist
- dependency
- risk/difficulty/blast radius
- agent tier
- task nào READY / task nào chưa READY
- bước tiếp theo được khuyến nghị.
```

---

# PHẦN 5 — NẾU LÀ DỰ ÁN CŨ NHƯ CRM

Với hệ thống đang hoạt động, nên bắt đầu AUDIT trước.

## Prompt S000 cho dự án cũ

```text
Đây là S000 — PROJECT OPEN cho một hệ thống cũ đang hoạt động.

Hãy đọc CLAUDE.md và governance V3.2.

Yêu cầu:
- Chưa sửa source code.
- Bắt đầu theo AUDIT profile nếu phù hợp.
- Xác định current architecture, routing, data model, authentication, authorization, business logic, database/API access, sensitive data, environment, deployment và technical debt.
- Khởi tạo PROJECT/PROJECT_PROFILE.md và PROJECT/PROJECT_PROGRESS.md.
- Tạo kế hoạch cho S001 — Discovery & Baseline.
- Không sửa lỗi ngay cả khi phát hiện lỗi.
- Mọi vấn đề chỉ ghi thành Finding với severity và evidence requirement.
- Sau audit mới đề xuất chuyển profile sang PRODUCT nếu phù hợp.

Cuối session hãy show:
1. Profile
2. Scope audit
3. Roadmap audit
4. Task list
5. Risk areas
6. Next session.
```

---

# PHẦN 6 — PROMPT CHO S001: DISCOVERY / AUDIT

```text
Thực hiện session tiếp theo theo PROJECT/PROJECT_PROGRESS.md.

Đây là session Discovery/Audit.

Yêu cầu:
1. Chạy Session Open Protocol.
2. Đọc Project Profile và Progress trước.
3. Không sửa source code.
4. Sử dụng governance/audit/DISCOVERY_BASELINE_TEMPLATE.md.
5. Ghi phát hiện theo governance/audit/AUDIT_FINDINGS_TEMPLATE.md.
6. Mỗi finding phải có:
   - ID
   - Severity
   - Category
   - Affected Area
   - Current Behavior
   - Expected Behavior
   - Evidence
   - Evidence Level
   - Risk
   - Recommended Fix
7. Không biến finding thành fix trong cùng session.
8. Cuối session cập nhật PROJECT_PROGRESS.md và tạo handoff.
```

---

# PHẦN 7 — PROMPT CHUYỂN TỪ AUDIT → PRODUCT

Dùng khi audit đã hoàn tất và bạn muốn bắt đầu sửa/refactor.

```text
Audit đã hoàn tất.

Hãy review PROJECT/PROJECT_PROGRESS.md, Discovery Baseline và Audit Findings.

Nếu đủ điều kiện:
1. Đề xuất chuyển Project Profile từ AUDIT sang PRODUCT.
2. Không code trong bước này.
3. Chuyển các finding được chấp nhận thành remediation roadmap.
4. Nhóm finding thành Major Task hợp lý.
5. Xác định dependency.
6. Xác định Difficulty / Risk / Blast Radius.
7. Đề xuất agent tier.
8. Tạo Preliminary Completion Gate.
9. Cập nhật PROJECT_PROFILE.md và PROJECT_PROGRESS.md sau khi profile transition được xác nhận.
10. Chỉ task có Ready Gate PASS mới được đánh dấu READY.
```

---

# PHẦN 8 — PROMPT MỞ MỘT SESSION LÀM TASK MỚI

Sau S000/S001, prompt mỗi session không cần dài.

## Prompt mặc định

```text
Tiếp tục dự án theo governance hiện tại.

Hãy chạy Session Open Protocol:
1. Đọc CLAUDE.md.
2. Đọc PROJECT/PROJECT_PROFILE.md.
3. Đọc PROJECT/PROJECT_PROGRESS.md.
4. Xác định Current Task.
5. Đọc task definition tương ứng.
6. Kiểm tra dependencies.
7. Kiểm tra Ready Gate.
8. Load Scope Lock.
9. Load frozen Completion Gate và evidence requirements.
10. Chỉ bắt đầu implementation nếu task đang READY.

Trước khi code, hãy cho tôi biết ngắn gọn:
- Session ID
- Profile
- Current Task
- Task Mode
- Status
- Difficulty / Risk / Blast Radius
- Agent tier được đề xuất
- Scope Lock
- Required Completion Gates.
```

---

# PHẦN 9 — PROMPT THỰC HIỆN TASK

Sau khi Agent xác nhận task READY:

```text
Thực hiện Current Task đúng theo task definition và Scope Lock.

Yêu cầu:
- Không sửa ngoài scope.
- Không thay đổi roadmap âm thầm.
- Không hạ Completion Gate.
- Không bịa evidence.
- Nếu cần vượt scope, dừng và báo SCOPE EXPANSION REQUIRED.
- Nếu gặp escalation trigger, dừng vá và thực hiện governance/core/ESCALATION_PROTOCOL.md.
- Sau implementation chuyển task sang VERIFYING và chạy Completion Gate.
```

---

# PHẦN 10 — PROMPT KIỂM TRA TIẾN ĐỘ

Dùng bất kỳ session nào.

## Prompt ngắn

```text
Đến đâu rồi?
Đọc PROJECT/PROJECT_PROGRESS.md và show checklist hiện tại.
```

## Prompt đầy đủ

```text
Hãy đọc PROJECT/PROJECT_PROGRESS.md và báo cáo trạng thái dự án hiện tại.

Cho tôi:
1. Overall status
2. Current Phase
3. Current Task
4. Current Task Mode
5. Task đã DONE
6. Task READY
7. Task BLOCKED
8. Required Completion Gate của Current Task đã PASS bao nhiêu
9. FAIL / BLOCKED / NOT_TESTED còn lại
10. Active risks
11. Open regression items
12. Next recommended task

Show checklist roadmap hiện tại.
Không trả lời dựa trên trí nhớ hội thoại.
```

---

# PHẦN 11 — PROMPT KIỂM TRA MỘT TASK ĐÃ THỰC SỰ HOÀN THÀNH CHƯA

```text
Audit trạng thái Current Task trước khi cho phép đánh dấu DONE.

Hãy kiểm tra:
1. Ready Gate có hợp lệ không.
2. Toàn bộ REQUIRED Completion Gate.
3. Evidence Level của từng check.
4. Có evidence nào chỉ là narrative claim không.
5. Có REQUIRED check nào FAIL / BLOCKED / NOT_TESTED không.
6. Build/test/typecheck/lint nào đã thực sự chạy.
7. Regression checks.
8. Security/data checks nếu liên quan.
9. Documentation update.
10. PROJECT_PROGRESS và session handoff.

Nếu chưa đủ điều kiện, không được đánh dấu DONE.
Hãy liệt kê chính xác những gì còn thiếu.
```

---

# PHẦN 12 — PROMPT AUDIT RIÊNG MỘT MODULE / TÍNH NĂNG

Ví dụ muốn audit `pricing`, `customers`, `auth`.

```text
Thực hiện AUDIT READ-ONLY cho module: [TÊN MODULE].

Không sửa code.

Đối chiếu với các governance rules liên quan.

Yêu cầu:
- xác định architecture
- data access
- security/authorization
- business logic
- API/database access
- error handling
- regression risk
- technical debt

Tạo findings theo governance/audit/AUDIT_FINDINGS_TEMPLATE.md.
Mỗi finding phải có Severity + Evidence + Recommended Fix.

Không chuyển sang remediation trong session này.
```

---

# PHẦN 13 — PROMPT KIỂM TRA SECURITY RIÊNG

```text
Thực hiện security audit READ-ONLY cho phạm vi hiện tại.

Bắt buộc đọc:
- governance/core/04_SECURITY_RULES.md
- governance/core/03_DATA_MODEL_RULES.md
- governance/core/06_DATABASE_API_RULES.md
- governance/product/17_DATA_GOVERNANCE_PRIVACY.md
- governance/core/11_FORBIDDEN_ACTIONS.md
- governance/core/EVIDENCE_STANDARD.md

Kiểm tra:
- authentication
- authorization
- IDOR
- client-trusted data
- sensitive fields
- secrets
- database rules
- direct API/database access
- exports
- audit logging
- personal data exposure

Không sửa code.
Tạo findings Critical/High/Medium/Low/Info kèm evidence.
```

---

# PHẦN 14 — PROMPT KHI AGENT ĐANG VÁ LỖI LIÊN TỤC

```text
Dừng implementation hiện tại.

Hãy kiểm tra governance/core/ESCALATION_PROTOCOL.md.

Tôi không muốn tiếp tục vá chồng vá.

Hãy:
1. Tổng hợp các attempt đã thử.
2. Xác định evidence từ từng attempt.
3. Phân tích root cause.
4. Xác định có architecture conflict / scope expansion / security ambiguity không.
5. Đề xuất escalation tier.
6. Cập nhật blocker vào PROJECT_PROGRESS.md.
7. Chưa tiếp tục code cho đến khi có hướng xử lý mới rõ ràng.
```

---

# PHẦN 15 — PROMPT KẾT THÚC SESSION

Đây là prompt nên dùng gần như cuối mọi Major Task session.

```text
Kết thúc session hiện tại theo Session Close Protocol.

Bắt buộc:
1. Dừng implementation mới.
2. Chạy các verification còn lại của Current Task.
3. Chạy Completion Gate.
4. Không đánh dấu DONE nếu REQUIRED check chưa PASS.
5. Ghi Evidence Level + Evidence cho từng check quan trọng.
6. Cập nhật task status.
7. Cập nhật PROJECT/PROJECT_PROGRESS.md.
8. Cập nhật PROJECT/PROJECT_DECISIONS.md nếu có quyết định mới.
9. Ghi Changed Files Registry.
10. Ghi blockers, risks và regression items.
11. Tạo session handoff trong docs/sessions/.
12. Xác định Next Recommended Session.

Cuối cùng trả cho tôi một SESSION HANDOFF SUMMARY gồm:
- Session ID
- Task
- Status
- Completed
- Remaining
- Gate PASS/FAIL/BLOCKED/NOT_TESTED
- Files changed
- Decisions
- Risks
- Next Session
- Prompt mở session tiếp theo.
```

---

# PHẦN 16 — PROMPT YÊU CẦU AGENT TỰ TẠO PROMPT CHO SESSION TIẾP THEO

```text
Dựa trên session handoff vừa tạo, hãy viết cho tôi một prompt duy nhất để mở session tiếp theo.

Prompt phải:
- yêu cầu chạy Session Open Protocol,
- đọc PROJECT_PROFILE.md,
- đọc PROJECT_PROGRESS.md,
- đọc handoff session trước,
- xác định Current Task,
- kiểm Ready Gate,
- load Scope Lock,
- load Completion Gate,
- không cho phép sửa ngoài scope,
- không cho phép code nếu task chưa READY.

Chỉ trả prompt mở session mới, không bắt đầu task mới trong session hiện tại.
```

---

# PHẦN 17 — PROMPT MỞ SESSION MỚI TỪ HANDOFF

Bạn có thể dùng prompt chung sau nếu không muốn copy prompt do agent tạo:

```text
Đây là session mới.

Hãy tiếp tục dự án từ repository state hiện tại, không dựa vào trí nhớ hội thoại cũ.

Thực hiện Session Open Protocol:
1. Đọc CLAUDE.md.
2. Đọc PROJECT/PROJECT_PROFILE.md.
3. Đọc PROJECT/PROJECT_PROGRESS.md.
4. Đọc session handoff mới nhất trong docs/sessions/.
5. Xác định Current Task và Next Recommended Task.
6. Đọc task definition tương ứng.
7. Kiểm dependencies và Ready Gate.
8. Load Scope Lock.
9. Load frozen Completion Gate và evidence requirements.
10. Báo trạng thái trước khi code.

Nếu task chưa READY hoặc đang BLOCKED, không implement.
```

---

# PHẦN 18 — PROMPT ĐỀ NGHỊ SHOW TOÀN BỘ ROADMAP

```text
Đọc PROJECT/PROJECT_PROGRESS.md.

Show cho tôi toàn bộ roadmap theo dạng checklist, gồm:
- Phase
- Major Task
- Micro Task nếu có
- trạng thái từng task
- Difficulty
- Risk
- Blast Radius
- Agent Tier
- Dependency
- Required Gate progress

Đánh dấu rõ:
DONE / READY / IN_PROGRESS / BLOCKED / NOT_STARTED.
```

---

# PHẦN 19 — PROMPT KIỂM TRA PROFILE CÓ ĐANG ĐƯỢC ÁP DỤNG ĐÚNG KHÔNG

```text
Kiểm tra Project Profile hiện tại có đang được thực thi đúng trong roadmap và task system không.

Đọc:
- PROJECT/PROJECT_PROFILE.md
- PROJECT/PROJECT_PROGRESS.md
- governance/core/PROJECT_PROFILE_STANDARD.md
- task definitions hiện tại.

Cho tôi ma trận:
Governance Domain | Profile Requirement | Applicable | Covered By Task | Current Status | Gap

Nếu có domain bắt buộc nhưng chưa được roadmap cover, tạo PROFILE COMPLIANCE GAP.
Không tự sửa roadmap trong bước kiểm tra này.
```

---

# PHẦN 20 — PROMPT REVIEW ĐỘC LẬP E2 CHO SOLO DEVELOPER

Dùng session riêng sau khi implementation session đã kết thúc.

```text
Đây là independent reviewer session cho E2 verification.

Không tin các PASS claim của implementing agent.

Hãy:
1. Đọc repository state hiện tại.
2. Đọc task definition và frozen Completion Gate.
3. Đọc implementation diff/code thực tế.
4. Đọc handoff chỉ để biết phạm vi, không dùng nó làm bằng chứng.
5. Tự chạy lại các verification cần thiết.
6. Ghi evidence độc lập.
7. Đánh dấu từng check PASS / FAIL / BLOCKED / NOT_TESTED.
8. Nếu phát hiện mismatch giữa handoff và code, báo rõ.
9. Không sửa code trong review session trừ khi tôi yêu cầu riêng.

Kết luận:
E2 PASS / E2 FAIL / E2 INCOMPLETE.
```

---

# PHẦN 21 — PROMPT PHASE GATE

```text
Các task trong phase hiện tại đã hoàn thành.

Hãy chạy PHASE GATE theo governance/core/PHASE_RELEASE_GATE_STANDARD.md.

Kiểm tra:
- task dependencies
- cross-module integration
- routing
- auth/authorization
- data consistency
- build
- integration test
- regression
- open regression items

Không mở phase tiếp theo nếu Phase Gate chưa PASS.
Cập nhật PROJECT_PROGRESS.md.
```

---

# PHẦN 22 — PROMPT RELEASE GATE

```text
Chuẩn bị Release Gate.

Hãy kiểm tra:
- required phases PASS
- migration readiness
- backup/rollback
- production environment
- secrets/config
- security
- observability
- deployment plan
- post-deploy checks
- unresolved Critical/High findings
- open regression items

Không đánh dấu RELEASE_READY nếu còn required gate chưa PASS.
```

---

# PHẦN 23 — PROMPT NGHIỆM THU CUỐI DỰ ÁN

```text
Thực hiện Final Acceptance cho toàn bộ dự án.

Đọc:
- Project Profile
- Project Progress
- Requirements
- Phase Gates
- Release Gate
- Audit Findings
- Open Regression Items
- Session history liên quan.

Kiểm tra:
1. End-to-end user flows.
2. Business acceptance criteria.
3. Security/data requirements.
4. Required documentation.
5. Backup/recovery readiness.
6. Deployment/runbook.
7. Remaining technical debt.
8. Remaining risks.

Chỉ đánh dấu PROJECT COMPLETE nếu toàn bộ mandatory acceptance criteria PASS.

Trả:
- Final status
- Passed criteria
- Remaining gaps
- Accepted risks
- Outstanding technical debt
- Operational handoff status.
```

---

# PHẦN 24 — BỘ PROMPT TỐI GIẢN DÙNG HẰNG NGÀY

Bạn thực tế chỉ cần nhớ 5 prompt sau:

## 1. Khởi tạo

```text
Chạy S000 — PROJECT OPEN theo CLAUDE.md. Chưa sửa source code. Phân loại profile, khởi tạo project state, roadmap, tasks, dependencies, risks, agent tier và preliminary gates.
```

## 2. Bắt đầu session

```text
Tiếp tục dự án. Chạy Session Open Protocol, đọc PROJECT_PROGRESS.md và chỉ bắt đầu Current Task nếu Ready Gate PASS.
```

## 3. Kiểm tra tiến độ

```text
Đến đâu rồi? Đọc PROJECT_PROGRESS.md và show checklist + blockers + next task.
```

## 4. Kết thúc session

```text
Kết thúc session theo Session Close Protocol. Chạy Completion Gate, cập nhật progress, tạo handoff và cho tôi prompt mở session tiếp theo.
```

## 5. Audit

```text
Thực hiện AUDIT READ-ONLY cho phạm vi hiện tại. Không sửa code. Ghi findings theo severity + evidence + remediation.
```

---

# PHẦN 25 — NGUYÊN TẮC QUAN TRỌNG NHẤT

Bạn không cần tự nhớ toàn bộ framework.

Bạn chỉ cần kiểm soát 5 thứ:

1. Agent đang dùng đúng Project Profile chưa?
2. Agent đang làm đúng Current Task chưa?
3. Task có đang trong Scope Lock không?
4. Completion Gate có PASS bằng evidence thật không?
5. PROJECT_PROGRESS.md có được cập nhật sau session không?

Nếu 5 điều này được giữ đúng, các session có thể nối tiếp nhau mà ít phụ thuộc vào trí nhớ hội thoại.

---

# PHẦN 26 — WORKFLOW TÓM TẮT

```text
UPLOAD V3.2 TO REPO ROOT
        ↓
VALIDATE STRUCTURE
        ↓
S000 PROJECT OPEN
        ↓
SELECT PROFILE
        ↓
INITIAL ROADMAP
        ↓
AUDIT/DISCOVERY (nếu cần)
        ↓
ROADMAP FINALIZATION
        ↓
TASK READY GATE
        ↓
SESSION OPEN
        ↓
IMPLEMENT
        ↓
VERIFY
        ↓
COMPLETION GATE
        ↓
SESSION CLOSE + HANDOFF
        ↓
NEXT SESSION
        ↓
PHASE GATE
        ↓
RELEASE GATE
        ↓
FINAL ACCEPTANCE
```
