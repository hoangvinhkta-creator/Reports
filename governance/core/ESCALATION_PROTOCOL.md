# Escalation Protocol

## Mục đích
Ngăn việc vá lỗi lặp đi lặp lại và bắt buộc rà soát nguyên nhân gốc khi một task vượt quá năng lực agent/session hiện tại.

## Escalation Triggers
Escalate khi xảy ra bất kỳ điều nào sau đây:

- hai lần thử triển khai khác biệt về bản chất đều thất bại;
- phát hiện xung đột kiến trúc;
- hành vi bảo mật không rõ ràng;
- xuất hiện rủi ro migration/mất dữ liệu ngoài dự kiến;
- scope phải mở rộng qua nhiều module lớn;
- required completion gate không thể được thỏa mãn một cách an toàn;
- regression lan rộng vượt quá Blast Radius dự kiến;
- hành vi ở production khác biệt đáng kể so với các giả định đã được tài liệu hóa.

## Hành động bắt buộc

STOP IMPLEMENTATION
→ bảo toàn evidence
→ ghi lại blocker
→ thực hiện rà soát nguyên nhân gốc
→ escalate agent tier / architecture review
→ cập nhật kế hoạch nếu cần

## Hành vi bị cấm
Không được:
- tiếp tục chồng thêm các bản sửa mang tính suy đoán;
- vô hiệu hóa các check đang fail;
- làm suy yếu Completion Gate;
- mở rộng scope một cách âm thầm;
- thực hiện các refactor không liên quan.

## Escalation Record

Reason:
...

Attempts made:
...

Observed evidence:
...

Suspected root cause:
...

Affected scope:
...

Recommended agent tier:
...

Recommended next action:
...
