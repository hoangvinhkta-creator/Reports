# R3 — Từ nhập sổ tới bảng nhân viên, xuất Excel và chốt kỳ

## Metadata

Status:
IMPLEMENTED

Current Status Reason:
Toàn bộ năm việc của R3 đã triển khai và có test đi hết chuỗi, gồm một lần
đối soát trên hai kỳ nghiệp vụ THẬT (đã ẩn danh). Sau đó Independent Review
tìm ra HAI finding trên vân tay chốt kỳ (`FIND-R3-IR-01` false negative,
`FIND-R3-IR-02` false positive) — cả hai đã sửa TẬN GỐC, chi tiết ở §7b.
`CHECK-R3-01` … `CHECK-R3-18` PASS (bằng chứng ở §7 và ở
`docs/sessions/S129-r3-nhap-so-den-chot-ky.md`). Hai check còn lại KHÔNG do
phiên triển khai quyết định và vẫn `NOT_TESTED`: `CHECK-R3-19` (Independent
Review) và `CHECK-R3-20` (Owner nghiệm thu trên production). Cùng kỷ luật đã
áp cho R1 và R2 — không tự tuyên bố Independent Review hay Owner Acceptance —
nên task DỪNG ở `IMPLEMENTED`.

Phase:
PHASE-01 — Engine tính toán

Task Mode:
MAJOR

Primary Agent Tier:
C

Escalation Tier:
C

Difficulty:
4/5

Risk:
4/5

Blast Radius:
5/5 (V4.1 §4 — chấm theo failure path: `khoá dòng khi nạp lại → quyết định
của Owner gắn vào dòng nào → giá nhập KPI hiệu lực → EligibleKpiProfit →
DS quy đổi → KPI/lương`, và thêm một nhánh mới: `bộ số đã chốt`)

Effective Risk:
HIGH (Blast Radius quyết định, không phải Risk cục bộ — V4.1 §4.1)

Project Profile:
PRODUCT

Review Budget lineage:
**Đề xuất `R3` là root lineage RIÊNG**, `2 allowed / 0 used / 2 remaining` —
cùng cách đọc đã dùng cho `R1` và `R2` (xem `PROJECT/REVIEW_BUDGET_LEDGER.md`
→ "Root Task: R3"). R3 KHÔNG sửa tiếp triển khai của R2; nó xây tiếp trên một
R2 đã merge vào nhánh mặc định. Không repair cycle nào bị tiêu trong phiên
triển khai này.

Owner Authority:
Chỉ thị R3 của Owner (bàn giao tiếp từ R2), năm việc ở §2. Nền đã merge:
`R2` (`45f0e1b`, PR #7) trên nhánh mặc định `claude/extract-upload-repo-gq2ws4`.
Quyết định nghiệp vụ được R3 THỰC THI chứ không tạo mới: `OD-105B-01` §3
(dòng phụ giá nhập `0` BY DEFINITION), `OD-1`/`OD-2`/`OD-4` (số lượng, hoàn/
trả, giá bán 0), `DEC-114`/`DEC-143` (công thức), `DEC-180` (chiết khấu),
`DEC-PHB02-02`/`-08` (giá nhập tay, không gian làm việc), `ADR-110` (thẩm
quyền giá MIN theo ngày bán — KHÔNG bị R3 sửa).

---

## 1. Ranh giới đã được Owner nói thẳng

> Phạm vi không có giá thực nhập. Mọi màn hình và file xuất phải dùng cùng
> một giá nhập KPI hiệu lực: MIN đúng ngày hoặc giá tay.

R3 vì thế KHÔNG xây một nguồn giá thứ ba. Nó làm cho MỘT giá nhập hiệu lực đã
có đi tới được mọi nơi cần nó — kể cả file rời khỏi hệ thống — và cho phép
đóng lại một kỳ khi bộ số ấy đã được duyệt.

Hai câu ràng buộc còn lại của chỉ thị, và cả hai đều đã thành hành vi kiểm
được:

> Đơn vắng trong file tải sau không tự bị xóa/hủy.
> Nếu nguồn không có ID dòng ổn định và không thể ghép chắc chắn, đưa vào xử
> lý ngoại lệ.

---

## 2. Năm việc, và điều mỗi việc thật sự sửa

### §1 — Import / idempotency / khoá dòng

**Lỗi:** `occurrence_index` được đánh theo VỊ TRÍ dòng trong file
(`extraction.build_source_lines`: sắp theo `source_row` rồi đếm 1..n trong
`(order_key, product_key)`). Ổn định khi và chỉ khi thứ tự dòng không đổi —
một điều kiện mà không gì bảo đảm, vì file là workbook kế toán sửa tay.

**Hệ quả, tái hiện được:** một đơn có hai dòng cùng tên hàng (sổ gốc có —
`extraction` đã ghi rõ ví dụ "Chi phí vận chuyển"). Owner gõ giá nhập cho dòng
thứ nhất. Lần nạp sau hai dòng đổi chỗ; dòng vật lý thứ hai nhận
`occurrence_index = 1` và giá nhập lặng lẽ chuyển sang nó. Không cờ nào bật.

**Sửa:** `app/history/line_binding.py` — ba mỏ neo theo thứ tự sức mạnh
`IMEI` → `FINGERPRINT` → vị trí, và vị trí CÓ ĐIỀU KIỆN (§3.1 dưới).

### §2 — Loại dòng và công thức

**Lỗi:** đường báo cáo đối xử với bốn thứ rất khác nhau như nhau — một chiếc
tủ lạnh bán ra, một khoản chiết khấu, một khoản phí vận chuyển, một món phụ
kiện tặng kèm — rồi dán `Missing.PurchasePrice` cho cả bốn.

**Hệ quả đo được trên sổ thật:** 22 dòng (kỳ 01/2026) và 14 dòng (kỳ 06/2026)
không có giá nhập để tra và sẽ không bao giờ có. Chúng khoá
`PROFIT_COVERAGE` dưới 100 % VĨNH VIỄN, tức khoá luôn trạng thái `OFFICIAL`
của cả kỳ, vì một lý do không ai sửa được bằng bất kỳ thao tác nào.

**Sửa:** `app/modules/reporting/line_type.py` — sáu loại dòng, và luật giá
nhập của `OD-105B-01` §3 áp cho đúng hai loại có thẩm quyền. Đây chính là
tầng policy mà `TASK-105B-Q3` bị `BLOCKED_BY [TASK-103]` chờ, đặt ĐÚNG chỗ
mà `OD-105B-01` §C yêu cầu: BÊN TRÊN provider, không nằm trong
`FilePriceProvider`.

### §3 — Một effective data cho mọi màn hình

**Lỗi tiềm tàng:** mỗi phép chiếu của kỳ (`for_employee`, `for_sheet`) dựng
lại một `PeriodData` mới bằng tay, nên mỗi lần thêm một lớp phủ là một lần
phải nhớ chở nó qua cả hai — và lần quên đầu tiên là một màn hình con nói
khác màn hình cha về cùng một dòng.

**Sửa:** một hàm `_slice()` dùng chung, và ba lớp phủ mới của R3 đọc MỘT lần
cùng lượt với override giá nhập.

### §4 — Xuất Excel

**Lỗi:** đường xuất duy nhất (`excel_exporter` ← `ImportResult`) là ảnh chụp
trạng thái TRƯỚC mọi quyết định của Owner. Từ PHB-03, thứ Owner nhìn trên màn
hình được hợp nhất LÚC ĐỌC; file xuất từ kết quả pipeline vì thế trông đầy đủ,
cân, và nói một bộ số KHÁC — loại sai nguy hiểm nhất, vì không có gì trong
file báo rằng nó cũ.

**Sửa:** `app/modules/exporting/business_export.py` đọc `PeriodData`.

### §5 — Chốt kỳ / phiên bản

**Khoảng trống:** không có cách nào nói "bộ số tháng này đã được duyệt", nên
không có ranh giới nào giữa "đang làm" và "đã xong", và một lần sửa sau khi
báo cáo đã gửi đi không để lại dấu vết nào.

**Sửa:** `app/web/period_lock.py` + bảng `period_close`.

---

## 3. Quyết định thiết kế và LÝ DO

### 3.1. Vị trí chỉ được dùng làm mỏ neo khi dùng SAI nó không hại gì

Ghép sai theo vị trí gây hại ĐÚNG khi một quyết định của người đang treo trên
khoá bị ghép sai. Nếu không khoá nào trong nhóm mang quyết định nào, hai cách
ghép cho ra hai lịch sử version khác nhau nhưng KHÔNG khác nhau một đồng nào.

Vì vậy:

```text
còn ĐÚNG một dòng vào và ĐÚNG một khoá trống    → ghép (không có gì để nhầm)
không khoá trống nào mang quyết định của người  → ghép theo thứ tự (vô hại)
còn lại                                         → NGOẠI LỆ, không đoán
```

Bắt mọi lần đổi thứ tự dòng thành một "ngoại lệ" sẽ tạo ra nhiễu tới mức Owner
học cách bấm bỏ qua — và khi đó ngoại lệ THẬT cũng bị bỏ qua theo. Đây là lý
do phép kiểm hỏi "có quyết định nào đang treo không", chứ không hỏi "có mơ hồ
không".

### 3.1b. "Đã xử lý" KHÔNG chuyển quyết định sang khoá mới

Nút `ĐÃ XỬ LÝ` của hàng đợi `gan-dong` chỉ ghi rằng người đã nhìn và đã quyết
— bằng chính các thao tác sẵn có (gõ lại giá nhập cho khoá mới, loại dòng cũ
khỏi báo cáo, hoặc không làm gì vì dòng cũ đúng là đã biến mất khỏi sổ).

Một nút "chuyển quyết định sang khoá mới" sẽ là ĐÚNG phép đoán mà cả cơ chế
này sinh ra để từ chối, chỉ khác là lần này có một cú bấm đứng ra chịu trách
nhiệm. Nó không tồn tại, và sẽ không.

### 3.2. Nhánh ngoại lệ KHÔNG xoá và KHÔNG hủy khoá cũ

Dòng vào nhận khoá MỚI (chỉ số nối tiếp sau chỉ số lớn nhất đã dùng); khoá cũ
chỉ VẮNG MẶT ở snapshot này, đúng cơ chế `absent_keys` đã nghiệm thu ở
PRA-002 slice B. Đó cũng chính là câu trả lời cho ràng buộc "đơn vắng trong
file tải sau không tự bị xóa/hủy".

### 3.3. Giá nhập theo chính sách đứng CUỐI, không đứng đầu

```text
1. người gõ tay          manual_purchase_price     DEC-PHB02-02
2. nguồn giá tự động     auto_purchase_price       ADR-110 (MIN theo ngày bán)
3. chính sách loại dòng  policy_purchase_price     OD-105B-01 §3
```

Nếu một nguồn giá thật trả lời được cho một dòng phí, con số thật đó THẮNG con
số 0 của chính sách. Chính sách là chỗ dựa khi không ai trả lời, không phải
một lệnh ghi đè.

### 3.4. `0` theo chính sách ≠ `0` thay cho thiếu

`OD-105B-01` §3 viết liền hai câu, và câu thứ hai quan trọng ngang câu đầu:
*"Product line thông thường không có price record: lookup = None → Pending.
Không dùng purchase_price = 0 thay cho missing."*

Vì vậy `policy_purchase_price` trả `Decimal(0)` cho ĐÚNG `FEE` và `DISCOUNT`,
và trả `None` cho mọi loại khác — kể cả `ACCESSORY_GIFT`. Một chiếc giá treo
tivi tặng kèm VẪN tốn tiền mua; ghi giá nhập của nó là 0 sẽ biến một khoản lỗ
có thật thành lãi 0 đồng.

### 3.5. Hoàn/hủy: R3 làm cho sự THIẾU VẮNG nhìn thấy được, không lấp nó

`OD-2` cấm phát minh ngữ nghĩa trả hàng/hoàn tiền. R3 không đảo lại điều đó.
`config/line_types.yaml` khai `BH: SALE` và **để trống** phần hoàn/hủy: repo
không có một quyết định nào của Owner nói `BTL` nghĩa là gì, dù `BTL` có mặt
trong dữ liệu thật (3 dòng kỳ 01/2026, 1 dòng kỳ 06/2026).

Hệ quả: dòng thuộc một tiền tố chứng từ chưa khai nhận
`UNDECIDED_DOCUMENT` + cửa chặn `LINE_TYPE_UNDECIDED`, và đi vào hàng đợi
ngoại lệ `loai-chua-ro`. Nó KHÔNG bị tính như một dòng bán (im lặng SAI) và
KHÔNG bị bỏ khỏi mọi phép gộp (im lặng MẤT).

### 3.6. Chiết khấu: hệ thống NÊU TÊN nguy cơ, không tự sửa

`DEC-180` ghi hai CÁCH GHI của cùng một nghiệp vụ (một dòng âm riêng ở sổ tay
cũ; một cột `discount` ở sổ hiện hành, `DEC-114` đã trừ). Một đơn mang CẢ HAI
là chỗ duy nhất phép trừ có thể xảy ra hai lần.

`discount_double_count_orders` chỉ NÊU TÊN đơn. Hai cách sửa có thật (bỏ cột,
hay bỏ dòng) là hai khẳng định khác nhau về sổ gốc, và không cái nào hệ thống
có thẩm quyền tự chọn. Con số vẫn ra như cũ; Owner nhận một ngoại lệ đọc được.

### 3.7. Chốt kỳ là PHIÊN BẢN, không phải một cột nhị phân

Một kỳ có thể chốt, mở lại vì phát hiện sai, rồi chốt lần nữa. Một cột nhị
phân ghi đè lịch sử đó và câu hỏi "bộ số nào đã được duyệt hồi tháng trước"
mất luôn câu trả lời. Mở lại KHÔNG xoá dòng cũ — nó ghi `reopened_at`/
`reopen_reason` lên chính dòng đó, và LÝ DO là bắt buộc.

### 3.8. Cửa chặn kỳ đã chốt hỏi NGÀY BÁN của dòng, không hỏi kỳ đang xem

Khung nhìn "toàn bộ dữ liệu" không có kỳ, và sửa một dòng của tháng đã chốt từ
màn hình đó vẫn phải bị chặn. Dòng không có `sale_date` rơi ngoài mọi kỳ —
đúng ngữ nghĩa kỳ đã freeze ở PRA-003 — nên không kỳ chốt nào khoá nó.

---

## 4. Scope Lock

### Trong phạm vi

1. Phép gắn dòng khi nạp lại sổ + bảng ngoại lệ + hàng đợi của nó.
2. Loại dòng, luật giá nhập theo chính sách, phát hiện nguy cơ trừ hai lần.
3. Một `PeriodData` chở đủ mọi lớp phủ qua mọi phép chiếu.
4. Xuất Excel từ effective data (kỳ · nhân viên · nhóm).
5. Chốt kỳ có phiên bản + cửa chặn ghi + phát hiện lệch sau khi chốt.
6. Đối soát trên dữ liệu thật khả dụng, test hồi quy, tài liệu bàn giao.

### Ngoài phạm vi

- KHÔNG xây giá thực nhập, KHÔNG thêm một nguồn giá nào.
- KHÔNG sửa công thức MIN của Tracking, KHÔNG sửa `ADR-110`.
- KHÔNG sửa repo `Tracking`.
- KHÔNG định nghĩa ngữ nghĩa hoàn/hủy (`OD-2`).
- KHÔNG khớp lại các lỗi công thức đã biết của workbook cũ
  (`docs/analysis/05_EXCEPTIONS.md`).
- KHÔNG tự tuyên bố Independent Review hay Owner Acceptance.

---

## 5. Thay đổi theo file

| File | Việc |
|---|---|
| `app/history/line_binding.py` | MỚI — ba mỏ neo, ngoại lệ khi không kết luận được |
| `app/web/history_store.py` | gọi phép gắn trong `write_snapshot`, ghi ngoại lệ |
| `app/modules/reporting/line_type.py` | MỚI — sáu loại dòng (THUẦN) |
| `app/modules/reporting/line_type_config.py` | MỚI — nạp YAML (tách khỏi phần thuần) |
| `config/line_types.yaml` | MỚI — từ vựng; phần hoàn/hủy để TRỐNG có chủ đích |
| `app/modules/reporting/business_metrics.py` | `line_type`, `policy_purchase_price`, `PROVENANCE_POLICY_ZERO`, `discount_double_count_orders` |
| `app/modules/reporting/profit_gate.py` | `BLOCK_LINE_TYPE_UNDECIDED` |
| `app/web/business_queries.py` | phân loại dòng lúc ĐỌC; `periods_for_product` |
| `app/web/business_service.py` | ba lớp phủ, `_slice()`, API chốt kỳ, API xuất |
| `app/web/period_lock.py` | MỚI — chốt kỳ có phiên bản |
| `app/web/binding_exceptions.py` | MỚI — đọc/đóng hàng đợi ngoại lệ gắn dòng |
| `app/modules/exporting/business_export.py` | MỚI — xuất từ effective data |
| `app/web/business_presentation.py` | `close_summary`, nhãn `POLICY_ZERO` |
| `app/web/server.py` | 3 route mới, 3 hàng đợi mới, 13 cửa chặn kỳ đã chốt |
| `app/web/templates/kinh_doanh_chot_ky.html` | MỚI |
| `app/web/templates/kinh_doanh.html` | hai đường dẫn: TẢI EXCEL · CHỐT KỲ |
| `tools/db/schema.py` | `line_binding_exception`, `period_close` |
| `tools/db/migrations/versions/0009_*.py` | MỚI — ADDITIVE |
| `tools/analysis/r3_reconcile.py` | MỚI — đối soát trên dữ liệu thật |

---

## 6. Bằng chứng trên DỮ LIỆU THẬT

`python3 -m tools.analysis.r3_reconcile`, hai kỳ nghiệp vụ thật đã ẩn danh:

```text
period_2026_01.xlsx — 351 dòng
  loại dòng   SALE 321 · FEE 22 · ACCESSORY_GIFT 5 · UNDECIDED_DOCUMENT 3
  nạp lại cùng file          INSERT 0 · SAME 351 · SOURCE_CHANGED 0 · ngoại lệ 0
  nạp lại ĐẢO THỨ TỰ DÒNG    INSERT 0 · SAME 351 · SOURCE_CHANGED 0 · ngoại lệ 0
                             khoá dòng mới phát sinh: 0
  tổng kỳ 351 == Σ nhân viên 351 == Σ sheet 351
  doanh thu 3.562.310.000 == Σ theo nhân viên
  coverage 24/351 · dòng giá 0 theo chính sách: 22
  file xuất == màn hình: True

period_2026_06.xlsx — 180 dòng
  loại dòng   SALE 163 · FEE 14 · ACCESSORY_GIFT 2 · UNDECIDED_DOCUMENT 1
  nạp lại cùng file          INSERT 0 · SAME 180 · ngoại lệ 0
  nạp lại ĐẢO THỨ TỰ DÒNG    INSERT 0 · SAME 180 · ngoại lệ 0 · khoá mới 0
  tổng kỳ 180 == Σ nhân viên 180 == Σ sheet 180
  coverage 14/180 · dòng giá 0 theo chính sách: 14
  file xuất == màn hình: True
```

**Giới hạn nói ra, không giấu:** hai kỳ golden KHÔNG có đơn nào chứa hai dòng
cùng một mặt hàng (nhóm lớn nhất = 1). Phép đảo thứ tự trên chính chúng vì thế
chỉ chứng minh phép gắn không làm hỏng ca thường. Ca dễ hỏng nhất được dựng
tường minh TRÊN NỀN sổ thật — nhân đôi một dòng phí CÓ THẬT vào cùng đơn, gắn
một giá nhập tay lên dòng thứ nhất, rồi đảo chỗ — và khoá vẫn không trôi
(`tests/test_r3_golden_reconciliation.py::test_a_repeated_item_built_on_the_real_book_survives_a_reorder`).

---

## 7. Completion Gate

| ID | Nội dung | Status | Evidence |
|---|---|---|---|
| `CHECK-R3-01` | Nạp lại CÙNG file: không version nguồn mới, không đếm hai lần | PASS | E1 |
| `CHECK-R3-02` | Nạp lại file ĐẢO THỨ TỰ DÒNG: khoá dòng không đổi | PASS | E1 |
| `CHECK-R3-03` | File SỬA một dòng: khoá giữ nguyên, ra `SOURCE_CHANGED` | PASS | E1 |
| `CHECK-R3-04` | Đơn nhiều hàng và cùng mã lặp: mỗi dòng đúng một khoá | PASS | E1 |
| `CHECK-R3-05` | Không ghép chắc chắn được ⟹ NGOẠI LỆ, không gắn nhầm override | PASS | E1 |
| `CHECK-R3-05b` | Ngoại lệ gắn dòng hiện NGAY TRÊN DÒNG và đóng được, không khoá nào bị đổi | PASS | E1 |
| `CHECK-R3-06` | Đơn vắng ở file sau KHÔNG bị xoá/hủy | PASS | E1 |
| `CHECK-R3-07` | Dòng phí/chiết khấu nhận giá `0` theo `OD-105B-01` §3, có provenance riêng | PASS | E1 |
| `CHECK-R3-08` | Hàng bán thiếu giá VẪN Pending, không thành `0` | PASS | E1 |
| `CHECK-R3-09` | Quà tặng kèm (giá bán 0) vẫn cần giá nhập thật; lỗ hiện ra | PASS | E1 |
| `CHECK-R3-10` | Chiết khấu không trừ hai lần; đơn có nguy cơ được NÊU TÊN | PASS | E1 |
| `CHECK-R3-11` | Hoàn/hủy và chứng từ chưa khai: chặn có tên, vào hàng đợi | PASS | E1 |
| `CHECK-R3-12` | Bảng nhân viên · tổng kỳ · hàng đợi đọc cùng effective data | PASS | E1 |
| `CHECK-R3-13` | Σ sheet == Σ nhân viên == tổng kỳ trên dữ liệu thật | PASS | E1 |
| `CHECK-R3-14` | File xuất mang giá Owner đã sửa, KHÔNG mang giá pipeline cũ | PASS | E1 |
| `CHECK-R3-15` | Đúng MỘT cột `Giá nhập KPI`; ô trống ≠ `0`; provenance đủ | PASS | E1 |
| `CHECK-R3-16` | Tổng trong file khớp giao diện; lệch ⟹ TỪ CHỐI xuất | PASS | E1 |
| `CHECK-R3-17` | Chốt kỳ TỪ CHỐI mọi đường ghi của kỳ; mở lại bắt buộc có lý do | PASS | E1 |
| `CHECK-R3-18` | Chốt kỳ có phiên bản, sống qua restart, phát hiện lệch sau chốt | PASS | E1 |
| `CHECK-R3-18a` | Vân tay chốt kỳ phủ TOÀN BỘ kết quả tài chính đã duyệt | PASS | E1 |
| `CHECK-R3-18b` | Vân tay chỉ phụ thuộc dữ liệu hiệu lực CỦA ĐÚNG KỲ ĐÓ | PASS | E1 |
| `CHECK-R3-19` | Independent Review PASS | NOT_TESTED | — |
| `CHECK-R3-20` | Owner nghiệm thu trên production | NOT_TESTED | — |

Lệnh và output nguyên văn: `docs/sessions/S129-r3-nhap-so-den-chot-ky.md` §5.

---

## 7b. Repair sau Independent Review — `FIND-R3-IR-01` và `-02`

Cả hai finding nằm trên CÙNG một hàm (`period_lock.content_fingerprint`) và
hỏng theo hai chiều NGƯỢC NHAU. Cả hai đã sửa tận gốc; không `ACCEPTED_RISK`
mới nào phát sinh, không migration mới (schema không đổi), không đụng công
thức MIN, không thêm fallback, không sửa Tracking.

### `FIND-R3-IR-01` — ACCEPTED. Vân tay false negative

**Nguyên nhân.** Payload chỉ có sáu trường: `order_key`, giá nhập hiệu lực,
provenance, lợi nhuận KPI, nhân viên, loại dòng. Nó MÙ với phần lớn kết quả
tài chính đã được duyệt — không tỉ lệ quy đổi, không DS quy đổi, không doanh
thu, không số lượng/đơn giá/chiết khấu, không cả bản chụp chỉ tiêu; và danh
tính dòng thiếu `product_key`/`occurrence_index`, nên hai dòng khác nhau của
cùng một đơn cho ra hai khối byte GIỐNG HỆT.

**Ca tái hiện (đo được, không phải giả định).** Owner tick Gia dụng cho một
mặt hàng của nhân viên Nội thành. Tỉ lệ quy đổi đi 2 % → 8 %; DS quy đổi rơi
từ `150.000.000` xuống `37.500.000`. Lợi nhuận KPI KHÔNG đổi — và đó chính là
lý do payload cũ không thấy gì. `period_drift` trả `False`.

**Sửa.** Payload mới có hai phần, và cả hai đều là thứ người duyệt đã nhìn:

```text
1. bản chụp chỉ tiêu SẼ ĐƯỢC LƯU (`snapshot_of`), JSON khoá đã sắp
2. 19 trường của TỪNG DÒNG, năm nhóm:
     danh tính  order_key · product_key · occurrence_index · sale_date
     đầu vào    quantity · sell_price · discount · total_sales
     giá vốn    purchase_price · purchase_provenance
     kết quả    kpi_profit · conversion_rate · converted_sales · profit_blockers
     quy thuộc  employee · employee_group · employee_provenance
                · line_type · product_group
```

`totals` đi vào CẢ bản chụp lẫn vân tay từ CÙNG một biến (`close_period`), nên
hai thứ đó không thể trôi khỏi nhau.

**Thứ tự canonical.** Các dòng được SẮP theo khoá dòng đầy đủ trước khi băm,
và `totals` serialize với `sort_keys=True`. `raw_lines` hôm nay trả về theo
`(sale_date, order_key, occurrence_index)`, nhưng vân tay KHÔNG được phụ thuộc
chi tiết đó — đổi một mệnh đề `ORDER BY` là một thay đổi kỹ thuật và không
được biến thành "bộ số đã duyệt đã đổi".

`Decimal` đi qua `normalize()`: `2.0` và `2` là CÙNG một tỉ lệ, và một lần đổi
cách viết số trong database không được thành drift.

### `FIND-R3-IR-02` — ACCEPTED. Vân tay false positive giữa các kỳ

**Nguyên nhân.** `close_period` và `period_drift` cùng cộng
`len(store.purchase_price_overrides())` vào payload — số override của TOÀN
DATABASE, không của kỳ đang chốt.

**Ca tái hiện.** Tháng 01 đã chốt. Owner gõ một giá tay cho một dòng THÁNG 02.
Không một dòng nào của tháng 01 đổi, `totals` tháng 01 không đổi — nhưng
`period_drift(2026-01)` trả `True`.

**Sửa.** Gỡ hẳn phụ thuộc toàn cục, và KHÔNG có gì thay chỗ nó. Giá nhập HIỆU
LỰC cùng provenance của TỪNG DÒNG đã nói đủ về mọi quyết định có ảnh hưởng tới
kỳ này; một quyết định không chạm dòng nào của kỳ thì theo định nghĩa không
đổi bộ số của kỳ, và vân tay phải im lặng đúng như vậy.

### Test tái hiện — ĐỎ trước sửa, XANH sau sửa

`tests/test_r3_ir_repair_fingerprint.py` (13 bài). Chạy trên `8aa6626`
(HEAD trước repair):

```text
FAILED ...::TestTheFingerprintCoversTheWholeApprovedResult::test_a_conversion_rate_change_is_drift
FAILED ...::TestTheFingerprintCoversTheWholeApprovedResult::test_a_revenue_change_is_drift_even_when_the_old_fields_hold
FAILED ...::TestTheFingerprintDependsOnlyOnItsOwnPeriod::test_a_manual_price_in_february_never_drifts_january
FAILED ...::TestTheFingerprintIsStable::test_the_payload_does_not_depend_on_query_order
FAILED ...::TestTheDriftWarningThroughTheWeb::test_the_close_page_warns_after_a_conversion_rate_change
FAILED ...::TestTheDriftWarningThroughTheWeb::test_the_close_page_stays_quiet_for_another_period
6 failed, 5 passed
```

Sau sửa: `15 passed`. Thuật toán trước repair được chép NGUYÊN VĂN vào bộ test
(`_fingerprint_before_repair`) và chạy CẠNH bản mới, nên hai finding tái hiện
được về sau chứ không chỉ được mô tả. Hai bài đo hàm THUẦN được thêm sau đó
(`test_two_lines_differing_only_in_identity_are_told_apart`,
`test_the_totals_snapshot_is_part_of_the_fingerprint`) — chúng chứng minh lỗ
hổng danh tính và lỗ hổng `totals` một cách trực tiếp, không phụ thuộc thứ tự
lặp; xem `S129` §11 để có phép đo chạy trên chính thuật toán cũ.

### Hệ quả vận hành phải nói ra

`FINGERPRINT_VERSION = "R3-FP-2"` nằm ngay đầu payload được băm. Một vân tay
lưu bởi thuật toán CŨ không so được với vân tay tính ra hôm nay, nên một kỳ đã
chốt TRƯỚC bản repair sẽ báo drift đúng MỘT lần và cần chốt lại.

Trên thực tế không có bản ghi nào như thế: migration `0009` (tạo bảng
`period_close`) mới ra đời trong CHÍNH nhánh R3 chưa merge, nên chưa database
production nào từng có một lần chốt kỳ. Ghi lại ở đây vì nó là ràng buộc thật
nếu nhánh này được deploy rồi mới nhận repair.

## 8. Rủi ro giữ lại (ACCEPTED_RISK)

### AR-R3-01 — phân loại mã sản phẩm KHÔNG đi qua cửa chặn kỳ đã chốt

Thẩm quyền Product Identity (R2) là quyết định TOÀN CỤC theo
`raw_identity_key`, không theo dòng và không theo kỳ. Một lần xác nhận mã có
thể làm đổi giá nhập — và vì thế đổi con số — của một kỳ ĐÃ CHỐT.

Không khoá nó, vì mapping là toàn cục: chặn nó sẽ chặn luôn việc phân loại cho
các kỳ đang mở ngay khi một kỳ bất kỳ được chốt.

Giảm nhẹ ĐÃ CÀI: `period_drift` so vân tay bộ số hiện tại với bộ số lúc chốt,
và trang chốt kỳ nói thẳng khi chúng đã lệch. Nghĩa là thay đổi không bị chặn
nhưng không bao giờ im lặng.

### AR-R3-02 — `BTL` vẫn chưa có nghĩa

4 dòng trên hai kỳ golden (3 + 1) mang tiền tố chứng từ `BTL` và hiện ở trạng
thái `UNDECIDED_DOCUMENT`. Chúng KHÔNG vào lợi nhuận, và chúng giữ coverage
dưới 100 % cho tới khi Owner quyết. Đó là hành vi ĐÚNG theo `OD-2`, nhưng nó
có nghĩa hai kỳ này không đạt `OFFICIAL` chỉ vì bốn dòng.

Việc cần Owner: nói `BTL` nghĩa là gì. Một dòng trong `config/line_types.yaml`
là đủ để đóng nó — nhưng dòng đó là một quyết định nghiệp vụ, không phải một
lần sửa cấu hình.

### AR-R3-03 — mỏ neo IMEI chưa đo được trên dữ liệu thật

`IMEI` là mỏ neo mạnh nhất trong ba mỏ neo, nhưng cột `imei` rỗng trên toàn bộ
hai kỳ golden đã ẩn danh (`anonymize.py` xoá nó). Nhánh IMEI vì thế chỉ được
kiểm bằng test tổng hợp, không bằng dữ liệu thật.

Tác động nếu nhánh này sai: hệ thống lùi về mỏ neo `FINGERPRINT` — tức đúng
hành vi đã đo được là an toàn trên dữ liệu thật. Không có nhánh nào tệ hơn
trạng thái trước R3.

### AR-R3-04 — `AR-R2-01` chưa được đóng

Lỗi có TRƯỚC R2 (`SetPending` rồi `ConfirmMapping` làm log identity không đọc
được) giữ nguyên. R3 không chạm vào chuỗi identity, và đóng nó cần một quyết
định về `_ACTIVE_STATUSES` của `PENDING`/`STALE` — ngoài Scope Lock của R3.

---

### AR-R3-05 — ngoại lệ gắn dòng chưa lọc tuyệt đối theo kỳ

Independent Review nêu và YÊU CẦU KHÔNG sửa trong vòng repair này.

`PeriodData.binding_exceptions` đọc `BindingExceptionStore.open_keys()` — mọi
ngoại lệ CÒN MỞ của toàn database, rồi tra theo khoá dòng. Vì tra theo khoá,
một dòng chỉ nhận đúng ngoại lệ của chính nó, nên bảng kê và file xuất KHÔNG
sai. Chỗ chưa chặt là các phép ĐẾM đọc thẳng `len(data.binding_exceptions)`
(ô "còn N ngoại lệ chưa xử lý" ở trang chốt kỳ), vốn đếm cả ngoại lệ của kỳ
khác.

Tác động: một con số cảnh báo cao hơn sự thật ở đúng một ô, không con số tiền
nào sai. Cách đóng: lọc theo tập khoá dòng của kỳ trước khi đếm.

### AR-R3-06 — `PeriodData._slice` chưa chiếu `excluded` và cảnh báo theo lát

Independent Review nêu và YÊU CẦU KHÔNG sửa trong vòng repair này.

`_slice()` chở `binding_exceptions`, `discount_double_count` và `closed` NGUYÊN
VẸN sang lát cắt, và KHÔNG chở `excluded` (lát cắt luôn có `excluded=[]`).
Nghĩa là ở khung nhìn một nhân viên/một sheet: danh sách dòng đã loại rỗng dù
nhân viên đó có dòng bị loại, và cảnh báo trừ chiết khấu hai lần có thể nêu
một đơn không thuộc lát đang xem.

Tác động: cảnh báo rộng hơn cần thiết và một danh sách khôi phục rỗng ở khung
nhìn con — không chỉ tiêu cộng được nào sai (`totals` vẫn tính trên đúng tập
dòng của lát). Cách đóng: chiếu cả ba lớp phủ theo tập khoá của lát.

## 9. Đầu vào cho phiên sau

- Một loại dòng hiệu lực mỗi dòng — `line_type.classify`, sáu `LINE_TYPES`.
- Một giá nhập KPI hiệu lực — `BusinessLine.purchase_price`, ba thẩm quyền
  theo thứ tự: giá tay → MIN đúng `sale_date` → chính sách loại dòng.
- Khoá dòng: `(order_key, product_key, occurrence_index)`, nay gắn theo NỘI
  DUNG (`app/history/line_binding.py`).
- Chốt kỳ: `app/web/period_lock.py`; cửa chặn ghi ở tầng route
  (`_guard_lines`, `guard_period_open`, `guard_product_open`).
- Lệnh đối soát: `python3 -m tools.analysis.r3_reconcile`.
- Lệnh test: `python -m pytest -q tests/` (full), hoặc
  `python -m pytest -q tests/test_r3_import_binding.py tests/test_r3_line_types.py tests/test_r3_export_and_period_close.py tests/test_r3_web_workflow.py tests/test_r3_golden_reconciliation.py`
  cho riêng R3.
