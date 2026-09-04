# PHB-04 — LEGACY REFERENCE V1

Status: IMPLEMENTED_AWAITING_REVIEW
Task Mode: MAJOR
Priority: REQUIRED
Evidence Level: E1
Executed By: S119 (Claude Code on the web)
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

## 2. Kết quả audit bằng chứng có sẵn (PHB-04 mục 4)

Audit trước khi thiết kế đã đổi HÌNH DẠNG của task này. Ba phát hiện:

**A. Nền lưu trữ legacy ĐÃ tồn tại và đã được nghiệm thu.** `TASK-PRA-001`
(DONE) dựng bốn bảng `legacy_*` với cột `origin` mang CHECK constraint
`origin = 'LEGACY_REFERENCE'`, cộng đường nhập workbook idempotent theo
fingerprint. PHB-04 vì vậy **không** thiết kế cơ chế lưu trữ mới, **không**
thêm bảng, **không** thêm migration.

**B. `Summary 2025` đã bị chủ dự án loại khỏi phạm vi bằng `DEC-169`** —
nguyên văn: *không import, không persist, không query, không display*. Sheet
đó cũng không có một ô công thức nào trên toàn bộ 755 dòng nên không dòng nào
phân loại được. PHB-04 **không** mở lại quyết định đó và **không** xây parser
cho 99 dòng value-only của sheet đó.

**C. Bằng chứng đã chấp nhận cho năm 2025 nằm ở CHỖ KHÁC.** `PHB-02` mục 5.6
`L2` chỉ đúng nguồn: cột `AH3:AH14` của `DataChart 2026` —
*"Doanh số cùng kỳ 2025 — số cứng"* (`docs/analysis/02_FORMULA_MAPPING.md` §5)
— đã được nhập sẵn thành `legacy_monthly_reference.sales_prev_year_vnd`.

Hệ quả: V1 của PHB-04 là một **phép chiếu chỉ-đọc** trên dữ liệu đã có, cộng
một hợp đồng ngữ nghĩa tường minh. Không có dữ liệu mới nào được tạo ra.

---

## 3. Hợp đồng Legacy Reference V1 (FROZEN)

### 3.1 Kỳ nào là LEGACY_REFERENCE?

Hai lớp kỳ, cùng `origin = LEGACY_REFERENCE`, khác nhau ở chỗ lấy số:

| Lớp kỳ | Kỳ | Nguồn ô | Chỉ tiêu có bằng chứng |
|---|---|---|---|
| `REFERENCE_YEAR` | các tháng của năm TRƯỚC năm workbook (với workbook 2026 → 2025) | `DataChart 2026!AH3:AH14` | **duy nhất** doanh số tháng (VND) |
| `WORKBOOK_YEAR` | các tháng của năm workbook có dòng người bán trong `Summary 2026` | `Summary 2026` C..S + `DataChart 2026` | 16 cột `C..S` (`L6`) |

Năm trước được suy ra bằng `row.year - 1`, **không hard-code 2025** — workbook
của năm sau tự sinh đúng kỳ tham chiếu của nó.

Ô `AH` trống ⟹ **không** phải một kỳ có dữ liệu. Nó hiện dấu gạch, và nó
không xuất hiện trong danh mục điều hướng.

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
(`REFERENCE_YEAR_CONTRACT`, `WORKBOOK_YEAR_CONTRACT`) — mỗi dòng mang lý do và
đường dẫn bằng chứng, và trang `/lich-su` in nguyên văn bảng đó ra cho chủ dự
án đọc. Tóm tắt:

```text
COMPARABLE               = KHÔNG CÓ CHỈ TIÊU NÀO (V1)
REFERENCE_ONLY (2025)    = Doanh số tháng
UNAVAILABLE   (2025)     = Tổng đơn · Tổng số SP · DS quy đổi · Tổng lợi nhuận ·
                           Target · chi tiết theo nhân viên · doanh số theo ngày
REFERENCE_ONLY (workbook)= Tổng đơn · Tổng số SP · Tổng bán · DS quy đổi ·
                           Tổng lợi nhuận · So tháng trước · Target · So target ·
                           Tỉ suất · Lợi nhuận thực nhận
UNAVAILABLE   (workbook) = Tỉ lệ tồn kho · Thưởng · Ngày công · Lương cơ bản ·
                           Phụ cấp · Tổng lương
OWNER_DECISION_REQUIRED  = KHÔNG CÓ (mọi ngữ nghĩa V1 đã có thẩm quyền)
```

**Vì sao `COMPARABLE` rỗng.** Không phải vì thận trọng, mà vì mỗi cặp đều có
một phân kỳ ngữ nghĩa ĐÃ FREEZE ở PHB-02: chiết khấu (`S3`, `DEC-114`), DS quy
đổi bằng phép chia và dòng tổng cộng thiếu (`S4`, `X2`, `X6`), lợi nhuận KPI
chỉ chính thức khi coverage 100 % (`S14`, `DEC-PHB02-02`), số SP mang lỗi `A1`
(`X1`), cột `I` so trên sai chỉ tiêu (`X9`). Mở một cặp trong tương lai phải
bác được ĐÚNG lý do đã ghi ở dòng đó.

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
LEGACY_STORAGE_MODEL = TÁI DÙNG NGUYÊN TRẠNG bốn bảng legacy_* của TASK-PRA-001.
                       KHÔNG bảng mới · KHÔNG migration · KHÔNG cột mới.
PHB-04 THÊM          = một phép CHIẾU CHỈ-ĐỌC (đổi khoá năm, không tính lại)
                       + một hợp đồng ngữ nghĩa + một trang đọc.
```

Điều này thoả toàn bộ ràng buộc của PHB-04 mục 6 **bằng cấu trúc, không bằng
kỷ luật**: không có đường ghi nào tồn tại để tạo dòng hàng giả, chạm Product
Identity, chạm Tracking, hay sinh KPI-profit eligibility. Xoá/nhập lại dữ liệu
kế toán hiện hành không thể làm đổi một con số lịch sử nào vì hai origin nằm ở
hai nhóm bảng tách biệt.

Idempotency đến sẵn từ `LegacyRepository.create_import()`: cùng fingerprint ⟹
trả bản cũ, không tạo bản mới.

---

## 5. Điều hướng

Tab mới **"Lịch sử"** (`/lich-su`). Ba khối: kỳ tham chiếu năm trước · danh
mục kỳ (mỗi kỳ ghi rõ có `SỐ CŨ` / `SỐ MỚI` / cả hai, kèm liên kết sang đúng
trang) · hợp đồng chỉ tiêu và bảng "so được ở đâu".

Giữ nguyên `P1` của PHB-02: **không** tái tạo mỗi tab bảng tính thành một tab
web. Kỳ có cả hai origin là MỘT dòng mang HAI nhãn — `DEC-166 E` cấm cộng
chung số cũ với số mới, và PHB-04 không xin ngoại lệ.

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
FOCUSED  tests/test_phb04_legacy_reference.py       → 35 passed
FULL     python -m pytest -q                        → 2171 passed, 11 skipped
GOLDEN   4 file golden                              → 74 passed, 2 skipped

validate_structure            PASS
validate_project_state        PASS
validate_evidence             PASS (155 REQUIRED)
validate_task_completion      PASS (13 DONE task)
validate_reference_integrity  FAIL với ĐÚNG 3 reference REM-T06 đã biết
                              (baseline không đổi)
```

Baseline trước phiên: `2136 passed, 11 skipped` — chênh lệch `+35` đúng bằng
số test mới, không test nào cũ bị đổi hay bị bỏ.

---

## 9. Exit Criteria

| # | Điều kiện | Trạng thái | Bằng chứng |
|---|---|---|---|
| E1 | Hợp đồng Legacy Reference V1 tường minh | **PASS** | Mục 3; `app/web/legacy_reference.py` |
| E2 | Kỳ legacy được định nghĩa | **PASS** | Mục 3.1 |
| E3 | Chỉ tiêu legacy được hỗ trợ được định nghĩa | **PASS** | Mục 3.3 |
| E4 | Provenance tường minh | **PASS** | Mục 3.4; `TestProvenanceIsExplicit` |
| E5 | Tách biệt legacy/hiện hành được chứng minh | **PASS** | `TestLegacyStaysOutOfTheAccountingPipeline` |
| E6 | Không tạo lịch sử giao dịch giả | **PASS** | Không có đường ghi nào; mục 4 |
| E7 | Không nhiễm coverage của engine hiện tại | **PASS** | `TestLegacyDoesNotTouchCurrentProfitCoverage` |
| E8 | Điều hướng chạy | **PASS** | `TestNavigationDistinguishesOrigins` |
| E9 | So sánh được phép là hợp lệ về ngữ nghĩa | **PASS** | Mục 3.6 |
| E10 | So sánh không được phép thất bại an toàn | **PASS** | `TestComparisonGate` |
| E11 | focused tests PASS | **PASS** | Mục 8 |
| E12 | full regression PASS | **PASS** | Mục 8 |
| E13 | golden tests PASS | **PASS** | Mục 8 |
| E14 | Independent review | **PENDING** | chưa thực hiện |
| E15 | Tài liệu dự án được cập nhật | **PASS** | file này · `PROJECT/PROJECT_PROGRESS.md` · `PROJECT/PROJECT_DECISIONS.md` · `docs/reviews/PHB-04-legacy-reference-v1-implementation.md` |

```text
PHB_04 = IMPLEMENTED_AWAITING_REVIEW
```

`E14` chưa đóng ⟹ **KHÔNG** được gọi là `DONE`.
