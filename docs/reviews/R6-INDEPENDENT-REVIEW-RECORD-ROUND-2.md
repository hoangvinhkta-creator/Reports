# `R6` — INDEPENDENT REVIEW RECORD, VÒNG 2 (bằng chứng nguyên văn)

Artifact Type:
INDEPENDENT REVIEW RECORD — vòng 2 của `CHECK-R6-31`, trên HEAD SAU `REPAIR-1`.

Executed By:
Phiên Independent Review `S146` (Claude Code, nhánh
`claude/r6-independent-review-round-2-dycl6b`).

Timestamp:
2026-09-09

Status:
`PASS`

Evidence Level:
E1 — mọi con số dưới đây là output nguyên văn của lệnh đã thực thi TRONG chính
phiên này. Phiên KHÔNG trích lại một con số nào từ `S143`, `S144` hay `S145`;
khi một con số của các phiên ấy được nhắc tới, nó được nhắc để ĐỐI CHIẾU, và
lần đo lại nằm ngay cạnh.

Vòng 1: `docs/reviews/R6-INDEPENDENT-REVIEW-RECORD.md` (`REPAIR_REQUIRED`).
Repair: `docs/sessions/S145-r6-repair-1.md`.
Tóm tắt cho người đọc nhanh: `docs/sessions/S146-r6-independent-review-round-2.md`.

---

## 0. Preflight — đúng đối tượng, đúng nền, đúng lineage

Phiên KHÔNG tin một SHA nào trong bàn giao `S145`; mọi mốc dưới đây được đo
lại bằng `git` trong phiên này.

```text
$ git remote show origin | grep "HEAD branch"
  HEAD branch: claude/extract-upload-repo-gq2ws4

$ git fetch origin claude/r6-business-analytics-dashboard-it73x5
$ git rev-parse FETCH_HEAD
40807efd50e675b71ccd1a14b5801394da4cafc1

$ git checkout --detach 40807efd50e675b71ccd1a14b5801394da4cafc1
$ git rev-parse HEAD
40807efd50e675b71ccd1a14b5801394da4cafc1
$ git status --porcelain | wc -l
0
```

Nhánh mặc định THẬT của Reports được xác định bằng `git remote show origin`
chứ không giả định là `"main"` — nó KHÔNG phải `main`.

### 0.1 Lineage — bốn mốc, đo bằng `git`, không tin bàn giao

```text
$ git log --oneline -6 --no-decorate
40807ef R6 REPAIR-1: ghi nhận INTEGRATION_DECISION_REQUIRED, cần Owner quyết
419391c R6 REPAIR-1: sửa cả 4 finding Independent Review vòng 1, một repair cycle
b3fa809 S144: Independent Review R6 — REPAIR_REQUIRED (CHECK-R6-31 = FAIL)
56aca4c R6: dọn ranh giới module — sum_optional công khai, bỏ import cục bộ
0adb6d1 R6: dashboard phân tích kinh doanh — 5 package, IMPLEMENTED
05f2b44 S142: điền SHA merge commit thật sau khi hai PR đã merge

$ for s in 05f2b44 56aca4c b3fa809 419391c; do
      git merge-base --is-ancestor $s 40807ef && echo "$s ancestor: YES"; done
  05f2b44 ancestor: YES        ← nền (nhánh mặc định)
  56aca4c ancestor: YES        ← R6 implementation đã review ở vòng 1
  b3fa809 ancestor: YES        ← bản ghi review vòng 1
  419391c ancestor: YES        ← REPAIR-1 (mã)
```

Chuỗi `56aca4c → b3fa809 → 419391c → 40807ef` được xác nhận ĐÚNG như đề bài
mô tả, và nền `05f2b44` vẫn là ancestor.

### 0.2 Tracking — dependency, KHÔNG có thay đổi `R6`

```text
$ git -C /home/user/Tracking remote show origin | grep "HEAD branch"
  HEAD branch: main
$ git -C /home/user/Tracking rev-parse origin/main
66787c0fb0d867a308c632e7f163cddd0c9dd0f2
$ git -C /home/user/Tracking checkout --detach 66787c0…
$ git -C /home/user/Tracking status --porcelain | wc -l
0
$ git -C /home/user/Tracking diff --stat origin/main HEAD
  (rỗng — không lệch một byte nào so với nhánh mặc định)
```

### 0.3 Branch authority (V4.1 Machine Control #1)

```text
$ TARGET_SHA=40807efd50e675b71ccd1a14b5801394da4cafc1 \
    bash scripts/branch_authority_check.sh
DEFAULT_BRANCH       : claude/extract-upload-repo-gq2ws4
DEFAULT_TIP          : 05f2b443e66ee4702d03c003d5f1f960b5765f8d
HEAD_SHA             : 40807efd50e675b71ccd1a14b5801394da4cafc1
WORKTREE             : CLEAN
MODE                 : DETACHED
TARGET_SHA           : 40807efd50e675b71ccd1a14b5801394da4cafc1
AUTHORITY            : DETACHED_EXACT_TARGET
RESULT               : AUTHORITY_OK
```

Chạy KHÔNG có `TARGET_SHA` cho ra `STOP — BRANCH AUTHORITY UNRESOLVED`, đúng
như script quy định cho chế độ detached. Đây là hành vi đúng, không phải lỗi.

### 0.4 `INTEGRATION_DECISION_REQUIRED` — vẫn MỞ, phiên này KHÔNG tự đóng

`S145` §8b đã ghi nhận cờ này. Phiên này đo LẠI, và con số khớp:

```text
$ MB=$(git merge-base origin/claude/extract-upload-repo-gq2ws4 40807ef)
05f2b443e66ee4702d03c003d5f1f960b5765f8d
$ git diff --numstat $MB..40807ef | awk '{a+=$1; d+=$2} END {print a, d, a+d}'
  added=10148  deleted=7  cumulative LOC=10155      ← ngưỡng V4.1 §8 là 5.000
```

`10.155` so với `10.098` mà `S145` ghi: chênh đúng `57` dòng của chính commit
tài liệu `40807ef`, tức `S145` đo tại `419391c`. Không có mâu thuẫn.

**Cờ `INTEGRATION_DECISION_REQUIRED` vẫn MỞ.** Owner phải chọn (A) integrate
sớm, (B) cắt scope, hay (C) tiếp tục divergence có lý do + ngày review. Phiên
review KHÔNG có thẩm quyền chọn thay, và KHÔNG chọn.

---

## 1. `R6` vẫn là READ-ONLY — đo lại từ đầu

### 1.1 Không migration, không bảng mới

```text
$ .venv/bin/alembic heads
0009_line_binding_period_close (head)        ← đúng MỘT head, của R3

$ git diff --stat 56aca4c 40807ef -- tools/db/ alembic.ini "*/migrations/*"
  (rỗng)
$ git diff --stat 05f2b44 40807ef -- "*models*" "*schema*" tools/db/
  (rỗng)
```

### 1.2 Không route GHI

```text
$ số route POST trong app/web/server.py
  05f2b44 → 18      56aca4c → 18      40807ef → 18   (KHÔNG đổi)

$ grep "@app.(get|post)(\"/kinh-doanh/phan-tich"
  3340:    @app.get("/kinh-doanh/phan-tich")
  3403:    @app.get("/kinh-doanh/phan-tich/co-cau")
  3425:    @app.get("/kinh-doanh/phan-tich/nhan-vien")
  3510:    @app.get("/kinh-doanh/phan-tich/gio-hang")
  3544:    @app.get("/kinh-doanh/phan-tich/don-hang")
```

Đo bằng HTTP THẬT trên server Flask thật, không bằng đọc mã:

```text
POST /kinh-doanh/phan-tich            → 405
POST /kinh-doanh/phan-tich/co-cau     → 405
POST /kinh-doanh/phan-tich/nhan-vien  → 405
POST /kinh-doanh/phan-tich/gio-hang   → 405
POST /kinh-doanh/phan-tich/don-hang   → 405
```

### 1.3 Bất biến tiền — `git diff` RỖNG trên đường tiền

```text
$ git diff --stat 56aca4c 40807ef -- app/modules/pricing/ app/modules/profit/ \
    app/modules/kpi/ app/web/period_lock.py app/web/business_store.py \
    app/web/business_queries.py app/web/business_service.py \
    app/modules/reporting/business_metrics.py tools/db/migrations/ config/ \
    alembic.ini tools/db/
  (rỗng)

$ …cùng lệnh, nhưng từ NỀN 05f2b44 tới 40807ef
  (rỗng)
```

MIN theo ngày bán, giá nhập, lợi nhuận, KPI, coverage, period lock, fingerprint
và `PeriodData`: KHÔNG file nào bị chạm — không phải chỉ ở `REPAIR-1`, mà trên
CẢ lineage `R6`.

### 1.4 Tracking / product identity / period-close: không đổi

Tracking đã đo ở §0.2 (không lệch một byte). `product identity` (`app/modules/
product/identity/**`) và `period-close` (`app/web/period_lock.py`) nằm trong
tập `git diff` rỗng ở §1.3.

### 1.5 Toàn bộ file mà lineage `R6` chạm — 37 file, đều trong Scope Lock

```text
$ git diff --name-only 05f2b44 40807ef | wc -l
37
```

Danh sách đầy đủ đã đối chiếu với `docs/tasks/R6-dashboard-phan-tich-kinh-doanh.md`
§1 (bản ĐÃ đính chính ở `REPAIR-1`, tức đã khai `app/web/revenue_timeline.py`).
Không file nào nằm ngoài. Xem `OBS-R6-IR2-03` ở §7 cho một sai lệch ĐẾM (không
phải sai lệch phạm vi) còn sót trong văn bản Scope Lock.

### 1.6 Độ bền tham số URL

```text
40 tổ hợp tham số hỏng/lạ trên 4 route R6 (ky=abc, ky=9999-99, muc=khong-co,
chieu=khong-ton-tai, tu-ngay=2026-13-45, thiếu một đầu khoảng ngày, a=/b= rỗng,
nhan-vien=KhongTonTai, muc=, chieu=) → 200/200 trả 200. Không route nào 500.
```

---

## 2. `FIND-R6-IR-01` — cửa sổ so sánh. **ĐÃ SỬA.**

Toàn bộ mục này đo trên **server Flask THẬT** (`app.run(host="127.0.0.1")` trên
một cổng thật, gọi bằng `urllib` qua HTTP), KHÔNG dùng `test_client()`. Oracle
là trang Báo cáo `R5` `/kinh-doanh` trên **CÙNG server, CÙNG sổ, CÙNG kỳ, CÙNG
mức gộp** — đúng bề mặt và đúng phép so mà vòng 1 đã dùng để phát hiện lỗi.

Bốn probe độc lập, sổ do phiên này tự dựng (KHÔNG dùng lại fixture của
`REPAIR-1`), tổng **93 phép đo, 93 PASS, 0 FAIL**.

### 2.1 Probe 1 — sổ ba tháng, coverage đã xác nhận (41 PASS / 0 FAIL)

Sổ: 14/05 4.000.000 · 08/07 5.500.000 · **05/08 3.000.000** · **18/08
12.000.000 + 2.000.000 (HAI đơn)** · 10/09 20.000.000 · 22/09 5.000.000.
Coverage đã xác nhận đầy đủ `01/05/2026–30/09/2026` (điều kiện KHUẾCH ĐẠI mà
vòng 1 §7.1 mô tả: mốc rỗng trong khoảng đã xác nhận thành số `0` "đã đo").
`TODAY = 30/09/2026`, kỳ đang xem `2026-09`.

```text
oracle R5    05/08 = 3000000        18/08 = 14000000
R6 doanh thu 05/08 = 3000000        18/08 = 14000000      ← vòng 1: 0
R6 số đơn    05/08 = 1              18/08 = 2             ← vòng 1: 0
R6 == R5 trên TỪNG MỐC của cửa sổ so sánh (30/30 mốc)     OK
R6 == R5 trên TỪNG MỐC của cửa sổ hiện tại                OK
cửa sổ so sánh KHÔNG toàn 0 (doanh thu và số đơn)         OK
hai biểu đồ cắt CÙNG một cửa sổ (cùng tập mốc, cả hai vế) OK
```

Bốn mức gộp có cửa sổ so sánh, so TỪNG MỐC với `R5`:

```text
muc=ngay   R5 prev=30 mốc  R6 prev=30 mốc   khớp từng mốc   tiền vẽ 42.000.000
muc=tuan   R5 prev=10 mốc  R6 prev=10 mốc   khớp từng mốc   tiền vẽ 51.500.000
muc=thang  R5 prev=0  mốc  R6 prev=0  mốc   khớp từng mốc   tiền vẽ 51.500.000
muc=quy    R5 prev=0  mốc  R6 prev=0  mốc   khớp từng mốc   tiền vẽ 51.500.000
muc=nam    R6 NÓI RA "Mức gộp NĂM không có cửa sổ so sánh" và KHÔNG dựng
           một cửa sổ giả (`data-metric="chart-year-level"`; hành vi này có
           TỪ 56aca4c, `git show 56aca4c:…kinh_doanh_phan_tich.html` xác nhận)
```

Số `0` chỉ xuất hiện đúng chỗ nó được phép:

```text
06/08 (rỗng THẬT, nằm TRỌN trong coverage đã xác nhận)  → "0"      ĐÚNG
mốc TUẦN trước 01/05 (ngoài coverage)                    → VẮNG MẶT ĐÚNG
    21/24 mốc được vẽ; 3 mốc ngoài coverage là KHOẢNG TRỐNG, không phải 0
```

Luật `R5` KHÔNG bị nới: `0` vẫn chỉ có nghĩa "hệ thống thật sự biết không có
đơn nào", và ngoài khoảng xác nhận nó vẫn là khoảng trống.

Phạm vi tự chọn:

```text
?tu-ngay=2026-09-01&den-ngay=2026-09-15&muc=ngay
  mốc 22/09 KHÔNG có mặt                        ← không trôi theo dữ liệu mới nhất
  mốc cuối cửa sổ hiện tại = 2026-09-15         ← neo ĐÚNG vào `Đến ngày`
  10/09 = 20000000                              ← tiền thật trong cửa sổ hiện tại
  cửa sổ so sánh = 2026-07-18 … 2026-08-16      ← 30 ngày liền trước neo
  05/08 = 3000000                               ← tiền thật trong cửa sổ so sánh
?tu-ngay=2026-08-01&den-ngay=2026-08-10&muc=ngay
  mốc cuối cửa sổ hiện tại = 2026-08-10         ← lại neo đúng `Đến ngày`

service.period(2026-07-18 … 2026-09-15).closed is None    ← KHÔNG mượn chốt kỳ
trang custom KHÔNG in một trạng thái chốt kỳ nào
```

Ô chỉ tiêu / bảng / giỏ hàng / bảng kê VẪN chỉ đọc phạm vi đang xem:

```text
ô doanh thu  = 25.000.000 đồng   (chỉ tháng 9: 20.000.000 + 5.000.000)
ô số đơn     = 2
…và giữ NGUYÊN 25.000.000 ở muc=tuan, muc=thang, muc=quy — tức việc mở rộng
  dữ liệu nguồn của biểu đồ KHÔNG rò sang một ô chỉ tiêu nào
bảng cơ cấu  data-reconciled="yes"
giỏ hàng     KHÔNG hiện BH0805 / BH0708 (đơn ngoài phạm vi)
bảng kê      CÓ BH0910, BH0922; KHÔNG có BH0805 / BH0818 / BH0708
```

### 2.2 Probe 1b — sổ NHIỀU NĂM, để cửa sổ so sánh của THÁNG và QUÝ có tiền thật (32 PASS / 0 FAIL)

Probe 1 chỉ phủ được cửa sổ so sánh của `ngay`/`tuan`: ở `thang` cửa sổ so
sánh lùi 12 tháng và ở `quy` lùi 8 quý, nên với một sổ 5 tháng chúng RỖNG — và
một bài kiểm trên cửa sổ rỗng không chứng minh được điều cần chứng minh. Probe
này dùng sổ trải từ 2023.

```text
muc=thang   oracle R5  2025-03 = 10000000
            R6 doanh thu 2025-03 = 10000000      ← KHÔNG phải 0
            R6 số đơn    2025-03 = 2 đơn
            R6 khớp R5 từng mốc, cả hai cửa sổ
muc=quy     oracle R5  2023-Q4 = 8000000   2024-Q2 = 6000000
            R6 doanh thu 2023-Q4 = 8000000   2024-Q2 = 6000000
            R6 số đơn    2023-Q4 = 1 đơn    2024-Q2 = 1 đơn
            R6 khớp R5 từng mốc, cả hai cửa sổ
custom range muc=thang (01/01/2026 → 30/09/2026)
            cửa sổ so sánh 2025-03 = 10000000; neo = 2026-09 (đúng `Đến ngày`)
ô chỉ tiêu  20.000.000 đồng / 1 đơn — GIỮ NGUYÊN ở cả năm mức gộp
```

Ghi chú môi trường thành thật: `history_store.confirm_coverage` từ chối một
khoảng dài hơn `366` ngày, mà sổ này trải nhiều năm — nên probe 1b chạy KHÔNG
có xác nhận coverage. Mệnh đề nó đo là *"cửa sổ so sánh có tiền thật phải VẼ
RA tiền thật"*; lớp khuếch đại "`0` cứng" đã được probe 1 đo riêng, trên đúng
điều kiện có coverage.

### 2.3 Probe 1d — lát MỞ RỘNG vẫn là EFFECTIVE DATA (8 PASS / 0 FAIL)

Câu hỏi mà `REPAIR-1` mở ra và vòng 1 chưa có: lát dữ liệu mở rộng có phải
một cửa sau đưa dòng Owner đã loại quay lại biểu đồ không?

```text
sổ: 12/08 có HAI đơn — BH51 3.000.000 và BH52 5.000.000; 10/09 20.000.000
trước khi loại   R5 12/08 = 8000000   R6 12/08 = 8000000   R6 số đơn = 2
$ store.exclude_line(BH51)                       ← đường GHI thật của R5
sau khi loại     R5 12/08 = 5000000   R6 12/08 = 5000000   R6 số đơn = 1
muc=tuan/thang/quy: R6 vẫn khớp R5 từng mốc trên cả hai cửa sổ
```

Dòng bị loại nằm ở cửa sổ SO SÁNH, tức NGOÀI phạm vi đang xem — đúng vùng mà
chỉ lát mở rộng chạm tới. Nó KHÔNG quay lại.

### 2.4 Probe 1e — neo của phạm vi `PERIOD`, ba ca biên (12 PASS / 0 FAIL)

`REPAIR-1` đổi neo từ `anchor_date(period, details)` sang `scope.date_to`, và
tuyên bố hai giá trị ấy BẰNG NHAU với phạm vi `PERIOD`. Phiên này đo tuyên bố
đó ở ba ca dễ làm nó sai:

```text
today=2026-09-15  ky=2026-09  (kỳ HIỆN TẠI, đang giữa tháng)
today=2026-09-30  ky=2026-08  (kỳ QUÁ KHỨ)
today=2026-10-05  ky=2026-09  (kỳ VỪA XONG)
→ cả ba ca, cả bốn mức gộp (ngay/tuan/thang/quy): R6 khớp R5 TỪNG MỐC
  trên CẢ HAI cửa sổ. 12/12 PASS.
```

### 2.5 Kết luận `FIND-R6-IR-01`

Hình dạng lỗi mà vòng 1 ghi (`{'0': 60}` — 30 mốc doanh thu + 30 mốc số đơn
đều bằng `0` cho một khoảng có tiền thật) KHÔNG còn tái hiện được ở bất kỳ
mức gộp nào, bất kỳ loại phạm vi nào, trong bốn probe độc lập với bốn sổ khác
nhau. `R6` và `R5` nói CÙNG một con số cho CÙNG một mốc.

**`FIND-R6-IR-01` = ĐÃ SỬA.** `CHECK-R6-33` … `-39` được xác nhận độc lập.

---

## 3. `FIND-R6-IR-02` — bucket "Chưa xác định" trong Basket. **ĐÃ SỬA.**

Ba probe, tổng **51 phép đo, 51 PASS, 0 FAIL**.

### 3.1 Probe 2 — TOÀN TRANG, xuyên hai repo (27 PASS / 0 FAIL)

Danh mục nhóm hàng do **chính producer Tracking thật** sinh ra
(`node kiem/smoke/sinh-catalog-reports.mjs`, `node v22.22.2`), đi qua mã
capture thật, và các dòng được phân loại bằng **route POST thật** của `R2`/`R5`
(`/kinh-doanh/nhan-vien/phan-loai`). Không một bucket nào gõ tay.

```text
danh mục thật:  TV-01 = "Tivi"  (DEC-206 còn nguyên trên producer)
mã dùng:        tivi=55Q6FA   nhóm 2=MGS-01("Máy giặt")
                metadata-absent=BAN-01 (đã khớp mã, Tracking CHƯA xếp nhóm hàng)

sổ:  BH11  Tivi (chính danh) + một dòng CHƯA KHỚP MÃ
     BH12  HAI lý do chưa xác định KHÁC NHAU (METADATA_ABSENT + UNRESOLVED)
     BH13  Tivi + Máy giặt   (hai nhóm CHÍNH DANH)
     BH14  Tivi + Máy giặt   (hai nhóm CHÍNH DANH)
```

```text
ô "đơn nhiều nhóm hàng hoá"          = 2        ← chỉ BH13, BH14. Vòng 1: BH11
                                                  cũng bị đếm.
bảng cặp NHÓM HÀNG                   = [("Máy giặt", "Tivi")]   support 2
  không ô nào là "Chưa xác định"      OK
  mọi ô cặp nhóm hàng data-known="yes" OK
  cặp ["…xung đột mã"] × ["…chưa khớp mã"] của vòng 1: KHÔNG còn
UI nói ra phần bị loại:
  unknown-category-orders = 2         (BH11, BH12)
  unknown-category-lines  = 3
  data-metric="category-coverage-partial" HIỆN RA
  câu chữ: "KHÔNG được coi là một nhóm hàng hoá"
KHÔNG PII trên trang giỏ hàng và trang tổng quan:
  "Nguyễn Thị Hoa" / "0912000111" / "12 Lê Lợi"  → không xuất hiện
chiều SẢN PHẨM vẫn sinh cặp: [("FV1412", "QLED 55Q6FA")], có cờ data-known
tổng tiền / SL / số đơn TRƯỚC và SAU phân loại:
  {sales_revenue 48.000, discount_total 0, orders 4, total_quantity 8,
   gross_before_discount 48.000}  →  Y HỆT
bảng nhóm hàng data-reconciled="yes"
bucket chưa xác định VẪN còn nguyên trong bảng cơ cấu:
  ['Tivi', 'Máy giặt', 'Chưa xác định — chưa khớp mã Tracking',
   'Chưa xác định — Tracking chưa xếp']
đối soát bộ chỉ tiêu nghiệp vụ: data-reconciled="yes"
```

### 3.2 Probe 2b — DIFF trực tiếp `56aca4c` vs HEAD trên CÙNG đầu vào (14 PASS / 0 FAIL)

Bản `basket_metrics.py` của `56aca4c` được nạp từ `git show` thành một module
thứ hai và chạy song song với bản trên HEAD, trên ĐÚNG cùng một `index`. Đây
là phép đo trực tiếp nhất cho câu *"repair có đổi thứ gì ngoài phạm vi không"*.

```text
TRƯỚC repair   multi_merchandise_category_orders = 5   (CẢ 5 đơn)
SAU   repair   multi_merchandise_category_orders = 2

TRƯỚC repair   cặp nhóm hàng = [('Tivi','Tủ lạnh'),
                                ('Tivi','__UNRESOLVED__'),
                                ('__CONFLICT__','__UNRESOLVED__')]
SAU   repair   cặp nhóm hàng = [('Tivi','Tủ lạnh')]
phần bị để ngoài được ĐẾM RA: 3 đơn / 5 dòng

KHÔNG ĐỔI (so bằng đúng, cả hai bản):
  BasketCounts.orders                      5 → 5
  BasketCounts.multi_line_orders           5 → 5
  BasketCounts.multi_product_orders        5 → 5
  BasketCounts.service_attachment_orders   0 → 0
  ngữ nghĩa CẶP SẢN PHẨM — left/right/support/pair_orders/pair_revenue/
    order_keys giống hệt
  products / lines / merchandise_lines / revenue của TỪNG đơn
  TỔNG doanh thu của chỉ số giỏ hàng
cặp SẢN PHẨM vẫn GIỮ thành viên chưa xác định, chỉ mang cờ:
  [('pk-tivi', True, 'pk-tl', True), ('pk-x', False, 'pk-y', False)]
```

Ranh giới nằm ở ĐÚNG chiều nhóm hàng, và không ở đâu khác.

### 3.3 Probe 2c — CẢ NĂM lý do, và dòng phí (10 PASS / 0 FAIL)

```text
trạng thái đọc từ chính product_taxonomy.UNDECIDED_ORDER:
  ['UNRESOLVED', 'CONFLICT', 'STALE_TARGET', 'OUT_OF_CATALOG', 'METADATA_ABSENT']

mỗi lý do, ghép với MỘT nhóm chính danh:
  multi_merchandise_category_orders = 0
  unknown_category_lines = 1, orders_with_unknown_category = 1   (5/5 lý do)

CẶP giữa hai lý do bất kỳ — 10/10 tổ hợp, đo ở min_support=1 (khắt khe hơn
mặc định): KHÔNG sinh một cặp nào.

dòng PHÍ và dòng CHIẾT KHẤU:
  unknown_category_lines = 0            ← không bị đếm là "chưa xác định nhóm"
  multi_merchandise_category_orders = 0
  đơn vẫn giữ lines=3 và revenue=3.000.000   ← TIỀN của chúng không mất

phạm vi RỖNG → category_coverage_complete = False   (fail-closed, đúng kỷ luật
  đã freeze ở Coverage.is_complete)
```

### 3.4 Kết luận `FIND-R6-IR-02`

**`FIND-R6-IR-02` = ĐÃ SỬA.** `CHECK-R6-40` … `-48` được xác nhận độc lập.

---

## 4. `AR-R6-IR-03` — giá bán bình quân. **ĐÃ SỬA.**

**34 phép đo, 34 PASS, 0 FAIL.** Phần lớn là DIFF trực tiếp với bản
`product_metrics.py` của `56aca4c`, nạp song song từ `git show`.

### 4.1 Năm ca của phép chia

```text
ca 1 — THIẾU total_sales (chính ca của finding)
  hai dòng, mỗi dòng 1 chiếc giá 10.000.000, MỘT dòng chưa có total_sales
  TRƯỚC repair  giá BQ = 5.000.000,00      ← thấp đúng một nửa
  SAU   repair  giá BQ = 10.000.000,00     ← đúng giá duy nhất quan sát được
  priced_lines = 1, priced_quantity = 1
  min/max = 10.000.000 / 10.000.000, GIỐNG HỆT bản trước repair

ca 2 — THIẾU quantity
  giá BQ = 8.000.000,00 ; priced_lines = 1 ; priced_quantity = 2
  dòng thiếu số lượng KHÔNG vào cả hai vế, nhưng VẪN góp vào min/max
  (nó có một đơn giá quan sát được)

ca 3 — quantity == 0  (chiều NGƯỢC LẠI của cùng lớp lỗi)
  TRƯỚC repair  giá BQ = 6.500.000,00      ← dòng SL=0 đẩy giá LÊN
  SAU   repair  giá BQ = 5.000.000,00

ca 4 — HÀNG TẶNG giá 0
  giá BQ = 5.000.000,00 ; min = 0
  average / minimum / maximum: KHÔNG đổi một số nào so với trước repair
  (0 là giá bán THẬT — OD-4 — và nó vẫn tham gia cả hai)

ca 5 — BÌNH THƯỜNG
  một dòng 1 chiếc 30.000.000 + một dòng 100 chiếc 200.000
  giá BQ = 495.049,50 ; priced_quantity = 101
  TRƯỚC và SAU repair BẰNG NHAU
```

### 4.2 Mẫu số bằng 0 ⟹ `None` KÈM LÝ DO, không bao giờ `0`

```text
nhóm chỉ có phí          average = None, merchandise_lines = 0
                         average_reason = NO_AVERAGE_NO_MERCHANDISE
                         "Nhóm này không có dòng hàng hoá nào…"
có hàng hoá, chưa dòng nào đủ dữ liệu
                         average = None, merchandise_lines = 1
                         average_reason = NO_AVERAGE_NO_PRICED_LINE
                         "…Ô trống ở đây nghĩa là CHƯA TÍNH ĐƯỢC, không phải
                          bằng 0."
average != 0 ở cả hai ca
```

### 4.3 Min/max, Tổng SL nghiệp vụ và tổng doanh thu KHÔNG bị đổi sai

```text
lát trộn: 1 dòng đủ · 1 dòng thiếu doanh thu (SL 3) · 1 dòng SL=0 có doanh thu
          · 1 dòng hàng tặng giá 0 (SL 2)
total_quantity     = 6      ← ĐẾM MỌI dòng có số lượng (1+3+0+2), KHÔNG thu hẹp
sales_revenue      = 15.000.000
lines_missing_revenue = 1   ← vẫn được đếm riêng
GroupReconciliation(lines=True, sales_revenue=True, quantity=True,
                    discount=True)          → is_exact
tổng doanh thu các bucket == tổng của lát dữ liệu
trường cũ `merchandise_quantity` / `merchandise_revenue`: KHÔNG còn một tham
  chiếu nào trong app/, tests/, scripts/
```

### 4.4 Trên TRANG THẬT

```text
$ /kinh-doanh/phan-tich/co-cau?ky=2026-09&chieu=san-pham
  ba ô giá BQ: ['7.333.333,33', '—', '—']
  7.333.333,33 = (10.000.000 + 12.000.000) / 3 chiếc   ← gia quyền, đúng
  MỌI ô trống đều mang một `title=` giải thích vì sao nó trống
```

Và khi sổ CÓ dòng chưa chốt doanh thu, khối chất lượng dữ liệu nói đúng điều
mã làm — mệnh đề mà vòng 1 §7.3 chỉ ra là SAI nay đã đúng:

```text
"— Chưa biết doanh thu KHÁC doanh thu bằng 0 — chúng không được cộng như số 0
  vào bất kỳ ô nào, và cũng không tham gia MỘT VẾ NÀO của phép chia giá bán
  bình quân (repair AR-R6-IR-03)."
```

(Xem `OBS-R6-IR2-01` ở §7 về đuôi câu này.)

**`AR-R6-IR-03` = ĐÃ SỬA.** `CHECK-R6-49` … `-53` được xác nhận độc lập.

---

## 5. `COR-R6-IR-01` — đính chính tài liệu. **ĐÃ SỬA.**

```text
$ grep -n "test_the_drilldown_never_renders_a_customer_field" \
    tests/test_r6_dashboard_vertical.py
331:def test_the_drilldown_never_renders_a_customer_field(client, repository):
   → bài canh TỒN TẠI, và nó đo trên chính HTML đã render:
     html = body(client, f"{DRILLDOWN}?{SEPTEMBER_QS}")
     for leaked in ("Nguyễn Thị Hoa", "0912000111", "12 Lê Lợi, Q1"):
         assert leaked not in html

$ ls tests/test_r6_drilldown_boundary.py
   → No such file (đúng như đính chính nói)

$ grep -rn "test_r6_drilldown_boundary" --include="*.py" --include="*.html" \
      --include="*.md" .
   app/web/dashboard_presentation.py:397   ← chính câu ĐÍNH CHÍNH, nói rằng
                                             file đó KHÔNG tồn tại
   docs/sessions/S144-r6-independent-review.md:137   ← bản ghi LỊCH SỬ vòng 1
   (không còn một tham chiếu nào coi nó là bài canh thật)
```

Docstring đã trỏ ĐÚNG bài canh và không còn mô tả hành vi cũ.
**`COR-R6-IR-01` = ĐÃ SỬA.** `CHECK-R6-54` được xác nhận độc lập.
Xem `OBS-R6-IR2-02` ở §7 cho một lỗi CHÍNH TẢ còn sót trong chính câu ấy.

---

## 6. Regression và bằng chứng vận hành

### 6.1 Bộ kiểm

```text
$ .venv/bin/python -m pytest -q tests/test_r6_repair1_basket_and_price.py \
      tests/test_r6_repair1_chart_windows.py
48 passed in 2.94s

$ .venv/bin/python -m pytest -q tests/test_r6_*.py   (9 file)
186 passed in 12.23s

$ .venv/bin/python -m pytest -q          ← LẦN 1, clone còn nông
1 failed, 3444 passed, 12 skipped in 270.87s
FAILED tests/test_105d_boundaries.py::TestG25GoldenBaselineUnchanged::
       test_protected_golden_artifacts_match_the_task_105e_review_base
E   AssertionError: fatal: bad object 740f396acb11cf279f303f09ea22dffd0ca95462
```

Bài đỏ ấy là **BASELINE của môi trường**, không phải của `R6`. Ba bằng chứng
độc lập, đo trong phiên này:

```text
1. R6 KHÔNG chạm bài kiểm ấy hay artifact nó canh:
   $ git diff --stat 05f2b44 40807ef -- tests/test_105d_boundaries.py \
       tests/fixtures/golden/ tests/fixtures/baseline_snapshot.py
     (rỗng)
2. Clone NÔNG là nguyên nhân:
   $ git rev-parse --is-shallow-repository → true   ($ ls .git/shallow → có)
3. Chạy riêng file ấy → 41 passed in 0.29s
```

Bằng chứng dứt điểm: `scripts/branch_authority_check.sh` (chạy ở §0.3) thực
hiện một `git fetch origin --prune` ĐẦY ĐỦ. Chạy LẠI toàn bộ bộ kiểm SAU lần
fetch ấy, không đổi một dòng mã nào:

```text
$ .venv/bin/python -m pytest -q          ← LẦN 2, sau khi fetch đầy đủ
3445 passed, 12 skipped in 259.13s (0:04:19)
EXIT=0
```

`0 failed`. Bài đỏ ở lần 1 biến mất mà KHÔNG ai sửa gì — nó là trạng thái của
CLONE, không phải của mã. `3445 passed` khớp đúng con số mà `S145` đã ghi.

Cùng hình dạng, cùng nguyên nhân và cùng cách xác minh mà vòng 1 (`S144` §6.2)
đã ghi.

### 6.2 Smoke xuyên hai repo

```text
$ .venv/bin/python scripts/r6_crossrepo_smoke.py --tracking /home/user/Tracking
KẾT QUẢ SMOKE: 29 PASS, 0 FAIL

$ .venv/bin/python scripts/r51_crossrepo_smoke.py --tracking /home/user/Tracking
KẾT QUẢ SMOKE: 63 PASS, 0 FAIL
```

`63` khớp đúng con số `S142` §4.5 — `R6` và `REPAIR-1` không làm lệch một phép
thử xuyên repo nào của `R5.1`. `29` là con số SAU khi `REPAIR-1` sửa bài smoke
mà vòng 1 §7.2 chỉ ra là "đúng tên gọi nhưng không đo được điều tên gọi gợi
ra" — phiên này chạy lại và nó xanh trên đúng mệnh đề của nó (§3.1 đo lại điều
tương tự bằng probe riêng).

### 6.3 Tracking — dependency, chạy để chứng minh không bị vạ lây

```text
$ node kiem/chay.js          (trên HEAD = origin/main = 66787c0, worktree sạch)
62 bộ · 2892 đạt · 0 hỏng · 2 bỏ qua
Tất cả đạt.
```

### 6.4 `git diff --check` và validator governance

```text
$ git diff --check 56aca4c 40807ef     → rỗng (sạch)
$ git diff --check 05f2b44 40807ef     → rỗng (sạch)

GOVERNANCE STRUCTURE: PASS   (21 required paths, deployment root PASS)
PROJECT STATE:        PASS
EVIDENCE VALIDATION:  PASS   (161 REQUIRED PASS evidence records)
TASK COMPLETION:      PASS   (14 DONE tasks)
REFERENCE INTEGRITY:  4 reference không phân giải được (quét 298 file .md)
  - docs/sessions/S136-r5-integration.md -> /tmp/…/r5_repair_crossrepo_smoke.py
  - docs/tasks/TASK-REM-T06-…md -> /README.md
  - docs/tasks/TASK-REM-T06-…md -> CODE_OF_CONDUCT.md
  - docs/tasks/TASK-REM-T06-…md -> CONTRIBUTING.md
```

Bốn reference đỏ thuộc `S136` (1) và `TASK-REM-T06` (3) — BASELINE, không file
nào của `R6` góp thêm. Trùng khớp với vòng 1 §6.4.

### 6.5 `CHECK-R6-30` — đối soát trên SỔ THẬT của Owner

Lệnh đã chạy đúng nguyên văn như đề bài yêu cầu:

```text
$ .venv/bin/python scripts/r6_book_reconciliation.py \
    --so /Users/hoangvinh/Downloads/So_chi_tiet_ban_hang.xlsx --so-cua-owner
KHÔNG TÌM THẤY SỔ: /Users/hoangvinh/Downloads/So_chi_tiet_ban_hang.xlsx
Đây KHÔNG phải một lỗi của R6 — file sổ kế toán không được commit vào repo
(DEC-108) và không có mặt trong môi trường này.
EXIT=2

$ find / -iname "So_chi_tiet_ban_hang*" 2>/dev/null
  (không kết quả)
```

`/Users/hoangvinh/Downloads/` là đường dẫn trên máy Owner; phiên này chạy trong
container Linux. Không có cách trung thực nào để đóng `CHECK-R6-30` từ đây, và
phiên này KHÔNG bịa ra một lần chạy.

Điều phiên này LÀM ĐƯỢC — và đã làm — là kiểm rằng công cụ ấy vẫn đúng SAU
`REPAIR-1`, trên sổ Golden đã freeze:

```text
$ .venv/bin/python scripts/r6_book_reconciliation.py \
    --so tests/fixtures/golden/period_2026_01.xlsx
Chỉ tiêu                                    Nguồn         Aggregate    Kết quả
Dòng nguồn (có Số BH)                         351               351    OK
Số BH khác nhau                               254               254    OK
BH có doanh thu sau CK dương                  248               248    OK
Tổng SL                                       407               407    OK
Doanh số bán (dẫn xuất)             3,564,610,000     3,564,610,000    OK
Chiết khấu                              2,300,000         2,300,000    OK
Doanh thu sau CK                    3,562,310,000     3,562,310,000    OK
BH có ít nhất hai dòng                         63                63    OK
KẾT QUẢ ĐỐI SOÁT: KHỚP TOÀN BỘ
EXIT=0
```

`3.562.310.000` là con số Golden freeze TRƯỚC `R6` — `REPAIR-1` không dời nó.

**`CHECK-R6-30` GIỮ `NOT_TESTED`.** Owner chạy đúng một lệnh trên máy mình để
đóng nó, trên HEAD `40807ef`.

---

## 7. Finding và ghi nhận của vòng 2

### 7.1 Finding `REPAIR_REQUIRED`: **KHÔNG CÓ**

Không một phép đo nào trong phiên này tìm ra một lỗi thuộc các lớp mà brief
`R6` §7 liệt kê là bắt buộc repair — *sai tổng tiền, sai số đơn, mất
persistence/audit, rò dữ liệu, hoặc gộp sai khó phát hiện*. Đây là điều kiện
quyết định, vì lineage `R6` còn `0 remaining` và một `REPAIR_REQUIRED` sẽ buộc
escalate.

### 7.2 Finding `ACCEPTED_RISK` mới: **KHÔNG CÓ**

### 7.3 Ghi nhận — bốn mục, KHÔNG mục nào tiêu ngân sách

Cả bốn đều là tài liệu/hiệu năng, không đổi một con số nào trên màn hình và
không thuộc một lớp nào của brief §7. Chúng được ghi ở đây để lần chạm mã kế
tiếp — bất kể là task nào — dọn cùng, KHÔNG phải để mở một repair cycle.

**`OBS-R6-IR2-01` — mã finding nội bộ lọt vào câu chữ Owner đọc.**
`dashboard_presentation.data_quality` in ra cho người dùng cuối chuỗi
`"(repair AR-R6-IR-03)"`. Đo được trên trang thật (§4.4). Một mã finding nội
bộ không nói được gì cho Owner và làm câu giải thích dài ra vô ích. Sửa là một
chuỗi. `0` tác động số liệu.

**`OBS-R6-IR2-02` — lỗi chính tả trong chính câu đính chính `COR-R6-IR-01`.**
`dashboard_presentation.drilldown_rows` docstring viết *"nó đo trên chính HTML
đã render **chứ trên** kết quả của hàm này"* — thiếu "không phải". Câu đọc ra
thành ngược nghĩa. Bài canh và tham chiếu file thì ĐÚNG (§5), nên `COR-R6-IR-01`
vẫn là ĐÃ SỬA; đây là một lỗi gõ trong docstring, `0` tác động hành vi.

**`OBS-R6-IR2-03` — con số trong Scope Lock đã lệch.**
`docs/tasks/R6-dashboard-phan-tich-kinh-doanh.md` §1 ghi
`tests/test_r6_*.py   MỚI (7 file)`; thực tế có `9` file (`REPAIR-1` thêm hai).
Mẫu `tests/test_r6_*.py` vẫn phủ đủ nên KHÔNG có file nào nằm ngoài Scope Lock
(§1.5 đã đối chiếu đủ 37 file); chỉ con số trong ngoặc là cũ.

**`OBS-R6-IR2-04` — lát mở rộng được đọc HAI LẦN mỗi lần nạp trang.**
`_chart_details` được biểu đồ doanh thu và biểu đồ số đơn gọi TÁCH RỜI, và cả
hai tính ra cùng một khoảng, nên cùng một câu truy vấn chạy hai lần. Đo được:

```text
muc=ngay:  3 lời gọi service.period, 2 lát MỞ RỘNG  2026-08-02 → 2026-09-30
muc=thang: 3 lời gọi service.period, 2 lát MỞ RỘNG  2024-10-01 → 2026-09-30
muc=quy:   3 lời gọi service.period, 2 lát MỞ RỘNG  2022-10-01 → 2026-09-30
```

Khoảng bị chặn bởi `paired_window_span` (không phải toàn bộ dòng thời gian như
trang `R5`) nên nó KHÔNG mở ra một lớp lỗi nào; nhưng ở mức `quy` nó là bốn
năm dữ liệu, đọc hai lần. Trên fixture của phiên này mỗi lần nạp trang mất
`0,03–0,07 s`, tức chưa thấy được. Nhớ một lần trong `_analysis_view` sẽ bỏ đi
đúng một nửa. Đây là hiệu năng, không phải đúng/sai.

### 7.4 `INTEGRATION_DECISION_REQUIRED` — vẫn MỞ

Đã đo lại ở §0.4: `cumulative LOC = 10.155` so với ngưỡng `5.000` của V4.1 §8.
Đây KHÔNG phải một finding về mã và KHÔNG chặn kết luận của vòng review này,
nhưng nó PHẢI được Owner quyết TRƯỚC lần merge. Phiên này ghi nhận và KHÔNG
chọn thay.

---

## 8. Trạng thái sau vòng 2

```text
CHECK-R6-31   NOT_TESTED → PASS (vòng 2, E1)
CHECK-R6-30   VẪN NOT_TESTED  — sổ Owner không có trong môi trường (§6.5)
CHECK-R6-32   VẪN NOT_TESTED  — phiên review KHÔNG tự đóng Owner Acceptance
CHECK-R51-26  VẪN NOT_TESTED  — và vẫn CHẶN merge/deploy R6

REPAIR_REQUIRED     0
ACCEPTED_RISK mới   0
Ghi nhận (tài liệu / hiệu năng)  4   OBS-R6-IR2-01 … -04
Lỗi BASELINE tách ra             2   1 bài pytest (clone nông) + 4 reference

Repair cycle tiêu bởi PHIÊN NÀY   0   (phiên review không sửa một dòng mã nào)
Số dư R6                          1 allowed / 1 used / 0 remaining  (KHÔNG đổi)
```

**`R6` vẫn KHÔNG được merge hay deploy.** Ba điều kiện còn thiếu, và không
điều nào thuộc thẩm quyền của phiên review:

1. `CHECK-R51-26` — Owner nghiệm thu `R5.1` trên production. Vẫn `NOT_TESTED`,
   vẫn chặn (`DEC-207` §10).
2. `CHECK-R6-30` — Owner chạy đối soát trên sổ thật, trên HEAD `40807ef`.
3. `CHECK-R6-32` — Owner Acceptance, và trước đó là quyết định V4.1 §8 cho cờ
   `INTEGRATION_DECISION_REQUIRED`.

---

## 9. Ghi chú môi trường

```text
Python 3.11.15 · node v22.22.2 · SQLite (file tạm và in-memory)
.venv dựng mới trong phiên (pip install -e ".[dev,web,history]")
Server Flask THẬT: app.run(127.0.0.1, cổng động), gọi bằng urllib qua HTTP
clone NÔNG (git rev-parse --is-shallow-repository → true)
12 skip của pytest đều có lý do môi trường (botocore chưa cài, GOLDEN_RAW_*
  chưa đặt, field kiểu của R1A)
```

Phiên KHÔNG sửa một dòng mã sản phẩm nào, KHÔNG merge, KHÔNG mở PR, KHÔNG
deploy, KHÔNG triển khai `R7`, KHÔNG mở rộng phạm vi `R6`, KHÔNG tự đánh dấu
Owner Acceptance, và KHÔNG tự chọn thay Owner ở cờ V4.1 §8. Toàn bộ probe được
viết trong thư mục scratchpad NGOÀI repo; không file dữ liệu khách hàng nào
được tạo ra hay in ra.
