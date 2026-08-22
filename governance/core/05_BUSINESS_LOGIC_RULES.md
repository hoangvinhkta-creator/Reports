# 05 — Quy tắc Business Logic

## Mục tiêu
Các quy tắc nghiệp vụ (business rule) phải được tập trung hóa, tái sử dụng được, kiểm thử được, và độc lập với cách triển khai UI.

## Quy tắc

### 1. Không chôn business logic trong UI component
Component nên chủ yếu xử lý:
- render,
- tương tác người dùng,
- trạng thái trình bày cục bộ (local presentation state).

### 2. Quy tắc nghiệp vụ thuộc về use case/service/domain logic
Ví dụ:
- tính toán báo giá,
- giới hạn chiết khấu,
- chuyển trạng thái đơn hàng,
- lên lịch chăm sóc khách hàng (follow-up),
- quy tắc gán khách hàng.

### 3. Một quy tắc nghiệp vụ = một cách triển khai có thẩm quyền duy nhất
Không được triển khai lại cùng một phép tính một cách độc lập ở nhiều trang.

### 4. Tránh handler khổng lồ
Không tạo handler gộp chung:
- validation,
- tính toán,
- truy cập database,
- phân quyền,
- ghi audit log,
- thông báo (notification),
- trạng thái UI.

Hãy tách các trách nhiệm ra riêng.

### 5. Chuyển trạng thái phải rõ ràng
Ví dụ:

DRAFT
→ SENT
→ ACCEPTED
→ ORDERED

Định nghĩa rõ các chuyển trạng thái được phép và bị cấm.

### 6. Quy tắc nghiệp vụ nên có tính xác định (deterministic) khi có thể
Logic tính toán thuần túy (pure calculation) nên tránh các phụ thuộc bên ngoài ẩn.

### 7. Side effect phải hiển thị rõ ràng
Ví dụ:
Việc tạo một đơn hàng cũng có thể:
- tạo các task follow-up,
- cập nhật trạng thái khách hàng,
- ghi lịch sử audit.

Các hiệu ứng phụ (side effect) này phải được thể hiện rõ ràng trong use case.

### 8. Domain validation khác với form validation
UI validation cải thiện trải nghiệm người dùng.
Business validation bảo vệ tính đúng đắn của hệ thống.

Cả hai đều có thể cần thiết.

### 9. Không âm thầm thay đổi hành vi nghiệp vụ khi refactor
Các thay đổi về hành vi phải có chủ đích và được ghi lại tài liệu.

## Luồng Được khuyến nghị

UI
↓
Use Case
↓
Business Rules
↓
Repository/API
↓
Persistence

## Ví dụ
Thay vì:

handleSaveQuote()

thực hiện mọi thứ, nên ưu tiên:

createQuote(input)
calculateQuoteTotals(items)
validateDiscount(user, discount)
quoteRepository.save(quote)
careService.scheduleFollowUps(order)
auditService.record(...)
