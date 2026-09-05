# PHB-04 — Legacy Reference V1: Báo Cáo Review Độc Lập

**Người review:** phiên độc lập (KHÔNG phải phiên đã triển khai PHB-04).
**Ngày:** 2026-09-05
**Vai trò:** INDEPENDENT REVIEWER — chỉ đọc, không sửa mã sản phẩm, không vá
lỗi, không merge, không deploy.

Báo cáo này viết cho chủ dự án đọc, không cần biết kỹ thuật. Mỗi mục trả lời
đúng một câu hỏi.

Một điều xin nói trước cho thẳng thắn: tôi **không tự tin vì bản báo cáo
triển khai nói rằng test đã xanh**. Tôi đã tự chạy lại toàn bộ test, tự dựng
lại hai workbook có số liệu lệch nhau, tự nạp chúng qua đúng nút "Tải lên"
của phần mềm, và tự mở trang web ra xem con số nào hiện lên. Những gì viết
dưới đây là điều tôi **tự đo được**, không phải điều tôi được kể lại.

---

## 1. Tôi đã review đúng commit nào?

```text
REVIEW_BRANCH  = claude/phb-04-legacy-reference-v1-widtzf
REVIEW_HEAD    = 6a0213d45931e3848103ab68fe302af10645aadd
EXPECTED_HEAD  = 6a0213d45931e3848103ab68fe302af10645aadd
WORKTREE       = sạch (không có thay đổi chưa lưu)
EXACT_TARGET   = PASS
```

Commit này mang tiêu đề *"PHB-04 (DEC-178): nguồn chuẩn lịch sử 2025 +
Summary/nhân viên 12 tháng"*. Tôi đã khoá mục tiêu review vào đúng mã băm đó,
và kiểm lại ở cuối phiên: **mã băm không đổi trong suốt quá trình review**,
nên mọi kết luận dưới đây gắn đúng vào bản mã này.

So với bản trước khi PHB-04 bắt đầu (`51d8fef`), thay đổi gồm 24 file:
4.642 dòng thêm, 137 dòng bớt.

---

## 2. Nguồn chuẩn 2025 có thật sự luôn thắng không?

**CÓ.** Đây là mục quan trọng nhất và tôi đã kiểm kỹ nhất.

Chủ dự án đã chốt (`DEC-178`): workbook `Báo cáo Kinh doanh 2025.xlsx` là
**nguồn chuẩn**; bản sao `Summary 2025` nằm trong workbook 2026 chỉ là **bằng
chứng đối chiếu**. Khi hai bên lệch nhau, bản độc lập thắng.

Tôi đã tự nạp cả hai workbook qua đúng đường người dùng thật (nút tải lên
trên trang Dữ liệu), rồi đọc số ra bằng đúng đường mà giao diện dùng:

| Điều kiểm | Kết quả tôi đo được |
|---|---|
| Nạp bản thứ cấp trước, nguồn chuẩn sau | số của **nguồn chuẩn** hiện ra |
| Nạp nguồn chuẩn trước, bản thứ cấp sau | số của **nguồn chuẩn** hiện ra |
| Nạp thêm bản thứ cấp 3 lần nữa | số **không đổi**, vẫn là nguồn chuẩn |
| Có bị lấy trung bình hai số không? | **Không** — luôn là một trong hai số nguồn, và luôn là số của bản chuẩn |
| Có phải "ai nạp sau thì thắng" không? | **Không** — đảo thứ tự vẫn ra cùng kết quả |

**Vì sao tôi tin điều này bền chứ không may mắn.** Quy tắc không nằm ở một
lời dặn trong tài liệu, cũng không dựa vào việc đặt tên file cho đúng. Nó nằm
ở **tầng đọc dữ liệu**: mỗi lần nạp workbook, hệ thống ghi vào cơ sở dữ liệu
một dấu "đây là nguồn chuẩn của năm" hay "đây là bản sao". Khi cần đọc số của
một năm, hệ thống **hỏi dấu đó trước**, rồi mới tính đến chuyện "đang xem bản
nào". Vì vậy không có đường nào để bản sao lặng lẽ thay chỗ bản chuẩn — kể cả
khi người dùng đổi tên file, hay nạp lại nhiều lần.

Một điểm nữa tôi đã kiểm và thấy làm đúng: nạp workbook 2025 **không** làm
biến mất các kỳ 2026. Trước khi nạp có 3 kỳ 2026; sau khi nạp vẫn đủ 3 kỳ
2026, cộng thêm các kỳ 2025 mới.

```text
SOURCE_PRECEDENCE = PASS
```

---

## 3. Một ô lệch thật giữa hai workbook cho kết quả nào?

Tôi đã dựng lại **đúng những con số mà chỉ thị nêu** cho tháng 12/2025 và cho
chúng chạy qua đường thật, tới tận trang web:

| Chỉ tiêu (Ly, T12/2025) | Nguồn chuẩn | Bản thứ cấp | Số hệ thống trả về |
|---|---|---|---|
| Tổng đơn | 105 | 104 | **105** |
| Tổng bán | 1.604.205 | 1.595.355 | **1.604.205** |
| Tổng lợi nhuận | 87.537 | 86.415 | **87.537** |
| Tổng bán cả tháng 12 | 23.016.871 | 23.097.181 | **23.016.871** |

Tôi **không** dừng ở việc gọi một hàm phụ trợ. Tôi đã mở trang
`Nhân viên → tháng 12/2025` và kiểm tận HTML mà trình duyệt nhận được: trang
hiện **105**, và **không** hiện 104. Đúng như vậy với **cả hai** thứ tự nạp
file.

Tôi cũng kiểm công cụ đối chiếu hai nguồn. Nó phân biệt "chỉ khác do làm
tròn" bằng **cơ chế** (`B == làm tròn của A`) chứ không bằng một ngưỡng do
người viết tự chọn. Tôi đã thử đúng bốn cặp số thật ở trên: **cả bốn đều bị
xếp là KHÁC BIỆT THẬT**, không cặp nào bị giấu vào rổ "chỉ là làm tròn". Đó
là điều quan trọng — một đơn hàng lệch (105 so với 104) không bao giờ được
phép biến mất dưới danh nghĩa làm tròn.

```text
REAL_CONFLICT_PRECEDENCE      = PASS
SECONDARY_SOURCE_ISOLATION    = PASS
```

Bản thứ cấp **vẫn được giữ lại**, không bị xoá. Nếu sau này cần đối chiếu,
vẫn mở ra xem được. Nhưng nó không bao giờ là số mặc định, và hai bộ số không
bao giờ hiện chồng lên nhau thành một con số mơ hồ — tôi đã kiểm: khi đọc
"tất cả các dòng", các dòng của năm 2025 **chỉ đến từ một bản nhập duy nhất**,
và đó là bản chuẩn.

---

## 4. 74 dòng nhân viên + 12 dòng tổng có được phân loại đúng không?

**Có.** Và ở đây có một bằng chứng rất mạnh mà tôi muốn chỉ ra riêng.

Cách hệ thống phân loại một dòng **không** dựa vào việc "dòng đó có số hay
không" — nếu dựa vào đó thì dòng nào cũng thành nhân viên. Nó dựa vào **cấu
trúc công thức Excel** của chính dòng đó:

- dòng **nhân viên**: có công thức trỏ sang một sheet chi tiết khác;
- dòng **tổng tháng**: có công thức `SUM` cộng khối ngay phía trên;
- dòng **tiến độ**: có công thức chia hai ô trong cùng sheet;
- dòng không khớp gì cả: **không đoán** — báo lên để người thật quyết.

**Bằng chứng then chốt:** workbook 2025 có **74 sheet chi tiết**, và hệ thống
nhận ra **đúng 74 dòng nhân viên**. Hai con số này khớp nhau không phải ngẫu
nhiên — mỗi dòng nhân viên trỏ tới đúng một sheet chi tiết. Nếu có dòng nhân
viên nào bị bỏ sót, con số sẽ là 73 hoặc ít hơn. **74 = 74 chứng minh không
một dòng nhân viên/tháng nào bị mất im lặng.** Tôi đã kiểm lại chính bất biến
này trên dữ liệu mô phỏng và nó giữ đúng.

Tôi cũng đã kiểm trực tiếp:

- Dòng **tổng tháng có bị nhầm thành nhân viên không?** Không — chúng có
  loại riêng, và ô tên người bán của chúng để trống.
- **Số tổng của workbook có bị thay bằng phép cộng các dòng nhân viên
  không?** Không. Tôi cố tình dựng một workbook mà ô tổng ghi 1.200.000 trong
  khi cộng các nhân viên ra 1.500.000 (đúng kiểu báo cáo tay cộng thiếu một
  người — lỗi đã biết từ trước). Hệ thống lưu **1.200.000**, tức **giữ nguyên
  con số workbook đã ghi**, không tự tính lại.
- **Ô trống có bị biến thành số 0 không?** Không. Các cột lương/thưởng/tồn
  kho không có số thì trả về "chưa có", và trên màn hình hiện dấu gạch `—`,
  không phải `0`.

```text
SUMMARY_ROW_CLASSIFICATION = PASS
```

---

## 5. Sáu dòng KPI cuối năm bị loại có đúng không?

**Đúng, và đây là một quyết định tốt chứ không phải một chỗ bỏ sót.**

Dưới 12 khối tháng, sheet Summary của workbook 2025 có một khối tổng kết cuối
năm mở đầu bằng ô ghi chữ **"Tổng KPI"**. Ở khối đó, các cột **đổi nghĩa
hoàn toàn**: cột vốn là "Tổng đơn" trở thành "Tổng KPI", cột vốn là "Tổng số
SP" trở thành "KPI trung bình".

Nếu nhập chúng vào cùng bộ cột, hệ thống sẽ ghi ra những câu vô nghĩa kiểu
**"Tổng đơn của Ly = 10,79"**. Đó không phải điều báo cáo cũ muốn nói. Loại
chúng ra là đúng.

Trả lời từng câu hỏi mà chỉ thị đặt ra:

| Câu hỏi | Trả lời |
|---|---|
| A. Đúng sáu dòng bị loại? | Bản triển khai ghi `recap_rows_excluded = 6` trên file thật. Tôi **không có file thật** để đếm lại (xem mục 12), nhưng cơ chế ghi số này là tự động, không gõ tay. |
| B. Chúng nằm ngoài 12 khối tháng? | **Có** — và tôi chứng minh được gián tiếp mà không cần file: nếu khối KPI nằm chen giữa các khối tháng, số dòng nhân viên nhận ra được sẽ nhỏ hơn 74. Nó đúng bằng 74. |
| C. Các cột có thật sự đổi nghĩa? | **Có** — tiêu đề do chính workbook viết ra ("Tổng KPI", "KPI trung bình"). |
| D. Nhập chúng có tạo ra sự thật giả không? | **Có** — nên phải loại. |
| E. Có loại tường minh hay bị bỏ qua im lặng? | **Tường minh** — số dòng bị loại được ghi lại vào bản ghi lần nhập và kiểm chứng được. |
| F. Loại chúng có làm mất chỉ tiêu nào cần cho Level 1/2 không? | **Không** — Level 1 là 12 dòng tổng tháng, Level 2 là 74 dòng nhân viên/tháng. Cả hai đều đủ. |

```text
YEAR_END_KPI_EXCLUSION = PASS
```

Tôi có **một lưu ý kỹ thuật** về độ bền của quy tắc này — không chặn PHB-04,
nhưng nên biết. Xem `F-REV-01` ở mục 12.

---

## 6. Bảy dòng tiến độ có ảnh hưởng số liệu không?

**Không.** Tôi đã kiểm và thấy chúng bị cô lập đúng cách.

Bảy dòng này ghi "tháng đã qua bao nhiêu ngày trên tổng số ngày" — một tỉ lệ
tiến độ, không phải một con số bán hàng. Chúng dùng chung ô với cột "Tổng
đơn", nên nếu xử lý cẩu thả thì một tỉ lệ như `0,97` có thể bị đọc thành
"Tổng đơn = 0,97".

Bảo vệ thực tế trong mã:

1. Chúng được lưu **không gắn với tháng nào**. Vì mọi khung nhìn theo kỳ đều
   đòi phải có tháng, chúng **tự nằm ngoài** mọi bảng người dùng nhìn thấy.
   Tôi đã kiểm: mở tháng bất kỳ của 2025, **không có dòng tiến độ nào** trong
   kết quả.
2. Chúng bị **loại khỏi phép đo "chỉ tiêu nào có số"**, nên một tỉ lệ tiến độ
   không bị đếm như một ô "Tổng đơn có giá trị".
3. Mọi kỳ trong danh sách kỳ đều có tháng — tôi đã kiểm, không có ngoại lệ.

Ba tính chất mà chỉ thị nêu đều giữ, nên `F-PHB04-03` được để **không chặn**
là hợp lý.

```text
PROGRESS_ROW_ISOLATION = PASS
```

---

## 7. Migration mới có an toàn không?

**Có.** Đây là loại thay đổi cơ sở dữ liệu nhẹ nhất có thể: **thêm đúng một
cột, cho phép để trống, trên đúng một bảng**. Không bảng mới, không xoá, không
viết lại dữ liệu cũ.

Tôi **không** chỉ đọc mã và tin. Tôi đã dựng một cơ sở dữ liệu ở đúng phiên
bản đang chạy trên production trước đây (`0004`), gỡ cột mới ra để tái hiện
đúng trạng thái production thật, nhét vào đó một bản ghi cũ, rồi chạy nâng
cấp thật:

| Điều kiểm | Kết quả |
|---|---|
| Nâng cấp từ đúng phiên bản production trước đó | **Thành công** |
| Dòng dữ liệu cũ còn nguyên sau nâng cấp | **Còn nguyên**, kể cả cờ "đang xem" |
| Có ghi đè/viết lại bảng cũ nào không | **Không** |
| Chạy lại nâng cấp lần hai | **Thành công**, không tạo cột trùng |
| Hạ cấp (rollback) rồi nâng lại | **Cả hai chiều đều chạy**, dữ liệu không mất |
| Ứng dụng khởi động được sau nâng cấp | **Được** |

Việc rollback an toàn ở đây có lý do rõ: giá trị của cột mới **tái tạo được
hoàn toàn** từ chính file workbook khi nạp lại — nó do máy suy ra, không phải
một quyết định con người gõ tay. Nên xoá cột không làm mất công sức của ai.

```text
MIGRATION_SAFETY = PASS
```

Tôi có một lưu ý về **độ phủ test** của migration này — xem `F-REV-02` ở mục
12. Bản thân migration chạy đúng; chỗ thiếu là một bài test tự động cho đúng
tình huống production.

---

## 8. Dữ liệu legacy cũ trước migration có an toàn không?

**Có.** Đây là câu hỏi tôi coi là nguy hiểm nhất, vì nếu sai thì dữ liệu
production cũ có thể **thắng nhầm** nguồn chuẩn mới.

Bản ghi được tạo **trước** quyết định `DEC-178` không mang dấu thẩm quyền
(cột mới để trống). Câu hỏi: một bản ghi như thế được hiểu là gì?

Tôi đã dựng đúng tình huống đó: nạp workbook 2026 (chứa bản sao 2025), rồi
**ép cột thẩm quyền về trống** để giả lập một bản nhập có từ trước, rồi mới
nạp nguồn chuẩn 2025.

```text
trước khi nạp nguồn chuẩn : Tổng đơn = 38   (số của bản cũ)
sau khi nạp nguồn chuẩn   : Tổng đơn = 41   (số của nguồn chuẩn)
```

**Nguồn chuẩn thắng.** Cơ chế rất rõ ràng: quy tắc tìm nguồn chuẩn chỉ chấp
nhận bản ghi mang **đúng** dấu "nguồn chuẩn của năm". Một ô trống **không bao
giờ** khớp điều kiện đó, nên bản ghi cũ không thể giành quyền. Nó chỉ được
đọc khi năm đó **chưa có** nguồn chuẩn nào — đúng như trước đây.

Không cần chạy backfill, không cần đoán ý nghĩa dữ liệu cũ. Hành vi của các
bản nhập cũ **giữ nguyên y như trước**.

```text
PREEXISTING_LEGACY_COMPATIBILITY = PASS
```

---

## 9. Legacy có thể làm thay đổi CURRENT_ENGINE không?

**Không.** Tôi kiểm bằng hai cách độc lập nhau.

**Cách 1 — đo trực tiếp.** Tôi nạp workbook legacy **bốn lần** (cả hai
workbook, cả nạp lặp), rồi so **nội dung đầy đủ** của toàn bộ 9 bảng thuộc
engine hiện tại trước và sau. Không phải chỉ đếm số dòng — tôi so từng dòng
từng cột:

```text
source_snapshot · order_line_source_version · snapshot_line ·
order_line_result_version · order_line_current · reconciliation_flag ·
kpi_purchase_price_override · product_group_classification ·
employee_attribution_override
```

**Tất cả: NỘI DUNG GIỐNG HỆT trước và sau.**

**Cách 2 — ranh giới bằng cấu trúc.** Tôi phân tích mã nguồn để xem phần đọc
workbook cũ có gọi tới phần tính toán hiện tại không. Kết quả:

```text
app/legacy/models.py           → chỉ thư viện chuẩn Python
app/legacy/defects.py          → chỉ thư viện chuẩn Python
app/legacy/parser.py           → chỉ openpyxl (đọc Excel) + chính nó
app/web/legacy_reference.py    → chỉ thư viện chuẩn Python
```

**Không một dòng nào** đụng tới Product Identity, Tracking, lịch sử giá nhập,
lợi nhuận KPI, coverage, phân bổ nhân viên, hay phân loại Gia dụng. Đây không
phải lời hứa — đây là điều **không thể xảy ra** vì đường dẫn không tồn tại.

Ngoài ra, bộ test của bản triển khai có bài kiểm tra thật với dữ liệu engine
đã nạp: nạp workbook 2025 rồi so lại doanh thu, coverage, lợi nhuận KPI, và
**giá nhập chủ dự án đã sửa tay** — tất cả không đổi. Tôi đã chạy lại và
chúng xanh.

```text
CURRENT_ENGINE_ISOLATION = PASS
CURRENT_REVENUE · CURRENT_PROFIT · CURRENT_COVERAGE · MANUAL_PP ·
EMPLOYEE_ATTRIBUTION · GIA_DUNG · CURRENT_SNAPSHOTS = UNCHANGED
```

**Xin nhấn mạnh một phân biệt quan trọng.** "Nguồn chuẩn 2025 thắng bản sao
2025" là quy tắc **bên trong dữ liệu lịch sử**. Nó **không** cho phép dữ liệu
lịch sử ghi đè lên số của engine hiện tại. Hai câu hỏi hoàn toàn khác nhau,
và bản triển khai giữ đúng ranh giới đó. Tôi đã kiểm trang `Lịch sử`: một kỳ
có **cả** số cũ **và** số mới hiện thành **một dòng với hai nhãn riêng và hai
đường dẫn riêng** — không có con số gộp nào được sinh ra.

```text
CROSS_ENGINE_COMPARISON_GATE = PASS
LEGACY_NAVIGATION            = PASS
HISTORY_UI_READ_ONLY         = PASS
```

Về **chỉ-đọc**: tôi mở các trang `Lịch sử`, `Nhân viên`, `Dữ liệu`,
`Doanh số ngày`, `Kỳ` — mỗi trang nhiều lần — rồi so lại số dòng của **mọi
bảng** trong cơ sở dữ liệu. **Giống hệt trước và sau.** Xem báo cáo lịch sử
không ghi gì cả.

Về **so sánh**: hệ thống có một "cổng so sánh" thật, đọc từ bảng hợp đồng chứ
không phải một câu trả lời cứng. Ở phiên bản này **chưa chỉ tiêu nào** được
chứng minh là cùng nghĩa giữa số cũ và số mới, nên **không tỉ lệ tăng trưởng
nào được sinh ra**. Trang web nói thẳng "Không so được" kèm lý do cho từng
cặp. Đây là cách làm đúng: hiển thị được và so sánh được là hai chuyện khác
nhau.

---

## 10. Level 3 hoãn có hợp lý không?

**Có.** Hoãn là hợp lệ, không chặn.

Phạm vi PHB-04 V1 được đóng khung từ đầu ở hai mức:

- **Level 1** — Summary theo tháng: tôi đã kiểm, **đủ cả 12 tháng**, không
  thiếu tháng nào.
- **Level 2** — Summary theo nhân viên/tháng: tôi đã kiểm, mở được, đúng
  tháng, đúng nhãn người bán, chỉ tiêu giữ nguyên.

Level 3 (74 sheet chi tiết, khoảng 62.802 dòng, 6 biến thể bố cục) là **có
điều kiện**, không bắt buộc. Tôi đã kiểm bốn điều mà chỉ thị yêu cầu:

| Điều kiểm | Kết quả |
|---|---|
| Level 1/2 có phụ thuộc Level 3 không? | **Không** — chúng đọc từ sheet Summary, độc lập hoàn toàn |
| Có hiển thị chi tiết dòng bán hàng giả không? | **Không** — không có ô dữ liệu nào của 74 sheet đó được đọc |
| Sự tồn tại của các sheet có được ghi nhận không? | **Có** — tên từng sheet được lưu với ghi chú "chưa nhập, 0 dòng", và trang Lịch sử hiện rõ "còn N sheet chi tiết — cố ý chưa nhập" |
| Hoãn có làm mất dữ liệu mà hợp đồng PHB-04 đòi không? | **Không** |

Lý do hoãn cũng đúng chỗ: mọi biến thể bố cục đều có **tên khách hàng, số
điện thoại, địa chỉ**. Đưa hàng chục nghìn dòng như vậy vào kho dữ liệu là
một quyết định về **bảo vệ dữ liệu cá nhân**, cần chủ dự án quyết riêng — chứ
không phải một chi tiết kỹ thuật mà phiên triển khai được tự định đoạt. Tôi
**không** đề xuất mở một hạng mục kiến trúc riêng tư mới; chỉ ghi nhận rằng
việc hoãn được trình bày là "có chủ đích", không phải "bị bỏ quên".

```text
LEGACY_LINE_DETAIL_2025 = DEFERRED_NON_BLOCKING
BESTSTAFF               = OUT_OF_SCOPE
```

`BestStaff` là bảng thi đua nhân viên theo quý — một tính năng xếp hạng nhân
sự, nằm ngoài phạm vi báo cáo lịch sử. Sự tồn tại của sheet đó **không** làm
nó thành việc phải làm.

**Về danh sách tên người bán 2025** (Ly · Thắng · Tín Phát · Hoàng · Kiên ·
Quân · Miền Bắc · Khác · Gia dụng · Nội thành): tôi lưu ý rằng một số tên
trong đó có vẻ là **kênh bán hoặc nhóm hàng**, không phải nhân viên nhân sự
("Miền Bắc", "Khác", "Gia dụng", "Nội thành"). Tôi đã kiểm và thấy hệ thống
làm **đúng điều cần làm**: nó giữ nguyên **nhãn mà workbook đã ghi**, không
tự diễn giải chúng thành một khái niệm nhân sự mới, không gộp, không tách.
Ý nghĩa lịch sử được bảo toàn nguyên trạng.

```text
LEGACY_LEVEL_1              = PASS
LEGACY_LEVEL_2              = PASS
LEGACY_METRIC_PRESERVATION  = PASS
```

Về **giữ nguyên chỉ tiêu**: tôi đã kiểm rằng số nguồn được lấy nguyên trạng,
không tính lại bằng công thức hiện hành (có cả một bài test cấu trúc cấm phép
nhân/chia trong phần đọc workbook, tôi đã chạy và nó xanh); ô trống không bị
ép thành 0; và các cột lương/thưởng/ngày công/tồn kho **không** bị diễn giải
theo luật nghiệp vụ hiện tại — chúng được đánh dấu "có số nhưng ý nghĩa chưa
chắc", tức không giấu số của chủ dự án mà cũng không nâng nó lên thành chỉ
tiêu chính thức. Bảng "chỉ tiêu nào có số" cũng được **đo trên chính dữ liệu
đã nạp**, không phải một danh sách viết cứng trong mã.

```text
PROVENANCE_UX = PASS
```

Mọi số cũ đều mang nhãn nguồn gốc. Trang lịch sử ghi rõ từng năm đang đọc từ
file nào và đó là "Nguồn chuẩn của năm" hay "Bản sao trong workbook năm
khác". Tôi đã kiểm HTML thật: **không** có nhãn nào của engine hiện tại
(`AUTO_CALCULATED`, `ERP_RECONCILED`, `CURRENT_ENGINE`) xuất hiện trên trang
số cũ. Không con số cũ nào đội lốt số mới.

---

## 11. Test có đi qua production path thật không?

**Có.** Tôi đã tự chạy lại toàn bộ, và cũng đọc mã test để xem chúng kiểm
thứ gì.

Kết quả tôi chạy được (không phải con số được báo cáo lại):

```text
PHB-04 tập trung   : 79 passed
Toàn bộ test suite : 2216 passed, 11 skipped
Golden (4 file)    : 74 passed, 2 skipped
Golden baseline    : 58 passed, 2 skipped   (mốc canonical — KHÔNG ĐỔI)
Migration DB       : 17 passed
PHB-03 liên quan   : 130 passed
```

Mọi con số **khớp đúng** với bản báo cáo triển khai.

**Chất lượng test — điều tôi quan tâm hơn số lượng.** Tôi đã đọc và xác nhận
các bài test quan trọng **không** chỉ gọi hàm phụ trợ:

| Chủ đề | Test đi qua đâu |
|---|---|
| Thẩm quyền nguồn | tải file qua **HTTP thật** → repository thật → so số |
| Ô lệch nhau thật | tải cả hai file, cả hai thứ tự, đọc bằng đường của giao diện |
| Loại khối KPI | tải file thật qua HTTP, đọc bản ghi lần nhập từ DB |
| Migration | gọi **alembic thật** bằng tiến trình con, nâng cấp và hạ cấp thật |
| Thẩm quyền để trống | có kiểm; tôi tự kiểm lại lần nữa và nó đúng |
| Cô lập engine hiện tại | nạp dữ liệu engine thật, so doanh thu/coverage/KPI/giá nhập tay |
| Điều hướng | mở trang bằng test client thật, kiểm HTML nhận được |

Ngoài ra tôi kiểm riêng: **các bài test guard cũ có bị làm yếu đi không?**
Câu trả lời là **không**. Guard `DEC-168` (không đoán ý nghĩa dòng từ việc
dòng có số) vẫn nguyên vẹn trên các sheet bắt buộc — một sheet production có
dòng không đọc được vẫn làm cả lần nhập trượt. Các test bị đổi là đổi **phạm
vi** cho khớp `DEC-177`/`DEC-178`, và mỗi chỗ đổi đều ghi rõ lý do. Không
bài test guard nào bị xoá lặng lẽ.

```text
TEST_REACHABILITY = PASS
PHB03_REGRESSION  = PASS
SCOPE_DRIFT       = NO
```

**Về phạm vi:** tôi đã soát toàn bộ mã sản phẩm thay đổi. Ngoài phần legacy,
file duy nhất bị đụng là kho đọc dữ liệu lịch sử — đúng chỗ quy tắc thẩm
quyền phải sống. **Không** có PHB-05, Brand, Advanced Analytics, R1/R2/R3,
UX-PI-01, BestStaff, parser Excel tổng quát, kho dữ liệu lịch sử tổng quát,
thay đổi Tracking, thay đổi Product Identity, tối ưu giá nhập, hay ngữ nghĩa
tiền lương.

---

## 12. Finding còn lại

Ba điểm dưới đây **đều không chặn**. Theo kỷ luật review, **finding không tự
động tạo ra task** — tôi ghi lại để chủ dự án biết, không đề nghị mở việc
mới.

### F-REV-01 — Quy tắc loại khối KPI dựa vào vị trí, và không có chốt chặn

- **Bằng chứng:** `app/legacy/parser.py` — hệ thống tìm ô đầu tiên ghi
  "Tổng KPI", rồi loại **mọi dòng từ đó trở xuống**, **trước** khi phân loại.
  Tôi đã thử dựng một workbook có chữ "Tổng KPI" nằm ở phía trên: kết quả là
  **toàn bộ dữ liệu bị loại, không một lỗi nào được báo**.
- **Đường sản phẩm:** có — chạy khi tải workbook qua trang Dữ liệu.
- **Hệ quả nghiệp vụ:** nếu sau này có một workbook lịch sử bố cục khác đặt
  khối KPI ở vị trí khác, phần dữ liệu bên dưới sẽ bị bỏ **im lặng**, và cửa
  chặn `DEC-168` **không nổ** vì các dòng đó không bao giờ được phân loại.
- **Vì sao KHÔNG chặn PHB-04:** trên nguồn chuẩn thật của chủ dự án, khối KPI
  **thật sự nằm dưới cùng** — chứng minh được bằng chính con số 74 dòng nhân
  viên khớp đúng 74 sheet chi tiết, cộng 12 dòng tổng tháng, 0 dòng chưa phân
  loại. Với dữ liệu đang có, kết quả nhập là **đúng và đầy đủ**.
- **Mức độ:** TRUNG BÌNH. **BLOCKING = NO.**
- **Hành động đề xuất (nếu chủ dự án muốn):** thêm một chốt chặn — khối KPI
  phải nằm dưới khối tháng cuối cùng, nếu không thì báo lỗi thay vì bỏ im
  lặng.

### F-REV-02 — Nhánh migration mà production sẽ chạy chưa có test tự động

- **Bằng chứng:** trên mọi cơ sở dữ liệu dựng mới (tức mọi database mà test
  dùng), bước `0001` đã tạo sẵn cột mới, nên `0005` chỉ in ra "đã có sẵn" rồi
  thoát. Tôi đã chạy và xác nhận đúng như vậy. Nhánh **thật sự thêm cột** —
  chính là nhánh production sẽ đi — **không bài test nào chạm tới**.
- **Đường sản phẩm:** có — đây là bước nâng cấp production.
- **Hệ quả nghiệp vụ:** không có, **ở thời điểm này**. Tôi đã **tự chạy tay**
  đúng kịch bản production (dựng ở `0004`, gỡ cột, nâng cấp lên `0005`) và
  **nó chạy đúng**: cột được thêm, dòng cũ còn nguyên, hạ cấp và nâng lại đều
  được. Đây là lỗ hổng **độ phủ test**, không phải lỗi hành vi.
- **Mức độ:** TRUNG BÌNH. **BLOCKING = NO.**
- **Hành động đề xuất:** thêm một bài test bỏ cột đi rồi chạy `0005`.

### F-REV-03 — Một đoạn tài liệu cũ chưa được cập nhật

- **Bằng chứng:** `docs/tasks/PHB-04-legacy-reference-v1.md` mục 2E vẫn viết
  *"Nội dung thật của 99 dòng đó CHƯA TỪNG được quan sát"* và chỉ sang mục 10
  là `NEED_OWNER_SOURCE`. Nhưng mục 10 (viết sau) nói rõ
  `NEED_OWNER_SOURCE` **đã ĐÓNG** vì chủ dự án đã cấp hai workbook thật.
- **Đường sản phẩm:** không — chỉ là tài liệu.
- **Hệ quả nghiệp vụ:** chủ dự án đọc mục 2 có thể hiểu nhầm rằng dữ liệu
  2025 chưa từng được xem, trong khi nó đã được xem và đo đầy đủ.
- **Vì sao KHÔNG phải mâu thuẫn chưa giải quyết:** mục 10 **nói thẳng** rằng
  nó thay thế trạng thái cũ, và nói đúng chiều. Chuỗi quyết định
  `DEC-169 → DEC-177 → DEC-178` mạch lạc, không có chỗ nào để lửng.
- **Mức độ:** THẤP. **BLOCKING = NO.**

```text
DECISION_CHAIN = PASS
```

Tôi xác nhận cả ba quyết định được đọc đúng như chỉ thị nêu:
`DEC-169` là **làm rõ phạm vi** ("chưa cần"), **không** phải lệnh cấm vĩnh
viễn; `DEC-177` là **đính chính của chủ dự án** mở rộng hỗ trợ 2025;
`DEC-178` chốt workbook độc lập là **nguồn chuẩn lịch sử**. Tài liệu trạng
thái hiện hành (`PROJECT/PROJECT_PROGRESS.md`) đã ghi đúng và đã gỡ kết luận
sai của bản đầu.

### Một ghi chú về giới hạn của chính bản review này

Tôi phải nói rõ để chủ dự án không hiểu nhầm mức độ chắc chắn:

**Hai workbook thật KHÔNG có trong phiên review này.** Chúng bị loại khỏi kho
mã (đúng như phải thế — chúng chứa dữ liệu cá nhân khách hàng). Vì vậy tôi
**không thể tự đếm lại** 76 sheet, 1005 công thức, hay 1132 ô đối chiếu.

Những gì tôi **đã tự kiểm được** thay cho việc đó:

- toàn bộ **cơ chế** xử lý, trên dữ liệu **cùng hình dạng** với nguồn thật;
- đúng những **con số lệch thật** mà chỉ thị nêu (105/104, 23.016.871 /
  23.097.181), chạy qua đường sản phẩm thật đến tận trang web;
- **tính nhất quán nội tại** của các con số được báo cáo — đặc biệt bất biến
  **74 dòng nhân viên = 74 sheet chi tiết**, thứ không thể khớp ngẫu nhiên
  nếu có dòng bị bỏ sót.

```text
SOURCE_A_STRUCTURE = PASS
```

Tôi kết luận PASS cho cấu trúc nguồn dựa trên tính nhất quán nội tại vừa nêu,
chứ **không** dựa trên việc tin lời báo cáo. Mục 15 dưới đây có một bước kiểm
trên môi trường thật để đóng nốt khoảng cách này.

---

## 13. Blocking finding

```text
BLOCKING_FINDINGS = NONE
```

Không có finding nào thoả đủ **cả bốn** điều kiện để bị coi là chặn:
(1) nằm trên đường sản phẩm hiện tại; (2) có hậu quả nghiệp vụ đáng tin;
(3) có bằng chứng đã được chấp nhận; (4) PHB-04 không thể hoàn tất an toàn
nếu không sửa.

Tôi **cố ý không** nâng những điều sau thành finding chặn, đúng theo kỷ luật
mà chỉ thị đặt ra: Level 3 hoãn; BestStaff hoãn; có thể diễn giải thêm chỉ
tiêu lịch sử trong tương lai; giao diện có thể đẹp hơn; parser có thể tổng
quát hơn; báo cáo đối chiếu nguồn có thể chi tiết hơn; kiến trúc dữ liệu cá
nhân có thể tốt hơn; mã có thể sạch hơn.

```text
OWNER_DECISIONS_REQUIRED = NONE
```

Hai câu hỏi được ghi lại (`OD-PHB04-A` — kỳ có cả số cũ và số mới có bao giờ
cần gộp thành một số duy nhất; `OD-PHB04-B` — có tháng 2026 nào muốn coi là
"legacy thuần") là **câu hỏi cho tương lai**, không phải điều kiện để PHB-04
V1 hoàn tất. Hợp đồng V1 đã trả lời được mà không cần chúng.

---

## 14. Kết luận review

```text
REVIEW_RESULT = PASS

PHB_04 = REVIEW_PASS_AWAITING_PRODUCTION_VERIFICATION
```

Tất cả 22 cửa bắt buộc đều PASS, không có finding chặn, không có trôi phạm
vi. Tôi **chưa** đánh dấu `DONE` — theo đúng chỉ thị, cần một bước kiểm nhỏ
trên môi trường thật trước đã (mục 15).

Nhận xét chung, nói thẳng: đây là một bản triển khai **cẩn thận hơn mức trung
bình**. Ba điểm tôi đánh giá cao nhất:

1. **Quy tắc thẩm quyền nguồn sống ở tầng truy vấn, không ở tài liệu.** Đây
   là khác biệt giữa "chúng tôi hứa bản sao không ghi đè bản chuẩn" và "không
   có đường nào để bản sao ghi đè bản chuẩn". Bản triển khai chọn vế thứ hai.
2. **Phân loại dòng dựa vào cấu trúc công thức, không dựa vào "dòng có số".**
   Nhờ đó có được bất biến 74 = 74, thứ tự nó chứng minh không dòng nào bị
   mất — mạnh hơn bất kỳ lời khẳng định nào.
3. **Từ chối đoán.** Ô trống không thành 0; dòng không đọc được thì đếm và
   báo lên chứ không im lặng; cột lương không bị diễn giải theo luật hiện
   hành; khối KPI bị loại tường minh kèm số dòng kiểm chứng được.

Bản báo cáo triển khai cũng **tự nhận sai** về kết luận ban đầu ("2025 chỉ có
12 con số") và giải thích đúng nguyên nhân, thay vì che đi. Điều đó làm tăng
độ tin cậy của phần còn lại.

---

## 15. Production verification tối thiểu cần làm

PHB-04 **chưa** được kiểm trên môi trường production thật. Cần một bước kiểm
**nhỏ và gọn** — không phải một buổi lễ triển khai.

Sáu việc, làm một lần, khoảng 10 phút:

```text
1. MIGRATION ĐÃ CHẠY
   Sau khi deploy, mở trang bất kỳ. Nếu ứng dụng khởi động được thì migration
   đã chạy xong (hệ thống tự chặn nếu chưa).

2. TRANG LỊCH SỬ MỞ ĐƯỢC
   Bấm tab "Lịch sử" trên thanh menu. Trang phải hiện ra, không báo lỗi.

3. NGUỒN CHUẨN 2025 NHÌN THẤY ĐƯỢC
   Nạp `Báo cáo Kinh doanh 2025.xlsx` qua trang Dữ liệu.
   Thông báo phải ghi: "nguồn CHUẨN của năm 2025".
   Trên trang Lịch sử, khối "Năm 2025" phải ghi đúng tên file đó và dòng
   chữ "Nguồn chuẩn của năm".

4. MỘT GIÁ TRỊ ĐÃ BIẾT KHỚP NGUỒN CHUẨN
   Mở: Lịch sử → Năm 2025 → Tháng 12 → xem dòng "Ly".
   Tổng đơn phải là 105 (KHÔNG phải 104).
   Tổng bán phải là 1.604.205 (KHÔNG phải 1.595.355).

5. QUY TẮC NGUỒN CHUẨN QUAN SÁT ĐƯỢC
   Nếu workbook 2026 cũng đã được nạp: số ở bước 4 vẫn phải là 105 sau khi
   nạp lại workbook 2026. Nạp lại rồi kiểm lại đúng ô đó.

6. CÁC TRANG KINH DOANH HIỆN TẠI VẪN KHOẺ
   Mở tab "Kinh doanh" và "Nhân viên" của một kỳ 2026. Doanh thu, lợi nhuận,
   coverage phải giống hệt trước khi nạp workbook 2025.
```

Nếu cả sáu bước đều đúng: **PHB-04 = DONE**.
Nếu bước 4 hoặc bước 5 sai: dừng lại và báo — đó sẽ là finding chặn thật.

---

## 16. Bước tiếp theo

```text
NEXT_VERTICAL_ACTION = Deploy commit 6a0213d lên production, chạy 6 bước kiểm
                       ở mục 15, ghi kết quả vào PROJECT/PROJECT_PROGRESS.md.
                       Đủ ⟹ PHB-04 = DONE ⟹ mở PHB-05 (Target).
```

Ba việc, theo thứ tự:

1. **Chủ dự án bấm deploy** commit `6a0213d` lên production.
2. **Chạy 6 bước kiểm** ở mục 15 và ghi lại kết quả (kèm ảnh chụp màn hình
   bước 4 thì tốt nhất — đó là bằng chứng mạnh nhất).
3. **Nếu đủ**, đánh dấu `PHB-04 = DONE` và mở vertical tiếp theo là
   **PHB-05 — Target**.

Ba finding không chặn ở mục 12 **không cần** xử lý trước khi đóng PHB-04.
Nếu chủ dự án muốn xử lý, `F-REV-01` (chốt chặn vị trí khối KPI) là cái đáng
làm nhất, vì nó bảo vệ những workbook lịch sử **sẽ** được nạp sau này. Nhưng
đó là lựa chọn, không phải điều kiện.

---

## Phụ lục — Bảng kết quả đầy đủ

```text
REVIEW_BRANCH                    = claude/phb-04-legacy-reference-v1-widtzf
REVIEW_HEAD                      = 6a0213d45931e3848103ab68fe302af10645aadd
EXPECTED_BRANCH                  = claude/phb-04-legacy-reference-v1-widtzf
EXPECTED_HEAD                    = 6a0213d45931e3848103ab68fe302af10645aadd

EXACT_TARGET                     = PASS
DECISION_CHAIN                   = PASS
SOURCE_A_STRUCTURE               = PASS
SOURCE_PRECEDENCE                = PASS
REAL_CONFLICT_PRECEDENCE         = PASS
SECONDARY_SOURCE_ISOLATION       = PASS
SUMMARY_ROW_CLASSIFICATION       = PASS
YEAR_END_KPI_EXCLUSION           = PASS
PROGRESS_ROW_ISOLATION           = PASS
LEGACY_LEVEL_1                   = PASS
LEGACY_LEVEL_2                   = PASS
LEGACY_METRIC_PRESERVATION       = PASS
CROSS_ENGINE_COMPARISON_GATE     = PASS
LEGACY_LINE_DETAIL_2025          = DEFERRED_NON_BLOCKING
BESTSTAFF                        = OUT_OF_SCOPE
MIGRATION_SAFETY                 = PASS
PREEXISTING_LEGACY_COMPATIBILITY = PASS
CURRENT_ENGINE_ISOLATION         = PASS
HISTORY_UI_READ_ONLY             = PASS
LEGACY_IDEMPOTENCY               = PASS
PROVENANCE_UX                    = PASS
LEGACY_NAVIGATION                = PASS
TEST_REACHABILITY                = PASS
PHB03_REGRESSION                 = PASS

FOCUSED_TESTS                    = 79 passed
FULL_TESTS                       = 2216 passed, 11 skipped
GOLDEN_TESTS                     = 74 passed, 2 skipped (4 file golden)
                                   58 passed, 2 skipped (test_golden_baseline.py — mốc canonical)
HISTORY_DB_TESTS                 = 17 passed

BLOCKING_FINDINGS                = NONE
NON_BLOCKING_FINDINGS            = F-REV-01 (chốt chặn vị trí khối KPI) ·
                                   F-REV-02 (nhánh migration production chưa có test) ·
                                   F-REV-03 (đoạn tài liệu mục 2E chưa cập nhật)
OWNER_DECISIONS_REQUIRED         = NONE

REVIEW_RESULT                    = PASS
PHB_04                           = REVIEW_PASS_AWAITING_PRODUCTION_VERIFICATION
SCOPE_DRIFT                      = NO
```
