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
> Cập nhật lần cuối: 2026-08-27 — **bước 14: phần lõi khó nhất (bộ quy tắc
> mô tả dữ liệu) đã được soát xét độc lập DUYỆT và niêm phong. Toàn bộ công
> việc của bước 14 đã được nhập vào bản chính của dự án. Bước 14 vẫn CHƯA
> xong hẳn — còn chờ một lần đối chiếu trên file bán hàng thật.** (xem "Có gì
> mới" ngay bên dưới).

## Có gì mới — bước 14: phần lõi được duyệt và niêm phong, công việc đã nhập vào bản chính (2026-08-27)

**Ba việc vừa xảy ra.**

**1 — Phần lõi khó nhất đã được duyệt.** Sau tám vòng soát xét độc lập (bảy
vòng đầu đều bị trả về và đều đã sửa), vòng cuối cùng soát phần lõi — bộ quy
tắc quy định "một ô dữ liệu được phép mang hình dạng nào" — và **DUYỆT**: 0
lỗi chặn, 1 ghi chú nhỏ để làm sau. Phần này nay được **niêm phong**, nghĩa là
không ai được sửa nó nữa nếu không có quyết định mới của chủ dự án.

Cần nói rõ để không hiểu nhầm: **được duyệt phần lõi ≠ cả bước 14 được
duyệt.** Các phần còn lại của bước 14 vẫn chưa qua soát xét riêng.

**2 — Công việc đã được nhập vào bản chính.** Trước đây công việc của bước 14
nằm trên một nhánh làm việc tách rời khỏi bản chính của dự án, càng ngày càng
xa (24 lần lưu, hơn 40.000 dòng). Việc để như vậy có rủi ro làm trùng việc và
lạc mất công sức. Nay toàn bộ đã được nhập vào bản chính, **không mất một dòng
nào**. Cùng lúc đó, bộ quy tắc quản trị mới của dự án (phiên bản 4.1) cũng
được nhập vào.

**3 — Bước 14 vẫn CHƯA XONG.** Còn đúng một điều kiện chưa đạt: **đối chiếu
trên file bán hàng thật**. File thô đó không nằm trong dự án (đúng quy định
bảo mật dữ liệu) nên máy không tự chạy được — cần chủ dự án cung cấp. Chủ dự
án đã quyết định cho phép nhập công việc vào bản chính trước, rồi đối chiếu
sau; nhưng **bước 14 chỉ được đánh dấu XONG khi lần đối chiếu đó thật sự
chạy và khớp**. Không có chuyện tự đánh dấu đạt bằng dữ liệu giả.

**Việc tiếp theo của dự án — ĐÃ LÀM XONG PHẦN DỰNG (2026-08-27).** "Bộ ảnh
chuẩn" (Golden Baseline) đã được dựng: một bộ dữ liệu mẫu và kết quả đúng đã
biết, để mỗi lần sửa công cụ có thể so ngay xem có làm lệch kết quả cũ không.

Chủ dự án đã gửi hai file bán hàng thật của Tín Phát (tháng 01 và tháng
06/2026). Công cụ chạy trên đúng hai file đó và ra **chính xác 254 đơn** cho
tháng 1 và **146 đơn** cho tháng 6 — khớp tuyệt đối con số đã biết từ trước.
Tổng doanh số, tổng chiết khấu và tổng lợi nhuận cũng khớp tuyệt đối với dòng
"Tổng cộng" mà chính file gốc tự ghi.

**Hai file thật KHÔNG được đưa vào dự án.** Thay vào đó, máy tạo ra một bản
sao đã **xoá sạch thông tin khách hàng**: tên khách, số điện thoại, địa chỉ,
số máy, và toàn bộ phần ghi chú tự do đều bị bỏ hoặc thay bằng nhãn vô danh
kiểu "KHÁCH_0001". Đã kiểm lại từng chữ trong bản sao đó: **không còn một
thông tin khách hàng nào**. Mọi con số nghiệp vụ thì giữ nguyên — và điều đó
được chứng minh bằng cách chạy công cụ trên cả hai bản rồi so từng ô: kết quả
giống hệt nhau.

Từ nay, chỉ cần chạy **một lệnh duy nhất** là biết bản sửa mới có làm lệch kết
quả cũ hay không.

**Cập nhật (2026-08-27) — đã qua vòng soát xét độc lập, kết quả ĐẠT.** Vòng
soát xét độc lập (lần thứ hai, sau khi sửa một lỗi nhỏ về cách so sánh dữ
liệu môi trường bị lẫn vào dữ liệu nghiệp vụ) đã **DUYỆT**: 0 lỗi chặn. Chi
tiết ghi tại `docs/reviews/TASK-GOLDEN-BASELINE-001-INDEPENDENT-REVIEW-2.md`.

**Cập nhật (2026-08-27) — ĐÃ XONG (DONE).** Phiên "Freeze Finalization +
Controlled Integration" đã: (1) niêm phong bộ ảnh chuẩn này (`DEC-142`) — từ
nay không ai được sửa bộ dữ liệu mẫu/kết quả đúng này nữa nếu không có một
quyết định mới của chủ dự án; (2) nhập hẳn vào bản chính của dự án (không
còn nằm trên nhánh riêng); (3) chạy lại đúng lệnh kiểm tra trên bản chính và
ra đúng kết quả cũ — không có gì lệch. Bước 14 phần lõi (Golden Baseline) coi
như **hoàn tất**. Cùng lúc, **bộ quy tắc quản trị dự án phiên bản 4.1 chuyển
sang có hiệu lực đầy đủ** (trước đó mới chỉ "đã thông qua chính sách", giờ ba
cơ chế máy kiểm tra tự động đi kèm đã chứng minh chạy được trên bản chính).

**Việc còn lại của Track A không phải governance nữa.** Quyết định thứ nhất —
định nghĩa "chi phí đủ điều kiện" (`EligibleCosts`, mục C15) — **chủ dự án đã
trả lời ngày 2026-08-27** (DEC-143). Câu trả lời: **không khoản chi phí nào
được cộng thêm vào lợi nhuận tính KPI**, kể cả chi phí giao hàng. Nói cách
khác, lợi nhuận tính KPI = tiền bán − chiết khấu − tiền nhập, đúng như cách
công ty vẫn tính trong file Excel hiện tại; không thêm khoản nào mới.

Nhưng bước 12b **vẫn chưa chạy được**, và lý do bây giờ khác trước: không phải
thiếu quyết định nữa, mà **thiếu dữ liệu giá nhập**. Công cụ cần biết mỗi món
hàng nhập vào bao nhiêu tiền thì mới tính được lợi nhuận — hiện **100 % số
dòng đều để trống ô giá nhập**, vì chưa có bảng giá nào được nạp vào (bước 25
của lộ trình). Đây không phải lỗi của công cụ: chủ dự án đã yêu cầu để trống
chờ bảng giá (DEC-103).

Quyết định thứ hai — cách xử lý **điều chỉnh giá nhập** (`Qua kho`, `NCC giao`,
`KHBH`, `Thợ lắp`) — chủ dự án cũng **đã trả lời** ngày 2026-08-27 (DEC-144).
Câu trả lời: dòng nào **đã xác định** là không có điều chỉnh thì dùng thẳng giá
nhập kế toán; nhưng "chưa biết" thì **vẫn phải để trống**, không được coi là
"không có điều chỉnh". Đây là điểm tinh tế và quan trọng: *thiếu thông tin*
khác với *biết chắc là không có*.

**Ba câu hỏi đó chủ dự án đã trả lời ngày 2026-08-27 (DEC-145)** — nội dung
câu trả lời vẫn đúng: bảng giá ghi rõ ngày bắt đầu **và** ngày kết thúc, không
cho hai mức giá chồng lấn; tên hàng khớp sau khi bỏ qua khoảng trắng thừa và
hoa/thường (nhưng **không** bỏ dấu tiếng Việt, **không** đoán gần đúng); các
dòng phí thì giá nhập = 0.

**Nhưng ngay sau đó (cùng ngày, DEC-146), chủ dự án sửa lại một điểm quan
trọng hơn cả ba câu hỏi trên: giá nhập KHÔNG nằm trong một file cố định.** Giá
thay đổi liên tục trong ngày, và nơi lưu giá thật hiện tại là một cơ sở dữ
liệu vận hành (Firebase Realtime Database — RTDB), không phải một file Excel/
CSV Owner gõ tay một lần. Đây là thông tin mới, chưa từng xuất hiện ở bất kỳ
đâu trong hồ sơ dự án trước đó.

Điều này **không** làm hỏng ba câu trả lời ở trên — cách xác định "giá nào
đúng cho ngày nào" và "tên hàng khớp thế nào" vẫn giữ nguyên, chỉ là áp dụng
cho dữ liệu lấy từ RTDB thay vì từ file. Nhưng nó mở ra một câu hỏi quan trọng
hơn: **hệ thống RTDB hiện tại có lưu lại lịch sử giá theo thời gian không, hay
chỉ có giá hiện tại?** Nếu chỉ có giá hiện tại, công cụ sẽ gặp một vấn đề
nghiêm trọng: tính lại báo cáo tháng 1 vào một ngày bất kỳ sau này phải ra
đúng giá của tháng 1, không phải giá của ngày hôm tính lại — giống hệt nguyên
tắc công ty đã chốt cho tỉ lệ quy đổi (không được để chính sách sau này làm
đổi số liệu báo cáo cũ). Nếu RTDB không tự giữ lịch sử, công cụ cần thêm một
bước "chụp lại" giá định kỳ, có ghi ngày — việc này cần chủ dự án xác nhận
trước khi làm tiếp.

Một điểm phải nói thẳng: phần "dòng phí thì giá nhập = 0" **chưa làm được
ngay**. Chủ dự án đã yêu cầu công cụ dùng lại cách nhận diện dòng phí **có
sẵn** thay vì tự bịa ra cách mới — yêu cầu đúng. Nhưng kiểm tra lại thì cách
nhận diện có sẵn được xây cho việc **sắp xếp thứ tự đọc hàng chờ kiểm tra**,
không phải để quyết định tiền, và tài liệu của chính nó ghi rõ là **tạm thời,
cấm chỉnh sửa**. Dùng nó để định giá sẽ khiến sau này ai đó chỉnh cho hàng chờ
bớt ồn lại vô tình đổi lương. Đo thử trên dữ liệu thật: nó bắt **36 dòng**
trong khi đúng 3 nhóm chủ dự án nêu chỉ có **34** — dôi ra `Phụ Phí` và
`Phụ Phí Đổi mới`. Nên phần này tách riêng, chờ bước 3 của lộ trình
(`TASK-103` — phân loại dòng hàng) hoặc chờ chủ dự án cấp một danh sách liệt kê
rõ ràng.

**Cùng ngày đó, một phiên tiếp theo (DEC-147) đã mở chính kho mã của hệ thống
giá ra đọc, và bốn trong năm câu hỏi trên nay đã có câu trả lời — không còn
phải đoán.**

**Tin tốt: RTDB CÓ lưu lịch sử giá.** Có hẳn một nhánh riêng ghi lại từng lần
đổi giá kèm ngày (`phist`), và nó chỉ ghi khi giá thật sự đổi nên rất gọn. Hỏi
"ngày 10/01 giá là bao nhiêu" thì hệ thống trả lời được: lấy mốc gần nhất
trước hoặc bằng ngày đó. Nỗi lo lớn nhất ở đoạn trên — "chỉ có giá hiện tại" —
**không xảy ra**.

**Tin phải nói thẳng: loại giá có lịch sử lại không phải loại giá công cụ
cần.** Hệ thống giá đang giữ ba loại giá khác nhau về bản chất:

- **giá nhà cung cấp báo trong ngày** — đây là loại **có** lịch sử đầy đủ.
  Nhưng nó là *báo giá*, không phải số tiền công ty đã thật sự trả cho lô hàng.
  Một mã có thể có năm nhà cung cấp cùng báo giá trong cùng một ngày, và không
  chỗ nào ghi đơn hàng cụ thể đã mua của ai;
- **giá thực nhập trung bình** của hàng đang nằm trong kho — gần nghĩa kế toán
  nhất, nhưng **không có lịch sử**: chỉ giữ đúng hai bản (hôm qua và hôm nay),
  bản mới ghi đè bản cũ;
- **giá lô** — tiền thật của lần nhập gần nhất, nhân viên gõ tay, cũng **không
  có lịch sử**.

Nói gọn: đây **không** phải lỗi kiến trúc như đã lo, mà là **chọn nhầm nguồn
nếu vội**. Lấy loại đầu tiên chỉ vì nó dễ lấy và có sẵn lịch sử là đúng cái bẫy
mà quy tắc "không được thấy một cột tên là *giá* rồi mặc định đó là giá nhập"
tồn tại để chặn.

Ba điều nữa tìm ra trong lượt đọc mã, đều ảnh hưởng trực tiếp tới con số:

- **Hệ thống giá lưu tiền theo đơn vị NGHÌN đồng** (5.200 nghĩa là 5,2 triệu),
  còn công cụ báo cáo lưu theo đồng nguyên. Sai chỗ này là sai đúng 1.000 lần,
  và sai *đều* nên nhìn bảng không phát hiện ra.
- **Số 0 trong lịch sử giá nghĩa là "hết hàng", không phải "giá bằng 0".** Đọc
  nhầm là biến một mã hết hàng thành lãi bằng đúng giá bán.
- **Lịch sử giá sửa được.** Có bốn thao tác bình thường trong app (xoá mốc từ
  một ngày, đổi mã hàng, gộp hai mã, khôi phục bảng cũ) làm lịch sử thay đổi
  hoặc lệch đi. Nghĩa là in lại cùng một báo cáo hai lần vẫn có thể ra hai số —
  đúng điều công ty đã chốt là không được phép. Vì vậy công cụ phải **tự chụp
  và đóng băng** dữ liệu đã dùng, chứ không đọc thẳng.

**Hướng đi đề xuất:** thêm một bước "chụp giá định kỳ" ghi lại thành một bản
lưu **không sửa được**, rồi công cụ báo cáo đọc bản lưu đó theo đúng định dạng
4 cột đã chốt. Cách này giữ hai hệ thống tách rời, không hệ nào phụ thuộc mã
nguồn của hệ nào.

**Việc còn lại cần chủ dự án — năm câu hỏi mới** (thay năm câu cũ, đã trả lời
được 4/5 bằng chính mã nguồn):

1. **Giá nhập kế toán là loại nào trong ba loại trên?** Đây là câu hỏi chính,
   và không ai ngoài chủ dự án trả lời được.
2. Nếu chọn "giá nhà cung cấp báo": một mã có nhiều nhà cung cấp cùng ngày thì
   lấy của ai — rẻ nhất, hay nhà cung cấp đã thật sự mua?
3. Chấp nhận độ chính xác **theo ngày** không? (giá đổi nhiều lần trong ngày
   thì chỉ giữ lần cuối trong ngày)
4. Đồng ý làm bước "chụp giá đóng băng" không, và bao lâu chụp một lần?
5. Dữ liệu lịch sử hiện có từ ngày nào? — cái này phải mở dữ liệu thật ra xem,
   đọc mã không trả lời được.

*(Năm câu hỏi trên — SUPERSEDED. Chủ dự án đã trả lời trực tiếp câu 1, và
làm câu 4 không còn cần thiết trong giai đoạn đầu. Xem đoạn "Chủ dự án đã
quyết định" ngay dưới đây. Giữ lại nguyên văn làm bản ghi lịch sử.)*

---

**Chủ dự án đã quyết định (cùng ngày, một phiên nữa sau đó).** Câu trả lời
cho câu hỏi 1 ở trên: **KHÔNG dùng "giá vốn rẻ nhất" (Min) hiện đang hiển
thị trên bảng, và KHÔNG cần chụp giá nhập kho làm lịch sử ngay bây giờ.**

Thay vào đó, công cụ dùng đúng **một** nguồn đã có sẵn: **lịch sử giá nhà
cung cấp** (loại đầu tiên trong ba loại kể trên). Cách tính: với mỗi đơn
hàng bán ra ngày D, lấy giá của TỪNG nhà cung cấp tại đúng ngày đó (mốc gần
nhất không sau ngày D), rồi lấy giá THẤP NHẤT trong số đó làm giá nhập.

Mã hàng nào không đủ dữ liệu để tính (ví dụ mã lạ, chưa nhà cung cấp nào
từng báo giá) thì để **trống, chờ xử lý tay** — không đoán, không lấy giá
hôm nay áp cho quá khứ. Chủ dự án xác nhận đây là lựa chọn có cân nhắc:
số trường hợp trống dự kiến ít, và xử lý tay từng trường hợp đó **rẻ hơn**
nhiều so với việc xây hẳn một hệ thống "chụp giá đóng băng" như câu hỏi 4
từng đặt ra — nên bước đó **không còn bắt buộc** ở giai đoạn này.

Điều này cũng làm rõ một thắc mắc còn treo: cái vòng tròn/popup "Lịch sử
giá" bấm được ngay trên ô Min của bảng — kiểm tra kỹ thì nó **chỉ** vẽ lại
giá của từng nhà cung cấp theo ngày (đúng loại giá công cụ vừa chọn dùng),
**không** phải lịch sử của số Min đang hiển thị. May mắn là đây đúng là
nguồn công cụ cần, chỉ là tên gọi trên màn hình dễ gây hiểu lầm.

**Còn hai câu hỏi kỹ thuật nhỏ, không cản việc bắt đầu làm:** nếu một nhà
cung cấp đã "nghỉ bán" hoặc bị đánh dấu "không tính vào giá Min" ở thời
điểm HIỆN TẠI, giá họ từng báo trong QUÁ KHỨ có tính hay không; và một luật
lọc giá bất thường mới thêm gần đây có nên áp ngược cho các mốc giá cũ hơn
hay không. Cả hai chưa có câu trả lời, nhưng công cụ vẫn làm được — dùng
tạm cách an toàn nhất (không lọc gì, tính hết) cho tới khi có câu trả lời.

Bốn cột file giá cũ (tên hàng / ngày bắt đầu / ngày kết thúc / giá nhập)
**vẫn đúng làm định dạng dự phòng** (nạp dữ liệu ban đầu, hoặc dữ liệu mẫu
kiểm thử) — nhưng **không còn là con đường chính** để lấy giá nhập nữa,
vì lịch sử giá nhà cung cấp đã có sẵn, không cần chờ ai gõ file.

*(Ba câu hỏi gốc và bảng 4 cột giữ lại bên dưới làm bản ghi lịch sử — nội dung
câu trả lời vẫn đúng, chỉ thay đổi ở chỗ dữ liệu lấy từ đâu.)*

- **Q1.** Trong bảng giá, mỗi dòng có ghi **ngày kết thúc** hiệu lực không? Nếu
  chỉ ghi ngày bắt đầu, hai mức giá của cùng một món sẽ cùng có hiệu lực và
  công cụ **không được phép tự đoán** nên lấy mức nào. (Đề xuất: ghi cả ngày
  kết thúc — rõ ràng nhất.)
- **Q2.** Tên hàng trong bảng giá phải khớp **chính xác từng ký tự** với file
  bán hàng, hay cho phép bỏ qua khoảng trắng thừa và hoa/thường? Kiểm tra trên
  dữ liệu thật: **15 tên hàng có khoảng trắng thừa**, và có **một cặp tên chỉ
  khác nhau đúng một dấu cách ở cuối**. Nếu bắt khớp chính xác, những dòng đó
  sẽ **âm thầm không tra được giá**.
- **Q3.** Các dòng không phải hàng hoá — `Chi phí vận chuyển`, `Chi phí lắp
  đặt`, `Chênh VAT` (khoảng **1.250 dòng trong 6 tháng**) — có giá nhập không?
  Phần mềm kế toán đang ghi lợi nhuận của chúng bằng đúng doanh số, tức giá
  nhập = 0. Nhưng công cụ **không được tự suy ra điều đó**. Nếu bảng giá bỏ sót
  nhóm này, lợi nhuận của **cả tháng sẽ không bao giờ tính xong**.

**File giá cần đúng 4 cột** (đơn vị **VND nguyên**, ví dụ `8000000` = tám
triệu): tên hàng (chép nguyên văn cột `Tên hàng trên chứng từ`), ngày bắt đầu,
ngày kết thúc, giá nhập. Không cần thêm gì khác. Bảng chi tiết:
`docs/tasks/TASK-108B-eligible-costs-owner-definition.md` Phần III mục 29.

**Và một việc độc lập:** cấp file bán hàng thô toàn công ty 6 tháng để đối
chiếu bước 14's `CHECK-110-16` (bộ dữ liệu toàn công ty, không chỉ Tín Phát).

## Có gì mới trước đó — bước 14 qua vòng soát xét thứ tư, bị trả 2 lỗi, đã sửa (2026-08-23)

**Cả 2 lỗi đều là cùng một chuyện: cảnh báo chỉ sai người.** Công cụ kết luận
đúng là "có vấn đề", nhưng khi liệt kê **dòng nào** gây ra vấn đề thì nó vơ cả
những dòng không liên quan.

1. **Cảnh báo "một tên khớp hai nhân viên"** đã ghi đúng số dòng ở vòng trước,
   nhưng phần liệt kê **cách viết tên** vẫn kéo cả dòng không dính dáng —
   dòng 6 có vấn đề, mà bảng chứng cứ ghi "dòng 6, 7".
2. **Cảnh báo "tên lạ bán nhiều hàng"** đếm đúng 1 dòng chưa nhận diện được,
   nhưng lại liệt kê thêm một dòng **đã nhận diện bình thường** chỉ vì trùng
   tên. Người duyệt mở ra sẽ thấy một dòng hoàn toàn hợp lệ và mất niềm tin
   vào cả hàng chờ.

**Lần này tôi sửa gốc, không vá từng chỗ.** Vòng trước tôi sửa đúng một ô
("số dòng") và tưởng xong, nhưng ô bên cạnh ("cách viết tên") vẫn đi qua đường
cũ. Nay mỗi cảnh báo **mang theo đúng tập dòng đã sinh ra nó**, và mọi thông
tin chứng cứ đều tính ra từ tập đó. Đường tra cứu cũ — "lấy tất cả dòng trùng
tên" — đã bị **xóa hẳn**, nên lỗi này không còn chỗ để tái phát ở ô tiếp theo.

**Sếp quyết thêm một việc:** cảnh báo "một tên khớp hai nhân viên" **chỉ được
phát khi dòng có ngày**. Không có ngày thì không biết dòng thuộc thời kỳ nào,
mà hai người bàn giao cho nhau (người cũ nghỉ, người mới vào) vốn **không hề**
trùng thời gian — coi họ là "cùng lúc" chỉ vì thiếu ngày là dựng chuyện. Dòng
đó vẫn được báo ở loại "thiếu ngày", và đó mới là việc cần sửa.

**Không đổi cách tính tiền, không đổi ai nhận doanh số. Vẫn chưa gộp vào nhánh
chính, và chưa vòng soát xét nào duyệt.**

## Ghi chép cũ (đã bị mục trên thay thế) — bước 14 qua vòng soát xét thứ ba (2026-08-23)

> Đây là bản ghi của một mốc đã qua trong cùng ngày. Trạng thái hiện tại
> nằm ở mục "Có gì mới" đầu file.

**Cả 3 lỗi đều cùng một dạng: kết luận đúng nhưng bằng chứng kèm theo sai.**
Với một hàng chờ để người duyệt kiểm tay, bằng chứng **chính là** sản phẩm —
một cảnh báo mà người duyệt không lần lại được thì gần như vô dụng, dù kết
luận của nó đúng.

1. **Cảnh báo "một tên khớp hai nhân viên" đánh dấu nhầm cả những dòng không
   liên quan.** Ví dụ thật: dòng ngày 10/02 rơi đúng vào khoảng thời gian hai
   nhân viên cùng hiệu lực → đúng là mập mờ. Nhưng dòng ngày 10/05 thì chỉ còn
   một người hiệu lực → hoàn toàn rõ ràng. Công cụ trước đây đánh dấu **cả
   hai**. Nay chỉ đánh dấu dòng thật sự mập mờ, và ghi kèm **ngày của dòng đó**
   cùng **danh sách bản ghi nhân viên bị đụng nhau**.
2. **Cảnh báo "nhân viên đã nghỉ mà vẫn có đơn" phát cả khi dòng không có
   ngày.** Không có ngày thì **không đủ căn cứ** để biết dòng đó thuộc thời kỳ
   nào — phát cảnh báo lúc đó là dựng một cáo buộc từ một ẩn số, về master data
   của một người thật. Sếp đã quyết: **không phát**. Dòng đó vẫn được báo ở
   loại "thiếu ngày" — và đó mới là việc cần sửa trước; sửa xong thì lần nạp
   sau cảnh báo kia tự trả lời được.
3. **Cảnh báo "tên lạ bán nhiều hàng" làm mất cách viết gốc.** `"Thảo Linh"`
   viết một dấu cách, hai dấu cách, hay gõ dấu kiểu khác đều quy về **một**
   người — gom nhóm như vậy là đúng. Nhưng công cụ vứt luôn bản gốc, nên người
   duyệt không còn thấy dữ liệu thật sự được nhập thế nào. Nay giữ **đủ mọi
   cách viết gốc** kèm dòng của từng cách.

**Không đổi cách tính tiền, không đổi ai nhận doanh số. Vẫn chưa gộp vào nhánh
chính.**

## Ghi chép cũ (đã bị mục trên thay thế) — bước 14 qua vòng soát xét thứ hai (2026-08-23)

> Đây là bản ghi của một mốc đã qua trong cùng ngày. Trạng thái hiện tại
> nằm ở mục "Có gì mới" đầu file.

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
| ⬜ | 11b. TASK-105C — Đọc giá nhập (từ lịch sử giá NCC) | Không có giá nhập thì không tính được lợi nhuận; đây là nút thắt duy nhất còn lại | C | **Chủ dự án đã chốt nguồn** (đoạn "Chủ dự án đã quyết định" ở trên): lấy giá thấp nhất trong lịch sử báo giá nhà cung cấp tại đúng ngày bán, mã thiếu căn cứ để trống chờ xử lý tay. Kỹ thuật đã sẵn sàng để bắt đầu; còn hai câu hỏi nhỏ (NCC nghỉ bán tính hồi tố không, lọc giá bất thường hồi tố không) không cản việc làm — dùng cách an toàn nhất trong lúc chờ |
| ⬜ | 11c. TASK-105B-Q3 — Dòng phí (vận chuyển/lắp đặt/VAT) tính giá nhập = 0 | Không có bước này thì lợi nhuận cả tháng không tính xong | C | **Chờ bước 3 (`TASK-103` phân loại dòng hàng)** hoặc danh sách liệt kê rõ ràng từ chủ dự án — không liên quan tới câu hỏi RTDB |
| ⬜ | 12b. TASK-108B — Quy đổi doanh thu theo 2 nhóm nguồn khách hàng | Cần lợi nhuận KPI | C | **Định nghĩa đã xong hoàn toàn** (chủ dự án duyệt 2026-08-27, DEC-143 + DEC-144) — **chờ đúng một thứ: bảng giá nhập** (bước 11b) |
| ⬜ | 13. TASK-109 (MAJOR, D3/R4/B4) — Tổng hợp báo cáo theo tháng và theo năm, cho từng người | Ra được đúng bảng Summary như công ty đang cần | B | Sau bước 12 |
| 🔶 | 14. TASK-110 (MAJOR, D3/R3/B2) — Rà soát dữ liệu bất thường, đưa vào hàng chờ kiểm tra tay | Không để một dòng dữ liệu lỗi âm thầm làm sai cả báo cáo | B | **Đã nhập vào bản chính; phần lõi được soát xét độc lập DUYỆT và niêm phong (vòng 8 vòng). CHƯA XONG** — 21/22 điều kiện đạt, 1 điều kiện còn lại là đối chiếu trên file bán hàng thật, chờ chủ dự án cung cấp file |
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
