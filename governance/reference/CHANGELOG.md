# CHANGELOG

## V3.2 Final

### Enforcement
- `governance/scripts/governance/validate_project_state.py` giờ đây kiểm tra giá trị profile/task-mode thực tế thay vì chỉ kiểm tra nhãn.
- Đã thêm `governance/scripts/governance/validate_task_completion.py`.
- Đã thêm `governance/scripts/governance/validate_evidence.py`.
- Structure validator giờ đây bao gồm cả `governance/core/11_FORBIDDEN_ACTIONS.md` và `governance/core/04_SECURITY_RULES.md`.

### Runtime consistency
- Việc theo dõi inline của Micro Task giờ đây tham chiếu đến checklist Micro Task chuẩn thay vì trùng lặp lại nó.
- `CLAUDE.md` không còn trùng lặp toàn bộ quy trình S000; `governance/core/00_SESSION_ORCHESTRATION.md` là nguồn sự thật duy nhất.
- Đã thêm vị trí lưu trữ và template cho output review E2.
- Báo cáo validation giờ đây bao gồm cả Executed By và Timestamp.
- Đã sửa lỗi sinh package manifest.

### Cleanup
- Các changelog/checklist lịch sử đã được chuyển sang `docs/history/`.

## V3.2
Xem `governance/reference/history/CHANGELOG_V3_2.md`.

## V3.1
Xem `governance/reference/history/CHANGELOG_V3_1.md`.
