# 14 — CI/CD & Release Rules

## Mục tiêu
Làm cho các thay đổi trên production trở nên có thể lặp lại (repeatable), có thể kiểm thử được, có thể review được, và có thể đảo ngược được.

## Delivery Flow được khuyến nghị

feature branch
→ pull request
→ automated checks
→ review
→ preview/staging
→ approval
→ production
→ post-deploy verification

## Các quy tắc bắt buộc

### 1. Không được xem thành công ở local là sẵn sàng release
Việc deploy lên production đòi hỏi phải có xác minh phù hợp.

### 2. Automated checks
Ở nơi được hỗ trợ, CI nên chạy:
- cài đặt dependency bằng lockfile,
- lint,
- typecheck,
- unit/integration tests,
- production build,
- security/dependency checks khi đã được cấu hình.

### 3. Bảo vệ production branch
Tránh việc commit trực tiếp không kiểm soát vào production branch.

### 4. Deploy lên production
Các thay đổi rủi ro cao không nên được AI agent deploy trực tiếp mà không qua quy trình phê duyệt bắt buộc của dự án.

### 5. Database migrations
Migrations phải được phối hợp với thứ tự deployment.

Ưu tiên các trình tự deployment tương thích ngược (backward-compatible).

### 6. Release notes
Các release quan trọng nên được tài liệu hóa:
- tính năng (features),
- các bản sửa lỗi (fixes),
- migrations,
- các thay đổi bảo mật,
- các giới hạn đã biết (known limitations).

### 7. Rollback
Trước khi release rủi ro cao, xác định:
- phương pháp rollback code,
- khả năng tương thích của database,
- các thao tác không thể đảo ngược,
- phương án dự phòng bằng feature flag nếu có.

### 8. Post-deployment verification (Xác minh sau khi deploy)
Xác minh các luồng quan trọng sau khi deploy.

Ví dụ:
- đăng nhập (login),
- dashboard chính,
- các thao tác CRUD quan trọng,
- phân quyền,
- các tích hợp then chốt.

### 9. Deployment thất bại
Không được liên tục vá lỗi (patch) production một cách mù quáng.

Dừng lại, kiểm tra giai đoạn bị lỗi, và xác định nên:
- rollback,
- fix forward (sửa tiếp lên phía trước),
- vô hiệu hóa feature bị ảnh hưởng.

## Các mức độ rủi ro của Release

### Low (Thấp)
Thay đổi UI/text không có ảnh hưởng đến data/security.

### Medium (Trung bình)
Feature bình thường có ảnh hưởng data/API trong phạm vi giới hạn.

### High (Cao)
Bao gồm:
- auth (xác thực),
- authorization (phân quyền),
- billing (thanh toán),
- pricing (định giá),
- bulk mutation (thay đổi dữ liệu hàng loạt),
- schema migration,
- deletion (xóa dữ liệu),
- hạ tầng production.

Các thay đổi rủi ro cao đòi hỏi review chặt chẽ hơn và chuẩn bị phương án rollback.
