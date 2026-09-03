# S108 — TASK-PRA-005 MAJOR Implementation (Sản Phẩm — Mặt Hàng Trên Chứng Từ)

## Metadata

```
SESSION                  : S108 — PRA-005 MAJOR Implementation
NGÀY                     : 2026-09-03
TASK MODE                : MAJOR
TASK                     : TASK-PRA-005 — Sản phẩm (Mặt hàng trên chứng từ) —
                            Aggregation View (CHỈ-ĐỌC)
TRẠNG THÁI TASK SAU PHIÊN: IMPLEMENTED (KHÔNG phải DONE — Independent Review
                            E2 + Owner Production Acceptance còn PENDING)
PROJECT PROFILE          : PRODUCT
RISK                     : 3        BLAST RADIUS : 3/5
BASE_CANONICAL           : claude/extract-upload-repo-gq2ws4 @ 4e06515895814d8fff41580dc0f3c64da464ac83
NHÁNH IMPLEMENT           : claude/pra-005-v1-implementation-3dcd5k (tạo sẵn ĐÚNG
                            tại BASE_SHA đầu phiên, 0 ahead/0 behind)
```

Phiên này TRIỂN KHAI hợp đồng đã freeze tại S107
(`docs/tasks/TASK-PRA-005-san-pham.md`, DEC-173). Không thiết kế lại contract,
không mở lại discovery, không thêm yêu cầu.

## Xác Minh Thẩm Quyền (đầu phiên)

```
git remote show origin → HEAD branch: claude/extract-upload-repo-gq2ws4
git fetch origin claude/extract-upload-repo-gq2ws4
git rev-parse origin/claude/extract-upload-repo-gq2ws4
  → 4e06515895814d8fff41580dc0f3c64da464ac83   ✓ khớp EXACT SHA kỳ vọng đầu phiên
git rev-parse HEAD (claude/pra-005-v1-implementation-3dcd5k)
  → 4e06515895814d8fff41580dc0f3c64da464ac83   ✓ CÙNG SHA — nhánh implementation
                                                  đã tồn tại sẵn, tạo đúng từ SHA này
git status --porcelain (đầu phiên) → rỗng (working tree sạch)
```

`CANONICAL_MOVED = KHÔNG`. Đọc lại đầy đủ trước khi code:
`docs/tasks/TASK-PRA-005-san-pham.md`, `docs/sessions/S105-pra-005-san-pham-
discovery.md`, `PROJECT/PROJECT_DECISIONS.md` (DEC-173),
`PROJECT/PROJECT_PROGRESS.md` khối "TASK-PRA-005 CONTRACT FREEZE" — không
phát hiện session song song nào khác đã làm lại phần việc này trên
`origin/claude/extract-upload-repo-gq2ws4`.

## Thứ Tự Triển Khai

1. `app/web/sales_queries.py` — thêm `product_totals()` (khuôn `employee_
   totals()`/`_order_metrics()` đã có, GROUP BY `product_key`).
2. `app/web/sales_presentation.py` — thêm `PRODUCT_COLUMNS`, ghi chú bắt
   buộc, `product_row()`/`product_rows()`/`product_summary()`.
3. `app/web/server.py` — route `/san-pham` (tái dụng `_pipeline_view()`).
4. `app/web/templates/san_pham.html` (mới) + 1 dòng tab ở `layout.html`.
5. Test (48 test PRA-005 mới: 28 tầng truy vấn, 14 vertical web, 6 tầng
   trình bày) trước khi tuyên bố xong.

Không CSS mới — `module`/`kpi-grid`/`sales-orders`/`tag` đã đủ (mục 24 cho
phép ≤10 dòng, dùng 0).

## Quyết Định Triển Khai Đáng Ghi Lại

### 1. Tóm tắt tái dụng `analytics_queries.period_totals()` thay vì cộng lại các dòng đã gộp

Bản nháp đầu tiên tính bốn chỉ tiêu tóm tắt bằng cách cộng (Python,
`sales_presentation.py`) các giá trị đã gộp trong `product_totals()`. Về mặt
toán học điều này ĐÚNG (`GROUP BY` là một phân hoạch — tổng các nhóm luôn
bằng tổng kỳ), và một test reconciliation trên oracle THẬT đã xác nhận điều
đó (khớp bit-for-bit). Nhưng `server.py::_pipeline_view()` đã sẵn gọi
`analytics_queries.period_totals()` cho CÙNG phạm vi lọc (dùng cho
`/tong-quan`) — tái dụng thẳng `view["totals"]` cho ba trong bốn chỉ tiêu
tóm tắt (Số lượng, Doanh thu, LN KPI) mạnh hơn: nó khớp BYTE-IDENTICAL với
`/tong-quan` theo đúng chữ "Tái dụng NGUYÊN VẸN" của mục 8.2/8.3 Contract,
không tốn thêm truy vấn (đã fetch sẵn), và đúng tiền lệ dòng TỔNG của
PRA-003 (`employee_rows()` lấy thẳng từ `period_totals()`, KHÔNG cộng các
dòng nhân viên). Đã refactor sang hướng này; `product_summary(rows, totals)`
chỉ còn tự tính MỘT chỉ tiêu thật sự mới của PRA-005 — `item_count =
len(rows)` (Số mặt hàng trên chứng từ, mục 8.1, không tồn tại ở
`analytics_queries`).

### 2. Drill-down (mục 18) — `DEFERRED_WITHIN_CONTRACT`

Contract đánh dấu drill-down `RECOMMENDED, NOT REQUIRED` và cho phép DEFER
nếu "direct filtered deep-link đòi hỏi phạm vi bất tương xứng với ngân sách
slice này". Đường tối thiểu (`product_lines()` lọc theo `product_key` + route
`/san-pham/<product_key>` + template dòng-chi-tiết mới) đòi một truy vấn
MỚI, MỘT route MỚI, và MỘT template MỚI riêng cho drill-down — vượt phần còn
lại của ngân sách 200 dòng Python nếu cộng cùng vertical chính, trong khi
CHECK-PRA005-13 là RECOMMENDED (không REQUIRED để task PASS). Quyết định:
DEFER trong Contract, `CHECK-PRA005-13 = NOT_APPLICABLE` (giải thích), giữ
budget cho REQUIRED checks. RE-TRIGGER: Owner yêu cầu xem trực tiếp các dòng
bán của một mặt hàng từ trang `/san-pham` (mở một task/slice riêng, KHÔNG mở
rộng V1 âm thầm).

### 3. `_product_metrics()` là hàm RIÊNG, không import từ `analytics_queries._metrics()`

`analytics_queries.py` nằm trong danh sách CẤM sửa (touch area mục 25, EAC-9).
`_metrics()` của nó có hình dạng gần giống nhưng KHÔNG hoàn toàn khớp (đếm
`orders` theo TOÀN kỳ, không theo nhóm mặt hàng — `order_count` của PRA-005
phải đếm PHÂN BIỆT TRONG PHẠM VI của chính nhóm). Import một hàm private
(`_metrics`, gạch dưới) từ module khác cũng phá vỡ đúng ranh giới kiến trúc
mà PRA-004 đã dựng (`sales_queries` giữ hàng rào/logic RIÊNG, hẹp/khác đúng
những gì nó cần — EAC-9). Viết `_product_metrics()` riêng trong
`sales_queries.py`, cùng khuôn `_order_metrics()` đã có trong CHÍNH module
đó — không phải một module mới, không phải một import xuyên ranh giới.

## Xác Minh Oracle TRƯỚC Khi Viết Test Reconciliation

Trước khi viết assertion cho split/service-line/reconciliation, phiên này
chạy lại ĐƯỜNG PRODUCTION THẬT trên fixture golden `period_2026_01.xlsx` rồi
truy vấn `product_totals()` trên dữ liệu đã persist, để đo — không suy đoán:

```text
226 nhóm mặt hàng (khớp EXACT số đo Discovery S105 §13: "226 chuỗi tên hàng
phân biệt")
351 dòng, Σ(lines theo nhóm) = 351

Split FTKB50ZVMV (S105 §9, DEC-173):
  'Điều hoà Daikin  FTKB50ZVMV'                 qty 7   doanh thu 113.750.000
  'Máy lạnh Daikin Inverter 2 HP FTKB50ZVMV'    qty 1   doanh thu  16.250.000
  → HAI dòng riêng, KHÔNG gộp — khớp S105 §9 (số doanh thu 16.250.000 khác
    con số minh hoạ 16.300.000 của Discovery vì Discovery đo sell_price gộp,
    PRA-005 đo total_sales SAU chiết khấu 50.000 — đây là ĐÚNG ngữ nghĩa
    "doanh thu" của mục 12, KHÔNG phải sai lệch)

Dòng dịch vụ/phí (S105 §13) vẫn trong bảng, không lọc:
  'Chi phí vận chuyển'   qty 19   doanh thu 4.683.750
  'Giá treo Tivi'        qty 15   doanh thu 2.150.000
  'Chi phí lắp đặt'      qty  2   doanh thu   200.000

Reconciliation với analytics_queries.period_totals() (CÙNG kỳ):
  Σ(quantity theo mặt hàng)   = 407     = totals["quantity"]
  Σ(total_sales theo mặt hàng)= 3.562.310.000 = totals["total_sales"]
  Σ(kpi_profit đã biết)      = 900.000  = totals["kpi_profit"]
  Σ(kpi_lines)               = 2        = totals["kpi_lines"]
  Σ(lines)                   = 351      = totals["lines"]
  Σ(order_count theo mặt hàng) = 351   ≠ totals["orders"] = 254 (KHÔNG cộng
    được — mục 17, đúng như Contract cảnh báo)
```

Toàn bộ khớp EXACT với S105 và với `analytics_queries.period_totals()` trên
CÙNG engine/dữ liệu. Oracle KHÔNG bị viết ngược từ kết quả triển khai.

## Kết Quả Kiểm Thử

```
Focused PRA-005                : 48 test PASS
  tests/test_product_queries.py       : 28 test (tầng truy vấn — A-O, split,
                                          reconciliation, PII, no-aggregate-PP)
  tests/test_web_product_view.py      : 14 test (vertical web thật — route,
                                          5 cột, disclosure note, split trên
                                          trang, NULL≠0, PII, trạng thái rỗng)
  tests/test_sales_presentation.py    :  6 test mới (product_row/summary)

PRA-003 regression (test_analytics_queries.py, test_analytics_presentation.py,
  test_web_pipeline_analytics.py)     : PASS, không đổi
PRA-004 regression (test_sales_queries.py, test_sales_presentation.py,
  test_web_sales_detail.py)           : PASS, không đổi

FULL SUITE (python -m pytest -q)      : 2032 passed, 11 skipped, 0 failed
  (con số trước phiên: đã xác nhận PRA-003/PRA-004 xanh nguyên vẹn — không
  Golden expectation nào bị sửa)
```

## Đo Hiệu Năng (mục 21/23, CHECK-PRA005-12)

```text
Engine    : PostgreSQL 16 (local psql server, sqlalchemy 2.0 + psycopg3) —
            ĐÚNG engine test/CI tương đương production, KHÔNG phải SQLite.
Dataset   : 12.000 dòng tổng hợp có kiểm soát, 2.491 nhóm mặt hàng phân biệt
            — CÙNG hình dạng đo ở Discovery S105 §35.
Truy vấn  : product_totals(engine, date_from=2026-01-01, date_to=2026-01-31)
Elapsed   : 81.7 ms / 65.4 ms / 102.8 ms (3 lần chạy liên tiếp)
```

Đối chiếu: PRA-003 đã nghiệm thu 64 ms cho truy vấn cùng tầng (`_joined()` +
`GROUP BY` + `ORDER BY`) trên PostgreSQL production thật với cùng quy mô.
Không blocker thuật toán nào. Con số này KHÔNG được freeze thành SLA (mục
21) — chỉ xác nhận `product_totals()` không cần cache/materialized
view/warehouse để chạy được ở quy mô hiện tại (thật: 61 dòng/kỳ, 09/2026).

## Findings

Không finding MỚI nào đe doạ bốn nhóm Review Budget (mục Review Budget
Contract §1-4). Ba finding mang theo nguyên vẹn từ Discovery (FIND-PRA005-01/
02/03) không cần xử lý lại — đã xử lý bằng cách gọi tên đúng ở Contract, và
implementation không đổi cách xử lý đó.

## Điều KHÔNG Làm Trong Phiên Này

```
KHÔNG sửa app/web/analytics_queries.py / analytics_presentation.py (git diff
  = rỗng, xác nhận bằng lệnh)
KHÔNG sửa tests/test_analytics_queries.py
KHÔNG gọi is_non_product_line() ở bất kỳ đâu trong touch area PRA-005
KHÔNG fuzzy/substring/model-code merge nào được thêm (AST + grep xác nhận)
KHÔNG hiển thị Giá mua tham chiếu tổng hợp cấp mặt hàng
KHÔNG schema/migration/Tracking change
KHÔNG drill-down mới (DEFERRED_WITHIN_CONTRACT, mục 18)
KHÔNG CSS mới
KHÔNG tạo TASK-PRA-005-INDEPENDENT-REVIEW-RECORD.md (mục 26 Contract —
  thuộc phiên Independent Review E2 tiếp theo)
KHÔNG tích hợp vào canonical trong phiên này (mục 27 — ở lại nhánh dedicated
  chờ Independent Review)
KHÔNG repair REM-T06 (3 issue reference-integrity baseline không đổi)
```

## Bàn Giao (Handoff)

```
TRẠNG THÁI TASK           : PRA-005 Discovery = DONE · Contract = FROZEN ·
                             Implementation = COMPLETE / REVIEW_PENDING
NHÁNH                     : claude/pra-005-v1-implementation-3dcd5k
                             (CHƯA tích hợp vào canonical)
NEXT_VERTICAL_ACTION      : PRA-005 INDEPENDENT REVIEW E2
                             (CHECK-PRA005-14, theo
                             governance/templates/E2_INDEPENDENT_REVIEW_
                             TEMPLATE.md, ghi tại docs/reviews/TASK-PRA-005-
                             INDEPENDENT-REVIEW-RECORD.md)
SAU ĐÓ                    : CHECK-PRA005-15 — Owner Production Acceptance
                             trên reports.tinphatcrm.com (mục 27 task file)
```

Session tiếp theo (Independent Review E2) nên đọc file này + `docs/tasks/
TASK-PRA-005-san-pham.md` mục Completion Gate (đã cập nhật evidence tại
phiên này) trước khi đánh giá.
