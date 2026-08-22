# Agent Capability Matrix

## Purpose
Tránh hard-code việc lập kế hoạch dự án theo tên model có thể thay đổi theo thời gian.

Task nên được gán vào các capability tier trước, sau đó mới ánh xạ (map) sang các agent/model hiện đang khả dụng.

## Tier A — Lightweight
Phù hợp nhất cho:
- các chỉnh sửa nhỏ (trivial edits),
- cập nhật documentation,
- các thay đổi lặp lại có giới hạn,
- bổ sung test đơn giản,
- các sửa lỗi UI rủi ro thấp.

Ánh xạ hiện tại điển hình:
Haiku.

## Tier B — Implementation
Lựa chọn mặc định tốt nhất cho:
- CRUD,
- forms,
- routes,
- triển khai service,
- công việc API tiêu chuẩn,
- refactor có giới hạn,
- công việc test thông thường.

Ánh xạ hiện tại điển hình:
Sonnet.

## Tier C — Advanced Reasoning
Dùng cho:
- architecture,
- authentication/authorization,
- migration phức tạp,
- thay đổi dữ liệu rủi ro cao,
- refactor xuyên module,
- debugging khó,
- phân tích nguyên nhân gốc (root-cause analysis),
- sự cố production.

Ánh xạ hiện tại điển hình:
Opus.

## Tier D — Design / Creative
Dùng khi agent khả dụng được tối ưu hóa cho:
- khám phá UX,
- thiết kế trực quan,
- ý tưởng giao diện,
- xây dựng ý tưởng design-system,
- công việc trình bày nội dung chuyên sâu.

Ánh xạ hiện tại:
Tùy theo project. Định nghĩa trong S000 dựa trên năng lực agent thực tế đang khả dụng.

Không sử dụng một tier tập trung vào thiết kế làm thẩm quyền cuối cùng cho kiến trúc security/data.

## Scoring Inputs
Việc gán agent nên cân nhắc:

- Difficulty: 1–5
- Risk: 1–5
- Blast Radius: 1–5
- Ambiguity (mức độ mơ hồ)
- Security impact (tác động bảo mật)
- Data impact (tác động dữ liệu)
- Architecture impact (tác động kiến trúc)

## Escalation
Mỗi task nên định nghĩa:
- Primary Tier
- Escalation Tier
- Escalation triggers
