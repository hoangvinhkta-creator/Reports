# 03 — Phân loại công thức: Universal / Business Rule / Manual-Special Case

Đáp ứng mục 27.3 đặc tả.

Ba loại:

- **U — Universal formula**: định nghĩa toán học, không đổi theo người/thời
  gian. Nằm trong code.
- **B — Business rule**: chính sách công ty, thay đổi được. **Bắt buộc nằm ở
  config**, không nằm trong code (mục 28 đặc tả).
- **M — Manual / special case**: quyết định của người quản lý cho một dòng, một
  đơn hoặc một kỳ cụ thể. Nằm ở lớp override + audit trail.

---

## U — Universal formula

| Công thức | Nguồn |
|---|---|
| `TotalSales = SellPrice × Quantity` | `Hn = Gn*En` |
| `AccountingProfit = (SellPrice − AccountingPurchasePrice) × Quantity` | `Mn = (Gn-Ln)*En` |
| `EligibleKpiProfit = (SellPrice − KpiPurchasePrice) × Quantity − EligibleCosts + OtherKpiAdjustment` | `In = (Gn-Fn)*En` + mục 11 đặc tả |
| `KpiPurchasePrice = AccountingPurchasePrice + KpiPurchaseAdjustment` | mục 11 đặc tả |
| `TotalOrders = COUNT DISTINCT OrderID` | `B1 = count(B3:Bn)` + mục 3 đặc tả |
| `TotalProducts = SUM(Quantity)` sau Classification | `E1` (đã sửa lỗi) |
| `ProfitMargin = Profit / Sales` | `J1 = I1/H1` |
| `AutoConvertedRevenue = EligibleKpiProfit / ConversionRate` | `F = G/rate` |
| `TotalConvertedRevenue = PersonalCR + AdsCR` | mục 6 đặc tả |
| `ConvertedRevenuePerOrder = ConvertedRevenue / Orders` | mục 15 đặc tả |
| `PercentTarget = TotalConvertedRevenue / Target` | `N = F/M` |
| `TotalSalary = Bonus + BaseSalary + Allowance` | `S = O+Q+R` |
| `StockRatio = SUMIF(PurchaseSource="Kho", Sales) / TotalSales` | `C1` |

Các công thức này **không được** cấu hình. Sửa chúng là sửa định nghĩa.

---

## B — Business rule (phải nằm ở config)

| Rule | Giá trị hiện tại | File config | Chiều thay đổi |
|---|---|---|---|
| Tỉ lệ quy đổi PERSONAL | 5,5 % | `conversion_rates.yaml` | theo thời gian |
| Tỉ lệ quy đổi ADS | 7,5 % | `conversion_rates.yaml` | theo thời gian |
| Tỉ lệ quy đổi kênh Nội thành | 2 % | `conversion_rates.yaml` | theo nhân viên + thời gian |
| Tỉ lệ quy đổi kênh Gia dụng | 8 % | `conversion_rates.yaml` | theo nhân viên + thời gian |
| Từ khóa nhận diện ADS | `["ADS"]` | `lead_source.yaml` | danh sách mở rộng được |
| Nguồn đơn mặc định | `PERSONAL` | `lead_source.yaml` | ghi đè được ở cấp nhân viên (mở — C1) |
| Mapping nhân viên | 8 raw → 6 chuẩn | `employees.yaml` | thêm/nghỉ không cần code |
| Target nhân viên/tháng | 1.300.000 / 2.700.000 / 12.000.000 | `targets.yaml` | theo nhân viên + thời gian |
| Target công ty/tháng | 28.790.000 | `targets.yaml` | theo thời gian |
| Target công ty/năm | 345.474.000 | `targets.yaml` | theo năm |
| Tỉ lệ thưởng | 0,02 % – 0,5 % | `commission.yaml` | theo nhân viên + tháng |
| Lương cứng | `NgàyCông × 4.500 / 26` | `payroll.yaml` | hằng số 4.500 và 26 |
| Phụ cấp | `IF(NgàyCông ≥ 26, 30 × 26, NgàyCông × 30)` | `payroll.yaml` | hằng số 30 và ngưỡng 26 |
| Số ngày công chuẩn | 26 | `payroll.yaml` | |
| Từ khóa Adjustment | `Qua kho`, `KHBH`, `Thợ lắp`, `NCC giao` | `adjustments.yaml` | thêm loại mới không cần code |
| Nhóm "Kho" cho tỉ lệ tồn kho | `PurchaseSource == "Kho"` | `adjustments.yaml` | |
| Classification dòng phụ | `chân máy giặt đa năng`, `giá treo tivi`, `vận chuyển` | `classification.yaml` | |
| Đơn vị hiển thị | nghìn đồng | `settings.yaml` | |

### Bảng Adjustment — từ vựng thật trong file mẫu

Cột `J: Giao hàng` của sheet nhân viên, đơn vị **nghìn đồng**, giá trị âm làm
giảm `KpiPurchasePrice` (tức tăng lợi nhuận KPI của nhân viên):

| Ghi chú | Số dòng | Diễn giải |
|---|---|---|
| `Kích` | 487 | Không phải điều chỉnh giá — ghi chú giao hàng |
| `KHBH -50` | 169 | Khách hàng bảo hành, −50 |
| `Thợ lắp -200, KHBH -50` | 109 | Hai điều chỉnh cộng dồn |
| `NCC giao -100` | 69 | Nhà cung cấp giao hộ, −100 |
| `Qua kho -100` | 58 | **Đúng ví dụ mục 11 đặc tả** |
| `Qua kho -100, KHBH -50` | 22 | Cộng dồn |
| `NCC giao -50` | 19 | |
| `Qua kho -50` | 19 | |
| `Qua kho -200` | 16 | |
| `Thợ lắp -200,KHBH -50` | 8 | Thiếu dấu cách sau dấu phẩy |
| `NCC giao -100, KHBH -50` | 4 | |
| `NCc giao -100` | 5 | Sai hoa/thường |
| `qua kho -100` | 3 | Sai hoa/thường |

**Yêu cầu cho parser:** không phân biệt hoa/thường, chấp nhận thiếu dấu cách
sau dấu phẩy, cộng dồn nhiều điều chỉnh trong một ô. Ghi chú không khớp mẫu
nào (`Kích`, `Quét`) giữ nguyên làm text, **không** coi là điều chỉnh 0 —
và đưa vào Review Queue nếu chứa dấu trừ mà không parse được.

### Bảng Classification — dòng không phải sản phẩm

Từ file thô, cột `Tên hàng trên chứng từ`:

| Loại dòng | Số dòng | Tính vào Số SP? | Doanh số? | Lợi nhuận? | Số đơn? |
|---|---|---|---|---|---|
| `Chi phí vận chuyển` (mọi biến thể) | ~1.110 | **Không** | Có | Có | Không tạo đơn riêng |
| `Chi phí lắp đặt` / `Công lắp đặt` | ~85 | **Không** | Có | Có | Không tạo đơn riêng |
| `Chênh VAT` (25 %, 30 %, …) | ~43 | **Không** | Có | Có | Không tạo đơn riêng |
| `Chi phí giao hộ …` | ~8 | **Không** | Có | Có | Không tạo đơn riêng |
| `Phí đổi trả` | 2 | **Không** | Có | Có | Không tạo đơn riêng |
| Sản phẩm thật | phần còn lại | Có | Có | Có | Có |

Giá trị ở cột "Tính vào …" là **đề xuất** dựa trên `COUNTIF` có sẵn trong file
mẫu (`chân máy giặt đa năng`, `giá treo tivi`, `vận chuyển` đều bị trừ khỏi số
SP). **Cần chủ dự án duyệt** — xem mục mở C5.

---

## M — Manual / Special case

| Trường hợp | Bằng chứng trong file mẫu | Xử lý trong công cụ |
|---|---|---|
| Số lợi nhuận ADS của Hoàng/Kiên | `=(G8-37270)/5.5%+37270/7.5%` | **Tự động hóa** qua rule ADS; vẫn override được ở cấp OrderID |
| Ghi đè `Giá thực nhập` | 635/18.148 dòng nhập tay thay vì `=F` | `AccountingPurchasePrice` override + audit |
| Ghi đè `Giá nhập TT` | `=5870-250` viết thẳng trong ô | `KpiPurchaseAdjustment` + audit |
| Loại trừ đơn khỏi báo cáo | Lệch 1–9 đơn giữa thô và báo cáo (tài liệu 05 §7) | Cờ `ExcludeFromKpi` + lý do bắt buộc |
| `Vs. tháng trước` tháng 01 | `=F4/1571182` — số cứng năm trước | Lấy từ dữ liệu 2025 khi có; chưa có thì để trống, không bịa |
| Ngày công | Nhập tay ở cột `P` | Nhập tay, có audit |
| Doanh số theo ngày ở DataChart | Nhập tay `B3:AF14` | **Sinh tự động** từ Working Data |

**Nguyên tắc bất biến (mục 30 đặc tả):** mọi giá trị loại M đều ghi vào audit
trail với `OriginalValue`, `NewValue`, `ChangedBy`, `Reason`. Không có override
nào được phép làm mất giá trị tự động — luôn Reset về Auto được.

---

## Thứ tự ưu tiên khi lấy giá trị

```
FinalValue = Manual Override ?? Business Rule ?? Master Data ?? Raw Data ?? Missing
```

Riêng LeadSource (mục 7 đặc tả):

```
LeadSourceFinal = Manual Override → Rule ADS → Default
```

Mỗi dòng hiển thị `SourceOfValue`: `Manual` / `Auto:ADS Rule` / `Auto:Default`.
