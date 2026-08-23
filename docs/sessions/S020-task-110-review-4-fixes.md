# BÀN GIAO SESSION (SESSION HANDOFF)

Session ID:
S020

Task:
TASK-110 — Validation + Review Queue (**sửa Independent Review #4**)

Task Mode:
MAJOR

Project Profile:
PRODUCT

Status:
**IMPLEMENTED — repairing after Independent Review #4.**
**NOT MERGED. NOT DONE.** CHECK-110-16 = **BLOCKED**.
Review #4 trên commit `35b398f`: **FAIL, 2 provenance defect** — đã sửa
**2/2**. Một Human Decision — **HD-110-05** → **DEC-131**. **298/298 test
PASS** (147 mới so với baseline `c7a1b24`, 0 regression).
**Chưa vòng review nào PASS.** Chờ **Independent Review #5**.

## Kết Quả (Result)

Cả hai defect **tái hiện bằng script trước khi sửa**. Cả hai là cùng một lớp
lỗi mà vòng #3 tưởng đã đóng — và đó là lý do lần này sửa **kiến trúc**, đúng
như review yêu cầu, chứ không vá từng case.

### Finding 1 — F3 provenance scoping

**Tái hiện.** Hai bản ghi cùng prefix `Đức`, chồng lấn tới 28/02. Hai dòng
cùng canonical identity, dòng 6 (10/02) trong overlap, dòng 7 (10/05) ngoài:

```
source_rows='6' n=1
raw_variants="'Đức Kiên' → 6, 7"      <-- dòng 7 không hề ambiguous
```

Vòng #3 đã sửa `source_rows`, nhưng `raw_variants` vẫn đi qua
`stats.render_variants(canonical)` — một đường tra cứu theo **identity**, rộng
hơn finding.

### Finding 2 — F4 provenance scoping

**Tái hiện.** `Thảo Linh` chỉ hiệu lực tháng 1, nên **cùng một chuỗi raw** vừa
map được (dòng 6, tháng 1) vừa không map được (dòng 7, tháng 5):

```
status: [(5,'mapped'), (6,'mapped'), (7,'unmapped')]
F4 source_rows='6, 7' n=1            <-- n và source_rows mâu thuẫn nhau
   raw_variants="'Thảo Linh' → 6, 7" <-- dòng 6 map bình thường
```

`affected_count` đếm đúng từ `unmapped`, nhưng provenance đi qua
`rows_by_raw_value[canonical]`.

### Sửa: kiến trúc, không phải if vá riêng

Hai vòng liền tái phát cùng một lớp lỗi ở **trường khác nhau** cho thấy vá lẻ
không đủ. Chừng nào còn tồn tại một hàm "cho tôi mọi dòng của identity này",
còn chỗ để lỗi quay lại ở trường tiếp theo.

- **`AffectedRow`** — đơn vị provenance: `source_file`, `source_row`,
  **`raw_original`** (identity đúng như đã gõ), `when`.
- **`MappingFinding.affected_rows`** — **chính tập row tạo ra finding đó**.
  `affected_count`, `source_rows`, `raw_variants()`, `render_variants()`,
  `source_file` đều là **`@property` dẫn xuất**, **không gán được**. Bất biến
  `affected_count == len(affected_rows)` đúng **theo cấu trúc**, không phải
  theo quy ước ai đó phải nhớ.
- **`MappingStats` bỏ hẳn** `rows_by_raw_value`, `rows_by_employee`,
  `raw_variants`, `render_variants()`. Chỉ còn accessor **có phạm vi**, mỗi
  cái trả lời đúng một câu hỏi mà một criterion được phép hỏi:
  `unmapped_rows()` (F4), `ambiguous_rows()` (F3), `rows_for_record()`
  (F1/F6), `all_unmapped_rows()` (F5).
- **`Validator._mapping_item()` không còn tra cứu theo identity.** Không còn
  đường để lùi về.

`MappingFinding.batch_scoped` cho criterion tự khai nó nói về **cả batch**:
F5 ("không nhân viên nào map được dòng nào") vẫn mang đủ row để
`affected_count` chính xác, nhưng không in 14.000 số dòng vào một dòng hàng
chờ. Đây là **cách trình bày**, không phải một ngoại lệ của bất biến.

**Sau khi sửa:**

```
F3: source_rows='6' n=1 raw_variants="'Đức Kiên' → 6"
    "7" xuất hiện ở bất kỳ provenance nào? False
F4: source_rows='7' n=1 raw_variants="'Thảo Linh' → 7"
```

### HD-110-05 (DEC-131) — F3 cần ngày giao dịch

Biểu thức cũ `(when is None or _overlaps(...))` khiến một dòng thiếu ngày khớp
**mọi** prefix bất kể cửa sổ hiệu lực — biến hai cửa sổ **rời nhau** (đúng cách
DEC-121 diễn đạt một lần bàn giao) thành một đụng độ. Cùng nguyên tắc
HD-110-04: không dựng cáo buộc từ một ẩn số.

Guard đặt trong `collect_mapping_stats` — **bộ thu của production** — chứ
không trong `evaluate_raw_mapping`: script phân tích tự dựng `ambiguities` của
nó và phải giữ nguyên hành vi đã ký ở CHECK-108A1-15.

**Bốn case bắt buộc, đo trực tiếp:**

| Tình huống | F3 | Missing.date |
|---|---|---|
| thiếu ngày + cửa sổ **rời nhau** | **0** | 1 |
| thiếu ngày + **overlap** | **0** | 1 |
| có ngày **trong** overlap | **1** | 0 |
| có ngày **ngoài** overlap | **0** | 0 |

**Hệ quả kèm theo, ghi rõ trong DEC-131:** việc **quy một dòng về một bản ghi
config** (`rows_by_record`, nền của F1 và F6) cũng chỉ làm cho dòng **có
ngày** — không có ngày thì bộ lọc cửa sổ không áp dụng được nên bản ghi chọn
ra là phỏng đoán. Đây là hệ quả trực tiếp của HD-110-04/05, **không** phải rule
mới: nó chỉ khiến `affected_count` của F1 thận trọng hơn, không tạo cảnh báo
nào.

## Subtask Đã Hoàn Thành (Subtasks Completed)
- [x] 110.R4 — sửa 2/2 provenance defect của Review #4, gồm HD-110-05.

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
1 (CHECK-110-18, RECOMMENDED — Independent Review #5)

## Evidence Xác Minh (Verification Evidence)

| Hạng mục | Status | Evidence Level | Evidence | Executed By | Timestamp |
|---|---|---|---|---|---|
| Regression | PASS | E1 | `python3 -m pytest tests/ -q` → **298 passed**; 151 baseline → 207 → 260 → 271 → 285 → **298** | Claude | 2026-08-23 |
| TASK-108A-1 evidence | PASS | E1 | `tests/test_reconcile_raw_*.py` **không sửa một dòng** (`git diff --stat HEAD` rỗng), **24/24 PASS**; `--help` exit 0 | Claude | 2026-08-23 |
| Finding 1 — tái hiện rồi sửa | PASS | E1 | Trước: `raw_variants="'Đức Kiên' → 6, 7"`. Sau: `→ 6`; chuỗi `"7"` không có trong **bất kỳ** trường provenance nào | Claude | 2026-08-23 |
| Finding 2 — tái hiện rồi sửa | PASS | E1 | Trước: `source_rows='6, 7'` với `n=1`, dòng 6 mapped. Sau: `source_rows='7'`, `n=1`, `raw_variants="'Thảo Linh' → 7"` | Claude | 2026-08-23 |
| HD-110-05 | PASS | E1 | 4/4 case: rời nhau→F3=0, overlap→F3=0, trong overlap→F3=1, ngoài overlap→F3=0; `Missing.date` phát đúng | Claude | 2026-08-23 |
| Bất biến provenance | PASS | E1 | `test_no_finding_can_carry_provenance_from_a_row_outside_its_own_set` + falsification + end-to-end qua `run_import()` | Claude | 2026-08-23 |
| `git diff --check` | PASS | E1 | clean | Claude | 2026-08-23 |
| Validator governance | PASS | E1 | `validate_structure` / `validate_project_state` / `validate_evidence` (83 record) / `validate_task_completion` PASS | Claude | 2026-08-23 |

## File Đã Thay Đổi (Files Changed)

Created:
- `docs/sessions/S020-task-110-review-4-fixes.md` (file này)

Modified:
- `app/modules/validation/employee_mapping.py` — `AffectedRow`;
  `MappingFinding.affected_rows` + các property dẫn xuất + `batch_scoped`;
  `MappingStats` thành row index **có phạm vi** (bỏ `rows_by_raw_value` /
  `rows_by_employee` / `raw_variants` / `render_variants`);
  `evaluate_raw_mapping(..., row_index=…)` gắn row theo từng criterion;
  `evaluate_inactive_records(employee_rows, row_index)`;
  HD-110-05 trong `collect_mapping_stats`
- `app/modules/validation/validator.py` — `_mapping_item()` chỉ đọc từ finding
- `tests/test_validation_employee_mapping.py` (+13 test)
- `PROJECT/PROJECT_DECISIONS.md` — **DEC-131**
- `docs/tasks/TASK-110-validation-review-queue.md` — Status, Scope Lock V7,
  3 check, "Review #4 — FAIL, 2 provenance defect"
- `PROJECT/PROJECT_PROGRESS.md`, `PROJECT/LO_TRINH_DE_HIEU.md` — current-state

Deleted:
- Không có file nào. Trong code: `MappingStats.rows_by_raw_value`,
  `.rows_by_employee`, `.raw_variants`, `.render_variants()` — **cố ý xóa**,
  chúng chính là đường tra cứu gây ra cả hai defect.

**Không đụng:** `app/pipeline.py`, `app/modules/validation/rules.py`,
`app/modules/validation/text.py`, `app/modules/validation/models.py`,
`config/` (mọi file), `app/modules/domain/models.py`, `orders/`,
`conversion/`, `profit/`, `pricing/`, `adjustment/`, `lead_source/`,
`mapping/`, `importing/`, ADR-101…106, `tests/factories.py`,
`tests/test_reconcile_raw_*.py`, mọi file Track B, handoff S015–S019.
Không đổi business calculation, không đổi KPI ownership, không mở rộng
TASK-108B/109/Price Master/UI.

## Quyết Định Chính (Key Decisions)
- **DEC-131 / HD-110-05** — F3 chỉ đánh giá khi dòng có ngày giao dịch.
- **Provenance là thuộc tính dẫn xuất, không phải trường gán được.** Đây là
  quyết định thiết kế trung tâm của vòng này: bất biến đúng theo cấu trúc thì
  không cần ai nhớ nó.
- **Xóa accessor rộng thay vì thêm guard.** Một guard chỉ bảo vệ nơi gọi hiện
  tại; xóa khả năng tra cứu bảo vệ cả nơi gọi chưa được viết.
- `batch_scoped` là **cách trình bày**, không phải ngoại lệ của bất biến —
  `affected_count` vẫn chính xác cho F5.

## Rủi Ro / Vướng Mắc (Risks / Blockers)

**BLOCKER cho DONE — CHECK-110-16.** Vẫn thiếu file thô production. Nhắc lại
HD-110-02: **1.261** là mốc tham chiếu, không phải đích.

**`select_effective_record` là bản đọc thứ hai của một rule production**, nay
được gọi cho **mọi dòng có ngày** (để dựng `rows_by_record`), không chỉ cho F6.
Bề mặt rủi ro trôi khỏi `EmployeeMapper` rộng hơn trước. Giảm nhẹ bằng
`test_f6_record_selection_agrees_with_the_production_employee_mapper` — nhưng
chỉ 8 case. **Đáng để Review #5 soi.**

**Chi phí tính toán tăng:** `collect_mapping_stats` nay gọi
`select_effective_record` một lần cho mỗi dòng có ngày. Trên 14.389 dòng thật,
mỗi lần là một vòng lọc + prefix match trên ~8 bản ghi. Chưa đo trên dữ liệu
thật (CHECK-110-16 BLOCKED). Nếu chậm, cache theo `(raw_value, when)`.

**F6 vẫn chưa từng bắn trên dữ liệu thật** — `config/employees.yaml` không có
ai `active: false`.

**`inactive` vẫn nhận tỉ lệ.** F6 chỉ báo. Đổi điều đó cần DEC riêng.

**Vế "dữ liệu nguồn mâu thuẫn" của §18 vẫn chưa làm** — chưa có định nghĩa.

## Hạng Mục Regression (Regression Items)
- `pytest tests/ -q` → **298/298 PASS**. 0 regression.
- Một test cũ đổi kỳ vọng: `test_f5_is_batch_scoped_and_counts_every_orphaned_row`
  vẫn PASS nguyên văn sau khi thêm `batch_scoped` — không sửa test để ép PASS,
  mà sửa **code** để F5 giữ đúng scope nó vốn khai.
- `tests/test_reconcile_raw_*.py` **không sửa một dòng**, 24/24 PASS.
- `git diff --check` → clean.
- `validate_reference_integrity.py` còn 3 reference chưa phân giải, tất cả
  thuộc `docs/tasks/TASK-REM-T06-repository-root-hygiene.md` (Track B). Tiền tồn.

## Chưa Được Thay Đổi (Do Not Change Yet)
- **Không merge TASK-110** — chờ Independent Review #5.
- `app/modules/mapping/employee_mapper.py` — validation **đọc** semantics của
  nó, không sửa nó.
- `app/modules/orders/order_builder.py`, `app/modules/conversion/`.
- TASK-108B (C15), TASK-109 (chặn một phần). Bất kỳ file nào của Track B.

## Session Tiếp Theo Được Khuyến Nghị (Next Recommended Session)

**S021 — Independent Review #5 cho TASK-110.** Điểm nên soi:

1. **`select_effective_record` nay chạy cho mọi dòng có ngày** — bề mặt tương
   đương với `EmployeeMapper` rộng hơn trước. 8 case đối chiếu đủ chưa?
2. **Hiệu năng** `collect_mapping_stats` trên 14.389 dòng — chưa đo được.
3. **`batch_scoped` của F5** — F5 mang đủ row nhưng không in ra. Có phải một
   lỗ hổng của bất biến, hay là cách trình bày đúng?
4. **`affected_count == 0` của F2** vẫn làm `affected_rows()` không bằng tổng
   dòng có vấn đề.
5. **CHECK-110-16** — điều kiện duy nhất còn lại để DONE.

## Ghi Chú Về Quy Trình (Process Note)

Năm vòng, và vòng này là vòng đầu tiên tôi sửa **lớp lỗi** thay vì sửa **lỗi**.

Vòng #3 tôi sửa `source_rows` của F3, viết test, và tin rằng đã đóng chuyện
"provenance rộng hơn finding". Nhưng tôi chỉ đóng **một trường**.
`raw_variants` vẫn gọi `stats.render_variants(canonical)`; F4 vẫn gọi
`rows_by_raw_value`. Cùng một cái sai, hai ô bên cạnh.

Bài học: khi một lỗi tái phát ở trường thứ hai, vấn đề không nằm ở trường đó
mà ở **khả năng** viết nó sai — ở đây là sự tồn tại của một hàm tra cứu theo
identity. Sửa đúng là **xóa khả năng đó**, để cả những nơi gọi chưa được viết
cũng không thể sai. Review #4 nói thẳng điều này ("Không sửa từng case bằng if
vá riêng nếu kiến trúc hiện tại khiến F3/F4 liên tục lấy provenance từ tập row
rộng hơn finding") và đó là chỉ dẫn đúng.

## File Agent Tiếp Theo Cần Đọc (Files Next Agent Should Read)
- `docs/tasks/TASK-110-validation-review-queue.md` → "Lịch Sử Independent Review"
- `PROJECT/PROJECT_DECISIONS.md` → **DEC-131** (HD-110-05), DEC-130, DEC-129, DEC-121
- `app/modules/validation/employee_mapping.py` → `AffectedRow`,
  `MappingFinding`, `MappingStats` (accessor có phạm vi), `collect_mapping_stats`
- `app/modules/validation/validator.py` → `_mapping_item`
- `tests/test_validation_employee_mapping.py` → mục "Review #4"
