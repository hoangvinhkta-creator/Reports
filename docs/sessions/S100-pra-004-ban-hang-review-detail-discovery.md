# S100 — TASK-PRA-004 Session 1: Discovery + Vertical Contract Freeze

Ngày: 2026-09-03
Task Mode: SPIKE / DISCOVERY (chuẩn bị cho MAJOR)
Loại phiên: docs-only — KHÔNG viết production code, KHÔNG sửa schema, KHÔNG migration.

---

## (1) SESSION_RESULT

```text
SESSION                   = S100 — PRA-004 Discovery + Vertical Contract Freeze (docs-only)
DISCOVERY_RESULT          = CONTRACT_FROZEN
PRODUCTION_CODE_DELTA     = 0 dòng
SCHEMA_CHANGED            = NO       MIGRATION_ADDED = NO       INDEX_ADDED = NO
DEPENDENCY_ADDED          = NO       CONFIG_CHANGED  = NO
TRACKING_CHANGED          = NO       INFRASTRUCTURE_CHANGED = NO
PRA-001/002/003_CHANGED   = NO
BLOCKING_FINDINGS         = 0
OWNER_DECISIONS_REQUIRED  = NONE
SCOPE_DRIFT               = NO
IMPLEMENTATION_READY      = YES
NEXT_VERTICAL_ACTION      = PRA-004 MAJOR IMPLEMENTATION
```

## (2) CANONICAL_SHA

```text
DEFAULT_BRANCH (origin HEAD) = claude/extract-upload-repo-gq2ws4
EXPECTED_HEAD                = 8181cebe0619a9c8d12604168a90914c04b3692f
git rev-parse origin/claude/extract-upload-repo-gq2ws4
                             = 8181cebe0619a9c8d12604168a90914c04b3692f
KẾT LUẬN                     = CANONICAL_NOT_MOVED — khớp CHÍNH XÁC EXPECTED
LOCAL HEAD (đầu phiên)       = 8181cebe0619a9c8d12604168a90914c04b3692f
SESSION_BRANCH               = claude/pra-004-sales-review-detail-0b2z4w
                               (tạo từ ĐÚNG canonical trên; KHÔNG dùng main)

scripts/branch_authority_check.sh (E1, đầu phiên):
  DEFAULT_TIP    = 8181cebe0619a9c8d12604168a90914c04b3692f
  HEAD_SHA       = 8181cebe0619a9c8d12604168a90914c04b3692f
  MODE           = BRANCH
  CURRENT_BRANCH = claude/pra-004-sales-review-detail-0b2z4w
  STOP — BRANCH AUTHORITY UNRESOLVED: nhánh phiên chưa có upstream
        (đúng như dự kiến với nhánh mới; giải quyết bằng chính lần push của phiên này)
```

Tiền đề đã xác minh: `TASK-PRA-003 = DONE` (S099, Owner đã nghiệm thu
`CHECK-PRA003-07` trên production, 12/12 REQUIRED PASS). `TASK-PRA-002 = DONE`.
`TASK-PRA-001 = DONE`. Điều kiện mở PRA-004 đã thoả.

## (3) BUSINESS_GOAL

Từ một con số tổng hợp trên Tổng quan, Owner đi xuống được tới tận dòng hàng:

```
Tổng quan → Bán hàng → Đơn hàng → Dòng hàng → AUTO / CẦN KIỂM TRA → Lý do
```

PRA-004 là **TRUY VẾT**, KHÔNG phải "Review Management System". Toàn bộ
CHỈ-ĐỌC.

## (4) PHƯƠNG PHÁP DISCOVERY

Không audit toàn repo. Trace đúng những gì cần:

1. Đọc `PROJECT/PROJECT_PROGRESS.md` (khối S099/S098/S097 hiện hành),
   `PROJECT/LO_TRINH_DE_HIEU.md`, `PROJECT/REVIEW_BUDGET_LEDGER.md`.
2. Đọc `docs/tasks/TASK-PRA-003-tong-quan-nhan-vien.md` (contract + gate).
3. Trace `tools/db/schema.py` — ba bảng `order_line_current` /
   `order_line_source_version` / `order_line_result_version`.
4. Trace tầng PRA-003 vừa tạo: `app/web/analytics_queries.py`,
   `app/web/analytics_presentation.py`, hai template, route trong
   `app/web/server.py`.
5. Trace đường sinh `pending_reasons`:
   `app/modules/exporting/excel_exporter.py::_present_lines` →
   `app/history/extraction.py::build_result_lines` →
   `app/web/history_store.py:662`.
6. **Chạy thật** đường production trên fixture golden rồi persist và truy vấn
   SQL — toàn bộ số liệu ở mục 5 và mục 6 là đo được, không suy đoán.

Môi trường: dependency đã khai trong `pyproject.toml`
(`[dev]`, `[web]`) được cài vào môi trường phiên để chạy trace. **KHÔNG thêm
dependency nào vào `pyproject.toml`** — `DEPENDENCY_ADDED = NO`.

## (5) CURRENT_DATA_CAPABILITY — kết quả đo (E1)

Chạy `run_import_production` → `present_lines` → `extraction.build_*_lines` →
`history_writer.write_run_history` trên `tests/fixtures/golden/period_2026_01.xlsx`,
rồi truy vấn SQL trên dữ liệu đã persist:

```text
PERSISTED OK
351 dòng · 254 đơn

Q1 danh sách 254 đơn (1 câu SQL, GROUP BY order_key)  : 6,6 ms
Q2 chi tiết đơn BH62439 (4 dòng)                      : 1,3 ms

Đơn TOÀN AUTO        : 1    (BH62063)
Đơn CẦN KIỂM TRA     : 253
Đơn TRỘN AUTO+PENDING: 1    (BH62439)
Đơn nhiều ngày bán   : 0
Đơn nhiều nhân viên  : 0     ← ARTEFACT của ẩn danh hoá, xem FIND-PRA004-03
Phân bố số dòng/đơn  : {1:191, 2:41, 3:16, 4:3, 5:1, 6:1, 7:1}  → Σ = 351

Coverage / 351 dòng:
  total_sales 351 · employee_normalized 351 · employee_group 351
  product_group_final 351 · conversion_rate_final 351
  accounting_purchase_price 2 · kpi_purchase_price 2
  accounting_profit 2 · eligible_kpi_profit 2
  canonical_product_code 0        ← KHÔNG dùng được làm tên sản phẩm
  product_raw rỗng 0/351          ← dùng được trên MỌI dòng
```

**Kết luận Q1 = CÓ, Q2 = CÓ.** Mô hình đã lưu ĐỦ để dựng cả danh sách đơn lẫn
chi tiết dòng, không thiếu trường nào, không cần schema mới.

## (6) REVIEW_REASON_MODEL — phát hiện then chốt của phiên

### Reason nằm ở đâu

`order_line_result_version.pending_reasons_json`, phía **RESULT**, có current
pointer `current_result_version_id` (`nullable=False`).

### Vũ trụ mã là ĐÓNG

Đường sinh cho thấy `pending_reasons` chỉ lấy được từ ba nguồn đóng:

```
PriceResolutionReason (enum ĐÓNG, 10 giá trị — docstring: "Không có UNKNOWN")
validation CATEGORIES (hằng số, 8 giá trị)
ba chuỗi Pending.<field>                                    (3 giá trị)
                                            ⟹ tối đa 21 mã
```

Đo trên fixture (351 dòng):

```text
IDENTITY_SOURCES_UNAVAILABLE        349
Missing.PurchasePrice               349
Pending.accounting_purchase_price   349
Pending.accounting_profit           349
Pending.eligible_kpi_profit         349
Suspicious                            8

Số reason/dòng: {0: 2 dòng, 5: 341 dòng, 6: 8 dòng}
```

### Reason có trình bày trực tiếp được không — CÓ

Bốn tính chất, tất cả `FACT`:

- Mã ngữ nghĩa ổn định, KHÔNG phải văn xuôi tự do.
- MỘT dòng có NHIỀU reason (đo được 5 hoặc 6) — UI phải chịu được n > 1.
- `details` (văn xuôi có chứa số dòng nguồn, `order_id`, thông điệp chẩn
  đoán) **KHÔNG được persist** — chỉ `reasons` đi vào JSON. Vì vậy KHÔNG có
  đường nào để stack trace / ID nội bộ / snapshot-version ID lọt vào lý do.
- Thẩm quyền trình bày **ĐÃ TỒN TẠI và ĐANG CHẠY PRODUCTION**:
  `app/beta_presentation.py::REASON_DISPLAY_LABELS`
  (S069, dùng bởi Owner Launcher và trang `/`).

⟹ PRA-004 **TÁI DỤNG** bảng nhãn đó và chỉ MỞ RỘNG cho 14 mã còn thiếu. Đây
là ánh xạ tối thiểu, **KHÔNG phải taxonomy mới**. 7 nhãn cũ giữ nguyên từng
chữ vì chúng đang hiển thị cho Owner ở nơi khác.

Đây là câu trả lời cho §6 chỉ thị: **current persistence ĐỦ**. Không mở
subsystem mới, không BLOCKING.

## (7) ORDER_STATUS_MODEL

Tái dụng NGUYÊN VẸN `analytics_queries._order_status()`:
đơn có ≥1 dòng `PENDING` ⟹ CẦN KIỂM TRA; ngược lại AUTO. Đây chính là ngữ
nghĩa Owner đã nghiệm thu trên production (15 AUTO / 25 Review, 09/2026).
KHÔNG thêm `PARTIAL`/`WARNING`/`RESOLVED`/`APPROVED`.

Ca TRỘN là ca THẬT và có oracle: **BH62439** = 1 dòng AUTO + 3 dòng PENDING
⟹ đơn CẦN KIỂM TRA. Một triển khai "lấy trạng thái dòng đầu tiên" sẽ hiện
đơn này thành AUTO — CHECK-PRA004-05 bắt lỗi đó.

## (8) PROFIT / COVERAGE — rủi ro đặc thù của PRA-004

Đo được trên BH62439:

```text
4 dòng · doanh thu net 66.000.000
  LN kế toán = 500.000  nhưng CHỈ 1/4 dòng có giá trị
  LN KPI     = 400.000  nhưng CHỈ 1/4 dòng là AUTO
```

Hiện "Lợi nhuận đơn = 500.000" trần trụi khiến Owner tin đó là lợi nhuận của
cả đơn 66 triệu. Contract vì vậy khoá: **mọi ô lợi nhuận cấp đơn PHẢI mang
coverage `N / M dòng`** (tái dụng `analytics_presentation.profit()`), và khi
coverage < số dòng thì trang chi tiết hiện câu cảnh báo tường minh.

Số học đọc được từ chính các trường đã lưu (dòng AUTO của BH62439):

```text
qty=2 · sell=10.500.000 · discount=100.000 · delivery_cost=None
net              = 20.900.000 = 2×10.500.000 − 100.000
acct_purchase_pp = 10.250.000
accounting_profit=    500.000 = 2×10.500.000 − 2×10.250.000  (KHÔNG trừ chiết khấu)
eligible_kpi     =    400.000 = 20.900.000  − 2×10.250.000  (CÓ trừ chiết khấu)
```

`INFERENCE` — chênh lệch giữa hai lợi nhuận được giải thích trọn vẹn bởi
`discount`, một trường đã persisted. Vì vậy `Chiết khấu` = `REQUIRED_NOW`.

**Giới hạn trung thực (giữ nguyên, không nới):** fixture chỉ có 2 dòng AUTO
và cả hai đều `delivery_cost = NULL`, trong khi 325/351 dòng CÓ
`delivery_cost`. ⟹ Trang **KHÔNG in công thức**, **KHÔNG tuyên bố** tự dẫn
xuất lại lợi nhuận. Xem FIND-PRA004-01.

## (9) PII_BOUNDARY — audit lại từ đầu

`grep` `tools/db/schema.py` cho `customer|phone|address|shipper|warranty`:
**0 kết quả** ⟹ các trường này KHÔNG BAO GIỜ được persist; chúng **không thể**
rò rỉ qua PRA-004. Bảo đảm CẤU TRÚC, mạnh hơn quy ước.

Có trong dữ liệu đã lưu:

```text
imei         → PROHIBITED  (anonymize.py XOÁ HẲN; không rule nghiệp vụ nào đọc)
note_raw     → PROHIBITED  (anonymize.py: trên dữ liệu THẬT có chứa TÊN và SĐT khách)
employee_raw → PROHIBITED  (thô, chưa chuẩn hoá; employee_normalized mới có thẩm quyền)
source_profit→ PROHIBITED  (PRA-003 D1/D2 đã loại tường minh; không phải PII)
product_raw  → REQUIRED_NOW (anonymize.py xếp là dữ liệu NGHIỆP VỤ business logic ĐỌC,
                             giữ NGUYÊN VĂN trong fixture; 0/351 dòng rỗng)
delivery_cost→ USEFUL_BUT_DEFER
```

### Xung đột đã phát hiện — FIND-PRA004-02

`app/web/analytics_queries.py` (docstring) xếp `product_raw` chung nhóm PII và
`tests/test_analytics_queries.py` canh điều đó bằng cách đọc CHÍNH file
`analytics_queries.py`. Trong khi `tests/fixtures/golden/anonymize.py` — phân
loại ĐO trên workbook production thật (GB-3, `OD-GB-1`) — xếp `product_raw`
vào nhóm dữ liệu nghiệp vụ.

**Cách giải đã áp dụng, KHÔNG nới gate nào:** PRA-004 KHÔNG chạm
`analytics_queries.py` và KHÔNG sửa test của PRA-003. Nó tạo module truy vấn
RIÊNG (`app/web/sales_queries`) với hàng rào PII riêng, hẹp hơn đúng một
trường. Gate PRA-003 tiếp tục PASS nguyên vẹn.

## (10) QUYẾT ĐỊNH KIẾN TRÚC

```text
PAGINATION            = KHÔNG (254 đơn / 6,6 ms; production 09/2026 = 40 đơn;
                        thay vào đó CHECK-PRA004-13 ĐO trên ≥12k dòng + RE-TRIGGER)
SCHEMA / MIGRATION    = 0    (mọi trường đã persisted; order_key là cột DẪN ĐẦU
                        PK order_line_current ⟹ đã index; ix_..._sale_date đã có)
PRODUCTION WRITE      = KHÔNG
TRACKING DEPENDENCY   = KHÔNG (không trường nào cần dữ liệu Tracking mới)
DEPENDENCY MỚI        = 0    · SERVICE/WORKER/QUEUE/CACHE MỚI = 0
NAVIGATION            = Option A (một tab "Bán hàng"). Option B (bấm ô số trên
                        Tổng quan) = USEFUL_BUT_DEFER, KHÔNG triển khai.
SOURCE SEPARATION     = SỐ MỚI ONLY, bảo đảm bằng CheckConstraint(origin) × 3 bảng
```

## (11) FINDINGS

| ID | Loại | Blocking | Xử lý |
|---|---|---|---|
| FIND-PRA004-01 | TRUTHFULNESS_CONSTRAINT | KHÔNG | Đã đưa vào contract: trang không in công thức; `delivery_cost` DEFER + RE-TRIGGER |
| FIND-PRA004-02 | DOC_INCONSISTENCY | KHÔNG | Giải bằng thiết kế (module + hàng rào riêng); không sửa PRA-003 |
| FIND-PRA004-03 | HARDENING | KHÔNG | "0 đơn nhiều nhân viên" là artefact ẩn danh hoá; contract vẫn thiết kế cho n ≥ 1; RE-TRIGGER khi production lần đầu có ca đó |

**BLOCKING_FINDINGS = 0.**

## (12) NGÂN SÁCH ĐỀ XUẤT

```text
Python production: mục tiêu 266 · cảnh báo mềm 330 · DỪNG CỨNG 400
Template ≤ 220 · CSS ≤ 25 · Test ≥ 30 (0 skip mới)
Schema/migration/index/dependency/config = 0
Review budget: MEDIUM = 1 blocking repair cycle · 1 Independent Review E2
```

Thiết kế để hoàn thành trong 1 phiên MAJOR.

## (13) VALIDATORS (E1, cuối phiên)

Chạy tương xứng với phiên docs-only. Xem khối `VALIDATORS` trong
`PROJECT/PROJECT_PROGRESS.md` → khối S100 để lấy output nguyên văn.

## (14) VIỆC PHIÊN NÀY KHÔNG LÀM

Không viết production code. Không sửa schema/migration/index. Không thêm
dependency vào `pyproject.toml`. Không sửa `analytics_queries.py`,
`analytics_presentation.py`, hay bất kỳ test nào của PRA-003. Không sửa
`tests/fixtures/golden/**`. Không upload workbook mới. Không truy vấn
PostgreSQL production. Không deploy. Không tích hợp canonical. Không đánh dấu
PRA-004 DONE. Không repair REM-T06 hay FIND-PRA003-03. Không mở PRA-005.

## (15) BÀN GIAO

```text
TASK_FILE            = docs/tasks/TASK-PRA-004-ban-hang-review-detail.md
                       Status: READY · Completion Gate FROZEN (11 REQUIRED + 2 RECOMMENDED)
BASE_SHA             = 8181cebe0619a9c8d12604168a90914c04b3692f
NEXT_VERTICAL_ACTION = PRA-004 MAJOR IMPLEMENTATION
                       Thứ tự bắt buộc: sales_queries → REASON_DISPLAY_LABELS
                       → sales_presentation → 2 route → 2 template → CSS.
                       Test đơn vị TRƯỚC test route và integration.
```
