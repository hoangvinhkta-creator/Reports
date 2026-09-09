# R6 — Dashboard phân tích kinh doanh

## Metadata

Status:
IMPLEMENTED

Current Status Reason:
Toàn bộ năm package của brief `R6` đã triển khai trên repo Reports. Không
migration, không bảng mới, không warehouse, không materialized view, không API
ngoài, không route GHI — `R6` là một tầng CHỈ ĐỌC dựng trên `PeriodData` hiệu
lực của `R3`–`R5`.

`CHECK-R6-01` … `CHECK-R6-29` PASS (E1, bằng chứng nguyên văn ở
`docs/sessions/S143-r6-dashboard-phan-tich.md` §4).

`CHECK-R6-30` (đối soát trên SỔ THẬT của Owner) `NOT_TESTED` — file
`So_chi_tiet_ban_hang.xlsx` KHÔNG được commit (`DEC-108`) và KHÔNG có mặt
trong môi trường phiên này. Công cụ đối soát đã viết và đã được kiểm chứng
trên hai sổ khác (xem `CHECK-R6-27`/`CHECK-R6-28`); còn thiếu đúng một lần
chạy trên sổ thật.

`CHECK-R6-31` (Independent Review) và `CHECK-R6-32` (Owner Acceptance)
`NOT_TESTED` — phiên triển khai KHÔNG tự đóng hai check này.

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
app/web/revenue_timeline.py       engine thời gian của R5
tools/db/migrations/**            KHÔNG migration mới
Tracking (toàn bộ repo)           CHỈ ĐỌC hợp đồng metadata đã merge
```

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
[ ] Independent Review (CHECK-R6-31)
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
| `CHECK-R6-31` | Independent Review | NOT_TESTED | — |
| `CHECK-R6-32` | Owner Acceptance trên production | NOT_TESTED | — |

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

## 7. Điều kiện merge/deploy

`R6` **KHÔNG được merge hay deploy** cho tới khi ĐỦ hai điều:

1. `CHECK-R51-26` (Owner nghiệm thu `R5.1` trên production) → `PASS`;
2. `CHECK-R6-31` (Independent Review của `R6`) → `PASS`.

Lý do đầy đủ: `docs/spec/R6-EXECUTION-BRIEF.md` §0.
