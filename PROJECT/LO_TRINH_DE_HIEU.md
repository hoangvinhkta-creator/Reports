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
> Cập nhật lần cuối: 2026-08-23 — **bước 14 đã qua hai vòng soát xét, cả hai
> đều bị trả về, đã sửa xong cả hai, đang chờ soát xét vòng 3** (xem "Có gì
> mới" ngay bên dưới). Trước đó: bước 12 đã xong và đã qua soát xét độc lập.

## Có gì mới — bước 14 qua vòng soát xét thứ hai, bị trả 4 lỗi, đã sửa (2026-08-23)

**Cả 4 lỗi đều đã sửa, mỗi lỗi kèm bài kiểm tra riêng.** Hai lỗi đáng kể về
nghiệp vụ:

1. **Dòng không ghi tên nhân viên bị đếm nhầm thành "có tên lạ bán nhiều
   hàng".** Dòng trống thì không có *tên* nào để thiếu cả — nó đã được báo ở
   loại "thiếu nhân viên" rồi. Cảnh báo sinh ra từ đó không chỉ được ra dòng
   nào, nên người duyệt không mở được gì.
2. **Cảnh báo "nhân viên đã nghỉ mà vẫn có đơn" báo nhầm.** Khi một người
   nghỉ rồi quay lại (hoặc bàn giao), danh sách có **hai bản ghi cùng tên**:
   bản cũ đã đóng, bản mới đang chạy. Công cụ trước đây gộp theo *tên*, nên
   bản cũ đã đóng "mượn" đơn hàng của bản mới và kêu oan. Nay công cụ chấm
   **theo ngày của từng dòng** và gắn đúng vào bản ghi mà hệ thống thật sự
   dùng cho ngày đó — giống hệt cách tính lương đang làm.

Hai lỗi còn lại thuộc về chất lượng kiểm chứng: mô tả trạng thái dự án còn sót
chỗ ghi "chưa viết code" (đã đồng bộ lại), và bài kiểm tra "công cụ không được
sửa dữ liệu" chụp ảnh **sau** khi đã chạy một lần rồi mới so — nghĩa là nếu có
sửa thật thì cả hai ảnh đều dính, không phát hiện được. Nay ảnh được chụp
**trước** lần chạy đầu tiên.

**Không đổi cách tính tiền, không đổi ai nhận doanh số. Vẫn chưa gộp vào nhánh
chính.**

## Ghi chép cũ (đã bị mục trên thay thế) — bước 14 bị trả về, đã sửa xong (2026-08-23)

> Đây là bản ghi của một mốc đã qua trong cùng ngày. Trạng thái hiện tại
> nằm ở mục "Có gì mới" đầu file.

**Người soát xét độc lập trả bước 14 về với 6 lỗi**, dù bản nộp đã chạy đúng
toàn bộ 207 bài kiểm tra tự động. Lại đúng bài học của bước 12: *tự mình kiểm
tra thấy đạt thì chưa đủ.* Cả 6 đã sửa, mỗi lỗi kèm một bài kiểm tra riêng để
lần sau không tái diễn.

**Ba việc sếp đã quyết trong đợt này:**

1. **Cho phép báo thêm 3 loại lỗi nghiêm trọng về danh sách nhân viên.** Trước
   đó công cụ đã báo chúng, nhưng đó là làm vượt phạm vi đã chốt — nay được
   duyệt chính thức nên không còn là làm vượt nữa.
2. **Cách nhận biết "dòng phụ" (chi phí vận chuyển, chênh VAT…) chỉ là tạm
   thời.** Nó tồn tại vì bước 7 (chuẩn hóa loại dòng) chưa làm, và **bước 7
   sẽ phải thay thế nó**. Đồng thời cấm chỉnh cách nhận biết chỉ để ra đúng
   con số cũ (1.261 dòng) — con số đó là mốc tham khảo, không phải đích đến.
3. **Nhân viên đã đánh dấu nghỉ mà vẫn có đơn** thì công cụ báo lên hàng chờ.
   Trước đây chỗ này báo nhầm là "thiếu nhân viên" (sai — biết rõ là ai);
   nhưng nếu chỉ gỡ đi thì sẽ **im lặng hoàn toàn** trong khi doanh số vẫn
   chạy vào tên người đó. Tôi đã **dừng lại hỏi sếp** thay vì tự quyết.

**Một lỗi đáng nhớ nhất:** cách nhận biết dòng phụ dùng chữ `"phí "` (có dấu
cách ở cuối) như một mẹo. Nếu ai đó gỡ dấu cách, `"phí"` sẽ khớp cả
**"bàn phím"** — một sản phẩm thật bị công cụ coi là dòng phụ và hạ mức cảnh
báo, không ai biết. Nay công cụ khớp theo **nguyên từ**, và có hẳn một bài
kiểm tra dùng "Bàn phím cơ Logitech" để chặn đúng tình huống đó.

**Vẫn chưa gộp vào nhánh chính** — chờ soát xét vòng 2.

## Ghi chép cũ (đã bị mục trên thay thế) — bước 14 đã làm xong, chờ soát xét (2026-08-23)

> Đây là bản ghi của một mốc đã qua trong cùng ngày. Trạng thái hiện tại
> nằm ở mục "Có gì mới" đầu file.

Sếp đã duyệt và chốt bảng kiểm tra cuối, nên công cụ được xây luôn trong cùng
ngày. **Kết quả: 16/17 điều kiện đạt.**

**Công cụ giờ tự phát hiện 7 loại dữ liệu bất thường** mỗi lần nạp file:

| Loại | Ví dụ |
|---|---|
| Thiếu thông tin | Thiếu ngày, mã đơn, nhân viên, số lượng, doanh số |
| Bất thường (công cụ tự tính) | Số lượng ≤ 0, giá bán = 0, giá nhập > giá bán, lợi nhuận âm |
| Bất thường (số ERP báo) | ERP báo lợi nhuận âm — ghi rõ "số của ERP, chưa kiểm chứng" |
| Đơn mâu thuẫn | Một đơn ghi hai nhân viên, hoặc hai ngày khác nhau |
| Nguồn đơn | Người dùng sửa tay khác với quy tắc tự động |
| Trùng dòng | Hai dòng nội dung giống hệt nhau |
| Nhân viên chưa có trong danh sách | Tên lạ bán nhiều hàng, hoặc người có tên mà không có đơn nào |

**Ba điều đáng nói:**

1. **Nạp file không bao giờ bị chặn.** Kể cả khi mọi dòng đều có cảnh báo,
   công cụ vẫn xử lý xong và trả kết quả — cảnh báo đi kèm bên cạnh, không
   chặn phía trước. Đây là yêu cầu trong đặc tả và đã có bài kiểm tra riêng.
2. **Hai cảnh báo "nhẹ" đã được xử lý** — chính là điều ghi ở phần "bước 12"
   bên dưới. Trước đây chúng chỉ hiện khi có người chạy tay một công cụ phân
   tích riêng; giờ chúng hiện ngay trong lúc nạp dữ liệu. Còn lại là làm màn
   hình cho người xem (bước 26).
3. **Đơn ghi hai nhân viên: công cụ báo, KHÔNG tự quyết.** Theo đúng chỉ đạo
   của sếp. Cảnh báo ghi đủ: mã đơn, những nhân viên nào bị phát hiện, dòng
   nào, và người mà cách tính cũ đang chọn — ghi rõ đó chỉ là **cách làm cũ**,
   không phải kết luận ai là chủ đơn. Ai nhận doanh số vẫn là quyết định của
   sếp.

**Điều kiện còn lại (thứ 17):** đối chiếu trên file bán hàng thật. Không làm
được ở đây vì file đó chứa thông tin khách hàng nên cố ý không lưu trong kho
mã nguồn. **Bước 14 chưa được tính là hoàn thành cho tới khi chạy được phép
đối chiếu này.**

**Chưa gộp vào nhánh chính** — đang chờ người soát xét độc lập, theo đúng cách
đã làm với bước 12.

## Ghi chép cũ (đã bị mục trên thay thế) — bước 14 đang chờ sếp duyệt (2026-08-23)

> Đây là bản ghi của một mốc đã qua trong cùng ngày. Trạng thái hiện tại
> nằm ở mục "Có gì mới" đầu file.

**Chưa viết dòng code nào.** Trước khi bắt tay làm bước 14 (rà soát dữ liệu
bất thường), chúng tôi đọc lại toàn bộ yêu cầu và phát hiện **bản đặc tả thiếu
4 chỗ có thể làm sai kết quả**. Sếp đã trả lời cả 4, ghi lại thành quyết định
**DEC-128**:

1. **Cảnh báo "thiếu giá nhập"** sẽ đúng với **toàn bộ 11.765 dòng**, vì công
   ty chưa có bảng giá điện tử — đây là điều đã biết, không phải lỗi. Nên
   gộp thành **một dòng thông báo duy nhất**, thay vì 11.765 dòng cảnh báo mà
   không ai đọc nổi.
2. **Cảnh báo "lợi nhuận âm"** tách làm hai loại rõ ràng: loại do công cụ tự
   tính (hiện chưa tính được vì thiếu giá nhập) và loại **lấy từ số ERP đang
   báo** (1.912 dòng) — loại sau ghi rõ là "số của ERP, chưa kiểm chứng", để
   không ai nhầm nó là số đã được xác minh.
3. **1.261 dòng phụ hợp lệ** (chi phí vận chuyển, chênh VAT, phí lắp đặt…)
   sẽ được hạ xuống mức "chỉ để biết", không kêu như lỗi. Và **cảnh báo trùng
   dòng** đổi cách nhận biết, vì cách ghi trong đặc tả về mặt kỹ thuật không
   bao giờ xảy ra được.
4. **Đơn hàng ghi hai nhân viên khác nhau**: công cụ sẽ **báo lên hàng chờ**
   nhưng **không tự ý đổi cách tính tiền**. Sếp chọn giữ ranh giới này — đổi
   cách tính tiền phải là một quyết định riêng.

**Việc còn lại trước khi bắt đầu code:** sếp xác nhận **chốt (đóng băng) bảng
kiểm tra cuối** của bước 14 — danh sách 17 điều kiện phải đạt thì mới được coi
là xong. Chốt rồi thì mới bắt đầu làm.

**Một điều cần biết:** có **một điều kiện không thể kiểm ở đây được** — đối
chiếu trên file bán hàng thật. File đó chứa tên, số điện thoại, địa chỉ khách
hàng nên **cố ý không lưu trong kho mã nguồn**. Muốn đóng điều kiện đó, cần
chạy công cụ ở nơi có file thật.

## Có gì mới — bước 12 đã xong và được duyệt (2026-08-23)

**Phần lõi của bước 12 đã hoàn tất và được người soát xét độc lập chấp nhận
sau 4 vòng kiểm tra.** Chi tiết nghiệp vụ giữ nguyên như mô tả bên dưới.

**Điều đáng ghi nhận:** bản làm đầu tiên đã chạy đúng toàn bộ 119 bài kiểm tra
tự động và tự báo "52 ô khớp, 0 ô lệch". Nhưng người soát xét độc lập vẫn tìm
ra nhiều lỗi thật, trong đó có **một lỗi nghiêm trọng ảnh hưởng trực tiếp tới
tiền lương**: nhân viên chưa có trong danh sách vẫn được gán tỷ lệ 5,5 % thay
vì phải đưa vào danh sách chờ xử lý. Và một trường hợp **"khớp giả"** — 16
trong 52 ô chỉ khớp vì chính công cụ đối chiếu đã tự gán sẵn đáp án.

Sau khi sửa, con số đối chiếu thật là **36 ô khớp chính xác, 0 ô lệch**, cộng
19 ô ghi rõ là **không kiểm chứng độc lập được** (các dòng gộp của kênh và hai
tên nhân viên cũ) — **không tìm cách đưa về 52 bằng phỏng đoán**.

Bài học: *tự mình kiểm tra thấy đạt thì chưa đủ; phải có người khác soát xét
độc lập.*

**Một điểm cần nhớ khi làm màn hình sau này:** hệ thống có hai loại cảnh báo
"nhẹ" — nhân viên có trong danh sách nhưng không có đơn nào, và tên lạ bán
nhiều hàng hơn cả nhân viên nhỏ nhất. Hai cảnh báo này **bắt buộc phải hiện
rõ** trên màn hình duyệt, **không được bỏ qua âm thầm** — vì bỏ qua nghĩa là
có người thật đang bán hàng mà hệ thống không tính doanh số cho ai cả.

## Chi tiết nghiệp vụ bước 12

**Đây là phần rủi ro cao nhất của cả dự án** — chọn sai tỷ lệ quy đổi là sai
lương của người thật. Vì vậy trước khi viết một dòng code nào, đã rà soát ba
vòng với sếp và chốt lại một số điểm quan trọng:

**1. Vinh, Quý, Hiệp giờ là ba nhân viên riêng biệt.** Trước đây hệ thống gộp
ba người thành một cái tên chung "Nội thành" — làm mất danh tính từng người.
Nay mỗi người giữ tên riêng, và cái họ dùng chung là **nhóm** (`NOI_THANH`),
chứ không phải cái tên.

**2. Gia dụng không phải là một nhân viên, cũng không phải một nhóm người —
mà là một loại hàng.** Cùng một nhân viên có thể bán cả Điện máy lẫn Gia dụng
trong **cùng một đơn**: kiểm tra trên dữ liệu thật thấy **118 đơn** như vậy.
Nếu áp một tỷ lệ cho cả đơn thì 118 đơn đó tính sai. Nay tỷ lệ được chọn cho
**từng dòng hàng**, không phải cho cả đơn.

**3. Cùng một mã máy nhưng người bán khác nhau thì tỷ lệ khác nhau.** Ví dụ
máy lọc không khí: nếu đi qua kênh Gia dụng thì 8 %, nhưng nếu Ly bán thì vẫn
5,5 % — đúng như báo cáo cũ đang tính. Đã kiểm chứng: 34 % số dòng hàng Gia
dụng là do nhân viên thường bán, nên nếu làm sai điểm này thì rất nhiều dòng
sẽ lệch.

**Kết quả kiểm tra trên số liệu thật của công ty:**

- Đối chiếu **55 ô tỷ lệ** trong file `Báo cáo Kinh doanh 2026` → **36 ô khớp
  chính xác, 0 ô lệch**; 19 ô còn lại ghi rõ là **không kiểm chứng độc lập
  được** (các dòng gộp của kênh Nội thành/Gia dụng và hai tên nhân viên cũ
  Linh/Fanpage). Con số này là sau khi sửa lỗi "khớp giả" mà người soát xét
  phát hiện — xem phần đầu file.
- Nhận diện đúng **8 nhân viên trên 14.389 dòng** dữ liệu thật. 107 dòng của
  5 người chưa khai báo được đưa vào danh sách chờ xử lý, **không bị bỏ sót
  và cũng không bị gán bừa tỷ lệ của ai**.
- **151/151** bài kiểm tra tự động đều đạt.

**Nguyên tắc an toàn đã cài sẵn:** nếu hệ thống không tìm được tỷ lệ phù hợp,
nó **báo "chưa xác định"** chứ tuyệt đối không mượn tỷ lệ của người khác. Nếu
cấu hình có hai dòng mâu thuẫn ngang nhau, hệ thống **báo lỗi** chứ không tự
chọn bừa một cái.

**Đã gộp vào nhánh chính** sau khi soát xét độc lập đạt (vòng 4).

## Có gì mới trước đó — bước 11 xong (2026-08-23)

**Bước 11 (TASK-107 — tính lợi nhuận) đã xong phần "lợi nhuận kế toán"
(`AccountingProfit`)** — con số lợi nhuận thật, dùng cho sổ sách. Ngay sau
khi sếp duyệt bước 10, sếp chốt thêm 6 nguyên tắc quan trọng cho cách hai
luồng số liệu — **lợi nhuận kế toán thật** và **lợi nhuận tính KPI/thưởng**
— phải tách biệt nhau, không được lẫn:

- Lợi nhuận kế toán không phụ thuộc gì vào các khoản điều chỉnh KPI (Qua
  kho, KHBH...) — hai con số hoàn toàn độc lập.
- Điều chỉnh KPI không bao giờ được sửa lại số liệu kế toán.
- Sau này một đơn hàng có thể có **nhiều** điều chỉnh cùng lúc (ví dụ vừa
  Qua kho vừa KHBH) — cần lưu riêng từng điều chỉnh, không gộp thành một số.
- Cần phân biệt rõ "số tiền hệ thống **gợi ý**" và "số tiền **đã chốt**" —
  hai giá trị khác nhau, không ghi đè lẫn nhau.
- Chỉ điều chỉnh nào đã được **xác nhận thật** mới được tính vào lợi nhuận
  KPI/thưởng — số mới chỉ là gợi ý thì chưa được dùng.
- Không bao giờ coi điều chỉnh chưa xác định là 0.

Vì cách chốt lương/thưởng (lợi nhuận KPI, không phải lợi nhuận kế toán) cần
những điều chỉnh đã xác nhận thật — mà việc "xác nhận" cần màn hình chọn tay
(chưa xây, thuộc giai đoạn sau) — bước này **chỉ làm phần lợi nhuận kế
toán** trước. Phần lợi nhuận KPI sẽ làm khi màn hình chọn tay + chỗ lưu điều
chỉnh đã xác nhận sẵn sàng.

## Có gì mới trước đó — bước 10 xong (2026-08-23)

**Bước 10 (TASK-106 — tính điều chỉnh KPI) đã xong**, sau khi sếp trả lời 4
câu hỏi làm rõ về cách tính. Kết quả:

- **Qua kho / NCC giao** — số tiền trừ tính theo **phương tiện giao hàng**,
  không theo loại sản phẩm: xe máy chở hàng nhẹ trừ 50 nghìn, xe máy chở
  hàng cồng kềnh trừ 100 nghìn, ô tô trừ 200 nghìn.
- **KHBH / Thợ lắp** — chỉ có mức trừ mặc định khi sản phẩm là **điều hòa**
  (trừ 50 nghìn / 200 nghìn). Sản phẩm khác điều hòa: **không có mặc định**,
  luôn phải nhập tay số tiền.
- **Nhận diện điều hòa** — hệ thống tự dò chữ "điều hòa" trong tên sản phẩm
  (file thô ghi rõ chữ này trước tên đời máy) — đã kiểm tra và đúng trên cả
  2 tháng dữ liệu thật.
- **Cách kích hoạt** — người dùng **chọn tay sau khi nhập dữ liệu** loại
  điều chỉnh áp dụng cho từng đơn; hệ thống không tự động quét rồi áp.

**Quan trọng:** vì bước này cần người dùng chọn tay, mà màn hình để chọn tay
chưa được xây (thuộc giai đoạn sau, khi có giao diện thật), hệ thống hiện
mới xây xong **phần "gợi ý số tiền"** — sẵn sàng để màn hình chọn tay sau
này gọi tới và điền sẵn con số, người dùng vẫn luôn sửa được. Phần lưu lựa
chọn thật của người dùng sẽ làm ở giai đoạn có giao diện.

## Có gì mới trước đó — bước 9 xong (2026-08-23)

**Bước 9 (TASK-105 — tính giá nhập hàng) đã xong.** Vì công ty chưa có bảng
giá nhập điện tử (Price Master) nào, hệ thống hiện để **mọi giá nhập ở
trạng thái "Chờ nhập"** — đúng như đã thống nhất từ đầu (không suy đoán giá,
không tự gán bằng 0). Phần khung sẵn sàng để sau này cắm bảng giá thật vào
mà không phải sửa lại phần đã làm.

**Bước 10 (tính điều chỉnh KPI, ví dụ "Qua kho -100") đang tạm dừng để làm
rõ một điểm:** rà lại tài liệu phân tích phát hiện danh sách điều chỉnh này
(Qua kho, KHBH, Thợ lắp, NCC giao) hiện chỉ có trong file báo cáo cũ — do
người làm báo cáo **gõ tay**, không nằm trong file dữ liệu thô từ ERP. Cần
làm rõ với đội kỹ thuật/ERP xem có lấy được cột này tự động không, trước khi
viết tiếp bước 10.

## Có gì mới trước đó — bước 5 xong hoàn toàn, đã kiểm tra bằng số liệu thật (2026-08-23)

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

- **Track A — Sản phẩm** (bảng chính bên dưới): đã xong 9/34 dòng (bước 1–9,
  trong đó bước 6–8 xong luôn cùng bước 5). Bước 10 (🟡) tạm dừng, cần làm
  rõ một điểm về nguồn dữ liệu trước khi viết tiếp.
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
| ✅ | 9. TASK-105 (MAJOR, D3/R3/B3) — Tính giá nhập hàng cho từng sản phẩm | Cần biết giá nhập mới tính được lợi nhuận. **Xong — hiện để "Chờ nhập" vì chưa có bảng giá điện tử** | B | Xong |
| ✅ | 10. TASK-106 (MAJOR, D4/R4/B4) — Xử lý các trường hợp đặc biệt (hàng qua kho, đổi trả, NCC giao thẳng...) | Không phải đơn nào cũng tính bình thường, cần quy tắc riêng. **Xong — phần "gợi ý số tiền", chờ màn hình chọn tay ở giai đoạn sau** (xem "Có gì mới") | C | Xong |
| ✅ | 11. TASK-107 (MAJOR, D2/R4/B4) — Tính lợi nhuận (lợi nhuận thật và lợi nhuận tính KPI riêng) | Hai con số phục vụ hai mục đích khác nhau (kế toán vs. thưởng KPI) | B | **Xong phần lợi nhuận kế toán** — phần KPI chờ màn hình chọn tay |
| ✅ | 12a. TASK-108A-1 — Chọn tỷ lệ quy đổi (nhân viên + nhóm + nguồn đơn + loại hàng + ngày) | **Phần rủi ro cao nhất** — sai ở đây nghĩa là sai lương của ai đó | C | **Xong** — đã qua soát xét độc lập 4 vòng |
| ⬜ | 12b. TASK-108B — Quy đổi doanh thu theo 2 nhóm nguồn khách hàng | Cần lợi nhuận KPI, mà khoản đó còn thiếu định nghĩa | C | **Đang chờ** — thiếu định nghĩa `EligibleCosts` |
| ⬜ | 13. TASK-109 (MAJOR, D3/R4/B4) — Tổng hợp báo cáo theo tháng và theo năm, cho từng người | Ra được đúng bảng Summary như công ty đang cần | B | Sau bước 12 |
| 🔶 | 14. TASK-110 (MAJOR, D3/R3/B2) — Rà soát dữ liệu bất thường, đưa vào hàng chờ kiểm tra tay | Không để một dòng dữ liệu lỗi âm thầm làm sai cả báo cáo | B | **Soát xét vòng 1 (6 lỗi) và vòng 2 (4 lỗi) đều đã sửa xong; chờ vòng 3** — 16/17 điều kiện đạt, 1 điều kiện chờ file bán hàng thật |
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
