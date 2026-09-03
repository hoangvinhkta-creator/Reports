# TASK-PRA-005 — Sản Phẩm (Mặt Hàng Trên Chứng Từ) — Aggregation View (CHỈ-ĐỌC)

## Metadata

Status:
READY

Phase:
PHASE-PRA — Slice 5 (phân hoạch lại cùng tập dòng bán hiện hành theo chiều
mặt hàng, thay vì theo chiều nhân viên PRA-003 hay theo chiều đơn PRA-004)

Task Mode:
MAJOR

Primary Agent Tier:
Tier B (tầng CHỈ-ĐỌC; blast radius theo failure path = hiển thị sai đóng góp
của một mặt hàng vào doanh thu/LN KPI của kỳ → Owner kết luận sai về mặt
hàng đó)

Escalation Tier:
Owner (mọi business semantics chưa có thẩm quyền); Independent Reviewer E2
theo `governance/templates/E2_INDEPENDENT_REVIEW_TEMPLATE.md`

Difficulty:
3/5

Risk:
3

Blast Radius:
3/5 — chấm theo failure path (`governance/core/V4_1_POLICY_FREEZE.md` §4),
KHÔNG theo tên module. Đường hỏng tệ nhất: (a) một dòng dịch vụ/phí bị lọc
âm thầm khỏi bảng, làm tổng bảng KHÔNG còn khớp tổng kỳ (Owner đối chiếu sai
mà không biết); (b) ô LN KPI của một mặt hàng bị coalesce về `0` thay vì `—`
khi không có dòng `AUTO` nào, khiến Owner đọc nhầm "mặt hàng này lỗ/không
lãi" thành "mặt hàng này không có dữ liệu"; (c) nhãn tóm tắt gọi sai
"Số sản phẩm" trong khi con số đếm cả dòng phí/dịch vụ, khiến Owner tin đó
là số SKU thật. KHÔNG phải HIGH vì: toàn bộ touch area CHỈ-ĐỌC (không một
câu `INSERT`/`UPDATE`/`DELETE` nào), KHÔNG đổi dữ liệu đã lưu, KHÔNG đổi
KPI/lương đã tính, KHÔNG chạm bất biến no-double-count (thuộc `TASK-PRA-002`,
PRA-005 chỉ đọc lại kết quả của nó), KHÔNG tạo product identity thứ hai.

Project Profile:
PRODUCT

Root task lineage (V4.1): `TASK-PRA-005` (root MỚI. KHÔNG kế thừa và KHÔNG
tiêu ngân sách của `TASK-PRA-001`, `TASK-PRA-002`, `TASK-PRA-003`,
`TASK-PRA-004` hay bất kỳ lineage nào khác). Review budget: **MEDIUM = 1
blocking repair cycle** (`governance/core/V4_1_POLICY_FREEZE.md` §2).
Ledger: `PROJECT/REVIEW_BUDGET_LEDGER.md` → "Root Task: TASK-PRA-005".

Kế hoạch gốc: `docs/tasks/TASK-PRA-000-persistent-reporting-analytics-plan.md`.
Nền dữ liệu: `docs/tasks/TASK-PRA-002-pipeline-persistence-reconciliation.md`
(DONE). Nền trình bày/truy vấn: `docs/tasks/TASK-PRA-003-tong-quan-nhan-vien.md`
(DONE). Nền drill-down: `docs/tasks/TASK-PRA-004-ban-hang-review-detail.md`
(DONE).

Discovery session: S105 (2026-09-03, nhánh `claude/pra-005-discovery-dsryx5`,
docs-only, 0 dòng production code) —
`docs/sessions/S105-pra-005-san-pham-discovery.md`. Xác minh + tích hợp
fast-forward vào canonical: S106 (2026-09-03). `DISCOVERY_EXIT_GATE = PASS`.

Contract Freeze session: **S107** (2026-09-03, nhánh
`claude/pra-005-contract-freeze-99nuai`) — file này +
`docs/sessions/S107-pra-005-contract-freeze.md`.
`BASE_SHA = 1ebb0021e13f85fe7ac7825e1219583e4c682889` (HEAD nhánh canonical
`claude/extract-upload-repo-gq2ws4` lúc freeze contract — đã verify khớp
EXACT kỳ vọng đầu phiên, `CANONICAL_MOVED = KHÔNG`).

Owner Decisions khoá tại phiên này: **OD-PRA005-01** (khoá gộp) và
**OD-PRA005-02** (dòng dịch vụ/phí) — nâng từ khuyến nghị Discovery (S105 §28)
thành `OWNER_DECISION` chính thức, ghi tại `PROJECT/PROJECT_DECISIONS.md`
DEC-173. Cả hai đúng phương án A/khuyến nghị mà S105 §28 đã nêu.

Quy ước: file DỰ KIẾN tạo được viết KHÔNG kèm phần mở rộng (ví dụ
`app/web/sales_queries`); file đã tồn tại viết đủ đường dẫn (ví dụ
`app/web/server.py`).

Quy ước phân loại: `FACT` (đo được trong repo/dữ liệu phiên này) ·
`OWNER_DECISION` (Owner đã chốt) · `INFERENCE` (suy từ code/evidence) ·
`ASSUMPTION` (chưa verify) · `UNKNOWN`.

**KHÔNG production implementation trong phiên này.** File này là Contract —
định nghĩa cái sẽ được xây, không xây nó.

---

## (1) Mục Tiêu (Goal) / Business Purpose

Đóng băng câu hỏi nghiệp vụ PRA-005 V1 trả lời, đúng nguyên văn:

> "Trong khoảng thời gian đang xem, các mặt hàng ghi trên chứng từ bán hàng
> đóng góp như thế nào vào số lượng, số đơn, doanh thu và LN KPI đã biết?"

Đây là **management analytics mô tả** (descriptive). Nó KHÔNG phải, và
KHÔNG được ngụ ý là:

```
Product Master · inventory analytics · purchase analytics
canonical SKU analytics · product recommendation · margin optimization
forecasting · ranking/scoring system
```

PRA-005 là **phân hoạch lại CÙNG tập dòng bán hiện hành** theo chiều mặt
hàng, giống hệt cách PRA-003 phân hoạch theo chiều nhân viên và PRA-004
theo chiều đơn. Nó KHÔNG phát minh chỉ tiêu mới — nó dùng đúng `_metrics()`
đã nghiệm thu với một `GROUP BY` khác.

---

## (2) Business Authority — Existing Accepted Contracts (tái dụng, KHÔNG diễn giải lại)

Thứ tự thẩm quyền (không đảo):

```
OWNER BUSINESS INTENT → ACCEPTED BUSINESS MODEL → PERSISTED DATA MODEL
                      → CURRENT CODE → TESTS
```

`FACT` — đã nghiệm thu ở PRA-003/PRA-004, PRA-005 TÁI DỤNG NGUYÊN VẸN:

| Mã | Hợp đồng | Vị trí |
|---|---|---|
| EAC-1 | Bảy chỉ tiêu + coverage; LN KPI chỉ cộng dòng `AUTO` | `app/web/analytics_queries.py::_metrics()` |
| EAC-2 | `coverage()` dạng `N / M dòng`, cố ý KHÔNG phần trăm | `app/web/analytics_presentation.py:75` |
| EAC-3 | `profit()` — không đường nào render lợi nhuận thiếu coverage | `analytics_presentation.py:87` (quy tắc P4) |
| EAC-4 | `NULL` luôn thành `—` | `money()`/`count()` |
| EAC-5 | Nhãn ô số lượng là "Tổng số lượng", KHÔNG là "Số lượng sản phẩm"/"Tổng số SP" — chưa có quy tắc phân loại product-line có thẩm quyền | `analytics_presentation.py:41-48` |
| EAC-6 | `_period()` luôn kèm `sale_date IS NOT NULL` | `analytics_queries.py` |
| EAC-7 | Từ vựng nội bộ (`price_source`, `kpi_purchase_provenance`, `product_key`, `occurrence_index`…) BỊ CẤM khỏi UI quản lý | `sales_queries.py:187-195` |
| EAC-8 | `is_non_product_line()` là heuristic GIẢM NHIỄU validation, KHÔNG phải phân loại sản phẩm, KHÔNG được persist | `app/modules/validation/rules.py:52-69` |
| EAC-9 | `sales_queries` giữ hàng rào PII RIÊNG, hẹp hơn `analytics_queries` đúng một trường (`product_raw` không nằm trong hàng rào) — tiền lệ PRA-004, KHÔNG được nới `analytics_queries` | `TASK-PRA-004` mục 14.4 |
| EAC-10 | `order_line_current` JOIN đúng version hiện hành; no-double-count là tính chất CẤU TRÚC bảng | `_joined()` |

`ASSUMPTION / NEEDS_AUTHORITY` — KHÔNG được biến thành requirement:

- Phân loại product-line ("dòng nào là sản phẩm thật/dịch vụ/phí"). Chưa có
  thẩm quyền (EAC-5, EAC-8). PRA-005 KHÔNG phân loại (xem mục 6).
- Canonical Product Identity phủ toàn phần. Chưa đủ coverage (mục 3).

---

## (3) OD-PRA005-01 — Khoá Gộp Mặt Hàng — `OWNER_DECISION`

```
GROUPING_CONTRACT = NORMALIZED_RAW_DOCUMENT_DESCRIPTION
RAW_PRODUCT_GROUP = NFC(product_raw).strip()
```

PRA-005 V1 gộp theo **mô tả sản phẩm thô đã chuẩn hoá từ chứng từ bán
hàng**. Về mặt kỹ thuật, đây CHÍNH LÀ khoá đã tồn tại và đã nghiệm thu ở
`TASK-PRA-002`:

```
product_key = sha256( NFC(product_raw).strip() )
```

(`app/history/keys.py:70`, hợp đồng khoá `TASK-PRA-002` §5.1, DEC-166,
DEC-171). Được TÁI DỤNG NGUYÊN VẸN — implementation KHÔNG được tạo một hàm
chuẩn hoá thứ hai chỉ vì tên gọi nghiệp vụ khác tên trường kỹ thuật; chỉ khi
ngữ nghĩa `product_key` thay đổi thì mới cần đánh giá lại tương đương.

**Đây KHÔNG PHẢI:**

```
canonical Product Identity · SKU authority · Tracking Product Identity
```

Tracking **vẫn là Product Identity Authority duy nhất** (DEC-103/ADR-106,
S105 §33/§34) — PRA-005 KHÔNG tạo hệ thứ hai, KHÔNG ghi đè, KHÔNG đọc/sửa
Tracking.

### Lý do (đã đo, S105 §8-§9)

Discovery đo được `canonical_product_code` = 0/349 trên fixture golden vì
identity chỉ điền khi có Tracking capture tại thời điểm xử lý (không nằm
trong repo, đúng thiết kế); bằng chứng thật S068 cho thấy trên production nó
cũng KHÔNG phủ hết (`identity unresolved 31/83`). Một khoá gộp có thể `NULL`
trên phần lớn dòng không thể là khoá phân hoạch của một bảng "toàn bộ mặt
hàng trong kỳ". Owner chấp nhận **SPLIT trung thực thay vì MERGE không an
toàn**.

### Vì sao KHÔNG các phương án khác

```
NO fuzzy merge
NO substring merge
NO model-code merge
NO COALESCE(product_raw_key, canonical_product_code) hybrid identity
```

Bằng chứng bác bỏ (S105 §9, đo trên fixture golden thật):

| Mã | Các chuỗi | Đọc đúng |
|---|---|---|
| `FTKB50ZVMV` | `Điều hoà Daikin  FTKB50ZVMV` · `Máy lạnh Daikin Inverter 2 HP FTKB50ZVMV` | SPLIT THẬT — cùng một máy, hai cách gọi |
| `LC-70` | `Tủ Mát Alaska LC-70` · `Tủ Mát Alaska LC-70 trắng` | KHÔNG CHẮC — có thể là biến thể, có thể không |
| `TD-H80SEV` | `…TD-H80SEV(SK)` · `…TD-H80SEV(WK)` | TÁCH ĐÚNG — SK/WK là hai SKU màu khác nhau, gộp lại mới SAI |

Dòng thứ ba là bằng chứng trực tiếp: một quy tắc "gộp theo mã model" sẽ sửa
đúng dòng một và làm HỎNG dòng ba. `COALESCE` hybrid = KHÔNG khuyến nghị vì
cùng một mặt hàng sẽ nhảy giữa hai bucket khác nhau tuỳ capture của lần chạy
đó, khiến bảng đổi hình dạng giữa hai kỳ mà không có sự kiện nghiệp vụ nào.

**Các tên gọi khác nhau trên chứng từ của CÙNG một sản phẩm thực tế có thể
tiếp tục hiển thị thành các dòng riêng biệt trong PRA-005 V1.** Đây là hành
vi ĐÃ CHẤP NHẬN, không phải bug (mục 10).

---

## (4) OD-PRA005-02 — Bao Gồm Toàn Bộ Dòng Chứng Từ — `OWNER_DECISION`

```
SERVICE_FEE_TREATMENT = INCLUDE_ALL
```

PRA-005 V1 gồm **TẤT CẢ** các dòng chứng từ bán hàng, kể cả các mô tả
không giống hàng tồn kho thật (`Chi phí vận chuyển`, `Chênh VAT`, `Phụ Phí`,
`Giá treo Tivi`…) nếu chúng tồn tại trong dữ liệu nguồn đã accepted. KHÔNG
loại bỏ chỉ vì mô tả "trông không như sản phẩm".

### Lý do

Reports hiện KHÔNG có phân loại có thẩm quyền cho `product` / `service` /
`fee` / `adjustment` (EAC-5, EAC-8). Do đó:

```
NO heuristic exclusion
NO is_product authority
NO is_service authority
NO is_fee authority
```

`is_non_product_line()` (`app/modules/validation/rules.py`) là heuristic
GIẢM NHIỄU cho validation, tài liệu chính nó nói rõ *"must never be tuned to
reproduce a historical count"* — dùng nó để lọc bảng PRA-005 sẽ biến một
công cụ giảm nhiễu thành một authority phân loại mà nó chưa từng được thiết
kế để làm, và sẽ vừa thiếu (bắt nhầm phụ kiện thật như "Giá treo Tivi") vừa
thừa.

### Mặc định trình bày

```
DEFAULT_SORT = REVENUE DESC
```

Đây là **mặc định trình bày, không phải phân loại nghiệp vụ**. Đo được
(S105 §13/§28): dòng dịch vụ/phí chiếm 6,3%–7,8% SỐ DÒNG nhưng chỉ
0,14%–0,25% DOANH THU của kỳ — sắp theo doanh thu khiến chúng tự chìm xuống
mà KHÔNG cần một luật loại trừ nào.

---

## (5) Terminology — FROZEN

Navigation/page: **"SẢN PHẨM"** — chấp nhận được như khái niệm nghiệp vụ
hướng người dùng.

Trong bảng/chỉ tiêu, dùng: **"MẶT HÀNG"**.

CẤM dùng trong bảng/chỉ tiêu: `SKU chuẩn`, `Sản phẩm chuẩn`, `Product
Identity`.

Ghi chú công khai BẮT BUỘC trên trang (một câu, tiếng Việt, đọc được bởi
người không rành kỹ thuật):

> "Mặt hàng được gộp theo tên ghi trên chứng từ. Các tên khác nhau của cùng
> một sản phẩm có thể được hiển thị thành các dòng riêng."

CẤM phơi ra UI quản lý (EAC-7, mở rộng): `SHA256`, `NFC`, `product_key`,
`RAW_PRODUCT_GROUP`, cùng toàn bộ danh sách từ vựng nội bộ đã cấm ở
`TASK-PRA-004` mục 14.3.

---

## (6) Product Identity Limitation — FROZEN

```
PRODUCT_IDENTITY_CLAIM = NOT_CANONICAL_PRODUCT_IDENTITY
```

PRA-005 V1 **KHÔNG** tuyên bố canonical product analytics. Ví dụ Discovery
đã biết (`FTKB50ZVMV`, mục 3) có thể tiếp tục hiển thị thành hai dòng riêng
— đây là hành vi **ĐÃ CHẤP NHẬN**, KHÔNG sửa trong PRA-005 V1.

Tracking vẫn là authority tương lai nếu canonical-product analytics trở nên
đủ thẩm quyền để triển khai. **Finding != task** — FIND-PRA005-01 (mục 20)
ghi lại giới hạn này, không mở một task repair.

---

## (7) All-Line Inclusion — FROZEN

Tất cả dòng chứng từ tham gia PRA-005 V1, kể cả các mô tả như:

```
Chi phí vận chuyển · Chênh VAT · Phụ Phí · Giá treo Tivi
```

nếu chúng tồn tại trong dữ liệu nguồn đã accepted. KHÔNG phân loại, KHÔNG
loại bỏ. Ngữ nghĩa BẮT BUỘC của chỉ tiêu đếm mặt hàng là **"Số mặt hàng trên
chứng từ"**, KHÔNG tuyên bố mọi nhóm là một SKU tồn kho.

---

## (8) Summary Contract — FROZEN (đúng bốn chỉ tiêu)

### 8.1 SỐ MẶT HÀNG TRÊN CHỨNG TỪ

```
COUNT(DISTINCT RAW_PRODUCT_GROUP) trong phạm vi lọc hiện hành
```

CẤM nhãn: **"Số sản phẩm"** (EAC-5, S105 §14 — con số này đếm cả
"Chi phí vận chuyển", "Chi phí lắp đặt", "Chênh VAT", "Phụ Phí"; gọi nó là
"số sản phẩm" là phát minh một quy tắc phân loại product-line chưa tồn tại).

### 8.2 TỔNG SỐ LƯỢNG

Tái dụng NGUYÊN VẸN ngữ nghĩa số lượng đã accepted (`SUM(quantity)`, EAC-1,
EAC-5). KHÔNG coalesce về `0`.

### 8.3 DOANH THU (NET)

Tái dụng NGUYÊN VẸN ngữ nghĩa doanh thu đã accepted (`SUM(total_sales)`,
đọc thẳng giá trị đã lưu). KHÔNG tính lại từ `(SL × đơn giá − chiết khấu)`.

### 8.4 LN KPI

```
SUM(CASE WHEN status = 'AUTO' THEN eligible_kpi_profit END)
```

CHỈ cộng giá trị KPI-profit ĐÃ BIẾT (dòng `AUTO`). Hiển thị coverage đi kèm:

```
LN KPI
5.000.000
7 / 10 dòng
```

Giá trị KPI thiếu là **UNKNOWN**, KHÔNG phải `0`. Một dòng `PENDING` có
`eligible_kpi_profit` khác `NULL` vẫn KHÔNG vào tổng (D1/P1 đã nghiệm thu,
không được "cải tiến").

---

## (9) Main Table Contract — FROZEN (đúng năm cột)

```
MẶT HÀNG · SỐ LƯỢNG · SỐ ĐƠN · DOANH THU · LN KPI
```

Không cột bắt buộc nào khác. CẤM thêm:

```
aggregate Giá mua tham chiếu · Coverage (cột riêng) · Trạng thái dữ liệu
Brand · Category · Vendor/NCC · Margin % · Score · Rank label
```

Lý do loại từng cột, đã đóng băng tại Discovery (S105 §25):

| Cột bị loại | Lý do |
|---|---|
| Giá mua tham chiếu | Mục 12 — không tồn tại như một đại lượng cấp mặt hàng |
| Coverage (cột riêng) | Đã nằm TRONG ô LN KPI qua `profit()` (EAC-3); cột riêng là lặp |
| Trạng thái dữ liệu | Coverage `N / M dòng` đã nói đúng điều đó; cột này cần một phân loại mới chưa ai quyết |

Nhãn cột "MẶT HÀNG" = `MIN(product_raw)` của nhóm — chọn `MIN` chỉ để có
MỘT chuỗi đại diện ổn định cho hiển thị, KHÔNG mang ý nghĩa nghiệp vụ nào
khác.

---

## (10) Quantity Semantics — FROZEN

```
QUANTITY = SUM(order_line_source_version.quantity)
           cho mọi dòng đóng góp vào nhóm/phạm vi lọc
```

Tái dụng NGUYÊN VẸN ngữ nghĩa số lượng đã có. KHÔNG tạo quy tắc số lượng
riêng cho sản phẩm.

---

## (11) Order Count Semantics — FROZEN

```
ORDER_COUNT = COUNT(DISTINCT order_key)
              trong nhóm/phạm vi lọc, dùng order_key làm khoá đơn có thẩm quyền
```

Đếm ĐƠN nghiệp vụ phân biệt, KHÔNG đếm dòng. Giống cảnh báo đã có ở PRA-004
(`ORDER_COLUMN_NOTE`): cột này KHÔNG cộng được qua các mặt hàng (một đơn
nhiều mặt hàng được đếm ở nhiều dòng mặt hàng) — trang phải nói rõ điều đó.

---

## (12) Revenue Semantics — FROZEN

```
REVENUE = SUM(order_line_result_version.total_sales)
          cho các dòng đóng góp, ĐỌC THẲNG giá trị đã lưu
```

KHÔNG công thức doanh thu mới. Phải khớp (reconcile) với phân tích đã
accepted cho cùng phạm vi lọc (xem Acceptance A/C, mục 19). `GROUP BY
RAW_PRODUCT_GROUP` là một PHÂN HOẠCH của cùng tập dòng — doanh thu cộng qua
các mặt hàng bằng ĐÚNG tổng kỳ.

---

## (13) KPI Profit Semantics — FROZEN

```
KPI_PROFIT_SEMANTICS = SUM_KNOWN_VALUES_WITH_EXPLICIT_COVERAGE
```

Tái dụng CHÍNH XÁC `_metrics()` (mục 8.4). Hai điểm giữ nguyên, KHÔNG "cải
tiến": dòng `PENDING` có KPI-profit khác `NULL` vẫn không vào tổng; tập cộng
rỗng ⟹ `None` ⟹ hiển thị `—`, KHÔNG BAO GIỜ `0`. Reuse nguyên vẹn semantics
PRA-003/PRA-004.

Ví dụ (S105 §17): 10 dòng đóng góp, 7 biết KPI ⟹ tổng 7 giá trị đã biết +
coverage `7 / 10 dòng`. KHÔNG ngụ ý đây là lợi nhuận đầy đủ cho cả 10 dòng.

---

## (14) KPI Coverage Semantics — FROZEN

```
COVERAGE = (số dòng AUTO đóng góp) / (tổng số dòng đóng góp của nhóm đó)
```

Tái dụng nguyên vẹn `coverage()` — dạng `N / M dòng`, cố ý KHÔNG phần trăm
(EAC-2). Coverage nằm BÊN TRONG/cạnh ô LN KPI, qua `profit()` (EAC-3).
KHÔNG tạo cột bảng V1 riêng cho coverage trừ khi cấu trúc component trình
bày hiện có bắt buộc phải tách.

---

## (15) Reference Purchase Price — LOẠI KHỎI BẢNG SẢN PHẨM

```
REFERENCE_PRICE_CONTRACT = LINE_LEVEL_ONLY
```

KHÔNG hiển thị một Giá mua tham chiếu cấp mặt hàng. Lý do (S105 §18, DEC-172):

1. PP có hiệu lực TẠI NGÀY BÁN (DEC-172). Một nhóm mặt hàng gộp nhiều ngày
   bán khác nhau thì "PP của mặt hàng" **không phải một đại lượng tồn
   tại** — nó là nhiều giá trị tại nhiều thời điểm.
2. `AVG` là một con số không giao dịch nào tương ứng. `SUM` vô nghĩa.
   `MIN`/`MAX`/`LAST` đều là quy tắc nghiệp vụ mới chưa ai quyết.

CẤM tất cả:

```
NO average PP · NO latest PP · NO current PP · NO min PP · NO max PP
NO weighted PP
```

Giá mua tham chiếu tiếp tục hiển thị đúng nơi nó ĐÃ đúng: **cấp dòng/đơn,
trong `TASK-PRA-004`** (một ngày bán, một PP). "Giá mua đang áp dụng"
(point-in-time lookup cấp mặt hàng) là một câu hỏi khác — **DEFER**, không
đưa vào slice này.

---

## (16) Time Semantics — FROZEN, ĐỒNG NHẤT VỚI PRA-003/PRA-004

Ngày nghiệp vụ = `sale_date`. Tái dụng NGUYÊN VẸN
`analytics_queries.available_periods()` / `month_bounds()` /
`analytics_presentation.period_options()` / `period_label()`; cùng bất biến
`sale_date IS NOT NULL` trong MỌI kỳ. KHÔNG tạo ngữ nghĩa thời gian mới.
KHÔNG trend chart cho V1. KHÔNG monthly-series feature cho V1.

---

## (17) Default Sort — FROZEN

```
DEFAULT_SORT = REVENUE DESC
```

Sort là TRÌNH BÀY, không phải phân loại nghiệp vụ (mục 4). CẤM nhãn dòng:
`best`, `worst`, `top-performing`, `high-margin`, `slow-moving` — bất kỳ
nhãn kiểu đó đều cần một công thức và một Owner Decision chưa tồn tại.

Sắp xếp theo cột khác, nếu cơ chế đã có sẵn/rẻ để tái dụng, CÓ THỂ triển
khai sau bên trong CÙNG V1 nếu còn trong ngân sách. KHÔNG bắt buộc để
Contract PASS.

---

## (18) Drill-Down — REUSE PRA-004, USEFUL_BUT_DEFER NẾU VƯỢT NGÂN SÁCH

Đường tối thiểu ưu tiên (S105 §21):

```
Trang Sản phẩm
  → (1 truy vấn mới) các dòng bán của RAW_PRODUCT_GROUP trong kỳ, kèm order_key
  → link tới /ban-hang/<order_key>  (route PRA-004 ĐÃ CÓ, KHÔNG sửa)
```

KHÔNG xây một hệ thống chi tiết đơn thứ hai. Nếu direct filtered deep-link
đòi hỏi phạm vi bất tương xứng với ngân sách slice này:

```
DEFER direct product drill-down
```

thay vì mở rộng V1. Drill-down hữu ích nhưng KHÔNG được phép chặn bảng cốt
lõi (CHECK-PRA005-13, mục 24 — RECOMMENDED, không REQUIRED).

**Hàng rào PII cho đường drill-down mới:** tái dụng ĐÚNG tiền lệ EAC-9 —
`sales_queries` giữ hàng rào PII RIÊNG hẹp hơn `analytics_queries` đúng một
trường (`product_raw` không nằm trong hàng rào). PRA-005 KHÔNG được nới
`analytics_queries.py`, KHÔNG được sửa `tests/test_analytics_queries.py`.

---

## (19) Brand / Category / Vendor — DEFERRED

```
BRAND    = NOT_AVAILABLE (không cột nào ở bất kỳ bảng nào)
CATEGORY = NOT_AVAILABLE (product_group_final là HẰNG SỐ, không phải chiều
           phân tích — DefaultProductGroupProvider.lookup() trả None cho
           MỌI dòng, mọi dòng rơi về DIEN_MAY với provenance DEFAULT)
VENDOR   = NOT_AVAILABLE (khái niệm của Tracking; Tracking = READ-ONLY
           REFERENCE)
```

Freeze: **DEFERRED**. KHÔNG suy luận từ tên sản phẩm. KHÔNG mở một dự án
phân loại.

---

## (20) Findings từ Discovery — mang theo nguyên vẹn

### FIND-PRA005-01 — `product_key` SPLIT một sản phẩm thật · `NON_BLOCKING`

Đo được (S105 §9): `FTKB50ZVMV` tách thành 7 SL / 113.750.000 và 1 SL /
16.300.000; gộp lại sẽ là mặt hàng doanh thu #1 của kỳ. Xử lý: KHÔNG sửa mã,
KHÔNG thêm matching — xử lý bằng cách gọi tên (mục 5, 6) + OD-PRA005-01.

**RE-TRIGGER CONDITION:** khi Owner ghi nhận một quyết định thật bị sai vì
split, hoặc khi tỉ lệ split đo lại vượt ~5% chuỗi trong một kỳ.

### FIND-PRA005-02 — ô "Số sản phẩm" va chạm EAC-5 · `NON_BLOCKING`

Đã xử lý bằng đổi nhãn thành "Số mặt hàng trên chứng từ" (mục 8.1). Không
cần quyết định Owner thêm — đây là tuân thủ một hợp đồng đã nghiệm thu.

### FIND-PRA005-03 — `product_group_final` trông như category nhưng là hằng số · `NON_BLOCKING`

Ghi lại để phiên implementation không nhầm nó là chiều phân tích sẵn có
(mục 19).

```
BLOCKING_FINDINGS = 0
```

---

## (21) Persistence / Schema — FROZEN

```
SCHEMA_REQUIRED = NO
```

Mọi trường cần cho trang tối thiểu đã ánh xạ về cột đã persist (S105 §11):
`order_line_current.product_key` (khoá gộp), `order_line_source_version.
product_raw` (nhãn hiển thị), `sale_date`, `order_key`, `quantity`,
`sell_price`, `discount`, `total_sales`, `kpi_purchase_price` (cấp
dòng, dùng ở drill-down chứ KHÔNG aggregate — mục 15),
`eligible_kpi_profit`, `status`, `pending_reasons_json`. Bốn trường
brand/category/vendor/identity đầy đủ đều DEFER khỏi slice này (mục 19),
KHÔNG thay bằng cột mới.

Nếu implementation phát hiện một nhu cầu schema: **KHÔNG âm thầm migrate.**

```
STOP: SCHEMA_EXPANSION_REQUIRED
```

kèm chứng minh vì sao persistence hiện tại không đủ cho vertical đã
contract.

---

## (22) New Authority / Tracking — FROZEN

```
NEW_AUTHORITY_REQUIRED     = NO
TRACKING_CHANGE_REQUIRED   = NO
```

PRA-005 KHÔNG tạo product authority, service authority, brand authority,
category authority, vendor authority, hay price authority nào mới. Tracking
vẫn là Product Identity / PP authority duy nhất nơi áp dụng (mục 15).

---

## (23) Performance — FROZEN

Discovery đo (S105 §35, SQLite in-memory, đúng hình dạng truy vấn đề xuất):
`12.000 dòng · 2.491 nhóm · 24–27 ms`.

```
PERFORMANCE_CONTRACT = SESSION_MEASUREMENT_ONLY — KHÔNG freeze 27 ms thành SLA
```

Contract yêu cầu: dùng aggregation PostgreSQL thẳng, thông thường (khuôn
`employee_totals()` với `GROUP BY` khác). Không blocker hiệu năng nào đã
được chứng minh. Implementation phải ĐO đường truy vấn thật, tỉ lệ thuận với
quy mô — không dùng con số Discovery làm bằng chứng cho production
PostgreSQL.

CẤM:

```
cache subsystem · materialized view · warehouse · Redis
worker · queue · OLAP · Elasticsearch
```

---

## (24) Change Budget — RIÊNG CỦA PRA-005

KHÔNG kế thừa ngân sách còn dư của bất kỳ lineage nào khác. Ước tính
Discovery (S105 §31) là ESTIMATE, KHÔNG phải tiêu chí nghiệm thu chính xác.

```
CLASSIFICATION = SMALL VERTICAL

Python production (mục tiêu, tái dụng employee_totals()/order_detail() làm khuôn)
  app/web/sales_queries.py (delta — product_totals() + product_lines())  ≈  70
  app/web/sales_presentation.py (delta — định nghĩa cột mặt hàng)        ≈  60
  app/web/server.py (delta — 1 route mới)                                ≈  25
  ------------------------------------------------------------------------
  MỤC TIÊU (soft target)                                                ≤ 200 dòng

Template mới/sửa
  app/web/templates/san_pham.html                                       ≈  90
  app/web/templates/layout.html (delta — 1 dòng tab)                    =    1

Test mới    : theo tỉ lệ với PRA-003 (67)/PRA-004 (94) nhưng hẹp hơn
DOCS        : task file (đã ghi ở đây) + session implementation + review
CSS thêm    : ≤ 10 dòng, tái dụng class bảng đã có
```

Vượt bất kỳ điều nào dưới đây:

```
> 200 production Python LOC
schema migration
new persistence
new authority
Tracking modification
new subsystem
```

⟹

```
STOP: SCOPE_EXPANSION_REQUIRED
```

kèm giải thích REAL VERTICAL cụ thể nào không dựng được trong ngân sách.
KHÔNG âm thầm mở rộng.

---

## (25) Touch Area / Scope Lock

### ĐƯỢC PHÉP tạo mới

```
app/web/templates/san_pham.html
tests/test_product_queries.py            (hoặc mở rộng test_sales_queries.py
                                            — quyết định tại session implementation)
tests/test_product_presentation.py       (hoặc mở rộng test_sales_presentation.py)
tests/test_web_product_view.py
docs/sessions/S1xx-*.md                  (session implementation)
docs/reviews/TASK-PRA-005-INDEPENDENT-REVIEW-RECORD.md
```

### ĐƯỢC PHÉP sửa (giới hạn chặt)

```
app/web/sales_queries.py               — CHỈ THÊM product_totals() +
                                          product_lines(); KHÔNG sửa hàm hiện có
app/web/sales_presentation.py          — CHỈ THÊM định nghĩa cột/nhãn cho
                                          bảng mặt hàng; tái dụng money/
                                          count/coverage/profit đã có
app/web/server.py                      — CHỈ THÊM 1 route mới /san-pham +
                                          helper của nó
app/web/templates/layout.html          — CHỈ thêm 1 dòng tab "Sản phẩm"
app/web/static/css/tinphat-ui.css      — CHỈ THÊM
PROJECT/PROJECT_PROGRESS.md
PROJECT/LO_TRINH_DE_HIEU.md
PROJECT/REVIEW_BUDGET_LEDGER.md
docs/tasks/TASK-PRA-005-san-pham.md
```

### CẤM (SCOPE EXPANSION REQUIRED nếu cần chạm)

```
app/web/analytics_queries.py          ← PRA-003 đã accepted; EAC-9
app/web/analytics_presentation.py     ← chỉ ĐƯỢC import, KHÔNG được sửa
app/web/templates/tong_quan.html
app/web/templates/nhan_vien.html
app/web/templates/ban_hang.html
app/web/templates/ban_hang_chi_tiet.html
tests/test_analytics_queries.py
tests/test_analytics_presentation.py
tests/test_sales_queries.py            ← CHỈ mở rộng nếu chọn không tạo file mới; KHÔNG sửa test hiện có
tests/test_web_pipeline_analytics.py
tools/db/**                            ← schema, migration
app/history/**                         ← core persistence/reconciliation
app/web/history_store.py
app/web/history_writer.py
app/web/run_registry.py
app/web/storage_backend.py
app/modules/**                         ← protected core
app/pipeline.py · app/composition.py · app/demo.py
tests/fixtures/golden/**               ← oracle độc lập, KHÔNG sửa một byte
config/**
alembic.ini · render.yaml · Dockerfile · pyproject.toml
Toàn bộ Tracking
```

`PROTECTED_CORE_IMPACT` phải = `NONE`.

---

## (26) Hard Exclusions

PRA-005 V1 **KHÔNG** bao gồm, dưới bất kỳ hình thức nào:

```
production implementation trong phiên Contract Freeze này
schema migration · Tracking write · canonical product project
identity repair · fuzzy/model-code merge · service classification
brand/category/vendor inference · aggregate PP
accounting metrics (LN kế toán không phải chỉ tiêu của trang này)
trend chart · forecast · recommendation · scoring
inventory analytics · purchase analytics · NCC KPI
PRA-006 · REM-T06 repair · XLSX cleanup · general refactor · infra expansion
```

Ba issue `reference_integrity` của REM-T06 là pre-existing; PRA-005 KHÔNG
repair và KHÔNG được làm tăng số issue.

---

## (27) Acceptance Oracle — Real Data Acceptance Plan (FROZEN)

Theo đúng khuôn PRA-003 `CHECK-07` / PRA-004 `CHECK-14` (mục 20.5): Owner tự
mở production thật, không phải ảnh chụp, không phải fixture.

```
A. Doanh thu tóm tắt reconcile với phân tích đã accepted cho CÙNG phạm vi lọc
   (/tong-quan cùng kỳ).
B. Số lượng tóm tắt reconcile với phân tích đã accepted cho cùng phạm vi lọc.
C. Σ(doanh thu theo nhóm mặt hàng) = tổng doanh thu đã lọc của kỳ.
D. Σ(số lượng theo nhóm mặt hàng) = tổng số lượng đã lọc của kỳ.
E. Σ(LN KPI ĐÃ BIẾT theo nhóm mặt hàng) = LN KPI ĐÃ BIẾT của phân tích đã
   accepted cho cùng phạm vi.
F. Tử số/mẫu số coverage LN KPI reconcile với số dòng đóng góp thật.
G. Split FTKB50ZVMV (hoặc ví dụ tương đương đo được trên kỳ đang xem) VẪN
   TÁCH RIÊNG — không bị âm thầm gộp.
H. Dòng dịch vụ/phí (nếu tồn tại trong kỳ đang xem) VẪN nằm trong bảng.
I. Sắp xếp mặc định = doanh thu giảm dần.
J. KHÔNG hiển thị bất kỳ giá mua tham chiếu tổng hợp cấp mặt hàng nào.
K. `NULL != 0` — ít nhất một mặt hàng có coverage một phần: ô LN KPI của nó
   hiện `—` hoặc một số kèm `N / M dòng` với `N < M`, KHÔNG BAO GIỜ `0`.
L. Nếu drill-down được triển khai, nó dẫn đúng về `/ban-hang/<order_key>`
   (PRA-004) và các con số KHÔNG đổi so với PRA-004.
```

**KHÔNG freeze thêm bất kỳ con số tiền cụ thể nào của kỳ tương lai làm kỳ
vọng đặt trước** — Real Data Acceptance chạy trên dữ liệu production TẠI
THỜI ĐIỂM implementation, không phải một oracle đóng băng từ Discovery.

---

## (28) Phụ Thuộc (Dependencies)

- `TASK-PRA-002` — DONE. Cung cấp ba bảng, `product_key`, bất biến
  no-double-count.
- `TASK-PRA-003` — DONE. Cung cấp `_metrics()`, `coverage()`, `profit()`,
  model kỳ.
- `TASK-PRA-004` — DONE. Cung cấp `sales_queries`/`sales_presentation` làm
  khuôn tái dụng, hàng rào PII riêng (EAC-9), route `/ban-hang/<order_key>`
  làm đích drill-down.

Không phụ thuộc nào chưa xong. **IMPLEMENTATION_READY = YES.**

## Chặn (Blocks)

Không task nào hiện tại phụ thuộc PRA-005.

## An Toàn Để Chạy Song Song Với (Parallel-Safe With)

Không task nào khác đang IN_PROGRESS trên lineage PRA. PRA-005 chỉ ĐỌC ba
bảng pipeline nên an toàn song song với mọi công việc không sửa
`tools/db/schema.py` hay `app/history/**`.

---

## Ready Gate

Dùng `governance/core/TASK_READY_GATE_STANDARD.md`.

| Điều kiện | Trạng thái | Bằng chứng |
|---|---|---|
| Canonical HEAD khớp EXACT SHA kỳ vọng | PASS | `git rev-parse origin/claude/extract-upload-repo-gq2ws4` = `1ebb0021e13f85fe7ac7825e1219583e4c682889` |
| Nhánh phiên tạo từ đúng canonical đó | PASS | `claude/pra-005-contract-freeze-99nuai` @ `1ebb0021` (0 ahead, 0 behind) |
| Discovery DONE, Exit Gate PASS | PASS | S105/S106; `docs/sessions/S105-pra-005-san-pham-discovery.md` mục 41 |
| Mọi phụ thuộc DONE | PASS | Mục 28 |
| Business authority đủ cho mọi ô REQUIRED_NOW | PASS | Mục 2, 8, 9 |
| Không có OWNER_DECISION nào còn treo | PASS | Mục 3, 4 — OD-PRA005-01/02 đã khoá tại phiên này |
| Scope Lock đã định nghĩa | PASS | Mục 25 |
| Completion Gate đã freeze | PASS | Mục dưới |
| Change Budget + Review Budget đã đặt | PASS | Mục 24, Review Budget |
| Acceptance Oracle độc lập, đo lại được | PASS | Mục 27 |
| Schema / migration / dependency = 0 | PASS | Mục 21, 22 |

**READY = YES.**

---

## Completion Gate — FROZEN

Dùng `governance/core/TASK_COMPLETION_GATE_STANDARD.md` và
`governance/core/EVIDENCE_STANDARD.md`.

**FROZEN tại S107 (2026-09-03)**,
`BASE_SHA = 1ebb0021e13f85fe7ac7825e1219583e4c682889`.

15 check: **14 REQUIRED** · 1 RECOMMENDED. Risk 3 ⟹ mọi REQUIRED thực thi
được PHẢI đạt E1; CHECK-PRA005-14 (Independent Review) phải đạt E2.

Không xoá, không làm yếu bất kỳ REQUIRED check nào để task pass. Thay đổi
gate phải đi qua `COMPLETION GATE CHANGE PROPOSAL`.

Toàn bộ check dưới đây **CHƯA THỰC THI** tại phiên Contract Freeze này —
đúng theo `governance/core/EVIDENCE_STANDARD.md`: "Nếu chưa thực thi: Status = NOT_TESTED."

#### CHECK-PRA005-01 — Tầng truy vấn CHỈ-ĐỌC, cấu trúc AST
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Yêu cầu:
Bằng chứng CẤU TRÚC bằng AST trên `app/web/sales_queries.py` (delta), theo
đúng khuôn `test_the_sales_query_module_has_no_path_that_writes`: không
import `insert`/`update`/`delete`/`text`; không gọi
`begin()`/`commit()`/`execution_options()`; mọi truy vấn xuất phát từ
`order_line_current` và join qua `current_source_version_id`/
`current_result_version_id`.

Executed By:
Session S108 — PRA-005 MAJOR Implementation (Claude Code)

Timestamp:
2026-09-03

Evidence:
S108. `tests/test_product_queries.py::test_the_query_module_still_has_no_
write_path_after_the_product_delta` + `::test_product_totals_starts_from_
the_current_pointers` — PASS. AST xác nhận không import
`insert`/`update`/`delete`/`text`, không gọi
`begin()`/`commit()`/`execution_options()`; `order_line_current`,
`current_source_version_id`, `current_result_version_id` đều nằm trong tập
định danh của module (bao gồm delta `product_totals()`).

#### CHECK-PRA005-02 — Khoá gộp đúng `product_key`, KHÔNG fuzzy/substring/model-code merge
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Yêu cầu:
Test khẳng định `product_totals()` group theo đúng `product_key` (đã tồn
tại, `sha256(NFC(product_raw).strip())`) — KHÔNG casefold, KHÔNG bỏ dấu,
KHÔNG substring/model-code matching mới nào được thêm vào đường tính khoá.
Grep/AST xác nhận `product_totals()`/`product_lines()` không import hoặc gọi
bất kỳ hàm fuzzy-matching nào.

Executed By:
Session S108 — PRA-005 MAJOR Implementation (Claude Code)

Timestamp:
2026-09-03

Evidence:
S108. `tests/test_product_queries.py`: `test_A_two_lines_with_the_identical_
raw_name_group_into_one_row`, `test_B_two_different_raw_names_stay_on_
separate_rows`, `test_grouping_is_case_and_diacritic_sensitive_no_extra_
normalization`, `test_a_model_code_shared_by_two_real_different_skus_is_not_
merged` (đối chứng `TD-H80SEV(SK)`/`(WK)`, mục 3), `test_product_totals_
module_calls_no_fuzzy_matching_helper` (AST định danh, không văn xuôi) — tất
cả PASS. `product_lines()` KHÔNG được triển khai (drill-down DEFER, mục 18)
nên không có bề mặt fuzzy-matching thứ hai cần canh.

#### CHECK-PRA005-03 — Tóm tắt reconcile với phân tích đã accepted (Acceptance A, B)
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Yêu cầu:
Trên cùng fixture golden đã persist qua đường production, khẳng định
`SUM(revenue theo mặt hàng)` = doanh thu `/tong-quan` cùng kỳ, và
`SUM(số lượng theo mặt hàng)` = tổng số lượng `/tong-quan` cùng kỳ.

Executed By:
Session S108 — PRA-005 MAJOR Implementation (Claude Code)

Timestamp:
2026-09-03

Evidence:
S108. Triển khai đi XA HƠN reconcile bằng SUM: tóm tắt `/san-pham`
(`sales_presentation.product_summary()`) TÁI DỤNG NGUYÊN VẸN
`analytics_queries.period_totals()` (đã fetch sẵn ở `_pipeline_view()` cho
`/tong-quan` cùng kỳ) — khớp byte-identical theo cấu trúc, không chỉ theo số
đo. `tests/test_web_product_view.py::test_the_default_table_order_is_
revenue_descending` + oracle thật (S108 §"Xác Minh Oracle") xác nhận trên
`period_2026_01`: 226 nhóm, Σ quantity=407, Σ total_sales=3.562.310.000 —
khớp EXACT `analytics_queries.period_totals()` cùng kỳ.

#### CHECK-PRA005-04 — Tổng nhóm mặt hàng = tổng kỳ đã lọc (Acceptance C, D)
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Yêu cầu:
Khẳng định `Σ(doanh thu theo nhóm) = tổng doanh thu đã lọc` và
`Σ(số lượng theo nhóm) = tổng số lượng đã lọc` — đây là bằng chứng
`GROUP BY` là một PHÂN HOẠCH đúng của cùng tập dòng (không double-count,
không mất dòng).

Executed By:
Session S108 — PRA-005 MAJOR Implementation (Claude Code)

Timestamp:
2026-09-03

Evidence:
S108. `tests/test_product_queries.py::test_L_group_sums_reconcile_with_the_
accepted_period_totals` — PASS trên oracle THẬT (`period_2026_01`, 226
nhóm): `Σ(quantity) == totals["quantity"]`, `Σ(total_sales) ==
totals["total_sales"]`, `Σ(lines) == totals["lines"] == 351`, tất cả bằng
`==` chính xác (Decimal, không dung sai làm tròn).

#### CHECK-PRA005-05 — LN KPI known-sum + coverage reconcile (Acceptance E, F)
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Yêu cầu:
Khẳng định `Σ(LN KPI đã biết theo mặt hàng)` = LN KPI đã biết của
`/tong-quan` cùng kỳ; tử số/mẫu số coverage của từng mặt hàng khớp số dòng
`AUTO`/tổng dòng đóng góp thật.

Executed By:
Session S108 — PRA-005 MAJOR Implementation (Claude Code)

Timestamp:
2026-09-03

Evidence:
S108. `tests/test_product_queries.py::test_L_group_sums_reconcile_with_the_
accepted_period_totals` — `Σ(kpi_profit đã biết) == totals["kpi_profit"] ==
900.000` và `Σ(kpi_lines) == totals["kpi_lines"] == 2` trên oracle THẬT.
`tests/test_web_product_view.py::test_a_partial_coverage_item_never_renders_
zero_profit` xác nhận trên HTML thật hai mặt hàng có KPI đã biết hiện đúng
coverage `1 / 2 dòng` (Điều hòa Daikin FTHF25XVMV) và `1 / 5 dòng` (Máy giặt
LG 10kg FV1410S4W1) — khớp mẫu số/tử số dòng đóng góp thật của CHÍNH nhóm đó.

#### CHECK-PRA005-06 — `NULL != 0`
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Yêu cầu:
Test trên một mặt hàng KHÔNG có dòng `AUTO` nào — LN KPI hiển thị `—`,
KHÔNG BAO GIỜ `0`/`0đ`. Test trên một mặt hàng coverage một phần —
`N / M dòng` với `N < M`, giá trị KHÔNG bị coalesce.

Executed By:
Session S108 — PRA-005 MAJOR Implementation (Claude Code)

Timestamp:
2026-09-03

Evidence:
S108. Bốn trường hợp mục 8 KPI NULL CASES đều có test riêng, PASS:
`test_F_full_kpi_coverage_sums_every_known_line` (CASE A),
`test_G_partial_kpi_coverage_sums_only_the_known_lines` (CASE B, `1 / 2
dòng`), `test_H_zero_known_kpi_lines_reports_none_not_zero` (CASE C —
`kpi_profit is None`, ô hiện `—`, `"0" not in text`),
`test_I_a_real_zero_kpi_profit_is_distinct_from_unknown` (CASE D — `kpi=0`
AUTO hiện `"0"`, `missing=False`, phân biệt rõ KHÔNG BIẾT). Tầng trình bày
canh thêm bằng `tests/test_sales_presentation.py::test_the_product_summary_
of_zero_known_kpi_lines_is_a_dash_not_zero`. Web-level:
`test_a_partial_coverage_item_never_renders_zero_profit` xác nhận `"0đ" not
in html`.

#### CHECK-PRA005-07 — Split `FTKB50ZVMV` (hoặc tương đương) được bảo toàn (Acceptance G)
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Yêu cầu:
Trên fixture golden `period_2026_01`, khẳng định hai chuỗi `Điều hoà Daikin
FTKB50ZVMV` và `Máy lạnh Daikin Inverter 2 HP FTKB50ZVMV` xuất hiện thành
HAI dòng riêng trong bảng, KHÔNG bị gộp.

Executed By:
Session S108 — PRA-005 MAJOR Implementation (Claude Code)

Timestamp:
2026-09-03

Evidence:
S108. `tests/test_product_queries.py::test_the_daikin_ftkb50zvmv_split_
survives_untouched` — PASS trên oracle THẬT, đo lại đúng chính tả fixture
(`'Điều hoà Daikin  FTKB50ZVMV'` — hai khoảng trắng, và `'Máy lạnh Daikin
Inverter 2 HP FTKB50ZVMV'`): SL 7/113.750.000 và SL 1/16.250.000, HAI dòng
riêng. `tests/test_web_product_view.py::test_the_daikin_ftkb50zvmv_split_
shows_as_two_separate_rows` xác nhận trên HTML thật của `/san-pham`. Test
không hardcode xử lý riêng cho FTKB50ZVMV — nó chứng minh hành vi GENERIC
của `product_key` (đối chứng thêm: `test_a_model_code_shared_by_two_real_
different_skus_is_not_merged`, ca `TD-H80SEV(SK)`/`(WK)`).

#### CHECK-PRA005-08 — Dòng dịch vụ/phí vẫn nằm trong bảng (Acceptance H)
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Yêu cầu:
Trên fixture golden, khẳng định các mô tả dịch vụ/phí đo được ở Discovery
(S105 §13) vẫn xuất hiện trong bảng kết quả, KHÔNG bị lọc bởi bất kỳ
heuristic nào (kể cả `is_non_product_line()`).

Executed By:
Session S108 — PRA-005 MAJOR Implementation (Claude Code)

Timestamp:
2026-09-03

Evidence:
S108. `tests/test_product_queries.py::test_J_the_golden_periods_real_
service_lines_still_reach_the_table` — PASS, xác nhận "Chi phí vận chuyển"
(SL 19/4.683.750), "Giá treo Tivi" (SL 15/2.150.000), "Chi phí lắp đặt" (SL
2/200.000) đều còn trong bảng — khớp EXACT S105 §13. `grep is_non_product_
line` trên `sales_queries.py` (delta) = KHÔNG khớp
(`test_product_totals_module_never_calls_the_non_product_line_heuristic`).
`test_J_a_service_looking_line_is_not_filtered_out` (đơn vị) +
`tests/test_web_product_view.py::test_service_fee_like_lines_are_still_on_
the_page` (HTML thật) cùng PASS.

#### CHECK-PRA005-09 — Mặc định sắp theo doanh thu giảm dần (Acceptance I)
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Yêu cầu:
Test khẳng định thứ tự mặc định của `product_totals()` là `ORDER BY
SUM(total_sales) DESC`, không tham số nào khác đảo ngược mặc định.

Executed By:
Session S108 — PRA-005 MAJOR Implementation (Claude Code)

Timestamp:
2026-09-03

Evidence:
S108. `tests/test_product_queries.py::test_K_default_order_is_revenue_
descending` + `::test_K_equal_revenue_groups_sort_by_a_stable_key_not_load_
order` (tie-breaker `product_key`, hai lần gọi cho cùng kết quả) — PASS.
`product_totals()` không nhận tham số sort nào khác — mặc định là ORDER BY
DUY NHẤT. Web-level: `tests/test_web_product_view.py::test_the_default_
table_order_is_revenue_descending` xác nhận trên HTML thật (226 dòng, mặt
hàng #1 KHÔNG phải dòng dịch vụ/phí).

#### CHECK-PRA005-10 — Không hiển thị PP tổng hợp cấp mặt hàng; nhãn đúng (Acceptance J)
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Yêu cầu:
Grep/kiểm template `san_pham.html` xác nhận không cột/ô nào render
`kpi_purchase_price`/`accounting_purchase_price` ở cấp tổng hợp. Khẳng định
nhãn ô tóm tắt là "Số mặt hàng trên chứng từ" (KHÔNG "Số sản phẩm"), nhãn
cột đầu bảng có chữ "Mặt hàng" (KHÔNG "Sản phẩm chuẩn"/"SKU chuẩn"), và câu
disclosure bắt buộc (mục 5) xuất hiện nguyên văn trên trang.

Executed By:
Session S108 — PRA-005 MAJOR Implementation (Claude Code)

Timestamp:
2026-09-03

Evidence:
S108. `tests/test_product_queries.py`: `test_N_product_totals_never_selects_
a_purchase_price_column` (AST trên hàm `product_totals()` — không
`kpi_purchase_price`/`accounting_purchase_price`), `test_N_the_product_
template_never_renders_an_aggregate_purchase_price` (grep template),
`test_N_the_summary_label_is_not_so_san_pham`. Web-level: `tests/test_web_
product_view.py::test_the_required_disclosure_note_appears_verbatim` (nguyên
văn `PRODUCT_GROUPING_NOTE` trên HTML thật),
`::test_the_summary_item_count_label_is_not_so_san_pham`, `::test_the_table_
has_exactly_the_five_contract_columns` (`["Mặt hàng", "Số lượng", "Số đơn",
"Doanh thu", "LN KPI"]`), `::test_no_forbidden_column_appears_on_the_page`.
Tất cả PASS.

#### CHECK-PRA005-11 — Hàng rào PII cấu trúc, tái dụng EAC-9
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Yêu cầu:
Xác nhận `sales_queries.py` (delta) không import/chọn `imei`, `note_raw`,
`employee_raw`, `customer`, `phone`, `address`. Xác nhận KHÔNG file nào
trong touch area sửa `app/web/analytics_queries.py`
(`git diff --stat <BASE_SHA> -- app/web/analytics_queries.py` = rỗng) và
`tests/test_analytics_queries.py` vẫn PASS nguyên vẹn.

Executed By:
Session S108 — PRA-005 MAJOR Implementation (Claude Code)

Timestamp:
2026-09-03

Evidence:
S108. `tests/test_product_queries.py::test_product_totals_selects_no_
personal_data_column` — PASS (grep `.c.<column>` cho cả sáu trường). Lệnh
thật, phiên này:
```
git diff 4e06515895814d8fff41580dc0f3c64da464ac83 -- app/web/analytics_queries.py
  → rỗng (0 dòng)
git diff 4e06515895814d8fff41580dc0f3c64da464ac83 -- app/web/analytics_presentation.py
  → rỗng (0 dòng)
git diff 4e06515895814d8fff41580dc0f3c64da464ac83 -- tests/test_analytics_queries.py
  → rỗng (0 dòng)
python -m pytest tests/test_analytics_queries.py tests/test_analytics_presentation.py \
  tests/test_web_pipeline_analytics.py -q
  → tất cả PASS, không đổi (chạy trong S108)
```

#### CHECK-PRA005-12 — Hiệu năng đo trên đường query thật
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Yêu cầu:
Đo thời gian `product_totals()` trên PostgreSQL (hoặc engine test tương
đương môi trường CI) với quy mô dữ liệu tỉ lệ thuận thực tế hiện hành; ghi
lại con số đo được KHÔNG dùng làm SLA, chỉ để xác nhận không có blocker
thuật toán (mục 23).

Executed By:
Session S108 — PRA-005 MAJOR Implementation (Claude Code)

Timestamp:
2026-09-03

Evidence:
S108. Đo THẬT trên PostgreSQL 16 (local server, sqlalchemy 2.0 + psycopg3 —
KHÔNG phải SQLite). Dataset: 12.000 dòng tổng hợp, 2.491 nhóm mặt hàng —
cùng hình dạng Discovery S105 §35. Kết quả 3 lần chạy: 81,7 ms / 65,4 ms /
102,8 ms. Đối chiếu: PRA-003 đã nghiệm thu 64 ms cho cùng tầng truy vấn trên
PostgreSQL production thật, cùng quy mô — không blocker thuật toán. Số đo
KHÔNG freeze thành SLA (mục 21/23). Database/user scratch đã xoá sau đo,
không để lại state.

#### CHECK-PRA005-13 — Drill-down dẫn về đúng sự thật PRA-004 (Acceptance L)
Priority:
RECOMMENDED

Status:
NOT_APPLICABLE

Evidence Level:
(không áp dụng — DEFERRED)

Yêu cầu:
NẾU drill-down được triển khai trong ngân sách: test mở một mặt hàng → một
đơn góp phần → xác nhận `/ban-hang/<order_key>` hiện đúng đơn đó với con số
KHÔNG đổi so với `TASK-PRA-004`. NẾU DEFER (mục 18 cho phép): ghi rõ lý do
và RE-TRIGGER CONDITION, check này chuyển `NOT_APPLICABLE` có giải thích —
không chặn task pass vì là RECOMMENDED.

Evidence:
S108. `DEFERRED_WITHIN_CONTRACT` — mục 18 cho phép tường minh. Đường tối
thiểu (`product_lines()` lọc theo `product_key` + route `/san-pham/
<product_key>` + template dòng-chi-tiết mới) đòi một truy vấn MỚI, một route
MỚI, một template MỚI — vượt phần ngân sách còn lại nếu cộng cùng vertical
chính REQUIRED, trong khi check này là RECOMMENDED. Xem S108 §"Quyết Định
Triển Khai Đáng Ghi Lại" mục 2. RE-TRIGGER CONDITION: Owner yêu cầu xem trực
tiếp các dòng bán của một mặt hàng từ trang `/san-pham` — mở slice/task
riêng, KHÔNG mở rộng V1 âm thầm.

#### CHECK-PRA005-14 — Independent Review (E2)
Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
(chưa có — mục tiêu E2)

Yêu cầu:
Theo `governance/templates/E2_INDEPENDENT_REVIEW_TEMPLATE.md`. Ghi tại
`docs/reviews/TASK-PRA-005-INDEPENDENT-REVIEW-RECORD.md`.

#### CHECK-PRA005-15 — Owner Production Acceptance
Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
(chưa có — mục tiêu E1, thực hiện bởi Owner trên hệ thống thật)

Yêu cầu:
Bảy bước mục 27 (A–G tối thiểu; H–L khi áp dụng) thực hiện trực tiếp trên
`reports.tinphatcrm.com` bởi Owner, KHÔNG phải ảnh chụp/fixture.

---

## Review Budget

```
root_task              : TASK-PRA-005
effective_risk         : MEDIUM
repair_cycles_allowed  : 1
repair_cycles_used     : 0
repair_cycles_remaining: 1
Independent Review     : BẮT BUỘC (E2, CHECK-PRA005-14)
```

MEDIUM chấm theo failure path (`governance/core/V4_1_POLICY_FREEZE.md` §4)
— lý do đầy đủ ở Metadata → Blast Radius.

**Finding KHÔNG tự động trở thành repair work.** Chỉ mở repair cycle khi
finding đe doạ TRỰC TIẾP một trong bốn điều:

1. tính trung thực/reconciliation của tổng doanh thu-số lượng-LN KPI cấp
   mặt hàng so với phân tích đã accepted (mục 27 A-F);
2. an toàn `NULL`/coverage (mục 27 K, EAC-2/EAC-3);
3. bảo toàn OD-PRA005-01/OD-PRA005-02 (KHÔNG âm thầm gộp/lọc);
4. ranh giới PII (EAC-9, mục 18).

Finding ngoài bốn nhóm đó: `HARDENING` kèm RE-TRIGGER CONDITION cụ thể
(V4.1 §7) hoặc `OUT_OF_SCOPE`. Vượt 1 cycle ⟹ `OWNER_EXTENSION REQUIRED`;
KHÔNG tách sub-unit, KHÔNG đổi tên task, KHÔNG mở nhánh mới để reset ngân
sách (V4.1 §2).

---

## Contract Exit Gate — kết quả phiên này

```
1.  Raw-description grouping                 PASS — mục 3
2.  NOT canonical Product Identity            PASS — mục 3, 6
3.  All-line inclusion                        PASS — mục 4, 7
4.  Four summary metrics                      PASS — mục 8
5.  Five table columns                        PASS — mục 9
6.  KPI known-value + coverage semantics      PASS — mục 13, 14
7.  NULL != 0                                 PASS — mục 8.4, 13
8.  Product-level PP exclusion                PASS — mục 15
9.  Identity limitation                       PASS — mục 6
10. Default revenue sort                      PASS — mục 17
11. Real-data acceptance                      PASS — mục 27
12. No schema/new authority/Tracking change   PASS — mục 21, 22
13. Bounded implementation scope              PASS — mục 24, 25

CONTRACT_EXIT_GATE = PASS
```
