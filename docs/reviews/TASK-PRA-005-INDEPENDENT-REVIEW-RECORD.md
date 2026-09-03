# RÀ SOÁT ĐỘC LẬP E2 (E2 INDEPENDENT REVIEW) — TASK-PRA-005 V1 IMPLEMENTATION

Review ID:
PRA-005-V1-IMPLEMENTATION-REVIEW-1

Task / Release:
TASK-PRA-005 — Sản phẩm (Mặt hàng trên chứng từ) — Aggregation View
(CHỈ-ĐỌC), đối chiếu với Contract + Completion Gate FROZEN tại S107.

Reviewer Session:
S109 — Independent Review E2 (rà soát trên nhánh
`claude/pra-005-v1-implementation-3dcd5k`)

Executed By:
S109 — TASK-PRA-005 Independent Review E2 (Claude Code)

Timestamp:
2026-09-03

Evidence Level:
E2 — reviewer TỰ RECOMPUTE toàn bộ phép gộp mặt hàng bằng **SQL THÔ**
(`sqlalchemy.text()`) chạy thẳng trên các bảng đã persist, **KHÔNG** gọi
`sales_queries.product_totals()` để dựng oracle; chỉ SAU KHI có kết quả thô
mới đem so với module đang review. DB test state dựng bằng ĐƯỜNG PRODUCTION
(`tests/test_sales_queries.py::load_golden` trên `period_2026_01.xlsx`).
Khoá gộp được re-derive độc lập bằng `app.history.keys.product_key` rồi so
với khoá đã persist trên CẢ 226 nhóm. Phần đọc mã tĩnh (AST, hình dạng SQL
phát sinh, hàng rào PII) được ghi rõ là suy luận tĩnh có dẫn nguồn.

## Scope

Independent Review E2 để quyết định `CHECK-PRA005-14`. KHÔNG implementation
mới, KHÔNG repair (không cần), KHÔNG Owner Production Acceptance
(`CHECK-PRA005-15` giữ `NOT_TESTED`), KHÔNG integrate canonical, KHÔNG
deploy, KHÔNG migration/schema/index, KHÔNG chạm Tracking, KHÔNG REM-T06.

### Authority — xác minh TRƯỚC khi đọc bất kỳ file governance nào

```
Nhánh mặc định thật trên origin : claude/extract-upload-repo-gq2ws4
CANONICAL (kỳ vọng / thực tế)   : 4e06515895814d8fff41580dc0f3c64da464ac83  ✓ KHỚP
CANDIDATE viết tắt (báo cáo)    : 18ab5d3
CANDIDATE FULL SHA (từ origin)  : 18ab5d39a15b224d34aa04e5c6bbe8261f60efeb
CANONICAL_MOVED                 : KHÔNG
WORKING TREE tại lúc mở phiên   : SẠCH
```

Tổ tiên (ancestry) — tuyến tính, một commit, không merge, không rebase:

```
$ git merge-base --is-ancestor 4e06515 18ab5d3   → CANONICAL IS ANCESTOR: YES
$ git rev-list --left-right --count 4e06515...18ab5d3
0	1                                    (0 behind · 1 ahead)
$ git rev-list --parents -n 1 18ab5d39a15b224d34aa04e5c6bbe8261f60efeb
18ab5d39a15b224d34aa04e5c6bbe8261f60efeb 4e06515895814d8fff41580dc0f3c64da464ac83
$ git log --oneline 4e06515..18ab5d3
18ab5d3 S108 — TASK-PRA-005 MAJOR Implementation: trang Sản phẩm (Mặt hàng trên chứng từ)
```

Candidate là con TRỰC TIẾP của canonical. `CANDIDATE_ANCESTRY_MISMATCH` =
KHÔNG.

`scripts/branch_authority_check.sh` → `RESULT: AUTHORITY_OK`,
`DIVERGENCE: WITHIN_LIMITS`, `WORKTREE: CLEAN`.

## (1) Diff chính xác — xác minh độc lập

13 file, khớp con số S108 báo cáo:

```
 PROJECT/LO_TRINH_DE_HIEU.md                        |  20 +-
 PROJECT/PROJECT_PROGRESS.md                        | 115 ++++++-
 PROJECT/REVIEW_BUDGET_LEDGER.md                    |  27 +-
 app/web/sales_presentation.py                      |  61 +++-
 app/web/sales_queries.py                           |  67 +++-
 app/web/server.py                                  |  26 +-
 app/web/templates/layout.html                      |   1 +
 app/web/templates/san_pham.html                    |  56 ++++
 docs/sessions/S108-pra-005-major-implementation.md | 223 +++++++++++++
 docs/tasks/TASK-PRA-005-san-pham.md                | 261 +++++++++++++--
 tests/test_product_queries.py                      | 352 +++++++++++++++++++++
 tests/test_sales_presentation.py                   |  65 ++++
 tests/test_web_product_view.py                     | 164 ++++++++++
 13 files changed, 1396 insertions(+), 42 deletions(-)
```

KHÔNG có file schema, migration, Tracking, identity resolution, hạ tầng nào
bị đụng tới. Grep trên delta `app/**` không tìm thấy `schema`, `migrat`,
`ALTER TABLE`, `CREATE TABLE`, `canonical_product`, `COALESCE` ở vị trí mã —
chỉ có hai dòng VĂN XUÔI trong docstring nhắc tới `coalesce`/`Tracking` để
phát biểu điều KHÔNG làm.

`git diff --check` → sạch, không lỗi khoảng trắng.

### Production Python LOC delta — đo lại

```
RAW added lines            : 149
RAW removed lines          : 5
NET (added-removed)        : 144
added, non-blank non-#     : 120
added code, excl docstrings: 83
BUDGET LIMIT               : 200 production Python LOC
```

Ngân sách mục 24 (`> 200 production Python LOC` ⟹ `SCOPE_EXPANSION_REQUIRED`)
**KHÔNG bị vượt dưới bất kỳ định nghĩa đếm nào**. Con số `126` mà S108 và
`PROJECT/REVIEW_BUDGET_LEDGER.md` ghi nằm giữa 120 và 149 nhưng không tái lập được
CHÍNH XÁC bằng các định nghĩa đếm ở trên — ghi lại là `FIND-PRA005-R1`
(`NON_BLOCKING`, độ chính xác báo cáo, không phải vấn đề Contract hay đúng
đắn).

## (2) Truy vết đường dữ liệu — SQL phát sinh THẬT

Câu SQL mà `product_totals()` thực sự phát ra (bắt bằng
`event.listens_for(engine, "before_cursor_execute")`):

```sql
SELECT order_line_current.product_key,
       min(order_line_source_version.product_raw) AS product_label,
       count(*) AS lines,
       count(DISTINCT order_line_current.order_key) AS order_count,
       sum(order_line_source_version.quantity) AS quantity,
       sum(order_line_result_version.total_sales) AS total_sales,
       sum(CASE WHEN (order_line_result_version.status = ?)
                THEN order_line_result_version.eligible_kpi_profit END) AS kpi_profit,
       sum(CASE WHEN (order_line_result_version.status = ?) THEN ? ELSE ? END) AS kpi_lines
FROM order_line_current
JOIN order_line_result_version ON order_line_result_version.id = order_line_current.current_result_version_id
JOIN order_line_source_version ON order_line_source_version.id = order_line_current.current_source_version_id
WHERE order_line_current.sale_date IS NOT NULL
GROUP BY order_line_current.product_key
ORDER BY sum(order_line_result_version.total_sales) DESC, order_line_current.product_key
```

Hình dạng đo được: `subquery: False` · `DISTINCT: 1` · `JOIN: 2` ·
`GROUP BY: 1` · `ORDER BY: 1` · **`COALESCE: 0`** · `LEFT/OUTER JOIN: 0`.

Trường dùng cho từng ngữ nghĩa, truy tới nguồn đã persist:

| Ngữ nghĩa | Trường persisted thật |
|---|---|
| Khoá gộp | `order_line_current.product_key` |
| Nhãn hiển thị | `MIN(order_line_source_version.product_raw)` |
| Số lượng | `SUM(order_line_source_version.quantity)` |
| Định danh đơn | `COUNT(DISTINCT order_line_current.order_key)` |
| Doanh thu | `SUM(order_line_result_version.total_sales)` |
| LN KPI | `SUM(CASE WHEN status='AUTO' THEN eligible_kpi_profit END)` |
| Tử số coverage | `SUM(CASE WHEN status='AUTO' THEN 1 ELSE 0 END)` |
| Mẫu số coverage | `COUNT(*)` |
| Lọc kỳ | `order_line_current.sale_date` |

Hai `JOIN` đều là đẳng thức trên `id` PRIMARY KEY của bảng version ⟹ mỗi
khoá dòng góp ĐÚNG MỘT bản ghi, không fan-out, không nhân đôi.

`GET /san-pham` phát ra **4 truy vấn, hằng số**, không tỉ lệ với 226 nhóm ⟹
không N+1.

## (3) An toàn khoá gộp — CRITICAL

`app/history/keys.py:70`:

```python
def product_key(product_raw: Optional[str]) -> str:
    return hashlib.sha256(canon(product_raw).encode("utf-8")).hexdigest()
```

với `canon()` cho chuỗi = `unicodedata.normalize("NFC", value).strip()`.
Đường GHI production (`app/history/extraction.py:40`) dùng CHÍNH hàm này.
⟹ `product_key == sha256(NFC(product_raw).strip())`, KHÔNG casefold, KHÔNG
bỏ dấu, KHÔNG chuẩn hoá khoảng trắng bên trong.

Re-derive độc lập trên CẢ 226 nhóm của oracle thật:

```
groups where sha256(NFC(label).strip()) != persisted key: 0
```

KHÔNG tồn tại: ưu tiên `canonical_product_code`, `COALESCE` canonical/raw,
fuzzy merge, model-code merge, substring merge, gộp không phân biệt hoa
thường, chuẩn hoá vượt ngữ nghĩa đã freeze, lọc dịch vụ. Xác nhận bằng cả
`COALESCE: 0` trong SQL phát sinh lẫn AST.

`GROUPING_VERDICT = PASS`. `PRODUCT_IDENTITY_CLAIM =
NOT_CANONICAL_PRODUCT_IDENTITY` (Tracking vẫn là Product Identity Authority
duy nhất, không bị đụng tới).

## (4) Nhãn hiển thị

`product_label = MIN(product_raw)` trong nhóm. Vì mọi `product_raw` trong
cùng một nhóm có NFC+strip GIỐNG HỆT nhau, khác biệt còn lại chỉ là khoảng
trắng đầu/cuối và biểu diễn NFC tương đương; `MIN` là hàm THUẦN, cho kết quả
TẤT ĐỊNH, không phụ thuộc thứ tự nạp. Không tạo naming authority mới.
`DISPLAY_DESCRIPTION_VERDICT = PASS`.

## (5) Oracle THẬT — reviewer tự recompute bằng SQL THÔ

Reviewer chạy phép gộp bằng `sqlalchemy.text()` thẳng trên bảng persisted,
KHÔNG gọi `sales_queries`:

```
=== REVIEWER RAW-SQL ORACLE (module NOT used) ===
groups        : 226
Σ quantity    : 407
Σ total_sales : 3562310000
Σ kpi_profit  : 900000
Σ kpi_lines   : 2
Σ lines       : 351

=== REVIEWER RAW UNGROUPED TOTALS ===
{'lines': 351, 'orders': 254, 'quantity': 407, 'total_sales': 3562310000,
 'kpi_profit': 900000, 'kpi_lines': 2}

=== NOW compare module output to reviewer oracle ===
  same group count      : True
  row-by-row mismatches : 0
  MODULE == RAW SQL     : True
```

Reconcile với `analytics_queries.period_totals()` đã nghiệm thu:

```
quantity  match: True      (407          = 407)
revenue   match: True      (3562310000   = 3562310000)
kpi       match: True      (900000       = 900000)
kpi_lines match: True      (2            = 2)
lines     match: True      (351          = 351)
```

Số S108 báo cáo (`quantity = 407`, `revenue = 3.562.310.000`) được **tái lập
độc lập**, không lấy S108 làm bằng chứng.

Reconcile này còn là tính chất CẤU TRÚC, không chỉ thực nghiệm: `_joined()`
và `_period()` của `sales_queries` GIỐNG HỆT `analytics_queries` từng ký tự,
và các biểu thức chỉ tiêu trùng khít `_metrics()`. `GROUP BY` chỉ PHÂN HOẠCH
cùng một tập dòng ⟹ Σ theo nhóm = tổng toàn kỳ theo định nghĩa.

## (6) Số đơn — không cộng được

```
Σ order_count (theo mặt hàng) : 351
orders (tổng kỳ)              : 254
```

Khác nhau đúng như mong đợi (một đơn nhiều mặt hàng được đếm ở nhiều nhóm).
Triển khai **KHÔNG** cộng `order_count` để suy ra tổng đơn: tóm tắt trang
không hiển thị ô số đơn nào, và `product_summary()` chỉ đọc `totals` toàn
kỳ. Ghi chú công khai `PRODUCT_ORDER_COUNT_NOTE` nói thẳng điều này trên
trang. `ORDER_COUNT_VERDICT = PASS`.

## (7) KPI — CRITICAL

Biểu thức KPI **trùng khít từng ký tự** với `_order_metrics()` (PRA-004) và
`_metrics()` (PRA-003) đã nghiệm thu — tái dụng ngữ nghĩa, không dựng nguồn
sự thật thứ hai.

`CASE` KHÔNG có `ELSE` ⟹ dòng không `AUTO` cho `NULL`, `SUM` bỏ qua `NULL`,
tập cộng rỗng trả `NULL`. Chuỗi `NULL` được truy từng tầng:

- SQL: không `COALESCE` (đo được: `COALESCE: 0`).
- `_product_shaped()`: ép `int` cho các ô ĐẾM, **giữ nguyên `None`** cho ba
  ô TIỀN (`quantity`, `total_sales`, `kpi_profit`).
- `profit()` → `money()` → `format_number()`: `None` ⟹ `"—"`, không bao giờ
  `0`; `missing=True`.
- Template: không `|default(0)`, không `or 0`.

Phân biệt bốn trạng thái:

| Ca | Kết quả đo | Hiển thị |
|---|---|---|
| A. KPI = `NULL` (0 dòng AUTO) | `kpi_profit is None`, `kpi_lines=0` | `—` + `0 / N dòng`, `missing=True` |
| B. KPI = `Decimal("0")` biết chắc | `kpi_profit == Decimal("0")`, `kpi_lines=1` | `0` + coverage, `missing=False` |
| C. KPI dương | `900000` trên oracle thật | số + coverage |
| D. KPI âm | `format_number` xử lý dấu `-` tường minh | số âm + coverage |

Trên dữ liệu thật: 224/226 nhóm có `kpi_profit = NULL`, 0 nhóm known-zero —
ca B chỉ tồn tại ở test tổng hợp `test_I`, đúng và đủ.

Tính toàn vẹn tử số coverage: truy vấn thô đếm được **0 dòng `AUTO` có
`eligible_kpi_profit IS NULL`** ⟹ tử số (`kpi_lines`) và tập cộng của
`kpi_profit` khớp nhau trên dữ liệu đã nghiệm thu.

`KPI_SOURCE_VERDICT`, `KPI_NULL_VERDICT`, `KPI_KNOWN_ZERO_VERDICT`,
`KPI_COVERAGE_VERDICT` = `PASS`.

Coverage: tử số = số dòng có KPI biết chắc, mẫu số = `COUNT(*)` mọi dòng góp
phần — KHÔNG phải số đơn, số lượng, số dòng AUTO theo nghĩa khác, hay số
dòng đã resolve identity. Đúng ở CẢ dòng mặt hàng lẫn tóm tắt kỳ.

## (8) Bao gồm toàn bộ dòng (OD-PRA005-02)

`is_non_product_line` **có thật** và **đang được dùng** ở production
(`app/modules/validation/rules.py:52,75`) ⟹ test khẳng định PRA-005 không
gọi nó là test CÓ NGHĨA, không rỗng. AST xác nhận định danh này không nằm
trong tập định danh của `sales_queries.py` (hai lần xuất hiện đều trong
VĂN XUÔI docstring, không phải lời gọi).

Trên oracle THẬT, các dòng dịch vụ/phí vẫn tới được bảng:

```
'Chi phí vận chuyển': True
'Giá treo Tivi'     : True
'Chi phí lắp đặt'   : True
```

Không heuristic phân loại nào trở thành thẩm quyền nghiệp vụ.
`ALL_LINE_INCLUSION = PASS`, `SERVICE_FEE_ORACLE = PASS`.

## (9) Split oracle FTKB50ZVMV

Tái lập độc lập trên fixture thật:

```
label='Điều hoà Daikin  FTKB50ZVMV'              qty=7  rev=113750000  key=4fe08a722a0b…
label='Máy lạnh Daikin Inverter 2 HP FTKB50ZVMV' qty=1  rev=16250000   key=4789641dc72b…
```

Hai nhóm RIÊNG BIỆT, hai khoá khác nhau, KHÔNG có mã đặc biệt cho
FTKB50ZVMV. Chú ý chính tả thật có HAI khoảng trắng
(`Daikin  FTKB50ZVMV`) — bằng chứng thêm rằng KHÔNG có chuẩn hoá khoảng
trắng bên trong. `SPLIT_ORACLE = PASS` (SPLIT là giới hạn ĐÃ CHẤP NHẬN
`FIND-PRA005-01`; MERGE sai đã được loại trừ).

## (10) Số lượng · Doanh thu

`SUM(quantity)` trên các dòng hiện hành góp phần; `Decimal` giữ nguyên, không
ép kiểu, không làm tròn. Trên dữ liệu đã nghiệm thu: 0 dòng `quantity NULL`,
0 dòng âm. Doanh thu đọc THẲNG `order_line_result_version.total_sales` đã
persist — **KHÔNG** tính lại từ đơn giá × số lượng, chiết khấu hay thuế.
`QUANTITY_VERDICT`, `REVENUE_VERDICT` = `PASS`.

## (11) Tóm tắt tái dụng

Xác nhận đúng như S108 báo cáo: 3/4 chỉ tiêu tóm tắt lấy NGUYÊN VẸN từ
`analytics_queries.period_totals()` qua `view["totals"]`; chỉ `item_count`
(`= len(rows)`) là mới. Phạm vi lọc GIỐNG HỆT nhau: route truyền
`date_from=view["bounds"][0], date_to=view["bounds"][1]` cho `product_totals()`,
trong khi `view["totals"]` được tính bằng CHÍNH `bounds` đó. `_period()` của
hai module giống hệt từng ký tự. `SUMMARY_REUSE_VERDICT`,
`TIME_FILTER_VERDICT` = `PASS`.

`item_count` = số mô tả thô đã chuẩn hoá PHÂN BIỆT (số nhóm `GROUP BY`) =
226 trên oracle thật — KHÔNG phải số sản phẩm canonical, số dòng (351), hay
số SKU. Nhãn `"Số mặt hàng trên chứng từ"` (tránh `"Số sản phẩm"` theo EAC-5,
`FIND-PRA005-02`). `ITEM_COUNT_VERDICT = PASS`.

## (12) Trang thật — kiểm tra trực tiếp HTML render

```
STATUS /san-pham : 200
Cột render      : ['Mặt hàng', 'Số lượng', 'Số đơn', 'Doanh thu', 'LN KPI']
Tóm tắt         : item_count=226 · quantity=407 · total_sales=3.562.310.000 · kpi_profit=900.000
Số dòng bảng    : 226
3 dòng đầu      : Tivi Samsung 98DU9000 Crystal UHD | 3 | 2 | 117.887.500 | — 0 / 2 dòng
                  Điều hoà Daikin FTKB50ZVMV        | 7 | 1 | 113.750.000 | — 0 / 1 dòng
                  Điều hoà Daikin FCF100CVM/RZA100DV1| 2 | 1 |  94.000.000 | — 0 / 1 dòng
```

Đúng NĂM cột Contract. Ô LN KPI không bao giờ render thiếu mẫu số, và ô chưa
biết hiện `—` kèm `0 / N dòng`, KHÔNG hiện `0`.

Vắng mặt PP cấp mặt hàng — đếm trên HTML đã render:

```
'Giá mua tham chiếu': 0   'Giá mua': 0   'Giá nhập': 0   'Giá vốn': 0
'purchase_price': 0       'purchase price': 0            'average cost': 0
'Giá trung bình': 0       'PP': 0        'Chi phí vốn': 0
```

PP cấp DÒNG của PRA-004 (`LINE_COLUMNS` → `"Giá mua tham chiếu"`) KHÔNG bị
đụng tới. `REFERENCE_PRICE_VERDICT = PASS`.

Từ vựng kỹ thuật/nội bộ — đếm trên HTML đã render:

```
'product_key': 0  'sha256': 0  'SHA': 0  'hash': 0  'NFC': 0
'canonical_product_code': 0    'order_key': 0
```

Ghi chú công khai BẮT BUỘC xuất hiện nguyên văn:

> Mặt hàng được gộp theo tên ghi trên chứng từ. Các tên khác nhau của cùng
> một sản phẩm có thể được hiển thị thành các dòng riêng.

`DISCLOSURE_VERDICT = PASS`.

Ranh giới trình bày: template chỉ RENDER giá trị đã chuẩn bị — không phép
tính nghiệp vụ, không `|default(0)`, không `or 0`. Mọi phép tính nằm ở tầng
query/presentation. `PRESENTATION_BOUNDARY = PASS`.

## (13) Sắp xếp mặc định

`ORDER BY sum(total_sales) DESC, product_key` — doanh thu giảm dần, khoá
phụ TẤT ĐỊNH. Đo trên trang thật: dãy doanh thu không tăng
(`is non-increasing: True`); hai lần gọi liên tiếp cho THỨ TỰ GIỐNG NHAU.
Không có ngữ nghĩa xếp hạng/chấm điểm nào. `DEFAULT_SORT_VERDICT = PASS`.

Ghi nhận `FIND-PRA005-R2` (`NON_BLOCKING`): `total_sales` là `nullable` trong
schema; PostgreSQL mặc định `NULLS FIRST` cho `DESC` còn SQLite cho `NULLS
LAST`, nên một nhóm có doanh thu TOÀN `NULL` sẽ nằm đầu bảng ở production
nhưng cuối bảng ở test. Đo được trên dữ liệu đã nghiệm thu: **0 dòng
`total_sales NULL`, 0 nhóm `total_sales NULL`** ⟹ chưa từng đạt tới. Không
sửa (mục 31 cấm repair hardening suy đoán). RE-TRIGGER: xuất hiện dòng bán có
`total_sales NULL` trong dữ liệu accepted.

## (14) Trạng thái rỗng

Kỳ không có dòng nào, render trực tiếp:

```
status: 200
no-products msg: True   ("Kỳ này chưa có mặt hàng nào trên số mới.")
item_count : 0
quantity   : —
total_sales: —
kpi_profit : —
```

`item_count = 0` là con số ĐÚNG (thật sự không có mô tả nào); ba ô tiền hiện
`—` vì `SUM` trên tập rỗng trả `NULL` — đúng ngữ nghĩa đã nghiệm thu của
`period_totals()`, KHÔNG bịa "biết chắc bằng 0", KHÔNG bịa coverage.
`EMPTY_STATE_VERDICT = PASS`.

## (15) Drill-down

`CHECK-PRA005-13` = `NOT_APPLICABLE`, `DEFERRED_WITHIN_CONTRACT` (mục 18 cho
phép tường minh; check là RECOMMENDED nên không chặn). Xác nhận KHÔNG có
drill-down một phần/hỏng nào được đưa vào: `__all__` của `sales_queries` chỉ
thêm `product_totals`, không có `product_lines`; không route
`/san-pham/<product_key>`; không template chi tiết mới. Reviewer KHÔNG triển
khai nó. `DRILLDOWN_VERDICT = DEFERRED_WITHIN_CONTRACT`.

## (16) Hiệu năng

S108 đo trên PostgreSQL 16 thật (sqlalchemy 2.0 + psycopg3), 12.000 dòng /
2.491 nhóm, 3 lần chạy: 81,7 / 65,4 / 102,8 ms; DB scratch đã xoá sau đo nên
KHÔNG tái lập được nguyên văn trong phiên này.

Phân loại: **`CREDIBLE_SESSION_MEASUREMENT`** — phương pháp ghi rõ (engine,
driver, quy mô, số lần chạy), quy mô đúng hình dạng Discovery S105 §35, và
đối chiếu được với mốc PRA-003 đã nghiệm thu (64 ms cùng tầng truy vấn trên
PostgreSQL production).

Reviewer bổ sung bằng chứng ĐỘC LẬP về hình dạng thuật toán (mạnh hơn một
con số): một truy vấn PHẲNG duy nhất, không subquery, không `LEFT JOIN`, hai
`JOIN` đẳng thức trên PRIMARY KEY, một `GROUP BY`, và `GET /san-pham` phát
ra 4 truy vấn HẰNG SỐ không tỉ lệ với số nhóm ⟹ không N+1, không blocker
thuật toán. Không có vấn đề dùng thực tế theo chiều dọc. KHÔNG tối ưu cho
quy mô giả định.

## (17) Chất lượng test

48 test mới, đếm lại khớp: `test_product_queries.py` 28 · `test_web_product_
view.py` 14 · `test_sales_presentation.py` +6.

Test chạy vào HÀNH VI PRODUCTION, không chỉ thuật lại nội bộ: oracle là
fixture golden qua ĐƯỜNG PRODUCTION (`load_golden`), và nhóm web test kiểm
tra HTML thật của `/san-pham`. Phủ đủ 15 nhóm yêu cầu: gộp theo raw · split ·
bao gồm toàn bộ dòng · số lượng · đơn phân biệt · doanh thu · KPI đủ · KPI
một phần · KPI zero-known · KPI known-zero · reconciliation · sắp xếp ·
trạng thái rỗng · vắng PP · route render.

Kiểm tra test giả-dương: các khẳng định PHỦ ĐỊNH đều có nghĩa —
`is_non_product_line` tồn tại và đang dùng ở production; `product_key` nằm
trong `INTERNAL_VOCABULARY` và được kiểm trên HTML thật; `_identifiers()`
dùng AST nên nhắc trong docstring không tạo pass giả, mà lời gọi thật sẽ bị
bắt. KHÔNG phát hiện test giả-dương. `TEST_QUALITY = PASS`.

## (18) Regression — reviewer chạy lại độc lập

```
Focused PRA-005     : 75 passed          (3 file focused)
PRA-003 analytics   : 42 passed
PRA-004 sales+web   : 261 passed
Golden / baseline   : 345 passed, 2 skipped, 1696 deselected
FULL SUITE          : 2032 passed, 11 skipped in 90.40s
```

Khớp CHÍNH XÁC baseline S108 báo cáo (`2032 passed, 11 skipped, 0 failed`).

Ghi chú môi trường: lần chạy full suite ĐẦU TIÊN có 1 failure
`TestG25GoldenBaselineUnchanged::test_protected_golden_artifacts_match_the_
task_105e_review_base` với `fatal: bad object 740f396acb11cf279f303f09ea22
dffd0ca95462`. Nguyên nhân đã xác định là clone NÔNG (`git rev-parse
--is-shallow-repository` → `true`, chỉ 56 commit) thiếu object đó, KHÔNG
phải lỗi mã: sau `git fetch origin 740f396…` object tồn tại và
`tests/test_105d_boundaries.py` → `41 passed`, full suite → `2032 passed,
11 skipped`. Đây là tạo tác môi trường review, không phải finding của
candidate.

`GOLDEN_EXPECTATION_CHANGE = NO` — diff không đụng tới bất kỳ file golden/
fixture/baseline/expectation nào (kiểm bằng lọc tên file trên toàn diff).

## (19) Governance

```
validate_structure          : GOVERNANCE STRUCTURE: PASS (21 required paths)
validate_project_state      : PROJECT STATE: PASS
validate_evidence           : EVIDENCE VALIDATION: PASS (153 REQUIRED PASS evidence)
validate_task_completion    : TASK COMPLETION: PASS (12 DONE task)
validate_reference_integrity: FAIL — ĐÚNG 3 reference REM-T06 đã biết
git diff --check            : sạch
branch_authority_check.sh   : AUTHORITY_OK · WITHIN_LIMITS · WORKTREE CLEAN
```

Ba reference chưa phân giải đều thuộc
`docs/tasks/TASK-REM-T06-repository-root-hygiene.md` và trỏ tới ba file
hygiene ở gốc repo chưa tồn tại (README ở gốc, CODE_OF_CONDUCT,
CONTRIBUTING) — ĐÚNG baseline kỳ vọng, KHÔNG có issue mới. KHÔNG sửa
REM-T06. Bản ghi này CỐ Ý không viết lại ba tên file đó dưới dạng literal
`.md`, để chính nó không sinh thêm reference gãy.

Bản ghi này KHÔNG làm tăng số reference gãy: trước và sau khi tạo file này,
`validate_reference_integrity` đều báo ĐÚNG 3 issue REM-T06.

Forward reference tới chính file này đang được miễn trừ tường minh trong
`KNOWN_EXEMPT_PAIRS` của `validate_reference_integrity.py`
(`docs/tasks/TASK-PRA-005-san-pham.md` → `docs/reviews/TASK-PRA-005-
INDEPENDENT-REVIEW-RECORD.md`). Việc tạo file này làm miễn trừ đó trở thành
không cần thiết mà không sinh issue mới.

## (20) Findings

```
BLOCKING_FINDINGS     : 0
NON_BLOCKING_FINDINGS : 2 (mới, của phiên review)
DEFERRED_FINDINGS     : 1 (CHECK-PRA005-13 drill-down, DEFERRED_WITHIN_CONTRACT)
```

### FIND-PRA005-R1 — LOC delta báo cáo không tái lập chính xác · `NON_BLOCKING`

`126` (S108 + `PROJECT/REVIEW_BUDGET_LEDGER.md`) không khớp chính xác phép đếm nào
của reviewer (149 thêm / 144 net / 120 không-trắng-không-comment / 83 loại
docstring). Mọi phép đếm đều DƯỚI ngân sách 200 nên không có hệ quả nghiệp
vụ hay Contract. Không sửa: không phải production path, không phải vấn đề
đúng đắn (mục 32).

### FIND-PRA005-R2 — Thứ tự `NULL` doanh thu khác nhau giữa SQLite và PostgreSQL · `NON_BLOCKING`

Xem mục (13). Chưa đạt tới trên dữ liệu đã nghiệm thu (0/351 dòng, 0/226
nhóm). Không sửa (mục 31: cấm repair hardening suy đoán).

### FIND-PRA005-01/02/03 (từ Discovery, không đổi)

`FIND-PRA005-01` (SPLIT của `product_key`) vẫn là giới hạn ĐÃ CHẤP NHẬN theo
DEC-173, được xác nhận lại bằng oracle FTKB50ZVMV ở mục (9).

## (21) Repair

```
REPAIR_BATCH_USED : NO
REPAIR_COMMIT     : (không có)
```

Không có finding BLOCKING nào ⟹ không mở repair batch. Review Budget
`repair_cycles_used` giữ nguyên `0 / 1`.

## (22) Completion Gate — kết luận

Reviewer đã xác minh ĐỘC LẬP rằng mỗi PASS hiện có đều có bằng chứng thật:

| Check | Status | Bằng chứng độc lập của reviewer |
|---|---|---|
| CHECK-PRA005-01 | PASS (E1) | AST: không import ghi, không `begin/commit`; SQL phát sinh chỉ `SELECT` |
| CHECK-PRA005-02 | PASS (E1) | Re-derive `product_key` khớp 226/226; `COALESCE: 0`; không fuzzy |
| CHECK-PRA005-03 | PASS (E1) | Tóm tắt trang = `period_totals` cùng `bounds`; đo trên HTML thật |
| CHECK-PRA005-04 | PASS (E1) | Σ nhóm = tổng kỳ, 5/5 đồng nhất, oracle SQL thô |
| CHECK-PRA005-05 | PASS (E1) | `kpi_profit` 900000 = 900000; `kpi_lines` 2 = 2 |
| CHECK-PRA005-06 | PASS (E1) | Chuỗi `NULL` truy đủ 4 tầng; ca A/B/C/D phân biệt |
| CHECK-PRA005-07 | PASS (E1) | FTKB50ZVMV tách 2 nhóm, 2 khoá, không mã đặc biệt |
| CHECK-PRA005-08 | PASS (E1) | 3 mô tả dịch vụ/phí thật có mặt; `is_non_product_line` không được gọi |
| CHECK-PRA005-09 | PASS (E1) | `ORDER BY … DESC, product_key`; dãy không tăng; tất định |
| CHECK-PRA005-10 | PASS (E1) | 10/10 thuật ngữ PP đếm được 0 trên HTML đã render |
| CHECK-PRA005-11 | PASS (E1) | SQL phát sinh chỉ chọn `product_key`/`product_raw` + tổng hợp |
| CHECK-PRA005-12 | PASS (E1) | `CREDIBLE_SESSION_MEASUREMENT` + hình dạng truy vấn do reviewer đo |
| CHECK-PRA005-13 | NOT_APPLICABLE | RECOMMENDED, `DEFERRED_WITHIN_CONTRACT`, không có drill-down dở dang |
| CHECK-PRA005-14 | **PASS (E2)** | **Chính bản ghi này** |
| CHECK-PRA005-15 | NOT_TESTED | Owner Production Acceptance — CHƯA có bằng chứng production |

`CHECK-PRA005-15` GIỮ `NOT_TESTED`: không đánh PASS bất kỳ tiêu chí
deployment/real-data nào trước khi có bằng chứng production thật.

⟹ **`TASK-PRA-005` TỔNG THỂ VẪN CHƯA `DONE`.**

## (23) Quyết định

```
REVIEW_RESULT            = ACCEPT
SCOPE_DRIFT              = NO
INTEGRATION_READY        = YES
CANONICAL_INTEGRATION_STATUS = NOT_YET_INTEGRATED
FINAL_REVIEWED_HEAD_SHA  = 18ab5d39a15b224d34aa04e5c6bbe8261f60efeb
```

Reviewer KHÔNG integrate vào canonical trong phiên này. SHA đầy đủ 40 ký tự
ở trên là ứng viên DUY NHẤT được uỷ quyền cho Controlled Integration.

`NEXT_VERTICAL_ACTION = PRA-005 CONTROLLED INTEGRATION`.
