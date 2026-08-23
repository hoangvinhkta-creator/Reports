# 03 — Quy tắc Mô hình Dữ liệu

## Mục tiêu
Cấu trúc dữ liệu phải được thiết kế có chủ đích trước khi feature code được xây dựng.

## Quy tắc: Không tạo schema một cách tình cờ (no schema-by-accident)
Một feature mới phải xác định tất cả các entity và field bị ảnh hưởng trước khi triển khai.

## Mỗi Entity Nên Định nghĩa
- tên entity,
- mục đích,
- định danh (identifier),
- các field,
- kiểu dữ liệu,
- trạng thái bắt buộc/tùy chọn,
- giá trị mặc định,
- mối quan hệ (relationship),
- quyền sở hữu (ownership),
- timestamp tạo,
- timestamp cập nhật,
- vòng đời/trạng thái (lifecycle/status) nếu áp dụng.

## Phân loại Field
Mỗi field quan trọng nên được phân loại thành một trong các nhóm sau:

- Public (công khai)
- Internal business data (dữ liệu nghiệp vụ nội bộ)
- Sensitive business data (dữ liệu nghiệp vụ nhạy cảm)
- Personal/customer data (dữ liệu cá nhân/khách hàng)
- System data (dữ liệu hệ thống)
- Secret / server-only (bí mật / chỉ dành cho server)

## Ví dụ

Customer
- id
- name
- phone
- assignedUserId
- createdAt
- updatedAt

Quote
- id
- customerId
- ownerId
- status
- items[]
- subtotal
- discount
- total
- createdAt
- updatedAt

## Quy tắc

### 1. Một biểu diễn có thẩm quyền duy nhất (one authoritative representation)
Tránh lưu cùng một sự kiện nghiệp vụ ở nhiều nơi, trừ khi việc phi chuẩn hóa (denormalization) là có chủ đích và được đồng bộ.

### 2. Định danh ổn định
Không dùng nhãn hiển thị (display label) làm định danh chính (primary identity).

### 3. Quan hệ rõ ràng
Các mối quan hệ phải được biểu diễn một cách có chủ đích.

### 4. Validate dữ liệu tại ranh giới
Dữ liệu bên ngoài/từ client gửi vào phải được validate trước khi lưu trữ (persistence).

### 5. Không ngầm định tin tưởng vào ngữ nghĩa missing/null
Xác định rõ liệu:
- missing (thiếu),
- null,
- empty string (chuỗi rỗng),
- zero (số 0)

có ý nghĩa khác nhau hay không.

### 6. Thay đổi schema cần phân tích tính tương thích
Trước khi thay đổi một schema đã được lưu trữ (persisted), phải xác định:
- schema hiện tại,
- schema mới,
- các bản ghi hiện có,
- nhu cầu migration,
- rollback,
- khả năng tương thích ngược (backward compatibility).

### 7. Không rename/delete mang tính phá hủy mà thiếu migration
Không được rename hoặc xóa field production rồi mặc định rằng dữ liệu cũ sẽ tự thích ứng.

### 8. Timestamp
Dùng một chiến lược timestamp nhất quán.

### 9. Field trạng thái (status field)
Dùng enum/giá trị trạng thái đã được định nghĩa thay vì chuỗi tùy ý.

### 10. Giá trị nhạy cảm
Không để lộ các field nhạy cảm chỉ vì lý do frontend không hiển thị chúng.

## Mẫu Migration
Đối với các thay đổi schema đã lưu trữ, hãy ghi lại tài liệu:

Schema hiện tại:
...

Schema mục tiêu:
...

Migration:
...

Khả năng tương thích ngược:
...

Validation:
...

Rollback:
...
