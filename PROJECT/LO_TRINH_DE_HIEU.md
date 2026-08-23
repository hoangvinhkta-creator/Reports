# LỘ TRÌNH DỰ ÁN — BẢN DỄ HIỂU

> File này viết cho người **không rành kỹ thuật/lập trình** — chủ dự án,
> quản lý, hoặc bất kỳ ai muốn biết dự án đang tới đâu mà không cần đọc
> thuật ngữ code.
>
> Bản đầy đủ, chi tiết kỹ thuật (dành cho người trực tiếp code): xem
> `PROJECT/PROJECT_PROGRESS.md`. File này là bản dịch dễ hiểu của cùng một
> lộ trình — **không phải một lộ trình khác**. Khi bản kỹ thuật thay đổi,
> file này phải được cập nhật theo (xem "Ghi chú" ở cuối) — ô Tick ở đây
> phải luôn khớp với trạng thái thật trong `PROJECT_PROGRESS.md`.
>
> Cập nhật lần cuối: 2026-08-23 — **bước 5 (nạp dữ liệu) đã xong hoàn toàn,
> kiểm tra đúng trên số liệu thật** (xem "Có gì mới" ngay bên dưới).

## Có gì mới — bước 5 xong hoàn toàn, đã kiểm tra bằng số liệu thật (2026-08-23)

**Bước 5 (TASK-101 — nạp và làm sạch dữ liệu) đã xong hoàn toàn.** Cùng lúc,
ba bước 6–8 (gán nhân viên, gộp đơn hàng, xác định nguồn quảng cáo) cũng
xong luôn — vì chúng nằm chung một khối công việc, không tách được.

Sếp đã gửi 2 file dữ liệu thật của Tín Phát (tháng 01/2026 và 06/2026) để
kiểm tra. Kết quả: **hệ thống đếm đúng tuyệt đối — 254 đơn tháng 01/2026 và
146 đơn tháng 06/2026**, khớp chính xác với số sếp đưa ra làm mốc kiểm tra.
Đối chiếu thêm bằng dòng "Tổng cộng" có sẵn trong chính file Excel (không
phải do hệ thống tự tính) — doanh số và chiết khấu cũng khớp tuyệt đối ở cả
hai tháng.

Có phát hiện một khoảng lệch nhỏ giữa số "Doanh số bán" ghi trong file thô và
số hệ thống tính ra — nhưng đây **không phải lỗi mới**, mà đúng như đã biết
từ trước: cột doanh số trong file thô ERP chưa trừ chiết khấu, hệ thống trừ
đúng theo quy tắc đã thống nhất. Không cần sửa gì.

File dữ liệu thật đã được xóa khỏi máy chạy việc ngay sau khi kiểm tra xong
— đúng quy định không lưu dữ liệu khách hàng vào hệ thống.

**Trước đó**, sếp đã duyệt Điểm duyệt 1 (GATE-00) và xem đợt rà soát 10 điểm
xác nhận về cách tính, trả lời trực tiếp 4 câu:

1. **"Đơn từ đâu" và "tính tiền theo tỷ lệ nào" giờ là hai việc tách rời**
   trong hệ thống — không đổi gì về cách bấm nút, chỉ là cách tính bên trong
   chính xác hơn. Nhóm Nội thành quy đổi 2 % như cũ, không bị ép về 5,5 %.

2. **Số liệu cũ năm 2026 sẽ cao hơn file Excel hiện tại khoảng 6 %** cho
   Hoàng và Kiên (khoảng 3 triệu đồng tiền thưởng cộng thêm cho cả hai người)
   — vì không nhập lại dữ liệu quảng cáo cũ cho gọn. **Sếp đã đồng ý chấp
   nhận** chênh lệch này.

3. **Chiết khấu trừ cả vào lợi nhuận**, không chỉ doanh số — sếp xác nhận
   đúng như mặc định hệ thống đang làm.

4. **Nhóm Nội thành/Gia dụng không bao giờ ghi "ADS"** — sếp xác nhận không
   cần lo tình huống đó, giữ nguyên cách tính hiện tại.

5. **Chính sách 2027 hiện chưa có gì khác 2026** — sếp xác nhận, sẽ hỏi lại
   khi có thay đổi thật.

**Còn 1 câu hỏi nhỏ chưa có câu trả lời**, sếp nói "chưa rõ": 88 dòng dữ liệu
có tên nhân viên lạ (không thuộc 6 người/nhóm đang bán hàng) xử lý ra sao khi
lên hệ thống thật. Không chặn việc bắt đầu làm — hệ thống tạm để những dòng
này vào hàng chờ kiểm tra tay, không tính cho ai cả. Chi tiết:
`docs/analysis/10_OPEN_QUESTIONS.md`.

## Dự án này làm gì, tóm tắt 1 câu

Xây một công cụ tự động tạo ra **Báo cáo Kinh doanh** hằng tháng cho công
ty, thay thế việc nhân viên phải tự tay ráp file Excel mỗi tháng — nhập
số liệu bán hàng thô, tự tính hoa hồng/lợi nhuận, tự lên báo cáo.

## Đang tới đâu rồi (tóm tắt nhanh)

File này gồm **hai bảng độc lập, không chặn nhau**:

- **Track A — Sản phẩm** (bảng chính bên dưới): đã xong 8/34 dòng (bước 1–8,
  trong đó bước 6–8 xong luôn cùng bước 5, đã kiểm tra bằng số liệu thật).
  Sẵn sàng bắt đầu bước 9.
- **Track B — Nền tảng kỹ thuật** (bảng ở cuối file): đã xong 6/9 dòng,
  một việc đang sẵn sàng làm (REM-T06), không ảnh hưởng ngày ra mắt sản
  phẩm.

Cuối file có thêm mục **"Bảo mật và phân chia luồng"** trả lời câu hỏi ngày
2026-08-23 về việc lưu dữ liệu qua máy chủ và tách riêng từng luồng việc.

## Cách đọc bảng bên dưới

Mỗi dòng là một công đoạn, theo đúng thứ tự phải làm từ trên xuống — trừ
khi cột cuối ghi rõ "làm song song được với bước khác".

**Cột Tick:**

| Ký hiệu | Nghĩa |
|---|---|
| ✅ | Đã làm xong |
| 🟡 | Đang chờ — là việc **duy nhất** đang cần hành động ngay bây giờ |
| ⬜ | Chưa bắt đầu (đang chờ các bước phía trước xong trước) |

**Cột Mức xử lý** — cho biết việc đó cần loại năng lực nào để làm, không
ảnh hưởng tới việc bạn có hiểu nó hay không, chỉ là ghi chú nội bộ cho
người thực hiện:

| Mức | Nghĩa là gì |
|---|---|
| **A** | Việc nhỏ, đơn giản, ít rủi ro (dọn dẹp, sửa lặt vặt) |
| **B** | Việc lập trình theo khuôn mẫu đã rõ ràng, làm đúng quy trình là ra |
| **C** | Việc cần suy nghĩ, thiết kế, cân nhắc kỹ — sai ở đây tốn công sửa nhiều |
| **D** | Việc thiết kế hình ảnh/giao diện — dự án này chưa tới bước dùng mức này |
| **Duyệt** | Không phải việc lập trình — là lúc chủ dự án xem và xác nhận |

## Track A — Checklist toàn bộ lộ trình sản phẩm

**Chú thích ký hiệu** (giống Track B bên dưới, để hai bảng đọc nhất quán):
`Mode` = MICRO (việc nhỏ, gọn) / MAJOR (việc lớn, có hồ sơ + gate riêng).
`D/R/B` = Difficulty/Risk/Blast Radius — độ khó / rủi ro / phạm vi ảnh
hưởng nếu sai, thang 1–5, số càng cao càng cần cẩn thận.

| Tick | Tên việc | Mục đích | Mức | Thứ tự / phụ thuộc |
|---|---|---|---|---|
| ✅ | 1. TASK-000 (MICRO, D1/R1/B2) — Dọn cấu trúc dự án | Có nền tảng gọn gàng để làm việc tiếp, không lộn xộn file | A | **GIAI ĐOẠN 0** — bước đầu tiên |
| ✅ | 2. TASK-001 (MAJOR, D2/R2/B1) — Lên kế hoạch tổng thể | Xác định làm gì, theo thứ tự nào, tránh làm ẩu rồi sửa lại | C | Sau bước 1 |
| ✅ | 3. TASK-002 (MAJOR, D3/R2/B1) — Đọc và đối chiếu dữ liệu mẫu | Hiểu đúng cách công ty đang bán hàng và tính lợi nhuận, trước khi viết bất kỳ dòng code nào | C | Sau bước 2 |
| ✅ | 4. TASK-003 (MICRO, D2/R2/B2) — Ghi lại các quyết định kỹ thuật lớn | Chọn cách tổ chức hệ thống ngay từ đầu, tránh phải đập đi làm lại giữa chừng | C | Sau bước 3 |
| ✅ | **GATE-00 — Điểm duyệt 1 — Sếp xác nhận dữ liệu** | Đọc phần phân tích dữ liệu, xác nhận đúng thực tế công ty. **PASS 2026-08-23.** | Duyệt | Sau bước 4 — đã xong |
| ✅ | 5. TASK-101 (MAJOR, D3/R3/B3) — Nạp và làm sạch dữ liệu bán hàng thô | Biến file Excel lộn xộn từ ERP thành dữ liệu tính toán được. **Xong hoàn toàn — đã kiểm tra đúng trên dữ liệu thật** (xem "Có gì mới" đầu file) | B | **GIAI ĐOẠN 1** — xong |
| ✅ | 6. TASK-102 (MAJOR, D2/R3/B3) — Gán đúng nhân viên phụ trách từng dòng bán hàng | Biết ai bán để tính đúng hoa hồng cho từng người. **Đã xây xong trong bước 5**, không phải làm riêng | B | Xong cùng bước 5 |
| ✅ | 7. TASK-103 (MAJOR, D2/R4/B4) — Gộp các dòng hàng thành từng đơn hàng hoàn chỉnh | Một đơn có thể có nhiều dòng sản phẩm, cần gộp lại đúng. **Đã xây xong trong bước 5** | B | Xong cùng bước 5 |
| ✅ | 8. TASK-104 (MAJOR, D3/R4/B5) — Xác định đơn nào từ quảng cáo, đơn nào nhân viên tự bán | **Quyết định trực tiếp thu nhập nhân viên** — cần làm rất cẩn thận. **Đã xây xong trong bước 5**, đã kiểm đủ 18 tình huống chuẩn | C | Xong cùng bước 5 |
| 🟡 | 9. TASK-105 (MAJOR, D3/R3/B3) — Tính giá nhập hàng cho từng sản phẩm | Cần biết giá nhập mới tính được lợi nhuận | B | Sẵn sàng bắt đầu ngay |
| ⬜ | 10. TASK-106 (MAJOR, D4/R4/B4) — Xử lý các trường hợp đặc biệt (hàng qua kho, đổi trả, NCC giao thẳng...) | Không phải đơn nào cũng tính bình thường, cần quy tắc riêng | C | Sau bước 9 |
| ⬜ | 11. TASK-107 (MAJOR, D2/R4/B4) — Tính lợi nhuận (lợi nhuận thật và lợi nhuận tính KPI riêng) | Hai con số phục vụ hai mục đích khác nhau (kế toán vs. thưởng KPI) | B | Sau bước 10 |
| ⬜ | 12. TASK-108 (MAJOR, D3/R5/B5) — Quy đổi doanh thu theo 2 nhóm nguồn khách hàng | **Phần rủi ro cao nhất** — sai ở đây nghĩa là sai lương của ai đó. Chọn tỷ lệ theo *nhân viên + nguồn đơn + ngày*, không suy trực tiếp từ nguồn đơn | C | Sau bước 11 |
| ⬜ | 13. TASK-109 (MAJOR, D3/R4/B4) — Tổng hợp báo cáo theo tháng và theo năm, cho từng người | Ra được đúng bảng Summary như công ty đang cần | B | Sau bước 12 |
| ⬜ | 14. TASK-110 (MAJOR, D2/R2/B2) — Rà soát dữ liệu bất thường, đưa vào hàng chờ kiểm tra tay | Không để một dòng dữ liệu lỗi âm thầm làm sai cả báo cáo | B | Sau bước 12 (làm song song được với bước 13) |
| ⬜ | 15. TASK-111 (MAJOR, D3/R2/B2) — Xuất kết quả ra file Excel giống mẫu hiện tại | Người dùng vẫn nhận được đúng định dạng quen thuộc | B | Sau bước 13 và 14 |
| ⬜ | 16. TASK-112 (MICRO, D1/R2/B2) — Đóng gói thành công cụ chạy được | Bước cuối để bắt đầu dùng thử trên máy | A | Sau bước 15 |
| ⬜ | **GATE-01 — Điểm duyệt 2 — Đối chiếu số liệu thật** | So khớp kết quả công cụ tính ra với sổ sách thật. Chỉ khi số khớp mới coi "bộ máy tính toán" xong | Duyệt | Sau bước 16 |
| ⬜ | 17. TASK-201 (MAJOR, D3/R4/B5) — Thiết kế nơi lưu dữ liệu lâu dài | Để nhiều người cùng xem/sửa dữ liệu mỗi ngày, không chỉ chạy 1 lần trên máy | C | **GIAI ĐOẠN 2** — sau Điểm duyệt 2 |
| ⬜ | 18. TASK-202 (MAJOR, D3/R4/B4) — Ghi lại lịch sử ai sửa gì, khi nào | Truy vết được khi có sai lệch, ai đã đổi số liệu | C | Sau bước 17 |
| ⬜ | 19. TASK-203 (MAJOR, D3/R3/B4) — Kết nối phần lưu trữ với giao diện sử dụng | Để các bước 22–27 (giao diện web) có dữ liệu để hiển thị. **Đã có bản thiết kế sơ bộ 24 đường kết nối, tách riêng theo từng luồng việc** — xem "Bảo mật và phân chia luồng" cuối file | B | Sau bước 18 |
| ⬜ | 20. TASK-204 (MAJOR, D3/R5/B5) — Thêm đăng nhập, chỉ người có quyền quản trị mới dùng được | Bảo vệ dữ liệu lương và thông tin khách hàng — sếp đã quyết định chỉ 1 loại tài khoản (quản trị), không phân nhiều cấp | C | Sau bước 19 |
| ⬜ | 21. TASK-205 (MAJOR, D4/R4/B4) — Cho phép tính lại nhanh khi có dữ liệu mới | Không phải tính lại từ đầu mỗi lần có đơn hàng mới | C | Sau bước 20 |
| ⬜ | 22. TASK-301 (MAJOR, D3/R2/B3) — Màn hình tải file lên, xem trước | Kiểm tra dữ liệu trước khi nhập chính thức vào hệ thống | B | **GIAI ĐOẠN 3** — sau bước 21 |
| ⬜ | 23. TASK-302 (MAJOR, D3/R2/B3) — Bảng chi tiết theo nhân viên/tháng, sửa trực tiếp | Người dùng chỉnh sửa số liệu hằng ngày ngay trên web | B | Sau bước 22 |
| ⬜ | 24. TASK-303 (MAJOR, D3/R2/B3) — Màn hình tổng quan, biểu đồ theo tháng/năm | Nhìn nhanh tình hình kinh doanh, so sánh giữa các nhân viên | B | Sau bước 22 (làm song song được với bước 23) |
| ⬜ | 25. TASK-304 (MAJOR, D3/R2/B3) — Màn hình cấu hình quy tắc | Đổi tỷ lệ quy đổi, target, danh sách nhân viên mà không cần sửa code | B | Sau bước 22 |
| ⬜ | 26. TASK-305 (MAJOR, D3/R2/B3) — Màn hình duyệt dữ liệu bất thường | Xử lý các dòng bị cảnh báo ở bước 14 | B | Sau bước 22 |
| ⬜ | 27. TASK-306 (MAJOR, D3/R2/B3) — Nút xuất Excel ngay trên web | Không cần quay lại chạy công cụ dòng lệnh nữa | B | Sau bước 22 |
| ⬜ | **GATE-03 — Điểm duyệt 3 — Nghiệm thu bản dùng thử đầy đủ** | Kiểm tra đủ mọi tiêu chí trước khi coi sản phẩm "dùng được thật" cho cả đội bán hàng | Duyệt | Sau bước 23–27 |
| ⬜ | 28. TASK-401 (MAJOR, chưa chấm D/R/B) — Kết nối bảng giá nhập chính thức (nếu công ty có sẵn hệ thống giá) | Tự động tra giá thay vì phải nhập tay | C | **GIAI ĐOẠN 4** — sau Điểm duyệt 3 |
| ⬜ | 29. TASK-402 (MAJOR, chưa chấm D/R/B) — Chuẩn hóa mã sản phẩm | Tránh tình trạng một sản phẩm bị ghi nhiều mã khác nhau | B | Sau bước 28 |
| ⬜ | 30. TASK-403 (MAJOR, chưa chấm D/R/B) — Công thức hóa cách tính hoa hồng theo target | Hiện đang nạp bảng tỷ lệ quan sát được làm dữ liệu tạm; bước này biến nó thành công thức chính thức | C | Sau bước 28 (làm song song được với bước 29) |
| ⬜ | 31. TASK-404 (MAJOR, chưa chấm D/R/B) — Xử lý trường hợp một đơn có 2 nguồn khách hàng cùng lúc | Trường hợp ngoại lệ hiếm gặp nhưng cần xử lý đúng | C | Sau bước 28 |

## Track B — Việc nền chạy song song (không ảnh hưởng ngày ra mắt sản phẩm)

Có một nhóm việc khác đang chạy song song để giữ cho "quy trình làm việc
nội bộ" của dự án luôn rõ ràng, nhất quán — như dọn dẹp hồ sơ/quy trình nội
bộ, không phải tính năng của sản phẩm. Việc này **không ảnh hưởng tới ngày
sản phẩm ra mắt**, sếp không cần theo dõi sát trừ khi muốn biết chi tiết.

Bảng này giữ nguyên mã kỹ thuật gốc (REM-Txx, Mode, Tier, chỉ số D/R/B) vì
đây vốn là công việc kỹ thuật thuần túy — không có cách diễn giải "không
thuật ngữ" nào có nghĩa hơn chính mã của nó. Đặt ở đây để xem tiện trong
cùng một file, không phải phải mở `PROJECT/PROJECT_PROGRESS.md` riêng.

**Chú thích ký hiệu:** `Mode` = MICRO (việc nhỏ, gọn) / MAJOR (việc lớn, có
hồ sơ + gate riêng). `D/R/B` = Difficulty/Risk/Blast Radius — độ khó / rủi
ro / phạm vi ảnh hưởng nếu sai, mỗi chỉ số thang 1–5, số càng cao càng cần
cẩn thận. `Tier` dùng chung thang A–D như bảng Track A ở trên.

| Tick | Tên việc | Mục đích | Tier | Thứ tự / phụ thuộc |
|---|---|---|---|---|
| ✅ | REM-T02 (MAJOR, D2/R3/B5) — Đưa gói governance lên gốc repository | Sửa lỗi mọi đường link nội bộ bị 404 do cấu trúc thư mục sai | C | DONE (S003) — trùng việc với TASK-000 của Track A, đã hội tụ đúng kết quả |
| ✅ | REM-T04 (MICRO, D1/R2/B2) — Sửa 3 đường dẫn tham chiếu bị gãy | Các link nội bộ trong tài liệu governance trỏ đúng chỗ | A | DONE (S004) |
| ✅ | REM-T03 (MAJOR, D3/R2/B2) — Xây công cụ tự động kiểm tra cấu trúc + tham chiếu | Máy tự phát hiện khi ai đó (người hoặc AI) làm lệch cấu trúc, thay vì phải tin lời khai | B | DONE (S005) |
| ✅ | REM-T07 (MAJOR, D2/R2/B2) — Bật kiểm tra tự động (CI) trên mỗi lần đẩy code | Có nguồn xác nhận độc lập, bền vững cho các thay đổi rủi ro cao trong tương lai | B | DONE (S005) |
| ✅ | Phase Gate 01 — Xác nhận PHASE-01 hoàn tất | Chốt chính thức trước khi coi giai đoạn dọn nền governance là xong | Gate | PASS (S006) — 10/10 check |
| ✅ | REM-T05 (MAJOR, D2/R2/B3) — Sửa tài liệu tham khảo đang ghi sai thực tế | Một báo cáo cũ đang khẳng định "đã kiểm tra PASS" không đúng sự thật — sửa để tài liệu đáng tin lại | B | DONE (S008) — 4/4 việc kiểm tra bắt buộc PASS |
| ⬜ | Phase Gate 02 — Xác nhận PHASE-02 hoàn tất | Chốt sau khi REM-T06 xong | Gate | Sau REM-T06 |
| 🟡 | REM-T06 (MICRO, D1/R1/B1) — Dọn dẹp thư mục gốc repo (thêm README/LICENSE) | Repo có tài liệu giới thiệu chuẩn khi người ngoài ghé xem | A | **Sẵn sàng làm ngay** — kế hoạch đã chốt xong |
| ⬜ | Phase Gate 03 — Xác nhận PHASE-03 hoàn tất, xem lại việc sao lưu dữ liệu | Chốt toàn bộ track dọn nền governance | Gate | Sau REM-T06 |

*(REM-T01 không có trong bảng — đã hủy vì trùng việc đã làm xong ở nơi
khác, không phải việc bị bỏ sót.)*

## Bảo mật và phân chia luồng — trả lời câu hỏi ngày 2026-08-23

Sếp hỏi hai câu: (1) có phần nào bảo mật thông tin, lưu qua máy chủ thay vì
để lộ hết ở màn hình người dùng không, và (2) đã có kế hoạch tách riêng từng
luồng việc thay vì dồn tất cả vào một trang duy nhất chưa.

**Trả lời ngắn: có cả hai, đã có thiết kế, và sếp đã chốt luôn một quyết định
quan trọng: công cụ này chỉ dành cho quản trị nội bộ.**

### Quyết định của sếp (2026-08-23)

Đây là công cụ **quản trị nội bộ**, không phải công cụ nhiều cấp nhân viên tự
vào xem. **Chỉ một loại tài khoản — quản trị — được dùng công cụ.** Không làm
riêng tài khoản "chỉ xem" hay "chỉ sửa phần của mình" ở bản đầu tiên.

- Ai không có tài khoản quản trị: **không mở được** giao diện web, và mọi yêu
  cầu gửi thẳng tới máy chủ đều bị từ chối — trừ bước đăng nhập/đăng xuất.
- Tài khoản quản trị: toàn quyền — xem báo cáo, nạp dữ liệu, sửa số liệu, đổi
  cấu hình, xem nhật ký, xuất Excel.
- Việc chặn vẫn nằm ở máy chủ, không phải chỉ ẩn nút trên màn hình — đúng yêu
  cầu bảo mật ban đầu.
- Thiết kế cơ sở dữ liệu vẫn để chỗ thêm loại tài khoản khác sau này nếu công
  ty cần, nhưng **không xây trước** khi chưa có nhu cầu thật.

Quyết định này đóng luôn ba câu hỏi từng nêu ở bản trước (ai xem được số của
ai, ai xem giá nhập, ai được chốt số liệu) — vì giờ chỉ có một loại tài khoản,
ba câu đó không còn cần hỏi riêng nữa.

### Về phân chia luồng

Mỗi màn hình có đường dẫn riêng, mở thẳng được, bấm Back/Forward đúng — không
dồn tất cả sau một link. Ví dụ: `/dashboard` (tổng quan), `/review` (duyệt dữ
liệu bất thường), `/settings/users` (quản lý tài khoản). Tổng cộng 14 màn
hình và 24 đường kết nối dữ liệu, mỗi cái gắn với đúng một bước trong bảng
Track A. Phần này không đổi so với trước.

### Lưu ý

Phần thiết kế đường dẫn (route) đã chốt từ trước, không đổi. Phần phân quyền
vừa được chốt lại theo quyết định trên — **cả hai đều đã là quyết định chính
thức**, không còn là bản nháp chờ duyệt. Việc còn lại chỉ là lập trình đúng
theo thiết kế khi tới Giai đoạn 2. Bản kỹ thuật đầy đủ:
`docs/adr/ADR-105-route-map-and-authorization-model.md`.

## Ghi chú quan trọng

- File này **không tự động cập nhật**. Người thực hiện dự án phải cập nhật
  tay cột Tick ở đây mỗi khi trạng thái trong `PROJECT/PROJECT_PROGRESS.md`
  (bản kỹ thuật) thay đổi — kể cả khi thêm/bớt bước hoặc đổi thứ tự.
- Số thứ tự đầu mỗi dòng ("5.", "12."...) chỉ để dễ trao đổi ("bước số 8"),
  không phải mã chính thức. Mã chính thức là phần `TASK-xxx`/`GATE-xx`/
  `REM-Txx` đi kèm ngay sau — lấy nguyên văn từ `PROJECT/PROJECT_PROGRESS.md`,
  dùng mã đó nếu cần đối chiếu hoặc trao đổi với người trực tiếp code.
- Có sai lệch giữa file này và bản kỹ thuật → bản kỹ thuật
  (`PROJECT/PROJECT_PROGRESS.md`) luôn là đúng, báo lại để sửa file này.
