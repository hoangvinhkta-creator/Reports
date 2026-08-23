# BẢNG KIỂM CHẤP NHẬN — KHUNG V3.1

Dùng file này để xem xét liệu V3.1 có giải quyết được các vấn đề thiết kế đã được xác định hay không.

## A. Cấu trúc Package
- [ ] `docs/tasks/` tồn tại trong package.
- [ ] `docs/sessions/` tồn tại trong package.
- [ ] Các file trạng thái dự án (runtime) nằm dưới `/PROJECT`.
- [ ] Các template tái sử dụng nằm dưới `/templates`.
- [ ] Template không bị nhầm lẫn với các file trạng thái runtime.

## B. Xử lý Xung đột Quy tắc
- [ ] `governance/core/RULE_PRECEDENCE.md` tồn tại.
- [ ] Security có mức ưu tiên cao hơn style/tiện lợi.
- [ ] Tính toàn vẹn dữ liệu (data integrity) và quyền riêng tư được xếp hạng rõ ràng.
- [ ] Precedence (thứ tự ưu tiên) chỉ áp dụng cho các xung đột thực sự.

## C. Governance Tương xứng (Proportional Governance)
- [ ] `governance/core/PROJECT_PROFILE_STANDARD.md` tồn tại.
- [ ] Profile SOLO_LITE tồn tại.
- [ ] Profile PRODUCT tồn tại.
- [ ] Profile TEAM_PRODUCTION tồn tại.
- [ ] Profile AUDIT tồn tại.
- [ ] S000 chọn một profile trước khi hoàn thiện roadmap chi tiết.

## D. Điều chỉnh Nghi thức Task theo Quy mô (Task Ceremony Scaling)
- [ ] `governance/core/TASK_MODE_STANDARD.md` tồn tại.
- [ ] Task MICRO được hỗ trợ.
- [ ] Task MAJOR giữ nguyên đầy đủ governance.
- [ ] Task SPIKE/EXPLORATORY được hỗ trợ.
- [ ] Micro task tự động được nâng cấp (promote) nếu risk/scope tăng lên.

## E. Tính Toàn vẹn của Evidence
- [ ] `governance/core/EVIDENCE_STANDARD.md` tồn tại.
- [ ] E0, E1, E2 được định nghĩa.
- [ ] Các required check thực thi được ở Risk 3 yêu cầu E1.
- [ ] Các check bảo mật/dữ liệu quan trọng ở Risk 4–5 cần đạt E2.
- [ ] Agent bị nghiêm cấm bịa đặt evidence.
- [ ] NOT_TESTED được dùng khi check chưa được thực thi.

## F. Completion Gate
- [ ] Gate sơ bộ được tạo trong giai đoạn lập kế hoạch.
- [ ] Gate cuối cùng chỉ được frozen (đóng băng) khi task chuyển sang READY.
- [ ] Agent không thể làm yếu gate để tự cho mình pass.
- [ ] CODE COMPLETE vẫn khác với TASK COMPLETE.

## G. Audit / Rà soát Dự án Hiện có
- [ ] `governance/audit/DISCOVERY_BASELINE_TEMPLATE.md` tồn tại.
- [ ] `governance/audit/AUDIT_FINDINGS_TEMPLATE.md` tồn tại.
- [ ] Severity hỗ trợ Critical/High/Medium/Low/Info.
- [ ] Finding yêu cầu evidence và hướng khắc phục (remediation path).
- [ ] Profile AUDIT mặc định là chỉ đọc (read-only).

## H. Chống Vá lỗi Lặp lại / Leo thang (Anti-Patching / Escalation)
- [ ] Escalation protocol vẫn còn được duy trì.
- [ ] Các cách tiếp cận thất bại lặp lại sẽ kích hoạt rà soát nguyên nhân gốc (root-cause review).
- [ ] Scope không thể mở rộng một cách âm thầm.
- [ ] Tiêu chí hoàn thành không thể bị vô hiệu hóa để ép cho PASS.

## I. Enforcement
- [ ] `governance/reference/OPTIONAL_ENFORCEMENT_LAYER.md` tồn tại.
- [ ] Việc kiểm tra bằng máy (machine-checkable validation) được mô tả.
- [ ] Enforcement là tùy chọn/tương xứng theo từng profile.
- [ ] TEAM_PRODUCTION khuyến nghị tích hợp CI.

## J. Ánh xạ Agent
- [ ] Các capability tier vẫn được giữ nguyên.
- [ ] Governance không phụ thuộc vào việc Fable là một model chuyên biệt cho thiết kế.
- [ ] Việc ánh xạ agent thực tế phụ thuộc vào dự án/môi trường cụ thể.

## Chấp nhận Cuối cùng

V3.1 được chấp nhận khi:
- [ ] Các mục A–J đều được thỏa mãn.
- [ ] Không còn sự mơ hồ trùng lặp giữa runtime/template.
- [ ] Không thiếu thư mục bắt buộc nào được governance tham chiếu đến.
- [ ] Framework có thể vận hành ở cả chế độ nhẹ (lightweight) lẫn chế độ nghiêm ngặt (strict).
- [ ] Việc hoàn thành task rủi ro cao không thể chỉ dựa vào các khẳng định tự nhận (self-claim) không có bằng chứng hỗ trợ.

Reviewer:
...

Date:
...

Result:
ACCEPTED / CHANGES_REQUIRED

Notes:
...
