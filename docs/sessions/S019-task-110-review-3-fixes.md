# BÀN GIAO SESSION (SESSION HANDOFF)

Session ID:
S019

Task:
TASK-110 — Validation + Review Queue (**sửa Independent Review #3**)

Task Mode:
MAJOR

Project Profile:
PRODUCT

Status:
**IMPLEMENTED — repair after Independent Review #3. Chưa merge. Chưa DONE.**
Review #3 trên commit `53264fe`: **FAIL, 3 finding** — đã sửa **3/3**. Một
Human Decision — **HD-110-04** → **DEC-130**. **285/285 test PASS** (134 mới
so với baseline `c7a1b24`, 0 regression). 16/17 REQUIRED check PASS;
CHECK-110-16 giữ **BLOCKED**. Chờ **Independent Review #4**.

## Kết Quả (Result)

Cả ba finding đều được **tái hiện bằng script trước khi sửa**. Và cả ba là
cùng một dạng lỗi: **verdict đúng, provenance sai**.

### Finding 1 — F3 provenance sai theo effective window

**Tái hiện.** Hai bản ghi cùng prefix `Đức`: A hiệu lực từ 2026-01-01 không
giới hạn, B hiệu lực 2026-01-01..2026-02-28. Hai dòng cùng raw value:

```
F3 row=6 n=2 rows=6, 7
```

Dòng 6 (10/02) nằm trong vùng chồng lấn → thật sự mập mờ. Dòng 7 (10/05) chỉ
còn A hiệu lực → **hoàn toàn rõ ràng**, nhưng vẫn bị đánh dấu.

**Nguyên nhân:** `collect_mapping_stats` ghi ambiguity vào
`ambiguities[raw_value] = hits` — theo **giá trị**, không theo **dòng**. Rồi
`_mapping_item` tra `rows_by_raw_value[raw_value]` → lấy **mọi** dòng mang giá
trị đó. Nhưng chính vòng lặp đó đã tính `hits` **theo từng dòng** (DEC-121:
hai prefix chỉ tồn tại ở hai kỳ rời nhau là bàn giao, không phải đụng độ) —
thông tin per-row có sẵn rồi mà bị vứt đi.

**Sửa.** `AmbiguousRow` mới ghi theo dòng, giữ đủ bốn thứ review yêu cầu:
raw identity (canonical + bản gốc), `source_file`/`source_row`, **ngày giao
dịch**, và **các bản ghi master xung đột**. Bản ghi được nêu bằng
`_record_label()` — tên **kèm prefix và cửa sổ hiệu lực** — vì hai bản ghi có
thể cố ý trùng tên (DEC-121), nên tên trần không định danh được.

`evaluate_raw_mapping` nhận `ambiguity_rows` như một tham số **tùy chọn**:
script phân tích gọi positional và chỉ in chuỗi, nên nó không đổi một byte
(CHECK-110-14).

**Sau khi sửa:** `rows="6"`, `n=1`,
`ambiguous_rows = dòng 6 (2026-02-10) → A[Đức|2026-01-01..9999-12-31], B[Đức|2026-01-01..2026-02-28]`.

**Test:** `test_f3_names_only_the_rows_that_are_really_ambiguous`,
`test_f3_provenance_carries_identity_row_date_and_conflicting_records` (khẳng
định `2026-05-10` **không** xuất hiện — falsification thật, không chỉ kiểm sự
hiện diện), `test_f3_counts_every_ambiguous_row_when_several_collide`,
`test_no_overlap_at_all_means_no_f3`.

### Finding 2 — HD-110-04: F6 khi thiếu ngày (DEC-130)

**Tái hiện.** Cặp bàn giao cùng prefix, một dòng **không có ngày**:

```
mapper status khi thiếu ngày: inactive
F6 khi thiếu ngày: 1   (HD-110-04 yêu cầu 0)
Missing.date: 1
```

`EmployeeMapper.resolve` khi `as_of is None` bỏ qua lọc `effective_rows` rồi
chọn prefix dài nhất — trúng bản ghi cũ `active: false`.
`select_effective_record` phản chiếu đúng hành vi đó, nên F6 bắn.

**Sửa.** `evaluate_inactive_records` bỏ qua dòng `date is None`. Guard đặt ở
**đó**, cố ý **không** ở `select_effective_record`: hàm đó phải tiếp tục phản
chiếu mapper nguyên vẹn, và
`test_f6_record_selection_agrees_with_the_production_employee_mapper` khẳng
định điều đó — sửa sai chỗ sẽ phá bảo đảm tương đương với production.

Đúng năm ràng buộc chủ dự án nêu: `Missing.date` **vẫn phát**; **không** chọn
bản ghi đầu tiên; **không** khẳng định dòng nằm trong cửa sổ nào; **không**
tạo loại business rule mới; **không** đổi `EmployeeMapper`/Conversion/KPI.

**Test bắt buộc, đủ cả ba:**
`test_missing_date_produces_missing_date_and_never_f6` (thiếu ngày + cặp
inactive-cũ/active-mới cùng prefix → **0** F6, **1** `Missing.date`),
`test_a_date_inside_the_inactive_window_still_raises_f6` (**1** F6),
`test_a_date_inside_the_active_window_raises_no_f6` (**0** F6). Thêm
`test_dateless_rows_are_dropped_without_hiding_the_dated_ones` và
`test_hd_110_04_does_not_change_mapping_status_for_a_dateless_row`.

### Finding 3 — F4 phải giữ raw identity nguyên bản

**Tái hiện.** Ba biến thể của cùng một tên — `'Thảo Linh 0900000001'`, bản có
dấu cách đôi, và bản NFD:

```
F4 n=3 raw_value='Thảo Linh 0900000001'
details keys = ['criterion', 'raw_value', 'source_rows']
```

Gom nhóm đúng, nhưng **không còn dấu vết** ba cách viết gốc.

**Sửa.** `MappingStats.raw_variants` giữ
`{canonical: {bản gốc: các dòng của nó}}`; `render_variants()` in bằng `repr`
— cố ý, vì một dấu cách đôi in trần thì không phân biệt được với một dấu cách,
mà đó chính là loại khác biệt cần giữ.

**Sau khi sửa:**
`raw_variants = 'Thảo Linh 0900000001' → 11 ; 'Thảo  Linh 0900000001' → 12 ; 'Thảo Linh 0900000001' → 13`
(mục thứ ba là bản NFD — nhìn giống bản đầu nhưng là chuỗi khác).

**Test:** `test_f4_keeps_every_original_raw_spelling_with_its_own_rows` — test
tự khẳng định NFD **thật sự khác** NFC trước khi so, nếu không phép kiểm vô
nghĩa; `test_raw_variants_use_repr_so_invisible_differences_stay_visible`;
`test_a_single_spelling_still_records_itself`.

### F3 × F6 interaction (theo yêu cầu review)

`test_f3_and_f6_describe_the_same_batch_without_contradicting_each_other` —
một raw identity, hai bản ghi chồng lấn, một trong hai `inactive`. F3 chỉ nêu
dòng có cả hai bản ghi hiệu lực; F6 chỉ nêu dòng phân giải về bản ghi
inactive; **không bên nào** nhận dòng 7. Và
`test_f3_fires_but_f6_stays_silent_when_the_dates_are_unknown` — HD-110-04 chỉ
áp cho F6, không lặng lẽ đổi semantics của F3.

## Subtask Đã Hoàn Thành (Subtasks Completed)
- [x] 110.R3 — sửa 3/3 finding của Independent Review #3, gồm HD-110-04.

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
1 (CHECK-110-18, RECOMMENDED — Independent Review #4)

## Evidence Xác Minh (Verification Evidence)

| Hạng mục | Status | Evidence Level | Evidence | Executed By | Timestamp |
|---|---|---|---|---|---|
| Regression | PASS | E1 | `python3 -m pytest tests/ -q` → **285 passed**; 151 baseline → 207 → 260 → 271 → **285** | Claude | 2026-08-23 |
| TASK-108A-1 evidence | PASS | E1 | `tests/test_reconcile_raw_*.py` **không sửa một dòng** (`git diff --stat HEAD` rỗng), 24/24 PASS; `--help` exit 0 | Claude | 2026-08-23 |
| Finding 1 — tái hiện rồi sửa | PASS | E1 | Trước: `rows="6, 7"`, `n=2`. Sau: `rows="6"`, `n=1`, kèm ngày giao dịch + hai bản ghi xung đột | Claude | 2026-08-23 |
| Finding 2 — tái hiện rồi sửa | PASS | E1 | Trước: thiếu ngày → mapper `inactive`, F6=1. Sau: thiếu ngày **F6=0** + `Missing.date`=1; kỳ inactive **F6=1**; kỳ active **F6=0** | Claude | 2026-08-23 |
| Finding 3 — tái hiện rồi sửa | PASS | E1 | Trước: 3 biến thể gộp, `details` không có bản gốc. Sau: `raw_variants` giữ đủ ba, NFD kiểm chứng bằng `in` trên chuỗi thật | Claude | 2026-08-23 |
| F3 × F6 interaction | PASS | E1 | Hai tiêu chí mô tả cùng một batch, không bên nào nhận dòng của bên kia | Claude | 2026-08-23 |
| Validator governance | PASS | E1 | `validate_structure` / `validate_project_state` / `validate_evidence` (83 record) / `validate_task_completion` PASS | Claude | 2026-08-23 |

## File Đã Thay Đổi (Files Changed)

Created:
- `docs/sessions/S019-task-110-review-3-fixes.md` (file này)

Modified:
- `app/modules/validation/models.py` — `DETAIL_RAW_VARIANTS`,
  `DETAIL_AMBIGUOUS_ROWS`, `DETAIL_CONFLICTING_RECORDS`
- `app/modules/validation/employee_mapping.py` — `AmbiguousRow`,
  `_record_label`, `MappingFinding.details`, `MappingStats.raw_variants` +
  `.ambiguity_rows` + `render_variants()`, F3 nhận `ambiguity_rows` (tùy
  chọn), F6 bỏ qua dòng thiếu ngày (HD-110-04)
- `app/modules/validation/validator.py` — truyền `ambiguity_rows`, merge
  `finding.details`, gắn `raw_variants`
- `tests/test_validation_employee_mapping.py` (+14 test)
- `PROJECT/PROJECT_DECISIONS.md` — **DEC-130**
- `docs/tasks/TASK-110-validation-review-queue.md` — Status, Scope Lock V7,
  4 check, "Review #3 — FAIL, 3 finding"
- `PROJECT/PROJECT_PROGRESS.md`, `PROJECT/LO_TRINH_DE_HIEU.md` — current-state

Deleted:
- Không có.

**Không đụng:** `app/pipeline.py`, `app/modules/validation/rules.py`,
`app/modules/validation/text.py`, `config/` (mọi file),
`app/modules/domain/models.py`, `orders/`, `conversion/`, `profit/`,
`pricing/`, `adjustment/`, `lead_source/`, `mapping/`, `importing/`,
ADR-101…106, `tests/factories.py`, `tests/test_reconcile_raw_*.py`, mọi file
Track B, handoff S015–S018. Không đổi business calculation, không đổi KPI
ownership, không mở rộng TASK-108B/109.

## Quyết Định Chính (Key Decisions)
- **DEC-130 / HD-110-04** — giao dịch thiếu ngày không phát F6.
- Guard HD-110-04 đặt ở `evaluate_inactive_records`, **không** ở
  `select_effective_record`: hàm đó phải tiếp tục phản chiếu `EmployeeMapper`
  nguyên vẹn, và có test khẳng định tương đương.
- `ambiguity_rows` là tham số **tùy chọn** của `evaluate_raw_mapping` — cùng
  kỹ thuật đã dùng cho F6 ở vòng #2: production giàu provenance hơn, script
  phân tích không đổi một byte.
- `render_variants()` dùng `repr` chứ không in trần — khác biệt vô hình là thứ
  duy nhất nó tồn tại để giữ.

## Rủi Ro / Vướng Mắc (Risks / Blockers)

**BLOCKER cho DONE — CHECK-110-16.** Vẫn thiếu file thô production. Nhắc lại
HD-110-02: **1.261** là mốc tham chiếu, không phải đích; **cấm** chỉnh từ khóa
để đưa về con số đó.

**F3 với dòng thiếu ngày giữ nguyên semantics cũ.** `collect_mapping_stats`
vẫn coi `when is None` là khớp mọi prefix, nên một dòng thiếu ngày có thể vào
F3. HD-110-04 chỉ quyết cho **F6**; tôi **không** tự mở rộng nó sang F3 vì đó
sẽ là đổi một hard-failure rule mà chưa ai quyết. Provenance nay ghi rõ
`(không có ngày)` để người duyệt thấy được. **Đáng để Review #4 cân nhắc.**

**`select_effective_record` là bản đọc thứ hai của một rule production.** Rủi
ro trôi khỏi `EmployeeMapper` nếu mapper đổi; giảm nhẹ bằng test tương đương
8 case, nhưng chỉ 8 case tôi nghĩ ra.

**F6 vẫn chưa từng bắn trên dữ liệu thật** — `config/employees.yaml` không có
ai `active: false`.

**`inactive` vẫn nhận tỉ lệ.** F6 chỉ báo. Đổi điều đó cần DEC riêng.

**Vế "dữ liệu nguồn mâu thuẫn" của §18 vẫn chưa làm** — chưa có định nghĩa.

## Hạng Mục Regression (Regression Items)
- `pytest tests/ -q` → **285/285 PASS**. 0 regression.
- Không sửa test cũ nào để làm nó PASS. Không gỡ test nào ở vòng này.
- `tests/test_reconcile_raw_*.py` **không sửa một dòng**, 24/24 PASS.
- `validate_reference_integrity.py` còn 3 reference chưa phân giải, tất cả
  thuộc `docs/tasks/TASK-REM-T06-repository-root-hygiene.md` (Track B). Tiền tồn.

## Chưa Được Thay Đổi (Do Not Change Yet)
- **Không merge TASK-110** — chờ Independent Review #4.
- `app/modules/mapping/employee_mapper.py` — validation **đọc** semantics của
  nó, không sửa nó.
- `app/modules/orders/order_builder.py`, `app/modules/conversion/`.
- TASK-108B (C15), TASK-109 (chặn một phần). Bất kỳ file nào của Track B.

## Session Tiếp Theo Được Khuyến Nghị (Next Recommended Session)

**S020 — Independent Review #4 cho TASK-110.** Điểm nên soi:

1. **F3 với dòng thiếu ngày** — HD-110-04 chỉ quyết cho F6. F3 hiện coi dòng
   thiếu ngày là khớp mọi prefix. Có nên áp cùng nguyên tắc "không đủ bằng
   chứng" không? Đó là đổi hard-failure rule → cần quyết định.
2. **`_record_label` format** (`Tên[prefix|từ..đến]`) — đủ để phân biệt hai
   bản ghi trùng tên chưa?
3. **`select_effective_record` vs `EmployeeMapper`** — 8 case đối chiếu đủ chưa?
4. **`affected_count == 0` của F2** vẫn làm `affected_rows()` không bằng tổng
   dòng có vấn đề.
5. **CHECK-110-16** — điều kiện duy nhất còn lại để DONE.

## Ghi Chú Về Quy Trình (Process Note)

Bốn vòng, và hình dạng lỗi đã dịch chuyển rõ rệt.

Vòng #1 là **phạm vi và thiết kế** (scope creep, thiếu provenance, semantic
sai). Vòng #2 là **bản sửa chưa đi hết đường** (đúng nhánh chính, sót nhánh
phụ) và **một oracle không thể fail**. Vòng #3 là **verdict đúng nhưng bằng
chứng sai** — cả ba finding đều thuộc dạng này.

Điều đáng ghi: ở một hàng chờ để người duyệt kiểm tay, **provenance chính là
sản phẩm**. Một cảnh báo mà người duyệt không lần lại được thì gần như vô
dụng, dù kết luận của nó đúng — và tệ hơn, nó dạy người ta bỏ qua hàng chờ.
Ba vòng đầu tôi coi "phát hiện đúng" là xong việc; đó là chỗ sai.

## File Agent Tiếp Theo Cần Đọc (Files Next Agent Should Read)
- `docs/tasks/TASK-110-validation-review-queue.md` → "Lịch Sử Independent Review"
- `PROJECT/PROJECT_DECISIONS.md` → **DEC-130** (HD-110-04), DEC-129, DEC-128, DEC-121
- `app/modules/validation/employee_mapping.py` → `AmbiguousRow`,
  `evaluate_inactive_records`, `select_effective_record`, `render_variants`
- `tests/test_validation_employee_mapping.py` (Findings 1/2/3 + F3×F6)
