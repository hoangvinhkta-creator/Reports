# 04 — Danh sách hard-coded values

Đáp ứng mục 27.4 đặc tả. Đây là toàn bộ con số đang bị gắn cứng trong file
Excel mẫu và **phải trở thành cấu hình** trong công cụ (tiêu chí nghiệm thu
cuối cùng của mục 28: *"Không hard-code nhân viên, margin, target hay
adjustment trong source code"*).

Đơn vị tiền: **nghìn đồng**, trừ khi ghi rõ.

---

## 1. Tỉ lệ quy đổi doanh thu → `config/conversion_rates.yaml`

Tra theo khóa `(employee, lead_source, ngày của đơn)`; dòng cụ thể nhất thắng
(DEC-119, ADR-104):

| employee | lead_source | scheme | Tỉ lệ | effective_from | Ô nguồn |
|---|---|---|---|---|---|
| `*` | `PERSONAL` | `PERSONAL_5_5` | **5,5 %** | 2026-01-01 | `Summary 2026!F4`, `F5`, `F22`… |
| `*` | `ADS` | `ADS_7_5` | **7,5 %** | 2026-01-01 | `Summary 2026!F6`; vế sau của `F7`, `F8` |
| `Nội thành` | `PERSONAL` | `NOI_THANH_2` | **2 %** | 2026-01-01 | `Summary 2026!F9` |
| `Gia dụng` | `PERSONAL` | `GIA_DUNG_8` | **8 %** | 2026-01-01 | `Summary 2026!F10` |

Tín Phát, Hoàng, Kiên, Ly **không cần dòng riêng** — họ rơi vào hai dòng `*`.
7,5 % của Tín Phát suy ra từ nguồn đơn, không phải từ tên nhân viên.

Không có kỳ nào trong 2026 dùng tỉ lệ khác → seed một dòng hiệu lực từ
`2026-01-01`, `effective_to` để trống. Mốc 01/01/2027 (DEC-121) triển khai bằng
cách **thêm dòng mới** có `effective_from: 2027-01-01`, không sửa dòng cũ — để
báo cáo 2026 in lại vào 2028 vẫn ra đúng số của 2026.

**Chưa định nghĩa:** `(Nội thành, ADS)` và `(Gia dụng, ADS)`. Xem
`10_OPEN_QUESTIONS.md` — C9.

---

## 2. Lợi nhuận ADS nhập tay → **biến mất, không được thay bằng gì cả**

> **Cập nhật 2026-08-23 — DEC-120.** Bảng này **không còn là dữ liệu di trú**
> phải nạp vào hệ thống. Nó là một **bảng đối chiếu tham khảo**: chỗ duy nhất
> định lượng được chênh lệch giữa cách làm cũ và cách làm mới. Lịch sử không có
> dấu hiệu ADS phân loại thành `PERSONAL`, và đó là kết quả cuối cùng.

Con số `X` trong `=(G−X)/5.5% + X/7.5%`:

| Kỳ | Hoàng | Kiên | Ô nguồn |
|---|---|---|---|
| 01.2026 | 2.750 | 37.270 | `F7`, `F8` |
| 02.2026 | 35.520 | 1.500 | `F16`, `F17` |
| 03.2026 | 7.790 | 11.000 | `F25`, `F26` |
| 04.2026 | 17.200 | 9.230 | `F35`, `F36` |
| 05.2026 | 3.770 + 16.190 | 7.820 | `F45`, `F46` |
| 06.2026 | — | 7.565 | `F56` |
| 07.2026 | — | 7.565 | `F63` |
| 08.2026 | — | 7.565 | `F70` |

**Tổng 2026 tính đến 08: Hoàng 83.220 · Kiên 89.515** (nghìn đồng lợi nhuận
được quy đổi ở 7,5 % thay vì 5,5 %).

Đây là dữ liệu lịch sử. Với dữ liệu **mới**, `X` sẽ do rule ADS + override sinh
ra, không còn ai gõ tay. Với dữ liệu **cũ**, `X` đơn giản là 0 — không di trú
(DEC-120).

**Hai cách dùng bảng này về sau:**

1. **Định lượng chênh lệch.** Công cụ sẽ báo doanh thu quy đổi 01–08.2026 của
   Hoàng + Kiên là **14.720.745** thay vì **13.883.242** — cao hơn 837.503
   nghìn (+6,0 %). Bảng này là chỗ giải thích con số đó khi ai đó hỏi.
2. **REQUIRED check của TASK-108.** Nạp lợi nhuận KPI theo nhân viên-tháng
   **và** 14 giá trị `X` này vào `conversion_engine`; kết quả phải tái hiện
   đúng cột `F` của `Summary 2026` ở cả 14 kỳ. Đây là phép kiểm engine cài đúng
   phép toán — không phải một lệnh nạp dữ liệu vào production.

---

## 3. Target → `config/targets.yaml`

| Đối tượng | Target/tháng | Ô nguồn |
|---|---|---|
| Ly | 1.300.000 | `Summary 2026!M4` |
| Thắng | 1.300.000 | `M5` |
| Tín Phát | **2.700.000** | `M6` |
| Hoàng | 1.300.000 | `M7` |
| Kiên | 1.300.000 | `M8` |
| Nội thành | **12.000.000** | `M9` |
| Gia dụng | *(không đặt target)* | — |
| Linh / Fanpage | 1.300.000 | `M27`, `M37` |
| **Công ty** | **28.790.000** | `M11`, `M20`, `M30`… |

Target không đổi qua cả 8 tháng 2026 → seed một dòng hiệu lực từ `2026-01-01`.

| Phạm vi năm | Giá trị | Ô nguồn | Ghi chú |
|---|---|---|---|
| Target 2026 | 345.474.000 | `Summary 2026!M3`, `DataChart!J15` | = 12 × 28.790.000 (làm tròn) |
| Target tháng (VND) | 28.789.481.081 | `DataChart!AJ2` | **Cùng một target, khác đơn vị 1.000 lần so với `M11`** |
| Mẫu số ngày/năm | 365 | `Summary 2026!A3`, `L3` | |
| Mẫu số target/ngày | **350** | `DataChart!P15` | Khác 365 ở sheet bên cạnh |

---

## 4. Thưởng → `config/commission.yaml`

Công thức: `Thưởng = DoanhThuQuyĐổi × tỉ_lệ`. Tỉ lệ thay đổi theo **từng
nhân viên từng tháng**:

| Kỳ | Ly | Thắng | Tín Phát | Hoàng | Kiên | Nội thành |
|---|---|---|---|---|---|---|
| 01.2026 | 0,5 % | 0,5 % | 0,25 % | 0,45 % | 0,5 % | 0,02 % |
| 02.2026 | 0,3 % | 0,3 % | 0,15 % | 0,3 % | 0,3 % | 0,02 % |
| 03.2026 | 0,3 % | 0,3 % | 0,15 % | 0,3 % | 0,3 % | 0,02 % |
| 04.2026 | 0,3 % | 0,3 % | 0,15 % | 0,3 % | 0,3 % | 0,02 % |
| 05.2026 | 0,3 % | 0,3 % | 0,15 % | 0,3 % | 0,3 % | 0,02 % |
| 06.2026 | 0,3 % | 0,3 % | 0,15 % | 0,3 % | 0,3 % | 0,02 % |
| 07.2026 | 0,3 % | — | 0,15 % | — | **0,5 %** | 0,02 % |
| 08.2026 | 0,3 % | — | 0,15 % | — | 0,3 % | 0,02 % |

Ghi chú ở dòng tổng mỗi tháng (`Summary 2026!O11`) viết:

> `Không đạt *0,3%, Đạt số *0,4%,`

Câu này gợi ý một rule bậc thang theo mức đạt target, **nhưng không khớp với
số thực tế** (tháng 01 dùng 0,45 %–0,5 %; Kiên tháng 07 dùng 0,5 % trong khi
mọi người khác 0,3 %). Câu ghi chú cũng bị cắt dở ở dấu phẩy cuối.

→ **MVP nạp bảng tỉ lệ theo nhân viên-tháng như dữ liệu.** Công thức hóa để
Phase 4 sau khi chủ dự án phát biểu đầy đủ chính sách (mục mở C3).

---

## 5. Lương → `config/payroll.yaml`

| Hằng số | Giá trị | Công thức nguồn |
|---|---|---|
| Đơn giá lương cứng | **4.500** | `Q4 = P4*4500/26` |
| Số ngày công chuẩn | **26** | mẫu số trên, và ngưỡng ở `R4` |
| Phụ cấp/ngày | **30** | `R4 = IF(P4>=26, 30*26, P4*30)` |
| Trần phụ cấp | **30 × 26 = 780** | `R4` |

Cột `Ngày công` (`P`) nhập tay, dao động 12–31 tùy người tùy tháng. Không phải
hằng số — là dữ liệu đầu vào.

Nhân viên kênh (Nội thành, Gia dụng) **không có** cột lương ở Summary.

---

## 6. Classification và Adjustment

| Hằng số | Giá trị | Ô nguồn |
|---|---|---|
| Từ khóa trừ khỏi số SP | `chân máy giặt đa năng`, `giá treo tivi`, `vận chuyển` | `D1 = COUNTIF(D2:Dn, …)` |
| Nhóm hàng tồn kho | `Kho` | `C1 = SUMIF(C3:Cn,"Kho",…)` |
| Ngưỡng biên lợi nhuận thấp | `< 1%` | `R1 = SUMIF(Q:Q,"<1%",G:G)` (layout kênh) |
| Từ khóa điều chỉnh | `Qua kho`, `KHBH`, `Thợ lắp`, `NCC giao` | cột `J` sheet nhân viên |
| Hệ số chia của sheet kênh | **2** | `G1 = SUM(G3:Gn)/2` |
| Hệ số chia tổng năm | **2** | `Summary 2026!E3 = SUM(E4:E902)/2` |

---

## 7. Nhân viên — hiện đang hard-code ở tên sheet

Bản thân tên sheet `MM.YYYY <Tên>` là hard-code: thêm một nhân viên nghĩa là
tạo tay 12 sheet mới và sửa tay công thức Summary. Đây chính là thứ DEC-104
loại bỏ — danh sách nhân viên trở thành `config/employees.yaml`, sheet sinh
tự động khi export.

---

## 8. Tổng kết: 47 giá trị cần chuyển thành config

| Nhóm | Số giá trị |
|---|---|
| Tỉ lệ quy đổi | 5 |
| Lợi nhuận ADS nhập tay | 14 *(bị loại bỏ, giữ để đối chiếu)* |
| Target | 9 |
| Tỉ lệ thưởng | 8 tổ hợp nhân viên × tháng |
| Lương | 4 |
| Classification / Adjustment | 7 |

**Không giá trị nào trong danh sách này được phép xuất hiện dưới dạng literal
trong mã nguồn ứng dụng.** Kiểm chứng bằng `grep` là một REQUIRED check ở mọi
Completion Gate của Phase 1 trở đi.
