# S094 — TASK-PRA-003 Session 1: Vertical Slice Discovery & Implementation Plan

Ngày: 2026-09-03
Task Mode: SPIKE / DISCOVERY (chuẩn bị cho MAJOR)
Loại phiên: docs-only — KHÔNG viết production code, KHÔNG sửa schema, KHÔNG migration.

---

## (1) SESSION_RESULT

```text
SESSION                   = S094 — PRA-003 Vertical Slice Discovery (docs-only)
RESULT                    = DISCOVERY_COMPLETE — kế hoạch vertical slice sẵn sàng triển khai
PRODUCTION_CODE_ADDED     = 0 dòng
SCHEMA_CHANGED            = NO       MIGRATION_ADDED = NO
TRACKING_CHANGED          = NO       INFRASTRUCTURE_CHANGED = NO
PRA-002_CHANGED           = NO       PRA-001_CHANGED = NO
IMPLEMENTATION_READY      = YES (với 3 default đã nêu ở mục 14; cả 3 đều NON-BLOCKING)
OWNER_DECISIONS_REQUIRED  = 3 (không cái nào chặn việc bắt đầu implement)
```

## (2) CANONICAL_SHA

```text
DEFAULT_BRANCH (origin HEAD) = claude/extract-upload-repo-gq2ws4
EXPECTED_HEAD                = facf090c782b022730ecc5f1cf0d0b02e29ca8d7
git ls-remote origin claude/extract-upload-repo-gq2ws4
                             = facf090c782b022730ecc5f1cf0d0b02e29ca8d7
KẾT LUẬN                     = CANONICAL_NOT_MOVED — khớp chính xác EXPECTED
LOCAL HEAD (session branch)  = facf090c782b022730ecc5f1cf0d0b02e29ca8d7 (bằng canonical)
SESSION_BRANCH               = claude/pra-003-vertical-slice-346ebn

scripts/branch_authority_check.sh (E1, đầu phiên):
  DEFAULT_TIP = facf090c782b022730ecc5f1cf0d0b02e29ca8d7
  HEAD_SHA    = facf090c782b022730ecc5f1cf0d0b02e29ca8d7
  WORKTREE    = CLEAN
  STOP — BRANCH AUTHORITY UNRESOLVED: nhánh phiên chưa có upstream
        (đúng như dự kiến với nhánh mới; giải quyết bằng chính lần push của phiên này)
```

Tiền đề đã xác minh: `TASK-PRA-002 = DONE` và đã Controlled Integration vào
canonical (`facf090`, `189516e`, `432ad4e` nằm trên default branch). Điều kiện
"chỉ mở PRA-003 sau khi PRA-002 DONE + tích hợp" (S093 `NEXT_VERTICAL_ACTION`)
đã thoả.

## (3) BUSINESS_GOAL

Biến dữ liệu nghiệp vụ ĐÃ ĐƯỢC LƯU thành một màn hình quản lý dùng được hằng
ngày, trả lời đúng ba câu:

1. Kỳ này bán được bao nhiêu, bao nhiêu đơn, lãi bao nhiêu — và phần nào của
   con số đó là chắc chắn (AUTO) so với phần còn phải kiểm tra (Review).
2. Từng nhân viên đóng góp bao nhiêu trong kỳ đó.
3. Số đang xem là **số cũ trong Excel** hay **số Reports tính từ sổ kế toán đã
   nạp** — không bao giờ để người xem phải đoán.

Không phải mục tiêu của PRA-003: thêm một dự án persistence nữa; drill-down
đơn/sản phẩm; quy trình xử lý Review (đều thuộc PRA-004/PRA-005).

## (4) CURRENT_DATA_CAPABILITIES

Nguồn: `tools/db/schema.py` (6 bảng `PIPELINE_GENERATED` của migration
`0002_snapshots`) + `app/history/extraction.py` (ghi gì vào đó) +
`app/web/history_store.py` (đọc ra thế nào). Tất cả là FACT đọc từ mã nguồn.

| Năng lực yêu cầu (mục 6 chỉ thị) | Cột/bảng thật | Phân loại |
|---|---|---|
| sale date | `order_line_current.sale_date` (có index) — bản sao đã chuẩn hoá của `order_line_source_version.sale_date` | READY_NOW |
| order | `order_line_current.order_key` = `normalize(Số BH)` (DEC-166) | READY_NOW |
| employee / seller | `order_line_result_version.employee_normalized`, `.employee_group` | READY_NOW |
| quantity | `order_line_source_version.quantity` (join qua `order_line_current.current_source_version_id`) | READY_NOW |
| sales | `order_line_result_version.total_sales` = `sell_price × quantity − discount` (DEC-114, `app/modules/importing/normalizer.py:27`) | READY_NOW |
| sales gộp (chưa trừ chiết khấu) | `order_line_source_version.total_sales_raw` (cột "Tổng bán" của ERP) | READY_NOW |
| accounting purchase price | `order_line_result_version.accounting_purchase_price` + `.price_source` | READY_NOW |
| KPI purchase price / PP | `.kpi_purchase_price` + `.kpi_purchase_provenance` | READY_NOW |
| accounting profit | `.accounting_profit` = `(sell_price − accounting_purchase_price) × quantity` | READY_NOW |
| KPI profit | `.eligible_kpi_profit` (fail-closed = `NULL` khi thiếu input hoặc authority) | READY_NOW |
| lợi nhuận ERP ghi sẵn trong sổ | `order_line_source_version.source_profit` | READY_NOW (nhưng xem mục 14 D1) |
| AUTO / Review — theo DÒNG | `order_line_result_version.status ∈ {AUTO, PENDING}` | READY_NOW |
| AUTO / Review — theo ĐƠN | DẪN XUẤT: đơn là Review ⟺ có ít nhất một dòng `PENDING` | DERIVABLE_WITH_EXISTING_DATA |
| lý do Review | `.pending_reasons_json` | READY_NOW (nhưng thuộc PRA-004) |
| source / result version | `order_line_source_version` / `order_line_result_version` (append-only) | READY_NOW |
| current-state pointer | `order_line_current` (PK = `order_key + product_key + occurrence_index`) | READY_NOW |
| data origin | cột `origin` trên MỌI bảng fact, có CHECK constraint (`LEGACY_REFERENCE` / `PIPELINE_GENERATED`) | READY_NOW |
| product identity | `.canonical_product_code`, `.identity_namespace` | READY_NOW (thuộc PRA-005) |
| conversion | `.conversion_scheme_final`, `.conversion_rate_final` | READY_NOW về dữ liệu — nhưng LATER về nghiệp vụ (mục 7) |

**FACT quan trọng #1 — AUTO kéo theo đầy đủ số tiền.**
`_PresentedLine.status` = `"PENDING" if self.reasons else "AUTO"`
(`app/modules/exporting/excel_exporter.py:71-73`), và `_present_lines` luôn
thêm reason `Pending.accounting_purchase_price` / `Pending.accounting_profit` /
`Pending.eligible_kpi_profit` cho mỗi trường còn `None`
(cùng file, dòng 141-149). Suy ra: **mọi dòng `status = AUTO` chắc chắn có đủ
`accounting_purchase_price`, `accounting_profit`, `eligible_kpi_profit`.**
Chiều ngược lại KHÔNG đúng — một dòng có đủ ba số vẫn có thể `PENDING` vì lý do
khác (EmployeeMapping, Suspicious.ERP…). Vì vậy "Lợi nhuận KPI chỉ cộng dòng
AUTO" là một quy tắc TRÌNH BÀY có định nghĩa chặt và luôn cộng được, không phải
một phép lọc tuỳ tiện.

**FACT quan trọng #2 — "Accounting coverage 100%" KHÔNG có nghĩa là đã có đủ giá nhập.**
`ReportSummary.order_accounting_rate = accounted_orders / input_orders`
(`excel_exporter.py:59-61`). Nó đo "mọi đơn trong sổ đã dựng được thành Order",
KHÔNG đo "mọi dòng đã có giá nhập kế toán". Con số 100% mà Owner đọc trên
production ngày 2026-09-03 vì vậy KHÔNG cho phép kết luận rằng 61 dòng đều có
lợi nhuận. Không được suy ra như vậy ở bất kỳ chỗ nào của PRA-003.

**FACT quan trọng #3 — `sale_date` là NULLABLE.**
`RawRow.date: Optional[date]` (`app/modules/domain/models.py:113`) và
`order_line_current.sale_date` nullable. Hàm lọc kỳ hiện có `_period()`
(`app/web/history_store.py:1106-1113`) so sánh `>=` / `<=`, nên dòng không có
ngày bán **rơi ra khỏi mọi kỳ trong im lặng**. PRA-003 bắt buộc phải đếm và
hiển thị số dòng hiện hành không có ngày bán, nếu không thì tổng doanh thu của
"toàn bộ các kỳ" có thể nhỏ hơn tổng thật mà không ai biết.

**FACT quan trọng #4 — `summary_json` per snapshot KHÔNG dùng được để cộng theo kỳ.**
`history_writer.build_summary()` lưu `auto_orders`/`review_orders`/`total_lines`
vào `source_snapshot.summary_json`. Đó là số của MỘT lần chạy. Hai snapshot có
ngày chồng nhau mà cộng `summary_json` lại là double-count — đúng thứ PRA-002
được sinh ra để chống. AUTO/Review theo kỳ **phải** dẫn xuất từ
`order_line_current` → `order_line_result_version.status`.

**Năng lực truy vấn đã có sẵn:**
`SnapshotRepository.current_totals(date_from, date_to)`
(`history_store.py:1047`) đã trả `lines`, `orders`, `total_sales` theo kỳ, và
đã chứng minh không double-count bằng chính cấu trúc PK của
`order_line_current`. Đây là hạt giống của Tổng quan — PRA-003 mở rộng theo
đúng khuôn đó, không phát minh mô hình truy vấn mới.

**Năng lực truy vấn còn thiếu:**
`available_periods()` (`history_store.py:269`) chỉ tồn tại trên
`LegacyRepository`. Phía pipeline **chưa có** hàm nào trả về danh sách kỳ có dữ
liệu. Đây là khoảng trống duy nhất chặn bộ chọn kỳ, và nó là DERIVABLE
(`min/max` trên `order_line_current.sale_date`).

## (5) LEGACY_REFERENCE_CAPABILITIES

Bốn bảng `legacy_*` (migration `0001_legacy`), origin = `LEGACY_REFERENCE`,
CHECK constraint khoá cứng.

- `legacy_summary_row` — ma trận (năm, tháng, người bán) × 17 chỉ tiêu:
  `orders`, `products`, `sales`, `converted_revenue`, `profit`, `margin_ratio`,
  `vs_prev_month_ratio`, `stock_ratio`, `actual_profit`, `per_day`, `target`,
  `vs_target_ratio`, `bonus`, `workdays`, `base_salary`, `allowance`,
  `total_salary`. `row_kind ∈ {SELLER, MONTH_TOTAL, PROGRESS, YEAR_TOTAL}`.
  Đơn vị mặc định **kVND** (nghìn đồng). Kèm `known_defects` (A1/A2/A4/A6) và
  `formula_text`.
- `legacy_daily_sales` — doanh số theo NGÀY (VND nguyên) từ DataChart.
- `legacy_monthly_reference` — cùng kỳ năm trước, target năm, bình quân/ngày.
- `legacy_import` — bản nhập nào đang `is_current`.

**Legacy là bản ghi lịch sử tính tay, KHÔNG phải authority tính toán hiện
hành** (DEC-166 E): không chạy lại bằng pipeline, không sửa lỗi công thức cũ,
luôn phân biệt với `PIPELINE_GENERATED`.

Legacy là nơi DUY NHẤT trong toàn hệ thống có **target** và có **margin_ratio**
đã tính sẵn. Nhưng cả hai là số tay của kỳ cũ, gắn với `import_id` cụ thể —
chúng không phải target/margin của kỳ pipeline hiện hành và không được dùng
thay.

## (6) PIPELINE_CAPABILITIES

Ngoài bảng cột đã liệt kê ở mục 4, những gì tầng pipeline BẢO ĐẢM:

- **Không double-count theo cấu trúc**: `order_line_current` có PK theo khoá
  dòng, nên mỗi khoá góp đúng một dòng vào mọi tổng — không phụ thuộc câu truy
  vấn có nhớ `DISTINCT` hay không. Đã được E2 kiểm chứng trên PostgreSQL 16.13
  thật (S092: `state(A rồi B) == state(B)` trên cả totals lẫn tập
  (khoá, fingerprint)).
- **Append-only**: mọi bảng fact chỉ INSERT; chỉ `order_line_current` và ba cột
  xác nhận coverage được UPDATE.
- **Fail-closed về `NULL`, không bao giờ về `0`**: `compute_accounting_profit`
  và `compute_eligible_kpi_profit` trả `None` khi thiếu input (DEC-103,
  `governance/core/03_DATA_MODEL_RULES.md` §5). PRA-003 phải giữ nguyên tính
  chất này lên UI: ô trống hiện `—`, không hiện `0`.
- **Không có PII khách hàng**: `app/history/extraction.py` cố ý không chép
  `customer`, `customer_code`, `phone`, `address`, `shipper_raw` sang tầng
  history. Vì vậy PRA-003 **không có đường nào** làm lộ PII, kể cả do sơ ý.
  `employee_raw` / `employee_normalized` CÓ (đó là dữ liệu KPI, không phải PII
  khách hàng).
- **Coverage tách hai mức**: `DETECTED_ONLY` / `HEADER_CONSISTENT` /
  `CONFIRMED_COMPLETE`. Chỉ mức thứ ba là lời khẳng định của con người rằng sổ
  đã đầy đủ cho một khoảng ngày.

## (7) DATA_GAPS

| Chỉ tiêu mong muốn | Phân loại | Bằng chứng |
|---|---|---|
| Số lượng SP (loại trừ dòng phí/chiết khấu) | **MISSING_BUSINESS_RULE** | `non_product_lines` trong `config/validation.yaml:144` là cấu hình **hạ mức cảnh báo xuống INFO** cho validator (`app/modules/validation/validator.py:77`), KHÔNG phải phân loại "hàng / không phải hàng" để đếm. Dùng nó làm quy tắc đếm là tự phát minh thẩm quyền. N.7 của TASK-PRA-000 vẫn MỞ. |
| Target theo (nhân viên, tháng) | **MISSING_DATA + MISSING_BUSINESS_RULE** | Không có cột target nào trong 6 bảng pipeline; `config/targets` không tồn tại (`ls config/` = adjustments, conversion_rates, eligible_costs, employees, lead_source, price_resolution, validation). Legacy có `target` nhưng là số tay của kỳ cũ. N.8 MỞ. |
| So target | **MISSING_DATA** | Hệ quả trực tiếp của dòng trên. |
| Margin / tỉ lệ lợi nhuận | **MISSING_BUSINESS_RULE** | Tính được về mặt số học, nhưng "LN nào chia doanh thu nào" là N.7, chưa chốt. TASK-PRA-000 §L xếp Margin = **LATER**. |
| Doanh số quy đổi | **OUT_OF_SCOPE_PRA003** | §L: LATER — "chờ engine chốt `converted_revenue` theo dòng có provenance; **không tính ở tầng UI**". `conversion_rate_final` có trong DB nhưng nhân nó ở tầng trình bày chính là điều §L cấm. |
| So kỳ trước | **DERIVABLE_WITH_EXISTING_DATA** | Cùng một truy vấn, dịch khoảng ngày. Chỉ đúng khi kỳ trước THỰC SỰ có dữ liệu — nếu không phải để trống, không dùng 0. |
| Danh sách kỳ có dữ liệu (pipeline) | **DERIVABLE_WITH_EXISTING_DATA** | `min/max(order_line_current.sale_date)`; hàm chưa tồn tại. |
| AUTO/Review theo ĐƠN, theo kỳ | **DERIVABLE_WITH_EXISTING_DATA** | Xem FACT #1 và FACT #4. |
| Dòng hiện hành không có ngày bán | **DERIVABLE_WITH_EXISTING_DATA** | `COUNT(*) WHERE sale_date IS NULL`. Bắt buộc phải hiện — xem FACT #3. |
| Cùng kỳ năm trước / YTD | **OUT_OF_SCOPE_PRA003** | §L: LATER; nguồn 2025 là legacy, khác định nghĩa. |
| Xu hướng nhân viên nhiều tháng | **OUT_OF_SCOPE_PRA003** | §L: LATER; cần ≥3 tháng dữ liệu pipeline, hiện có 3 NGÀY. |
| Drill-down đơn / sản phẩm, lý do Review | **OUT_OF_SCOPE_PRA003** | PRA-004 / PRA-005 (chỉ thị mục 3 và 17). |

**Không mở ingestion mới cho bất kỳ dòng nào ở trên.**

## (8) TONG_QUAN_MINIMUM_SLICE

Nguyên tắc: mỗi ô phải nói được nó là gì, lấy từ đâu, và phần nào của dữ liệu
nó phủ. Ô nào không nói được thì không lên trang.

| Ô | Ý nghĩa nghiệp vụ | Nguồn | Cách tính | Sẵn sàng | Thẩm quyền | Cần Owner? |
|---|---|---|---|---|---|---|
| Kỳ đang xem | Khoảng ngày bán của số đang hiển thị | `order_line_current.sale_date` | tham số kỳ | READY_NOW | PIPELINE | Không |
| Tổng đơn | Số đơn hàng hiện hành trong kỳ | `order_line_current.order_key` | `COUNT(DISTINCT order_key)` | READY_NOW | PIPELINE | Không |
| Số dòng hàng | Số dòng sổ hiện hành trong kỳ | `order_line_current` | `COUNT(*)` | READY_NOW | PIPELINE | Không |
| Tổng số lượng | Tổng cột SL của mọi dòng (KHÔNG loại dòng phí) | `order_line_source_version.quantity` | `SUM(quantity)` | READY_NOW | PIPELINE | D3 (nhãn) |
| Doanh thu (đã trừ chiết khấu) | Tiền bán thực tế | `order_line_result_version.total_sales` | `SUM(total_sales)` | READY_NOW | PIPELINE | Không |
| Lợi nhuận KPI + coverage | LN dùng cho KPI, CHỈ trên dòng AUTO | `.eligible_kpi_profit`, `.status` | `SUM(...) WHERE status='AUTO'`, kèm `AUTO lines / total lines` | READY_NOW | PIPELINE (DEC-166 → §L NOW) | D1 |
| Lợi nhuận kế toán + coverage | LN kế toán trên các dòng đã có giá nhập | `.accounting_profit` | `SUM(...) WHERE accounting_profit IS NOT NULL`, kèm coverage | READY_NOW | PIPELINE | D1 |
| AUTO / Cần kiểm tra (đơn) | Bao nhiêu đơn đã chắc, bao nhiêu còn phải xem | `.status` | đơn Review ⟺ có ≥1 dòng PENDING | DERIVABLE | PIPELINE | Không |
| AUTO / Cần kiểm tra (dòng) | Cùng ý nghĩa ở mức dòng | `.status` | `COUNT` theo status | READY_NOW | PIPELINE | Không |
| So kỳ trước | Δ tuyệt đối + Δ % của đơn/doanh thu | cùng truy vấn, kỳ liền trước | trống khi kỳ trước không có dữ liệu | DERIVABLE | PIPELINE | Không |
| Dòng chưa có ngày bán | Cảnh báo trung thực: tiền nằm ngoài mọi kỳ | `order_line_current.sale_date IS NULL` | `COUNT(*)` | DERIVABLE | PIPELINE | Không |
| Top nhân viên trong kỳ | 5 dòng đầu của bảng Nhân viên | như mục 9 | `ORDER BY doanh thu DESC` | DERIVABLE | PIPELINE | Không |

**KHÔNG lên trang ở slice này** (đã có lý do ở mục 7): margin, target, so
target, doanh số quy đổi, YTD, biểu đồ, "Số lượng SP" theo nghĩa loại dòng phí,
bảng đối chiếu lệch legacy↔pipeline.

Bỏ bảng đối chiếu legacy↔pipeline khỏi slice tối thiểu là một chỗ **hẹp hơn**
TASK-PRA-000 §M SLICE 3: dữ liệu pipeline hiện có là 3 ngày của tháng 09/2026,
còn legacy dừng ở tháng 08/2026 — chưa có một (tháng × nhân viên) nào có mặt ở
cả hai nguồn, nên bảng lệch sẽ rỗng hoặc chỉ toàn ô "không so được". Xây nó bây
giờ là xây một màn hình chưa có gì để nói.

## (9) NHAN_VIEN_MINIMUM_SLICE

Trang `/nhan-vien` hiện tại hiển thị ma trận Summary cũ (kVND, badge `LEGACY`,
dấu nhắc lỗi A1/A2/A4/A6). **Giữ nguyên 100%, không đổi một ô nào** —
PRA-001 đã DONE và S093 đã dùng chính trang này làm bằng chứng không hồi quy.

Cách tiến hoá: thêm **một bộ chuyển nguồn** ngay dưới tiêu đề, hai lựa chọn:

```
[ SỐ CŨ (Excel) ]   [ SỐ MỚI (Reports) ]
```

- `GET /nhan-vien` (không tham số) → **giữ đúng trang legacy như hôm nay**.
  Đây là lựa chọn có chủ đích: bảo toàn tuyệt đối bằng chứng non-regression của
  PRA-001, và người dùng cũ không bị đổi màn hình dưới chân.
- `GET /nhan-vien?nguon=moi` → bảng nhân viên từ pipeline.

Hai bảng nằm ở hai màn hình khác nhau, **không bao giờ trộn vào một ô**
(TASK-PRA-000 acceptance (4)).

Bảng "SỐ MỚI" — một dòng cho mỗi `employee_normalized`, cộng một dòng
`TỔNG` phải bằng đúng số trên Tổng quan cùng kỳ:

| Cột | Nguồn | Ghi chú |
|---|---|---|
| Nhân viên | `.employee_normalized` | `NULL`/rỗng → dòng "Chưa xác định nhân viên", KHÔNG gộp vào ai |
| Nhóm | `.employee_group` | `STANDARD_SALES` / `NOI_THANH` (`config/employees.yaml`) |
| Đơn | `COUNT(DISTINCT order_key)` | Một đơn có hai nhân viên sẽ được đếm ở cả hai dòng — chú thích rõ, không âm thầm chia |
| Dòng hàng | `COUNT(*)` | |
| Số lượng | `SUM(quantity)` | cùng định nghĩa Tổng quan |
| Doanh thu | `SUM(total_sales)` | |
| LN KPI (AUTO) + coverage | `SUM(eligible_kpi_profit) WHERE status='AUTO'` | luôn kèm `AUTO/tổng dòng` |
| LN kế toán + coverage | `SUM(accounting_profit) WHERE NOT NULL` | |
| AUTO / Cần kiểm tra | đếm dòng theo `status` | |
| So kỳ trước | Δ doanh thu | trống khi kỳ trước không có dữ liệu |

**KHÔNG có trong slice này:** chi tiết đơn, chi tiết sản phẩm, lý do Review,
thao tác xử lý Review, target/so target, margin, xu hướng nhiều tháng.
Tất cả thuộc PRA-004 / PRA-005 hoặc chờ Owner (mục 14).

## (10) PERIOD_MODEL

Mô hình nhỏ nhất đủ dùng thật:

```
Bộ chọn kỳ = MỘT select duy nhất, toàn bộ tuỳ chọn DẪN XUẤT từ dữ liệu đã lưu:

  • "Toàn bộ dữ liệu"        → min(sale_date) → max(sale_date)
  • "Tháng MM/YYYY"          → mỗi tháng thực sự có dòng hiện hành
```

- Nguồn kỳ = `order_line_current.sale_date` (trạng thái hiện hành), **không
  phải** header dòng 2 của workbook. Chỉ thị mục 9 và FIND-RDA-01 (header dạng
  `Ngày 01 tháng 9 năm 2026` không parse được) đều dẫn tới cùng kết luận: không
  suy ngữ nghĩa kỳ báo cáo từ giới hạn của parser.
- Kỳ so sánh = **tháng liền trước** của tháng đang chọn. Không có dữ liệu ở đó
  → mọi ô so sánh để **trống kèm chữ "chưa có dữ liệu kỳ trước"**, tuyệt đối
  không hiển thị `0` hay `0%`.
- Với lựa chọn "Toàn bộ dữ liệu" → **không có** kỳ so sánh (không bịa ra một
  kỳ trước cho một khoảng tuỳ ý).
- **DEFER**: chọn khoảng ngày tự do (from/to), quý, năm, "hôm nay/tuần này".
  Khoảng tự do chưa có nhu cầu đã chứng minh; quý/năm chưa có đủ dữ liệu; bộ
  chọn "hôm nay" là lời hứa sai với nguồn dữ liệu theo lô (§L: DEFER).

Ca production 2026-09-01 → 2026-09-03 nằm gọn trong "Tháng 09/2026", nên mô
hình tháng phục vụ được ca thật đầu tiên mà không cần thêm điều khiển nào.

## (11) DATA_ORIGIN_UX

Hai nguồn, hai nhãn, không bao giờ cộng chung:

| | Nhãn hiển thị | Giải thích tiếng Việt (title + câu dẫn trên trang) |
|---|---|---|
| `LEGACY_REFERENCE` | `LEGACY` *(giữ nguyên, không đổi)* | "Số cũ chép nguyên từ file Excel Báo cáo Kinh doanh, giữ nguyên trạng — không do Reports tính lại." |
| `PIPELINE_GENERATED` | `SỐ MỚI` | "Số do Reports tính từ sổ kế toán đã nạp." |

Quyết định giữ nguyên chữ `LEGACY`: nó là hằng số
`legacy_presentation.ORIGIN_BADGE` mà PRA-001 đã đóng gate và S093 đã dùng làm
bằng chứng production. Đổi chuỗi đó là sửa bề mặt đã nghiệm thu của một task
DONE để lấy sự cân xứng thẩm mỹ — không đáng.

Cách áp dụng, theo mức độ ồn:

- **Tổng quan**: 100% số là pipeline → **một câu dẫn ở đầu trang**, không gắn
  badge lên từng ô (badge trên mọi ô của một trang đơn-nguồn chỉ là nhiễu).
- **Nhân viên**: hai màn hình tách biệt; mỗi màn hình có badge của nguồn mình ở
  tiêu đề bảng, và bảng legacy giữ nguyên badge trên từng ô như hôm nay.
- Mọi trang có cả hai lựa chọn đều mang một câu: *"LEGACY = số cũ trong Excel.
  SỐ MỚI = số Reports tính từ sổ kế toán đã nạp. Hai loại số không bao giờ được
  cộng chung."*

**Không phơi lên dashboard**: `snapshot_id`, `run_id`, `source_version` /
`result_version`, `coverage_state`, `outcome` reconcile, `reconciliation_flag`.
Chúng đã có chỗ đúng của chúng ở tab **Dữ liệu** và trang snapshot. Ngoại lệ
DUY NHẤT: khi kỳ đang xem có dòng cờ `NOT_SEEN`/`REMOVED_CANDIDATE`/
`SOURCE_CHANGED`, Tổng quan hiển thị **một dòng chữ + link sang tab Dữ liệu**,
không hiển thị bảng cờ.

## (12) REAL_VERTICAL_01_03_09

Ca production đã nghiệm thu (S093, `PRODUCTION_ACCEPTANCE_RESULT = PASS`):

```text
Kỳ                       : 2026-09-01 → 2026-09-03
Trạng thái hiện hành     : 61 dòng · 40 đơn
AUTO / Review (theo ĐƠN) : 15 / 25
Dòng không nhận ra       : 0
order_accounting_rate    : 100%   (= 40/40 đơn dựng được — KHÔNG phải coverage giá nhập)
Snapshot                 : SNAP-20260903034024-7b421983 (upload 1),
                           SNAP-20260903034120-7b421983 (upload 2, FILE TRÙNG, SAME 61)
Coverage state           : HEADER_CONSISTENT
```

Với dữ liệu này, chọn kỳ **"Tháng 09/2026"**, Tổng quan phải hiển thị được:

```text
Tổng đơn            = 40                          ← ĐÃ QUAN SÁT trên production
Số dòng hàng        = 61                          ← ĐÃ QUAN SÁT trên production
AUTO (đơn)          = 15   Cần kiểm tra (đơn) = 25 ← ĐÃ QUAN SÁT trên production
Tổng số lượng       = <đọc từ DB>                 ← CHƯA QUAN SÁT — không được bịa
Doanh thu           = <đọc từ DB>                 ← CHƯA QUAN SÁT — không được bịa
LN KPI (AUTO)       = <đọc từ DB> + coverage      ← CHƯA QUAN SÁT — không được bịa
LN kế toán          = <đọc từ DB> + coverage      ← CHƯA QUAN SÁT — không được bịa
So tháng trước      = TRỐNG ("chưa có dữ liệu kỳ trước")
                      ← tháng 08/2026 KHÔNG có dữ liệu pipeline; đây là kết luận
                        từ FIRST_UPLOAD range 2026-09-01→03, không phải giả định
Dòng chưa có ngày bán = <đọc từ DB> (kỳ vọng 0)
```

**KHÔNG tuyên bố** gross/net/qty production. Bộ số
`qty 71 · gross 593.750.000 · discount 200.000 · net 593.550.000` có provenance
RDA S090/S091 (`CHECK-PRA002-14`) và đã được S093 ghi rõ là
`NOT_CLAIMED_AS_PRODUCTION` — nó không phải số của ca 01→03/09 trên production.
PRA-003 không được dùng nó làm kỳ vọng.

Giá trị của ca này với PRA-003: nó là ca thật đầu tiên **đi qua nhánh "kỳ trước
trống"** — nhánh dễ sai nhất của mọi dashboard (hiện `0` hoặc `-100%` thay vì
để trống). Đó là lý do nó xứng đáng là vertical target đầu tiên.

## (13) METRIC_AUTHORITY_MATRIX

`AUTH` = thẩm quyền của định nghĩa. `DATA` = dữ liệu đã có chưa.

| Chỉ tiêu | AUTH | Nguồn thẩm quyền | DATA | Vào slice 1? |
|---|---|---|---|---|
| Tổng đơn | ĐÃ CÓ | DEC-166 (`ORDER_KEY = normalize(Số BH)`) + §L NOW | READY_NOW | CÓ |
| Số dòng hàng | ĐÃ CÓ | PRA-002 `ORDER_LINE_KEY` | READY_NOW | CÓ |
| Doanh thu (net) | ĐÃ CÓ | DEC-114 (`sell_price×qty − discount`) | READY_NOW | CÓ |
| Doanh thu gộp | ĐÃ CÓ | cột ERP `total_sales_raw` | READY_NOW | KHÔNG (chưa có nhu cầu) |
| Tổng số lượng (thô) | ĐÃ CÓ (số học) | cột `quantity` của sổ | READY_NOW | CÓ — nhãn chính xác "chưa loại dòng phí" |
| Số lượng SP (loại dòng phí) | **CHƯA CÓ** | N.7 MỞ | MISSING_BUSINESS_RULE | KHÔNG |
| LN KPI (AUTO) + coverage | ĐÃ CÓ | DEC-166 → TASK-PRA-000 §L = NOW | READY_NOW | CÓ |
| LN kế toán + coverage | ĐÃ CÓ (công thức) / **CHƯA CÓ** (vai trò trên dashboard) | `profit_engine` §U | READY_NOW | CÓ, ở vai trò phụ — xem D1 |
| LN theo sổ ERP (`source_profit`) | **CHƯA CÓ** vai trò | không có văn bản nào cho nó lên dashboard | READY_NOW | KHÔNG — xem D1 |
| AUTO/Review (dòng) | ĐÃ CÓ | `_PresentedLine.status` | READY_NOW | CÓ |
| AUTO/Review (đơn) | ĐÃ CÓ | `pending_orders` của exporter | DERIVABLE | CÓ |
| So kỳ trước | ĐÃ CÓ | §L NOW ("trống khi kỳ trước không có dữ liệu, không dùng 0") | DERIVABLE | CÓ |
| Đóng góp theo nhân viên | ĐÃ CÓ | §L NOW | READY_NOW | CÓ |
| Margin | **CHƯA CÓ** | §L = LATER, N.7 MỞ | MISSING_BUSINESS_RULE | KHÔNG |
| Target / So target | **CHƯA CÓ** | §L NOW *nhưng* cần N.8 | MISSING_DATA | KHÔNG — xem D2 |
| Doanh số quy đổi | **CHƯA CÓ** | §L = LATER, cấm tính ở tầng UI | READY_NOW (rate có) | KHÔNG |
| Lệch legacy ↔ pipeline | ĐÃ CÓ | §L NOW-lite | chưa có kỳ chồng nhau | KHÔNG (mục 8) |
| Review burden theo nhóm lý do | ĐÃ CÓ | §L slice 4 | READY_NOW | KHÔNG — PRA-004 |
| Sản phẩm / Pareto | ĐÃ CÓ | §L slice 5 | READY_NOW | KHÔNG — PRA-005 |

## (14) OWNER_DECISIONS_REQUIRED

Ba quyết định. **Cả ba đều NON-BLOCKING** — mỗi cái có một default an toàn để
phiên implement bắt đầu ngay; Owner có thể ghi đè trước khi phiên 2 mở.

### D1 — Dashboard quản lý nhấn mạnh LỢI NHUẬN NÀO?

- **DECISION**: chọn con số lợi nhuận chính của Tổng quan và của bảng Nhân
  viên.
- **WHY_REQUIRED**: hệ thống có **ba** con số lợi nhuận khác nhau, đều tồn tại
  thật trong DB, và không văn bản nào nói cái nào là "con số quản lý": (a)
  `eligible_kpi_profit` — LN dùng cho KPI/thưởng, fail-closed; (b)
  `accounting_profit = (giá bán − giá nhập kế toán) × SL`; (c) `source_profit` —
  cột lợi nhuận do chính ERP ghi trong sổ. Đây là ý nghĩa nghiệp vụ, code không
  trả lời được.
- **OPTIONS**:
  - A. **KPI là số chính, kế toán là cột phụ, cả hai kèm coverage.**
  - B. Chỉ LN KPI (đúng nghĩa đen §L NOW).
  - C. Chỉ LN kế toán.
  - D. Thêm cả `source_profit` để đối chiếu với "Tổng lợi nhuận" của báo cáo cũ.
- **RECOMMENDED_DEFAULT**: **A**. TASK-PRA-000 §L đã đặt "LN KPI (eligible) +
  coverage" vào nhóm NOW, và DEC-166 giữ nguyên bảng ưu tiên đó — nên KPI làm
  số chính là đi theo thẩm quyền đã có. LN kế toán đứng cạnh vì nó là con số mà
  bộ phận kế toán đọc, và vì hai coverage khác nhau (LN KPI chỉ trên dòng AUTO,
  LN kế toán trên mọi dòng đã có giá nhập) tự nó đã là thông tin quản lý.
  `source_profit` **không** lên dashboard: nó là số của ERP, chưa qua bất kỳ
  quy tắc nào của Reports, đưa lên cạnh hai số kia là mời người đọc so ba số mà
  không ai giải thích được chênh lệch.
- **CONSEQUENCE**: nếu Owner chọn B → bớt một cột, bớt ~15 LOC. Nếu chọn D →
  cần một mục "vì sao ba số khác nhau" và một task đối chiếu riêng; đó là mở
  scope, khuyến nghị không làm trong PRA-003.

### D2 — Target lấy từ đâu?

- **DECISION**: có đưa "Target" và "So target" vào PRA-003 slice 1 không, và
  nếu có thì Owner cấp dữ liệu target dạng nào.
- **WHY_REQUIRED**: pipeline **không có** dữ liệu target ở bất kỳ bảng nào, và
  `config/targets` chưa tồn tại. Legacy có `target` nhưng là số tay của kỳ cũ,
  gắn với một `import_id` — dùng nó cho kỳ pipeline là gán số cũ cho kỳ mới.
  N.8 của TASK-PRA-000 vẫn MỞ.
- **OPTIONS**:
  - A. **DEFER target khỏi slice 1**; đưa vào một micro-slice sau khi Owner cấp
    file.
  - B. Owner cấp `config/targets.yaml` theo (nhân viên | nhóm, tháng, số tiền,
    `effective_from`) ngay; slice 1 có thêm 2 cột.
  - C. Dùng tạm target legacy của tháng gần nhất.
- **RECOMMENDED_DEFAULT**: **A**. Không có dữ liệu thì không có cột; một cột
  target trống hoặc suy từ kỳ khác làm hỏng đúng thứ mà dashboard tồn tại để
  làm. C bị loại thẳng: nó trộn `LEGACY_REFERENCE` vào một con số
  `PIPELINE_GENERATED` — vi phạm DEC-166 E.
- **CONSEQUENCE**: Tổng quan slice 1 không trả lời "có đạt chỉ tiêu không". Đây
  là mất mát thật và cần nói rõ với Owner. Bù lại nó không nói sai. Nếu Owner
  chọn B, chi phí thêm khoảng +45 LOC production + 1 file config + 4 test; vẫn
  không cần schema/migration.

### D3 — "Số lượng" trên dashboard nghĩa là gì?

- **DECISION**: ô số lượng đếm mọi dòng, hay loại các dòng phí vận chuyển /
  công lắp đặt / chiết khấu / voucher?
- **WHY_REQUIRED**: `non_product_lines` trong `config/validation.yaml` **là cấu
  hình hạ mức cảnh báo cho validator**, không phải phân loại "hàng hoá". Dùng
  nó làm quy tắc đếm sản phẩm là tự cấp thẩm quyền cho một file cấu hình chưa
  bao giờ được duyệt cho mục đích đó. N.7 MỞ.
- **OPTIONS**:
  - A. **Slice 1 hiển thị "Tổng số lượng (mọi dòng)"** — nhãn nói đúng điều nó
    làm; DEFER chỉ tiêu "Số lượng SP".
  - B. Loại theo `non_product_lines` ngay, ghi rõ danh sách từ khoá trên UI.
  - C. Bỏ hẳn ô số lượng khỏi slice 1.
- **RECOMMENDED_DEFAULT**: **A**. Con số vẫn có ích (kiểm tra nhanh khối lượng
  bán), nhãn không hứa điều nó không làm, và không tạo ra một quy tắc nghiệp vụ
  mới sau lưng Owner.
- **CONSEQUENCE**: số này sẽ **không khớp** cột "Tổng số SP" của báo cáo cũ.
  Chênh lệch đó có hai nguyên nhân đã biết và cần một dòng chú thích trên trang:
  (1) báo cáo cũ có lỗi công thức A1 (số SP bị trừ nhầm một tỉ lệ phần trăm nên
  không nguyên); (2) cách đếm dòng phí chưa được định nghĩa.

## (15) PROPOSED_TOUCH_AREA

Tất cả đều nằm **quanh** phần persistence đã có, không đi vào trong nó.

**File mới (2):**

| File | Vai trò | Ghi chú kiến trúc |
|---|---|---|
|  `app/web/analytics_queries` (module .py mới) | Toàn bộ SQL/aggregation của PRA-003 | Nhận một `Engine` (đã có sẵn qua `SnapshotRepository.engine`, `history_store.py:375`). **Không** import `app/modules/*` ngoài không có. Không business rule mới — chỉ `SUM`/`COUNT`/`GROUP BY` trên các cột engine đã ghi. |
|  `app/web/analytics_presentation` (module .py mới) | Presentation model + định dạng + nhãn nguồn | Không có phép tính nghiệp vụ nào; cùng kỷ luật với `legacy_presentation.py`. Dùng lại `legacy_presentation.format_number` (thuần định dạng, trung lập nguồn) thay vì nhân bản — có comment nói rõ vì sao. |

**File sửa (4):**

| File | Delta | Ghi chú |
|---|---|---|
| `app/web/server.py` | +1 route `GET /tong-quan`; `GET /nhan-vien` nhận tham số `nguon`; 1 helper parse kỳ | Đường legacy hiện tại **không đổi hành vi** khi không có `nguon`. |
| `app/web/templates/layout.html` | +1 tab nav "Tổng quan" | 1 dòng. |
| `app/web/templates/nhan_vien.html` | + bộ chuyển nguồn + bảng pipeline | Nhánh legacy giữ nguyên từng dòng. |
| `app/web/static/css/tinphat-ui.css` | + lưới thẻ KPI, `.tag-pipeline` | Dùng lại `--tp-*` token, `.module`, `.summary-grid`, `.tag` sẵn có. |

**File mới (template, 2):** `tong_quan.html`, `_pipeline_bits.html` (macro
badge/ô, đối xứng với `_legacy_bits.html`).

**KHÔNG chạm:**
`tools/db/**` · `app/history/**` · `app/web/history_store.py` ·
`app/web/history_writer.py` · `app/web/run_registry.py` ·
`app/modules/**` (toàn bộ engine, exporter, validator, pricing) ·
`config/**` (trừ khi Owner chọn D2-B) · `alembic.ini` · `render.yaml` ·
`Dockerfile` · Tracking · `app/demo.py` · `app/owner_launcher.py`.

`PROTECTED_CORE_IMPACT = NONE`. `TRACKING_CHANGE_REQUIRED = NO`.

**Vì sao không refactor gì cả** (§13 chỉ thị): `SnapshotRepository` đã phơi
`engine` dưới dạng property, nên module truy vấn mới cắm vào được mà không cần
sửa một dòng nào của module đã qua Independent Review E2 ở S092. Kiến trúc hiện
tại đỡ được vertical này nguyên vẹn — không có lý do kỹ thuật nào để đề xuất
refactor.

## (16) SCHEMA_MIGRATION_IMPACT

```text
SCHEMA_CHANGE      = NONE
MIGRATION_ADDED    = NONE
ALEMBIC_HEAD       = 0002_snapshots (KHÔNG đổi)
INDEX_ADDED        = NONE
BACKFILL           = NONE
DATA_MIGRATION     = NONE
```

Toàn bộ 12 ô của Tổng quan và 10 cột của bảng Nhân viên đọc được từ các cột đã
tồn tại. Index sẵn có đủ dùng: `ix_order_line_current_sale_date` phục vụ lọc
kỳ; join `order_line_current → order_line_result_version` và
`→ order_line_source_version` đều đi qua khoá chính. `GROUP BY
employee_normalized` không có index riêng — với quy mô thật (61 dòng của ca
production, 351 dòng của golden, ~12k dòng của workbook lớn nhất từng gặp) đó
là một sequential scan vài mili-giây; thêm index bây giờ là tối ưu hoá suy đoán.

**Điều kiện mở lại**: nếu đo được trang > 1 giây trên tập ≥12k dòng
(CHECK-06 mục 18), khi đó mới xét index — có số đo trước, không thêm trước.

## (17) ESTIMATED_CHANGE_BUDGET

Ngân sách riêng của PRA-003, **không** kế thừa 40 LOC còn lại của PRA-002.
Theo cùng quy ước đo của TASK-PRA-002 mục 17 (Python production tách riêng
template/CSS/test).

```text
Python production mới/sửa
  app/web/analytics_queries.py          ≈ 130      (mục tiêu)
  app/web/analytics_presentation.py     ≈  90
  app/web/server.py (delta)             ≈  55
  ---------------------------------------------
  MỤC TIÊU                              ≈ 275 dòng
  DỪNG CỨNG                               400 dòng  → vượt = CHANGE_BUDGET_EXCEEDED,
                                                      dừng, Owner quyết

Template mới/sửa                        ≤ 220 dòng
  tong_quan.html          ≈ 95
  _pipeline_bits.html     ≈ 40
  nhan_vien.html (delta)  ≈ 60
  layout.html (delta)     =  1

CSS thêm                                ≤  25 dòng
Test mới                                ≥  30 test (không skip mới)
Dependency mới                          = 0  (sqlalchemy/flask/jinja đã có)
Schema / migration                      = 0
Config mới                              = 0  (trừ khi Owner chọn D2-B: +1 file YAML)

Hardening (90/10)                       ≤ 10% và CHỈ sau khi mọi CHECK REQUIRED PASS.
  Ứng viên DUY NHẤT: đo và ghi thời gian tải trang trên tập ≥12k dòng.
  Không ứng viên nào khác được thêm trong phiên implement.

Effort                                  1 session MAJOR implement
                                        + 1 Independent Review
                                        + ≤1 repair cycle
```

**Review budget** (V4.1 §2): `effective_risk` của PRA-003 = **MEDIUM** → **1
blocking repair cycle**. Lý do chấm MEDIUM theo failure path (V4.1 §4, không
theo tên file): đường hỏng tệ nhất của PRA-003 là *hiển thị sai một con số quản
lý* (ví dụ cộng cả dòng PENDING vào LN KPI, hoặc hiện `0` thay vì trống cho kỳ
trước). Hậu quả là một quyết định quản lý sai — nghiêm trọng, nhưng **không**
ghi đè dữ liệu, **không** đổi KPI/lương đã tính, **không** double-count (bất
biến đó thuộc PRA-002 và PRA-003 chỉ đọc). Đây là tầng chỉ-đọc: không có
INSERT/UPDATE/DELETE nào trong toàn bộ touch area. Vì vậy MEDIUM, không HIGH.

## (18) TEST_PLAN

Ba tầng, dùng lại nguyên hạ tầng test đã có — không dựng khung mới.

**Tầng 1 — `tests/test_analytics_queries` — file .py mới (unit, SQLite in-memory).**
Dựng dữ liệu bằng chính factory `_presented()` của
`tests/test_web_history.py` (đã hỗ trợ đặt `status`, `purchase`, `kpi`,
`sale_date`, `employee`), rồi ghi qua `history_writer.write_run_history`.

| # | Test | Khẳng định |
|---|---|---|
| T1 | `period_totals` trên hai snapshot chồng ngày | tổng bằng đúng snapshot rộng — không double-count |
| T2 | LN KPI chỉ cộng dòng `AUTO` | dòng PENDING có `eligible_kpi_profit` ≠ NULL **không** vào tổng |
| T3 | coverage LN KPI | `auto_lines / total_lines` đúng cả khi = 0 |
| T4 | LN kế toán bỏ qua `NULL` | tổng ≠ 0 khi mọi dòng NULL → trả `None`, KHÔNG trả `Decimal(0)` |
| T5 | AUTO/Review theo ĐƠN | đơn có 1 dòng AUTO + 1 dòng PENDING → đếm là Review, không phải nửa đơn |
| T6 | dòng `sale_date IS NULL` | không vào bất kỳ kỳ nào **và** được đếm riêng |
| T7 | `period_bounds` | min/max đúng; DB rỗng → `None`, không ném lỗi |
| T8 | danh sách tháng | chỉ tháng thực sự có dòng hiện hành |
| T9 | `employee_totals` | tổng các dòng nhân viên = tổng của `period_totals` cùng kỳ |
| T10 | nhân viên `NULL` | thành dòng "Chưa xác định", không bị bỏ và không gộp vào ai |
| T11 | đơn có hai nhân viên | đếm ở cả hai dòng, tổng đơn của trang vẫn `COUNT(DISTINCT)` |
| T12 | dòng SOURCE_CHANGED | chỉ version hiện hành được cộng |

**Tầng 2 — `tests/test_web_analytics` — file .py mới (route, Flask test client).**

| # | Test | Khẳng định |
|---|---|---|
| T13 | `GET /tong-quan` 200 | render với dữ liệu thật đã ghi |
| T14 | không cấu hình history | 503 + thông báo "chưa có nơi để đọc", KHÔNG phải "chưa có dữ liệu" |
| T15 | kỳ trước trống | trang chứa "chưa có dữ liệu kỳ trước", **không** chứa `0%` ở ô so sánh |
| T16 | không có PII | body không chứa tên/SĐT/địa chỉ khách của fixture |
| T17 | không lộ nội bộ | body không chứa `snapshot_id`, `run_id`, đường dẫn tuyệt đối, secret |
| T18 | `GET /nhan-vien` không tham số | **byte-tương đương** trang legacy hiện tại (bảo vệ non-regression PRA-001) |
| T19 | `GET /nhan-vien?nguon=moi` | bảng pipeline, badge `SỐ MỚI` |
| T20 | hai nguồn không trộn | trong một `<table>` không bao giờ có cả `LEGACY` lẫn `SỐ MỚI` |
| T21 | `nguon` giá trị lạ | rơi về legacy, không 500 |
| T22 | không tính toán trong template | grep: `tong_quan.html`/`nhan_vien.html` không chứa toán tử số học trên biến tiền |
| T23 | ô trống hiện `—` | không nơi nào hiển thị `0` cho một giá trị `None` |

**Tầng 3 — `tests/test_pra003_golden_vertical` — file .py mới (integration, oracle độc lập).**
Dùng lại nguyên khuôn `tests/test_pipeline_history_vertical.py`: chạy pipeline
thật trên `tests/fixtures/golden/period_2026_01.xlsx`, ghi lịch sử, rồi truy
vấn.

| # | Test | Oracle |
|---|---|---|
| T24 | `orders` | `expected/period_2026_01.json` → `counts.orders = 254` |
| T25 | `lines` | `counts.lines = 351` |
| T26 | `quantity` | `money.quantity_total = 407` |
| T27 | doanh thu | `money.sales_normalized = 3562310000` |
| T28 | LN KPI | fixture golden có `pricing.price_source_distribution = {Pending: 351}` → tổng LN KPI = `None`, coverage `0/351`, hiển thị `—` |
| T29 | LN kế toán | tương tự T28 — `None`, KHÔNG `0` |
| T30 | bảng Nhân viên | khớp `employees` block: `Tín Phát` 254 đơn / 351 dòng / SL 407 / doanh thu 3.562.310.000 |

**Giới hạn đã biết của oracle golden — phải nói ra, không được lờ đi:**
fixture golden đã ẩn danh về **một** nhân viên (`employees` chỉ có
`"Tín Phát"`) và **mọi** dòng đều `price_source = Pending`. Vì vậy golden
**không thể** làm oracle cho phân rã nhiều nhân viên hay cho bất kỳ con số lợi
nhuận nào. Hai vùng đó do tầng 1 (dữ liệu tổng hợp có kiểm soát) phủ. Không
được dựng một fixture "giống production" rồi gọi nó là bằng chứng thật.

**Không hồi quy**: Golden Baseline giữ `58 passed, 2 skipped`; full suite không
giảm; `validate_*` giữ nguyên trạng thái hiện tại (kể cả 3 issue
`reference_integrity` đã biết của REM-T06 — DEFER, không sửa trong PRA-003).

## (19) ACCEPTANCE_ORACLE

```text
O1  Golden 01/2026, kỳ "Toàn bộ": orders=254 · lines=351 · quantity=407 ·
    doanh thu=3.562.310.000
    → nguồn: tests/fixtures/golden/expected/period_2026_01.json
      (counts.orders, counts.lines, money.quantity_total, money.sales_normalized)
    → oracle ĐỘC LẬP với PRA-003: file này do TASK-GOLDEN-BASELINE-001 sinh ra
      trước khi PRA-003 tồn tại.

O2  Cùng kỳ đó: LN KPI = "—" (coverage 0/351) và LN kế toán = "—".
    → Không có ô nào hiện 0. Đây là oracle về TÍNH TRUNG THỰC, không phải về số.

O3  Bảng Nhân viên cùng kỳ: đúng 1 dòng "Tín Phát" khớp block `employees`
    của cùng file JSON; dòng TỔNG bằng O1.

O4  Bất biến nội bộ: với MỌI kỳ, Σ(các dòng nhân viên) == period_totals cùng kỳ,
    trên cả 5 chỉ tiêu cộng được (dòng, số lượng, doanh thu, LN KPI, LN kế toán).
    Đơn KHÔNG cộng được (một đơn có thể thuộc hai nhân viên) — bất biến này
    KHÔNG áp cho cột Đơn, và trang phải nói rõ điều đó.

O5  Bất biến no-double-count: upload sổ A (nửa kỳ) rồi sổ B (cả kỳ)
    → Tổng quan kỳ đó == upload mình sổ B.
    → Tái dùng nguyên kịch bản của tests/test_pipeline_history_vertical.py.

O6  Production 2026-09-01→03, kỳ "Tháng 09/2026":
      orders = 40 · lines = 61 · AUTO(đơn) = 15 · Review(đơn) = 25
      → ĐÃ QUAN SÁT trên production (S093). Đây là oracle thật.
      So tháng trước = TRỐNG.
      Tiền và số lượng: Owner đọc trên production sau deploy —
      KHÔNG đặt giá trị kỳ vọng trong phiên này.

O7  Không hồi quy: GET /nhan-vien (không tham số) cho ra đúng trang legacy
    như trước; Golden Baseline 58 passed / 2 skipped; full suite không giảm.
```

## (20) OUT_OF_SCOPE

Nhắc lại nguyên văn ranh giới, cộng những thứ phiên này chủ động cắt:

- Drill-down đơn hàng, drill-down dòng hàng, trang chi tiết một đơn → **PRA-004**.
- Review Queue vận hành, nhóm lý do Review, nút "đã xem" → **PRA-004**.
- Phân tích theo sản phẩm canonical, Pareto, sales mix → **PRA-005**.
- Doanh số quy đổi, margin, target/so target, YTD, cùng kỳ năm trước, AOV, xu
  hướng nhiều tháng → **LATER** theo TASK-PRA-000 §L (giữ nguyên bởi DEC-166).
- Biểu đồ (chart) → chỉ bảng ở slice này; §M SLICE 3 đã DEFER sẵn.
- Bảng đối chiếu lệch legacy ↔ pipeline → **cắt khỏi slice 1** vì chưa có
  (tháng × nhân viên) nào tồn tại ở cả hai nguồn (mục 8).
- Bộ chọn khoảng ngày tự do, quý, năm, "hôm nay/tuần này" → DEFER (mục 10).
- Ingestion mới, service/worker/queue, đổi Render/PostgreSQL/R2/Cloudflare,
  refactor kiến trúc, đổi Tracking, sửa PRA-002, sửa REM-T06, hardening suy
  đoán, Tkinter, design system → **cấm tuyệt đối** theo chỉ thị mục 17.

## (21) SCOPE_DRIFT_CHECK

```text
SCOPE_DRIFT = NO

Đối chiếu từng ranh giới của chỉ thị:
  implement code                     : KHÔNG — 0 dòng production
  modify Tracking                    : KHÔNG
  change PRA-002                     : KHÔNG — không file nào của PRA-002 bị chạm
  repair deferred findings / REM-T06 : KHÔNG
  start PRA-004 / PRA-005            : KHÔNG — đã liệt kê là out-of-scope
  add detailed orders/products       : KHÔNG
  add Review workflow                : KHÔNG
  add new ingestion                  : KHÔNG
  redesign architecture              : KHÔNG — 2 file mới cắm vào Engine đã phơi sẵn
  add service/worker/queue           : KHÔNG
  change infra                       : KHÔNG
  refactor unrelated modules         : KHÔNG
  harden speculative cases           : KHÔNG — chỉ 1 ứng viên hardening, có điều kiện đo

Kế hoạch HẸP HƠN TASK-PRA-000 §M SLICE 3 ở ba chỗ, đều có lý do dữ liệu:
  (a) bỏ trang chi tiết một nhân viên → theo ngày → đơn  (là drill-down = PRA-004)
  (b) bỏ bảng đối chiếu lệch legacy/pipeline             (chưa có kỳ chồng nhau)
  (c) bỏ target/so target                                 (không có dữ liệu — D2)
Ba chỗ này KHÔNG phải scope drift theo hướng mở rộng; chúng là thu hẹp có
bằng chứng. Nếu Owner muốn giữ (a)/(b)/(c) trong slice 1, đó là quyết định của
Owner và ngân sách mục 17 phải được tính lại.

90/10: 100% ngân sách phiên này dùng cho discovery của kết quả quản lý thật;
hardening được giới hạn ≤10% và chỉ mở sau khi mọi CHECK REQUIRED PASS.
Finding của phiên này KHÔNG tạo task mới nào.
```

## (22) IMPLEMENTATION_READY

```text
IMPLEMENTATION_READY = YES

Điều kiện đã thoả:
  [x] Canonical xác minh, không moved (facf090c…)
  [x] PRA-002 = DONE và đã tích hợp vào canonical
  [x] PRA-001 = DONE, đường legacy được bảo toàn nguyên vẹn bởi thiết kế
  [x] Mọi ô của slice truy được về một cột đã tồn tại — không có ô nào
      "chờ dữ liệu"
  [x] Không schema, không migration, không dependency, không config mới
  [x] Không chạm bất kỳ file nào của protected core hay của PRA-002
  [x] Oracle nghiệm thu độc lập đã có sẵn (golden expected JSON) +
      1 oracle production thật (đếm đơn/dòng/AUTO/Review)
  [x] Ngân sách thay đổi riêng, nhỏ, có mức dừng cứng
  [x] Review budget xác định: MEDIUM = 1 blocking repair cycle (V4.1 §2)

Điều kiện CHƯA thoả (không chặn bắt đầu):
  [ ] D1/D2/D3 — Owner có thể xác nhận default hoặc ghi đè. Phiên implement
      chạy được với default đã ghi ở mục 14.
  [ ] Task file docs/tasks/TASK-PRA-003-*.md chưa tồn tại; Completion Gate
      chưa FROZEN. Đây là bước Roadmap Finalization, thuộc phiên kế tiếp —
      KHÔNG được freeze gate trong một phiên discovery.
  [ ] Lineage PRA-003 chưa mở trong PROJECT/REVIEW_BUDGET_LEDGER.md.
```

## (23) NEXT_VERTICAL_ACTION

```text
BƯỚC 1 (Owner, ~5 phút)
  Xác nhận hoặc ghi đè D1 / D2 / D3 (mục 14). Im lặng = chấp nhận
  RECOMMENDED_DEFAULT: LN KPI là số chính + LN kế toán là cột phụ, cả hai kèm
  coverage; KHÔNG có target ở slice 1; ô số lượng là "Tổng số lượng (mọi dòng)".

BƯỚC 2 (phiên Roadmap Finalization, docs-only)
  Viết docs/tasks/TASK-PRA-003-tong-quan-nhan-vien.md từ chính tài liệu này:
  Scope Lock, Ready Gate, Completion Gate (dự kiến 12–14 check, ~10 REQUIRED,
  Risk 3 → E1), Exit Criteria, Change Budget mục 17. FREEZE gate.
  Mở lineage TASK-PRA-003 trong PROJECT/REVIEW_BUDGET_LEDGER.md:
  effective_risk = MEDIUM, allowed = 1, used = 0, base_sha = SHA lúc mở.

BƯỚC 3 (1 phiên MAJOR implement)
  analytics_queries → analytics_presentation → routes → template → CSS,
  theo đúng thứ tự đó, test tầng 1 viết trước tầng 2/3.

BƯỚC 4 (Independent Review)
  Reviewer chạy lại tầng 3 (oracle golden) độc lập; ≤1 repair cycle.

BƯỚC 5 (Owner, trên production)
  Chọn "Tháng 09/2026" trên Tổng quan; đối chiếu 40 đơn / 61 dòng /
  AUTO 15 / Review 25; xác nhận ô "so tháng trước" TRỐNG chứ không phải 0.
  Đó là Production Acceptance của PRA-003.

KHÔNG làm trong bước nào ở trên: PRA-004, PRA-005, migration, ingestion mới,
đổi Tracking, đổi hạ tầng.
```

---

## Phụ lục — Bằng chứng thực thi của phiên (E1)

```text
git remote show origin                → HEAD branch: claude/extract-upload-repo-gq2ws4
git ls-remote origin <default>        → facf090c782b022730ecc5f1cf0d0b02e29ca8d7
git rev-parse HEAD                    → facf090c782b022730ecc5f1cf0d0b02e29ca8d7
scripts/branch_authority_check.sh     → DEFAULT_TIP == HEAD_SHA; WORKTREE = CLEAN;
                                        STOP vì nhánh phiên chưa có upstream (dự kiến)
git log --oneline -8 origin/<default> → facf090 = "TASK-PRA-002 S093 closeout:
                                        CHECK-PRA002-15 = PASS, TASK = DONE"
```

Không chạy test suite trong phiên này: phiên không sửa một dòng code nào, nên
không có gì để hồi quy. Số liệu Golden (`58 passed, 2 skipped`) và full suite
được trích từ bản ghi S092/S093, có ghi rõ nguồn — không tuyên bố là đã chạy lại
ở đây.
