# S107 — TASK-PRA-005 Session 2: Contract Freeze "SẢN PHẨM"

Ngày: 2026-09-03
Task Mode: MAJOR (Contract Freeze — chuẩn bị cho Implementation)
Loại phiên: docs-only — KHÔNG viết production code, KHÔNG sửa schema, KHÔNG
migration, KHÔNG chạm Tracking.
Nhánh: `claude/pra-005-contract-freeze-99nuai`.

---

## (1) CONTRACT_RESULT

```text
SESSION                   = S107 — PRA-005 Contract Freeze SẢN PHẨM (docs-only)
CONTRACT_RESULT           = PASS
PRODUCTION_CODE_CHANGE    = NO
BLOCKING_FINDINGS         = 0
SCOPE_DRIFT               = NO
NEXT_VERTICAL_ACTION      = PRA-005 IMPLEMENTATION
```

---

## (2) CANONICAL

```text
DEFAULT_BRANCH (origin HEAD) = claude/extract-upload-repo-gq2ws4
EXPECTED_HEAD                = 1ebb0021e13f85fe7ac7825e1219583e4c682889
git rev-parse origin/claude/extract-upload-repo-gq2ws4
                             = 1ebb0021e13f85fe7ac7825e1219583e4c682889
KẾT LUẬN                     = CANONICAL_NOT_MOVED — khớp CHÍNH XÁC EXPECTED
LOCAL HEAD (đầu phiên)       = 1ebb0021e13f85fe7ac7825e1219583e4c682889
                              (0 ahead, 0 behind origin canonical)
WORKTREE                     = CLEAN
SESSION_BRANCH               = claude/pra-005-contract-freeze-99nuai
```

Session branch trùng chính xác canonical HEAD lúc mở phiên — không cần
fast-forward hay merge nào để đồng bộ.

## (3) DISCOVERY_STATUS

```text
DISCOVERY_STATUS   = DONE (S105, xác minh + tích hợp S106)
DISCOVERY_ARTIFACT = docs/sessions/S105-pra-005-san-pham-discovery.md (822 dòng)
```

Đọc TOÀN VĂN artifact này trước khi freeze contract (không chỉ dựa vào tóm
tắt trong PROJECT_PROGRESS.md). Evidence limitations của Discovery được giữ
nguyên đúng phân loại, KHÔNG được nâng cấp thành evidence mạnh hơn trong
phiên này:

```text
A. 12.000 dòng / 2.491 nhóm / 24-27 ms SQLite  = SESSION_MEASUREMENT_ONLY
B. ~110-150 production LOC                     = ESTIMATE, không phải kích
                                                  thước implementation đo được
C. service/fee % được Discovery ghi lại nhưng chưa tái lập độc lập ở S106/S107
```

Không mục nào trong ba mục trên là blocker cho Contract Freeze.

## (4) OWNER DECISIONS — KHOÁ TẠI PHIÊN NÀY

### OD-PRA005-01

```text
OD_PRA005_01 = RAW_DOCUMENT_DESCRIPTION
```

PRA-005 V1 gộp theo mô tả sản phẩm thô đã chuẩn hoá trên chứng từ bán hàng
(`NFC(product_raw).strip()`, tương đương `product_key` đã tồn tại). KHÔNG
phải canonical Product Identity/SKU authority/Tracking Product Identity.
Cấm fuzzy/substring/model-code merge và hybrid `COALESCE`. Chi tiết đầy đủ
+ lý do: `docs/tasks/TASK-PRA-005-san-pham.md` mục 3.

### OD-PRA005-02

```text
OD_PRA005_02 = INCLUDE_ALL_DOCUMENT_LINES
```

PRA-005 V1 bao gồm TẤT CẢ dòng chứng từ, kể cả mô tả dịch vụ/phí/điều
chỉnh, vì Reports chưa có phân loại có thẩm quyền cho product/service/fee.
Mặc định sắp bảng theo Doanh thu giảm dần — đây là mặc định TRÌNH BÀY,
không phải phân loại nghiệp vụ. Chi tiết đầy đủ + lý do:
`docs/tasks/TASK-PRA-005-san-pham.md` mục 4.

```text
OWNER_DECISIONS_RECORDED = YES — ghi tại PROJECT/PROJECT_DECISIONS.md DEC-173
```

Cả hai đúng phương án A/khuyến nghị mà Discovery S105 §28 đã đề xuất; phiên
này nâng chúng từ khuyến nghị Discovery thành `OWNER_DECISION` chính thức
theo đúng nội dung brief Contract Freeze đã nhận.

## (5) BUSINESS PURPOSE — FROZEN

> "Trong khoảng thời gian đang xem, các mặt hàng ghi trên chứng từ bán hàng
> đóng góp như thế nào vào số lượng, số đơn, doanh thu và LN KPI đã biết?"

Descriptive management analytics. KHÔNG phải Product Master, inventory
analytics, purchase analytics, canonical SKU analytics, product
recommendation, margin optimization, forecasting, hay ranking/scoring
system. Chi tiết: `docs/tasks/TASK-PRA-005-san-pham.md` mục 1.

## (6) TERMINOLOGY — FROZEN

Navigation: "SẢN PHẨM". Trong bảng/chỉ tiêu: "MẶT HÀNG" (không "SKU chuẩn",
"Sản phẩm chuẩn", "Product Identity"). Disclosure bắt buộc trên trang:

> "Mặt hàng được gộp theo tên ghi trên chứng từ. Các tên khác nhau của cùng
> một sản phẩm có thể được hiển thị thành các dòng riêng."

Cấm phơi `SHA256`/`NFC`/`product_key`/`RAW_PRODUCT_GROUP` ra UI. Chi tiết:
mục 5 file task.

## (7) SUMMARY_CONTRACT — FROZEN (4 chỉ tiêu)

```text
1. SỐ MẶT HÀNG TRÊN CHỨNG TỪ  — COUNT(DISTINCT RAW_PRODUCT_GROUP), KHÔNG "Số sản phẩm"
2. TỔNG SỐ LƯỢNG              — tái dụng ngữ nghĩa đã accepted
3. DOANH THU (NET)            — tái dụng ngữ nghĩa đã accepted
4. LN KPI                     — SUM giá trị AUTO đã biết + coverage "N / M dòng"
```

## (8) TABLE_CONTRACT — FROZEN (5 cột)

```text
MẶT HÀNG · SỐ LƯỢNG · SỐ ĐƠN · DOANH THU · LN KPI
```

Không cột Giá mua tham chiếu / Coverage riêng / Trạng thái dữ liệu /
Brand / Category / Vendor / Margin % / Score / Rank label. Lý do loại từng
cột: mục 9 file task.

## (9) SEMANTICS FROZEN — TÓM TẮT

```text
QUANTITY_SEMANTICS    = SUM(quantity), tái dụng nguyên vẹn
ORDER_COUNT_SEMANTICS = COUNT(DISTINCT order_key), KHÔNG cộng được qua mặt hàng
REVENUE_SEMANTICS     = SUM(total_sales), đọc thẳng giá trị đã lưu, phân hoạch
                        đúng của cùng tập dòng
KPI_PROFIT_SEMANTICS  = SUM_KNOWN_VALUES_WITH_EXPLICIT_COVERAGE
KPI_COVERAGE_SEMANTICS= N/M dòng, cố ý KHÔNG phần trăm, nằm trong ô LN KPI
NULL_SEMANTICS         = UNKNOWN_IS_NOT_ZERO
REFERENCE_PRICE_CONTRACT = LINE_LEVEL_ONLY — KHÔNG một PP tổng hợp cấp mặt hàng
TIME_SEMANTICS         = sale_date, tái dụng nguyên vẹn PRA-003/PRA-004
DEFAULT_SORT            = REVENUE_DESC — trình bày, KHÔNG phân loại
```

## (10) DRILLDOWN_CONTRACT

Reuse `TASK-PRA-004` `/ban-hang/<order_key>`. KHÔNG xây hệ chi tiết thứ hai.
Nếu vượt ngân sách: DEFER direct product drill-down (RECOMMENDED, không
REQUIRED — CHECK-PRA005-13). Hàng rào PII mới tái dụng đúng tiền lệ EAC-9
của PRA-004 (`sales_queries` giữ hàng rào riêng, `product_raw` không nằm
trong hàng rào; `analytics_queries.py` KHÔNG bị chạm).

## (11) BRAND_CATEGORY_VENDOR

```text
BRAND    = NOT_AVAILABLE → DEFERRED
CATEGORY = NOT_AVAILABLE (product_group_final là hằng số) → DEFERRED
VENDOR   = NOT_AVAILABLE (khái niệm Tracking) → DEFERRED
```

Không suy luận từ tên sản phẩm. Không mở dự án phân loại.

## (12) SCHEMA / AUTHORITY / TRACKING

```text
SCHEMA_REQUIRED           = NO
NEW_AUTHORITY_REQUIRED    = NO
TRACKING_CHANGE_REQUIRED  = NO
```

Mọi trường cần cho trang tối thiểu đã ánh xạ về cột đã persist (S105 §11).
Nếu implementation phát hiện nhu cầu schema: `STOP =
SCHEMA_EXPANSION_REQUIRED`, không âm thầm migrate.

## (13) PERFORMANCE_CONTRACT

```text
SESSION_MEASUREMENT_ONLY — 27 ms KHÔNG được freeze thành SLA
```

Dùng aggregation PostgreSQL thẳng, khuôn `employee_totals()`. Không cache/
materialized view/warehouse/Redis/worker/queue/OLAP/Elasticsearch.

## (14) CHANGE_BUDGET

```text
Soft target ≤ 200 production Python LOC
Vượt 200 LOC / cần schema / cần authority mới / cần sửa Tracking / cần
subsystem mới ⟹ STOP = SCOPE_EXPANSION_REQUIRED
```

Chi tiết breakdown theo component: mục 24 file task.

## (15) REAL_DATA_ACCEPTANCE

12 điều kiện A–L, đóng băng tại mục 27 file task (reconciliation doanh
thu/số lượng/LN KPI, split FTKB50ZVMV bảo toàn, dòng dịch vụ vẫn nằm trong
bảng, sort mặc định, KHÔNG PP tổng hợp, `NULL != 0`, drill-down nếu có dẫn
đúng về PRA-004). KHÔNG freeze số tiền cụ thể của kỳ tương lai làm oracle
đặt trước — Owner tự nghiệm thu trên production tại thời điểm implementation.

## (16) CONTRACT_ARTIFACT

```text
CONTRACT_ARTIFACT = docs/tasks/TASK-PRA-005-san-pham.md
Status             = READY
Completion Gate    = FROZEN (15 check: 14 REQUIRED · 1 RECOMMENDED, tất cả NOT_TESTED)
Ready Gate         = PASS (10/10 điều kiện)
```

## (17) GOVERNANCE_VALIDATORS

Chạy cuối phiên (E1). Output nguyên văn ghi tại khối tương ứng trong
`PROJECT/PROJECT_PROGRESS.md` → "CANONICAL CURRENT STATE — TASK-PRA-005
CONTRACT FREEZE".

```text
validate_structure            : PASS (21 required path)
validate_project_state        : PASS
validate_evidence             : PASS (141 REQUIRED PASS evidence record)
validate_task_completion      : PASS (12 DONE task)
validate_reference_integrity  : FAIL — ĐÚNG 3 issue REM-T06 đã biết
                                (/README.md, CODE_OF_CONDUCT.md,
                                CONTRIBUTING.md), không phát sinh issue mới.
                                Một entry KNOWN_EXEMPT_PAIRS được thêm vào
                                validate_reference_integrity.py cho
                                forward-reference tới bản ghi Independent
                                Review chưa tồn tại (đúng tiền lệ DEC-152/
                                TASK-105C).
git diff --check               : sạch
branch_authority_check.sh      : AUTHORITY_OK sau khi push
                                (AUTHORITY = BRANCH_WITH_UPSTREAM, ahead
                                default 1 commit, DIVERGENCE = WITHIN_LIMITS)
```

## (18) BLOCKING_FINDINGS / NON_BLOCKING / DEFERRED

```text
BLOCKING_FINDINGS = 0
```

Non-blocking mang theo nguyên vẹn từ Discovery: FIND-PRA005-01 (split
`product_key`, xử lý bằng cách gọi tên + OD-PRA005-01), FIND-PRA005-02
(nhãn "Số sản phẩm" va chạm EAC-5, đã đổi nhãn), FIND-PRA005-03
(`product_group_final` là hằng số, không phải category). Deferred: Brand/
Category/Vendor, trend/so kỳ/top-N/biểu đồ, ma trận Sản phẩm × Nhân viên,
khoảng ngày tuỳ chọn, "giá mua đang áp dụng" cấp mặt hàng, chuẩn hoá tên
hàng có thẩm quyền, zero-stock identity discovery gap.

## (19) SCOPE_DRIFT

```text
SCOPE_DRIFT = NO
```

Phiên này: 0 dòng production code, 0 schema, 0 migration, 0 config, 0 chạm
Tracking, 0 task mới ngoài TASK-PRA-005, 0 thay đổi roadmap. Không mở
REM-T06, không sửa `analytics_queries.py`, không thêm matching để vá
FIND-PRA005-01.

## (20) CONTRACT_EXIT_GATE

13/13 điều kiện PASS — xem `docs/tasks/TASK-PRA-005-san-pham.md` mục
"Contract Exit Gate".

```text
CONTRACT_EXIT_GATE = PASS
```

## (21) CANONICAL_INTEGRATION_STATUS

```text
CANONICAL_INTEGRATION_STATUS = NOT_YET_INTEGRATED
```

Phiên này chạy trên nhánh `claude/pra-005-contract-freeze-99nuai`, đã push.
Việc tích hợp fast-forward vào canonical (`claude/extract-upload-repo-gq2ws4`)
là một hành động riêng, chưa thực hiện trong phiên này — tương tự cách S105
(Discovery) được tích hợp riêng ở S106.

## (22) IMPLEMENTATION_READY

```text
IMPLEMENTATION_READY = YES
```

Không phụ thuộc nào chưa DONE (TASK-PRA-002/003/004 đều DONE). Không
OWNER_DECISION nào còn treo.

## (23) VIỆC PHIÊN NÀY KHÔNG LÀM

Không viết production code. Không sửa schema/migration/index. Không thêm
dependency. Không sửa `analytics_queries.py`, `analytics_presentation.py`,
hay bất kỳ test nào của PRA-003/PRA-004. Không sửa
`tests/fixtures/golden/**`. Không upload workbook mới. Không truy vấn
PostgreSQL production. Không deploy. Không tự tích hợp canonical. Không
đánh dấu PRA-005 DONE. Không repair REM-T06. Không mở PRA-006.

## (24) BÀN GIAO

```text
TASK_FILE             = docs/tasks/TASK-PRA-005-san-pham.md
                        Status: READY · Completion Gate FROZEN (14 REQUIRED + 1 RECOMMENDED)
BASE_SHA              = 1ebb0021e13f85fe7ac7825e1219583e4c682889
NEXT_VERTICAL_ACTION  = PRA-005 IMPLEMENTATION
                        Thứ tự khuyến nghị: sales_queries.py (product_totals +
                        product_lines) → sales_presentation.py (cột mặt hàng)
                        → route /san-pham → template san_pham.html → CSS.
                        Test đơn vị TRƯỚC test route và integration.
```
