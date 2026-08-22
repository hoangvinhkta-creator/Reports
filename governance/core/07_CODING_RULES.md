# 07 — Coding Rules

## Objective
Tạo ra code dễ đọc, dễ bảo trì, không phụ thuộc vào các shortcut ẩn.

## Rules

### 1. Ưu tiên sự rõ ràng hơn sự khôn khéo
Code phải dễ hiểu đối với một developer khác và AI agent trong tương lai.

### 2. Function phải có trách nhiệm rõ ràng
Tránh các function lớn làm nhiều việc không liên quan.

### 3. Component nên giữ tính tập trung
Tách nhỏ component lớn khi các trách nhiệm trở nên khác biệt.

### 4. Không được nuốt lỗi âm thầm
Tránh:

try {
  ...
} catch (e) {}

Lỗi phải được xử lý, lan truyền (propagated), hoặc ghi nhận có chủ đích.

### 5. Không mặc định che giấu type errors
Tránh:
- `@ts-ignore`
- unsafe casts
- tắt các kiểm tra của compiler

trừ khi có lý do biện minh rõ ràng.

### 6. Tránh magic values
Không hard-code:
- tên role,
- statuses,
- route paths,
- limits,
- các khoảng thời gian quan trọng,
- configuration values

xuyên suốt codebase.

Sử dụng constants/config/enums tập trung.

### 7. Tái sử dụng trước khi tạo trùng lặp
Trước khi tạo mới một:
- helper,
- service,
- component,
- type,
- utility,

hãy tìm kiếm phần tương đương đã tồn tại.

### 8. Không cài đặt dependency khi không cần thiết
Trước khi cài một package:
- kiểm tra các dependency hiện có,
- đánh giá khả năng bảo trì/bảo mật,
- xác nhận các công cụ hiện có không thể giải quyết vấn đề.

### 9. Tuân theo các convention hiện có
Không đưa vào một style hoàn toàn khác mà không có lý do kiến trúc.

### 10. Comment giải thích lý do (why), không phải cú pháp hiển nhiên
Dùng comment cho các quyết định, ràng buộc, hoặc đánh đổi (tradeoff) không hiển nhiên.

### 11. Naming
Tên gọi phải truyền tải ý nghĩa nghiệp vụ.

Ưu tiên:
calculateQuoteTotal()

thay vì:
calc()

### 12. Không để lại dead code
Xóa code lỗi thời được tạo ra bởi cùng task khi an toàn và nằm trong phạm vi.

Không thực hiện dọn dẹp không liên quan.

### 13. Tách biệt configuration
Các thiết lập đặc thù theo môi trường thuộc về configuration, không rải rác trong implementation.

### 14. Code production không được phụ thuộc vào debug hack
Các bypass tạm thời không được trở thành hành vi vĩnh viễn.

## Code Review Questions
- Đây có phải là giải pháp nhỏ nhất còn mạch lạc không?
- Trách nhiệm có được đặt đúng layer không?
- Chúng ta có lặp lại logic không?
- Có shortcut ẩn nào không?
- Hành vi khi thất bại (failure behavior) có tường minh không?
- Một developer khác sau này có hiểu được điều này không?
