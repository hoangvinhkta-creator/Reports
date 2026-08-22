# 05 — Exception và công thức không đồng nhất

Đáp ứng mục 27.5 đặc tả.

Theo **DEC-007**: công cụ **tính đúng và báo cáo chênh lệch**, không sao chép
lỗi. Nếu chủ dự án muốn giữ nguyên một con số sai vì lý do đối chiếu lịch sử,
điều đó trở thành một cờ cấu hình có tên rõ ràng — không phải mặc định thầm lặng.

---

## Nhóm A — Lỗi công thức trong file mẫu

### A1. Số SP trừ nhầm một tỉ lệ phần trăm — **mức độ: cao**

```
E1 = SUM(E3:E945) - D1 - C1
```

- `D1` = số dòng phụ kiện/vận chuyển → trừ đi là **đúng ý định**.
- `C1` = `SUMIF(C,"Kho",H)/H1` → là **tỉ lệ phần trăm** (khoảng 0,05–0,3).

Trừ một tỉ lệ khỏi một số lượng không có nghĩa gì. Hệ quả: mọi ô "Tổng số SP"
trong Summary đều là **số thập phân**:

| Sheet | Số SP báo cáo |
|---|---|
| `01.2026 Tín Phát` | 387,6 |
| `06.2026 Tín Phát` | 178,8 |
| `06.2026 Kiên` | 62,6 |
| `06.2026 Ly` | 180,8 |
| `01.2026 Hoàng` | 176,5 |

**Xử lý:** `TotalProducts = SUM(Quantity)` trên các dòng được Classification
đánh dấu là sản phẩm thật. Kết quả sẽ là số nguyên và **lớn hơn** con số hiện
tại khoảng 0,05–0,3 đơn vị. Chênh lệch nhỏ nhưng phải nói ra.

Layout kênh không dính lỗi này: `D1 = SUM(D3:D452) - C1` với `C1` là `COUNTIF`
thật — nên số SP của Nội thành/Gia dụng là số nguyên (1517, 186, 656, 587).

### A2. Dòng tổng tháng bỏ sót nhân viên — **mức độ: cao**

Trong cùng một dòng tổng (ví dụ dòng 11 của tháng 01):

| Cột | Công thức | Bao gồm |
|---|---|---|
| `E` Tổng bán | `=SUM(E4:E9)` | Ly, Thắng, Tín Phát, Hoàng, Kiên, **Nội thành** |
| `F` **DS quy đổi** | `=SUM(F4:F8)` | Ly, Thắng, Tín Phát, Hoàng, Kiên |
| `G` Tổng lợi nhuận | `=SUM(G4:G9)` | … + **Nội thành** |
| `K` Lợi nhuận thực tế | `=SUM(K4:K9)` | … + **Nội thành** |

**Không cột nào bao gồm Gia dụng** (dòng 10), và **DS quy đổi còn bỏ cả Nội
thành**. Ba cột trong cùng một dòng tổng có ba phạm vi khác nhau.

**Sai số cụ thể tháng 01.2026** (nghìn đồng, tính lại từ `sheet_totals` trong
`evidence.json`):

| Đối tượng | DS quy đổi | Có trong `SUM(F4:F8)`? |
|---|---:|---|
| Ly | 1.638.455 | Có |
| Thắng | 1.843.455 | Có |
| Tín Phát | 3.174.867 | Có |
| Hoàng | 1.497.939 | Có |
| Kiên | 1.587.842 | Có |
| **Tổng đang báo cáo** | **9.742.558** | |
| Nội thành | 14.452.000 | **Không** |
| Gia dụng | 187.125 | **Không** |
| **Tổng đúng** | **24.381.683** | |

**Tổng DS quy đổi tháng 01.2026 đang thiếu 60,0 %** — riêng Nội thành đã lớn
hơn tổng của cả 5 nhân viên cá nhân cộng lại.

**Xử lý:** tổng luôn cộng đủ mọi đối tượng có `include_in_kpi = true`. Nếu
chính sách thật sự là loại kênh khỏi tổng DS quy đổi, đó là cấu hình
`include_in_company_total`, không phải một khoảng `SUM` bị gõ thiếu.

### A3. Sheet kênh chia đôi mọi tổng — **ĐÃ GIẢI THÍCH (DEC-015)**

```
Nội thành / Gia dụng:  G1 = SUM(G3:G452)/2      H1 = SUM(H3:H452)/2
```

Nhưng `L1 = SUM(L2:L452)` **không chia 2** — và bắt đầu từ dòng 2 chứ không
phải dòng 3.

**Nguyên nhân (chủ dự án xác nhận):** sheet kênh có **dòng tổng theo ngày nằm
lẫn ngay trong vùng dữ liệu**. `SUM` cộng cả dòng chi tiết lẫn dòng tổng ngày,
nên mọi con số bị nhân đôi. Chia 2 là cách bù đúng cho layout đó.

Cùng cơ chế ở `Summary 2026!E3 = SUM(E4:E902)/2`: vùng chứa cả dòng nhân viên
lẫn dòng tổng tháng.

**Vậy phép chia 2 không sai — nhưng nó vô hình.** Ai thêm một dòng sai chỗ, hoặc
đọc sheet mà không biết quy ước này, sẽ nhận một con số lệch đúng 2 lần. Không
có gì trong sheet cho biết dòng nào là chi tiết, dòng nào là tổng.

**Cách công cụ làm thay (DEC-015):**

1. Dòng dữ liệu chỉ là dữ liệu. Không có dòng tổng nào nằm trong vùng dữ liệu.
2. Tổng tính riêng từ tập dòng chi tiết, mỗi con số cộng đúng **một** lần.
3. Khi xuất Excel, dòng tổng ngày/tháng vẫn hiện — nhưng dưới dạng **outline /
   group row** của Excel và mang cột `RowType` (`DETAIL` / `DAY_TOTAL` /
   `MONTH_TOTAL`) để nằm ngoài mọi vùng `SUM`, đồng thời lọc được.
4. **Không có phép chia bù nào trong toàn bộ mã nguồn.** Một `/2` xuất hiện
   trong logic tổng hợp được coi là lỗi.

### A4. Tham chiếu sai sheet — **mức độ: cao, sai số liệu trực tiếp**

```
Summary 2026!D64  =  '07.2026 Tín Phát'!$E$1
```

Dòng 64 là **Nội thành** tháng 07, nhưng số SP lại lấy từ sheet **Tín Phát**.
Mọi dòng Nội thành khác đều lấy đúng `'MM.2026 Nội thành'!$D$1`.

**Xử lý:** biến mất khi Summary được sinh tự động từ Working Data.

### A5. `COUNTIF` quét cả dòng tiêu đề — **mức độ: thấp**

```
D1 = COUNTIF(D2:D945, "chân máy giặt đa năng") + …
```

Vùng bắt đầu từ `D2` — dòng tiêu đề (`Mã Sản phẩm`). Không gây sai số vì tiêu
đề không khớp từ khóa nào, nhưng cho thấy vùng công thức được kéo tay chứ không
được kiểm tra. Các công thức `SUM` bên cạnh đều bắt đầu từ `D3`.

### A6. So sánh tháng trước bằng số cứng — **mức độ: trung bình**

Tháng 01.2026 không có tháng trước trong workbook, nên cột `I` dùng số cứng
của tháng 12.2025:

| Ô | Công thức | Nhân viên |
|---|---|---|
| `I4` | `=F4/1571182` | Ly |
| `I5` | `=F5/1624818` | Thắng |
| `I6` | `=F6/3863427` | Tín Phát |
| `I7` | `=F7/1450818` | Hoàng |
| `I8` | `=F8/1374491` | Kiên |
| `I9` | `=F9/13335100` | Nội thành |
| `I11` | `=E11/9884736` | Tổng công ty |

Từ tháng 02 trở đi công thức tham chiếu đúng ô tháng trước (`=F13/F4`).

**Xử lý:** lấy từ dữ liệu kỳ trước khi có. Không có thì để trống — **không bịa
số, không dùng 0**, vì `x/0` và `x/null` cho ra hai loại sai khác nhau và cả
hai đều tệ hơn một ô trống trung thực.

---

## Nhóm B — Không đồng nhất giữa các nhân viên và các tháng

### B1. Hoàng: công thức tách bucket biến mất từ tháng 06

| Kỳ | Công thức |
|---|---|
| 01–05.2026 | `=(G−X)/5.5% + X/7.5%` |
| **06.2026** | `=G55/5.5%` |
| 07–08.2026 | *(không có sheet Hoàng)* |

Không rõ tháng 06 Hoàng thật sự không có đơn ADS, hay người nhập quên tách.
Không kiểm chứng được từ dữ liệu — file thô không có dấu hiệu ADS nào.

### B2. Kiên: cùng một con số ba tháng liền

`7565` xuất hiện y hệt ở 06, 07 và 08.2026. Xác suất ba tháng có đúng cùng một
tổng lợi nhuận ADS đến đơn vị nghìn đồng là rất thấp — nhiều khả năng công thức
được copy sang tháng mới mà chưa cập nhật số.

**Đây chính là loại lỗi mà công cụ tồn tại để loại bỏ.**

### B3. Nhân viên xuất hiện và biến mất giữa chừng

| Nhân viên | Có mặt | Ghi chú |
|---|---|---|
| Linh | chỉ 03.2026 | Dòng Summary ghi `Linh`, sheet tên `03.2026 Fanpage` |
| Fanpage | 04, 05.2026 | Cùng thực thể với `Linh`, khác tên |
| Thắng | 01–06.2026 | Biến mất từ 07 |
| Hoàng | 01–06.2026 | Biến mất từ 07 |

Tên hiển thị ở Summary và tên sheet **không khớp** với nhau ở trường hợp
Linh/Fanpage. Đúng lý do vì sao mapping phải có `effective_from`/`effective_to`
thay vì một danh sách phẳng.

### B4. Sáu biến thể layout

Xem tài liệu 01 §4. Bốn trong sáu biến thể chỉ khác nhau ở ký tự rác trong ô
`R1` (`,` hoặc `.`) và vùng công thức — dấu vết của việc copy sheet qua nhiều
tháng. Một biến thể (kênh) khác thật sự.

### B5. `G1` trùng `C1` nhưng viết khác

```
C1 = (SUMIF(C3:C945,"Kho",H3:H945)/H1)     ' vùng có giới hạn
G1 = SUMIF(C:C,"Kho",H:H)/H1               ' quét toàn cột
```

Hai công thức cùng ý nghĩa, một cái quét cả cột nên gộp luôn dòng 1 và dòng
tiêu đề. Sheet `01.2026 Hoàng` và `02.2026 Hoàng` **thiếu hẳn** `G1`.

---

## Nhóm C — Chênh lệch giữa file thô và file báo cáo

Bảng đối chiếu đầy đủ, sinh từ `evidence.json`. Đơn vị nghìn đồng.

| Kỳ / NV | Đơn thô | Đơn BC | Lệch | DS thô | DS BC | Lệch % | LN thô | LN BC |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 01.2026 Tín Phát | 254 | **254** | **0** | 3.564.610 | 3.544.010 | 0,6 % | 240.033 | 238.115 |
| 01.2026 Ly | 100 | 99 | 1 | 1.775.850 | 1.715.865 | 3,5 % | 121.436 | 90.115 |
| 01.2026 Thắng | 65 | 59 | 6 | 1.642.235 | 1.579.060 | 4,0 % | 107.998 | 101.390 |
| 01.2026 Hoàng | 86 | 79 | 7 | 1.355.063 | 1.384.985 | −2,2 % | 77.730 | 83.120 |
| 01.2026 Kiên | 100 | 97 | 3 | 1.327.240 | 1.387.110 | −4,3 % | 88.852 | 97.270 |
| 02.2026 Tín Phát | 231 | 223 | 8 | 2.680.927 | 2.516.130 | 6,5 % | 208.626 | 176.735 |
| 02.2026 Hoàng | 81 | **81** | **0** | 1.064.750 | 1.063.130 | 0,2 % | 57.007 | 65.190 |
| 03.2026 Tín Phát | 156 | **156** | **0** | 2.180.880 | 2.070.380 | 5,3 % | 121.392 | 142.045 |
| 03.2026 Hoàng | 60 | **60** | **0** | 793.330 | 786.290 | 0,9 % | 49.485 | 48.039 |
| 03.2026 Kiên | 66 | **66** | **0** | 658.370 | 659.960 | −0,2 % | 45.032 | 45.390 |
| 04.2026 Kiên | 52 | **52** | **0** | 598.350 | 574.400 | 4,2 % | 38.577 | 37.840 |
| 05.2026 Hoàng | 33 | **33** | **0** | 875.800 | 873.550 | 0,3 % | 46.380 | 56.660 |
| 06.2026 Tín Phát | 146 | **146** | **0** | 1.925.272 | 1.799.920 | 7,0 % | 95.957 | 119.236 |
| 06.2026 Hoàng | 31 | **31** | **0** | 380.375 | 382.950 | −0,7 % | 19.254 | 20.866 |
| 06.2026 Ly | 89 | 98 | −9 | 1.156.490 | 1.158.490 | −0,2 % | 60.236 | 63.010 |

*(30 tổ hợp kỳ × nhân viên; bảng trên trích các dòng đáng chú ý. Bảng đầy đủ
sinh lại được từ `evidence.json`.)*

### Đọc bảng này thế nào

**Số đơn khớp tuyệt đối ở 9/30 kỳ và lệch ≤ 3 đơn ở 22/30 kỳ.** Với 8.714 đơn
và không có OrderID nào trong file báo cáo, mức khớp này chỉ có thể xảy ra nếu
`COUNT DISTINCT Số BH` đúng là cách đếm và mapping nhân viên đúng.

Các nguồn chênh lệch đã nhận diện được:
- **Loại trừ tay:** một số đơn bị bỏ khỏi báo cáo (đơn hủy, đơn nội bộ, đơn
  chuyển sang người khác). Không có dấu vết nào trong file để biết đơn nào.
- **Doanh số lệch 0,2 %–7 %:** báo cáo tính `Giá bán × SL` sau khi người nhập
  đã sửa giá; file thô giữ giá gốc ERP.
- **Lợi nhuận lệch nhiều hơn doanh số** (Ly 01.2026: 121.436 vs 90.115, lệch
  26 %): đúng như dự đoán, vì lợi nhuận KPI đã qua điều chỉnh tay còn lợi nhuận
  ERP thì chưa.
- **06.2026 Ly có 98 đơn trên báo cáo nhưng chỉ 89 trong file thô:** báo cáo
  nhiều hơn nguồn. Nghĩa là có đơn được thêm tay, hoặc đơn của cuối tháng 05
  được ghi sang tháng 06.

**Không kết luận nào ở trên được suy ra từ dữ liệu — chúng là giả thuyết.**
Công cụ sẽ đưa từng chênh lệch vào Review Queue để người biết việc quyết định,
thay vì làm tròn cho khớp.

---

## Tổng kết mức độ ưu tiên

| # | Vấn đề | Ảnh hưởng số liệu | Cần chủ dự án quyết? |
|---|---|---|---|
| A2 | Tổng tháng bỏ sót nhân viên | **Rất lớn** — thiếu > 50 % DS quy đổi tháng | Có |
| A3 | Sheet kênh chia 2 | Không còn — đã giải thích, không tái tạo | Xong — DEC-015 |
| A1 | Số SP trừ nhầm tỉ lệ | Nhỏ (0,05–0,3 SP), và Số SP đã bị hạ ưu tiên | Xong — DEC-013 |
| A4 | Tham chiếu sai sheet | Lớn, 1 ô | Không |
| B2 | Kiên lặp `7565` 3 tháng | Không rõ | Có |
| B1 | Hoàng mất tách bucket từ T06 | Không rõ | Có |
| C | Chênh lệch thô ↔ báo cáo | Trung bình, phân tán | Có, qua Review Queue |
| A6 | Số cứng tháng trước | Nhỏ, chỉ tháng 01 | Không |
| A5 | `COUNTIF` từ dòng 2 | Không | Không |
| B5 | `G1` trùng `C1` | Không | Không |
