# PHB-04 — LEGACY REFERENCE V1 — BÁO CÁO CHO CHỦ DỰ ÁN (BẢN ĐÍNH CHÍNH)

Ngày: 2026-09-04 · Phiên: S119 (tiếp tục) · Nhánh:
`claude/phb-04-legacy-reference-v1-widtzf`

> **Bản này thay thế báo cáo PHB-04 trước đó.**
> Báo cáo trước kết luận *"với năm 2025 — đúng một chỉ tiêu: doanh số
> tháng."* Chủ dự án đã bác bỏ kết luận đó. **Kết luận đó SAI**, và bản này
> nói rõ nó sai ở đâu, vì sao, và đã sửa những gì. Kết luận cũ không được
> giữ lại ở bất kỳ chỗ nào trong tài liệu dự án.

---

## 1. Năm 2025 thật sự có dữ liệu gì?

Đây là kiểm kê đầy đủ, đọc từ chính hồ sơ bằng chứng của dự án
(`docs/analysis/_evidence/evidence.json`) và từ workbook cũ.

**Workbook có 59 sheet:**

```text
56 sheet chi tiết "tháng + nhân viên"   → TẤT CẢ đều là 2026 (01.2026 … 08.2026)
 1 sheet Summary 2026                   → bảng người bán × tháng, năm 2026
 1 sheet Summary 2025                   → bảng người bán × tháng, năm 2025
 1 sheet DataChart 2026                 → doanh số theo ngày + 12 ô doanh số 2025
```

Nói theo cách dễ hình dung:

- **2025 KHÔNG có sheet riêng cho từng nhân viên từng tháng.** Không có
  "06.2025 Vinh". Chỉ 2026 mới có kiểu sheet đó.
- **2025 CÓ một Summary riêng, và chi tiết theo nhân viên nằm TRONG chính
  Summary đó** — mỗi dòng là một (tháng, người bán) với đủ 16 cột, y như
  Summary 2026. Điều này khớp đúng với mô tả của chủ dự án: *"cấu trúc gần
  giống báo cáo 2026"*.
- Ngoài ra `DataChart` có thêm 12 ô doanh số tháng của 2025 (số gõ cứng, để
  làm mốc so với 2026).

**Về quy mô của Summary 2025:** sheet đó có **99 dòng mang số**. So sánh:
Summary 2026 có 71 dòng cho 8 tháng (~8,9 dòng/tháng); Summary 2025 có 99
dòng cho 12 tháng (~8,3 dòng/tháng). Hai mật độ khớp nhau — nhất quán với
một bảng người bán × tháng cùng hình dạng.

**Một điều phải nói thẳng:** con số 99 là số ĐẾM DÒNG. **Nội dung** của 99
dòng đó chưa từng được ghi lại trong repo — xem mục 13.

---

## 2. Vì sao bản trước chỉ thấy 12 con số của 2025?

Vì cả dây chuyền đọc dữ liệu đều **bám vào công thức Excel**, ở ba tầng độc
lập nhau, và Summary 2025 là một sheet **đã bị dán cứng thành giá trị** —
không còn một ô công thức nào.

| Tầng | Nó tìm gì | Gặp Summary 2025 thì sao |
|---|---|---|
| Công cụ trích bằng chứng | chỉ ghi dòng nào có **công thức** ở cột F | ghi được **0** dòng |
| Bộ nhập workbook | đoán "dòng này là người bán hay dòng tổng" từ **cấu trúc công thức** | không phân loại được dòng nào |
| Hợp đồng PHB-04 (bản trước) | dựng trên hai tầng trên | kết luận sai "2025 chỉ có doanh số tháng" |

Bằng chứng lạnh lùng nhất: file `evidence.json` — hồ sơ bằng chứng chính của
dự án — chứa **0 lần** chuỗi ký tự `"2025"`.

Nói gọn: đó là **kết luận về công cụ đọc**, bị trình bày nhầm thành **kết
luận về dữ liệu**. Dữ liệu 2025 vẫn nằm đó trong workbook; công cụ chỉ chưa
nhìn thấy nó.

---

## 3. `DEC-169` thật ra có nghĩa gì?

Nguyên văn quyết định cũ:

> *"Owner KHÔNG yêu cầu: import Summary 2025; persist; query; display; xây
> parser cho value-only rows của Summary 2025."*

**"Không yêu cầu" = "chưa cần". Nó KHÔNG phải "không được có".**

Chính `DEC-169` tự gọi mình là một *"làm rõ phạm vi"*, không phải một lệnh
cấm. Bản triển khai trước đã đọc rộng thành "bị cấm khỏi sản phẩm" — và đó
là lỗi diễn giải của phiên làm việc, không phải nội dung quyết định.

Chiếu theo bốn khả năng mà chủ dự án nêu:

| | Nghĩa | Đúng? |
|---|---|---|
| A | Không được dùng làm dữ liệu kế toán hiện hành | **ĐÚNG** — vẫn giữ |
| B | Không được dùng làm thước đo để đối chiếu số mới | **ĐÚNG** — vẫn giữ |
| C | Không đọc được bằng cách phân loại dòng theo công thức | **ĐÚNG** — vẫn giữ |
| D | Loại khỏi sản phẩm hoàn toàn, kể cả để tham chiếu | **SAI** — đây là chỗ đọc nhầm |

Quyết định mới `DEC-177` sửa đúng điểm `D` và **không** đụng vào `A`, `B`,
`C`.

---

## 4. Summary 2025 giờ có được hỗ trợ không?

**CÓ — về mặt năng lực. Còn thiếu dữ liệu nguồn.**

Sheet `Summary 2025` đã chuyển từ *"không đọc tới"* sang **`OPTIONAL_IMPORT`**:

- dòng nào công cụ xác định được ý nghĩa → **NHẬP**, dán nhãn
  `LEGACY_REFERENCE`;
- dòng nào chưa xác định được → **không đoán**, nhưng cũng **không im lặng
  bỏ qua**: đếm lại và hiện lên màn hình kèm số dòng cụ thể;
- dù thế nào cũng **không làm hỏng phần 2026** đang chạy tốt.

Điều cuối cùng quan trọng: mở phạm vi mà làm gãy phần đang chạy thì là một
bước lùi. Có test riêng khoá điều đó lại.

---

## 5. Chi tiết theo nhân viên 2025 có được hỗ trợ không?

**CÓ — về mặt năng lực, và không phải viết thêm gì cho phần hiển thị.**

Bảng lưu số cũ (`legacy_summary_row`) từ đầu đã lưu theo
*(năm, tháng, người bán, loại dòng)* với đủ 16 cột — và **không hề gắn với
năm 2026**. Trang "Nhân viên" cũng vậy: nó không giả định năm nào.

Nghĩa là **ngay khi có dòng 2025 trong kho, trang chi tiết nhân viên phục vụ
2025 mà không cần sửa một dòng mã nào.** Điều này đã được chứng minh bằng
test chạy thật, không phải suy đoán.

Với dữ liệu mẫu đang có, chủ dự án trả lời được đúng những câu đã nêu:

- Tháng 01/2025 tổng bán bao nhiêu? → có
- Nhân viên nào có số trong kỳ? → có (và dòng "Tổng T01" **không** bị nhầm
  thành một nhân viên)
- Một nhân viên bán bao nhiêu, DS quy đổi, lợi nhuận lịch sử? → có
- Target / So target lịch sử? → có, **nếu** ô đó có số trong file

---

## 6. Những chỉ số lịch sử nào có?

Câu trả lời quan trọng: **công cụ không còn trả lời câu này bằng một danh
sách viết sẵn.** Nó **ĐẾM trên chính dữ liệu đã nhập của từng năm** và hiện
ra ba trạng thái:

| Trạng thái | Nghĩa |
|---|---|
| Có, kèm bằng chứng đã chấp nhận | ô có số, và ý nghĩa chỉ tiêu đã được chốt |
| Có số, nhưng ý nghĩa chưa chắc | ô có số, nhưng dự án chưa chốt cách hiểu |
| Không có | cột tồn tại nhưng mọi ô đều trống |

Đây là điểm sửa quan trọng nhất về mặt phương pháp: bản trước **viết cứng**
"2025 không có X". Bản này **đo** và báo cáo. Nếu workbook thật của chủ dự
án giàu hơn dữ liệu mẫu, màn hình sẽ tự phản ánh điều đó — không cần ai sửa
mã.

Với một sheet Summary bất kỳ (2025 hay 2026, cùng 16 cột nên cùng cách đọc),
những chỉ tiêu dự án đã chốt cách hiểu là: Tổng đơn · Tổng số SP · Tổng bán ·
DS quy đổi · Tổng lợi nhuận · So tháng trước · Target · So target · Tỉ suất ·
Lợi nhuận thực nhận.

---

## 7. Chỉ số nào chỉ để tham khảo?

**Tất cả** — nhưng xin đọc kỹ câu này, vì nó khác hẳn câu ở bản trước.

"Chỉ để tham khảo" ở đây có nghĩa: **xem được đầy đủ, nhưng không đem trừ
với số của công cụ hiện tại để ra phần trăm tăng trưởng.** Nó **KHÔNG** có
nghĩa là ẩn đi hay không hỗ trợ.

Bản trước đã trộn lẫn hai chuyện này, và đó là một phần của cái sai. **Hiển
thị** và **so sánh** là hai câu hỏi khác nhau.

Lý do không so được vẫn như cũ, và vẫn đứng vững: báo cáo tay trừ chiết khấu
khác cách công cụ mới trừ; lợi nhuận cũ dựa trên giá nhập sửa tay; DS quy
đổi cũ có kỳ cộng thiếu người bán. Đây là những khác biệt **đã được chốt từ
trước**, không phải lỗi mới.

---

## 8. Chỉ số nào không đủ bằng chứng?

Theo hợp đồng, các cột lương/thưởng (Thưởng, Ngày công, Lương cơ bản, Phụ
cấp, Tổng lương) và Tỉ lệ tồn kho vẫn nằm ngoài phiên bản này — cột "Nơi
nhập" không tồn tại trong file ERP, còn lương/thưởng thuộc luật nhân sự đã
hoãn.

Ngoài ra, với **từng năm cụ thể**, chỉ tiêu nào mà mọi ô đều trống sẽ hiện
**dấu gạch `—`**, kèm câu giải thích. **Không bao giờ hiện số 0.** Một số 0
bịa ra nguy hiểm hơn một ô trống: ô trống thì ai cũng biết là thiếu, còn số
0 trông như một sự thật.

---

## 9. Chủ dự án xem 2025 thế nào?

Tab **"Lịch sử"**, đi từ trên xuống:

1. **Chuỗi doanh số tháng của năm trước** — 12 ô lấy từ DataChart.
2. **Năm lịch sử đã nhập** — với mỗi năm (2025, 2026…):
   - những tháng có số, **mỗi tháng là một liên kết bấm được**;
   - có chi tiết theo nhân viên hay không, và gồm những ai;
   - bảng tình trạng từng chỉ tiêu, kèm số ô thực sự có giá trị;
   - nếu còn dòng chưa đọc được → **nói thẳng còn bao nhiêu dòng, ở dòng số
     mấy**.
3. **Đi tới kỳ** — mỗi kỳ dán nhãn `SỐ CŨ` / `SỐ MỚI` / cả hai.
4. **So số cũ với số mới ở đâu?** — bảng phán quyết từng cặp kèm lý do.
5. **Chỉ tiêu lịch sử nào được hỗ trợ?** — hợp đồng in nguyên văn.

Luồng chủ dự án yêu cầu:

```text
Lịch sử → chọn năm → bấm một tháng → bảng người bán × chỉ tiêu của tháng đó
```

Bước cuối dùng lại trang "Nhân viên" đã có — không dựng trang mới, không tái
tạo các tab của bảng tính cũ.

Mọi con số vẫn đeo nhãn `LEGACY` và có dòng chữ nói rõ đây là **số liệu tham
chiếu lịch sử**, không phải số do công cụ hiện tại tính.

---

## 10. Việc này có làm đổi dữ liệu hiện tại không?

**Không.** Bốn lý do, và lần này có thêm bằng chứng đo được:

1. **Không có bảng mới, không nâng cấp cơ sở dữ liệu, không thêm cột.** Kho
   cũ vốn đã lưu được cả số theo kỳ lẫn số theo nhân viên cho mọi năm.
2. **Hai kho tách biệt**, và cơ sở dữ liệu tự ép nhãn `LEGACY_REFERENCE` ở
   tầng cấu trúc.
3. **Đã đo:** nạp một bản legacy rồi tính lại toàn bộ kỳ hiện hành —
   coverage giá nhập, doanh thu, số dòng **giống hệt trước khi nạp**.
4. **Trang "Lịch sử" không ghi gì**: mở trang hai lần, đếm dòng của **mọi
   bảng** không đổi một đơn vị.

Những thứ không bị đụng tới: dòng hàng kế toán · Product Identity · Tracking
· lịch sử giá nhập · các lần chủ dự án sửa tay ở PHB-03 · gán nhân viên ·
phân loại Gia dụng · snapshot đã lưu.

Một điều nữa cần khẳng định vì nó là hàng rào an toàn quan trọng nhất của
bản nhập: **hàng rào chống bỏ sót dữ liệu 2026 KHÔNG bị nới lỏng.** Với
sheet 2026, một dòng có số mà công cụ không hiểu vẫn làm cả lần nhập dừng
lại và báo lỗi. Chỉ với sheet lịch sử, việc chưa đọc được mới là *"đếm và
báo"* thay vì *"dừng"* — vì thiếu một dòng 2026 nghĩa là số hiện tại sai,
còn thiếu một dòng lịch sử nghĩa là còn một phần chưa đọc được.

---

## 11. Test nào chứng minh?

```text
Test riêng của PHB-04   tests/test_phb04_legacy_reference.py   50 passed
Toàn bộ hệ thống        python -m pytest -q                    2187 passed, 11 skipped
Test golden             4 file golden                          74 passed, 2 skipped (KHÔNG ĐỔI)
```

Mười câu hỏi của chủ dự án được khoá bằng mười test đặt tên theo đúng câu
hỏi: tổng bán một tháng 2025 · các chỉ tiêu Summary khác · nhân viên nào có
số · chỉ tiêu của một nhân viên · mọi giá trị vẫn là `LEGACY_REFERENCE` ·
không nhiễm coverage hiện hành · đi được từ Summary 2025 sang chi tiết nhân
viên · chỉ tiêu thiếu hiện `—` chứ không phải 0 · tính sẵn có được ĐO chứ
không viết cứng · không sinh phần trăm so hai nguồn.

**10 test cũ đã được sửa** vì chúng khoá phạm vi cũ của `DEC-169` (ví dụ:
"Summary 2025 không bao giờ được lưu"). Chúng được **cập nhật, không bị
xoá**, và danh sách đầy đủ nằm ở `docs/tasks/PHB-04-legacy-reference-v1.md`
mục 8b. **Không hàng rào an toàn nào bị hạ** — ngược lại, có thêm một test
mới khẳng định hàng rào 2026 vẫn nổ đúng lúc.

---

## 12. Còn Owner decision nào cần không?

**Không có quyết định nghiệp vụ nào đang chặn.** `DEC-177` đã đóng câu hỏi
phạm vi. Hai câu hỏi mở rộng vẫn ghi lại, không chặn gì:

- **`OD-PHB04-A`** — kỳ có **cả** số cũ **và** số mới: có bao giờ cần một
  con số duy nhất không, và nguồn nào thắng?
- **`OD-PHB04-B`** — có tháng 2026 nào muốn coi là "legacy thuần" không?

Nhắc lại một điểm dễ hiểu nhầm: **ranh giới legacy / hiện hành không phải
một cái mốc ngày.** Trong toàn bộ hồ sơ dự án không có quyết định nào đặt ra
một ngày như vậy cho báo cáo. Cái thật sự tồn tại là ranh giới **theo nguồn
dữ liệu, tính riêng từng kỳ**. Phiên này không bịa ra ngày nào — mốc
`2026-09-01` đã có là mốc về **giá nhập**, và hồ sơ đã ghi rõ *"hai cutover,
không gộp"*.

---

## 13. Cái duy nhất còn thiếu: nội dung thật của Summary 2025

```text
NEED_OWNER_SOURCE = nội dung thật của sheet `Summary 2025`
```

**Năng lực đã sẵn sàng và đã có test. Dữ liệu thì chưa có trong repo.**

Workbook `Báo cáo Kinh doanh 2026.xlsx` **không** được lưu trong kho mã
(đúng như thiết kế: nó chứa tên, số điện thoại và địa chỉ khách hàng), và
không có trên máy chạy phiên này. Vì vậy nội dung 99 dòng của Summary 2025
chưa từng được bất kỳ hồ sơ bằng chứng nào của dự án ghi lại.

Chủ dự án cần cấp **một trong hai** (không cần cả hai):

**Cách 1 — gửi workbook thật.** Nếu Summary 2025 còn giữ công thức, công cụ
đọc được **ngay**, không phải sửa mã. Đây là đường ngắn nhất.

**Cách 2 — nếu sheet đó thật sự không còn công thức nào:** cần **nội dung
cột nhãn (cột A/B) của 99 dòng** — tức mỗi dòng ghi chữ gì: "Mr Vinh",
"Tổng T01", v.v. Có danh sách đó là dựng được cách phân loại dòng theo nhãn.

**Vì sao không tự đoán ngay bây giờ.** Chưa ai trong phiên này nhìn thấy
cách sheet đó ghi nhãn. Viết luật đọc cho một sheet chưa từng thấy là đoán —
và đoán sai một dòng tổng thành một người bán sẽ dựng ra một "nhân viên"
không có thật, làm sai lệch đúng loại số mà chủ dự án dùng để đánh giá người
thật. Vì vậy công cụ nói thẳng còn bao nhiêu dòng chưa đọc được, thay vì
đoán bừa.

Trong lúc chờ, hành vi trên workbook thật là: **2026 nhập bình thường**,
phần Summary 2025 báo rõ còn bao nhiêu dòng chưa đọc được và ở dòng số mấy.

---

## 14. Trạng thái PHB-04

```text
PHB_04 = IMPLEMENTED_AWAITING_REVIEW   (phần năng lực — đã xong, đã có bằng chứng)
       + OWNER_SOURCE_REQUIRED         (phần nội dung Summary 2025 — mục 13)
```

Phần triển khai đã xong. Còn thiếu **một lượt review độc lập** (do phiên
khác thực hiện) và **nguồn dữ liệu 2025**. Chưa có review độc lập thì chưa
được gọi là `DONE`.

---

## 15. Bước tiếp theo

1. **Chủ dự án cấp nguồn 2025** theo mục 13 — workbook thật, hoặc danh sách
   nhãn cột A/B của Summary 2025.
2. **Review độc lập PHB-04** — kiểm lại cách đọc `DEC-169`, hợp đồng chỉ
   tiêu, phần tách biệt legacy/hiện hành, và 50 test.
3. Sau đó: **PHB-05 — Target**.

Việc dọn dẹp R1/R2/R3 của PHB-03 vẫn ở nhánh phụ không chặn.
