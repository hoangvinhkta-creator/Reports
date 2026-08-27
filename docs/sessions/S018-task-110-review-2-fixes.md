# BÀN GIAO SESSION (SESSION HANDOFF)

Session ID:
S018

Task:
TASK-110 — Validation + Review Queue (**sửa Independent Review #2**)

Task Mode:
MAJOR

Project Profile:
PRODUCT

Status:
**IMPLEMENTED — repair after Independent Review #2. Chưa merge. Chưa DONE.**
Review #2 trên commit `01ff25f`: **FAIL, 4 finding** — đã sửa **4/4**. Không
phát sinh Human Decision mới. **271/271 test PASS** (120 mới so với baseline
`c7a1b24`, 0 regression). 16/17 REQUIRED check PASS; CHECK-110-16 giữ
**BLOCKED**. Chờ **Independent Review #3**.

## Kết Quả (Result)

Hai trong bốn finding là lỗi thật **nằm trong chính các bản sửa của vòng #1**.
Cả hai đã được **tái hiện bằng script trước khi sửa**, để bản sửa nhắm vào
hành vi thật chứ không vào cách tôi hình dung về nó.

### Finding 1 — `employee_raw` rỗng không được tham gia F4

**Tái hiện (trước khi sửa):** batch có 1 dòng mapped + 2 dòng `employee_raw`
rỗng →

```
F4 scope=batch row=None n=2 details={'criterion': 'F4',
    'dataset_range': '2026-01-15..2026-01-15', 'batch_rows': '3'}
```

Không raw identity, không dòng nguồn, `scope=batch`. Đúng loại mục mà Finding
1 của vòng #1 tồn tại để chặn — lọt qua ở một nhánh khác: dòng rỗng rơi vào
`unmapped[""]`, và khóa `""` là falsy nên `_mapping_item` không tìm được rows.

**Sửa:** vòng F4 trong `evaluate_raw_mapping` bỏ qua raw value rỗng. Một dòng
không có `NVBH` **không có danh tính** để master data thiếu — nó đã được báo
đầy đủ ở `Missing.employee`.

**Không đụng script phân tích:** `reconcile_conversion.py` vốn `continue` trên
dòng không có `NVBH` trước khi đếm, nên nó chưa bao giờ có khóa rỗng.

**Test:** `test_blank_employee_produces_only_missing_and_never_an_f4` (ba dạng
rỗng `None` / `""` / `"   "` → **0** mục F4, **3** mục `Missing.employee`),
`test_a_real_unmapped_identity_still_raises_a_fully_traceable_f4` (**đúng 1**
mục, không có bản sao sinh từ khóa rỗng; `source_rows="11, 14"`,
`affected_count == 2`, `raw_value` đầy đủ),
`test_blank_rows_do_not_inflate_the_f4_threshold_either` (20 dòng rỗng → vẫn
0 mục F4).

### Finding 2 — F6 phải chấm theo effective dating

**Tái hiện (trước khi sửa):** hai bản ghi cùng `normalized = "Ly"` — bản cũ
`active: false`, `effective_to: 2026-03-31`; bản mới `active: true`,
`effective_from: 2026-04-01`. Hai dòng ngày tháng 5:

```
status production mapper cho 2 dòng tháng 5: {'mapped'}
F6 :: F6 — 'Ly' khai `active: false` nhưng vẫn có 2 dòng trong kỳ...
```

Production mapper nói **mapped**, F6 vẫn kêu. Nguyên nhân: F6 gộp theo *tên*
rồi áp một boolean `active` cho mọi bản ghi cùng tên. Một bàn giao (DEC-121)
**cố ý** dùng lại tên, nên bản ghi đã đóng mượn giao dịch của bản ghi đang
chạy.

**Sửa:** `evaluate_inactive_records()` mới trong
`app/modules/validation/employee_mapping.py`:

- `select_effective_record(rows, employee_raw, when)` — **cùng semantics**
  `EmployeeMapper.resolve`: lọc `effective_rows` theo **ngày của chính dòng
  đó** → khớp prefix trên chuỗi raw (không chuẩn hóa, y như production) →
  prefix dài nhất thắng.
- Gom theo **bản ghi** (`_record_key` = normalized + raw_prefix + cửa sổ hiệu
  lực), **không** theo tên.
- `MappingFinding.source_rows` mới: F6 mang theo dòng của chính nó, nên
  `_mapping_item` không tra ngược theo tên nữa.

**Hệ quả phụ có lợi:** F6 rời khỏi `evaluate_raw_mapping`, nên hàm dùng chung
với script phân tích **trở lại đúng bộ F1–F5** như bản đã ký ở CHECK-108A1-15.
Script không thể sinh F6 kể cả trên master data mâu thuẫn — CHECK-110-14 nay
mạnh hơn trước.

**Test bắt buộc theo yêu cầu review, đủ cả bốn:**
`test_a_closed_record_never_borrows_the_active_record_s_transactions` (dòng kỳ
mới → mapper `mapped`, **0** F6),
`test_rows_inside_the_inactive_record_s_own_window_do_raise_f6` (dòng kỳ cũ →
`inactive`, 1 F6, `source_rows="6, 8"`, message nêu rõ cửa sổ
`2026-01-01..2026-03-31`),
`test_a_batch_spanning_both_windows_attributes_each_row_to_its_own_record`
(cùng batch 3 dòng 2 cửa sổ → chỉ 2 dòng kỳ cũ được tính),
`test_two_inactive_records_sharing_a_name_are_reported_separately`.

Thêm `test_f6_record_selection_agrees_with_the_production_employee_mapper` —
8 case đối chiếu trực tiếp với `EmployeeMapper` thật. Một bản đọc thứ hai của
một rule chỉ an toàn khi có thứ **chứng minh** hai bên khớp, không phải khi
tôi tin là chúng khớp. Và `test_f6_never_changes_mapping_status_or_group`:
KPI/conversion không đổi.

### Finding 3 — Đồng bộ mô tả trạng thái hiện tại

**Vấn đề:** `PROJECT/PROJECT_PROGRESS.md` → "Trạng thái Task hiện tại" vẫn
ghi `PLANNED`, *"mục duy nhất còn thiếu là chủ dự án freeze Completion Gate"*,
*"Chưa viết dòng code nào"* — trong khi Gate đã freeze và code đã xong hai
vòng trước. Khối `Required Gate Progress` còn ghi `83/83 test`.

**Sửa:** mọi artifact current-state nay nói cùng một điều —
`IMPLEMENTED — repair after Independent Review #2`, **chưa merge, chưa DONE,
CHECK-110-16 BLOCKED**: `PROJECT/PROJECT_PROGRESS.md` (Current Task, Trạng thái Task
hiện tại, Required Gate Progress, Last Updated, Next Recommended Task, bullet
roadmap, hai chỗ TD-001), `docs/tasks/TASK-110-*.md` (Status),
`PROJECT/LO_TRINH_DE_HIEU.md`.

**Lịch sử không bị sửa.** Ba mục "Có gì mới" cũ về bước 14 trong
`PROJECT/LO_TRINH_DE_HIEU.md` chỉ được **gắn nhãn** `Ghi chép cũ (đã bị mục trên thay
thế)` kèm một dòng chỉ về mục hiện tại. Nội dung giữ nguyên. Handoff S015/S016/
S017 không đụng tới.

### Finding 4 — Oracle non-mutation chụp sai thời điểm

**Vấn đề:** test gọi `run_import()` — vốn **đã dựng queue một lần bên trong**
— rồi mới chụp ảnh "trước". Một mutation do lần chạy đó gây ra sẽ nằm sẵn ở
**cả hai** phía, và phép so luôn PASS. Oracle vô hiệu đúng trong kịch bản nó
tồn tại để bắt.

**Sửa:** `app/pipeline.py` tách `build_working_data()` — bước 1–10, trả
`WorkingData(preview, lines, orders)`, **không** dựng queue. `run_import()`
gọi nó rồi mới `build_queue()` **đúng một lần**. Test:

```
working = build_working_data(path)           # validation CHƯA từng chạy
before  = _snapshot(working.lines, working.orders)
Validator.from_config_dir(...).build_queue(working.lines, working.orders)
after   = _snapshot(working.lines, working.orders)
assert after == before
```

Snapshot nay phủ **cả `lines`**, không chỉ `orders` — một detector ghi vào một
dòng mà đồ thị order không chạm tới vẫn bị bắt.

**Falsification giữ và mở rộng:**
`test_the_non_mutation_snapshot_would_actually_catch_a_write` (sửa
`conversion_rate_final` ở một dòng sâu → snapshot **khác**),
`test_the_oracle_catches_a_mutation_on_a_line_outside_any_order`, và
`test_build_working_data_really_stops_before_the_review_queue` — chặn việc
oracle âm thầm quay về chụp state "sau" nếu ai đó thêm validation vào
`build_working_data`.

## Subtask Đã Hoàn Thành (Subtasks Completed)
- [x] 110.R2 — sửa 4/4 finding của Independent Review #2.

## Subtask Còn Lại (Subtasks Remaining)
- [ ] 110.10 — Đối chiếu dữ liệu thật (CHECK-110-16). **BLOCKED**.

## Tóm Tắt Completion Gate (Completion Gate Summary)

Required:
17

PASS:
16

FAIL:
0

BLOCKED:
1 (CHECK-110-16)

NOT_TESTED:
1 (CHECK-110-18, RECOMMENDED — Independent Review #3)

## Evidence Xác Minh (Verification Evidence)

| Hạng mục | Status | Evidence Level | Evidence | Executed By | Timestamp |
|---|---|---|---|---|---|
| Regression | PASS | E1 | `python3 -m pytest tests/ -q` → **271 passed**; 151 baseline → 207 → 260 → **271** | Claude | 2026-08-23 |
| TASK-108A-1 evidence | PASS | E1 | `tests/test_reconcile_raw_*.py` **không sửa một dòng** (`git diff --stat HEAD` rỗng), 24/24 PASS; `--help` exit 0 | Claude | 2026-08-23 |
| Finding 1 — tái hiện rồi sửa | PASS | E1 | Trước: `F4 scope=batch row=None n=2` không raw identity. Sau: 0 mục F4, 3 mục `Missing.employee` | Claude | 2026-08-23 |
| Finding 2 — tái hiện rồi sửa | PASS | E1 | Trước: mapper `mapped` cho 2 dòng tháng 5 mà F6 vẫn bắn. Sau: kỳ mới **F6=0**, kỳ cũ **F6=1** (`source_rows="6, 8"`) | Claude | 2026-08-23 |
| Finding 2 — khớp production | PASS | E1 | `test_f6_record_selection_agrees_with_the_production_employee_mapper`, 8 case đối chiếu `EmployeeMapper` | Claude | 2026-08-23 |
| Finding 3 — quét state | PASS | E1 | `grep -rn "PLANNED\|chờ chủ dự án freeze\|Chưa viết dòng code" PROJECT/*.md docs/tasks/TASK-110*.md` → **0 kết quả** | Claude | 2026-08-23 |
| Finding 4 — oracle | PASS | E1 | Snapshot lấy từ `build_working_data()`; 3 falsification test đều FAIL đúng khi có mutation | Claude | 2026-08-23 |
| Validator governance | PASS | E1 | `validate_structure` / `validate_project_state` / `validate_evidence` (83 record) / `validate_task_completion` PASS | Claude | 2026-08-23 |

## File Đã Thay Đổi (Files Changed)

Created:
- `docs/sessions/S018-task-110-review-2-fixes.md` (file này)

Modified:
- `app/modules/validation/employee_mapping.py` — F4 bỏ raw value rỗng; F6 rời
  `evaluate_raw_mapping` sang `evaluate_inactive_records`;
  `select_effective_record`, `_record_key`, `MappingFinding.source_rows`
- `app/modules/validation/validator.py` — gọi `evaluate_inactive_records`;
  `_mapping_item` ưu tiên `finding.source_rows`
- `app/pipeline.py` — tách `build_working_data()` / `WorkingData`
- `tests/test_validation_employee_mapping.py` (+9 test), `tests/test_validation_pipeline.py` (+2 test)
- `docs/tasks/TASK-110-validation-review-queue.md` — Status, Scope Lock, 5 check,
  "Review #2 — FAIL, 4 finding"
- `PROJECT/PROJECT_PROGRESS.md`, `PROJECT/LO_TRINH_DE_HIEU.md` — current-state

Deleted:
- Không có.

**Không đụng:** `app/modules/domain/models.py`, `orders/`, `conversion/`,
`profit/`, `pricing/`, `adjustment/`, `lead_source/`, `mapping/`, `importing/`,
`config/` (mọi file), ADR-101…106, `tests/factories.py`,
`tests/test_reconcile_raw_*.py`, mọi file Track B, handoff S015/S016/S017.
Không đổi business calculation, không đổi KPI ownership, không mở rộng
TASK-108B/109/Price Master/UI.

## Quyết Định Chính (Key Decisions)
- Không phát sinh Human Decision mới. Cả 4 finding đều nằm trong khuôn khổ
  DEC-128 / DEC-129 đã có.
- F6 tách khỏi `evaluate_raw_mapping` **có chủ đích**: nó cần ngày của từng
  dòng và semantics chọn bản ghi của production mapper — thứ script phân tích
  không thu thập. Tách ra vừa đúng về thiết kế vừa làm CHECK-110-14 mạnh hơn.
- `build_working_data()` là refactor production nhỏ nhất đủ để oracle đúng.
  Cách thay thế — chép lại bước 1–10 trong test — sẽ trôi khỏi `run_import()`
  ngay lần đầu pipeline đổi.

## Rủi Ro / Vướng Mắc (Risks / Blockers)

**BLOCKER cho DONE — CHECK-110-16.** Vẫn thiếu file thô production. Nhắc lại
HD-110-02: con số **1.261** là **mốc tham chiếu**, không phải đích; chênh lệch
phải giải thích bằng ví dụ dòng cụ thể, **cấm** chỉnh từ khóa để đưa về 1.261.

**`select_effective_record` là bản đọc thứ hai của một rule production.** Rủi
ro là nó trôi khỏi `EmployeeMapper` khi mapper đổi. Giảm nhẹ bằng
`test_f6_record_selection_agrees_with_the_production_employee_mapper`, nhưng
test đó chỉ phủ 8 case tôi nghĩ ra. Nếu `EmployeeMapper` đổi cách chọn, phải
xem lại hàm này — đã ghi trong docstring.

**F6 vẫn chưa từng bắn trên dữ liệu thật** — `config/employees.yaml` không có
ai `active: false`.

**`inactive` vẫn nhận tỉ lệ.** F6 chỉ báo. Đổi điều đó là đổi business
calculation + KPI ownership → cần DEC riêng.

**Vế "dữ liệu nguồn mâu thuẫn" của §18 vẫn chưa làm** — chưa có định nghĩa
nghiệp vụ. Không đoán.

## Hạng Mục Regression (Regression Items)
- `pytest tests/ -q` → **271/271 PASS**. 0 regression.
- Không sửa test cũ nào để làm nó PASS. Test bị đổi chữ ký duy nhất là
  `_snapshot()` (nhận thêm `lines`) — đổi vì oracle sai, không vì nó FAIL.
- `tests/test_reconcile_raw_*.py` **không sửa một dòng**, 24/24 PASS.
- `validate_reference_integrity.py` còn 3 reference chưa phân giải, tất cả
  thuộc `docs/tasks/TASK-REM-T06-repository-root-hygiene.md` (Track B). Tiền tồn.

## Chưa Được Thay Đổi (Do Not Change Yet)
- **Không merge TASK-110** — chờ Independent Review #3.
- `app/modules/mapping/employee_mapper.py` — validation **đọc** semantics của
  nó, không sửa nó.
- `app/modules/orders/order_builder.py`, `app/modules/conversion/`.
- TASK-108B (C15), TASK-109 (chặn một phần). Bất kỳ file nào của Track B.

## Session Tiếp Theo Được Khuyến Nghị (Next Recommended Session)

**S019 — Independent Review #3 cho TASK-110.** Điểm nên soi:

1. **`select_effective_record` vs `EmployeeMapper`** — hai bản đọc của một
   rule. Test đối chiếu 8 case có đủ không?
2. **`affected_count == 0` của F2** — cố ý, nhưng làm `affected_rows()` không
   bằng tổng số dòng có vấn đề.
3. **Từ khóa `"phí"` một mình** rộng hơn `"phí "` cũ ở một chiều. Đáng soi
   trên tên sản phẩm thật.
4. **F6 và F3 trên cùng dữ liệu bàn giao** — F3 xét chồng lấn cửa sổ theo ngày
   của dòng; F6 xét bản ghi được chọn. Hai tiêu chí có thể nói khác nhau
   không?
5. **CHECK-110-16** — điều kiện duy nhất còn lại để DONE.

## Ghi Chú Về Quy Trình (Process Note)

Ba vòng, ba dạng thiếu sót khác nhau, cùng một gốc.

Vòng #1: tôi **thấy** vấn đề (scope creep) và vẫn ship nó kèm ghi chú tự thú.
Vòng #2: tôi **sửa** đúng vấn đề nhưng chỉ ở nhánh chính — Finding 1 lần này
là đúng lỗi của vòng trước lọt qua một đường vào khác; và tôi viết một oracle
phủ đủ field nhưng **chụp sai thời điểm**, nên nó không thể fail.

Bài học chung: một bản sửa chỉ hoàn tất khi nó đúng ở **mọi** đường vào, và
một phép kiểm chỉ có nghĩa khi nó **fail được** trong đúng kịch bản nó tồn tại
để bắt. Vòng này tôi tái hiện cả hai lỗi bằng script **trước** khi sửa, và
viết falsification cho từng oracle.

## File Agent Tiếp Theo Cần Đọc (Files Next Agent Should Read)
- `docs/tasks/TASK-110-validation-review-queue.md` → "Lịch Sử Independent Review"
- `app/modules/validation/employee_mapping.py` → `evaluate_inactive_records`,
  `select_effective_record`
- `app/pipeline.py` → `build_working_data` / `run_import`
- `tests/test_validation_employee_mapping.py` (Findings 1/2),
  `tests/test_validation_pipeline.py` (Finding 4)
- `PROJECT/PROJECT_DECISIONS.md` → DEC-129, DEC-128, DEC-127, DEC-121
