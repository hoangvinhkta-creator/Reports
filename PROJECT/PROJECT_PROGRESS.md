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
2026-08-23 (GATE-00 ĐÃ DUYỆT — DEC-122, PHASE-01 mở khóa)

Overall Status:
IN_PROGRESS

Current Phase:
PHASE-00 DONE → PHASE-01 — Engine tính toán

Current Task:
TASK-101 — importer + normalizer

Current Task Mode:
MAJOR

Next Recommended Task:
TASK-101 — importer + normalizer (không còn bị chặn — GATE-00 PASS)

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
  - [ ] TASK-101 — importer + normalizer. Thực hiện 7 bước đầu của import
        workflow mục §22 đặc tả: đọc `.xlsx`, báo cáo metadata (số dòng,
        khoảng ngày, tổng doanh số, số đơn, số NVBH) trước khi commit, chuẩn
        hóa cột, áp employee mapping, nhóm theo OrderID, áp rule ADS ở cấp
        đơn, propagate nguồn đơn xuống line item. Trừ `Chiết khấu` khỏi doanh
        số (DEC-114).
  - [ ] TASK-102 — employee_mapper
  - [ ] TASK-103 — order_builder
  - [ ] TASK-104 — lead_source_engine (rule ADS). Phân giải `LeadSource` ở cấp
        OrderID, đúng hai giá trị `PERSONAL`/`ADS`, chuỗi 4 bậc: override tay →
        rule từ khóa → mặc định cấp nhân viên → mặc định hệ thống (DEC-119,
        ADR-104). **Không** quyết định tỉ lệ — đó là việc của TASK-108.
  - [ ] TASK-105 — price_engine + interface PriceProvider. Bước 8 của §22 đặc
        tả: tra giá nhập nếu có Price Master, chưa có thì Pending.
  - [ ] TASK-106 — adjustment_engine. Bước 9 của §22 đặc tả.
  - [ ] TASK-107 — profit_engine. Bước 11 của §22 đặc tả, phần lợi nhuận.
  - [ ] TASK-108 — conversion_engine (2 bucket PERSONAL/ADS). Bước 10 và 11
        của §22 đặc tả. Phân giải `ConversionScheme` **độc lập** với
        `LeadSource`, tra config theo `(employee, lead_source, ngày của đơn)`
        (DEC-119, DEC-121, ADR-104), sau đó quy đổi từng bucket độc lập rồi
        cộng lại. Engine tự tổng hợp `PersonalProfit`/`AdsProfit` từ phân loại
        cấp đơn — `X` không còn là đầu vào (DEC-120).
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
  - [ ] GATE-01 — Đối chiếu với file thô thật; xác nhận chênh lệch +6,0% của
        Hoàng/Kiên do không di trú (DEC-120) là chấp nhận được với số liệu
        thật; đóng C11 (88 dòng chưa map)

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

### Session tiếp theo cho track này

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
- Mọi phase: không tên nhân viên, tỉ lệ quy đổi, target, số tiền adjustment
  hay từ khóa ADS nào xuất hiện dưới dạng literal trong mã nguồn ứng dụng
  (E1, kiểm chứng được bằng grep).

## Trạng thái Task hiện tại

Task:
TASK-101 — importer + normalizer

Task Mode:
MAJOR

Status:
PLANNED — chưa bắt đầu implement; sẵn sàng vào Ready Gate

Required Gate Progress:
GATE-00 PASS (DEC-122). Chi tiết TASK-101: xem mô tả ở roadmap PHASE-01 phía
trên (7 bước đầu của import workflow §22 đặc tả) và Ready Gate chuẩn của
`governance/core/TASK_READY_GATE_STANDARD.md`.

Primary Agent Tier:
B

Escalation Tier:
C

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
- Chưa có — chưa tồn tại mã ứng dụng nào.

## Quyết định gần đây
- Xem `PROJECT/PROJECT_DECISIONS.md` — DEC-101 đến DEC-121 (track Tín Phát).
  Ba quyết định mới nhất, từ đợt xác nhận nghiệp vụ 2026-08-23:
  - **DEC-119** — tách `LeadSource` khỏi `ConversionScheme`; `TINPHAT_ADS` bị
    loại bỏ. Xem ADR-104.
  - **DEC-120** — không di trú dữ liệu ADS lịch sử; thay thế DEC-112. Gỡ mốc
    13.883.242 khỏi REQUIRED check của TASK-108.
  - **DEC-121** — 2026 là giai đoạn chuyển đổi; mốc chuẩn chính thức
    01/01/2027; mọi business rule mang `effective_from`/`effective_to` và tra
    theo ngày của đơn.
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

## Session tiếp theo

Có hai session được đề xuất, thuộc hai track độc lập — chủ dự án chọn thứ tự,
không có ràng buộc kỹ thuật bắt buộc cái nào trước:

### Track A (Tín Phát) — Recommended Session: S001 — Phase 1, từ TASK-101

Purpose:
**GATE-00 đã PASS (DEC-122, 2026-08-23).** Bắt tay ngay TASK-101 (importer +
normalizer) — không còn gì chặn. Đọc Ready Gate của TASK-101 trước khi
implement (`governance/core/TASK_READY_GATE_STANDARD.md`), rồi bám đúng chuỗi
phân giải hai bậc LeadSource/ConversionScheme của ADR-104 khi tới TASK-104 và
TASK-108. C3 đã có mặc định ghi nhận, đóng lại đúng lúc ở TASK-403. C11 còn
mở, không chặn Phase 1, đóng trước GATE-01.

Files to read first:
- `PROJECT/PROJECT_PROGRESS.md` (mục "Trạng thái Task hiện tại" — TASK-101)
- `PROJECT/PROJECT_PROFILE.md`
- `PROJECT/PROJECT_DECISIONS.md` (đặc biệt DEC-119, DEC-120, DEC-121, DEC-122)
- `docs/adr/ADR-104-lead-source-vs-conversion-scheme.md`
- `docs/spec/Dac_ta_cong_cu_bao_cao_kinh_doanh.docx`
- `docs/analysis/`

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

### Bắt buộc cho cả hai track

Trước khi mở bất kỳ session nào ở trên: thực hiện "Đồng Bộ Nhánh" (đầu file
này) trước tiên. Đây chính là bước từng bị bỏ qua dẫn tới sự cố cần hợp nhất
hôm nay (DEC-118).
