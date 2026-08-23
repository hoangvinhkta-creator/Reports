# TIẾN ĐỘ DỰ ÁN

## Đồng Bộ Nhánh

Nhánh mặc định (canonical) trên GitHub remote hiện tại:
`claude/extract-upload-repo-gq2ws4` — xác nhận bằng `git remote show origin`
→ "HEAD branch". Tên này là do lịch sử tạo nhánh, không phải "main" theo
nghĩa đen — coi nó là "main" của dự án cho tới khi owner đổi tên chính thức.

Trước khi đọc phần còn lại của file này, xác nhận bạn đang đứng trên nhánh
đó và đã `git fetch` mới nhất. Xem `CLAUDE.md` → "Đồng Bộ Nhánh" và
`governance/core/00_SESSION_ORCHESTRATION.md` → "Giao thức Mở Phiên" bước 0.
File này từng bị đọc từ một nhánh lỗi thời 14 commit, dẫn tới báo cáo tiến độ
sai — xem DEC-118.

## Hai Track Song Song

Repo này chứa **hai track công việc độc lập**, cả hai đều canonical, cả hai
đều track trong chính file này:

- **Track A — Sản phẩm Tín Phát** (phần "Tóm tắt dự án" → "Session tiếp
  theo" ngay bên dưới) — xây dựng công cụ báo cáo kinh doanh. Đây là track
  đang hoạt động chính (GATE-00 đang chờ owner duyệt).
- **Track B — Governance Remediation** (mục "Track Governance — Bảo Trì Nền
  Tảng (PHASE-GOV)" phía dưới) — sửa chữa chính khung governance của repo.
  Chạy song song, không chặn Track A trừ khi ghi rõ dependency.

**Bản dễ hiểu cho người ngoài dự án:** `PROJECT/LO_TRINH_DE_HIEU.md` — cùng
một lộ trình Track A, viết lại không dùng thuật ngữ kỹ thuật, dành cho chủ
dự án/quản lý không rành code. File đó KHÔNG tự động đồng bộ — **bất kỳ
session nào sửa roadmap Track A trong file này cũng phải cập nhật file đó
theo, cùng một lần sửa** (xem `governance/core/00_SESSION_ORCHESTRATION.md`
→ "Giao thức Đóng Phiên").

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
2026-08-23 (S021 — **Independent Review #5 FAIL, 4 finding, đã sửa toàn bộ
bằng ARCHITECTURE REPAIR**, không phải một vòng patch cục bộ. Audit trước khi
code chỉ ra cả bốn finding là bốn biểu hiện của **một** root cause: validation
tái tạo lại các sự thật production đã biết thay vì nhận lại chúng — và audit
tìm thêm một drift thứ năm reviewer chưa nêu (F3 khớp prefix trên chuỗi đã
normalize trong khi production khớp trên chuỗi thô). Đã **xóa** nguồn sự thật
thứ hai (`select_effective_record`, `_record_key`, vòng khớp prefix riêng);
`EmployeeMapper` nay là nguồn duy nhất và trả `RecordRef` — danh tính của bản
ghi đã load, nên collision là **bất khả**. `MappingFinding` mất hẳn trường
`details`; `ReviewItem` mất hẳn field `affected_count`/`source_row` — tất cả
dẫn xuất từ `RowProvenance`. Ba Human Decision (**HD-110-06/07/08**) ghi thành
**DEC-132**. **330/330 test**, 179 mới so với baseline `c7a1b24`, 0 regression;
L1/L2/L3 chứng minh 0 dịch chuyển nghiệp vụ.

TASK-110 = **IMPLEMENTED — architecture repair sau Independent Review #5**,
**NOT MERGED, NOT DONE**, CHECK-110-16 **BLOCKED**, chờ Review #6.

Lịch sử: S020 sửa Review #4 (2 provenance defect, DEC-131), S019 sửa Review #3
(3 finding, DEC-130), S018 sửa Review #2 (4 finding), S017 sửa Review #1
(6 finding, DEC-129), S016 triển khai, S015 Gate Review (DEC-128).
**Chưa vòng review nào PASS.**)

Overall Status:
IN_PROGRESS

Current Phase:
PHASE-01 — Engine tính toán

Current Task:
TASK-110 — validation + Review Queue — **IMPLEMENTED — architecture repair #2
sau Independent Review #6**. **NOT MERGED. NOT DONE.** CHECK-110-16 =
**BLOCKED**. Sáu vòng review, **cả sáu đều FAIL**; bản sửa vòng #6 đã xong
nhưng **chưa review nào PASS**. Xung đột canonical phát sinh khi triển khai
HD-110-09 đã được giải quyết (DEC-133, phương án A). Chờ Review #7.

Current Task Mode:
MAJOR

Next Recommended Task:
**Independent Review #7 cho TASK-110.** Sáu vòng review đều FAIL và đều đã sửa xong (6 + 4 + 3 + 2 + 4 + 6
finding); mỗi finding có regression hoặc falsification test riêng. Vòng #5 và
#6 là **Architecture Repair**, không phải vá cục bộ. Task vẫn **chưa merge,
chưa DONE**, và **chưa vòng nào PASS**. Tiền lệ TASK-108A-1: 4 vòng review mới
PASS.

Sau đó: **TASK-111 (excel_exporter)** dùng được đầu ra Review Queue cho sheet
Audit/Overrides.

**TASK-109 (summary_engine) bị chặn một phần** — cột "DS quy đổi" và "LN KPI"
cần TASK-108B. Không nên bắt đầu trước khi C15 đóng, nếu không sẽ phải làm
lại một nửa.

TASK-108 gốc đã tách làm ba (DEC-127, Gate v3):
- **108A-1** ConversionScheme Resolution — **DONE** (Review #4 PASS)
- **108A-2** ProductGroup Auto Classification — NOT REQUIRED FOR PHASE 1
- **108B** Converted Revenue — BLOCKED (C15 `EligibleCosts`)

## Roadmap tổng thể

- [x] PHASE-00 — Bootstrap governance và phân tích nguồn
  - [x] TASK-000 — Đưa gói governance lên gốc repository (MICRO). **Trùng
        việc với REM-T02 của Track Governance** — cả hai làm trên hai nhánh
        khác nhau, không biết về nhau, cùng hội tụ đúng một kết quả. Xem
        "Track Governance" bên dưới và DEC-118.
  - [x] TASK-001 — S000: chọn profile và khởi tạo trạng thái dự án (MAJOR)
  - [x] TASK-002 — Phân tích workbook nguồn, 6 tài liệu theo mục 27 đặc tả (MAJOR)
  - [x] TASK-003 — ADR-101/102/103 (MICRO)
  - [x] GATE-00 — Chủ dự án duyệt `docs/analysis/` trước khi có dòng code ứng
        dụng nào. **PASS (DEC-122, 2026-08-23).** Duyệt trực tiếp trong hội
        thoại sau đợt rà soát nghiệp vụ DEC-119/120/121; C4b/C9/C10 đóng cùng
        lúc, C11 còn mở không chặn.

- [ ] PHASE-01 — Engine tính toán (Python thuần, không UI, không database)
  - [x] TASK-101 — importer + normalizer. **DONE** (2026-08-23). Thực hiện 7
        bước đầu của import workflow mục §22 đặc tả: đọc `.xlsx` (header
        dòng 4, data dòng 6), báo cáo metadata trước khi chuẩn hóa, chuẩn
        hóa cột (trừ `Chiết khấu` — DEC-114), áp employee mapping, nhóm theo
        OrderID, áp rule ADS ở cấp đơn, propagate nguồn đơn xuống line item.
        49/49 test PASS trên fixture tổng hợp ẩn danh (DEC-108); **13/13
        REQUIRED check PASS**, bao gồm đối chiếu trên dữ liệu thật Tín Phát
        01.2026 (254 đơn) và 06.2026 (146 đơn) — khớp tuyệt đối, không sai
        lệch nghiệp vụ đáng kể, không sửa business rule để ép khớp. Chi
        tiết đầy đủ + mục "Đối Chiếu Dữ Liệu Thật":
        `docs/tasks/TASK-101-importer-normalizer.md`.
  - [x] TASK-102 — employee_mapper. **Năng lực lõi đã xây trong TASK-101**
        (`app/modules/mapping/employee_mapper.py`, config-driven, effective-
        dated, 7/7 test PASS). Không tạo task riêng trùng lặp — nếu phát sinh
        yêu cầu mở rộng (vd. UI quản lý mapping) sẽ mở lại dưới TASK-304.
  - [x] TASK-103 — order_builder. **Năng lực lõi đã xây trong TASK-101**
        (`app/modules/orders/order_builder.py`, nhóm theo OrderID, 3/3 test
        PASS). Product/transaction classification (dòng phụ có giá trị tiền)
        **chưa làm** — đúng phạm vi gốc của TASK-103, dời sang khi cần
        (DEC-110/113 áp dụng lúc đó).
  - [x] TASK-104 — lead_source_engine (rule ADS). **Đã xây trong TASK-101**
        (`app/modules/lead_source/classifier.py`). Phân giải `LeadSource` ở
        cấp OrderID, đúng hai giá trị `PERSONAL`/`ADS`, chuỗi 4 bậc: override
        tay → rule từ khóa → mặc định cấp nhân viên → mặc định hệ thống
        (DEC-119, ADR-104). 19/19 test PASS, khớp hành vi bản tham chiếu
        `tools/analysis/verify_ads_rule.py` (31/31 PASS) trên 18 case
        LeadSource dùng chung. **Không** quyết định tỉ lệ — đó là việc của
        TASK-108 (ConversionScheme, bước phân giải độc lập).
  - [x] TASK-105 — price_engine + interface PriceProvider. **DONE**
        (2026-08-23). Bước 8 của §22 đặc tả: tra giá nhập nếu có Price
        Master, chưa có thì Pending (DEC-103). `PriceProvider` là Protocol
        ổn định (`lookup(product_code, sale_date) -> Optional[Decimal]`);
        `PendingPriceProvider` là implementation mặc định — đúng cho 100%
        dòng ở Phase 1 vì chưa có Price Master nào tồn tại, không phải giới
        hạn tạm thời. Không bao giờ coi giá thiếu là 0 (kiểm chứng bằng
        test kể cả với provider "thật" nhưng miss một sản phẩm). 9/9
        REQUIRED check PASS, 57/57 test tổng (8 mới, không regression trên
        49 test TASK-101). Chi tiết: `docs/tasks/TASK-105-price-engine.md`.
  - [x] TASK-106 — adjustment_engine. **DONE** (2026-08-23). DEC-125 làm rõ:
        `KpiAdjustment` không có nguồn raw (không có gì để "parse" tự động,
        khác giả định ban đầu) — loại điều chỉnh (`Qua kho`, `NCC giao`,
        `KHBH`, `Thợ lắp`) và phương tiện giao hàng là thứ người dùng chọn
        tay sau khi import. Task giao đúng phần Phase 1 làm được:
        `AirConditionerClassifier` (dò từ khóa điều hòa trên `ProductRaw`) +
        `AdjustmentResolver` (số tiền đề xuất theo `delivery_method_tiers`
        cho Qua kho/NCC giao, `air_conditioner_only_defaults` cho KHBH/Thợ
        lắp — không có mặc định cho non-AC, không bao giờ suy đoán). **Không**
        nối vào `run_import()`, **không** thêm field domain model — cả hai
        thuộc phạm vi override thật (Phase 2/3, TASK-202/302/305). 5/5
        REQUIRED check PASS, 74/74 test tổng (17 mới, không regression).
        Chi tiết: `docs/tasks/TASK-106-adjustment-engine.md`.
  - [x] TASK-107 — profit_engine. **DONE** (2026-08-23). Trước khi code, chủ
        dự án chốt DEC-126 — 6 nguyên tắc ranh giới AccountingProfit/Adjustment.
        Task chỉ triển khai `AccountingProfit = (SellPrice −
        AccountingPurchasePrice) × Quantity` (Universal formula), **không**
        mở rộng sang `EligibleKpiProfit` vì persistence + xác nhận Adjustment
        chưa tồn tại (DEC-126 điểm 3–6). `profit_engine` không phụ thuộc
        `app.modules.adjustment` theo bất kỳ cách nào (kiểm chứng bằng grep).
        Nối vào `run_import()` làm bước 9 — tự động Pending khi giá nhập
        chưa có, không cần logic điều kiện riêng. 6/6 REQUIRED check PASS,
        83/83 test tổng (9 mới, không regression). Chi tiết:
        `docs/tasks/TASK-107-profit-engine.md`.
  - [x] TASK-108A-1 — ConversionScheme Resolution. **DONE**
        (2026-08-23, Independent Review #1→#4, #4 PASS, đã merge). Ba vòng pre-implementation
        review (Gate v1→v3) trước khi code; DEC-127 + ADR-106 chốt: tách
        `Nội thành` thành ba Employee thật (Vinh/Quý/Hiệp) cùng
        `employee_group = NOI_THANH`; thêm dimension `ProductGroup`
        (`DIEN_MAY`/`GIA_DUNG`) ở **cấp product line**; `ConversionScheme`
        hạ từ cấp Order xuống cấp line. Resolver 4 chiều, lọc cứng theo
        `lead_source`, chọn dòng cụ thể nhất theo specificity, hòa điểm là
        lỗi cấu hình, không khớp là `Unresolved`. 16/16 REQUIRED check PASS,
        119/119 test, reconciliation 55 ô cột F Summary 2026 **0 ô lệch** và
        employee mapping đúng trên 14.389 dòng thô thật. Chi tiết:
        `docs/tasks/TASK-108A-1-conversion-scheme-resolver.md`.
  - [ ] TASK-108B — Converted Revenue (2 bucket PERSONAL/ADS). **BLOCKED** —
        cần `EligibleCosts` (C15, chưa có định nghĩa nghiệp vụ), Price
        Master, `OtherKpiAdjustment`, và KPI Adjustment đã xác nhận
        (DEC-126). Bước 11 của §22 đặc tả. Phân giải `ConversionScheme` đã
        xong ở 108A-1; phần còn lại là quy đổi hai bucket
        (DEC-119, DEC-121, ADR-104), sau đó quy đổi từng bucket độc lập rồi
        cộng lại. Engine tự tổng hợp `PersonalProfit`/`AdsProfit` từ phân loại
        cấp đơn — `X` không còn là đầu vào (DEC-120).
  - [ ] TASK-109 — summary_engine. Mục §15 đặc tả: Summary tháng có 3 cột
        Personal / ADS / Total cho Tổng đơn, Số SP, Doanh số, LN KPI, DS quy
        đổi, DSQĐ/đơn, Lợi nhuận thực, % Target — **và tương tự theo từng
        nhân viên dạng YTD**, để tách bạch năng lực tự bán với năng lực xử lý
        lead do công ty tạo ra.
  - [ ] TASK-110 — validation + Review Queue. **IMPLEMENTED — architecture
        repair #2 sau Independent Review #6. NOT MERGED, NOT DONE.** Sáu vòng
        review đều FAIL (6 + 4 + 3 + 2 + 4 + 6 finding, S017–S022); **chưa
        vòng nào PASS**, chờ Review #7. 21/22 REQUIRED check PASS;
        CHECK-110-16 (đối chiếu dữ liệu thật) **BLOCKED** vì thiếu file thô
        production — chủ dự án cho phép giữ, chặn DONE không chặn IMPLEMENTED.
        **342/342 test** (191 mới, 0 regression). Phạm vi
        thật **7 loại** sau DEC-128 (V7 mở thành **F1–F6** theo DEC-129),
        không phải 5 — xem `docs/tasks/TASK-110-validation-review-queue.md`.
        Mục §18 đặc tả, 5 loại gốc:
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
  - [ ] GATE-01 — Đối chiếu với file thô thật; xác nhận chênh lệch +6,0% của
        Hoàng/Kiên do không di trú (DEC-120) là chấp nhận được với số liệu
        thật; đóng C11 (88 dòng chưa map)

- [ ] PHASE-02 — Lưu trữ và API
  - [ ] TASK-201 — schema database + migration
  - [ ] TASK-202 — audit_service
  - [ ] TASK-203 — HTTP API. Triển khai bản đồ route backend trong **ADR-105**
        §2: 24 endpoint dưới tiền tố `/api/v1`, nhóm theo 9 module của
        ADR-101. **Không viết endpoint ghi vào RAW** — `raw_rows` không có
        UPDATE/DELETE theo ADR-102, ở đây điều đó nghĩa là code không được
        phép tồn tại (kiểm chứng bằng `grep`). Mỗi endpoint phải điền đủ
        `API Contract Template` (`governance/core/06_DATABASE_API_RULES.md`),
        mục Authorization không được để trống.
  - [ ] TASK-204 — authentication và phân quyền. **Đơn giản hóa 2026-08-23
        (DEC-124):** chủ dự án xác nhận trực tiếp — công cụ quản trị nội bộ,
        chỉ một vai trò `ADMIN` trong MVP, không `viewer`/`editor`/
        `employee_scope` (**ADR-105** §4, Accepted). Danh tính không phải
        `ADMIN` nhận `403` ở mọi endpoint trừ
        `auth/login`/`auth/logout`/`auth/me`, và không mở được frontend.
        Ranh giới bảo mật đặt ở backend dù chỉ một vai trò: một `curl`
        không mang token `ADMIN` hợp lệ phải bị chặn, không chỉ ẩn nút trên
        UI. Thiết kế `users.role` dạng enum cho phép thêm vai trò sau này,
        không xây trước hạ tầng nhiều vai trò (ADR-105 §5). C12/C13/C14 đã
        đóng — không còn phụ thuộc nghiệp vụ nào chặn Roadmap Finalization
        của task này khi PHASE-02 mở.
  - [ ] TASK-205 — recalculate tăng dần (incremental)

- [ ] PHASE-03 — Giao diện Web
  - [ ] TASK-301 — upload và xem trước khi import. Route: `/imports`,
        `/imports/new`, `/imports/{batchId}` (ADR-105 §3)
  - [ ] TASK-302 — lưới chi tiết nhân viên theo tháng, sửa inline. Route:
        `/employees/{employeeId}/{period}` (ADR-105 §3)
  - [ ] TASK-303 — Summary tháng và dashboard năm. Mục §16 đặc tả: chuyển đổi
        metric giữa Orders / Sales / Converted Revenue / Accounting Profit /
        KPI Profit / % Target; lọc theo nguồn đơn All / Personal / ADS; so
        sánh nhân viên theo doanh thu quy đổi Personal và Ads riêng biệt;
        trend theo tháng cho từng nguồn đơn; tỉ trọng ADS trên tổng doanh thu
        quy đổi của mỗi người. Route: `/dashboard`, `/summary/{period}`
        (ADR-105 §3)
  - [ ] TASK-304 — màn hình cấu hình. Route: `/settings/employees`,
        `/settings/conversion`, `/settings/adjustments`, `/settings/targets`
        (ADR-105 §3)
  - [ ] TASK-305 — màn hình review queue và audit. Route: `/review`, `/audit`
        (ADR-105 §3)
  - [ ] TASK-306 — xuất Excel. Route: `/exports` (ADR-105 §3)
  - [ ] GATE-03 — Nghiệm thu MVP, mục 28 đặc tả, đủ 14 tiêu chí. Bổ sung:
        mọi route ở ADR-105 §3 phải mở trực tiếp được, refresh được,
        back/forward đúng, và chặn đúng khi truy cập trái quyền
        (`governance/core/02_ROUTING_RULES.md` → "Checklist Routing")

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

## Track Governance — Bảo Trì Nền Tảng (PHASE-GOV)

Track thứ hai, độc lập với roadmap sản phẩm Tín Phát ở trên. Track này audit
và sửa chính khung governance của repo (không phải tính năng Tín Phát). Chạy
song song, KHÔNG chặn PHASE-00..04 của Tín Phát trừ khi ghi rõ dependency.

Lịch sử: chạy trên nhánh `claude/s001-discovery-pka3fu` qua 7 session
(S001–S007, 2026-08-22 → 2026-08-23), merge vào nhánh mặc định qua PR#4/#5
(2026-08-23). Trong lúc merge, nội dung phần này từng bị nhánh Tín Phát ghi
đè hoàn toàn khỏi `PROJECT_PROGRESS.md` — không mất dữ liệu thật (mọi file
vẫn còn dưới `docs/audit/`, `docs/tasks/TASK-REM-*.md`), nhưng mất khả năng
nhìn thấy trong checklist canonical, khiến REM-T05 (đã READY, gate frozen)
trông như không tồn tại. Khôi phục lại ở đây theo DEC-118.

Chi tiết đầy đủ (không lặp lại ở đây — chỉ tóm tắt trạng thái):
`docs/audit/REMEDIATION_ROADMAP.md`, `docs/audit/S001_AUDIT_FINDINGS.md`,
`docs/audit/DECISIONS.md` (DEC-001..016 của riêng track này — đánh số trùng
với DEC-101..117 của Tín Phát chỉ là trùng dải số cũ trước khi tách theo
DEC-117, không phải cùng một quyết định).

### Trạng thái

- [x] **PHASE-01 — Governance Foundation Repair — DONE.** Phase Gate 01 PASS
      (10/10 check, S006). REM-T02, REM-T03, REM-T04, REM-T07 đều DONE.
      **Lưu ý:** REM-T02 (dời governance package lên root) trùng việc với
      TASK-000 của Track Tín Phát — xem ghi chú ở PHASE-00 phía trên. Cả hai
      hội tụ đúng cùng một kết quả, xác nhận bằng `validate_structure.py`
      PASS trên state hiện tại. Không cần làm lại; ghi nhận như bài học về
      chi phí của việc thiếu bước "đồng bộ nhánh" (DEC-118).
- [ ] PHASE-02 — Documentation & Evidence Truth-Up
  - [x] **REM-T05** — Sửa tài liệu và artifact kiểm chứng — MAJOR — Tier B —
        **DONE** (S008, 2026-08-23) — 4/4 check REQUIRED PASS (E1);
        CHECK-T05-05 (RECOMMENDED, E2) NOT_TESTED — không có reviewer độc
        lập khả dụng trong session solo, ghi giới hạn tường minh, không
        chặn DONE. Đóng FIND-005, FIND-006, FIND-011, FIND-012. File:
        `docs/tasks/TASK-REM-T05-documentation-truth-up.md`, handoff:
        `docs/sessions/S008-rem-t05-documentation-truth-up.md`.
  - [ ] Phase Gate 02 — chờ REM-T06
- [ ] PHASE-03 — Repository Hygiene
  - [ ] REM-T06 — Vệ sinh repository root — MICRO — Tier A — **READY, gate
        FROZEN** (S009 sẽ implement). Đóng FIND-009 (một phần đã xử lý —
        `.gitignore` đã có từ S003). File:
        `docs/tasks/TASK-REM-T06-repository-root-hygiene.md`.
  - [ ] Phase Gate 03 — đánh giá lại GAP-01 (Backup/DR)

### Finding còn OPEN

Không tự đóng chỉ vì bị mồ côi khỏi checklist ở lần merge trước:

| ID | Severity | Tóm tắt | Đóng bởi |
|---|---|---|---|
| FIND-009 | LOW | Thiếu root README/LICENSE (một phần đã xử lý) | REM-T06 |

### Finding đã RESOLVED (S008, 2026-08-23)

| ID | Severity | Tóm tắt | Đóng bởi | Bằng chứng |
|---|---|---|---|---|
| FIND-005 | MEDIUM | Báo cáo validation đã ship khẳng định một PASS sai sự thật | REM-T05 | `governance/reference/COMPACT_STRUCTURE_VALIDATION.md` nay trích dẫn lệnh + output thật của cả 5 validator (CHECK-T05-01) |
| FIND-006 | MEDIUM | START_HERE guide tự mâu thuẫn về layout | REM-T05 | 5 vị trí trong `governance/reference/START_HERE_USAGE_GUIDE_V3_2.md` đã sửa về layout compact (CHECK-T05-02) |
| FIND-011 | LOW | Bare reference không resolve trong changelog lịch sử | REM-T05 | Ghi rõ tường minh 2 loại trừ (`governance/reference/history/`, `docs/audit/`) trong báo cáo validation, không sửa file lịch sử |
| FIND-012 | LOW | README validator từng thiếu tài liệu hóa | REM-T05 | Re-verify CHECK-T05-03 PASS — đã DONE tiện thể ở REM-T03/S005, xác nhận chính thức ở đây |

### Việc phụ tồn đọng (không thuộc task nào)

- Owner xóa thủ công nhánh `scratch/ci-failure-test` trên GitHub (DEC-014,
  proxy chặn agent xóa).
- Owner cân nhắc bật branch protection cho check `governance`.

### Nợ Kỹ Thuật / Cảnh Báo Vận Hành

Ghi theo yêu cầu của Independent Review #4 khi duyệt TASK-108A-1.

### TD-001 — F2/F4 là WARNING, phải hiển thị trong Review Queue/UI

`tools/analysis/reconcile_conversion.py` phân loại kết quả thành HARD FAILURE
(F1/F3/F5 — quyết định exit code) và **WARNING / REVIEW SIGNAL** (F2/F4 —
không làm exit non-zero):

- **F2** — nhân viên đang `active` và hiệu lực trong kỳ nhưng không khớp dòng
  nào. Có thể sai `raw_prefix` (lỗi thật), cũng có thể chỉ là không có doanh
  số kỳ đó (bình thường).
- **F4** — tên chưa map có số dòng ≥ nhân viên đã map nhỏ nhất. Dấu hiệu
  master data đang thiếu người đáng kể.

**Yêu cầu bắt buộc:** hai cảnh báo này **phải được hiển thị rõ ràng** trong
Review Queue / UI khi xây (TASK-110 trở đi). **Không được âm thầm bỏ qua.**

**Vì sao:** một F4 bị nuốt nghĩa là một nhân viên thật đang bán hàng mà hệ
thống không biết — và theo DEC-127 §8, mọi dòng của người đó trả `Unresolved`,
tức **không nhận tỉ lệ nào**, tức không vào KPI của ai. Im lặng ở đây là mất
doanh số của một người thật khỏi bảng lương.

Owner: TASK-110. **ĐÃ XỬ LÝ (S016). Sáu vòng review siết dần provenance:
#1 yêu cầu mỗi mục phải truy vết được (S017); #2 yêu cầu F4 bỏ qua
`employee_raw` rỗng và F6 chấm theo effective dating từng dòng (S018); #3 yêu
cầu F3 chỉ đánh dấu dòng thật sự ambiguous, F4 giữ mọi biến thể raw, và F6
không phát khi thiếu ngày — HD-110-04/DEC-130 (S019); #4 yêu cầu **mọi**
provenance dựng từ chính tập row của finding, và F3 cũng cần ngày —
HD-110-05/DEC-131 (S020); #5 là một **Architecture Repair** — xóa nguồn sự
thật thứ hai cho việc chọn employee record, xóa kênh provenance song song
(`details`), và fail-fast cho master data hỏng — HD-110-06/07/08 → **DEC-132**
(S021). **Chưa vòng nào PASS**; chờ Review #6 xác nhận.** F2/F4 nay do `app/modules/validation/validator.py` sinh ra trên chính
luồng `run_import()`, không còn chỉ nằm trong script phân tích chạy tay. Bằng
chứng: **CHECK-110-12** (F2 có mặt trong `ImportResult.review_queue`),
**CHECK-110-13** (F4, và F2/F4 không làm `run_import()` raise),
**CHECK-110-14** (`reconcile_conversion.py` giữ nguyên hành vi, 24/24 test
không sửa). Cả ba PASS. Tiêu chí F1–F5 đã dời sang
`app/modules/validation/employee_mapping.py`; script phân tích import ngược
lại đúng các tên đó, nên hai đường dùng chung một bộ tiêu chí thay vì hai bản
cài đặt. Xem `docs/tasks/TASK-110-validation-review-queue.md`.

**Chưa đóng hoàn toàn:** màn hình duyệt thật vẫn là TASK-305 — hiện F2/F4 nằm
trong `ImportResult`, chưa có UI hiển thị. Đóng hẳn TD-001 khi TASK-305 xong.

## Session tiếp theo cho track này

S009 — REM-T06 (vệ sinh repository root, MICRO, Tier A, **gate FROZEN**) →
sau đó Phase Gate 02 → Phase Gate 03. Không chặn Track Tín Phát — có thể xen
kẽ vào bất kỳ lúc nào một session rảnh, hoặc sau khi GATE-00 duyệt, tùy chủ
dự án quyết định thứ tự ưu tiên.

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
| TASK-110 | 3 | 3 | 2 | MAJOR | B | C |
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
  khớp. **✅ VERIFIED 2026-08-23 (TASK-101, CHECK-101-08)** — khớp tuyệt đối
  cả hai kỳ, xem `docs/tasks/TASK-101-importer-normalizer.md`.
- TASK-104: `LeadSource` chỉ nhận đúng hai giá trị `PERSONAL` và `ADS`. Không
  literal `TINPHAT_ADS` nào còn tồn tại trong mã nguồn hay tài liệu (E1, kiểm
  chứng bằng grep) — DEC-119.
- TASK-104: phân loại quyết định ở cấp OrderID và áp cho mọi dòng của đơn; hai
  dòng cùng `OrderID` không bao giờ mang hai `LeadSource` khác nhau (E1).
- TASK-108: `ConversionScheme` tra từ config theo `(employee, lead_source,
  ngày của đơn)`. Không đường code nào suy tỉ lệ trực tiếp từ `LeadSource`
  (E1). Case E/F của DEC-119 là phép kiểm: cùng `PERSONAL` như Kiên nhưng Nội
  thành phải ra 2 %, không phải 5,5 %.
- TASK-108: tra tỉ lệ dùng **ngày của đơn**, không dùng thời điểm chạy. Thêm
  một dòng chính sách có `effective_from` trong tương lai rồi chạy lại một kỳ
  lịch sử phải cho kết quả **không đổi** (E1) — DEC-121.
- TASK-108: nạp lợi nhuận KPI theo nhân viên-tháng **và** 14 giá trị `X` của
  workbook vào `conversion_engine` phải tái hiện đúng cột `F` của
  `Summary 2026` ở cả 14 kỳ (E1). Đây là phép kiểm engine cài đúng phép toán,
  thay cho mốc 13.883.242 đã gỡ theo DEC-120.
- TASK-108: một tổ hợp `(employee, lead_source, ngày)` không khớp dòng config
  nào phải trả về `Unresolved` và vào Review Queue — không bao giờ mượn tỉ lệ
  của nhân viên khác, không bao giờ mặc định về một tỉ lệ nào (E1).
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
- TASK-203: không tồn tại endpoint nào ghi vào `raw_rows` — không UPDATE,
  không DELETE, không PATCH. Kiểm chứng bằng `grep` trên toàn bộ định nghĩa
  router (E1). Đây là hệ quả trực tiếp của ADR-102, xem ADR-105 §2.
- TASK-203: mọi endpoint có mục Authorization được điền trong `API Contract
  Template`, không endpoint nào để trống (E1).
- TASK-204: với **mọi endpoint** ở ADR-105 §2 (trừ ba endpoint auth), một
  test gọi thẳng API bằng danh tính không phải `ADMIN` (chưa đăng nhập, hoặc
  đăng nhập với role khác) và khẳng định `403` — không phải khẳng định nút
  bị ẩn trên UI (E1, hướng tới E2 vì đây là bề mặt bảo mật).
- TASK-204: với danh tính `ADMIN`, test khẳng định từng endpoint trả đúng dữ
  liệu, không bị chặn nhầm — kiểm chứng bằng cách gọi API thật (E1).
- TASK-301…306 / GATE-03: mọi route ở ADR-105 §3 mở trực tiếp được, refresh
  được, back/forward đúng, có trạng thái not-found; không có màn hình chính
  nào chỉ tới được bằng tab state (E1, theo "Checklist Routing" của
  `governance/core/02_ROUTING_RULES.md`). Riêng frontend: danh tính không
  phải `ADMIN` phải nhận màn hình "không có quyền truy cập" ở mọi route
  nghiệp vụ, kể cả khi gõ thẳng URL (E1).
- Mọi phase: không tên nhân viên, tỉ lệ quy đổi, target, số tiền adjustment
  hay từ khóa ADS nào xuất hiện dưới dạng literal trong mã nguồn ứng dụng
  (E1, kiểm chứng được bằng grep).

**Lưu ý cho session sau — các check PHASE-02/03 ở trên là PRELIMINARY.**
`ADR-105` §4/§5 (phân quyền) đã chuyển **Accepted** (DEC-124, C12/C13/C14 đã
đóng); §2/§3 (route) vẫn Accepted như từ đầu. **Nhưng Completion Gate của
TASK-203/204 vẫn chưa freeze** — chấp nhận ADR khác với freeze gate. Quy
trình đúng khi PHASE-02 mở: chạy Roadmap Finalization đầy đủ cho TASK-203/204
(`governance/core/00_SESSION_ORCHESTRATION.md` → "Hoàn thiện Roadmap") rồi
mới freeze — bước này giờ nhanh hơn nhiều vì không còn câu hỏi nghiệp vụ nào
mở. Xem DEC-123, DEC-124.

## Trạng thái Task hiện tại

Task:
TASK-110 — Validation + Review Queue

Task Mode:
MAJOR

Status:
**IMPLEMENTED — repairing after Independent Review #4.**
**NOT MERGED. NOT DONE.** CHECK-110-16 = **BLOCKED**.

Completion Gate đã **FROZEN** (chủ dự án, 2026-08-23) — Gate không còn ở trạng
thái chờ duyệt, và code đã viết xong. Lịch sử hai vòng review:

- **Independent Review #1 — FAIL, 6 finding** → đã sửa toàn bộ (S017), ba
  Human Decision ghi thành **DEC-129**.
- **Independent Review #2 — FAIL, 4 finding** → đã sửa toàn bộ (S018).
- **Independent Review #3 — FAIL, 3 finding** → đã sửa toàn bộ (S019); một
  Human Decision (**HD-110-04**) ghi thành **DEC-130**.
- **Independent Review #4 — FAIL, 2 provenance defect** → đã sửa toàn bộ
  (S020); một Human Decision (**HD-110-05**) ghi thành **DEC-131**.
- **Independent Review #5 — FAIL, 4 finding** → đã sửa toàn bộ bằng
  **Architecture Repair** (S021); ba Human Decision (**HD-110-06/07/08**) ghi
  thành **DEC-132**. Hai finding provenance đã tái xuất ở representation khác
  nhau qua các vòng trước, nên vòng này sửa **cơ chế sinh ra chúng** thay vì
  sửa representation: trạng thái sai không còn **biểu diễn được**.

**Chưa vòng review nào PASS.** Chờ **Independent Review #6**.

21/22 REQUIRED check PASS. **CHECK-110-16 (đối chiếu dữ liệu thật) vẫn
BLOCKED** — file thô production không có trong repo (đúng
`governance/product/17_DATA_GOVERNANCE_PRIVACY.md`) và không có trong
container. Check này **chặn DONE, không chặn IMPLEMENTED**.

Phạm vi: **7 loại cảnh báo** (không phải 5), V7 mở thành **F1–F6** theo
DEC-129. Chấm điểm: Difficulty 3, **Risk 3** (kéo theo E1 bắt buộc cho mọi
check REQUIRED). Bốn khoảng trống nghiệp vụ của §18 đã đóng bằng **DEC-128**.

File: `docs/tasks/TASK-110-validation-review-queue.md`.
Handoff: `docs/sessions/S021-*.md` (Architecture Repair, mới nhất),
`S015-*.md` (Gate), `S016-*.md` (triển khai),
`S017-*.md` (sửa Review #1), `S018-*.md` (sửa Review #2),
`S019-*.md` (sửa Review #3), `S020-*.md` (sửa Review #4).

### TASK-108A-1 (task liền trước)

Task Mode:
MAJOR

Status:
**DONE** — 16/16 REQUIRED check PASS, 151/151 test, Independent Review #4
PASS, đã merge tại `c7a1b24`.

Required Gate Progress:
GATE-00 PASS (DEC-122). TASK-101, TASK-105, TASK-106, TASK-107, TASK-108A-1
đều **DONE**. Bộ test hiện tại: **342/342 PASS** (`pytest tests/ -q`) —
xem "Trạng thái Task hiện tại" cho TASK-110. Chi tiết từng task:
`docs/tasks/TASK-101-importer-normalizer.md`,
`docs/tasks/TASK-105-price-engine.md`,
`docs/tasks/TASK-106-adjustment-engine.md`,
`docs/tasks/TASK-107-profit-engine.md`.

Primary Agent Tier:
C

Escalation Tier:
—

### TASK-108A-1 — DONE (2026-08-23), Independent Review #4 PASS

Ba vòng pre-implementation review trước khi có dòng code nào. Kết quả chốt
thành **DEC-127** (8 quyết định nghiệp vụ) và **ADR-106** (ProductGroup +
hạ granularity xuống cấp line).

Thay đổi mô hình: `Nội thành` không còn là Employee — Vinh, Quý, Hiệp là ba
Employee thật, cùng `employee_group = NOI_THANH`. Thêm dimension
`ProductGroup` (`DIEN_MAY`/`GIA_DUNG`) ở **cấp product line**, vì đo được
118/10.609 OrderID chứa đồng thời cả hai loại. `ConversionScheme` do đó hạ
từ cấp Order xuống cấp line; `LeadSource` giữ nguyên cấp Order (DEC-119).

Resolver tra 4 chiều `(employee, employee_group, lead_source, product_group,
ngày của đơn)`: `lead_source` là lọc cứng, dòng cụ thể nhất thắng theo
specificity `4×employee + 2×group + 1×product_group`, **hòa điểm là lỗi cấu
hình** (engine từ chối chọn), không khớp là `Unresolved` (không fallback).

Bằng chứng trên dữ liệu thật: reconciliation 55 ô cột F của `Summary 2026`
— **52 khớp chính xác, 3 legacy, 0 lệch**; employee mapping đúng trên
**14.389 dòng** file thô toàn công ty với 107 dòng `unmapped` đúng C11.
16/16 REQUIRED check PASS, 119/119 test (36 mới), không regression.

**Bốn vòng independent review.** Bản đầu (`98142af`) có 119/119 test nội bộ
PASS và reconciliation tự báo "52 khớp, 0 lệch", nhưng reviewer độc lập vẫn
tìm ra bốn lớp lỗi qua ba vòng: nhân viên chưa map vẫn nhận tỉ lệ 5,5 %
(CRITICAL, ảnh hưởng trực tiếp tiền lương); manual override bỏ qua
effective date; reconciliation hard-code dimension tạo "khớp giả" ở 16/52 ô;
verification có oracle song song; sau đó là thiếu failure criterion cho raw
mapping, bỏ qua effective window, và dùng heuristic làm hard failure. Tất cả
đã sửa; **Review #4 PASS**. Chi tiết từng vòng:
`docs/tasks/TASK-108A-1-conversion-scheme-resolver.md` mục "Lịch Sử
Independent Review".

**Kết quả đối chiếu cuối:** 36 ô khớp độc lập / 0 lệch / 19 ô ghi nhận
LIMITED (nhãn báo cáo gộp + legacy, không có artifact production để nối) —
**không đưa về 52 bằng bất kỳ assumption nào**.

Chi tiết: `docs/tasks/TASK-108A-1-conversion-scheme-resolver.md`.

### TASK-107 — DONE (2026-08-23)

`profit_engine.compute_accounting_profit()` + `apply_accounting_profit()` —
`AccountingProfit = (SellPrice − AccountingPurchasePrice) × Quantity`,
Universal formula, `None` khi bất kỳ input nào thiếu (không bao giờ 0).
Trước khi code, chủ dự án chốt **DEC-126**: 6 nguyên tắc ranh giới, quan
trọng nhất là AccountingProfit độc lập hoàn toàn với KPI Adjustment, và
`EligibleKpiProfit` **không** thuộc scope task này (cần Adjustment record đã
xác nhận, persistence đó chưa tồn tại). Nối vào `run_import()` làm bước 9,
tự động — không cần lựa chọn thủ công như TASK-106, vì đây là hàm thuần túy
của các field đã sẵn có. 6/6 REQUIRED check PASS, 83/83 test tổng (9 mới,
không regression). Chi tiết: `docs/tasks/TASK-107-profit-engine.md`.

### TASK-106 — DONE (2026-08-23)

`AirConditionerClassifier` (dò từ khóa điều hòa trên `ProductRaw`, NFC-
normalize, không phân biệt hoa/thường) + `AdjustmentResolver`
(`resolve_suggested_amount()` — Qua kho/NCC giao tra `delivery_method_tiers`
theo phương tiện giao; KHBH/Thợ lắp chỉ có mặc định khi `is_air_conditioner=True`).
DEC-125 làm rõ: không có nguồn raw cho từ vựng adjustment — module này
**không** nối vào `run_import()`, khác hẳn `PendingPriceProvider` (TASK-105).
Trả giá trị **đề xuất**, không tự áp; `None` khi không có căn cứ (không bao
giờ suy đoán, không coi 0 — DEC-103). 5/5 REQUIRED check PASS, 74/74 test
tổng (17 mới, không regression trên 57 test TASK-101+105). Chi tiết:
`docs/tasks/TASK-106-adjustment-engine.md`.

### TASK-105 — DONE (2026-08-23)

`PriceProvider` (Protocol) + `PendingPriceProvider` + `price_engine.apply_prices()`,
nối vào `run_import()` làm bước 8. Vì chưa có Price Master nào tồn tại ở
Phase 1, mọi dòng đều `Pending` — đúng hành vi kỳ vọng, không phải giới hạn
tạm thời. Không bao giờ coi giá thiếu là 0 (DEC-103), kiểm chứng cả khi
provider có dữ liệu cho sản phẩm khác trong cùng lần chạy. Provider tùy
chỉnh cắm được qua dependency injection (`run_import(price_provider=...)`)
mà không sửa `price_engine`/`provider.py` — chuẩn bị sẵn cho TASK-401
(Phase 4) tích hợp Price Master thật. 9/9 REQUIRED check PASS, 57/57 test
tổng (8 mới, không regression). Chi tiết:
`docs/tasks/TASK-105-price-engine.md`.

### TASK-101 — DONE (2026-08-23)

Implement xong ngày 2026-08-23 với 12/13 REQUIRED check PASS trên fixture
tổng hợp ẩn danh; CHECK-101-08 (đối chiếu 254 đơn 01.2026 / 146 đơn 06.2026)
BLOCKED vì thiếu `data/samples/` thật trong môi trường phiên đó.

**Cùng ngày, phiên kế tiếp:** chủ dự án cung cấp trực tiếp 2 file thật của
Tín Phát (xuất riêng theo tháng, 01.2026 và 06.2026). Chạy
`tools/analysis/reconcile_real_data.py` gọi thẳng `app.pipeline.run_import()`
— kết quả:

- 01.2026: 254 đơn — khớp tuyệt đối với kỳ vọng.
- 06.2026: 146 đơn — khớp tuyệt đối với kỳ vọng.
- Đối chiếu chéo độc lập với dòng "Tổng cộng" tự có trong chính file thô
  (không do engine tính): khớp tuyệt đối cả doanh số lẫn chiết khấu ở cả hai
  tháng — xác nhận không sót, không đếm trùng dòng nào.
- 100% đơn Tín Phát phân loại ADS qua mặc định nhân viên (DEC-109), 0 đơn qua
  từ khóa "ADS" — khớp phát hiện gốc (chuỗi "ADS" không xuất hiện trong dữ
  liệu công ty).
- So sánh `Doanh số bán` (raw) với `SellPrice × Quantity − Discount`: mọi
  chênh lệch quan sát được (22/351 dòng ở 01.2026, 1/180 dòng ở 06.2026) đều
  giải thích được bằng đúng một pattern đã biết trước — DEC-114 (raw là số
  gross, chưa trừ chiết khấu). Không có pattern lệch nào khác, không cần và
  không sửa business rule.

**CHECK-101-08 chuyển PASS. TASK-101 chuyển DONE.** Không sai lệch nghiệp vụ
đáng kể. Chi tiết đầy đủ (kèm bảng số liệu hai kỳ):
`docs/tasks/TASK-101-importer-normalizer.md` → mục "Đối Chiếu Dữ Liệu Thật".
File thật đã xóa khỏi môi trường làm việc sau khi dùng, đúng DEC-108 — chưa
từng commit vào git.

Sửa thêm theo góp ý review: CHECK-101-05 từng ghi heading "8 case A–G" gây
hiểu nhầm task đã kiểm chúng — đã sửa lại chỉ claim phạm vi `LeadSource`
thật sự thuộc TASK-101; 8 case A–G (ConversionScheme) vẫn thuộc TASK-108,
không mở rộng phạm vi TASK-101 sang đó.

### GATE-00 — PASS (2026-08-23)

**Đã duyệt.** Chủ dự án đọc `docs/analysis/` cùng đợt rà soát nghiệp vụ
DEC-119/120/121, sau đó xác nhận trực tiếp trong hội thoại — nguyên văn và
đầy đủ hệ quả ghi ở **DEC-122**. Lượt duyệt: 1/1.

Ba điểm chủ dự án đã xác nhận biết trước khi duyệt (không phải giả định ngầm):

1. **Lịch sử 2026 không khớp workbook cũ** — Hoàng và Kiên cao hơn 6,0 %
   (+837.503 nghìn, ~3,0 triệu tiền thưởng) do bỏ di trú (DEC-120). Chủ dự án:
   *"chấp nhận"*.
2. **C9** — đơn của Nội thành/Gia dụng có chữ "ADS" quy đổi ở 7,5 % (không có
   dòng scheme riêng). Chủ dự án: *"luôn không xuất hiện ADS, không cần quan
   tâm"* — đóng, không đổi cấu hình.
3. **C10** — chính sách 2027 chưa có gì khác 2026 để cấu hình. Chủ dự án:
   *"không đổi"* — đóng cho hiện tại, mở lại nếu có tin mới.

PHASE-01 mở khóa ngay khi duyệt. Không cần vòng duyệt bổ sung nào cho GATE-00.

### Đã trả lời

| # | Câu hỏi | Trả lời |
|---|---|---|
| C1 | Tín Phát có nên mặc định ADS không? | **Có** — mọi đơn của Tín Phát quy đổi 7,5% bất kể ghi chú. DEC-109, sửa đổi bởi DEC-119. Số liệu lịch sử của Tín Phát không cần di trú gì cả. |
| C5 | Loại dòng nào tính vào số SP, doanh số, lợi nhuận, số đơn? | Dòng phụ có giá trị tiền **có** tính vào doanh số và lợi nhuận, không tính vào số SP, và mỗi dòng đều vào hàng đợi duyệt tay để giữ lại hoặc loại trừ. DEC-110. |
| C6 | Nhân viên có sửa được `Diễn giải` không? | **Có.** Mặc định ERP giữ nguyên; nhân viên chỉ sửa khi là đơn ADS. DEC-111. |
| C7 | Lợi nhuận ADS lịch sử của Hoàng và Kiên xử lý thế nào? | **Không di trú** — lịch sử mặc định PERSONAL. DEC-120 (thay thế DEC-112). |
| C8 | Số SP có loại trừ dòng phụ có giá trị tiền không? | **Có**, và bản thân chỉ số này giá trị thấp — vẫn giữ làm cột nhưng bỏ khỏi tiêu chí gate. DEC-113. |
| C4 | `Chiết khấu` trừ vào đâu? | **Trừ vào doanh số.** DEC-114. Đã xác minh số của ERP là gross, nên đây là một phép sửa thật, không phải trừ hai lần. |
| C4b | Chiết khấu có trừ vào lợi nhuận không? | **Có.** DEC-122, xác nhận trực tiếp 2026-08-23. |
| C2 | Vì sao sheet kênh chia đôi? | **Có dòng tổng phụ theo ngày nằm trong vùng dữ liệu**, nên một phép SUM đơn thuần bị đếm hai lần. Đã giải thích, không tái tạo — dòng tổng phụ chuyển ra ngoài vùng SUM, đánh dấu bằng nhãn `RowType`. DEC-115. |
| C3 | Rule hoa hồng? | **Dựa trên mức đạt target**; công thức hóa ở TASK-403 như kế hoạch. Phase 1 nạp bảng tỉ lệ quan sát được làm dữ liệu. DEC-116. |
| C9 | Tỉ lệ ADS cho Nội thành/Gia dụng? | **Không quan tâm** — tổ hợp này không xảy ra trong thực tế, giữ mặc định 7,5%. DEC-122. |
| C10 | Chính sách 2027 khác 2026 ở đâu? | **Không đổi**, tính đến 2026-08-23. DEC-122. |

### Còn mở

Danh sách đầy đủ: `docs/analysis/10_OPEN_QUESTIONS.md`.

| # | Câu hỏi | Mặc định đang áp dụng | Cần trước |
|---|---|---|---|
| C11 | 88 dòng nhân viên chưa map xử lý thế nào khi lên production? | Review Queue loại `Missing`, không tính vào KPI của ai. Chủ dự án: *"tôi chưa rõ"* (2026-08-23). | GATE-01 |

Không chặn GATE-00 (đã PASS) hay Phase 1 — mặc định Review Queue đã an toàn:
không âm thầm bỏ, không âm thầm gán nhân viên.

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

- **RISK-02 — ĐÃ XỬ LÝ 2026-08-22.** Tín Phát mặc định `ADS` (DEC-109, sửa đổi
  bởi DEC-119), nên tỉ lệ 7,5% được giữ nguyên, không con số nào thay đổi. Còn
  lại: đánh dấu một đơn là ADS *làm giảm* doanh thu quy đổi (5,5% chia ra số
  lớn hơn 7,5%), nên đánh dấu ADS quá tay sẽ khiến nhân viên mất tiền. Review
  queue phải hiện cả đơn mới chuyển sang ADS, không chỉ đơn mới chuyển về
  PERSONAL.

- **RISK-05 — Chênh lệch 6,0% của Hoàng và Kiên trên dữ liệu lịch sử.** Hệ quả
  trực tiếp của DEC-120 (không di trú): doanh thu quy đổi 01–08.2026 của hai
  người sẽ là 14.720.745 thay vì 13.883.242 nghìn đồng đang báo cáo — cao hơn
  837.503 nghìn, kéo theo khoảng 3,0 triệu đồng tiền thưởng. Chiều lệch *có
  lợi* cho nhân viên.
  Giảm thiểu: chênh lệch đã được định lượng chính xác và ghi tại
  `docs/analysis/06_ADS_RULE_VERIFICATION.md` §6.1 và §8, nên giải thích được
  bất cứ lúc nào. DEC-112 vẫn còn nguyên vẹn để kích hoạt lại nếu GATE-01 kết
  luận chênh lệch này không chấp nhận được.

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

- **REG-01 (mới, 2026-08-23) — `validate_reference_integrity.py` đang FAIL
  trên nhánh mặc định.** Ba reference không phân giải được, tất cả trong
  `docs/tasks/TASK-REM-T06-repository-root-hygiene.md`: README, CONTRIBUTING
  và CODE_OF_CONDUCT ở gốc repo (cố ý viết không có backtick ở đây — xem đoạn
  cuối mục này).

  Đây là **forward-reference tới chính các file mà REM-T06 sẽ tạo** — task
  file mô tả sản phẩm bàn giao của nó bằng backtick, và validator coi mọi
  chuỗi backtick kết thúc bằng `.md` là một reference cần phân giải.

  Xuất hiện từ commit `2d5cf9b` ("Hoàn thiện Ready Gate REM-T06"), **không
  phải** do session soạn ADR-105 gây ra — đã kiểm chứng bằng cách stash toàn
  bộ thay đổi của session này rồi chạy lại validator: vẫn đúng 3 lỗi đó.
  Nghĩa là CI trên nhánh mặc định đang đỏ kể từ `2d5cf9b`.

  **Chưa sửa, có chủ đích.** Sửa nội dung task file của REM-T06 khi gate của
  nó đã FROZEN là đụng vào Scope Lock của một task khác — đúng thứ DEC-012 đã
  rút kinh nghiệm ("khi phát hiện một sửa đổi thuộc task khác trong lúc làm
  việc, ghi nhận nó thay vì tự sửa"). Tiền lệ ngược lại cũng có: S005 từng sửa
  ngay reference do chính task đó tạo ra (commit `1da459d`) — nhưng khi ấy là
  task đang implement, không phải task đã frozen chờ session khác.

  **Đóng ở S009 (REM-T06)** — session đó vừa tạo ba file thật, vừa làm ba
  reference này phân giải được, nên lỗi tự biến mất mà không cần sửa văn bản.
  Nếu S009 bị hoãn lâu, cân nhắc một MICRO riêng để bỏ backtick khỏi ba tên
  file đó trong task file.

  **Bẫy cần biết cho mọi session:** viết tên một file *chưa tồn tại* trong
  backtick sẽ làm validator FAIL — kể cả khi đang mô tả nó như một sản phẩm
  sắp tạo, và kể cả trong chính ghi chú về lỗi đó. Session này vấp đúng bẫy
  ấy khi soạn mục REG-01 và phải viết lại không dùng backtick. Khi cần nhắc
  tên một file sắp tạo, viết trần (README.md) thay vì trong backtick.

## Quyết định gần đây
- Xem `PROJECT/PROJECT_DECISIONS.md` — DEC-101 đến DEC-124 (track Tín Phát).
  Các quyết định mới nhất:
  - **DEC-119** — tách `LeadSource` khỏi `ConversionScheme`; `TINPHAT_ADS` bị
    loại bỏ. Xem ADR-104.
  - **DEC-120** — không di trú dữ liệu ADS lịch sử; thay thế DEC-112. Gỡ mốc
    13.883.242 khỏi REQUIRED check của TASK-108.
  - **DEC-121** — 2026 là giai đoạn chuyển đổi; mốc chuẩn chính thức
    01/01/2027; mọi business rule mang `effective_from`/`effective_to` và tra
    theo ngày của đơn.
  - **DEC-122** — GATE-00 PASS; PHASE-01 mở khóa.
  - **DEC-123** — Roadmap Finalization **sơ bộ** cho TASK-203/204; ADR-105
    (route map + mô hình phân quyền) dựng lần đầu, ba mặc định tạm cho
    C12/C13/C14.
  - **DEC-124** — chủ dự án quyết định trực tiếp: MVP chỉ một vai trò
    `ADMIN`, không `viewer`/`editor`/`employee_scope`. Đóng C12/C13/C14.
    ADR-105 §4/§5 viết lại, chuyển `Accepted`. Completion Gate TASK-203/204
    vẫn chưa freeze.
- Xem `docs/audit/DECISIONS.md` — DEC-001 đến DEC-016 (track Governance,
  dải số riêng, xem DEC-117 về lý do tách).

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
- 2026-08-23 — **Hợp nhất hai track (DEC-118).** Một session được yêu cầu rà
  soát tiến độ phát hiện nhánh local đang lỗi thời 14 commit so với nhánh mặc
  định thật trên origin, dẫn tới một câu trả lời sai trước đó ("3 file đặc tả
  Report chưa được intake"). Sau khi fast-forward về đúng state, phát hiện
  track Governance (S001–S007) đã bị merge PR#4/#5 ghi đè khỏi
  `PROJECT_PROGRESS.md` — REM-T05 (READY, gate frozen) và REM-T06 không còn
  xuất hiện trong checklist canonical nào. Khôi phục lại dưới mục "Track
  Governance — Bảo Trì Nền Tảng (PHASE-GOV)" phía trên. Xác nhận TASK-000 và
  REM-T02 đã làm trùng một việc (dời governance lên root) trên hai nhánh
  khác nhau — cả hai hội tụ đúng kết quả, không cần làm lại. Thêm cơ chế bắt
  buộc đồng bộ nhánh cho mọi session tương lai: SessionStart hook
  (`.claude/hooks/session-start.sh` + `.claude/settings.json`, nới
  `.gitignore` để commit được hai file này), bước 0 mới trong
  `governance/core/00_SESSION_ORCHESTRATION.md` → "Giao thức Mở Phiên", và
  mục "Đồng Bộ Nhánh" mới trong `CLAUDE.md`. Đã chạy lại cả 5 validator sau
  toàn bộ thay đổi — PASS. Push thẳng lên nhánh mặc định theo yêu cầu trực
  tiếp của chủ dự án.
- 2026-08-23 — **S008 — REM-T05 DONE (Track Governance).** Đồng bộ nhánh
  trước tiên (bước 0), xác nhận HEAD khớp origin default branch. Chạy lại
  toàn bộ 5 validator tại thời điểm thực thi (không copy baseline S007) và
  dán output thật vào `governance/reference/COMPACT_STRUCTURE_VALIDATION.md`,
  kèm nêu rõ 2 loại trừ của `validate_reference_integrity.py`. Sửa 5 vị trí
  layout pre-compact trong `governance/reference/START_HERE_USAGE_GUIDE_V3_2.md` (4 dòng đã biết
  trước — 83, 85, 144, 146 — cộng 1 dòng phát hiện thêm khi thực thi, dòng
  179 PHẦN 3, cùng loại lỗi, đã sửa và ghi nhận minh bạch thay vì âm thầm mở
  rộng); rút gọn khối liệt kê tay 21 required path ở PHẦN 2 thành hướng dẫn
  chạy validator để tránh tái diễn chính vấn đề FIND-005/006 mô tả (hai
  nguồn sự thật dễ lệch nhau). Re-verify README validator vẫn liệt kê đủ mọi
  script (kể cả `regression_nested_layout.py` mới từ S007) — không cần sửa.
  Xác nhận `governance/reference/history/` không bị đụng bằng `git diff`.
  4/4 REQUIRED check PASS (E1); CHECK-T05-05 (RECOMMENDED, E2) NOT_TESTED —
  không có reviewer độc lập trong session solo, ghi giới hạn rõ ràng, không
  chặn DONE theo đúng điều kiện task đã ghi. Đóng FIND-005, FIND-006,
  FIND-011, FIND-012.

- 2026-08-23 — **Rà soát xác nhận nghiệp vụ trước khi chuyển Phase.** Chủ dự
  án gửi 10 xác nhận nghiệp vụ kèm chỉ thị không tự chuyển Phase. Rà soát lại
  toàn bộ tài liệu phân tích, ADR, data mapping, formula mapping và acceptance
  criteria theo các xác nhận đó. Phát hiện và xử lý ba mâu thuẫn thật: (1)
  `TINPHAT_ADS` là một giá trị enum nguồn đơn có chứa tên nhân viên, khiến
  `PERSONAL` bị hiểu là đồng nghĩa 5,5% và khiến Nội thành/Gia dụng chỉ tồn
  tại được dưới dạng ngoại lệ ngoài mô hình → tách thành `LeadSource` và
  `ConversionScheme` (DEC-119, ADR-104 mới); (2) xác nhận số 6 phủ định
  DEC-112 và làm mất hiệu lực một REQUIRED check đã ghi trong completion gate
  (mốc 13.883.242) → DEC-120 thay thế DEC-112, thay bằng một check tái lập
  được, ghi rõ chênh lệch +6,0% mà quyết định này tạo ra (RISK-05 mới); (3)
  yêu cầu mốc 2027 chưa có chỗ nào trong thiết kế → DEC-121, kèm ràng buộc tra
  cứu theo ngày của đơn. Bổ sung 8 test case A–G do chủ dự án chỉ định, 2
  check hai bucket end-to-end và 3 check tra theo thời điểm vào
  `tools/analysis/verify_ads_rule.py` — **31/31 PASS**. Sửa một tham chiếu
  DEC-009 lỗi thời còn sót trong script sau đợt renumber DEC-117. Ghi 4 câu
  hỏi nghiệp vụ còn mở vào `docs/analysis/10_OPEN_QUESTIONS.md` (C4b, và C9,
  C10, C11 mới). GATE-00 giữ nguyên trạng thái VERIFYING — đợt xác nhận này là
  đầu vào cho việc duyệt, không phải bản thân lượt duyệt.
- 2026-08-23 — **GATE-00 PASS (DEC-122).** Chủ dự án duyệt trực tiếp trong
  hội thoại: (a) chấp nhận chênh lệch +6,0% của Hoàng/Kiên; (b) C4b — chiết
  khấu trừ cả lợi nhuận; (c) C9 — tổ hợp Nội thành/Gia dụng + ADS không xảy
  ra trong thực tế, không cần đổi cấu hình; (d) C10 — chính sách 2027 chưa có
  gì khác 2026; (e) C11 — chưa rõ, giữ mở, không chặn. Cập nhật
  `docs/analysis/10_OPEN_QUESTIONS.md` đóng C4b/C9/C10, giữ C11 mở. Chuyển
  Current Task từ GATE-00 sang TASK-101, đánh dấu PHASE-00 DONE trong roadmap.
  Đồng bộ `PROJECT/LO_TRINH_DE_HIEU.md` theo "Giao thức Đóng Phiên". Merge
  `origin/claude/extract-upload-repo-gq2ws4` (REM-T05 DONE, Track Governance,
  không chồng lấn nội dung với thay đổi Track A) trước khi push. Chạy lại cả
  5 validator governance — PASS.
- 2026-08-23 — **Roadmap Finalization sơ bộ cho TASK-203/204 (DEC-123).** Chủ
  dự án hỏi roadmap đã tính tới bảo mật qua backend và phân chia router chưa.
  Rà soát cho kết quả: nguyên tắc có đủ (`ADR-101` phân lớp, `04_SECURITY_RULES`
  và `02_ROUTING_RULES` đều Mandatory và cấm thẳng những thứ được hỏi), nhưng
  TASK-203/204 mỗi cái chỉ là một dòng một câu, ba vai trò được đặt tên mà
  chưa định nghĩa, và không có danh sách route nào trong repo. Soạn `ADR-105`
  (24 endpoint backend, 14 route frontend gán cho TASK-301…306, ma trận 3 vai
  trò × 13 năng lực, ba phát biểu ràng buộc ranh giới backend/frontend). Mở
  rộng TASK-203/204, gán route cho TASK-301…306 và GATE-03, thêm 6 check
  PRELIMINARY. **Cố ý không freeze** — ADR-105 ở trạng thái `Proposed`, vì
  PHASE-02 còn xa và vì ma trận phân quyền chứa ba câu hỏi nghiệp vụ chủ dự án
  chưa được hỏi (C12/C13/C14 mới trong `docs/analysis/10_OPEN_QUESTIONS.md`).
  Không đổi thứ tự task, không đổi Current Task — TASK-101 vẫn là việc tiếp
  theo. Chạy lại cả 5 validator governance — PASS.
- 2026-08-23 — **TASK-101 implement (Python thuần, ADR-101).** Tạo
  `docs/tasks/TASK-101-importer-normalizer.md`, freeze Completion Gate trước
  khi code. Xây 7 module: `domain` (dataclass `RawRow`/`WorkingLine`/`Order`,
  `Decimal` VND nguyên theo ADR-103), `config/loader` (YAML + effective-dating
  theo DEC-121), `importing` (raw_reader đọc đúng layout header dòng 4/data
  dòng 6, preview metadata, normalizer trừ `Chiết khấu` theo DEC-114),
  `mapping/employee_mapper` (DEC-104, config-driven, dòng chưa map được flag
  không bị bỏ), `orders/order_builder` (nhóm theo OrderID),
  `lead_source/classifier` (DEC-119/ADR-104, chuỗi 4 bậc, tách khỏi
  ConversionScheme). Đây cũng là năng lực lõi mà TASK-102/103/104 định xây
  riêng — không tạo 3 task trùng lặp, đánh dấu chúng hoàn thành phần lõi
  trong roadmap.

  Vì `data/samples/` không tồn tại trong môi trường này (DEC-108 — dữ liệu cá
  nhân khách hàng không commit), dựng fixture tổng hợp đã ẩn danh
  (`tests/fixtures/synthetic_workbook.py`, 8 dòng/7 đơn synthetic, không liên
  quan dữ liệu thật) làm cơ sở test. 49/49 test PASS
  (`pytest tests/ -q`), gồm: 18 case LeadSource port nguyên văn từ
  `tools/analysis/verify_ads_rule.py` để đối chiếu hành vi. Static check xác
  nhận: không import `fastapi`/`sqlalchemy` trong `app/modules/`, không
  hard-code business value (chỉ có hằng số cấu trúc `ADS = "ADS"` của enum
  `LeadSource`), không `float` cho tiền, không log dữ liệu cá nhân.

  12/13 REQUIRED check PASS (E1 trên fixture). **CHECK-101-08 BLOCKED** —
  đối chiếu 254 đơn (01.2026) / 146 đơn (06.2026) với file thô thật đòi hỏi
  `data/samples/So_chi_tiet_ban_hang.xlsx`, không có trong session này. Ghi
  rõ BLOCKED, không bịa PASS, không đoán số. TASK-101 dừng ở **VERIFYING**,
  không DONE. Cập nhật roadmap: TASK-101 đánh dấu VERIFYING; TASK-102,
  TASK-103, TASK-104 đánh dấu phần lõi đã có, ghi rõ phạm vi còn thiếu (kênh
  UI, product classification) dời sang lúc cần.
- 2026-08-23 — **TASK-101 → DONE: đóng CHECK-101-08 bằng dữ liệu thật.**
  Review trước đó yêu cầu 5 việc: (1) sửa wording CHECK-101-05 vì heading cũ
  nói đã kiểm 8 case A–G trong khi Evidence nói chưa — sửa lại chỉ claim
  đúng phạm vi `LeadSource` của TASK-101, không đụng ConversionScheme;
  (2)(3) chủ dự án cung cấp trực tiếp 2 file thật Tín Phát (01.2026,
  06.2026, xuất riêng theo tháng) — chạy `tools/analysis/reconcile_real_data.py`
  (script mới, gọi thẳng `run_import()`) tính đủ các chỉ số reviewer yêu
  cầu: raw rows, OrderID duy nhất, employee mapped/unmapped, tổng doanh số
  raw, chiết khấu, doanh số normalized, PERSONAL/ADS breakdown theo nguồn
  (mặc định nhân viên vs từ khóa), OrderID thiếu, OrderID nhiều employee.
  Kết quả: 254/146 đơn khớp tuyệt đối cả hai kỳ; đối chiếu chéo độc lập với
  dòng "Tổng cộng" tự có trong file thô (không do engine tính) cũng khớp
  tuyệt đối; (4) so sánh `Doanh số bán` raw vs `SellPrice×Qty−Discount` —
  mọi lệch (22/351 và 1/180 dòng) đều đúng bằng số ở cột Chiết khấu, khớp
  100% với DEC-114 đã biết trước, không phải phát hiện mới, không sửa rule;
  (5) không mở rộng sang ConversionScheme — xác nhận giữ nguyên ranh giới.
  CHECK-101-08 chuyển PASS, TASK-101 chuyển DONE (13/13 REQUIRED check
  PASS). File thật xóa khỏi môi trường sau khi dùng, chưa từng commit
  (DEC-108). Current Task chuyển sang TASK-105.
- 2026-08-23 — **Đơn giản hóa phân quyền — ADMIN-only (DEC-124).** Chủ dự án
  trả lời trực tiếp, đóng cùng lúc C12/C13/C14 mà DEC-123 để mở: công cụ quản
  trị nội bộ, MVP chỉ một vai trò `ADMIN`, không `viewer`/`editor`/
  `employee_scope`. Non-ADMIN nhận `403` ở mọi API trừ `auth/login`,
  `auth/logout`, `auth/me`, và không mở được frontend; phân quyền vẫn kiểm ở
  backend, không chỉ ẩn UI. Database thiết kế cho phép thêm vai trò sau này
  (cột `role` enum), không xây trước hạ tầng nhiều vai trò.

  Viết lại `ADR-105` §4 (ma trận 3 vai trò → nhị phân ADMIN/không-ADMIN) và
  §5 (`employee_scope` hạn chế → mở rộng vai trò trong tương lai, không xây
  trước); §2/§3 (route) không đổi. Chuyển §4/§5 sang `Accepted` — thêm annotation
  "Sửa đổi 2026-08-23" vào DEC-123 thay vì viết lại lịch sử. Đóng C12/C13/C14
  trong `docs/analysis/10_OPEN_QUESTIONS.md`, chuyển vào bảng "Đã đóng". Cập
  nhật `PROJECT/PROJECT_PROFILE.md` (Authentication), 2 check PRELIMINARY của
  TASK-204 (ma trận → nhị phân). **Completion Gate TASK-203/204 vẫn KHÔNG
  freeze** — chấp nhận ADR khác với freeze gate của task còn hai phase nữa
  mới tới. Đồng bộ `PROJECT/LO_TRINH_DE_HIEU.md`. Chạy lại 5 validator
  governance — PASS.
- 2026-08-23 — **TASK-105 DONE (price_engine + PriceProvider).** Tạo
  `docs/tasks/TASK-105-price-engine.md`, freeze Completion Gate trước khi
  code. Mở rộng `WorkingLine` thêm `accounting_purchase_price` và
  `price_source` (default `Pending`, không bao giờ suy ra 0 — DEC-103, khớp
  nguyên tắc 03_DATA_MODEL_RULES §5 đã dùng cho quantity/sell_price ở
  TASK-101). Định nghĩa `PriceProvider` (Protocol) ổn định cho TASK-401 sau
  này, và `PendingPriceProvider` — implementation đúng cho 100% dòng ở
  Phase 1 vì thật sự chưa có Price Master nào, không phải giới hạn của môi
  trường test (khác TASK-101, không cần dữ liệu thật để đối chiếu). Nối
  `apply_prices()` vào `run_import()` làm bước 8, thêm tham số
  `price_provider` tùy chọn cho dependency injection. 8 test mới (provider,
  price_engine, 2 test tích hợp pipeline dùng provider giả lập) — xác nhận
  cả trường hợp provider "thật" miss một sản phẩm vẫn giữ Pending, không
  âm thầm dùng giá của sản phẩm khác. 9/9 REQUIRED check PASS, 57/57 test
  tổng, không regression trên 49 test TASK-101. Current Task chuyển sang
  TASK-106.
- 2026-08-23 — **TASK-106 DONE (adjustment_engine).** Trước khi code: chủ
  dự án làm rõ 4 điểm nghiệp vụ qua AskUserQuestion, ghi lại thành **DEC-125**
  — kết luận đúng phương án (b) mà S011 đã nêu: `KpiAdjustment` không có
  nguồn raw, là dữ liệu chọn tay sau khi import, không phải thứ để "parse".
  Bốn quy tắc cụ thể: Qua kho/NCC giao tính theo phương tiện giao (xe máy
  nhẹ/cồng kềnh/ô tô = -50k/-100k/-200k, không theo model); KHBH/Thợ lắp chỉ
  có mặc định khi sản phẩm là điều hòa (-50k/-200k), ngoài điều hòa luôn
  nhập tay; nhận diện điều hòa bằng khớp từ khóa trên `ProductRaw` (đã xác
  nhận khả thi trên dữ liệu thật); kích hoạt là người dùng chọn tay, không
  có quét tự động. Tạo `docs/tasks/TASK-106-adjustment-engine.md`, freeze
  Completion Gate trước khi code. Xây `AirConditionerClassifier` +
  `AdjustmentResolver` (`app/modules/adjustment/`) + `config/adjustments.yaml`
  — **module tính toán độc lập, không nối `run_import()`, không thêm field
  domain model** (khác TASK-105 — không có "mọi dòng đều Pending" nào đúng
  ở đây, vì không có nguồn dữ liệu thật nào để tự động áp). 17 test mới, tất
  cả nhánh (3 tier × 2 loại, AC/non-AC × 2 loại, không khớp, loại lạ) đều
  trả `None` đúng lúc, không suy đoán. 5/5 REQUIRED check PASS, 74/74 test
  tổng, không regression. Current Task chuyển sang TASK-107.
- 2026-08-23 — **TASK-107 DONE (profit_engine).** Ngay sau khi chấp nhận
  TASK-106 DONE, chủ dự án chốt luôn 6 nguyên tắc ranh giới cho profit/
  adjustment trước khi cho phép code TASK-107 — ghi lại thành **DEC-126**:
  (1) AccountingProfit độc lập hoàn toàn với KPI Adjustment; (2) Adjustment
  không ghi đè dữ liệu kế toán; (3) một Order phải hỗ trợ nhiều Adjustment
  records khi có persistence thật; (4) phân biệt `suggested_amount` (từ
  `AdjustmentResolver`, TASK-106) và `final_amount` (người dùng xác nhận);
  (5) chỉ Adjustment đã xác nhận mới dùng cho `EligibleKpiProfit`; (6) không
  mặc định adjustment chưa xác định = 0. Hệ quả: TASK-107 **chỉ** triển khai
  `AccountingProfit`, không tự mở rộng sang `EligibleKpiProfit` vì
  persistence/xác nhận Adjustment chưa sẵn sàng. Xây
  `profit_engine.compute_accounting_profit()` (hàm thuần túy, `None` khi
  thiếu bất kỳ input nào) + `apply_accounting_profit()`, nối vào
  `run_import()` làm bước 9 — tự động, không cần chọn tay (khác TASK-106) vì
  chỉ dùng field đã sẵn có trên `WorkingLine`. Xác nhận bằng grep:
  `profit_engine` không có bất kỳ import/dependency nào vào
  `app.modules.adjustment`. 9 test mới, gồm case cố ý đặt discount cực lớn
  để xác nhận công thức không bị discount ảnh hưởng (đúng §U, khác
  `TotalSales`). 6/6 REQUIRED check PASS, 83/83 test tổng, không regression.
  Current Task chuyển sang TASK-108.

## Nợ Kỹ Thuật / Cảnh Báo Vận Hành

Ghi theo yêu cầu của Independent Review #4 khi duyệt TASK-108A-1.

### TD-001 — F2/F4 là WARNING, phải hiển thị trong Review Queue/UI

`tools/analysis/reconcile_conversion.py` phân loại kết quả thành HARD FAILURE
(F1/F3/F5 — quyết định exit code) và **WARNING / REVIEW SIGNAL** (F2/F4 —
không làm exit non-zero):

- **F2** — nhân viên đang `active` và hiệu lực trong kỳ nhưng không khớp dòng
  nào. Có thể sai `raw_prefix` (lỗi thật), cũng có thể chỉ là không có doanh
  số kỳ đó (bình thường).
- **F4** — tên chưa map có số dòng ≥ nhân viên đã map nhỏ nhất. Dấu hiệu
  master data đang thiếu người đáng kể.

**Yêu cầu bắt buộc:** hai cảnh báo này **phải được hiển thị rõ ràng** trong
Review Queue / UI khi xây (TASK-110 trở đi). **Không được âm thầm bỏ qua.**

**Vì sao:** một F4 bị nuốt nghĩa là một nhân viên thật đang bán hàng mà hệ
thống không biết — và theo DEC-127 §8, mọi dòng của người đó trả `Unresolved`,
tức **không nhận tỉ lệ nào**, tức không vào KPI của ai. Im lặng ở đây là mất
doanh số của một người thật khỏi bảng lương.

Owner: TASK-110. **ĐÃ XỬ LÝ (S016). Sáu vòng review siết dần provenance:
#1 yêu cầu mỗi mục phải truy vết được (S017); #2 yêu cầu F4 bỏ qua
`employee_raw` rỗng và F6 chấm theo effective dating từng dòng (S018); #3 yêu
cầu F3 chỉ đánh dấu dòng thật sự ambiguous, F4 giữ mọi biến thể raw, và F6
không phát khi thiếu ngày — HD-110-04/DEC-130 (S019); #4 yêu cầu **mọi**
provenance dựng từ chính tập row của finding, và F3 cũng cần ngày —
HD-110-05/DEC-131 (S020); #5 là một **Architecture Repair** — xóa nguồn sự
thật thứ hai cho việc chọn employee record, xóa kênh provenance song song
(`details`), và fail-fast cho master data hỏng — HD-110-06/07/08 → **DEC-132**
(S021). **Chưa vòng nào PASS**; chờ Review #6 xác nhận.** F2/F4 nay do `app/modules/validation/validator.py` sinh ra trên chính
luồng `run_import()`, không còn chỉ nằm trong script phân tích chạy tay. Bằng
chứng: **CHECK-110-12** (F2 có mặt trong `ImportResult.review_queue`),
**CHECK-110-13** (F4, và F2/F4 không làm `run_import()` raise),
**CHECK-110-14** (`reconcile_conversion.py` giữ nguyên hành vi, 24/24 test
không sửa). Cả ba PASS. Tiêu chí F1–F5 đã dời sang
`app/modules/validation/employee_mapping.py`; script phân tích import ngược
lại đúng các tên đó, nên hai đường dùng chung một bộ tiêu chí thay vì hai bản
cài đặt. Xem `docs/tasks/TASK-110-validation-review-queue.md`.

**Chưa đóng hoàn toàn:** màn hình duyệt thật vẫn là TASK-305 — hiện F2/F4 nằm
trong `ImportResult`, chưa có UI hiển thị. Đóng hẳn TD-001 khi TASK-305 xong.

## Session tiếp theo

Có hai session được đề xuất, thuộc hai track độc lập — chủ dự án chọn thứ tự,
không có ràng buộc kỹ thuật bắt buộc cái nào trước:

### Track A (Tín Phát) — Recommended Session: TASK-108 (conversion_engine)

Purpose:
**TASK-107 đã DONE** (2026-08-23) — `AccountingProfit` tồn tại trên mỗi
`WorkingLine`, tự động tính ở bước 9, `None` khi giá nhập còn Pending.
`EligibleKpiProfit` cố ý chưa làm (DEC-126) — không chặn TASK-108, vì
`ConversionScheme`/quy đổi doanh thu không phụ thuộc `EligibleKpiProfit`.

TASK-108 là **task rủi ro cao nhất trong toàn bộ roadmap** (Risk 5/5, Blast
Radius 5/5 — xem bảng "Chấm điểm sơ bộ"). Bước 10–11 của §22 đặc tả: phân
giải `ConversionScheme` **độc lập** với `LeadSource` — tra config theo
`(employee, lead_source, ngày của đơn)` (DEC-119, DEC-121, ADR-104), sau đó
quy đổi doanh thu qua 2 bucket **độc lập** PERSONAL/ADS. Sai ở đây nghĩa là
sai lương/thưởng của ai đó.

Các REQUIRED check đã ghi sẵn ở mục "Completion Gate sơ bộ" phía trên (đọc
kỹ trước khi code) — trong đó quan trọng nhất:
- Không đường code nào suy tỉ lệ trực tiếp từ `LeadSource` — case E/F của
  DEC-119 là phép kiểm bắt buộc (cùng `PERSONAL` nhưng nhân viên Nội thành
  phải ra tỉ lệ khác nhân viên thường).
- Tra tỉ lệ dùng **ngày của đơn**, không dùng thời điểm chạy (effective-dating
  đúng, DEC-121) — thêm một dòng chính sách tương lai rồi chạy lại kỳ lịch sử
  phải cho kết quả không đổi.
- Tổ hợp `(employee, lead_source, ngày)` không khớp dòng config nào phải trả
  `Unresolved` + Review Queue — không mượn tỉ lệ của nhân viên khác, không
  mặc định về bất kỳ tỉ lệ nào.
- Nạp lại 14 kỳ của workbook mẫu phải tái hiện đúng cột `F` của `Summary
  2026` — đây là phép kiểm engine cài đúng phép toán.

Files to read first:
- `PROJECT/PROJECT_PROGRESS.md` mục "Completion Gate sơ bộ" — toàn bộ check
  TASK-108 đã ghi sẵn, đọc trước khi viết Ready Gate cho task
- `docs/adr/ADR-104-lead-source-vs-conversion-scheme.md` — kiến trúc tách
  LeadSource/ConversionScheme
- `PROJECT/PROJECT_DECISIONS.md` (DEC-119, DEC-120, DEC-121)
- `tools/analysis/verify_ads_rule.py` — bản tham chiếu đã verify 31/31 case,
  bao gồm case E/F dùng làm phép kiểm
- `app/modules/lead_source/classifier.py` — pattern config-driven +
  effective-dating đã dùng ở TASK-101, nên theo cùng phong cách
- `app/pipeline.py`, `app/modules/domain/models.py` — code đã có

### Track B (Governance) — Recommended Session: S009 — REM-T06

Purpose:
REM-T05 đã DONE (S008). REM-T06 (vệ sinh repository root, MICRO, Tier A) 
nay READY — gate FROZEN, sẵn sàng implement. Không còn cần hoàn thiện 
Ready Gate; S009 sẽ triển khai luôn. Xem "Track Governance — Bảo Trì Nền 
Tảng" phía trên để có chi tiết đầy đủ.

Files to read first:
- `PROJECT/PROJECT_PROGRESS.md` (mục "Track Governance")
- `docs/sessions/S008-rem-t05-documentation-truth-up.md`
- `docs/audit/S001_AUDIT_FINDINGS.md` (FIND-009)

### Ghi chú cho session nào mở PHASE-02 (chưa phải bây giờ)

`ADR-105` đã dựng sẵn bản đồ route (§2/§3) và mô hình phân quyền (§4/§5) cho
TASK-203/204. **Cả bốn mục đều `Accepted`** (DEC-123 cho §2/§3; DEC-124
2026-08-23 cho §4/§5, sau khi chủ dự án xác nhận trực tiếp: công cụ quản trị
nội bộ, chỉ một vai trò `ADMIN`, không `viewer`/`editor`/`employee_scope`
trong MVP). **Completion Gate của TASK-203/204 vẫn CHƯA freeze** — ADR được
chấp nhận không tự động freeze gate của task tương ứng.

Quy trình đúng khi PHASE-02 mở:
1. Chạy Roadmap Finalization đầy đủ cho TASK-203 và TASK-204
   (`governance/core/00_SESSION_ORCHESTRATION.md` → "Hoàn thiện Roadmap",
   9 bước), dùng ADR-105 làm bản thiết kế đã chốt chứ không phải bản nháp —
   không còn câu hỏi nghiệp vụ nào mở nên bước này nên nhanh.
2. Freeze Completion Gate dựa trên 6 check PRELIMINARY đã có sẵn trong mục
   "Completion Gate sơ bộ" phía trên, điều chỉnh nếu thực tế lúc đó khác.

Không còn phụ thuộc nghiệp vụ nào (C12/C13/C14 đã đóng) — bước 1 giờ chỉ còn
là thủ tục hoàn thiện gate, không cần hỏi lại chủ dự án gì thêm cho phần này.

### Bắt buộc cho cả hai track

Trước khi mở bất kỳ session nào ở trên: thực hiện "Đồng Bộ Nhánh" (đầu file
này) trước tiên. Đây chính là bước từng bị bỏ qua dẫn tới sự cố cần hợp nhất
hôm nay (DEC-118).
