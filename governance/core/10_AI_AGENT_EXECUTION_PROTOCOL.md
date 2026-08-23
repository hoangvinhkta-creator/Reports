# 10 — AI Agent Execution Protocol

## Objective
Buộc thực hiện một quy trình làm việc kỷ luật cho Claude Code hoặc một AI coding agent khác.

# PHASE 1 — DISCOVER

Đọc các nội dung liên quan:
- hướng dẫn của repository,
- architecture,
- routes,
- schemas,
- security rules,
- business rules,
- implementation hiện có,
- tests.

CHƯA được sửa code.

Xuất ra (nội bộ hoặc trong task report):
- các file liên quan,
- hành vi hiện tại,
- pattern hiện có.

# PHASE 2 — ANALYZE

Xác định:

- module sở hữu (owning module),
- các module bị ảnh hưởng,
- các route bị ảnh hưởng,
- tác động đến data,
- tác động đến schema,
- tác động đến security,
- tác động đến API,
- tác động đến dependency,
- yêu cầu migration,
- rủi ro regression.

Không được giả định.

# PHASE 3 — DESIGN

Chọn implementation nhỏ nhất còn mạch lạc, tương thích với kiến trúc hiện có.

Định nghĩa:
- các file cần thay đổi,
- interfaces/contracts,
- validation,
- authorization,
- error behavior,
- test plan.

Không tự tạo ra một kiến trúc mới khi không cần thiết.

# PHASE 4 — IMPLEMENT

Quy tắc:
- giữ trong phạm vi đã định,
- tái sử dụng pattern hiện có,
- duy trì ranh giới layer,
- bảo toàn tính tương thích khi cần,
- không bypass security,
- không thêm refactor không liên quan.

# PHASE 5 — VERIFY

Chạy các kiểm tra áp dụng được:
- build,
- lint,
- typecheck,
- tests.

Xác minh thủ công/tự động:
- route,
- auth,
- permission,
- data behavior,
- error states,
- regression.

# PHASE 6 — REPORT

Báo cáo cuối cùng phải bao gồm:

## Summary
Những gì đã thay đổi.

## Files Changed
File + lý do.

## Architecture Impact
Không có / mô tả.

## Routing Impact
Không có / mô tả.

## Data Impact
Không có / mô tả.

## Security Impact
Không có / mô tả.

## Migration
Không có / các bước cần thiết.

## Verification
Các kiểm tra đã thực hiện và kết quả.

## Remaining Risks
Các vấn đề còn tồn đọng đã biết.

## Follow-up
Công việc tương lai tùy chọn, tách biệt rõ ràng khỏi task hiện tại.

# Important
Không bao giờ được tuyên bố hoàn thành chỉ vì code đã được viết.
Verification là một phần của implementation.
