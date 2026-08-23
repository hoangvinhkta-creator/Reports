# Governance Validators

Chạy từ thư mục gốc của repository (git root):

```bash
python3 governance/scripts/governance/validate_structure.py
python3 governance/scripts/governance/validate_project_state.py
python3 governance/scripts/governance/validate_task_completion.py
python3 governance/scripts/governance/validate_evidence.py
python3 governance/scripts/governance/validate_reference_integrity.py
```

Các script này cung cấp mức thực thi tối thiểu bằng máy (minimum machine
enforcement). Chúng KHÔNG thay thế cho:
- test thực tế,
- kiểm thử bảo mật,
- CI,
- rà soát bởi con người/rà soát độc lập.

## Danh sách validator

### `validate_structure.py`
Kiểm tra 21 đường dẫn bắt buộc của bộ khung governance có tồn tại, và (từ
REM-T03) xác nhận thêm rằng gốc mà script tự resolve được
(`Path(__file__).resolve().parents[3]`) trùng với git root thật — phát hiện
lớp lỗi từng gây ra FIND-001 (governance package bị deploy lồng trong một
thư mục con). Nếu không chạy trong một git repository, phần kiểm tra gốc báo
`NOT_APPLICABLE` (không phải `PASS`) thay vì bị bỏ qua âm thầm.

Không nhận tham số.

### `validate_project_state.py`
Kiểm tra `PROJECT/PROJECT_PROFILE.md` và `PROJECT/PROJECT_PROGRESS.md` có
`Selected Profile` / `Profile` / `Current Task Mode` hợp lệ theo các giá trị
enum đã định nghĩa (`SOLO_LITE`, `PRODUCT`, `TEAM_PRODUCTION`, `AUDIT` /
`MICRO`, `MAJOR`, `SPIKE`). Kỳ vọng FAIL trước khi S000 chạy xong — đó là
bình thường.

Không nhận tham số.

### `validate_task_completion.py`
Với mỗi file `docs/tasks/TASK-*.md` có `Status: DONE`, xác nhận task có ít
nhất một REQUIRED Completion Gate check, và mọi REQUIRED check đều ở trạng
thái `PASS` kèm `Evidence Level` + `Evidence` cụ thể (không phải placeholder
`...`).

Không nhận tham số.

### `validate_evidence.py`
Với mỗi REQUIRED check đã `PASS` trong `docs/tasks/TASK-*.md` của một task có
`Risk >= 3`, xác nhận `Evidence Level` là `E1` hoặc `E2` (không chấp nhận
`E0` cho check REQUIRED rủi ro cao), và có `Executed By` + `Timestamp` cụ
thể.

Không nhận tham số.

### `validate_reference_integrity.py`  *(mới — REM-T03)*
Quét mọi file `.md` dưới ROOT (git root tự phát hiện, hoặc thư mục truyền
vào) tìm các reference `.md`/`.py`/`.svg` được trích trong dấu backtick, và
xác nhận từng reference resolve được thành một file thật — thử từ ROOT
trước, sau đó từ thư mục chứa file đang tham chiếu; chỉ coi là hỏng khi cả
hai đều không resolve được.

Loại trừ khỏi việc quét:
- `governance/reference/history/` — kho lưu trữ đã đóng băng (FIND-011).
- `docs/audit/` — bản ghi audit bất biến, trích dẫn nguyên văn token lỗi làm
  bằng chứng lịch sử.
- Reference chứa `*` (glob pattern).
- Một allowlist nhỏ theo từng cặp (file nguồn, reference) chính xác cho các
  trường hợp trích dẫn token lỗi lịch sử hoặc forward-reference tới file mà
  một task PLANNED/READY sẽ tạo — xem `KNOWN_EXEMPT_PAIRS` trong file script
  và DEC-012/DEC-013 trong `PROJECT/PROJECT_DECISIONS.md`.

**Giới hạn đã biết:** chỉ bắt reference có phần mở rộng `.md`/`.py`/`.svg`,
không bắt reference dạng thư mục (ví dụ `` `templates/` ``). Đã thử mở rộng
sang dạng thư mục nhưng gây 20 false positive trên repo hiện tại (đa số là
ví dụ minh họa trong văn xuôi, không phải reference sống thật) — xem
DEC-013.

Usage:
```bash
python3 governance/scripts/governance/validate_reference_integrity.py [ROOT_DIR]
```
Không truyền `ROOT_DIR`: tự phát hiện git root. Truyền `ROOT_DIR`: quét thư
mục đó thay thế — dùng để test lại trên một git worktree checkout tại một
commit lịch sử (xem `fixtures/`).

### `validate_refactor_preservation.py`
So sánh nội dung file governance giữa cấu trúc hiện tại (compact) và một bản
sao ở cấu trúc phi-compact V3.2 FINAL, để xác nhận một lần tái cấu trúc thư
mục không vô tình viết lại/rút gọn/xóa ngữ nghĩa governance.

**Bắt buộc một tham số vị trí** — thư mục gốc của bản không-compact để so
sánh:
```bash
python3 governance/scripts/governance/validate_refactor_preservation.py <non-compact-v3.2-final-dir>
```
Chạy không kèm tham số sẽ in usage và exit 2. Chỉ có ý nghĩa khi đang thực
hiện một lần tái cấu trúc thư mục có bản đối chiếu; bỏ qua trong các lần
chạy thông thường (CI báo cáo việc bỏ qua này tường minh, không âm thầm —
xem `.github/workflows/governance.yml`).

## Fixtures / Regression tests

### `fixtures/regression_nested_layout.py`
Regression test cho phần kiểm tra deployment-root của `validate_structure.py`
(CHECK-T03-01, TASK-REM-T03). Tự tạo một bản sao `validate_structure.py`
trong một cây thư mục tạm giả lập layout lồng (loại lỗi đã gây ra FIND-001),
chạy nó như subprocess, và xác nhận nó FAIL với thông báo rõ ràng nêu tên gốc
kỳ vọng — chứ không chỉ FAIL vì thiếu required path.

```bash
python3 governance/scripts/governance/fixtures/regression_nested_layout.py
```
