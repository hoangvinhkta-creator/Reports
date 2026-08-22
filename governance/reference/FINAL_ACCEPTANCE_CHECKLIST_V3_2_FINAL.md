# CHECKLIST NGHIỆM THU CUỐI CÙNG — V3.2 FINAL

## F-01 Project State Validator
- [ ] Selected Profile được kiểm tra đối chiếu với các giá trị profile được phép.
- [ ] Progress Profile được kiểm tra đối chiếu với các giá trị profile được phép.
- [ ] Current Task Mode được kiểm tra ngữ nghĩa khi được điền.

## F-02 Task / Evidence Enforcement
- [ ] validate_task_completion.py tồn tại.
- [ ] Các task DONE không được chứa REQUIRED FAIL.
- [ ] Các task DONE không được chứa REQUIRED BLOCKED.
- [ ] Các task DONE không được chứa REQUIRED NOT_TESTED.
- [ ] Các check REQUIRED PASS yêu cầu Evidence Level và Evidence.
- [ ] validate_evidence.py tồn tại.
- [ ] REQUIRED PASS với Risk >= 3 yêu cầu E1/E2.
- [ ] E1/E2 yêu cầu Executed By và Timestamp.

## F-03 Manifest
- [ ] Số lượng trong manifest bằng đúng số lượng file thực tế được đóng gói.

## F-04 Micro Task Source of Truth
- [ ] PROJECT_PROGRESS không trùng lặp tiêu chí gate của Micro Task.
- [ ] Checklist Micro chuẩn là `governance/templates/MICRO_TASK_CHECKLIST.md`.

## F-05 S000 Source of Truth
- [ ] CLAUDE.md không trùng lặp toàn bộ quy trình S000.
- [ ] governance/core/00_SESSION_ORCHESTRATION.md là bản chuẩn (canonical).

## F-06 Validation Evidence
- [ ] Báo cáo validation bao gồm Executed By.
- [ ] Báo cáo validation bao gồm Timestamp.
- [ ] Báo cáo validation bao gồm output lệnh E1.

## F-07 E2 Storage
- [ ] docs/reviews/ tồn tại.
- [ ] Template review E2 tồn tại.
- [ ] Evidence Standard quy định nơi lưu trữ artifact E2.

## F-08 Core Structure Validation
- [ ] validate_structure.py kiểm tra governance/core/04_SECURITY_RULES.md.
- [ ] validate_structure.py kiểm tra governance/core/11_FORBIDDEN_ACTIONS.md.

## F-09 Root Cleanup
- [ ] Các changelog/checklist lịch sử đã được chuyển sang docs/history/.
- [ ] Root chỉ chứa một governance/reference/CHANGELOG.md hiện hành.

## Framework Freeze
Sau khi checklist này pass:
- Không thêm tính năng governance nào nữa trước khi pilot trên một dự án thực tế.
- Pilot framework trên một dự án hiện có đã biết rõ.
- Chỉ mở phiên bản kế tiếp dựa trên các phát hiện quan sát được từ pilot.
