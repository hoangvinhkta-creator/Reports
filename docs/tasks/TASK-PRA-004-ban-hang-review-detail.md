# TASK-PRA-004 — Bán Hàng + Chi Tiết Đơn/Dòng + Review Visibility (CHỈ-ĐỌC)

## Metadata
Status:
IN_PROGRESS

Phase:
PHASE-PRA — Slice 4 (truy vết từ con số tổng hợp xuống dòng hàng)

Task Mode:
MAJOR

Primary Agent Tier:
Tier B (tầng CHỈ-ĐỌC; blast radius theo failure path = hiển thị sai một đơn
hoặc một lý do kiểm tra → Owner kết luận sai về một đơn cụ thể)

Escalation Tier:
Owner (mọi business semantics chưa có thẩm quyền: quyền sở hữu đơn khi có
nhiều nhân viên, phân loại product-line, workflow duyệt/từ chối); Independent
Reviewer E2 theo `governance/templates/E2_INDEPENDENT_REVIEW_TEMPLATE.md`

Difficulty:
3/5

Risk:
3

Blast Radius:
3/5 — chấm theo failure path (`governance/core/V4_1_POLICY_FREEZE.md` §4),
KHÔNG theo tên module. Đường hỏng tệ nhất: một đơn `PENDING` hiện thành
`AUTO` (Owner tin một con số chưa chắc chắn); hoặc lợi nhuận đơn hiện đầy đủ
trong khi chỉ một phần dòng có giá trị (Owner tin "đơn này lãi X" trong khi
X chỉ là lãi của 1/4 dòng); hoặc một lý do kiểm tra bị diễn giải sai. Nghiêm
trọng vì nó ở cấp ĐƠN CỤ THỂ — Owner có thể hành động lên đúng đơn đó.
KHÔNG phải HIGH vì: toàn bộ touch area CHỈ-ĐỌC (không một câu
`INSERT`/`UPDATE`/`DELETE` nào), KHÔNG đổi dữ liệu đã lưu, KHÔNG đổi
KPI/lương đã tính, KHÔNG chạm bất biến no-double-count (bất biến đó thuộc
`TASK-PRA-002`; PRA-004 chỉ đọc lại kết quả của nó).

Project Profile:
PRODUCT

Root task lineage (V4.1): `TASK-PRA-004` (root MỚI. KHÔNG kế thừa và KHÔNG
tiêu ngân sách của `TASK-PRA-001`, `TASK-PRA-002`, `TASK-PRA-003` hay bất kỳ
lineage nào khác; đặc biệt KHÔNG kế thừa phần CHANGE_BUDGET còn dư của
PRA-003). Review budget: **MEDIUM = 1 blocking repair cycle**
(`governance/core/V4_1_POLICY_FREEZE.md` §2). Ledger:
`PROJECT/REVIEW_BUDGET_LEDGER.md` → "Root Task: TASK-PRA-004".

Kế hoạch gốc: `docs/tasks/TASK-PRA-000-persistent-reporting-analytics-plan.md`.
Nền dữ liệu: `docs/tasks/TASK-PRA-002-pipeline-persistence-reconciliation.md`
(DONE). Nền trình bày/truy vấn: `docs/tasks/TASK-PRA-003-tong-quan-nhan-vien.md`
(DONE). Nền legacy: `docs/tasks/TASK-PRA-001-legacy-reference-vertical.md` (DONE).

Discovery + Contract Freeze session: S100 (2026-09-03) —
`docs/sessions/S100-pra-004-ban-hang-review-detail-discovery.md`.
`BASE_SHA = 8181cebe0619a9c8d12604168a90914c04b3692f` (HEAD nhánh canonical
`claude/extract-upload-repo-gq2ws4` lúc freeze contract — đã verify khớp
EXACT kỳ vọng đầu phiên, `CANONICAL_MOVED = KHÔNG`).

Quy ước: file DỰ KIẾN tạo được viết KHÔNG kèm phần mở rộng (ví dụ
`app/web/sales_queries`); file đã tồn tại viết đủ đường dẫn (ví dụ
`app/web/server.py`).

Quy ước phân loại: `FACT` (đo được trong repo/dữ liệu phiên này) ·
`OWNER_DECISION` (Owner đã chốt) · `INFERENCE` (suy từ code/evidence) ·
`ASSUMPTION` (chưa verify) · `UNKNOWN`.

---

## (1) Mục Tiêu (Goal)

Từ một con số tổng hợp trên Tổng quan, Owner đi xuống được tới tận dòng hàng
và hiểu tại sao:

```
Tổng quan → Bán hàng (danh sách đơn) → Một đơn → Các dòng của đơn
          → AUTO / CẦN KIỂM TRA → Lý do cần kiểm tra
```

PRA-004 là **TRUY VẾT (traceability / drill-down)**, KHÔNG phải một
"Review Management System". Toàn bộ slice là CHỈ-ĐỌC.

Câu hỏi PRA-004 phải trả lời được, đúng thứ tự:

1. Con số tổng của kỳ được tạo từ những đơn nào?
2. Một đơn gồm những dòng hàng nào?
3. Dòng nào AUTO?
4. Dòng/đơn nào CẦN KIỂM TRA?
5. Tại sao nó cần kiểm tra?
6. Doanh thu / lợi nhuận của đơn hình thành thế nào từ các dòng hiện hành?

---

## (2) Business Authority

Thứ tự thẩm quyền (không đảo):

```
OWNER BUSINESS INTENT → ACCEPTED BUSINESS MODEL → PERSISTED DATA MODEL
                      → CURRENT CODE → TESTS
```

`FACT` — thẩm quyền đã có sẵn, PRA-004 TÁI DỤNG chứ không phát minh:

| Nội dung | Thẩm quyền | Vị trí |
|---|---|---|
| Trạng thái dòng chỉ có `AUTO` / `PENDING` | Ràng buộc DB | `tools/db/schema.py:316` `CheckConstraint(status IN ('AUTO','PENDING'))` |
| Đơn có ≥1 dòng `PENDING` ⟹ đơn CẦN KIỂM TRA | PRA-003 đã dùng và đã được Owner nghiệm thu production | `app/web/analytics_queries.py::_order_status` |
| `NULL` ≠ `0`; ô lợi nhuận luôn kèm coverage | PRA-003 mục 10 (FROZEN) | `app/web/analytics_presentation.py::profit`, `coverage` |
| Nhãn tiếng Việt cho reason code | S069, ĐANG CHẠY THẬT trên Owner Launcher + trang `/` | `app/beta_presentation.py::REASON_DISPLAY_LABELS` |
| Model kỳ (Toàn bộ dữ liệu / Tháng MM/YYYY) | PRA-003 mục 6 (FROZEN) | `app/web/analytics_queries.py::available_periods` |
| Chỉ `PIPELINE_GENERATED` được vào 3 bảng này | Ràng buộc DB × 3 bảng | `tools/db/schema.py` `ck_*_origin` |
| Đơn nhiều nhân viên: công cụ KHÔNG tự chọn chủ đơn | Đã ghi thành văn trong renderer production | `app/modules/validation/renderer.py::_order_inconsistency` |
| `product_raw` là dữ liệu nghiệp vụ (business logic ĐỌC nó), KHÔNG phải PII | GB-3, đo trên workbook production thật | `tests/fixtures/golden/anonymize.py` §"MINIMIZE trước, ANONYMIZE sau" |
| `note_raw` CÓ chứa tên + số điện thoại khách trên dữ liệu thật | GB-3, đo trên workbook production thật | `tests/fixtures/golden/anonymize.py` §"`Diễn giải` — A1" |

`ASSUMPTION / NEEDS_AUTHORITY` — KHÔNG được biến thành requirement trong
PRA-004:

- Quyền sở hữu một đơn khi các dòng mang nhiều nhân viên. `order_builder`
  hiện lấy nhân viên của dòng ĐẦU TIÊN; renderer production gọi thẳng đó là
  *"hành vi legacy, KHÔNG phải quyền sở hữu đã được xác minh"*. PRA-004
  KHÔNG dùng hành vi đó (xem mục 9).
- Phân loại product-line ("dòng nào là sản phẩm thật"). Chưa có thẩm quyền
  (PRA-003 N.7). PRA-004 KHÔNG phân loại, chỉ đếm dòng.
- Bất kỳ workflow duyệt/từ chối/gán/bình luận nào. Chưa tồn tại. Xem mục 19.

---

## (3) Owner Intent — LOCKED

Owner đang nhìn Tổng quan tháng và muốn đi xuống:

> "40 đơn này là những đơn nào? Mở một đơn ra — nó gồm những dòng gì? Dòng
> nào chắc chắn, dòng nào chưa? Vì sao chưa?"

Ví dụ production đã quan sát cho **Tháng 09/2026** (`FACT`, S099 —
**OBSERVED, KHÔNG phải oracle của PRA-004**):

```text
40 đơn · 61 dòng · AUTO 15 đơn · Cần kiểm tra 25 đơn
Tổng số lượng 71 · Doanh thu NET 593.550.000
LN KPI 8.936.667 (coverage 32/61 dòng)
LN kế toán 8.085.000 (coverage 35/61 dòng)
```

Bốn con số **40 / 61 / 15 / 25** đã là oracle FROZEN của PRA-003 và được
Owner tự tay nghiệm thu. PRA-004 tái dùng CHÍNH bốn con số đó (mục 20).
Các giá trị tiền ở trên là OBSERVED_ONLY — **KHÔNG** trở thành oracle của
PRA-004 và **KHÔNG** được viết ngược thành kỳ vọng đặt trước.

---

## (4) Current Data Capability — kết quả trace (E1, phiên S100)

Toàn bộ mục này đo được trong phiên này bằng cách chạy đường production thật
(`run_import_production` → `present_lines` → `extraction.build_*_lines` →
`history_writer.write_run_history`) trên fixture golden `period_2026_01.xlsx`
rồi truy vấn SQL trên dữ liệu đã persist.

### 4.1 Bảng và con trỏ hiện hành — `FACT`

```
order_line_current            PK (order_key, product_key, occurrence_index)
  → current_source_version_id  → order_line_source_version.id   (nullable=False)
  → current_result_version_id  → order_line_result_version.id   (nullable=False)
  sale_date (Date, nullable, đã có index ix_order_line_current_sale_date)
```

`order_key` **chính là `order_id` của engine = "Số BH"** (`app/history/keys.py`
Hợp đồng khoá) — một mã đơn NGƯỜI ĐỌC ĐƯỢC, dạng `BH<digits>`. Đây là
"mã đơn" của mục 5. `product_key` là **sha256**, KHÔNG hiển thị được.

Hệ quả cấu trúc (`FACT`): `order_key` là cột DẪN ĐẦU của PK
`order_line_current` ⟹ tra cứu/nhóm theo `order_key` đã được index sẵn,
**KHÔNG cần index mới**.

### 4.2 Trường có sẵn cho danh sách đơn và chi tiết dòng — `FACT`

| Nhu cầu mục 5 | Cột persisted | Bảng |
|---|---|---|
| mã đơn | `order_key` | `order_line_current` |
| ngày bán | `sale_date` | `order_line_current` |
| nhân viên | `employee_normalized`, `employee_group` | result version |
| số lượng | `quantity` | source version |
| doanh thu | `total_sales` | result version |
| LN KPI | `eligible_kpi_profit` | result version |
| LN kế toán | `accounting_profit` | result version |
| trạng thái | `status` | result version |
| sản phẩm | `product_raw` | source version |
| đơn giá bán | `sell_price` | source version |
| chiết khấu | `discount` | source version |
| giá vốn kế toán | `accounting_purchase_price` | result version |
| giá vốn KPI | `kpi_purchase_price` | result version |
| **lý do cần kiểm tra** | **`pending_reasons_json`** | **result version** |

**Q1 = CÓ · Q2 = CÓ.** Không thiếu trường nào cho minimum vertical.

### 4.3 Đo được trên fixture golden `period_2026_01` — `FACT` (E1)

```text
351 dòng · 254 đơn
Đơn TOÀN AUTO       : 1   (BH62063)
Đơn CẦN KIỂM TRA    : 253
Đơn TRỘN AUTO+PENDING: 1  (BH62439 — 1 dòng AUTO + 3 dòng PENDING)
Đơn nhiều ngày bán  : 0
Đơn nhiều nhân viên : 0   ← xem cảnh báo 4.6
Phân bố số dòng/đơn : {1:191, 2:41, 3:16, 4:3, 5:1, 6:1, 7:1}

Coverage / 351 dòng :
  total_sales 351 · employee_normalized 351 · employee_group 351
  product_group_final 351 · conversion_rate_final 351
  accounting_purchase_price 2 · kpi_purchase_price 2
  accounting_profit 2 · eligible_kpi_profit 2
  canonical_product_code 0        ← KHÔNG dùng được làm tên sản phẩm
  product_raw rỗng: 0/351         ← dùng được, có giá trị trên MỌI dòng
```

Đo thời gian truy vấn trên chính dữ liệu đã persist (SQLite in-memory):

```text
Q1 danh sách 254 đơn (1 câu SQL, GROUP BY order_key) : 6,6 ms
Q2 chi tiết đơn BH62439 (4 dòng)                     : 1,3 ms
```

### 4.4 Vũ trụ reason code — `FACT` (đây là câu trả lời cho Q3/Q4)

Đo trên fixture `period_2026_01` (351 dòng):

```text
IDENTITY_SOURCES_UNAVAILABLE        349
Missing.PurchasePrice               349
Pending.accounting_purchase_price   349
Pending.accounting_profit           349
Pending.eligible_kpi_profit         349
Suspicious                            8

Số reason TRÊN MỘT DÒNG: {0 reason: 2 dòng, 5 reason: 341 dòng, 6 reason: 8 dòng}
```

Đường sinh (`app/modules/exporting/excel_exporter.py::_present_lines`) cho
thấy `pending_reasons` chỉ có thể lấy giá trị từ **ba nguồn ĐÓNG**:

1. `PriceResolutionReason` — enum ĐÓNG, 10 giá trị
   (`app/modules/pricing/resolution/composition.py:158`, docstring ghi rõ
   *"Enum ĐÓNG. Không có `UNKNOWN`"*).
2. `CATEGORIES` của validation — hằng số, 8 giá trị
   (`app/modules/validation/models.py:62`).
3. Ba chuỗi `Pending.<field>` sinh từ đúng ba trường kết quả còn trống:
   `Pending.accounting_purchase_price`, `Pending.accounting_profit`,
   `Pending.eligible_kpi_profit`.

⟹ **Vũ trụ đóng tối đa 21 mã.**

Bốn tính chất quan trọng, tất cả đều là `FACT`:

- Reason nằm ở phía **RESULT**, không phải source. Có current pointer
  (`current_result_version_id`, `nullable=False`).
- MỘT dòng CÓ THỂ có NHIỀU reason (đo được: 5 hoặc 6).
- Reason là **mã ngữ nghĩa ỔN ĐỊNH**, không phải văn xuôi tự do.
- `details` (văn xuôi có chứa số dòng, `order_id`, thông điệp chẩn đoán)
  **KHÔNG được persist** — chỉ `reasons` đi vào `pending_reasons_json`
  (`app/web/history_store.py:662`). Vì vậy **không có đường nào** để stack
  trace, ID nội bộ, hay snapshot/version ID lọt vào lý do đã lưu.

### 4.5 Số học lợi nhuận đọc được từ chính các trường persisted — `INFERENCE`

Đo trên dòng AUTO của BH62439 (`FACT`):

```text
qty=2 · sell_price=10.500.000 · discount=100.000 · delivery_cost=None
total_sales (net) = 20.900.000 = 2 × 10.500.000 − 100.000
accounting_purchase_price = 10.250.000
accounting_profit = 500.000   = 2 × 10.500.000 − 2 × 10.250.000   (KHÔNG trừ chiết khấu)
eligible_kpi_profit = 400.000 = 20.900.000     − 2 × 10.250.000   (CÓ trừ chiết khấu)
```

`INFERENCE` — trên quan sát này, khoảng chênh giữa LN kế toán và LN KPI được
giải thích TRỌN VẸN bởi `discount`, một trường **đã persisted**. Đây là lý do
`Chiết khấu` được xếp `REQUIRED_NOW` ở mục 12.

**Giới hạn trung thực của suy luận này (phải giữ nguyên, không được nới):**
fixture chỉ có **2 dòng AUTO**, và cả hai đều có `delivery_cost = None`
(trong khi 325/351 dòng của kỳ CÓ `delivery_cost`). Vì vậy PRA-004
**KHÔNG được in một công thức** lên trang và **KHÔNG được tuyên bố** trang
tự dẫn xuất lại lợi nhuận. Trang chỉ hiển thị các số ĐÃ LƯU cạnh nhau để
Owner tự đối chiếu. Xem FIND-PRA004-01 (mục 22).

### 4.6 Cảnh báo về "0 đơn nhiều nhân viên" — `INFERENCE`, KHÔNG phải `FACT` về production

Fixture golden đã ẩn danh và mọi dòng đều mang `employee_normalized = 'Tín Phát'`.
Vì vậy **"0 đơn nhiều nhân viên" là hệ quả của ẩn danh hoá, KHÔNG phải bằng
chứng về dữ liệu production.** Thẩm quyền ngược lại đã tồn tại thành văn:

- `app/modules/validation/renderer.py::_order_inconsistency` render câu
  *"Đơn X có N nhân viên khác nhau trên các dòng"*;
- `app/web/analytics_presentation.py::ORDER_COLUMN_NOTE` (PRA-003, đang chạy
  production) khẳng định một đơn có nhiều nhân viên được đếm ở TỪNG dòng
  nhân viên.

⟹ PRA-004 PHẢI thiết kế cho n ≥ 1 nhân viên/đơn (mục 9), dù chưa quan sát
được ca đó.

---

## (5) Order Model — FROZEN

Một "đơn" của PRA-004 = tập các dòng **hiện hành** cùng `order_key`, trong kỳ
đang xem.

```
NGUỒN     : order_line_current JOIN current_result_version JOIN current_source_version
LỌC KỲ    : sale_date IS NOT NULL [AND >= date_from] [AND <= date_to]
            (giống HỆT _period() của PRA-003 — kể cả "Toàn bộ dữ liệu")
NHÓM      : GROUP BY order_key
```

Ngữ nghĩa từng trường cấp đơn (FROZEN):

| Trường | Dẫn xuất | Ghi chú |
|---|---|---|
| mã đơn | `order_key` | Chính là Số BH |
| ngày bán | `MIN(sale_date)` … `MAX(sale_date)` | Bằng nhau ⟹ hiện MỘT ngày. Khác nhau ⟹ hiện KHOẢNG + chú thích. KHÔNG chọn một ngày làm đại diện |
| nhân viên | tập `DISTINCT employee_normalized` | Xem mục 9 |
| số dòng | `COUNT(*)` | Mẫu số của cả hai coverage |
| tổng số lượng | `SUM(quantity)` | KHÔNG coalesce về 0 |
| doanh thu (net) | `SUM(total_sales)` | KHÔNG coalesce về 0 |
| LN KPI | `SUM(CASE WHEN status='AUTO' THEN eligible_kpi_profit END)` | Giống HỆT `_metrics()` của PRA-003 |
| LN kế toán | `SUM(accounting_profit)` | `SUM` tự bỏ qua `NULL` |
| trạng thái | `MAX(CASE WHEN status='PENDING' THEN 1 ELSE 0)` | Xem mục 7 |

**Bất biến no-double-count (FROZEN).** PK của `order_line_current` là
`(order_key, product_key, occurrence_index)` và cả hai join đều trỏ vào cột
`id` PRIMARY KEY của bảng version ⟹ quan hệ many-to-one NGHIÊM NGẶT, mỗi khoá
dòng góp ĐÚNG MỘT bản ghi. No-double-count là tính chất của CẤU TRÚC BẢNG,
không phải của việc câu truy vấn có nhớ `DISTINCT` hay không.

**CẤM tuyệt đối:** cộng `source_snapshot.summary_json` qua các run; đọc
version cũ; aggregate lịch sử snapshot. **CHỈ trạng thái hiện hành.**

---

## (6) Line Model — FROZEN

Các dòng của một đơn = các bản ghi `order_line_current` có `order_key` đó,
sắp xếp theo `occurrence_index` tăng dần (thứ tự ổn định, dẫn xuất từ
`source_row` — xem `app/history/keys.py`).

Mỗi dòng hiển thị đúng các trường ở mục 12.B. Không trường nào khác.

`Doanh thu dòng` = `order_line_result_version.total_sales` — **đọc thẳng từ
giá trị đã lưu**, KHÔNG tính lại trong PRA-004.

---

## (7) Order Status Model — FROZEN, TÁI DỤNG NGUYÊN VẸN

```
đơn có ≥ 1 dòng status = 'PENDING'  →  CẦN KIỂM TRA
đơn không có dòng PENDING nào        →  AUTO
```

Đây ĐÚNG là `analytics_queries._order_status()` mà PRA-003 đã dùng và Owner
đã nghiệm thu trên production (15 AUTO / 25 Review, Tháng 09/2026).

**KHÔNG phát minh trạng thái mới.** Cấm thêm `PARTIAL`, `WARNING`,
`RESOLVED`, `APPROVED`, hay bất kỳ trạng thái nào khác.

Ca TRỘN là ca thật và đã có oracle: **BH62439** có 1 dòng `AUTO` + 3 dòng
`PENDING` ⟹ đơn = **CẦN KIỂM TRA**. Một triển khai đọc nhầm (ví dụ lấy
trạng thái của dòng đầu tiên) sẽ hiện đơn này thành `AUTO` và bị
CHECK-PRA004-05 bắt.

---

## (8) Review Reason Model — FROZEN

### 8.1 Nguồn

`order_line_result_version.pending_reasons_json` của version **hiện hành**
(`order_line_current.current_result_version_id`). JSON array các chuỗi mã.

### 8.2 Trả lời trực tiếp các câu hỏi bắt buộc của mục 6 chỉ thị

| Câu hỏi | Trả lời | Loại |
|---|---|---|
| Reason nằm ở field nào? | `pending_reasons_json` | `FACT` |
| Persisted ở đâu? | `order_line_result_version` | `FACT` |
| Có current pointer không? | CÓ — `current_result_version_id`, `nullable=False` | `FACT` |
| Thuộc source hay result? | **RESULT** | `FACT` |
| Nhiều reason trên một dòng? | CÓ — đo được 5 hoặc 6 | `FACT` |
| Mã ổn định hay text? | **MÃ ỔN ĐỊNH**, vũ trụ đóng ≤ 21 mã | `FACT` |
| Có PII / chẩn đoán nội bộ không? | KHÔNG — `details` không được persist | `FACT` |
| Trình bày trực tiếp cho Owner được không? | CÓ, sau khi ánh xạ qua bảng nhãn tiếng Việt đã có | `INFERENCE` |

### 8.3 Trình bày — TÁI DỤNG thẩm quyền đã có

`app/beta_presentation.py::REASON_DISPLAY_LABELS` **đã tồn tại và đang chạy
production** (Owner Launcher S069 + trang kết quả `/` qua
`server._review_reason_lines`). PRA-004 **TÁI DỤNG chính bảng đó**.

7 nhãn hiện có **GIỮ NGUYÊN TỪNG CHỮ** — chúng đang hiển thị cho Owner ở nơi
khác, đổi chúng là đổi một UI đã được chấp nhận:

```
IDENTITY_UNRESOLVED               → Chưa nhận diện sản phẩm
TRACKING_HISTORY_PENDING          → Thiếu giá lịch sử Tracking
Missing.PurchasePrice             → Thiếu giá mua tham chiếu
Pending.accounting_purchase_price → Thiếu giá nhập kế toán
Pending.accounting_profit         → Thiếu lợi nhuận kế toán
Pending.eligible_kpi_profit       → Thiếu lợi nhuận KPI
Suspicious                        → Bất thường
```

PRA-004 **MỞ RỘNG** bảng để phủ TRỌN vũ trụ đóng 21 mã (14 mã còn lại). Đây
là ánh xạ tối thiểu theo §15 chỉ thị, **KHÔNG phải một taxonomy mới**: tập mã
đã đóng sẵn ở tầng engine, PRA-004 chỉ đặt tên tiếng Việt cho phần chưa có
tên.

Ràng buộc lên các nhãn mới (FROZEN):

- Một câu ngắn, hướng NGHIỆP VỤ, đọc được bởi người không rành kỹ thuật.
- KHÔNG chứa: ID nội bộ, `snapshot_id`/`run_id`/version id, tên bảng, tên
  cột, tên enum tiếng Anh, số dòng nguồn, exception, stack trace.
- KHÔNG hứa hành động ("hãy duyệt", "cần sửa") — PRA-004 CHỈ-ĐỌC.

Hành vi khi gặp mã chưa có nhãn: **giữ nguyên hành vi hiện tại** —
`REASON_DISPLAY_LABELS.get(reason, reason)`, tức hiện nguyên văn mã, KHÔNG
che giấu. CHECK-PRA004-04 khẳng định bảng là TOÀN PHẦN trên vũ trụ đóng nên
nhánh dự phòng này không bao giờ chạy trên dữ liệu thật.

### 8.4 Hiển thị nhiều reason

Một dòng có nhiều reason ⟹ hiện **TẤT CẢ**, đã khử trùng lặp, theo ĐÚNG thứ
tự đã persist. **KHÔNG** gộp, **KHÔNG** chọn "reason chính", **KHÔNG** cắt
bớt: mọi quy tắc ưu tiên/gộp đều là nghiệp vụ mới chưa có ai quyết.

---

## (9) Employee Model — FROZEN

Nhân viên của một đơn = **tập `DISTINCT employee_normalized`** trên các dòng
hiện hành của đơn đó trong kỳ.

```
n = 1  → hiện đúng tên đó
n ≥ 2  → hiện TẤT CẢ tên, nối bằng " · ", kèm chú thích:
         "Đơn này có nhiều nhân viên trên các dòng. Reports KHÔNG tự chọn
          chủ đơn."
NULL hoặc chuỗi rỗng → "Chưa xác định nhân viên"
         (tái dụng analytics_presentation.UNKNOWN_EMPLOYEE; PRA-003 đã gộp
          NULL và "" thành cùng một tình trạng ở tầng SQL)
```

**CẤM** lấy nhân viên của dòng đầu tiên. `order_builder` làm vậy, và
`renderer.py::_order_inconsistency` gọi đúng tên hành vi đó là *"hành vi
legacy, KHÔNG phải quyền sở hữu đã được xác minh"*. Sao chép nó vào một màn
hình quản lý là biến một hành vi legacy thành một khẳng định về quyền sở hữu.

PRA-004 **KHÔNG phát minh** ownership rule. Nó trình bày SỰ THẬT của dữ liệu
hiện hành: đơn này liên quan tới những nhân viên nào.

---

## (10) Period Model — FROZEN, ĐỒNG NHẤT VỚI TỔNG QUAN

Tái dụng NGUYÊN VẸN PRA-003:

- Hai loại kỳ duy nhất: **Toàn bộ dữ liệu** và **Tháng MM/YYYY**.
- Cùng tham số URL `ky` (`tat-ca` hoặc `YYYY-MM`).
- Cùng `analytics_queries.available_periods()` / `month_bounds()`.
- Cùng `analytics_presentation.period_options()` / `period_label()`.
- Cùng quy tắc dự phòng: `ky` không hợp lệ ⟹ rơi về "Toàn bộ dữ liệu", KHÔNG
  HTTP 500, KHÔNG bảng toàn số 0 cho một tháng bịa.
- Cùng bất biến `sale_date IS NOT NULL` trong MỌI kỳ.

**KHÔNG thêm** khoảng ngày tuỳ chọn, quý, năm, tuần.

Điều này bảo đảm điều kiện nghiệm thu quan trọng nhất của mục 20: Owner chọn
"Tháng 09/2026" ở CẢ HAI trang và thấy CÙNG một tập đơn.

---

## (11) Profit / Coverage Model — FROZEN

Giữ nguyên toàn bộ kỷ luật PRA-003 mục 10:

1. **`NULL` ≠ `0`.** Không coalesce ở tầng truy vấn. Không có giá trị có
   thẩm quyền ⟹ hiện `—`, KHÔNG BAO GIỜ `0`, `0đ`, `0%`.
2. **Mọi ô lợi nhuận đi kèm coverage của chính nó** (quy tắc P4). Tái dụng
   `analytics_presentation.profit()` / `coverage()` — dạng `N / M dòng`, cố
   ý KHÔNG dùng phần trăm.
3. **LN KPI chỉ cộng dòng `AUTO`.** Một dòng `PENDING` có
   `eligible_kpi_profit` khác `NULL` vẫn KHÔNG vào tổng.
4. **LN kế toán cộng mọi dòng có giá trị.**

### Coverage một phần ở CẤP ĐƠN — quy tắc mới của PRA-004 (Q7)

Đây là rủi ro đặc thù của PRA-004 và nó có oracle thật:

```text
BH62439 · 4 dòng · doanh thu net 66.000.000
  LN kế toán = 500.000   nhưng CHỈ 1/4 dòng có giá trị
  LN KPI     = 400.000   nhưng CHỈ 1/4 dòng là AUTO
```

Hiện "Lợi nhuận đơn = 500.000" trần trụi sẽ khiến Owner tin đó là lợi nhuận
của CẢ đơn 66 triệu. Đó chính là failure path ở Blast Radius.

**Quy tắc FROZEN:** trên danh sách đơn LẪN trang chi tiết đơn, mỗi ô lợi
nhuận cấp đơn PHẢI mang coverage `N / M dòng` của chính nó, dùng CHÍNH
`analytics_presentation.profit()`. Không có đường nào render lợi nhuận đơn
mà thiếu mẫu số.

Thêm: khi đơn có `coverage < số dòng`, trang chi tiết hiện một câu cảnh báo
tường minh rằng con số này chỉ tổng hợp các dòng đã có giá trị, không phải
lợi nhuận của toàn đơn.

---

## (12) Minimum-Value Filter — kết quả

Quy tắc: mỗi `REQUIRED_NOW` phải trả lời được *"Nếu bỏ field này, Owner mất
khả năng quyết định/kiểm tra điều gì?"*. Không trả lời được ⟹ CUT hoặc DEFER.

### 12.A Danh sách đơn — `/ban-hang`

| Cột | Phân loại | Bỏ đi thì Owner mất gì |
|---|---|---|
| Mã đơn (Số BH) | REQUIRED_NOW | Không định danh được đơn để mở ra, không đối chiếu được với sổ |
| Ngày bán | REQUIRED_NOW | Không định vị đơn trong kỳ |
| Nhân viên | REQUIRED_NOW | Không nối được về trang Nhân viên đã có |
| Số dòng | REQUIRED_NOW | Mất mẫu số của cả hai coverage |
| Tổng số lượng | REQUIRED_NOW | Không thấy quy mô đơn |
| Doanh thu (net) | REQUIRED_NOW | Chính là con số cần truy vết |
| LN KPI + coverage | REQUIRED_NOW | Không truy vết được ô LN KPI của Tổng quan |
| LN kế toán + coverage | REQUIRED_NOW | Không truy vết được ô LN kế toán của Tổng quan |
| Trạng thái AUTO / CẦN KIỂM TRA | REQUIRED_NOW | Chính là câu hỏi 3 và 4 của mục 1 |

`USEFUL_BUT_DEFER`: sắp xếp theo cột tuỳ ý · lọc theo trạng thái · lọc theo
nhân viên · tìm kiếm mã đơn · so kỳ trước theo đơn · nhóm nhân viên
(`employee_group`).

`NOT_NEEDED`: `product_group_final` cấp đơn · `lead_source_final` ·
`conversion_*` · số snapshot/run · thời điểm cập nhật.

### 12.B Chi tiết đơn — `/ban-hang/<order_key>`

Khối đầu trang (tái dụng đúng các ô của 12.A cho MỘT đơn): mã đơn, ngày bán,
nhân viên, trạng thái, số dòng, tổng số lượng, doanh thu, LN KPI + coverage,
LN kế toán + coverage.

Bảng dòng hàng:

| Cột | Phân loại | Bỏ đi thì Owner mất gì |
|---|---|---|
| Sản phẩm (`product_raw`) | REQUIRED_NOW | Không phân biệt được các dòng với nhau. `canonical_product_code` = 0/351 nên KHÔNG thay thế được |
| Số lượng | REQUIRED_NOW | Không kiểm được doanh thu dòng |
| Đơn giá bán | REQUIRED_NOW | Không kiểm được doanh thu dòng |
| Chiết khấu | REQUIRED_NOW | Không giải thích được chênh lệch giữa `SL × đơn giá` và doanh thu dòng, cũng như giữa hai loại lợi nhuận (mục 4.5) |
| Doanh thu dòng | REQUIRED_NOW | Không thấy dòng nào đóng góp bao nhiêu vào tổng đơn |
| Giá vốn (kế toán) | REQUIRED_NOW | Không kiểm được LN kế toán |
| Giá vốn (KPI) | REQUIRED_NOW | Không kiểm được LN KPI khi nó khác giá vốn kế toán — xem 12.C |
| LN kế toán dòng | REQUIRED_NOW | Không thấy dòng nào tạo ra lợi nhuận |
| LN KPI dòng | REQUIRED_NOW | Không thấy dòng nào tạo ra lợi nhuận KPI |
| Trạng thái AUTO / CẦN KIỂM TRA | REQUIRED_NOW | Chính là câu hỏi 3 và 4 |
| Lý do cần kiểm tra | REQUIRED_NOW | Chính là câu hỏi 5 |

Lý do hiển thị dưới dạng **dòng phụ ngay dưới dòng hàng PENDING**, KHÔNG
phải một cột — một dòng có tới 6 lý do, nhét vào ô bảng là không đọc được.

`USEFUL_BUT_DEFER`: `delivery_cost` (xem 12.C) · `product_group_final` ·
`employee_normalized` theo TỪNG dòng (chỉ cần khi đơn có nhiều nhân viên) ·
liên kết sang trang Nhân viên.

`NOT_NEEDED`: `canonical_product_code` (0/351) · `identity_namespace` ·
`conversion_scheme_final` · `conversion_rate_final` · `price_source` ·
`kpi_purchase_provenance` · `composition_rule` · `result_fingerprint` ·
`row_hash` · `line_fingerprint` · `occurrence_index` · `source_row`.

`PROHIBITED_FROM_MANAGEMENT_UI`: xem mục 14.

### 12.C Quyết định về hai giá vốn — Q8

`§10` của chỉ thị yêu cầu KHÔNG mặc định đưa cả Y và PP lên UI, và yêu cầu
đề xuất tập giá TỐI THIỂU để hiểu con số. Quyết định và lý do:

- `accounting_purchase_price` = **REQUIRED_NOW**. Không có nó, LN kế toán
  không kiểm được bằng bất cứ cách nào.
- `kpi_purchase_price` = **REQUIRED_NOW**. Lý do KHÔNG phải "có sẵn thì
  hiện": trang hiển thị **HAI** loại lợi nhuận, và theo business semantics đã
  khoá (`§10` chỉ thị: Y = giá vốn hệ thống, PP = Public Purchase do Owner
  kiểm soát, KPI dùng PP tại ngày bán) hai lợi nhuận đó có HAI cơ sở giá
  KHÁC NHAU. Hiện một giá cho hai lợi nhuận là để một trong hai con số
  vĩnh viễn không kiểm được, và tệ hơn — dẫn Owner đối chiếu bằng cơ sở
  SAI. Tập tối thiểu để hiểu HAI con số là ĐÚNG HAI cơ sở giá, ánh xạ 1:1.
  `FACT`: trên 2/2 dòng AUTO quan sát được, hai giá TRÙNG nhau; đây KHÔNG
  phải bằng chứng chúng luôn trùng.
- `price_source` và `kpi_purchase_provenance` = **NOT_NEEDED**. Chúng là enum
  nội bộ (`OWNER_MANUAL_LEGACY_CONFIRMATION`, `Config:NoConfirmedAdjustment`,
  `Pending`) — từ vựng nội bộ, bị cấm bởi mục 14.
- `delivery_cost` = **USEFUL_BUT_DEFER**, kèm RE-TRIGGER CONDITION tường
  minh: kích hoạt lại khi gặp một dòng `AUTO` có `delivery_cost` khác `NULL`
  mà lợi nhuận của nó KHÔNG khớp với số học ở mục 4.5. Chưa quan sát được ca
  đó (2/2 dòng AUTO đều có `delivery_cost = NULL`), nên chưa trả lời được câu
  hỏi Minimum-Value ⟹ DEFER, không CUT.

**Trang KHÔNG in công thức.** Nó đặt các số đã lưu cạnh nhau; Owner tự đối
chiếu. Xem FIND-PRA004-01.

---

## (13) Source Separation — FROZEN

**PRA-004 = SỐ MỚI (`PIPELINE_GENERATED`) ONLY.**

`FACT`: cả ba bảng (`order_line_current`, `order_line_source_version`,
`order_line_result_version`) đều mang `CheckConstraint(origin = 'PIPELINE_GENERATED')`
(`tools/db/schema.py` — `ck_order_line_current_origin`,
`ck_source_version_origin`, `ck_result_version_origin`). Dòng
`LEGACY_REFERENCE` **KHÔNG THỂ** lọt vào về mặt vật lý. Tách nguồn ở PRA-004
là tính chất CẤU TRÚC, không phải một bộ lọc phải nhớ viết.

**KHÔNG** xây drill-down cho Legacy. Legacy Reference đã có mục đích riêng
(PRA-001) và không có business need trực tiếp nào ở đây.

Mọi con số trên hai trang mới đều mang badge **SỐ MỚI** (tái dụng
`_pipeline_bits.html::pipeline_badge`) — không có đường nào render một số mới
mà thiếu nhãn nguồn.

---

## (14) PII Boundary — FROZEN

Trang chi tiết đi sâu hơn PRA-003, nên ranh giới được audit lại từ đầu.

### 14.1 KHÔNG TỒN TẠI trong dữ liệu đã lưu — `FACT`

`grep` trên `tools/db/schema.py` cho `customer`, `phone`, `address`,
`shipper`, `warranty`: **0 kết quả**. Các trường này bị `normalizer` chép qua
`WorkingLine` nhưng **KHÔNG BAO GIỜ được persist** vào ba bảng pipeline.

⟹ Chúng **không thể** rò rỉ qua PRA-004. Đây là bảo đảm CẤU TRÚC, mạnh hơn
một quy ước.

### 14.2 CÓ trong dữ liệu đã lưu — phân loại từng trường

| Trường | Phân loại | Lý do |
|---|---|---|
| `imei` | **PROHIBITED_FROM_MANAGEMENT_UI** | Định danh thiết bị. `anonymize.py` XOÁ HẲN vì KHÔNG rule nghiệp vụ nào đọc nó. Không có business value nào cho drill-down doanh thu/lợi nhuận |
| `note_raw` | **PROHIBITED_FROM_MANAGEMENT_UI** | `anonymize.py` §"`Diễn giải` — A1": trên dữ liệu thật trường này **CÓ chứa tên và số điện thoại khách**. Đây là PII trực tiếp |
| `employee_raw` | **PROHIBITED_FROM_MANAGEMENT_UI** | Chuỗi thô chưa chuẩn hoá. `employee_normalized` là dạng đã có thẩm quyền và PRA-003 đã dùng |
| `source_profit` | **PROHIBITED** (không phải PII) | PRA-003 Owner Decision D1/D2 đã loại tường minh; `test_the_overview_never_shows_source_profit_or_a_target` canh nó |
| `product_raw` | **REQUIRED_NOW** | `anonymize.py` phân loại là dữ liệu NGHIỆP VỤ được business logic ĐỌC (`rules.is_non_product_line()`, `ProductGroupProvider.classify()`), giữ NGUYÊN VĂN trong fixture, KHÔNG thay surrogate, KHÔNG xoá. Đo được: 0/351 dòng rỗng |
| `delivery_cost` | USEFUL_BUT_DEFER | Không phải PII; xem 12.C |

### 14.3 Từ vựng nội bộ — cấm như PII

Cấm xuất hiện trên hai trang mới (tái dụng danh sách của
`tests/test_web_pipeline_analytics.py::INTERNAL_VOCABULARY` và mở rộng cho
PRA-004): `snapshot_id`, `run_id`, `coverage_state`, `source_version`,
`result_version`, `reconciliation_flag`, `PIPELINE_GENERATED`,
`LEGACY_REFERENCE`, `price_source`, `kpi_purchase_provenance`,
`composition_rule`, `identity_namespace`, `result_fingerprint`, `row_hash`,
`line_fingerprint`, `product_key`, `occurrence_index`, đường dẫn tuyệt đối.

### 14.4 Xung đột đã phát hiện và cách giải quyết — KHÔNG nới lỏng gate nào

```
CONFLICT DETECTED

Documentation:
  app/web/analytics_queries.py (docstring) liệt kê `product_raw` chung nhóm
  "PII / dữ liệu cá nhân" cùng imei/note_raw/employee_raw, và
  tests/test_analytics_queries.py::test_the_query_module_never_selects_a_personal_data_column
  canh điều đó bằng cách đọc CHÍNH file analytics_queries.py.

Implementation:
  tests/fixtures/golden/anonymize.py — phân loại được đo trên workbook
  production THẬT (GB-3, Owner Decision OD-GB-1) — xếp `product_raw` vào
  nhóm dữ liệu NGHIỆP VỤ được business logic ĐỌC, giữ nguyên văn, và chỉ
  XOÁ HẲN address/phone/shipper_raw/imei.

Risk:
  PRA-004 cần tên sản phẩm để phân biệt các dòng trong một đơn.
  `canonical_product_code` = 0/351 nên không thay thế được. Nếu mở rộng
  analytics_queries.py để đọc `product_raw`, test PII của PRA-003 sẽ ĐỎ —
  và "sửa test cho xanh" là làm yếu một gate đã accepted.

Recommended resolution (ĐÃ ÁP DỤNG trong contract này):
  PRA-004 KHÔNG chạm `app/web/analytics_queries.py` và KHÔNG sửa
  tests/test_analytics_queries.py. Nó tạo module truy vấn RIÊNG
  (`app/web/sales_queries`) với hàng rào PII RIÊNG, hẹp hơn đúng một
  trường: imei, note_raw, employee_raw, customer, phone, address —
  `product_raw` KHÔNG nằm trong hàng rào đó.
  Kết quả: gate PRA-003 tiếp tục PASS NGUYÊN VẸN, và ranh giới PII của
  PRA-004 được phát biểu tường minh thay vì thừa kế ngầm.
```

CHECK-PRA004-09 và CHECK-PRA004-10 canh cả hai phía.

---

## (15) Minimum UI — FROZEN

### 15.1 Điều hướng

**Option A** (chỉ thị mục 13): thêm MỘT tab **"Bán hàng"** vào
`app/web/templates/layout.html`, đặt giữa "Tổng quan" và "Nhân viên".

**Option B** (bấm vào ô số trên Tổng quan để nhảy sang Bán hàng cùng kỳ) =
**USEFUL_BUT_DEFER, KHÔNG triển khai.** Nó kéo theo tham số lọc trạng thái
(AUTO / cần kiểm tra) mà minimum vertical không cần, cộng thêm test và bề mặt
contract. Owner chọn kỳ một lần trên mỗi trang — ma sát nhỏ, chấp nhận được.
Mục tiêu là TRUY VẾT, không phải độ tinh vi UX.

### 15.2 Hai route

```
GET /ban-hang                 → danh sách đơn của kỳ (bộ chọn kỳ giống Tổng quan)
GET /ban-hang/<order_key>     → chi tiết một đơn
```

`/ban-hang/<order_key>` với `order_key` không tồn tại ⟹ **HTTP 404**, KHÔNG
phải một trang rỗng trông như "đơn này không có dòng nào".

Không có kho dữ liệu (`snapshot_repo is None`) ⟹ **HTTP 503**, giống HỆT
`/tong-quan`. Lỗi database KHÔNG BAO GIỜ được biến thành "chưa có dữ liệu" —
tái dụng `_guarded` + `HistoryUnavailableError` của PRA-003.

### 15.3 Kiểu dáng

Tái dụng NGUYÊN VẸN ngôn ngữ UI hiện có: `layout.html`, `tinphat-ui.css`,
macro của `_pipeline_bits.html` (`pipeline_badge`, `source_note`, `kpi`,
`profit_kpi`, `period_picker`, `profit_cells`). **KHÔNG** thiết kế lại,
**KHÔNG** thêm framework, **KHÔNG** thêm JavaScript.

---

## (16) Read-Only Boundary — FROZEN

```
PRA-004 = READ ONLY. TUYỆT ĐỐI.
```

- KHÔNG `INSERT` / `UPDATE` / `DELETE`.
- KHÔNG approve / reject / resolve / assign / comment.
- KHÔNG write-back sang Tracking.
- KHÔNG sửa business state đã lưu.
- KHÔNG có review history UI, workflow, notification.

Bằng chứng phải là **CẤU TRÚC**, không phải grep chuỗi: tái dụng đúng khuôn
`test_the_query_module_never_writes_and_never_reads_a_run_summary` của
PRA-003 (kiểm bằng AST: không import `insert`/`update`/`delete`/`text`,
không gọi `begin()`/`commit()`/`execution_options()`; SQLAlchemy 2.0 không
autocommit ⟹ không tồn tại đường ghi). Xem CHECK-PRA004-01.

Nếu phiên implement thấy CẦN ghi: **DỪNG**, phân loại
`ARCHITECTURE_CHANGE_REQUIRED`, không tự triển khai.

---

## (17) Quyết định kiến trúc / hạ tầng

| Câu hỏi | Trả lời | Bằng chứng |
|---|---|---|
| Q11 — Cần pagination ngay không? | **KHÔNG** | 254 đơn / 6,6 ms đo được phiên này; production 09/2026 = 40 đơn; tool phục vụ 2–3 người xem (§22 chỉ thị). Thay vào đó: CHECK-PRA004-13 ĐO trên tập ≥12k dòng và ghi RE-TRIGGER CONDITION |
| Q12 — Cần schema / migration không? | **KHÔNG** | Mọi trường của mục 12 đã persisted. `order_key` là cột dẫn đầu PK `order_line_current` ⟹ đã index. `ix_order_line_current_sale_date` đã tồn tại |
| Q13 — Cần production write không? | **KHÔNG** | Mục 16 |
| Q14 — Cần đổi Tracking không? | **KHÔNG** | Reports = write scope DUY NHẤT. Không một trường nào của mục 12 cần dữ liệu Tracking mới; tất cả đã nằm trong ba bảng pipeline |
| Dependency mới? | **0** | SQLAlchemy / Flask / Jinja đã có |
| Service / worker / queue / cache / search mới? | **0** | Architecture hiện tại đủ |

---

## (18) Touch Area / Scope Lock

### ĐƯỢC PHÉP tạo mới

```
app/web/sales_queries                          (tầng SQL CHỈ-ĐỌC của PRA-004)
app/web/sales_presentation                     (định dạng + gắn nhãn)
app/web/templates/ban_hang.html
app/web/templates/ban_hang_chi_tiet.html
tests/test_sales_queries.py
tests/test_sales_presentation.py
tests/test_web_sales_detail.py
docs/sessions/S1xx-*.md
docs/reviews/TASK-PRA-004-INDEPENDENT-REVIEW-RECORD.md
```

### ĐƯỢC PHÉP sửa (giới hạn chặt)

```
app/web/server.py                     — CHỈ thêm 2 route mới + helper của chúng
app/beta_presentation.py              — CHỈ THÊM key vào REASON_DISPLAY_LABELS.
                                        KHÔNG đổi 7 nhãn hiện có. KHÔNG đổi
                                        chữ ký hay hành vi format_review_reasons
app/web/templates/layout.html         — CHỈ thêm 1 dòng tab "Bán hàng"
app/web/templates/_pipeline_bits.html — CHỈ THÊM macro mới; KHÔNG sửa macro cũ
app/web/static/css/tinphat-ui.css     — CHỈ THÊM
PROJECT/PROJECT_PROGRESS.md
PROJECT/LO_TRINH_DE_HIEU.md
PROJECT/REVIEW_BUDGET_LEDGER.md
docs/tasks/TASK-PRA-004-ban-hang-review-detail.md
```

### CẤM (SCOPE EXPANSION REQUIRED nếu cần chạm)

```
app/web/analytics_queries.py          ← PRA-003 đã accepted; xem 14.4
app/web/analytics_presentation.py     ← chỉ ĐƯỢC import, KHÔNG được sửa
app/web/templates/tong_quan.html
app/web/templates/nhan_vien.html
tests/test_analytics_queries.py
tests/test_analytics_presentation.py
tests/test_web_pipeline_analytics.py
tools/db/**                           ← schema, migration
app/history/**                        ← core persistence/reconciliation
app/web/history_store.py
app/web/history_writer.py
app/web/run_registry.py
app/web/storage_backend.py
app/modules/**                        ← protected core
app/pipeline.py · app/composition.py · app/demo.py
tests/fixtures/golden/**              ← oracle độc lập, KHÔNG sửa một byte
config/**
alembic.ini · render.yaml · Dockerfile · pyproject.toml
Toàn bộ Tracking
```

`PROTECTED_CORE_IMPACT` phải = `NONE`.

---

## (19) Hard Exclusions

PRA-004 **KHÔNG** bao gồm, dưới bất kỳ hình thức nào:

```
PRA-005 Product Analytics · biểu đồ · trend · target · margin analytics · YTD
khoảng ngày tuỳ chọn · phân tích quý/năm · thiết kế lại export
Review workflow · duyệt/từ chối · gán việc · bình luận · thông báo · write-back
review history UI · CRM khách hàng · quy trình bảo hành · quản lý IMEI
quản lý tồn kho · sửa đổi Tracking · hệ thống auth mới · database mới
worker · queue · service mới · dependency mới (trừ khi không thể tránh)
quy mô enterprise · refactor tổng quát
REM-T06 repair · FIND-PRA003-03 repair · rare Product Identity discovery
```

`FIND-PRA003-03` (một `employee_normalized` mang hai `employee_group`) giữ
nguyên trạng thái DEFER với RE-TRIGGER CONDITION đã ghi trong
`docs/reviews/TASK-PRA-003-INDEPENDENT-REVIEW-RECORD.md`. PRA-004 **KHÔNG**
sửa nó. `employee_group` không phải cột `REQUIRED_NOW` của PRA-004 nên
finding đó không chạm đường production của slice này.

Ba issue `reference_integrity` của REM-T06 là **pre-existing**; PRA-004
KHÔNG repair và KHÔNG được làm tăng số issue.

---

## (20) Acceptance Oracle — FROZEN

### 20.1 Oracle A — Golden fixture `period_2026_01` (độc lập, đo lại được)

Đo trong phiên S100 bằng đường production thật rồi persist và truy vấn SQL.
Test PHẢI dựng lại bằng cùng đường đó, KHÔNG hard-code bằng cách chép số.

```text
O-A1  Tổng: 254 đơn · 351 dòng hiện hành
O-A2  Đơn TOÀN AUTO = 1 · đơn CẦN KIỂM TRA = 253
O-A3  auto_orders + review_orders = 254 = COUNT(DISTINCT order_key)
O-A4  Phân bố số dòng/đơn = {1:191, 2:41, 3:16, 4:3, 5:1, 6:1, 7:1}
      Σ(số dòng × số đơn) = 351  ⟹ không double-count
```

### 20.2 Oracle B — Đơn AUTO thuần: `BH62063`

```text
Trạng thái      : AUTO
Số dòng         : 1
Ngày bán        : 2026-01-02
Tổng số lượng   : 1
Doanh thu (net) : 7.500.000
LN kế toán      : 500.000    coverage 1 / 1 dòng
LN KPI          : 500.000    coverage 1 / 1 dòng
Giá vốn kế toán : 7.000.000
Giá vốn KPI     : 7.000.000
Lý do cần kiểm tra: KHÔNG CÓ (pending_reasons = [])
```

### 20.3 Oracle C — Đơn TRỘN: `BH62439` (oracle quan trọng nhất)

```text
Trạng thái      : CẦN KIỂM TRA        ← dù có 1 dòng AUTO
Số dòng         : 4  (1 AUTO + 3 PENDING)
Ngày bán        : 2026-01-08 (cả 4 dòng cùng ngày)
Nhân viên       : đúng 1 người
Tổng số lượng   : 5
Doanh thu (net) : 66.000.000
LN kế toán      : 500.000    coverage 1 / 4 dòng     ← coverage MỘT PHẦN
LN KPI          : 400.000    coverage 1 / 4 dòng     ← coverage MỘT PHẦN

Dòng AUTO — Điều hòa Daikin FTHF25XVMV
  SL 2 · đơn giá 10.500.000 · chiết khấu 100.000 · doanh thu dòng 20.900.000
  giá vốn kế toán 10.250.000 · giá vốn KPI 10.250.000
  LN kế toán 500.000 · LN KPI 400.000 · lý do: KHÔNG CÓ

Ba dòng PENDING — mỗi dòng ĐÚNG 5 mã lý do, theo ĐÚNG thứ tự này:
  IDENTITY_SOURCES_UNAVAILABLE
  Missing.PurchasePrice
  Pending.accounting_purchase_price
  Pending.accounting_profit
  Pending.eligible_kpi_profit
  (mọi giá vốn và mọi lợi nhuận của ba dòng này = NULL ⟹ PHẢI hiện "—")
```

### 20.4 Oracle D — Vũ trụ reason code là ĐÓNG

```text
O-D1  Tập mã hợp lệ = 10 giá trị PriceResolutionReason
                    ∪ 8 giá trị CATEGORIES của validation
                    ∪ 3 chuỗi Pending.<field>
      = tối đa 21 mã. Test PHẢI dẫn xuất tập này TỪ CHÍNH các enum/hằng số
      trong mã nguồn, KHÔNG chép tay danh sách.
O-D2  REASON_DISPLAY_LABELS phủ TOÀN PHẦN tập O-D1.
O-D3  7 nhãn có sẵn từ S069 giữ NGUYÊN TỪNG CHỮ.
O-D4  Không nhãn nào chứa từ vựng nội bộ ở mục 14.3.
```

### 20.5 Bất biến an toàn có thẩm quyền cao hơn mọi literal

Nếu một literal ở 20.1–20.3 lệch vì môi trường/config thay đổi, bất biến
DƯỚI ĐÂY vẫn thắng và vẫn phải PASS:

```text
INV-1  Σ(doanh thu các dòng của đơn) = doanh thu đơn      (mọi đơn)
INV-2  Σ(số lượng các dòng của đơn)  = tổng SL đơn        (mọi đơn)
INV-3  Σ(số dòng theo đơn)           = tổng dòng của kỳ   (không double-count)
INV-4  auto_orders + review_orders   = tổng đơn của kỳ    (phân hoạch)
INV-5  đơn có ≥1 dòng PENDING        ⟺ đơn CẦN KIỂM TRA
INV-6  giá trị NULL                  ⟹ hiển thị "—", KHÔNG BAO GIỜ 0/0đ/0%
INV-7  ô lợi nhuận không kèm coverage ⟹ FAIL
```

---

## (21) Production Acceptance — Tháng 09/2026

Owner thực hiện trên hệ thống chạy thật, **KHÔNG cần upload lại workbook** —
dữ liệu production hiện tại đã đủ (`FACT`, S093/S099).

```text
1. Mở /ban-hang, chọn kỳ "Tháng 09/2026".
2. Thấy ĐÚNG 40 đơn trong danh sách.
3. Thấy ĐÚNG 15 đơn AUTO và 25 đơn CẦN KIỂM TRA.
4. Mở ÍT NHẤT 1 đơn AUTO   → thấy các dòng tạo thành đơn, không dòng nào
                              có lý do cần kiểm tra.
5. Mở ÍT NHẤT 1 đơn CẦN KIỂM TRA → thấy các dòng, và với mỗi dòng PENDING
                              thấy lý do bằng TIẾNG VIỆT đọc được.
6. Với mỗi đơn mở ra: Σ doanh thu các dòng = doanh thu đơn hiện trên
   danh sách (INV-1); Σ số lượng khớp (INV-2).
7. Mở /tong-quan cùng kỳ "Tháng 09/2026" → 40 đơn · 61 dòng · 15 AUTO ·
   25 cần kiểm tra KHỚP với /ban-hang (reconcile).
8. Không thấy IMEI, tên khách, số điện thoại, địa chỉ, hay ghi chú thô ở
   bất kỳ đâu trên hai trang mới.
```

**KHÔNG freeze thêm bất kỳ con số tiền hay chi tiết đơn nào của 09/2026 làm
kỳ vọng đặt trước** — chưa có oracle độc lập cho chúng. Các giá trị Owner
đọc được ngoài 4 con số trên được ghi lại dưới nhãn `OBSERVED_ONLY`.

---

## (22) Findings từ phiên discovery

### FIND-PRA004-01 — `TRUTHFULNESS_CONSTRAINT` · KHÔNG BLOCKING · đã đưa vào contract

PRA-004 hiển thị các số đã lưu cạnh nhau nhưng **KHÔNG chứng minh được**
bằng dữ liệu persisted rằng lợi nhuận luôn dẫn xuất từ đúng
`(SL, đơn giá, chiết khấu, giá vốn)`: chỉ có 2 dòng `AUTO` trong toàn bộ
fixture golden và cả hai đều có `delivery_cost = NULL`, trong khi 325/351
dòng của kỳ CÓ `delivery_cost`.

Xử lý (đã khoá trong contract): trang **KHÔNG in công thức** và **KHÔNG
tuyên bố** tự dẫn xuất lại lợi nhuận. `delivery_cost` = USEFUL_BUT_DEFER.

RE-TRIGGER CONDITION: gặp một dòng `AUTO` có `delivery_cost` khác `NULL` mà
lợi nhuận của nó không khớp số học ở mục 4.5 ⟹ mở lại quyết định về
`delivery_cost`.

### FIND-PRA004-02 — `DOC_INCONSISTENCY` · KHÔNG BLOCKING · đã giải quyết bằng thiết kế

Xung đột phân loại `product_raw` giữa docstring `analytics_queries.py` và
`tests/fixtures/golden/anonymize.py`. Chi tiết và cách giải ở mục 14.4.
**KHÔNG sửa** `analytics_queries.py`, **KHÔNG nới** test PII của PRA-003.

### FIND-PRA004-03 — `HARDENING` · KHÔNG BLOCKING · DEFER

"0 đơn nhiều nhân viên" trên fixture golden là hệ quả của ẩn danh hoá, không
phải bằng chứng về production (mục 4.6). Contract vẫn thiết kế cho n ≥ 1
(mục 9), nên đây không phải lỗ hổng — chỉ là một nhánh CHƯA có dữ liệu thật
để kiểm.

RE-TRIGGER CONDITION: khi dữ liệu production lần đầu có một đơn mà các dòng
mang từ hai `employee_normalized` trở lên, kiểm lại cách trình bày của mục 9
trên chính đơn đó.

**BLOCKING_FINDINGS = 0.**

---

## (23) Change Budget — RIÊNG CỦA PRA-004

**KHÔNG kế thừa** ngân sách còn dư của bất kỳ lineage nào khác.

```
Python production mới/sửa
  app/web/sales_queries                   ≈ 110   (mục tiêu)
  app/web/sales_presentation              ≈  95
  app/web/server.py (delta, 2 route)      ≈  45
  app/beta_presentation.py (delta, nhãn)  ≈  16
  ------------------------------------------------
  MỤC TIÊU                                ≈ 266 dòng
  CẢNH BÁO MỀM                              330 dòng → dừng, lập BUDGET-AWARE PLAN
  DỪNG CỨNG                                 400 dòng → STOP = CHANGE_BUDGET_EXCEEDED

Template mới/sửa                          ≤ 220 dòng
  ban_hang.html                ≈  85
  ban_hang_chi_tiet.html       ≈  95
  _pipeline_bits.html (delta)  ≈  15
  layout.html (delta)          =   1

CSS thêm                                  ≤  25 dòng
Test mới                                  ≥  30 test (0 skip mới)
Dependency mới                            =   0
Schema / migration / index                =   0
Config mới                                =   0
```

Quy ước đo giống PRA-002 mục 17 / PRA-003 mục 13: Python production tách
riêng khỏi template/CSS/test; đếm dòng MÃ (không tính dòng trống, không tính
docstring/comment thuần).

Mục tiêu 266 cao hơn PRA-003 (255) đúng ở phần chi tiết dòng + ánh xạ lý do —
hai thứ PRA-003 không có. `sales_presentation` KHÔNG nhân bản
`analytics_presentation`: nó **import và tái dụng** `money`, `count`,
`coverage`, `profit`, `period_label`, `period_options`, `period_value`,
`UNKNOWN_EMPLOYEE`, `ORIGIN_*`. Nếu phiên implement thấy mình đang chép lại
các hàm đó ⟹ đó là dấu hiệu sai hướng, dừng và tái dụng.

Hardening (quy tắc 90/10): ≤ 10% ngân sách và CHỈ sau khi mọi REQUIRED đã
PASS. Ứng viên DUY NHẤT được phép: đo thời gian tải danh sách đơn trên tập
≥12k dòng (CHECK-PRA004-13). Không ứng viên nào khác.

Vượt DỪNG CỨNG:

```
STOP = CHANGE_BUDGET_EXCEEDED
```

kèm giải thích REAL VERTICAL cụ thể nào không dựng được trong ngân sách.
**Không âm thầm mở rộng.**

---

## (24) Review Budget

```
root_task              : TASK-PRA-004
effective_risk         : MEDIUM
repair_cycles_allowed  : 1
repair_cycles_used     : 0
repair_cycles_remaining: 1
Independent Review     : BẮT BUỘC (E2, CHECK-PRA004-12)
```

MEDIUM chấm theo failure path (`governance/core/V4_1_POLICY_FREEZE.md` §4) —
lý do đầy đủ ở Metadata → Blast Radius.

**Finding KHÔNG tự động trở thành repair work.** Chỉ mở repair cycle khi
finding đe doạ TRỰC TIẾP một trong năm điều:

1. tính trung thực của kết quả quản lý ở cấp ĐƠN hoặc DÒNG;
2. bất biến no-double-count (INV-1 … INV-4);
3. sự tách bạch `LEGACY_REFERENCE` ↔ `PIPELINE_GENERATED`;
4. an toàn `NULL` / coverage (INV-6, INV-7) hoặc ranh giới PII (mục 14);
5. nghiệm thu real vertical Tháng 09/2026.

Finding ngoài năm nhóm đó: `HARDENING` kèm RE-TRIGGER CONDITION cụ thể
(V4.1 §7) hoặc `OUT_OF_SCOPE`. Vượt 1 cycle ⟹ `OWNER_EXTENSION REQUIRED`;
KHÔNG tách sub-unit, KHÔNG đổi tên task, KHÔNG mở nhánh mới để reset ngân
sách (V4.1 §2).

---

## Phụ Thuộc (Dependencies)

- `TASK-PRA-002` — DONE. Cung cấp ba bảng và bất biến no-double-count.
- `TASK-PRA-003` — DONE. Cung cấp model kỳ, quy tắc `NULL`/coverage, ngữ
  nghĩa trạng thái đơn, macro UI, và bốn con số nghiệm thu 09/2026.
- `TASK-PRA-001` — DONE. Tách nguồn SỐ CŨ / SỐ MỚI.

Không phụ thuộc nào chưa xong. **IMPLEMENTATION_READY = YES.**

## Chặn (Blocks)

- `PRA-005` Product Analytics (chưa mở).

## An Toàn Để Chạy Song Song Với (Parallel-Safe With)

Không task nào khác đang IN_PROGRESS trên lineage PRA. PRA-004 chỉ ĐỌC ba
bảng pipeline nên an toàn song song với mọi công việc không sửa
`tools/db/schema.py` hay `app/history/**`.

---

## Ready Gate

Dùng `governance/core/TASK_READY_GATE_STANDARD.md`.

| Điều kiện | Trạng thái | Bằng chứng |
|---|---|---|
| Canonical HEAD khớp EXACT SHA kỳ vọng | PASS | `git rev-parse origin/claude/extract-upload-repo-gq2ws4` = `8181cebe0619a9c8d12604168a90914c04b3692f` |
| Nhánh PRA-004 tạo từ đúng canonical đó | PASS | `claude/pra-004-sales-review-detail-0b2z4w` @ `8181cebe` |
| Mọi phụ thuộc DONE | PASS | PRA-001/002/003 = DONE |
| Business authority đủ cho mọi ô REQUIRED_NOW | PASS | Mục 2 + mục 12 |
| Không có OWNER_DECISION nào còn treo | PASS | Mục 2 — ba mục `NEEDS_AUTHORITY` đều nằm NGOÀI scope (mục 9, 12, 19) |
| Scope Lock đã định nghĩa | PASS | Mục 18 |
| Completion Gate đã freeze | PASS | Mục dưới |
| Change Budget + Review Budget đã đặt | PASS | Mục 23, 24 |
| Acceptance Oracle độc lập, đo lại được | PASS | Mục 20 |
| Schema / migration / dependency = 0 | PASS | Mục 17 |

**READY = YES.**

---

## Completion Gate — FROZEN

Dùng `governance/core/TASK_COMPLETION_GATE_STANDARD.md` và
`governance/core/EVIDENCE_STANDARD.md`.

**FROZEN tại S100 (2026-09-03)**,
`BASE_SHA = 8181cebe0619a9c8d12604168a90914c04b3692f`.

13 check: **11 REQUIRED** · 2 RECOMMENDED. Risk 3 ⟹ mọi REQUIRED thực thi
được PHẢI đạt E1; CHECK-PRA004-12 phải đạt E2.

Không xoá, không làm yếu bất kỳ REQUIRED check nào để task pass. Thay đổi
gate phải đi qua `COMPLETION GATE CHANGE PROPOSAL`.

### Data / Truthfulness

#### CHECK-PRA004-01 — Tầng truy vấn CHỈ-ĐỌC và chỉ đọc trạng thái hiện hành
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Yêu cầu: bằng chứng CẤU TRÚC bằng AST trên `app/web/sales_queries` (file DỰ KIẾN) (không phải grep chuỗi), theo đúng khuôn `tests/test_analytics_queries.py::test_the_query_module_never_writes_and_never_reads_a_run_summary`: (a) không import `insert`/`update`/`delete`/`text`; (b) không gọi `begin()`/`commit()`/`execution_options()`; (c) không định danh nào là `summary_json` hoặc `source_snapshot`; (d) mọi truy vấn xuất phát từ `order_line_current` và join qua `current_source_version_id`/`current_result_version_id`. Kèm test dòng `SOURCE_CHANGED`: chỉ version hiện hành xuất hiện trong chi tiết đơn, version cũ KHÔNG. Output test nguyên văn.

Executed By:
Session S101 — PRA-004 MAJOR Implementation (Claude Code)

Timestamp:
2026-09-03

Kết quả S101:
PASS (S101, 2026-09-03). Bằng chứng CẤU TRÚC bằng AST trên `app/web/sales_queries.py`:
`tests/test_sales_queries.py::test_the_sales_query_module_has_no_path_that_writes`
(không import `insert`/`update`/`delete`/`text`; không gọi `begin`/`commit`/
`execution_options`; có `connect`),
`::test_the_sales_query_module_never_aggregates_run_history`
(`summary_json` và `source_snapshot` không xuất hiện như định danh),
`::test_every_sales_query_starts_from_the_current_pointers`
(`order_line_current` + `current_source_version_id` + `current_result_version_id`).
Dòng `SOURCE_CHANGED`:
`::test_only_the_current_version_of_a_changed_line_reaches_the_detail` — sau hai lần
chạy, chi tiết đơn hiện ĐÚNG 1 dòng với `sell_price = 9.000.000` (version mới), version
cũ KHÔNG lọt vào. Output: `89 passed in 6.55s`
(`python -m pytest tests/test_sales_queries.py tests/test_sales_presentation.py tests/test_web_sales_detail.py -q`).

#### CHECK-PRA004-02 — Oracle golden: danh sách đơn khớp và KHÔNG double-count
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Yêu cầu: persist fixture `tests/fixtures/golden/period_2026_01.xlsx` qua ĐƯỜNG PRODUCTION (`run_import_production` → `present_lines` → `extraction.build_source_lines`/`build_result_lines` → `history_writer.write_run_history`), rồi khẳng định O-A1 … O-A4 của mục 20.1: 254 đơn · 351 dòng · 1 đơn AUTO · 253 đơn cần kiểm tra · phân bố số dòng/đơn · Σ(số dòng × số đơn) = 351. Thêm INV-3 và INV-4 dạng khẳng định. KHÔNG sửa một byte nào trong `tests/fixtures/golden/**`. Output test nguyên văn.

Executed By:
Session S101 — PRA-004 MAJOR Implementation (Claude Code)

Timestamp:
2026-09-03

Kết quả S101:
PASS (S101, 2026-09-03). Fixture `tests/fixtures/golden/period_2026_01.xlsx` được persist qua
ĐƯỜNG PRODUCTION trong `tests/test_sales_queries.py::load_golden`
(`build_price_composition` → `run_import_production` → `export_report` → `present_lines`
→ `history_writer.write_run_history` → `extraction.build_source_lines`/`build_result_lines`).
KHÔNG một byte nào trong `tests/fixtures/golden/**` bị sửa
(`git diff --stat 8181cebe -- tests/fixtures/golden/` = rỗng).

O-A1 `::test_the_golden_period_lists_the_orders_the_production_path_produced` — 254 đơn,
351 dòng. O-A2 `::test_the_golden_period_has_exactly_one_all_auto_order` — đơn AUTO thuần
= `["BH62063"]`, đơn cần kiểm tra = 253. O-A3 (INV-4) — phân hoạch AUTO + Review = tổng
đơn, khẳng định trong cùng test và trong
`tests/test_web_sales_detail.py::test_the_sales_layer_reconciles_with_the_overview_on_the_same_period`.
O-A4 + INV-3 `::test_the_line_count_distribution_adds_back_up_to_every_line` — phân bố
`{1: 191, 2: 41, 3: 16, 4: 3, 5: 1, 6: 1, 7: 1}` và `Σ(số dòng × số đơn) = 351`.
No-double-count thêm: `::test_reuploading_the_same_book_moves_no_order_total` (nạp lại
cùng sổ ⟹ danh sách đơn KHÔNG đổi một ô nào) và
`::test_a_multi_line_order_aggregates_its_lines_exactly_once` (INV-1/INV-2).

#### CHECK-PRA004-03 — Oracle đơn AUTO thuần (BH62063) và đơn TRỘN (BH62439)
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Yêu cầu: trên cùng dữ liệu đã persist của CHECK-02, khẳng định TRỌN VẸN Oracle B (mục 20.2) và Oracle C (mục 20.3) — bao gồm: BH62439 có trạng thái CẦN KIỂM TRA dù chứa 1 dòng AUTO; 4 dòng đúng thứ tự `occurrence_index`; doanh thu net 66.000.000; LN kế toán 500.000 coverage 1/4; LN KPI 400.000 coverage 1/4; ba dòng PENDING mỗi dòng ĐÚNG 5 mã lý do theo đúng thứ tự; mọi giá vốn/lợi nhuận của ba dòng đó là NULL. Kèm INV-1 và INV-2 cho cả hai đơn. Output test nguyên văn.

Executed By:
Session S101 — PRA-004 MAJOR Implementation (Claude Code)

Timestamp:
2026-09-03

Kết quả S101:
PASS (S101, 2026-09-03). Trên CÙNG dữ liệu đã persist của CHECK-PRA004-02.

Oracle B — `::test_the_pure_auto_order_bh62063_reads_exactly_as_the_oracle`: AUTO, 1 dòng,
`2026-01-02`, SL 1, doanh thu 7.500.000, LN kế toán 500.000 coverage 1/1, LN KPI 500.000
coverage 1/1, giá vốn kế toán = giá vốn KPI = 7.000.000, `reasons == []`.

Oracle C — `::test_the_mixed_order_bh62439_is_review_even_though_one_line_is_auto`
(CẦN KIỂM TRA dù có 1 dòng AUTO; 4 dòng = 1 AUTO + 3 PENDING; cùng ngày `2026-01-08`;
SL 5; doanh thu 66.000.000; đúng 1 nhân viên),
`::test_the_mixed_order_reports_partial_coverage_on_both_profits` (LN kế toán 500.000
coverage 1/4, LN KPI 400.000 coverage 1/4),
`::test_the_detail_lines_follow_the_order_they_had_in_the_book` (4 dòng đúng thứ tự sổ),
`::test_the_auto_line_of_bh62439_carries_both_purchase_prices` (SL 2 · đơn giá 10.500.000
· chiết khấu 100.000 · doanh thu dòng 20.900.000 · hai giá vốn 10.250.000 · LN kế toán
500.000 · LN KPI 400.000),
`::test_the_three_pending_lines_of_bh62439_carry_no_value_at_all` (mọi giá vốn và mọi lợi
nhuận của ba dòng = `NULL`),
`::test_the_persisted_reason_codes_of_bh62439_are_read_back_in_order` (mỗi dòng ĐÚNG 5 mã
theo ĐÚNG thứ tự đã persist).
INV-1/INV-2 trên chính HTML:
`tests/test_web_sales_detail.py::test_the_detail_totals_add_back_up_from_its_own_lines`.

#### CHECK-PRA004-04 — Vũ trụ reason code ĐÓNG và bảng nhãn TOÀN PHẦN
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Yêu cầu: test DẪN XUẤT tập mã hợp lệ TỪ CHÍNH mã nguồn — `PriceResolutionReason` (enum), `validation.models.CATEGORIES` (hằng số), và ba chuỗi `Pending.<field>` đọc từ chính vòng lặp sinh chúng trong `excel_exporter._present_lines` — KHÔNG chép tay danh sách. Sau đó khẳng định O-D1 … O-D4 của mục 20.4: `REASON_DISPLAY_LABELS` phủ TOÀN PHẦN tập đó; 7 nhãn S069 giữ nguyên TỪNG CHỮ; không nhãn nào chứa từ vựng nội bộ của mục 14.3. Output test nguyên văn.

Executed By:
Session S101 — PRA-004 MAJOR Implementation (Claude Code)

Timestamp:
2026-09-03

Kết quả S101:
PASS (S101, 2026-09-03). Tập mã hợp lệ được DẪN XUẤT từ mã nguồn trong
`tests/test_sales_presentation.py::reason_universe` — `PriceResolutionReason` (enum),
`app.modules.validation.models.CATEGORIES` (hằng số), và ba chuỗi `Pending.<field>` đọc
bằng AST TỪ CHÍNH vòng lặp sinh chúng trong `excel_exporter._present_lines`
(`::pending_fields_from_source`). Không danh sách nào chép tay.

O-D1 `::test_the_reason_universe_derived_from_source_is_closed_at_21_codes` — 10 + 8 + 3
= 21 mã. O-D2 `::test_the_label_table_covers_the_whole_closed_universe` — phủ TOÀN PHẦN
(hiệu tập = rỗng). Thêm `::test_the_label_table_invents_no_code_of_its_own` — bảng nhãn
KHÔNG rộng hơn vũ trụ đóng, tức không có taxonomy mới nào lén hình thành.
O-D3 `::test_the_seven_s069_labels_are_unchanged_word_for_word`.
O-D4 `::test_no_label_leaks_internal_vocabulary`.
Hành vi khi thiếu nhãn: `::test_an_unlabelled_code_is_shown_verbatim_not_swallowed`.

#### CHECK-PRA004-05 — Trạng thái đơn derive đúng, KHÔNG có trạng thái mới
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Yêu cầu: (a) INV-5 dạng khẳng định trên mọi đơn của fixture golden — đơn có ≥1 dòng PENDING ⟺ CẦN KIỂM TRA; (b) test hồi quy riêng cho ca TRỘN BH62439 chứng minh một triển khai "lấy trạng thái dòng đầu tiên" sẽ ĐỎ; (c) grep chứng minh không chuỗi trạng thái nào ngoài hai nhãn tiếng Việt của AUTO / CẦN KIỂM TRA xuất hiện trong `sales_presentation` và hai template mới (không `PARTIAL`/`WARNING`/`RESOLVED`/`APPROVED`); (d) `auto_orders + review_orders = COUNT(DISTINCT order_key)` trên cùng kỳ. Output test nguyên văn.

Executed By:
Session S101 — PRA-004 MAJOR Implementation (Claude Code)

Timestamp:
2026-09-03

Kết quả S101:
PASS (S101, 2026-09-03).
(a) INV-5 — `tests/test_sales_queries.py::test_the_golden_period_has_exactly_one_all_auto_order`
trên toàn bộ 254 đơn của fixture golden.
(b) `::test_an_order_whose_first_line_is_auto_is_still_review` — đơn tổng hợp có dòng ĐẦU
TIÊN `AUTO` và dòng sau `PENDING` vẫn phải là CẦN KIỂM TRA; một triển khai "lấy trạng
thái dòng đầu tiên" ĐỎ ở đây (nhánh mà oracle golden không canh được, vì dòng đầu của
BH62439 tình cờ là PENDING). Phía golden:
`::test_the_mixed_order_bh62439_is_review_even_though_one_line_is_auto`.
(c) `tests/test_sales_presentation.py::test_the_presentation_module_names_no_third_status`
và `::test_neither_new_template_names_a_third_status` — không `PARTIAL`/`WARNING`/
`RESOLVED`/`APPROVED`/`REJECTED` trong `sales_presentation` (xét chuỗi in ra + định danh,
bỏ docstring) và trong hai template mới (bỏ chú thích Jinja). Hai nhãn duy nhất:
`AUTO` / `CẦN KIỂM TRA` (`::test_there_are_exactly_two_status_labels`).
(d) `auto_orders + review_orders = COUNT(DISTINCT order_key)` —
`tests/test_web_sales_detail.py::test_the_sales_layer_reconciles_with_the_overview_on_the_same_period`,
chạy trên cả "Toàn bộ dữ liệu" và Tháng 01/2026.

#### CHECK-PRA004-06 — `NULL` ≠ `0` và coverage bắt buộc ở cấp đơn LẪN dòng
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Yêu cầu: (a) INV-6 — với ba dòng PENDING của BH62439 (mọi giá vốn/lợi nhuận NULL), HTML render ra `—` và KHÔNG chứa `0đ`/`0%`/`0` ở các ô đó; (b) INV-7 — mọi ô lợi nhuận cấp đơn trên `/ban-hang` VÀ trên trang chi tiết đều mang chuỗi coverage dạng `N / M dòng`, khẳng định bằng cách duyệt DOM/`data-metric`, không phải bằng mắt; (c) đơn có coverage < số dòng hiện câu cảnh báo tường minh (kiểm trên BH62439 với coverage 1/4). Output test nguyên văn.

Executed By:
Session S101 — PRA-004 MAJOR Implementation (Claude Code)

Timestamp:
2026-09-03

Kết quả S101:
PASS (S101, 2026-09-03). Khẳng định trên HTML THẬT, duyệt theo `data-metric`.
(a) INV-6 — `tests/test_web_sales_detail.py::test_the_pending_lines_show_a_dash_and_never_a_zero`:
với cả ba dòng PENDING của BH62439, bốn ô tiền (`accounting_purchase_price`,
`kpi_purchase_price`, `accounting_profit`, `kpi_profit`) render `—`, và không ô nào chứa
`0` hay `%`.
(b) INV-7 — `::test_every_profit_cell_on_the_list_carries_its_coverage`: duyệt CẢ 254 dòng
đơn của `/ban-hang`, mỗi ô lợi nhuận có chuỗi coverage khớp `\d+ / \d+ dòng`;
`::test_the_detail_page_of_the_mixed_order_reads_as_the_oracle` khẳng định cùng điều trên
trang chi tiết. Ở tầng trình bày:
`tests/test_sales_presentation.py::test_every_order_profit_cell_carries_its_own_coverage`.
(c) `::test_the_mixed_order_shows_partial_coverage_on_the_list` (coverage 1/4 hiện cạnh
cả hai con số) và `::test_the_detail_page_warns_that_the_profit_is_only_part_of_the_order`
(BH62439 hiện câu cảnh báo tường minh); phía đối xứng
`::test_the_pure_auto_order_raises_no_partial_coverage_warning`.
Phân biệt `0` thật với "chưa biết":
`tests/test_sales_presentation.py::test_a_real_zero_profit_still_renders_as_zero` và
`tests/test_sales_queries.py::test_a_real_zero_profit_stays_a_real_zero`.

#### CHECK-PRA004-07 — Reconcile với Tổng quan trên cùng kỳ
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Yêu cầu: trên cùng dữ liệu và cùng tham số `ky`, so trực tiếp kết quả tầng truy vấn của `/ban-hang` với `analytics_queries.period_totals()`: tổng đơn, tổng dòng, tổng số lượng, doanh thu net, LN KPI + coverage, LN kế toán + coverage, số đơn AUTO, số đơn cần kiểm tra — TẤT CẢ phải bằng nhau. Kiểm trên cả "Toàn bộ dữ liệu" và một tháng cụ thể. Output test nguyên văn.

Executed By:
Session S101 — PRA-004 MAJOR Implementation (Claude Code)

Timestamp:
2026-09-03

Kết quả S101:
PASS (S101, 2026-09-03).
`tests/test_web_sales_detail.py::test_the_sales_layer_reconciles_with_the_overview_on_the_same_period`
so TRỰC TIẾP `sales_queries.order_list()` với `analytics_queries.period_totals()` trên
cùng dữ liệu và cùng tham số kỳ, cho CẢ HAI kỳ (`{}` = Toàn bộ dữ liệu, và Tháng
01/2026): tổng đơn, tổng dòng, tổng số lượng, doanh thu net, LN KPI + `kpi_lines`, LN kế
toán + `accounting_lines`, số đơn AUTO, số đơn cần kiểm tra — TẤT CẢ bằng nhau.
Reconcile ở tầng HTML: `::test_the_two_pages_agree_on_how_many_orders_the_period_has`
(ô `orders` của `/ban-hang` và `/tong-quan` cùng kỳ).

### Bảo Toàn / Không Hồi Quy

#### CHECK-PRA004-08 — PRA-003, PRA-001 và Golden Baseline KHÔNG hồi quy
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Yêu cầu: chạy lại và dán nguyên văn output của `tests/test_analytics_queries.py`, `tests/test_analytics_presentation.py`, `tests/test_web_pipeline_analytics.py` (PRA-003 — phải PASS NGUYÊN VẸN, không sửa một dòng test nào), bộ test legacy routes (PRA-001), Golden Baseline (`58 passed, 2 skipped`), và FULL SUITE (không giảm số test PASS so với baseline canonical `8181cebe`). Đặc biệt phải chứng minh `test_the_query_module_never_selects_a_personal_data_column` vẫn PASS mà KHÔNG bị sửa.

Executed By:
Session S101 — PRA-004 MAJOR Implementation (Claude Code)

Timestamp:
2026-09-03

Kết quả S101:
PASS (S101, 2026-09-03).

PRA-003 — `python -m pytest tests/test_analytics_queries.py tests/test_analytics_presentation.py tests/test_web_pipeline_analytics.py -q`
→ `67 passed in 7.07s`. Ba file test này KHÔNG bị sửa một dòng nào:
`git diff --stat 8181cebe -- tests/test_analytics_queries.py tests/test_analytics_presentation.py tests/test_web_pipeline_analytics.py`
= rỗng. Riêng gate PII:
`python -m pytest "tests/test_analytics_queries.py::test_the_query_module_never_selects_a_personal_data_column" -q`
→ `1 passed in 0.18s`, trên file test NGUYÊN VẸN.

Golden Baseline — `python -m pytest tests/test_golden_baseline.py -q` →
`58 passed, 2 skipped in 6.45s` (khớp ĐÚNG baseline đã freeze).

FULL SUITE — `python -m pytest -q` → `1962 passed, 11 skipped in 78.83s`.
Baseline canonical đo lại trong chính phiên này bằng `git worktree` tại `8181cebe`:
`1873 passed, 11 skipped in 77.08s`. Chênh lệch `+89` ĐÚNG BẰNG số test mới của PRA-004
(`89 passed`), số skip KHÔNG đổi (11), số test PASS KHÔNG giảm.

Ghi chú môi trường (KHÔNG phải finding của PRA-004): lần chạy full suite đầu tiên có
`tests/test_105d_boundaries.py::TestG25GoldenBaselineUnchanged::test_protected_golden_artifacts_match_the_task_105e_review_base`
FAIL với `fatal: bad object 740f396acb11cf279f303f09ea22dffd0ca95462` — hệ quả của
shallow clone, không phải của thay đổi nào trong phiên. Sau `git fetch --unshallow`
(`git rev-parse --is-shallow-repository` → `false`) test này PASS và toàn bộ suite xanh.

### Bảo Mật / Riêng Tư

#### CHECK-PRA004-09 — Hai trang mới KHÔNG BAO GIỜ render PII
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E2

Evidence:
Yêu cầu: (a) khẳng định trên HTML thật của cả `/ban-hang` và `/ban-hang/<order_key>` (dùng đơn TRỘN BH62439 và đơn AUTO BH62063) rằng KHÔNG xuất hiện: `imei`, `note_raw`, `employee_raw`, `customer`, `phone`, `address`, và các giá trị PII mẫu; (b) hàng rào CẤU TRÚC riêng của PRA-004 trên `app/web/sales_queries` (file DỰ KIẾN) — module KHÔNG tham chiếu `.c.imei`, `.c.note_raw`, `.c.employee_raw`, `.c.customer`, `.c.phone`, `.c.address` (`product_raw` CỐ Ý không nằm trong hàng rào này, lý do ở mục 14.4); (c) khẳng định cấu trúc rằng `customer`/`phone`/`address`/`shipper_raw` KHÔNG tồn tại như cột trong `tools/db/schema.py`. E2 vì đây là ranh giới bảo mật/dữ liệu cá nhân.

Executed By:
Session S101 — PRA-004 MAJOR Implementation (Claude Code)

Timestamp:
2026-09-03

Kết quả S101:
PASS (S101, 2026-09-03) — E2 (ranh giới bảo mật/dữ liệu cá nhân), ba lớp bằng chứng ĐỘC LẬP.

(a) HTML THẬT — `tests/test_web_sales_detail.py::test_no_new_page_ever_renders_a_personal_data_field`
chạy trên CẢ BA trang (`/ban-hang?ky=tat-ca`, `/ban-hang/BH62439?ky=tat-ca` = đơn TRỘN,
`/ban-hang/BH62063?ky=tat-ca` = đơn AUTO) và khẳng định KHÔNG xuất hiện `imei`,
`note_raw`, `employee_raw`, `source_profit`, `customer`, `phone`, `address`, `shipper`.

(b) Hàng rào CẤU TRÚC riêng của PRA-004 —
`tests/test_sales_queries.py::test_the_sales_query_module_never_selects_a_personal_data_column`:
`app/web/sales_queries.py` không tham chiếu `.c.imei`, `.c.note_raw`, `.c.employee_raw`,
`.c.customer`, `.c.phone`, `.c.address`. Phía đối xứng
`::test_the_sales_query_module_does_read_product_raw` canh CHIỀU NGƯỢC LẠI: nếu ai đó
"dọn dẹp" cho khớp hàng rào PRA-003 thì trang chi tiết mất khả năng phân biệt các dòng
và test đỏ TRƯỚC. `product_raw` = REQUIRED_NOW, lý do ở mục 14.4.
Ở tầng trình bày:
`tests/test_sales_presentation.py::test_the_presentation_object_of_a_line_carries_no_prohibited_field`
— object đi TỚI Jinja không chứa trường cấm nào, tức ranh giới không chỉ nằm ở template.

(c) Bảo đảm cấu trúc mạnh hơn quy ước —
`tests/test_web_sales_detail.py::test_the_customer_columns_do_not_even_exist_in_the_schema`:
`customer`/`phone`/`address`/`shipper` KHÔNG tồn tại như cột trong `tools/db/schema.py`,
nên chúng không thể rò rỉ qua bất kỳ truy vấn nào.

Gate PII của PRA-003 tiếp tục PASS NGUYÊN VẸN, không bị sửa — xem CHECK-PRA004-08.

#### CHECK-PRA004-10 — Hai trang mới KHÔNG rò rỉ từ vựng nội bộ
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Yêu cầu: khẳng định trên HTML thật của cả hai trang rằng KHÔNG xuất hiện bất kỳ chuỗi nào trong danh sách mục 14.3 (`snapshot_id`, `run_id`, `coverage_state`, `source_version`, `result_version`, `reconciliation_flag`, `PIPELINE_GENERATED`, `LEGACY_REFERENCE`, `price_source`, `kpi_purchase_provenance`, `composition_rule`, `identity_namespace`, `result_fingerprint`, `row_hash`, `line_fingerprint`, `product_key`, `occurrence_index`) và không chứa đường dẫn tuyệt đối của repo. Thêm: `/ban-hang/<order_key>` với mã đơn không tồn tại trả HTTP 404 (không phải trang rỗng); khi không có kho dữ liệu trả HTTP 503 (không phải "chưa có dữ liệu"). Output test nguyên văn.

Executed By:
Session S101 — PRA-004 MAJOR Implementation (Claude Code)

Timestamp:
2026-09-03

Kết quả S101:
PASS (S101, 2026-09-03).
`tests/test_web_sales_detail.py::test_no_new_page_leaks_internal_vocabulary` khẳng định
trên HTML thật của cả hai trang rằng KHÔNG xuất hiện bất kỳ chuỗi nào trong danh sách mục
14.3 (`snapshot_id`, `run_id`, `coverage_state`, `source_version`, `result_version`,
`reconciliation_flag`, `PIPELINE_GENERATED`, `LEGACY_REFERENCE`, `price_source`,
`kpi_purchase_provenance`, `composition_rule`, `identity_namespace`,
`result_fingerprint`, `row_hash`, `line_fingerprint`, `product_key`,
`occurrence_index`), và không chứa đường dẫn tuyệt đối của repo. Nhãn cột cũng sạch:
`tests/test_sales_presentation.py::test_the_line_columns_expose_no_internal_field`.

Biên route: `::test_an_unknown_order_key_is_a_404_not_an_empty_page` (HTTP 404, KHÔNG
phải trang rỗng), `::test_without_a_data_store_the_pages_answer_503_not_no_data_yet`
(HTTP 503 cho CẢ HAI route khi `snapshot_repo is None`),
`::test_an_invalid_period_falls_back_to_all_data_instead_of_failing` (`ky` sai ⟹ rơi về
"Toàn bộ dữ liệu", không HTTP 500), `::test_an_empty_period_says_so_instead_of_showing_a_blank_table`.

### Phạm Vi / Ngân Sách

#### CHECK-PRA004-11 — Scope Lock và Change Budget được tôn trọng
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Yêu cầu: `git diff --stat` so với `BASE_SHA = 8181cebe` chứng minh KHÔNG file nào trong danh sách CẤM của mục 18 bị chạm; đếm dòng Python production / template / CSS theo quy ước mục 23 và đối chiếu với DỪNG CỨNG; khẳng định `SCHEMA_CHANGE = 0`, `MIGRATION = 0`, `INDEX = 0`, `DEPENDENCY = 0`, `CONFIG = 0`, `TRACKING_CHANGED = NO`, `INFRASTRUCTURE_CHANGED = NO`, `PROTECTED_CORE_IMPACT = NONE`. Kèm `git diff --check` sạch trên DẢI COMMIT (không chỉ working tree — xem FIND-PRA003-02).

Executed By:
Session S101 — PRA-004 MAJOR Implementation (Claude Code)

Timestamp:
2026-09-03

Kết quả S101:
PASS (S101, 2026-09-03).

Scope Lock — `git diff --name-only 8181cebe` + `git status --porcelain` cho ĐÚNG 12 file,
tất cả nằm trong danh sách ĐƯỢC PHÉP của mục 18:
`app/web/sales_queries.py`, `app/web/sales_presentation.py` (mới),
`app/web/templates/ban_hang.html`, `app/web/templates/ban_hang_chi_tiet.html` (mới),
`tests/test_sales_queries.py`, `tests/test_sales_presentation.py`,
`tests/test_web_sales_detail.py` (mới), `app/web/server.py` (chỉ 2 route + globals Jinja),
`app/beta_presentation.py` (chỉ THÊM key), `app/web/templates/layout.html` (1 dòng tab),
`app/web/templates/_pipeline_bits.html` (chỉ THÊM macro `reason_row`),
`app/web/static/css/tinphat-ui.css` (chỉ THÊM). Lọc danh sách CẤM của mục 18 trên
`git diff --name-only 8181cebe` → 0 kết quả.

Change Budget đo theo quy ước mục 23 (dòng MÃ, bỏ dòng trống và docstring/comment thuần):
```
app/web/sales_queries.py        +141
app/web/sales_presentation.py    +93
app/web/server.py                +34
app/beta_presentation.py         +14
------------------------------------
PYTHON PRODUCTION               +282   (MỤC TIÊU 266 · CẢNH BÁO MỀM 330 · DỪNG CỨNG 400)
TEMPLATE                        +126   (trần 220)
CSS                              +10   (trần 25)
TEST                          89 test  (sàn 30 · 0 skip mới)
```
`SCHEMA_CHANGE = 0` · `MIGRATION = 0` · `INDEX = 0` · `DEPENDENCY = 0` · `CONFIG = 0` ·
`TRACKING_CHANGED = NO` · `INFRASTRUCTURE_CHANGED = NO` · `PROTECTED_CORE_IMPACT = NONE`.

`git diff --check` sạch trên DẢI COMMIT (không chỉ working tree — bài học FIND-PRA003-02):
`git diff --check 8181cebe..HEAD` → không output.

#### CHECK-PRA004-12 — Independent Review E2
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E2

Evidence:
Yêu cầu: đo thời gian dựng danh sách đơn cho kỳ "Toàn bộ dữ liệu" trên tập ≥12.000 dòng hiện hành và ghi số đo thật. Đây là ứng viên hardening DUY NHẤT được phép. RE-TRIGGER CONDITION tường minh: nếu số đo > 3 giây, pagination trở thành REQUIRED và phải mở như một quyết định riêng — KHÔNG tự thêm pagination trong phiên implement chỉ vì "để chắc".

Executed By:
Session S101 — PRA-004 MAJOR Implementation (Claude Code)

Timestamp:
2026-09-03

Kết quả S101:
Yêu cầu: reviewer ĐỘC LẬP theo `governance/templates/E2_INDEPENDENT_REVIEW_TEMPLATE.md`. Phải: (a) verify `BASE_SHA`, `REVIEW_TARGET_SHA`, `FROZEN_CONTRACT_SHA` khớp kỳ vọng; (b) khẳng định frozen contract KHÔNG bị nới lỏng — không một dòng `Yêu cầu:`, không một oracle O-A…O-D, không một bất biến INV-1…INV-7 nào bị sửa chữ; (c) RECOMPUTE ĐỘC LẬP bằng SQL thô (không qua `sales_queries`) cho danh sách đơn và cho chi tiết BH62439, RỒI mới đem so; (d) chạy lại toàn bộ suite + validators; (e) đo lại change budget. Artifact: `docs/reviews/TASK-PRA-004-INDEPENDENT-REVIEW-RECORD` (file DỰ KIẾN).

Kết quả S102 — Independent Review E2 (2026-09-03):
PASS. Reviewer ĐỘC LẬP, artifact
`docs/reviews/TASK-PRA-004-INDEPENDENT-REVIEW-RECORD.md`.
(a) Ba SHA khớp kỳ vọng: `BASE_SHA = 8181cebe…`, `CONTRACT_SHA = 46a5cdb0…`,
`REVIEW_TARGET = 6a23c328…`; ancestry tuyến tính; `REVIEW_TARGET_MOVED = KHÔNG`.
(b) Frozen contract KHÔNG bị nới lỏng: `diff` 14 dòng `Yêu cầu:` giữa `46a5cdb`
và `6a23c32` = IDENTICAL; `Priority` = 13 REQUIRED · 1 RECOMMENDED ở CẢ HAI
bản; không một oracle O-A…O-D, không một bất biến INV-1…INV-7 nào bị sửa chữ.
(c) RECOMPUTE ĐỘC LẬP bằng SQL THÔ (`sqlalchemy.text()`, KHÔNG qua
`sales_queries`): danh sách đơn golden — 254 đơn / 351 dòng / 1 AUTO / 253
cần kiểm tra / phân bố `{1:191,2:41,3:16,4:3,5:1,6:1,7:1}` / Σ = 351; so với
`sales_queries.order_list` = **0 lệch** trên 254 đơn × 9 trường. BH62439 đọc
thẳng persisted rows — 4 dòng (1 AUTO + 3 PENDING), CẦN KIỂM TRA, doanh thu
66.000.000, LN kế toán 500.000 coverage 1/4, LN KPI 400.000 coverage 1/4, ba
dòng PENDING mỗi dòng ĐÚNG 5 mã lý do đúng thứ tự, mọi giá vốn/lợi nhuận
`NULL` ⟹ khớp TRỌN VẸN Oracle C. INV-1…INV-7 recompute độc lập: 0 vi phạm.
Vũ trụ reason code reviewer TỰ dẫn xuất từ enum/hằng số = ĐÚNG 21 mã, bảng
nhãn phủ TOÀN PHẦN, 7 nhãn S069 nguyên từng chữ. PII kiểm theo GIÁ TRỊ bằng
sentinel trên HTML thật của cả hai route: 0 giá trị cấm xuất hiện. CHỈ-ĐỌC
chứng minh bằng AST + hash 4 bảng trước/sau 7 lượt GET (không một byte đổi).
(d) Chạy lại: focused 89 passed · PRA-003 67 passed (không sửa test) · legacy
82 passed · PRA-002 32 passed · Golden Baseline **58 passed, 2 skipped** ·
full suite 1962 passed, 11 skipped (baseline `8181ceb` = 1873 passed, 11
skipped ⟹ +89 đúng số test mới, skip không đổi); validators
structure/project_state/evidence/task_completion = PASS,
reference_integrity = FAIL đúng 3 issue REM-T06 pre-existing (không issue
mới); `git diff --check` sạch trên DẢI COMMIT; `branch_authority_check.sh` =
AUTHORITY_OK.
(e) Change budget đo lại: Python production 226 · template 132 · CSS 13 ·
85 test mới — dưới MỌI biên (DỪNG CỨNG 400 / 220 / 25, SÀN 30); 0 file trong
danh sách CẤM bị chạm; `SCHEMA_CHANGE = MIGRATION = INDEX = DEPENDENCY =
CONFIG = 0`.
QUYẾT ĐỊNH: `ACCEPT_WITH_NON_BLOCKING_FINDINGS` — 0 BLOCKING finding;
6 NON_BLOCKING (`FIND-PRA004-04` xác nhận phân loại `DOC_INCONSISTENCY`;
`FIND-PRA004-05/06/07/08/09` mới, mỗi cái kèm RE-TRIGGER CONDITION).
Repair cycle tiêu thụ: **0** (còn lại 1/1).
LƯU Ý (`FIND-PRA004-09`): hai ô `Evidence:` của CHECK-12 và CHECK-13 trong
CHÍNH file này đang giữ nhầm văn bản `Yêu cầu:` của nhau, và `Executed By:`
của CHECK-12 ghi S101. Reviewer CỐ Ý không tự sửa — gộp vào một lần docs
reconciliation cùng `FIND-PRA004-04` ở khâu chuẩn bị Controlled Integration.
Bản FROZEN `46a5cdb` nguyên vẹn và vẫn là thẩm quyền; reviewer đã thực thi
theo yêu cầu đọc từ bản đó.

### Nghiệm Thu Thật

#### CHECK-PRA004-13 — Thời gian tải danh sách đơn trên tập lớn
Priority:
RECOMMENDED

Status:
PASS

Evidence Level:
E1

Evidence:
PASS (S101, 2026-09-03) — CHỈ ĐO, không tối ưu suy đoán.
`tests/test_web_sales_detail.py::test_the_order_list_stays_usable_on_a_large_period` dựng
12.000 dòng hiện hành (4.000 đơn × 3 dòng) rồi đo `sales_queries.order_list()` cho kỳ
"Toàn bộ dữ liệu":

```
CHECK-PRA004-13 · 4000 đơn / 12.000 dòng · order_list = 85.2 ms
```

Dưới ngưỡng RE-TRIGGER 3 giây gần hai bậc độ lớn ⟹ pagination KHÔNG trở thành REQUIRED,
và phiên này KHÔNG tự thêm pagination, KHÔNG thêm chỉ mục nào (`INDEX = 0`).
RE-TRIGGER CONDITION giữ nguyên: số đo > 3 giây ⟹ pagination thành REQUIRED và phải mở
như một quyết định RIÊNG.

#### CHECK-PRA004-14 — Owner Production Acceptance Tháng 09/2026
Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E1

Evidence:
Yêu cầu: Owner tự thực hiện TRỌN VẸN 8 bước của mục 21 trên production thật và ghi lại kết quả. Không suy dẫn, không dựng fixture "giống production", không đóng bằng ảnh chụp mô tả lại. Bốn con số 40 / 15 / 25 / 61 phải khớp ĐÚNG. Các giá trị khác Owner đọc được ghi dưới nhãn `OBSERVED_ONLY` và KHÔNG viết ngược thành kỳ vọng đặt trước.

---

## Yêu Cầu Evidence

| Yêu cầu | Nội dung |
|---|---|
| Risk 3 ⟹ E1 | Mọi REQUIRED check thực thi được PHẢI có E1 (output lệnh/test nguyên văn). `governance/core/EVIDENCE_STANDARD.md` |
| E2 | CHECK-PRA004-09 (ranh giới PII) và CHECK-PRA004-12 (Independent Review) bắt buộc E2 |
| Không bịa | Không bịa output lệnh, kết quả test, mã HTTP, ảnh chụp, kết quả CI, hay sự phê duyệt của con người. Chưa thực thi ⟹ `Status: NOT_TESTED` |
| Oracle dẫn xuất, không chép tay | CHECK-PRA004-04 phải DẪN XUẤT vũ trụ mã từ enum/hằng số trong mã nguồn |
| Oracle đi qua đường production | CHECK-PRA004-02/03 phải persist qua `run_import_production` + `history_writer`, không dựng bảng bằng tay |
| Production | CHECK-PRA004-14 chỉ đóng bằng bằng chứng Owner đọc trên production thật |
| `git diff --check` | Kiểm trên DẢI COMMIT, không chỉ working tree (bài học FIND-PRA003-02) |

---

## Tiêu Chí Hoàn Thành (Exit Criteria)

1. 11/11 REQUIRED check PASS với evidence level bắt buộc được thoả.
2. 0 BLOCKING finding chưa giải quyết; mọi `HARDENING`/`DEFER` có RE-TRIGGER
   CONDITION cụ thể được ghi lại.
3. CHANGE_BUDGET không vượt DỪNG CỨNG, hoặc đã có quyết định Owner tường minh.
4. Review budget không vượt 1 blocking repair cycle, hoặc đã có
   `OWNER_EXTENSION`.
5. Golden Baseline `58 passed, 2 skipped`; full suite không giảm; validators
   giữ nguyên trạng thái baseline (3 issue REM-T06 đã biết, không thêm).
6. Toàn bộ test của PRA-003 PASS NGUYÊN VẸN, KHÔNG file test nào của PRA-003
   bị sửa.
7. `PROJECT/PROJECT_PROGRESS.md`, `PROJECT/LO_TRINH_DE_HIEU.md` và
   `PROJECT/REVIEW_BUDGET_LEDGER.md` đã cập nhật.
8. Session handoff đã viết (Task Mode = MAJOR).
9. `SCHEMA_CHANGE = 0`, `MIGRATION = 0`, `INDEX = 0`, `DEPENDENCY = 0`,
   `CONFIG = 0`, `TRACKING_CHANGED = NO`, `INFRASTRUCTURE_CHANGED = NO`,
   `PROTECTED_CORE_IMPACT = NONE`.

---

## Điều Kiện Kích Hoạt Leo Thang (Escalation Triggers)

| Kích hoạt | Hành động |
|---|---|
| Python production chạm 330 dòng | Dừng viết mã, lập BUDGET-AWARE PLAN cho phần còn lại |
| Python production sẽ vượt 400 dòng | `STOP = CHANGE_BUDGET_EXCEEDED` — Owner quyết |
| Cần sửa bất kỳ file nào trong danh sách CẤM của mục 18 | `SCOPE EXPANSION REQUIRED` — không sửa trước, hỏi trước |
| Cần sửa hoặc nới một test của PRA-003 để test PRA-004 xanh | `STOP` — đó là làm yếu một gate đã accepted, xem mục 14.4 |
| Cần một business rule chưa có thẩm quyền (chủ đơn khi nhiều nhân viên, phân loại product-line, quy tắc gộp reason) | Dừng — Owner quyết, KHÔNG tự phát minh |
| Discovery/implement thấy cần INSERT/UPDATE/DELETE | Dừng — `ARCHITECTURE_CHANGE_REQUIRED`, không tự triển khai |
| Cần đổi Tracking | Dừng — ghi dependency, tìm Reports-only alternative trước |
| Đã dùng hết 1 blocking repair cycle mà vẫn còn BLOCKING | `OWNER_EXTENSION REQUIRED` — không mở lineage mới, không đổi tên task để reset ngân sách (V4.1 §2) |
| Phát hiện double-count hoặc trộn nguồn trong dữ liệu đã lưu | Dừng ngay — đó là defect của PRA-002, không vá ở tầng trình bày |
| Canonical HEAD đã moved so với `BASE_SHA` | `STOP = CANONICAL_MOVED` — đồng bộ và đánh giá lại trước khi tiếp tục |

---

## Đăng Ký File Đã Thay Đổi (Changed Files Registry)

Điền trong phiên implement. Tại thời điểm freeze contract: **0 file production
thay đổi**.

| File | Loại | Delta | Phiên |
|---|---|---|---|
| `app/web/sales_queries.py` | Python production (MỚI) | +141 | S101 |
| `app/web/sales_presentation.py` | Python production (MỚI) | +93 | S101 |
| `app/web/server.py` | Python production (chỉ 2 route + globals Jinja) | +34 | S101 |
| `app/beta_presentation.py` | Python production (chỉ THÊM 14 key nhãn) | +14 | S101 |
| `app/web/templates/ban_hang.html` | Template (MỚI) | +46 | S101 |
| `app/web/templates/ban_hang_chi_tiet.html` | Template (MỚI) | +69 | S101 |
| `app/web/templates/_pipeline_bits.html` | Template (chỉ THÊM macro `reason_row`) | +10 | S101 |
| `app/web/templates/layout.html` | Template (1 dòng tab "Bán hàng") | +1 | S101 |
| `app/web/static/css/tinphat-ui.css` | CSS (chỉ THÊM) | +10 | S101 |
| `tests/test_sales_queries.py` | Test (MỚI) | 31 test | S101 |
| `tests/test_sales_presentation.py` | Test (MỚI) | 24 test | S101 |
| `tests/test_web_sales_detail.py` | Test (MỚI) | 34 test | S101 |
| `docs/tasks/TASK-PRA-004-ban-hang-review-detail.md` | Evidence (check matrix + registry) | — | S101 |
| `docs/sessions/S101-pra-004-major-implementation.md` | Session record (MỚI) | — | S101 |
| `PROJECT/PROJECT_PROGRESS.md` | Trạng thái dự án | — | S101 |
| `PROJECT/LO_TRINH_DE_HIEU.md` | Lộ trình | — | S101 |
| `PROJECT/REVIEW_BUDGET_LEDGER.md` | Ngân sách review (cycle KHÔNG tiêu) | — | S101 |

Tổng: **Python production +282** (MỤC TIÊU 266 · CẢNH BÁO MỀM 330 · DỪNG CỨNG 400) ·
**Template +126** (trần 220) · **CSS +10** (trần 25) · **89 test mới** (sàn 30, 0 skip mới).

---

## Ghi Chú (Notes)

- Thứ tự triển khai bắt buộc: `sales_queries` → mở rộng
  `REASON_DISPLAY_LABELS` → `sales_presentation` → hai route → hai template →
  CSS. Test tầng đơn vị viết TRƯỚC test route và test integration.
- `sales_presentation` **import** `analytics_presentation`; nó KHÔNG nhân bản
  `money`/`count`/`coverage`/`profit`/`period_*`. Đang chép lại một trong các
  hàm đó ⟹ sai hướng, dừng lại.
- Lý do cần kiểm tra hiển thị dưới dạng dòng phụ dưới dòng hàng PENDING,
  KHÔNG phải một cột bảng — một dòng có tới 6 lý do.
- Toàn bộ tài liệu discovery nền:
  `docs/sessions/S100-pra-004-ban-hang-review-detail-discovery.md`. Khi tài
  liệu này và S100 mâu thuẫn, **tài liệu này thắng**.
- `INFERENCE` — nếu phiên implement phát hiện `pending_reasons_json` trên
  dữ liệu production 09/2026 chứa một mã NGOÀI vũ trụ đóng 21 mã của mục
  20.4, thì tiền đề của CHECK-PRA004-04 sai và phải dừng để đánh giá lại —
  đây là RE-TRIGGER CONDITION tường minh, không phải lời hứa.
