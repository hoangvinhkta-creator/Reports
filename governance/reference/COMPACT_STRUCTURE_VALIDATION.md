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

Chạy lại tại thời điểm REM-T05 thực thi (không copy nguyên si baseline S007 —
xem bài học FIND-005 và "Ghi Chú" trong `docs/tasks/TASK-REM-T05-documentation-truth-up.md`).
Baseline S007 (2026-08-23) chụp ở trạng thái repo lúc đó; số liệu bên dưới
khác baseline vì Track Tín Phát và việc hợp nhất hai track (DEC-118) đã thêm
task/file/quyết định mới từ S007 tới nay — đúng như task đã cảnh báo trước.

### Structure
```bash
$ python3 governance/scripts/governance/validate_structure.py
GOVERNANCE STRUCTURE: PASS
Deployment root: PASS — /home/user/Reports
Checked 21 required paths.
```

### Project State
```bash
$ python3 governance/scripts/governance/validate_project_state.py
PROJECT STATE: PASS
```
Ghi chú: FAIL chỉ xảy ra trước khi S000 chọn profile thật cho dự án (chưa có
`Selected Profile` hợp lệ trong `PROJECT/PROJECT_PROFILE.md`/`PROJECT/PROJECT_PROGRESS.md`).
Ở trạng thái hiện tại, S000 của Track Tín Phát đã chọn profile PRODUCT, nên
kết quả đúng đắn là PASS, không phải FAIL.

### Task Completion
```bash
$ python3 governance/scripts/governance/validate_task_completion.py
TASK COMPLETION: PASS
Checked 4 DONE task(s).
```

### Evidence
```bash
$ python3 governance/scripts/governance/validate_evidence.py
EVIDENCE VALIDATION: PASS
Checked 19 REQUIRED PASS evidence record(s).
```

### Reference Integrity
```bash
$ python3 governance/scripts/governance/validate_reference_integrity.py
REFERENCE INTEGRITY: PASS
Quét 89 file .md (loại trừ 10 file trong governance/reference/history/, docs/audit/).
0 reference bị hỏng.
```

## Tính toàn vẹn tham chiếu tương đối trong repository

`validate_reference_integrity.py` quét mọi file `.md` được git track, tìm
reference `.md`/`.py`/`.svg` trong dấu backtick, và xác nhận từng reference
phân giải được thành file thật (từ ROOT, hoặc nếu không được thì từ thư mục
chứa file tham chiếu — xem docstring của script để biết đầy đủ quy tắc).

**Hai loại trừ tường minh áp dụng khi quét** (không phải bị bỏ sót ngầm —
khai báo trong chính script, biến `EXCLUDED_DIR_PREFIXES`):

1. `governance/reference/history/` — kho lưu trữ đã đóng băng (frozen
   archive). Không quét NỘI DUNG file trong thư mục này, vì đây là bản ghi
   lịch sử bất biến có thể chứa bare reference đã lỗi thời từ các phiên bản
   cũ (ví dụ FIND-011 —
   `governance/reference/history/CHANGELOG_V3_1.md` trích "PROJECT_PROFILE.md"
   không kèm đường dẫn đầy đủ). File khác tham chiếu VÀO thư mục này vẫn được kiểm
   tra bình thường.
2. `docs/audit/` — bản ghi audit bất biến, trích dẫn nguyên văn các token lỗi
   (ví dụ tên file trần trụi) làm bằng chứng lịch sử cho một finding đã đóng.
   Không quét nội dung file trong thư mục này vì sửa nó sẽ làm mất tính
   nguyên vẹn của bằng chứng đã ghi nhận.

Kết quả hiện tại: **0 reference bị hỏng** trên 89 file `.md` được quét (sau
khi áp dụng 2 loại trừ trên).
