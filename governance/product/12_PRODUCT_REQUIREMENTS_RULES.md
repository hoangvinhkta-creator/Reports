# 12 — Product Requirements Rules

## Mục tiêu
Đảm bảo team và AI agent hiểu rõ cái gì cần được xây dựng, tại sao nó quan trọng, ai được phép sử dụng, và "hoàn thành" nghĩa là gì trước khi bắt đầu implementation.

## Quy tắc cốt lõi
Không implement một feature không tầm thường chỉ từ một câu mô tả không chính thức khi hành vi nghiệp vụ quan trọng vẫn còn chưa được xác định.

Một feature specification cần được tạo hoặc xác nhận trước khi thay đổi code.

## Feature Specification tối thiểu

### 1. Problem (Vấn đề)
Vấn đề người dùng/nghiệp vụ nào đang được giải quyết?

### 2. Business Goal (Mục tiêu nghiệp vụ)
Kết quả nào cần được cải thiện?

Ví dụ:
- giảm việc theo dõi thủ công,
- giảm lỗi định giá,
- tăng tốc độ phản hồi,
- ngăn chặn việc lộ dữ liệu trái phép.

### 3. Users / Roles (Người dùng / Vai trò)
Ai sử dụng feature này?

Ví dụ:
- sales,
- sales_manager,
- admin,
- customer_service.

### 4. User Flow (Luồng người dùng)
Mô tả luồng công việc chính được kỳ vọng.

### 5. Functional Requirements (Yêu cầu chức năng)
Nêu rõ hành vi hệ thống bắt buộc.

### 6. Acceptance Criteria (Tiêu chí nghiệm thu)
Sử dụng các phát biểu có thể kiểm thử được.

Ví dụ:
- Sales Manager có thể export dữ liệu khách hàng được giao.
- Vai trò Sales không thể export toàn bộ cơ sở dữ liệu khách hàng.
- Mỗi lần export đều tạo ra một audit event.

### 7. Out of Scope (Nằm ngoài phạm vi)
Nêu rõ những gì task này KHÔNG bao gồm.

### 8. Data Requirements (Yêu cầu dữ liệu)
Xác định:
- entity được đọc,
- entity được ghi,
- các field được hiển thị,
- các field nhạy cảm,
- ảnh hưởng đến retention (thời gian lưu trữ).

### 9. Permission Requirements (Yêu cầu phân quyền)
Xác định ai có thể:
- xem (view),
- tạo (create),
- cập nhật (update),
- xóa (delete),
- export,
- phê duyệt (approve).

### 10. Edge Cases (Trường hợp biên)
Ví dụ:
- dữ liệu rỗng,
- bản ghi liên kết bị thiếu,
- hành động bị trùng lặp,
- session hết hạn,
- người dùng bị mất quyền giữa chừng luồng xử lý,
- lỗi network/API.

### 11. Success Metric (Chỉ số thành công)
Khi phù hợp, xác định cách đo lường thành công.

## Requirement Ambiguity Rule (Quy tắc về sự mơ hồ trong yêu cầu)
Nếu việc implementation đòi hỏi phải đoán một business rule có thể làm thay đổi đáng kể hành vi hệ thống, hãy gắn cờ nó là:

REQUIREMENT GAP

Missing decision:
...

Possible options:
...

Risk of guessing:
...

Recommended default:
...

Đối với các chi tiết implementation có rủi ro thấp, hãy dùng giá trị mặc định an toàn nhất tương thích với kiến trúc và ghi chú lại.

## Quy tắc thay đổi
Nếu yêu cầu thay đổi sau khi implementation đã bắt đầu:
- cập nhật specification,
- chạy lại impact analysis (phân tích tác động),
- xác định tác động đến data/security/test,
- không được âm thầm thay đổi hành vi hệ thống.
