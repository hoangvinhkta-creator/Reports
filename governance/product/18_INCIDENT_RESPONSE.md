# 18 — Quy Tắc Ứng Phó Sự Cố

## Mục Tiêu
Ứng phó với sự cố production một cách có hệ thống thay vì áp dụng các bản vá thiếu kiểm soát.

## Ví Dụ Về Sự Cố
- sập hệ thống production,
- truy cập trái phép,
- rò rỉ dữ liệu,
- cập nhật hàng loạt sai,
- migration thất bại,
- suy giảm hiệu năng nghiêm trọng,
- lỗi tích hợp nghiêm trọng.

## Quy Trình Xử Lý Sự Cố

INCIDENT DETECTED
↓
ASSESS
↓
CONTAIN
↓
PRESERVE EVIDENCE
↓
DIAGNOSE
↓
RECOVER
↓
VERIFY
↓
POSTMORTEM

## 1. Đánh Giá (Assess)
Xác định:
- người dùng bị ảnh hưởng,
- hệ thống bị ảnh hưởng,
- rủi ro dữ liệu,
- rủi ro bảo mật,
- mức độ nghiêm trọng đối với business,
- thời điểm bắt đầu.

## 2. Ngăn Chặn (Contain)
Ví dụ:
- vô hiệu hóa tính năng bị ảnh hưởng,
- thu hồi credential bị lộ,
- chặn mutation nguy hiểm,
- rollback bản release.

Ưu tiên ngăn chặn hơn là viết lại theo suy đoán.

## 3. Bảo Toàn Bằng Chứng (Preserve Evidence)
Không phá hủy các thông tin hữu ích sau:
- logs,
- audit records,
- request IDs,
- chi tiết deployment,
- timestamps.

## 4. Chẩn Đoán (Diagnose)
Xác định root cause thực sự hoặc phạm vi lỗi hẹp nhất đã được xác nhận.

## 5. Khôi Phục (Recovery)
Lựa chọn:
- rollback,
- restore,
- sửa cấu hình,
- hotfix tối thiểu,
- fix-forward có kiểm soát.

## 6. Xác Minh (Verify)
Xác nhận:
- dịch vụ đã được khôi phục,
- bảo mật đã được khôi phục,
- tính toàn vẹn dữ liệu,
- không còn lỗi tiếp diễn,
- các luồng bị ảnh hưởng hoạt động bình thường.

## 7. Rút Kinh Nghiệm (Postmortem)
Tài liệu hóa:
- timeline,
- tác động (impact),
- root cause,
- lý do các cơ chế phòng vệ thất bại,
- hành động khắc phục,
- biện pháp phòng ngừa.

## Quy Tắc Cho AI Agent Khi Xử Lý Sự Cố
Trong lúc xử lý sự cố:
- không thực hiện refactor không liên quan,
- không thực hiện nhiều bản sửa mang tính suy đoán cùng lúc,
- không xóa bằng chứng,
- ưu tiên các thay đổi tối thiểu và có thể đảo ngược,
- báo cáo rõ ràng các giả định đang sử dụng.

## Sự Cố Bảo Mật
Nếu nghi ngờ credential/dữ liệu bị xâm phạm:
- xoay vòng/thu hồi credential,
- hạn chế quyền truy cập,
- bảo toàn logs,
- đánh giá dữ liệu bị lộ,
- tuân theo quy trình thông báo hợp pháp/của tổ chức áp dụng.
