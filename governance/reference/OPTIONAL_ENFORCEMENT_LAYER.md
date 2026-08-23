# Lớp thực thi tùy chọn (Optional Enforcement Layer)

## Các Validator đi kèm

V3.2 Final đi kèm các validator có thể thực thi được:

```bash
python governance/scripts/governance/validate_structure.py
python governance/scripts/governance/validate_project_state.py
python governance/scripts/governance/validate_task_completion.py
python governance/scripts/governance/validate_evidence.py
```

## Những gì chúng thực thi

### validate_structure.py
Kiểm tra các đường dẫn governance bắt buộc có tồn tại hay không.

### validate_project_state.py
Kiểm tra ngữ nghĩa các giá trị profile của dự án:
- Selected Profile phải là một trong các profile được phép.
- Progress Profile phải hợp lệ.
- Current Task Mode, khi được điền, phải là MICRO / MAJOR / SPIKE.

### validate_task_completion.py
Đối với các task file có `Status: DONE`:
- Các check REQUIRED không được là FAIL / BLOCKED / NOT_TESTED.
- Các check REQUIRED PASS phải bao gồm Evidence Level.
- Các check REQUIRED PASS phải bao gồm Evidence cụ thể.

### validate_evidence.py
Đối với các check REQUIRED PASS:
- Risk >= 3 yêu cầu E1/E2.
- E1/E2 yêu cầu Executed By.
- E1/E2 yêu cầu Timestamp.

## Tích hợp CI

TEAM_PRODUCTION:
Chạy tất cả các validator trong CI khi khả thi.

PRODUCT:
Khuyến nghị chạy ít nhất trước Phase/Release Gate.

SOLO_LITE:
Chạy thủ công khi cần thiết.

AUDIT:
Việc kiểm tra structure/state hữu ích; các validator completion áp dụng khi các task khắc phục (remediation) bắt đầu.

## Nguyên tắc

Việc thực thi bằng máy chỉ bổ sung cho governance; nó không thay thế cho các bài test thực tế hay đánh giá độc lập.
