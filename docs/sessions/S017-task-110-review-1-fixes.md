# BÀN GIAO SESSION (SESSION HANDOFF)

Session ID:
S017

Task:
TASK-110 — Validation + Review Queue (**sửa Independent Review #1**)

Task Mode:
MAJOR

Project Profile:
PRODUCT

Status:
**IMPLEMENTED — awaiting Independent Review #2.** Independent Review #1 trên
commit `e2c0c18`: **FAIL, 6 finding** — đã sửa **6/6**. Ba Human Decision phát
sinh → **DEC-129**. **260/260 test PASS** (109 mới so với baseline `c7a1b24`,
0 regression). 16/17 REQUIRED check PASS; CHECK-110-16 giữ **BLOCKED**.
**Chưa merge. Không tự chuyển DONE.**

## Kết Quả (Result)

Bản nộp vòng trước có 207/207 test nội bộ PASS và tự báo 16/17 check PASS.
Reviewer độc lập vẫn tìm ra 6 finding. Mỗi finding nay có regression hoặc
falsification test riêng, viết cùng lúc với bản sửa.

### Finding 1 — Provenance cho mục `EmployeeMapping`

**Vấn đề:** mục F1–F5 vào queue chỉ có `category` + `severity` + `message`.
Một mục F4 nói "tên này có 2 dòng" mà không nói **dòng nào** thì người đọc
không mở được gì.

**Sửa:** `RawMappingVerdict` nay giữ danh sách `MappingFinding` có cấu trúc
(`criterion` / `employee` / `raw_value` / `raw_prefix` / `declared_group` /
`affected_count`). `MappingStats` thu thêm `rows_by_raw_value`,
`rows_by_employee`, `source_file`, `total_rows`. `Validator._mapping_item()`
dựng:

- **có dòng thật** → `scope=row`, `source_row` = dòng đầu tiên,
  `details[source_rows]` = danh sách đầy đủ, `affected_count` = **số thật**.
- **không có dòng** (F2, F5, F1 của nhân viên vắng mặt) → `scope=batch`, kèm
  `dataset_range` + `batch_rows`, `affected_count` giữ đúng con số của tiêu
  chí — với F2 là **0**, vì F2 nghĩa là *không* khớp dòng nào; ghi 1 sẽ là
  bịa ra một dòng.

**Bằng chứng:** `test_f4_names_the_rows_it_is_about` (`source_row=11`,
`source_rows="11, 14"`, `affected_count == 2`),
`test_f2_carries_batch_provenance_and_an_honest_zero_count`,
`test_f1_points_at_the_rows_of_the_employee_whose_group_is_undeclared`,
`test_f5_is_batch_scoped_and_counts_every_orphaned_row`,
`test_every_employee_mapping_item_satisfies_the_reference_invariant`.

### Finding 2 — F1/F3/F5 là scope creep

**Vấn đề:** bảng phạm vi freeze ghi V7 là "F2 và F4"; tôi ship cả F1/F3/F5 kèm
một ghi chú "reviewer bác nếu thấy không nên".

**Sửa:** chủ dự án duyệt (**HD-110-01**). Governance nay nói ra điều đó:
- **DEC-129 §1** — bản ghi canonical.
- Bảng Phạm Vi của task: V7 = **F1–F6**.
- `config/validation.yaml` mục `employee_mapping` — ghi rõ HD-110-01/HD-110-03.

**Bài học ghi lại:** nêu ra một sai lệch không làm nó hết sai lệch. Thứ phải
làm là **hỏi trước** — đúng như đã làm với Finding 3 ở vòng này.

### Finding 3 — `Missing.employee` báo nhầm cho `inactive`

**Vấn đề:** `_is_missing()` coi mọi trạng thái khác `mapped` là thiếu nhân
viên. Một mapping `inactive` **đã nhận diện** được người bán.

**Đã STOP và hỏi.** Gỡ `inactive` khỏi `Missing` để lộ một khoảng trống thật:
`conversion_engine.py:62` chỉ chặn `unmapped` về `Unresolved` (DEC-127 §8), nên
`inactive` **vẫn nhận tỉ lệ và vẫn vào KPI**, trong khi F1–F5 chỉ phủ ca
"inactive **không** có dòng". Gỡ xong thì trạng thái đó im lặng hoàn toàn.
Không quyết định nào (§18, DEC-104, DEC-127, DEC-128) phủ ca này → hỏi chủ dự
án thay vì tự phát minh.

**Sửa:** `Missing.employee` chỉ còn `unmapped`. Ca "inactive có đơn" báo bằng
tiêu chí **F6** trong loại `EmployeeMapping` đã có (**HD-110-03**), mức
`WARNING`, kèm provenance. **Không** mã loại mới, **không** đổi cách tính,
**không** đổi KPI ownership.

**Bằng chứng:** `test_inactive_employee_is_not_reported_as_missing_employee`,
`test_only_unmapped_counts_as_a_missing_employee` (bảng 3 trạng thái),
`test_blank_employee_still_counts_as_missing` (C11 vẫn được bảo vệ),
`test_f6_reports_an_inactive_employee_that_still_has_rows`,
`test_f6_and_f2_never_describe_the_same_employee_at_once`.

### Finding 4 — Chuẩn hóa Unicode / khoảng trắng / hoa thường

**Vấn đề:** `product_raw` từ Excel, từ khóa từ YAML. Cùng một chữ có thể khác
byte (NFC vs NFD), ô Excel mang space đôi/tab. So sánh thô làm kết quả phụ
thuộc vào cách ai đó gõ file.

**Sửa:** `app/modules/validation/text.py` mới. `normalize_text()` = NFC + gộp
khoảng trắng + strip; `fold()` thêm case-folding rồi **NFC lại** (case-folding
tự nó có thể phá chuẩn hóa). Áp cho **cả hai phía**. `employee_mapping.norm`
nay trỏ vào cùng hàm đó, nên hai đường dùng chung một cách chuẩn hóa.

**Bằng chứng:** `tests/test_validation_text.py` —
`test_nfd_and_nfc_spellings_are_the_same_word` (test tự khẳng định hai chuỗi
**thật sự** khác byte trước khi so, nếu không phép kiểm vô nghĩa),
`test_a_keyword_written_in_nfd_still_compiles_to_the_same_matcher`, 4 biến thể
khoảng trắng, 3 biến thể hoa thường.

### Finding 5 — `"phí "` làm semantic

**Vấn đề:** dấu cách cuối là một **mẹo** thay cho "hết từ ở đây". Nó bỏ sót
giá trị kết thúc bằng từ đó, và mời người sau gỡ dấu cách — lúc đó `"phí"`
khớp `"bàn phím"` (một sản phẩm thật) và dòng đó bị hạ xuống INFO.

**Sửa (HD-110-02):** khớp theo **biên từ** `(?<!\w)…(?!\w)` — không dùng `\b`
vì `\b` đảo nghĩa với từ khóa không bắt đầu/kết thúc bằng ký tự chữ. Config:
`"phí "` → `"phí"`, danh sách rút về 5 từ khóa mang nghĩa.

**Bằng chứng — false positive:** `test_phi_does_not_match_ban_phim` khẳng định
**trước** rằng substring `phí` thật sự nằm trong `"bàn phím"`, rồi khẳng định
matcher **không** khớp — nên chỉ biên từ mới cứu được. Thêm 4 sản phẩm thật.
**False negative:** `test_a_keyword_at_the_very_end_of_the_value_still_matches`
(`"Thu chi phí"` — đúng ca mà mẹo dấu-cách-cuối **luôn** bỏ sót),
`test_multiword_keyword_needs_the_whole_phrase`,
`test_blank_keywords_are_dropped_rather_than_matching_everything`.

**Không tune theo 1.261.** Test khóa danh sách vào bộ lọc lịch sử đã bị **gỡ
bỏ** — nó chỉ chứng minh rule mới khớp rule cũ, không chứng minh rule đúng.
Thay bằng `test_keyword_config_expresses_semantics_not_a_historical_count`
(khẳng định hình dạng: không từ khóa nào dựa vào khoảng trắng đệm).
CHECK-110-16 nay ghi 1.261 là **mốc tham chiếu** với cảnh báo cấm tune hai
chiều.

### Finding 6 — Snapshot và provenance test quá lỏng

**Vấn đề:** snapshot non-mutation liệt kê **11 field bằng tay** (một field
thêm sau sẽ lặng lẽ thoát khỏi bảo đảm); test provenance chấp nhận mục có
reference toàn `None`.

**Sửa:**
- `_snapshot()` duyệt `dataclasses.fields` **đệ quy** qua `Order` →
  `WorkingLine` → `RawRow`. Không thể tụt lại sau model.
- Thêm `test_the_non_mutation_snapshot_would_actually_catch_a_write` — cố tình
  sửa một field sâu và khẳng định snapshot **phát hiện được**, để việc nó PASS
  có nghĩa; và `test_the_snapshot_actually_covers_every_frozen_field`.
- `ReviewItem.scope` ∈ `row`|`order`|`batch`, `__post_init__` **từ chối dựng**
  một mục không truy vết được. Bất biến là **cấu trúc**, không phải quy ước.
- `test_every_queue_item_from_a_real_import_is_traceable` khẳng định **mỗi**
  mục có reference hợp lệ theo `scope`;
  `test_an_untraceable_item_cannot_even_be_constructed` khóa ở tầng model;
  `test_every_detector_stamps_a_scope_and_a_matching_reference` phủ cả 7
  detector và khẳng định cả ba scope đều thật sự xuất hiện.

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
1 (CHECK-110-18, RECOMMENDED — Independent Review #2)

## Evidence Xác Minh (Verification Evidence)

| Hạng mục | Status | Evidence Level | Evidence | Executed By | Timestamp |
|---|---|---|---|---|---|
| Regression | PASS | E1 | `python3 -m pytest tests/ -q` → **260 passed in 1.65s**; baseline `c7a1b24` = 151, vòng trước `e2c0c18` = 207 | Claude | 2026-08-23 |
| `reconcile_conversion.py` không đổi | PASS | E1 | 24/24 PASS; `git diff --stat HEAD` **rỗng** trên hai file test của TASK-108A-1; `--help` exit 0 | Claude | 2026-08-23 |
| Không literal nghiệp vụ | PASS | E1 | `grep -rnE "<8 tên NV>\|NOI_THANH\|Decimal(\"0.N\")" app/modules/validation/*.py` → **0 kết quả** | Claude | 2026-08-23 |
| Không suy giá nhập từ ERP | PASS | E1 | `grep -rn "source_profit" app/modules/validation/*.py` → **2 dòng**, cả hai trong `detect_suspicious_erp` | Claude | 2026-08-23 |
| Provenance F4 | PASS | E1 | `run_import()` fixture → mục F4 `scope=row`, `source_row=11`, `affected_count=1` (số thật) | Claude | 2026-08-23 |
| Boundary matching | PASS | E1 | `Bàn phím cơ Logitech` **không** khớp; `Thu chi phí` khớp | Claude | 2026-08-23 |
| Validator governance | PASS | E1 | `validate_structure` / `validate_project_state` / `validate_evidence` (83 record) / `validate_task_completion` đều PASS | Claude | 2026-08-23 |

## File Đã Thay Đổi (Files Changed)

Created:
- `app/modules/validation/text.py`
- `tests/test_validation_text.py` (31 test)
- `docs/sessions/S017-task-110-review-1-fixes.md` (file này)

Modified:
- `app/modules/validation/models.py` — `scope`, bất biến reference, detail key mới
- `app/modules/validation/employee_mapping.py` — `MappingFinding`, F6, row index
- `app/modules/validation/rules.py` — Finding 3, patterns, `scope`
- `app/modules/validation/validator.py` — `_mapping_item()` provenance
- `config/validation.yaml` — HD-110-02, `"phí "` → `"phí"`, ghi chú V7
- `tests/test_validation_rules.py`, `tests/test_validation_employee_mapping.py`,
  `tests/test_validation_pipeline.py`
- `PROJECT/PROJECT_DECISIONS.md` — **DEC-129**
- `docs/tasks/TASK-110-validation-review-queue.md` — Scope Lock V7 → F1–F6,
  evidence 8 check, "Lịch Sử Independent Review"
- `PROJECT/PROJECT_PROGRESS.md`, `PROJECT/LO_TRINH_DE_HIEU.md`

Deleted:
- `test_config_keyword_list_matches_the_measured_evidence_filter` (test, không
  phải file) — nó khóa danh sách từ khóa vào con số lịch sử 1.261, đúng thứ
  HD-110-02 cấm.

**Không đụng:** `app/modules/domain/models.py`, `orders/`, `conversion/`,
`profit/`, `pricing/`, `adjustment/`, `lead_source/`, `mapping/`, `importing/`,
`config/employees.yaml`, `config/conversion_rates.yaml`, `config/lead_source.yaml`,
ADR-101…106, `tests/factories.py`, `tests/test_reconcile_raw_*.py`, mọi file
Track B. Không đổi business calculation, không đổi KPI ownership.

## Quyết Định Chính (Key Decisions)
- **DEC-129** — HD-110-01 (F1–F5 vào queue), HD-110-02 (heuristic tạm thời,
  bỏ literal `"phí "`, cấm tune theo 1.261), HD-110-03 (tiêu chí F6).
- `RawMappingVerdict` giữ findings có cấu trúc nhưng vẫn phơi ba list chuỗi cũ
  **đúng thứ tự cũ** — script phân tích không thấy khác biệt (CHECK-110-14).
- Bất biến truy vết đặt ở `__post_init__` chứ không ở test: một mục không
  truy vết được phải **không dựng nổi**, chứ không phải "được test bắt".

## Rủi Ro / Vướng Mắc (Risks / Blockers)

**BLOCKER cho DONE — CHECK-110-16.** Vẫn thiếu file thô production. Thêm một
điểm mới sau HD-110-02: con số **1.261** nay là **mốc tham chiếu**, không phải
đích. Ngữ nghĩa biên từ mới có thể cho con số khác **một cách chính đáng** (nó
bắt được cả giá trị kết thúc bằng "phí" mà bộ lọc cũ bỏ sót). Chênh lệch phải
được giải thích bằng ví dụ dòng cụ thể — **cấm chỉnh từ khóa để đưa về 1.261**.

**F6 tạo áp lực lên master data (mong muốn, không phải nhiễu).** Nếu ai được
set `active: false` mà `effective_to` chưa đóng, F6 sẽ kêu mỗi lần import cho
tới khi config được sửa. Hiện `config/employees.yaml` không có ai
`active: false`, nên F6 chưa từng bắn trên dữ liệu thật.

**`inactive` vẫn nhận tỉ lệ.** F6 chỉ **báo**. Muốn `inactive` không nhận tỉ
lệ là đổi business calculation + KPI ownership → DEC riêng + sửa
`conversion_engine` (ngoài Expected Touch Area).

**Vế "dữ liệu nguồn mâu thuẫn" của §18 vẫn chưa làm** — chưa có định nghĩa
nghiệp vụ. Không đoán.

**PHỤ THUỘC MỀM lên TASK-103 nay là ràng buộc tường minh.** HD-110-02: heuristic
từ khóa là **tạm thời**, TASK-103 phải **thay thế** chứ không kế thừa.

## Hạng Mục Regression (Regression Items)
- `pytest tests/ -q` → **260/260 PASS** (151 baseline + 109 mới). 0 regression.
- Không sửa một test cũ nào để làm nó PASS. Test duy nhất bị **gỡ** là test
  khóa danh sách từ khóa vào con số 1.261 — gỡ vì HD-110-02 cấm nó, không phải
  vì nó FAIL.
- `tests/test_reconcile_raw_*.py` (TASK-108A-1) **không sửa một dòng nào**,
  24/24 PASS — Independent Review evidence cũ giữ nguyên.
- `validate_reference_integrity.py` vẫn còn 3 reference chưa phân giải, tất cả
  thuộc `docs/tasks/TASK-REM-T06-repository-root-hygiene.md` (Track B, forward
  reference tới ba file ở root mà chính task đó sẽ tạo). Tiền tồn.

## Chưa Được Thay Đổi (Do Not Change Yet)
- **Không merge TASK-110** — chờ Independent Review #2.
- `app/modules/orders/order_builder.py`, `app/modules/conversion/conversion_engine.py`.
- `app/modules/domain/models.py`.
- TASK-108B (C15), TASK-109 (chặn một phần).
- Bất kỳ file nào của Track B.

## Session Tiếp Theo Được Khuyến Nghị (Next Recommended Session)

**S018 — Independent Review #2 cho TASK-110.** Điểm nên soi:

1. **`affected_count == 0` của F2** — cố ý (F2 nghĩa là không khớp dòng nào),
   nhưng nó làm `ReviewQueue.affected_rows()` không bằng tổng số dòng có vấn
   đề. Cách đọc này có ổn không?
2. **`_selling_identity()`** vẫn coi mỗi giá trị `NVBH` chưa map là một danh
   tính riêng. Chưa đo được trên dữ liệu thật là V4 có bắn quá tay không.
3. **Từ khóa `"phí"` một mình** giờ khớp mọi cụm chứa nguyên từ "phí". Rộng
   hơn `"phí "` cũ ở đúng một chiều (giá trị kết thúc bằng "phí"). Đúng ý
   định, nhưng đáng soi trên tên sản phẩm thật.
4. **F6 trên dữ liệu thật** — chưa quan sát được, vì chưa ai `active: false`.
5. **CHECK-110-16** — điều kiện duy nhất còn lại để DONE.

## Ghi Chú Về Quy Trình (Process Note)

Hai vòng, hai lần cùng một bài học ở hai mức độ khác nhau.

Vòng trước tôi **đã nhìn thấy** vấn đề của Finding 2 và viết hẳn ra
("ghi ra để reviewer bác nếu thấy không nên") — rồi vẫn ship nó. Nêu ra một
sai lệch không làm nó hết sai lệch; nó chỉ chuyển việc quyết định sang người
khác **sau khi** code đã nằm đó.

Vòng này, khi Finding 3 lộ ra một khoảng trống nghiệp vụ tương tự, tôi dừng
lại hỏi **trước khi** viết dòng nào. Kết quả là HD-110-03 — một quyết định của
chủ dự án, không phải một hành vi của công cụ cần biện minh về sau.

## File Agent Tiếp Theo Cần Đọc (Files Next Agent Should Read)
- `docs/tasks/TASK-110-validation-review-queue.md` → "Lịch Sử Independent Review"
- `PROJECT/PROJECT_DECISIONS.md` → **DEC-129** (và DEC-128, DEC-127, DEC-103)
- `app/modules/validation/text.py` (ngữ nghĩa khớp), `models.py` (bất biến scope)
- `tests/test_validation_text.py` (falsification Findings 4/5)
- `docs/sessions/S016-task-110-validation-review-queue.md` (vòng triển khai)
