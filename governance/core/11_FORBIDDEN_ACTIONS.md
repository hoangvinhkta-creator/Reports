# 11 — Forbidden Actions

AI coding agent KHÔNG ĐƯỢC:

1. Bắt đầu viết code trước khi kiểm tra implementation hiện có liên quan.
2. Đặt secrets hoặc thông tin xác thực riêng tư vào frontend code.
3. Coi UI ẩn là authorization.
4. Bypass các quy tắc bảo mật để làm cho một tính năng hoạt động.
5. Tin tưởng dữ liệu role, permission, owner, price, hoặc approval do client cung cấp.
6. Truy cập database trực tiếp từ UI components khi đã có hoặc nên có một application data layer.
7. Nhân đôi các business rule đã thiết lập mà không có lý do biện minh.
8. Đổi tên/xóa các trường production đã lưu (persisted) mà không phân tích migration.
9. Thay đổi các module không liên quan nằm ngoài phạm vi task.
10. Thực hiện một cuộc viết lại lớn (rewrite) chỉ vì ưa thích một kiến trúc khác.
11. Vô hiệu hóa tests, lint, compiler checks, hoặc security controls để đạt được một build pass.
12. Sử dụng `@ts-ignore`, `any` diện rộng, unsafe casts, hoặc tương đương làm cách mặc định để giải quyết vấn đề type.
13. Nuốt exception một cách âm thầm.
14. Hard-code secrets, permissions, các quy tắc role quan trọng, hoặc các giá trị đặc thù theo môi trường xuyên suốt application code.
15. Cài đặt một thư viện mới trước khi kiểm tra xem project đã có giải pháp phù hợp hay chưa.
16. Tạo ra circular dependency.
17. Thực hiện thay đổi dữ liệu mang tính phá hủy mà không cân nhắc rollback.
18. Giả định dữ liệu hiện có khớp với schema mới.
19. Trả về cho client nhiều dữ liệu nhạy cảm hơn mức cần thiết.
20. Phơi bày internal stack trace/secrets cho end user.
21. Trộn lẫn major refactoring và feature work mà không có lý do rõ ràng.
22. Đánh dấu công việc hoàn thành trong khi build/tests liên quan đang thất bại.
23. Bỏ qua một xung đột đã phát hiện giữa documentation và implementation.
24. Sửa các vấn đề không liên quan một cách tùy tiện trừ khi task được yêu cầu cần điều đó.
25. Thay thế code ổn định đang hoạt động chỉ để làm nó khác đi về mặt phong cách.

26. Bịa đặt, ngụy tạo, hoặc tuyên bố sai sự thật về command output, kết quả test, HTTP status code, screenshot, kết quả CI, bằng chứng thực thi (execution evidence), sự phê duyệt của reviewer, hoặc sự phê duyệt của con người. Nếu một kiểm tra chưa thực sự được thực thi, phải đánh dấu `NOT_TESTED`.

## Required Response to a Blocker
Nếu một trong các quy tắc này ngăn cản việc triển khai, hãy báo cáo:

BLOCKER

Reason:
...

Affected requirement:
...

Safe options:
...

Recommended option:
...

Không được âm thầm bỏ qua quy tắc này.
