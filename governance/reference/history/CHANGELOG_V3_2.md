# CHANGELOG — V3.2

## Kết nối Runtime (Runtime Wiring)
- Thêm Task Mode vào template Task Definition.
- Thêm Evidence Level, Evidence, Executed By, Timestamp vào các bản ghi gate.
- Thêm bảng evidence vào Session Handoff.
- Thêm Profile và Current Task Mode vào Project Progress.
- Thêm theo dõi Micro Task nội tuyến (inline).

## Micro Task
- Thêm file thực tế `governance/templates/MICRO_TASK_CHECKLIST.md`.
- Thêm các Ready Gate riêng biệt cho MICRO / MAJOR / SPIKE.

## Evidence
- Completion Gate giờ đây tham chiếu trực tiếp đến Evidence Standard.
- Thêm yêu cầu evidence theo risk vào Completion Gate.
- Thêm quy định nghiêm cấm rõ ràng việc bịa đặt evidence vào Forbidden Actions.
- Thêm Solo Independent Review Procedure (quy trình rà soát độc lập cho cá nhân) cho E2.

## Tích hợp (Integration)
- Viết lại CLAUDE.md thay vì dùng một addendum (phụ lục) được gắn thêm vào.
- Viết lại Session Orchestration để Profile Selection trở thành bước 0 trong luồng S000 thực tế.
- Thêm các standard mới vào chỉ mục governance chính.

## Profile
- Làm rõ ràng tính kế thừa của profile.
- Thêm bộ quy tắc AUDIT rõ ràng.
- AUDIT vẫn mặc định là chỉ đọc (read-only).

## Enforcement
- Thêm các validator Python có thể thực thi:
  - `governance/scripts/governance/validate_structure.py`
  - `governance/scripts/governance/validate_project_state.py`

## Chấp nhận (Acceptance)
- Thêm `ACCEPTANCE_CHECKLIST_V3_2.md`.
