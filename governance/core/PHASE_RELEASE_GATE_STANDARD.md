# Phase & Release Gate Standard

## Mục đích
Việc một task riêng lẻ thành công không chứng minh rằng hệ thống đã tích hợp là khỏe mạnh.

## Các cấp Gate

### 1. Task Gate
Xác thực một Major Task.

### 2. Phase Gate
Xác thực rằng tất cả các task trong một phase hoạt động tốt cùng nhau.

### 3. Release Gate
Xác thực mức độ sẵn sàng cho production.

## Phase Gate
Chạy sau khi hoàn tất một tập hợp các task liên quan đã được xác định.

Các check điển hình:
- tất cả required task đã DONE;
- tích hợp liên module hoạt động đúng;
- các route vẫn hợp lệ;
- không có regression về authentication/authorization;
- các data contract vẫn tương thích;
- build pass;
- bộ test integration/regression pass;
- không còn hạng mục regression nghiêm trọng nào đang mở.

## Release Gate
Trước khi lên production, xác minh những điều sau khi phù hợp:
- các phase bắt buộc đã pass;
- migration đã sẵn sàng;
- backup/rollback đã được chuẩn bị;
- môi trường production đã được xác minh;
- secrets/config đã được xác minh;
- các check bảo mật quan trọng đã pass;
- release notes đã chuẩn bị xong;
- observability khả dụng;
- kế hoạch deployment rõ ràng;
- các check sau deploy đã được xác định.

## Quy tắc
Task DONE không có nghĩa là Phase DONE.
Phase DONE không có nghĩa là RELEASE READY.
