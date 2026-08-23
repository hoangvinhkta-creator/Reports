# S022 — TASK-110, Architecture Repair #2 sau Independent Review #6

## Metadata

Task:
TASK-110 — Validation + Review Queue

Current Task Mode:
MAJOR

Selected Profile:
PRODUCT

Ngày:
2026-08-23

Commit vào phiên:
`ed38fd6b9dc423826dcf1cb2a938debd19f2e7f1`

Trạng thái ra khỏi phiên:
**IMPLEMENTED. NOT MERGED. NOT DONE.** CHECK-110-16 tiếp tục **BLOCKED**.
**Còn một xung đột canonical đang chờ quyết định — xem cuối file.**

## Root Cause: root cause của chính bản sửa lần trước

Repair #1 (DEC-132) đóng đúng các *thể hiện* mà Review #5 chỉ ra, nhưng để lại
dạng *tổng quát*:

> Repair #1 thay giá trị sai bằng giá trị dẫn xuất, nhưng giữ nguyên
> **ENUMERATION** làm cơ chế cưỡng chế ở mọi biên — danh sách đen (4 khoá),
> chỉ số vị trí (`index`), danh sách trắng (9 trường oracle). Một liệt kê chỉ
> đầy đủ do may mắn, và cả sáu finding của Review #6 đều là một chỗ mà liệt kê
> thiếu.

Bốn nhánh: RC-1 invariant kiểm soát **văn bản** thay vì **cấu trúc**; RC-2
danh tính tường minh nhưng **không định phạm vi**; RC-3 luật một-biên-canonical
áp cho việc *chọn* record nhưng không áp cho việc *nạp*; RC-4 chính các oracle
chứng minh bản sửa cũng là liệt kê.

Audit tự tìm thêm hai defect Review #6 chưa nêu: group ma làm **dời tỉ lệ quy
đổi 2,0 % → 5,5 %** (nâng Finding 3 lên mức ảnh hưởng tiền lương), và
`employee_groups` không thuộc sở hữu của mapper nên `Validator` vẫn đọc
`employees.yaml` lần thứ hai.

## Ràng Buộc Cứng #0 — chứng minh được bằng git

Baseline L2 structural được chụp **trước dòng code sửa đầu tiên** và commit
riêng (`4ab3df0`): diff của commit đó trên `app/` và `tools/` là **rỗng**, nên
ảnh chụp chứng minh được là hành vi của `ed38fd6`, không phải của bản đã sửa.
L1 (`employee_resolve_matrix.json`) giữ **byte-identical** — bằng chứng đã đông
cứng, không sinh lại.

## Đã Làm

1. **INVARIANT P** — `ReviewItem` không còn lưu `dict[str, str]` nào.
   `Diagnostics` là dataclass có kiểu; `details` là projection lúc đọc, trả
   `MappingProxyType`. Không còn khoá nào để đặt, nên không cần danh sách đen.
2. **INVARIANT I** — bất biến **sâu**: `RowProvenance.rows`,
   `AmbiguousRow.records` bị ép tuple và **sao chép** ở biên
   (`object.__setattr__`), nên alias của caller bị cắt đứt.
3. **INVARIANT M** — `EmployeeMaster` là snapshot bất biến có `snapshot_id`
   dẫn từ nội dung; `RecordRef` mang `snapshot_id`; ref lạ raise
   `ForeignRecordRef`; `Validator.build_queue_for(working)` nhận nguyên bundle
   và so `snapshot_id`.
4. **INVARIANT C** — referential integrity `employee.group ∈ employee_groups`
   fail-fast tại loader (HD-110-09), kèm test canh lằn ranh một chiều: dữ liệu
   giao dịch hỏng vẫn vào Review Queue.
5. **INVARIANT L** — `load_employee_master()` là biên duy nhất; hai đường
   `load_yaml` thô trong `reconcile_conversion.py` được thay (HD-110-10, sửa
   tối thiểu: 13 thêm / 9 bớt, không đụng logic đối chiếu, không đụng vòng
   khớp prefix đã freeze).
6. **INVARIANT O** — oracle L2 dẫn xuất bằng `dataclasses.fields()`, phủ **66
   trường** (RawRow 21 + WorkingLine 35 + Order 10) thay cho 13 trường liệt kê
   tay; PII lưu digest. **Xoá** test tautology `..._covers_every_field_the_
   owner_named` — nó đối chiếu danh sách trắng với chính nó.

## Bằng Chứng Ra Khỏi Phiên

- `python3 -m pytest tests/ -q` → **340 passed, 2 failed**. Hai FAIL là xung
  đột canonical dưới đây, **không** phải lỗi triển khai.
- **L1** — 972 tổ hợp raw × as_of: **0 khác biệt**.
- **L2** — 66 trường, đầu-cuối: **0 khác biệt**.
- **L3** — config hợp lệ: 22/24 test reconciliation PASS (2 FAIL = xung đột).
- **P1–P4, M1–M3, C1–C3, L1/L3, O1–O3**: 36 test, tất cả PASS.
- `validate_reference_integrity` → còn đúng **3** reference hỏng, tất cả
  **PRE-EXISTING** của TASK-REM-T06; **0** reference hỏng mới.
- Module nghiệp vụ được bảo vệ: `sha256sum -c` → không file nào đổi.

## ⚠️ XUNG ĐỘT CANONICAL CÒN MỞ — cần Human Decision

**HD-110-09 (đã duyệt) va với ràng buộc #9 (MUST NOT CHANGE).**

Hai test trong `tests/test_reconcile_raw_integration.py` — một file thuộc diện
**MUST NOT CHANGE** — khẳng định rằng master data có group hỏng làm
`reconcile_raw` trả exit code **> 0**:

- `test_group_renamed_out_of_existence_fails`
- `test_declared_group_deleted_fails`

Sau HD-110-09, `EmployeeMapper.from_yaml` **raise `InvalidEmployeeConfig`**
trước khi đối chiếu chạy. Cấu hình hỏng **vẫn bị bắt, và bắt chặt hơn** — từ
chối trước khi xử lý thay vì báo cáo sau — nhưng cơ chế đã đổi, nên khẳng định
`_run(...) > 0` không còn đúng.

Phạm vi va chạm **hẹp và giải thích được**: đúng hai hàm test, cả hai đều về
đúng trường hợp group-reference mà HD-110-09 vừa chuyển sang fail-fast. **22/24
test còn lại của file đó vẫn PASS**, gồm cả `test_unmodified_config_passes_on_
the_fixture` — nên bằng chứng thật của CHECK-108A1-15 (output trên config hợp
lệ) **không đổi**.

Tôi **không** tự sửa hai test đó: đó là file MUST NOT CHANGE, và chủ dự án đã
dặn STOP khi gặp xung đột canonical mới.

## Bàn Giao

Trả lời xung đột trên, sau đó **Independent Review #7**. Không merge, không tự
chuyển DONE.
