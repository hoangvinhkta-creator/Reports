# Checklist Task MICRO (Micro Task Checklist)

Chỉ sử dụng khi task thỏa điều kiện đủ tiêu chuẩn cho chế độ MICRO theo `governance/core/TASK_MODE_STANDARD.md`.

## Ready Gate Rút Gọn (Compact Ready Gate)
- [ ] Yêu cầu/lỗi đã rõ ràng đủ để bắt tay vào làm.
- [ ] Risk <= 2.
- [ ] Blast Radius <= 2.
- [ ] Không có thay đổi về architecture/auth/schema/dữ liệu mang tính phá hủy.
- [ ] Phạm vi tác động dự kiến hẹp và đã biết rõ.
- [ ] Phương pháp xác minh liên quan đã được xác định.

## Completion Gate Rút Gọn (Compact Completion Gate)
- [ ] Hành vi dự kiến đã được triển khai.
- [ ] Việc build/test/xác minh thủ công liên quan đã thực sự được thực thi.
- [ ] Evidence được ghi nhận theo `governance/core/EVIDENCE_STANDARD.md`.
- [ ] Không xảy ra mở rộng phạm vi ngoài dự kiến.
- [ ] Kiểm tra regression liên quan đã PASS.
- [ ] Mục Micro Task inline trong `PROJECT/PROJECT_PROGRESS.md` đã được cập nhật.

## Quy Tắc Thoát (Exit Rule)
Nếu xuất hiện bất kỳ điều nào sau đây, DỪNG việc coi công việc này là MICRO và nâng cấp lên MAJOR:
- Risk > 2
- Blast Radius > 2
- có tác động đến architecture
- có tác động đến authorization/security
- migration schema đã persist
- thao tác dữ liệu mang tính phá hủy
- thiết kế lại xuyên nhiều module (cross-module redesign)
