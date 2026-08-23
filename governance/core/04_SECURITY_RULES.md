# 04 — Quy tắc Bảo mật

## Nguyên tắc Bảo mật Cốt lõi
Client là không đáng tin cậy (untrusted).

Bất cứ thứ gì gửi tới browser/app phải được xem là có thể quan sát được và có thể bị thao túng.

## Quy tắc Bắt buộc

### 1. Không bao giờ lưu secret trong frontend code
Không được để lộ:
- private API key,
- admin credential,
- database secret,
- private token,
- service account credential.

### 2. Ẩn trên UI không phải là authorization
Đây KHÔNG phải là bảo mật:

if (!isAdmin) hideButton()

Việc phân quyền (authorization) cũng phải được thực thi ở:
- backend,
- server function,
- API,
- database/security rules.

### 3. Nguyên tắc đặc quyền tối thiểu (least privilege)
Người dùng và service chỉ nhận đúng quyền cần thiết cho vai trò của họ.

### 4. Mặc định từ chối (default deny)
Các resource nhạy cảm nên không thể truy cập được trừ khi được cấp phép rõ ràng.

### 5. Không bao giờ tin dữ liệu phân quyền do client gửi lên
Không được tin các giá trị client gửi lên như:
- role,
- userId,
- ownerId,
- permission,
- price,
- discount,
- approval state.

Phải validate các giá trị có thẩm quyền (authoritative) ở phía server.

### 6. Bảo vệ dữ liệu nghiệp vụ nhạy cảm
Ví dụ:
- giá vốn (cost price),
- biên lợi nhuận (margin),
- điều khoản nhà cung cấp nội bộ,
- ghi chú nội bộ,
- thông tin cá nhân của khách hàng,
- các bản export.

### 7. Authentication không phải là authorization
Một người dùng đã xác thực (authenticated) không tự động được phép truy cập mọi resource.

### 8. Phải thực thi quyền sở hữu resource
Nếu người dùng chỉ được truy cập các customer/order/v.v. được gán cho họ, quy tắc đó phải được thực thi ở tầng backend/data.

### 9. Validate các thao tác thay đổi (mutation)
Các thao tác create/update/delete yêu cầu:
- danh tính đã xác thực (authenticated identity),
- phân quyền (authorization),
- input đã được validate,
- chuyển trạng thái (state transition) được phép.

### 10. Tránh trả về dữ liệu dư thừa
API và database query chỉ nên trả về các field cần thiết.

### 11. Hạn chế logging
Không bao giờ log:
- mật khẩu,
- token xác thực đầy đủ,
- private secret,
- dữ liệu khách hàng nhạy cảm không cần thiết.

### 12. Thông báo lỗi (error message)
Không để lộ chi tiết stack nội bộ hoặc secret cho end user.

### 13. Các thao tác nhạy cảm về bảo mật
Cân nhắc thêm các biện pháp kiểm soát bổ sung cho:
- xóa bản ghi,
- export hàng loạt,
- thay đổi vai trò (role),
- ghi đè giá (price override),
- điều chỉnh tài chính,
- cấu hình nhạy cảm.

### 14. Khả năng kiểm toán (auditability)
Các thay đổi rủi ro cao nên ghi lại:
- người thực hiện (actor),
- timestamp,
- hành động (action),
- đối tượng tác động (target),
- trạng thái trước/sau liên quan, khi thích hợp.

## Rà soát Bảo mật
Với mỗi feature, hãy đặt câu hỏi:
- Ai có thể đọc cái này?
- Ai có thể tạo nó?
- Ai có thể cập nhật nó?
- Ai có thể xóa nó?
- Người dùng có thể truy cập resource của người dùng khác bằng cách đổi ID không?
- Frontend có nhận được dữ liệu mà người dùng lẽ ra không bao giờ được thấy không?
- Việc phân quyền có được thực thi bên ngoài UI không?
