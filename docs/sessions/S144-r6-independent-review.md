# S144 — Independent Review cho `R6` (Dashboard phân tích kinh doanh)

Ngày: 2026-09-09
Task Mode: `MAJOR` (phiên review, không phải phiên triển khai)
Kết luận: **`REPAIR_REQUIRED`**

Phiên chỉ ĐỌC, CHẠY, TẠO PROBE và KIỂM. **Không sửa một dòng mã sản phẩm nào,
không merge, không deploy, không làm `R7`, không mở rộng phạm vi `R6`, không
tự đánh dấu Owner Acceptance.**

Bản ghi đầy đủ (bằng chứng nguyên văn từng chuỗi):
`docs/reviews/R6-INDEPENDENT-REVIEW-RECORD.md`.

---

## 1. Đối tượng review

```text
Reports   claude/r6-business-analytics-dashboard-it73x5
          @ 56aca4c91bd788b1e14d7f71b9246d1577255c1a

Nền   Reports   claude/extract-upload-repo-gq2ws4 @ 05f2b443e66ee4702d03c003d5f1f960b5765f8d
      Tracking  main                              @ 66787c0fb0d867a308c632e7f163cddd0c9dd0f2
                chứa R5.1 taxonomy merge dc9891087687f25b6f92804f46eba2628ebe788b
```

Preflight (đo lại bằng `git`, không tin SHA trong bàn giao `S143`): HEAD khớp
mục tiêu từng ký tự; nền là ancestor (`merge-base --is-ancestor` → YES);
worktree CLEAN cả hai repo; nhánh mặc định THẬT của Reports được xác định bằng
`git remote show origin` (`claude/extract-upload-repo-gq2ws4`, **không phải**
`main`) nên không có chuyện review nhầm nhánh mặc định.

Diff được review: `05f2b44…56aca4c`, 31 file, `+6800 / −6`. Sáu dòng xoá đúng
bằng ba thay đổi đã khai trong Scope Lock.

---

## 2. Kết luận và finding

```text
REPAIR_REQUIRED       2   FIND-R6-IR-01, FIND-R6-IR-02
RECOMMENDED           1   AR-R6-IR-03
Đính chính tài liệu   1   COR-R6-IR-01
Lỗi BASELINE tách ra  2   1 bài pytest (clone nông) + 4 reference integrity

CHECK-R6-31   NOT_TESTED → FAIL (vòng 1, E1)
CHECK-R6-30   VẪN NOT_TESTED   (sổ Owner không có mặt trong môi trường — §5)
CHECK-R6-32   VẪN NOT_TESTED
CHECK-R51-26  VẪN NOT_TESTED

Repair cycle tiêu bởi PHIÊN NÀY   0
Số dư R6 hiện tại                 1 allowed / 0 used / 1 remaining
```

### `FIND-R6-IR-01` — `REPAIR_REQUIRED`

**Cửa sổ so sánh của CẢ HAI biểu đồ trên trang phân tích vẽ số 0 cho một
khoảng thời gian có doanh thu và số đơn THẬT.**

`_revenue_chart_for_scope` và `_orders_chart` (`app/web/server.py`) nạp cho
`revenue_timeline.paired_series()` lát dữ liệu ĐÃ LỌC theo phạm vi — nhưng cửa
sổ so sánh, theo định nghĩa, nằm NGOÀI phạm vi ấy. Trang Báo cáo của `R5`
tránh đúng điều này bằng một dòng có chủ ý (`server.py:1257`): nó đọc lại
`service.period()` KHÔNG lọc cho biểu đồ.

Hệ quả bị khuếch đại bởi `_covered_by_confirmed`: mốc không có điểm được vẽ
thành `Decimal(0)` với `origin=ORIGIN_CURRENT` khi ngày đó nằm trong một sổ đã
xác nhận đầy đủ — và `confirm_coverage` BẮT BUỘC khoảng xác nhận bao trọn dữ
liệu snapshot, nên trên sổ nhiều tháng đây là số 0 CỨNG mang cờ "đã đo", chứ
không phải một khoảng trống nhìn ra được.

Bằng chứng E1 trên SERVER FLASK THẬT, cùng sổ, cùng kỳ, cùng mức gộp:

```text
R5 /kinh-doanh          : Cửa sổ so sánh (liền trước) · 10/08/2026 — 7.000.000 đồng
R6 /kinh-doanh/phan-tich: Cửa sổ so sánh (liền trước) · 10/08/2026 — 0 đồng
R6 /kinh-doanh/phan-tich: Cửa sổ so sánh (liền trước) · 10/08/2026 — 0 đơn

phân bố 30 mốc cửa sổ liền trước:  R5 {'0': 29, '7000000': 1}
                                   R6 {'0': 60}   (30 doanh thu + 30 số đơn)
```

Sự thật trên sổ: 10/08/2026 có 1 đơn, 7.000.000 đồng.

Bốn lý do buộc phải repair: (1) vi phạm brief §3 *"so với cửa sổ liền trước
cùng độ dài"* — trang không từ chối vẽ, nó vẽ SAI; (2) vi phạm luật `R5` mà
`R6` tuyên bố dùng lại nguyên vẹn (*"số 0 CHỈ khi phạm vi đã được xác nhận đầy
đủ"*); (3) tạo ra đúng lớp lỗi mà `dashboard_metrics` mở đầu bằng việc cấm —
hai trang cùng sản phẩm, cùng sổ, cùng ngày, hai con số; (4) failure path của
`R6` kết thúc ở *"quyết định kinh doanh của Owner"*, và con số này đọc thành
một tín hiệu tăng trưởng BỊA trên đúng trang dựng để quyết định mua hàng.

Không test nào bắt được vì không bài `tests/test_r6_*.py` nào chạm tới
`comparison`/`paired`. `CHECK-R6-13` chứng minh `R6` dùng ĐÚNG ENGINE của `R5`
— điều đó đúng và vẫn đúng — nhưng nó không nói gì về dữ liệu nạp vào engine.

### `FIND-R6-IR-02` — `REPAIR_REQUIRED`

**Bucket "Chưa xác định" đứng làm một NHÓM HÀNG HOÁ trong Basket, và bảng cặp
không phân biệt nó với một nhóm hàng thật.**

Đo trên route thật, qua producer Tracking thật và phân loại qua đúng route
`POST` của `R2`/`R5`:

```text
O 'Don nhieu nhom hang hoa' = 1
  [Tivi] x [Chưa xác định — chưa khớp mã Tracking]  support=1  A->B=50%
co nhan 'chua xac dinh' rieng trong bang cap: False
```

Và khi một đơn có hai lý do chưa xác định KHÁC NHAU, bảng sinh ra hàng gợi ý
bán chéo giữa hai lý do ấy: `[Chưa xác định — xung đột mã] × [Chưa xác định —
chưa khớp mã Tracking]`, support 2, attachment 100 %/100 %.

Trả lời trực tiếp câu hỏi của brief review — **tiền GIỮ ĐỦ** (`pair_revenue`
đúng, đối soát vẫn `yes`), **nhãn HIỆN RÕ** (chuỗi đầy đủ, không rút gọn),
nhưng **UI CÓ THỂ khiến người dùng hiểu nhầm đây là gợi ý cross-sell chính
thức**: `pair_rows` không chở `known` và không chở `reason` (khác hẳn
`group_rows`, vốn chở cả hai), template render hai cột y hệt một cặp thật, và
khối "Cách đọc bảng này" không có chú thích nào về bucket chưa xác định. Thêm
vào đó, chú thích của chính ô "Đơn nhiều nhóm hàng hoá" liệt kê những gì KHÔNG
được tính nhưng không nói dòng chưa xác định thì ĐƯỢC tính.

### `AR-R6-IR-03` — `RECOMMENDED`

`PriceStats.average` chia một tử số đã loại dòng thiếu doanh thu cho một mẫu
số vẫn còn số lượng của chính dòng ấy: hai dòng mỗi dòng 1 chiếc giá
10.000.000, một dòng chưa có `total_sales` ⟹ giá bình quân `5.000.000` —
đúng một nửa giá duy nhất quan sát được. Nặng hơn con số: `data_quality` in ra
cho người đọc rằng dòng chưa có doanh thu *"không được cộng như số 0 vào bất
kỳ ô nào"*, và mệnh đề ấy SAI với đúng ô này. Sửa rẻ: loại các dòng hàng hoá
có `total_sales is None` khỏi mẫu số, hoặc trả `None`.

### `COR-R6-IR-01` — đính chính tài liệu (không tiêu ngân sách)

Docstring của `dashboard_presentation.drilldown_rows` dẫn một file test tên
`test_r6_drilldown_boundary` dưới `tests/` — file KHÔNG tồn tại. Bài canh thật
là `tests/test_r6_dashboard_vertical.py`, hàm
`test_the_drilldown_never_renders_a_customer_field`.

---

## 3. Kiểm đã chạy (không tin số trong bàn giao `S143`)

```text
$ .venv/bin/python -m pytest -q
3397 passed, 12 skipped in 178.04s          ← 0 failed

$ .venv/bin/python scripts/r51_crossrepo_smoke.py --tracking /home/user/Tracking
KẾT QUẢ SMOKE: 63 PASS, 0 FAIL              ← khớp đúng số S142 §4.5

$ .venv/bin/python scripts/r6_crossrepo_smoke.py --tracking /home/user/Tracking
KẾT QUẢ SMOKE: 24 PASS, 0 FAIL              ← producer Tracking THẬT, node v22.22.2

GOVERNANCE STRUCTURE: PASS   PROJECT STATE: PASS
EVIDENCE VALIDATION:  PASS   TASK COMPLETION: PASS
REFERENCE INTEGRITY:  4 finding — BASELINE, không file R6 nào góp thêm
$ git diff --check 05f2b44 56aca4c   → rỗng (sạch)
```

Server Flask THẬT (`app.run(127.0.0.1:8971)`, gọi bằng `curl`/HTTP — không
phải test client): 8 route/biến thể trả `200`, 12 tổ hợp tham số hỏng trả
`200` (không route nào `500`), `POST` vào ba route `R6` trả `405`.

---

## 4. Điều đã xác minh theo từng chuỗi của brief review

| Chuỗi | Kết quả | Ghi chú |
|---|---|---|
| 1 — Effective data và phạm vi | PASS | không đọc Excel/`ImportResult`; custom T8 trong khi `ky`=T9 cho ra ĐÚNG 1 đơn của T8 (giao ⟹ 0, cộng gộp ⟹ 5) — không giao, không cộng; ba cách hỏng khoảng ngày cho ba lý do khác nhau; `CUSTOM` không mượn period lock, chặn ở 4 lớp |
| 2 — Tiền, SL, chiết khấu, số đơn | **`REPAIR_REQUIRED`** | bất biến số đơn giữ ở CẢ NĂM mức gộp; đơn nhiều ngày vào ngày nhỏ nhất, đếm riêng; giá bình quân gia quyền đúng; giá 0 hàng tặng vẫn vào `min`; cửa sổ `30/12/12/8` đúng — **nhưng dữ liệu nạp vào cửa sổ so sánh sai (`FIND-R6-IR-01`)**, và mẫu số giá bình quân lệch (`AR-R6-IR-03`) |
| 3 — Product, hãng, nhóm hàng | PASS | `product_key` là khoá duy nhất; `brand_bucket`/`category_bucket` không nhận `detail` nên không thể suy từ tên thô; năm bucket năm lý do; đổi bucket không đổi một đồng; taxonomy Owner (`Điều hoà`, `Tivi`, `Máy giặt`) có đủ trong Tracking, Reports không giữ bản sao |
| 4 — Basket | **`REPAIR_REQUIRED`** | bốn chỉ tiêu tách rời; `set` theo `product_key` nên mã lặp không tạo cặp; FEE không tăng multi-category; attachment hai mẫu số; `pair_revenue` cộng mỗi đơn một lần — **nhưng bucket chưa xác định đứng làm nhóm hàng hoá (`FIND-R6-IR-02`)** |
| 5 — Web, drill-down, riêng tư | PASS | route Flask THẬT; 7 chuỗi khách hàng quét trên 8 trang, KHÔNG chuỗi nào lộ; drill-down giữ đúng phạm vi; 5 route đều `GET`, POST giữ nguyên 18, không migration, `alembic` một head `0009`, không module nào ngoài `R6` tiêu thụ `R6` |
| 6 — Bất biến R1–R5.1 | PASS | diff RỖNG trên pricing/profit/kpi/period_lock/business_store/revenue_timeline/business_queries/business_service/migrations/config; regression 3397 pass 0 fail; hai smoke xanh |

---

## 5. `CHECK-R6-30` — KHÔNG đóng được ở phiên này

Lệnh đã chạy đúng nguyên văn theo yêu cầu và trả:

```text
KHÔNG TÌM THẤY SỔ: /Users/hoangvinh/Downloads/So_chi_tiet_ban_hang.xlsx
EXIT=2
```

`/Users/hoangvinh/Downloads/` là đường dẫn trên máy Owner; phiên này chạy
trong container Linux, và `find / -iname "So_chi_tiet_ban_hang*"` không trả
kết quả. Phiên KHÔNG bịa ra một lần chạy.

Điều đã làm thay vào đó: kiểm rằng công cụ có nghĩa khi Owner chạy nó. Trên
một sổ dựng đúng tám đặc trưng của vector Owner, đi qua ĐÚNG pipeline
production, cả tám ô đều `OK` ở cả ba cạnh (nguồn ↔ aggregate ↔ kỳ vọng),
`KẾT QUẢ ĐỐI SOÁT: KHỚP TOÀN BỘ`, `EXIT=0`. Công cụ so BẰNG ĐÚNG trên
`Decimal`, phân biệt `EXIT=1` (hệ thống lệch) với `EXIT=2` (thiếu file), có
bài kiểm âm, và không đọc cột `Lợi nhuận` của Excel. Chiết khấu được chứng
minh cộng đúng một lần: hai tầng tính doanh thu sau CK bằng hai đường độc lập
và gặp nhau ở cùng `4.498.535.001`.

`CHECK-R6-30` vẫn `NOT_TESTED`. Nên chạy SAU `REPAIR-1` để lần đối soát nằm
trên HEAD đã sửa.

---

## 6. Bàn giao cho bước kế tiếp

`R6` **KHÔNG được merge hay deploy**: `CHECK-R51-26` vẫn `NOT_TESTED` và
`CHECK-R6-31` vừa `FAIL`.

**Cảnh báo ngân sách — đọc trước khi mở `REPAIR-1`.** `R6` chỉ có
`1 repair cycle`. Sau `REPAIR-1` lineage HẾT ngân sách; nếu vòng review thứ
hai lại ra `REPAIR_REQUIRED`, `R6` KHÔNG được mở cycle thứ hai mà phải
escalate theo `governance/core/ESCALATION_PROTOCOL.md`. Vì thế `REPAIR-1`
phải xử lý **cả bốn** mục trong CÙNG một vòng:

```text
FIND-R6-IR-01   cửa sổ so sánh của hai biểu đồ            BẮT BUỘC
FIND-R6-IR-02   bucket chưa xác định trong Basket         BẮT BUỘC
AR-R6-IR-03     mẫu số giá bán bình quân                  NÊN LÀM
COR-R6-IR-01    tham chiếu test sai trong docstring       NÊN LÀM
```

Bài kiểm hồi quy tối thiểu cho `FIND-R6-IR-01`: một mốc CÓ tiền thật trong
cửa sổ liền trước, với sổ đã xác nhận đầy đủ phủ CẢ HAI cửa sổ — đúng hình
dạng dữ liệu mà phiên này dựng để bắt lỗi.

Hai hướng sửa cho `FIND-R6-IR-01` (phiên review KHÔNG chọn thay người triển
khai): nạp cho hai biểu đồ lát dữ liệu KHÔNG lọc như trang Báo cáo đang làm;
hoặc bỏ hẳn cửa sổ so sánh khi nó rơi ra ngoài phạm vi và NÓI RA điều đó —
phương án sau an toàn nhưng làm trang mất khả năng trả lời chính câu brief §3
yêu cầu.

---

## 7. Ghi chú môi trường

```text
Python 3.11.15 · node v22.22.2 · SQLite in-memory
.venv dựng mới trong phiên (pip install -e ".[dev,web,history]")
botocore KHÔNG cài → 1 skip thêm so với S143 (11 → 12); tổng bài không đổi (3409)
Bài đỏ duy nhất ở lần chạy đầu là BASELINE clone nông:
  fatal: bad object 740f396acb11cf279f303f09ea22dffd0ca95462
  → sau `git fetch origin 740f396…`: tests/test_105d_boundaries.py 41 passed
```

Mọi probe được viết ngoài repo (thư mục scratchpad của phiên), không file dữ
liệu khách hàng nào được tạo hay in ra, và không một dòng mã sản phẩm nào bị
sửa.
