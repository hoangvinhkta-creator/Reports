# PHB-04 — LEGACY REFERENCE V1 — BÁO CÁO CHO CHỦ DỰ ÁN

Ngày: 2026-09-04 · Phiên: S119 · Nhánh: `claude/phb-04-legacy-reference-v1-widtzf`

Báo cáo này viết cho người đọc không phải kỹ thuật. Mỗi mục trả lời đúng một
câu hỏi.

---

## 1. Legacy Reference là gì?

Là **số của những kỳ báo cáo cũ, làm bằng tay trên Excel, trước khi công cụ
này trở thành nơi tính số chính thức.**

Điều quan trọng nhất: số cũ và số mới là **hai loại bằng chứng khác nhau**.

- Số mới do công cụ tính từ sổ bán hàng gốc, theo những quy tắc đã chốt.
- Số cũ do người lập báo cáo gõ và sửa tay trong Excel.

Cả hai đều là số thật của công ty. Nhưng chúng **không được tính theo cùng một
cách**, nên đặt cạnh nhau thì xem được, còn trừ nhau ra để lấy phần trăm tăng
trưởng thì sai.

Nguyên tắc của PHB-04 gói gọn trong một câu:

> Cho phép xem lại số cũ, mà không làm số cũ trông như thể do công cụ mới tính.

---

## 2. Dữ liệu nào được coi là legacy?

Hai nhóm kỳ:

**Nhóm 1 — Các tháng của năm 2025.**
Nguồn duy nhất được chấp nhận là cột "Doanh số cùng kỳ 2025" nằm trong sheet
`DataChart 2026` của workbook cũ. Đó là những con số gõ cứng, mỗi tháng một ô.
Kỳ nào ô đó trống thì kỳ đó **không có dữ liệu** — và công cụ nói thẳng là
trống, không tự điền 0.

**Nhóm 2 — Các tháng của năm workbook (2026) có trong báo cáo tay.**
Đây là những dòng của sheet `Summary 2026`, đã hiển thị từ trước ở trang
"Nhân viên" và "Doanh số ngày". PHB-04 không đổi cách hiện chúng; nó chỉ nói
rõ từng chỉ tiêu thuộc loại bằng chứng nào.

**Sheet `Summary 2025` KHÔNG được dùng.** Chính chủ dự án đã quyết định điều
này trước đây (`DEC-169`): sheet đó chỉ là tài liệu tham chiếu, không nhập,
không lưu, không truy vấn, không hiển thị. Phiên này **không** mở lại quyết
định đó. Lý do kỹ thuật đi kèm cũng rất rõ: sheet đó không có một ô công thức
nào trên toàn bộ 755 dòng, nên công cụ không có cách nào biết dòng nào là
người bán, dòng nào là dòng tổng.

---

## 3. Dữ liệu legacy được lưu ở đâu?

**Ở đúng chỗ nó đã nằm từ trước — không có kho mới nào được dựng.**

Khi làm `TASK-PRA-001`, hệ thống đã có sẵn bốn bảng riêng dành cho số cũ, tách
hoàn toàn khỏi các bảng của dữ liệu kế toán hiện hành. Mỗi dòng trong bốn bảng
đó mang một dấu cố định `LEGACY_REFERENCE`, và dấu này được **cơ sở dữ liệu ép
buộc** chứ không phải do quy ước đặt tên — không có cách nào ghi một dòng mang
dấu khác vào đó.

PHB-04 **không** thêm bảng, **không** thêm cột, **không** chạy bước nâng cấp
cơ sở dữ liệu nào. Nó chỉ đọc dữ liệu đã có và trình bày lại.

Đây là điều đáng yên tâm nhất trong toàn bộ phiên: phần rủi ro nhất — thay đổi
cấu trúc dữ liệu production — đã **không xảy ra**, vì audit cho thấy nó không
cần xảy ra.

---

## 4. Vì sao nó không làm sai dữ liệu production hiện tại?

Bốn lý do, xếp theo độ chắc chắn:

1. **Không có đường ghi nào.** Toàn bộ phần mới của PHB-04 chỉ ĐỌC. Không một
   dòng mã nào ghi, sửa hay xoá dữ liệu.
2. **Hai kho tách biệt.** Số cũ nằm ở bốn bảng `legacy_*`; số mới nằm ở nhóm
   bảng khác. Xoá và nhập lại toàn bộ sổ kế toán hiện hành cũng không chạm
   được vào một con số lịch sử nào, và ngược lại.
3. **Cơ sở dữ liệu tự ép dấu nguồn.** Ràng buộc `origin = 'LEGACY_REFERENCE'`
   nằm ở tầng cấu trúc, không phải ở tầng "nhớ viết cho đúng".
4. **Đã đo, không chỉ suy luận.** Có test nạp một bản legacy rồi đo lại toàn
   bộ số liệu của kỳ hiện hành: coverage giá nhập, doanh thu, số dòng — tất cả
   **giống hệt trước khi nạp**.

Những thứ PHB-04 **không** đụng tới, đúng như yêu cầu: dòng hàng kế toán đã
nhập · Product Identity · Tracking · lịch sử giá nhập · các lần chủ dự án sửa
tay ở PHB-03 · gán nhân viên · phân loại Gia dụng · các bản snapshot đã lưu.

---

## 5. Những chỉ số legacy nào được hỗ trợ?

**Với năm 2025 — đúng một chỉ tiêu: Doanh số tháng** (đơn vị: đồng).

Chỉ có vậy, vì trong toàn bộ bằng chứng đã được chấp nhận, năm 2025 chỉ có
đúng 12 ô số — mỗi tháng một ô tổng doanh số. Không có gì khác.

**Với các tháng báo cáo tay của 2026** — 16 cột của báo cáo cũ vẫn giữ nguyên
và vẫn xem được như trước: Tổng đơn, Tổng số SP, Tổng bán, DS quy đổi, Tổng
lợi nhuận, So tháng trước, Target, So target, và các cột lương/thưởng.

---

## 6. Chỉ số nào chỉ để tham khảo?

**Tất cả.** Không có một chỉ tiêu legacy nào được xếp loại "so được với số
mới" trong phiên bản này.

Đây không phải sự thận trọng thừa. Với mỗi chỉ tiêu đều có một khác biệt về
cách tính đã được chốt từ trước:

| Chỉ tiêu | Vì sao không so được |
|---|---|
| Doanh số / Tổng bán | Báo cáo tay và công cụ mới trừ chiết khấu khác nhau — đây là khác biệt **có chủ đích**, đã chốt ở `DEC-114` |
| Tổng lợi nhuận | Số cũ dựa trên giá nhập sửa tay; lợi nhuận mới chỉ được coi là chính thức khi đủ 100 % giá nhập |
| DS quy đổi | Dòng tổng trong workbook cũ cộng thiếu người bán, và vài kỳ dùng số gõ tay |
| Tổng số SP | Ô nguồn cũ bị trừ nhầm một tỉ lệ phần trăm khỏi một số lượng |
| So tháng trước | Cột cũ so trên "DS quy đổi"; chỉ tiêu được so của số mới là "Doanh thu bán hàng" |
| Tổng đơn | Không có bằng chứng hai cách đếm đơn cho cùng kết quả |

Vì vậy công cụ **hiện cả hai số cạnh nhau nhưng không trừ nhau**. Không có
phần trăm tăng trưởng nào được sinh ra giữa số cũ và số mới.

---

## 7. Chỉ số nào không có đủ bằng chứng?

**Với năm 2025:** Tổng đơn · Tổng số SP · DS quy đổi · Tổng lợi nhuận · Target
· chi tiết theo từng nhân viên · doanh số theo ngày.

**Với các tháng báo cáo tay 2026:** Tỉ lệ tồn kho (cột "Nơi nhập" không tồn
tại trong file ERP) · Thưởng · Ngày công · Lương cơ bản · Phụ cấp · Tổng lương
(thuộc luật nhân sự, đã hoãn khỏi V1).

Những chỉ tiêu này hiện **dấu gạch ngang `—`**, kèm câu giải thích vì sao
không có. Chúng **không bao giờ** hiện thành số 0. Một số 0 bịa ra nguy hiểm
hơn một ô trống, vì ô trống thì ai cũng biết là thiếu, còn số 0 thì trông như
một sự thật.

---

## 8. Có thể so legacy với dữ liệu hiện tại ở đâu?

**Ở phiên bản này: không ở đâu cả** — và điều đó được ghi rõ ngay trên màn
hình, kèm lý do cho từng cặp chỉ tiêu.

Có một ngoại lệ cần nói cho đúng: tỉ lệ **"so cùng kỳ năm trước"** đang hiện ở
trang "Doanh số ngày" là một con số **đã có sẵn trong workbook cũ, do Excel
tính**. Nó là số cũ so với số cũ, mang nhãn legacy như mọi ô cũ khác — không
phải phép so do công cụ này thực hiện.

Cơ chế so sánh được viết như một **cánh cổng thật**, không phải một câu "không"
cứng nhắc: ngày nào một chỉ tiêu được chứng minh là cùng nghĩa ở hai bên, chỉ
cần thêm một dòng vào bảng hợp đồng là phép so mở ra. Có test chứng minh cổng
đó thật sự đọc hợp đồng chứ không trả lời cứng.

---

## 9. Giao diện Chủ dự án sử dụng thế nào?

Có một tab mới: **"Lịch sử"**.

Trang đó có bốn phần, đọc từ trên xuống:

1. **Kỳ lịch sử của năm trước** — bảng 12 tháng của 2025 với doanh số từng
   tháng. Tháng nào không có số thì hiện `—`. Mỗi dòng ghi rõ số đó lấy từ ô
   nào của workbook.
2. **Đi tới kỳ** — danh sách mọi kỳ đang có, mỗi kỳ dán nhãn `SỐ CŨ`,
   `SỐ MỚI`, hoặc **cả hai**, kèm liên kết mở đúng trang tương ứng. Đây là chỗ
   chuyển qua lại giữa kỳ lịch sử và kỳ hiện hành mà không lẫn nguồn.
3. **So số cũ với số mới ở đâu?** — bảng nói thẳng từng cặp chỉ tiêu có so
   được không và vì sao.
4. **Chỉ tiêu lịch sử nào được hỗ trợ?** — hợp đồng đầy đủ, in nguyên văn.

Mọi con số cũ trên toàn hệ thống đều đeo nhãn `LEGACY` kèm đơn vị. Không có
đường nào hiện một số cũ mà thiếu nhãn.

---

## 10. Những gì cố tình KHÔNG làm?

- **Không** nhập lại báo cáo cũ qua đường xử lý kế toán hiện hành.
- **Không** tạo dòng hàng giả để "giả vờ" 2025 có giao dịch.
- **Không** dựng bảng mới hay nâng cấp cơ sở dữ liệu.
- **Không** mở lại `DEC-169` (`Summary 2025` vẫn ngoài phạm vi).
- **Không** mở lại PHB-03.
- **Không** dựng parser cho 99 dòng không phân loại được của `Summary 2025`.
- **Không** làm Target (PHB-05), Brand, Advanced Analytics, dọn dẹp R1/R2/R3.
- **Không** đổi Product Identity, Tracking, hay logic giá nhập.
- **Không** tái tạo mỗi sheet Excel thành một tab web.

---

## 11. Test đã chạy

```text
Test riêng của PHB-04   tests/test_phb04_legacy_reference.py   35 passed
Toàn bộ hệ thống        python -m pytest -q                    2171 passed, 11 skipped
Test golden (chống sai
số nghiệp vụ)           4 file golden                          74 passed, 2 skipped
```

Trước phiên, toàn bộ hệ thống là `2136 passed, 11 skipped`. Chênh lệch `+35`
đúng bằng số test mới — **không test cũ nào bị sửa, bị bỏ hay bị tắt**.

35 test mới chứng minh đúng những điều đã hứa: kỳ legacy đọc được · mọi số mang
dấu `LEGACY_REFERENCE` · số cũ không lọt vào đường kế toán · số cũ không làm
nhúc nhích coverage lợi nhuận · các trang PHB-03 giữ nguyên · điều hướng phân
biệt được hai nguồn · chỉ tiêu thiếu hiện `—` chứ không phải 0 · phép so chỉ
chạy khi hợp đồng cho phép · chỉ tiêu tham khảo không âm thầm sinh phần trăm ·
nạp lại cùng một file không nhân đôi số.

Các bộ kiểm tra governance cũng chạy: 4 bộ PASS, 1 bộ báo đúng 3 lỗi cũ đã
biết từ trước (không phát sinh lỗi mới).

---

## 12. Finding còn lại

Không có finding nào chặn.

**F-PHB04-01 (không chặn).** Trang "Lịch sử" có sẵn một câu cảnh báo cho
trường hợp không đọc được danh mục kỳ của số mới. Với cách hệ thống đang nối
dây hôm nay, trạng thái đó không xảy ra được trên production. Câu cảnh báo vẫn
được giữ và vẫn có test, vì nó là cùng một kỷ luật đã áp dụng ở nơi khác: một
danh sách thiếu nguồn không bao giờ được trông giống một danh sách đủ.

**F-PHB04-02 (không chặn, môi trường).** Trong phiên này, bản sao repo về máy
ở dạng rút gọn nên một test golden ban đầu báo lỗi vì thiếu một mốc lịch sử
git. Đã lấy đủ lịch sử và test PASS. Đây là chuyện của môi trường chạy, không
phải của mã.

---

## 13. Owner decision còn thiếu

**Không có quyết định nào đang chặn PHB-04.** Toàn bộ ngữ nghĩa của V1 đều đã
có thẩm quyền từ PHB-02 và `DEC-169`.

Hai câu hỏi được ghi lại cho tương lai, **không chặn gì cả**:

- **`OD-PHB04-A`** — Với một kỳ có **cả** số cũ **và** số mới, có bao giờ chủ
  dự án muốn nhìn thấy **một con số duy nhất** cho kỳ đó không, và nếu có thì
  nguồn nào thắng? Hôm nay công cụ hiện hai con số cạnh nhau, mỗi con một nhãn
  — nên câu hỏi này chưa cần trả lời.
- **`OD-PHB04-B`** — Có tháng 2026 nào chủ dự án muốn coi là "legacy thuần",
  kể cả khi công cụ đã có số cho tháng đó không? Hôm nay công cụ không giả
  định: kỳ có nguồn nào thì hiện đúng nguồn đó.

Một điểm cần nói rõ vì nó dễ bị hiểu nhầm: **ranh giới legacy / hiện hành
không phải là một cái mốc ngày.** Trong toàn bộ bằng chứng của dự án không có
quyết định nào đặt ra một ngày như vậy cho báo cáo. Cái thật sự tồn tại là
ranh giới **theo nguồn dữ liệu, tính riêng cho từng kỳ**. Phiên này **không
bịa ra một ngày** — mốc `2026-09-01` đã có trong dự án là mốc về **giá nhập**,
và hồ sơ dự án đã ghi rõ "hai cutover, không gộp".

---

## 14. Trạng thái PHB-04

```text
PHB_04 = IMPLEMENTED_AWAITING_REVIEW
```

Phần triển khai đã xong và đã có bằng chứng. Phần còn thiếu duy nhất là
**một lượt review độc lập** — do một phiên khác thực hiện, không phải phiên đã
viết mã. Theo quy tắc của dự án, chưa có lượt đó thì **chưa được gọi là
`DONE`**.

---

## 15. Bước tiếp theo

1. **Review độc lập PHB-04** — kiểm lại hợp đồng ngữ nghĩa (đặc biệt: kết luận
   "không chỉ tiêu nào so được" có đúng là suy ra từ bằng chứng không), kiểm
   phần tách biệt legacy/hiện hành, và kiểm 35 test mới. Đủ bằng chứng ⟹
   `PHB-04 = DONE`.
2. Sau đó: **PHB-05 — Target**, theo phần ý định nghiệp vụ đã freeze ở
   `DEC-PHB02-06`.
3. Việc dọn dẹp R1/R2/R3 của PHB-03 vẫn nằm ở nhánh phụ không chặn, đúng như
   đã quyết định.
