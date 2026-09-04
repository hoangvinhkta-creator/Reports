# PHB-03 — SOÁT XÉT ĐỘC LẬP LẦN 2 (sau bản sửa ngữ nghĩa nghiệp vụ có ranh giới)

**Loại:** Independent Re-Review · chỉ đọc · **không sửa code, không deploy, không merge**
**Ngày:** 2026-09-04
**Nhánh được soát:** `claude/phb-03-bounded-semantics-repair-685gf4`
**Mã bản dựng (HEAD):** `d066d227da852b17a57d4a8492fa79c7fc7b2aff`
**Nền so sánh (bản trước khi sửa):** `60adb2ec22efdb4967d6971bbee852db660c8c18`
**Cổng xác minh mục tiêu:** **ĐẠT** — đúng mã bản dựng yêu cầu, cây làm việc sạch.

> Ghi chú kỹ thuật nhỏ, không ảnh hưởng kết luận: phiên soát xét này đứng trên
> nhánh `claude/phb-03-bounded-semantics-review-p489lh`, và nhánh đó trỏ vào
> **đúng cùng một mã bản dựng** `d066d22` — đã kiểm bằng `git diff` giữa hai
> nhánh và kết quả là **không có một khác biệt nào**. Nói cách khác: nội dung
> được soát đúng là nội dung được yêu cầu soát.

---

## 1. Kết luận ngắn gọn

**ĐẠT (PASS).** Bản sửa làm đúng điều quan trọng nhất: nó tách **hai câu hỏi
khác nhau** mà trước đây bị trộn làm một.

| Câu hỏi | Trước bản sửa | Sau bản sửa |
|---|---|---|
| "Dòng hàng này có tính được lợi nhuận không?" | Phụ thuộc vào một **cái nhãn** mà máy đóng lúc nạp sổ | Phụ thuộc vào **con số kinh tế thật**: có giá bán, có số lượng dương, có giá vốn, và bảng thẩm quyền chi phí đọc được |
| "Lợi nhuận đó cộng cho nhân viên nào?" | Không trả lời được thì **mất luôn** lợi nhuận | Không trả lời được thì lợi nhuận **vẫn vào tổng của kỳ**, chỉ chưa cộng cho ai |

Cả 4 vấn đề nghiệp vụ B01–B04 đều đã được sửa thật, và tôi đã tự kiểm chứng
bằng cách chạy lại hệ thống chứ không chỉ đọc code hay tin vào báo cáo.

**Không có phát hiện nào ở mức chặn (blocking).** Có 6 điểm ghi nhận ở mức
không chặn, liệt kê ở mục 12 — không điểm nào làm sai một con số nào.

**Không còn câu hỏi nào chờ chủ dự án quyết.** Bản triển khai có để lại đúng
một câu hỏi mở ("dòng số lượng âm có vào tổng công ty không?"), và quyết định
`OD-2` mà chủ dự án vừa đóng băng đã trả lời đúng theo hướng mà bản sửa đang
làm — nên không phải sửa gì thêm.

---

## 2. Giá vốn nhập tay đã hoạt động thật chưa?

**RỒI. Đây là thay đổi quan trọng nhất của bản sửa.**

### Trước đây hỏng ở đâu — nói bằng ví dụ

Hình dung một dòng hàng: **tủ lạnh, bán 8.000.000, máy không tra ra giá nhập.**

1. Máy tra giá nhập → không ra → máy **đóng dấu "cần kiểm tra"** lên dòng đó và
   ghi dấu đó xuống cơ sở dữ liệu.
2. Chủ dự án mở màn hình, gõ giá nhập 6.000.000, bấm LƯU. Giá được lưu đúng.
3. Nhưng khi tính lợi nhuận, hệ thống **nhìn lại cái dấu "cần kiểm tra"** đã
   đóng từ bước 1 — cái dấu đó không bao giờ được đóng lại — và loại dòng đó ra.

Kết quả: **đúng những dòng mà tính năng nhập giá tay sinh ra để cứu, tính năng
đó không bao giờ cứu được.** Chủ dự án gõ giá xong, bấm LƯU thành công, và con
số lợi nhuận **không nhúc nhích**. Đó là một vòng tự khoá.

### Nay đã khác

Tôi đã tự chạy lại đúng kịch bản đó trên hệ thống thật:

| Bước | Kết quả tôi đo được |
|---|---|
| Dòng do máy nạp, chưa tra ra giá nhập | Lợi nhuận = *chưa xác định*; lý do hiện đúng một câu: **"Chưa có giá nhập — Owner nhập được ngay tại đây"** |
| Chủ dự án gõ 6.000.000 và bấm LƯU | Lợi nhuận **lập tức** = 2.000.000 (8.000.000 − 6.000.000) |
| Nguồn giá được ghi lại | **"Owner đã nhập"** — không bị báo nhầm thành giá máy tự tra |
| Có phải nạp lại sổ không? | **KHÔNG.** Con số mới có ngay trên chính trang đó |
| Cái dấu "cần kiểm tra" cũ | **Vẫn còn nguyên** trong lịch sử — không ai viết lại quá khứ; nó chỉ thôi làm luật |

### Sửa một giá máy đã tự tra được không?

**Được.** Tôi đã kiểm: khi chủ dự án sửa đè lên một giá máy tự tra, hệ thống ghi
nguồn giá là **"Owner đã sửa đè"** và tính lại ngay. Kể cả khi chủ dự án gõ vào
**đúng bằng** con số máy đã tra, hệ thống **vẫn** ghi là "Owner đã sửa đè" —
đúng như quy định: một quyết định của con người không được xoá dấu vết.

**B01 = ĐẠT.**

---

## 3. Một dòng "cần kiểm tra" còn bị loại lợi nhuận oan không?

**KHÔNG CÒN.**

Bản kiểm tra 19 mã lý do trước đó đã đếm hết: **không mã nào** trong số đó là
một lý do kinh tế khiến không tính được lợi nhuận, một khi đã có giá bán, số
lượng và giá vốn. Chúng chỉ là **ghi chú của máy khi nạp sổ**.

Nay hệ thống hỏi đúng bốn câu về **chính dòng hàng**, và mỗi câu trả lời "không"
có một cái tên mà chủ dự án đọc được:

1. Có giá bán không?
2. Có số lượng, và số lượng có lớn hơn 0 không?
3. Có giá vốn hiệu lực không? (máy tra ra · chủ dự án nhập · chủ dự án sửa đè —
   cả ba đều được tính)
4. Bảng thẩm quyền chi phí KPI có đọc được không?

**Không câu nào hỏi tới cái nhãn "cần kiểm tra".** Điều này không chỉ là lời
hứa: có một bài kiểm tra tự động **đọc thẳng mã nguồn** và bắt lỗi ngay nếu ai
đó vô tình đưa cái nhãn đó quay lại làm luật.

Tôi cũng đã kiểm trường hợp cụ thể: một dòng mang cả ba ghi chú
"OrderInconsistency · EmployeeMapping · Suspicious.ERP" mà **có đủ** giá bán,
số lượng và giá vốn → **lợi nhuận vẫn được tính bình thường**, và các ghi chú
đó vẫn hiện nguyên văn ở cột Ghi chú để chủ dự án xem.

### Cái van an toàn có bị nới lỏng theo không?

**Không — và đây là điểm tôi soi kỹ nhất.**

Có một cái van đã được quy định từ trước: khi **file cấu hình thẩm quyền chi phí
KPI bị hỏng**, hệ thống phải **từ chối ra số cho mọi dòng** — thà không ra số
còn hơn ra số sai. Rủi ro của bản sửa này là: nới cửa chặn lợi nhuận ra rồi thì
những dòng có giá nhập tay sẽ **đi vòng qua cái van đó** và vẫn ra số trong lúc
cấu hình đang hỏng.

Tôi đã dựng một file cấu hình hỏng thật rồi chạy qua đúng đường mà hệ thống thật
đi. Kết quả:

- Dòng có giá nhập tay: **vẫn không ra số**.
- Lý do hiện ra: *"Bảng thẩm quyền chi phí KPI đang hỏng — hệ thống từ chối ra
  số cho MỌI dòng cho tới khi người quản trị sửa file cấu hình"*.
- Và dòng đó **không** bị đếm nhầm vào nhóm "gõ giá là xong" — vì gõ giá không
  cứu được nó.

**Van an toàn = ĐẠT.** Giá nhập tay **không** đi vòng qua nó được.

---

## 4. Số lượng 0 và số lượng âm hoạt động ra sao?

### Số lượng bằng 0 (quyết định OD-1)

Ví dụ thật từ dữ liệu golden: `BTL00300`, *Máy Giặt Panasonic*, số lượng **0**,
đơn giá 6.200.000.

| Câu hỏi | Hệ thống làm gì |
|---|---|
| Có ghi lợi nhuận = 0 không? | **KHÔNG.** Ô lợi nhuận hiện dấu `—` |
| Vì sao không ghi 0? | Vì một số `0` bịa ra **nguy hiểm hơn một ô trống** — nó trông như đã tính xong rồi |
| Chủ dự án đọc được lý do gì? | *"Số lượng bằng 0 — đây là dữ liệu chưa đủ tin, không phải lãi 0 đồng. Cần sửa số lượng trên sổ gốc"* |
| Có bị hứa "nhập giá là xong" không? | **KHÔNG.** Dòng này nằm ngoài nhóm "gõ giá là xong" |
| Có chặn con số "chính thức" của cả kỳ không? | **CÓ** — đúng như yêu cầu |

### Số lượng âm (quyết định OD-2 — nay đã đóng băng)

Chủ dự án đã quyết: đây là **dữ liệu nghiệp vụ chưa giải quyết**; cần xem lại;
**không** cộng vào lợi nhuận công ty/kỳ; **không** cộng vào KPI nhân viên;
**không** tự diễn giải thành trả hàng/hoàn tiền.

Tôi đã kiểm và **bản sửa làm đúng cả bốn vế**:

- Dòng số lượng âm → lợi nhuận = *chưa xác định*, **không** vào tổng công ty.
- **Không** vào KPI của bất kỳ nhân viên nào.
- Lý do hiện ra: *"Số lượng âm — cần xem lại. Chưa có quy tắc nào của Owner nói
  dấu âm nghĩa là gì, nên hệ thống không tự diễn giải"*.
- **Không có** hệ thống trả hàng/hoàn tiền nào được dựng lên trong bản sửa này.
- Dòng đó **chặn** con số "chính thức" của kỳ — đúng yêu cầu.
- Gõ giá nhập vào **cũng không cứu được** dòng đó, và màn hình không hứa như vậy.

Bản triển khai từng để lại đây một câu hỏi mở cho chủ dự án. **Quyết định OD-2
đã trả lời đúng theo hướng bản sửa đang làm** — nên **không còn câu hỏi nào chờ
quyết**, và không cần sửa thêm dòng nào.

**Một điểm nhỏ tôi ghi nhận (không chặn):** dòng số lượng âm **vẫn được cộng vào
cột Doanh thu bán hàng** (vì doanh thu lấy đúng con số kế toán đã ghi). Quyết
định `OD-2` chỉ nói về **lợi nhuận** và **KPI**, không nói về doanh thu, nên bản
sửa không tự quyết thay. Dòng đó **không bị giấu**: nó hiện cảnh báo "cần xem
lại" và nó kéo kỳ xuống trạng thái CHƯA HOÀN CHỈNH. Nếu sau này chủ dự án muốn
doanh thu cũng loại nó ra, đó là một quyết định mới, rất nhỏ.

---

## 5. Dòng nghi trùng hoạt động ra sao?

**Chỉ cảnh báo, không loại (quyết định OD-3). ĐẠT.**

### Cái sai cũ, nói bằng ví dụ

Giả sử kế toán gõ nhầm cùng một đơn hai lần. Hệ thống cũ xử lý **mâu thuẫn với
chính nó**:

- **Doanh thu:** cộng **cả hai** dòng → doanh thu bị đếm đúp mà không ai chặn.
- **Lợi nhuận:** bỏ **cả hai** dòng → mất lợi nhuận của cả dòng thật lẫn dòng
  trùng.

Không có cách đọc nào khiến hành vi đó là đúng: nếu đúng là trùng thì doanh thu
đã sai; nếu không trùng thì lợi nhuận đang bị loại oan.

### Nay

Tôi đã dựng đúng tình huống hai dòng, một dòng bị máy đánh dấu nghi trùng:

- Doanh thu: **16.000.000** (cả hai dòng) ✓
- Lợi nhuận: **6.000.000** (cả hai dòng) ✓ — hết mâu thuẫn
- Kỳ vẫn đạt trạng thái **CHÍNH THỨC**
- Đúng **một** dòng mang cảnh báo: *"Sổ có một dòng khác giống hệt dòng này.
  Doanh thu và lợi nhuận VẪN được tính — nếu đây thật sự là gõ nhầm hai lần thì
  cần sửa trên sổ gốc"*

Doanh thu và lợi nhuận nay dùng **cùng một luật gộp**. Và không có hệ thống chống
trùng tổng quát nào được mở ra — đúng phạm vi.

---

## 6. Giá bán 0 hoạt động ra sao?

**Tính đúng phép trừ, ra số âm thật. ĐẠT.**

Vector nguyên văn của chủ dự án:

```
số lượng   = 1
giá bán    = 0
giá nhập   = 500.000
```

Kết quả tôi đo được trên hệ thống: **lợi nhuận = −500.000** ✓

Kèm ba cảnh báo, không cảnh báo nào chặn con số:

- *"Giá bán bằng 0 (thường là hàng tặng kèm). Lợi nhuận vẫn được tính đúng theo
  phép trừ, nên nó có thể ra số âm"*
- *"Giá nhập cao hơn giá bán — dòng này đang bán lỗ"*
- *"Lợi nhuận của dòng này là số âm"*

Cách nghĩ đúng ở đây: **`0` là một giá bán THẬT** (hàng tặng kèm), không phải một
ô trống. Khoản 500.000 kia là chi phí doanh nghiệp thật sự chịu. Đổi nó thành `0`
là làm báo cáo **đẹp hơn sự thật**.

Và: hệ thống **không** chặn dòng chỉ vì giá bán bằng 0.

---

## 7. Chưa xác định nhân viên và việc gán lại hoạt động ra sao?

**ĐẠT trọn vẹn.** Tôi đã đi hết vòng qua giao diện web thật, không chỉ qua code.

### Trước khi gán

| Điều cần đúng | Kết quả đo được |
|---|---|
| Lợi nhuận của dòng chưa rõ nhân viên có vào tổng kỳ không? | **CÓ** — 3.000.000 vẫn nằm trong tổng 6.000.000 của kỳ |
| Có bị cộng cho nhân viên nào không? | **KHÔNG** |
| Chủ dự án có nhìn thấy nó không? | **CÓ** — trang tổng quan tách rõ hai ô: *"Đã cộng cho nhân viên"* và *"Chưa xác định nhân viên · 1 dòng chưa gán"* |
| Hai ô đó cộng lại có bằng tổng không? | **CÓ, luôn luôn** — không đồng nào biến mất không dấu vết |
| Có mở ra xem được những dòng đang treo không? | **CÓ** — "Chưa xác định nhân viên" là một mục trong bộ chọn nhân viên như mọi người khác |

### Sau khi chủ dự án chọn nhân viên và bấm LƯU

| Điều cần đúng | Kết quả đo được |
|---|---|
| Có phải nạp lại sổ không? | **KHÔNG** |
| Nhóm "chưa xác định" có giảm không? | **CÓ** — về 0, và khối tách đôi tự biến mất khỏi trang |
| Dòng có hiện trong trang của người được chọn không? | **CÓ** — trang của "Vinh": 1 dòng, lợi nhuận 3.000.000 |
| Tổng lợi nhuận cả kỳ có đổi không? | **KHÔNG** — vẫn đúng 6.000.000. Thao tác này chỉ **dời** một khoản, không tạo ra và không làm mất tiền |
| Tên mà **sổ gốc** ghi có bị xoá không? | **KHÔNG** — được giữ nguyên bên cạnh, và hiện trong ô chú thích *"Sổ ghi: …"* trên chính dòng đó |

### Gỡ được không? Gán bừa được không?

- **Gỡ được.** Có nút GỠ NV; sau khi gỡ, dòng trở về đúng tên mà sổ ghi. Một lần
  gán nhầm **không** mắc kẹt vĩnh viễn.
- **Không gán bừa được.** Tên phải nằm trong danh sách nhân viên chính thức. Tôi
  đã thử gửi lên một cái tên bịa ("Người Lạ") → hệ thống **từ chối** và **không
  ghi gì** vào cơ sở dữ liệu.
- **Nhân viên đã nghỉ không gán được.** Tôi đã tự thêm một nhân viên
  `active: false` vào danh sách rồi kiểm lại → người đó **không xuất hiện** trong
  ô chọn. Gán việc mới cho người đã nghỉ là một quyết định nhân sự, không phải
  một lần sửa dữ liệu.
- **Danh sách nhân viên hỏng → không gán được gì cả** (chứ không đoán mò một
  danh sách nào khác). Tôi đã kiểm bằng một file hỏng thật.
- **Dòng không tồn tại → từ chối.** Gửi lên một mã đơn bịa → hệ thống trả lỗi
  404 và không ghi gì.

### Bằng chứng kế toán gốc

**Được giữ nguyên vẹn.** Bảng ghi kết quả của máy là loại **chỉ-thêm-không-sửa**;
việc gán nhân viên được lưu ở **một bảng riêng** và chỉ được hợp nhất **lúc đọc**.
Nên "sổ ghi ai" và "chủ dự án quyết là ai" không bao giờ bị trộn thành một con số
không nhãn. Có bài kiểm tra tự động **đọc thẳng mã nguồn** để canh ranh giới này.

---

## 8. Bảng kê chi tiết có đúng kiểu "trang tính" không?

**CÓ — và quan trọng hơn: nó dừng đúng chỗ, không biến thành một Excel trong
trình duyệt.**

| Yêu cầu | Kết quả |
|---|---|
| Ô **sửa được**: giá nhập | ✓ ngay trên dòng |
| Ô **sửa được**: nhân viên | ✓ ngay trên dòng |
| Ô **suy ra** (chỉ đọc): doanh thu · lợi nhuận KPI · DS quy đổi | ✓ |
| Gõ thẳng lợi nhuận được không? | **KHÔNG** — tôi đã kiểm bằng cách liệt kê **toàn bộ** ô nhập mà trang gửi lên máy chủ: chỉ có đúng giá nhập và nhân viên, không có ô nào cho lợi nhuận / doanh thu / DS quy đổi |
| Gõ thẳng DS quy đổi được không? | **KHÔNG** |
| Lưu giá nhập xong có tự tính lại không? | **CÓ.** Tôi đo: trước khi lưu, lợi nhuận `—`; sau khi lưu 6.000.000 → lợi nhuận **2.000.000**, DS quy đổi **100.000.000** |
| Có bước "bấm nút tính" riêng không? | **KHÔNG** — cùng một trang, sau khi lưu đã là số mới |
| Lưu nhân viên xong báo cáo nhân viên có cập nhật không? | **CÓ** (mục 7) |
| Thiếu dữ liệu thì hiện gì? | Dấu **`—` kèm lý do ngay trên dòng đó**, **không bao giờ** bịa ra số `0` |
| Doanh thu có bị thay bằng "số lượng × đơn giá" tính lại không? | **KHÔNG.** Lấy đúng con số kế toán đã ghi khi nạp sổ. Trang nói rõ điều này bằng một câu ngay dưới tiêu đề |

Bảng còn có **ba bộ lọc**, mỗi bộ trả lời một câu khác nhau của chủ dự án —
*chưa có giá nhập* · *chưa xác định nhân viên* · *tất cả dòng* — thay vì gộp
thành một danh sách "còn thiếu" chung chung.

**Không có** máy trang tính tổng quát nào được dựng lên. Đúng phạm vi.

---

## 9. Coverage có nói đúng cho chủ dự án phải sửa gì không?

**CÓ. Đây là chỗ bản sửa thay đổi rõ nhất về mặt "đọc là hiểu".**

### Cái sai cũ

Màn hình cũ có hai ô đếm:

1. *"… dòng chưa có giá nhập"* — ô này **luôn bằng 0**, không phải vì mọi dòng
   đã đủ giá, mà vì **định nghĩa của nó tự mâu thuẫn**: nó chỉ đếm những dòng
   "sạch nhãn" **và** thiếu giá — mà một dòng thiếu giá thì luôn bị đóng nhãn,
   nên không dòng nào lọt vào. Ô đếm đó **không thể khác 0 được**.
2. *"… dòng đang chờ kiểm tra — nhập giá KHÔNG mở khoá được"* — vì ô thứ nhất
   luôn bằng 0, **toàn bộ** số dòng thiếu bị dồn hết sang đây. Màn hình nói với
   chủ dự án **đúng điều ngược lại sự thật**: nó bảo nhập giá vô ích, trong khi
   nhập giá chính là việc cần làm.

### Nay

Tôi dựng 3 dòng, 3 nguyên nhân khác nhau, rồi mở trang thật:

| Ô trên màn hình | Con số | Ý nghĩa |
|---|---|---|
| Đã tính được lợi nhuận | **1 / 3 dòng** | Bao nhiêu dòng đã có số |
| Dòng chưa có giá nhập | **1** | Nay **khác 0** — nói đúng sự thật |
| Trong đó "gõ giá là xong" | **1** | Việc chủ dự án làm được **ngay bây giờ** |
| Liệt kê từng cửa chặn | *"1 dòng: Số lượng bằng 0 — …"*, *"1 dòng: Chưa có giá nhập — …"* | Mỗi loại vướng mắc **tự nói tên mình**, kèm số dòng |
| Dòng đã có lãi nhưng chưa biết của ai | tách riêng | Không lẫn vào nhóm "chưa tính được" |

Hai câu văn chung cũng đã được sửa lại cho đúng: câu cũ nói *"chưa đủ **giá
nhập** cho toàn bộ dòng hàng"* — quy mọi thiếu sót về giá nhập; câu mới nói
*"còn dòng hàng của kỳ **chưa tính được lợi nhuận**… Danh sách ngay dưới nói rõ
thiếu cái gì và sửa ở đâu"*.

### Con số "chính thức" có còn chặt không?

**Còn nguyên, và chặt hơn trước.** Chỉ có **một** mốc được chấp nhận: **100 %**.
Và "100 % của cái gì" nay được định nghĩa để **không thể nói dối**: phần tử trên
của phép chia **đúng bằng** tập dòng thật sự nằm trong con số lợi nhuận. Nên
"đủ 100 %" đồng nghĩa với "mọi dòng của kỳ đều đã có mặt trong con số này".

Tôi đã xác nhận riêng ba điều mà chỉ thị yêu cầu:

- Dòng **số lượng 0** → **chặn** con số chính thức ✓
- Dòng **số lượng âm** → **chặn** con số chính thức, và ở trạng thái cần xem lại ✓
- Dòng **chưa rõ nhân viên** (nhưng đủ dữ liệu kinh tế) → **KHÔNG** bị loại khỏi
  lợi nhuận công ty, và **KHÔNG** kéo kỳ xuống CHƯA HOÀN CHỈNH; nó được nêu
  riêng ở mục KPI nhân viên ✓

**B02 = ĐẠT. B03 = ĐẠT.**

---

## 10. Rollback có làm mất dữ liệu chủ dự án không?

**KHÔNG. Tôi đã tự chạy thật, hai lần, theo hai kịch bản khác nhau.**

### Vì sao chuyện này quan trọng

Trong toàn bộ cơ sở dữ liệu chỉ có **ba thứ không tái tạo lại được**:

1. giá nhập chủ dự án gõ tay,
2. tick phân loại Gia dụng,
3. việc gán nhân viên cho một dòng.

Mọi bảng khác: chạy lại máy từ file sổ gốc là dựng lại được. Ba thứ trên thì
**nằm trong đầu chủ dự án**, không có file nào chứa chúng. Một lệnh hạ cấp
(rollback) thường được gõ **vội, lúc đang có sự cố khác** — đúng lúc không ai kịp
nghĩ tới hậu quả.

### Tôi đã kiểm thế nào

**Kịch bản 1 — hạ một bậc:** nâng cấp → nhập cả 3 loại dữ liệu → hạ cấp → nâng
cấp lại.

```
hạ cấp:   "giữ lại 1 dòng của employee_attribution_override trong … — `alembic upgrade` sẽ nạp lại."
          "giữ lại 1 dòng của kpi_purchase_price_override trong … — `alembic upgrade` sẽ nạp lại."
          "giữ lại 1 dòng của product_group_classification trong … — `alembic upgrade` sẽ nạp lại."
nâng lại: "đã nạp lại 1 dòng Owner vào kpi_purchase_price_override."
          "đã nạp lại 1 dòng Owner vào product_group_classification."
          "đã nạp lại 1 dòng Owner vào employee_attribution_override."
```

Kiểm lại nội dung sau khi nâng cấp: giá nhập `7.777.777 · Owner đã nhập · owner`
✓ · nhân viên `Vinh · NOI_THANH` ✓ · phân loại `GIA_DUNG` ✓ · **không còn bảng
lưu tạm nào sót lại** ✓.

**Kịch bản 2 — hạ về tận đáy** (`downgrade base`, kịch bản xấu nhất): dữ liệu
vẫn về đủ sau khi nâng cấp lại ✓.

### Cơ chế — và nó dừng đúng chỗ

Trước khi xoá bảng, hệ thống **sao nguyên nội dung sang một bảng lưu tạm trong
chính cơ sở dữ liệu đó**; lần nâng cấp sau nạp lại rồi dọn bảng lưu tạm đi. Nó
**không** dựng một hệ thống sao lưu doanh nghiệp, **không** ghi file dump ra
ngoài (nếu ghi file thì lại đẻ ra câu hỏi ai giữ file, giữ ở đâu, ai được đọc).
Và nếu chưa có dữ liệu nào thì **không tạo bảng lưu tạm rỗng** — để người vận
hành sau này không phải đoán cái bảng rỗng đó là gì.

Một giới hạn được nói thẳng trong tài liệu, và tôi xác nhận là đúng: **đây không
phải bản sao lưu chống mất cả cơ sở dữ liệu.** Nó chống đúng một tình huống đã
được nêu tên — lệnh hạ cấp xoá dữ liệu chủ dự án nhập tay. Chống mất cả cơ sở dữ
liệu là việc của sao lưu hạ tầng, không phải của một lệnh nâng/hạ cấp.

**B04 = ĐẠT.**

### Bảng dữ liệu mới cho việc gán nhân viên — có cần thiết không?

**CÓ — đây là mức tối thiểu bắt buộc, không phải mở rộng phạm vi.**

| Tiêu chí | Kết quả |
|---|---|
| Chỉ thêm, không sửa gì đang có? | ✓ Một bảng mới, không đổi một cột nào của bảng cũ, không đụng dữ liệu cũ |
| Có ghi đè bằng chứng kế toán gốc không? | ✗ Không — đó chính là **lý do** phải có bảng riêng |
| Khoá nghiệp vụ có đúng không? | ✓ Theo (mã đơn · mặt hàng · lần xuất hiện) — nên nó **sống sót qua một lần kế toán gửi lại sổ** |
| Có ghi lại nguồn gốc không? | ✓ Tên mà sổ ghi lúc gán · thời điểm · người gán |
| Có đẻ ra một hệ thống quản lý nhân sự không? | ✗ Không — một bảng, một trường, một thao tác |
| Hạ cấp có an toàn không? | ✓ Đã kiểm thật (ở trên) |

**Phân loại: LƯỢC ĐỒ TỐI THIỂU CÓ CƠ SỞ (JUSTIFIED_MINIMAL_SCHEMA).**

---

## 11. Test có đại diện cho dữ liệu thật không?

**CÓ — và đây là điểm bản sửa cải thiện âm thầm nhưng rất quan trọng.**

### Cái bẫy cũ

Bài kiểm tra cũ chứng minh "nhập giá tay có tác dụng" bằng cách dựng một dòng
**nhãn sạch + thiếu giá nhập**. Nhưng tổ hợp đó **không tồn tại trên dữ liệu
thật**: hễ thiếu giá nhập là máy đóng nhãn ngay. Nên bài test đó **chạy xanh mà
không chứng minh gì** về hệ thống thật — nó xanh đúng ở cái trạng thái mà thực tế
không bao giờ xảy ra.

### Nay

Bài chứng minh "nhập giá tay có tác dụng" đã được dựng lại trên **đúng trạng thái
mà máy sinh ra trên dữ liệu thật**: nhãn "cần kiểm tra" + đúng những mã lý do mà
máy ghi xuống (`TRACKING_HISTORY_PENDING`, `Missing.PurchasePrice`,
`Pending.eligible_kpi_profit`). Tôi đã đọc và xác nhận điều này.

Cả 11 tình huống mà chỉ thị yêu cầu đều **có bài kiểm tra thật**, và tôi đã chạy
lại toàn bộ:

| # | Tình huống | Có |
|---|---|---|
| 1 | Dòng "cần kiểm tra" thật + thiếu giá nhập + cứu bằng giá tay | ✓ |
| 2 | Dòng "cần kiểm tra" + sửa đè giá hợp lệ | ✓ |
| 3 | Số lượng 0 | ✓ |
| 4 | Số lượng âm | ✓ |
| 5 | Cảnh báo nghi trùng | ✓ |
| 6 | Giá bán 0 → lợi nhuận âm | ✓ |
| 7 | Chưa rõ nhân viên nhưng vẫn vào lợi nhuận công ty | ✓ |
| 8 | Gán lại nhân viên, kiểm qua cả ba màn hình | ✓ |
| 9 | Thẩm quyền KPI hỏng dù đã có giá tay | ✓ |
| 10 | Giá máy tra → chủ dự án sửa đè | ✓ |
| 11 | Hạ cấp rồi nâng cấp lại | ✓ |

Đáng chú ý: phần lớn các bài này **đi qua cơ sở dữ liệu thật và qua giao diện web
thật** (gửi form, nhận chuyển hướng, đọc lại HTML), chứ không chỉ gọi hàm.

### Kết quả chạy — nguyên văn, không giấu số bỏ qua

| Bộ test | Kết quả |
|---|---|
| Test tập trung PHB-03 (ngữ nghĩa + toàn tuyến + ranh giới) | **101 passed** |
| Test cơ sở dữ liệu / nâng-hạ cấp | **17 passed** |
| Riêng vòng hạ cấp → nâng cấp lại | **2 passed** |
| **Toàn bộ dự án** | **2136 passed, 11 skipped** |
| **Golden baseline** | **74 passed, 2 skipped** |

**11 dòng bỏ qua (skipped) là gì — nói rõ, không giấu:**

- **2 dòng** ở golden baseline: cần file Excel sổ gốc của kỳ 01.2026 và 06.2026,
  mà file thô đó **không nằm trong repo** (dữ liệu kinh doanh thật). Đây là hành
  vi có sẵn từ trước, **không** do bản sửa này gây ra.
- **9 dòng** còn lại: các bài kiểm tra kiểu dữ liệu tự động bỏ qua khi một cấu
  trúc không có trường thuộc kiểu đang xét — cơ chế có sẵn, không liên quan
  PHB-03.

Các con số này **khớp chính xác** với những gì báo cáo triển khai công bố. Báo
cáo đó nói đúng sự thật.

---

## 12. Có thay đổi nào vượt phạm vi không?

**KHÔNG.** Tôi đã xem toàn bộ danh sách file thay đổi giữa bản gốc và bản sửa.

**Đã kiểm và xác nhận KHÔNG đụng tới:** Tracking · Product Identity · Review
Queue · trình sửa đơn hàng tổng quát · máy trang tính tổng quát · hệ thống trả
hàng/hoàn tiền · Target · Legacy · Brand · Advanced Analytics · các truy vấn
bán hàng và phân tích đã nghiệm thu trước đó · gia cố linh tinh không liên quan.

**Thay đổi gói gọn trong:** ngữ nghĩa lợi nhuận của vertical Kinh doanh · tầng
trình bày và giao diện của chính vertical đó · một bảng dữ liệu mới cho việc gán
nhân viên · cơ chế an toàn khi hạ cấp · các bài kiểm tra tương ứng · tài liệu.

**SCOPE_DRIFT = KHÔNG.**

### Sáu điểm ghi nhận — KHÔNG điểm nào chặn

Theo đúng chỉ thị: *phát hiện không tự động sinh ra task mới.* Sáu điểm dưới đây
**không** đạt tiêu chí mở một chu kỳ sửa, và tôi ghi lại để chủ dự án biết chứ
không đề nghị làm gì ngay.

| # | Ghi nhận | Vì sao không chặn |
|---|---|---|
| **N-1** | Dòng **số lượng âm** vẫn được cộng vào cột **Doanh thu** | Quyết định `OD-2` chỉ nói về lợi nhuận và KPI. Dòng đó không bị giấu: nó có cảnh báo và nó kéo kỳ xuống CHƯA HOÀN CHỈNH. Nếu muốn loại khỏi doanh thu thì đó là một quyết định **mới** của chủ dự án |
| **N-2** | Ô chọn nhân viên trên bảng kê **không có mục trống**, nên với dòng chưa xác định nó hiện sẵn tên đầu danh sách. Bấm nhầm sẽ gán nhầm người | Có chủ đích (để tránh một mục trống lẫn giữa tên người). Và **sửa lại được ngay** bằng nút GỠ NV, kèm nhãn "Owner đã gán" cho thấy dòng nào do người sửa |
| **N-3** | Một tên nhân viên **chỉ gồm dấu cách** từ máy sẽ được coi là "đã xác định" | Đường ghi của chủ dự án **đã chặn** tên rỗng ở cả hai lớp (mã và cơ sở dữ liệu). Chỉ máy mới tạo được tình huống này, và thực tế không tạo |
| **N-4** | Vài bài kiểm tra đơn lẻ vẫn để nhãn "sạch" trên dòng thiếu giá nhập | Cái nhãn nay **không còn tham gia quyết định nào** — có bài kiểm tra đọc mã nguồn để canh điều đó. Đây là chữ nghĩa trong test, không phải hành vi hệ thống. **Quan trọng:** bài chứng minh việc cứu bằng giá tay **đã** dùng trạng thái thật |
| **N-5** | Sổ ngân sách soát xét (`PROJECT/REVIEW_BUDGET_LEDGER.md`) vẫn ghi trạng thái của phiên triển khai cũ (`2106 passed`, `golden 58`, chưa ghi chu kỳ sửa này) | Là việc ghi chép quản trị, **không** ảnh hưởng một con số nghiệp vụ nào. `PROJECT/PROJECT_PROGRESS.md` — nơi có thẩm quyền về trạng thái hiện tại — **đã** cập nhật đầy đủ và trung thực. Chế độ soát xét cấm tôi sửa file này |
| **N-6** | Tài liệu kiểm tra 19 mã lý do (`docs/reviews/PHB-03-pending-reason-business-classification.md`) được trích dẫn nhưng **không có mặt trên nhánh này** — nó nằm ở nhánh khác (`claude/phb-03-pending-reason-audit-ap9z60`, commit `c597f5a`) | Chỉ là chuyện đường dẫn tài liệu. Tôi đã lấy được bản gốc từ nhánh đó và đối chiếu — nội dung khớp với những gì bản sửa viện dẫn. Sẽ tự hết khi hai nhánh được gộp |

---

## 13. Có được phép deploy chưa?

**CHƯA — và điều đó KHÔNG phải vì có lỗi.**

| Câu hỏi | Trả lời |
|---|---|
| Bản sửa có đúng không? | **CÓ.** Không có phát hiện chặn nào |
| Có được deploy trong phiên này không? | **KHÔNG.** Chỉ thị soát xét cấm tường minh, và tôi đã không làm |
| Còn thiếu gì trước khi deploy? | **Kiểm chứng trên môi trường thật (E2E)** — mọi bằng chứng ở báo cáo này đến từ máy kiểm thử, chưa từ hệ thống đang chạy thật |
| Còn câu hỏi nào chờ chủ dự án quyết không? | **KHÔNG** |
| Có cần sửa thêm gì không? | **KHÔNG** |

**Đánh giá bản dự tuyển: ĐẠT (PASS). Sẵn sàng deploy: CHƯA (chờ kiểm chứng thật).**

---

## 14. Việc tiếp theo duy nhất là gì?

> **Kiểm chứng trên hệ thống thật (production verification / E2E).**
> Không sửa code. Không mở task mới. Không đổi phạm vi.

Cụ thể, cần xác nhận trên hệ thống đang chạy đúng những gì báo cáo này đã đo trên
máy kiểm thử:

1. Nâng cấp cơ sở dữ liệu lên phiên bản mới, xác nhận dữ liệu chủ dự án đã nhập
   trước đó **còn nguyên**.
2. Mở một kỳ thật, xác nhận ô **"dòng chưa có giá nhập"** nay **khác 0** (trên dữ
   liệu thật, gần như mọi dòng đều thiếu giá nhập — nên con số này phải lớn).
3. Nhập giá vốn cho **một** dòng thật, xác nhận lợi nhuận và DS quy đổi của dòng
   đó **đổi ngay**, không phải nạp lại sổ.
4. Gán **một** dòng "chưa xác định nhân viên" cho một người, xác nhận nó chuyển
   sang bảng của người đó và **tổng của kỳ không đổi**.
5. Xác nhận dòng số lượng 0 và số lượng âm hiện dấu `—` kèm lý do, **không** hiện
   số `0`.

Sau khi 5 điểm trên xanh trên hệ thống thật, PHB-03 mới đủ điều kiện chuyển sang
`DONE` và bàn tới việc phát hành.

---

## Phụ lục — Bảng tổng hợp kết quả soát xét

```
TARGET_GATE                      = PASS
REVIEW_BRANCH                    = claude/phb-03-bounded-semantics-repair-685gf4
                                   (nội dung giống hệt nhánh soát xét
                                    claude/phb-03-bounded-semantics-review-p489lh)
REVIEW_HEAD                      = d066d227da852b17a57d4a8492fa79c7fc7b2aff
RE_REVIEW_RESULT                 = PASS

B01 (giá nhập tay có hiệu lực)   = PASS
B02 (đếm thiếu giá trung thực)   = PASS
B03 (giao diện nói đúng lý do)   = PASS
B04 (hạ cấp không mất dữ liệu)   = PASS

MANUAL_PRICE_REAL_EFFECT         = YES
GENERIC_PENDING_PROFIT_GATE      = REMOVED
KPI_AUTHORITY_FAIL_CLOSED        = PASS
QUANTITY_ZERO                    = PASS
NEGATIVE_QUANTITY                = PASS
DUPLICATE_WARNING_ONLY           = PASS
ZERO_SELL_PRICE_NEGATIVE_PROFIT  = PASS
UNKNOWN_EMPLOYEE_COMPANY_PROFIT  = PASS
EMPLOYEE_RECLASSIFICATION        = PASS
RAW_EMPLOYEE_EVIDENCE_PRESERVED  = PASS
EMPLOYEE_ATTRIBUTION_SCHEMA      = JUSTIFIED_MINIMAL_SCHEMA
SPREADSHEET_LIKE_DETAIL          = PASS
COVERAGE_SEMANTICS               = PASS
REACHABLE_PRODUCTION_TESTS       = PASS

FOCUSED_TESTS                    = 101 passed (metrics + vertical + boundaries)
                                   17 passed  (history/migration)
FULL_TESTS                       = 2136 passed, 11 skipped
GOLDEN_TESTS                     = 74 passed, 2 skipped
MIGRATION_ROUND_TRIP             = 2 passed; và đã tự kiểm thêm bằng tay hai
                                   kịch bản (hạ 1 bậc, hạ về đáy) — dữ liệu
                                   Owner về đủ ở cả hai

BLOCKING_FINDINGS                = 0
NON_BLOCKING_FINDINGS            = 6 (N-1 … N-6, mục 12)
OWNER_DECISIONS_REQUIRED         = NONE
SCOPE_DRIFT                      = NO
DEPLOY_READY                     = NO (chờ kiểm chứng trên hệ thống thật)

NEXT_VERTICAL_ACTION             = Production verification / E2E only
```
