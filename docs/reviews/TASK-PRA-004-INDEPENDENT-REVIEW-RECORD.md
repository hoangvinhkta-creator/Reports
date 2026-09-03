# RÀ SOÁT ĐỘC LẬP E2 (E2 INDEPENDENT REVIEW) — TASK-PRA-004 TOÀN TASK

Review ID:
PRA-004-WHOLE-TASK-REVIEW-1

Task / Release:
TASK-PRA-004 — Bán Hàng + Chi Tiết Đơn/Dòng + Review Visibility (CHỈ-ĐỌC),
đối chiếu với Completion Gate FROZEN tại S100

Reviewer Session:
S102 — Independent Review E2 (nhánh
`claude/pra-004-sales-review-detail-0b2z4w`, docs-only)

Executed By:
S102 — TASK-PRA-004 Independent Review E2 (2026-09-03)

Timestamp:
2026-09-03

Evidence Level:
E2 — mọi kết luận về tiền, số đếm, trạng thái và PII đều do reviewer TỰ
RECOMPUTE trong phiên bằng **SQL THÔ** (`sqlalchemy.text()`) chạy thẳng trên
các bảng đã persist, **KHÔNG** gọi `sales_queries` hay `sales_presentation`
để dựng oracle. Chỉ SAU KHI có kết quả thô mới đem so với module đang review.
DB test state được dựng bằng ĐƯỜNG PRODUCTION thật
(`run_import_production` → `present_lines` → `history_writer.write_run_history`),
không dựng bảng bằng tay. Phần chỉ đọc mã (ràng buộc `CHECK`, khoá chính,
AST) được ghi rõ là suy luận tĩnh có dẫn nguồn.

## Scope

Independent Review E2 cấp TOÀN TASK để quyết định `CHECK-PRA004-12`. KHÔNG
implementation, KHÔNG repair, KHÔNG Owner Production Acceptance
(`CHECK-PRA004-14` giữ `NOT_TESTED`), KHÔNG integrate canonical, KHÔNG
deploy, KHÔNG migration/schema/index, KHÔNG chạm Tracking, KHÔNG REM-T06,
KHÔNG mở PRA-005.

### Authority — xác minh TRƯỚC khi đọc bất kỳ file governance nào

```
Nhánh mặc định thật trên origin : claude/extract-upload-repo-gq2ws4
BASE_SHA (kỳ vọng / thực tế)    : 8181cebe0619a9c8d12604168a90914c04b3692f  ✓ KHỚP
CONTRACT_SHA (kỳ vọng/thực tế)  : 46a5cdb08bbac77eb4c6a7a3ad483edba988b7f9  ✓ KHỚP
REVIEW_TARGET (kỳ vọng/thực tế) : 6a23c328788af254104b335c80d7091b8c8e8163  ✓ KHỚP
CANONICAL_MOVED                 : KHÔNG
REVIEW_TARGET_MOVED             : KHÔNG
WORKING TREE tại lúc mở phiên   : SẠCH
```

Tổ tiên (ancestry) — tuyến tính, không merge, không rebase:

```
$ git merge-base --is-ancestor 8181ceb 46a5cdb  → 8181ceb IS ancestor of 46a5cdb
$ git merge-base --is-ancestor 46a5cdb 6a23c32  → 46a5cdb IS ancestor of 6a23c32
$ git log --oneline 8181ceb..46a5cdb
46a5cdb docs(PRA-004): freeze vertical contract Bán hàng + chi tiết đơn/dòng (S100)
$ git log --oneline 46a5cdb..6a23c32
6a23c32 TASK-PRA-004 S101: MAJOR implementation — Bán hàng + chi tiết đơn/dòng (CHỈ-ĐỌC)
```

`DIFF_SCOPE` (`46a5cdb..6a23c32`) — 17 file, +2723 / −22:

```
PROJECT/LO_TRINH_DE_HIEU.md                         80 +-
PROJECT/PROJECT_PROGRESS.md                        137 +-
PROJECT/REVIEW_BUDGET_LEDGER.md                     24 +
app/beta_presentation.py                            20 +
app/web/sales_presentation.py                      177 +
app/web/sales_queries.py                           271 +
app/web/server.py                                   51 +-
app/web/static/css/tinphat-ui.css                   19 +
app/web/templates/_pipeline_bits.html               15 +
app/web/templates/ban_hang.html                     54 +
app/web/templates/ban_hang_chi_tiet.html            83 +
app/web/templates/layout.html                        1 +
docs/sessions/S101-pra-004-major-implementation.md 239 +
docs/tasks/TASK-PRA-004-ban-hang-review-detail.md  354 +-
tests/test_sales_presentation.py                   314 +
tests/test_sales_queries.py                        509 +
tests/test_web_sales_detail.py                     397 +
```

### Frozen contract KHÔNG bị nới lỏng — xác minh từng chữ

Reviewer trích 14 dòng `Yêu cầu:` của bản FROZEN (`46a5cdb`) và bản hiện tại
(`6a23c32`), sắp xếp rồi `diff`:

```
$ diff yc_frozen.txt yc_impl.txt
(không có output) → IDENTICAL — không một dòng "Yêu cầu:" nào bị sửa

Priority (bản FROZEN)  : 13 REQUIRED · 1 RECOMMENDED
Priority (bản hiện tại): 13 REQUIRED · 1 RECOMMENDED   → KHÔNG đổi
```

15 dòng bị xoá trong file task là: `READY` → `IN_PROGRESS` (Status), 12 dòng
`NOT_TESTED` → `PASS` (Status của check), dòng `Yêu cầu:` của
`CHECK-PRA004-13` được thay bằng bằng chứng PASS, và placeholder
`*(chưa có)*` của Changed Files Registry. **Không một oracle `O-A…O-D`,
không một bất biến `INV-1…INV-7`, không một `Priority:` nào bị đụng đến.**

## Tài Liệu Đầu Vào Đã Đọc (Inputs Read)

- `docs/tasks/TASK-PRA-004-ban-hang-review-detail.md` — bản FROZEN tại
  `46a5cdb` (1427 dòng), đọc TRƯỚC bản implementation.
- `docs/sessions/S100-pra-004-ban-hang-review-detail-discovery.md`,
  `docs/sessions/S101-pra-004-major-implementation.md`.
- Diff `46a5cdb..6a23c32` toàn bộ, cộng mã production hiện hành:
  `app/web/sales_queries.py`, `app/web/sales_presentation.py`,
  `app/web/server.py`, `app/beta_presentation.py`, hai template mới,
  `_pipeline_bits.html`, `layout.html`.
- Nguồn thẩm quyền để đối chiếu: `tools/db/schema.py`,
  `app/web/analytics_queries.py`, `app/web/analytics_presentation.py`,
  `app/history/extraction.py`, `app/history/keys.py`,
  `app/modules/pricing/resolution/composition.py`,
  `app/modules/validation/models.py`, `app/modules/validation/rules.py`.
- `governance/core/V4_1_POLICY_FREEZE.md`, `PROJECT/REVIEW_BUDGET_LEDGER.md`.

Phân biệt thẩm quyền được giữ suốt phiên: `OWNER_DECISION` /
`FROZEN_CONTRACT` / `IMPLEMENTATION_CLAIM` / `REVIEWER_EVIDENCE`. Không một
hành vi nào của implementation được nâng thành thẩm quyền chỉ vì test đang
xanh.

## Xác Minh Độc Lập (Independent Verification)

### 1. `RAW_SQL_ORDER_RECOMPUTATION` — danh sách đơn, recompute bằng SQL THÔ

Reviewer dựng lại fixture golden qua đường production rồi recompute bằng
`text()` trên `order_line_current` JOIN đúng hai con trỏ hiện hành:

```text
O-A1  đơn (raw)                 = 254   dòng hiện hành (raw) = 351
O-A2  đơn AUTO thuần (raw)      = 1     đơn CẦN KIỂM TRA (raw) = 253
O-A3/INV-4  auto+review         = 254  == COUNT(DISTINCT order_key) = 254  -> True
O-A4  phân bố dòng/đơn (raw)    = {1: 191, 2: 41, 3: 16, 4: 3, 5: 1, 6: 1, 7: 1}
      Σ(số dòng × số đơn)       = 351  == tổng dòng 351 -> True
INV-3 Σ(lines theo đơn)         = 351 == 351 -> True
INV-1 Σ doanh thu dòng == doanh thu đơn : vi phạm = 0
INV-2 Σ số lượng dòng  == SL đơn        : vi phạm = 0
      Σ đếm dòng       == lines đơn     : vi phạm = 0
INV-5 (≥1 PENDING ⟺ CẦN KIỂM TRA)       : True

----------- SO SÁNH: RAW SQL  vs  sales_queries.order_list -----------
số đơn      raw=254  impl=254  khớp=True
LỆCH money/count/status/date trên 254 đơn × 9 trường = 0
```

O-A1…O-A4 và INV-1…INV-5 do reviewer tự đo, **rồi mới** so với
`sales_queries`: **0 lệch** trên 254 đơn × 9 trường (số dòng, số lượng, doanh
thu, LN KPI, tử số KPI, LN kế toán, tử số kế toán, trạng thái, khoảng ngày).

### 2. `RAW_SQL_BH62439` — oracle quan trọng nhất, đọc thẳng persisted rows

Reviewer KHÔNG lấy expected từ `sales_queries`. Đọc thẳng
`order_line_current` của `order_key = BH62439`:

```text
số dòng          = 4   (1 AUTO + 3 PENDING)
trạng thái đơn   = CẦN KIỂM TRA   (≥1 PENDING ⟹ CẦN KIỂM TRA)
ngày bán         = ['2026-01-08']
nhân viên (DISTINCT) = ['Tín Phát']
tổng số lượng    = 5
doanh thu (net)  = 66000000
LN kế toán       = 500000   coverage 1/4
LN KPI           = 400000   coverage 1/4
occurrence_index của các dòng = [1, 1, 1, 1]
current_source_version_id     = [45, 46, 47, 48]
  dòng 1 [PENDING] Tủ lạnh Panasonic NR-BX471GPKV  SL=1 đơn giá=14150000 CK=50000 DT=14100000
           giá vốn KT=None · giá vốn KPI=None · LN KT=None · LN KPI=None
           lý do (5) = ['IDENTITY_SOURCES_UNAVAILABLE', 'Missing.PurchasePrice',
                        'Pending.accounting_purchase_price', 'Pending.accounting_profit',
                        'Pending.eligible_kpi_profit']
  dòng 2 [PENDING] Máy Giặt Sấy LG FV1414H3BA      SL=1 đơn giá=14800000 CK=50000 DT=14750000
           giá vốn KT=None · giá vốn KPI=None · LN KT=None · LN KPI=None
           lý do (5) = [ … 5 mã ĐÚNG thứ tự trên … ]
  dòng 3 [AUTO   ] Điều hòa Daikin FTHF25XVMV      SL=2 đơn giá=10500000 CK=100000 DT=20900000
           giá vốn KT=10250000 · giá vốn KPI=10250000 · LN KT=500000 · LN KPI=400000
           lý do (0) = []
  dòng 4 [PENDING] Máy lạnh Daikin Inverter 2 HP FTKB50ZVMV SL=1 đơn giá=16300000 CK=50000 DT=16250000
           giá vốn KT=None · giá vốn KPI=None · LN KT=None · LN KPI=None
           lý do (5) = [ … 5 mã ĐÚNG thứ tự trên … ]
```

Đối chiếu với Oracle C (mục 20.3) của contract FROZEN: **khớp TRỌN VẸN** —
4 dòng, trạng thái đơn `CẦN KIỂM TRA` dù có 1 dòng AUTO, doanh thu
`66.000.000`, LN kế toán `500.000` coverage `1/4`, LN KPI `400.000` coverage
`1/4`, ba dòng PENDING mỗi dòng ĐÚNG 5 mã lý do theo ĐÚNG thứ tự đã đóng
băng, mọi giá vốn/lợi nhuận của ba dòng đó là `NULL`.

Oracle B (`BH62063`) cũng khớp trọn vẹn: AUTO · 1 dòng · 2026-01-02 · SL 1 ·
doanh thu `7.500.000` · LN kế toán `500.000` (1/1) · LN KPI `500.000` (1/1) ·
giá vốn `7.000.000`/`7.000.000` · không lý do.

**Lý do PENDING của cả 3 dòng đã xác minh:** cùng một bộ 5 mã, gốc là
`IDENTITY_SOURCES_UNAVAILABLE` (không nhận diện được sản phẩm ⟹ không lấy
được giá) kéo theo `Missing.PurchasePrice` và ba `Pending.<field>`. Nhãn
nghiệp vụ tương ứng đọc được trên HTML thật (xem mục 9).

### 3. `CURRENT_STATE_PROOF` — chỉ trạng thái hiện hành

Cấu trúc (đọc `tools/db/schema.py`):

```
order_line_current PK = (order_key, product_key, occurrence_index)
  current_result_version_id → order_line_result_version.id   (PRIMARY KEY)
  current_source_version_id → order_line_source_version.id   (PRIMARY KEY)
⟹ many-to-one NGHIÊM NGẶT; mỗi khoá dòng góp ĐÚNG MỘT bản ghi.
```

Ca `SOURCE_CHANGED` reviewer tự dựng (hai lần chạy, dòng bị SỬA):

```text
version NGUỒN đã lưu = 2 · version KẾT QUẢ đã lưu = 2 · dòng CURRENT = 1
RAW SQL qua con trỏ hiện hành : dòng=1 doanh thu=9000000 LN KT=4000000 LN KPI=4000000
sales_queries.order_detail    : dòng=1 doanh thu=9000000 LN KT=4000000 LN KPI=4000000
  -> version CŨ (8.000.000/3.000.000) có lọt vào không? KHÔNG
  -> chỉ 1 dòng dù có 2 version nguồn ⟹ không double-count: True
```

Bằng chứng CẤU TRÚC bằng AST do reviewer tự chạy trên
`app/web/sales_queries.py`:

```text
import câu GHI (insert/update/delete/text): KHÔNG
gọi begin/commit/execution_options        : KHÔNG
định danh summary_json / source_snapshot  : KHÔNG
đi qua con trỏ hiện hành (3 định danh)    : True
hàng rào PII (tham chiếu cột CẤM)         : KHÔNG
```

⟹ Version cũ, snapshot và `summary_json` **không có đường nào** vào tổng hợp.

### 4. `NO_DOUBLE_COUNT` — recompute bất biến, không chỉ đọc `GROUP BY`

- `Σ(số dòng theo đơn) = 351 = tổng dòng của kỳ` (INV-3) — vi phạm 0.
- `COUNT(DISTINCT order_key) = 254 = số dòng của danh sách đơn` — khớp.
- `auto + review = 254` (INV-4) — phân hoạch đúng, không đơn nào thuộc cả hai.
- `Σ(doanh thu dòng) = doanh thu đơn` và `Σ(SL dòng) = SL đơn` trên **cả 254
  đơn**: vi phạm 0 (INV-1/INV-2) — đơn nhiều dòng aggregate ĐÚNG MỘT LẦN.
- Nạp lại Y HỆT (cùng fingerprint, hai run): `RAW dòng=1 doanh thu=5000000` /
  `IMPL dòng=1 doanh thu=5000000` — **không nhân count, không nhân tiền**.
- Cardinality của join: cả hai FK trỏ vào cột `id` PRIMARY KEY ⟹ không có
  đường nào nhân dòng.

### 5. `LINE_ORDERING_REVIEW`

Fact do implementation nêu — reviewer **xác minh độc lập là ĐÚNG**: cả 4 dòng
của `BH62439` mang `occurrence_index = 1`. Truy `app/history/keys.py`:
*"occurrence_index = 1..n theo source_row tăng dần trong (snapshot, ORDER_KEY,
product_key)"* — nó đếm theo (đơn, **sản phẩm**), nên 4 dòng KHÁC sản phẩm
đều nhận giá trị `1`. `occurrence_index` một mình KHÔNG đủ để sắp thứ tự.

Ngữ nghĩa của khoá phụ `current_source_version_id`:
`app/history/extraction.py:34` — `sorted(presented, key=... .source_row)`
TRƯỚC khi ghi ⟹ id tăng dần theo `source_row`.

Reviewer đối chiếu với **sổ nguồn thật**:

```text
$ đọc read_raw_rows(period_2026_01.xlsx), lọc order_id = BH62439
  source_row=  50  Tủ lạnh Panasonic NR-BX471GPKV
  source_row=  51  Máy Giặt Sấy LG FV1414H3BA
  source_row=  52  Điều hòa Daikin FTHF25XVMV
  source_row=  53  Máy lạnh Daikin Inverter 2 HP FTKB50ZVMV
```

Thứ tự render trên HTML thật TRÙNG KHỚP thứ tự sổ nguồn. ⟹ **Trình bày là
TRUTHFUL**, không phải một thứ tự tuỳ tiện.

Hệ quả nghiệp vụ của ca `SOURCE_CHANGED` (dòng bị sửa nhận version mới nên
tụt xuống cuối đơn): danh tính dòng do `product_raw` mang (luôn hiển thị),
tiền là của TỪNG dòng nên không đổi theo vị trí, lý do gắn vào đúng dòng phụ
của nó. ⟹ **KHÔNG** sai identity, **KHÔNG** sai tiền, **KHÔNG** sai lý do,
**KHÔNG** sai diễn giải nghiệp vụ. Chỉ là ổn định trình bày ⟹
`NON_BLOCKING / DEFER` (FIND-PRA004-08). Reviewer **KHÔNG** đề nghị mở
schema/index để sửa thứ tự.

### 6. `STATUS_SEMANTICS`

- Ràng buộc DB: `CheckConstraint status IN ('AUTO','PENDING')` trên
  `order_line_result_version` ⟹ **không tồn tại trạng thái thứ ba** ở tầng
  dữ liệu.
- Recompute độc lập INV-5 trên toàn fixture: `True` (không ngoại lệ).
- Ca bẫy "lấy trạng thái dòng ĐẦU TIÊN" — reviewer tự dựng đơn có dòng đầu
  `AUTO`, dòng sau `PENDING`:

```text
RAW  has_pending=1 ⟹ CẦN KIỂM TRA
IMPL review=True  nhãn hiển thị = 'CẦN KIỂM TRA'
  -> dòng ĐẦU là AUTO nhưng đơn vẫn CẦN KIỂM TRA: True
```

- `sales_presentation` chỉ định nghĩa đúng hai hằng `STATUS_AUTO = "AUTO"` và
  `STATUS_REVIEW = "CẦN KIỂM TRA"`; không `PARTIAL`/`WARNING`/`RESOLVED`/
  `APPROVED` ở bất kỳ đâu trong hai template mới.

### 7. `KPI_PROFIT_AUTHORITY` / `ACCOUNTING_PROFIT_AUTHORITY`

Truy nguồn trường độc lập trong `tools/db/schema.py`: cả
`eligible_kpi_profit`, `accounting_profit`, `accounting_purchase_price`,
`kpi_purchase_price` đều thuộc `order_line_result_version`, đọc qua
`current_result_version_id`.

```
LN KPI      = SUM(CASE WHEN status='AUTO' THEN eligible_kpi_profit END)
LN kế toán  = SUM(accounting_profit)          (SUM tự bỏ qua NULL)
```

Reviewer đối chiếu từng ký tự với `analytics_queries._metrics()` của PRA-003
(đã accepted, đang chạy production): **giống hệt**. PRA-004 KHÔNG phát minh
số học lợi nhuận mới. Một dòng `PENDING` có `eligible_kpi_profit` khác `NULL`
vẫn KHÔNG vào tổng KPI (mệnh đề `CASE` chặn ở tầng SQL).

Bất biến `UNKNOWN != ZERO` — reviewer dựng đủ bốn ca:

```text
BH_0: RAW acc=    None (0/2)  kpi=    None (0/2)   ← tập authoritative RỖNG
       HIỂN THỊ  LN kế toán='—' coverage='0 / 2 dòng'
       HIỂN THỊ  LN KPI    ='—' coverage='0 / 2 dòng'
BH_1: RAW acc= 1000000 (1/2)  kpi= 1000000 (1/2)   ← coverage MỘT PHẦN
       HIỂN THỊ  LN kế toán='1.000.000' coverage='1 / 2 dòng'
       HIỂN THỊ  LN KPI    ='1.000.000' coverage='1 / 2 dòng'
BH_Z: RAW acc=       0 (2/2)  kpi=       0 (2/2)   ← ZERO THẬT
       HIỂN THỊ  LN kế toán='0' coverage='2 / 2 dòng'
       HIỂN THỊ  LN KPI    ='0' coverage='2 / 2 dòng'
```

⟹ "chưa biết" hiện `—`, "bằng không thật" hiện `0`. Hai tình trạng **KHÔNG**
bị trộn. Trên HTML thật của `BH62439`, ba dòng PENDING render `—` ở cả bốn ô
tiền (xem mục 9) — **không một `0đ`/`0%` nào**. INV-6 GIỮ.

### 8. `COVERAGE`

- Tử số được reviewer đếm ĐỘC LẬP bằng SQL thô, KHÔNG suy từ số tiền hiển
  thị: `kpi_lines = SUM(CASE WHEN status='AUTO' THEN 1 ELSE 0)`,
  `accounting_lines = SUM(CASE WHEN accounting_profit IS NOT NULL THEN 1 ELSE 0)`.
  Trên `BH62439`: `1/4` và `1/4` — khớp Oracle C.
- Ba ca `0/M`, `1/M`, `M/M` đã đo ở mục 7.
- `analytics_presentation.coverage()` viết `N / M dòng`, **cố ý không dùng
  phần trăm** — đúng contract; reviewer xác nhận chuỗi `%` không xuất hiện ở
  ô coverage nào.
- INV-7: mọi ô lợi nhuận đi qua `analytics_presentation.profit()` — hàm này
  LUÔN trả `{"text", "coverage", "missing"}`, và cả hai macro
  `profit_cells` / `profit_kpi` in cả `text` lẫn `coverage` trong **cùng một
  thẻ**. Không có đường nào render lợi nhuận mà rơi mất mẫu số.
- Cảnh báo coverage một phần bật khi
  `min(kpi_lines, accounting_lines) < lines` — trên `BH62439` (1/4) reviewer
  đọc được câu cảnh báo tường minh trên HTML thật.

### 9. `PURCHASE_PRICE_VISIBILITY`

Trên fixture golden hai giá TRÙNG nhau (`10.250.000`), nên một phép tráo sẽ
**không lộ ra**. Reviewer dựng dữ liệu có 4 giá trị PHÂN BIỆT ĐƯỢC:

```text
DB đã lưu: giá vốn KT=1111111 · giá vốn KPI=2222222 · LN KT=3333333 · LN KPI=4444444

Trên HTML THẬT (theo đúng thứ tự cột):
   accounting_purchase_price    = '1.111.111'
   kpi_purchase_price           = '2.222.222'
   accounting_profit            = '3.333.333'
   kpi_profit                   = '4.444.444'
Nhãn cột: ['Sản phẩm','Số lượng','Đơn giá bán','Chiết khấu','Doanh thu dòng',
           'Giá vốn (kế toán)','Giá vốn (KPI)','LN kế toán','LN KPI','Trạng thái']
```

⟹ ánh xạ 1:1, **KHÔNG tráo hai giá**, **KHÔNG gắn sai nhãn**. `price_source`
và `kpi_purchase_provenance` (provenance nội bộ) KHÔNG được đọc và KHÔNG xuất
hiện. `sales_presentation` chỉ `money()` các giá trị ĐÃ LƯU — **không tự tính
lại giá** (không một phép `*`, `-`, `/` nào trên tiền trong module).

### 10. `REASON_CODE_UNIVERSE` / `REASON_MAPPING`

Reviewer **tự dẫn xuất** vũ trụ mã từ chính mã nguồn có thẩm quyền — KHÔNG
lấy số 21 từ test:

```text
(1) PriceResolutionReason  (10): IDENTITY_REQUIRES_CONFIRMATION, IDENTITY_SOURCES_UNAVAILABLE,
    IDENTITY_UNRESOLVED, PUBLIC_PURCHASE_NO_PRICE_AT_SALE_DATE, PUBLIC_PURCHASE_SOURCE_UNAVAILABLE,
    RAW_PRODUCT_IDENTITY_EMPTY, SALE_DATE_MISSING, TRACKING_HISTORY_PENDING,
    TRACKING_HISTORY_SOURCE_UNAVAILABLE, VENDOR_SOURCE_NOT_AUTHORIZED
(2) validation CATEGORIES  (8): Duplicate, EmployeeMapping, Missing, Missing.PurchasePrice,
    OrderInconsistency, SourceClassification, Suspicious, Suspicious.ERP
(3) chuỗi Pending.<field>  (3): Pending.accounting_profit,
    Pending.accounting_purchase_price, Pending.eligible_kpi_profit

=> VŨ TRỤ ĐÓNG reviewer dẫn xuất = 21 mã

O-D1 |vũ trụ| = 21  (contract nói tối đa 21)  -> True
O-D2 REASON_DISPLAY_LABELS phủ TOÀN PHẦN? thiếu=[]  -> True
     key trong bảng nhãn nhưng NGOÀI vũ trụ: []
O-D3 7 nhãn S069 giữ NGUYÊN TỪNG CHỮ? sai={}  -> True
O-D4 nhãn rò rỉ từ vựng nội bộ: {}  -> True
```

Mã thực sự có trong dữ liệu golden và nhãn nghiệp vụ tương ứng:

```text
mã quan sát được trên fixture (6): IDENTITY_SOURCES_UNAVAILABLE, Missing.PurchasePrice,
  Pending.accounting_profit, Pending.accounting_purchase_price,
  Pending.eligible_kpi_profit, Suspicious
nằm TRỌN trong vũ trụ đóng? True     đều CÓ nhãn nghiệp vụ? True
   IDENTITY_SOURCES_UNAVAILABLE  -> 'Chưa có dữ liệu để nhận diện sản phẩm'
   Missing.PurchasePrice         -> 'Thiếu giá mua tham chiếu'
   Pending.accounting_profit     -> 'Thiếu lợi nhuận kế toán'
   Pending.accounting_purchase_price -> 'Thiếu giá nhập kế toán'
   Pending.eligible_kpi_profit   -> 'Thiếu lợi nhuận KPI'
   Suspicious                    -> 'Bất thường'
```

Ca một lý do / nhiều lý do / mã chưa ánh xạ:

```text
reason_labels(['MOT_MA_LA'])            = ['MOT_MA_LA']   ← hiện NGUYÊN VĂN, KHÔNG biến mất
reason_labels(['Suspicious','Missing']) = ['Bất thường', 'Thiếu dữ liệu bắt buộc trên dòng']
_reasons(JSON có mã trùng)              = ['A', 'B']      ← khử trùng lặp, GIỮ thứ tự persist
_reasons('khong-phai-json')             = []              ← không HTTP 500
```

⟹ mã lạ **không biến mất im lặng** (fail-safe đúng contract mục 8.3).

Kiểm ngữ nghĩa từng nhãn mới so với nguồn: `Suspicious.ERP` truy về
`rules.py:259 rule="erp_profit_negative"` ⟹ nhãn *"ERP báo lợi nhuận âm"* là
ĐÚNG nghĩa. Không phát hiện nhãn nào nói SAI nghiệp vụ.

### 11. `REVIEW_REASON_SAFETY`

Cấu trúc thật của `pending_reasons_json`: `app/history/extraction.py:78` ghi
`pending_reasons=tuple(view.reasons)` — **chỉ mảng chuỗi mã**. Reviewer
grep `detail` trong `extraction.py`: **0 kết quả** ⟹ `details`, diagnostics,
`provenance`, stack trace, exception **KHÔNG được persist**, nên UI không thể
lộ chúng. Trên HTML thật của cả hai trang: không `snapshot_id`, không
`run_id`, không version id, không đường dẫn tuyệt đối (mục 12).

Nhãn giải thích được vì sao dòng cần kiểm tra mà không nói sai nghiệp vụ, và
không hứa hành động ("hãy duyệt"/"cần sửa") — đúng ràng buộc CHỈ-ĐỌC.
Không tìm thấy `misleading reason`.

### 12. `PII_VALUE_BASED_REVIEW` — theo GIÁ TRỊ, không chỉ grep tên trường

Reviewer ghi sentinel KHÔNG THỂ trùng ngẫu nhiên vào DB rồi render route
thật. Xác nhận sentinel THẬT SỰ nằm trong dữ liệu đã lưu (nếu không, test vô
nghĩa):

```text
DB.imei           = 'SENTINELIMEI0000123'
DB.note_raw       = 'SENTINELNOTE Nguyen Van Khach 0909123456 so 5 duong X'
DB.employee_raw   = 'SENTINELEMPRAW  Vu  Hanh   Ly '
DB.source_profit  = '987654321'
DB.product_raw    = 'SENTINELPRODUCT Tu lanh Panasonic'
```

Kết quả tìm sentinel trong HTML trả về:

```text
--- /ban-hang  HTTP 200 (4391 bytes) ---
   GIÁ TRỊ sentinel của imei / note_raw / employee_raw / source_profit : KHÔNG (cả 4)
   TÊN TRƯỜNG bị cấm xuất hiện? KHÔNG
   từ vựng nội bộ rò rỉ: KHÔNG        đường dẫn tuyệt đối repo: False
--- /ban-hang/BH62439  HTTP 200 (5810 bytes) ---
   GIÁ TRỊ sentinel của imei / note_raw / employee_raw / source_profit : KHÔNG (cả 4)
   product_raw (ĐƯỢC PHÉP) hiện? True
   từ vựng nội bộ rò rỉ: KHÔNG        đường dẫn tuyệt đối repo: False
--- /ban-hang/BH62063  HTTP 200 (4374 bytes) ---
   (kết quả y hệt)
```

`product_raw` hiện đúng theo contract FROZEN mục 14.2/14.4 (được phép, và
là trường DUY NHẤT phân biệt được các dòng vì `canonical_product_code` rỗng
0/351).

Ranh giới PRA-003 **KHÔNG bị làm yếu**: `app/web/analytics_queries.py` và
`tests/test_analytics_queries.py` **không nằm trong diff**;
`test_the_query_module_never_selects_a_personal_data_column` và
`test_the_query_module_never_writes_and_never_reads_a_run_summary` chạy lại
**PASS mà không bị sửa** (`2 passed, 20 deselected`).

Cấu trúc: grep `customer|phone|address|shipper|warranty` trên
`tools/db/schema.py` = **0 kết quả** ⟹ các trường đó không tồn tại như cột,
không thể rò rỉ.

Mã HTTP: `/ban-hang/KHONG-CO-DON → 404`; không có kho dữ liệu →
`/ban-hang → 503` và `/ban-hang/BH1 → 503` (không phải "chưa có dữ liệu",
không phải trang rỗng).

### 13. `EMPLOYEE_MODEL`

```text
BH_M: RAW DISTINCT=['Nguyen A','Tran B']  HIỂN THỊ='Nguyen A · Tran B'  multi=True
BH_N: RAW DISTINCT=[None]                 HIỂN THỊ='Chưa xác định nhân viên'  multi=False
BH_E: RAW DISTINCT=['']                   HIỂN THỊ='Chưa xác định nhân viên'  multi=False
```

Đơn nhiều nhân viên hiện **TẤT CẢ** tên và kèm câu
*"Đơn này có nhiều nhân viên trên các dòng. Reports KHÔNG tự chọn chủ đơn."*
⟹ KHÔNG chọn tuỳ tiện nhân viên dòng đầu, KHÔNG phát minh ownership.
`NULL` và chuỗi rỗng gộp thành CÙNG một tình trạng ở tầng SQL, đúng như
PRA-003.

### 14. `PERIOD_RECONCILIATION`

Reviewer so ba chiều — SQL THÔ, `analytics_queries.period_totals()` (Tổng
quan), và tầng truy vấn của `/ban-hang`:

```text
--- Toàn bộ dữ liệu ---
  tổng dòng          RAW=         351 · Tổng quan=         351 · Bán hàng=         351  OK
  tổng đơn           RAW=         254 · Tổng quan=         254 · Bán hàng=         254  OK
  tổng số lượng      RAW=         407 · Tổng quan=         407 · Bán hàng=         407  OK
  doanh thu net      RAW=  3562310000 · Tổng quan=  3562310000 · Bán hàng=  3562310000  OK
  LN KPI             RAW=      900000 · Tổng quan=      900000 · Bán hàng=      900000  OK
  coverage KPI       RAW=           2 · Tổng quan=           2 · Bán hàng=           2  OK
  LN kế toán         RAW=     1000000 · Tổng quan=     1000000 · Bán hàng=     1000000  OK
  coverage kế toán   RAW=           2 · Tổng quan=           2 · Bán hàng=           2  OK
  đơn AUTO/Review    Tổng quan=1/253 · Bán hàng=1/253 · phân hoạch=254==254  OK
  KẾT LUẬN kỳ này: KHỚP HOÀN TOÀN

--- Tháng 01/2026 --- (tháng CÓ dữ liệu)
  (cả 9 hàng OK — KẾT LUẬN: KHỚP HOÀN TOÀN)

--- Tháng 02/2026 --- (tháng KHÔNG có dữ liệu)
  Tổng quan và Bán hàng KHỚP nhau tuyệt đối (0 dòng / 0 đơn / tiền = None /
  tử số coverage = 0 / 0 đơn AUTO / 0 đơn Review).
```

Ghi chú trung thực về ca tháng rỗng: hai hàng tử số coverage lệch giữa cột
`RAW` và hai cột kia là **hiện vật của chính script reviewer** (`SUM` trên
tập rỗng trả `NULL`, trong khi cả PRA-003 lẫn PRA-004 dùng chung
`int(... or 0)` để ép tử số ĐẾM về `0`). Đây **KHÔNG** phải lệch giữa Tổng
quan và Bán hàng — hai trang cho cùng một kết quả. Không phải finding.

`_period()` của PRA-004 so từng dòng với `_period()` của PRA-003: giống hệt,
kể cả `sale_date IS NOT NULL` trong MỌI kỳ. Cùng `ky`, cùng
`available_periods()`/`month_bounds()`/`period_options()`. `?ky` rác →
HTTP 200 rơi về "Toàn bộ dữ liệu" (không 500, không bảng số 0 cho tháng
bịa). **Không thêm loại kỳ mới.**

### 15. `LEGACY_SEPARATION`

```text
order_line_current           ck_order_line_current_origin     origin = 'PIPELINE_GENERATED'
order_line_source_version    ck_source_version_origin         origin = 'PIPELINE_GENERATED'
order_line_result_version    ck_result_version_origin         origin = 'PIPELINE_GENERATED'
```

⟹ `LEGACY_REFERENCE` **KHÔNG THỂ** tồn tại trong ba bảng PRA-004 đọc — tách
nguồn là ràng buộc DB, không phải bộ lọc phải nhớ viết. Không có drill-down
legacy nào được dựng. Mọi số trên hai trang mới mang badge `SỐ MỚI`.

### 16. `READ_ONLY_PROOF`

Bằng chứng CẤU TRÚC (AST) ở mục 3, cộng bằng chứng **CHẠY THẬT** — chụp hash
toàn bộ 4 bảng trước và sau 7 lượt GET:

```text
   GET /ban-hang                     -> 200      GET /ban-hang/BH62439        -> 200
   GET /ban-hang?ky=2026-01          -> 200      GET /ban-hang/BH62063        -> 200
   GET /ban-hang?ky=tat-ca           -> 200      GET /ban-hang/BH62439?ky=... -> 200
   GET /ban-hang?ky=rac-khong-hop-le -> 200

   DB thay đổi sau 7 lần GET? KHÔNG — không một byte nào đổi
     order_line_current        rows 351 -> 351  hash 64943b82676289f7 -> 64943b82676289f7
     order_line_source_version rows 351 -> 351  hash 3b63d82ab7f6ee3b -> 3b63d82ab7f6ee3b
     order_line_result_version rows 351 -> 351  hash a110680a7e3fe1bd -> a110680a7e3fe1bd
     source_snapshot           rows   1 -> 1    hash fa838b77edb52b01 -> fa838b77edb52b01
   Route GHI trên hai path này? KHÔNG — chỉ GET
```

Không `INSERT`/`UPDATE`/`DELETE`, không commit business mutation, không ghi
Tracking, không ghi Review state. `@app.get` cho cả hai route.

### 17. `UI_REVIEW` — HTML thật Owner nhìn thấy (`/ban-hang/BH62439`)

```text
ĐƠN BH62439 · SỐ MỚI · Số do Reports tính từ sổ kế toán đã nạp.
← Danh sách đơn · Toàn bộ dữ liệu
Tổng hợp đơn SỐ MỚI [CẦN KIỂM TRA]
Ngày bán 08/01/2026 · Nhân viên Tín Phát · Dòng hàng 4 · Tổng số lượng 5
Doanh thu (net) 66.000.000 đồng
Lợi nhuận KPI 400.000        1 / 4 dòng
Lợi nhuận kế toán 500.000    1 / 4 dòng
"Lợi nhuận của đơn này chỉ tổng hợp các dòng ĐÃ có giá trị — nó KHÔNG phải
 lợi nhuận của toàn đơn. Các dòng còn lại chưa đủ căn cứ nên để trống, và
 ô trống nghĩa là chưa biết, không phải bằng không."

Các dòng của đơn · 4 dòng
Sản phẩm | Số lượng | Đơn giá bán | Chiết khấu | Doanh thu dòng |
Giá vốn (kế toán) | Giá vốn (KPI) | LN kế toán | LN KPI | Trạng thái
Tủ lạnh Panasonic NR-BX471GPKV  1  14.150.000  50.000  14.100.000  —  —  —  —  CẦN KIỂM TRA
  Lý do cần kiểm tra: Chưa có dữ liệu để nhận diện sản phẩm · Thiếu giá mua
  tham chiếu · Thiếu giá nhập kế toán · Thiếu lợi nhuận kế toán · Thiếu lợi nhuận KPI
Máy Giặt Sấy LG FV1414H3BA      1  14.800.000  50.000  14.750.000  —  —  —  —  CẦN KIỂM TRA
  Lý do cần kiểm tra: (5 lý do như trên)
Điều hòa Daikin FTHF25XVMV      2  10.500.000 100.000  20.900.000  10.250.000 10.250.000 500.000 400.000  AUTO
Máy lạnh Daikin ... FTKB50ZVMV  1  16.300.000  50.000  16.250.000  —  —  —  —  CẦN KIỂM TRA
```

Kiểm tối thiểu: đơn hiểu được ✓ · trạng thái thấy được ✓ · coverage lợi
nhuận thấy được ✓ · dòng hàng thấy được ✓ · lý do thấy được ✓ · không ô
trống/`0` gây hiểu nhầm ✓ · điều hướng hoạt động (tab "Bán hàng" →
danh sách → chi tiết → quay lại, `ky` được giữ qua link) ✓.
Reviewer KHÔNG thiết kế lại styling. Không có phát hiện UX nào cản trở diễn
giải nghiệp vụ.

### 18. `PERFORMANCE` — reviewer tự đo

```text
dựng dữ liệu: 12000 dòng / 4000 đơn
RAW SQL xác nhận: 12000 dòng hiện hành / 4000 đơn
sales_queries.order_list('Toàn bộ dữ liệu') = 78.1 ms (tốt nhất/3), trả 4000 đơn
GET /ban-hang (render CẢ trang 4000 đơn)    = 433 ms · HTTP 200 · 3745 KB
Ngưỡng RE-TRIGGER của contract = 3000 ms ⟹ DƯỚI ngưỡng
```

Số đo của reviewer (**78,1 ms**) tái lập cùng bậc độ lớn với số
implementation báo (85,2 ms); reviewer KHÔNG đòi trùng khít. Thiết kế
không-pagination hiện tại **vẫn dùng được** cho kịch bản ≥12k dòng đã đóng
băng (production 09/2026 chỉ 40 đơn) ⟹ `PASS`. Reviewer **KHÔNG** thêm
pagination. Trọng lượng trang 3,7 MB ở mốc 4.000 đơn được ghi làm quan sát
`DEFER` (FIND-PRA004-07), KHÔNG phải blocker.

### 19. `CHANGE_BUDGET` — reviewer đo lại

```text
PYTHON PRODUCTION (dòng MÃ thêm; bỏ trống/comment/docstring)
   app/web/sales_queries.py              128
   app/web/sales_presentation.py          52
   app/web/server.py                      32
   app/beta_presentation.py               14
   TỔNG                                  226   (MỤC TIÊU 266 · MỀM 330 · DỪNG CỨNG 400)
   -> vượt DỪNG CỨNG? KHÔNG   vượt CẢNH BÁO MỀM? KHÔNG

TEMPLATE   132   (TRẦN 220) -> vượt? KHÔNG
CSS         13   (TRẦN  25) -> vượt? KHÔNG   (0 dòng bị XOÁ — chỉ THÊM)
TEST        85 test mới (SÀN 30) -> đạt? CÓ
_pipeline_bits.html: 15 thêm / 0 xoá  ⟹ KHÔNG sửa macro cũ
```

Số của reviewer (Python 226) thấp hơn số implementation báo (282) do quy ước
loại docstring chặt hơn. **Cả hai đều dưới mọi biên**, nên theo mục 23 chỉ
thị reviewer **KHÔNG thổi phồng thành finding**.

Scope Lock — 18 file bị chạm so với `BASE_SHA`; đối chiếu với danh sách CẤM
của contract mục 18:

```text
FILE TRONG DANH SÁCH CẤM bị chạm: KHÔNG — 0 file
```

Không file nào thuộc `tools/db/**`, `app/history/**`, `app/modules/**`,
`tests/fixtures/golden/**`, `config/**`, `analytics_*`, ba file test PRA-003,
`alembic.ini`, `render.yaml`, `Dockerfile`, `pyproject.toml`.

```text
SCHEMA_CHANGE = 0 · MIGRATION = 0 · INDEX = 0 · DEPENDENCY = 0 · CONFIG = 0
TRACKING_CHANGED = NO · INFRASTRUCTURE_CHANGED = NO · PROTECTED_CORE_IMPACT = NONE
$ git diff --check 8181ceb 6a23c32   → SẠCH (0 lỗi whitespace, kiểm trên DẢI COMMIT)
```

### 20. `TESTS` / `GOLDEN`

Môi trường: clone ban đầu là **shallow** và thiếu dependency. Reviewer
`git fetch --unshallow` (258 commit) và `pip install -e ".[dev,web,storage]"`
trước khi chạy — theo mục 27 chỉ thị, đây là điều kiện môi trường, **không
phải defect sản phẩm**.

```text
Focused PRA-004      : 89 passed in 7.49s
PRA-003 regression   : 67 passed in 7.07s   (3 file test KHÔNG nằm trong diff)
gate PII của PRA-003 : 2 passed, 20 deselected  (PASS mà KHÔNG bị sửa)
legacy routes PRA-001: 82 passed in 4.56s
PRA-002 persistence  : 32 passed in 0.95s
GOLDEN BASELINE      : 58 passed, 2 skipped in 6.31s   ← khớp ĐÚNG con số đóng băng
FULL SUITE (6a23c32) : 1962 passed, 11 skipped in 78.60s
FULL SUITE (8181ceb) : 1873 passed, 11 skipped in 74.27s   (đo bằng git worktree)
                       → chênh +89 = ĐÚNG số test mới; số skip KHÔNG đổi
```

Theo mục 27 chỉ thị, test PASS **một mình không phải** bằng chứng review cho
các khẳng định trọng yếu về tiền/trạng thái/PII — vì vậy toàn bộ mục 1–13 ở
trên đều dựa trên recompute thô của reviewer.

### 21. `VALIDATORS`

```text
validate_structure        : GOVERNANCE STRUCTURE: PASS (21 required paths)
validate_project_state    : PROJECT STATE: PASS
validate_evidence         : EVIDENCE VALIDATION: PASS (139 REQUIRED PASS record)
validate_task_completion  : TASK COMPLETION: PASS (11 DONE task)
validate_reference_integrity : FAIL — ĐÚNG 3 issue pre-existing của REM-T06:
    docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> /README.md
    docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> CODE_OF_CONDUCT.md
    docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> CONTRIBUTING.md
  → KHÔNG issue reference mới.
branch_authority_check.sh : AUTHORITY_OK · DIVERGENCE = WITHIN_LIMITS
                            (behind default 0 · ahead default 2)
git diff --check          : SẠCH trên dải commit
```

## Sai Lệch So Với Tuyên Bố Của Người Triển Khai (Mismatches With Implementer Claims)

Không có sai lệch trọng yếu về TIỀN / SỐ ĐẾM / TRẠNG THÁI / PII.

**Một khiếm khuyết tài liệu implementation KHÔNG báo cáo** — reviewer phát
hiện độc lập: văn bản yêu cầu của `CHECK-PRA004-12` và `CHECK-PRA004-13` bị
đặt nhầm khối, và `CHECK-PRA004-12` mang `Executed By: Session S101` trong
khi S101 không thực thi review độc lập. Chi tiết và đề xuất sửa ở
`FIND-PRA004-09`. Không BLOCKING (không đường production, không hệ quả
nghiệp vụ, bản FROZEN `46a5cdb` nguyên vẹn), nhưng phải sửa trong cùng lần
docs reconciliation.

Ba khác biệt về SỐ ĐO, đều đã giải thích và không đổi kết luận nào:

| Hạng mục | Implementation báo | Reviewer đo lại | Đánh giá |
|---|---|---|---|
| Python production | +282 | 226 | Khác quy ước loại docstring; **cả hai dưới mọi biên** ⟹ không finding |
| Template / CSS / test | 126 / 10 / 89 | 132 / 13 / 85 | Khác cách đếm dòng thêm và cách đếm hàm `test_`; đều trong ngưỡng |
| `CHECK-PRA004-13` | 85,2 ms | 78,1 ms | Cùng bậc độ lớn; contract KHÔNG đòi trùng khít |

Mọi khẳng định về TIỀN, SỐ ĐẾM, TRẠNG THÁI, COVERAGE, LÝ DO và PII của
implementation đều được reviewer tái lập độc lập và **khớp**.

## Findings

### BLOCKING — **0 (KHÔNG CÓ)**

Không finding nào hội đủ ĐỒNG THỜI ba điều kiện của mục 25 chỉ thị (đường
production + hệ quả nghiệp vụ + vi phạm frozen contract).

### FIND-PRA004-04 — `DOC_INCONSISTENCY` · KHÔNG BLOCKING · reviewer XÁC NHẬN phân loại A

Reviewer **tự đếm** các check trong bản FROZEN (`46a5cdb`), không lấy số từ
báo cáo implementation:

```text
Header Completion Gate (FROZEN) viết : "13 check: 11 REQUIRED · 2 RECOMMENDED"
Đếm thật trong chính bản FROZEN      : 14 check — 13 REQUIRED · 1 RECOMMENDED
Exit Criteria số 1 (FROZEN) viết     : "11/11 REQUIRED"
```

**Quyết định phân loại: A. `DOC_INCONSISTENCY`, KHÔNG phải
`CONTRACT_SEMANTIC_CHANGE`.** Căn cứ, theo đúng key rule mục 24 chỉ thị:

1. Cả 14 check **đã tồn tại đầy đủ trong bản FROZEN tại `46a5cdb`** — sai số
   học nằm ở CHÍNH artifact đóng băng, không do implementation tạo ra.
2. `diff` 14 dòng `Yêu cầu:` giữa `46a5cdb` và `6a23c32`: **IDENTICAL**.
3. Đếm `Priority:` hai bản: **13 REQUIRED · 1 RECOMMENDED ở CẢ HAI** — không
   một phân loại yêu cầu nào bị đổi.
4. Không check nào bị xoá, bị hạ cấp, hay bị làm yếu.

⟹ Chỉ có con số TÓM TẮT ở header và Exit Criteria là sai; không cần đổi phân
loại của bất kỳ requirement nào ⟹ theo key rule, **không được** xếp là thay
đổi contract chỉ vì header sai số học.

**Đề xuất reconciliation chính xác (KHÔNG áp dụng trong phiên review này):**

```text
docs/tasks/TASK-PRA-004-ban-hang-review-detail.md
  dòng 1148:  "13 check: **11 REQUIRED** · 2 RECOMMENDED."
           →  "14 check: **13 REQUIRED** · 1 RECOMMENDED."
  dòng 1669:  "1. 11/11 REQUIRED check PASS với evidence level bắt buộc được thoả."
           →  "1. 13/13 REQUIRED check PASS với evidence level bắt buộc được thoả."
```

Reviewer **KHÔNG** sửa frozen contract trong phiên review (governance chỉ cho
phép review artifact). Đường sạch được ưu tiên: ghi finding →
`ACCEPT_WITH_NON_BLOCKING_FINDINGS` → **một** lần docs reconciliation trong
khâu chuẩn bị Controlled Integration. Việc này **KHÔNG tiêu repair cycle**
(mục 26 chỉ thị: dọn số học tài liệu không đổi frozen semantics).

Implementation đã ghi nhận finding này đúng cách (`S101` mục
`FIND-PRA004-04`, `PROJECT_PROGRESS` dòng 103–107) và **không tự ý sửa** —
reviewer xác nhận đó là xử lý đúng.

### FIND-PRA004-05 — `HARDENING` · KHÔNG BLOCKING · DEFER (reviewer PHÁT HIỆN MỚI)

`app/web/sales_queries.py::_line()` có docstring
*"Dòng đem ra trình bày: mã lý do đã giải mã, KHÔNG kèm chuỗi JSON thô."*
Nhưng biểu thức `{**row, "reasons": _reasons(row.pop("pending_reasons_json"))}`
mở gói `**row` **TRƯỚC** khi `row.pop()` chạy, nên dict trả về **VẪN CHỨA**
khoá `pending_reasons_json`:

```text
_line() keys: ['pending_reasons_json', 'product_raw', 'quantity', 'reasons']
pending_reasons_json còn trong dict trả về? True   giá trị: ["Suspicious"]
```

**Hệ quả nghiệp vụ trên đường PRA-004 hiện tại: KHÔNG CÓ.**
`sales_presentation.line_row()` dựng dict **whitelist tường minh** (12 khoá,
không có `pending_reasons_json`), nên chuỗi thô **không tới template**:

```text
line_row() keys: ['accounting_profit','accounting_purchase_price','discount','kpi_profit',
 'kpi_purchase_price','product','quantity','reasons','review','sell_price','status','total_sales']
pending_reasons_json rò ra template? False
```

Và bản thân chuỗi đó chỉ chứa mã nghiệp vụ (không `details`, không
diagnostics — mục 11), nên kể cả nếu render cũng không phải PII. Quét theo
giá trị trên HTML thật của cả hai trang: không xuất hiện.

⟹ Đây là **docstring nói sai về hành vi thật**, không phải defect tiền/trạng
thái/PII. Không thuộc năm nhóm mở repair cycle của contract mục 24.

**RE-TRIGGER CONDITION tường minh:** kích hoạt lại NGAY nếu (a) một template
hoặc route bất kỳ lặp qua dict thô của tầng truy vấn thay vì đi qua
`sales_presentation.line_row()`; HOẶC (b) `pending_reasons_json` về sau mang
thêm `details`/diagnostics/provenance. Khi đó phải sửa thành
`row.pop(...)` trước khi mở gói (hoặc whitelist ở chính `_line`), và
docstring phải khớp hành vi.

### FIND-PRA004-06 — `TRUTHFULNESS_CONSTRAINT` (kế thừa PRA-003) · KHÔNG BLOCKING · DEFER

Tử số coverage KPI đếm **dòng `AUTO`**, không đếm dòng **CÓ giá trị**. Trên
một dòng `AUTO` mà `eligible_kpi_profit IS NULL` (ca lý thuyết), màn hình
hiện:

```text
HIỂN THỊ LN KPI     = '—'  coverage='1 / 1 dòng'
HIỂN THỊ LN kế toán = '—'  coverage='0 / 1 dòng'
Tổng quan (PRA-003) cùng dữ liệu: kpi_lines=1  accounting_lines=0
-> Bán hàng khớp Tổng quan: True
```

Tiền vẫn hiện `—` chứ **không bao giờ** `0` ⟹ INV-6 GIỮ. Ngữ nghĩa này được
**TÁI DỤNG NGUYÊN VẸN** từ `analytics_queries._metrics()` của PRA-003 (đã
accepted, đang chạy production); đổi tử số ở PRA-004 sẽ **LÀM VỠ** đối chiếu
`CHECK-PRA004-07`. Ca này **không xuất hiện** trên fixture golden (2/2 dòng
AUTO đều có đủ hai lợi nhuận) và thuộc lineage PRA-003, **không phải**
defect của PRA-004.

**RE-TRIGGER CONDITION:** kích hoạt khi quan sát được trên dữ liệu
production một dòng `status = 'AUTO'` có `eligible_kpi_profit IS NULL`; khi
đó câu hỏi "tử số coverage KPI nên đếm gì" phải được mở như một quyết định
RIÊNG ở cấp PRA-003 lineage, không vá ở tầng trình bày PRA-004.

### FIND-PRA004-07 — `HARDENING` · KHÔNG BLOCKING · DEFER

`/ban-hang` không phân trang: ở mốc 4.000 đơn trang HTML nặng **3,7 MB**
(dựng danh sách 78,1 ms, render tổng 433 ms). Vẫn **dưới** ngưỡng RE-TRIGGER
3 giây đã đóng băng, và production 09/2026 chỉ 40 đơn. Contract mục 17/22
cấm tự thêm pagination ⟹ reviewer **KHÔNG** thêm.

**RE-TRIGGER CONDITION:** kích hoạt khi số đo dựng danh sách > 3 giây (theo
đúng `CHECK-PRA004-13`), HOẶC khi Owner báo trang tải chậm trên thiết bị
thật ở tập dữ liệu production thực tế.

### FIND-PRA004-08 — `HARDENING` · KHÔNG BLOCKING · DEFER

Ổn định thứ tự dòng khi có `SOURCE_CHANGED`: dòng bị SỬA nhận
`current_source_version_id` mới nên chuyển xuống cuối đơn, không còn trùng vị
trí trong sổ gốc. Đã chứng minh ở mục 5 là **không** gây sai identity dòng,
sai tiền, sai lý do hay sai diễn giải nghiệp vụ ⟹ thuần ổn định trình bày.

**RE-TRIGGER CONDITION:** kích hoạt khi Owner cần đối chiếu TỪNG DÒNG theo
đúng số dòng của sổ nguồn sau một lần sửa (khi đó cần đưa `source_row` vào
mô hình đọc — một quyết định RIÊNG, KHÔNG mở schema/index chỉ để sửa thứ tự).

### FIND-PRA004-09 — `DOC_INCONSISTENCY` · KHÔNG BLOCKING · reviewer PHÁT HIỆN MỚI

Trong bản hiện tại của file task, **văn bản yêu cầu của `CHECK-PRA004-12` và
`CHECK-PRA004-13` bị đặt nhầm chỗ**.

Quy ước ghi bằng chứng của S101 (thấy rõ ở CHECK-01 … CHECK-11) là:

```
Evidence:
Yêu cầu: <nguyên văn yêu cầu ĐÃ ĐÓNG BĂNG>
Executed By: …
Timestamp: …
Kết quả S101: <bằng chứng thực thi>
```

Riêng khối `CHECK-PRA004-12` (dòng 1589–1610) lệch khỏi quy ước đó:

```text
#### CHECK-PRA004-12 — Independent Review E2
Evidence:
Yêu cầu: đo thời gian dựng danh sách đơn …          ← đây là yêu cầu của CHECK-13
Executed By:
Session S101 — PRA-004 MAJOR Implementation          ← S101 KHÔNG thực thi review độc lập
Timestamp: 2026-09-03
Kết quả S101:
Yêu cầu: reviewer ĐỘC LẬP theo E2_INDEPENDENT_REVIEW_TEMPLATE.md …
                                                     ← đây MỚI là yêu cầu của CHECK-12,
                                                       nhưng nằm dưới nhãn "Kết quả"
```

Đồng thời khối `CHECK-PRA004-13` không còn giữ dòng `Yêu cầu:` của chính nó —
ô `Evidence:` của nó đã bị thay bằng bằng chứng PASS.

**Vì sao đây là `DOC_INCONSISTENCY` chứ không phải
`CONTRACT_SEMANTIC_CHANGE`:**

1. **Không một dòng yêu cầu nào bị xoá khỏi tài liệu** — reviewer đã chứng
   minh ở đầu phiên rằng tập 14 dòng `Yêu cầu:` của bản hiện tại **IDENTICAL**
   với bản FROZEN. Hai dòng chỉ bị **đổi chỗ**, không bị sửa chữ.
2. Không `Priority:` nào đổi (13 REQUIRED · 1 RECOMMENDED ở cả hai bản),
   không `Evidence Level:` nào đổi, không check nào bị xoá hay hạ cấp.
3. **Thẩm quyền vẫn là bản FROZEN `46a5cdb`**, và bản đó KHÔNG bị đụng tới.
   Reviewer đã thực thi ĐÚNG yêu cầu CHECK-12 đọc từ `46a5cdb` — (a) verify
   ba SHA ✓ (b) khẳng định contract không bị nới lỏng ✓ (c) recompute độc lập
   bằng SQL thô cho danh sách đơn và BH62439 ✓ (d) chạy lại suite +
   validators ✓ (e) đo lại change budget ✓ — **không** theo văn bản bị đặt
   nhầm trong tài liệu.
4. `CHECK-PRA004-12` vẫn đang ở `NOT_TESTED` tại thời điểm phát hiện, nên
   **chưa có check nào được đóng trên cơ sở sai**.

**Vì sao vẫn phải ghi lại nghiêm túc:** khác với sai số học ở
`FIND-PRA004-04`, chỗ này chạm vào **văn bản của gate**. Một người đọc sau
này chỉ đọc tài liệu có thể tưởng "Independent Review E2" chỉ đòi một phép đo
hiệu năng. Đó là lý do nó phải được sửa trong **CÙNG** một lần docs
reconciliation, không được để trôi.

**Đề xuất reconciliation chính xác (KHÔNG áp dụng trong phiên review này):**

```text
docs/tasks/TASK-PRA-004-ban-hang-review-detail.md
  CHECK-PRA004-12 · ô "Evidence:"      → trả lại nguyên văn "Yêu cầu:" của
                                          CHECK-12 (bản 46a5cdb)
  CHECK-PRA004-12 · ô "Kết quả S101:"  → thay bằng "Kết quả S102:" + bằng
                                          chứng Independent Review E2 (hồ sơ này)
  CHECK-PRA004-12 · "Executed By:"     → S102 — Independent Review E2,
                                          KHÔNG phải S101
  CHECK-PRA004-13 · ô "Evidence:"      → khôi phục dòng "Yêu cầu:" đã đóng
                                          băng, giữ bằng chứng PASS ở ô
                                          "Kết quả S101:" theo đúng quy ước
```

Reviewer **KHÔNG** tự sửa trong phiên này (governance chỉ cho phép review
artifact). Gộp chung vào một lần reconciliation với `FIND-PRA004-04`.
**KHÔNG tiêu repair cycle** — không đổi frozen semantics, không đổi phân loại
requirement nào, và bản FROZEN `46a5cdb` vẫn nguyên vẹn.

### Findings của contract giữ nguyên trạng thái

`FIND-PRA004-01` (`TRUTHFULNESS_CONSTRAINT`, đã đưa vào thiết kế — trang
không in công thức): reviewer xác nhận trang chỉ đặt số ĐÃ LƯU cạnh nhau.
`FIND-PRA004-02` (đã giải quyết bằng thiết kế), `FIND-PRA004-03`
(`HARDENING`, DEFER): không đổi. `FIND-PRA003-03` giữ DEFER — `employee_group`
không nằm trên đường production của slice này.

## Kết Luận (Conclusion)

**E2 PASS.**

```
CHECK-PRA004-12 — Independent Review E2   = PASS   (Evidence Level E2)
CHECK-PRA004-14 — Owner Production Acceptance = NOT_TESTED (KHÔNG đụng tới)

FINAL_DECISION      = ACCEPT_WITH_NON_BLOCKING_FINDINGS
BLOCKING_FINDINGS   = 0
NON_BLOCKING        = 6 (FIND-PRA004-04 xác nhận · 05 · 06 · 07 · 08 · 09 mới)
REVIEW_BUDGET       : repair_cycles_allowed = 1 · used = 0 · remaining = 1
                      (KHÔNG tiêu cycle nào — không có defect blocking)
TASK_PRA004         = IN_PROGRESS
```

Trả lời câu hỏi chính của mục 3 chỉ thị — PRA-004 **CÓ** cho phép đi
Tổng quan → Bán hàng → Đơn → Dòng → AUTO/CẦN KIỂM TRA → lý do, một cách:
truthful ✓ · chỉ trạng thái hiện hành ✓ · không double-count ✓ · không sai
tiền ✓ · không biến `NULL` thành `0` ✓ · không lộ PII ✓ · không phát minh
business semantics ✓.

## Việc Cần Theo Dõi Tiếp (Required Follow-up)

1. **Controlled Integration** — trong khâu chuẩn bị, thực hiện **một** lần
   docs reconciliation gộp CẢ HAI finding tài liệu, theo đúng các dòng đề
   xuất ở trên:
   - `FIND-PRA004-04`: header Completion Gate (dòng 1148) + Exit Criteria số
     1 (dòng 1669);
   - `FIND-PRA004-09`: trả văn bản `Yêu cầu:` của `CHECK-PRA004-12` và
     `CHECK-PRA004-13` về đúng khối của chúng, và sửa `Executed By:` của
     CHECK-12 thành phiên review độc lập.
   Không tiêu repair cycle.
2. Deploy.
3. **Owner Production Acceptance Tháng 09/2026** (`CHECK-PRA004-14`) — Owner
   tự thực hiện trọn vẹn 8 bước của contract mục 21 trên production thật;
   bốn con số 40 / 15 / 25 / 61 phải khớp ĐÚNG. Reviewer **KHÔNG** suy dẫn và
   **KHÔNG** đánh dấu check này.
4. Bốn `RE-TRIGGER CONDITION` của FIND-PRA004-05/06/07/08 giữ ở trạng thái
   DEFER, theo dõi theo đúng điều kiện đã ghi.
5. Ba issue `reference_integrity` của REM-T06 vẫn pre-existing — PRA-004
   không repair và không làm tăng.
