# PHB-02 — BUSINESS PARITY CONTRACT (ĐỀ XUẤT, CHỜ OWNER)

Status: AWAITING_OWNER
Task Mode: MAJOR (audit-only vertical — không có production code trong phiên dựng tài liệu này)
Nguồn thẩm quyền: Owner > báo cáo tay của Owner > tài liệu Phase B đã chấp nhận >
hành vi production hiện tại của Reports > mã nguồn > test > suy diễn.

Tài liệu này **chưa phải hợp đồng đã freeze**. Nó là hợp đồng ĐỀ XUẤT, kèm
đúng bảy quyết định mà chỉ Owner mới có thẩm quyền trả lời. Freeze PHB-02 chỉ
xảy ra sau khi bảy quyết định đó được trả lời.

Câu hỏi trung tâm của PHB-02:

> *Thông tin nghiệp vụ và quy trình nào trong báo cáo tay của Owner bắt buộc
> Reports phải bảo toàn hoặc thay thế, để ứng dụng web thật sự thay được quy
> trình báo cáo thủ công?*

Đây **không** phải bài tập clone giao diện Excel. Kết luận "55 tab Excel ⟹ 55
tab web" bị bác bỏ ngay từ đầu (xem mục 5.3).

---

## 1. Target Gate

```text
EXPECTED_HEAD   = eaa3fdeb4ffdfd2d5772314ac24cf8a1273cc67e
OBSERVED_HEAD   = eaa3fdeb4ffdfd2d5772314ac24cf8a1273cc67e   → KHỚP
DEFAULT_BRANCH  = claude/extract-upload-repo-gq2ws4 (origin HEAD branch)
SESSION_BRANCH  = claude/business-parity-contract-me80ij
                  (0 ahead / 0 behind default tại thời điểm mở phiên)
WORKTREE        = sạch
PHB-01          = DONE      (PROJECT/PROJECT_PROGRESS.md, khối canonical S112)
PHB-02          = CURRENT   (NEXT_VERTICAL_ACTION của cùng khối)
TARGET_GATE     = PASS
```

Sức khoẻ HEAD tại thời điểm audit (E1, thực thi trong phiên):

```text
python -m pytest tests/ -q            → 2032 passed, 11 skipped in 89.95s
python -m pytest tests/test_golden_baseline.py -q → 58 passed, 2 skipped
validate_structure           → PASS (21 required path)
validate_project_state       → PASS
validate_evidence            → PASS (155 REQUIRED PASS)
validate_task_completion     → PASS (13 DONE task)
validate_reference_integrity → FAIL với ĐÚNG 3 reference REM-T06 đã biết
                               (baseline không đổi, không phát sinh mới)
```

---

## 2. Định vị báo cáo tay của Owner

Phải phân biệt ba loại artifact, vì lẫn chúng là cách nhanh nhất để dựng một
hợp đồng parity sai:

| Loại | Artifact | Có trong phiên này? |
|---|---|---|
| RAW ACCOUNTING INPUT | `data/samples/So_chi_tiet_ban_hang.xlsx` (11.765 dòng, 8.714 Số BH, 01/01–30/06/2026) | KHÔNG (PII, `.gitignore`) |
| **OWNER MANUAL REPORT** | **`data/samples/Bao_cao_Kinh_doanh_2026.xlsx`** — 59 sheet: 56 sheet nhân viên-tháng (01.2026–08.2026) + `Summary 2025` + `Summary 2026` + `DataChart 2026` | **KHÔNG** (PII, `.gitignore`) |
| LEGACY_REFERENCE | `Summary 2025` (REFERENCE_ONLY, DEC-169) và mọi báo cáo tay trước kỳ hiện hành | KHÔNG |

```text
MANUAL_REPORT_AVAILABLE = NO   (file .xlsx không có trong session — đúng chính sách PII)
```

**Nhưng cấu trúc nghiệp vụ của nó KHÔNG bị bịa ra ở đây.** Nó được trích xuất
một lần, có kịch bản tái tạo được, và đã commit:

- `docs/analysis/_evidence/evidence.json` — trích xuất máy, sinh bởi
  `tools/analysis/extract_evidence.py`. Chứa `report.layouts` (6 biến thể
  layout + công thức dòng 1 nguyên văn), `report.sheet_totals` (56 tổng
  sheet), `report.conversion_rows` (56 dòng `Summary 2026`: công thức quy
  đổi, target, công thức thưởng, ngày công), `report.manual_price_overrides`
  (635/18.148 ô giá bị gõ tay).
- `docs/analysis/01..07, 10_*.md` — sáu tài liệu bắt buộc của mục 27 đặc tả,
  **đã được Owner duyệt** (GATE-00, DEC-122, 2026-08-23).

Vì vậy:

```text
MANUAL_REPORT_STRUCTURE_AVAILABLE = YES (qua trích xuất đã chấp nhận, thẩm quyền mức 3)
```

Mọi kết luận parity dưới đây trích từ hai nguồn trên hoặc từ mã nguồn/fixture
tại `EXPECTED_HEAD`. **Không có cấu trúc sheet nào được suy đoán.** Các câu
hỏi mà trích xuất không trả lời được đều bị đánh dấu `AMBIGUOUS` chứ không
được điền bằng phỏng đoán.

---

## 3. Năng lực hiện tại của Reports tại `EXPECTED_HEAD`

Phân biệt nghiêm ngặt **DISPLAY EXISTS** (có ô trên màn hình) với
**BUSINESS SEMANTICS VERIFIED** (nghĩa nghiệp vụ đã được chứng minh, không
suy ra từ việc nhãn trông giống nhau).

### 3.1 SỐ MỚI — do pipeline tính

| # | Năng lực | Bề mặt | Display | Semantics |
|---|---|---|---|---|
| A | Tổng quan kỳ — 10 ô | `/tong-quan` | CÓ | VERIFIED (`analytics_queries.period_totals`) |
| A1 | Tổng đơn (`COUNT DISTINCT order_key`) | `/tong-quan`, `/nhan-vien?nguon=moi` | CÓ | VERIFIED |
| A2 | Dòng hàng (mẫu số của mọi coverage) | như trên | CÓ | VERIFIED |
| A3 | Tổng số lượng | như trên | CÓ | VERIFIED — nhưng **cố ý KHÁC** "Tổng số SP" của báo cáo tay (D3) |
| A4 | Doanh thu (net) | như trên | CÓ | VERIFIED — `sell_price × quantity − discount` (DEC-114) |
| A5 | Lợi nhuận KPI + coverage | như trên | CÓ | VERIFIED công thức; **coverage thấp**, xem mục 4.4 |
| A6 | Lợi nhuận kế toán | KHÔNG render | backend only | VERIFIED — gỡ khỏi UI theo `OWNER_PRESENTATION_DECISION` KPI-first (2026-09-03) |
| A7 | Đơn AUTO / Đơn cần kiểm tra | `/tong-quan` | CÓ | VERIFIED (theo ĐƠN: một đơn PENDING nếu có ≥1 dòng PENDING) |
| A8 | Dòng chưa có ngày bán | `/tong-quan` | CÓ | VERIFIED |
| B | Nhân viên — 7 cột | `/nhan-vien?nguon=moi` | CÓ | VERIFIED (`employee_totals`, `GROUP BY employee_normalized, employee_group`) |
| C | So kỳ trước (Δ tuyệt đối + Δ %) | `/tong-quan` | CÓ | VERIFIED — chỉ 2 chỉ tiêu (Tổng đơn, Doanh thu), chỉ khi đang xem MỘT tháng |
| D | Danh sách đơn + chi tiết đơn | `/ban-hang`, `/ban-hang/<order_key>` | CÓ | VERIFIED |
| E | Mặt hàng trên chứng từ | `/san-pham` | CÓ | VERIFIED — gộp theo **mô tả thô đã chuẩn hoá**, KHÔNG phải canonical identity, KHÔNG phải ProductGroup |
| F | Review / Pending | `/du-lieu`, cột trạng thái | CÓ | VERIFIED |
| G | Nhãn nguồn dữ liệu | badge `SỐ MỚI` / `SỐ CŨ` trên mọi số | CÓ | VERIFIED — hai loại số không bao giờ được cộng chung |

### 3.2 SỐ CŨ — legacy reference (chỉ đọc, không tính lại)

| # | Năng lực | Bề mặt | Ghi chú |
|---|---|---|---|
| H | Ma trận `Summary 2026` tháng × người bán — 8 cột: Tổng đơn · Tổng số SP · Tổng bán · **DS quy đổi** · Tổng lợi nhuận · So tháng trước · **Target** · So target | `/nhan-vien` (mặc định) | Giá trị Excel nguyên trạng, đơn vị kVND, badge `SỐ CŨ`, ô có lỗi công thức mang dấu (i) |
| I | `DataChart 2026` — doanh số theo ngày + tham chiếu tháng (cùng kỳ năm trước, so target, target/ngày) | `/doanh-so-ngay` | Đơn vị VND nguyên |

`legacy_summary_row` lưu đủ **16 cột** của `Summary 2026` (C..S), kể cả
`bonus`, `workdays`, `base_salary`, `allowance`, `total_salary` — nghĩa là
không có thông tin nào của Summary tay bị mất khi số hoá.

### 3.3 Khoảng trống đã đo được của SỐ MỚI

| Năng lực có trong báo cáo tay | Trạng thái trên đường pipeline |
|---|---|
| **DS quy đổi** (cột `F` Summary) | **NOT_IMPLEMENTED.** `conversion_rate_final` được tính và lưu **theo từng dòng** (`order_line_result_version`), nhưng **không có phép tổng hợp `converted_revenue` nào** trong `app/web/*`, trong `tools/db/schema.py` phía pipeline, hay trong exporter. `converted_revenue` chỉ tồn tại ở đường legacy. |
| **Target / So target** (cột `M`, `N`) | **NOT_IMPLEMENTED** trên pipeline — `OWNER_DECISION` D2 khoá cứng: cấm sao chép `legacy_summary_row.target` vào bất kỳ chỉ tiêu `PIPELINE_GENERATED` nào (DEC-166 E). |
| **Tỉ suất lợi nhuận** (cột `H` = `G/E`) | **NOT_IMPLEMENTED** — LATER, tử số chưa được Owner chọn (N.7). |
| **Tỉ lệ tồn kho** (cột `J`, từ `Nơi nhập = "Kho"`) | **DEFER** — cột `Nơi nhập` không tồn tại trong file ERP thô. |
| **Thưởng / ngày công / lương** (cột `O`–`S`) | **DEFER** (N.9) — luật HR, ngoài đặc tả Reports. |
| **Dòng "Gia dụng"** như một thực thể báo cáo | **NOT_IMPLEMENTED.** Xem mục 4.5 — đây là thay đổi mô hình có chủ đích (ADR-106/DEC-127), không phải thiếu sót. |
| **Cùng kỳ năm trước / YTD** | Một phần: `DataChart 2026` đã import mang `sales_prev_year_vnd`. `Summary 2025` = `REFERENCE_ONLY`, **không import** (DEC-169). |

---

## 4. Đối chiếu số thật — bằng chứng quyết định

Đây là phần quan trọng nhất của PHB-02. Ba nguồn được đối chiếu trên **cùng
một kỳ, cùng một nhân viên**, tất cả đều là artifact đã commit:

- **BC** = báo cáo tay của Owner (`evidence.json → report.sheet_totals`)
- **THÔ** = sổ ERP (`evidence.json → raw_by_month_employee`)
- **REPORTS** = kết quả pipeline tại `EXPECTED_HEAD`
  (`tests/fixtures/golden/expected/period_2026_*.json`, sinh từ workbook
  production thật đã ẩn danh, `pipeline_entry_point = app.pipeline.run_import`)

### 4.1 `01.2026 Tín Phát`

| Chỉ tiêu | BC (tay) | THÔ (ERP) | REPORTS | Đọc |
|---|---:|---:|---:|---|
| Tổng đơn | **254** | **254** | **254** | **KHỚP TUYỆT ĐỐI** |
| Tổng SP / số lượng | 387,6271681 | 407 | 407 | BC sai công thức (A1); Reports = THÔ |
| Tổng bán (gộp) | 3.544.010 k | **3.564.610 k** | **3.564.610.000 VND** | **Reports = THÔ TUYỆT ĐỐI**; BC thấp hơn 20.600 k (0,58 %) |
| Doanh thu net | — | — | 3.562.310.000 VND | net = gộp − chiết khấu 2.300.000 (DEC-114) |
| Lợi nhuận | 238.115 k (KPI) / 238.775 k (gộp) | 240.033 k (ERP) | **KHÔNG TÍNH ĐƯỢC** | `price_source_distribution = {"Pending": 351}` — 351/351 dòng |

### 4.2 `06.2026 Tín Phát`

| Chỉ tiêu | BC (tay) | THÔ (ERP) | REPORTS | Đọc |
|---|---:|---:|---:|---|
| Tổng đơn | **146** | **146** | **146** | **KHỚP TUYỆT ĐỐI** |
| Tổng SP / số lượng | 178,8029801 | 210 | 210 | như trên |
| Tổng bán (gộp) | 1.799.920 k | **1.925.272 k** | **1.924.872.000 VND** (net, sau chiết khấu 400.000) | Reports = THÔ; BC thấp hơn 6,5 % |
| Lợi nhuận | 119.236 k | 95.957 k (ERP) | **KHÔNG TÍNH ĐƯỢC** | `{"Pending": 180}` — 180/180 dòng |

### 4.3 Kết luận bắt buộc rút ra từ hai bảng trên

**Báo cáo tay KHÔNG phải một oracle số học tái tạo được.**

Ba bằng chứng độc lập cùng chỉ một hướng:

1. `01.2026`: BC **thấp hơn** ERP 0,58 % ở doanh số nhưng **thấp hơn** 0,8 % ở
   lợi nhuận.
2. `06.2026`: BC **thấp hơn** ERP 6,5 % ở doanh số nhưng **CAO HƠN** ERP
   24,3 % ở lợi nhuận (119.236 vs 95.957). Lệch **hai chiều ngược nhau trong
   cùng một sheet** — không thể giải thích bằng một quy tắc duy nhất.
3. `report.manual_price_overrides = 635/18.148` — 635 ô giá nhập bị gõ tay
   thay vì công thức, và **không có dấu vết nào trong file cho biết ô nào,
   vì sao, ai sửa**.

Cộng thêm việc số đơn BC lệch tới 9 đơn ở một số kỳ-nhân-viên (ví dụ
`06.2026 Ly`: BC 98 đơn > THÔ 89 đơn — báo cáo có nhiều hơn nguồn), kết luận
là:

> Báo cáo tay chứa các **quyết định nghiệp vụ của con người** (loại trừ đơn,
> điều chỉnh giá nhập KPI) chồng lên số ERP, và những quyết định đó **không
> được ghi lại ở đâu cả**. Reports tái tạo sổ ERP một cách chính xác tuyệt
> đối. Sự chênh lệch giữa hai bên **không phải lỗi của Reports**.

Hệ quả trực tiếp cho hợp đồng parity: **`MUST_MATCH` không thể có nghĩa "khớp
con số trong báo cáo tay"**, vì con số đó không phải hàm của bất kỳ đầu vào
nào Reports có. `MUST_MATCH` chỉ có nghĩa "khớp định nghĩa nghiệp vụ đã được
chấp nhận, tính trên nguồn đã được chấp nhận". Đây chính là **Câu hỏi Owner
Q1**.

### 4.4 Lợi nhuận KPI — chỉ tiêu quản trị chính, và nó chưa có

Trên cả hai kỳ golden, **100 % dòng có `price_source = "Pending"`** ⟹
`accounting_profit` và `eligible_kpi_profit` đều `NULL` ⟹ ô "Lợi nhuận KPI"
hiện `—` với coverage `0 / 351` (đường `run_import` trần) hoặc `2 / 351`
(đường production có nạp historical-confirmed registry — xem
`FIND-PRA003-01`). Trên production thật kỳ 09/2026, coverage đo được là
**34 / 142 dòng** (khối canonical `TASK-PRA-005`, S111).

Điều này quan trọng vì trong báo cáo tay, **Lợi nhuận KPI là gốc của mọi thứ
khác**:

```
Lợi nhuận KPI (cột I) → DS quy đổi (cột F = I/tỉ lệ) → % Target (cột N = F/M)
                                                     → Thưởng (cột O = F × %)
```

Không có Lợi nhuận KPI phủ đủ, **không có DS quy đổi, không có % Target,
không có thưởng**. Đây là **Câu hỏi Owner Q2**.

### 4.5 Tỉ lệ quy đổi — điểm khớp ngữ nghĩa đã được chứng minh

`conversion.scheme_distribution = {"ADS_7_5@0.075": 351}` trên `01.2026 Tín
Phát`, provenance `Auto:LeadSource`. Báo cáo tay dùng đúng `=G6/7.5%` cho Tín
Phát ở mọi kỳ.

Toàn bộ bảng tỉ lệ quan sát trong báo cáo tay được `config/conversion_rates.yaml`
tái hiện đúng:

| Đối tượng trong BC tay | Tỉ lệ BC | Dòng scheme tương ứng |
|---|---|---|
| Ly, Thắng, Linh, Fanpage | 5,5 % | `* + PERSONAL → PERSONAL_5_5` |
| Tín Phát | 7,5 % | `* + ADS → ADS_7_5` (mặc định NV, DEC-109/DEC-119) |
| Nội thành | 2 % | `NOI_THANH + PERSONAL + DIEN_MAY → NOI_THANH_2` |
| Gia dụng | 8 % | `NOI_THANH + PERSONAL + GIA_DUNG → GIA_DUNG_8` |
| Hoàng, Kiên | `(G−X)/5,5% + X/7,5%` gõ tay | hai bucket sinh tự động từ `lead_source_final` cấp đơn |

**Nhưng** `conversion.product_group_provenance = {"DEFAULT": 351}` — 100 %
dòng rơi về `DIEN_MAY` theo fallback, **không dòng nào được phân loại
ProductGroup thật**. `DefaultProductGroupProvider` trả `None` cho mọi dòng,
cố ý (ADR-106 §6 / DEC-127 §5: Phase 1 phân loại 100 % thủ công, chưa có UI).

⟹ Hai dòng scheme `NOI_THANH_2` và `GIA_DUNG_8` **hiện không bao giờ được
kích hoạt đúng**, và dòng báo cáo "Gia dụng" của báo cáo tay **không tái tạo
được**. Đây là **Câu hỏi Owner Q5**.

---

## 5. Phân loại parity

Mỗi mục có bằng chứng hoặc lý do. Mục nào không có bằng chứng thì nằm ở
`AMBIGUOUS` / câu hỏi Owner, không nằm ở đây.

### 5.1 MUST_MATCH — kết quả số phải khớp định nghĩa nghiệp vụ đã chấp nhận

Chỉ hai chỉ tiêu đã được **chứng minh** khớp hôm nay. Không suy rộng.

| # | Chỉ tiêu | Định nghĩa chấp nhận | Bằng chứng |
|---|---|---|---|
| M1 | **Số đơn** theo (nhân viên, tháng) | `COUNT DISTINCT` mã đơn — tương đương `count(Trans)` của sheet cá nhân | 254=254=254 và 146=146=146 (mục 4.1/4.2); 9/30 kỳ khớp tuyệt đối, ≤3 đơn ở 22/30 kỳ trên toàn dataset |
| M2 | **Tổng bán gộp** theo (nhân viên, tháng) so với **sổ ERP** | `Σ (Giá bán × SL)` trước chiết khấu | `sales_raw_gross = 3.564.610.000` ≡ `raw…sales_thousands = 3.564.610` — khớp đến từng đồng |

`M1`/`M2` là các neo parity. **Chúng không khớp con số của báo cáo tay** và
theo mục 4.3 thì không được phép khớp. Việc chốt điều này là Q1.

### 5.2 MUST_PRESERVE_SEMANTICS — nghĩa nghiệp vụ phải tương đương, cách trình bày có thể khác

| # | Ngữ nghĩa | Ràng buộc | Nguồn |
|---|---|---|---|
| S1 | Lợi nhuận KPI = `(SellPrice − KpiPurchasePrice) × Qty − Discount` | `EligibleCosts = {}` (closed empty set, KHÔNG phải fallback `0`); `DeliveryCost` NOT ELIGIBLE; `OtherKpiAdjustment = 0` | DEC-143 / `OD-108B-01` |
| S2 | Hai cột giá nhập giữ hai vai trò khác nhau | `L` Giá thực nhập → `AccountingPurchasePrice`; `F` Giá nhập TT → `KpiPurchasePrice` = `L + KpiPurchaseAdjustment` | `docs/analysis/02_FORMULA_MAPPING.md` §1 |
| S3 | Chiết khấu trừ vào **cả** doanh số **và** lợi nhuận | Doanh thu net ≠ "Tổng bán" của BC tay — đây là **phân kỳ có chủ đích, Owner đã quyết** | DEC-114, DEC-122 (C4b) |
| S4 | DS quy đổi = **tổng của các bucket**, không bao giờ là một tỉ lệ pha trộn | `Σ(LN KPI theo lead_source ÷ rate(NV, group, lead_source, product_group, **ngày của đơn**))`. Cấm tuyệt đối mọi đường code chia một lợi nhuận gộp cho một tỉ lệ duy nhất | DEC-119, DEC-120, ADR-106 §4 |
| S5 | `X` (phần lợi nhuận ADS) **không còn là đầu vào** | `X` gõ tay của Hoàng/Kiên thay bằng tổng có truy vết từ phân loại `lead_source` cấp đơn | `docs/analysis/02_FORMULA_MAPPING.md` §4 |
| S6 | Tỉ lệ tra theo **ngày của đơn**, không theo "hôm nay" | `effective_from`/`effective_to`; in lại báo cáo tháng 3/2026 vào năm 2028 phải ra cùng số | DEC-121 |
| S7 | Danh tính nhân viên được bảo toàn | Vinh/Quý/Hiệp là **ba** Employee thật thuộc group `NOI_THANH` — KHÔNG gộp thành một Employee giả tên "Nội thành" | DEC-127 §1 |
| S8 | Đổi tên/vào-ra giữa chừng dùng `effective_from`/`effective_to` | Linh (03.2026) và Fanpage (04–05.2026) là **cùng một thực thể**, khác tên hiển thị | `docs/analysis/05_EXCEPTIONS.md` B3 |
| S9 | Loại trừ thủ công thầm lặng → **Review Queue tường minh** | Đơn bị bỏ khỏi BC tay không dấu vết ⟹ trong Reports phải là một mục có lý do, có người quyết | đặc tả §18, DEC-128 |
| S10 | `NULL` không bao giờ là `0`; kỳ trước vắng mặt không bao giờ là `−100 %` | Ô trống hiện `—`; mọi ô lợi nhuận đi kèm coverage `N / M dòng` | `analytics_presentation.py`, quy tắc P4 |
| S11 | `SỐ CŨ` và `SỐ MỚI` không bao giờ cộng chung | badge nguồn bắt buộc trên mọi con số | DEC-166 E, `TASK-PRA-001` |
| S12 | Lợi nhuận kế toán vẫn tồn tại ở backend | Gỡ khỏi management UI là quyết định trình bày, KHÔNG phải xoá khỏi mô hình | `OWNER_PRESENTATION_DECISION`, 2026-09-03 |

### 5.3 MAY_IMPROVE_PRESENTATION — cơ học bảng tính, không cần tái tạo

| # | Yếu tố của báo cáo tay | Thay bằng |
|---|---|---|
| P1 | **56 sheet nhân viên-tháng** | **Một** trang + bộ chọn kỳ + chiều nhân viên. Không có bằng chứng nào cho thấy sheet riêng mang ngữ nghĩa nghiệp vụ ngoài việc là nơi chứa dữ liệu: cả 56 sheet chỉ có **6 biến thể layout**, và 4 trong 6 chỉ khác nhau ở ký tự rác ô `R1` (`,` hoặc `.`) và vùng công thức bị kéo tay. **Không cần một tab web cho mỗi nhân viên.** |
| P2 | Dòng tổng ngày/tháng nằm **lẫn trong vùng dữ liệu** | `RowType` (`DETAIL`/`DAY_TOTAL`/`MONTH_TOTAL`) + outline row của Excel khi xuất; dòng dữ liệu chỉ là dữ liệu (DEC-115) |
| P3 | Bố cục Summary một bảng phẳng 16 cột | Thẻ KPI + bảng + drill-down + bộ lọc |
| P4 | Thứ tự và tên cột Excel | Tự do, miễn giữ ngữ nghĩa mục 5.2 |
| P5 | Ô rác `R1` (`,` / `.`), `COUNTIF` bắt đầu từ dòng tiêu đề | Không tái tạo |

### 5.4 DEFER — hữu ích, không thuộc lần giao parity đầu tiên

| # | Năng lực | Lý do |
|---|---|---|
| D1 | Tỉ suất lợi nhuận (margin) | Tử số chưa được Owner chọn — N.7 (xem Q7) |
| D2 | Cùng kỳ năm trước / YTD | Cần `Summary 2025`, hiện `REFERENCE_ONLY` — PHB-04 |
| D3 | Xu hướng nhân viên nhiều tháng | Cần ≥3 tháng dữ liệu pipeline |
| D4 | Average order value | Không tồn tại trong báo cáo tay — không phải parity |
| D5 | Sales mix `employee_group` × `product_group` | Chặn bởi ProductGroup chưa phân loại (Q5) |
| D6 | Top-N nhân viên trên Tổng quan; Δ kỳ trước theo nhân viên | `USEFUL_BUT_DEFER` — trang Nhân viên đã trả lời đủ |
| D7 | Thưởng / ngày công / lương cứng / phụ cấp (cột `O`–`S`) | Luật HR, ngoài đặc tả Reports — N.9 |
| D8 | Tỉ lệ tồn kho (cột `J`) | Cột `Nơi nhập` không có trong file ERP; lấy từ Tracking sẽ là `ARCHITECTURE_DEPENDENCY` |
| D9 | **UX-PI-01 — Inline Product Identity Resolution** | Chưa có vị trí backlog canonical trong repo; ghi tại đây để không mất. Ý định: sau khi Reports phát hiện các mô tả chưa phân giải, Owner phân loại được ngay từ UI của Reports, trong khi **Tracking vẫn là Product Identity Authority** và là nơi validate/persist quyết định. `NB-6` (bất nhất thị giác của modal "Phân loại theo tên hàng" bên Tracking) có thể được hấp thụ vào UX-PI-01. **KHÔNG thiết kế API, KHÔNG implement trong PHB-02.** |

### 5.5 DROP_INTENTIONALLY — cố ý không tái tạo

| # | Yếu tố | Vì sao bỏ |
|---|---|---|
| X1 | `E1 = SUM(E3:E945) − D1 − C1` | Trừ một **tỉ lệ phần trăm** khỏi một **số lượng**. Sinh ra mọi "Tổng số SP" thập phân (387,6 / 178,8 / 62,6). Lỗi A1 |
| X2 | `F` dòng tổng tháng = `SUM(F4:F8)` | Bỏ sót **cả Nội thành lẫn Gia dụng**; riêng tháng 01.2026 thiếu **60,0 %** tổng DS quy đổi. Ba cột cùng dòng tổng có ba phạm vi khác nhau. Lỗi A2 → thay bằng cấu hình `include_in_company_total` tường minh (Q4) |
| X3 | Phép `/2` bù layout ở sheet kênh và `Summary!E3` | Bù cho việc dòng tổng nằm lẫn trong vùng `SUM`. DEC-115: một `/2` trong logic tổng hợp bị coi là **lỗi** |
| X4 | `Summary 2026!D64 = '07.2026 Tín Phát'!$E$1` | Tham chiếu sai sheet (dòng Nội thành lấy số SP của Tín Phát). Lỗi A4 |
| X5 | Mẫu số tháng trước gõ cứng (`=F4/1571182` …) | Lỗi A6 — thiếu dữ liệu kỳ trước thì để trống, không bịa số, không dùng `0` |
| X6 | Số `X` gõ tay trong công thức quy đổi của Hoàng/Kiên | Gồm cả `05.2026 Hoàng` = `3770+16190` (cộng tay từng đơn) và Kiên giữ nguyên `7565` suốt 06/07/08.2026 (nhiều khả năng copy công thức chưa cập nhật — lỗi B2). **Đây chính là loại lỗi mà công cụ tồn tại để loại bỏ** |
| X7 | `G1` trùng `C1` viết khác vùng quét | Lỗi B5, không ảnh hưởng số |
| X8 | `B1 = 0` trên mọi sheet kênh | Kênh không điền `Trans` ⟹ số đơn kênh của BC tay là **0**, một artifact nhập liệu chứ không phải sự thật nghiệp vụ |

### 5.6 LEGACY_DEPENDENT — yêu cầu giữ lại cho PHB-04

**KHÔNG implement trong PHB-02.**

| # | Yêu cầu | Ghi chú |
|---|---|---|
| L1 | `Summary 2025` = `REFERENCE_ONLY` — không import / persist / query / display | DEC-169. Là sheet dán cứng, 0 ô công thức, 99 dòng value-only |
| L2 | Cùng kỳ năm trước lấy từ `DataChart 2026` cột `AH` (số cứng 2025), đã import thành `legacy_monthly_reference.sales_prev_year_vnd` | Chỉ theo tháng |
| L3 | Target lịch sử (`legacy_summary_row.target`) là số tay gắn với một `import_id` — **chỉ đọc** | Cấm kết hợp vào bất kỳ chỉ tiêu `PIPELINE_GENERATED` nào (D2, DEC-166 E) |
| L4 | Báo cáo tay 2025 và trước kỳ hiện hành = `LEGACY_REFERENCE` | **KHÔNG chạy lại qua pipeline production như raw accounting input** — luật đã freeze |
| L5 | 2026 sẽ **không** khớp tuyệt đối workbook cũ | DS quy đổi của Hoàng và Kiên cao hơn ~**6,0 %** vì không di trú số ADS lịch sử. Chênh lệch đã được chấp nhận có ý thức (DEC-120), mốc chuẩn chính thức 01/01/2027 (DEC-121) |
| L6 | `legacy_summary_row` giữ đủ 16 cột `C..S` | Không mất thông tin nào của Summary tay |

### 5.7 TARGET_DEPENDENT — trích xuất, không phát minh (PHB-05)

**KHÔNG implement Target trong PHB-02.** Chỉ ghi lại đủ để PHB-05 không phải
đoán:

```text
CHỈ TIÊU ĐƯỢC ÁP    = cột N = F/M = DS QUY ĐỔI / Target
                      (KHÔNG phải doanh số, KHÔNG phải lợi nhuận)
KỲ                  = tháng; cộng thêm một target năm ở Summary!M3
PHẠM VI             = theo từng nhân viên/kênh + một target công ty/tháng
TARGET ĐỔI THEO THỜI GIAN? = KHÔNG trong 2026 — hằng số suốt 8 tháng:
                      Ly 1.300.000 · Thắng 1.300.000 · Hoàng 1.300.000 ·
                      Kiên 1.300.000 · Tín Phát 2.700.000 ·
                      Nội thành 12.000.000 · Linh/Fanpage 1.300.000 ·
                      Gia dụng = KHÔNG CÓ TARGET (null ở cả 8 kỳ)
                      Công ty/tháng 28.790.000 · Năm 345.474.000 (= 12 × 28.790.000)
CÔNG THỨC TƯỜNG MINH? = KHÔNG. Ba điểm mơ hồ đã đo được:
  (a) XUNG ĐỘT ĐƠN VỊ trong CÙNG một sheet DataChart:
      AJ2 = 28.789.481.081 (VND nguyên) vs J15 = 345.474.000 (nghìn đồng)
      — lệch nhau 1.000 lần. Đúng loại lỗi mà DEC-106 tồn tại để ngăn.
  (b) TỔNG KHÔNG KHỚP: tổng target nhân viên tháng 01.2026
      = 1,3+1,3+2,7+1,3+1,3+12,0 = 19.900.000 nghìn đồng,
      nhưng target công ty/tháng = 28.790.000. Chênh 8.890.000 không giải thích được.
  (c) MẪU SỐ BẤT NHẤT: target/ngày = J15/350 nhưng tiến độ năm = B3/A3 với A3 = 365.
SEMANTICS           = AMBIGUOUS  →  OWNER_DECISION_REQUIRED (Q6)
```

---

## 6. Summary Parity Matrix

`Summary 2026` (tay) so với `/tong-quan` + `/nhan-vien?nguon=moi` (SỐ MỚI).

| Cột tay | Nhãn tay | Công thức tay | Reports SỐ MỚI | PARITY |
|---|---|---|---|---|
| `C` | Tổng đơn | `'MM.2026 NV'!$B$1` = `count(Trans)` | Tổng đơn (`COUNT DISTINCT order_key`) | **MATCH** (M1) |
| `D` | Tổng số SP | `$E$1` = `SUM(SL) − D1 − C1` | "Tổng số lượng" = `SUM(quantity)` **mọi dòng** | **MISMATCH có chủ đích** — tay sai (X1); Reports cố ý đổi nhãn + kèm chú thích cảnh báo (D3). Định nghĩa "SP" thật vẫn MỞ (Q3) |
| `E` | Tổng bán | `$H$1` = `SUM(Giá bán × SL)` | "Doanh thu (net)" = `Σ(sell_price×qty − discount)` | **MISMATCH có chủ đích** — khác đúng phần chiết khấu (S3/DEC-114). Gộp thì khớp ERP tuyệt đối (M2) |
| `F` | **DS quy đổi** | `=G/5,5%` \| `=G/7,5%` \| `=(G−X)/5,5%+X/7,5%` | **KHÔNG CÓ** | **NOT_IMPLEMENTED** — chỉ có `conversion_rate_final` theo dòng, không có tổng hợp |
| `G` | Tổng lợi nhuận | `$I$1` = `Σ(Giá bán − Giá nhập TT)×SL` | "Lợi nhuận KPI" + coverage | **AMBIGUOUS** — công thức tương đương (S1), nhưng coverage 0–2/351 (golden) / 34/142 (production) ⟹ chưa có gì để so (Q2) |
| `H` | Tỉ suất lợi nhuận | `=G/E` | **KHÔNG CÓ** | **NOT_IMPLEMENTED** — DEFER D1, tử số chưa chốt (Q7) |
| `I` | So tháng trước | `=F/F(tháng trước)` — **mẫu số là DS quy đổi** | Δ trên **Tổng đơn** và **Doanh thu**, không phải DS quy đổi | **MISMATCH** — cùng tên, khác mẫu số. Reports so 2 chỉ tiêu tay không so; tay so 1 chỉ tiêu Reports chưa có |
| `J` | Tỉ lệ tồn kho | `SUMIF(Nơi nhập="Kho")/H1` | **KHÔNG CÓ** | **NOT_IMPLEMENTED** — DEFER D8, không có nguồn |
| `K` | Lợi nhuận thực tế | `$M$1` = `Σ(Giá bán − Giá thực nhập)×SL` | `accounting_profit` — có ở backend, **không render** | **NOT_DISPLAYED** có chủ đích (S12) |
| `M` | Target | số cứng | **KHÔNG CÓ** | **NOT_IMPLEMENTED** — D2 khoá cứng (Q6) |
| `N` | % Target | `=IFERROR(F/M,"")` | **KHÔNG CÓ** | **NOT_IMPLEMENTED** — phụ thuộc cả `F` lẫn `M` |
| `O`–`S` | Thưởng, ngày công, lương cứng, phụ cấp, tổng lương | `=F×%`, nhập tay, `=P×4500/26`, `=IF(P>=26,30*26,P*30)`, `=SUM(O+Q+R)` | **KHÔNG CÓ** | **DEFER D7** — luật HR |
| — | — | — | Dòng hàng (mẫu số coverage) | **Reports có, tay không** |
| — | — | — | Đơn AUTO / Đơn cần kiểm tra | **Reports có, tay không** — thay cho việc loại trừ thầm lặng (S9) |
| — | — | — | Dòng chưa có ngày bán | **Reports có, tay không** |
| — | — | — | Badge nguồn `SỐ MỚI`/`SỐ CŨ` | **Reports có, tay không** (S11) |

### 6.1 Ngữ nghĩa kỳ

| | Báo cáo tay | Reports |
|---|---|---|
| Đơn vị kỳ | Tháng, cố định bởi tên sheet | Tháng, dẫn xuất từ `sale_date` thật có trong dữ liệu |
| "Toàn bộ" | Không có | Có — và **không** bịa kỳ trước để so |
| Dòng thiếu ngày | Rơi vào sheet của người nhập | Rơi khỏi **mọi** kỳ một cách nhất quán, và được đếm riêng ở ô "Dòng chưa có ngày bán" |
| Kỳ trước rỗng | `=F/1571182` số cứng | Mọi ô so sánh để trống — **không** `−100 %` |

### 6.2 Ngữ nghĩa gộp theo nhân viên

| | Báo cáo tay | Reports |
|---|---|---|
| Thực thể | 8 dòng Summary: Ly, Thắng, Tín Phát, Hoàng, Kiên, Nội thành, Gia dụng, Linh/Fanpage | `employee_normalized` (người thật) × `employee_group` |
| "Nội thành" | **một** dòng như thể một người | **ba** người thật (Vinh, Quý, Hiệp) trong group `NOI_THANH` (S7) |
| "Gia dụng" | **một** dòng như thể một người | **không phải người** — là `ProductGroup`, thuộc tính của dòng hàng (ADR-106). Hiện 100 % `DEFAULT` ⟹ không tái tạo được (Q5) |
| Nhân viên chưa map | im lặng rơi ra ngoài | "Chưa xác định nhân viên" + Review Queue loại `Missing` (C11 còn mở, không chặn) |
| Đơn nhiều nhân viên | không xử lý | đếm ở **từng** dòng nhân viên; dòng TỔNG đếm mỗi đơn đúng **một** lần, kèm chú thích |

---

## 7. Employee Parity

Cách Owner đánh giá một nhân viên trong báo cáo tay, đọc từ `Summary 2026`
theo thứ tự cột:

```
Tổng đơn → Tổng SP → Tổng bán → DS QUY ĐỔI → Lợi nhuận → Tỉ suất
→ So tháng trước → Tỉ lệ tồn kho → Lợi nhuận thực tế
→ TARGET → % TARGET → Thưởng → Ngày công → Lương
```

**Chỉ tiêu quyết định là `F` — DS quy đổi.** Bằng chứng: nó là mẫu số của
`% Target` (`N = F/M`), là cơ sở của `Thưởng` (`O = F × %`), và là chỉ tiêu
mà `So tháng trước` (`I`) so sánh. Doanh số và lợi nhuận thô chỉ là đầu vào
của nó.

Reports hôm nay cho Owner: nhân viên, nhóm, đơn, dòng hàng, tổng số lượng,
doanh thu, LN KPI (+ coverage). **Bốn cột cuối của chuỗi đánh giá — DS quy
đổi, Target, % Target, Thưởng — đều chưa có.**

**Không kết luận rằng web cần một tab cho mỗi nhân viên.** Yêu cầu nghiệp vụ
đúng là:

> Owner chọn **nhân viên + kỳ** và nhận đủ chuỗi đánh giá ở trên.

Không có bằng chứng nào trong trích xuất cho thấy 56 sheet riêng mang ngữ
nghĩa vượt quá việc trình bày: chúng chỉ có 6 biến thể layout, 4 trong đó
khác nhau đúng một ký tự rác. Sheet riêng là hệ quả của việc Excel không có
bộ lọc, không phải một quyết định nghiệp vụ.

---

## 8. Metric Semantic Audit

| METRIC | MANUAL_DEFINITION | REPORTS_DEFINITION | PARITY | BUSINESS_CONSEQUENCE | OWNER_DECISION_REQUIRED |
|---|---|---|---|---|---|
| **số đơn** | `count(Trans)` trên sheet; kênh = 0 vì không điền `Trans` | `COUNT DISTINCT order_key` | **MATCH** | Neo parity tin cậy | KHÔNG |
| **tổng bán** | `Σ(Giá bán × SL)`, giá đã bị sửa tay | `Σ(sell_price×qty)` từ ERP, chưa trừ chiết khấu | **MATCH với ERP**, MISMATCH với BC tay | BC tay thấp hơn ERP 0,6–7,0 % tuỳ kỳ | **CÓ — Q1** |
| **doanh số (net)** | không tồn tại như một khái niệm riêng | `Σ(sell_price×qty − discount)` | **NOT_IN_MANUAL** | 408 dòng, 36.750 k, 0,03 % doanh số công ty | KHÔNG (DEC-114/DEC-122 đã chốt) |
| **lợi nhuận (KPI)** | `Σ(Giá bán − Giá nhập TT)×SL` — `Giá nhập TT` gõ tay ở 635/18.148 dòng | `(SellPrice − KpiPurchasePrice)×Qty − Discount`, chỉ cộng dòng `AUTO` | **AMBIGUOUS** | 100 % dòng golden `price_source = Pending` ⟹ chưa có số để so | **CÓ — Q2** |
| **lợi nhuận thực tế / gộp** | `Σ(Giá bán − Giá thực nhập)×SL` (cột `M`) | `accounting_profit` | **MATCH về công thức**, NOT_DISPLAYED | Có ở backend cho audit/reconciliation | KHÔNG |
| **tỷ lệ lợi nhuận** | `H = G/E` = LN KPI / Tổng bán **gộp** | không có | **NOT_IMPLEMENTED** | Cùng công thức trên mẫu số net sẽ ra số khác | **CÓ — Q7** |
| **DS quy đổi** | `LN KPI ÷ tỉ lệ`, hai bucket cho Hoàng/Kiên với `X` gõ tay | không có tổng hợp; chỉ `conversion_rate_final` theo dòng | **NOT_IMPLEMENTED** | Chỉ tiêu quản trị chính đang thiếu | **CÓ — Q2 (chặn bởi coverage LN KPI)** |
| **conversion / tỉ lệ quy đổi** | 5,5 % PERSONAL · 7,5 % ADS · 2 % Nội thành · 8 % Gia dụng | `config/conversion_rates.yaml` 4 chiều, tra theo ngày đơn | **MATCH** ở chiều `lead_source`; **NOT_IMPLEMENTED** ở chiều `product_group` (100 % `DEFAULT`) | Dòng "Gia dụng"/8 % không tái tạo được | **CÓ — Q5** |
| **đơn hợp lệ** | ngầm định — đơn Owner **chọn giữ lại** trên sheet, không dấu vết | `AUTO` (mọi dòng có kết quả, không finding cần xem) vs `PENDING` | **MISMATCH về bản chất** | Loại trừ thầm lặng → hàng đợi tường minh (S9). Đây là **cải thiện**, không phải hồi quy | **CÓ — Q1** |
| **số SP / tổng số SP** | `SUM(SL) − dòng phụ − một tỉ lệ %` (sai) | `SUM(quantity)` mọi dòng, nhãn khác đi có chủ đích | **MISMATCH có chủ đích** | Reports ra số nguyên, lớn hơn BC 0,05–0,3 và lớn hơn nữa vì tính cả dòng phụ | **CÓ — Q3** |
| **target** | số cứng theo (nhân viên, tháng), hằng số suốt 2026 | không có | **NOT_IMPLEMENTED** | Xung đột đơn vị 1.000 lần; tổng NV ≠ tổng công ty | **CÓ — Q6** |
| **comparison percentages** | `I = F/F(tháng trước)` trên **DS quy đổi**; tháng 01 dùng số cứng | Δ tuyệt đối + Δ % trên **Tổng đơn** và **Doanh thu** | **MISMATCH** | Cùng nhãn "So tháng trước", khác hẳn mẫu số | **CÓ — Q7 (cùng nhóm mẫu số)** |
| **tỉ lệ tồn kho** | `SUMIF(Nơi nhập="Kho", Tổng bán)/H1` | không có | **NOT_IMPLEMENTED** | Cột `Nơi nhập` không tồn tại trong file ERP | KHÔNG (DEFER D8) |

---

## 9. OWNER QUESTIONS — 7 câu

Chỉ những câu **không thể** trả lời từ file hoặc mã nguồn.

### Q1 — Báo cáo tay là oracle SỐ HỌC hay oracle NGHIỆP VỤ?

```text
WHY_REQUIRED = Reports tái tạo sổ ERP đến từng đồng (3.564.610.000 ≡ 3.564.610 k).
  Báo cáo tay thì không: 01.2026 thấp hơn ERP 0,58 % ở doanh số nhưng
  06.2026 lại thấp hơn 6,5 % ở doanh số VÀ CAO HƠN 24,3 % ở lợi nhuận.
  635/18.148 ô giá bị gõ tay, không dấu vết ô nào/vì sao/ai. Một số kỳ có
  nhiều đơn hơn cả sổ nguồn (06.2026 Ly: BC 98 > THÔ 89).
  Không có hàm nào từ dữ liệu Reports có thể sinh ra con số của báo cáo tay.
WHAT_DECISION_IT_UNLOCKS = Định nghĩa của chính từ "parity", và do đó toàn bộ
  tiêu chí nghiệm thu PHB-03. Không trả lời câu này thì mọi con số khác đều
  đang được so với một mốc không xác định.
OPTIONS =
  A (khuyến nghị) — ORACLE NGHIỆP VỤ: Reports phải tái tạo các QUYẾT ĐỊNH của
     báo cáo tay từ đầu vào kiểm toán được. Số sẽ khác, và mỗi chênh lệch phải
     giải thích được. Loại trừ thủ công trở thành Review Queue tường minh.
  B — ORACLE SỐ HỌC: Reports phải khớp con số báo cáo tay. Chỉ khả thi nếu
     Owner cung cấp được, cho từng kỳ, danh sách đơn bị loại và từng điều
     chỉnh giá nhập. Nếu không có, phương án này bất khả thi — không phải khó.
  C — SONG SONG: BC tay giữ nguyên là LEGACY_REFERENCE cạnh SỐ MỚI, không bao
     giờ hoà làm một, và parity chỉ áp cho các kỳ từ một mốc trở đi.
```

### Q2 — Ngưỡng coverage Lợi nhuận KPI nào được coi là "parity đã giao"?

```text
WHY_REQUIRED = Lợi nhuận KPI là gốc của DS quy đổi → % Target → Thưởng.
  Đo được: golden 01.2026 và 06.2026 có price_source = "Pending" trên
  351/351 và 180/180 dòng; production kỳ 09/2026 đạt 34/142 dòng.
  Reports trung thực hiển thị "—" thay vì bịa số — nhưng một báo cáo mà
  chỉ tiêu quản trị chính là "—" thì chưa thay được quy trình thủ công.
WHAT_DECISION_IT_UNLOCKS = Có được phép mở DS quy đổi (PHB-03) hay không, và
  Reports được coi là "đủ dùng" ở mức phủ nào.
OPTIONS =
  A — Đặt một ngưỡng coverage tối thiểu; dưới ngưỡng thì kỳ đó được đánh dấu
      chưa đủ điều kiện thay báo cáo tay.
  B — Chấp nhận coverage thấp, hiển thị DS quy đổi chỉ trên phần AUTO, luôn
      kèm mẫu số.
  C — Ưu tiên nguồn giá nhập trước (Price Master / persistence của
      KpiPurchaseAdjustment) và hoãn DS quy đổi cho tới khi coverage đạt.
```

### Q3 — "Tổng số SP" nghĩa là gì?

```text
WHY_REQUIRED = Công thức của báo cáo tay chứng minh được là sai (trừ một tỉ lệ
  phần trăm khỏi một số lượng), nên không dùng làm định nghĩa được. Reports
  hiện đếm MỌI dòng và cố ý đổi nhãn thành "Tổng số lượng" kèm chú thích.
  `non_product_lines` trong config/validation.yaml là cấu hình hạ mức cảnh
  báo cho validator, KHÔNG phải phân loại hàng hoá — dùng nó làm quy tắc đếm
  là tự cấp thẩm quyền cho một file chưa bao giờ được duyệt cho việc đó (N.7).
WHAT_DECISION_IT_UNLOCKS = Ô "Tổng số SP" có tồn tại trong V1 hay không, và
  gián tiếp cả tử số của tỉ suất nếu Owner muốn tính theo SP.
OPTIONS =
  A — Giữ "Tổng số lượng" (đếm mọi dòng) làm chỉ tiêu duy nhất, bỏ hẳn "Tổng số SP".
  B — Owner ban hành danh sách có thẩm quyền các loại dòng KHÔNG phải hàng hoá
      (phí vận chuyển, công lắp đặt, chiết khấu, voucher, chân máy giặt, giá
      treo tivi…), và Reports hiển thị CẢ HAI, phân biệt rõ.
```

### Q4 — Tổng công ty theo tháng gồm những ai?

```text
WHY_REQUIRED = Trong CÙNG một dòng tổng của báo cáo tay, ba cột có ba phạm vi
  khác nhau: E = SUM(E4:E9) gồm Nội thành, bỏ Gia dụng; F = SUM(F4:F8) bỏ CẢ
  HAI; G và K gồm Nội thành, bỏ Gia dụng. Riêng tháng 01.2026, tổng DS quy đổi
  đang báo cáo thiếu 60,0 % (9.742.558 so với 24.381.683 nghìn đồng) — riêng
  Nội thành đã lớn hơn tổng của cả 5 nhân viên cá nhân cộng lại.
  Không thể biết đây là chính sách hay là vùng SUM bị gõ thiếu.
WHAT_DECISION_IT_UNLOCKS = Ý nghĩa của mọi con số "tổng công ty", và việc có
  cần cấu hình include_in_company_total tách khỏi include_in_kpi hay không.
OPTIONS =
  A — Mọi đối tượng có include_in_kpi = true đều vào tổng, ở MỌI cột (nghĩa là
      vùng SUM cũ là lỗi gõ).
  B — Kênh thật sự bị loại khỏi tổng công ty theo chính sách ⟹ khai báo tường
      minh bằng include_in_company_total, không bằng một vùng SUM.
```

### Q5 — "Gia dụng" có phải một dòng báo cáo hạng nhất trong V1 không?

```text
WHY_REQUIRED = Báo cáo tay coi "Gia dụng" như một thực thể (một dòng Summary,
  16 sheet, tỉ lệ quy đổi 8 %). Mô hình Reports đã cố ý khác: Gia dụng là
  ProductGroup — thuộc tính của DÒNG HÀNG, không phải một con người
  (ADR-106/DEC-127), vì đo trên dữ liệu thật thì 34 % dòng hàng Gia dụng do
  nhóm STANDARD_SALES bán.
  Đo được tại HEAD: product_group_provenance = {"DEFAULT": 351} — 100 % dòng
  rơi về DIEN_MAY theo fallback. DefaultProductGroupProvider trả None cho mọi
  dòng, CÓ CHỦ ĐÍCH: 155 mã model trong sheet Gia dụng lịch sử không phải sự
  thật nghiệp vụ (50 mã cũng xuất hiện ở sheet cá nhân, cùng model quy đổi ở
  tỉ lệ khác), và chưa ai định nghĩa tiền tố tên hàng nào nghĩa là GIA_DUNG.
  ⟹ Hai dòng scheme NOI_THANH_2 và GIA_DUNG_8 hiện không bao giờ kích hoạt đúng.
WHAT_DECISION_IT_UNLOCKS = DS quy đổi có đúng cho kênh hay không; sales mix
  theo nhóm hàng; và ai/khi nào phân loại ProductGroup.
OPTIONS =
  A — V1 không cần dòng "Gia dụng"; chấp nhận mọi dòng là DIEN_MAY và nói rõ
      hệ quả lên DS quy đổi của kênh.
  B — Cần dòng "Gia dụng" ⟹ phải có nguồn phân loại ProductGroup trước
      (Owner phân loại tay qua UI, hoặc Tracking cấp phân loại).
```

### Q6 — Target: tái dùng số lịch sử hay Owner cấp bảng mới? (biên PHB-05)

```text
WHY_REQUIRED = Target ĐÃ tồn tại trong báo cáo tay và ĐÃ được import làm SỐ CŨ
  (legacy_summary_row.target), nhưng OWNER_DECISION D2 cấm tuyệt đối sao chép
  nó vào bất kỳ chỉ tiêu PIPELINE_GENERATED nào. Ba điểm mơ hồ đã đo được:
  (a) xung đột đơn vị 1.000 lần trong cùng sheet DataChart (AJ2 = 28.789.481.081
      VND vs J15 = 345.474.000 nghìn đồng);
  (b) tổng target nhân viên tháng 01.2026 = 19.900.000 nghìn đồng nhưng target
      công ty/tháng = 28.790.000 — chênh 8.890.000 không giải thích được;
  (c) target/ngày chia 350 nhưng tiến độ năm chia 365.
  Fact có lợi: target KHÔNG đổi theo thời gian trong suốt 2026, và Gia dụng
  không có target ở cả 8 kỳ.
WHAT_DECISION_IT_UNLOCKS = PHB-05 có nguồn target hợp lệ hay không, và đơn vị
  chuẩn của nó.
OPTIONS =
  A — Owner cấp bảng target mới (nhân viên/kênh × tháng, VND nguyên theo DEC-106),
      số cũ ở lại đường legacy làm tham chiếu.
  B — Ratify số lịch sử làm target chính thức từ một mốc, kèm quyết định tường
      minh về đơn vị và về khoản chênh 8.890.000.
```

### Q7 — Mẫu số của tỉ suất lợi nhuận và của "So tháng trước"

```text
WHY_REQUIRED = Hai chỗ dùng chung một vấn đề mẫu số, và cả hai đều đổi nghĩa
  con số Owner đọc:
  (a) Tỉ suất: báo cáo tay H = G/E = LN KPI / Tổng bán GỘP. Doanh thu của
      Reports là NET (đã trừ chiết khấu, DEC-114). Cùng công thức, hai mẫu số,
      hai kết quả khác nhau.
  (b) So tháng trước: báo cáo tay so trên DS QUY ĐỔI (I = F/F tháng trước).
      Reports so trên Tổng đơn và Doanh thu. Cùng nhãn, khác hẳn ý nghĩa.
WHAT_DECISION_IT_UNLOCKS = Mở được ô Tỉ suất (hiện DEFER D1/N.7) và làm cho ô
  "So tháng trước" nói đúng điều Owner vẫn dùng để ra quyết định.
OPTIONS =
  A — Tỉ suất = LN KPI / Doanh thu net; So tháng trước giữ Tổng đơn + Doanh thu
      cho tới khi DS quy đổi tồn tại, rồi bổ sung DS quy đổi.
  B — Tỉ suất = LN KPI / Tổng bán gộp để đọc liền mạch với báo cáo cũ; đồng thời
      hiển thị chiết khấu tách riêng.
```

```text
OWNER_DECISIONS_REQUIRED = 7
```

---

## 10. Hợp đồng đề xuất — tách yêu cầu khỏi ý tưởng triển khai

Mọi mục dưới đây là **BUSINESS REQUIREMENT**. Không mục nào mô tả bảng, route,
schema hay thành phần UI. Ý tưởng triển khai được ghi riêng ở mục 10.11 và
**không phải** yêu cầu.

### 10.1 Summary V1 — yêu cầu
- R-S1 Owner chọn một kỳ (tháng) và thấy: số đơn · doanh thu · lợi nhuận KPI kèm coverage trung thực · khối lượng cần kiểm tra.
- R-S2 Mọi giá trị chưa xác định hiển thị là "chưa biết", không bao giờ là `0`.
- R-S3 Mọi con số mang nhãn nguồn; số cũ và số mới không bao giờ cộng chung.
- R-S4 So kỳ trước tồn tại cho ít nhất Tổng đơn và Doanh thu; kỳ trước không có dữ liệu ⟹ để trống, không suy ra `−100 %`.
- R-S5 Dòng không rơi vào kỳ nào (thiếu ngày bán) phải được phơi ra, không được im lặng.
- R-S6 *(chờ Q1)* Tổng công ty theo tháng cộng đủ mọi đối tượng theo một quy tắc **được khai báo**, không theo một vùng SUM.

### 10.2 Employee V1 — yêu cầu
- R-E1 Owner chọn **nhân viên + kỳ** và nhận đủ chuỗi đánh giá; **không** yêu cầu một trang riêng cho mỗi nhân viên.
- R-E2 Danh tính nhân viên được bảo toàn: Vinh/Quý/Hiệp là ba người trong nhóm `NOI_THANH`.
- R-E3 Đổi tên (Linh → Fanpage) và vào/ra giữa chừng xử lý bằng hiệu lực theo thời gian, không bằng danh sách phẳng.
- R-E4 Nhân viên chưa map không bị bỏ im lặng.
- R-E5 Một đơn liên quan nhiều nhân viên được đếm ở từng dòng nhân viên; dòng TỔNG đếm mỗi đơn đúng một lần, và trang phải nói rõ điều đó.
- R-E6 *(chờ Q2)* DS quy đổi theo nhân viên/kỳ, tính bằng tổng các bucket, không bao giờ bằng một tỉ lệ pha trộn.

### 10.3 So sánh kỳ / tháng — yêu cầu
- R-C1 Kỳ mặc định là tháng, dẫn xuất từ ngày bán thật có trong dữ liệu.
- R-C2 Kỳ trước = tháng liền trước cùng độ dài.
- R-C3 *(chờ Q7)* Chỉ tiêu nào được so, và trên mẫu số nào.

### 10.4 Định nghĩa đã được chứng minh (không cần Owner nữa)
S1 · S2 · S3 · S4 · S5 · S6 · S7 · S8 · S9 · S10 · S11 · S12 và neo M1 · M2 (mục 5.1/5.2).

### 10.5 Định nghĩa còn mơ hồ (cần Owner)
Q1 oracle parity · Q2 ngưỡng coverage LN KPI · Q3 "SP" · Q4 phạm vi tổng công ty · Q5 Gia dụng/ProductGroup · Q6 target · Q7 mẫu số tỉ suất và so sánh.

### 10.6 Tự do trình bày
P1–P5 (mục 5.3). Đặc biệt: **không tái tạo 56 sheet thành 56 tab.**

### 10.7 Yêu cầu phụ thuộc legacy (PHB-04)
L1–L6 (mục 5.6).

### 10.8 Yêu cầu phụ thuộc target (PHB-05)
Mục 5.7 nguyên khối.

### 10.9 Loại trừ có chủ đích
X1–X8 (mục 5.5).

### 10.10 Cải thiện đã hoãn
D1–D9 (mục 5.4), gồm `UX-PI-01`.

### 10.11 Ý tưởng triển khai — KHÔNG phải yêu cầu
Ghi lại để không bị mất, và **không** được coi là đã chốt:
`converted_revenue` tổng hợp ở tầng truy vấn thay vì tầng UI · một cấu hình
`include_in_company_total` tách khỏi `include_in_kpi` · `LearnedProductGroupProvider`
cắm vào seam `ProductGroupProvider` đã có · bảng target dạng YAML theo
`(đối tượng, tháng)` với `effective_from`/`effective_to`. Bất kỳ mục nào ở đây
muốn thành yêu cầu đều phải qua Owner trước.

---

## 11. Sẵn sàng cho PHB-03

```text
PHB_03_READY = NO
```

Ngữ nghĩa nghiệp vụ của Summary + Employee V1 **chưa đủ đóng băng để triển
khai mà không phải đoán**. Danh sách quyết định Owner đang chặn PHB-03 —
đúng bằng đây, không hơn:

| Chặn | Vì sao chặn PHB-03 |
|---|---|
| **Q1** | Không có định nghĩa "parity" thì không có tiêu chí nghiệm thu cho PHB-03 |
| **Q2** | Quyết định DS quy đổi có được mở trong PHB-03 hay không |
| **Q4** | Mọi ô "tổng" trên Summary V1 phụ thuộc câu trả lời này |
| **Q7** | Quyết định ô Tỉ suất và mẫu số của "So tháng trước" |

**Không chặn PHB-03** (có thể trả lời song song): Q3 (Reports đã có đường an
toàn là "Tổng số lượng" kèm chú thích), Q5 (thuộc DS quy đổi/kênh), Q6
(thuộc PHB-05).

---

## 12. Findings

Finding **không** tự sinh task.

### BLOCKING (2)

```text
FIND-PHB02-B01  PARITY ORACLE KHÔNG XÁC ĐỊNH
  Báo cáo tay không phải hàm của bất kỳ đầu vào nào Reports có (mục 4.3).
  Nếu không chốt Q1, mọi chỉ tiêu MUST_MATCH sẽ được implement với một mốc
  so sánh không tồn tại. Đúng tiêu chí blocking: "business parity không thể
  được định nghĩa an toàn".

FIND-PHB02-B02  DS QUY ĐỔI SẼ ĐƯỢC IMPLEMENT VỚI NGỮ NGHĨA ĐOÁN
  DS quy đổi là chỉ tiêu quản trị CHÍNH của báo cáo tay, và ba tiền đề của
  nó đều chưa vững: coverage LN KPI 0–2/351 trên golden (Q2), ProductGroup
  100 % DEFAULT nên hai scheme kênh không kích hoạt đúng (Q5), và phạm vi
  tổng công ty mâu thuẫn trong chính báo cáo tay (Q4). Đúng tiêu chí
  blocking: "một chỉ tiêu sẽ được implement với ngữ nghĩa đoán".
```

### NON-BLOCKING (5)

```text
FIND-PHB02-N01  Báo cáo tay chứa 635/18.148 ô giá nhập gõ tay, không dấu vết.
                Là dữ kiện lịch sử, không phải lỗi cần sửa.
FIND-PHB02-N02  Target công ty/tháng (28.790.000) ≠ tổng target nhân viên
                (19.900.000) tháng 01.2026; chênh 8.890.000 không giải thích
                được từ file. Thuộc PHB-05.
FIND-PHB02-N03  Xung đột đơn vị 1.000 lần trong cùng sheet DataChart
                (AJ2 VND vs J15 nghìn đồng). Thuộc PHB-05.
FIND-PHB02-N04  Không tồn tại vị trí backlog UX canonical trong repo; UX-PI-01
                được ghi tại mục 5.4 D9 của tài liệu này để không thất lạc.
FIND-PHB02-N05  `app/modules/conversion/` đã có đủ resolver + engine cấp dòng
                nhưng không có consumer nào tổng hợp `converted_revenue`.
                Là trạng thái ĐÚNG theo §L ("LATER", cấm tính ở tầng UI),
                ghi lại để phiên sau không nhầm là bug.
```

Không có finding nào thuộc loại hardening — hardening không phải việc của PHB-02.

---

## 13. Ràng buộc phạm vi đã tuân thủ

```text
PHB-01 (Product Identity)  = KHÔNG mở lại. Chỉ ghi UX-PI-01 làm backlog hoãn.
PHB-03                     = KHÔNG bắt đầu.
PHB-04 (Legacy)            = KHÔNG implement. Yêu cầu bảo toàn ở mục 5.6.
PHB-05 (Target)            = KHÔNG implement. Trích xuất tối thiểu ở mục 5.7.
PRODUCTION CODE            = 0 dòng thay đổi.
SCOPE_DRIFT                = NO
PHB_02                     = AWAITING_OWNER
```
