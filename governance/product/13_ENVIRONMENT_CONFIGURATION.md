# 13 — Environment & Configuration Management

## Mục tiêu
Ngăn chặn việc trộn lẫn ngoài ý muốn giữa các hệ thống development, staging, và production.

## Các Environment bắt buộc
Tối thiểu, production phải được tách biệt logic khỏi development.

Khuyến nghị:
- local
- development
- staging
- production

## Các quy tắc

### 1. Tài nguyên production phải có thể nhận diện được
Database, project, bucket, queue, API credentials, và domain của production không được để mơ hồ, khó phân biệt.

### 2. Development không được tùy tiện sử dụng dữ liệu production
Development/testing nên sử dụng:
- dữ liệu tổng hợp (synthetic data),
- dữ liệu test,
- dữ liệu đã được làm sạch (sanitized).

Không được copy dữ liệu khách hàng thật của production vào development mà không có một quy trình rõ ràng, được kiểm soát.

### 3. Secrets là riêng biệt theo từng environment
Credentials của DEV không được trùng với credentials của PROD ở những nơi có hỗ trợ tách biệt.

### 4. Không commit secrets
Các file như `.env` chứa secrets thật không được commit.

Có thể commit một file `.env.example` an toàn chỉ chứa placeholder.

### 5. Tập trung hóa configuration
Không được rải rác:
- API base URLs,
- tên environment,
- feature switches,
- các giới hạn (limits) quan trọng

khắp nơi trong implementation.

### 6. Fail an toàn khi thiếu configuration quan trọng
Không được âm thầm fallback về production hoặc một giá trị mặc định không an toàn.

### 7. Kiểm tra environment
Các thao tác chỉ dành riêng cho production nên xác thực rõ ràng environment đang hoạt động khi phù hợp.

### 8. Feature flags
Nếu sử dụng feature flags:
- xác định chủ sở hữu (ownership),
- xác định hành vi mặc định,
- gỡ bỏ các flag đã lỗi thời,
- không sử dụng flags như một kiến trúc vĩnh viễn.

### 9. Firebase / cloud projects
Khi áp dụng được, ưu tiên sử dụng project/resource riêng biệt cho:
- development/staging,
- production.

### 10. Tài liệu hóa configuration
Tài liệu hóa:
- các biến environment bắt buộc,
- mục đích,
- thuộc về client hay server,
- định dạng ví dụ,
- phân loại secret/non-secret.

## Deployment Safety Check (Kiểm tra an toàn trước khi deploy)
Trước khi deploy lên production, xác minh:
- project/account đích,
- các biến environment,
- database đích,
- storage đích,
- callback URLs,
- API base URL,
- feature flags,
- migrations.
