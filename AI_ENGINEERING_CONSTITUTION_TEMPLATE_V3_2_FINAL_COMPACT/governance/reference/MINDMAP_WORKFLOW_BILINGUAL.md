# Mindmap — AI Engineering Workflow / Quy trình phát triển dự án với AI Agent

PROJECT INITIATION / KHỞI TẠO DỰ ÁN
- Session Open / Mở phiên dự án
  - Xác định mục tiêu, loại dự án, quy mô và cách chia session.
- Project Baseline / Thiết lập đường cơ sở
  - Ghi nhận trạng thái ban đầu để biết chính xác hệ thống đang có gì.
- Initial Roadmap / Roadmap sơ bộ
  - Chia dự án thành phase, major task và thứ tự thực hiện.

DISCOVERY & PLANNING / KHẢO SÁT & LẬP KẾ HOẠCH
- Discovery / Khảo sát hệ thống
  - Map architecture, route, data, security, business logic, technical debt.
- Task Decomposition / Phân rã công việc
  - Chia Major Task thành các subtask đủ nhỏ và rõ phạm vi.
- Dependency Analysis / Phân tích phụ thuộc
  - Xác định task nào phải hoàn thành trước và task nào có thể song song.
- Difficulty-Risk-Blast Radius / Độ khó-Rủi ro-Phạm vi ảnh hưởng
  - Đánh giá để quyết định mức kiểm soát và agent phù hợp.
- Agent Assignment / Phân bổ AI Agent
  - Chọn Tier A/B/C/D rồi map sang Haiku/Sonnet/Opus/Fable.
- Preliminary Completion Gate / Bộ kiểm nghiệm thu sơ bộ
  - Xác định trước cách mỗi task phải chứng minh rằng nó hoàn thành đúng.

ROADMAP FINALIZATION / CHỐT ROADMAP
- Scope Lock / Khóa phạm vi
  - Quy định file/module nào task được phép chạm vào.
- Ready Gate / Cổng sẵn sàng
  - Kiểm tra yêu cầu, dependency, scope, agent và điều kiện trước khi code.
- Final Completion Gate / Chốt bộ kiểm nghiệm thu
  - Hoàn thiện và freeze checklist PASS/FAIL trước khi implementation.
- Project Progress Initialization / Khởi tạo file tiến độ
  - PROJECT_PROGRESS.md trở thành dashboard trạng thái chung cho mọi session.

TASK EXECUTION / THỰC THI TASK
- Session Open / Mở session task
  - Đọc progress, task definition, dependency, scope và completion gate.
- Implement / Triển khai
  - Code trong đúng boundary và theo architecture/business/security rules.
- Scope Control / Kiểm soát phạm vi
  - Nếu cần vượt scope phải tạo Scope Expansion thay vì sửa âm thầm.
- Escalation / Nâng cấp xử lý
  - Nếu fail nhiều lần hoặc phát sinh rủi ro lớn, dừng vá và chuyển lên agent mạnh hơn/root-cause review.

VERIFY & ACCEPT TASK / KIỂM TRA & NGHIỆM THU TASK
- Verify / Xác minh
  - Build, lint, typecheck, unit/integration/security/regression test theo task.
- Completion Gate / Cổng hoàn thành
  - Tất cả REQUIRED checks phải PASS và có evidence.
- Exit Criteria / Điều kiện thoát
  - Không còn lỗi critical, tài liệu/progress/handoff đã cập nhật.
- Task Done / Hoàn thành task
  - Chỉ lúc này task mới được đánh dấu DONE.
- Session Handoff / Bàn giao session
  - Ghi file đã sửa, quyết định, rủi ro, checklist và task tiếp theo.

PHASE INTEGRATION / TÍCH HỢP THEO GIAI ĐOẠN
- Phase Gate / Cổng nghiệm thu phase
  - Kiểm tra các task khi ghép lại có hoạt động đúng hay không.
- Regression Invalidation / Phát hiện hồi quy
  - Nếu task mới làm hỏng bảo đảm cũ, mở regression item thay vì giả định mọi task DONE vẫn đúng.

RELEASE READINESS / SẴN SÀNG PHÁT HÀNH
- Release Gate / Cổng phát hành
  - Kiểm tra security, migration, backup, environment, config, rollback, observability.
- Deployment / Triển khai
  - Đưa phiên bản đã qua gate lên môi trường production theo quy trình kiểm soát.
- Post-Deploy Verification / Kiểm tra sau triển khai
  - Xác nhận login, route, CRUD, permission và luồng nghiệp vụ quan trọng hoạt động thật.

FINAL ACCEPTANCE / NGHIỆM THU CUỐI
- End-to-End Validation / Kiểm thử đầu-cuối
  - Kiểm tra toàn bộ luồng người dùng và nghiệp vụ xuyên module.
- Business Acceptance / Nghiệm thu nghiệp vụ
  - Xác nhận sản phẩm đáp ứng requirement và acceptance criteria ban đầu.
- Documentation & Operational Handoff / Bàn giao tài liệu & vận hành
  - Đảm bảo runbook, backup, recovery, deployment, monitoring và quyền vận hành rõ ràng.
- Project Complete / Hoàn tất dự án
  - Chỉ đóng dự án khi release gate, business acceptance và hồ sơ bàn giao đều đạt.
