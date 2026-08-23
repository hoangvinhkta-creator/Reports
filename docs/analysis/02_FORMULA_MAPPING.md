# 02 — Formula Mapping

Đáp ứng mục 27.2 đặc tả: toàn bộ công thức trong sheet nhân viên và Summary.

Mọi công thức dưới đây trích trực tiếp từ workbook, có trong
`docs/analysis/_evidence/evidence.json`.

---

## 1. Sheet nhân viên — công thức dòng dữ liệu

Layout cá nhân (L1), dòng `n` từ 3 trở đi:

| Ô | Công thức thật | Ý nghĩa | Thành field Working |
|---|---|---|---|
| `Hn` | `=IF(Gn*En=0," ",Gn*En)` | Tổng bán = Giá bán × SL | `TotalSales` |
| `In` | `=IF((Gn-Fn)*En=0," ",(Gn-Fn)*En)` | **Lợi nhuận KPI** = (Giá bán − **Giá nhập TT**) × SL | `EligibleKpiProfit` |
| `Ln` | `=Fn` *(mặc định)* | Giá thực nhập mặc định bằng Giá nhập TT | `AccountingPurchasePrice` |
| `Mn` | `=IF((Gn-Ln)*En=0," ",(Gn-Ln)*En)` | **Lợi nhuận gộp** = (Giá bán − **Giá thực nhập**) × SL | `AccountingProfit` |

### Điểm mấu chốt: hai cột giá nhập nghĩa là gì

Tên cột trong file mẫu gây hiểu nhầm. Bằng chứng từ `06.2026 Tín Phát`:

| Dòng | `F` Giá nhập TT | `L` Giá thực nhập | `J` Giao hàng |
|---|---|---|---|
| 10 | `7950` | `8000` | `KHBH -50` |
| 11 | `=5870-250` | `5870` | `Thợ lắp -200, KHBH -50` |

`F` thấp hơn `L` đúng bằng số ghi trong ghi chú điều chỉnh. Giá nhập thấp hơn
→ lợi nhuận cao hơn → nhân viên được cộng thêm. Vậy:

- **`L` (Giá thực nhập) = giá nhập kế toán thật** → `AccountingPurchasePrice`
- **`F` (Giá nhập TT) = giá nhập sau điều chỉnh KPI** → `KpiPurchasePrice`

Xác nhận thêm: Summary gọi cột lấy từ `M1` là **"Lợi nhuận thực tế"** — mà `M`
tính từ `L`. Đúng chiều.

Ánh xạ sang công thức đặc tả mục 11:
```
KpiPurchasePrice = AccountingPurchasePrice + KpiPurchaseAdjustment
       F         =            L            +   (số âm trong cột J)
```

**635/18.148 dòng** có `L` bị nhập tay thay vì `=F` — đó là các dòng có điều chỉnh.

---

## 2. Sheet nhân viên — công thức dòng 1 (tổng nạp vào Summary)

Layout cá nhân, ví dụ `06.2026 Tín Phát` (vùng `3:945`):

| Ô | Công thức thật | Ý nghĩa | Summary lấy vào cột |
|---|---|---|---|
| `B1` | `=count(B3:B945)` | **Tổng đơn** — đếm ô `Trans` có số | `E` Tổng đơn |
| `C1` | `=(SUMIF(C3:C945,"Kho",H3:H945)/H1)` | Tỉ lệ doanh số hàng từ Kho | `J` Tỉ lệ tồn kho |
| `D1` | `=COUNTIF(D2:D945,"chân máy giặt đa năng")+COUNTIF(D2:D945,"giá treo tivi")+COUNTIF(D2:D945,"vận chuyển")` | Đếm dòng phụ kiện/vận chuyển | *(chỉ dùng nội bộ)* |
| `E1` | `=SUM(E3:E945)-D1-C1` | **Số SP** = tổng SL − dòng phụ − ??? | `D` Tổng số SP |
| `G1` | `=SUMIF(C:C,"Kho",H:H)/H1` | Trùng `C1`, quét cả cột | — |
| `H1` | `=SUM(H3:H945)` | **Tổng bán** | `E` Tổng bán |
| `I1` | `=SUM(I3:I945)` | **Tổng lợi nhuận KPI** | `G` Tổng lợi nhuận |
| `J1` | `=I1/H1` | Tỉ suất lợi nhuận | `H` Tỉ suất lợi nhuận |
| `K1` | `=SUM(K3:K945)` | Tổng chi phí giao | — |
| `M1` | `=SUM(M3:M945)` | **Tổng lợi nhuận gộp** | `K` Lợi nhuận thực tế |

> `E1` trừ `C1` — mà `C1` là **phần trăm**. Đây là lỗi, xem tài liệu 05 §1.

Layout kênh (L6), ví dụ `06.2026 Nội thành`:

| Ô | Công thức thật | Khác biệt |
|---|---|---|
| `B1` | `=count(B3:B452)` | Kênh không điền `Trans` → **B1 = 0** ở mọi sheet kênh |
| `C1` | `=COUNTIF(C2:C452,…)` | Đếm dòng phụ |
| `D1` | `=SUM(D3:D452)-C1` | Số SP |
| `G1` | `=SUM(G3:G452)/2` | **Chia 2** — xem tài liệu 05 §3 |
| `H1` | `=SUM(H3:H452)/2` | **Chia 2** |
| `I1` | `=H1/G1` | Tỉ suất |
| `L1` | `=SUM(L2:L452)` | Lợi nhuận gộp — bắt đầu từ dòng **2**, không phải 3 |
| `R1` | `=SUMIF(Q:Q,"<1%",G:G)` | Doanh số của dòng biên lợi nhuận < 1% |
| `S1` | `=SUMIF(Q:Q,"<1%",H:H)` | Lợi nhuận tương ứng |

---

## 3. Summary 2026 — công thức từng dòng nhân viên

Ví dụ dòng 4 (`01.2026 Ly`):

| Cột | Công thức | Ý nghĩa | Engine tương ứng |
|---|---|---|---|
| `C` | `='01.2026 Ly'!$B$1` | Tổng đơn | `summary_engine` |
| `D` | `='01.2026 Ly'!$E$1` | Tổng số SP | `summary_engine` |
| `E` | `='01.2026 Ly'!$H$1` | Tổng bán | `summary_engine` |
| **`F`** | **`=G4/5.5%`** | **Doanh thu quy đổi** | **`conversion_engine`** |
| `G` | `='01.2026 Ly'!$I$1` | Tổng lợi nhuận KPI | `profit_engine` |
| `H` | `=G4/E4` | Tỉ suất lợi nhuận | `summary_engine` |
| `I` | `=F4/1571182` | Vs. tháng trước | *(số cứng — xem tài liệu 05 §6)* |
| `J` | `='01.2026 Ly'!$C$1` | Tỉ lệ tồn kho | `summary_engine` |
| `K` | `='01.2026 Ly'!$M$1` | Lợi nhuận thực tế | `profit_engine` |
| `M` | `1300000` | Target | `config/targets.yaml` |
| `N` | `=IFERROR(F4/M4,"")` | % Target | `summary_engine` |
| `O` | `=F4*0.5%` | Thưởng | `config/commission.yaml` |
| `P` | `28` | Ngày công | nhập tay |
| `Q` | `=P4*4500/26` | Lương cứng | `config/payroll.yaml` |
| `R` | `=IF(P4>=26,30*26,P4*30)` | Phụ cấp | `config/payroll.yaml` |
| `S` | `=IF(P4>0,SUM(O4+Q4+R4),"")` | Tổng lương | `summary_engine` |

### Dòng tổng tháng (ví dụ dòng 11 cho tháng 01)

| Cột | Công thức | Vấn đề |
|---|---|---|
| `E` | `=SUM(E4:E9)` | Gồm Nội thành, **bỏ Gia dụng** (dòng 10) |
| **`F`** | **`=SUM(F4:F8)`** | **Bỏ cả Nội thành lẫn Gia dụng** — xem tài liệu 05 §2 |
| `G` | `=SUM(G4:G9)` | Gồm Nội thành, bỏ Gia dụng |
| `K` | `=SUM(K4:K9)` | Gồm Nội thành, bỏ Gia dụng |
| `M` | `28790000` | Target công ty/tháng |

### Dòng đầu năm (dòng 3)

| Ô | Công thức | Ý nghĩa |
|---|---|---|
| `A3` | `365` | Số ngày trong năm |
| `B3` | `=31+B12+B21+B31` | Số ngày đã trôi qua (cộng tay từng tháng) |
| `C3` | `=B3/A3` | Tiến độ năm |
| `E3` | `=SUM(E4:E902)/2` | Tổng doanh số năm — **chia 2 vì cộng cả dòng tổng tháng** |
| `F3` | `=E3/M3` | % target năm |
| `M3` | `345474000` | Target năm (nghìn đồng) = 12 × 28.790.000 |

---

## 4. Công thức doanh thu quy đổi — bảng đầy đủ 2026

**Dạng chuẩn:** `DS quy đổi = Lợi nhuận KPI / tỉ lệ`

| Đối tượng | Tỉ lệ | Số kỳ dùng |
|---|---|---|
| Ly, Thắng, Linh, Fanpage | **5,5 %** | mọi kỳ |
| Tín Phát | **7,5 %** | mọi kỳ |
| Nội thành | **2 %** | mọi kỳ |
| Gia dụng | **8 %** | mọi kỳ |

**Dạng tách 2 bucket (chỉ Hoàng và Kiên):**

```
= (LợiNhuận − X) / 5,5%  +  X / 7,5%
```

| Kỳ | Hoàng — X | Kiên — X |
|---|---|---|
| 01.2026 | 2.750 | 37.270 |
| 02.2026 | 35.520 | 1.500 |
| 03.2026 | 7.790 | 11.000 |
| 04.2026 | 17.200 | 9.230 |
| 05.2026 | 3.770 + 16.190 | 7.820 |
| 06.2026 | *(không tách)* | 7.565 |
| 07.2026 | *(không có sheet)* | 7.565 |
| 08.2026 | *(không có sheet)* | 7.565 |

> **Đây chính là chức năng chính của công cụ.** `X` là phần lợi nhuận đến từ
> đơn Tín Phát Ads, hiện đang được **gõ tay vào công thức mỗi tháng**. Trong
> `05.2026 Hoàng` nó thậm chí là tổng của hai số rời (`3770+16190`) — dấu vết
> của việc cộng tay từng đơn.
>
> Kiên giữ nguyên `7565` suốt 06, 07, 08.2026 — nhiều khả năng là copy công
> thức tháng trước chứ không phải tính lại. Không kiểm chứng được.

**Ánh xạ sang engine:**

```
PersonalConvertedRevenue = PersonalEligibleProfit / rate(PERSONAL, kỳ)   # 5,5%
AdsConvertedRevenue      = AdsEligibleProfit      / rate(ADS, kỳ)        # 7,5%
TotalConvertedRevenue    = PersonalConvertedRevenue + AdsConvertedRevenue
```

Tỉ lệ tra theo `(scheme, employee, ngày)` từ `config/conversion_rates.yaml`,
có `effective_from` / `effective_to` — **không hard-code** (mục 12 đặc tả).

---

## 5. DataChart 2026

| Vùng | Nội dung |
|---|---|
| `B3:AF14` | Doanh số theo ngày, 12 dòng tháng × 31 cột ngày — nhập tay |
| `AG3:AG14` | `=SUM(B3:AF3)` — tổng tháng |
| `AH3:AH14` | Doanh số cùng kỳ 2025 — số cứng |
| `AI` | `=AGn/AHn` — so cùng kỳ |
| `AJ` | `=AGn/$AJ$2` — so target |
| `AJ2` | `28789481081` — target tháng, **đơn vị VND nguyên** |
| `J15` | `345474000` — target năm, **đơn vị nghìn đồng** |
| `P15` | `=J15/350` — target/ngày, mẫu số **350** chứ không phải 365 |

> `AJ2` và `J15` lệch nhau 1.000 lần về đơn vị trong cùng một sheet. Đây đúng
> là loại lỗi mà DEC-106 (lưu chuẩn VND nguyên) tồn tại để ngăn.

Toàn bộ vùng `B3:AF14` sẽ được `summary_engine` sinh tự động từ Working Data
thay vì nhập tay.
