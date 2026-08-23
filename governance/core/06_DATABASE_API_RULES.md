# 06 — Database & API Rules

## Objective
Ngăn chặn truy cập database không kiểm soát và tạo ranh giới rõ ràng giữa application logic và persistence.

## Required Flow
Ưu tiên:

UI
→ Use Case / Service
→ Repository / API
→ Database

## Rules

### 1. UI components không được truy cập database trực tiếp
Tránh các lệnh gọi database SDK rải rác khắp pages/components.

### 2. Tập trung hóa persistence
Sử dụng repositories/services/API clients.

### 3. Validate mọi input từ bên ngoài
Validate:
- types,
- required fields,
- formats,
- allowed ranges,
- enum values,
- ownership,
- permission.

### 4. Server authority
Các phép tính nhạy cảm và quyết định phân quyền nên dùng thông tin server-side đáng tin cậy.

### 5. API contracts phải tường minh
Định nghĩa:
- request,
- response,
- errors,
- authorization,
- validation,
- side effects.

### 6. Không phơi bày implementation nội bộ khi không cần thiết
Frontend không nên phụ thuộc chặt chẽ vào cấu trúc lưu trữ thô.

### 7. Idempotency
Đối với các thao tác có khả năng bị retry, đánh giá xem request lặp lại có thể:
- tạo bản trùng lặp,
- tính phí hai lần,
- gửi hai lần,
- tạo task trùng lặp.

Sử dụng cơ chế idempotency khi phù hợp.

### 8. Transactions
Sử dụng hành vi transactional khi nhiều thao tác ghi phải cùng thành công hoặc cùng thất bại.

### 9. Pagination
Không nên tải toàn bộ tập dữ liệu lớn mà không có lý do.

### 10. Query access boundaries
Các truy vấn phải tuân thủ bộ lọc quyền và quy tắc ownership.

### 11. Error handling
Phân biệt:
- lỗi validation,
- lỗi authorization,
- not found,
- conflicts,
- lỗi hạ tầng (infrastructure failures).

### 12. Destructive operations
Các thao tác xóa nên cân nhắc:
- dependencies,
- soft delete,
- audit trail,
- khả năng khôi phục,
- permission.

## API Contract Template

Endpoint / Function:
...

Purpose:
...

Authentication:
...

Authorization:
...

Input:
...

Validation:
...

Output:
...

Errors:
...

Side effects:
...

Idempotency:
...
