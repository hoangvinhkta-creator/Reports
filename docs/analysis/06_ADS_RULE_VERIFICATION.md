# 06 — Xác nhận rule ADS trên dữ liệu thật

Đáp ứng mục 27.6 đặc tả: *"Xác nhận cách cột Ghi chú/Diễn giải trong file thô
đang lưu chuỗi ADS và kiểm thử rule ở cấp OrderID."*

> **Cập nhật 2026-08-23 — DEC-119.** `LeadSource` và `ConversionScheme` giờ là
> hai khái niệm độc lập. `LeadSource` có đúng hai giá trị `PERSONAL` và `ADS`;
> giá trị `TINPHAT_ADS` đã bị loại bỏ. Tài liệu này nói về **bước phân giải
> nguồn đơn**; bước phân giải tỉ lệ nằm ở §9 và ADR-104.

---

## 1. Kết luận đứng đầu

> **Chuỗi "ADS" không xuất hiện dù chỉ một lần trong bất kỳ ô nào của cả hai
> file mẫu.**

| Kiểm tra | Kết quả |
|---|---|
| Số ô chứa "ADS" trong `So_chi_tiet_ban_hang.xlsx` | **0** / 11.765 dòng |
| Số ô chứa "ADS" trong `Bao_cao_Kinh_doanh_2026.xlsx` | **0** / 59 sheet |
| Số Số BH khớp **rule từ khóa** | **0** / 8.714 |
| Số Số BH thành `ADS` nhờ **mặc định cấp nhân viên** (DEC-109) | **1.108** / 8.714 = 12,7 % |
| Số Số BH còn lại là `PERSONAL` | **7.606** / 8.714 |

Dòng thứ tư là toàn bộ đơn của `Tín Phát` — chúng thành ADS nhờ cấu hình mặc
định, không nhờ từ khóa. Xem §7.

Lưu ý: đây là con số **nguồn đơn**, không phải tỉ lệ. Việc 1.108 đơn này quy
đổi ở 7,5% là kết quả của bước thứ hai (§9), không phải của bảng trên.

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

**Đã xác nhận (DEC-111):** cột `Diễn giải` **sửa được**. Quy ước vận hành:
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

Kết quả thực tế (2026-08-23, sau DEC-119):

```
LeadSource — spec section 29 + section 13 edge cases + DEC-109
------------------------------------------------------------------------------------------
  [PASS] 1  Một order 1 dòng, ghi chú 'ADS'                   -> ADS      (Auto:ADS Rule)
  [PASS] 2  Ghi chú 'ads facebook'                            -> ADS      (Auto:ADS Rule)
  [PASS] 3  Ghi chú 'Đơn Ads web'                             -> ADS      (Auto:ADS Rule)
  [PASS] 4  Order 4 dòng, dòng 3 có 'ADS', còn lại trống      -> ADS      (Auto:ADS Rule)
  [PASS] 5  Không dòng nào có ADS                             -> PERSONAL (Auto:Default)
  [PASS] 6  Rule auto = ADS nhưng user override PERSONAL      -> PERSONAL (Manual)
  [PASS] 7  User reset override                               -> ADS      (Auto:ADS Rule)
  [PASS] 8a Nhân viên có đơn ADS trong tháng                  -> ADS      (Auto:ADS Rule)
  [PASS] 8b Cùng nhân viên, đơn không ADS                     -> PERSONAL (Auto:Default)
  [PASS] 9  Chữ thường hoàn toàn                              -> ADS      (Auto:ADS Rule)
  [PASS] 10 Khoảng trắng thừa                                 -> ADS      (Auto:ADS Rule)
  [PASS] 11 Ghi chú None                                      -> PERSONAL (Auto:Default)
  [PASS] 12 Override sang ADS khi auto = PERSONAL             -> ADS      (Manual)
  [PASS] 13 Tín Phát, ghi chú mặc định ERP, không có ADS      -> ADS      (Auto:Employee Default (Tín Phát))
  [PASS] 14 Tín Phát, ghi chú có ADS                          -> ADS      (Auto:ADS Rule)
  [PASS] 15 Tín Phát, quản lý override về PERSONAL            -> PERSONAL (Manual)
  [PASS] 16 Ly, ghi chú mặc định ERP — không ăn theo Tín Phát -> PERSONAL (Auto:Default)
  [PASS] 17 Ly, ghi chú có ADS                                -> ADS      (Auto:ADS Rule)
------------------------------------------------------------------------------------------
  18/18 passed
```

- **Case 1–8** là 8 test case bắt buộc của mục 29 đặc tả. Case 8 tách làm 8a/8b
  để thể hiện đúng ý "một nhân viên có cả đơn ADS lẫn đơn Personal trong một
  tháng".
- **Case 9–12** là bốn case bổ sung cho các yêu cầu ở mục 13 mà mục 29 không
  liệt kê: chữ thường, khoảng trắng thừa, ghi chú rỗng, và override theo chiều
  ngược lại.
- **Case 13–17** kiểm chứng mặc định cấp nhân viên của DEC-109.
- Cột trong ngoặc là `SourceOfValue` theo mục 7 đặc tả — mỗi dòng phải nói được
  giá trị của nó từ đâu ra.

Case A–G do chủ dự án chỉ định (DEC-119) kiểm chứng cả nguồn đơn **lẫn** tỉ lệ
phân giải ra — xem §9.

Phần quét file thô không chạy lại được trong session này — `data/samples/`
không nằm trong git theo DEC-108. Con số 0/8.714 ở §1 là kết quả đã ghi nhận
ngày 2026-08-22 và không có gì trong DEC-119 làm nó thay đổi: việc đổi tên
`TINPHAT_ADS` → `ADS` không tạo ra một lần khớp từ khóa nào.

Mã nguồn: `tools/analysis/verify_ads_rule.py`. Đây là bản tham chiếu của rule;
`lead_source_engine` ở TASK-104 phải cho kết quả giống hệt trên cùng bộ case.

---

## 6. Hệ quả và việc phải làm

### 6.1. Với dữ liệu lịch sử 01–06.2026 — DEC-120

Toàn bộ 8.714 đơn ra `PERSONAL`, trừ 1.108 đơn của Tín Phát vào `ADS` qua mặc
định cấp nhân viên. **Đó là kết quả cuối cùng — không di trú, không override
hàng loạt** (DEC-120).

Hệ quả bằng số, cần nói thẳng: quy đổi ở 5,5 % cho ra số **lớn hơn** quy đổi ở
7,5 %, nên khi phần lợi nhuận ADS lịch sử của Hoàng và Kiên rơi về 5,5 %, doanh
thu quy đổi của hai người **cao hơn** báo cáo hiện tại:

| | 01–08.2026 (nghìn đồng) |
|---|---:|
| Workbook hiện tại đang báo cáo (có tách bucket tay) | 13.883.242 |
| Công cụ sẽ tính (lịch sử mặc định PERSONAL) | **14.720.745** |
| Chênh lệch | **+837.503 (+6,0 %)** |
| Tiền thưởng kéo theo | khoảng +2.967 (~3,0 triệu đồng) |

Chủ dự án đã chấp nhận chênh lệch này có ý thức: 2026 là giai đoạn chuyển đổi
(DEC-121), không phải một năm bị tính sai. Bảng 14 số ở tài liệu 04 §2 giữ lại
làm **mốc đối chiếu**, không phải đầu vào của engine.

Phương án di trú vẫn còn nguyên vẹn trong DEC-112 nếu GATE-01 kết luận chênh
lệch 6,0 % là không chấp nhận được.

### 6.2. Với dữ liệu mới

Rule chỉ bắt đầu có tác dụng khi nhân viên thực sự gõ "ADS". Công cụ phải làm
cho việc này **không thể bị bỏ quên trong im lặng**:

- Mỗi lần import, hiển thị rõ: `X / Y đơn được phân loại ADS`, tách riêng số
  đến từ rule từ khóa và số đến từ mặc định cấp nhân viên.
- Nếu một tháng có **0 đơn ADS**, đưa cảnh báo vào Review Queue thay vì coi là
  bình thường — vì với lịch sử đang có, 0 nhiều khả năng nghĩa là "chưa ai gõ"
  chứ không phải "tháng này không có đơn ADS".
- Danh sách từ khóa nằm ở `config/lead_source.yaml`. Thêm `QUẢNG CÁO`, `WEB`
  hay bất kỳ ký hiệu nào khác **không cần sửa code**.

### 6.3. Trạng thái các câu hỏi

| # | Câu hỏi | Trạng thái |
|---|---|---|
| **C1** | Tín Phát quy đổi 7,5 % cho mọi đơn — có đặt mặc định ADS riêng không? | **Đã chốt — DEC-109, sửa đổi bởi DEC-119.** `default_lead_source: ADS`. Xem §7. |
| **C6** | ERP có cho sửa `Diễn giải` không? | **Đã chốt — DEC-111.** Sửa được; mặc định giữ nguyên, chỉ sửa khi là đơn ADS. |
| **C7** | Xử lý đơn ADS lịch sử thế nào? | **Đã chốt lại — DEC-120 thay thế DEC-112.** Không di trú; lịch sử mặc định `PERSONAL`. Xem §6.1 và §8. |

---

## 7. Thứ tự ưu tiên sau DEC-109

```
LeadSourceFinal =
    1. Manual Override                    → SourceOfValue = "Manual"
    2. Rule ADS trên Diễn giải            → "Auto:ADS Rule"
    3. Default của nhân viên (nếu có)     → "Auto:Employee Default (<tên>)"
    4. Default toàn hệ thống (PERSONAL)   → "Auto:Default"
```

Chuỗi này chỉ quyết định **nguồn đơn**. Nó không quyết định tỉ lệ — xem §9.

Default cấp nhân viên nằm **dưới** rule ADS và **trên** default toàn hệ thống.
Vì vậy nó chỉ có thể nâng một đơn lên ADS, **không bao giờ hạ** một đơn mà rule
đã bắt được. Override tay vẫn thắng cả hai.

Không có gì trong code biết tới cái tên "Tín Phát" — đó là một dòng trong
`config/employees.yaml`. Bất kỳ nhân viên hay kênh nào cũng đặt được mặc định
riêng.

Kiểm chứng (case 13–17 trong `verify_ads_rule.py`, **18/18 PASS**) — xem output
đầy đủ ở §5.

Case 15 đáng chú ý: chủ dự án nói *"100% đơn đứng tên Tín Phát được coi là
`LeadSource = ADS`"*, nhưng điều đó nói về **rule tự động**. Override tay vẫn
thắng, đúng theo xác nhận số 9 — nếu quản lý cần hạ một đơn Tín Phát về
PERSONAL vì một lý do có thật, hệ thống phải cho phép, có ghi lý do và audit.

**Hệ quả tốt:** số liệu lịch sử của Tín Phát **không cần di trú gì cả** — vốn
đã là 7,5 %. Phạm vi của C7 thu hẹp lại chỉ còn Hoàng và Kiên, và DEC-120 đã
đóng luôn phần đó bằng cách bỏ di trú.

---

## 8. C7 — dữ liệu ADS lịch sử của Hoàng và Kiên

> **Trạng thái: ĐÃ ĐÓNG bằng DEC-120 (2026-08-23) — không di trú.** Toàn bộ mục
> này giữ lại vì bảng số bên dưới vẫn là **mốc đối chiếu** hợp lệ và là chỗ duy
> nhất định lượng được chênh lệch mà quyết định không-di-trú tạo ra. Cột "CR
> không tách" chính là con số công cụ sẽ tính ra.

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

### Quyết định — DEC-120 (thay thế DEC-112)

**Không di trú.** Lịch sử không có dấu hiệu ADS phân loại thành `PERSONAL`.
Công cụ sẽ tính ra cột **"CR không tách" = 14.720.745**, không phải cột "CR có
tách". Chênh lệch +6,0 % là hệ quả đã được chấp nhận có ý thức, vì 2026 là giai
đoạn chuyển đổi (DEC-121).

Phương án truy từng đơn đã bị loại từ đầu vì **không khả thi**: không có dấu vết
nào trong bất kỳ file nào cho biết đơn nào là ADS. Con số `3770+16190` của Hoàng
tháng 05 cho thấy chúng được cộng tay từ một nguồn nằm ngoài hệ thống. Phương án
nhập 14 số di trú (DEC-112) sau đó cũng bị loại, theo hướng ưu tiên đơn giản hóa
và chuẩn hóa dữ liệu mới.

### Yêu cầu kỹ thuật — đã gỡ khỏi phạm vi TASK-108

Bốn yêu cầu mà DEC-112 kéo theo **không còn cần triển khai**: đường vào riêng
cho số di trú, cách hiển thị phân biệt, logic loại trừ giữa hai đường, và cấu
hình cut-over theo tháng. Chúng vẫn được ghi lại nguyên văn trong DEC-112 phòng
khi GATE-01 quyết định kích hoạt lại.

### REQUIRED check thay thế cho TASK-108

Mốc **13.883.242** không còn là tiêu chí gate — nó mô tả một hành vi mà công cụ
không còn thực hiện. Thay bằng một check **tái lập được từ dữ liệu**, không cần
di trú:

> Nạp lợi nhuận KPI theo nhân viên-tháng **và** 14 giá trị `X` của chính
> workbook vào `conversion_engine`. Kết quả phải tái hiện đúng cột `F` của
> `Summary 2026` ở cả 14 kỳ (E1).

Check này chứng minh engine cài đúng phép toán mà con người đang làm tay, mà
không buộc production phải mang theo dữ liệu di trú. Danh sách REQUIRED check
đầy đủ của TASK-108: xem `PROJECT/PROJECT_PROGRESS.md`.

---

## 9. ConversionScheme — bước phân giải thứ hai (DEC-119)

`LeadSource` trả lời *"đơn này đến từ đâu"*. Nó **không** trả lời *"tỉ lệ nào
quy đổi nó"*. Hai câu hỏi có hai bảng riêng.

Bằng chứng cho thấy vì sao phải tách: **Nội thành bán đơn `PERSONAL` nhưng quy
đổi ở 2 %**, Gia dụng ở 8 %. Nếu `PERSONAL` kéo theo 5,5 %, hai nhóm này không
diễn đạt được trong mô hình.

### Bảng phân giải — `config/conversion_rates.yaml`

Tra theo khóa `(employee, lead_source, ngày của đơn)`; dòng cụ thể nhất thắng.

| employee | lead_source | scheme | rate | effective_from |
|---|---|---|---|---|
| `*` | `PERSONAL` | `PERSONAL_5_5` | 5,5 % | 2026-01-01 |
| `*` | `ADS` | `ADS_7_5` | 7,5 % | 2026-01-01 |
| `Nội thành` | `PERSONAL` | `NOI_THANH_2` | 2 % | 2026-01-01 |
| `Gia dụng` | `PERSONAL` | `GIA_DUNG_8` | 8 % | 2026-01-01 |

Tín Phát, Hoàng, Kiên, Ly **không cần dòng riêng** — họ rơi vào hai dòng `*`.
Đó là điểm mấu chốt: 7,5 % của Tín Phát suy ra từ *nguồn đơn*, không phải từ
*tên nhân viên*.

**Không có tỉ lệ mặc định cuối cùng.** Tổ hợp không khớp dòng nào trả về
`Unresolved` và vào Review Queue.

### Kiểm thử case A–G — E1

Chạy `python tools/analysis/verify_ads_rule.py`, kết quả thực tế 2026-08-23:

```
LeadSource + ConversionScheme — DEC-119 cases A–G
------------------------------------------------------------------------------------------
  [PASS] A  Tín Phát, không có chữ ADS                -> ADS / ADS_7_5 / 7.500%             (Auto:LeadSource (ADS_7_5))
  [PASS] B  Kiên, không có ADS                        -> PERSONAL / PERSONAL_5_5 / 5.500%   (Auto:LeadSource (PERSONAL_5_5))
  [PASS] C  Kiên, một dòng trong OrderID có ADS       -> ADS / ADS_7_5 / 7.500%             (Auto:LeadSource (ADS_7_5))
  [PASS] D  Hoàng, order nhiều SP, chỉ 1 dòng có ADS  -> ADS / ADS_7_5 / 7.500%             (Auto:LeadSource (ADS_7_5))
  [PASS] E  Vinh → Nội thành, không ADS               -> PERSONAL / NOI_THANH_2 / 2.000%    (Auto:Employee (NOI_THANH_2))
  [PASS] F  Quý/Hiệp → Nội thành, không ADS           -> PERSONAL / NOI_THANH_2 / 2.000%    (Auto:Employee (NOI_THANH_2))
  [PASS] G1 Kiên trong tháng — phần PERSONAL          -> PERSONAL / PERSONAL_5_5 / 5.500%   (Auto:LeadSource (PERSONAL_5_5))
  [PASS] G2 Kiên trong tháng — phần ADS               -> ADS / ADS_7_5 / 7.500%             (Auto:LeadSource (ADS_7_5))
------------------------------------------------------------------------------------------
  8/8 passed
```

Case E và F là bằng chứng trực tiếp cho việc tách: cùng `LeadSource = PERSONAL`
như case B, nhưng ra 2 % thay vì 5,5 %.

### Case G end-to-end — hai bucket

```
Case G — hai bucket quy đổi độc lập (Kiên, một tháng)
------------------------------------------------------------------------------------------
  PersonalProfit       30,000 / 5.5% =        545,455
  AdsProfit             7,565 / 7.5% =        100,867
  Total                                     =        646,321

  [PASS] Total == Personal + Ads
  [PASS] Khác với quy đổi gộp một tỉ lệ (683,000, lệch 36,679)
------------------------------------------------------------------------------------------
  2/2 passed
```

Check thứ hai là cái quan trọng: quy đổi gộp một tỉ lệ duy nhất cho ra
**683.000** thay vì **646.321**. Chênh **36.679** — đúng bằng con số delta của
Kiên tháng 06, 07, 08.2026 trong bảng §8, xác nhận bản cài đặt tham chiếu tái
hiện đúng số học đang có trong workbook.

### Tra theo thời điểm — DEC-121

```
Tra tỉ lệ theo thời điểm — DEC-121
------------------------------------------------------------------------------------------
  [PASS] 15/03/2026 -> ADS_7_5 7.5%
  [PASS] 01/06/2027 -> ADS_7_5 7.5% (chưa có chính sách mới nào hiệu lực)
  [PASS] 31/12/2025 -> Unresolved (trước effective_from, không đoán tỉ lệ)
------------------------------------------------------------------------------------------
  3/3 passed
```

Tra bằng **ngày của đơn**, không bao giờ bằng "hôm nay". Đây là điều kiện để một
chính sách đổi vào 2027 không làm thay đổi báo cáo 2026 đã phát hành.

### Câu hỏi còn mở

Bảng trên **chưa định nghĩa** tỉ lệ cho `(Nội thành, ADS)` và `(Gia dụng, ADS)`.
Với chuỗi phân giải hiện tại, một đơn Nội thành có chữ "ADS" sẽ rơi vào dòng
`* + ADS` và quy đổi ở **7,5 %** thay vì 2 %. Xem `10_OPEN_QUESTIONS.md` — C9.

Đây là một dòng cấu hình, không phải một thay đổi code, dù chủ dự án chọn hướng
nào.
