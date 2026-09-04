# PHB-03 — SUMMARY + EMPLOYEE BUSINESS PARITY V1

Status: IMPLEMENTED_AWAITING_REVIEW
Task Mode: MAJOR
Priority: REQUIRED
Evidence Level: E1
Executed By: S115 (Claude Opus 5, Claude Code on the web)
Timestamp: 2026-09-04
Risk: 4 (chỉ tiêu ở đây đi thẳng vào đánh giá hiệu suất và thù lao nhân viên)

Nguồn thẩm quyền: `docs/tasks/PHB-02-business-parity-contract.md` (FROZEN) —
`DEC-PHB02-01…07`, `R-S1…R-S8`, `R-E1…R-E8`, `R-P1…R-P4`.

Vertical này trả lời **một** câu hỏi:

> *Owner có thể bỏ workbook tay và dùng Reports để trả lời toàn bộ chuỗi đánh
> giá Summary + Nhân viên hay chưa?*

Đây **không** phải bài tập clone giao diện Excel (`P1`, mục 10.6 hợp đồng), và
**không** phải bài tập đuổi theo con số lịch sử đã sửa tay (`DEC-PHB02-01`).

---

## 1. Target Gate

```text
SOURCE_BRANCH   = claude/business-parity-contract-me80ij
EXPECTED_HEAD   = c996ca8
OBSERVED_HEAD   = c996ca8f92a5abd7d004ffb85a802992dd3c367f   → KHỚP
WORKING_BRANCH  = claude/phb-03-summary-employee-parity-7x3uid (tạo từ đúng HEAD trên)
DEFAULT_BRANCH  = claude/extract-upload-repo-gq2ws4 (origin HEAD branch)
BEHIND_DEFAULT  = 0 commit
CONTRACT        = FROZEN · PHB_03_READY = YES
TARGET_GATE     = PASS
```

Sức khoẻ HEAD tại thời điểm mở phiên (E1, thực thi trong phiên):

```text
python -m pytest tests/ -q                       → 2032 passed, 11 skipped
python -m pytest tests/test_golden_baseline.py -q → 58 passed, 2 skipped
```

---

## 2. Quyết định PHẠM VI mà hợp đồng để mở

Mục 11.1 của hợp đồng để lại đúng một câu hỏi ROADMAP (không phải ngữ nghĩa):

> *PHB-03 có bao gồm đường nhập/override giá nhập không, hay đường đó thuộc
> một vertical riêng đứng TRƯỚC?*

```text
QUYẾT ĐỊNH = PHB-03 BAO GỒM đường ghi giá nhập, ở dạng BOUNDED.
```

Chỉ thị phiên (`PHB-03 §3`) chốt điều này và nói rõ lý do: giá nhập →
`EligibleKpiProfit` → lợi nhuận KPI chính thức → DS quy đổi. Tách nó ra sẽ
giao một PHB-03 mà **không chỉ tiêu quyết định nào** (`DEC-PHB02-04`: DS quy
đổi là *"chỉ tiêu cốt lõi đánh giá hiệu suất nhân viên"*) chạy được.

Ranh giới của "bounded" được ghi ở mục 5 dưới đây.

---

## 3. Định nghĩa `PROFIT_COVERAGE` — điểm cần review kỹ nhất

`DEC-PHB02-02` §4 chốt **gate 100 %** và cấm phát minh ngưỡng khác. Nó **không**
nói 100 % *của cái gì*, và câu đó phải được trả lời trước khi chữ "CHÍNH THỨC"
có nghĩa.

```text
PROFIT_COVERAGE = (số dòng THỰC SỰ góp một giá trị lợi nhuận KPI)
                / (tổng số dòng hiện hành của kỳ)

Một dòng góp giá trị  ⟺  status = "AUTO"                      (D1/P1 đã freeze)
                     VÀ  có giá nhập KPI phân giải được       (AUTO | MANUAL |
                                                               MANUAL_OVERRIDE)
                     VÀ  có sell_price và quantity
```

**Tử số đúng bằng tập được cộng.** Đó là toàn bộ lý do chọn định nghĩa này:
`coverage = 100 %` khi đó tương đương *"mọi dòng của kỳ đều đã có mặt trong con
số này"*, nên nhãn CHÍNH THỨC không thể nói dối. Một định nghĩa rộng hơn —
"số dòng có giá nhập" — sẽ cho `100 %` trong khi tổng vẫn bỏ sót các dòng
`PENDING`, và Owner sẽ ký một con số thiếu.

**Hệ quả đã lường trước, nói thẳng.** Vì `D1/P1` (`TASK-PRA-003`) giữ nguyên —
một dòng `PENDING` KHÔNG vào tổng lợi nhuận KPI kể cả khi có sẵn giá trị —
một kỳ còn dòng chờ kiểm tra sẽ **không** đạt 100 % dù Owner nhập đủ giá nhập.
Điều đó là ĐÚNG, không phải defect: luồng nhập giá bù đúng MỘT input còn
thiếu, nó không phải một lượt duyệt Review Queue. Vì vậy hai lý do "chưa đủ"
được đếm và hiển thị **RIÊNG**:

| Lý do | Đếm ở | Hoàn thiện bằng |
|---|---|---|
| Thiếu giá nhập | `coverage.missing_price_lines` | Luồng nhập giá của PHB-03 |
| Dòng đang chờ kiểm tra | `coverage.review_blocked_lines` | Review Queue (tab Bán hàng) — **ngoài** PHB-03 |

Gộp hai con số này lại sẽ hứa với Owner rằng nhập nốt giá là xong, trong khi
không phải. Xem `FIND-PHB03-N01`.

---

## 4. Chỉ tiêu đã implement — mỗi cái chỉ tới một quyết định

| Chỉ tiêu | Định nghĩa thi hành | Thẩm quyền |
|---|---|---|
| Số đơn | `COUNT DISTINCT order_key` trong phạm vi đang xét | M1 |
| Doanh thu bán hàng | `Σ(sell_price × quantity − discount)` — đọc `total_sales` pipeline đã ghi | DEC-114 |
| Tổng số SP | `SUM(quantity)` khi **đơn giá bán > 1.000.000 VND** (`>` chặt) | `DEC-PHB02-03` |
| Lợi nhuận KPI | `(SellPrice − KpiPurchasePrice) × Quantity − Discount`, chỉ dòng `AUTO` | `DEC-143`/`OD-108B-01` + `FIND-PHB02-N06` |
| DS quy đổi | `EligibleKpiProfit ÷ rate` **theo TỪNG DÒNG** rồi cộng | `DEC-PHB02-04` + `R-E6` |
| Tỉ lệ quy đổi | `config/conversion_rates.yaml` qua `ConversionSchemeResolver` | `DEC-PHB02-05` |
| So tháng trước | `(cur − prev) / prev × 100` trên **doanh thu bán hàng** | `DEC-PHB02-07` |
| Trạng thái CHÍNH THỨC | `PROFIT_COVERAGE = 100 %` (mục 3) | `DEC-PHB02-02` §4 |

Bốn điểm cần nói rõ vì chúng dễ bị implement sai:

1. **DS quy đổi chia ở CẤP DÒNG.** Tỉ lệ đổi ngay bên trong một nhân viên (một
   dòng Gia dụng của Vinh là 8 %, dòng Điện máy kế bên là 2 %). Chia tổng lợi
   nhuận cho một tỉ lệ trung bình là đúng cái sai mà `R-E6` gọi tên.
2. **`profit × rate` không tồn tại ở bất kỳ đâu trong mã.** Có test khẳng định
   kết quả *khác* phép nhân (hai con số cách nhau 178 lần ở tỉ lệ 7,5 %).
3. **Lợi nhuận KPI không được tính lại khi Owner chưa động vào dòng.**
   `compute_eligible_kpi_profit` fail-closed khi `config/eligible_costs.yaml`
   hỏng (`DEC-143` §1); tính lại ở tầng báo cáo sẽ "sửa" một `None` **cố ý**
   thành một con số mà engine đã từ chối tạo ra. Chỉ dòng có override mới
   được tính lại, và bằng đúng công thức đã freeze.
4. **Ngưỡng Tổng số SP là `>` chứ không phải `>=`.** Owner viết
   *"giá bán sản phẩm > 1.000.000 VND"*; một dòng đúng 1.000.000 nằm ở phía
   BỊ LOẠI.

---

## 5. Giá nhập — thẩm quyền, provenance, và ranh giới

### 5.1 Không có authority giá nhập thứ hai

```text
PURCHASE_PRICE_AUTHORITY = tầng báo cáo KPI, bảng kpi_purchase_price_override
                           (origin PIPELINE_GENERATED, migration 0003_business)
```

Ba thẩm quyền hiện có **không bị chạm**:

- `accounting_purchase_price` / `price_source` — PriceProvider
  (`TASK-105`, `105B`–`105E`). Không đường ghi nào từ PHB-03 tới đây.
- `HistoricalConfirmedRegistry` (E-J) — **chỉ pre-cutover**
  (`sale_date < 2026-09-01`), seed từ báo cáo Owner-confirmed thật
  (`INV-47`, `INV-51`, `INV-54`). Dùng nó làm chỗ chứa giá nhập tay
  post-cutover sẽ vi phạm chính ranh giới đó, nên **không tái dụng**.
- `order_line_result_version` — **append-only**, mỗi dòng là kết quả của MỘT
  lần chạy engine. Không `UPDATE` nào.

Giá do Owner nhập vì vậy sống ở bảng riêng và được hợp nhất **lúc ĐỌC**
(`COALESCE` ở `business_queries.build_lines`), nơi provenance vẫn nhìn thấy
được. Đây đúng là slot mà `app/modules/domain/models.py` đã chừa từ
`TASK-105` (`PRICE_SOURCE_MANUAL` — *"for when override/audit trail exists"*)
và đúng ý tưởng triển khai đã ghi ở mục 10.11 hợp đồng.

```text
PURCHASE_PRICE_AUTHORITY_CONFLICT = KHÔNG PHÁT SINH
```

### 5.2 Provenance — do server quyết, không do form khai

```text
không có dòng override                       → AUTO      (hoặc PENDING nếu
                                                pipeline chưa phân giải được)
Owner nhập khi KHÔNG có giá AUTO              → MANUAL
Owner nhập khi ĐÃ có giá AUTO                 → MANUAL_OVERRIDE
```

Giá AUTO được **đọc lại từ server ngay trước khi ghi**
(`BusinessReportService.auto_price_of`). Để trình duyệt tự khai provenance là
mở đúng cánh cửa mà `DEC-PHB02-02` §3 đóng lại. Nhập lại **đúng bằng** giá
AUTO vẫn là `MANUAL_OVERRIDE` — Owner đã ra một quyết định, và xoá dấu vết
quyết định đó là nói dối về nguồn con số.

`auto_price_at_entry` (giá AUTO tại thời điểm ghi đè) là bằng chứng **một
dòng** cho chữ `MANUAL_OVERRIDE`. Không có nó, "override" chỉ là một cái nhãn
tự khai. Nó **không** phải lịch sử phiên bản.

### 5.3 Ranh giới "bounded" đã giữ

KHÔNG dựng (chỉ thị `PHB-03 §3`): hệ thống quản lý giá nhập · luồng duyệt ·
version-control · audit service · trình soạn dữ liệu kinh tế tổng quát.
Persistence mới = **hai bảng**, mỗi bảng giữ đúng MỘT quyết định hiện hành,
ghi đè tại chỗ khi Owner đổi ý.

---

## 6. Gia dụng — phân loại và ranh giới nhóm

```text
GIA_DUNG_AUTHORITY = bảng product_group_classification, khoá theo product_key
                     ( = sha256(NFC(product_raw).strip()), cùng khoá mà
                       order_line_source_version dùng )
```

- **Quyết định tường minh của con người.** Không luật nào trong mã đọc tên
  hàng để suy ra nhóm (`DEC-PHB02-05` cấm). `DefaultProductGroupProvider`
  giữ nguyên hành vi trả `None` (ADR-106 §6).
- **Tick một lần, có hiệu lực mọi kỳ.** Khoá theo `product_key` nên cùng mặt
  hàng không phải phân loại lại — yêu cầu *"persisted sufficiently for repeat
  reporting"*.
- **`DEFAULT` không được coi là thẩm quyền.** Audit PHB-02 quan sát
  `product_group_provenance = DEFAULT` trên 100 % dòng; một dòng chưa được
  tick vẫn giữ nguyên tỉ lệ pipeline đã ghi, và trang nói rõ nhóm hiện tại.
- **Ranh giới 8 % là CẤU TRÚC, không phải một câu `if`.** Dòng `GIA_DUNG_8`
  trong `config/conversion_rates.yaml` khoá trên `employee_group: NOI_THANH`,
  nên một nhân viên bán lẻ có mặt hàng đã tick vẫn khớp dòng phổ quát
  `* + PERSONAL + *` và ra **5,5 %**. Vector nghiệm thu L đo đúng điều này.
- **Không phơi luồng ra nhân viên bán lẻ.** `gia_dung_workflow_applies` gác
  cả khối UI lẫn route (`GET` và `POST` đều 404 cho nhóm khác `NOI_THANH`).
- **Tick có hiệu lực NGAY, không phải nạp lại sổ.** Tỉ lệ được hỏi lại
  `ConversionSchemeResolver` lúc đọc, truyền `as_of = sale_date` (`DEC-121`).
  `conversion_rate_final` đã lưu **không** bị sửa — nó vẫn là bằng chứng của
  lần chạy đã sinh ra nó.

Không có Product Master redesign, không có `LearnedProductGroupProvider`,
không có ProductGroup system tổng quát.

---

## 7. Bề mặt đã giao

| Route | Vai trò | Yêu cầu hợp đồng |
|---|---|---|
| `/kinh-doanh` | **Summary V1** — một kỳ, sáu chỉ tiêu, coverage, So tháng trước, bảng theo nhân viên, dòng chưa có ngày bán | `R-S1`…`R-S8` |
| `/kinh-doanh/nhan-vien` | **Employee V1** — chọn NHÂN VIÊN + KỲ | `R-E1`…`R-E8` |
| `/kinh-doanh/gia-nhap` | Hoàn thiện giá nhập (`GET` danh sách, `POST` ghi/gỡ) | `R-P1`…`R-P4` |
| `/kinh-doanh/gia-dung` | Tick Gia dụng, chỉ Nội thành | `DEC-PHB02-05` |

**Một trang có bộ chọn, không phải một tab mỗi nhân viên** (`R-E1`, `P1`).
56 sheet tay không trở thành 56 trang web.

Trang `/tong-quan` và `/nhan-vien?nguon=moi` của `TASK-PRA-003` **giữ nguyên
không đổi** — chúng là bề mặt đã nghiệm thu với ngữ nghĩa riêng (`D1` coverage
theo dòng AUTO), và viết lại chúng trong PHB-03 sẽ là mở phạm vi.

---

## 8. Vector nghiệm thu — kết quả

Toàn bộ mục 8 của chỉ thị phiên, `tests/test_business_metrics.py` (33 test)
và `tests/test_business_vertical.py` (35 test):

| # | Vector | Kết quả |
|---|---|---|
| A | `1.000.000 / 7,5 %` | `13.333.333,33` **PASS** |
| B | `1.000.000 / 2 %` | `50.000.000,00` **PASS** |
| C | `1.000.000 / 8 %` (Gia dụng) | `12.500.000,00` **PASS** |
| D | `1.000.000 / 5,5 %` | `18.181.818,18` **PASS** |
| E | `SUM(quantity)` khi đơn giá > 1.000.000 | **PASS** (kể cả biên `= 1.000.000` bị loại) |
| F | `99,72 %` KHÔNG mở khoá số chính thức | **PASS** (dựng đúng 350/351) |
| G | `100 %` mở khoá số chính thức | **PASS** |
| H | PENDING → MANUAL → tính lại | **PASS** (đơn vị + qua database + qua HTTP) |
| I | AUTO → MANUAL_OVERRIDE → tính lại | **PASS** |
| J | So tháng trước đúng % doanh thu | **PASS** |
| K | Tháng trước = 0 ⟹ không vô cực/không % gây hiểu nhầm | **PASS** (ba nhánh chữ riêng) |
| L | Chỉ Vinh/Quý/Hiệp đi qua 8 % | **PASS** (đo trên `conversion_rates.yaml` thật) |
| M | Bán lẻ thường không có yêu cầu Gia dụng | **PASS** (UI ẩn + route 404) |

Ngoài 13 vector bắt buộc, các bất biến sau cũng được khẳng định bằng test:
tử số coverage đúng bằng tập được cộng · override sống sót qua một lần nạp
lại sổ · `0/0` không phải "đã đủ 100 %" · `NULL` không bao giờ thành `0` ·
phân hoạch theo nhân viên cộng đúng tổng kỳ · nhân viên chưa map không bị bỏ
im lặng · hàng rào PII · `503` khi chưa có kho dữ liệu.

---

## 9. Bằng chứng thực thi (E1)

```text
python -m pytest tests/ -q                        → 2106 passed, 11 skipped
python -m pytest tests/test_golden_baseline.py -q → 58 passed, 2 skipped
python -m pytest tests/test_business_metrics.py tests/test_business_vertical.py \
                tests/test_business_boundaries.py -q
                                                  → 74 passed

validate_structure           → PASS (21 required path)
validate_project_state       → PASS
validate_evidence            → PASS (155 REQUIRED PASS)
validate_task_completion     → PASS (13 DONE task)
validate_reference_integrity → FAIL với ĐÚNG 3 reference REM-T06 đã biết
                               (baseline không đổi, không phát sinh mới)
```

Golden Baseline **không đổi** (`58 passed, 2 skipped`): PHB-03 không sửa một
kỳ vọng nghiệp vụ nào đã được Owner chấp nhận.

Bốn test của `tests/test_history_db.py` được cập nhật vì bản kiểm kê
schema/migration là một danh sách **đóng** đã freeze, và `DEC-PHB02-02`/
`DEC-PHB02-05` yêu cầu persistence mới. Đây là trường hợp *"frozen business
decisions explicitly supersede an old expectation"*, không phải một lần nới
lỏng tuỳ tiện — chúng vẫn khẳng định danh sách **đóng**, chỉ dài thêm đúng
hai bảng và một revision.

---

## 10. Findings

Finding **không** tự sinh task.

### BLOCKING: 0

### NON-BLOCKING

```text
FIND-PHB03-N01  COVERAGE 100 % CÓ THỂ KHÔNG ĐẠT ĐƯỢC BẰNG RIÊNG LUỒNG NHẬP GIÁ.
                Một kỳ còn dòng `status = PENDING` (lý do khác thiếu giá nhập)
                sẽ không bao giờ đạt 100 %, vì D1/P1 giữ các dòng đó ngoài
                tổng lợi nhuận KPI. Trang phơi con số này RIÊNG
                (`review_blocked_lines`) và nói rõ nhập giá không mở khoá được
                chúng. Đường xử lý là Review Queue đã có, thuộc phạm vi khác.
                KHÔNG mở task ở đây.

FIND-PHB03-N02  FIND-PHB02-N07 ĐÃ XÁC NHẬN LẠI KHI IMPLEMENT.
                Engine định tuyến qua `lead_source` (bộ lọc cứng, DEC-109/119);
                `DEC-PHB02-05` phát biểu theo NHÓM NHÂN VIÊN. Trên
                `config/conversion_rates.yaml` hiện hành, hai cách đọc cho
                CÙNG kết quả ở cả năm tổ hợp thật (đo trong
                `test_the_conversion_rate_matrix_matches_the_frozen_decision`).
                Điểm phân kỳ duy nhất vẫn là một đơn của nhân viên bán lẻ mang
                lead_source ADS — 0 dòng trên mọi dữ liệu đã quan sát.
                Giữ NON-BLOCKING, không đổi cơ chế đã freeze.

FIND-PHB03-N03  GIÁ NHẬP NHẬP TAY KHÔNG CÓ LỊCH SỬ SỬA.
                Bảng ghi đè tại chỗ theo đúng chỉ thị "keep it SMALL" và lệnh
                cấm dựng version-control. `auto_price_at_entry` giữ đúng một
                mốc (giá AUTO tại lần ghi đè gần nhất). Nếu sau này cần dấu
                vết đầy đủ "ai sửa gì lúc nào", đó là một quyết định Owner
                riêng về audit trail, không phải một khiếm khuyết của PHB-03.

FIND-PHB03-N04  `entered_by` / `classified_by` LUÔN `NULL` HÔM NAY.
                Reports chưa có khái niệm người dùng đăng nhập; hai cột tồn
                tại để khi có xác thực thì là một dòng code, không phải một
                migration. Chúng KHÔNG được điền bằng một giá trị bịa.

FIND-PHB03-N05  MIGRATION 0003 PHẢI CHẠY TRƯỚC KHI DEPLOY.
                `ALEMBIC_HEAD` chuyển `0002_snapshots` → `0003_business`, và
                `assert_schema_current` fail-closed nếu database còn ở
                revision cũ (đúng thiết kế). Quy trình `alembic upgrade head`
                trước khi mở cổng đã có sẵn ở `docs/deployment/S071_DEPLOYMENT.md`
                — không có bước mới, chỉ một head mới. Migration là ADDITIVE
                thuần, dữ liệu legacy và pipeline đi qua nguyên vẹn (có test).
```

---

## 11. Ràng buộc phạm vi đã tuân thủ

```text
PHB-04 (Legacy Reference)     = KHÔNG implement
PHB-05 (Target / So target)   = KHÔNG implement — không config, không schema,
                                không ô target nào. Layout Summary/Employee
                                KHÔNG chừa hạ tầng riêng cho nó.
Brand · Advanced Analytics    = KHÔNG
Dashboard redesign            = KHÔNG — /tong-quan, /nhan-vien, /ban-hang,
                                /san-pham, /doanh-so-ngay không đổi một dòng
UX-PI-01 · Tracking · PHB-01  = KHÔNG mở lại
NB-1/NB-3/NB-4/NB-5/NB-6      = KHÔNG
Product Master redesign       = KHÔNG
Generalized purchase-price mgmt = KHÔNG — hai bảng, ghi đè tại chỗ
Generalized ProductGroup system = KHÔNG — một tick, một bảng, một khoá
Broad refactor                = KHÔNG

PRODUCTION_CODE_FILES_CHANGED = 18 dưới app/ + tools/
                                  8 module Python MỚI (app/modules/reporting/*,
                                    app/web/business_*, migration 0003)
                                  3 file SỬA (app/web/server.py + 252 dòng,
                                    tools/db/schema.py + 83, tools/db/__init__.py
                                    đúng 1 dòng ALEMBIC_HEAD)
                                  5 template MỚI + 1 dòng nav ở layout.html
                                  1 khối CSS bổ sung (21 dòng)
                                → 2.223 dòng thêm, 2 dòng xoá dưới app/ + tools/
SCOPE_DRIFT                   = NO
```

---

## 12. Exit Criteria

| # | Exit Criterion | Trạng thái | Bằng chứng |
|---|---|---|---|
| E1 | Target Gate PASS trên đúng HEAD kỳ vọng | **PASS** | Mục 1 |
| E2 | Quyết định phạm vi của mục 11.1 hợp đồng được trả lời tường minh | **PASS** | Mục 2 |
| E3 | Sáu chỉ tiêu V1 implement đúng định nghĩa đã freeze | **PASS** | Mục 4 + `test_business_metrics.py` |
| E4 | `PROFIT_COVERAGE` có định nghĩa nói được và tử số = tập được cộng | **PASS** | Mục 3 + `test_coverage_numerator_equals_the_set_that_is_actually_summed` |
| E5 | Gate 100 % chặn số chính thức; 99,x % KHÔNG mở khoá | **PASS** | Vector F/G |
| E6 | Ba provenance giá nhập phân biệt được, override không bao giờ thành AUTO | **PASS** | Mục 5.2 + vector H/I |
| E7 | Không mở authority giá nhập thứ hai; bảng append-only không bị UPDATE | **PASS** | Mục 5.1 + `test_business_boundaries.py` |
| E8 | Gia dụng: quyết định người, không suy tên hàng, chỉ Nội thành | **PASS** | Mục 6 + vector L/M |
| E9 | Summary V1 + Employee V1 là MỘT trang có bộ chọn | **PASS** | Mục 7 + `test_the_employee_page_is_one_page_with_a_picker_not_one_tab_each` |
| E10 | Vòng lặp `PHB-03 §7` khép kín qua database VÀ qua HTTP | **PASS** | `test_the_owner_workflow_closes_from_pending_to_official`, `test_posting_a_price_through_the_page_recalculates_the_report` |
| E11 | 13 vector nghiệm thu A–M PASS | **PASS** | Mục 8 |
| E12 | Golden Baseline không đổi | **PASS** | Mục 9 — `58 passed, 2 skipped` |
| E13 | Governance validator giữ nguyên baseline | **PASS** | Mục 9 |
| E14 | Biên PHB-04/PHB-05 và mọi mục §9 được giữ | **PASS** | Mục 11 |

Không có check REQUIRED nào ở trạng thái `NOT_TESTED`, `FAIL` hay `BLOCKED`.

`PHB-03` **chưa** `DONE`: theo `governance/core/TASK_COMPLETION_GATE_STANDARD.md`
và chỉ thị phiên, bước kế tiếp là **Independent Review**. Trạng thái hiện tại là
`IMPLEMENTED_AWAITING_REVIEW`.
