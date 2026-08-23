# ADR-106 — ProductGroup và ConversionScheme ở cấp Product Line

## Status
Accepted

## Date
2026-08-23

## Context

ADR-104 tách `LeadSource` khỏi `ConversionScheme` và đặt cả hai ở **cấp
OrderID** (§Migration: "`orders` mang `lead_source_*`, `conversion_scheme_*`").
Với chính sách lúc đó, tỉ lệ quy đổi phụ thuộc `(employee, lead_source, ngày)`
— cả ba đều là thuộc tính của đơn hàng, nên đặt ở cấp đơn là đúng.

Rà soát nghiệp vụ ngày 2026-08-23 (DEC-127) bổ sung một chiều thứ tư mà
ADR-104 chưa lường:

> Sản phẩm **Gia dụng** có biên lợi nhuận khác **Điện máy**, nên dùng hệ số
> quy đổi khác — ngay cả khi cùng một nhân viên bán, cùng một nguồn đơn.

Chiều này **không** phải thuộc tính của đơn hàng. Nó là thuộc tính của **từng
dòng sản phẩm**. Ba phép đo trên dữ liệu thật xác nhận đây là vấn đề thật,
không phải phòng xa:

1. **118 trên 10.609 OrderID chứa đồng thời cả Điện máy lẫn Gia dụng.** Gán
   một `ConversionScheme` cho cả đơn sẽ tính sai 118 đơn.
2. Trong tổng số dòng khớp mã Gia dụng, **436 (66 %) thuộc nhóm `NOI_THANH`**
   và **227 (34 %) thuộc `STANDARD_SALES`** — nên "Gia dụng" không thể mô
   hình hóa thành một nhân viên hay một nhóm nhân viên.
3. **50 trên 155 mã Gia dụng cũng xuất hiện ở sheet nhân viên cá nhân** —
   cùng một mã máy đi qua hai luồng có tỉ lệ khác nhau, nên `ProductGroup`
   không suy được từ mã sản phẩm.

Đồng thời, gộp Vinh/Quý/Hiệp thành một Employee giả tên `Nội thành` (cách làm
của TASK-101) làm mất danh tính ba nhân viên có thật, trong khi file thô ghi
rõ ba giá trị `NVBH` riêng.

## Decision

**Bổ sung `ProductGroup` làm dimension thứ tư, và hạ `ConversionScheme` xuống
cấp product line.**

### 1. Năm dimension độc lập

```
Employee          — ai bán?                    master data
EmployeeGroup     — thuộc nhóm chính sách nào?  master data
LeadSource        — đơn đến từ đâu?             PERSONAL | ADS      (cấp Order)
ProductGroup      — dòng này là hàng gì?        DIEN_MAY | GIA_DUNG (cấp Line)
ConversionScheme  — tỉ lệ nào quy đổi?          một dòng config     (cấp Line)
```

`Employee ≠ EmployeeGroup ≠ LeadSource ≠ ProductGroup ≠ ConversionScheme`.
Không dimension nào được suy trực tiếp từ dimension khác.

### 2. Granularity

| Khái niệm | Cấp | So với ADR-104 |
|---|---|---|
| `LeadSource` | **Order** | **Không đổi** — một đơn đến từ một nguồn (DEC-119) |
| `ProductGroup` | **Line** | Mới |
| `ConversionScheme` | **Line** | **Đổi** — ADR-104 đặt ở Order |

Chuỗi tổng hợp bắt buộc:

```
Product Line → Order → Employee → Month → Summary
```

**Cấm** cộng lợi nhuận của các line có `ConversionScheme` khác nhau rồi chia
chung một tỉ lệ. Đây là dạng tổng quát của ràng buộc hai-bucket mà ADR-104 đã
đặt ra cho `LeadSource`; nay áp cho mọi chiều.

### 3. Bảng scheme 4 chiều

`config/conversion_rates.yaml`, khóa
`(employee, employee_group, lead_source, product_group, hiệu lực theo ngày)`:

| employee | employee_group | lead_source | product_group | scheme | rate |
|---|---|---|---|---|---|
| `*` | `*` | `PERSONAL` | `*` | `PERSONAL_5_5` | 5,5 % |
| `*` | `*` | `ADS` | `*` | `ADS_7_5` | 7,5 % |
| `*` | `NOI_THANH` | `PERSONAL` | `DIEN_MAY` | `NOI_THANH_2` | 2 % |
| `*` | `NOI_THANH` | `PERSONAL` | `GIA_DUNG` | `GIA_DUNG_8` | 8 % |

`GIA_DUNG_8` khóa trên `NOI_THANH`, **không** trên `*` — để 227 dòng Gia dụng
do nhóm `STANDARD_SALES` bán giữ đúng scheme của họ, khớp cách workbook lịch
sử đang tính (DEC-127 §3).

### 4. Resolver precedence

`lead_source` là **bộ lọc cứng** — dòng không khớp nguồn đơn bị loại, không có
`*` nào thắng sai nguồn.

Trong số dòng còn lại, chọn dòng **cụ thể nhất** theo điểm:

```
specificity = 4×(employee ≠ "*") + 2×(employee_group ≠ "*") + 1×(product_group ≠ "*")
```

- Điểm cao nhất thắng.
- **Hòa điểm → lỗi cấu hình mơ hồ**, không tự chọn.
- Không dòng nào khớp → `Unresolved` + Review Queue, **không** fallback.

> **Đây là quy ước phân giải của ADR này, không phải business rule bất
> biến** (chủ dự án ghi rõ khi phê duyệt). Trọng số phản ánh trực giác "cá
> nhân cụ thể hơn nhóm, nhóm cụ thể hơn loại hàng". Nếu sau này xuất hiện
> dimension thứ năm, **không được tự mở rộng công thức** — phải mở lại ADR
> này và để chủ dự án quyết định thứ tự ưu tiên.

### 5. Provenance của ProductGroup

Theo khuôn `_auto/_manual/_final` của ADR-102:

```
product_group_auto             Phase 1 luôn None (chưa có auto-classification)
product_group_manual           checkbox "☐ Gia dụng" ghi vào đây
product_group_final            DIEN_MAY | GIA_DUNG
product_group_source_of_value  DEFAULT | MANUAL | AUTO
```

Phải phân biệt được **mặc định** với **người dùng đã xác nhận**:
`(DIEN_MAY, DEFAULT)` khác `(GIA_DUNG, MANUAL)`. Manual override đi qua audit
trail của ADR-102.

### 6. Phase 1 không có auto-classification

`ProductGroupProvider` là interface ổn định; Phase 1 chỉ có
`DefaultProductGroupProvider` trả `None` → mọi dòng rơi về `DIEN_MAY`.

**Không** dùng danh sách 155 model lịch sử làm business truth, **không** suy
luận bằng keyword/tên sản phẩm, **không** tự học `Model → ProductGroup` —
xem phép đo 3 ở §Context.

## Alternatives Considered

1. **Tạo employee `Gia dụng`** — đúng cách workbook đang tổ chức (một sheet
   riêng mỗi tháng).
2. **Tạo `employee_group = GIA_DUNG`.**
3. **Giữ ConversionScheme ở cấp Order, lấy ProductGroup "chủ đạo" của đơn.**
4. **Áp `* + GIA_DUNG → 8 %` cho mọi nhân viên.**

## Rationale

**Vì sao không tạo employee `Gia dụng`.** Gia dụng không bán hàng; người bán
là Hiệp, Quý, Vinh và cả nhóm `STANDARD_SALES`. Một employee giả sẽ lặp lại
đúng lỗi mà ADR-104 đã sửa với `TINPHAT_ADS`: nhét một khái niệm vào một enum
của khái niệm khác. Ngoài ra sheet `Gia dụng` của workbook **không có cột
nhân viên và không có OrderID** — nó là một cách tổ chức báo cáo, không phải
một thực thể nghiệp vụ.

**Vì sao không tạo `employee_group = GIA_DUNG`.** Group là thuộc tính của
người; một người không thể vừa thuộc `NOI_THANH` vừa thuộc `GIA_DUNG` tùy
theo dòng hàng anh ta vừa bán. Đo được: cùng một nhân viên có cả hai loại
hàng trong cùng một đơn ở 118 đơn.

**Vì sao không lấy ProductGroup "chủ đạo" của đơn.** Nó trả lời sai ở 118
đơn, và sai theo hướng không phát hiện được — con số vẫn trông hợp lý. Đúng
loại lỗi mà toàn bộ khung governance này tồn tại để chặn.

**Vì sao không áp `* + GIA_DUNG → 8 %`.** 227 dòng Gia dụng do nhóm
`STANDARD_SALES` bán sẽ nhảy từ 5,5 % lên 8 %, lệch khỏi cách workbook lịch
sử tính. Nếu chính sách tương lai muốn thế, thêm một dòng có
`effective_from` — cơ chế effective-dating (DEC-121) cho phép cả hai cùng tồn
tại mà không viết lại lịch sử.

**Vì sao hạ granularity là thay đổi nhỏ chứ không phải lật ngược ADR-104.**
ADR-104 đúng ở phần cốt lõi: hai khái niệm độc lập, hai bước phân giải, không
suy tỉ lệ từ nguồn đơn. ADR-106 chỉ thêm chiều thứ tư và chuyển chỗ lưu
`conversion_scheme_*` từ `Order` xuống `WorkingLine`. Mọi lập luận của
ADR-104 giữ nguyên hiệu lực.

## Consequences

### Positive

- 118 đơn hỗn hợp tính đúng thay vì sai âm thầm.
- Vinh/Quý/Hiệp giữ danh tính riêng trong khi vẫn dùng chung scheme 2 %.
- Thêm nhân viên hoặc đổi chính sách vẫn là sửa YAML, không sửa code.
- `ProductGroup` sai/thiếu nhìn thấy được qua `source_of_value = DEFAULT`.

### Negative / Tradeoffs

- **Phase 1 mọi dòng là `DIEN_MAY`.** Các dòng Gia dụng của kênh Nội thành sẽ
  quy đổi ở 2 % thay vì 8 % cho tới khi có UI checkbox. Hệ quả đã biết và
  được chấp nhận (DEC-127 §5); `source_of_value` làm nó hiển thị được.
- Nhiều cột hơn trên `WorkingLine`; tầng báo cáo phải gộp từ line lên.
- Bảng config có thể thiếu dòng → `Unresolved`. Đánh đổi có chủ ý, giống
  ADR-104: thà ồn ào còn hơn một tỉ lệ mặc định im lặng.

## Migration / Implementation Notes

- `WorkingLine` mang `employee_group`, `product_group_auto/_manual/_final`,
  `product_group_source_of_value`, `conversion_scheme_auto/_manual/_final`,
  `conversion_rate_final`, `conversion_scheme_source_of_value`.
- `Order` mang `employee_group`; **không** mang `conversion_scheme_*` nữa —
  sửa đổi này thay thế câu tương ứng ở ADR-104 §Migration.
- `rate` lưu dạng chuỗi trong YAML, đọc ra `Decimal`, không bao giờ `float`
  (ADR-103).
- Kiểm chứng tĩnh: không literal `0.02` / `0.055` / `0.075` / `0.08` và không
  tên nhân viên nào trong `app/modules/`.
- Bản cài đặt tham chiếu `tools/analysis/verify_ads_rule.py` cập nhật sang
  bảng 4 chiều; 8 case A–G phải cho **cùng scheme và cùng rate** như trước
  khi tách Employee/EmployeeGroup.

## Supersedes
Không thay thế ADR nào. **Sửa đổi ADR-104 §Migration** ở đúng một điểm: cặp
`conversion_scheme_*` chuyển từ `orders` xuống `WorkingLine`. Phần còn lại
của ADR-104 giữ nguyên hiệu lực.

## Superseded By
None
