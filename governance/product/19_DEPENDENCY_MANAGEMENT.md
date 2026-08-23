# 19 — Quy Tắc Quản Lý Dependency

## Mục Tiêu
Ngăn ngừa các dependency không cần thiết, không an toàn, không còn được duy trì, hoặc xung đột.

## Trước Khi Thêm Một Dependency
Kiểm tra:
1. Đã có chức năng tương đương chưa?
2. Nền tảng/thư viện native có thể giải quyết an toàn không?
3. Package có đang được duy trì tích cực không?
4. License của nó có chấp nhận được không?
5. Nó có gây ra rủi ro bảo mật đã biết không?
6. Chi phí bundle/runtime của nó có hợp lý không?
7. Nó có tạo ra vendor lock-in hoặc coupling kiến trúc không?

## Quy Tắc

### 1. Sử dụng lockfile
Commit lockfile phù hợp.

### 2. Tránh trùng lặp thư viện
Không cài nhiều package cùng giải quyết một vấn đề mà không có lý do chính đáng.

### 3. Pin/giới hạn phiên bản phù hợp
Tuân theo best practice của hệ sinh thái.

### 4. Cập nhật bảo mật
Thường xuyên rà soát lỗ hổng của dependency.

### 5. Nâng cấp phiên bản lớn (Major upgrade)
Nâng cấp major version yêu cầu:
- đánh giá tương thích,
- ghi chú migration,
- tests.

### 6. Loại bỏ dependency không sử dụng
Không giữ lại các package không còn consumer hợp lệ.

### 7. Yêu Cầu Đối Với AI Agent
Trước khi chạy lệnh install, báo cáo:
- package,
- mục đích,
- các phương án thay thế đã kiểm tra,
- tác động dự kiến.

## Báo Cáo Thay Đổi Dependency
Đối với các thay đổi dependency quan trọng, cần tài liệu hóa:
- phiên bản cũ,
- phiên bản mới,
- breaking changes,
- migration,
- xác minh (verification).
