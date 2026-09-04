# PHB-04 — LEGACY REFERENCE V1

Status: IMPLEMENTED_AWAITING_REVIEW
Task Mode: MAJOR
Priority: REQUIRED
Evidence Level: E1
Executed By: S119 (Claude Code on the web) — bản đính chính DEC-177
Timestamp: 2026-09-04
Risk: 3 (số cũ hiện sai nhãn khiến chủ dự án đọc nhầm số tay thành số kế toán
chính thức; KHÔNG chạm pipeline, KHÔNG chạm KPI/lương, KHÔNG có migration)

Nguồn thẩm quyền: `docs/tasks/PHB-02-business-parity-contract.md` (FROZEN)
mục 5.6 `L1`–`L6` và 10.7 · `DEC-169` (Owner scope clarification) ·
`docs/tasks/TASK-PRA-001-legacy-reference-vertical.md` (DONE — nền lưu trữ) ·
`docs/analysis/02_FORMULA_MAPPING.md` §5.

Vertical này trả lời **một** câu hỏi:

> *Chủ dự án có xem được số của các kỳ lịch sử, và so được ở những chỗ được
> phép so, mà KHÔNG khiến số cũ bị nhầm thành số của công cụ hiện tại?*

Đây **không** phải bài tập import lại workbook cũ qua pipeline kế toán, và
**không** phải bài tập làm cho 2025 trông như thể đã chạy qua engine mới.

---

## 1. Target Gate

```text
CANONICAL_BRANCH = claude/extract-upload-repo-gq2ws4 (origin HEAD branch)
CANONICAL_HEAD   = 51d8fef4499642290398d795e7639e13792bee45
BEHIND_DEFAULT   = 0 commit
WORKING_BRANCH   = claude/phb-04-legacy-reference-v1-widtzf
WORKTREE         = CLEAN
TARGET_GATE      = PASS
```

Sức khoẻ HEAD tại thời điểm mở phiên (E1, thực thi trong phiên):

```text
python -m pytest -q                               → 2136 passed, 11 skipped
python -m pytest tests/test_golden_baseline.py \
    tests/test_golden_bh62063_kpi.py \
    tests/test_golden_bh62439_kpi.py \
    tests/test_golden_bh62439_safe_pending.py -q  → 74 passed, 2 skipped
```

---

## 2. Kết quả audit bằng chứng — BẢN ĐÃ ĐÍNH CHÍNH (`DEC-177`)

> **Đính chính.** Bản audit đầu tiên của phiên này kết luận *"năm 2025 chỉ
> có một chỉ tiêu: doanh số tháng"*. Chủ dự án đã BÁC BỎ kết luận đó và xác
> nhận 2025 có Summary riêng + chi tiết theo nhân viên. Mục này là bản đã
> sửa; kết luận cũ không được giữ lại ở bất kỳ đâu trong tài liệu.

**A. Nền lưu trữ legacy ĐÃ tồn tại và đã được nghiệm thu.** `TASK-PRA-001`
(DONE) dựng bốn bảng `legacy_*` với cột `origin` mang CHECK constraint
`origin = 'LEGACY_REFERENCE'`, cộng đường nhập workbook idempotent theo
fingerprint. Quan trọng hơn: `legacy_summary_row` khoá theo
`(year, month, seller_label, row_kind)` với đủ 16 cột `C..S` và **không hề
gắn với năm 2026** — nó lưu được cả period-level lẫn employee-level của 2025
mà KHÔNG cần thêm cột nào.

**B. `DEC-169` là tuyên bố PHẠM VI, không phải lệnh cấm.** Nguyên văn:
*"Owner KHÔNG yêu cầu import / persist / query / display Summary 2025"* —
tức *"chưa cần"*, không phải *"không được có"*. Bản triển khai đầu của phiên
đã đọc rộng thành "bị cấm khỏi sản phẩm". Phân tích đầy đủ bốn khả năng ở
`DEC-177` §1; kết luận: `A`/`B`/`C` ĐÚNG và vẫn giữ, `D` SAI.

**C. Vì sao chuỗi bằng chứng chỉ nhìn thấy 12 số của 2025.** Cả ba tầng đọc
đều **bị chặn bởi công thức**, độc lập nhau:

| Tầng | Điều kiện | Hệ quả trên `Summary 2025` |
|---|---|---|
| `tools/analysis/extract_evidence.py` | chỉ ghi dòng khi cột `F` **là công thức** | `evidence.json` chứa **0** lần chuỗi `"2025"` |
| `app/legacy/parser.py::_classify()` | `row_kind` suy từ **cấu trúc công thức** | không dòng 2025 nào phân loại được |
| hợp đồng PHB-04 (bản đầu) | dựng trên hai tầng trên | kết luận sai "2025 chỉ có doanh số tháng" |

Kết luận cũ vì vậy là **kết luận về công cụ đọc**, bị trình bày nhầm thành
**kết luận về dữ liệu**.

**D. Kiểm kê thật của workbook (từ `evidence.json`).**

```text
sheet_count                    = 59
sheet đơn-nhân-viên-tháng      = 56  — TẤT CẢ đều là 2026 (01.2026 … 08.2026)
sheet còn lại                  = 3   — Summary 2026 · Summary 2025 · DataChart 2026
số lần chuỗi "2025" trong evidence.json = 0
```

⟹ Workbook **không có** sheet `MM.2025 <Nhân viên>` nào. Toàn bộ chi tiết
2025 — nếu có — nằm **trong chính sheet `Summary 2025`**, đúng như chủ dự án
mô tả ("cấu trúc gần giống báo cáo 2026").

Số dòng củng cố điều đó, và được ghi ở đây như **suy luận từ hình dạng, KHÔNG
phải nội dung đã quan sát**: `Summary 2026` có 71 dòng công thức cho 8 tháng
(~8,9 dòng/tháng); `Summary 2025` có 99 dòng value-only cho 12 tháng
(~8,3 dòng/tháng). Hai mật độ khớp nhau — nhất quán với một bảng người bán ×
tháng cùng hình dạng.

**E. Nội dung thật của 99 dòng đó CHƯA TỪNG được quan sát.** Workbook không
có trong repo (`data/samples/` nằm trong `.gitignore` vì chứa dữ liệu cá nhân
khách hàng) và không có trên đĩa của phiên. Xem mục 10 —
`NEED_OWNER_SOURCE`.

---

## 3. Hợp đồng Legacy Reference V1 (FROZEN)

### 3.1 Kỳ nào là LEGACY_REFERENCE?

Hai NGUỒN legacy, không phải hai "lớp năm". Cả hai cùng
`origin = LEGACY_REFERENCE`; chúng KHÔNG thay thế nhau và KHÔNG được cộng
vào nhau:

| Nguồn | Phạm vi nhập | Nội dung | Chỉ tiêu |
|---|---|---|---|
| `Summary 2026` | `REQUIRED_IMPORT` | bảng người bán × tháng, 2026 | 16 cột `C..S` (`L6`) |
| **`Summary 2025`** | **`OPTIONAL_IMPORT`** (`DEC-177`) | bảng người bán × tháng, 2025 | **cùng 16 cột `C..S`** |
| `DataChart 2026!AH3:AH14` | `REQUIRED_IMPORT` | 12 ô doanh số tháng của năm trước | doanh số tháng (VND) |

Điểm then chốt của bản đính chính: **`Summary 2025` và `Summary 2026` dùng
CÙNG 16 cột với cùng ý nghĩa**, nên hợp đồng chỉ tiêu KHÔNG gắn với năm —
`SUMMARY_SHEET_CONTRACT` áp dụng cho mọi năm. Chi tiết theo NHÂN VIÊN của
một năm lịch sử sống ở đây: mỗi dòng `row_kind = SELLER` là một
(kỳ, người bán) với 16 chỉ tiêu.

Ngữ nghĩa `OPTIONAL_IMPORT`:

```text
dòng contract phân loại được   → NHẬP (origin = LEGACY_REFERENCE)
dòng KHÔNG phân loại được      → KHÔNG đoán, KHÔNG im lặng:
                                 đếm + lưu vào sheets_imported + hiện lên /lich-su
sheet vắng mặt / không đọc được → KHÔNG làm trượt cả workbook
```

Nhánh cuối là điều kiện để `DEC-177` không lật `DEC-169` thành một hồi quy.
Guard `DEC-168` trên sheet `REQUIRED_IMPORT` **không bị nới lỏng**: ở đó một
dòng có số mà không phân loại được vẫn FAIL TO.

Năm trước của chuỗi `DataChart` suy ra bằng `row.year - 1` — **không
hard-code 2025**. Ô `AH` trống ⟹ không phải một kỳ có dữ liệu.

**Tình trạng chỉ tiêu của một năm được ĐO, không viết cứng.**
`summary_year_availability()` đếm ô có giá trị trên chính dòng đã nhập của
năm đó:

```text
AVAILABLE_WITH_ACCEPTED_EVIDENCE   có ô mang số + hợp đồng xếp là hiển thị được
AVAILABLE_BUT_SEMANTICS_UNCERTAIN  có ô mang số nhưng hợp đồng chưa chốt nghĩa
NOT_AVAILABLE                      cột tồn tại, mọi ô đều trống
```

Cách này chịu được điều mà một danh sách cứng không chịu được: workbook thật
có thể mang nhiều hoặc ít cột hơn fixture, và câu trả lời phải theo FILE.

### 3.2 Ranh giới cutover

```text
CUTOVER_BOUNDARY = THEO ORIGIN, KHÔNG THEO NGÀY
```

Đây là **phát hiện từ bằng chứng**, không phải một ngày được chọn. Repo không
có quyết định nào định nghĩa một mốc ngày cho báo cáo. Cái repo thực sự có là
một ranh giới theo **nguồn dữ liệu, tính theo từng kỳ**:

- `origin = LEGACY_REFERENCE` — dòng đến từ workbook tay (bốn bảng `legacy_*`);
- `origin = PIPELINE_GENERATED` — dòng do công cụ hiện tại sinh ra
  (`order_line_*`, `snapshot_*`).

Một kỳ 2026 có thể có **cả hai**; kỳ 2025 chỉ có legacy. V1 không bao giờ hợp
nhất hai origin thành một con số, nên V1 **không cần** một mốc ngày để chạy
đúng — và vì vậy đây KHÔNG phải một `OWNER_DECISION_REQUIRED` chặn PHB-04.

`CUTOVER_DATE = 2026-09-01` đã tồn tại trong repo là mốc **giá / Product
Identity**, và `PROJECT/PROJECT_PROGRESS.md` đã ghi rõ *"Hai cutover, không gộp"*. Mốc
đó **không** được tái sử dụng làm ranh giới báo cáo.

Câu hỏi *"kỳ có cả hai nguồn thì số nào là số của kỳ?"* là một quyết định của
chủ dự án còn **để mở** — nhưng nó chỉ phát sinh nếu sau này có yêu cầu hiển
thị MỘT con số duy nhất cho mỗi kỳ. V1 không đưa ra yêu cầu đó (`OD-PHB04-A`,
mục 6).

### 3.3 Phân loại chỉ tiêu

Bảng đầy đủ sống trong mã tại `app/web/legacy_reference.py`
(`REFERENCE_YEAR_CONTRACT` cho chuỗi `DataChart`, `SUMMARY_SHEET_CONTRACT`
cho dòng Summary MỌI NĂM) — mỗi dòng mang lý do và đường dẫn bằng chứng, và
trang `/lich-su` in nguyên văn ra cho chủ dự án đọc.

```text
COMPARABLE (so được với số mới)  = KHÔNG CÓ CHỈ TIÊU NÀO (V1) — xem 3.6
REFERENCE_ONLY (hiển thị được)   = Tổng đơn · Tổng số SP · Tổng bán ·
                                   DS quy đổi · Tổng lợi nhuận ·
                                   So tháng trước · Target · So target ·
                                   Tỉ suất · Lợi nhuận thực nhận
                                   (áp dụng cho MỌI năm Summary, 2025 lẫn 2026)
                                   + doanh số tháng của chuỗi DataChart
UNAVAILABLE theo hợp đồng        = Tỉ lệ tồn kho · Thưởng · Ngày công ·
                                   Lương cơ bản · Phụ cấp · Tổng lương
OWNER_DECISION_REQUIRED          = KHÔNG CÓ
```

`UNAVAILABLE` trong bảng `REFERENCE_YEAR_CONTRACT` nay có nghĩa HẸP:
*không có trong sheet `DataChart`*. Nó KHÔNG còn là tuyên bố "năm 2025 không
có chỉ tiêu này" — tuyên bố đó thuộc về tình trạng nhập của `Summary 2025`,
và được ĐO chứ không được viết sẵn.

**Vì sao `COMPARABLE` rỗng.** Không phải vì thận trọng, mà vì mỗi cặp đều có
một phân kỳ ngữ nghĩa ĐÃ FREEZE ở PHB-02: chiết khấu (`S3`, `DEC-114`), DS quy
đổi bằng phép chia và dòng tổng cộng thiếu (`S4`, `X2`, `X6`), lợi nhuận KPI
chỉ chính thức khi coverage 100 % (`S14`, `DEC-PHB02-02`), số SP mang lỗi `A1`
(`X1`), cột `I` so trên sai chỉ tiêu (`X9`). Mở một cặp trong tương lai phải
bác được ĐÚNG lý do đã ghi ở dòng đó.

Điều này **không** giới hạn việc hiển thị: hiển thị và so sánh là hai câu
hỏi khác nhau (`DEC-177` §5).

### 3.4 Provenance phải thấy được

Mọi số cũ đi qua `legacy_presentation.cell()` — nơi DUY NHẤT gắn nhãn — nên
không có đường nào hiện một số legacy mà thiếu nhãn nguồn và đơn vị. Trang
`/lich-su` ghi thêm: `LEGACY_REFERENCE`, "Dữ liệu tham chiếu lịch sử", ô nguồn
(`DataChart 2026!AH`), kỳ suy ra từ đâu, và bản nhập đang xem.

### 3.5 Chỉ tiêu không có ⟹ dấu gạch, KHÔNG PHẢI 0

`S10` giữ nguyên: `NULL` không bao giờ là `0`; kỳ vắng mặt không bao giờ là
`−100 %`.

### 3.6 So sánh

Cổng `legacy_reference.compare()` chỉ tính chênh lệch khi bảng
`CROSS_ORIGIN_CONTRACT` cho phép cặp đó. V1: **mọi cặp đều bị chặn**, mỗi cặp
kèm lý do. Cổng đọc hợp đồng qua tham số chứ không cứng hoá câu trả lời —
`test_the_gate_reads_the_contract_instead_of_hardcoding_a_refusal` chứng minh
điều đó bằng một hợp đồng cho phép.

Tỉ lệ "so cùng kỳ năm trước" hiện ở trang Doanh số ngày là
`legacy_monthly_reference.vs_last_year_ratio` — **một số cũ đã lưu sẵn, do
Excel tính**, không phải phép so do công cụ này thực hiện. Nó là legacy↔legacy
và mang nhãn legacy như mọi ô cũ khác.

---

## 4. Mô hình lưu trữ

```text
LEGACY_STORAGE_MODEL   = TÁI DÙNG NGUYÊN TRẠNG bốn bảng legacy_* của TASK-PRA-001
SCHEMA_CHANGE_REQUIRED = NO — không bảng mới · không migration · không cột mới
```

Chỉ thị đính chính CHO PHÉP mở rộng schema nếu thật sự cần. Đánh giá lại sau
khi biết hình dạng 2025: **không cần**. `legacy_summary_row` đã khoá theo
`(year, month, seller_label, row_kind)` với đủ 16 cột `C..S` và không gắn
với năm nào, nên nó lưu được **cả period-level lẫn employee-level** của 2025
ngay lập tức. Quyền mở rộng chỉ được dùng khi có nhu cầu thật, và ở đây
không có.

Hệ quả kèm theo, đáng ghi vì nó tiết kiệm đúng phần việc rủi ro nhất: trang
`/nhan-vien` vốn đã year-agnostic (`available_periods()` + `query_summary()`
không giả định năm), nên nó phục vụ chi tiết nhân viên 2025 **ngay khi có
dòng 2025**, không cần sửa một dòng nào.

Phần PHB-04 thêm vào vẫn là CHỈ-ĐỌC: một phép chiếu (đổi khoá năm cho chuỗi
`DataChart`), một hợp đồng ngữ nghĩa, một phép đo tính sẵn có, và một trang
đọc. Không có đường ghi mới nào tồn tại để tạo dòng hàng giả, chạm Product
Identity/Tracking, hay sinh KPI-profit eligibility. Idempotency đến sẵn từ
`create_import()` (cùng fingerprint ⟹ trả bản cũ).

Thay đổi DUY NHẤT ở đường ghi là phạm vi parse: `Summary 2025` chuyển từ
"không đọc" sang `OPTIONAL_IMPORT`. Không cột nào, bảng nào, hay ràng buộc
nào đổi.

---

## 5. Điều hướng

Tab **"Lịch sử"** (`/lich-su`), năm khối:

1. **Chuỗi doanh số tháng của năm trước** (từ `DataChart!AH`).
2. **Năm lịch sử đã nhập** — mỗi năm: kỳ nào có số (mỗi kỳ là một liên kết
   mở thẳng bảng người bán của kỳ đó), có chi tiết theo nhân viên hay không
   và gồm những ai, và bảng tình trạng từng chỉ tiêu ĐO trên dòng thật.
   Kèm khối **"Phần lịch sử CHƯA đọc được"** khi còn dòng chưa phân loại.
3. **Đi tới kỳ** — mỗi kỳ dán nhãn `SỐ CŨ` / `SỐ MỚI` / cả hai.
4. **So số cũ với số mới ở đâu?** — bảng phán quyết từng cặp, kèm lý do.
5. **Chỉ tiêu lịch sử nào được hỗ trợ?** — hai hợp đồng, in nguyên văn.

Luồng chủ dự án cần (chỉ thị đính chính §6):

```text
Lịch sử → chọn năm → chọn tháng → bảng người bán × chỉ tiêu của kỳ đó
```

Bước cuối dùng lại trang `/nhan-vien` đã có, không dựng trang mới. Giữ
nguyên `P1` của PHB-02: **không** tái tạo mỗi tab bảng tính thành một tab
web. Kỳ có cả hai origin là MỘT dòng mang HAI nhãn — `DEC-166 E` cấm cộng
chung số cũ với số mới.

---

## 6. Quyết định của chủ dự án còn để mở (KHÔNG chặn V1)

```text
OD-PHB04-A  Kỳ có CẢ HAI origin: có bao giờ cần hiển thị MỘT con số duy nhất
            cho kỳ đó không, và nếu có thì nguồn nào thắng?
            V1 không cần trả lời — V1 hiện hai con số cạnh nhau, có nhãn.
            Chỉ trở thành câu hỏi chặn khi có yêu cầu hợp nhất.

OD-PHB04-B  Có kỳ 2026 nào TRƯỚC khi công cụ trở thành nguồn chính thức mà
            chủ dự án muốn coi là legacy "thuần", kể cả khi pipeline đã có số
            cho kỳ đó không? V1 không giả định: kỳ nào có origin nào thì hiện
            đúng origin đó.
```

Cả hai đều là câu hỏi MỞ RỘNG, không phải ngữ nghĩa bị treo. Không câu nào
chặn bất kỳ phần nào của V1.

---

## 7. Cố ý KHÔNG làm (`ANTI-SCOPE-CREEP`)

Target/PHB-05 · R1/R2/R3 của PHB-03 · Brand · Advanced Analytics · engine
bảng tính tổng quát · framework import lịch sử tổng quát · tương thích XLSX
tuỳ ý · thay đổi Product Identity · thay đổi Tracking · tối ưu giá nhập ·
thiết kế lại dashboard. Không mở lại `DEC-169`. Không mở lại PHB-03.

---

## 8. Bằng chứng thực thi (E1)

```text
FOCUSED  tests/test_phb04_legacy_reference.py       → 50 passed
FULL     python -m pytest -q                        → 2187 passed, 11 skipped
GOLDEN   4 file golden                              → 74 passed, 2 skipped

validate_structure            PASS
validate_project_state        PASS
validate_evidence             PASS (155 REQUIRED)
validate_task_completion      PASS (13 DONE task)
validate_reference_integrity  FAIL với ĐÚNG 3 reference REM-T06 đã biết
                              (baseline không đổi)
```

Baseline trước phiên: `2136 passed, 11 skipped`. Bản PHB-04 đầu: `2171`.
Bản đính chính: `2187`. Golden `74 passed, 2 skipped` không đổi ở cả ba mốc.

---

## 8b. Test cũ đã sửa vì phạm vi đổi (`DEC-177`)

10 bài test mã hoá phạm vi `DEC-169` cũ. Chúng được **cập nhật**, không bị
bỏ — và không bài guard nào bị hạ ngưỡng:

| File | Test | Đổi gì |
|---|---|---|
| `test_legacy_importer.py` | `sheet_visibility_state_is_recorded_as_imported` | `Summary 2025` nay CÓ trong `sheets_imported` (state `hidden`) |
| `test_legacy_repository.py` | `available_periods_lists_only_periods_that_exist` | kỳ `(2025, 1)` nay có mặt |
| `test_legacy_source_coverage.py` | `b_..._never_parsed_into_summary_rows` | → `b_a_classifiable_optional_sheet_is_parsed...` |
| | `b_..._never_persisted` | → `b_an_optional_sheet_is_persisted_with_the_legacy_origin` |
| | `b_..._absent_from_the_import_provenance` | → `b_the_optional_sheet_is_recorded_in_the_import_provenance` (khẳng định `scope`) |
| | `c_the_required_summary_sheet_is_still_imported` | đếm theo sheet thay vì đếm gộp |
| | `the_verifier_reports_reference_only_sheets_as_not_persisted` | → `the_verifier_checks_fidelity_of_imported_optional_rows` |
| | `the_verifier_fails_if_a_reference_only_row_ever_gets_persisted` | → `the_verifier_counts_unimported_optional_rows_without_failing` |
| | `a_well_formed_workbook_still_imports_with_no_unaccounted_rows` | 13 → `{2026: 13, 2025: 3}` |
| | `the_verifier_exits_zero_on_a_complete_faithful_import` | dòng output mới |
| `test_phb04_legacy_reference.py` | `TestSummary2025StaysOutOfScope` | → `TestSummary2025IsInScope` |

**Không bị đổi** (guard `DEC-168` / `FIND-PRA001-R01`, vẫn FAIL TO):
`f_a_required_sheet_that_would_import_nothing_fails_loudly` ·
`test_the_dec_168_guard_still_fires_on_a_required_sheet` (mới) ·
`a_value_only_reference_sheet_does_not_fail_production_import` (được SIẾT
thêm: nay còn khẳng định `Summary 2025` không nhập dòng nào ở ca đó).

---

## 9b. Câu hỏi của chủ dự án — bằng chứng từng câu (chỉ thị §11)

| # | Câu hỏi | Test |
|---|---|---|
| A | Tổng bán của một tháng 2025? | `test_a_total_historical_sales_for_a_2025_month` |
| B | Các chỉ tiêu Summary khác của tháng đó? | `test_b_the_other_accepted_summary_metrics_of_that_month` |
| C | Nhân viên nào có số trong kỳ? | `test_c_which_employees_had_data_that_month` |
| D | Chỉ tiêu của MỘT nhân viên? | `test_d_the_accepted_metrics_for_one_employee` |
| E | Mọi giá trị vẫn là `LEGACY_REFERENCE`? | `test_e_every_displayed_2025_value_stays_legacy_reference` |
| F | Không nhiễm coverage/lợi nhuận hiện hành? | `test_f_none_of_it_contaminates_current_engine_coverage` |
| G | Đi được từ Summary 2025 → chi tiết nhân viên? | `test_g_the_owner_can_navigate_from_2025_summary_to_employee_detail` |
| H | Chỉ tiêu không có hiện `—` chứ không phải 0? | `test_h_an_unavailable_2025_metric_shows_a_dash_not_a_zero` |
| H2 | Tính sẵn có được ĐO chứ không viết cứng? | `test_h2_an_available_2025_metric_is_measured_from_the_rows` |
| I | Không sinh phần trăm liên-origin? | `test_i_no_cross_engine_percentage_is_generated_for_2025` |

---

## 10. `NEED_OWNER_SOURCE` — phần duy nhất còn thiếu

```text
NEED_OWNER_SOURCE = nội dung thật của sheet `Summary 2025`
```

Năng lực đã sẵn sàng và đã có test; **dữ liệu thì chưa có trong repo.**
Workbook `Báo cáo Kinh doanh 2026.xlsx` không được commit (`data/samples/`
nằm trong `.gitignore` vì chứa dữ liệu cá nhân khách hàng) và không có trên
đĩa của phiên. Không artifact bằng chứng nào của repo từng quan sát nội dung
99 dòng đó — `evidence.json` chứa **0** lần chuỗi `"2025"`.

Chủ dự án cần cấp MỘT trong hai (không cần cả hai):

1. **Workbook thật.** Nếu `Summary 2025` còn giữ công thức (tham chiếu chéo
   sheet, hoặc `SUM`), contract phân loại hiện tại đọc được **ngay**, không
   cần sửa mã. Đây là đường ngắn nhất.

2. **Nếu sheet đó thật sự không có công thức nào** (đúng như đo lúc `DEC-169`):
   cần **nội dung cột nhãn `A`/`B` của 99 dòng** — tức mỗi dòng ghi chữ gì
   ("Mr Vinh", "Tổng T01", …). Từ đó dựng được một contract phân loại theo
   NHÃN cho sheet value-only.

**Vì sao KHÔNG tự viết contract theo nhãn ngay bây giờ.** Từ vựng nhãn của
`Summary 2025` chưa ai trong phiên này quan sát. Viết một bộ luật nhãn cho
một sheet chưa từng nhìn thấy là đoán — và đoán sai một dòng tổng thành một
người bán sẽ dựng ra một "nhân viên" không tồn tại, đúng thất bại mà
`DEC-168` / `FIND-PRA001-R01` sinh ra để chặn. Hôm nay công cụ nói thẳng còn
bao nhiêu dòng chưa đọc được, thay vì đoán.

Trong lúc chờ, hành vi trên workbook thật là: 2026 nhập bình thường, phần
`Summary 2025` báo rõ `N` dòng chưa đọc được kèm số dòng cụ thể.

---

## 11. Exit Criteria

| # | Điều kiện | Trạng thái | Bằng chứng |
|---|---|---|---|
| E1 | Hợp đồng Legacy Reference V1 tường minh | **PASS** | Mục 3; `app/web/legacy_reference.py` |
| E2 | Kỳ legacy được định nghĩa (gồm 2025) | **PASS** | Mục 3.1 |
| E3 | Chỉ tiêu legacy được hỗ trợ được định nghĩa, ĐO trên dòng thật | **PASS** | Mục 3.3; `summary_year_availability()` |
| E4 | Provenance tường minh | **PASS** | Mục 3.4; `TestProvenanceIsExplicit` |
| E5 | Tách biệt legacy/hiện hành được chứng minh | **PASS** | `TestLegacyStaysOutOfTheAccountingPipeline` |
| E6 | Không tạo lịch sử giao dịch giả | **PASS** | Không có đường ghi nào; mục 4 |
| E7 | Không nhiễm coverage của engine hiện tại | **PASS** | `test_f_none_of_it_contaminates...` |
| E8 | Điều hướng 2025 Summary → chi tiết nhân viên | **PASS** | `test_g_the_owner_can_navigate...` |
| E9 | So sánh được phép là hợp lệ về ngữ nghĩa | **PASS** | Mục 3.6 |
| E10 | So sánh không được phép thất bại an toàn | **PASS** | `TestComparisonGate` |
| E11 | `DEC-169` được đọc đúng, không diễn giải rộng | **PASS** | `DEC-177` §1; mục 2 |
| E12 | Guard `DEC-168` trên sheet REQUIRED không bị nới | **PASS** | `test_the_dec_168_guard_still_fires_on_a_required_sheet` |
| E13 | focused tests PASS | **PASS** | Mục 8 |
| E14 | full regression PASS | **PASS** | Mục 8 |
| E15 | golden tests PASS | **PASS** | Mục 8 |
| E16 | Nội dung thật của `Summary 2025` | **OWNER_SOURCE_REQUIRED** | Mục 10 |
| E17 | Independent review | **PENDING** | chưa thực hiện |
| E18 | Tài liệu dự án được cập nhật | **PASS** | file này · `PROJECT/PROJECT_PROGRESS.md` · `PROJECT/PROJECT_DECISIONS.md` (`DEC-176`, `DEC-177`) · `docs/reviews/PHB-04-legacy-reference-v1-implementation.md` |

```text
PHB_04 = IMPLEMENTED_AWAITING_REVIEW  (phần năng lực)
         + OWNER_SOURCE_REQUIRED      (phần nội dung Summary 2025 — mục 10)
```

`E17` chưa đóng ⟹ **KHÔNG** được gọi là `DONE`. `E16` không chặn phần còn
lại: mọi phần khác của V1 đã chạy và đã có bằng chứng.
