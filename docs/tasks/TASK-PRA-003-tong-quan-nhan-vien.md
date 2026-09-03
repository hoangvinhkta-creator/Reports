# TASK-PRA-003 — Tổng Quan + Nhân Viên (Màn Hình Quản Lý Trên Dữ Liệu Đã Lưu)

## Metadata
Status:
IN_PROGRESS

Phase:
PHASE-PRA — Slice 3 (màn hình quản lý đọc từ nền dữ liệu PRA-002)

Task Mode:
MAJOR

Primary Agent Tier:
Tier B (tầng CHỈ-ĐỌC; blast radius theo failure path = hiển thị sai một con
số quản lý → quyết định quản lý sai)

Escalation Tier:
Owner (mọi business semantics: định nghĩa "số lượng sản phẩm", target, margin,
vai trò của `source_profit`); Independent Reviewer E2 theo
`governance/templates/E2_INDEPENDENT_REVIEW_TEMPLATE.md`

Difficulty:
3/5

Risk:
3

Blast Radius:
3/5 — chấm theo failure path (`governance/core/V4_1_POLICY_FREEZE.md` §4),
KHÔNG theo tên module. Đường hỏng tệ nhất: một ô trên dashboard hiển thị sai
(cộng cả dòng `PENDING` vào Lợi nhuận KPI; hiện `0` thay vì `—` cho kỳ trước
không có dữ liệu; trộn `LEGACY_REFERENCE` với `PIPELINE_GENERATED` trong cùng
một ô) → Owner ra quyết định quản lý dựa trên số sai. Nghiêm trọng, nhưng:
KHÔNG ghi đè dữ liệu (toàn bộ touch area không có một câu
`INSERT`/`UPDATE`/`DELETE` nào), KHÔNG đổi KPI/lương đã tính, KHÔNG chạm bất
biến no-double-count (bất biến đó thuộc `TASK-PRA-002`, PRA-003 chỉ đọc lại
kết quả của nó). Vì vậy MEDIUM (3), không HIGH.

Project Profile:
PRODUCT

Root task lineage (V4.1): `TASK-PRA-003` (root mới, KHÔNG kế thừa và KHÔNG
tiêu ngân sách của `TASK-PRA-001`, `TASK-PRA-002` hay bất kỳ lineage nào
khác; đặc biệt KHÔNG kế thừa 40 LOC còn lại trong CHANGE_BUDGET của PRA-002).
Review budget: **MEDIUM = 1 blocking repair cycle**
(`governance/core/V4_1_POLICY_FREEZE.md` §2). Ledger:
`PROJECT/REVIEW_BUDGET_LEDGER.md` → "Root Task: TASK-PRA-003".

Kế hoạch gốc: `docs/tasks/TASK-PRA-000-persistent-reporting-analytics-plan.md`
(mục L, M SLICE 3). Nền dữ liệu: `docs/tasks/TASK-PRA-002-pipeline-persistence-reconciliation.md`
(DONE, đã Controlled Integration vào canonical). Nền legacy:
`docs/tasks/TASK-PRA-001-legacy-reference-vertical.md` (DONE).
Quyết định nền: DEC-166 (B/C/D/E), DEC-167, DEC-170, DEC-171.

Discovery session: S094 (2026-09-03) —
`docs/sessions/S094-pra-003-vertical-slice-discovery.md`.
Finalization session: S095 (2026-09-03) —
`docs/sessions/S095-pra-003-roadmap-finalization.md`.
`BASE_SHA = facf090c782b022730ecc5f1cf0d0b02e29ca8d7` (HEAD nhánh canonical
`claude/extract-upload-repo-gq2ws4` lúc freeze gate).

Quy ước: file DỰ KIẾN tạo được viết KHÔNG kèm phần mở rộng (ví dụ
`app/web/analytics_queries`); file đã tồn tại viết đủ đường dẫn (ví dụ
`app/web/history_store.py`).

Quy ước phân loại: `FACT` (đo được trong repo/dữ liệu) · `OWNER_DECISION`
(Owner đã chốt) · `INFERENCE` (suy từ code/evidence) · `ASSUMPTION` (chưa
verify) · `UNKNOWN`.

---

## (1) Mục Tiêu (Goal)

Biến dữ liệu `PIPELINE_GENERATED` đã persist ở PRA-002 thành một màn hình
quản lý dùng được hằng ngày, trả lời đúng bốn câu:

1. Kỳ này hoạt động bán hàng thế nào?
2. Bao nhiêu kết quả đã đủ chắc chắn (AUTO) và bao nhiêu còn phải xem lại
   (Review)?
3. Nhân viên nào đóng góp bao nhiêu?
4. Người xem đang nhìn **SỐ CŨ** hay **SỐ MỚI**?

PRA-003 là một **management view**. Nó KHÔNG phải: trình duyệt bán hàng chi
tiết, drill-down đơn, drill-down sản phẩm, quy trình xử lý Review, hệ thống
target, hay nền tảng analytics.

---

## (2) Business Authority

| Điều được khẳng định | Thẩm quyền |
|---|---|
| Lợi nhuận KPI là số quản lý CHÍNH; lợi nhuận kế toán là số PHỤ | `OWNER_DECISION` D1 (mục 3), khớp `TASK-PRA-000` §L (LN KPI eligible + coverage = NOW) và DEC-166 |
| `source_profit` KHÔNG lên dashboard PRA-003 | `OWNER_DECISION` D1 |
| Không có target / so target trong PRA-003 | `OWNER_DECISION` D2 |
| Ô số lượng gọi là "Tổng số lượng" | `OWNER_DECISION` D3 |
| `ORDER_KEY = normalize(Số BH)` | DEC-166 |
| Doanh thu net `= sell_price × quantity − discount` | DEC-114, `app/modules/importing/normalizer.py` |
| `LEGACY_REFERENCE` và `PIPELINE_GENERATED` không bao giờ cộng chung | DEC-166 E, `TASK-PRA-000` acceptance (4) |
| Thiếu dữ liệu ⟹ `NULL`, không bao giờ `0` | DEC-103, `governance/core/03_DATA_MODEL_RULES.md` §5 |
| Kỳ báo cáo dẫn xuất từ `order_line_current.sale_date`, KHÔNG từ header workbook | Chỉ thị S095 §8; FIND-RDA-01 (header `Ngày 01 tháng 9 năm 2026` không parse được) |
| Margin, doanh số quy đổi, YTD, xu hướng nhiều tháng = LATER | `TASK-PRA-000` §L, giữ nguyên bởi DEC-166 |
| "Số lượng SP" (loại dòng phí) chưa có quy tắc nghiệp vụ | N.7 của `TASK-PRA-000` — vẫn MỞ |
| Target chưa có dữ liệu lẫn quy tắc | N.8 của `TASK-PRA-000` — vẫn MỞ |

---

## (3) Owner Decisions D1–D3 — ĐÃ LOCKED

Ba quyết định được Owner chốt tại phiên Roadmap Finalization S095. Chúng
**thay thế** phần `RECOMMENDED_DEFAULT` của `S094` mục 14: từ đây chúng là
`OWNER_DECISION`, không còn là default của agent.

### D1 — Thứ bậc lợi nhuận trên dashboard — LOCKED

```
PRIMARY   = Lợi nhuận KPI      (eligible_kpi_profit, chỉ cộng dòng status = AUTO)
SECONDARY = Lợi nhuận kế toán  (accounting_profit, chỉ cộng dòng NOT NULL)
CẢ HAI    = bắt buộc kèm coverage trung thực
KHÔNG HIỂN THỊ = source_profit (cột lợi nhuận do ERP tự ghi trong sổ)
```

Lý do `source_profit` bị loại: nó chưa qua bất kỳ quy tắc nào của Reports.
Đặt nó cạnh hai số kia là mời người đọc so ba số mà không ai giải thích được
chênh lệch — đó là mở scope đối chiếu, không phải hiển thị.

**Hệ quả bắt buộc:** hai coverage có DENOMINATOR KHÁC NHAU và KHÔNG được
trình bày như thể giống nhau:

```
coverage LN KPI      = số dòng AUTO / tổng số dòng hiện hành trong kỳ
coverage LN kế toán  = số dòng có accounting_profit IS NOT NULL / tổng số dòng hiện hành trong kỳ
```

### D2 — Target / So target — LOCKED

```
TARGET trong PRA-003 = DEFER hoàn toàn
```

Cấm tuyệt đối: sao chép hoặc kết hợp `legacy_summary_row.target` (số tay của
kỳ cũ, gắn với một `import_id` cụ thể) vào bất kỳ chỉ tiêu
`PIPELINE_GENERATED` nào — đó là vi phạm DEC-166 E.

Không thêm config target, không thêm schema target, không thêm ingestion
target trong PRA-003.

**Mất mát đã chấp nhận, nói rõ với Owner:** Tổng quan slice 1 KHÔNG trả lời
được "có đạt chỉ tiêu không". Bù lại nó không nói sai.

### D3 — Ý nghĩa ô số lượng — LOCKED

```
NHÃN HIỂN THỊ = "Tổng số lượng"
NGUỒN         = SUM(order_line_source_version.quantity) của các dòng hiện hành trong kỳ
```

Cấm dùng các nhãn `"Số lượng sản phẩm"` hoặc `"Tổng số SP"` cho tới khi tồn
tại một quy tắc phân loại product-line có thẩm quyền (N.7). `non_product_lines`
trong `config/validation.yaml` là cấu hình **hạ mức cảnh báo cho validator**
(`app/modules/validation/validator.py`), KHÔNG phải phân loại hàng hoá — dùng
nó làm quy tắc đếm là tự cấp thẩm quyền cho một file cấu hình chưa bao giờ
được duyệt cho mục đích đó.

**Hệ quả bắt buộc:** trang phải mang một dòng chú thích rằng con số này đếm
MỌI dòng (kể cả phí vận chuyển / công lắp đặt / chiết khấu / voucher) nên
KHÔNG khớp cột "Tổng số SP" của báo cáo cũ.

---

## (4) Minimum-Value Filter — kết quả

Discovery S094 đề xuất 12 ô cho Tổng quan. Mỗi ô được hỏi đúng một câu:
*"Nếu bỏ ô này, người quản lý có mất một quyết định vận hành có ý nghĩa
không?"* Kết quả:

### Tổng quan — 12 ô đề xuất → 10 `REQUIRED_NOW`, 1 `USEFUL_BUT_DEFER`, 1 `NOT_NEEDED`

| # | Ô | Phân loại | Lý do |
|---|---|---|---|
| 1 | Kỳ đang xem | `REQUIRED_NOW` | Không có nhãn kỳ thì mọi con số còn lại vô nghĩa |
| 2 | Tổng đơn | `REQUIRED_NOW` | Câu hỏi 1; oracle production đã quan sát (40) |
| 3 | Số dòng hàng | `REQUIRED_NOW` | Là MẪU SỐ của cả hai coverage và của cảnh báo thiếu ngày bán — bỏ nó thì mọi tỉ lệ mất khả năng diễn giải. Trình bày CHUNG cụm với Tổng đơn ("40 đơn · 61 dòng"), KHÔNG làm thẻ KPI riêng |
| 4 | Tổng số lượng | `REQUIRED_NOW` | `OWNER_DECISION` D3 buộc hiển thị; đồng thời là oracle golden (407) |
| 5 | Doanh thu (net) | `REQUIRED_NOW` | Câu hỏi 1; oracle golden (3.562.310.000) |
| 6 | Lợi nhuận KPI + coverage | `REQUIRED_NOW` | `OWNER_DECISION` D1 — số chính |
| 7 | Lợi nhuận kế toán + coverage | `REQUIRED_NOW` | `OWNER_DECISION` D1 — số phụ |
| 8 | AUTO / Cần kiểm tra (theo ĐƠN) | `REQUIRED_NOW` | Câu hỏi 2; oracle production đã quan sát (15 / 25) |
| 9 | AUTO / Cần kiểm tra (theo DÒNG) — ô riêng | `NOT_NEEDED` | **Trùng lặp thông tin.** `status ∈ {AUTO, PENDING}` là một phân hoạch, nên `dòng Review = tổng dòng − dòng AUTO`. Coverage LN KPI ở ô 6 đã hiển thị đúng cặp `dòng AUTO / tổng dòng`. Một ô thứ hai chứa đúng hai con số đó không thêm thông tin, chỉ thêm bề mặt. **Thông tin KHÔNG bị mất** — nó nằm trong ô 6 |
| 10 | So kỳ trước (Δ đơn, Δ doanh thu) | `REQUIRED_NOW` | Câu hỏi 1 ở dạng "tốt lên hay xấu đi"; và mô hình kỳ ở mục 6 đã freeze nhánh "kỳ trước trống" — đây là nhánh dễ sai nhất của mọi dashboard. Giới hạn ĐÚNG 2 chỉ tiêu, không mở rộng |
| 11 | Dòng chưa có ngày bán | `REQUIRED_NOW` | **Thông tin an toàn.** `_period()` lọc bằng `>=`/`<=` nên dòng `sale_date IS NULL` rơi khỏi mọi kỳ trong im lặng; không hiện nó thì tổng của "toàn bộ dữ liệu" có thể nhỏ hơn tổng thật mà không ai biết |
| 12 | Top nhân viên trong kỳ | `USEFUL_BUT_DEFER` | Câu hỏi 3 đã được trang Nhân viên (SỐ MỚI) trả lời đầy đủ. Top-5 trên Tổng quan là lối tắt một cú nhấp, không phải một quyết định bị mất. Bỏ khỏi slice 1 |

### Nhân viên (SỐ MỚI) — 10 cột đề xuất → 8 `REQUIRED_NOW`, 1 `USEFUL_BUT_DEFER`, 1 `NOT_NEEDED`

| # | Cột | Phân loại | Lý do |
|---|---|---|---|
| 1 | Nhân viên | `REQUIRED_NOW` | Trục của bảng |
| 2 | Nhóm (`employee_group`) | `REQUIRED_NOW` | Thông tin an toàn: so doanh thu của `NOI_THANH` với `STANDARD_SALES` mà không thấy nhóm là so nhầm hai cơ chế khác nhau. 1 cột, đọc thẳng từ DB |
| 3 | Đơn | `REQUIRED_NOW` | Câu hỏi 3 |
| 4 | Dòng hàng | `REQUIRED_NOW` | Mẫu số của hai coverage theo từng nhân viên |
| 5 | Số lượng | `REQUIRED_NOW` | D3; và là một trong 5 chỉ tiêu cộng được của bất biến đối soát (oracle D) |
| 6 | Doanh thu | `REQUIRED_NOW` | Câu hỏi 3 |
| 7 | LN KPI + coverage | `REQUIRED_NOW` | D1 |
| 8 | LN kế toán + coverage | `REQUIRED_NOW` | D1 |
| 9 | AUTO / Cần kiểm tra (dòng) — cột riêng | `NOT_NEEDED` | Cùng lý do trùng lặp như ô 9 của Tổng quan: coverage LN KPI theo nhân viên đã là `dòng AUTO / tổng dòng` của chính nhân viên đó |
| 10 | So kỳ trước (Δ doanh thu theo nhân viên) | `USEFUL_BUT_DEFER` | Trong ca thật đầu tiên toàn bộ cột này sẽ là `—` (tháng 08/2026 không có dữ liệu pipeline). Thêm một cột rỗng vào một bảng đã 8 cột, cho một câu hỏi mà Tổng quan đã trả lời ở mức tổng — không đáng. `TASK-PRA-000` §L cũng xếp xu hướng nhân viên nhiều tháng = LATER |

**Kết luận filter:** không có chỉ tiêu trang trí nào lọt vào. Hai mục
`NOT_NEEDED` bị loại vì TRÙNG LẶP, không phải vì hi sinh an toàn — thông tin
của chúng vẫn hiển thị trong ô/cột coverage. Hai mục `USEFUL_BUT_DEFER` là
tiện lợi, không phải quyết định.

**Headroom thu được:** loại top-nhân-viên, cột so-kỳ-trước theo nhân viên và
hai ô AUTO/Review trùng lặp giải phóng ước tính ~35 dòng Python production và
~30 dòng template so với đề xuất S094. Headroom này KHÔNG được tiêu vào việc
khác — nó là biên an toàn của CHANGE_BUDGET (mục 13).

---

## (5) Phạm Vi (Scope)

### 5.1 Tổng quan (`GET /tong-quan`) — FINAL SLICE

Đúng 10 ô đã lọc ở mục 4, không hơn:

| Ô | Nguồn | Cách tính |
|---|---|---|
| Kỳ đang xem | tham số kỳ | nhãn "Toàn bộ dữ liệu" hoặc "Tháng MM/YYYY" |
| Tổng đơn · Số dòng hàng | `order_line_current` | `COUNT(DISTINCT order_key)` · `COUNT(*)` |
| Tổng số lượng | `order_line_source_version.quantity` qua `current_source_version_id` | `SUM(quantity)` |
| Doanh thu | `order_line_result_version.total_sales` qua `current_result_version_id` | `SUM(total_sales)` |
| Lợi nhuận KPI + coverage | `.eligible_kpi_profit`, `.status` | `SUM(...) WHERE status = 'AUTO'`; coverage `dòng AUTO / tổng dòng` |
| Lợi nhuận kế toán + coverage | `.accounting_profit` | `SUM(...) WHERE accounting_profit IS NOT NULL`; coverage `dòng có giá trị / tổng dòng` |
| AUTO / Cần kiểm tra (đơn) | `.status` | đơn là Review ⟺ có ≥1 dòng `PENDING` |
| So kỳ trước | cùng truy vấn, tháng liền trước | Δ tuyệt đối + Δ % của ĐÚNG hai chỉ tiêu: đơn và doanh thu |
| Dòng chưa có ngày bán | `order_line_current.sale_date IS NULL` | `COUNT(*)` — KHÔNG lọc kỳ |
| Câu dẫn nguồn dữ liệu | — | một câu ở đầu trang, mục 7 |

### 5.2 Nhân viên (`GET /nhan-vien`) — FINAL SLICE

- `GET /nhan-vien` **không tham số** → giữ NGUYÊN VẸN trang legacy như hôm
  nay, từng ô một. Đây là lựa chọn có chủ đích để bảo toàn tuyệt đối bằng
  chứng non-regression của `TASK-PRA-001`.
- `GET /nhan-vien?nguon=cu` → cùng trang legacy đó (nhãn hiển thị `SỐ CŨ`).
- `GET /nhan-vien?nguon=moi` → bảng nhân viên `PIPELINE_GENERATED`, 8 cột đã
  lọc ở mục 4, cộng một dòng `TỔNG`.
- Giá trị `nguon` lạ → rơi về nhánh legacy, KHÔNG `500`.

Quy tắc dòng nhân viên rỗng: `employee_normalized` `NULL`/rỗng thành một
dòng riêng **"Chưa xác định nhân viên"** — KHÔNG bỏ khỏi bảng và KHÔNG gộp
vào bất kỳ ai.

Quy tắc cột Đơn: một đơn có hai nhân viên được đếm ở CẢ HAI dòng. Trang phải
nói rõ điều này; dòng `TỔNG` của cột Đơn dùng `COUNT(DISTINCT order_key)` của
cả kỳ, KHÔNG phải tổng các dòng.

### 5.3 Ngoài phạm vi (nhắc lại, ngắn)

Xem mục 11 — Hard exclusions.

---

## (6) Period Model — FROZEN

```
Bộ chọn kỳ = MỘT select duy nhất; MỌI tuỳ chọn DẪN XUẤT từ dữ liệu đã lưu:

  • "Toàn bộ dữ liệu"   → min(sale_date) → max(sale_date) của order_line_current
  • "Tháng MM/YYYY"     → mỗi tháng THỰC SỰ có dòng hiện hành

Kỳ so sánh = tháng dương lịch LIỀN TRƯỚC của tháng đang chọn.
"Toàn bộ dữ liệu" ⟹ KHÔNG có kỳ so sánh (không bịa một kỳ trước cho một
khoảng tuỳ ý).
```

Quy tắc trung thực bắt buộc:

- Kỳ trước KHÔNG có dữ liệu pipeline → mọi ô so sánh để **trống / `—`** kèm
  chữ "chưa có dữ liệu kỳ trước".
- **TUYỆT ĐỐI KHÔNG** hiển thị `0`, `0%`, `-100%` chỉ vì kỳ so sánh vắng mặt.

Cấm dẫn xuất kỳ quản lý từ header của workbook (`FIND-RDA-01`: header dạng
`Ngày 01 tháng 9 năm 2026` không parse được — không được suy ngữ nghĩa kỳ báo
cáo từ giới hạn của parser).

DEFER khỏi slice này: khoảng ngày tự do (from/to), quý, năm, "hôm nay / tuần
này".

`FACT` — khoảng trống duy nhất phải lấp: `available_periods()`
(`app/web/history_store.py:269`) chỉ tồn tại trên `LegacyRepository`. Phía
pipeline chưa có hàm trả danh sách kỳ; nó là `DERIVABLE` bằng `min/max` trên
`order_line_current.sale_date` và thuộc module truy vấn mới.

---

## (7) Data Origin UX — FROZEN

| Origin | Nhãn hiển thị |
|---|---|
| `LEGACY_REFERENCE` | **SỐ CŨ** (badge `LEGACY` hiện có của `legacy_presentation.ORIGIN_BADGE` GIỮ NGUYÊN, không đổi chuỗi) |
| `PIPELINE_GENERATED` | **SỐ MỚI** |

Giải thích SỐ MỚI, viết ĐÚNG MỘT LẦN trên mỗi trang có nó:

> "Số do Reports tính từ sổ kế toán đã nạp."

Trang có cả hai lựa chọn mang thêm một câu: *"SỐ CŨ = số cũ trong Excel.
SỐ MỚI = số Reports tính từ sổ kế toán đã nạp. Hai loại số không bao giờ được
cộng chung."*

Không phơi từ vựng kiến trúc nội bộ lên dashboard: `snapshot_id`, `run_id`,
`source_version`, `result_version`, `coverage_state`, `outcome` reconcile,
`reconciliation_flag`. Ngoại lệ DUY NHẤT: khi kỳ đang xem có dòng mang cờ
`NOT_SEEN` / `REMOVED_CANDIDATE` / `SOURCE_CHANGED`, Tổng quan hiển thị MỘT
dòng chữ + link sang tab Dữ liệu — không hiển thị bảng cờ.

Lý do giữ nguyên chuỗi badge `LEGACY` trong code: nó là hằng số đã đóng gate
ở `TASK-PRA-001` và đã được S093 dùng làm bằng chứng production. Đổi chuỗi đó
để lấy sự cân xứng thẩm mỹ là sửa bề mặt đã nghiệm thu của một task DONE.

---

## (8) Metric Authority Matrix

`AUTH` = thẩm quyền của ĐỊNH NGHĨA. `DATA` = dữ liệu đã có chưa.

| Chỉ tiêu | AUTH | DATA | Vào PRA-003? |
|---|---|---|---|
| Tổng đơn | ĐÃ CÓ — DEC-166 | READY_NOW | CÓ |
| Số dòng hàng | ĐÃ CÓ — `ORDER_LINE_KEY` (PRA-002) | READY_NOW | CÓ |
| Doanh thu net | ĐÃ CÓ — DEC-114 | READY_NOW | CÓ |
| Tổng số lượng (mọi dòng) | ĐÃ CÓ — D3 | READY_NOW | CÓ |
| LN KPI (AUTO) + coverage | ĐÃ CÓ — D1 + §L NOW | READY_NOW | CÓ (số CHÍNH) |
| LN kế toán + coverage | ĐÃ CÓ — D1 | READY_NOW | CÓ (số PHỤ) |
| AUTO/Review theo đơn | ĐÃ CÓ — `pending_orders` của exporter | DERIVABLE | CÓ |
| So kỳ trước (đơn, doanh thu) | ĐÃ CÓ — §L NOW | DERIVABLE | CÓ |
| Đóng góp theo nhân viên | ĐÃ CÓ — §L NOW | READY_NOW | CÓ |
| Dòng chưa có ngày bán | ĐÃ CÓ — an toàn dữ liệu | DERIVABLE | CÓ |
| AUTO/Review theo dòng (ô riêng) | ĐÃ CÓ | READY_NOW | KHÔNG — trùng coverage (mục 4) |
| Top nhân viên trên Tổng quan | ĐÃ CÓ | DERIVABLE | KHÔNG — `USEFUL_BUT_DEFER` |
| So kỳ trước theo nhân viên | ĐÃ CÓ | DERIVABLE | KHÔNG — `USEFUL_BUT_DEFER` |
| Doanh thu gộp (`total_sales_raw`) | ĐÃ CÓ | READY_NOW | KHÔNG — chưa có nhu cầu |
| `source_profit` | **CHƯA CÓ** vai trò | READY_NOW | KHÔNG — D1 |
| Số lượng SP (loại dòng phí) | **CHƯA CÓ** — N.7 MỞ | MISSING_BUSINESS_RULE | KHÔNG — D3 |
| Target / So target | **CHƯA CÓ** — N.8 MỞ | MISSING_DATA | KHÔNG — D2 |
| Margin | **CHƯA CÓ** — §L LATER | MISSING_BUSINESS_RULE | KHÔNG |
| Doanh số quy đổi | **CHƯA CÓ** — §L LATER, cấm tính ở tầng UI | rate CÓ | KHÔNG |
| Lệch legacy ↔ pipeline | ĐÃ CÓ — §L NOW-lite | chưa có kỳ chồng nhau | KHÔNG |
| Review burden theo nhóm lý do | ĐÃ CÓ — §L slice 4 | READY_NOW | KHÔNG — PRA-004 |
| Sản phẩm / Pareto | ĐÃ CÓ — §L slice 5 | READY_NOW | KHÔNG — PRA-005 |

---

## (9) Query Safety — FROZEN

`FACT #1` — **Cấm cộng `source_snapshot.summary_json` qua các run.**
`history_writer.build_summary()` ghi `auto_orders` / `review_orders` /
`total_lines` của MỘT lần chạy. Hai snapshot chồng ngày mà cộng `summary_json`
lại là double-count — đúng thứ `TASK-PRA-002` được sinh ra để chống. Mọi con
số AUTO/Review theo kỳ **PHẢI** dẫn xuất từ `order_line_current` →
`order_line_result_version.status`.

`FACT #2` — **Chỉ đọc trạng thái hiện hành.** Mọi tổng phải đi qua
`order_line_current` và hai con trỏ `current_source_version_id` /
`current_result_version_id`. PK của `order_line_current` là
`(order_key, product_key, occurrence_index)`, nên mỗi khoá góp đúng MỘT dòng
vào mọi tổng — no-double-count là tính chất của cấu trúc bảng, không phụ
thuộc câu truy vấn có nhớ `DISTINCT` hay không. Không đọc trực tiếp
`order_line_source_version` / `order_line_result_version` mà không qua con
trỏ hiện hành.

`FACT #3` — **`sale_date` là NULLABLE.** `_period()`
(`app/web/history_store.py:1106-1113`) so sánh `>=` / `<=`, nên dòng không có
ngày bán rơi khỏi MỌI kỳ trong im lặng. PRA-003 phải đếm và hiển thị số dòng
hiện hành `sale_date IS NULL` (không lọc kỳ), nếu không thì tổng của "Toàn bộ
dữ liệu" có thể nhỏ hơn tổng thật mà không ai biết.

`FACT #4` — **`current_totals()` coalesce `total_sales` `None` → `Decimal("0")`**
(`app/web/history_store.py:1073`). Với doanh thu điều đó chấp nhận được (không
dòng nào ⟹ không doanh thu). Với LỢI NHUẬN thì KHÔNG: module truy vấn mới
**không được** tái dụng khuôn coalesce đó cho `eligible_kpi_profit` hay
`accounting_profit` — xem mục 10.

`FACT #5` — **Không thêm index suy đoán.** `ix_order_line_current_sale_date`
đã có, phục vụ lọc kỳ; các join đi qua khoá chính. `GROUP BY
employee_normalized` không có index riêng — với quy mô thật (61 dòng
production, 351 dòng golden, ~12k dòng workbook lớn nhất từng gặp) đó là một
sequential scan vài mili-giây. Điều kiện mở lại: chỉ khi ĐO ĐƯỢC trang > 1
giây trên tập ≥12k dòng (CHECK-PRA003-14) mới xét index — có số đo trước,
không thêm trước.

---

## (10) Profit Safety — FROZEN

```
NULL ≠ 0.  Đây là bất biến, không phải khuyến nghị.
```

| Quy tắc | Nội dung |
|---|---|
| P1 | Lợi nhuận KPI CHỈ cộng các dòng `status = 'AUTO'`. Một dòng `PENDING` có `eligible_kpi_profit` khác `NULL` **KHÔNG** được vào tổng |
| P2 | Lợi nhuận kế toán CHỈ cộng các dòng `accounting_profit IS NOT NULL`. Dòng `NULL` bị bỏ qua, **KHÔNG** được quy về `0` |
| P3 | Khi tập cộng RỖNG (không dòng nào đủ điều kiện), hàm truy vấn trả `None`, **KHÔNG** trả `Decimal("0")`, và UI hiển thị `—` |
| P4 | Cả hai lợi nhuận LUÔN đi kèm coverage tường minh với mẫu số là tổng dòng hiện hành của kỳ. Không có coverage ⟹ không được hiển thị con số lợi nhuận |
| P5 | Coverage `0/351` là một kết quả HỢP LỆ và phải hiển thị được — nó nói "chưa có gì chắc chắn", khác hẳn với "lãi bằng không" |

`FACT` nền cho P1 (đọc từ mã nguồn, không phải giả định):
`_PresentedLine.status = "PENDING" if self.reasons else "AUTO"`
(`app/modules/exporting/excel_exporter.py:71-73`), và `_present_lines` luôn
thêm reason `Pending.accounting_purchase_price` /
`Pending.accounting_profit` / `Pending.eligible_kpi_profit` cho mỗi trường
còn `None` (cùng file, 141-149). Suy ra: **mọi dòng `AUTO` chắc chắn có đủ
ba số tiền.** Chiều ngược lại KHÔNG đúng — một dòng có đủ ba số vẫn có thể
`PENDING` vì lý do khác (`EmployeeMapping`, `Suspicious.ERP`…). Vì vậy "LN
KPI chỉ cộng dòng AUTO" là một quy tắc TRÌNH BÀY có định nghĩa chặt và luôn
cộng được, không phải một phép lọc tuỳ tiện.

`FACT` cảnh báo diễn giải: `ReportSummary.order_accounting_rate =
accounted_orders / input_orders` (`excel_exporter.py:59-61`) đo "mọi đơn
trong sổ đã dựng được thành Order", **KHÔNG** đo "mọi dòng đã có giá nhập kế
toán". Con số "Accounting coverage 100%" mà Owner đọc trên production ngày
2026-09-03 vì vậy KHÔNG cho phép kết luận rằng 61 dòng đều có lợi nhuận.
Không được suy ra như vậy ở bất kỳ chỗ nào của PRA-003.

---

## (11) Hard Exclusions

PRA-003 **KHÔNG** được làm bất kỳ điều nào sau đây:

```
target / so target                      | margin
doanh số quy đổi                        | YTD / cùng kỳ năm trước
source_profit trên dashboard            | biểu đồ / trend / chart
drill-down đơn                          | drill-down dòng hàng / sản phẩm
Review workflow (nút xử lý, nhóm lý do) | bảng đối chiếu lệch legacy ↔ pipeline
khoảng ngày tự do (from/to)             | bộ chọn quý / năm
ingestion mới                           | observability system mới
đổi schema                              | thêm migration
đổi Tracking                            | đổi hạ tầng (PostgreSQL/R2/Render/Cloudflare)
sửa PRA-002 core                        | sửa PRA-001 legacy path
repair REM-T06                          | repair các finding đã DEFER của PRA-002
mở PRA-004                              | mở PRA-005
refactor code không liên quan           | hardening suy đoán
```

Refactor CHỈ được phép khi có một implementation blocker đã CHỨNG MINH
(không phải "sẽ sạch hơn"), và khi đó phải mở
`SCOPE EXPANSION REQUIRED` trước, không sửa trước.

---

## (12) Touch Area / Scope Lock

### File MỚI (4)

| File | Vai trò | Kỷ luật kiến trúc |
|---|---|---|
| `app/web/analytics_queries` | Toàn bộ SQL/aggregation của PRA-003 | Nhận một `Engine` (đã phơi sẵn qua `SnapshotRepository.engine`, `app/web/history_store.py:375`). CHỈ `SUM`/`COUNT`/`GROUP BY` trên các cột engine đã ghi. KHÔNG business rule mới. KHÔNG `INSERT`/`UPDATE`/`DELETE` |
| `app/web/analytics_presentation` | Presentation model + định dạng + nhãn nguồn | KHÔNG có phép tính nghiệp vụ. Tái dụng `legacy_presentation.format_number` (thuần định dạng, trung lập nguồn) thay vì nhân bản, kèm comment nói rõ vì sao |
| `app/web/templates/tong_quan.html` | Trang Tổng quan | Không toán tử số học trên biến tiền trong template |
| `app/web/templates/_pipeline_bits.html` | Macro badge/ô cho nguồn pipeline | Đối xứng với `_legacy_bits.html` |

### File SỬA (4)

| File | Delta cho phép |
|---|---|
| `app/web/server.py` | +1 route `GET /tong-quan`; `GET /nhan-vien` nhận tham số `nguon`; 1 helper parse kỳ. **Đường legacy hiện tại KHÔNG đổi hành vi khi không có `nguon`** |
| `app/web/templates/layout.html` | +1 tab nav "Tổng quan" (1 dòng) |
| `app/web/templates/nhan_vien.html` | + bộ chuyển nguồn + nhánh bảng pipeline. **Nhánh legacy giữ nguyên từng dòng** |
| `app/web/static/css/tinphat-ui.css` | + lưới thẻ KPI, `.tag-pipeline`. Tái dụng token `--tp-*`, `.module`, `.summary-grid`, `.tag` sẵn có |

### Scope Lock — FORBIDDEN

```
tools/db/**                              : FORBIDDEN (schema, migration)
app/history/**                           : FORBIDDEN (persistence core PRA-002)
app/web/history_store.py                 : FORBIDDEN
app/web/history_writer.py                : FORBIDDEN
app/web/run_registry.py                  : FORBIDDEN
app/web/storage_backend.py               : FORBIDDEN
app/web/legacy_presentation.py           : FORBIDDEN (chỉ ĐỌC/import, không sửa)
app/modules/**                           : FORBIDDEN (engine, exporter, validator, pricing)
app/pipeline.py, app/composition.py      : FORBIDDEN
app/demo.py, app/owner_launcher.py       : FORBIDDEN
app/legacy/**, 4 bảng legacy_*           : FORBIDDEN
config/**, data/**                       : FORBIDDEN
alembic.ini, render.yaml, Dockerfile     : FORBIDDEN
Tracking (mọi thứ)                       : FORBIDDEN — READ-ONLY REFERENCE
tests/fixtures/golden/**                 : FORBIDDEN (fixture không sửa; test mới đọc chúng)
Mọi câu INSERT/UPDATE/DELETE             : FORBIDDEN — PRA-003 là tầng CHỈ-ĐỌC
```

```
PROTECTED_CORE_IMPACT     = NONE
TRACKING_CHANGE_REQUIRED  = NO
SCHEMA_CHANGE             = NONE
MIGRATION_ADDED           = NONE
ALEMBIC_HEAD              = 0002_snapshots (KHÔNG đổi)
INDEX_ADDED               = NONE
DEPENDENCY_ADDED          = NONE
```

`INFERENCE` — vì sao KHÔNG refactor gì: `SnapshotRepository` đã phơi `engine`
dưới dạng property, nên module truy vấn mới cắm vào được mà không sửa một dòng
nào của module đã qua Independent Review E2 ở S092. Kiến trúc hiện tại đỡ được
vertical này nguyên vẹn — không có lý do kỹ thuật nào để đề xuất refactor.

---

## (13) Change Budget — RIÊNG CỦA PRA-003

Ngân sách riêng, **KHÔNG kế thừa** 40 LOC còn lại của `TASK-PRA-002`. Quy ước
đo giống `TASK-PRA-002` mục 17: Python production tách riêng khỏi
template/CSS/test.

```
Python production mới/sửa
  app/web/analytics_queries               ≈ 120   (mục tiêu)
  app/web/analytics_presentation          ≈  80
  app/web/server.py (delta)               ≈  55
  ------------------------------------------------
  MỤC TIÊU                                ≈ 255 dòng
  CẢNH BÁO MỀM                              320 dòng  → dừng lại, lập BUDGET-AWARE PLAN
  DỪNG CỨNG                                 400 dòng  → STOP = CHANGE_BUDGET_EXCEEDED

Template mới/sửa                          ≤ 220 dòng
  tong_quan.html          ≈  85
  _pipeline_bits.html     ≈  35
  nhan_vien.html (delta)  ≈  55
  layout.html (delta)     =   1

CSS thêm                                  ≤  25 dòng
Test mới                                  ≥  30 test (0 skip mới)
Dependency mới                            =   0   (sqlalchemy / flask / jinja đã có)
Schema / migration / index                =   0
Config mới                                =   0
```

Mục tiêu Python 255 (thấp hơn ước tính 275 của S094) phản ánh headroom thu
được từ Minimum-Value Filter ở mục 4. DỪNG CỨNG giữ nguyên 400 theo chỉ thị.

Hardening (quy tắc 90/10): ≤ 10% ngân sách, và CHỈ sau khi mọi CHECK REQUIRED
đã PASS. Ứng viên DUY NHẤT được phép: đo và ghi thời gian tải trang trên tập
≥12k dòng (CHECK-PRA003-14). Không ứng viên nào khác được thêm.

Nếu triển khai đòi vượt DỪNG CỨNG:

```
STOP = CHANGE_BUDGET_EXCEEDED
```

kèm giải thích lý do REAL VERTICAL cụ thể (một ô nào của mục 5 không dựng
được trong ngân sách, và vì sao). **Không âm thầm mở rộng.**

---

## (14) Review Budget

```
root_task              : TASK-PRA-003
effective_risk         : MEDIUM
repair_cycles_allowed  : 1
repair_cycles_used     : 0
repair_cycles_remaining: 1
Independent Review     : BẮT BUỘC (E2, CHECK-PRA003-12)
```

Chấm MEDIUM theo failure path (`governance/core/V4_1_POLICY_FREEZE.md` §4) —
lý do đầy đủ ở Metadata → Blast Radius.

**Finding KHÔNG tự động trở thành repair work.** Chỉ repair khi finding đe doạ
TRỰC TIẾP một trong năm điều:

1. tính trung thực của kết quả quản lý;
2. bất biến no-double-count;
3. sự tách bạch hai nguồn (`LEGACY_REFERENCE` ↔ `PIPELINE_GENERATED`);
4. an toàn `NULL` / coverage;
5. nghiệm thu real vertical.

Finding không thuộc năm nhóm trên: phân loại `HARDENING` kèm RE-TRIGGER
CONDITION cụ thể (V4.1 §7), hoặc `OUT_OF_SCOPE`. Vượt 1 cycle →
`OWNER_EXTENSION REQUIRED`.

---

## (15) Real Vertical — Tháng 09/2026

`FACT` production đã quan sát (S093, `PRODUCTION_ACCEPTANCE_RESULT = PASS`):

```text
Kỳ                       : 2026-09-01 → 2026-09-03
Trạng thái hiện hành     : 61 dòng · 40 đơn
AUTO / Review (theo ĐƠN) : 15 / 25
Dòng không nhận ra       : 0
Snapshot                 : SNAP-20260903034024-7b421983 (upload 1)
                           SNAP-20260903034120-7b421983 (upload 2, FILE TRÙNG, SAME 61)
Coverage state           : HEADER_CONSISTENT
Tháng 08/2026            : KHÔNG có dữ liệu pipeline
```

Với kỳ "Tháng 09/2026", Tổng quan phải hiển thị:

```text
Tổng đơn              = 40                         ← ĐÃ QUAN SÁT
Số dòng hàng          = 61                         ← ĐÃ QUAN SÁT
AUTO (đơn) = 15   Cần kiểm tra (đơn) = 25          ← ĐÃ QUAN SÁT
Tổng số lượng         = <Owner đọc trên production> ← CHƯA QUAN SÁT — KHÔNG BỊA
Doanh thu             = <Owner đọc trên production> ← CHƯA QUAN SÁT — KHÔNG BỊA
LN KPI + coverage     = <Owner đọc trên production> ← CHƯA QUAN SÁT — KHÔNG BỊA
LN kế toán + coverage = <Owner đọc trên production> ← CHƯA QUAN SÁT — KHÔNG BỊA
So tháng trước        = TRỐNG / "—" + "chưa có dữ liệu kỳ trước"
Dòng chưa có ngày bán = <đọc từ DB> (kỳ vọng 0)
```

`NOT_CLAIMED_AS_PRODUCTION` — bộ số `qty 71 · gross 593.750.000 ·
discount 200.000 · net 593.550.000` có provenance RDA S090/S091
(`CHECK-PRA002-14`) và đã được S093 ghi rõ là không phải số của ca 01→03/09
trên production. **PRA-003 KHÔNG được dùng nó làm kỳ vọng.**

Giá trị của ca này: nó là ca thật đầu tiên đi qua nhánh "kỳ trước trống" —
nhánh dễ sai nhất của mọi dashboard (hiện `0` hoặc `-100%` thay vì để trống).

---

## (16) Acceptance Oracle — FROZEN

| ID | Oracle | Nguồn thẩm quyền | Check |
|---|---|---|---|
| **O-A** | Tổng hợp theo trạng thái hiện hành KHÔNG double-count: upload sổ A (nửa kỳ) rồi sổ B (cả kỳ) → Tổng quan kỳ đó == upload MÌNH sổ B | cấu trúc PK `order_line_current`; kịch bản của `tests/test_pipeline_history_vertical.py` | 01 |
| **O-B** | Golden kỳ 01/2026 (`Toàn bộ dữ liệu` hoặc `Tháng 01/2026`): `orders = 254` · `lines = 351` · `quantity = 407` · `doanh thu = 3.562.310.000` | `tests/fixtures/golden/expected/period_2026_01.json` → `counts.orders`, `counts.lines`, `money.quantity_total`, `money.sales_normalized`. Oracle ĐỘC LẬP: file do `TASK-GOLDEN-BASELINE-001` sinh TRƯỚC khi PRA-003 tồn tại | 02 |
| **O-C** | Lợi nhuận thiếu hiển thị `—`, KHÔNG hiển thị `0` — đây là bất biến an toàn được bảo vệ, không phải một con số literal cụ thể. Minh hoạ bằng cùng kỳ golden: LN KPI và LN kế toán đều `—` khi tập cộng rỗng.[^oc-context] | oracle về TÍNH TRUNG THỰC | 03, 04 |
| **O-D** | Với MỌI kỳ: Σ(các dòng nhân viên) == `period_totals` cùng kỳ trên 5 chỉ tiêu CỘNG ĐƯỢC (dòng, số lượng, doanh thu, LN KPI, LN kế toán). Bảng nhân viên golden có ĐÚNG 1 dòng `Tín Phát` khớp block `employees` | bất biến nội bộ + `employees` của cùng file JSON | 05 |
| **O-D′** | Cột **Đơn** KHÔNG áp bất biến trên — một đơn có thể liên quan nhiều nhân viên. Trang phải nói rõ điều đó | `counts.orders_with_multiple_employee_raw` tồn tại như một khái niệm trong golden | 05 |
| **O-E** | `GET /nhan-vien` không tham số cho ra ĐÚNG trang legacy như trước PRA-003 | non-regression `TASK-PRA-001` | 06 |
| **O-F** | SỐ MỚI chỉ dùng dữ liệu pipeline; trong MỘT `<table>` không bao giờ có cả nhãn SỐ CŨ lẫn SỐ MỚI | DEC-166 E | 06 |
| **O-G** | Production Tháng 09/2026: `40 đơn` · `61 dòng` · `AUTO 15` · `Review 25`; ô so tháng trước TRỐNG | ĐÃ QUAN SÁT trên production (S093) | 07 |
| **O-H** | Kỳ pipeline liền trước vắng mặt → ô so sánh blank / `—`, TUYỆT ĐỐI không `0%` | mục 6 | 08 |
| **O-I** | Dòng `sale_date IS NULL` được đếm và hiển thị riêng; chúng KHÔNG vào bất kỳ kỳ nào và KHÔNG bị lờ đi | `FACT #3` mục 9 | 09 |
| **O-J** | Không PII trong management UI: body không chứa tên/SĐT/địa chỉ khách, không chứa `imei`, không chứa `note_raw` | `governance/product/17_DATA_GOVERNANCE_PRIVACY.md`; `PROJECT/PROJECT_PROFILE.md` (IMEI/serial là dữ liệu cá nhân) | 10 |
| **O-K** | Golden Baseline giữ `58 passed, 2 skipped`; full suite không giảm; `validate_*` giữ nguyên trạng thái hiện tại (kể cả 3 issue `reference_integrity` đã biết của REM-T06 — DEFER, KHÔNG sửa) | S092/S093 | 11 |

[^oc-context]: **Làm rõ ngữ cảnh thực thi (bổ sung tại S098, sau Independent
Review E2 — `FIND-PRA003-01`, `CONTRACT_MISMATCH`, NON_BLOCKING, KHÔNG đổi bất
biến an toàn hay Owner Decision nào).** Có HAI ngữ cảnh thực thi khác nhau
trên cùng fixture golden, và mỗi ngữ cảnh có một coverage LITERAL khác nhau —
cả hai đều ĐÚNG cho ngữ cảnh của mình:
`0/351` thuộc ngữ cảnh sinh golden TRẦN (`tests/fixtures/golden/build_expected.py`
gọi `run_import()` không nạp historical-confirmed registry, mọi dòng ra
`Pending`); `2/351` thuộc ngữ cảnh giống production mà PRA-003 thực sự đọc
(`demo.run_demo` → `run_import_production`, có nạp registry canonical đã
commit, 2 dòng ra `AUTO`). Bất biến CÓ THẨM QUYỀN của O-C không phải một trong
hai con số literal đó — nó là `NULL ≠ 0`: một tập lợi nhuận rỗng/không đủ điều
kiện PHẢI hiển thị `—`, không bao giờ `0`. Cả hai coverage `0/351` và `2/351`
đều thoả bất biến đó (không dòng nào lọt vào tổng khiến ô hiện `0`).
`CHECK-PRA003-03`/`CHECK-PRA003-04` xác nhận bất biến này bằng dữ liệu tổng
hợp có kiểm soát (không phụ thuộc ngữ cảnh nào ở trên) VÀ bằng chính đường
production trên fixture golden (`tests/test_web_pipeline_analytics.py::test_the_golden_period_reports_the_coverage_it_actually_has`,
khoá `2/351` — coverage THẬT của đường mà PRA-003 đọc). Chi tiết điều tra:
`docs/reviews/TASK-PRA-003-INDEPENDENT-REVIEW-RECORD.md`.

**Giới hạn đã biết của oracle golden — phải nói ra, không được lờ đi:**
fixture golden đã ẩn danh về ĐÚNG MỘT nhân viên (`employees` chỉ có
`"Tín Phát"`, `counts.orders_with_multiple_employee_raw = 0`) và MỌI dòng đều
`price_source = Pending`. Vì vậy golden **KHÔNG THỂ** làm oracle cho phân rã
nhiều nhân viên hay cho bất kỳ giá trị lợi nhuận dương nào. Hai vùng đó do
test đơn vị (dữ liệu tổng hợp có kiểm soát) phủ. **Không được dựng một fixture
"giống production" rồi gọi nó là bằng chứng thật.**

---

## Phụ Thuộc (Dependencies)

- `TASK-PRA-002` = DONE và đã Controlled Integration vào canonical
  (`facf090`, `189516e`, `432ad4e` nằm trên default branch). ĐÃ THOẢ.
- `TASK-PRA-001` = DONE. ĐÃ THOẢ.
- `TASK-GOLDEN-BASELINE-001` = DONE (V4.1 `FULLY_ENFORCED`). ĐÃ THOẢ.
- Không phụ thuộc nào còn mở.

## Chặn (Blocks)

- `TASK-PRA-004` (Bán hàng chi tiết / Review workflow) — chưa mở.
- `TASK-PRA-005` (Sản phẩm) — chưa mở.

## An Toàn Để Chạy Song Song Với (Parallel-Safe With)

Không có. Đây là dự án một người; chạy tuần tự.

---

## Ready Gate

| # | Điều kiện | Trạng thái |
|---|---|---|
| R1 | Canonical xác minh, không moved (`facf090c…`) | ĐẠT (S095) |
| R2 | `TASK-PRA-002` DONE + đã tích hợp vào canonical | ĐẠT |
| R3 | Mọi ô của slice truy được về một CỘT ĐÃ TỒN TẠI — không ô nào "chờ dữ liệu" | ĐẠT (mục 5, 8) |
| R4 | 0 schema · 0 migration · 0 dependency · 0 config mới | ĐẠT (mục 12) |
| R5 | Không chạm protected core hay file nào của PRA-001/PRA-002 | ĐẠT (Scope Lock mục 12) |
| R6 | Owner Decisions D1–D3 đã LOCKED | ĐẠT (mục 3) |
| R7 | Acceptance oracle độc lập có sẵn + oracle production thật | ĐẠT (mục 16) |
| R8 | CHANGE_BUDGET riêng, có mức DỪNG CỨNG | ĐẠT (mục 13) |
| R9 | Review budget xác định + lineage đã mở trong ledger | ĐẠT (mục 14) |
| R10 | Completion Gate FROZEN | ĐẠT (mục dưới) |

```
READY_GATE = ĐẠT — TASK-PRA-003 = READY_FOR_IMPLEMENTATION
```

---

## Completion Gate — FROZEN

Dùng `governance/core/TASK_COMPLETION_GATE_STANDARD.md` và
`governance/core/EVIDENCE_STANDARD.md`.

**FROZEN tại S095 (2026-09-03)**, `BASE_SHA = facf090c782b022730ecc5f1cf0d0b02e29ca8d7`.

14 check: **12 REQUIRED** · 2 RECOMMENDED. Risk 3 → mọi REQUIRED có thể thực
thi PHẢI đạt E1; CHECK-PRA003-12 phải đạt E2.

Không xoá, không làm yếu bất kỳ REQUIRED check nào để task pass. Thay đổi
gate phải đi qua `COMPLETION GATE CHANGE PROPOSAL`.

### Data / Truthfulness

#### CHECK-PRA003-01 — Tổng hợp theo trạng thái hiện hành KHÔNG double-count
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Yêu cầu: (a) test tái dùng kịch bản `tests/test_pipeline_history_vertical.py` — ghi sổ A (nửa kỳ) rồi sổ B (cả kỳ) qua `history_writer.write_run_history`, rồi truy vấn Tổng quan cho kỳ đó; mọi chỉ tiêu (đơn, dòng, số lượng, doanh thu, LN KPI, LN kế toán, AUTO/Review đơn) BẰNG ĐÚNG kết quả của kịch bản chỉ-ghi-sổ-B; (b) test dòng `SOURCE_CHANGED` — chỉ version hiện hành được cộng, version cũ không; (c) grep chứng minh module truy vấn mới KHÔNG đọc `source_snapshot.summary_json` và KHÔNG có câu `INSERT`/`UPDATE`/`DELETE` nào. Output test nguyên văn.

Executed By:
Session S096 — PRA-003 MAJOR Implementation (Claude Code)

Timestamp:
2026-09-03

Kết quả S096:
(a) `tests/test_analytics_queries.py::test_a_half_month_book_then_the_full_month_totals_the_full_month_alone` — ghi sổ A (2 dòng nửa kỳ) rồi sổ B (4 dòng cả kỳ) qua `history_writer.write_run_history`; `period_totals()` của chuỗi A→B BẰNG ĐÚNG `period_totals()` của B một mình trên TOÀN BỘ dict (đơn, dòng, số lượng, doanh thu, LN KPI, LN kế toán, AUTO/Review đơn). Thêm `test_reuploading_the_same_book_moves_nothing`.
(b) `test_only_the_current_version_of_a_changed_line_is_counted` — dòng `SOURCE_CHANGED` (8.000.000 → 9.000.000): tổng = 9.000.000 và `lines = 1`; version cũ nằm trong bảng audit nhưng KHÔNG được cộng.
(c) `test_the_query_module_never_writes_and_never_reads_a_run_summary` — bằng chứng CẤU TRÚC bằng AST, mạnh hơn grep chuỗi: `app/web/analytics_queries.py` không import `insert`/`update`/`delete`/`text`, không gọi `begin()`/`commit()`/`execution_options()` (SQLAlchemy 2.0 không autocommit ⟹ không có đường nào ghi), và không định danh nào là `summary_json` hay `source_snapshot`.

```
tests/test_analytics_queries.py: 22 passed in 0.63s
```

#### CHECK-PRA003-02 — Oracle golden độc lập kỳ 01/2026
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Yêu cầu: test integration chạy pipeline thật trên `tests/fixtures/golden/period_2026_01.xlsx`, ghi lịch sử, rồi truy vấn Tổng quan cho kỳ chứa toàn bộ dữ liệu. Bốn giá trị phải khớp TỚI TỪNG ĐƠN VỊ với `tests/fixtures/golden/expected/period_2026_01.json`: `counts.orders = 254`, `counts.lines = 351`, `money.quantity_total = 407`, `money.sales_normalized = 3562310000`. Test phải ĐỌC file JSON, không hard-code bốn số đó. Output test nguyên văn.

Executed By:
Session S096 — PRA-003 MAJOR Implementation (Claude Code)

Timestamp:
2026-09-03

Kết quả S096:
`tests/test_web_pipeline_analytics.py::test_the_overview_matches_the_independent_golden_oracle` — chạy pipeline THẬT trên `tests/fixtures/golden/period_2026_01.xlsx`, ghi lịch sử, rồi `GET /tong-quan?ky=tat-ca`. Bốn giá trị ĐỌC TỪ `tests/fixtures/golden/expected/period_2026_01.json` (không hard-code trong test) và khớp tới từng đơn vị: `counts.orders = 254`, `counts.lines = 351`, `money.quantity_total = 407`, `money.sales_normalized = 3562310000`.

```
tests/test_web_pipeline_analytics.py: 25 passed in 6.66s
```

#### CHECK-PRA003-03 — NULL ≠ 0: giá trị thiếu hiển thị `—`, không hiển thị `0`
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Yêu cầu: (a) test đơn vị — khi không dòng nào đủ điều kiện, hàm tổng hợp trả `None`, KHÔNG trả `Decimal("0")` (bảo vệ khỏi việc tái dụng khuôn coalesce của `current_totals`, `app/web/history_store.py:1073`); (b) test route trên kỳ golden — trang chứa `—` ở cả hai ô lợi nhuận và KHÔNG chứa `0` ở hai ô đó (`pricing.price_source_distribution = {Pending: 351}` ⟹ cả hai lợi nhuận đều thiếu); (c) test quét toàn trang: không nơi nào render `0` cho một giá trị `None`. Output test nguyên văn.

Executed By:
Session S096 — PRA-003 MAJOR Implementation (Claude Code)

Timestamp:
2026-09-03

Kết quả S096:
(a) `test_an_empty_period_returns_none_for_money_not_zero` + `test_a_period_with_lines_but_no_profit_values_returns_none` — hàm tổng hợp trả `None` (KHÔNG `Decimal("0")`) cho `total_sales`, `quantity`, `kpi_profit`, `accounting_profit` khi tập cộng rỗng. `app/web/analytics_queries.py` KHÔNG coalesce ở bất kỳ đâu (khác `current_totals`, `history_store.py:1073`).
(b) `test_a_period_where_nothing_is_eligible_renders_a_dash_and_zero_coverage` — test route trên dữ liệu KHÔNG dòng nào đủ điều kiện: cả hai ô lợi nhuận render `—`, coverage `0 / 3 dòng`, và ô GIÁ TRỊ không nằm trong `{"0", "0đ", "0%"}`. Khẳng định được neo vào đúng ô qua `data-metric`, không quét cả body — coverage `0 / 351 dòng` chứa chữ "0" một cách hợp lệ.
(c) `tests/test_analytics_presentation.py::test_no_field_of_an_empty_overview_is_ever_rendered_as_zero_money` quét TOÀN BỘ mô hình hiển thị, và `test_a_zero_profit_is_written_differently_from_a_missing_profit` khoá lại bất biến trung tâm: `Decimal("0")` → `"0"`, `None` → `"—"`.

LƯU Ý PROVENANCE (FIND-PRA003-01, không blocking): O-C mô tả kỳ golden có `LN KPI = —` với coverage `0/351`. Tiền đề đó đến từ block `pricing` của `period_2026_01.json`, do `tests/fixtures/golden/build_expected.py` sinh bằng `run_import()` TRẦN (không nạp historical-confirmed registry). Đường mà PRA-003 thực sự đọc là đường production (`demo.run_demo` → `run_import_production`) có nạp registry canonical đã commit, nên trên CÙNG fixture đó có 2 dòng `AUTO` với `price_source = OWNER_MANUAL_LEGACY_CONFIRMATION`. Hai con số đều ĐÚNG cho cấu hình của mình. Test khoá con số THẬT của đường production (`2 / 351 dòng`) thay vì mượn con số của cấu hình khác; tính chất mà O-C bảo vệ được chứng minh riêng ở (b) trên dữ liệu có kiểm soát.

#### CHECK-PRA003-04 — Lợi nhuận KPI chỉ cộng dòng AUTO; hai coverage tường minh và đúng mẫu số
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Yêu cầu: (a) dựng dữ liệu có một dòng `PENDING` với `eligible_kpi_profit` KHÁC `NULL` — dòng đó KHÔNG được vào tổng LN KPI; (b) coverage LN KPI = `dòng AUTO / tổng dòng hiện hành trong kỳ`, đúng cả khi tử số = 0; (c) coverage LN kế toán = `dòng có accounting_profit IS NOT NULL / tổng dòng hiện hành trong kỳ`, KHÁC mẫu số của (b) về mặt tử số và được trình bày tách biệt; (d) test route: không ô lợi nhuận nào render mà thiếu coverage đi kèm. Output test nguyên văn.

Executed By:
Session S096 — PRA-003 MAJOR Implementation (Claude Code)

Timestamp:
2026-09-03

Kết quả S096:
(a) `test_a_pending_line_with_a_kpi_profit_never_enters_the_kpi_total` — dòng `PENDING` CÓ `eligible_kpi_profit = 5.000.000` vẫn bị loại; tổng LN KPI = 3.000.000 (chỉ dòng AUTO), `kpi_lines = 1 / lines = 2`.
(b) coverage LN KPI = `dòng AUTO / tổng dòng hiện hành`, đúng cả khi tử số = 0 — `test_a_kpi_coverage_of_zero_over_many_lines_is_a_valid_answer` (`0 / 3`).
(c) `test_the_two_coverages_have_the_same_denominator_but_count_different_lines` — dựng 3 dòng để hai TỬ SỐ khác nhau thật sự (`kpi_lines = 1`, `accounting_lines = 2`, cùng mẫu số 3); render thành hai ô tách biệt (`test_the_two_coverages_are_rendered_as_separate_cells_with_their_own_numerators`).
(d) `test_no_profit_cell_is_ever_rendered_without_its_coverage` — trên cả `/tong-quan` lẫn `/nhan-vien?nguon=moi`, mọi ô lợi nhuận đều có ô coverage đi kèm (macro `profit_kpi`/`profit_cells` đặt giá trị và coverage trong CÙNG một thẻ, nên không cắt bớt cái này mà giữ cái kia).
(e) AUTO/Review THEO ĐƠN: `test_an_order_is_review_when_any_single_line_of_it_is_pending` — đơn 2 dòng có 1 dòng PENDING là 1 đơn Review; `auto_orders + review_orders == orders`.

#### CHECK-PRA003-05 — Bảng Nhân viên đối soát với tổng của kỳ (chỉ tiêu cộng được)
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Yêu cầu: (a) bất biến — với mọi kỳ trong bộ test, Σ(các dòng nhân viên) == `period_totals` cùng kỳ trên ĐÚNG 5 chỉ tiêu cộng được: dòng, số lượng, doanh thu, LN KPI, LN kế toán; (b) bất biến này KHÔNG áp cho cột Đơn, và trang có chú thích nói rõ một đơn có thể được đếm ở nhiều nhân viên; (c) `employee_normalized` `NULL`/rỗng thành dòng "Chưa xác định nhân viên", không bị bỏ và không gộp vào ai; (d) trên kỳ golden: đúng 1 dòng `Tín Phát` khớp block `employees` của `period_2026_01.json` (254 đơn · 351 dòng · SL 407 · doanh thu 3.562.310.000). Output test nguyên văn.

Executed By:
Session S096 — PRA-003 MAJOR Implementation (Claude Code)

Timestamp:
2026-09-03

Kết quả S096:
(a) `test_employee_rows_add_up_to_the_period_totals_on_the_additive_metrics` — với 2 nhân viên và 1 dòng thiếu lợi nhuận, Σ(dòng nhân viên) == `period_totals` trên ĐÚNG 5 chỉ tiêu cộng được (dòng, số lượng, doanh thu, LN KPI, LN kế toán); `None` được xử lý như VẮNG MẶT, không như 0.
(b) `test_the_order_column_is_deliberately_not_additive` — đơn 2 dòng 2 nhân viên: `period_totals["orders"] = 1` nhưng Σ(cột Đơn) = 2. Bất biến CỐ Ý không áp cho cột Đơn, và trang mang chú thích `ORDER_COLUMN_NOTE` nói rõ điều đó; dòng `TỔNG` lấy thẳng từ `period_totals` (`test_the_total_row_counts_each_order_once_not_the_sum_of_the_employee_rows`).
(c) `test_lines_without_an_employee_become_one_row_and_are_never_dropped` — `NULL` và chuỗi rỗng gộp thành ĐÚNG MỘT dòng (gộp ở tầng SQL), nhãn "Chưa xác định nhân viên", không bị bỏ và không gộp vào ai.
(d) `test_the_golden_employee_table_has_exactly_one_employee_row` — trên kỳ golden: đúng 1 dòng `Tín Phát`, bốn giá trị ĐỌC từ block `employees` của `period_2026_01.json` (254 đơn · 351 dòng · SL 407 · doanh thu 3.562.310.000).

### Source Separation / Regression

#### CHECK-PRA003-06 — Tách nguồn: legacy không hồi quy · SỐ MỚI chỉ pipeline · không trộn trong một ô
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Yêu cầu ba assertion trong cùng một check vì chúng là một tính chất: (a) `GET /nhan-vien` KHÔNG tham số trả ra trang legacy tương đương trang trước PRA-003 — so sánh body với baseline chụp trước khi sửa (`TASK-PRA-001` non-regression); (b) `GET /nhan-vien?nguon=moi` trả bảng pipeline mang nhãn `SỐ MỚI` và mọi giá trị đọc từ 6 bảng `PIPELINE_GENERATED`, không đọc bảng `legacy_*` nào; (c) trong MỘT phần tử `<table>` không bao giờ xuất hiện đồng thời nhãn nguồn cũ và nhãn `SỐ MỚI`; (d) `nguon` mang giá trị lạ → rơi về legacy, HTTP 200, không 500. Output test nguyên văn.

Executed By:
Session S096 — PRA-003 MAJOR Implementation (Claude Code)

Timestamp:
2026-09-03

Kết quả S096:
(a) `test_the_sellers_page_without_a_parameter_is_still_the_legacy_page` — `GET /nhan-vien` không tham số vẫn là trang legacy nguyên vẹn (tiêu đề "NHÂN VIÊN — SỐ CŨ THEO THÁNG", badge `LEGACY`, cột "Tổng số SP"). Toàn bộ `tests/test_web_legacy_routes.py` PASS không sửa một dòng nào — đó là bằng chứng non-regression `TASK-PRA-001` mạnh nhất có sẵn (59 passed cùng file test PRA-003).
(b) `test_the_new_numbers_page_reads_no_legacy_table` — nhập workbook legacy TRƯỚC, rồi `?nguon=moi`: không `LEG-`, không `bao_cao.xlsx`, không nhãn cột legacy nào trong `<th>` của bảng SỐ MỚI.
(c) `test_no_single_table_ever_carries_both_source_labels` — quét từng phần tử `<table>`: không bảng nào chứa đồng thời `LEGACY` và `SỐ MỚI`.
(d) `test_an_unknown_source_value_falls_back_to_legacy_and_never_500s` — `nguon` ∈ {`cu`, `xyz`, rỗng, `moi'; DROP TABLE`} đều HTTP 200 và rơi về legacy.

#### CHECK-PRA003-07 — Real vertical production Tháng 09/2026
Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E1

Evidence:
Yêu cầu (Owner thực hiện trên production sau deploy, giống mô hình `CHECK-PRA002-15`): mở `/tong-quan`, chọn kỳ "Tháng 09/2026", đọc và trả về bằng chứng: `Tổng đơn = 40`, `Số dòng hàng = 61`, `AUTO (đơn) = 15`, `Cần kiểm tra (đơn) = 25`, và ô so tháng trước TRỐNG / `—` kèm chữ "chưa có dữ liệu kỳ trước" (KHÔNG phải `0%`). Tiền, số lượng và hai lợi nhuận: Owner ĐỌC và ghi lại giá trị thật — KHÔNG đặt giá trị kỳ vọng trước trong task file này. `/nhan-vien` mặc định vẫn trả trang legacy như trước.

Executed By:
(chưa thực thi)

Timestamp:
(chưa thực thi)

### Period / Safety

#### CHECK-PRA003-08 — Kỳ trước vắng mặt → blank / `—`, không bao giờ `0%`
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Yêu cầu: (a) test route với dữ liệu CHỈ có tháng N — chọn kỳ "Tháng MM/YYYY" của tháng N, trang chứa chữ "chưa có dữ liệu kỳ trước" và KHÔNG chứa `0%`, `-100%`, hay `0` ở hai ô so sánh; (b) test với dữ liệu có cả tháng N-1 và N — ô so sánh hiển thị Δ đúng dấu và đúng giá trị; (c) chọn "Toàn bộ dữ liệu" → KHÔNG hiển thị ô so sánh nào (không bịa kỳ trước cho một khoảng tuỳ ý); (d) danh sách kỳ chỉ chứa tháng THỰC SỰ có dòng hiện hành; DB rỗng → trả rỗng, không ném lỗi. Output test nguyên văn.

Executed By:
Session S096 — PRA-003 MAJOR Implementation (Claude Code)

Timestamp:
2026-09-03

Kết quả S096:
(a) `test_a_month_whose_previous_month_is_empty_shows_blanks_not_zero_percent` — dữ liệu CHỈ có tháng 09/2026; `/tong-quan?ky=2026-09` chứa "chưa có dữ liệu kỳ trước" và cả bốn ô so sánh (`delta-orders`, `ratio-orders`, `delta-total_sales`, `ratio-total_sales`) đều là `—`, không `0`/`0%`/`-100%`.
(b) `test_a_month_with_a_populated_previous_month_shows_a_real_delta` — có cả 08 và 09/2026: Δ = `+500.000`, tỉ lệ = `+50%`, đúng dấu và đúng giá trị.
(c) `test_the_whole_dataset_view_shows_no_comparison_block_at_all` — "Toàn bộ dữ liệu" KHÔNG render ô so sánh nào.
(d) `test_the_period_picker_only_offers_months_that_really_have_lines` + `test_available_periods_on_an_empty_database_is_empty_not_an_error` + `test_an_empty_database_renders_the_overview_without_raising` — danh sách kỳ chỉ chứa tháng thực sự có dòng; DB rỗng trả rỗng và trang vẫn render (mọi ô tiền = `—`).

`INFERENCE` được kiểm chứng: kỳ trước có `lines == 0` thì MỌI ô so sánh để trống — không đọc `previous["orders"] == 0` như thể "kỳ trước bán được 0 đơn" (`analytics_presentation._comparison`).

#### CHECK-PRA003-09 — Dòng thiếu `sale_date` được phơi ra, không biến mất trong im lặng
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Yêu cầu: (a) dựng dữ liệu có ≥1 dòng hiện hành `sale_date IS NULL` cùng với các dòng có ngày; (b) dòng đó KHÔNG vào bất kỳ kỳ nào (`_period()` lọc bằng `>=`/`<=`); (c) số đếm dòng thiếu ngày bán được truy vấn KHÔNG lọc kỳ và ĐƯỢC hiển thị trên Tổng quan; (d) test route xác nhận con số đó xuất hiện trong body khi > 0. Output test nguyên văn.

Executed By:
Session S096 — PRA-003 MAJOR Implementation (Claude Code)

Timestamp:
2026-09-03

Kết quả S096:
(a)(b) `test_lines_without_a_sale_date_fall_out_of_every_period_and_are_counted` — dòng `sale_date IS NULL` không vào kỳ tháng NÀO, và cũng không vào "Toàn bộ dữ liệu": `_period()` LUÔN kèm `sale_date IS NOT NULL` vì "Toàn bộ dữ liệu" là khoảng `min(sale_date)…max(sale_date)` theo mục 6, không phải "mọi dòng trong bảng".
(c) `undated_lines()` truy vấn KHÔNG lọc kỳ — `test_the_undated_count_ignores_the_selected_period`.
(d) `test_lines_without_a_sale_date_are_surfaced_on_the_overview` — trang hiện khối cảnh báo với số đếm khi > 0; `test_with_no_undated_lines_the_page_says_so_explicitly` — khi = 0 trang nói rõ "Không có dòng nào thiếu ngày bán" thay vì im lặng.

#### CHECK-PRA003-10 — Không PII và không từ vựng nội bộ trong management UI
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Yêu cầu: (a) body của `/tong-quan` và `/nhan-vien?nguon=moi` KHÔNG chứa tên khách, số điện thoại, địa chỉ giao hàng của fixture; KHÔNG chứa `imei`; KHÔNG chứa `note_raw` (`PROJECT/PROJECT_PROFILE.md` xếp IMEI/serial vào dữ liệu cá nhân); (b) body KHÔNG chứa `snapshot_id`, `run_id`, `coverage_state`, đường dẫn tuyệt đối, hay secret; ngoại lệ DUY NHẤT được phép là MỘT dòng chữ + link sang tab Dữ liệu khi kỳ có cờ `NOT_SEEN`/`REMOVED_CANDIDATE`/`SOURCE_CHANGED`; (c) grep chứng minh module truy vấn mới không `SELECT` các cột `imei`, `note_raw`, `employee_raw`. Output test nguyên văn.

Executed By:
Session S096 — PRA-003 MAJOR Implementation (Claude Code)

Timestamp:
2026-09-03

Kết quả S096:
(a) `test_the_management_pages_never_render_personal_data` — body của `/tong-quan` và `/nhan-vien?nguon=moi` không chứa `imei`, `note_raw`, `employee_raw`, `customer`, `phone`, `address`, số điện thoại hay tên khách của fixture.
(b) `test_the_management_pages_never_leak_internal_vocabulary` — không `snapshot_id`, `run_id`, `coverage_state`, `source_version`, `result_version`, `reconciliation_flag`, `PIPELINE_GENERATED`, `LEGACY_REFERENCE`, và không đường dẫn tuyệt đối.
(c) `test_the_query_module_never_selects_a_personal_data_column` — quét mã (bỏ comment): `app/web/analytics_queries.py` không tham chiếu `.c.imei`, `.c.note_raw`, `.c.employee_raw`, `.c.product_raw`, `.c.customer`, `.c.phone`, `.c.address`. PII được loại ở tầng TRUY VẤN, không phải bằng cách xoá dữ liệu đã lưu.
(d) `test_the_overview_never_shows_source_profit_or_a_target` — D1/D2: không `source_profit`, không `Target`/`So target`, không `DS quy đổi`, không nhãn `Số lượng sản phẩm`/`Tổng số SP` trong bất kỳ `<th>` hay nhãn thẻ KPI nào ("Tổng số SP" CHỈ xuất hiện trong chú thích cảnh báo mà D3 YÊU CẦU).

### Regression / Review

#### CHECK-PRA003-11 — Không hồi quy: Golden Baseline + full suite + validators
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Yêu cầu, đo TRƯỚC và SAU implementation, output nguyên văn cả hai lần: (a) `tests/test_golden_baseline.py` giữ `58 passed, 2 skipped`; (b) full suite số test PASS không giảm và số skip không tăng; (c) `validate_structure`, `validate_project_state`, `validate_evidence`, `validate_task_completion` = PASS; `validate_reference_integrity` = FAIL với ĐÚNG 3 issue đã biết của `TASK-REM-T06` (README ở repo root, CODE_OF_CONDUCT, CONTRIBUTING — dùng nguyên văn tên đã ghi trong `docs/tasks/TASK-REM-T06-repository-root-hygiene.md`) — không phát sinh issue mới, và KHÔNG được sửa 3 issue đó trong PRA-003; (d) `git diff --check` sạch.

Executed By:
Session S096 — PRA-003 MAJOR Implementation (Claude Code)

Timestamp:
2026-09-03

Kết quả S096:
Đo TRƯỚC (`c12c563`, chưa có file production nào của PRA-003) và SAU implementation:

```
(a) Golden Baseline
    TRƯỚC : 58 passed, 2 skipped in 6.75s
    SAU   : 58 passed, 2 skipped in 6.64s

(b) Full suite
    TRƯỚC : 1806 passed, 11 skipped in 68.36s
    SAU   : 1873 passed, 11 skipped in 76.33s
    → +67 test (không test nào bị xoá/làm yếu), skip KHÔNG tăng

(c) Validators — TRƯỚC và SAU giống hệt nhau
    validate_structure          : GOVERNANCE STRUCTURE: PASS (21 required paths)
    validate_project_state      : PROJECT STATE: PASS
    validate_evidence           : EVIDENCE VALIDATION: PASS (116 record)
    validate_task_completion    : TASK COMPLETION: PASS (10 DONE task)
    validate_reference_integrity: REFERENCE INTEGRITY: FAIL — ĐÚNG 3 issue đã biết
      - docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> /README.md
      - docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> CODE_OF_CONDUCT.md
      - docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> CONTRIBUTING.md
      → không phát sinh issue mới; 3 issue REM-T06 KHÔNG được sửa trong PRA-003

(d) git diff --check : sạch (không output)
```

Ghi chú môi trường (không phải hồi quy): lần chạy full suite đầu tiên trong container này có 1 FAIL ở `tests/test_105d_boundaries.py::TestG25GoldenBaselineUnchanged` với `fatal: bad object 740f396…` — clone ban đầu là shallow (58 commit) nên commit lịch sử đó không tồn tại cục bộ. Sau `git fetch --unshallow` (252 commit) test PASS. Đây là giới hạn của môi trường, KHÔNG phải lỗi mã; con số baseline TRƯỚC ở trên đã đo sau khi unshallow.

#### CHECK-PRA003-12 — Independent Review E2 toàn task
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E2

Evidence:
Yêu cầu: một reviewer session ĐỘC LẬP theo `governance/core/EVIDENCE_STANDARD.md` → "Quy trình Review độc lập cho Solo Developer": bắt đầu từ trạng thái thật của repository, đọc gate FROZEN này, kiểm tra diff thật, CHẠY LẠI độc lập tối thiểu CHECK-PRA003-01, -02, -03, -04, -05 (oracle golden + bất biến), ghi evidence của chính mình. Artifact lưu tại `docs/reviews/` theo `governance/templates/E2_INDEPENDENT_REVIEW_TEMPLATE.md`. Reviewer phải phân loại mọi finding thành BLOCKING / HARDENING / OUT_OF_SCOPE theo V4.1 §5 và §7; chỉ finding đe doạ 1 trong 5 điều ở mục 14 mới được mở repair cycle.

Executed By:
Session S097 — TASK-PRA-003 Independent Review E2 (Claude Code)

Timestamp:
2026-09-03

Kết quả S097 — Independent Review E2:
Artifact: `docs/reviews/TASK-PRA-003-INDEPENDENT-REVIEW-RECORD.md`.
Reviewer xác minh TRƯỚC khi đọc governance: `BASE_SHA = facf090c…`,
`REVIEW_TARGET = a36f9591…`, `CONTRACT_SHA = c12c5635…` — cả ba KHỚP, không
`REVIEW_TARGET_MOVED`. Diff `c12c563..a36f959` trên chính file task chỉ đổi các
trường ghi bằng chứng; KHÔNG oracle O-A…O-K hay Owner Decision D1–D3 nào bị
sửa chữ. `CHECK-PRA003-07` và `-12` được implementer giữ đúng `NOT_TESTED`.

Chạy lại ĐỘC LẬP (E2 — reviewer tự viết khẳng định; các tổng được recompute
bằng SQL THÔ, độc lập với `analytics_queries`, rồi mới đem so):

```
oracle golden — ba nguồn KHỚP (raw SQL · expected JSON · implementation):
  lines=351 orders=254 qty=407 sales=3562310000 · status AUTO=2 PENDING=349
  auto_orders + review_orders = 1 + 253 = 254 = orders

CHECK-01 no-double-count : A→B == B một mình · re-upload no-op · SOURCE_CHANGED chỉ version hiện hành
CHECK-03 NULL ≠ 0        : tập rỗng → None (không Decimal 0); None→'—', Decimal(0)→'0'
CHECK-04 KPI chỉ AUTO    : dòng PENDING có kpi=5.000.000 BỊ LOẠI; hai coverage khác tử số, chung mẫu số
CHECK-05 đối soát NV     : Σ khớp trên cả 5 chỉ tiêu cộng được; cột Đơn CỐ Ý không cộng được
CHECK-06 tách nguồn      : không <table> nào mang cả hai nhãn; nguon lạ → 200 về legacy; escape đúng
CHECK-08 kỳ trước vắng   : '—' chứ không 0%/-100%; biên năm Jan 2026 → Tháng 12/2025 đúng
CHECK-09 thiếu sale_date : rơi khỏi MỌI kỳ và được undated_lines() phơi ra
CHECK-10 PII             : dò bằng GIÁ TRỊ THẬT đọc ngược từ DB — không rò rỉ; không từ vựng nội bộ

test  : PRA-003 67 passed · golden 58 passed 2 skipped · legacy 34 passed
        PRA-002 vertical 12 passed · FULL SUITE 1873 passed, 11 skipped (exit 0)
budget: Python 284 (< cảnh báo mềm 320) · template 191 (≤220) · CSS 16 (≤25)
        schema/migration/index/dependency/config = 0 · Scope Lock 0 vi phạm
        tests/fixtures/golden/** KHÔNG bị sửa — oracle golden còn nguyên
```

Chứng minh CẤU TRÚC (mạnh hơn grep): PK của `order_line_current` cộng với hai
join đều trỏ vào cột `id` là PRIMARY KEY ⟹ many-to-one nghiêm ngặt, KHÔNG có
đường nhân bản cardinality; hai con trỏ hiện hành `nullable=False` ⟹ không âm
thầm đánh rơi dòng; `CheckConstraint(status IN ('AUTO','PENDING'))` ⟹ phân
hoạch thật ở cấp DB; `CheckConstraint(origin='PIPELINE_GENERATED')` trên cả ba
bảng ⟹ một dòng legacy KHÔNG THỂ lọt vào về mặt vật lý.

Finding: **0 BLOCKING**. Ba finding NON_BLOCKING —
`FIND-PRA003-01` = `CONTRACT_MISMATCH`: minh hoạ số học của O-C dẫn xuất từ
đường `run_import()` TRẦN mà `build_expected.py` dùng; đường persist thật là
`run_import_production`, nên coverage đúng của kỳ golden là `2/351`.
Implementation test ĐÚNG đường production, KHÔNG sửa fixture, và còn assert
ngược lại rằng file golden vẫn đọc ra `{Pending: 351}` — bảo tồn oracle chứ
không làm yếu. Khắc phục đúng là sửa TÀI LIỆU O-C, không sửa mã.
`FIND-PRA003-02` = `EVIDENCE_DEFECT`: 1 trailing whitespace ở
`docs/sessions/S094-…md:341` trên dải commit (chỉ file docs); dạng working-tree
của `git diff --check` đúng là sạch — hai dạng lệnh đo hai thứ khác nhau.
`FIND-PRA003-03` = `HARDENING`: một nhân viên mang hai `employee_group` sẽ hiện
thành hai dòng; bất biến cộng được vẫn đúng, kèm RE-TRIGGER CONDITION.

Không finding nào đe doạ 1 trong 5 điều kiện mục 14 ⟹ KHÔNG mở repair cycle:
`repair_cycles_used = 0`, `repair_cycles_remaining = 1`.

```
REVIEW_RESULT = ACCEPT_WITH_NON_BLOCKING_FINDINGS
```

### Budget / Performance

#### CHECK-PRA003-13 — CHANGE_BUDGET được đo và nằm trong giới hạn
Priority:
RECOMMENDED

Status:
PASS

Evidence Level:
E1

Evidence:
Yêu cầu: đo và ghi số dòng Python production mới/sửa (mục tiêu ≈255, cảnh báo mềm 320, DỪNG CỨNG 400), template (≤220), CSS (≤25), số test mới (≥30, 0 skip mới), dependency (=0), schema/migration/index (=0), config mới (=0). Nếu vượt DỪNG CỨNG: `STOP = CHANGE_BUDGET_EXCEEDED` kèm lý do real vertical cụ thể, KHÔNG âm thầm mở rộng. Lệnh đo và output nguyên văn.

Executed By:
Session S096 — PRA-003 MAJOR Implementation (Claude Code)

Timestamp:
2026-09-03

Kết quả S096:
Lệnh đo: script AST đếm dòng MÃ (bỏ dòng trống, comment và docstring) giao với tập dòng THÊM MỚI của `git diff -U0` — cùng quy ước với `TASK-PRA-002` mục 17.

```
Python production
  app/web/analytics_queries.py        117   (mục tiêu ≈120)  ✓
  app/web/analytics_presentation.py   105   (mục tiêu ≈ 80)  +25
  app/web/server.py (delta)            62   (mục tiêu ≈ 55)  + 7
  ---------------------------------------------------------------
  TỔNG                                284   mục tiêu 255 · cảnh báo mềm 320 · DỪNG CỨNG 400
                                            → TRONG NGƯỠNG, dưới cảnh báo mềm 36 dòng

Template                              191   (trần 220) ✓
  tong_quan.html          80
  _pipeline_bits.html     63
  nhan_vien.html (delta)  47
  layout.html (delta)      1

CSS thêm                               16   (trần 25) ✓
Test mới                               67   (sàn 30, 0 skip mới) ✓
Dependency mới                          0   ✓   Schema/migration/index  0 ✓
Config mới                              0   ✓   ALEMBIC_HEAD = 0002_snapshots (không đổi)
```

Vượt mục tiêu 255 là 29 dòng (11%), nằm dưới cảnh báo mềm nên KHÔNG kích hoạt BUDGET-AWARE PLAN và KHÔNG kích hoạt `STOP`. Phần vượt nằm gần hết ở `analytics_presentation`: mỗi hằng số văn bản mà frozen contract YÊU CẦU tường minh (`QUANTITY_NOTE` của D3, `ORDER_COLUMN_NOTE` của O-D′, `BOTH_SOURCES_NOTE` của mục 7, `NO_PREVIOUS_PERIOD`) là một dòng mã ở tầng này thay vì một chuỗi rải trong template — đổi lại chúng test được trực tiếp và không thể lệch giữa hai trang.

`git status --porcelain` — 8 file production/template/CSS + 3 file test, không file nào nằm trong Scope Lock FORBIDDEN:
```
 M app/web/server.py
 M app/web/static/css/tinphat-ui.css
 M app/web/templates/layout.html
 M app/web/templates/nhan_vien.html
?? app/web/analytics_presentation.py
?? app/web/analytics_queries.py
?? app/web/templates/_pipeline_bits.html
?? app/web/templates/tong_quan.html
?? tests/test_analytics_presentation.py
?? tests/test_analytics_queries.py
?? tests/test_web_pipeline_analytics.py
```

#### CHECK-PRA003-14 — Thời gian tải trang trên tập ≥12k dòng (ứng viên hardening DUY NHẤT)
Priority:
RECOMMENDED

Status:
PASS

Evidence Level:
E1

Evidence:
Yêu cầu: đo thời gian render `/tong-quan` và `/nhan-vien?nguon=moi` trên một tập ≥12.000 dòng hiện hành, ghi số đo nguyên văn. Chỉ khi ĐO ĐƯỢC > 1 giây mới được xét thêm index trên `employee_normalized` — và khi đó phải mở `SCOPE EXPANSION REQUIRED`, không tự thêm. Không đo được ⟹ `NOT_TESTED`, không suy đoán. Check này chỉ được chạy SAU khi mọi REQUIRED đã PASS (quy tắc 90/10, mục 13).

Executed By:
Session S096 — PRA-003 MAJOR Implementation (Claude Code)

Timestamp:
2026-09-03

Kết quả S096:
Đo trên tập 12.000 dòng hiện hành (9 tháng, 400 mã hàng, 12 nhân viên, trộn AUTO/PENDING và lợi nhuận thiếu), SQLite trong bộ nhớ, sau khi mọi REQUIRED check đã PASS (quy tắc 90/10):

```
nạp 12000 dòng: 1.2s
dòng hiện hành: 12000
/tong-quan?ky=tat-ca            : 28 ms (nhanh nhất trong 3 lần), 49 ms (chậm nhất)
/tong-quan?ky=2026-05           : 16 ms (nhanh nhất trong 3 lần), 21 ms (chậm nhất)
/nhan-vien?nguon=moi&ky=tat-ca  : 47 ms (nhanh nhất trong 3 lần), 64 ms (chậm nhất)
```

Chậm nhất 64 ms — kém ngưỡng 1 giây khoảng 15 lần. Điều kiện mở lại câu hỏi index trên `employee_normalized` (`FACT #5` mục 9) KHÔNG thoả, nên KHÔNG thêm index và KHÔNG mở `SCOPE EXPANSION`. Có số đo trước, không thêm trước.

---

## Yêu Cầu Evidence

| Yêu cầu | Nội dung |
|---|---|
| Risk 3 ⟹ E1 | Mọi REQUIRED check thực thi được PHẢI có E1 (output lệnh/test nguyên văn). `governance/core/EVIDENCE_STANDARD.md` |
| E2 | CHECK-PRA003-12 bắt buộc E2, artifact lưu tại `docs/reviews/` |
| Không bịa | Không bịa output lệnh, kết quả test, mã HTTP, ảnh chụp, kết quả CI, hay sự phê duyệt của con người. Chưa thực thi ⟹ `Status: NOT_TESTED` |
| Đo hai lần | CHECK-PRA003-11 phải có số đo TRƯỚC và SAU implementation, không chỉ số sau |
| Oracle đọc từ file | CHECK-PRA003-02 phải ĐỌC `period_2026_01.json`, không hard-code bốn con số |
| Production | CHECK-PRA003-07 chỉ đóng bằng bằng chứng Owner đọc trên production thật; không suy dẫn, không dựng fixture "giống production" |

---

## Tiêu Chí Hoàn Thành (Exit Criteria)

1. 12/12 REQUIRED check PASS với evidence level bắt buộc được thoả.
2. 0 BLOCKING finding chưa giải quyết; mọi `HARDENING` có RE-TRIGGER CONDITION
   cụ thể được ghi lại.
3. CHANGE_BUDGET không vượt DỪNG CỨNG, hoặc đã có quyết định Owner tường minh.
4. Review budget không vượt 1 blocking repair cycle, hoặc đã có
   `OWNER_EXTENSION`.
5. Golden Baseline `58 passed, 2 skipped`; full suite không giảm; validators
   giữ nguyên trạng thái baseline (3 issue REM-T06 đã biết, không thêm).
6. `PROJECT/PROJECT_PROGRESS.md` và `PROJECT/REVIEW_BUDGET_LEDGER.md` đã cập
   nhật.
7. Session handoff đã viết (Task Mode = MAJOR).
8. `SCHEMA_CHANGE = 0`, `MIGRATION = 0`, `DEPENDENCY = 0`, `TRACKING_CHANGED = NO`,
   `INFRASTRUCTURE_CHANGED = NO`, `PROTECTED_CORE_IMPACT = NONE`.

---

## Điều Kiện Kích Hoạt Leo Thang (Escalation Triggers)

| Kích hoạt | Hành động |
|---|---|
| Python production chạm 320 dòng | Dừng viết mã, lập BUDGET-AWARE PLAN cho phần còn lại |
| Python production sẽ vượt 400 dòng | `STOP = CHANGE_BUDGET_EXCEEDED` — Owner quyết |
| Cần sửa bất kỳ file nào trong Scope Lock FORBIDDEN | `SCOPE EXPANSION REQUIRED` — không sửa trước, hỏi trước |
| Cần một business rule chưa có thẩm quyền (đếm SP, target, margin) | Dừng — đó là N.7/N.8, Owner quyết, KHÔNG tự phát minh |
| Đã dùng hết 1 blocking repair cycle mà vẫn còn BLOCKING | `OWNER_EXTENSION REQUIRED` — không mở lineage mới, không đổi tên task để reset ngân sách (V4.1 §2) |
| Phát hiện double-count hoặc trộn nguồn trong dữ liệu đã lưu | Dừng ngay — đó là defect của PRA-002, không vá ở tầng trình bày |
| Canonical HEAD đã moved so với `BASE_SHA` | `STOP = CANONICAL_MOVED` — đồng bộ và đánh giá lại trước khi tiếp tục |

---

## Đăng Ký File Đã Thay Đổi (Changed Files Registry)

Điền trong phiên implement. Tại thời điểm freeze gate: **0 file production
thay đổi**.

| File | Loại | Delta | Phiên |
|---|---|---|---|
| `app/web/analytics_queries.py` | MỚI | 117 dòng mã | S096 |
| `app/web/analytics_presentation.py` | MỚI | 105 dòng mã | S096 |
| `app/web/templates/tong_quan.html` | MỚI | 80 dòng | S096 |
| `app/web/templates/_pipeline_bits.html` | MỚI | 63 dòng | S096 |
| `app/web/server.py` | SỬA | +62 dòng mã | S096 |
| `app/web/templates/nhan_vien.html` | SỬA | +47 dòng | S096 |
| `app/web/static/css/tinphat-ui.css` | SỬA | +16 dòng | S096 |
| `app/web/templates/layout.html` | SỬA | +1 dòng | S096 |
| `tests/test_analytics_queries.py` | MỚI (test) | 22 test | S096 |
| `tests/test_analytics_presentation.py` | MỚI (test) | 20 test | S096 |
| `tests/test_web_pipeline_analytics.py` | MỚI (test) | 25 test | S096 |

---

## Ghi Chú (Notes)

- Thứ tự triển khai bắt buộc: `analytics_queries` → `analytics_presentation`
  → route → template → CSS. Test tầng đơn vị viết TRƯỚC test route và test
  integration.
- `INFERENCE` — hai mục `NOT_NEEDED` ở mục 4 bị loại vì TRÙNG LẶP thông tin,
  không phải vì cắt an toàn. Nếu phiên implement thấy coverage KHÔNG thực sự
  phơi ra cặp `dòng AUTO / tổng dòng`, thì tiền đề của việc loại bỏ sai và
  phải mở lại ô AUTO/Review theo dòng — đây là RE-TRIGGER CONDITION tường
  minh, không phải lời hứa.
- Toàn bộ tài liệu discovery nền:
  `docs/sessions/S094-pra-003-vertical-slice-discovery.md`. Khi tài liệu này
  và S094 mâu thuẫn, **tài liệu này thắng** (S094 là discovery; các default
  D1–D3 của nó đã bị thay bằng `OWNER_DECISION` ở mục 3, và
  Minimum-Value Filter ở mục 4 đã cắt bớt so với đề xuất 12 ô của S094).
