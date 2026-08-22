# BÁO CÁO SỬA LỖI HỒI QUY COMPACT (COMPACT REGRESSION FIX REPORT)

## F-14 — PROJECT_PROFILE_STANDARD

Số từ nguồn: 358
Số từ Compact: 358

Status:
PASS

File Compact được khôi phục từ nguồn chuẩn (source-of-truth) của V3.2 Final và chỉ có các đường dẫn canonical là được thay đổi.

Các section bắt buộc được khôi phục, đã kiểm tra thủ công/bảo toàn nguồn:
- Profile Selection Inputs
- Use for
- Ceremony
- Runtime Record fields / justification

## F-15 — CLAUDE.md

Số từ nguồn: 531
Số từ Compact: 600

Sự khác biệt là do ghi chú `Compact Directory Layout` được thêm có chủ đích.
Nội dung ngữ nghĩa gốc được giữ nguyên với các đường dẫn được thay thế.

Các cơ chế đã được xác minh:
- Toàn bộ Task Lifecycle có mặt đầy đủ
- BLOCKED / DEFERRED / CANCELLED có mặt
- CONFLICT DETECTED có mặt

## F-10 — Empty Completion Gate Fixture

Fixture:
- Status: DONE
- Risk: 5/5
- Completion Gate: rỗng

Expected:
FAIL

Actual:
```text
TASK COMPLETION: FAIL
- TASK-F10-FIXTURE.md: Status=DONE but no REQUIRED Completion Gate checks were found.
```

Kết quả regression test:
PASS

## Validators

### Structure
```text
GOVERNANCE STRUCTURE: PASS
Checked 21 required paths.
```

### Project State
Kỳ vọng FAIL trước khi chạy S000:
```text
PROJECT STATE: FAIL
- PROJECT/PROJECT_PROFILE.md must contain a valid Selected Profile: AUDIT, PRODUCT, SOLO_LITE, TEAM_PRODUCTION
- PROJECT_PROGRESS.md must contain a valid Profile value: AUDIT, PRODUCT, SOLO_LITE, TEAM_PRODUCTION
```

### Task Completion (package thông thường)
```text
TASK COMPLETION: PASS
Checked 0 DONE task(s).
```

### Evidence
```text
EVIDENCE VALIDATION: PASS
Checked 0 REQUIRED PASS evidence record(s).
```

### Refactor Preservation
```text
PRESERVATION: PASS
Profile selection content preserved; lifecycle/conflict mechanisms present.
```

## Quy tắc Refactor về sau

Việc tái cấu trúc thư mục thuần túy chỉ được thay đổi đường dẫn.

Không được tóm tắt hoặc viết lại nội dung governance trong lúc di chuyển.
Các thay đổi ngữ nghĩa phải được khai báo riêng và có regression test kèm theo.
