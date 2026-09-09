# R6 — Dashboard phân tích kinh doanh

## Metadata

Status:
IMPLEMENTED

Current Status Reason:
Independent Review vòng 1 (`S144`) kết luận `REPAIR_REQUIRED`. **`REPAIR-1`
(`S145`, 2026-09-09) đã sửa CẢ BỐN mục trong ĐÚNG MỘT repair cycle** — chi
tiết ở §8 cuối file. **Independent Review vòng 2 (`S146`, 2026-09-09) trên
exact HEAD `40807efd50e675b71ccd1a14b5801394da4cafc1` kết luận `PASS`:
`CHECK-R6-31` = `PASS` (E1), `0` finding `REPAIR_REQUIRED`, `0`
`ACCEPTED_RISK` mới, `0` repair cycle tiêu — xem §9.** Task ở `IMPLEMENTED` và
chờ ba việc thuộc thẩm quyền Owner: `CHECK-R51-26`, `CHECK-R6-30`,
`CHECK-R6-32` (và trước đó là quyết định V4.1 §8 cho cờ
`INTEGRATION_DECISION_REQUIRED`).

Toàn bộ năm package của brief `R6` đã triển khai trên repo Reports.
Không migration, không bảng mới, không warehouse, không materialized view,
không API ngoài, không route GHI — `R6` là một tầng CHỈ ĐỌC dựng trên
`PeriodData` hiệu lực của `R3`–`R5`.

`CHECK-R6-01` … `CHECK-R6-29` PASS (E1, bằng chứng nguyên văn ở
`docs/sessions/S143-r6-dashboard-phan-tich.md` §4).

`CHECK-R6-30` (đối soát trên SỔ THẬT của Owner) `NOT_TESTED` — file
`So_chi_tiet_ban_hang.xlsx` KHÔNG được commit (`DEC-108`) và KHÔNG có mặt
trong môi trường phiên này. Công cụ đối soát đã viết và đã được kiểm chứng
trên hai sổ khác (xem `CHECK-R6-27`/`CHECK-R6-28`); còn thiếu đúng một lần
chạy trên sổ thật.

`CHECK-R6-31` (Independent Review) = **`PASS`** (vòng 2, `S146`, 2026-09-09,
E1). Vòng 1 ĐÃ CHẠY ở `S144` trên exact HEAD
`56aca4c91bd788b1e14d7f71b9246d1577255c1a` và kết luận **`REPAIR_REQUIRED`**
(`FAIL`, E1) — kết luận ấy vẫn ĐÚNG với HEAD nó đã review và không được viết
lại. Sau `REPAIR-1` nó trở về `NOT_TESTED` (phiên repair KHÔNG có thẩm quyền
tự tuyên bố mình đã qua review), rồi vòng 2 chạy trên exact HEAD
`40807efd50e675b71ccd1a14b5801394da4cafc1` và đóng nó là `PASS`.

Finding của vòng 1 (hai mục BẮT BUỘC, hai mục nên làm) — **cả bốn ĐÃ SỬA ở
`REPAIR-1` (§8) và ĐÃ ĐƯỢC XÁC NHẬN ĐỘC LẬP ở vòng 2 (§9)**:

```text
FIND-R6-IR-01  cửa sổ so sánh của CẢ HAI biểu đồ vẽ số 0 cho một khoảng có
               doanh thu và số đơn THẬT — hai biểu đồ được nạp lát dữ liệu ĐÃ
               LỌC theo phạm vi, trong khi cửa sổ liền trước nằm NGOÀI phạm vi
               ấy; `_covered_by_confirmed` biến chỗ trống thành số 0 mang cờ
               "đã đo". Trang Báo cáo của R5 đọc lại `service.period()` KHÔNG
               lọc chính vì lý do này.
FIND-R6-IR-02  bucket "Chưa xác định" đứng làm một NHÓM HÀNG HOÁ trong Basket:
               nó làm tăng `multi_merchandise_category_orders` và sinh ra hàng
               gợi ý bán chéo giữa hai lý do chưa xác định, trong khi
               `pair_rows` không chở `known`/`reason` như `group_rows`.
AR-R6-IR-03    (RECOMMENDED) mẫu số giá bán bình quân giữ số lượng của dòng
               thiếu `total_sales` trong khi tử số đã loại dòng ấy — và
               `data_quality` đang in ra một bất biến mà mã không giữ.
COR-R6-IR-01   (tài liệu) docstring `drilldown_rows` dẫn một file test không
               tồn tại.
```

Bằng chứng nguyên văn: `docs/reviews/R6-INDEPENDENT-REVIEW-RECORD.md`;
tóm tắt: `docs/sessions/S144-r6-independent-review.md`.

**Ngân sách:** `R6` có `1 repair cycle`. `REPAIR-1` đã xử lý CẢ BỐN mục trong
CÙNG một vòng và tiêu cycle DUY NHẤT ấy. Vòng review thứ hai KHÔNG ra
`REPAIR_REQUIRED` và tiêu `0` cycle, nên lineage KHÔNG phải escalate. Số dư
giữ nguyên `1 allowed / 1 used / 0 remaining`: một `REPAIR_REQUIRED` phát sinh
về sau vẫn buộc escalate theo `governance/core/ESCALATION_PROTOCOL.md`.

`CHECK-R6-32` (Owner Acceptance) vẫn `NOT_TESTED` — không phiên review nào tự
đóng nó, kể cả vòng 2.

**`INTEGRATION_DECISION_REQUIRED` vẫn MỞ.** Vòng 2 đo lại `cumulative LOC` từ
nhánh mặc định tới HEAD = `10.155`, ngưỡng V4.1 §8 = `5.000`. Owner phải chọn
(A) integrate sớm, (B) cắt scope, hay (C) tiếp tục divergence có lý do + ngày
review, TRƯỚC lần merge.

Phase:
PHASE-01 — Engine tính toán

Task Mode:
MAJOR

Primary Agent Tier:
C

Escalation Tier:
C

Difficulty:
3/5

Risk:
3/5

Blast Radius:
3/5 (`V4.1` §4 — chấm theo FAILURE PATH, không theo tên file). Failure path
của `R6`:

```text
PeriodData hiệu lực → aggregate R6 → bảng / biểu đồ / giỏ hàng phân tích
                    → quyết định kinh doanh của Owner
```

Nó DỪNG ở đó. Ba tính chất CẤU TẠO giữ nó không đi xa hơn, và cả ba đo được:

1. **Không có đường GHI.** `R6` không thêm một route `POST` nào, không một
   bảng nào, không một store quyết định nào, không một migration nào
   (`CHECK-R6-24`). Một lỗi ở đây không sửa được một bản ghi kế toán.
2. **Không định nghĩa lại một con số đã nghiệm thu.** Doanh thu đọc
   `BusinessLine.total_sales`, số đơn và số dòng đối soát TUYỆT ĐỐI với
   `business_metrics` ở MỖI lần tải trang (`CHECK-R6-06`). MIN, giá nhập, lợi
   nhuận, coverage, fingerprint, period lock và target engine không bị chạm
   (`CHECK-R6-23`).
3. **Không có tầng dưới nào tiêu thụ `R6`.** Không module nào import
   `dashboard_metrics`/`product_metrics`/`basket_metrics` ngoài chính đường
   trình bày của `R6`.

Nó KHÔNG phải `2/5` vì hai lý do THẬT: (a) một bucket gộp sai làm Owner đọc ra
một cơ cấu hàng bán sai và ra quyết định mua hàng sai — brief liệt kê "gộp sai
khó phát hiện" vào nhóm bắt buộc repair; (b) `R6` mở một bề mặt drill-down mới
trên dữ liệu dòng, tức một đường rò dữ liệu tiềm năng nếu bảng kê đó nới ra.

Nó KHÔNG đạt `4/5` như `R5`: `R5` có quyền LOẠI dòng khỏi tập được cộng và vì
thế đổi được vân tay chốt kỳ và file export; `R6` không có quyền đó và không
chạm hai thứ ấy.

Effective Risk:
MEDIUM (`max(Local Risk 3, Blast Radius 3)` — `V4.1` §4)

Golden Baseline KHÔNG được dùng để hạ bậc (`V4.1` §4.1): không Golden test nào
phủ failure path "aggregate phân tích → quyết định kinh doanh", nên không có
gì để hạ.

Project Profile:
PRODUCT

Review Budget lineage:
`R6` là một ROOT TASK LINEAGE MỚI — nó không mở rộng hợp đồng của `R5`/`R5.1`
mà dựng một tầng đọc mới trên đầu ra của chúng. Ngân sách cấp theo bảng đã
freeze `V4.1` §2: `MEDIUM = 1 blocking repair cycle`. Ngân sách này được ĐO
LẠI từ blast radius ở trên, **không** sao chép ngân sách `2` của `R5` (`R5` là
`HIGH` vì một lý do mà `R6` không có — xem mục Blast Radius). Trạng thái sống:
`PROJECT/REVIEW_BUDGET_LEDGER.md` → "Root Task: R6".

ADR:
`R6` KHÔNG mở một ADR mới. Nó thừa hưởng nguyên vẹn ba quyết định kiến trúc đã
có: `ADR-108` (history store), `ADR-111` §3 (thẩm quyền metadata sản phẩm
thuộc Tracking), và mô hình "effective data giải lúc ĐỌC" mà `PHB-03` dựng.
Quyết định chiến thuật: `PROJECT/PROJECT_DECISIONS.md` → `DEC-207`.

Owner Authority:
Brief `R6 — Dashboard phân tích kinh doanh` (2026-09-09). Hợp đồng phạm vi đầy
đủ: `docs/spec/R6-EXECUTION-BRIEF.md`.

---

## 1. Scope Lock

TRONG phạm vi:

```text
app/modules/reporting/analysis_range.py       MỚI
app/modules/reporting/dashboard_metrics.py    MỚI
app/modules/reporting/product_metrics.py      MỚI
app/modules/reporting/basket_metrics.py       MỚI
app/web/product_taxonomy.py                   MỚI
app/web/dashboard_presentation.py             MỚI
app/web/business_presentation.py              THÊM paired_count_chart,
                                              money_text/money_kvnd; `_slot_title`
                                              nhận thêm tham số `unit` CÓ MẶC ĐỊNH
app/web/revenue_timeline.py                   REPAIR-1: THÊM paired_window_span
                                              (thuần THÊM — xem §8.4)
app/web/server.py                             THÊM 5 route GET + hàm phụ
app/web/templates/_r6_bits.html               MỚI
app/web/templates/kinh_doanh_phan_tich*.html  MỚI (4 file)
app/web/templates/kinh_doanh.html             THÊM 1 liên kết
scripts/r6_book_reconciliation.py             MỚI
scripts/r6_crossrepo_smoke.py                 MỚI
tests/fixtures/r6_reconciliation_workbook.py  MỚI
tests/test_r6_*.py                            MỚI (7 file)
```

NGOÀI phạm vi (và không file nào bị chạm):

```text
app/modules/pricing/**            MIN theo ngày bán, giá nhập
app/modules/profit/**             lợi nhuận
app/modules/kpi/**                KPI
app/web/period_lock.py            chốt kỳ, fingerprint
app/web/business_store.py         mọi đường GHI quyết định
app/web/business_queries.py       tầng truy vấn đọc
app/web/business_service.py       PeriodData và effective data
app/modules/reporting/business_metrics.py   ngữ nghĩa nghiệp vụ đã freeze
tools/db/migrations/**            KHÔNG migration mới
Tracking (toàn bộ repo)           CHỈ ĐỌC hợp đồng metadata đã merge
```

**Đính chính phạm vi tại `REPAIR-1`.** Bản trước của mục này liệt kê
`app/web/revenue_timeline.py` là NGOÀI phạm vi và "không file nào bị chạm".
`REPAIR-1` **có** chạm file đó, và nói ra ở đây thay vì để một lần đọc diff
sau này phát hiện: nó THÊM một hàm công khai `paired_window_span()` và mở rộng
`__all__`, KHÔNG sửa một dòng hành vi nào của engine cũ (`git diff` xác nhận
dòng bị xoá duy nhất là chính dòng `__all__` được viết dài ra — xem `S145`
§4.4). Brief `REPAIR-1` cho phép tường minh: *"Dùng/làm rõ helper thuộc engine
timeline hiện có nếu cần"*. Ràng buộc thật — KHÔNG dựng một engine thời gian
thứ hai — vẫn được giữ, và `CHECK-R6-13`/`CHECK-R6-36` đo nó.

## 2. Ready Gate

| Điều kiện | Trạng thái | Bằng chứng |
|---|---|---|
| Dependency Tracking `dc98910` là ancestor của `main` | PASS | `git merge-base --is-ancestor` → YES |
| Dependency Reports `a59936c` là ancestor của nhánh mặc định | PASS | `git merge-base --is-ancestor` → YES |
| Nhánh mặc định thật đã xác định (KHÔNG giả định "main") | PASS | Reports = `claude/extract-upload-repo-gq2ws4`; Tracking = `main` |
| Đã đọc `S142`, `TASK-105D-DATA-CONTRACT`, tài liệu R3–R5 | PASS | `docs/sessions/S143-r6-dashboard-phan-tich.md` §1 |
| Baseline test/validator đo TRƯỚC khi sửa mã | PASS | `S143` §2 |
| `CHECK-R51-26` được ghi nhận là `NOT_TESTED` | PASS | brief §0, mục này, và `S143` §7 |

## 3. Completion Gate

Task `DONE` khi và chỉ khi toàn bộ check `REQUIRED` PASS **và** ba check còn
lại (`CHECK-R6-30`, `-31`, `-32`) chuyển khỏi `NOT_TESTED`. Phiên triển khai
kết thúc ở `IMPLEMENTED` theo đúng brief.

## 4. Exit Criteria

```text
[x] Năm package triển khai đủ, mỗi package có test đơn vị riêng
[x] Đối soát dashboard ↔ business_metrics chạy ở MỖI lần tải trang
[x] Dòng R5 tạm loại và dòng Owner loại không lọt vào một ô nào
[x] Đổi brand/category/mapping chỉ đổi bucket, không đổi tổng công ty
[x] Test route/web qua Flask thật
[x] Smoke producer Tracking thật → capture thật → dashboard/drill-down
[x] Full regression R1–R5.1 + validators governance + `git diff --check`
[ ] Đối soát trên SỔ THẬT của Owner (CHECK-R6-30)
[x] Independent Review (CHECK-R6-31) — vòng 1 REPAIR_REQUIRED → REPAIR-1 →
    vòng 2 (S146, HEAD 40807ef) PASS
[ ] Owner Acceptance (CHECK-R6-32)
```

---

## 5. Checklist

| Check | Nội dung | Trạng thái | Evidence Level |
|---|---|---|---|
| `CHECK-R6-01` | Aggregate đọc `PeriodData`, KHÔNG đọc Excel/`ImportResult` | PASS | E1 |
| `CHECK-R6-02` | Doanh thu đọc `total_sales`, KHÔNG tính lại `sell × qty − discount` | PASS | E1 |
| `CHECK-R6-03` | Chiết khấu cộng ĐÚNG MỘT LẦN ở cấp dòng | PASS | E1 |
| `CHECK-R6-04` | `Doanh số bán` là DẪN XUẤT, `None` khi doanh thu chưa biết | PASS | E1 |
| `CHECK-R6-05` | `total_quantity` KHÁC `qualifying_quantity`, không thay nghĩa cái cũ | PASS | E1 |
| `CHECK-R6-06` | Đối soát dashboard ↔ `business_metrics` khớp, và BẮT được lỗi | PASS | E1 |
| `CHECK-R6-07` | `NULL ≠ 0` ở mọi ô: lát rỗng ⟹ `None`, không phải `0` | PASS | E1 |
| `CHECK-R6-08` | Phạm vi: ĐÚNG MỘT, không bao giờ giao hai phạm vi | PASS | E1 |
| `CHECK-R6-09` | Khoảng ngày không dùng được ⟹ từ chối KÈM LÝ DO, không im lặng | PASS | E1 |
| `CHECK-R6-10` | Phạm vi `CUSTOM` KHÔNG mượn trạng thái chốt kỳ của tháng nào | PASS | E1 |
| `CHECK-R6-11` | Một đơn thuộc ĐÚNG MỘT mốc (ngày nhỏ nhất), ở CẢ NĂM mức gộp | PASS | E1 |
| `CHECK-R6-12` | `orders_with_multiple_sale_dates` đếm riêng, không chia đôi đơn | PASS | E1 |
| `CHECK-R6-13` | Biểu đồ số đơn dùng ĐÚNG engine cửa sổ của R5, không engine thứ hai | PASS | E1 |
| `CHECK-R6-14` | Giá bán bình quân = `Σ total_sales / Σ quantity` (gia quyền) | PASS | E1 |
| `CHECK-R6-15` | Giá 0 của hàng tặng là giá THẬT, vẫn tham gia min | PASS | E1 |
| `CHECK-R6-16` | FEE/DISCOUNT hiện `—` ở cột giá nhưng GIỮ doanh thu để đối soát | PASS | E1 |
| `CHECK-R6-17` | Năm lý do "chưa xác định" vào NĂM bucket riêng, mỗi bucket một cách sửa | PASS | E1 |
| `CHECK-R6-18` | KHÔNG suy hãng/nhóm hàng từ tên thô (đọc mã nguồn) | PASS | E1 |
| `CHECK-R6-19` | Đổi brand/category/mapping chỉ đổi BUCKET, không đổi tổng công ty | PASS | E1 |
| `CHECK-R6-20` | Bốn chỉ tiêu Basket là bốn tập đơn khác nhau, không suy ra từ nhau | PASS | E1 |
| `CHECK-R6-21` | Mã lặp hai dòng KHÔNG tự tạo cặp; FEE KHÔNG tăng nhóm hàng hoá | PASS | E1 |
| `CHECK-R6-22` | Attachment có HAI mẫu số đúng; `pair_revenue` cộng đơn đúng một lần | PASS | E1 |
| `CHECK-R6-23` | MIN/giá nhập/lợi nhuận/coverage/fingerprint/period lock KHÔNG đổi | PASS | E1 |
| `CHECK-R6-24` | KHÔNG migration, bảng, warehouse, materialized view, API ngoài, route GHI | PASS | E1 |
| `CHECK-R6-25` | Dòng Owner đã loại KHÔNG lọt vào tổng, chart, bucket, giỏ hàng, bảng kê | PASS | E1 |
| `CHECK-R6-26` | Dòng R5 tạm loại KHÔNG lọt vào một ô nào của R6 | PASS | E1 |
| `CHECK-R6-27` | Drill-down KHÔNG rò một trường khách hàng nào (đo trên HTML) | PASS | E1 |
| `CHECK-R6-28` | Công cụ đối soát tái tạo ĐỦ tám con số vector Owner qua pipeline THẬT | PASS | E1 |
| `CHECK-R6-29` | Smoke xuyên hai repo: producer Tracking THẬT → dashboard THẬT | PASS | E1 |
| `CHECK-R6-30` | Đối soát trên SỔ THẬT `So_chi_tiet_ban_hang.xlsx` của Owner | NOT_TESTED | — |
| `CHECK-R6-31` | Independent Review | PASS | E1 |
| `CHECK-R6-32` | Owner Acceptance trên production | NOT_TESTED | — |

`CHECK-R6-31` = `FAIL` là kết luận của vòng 1 trên HEAD `56aca4c`, và nó VẪN
đúng với HEAD ấy. Sau `REPAIR-1` nó trở về `NOT_TESTED` chứ KHÔNG thành `PASS`:
một phiên repair không có thẩm quyền tự tuyên bố mình đã qua review. `PASS` ở
bảng trên là kết luận của **vòng 2** (`S146`, HEAD `40807ef`), do một phiên
review độc lập đóng — không phải do phiên repair. Bản ghi vòng 1 giữ nguyên
văn tại `docs/reviews/R6-INDEPENDENT-REVIEW-RECORD.md`; bản ghi vòng 2 tại
`docs/reviews/R6-INDEPENDENT-REVIEW-RECORD-ROUND-2.md`.

Check của `REPAIR-1` (`S145`) — mỗi check gắn với một finding của vòng 1:

| Check | Nội dung | Trạng thái | Evidence Level |
|---|---|---|---|
| `CHECK-R6-33` | `FIND-R6-IR-01` — cửa sổ so sánh của biểu đồ DOANH THU hiện giá trị THẬT, khác 0 | PASS | E1 |
| `CHECK-R6-34` | `FIND-R6-IR-01` — cửa sổ so sánh của biểu đồ SỐ ĐƠN hiện giá trị THẬT, khác 0 | PASS | E1 |
| `CHECK-R6-35` | `R5` và `R6` khớp TỪNG MỐC của cửa sổ so sánh, cùng sổ/kỳ/mức gộp, qua HTTP thật | PASS | E1 |
| `CHECK-R6-36` | Bốn mức gộp có cửa sổ so sánh (`ngay`/`tuan`/`thang`/`quy`) đều nạp đủ dữ liệu thật | PASS | E1 |
| `CHECK-R6-37` | Custom range neo cửa sổ vào `Đến ngày` của chính nó, KHÔNG mượn period lock | PASS | E1 |
| `CHECK-R6-38` | Số 0 CHỈ hiện khi mốc thật sự rỗng VÀ nằm trọn trong khoảng đã xác nhận | PASS | E1 |
| `CHECK-R6-39` | Ô chỉ tiêu, bảng gộp và giỏ hàng VẪN chỉ đọc phạm vi đang xem | PASS | E1 |
| `CHECK-R6-40` | `FIND-R6-IR-02` — `Tivi + Chưa xác định` KHÔNG là đơn nhiều nhóm hàng hoá | PASS | E1 |
| `CHECK-R6-41` | `FIND-R6-IR-02` — hai lý do chưa xác định KHÁC NHAU không tạo cặp | PASS | E1 |
| `CHECK-R6-42` | CẢ NĂM lý do chưa xác định đều ngoài chiều nhóm hàng | PASS | E1 |
| `CHECK-R6-43` | Hai nhóm hàng THẬT vẫn là đơn nhiều nhóm và vẫn tạo cặp | PASS | E1 |
| `CHECK-R6-44` | Ngữ nghĩa cặp SẢN PHẨM KHÔNG đổi | PASS | E1 |
| `CHECK-R6-45` | Tín hiệu data-quality nói ra số ĐƠN và số DÒNG bị để ngoài phân tích cặp | PASS | E1 |
| `CHECK-R6-46` | Dòng phí KHÔNG bị đếm là "chưa xác định nhóm hàng" | PASS | E1 |
| `CHECK-R6-47` | Tiền và đối soát bảng gộp KHÔNG đổi sau repair Basket | PASS | E1 |
| `CHECK-R6-48` | Tín hiệu data-quality KHÔNG rò một trường khách hàng nào | PASS | E1 |
| `CHECK-R6-49` | `AR-R6-IR-03` — tử số và mẫu số giá bình quân dùng CÙNG tập dòng | PASS | E1 |
| `CHECK-R6-50` | Thiếu doanh thu / thiếu số lượng / số lượng 0 đều rời khỏi CẢ HAI vế | PASS | E1 |
| `CHECK-R6-51` | Ca bình thường và hàng tặng giá 0 KHÔNG đổi kết quả | PASS | E1 |
| `CHECK-R6-52` | Không đủ dữ liệu ⟹ `None` KÈM LÝ DO, không trả 0 | PASS | E1 |
| `CHECK-R6-53` | `min`/`max` và `total_quantity` nghiệp vụ KHÔNG bị thu hẹp | PASS | E1 |
| `CHECK-R6-54` | `COR-R6-IR-01` — docstring `drilldown_rows` dẫn đúng bài canh thật | PASS | E1 |

Bằng chứng nguyên văn của `CHECK-R6-33` … `-54`:
`docs/sessions/S145-r6-repair-1.md` §4.

Bằng chứng nguyên văn: `docs/sessions/S143-r6-dashboard-phan-tich.md` §4.

`CHECK-R6-30` GIỮ `NOT_TESTED`, và đây là lý do CHÍNH XÁC: file sổ kế toán
thật không được commit vào repo (`DEC-108`, ghi lại ở
`tests/fixtures/synthetic_workbook.py`) và không có mặt trong môi trường phiên
này (`/Users/hoangvinh/Downloads/` là đường dẫn trên máy Owner). Công cụ
`scripts/r6_book_reconciliation.py` đã sẵn sàng và đã được kiểm chứng trên hai
sổ có thật; Owner chạy một lệnh để đóng check này — xem `S143` §8.

---

## 6. Rủi ro đã chấp nhận

`ACCEPTED_RISK R6-01` — **Mọi lý do "chưa xác định" đều đổ vào bucket của
chính nó, kể cả khi số dòng rất nhỏ.** Một kỳ có đúng một dòng `CONFLICT` vẫn
sinh ra một hàng riêng trên bảng nhóm hàng. Bảng vì thế dài hơn cần thiết ở
những kỳ sạch.

*Điều kiện kích hoạt:* bảng cơ cấu có từ ba bucket "chưa xác định" trở lên mà
mỗi bucket dưới 1 % doanh thu kỳ, và Owner nói ra rằng nó gây nhiễu.
*Vì sao chấp nhận:* tác động là ĐỘ DÀI bảng, không phải con số; và gộp năm lý
do vào một ô sẽ xoá đúng chiều "sửa ở đâu" mà `PHB-06 §10` yêu cầu.

`ACCEPTED_RISK R6-02` — **Cặp nhóm hàng có support 1 vẫn hiển thị.** Bảng cặp
theo NHÓM HÀNG hiện toàn bộ (khác bảng cặp sản phẩm, mặc định support ≥ 2),
nên một cặp xuất hiện đúng một lần vẫn có một hàng.

*Điều kiện kích hoạt:* bảng cặp nhóm hàng vượt 30 hàng trên một kỳ thật.
*Vì sao chấp nhận:* số nhóm hàng nhỏ theo bản chất taxonomy đóng của Tracking,
support được ghi thành CỘT nên người đọc thấy ngay, và ẩn support 1 ở chiều
nhóm hàng sẽ giấu mất chính những nhóm mới bắt đầu bán.

`ACCEPTED_RISK R6-03` — **Đơn có dòng ở nhiều ngày được gán vào ngày nhỏ
nhất.** Với một đơn giao nhiều đợt, biểu đồ số đơn ghi nhận nó ở ngày phát
sinh đầu tiên chứ không trải ra.

*Điều kiện kích hoạt:* `orders_with_multiple_sale_dates` vượt 5 % số đơn của
một kỳ thật.
*Vì sao chấp nhận:* đây là một QUY ƯỚC được nói ra trên chính trang
(`dashboard_metrics.MULTI_DATE_NOTE`) và có ô đếm riêng; phương án còn lại —
đếm đơn ở mọi ngày nó có dòng — làm tổng của biểu đồ VƯỢT tổng số đơn của kỳ,
tức đúng lớp lỗi mà brief cấm.

`ACCEPTED_RISK R6-04` — **Biểu đồ của trang phân tích KHÔNG nối dòng thời gian
số cũ.** Trang Báo cáo vẫn nối `legacy_months`/`legacy_days`; trang phân tích
thì không.

*Điều kiện kích hoạt:* Owner yêu cầu so một cửa sổ phân tích với một kỳ chỉ có
bản ghi lịch sử.
*Vì sao chấp nhận:* trộn hai loại bằng chứng vào cùng một cửa sổ so sánh sẽ
đặt một tổng tháng lịch sử cạnh các mốc ngày của sổ nạp mà không ô nào nói ra;
dòng thời gian có lịch sử vẫn còn nguyên ở trang Báo cáo, không bị xoá.

---

## 8. REPAIR-1 (`S145`, 2026-09-09) — cả bốn finding, một repair cycle

```text
FIND-R6-IR-01  ĐÃ SỬA   CHECK-R6-33 … -39
FIND-R6-IR-02  ĐÃ SỬA   CHECK-R6-40 … -48
AR-R6-IR-03    ĐÃ SỬA   CHECK-R6-49 … -53
COR-R6-IR-01   ĐÃ SỬA   CHECK-R6-54
Repair cycle tiêu   1  ⟹ R6 còn 1 allowed / 1 used / 0 remaining
```

### 8.1 `FIND-R6-IR-01` — nạp đủ dữ liệu cho cả hai cửa sổ

Thêm `revenue_timeline.paired_window_span(granularity, anchor)`: nó trả về
`(ngày đầu cửa sổ SO SÁNH, ngày cuối cửa sổ HIỆN TẠI)` bằng đúng phép lùi mốc
mà `window_slots`/`comparison_anchor` đã dùng. `server._chart_details()` đọc
lại `service.period(...)` trên đúng khoảng đó — **bounded**, không phải toàn bộ
dòng thời gian như trang Báo cáo `R5` đang làm — rồi cấp lát ấy cho CẢ HAI biểu
đồ.

Ba ràng buộc giữ bằng cấu tạo: chỉ biểu đồ được mở rộng (ô chỉ tiêu, bảng gộp
và giỏ hàng vẫn đọc `view["data"]`); vẫn là effective data (cùng lời gọi
`service.period` mà mọi trang nghiệp vụ dùng, nên dòng đã loại/tạm loại vẫn
vắng); và `period=` cố ý KHÔNG truyền nên lát mở rộng không mượn chốt kỳ của
tháng nào.

Neo được nói ra tường minh là `scope.date_to` thay cho
`revenue_timeline.anchor_date(...)`: với `PERIOD` hai giá trị bằng nhau, còn
với `CUSTOM` thì `anchor_date` rơi về "ngày bán muộn nhất CÓ dữ liệu" và làm
cửa sổ trôi theo dữ liệu — cùng một khoảng ngày người dùng gõ sẽ cho hai cửa
sổ khác nhau ở hai lần nạp sổ khác nhau.

### 8.2 `FIND-R6-IR-02` — chiều nhóm hàng chỉ nhận nhóm chính danh

`basket_metrics.build_index` chỉ thêm vào `OrderBasket.categories` những bucket
có `known is True`; dòng hàng hoá còn lại được đếm vào
`unknown_category_lines`. `BasketCounts` vì thế có thêm
`orders_with_unknown_category` + `unknown_category_lines`, và trang giỏ hàng
hiện chúng thành một khối độ phủ CÓ CON SỐ, ngay cạnh bốn ô đếm.

Ranh giới nằm ở ĐÚNG MỘT chỗ (`build_index`) — `category_pairs` cố ý KHÔNG có
phép lọc thứ hai, vì hai phép lọc là hai chỗ để ô đếm và bảng cặp trôi khỏi
nhau. Ngữ nghĩa cặp SẢN PHẨM không đổi (`CHECK-R6-44`); `Pair` chỉ nhận thêm
hai cờ `left_known`/`right_known` CHỈ ĐỂ HIỂN THỊ, không tham gia một phép đếm
nào.

Bảng gộp theo nhóm hàng (`product_metrics`) KHÔNG bị chạm: nó vẫn giữ TOÀN BỘ
dòng trong bucket riêng của chúng, và `CHECK-R6-47` đo rằng đối soát vẫn khớp
tuyệt đối.

### 8.3 `AR-R6-IR-03` — một tập dòng cho cả hai vế

`PriceStats` đổi `merchandise_quantity`/`merchandise_revenue` thành
`priced_quantity`/`priced_revenue` (thêm `priced_lines`), tính trên tập dòng
hàng hoá có ĐỦ `total_sales`, `quantity` và `quantity > 0`. `min`/`max` giữ
nguyên tập cũ (mọi dòng hàng hoá có đơn giá) vì chúng trả lời câu hỏi về ĐƠN
GIÁ, không về doanh thu. `average_reason` nói ra vì sao ô trống, và trang chở
nó lên tooltip.

`dashboard_metrics.total_quantity` KHÔNG bị chạm — thu hẹp nó sẽ đánh đổi một
phép đối soát để sửa một phép chia.

### 8.4 Đính chính phạm vi

`app/web/revenue_timeline.py` bị chạm (thuần THÊM). Xem §1 "Đính chính phạm vi
tại `REPAIR-1`".

### 8.5 Hai lỗi của chính bộ kiểm, tìm ra và sửa trong phiên

- `scripts/r6_crossrepo_smoke.py` §4 có bài *"phí KHÔNG làm tăng ô nhiều nhóm
  hàng hoá"* mà — đúng như review §7.2 đã ghi — xanh nhờ một dòng CHƯA KHỚP MÃ,
  không nhờ hai nhóm hàng thật. Đã sửa để phân loại theo TÊN HÀNG (xác định)
  và để `BH1` có hai nhóm hàng chính danh; smoke tăng từ 24 lên 29 phép thử.
- Bài kiểm mới của `REPAIR-1` ban đầu gán thẳng vào module
  (`live_pull.is_configured = ...`) và làm rò trạng thái sang
  `tests/test_tracking_live_pull.py`. Đã sửa bằng `pytest.MonkeyPatch()` có
  `undo()`.

---

## 7. Điều kiện merge/deploy

`R6` **KHÔNG được merge hay deploy** cho tới khi ĐỦ hai điều:

1. `CHECK-R51-26` (Owner nghiệm thu `R5.1` trên production) → `PASS`;
2. `CHECK-R6-31` (Independent Review của `R6`) → `PASS`.

Lý do đầy đủ: `docs/spec/R6-EXECUTION-BRIEF.md` §0.

**Trạng thái sau vòng 2 (`S146`, 2026-09-09):** điều (2) ĐÃ THOẢ
(`CHECK-R6-31` = `PASS`). Điều (1) VẪN CHƯA: `CHECK-R51-26` `NOT_TESTED`, nên
`R6` VẪN KHÔNG được merge hay deploy. Ngoài hai điều trên còn một cờ governance
phải đóng TRƯỚC lần merge: `INTEGRATION_DECISION_REQUIRED` (V4.1 §8,
`cumulative LOC = 10.155` so với ngưỡng `5.000`) — Owner chọn (A) integrate
sớm, (B) cắt scope, hay (C) tiếp tục divergence có lý do + ngày review.

---

## 9. Independent Review VÒNG 2 (`S146`, 2026-09-09) — `PASS`

Đối tượng: exact HEAD `40807efd50e675b71ccd1a14b5801394da4cafc1`, detached,
worktree sạch; `branch_authority_check.sh` → `AUTHORITY_OK`
(`DETACHED_EXACT_TARGET`). Tracking = `origin/main` `66787c0`, không lệch một
byte — dependency, không có thay đổi `R6`.

```text
CHECK-R6-31             NOT_TESTED → PASS (E1)
finding REPAIR_REQUIRED 0
finding ACCEPTED_RISK   0
ghi nhận tài liệu/hiệu năng  4   OBS-R6-IR2-01 … -04 (KHÔNG tiêu ngân sách)
repair cycle tiêu       0
số dư R6                1 allowed / 1 used / 0 remaining   (KHÔNG đổi)
ESCALATION              KHÔNG cần
```

Vòng 2 xác nhận `CHECK-R6-33` … `CHECK-R6-54` bằng bằng chứng ĐỘC LẬP: phiên
review KHÔNG dùng lại một fixture nào của `REPAIR-1` và KHÔNG lấy một con số
nào từ `S145` làm bằng chứng. Tóm tắt phép đo:

```text
FIND-R6-IR-01  93 phép đo qua HTTP THẬT (app.run, cổng thật), oracle là trang
               Báo cáo R5 trên CÙNG server/sổ/kỳ/mức gộp. R6 khớp R5 TỪNG MỐC
               ở ngay/tuan/thang/quy và ở custom range; cửa sổ so sánh có tiền
               thật ở CẢ BỐN mức; số 0 chỉ ở mốc rỗng THẬT nằm trọn trong
               coverage đã xác nhận, ngoài coverage vẫn là khoảng trống; custom
               range neo vào `Đến ngày` và KHÔNG mượn chốt kỳ; lát mở rộng vẫn
               là effective data (dòng Owner loại KHÔNG quay lại); ô chỉ tiêu/
               bảng gộp/giỏ hàng/bảng kê vẫn chỉ đọc phạm vi đang xem.
FIND-R6-IR-02  51 phép đo: 1 probe TOÀN TRANG xuyên hai repo (danh mục do
               producer Tracking THẬT sinh, phân loại qua route POST thật),
               1 DIFF trực tiếp `56aca4c` vs HEAD trên cùng đầu vào, và 1 probe
               phủ CẢ NĂM lý do + 10/10 tổ hợp hai lý do ở min_support=1.
AR-R6-IR-03    34 phép đo, phần lớn là diff trực tiếp với `56aca4c`; năm ca
               (thiếu doanh thu, thiếu SL, SL=0, hàng tặng giá 0, ca bình
               thường) + hai ca `None` kèm lý do + bất biến min/max,
               total_quantity, tổng doanh thu và đối soát bảng nhóm.
COR-R6-IR-01   bài canh thật tồn tại và đo đúng HTML đã render; không còn tham
               chiếu nào coi file không tồn tại là bài canh.
```

Regression đo trong vòng 2: full `pytest` `3445 passed / 12 skipped /
0 failed`; smoke `R6` `29 PASS`; smoke `R5.1` `63 PASS`; Tracking `2892 đạt /
0 hỏng`; `git diff --check` sạch; validator = baseline; đối soát sổ Golden
`3.562.310.000` KHỚP TOÀN BỘ.

Bốn ghi nhận KHÔNG tiêu ngân sách, dọn kèm ở lần chạm mã kế tiếp:

```text
OBS-R6-IR2-01  chuỗi "(repair AR-R6-IR-03)" — mã finding NỘI BỘ — lọt vào câu
               chữ Owner đọc trong `dashboard_presentation.data_quality`.
OBS-R6-IR2-02  docstring `drilldown_rows` thiếu "không phải": "…đo trên chính
               HTML đã render CHỨ TRÊN kết quả của hàm này" — đọc ra ngược
               nghĩa. Tham chiếu bài canh thì ĐÚNG.
OBS-R6-IR2-03  §1 Scope Lock ghi `tests/test_r6_*.py MỚI (7 file)`; thực tế 9.
OBS-R6-IR2-04  `_chart_details` chạy HAI LẦN mỗi lần nạp trang với CÙNG một
               khoảng (mỗi biểu đồ một lần); ở `muc=quy` là 4 năm dữ liệu đọc
               hai lần. Hiệu năng, không đúng/sai.
```

Bằng chứng nguyên văn: `docs/reviews/R6-INDEPENDENT-REVIEW-RECORD-ROUND-2.md`;
tóm tắt: `docs/sessions/S146-r6-independent-review-round-2.md`.
