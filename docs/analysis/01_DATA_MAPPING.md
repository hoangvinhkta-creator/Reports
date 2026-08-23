# 01 — Data Mapping: Raw → Working → Report

Đáp ứng mục 27.1 đặc tả.

---

## 1. Cấu trúc vật lý file thô

`data/samples/So_chi_tiet_ban_hang.xlsx` — 1 sheet `SỔ CHI TIẾT BÁN HÀNG`.

| Dòng | Nội dung |
|---|---|
| 1 | Tiêu đề `SỔ CHI TIẾT BÁN HÀNG` |
| 2 | `Từ ngày 01/01/2026 đến ngày …` |
| 3 | Trống |
| **4** | **Header tầng 1** — tên cột chính |
| **5** | **Header tầng 2** — mô tả bổ sung, chỉ điền một số cột |
| **6+** | **Dữ liệu** |

Importer phải đọc header ở dòng 4, bỏ dòng 5, bắt đầu dữ liệu từ dòng 6.
Không được dùng `pandas.read_excel` mặc định — nó sẽ lấy dòng 1 làm header.

**Thống kê:** 11.765 dòng dữ liệu · 8.714 Số BH duy nhất · 2.139 đơn nhiều dòng
(tối đa 10 dòng/đơn) · khoảng ngày 2026-01-01 → 2026-06-30.

---

## 2. Bảng mapping đầy đủ

Đơn vị: file thô **VND nguyên**, file báo cáo **nghìn đồng**. Cột `Report field`
ghi theo layout nhân viên cá nhân (18 sheet dùng layout này); layout kênh
Nội thành/Gia dụng lệch trái 1 cột vì không có `Nơi nhập` — xem mục 4.

| # | Raw field (dòng 4) | Working field | Report field | Ghi chú chuyển đổi |
|---|---|---|---|---|
| 1 | `Ngày` | `Date` | `A: Date` | Ngày hạch toán. Báo cáo chỉ ghi ngày ở dòng đầu mỗi ngày; công cụ luôn ghi đủ mọi dòng. |
| — | *(dẫn xuất)* | `Month` | — | `YYYY-MM` từ `Date`. |
| 2 | `Số BH` | `OrderID` | *(không có)* | **Báo cáo mẫu không lưu OrderID.** Đây là mất mát dữ liệu cần khôi phục — không có OrderID thì không thể phân loại nguồn đơn ở cấp đơn. |
| — | *(dẫn xuất)* | `LineNo` | `B: Trans` | `Trans` = số thứ tự đơn trong ngày, để trống ở dòng nối tiếp của cùng đơn. Công cụ sinh lại từ `OrderID` + `Date`. |
| 3 | `Diễn giải` | `NoteRaw` | `Ghi chú` | **Nguồn duy nhất nhận diện ADS.** File thô không có cột `Ghi chú` riêng. |
| 4 | `Tên hàng trên chứng từ` | `ProductRaw` | — | Tên đầy đủ, ví dụ `Máy giặt LG FV1410S4B`. |
| — | *(dẫn xuất, Phase 4)* | `ProductCode` | `D: Mã Sản phẩm` | Báo cáo dùng mã ngắn (`5089K3`, `EWF1023P5SC`). Cần product_mapper. **MVP để trống, hiện `ProductRaw`.** |
| — | *(dẫn xuất, Phase 4)* | `Brand` | `R: Hãng` | |
| — | *(dẫn xuất, Phase 4)* | `Category` | — | |
| 5 | `Mã khách hàng` | `CustomerCode` | — | |
| 6 | `Tên KH` | `Customer` | `O: Tên khách hàng` | **Dữ liệu cá nhân.** |
| 7 | `Địa chỉ` | `Address` | `Q: Địa chỉ` | **Dữ liệu cá nhân.** |
| 8 | `ĐT di động (Người liên hệ)` | `Phone` | `P: Số điện thoại` | **Dữ liệu cá nhân.** |
| 9 | `SL` | `Quantity` | `E: Số lượng` | |
| 10 | `Đơn giá` | `SellPrice` | `G: Giá bán` | Chia 1.000 khi xuất. |
| 11 | `Doanh số bán` | `TotalSales` | `H: Tổng bán` | Báo cáo tính lại `=G*E`; công cụ giữ cả giá trị nguồn để đối chiếu. |
| 12 | `Chiết khấu` | `Discount` | *(không có)* | 408 dòng có chiết khấu ≠ 0. **Mở — xem C4.** |
| 13 | `NVBH` | `EmployeeRaw` | *(tên sheet)* | 14 giá trị riêng biệt. |
| — | *(dẫn xuất)* | `EmployeeNormalized` | *(tên sheet `MM.YYYY <tên>`)* | Qua `config/employees.yaml`. |
| 14 | `Giao vận` | `ShipperRaw` | — | Tên người/đơn vị giao. |
| 15 | `Lương chuyến` | `DeliveryCost` | `K: Chi phí giao` | |
| 16 | `Trường mở rộng chi tiết 1` | `IMEI` | `S: IMEI` | Nhiều IMEI ngăn bởi ` / `. |
| 17 | `Lợi nhuận` | `SourceProfit` | *(không có)* | **Lợi nhuận do ERP tính.** Chỉ dùng để đối chiếu — xem mục 3. |

### Field trong Working Data không có nguồn thô

| Working field | Report field | Nguồn |
|---|---|---|
| `PurchaseSource` | `C: Nơi nhập` | **Không có trong file thô.** Nhập tay hoặc từ hệ thống kho sau. 22.029 ô trong các sheet cá nhân của báo cáo mẫu đang để trống. |
| `AccountingPurchasePrice` | `L: Giá thực nhập` | **Pending** (DEC-103). Sau này từ Price Master. |
| `KpiPurchasePrice` | `F: Giá nhập TT` | `AccountingPurchasePrice + KpiPurchaseAdjustment`. |
| `KpiAdjustment` | `J: Giao hàng` | Parse từ ghi chú điều chỉnh — xem tài liệu 03. |
| `AccountingProfit` | `M: Lợi nhuận gộp` | `(SellPrice − AccountingPurchasePrice) × Quantity` |
| `EligibleKpiProfit` | `I: Lợi nhuận` | `(SellPrice − KpiPurchasePrice) × Quantity − EligibleCosts + OtherKpiAdjustment` |
| `LeadSourceAuto` | *(không có)* | Rule ADS trên `NoteRaw`. |
| `LeadSourceManual` | *(không có)* | Override tay. |
| `LeadSourceFinal` | *(cần thêm)* | Cột mới, badge `PERSONAL`/`ADS`. |
| `ConversionScheme` | *(không có)* | Từ `LeadSourceFinal`. |
| `AutoConvertedRevenue` | *(chỉ có ở Summary)* | `EligibleKpiProfit / ConversionRate` |
| `ManualConvertedRevenue` | — | Override tay. |
| `FinalConvertedRevenue` | *(cần thêm)* | Cột mới ở sheet chi tiết. |
| `WarrantyStatus` | `T: Tình trạng bảo hành` | Nhập tay. |
| `ManualOverrideFlag`, `OverrideReason` | — | Nội bộ. |
| `source_file`, `source_sheet`, `source_row` | — | Truy ngược về Raw (mục 4.1 đặc tả). |

---

## 3. Vì sao `Lợi nhuận` của ERP không được dùng làm giá nhập

File thô có `Lợi nhuận`, nên về mặt số học có thể suy ra
`GiaNhap = DonGia − LoiNhuan / SL`. **Công cụ không làm việc này** (DEC-103):

- Chủ dự án yêu cầu để trống, chờ công cụ bảng giá.
- `Lợi nhuận` của ERP đã gồm những khoản mà công cụ chưa biết cấu thành:
  1.912/11.765 dòng có lợi nhuận **âm**, trong đó có cả dòng
  `Chi phí vận chuyển` với lợi nhuận đúng bằng doanh số (giá nhập = 0).
- Suy ngược sẽ tạo ra một con số trông như dữ liệu kế toán nhưng thực chất là
  phép chia — đúng loại nhầm lẫn mà mục 30 đặc tả cấm.

`SourceProfit` **vẫn được giữ** trong Working Data như cột tham chiếu chỉ đọc,
để đối chiếu và để cảnh báo khi lợi nhuận tính ra lệch xa giá trị ERP.

---

## 4. Sáu biến thể layout của sheet nhân viên

| Layout | Số sheet | Đặc điểm |
|---|---|---|
| L1 | 18 | Cá nhân, đầy đủ, `R: Hãng` |
| L2 | 11 | Như L1 nhưng `R1` = `,` (rác) |
| L3 | 6 | Như L1, khác vùng công thức |
| L4 | 3 | Như L1 nhưng `R1` = `.` |
| L5 | 2 | Như L1, thiếu công thức `G1` |
| **L6** | **16** | **Kênh Nội thành / Gia dụng — không có `Nơi nhập`, mọi cột lệch trái 1** |

L1–L5 khác nhau chỉ ở ký tự rác và vùng công thức → công cụ coi là **một**
layout cá nhân. L6 là layout thật sự khác.

**Ánh xạ cột L6 ↔ L1:**

| L1 (cá nhân) | L6 (kênh) | Ý nghĩa |
|---|---|---|
| `C` Nơi nhập | *(không có)* | |
| `D` Mã Sản phẩm | `C` | |
| `E` Số lượng | `D` | |
| `F` Giá nhập TT | `E` | |
| `G` Giá bán | `F` | |
| `H` Tổng bán | `G` | |
| `I` Lợi nhuận | `H` | |
| `J` Giao hàng | `I` | |
| `K` Chi phí giao | `J` | |
| `L` Giá thực nhập | `K` | |
| `M` Lợi nhuận gộp | `L` | |

Công cụ **xuất một layout duy nhất** cho mọi nhân viên và mọi kênh, có đủ cột
`Nơi nhập`, `Nguồn đơn`, `Scheme quy đổi`, `DS quy đổi` theo mục 14 đặc tả.

---

## 5. Mapping nhân viên đã chốt (DEC-104)

| Raw NVBH | Số dòng | Normalized | Active | Include in KPI | Default lead source |
|---|---|---|---|---|---|
| `Tín Phát 0869931931` | 1.440 | Tín Phát | Yes | Yes | **`TINPHAT_ADS`** (DEC-109) |
| `Vũ Hạnh Ly 0868345633` | 735 | Ly | Yes | Yes | `PERSONAL` |
| `Lê Mạnh Hoàng 0865111533` | 531 | Hoàng | Yes | Yes | `PERSONAL` |
| `Đức Kiên - Tân Á 0867666533` | 524 | Kiên | Yes | Yes | `PERSONAL` |
| `Phước Thắng 0865909022` | 411 | Thắng | Yes | Yes | `PERSONAL` |
| `Đức Hiệp` | 4.342 | **Nội thành** | Yes | Yes | `PERSONAL` |
| `Mr Quý` | 2.246 | **Nội thành** | Yes | Yes | `PERSONAL` |
| `Mr Vinh` | 1.448 | **Nội thành** | Yes | Yes | `PERSONAL` |
| `Thảo Linh` | 63 | *chưa map* | — | — | — |
| `Tống Khánh Linh 0865111033` | 14 | *chưa map* | — | — | — |
| `Lê Quang Trường 0589691228` | 6 | *chưa map* | — | — | — |
| `Lê Văn Quân 0865111033` | 2 | *chưa map* | — | — | — |
| `Nguyễn Thị Minh Bảo` | 1 | *chưa map* | — | — | — |
| *(rỗng)* | 2 | *chưa map* | — | — | — |

> Nội thành và Gia dụng có tỉ lệ quy đổi riêng (2 % và 8 %) đặt ở cấp nhân
> viên, nên `default_lead_source` của họ không ảnh hưởng tới con số — vẫn để
> `PERSONAL` cho nhất quán.

**88 dòng chưa map.** Chúng **không bị bỏ** — vào Review Queue loại `Missing`
để người quản lý quyết định. `Fanpage` không xuất hiện trong file thô 6 tháng
đầu 2026 nên không cần map (đặc tả cũng đã loại khỏi phạm vi).

Bảng này nằm ở `config/employees.yaml` với `effective_from` / `effective_to`,
nên thêm nhân viên mới hoặc cho nghỉ **không cần sửa code** (DEC-104).
