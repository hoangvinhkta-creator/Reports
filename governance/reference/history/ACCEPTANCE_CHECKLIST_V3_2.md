# BẢNG KIỂM CHẤP NHẬN — V3.2

## A. Kết nối Runtime (Runtime Wiring)
- [ ] Task Definition bao gồm Task Mode.
- [ ] Task Definition bao gồm Evidence Level.
- [ ] Task Definition bao gồm Executed By và Timestamp.
- [ ] Session Handoff bao gồm bảng evidence.
- [ ] Project Progress bao gồm Profile.
- [ ] Project Progress bao gồm Current Task Mode.
- [ ] Project Progress bao gồm mục Micro Task nội tuyến (inline).

## B. Micro Task
- [ ] `governance/templates/MICRO_TASK_CHECKLIST.md` tồn tại.
- [ ] Micro Ready Gate tồn tại.
- [ ] Micro Completion Gate tồn tại.
- [ ] Việc nâng cấp (promotion) lên MAJOR được định nghĩa.

## C. Evidence
- [ ] Completion Gate tham chiếu trực tiếp đến `governance/core/EVIDENCE_STANDARD.md`.
- [ ] Yêu cầu evidence theo risk được nêu rõ ràng.
- [ ] Các check chưa được thực thi trở thành NOT_TESTED.
- [ ] Forbidden Actions nghiêm cấm việc bịa đặt evidence.
- [ ] Quy trình Solo E2 Independent Review (rà soát độc lập) tồn tại.

## D. Governance Tích hợp
- [ ] `CLAUDE.md` có một cấu trúc top-level tích hợp thống nhất.
- [ ] S000 bắt đầu bằng Profile Selection.
- [ ] `governance/core/00_SESSION_ORCHESTRATION.md` bao gồm việc chọn profile trong luồng chính có thứ tự của S000.
- [ ] Relevant Governance Files bao gồm tất cả các standard mới của V3.1/V3.2.

## E. Profile
- [ ] Tính kế thừa của SOLO_LITE được nêu rõ ràng.
- [ ] Tính kế thừa của PRODUCT được nêu rõ ràng.
- [ ] Tính kế thừa của TEAM_PRODUCTION được nêu rõ ràng.
- [ ] Bộ quy tắc bắt buộc của AUDIT được liệt kê rõ ràng.
- [ ] AUDIT mặc định là READ ONLY.

## F. Enforcement
- [ ] `governance/scripts/governance/validate_structure.py` tồn tại.
- [ ] `governance/scripts/governance/validate_project_state.py` tồn tại.
- [ ] Cả hai validator đều thực thi thành công trên cấu trúc package đã được khởi tạo, ở những nơi áp dụng được.

## G. Package
- [ ] Không còn mơ hồ giữa root/runtime template.
- [ ] `docs/tasks/` tồn tại.
- [ ] `docs/sessions/` tồn tại.
- [ ] Số lượng trong manifest khớp với nội dung package.

## Kết quả Cuối cùng
ACCEPTED / CHANGES_REQUIRED

Reviewer:
...

Date:
...

Notes:
...
