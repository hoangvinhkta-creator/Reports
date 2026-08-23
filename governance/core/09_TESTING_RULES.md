# 09 — Testing Rules

## Objective
Một tính năng chỉ được coi là hoàn thành khi hành vi liên quan và các chế độ lỗi (failure modes) đã được xác minh.

## Minimum Verification Where Applicable

- build
- lint
- type check
- unit tests
- integration tests
- route behavior
- authentication
- authorization
- CRUD behavior
- error handling
- regression checks

## Feature Test Cases
Đối với các tính năng quan trọng, cân nhắc:

### Happy path
Người dùng hợp lệ, được phân quyền hoàn thành quy trình bình thường.

### Invalid input
Input sai hoặc không đầy đủ bị từ chối một cách an toàn.

### Unauthorized
Người dùng đã xác thực nhưng không có quyền không thể thực hiện hành động.

### Unauthenticated
Các thao tác được bảo vệ từ chối truy cập chưa xác thực.

### Missing data
Các bản ghi liên quan bị thiếu/đã xóa không làm ứng dụng crash.

### Duplicate/retry
Request lặp lại không tạo ra side effect trùng lặp nguy hiểm.

### Backend failure
Lỗi tạo ra một trạng thái lỗi được kiểm soát.

### Boundary values
Kiểm tra các giá trị quan trọng:
- zero,
- max/min,
- mảng rỗng,
- giá trị lớn,
- boundary về ngày tháng.

## Security Testing
Kiểm tra quyền truy cập bằng cách chỉnh sửa:
- URL IDs,
- request body IDs,
- owner IDs,
- roles,
- các trường ẩn (hidden fields).

Không được giả định rằng giới hạn ở UI là đủ.

## Regression
Xác minh các hành vi hiện có lân cận có khả năng bị ảnh hưởng bởi thay đổi.

## Completion Rule
Không được báo cáo "done" nếu:
- build bị lỗi,
- tests thất bại,
- vấn đề permission đã biết vẫn còn tồn tại,
- schema migration chưa hoàn tất,
- critical path chưa được xác minh.

Nếu một kiểm tra không thể thực thi, phải báo cáo rõ ràng:
- những gì chưa được test,
- lý do,
- rủi ro phát sinh.
