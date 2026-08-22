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
| Số Số BH được rule phân loại `TINPHAT_ADS` | **0** / 8.714 |
| Số Số BH được rule phân loại `PERSONAL` | **8.714** / 8.714 |

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

**Điểm cần chủ dự án xác nhận:** cột `Diễn giải` vừa chứa chuỗi ERP tự sinh vừa
chứa ghi chú gõ tay. Cần chắc rằng nhân viên **sửa được** ô này trong ERP để
thêm chữ "ADS", chứ không chỉ đọc được. Nếu ERP ghi đè trường này khi lưu
chứng từ, cần đổi sang phương án đánh dấu khác (mục mở, xem §6).

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

### 6.3. Vấn đề còn mở

| # | Câu hỏi | Cần trước |
|---|---|---|
| **C1** | Tín Phát hiện quy đổi 7,5 % cho **mọi** đơn — bằng đúng tỉ lệ ADS. Theo rule mới, đơn Tín Phát không ghi "ADS" sẽ rơi xuống 5,5 % và **số liệu thay đổi**. Có nên đặt `default_lead_source: TINPHAT_ADS` riêng cho Tín Phát không? | GATE-01 |
| **C6** | ERP có cho phép nhân viên sửa cột `Diễn giải` không, hay nó bị ghi đè bằng `"Bán hàng " + Tên KH` khi lưu chứng từ? | Trước khi phổ biến quy ước |
| **C7** | Có xử lý ngược lại cho dữ liệu lịch sử không (truy từng đơn, hay nhập số tổng theo tháng)? | GATE-01 |
