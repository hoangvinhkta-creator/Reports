# 06 — Xác nhận rule ADS trên dữ liệu thật

Đáp ứng mục 27.6 đặc tả: *"Xác nhận cách cột Ghi chú/Diễn giải trong file thô
đang lưu chuỗi ADS và kiểm thử rule ở cấp OrderID."*

---

## 1. Kết luận đứng đầu

> **Chuỗi "ADS" không xuất hiện dù chỉ một lần trong bất kỳ ô nào của cả hai
> file mẫu.**

| Kiểm tra | Kết quả |
|---|---|
| Số ô chứa "ADS" trong `So_chi_tiet_ban_hang.xlsx` | **0** / 11.765 dòng |
| Số ô chứa "ADS" trong `Bao_cao_Kinh_doanh_2026.xlsx` | **0** / 59 sheet |
| Số Số BH khớp **rule từ khóa** | **0** / 8.714 |
| Số Số BH thành `TINPHAT_ADS` nhờ **mặc định cấp nhân viên** (DEC-009) | **1.108** / 8.714 = 12,7 % |
| Số Số BH còn lại là `PERSONAL` | **7.606** / 8.714 |

Dòng thứ tư là toàn bộ đơn của `Tín Phát` — chúng thành ADS nhờ cấu hình mặc
định, không nhờ từ khóa. Xem §7.

Tìm kiếm không phân biệt hoa/thường, sau khi chuẩn hóa Unicode NFC và gộp
khoảng trắng — đúng quy trình mục 13 đặc tả. Cũng đã quét cả **công thức**, chứ
không chỉ giá trị hiển thị, phòng trường hợp chuỗi nằm trong một `IF` nào đó.

Rule ADS được xây dựng **đúng nguyên văn đặc tả** và đã kiểm thử đầy đủ, nhưng
trên dữ liệu hiện có nó luôn trả về `PERSONAL`. Đây là kết quả đúng của một
rule đúng chạy trên dữ liệu chưa có dấu hiệu — **không phải lỗi**.

---

## 2. Không có cột `Ghi chú` — chỉ có `Diễn giải`

File thô có 17 cột, không cột nào tên `Ghi chú`. Cột duy nhất chứa nội dung
nghiệp vụ là **`Diễn giải`** (cột thứ 3, header ở dòng 4, mô tả ở dòng 5 là
`Diễn giải chung`).

Mục 13 đặc tả đã dự liệu đúng tình huống này:

> *"Đọc tất cả cột khả dĩ chứa ghi chú: ưu tiên Ghi chú; **nếu file nguồn chỉ
> có Diễn giải thì dùng Diễn giải**."*

→ Công cụ đọc `Diễn giải`. Nếu sau này ERP xuất thêm cột `Ghi chú`, engine nối
hai trường lại để kiểm tra nhưng vẫn lưu riêng giá trị gốc, đúng như đặc tả.

---

## 3. Cột `Diễn giải` hiện đang chứa gì

11.737 / 11.765 dòng có nội dung. Nhưng phần lớn **do ERP sinh tự động**:

| Mẫu nội dung | Số dòng | Nguồn |
|---|---|---|
| `Bán hàng CÔNG TY CỔ PHẦN ĐIỆN MÁY 88 HÀ NỘI` | 255 | ERP tự sinh: `"Bán hàng " + Tên KH` |
| `Bán hàng Điện Máy Long Châu 0859826197` | 107 | ERP tự sinh |
| `Bán hàng CÔNG TY TNHH ĐIỆN TỬ HOÀN KIẾM` | 104 | ERP tự sinh |
| `THU TIỀN LUÔN` | 61 | **Người nhập gõ tay** |
| `Giao lắp m2/1`, `Giao 11H trưa mai 31/12`, `lắp chiều nay càng sớm càng tốt` | rải rác | **Người nhập gõ tay** |

Kết quả dò các từ khóa có thể liên quan đến kênh quảng cáo:

| Từ khóa | Số dòng chứa |
|---|---|
| `ADS` | **0** |
| `QUẢNG CÁO` | 0 |
| `WEB` | 0 |
| `FACEBOOK` / `FB` | 0 |
| `SHOPEE` / `TIKTOK` / `LIVE` / `MKT` | 0 |
| `ONLINE` | 27 |
| `ZALO` | 2 |

Không có dấu hiệu nào cho thấy nguồn đơn từng được ghi nhận trong file thô,
dưới bất kỳ hình thức nào.

**Đã xác nhận (DEC-011):** cột `Diễn giải` **sửa được**. Quy ước vận hành:
ERP để mặc định `"Bán hàng " + Tên KH`; nhân viên chỉ sửa khi đơn là ADS.

Hệ quả cho engine: ghi chú dạng mẫu ERP là **trường hợp bình thường**, không
phải dấu hiệu thiếu dữ liệu. Không được đưa vào Review Queue chỉ vì ghi chú
trông tự động.

---

## 4. Nguồn đơn ADS hiện đang được ghi nhận ở đâu

Không ghi ở đâu trong dữ liệu — nó nằm **trong công thức Summary**, dưới dạng
một con số gõ tay:

```
Summary 2026!F8   =(G8-37270)/5.5% + 37270/7.5%       ' Kiên, 01.2026
Summary 2026!F45  =(G45-3770-16190)/5.5% + (3770+16190)/7.5%   ' Hoàng, 05.2026
```

`37270` là tổng lợi nhuận (nghìn đồng) của các đơn ADS trong tháng — do người
làm báo cáo tự cộng từ trí nhớ hoặc từ một nguồn nằm ngoài hệ thống. Trường hợp
`3770+16190` cho thấy rõ: hai đơn được cộng tay ngay trong ô công thức.

**Danh sách đầy đủ 14 con số này ở tài liệu 04 §2.** Tổng đến tháng 08.2026:
Hoàng 83.220 · Kiên 89.515 (nghìn đồng).

Đây chính là thứ công cụ thay thế.

---

## 5. Kiểm thử rule ở cấp OrderID — E1

Chạy:

```bash
python tools/analysis/verify_ads_rule.py --raw data/samples/So_chi_tiet_ban_hang.xlsx
```

Kết quả thực tế (2026-08-22):

```
Spec section 29 — minimum test cases for the ADS rule
------------------------------------------------------------------------------
  [PASS] 1  Một order 1 dòng, ghi chú 'ADS'                   -> TINPHAT_ADS  (Auto:ADS Rule)
  [PASS] 2  Ghi chú 'ads facebook'                            -> TINPHAT_ADS  (Auto:ADS Rule)
  [PASS] 3  Ghi chú 'Đơn Ads web'                             -> TINPHAT_ADS  (Auto:ADS Rule)
  [PASS] 4  Order 4 dòng, dòng 3 có 'ADS', còn lại trống      -> TINPHAT_ADS  (Auto:ADS Rule)
  [PASS] 5  Không dòng nào có ADS                             -> PERSONAL     (Auto:Default)
  [PASS] 6  Rule auto = ADS nhưng user override PERSONAL      -> PERSONAL     (Manual)
  [PASS] 7  User reset override                               -> TINPHAT_ADS  (Auto:ADS Rule)
  [PASS] 8a Nhân viên có đơn ADS trong tháng                  -> TINPHAT_ADS  (Auto:ADS Rule)
  [PASS] 8b Cùng nhân viên, đơn không ADS                     -> PERSONAL     (Auto:Default)
  [PASS] 9  Chữ thường hoàn toàn                              -> TINPHAT_ADS  (Auto:ADS Rule)
  [PASS] 10 Khoảng trắng thừa                                 -> TINPHAT_ADS  (Auto:ADS Rule)
  [PASS] 11 Ghi chú None                                      -> PERSONAL     (Auto:Default)
  [PASS] 12 Override sang ADS khi auto = PERSONAL             -> TINPHAT_ADS  (Manual)
------------------------------------------------------------------------------
  13/13 passed

Real raw file — So_chi_tiet_ban_hang.xlsx
------------------------------------------------------------------------------
  distinct orders           : 8714
  classified TINPHAT_ADS    : 0
  classified PERSONAL       : 8714
```

- **Case 1–8** là 8 test case bắt buộc của mục 29 đặc tả. Case 8 tách làm 8a/8b
  để thể hiện đúng ý "một nhân viên có cả đơn ADS lẫn đơn Personal trong một
  tháng".
- **Case 9–12** là bốn case bổ sung cho các yêu cầu ở mục 13 mà mục 29 không
  liệt kê: chữ thường, khoảng trắng thừa, ghi chú rỗng, và override theo chiều
  ngược lại.
- Cột trong ngoặc là `SourceOfValue` theo mục 7 đặc tả — mỗi dòng phải nói được
  giá trị của nó từ đâu ra.

Mã nguồn: `tools/analysis/verify_ads_rule.py`. Đây là bản tham chiếu của rule;
`lead_source_engine` ở TASK-104 phải cho kết quả giống hệt trên cùng bộ case.

---

## 6. Hệ quả và việc phải làm

### 6.1. Với dữ liệu lịch sử 01–06.2026

Toàn bộ 8.714 đơn sẽ ra `PERSONAL`. Nếu chạy công cụ trên dữ liệu này và xuất
báo cáo, **doanh thu quy đổi của Hoàng và Kiên sẽ thấp hơn báo cáo hiện tại**,
vì phần lợi nhuận đang được quy đổi ở 7,5 % sẽ rơi về 5,5 %.

Cách xử lý: dùng Manual Override ở cấp OrderID cho các đơn ADS lịch sử. Bảng ở
tài liệu 04 §2 là mục tiêu để đối chiếu — khi override xong, tổng lợi nhuận ADS
mỗi kỳ phải khớp với con số đang gõ tay trong công thức.

Nếu chủ dự án không muốn truy lại từng đơn lịch sử, phương án thay thế là nhập
thẳng số lợi nhuận ADS theo nhân viên-tháng cho giai đoạn trước khi áp dụng quy
ước mới, đánh dấu rõ là dữ liệu di trú. Cần quyết định ở GATE-01.

### 6.2. Với dữ liệu mới

Rule chỉ bắt đầu có tác dụng khi nhân viên thực sự gõ "ADS". Công cụ phải làm
cho việc này **không thể bị bỏ quên trong im lặng**:

- Mỗi lần import, hiển thị rõ: `X / Y đơn được phân loại TINPHAT_ADS`.
- Nếu một tháng có **0 đơn ADS**, đưa cảnh báo vào Review Queue thay vì coi là
  bình thường — vì với lịch sử đang có, 0 nhiều khả năng nghĩa là "chưa ai gõ"
  chứ không phải "tháng này không có đơn ADS".
- Danh sách từ khóa nằm ở `config/lead_source.yaml`. Thêm `QUẢNG CÁO`, `WEB`
  hay bất kỳ ký hiệu nào khác **không cần sửa code**.

### 6.3. Trạng thái các câu hỏi

| # | Câu hỏi | Trạng thái |
|---|---|---|
| **C1** | Tín Phát quy đổi 7,5 % cho mọi đơn — có đặt mặc định ADS riêng không? | **Đã chốt — DEC-009.** `default_lead_source: TINPHAT_ADS`. Xem §7. |
| **C6** | ERP có cho sửa `Diễn giải` không? | **Đã chốt — DEC-011.** Sửa được; mặc định giữ nguyên, chỉ sửa khi là đơn ADS. |
| **C7** | Xử lý đơn ADS lịch sử thế nào? | **Đã chốt — DEC-012.** Nhập 14 số theo nhân viên-tháng làm dữ liệu di trú. Xem §8. |

---

## 7. Thứ tự ưu tiên sau DEC-009

```
LeadSourceFinal =
    1. Manual Override                    → SourceOfValue = "Manual"
    2. Rule ADS trên Diễn giải            → "Auto:ADS Rule"
    3. Default của nhân viên (nếu có)     → "Auto:Employee Default (<tên>)"
    4. Default toàn hệ thống (PERSONAL)   → "Auto:Default"
```

Default cấp nhân viên nằm **dưới** rule ADS và **trên** default toàn hệ thống.
Vì vậy nó chỉ có thể nâng một đơn lên ADS, **không bao giờ hạ** một đơn mà rule
đã bắt được. Override tay vẫn thắng cả hai.

Không có gì trong code biết tới cái tên "Tín Phát" — đó là một dòng trong
`config/employees.yaml`. Bất kỳ nhân viên hay kênh nào cũng đặt được mặc định
riêng.

Kiểm chứng (case 13–17 trong `verify_ads_rule.py`, **18/18 PASS**):

```
  [PASS] 13 Tín Phát, ghi chú mặc định ERP, không có ADS      -> TINPHAT_ADS  (Auto:Employee Default (Tín Phát))
  [PASS] 14 Tín Phát, ghi chú có ADS                          -> TINPHAT_ADS  (Auto:ADS Rule)
  [PASS] 15 Tín Phát, quản lý override về PERSONAL            -> PERSONAL     (Manual)
  [PASS] 16 Ly, ghi chú mặc định ERP — không ăn theo Tín Phát -> PERSONAL     (Auto:Default)
  [PASS] 17 Ly, ghi chú có ADS                                -> TINPHAT_ADS  (Auto:ADS Rule)
```

**Hệ quả tốt:** số liệu lịch sử của Tín Phát **không cần di trú gì cả** — vốn
đã là 7,5 %. Phạm vi của C7 thu hẹp lại chỉ còn Hoàng và Kiên.

---

## 8. C7 — dữ liệu ADS lịch sử của Hoàng và Kiên

### Vấn đề

Chia cho tỉ lệ nhỏ hơn thì ra số lớn hơn. Quy đổi ở 5,5 % cho **nhiều** doanh
thu quy đổi hơn quy đổi ở 7,5 %. Nói cách khác: **đánh dấu một đơn là ADS làm
GIẢM doanh thu quy đổi của nhân viên** — đúng logic kinh doanh, vì lead do công
ty chạy quảng cáo mang lại thì công của nhân viên ít hơn.

Hệ quả: nếu không đánh dấu các đơn ADS lịch sử, Hoàng và Kiên được tính **cao
hơn** con số đang báo cáo.

| NV / kỳ | LN KPI | X (ADS) | CR có tách | CR không tách | Chênh | % |
|---|---:|---:|---:|---:|---:|---:|
| 01.2026 Hoàng | 83.120 | 2.750 | 1.497.939 | 1.511.273 | 13.333 | 0,9 % |
| 02.2026 Hoàng | 65.190 | 35.520 | 1.013.055 | 1.185.273 | 172.218 | **17,0 %** |
| 03.2026 Hoàng | 48.039 | 7.790 | 835.667 | 873.436 | 37.770 | 4,5 % |
| 04.2026 Hoàng | 59.891 | 17.200 | 1.005.533 | 1.088.927 | 83.394 | 8,3 % |
| 05.2026 Hoàng | 56.660 | 19.960 | 933.406 | 1.030.182 | 96.776 | 10,4 % |
| 06.2026 Hoàng | 20.866 | 0 | 379.382 | 379.382 | 0 | 0 % |
| 01.2026 Kiên | 97.270 | 37.270 | 1.587.842 | 1.768.545 | 180.703 | **11,4 %** |
| 02.2026 Kiên | 58.655 | 1.500 | 1.059.182 | 1.066.455 | 7.273 | 0,7 % |
| 03.2026 Kiên | 45.390 | 11.000 | 771.939 | 825.273 | 53.333 | 6,9 % |
| 04.2026 Kiên | 37.840 | 9.230 | 643.248 | 688.000 | 44.752 | 7,0 % |
| 05.2026 Kiên | 56.920 | 7.820 | 996.994 | 1.034.909 | 37.915 | 3,8 % |
| 06.2026 Kiên | 39.870 | 7.565 | 688.230 | 724.909 | 36.679 | 5,3 % |
| 07.2026 Kiên | 98.260 | 7.565 | 1.749.867 | 1.786.545 | 36.679 | 2,1 % |
| 08.2026 Kiên | 41.670 | 7.565 | 720.958 | 757.636 | 36.679 | 5,1 % |
| **TỔNG** | | | **13.883.242** | **14.720.745** | **837.503** | **6,0 %** |

Đơn vị nghìn đồng. Nếu bỏ qua hoàn toàn, hai người được cộng thêm **837.503
nghìn đồng ≈ 837 triệu** doanh thu quy đổi trong 8 tháng, kéo theo khoảng
**2.967 nghìn ≈ 3,0 triệu đồng tiền thưởng** tính theo đúng tỉ lệ thưởng từng
tháng ở tài liệu 04 §4.

### Quyết định — DEC-012

**Nhập 14 số ở cột `X` trong bảng trên làm dữ liệu di trú**, theo nhân viên và
tháng, đánh dấu rõ là số khai báo cho quá khứ chứ không phải số do rule tính ra.

Phương án truy từng đơn đã bị loại vì **không khả thi**: không có dấu vết nào
trong bất kỳ file nào cho biết đơn nào là ADS. Con số `3770+16190` của Hoàng
tháng 05 cho thấy chúng được cộng tay từ một nguồn nằm ngoài hệ thống.

### Yêu cầu kỹ thuật kéo theo

1. `conversion_engine` cần một đường vào riêng cho số di trú, bỏ qua phân loại
   ở cấp đơn.
2. Số di trú phải **hiển thị khác** số do rule sinh ra, cả trên UI lẫn trong
   file xuất. Đó là một lời khai về quá khứ, không phải một phép tính.
3. Hai đường phải **loại trừ nhau** trong cùng một nhân viên-tháng. Nếu một
   tháng vừa có số di trú vừa có đơn được rule phân loại ADS thì đó là **xung
   đột đưa vào Review Queue**, không phải hai số cộng lại.
4. Tháng bắt đầu áp dụng quy ước mới (cut-over) là cấu hình: trước tháng đó
   dùng số di trú, từ tháng đó trở đi dùng rule.
5. **Mốc đối chiếu bắt buộc (REQUIRED check của TASK-108):** với 14 số đã nạp,
   tổng doanh thu quy đổi của Hoàng + Kiên trong 01–08.2026 phải bằng đúng
   **13.883.242** nghìn đồng.
