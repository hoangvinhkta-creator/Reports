# S095 — TASK-PRA-003 Session 2: Roadmap Finalization (Freeze Contract & Gate)

Ngày: 2026-09-03
Task Mode: MAJOR (phiên finalization — docs-only)
Loại phiên: **KHÔNG viết production code**, KHÔNG sửa schema, KHÔNG migration,
KHÔNG chạm Tracking/hạ tầng.

---

## (1) FINALIZATION_RESULT

```text
SESSION                   = S095 — PRA-003 Roadmap Finalization (docs-only)
FINALIZATION_RESULT       = CONTRACT_FROZEN
TASK-PRA-003              = IN_PROGRESS / READY_FOR_IMPLEMENTATION
COMPLETION_GATE           = FROZEN (14 check: 12 REQUIRED + 2 RECOMMENDED)
REVIEW_BUDGET_LINEAGE     = MỞ (MEDIUM · allowed 1 · used 0)
PRODUCTION_CODE_ADDED     = 0 dòng
SCHEMA_CHANGED            = NO       MIGRATION_ADDED = NO
TRACKING_CHANGED          = NO       INFRASTRUCTURE_CHANGED = NO
PRA-001 / PRA-002 CHANGED = NO       DEPENDENCY_ADDED = 0
IMPLEMENTATION_READY      = YES
```

Phiên này làm đúng BƯỚC 2 mà S094 mục 23 chỉ định, không hơn: viết task file,
freeze gate, mở lineage ngân sách. Không freeze gate trong phiên discovery và
không bắt đầu implement trong phiên finalization.

## (2) CANONICAL_SHA

```text
DEFAULT_BRANCH (origin HEAD) = claude/extract-upload-repo-gq2ws4
EXPECTED_HEAD                = facf090c782b022730ecc5f1cf0d0b02e29ca8d7
git remote show origin       → HEAD branch: claude/extract-upload-repo-gq2ws4
git fetch origin claude/extract-upload-repo-gq2ws4  → OK
git rev-parse origin/claude/extract-upload-repo-gq2ws4
                             = facf090c782b022730ecc5f1cf0d0b02e29ca8d7
KẾT LUẬN                     = CANONICAL_NOT_MOVED — khớp chính xác EXPECTED
SESSION_BRANCH               = claude/pra-003-roadmap-finalization-di33bn
LOCAL HEAD lúc mở phiên      = facf090c782b022730ecc5f1cf0d0b02e29ca8d7
WORKTREE lúc mở phiên        = CLEAN
```

SessionStart hook (`.claude/hooks/session-start.sh`) xác nhận behind = 0,
ahead = 0 so với nhánh mặc định trước khi phiên đọc bất kỳ file governance nào.

## (3) DISCOVERY_INPUT_SHA

```text
DISCOVERY_BRANCH = claude/pra-003-vertical-slice-346ebn
DISCOVERY_SHA    = c776c8ae2656458099f5bcbc054bfec6f73ed058
DELTA vs canonical = 3 file, 950 dòng thêm, 0 dòng production:
  PROJECT/LO_TRINH_DE_HIEU.md                          (+54)
  PROJECT/PROJECT_PROGRESS.md                          (+89)
  docs/sessions/S094-pra-003-vertical-slice-discovery.md (+807, file mới)
```

Nhánh discovery được **fast-forward** vào nhánh phiên này để giữ nguyên
ancestry và để mọi tham chiếu tới `docs/sessions/S094-...` phân giải được
(`validate_reference_integrity`). Đây KHÔNG phải Controlled Integration vào
canonical, và nhánh discovery KHÔNG được coi là production authority — mọi
claim quan trọng đã được phiên này kiểm chứng lại trực tiếp trên mã nguồn
canonical (mục 4).

## (4) REVALIDATION — claim của S094 được kiểm chứng lại trên canonical

Không nhận claim nào của phiên discovery mà không đọc lại nguồn.

| Claim của S094 | Cách kiểm chứng ở S095 | Kết quả |
|---|---|---|
| `SnapshotRepository` phơi `engine` dưới dạng property | `grep -n "def engine" app/web/history_store.py` → dòng 81 (`LegacyRepository`), **375** (`SnapshotRepository`) | XÁC NHẬN |
| `_period()` lọc bằng `>=`/`<=` nên dòng `sale_date IS NULL` rơi khỏi mọi kỳ | đọc `app/web/history_store.py:1106-1113` | XÁC NHẬN |
| `available_periods()` chỉ có trên `LegacyRepository` | `grep` → chỉ dòng 269, trong `LegacyRepository` | XÁC NHẬN |
| Oracle golden 254/351/407/3.562.310.000 | đọc `tests/fixtures/golden/expected/period_2026_01.json`: `counts.orders=254`, `counts.lines=351`, `money.quantity_total=407`, `money.sales_normalized=3562310000` | XÁC NHẬN |
| Golden có ĐÚNG 1 nhân viên, mọi dòng `Pending` | cùng file: `employees = {"Tín Phát": {...}}`, `pricing.price_source_distribution = {"Pending": 351}`, `counts.orders_with_multiple_employee_raw = 0` | XÁC NHẬN |
| `ORIGIN_BADGE = "LEGACY"` là hằng số đã đóng gate | `app/web/legacy_presentation.py:19` | XÁC NHẬN |
| Route `/nhan-vien` hiện tại và tab nav | `app/web/server.py:454`; `app/web/templates/layout.html:16-19` (4 tab) | XÁC NHẬN |
| Các cột cần dùng đều tồn tại | trích `Column("…")` từ `tools/db/schema.py`: `order_line_current` có `sale_date`, `current_source_version_id`, `current_result_version_id`; `order_line_result_version` có `status`, `employee_normalized`, `employee_group`, `total_sales`, `accounting_profit`, `eligible_kpi_profit`; `order_line_source_version` có `quantity` | XÁC NHẬN |
| Tầng history không chép PII khách | `tools/db/schema.py` — không cột `customer`/`phone`/`address` nào trong 3 bảng fact | XÁC NHẬN |

### FACT MỚI do S095 phát hiện (không có trong S094)

**`current_totals()` coalesce `total_sales` `None` → `Decimal("0")`**
(`app/web/history_store.py:1073`:
`"total_sales": row["total_sales"] or Decimal("0")`).

Với doanh thu điều đó chấp nhận được (không dòng nào ⟹ không doanh thu).
Với LỢI NHUẬN thì **KHÔNG** — đó chính xác là cái bẫy `NULL → 0` mà chỉ thị
mục 12 cấm. Module truy vấn mới **không được** tái dụng khuôn coalesce này cho
`eligible_kpi_profit` hay `accounting_profit`.

Đã đưa thành: `FACT #4` mục 9 của task file, quy tắc P3 mục 10, và một
assertion tường minh trong CHECK-PRA003-03.

**IMEI nằm trong `order_line_source_version`.** S094 nói đúng rằng tên/SĐT/địa
chỉ khách không được chép sang tầng history, nhưng `imei` và `note_raw` thì CÓ.
`PROJECT/PROJECT_PROFILE.md` xếp IMEI/số serial thiết bị vào dữ liệu cá nhân.
Vì vậy CHECK-PRA003-10 assert thêm: body không chứa `imei`, không chứa
`note_raw`, và module truy vấn không `SELECT` hai cột đó.

## (5) OWNER_DECISIONS_LOCKED

D1, D2, D3 do Owner chốt trong chỉ thị mở phiên này. Chúng **thay thế** phần
`RECOMMENDED_DEFAULT` của S094 mục 14 — từ đây chúng là `OWNER_DECISION`,
không còn là default của agent.

Nội dung đầy đủ: `docs/tasks/TASK-PRA-003-tong-quan-nhan-vien.md` mục 3.
Tóm tắt: D1 = LN KPI chính / LN kế toán phụ / cả hai kèm coverage /
`source_profit` KHÔNG lên dashboard. D2 = target DEFER hoàn toàn, cấm dùng
target legacy cho kỳ pipeline. D3 = nhãn "Tổng số lượng", cấm nhãn "Số lượng
sản phẩm"/"Tổng số SP".

Cả ba khớp với khuyến nghị của S094, nên không phát sinh thay đổi kế hoạch
kỹ thuật nào từ việc chốt.

## (6) MINIMUM_VALUE_FILTER_RESULT

Áp đúng câu hỏi của chỉ thị mục 5 cho từng mục đề xuất: *"Nếu bỏ mục này,
người quản lý có mất một quyết định vận hành có ý nghĩa không?"*

**Tổng quan — 12 → 10 `REQUIRED_NOW`, 1 `USEFUL_BUT_DEFER`, 1 `NOT_NEEDED`.**

Bị cắt:

- **Top nhân viên trong kỳ** → `USEFUL_BUT_DEFER`. Câu hỏi "nhân viên nào đóng
  góp bao nhiêu" đã được trang Nhân viên (SỐ MỚI) trả lời đầy đủ; top-5 trên
  Tổng quan là lối tắt một cú nhấp, không phải một quyết định bị mất.
- **Ô AUTO/Cần kiểm tra theo DÒNG** → `NOT_NEEDED` vì **trùng lặp**.
  `status ∈ {AUTO, PENDING}` là một phân hoạch, nên `dòng Review = tổng dòng −
  dòng AUTO`. Coverage LN KPI (REQUIRED) đã hiển thị đúng cặp `dòng AUTO /
  tổng dòng`. Ô thứ hai chứa đúng hai con số đó không thêm thông tin.
  **Thông tin KHÔNG bị mất** — đây là cắt trùng lặp, không phải cắt an toàn.

**Nhân viên — 10 cột → 8 `REQUIRED_NOW`, 1 `USEFUL_BUT_DEFER`, 1 `NOT_NEEDED`.**

Bị cắt: cột **Δ doanh thu theo nhân viên** (`USEFUL_BUT_DEFER` — trong ca thật
đầu tiên toàn cột sẽ là `—`; `TASK-PRA-000` §L cũng xếp xu hướng nhân viên
nhiều tháng = LATER) và cột **AUTO/Cần kiểm tra** (`NOT_NEEDED`, cùng lý do
trùng lặp).

**Được giữ dù có thể tranh luận, kèm lý do:**

- **Số dòng hàng** — giữ vì nó là MẪU SỐ của cả hai coverage và của cảnh báo
  thiếu ngày bán; bỏ nó thì mọi tỉ lệ mất khả năng diễn giải. Nhưng trình bày
  CHUNG cụm với Tổng đơn ("40 đơn · 61 dòng"), KHÔNG làm thẻ KPI riêng.
- **So kỳ trước** — giữ vì mô hình kỳ (chỉ thị mục 8) và oracle H đã freeze
  nhánh "kỳ trước trống"; bỏ nó thì oracle H thành rỗng nghĩa. Giới hạn ĐÚNG
  2 chỉ tiêu (đơn, doanh thu).
- **Dòng chưa có ngày bán** — thông tin an toàn theo chỉ thị mục 6 và 11, giữ
  nguyên.
- **Nhóm nhân viên (`employee_group`)** — thông tin an toàn: so doanh thu
  `NOI_THANH` với `STANDARD_SALES` mà không thấy nhóm là so nhầm hai cơ chế.

**Headroom thu được:** ước tính ~35 dòng Python production và ~30 dòng
template. Headroom này được ghi nhận bằng cách HẠ mục tiêu Python từ 275
(S094) xuống 255, KHÔNG bằng cách thêm việc khác.

## (7) NHỮNG GÌ ĐÃ TẠO / SỬA

| File | Loại | Nội dung |
|---|---|---|
| `docs/tasks/TASK-PRA-003-tong-quan-nhan-vien.md` | MỚI | Contract đầy đủ: Goal, Business authority, D1–D3, Minimum-Value Filter, Scope, Period model, Data origin UX, Metric authority matrix, Query safety, Profit safety, Hard exclusions, Touch area + Scope Lock, Change budget, Review budget, Real vertical, Acceptance oracle, Ready Gate, **Completion Gate FROZEN (14 check)**, Evidence requirements, Exit Criteria, Escalation triggers |
| `PROJECT/REVIEW_BUDGET_LEDGER.md` | SỬA | Mở "Root Task: TASK-PRA-003" — MEDIUM, allowed 1, used 0, `BASE_SHA = facf090`, lý do chấm MEDIUM theo failure path, điều kiện mở repair cycle, Scope Lock tóm tắt |
| `PROJECT/PROJECT_PROGRESS.md` | SỬA | Thêm khối `CANONICAL CURRENT STATE — TASK-PRA-003 (AUTHORITATIVE, S095)`; hạ khối S094 xuống "lịch sử" |
| `PROJECT/LO_TRINH_DE_HIEU.md` | SỬA | Cập nhật cho Owner: ba câu hỏi đã được trả lời và chốt |
| `docs/sessions/S095-pra-003-roadmap-finalization.md` | MỚI | File này |

Không file production nào bị chạm.

## (8) FROZEN_COMPLETION_GATE — 14 check

12 REQUIRED · 2 RECOMMENDED. Risk 3 ⟹ mọi REQUIRED thực thi được phải đạt E1;
CHECK-PRA003-12 phải đạt E2. **Mọi check đang ở `Status: NOT_TESTED`** — chưa
implement nên không có gì để PASS, và không được bịa.

| ID | Priority | Nội dung | Oracle |
|---|---|---|---|
| 01 | REQUIRED | Tổng hợp trạng thái hiện hành KHÔNG double-count | O-A |
| 02 | REQUIRED | Oracle golden độc lập 254/351/407/3.562.310.000 (ĐỌC từ JSON) | O-B |
| 03 | REQUIRED | `NULL` ≠ `0` — giá trị thiếu hiện `—` | O-C |
| 04 | REQUIRED | LN KPI chỉ cộng dòng AUTO; hai coverage đúng mẫu số | O-C |
| 05 | REQUIRED | Nhân viên đối soát tổng kỳ trên 5 chỉ tiêu cộng được; Đơn KHÔNG cộng | O-D, O-D′ |
| 06 | REQUIRED | Tách nguồn: legacy không hồi quy · SỐ MỚI chỉ pipeline · không trộn trong một `<table>` · `nguon` lạ không 500 | O-E, O-F |
| 07 | REQUIRED | Real vertical production Tháng 09/2026 (40/61/15/25 + so tháng trước TRỐNG) | O-G |
| 08 | REQUIRED | Kỳ trước vắng ⟹ blank/`—`, không bao giờ `0%` | O-H |
| 09 | REQUIRED | Dòng thiếu `sale_date` được phơi ra | O-I |
| 10 | REQUIRED | Không PII (gồm `imei`, `note_raw`) và không từ vựng nội bộ | O-J |
| 11 | REQUIRED | Không hồi quy: Golden 58/2 · full suite · validators | O-K |
| 12 | REQUIRED | Independent Review E2 toàn task, artifact ở `docs/reviews/` | — |
| 13 | RECOMMENDED | CHANGE_BUDGET được đo và trong giới hạn | — |
| 14 | RECOMMENDED | Thời gian tải ≥12k dòng (ứng viên hardening DUY NHẤT) | — |

**Vì sao đúng 14 và vì sao 13/14 là RECOMMENDED chứ không REQUIRED:** 12 check
REQUIRED là 12 check bảo vệ TRỰC TIẾP kết quả PRA-003 (tính trung thực của số
quản lý, no-double-count, tách nguồn, an toàn `NULL`/coverage, real vertical,
không hồi quy, xác minh độc lập). Ngân sách thay đổi và thời gian tải là kỷ
luật quy trình và số đo — chúng được thực thi bằng luật DỪNG CỨNG ở mục 13 của
task file và bằng quy tắc 90/10, không cần nâng lên REQUIRED. Nâng chúng lên
REQUIRED là governance inflation mà chỉ thị mục 17 cấm.

## (9) VALIDATORS (E1 — output thật của phiên)

```text
validate_structure           : PASS — Deployment root PASS, 21 required paths
validate_project_state       : PASS
validate_evidence            : PASS — 116 REQUIRED PASS evidence record
validate_task_completion     : PASS — 10 DONE task
validate_reference_integrity : FAIL — ĐÚNG 3 issue đã biết của TASK-REM-T06
                               (README ở repo root, CODE_OF_CONDUCT, CONTRIBUTING)
                               — KHÔNG phát sinh mới, KHÔNG sửa (hard exclusion)
```

Ghi chú về `validate_evidence`: con số 116 KHÔNG đổi trước và sau phiên, đúng
như mong đợi — mọi check của PRA-003 đang `NOT_TESTED`, và validator chỉ đếm
record `REQUIRED` + `PASS`.

Ghi chú về `validate_reference_integrity`: bản nháp đầu của task file làm phát
sinh 2 issue mới vì trích tên hai file quy ước cộng đồng kèm phần mở rộng .md
trong dấu backtick — `REF_PATTERN` của validator coi MỌI chuỗi dạng backtick +
tên file + phần mở rộng .md/.py/.svg là một reference phải phân giải được. Đã sửa cách trích
dẫn để không tạo reference giả; số issue trở lại đúng 3 issue lịch sử.

Không chạy test suite trong phiên này: phiên không sửa một dòng code nào nên
không có gì để hồi quy. Số liệu Golden (`58 passed, 2 skipped`) trong task file
được trích từ bản ghi S092/S093 có ghi rõ nguồn — **không tuyên bố là đã chạy
lại ở đây**.

## (10) SCOPE_DRIFT_CHECK

```text
SCOPE_DRIFT = NO

Đối chiếu từng ranh giới của chỉ thị mục 19:
  write production implementation      : KHÔNG — 0 dòng
  modify Tracking                      : KHÔNG
  modify schema / migration            : KHÔNG
  modify infrastructure                : KHÔNG
  change PostgreSQL/R2/Render/Cloudflare: KHÔNG
  start PRA-004 / PRA-005              : KHÔNG
  add target                           : KHÔNG — D2 khoá, ghi vào Hard Exclusions
  add source_profit dashboard          : KHÔNG — D1 khoá
  add margin                           : KHÔNG
  add doanh số quy đổi                 : KHÔNG
  add YTD                              : KHÔNG
  add trends / charts                  : KHÔNG
  add detailed orders / products       : KHÔNG
  add Review workflow                  : KHÔNG
  add custom date range                : KHÔNG
  add quarter / year selector          : KHÔNG
  refactor unrelated code              : KHÔNG
  repair REM-T06                       : KHÔNG — 3 issue giữ nguyên, ghi rõ là DEFER
  repair deferred PRA-002 findings     : KHÔNG
  add observability system             : KHÔNG

Thu hẹp CÓ CHỦ Ý so với đề xuất S094 (đều có lý do, không phải mở rộng):
  (a) bỏ top nhân viên trên Tổng quan        — trang Nhân viên đã trả lời
  (b) bỏ ô/cột AUTO/Review theo dòng          — trùng lặp với coverage
  (c) bỏ cột Δ doanh thu theo nhân viên       — rỗng trong ca thật, §L LATER
  (d) hạ mục tiêu Python 275 → 255            — headroom từ (a)(b)(c)

90/10: 100% ngân sách phiên này dùng cho contract của kết quả quản lý thật;
hardening giới hạn 1 ứng viên có điều kiện đo (CHECK-PRA003-14). Phiên này
KHÔNG mở task mới nào.
```

## (11) IMPLEMENTATION_READY

```text
IMPLEMENTATION_READY = YES

  [x] Canonical xác minh, không moved (facf090c…)
  [x] PRA-002 = DONE và đã tích hợp vào canonical
  [x] PRA-001 = DONE, đường legacy bảo toàn bằng thiết kế (mặc định = legacy)
  [x] Owner Decisions D1–D3 LOCKED
  [x] Minimum-Value Filter đã áp; slice cuối cùng nhỏ hơn đề xuất discovery
  [x] Mọi ô truy được về một CỘT ĐÃ TỒN TẠI — không ô nào "chờ dữ liệu"
  [x] 0 schema · 0 migration · 0 dependency · 0 config · 0 index
  [x] Scope Lock tường minh; PROTECTED_CORE_IMPACT = NONE
  [x] Acceptance oracle độc lập (golden JSON) + oracle production thật
  [x] CHANGE_BUDGET riêng, có cảnh báo mềm và DỪNG CỨNG
  [x] Review budget MEDIUM = 1 cycle; lineage ĐÃ MỞ trong ledger
  [x] Completion Gate FROZEN, 14 check, mọi check NOT_TESTED (trung thực)
  [x] Task file docs/tasks/TASK-PRA-003-tong-quan-nhan-vien.md tồn tại

Không còn điều kiện nào chưa thoả.
```

## (12) NEXT_VERTICAL_ACTION

```text
BƯỚC 1 (1 phiên MAJOR implement)
  Thứ tự BẮT BUỘC: analytics_queries → analytics_presentation → route →
  template → CSS. Test tầng đơn vị viết TRƯỚC test route và test integration.
  Đo CHANGE_BUDGET liên tục; chạm 320 dòng Python ⟹ dừng lập BUDGET-AWARE PLAN;
  sẽ vượt 400 ⟹ STOP = CHANGE_BUDGET_EXCEEDED, Owner quyết.
  Đóng được ở phiên này: CHECK-PRA003-01..06, 08..11, 13.

BƯỚC 2 (Independent Review E2)
  Reviewer chạy lại độc lập tối thiểu CHECK-PRA003-01, -02, -03, -04, -05.
  Artifact lưu docs/reviews/ theo E2_INDEPENDENT_REVIEW_TEMPLATE.md.
  Đóng CHECK-PRA003-12. ≤1 blocking repair cycle.

BƯỚC 3 (Controlled Integration vào canonical)
  Chỉ sau khi E2 PASS.

BƯỚC 4 (Owner, trên production)
  Deploy, mở /tong-quan, chọn "Tháng 09/2026", đối chiếu 40 đơn / 61 dòng /
  AUTO 15 / Review 25; xác nhận ô so tháng trước TRỐNG chứ không phải 0%;
  đọc và ghi lại tiền/số lượng/hai lợi nhuận thật. Đóng CHECK-PRA003-07.
  Đó là Production Acceptance của PRA-003 và là gate REQUIRED cuối cùng.

BƯỚC 5 (tuỳ chọn, sau khi mọi REQUIRED PASS)
  CHECK-PRA003-14 — đo thời gian tải trên tập ≥12k dòng.

KHÔNG làm trong bước nào ở trên: PRA-004, PRA-005, migration, ingestion mới,
đổi Tracking, đổi hạ tầng, repair REM-T06.
```

---

## Phụ lục — Bằng chứng thực thi của phiên (E1)

```text
git remote show origin                → HEAD branch: claude/extract-upload-repo-gq2ws4
git rev-parse origin/claude/extract-upload-repo-gq2ws4
                                      → facf090c782b022730ecc5f1cf0d0b02e29ca8d7
git rev-parse HEAD (đầu phiên)        → facf090c782b022730ecc5f1cf0d0b02e29ca8d7
git status --short (đầu phiên)        → rỗng (WORKTREE CLEAN)
git rev-parse FETCH_HEAD (discovery)  → c776c8ae2656458099f5bcbc054bfec6f73ed058
git diff --stat facf090..c776c8a      → 3 file, 950 dòng thêm, 0 dòng production
git merge --ff-only c776c8a           → fast-forward OK

validate_structure                    → PASS (21 required paths)
validate_project_state                → PASS
validate_evidence                     → PASS (116 record)
validate_task_completion              → PASS (10 DONE task)
validate_reference_integrity          → FAIL, đúng 3 issue REM-T06 đã biết

Đọc lại mã nguồn canonical để revalidate (mục 4):
  app/web/history_store.py:81,269,375,1047,1073,1106
  app/web/legacy_presentation.py:19
  app/web/server.py:454
  app/web/templates/layout.html:16-19
  tools/db/schema.py (cột của 3 bảng fact)
  tests/fixtures/golden/expected/period_2026_01.json
```

Test suite: KHÔNG chạy — phiên không sửa một dòng code nào.
