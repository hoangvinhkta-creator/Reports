# 15 — Logging, Audit & Observability Rules

## Mục tiêu
Giúp hành vi của production có thể chẩn đoán được mà không làm lộ dữ liệu nhạy cảm.

## Ba khái niệm khác nhau

### Application Logs (Log ứng dụng)
Các sự kiện kỹ thuật dùng để xử lý sự cố (troubleshoot) hệ thống.

### Metrics / Monitoring (Chỉ số / Giám sát)
Các tín hiệu được tổng hợp như:
- tỷ lệ lỗi (error rate),
- độ trễ (latency),
- các request thất bại,
- số lượng job thất bại.

### Audit Log (Nhật ký kiểm toán)
Bản ghi nghiệp vụ/bảo mật về việc ai đã thay đổi cái gì.

Không được nhầm lẫn giữa các hệ thống này.

## Các quy tắc Logging

### 1. Log lại các lỗi có ý nghĩa
Bao gồm đủ ngữ cảnh để chẩn đoán vấn đề mà không làm lộ secrets.

### 2. Sử dụng structured context (ngữ cảnh có cấu trúc)
Khi có thể, hãy bao gồm:
- tên sự kiện (event name),
- request/correlation ID,
- module,
- entity ID an toàn,
- user ID khi phù hợp,
- environment.

### 3. Không bao giờ log secrets
Không được log:
- mật khẩu (passwords),
- access tokens,
- refresh tokens,
- private keys,
- secret API credentials.

### 4. Giảm thiểu dữ liệu cá nhân nhạy cảm
Không log toàn bộ dữ liệu khách hàng trừ khi thực sự cần thiết.

### 5. Khả năng thấy lỗi (Error visibility)
Các lỗi backend nghiêm trọng không được biến mất một cách âm thầm.

## Monitoring (Giám sát)
Cân nhắc thiết lập cảnh báo (alert) cho:
- tỷ lệ lỗi tăng cao,
- lỗi xác thực (auth failures),
- lỗi database,
- lỗi queue/job,
- độ trễ bất thường,
- dung lượng lưu trữ (storage capacity),
- các tích hợp bị lỗi.

## Audit Logging

Các hành động có giá trị cao nên cân nhắc có một bản ghi audit bất biến (immutable) hoặc được bảo vệ.

Các sự kiện điển hình:
- các sự kiện bảo mật liên quan đến đăng nhập,
- thay đổi role/permission,
- export dữ liệu khách hàng,
- xóa bản ghi,
- ghi đè báo giá/giá (quote/price override),
- phê duyệt/từ chối,
- thay đổi cấu hình.

Các field được khuyến nghị:
- auditEventId,
- timestamp,
- actorUserId,
- action,
- resourceType,
- resourceId,
- giá trị before/after an toàn khi phù hợp,
- source/request ID.

## Audit Security (Bảo mật Audit)
Người dùng thông thường không được phép thay đổi các bản ghi audit lịch sử.

## Privacy (Quyền riêng tư)
Việc ghi audit log không phải là lý do để lưu trữ dữ liệu nhạy cảm không cần thiết.

## Diagnostic Correlation (Liên kết chẩn đoán)
Ở nơi khả thi, lan truyền một request/correlation ID xuyên suốt:
frontend → API → backend → tích hợp bên ngoài.
