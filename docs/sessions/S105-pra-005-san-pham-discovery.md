# S105 — TASK-PRA-005 Session 1: Discovery "SẢN PHẨM"

Ngày: 2026-09-03
Task Mode: SPIKE / DISCOVERY (business-first, chuẩn bị cho MAJOR)
Loại phiên: docs-only — KHÔNG viết production code, KHÔNG sửa schema, KHÔNG
migration, KHÔNG chạm Tracking.

---

## (1) DISCOVERY_RESULT

```text
SESSION                   = S105 — PRA-005 Discovery SẢN PHẨM (docs-only)
DISCOVERY_RESULT          = PASS
PRODUCTION_CODE_DELTA     = 0 dòng
SCHEMA_CHANGED            = NO    MIGRATION_ADDED = NO    INDEX_ADDED = NO
DEPENDENCY_ADDED          = NO    CONFIG_CHANGED  = NO
TRACKING_CHANGED          = NO    INFRASTRUCTURE_CHANGED = NO
PRA-001/002/003/004_CHANGED = NO
BLOCKING_FINDINGS         = 0
OWNER_DECISIONS_REQUIRED  = 2  (OD-PRA005-1 khoá gộp · OD-PRA005-2 dòng dịch vụ)
SCOPE_DRIFT               = NO
NEXT_VERTICAL_ACTION      = PRA-005 CONTRACT FREEZE
```

Discovery PASS **không** có nghĩa "mọi thứ đều sạch". Nó có nghĩa: khoá gộp đã
được truy vết đến đúng dòng mã sinh ra nó, chế độ hỏng của khoá đó đã được ĐO
trên dữ liệu sản phẩm thật (không suy đoán), và cách trình bày trung thực cho
chế độ hỏng ấy đã có phương án — chứ không phải nó không tồn tại.

## (2) CANONICAL

```text
DEFAULT_BRANCH (origin HEAD) = claude/extract-upload-repo-gq2ws4
EXPECTED_HEAD                = 4dfe4b2525ec9496be27b3856e9b3698588dc22a
git rev-parse origin/claude/extract-upload-repo-gq2ws4
                             = 4dfe4b2525ec9496be27b3856e9b3698588dc22a
KẾT LUẬN                     = CANONICAL_NOT_MOVED — khớp CHÍNH XÁC EXPECTED
LOCAL HEAD (đầu phiên)       = 4dfe4b2525ec9496be27b3856e9b3698588dc22a
WORKTREE                     = CLEAN
SESSION_BRANCH               = claude/pra-005-discovery-dsryx5
```

`scripts/branch_authority_check.sh` đầu phiên: `DEFAULT_TIP` = `HEAD_SHA` =
`4dfe4b2…`, `WORKTREE = CLEAN`. Script dừng ở `BRANCH AUTHORITY UNRESOLVED` vì
nhánh phiên chưa có upstream (chưa push) — đây là trạng thái ĐÚNG của một
nhánh mới, không phải canonical moved.

## (3) ROADMAP_STATE

```text
PRA-000 = DONE   PRA-001 = DONE   PRA-002 = DONE   PRA-003 = DONE
PRA-004 = DONE   (S104 — Owner Production Acceptance, 14/14 check PASS)
KPI-FIRST UI                   = DONE
PRICE AUTHORITY NORMALIZATION  = DONE (DEC-172), fresh-processing visual = PASS
PRA-005                        = NOT STARTED → Discovery (phiên này)
```

Phiên này KHÔNG mở lại task nào ở trên, KHÔNG tạo PRA-005B/PRA-006, KHÔNG sửa
roadmap.

## (4) BUSINESS_INTENT_INTERPRETATION

Câu hỏi nghiệp vụ gốc của Owner ("sản phẩm nào bán tốt / tạo doanh thu / tạo
LN KPI") quy về đúng một phép toán: **phân hoạch lại CÙNG tập dòng bán hiện
hành theo chiều sản phẩm, thay vì theo chiều nhân viên (PRA-003) hay theo
chiều đơn (PRA-004).**

Đây là điểm mạnh nhất của vertical này: bảy chỉ tiêu, ngữ nghĩa coverage,
quy tắc `NULL ≠ 0` và tầng trình bày đều ĐÃ được nghiệm thu trên hai chiều
khác. PRA-005 không cần phát minh chỉ tiêu mới — nó cần một `GROUP BY` khác.

Rủi ro thật của vertical này KHÔNG nằm ở phép cộng. Nó nằm ở câu hỏi
**"một sản phẩm là gì"** — chiều nhân viên có `employee_normalized` (có
`EmployeeMapper` làm authority), chiều đơn có `order_key` (khoá nghiệp vụ
thật). Chiều sản phẩm KHÔNG có một khoá tương đương đã được nghiệm thu.

## (5) OWNER_FACTS

| Sự kiện | Phân loại | Nguồn |
|---|---|---|
| Giá mua tham chiếu = Tracking PP tại ngày bán, là authority DUY NHẤT | `OWNER_DECISION` | DEC-172 |
| Lợi nhuận quản trị = LN KPI; không có LN kế toán trên UI quản lý | `OWNER_DECISION` | KPI-FIRST UI |
| Tracking = Product Identity Authority | `OWNER_DECISION` | DEC-103/ADR-106 |
| `NULL ≠ 0` — thiếu dữ liệu hiện `—`, không bao giờ `0` | `OWNER_DECISION` | PRA-003 D2/P4 |
| Công cụ nội bộ 2–3 người xem | `OWNER_FACT` | brief PRA-005 §20 |
| 13 mô tả kế toán thật chưa classify, đều "sản phẩm hiếm, không nhập lại" | `OWNER_FACT` | S068 follow-up audit |

Mười câu hỏi A–J trong brief là **HYPOTHESES**, phiên này KHÔNG freeze chúng
thành yêu cầu.

## (6) EXISTING_ACCEPTED_CONTRACTS

Đây là các hợp đồng ĐÃ nghiệm thu mà PRA-005 phải tuân theo, không được diễn
giải lại:

1. **EAC-1 — Bảy chỉ tiêu + coverage.** `analytics_queries._metrics()`
   (`app/web/analytics_queries.py:56`). LN KPI chỉ cộng dòng `AUTO`;
   `kpi_lines` là tử số coverage; mẫu số là `lines`.
2. **EAC-2 — `coverage()` viết dạng `N / M dòng`, cố ý KHÔNG dạng %.**
   `app/web/analytics_presentation.py:75`.
3. **EAC-3 — `profit()` không có đường nào render lợi nhuận thiếu coverage.**
   `analytics_presentation.py:87` (quy tắc P4).
4. **EAC-4 — `NULL` luôn thành `—`.** `money()`/`count()`.
5. **EAC-5 (QUAN TRỌNG NHẤT VỚI PRA-005) — D3/N.7: nhãn ô số lượng là
   "Tổng số lượng" và KHÔNG được gọi là "Số lượng sản phẩm"/"Tổng số SP", vì
   *chưa có quy tắc phân loại product-line có thẩm quyền*.** Con số đếm MỌI
   dòng, kể cả phí vận chuyển / công lắp đặt / chiết khấu.
   `analytics_presentation.py:41-48`.
6. **EAC-6 — `_period()` luôn kèm `sale_date IS NOT NULL`;
   `undated_lines()` là chỗ DUY NHẤT phơi dòng thiếu ngày.**
7. **EAC-7 — Từ vựng nội bộ (`price_source`, `kpi_purchase_provenance`,
   `composition_rule`) BỊ CẤM khỏi UI quản lý.** `sales_queries.py:187-195`.
8. **EAC-8 — `is_non_product_line()` là heuristic GIẢM NHIỄU validation, KHÔNG
   phải phân loại sản phẩm, và "must never be tuned to reproduce a historical
   count".** `app/modules/validation/rules.py:52-69`. Nó KHÔNG được persist.

## (7) INFERENCES_NOT_FROZEN

Các suy luận sau là `INFERENCE`, phiên này KHÔNG nâng thành yêu cầu:

- Owner muốn ranking chứ không chỉ bảng sort được (câu I chưa trả lời).
- "Bán tốt" nghĩa là số lượng (có thể là doanh thu, hoặc LN KPI).
- Drill-down sản phẩm → đơn là cần thiết ngay ở slice đầu (câu H).
- Cần trend theo thời gian ở slice đầu (câu F).
- Cần brand/category/vendor (câu J).

## (8) PRODUCT_AGGREGATION_KEY

**Khoá mà PRA-005 có thể gộp HÔM NAY:**

```text
PRODUCT_AGGREGATION_KEY = order_line_current.product_key
                        = sha256( NFC(product_raw).strip() )
```

Nguồn sự thật: `app/history/keys.py:70`, hợp đồng khoá TASK-PRA-002 §5.1 /
DEC-166 / DEC-171. Cố ý **KHÔNG** casefold, **KHÔNG** bỏ dấu (D9 DEFER).

Kết luận thẳng: `product_key` **KHÔNG PHẢI** product identity nghiệp vụ. Nó là
**khoá dòng** — thành phần thứ hai của `ORDER_LINE_KEY = (order_key,
product_key, occurrence_index)`, sinh ra để hai dòng cùng tên hàng trong một
đơn không ghi đè nhau. Dùng nó làm chiều sản phẩm là **tái dụng một khoá kỹ
thuật cho một mục đích nghiệp vụ** — hợp lệ, nhưng phải gọi đúng tên.

**Vì sao KHÔNG dùng `canonical_product_code` làm khoá gộp** (dù nó LÀ
authority): đo được, không suy đoán —

```text
Đường production trên fixture golden period_2026_01 (E1, phiên này):
  records                          = 349
  identity NOT None                =   0
  canonical_product_code NOT None  =   0
  reason                           = IDENTITY_SOURCES_UNAVAILABLE (349/349)
```

`canonical_product_code` chỉ được điền khi có Tracking capture tại thời điểm
xử lý. Capture Tracking KHÔNG (và KHÔNG NÊN) nằm trong repo. Trên production
nó ĐƯỢC điền cho dòng đã resolve, nhưng bằng chứng thật S068 cho thấy nó
**không phủ hết**: `identity unresolved 31`, `PP pending 13` trên cohort thật
đã accepted. Một khoá gộp `NULL` trên một phần đáng kể số dòng không thể là
khoá phân hoạch của một bảng "toàn bộ sản phẩm trong kỳ".

**`COALESCE(canonical_product_code, product_key)` = UNSAFE, KHÔNG khuyến
nghị.** Cùng một sản phẩm sẽ nhảy giữa hai bucket khác nhau tuỳ theo capture
lần chạy đó có resolve được identity hay không — bảng sẽ đổi hình dạng giữa
hai kỳ mà không có sự kiện nghiệp vụ nào xảy ra.

## (9) PRODUCT_IDENTITY_SAFETY

```text
PRODUCT_IDENTITY_SAFETY = PASS_WITH_MEASURED_LIMITATION
```

Hai chiều rủi ro, đo riêng:

**MERGE (gộp nhầm hai sản phẩm khác nhau thành một) = KHÔNG XẢY RA.**
`product_key` là hàm thuần của chuỗi tên hàng đã NFC+strip, phân biệt hoa
thường và dấu. Hai sản phẩm khác nhau chỉ bị gộp nếu kế toán gõ **y hệt** một
chuỗi cho cả hai. Đây là chiều rủi ro NGUY HIỂM hơn (nó tạo ra một khẳng định
sai), và nó bị chặn theo cấu trúc.

**SPLIT (một sản phẩm tách thành nhiều dòng) = CÓ, ĐÃ ĐO, CÓ VÍ DỤ THẬT.**

Phép đo trên tên hàng THẬT (fixture golden giữ nguyên văn `product_raw` —
`tests/fixtures/golden/anonymize.py` liệt kê nó là trường business logic ĐỌC,
nên nó không bị thay surrogate):

```text
period_2026_01 : 351 dòng · 226 chuỗi tên hàng phân biệt · 166 chuỗi chỉ 1 dòng
period_2026_06 : 180 dòng · 135 chuỗi tên hàng phân biệt · 108 chuỗi chỉ 1 dòng
Gộp hoa-thường + gộp khoảng trắng : delta = 0 trên CẢ HAI kỳ
Mã model xuất hiện trên >1 chuỗi  : 3 (01.2026) · 0 (06.2026)
```

Ba trường hợp mã model nằm trên nhiều chuỗi, và cách đọc từng cái:

| Mã | Các chuỗi | Đọc đúng |
|---|---|---|
| `FTKB50ZVMV` | `Điều hoà Daikin  FTKB50ZVMV` · `Máy lạnh Daikin Inverter 2 HP FTKB50ZVMV` | **SPLIT THẬT** — cùng một máy, hai cách gọi ("điều hoà"/"máy lạnh") + một dấu cách kép |
| `LC-70` | `Tủ Mát Alaska LC-70` · `Tủ Mát Alaska LC-70 trắng` | **KHÔNG CHẮC** — có thể là biến thể màu, có thể là cùng một máy |
| `TD-H80SEV` | `…TD-H80SEV(SK)` · `…TD-H80SEV(WK)` | **TÁCH ĐÚNG** — SK/WK là hai SKU màu khác nhau, gộp lại mới là SAI |

Cột thứ ba chính là bằng chứng vì sao **fuzzy/substring/prefix matching bị
cấm làm authority**: một quy tắc "gộp theo mã model" sẽ sửa đúng dòng 1 và
làm HỎNG dòng 3.

**Độ lớn của SPLIT — đây là phần quan trọng, không phải chi tiết kỹ thuật:**

```text
'Điều hoà Daikin  FTKB50ZVMV'                  qty 7   doanh thu 113.750.000  (1 dòng)
'Máy lạnh Daikin Inverter 2 HP FTKB50ZVMV'     qty 1   doanh thu  16.300.000  (1 dòng)
                                        NẾU GỘP: qty 8   doanh thu 130.050.000
```

Gộp lại, đây là sản phẩm **doanh thu #1** của kỳ. Tách ra, nó hiện thành #2 và
một dòng nhỏ. Với đúng câu hỏi B của Owner ("sản phẩm nào tạo doanh thu lớn"),
sai lệch này là **có ý nghĩa nghiệp vụ**, không phải nhiễu làm tròn.

Tỉ lệ đo được: 1 SPLIT chắc chắn / 226 chuỗi (~0,4%), 1 nữa không chắc.

## (10) UNRESOLVED_PRODUCT_TREATMENT_OPTIONS

Vì khoá gộp là `product_key` (luôn có giá trị, không bao giờ `NULL`), **không
tồn tại "bucket chưa nhận diện"** theo nghĩa PRA-005 phải xử lý — mọi dòng đều
vào đúng một bucket. Đây là hệ quả trực tiếp của lựa chọn khoá ở §8 và là lý
do nó KHÔNG phải blocking finding.

Điều cần quyết định không phải "để dòng unresolved ở đâu", mà **có phơi trạng
thái identity ra bảng hay không**:

- **Phương án U1 (khuyến nghị) — không thêm cột identity.** Bảng gộp theo tên
  hàng trên chứng từ; cột "Trạng thái dữ liệu" đã có sẵn ngữ nghĩa qua
  coverage LN KPI. Không thêm từ vựng nội bộ (EAC-7).
- **Phương án U2 — thêm cột "đã nhận diện Tracking" (có/không).** Trung thực
  hơn về identity nhưng phơi một khái niệm nội bộ ra UI quản lý và va chạm
  EAC-7; giá trị nghiệp vụ chưa được chứng minh.
- **Phương án U3 — tách riêng bảng "sản phẩm chưa nhận diện".** BÁC BỎ: nó
  ngụ ý rằng phần còn lại ĐÃ nhận diện chuẩn, trong khi bảng đang gộp theo
  chuỗi tên hàng chứ không theo identity. Đây sẽ là một khẳng định sai.

## (11) PERSISTED_FIELD_MATRIX

Đọc từ `tools/db/schema.py` (`order_line_current` +
`order_line_source_version` + `order_line_result_version`):

| Trường PRA-005 cần | Cột persisted | Trạng thái |
|---|---|---|
| Khoá gộp sản phẩm | `order_line_current.product_key` | **AVAILABLE** (là 1 phần PK) |
| Tên hiển thị sản phẩm | `order_line_source_version.product_raw` | **AVAILABLE** (hàng rào PII: xem §21) |
| Ngày bán | `order_line_current.sale_date` | **AVAILABLE** (có index) |
| Nhân viên | `order_line_result_version.employee_normalized` | **AVAILABLE** |
| Số đơn | `order_line_current.order_key` | **AVAILABLE** |
| Số lượng | `order_line_source_version.quantity` | **AVAILABLE** |
| Đơn giá bán | `order_line_source_version.sell_price` | **AVAILABLE** |
| Chiết khấu | `order_line_source_version.discount` | **AVAILABLE** |
| Doanh thu dòng | `order_line_result_version.total_sales` | **AVAILABLE** |
| Giá mua tham chiếu | `order_line_result_version.kpi_purchase_price` | **AVAILABLE** (cấp dòng — xem §18) |
| LN KPI | `order_line_result_version.eligible_kpi_profit` | **AVAILABLE** |
| AUTO/PENDING | `order_line_result_version.status` | **AVAILABLE** |
| Lý do kiểm tra | `order_line_result_version.pending_reasons_json` | **AVAILABLE** |
| Snapshot/version nguồn | `snapshot_id` / `current_*_version_id` | **AVAILABLE** |
| Identity chuẩn | `order_line_result_version.canonical_product_code` | **PARTIAL** — `NULL` khi identity chưa resolve (đo: 0/349 trong repo; thật: unresolved 31 ở cohort S068) |
| Namespace identity | `order_line_result_version.identity_namespace` | **PARTIAL** (cùng lý do) |
| Brand | — | **NOT_AVAILABLE** |
| Category | `product_group_final` | **NOT_AVAILABLE trên thực tế** — xem §23 |
| Vendor / NCC | — | **NOT_AVAILABLE** |

**Kết luận: PRA-005 KHÔNG cần thêm một cột nào.** `SCHEMA_REQUIRED = NO`.

## (12) EXISTING_QUERY_CAPABILITIES

`app/web/analytics_queries.py` đã có sẵn, dùng lại NGUYÊN VẸN:

- `_metrics()` — 7 chỉ tiêu, không coalesce `0` (EAC-1).
- `_joined()` — `order_line_current` nối ĐÚNG version hiện hành; no-double-count
  là tính chất CẤU TRÚC BẢNG, không phải của `DISTINCT`.
- `_period()` — điều kiện kỳ + `sale_date IS NOT NULL`.
- `_shaped()` — ép `int` cho ô ĐẾM, giữ `None` cho ô TIỀN.
- `employee_totals()` — **đây chính là khuôn mẫu cấu trúc của
  `product_totals()`**: `select(<chiều>, *_metrics()).select_from(_joined())`
  → `.group_by(<chiều>)` → `.order_by(SUM(total_sales).desc())`.

`app/web/sales_queries.py` đã có:
- `order_detail()` + route `/ban-hang/<order_key>` — đích drill-down.
- `_line_columns()` — mẫu cột cấp dòng, đã qua hàng rào PII hẹp.

Nói thẳng: `product_totals()` là `employee_totals()` với `GROUP BY` khác và
thêm một `MIN(product_raw)` làm nhãn hiển thị. Đó là toàn bộ phần SQL mới.

## (13) REAL_DATA_PROFILE

Đo trong phiên này (E1). Nguồn: fixture golden — `product_raw` giữ NGUYÊN VĂN
production; PII đã xoá/surrogate.

```text
                                    period_2026_01   period_2026_06
số dòng bán                                    351              180
chuỗi tên hàng phân biệt (= product_key)       226              135
chuỗi chỉ xuất hiện 1 dòng                     166              108
tên hàng rỗng                                    0                0
gộp hoa-thường+khoảng trắng (delta)              0                0
mã model trên >1 chuỗi (ứng viên SPLIT)          3                0
dòng dịch vụ (heuristic non_product_lines)   22 (6,3%)      14 (7,8%)
  — % doanh thu của các dòng đó               0,14%            0,25%
```

Coverage giá / KPI **KHÔNG đo được trong repo**, và điều này phải nói thẳng
thay vì bịa:

```text
period_2026_01 : price_source = {OWNER_MANUAL_LEGACY_CONFIRMATION: 2, Pending: 349}
                 kpi_purchase_price NOT NULL   = 2 / 351
                 eligible_kpi_profit NOT NULL  = 2 / 351
period_2026_06 : price_source = {Pending: 180}   → 0 / 180
```

Con số `2/351` tái lập ĐÚNG `FIND-PRA003-01` đã accepted. Lý do coverage ≈ 0
là capture Tracking không nằm trong repo (đúng thiết kế), KHÔNG phải lỗi.

Bằng chứng coverage THẬT chỉ có từ production, và đã có sẵn, không cần đo lại:
`40 đơn · 61 dòng · 15 AUTO · 25 CẦN KIỂM TRA` (Owner quan sát, 09/2026);
cohort S068: `58 đơn · 83 dòng · 22 AUTO · 36 Review`, `identity unresolved 31`,
`PP pending 13`, 13 mô tả chưa classify.

## (14) QUANTITY_SEMANTICS

`SUM(order_line_source_version.quantity)` — tái dụng nguyên vẹn.

**Ràng buộc EAC-5 áp dụng NGUYÊN VẸN cho PRA-005 và nó chặn một ô mà brief
đề xuất.** Nhãn phải là "Tổng số lượng", KHÔNG được là "Số lượng sản phẩm".

Và ô tóm tắt **"Số sản phẩm"** mà brief §17 đề xuất là **KHÔNG hợp lệ như đã
viết**: nó đếm số `product_key` phân biệt, trong đó có "Chi phí vận chuyển",
"Chi phí lắp đặt", "Chênh VAT", "Phụ Phí". Gọi con số đó là "số sản phẩm"
chính là phát minh ra quy tắc phân loại product-line mà EAC-5 nói là chưa
tồn tại. Nhãn trung thực: **"Số mặt hàng trên chứng từ"**.

## (15) REVENUE_SEMANTICS

`SUM(order_line_result_version.total_sales)` — ĐỌC THẲNG giá trị đã lưu,
KHÔNG tính lại từ `(số lượng × đơn giá − chiết khấu)`. Tính lại là dựng nguồn
sự thật thứ hai cạnh nguồn đã nghiệm thu (`sales_queries.py:196-201`).

`GROUP BY product_key` là một **phân hoạch** của cùng tập dòng, nên doanh thu
cộng qua các dòng sản phẩm bằng ĐÚNG tổng kỳ. Cột "Số đơn" thì KHÔNG cộng
được (một đơn nhiều sản phẩm được đếm ở nhiều dòng) — giống hệt cảnh báo đã có
cho chiều nhân viên (`ORDER_COLUMN_NOTE`), và trang phải nói rõ điều đó.

## (16) KPI_PROFIT_SEMANTICS

```text
KPI_PROFIT_SEMANTICS = SUM_KNOWN_VALUES_WITH_EXPLICIT_COVERAGE
```

Tái dụng CHÍNH XÁC `_metrics()`:
`SUM(CASE WHEN status = 'AUTO' THEN eligible_kpi_profit END)`.

Hai điểm phải giữ nguyên, không được "cải tiến":
- Dòng `PENDING` có `eligible_kpi_profit` khác `NULL` **vẫn KHÔNG vào tổng**
  (D1/P1). Đây là quyết định đã nghiệm thu, không phải bug.
- Tập cộng rỗng ⟹ `None` ⟹ hiển thị `—`. KHÔNG BAO GIỜ `0`.

## (17) KPI_COVERAGE_SEMANTICS

Tái dụng nguyên vẹn: tử số `kpi_lines` = số dòng `AUTO`; mẫu số = `lines` của
chính dòng sản phẩm đó; định dạng `coverage()` = `"N / M dòng"`, cố ý không
phần trăm (EAC-2).

Ví dụ brief §13 (12 dòng, 9 có KPI) hiển thị đúng là:
`LN KPI 4.200.000` · `9 / 12 dòng`.

`profit()` (EAC-3) đảm bảo theo CẤU TRÚC rằng không có đường nào render con số
lợi nhuận mà thiếu mẫu số — PRA-005 chỉ cần gọi nó, không cần cơ chế mới.

## (18) REFERENCE_PRICE_AGGREGATION_VERDICT

```text
REFERENCE_PRICE_AGGREGATION_VERDICT = DO_NOT_SHOW_AS_SINGLE_AGGREGATE
```

Bỏ cột "Giá mua tham chiếu" khỏi bảng sản phẩm. Lý do không phải thẩm mỹ:

1. PP là **PP có hiệu lực tại NGÀY BÁN** (DEC-172). Một dòng sản phẩm gộp
   nhiều ngày bán khác nhau thì "PP của sản phẩm" **không phải một đại lượng
   tồn tại** — nó là nhiều giá trị tại nhiều thời điểm.
2. `AVG` sẽ là một con số **không có giao dịch nào tương ứng**. `SUM` vô
   nghĩa. `MIN`/`MAX`/`LAST` đều là quy tắc nghiệp vụ mới chưa ai quyết.
3. Cột này chỉ đúng ở nơi nó ĐÃ đúng: **cấp dòng, trong chi tiết đơn PRA-004**
   — nơi có đúng một ngày bán và đúng một PP.

Nếu Owner sau này cần "giá mua đang áp dụng", đó là một câu hỏi khác
(point-in-time lookup), cần authority riêng — **DEFER**, không đưa vào slice
này.

## (19) TIME_DIMENSION

Ngày nghiệp vụ = `sale_date`, đã accepted, không đổi.

| Khả năng | Trạng thái | Phân loại |
|---|---|---|
| Một tháng | `available_periods()` + `month_bounds()` đã có | **CORE** |
| Toàn bộ dữ liệu | đã có (`period = None`) | **CORE** |
| Hôm nay | `_period()` nhận `date_from`/`date_to` bất kỳ — chỉ thiếu UI | **OPTIONAL** |
| Khoảng ngày tuỳ chọn | như trên; PRA-003 đã DEFER tường minh | **DEFERRED** |
| Trend theo tháng / biểu đồ | cần nhiều truy vấn + tầng chart | **DEFERRED** |

Tầng truy vấn hỗ trợ khoảng ngày tuỳ ý **mà không cần đổi schema**; chỉ bộ
chọn kỳ trên UI là bị giới hạn theo tháng (`period_options()`). Không làm
trend chỉ vì làm được (brief §14).

## (20) EMPLOYEE_DIMENSION

```text
EMPLOYEE_DIMENSION = REQUIRES_QUERY_ONLY
```

`employee_normalized` nằm cùng bảng `order_line_result_version` với các chỉ
tiêu, nên "Sản phẩm X → Ly 4, Tín Phát 3" là `GROUP BY product_key,
employee` — cùng phân hoạch, cùng bảy chỉ tiêu, KHÔNG schema, KHÔNG join mới.

Cảnh báo đã biết cần mang theo: `FIND-PRA003-03` (một
`employee_normalized` mang nhiều `employee_group` sẽ hiện thành nhiều dòng
cùng tên). Trạng thái DEFER, không mở lại ở đây.

Khuyến nghị: **KHÔNG đưa vào slice đầu.** Nó là một trục thứ hai trên cùng
một trang và làm bảng thành ma trận. Đưa vào slice sau nếu Owner xác nhận
câu hỏi E là thật.

## (21) DRILLDOWN_REUSE

```text
DRILLDOWN_REUSE = PRA004_ORDER_DETAIL
```

Đường tối thiểu, KHÔNG dựng hệ thống chi tiết thứ hai:

```text
Trang Sản phẩm
  → (1 truy vấn mới) các dòng bán của product_key trong kỳ, kèm order_key
  → link tới /ban-hang/<order_key>  (route PRA-004 ĐÃ CÓ, không sửa)
```

Truy vấn mới là `_line_columns()` của `sales_queries` lọc theo `product_key`
thay vì `order_key` — cùng hàng rào PII, cùng `_reasons()`, cùng thứ tự.

**Hàng rào PII — điểm cần nêu tường minh trong contract.** `product_raw` bị
`analytics_queries` cấm đọc (nó nằm cùng nhóm `imei`/`note_raw`/`employee_raw`,
và danh sách này được test canh bằng grep). PRA-004 đã gặp đúng vấn đề này và
giải bằng cách dựng hàng rào RIÊNG, hẹp hơn ĐÚNG một trường, trong
`sales_queries` — thay vì nới hàng rào PRA-003 (làm yếu một gate đã nghiệm
thu). **PRA-005 phải theo đúng tiền lệ đó**, không được sửa
`analytics_queries`. Đây là quyết định kiến trúc quan trọng nhất của phần
implementation.

## (22) BRAND_AUTHORITY

```text
BRAND_AUTHORITY = NOT_AVAILABLE
```

Không tồn tại cột brand ở bất kỳ bảng nào. Suy brand từ chuỗi tên hàng bị
brief §19 cấm tường minh, và §9 của tài liệu này cho thấy vì sao lệnh cấm đó
đúng: cùng một máy Daikin xuất hiện dưới "Điều hoà Daikin" và "Máy lạnh
Daikin Inverter 2 HP". **DEFER.**

## (23) CATEGORY_AUTHORITY

```text
CATEGORY_AUTHORITY = NOT_AVAILABLE
```

Có vẻ như tồn tại (`order_line_result_version.product_group_final`), nhưng
truy vết đến nguồn thì nó rỗng nghĩa: `DefaultProductGroupProvider.lookup()`
trả `None` cho MỌI dòng (`app/modules/product/product_group.py:43-48`), nên
mọi dòng rơi về `DIEN_MAY` với provenance `DEFAULT`. Docstring của chính file
đó nói rõ vì sao không có classifier tự động: *"nobody has defined which
prefixes mean GIA_DUNG. Guessing that mapping would put an invented business
rule straight into payroll."*

`product_group_final` vì vậy là **một hằng số, không phải một chiều phân
tích**. Đưa nó lên UI sẽ là hiển thị một phân loại mà không ai quyết. **DEFER**
(phụ thuộc TASK-103, chưa tồn tại).

## (24) VENDOR_AUTHORITY

```text
VENDOR_AUTHORITY = NOT_AVAILABLE
```

Không có cột vendor/NCC ở bất kỳ bảng nào. NCC là khái niệm của Tracking, và
Tracking = READ-ONLY REFERENCE. **DEFER.**

## (25) MINIMUM_PRODUCT_PAGE

Sau khi challenge từng cột như brief §17 yêu cầu:

```text
/san-pham?ky=YYYY-MM

Tóm tắt kỳ (tái dụng period_totals — KHÔNG tính lại)
  Số mặt hàng trên chứng từ   ← KHÔNG gọi là "Số sản phẩm" (EAC-5, §14)
  Tổng số lượng               ← kèm QUANTITY_NOTE đã có
  Doanh thu
  LN KPI + coverage "N / M dòng"

Bảng, mặc định sắp theo Doanh thu giảm dần
  Tên hàng trên chứng từ   ← nhãn = MIN(product_raw), KHÔNG gọi là "Sản phẩm"
  Số lượng
  Số đơn                   ← kèm ghi chú KHÔNG cộng được
  Doanh thu
  LN KPI                   ← kèm coverage của CHÍNH dòng đó
```

**Các cột bị LOẠI, kèm lý do:**

| Cột brief đề xuất | Quyết định | Lý do |
|---|---|---|
| Giá mua tham chiếu | **LOẠI** | §18 — không tồn tại như một đại lượng cấp sản phẩm |
| Coverage (cột riêng) | **LOẠI** | Đã nằm TRONG ô LN KPI qua `profit()` (EAC-3); cột riêng là lặp |
| Trạng thái dữ liệu | **LOẠI** | Coverage `N / M dòng` đã nói đúng điều đó; một cột trạng thái nữa cần một quy tắc phân loại mới chưa ai quyết |
| "Số sản phẩm" (ô tóm tắt) | **ĐỔI NHÃN** | §14 |

Ghi chú bắt buộc trên trang (một dòng, tiếng Việt): bảng gộp theo **tên hàng
ghi trên chứng từ**, nên cùng một máy được gõ hai cách sẽ hiện thành hai
dòng. Đây là §9 nói ra thành lời với Owner, thay vì giấu đi.

## (26) METRICS_RECOMMENDED

Số lượng · Số đơn · Doanh thu · LN KPI + coverage. Đúng bốn, tất cả tái dụng
`_metrics()` nguyên vẹn, không có chỉ tiêu nào mới.

## (27) METRICS_DEFERRED

Ranking/scoring, "sản phẩm bán chậm", tỉ suất lợi nhuận, trend theo tháng,
so kỳ trước theo sản phẩm, top-N, biểu đồ, brand/category/vendor, ma trận
sản phẩm × nhân viên, forecasting, gợi ý.

Ghi rõ theo brief §18: **KHÔNG** có "best product"/"high margin"/"slow
product" — mọi nhãn kiểu đó cần một công thức và một quyết định Owner chưa
tồn tại. Bảng sắp xếp được đã trả lời câu hỏi A/B/C mà không cần phát minh
một hệ chấm điểm.

## (28) OWNER_DECISIONS_REQUIRED

Đúng hai. Cả hai đều làm đổi **ý nghĩa nghiệp vụ** của con số Owner đọc, nên
không được tự quyết.

**OD-PRA005-1 — Bảng sản phẩm gộp theo cái gì?**

| Phương án | Hệ quả |
|---|---|
| **A (khuyến nghị)** — gộp theo tên hàng trên chứng từ (`product_key`) | Mọi dòng đều được tính; không bao giờ gộp nhầm hai sản phẩm; ~0,4% chuỗi bị tách (đo được, có ví dụ 130 triệu ở §9); trang phải NÓI RÕ điều này |
| B — chỉ gộp theo identity Tracking đã resolve | Đúng nghĩa "sản phẩm" hơn, nhưng **bỏ sót** dòng chưa resolve (thật: 31/83 ở cohort S068) → bảng không còn là bức tranh đầy đủ của kỳ |
| C — hybrid `COALESCE` | **KHÔNG khuyến nghị** — cùng một sản phẩm nhảy bucket giữa các kỳ tuỳ theo capture (§8) |

**OD-PRA005-2 — Dòng dịch vụ (vận chuyển, lắp đặt, chênh VAT, phụ phí) có
nằm trong bảng sản phẩm không?**

Đo được: 6,3% / 7,8% số dòng, nhưng chỉ 0,14% / 0,25% doanh thu. Chúng chiếm
**3 vị trí đầu bảng khi sắp theo số lượng**:

```text
qty  19 · 'Chi phí vận chuyển'
qty  15 · 'Giá treo Tivi'
qty   9 · 'Chân máy giặt Đa Năng'
```

| Phương án | Hệ quả |
|---|---|
| **A (khuyến nghị)** — giữ hết, mặc định sắp theo **Doanh thu** | Không phát minh phân loại (tôn trọng EAC-5/EAC-8); tổng bảng = tổng kỳ; dòng dịch vụ tự chìm xuống khi sắp theo doanh thu |
| B — lọc dòng dịch vụ ra | Cần một authority phân loại product-line mà EAC-8 nói **không được** dùng heuristic validation để làm; và "Giá treo Tivi" (phụ kiện thật) heuristic KHÔNG bắt được → lọc sẽ vừa thiếu vừa thừa |

Nếu Owner không trả lời, **mặc định A cho cả hai** — đó là phương án không
phát minh quy tắc nghiệp vụ nào, và có thể đảo ngược.

## (29) RECOMMENDED_DEFAULTS

Không cần Owner, low-risk, thuần tái dụng ngữ nghĩa đã nghiệm thu:

- LN KPI = `SUM` dòng `AUTO` + coverage `N / M dòng` (§16/§17).
- `NULL` → `—`, không bao giờ `0`.
- Bỏ cột Giá mua tham chiếu khỏi bảng (§18).
- Sắp mặc định theo Doanh thu giảm dần (khớp `employee_totals`).
- Bộ chọn kỳ theo tháng + "Toàn bộ dữ liệu" (khớp PRA-003).
- Drill-down link sang `/ban-hang/<order_key>` đã có (§21).
- Nhãn "Số mặt hàng trên chứng từ", "Tên hàng trên chứng từ" (§14/§25).
- `sales_queries` giữ hàng rào PII riêng; KHÔNG sửa `analytics_queries` (§21).

## (30) MINIMUM_VERTICAL_SLICE

```text
dữ liệu đã persist (KHÔNG schema mới)
  → product_totals()      trong app/web/sales_queries.py   (1 truy vấn gộp)
  → product_lines()       trong app/web/sales_queries.py   (1 truy vấn drill-down)
  → product_presentation  (tái dụng money/count/coverage/profit)
  → route /san-pham + template san_pham.html
  → link sang /ban-hang/<order_key> ĐÃ CÓ
  → Owner nghiệm thu trên production 09/2026
```

Không ingestion mới, không authority mới, không subsystem mới, không migration.

## (31) IMPLEMENTATION_CHANGE_BUDGET

```text
CLASSIFICATION = SMALL
```

| Hạng mục | Ước tính | Đối chiếu |
|---|---|---|
| QUERY | ~60–80 dòng mã | `employee_totals` + `order_detail` là khuôn có sẵn |
| PRESENTATION | ~50–70 | tái dụng toàn bộ helper; chỉ thêm định nghĩa cột |
| WEB (route + template) | ~90–120 | PRA-003 dùng 80 dòng cho `tong_quan.html` |
| TESTS | ~45–60 test mới | PRA-003 = 67, PRA-004 = 94; PRA-005 hẹp hơn cả hai |
| DOCS | task file + contract + session | theo tiền lệ S095/S100 |
| CSS | ~0–10 | tái dụng class bảng đã có |

Tổng Python production ước tính **~110–150 dòng mã** — nhỏ hơn PRA-003 (284)
vì không có Δ so kỳ trước, không có bộ chuyển SỐ CŨ/SỐ MỚI, không có chỉ tiêu
mới nào.

## (32) SCHEMA_REQUIRED

```text
SCHEMA_REQUIRED = NO
```

Chứng minh: §11 ánh xạ TỪNG trường của trang tối thiểu về một cột đã persist.
Bốn trường không có (brand/category/vendor/identity đầy đủ) đều bị DEFER khỏi
slice này chứ không được thay bằng cột mới.

## (33) NEW_AUTHORITY_REQUIRED

```text
NEW_AUTHORITY_REQUIRED = NO
```

PRA-005 KHÔNG tạo product identity thứ hai. Nó gộp theo một khoá **đã tồn
tại và đã được nghiệm thu ở PRA-002**, và gọi đúng tên khoá đó trên UI ("tên
hàng trên chứng từ"), thay vì tuyên bố đó là identity chuẩn. Tracking vẫn là
Product Identity Authority duy nhất.

## (34) TRACKING_CHANGE_REQUIRED

```text
TRACKING_CHANGE_REQUIRED = NO
```

Toàn phiên đọc repo Reports; không truy cập, không sửa Tracking production.
Giới hạn zero-stock identity discovery giữ nguyên `DEFERRED_KNOWN_LIMITATION`
— PRA-005 không tạo blocker production nào cho nó, vì phương án khoá gộp
được khuyến nghị không phụ thuộc identity đã resolve.

## (35) PERFORMANCE_BLOCKER

```text
PERFORMANCE_BLOCKER = NO
```

Đo trong phiên này (E1), SQLite in-memory, đúng hình dạng truy vấn đề xuất
(`_joined()` + `GROUP BY product_key` + `ORDER BY SUM(total_sales) DESC`):

```text
12.000 dòng · 2.491 nhóm sản phẩm · 27,4 ms  (lần 1)
12.000 dòng · 2.491 nhóm sản phẩm · 24,3 ms  (lần 2)
```

Đối chiếu: PRA-003 đo 64 ms trên 12.000 dòng cho truy vấn cùng tầng trên
production PostgreSQL và kết luận KHÔNG cần thêm index. Quy mô thật hiện tại
nhỏ hơn nhiều bậc (09/2026 = 61 dòng). Không warehouse, không OLAP, không
Redis, không materialized view, không index mới.

Lưu ý trung thực: phép đo trên là SQLite, không phải PostgreSQL production —
nó chứng minh hình dạng truy vấn không có vấn đề thuật toán, và con số 64 ms
đã nghiệm thu của PRA-003 là mốc đối chiếu trên đúng engine production.

## (36) BLOCKING_FINDINGS

```text
BLOCKING_FINDINGS = 0
```

Không có finding nào chặn việc freeze contract PRA-005. `FIND-PRA005-01` (§37)
làm đổi **cách gọi tên** trên UI, không chặn triển khai.

## (37) NON_BLOCKING_FINDINGS

**FIND-PRA005-01 — `product_key` SPLIT một sản phẩm thật, có ví dụ định
lượng.** `NON_BLOCKING`. Đo được ở §9: `FTKB50ZVMV` tách thành 7 qty /
113.750.000 và 1 qty / 16.300.000; gộp lại sẽ là sản phẩm doanh thu #1 của
kỳ. Xử lý: KHÔNG sửa mã, KHÔNG thêm matching. Xử lý bằng **cách gọi tên**
(bảng gộp theo "tên hàng trên chứng từ", có ghi chú trên trang) + OD-PRA005-1.
RE-TRIGGER: khi Owner ghi nhận một quyết định thật bị sai vì split, hoặc khi
tỉ lệ split đo lại vượt ~5% chuỗi trong một kỳ.

**FIND-PRA005-02 — ô "Số sản phẩm" trong brief va chạm EAC-5.** `NON_BLOCKING`.
Đã xử lý bằng đổi nhãn thành "Số mặt hàng trên chứng từ" (§14). Không cần
quyết định Owner: đây là tuân thủ một hợp đồng đã nghiệm thu, không phải một
lựa chọn mới.

**FIND-PRA005-03 — `product_group_final` trông như category nhưng là hằng
số.** `NON_BLOCKING`. Ghi lại để phiên sau không nhầm nó là chiều phân tích
sẵn có (§23).

## (38) DEFERRED_FINDINGS

- Brand / Category / Vendor (§22–24) — phụ thuộc TASK-103, chưa tồn tại.
- Trend theo tháng, so kỳ trước theo sản phẩm, top-N, biểu đồ.
- Ma trận Sản phẩm × Nhân viên (§20).
- Khoảng ngày tuỳ chọn / "hôm nay" trên UI (§19).
- "Giá mua đang áp dụng" cấp sản phẩm (point-in-time) (§18).
- Chuẩn hoá tên hàng có thẩm quyền (sửa gốc FIND-PRA005-01) — cần quy trình
  Owner xác nhận alias, KHÔNG phải fuzzy matching.
- Zero-stock identity discovery gap — giữ `DEFERRED_KNOWN_LIMITATION`.

## (39) REAL_DATA_ACCEPTANCE_PLAN

Theo đúng khuôn PRA-003 `CHECK-07` / PRA-004 `CHECK-14`: Owner tự mở
production thật, không phải ảnh chụp, không phải fixture.

1. Mở `/san-pham?ky=2026-09` trên `reports.tinphatcrm.com`.
2. **Bất biến cộng được:** Doanh thu và Tổng số lượng cộng qua TẤT CẢ dòng
   sản phẩm phải bằng ĐÚNG ô tương ứng trên `/tong-quan?ky=2026-09`.
   Cột "Số đơn" KHÔNG cộng được — đúng như ghi chú trên trang.
3. **Đối chiếu oracle FROZEN:** tổng dòng của bảng = **61**, tổng đơn phân
   biệt = **40** (khớp oracle PRA-003/PRA-004 đã accepted).
4. **`NULL ≠ 0`:** ít nhất một sản phẩm có coverage một phần; ô LN KPI của nó
   hiện `—` hoặc một số kèm `N / M dòng` với `N < M`, và KHÔNG BAO GIỜ `0`.
5. **Drill-down:** chọn một sản phẩm → xem các dòng bán của nó → mở một đơn →
   trang `/ban-hang/<order_key>` PRA-004 hiện đúng đơn đó, các con số khớp.
6. **Đối chiếu chéo hai đơn thật đã nghiệm thu:** `BH73844` (AUTO, 9.550.000)
   và `BH73877` (CẦN KIỂM TRA, 32.800.000, coverage 2/3) phải tìm được qua
   drill-down từ sản phẩm tương ứng, với con số KHÔNG đổi so với PRA-004.
7. **Kiểm tra split:** Owner xác nhận có hay không hai dòng cùng một máy được
   gõ khác nhau trong kỳ 09/2026 — dữ liệu thật cho FIND-PRA005-01 và cho
   OD-PRA005-1.

## (40) SCOPE_DRIFT

```text
SCOPE_DRIFT = NO
```

Phiên này: 0 dòng production code, 0 schema, 0 migration, 0 config, 0 chạm
Tracking, 0 task mới, 0 thay đổi roadmap. Không mở REM-T06, không dọn import,
không sửa export/XLSX header. Artifact duy nhất là chính tài liệu này.

Ba lần từ chối mở rộng phạm vi đã ghi lại tường minh: không sửa
`analytics_queries` để nới hàng rào PII (§21); không dùng
`is_non_product_line()` làm phân loại (§28 OD-2); không thêm matching để vá
FIND-PRA005-01 (§37).

## (41) DISCOVERY_EXIT_GATE

```text
DISCOVERY_EXIT_GATE = PASS
```

| # | Điều kiện | Kết quả |
|---|---|---|
| 1 | Khoá gộp được xác định và an toàn, HOẶC blocker được chứng minh | **PASS** — `product_key`, truy vết tới `app/history/keys.py:70`; MERGE bị chặn theo cấu trúc; SPLIT đo được và định lượng (§9) |
| 2 | Trường cần thiết ánh xạ về dữ liệu đã persist | **PASS** — §11, không cột nào thiếu cho trang tối thiểu |
| 3 | Ngữ nghĩa gộp KPI trung thực | **PASS** — §16/§17, tái dụng nguyên vẹn PRA-003 |
| 4 | Product Identity authority được bảo toàn | **PASS** — §33, Tracking vẫn là authority duy nhất; không tạo hệ thứ hai |
| 5 | Trang tối thiểu định nghĩa được mà không phát minh luật nghiệp vụ | **PASS** — §25, bốn cột bị loại kèm lý do |
| 6 | Quyết định Owner được cô lập | **PASS** — §28, đúng 2, cả hai có mặc định an toàn |
| 7 | Không schema/subsystem mới trừ khi chứng minh cần | **PASS** — §32/§33/§34 |
| 8 | Kế hoạch nghiệm thu dữ liệu thật đã định nghĩa | **PASS** — §39, 7 bước |

## (42) NEXT_VERTICAL_ACTION

```text
PRA-005 CONTRACT FREEZE
  → IMPLEMENTATION (MAJOR)
  → INDEPENDENT REVIEW (E2)
  → CONTROLLED INTEGRATION
  → DEPLOY
  → REAL DATA ACCEPTANCE (§39)
```

Phiên tiếp theo mở file task `TASK-PRA-005` dưới `docs/tasks/` + freeze Completion
Gate + mở review budget lineage cho root task `TASK-PRA-005`. Trước khi
freeze, nên có câu trả lời cho OD-PRA005-1 và OD-PRA005-2; nếu Owner không
trả lời, freeze theo mặc định A/A đã nêu ở §28 và ghi rõ đó là
`RECOMMENDED_DEFAULT`, không phải `OWNER_DECISION`.

---

## Phụ lục — Lệnh đã chạy trong phiên (E1)

Mọi con số trong tài liệu này đến từ lệnh thật chạy trong phiên, trên
`4dfe4b2`, chế độ chỉ đọc:

```text
git rev-parse origin/claude/extract-upload-repo-gq2ws4   → 4dfe4b2525ec…
scripts/branch_authority_check.sh                        → DEFAULT_TIP = HEAD_SHA, WORKTREE CLEAN

run_import_production(period_2026_01.xlsx)
  price_source = {OWNER_MANUAL_LEGACY_CONFIRMATION: 2, Pending: 349}
  kpi_purchase_price NOT NULL = 2 · eligible_kpi_profit NOT NULL = 2
  identity NOT None = 0 · canonical_product_code NOT None = 0
  reason = IDENTITY_SOURCES_UNAVAILABLE ×349
run_import_production(period_2026_06.xlsx)
  price_source = {Pending: 180} · kpi NOT NULL = 0

Hồ sơ chiều sản phẩm (đọc trực tiếp cột "Tên hàng trên chứng từ")
  01.2026: 351 dòng · 226 chuỗi · 166 singleton · fold-delta 0 · 3 mã model đa-chuỗi
  06.2026: 180 dòng · 135 chuỗi · 108 singleton · fold-delta 0 · 0 mã model đa-chuỗi

Dòng dịch vụ (compile_keyword_patterns từ config/validation.yaml)
  01.2026: 22/351 dòng (6,3%) · 5.100.000 / 3.564.610.000 doanh thu (0,14%)
  06.2026: 14/180 dòng (7,8%) · 4.852.000 / 1.925.272.000 doanh thu (0,25%)

Hiệu năng GROUP BY product_key (SQLite in-memory, cùng hình dạng truy vấn)
  12.000 dòng · 2.491 nhóm · 27,4 ms / 24,3 ms
```

Phép đo hồ sơ sản phẩm dùng `product_raw` NGUYÊN VĂN của fixture golden —
`tests/fixtures/golden/anonymize.py` liệt kê `product_raw` là trường business
logic ĐỌC, nên nó KHÔNG bị thay surrogate. Các trường PII đã bị xoá/thay từ
trước và phiên này không đọc chúng.
