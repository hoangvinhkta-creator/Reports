# 23 — Tiêu Chuẩn Documentation

## Mục Tiêu
Giữ cho documentation luôn hữu ích như một nguồn sự thật (source of truth) thực sự, thay vì trở thành trang trí lỗi thời.

## Các Danh Mục Documentation Bắt Buộc
Tùy theo quy mô dự án:
- README,
- architecture,
- routes,
- data model,
- permissions/security,
- API contracts,
- environment setup,
- deployment,
- backup/restore,
- incident runbook,
- ADRs.

## Quy Tắc

### 1. Documentation thay đổi cùng với hành vi
Nếu code thay đổi một cách có chủ đích:
- schema,
- route,
- API,
- permission,
- architecture,
- quy trình deployment,

hãy cập nhật documentation tương ứng trong cùng một thay đổi.

### 2. Ưu tiên sự thật hiện tại
Xóa hoặc đánh dấu các hướng dẫn đã lỗi thời.

### 3. Ví dụ phải an toàn
Không bao giờ đặt secret thật, dữ liệu khách hàng, hoặc credential production vào trong documentation.

### 4. Lệnh (Commands)
Các lệnh vận hành cần nêu rõ:
- môi trường (environment),
- điều kiện tiên quyết (prerequisites),
- rủi ro phá hủy nếu có liên quan.

### 5. Sở hữu nguồn sự thật (Source-of-truth ownership)
Tránh trùng lặp các định nghĩa mang tính thẩm quyền (authoritative) ở nhiều file.

Thay vào đó, tham chiếu đến tài liệu gốc có thẩm quyền.

### 6. ADR
Sử dụng Architecture Decision Records cho các lựa chọn kiến trúc mang tính lâu dài.

### 7. Runbook
Các quy trình vận hành cần có thể thực thi được bởi người khác, không chỉ tác giả gốc.

## Bài Kiểm Tra Chất Lượng Documentation
Một developer/AI agent mới cần có khả năng xác định:
- cách chạy dự án,
- cấu trúc dự án như thế nào,
- dữ liệu nằm ở đâu,
- permission hoạt động ra sao,
- cách test,
- cách deploy an toàn,
- những gì không nên thay đổi tùy tiện.
