# Task Ready Gate Standard

## Mục đích
Định nghĩa khi nào một task được phép bước vào giai đoạn triển khai (implementation).

## Nguyên tắc
Một task không được bắt đầu chỉ vì nó tồn tại trên roadmap.

## MICRO Ready Gate
Đối với các MICRO task đủ điều kiện, sử dụng `governance/templates/MICRO_TASK_CHECKLIST.md`.

Không được áp đặt toàn bộ Major Task Ready Gate lên các Micro Task.

## MAJOR Ready Gate

Yêu cầu trước khi READY:

- [ ] Objective rõ ràng.
- [ ] Scope đã được xác định.
- [ ] Out-of-scope đã được xác định.
- [ ] Các dependency đã DONE hoặc được miễn trừ (waived) một cách rõ ràng.
- [ ] Vùng tác động dự kiến (expected touch area) đã được xác định.
- [ ] Các yêu cầu liên quan đã được hiểu rõ.
- [ ] Tác động đến dữ liệu (data impact) đã được biết rõ.
- [ ] Tác động bảo mật (security impact) đã được biết rõ.
- [ ] Tác động routing/API đã được biết rõ khi liên quan.
- [ ] Các điều kiện tiên quyết cho migration đã sẵn sàng khi liên quan.
- [ ] Difficulty đã được chấm điểm.
- [ ] Risk đã được chấm điểm.
- [ ] Blast Radius đã được chấm điểm.
- [ ] Agent tier chính đã được chỉ định.
- [ ] Các escalation trigger đã được xác định.
- [ ] Completion Gate đã được hoàn thiện.
- [ ] Completion Gate đã được frozen trước khi triển khai.

## SPIKE / EXPLORATORY Ready Gate
Yêu cầu:
- [ ] Điều chưa biết/câu hỏi đã được nêu rõ ràng.
- [ ] Giả thuyết hoặc mục tiêu học hỏi (learning objective) đã được xác định.
- [ ] Scope/time-box đã được xác định.
- [ ] Phương pháp thu thập evidence đã được xác định.
- [ ] Không có tiêu chí nghiệm thu production nào bị ép buộc quá sớm.
- [ ] Định dạng output cho kết quả/khuyến nghị đã được xác định.

## Ready Status
- `PLANNED`
- `READY`
- `BLOCKED`

## Quy tắc
Một task không thể chuyển trực tiếp:

PLANNED
→ IN_PROGRESS

Nó phải chuyển qua:

PLANNED
→ READY
→ IN_PROGRESS
