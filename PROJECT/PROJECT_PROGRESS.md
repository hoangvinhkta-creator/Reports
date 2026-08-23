# TIẾN ĐỘ DỰ ÁN

## Tóm tắt dự án

Project:
Tín Phát — Công cụ tự động tạo Báo cáo Kinh doanh

Objective:
Thay thế việc lắp ráp thủ công hằng tháng file `Báo cáo Kinh doanh 2026.xlsx`
bằng một công cụ nạp sổ bán hàng thô từ ERP, phân loại nguồn đơn của từng đơn
hàng, tính lợi nhuận kế toán và lợi nhuận KPI tách riêng, quy đổi doanh thu qua
hai bucket độc lập PERSONAL/ADS, tạo Summary tháng và năm, và cho nhiều người
xem/sửa dữ liệu hằng ngày trước khi xuất `.xlsx`.

Project Type:
NEW (ứng dụng xây mới, thay thế một quy trình dựa trên bảng tính)

Profile:
PRODUCT

Last Updated:
2026-08-22 (S000)

Overall Status:
IN_PROGRESS

Current Phase:
PHASE-00 — Bootstrap governance và phân tích nguồn

Current Task:
GATE-00 — chờ chủ dự án duyệt `docs/analysis/`

Current Task Mode:
MAJOR

Next Recommended Task:
TASK-101 — importer + normalizer (đang bị GATE-00 chặn)

## Roadmap tổng thể

- [x] PHASE-00 — Bootstrap governance và phân tích nguồn
  - [x] TASK-000 — Đưa gói governance lên gốc repository (MICRO)
  - [x] TASK-001 — S000: chọn profile và khởi tạo trạng thái dự án (MAJOR)
  - [x] TASK-002 — Phân tích workbook nguồn, 6 tài liệu theo mục 27 đặc tả (MAJOR)
  - [x] TASK-003 — ADR-101/102/103 (MICRO)
  - [ ] GATE-00 — Chủ dự án duyệt `docs/analysis/` trước khi có dòng code ứng dụng nào

- [ ] PHASE-01 — Engine tính toán (Python thuần, không UI, không database)
  - [ ] TASK-101 — importer + normalizer. Thực hiện 7 bước đầu của import
        workflow mục §22 đặc tả: đọc `.xlsx`, báo cáo metadata (số dòng,
        khoảng ngày, tổng doanh số, số đơn, số NVBH) trước khi commit, chuẩn
        hóa cột, áp employee mapping, nhóm theo OrderID, áp rule ADS ở cấp
        đơn, propagate nguồn đơn xuống line item. Trừ `Chiết khấu` khỏi doanh
        số (DEC-114).
  - [ ] TASK-102 — employee_mapper
  - [ ] TASK-103 — order_builder
  - [ ] TASK-104 — lead_source_engine (rule ADS)
  - [ ] TASK-105 — price_engine + interface PriceProvider. Bước 8 của §22 đặc
        tả: tra giá nhập nếu có Price Master, chưa có thì Pending.
  - [ ] TASK-106 — adjustment_engine. Bước 9 của §22 đặc tả.
  - [ ] TASK-107 — profit_engine. Bước 11 của §22 đặc tả, phần lợi nhuận.
  - [ ] TASK-108 — conversion_engine (2 bucket PERSONAL/ADS). Bước 10 và 11
        của §22 đặc tả: chọn scheme theo nguồn đơn và thời gian, sau đó quy
        đổi từng bucket độc lập.
  - [ ] TASK-109 — summary_engine. Mục §15 đặc tả: Summary tháng có 3 cột
        Personal / ADS / Total cho Tổng đơn, Số SP, Doanh số, LN KPI, DS quy
        đổi, DSQĐ/đơn, Lợi nhuận thực, % Target — **và tương tự theo từng
        nhân viên dạng YTD**, để tách bạch năng lực tự bán với năng lực xử lý
        lead do công ty tạo ra.
  - [ ] TASK-110 — validation + Review Queue. Mục §18 đặc tả, 5 loại cảnh báo:
        `Missing` (thiếu ngày, OrderID, nhân viên, số lượng, doanh số, giá
        nhập), `Suspicious` (SL ≤ 0, giá bán = 0, giá nhập > giá bán, lợi
        nhuận âm — 1.912 dòng như vậy trong mẫu), `Order inconsistency` (cùng
        OrderID, khác nhân viên), `Source classification` (override tay
        không khớp rule ADS), `Duplicate` (cùng `source_file` +
        `source_row`). Không bao giờ chặn toàn bộ import.
  - [ ] TASK-111 — excel_exporter. Mục §23 đặc tả, 5 loại sheet: Summary;
        Processed Data; sheet `MM.YYYY Employee` theo từng nhân viên khi bật
        tùy chọn; Config Snapshot (employee mapping, source rules, conversion
        rules, adjustment rules, target); Audit/Overrides. Personal / ADS /
        Total luôn hiển thị ở cả sheet chi tiết lẫn Summary. Dòng tổng phụ
        mang nhãn `RowType` và nằm ngoài mọi vùng SUM (DEC-115).
  - [ ] TASK-112 — CLI
  - [ ] GATE-01 — Đối chiếu với file thô thật; xác nhận mốc di trú DEC-112

- [ ] PHASE-02 — Lưu trữ và API
  - [ ] TASK-201 — schema database + migration
  - [ ] TASK-202 — audit_service
  - [ ] TASK-203 — HTTP API
  - [ ] TASK-204 — authentication và phân quyền
  - [ ] TASK-205 — recalculate tăng dần (incremental)

- [ ] PHASE-03 — Giao diện Web
  - [ ] TASK-301 — upload và xem trước khi import
  - [ ] TASK-302 — lưới chi tiết nhân viên theo tháng, sửa inline
  - [ ] TASK-303 — Summary tháng và dashboard năm. Mục §16 đặc tả: chuyển đổi
        metric giữa Orders / Sales / Converted Revenue / Accounting Profit /
        KPI Profit / % Target; lọc theo nguồn đơn All / Personal / ADS; so
        sánh nhân viên theo doanh thu quy đổi Personal và Ads riêng biệt;
        trend theo tháng cho từng nguồn đơn; tỉ trọng ADS trên tổng doanh thu
        quy đổi của mỗi người.
  - [ ] TASK-304 — màn hình cấu hình
  - [ ] TASK-305 — màn hình review queue và audit
  - [ ] TASK-306 — xuất Excel
  - [ ] GATE-03 — Nghiệm thu MVP, mục 28 đặc tả, đủ 14 tiêu chí

- [ ] PHASE-04 — Hoàn thiện
  - [ ] TASK-401 — tích hợp PriceMasterProvider. Schema mục §20 đặc tả:
        ProductCode, ProductName, Supplier, EffectiveFrom, EffectiveTo,
        PurchasePrice, Source, UpdatedAt. Tra theo ProductCode + SaleDate;
        giá tra được chỉ là giá trị *đề xuất*, luôn override được.
  - [ ] TASK-402 — product_mapper
  - [ ] TASK-403 — công thức hóa target và hoa hồng
  - [ ] TASK-404 — sheet kênh và Split Conversion. Mục §12 đặc tả: Split
        Conversion chỉ hỗ trợ như một ngoại lệ — workflow thông thường vẫn là
        một OrderID → một LeadSource → một ConversionScheme.

## Độ phủ đặc tả

Toàn bộ 31 mục của `docs/spec/Dac_ta_cong_cu_bao_cao_kinh_doanh.docx` đã được
truy vết tới một artifact và một task trong `docs/analysis/07_SPEC_COVERAGE.md`.
Không mục nào chưa được giao. Mục 27, 29 và 31 đã hoàn thành; các mục còn lại
đã phân tích hoặc ghi nhận, chờ Phase 1.

## Sơ đồ phụ thuộc sơ bộ

```
TASK-000 → TASK-001 → TASK-002 → TASK-003 → GATE-00
GATE-00  → TASK-101 → TASK-102 → TASK-103 → TASK-104
                                   ↓          ↓
                        TASK-105 → TASK-106 → TASK-107 → TASK-108 → TASK-109
                                                                       ↓
                                              TASK-110 ─────────────→ TASK-111 → TASK-112 → GATE-01
GATE-01  → TASK-201 → TASK-202 → TASK-203 → TASK-204 → TASK-205
TASK-205 → TASK-301 … TASK-306 → GATE-03 → PHASE-04
```

Làm song song được: TASK-105 có thể chạy cùng lúc với TASK-103/TASK-104;
TASK-110 có thể chạy cùng lúc với TASK-108/TASK-109.

## Chấm điểm sơ bộ

| Task | Difficulty | Risk | Blast Radius | Mode | Primary Tier | Escalation |
|---|---|---|---|---|---|---|
| TASK-000 | 1 | 1 | 2 | MICRO | A | B |
| TASK-001 | 2 | 2 | 1 | MAJOR | C | — |
| TASK-002 | 3 | 2 | 1 | MAJOR | C | — |
| TASK-003 | 2 | 2 | 2 | MICRO | C | — |
| TASK-101 | 3 | 3 | 3 | MAJOR | B | C |
| TASK-102 | 2 | 3 | 3 | MAJOR | B | C |
| TASK-103 | 2 | 4 | 4 | MAJOR | B | C |
| TASK-104 | 3 | 4 | 5 | MAJOR | C | — |
| TASK-105 | 3 | 3 | 3 | MAJOR | B | C |
| TASK-106 | 4 | 4 | 4 | MAJOR | C | — |
| TASK-107 | 2 | 4 | 4 | MAJOR | B | C |
| TASK-108 | 3 | 5 | 5 | MAJOR | C | — |
| TASK-109 | 3 | 4 | 4 | MAJOR | B | C |
| TASK-110 | 2 | 2 | 2 | MAJOR | B | C |
| TASK-111 | 3 | 2 | 2 | MAJOR | B | C |
| TASK-112 | 1 | 2 | 2 | MICRO | A | B |
| TASK-201 | 3 | 4 | 5 | MAJOR | C | — |
| TASK-202 | 3 | 4 | 4 | MAJOR | C | — |
| TASK-203 | 3 | 3 | 4 | MAJOR | B | C |
| TASK-204 | 3 | 5 | 5 | MAJOR | C | — |
| TASK-205 | 4 | 4 | 4 | MAJOR | C | — |
| TASK-301…306 | 3 | 2 | 3 | MAJOR | B | C |

Risk 4–5 tập trung ở TASK-104, TASK-106, TASK-108, TASK-201, TASK-204 và
TASK-205 — những task mà một lỗi âm thầm trở thành một con số sai trên lương
của ai đó, hoặc rò rỉ dữ liệu cá nhân khách hàng. Các task này bắt buộc E1 và
khuyến nghị E2 theo quy tắc bằng chứng của profile.

## Completion Gate sơ bộ

Được chốt và đóng băng cho từng task trước khi task đó READY. Các REQUIRED
check sơ bộ ghi nhận ngay bây giờ:

- Toàn bộ PHASE-01: số đơn duy nhất của Tín Phát phải bằng 254 cho 01.2026 và
  146 cho 06.2026 đối chiếu với file thô thật (E1). Mọi chênh lệch còn lại so
  với báo cáo mẫu phải được giải thích bằng văn bản, không được làm tròn cho
  khớp.
- TASK-108: sau khi nạp số di trú của DEC-112, tổng doanh thu quy đổi của
  Hoàng và Kiên trong 01–08.2026 phải bằng 13.883.242 nghìn đồng (E1).
- TASK-108: số di trú và đơn được rule phân loại ADS phải loại trừ nhau trong
  cùng một nhân viên-tháng; nếu chồng nhau phải đưa vào review queue, không
  được cộng dồn (E1).
- TASK-109/111: không có phép chia bù nào trong logic tổng hợp. Mọi con số
  cộng đúng một lần; dòng tổng phụ mang nhãn `RowType` và nằm ngoài mọi vùng
  SUM (DEC-115). Một phép `/2` trong logic tổng hợp là một lỗi
  (E1, kiểm chứng được bằng grep).
- TASK-101: `Chiết khấu` bị trừ khỏi doanh số ở toàn bộ 408 dòng bị ảnh hưởng;
  tổng 6 tháng là 36.750 nghìn đồng, trong đó 26.300 là của Ly (E1).
- TASK-104: cả 8 test case ADS ở mục 29 đặc tả đều PASS (E1).
- TASK-108: `TotalConvertedRevenue == PersonalConvertedRevenue + AdsConvertedRevenue`
  đúng cho mọi nhân viên-tháng, và không có đường code nào chia một lợi nhuận
  gộp cho một tỉ lệ duy nhất (E1).
- TASK-201/204: không có dữ liệu cá nhân khách hàng trong log ứng dụng; kiểm
  tra vai trò thực hiện ở phía server (E1, hướng tới E2).
- Mọi phase: không tên nhân viên, tỉ lệ quy đổi, target, số tiền adjustment
  hay từ khóa ADS nào xuất hiện dưới dạng literal trong mã nguồn ứng dụng
  (E1, kiểm chứng được bằng grep).

## Trạng thái Task hiện tại

Task:
GATE-00 — chủ dự án duyệt phần phân tích nguồn

Task Mode:
MAJOR

Status:
VERIFYING — chờ chủ dự án duyệt `docs/analysis/`

Required Gate Progress:
7/7 tài liệu phân tích đã viết; 3/3 ADR đã viết; 31/31 mục đặc tả đã truy vết;
16/16 quyết định đã ghi nhận; 8/8 câu hỏi chặn đã trả lời (C1–C8); 1 giả định
đã nêu rõ còn treo (C4b); 0/1 lượt duyệt.

Primary Agent Tier:
C

Escalation Tier:
—

### GATE-00 đang chờ điều gì

Đúng một việc: chủ dự án đọc `docs/analysis/` và xác nhận mapping cùng
business rule là đúng. Phase 1 bắt đầu ngay khi có xác nhận đó.

### Đã trả lời ngày 2026-08-22

| # | Câu hỏi | Trả lời |
|---|---|---|
| C1 | Tín Phát có nên mặc định `TINPHAT_ADS` không? | **Có** — mọi đơn của Tín Phát quy đổi 7,5% bất kể ghi chú. DEC-109. Số liệu lịch sử của Tín Phát giờ không cần di trú gì cả. |
| C5 | Loại dòng nào tính vào số SP, doanh số, lợi nhuận, số đơn? | Dòng phụ có giá trị tiền **có** tính vào doanh số và lợi nhuận, không tính vào số SP, và mỗi dòng đều vào hàng đợi duyệt tay để giữ lại hoặc loại trừ. DEC-110. |
| C6 | Nhân viên có sửa được `Diễn giải` không? | **Có.** Mặc định ERP giữ nguyên; nhân viên chỉ sửa khi là đơn ADS. DEC-111. |
| C7 | Lợi nhuận ADS lịch sử của Hoàng và Kiên xử lý thế nào? | **Nhập 14 số theo tháng làm dữ liệu di trú.** DEC-112. Truy lại từng đơn là bất khả thi — không có gì ghi lại đơn nào từng là ADS. |
| C8 | Số SP có loại trừ dòng phụ có giá trị tiền không? | **Có**, và bản thân chỉ số này giá trị thấp — vẫn giữ làm cột nhưng bỏ khỏi tiêu chí gate. DEC-113. |
| C4 | `Chiết khấu` trừ vào đâu? | **Trừ vào doanh số.** DEC-114. Đã xác minh số của ERP là gross, nên đây là một phép sửa thật, không phải trừ hai lần. |
| C2 | Vì sao sheet kênh chia đôi? | **Có dòng tổng phụ theo ngày nằm trong vùng dữ liệu**, nên một phép SUM đơn thuần bị đếm hai lần. Đã giải thích, không tái tạo — dòng tổng phụ chuyển ra ngoài vùng SUM, đánh dấu bằng nhãn `RowType`. DEC-115. |
| C3 | Rule hoa hồng? | **Dựa trên mức đạt target**; công thức hóa ở TASK-403 như kế hoạch. Phase 1 nạp bảng tỉ lệ quan sát được làm dữ liệu. DEC-116. |

### Còn mở

| # | Câu hỏi | Mặc định đang áp dụng | Cần trước |
|---|---|---|---|
| C4b | `Chiết khấu` có trừ vào lợi nhuận cùng số đó không? Chủ dự án chỉ nói về doanh số. | Trừ vào cả lợi nhuận. Giảm doanh số mà không giảm lợi nhuận sẽ báo một tỉ suất lợi nhuận công ty không thực sự đạt được — chiết khấu là tiền đã cho đi. | GATE-01 |

C4b là một giả định đã nêu rõ, không phải một ẩn số: công cụ áp dụng nó,
DEC-114 và `docs/analysis/03_RULE_CLASSIFICATION.md` ghi nhận nó, và đảo lại
chỉ mất một thay đổi cấu hình. Không câu hỏi nào chặn GATE-00.

Cũng đã ghi nhận, không chặn: tổng tháng trong Summary mẫu bỏ sót 60,0% doanh
thu quy đổi (`05 §A2`), và Kiên mang cùng một số ADS gõ tay `7565` suốt ba
tháng liên tiếp (`05 §B2`). Cả hai không phải câu hỏi cần chủ dự án trả lời
ngay — cả hai được ghi lại để giải thích được khi con số của công cụ khác với
bảng tính.

## Micro Task (Inline)

Checklist chuẩn:
`governance/templates/MICRO_TASK_CHECKLIST.md`

### MICRO-003 — Architecture Decision Records
Status:
DONE

Checklist Reference:
`governance/templates/MICRO_TASK_CHECKLIST.md`

Evidence Summary:
E1 — `docs/adr/ADR-101-architecture-and-stack.md`,
`docs/adr/ADR-102-three-layer-data-model-and-audit.md`,
`docs/adr/ADR-103-currency-unit-standard.md` tồn tại và theo đúng cấu trúc
đặt tên/section của `docs/adr/README.md`.

### MICRO-000 — Đưa gói governance lên gốc repository
Status:
DONE

Checklist Reference:
`governance/templates/MICRO_TASK_CHECKLIST.md`

Evidence Summary:
E1 — đã chạy `git mv`, `ls` xác nhận `CLAUDE.md`, `PROJECT/`, `docs/`,
`governance/` ở gốc repository; `git status` cho thấy 74 pure rename, không
đổi nội dung. Commit `8f77e20`.

## Blocker đang hoạt động
- Không có.

## Rủi ro đang hoạt động

- **RISK-01 — Từ khóa ADS chưa có dữ liệu nào để đứng vững.** Chuỗi "ADS"
  xuất hiện 0 lần trong sổ bán hàng thô và 0 lần trong workbook báo cáo. Rule
  từ khóa được xây đúng đặc tả, nhưng chỉ bắt đầu khớp khi cách nhập liệu thay
  đổi. DEC-109 xử lý phần lớn nhất — 1.108 đơn của Tín Phát (12,7%) được phân
  loại ADS từ mặc định cấp nhân viên chứ không phải từ khóa — nên phần chưa
  đánh dấu còn lại là công việc ADS của các nhân viên khác.
  Giảm thiểu: override tay ở cấp OrderID có audit trail; công cụ báo cáo số
  đơn khớp rule mỗi lần import, để một tháng toàn số 0 hiện ra rõ ràng thay vì
  bị mặc nhiên coi là đúng.

- **RISK-02 — ĐÃ XỬ LÝ 2026-08-22.** Tín Phát mặc định `TINPHAT_ADS`
  (DEC-109), nên tỉ lệ 7,5% được giữ nguyên, không con số nào thay đổi. Còn
  lại: đánh dấu một đơn là ADS *làm giảm* doanh thu quy đổi (5,5% chia ra số
  lớn hơn 7,5%), nên đánh dấu ADS quá tay sẽ khiến nhân viên mất tiền. Review
  queue phải hiện cả đơn mới chuyển sang ADS, không chỉ đơn mới chuyển về
  PERSONAL.

- **RISK-03 — Giá nhập vắng mặt ở nguồn.** File thô không mang giá nhập, chỉ
  có lợi nhuận do ERP tính sẵn. Theo quyết định của chủ dự án, trường này giữ
  Pending thay vì suy đoán. Hệ quả: lợi nhuận KPI và doanh thu quy đổi chưa
  đầy đủ cho tới khi công cụ bảng giá được kết nối hoặc giá được nhập tay.
  Công cụ phải hiển thị Pending rõ ràng và không bao giờ được âm thầm coi giá
  thiếu là bằng 0.

- **RISK-04 — Dữ liệu cá nhân khách hàng.** Tên, số điện thoại, địa chỉ trên
  mọi dòng. Dữ liệu mẫu bị `.gitignore` loại trừ; test cần fixture đã ẩn danh;
  trường dữ liệu cá nhân không được lọt vào log ứng dụng.

## Regression còn tồn đọng
- Chưa có — chưa tồn tại mã ứng dụng nào.

## Quyết định gần đây
- Xem `PROJECT/PROJECT_DECISIONS.md` — DEC-101 đến DEC-117.

## Lịch sử Session
- S000 — MỞ DỰ ÁN — 2026-08-22 — Đọc đặc tả và cả hai workbook mẫu; xác minh
  business rule với dữ liệu thật; chọn profile PRODUCT; tạo roadmap, sơ đồ phụ
  thuộc, chấm điểm và completion gate sơ bộ; ghi nhận 8 quyết định chiến thuật
  và 4 rủi ro đang hoạt động. Sau đó hoàn thành TASK-002 (sáu tài liệu phân
  tích, có script trích xuất bằng chứng chạy lại được) và TASK-003 (ba ADR).
  Dừng ở GATE-00.
- 2026-08-23 — Merge PR#4 vào nhánh mặc định `claude/extract-upload-repo-gq2ws4`,
  hợp nhất với nhánh audit bộ khung quản trị (S001–S007). Phát hiện và sửa va
  chạm mã số: cả hai track cùng dùng DEC-001..016 và cả hai đều có một
  `ADR-001`. Renumber toàn bộ quyết định và ADR của dự án Tín Phát sang
  DEC-101..117 / ADR-101..103 (DEC-117 ghi nhận chính việc renumber này);
  khôi phục nguyên văn 16 quyết định gốc của track audit vào
  `docs/audit/DECISIONS.md` để không mất tính toàn vẹn của các tham chiếu
  DEC-XXX mà `docs/audit/`, `docs/sessions/`, `docs/tasks/TASK-REM-*.md` và
  `governance/scripts/governance/README.md` đang trích dẫn. Đã chạy lại cả 5
  validator của governance và bộ test rule ADS sau khi sửa — toàn bộ PASS.
  Nội dung roadmap của dự án Tín Phát không đổi qua lần merge này.

## Session tiếp theo

Recommended Session:
S001 — Phase 1, từ TASK-101 trở đi

Purpose:
Bắt đầu engine tính toán, ngay khi GATE-00 được duyệt. C4b vẫn còn mở, cần
đóng trước GATE-01 — đó là điểm mà các con số bắt đầu được công bố chính thức.
C2, C3 và C8 đã có mặc định ghi nhận, đóng lại đúng lúc ở task/gate tương ứng
của chúng (TASK-404, TASK-403, GATE-01).

Files to read first:
- `PROJECT/PROJECT_PROGRESS.md`
- `PROJECT/PROJECT_PROFILE.md`
- `PROJECT/PROJECT_DECISIONS.md`
- `docs/spec/Dac_ta_cong_cu_bao_cao_kinh_doanh.docx`
- `docs/analysis/`
