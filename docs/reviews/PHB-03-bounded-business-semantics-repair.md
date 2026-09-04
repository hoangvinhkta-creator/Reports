# PHB-03 — Sửa Ngữ Nghĩa Nghiệp Vụ Có Ranh Giới

**Loại phiên:** BOUNDED REPAIR (sửa có ranh giới, có sửa mã sản xuất)
**Ngày:** 2026-09-04
**Nhánh sửa:** `claude/phb-03-bounded-semantics-repair-685gf4`
**Dựng từ đúng bản triển khai PHB-03:** `60adb2ec22efdb4967d6971bbee852db660c8c18`
**Bản audit làm căn cứ:** `docs/reviews/PHB-03-pending-reason-business-classification.md`
(nhánh `claude/phb-03-pending-reason-audit-ap9z60`, commit `c597f5a`)

---

## 0. Đọc bản này thế nào

Bản này viết cho chủ dự án, không viết cho lập trình viên. Mỗi từ kỹ thuật
buộc phải dùng đều được giải thích ngay tại chỗ.

Ba từ xuất hiện xuyên suốt:

| Từ | Nghĩa trong bản này |
|---|---|
| **Dòng hàng** | Một dòng trong sổ chi tiết bán hàng: một mặt hàng, trên một số chứng từ, bán ngày nào, số lượng bao nhiêu, giá bao nhiêu. |
| **Giá nhập** | Giá công ty bỏ ra để có món hàng đó. Lấy giá bán trừ đi nó ra lợi nhuận. |
| **CẦN KIỂM TRA** (`PENDING`) | Một cái nhãn mà máy dán lên dòng hàng khi nạp sổ, nghĩa là "dòng này có ít nhất một ghi chú nào đó". |

Một điều cần nắm ngay, vì toàn bộ vấn đề nằm ở đó:

> **`CẦN KIỂM TRA` không phải một lý do. Nó chỉ là kết quả của phép cộng:
> "dòng này có ít nhất một ghi chú nào đó" thì dán nhãn.**
>
> Bản audit đã đếm hết: có **19 mã ghi chú** khiến máy dán nhãn đó, che **31
> tình huống** rất khác nhau — từ "chưa nạp bảng giá" tới "một đơn có hai tên
> nhân viên". Hệ thống cũ dùng **kết quả phép cộng** đó làm luật để quyết định
> có được tính lợi nhuận hay không.

---

## 1. Đã sửa vấn đề gì?

Sáu việc, tất cả nằm trong đúng vertical Kinh doanh của PHB-03.

### 1.1 Lợi nhuận nay phụ thuộc vào SỐ LIỆU KINH TẾ, không phụ thuộc cái nhãn

Trước: máy hỏi *"dòng này có mang nhãn CẦN KIỂM TRA không?"*
Sau: máy hỏi **năm câu về chính dòng hàng đó**:

```
CÓ TÍNH ĐƯỢC LỢI NHUẬN KHÔNG?
        có giá bán?
    VÀ  có số lượng?
    VÀ  số lượng lớn hơn 0?
    VÀ  có giá nhập (máy tìm ra HOẶC chủ dự án nhập)?
    VÀ  bảng thẩm quyền chi phí KPI đọc được?
```

Không câu nào trong năm câu đó hỏi cái nhãn. Đó là toàn bộ nội dung quyết
định **OD-6** của chủ dự án.

### 1.2 Giá chủ dự án nhập nay THẬT SỰ làm lợi nhuận đổi (`B01`)

Đây là lỗi nặng nhất, và nó là một **vòng tự khoá**:

```
1. Máy nạp sổ, không tra ra giá nhập của dòng X.
2. Máy ghi ghi chú "Thiếu giá mua tham chiếu" và đóng dấu CẦN KIỂM TRA.
   Dấu này được LƯU vào cơ sở dữ liệu.
3. Chủ dự án mở màn hình, gõ giá nhập của dòng X vào. Giá được lưu.
4. Máy đọc báo cáo: giá tay được ghép vào dòng X đúng như thiết kế...
5. ...NHƯNG cửa chặn đọc cái dấu đã đóng ở bước 2, và từ chối.
                                    ↑
   Lý do khiến nó bị đóng dấu chính là thứ chủ dự án vừa sửa xong ở bước 3.
```

Hệ quả: **với đúng những dòng mà tính năng nhập giá tay sinh ra để cứu, tính
năng đó không bao giờ có tác dụng.** Nó chỉ chạy trên những dòng vốn đã có giá
rồi — tức là những dòng không cần cứu.

Nay vòng lặp đã bị cắt: cửa chặn hỏi *"đã có giá nhập chưa?"*, và giá đó đến
từ máy hay từ tay chủ dự án đều được.

### 1.3 Lợi nhuận công ty tách khỏi KPI của từng nhân viên (`OD-5`)

Trước, hai câu hỏi rất khác nhau bị trộn làm một:

| | Trước | Sau |
|---|---|---|
| *"Dòng này lãi bao nhiêu?"* | mất số | có số, vào tổng của kỳ |
| *"Lãi đó của ai?"* | mất số | chưa rõ ⟹ nằm ở nhóm **Chưa xác định nhân viên** |

### 1.4 Bảng kê chi tiết hoạt động như một trang tính

Sửa ô nhập được → bấm LƯU → các ô tiền suy ra tự tính lại trên chính trang đó.
Không còn bước "tính" riêng nào.

### 1.5 Coverage nói đúng thiếu cái gì và sửa ở đâu (`B02`, `B03`)

Ô đếm "chỉ thiếu mỗi giá nhập" trước đây **luôn bằng 0 theo cấu tạo**, nên mọi
dòng thiếu bị dồn sang ô "nhập giá không cứu được" — màn hình nói ngược lại
sự thật. Nay mỗi cửa chặn tự nói tên mình kèm số dòng.

### 1.6 Rollback không còn xoá dữ liệu chủ dự án tự nhập (`B04`)

---

## 2. Hành vi trước đây sai ở đâu?

Bốn chỗ, xếp theo mức nghiêm trọng.

### `B01` — cửa chặn tự quy chiếu

Đã mô tả ở mục 1.2. Câu lệnh gây ra nó dài đúng một dòng:

> *nếu nhãn của dòng không phải `AUTO` thì trả về "không có lợi nhuận"*

Nó không chỉ "quá rộng". Nó đọc **một ảnh chụp cũ của chính điều kiện mà thao
tác của chủ dự án vừa làm cho hết đúng**.

### `B02` — ô đếm luôn bằng 0

Ô "còn bao nhiêu dòng chỉ thiếu mỗi giá nhập" được định nghĩa là:

> *nhãn là `AUTO` **VÀ** chưa có giá nhập*

Nhưng một dòng chưa có giá nhập thì luôn mang ghi chú "Thiếu giá mua tham
chiếu" ⟹ nhãn của nó **chắc chắn** là `CẦN KIỂM TRA`, không bao giờ là `AUTO`.
Hai vế loại trừ nhau, nên ô đó **không bao giờ khác 0**, dù thực tế có bao
nhiêu dòng thiếu giá đi nữa.

### `B03` — màn hình đổ mọi lỗi cho "thiếu giá nhập"

Câu cảnh báo cũ viết nguyên văn: *"Chưa đủ giá nhập cho toàn bộ dòng hàng của
kỳ"*. Nhưng một dòng có thể chưa tính được vì **số lượng bằng 0**, vì **thiếu
giá bán**, hoặc vì **file cấu hình thẩm quyền hỏng** — ba việc phải sửa ở ba
chỗ khác nhau. Nói sai nguyên nhân là đẩy chủ dự án đi sửa nhầm chỗ.

### `B04` — rollback xoá dữ liệu không tái tạo lại được

Lệnh quay lui phiên bản cơ sở dữ liệu (`alembic downgrade`) xoá thẳng hai bảng
chứa giá nhập chủ dự án gõ tay và tick Gia dụng. Chạy lại máy từ file sổ gốc
dựng lại được **mọi bảng khác**, nhưng không dựng lại được hai bảng này — nội
dung của chúng ở trong đầu chủ dự án, không ở trong file nào. Và lệnh rollback
thường được gõ vội lúc đang có sự cố khác, đúng lúc không ai kịp nghĩ tới.

---

## 3. Sau sửa, khi thiếu giá vốn thì chuyện gì xảy ra?

**Ví dụ cụ thể.** Đơn `BTL00300`, mặt hàng `Máy Giặt Panasonic NA-F10S10BRV`,
số lượng 1, giá bán 8.000.000. Máy không tra được giá nhập.

| Chỗ hiện | Nội dung |
|---|---|
| Bảng kê chi tiết → cột **Doanh thu** | `8.000.000` — con số kế toán đã ghi, có ngay |
| Bảng kê chi tiết → cột **Lợi nhuận KPI** | `—` kèm câu *"Chưa có giá nhập — Owner nhập được ngay tại đây"* |
| Bảng kê chi tiết → cột **DS quy đổi** | `—`, cùng lý do |
| Trang Tổng hợp → khối coverage | *"1 dòng chưa có giá nhập. 1 trong số đó chỉ cần gõ giá nhập là có lợi nhuận ngay."* |
| Lợi nhuận KPI toàn kỳ | dán nhãn **CHƯA HOÀN CHỈNH** |

**Điều KHÔNG xảy ra:** ô lợi nhuận **không** hiện `0`. Một ô `0` trông như đã
tính xong và ra kết quả bằng không; một ô `—` kèm lý do nói đúng sự thật và
chỉ luôn việc phải làm.

---

## 4. Khi chủ dự án nhập/sửa giá vốn thì chuyện gì xảy ra?

Tiếp ví dụ trên. Chủ dự án gõ `6.000.000` vào ô Giá nhập KPI của dòng đó rồi
bấm **LƯU**. Trang tải lại, và ngay lập tức:

| Ô | Trước khi lưu | Sau khi lưu |
|---|---|---|
| Giá nhập KPI | `—` | `6.000.000` |
| Nguồn giá | *Chưa có* | **Owner đã nhập** |
| Lợi nhuận KPI của dòng | `—` | `2.000.000` (= 8.000.000 − 6.000.000, × 1 cái) |
| DS quy đổi của dòng | `—` | `100.000.000` (= 2.000.000 ÷ 2 %) |
| Coverage của kỳ | `0 / 1 dòng` | `1 / 1 dòng` |
| Lợi nhuận KPI toàn kỳ | CHƯA HOÀN CHỈNH | **CHÍNH THỨC** |

**Hai điều quan trọng:**

1. **Không cần nạp lại sổ.** Việc ghép giá tay vào dòng xảy ra lúc ĐỌC báo
   cáo, nên con số mới có hiệu lực ngay ở lần tải trang kế tiếp.

2. **Lịch sử không bị viết lại.** Nhãn `CẦN KIỂM TRA` mà máy đóng lúc nạp sổ
   **vẫn còn nguyên** trong cơ sở dữ liệu — nó là bằng chứng của lần chạy máy
   đó, và bằng chứng thì không được sửa. Nó chỉ không còn quyền chặn tính toán.

**Hai nhãn nguồn giá, và chúng khác nhau thật:**

| Tình huống | Nhãn lưu lại | Ý nghĩa |
|---|---|---|
| Máy chưa tra được, chủ dự án gõ vào | `MANUAL` — *Owner đã nhập* | lấp một chỗ trống |
| Máy đã tra ra một giá, chủ dự án gõ đè lên | `MANUAL_OVERRIDE` — *Owner đã sửa* | thay một con số đã có |

Gõ đè đúng bằng giá máy tìm ra **vẫn** là *Owner đã sửa*: chủ dự án đã ra một
quyết định, và xoá dấu vết quyết định đó là nói dối về nguồn con số.

Nhập nhầm thì bấm **GỠ** — dòng trở lại đúng giá máy tính.

---

## 5. Dòng trùng được xử lý thế nào?

**Quyết định OD-3: chỉ CẢNH BÁO, không loại khỏi bất kỳ con số nào.**

Hành vi cũ **tự mâu thuẫn**, và không có cách đọc nào khiến nó đúng:

| Chỉ tiêu | Có loại dòng trùng không? |
|---|---|
| Doanh thu bán hàng | **KHÔNG** — cộng cả hai dòng |
| Lợi nhuận KPI | **CÓ** — bỏ cả hai dòng |

Nghĩa là: nếu đó thật sự là gõ nhầm hai lần thì **doanh thu đã bị đếm đúp mà
chưa ai chặn**; còn nếu đó là hàng thật (một đơn bán tivi kèm hai cái giá treo
giống hệt nhau — chuyện hoàn toàn bình thường) thì **lợi nhuận đang bị loại
oan**.

Nay hai chỉ tiêu xử lý dòng trùng **giống nhau**: cả hai đều cộng, và dòng đó
mang một cảnh báo nói rõ:

> *"Sổ có một dòng khác giống hệt dòng này. Doanh thu và lợi nhuận VẪN được
> tính — nếu đây thật sự là gõ nhầm hai lần thì cần sửa trên sổ gốc."*

Việc chống trùng khi **nạp lại cùng một file** là chuyện khác hẳn và đã được
giao cho `TASK-201`; bản sửa này không đụng tới.

---

## 6. Giá bán 0 được xử lý thế nào?

**Quyết định OD-4: vẫn tính, và cảnh báo.**

Ví dụ nguyên văn của chủ dự án:

```
số lượng   = 1
giá bán    = 0            (hàng tặng kèm)
giá nhập   = 500.000
lợi nhuận  = (0 − 500.000) × 1 = −500.000
```

Con số `0` ở ô giá bán là một **giá bán thật**, không phải một ô trống. Và
500.000 kia là khoản tiền doanh nghiệp **thật sự bỏ ra**, nên nó phải hiện ra
dưới dạng âm.

Hệ thống hiện đồng thời ba cảnh báo trên dòng đó:

- *"Giá bán bằng 0 (thường là hàng tặng kèm)…"*
- *"Giá nhập cao hơn giá bán — dòng này đang bán lỗ"*
- *"Lợi nhuận của dòng này là số âm"*

**Điều KHÔNG xảy ra:** con số `−500.000` không bị âm thầm thay bằng `0`. Thay
nó là làm báo cáo đẹp hơn thực tế.

Ghi nhận thêm một điểm bản audit nêu (**không** sửa trong task này): danh sách
từ khoá hạ mức cảnh báo hiện có chữ `"phí"` mà không có `"giá treo"`, nên
*"Chi phí lắp đặt"* giá 0 thì được tha còn *"Giá treo Tivi"* tặng kèm giá 0 thì
bị đánh dấu. Sau bản sửa này điều đó **không còn ảnh hưởng tới con số nào** —
cả hai loại dòng đều được tính bình thường — nó chỉ ảnh hưởng dòng nào hiện
cảnh báo.

---

## 7. Số lượng 0 / âm được xử lý thế nào?

### Số lượng bằng 0 — quyết định OD-1

**Không tính, không chốt lợi nhuận, yêu cầu sửa.**

Ví dụ thật từ dữ liệu nghiệm thu: `BTL00300`, `Máy Giặt Panasonic`, số lượng
`0`, đơn giá `6.200.000`. Nhìn dòng đó không ai biết được nó nghĩa là *"thật
sự không giao cái nào"* hay *"quên gõ số lượng"*.

Chủ dự án đã quyết: **đây là dữ liệu chưa đủ tin, không phải lãi 0 đồng.**

| | Hiện thế nào |
|---|---|
| Ô Lợi nhuận KPI của dòng | `—`, **không phải** `0` |
| Lý do trên dòng | *"Số lượng bằng 0 — đây là dữ liệu chưa đủ tin, không phải lãi 0 đồng. Cần sửa số lượng trên sổ gốc"* |
| Có nằm trong nhóm "gõ giá là xong" không? | **KHÔNG** — màn hình không hứa nhầm rằng nhập giá sẽ cứu được nó |

### Số lượng âm — quyết định OD-2

**Cần xem lại; không tự cộng vào KPI của nhân viên nào.**

Chủ dự án đã ghi rõ: *không phát minh ngữ nghĩa trả hàng/hoàn tiền trong task
này*. Vì vậy dòng số lượng âm dừng ở mức "cần xem lại", giữ nguyên vẹn.

> **Cần chủ dự án xác nhận một điểm** (xem mục 13): bản sửa này cũng **không**
> cộng dòng số lượng âm vào lợi nhuận của cả kỳ. Lý do: cộng
> `−1 × biên lợi nhuận` vào một con số nào đó **chính là** khẳng định dấu âm
> nghĩa là hoàn hàng — tức là phát minh đúng cái ngữ nghĩa mà `OD-2` cấm. Nếu
> ý chủ dự án là "vẫn vào tổng công ty, chỉ không vào KPI cá nhân", đây là một
> dòng cần sửa và bản sửa sẽ rất nhỏ.

---

## 8. Chưa xác định nhân viên được xử lý thế nào?

**Quyết định OD-5: lợi nhuận vẫn tính, KPI cá nhân thì chưa gán.**

### Ví dụ dễ hiểu

Một đơn có 3 dòng. Hai dòng ghi nhân viên là `"Vinh"`, dòng thứ ba người ta gõ
nhầm thành `"Vjnh"` — không có trong danh sách nhân viên.

| | Trước | Sau |
|---|---|---|
| Lợi nhuận của 3 dòng | **mất cả 3** (vạ lây cả đơn) | tính cả 3 |
| Hai dòng của Vinh | không vào KPI của ai | vào KPI của Vinh |
| Dòng thứ ba | biến mất không dấu vết | nằm ở nhóm **Chưa xác định nhân viên** |

### Trên màn hình

Trang Tổng hợp hiện thêm hai ô, và **hai ô này cộng lại luôn đúng bằng tổng
lợi nhuận của kỳ** — nên không đồng nào biến mất:

```
Đã cộng cho nhân viên        3.000.000 đồng
Chưa xác định nhân viên      3.000.000 đồng    (1 dòng chưa gán)
```

Nhóm *Chưa xác định nhân viên* cũng là **một mục trong ô chọn nhân viên** như
mọi người khác, nên chủ dự án mở nó ra xem được đúng những dòng đang treo. Khi
dòng cuối cùng được gán, mục đó **tự biến mất** khỏi ô chọn — nếu không, chủ
dự án sẽ mở ra một trang trống và tưởng mất dữ liệu.

### Cách sửa

Trên Bảng kê chi tiết, mỗi dòng có một ô chọn nhân viên và nút **GÁN NV**:

```
"Chưa xác định nhân viên"
   → chọn "Vinh" trong ô
   → bấm GÁN NV
   → dòng rời khỏi nhóm chưa xác định
   → dòng hiện trong trang của Vinh
   → KPI và tổng của Vinh cập nhật
   → tổng của CẢ KỲ không đổi
```

Không cần nạp lại sổ.

**Ba ràng buộc an toàn:**

1. **Chỉ chọn được người có thật.** Danh sách lấy từ file danh sách nhân viên
   chính thức (`config/employees.yaml`), không gõ tự do. Gõ tự do một cái tên
   vào KPI là mở lại đúng lớp lỗi mà quy tắc `HD-110-06` đã đóng.
2. **Người đã nghỉ không có trong danh sách chọn.** Gán một dòng mới cho người
   đã nghỉ là một quyết định nhân sự, không phải một lần sửa dữ liệu.
3. **Bằng chứng gốc không bị ghi đè.** Tên mà sổ kế toán ghi **vẫn nằm nguyên**
   ở chỗ cũ; việc gán được lưu ở một bảng riêng, kèm cột ghi lại tên cũ tại
   thời điểm sửa. Sau này vẫn trả lời được câu *"sổ ghi ai, và chủ dự án sửa
   thành ai"*. Bấm **GỠ NV** là dòng trở lại đúng tên sổ ghi.

---

## 9. Bảng kê chi tiết hoạt động giống trang tính ra sao?

Đây **không** phải một Excel dựng trong trình duyệt. Nó là một bảng có đúng
hai loại ô, và ranh giới giữa hai loại là tuyệt đối.

### Ô SỬA ĐƯỢC — chỉ hai

| Ô | Sửa thế nào |
|---|---|
| **Giá nhập KPI** | gõ số rồi bấm LƯU. Máy đã tự điền thì vẫn sửa được. |
| **Nhân viên** | chọn tên rồi bấm GÁN NV |

### Ô SUY RA — không gõ được, tự tính lại

| Ô | Lấy từ đâu |
|---|---|
| **Doanh thu** | con số kế toán mà hệ thống đã ghi khi nạp sổ — **KHÔNG** phải phép nhân `số lượng × đơn giá` làm lại |
| **Lợi nhuận KPI** | `(giá bán − giá nhập) × số lượng − chiết khấu` |
| **DS quy đổi** | `lợi nhuận KPI ÷ tỉ lệ quy đổi của chính dòng đó` |

Chuỗi phụ thuộc mà chủ dự án yêu cầu:

```
số lượng  ·  giá bán  ·  giá nhập
                 ↓
   doanh thu · lợi nhuận · DS quy đổi   (tự cập nhật sau khi lưu)
```

### Bốn quy tắc của bảng này

1. **Không có nút "tính".** Lưu xong là trang đã hiện số mới.
2. **Không gõ thẳng vào ô lợi nhuận được.** Không có ô nhập nào cho ba cột suy
   ra — điều này được một bài kiểm thử canh bằng cấu trúc, không bằng lời hứa.
3. **Thiếu đầu vào thì để trống KÈM LÝ DO**, không bao giờ bịa số `0`.
4. **Doanh thu giữ nguyên ngữ nghĩa kế toán đã chốt.** Không thay bằng công
   thức đơn giản hoá.

### Ba bộ lọc, ba câu hỏi khác nhau

| Nút | Trả lời câu |
|---|---|
| **CHƯA CÓ GIÁ NHẬP** | *"Tôi phải gõ giá cho những dòng nào?"* |
| **CHƯA XÁC ĐỊNH NHÂN VIÊN** | *"Dòng nào đã có lãi nhưng chưa biết của ai?"* |
| **TẤT CẢ DÒNG** | *"Cho tôi xem cả kỳ"* (để sửa một giá máy đã tự điền) |

Mỗi dòng chưa tính được lợi nhuận còn có một dòng phụ ngay bên dưới, ghi rõ
cửa chặn, các cảnh báo, và những ghi chú mà máy đã ghi khi nạp sổ (phần ghi
chú này **chỉ để đọc**, không còn chặn gì nữa).

---

## 10. Coverage hiện nói cho chủ dự án biết điều gì?

Một câu duy nhất: **"Thiếu cái gì và tôi cần sửa ở đâu?"**

### Trước

```
Giá nhập đã đủ chưa?   1 / 3 dòng
  0  dòng chưa có giá nhập — Owner nhập được ngay ở trang hoàn thiện giá nhập.
  2  dòng đang chờ kiểm tra — nhập giá KHÔNG mở khoá được các dòng này.
```

Con số `0` ở dòng đầu là **sai theo cấu tạo** (mục 2, `B02`). Câu thứ hai nói
với chủ dự án rằng nhập giá vô ích — trong khi sự thật là nhập giá cứu được
gần như tất cả.

### Sau

```
Đã tính được lợi nhuận cho bao nhiêu dòng?   1 / 3 dòng

  1 dòng chưa có giá nhập. 1 trong số đó chỉ cần gõ giá nhập
    là có lợi nhuận ngay.
  1 dòng: Số lượng bằng 0 — đây là dữ liệu chưa đủ tin, không phải
    lãi 0 đồng. Cần sửa số lượng trên sổ gốc.

  1 dòng đã tính được lợi nhuận nhưng CHƯA biết của nhân viên nào.
```

### Bốn con số, cố ý không gộp

| Con số | Trả lời câu | Sửa ở đâu |
|---|---|---|
| **Chưa có giá nhập** | *"Còn bao nhiêu dòng thiếu giá?"* | Bảng kê chi tiết |
| **Chỉ cần gõ giá là xong** | *"Trong đó bao nhiêu dòng tôi làm xong ngay được?"* | Bảng kê chi tiết |
| **Từng cửa chặn khác** | *"Những dòng còn lại vướng cái gì?"* | sổ gốc / cấu hình |
| **Chưa xác định nhân viên** | *"Bao nhiêu dòng đã có lãi nhưng chưa biết của ai?"* | Bảng kê chi tiết |

Chênh lệch giữa hai con số đầu chính là **số dòng mà nhập giá không đủ để
cứu** — chủ dự án đọc được ngay, thay vì bị hứa hẹn.

**Mốc CHÍNH THỨC không đổi:** vẫn là 100 %, vẫn là phép so bằng, không có
ngưỡng phần trăm nào thay thế. Chỉ có định nghĩa "100 % của cái gì" là được
nói cho đúng: *mọi dòng của kỳ đều đã tính được lợi nhuận*.

---

## 11. Rollback đã an toàn như thế nào?

### Vấn đề (`B04`)

Ba bảng chứa thứ **duy nhất** trong toàn bộ cơ sở dữ liệu không tái tạo lại
được:

1. Giá nhập chủ dự án gõ tay
2. Tick Gia dụng
3. Việc gán nhân viên cho một dòng

Chạy lại máy từ file sổ gốc dựng lại được mọi bảng khác. Nhưng không dựng lại
được ba bảng này — nội dung của chúng ở trong đầu chủ dự án. Lệnh quay lui
phiên bản cơ sở dữ liệu xoá thẳng chúng, không thông báo gì.

### Cách sửa — nhỏ nhất có thể

**Trước khi xoá, chép sang một cái két trong cùng cơ sở dữ liệu. Lần nâng cấp
lại thì lấy ra trả về chỗ cũ, rồi dọn cái két đi.**

```
Chạy lệnh quay lui
   → "giữ lại 143 dòng của kpi_purchase_price_override trong ... — `alembic upgrade` sẽ nạp lại."
   → bảng thật bị xoá (lệnh vẫn làm đúng việc của nó)
   → nhưng KHÔNG một dòng nào của chủ dự án bị mất

Chạy lệnh nâng cấp lại
   → "đã nạp lại 143 dòng Owner vào kpi_purchase_price_override."
   → dữ liệu về đúng chỗ cũ, cái két rỗng đi
```

### Vì sao chọn cách này

| Cách | Vì sao **không** chọn |
|---|---|
| Dịch vụ sao lưu riêng | Chỉ thị cấm dựng "enterprise backup subsystem". Và nó đặt ra câu hỏi ai giữ, giữ ở đâu, ai được đọc — tức là một hệ thống mới. |
| Xuất ra file | Cùng lý do trên, cộng thêm việc dữ liệu rời khỏi nơi vốn được bảo vệ. |
| **Két cùng cơ sở dữ liệu** | Cùng quyền, cùng giao dịch, cùng vòng đời sao lưu hạ tầng. Một câu lệnh chạy được trên cả hai loại cơ sở dữ liệu dự án dùng. |

**Điều cách này KHÔNG hứa:** đây không phải bản sao lưu chống mất cả cơ sở dữ
liệu. Chống chuyện đó là việc của sao lưu hạ tầng
(`governance/product/16_BACKUP_DISASTER_RECOVERY.md`), không phải của một lệnh
nâng cấp. Nó chống đúng **một** tình huống, và là tình huống đã được nêu tên.

**Chi tiết nhỏ nhưng quan trọng:** cơ sở dữ liệu rỗng thì **không** tạo két. Một
cái két rỗng nằm lại là rác, và tệ hơn — lần sau nhìn thấy nó, người vận hành
không biết nó rỗng vì chưa có dữ liệu hay vì đã có ai xoá mất.

---

## 12. Test thực tế nào chứng minh các hành vi trên?

### Nguyên tắc: test phải dựng trạng thái mà production THẬT SỰ tạo ra

Bản audit đã chỉ ra một vấn đề nặng ở bộ test cũ: bài
`test_a_missing_price_becomes_manual_and_recalculates_the_profit` dựng một dòng
**không có giá nhập** nhưng đặt nhãn là `AUTO`. Tổ hợp đó **không thể xảy ra
trên dữ liệu thật** — thiếu giá nhập thì máy luôn đóng dấu `CẦN KIỂM TRA`. Bài
test đó chạy xanh nhưng **không chứng minh gì** về production.

Bản sửa này đổi công cụ dựng dữ liệu thử: thiếu giá nhập ⟹ nhãn `CẦN KIỂM TRA`
+ đúng những mã ghi chú mà máy ghi. Hệ quả: **mọi bài kiểm thử qua cơ sở dữ
liệu của PHB-03 nay chạy trên trạng thái production thật**, không chỉ những bài
mới.

Bài `test_a_pending_line_stays_out_of_the_profit_sum_even_with_a_manual_price`
— bài đang **cố định hoá chính lỗi `B01`** thành hành vi mong muốn — đã được
thay bằng bài khẳng định điều ngược lại theo `OD-6`.

### Mười hành vi chủ dự án yêu cầu, và bài test tương ứng

| # | Hành vi | Bài kiểm thử |
|---|---|---|
| 1 | Thiếu giá tự động → chủ dự án nhập tay → lợi nhuận tính lại | `test_a_manual_price_rescues_the_exact_lines_it_was_built_to_rescue` (qua cơ sở dữ liệu thật) |
| 2 | `CẦN KIỂM TRA` + giá sửa tay hợp lệ → nhãn không chặn | `test_a_pending_line_with_a_valid_override_is_not_blocked_by_the_label` |
| 3 | Số lượng 0 → cảnh báo, không chốt lợi nhuận | `test_quantity_zero_warns_and_never_finalises_a_profit` · `test_a_zero_quantity_line_is_never_finalised_as_zero_profit` |
| 4 | Dòng trùng đủ số liệu → cảnh báo, **cả** doanh thu **và** lợi nhuận vẫn tính | `test_a_possible_duplicate_only_warns_and_keeps_both_revenue_and_profit` · `test_a_duplicate_line_keeps_both_its_revenue_and_its_profit` |
| 5 | Giá bán 0 + số lượng > 0 + có giá nhập → lợi nhuận âm được tính | `test_a_zero_sell_price_warns_and_still_produces_a_negative_profit` · `test_a_zero_sell_price_line_reports_the_real_negative_profit` |
| 6 | Chưa rõ nhân viên → lợi nhuận kỳ vẫn cộng, KPI cá nhân chưa gán, nhóm treo nhìn thấy được | `test_an_unknown_employee_keeps_company_profit_but_not_an_individual_kpi` · `test_an_unknown_employee_line_still_counts_toward_the_period_profit` · `test_the_unresolved_employee_bucket_is_a_place_the_owner_can_open` |
| 7 | Chủ dự án gán nhân viên → nhóm treo giảm, trang của người đó có thêm dòng, KPI cập nhật | `test_the_owner_classifies_an_unknown_employee_and_every_view_follows` (đi hết vòng qua HTTP thật) |
| 8 | Thẩm quyền KPI hỏng → vẫn chặn, kể cả khi đã có giá tay | `test_a_broken_kpi_authority_fails_closed_even_with_a_manual_price` · `test_a_broken_kpi_authority_still_fails_closed_through_the_whole_stack` |
| 9 | Sửa giá máy đã điền → nhãn *Owner đã sửa* → tính lại | `test_editing_an_auto_price_becomes_manual_override_and_recalculates` · `test_editing_an_auto_price_records_override_and_moves_the_number` |
| 10 | Điền giá còn thiếu → nhãn *Owner đã nhập* → tính lại | `test_a_missing_price_becomes_manual_and_recalculates_the_profit` |

### Các bài kiểm thử thêm cho phần còn lại

| Chủ đề | Bài kiểm thử |
|---|---|
| Coverage nói đúng thiếu cái gì (`B02`/`B03`) | `test_coverage_separates_what_the_owner_can_fix_from_what_they_cannot` · `test_the_coverage_block_says_what_is_missing_and_where_to_fix_it` |
| Bảng kê tự tính lại như trang tính | `test_the_detail_table_shows_derived_money_and_recalculates_after_a_save` |
| Không gõ được vào ô suy ra | `test_the_detail_table_never_lets_anyone_type_into_a_derived_column` |
| Rollback không mất dữ liệu (`B04`) | `test_rollback_never_destroys_what_the_owner_typed_in` |
| Không để lại két rỗng | `test_rollback_of_an_empty_database_leaves_no_leftover_backup` |
| Cửa chặn **không bao giờ** đọc cái nhãn | `test_the_profit_gate_never_reads_the_pipeline_status_label` (đọc chính mã nguồn) |
| Bất biến chống coverage nói dối | `test_the_invariant_that_keeps_coverage_from_lying` |
| Bằng chứng gốc không bị ghi đè | `test_the_raw_accounting_employee_survives_a_reassignment` · `test_removing_an_assignment_returns_the_line_to_what_the_book_says` |
| Không gán được cho người không có thật | `test_the_page_refuses_to_assign_a_name_that_is_not_a_real_employee` |

### Kết quả chạy thật (bằng chứng E1, trên nhánh sửa)

```
Toàn bộ test          2136 passed, 11 skipped in 87.09s
Golden baseline         74 passed,  2 skipped in  9.10s
Vertical PHB-03        101 passed             in  2.77s
Rollback B04             2 passed, 15 deselected in 2.37s
```

Không có bài nào bị bỏ qua, tắt, hay khoanh vùng để lấy màu xanh.

---

## 13. Những gì cố tình KHÔNG làm trong task này?

### Không mở, đúng theo ranh giới chủ dự án đặt ra

- **Tracking** — không đụng một dòng nào.
- **Nhận diện sản phẩm (Product Identity)** — không thiết kế lại. Bản audit đã
  chứng minh nhận diện chỉ cần để **TÌM** giá nhập tự động, không cần để
  **TÍNH** lợi nhuận khi đã có giá; nên sau bản sửa này, một dòng chưa nhận
  diện được sản phẩm vẫn tính được lợi nhuận bình thường một khi chủ dự án đã
  nhập giá.
- **Hàng chờ kiểm tra (Review Queue)** — không thiết kế lại. Các ghi chú của nó
  vẫn được ghi và vẫn hiện ra; chúng chỉ thôi không chặn tính toán nữa.
- **Hệ thống trả hàng/hoàn tiền** — không dựng.
- **Hệ thống sửa đơn hàng tổng quát** — không dựng. Chỉ thêm đúng một thao tác
  hẹp: gán nhân viên cho một dòng.
- **Trang tính (spreadsheet engine)** — không dựng. Chỉ có hai ô nhập được và
  ba ô suy ra, ranh giới cố định.
- **Target · Legacy · Brand · Advanced Analytics · quy trình tổng quát** —
  không đụng.
- **Bốn chỗ khác cũng dùng cửa chặn theo nhãn** (`sales_queries`,
  `analytics_queries`) — **cố ý không sửa**. Chúng thuộc `PRA-003`/`PRA-004` và
  **không** hợp nhất giá tay, nên chúng đang tự nhất quán. Sửa chúng là mở rộng
  phạm vi.
- **Không đổi cấu trúc dữ liệu cho việc tính lại giá nhập.** Cột danh sách ghi
  chú đã có sẵn từ trước; bản sửa chỉ bắt đầu đọc nó.
- **Không chạy lại máy, không viết lại lịch sử.** Nhãn cũ giữ nguyên trong cơ
  sở dữ liệu.

### Một bảng mới, và vì sao nó là bắt buộc

Việc gán nhân viên **buộc** phải có một bảng mới (`0004_employee_attribution`).
Trong toàn bộ dự án không có sẵn chỗ nào lưu được khẳng định đó, và ba lựa chọn
thay thế đều sai:

| Lựa chọn | Vì sao không được |
|---|---|
| Ghi đè tên nhân viên ở bảng kết quả máy | Bảng đó **chỉ ghi thêm, không sửa** và là bằng chứng kế toán gốc. Ghi đè là xoá bằng chứng để thay bằng ý kiến — chỉ thị cấm tường minh. |
| Dùng lại bảng giá nhập | Ngữ nghĩa khác hẳn. |
| Không lưu, hỏi lại mỗi lần | Không đạt được kết quả UX mà `OD-5` yêu cầu. |

Bảng mới nhỏ nhất có thể: ba khoá nghiệp vụ, một tên, một cột ghi lại tên cũ,
hai cột ai-sửa-lúc-nào. Nó dùng lại **nguyên** cấu trúc của bảng giá nhập đã
được nghiệm thu.

### Ghi nhận nhưng KHÔNG xử lý (**phát hiện không tự sinh ra task**)

1. Câu mô tả trong `TASK-PRA-003` mục (10) đang nói sai hành vi hiện tại
   (`Suspicious.ERP` không còn gây `CẦN KIỂM TRA`; hai mã `Pending.accounting_*`
   đã nghỉ hưu).
2. Tám mã ghi chú chi tiết của khâu nhận diện bị nén thành một chữ khi lưu, làm
   mất phân biệt giữa *"đã có người xem và kết luận"* và *"chưa ai đụng tới"*.
3. Bốn mã `Missing` / `Suspicious` / `EmployeeMapping` / `OrderInconsistency`
   gộp 16 tình huống vào 4 chữ, chi tiết không lưu xuống. **Sau bản sửa này
   điều đó không còn ảnh hưởng tới con số nào**, vì cửa chặn không đọc các mã
   đó nữa — nó chỉ còn ảnh hưởng tới độ chi tiết của phần ghi chú hiển thị.
4. Danh sách từ khoá hạ mức cảnh báo (chữ `"phí"`) — xem mục 6.

### Một điểm CẦN CHỦ DỰ ÁN XÁC NHẬN

**Dòng có số lượng ÂM có được cộng vào lợi nhuận của cả kỳ không?**

Bản sửa này chọn **không** cộng, và giải thích lý do ở mục 7: cộng
`−1 × biên lợi nhuận` chính là khẳng định dấu âm nghĩa là hoàn hàng, tức là
phát minh đúng cái ngữ nghĩa mà `OD-2` cấm. Đây là phía thận trọng.

Nếu ý chủ dự án là *"vẫn vào tổng công ty, chỉ không vào KPI cá nhân"*, cho
biết là được — bản sửa sẽ rất nhỏ (một dòng trong bảng phân loại cửa chặn) và
đã có sẵn chỗ để đặt nó.

Đây là điểm **duy nhất** cần chủ dự án quyết. Năm tình huống còn lại mà bản
audit nêu (`OD-1` số lượng 0, `OD-3` dòng trùng, `OD-4` giá bán 0, `OD-5` chưa
rõ nhân viên, `OD-6` nhãn chung chung) đều đã được chủ dự án quyết và đã thi
hành đúng.

---

## 14. Bảng tổng kết

| Trường | Giá trị |
|---|---|
| `BASE_HEAD` | `60adb2ec22efdb4967d6971bbee852db660c8c18` (đã xác minh khớp) |
| `B01` — giá tay có hiệu lực kinh tế | **PASS** |
| `B02` — ô đếm dòng thiếu giá | **PASS** |
| `B03` — màn hình nói đúng nguyên nhân | **PASS** |
| `B04` — rollback an toàn | **PASS** |
| `MANUAL_PRICE_RECALCULATES_PROFIT` | **YES** |
| `GENERIC_PENDING_BLOCKS_PROFIT` | **NO** |
| `KPI_AUTHORITY_FAIL_CLOSED` | **PASS** (giữ nguyên `DEC-143` §1) |
| `SCOPE_DRIFT` | **NO** |
| Toàn bộ test | `2136 passed, 11 skipped` |
| Golden baseline | `74 passed, 2 skipped` |
| Cần chủ dự án quyết | **1** — số lượng âm có vào tổng công ty không (mục 13) |
