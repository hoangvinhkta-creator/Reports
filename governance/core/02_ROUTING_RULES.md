# 02 — Quy tắc Routing

## Mục tiêu
Route phải phản ánh cấu trúc ứng dụng thay vì dồn các chức năng không liên quan vào phía sau một URL tĩnh duy nhất.

## Quy tắc

### 1. Các năng lực chính phải có route rõ ràng
Ví dụ:

/dashboard
/customers
/customers/:customerId
/quotes
/quotes/:quoteId
/orders
/orders/:orderId
/care/today
/reports
/settings/users

### 2. Không ẩn toàn bộ ứng dụng phía sau một route duy nhất
Việc chuyển đổi giữa các phần chính của ứng dụng chỉ thông qua local tab state là không được khuyến khích.

Tab có thể chấp nhận được cho các view phụ bên trong một resource logic duy nhất.

### 3. Route phải an toàn khi refresh
Mở hoặc refresh một deep link hợp lệ phải render đúng trang dự kiến.

### 4. Lịch sử trình duyệt phải hoạt động
Điều hướng Back/Forward phải phản ánh đúng việc điều hướng có ý nghĩa trong ứng dụng.

### 5. Tham số route phải rõ ràng
Dùng các định danh ổn định như:

/customers/:customerId

Không dựa vào trạng thái ẩn/tạm thời cho danh tính (identity) trang quan trọng.

### 6. Bảo vệ xác thực (authentication guard)
Các route được bảo vệ phải yêu cầu danh tính đã xác thực (authenticated identity).

### 7. Bảo vệ phân quyền (authorization guard)
Các route nhạy cảm phải kiểm tra quyền/vai trò cần thiết trước khi render.

Ví dụ:
/settings/users
/admin
/pricing/cost

### 8. Frontend guard không phải là ranh giới bảo mật
Việc phân quyền ở backend/database vẫn phải được thực thi.

### 9. Xác định quyền sở hữu route
Mỗi route phải thuộc về một module.

### 10. Thay đổi route cần rà soát tác động
Kiểm tra:
- link điều hướng,
- bookmark,
- redirect,
- quyền hạn,
- test,
- analytics,
- các giả định về API,
- deep link.

## Checklist Routing
Trước khi hoàn tất một thay đổi route:
- URL trực tiếp hoạt động.
- Refresh hoạt động.
- Back/forward hoạt động.
- Truy cập trái phép bị chặn.
- Có trạng thái not-found.
- Có trạng thái loading khi cần.
- Tham số route được validate.
