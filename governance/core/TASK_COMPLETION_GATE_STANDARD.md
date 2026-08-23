# Task Completion Gate Standard

## Mục đích
Định nghĩa cách mỗi task chứng minh rằng nó đã được hoàn thành đúng đắn.

## Quy tắc cốt lõi
CODE COMPLETE ≠ TASK COMPLETE.

Một task chỉ DONE khi:
- tất cả các REQUIRED check đều PASS,
- required evidence level được thỏa mãn,
- Exit Criteria được thỏa mãn.

## Liên kết Evidence bắt buộc
Mỗi check trong Completion Gate phải tuân theo `governance/core/EVIDENCE_STANDARD.md`.

Một PASS mà không có evidence level yêu cầu thì không phải là một PASS hợp lệ.

Nếu một check chưa thực sự được thực thi:
Status = NOT_TESTED.

## Thời điểm tạo Gate

### Trong S000 / Planning
Tạo trước các Completion Gate sơ bộ cho các task trong tương lai.

### Trước khi Task chuyển sang READY
Rà soát và hoàn thiện gate dựa trên hiểu biết hiện tại về project.

### Sau khi Freeze
Agent không được xóa bỏ hoặc làm suy yếu các REQUIRED check chỉ để khiến task pass.

## Task Mode

### MICRO
Sử dụng `governance/templates/MICRO_TASK_CHECKLIST.md`.

### MAJOR
Sử dụng cấu trúc gate đầy đủ bên dưới.

### SPIKE / EXPLORATORY
Gate tập trung vào kết quả học hỏi (learning outcomes), evidence, các ràng buộc đã phát hiện, các phương án thay thế đã so sánh, và khuyến nghị được đưa ra.

## Danh mục Check
Chỉ sử dụng các danh mục liên quan đến task:

- Functional
- Architecture
- Data
- Security
- Routing
- API
- UI/UX
- Accessibility
- Performance
- Reliability
- Error Handling
- Migration
- Backward Compatibility
- Testing
- Regression
- Documentation
- Observability
- Deployment
- Audit
- Backup / Rollback

## Mức độ ưu tiên của Check
Mỗi check có mức:

- REQUIRED
- RECOMMENDED
- OPTIONAL

Bất kỳ REQUIRED check nào là FAIL, BLOCKED, hoặc NOT_TESTED đều ngăn task đạt DONE, trừ khi được đánh dấu rõ ràng là NOT_APPLICABLE kèm lý do hợp lệ.

## Trạng thái Check
- NOT_TESTED
- PASS
- FAIL
- BLOCKED
- NOT_APPLICABLE

## Evidence Record
Mỗi check quan trọng phải bao gồm:

Check ID:
...

Priority:
...

Status:
...

Evidence Level:
E0 / E1 / E2

Evidence:
...

Executed By:
...

Timestamp:
...

## Evidence dựa theo Risk
Tuân theo `governance/core/EVIDENCE_STANDARD.md`.

Tóm tắt:
- Risk 1–2: E0/E1 tùy theo check.
- Risk 3: E1 bắt buộc cho các REQUIRED check có thể thực thi được.
- Risk 4–5: E1 bắt buộc; các check liên quan bảo mật/dữ liệu quan trọng nên tìm cách đạt E2.

## Exit Criteria
Các exit criteria điển hình:

1. 100% REQUIRED check PASS.
2. Required evidence level được thỏa mãn.
3. 0 lỗi nghiêm trọng (critical defect) chưa được giải quyết.
4. 0 required security failure chưa được giải quyết.
5. Các check build/type/lint liên quan đều PASS.
6. Các check regression liên quan đều PASS.
7. Tài liệu bắt buộc đã được cập nhật.
8. `PROJECT/PROJECT_PROGRESS.md` đã được cập nhật.
9. Session handoff đã được viết khi task mode yêu cầu.

## Kiểm soát thay đổi Gate
Sử dụng:

COMPLETION GATE CHANGE PROPOSAL

Original check:
...

Proposed change:
...

Reason:
...

Risk:
...

Impact:
...

Không được âm thầm hạ thấp tiêu chí chất lượng.
