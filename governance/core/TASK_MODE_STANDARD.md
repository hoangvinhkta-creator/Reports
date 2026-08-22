# Task Mode Standard

## Mục đích
Điều chỉnh mức độ overhead của quy trình tương xứng với quy mô, rủi ro, và mức độ không chắc chắn thực tế của công việc.

## Mode 1 — MICRO TASK

Chỉ đủ điều kiện khi TẤT CẢ các điều sau đều đúng:
- Difficulty <= 2
- Risk <= 2
- Blast Radius <= 2
- Không có thay đổi kiến trúc
- Không có thay đổi auth/authorization
- Không có migration schema đã persist
- Không có thao tác dữ liệu mang tính hủy hoại (destructive)
- Không có tác động bảo mật rủi ro cao
- Không có thiết kế lại liên module

Ví dụ:
- lỗi UI nhỏ,
- sửa nhãn/văn bản,
- lỗi tính toán cục bộ,
- sửa CSS nhỏ,
- sửa test đơn giản.

Quy trình:
- Theo dõi trực tiếp (inline) trong `PROJECT/PROJECT_PROGRESS.md`.
- Sử dụng checklist Ready/Completion rút gọn.
- File task riêng và session handoff riêng là tùy chọn, trừ khi công việc mở rộng.

Nếu scope/risk tăng lên, nâng cấp thành MAJOR TASK.

## Mode 2 — MAJOR TASK

Sử dụng cho:
- tính năng thông thường,
- thay đổi module,
- refactor có giới hạn (bounded),
- thay đổi routing,
- thay đổi database/API,
- công việc có rủi ro trung bình/cao.

Yêu cầu:
- file định nghĩa task,
- session riêng biệt,
- Ready Gate,
- Completion Gate đã frozen,
- session handoff.

## Mode 3 — SPIKE / EXPLORATORY

Sử dụng khi giải pháp đúng hoặc mục tiêu nghiệm thu chưa được biết trước.

Ví dụ:
- khả thi về mặt kỹ thuật,
- prototype,
- khám phá cơ chế game (game mechanic),
- thử nghiệm UX,
- hành vi chưa rõ của library/tích hợp.

Mục tiêu:
Giảm mức độ không chắc chắn, không phải để đạt tới sự hoàn thiện production.

Completion Gate nên xác thực việc học hỏi:
- giả thuyết đã được kiểm chứng,
- các phương án thay thế đã được so sánh,
- các ràng buộc đã được phát hiện,
- prototype đã được tạo ra nếu hữu ích,
- evidence đã được ghi lại,
- khuyến nghị đã được ghi thành tài liệu,
- task triển khai tiếp theo đã được xác định nếu phù hợp.

KHÔNG được ép buộc tiêu chí nghiệm thu triển khai cuối cùng trước khi giai đoạn khám phá (discovery) hoàn tất.

## Quy tắc nâng cấp (Promotion)

MICRO → MAJOR nếu:
- Risk > 2,
- Blast Radius > 2,
- xuất hiện tác động về kiến trúc/bảo mật/dữ liệu,
- xuất hiện các dependency ngoài dự kiến.

SPIKE → MAJOR sau khi:
- mức độ không chắc chắn đã giảm,
- hướng triển khai đã được chọn,
- các yêu cầu có thể được hoàn thiện (finalize).
