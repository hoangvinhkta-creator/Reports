# PHB-02 — BUSINESS PARITY CONTRACT (FROZEN)

Status: FROZEN
Task Mode: MAJOR (audit + contract freeze — 0 dòng production code)
Frozen: 2026-09-04 (S114) bằng bảy quyết định Owner `DEC-PHB02-01…07`.
Nguồn thẩm quyền: Owner > báo cáo tay của Owner > tài liệu Phase B đã chấp nhận >
hành vi production hiện tại của Reports > mã nguồn > test > suy diễn.

Câu hỏi trung tâm của PHB-02:

> *Thông tin nghiệp vụ và quy trình nào trong báo cáo tay của Owner bắt buộc
> Reports phải bảo toàn hoặc thay thế, để ứng dụng web thật sự thay được quy
> trình báo cáo thủ công?*

Đây **không** phải bài tập clone giao diện Excel. Kết luận "55 tab Excel ⟹ 55
tab web" bị bác bỏ (mục 5.3 P1).

Bản audit (mục 1–8) là **bản ghi bằng chứng, không viết lại**. Bảy quyết định
Owner ở mục 0 giải quyết các câu hỏi mà audit đã mở, và mục 9–13 ghi kết quả
sau khi áp dụng chúng.

---

## 0. QUYẾT ĐỊNH OWNER — ĐÃ CHỐT, THAY THẾ MỌI SUY DIỄN

Bảy quyết định dưới đây do Owner ban hành. Chúng **thay thế** suy diễn của
agent và **thay thế** mọi suy diễn ngược lại rút ra từ workbook tay cũ.

### DEC-PHB02-01 — Mục đích của Reports / Parity Oracle

```text
Reports được xây dựng để THAY THẾ quy trình báo cáo thủ công.

Báo cáo production phải được dẫn xuất từ:
  - sổ kế toán thô;
  - các nguồn hỗ trợ có thẩm quyền đã được chấp nhận;
  - business rule đã được Owner duyệt.

Báo cáo tay cũ KHÔNG phải oracle số học.

Reports KHÔNG ĐƯỢC sửa chỉ để tái tạo các con số lịch sử đã nhập/sửa bằng
tay, khi những giá trị đó không tái tạo được từ nguồn dữ liệu đã chấp nhận
+ business rule đã duyệt.

Báo cáo tay cũ có giá trị với tư cách:  BUSINESS REQUIREMENT / SEMANTIC REFERENCE
Nó KHÔNG phải:                          FINAL NUMERIC AUTHORITY

⟹ "business parity" nghĩa là thay thế NĂNG LỰC NGHIỆP VỤ và NGỮ NGHĨA hữu ích
   của quy trình thủ công, KHÔNG phải tái tạo mọi con số lịch sử hay mọi
   artifact bảng tính.
```

**Đóng Q1.** Đúng phương án A mà audit khuyến nghị (mục 9.1).

### DEC-PHB02-02 — Giá nhập / coverage lợi nhuận

```text
1. AUTO-fill giá nhập bất cứ khi nào dữ liệu có thẩm quyền cho phép thuật
   toán khớp giá nhập ĐÃ ĐƯỢC CHẤP NHẬN trước đó trong dự án phân giải được.

2. Nếu không đủ dữ liệu để phân giải giá nhập:
   - hiện CẢNH BÁO TƯỜNG MINH;
   - cho phép Owner/người dùng NHẬP TAY giá nhập.

3. Ô giá nhập PHẢI vẫn sửa được ngay cả khi đã AUTO-fill.
   Giữ provenance để hệ thống phân biệt được TỐI THIỂU:  AUTO  |  MANUAL / MANUAL_OVERRIDE
   KHÔNG được âm thầm coi một manual override là AUTO.

4. Lợi nhuận KPI chỉ được công nhận là HOÀN CHỈNH/CHÍNH THỨC khi:

       PROFIT_COVERAGE = 100 %

   Nếu coverage < 100 %:
   - KHÔNG trình bày kết quả một phần như lợi nhuận KPI chính thức;
   - phơi rõ phần giá nhập còn thiếu;
   - cho phép hoàn thiện phần thiếu bằng tay.

   KHÔNG phát minh ngưỡng 90 %, 95 % hay bất kỳ ngưỡng nào khác.
```

**Đóng Q2** — nhưng bằng một **GATE**, không phải một ngưỡng. Đây là khác biệt
quan trọng: audit hỏi "ngưỡng nào là đủ"; Owner trả lời "không có ngưỡng —
100 % hoặc chưa chính thức", cộng với một năng lực mới để đạt được 100 %.

### DEC-PHB02-03 — Tổng số SP

```text
"Tổng số SP" = SUM(quantity) của các sản phẩm bán ra ĐỦ ĐIỀU KIỆN.

Quy tắc đủ điều kiện:   giá bán sản phẩm > 1.000.000 VND

Sản phẩm có giá bán <= 1.000.000 VND bị LOẠI khỏi chỉ tiêu này, để tránh
nhiễu từ phụ kiện: giá treo, chân kê, và các phụ kiện giá trị thấp tương tự.

Đây KHÔNG phải:  - số SKU duy nhất;
                 - số dòng chứng từ.
Nó là SỐ LƯỢNG sản phẩm đủ điều kiện đã bán.

KHÔNG mở rộng thành một product taxonomy trừ khi có yêu cầu riêng.
```

**Đóng Q3 và đóng `N.7`** cho chỉ tiêu này. Đây là **quy tắc ngưỡng giá**, cố
ý KHÔNG phải phân loại hàng hoá.

### DEC-PHB02-04 — DS quy đổi (converted sales)

```text
DS quy đổi là CHỈ TIÊU CỐT LÕI đánh giá hiệu suất nhân viên.

MỤC ĐÍCH: doanh thu thô tạo động lực sai lệch — một sản phẩm giá cao có thể
sinh ra lợi nhuận bằng hoặc thấp hơn một sản phẩm giá thấp hơn.
  Tủ lạnh: giá bán 30.000.000, lợi nhuận 1.000.000
  Tivi:    giá bán 15.000.000, lợi nhuận 1.000.000
Dùng doanh thu thô thì bán tủ lạnh được thưởng gấp đôi dù lợi nhuận như nhau.
DS quy đổi chuẩn hoá hiệu suất qua lợi nhuận và một hệ số quy đổi kỳ vọng.

CÔNG THỨC:
       PROFIT          = sale_price − purchase_price
       CONVERTED_SALES = PROFIT / CONVERSION_RATE

  ví dụ: 1.000.000 / 0,075 = 13.333.333,33

TUYỆT ĐỐI KHÔNG implement:  profit * rate     ← công thức này SAI

PHẠM VI: DS quy đổi gồm TẤT CẢ đơn/bán hàng đủ điều kiện do nhân viên bán
trong tháng. KHÔNG giới hạn ở một tập con được chọn tay.

Vì DS quy đổi phụ thuộc lợi nhuận/giá nhập, implementation phải tôn trọng
ngữ nghĩa completeness của DEC-PHB02-02.
KHÔNG bịa DS quy đổi từ giá nhập chưa phân giải.
```

**Đóng ambiguity công thức DS quy đổi.** Khớp đúng `S4` mà audit đã ghi và
đúng công thức `=G4/5,5%` của workbook tay.

> **Đọc bắt buộc — `PROFIT` ở đây là gì.** Dòng `PROFIT = sale_price −
> purchase_price` là minh hoạ **theo một đơn vị sản phẩm**, dùng để nói rõ
> phép chia (không phải phép nhân). Nó **không** thay thế công thức lợi nhuận
> KPI đã freeze bởi `DEC-143` / `OD-108B-01`:
> `EligibleKpiProfit = (SellPrice − KpiPurchasePrice) × Quantity − Discount`
> (`EligibleCosts = {}` closed empty set, `DeliveryCost` NOT ELIGIBLE,
> `OtherKpiAdjustment = 0`). Không có gì trong `DEC-PHB02-04` nói bỏ `× Quantity`
> hay bỏ `− Discount`, và cả hai đều đã là quyết định Owner đứng độc lập
> (`DEC-114`, `DEC-122`, `DEC-143`). Vì vậy `PROFIT` trong `DEC-PHB02-04`
> **=** `EligibleKpiProfit`. Ghi lại làm điểm xác nhận một dòng cho PHB-03,
> KHÔNG phải câu hỏi Owner mới (xem `FIND-PHB02-N06`).

### DEC-PHB02-05 — Định tuyến tỉ lệ quy đổi

```text
Nhóm nhân viên/nghiệp vụ quyết định tỉ lệ quy đổi MẶC ĐỊNH.

A. TÍN PHÁT                                            rate = 7,5 %

B. WHOLESALE / NỘI THÀNH  — Vinh · Quý · Hiệp
     mặc định (hàng KHÔNG phải gia dụng)                rate = 2 %
     nếu sản phẩm được TICK phân loại GIA_DUNG          rate = 8 %

       if product_is_gia_dung:  rate = 8 %
       else:                    rate = 2 %

   Đây là nhóm DUY NHẤT hiện cần năng lực phân loại/tick "Gia dụng".
   Phân loại Gia dụng là một PRODUCT-LEVEL OVERRIDE bên trong luồng
   wholesale/nội-thành. Nó KHÔNG phải một loại nhân viên riêng.
   KHÔNG suy ra Gia dụng tự động từ tên hàng, trừ khi có hợp đồng khác
   được chấp nhận cho phép rõ ràng.

C. NHÂN VIÊN BÁN LẺ KHÁC                                rate = 5,5 %
   Nhóm này KHÔNG cần tính năng tick/phân loại Gia dụng cho luật này.
   KHÔNG hiện và KHÔNG bắt buộc luồng đó với nhân viên bán lẻ thường.

VÍ DỤ NGHIỆM THU (lợi nhuận = 1.000.000 VND):
   Tín Phát                    1.000.000 / 7,5 %  = 13.333.333,33
   Vinh/Quý/Hiệp, hàng thường  1.000.000 / 2 %    = 50.000.000
   Vinh/Quý/Hiệp, Gia dụng     1.000.000 / 8 %    = 12.500.000
   Bán lẻ khác                 1.000.000 / 5,5 %  = 18.181.818,18
```

**Đóng Q5.**

### DEC-PHB02-06 — Target nhân viên

```text
Target PHẢI cấu hình được theo từng nhân viên.
Owner/người dùng phải có chỗ để NHẬP và SỬA target.
KHÔNG hard-code giá trị target của từng nhân viên vào logic tính toán.

PHB-02 chỉ freeze YÊU CẦU NGHIỆP VỤ này.
Implementation chi tiết của Target ở lại vertical roadmap của nó.
```

**Đóng Q6** ở mức ý định nghiệp vụ.

### DEC-PHB02-07 — So tháng trước

```text
"So tháng trước" = phần trăm thay đổi của DOANH THU BÁN HÀNG
                   tháng hiện tại so với tháng liền trước.

    (doanh_thu_tháng_này − doanh_thu_tháng_trước) / doanh_thu_tháng_trước × 100 %

Chỉ tiêu được so:  DOANH THU BÁN HÀNG
KHÔNG phải:        DS quy đổi · lợi nhuận · số lượng SP · mức đạt target

Xử lý doanh_thu_tháng_trước = 0 một cách TƯỜNG MINH khi implement;
KHÔNG bịa vô cực hay một phần trăm gây hiểu nhầm.
```

**Đóng Q7** (phần So tháng trước). Xác nhận hành vi hiện tại của Reports và
bác bỏ mẫu số của workbook tay (`I = F/F(tháng trước)` trên DS quy đổi).

---

## 1. Target Gate

### 1.1 Gate của phiên audit (S113)

```text
EXPECTED_HEAD   = eaa3fdeb4ffdfd2d5772314ac24cf8a1273cc67e
OBSERVED_HEAD   = eaa3fdeb4ffdfd2d5772314ac24cf8a1273cc67e   → KHỚP
DEFAULT_BRANCH  = claude/extract-upload-repo-gq2ws4 (origin HEAD branch)
SESSION_BRANCH  = claude/business-parity-contract-me80ij
WORKTREE        = sạch
PHB-01          = DONE      (PROJECT/PROJECT_PROGRESS.md, khối canonical S112)
PHB-02          = CURRENT   (NEXT_VERTICAL_ACTION của cùng khối)
TARGET_GATE     = PASS
```

### 1.2 Gate của phiên freeze (S114)

```text
EXPECTED_HEAD   = a47c164   OBSERVED = a47c164bc018bfc5fdc97af08dacea406812a17c → KHỚP
BRANCH          = claude/business-parity-contract-me80ij → KHỚP
WORKTREE        = sạch
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

```text
MANUAL_REPORT_STRUCTURE_AVAILABLE = YES (qua trích xuất đã chấp nhận, thẩm quyền mức 3)
```

Mọi kết luận parity dưới đây trích từ hai nguồn trên hoặc từ mã nguồn/fixture
tại `EXPECTED_HEAD`. **Không có cấu trúc sheet nào được suy đoán.**

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
| A3 | Tổng số lượng | như trên | CÓ | VERIFIED — sẽ được thay/bổ sung bởi `DEC-PHB02-03` |
| A4 | Doanh thu (net) | như trên | CÓ | VERIFIED — `sell_price × quantity − discount` (DEC-114) |
| A5 | Lợi nhuận KPI + coverage | như trên | CÓ | VERIFIED công thức; **coverage thấp**, xem mục 4.4 |
| A6 | Lợi nhuận kế toán | KHÔNG render | backend only | VERIFIED — gỡ khỏi UI theo `OWNER_PRESENTATION_DECISION` KPI-first (2026-09-03) |
| A7 | Đơn AUTO / Đơn cần kiểm tra | `/tong-quan` | CÓ | VERIFIED (theo ĐƠN: một đơn PENDING nếu có ≥1 dòng PENDING) |
| A8 | Dòng chưa có ngày bán | `/tong-quan` | CÓ | VERIFIED |
| B | Nhân viên — 7 cột | `/nhan-vien?nguon=moi` | CÓ | VERIFIED (`GROUP BY employee_normalized, employee_group`) |
| C | So kỳ trước (Δ tuyệt đối + Δ %) | `/tong-quan` | CÓ | VERIFIED — Tổng đơn + Doanh thu; **khớp `DEC-PHB02-07`** |
| D | Danh sách đơn + chi tiết đơn | `/ban-hang`, `/ban-hang/<order_key>` | CÓ | VERIFIED |
| E | Mặt hàng trên chứng từ | `/san-pham` | CÓ | VERIFIED — gộp theo **mô tả thô đã chuẩn hoá** |
| F | Review / Pending | `/du-lieu`, cột trạng thái | CÓ | VERIFIED |
| G | Nhãn nguồn dữ liệu | badge `SỐ MỚI` / `SỐ CŨ` | CÓ | VERIFIED — hai loại số không bao giờ cộng chung |

### 3.2 SỐ CŨ — legacy reference (chỉ đọc, không tính lại)

| # | Năng lực | Bề mặt |
|---|---|---|
| H | Ma trận `Summary 2026` tháng × người bán — 8 cột: Tổng đơn · Tổng số SP · Tổng bán · DS quy đổi · Tổng lợi nhuận · So tháng trước · Target · So target | `/nhan-vien` (mặc định) |
| I | `DataChart 2026` — doanh số theo ngày + tham chiếu tháng | `/doanh-so-ngay` |

`legacy_summary_row` lưu đủ **16 cột** của `Summary 2026` (C..S) — không có
thông tin nào của Summary tay bị mất khi số hoá.

### 3.3 Khoảng trống đã đo được của SỐ MỚI

| Năng lực | Trạng thái trên đường pipeline |
|---|---|
| **DS quy đổi** | **NOT_IMPLEMENTED.** `conversion_rate_final` được tính/lưu **theo dòng**, nhưng **không có phép tổng hợp `converted_revenue` nào** ở `app/web/*`, ở phần pipeline của `tools/db/schema.py`, hay ở exporter. `converted_revenue` chỉ tồn tại ở đường legacy. |
| **Target / So target** | **NOT_IMPLEMENTED** trên pipeline (D2 của PRA-003). |
| **Tỉ suất lợi nhuận** | **NOT_IMPLEMENTED** — DEFER `D1`. |
| **Nhập tay / override giá nhập** | **NOT_IMPLEMENTED.** Từ vựng đã có (`PRICE_SOURCE_MANUAL = "Manual"`, `app/modules/domain/models.py:43`, dành sẵn cho "when override/audit trail exists"), nhưng **không có đường ghi nào**. Tầng analytics là CHỈ-ĐỌC theo thiết kế. |
| **Tick GIA_DUNG cấp sản phẩm** | **NOT_IMPLEMENTED.** `DefaultProductGroupProvider` trả `None` cho mọi dòng, CÓ CHỦ ĐÍCH (ADR-106 §6). |
| Tỉ lệ tồn kho (cột `J`) | **DEFER** — cột `Nơi nhập` không có trong file ERP. |
| Thưởng / ngày công / lương (cột `O`–`S`) | **DEFER** (N.9) — luật HR. |
| Cùng kỳ năm trước / YTD | Một phần: `DataChart 2026` mang `sales_prev_year_vnd`. `Summary 2025` = `REFERENCE_ONLY`, không import. |

---

## 4. Đối chiếu số thật — bằng chứng quyết định

Ba nguồn được đối chiếu trên **cùng kỳ, cùng nhân viên**, tất cả đều là
artifact đã commit:

- **BC** = báo cáo tay (`evidence.json → report.sheet_totals`)
- **THÔ** = sổ ERP (`evidence.json → raw_by_month_employee`)
- **REPORTS** = pipeline tại `EXPECTED_HEAD`
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

### 4.3 Vì sao báo cáo tay không thể là oracle số học

Ba bằng chứng độc lập cùng chỉ một hướng:

1. `01.2026`: BC **thấp hơn** ERP 0,58 % ở doanh số và thấp hơn 0,8 % ở lợi nhuận.
2. `06.2026`: BC **thấp hơn** ERP 6,5 % ở doanh số nhưng **CAO HƠN** ERP
   24,3 % ở lợi nhuận (119.236 vs 95.957) — lệch **hai chiều ngược nhau trong
   cùng một sheet**, không giải thích được bằng một quy tắc duy nhất.
3. `report.manual_price_overrides = 635/18.148` — 635 ô giá nhập bị gõ tay,
   **không có dấu vết nào** cho biết ô nào, vì sao, ai sửa.

Cộng thêm việc số đơn BC lệch tới 9 đơn ở một số kỳ (`06.2026 Ly`: BC 98 đơn >
THÔ 89 đơn — báo cáo có nhiều hơn nguồn).

> **`DEC-PHB02-01` chốt đúng kết luận này.** Báo cáo tay = BUSINESS
> REQUIREMENT / SEMANTIC REFERENCE, không phải FINAL NUMERIC AUTHORITY.
> Reports **không được sửa** để đuổi theo con số tay. Một chênh lệch chỉ đáng
> quan tâm khi Reports vi phạm một business rule đã duyệt hoặc một nguồn có
> thẩm quyền — không phải khi nó đơn giản khác con số tay.

### 4.4 Lợi nhuận KPI — chỉ tiêu quản trị chính, và nó chưa có

Trên cả hai kỳ golden, **100 % dòng có `price_source = "Pending"`** ⟹
`eligible_kpi_profit` `NULL` ⟹ ô "Lợi nhuận KPI" hiện `—` với coverage
`0 / 351` (đường `run_import` trần) hoặc `2 / 351` (đường production có nạp
historical-confirmed registry — `FIND-PRA003-01`). Trên production thật kỳ
09/2026, coverage đo được là **34 / 142 dòng**.

Trong báo cáo tay, Lợi nhuận KPI là gốc của mọi thứ khác:

```
Lợi nhuận KPI (cột I) → DS quy đổi (cột F = I/tỉ lệ) → % Target (cột N = F/M)
                                                     → Thưởng (cột O = F × %)
```

> **`DEC-PHB02-02` chốt xử lý.** Không có ngưỡng coverage nào được chấp nhận
> ngoài **100 %**: dưới 100 % thì lợi nhuận KPI **không phải** số chính thức,
> phần thiếu phải được phơi rõ, và phải có đường **nhập tay** để hoàn thiện.
> Giá nhập AUTO vẫn phải sửa được, và override phải mang provenance riêng.

### 4.5 Tỉ lệ quy đổi — điểm khớp ngữ nghĩa đã được chứng minh

`conversion.scheme_distribution = {"ADS_7_5@0.075": 351}` trên `01.2026 Tín
Phát`, provenance `Auto:LeadSource` — đúng `=G6/7,5%` mà báo cáo tay dùng cho
Tín Phát ở mọi kỳ. Toàn bộ bảng tỉ lệ quan sát trong báo cáo tay được
`config/conversion_rates.yaml` tái hiện đúng.

**Nhưng** `conversion.product_group_provenance = {"DEFAULT": 351}` — 100 %
dòng rơi về `DIEN_MAY` theo fallback. `DefaultProductGroupProvider` trả `None`
cho mọi dòng, cố ý (ADR-106 §6 / DEC-127 §5): 155 mã model trong sheet Gia
dụng lịch sử không phải sự thật nghiệp vụ (50 mã cũng xuất hiện ở sheet cá
nhân, cùng model quy đổi ở tỉ lệ khác), và chưa ai định nghĩa tiền tố tên hàng
nào nghĩa là `GIA_DUNG`.

> **`DEC-PHB02-05` chốt xử lý và thu hẹp bài toán.** Tick `GIA_DUNG` là
> **product-level override chỉ bên trong luồng wholesale/nội-thành
> (Vinh/Quý/Hiệp)**; nhân viên bán lẻ khác **không cần** tính năng đó. Và
> **cấm suy ra Gia dụng tự động từ tên hàng** — đúng thiết kế hiện có của
> `DefaultProductGroupProvider`, nay được nâng thành luật nghiệp vụ.

### 4.6 `DEC-PHB02-03` đo trên dữ liệu thật (E1, phiên S114)

Áp quy tắc `SUM(quantity) khi giá bán > 1.000.000 VND` lên chính hai fixture
golden (đọc trực tiếp `tests/fixtures/golden/period_2026_*.xlsx`):

| Kỳ | `SUM(qty)` mọi dòng | **`DEC-PHB02-03`** | Số dòng bị loại | BC tay |
|---|---:|---:|---:|---:|
| 01.2026 Tín Phát | 407 | **358** | 45 | 387,6271681 |
| 06.2026 Tín Phát | 210 | **178** | 27 | 178,8029801 |

Hai điều đo được, cả hai đều làm quy tắc này an toàn để implement:

1. **Đơn giá hay tổng dòng — không quan trọng trên dữ liệu thật.** Đọc
   "giá bán" là **đơn giá** cho ra `358` / `178`; đọc là **tổng dòng** cũng
   cho ra `358` / `178`. Chênh lệch **bằng 0** ở cả hai kỳ. Cách đọc canonical
   là **đơn giá** (khớp cột `Giá bán` của sheet tay và cụm từ "product sale
   price"), và sự mơ hồ này là **vô hại** trên thực tế.
2. **Quy tắc loại đúng thứ Owner muốn loại.** Các mô tả bị loại nhiều nhất:
   `Chi phí vận chuyển` (19/10) · `Giá treo Tivi` (12/9) · `Chân máy giặt Đa
   Năng` (8) · `Chi phí lắp đặt` (2/1) · `Phụ Phí` (1/2) · `Giá treo xoay NB
   P6`. Đúng nhóm "giá treo, chân kê, phụ kiện giá trị thấp".

Hệ quả đã chấp nhận, nói rõ: vì đây là **ngưỡng giá** chứ không phải taxonomy,
vài **sản phẩm thật giá thấp** cũng bị loại — đo được 2 dòng ở 01.2026 (`Đèn
sưởi nhà tắm Kangaroo KGWH03T`) và 1 dòng ở 06.2026 (`Bình nước nóng Ariston
Slim 3 20 RS VN`). Owner đã chỉ thị rõ *"KHÔNG mở rộng thành product
taxonomy"*, nên đây là đánh đổi có chủ đích, không phải defect.

---

## 5. Phân loại parity

### 5.1 MUST_MATCH — kết quả số phải khớp định nghĩa nghiệp vụ đã chấp nhận

Theo `DEC-PHB02-01`, mốc so sánh là **sổ kế toán thô + nguồn có thẩm quyền +
business rule đã duyệt**, KHÔNG phải con số báo cáo tay.

| # | Chỉ tiêu | Định nghĩa chấp nhận | Bằng chứng |
|---|---|---|---|
| M1 | **Số đơn** theo (nhân viên, tháng) | `COUNT DISTINCT` mã đơn | 254=254=254 · 146=146=146 (mục 4.1/4.2) |
| M2 | **Tổng bán gộp** so với **sổ ERP** | `Σ (Giá bán × SL)` trước chiết khấu | `sales_raw_gross = 3.564.610.000` ≡ `THÔ 3.564.610 k` — khớp từng đồng |
| M3 | **Tổng số SP** | `DEC-PHB02-03` — `SUM(quantity)` khi đơn giá > 1.000.000 VND | Đo được 358 (01.2026) · 178 (06.2026), mục 4.6 |
| M4 | **DS quy đổi** | `DEC-PHB02-04` + `DEC-PHB02-05` — `EligibleKpiProfit ÷ rate`, cộng đủ MỌI đơn đủ điều kiện trong tháng | Ví dụ nghiệm thu ở `DEC-PHB02-05`; **chỉ hợp lệ khi coverage = 100 %** |
| M5 | **So tháng trước** | `DEC-PHB02-07` — `(DT tháng này − DT tháng trước) / DT tháng trước` | Hành vi hiện tại của `/tong-quan` đã đúng chỉ tiêu |

### 5.2 MUST_PRESERVE_SEMANTICS

| # | Ngữ nghĩa | Ràng buộc | Nguồn |
|---|---|---|---|
| S1 | Lợi nhuận KPI = `(SellPrice − KpiPurchasePrice) × Qty − Discount` | `EligibleCosts = {}` closed empty set; `DeliveryCost` NOT ELIGIBLE; `OtherKpiAdjustment = 0` | DEC-143 / `OD-108B-01`, xác nhận lại bởi `DEC-PHB02-04` |
| S2 | Hai cột giá nhập giữ hai vai trò khác nhau | `L` → `AccountingPurchasePrice`; `F` → `KpiPurchasePrice` = `L + KpiPurchaseAdjustment` | `docs/analysis/02_FORMULA_MAPPING.md` §1 |
| S3 | Chiết khấu trừ vào **cả** doanh số **và** lợi nhuận | Doanh thu net ≠ "Tổng bán" của BC tay — phân kỳ có chủ đích | DEC-114, DEC-122 (C4b) |
| S4 | DS quy đổi = **PHÉP CHIA**, không bao giờ phép nhân, không bao giờ một tỉ lệ pha trộn | `Σ(LN KPI theo nhóm ÷ rate)`. `profit * rate` bị cấm tuyệt đối | **`DEC-PHB02-04`**, DEC-119, DEC-120, ADR-106 §4 |
| S5 | `X` (phần lợi nhuận ADS gõ tay) **không còn là đầu vào** | thay bằng tổng có truy vết từ phân loại cấp đơn | `docs/analysis/02_FORMULA_MAPPING.md` §4 |
| S6 | Tỉ lệ tra theo **ngày của đơn**, không theo "hôm nay" | `effective_from`/`effective_to` | DEC-121 |
| S7 | Danh tính nhân viên được bảo toàn | Vinh/Quý/Hiệp là **ba** Employee thật thuộc `NOI_THANH` — không gộp thành một thực thể giả | DEC-127 §1, xác nhận lại bởi `DEC-PHB02-05` B |
| S8 | Đổi tên/vào-ra giữa chừng dùng hiệu lực theo thời gian | Linh (03.2026) và Fanpage (04–05.2026) là cùng một thực thể | `docs/analysis/05_EXCEPTIONS.md` B3 |
| S9 | Loại trừ thủ công thầm lặng → **Review Queue tường minh** | đơn bị bỏ phải có lý do và người quyết | đặc tả §18, DEC-128 |
| S10 | `NULL` không bao giờ là `0`; kỳ trước vắng mặt không bao giờ là `−100 %` | ô trống hiện `—`; mọi ô lợi nhuận kèm coverage `N / M dòng` | `analytics_presentation.py`; xác nhận lại bởi `DEC-PHB02-07` (xử lý mẫu số 0 tường minh) |
| S11 | `SỐ CŨ` và `SỐ MỚI` không bao giờ cộng chung | badge nguồn bắt buộc | DEC-166 E |
| S12 | Lợi nhuận kế toán vẫn tồn tại ở backend | gỡ khỏi UI là quyết định trình bày, không phải xoá khỏi mô hình | `OWNER_PRESENTATION_DECISION`, 2026-09-03 |
| **S13** | **Giá nhập AUTO phải SỬA ĐƯỢC, và override mang provenance riêng** | tối thiểu phân biệt `AUTO` vs `MANUAL / MANUAL_OVERRIDE`; **cấm** âm thầm coi override là AUTO | **`DEC-PHB02-02`** |
| **S14** | **Lợi nhuận KPI chỉ CHÍNH THỨC khi coverage = 100 %** | dưới 100 %: không trình bày như số chính thức, phơi rõ phần thiếu, cho hoàn thiện bằng tay. **Không có ngưỡng nào khác** | **`DEC-PHB02-02`** |
| **S15** | **Tick `GIA_DUNG` là product-level override, chỉ trong luồng Vinh/Quý/Hiệp** | không phải loại nhân viên; **cấm** suy ra tự động từ tên hàng; **không** hiện luồng này cho bán lẻ thường | **`DEC-PHB02-05`** |
| **S16** | **Target cấu hình được theo nhân viên, nhập/sửa được** | **cấm** hard-code giá trị target vào logic tính | **`DEC-PHB02-06`** |

### 5.3 MAY_IMPROVE_PRESENTATION

| # | Yếu tố của báo cáo tay | Thay bằng |
|---|---|---|
| P1 | **56 sheet nhân viên-tháng** | **Một** trang + bộ chọn kỳ + chiều nhân viên. 56 sheet chỉ có **6 biến thể layout**, 4/6 khác nhau đúng ký tự rác ô `R1`. **Không cần một tab web cho mỗi nhân viên.** |
| P2 | Dòng tổng ngày/tháng nằm **lẫn trong vùng dữ liệu** | `RowType` + outline row khi xuất (DEC-115) |
| P3 | Bố cục Summary một bảng phẳng 16 cột | Thẻ KPI + bảng + drill-down + bộ lọc |
| P4 | Thứ tự và tên cột Excel | Tự do, miễn giữ ngữ nghĩa mục 5.2 |
| P5 | Ô rác `R1`, `COUNTIF` bắt đầu từ dòng tiêu đề | Không tái tạo |

### 5.4 DEFER

| # | Năng lực | Lý do |
|---|---|---|
| D1 | Tỉ suất lợi nhuận (margin) | `DEC-PHB02-07` chốt "So tháng trước" nhưng **không** đề cập margin. Margin vẫn LATER theo §L — **không chặn PHB-03** |
| D2 | Cùng kỳ năm trước / YTD | Cần `Summary 2025`, hiện `REFERENCE_ONLY` — PHB-04 |
| D3 | Xu hướng nhân viên nhiều tháng | Cần ≥3 tháng dữ liệu pipeline |
| D4 | Average order value | Không tồn tại trong báo cáo tay |
| D5 | Sales mix `employee_group` × `product_group` | Ngoài phạm vi hẹp mà `DEC-PHB02-05` cho phép |
| D6 | Top-N nhân viên trên Tổng quan; Δ kỳ trước theo nhân viên | `USEFUL_BUT_DEFER` |
| D7 | Thưởng / ngày công / lương (cột `O`–`S`) | Luật HR — N.9 |
| D8 | Tỉ lệ tồn kho (cột `J`) | Cột `Nơi nhập` không có trong file ERP |
| D9 | **UX-PI-01 — Inline Product Identity Resolution** | **DEFERRED / NON-BLOCKING.** Ý định: Reports hiện các mô tả duy nhất chưa phân giải và cho Owner phân giải từ UI của Reports, trong khi **Tracking vẫn là Product Identity Authority**. `NB-6` có thể gộp vào đây. **KHÔNG implement bây giờ.** Repo chưa có vị trí backlog canonical nên mục này là nơi lưu giữ |

### 5.5 DROP_INTENTIONALLY

`DEC-PHB02-01` cho phép bỏ dứt khoát mọi artifact bảng tính dưới đây.

| # | Yếu tố | Vì sao bỏ |
|---|---|---|
| X1 | `E1 = SUM(E3:E945) − D1 − C1` | Trừ một **tỉ lệ phần trăm** khỏi một **số lượng** (lỗi A1). Thay bằng `DEC-PHB02-03` |
| X2 | `F` dòng tổng tháng = `SUM(F4:F8)` | Bỏ sót cả Nội thành lẫn Gia dụng; riêng 01.2026 thiếu **60,0 %** tổng DS quy đổi (lỗi A2). Thay bằng `DEC-PHB02-04` "TẤT CẢ đơn đủ điều kiện" |
| X3 | Phép `/2` bù layout | DEC-115: một `/2` trong logic tổng hợp bị coi là **lỗi** |
| X4 | `Summary 2026!D64 = '07.2026 Tín Phát'!$E$1` | Tham chiếu sai sheet (lỗi A4) |
| X5 | Mẫu số tháng trước gõ cứng (`=F4/1571182` …) | Lỗi A6. `DEC-PHB02-07` yêu cầu xử lý mẫu số 0 tường minh thay vì số cứng |
| X6 | Số `X` gõ tay trong công thức quy đổi của Hoàng/Kiên | Gồm `05.2026 Hoàng = 3770+16190` và Kiên giữ `7565` suốt 06/07/08.2026 (lỗi B2) |
| X7 | `G1` trùng `C1` viết khác vùng quét | Lỗi B5 |
| X8 | `B1 = 0` trên mọi sheet kênh | Artifact nhập liệu (kênh không điền `Trans`), không phải sự thật nghiệp vụ |
| **X9** | **Cột `I` "So tháng trước" tính trên DS quy đổi** | `DEC-PHB02-07` chốt chỉ tiêu được so là **DOANH THU BÁN HÀNG**, không phải DS quy đổi |
| **X10** | **Dòng Summary "Gia dụng" như một thực thể nhân viên** | `DEC-PHB02-05`: Gia dụng là **product-level override**, KHÔNG phải một loại nhân viên |

### 5.6 LEGACY_DEPENDENT (PHB-04) — không implement ở đây

| # | Yêu cầu |
|---|---|
| L1 | `Summary 2025` = `REFERENCE_ONLY` — không import / persist / query / display (DEC-169) |
| L2 | Cùng kỳ năm trước lấy từ `DataChart 2026` cột `AH`, đã import thành `legacy_monthly_reference.sales_prev_year_vnd` |
| L3 | Target lịch sử (`legacy_summary_row.target`) **chỉ đọc**; cấm kết hợp vào chỉ tiêu `PIPELINE_GENERATED`. `DEC-PHB02-06` củng cố: target thật đến từ **cấu hình do Owner nhập**, không từ số lịch sử |
| L4 | Báo cáo tay 2025 và trước kỳ hiện hành = `LEGACY_REFERENCE` — **KHÔNG chạy lại qua pipeline production như raw accounting input** |
| L5 | 2026 sẽ **không** khớp tuyệt đối workbook cũ (DEC-120/DEC-121). `DEC-PHB02-01` nâng điều này thành nguyên tắc chung, không còn là ngoại lệ |
| L6 | `legacy_summary_row` giữ đủ 16 cột `C..S` |

### 5.7 TARGET_DEPENDENT (PHB-05) — không implement ở đây

```text
YÊU CẦU NGHIỆP VỤ ĐÃ FREEZE (DEC-PHB02-06):
  - Target cấu hình được THEO TỪNG NHÂN VIÊN.
  - Owner/người dùng có chỗ để NHẬP và SỬA target.
  - CẤM hard-code giá trị target của từng nhân viên vào logic tính toán.

CHỈ TIÊU ĐƯỢC ÁP  = DS quy đổi (cột N = F/M), KHÔNG phải doanh số, KHÔNG phải lợi nhuận
KỲ                = tháng (+ một target năm ở Summary!M3)

QUAN SÁT TỪ WORKBOOK TAY — THAM CHIẾU, KHÔNG PHẢI NGUỒN:
  target KHÔNG đổi suốt 8 kỳ 2026:
    Ly · Thắng · Hoàng · Kiên · Linh/Fanpage = 1.300.000
    Tín Phát = 2.700.000 · Nội thành = 12.000.000 · Gia dụng = KHÔNG CÓ
    Công ty/tháng = 28.790.000 · Năm = 345.474.000 (= 12 × 28.790.000)
  Ba điểm bất nhất của số lịch sử (nay KHÔNG còn chặn PHB-02 vì Owner sẽ nhập
  target, không nhập kế thừa số cũ):
    (a) xung đột đơn vị 1.000 lần trong cùng sheet DataChart
        (AJ2 = 28.789.481.081 VND vs J15 = 345.474.000 nghìn đồng);
    (b) tổng target nhân viên 01.2026 = 19.900.000 ≠ target công ty 28.790.000
        (chênh 8.890.000);
    (c) target/ngày chia 350 nhưng tiến độ năm chia 365.
  ⟹ PHB-05 phải chốt ĐƠN VỊ CHUẨN (DEC-106: VND nguyên) khi dựng ô nhập target,
     và KHÔNG kế thừa ba điểm bất nhất trên.
```

---

## 6. Summary Parity Matrix

| Cột tay | Nhãn tay | Công thức tay | Reports SỐ MỚI | PARITY sau freeze |
|---|---|---|---|---|
| `C` | Tổng đơn | `count(Trans)` | Tổng đơn (`COUNT DISTINCT order_key`) | **MATCH** (M1) |
| `D` | Tổng số SP | `SUM(SL) − D1 − C1` | "Tổng số lượng" = `SUM(quantity)` mọi dòng | **RESOLVED** — `DEC-PHB02-03` thay cả hai: `SUM(qty)` khi đơn giá > 1.000.000 (M3) |
| `E` | Tổng bán | `SUM(Giá bán × SL)` | "Doanh thu (net)" | **MATCH với ERP** (M2); khác BC tay đúng phần chiết khấu (S3) — chấp nhận theo `DEC-PHB02-01` |
| `F` | **DS quy đổi** | `=G/tỉ lệ` | **KHÔNG CÓ** | **REQUIRED_V1** — `DEC-PHB02-04`/`05` (M4). Chặn bởi coverage 100 % (S14) |
| `G` | Tổng lợi nhuận | `Σ(Giá bán − Giá nhập TT)×SL` | "Lợi nhuận KPI" + coverage | **SEMANTICS MATCH** (S1); chính thức chỉ khi coverage = 100 % (S14) |
| `H` | Tỉ suất lợi nhuận | `=G/E` | **KHÔNG CÓ** | **DEFER D1** — không chặn PHB-03 |
| `I` | So tháng trước | `=F/F(tháng trước)` trên **DS quy đổi** | Δ trên Tổng đơn + Doanh thu | **RESOLVED** — `DEC-PHB02-07` chốt **doanh thu bán hàng**; công thức tay bị bỏ (X9) |
| `J` | Tỉ lệ tồn kho | `SUMIF(Nơi nhập="Kho")/H1` | **KHÔNG CÓ** | **DEFER D8** — không có nguồn |
| `K` | Lợi nhuận thực tế | `Σ(Giá bán − Giá thực nhập)×SL` | backend, không render | **NOT_DISPLAYED** có chủ đích (S12) |
| `M` | Target | số cứng | **KHÔNG CÓ** | **PHB-05** — `DEC-PHB02-06` (S16) |
| `N` | % Target | `=IFERROR(F/M,"")` | **KHÔNG CÓ** | **PHB-05** — phụ thuộc `F` và `M` |
| `O`–`S` | Thưởng, ngày công, lương | | **KHÔNG CÓ** | **DEFER D7** — luật HR |
| — | — | — | Dòng hàng · Đơn AUTO/cần kiểm tra · Dòng chưa có ngày bán · badge nguồn | **Reports có, tay không** — giữ (S9/S10/S11) |

### 6.1 Ngữ nghĩa kỳ

| | Báo cáo tay | Reports |
|---|---|---|
| Đơn vị kỳ | Tháng, cố định bởi tên sheet | Tháng, dẫn xuất từ `sale_date` thật |
| "Toàn bộ" | Không có | Có — và không bịa kỳ trước để so |
| Dòng thiếu ngày | Rơi vào sheet của người nhập | Rơi khỏi **mọi** kỳ nhất quán, đếm riêng |
| Kỳ trước rỗng | `=F/1571182` số cứng | Mọi ô so sánh để trống (`DEC-PHB02-07`) |

### 6.2 Ngữ nghĩa gộp theo nhân viên (sau `DEC-PHB02-05`)

| | Báo cáo tay | Reports (frozen) |
|---|---|---|
| Thực thể | 8 dòng Summary gồm cả "Nội thành" và "Gia dụng" | Nhân viên thật × nhóm |
| "Nội thành" | **một** dòng như thể một người | **ba** người thật: Vinh, Quý, Hiệp — rate 2 % mặc định (S7) |
| "Gia dụng" | **một** dòng như thể một người | **KHÔNG phải thực thể** — là tick cấp sản phẩm, đổi rate 2 % → 8 % chỉ trong luồng Vinh/Quý/Hiệp (S15, X10) |
| Bán lẻ khác | mỗi người một dòng | mỗi người một dòng, rate 5,5 %, **không** có luồng Gia dụng |
| Tín Phát | một dòng, 7,5 % | một dòng, 7,5 % |
| Nhân viên chưa map | im lặng rơi ra ngoài | "Chưa xác định nhân viên" + Review Queue |
| Đơn nhiều nhân viên | không xử lý | đếm ở từng dòng NV; dòng TỔNG đếm mỗi đơn một lần |

---

## 7. Employee Parity

Chuỗi đánh giá nhân viên của Owner, đọc từ `Summary 2026`:

```
Tổng đơn → Tổng SP → Tổng bán → DS QUY ĐỔI → Lợi nhuận → Tỉ suất
→ So tháng trước → Tỉ lệ tồn kho → Lợi nhuận thực tế
→ TARGET → % TARGET → Thưởng → Ngày công → Lương
```

**Chỉ tiêu quyết định là DS quy đổi** — `DEC-PHB02-04` nâng nó lên thành *"chỉ
tiêu cốt lõi đánh giá hiệu suất nhân viên"*, không còn là artifact bảng tính.

Yêu cầu nghiệp vụ đúng (không phải một tab cho mỗi nhân viên):

> Owner chọn **nhân viên + kỳ** và nhận đủ chuỗi đánh giá.

---

## 8. Metric Semantic Audit (sau freeze)

| METRIC | MANUAL_DEFINITION | REPORTS_DEFINITION (frozen) | PARITY | OWNER_DECISION_REQUIRED |
|---|---|---|---|---|
| **số đơn** | `count(Trans)`; kênh = 0 | `COUNT DISTINCT order_key` | **MATCH** | KHÔNG |
| **tổng bán** | `Σ(Giá bán × SL)`, giá đã sửa tay | `Σ(sell_price×qty)` từ ERP | **MATCH với ERP** | KHÔNG — `DEC-PHB02-01` |
| **doanh số (net)** | không tồn tại riêng | `Σ(sell_price×qty − discount)` | **NOT_IN_MANUAL**, chấp nhận | KHÔNG — DEC-114/DEC-122 |
| **lợi nhuận (KPI)** | `Σ(Giá bán − Giá nhập TT)×SL` | `(SellPrice − KpiPurchasePrice)×Qty − Discount`, chỉ dòng `AUTO` | **SEMANTICS MATCH**; chính thức khi coverage = 100 % | KHÔNG — `DEC-PHB02-02` |
| **lợi nhuận thực tế** | `Σ(Giá bán − Giá thực nhập)×SL` | `accounting_profit`, backend | **MATCH**, NOT_DISPLAYED | KHÔNG |
| **tỷ lệ lợi nhuận** | `H = G/E` | chưa có | **DEFER D1** | KHÔNG (đã DEFER, không chặn) |
| **DS quy đổi** | `LN KPI ÷ tỉ lệ`, `X` gõ tay | `EligibleKpiProfit ÷ rate`, mọi đơn đủ điều kiện | **REQUIRED_V1** | KHÔNG — `DEC-PHB02-04` |
| **conversion / tỉ lệ** | 5,5 · 7,5 · 2 · 8 % | ma trận `DEC-PHB02-05` | **MATCH**; chiều `product_group` thu hẹp về tick thủ công trong luồng wholesale | KHÔNG — `DEC-PHB02-05` |
| **đơn hợp lệ** | đơn Owner chọn giữ, không dấu vết | `AUTO` vs `PENDING` + Review Queue | **THAY THẾ có chủ đích** | KHÔNG — `DEC-PHB02-01`/`04` |
| **số SP / tổng số SP** | `SUM(SL) − phụ − %` (sai) | `SUM(qty)` khi đơn giá > 1.000.000 | **RESOLVED** — 358 / 178 đo được | KHÔNG — `DEC-PHB02-03` |
| **target** | số cứng theo (NV, tháng) | cấu hình do Owner nhập/sửa | **PHB-05** | KHÔNG ở mức ý định — `DEC-PHB02-06` |
| **comparison percentages** | `I = F/F(prev)` trên DS quy đổi | Δ % trên **doanh thu bán hàng** | **RESOLVED** | KHÔNG — `DEC-PHB02-07` |
| **tỉ lệ tồn kho** | `SUMIF(Nơi nhập="Kho")/H1` | chưa có | **DEFER D8** | KHÔNG |

---

## 9. Bảy câu hỏi Owner — TẤT CẢ ĐÃ ĐÓNG

```text
OWNER_DECISIONS_REQUIRED (audit S113) = 7
OWNER_DECISIONS_APPLIED  (freeze S114) = 7
OWNER_DECISIONS_REMAINING              = 0
```

| # | Câu hỏi (S113) | Đóng bởi | Kết quả |
|---|---|---|---|
| **Q1** | Báo cáo tay là oracle SỐ HỌC hay NGHIỆP VỤ? | **`DEC-PHB02-01`** | **CLOSED** — oracle NGHIỆP VỤ (phương án A). Báo cáo tay = BUSINESS REQUIREMENT / SEMANTIC REFERENCE, không phải FINAL NUMERIC AUTHORITY |
| **Q2** | Ngưỡng coverage LN KPI nào là "parity đã giao"? | **`DEC-PHB02-02`** | **CLOSED** — **không có ngưỡng**: chính thức chỉ khi 100 %. Kèm năng lực mới: AUTO-fill + cảnh báo + nhập tay + override sửa được có provenance |
| **Q3** | "Tổng số SP" nghĩa là gì? (`N.7`) | **`DEC-PHB02-03`** | **CLOSED** — `SUM(quantity)` khi giá bán > 1.000.000 VND. Ngưỡng giá, không phải taxonomy. Đo được: 358 / 178 (mục 4.6) |
| **Q4** | Tổng công ty theo tháng gồm những ai? (lỗi A2) | **`DEC-PHB02-01` + `04` + `05`** (đóng bằng dẫn xuất) | **CLOSED** — xem mục 9.1 |
| **Q5** | "Gia dụng" có phải dòng báo cáo hạng nhất? | **`DEC-PHB02-05`** | **CLOSED** — KHÔNG. Là product-level override (tick), chỉ trong luồng Vinh/Quý/Hiệp; cấm suy tự động từ tên hàng; bán lẻ khác không có luồng này |
| **Q6** | Target: tái dùng số lịch sử hay Owner cấp bảng mới? | **`DEC-PHB02-06`** | **CLOSED** ở mức ý định — target **cấu hình được, do Owner nhập/sửa**, cấm hard-code. Số lịch sử ở lại `LEGACY_REFERENCE` (L3). Chi tiết → PHB-05 |
| **Q7** | Mẫu số của tỉ suất và của "So tháng trước" | **`DEC-PHB02-07`** | **CLOSED cho So tháng trước** — chỉ tiêu = **doanh thu bán hàng**. Phần **tỉ suất/margin** không được đề cập ⟹ giữ nguyên **DEFER `D1`**, và vì đã DEFER nên **không** phải quyết định Owner còn treo |

### 9.1 Q4 đóng bằng dẫn xuất — trình bày đầy đủ

`Q4` không được nêu đích danh trong bảy quyết định. Nó đóng vì **nội dung của
nó bị hoà tan** bởi ba quyết định khác. Ghi rõ dẫn xuất để không ai phải đoán
lại:

1. `DEC-PHB02-01`: vùng `SUM(F4:F8)` bị cắt cụt là một **artifact bảng tính**
   nhập tay, không tái tạo được từ nguồn đã chấp nhận ⟹ bị bỏ dứt khoát (X2).
2. `DEC-PHB02-04`: DS quy đổi gồm **TẤT CẢ** đơn đủ điều kiện của nhân viên
   trong tháng, *"không giới hạn ở một tập con được chọn tay"* ⟹ không còn cơ
   sở nào để loại một nhân viên khỏi tổng.
3. `DEC-PHB02-05`: liệt kê **đầy đủ** các nhóm và mỗi nhóm đều **có** một tỉ
   lệ (Tín Phát 7,5 % · Vinh/Quý/Hiệp 2 %/8 % · bán lẻ khác 5,5 %) ⟹ mọi nhân
   viên đều quy đổi được, nên mọi nhân viên đều vào tổng. Đồng thời "Gia dụng"
   **không còn là một thực thể** để mà bao gồm hay loại trừ (X10).

```text
KẾT LUẬN Q4 = Tổng công ty theo tháng cộng ĐỦ mọi nhân viên có
              include_in_kpi = true, ở MỌI cột.
              KHÔNG cần một cờ include_in_company_total tách biệt.
              (Ý tưởng cờ đó ở mục 10.11 KHÔNG trở thành yêu cầu.)
```

---

## 10. Hợp đồng — yêu cầu nghiệp vụ (FROZEN)

Mọi mục dưới đây là **BUSINESS REQUIREMENT**. Không mục nào mô tả bảng, route,
schema hay thành phần UI. Ý tưởng triển khai ở mục 10.11 **không** phải yêu cầu.

### 10.1 Summary V1 — yêu cầu
- **R-S1** Owner chọn một kỳ (tháng) và thấy: số đơn · doanh thu · lợi nhuận KPI kèm coverage trung thực · khối lượng cần kiểm tra.
- **R-S2** Mọi giá trị chưa xác định hiển thị là "chưa biết", không bao giờ là `0`.
- **R-S3** Mọi con số mang nhãn nguồn; số cũ và số mới không bao giờ cộng chung.
- **R-S4** So kỳ trước = **% thay đổi doanh thu bán hàng** so tháng liền trước; mẫu số `0` xử lý tường minh, không bịa vô cực (`DEC-PHB02-07`).
- **R-S5** Dòng không rơi vào kỳ nào phải được phơi ra, không im lặng.
- **R-S6** Tổng công ty cộng đủ mọi nhân viên có `include_in_kpi = true` (mục 9.1).
- **R-S7** *(mới)* Lợi nhuận KPI chỉ được trình bày là **chính thức** khi coverage giá nhập = **100 %**; dưới đó phải nói rõ nó chưa chính thức và phơi phần thiếu (`DEC-PHB02-02`).
- **R-S8** *(mới)* "Tổng số SP" = `SUM(quantity)` của dòng có **đơn giá bán > 1.000.000 VND** (`DEC-PHB02-03`).

### 10.2 Employee V1 — yêu cầu
- **R-E1** Owner chọn **nhân viên + kỳ** và nhận đủ chuỗi đánh giá; **không** cần một trang riêng cho mỗi nhân viên.
- **R-E2** Danh tính nhân viên được bảo toàn: Vinh/Quý/Hiệp là ba người trong nhóm wholesale/nội-thành.
- **R-E3** Đổi tên và vào/ra giữa chừng xử lý bằng hiệu lực theo thời gian.
- **R-E4** Nhân viên chưa map không bị bỏ im lặng.
- **R-E5** Một đơn liên quan nhiều nhân viên đếm ở từng dòng NV; dòng TỔNG đếm mỗi đơn một lần, và trang nói rõ điều đó.
- **R-E6** **DS quy đổi theo (nhân viên, kỳ) = `EligibleKpiProfit ÷ rate`** — phép **CHIA**, cộng đủ **mọi** đơn đủ điều kiện trong tháng, không bao giờ `profit × rate`, không bao giờ một tỉ lệ pha trộn (`DEC-PHB02-04`).
- **R-E7** *(mới)* Định tuyến tỉ lệ theo `DEC-PHB02-05`: Tín Phát 7,5 % · Vinh/Quý/Hiệp 2 % (8 % khi sản phẩm được tick `GIA_DUNG`) · bán lẻ khác 5,5 %.
- **R-E8** *(mới)* DS quy đổi **không được** sinh ra từ giá nhập chưa phân giải (`DEC-PHB02-04`).

### 10.3 Giá nhập — yêu cầu *(mới, `DEC-PHB02-02`)*
- **R-P1** AUTO-fill giá nhập bằng thuật toán khớp giá đã được chấp nhận trước đó, bất cứ khi nào nguồn có thẩm quyền cho phép.
- **R-P2** Không phân giải được ⟹ **cảnh báo tường minh** + cho phép **nhập tay**.
- **R-P3** Ô giá nhập **sửa được** kể cả khi đã AUTO-fill.
- **R-P4** Provenance phân biệt tối thiểu `AUTO` vs `MANUAL / MANUAL_OVERRIDE`; **cấm** âm thầm coi override là AUTO.

### 10.4 Định nghĩa đã được chứng minh / đã freeze
`M1`–`M5` (mục 5.1) và `S1`–`S16` (mục 5.2).

### 10.5 Định nghĩa còn mơ hồ cần Owner
```text
KHÔNG CÒN.  OWNER_DECISIONS_REMAINING = 0
```
Các điểm còn chưa nói tới (margin `D1`, tỉ lệ tồn kho `D8`, thưởng/lương `D7`)
đều **đã DEFER**, nên chúng là *phạm vi bị hoãn*, không phải *ngữ nghĩa bị
treo*.

### 10.6 Tự do trình bày
`P1`–`P5`. Đặc biệt: **không tái tạo 56 sheet thành 56 tab.**

### 10.7 Yêu cầu phụ thuộc legacy (PHB-04)
`L1`–`L6` (mục 5.6).

### 10.8 Yêu cầu phụ thuộc target (PHB-05)
Mục 5.7 nguyên khối, đã freeze phần ý định nghiệp vụ bằng `DEC-PHB02-06`.

### 10.9 Loại trừ có chủ đích
`X1`–`X10` (mục 5.5).

### 10.10 Cải thiện đã hoãn
`D1`–`D9` (mục 5.4), gồm `UX-PI-01`.

### 10.11 Ý tưởng triển khai — KHÔNG phải yêu cầu
Ghi lại để không mất, **không** được coi là đã chốt: tổng hợp
`converted_revenue` ở tầng truy vấn thay vì tầng UI · tái dùng slot từ vựng
`PRICE_SOURCE_MANUAL` đã dành sẵn cho override · `LearnedProductGroupProvider`
cắm vào seam `ProductGroupProvider` đã có · bảng target theo `(nhân viên,
tháng)` với `effective_from`/`effective_to`. Cờ `include_in_company_total`
**đã bị bác bỏ** (mục 9.1) và không còn nằm ở đây.

---

## 11. Sẵn sàng cho PHB-03

```text
PHB_03_READY = YES
```

Bốn quyết định từng chặn PHB-03 (`Q1`, `Q2`, `Q4`, `Q7`) đều đã đóng, và mọi
chỉ tiêu của Summary + Employee V1 nay đều có định nghĩa có thẩm quyền:

| Chỉ tiêu V1 | Định nghĩa có thẩm quyền |
|---|---|
| Số đơn | `COUNT DISTINCT order_key` (M1) |
| Doanh thu | `Σ(sell_price×qty − discount)` (DEC-114) |
| Lợi nhuận KPI | `DEC-143` + gate 100 % của `DEC-PHB02-02` |
| Tổng số SP | `DEC-PHB02-03` — đơn giá > 1.000.000 |
| DS quy đổi | `DEC-PHB02-04` (chia) + `DEC-PHB02-05` (ma trận tỉ lệ) |
| So tháng trước | `DEC-PHB02-07` — doanh thu bán hàng |
| Target | `DEC-PHB02-06` — cấu hình được; chi tiết ở PHB-05 |
| Tỉ suất | DEFER `D1` — không thuộc V1 |

Không còn ngữ nghĩa nghiệp vụ nào phải đoán.

### 11.1 Ghi chú SEQUENCING cho PHB-03 — không giải ở đây

Đây là **mối bận tâm triển khai**, ghi lại đúng mức cần cho vertical kế tiếp,
**không** phải một câu hỏi Owner và **không** phải một khoảng trống ngữ nghĩa:

```text
DS quy đổi (R-E6) và lợi nhuận KPI CHÍNH THỨC (R-S7) đều phụ thuộc
coverage giá nhập = 100 %.
Coverage đo được hôm nay: 0–2/351 (golden) · 34/142 (production 09/2026).
Đường ghi để đạt 100 % (R-P1…R-P4: nhập tay + override có provenance)
CHƯA TỒN TẠI — tầng analytics hiện là CHỈ-ĐỌC theo thiết kế, và
PRICE_SOURCE_MANUAL mới chỉ là một slot từ vựng đã dành sẵn.

⟹ Khi mở PHB-03, quyết định PHẠM VI cần trả lời trước:
   PHB-03 có bao gồm đường nhập/override giá nhập không, hay đường đó
   thuộc một vertical riêng đứng TRƯỚC phần DS quy đổi của PHB-03?
   Đây là quyết định ROADMAP, không phải quyết định ngữ nghĩa.
```

---

## 12. Findings sau freeze

Finding **không** tự sinh task.

### BLOCKING: 0 — cả hai đã ĐÓNG

```text
FIND-PHB02-B01  PARITY ORACLE KHÔNG XÁC ĐỊNH
                → CLOSED bởi DEC-PHB02-01. Báo cáo tay = semantic reference,
                  không phải numeric authority. Chênh lệch so với số tay
                  KHÔNG còn là blocker; chỉ vi phạm business rule đã duyệt
                  hoặc nguồn có thẩm quyền mới đáng quan tâm.

FIND-PHB02-B02  DS QUY ĐỔI SẼ ĐƯỢC IMPLEMENT VỚI NGỮ NGHĨA ĐOÁN
                → CLOSED bởi DEC-PHB02-04 (công thức chia + phạm vi mọi đơn),
                  DEC-PHB02-05 (ma trận tỉ lệ đầy đủ + phạm vi Gia dụng), và
                  DEC-PHB02-02 (điều kiện coverage). Không còn chỗ nào phải đoán.
```

### NON-BLOCKING

```text
FIND-PHB02-N01  635/18.148 ô giá gõ tay trong báo cáo tay, không dấu vết.
                → GIỮ làm dữ kiện lịch sử. DEC-PHB02-01 khiến nó không còn là
                  vấn đề cần giải: đó là lý do báo cáo tay không phải oracle.

FIND-PHB02-N02  Target công ty ≠ tổng target nhân viên (chênh 8.890.000).
FIND-PHB02-N03  Xung đột đơn vị 1.000 lần trong cùng sheet DataChart.
                → N02/N03 HẠ CẤP: không còn là vấn đề của PHB-02. DEC-PHB02-06
                  chốt target đến từ cấu hình do Owner nhập, không kế thừa số
                  lịch sử. Giữ lại như cảnh báo đơn vị cho PHB-05 (mục 5.7).

FIND-PHB02-N04  Repo chưa có vị trí backlog UX canonical.
                → GIỮ. UX-PI-01 lưu tại mục 5.4 D9.

FIND-PHB02-N05  app/modules/conversion/ chưa có consumer tổng hợp converted_revenue.
                → ĐỔI TRẠNG THÁI: từ "trạng thái đúng theo §L LATER" thành
                  KHOẢNG TRỐNG ĐÃ BIẾT của PHB-03. DEC-PHB02-04 nâng DS quy đổi
                  thành chỉ tiêu cốt lõi bắt buộc, nên đây là việc của PHB-03,
                  không còn là "để sau".

FIND-PHB02-N06  (mới) DEC-PHB02-04 viết PROFIT = sale_price − purchase_price,
                là minh hoạ theo một đơn vị sản phẩm. Công thức thi hành vẫn là
                EligibleKpiProfit của DEC-143 ((SellPrice − KpiPurchasePrice)
                × Quantity − Discount). Điểm xác nhận MỘT DÒNG cho PHB-03;
                không phải câu hỏi Owner (xem ghi chú ở DEC-PHB02-04).

FIND-PHB02-N07  (mới) DEC-PHB02-05 định tuyến theo NHÓM NHÂN VIÊN và không
                nhắc tới lead_source. Engine hiện định tuyến qua lead_source
                (bộ lọc cứng), với Tín Phát mặc định ADS. Trên MỌI dữ liệu đã
                quan sát hai mô hình cho KẾT QUẢ GIỐNG HỆT — Tín Phát 7,5 %,
                bán lẻ khác 5,5 %, NOI_THANH 2 %/8 % — và chuỗi "ADS" xuất hiện
                0 lần trong cả hai workbook (ads_keyword_cell_hits). Điểm phân
                kỳ DUY NHẤT: một đơn của nhân viên bán lẻ có ghi chú "ADS" sẽ
                ra 7,5 % theo engine nhưng 5,5 % theo cách đọc chữ của
                DEC-PHB02-05. Vì DEC-PHB02-05 nói "tỉ lệ MẶC ĐỊNH", cách đọc
                nhất quán là: DEC-PHB02-05 đặt mặc định, cơ chế lead_source đã
                freeze (DEC-109/DEC-119) vẫn giữ nguyên. NON-BLOCKING (tác động
                thực tế = 0 dòng); PHB-03 xác nhận lại khi implement.

FIND-PHB02-N08  (mới) DEC-PHB02-03 là NGƯỠNG GIÁ, nên vài sản phẩm thật giá
                thấp cũng bị loại (đo được: 2 dòng ở 01.2026, 1 dòng ở 06.2026).
                Đây là đánh đổi CÓ CHỦ ĐÍCH — Owner chỉ thị rõ không mở rộng
                thành taxonomy. Ghi lại để không ai coi là defect.
```

---

## 13. Ràng buộc phạm vi đã tuân thủ

```text
PHB-01 (Product Identity)  = KHÔNG mở lại. UX-PI-01 chỉ là backlog hoãn (5.4 D9).
PHB-03                     = KHÔNG bắt đầu. PHB_03_READY = YES.
PHB-04 (Legacy)            = KHÔNG implement. Yêu cầu bảo toàn L1–L6.
PHB-05 (Target)            = KHÔNG implement. Ý định nghiệp vụ freeze ở S16/5.7.
ProductGroup redesign      = KHÔNG. DEC-PHB02-05 thu hẹp về một tick thủ công
                             trong đúng một luồng.
PRODUCTION CODE            = 0 dòng thay đổi
SCOPE_DRIFT                = NO
BUSINESS_PARITY_CONTRACT   = FROZEN
PHB_02                     = DONE
```

### 13.1 Exit Criteria của PHB-02 — bằng chứng, không phải khẳng định

`PHB-02` là một vertical HỢP ĐỒNG NGHIỆP VỤ (không có production code), nên
Exit Criteria của nó là các điều kiện dưới đây, mỗi điều kiện chỉ tới bằng
chứng cụ thể trong chính tài liệu này:

| # | Exit Criterion | Trạng thái | Bằng chứng |
|---|---|---|---|
| E1 | Xác định được báo cáo tay của Owner và phân biệt nó với raw input và legacy | **PASS** | Mục 2 |
| E2 | Năng lực hiện tại của Reports được map, tách `DISPLAY EXISTS` khỏi `SEMANTICS VERIFIED` | **PASS** | Mục 3 |
| E3 | Năng lực nghiệp vụ của báo cáo tay được trích, không suy đoán cấu trúc | **PASS** | Mục 2, 4, 6, 7 — nguồn `evidence.json` tái tạo được |
| E4 | Mọi năng lực có ý nghĩa được phân loại vào đúng MỘT nhóm, kèm bằng chứng/lý do | **PASS** | Mục 5.1–5.7 (`M1`–`M5`, `S1`–`S16`, `P1`–`P5`, `D1`–`D9`, `X1`–`X10`, `L1`–`L6`, 5.7) |
| E5 | Summary Parity Matrix hoàn chỉnh | **PASS** | Mục 6 |
| E6 | Employee Parity hoàn chỉnh, không kết luận "một tab mỗi nhân viên" | **PASS** | Mục 7, `P1` |
| E7 | Metric Semantic Audit cho mọi chỉ tiêu giá trị cao | **PASS** | Mục 8 |
| E8 | Mọi quyết định Owner cần thiết đã được nêu và ĐÃ ĐƯỢC TRẢ LỜI | **PASS** | Mục 9 — 7/7 đóng, `OWNER_DECISIONS_REMAINING = 0` |
| E9 | Hợp đồng tách BUSINESS REQUIREMENT khỏi IMPLEMENTATION IDEA | **PASS** | Mục 10.1–10.10 vs 10.11 |
| E10 | Biên PHB-04 (Legacy) và PHB-05 (Target) được giữ, không implement | **PASS** | Mục 5.6, 5.7, 13 |
| E11 | 0 dòng production code thay đổi | **PASS** | `git diff` chỉ chạm 3 file tài liệu (S113 + S114) |
| E12 | Governance validator giữ nguyên baseline | **PASS** | Mục 1.2 + bàn giao S114 |

Không có check REQUIRED nào ở trạng thái `NOT_TESTED`, `FAIL` hay `BLOCKED`.
