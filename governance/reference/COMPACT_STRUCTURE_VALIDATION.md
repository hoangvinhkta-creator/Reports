# XÁC THỰC CẤU TRÚC COMPACT (COMPACT STRUCTURE VALIDATION)

## Thiết kế Root

Các mục ở root liên quan đến governance:
- `CLAUDE.md`
- `PROJECT/`
- `docs/`
- `governance/`

Số standard governance ở cấp root:
0

Chỉ còn `CLAUDE.md` là điểm vào (entry point) governance ở root.

## An toàn "đọc trước khi làm việc"

Cấu trúc compact vẫn bảo toàn hành vi đọc bắt buộc.

### S000
`CLAUDE.md` điều hướng agent đến:
1. `governance/core/PROJECT_PROFILE_STANDARD.md`
2. `governance/core/RULE_PRECEDENCE.md`
3. `governance/core/TASK_MODE_STANDARD.md`
4. `governance/core/00_SESSION_ORCHESTRATION.md`

### Phiên làm việc Major Task thông thường
Agent đọc:
1. `PROJECT/PROJECT_PROFILE.md`
2. `PROJECT/PROJECT_PROGRESS.md`
3. task hiện tại dưới `docs/tasks/`
4. chỉ các file governance áp dụng được
5. Ready Gate trước khi code

### Câu hỏi chỉ về tiến độ (Progress-only)
Agent đọc:
`PROJECT/PROJECT_PROGRESS.md`
trước tiên.

### Audit
Profile AUDIT được chọn sẽ điều hướng rõ ràng đến các rule core/product/audit bắt buộc.

Do đó, việc di chuyển các rule tĩnh vào dưới `governance/` không làm suy yếu các yêu cầu đọc-trước-khi-làm-việc.

## Kết quả Validator

### Structure
```text
GOVERNANCE STRUCTURE: PASS
Checked 21 required paths.
```

### Project State
Kỳ vọng FAIL trước khi chạy S000 vì chưa có profile thực sự nào được chọn.
```text
PROJECT STATE: FAIL
- PROJECT/PROJECT_PROFILE.md must contain a valid Selected Profile: AUDIT, PRODUCT, SOLO_LITE, TEAM_PRODUCTION
- PROJECT_PROGRESS.md must contain a valid Profile value: AUDIT, PRODUCT, SOLO_LITE, TEAM_PRODUCTION
```

### Task Completion
```text
TASK COMPLETION: PASS
Checked 0 DONE task(s).
```

### Evidence
```text
EVIDENCE VALIDATION: PASS
Checked 0 REQUIRED PASS evidence record(s).
```

## Tính toàn vẹn tham chiếu tương đối trong repository

Số tham chiếu canonical path bị hỏng: 0

PASS — không phát hiện tham chiếu canonical repository-relative `.md`/`.py`/`.svg` nào bị hỏng.
