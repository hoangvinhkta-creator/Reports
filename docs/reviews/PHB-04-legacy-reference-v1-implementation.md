# PHB-04 — LEGACY REFERENCE V1 — BÁO CÁO TRIỂN KHAI (BẢN CUỐI)

Ngày: 2026-09-05 · Phiên: S119 (pass triển khai cuối) · Nhánh:
`claude/phb-04-legacy-reference-v1-widtzf`

> **Bản này thay thế mọi báo cáo PHB-04 trước đó.** Hai bản trước có kết luận
> sai về dữ liệu 2025; mục 2 nói rõ sai ở đâu và vì sao. Lần này công cụ đã
> đọc **chính hai file thật** mà chủ dự án cấp, không đoán từ hồ sơ cũ.

---

## 1. Nguồn chuẩn lịch sử 2025 là file nào?

**`Báo cáo Kinh doanh 2025.xlsx`** — workbook riêng của năm 2025.

Đây là quyết định của chủ dự án, nay đã đóng băng thành `DEC-178`. Bản sao
`Summary 2025` nằm bên trong workbook 2026 chỉ là **bằng chứng thứ cấp**.
Khi hai bên lệch nhau, **workbook 2025 riêng luôn thắng** — và hệ thống
không có đường nào để bản thứ cấp âm thầm thay thế nó.

---

## 2. Vì sao file đó là nguồn chuẩn?

Ngoài việc chủ dự án đã quyết, chính hai file cũng cho thấy vì sao quyết định
đó đúng:

| | Workbook 2025 riêng (chuẩn) | Bản sao trong workbook 2026 (thứ cấp) |
|---|---|---|
| Sheet `Summary` | **1005 ô công thức**, mỗi dòng liên kết tới sheet chi tiết của đúng người bán đó | **0 ô công thức** — chỉ còn giá trị dán cứng |
| Sheet chi tiết | **74 sheet**, đủ 12 tháng | không có |
| Truy ngược được không | **Có** — bấm ngược về được tận sổ gốc | Không |
| Số tháng 12/2025 | đã chốt sổ | còn số cũ chưa chốt |

Nói ngắn gọn: bản riêng là **bản gốc còn nguyên dây liên kết**; bản trong
workbook 2026 là **một tấm ảnh chụp lại**, chụp trước khi tháng 12 chốt sổ.

**Và đây là chỗ hai báo cáo trước đã sai.** Cả dây chuyền đọc dữ liệu của
công cụ đều bám vào công thức Excel. Bản sao trong workbook 2026 không còn
công thức nào, nên công cụ không đọc được nó — rồi báo cáo lại kết luận
thành *"năm 2025 chỉ có 12 con số doanh thu"*. Đó là kết luận về **công cụ
đọc**, bị trình bày nhầm thành kết luận về **dữ liệu**. File 2025 riêng cho
thấy dữ liệu luôn ở đó, đầy đủ.

---

## 3. File 2025 thật sự chứa những gì?

Đọc trực tiếp từ file:

```text
Tổng số sheet             = 76
  sheet chi tiết          = 74   (mỗi tháng × mỗi người bán một sheet)
  Summary                 =  1   bảng tổng hợp, 1005 công thức
  BestStaff               =  1   bảng thi đua nhân viên theo quý
```

Công cụ nhập vào được **93 dòng** của sheet `Summary`:

```text
74 dòng người bán   ← khớp CHÍNH XÁC 74 sheet chi tiết
12 dòng tổng tháng  ← đủ cả 12 tháng
 7 dòng tiến độ     ← "đã qua bao nhiêu ngày trong tháng", không phải số bán
 0 dòng không đọc được
```

Con số 74 khớp 74 là một phép kiểm chéo mạnh: mọi sheet chi tiết đều có đúng
một dòng tương ứng trong bảng tổng hợp, không thừa không thiếu.

**Sáu dòng bị loại trừ có chủ đích.** Dưới 12 khối tháng còn một khối tổng
kết KPI cuối năm. Ở khối đó **các cột mang ý nghĩa khác hẳn**: cột vốn là
"Tổng đơn" lại chứa "Tổng KPI cả năm". Nếu nhập bừa, hệ thống sẽ ghi
*"Tổng đơn của Ly = 10,79"* — một con số vô nghĩa. Hàng rào an toàn của hệ
thống đã chặn đúng khối này ngay lần chạy đầu tiên trên file thật, và công cụ
ghi lại rõ "đã loại 6 dòng" thay vì im lặng.

---

## 4. 12 tháng và nhân viên nào được tìm thấy?

| Tháng | Sheet chi tiết | Dòng người bán | Dòng tổng | Không đọc được | Người bán / kênh |
|---|---|---|---|---|---|
| 01 | 7 | 7 | 1 | 0 | Ly, Thắng, Tín Phát, Miền Bắc, Hoàng, Khác, Nội thành |
| 02 | 6 | 6 | 1 | 0 | Ly, Thắng, Tín Phát, Khác, Hoàng, Nội thành |
| 03 | 5 | 5 | 1 | 0 | Ly, Thắng, Tín Phát, Hoàng, Nội thành |
| 04 | 5 | 5 | 1 | 0 | Ly, Thắng, Tín Phát, Hoàng, Nội thành |
| 05 | 6 | 6 | 1 | 0 | Ly, Thắng, Tín Phát, Hoàng, Gia dụng, Nội thành |
| 06 | 6 | 6 | 1 | 0 | Ly, Thắng, Tín Phát, Hoàng, Gia dụng, Nội thành |
| 07 | 6 | 6 | 1 | 0 | Ly, Thắng, Tín Phát, Hoàng, Gia dụng, Nội thành |
| 08 | 7 | 7 | 1 | 0 | Ly, Thắng, Tín Phát, Hoàng, Quân, Gia dụng, Nội thành |
| 09 | 7 | 7 | 1 | 0 | Ly, Thắng, Tín Phát, Hoàng, Kiên, Gia dụng, Nội thành |
| 10 | 7 | 7 | 1 | 0 | Ly, Thắng, Tín Phát, Hoàng, Kiên, Gia dụng, Nội thành |
| 11 | 6 | 6 | 1 | 0 | Ly, Thắng, Tín Phát, Hoàng, Kiên, Nội thành |
| 12 | 6 | 6 | 1 | 0 | Ly, Thắng, Tín Phát, Hoàng, Kiên, Nội thành |
| **Tổng** | **74** | **74** | **12** | **0** | |

Mười tên xuất hiện trong năm 2025: **Ly · Thắng · Tín Phát · Hoàng · Kiên ·
Quân · Miền Bắc · Khác · Gia dụng · Nội thành**. Có thể thấy rõ lịch sử nhân
sự: Miền Bắc và Khác chỉ có đầu năm, Gia dụng xuất hiện từ tháng 5, Quân chỉ
tháng 8, Kiên từ tháng 9.

---

## 5. Summary 2025 chứa những chỉ tiêu nào?

Đo trên chính 86 dòng (74 người bán + 12 dòng tổng) của file thật:

| Chỉ tiêu | Ô có số | Ô trống | Kết luận |
|---|---|---|---|
| Tổng đơn | 74 | 12 | Có, bằng chứng đầy đủ |
| Tổng số SP | 74 | 12 | Có, bằng chứng đầy đủ |
| Tổng bán | 86 | 0 | Có, bằng chứng đầy đủ |
| Doanh thu quy đổi | 83 | 3 | Có, bằng chứng đầy đủ |
| Tổng lợi nhuận | 86 | 0 | Có, bằng chứng đầy đủ |
| Tỉ suất lợi nhuận | 86 | 0 | Có, bằng chứng đầy đủ |
| Lợi nhuận thực nhận | 86 | 0 | Có, bằng chứng đầy đủ |
| Vs. tháng trước | 79 | 7 | Có, bằng chứng đầy đủ |
| Target | 70 | 16 | Có, bằng chứng đầy đủ |
| Vs. target | 70 | 16 | Có, bằng chứng đầy đủ |
| Tỉ lệ tồn kho | 29 | 57 | Có số, ý nghĩa chưa chốt |
| Thưởng | 63 | 23 | Có số, ý nghĩa chưa chốt |
| Ngày công | 60 | 26 | Có số, ý nghĩa chưa chốt |
| Lương cứng | 55 | 31 | Có số, ý nghĩa chưa chốt |
| Phụ cấp | 56 | 30 | Có số, ý nghĩa chưa chốt |
| Tổng lương | 54 | 32 | Có số, ý nghĩa chưa chốt |

Hai điều đáng chú ý:

- Bảng này **không phải danh sách viết sẵn** — công cụ đếm trên dữ liệu thật.
  File giàu hơn thì bảng tự đầy hơn, không cần ai sửa mã.
- Các cột lương/thưởng **có số trong file** nhưng vẫn xếp "ý nghĩa chưa
  chốt": dự án chưa chốt luật nhân sự, nên công cụ không tự diễn giải chúng.
  Không giấu số của chủ dự án, cũng không tự phong cho nó một ý nghĩa.

Ô trống luôn hiện **dấu gạch `—`**, không bao giờ thành số 0.

---

## 6. Chi tiết nhân viên/tháng được hỗ trợ đến đâu?

**Hỗ trợ đầy đủ.** Đây là Level 2 và nó đã chạy trên dữ liệu thật.

Với mỗi tháng của 2025, chủ dự án xem được bảng **người bán × chỉ tiêu**, trả
lời được đúng những câu đã nêu: ai có số trong kỳ, tổng đơn, tổng số SP, tổng
bán, doanh thu quy đổi, tổng lợi nhuận, tỉ suất, so tháng trước, target, so
target.

Điểm đáng nói về chi phí: **không phải viết mới phần hiển thị.** Kho lưu số
cũ vốn đã lưu theo *(năm, tháng, người bán, loại dòng)* và trang "Nhân viên"
vốn không giả định năm nào — nên vừa có dòng 2025 là chúng phục vụ được ngay.

Dòng tổng tháng luôn là **một loại dòng riêng**, không bao giờ bị coi là một
nhân viên tên "Tổng".

---

## 7. Chi tiết từng dòng bán hàng có nằm trong V1 không? Vì sao?

**Không — hoãn có chủ đích** (`LEGACY_LINE_DETAIL_2025 = DEFERRED`).

Lý do chính không phải kỹ thuật mà là **bảo vệ dữ liệu cá nhân**:

```text
74 sheet chi tiết · 62.802 dòng · 6 kiểu bố cục khác nhau
Mọi kiểu đều có cột:  Tên khách hàng · Số điện thoại · Địa chỉ
```

Đưa hơn 62 nghìn dòng chứa tên, số điện thoại và địa chỉ khách hàng vào kho
dữ liệu của hệ thống là **một quyết định về bảo vệ dữ liệu cá nhân**, cần
được quyết riêng — không phải một chi tiết kỹ thuật lặng lẽ nằm trong phần
báo cáo lịch sử. Thêm nữa, 6 kiểu bố cục khác nhau nghĩa là phải viết một bộ
đọc Excel tổng quát, đúng thứ mà phạm vi PHB-04 cấm.

**Không có gì bị bỏ quên:** tên cả 74 sheet vẫn được ghi lại và hiện trên
giao diện là "đang hoãn có chủ đích", kèm số lượng.

`BestStaff` (bảng thi đua nhân viên theo quý) cũng nằm ngoài phạm vi — đó là
một tính năng xếp hạng nhân sự, không phải báo cáo lịch sử.

---

## 8. Hai workbook 2025 khác nhau ở đâu?

So từng ô giữa hai nguồn:

```text
Tổng số ô so sánh          = 1132
Giống hệt                  =  573
Chỉ khác do làm tròn       =  505
Khác thật sự               =   42   (nằm trên 12 dòng)
Có ở bản chuẩn, thiếu ở bản sao = 12
Có ở bản sao, thiếu ở bản chuẩn =  0
```

"Chỉ khác do làm tròn" được xác định bằng **cơ chế**, không bằng một ngưỡng
tự chọn: bản sao lưu số đã làm tròn để hiển thị. Nhờ vậy một đơn hàng lệch
(105 so với 104) không bao giờ bị xếp nhầm vào nhóm này.

**Khác biệt thật tập trung ở tháng 12/2025** — đúng như dự đoán "ảnh chụp
trước khi chốt sổ":

| Chỉ tiêu | Bản chuẩn (2025) | Bản sao (trong 2026) |
|---|---|---|
| Ly — Tổng đơn | 105 | 104 |
| Ly — Tổng số SP | 231,72 | 229 |
| Ly — Tổng bán | 1.604.205 | 1.595.355 |
| Ly — Tổng lợi nhuận | 87.537 | 86.415 |
| Nội thành — Tổng số SP | 1.655 | 1.682 |
| Nội thành — Tổng bán | 12.776.886 | 12.866.046 |
| Nội thành — Tổng lợi nhuận | 270.432 | 273.602 |
| **Tổng tháng 12 — Tổng bán** | **23.016.871** | **23.097.181** |

Mọi con số chủ dự án nêu trong chỉ thị đều đã được xác nhận đúng trên file
thật. Ngoài ra bản sao để trống các ô lương tháng 12 (bản chuẩn có).

---

## 9. Khi hai nguồn lệch nhau, hệ thống chọn số nào?

**Luôn chọn bản chuẩn** — và điều này không dựa vào việc ai nhớ quy tắc, mà
được cài thẳng vào chỗ hệ thống đọc dữ liệu.

Cụ thể, khi đọc số của một năm, hệ thống hỏi theo thứ tự: *"năm này có nguồn
chuẩn riêng không?"* → có thì đọc từ đó; không thì mới dùng bản đang xem.

Đã kiểm bằng test với một ô cố tình cho lệch nhau:

- nạp bản sao trước, bản chuẩn sau → ra số của **bản chuẩn**;
- nạp bản chuẩn trước, bản sao sau → vẫn ra số của **bản chuẩn**;
- nạp bản sao **ba lần liên tiếp** → vẫn không đổi được số.

Không lấy trung bình, không "ai ghi sau thì thắng", không trộn. Bản sao
**không bị xoá** — vẫn tra được khi cần đối chiếu.

Một chi tiết quan trọng: nạp workbook 2025 **không làm biến mất dữ liệu
2026**. Workbook một năm chỉ nắm thẩm quyền của riêng năm nó.

---

## 10. Số legacy được lưu và nhận diện thế nào?

Dùng lại kho lưu sẵn có (bốn bảng `legacy_*`), **không dựng kho mới**. Mọi
dòng mang dấu `LEGACY_REFERENCE` do cơ sở dữ liệu tự ép ở tầng cấu trúc.

Có **một thay đổi cấu trúc duy nhất** trong toàn bộ PHB-04: thêm **một cột**
ghi "bản nhập này là nguồn chuẩn hay bản sao". Đây là thay đổi nhẹ nhất có
thể — một cột, cho phép để trống, không đụng một dòng dữ liệu nào đang có.

Vì sao vẫn phải thêm: quy tắc "nguồn nào thắng" là một quyết định của chủ dự
án. Nó không được phép phụ thuộc vào việc ai đó gõ đúng tên file hay đặt đúng
tên sheet. Cột này ghi thẳng điều đó ra, do công cụ tự xác định khi đọc file.

---

## 11. Vì sao legacy không làm sai dữ liệu hiện tại?

Đã **đo**, không chỉ suy luận. Sau khi nạp toàn bộ 2025:

- doanh thu kỳ hiện hành: **không đổi**;
- coverage giá nhập: **không đổi**;
- giá nhập chủ dự án tự nhập ở PHB-03: **còn nguyên**;
- lợi nhuận KPI: **không đổi**;
- các trang 2026: **không đổi**.

Ngoài ra có một test kiểm bằng **cấu trúc mã**: phần đọc dữ liệu lịch sử
không hề tham chiếu tới Product Identity, Tracking, giá nhập hay KPI. Không
phải "không gọi tới" mà là **không có đường nào để gọi**.

Mở giao diện lịch sử cũng không ghi gì: mở hai lần, số dòng của **mọi bảng**
không đổi một đơn vị.

Hàng rào chống bỏ sót dữ liệu 2026 **không bị nới lỏng** — và nay còn áp
dụng cho cả nguồn chuẩn 2025, vì đó cũng là nguồn chính thức.

---

## 12. Chủ dự án xem 2025 trên giao diện thế nào?

Tab **"Lịch sử"**:

```text
Lịch sử → Năm 2025 → bấm một tháng → bảng người bán × chỉ tiêu của tháng đó
```

Trang ghi rõ cho từng năm: **đang đọc từ file nào**, file đó là *nguồn chuẩn*
hay *bản sao*, và còn bao nhiêu sheet chi tiết đang hoãn.

Mọi con số vẫn đeo nhãn `LEGACY` kèm đơn vị, và có dòng chữ nói rõ đây là
**số liệu tham chiếu lịch sử** — không phải số do công cụ hiện tại tính.

Một kỳ có thể có **số cũ**, **số mới**, hoặc **cả hai**. Khi có cả hai, trang
hiện **hai con số riêng biệt, mỗi con một nhãn** — không tự gộp thành một.

---

## 13. Những gì cố tình không làm?

- Không dựng lại giao dịch kế toán 2025.
- Không nhập 62.802 dòng chi tiết chứa dữ liệu cá nhân khách hàng.
- Không viết bộ đọc Excel tổng quát cho 6 kiểu bố cục.
- Không tái tạo 74 sheet thành 74 trang web.
- Không biến số lịch sử thành số của engine hiện tại.
- Không chạy lại 2025 qua công thức hiện hành.
- Không làm BestStaff, PHB-05 Target, Brand, Advanced Analytics, dọn R1/R2/R3.
- Không đổi Product Identity, Tracking, hay logic giá nhập.
- Không nới lỏng quy tắc so sánh (mục 14).

**Về so sánh:** "nguồn chuẩn lịch sử" **không** có nghĩa "cùng nghĩa với số
mới". Lợi nhuận lịch sử của 2025 nay là số chính thức của lịch sử, nhưng vẫn
**không đem trừ** với lợi nhuận KPI hiện tại — hai bên tính khác nhau. Xem
được đầy đủ, chỉ là không sinh ra phần trăm tăng trưởng giả.

---

## 14. Test đã chạy

```text
Test riêng của PHB-04    tests/test_phb04_legacy_reference.py   79 passed
Toàn bộ hệ thống         python -m pytest -q                    2216 passed, 11 skipped
Test golden              4 file golden                          74 passed, 2 skipped (KHÔNG ĐỔI)
Round-trip nâng cấp DB   tests/test_history_db.py               17 passed
```

Diễn biến qua ba mốc của phiên: `2136` (trước phiên) → `2171` → `2187` →
**`2216`**. Golden giữ nguyên `74 passed, 2 skipped` ở **cả bốn mốc** — nghĩa
là không có chỉ tiêu nghiệp vụ nào bị xê dịch.

Hai mươi câu hỏi bắt buộc đều có test riêng, gồm: nguồn chuẩn thắng · bản sao
không ghi đè được · ô lệch nhau ra số bản chuẩn · đủ 12 tháng · sheet chi
tiết được ghi nhưng không nhập · dòng người bán nhận diện đúng · dòng tổng
tách riêng · dòng tổng không bao giờ thành nhân viên · giá trị giữ nguyên
gốc · ô trống hiện `—` · điều hướng nhân viên/tháng · nhãn
`LEGACY_REFERENCE` · nạp lại không nhân đôi · nạp bản sao nhiều lần không đổi
số · doanh thu, coverage, giá nhập tay không đổi · không chạm Product
Identity/Tracking · chặn so sánh hai engine · 2026 không đổi.

**Không test cũ nào bị tắt hay bị nới.** Ba test của bản kiểm kê nâng cấp cơ
sở dữ liệu được cập nhật để thêm bước nâng cấp mới — vẫn là một danh sách
đóng.

---

## 15. Finding còn lại

Không có finding nào chặn.

**F-PHB04-03 (không chặn).** Dòng "tiến độ" trong sheet Summary (`C = số ngày
đã qua ÷ số ngày trong tháng`) lưu tỉ lệ đó vào ô vốn dành cho "Tổng đơn".
Đây là hành vi có từ trước, không phải do phiên này. Nó **không ảnh hưởng
Owner**: các dòng đó không thuộc tháng nào nên tự nằm ngoài mọi khung nhìn
theo kỳ, và phiên này đã loại chúng khỏi phép đếm chỉ tiêu. Sửa tận gốc thuộc
phạm vi khác.

**F-PHB04-04 (không chặn).** Ba ô của "Gia dụng" lệch nhau giữa hai nguồn do
**cách làm tròn khác nhau** ở chữ số thứ năm (ví dụ 0,48425 → 0,4842 so với
0,4843). Không phải khác biệt nghiệp vụ. Quy tắc nguồn chuẩn đã xử lý xong.

**F-PHB04-01 / F-PHB04-02** của bản trước vẫn giữ nguyên, vẫn không chặn.

---

## 16. Owner decision còn thiếu

**Không có quyết định nào đang chặn.** `DEC-178` đã đóng câu hỏi nguồn.

Ba việc ghi lại cho tương lai, **không chặn gì**:

- **Dữ liệu chi tiết từng dòng 2025** — cần một quyết định về việc có lưu
  tên/số điện thoại/địa chỉ khách hàng trong hệ thống hay không, và nếu có
  thì lưu những cột nào. Chỉ khi đó mới nên bàn tiếp Level 3.
- **`OD-PHB04-A`** — kỳ có **cả** số cũ **và** số mới: có bao giờ cần gộp
  thành một con số duy nhất không?
- **`OD-PHB04-B`** — có tháng 2026 nào muốn coi là "legacy thuần" không?

---

## 17. Trạng thái PHB-04

```text
PHB_04 = IMPLEMENTED_AWAITING_REVIEW
```

Toàn bộ phần bắt buộc đã xong và đã chạy trên **dữ liệu thật**: nguồn chuẩn
đã xử lý, đủ 12 tháng, tổng hợp tháng và chi tiết nhân viên/tháng đều chạy,
0 dòng không đọc được, quy tắc nguồn đã kiểm, dữ liệu hiện hành không đổi,
nạp lại không nhân đôi.

Còn thiếu **một lượt review độc lập**, do một phiên khác thực hiện. Chưa có
lượt đó thì **chưa được gọi là `DONE`**.

---

## 18. Bước tiếp theo

1. **Mở phiên review độc lập PHB-04** trên đúng commit này. Nên soi trước:
   quy tắc nguồn chuẩn ở tầng truy vấn, việc loại trừ khối tổng kết KPI, và
   quyết định hoãn phần chi tiết từng dòng.
2. Nếu chủ dự án muốn phần chi tiết từng dòng: cần quyết định về dữ liệu cá
   nhân trước (mục 16).
3. Sau khi PHB-04 `DONE`: **PHB-05 — Target**.
