# `R6` — INDEPENDENT REVIEW RECORD (bằng chứng nguyên văn)

Artifact Type:
INDEPENDENT REVIEW RECORD — bản ghi đầy đủ của `CHECK-R6-31`.

Executed By:
Phiên Independent Review `S144` (Claude Code, nhánh
`claude/r6-independent-review-dvuiiw`).

Timestamp:
2026-09-09

Status:
`REPAIR_REQUIRED`

Evidence Level:
E1 — mọi con số dưới đây là output nguyên văn của lệnh đã thực thi trong
chính phiên này, không trích lại từ bàn giao `S143`.

Bản tóm tắt cho người đọc nhanh: `docs/sessions/S144-r6-independent-review.md`.

---

## 0. Preflight — đúng đối tượng, đúng nền

Phiên KHÔNG tin một SHA nào trong bàn giao `S143`; mọi mốc dưới đây được đo
lại bằng `git` trong phiên này.

```text
$ git remote show origin | grep "HEAD branch"
  HEAD branch: claude/extract-upload-repo-gq2ws4

$ git rev-parse HEAD
56aca4c91bd788b1e14d7f71b9246d1577255c1a
$ git rev-parse origin/claude/r6-business-analytics-dashboard-it73x5
56aca4c91bd788b1e14d7f71b9246d1577255c1a
$ git rev-parse origin/claude/extract-upload-repo-gq2ws4
05f2b443e66ee4702d03c003d5f1f960b5765f8d

$ git merge-base --is-ancestor 05f2b443... 56aca4c9... && echo YES
BASE_IS_ANCESTOR=YES

$ git status --porcelain | wc -l
0
```

Tracking:

```text
$ git remote show origin | grep "HEAD branch"
  HEAD branch: main
$ git rev-parse origin/main
66787c0fb0d867a308c632e7f163cddd0c9dd0f2
$ git merge-base --is-ancestor dc9891087687f25b6f92804f46eba2628ebe788b origin/main
DC98910_IN_MAIN=YES
$ git status --porcelain | wc -l
0
```

Bốn điều kiện của mục "Exact target" đều thoả: đúng HEAD `R6`, nền là
ancestor, worktree sạch cả hai repo, và nhánh mặc định THẬT của Reports
(`claude/extract-upload-repo-gq2ws4`) đã được xác định bằng `git remote show`
chứ không giả định là `main` — nên không có chuyện review nhầm nhánh mặc định.
Tracking default chứa merge taxonomy `R5.1` `dc98910`.

Diff được review là `05f2b44…56aca4c`: 31 file, `+6800 / −6`. Sáu dòng xoá là
đúng ba dòng đã khai trong Scope Lock (chữ ký `_slot_title`, chuỗi đơn vị của
tooltip, một dòng liên kết trong `kinh_doanh.html`).

---

## 1. Chuỗi 1 — Effective data và phạm vi

### 1.1 `R6` không đọc Excel hay `ImportResult`

```text
$ grep -rn "openpyxl|ImportResult|raw_reader|read_raw_rows|load_workbook" \
    app/modules/reporting/{dashboard,product,basket}_metrics.py \
    app/modules/reporting/analysis_range.py \
    app/web/{product_taxonomy,dashboard_presentation}.py
  (không có kết quả)
```

Mọi route `R6` vào dữ liệu qua đúng một cửa: `service.period(...)` →
`PeriodData.details` (`app/web/server.py:3193-3196`). Dòng Owner đã loại và
dòng `R5` tạm loại KHÔNG nằm trong `PeriodData.lines/details` theo cấu tạo
(`business_service.py:411-433`), nên chúng không thể lọt vào một ô nào của
`R6` — không phải nhờ mỗi metric tự nhớ trừ ra.

Đo bằng hành vi, trên route thật, qua smoke xuyên hai repo:

```text
5) Dòng R5 tạm loại KHÔNG lọt vào một ô nào của R6
  ok   BH3 rời khỏi số đơn của R6
  ok   doanh thu R6 giảm đúng phần của BH3
  ok   ...và trang vẫn ĐỐI SOÁT khớp
  ok   BH3 cũng biến khỏi bảng kê drill-down
```

### 1.2 `ky` và `Từ ngày/Đến ngày` không giao, không cộng

Đo trên SERVER FLASK THẬT (`app.run()`, cổng 8971, gọi bằng HTTP), dữ liệu có
1 đơn tháng 8 và 4 đơn tháng 9:

```text
1a ky=2026-09
     scope-label[PERIOD]  |  orders='4'  |  sales_revenue='28.300'
1b custom 05-06/09
     scope-label[CUSTOM]  |  orders='2'  |  sales_revenue='18.300'
1f custom T8 trong khi ky=T9
     scope-label[CUSTOM]  |  orders='1'  |  sales_revenue='7.000'
```

`1f` là phép đo quyết định: nếu hai phạm vi bị GIAO nhau kết quả phải là `0`
đơn; nếu bị CỘNG GỘP phải là `5` đơn. Kết quả `1` đơn / `7.000` nghìn = đúng
phần tháng 8 và chỉ phần tháng 8. Không giao, không cộng.

### 1.3 Khoảng ngày hỏng bị TỪ CHỐI kèm lý do, không im lặng

```text
1c dao nguoc      scope-label[PERIOD] | scope-rejected='Từ ngày nằm SAU Đến ngày…'
1d thieu mot dau  scope-label[PERIOD] | scope-rejected='Khoảng ngày tự chọn cần ĐỦ hai đầu…'
1e dinh dang hong scope-label[PERIOD] | scope-rejected='Khoảng ngày tự chọn không đọc được…'
```

Ba lý do KHÁC NHAU cho ba cách hỏng khác nhau, và cả ba đều rơi về phạm vi kỳ
với con số của phạm vi kỳ (`orders='4'`, `sales_revenue='28.300'`) — không có
đường nào để một khoảng ngày hỏng âm thầm trả số của một khoảng khác.

### 1.4 `CUSTOM` không mượn trạng thái chốt kỳ

Bốn lớp chặn, đo từng lớp:

```text
resolve(CUSTOM)      → kind=CUSTOM period=None period_value=''
AnalysisRange(...)   → ValueError: phạm vi CUSTOM KHÔNG mang `period`:
                       một khoảng ngày tự chọn không có trạng thái chốt kỳ để mượn
business_service     → closed=(None if period is None …)
template R6          → grep "closed|chốt|period_lock" trong 5 template R6:
                       KHÔNG có — trang R6 không tuyên bố trạng thái chốt kỳ nào
```

**Chuỗi 1: PASS.**

---

## 2. Chuỗi 2 — Tổng tiền, SL, chiết khấu và số đơn

### 2.1 Bất biến số đơn ở CẢ NĂM mức gộp

Probe dựng tay 5 đơn: một đơn hai ngày (05/09 và 20/09), một đơn không ngày,
ba đơn rải các năm/quý khác nhau.

```text
  ngay    : sum(bucket)=4 + khong ngay=1 = 5  vs totals.orders=5  OK
  tuan    : sum(bucket)=4 + khong ngay=1 = 5  vs totals.orders=5  OK
  thang   : sum(bucket)=4 + khong ngay=1 = 5  vs totals.orders=5  OK
  quy     : sum(bucket)=4 + khong ngay=1 = 5  vs totals.orders=5  OK
  nam     : sum(bucket)=4 + khong ngay=1 = 5  vs totals.orders=5  OK
  don nhieu ngay ban (dem rieng) = 1
  BH1 (5/9 va 20/9) roi vao moc: ['2026-09-05']   (ky vong: 2026-09-05)
```

Một đơn nhiều ngày vào ĐÚNG ngày nhỏ nhất, đếm đúng một lần, và được đếm
riêng ở `orders_with_multiple_sale_dates`.

### 2.2 Doanh thu, chiết khấu, hai chỉ tiêu số lượng

`sales_revenue` đọc thẳng `BusinessLine.total_sales`
(`dashboard_metrics.py:totals`) — không một nhánh nào tính lại
`sell_price × quantity − discount`. `discount_total` cộng
`BusinessLine.discount` đúng một lần ở cấp dòng. `gross_before_discount` là
`@property` DẪN XUẤT và trả `None` khi `sales_revenue is None`.

`total_quantity` (mọi dòng có SL) là một trường MỚI đứng cạnh
`BusinessTotals.qualifying_quantity` (chỉ dòng đơn giá > 1.000.000); không
trường nào bị đổi nghĩa. `TotalsReconciliation` cố ý KHÔNG so hai con số ấy
với nhau và nói ra lý do.

Phép đối soát `dashboard_metrics ↔ business_metrics` chạy thật ở mỗi lần tải
trang, và được chứng minh là BẮT ĐƯỢC lỗi
(`tests/test_r6_dashboard_metrics.py`, 28 passed).

### 2.3 Giá bình quân gia quyền và giá 0 của hàng tặng

```text
  gia quyen = 495049.50    (TB don gia se la 15100000 — sai hoan toan)
  min voi hang tang gia 0 = 0        (ky vong 0 — OD-4)
  dong khong don gia: min=None max=None   (vang mat KHAC 0)
```

Giá bình quân là `Σ doanh thu / Σ SL`, không phải trung bình các đơn giá. Giá
0 của hàng tặng là giá THẬT và vẫn tham gia `min`. Dòng không có đơn giá
không kéo `min` xuống 0.

### 2.4 Engine thời gian

```text
   ngay     Ngày         size=30
   tuan     Tuần         size=12
   thang    Tháng        size=12
   quy      Quý          size=8
   nam      Năm          size=None
```

Đúng `30 / 12 / 12 / 8` của brief, và mức Năm không có cửa sổ so sánh — trang
NÓI RA điều đó thay vì để trống (`data-metric="chart-year-level"`).
`git diff --stat -- app/web/revenue_timeline.py` RỖNG: `R6` không sửa một
dòng nào của engine `R5`.

**Nhưng DỮ LIỆU nạp vào engine ấy thì sai — xem `FIND-R6-IR-01` §7.1, và
`AR-R6-IR-03` §7.3 cho mẫu số của giá bình quân. Chuỗi 2: `REPAIR_REQUIRED`.**

---

## 3. Chuỗi 3 — Product, hãng và nhóm hàng

### 3.1 `product_key` là khoá phân tích duy nhất

`product_bucket()` đặt `key = detail["product_key"]` cho MỌI dòng, kể cả dòng
chưa xác định — nên bảng mặt hàng không bao giờ dồn nhiều mặt hàng vào một ô
"chưa xác định". Không có khoá normalize thứ hai trong toàn bộ diff.

### 3.2 Metadata chỉ đến từ Tracking qua identity đã CONFIRMED

Ba nguồn, và chỉ ba: `line_identity.state_of`,
`identity_gateway.confirmed_identities`, `catalog_display.read`. Không nhánh
nào nhận `product_raw` làm đầu vào PHÂN LOẠI — `product_bucket` chỉ dùng chuỗi
đó làm NHÃN ĐỐI CHIẾU của một hàng ĐÃ tự khai là chưa xác định; `brand_bucket`
và `category_bucket` không nhận `detail` chút nào (chữ ký chỉ có
`LineMetadata`), nên ranh giới đúng theo CẤU TẠO.

### 3.3 Năm bucket, năm lý do, năm chỗ sửa

`UNDECIDED_ORDER` = `UNRESOLVED`, `CONFLICT`, `STALE_TARGET`,
`OUT_OF_CATALOG`, `METADATA_ABSENT`; mỗi bucket có `label` + `reason` riêng và
`GroupBucket.__post_init__` NÉM LỖI nếu một bucket `UNDECIDED` không kèm lý
do. Tiền không rời bucket nào: `product_metrics.reconciliation` so BẰNG ĐÚNG
trên `Decimal` bốn chỉ tiêu cộng được, và nó khớp trên route thật
(`data-reconciled="yes"`).

### 3.4 Đổi bucket không đổi tổng công ty

```text
  ok   đổi nhóm hàng bên Tracking hiện ra ngay ở lần đọc sau
  ok   ...và KHÔNG đổi một đồng, một cái, một BH nào
  ok   tổng tiền/SL/đơn KHÔNG đổi sau khi nhóm hàng xuất hiện
```

### 3.5 Taxonomy Owner đã chốt

Nguồn canonical nằm ở Tracking, không phải Reports:

```text
$ sed -n 683,690p /home/user/Tracking/src/index.js
const NHOM = [
  ['Tivi',              ['TV', 'Ti vi']],
  …
  ['Máy giặt',          ['Máy giặt sấy']],
  …
  ['Điều hoà',          ['Máy lạnh']],
```

Cả ba quyết định Owner có mặt: `Máy lạnh → Điều hoà`, `TV`/`Ti vi → Tivi`,
`Máy giặt sấy → Máy giặt`. Trong Reports, hai lần xuất hiện duy nhất của các
chuỗi ấy là NỘI DUNG CHÚ THÍCH hiển thị
(`product_taxonomy.CATEGORY_TAXONOMY_NOTE`), không phải một bảng ánh xạ —
Reports không giữ bản sao từ điển.

**Chuỗi 3: PASS.**

---

## 4. Chuỗi 4 — Basket

### 4.1 Bốn chỉ tiêu là bốn tập đơn khác nhau

```text
  ok   BH1 là đơn nhiều mặt hàng; BH2 có dịch vụ kèm
  ok   đơn nhiều dòng đếm cả BH1 lẫn BH2
  ok   phí KHÔNG làm tăng ô nhiều nhóm hàng hoá: chỉ BH1 được đếm
  ok   attachment có HAI cột riêng
```

`OrderBasket.products/categories` là `frozenset`, nên một mã lặp hai dòng chỉ
là MỘT thành viên và không tự tạo cặp với chính nó
(`tests/test_r6_basket_metrics.py`, 16 passed; và
`test_a_repeated_product_line_never_creates_a_pair` trên route thật).

`_pairs()` giữ hai mẫu số riêng (`orders_with_left`, `orders_with_right`) và
`pair_revenue` cộng `basket.revenue` — doanh thu TOÀN BỘ đơn — đúng một lần
cho mỗi đơn.

### 4.2 Bucket "Chưa xác định" trong Basket — đo trực tiếp

Đây là mục người review được yêu cầu kiểm RÕ. Kết quả tách làm ba phần.

**Tiền: GIỮ ĐỦ.** `pair_revenue` của cặp chứa bucket chưa xác định bằng đúng
tổng doanh thu hiệu lực của các đơn ấy, cộng mỗi đơn một lần; bảng cơ cấu
cùng dữ liệu vẫn `data-reconciled="yes"`.

**Nhãn: HIỆN RÕ.** Chuỗi đầy đủ đi lên ô, không bị rút gọn:
`Chưa xác định — chưa khớp mã Tracking`, `Chưa xác định — xung đột mã`.

**UI: CÓ THỂ ĐỌC NHẦM — xem `FIND-R6-IR-02` §7.2.** Bằng chứng route thật
(qua producer Tracking thật, capture thật, phân loại qua ĐÚNG route `POST` của
`R2`/`R5`, rồi mở trang giỏ hàng):

```text
===== BANG CAP THEO NHOM HANG, sau khi BH1 co MOT dong da khop =====
  O 'Don nhieu nhom hang hoa' = 1
    [Tivi] x [Chưa xác định — chưa khớp mã Tracking]  support=1  A->B=50%  DT=16.000
  co nhan 'chua xac dinh' rieng trong bang cap: False
```

Và ở mức module, khi một đơn có hai lý do chưa xác định KHÁC NHAU:

```text
  categories cua BHX = ['Tivi', '__CONFLICT__', '__UNRESOLVED__']
  multi_merchandise_category_orders = 2 / 2 don
  ty le 'don nhieu nhom hang hoa' = 100.00%
  Bang CAP theo nhom hang (min_support=1, mac dinh cua route):
    [Tivi]  x  [Chưa xác định — xung đột mã]                        support=2
    [Tivi]  x  [Chưa xác định — chưa khớp mã Tracking]              support=2
    [Chưa xác định — xung đột mã] x [Chưa xác định — chưa khớp mã Tracking]
                                     support=2  A->B=100.00%  B->A=100.00%
  Khoa dict mot hang cua bang cap:
    ['attachment_left','attachment_right','left','left_label',
     'orders_with_left','orders_with_right','pair_orders','pair_revenue',
     'right','right_label','support']
```

**Chuỗi 4: `REPAIR_REQUIRED` ở đúng một điểm (`FIND-R6-IR-02`); phần tiền,
cặp, attachment và `pair_revenue`: PASS.**

---

## 5. Chuỗi 5 — Web, drill-down và riêng tư

### 5.1 Chạy ROUTE FLASK THẬT, không chỉ test client

Dựng `create_app()` rồi `app.run(host="127.0.0.1", port=8971)`, gọi bằng
`curl`/HTTP thật. Dữ liệu mang ĐẦY ĐỦ tên khách, số điện thoại và địa chỉ
trên từng dòng.

```text
200  KHONG RO KHACH HANG  /kinh-doanh/phan-tich?ky=2026-09
200  KHONG RO KHACH HANG  /kinh-doanh/phan-tich/co-cau?ky=2026-09
200  KHONG RO KHACH HANG  /kinh-doanh/phan-tich/co-cau?ky=2026-09&chieu=nhom-hang
200  KHONG RO KHACH HANG  /kinh-doanh/phan-tich/co-cau?ky=2026-09&chieu=hang
200  KHONG RO KHACH HANG  /kinh-doanh/phan-tich/nhan-vien?ky=2026-09
200  KHONG RO KHACH HANG  /kinh-doanh/phan-tich/gio-hang?ky=2026-09
200  KHONG RO KHACH HANG  /kinh-doanh/phan-tich/gio-hang?ky=2026-09&chieu=nhom-hang
200  KHONG RO KHACH HANG  /kinh-doanh/phan-tich/don-hang?ky=2026-09
```

Bảy chuỗi được quét trên từng trang: `Nguyễn Thị Hoa`, `0912000111`,
`12 Lê Lợi`, `Trần Văn Bảy`, `0987654321`, `Phạm Văn Dũng`, `0933444555`.
KHÔNG chuỗi nào xuất hiện. Hàng rào giữ bằng CẤU TẠO:
`dashboard_presentation.drilldown_rows` trả dict có ĐÚNG bốn khoá
(`order_key`, `sale_date`, `employee`, `product`), nên không template nào
render được một trường khách hàng kể cả khi `details` mang sẵn.

### 5.2 Drill-down giữ đúng phạm vi

```text
   ky=2026-09                                    kind=PERIOD  don=4
   ky=2026-09&tu-ngay=2026-09-05&den-ngay=2026-09-05   kind=CUSTOM  don=1
   ky=2026-09&tu-ngay=2026-08-01&den-ngay=2026-08-31   kind=CUSTOM  don=1
```

### 5.3 Không route GHI, không migration, không bảng mới

```text
$ git diff 05f2b44 56aca4c -- app/web/server.py | grep "^+.*@app\."
+    @app.get("/kinh-doanh/phan-tich")
+    @app.get("/kinh-doanh/phan-tich/co-cau")
+    @app.get("/kinh-doanh/phan-tich/nhan-vien")
+    @app.get("/kinh-doanh/phan-tich/gio-hang")
+    @app.get("/kinh-doanh/phan-tich/don-hang")

$ số route POST:  05f2b44 → 18      56aca4c → 18   (KHÔNG đổi)

$ git diff --stat 05f2b44 56aca4c -- tools/db/ alembic.ini "*/migrations/*"
  (rỗng)
$ alembic heads
0009_line_binding_period_close (head)        ← đúng MỘT head, của R3

$ POST /kinh-doanh/phan-tich            → 405
$ POST /kinh-doanh/phan-tich/gio-hang   → 405
$ POST /kinh-doanh/phan-tich/don-hang   → 405
```

Không module nào ngoài chính đường trình bày của `R6` (`app/web/server.py`)
import `dashboard_metrics` / `product_metrics` / `basket_metrics` /
`product_taxonomy` / `dashboard_presentation` / `analysis_range` — không có
tầng dưới nào tiêu thụ `R6`. Không taxonomy thứ hai, không store quyết định
thứ hai, không API ngoài.

### 5.4 Độ bền tham số URL

12 tổ hợp tham số hỏng/lạ (`ky=abc`, `ky=9999-99`, `muc=khong-co`,
`chieu=khong-ton-tai`, `nhan-vien=KhongTonTai`, `a=`/`b=` không tồn tại,
`tu-ngay=2026-13-45`, …) đều trả `200` — không route nào `500`.

**Chuỗi 5: PASS.**

---

## 6. Chuỗi 6 — Bất biến `R1`–`R5.1`

### 6.1 Diff không chạm đường tiền đã nghiệm thu

```text
$ git diff --stat 05f2b44 56aca4c -- app/modules/pricing/ app/modules/profit/ \
    app/modules/kpi/ app/web/period_lock.py app/web/business_store.py \
    app/web/revenue_timeline.py app/web/business_queries.py \
    app/web/business_service.py tools/db/migrations/ config/
  (rỗng)
```

MIN theo ngày bán, giá nhập, lợi nhuận, coverage, period lock, fingerprint và
target engine: KHÔNG file nào bị chạm.

### 6.2 Full regression `R1`–`R5.1`

```text
$ .venv/bin/python -m pytest -q
3397 passed, 12 skipped in 178.04s (0:02:58)
```

`0 failed`. Trong lần chạy ĐẦU trên clone mới có 1 bài đỏ:

```text
FAILED tests/test_105d_boundaries.py::TestG25GoldenBaselineUnchanged::
       test_protected_golden_artifacts_match_the_task_105e_review_base
E   AssertionError: fatal: bad object 740f396acb11cf279f303f09ea22dffd0ca95462
```

Đây là lỗi BASELINE của môi trường (clone nông thiếu object), KHÔNG phải lỗi
của `R6`. Xác minh trực tiếp:

```text
$ git fetch origin 740f396acb11cf279f303f09ea22dffd0ca95462
$ git cat-file -t 740f396
commit
$ .venv/bin/python -m pytest -q tests/test_105d_boundaries.py
41 passed in 0.24s
```

12 skip đều có lý do môi trường in ra nguyên văn (`botocore` chưa cài — đây là
skip DUY NHẤT lệch so với `S143`, vốn ghi 11 skip; hai lần chạy có cùng TỔNG
3409 bài — `GOLDEN_RAW_01`/`GOLDEN_RAW_06` chưa đặt, và các field kiểu của
`R1A`).

### 6.3 Smoke `R5.1` và smoke xuyên hai repo `R6`

```text
$ .venv/bin/python scripts/r51_crossrepo_smoke.py --tracking /home/user/Tracking
KẾT QUẢ SMOKE: 63 PASS, 0 FAIL

$ .venv/bin/python scripts/r6_crossrepo_smoke.py --tracking /home/user/Tracking
KẾT QUẢ SMOKE: 24 PASS, 0 FAIL
```

`63` khớp đúng con số `S142` §4.5 đã ghi — `R6` không làm lệch một phép thử
xuyên repo nào của `R5.1`. Cả hai smoke chạy với producer Tracking THẬT
(`node v22.22.2`, `chieuBoard()` thật) trên `origin/main` = `66787c0`.

### 6.4 Validator governance và `git diff --check`

```text
GOVERNANCE STRUCTURE: PASS   (21 required paths)
PROJECT STATE:        PASS
EVIDENCE VALIDATION:  PASS   (161 REQUIRED PASS evidence records)
TASK COMPLETION:      PASS   (14 DONE tasks)
REFERENCE INTEGRITY:  4 reference không phân giải được
$ git diff --check 05f2b44 56aca4c   → rỗng (sạch)
```

Bốn reference đỏ thuộc `S136` (1) và `TASK-REM-T06` (3) — BASELINE, không
file nào của `R6` góp thêm. Trùng khớp với §4.3 của `S143`.

**Chuỗi 6: PASS.**

---

## 7. Finding

### 7.1 `FIND-R6-IR-01` — `REPAIR_REQUIRED`

**Cửa sổ so sánh của CẢ HAI biểu đồ trên trang phân tích vẽ SỐ 0 cho một
khoảng thời gian có doanh thu và số đơn THẬT.**

Nguyên nhân gốc, ở đúng hai hàm:

```text
app/web/server.py:_revenue_chart_for_scope   points = revenue_timeline.series(
app/web/server.py:_orders_chart                  view["data"].details, …)
```

Cả hai nạp vào `revenue_timeline.paired_series()` lát dữ liệu ĐÃ LỌC theo
phạm vi. Nhưng cửa sổ so sánh — theo định nghĩa — nằm NGOÀI phạm vi ấy. Trang
Báo cáo của `R5` tránh đúng điều này bằng một dòng có chủ ý
(`app/web/server.py:1257`):

```python
data = (view["data"] if view["period"] is None else _guarded(service.period))
```

tức nó ĐỌC LẠI toàn bộ dòng thời gian cho biểu đồ, không dùng lát của kỳ.

Hệ quả bị KHUẾCH ĐẠI bởi `revenue_timeline._covered_by_confirmed`: một mốc
không có điểm được vẽ thành `Decimal(0)` với `origin=ORIGIN_CURRENT` khi ngày
đó nằm trọn trong một sổ đã xác nhận đầy đủ. Và
`history_store.confirm_coverage` BẮT BUỘC khoảng xác nhận phải bao trọn dữ
liệu của snapshot:

```text
CoverageRangeError: Dữ liệu của snapshot có ngày nằm NGOÀI khoảng khai báo
(sớm nhất 2026-08-10). Khoảng xác nhận phải bao trọn dữ liệu đang có.
```

nên trên một sổ nhiều tháng đã xác nhận, cửa sổ liền trước KHÔNG thành khoảng
trống nhìn ra được — nó thành SỐ 0 CỨNG mang cờ "đã đo".

Bằng chứng E1, SERVER FLASK THẬT, cùng sổ, cùng kỳ, cùng mức gộp:

```text
$ curl http://127.0.0.1:8971/kinh-doanh?ky=2026-09&muc=ngay
   R5: Cửa sổ so sánh (liền trước) · 10/08/2026 — 7.000.000 đồng

$ curl http://127.0.0.1:8971/kinh-doanh/phan-tich?ky=2026-09&muc=ngay
   R6: Cửa sổ so sánh (liền trước) · 10/08/2026 — 0 đồng
   R6: Cửa sổ so sánh (liền trước) · 10/08/2026 — 0 đơn
```

```text
[BAO CAO  (R5) /kinh-doanh]
   cua so lien truoc: 2026-08-02..2026-08-31  n=30
   gia tri 10/08 = ['7000000']
   phan bo gia tri: {'0': 29, '7000000': 1}
[PHAN TICH (R6) /kinh-doanh/phan-tich]
   cua so lien truoc: 2026-08-02..2026-08-31  n=60
   gia tri 10/08 = ['0', '0']
   phan bo gia tri: {'0': 60}          ← 30 mốc doanh thu + 30 mốc số đơn
```

Sự thật trên sổ: 10/08/2026 có 1 đơn, 7.000.000 đồng.

Vì sao đây là `REPAIR_REQUIRED` chứ không phải `ACCEPTED_RISK`:

1. Nó vi phạm chính hợp đồng brief §3 — *"so với cửa sổ liền trước cùng độ
   dài"*. Trang vẫn ghi nhãn `Cửa sổ so sánh (liền trước) · 02/08 → 31/08` và
   vẫn dựng đủ 30 mốc; nó không từ chối vẽ, nó vẽ SAI.
2. Nó vi phạm luật `R5` mà `R6` tuyên bố dùng lại nguyên vẹn:
   *"số 0 CHỈ khi phạm vi đã được xác nhận đầy đủ, tức hệ thống thật sự biết
   không có đơn nào"* (`revenue_timeline.paired_series`). Ở đây hệ thống KHÔNG
   biết điều đó — nó chỉ không được đưa dữ liệu.
3. Nó tạo ra đúng lớp lỗi mà `dashboard_metrics` mở đầu bằng việc cấm: *"một
   trang phân tích cộng đúng số tiền mà trang Báo cáo vừa trừ ra — không màn
   hình nào cảnh báo, vì cả hai đều đúng theo nguồn của chính nó."* Hai trang
   cùng sản phẩm, cùng sổ, cùng ngày, hai con số.
4. Failure path của `R6` trong `REVIEW_BUDGET_LEDGER` kết thúc ở *"quyết định
   kinh doanh của Owner"*. Con số này đọc thành "tháng trước 0 đồng / 0 đơn,
   tháng này 17 triệu / 4 đơn" — một tín hiệu tăng trưởng BỊA, trên đúng trang
   được dựng để ra quyết định mua hàng. Brief §7 xếp "gộp sai khó phát hiện"
   vào nhóm BẮT BUỘC repair.

Vì sao không test nào bắt được: không một bài `tests/test_r6_*.py` nào chạm
tới `comparison` / `paired`. `CHECK-R6-13` chứng minh `R6` dùng ĐÚNG ENGINE
cửa sổ của `R5` — điều đó ĐÚNG và vẫn đúng — nhưng nó không nói gì về dữ liệu
được nạp vào engine ấy. Đây là khoảng trống giữa hai mệnh đề, không phải một
mệnh đề sai.

Hướng sửa (phiên review KHÔNG triển khai — đây là gợi ý, không phải chỉ thị
cài đặt): hoặc nạp cho hai biểu đồ lát dữ liệu KHÔNG lọc như trang Báo cáo
đang làm và giữ nhãn phạm vi trung thực; hoặc bỏ hẳn cửa sổ so sánh khi nó
rơi ra ngoài phạm vi và NÓI RA điều đó. Phương án thứ hai an toàn nhưng làm
trang mất khả năng trả lời chính câu brief §3 yêu cầu. Bài kiểm hồi quy tối
thiểu phải có: một mốc CÓ tiền thật trong cửa sổ liền trước, với sổ đã xác
nhận đầy đủ phủ cả hai cửa sổ.

### 7.2 `FIND-R6-IR-02` — `REPAIR_REQUIRED`

**Bucket "Chưa xác định" đứng làm MỘT NHÓM HÀNG HOÁ trong Basket, và bảng cặp
không phân biệt nó với một nhóm hàng thật.**

`category_bucket()` trả về `__UNRESOLVED__` / `__CONFLICT__` /
`__STALE_TARGET__` / `__OUT_OF_CATALOG__` / `__METADATA_ABSENT__` như thành
viên bình thường của `OrderBasket.categories`. Hai hệ quả đo được ở §4.2:

1. `multi_merchandise_category_orders` đếm một đơn là "nhiều nhóm hàng hoá"
   khi "nhóm" thứ hai chỉ là một dòng chưa phân loại. Chú thích của chính ô
   ấy liệt kê những gì KHÔNG được tính (*"Phí, chiết khấu, hoàn/hủy và chứng
   từ chưa định nghĩa"*) nhưng KHÔNG nói dòng chưa xác định thì ĐƯỢC tính —
   nên chú thích đang dẫn người đọc sai hướng.
2. Bảng cặp sinh ra hàng gợi ý bán chéo giữa HAI lý do chưa xác định:
   `[Chưa xác định — xung đột mã] × [Chưa xác định — chưa khớp mã Tracking]`,
   support 2, attachment 100 %/100 %.

Trả lời trực tiếp câu hỏi của mục review — *"đánh giá xem UI có thể khiến
người dùng hiểu nhầm đây là gợi ý cross-sell chính thức hay không"*: **CÓ.**
`dashboard_presentation.pair_rows` không chở `known` và không chở `reason`
(khác hẳn `group_rows`, vốn chở cả hai), và template render hai cột thành
`<td class="code">` y hệt một cặp thật. Khối "Cách đọc bảng này" có ba chú
thích (attachment, `pair_revenue`, support) và KHÔNG có chú thích nào về
bucket chưa xác định.

Ghi chú về vùng phủ: `scripts/r6_crossrepo_smoke.py` §4 có bài
`phí KHÔNG làm tăng ô nhiều nhóm hàng hoá: chỉ BH1 được đếm` — bài này XANH,
và mệnh đề của nó ĐÚNG. Nhưng trong chính lần chạy ấy `BH1` được đếm là nhiều
nhóm hàng hoá CHỈ VÌ một trong hai dòng của nó chưa khớp mã. Bài kiểm đúng
tên gọi của nó nhưng không đo được điều mà tên gọi gợi ra.

Phân loại `REPAIR_REQUIRED` chứ không `ACCEPTED_RISK`: tiền KHÔNG sai và
đối soát VẪN khớp, nhưng brief §7 liệt kê "gộp sai khó phát hiện" vào nhóm
bắt buộc repair, và đây đúng là một phép gộp sai — một trạng thái quy trình
được đếm như một nhóm hàng hoá, ngay trên hai bề mặt (ô tỉ lệ giỏ hàng và
bảng gợi ý bán kèm) mà Owner đọc để quyết định bán chéo.

### 7.3 `AR-R6-IR-03` — `RECOMMENDED` (không tự tiêu một repair cycle riêng)

**`PriceStats.average` chia một tử số đã loại dòng thiếu doanh thu cho một
mẫu số vẫn còn số lượng của chính dòng ấy.**

```python
merchandise_revenue = sum(revenues) if revenues else None   # bỏ dòng total_sales None
merchandise_quantity = sum(quantity của MỌI dòng hàng hoá có quantity)
```

```text
  merchandise_revenue=10000000  merchandise_quantity=2
  gia BQ = 5000000.00   ← hai dòng, mỗi dòng 1 chiếc giá 10.000.000,
                          một dòng chưa có total_sales
```

Giá bình quân bị hạ đúng một nửa so với giá duy nhất quan sát được.

Điểm nặng hơn con số: `dashboard_presentation.data_quality` in ra cho người
đọc rằng dòng chưa có doanh thu *"không được cộng như số 0 vào bất kỳ ô nào"*
— mệnh đề ấy SAI với đúng ô này. Trang đang khẳng định một bất biến mà mã
không giữ.

Tần suất bị chặn và nhìn thấy được: `lines_missing_revenue` đã có ô đếm
riêng. Sửa rẻ: loại khỏi mẫu số các dòng hàng hoá có `total_sales is None`,
hoặc trả `None`. Nếu Owner chọn giữ hành vi hiện tại, phải sửa câu chú thích
— không được để trang hứa một điều mã không làm.

### 7.4 `COR-R6-IR-01` — đính chính tài liệu (không tiêu ngân sách)

Docstring của `dashboard_presentation.drilldown_rows` dẫn một file test tên
`test_r6_drilldown_boundary` dưới `tests/` — file này KHÔNG tồn tại. Bài canh
thật là `tests/test_r6_dashboard_vertical.py`, hàm
`test_the_drilldown_never_renders_a_customer_field` (đã chạy trong phiên này,
PASS). Chỉ là một tham chiếu sai trong chú thích; 0 tác động hành vi.

---

## 8. Trạng thái sau review

```text
CHECK-R6-31   NOT_TESTED → FAIL (vòng 1, E1)
CHECK-R6-30   VẪN NOT_TESTED  — xem §9
CHECK-R6-32   VẪN NOT_TESTED  — phiên review KHÔNG tự đóng Owner Acceptance
CHECK-R51-26  VẪN NOT_TESTED

REPAIR_REQUIRED     2   FIND-R6-IR-01, FIND-R6-IR-02
RECOMMENDED         1   AR-R6-IR-03
Đính chính tài liệu 1   COR-R6-IR-01
Lỗi BASELINE tách ra 2  1 bài pytest (clone nông) + 4 reference integrity

Repair cycle tiêu bởi PHIÊN NÀY   0   (phiên review không sửa mã)
Repair cycle sẽ tiêu bởi REPAIR-1 1
Số dư R6 sau REPAIR-1             1 allowed / 1 used / 0 remaining
```

`R6` **KHÔNG được merge hay deploy**. Điều kiện §7 của task file chưa thoả:
`CHECK-R51-26` vẫn `NOT_TESTED` và `CHECK-R6-31` vừa `FAIL`.

**Cảnh báo ngân sách:** `R6` chỉ có `1 repair cycle`. Sau `REPAIR-1`, lineage
HẾT ngân sách. Nếu vòng Independent Review thứ hai lại ra `REPAIR_REQUIRED`,
`R6` KHÔNG được mở repair cycle thứ hai mà phải escalate theo
`governance/core/ESCALATION_PROTOCOL.md`. Vì thế `REPAIR-1` nên xử lý CẢ
`FIND-R6-IR-01`, `FIND-R6-IR-02`, `AR-R6-IR-03` và `COR-R6-IR-01` trong cùng
một vòng.

---

## 9. `CHECK-R6-30` — vì sao KHÔNG đóng được ở phiên này

Lệnh đã chạy đúng nguyên văn như yêu cầu:

```text
$ .venv/bin/python scripts/r6_book_reconciliation.py \
    --so /Users/hoangvinh/Downloads/So_chi_tiet_ban_hang.xlsx \
    --so-cua-owner --tmp /private/tmp/r6-independent-review-owner-book
KHÔNG TÌM THẤY SỔ: /Users/hoangvinh/Downloads/So_chi_tiet_ban_hang.xlsx
Đây KHÔNG phải một lỗi của R6 — file sổ kế toán không được commit vào repo
(DEC-108) và không có mặt trong môi trường này.
EXIT=2
```

`/Users/hoangvinh/Downloads/` là đường dẫn trên máy Owner; phiên này chạy
trong container Linux. `find / -iname "So_chi_tiet_ban_hang*"` không trả kết
quả nào. Không có cách trung thực nào để đóng `CHECK-R6-30` từ đây, và phiên
này KHÔNG bịa ra một lần chạy.

Điều phiên này LÀM ĐƯỢC — và đã làm — là kiểm rằng khi Owner chạy đúng lệnh
ấy, kết quả có nghĩa. Công cụ được chạy trên một sổ dựng đúng tám đặc trưng
của vector Owner, đi qua ĐÚNG pipeline production (`demo.run_demo` →
`history_writer` → `PeriodData` → `dashboard_metrics`):

```text
$ .venv/bin/python scripts/r6_book_reconciliation.py --so <sổ tổng hợp> --so-cua-owner

Chỉ tiêu                                       Nguồn         Aggregate           Kỳ vọng  Kết quả
----------------------------------------------------------------------------------------------------
Dòng nguồn (có Số BH)                            466               466               466  OK
Số BH khác nhau                                  345               345               345  OK
BH có doanh thu sau CK dương                     338               338               338  OK
Tổng SL                                          626               626               626  OK
Doanh số bán (dẫn xuất)                4,500,085,001     4,500,085,001     4,500,085,001  OK
Chiết khấu                                 1,550,000         1,550,000         1,550,000  OK
Doanh thu sau CK                       4,498,535,001     4,498,535,001     4,498,535,001  OK
BH có ít nhất hai dòng                            85                85                85  OK
----------------------------------------------------------------------------------------------------
KẾT QUẢ ĐỐI SOÁT: KHỚP TOÀN BỘ
EXIT=0
```

Ba cạnh (nguồn ↔ aggregate ↔ vector kỳ vọng) so BẰNG ĐÚNG trên `Decimal`,
không ngưỡng dung sai; công cụ trả `EXIT=1` khi lệch và `EXIT=2` khi thiếu
file, nên nó phân biệt được "hệ thống sai" với "chưa chạy được". Công cụ có
bài kiểm âm (`test_the_harness_reports_the_exact_metric_that_drifted`) nên nó
không xanh một cách vô nghĩa. Cột `Lợi nhuận` của Excel không được đọc.

Chiết khấu được cộng ĐÚNG MỘT LẦN: hai tầng tính doanh thu sau CK bằng hai
đường độc lập (`nguồn`: `Σ doanh số bán − Σ chiết khấu`; `aggregate`:
`Σ BusinessLine.total_sales`) và gặp nhau ở cùng `4.498.535.001`.

`CHECK-R6-30` vẫn `NOT_TESTED`. Owner chạy đúng một lệnh trên máy mình để
đóng nó — nhưng nên chạy SAU `REPAIR-1`, để lần đối soát nằm trên HEAD đã sửa.

---

## 10. Ghi chú môi trường

```text
Python 3.11.15 · node v22.22.2 · SQLite in-memory
.venv dựng mới trong phiên (pip install -e ".[dev,web,history]")
botocore KHÔNG cài  → 1 test skip thêm so với S143 (11 → 12 skip)
Server Flask thật: app.run(127.0.0.1:8971), gọi bằng curl/urllib
```

Phiên KHÔNG sửa một dòng mã sản phẩm nào, KHÔNG merge, KHÔNG deploy, KHÔNG
triển khai `R7`, KHÔNG mở rộng phạm vi `R6`, và KHÔNG tự đánh dấu Owner
Acceptance. Toàn bộ probe được viết trong thư mục scratchpad ngoài repo và
không có file dữ liệu khách hàng nào được tạo ra hay in ra.
