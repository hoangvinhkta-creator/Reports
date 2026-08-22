# CLAUDE.md — Điểm Vào Governance Của Dự Án

## Bố Cục Thư Mục Compact

Gói này lưu governance tĩnh dưới `governance/` để giữ root repo gọn nhẹ.

- `CLAUDE.md` = điểm vào governance ở root.
- `PROJECT/` = trạng thái hiện tại của dự án.
- `docs/` = task, session, review, ADR vận hành.
- `governance/` = luật tĩnh, template, validator, tài liệu tham khảo.

Không đưa các file governance quay lại root dưới dạng phẳng (không dùng lại cấu trúc pre-compact).
Thứ tự đọc bắt buộc và toàn bộ cơ chế governance gốc không đổi; chỉ đường dẫn canonical là khác.

## Ngôn Ngữ Nội Dung

Toàn bộ văn xuôi (prose) trong các file đẩy lên repo — hướng dẫn, giải thích, mô tả, lý do, ghi chú — phải viết bằng **tiếng Việt**.

Ngoại lệ — PHẢI giữ nguyên tiếng Anh, không dịch:
- Tên file và đường dẫn thư mục.
- Toàn bộ mã nguồn `.py` trong `governance/scripts/governance/`, kể cả comment, docstring, và chuỗi in ra (output). Nhiều task/audit trích dẫn nguyên văn output các script này làm bằng chứng E1/E2 — dịch sẽ khiến bằng chứng cũ không còn khớp với hành vi thực tế của hệ thống.
- Các nhãn trường mà validator đọc bằng regex: `Status:`, `Priority:`, `Evidence Level:`, `Evidence:`, `Executed By:`, `Timestamp:`, `Risk:`, `Selected Profile:`, `Profile:`, `Current Task Mode:`.
- Các giá trị enum mà validator so khớp chính xác: tên Profile (`SOLO_LITE`, `PRODUCT`, `TEAM_PRODUCTION`, `AUDIT`), Task Mode (`MICRO`, `MAJOR`, `SPIKE`), trạng thái check (`PASS`, `FAIL`, `BLOCKED`, `NOT_TESTED`, `NOT_APPLICABLE`), trạng thái task (`PLANNED`, `READY`, `IN_PROGRESS`, `IMPLEMENTED`, `VERIFYING`, `DONE`, `BLOCKED`, `DEFERRED`, `CANCELLED`), Evidence Level (`E0`, `E1`, `E2`), Priority (`REQUIRED`, `RECOMMENDED`, `OPTIONAL`).
- ID và định danh: `TASK-XX`, `REM-TXX`, `FIND-XXX`, `DEC-XXX`, `ADR-XXX`, `CHECK-XXX`, mã commit git.
- Đoạn Evidence trích dẫn nguyên văn output lệnh đã thực thi — đây là bản ghi lịch sử, không phải văn xuôi để dịch.

Nếu việc tuân thủ quy tắc này làm hỏng khả năng parse của validator (`governance/scripts/governance/*.py`), giữ hệ thống chạy được được ưu tiên hơn việc dịch triệt để.

## Nguyên Tắc Cốt Lõi
Không code trước rồi tổ chức sau.

Repo là bộ nhớ chung:
- Luật → file governance
- Trạng thái hiện tại → `PROJECT/PROJECT_PROGRESS.md`
- Profile dự án → `PROJECT/PROJECT_PROFILE.md`
- Quyết định chiến thuật → `PROJECT/PROJECT_DECISIONS.md`
- Quyết định kiến trúc → `docs/adr/`
- Định nghĩa task → `docs/tasks/`
- Lịch sử/bàn giao session → `docs/sessions/`
- Biểu mẫu tái sử dụng → `governance/templates/`

## S000 — Hành Động Đầu Tiên

S000 có DUY NHẤT một quy trình canonical.

1. Đọc `governance/core/PROJECT_PROFILE_STANDARD.md`.
2. Đọc `governance/core/RULE_PRECEDENCE.md`.
3. Đọc `governance/core/TASK_MODE_STANDARD.md`.
4. Sau đó thực hiện đầy đủ quy trình S000 theo thứ tự trong `governance/core/00_SESSION_ORCHESTRATION.md`.

Không duy trì một checklist S000 thứ hai trong file này.

## Project Profiles

Dùng `governance/core/PROJECT_PROFILE_STANDARD.md`.

Các profile:
- SOLO_LITE
- PRODUCT
- TEAM_PRODUCTION
- AUDIT

Việc chọn profile quyết định độ sâu governance; không quyết định stack kỹ thuật cụ thể.

## Xung Đột Luật

Dùng `governance/core/RULE_PRECEDENCE.md`.

Không âm thầm tự giải quyết xung đột luật có tính chất trọng yếu.

## Mỗi Session Triển Khai

1. Đọc `PROJECT/PROJECT_PROGRESS.md`.
2. Đọc `PROJECT/PROJECT_PROFILE.md`.
3. Xác định task hiện tại và Task Mode.
4. Với task MAJOR, đọc file task dưới `docs/tasks/`.
5. Kiểm tra Ready Gate phù hợp.
6. Nạp Scope Lock.
7. Nạp Completion Gate đã finalize/frozen.
8. Đọc các file governance liên quan.
9. Chỉ bắt đầu triển khai khi đã READY.

## Task Modes

Dùng `governance/core/TASK_MODE_STANDARD.md`.

- MICRO — việc rủi ro thấp, phạm vi hẹp, dùng checklist gọn.
- MAJOR — đầy đủ file task + session riêng + gate + bàn giao.
- SPIKE / EXPLORATORY — giảm bất định trước khi triển khai.

## Vòng Đời Task

NOT_PLANNED
→ PLANNED
→ READY
→ IN_PROGRESS
→ IMPLEMENTED
→ VERIFYING
→ DONE

Trạng thái thay thế:
BLOCKED / DEFERRED / CANCELLED

## Bằng Chứng (Evidence)

Dùng `governance/core/EVIDENCE_STANDARD.md`.

Không bao giờ bịa bằng chứng.

Với các check thực thi được:
- Risk 3 → bắt buộc E1 cho check REQUIRED.
- Risk 4–5 → bắt buộc E1; check liên quan security/data nên hướng tới E2.

Nếu chưa thực thi:
Status = NOT_TESTED.

## Hoàn Thành (Completion)

Dùng `governance/core/TASK_COMPLETION_GATE_STANDARD.md`.

CODE COMPLETE ≠ TASK COMPLETE.

Một task chỉ DONE khi:
- toàn bộ check REQUIRED PASS,
- evidence level bắt buộc được thỏa mãn,
- Exit Criteria được thỏa mãn.

## Tích Hợp (Integration)

Dùng `governance/core/PHASE_RELEASE_GATE_STANDARD.md`.

Task DONE ≠ Phase DONE.
Phase DONE ≠ Release Ready.

## Escalation

Dùng `governance/core/ESCALATION_PROTOCOL.md`.

Không liên tục vá một triển khai đang thất bại.

## Câu Hỏi Về Tiến Độ

Nếu người dùng hỏi:
- tiến độ hiện tại,
- bước hiện tại,
- công việc còn lại,
- bước tiếp theo,
- checklist,

ĐỌC `PROJECT/PROJECT_PROGRESS.md` TRƯỚC TIÊN.

Không trả lời dựa trên trí nhớ hội thoại.

## Mở Rộng Phạm Vi (Scope Expansion)

Không âm thầm sửa ngoài Scope Lock của task.

Nếu cần thiết:

SCOPE EXPANSION REQUIRED

Sau đó đánh giá lại tác động trước khi tiếp tục.

## Quy Tắc Xung Đột

Nếu documentation, implementation, data, security, hoặc hành vi hiện tại xung đột với nhau:

CONFLICT DETECTED

Documentation:
...

Implementation:
...

Risk:
...

Recommended resolution:
...

Không âm thầm đoán mò.

## Các File Governance Liên Quan

### Session / Planning
- `governance/core/00_SESSION_ORCHESTRATION.md`
- `governance/core/PROJECT_PROFILE_STANDARD.md`
- `governance/core/TASK_MODE_STANDARD.md`
- `governance/core/TASK_READY_GATE_STANDARD.md`
- `governance/core/TASK_COMPLETION_GATE_STANDARD.md`
- `governance/core/PHASE_RELEASE_GATE_STANDARD.md`
- `governance/core/AGENT_CAPABILITY_MATRIX.md`
- `governance/core/ESCALATION_PROTOCOL.md`
- `governance/core/RULE_PRECEDENCE.md`
- `governance/core/EVIDENCE_STANDARD.md`

### Kỹ Thuật (Engineering)
- `governance/core/01_PROJECT_ARCHITECTURE_RULES.md`
- `governance/core/02_ROUTING_RULES.md`
- `governance/core/03_DATA_MODEL_RULES.md`
- `governance/core/04_SECURITY_RULES.md`
- `governance/core/05_BUSINESS_LOGIC_RULES.md`
- `governance/core/06_DATABASE_API_RULES.md`
- `governance/core/07_CODING_RULES.md`
- `governance/core/08_CHANGE_MANAGEMENT_RULES.md`
- `governance/core/09_TESTING_RULES.md`
- `governance/core/10_AI_AGENT_EXECUTION_PROTOCOL.md`
- `governance/core/11_FORBIDDEN_ACTIONS.md`

### Sản Phẩm / Vận Hành (Product / Operations)
- `governance/product/12_PRODUCT_REQUIREMENTS_RULES.md`
- `governance/product/13_ENVIRONMENT_CONFIGURATION.md`
- `governance/product/14_CI_CD_RELEASE_RULES.md`
- `governance/product/15_LOGGING_AUDIT_OBSERVABILITY.md`
- `governance/product/16_BACKUP_DISASTER_RECOVERY.md`
- `governance/product/17_DATA_GOVERNANCE_PRIVACY.md`
- `governance/product/18_INCIDENT_RESPONSE.md`
- `governance/product/19_DEPENDENCY_MANAGEMENT.md`
- `governance/product/20_API_VERSIONING_COMPATIBILITY.md`
- `governance/product/21_ACCESSIBILITY_UI_RULES.md`
- `governance/product/22_CODE_OWNERSHIP_REVIEW.md`
- `governance/product/23_DOCUMENTATION_STANDARDS.md`

### Audit / Enforcement
- `governance/audit/DISCOVERY_BASELINE_TEMPLATE.md`
- `governance/audit/AUDIT_FINDINGS_TEMPLATE.md`
- `governance/reference/OPTIONAL_ENFORCEMENT_LAYER.md`

## Luật Cuối Cùng

Agent phải chứng minh việc hoàn thành bằng artifact và bằng chứng, không phải bằng sự tự tin trong lời kể.
