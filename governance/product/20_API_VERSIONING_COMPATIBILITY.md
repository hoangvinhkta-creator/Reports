# 20 — Quy Tắc Versioning & Tương Thích API

## Mục Tiêu
Ngăn các thay đổi client/server âm thầm phá vỡ các consumer hiện có.

## Quy Tắc

### 1. Coi các hợp đồng API đã publish là interface
Không thay đổi ý nghĩa của request/response một cách tùy tiện.

### 2. Phân loại thay đổi

Ví dụ không gây breaking:
- thêm trường response tùy chọn (optional),
- thêm trường request tùy chọn với default an toàn.

Có khả năng gây breaking:
- xóa trường,
- đổi tên trường,
- thay đổi kiểu dữ liệu,
- thay đổi ý nghĩa của status,
- thay đổi hành vi authorization,
- thay đổi ngữ nghĩa (semantics) của endpoint.

### 3. Thay đổi gây breaking cần có chiến lược migration
Các lựa chọn có thể bao gồm:
- endpoint có version,
- adapter tương thích,
- rollout theo giai đoạn,
- phối hợp triển khai client.

### 4. Hợp đồng lỗi (Error contracts)
Sử dụng các nhóm lỗi có thể dự đoán được.

### 5. Mở rộng enum/status
Cần cân nhắc đến consumer khi thêm state mới.

### 6. Deprecation (loại bỏ dần)
Khi một API bị deprecate:
- đánh dấu nó,
- xác định các consumer,
- thiết lập lộ trình migration,
- chỉ xóa sau khi các tiêu chí migration được đáp ứng.

### 7. API nội bộ
Ngay cả API nội bộ cũng cần tư duy về tính tương thích nếu có nhiều module/service tiêu thụ nó.

## Review API
Trước khi thay đổi một API, hãy tự hỏi:
- Ai đang tiêu thụ API này?
- Các client cũ có còn hoạt động không?
- Thứ tự deploy có thể làm hỏng hệ thống không?
- Thay đổi có thể backward compatible không?
