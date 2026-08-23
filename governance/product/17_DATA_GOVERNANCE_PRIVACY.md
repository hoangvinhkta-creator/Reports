# 17 — Data Governance & Privacy Rules

## Mục tiêu
Xác định cách dữ liệu nghiệp vụ và dữ liệu cá nhân được thu thập, truy cập, lưu trữ, export, chia sẻ, và xóa bỏ.

## Data Inventory (Kiểm kê dữ liệu)
Đối với các tập dữ liệu quan trọng, hãy tài liệu hóa:
- chủ sở hữu (owner),
- mục đích (purpose),
- mức độ nhạy cảm (sensitivity),
- vị trí lưu trữ,
- người dùng được phép,
- thời gian lưu trữ (retention),
- phương pháp xóa,
- hành vi export.

## Data Minimization (Tối thiểu hóa dữ liệu)
Chỉ thu thập và lưu trữ dữ liệu cần thiết cho một mục đích nghiệp vụ đã được xác định.

## Purpose Limitation (Giới hạn mục đích)
Không được tái sử dụng dữ liệu nhạy cảm/khách hàng cho các mục đích không liên quan mà không có quyết định/quy trình phù hợp.

## Access (Truy cập)
Việc truy cập nên tuân theo:
- vai trò (role),
- nhu cầu nghiệp vụ,
- least privilege (đặc quyền tối thiểu).

## Dữ liệu Production trong Development
Quy tắc mặc định:

KHÔNG được sử dụng dữ liệu khách hàng production chưa được làm sạch (unsanitized) trong development hoặc testing.

Sử dụng:
- dữ liệu giả (fake data),
- dữ liệu đã được che dấu (masked data),
- tập con đã được ẩn danh hóa/làm sạch (anonymized/sanitized subsets).

## Export Controls (Kiểm soát export)
Export hàng loạt có thể gây ra rủi ro lớn hơn so với việc xem thông thường.

Xác định:
- các role được phép,
- các field được phép,
- yêu cầu audit,
- kiểm soát về tốc độ/khối lượng khi phù hợp.

## Data Retention (Lưu trữ dữ liệu)
Xác định:
- bản ghi được lưu trữ trong bao lâu,
- điều gì xảy ra với dữ liệu không còn hoạt động (inactive),
- các ràng buộc pháp lý/nghiệp vụ về việc lưu trữ,
- ảnh hưởng đến việc lưu trữ backup.

## Deletion (Xóa dữ liệu)
Làm rõ:
- hard delete (xóa vĩnh viễn),
- soft delete (xóa mềm),
- anonymization (ẩn danh hóa),
- archival (lưu trữ dài hạn).

Không được triển khai việc xóa dữ liệu mà chưa hiểu rõ các bản ghi liên quan cũng như các yêu cầu về compliance/nghiệp vụ.

## Employee Offboarding (Quy trình khi nhân viên nghỉ việc)
Khi một người dùng rời đi:
- thu hồi quyền truy cập tài khoản,
- thu hồi các session/token đang hoạt động khi được hỗ trợ,
- chuyển giao quyền sở hữu (ownership) nếu cần,
- rà soát lại các đặc quyền nâng cao (elevated privileges).

## Bên thứ ba (Third Parties)
Trước khi gửi dữ liệu đến các dịch vụ bên ngoài, hãy cân nhắc:
- các field được truyền đi,
- mục đích,
- credentials,
- thời gian lưu trữ,
- rủi ro từ nhà cung cấp (vendor risk),
- liệu các field nhạy cảm có thực sự cần thiết hay không.

## Privacy by Design (Quyền riêng tư ngay từ thiết kế)
Các tính năng mới nên tự hỏi:
- Chúng ta có thực sự cần field này không?
- Người dùng này có cần field này không?
- Client có cần nhận field này không?
- Nó nên tồn tại trong bao lâu?
