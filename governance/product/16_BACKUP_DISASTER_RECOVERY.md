# 16 — Backup & Disaster Recovery Rules

## Mục tiêu
Bảo vệ doanh nghiệp khỏi việc xóa nhầm, hỏng dữ liệu, migration thất bại, tài khoản bị xâm nhập, và lỗi hạ tầng.

## Nguyên tắc cốt lõi
Một bản backup chỉ hữu ích nếu nó có thể được restore (khôi phục).

## Các quyết định bắt buộc

### RPO — Recovery Point Objective (Mục tiêu điểm khôi phục)
Lượng dữ liệu mất mát tối đa có thể chấp nhận được, đo bằng thời gian.

Ví dụ:
RPO = 24 giờ.

### RTO — Recovery Time Objective (Mục tiêu thời gian khôi phục)
Thời gian tối đa mục tiêu để khôi phục dịch vụ quan trọng.

Ví dụ:
RTO = 4 giờ.

Các giá trị riêng của từng dự án phải được xác định dựa trên mức độ quan trọng đối với nghiệp vụ.

## Các quy tắc Backup

### 1. Xác định dữ liệu quan trọng
Ví dụ:
- khách hàng (customers),
- đơn hàng (orders),
- báo giá (quotes),
- configuration,
- bản ghi audit,
- các file quan trọng.

### 2. Xác định tần suất backup
Dựa trên RPO và tốc độ thay đổi dữ liệu.

### 3. Xác định thời gian lưu trữ (retention)
Ví dụ:
- lưu trữ theo ngày,
- theo tuần,
- theo tháng.

### 4. Bảo vệ backups
Quyền truy cập backup nên tuân theo nguyên tắc least privilege (đặc quyền tối thiểu).

### 5. Tách biệt failure domain (vùng lỗi)
Ở nơi khả thi, tránh việc chỉ lưu bản backup duy nhất trong cùng một failure domain logic với production.

### 6. Kiểm thử việc restore
Định kỳ kiểm thử:
- tính toàn vẹn của backup,
- quy trình restore,
- credentials,
- các bước đã được tài liệu hóa.

### 7. Schema migrations
Thực hiện backup/snapshot phù hợp trước các migration mang tính phá hủy có rủi ro.

### 8. Các thao tác phá hủy hàng loạt (Bulk destructive operations)
Trước khi xóa/cập nhật hàng loạt:
- xác thực phạm vi mục tiêu (target scope),
- yêu cầu ủy quyền (authorization) phù hợp,
- cân nhắc snapshot/backup,
- cung cấp dry-run (chạy thử) khi khả thi.

## Disaster Recovery Runbook (Quy trình khôi phục sau thảm họa)
Tài liệu hóa:
1. công bố sự cố (incident declaration),
2. ngăn chặn (containment) dịch vụ,
3. xác định trạng thái tốt cuối cùng đã biết (last known good state),
4. chọn điểm khôi phục (recovery point),
5. thực hiện restore,
6. xác minh tính toàn vẹn,
7. khôi phục lưu lượng truy cập ứng dụng,
8. giám sát (monitor),
9. tài liệu hóa sự cố.

## Quy tắc dành cho AI Agent
Một AI coding agent không được mặc định rằng đã tồn tại một bản backup.
Trước khi đề xuất một migration mang tính phá hủy, phải xác định rõ ràng các yêu cầu về backup/rollback.
