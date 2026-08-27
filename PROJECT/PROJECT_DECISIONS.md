# QUYẾT ĐỊNH DỰ ÁN

Dùng file này cho các quyết định chiến thuật của dự án — quan trọng xuyên suốt
nhiều session nhưng chưa đủ tầm để cần một ADR đầy đủ.

## DEC-101

Date:
2026-08-22

Task:
TASK-000

Decision:
Đưa `CLAUDE.md`, `PROJECT/`, `docs/` và `governance/` từ
`AI_ENGINEERING_CONSTITUTION_TEMPLATE_V3_2_FINAL_COMPACT/` lên gốc repository
bằng `git mv`.

Reason:
Bố cục compact V3.2 định nghĩa `CLAUDE.md` là điểm vào governance ở gốc, và
mọi đường dẫn governance đều là `governance/...` tính từ gốc. Nằm sâu hơn một
cấp, không đường dẫn canonical nào trong số đó phân giải được.

Impact:
74 file đổi tên, không đổi nội dung. Mọi cross-reference của governance giờ
phân giải được.

Can Revisit After:
Không bao giờ — đây là bố cục bắt buộc của chính bộ khung.

## DEC-102

Date:
2026-08-22

Task:
TASK-001

Decision:
Nguồn đơn ADS được nhận diện bằng từ khóa "ADS" xuất hiện trong cột
`Diễn giải`, đúng như mục 5 đặc tả định nghĩa. Nhân viên sẽ bắt đầu gõ "ADS"
vào cột đó từ nay.

Reason:
Quyết định của chủ dự án. File thô không có cột `Ghi chú` riêng, nên
`Diễn giải` là trường ghi chú duy nhất có sẵn — đúng phương án dự phòng mà
chính đặc tả nêu ở mục 13.

Impact:
Dữ liệu lịch sử từ 01.2026 đến 06.2026 không có dấu hiệu ADS nào và sẽ phân
loại toàn bộ thành PERSONAL. Đơn ADS lịch sử phải sửa bằng override tay. Danh
sách từ khóa là cấu hình, không phải code, nên thêm từ khóa thứ hai sau này
không tốn công phát triển.

Can Revisit After:
Tháng đầu tiên dữ liệu được nhập theo quy ước mới.

## DEC-103

Date:
2026-08-22

Task:
TASK-001

Decision:
Giá nhập giữ trống (Pending) khi import. Không bao giờ suy ra từ cột lợi
nhuận của ERP. Một interface `PriceProvider` được định nghĩa ngay bây giờ để
công cụ bảng giá bên ngoài điền vào sau; luôn nhập tay được ở mọi dòng bất kể
provider trả về gì.

Reason:
Quyết định của chủ dự án. Mục 10 đặc tả nói rõ: nếu chưa có giá nhập, đánh dấu
Missing/Pending và không suy đoán.

Impact:
Lợi nhuận KPI và doanh thu quy đổi chưa đầy đủ cho tới khi có giá. Công cụ
phải hiển thị Pending là Pending — giá thiếu không bao giờ được coi là 0, vì
0 sẽ âm thầm tạo ra lợi nhuận bằng đúng giá bán.

Can Revisit After:
Khi công cụ bảng giá bên ngoài tồn tại.

## DEC-104

Date:
2026-08-22

Task:
TASK-001

Decision:
Nhân viên bán hàng thô `Mr Quý`, `Mr Vinh` và `Đức Hiệp` map về một đơn vị
chuẩn hóa duy nhất, `Nội thành`. `Gia dụng` là một nhóm sản phẩm nằm trong
`Nội thành`, không phải một nhân viên riêng. `Fanpage` nằm ngoài phạm vi.

Reason:
Quyết định của chủ dự án, khớp với báo cáo mẫu: ba tên này có số dòng thô cao
nhất và chưa từng xuất hiện dưới dạng sheet nhân viên riêng, trong khi doanh
số tháng của sheet `Nội thành` cùng bậc độ lớn với tổng của ba người cộng lại.

Impact:
Employee mapping là nhiều-về-một và phải nằm trong cấu hình, có `active` và
ngày hiệu lực, để nhân viên mới/nghỉ không bao giờ cần sửa code. Bất kỳ giá
trị NVBH thô nào chưa có mapping đều vào review queue — không bao giờ âm thầm
bỏ, không bao giờ âm thầm tự bịa.

Can Revisit After:
Bất cứ lúc nào — đây là cấu hình theo đúng thiết kế.

## DEC-105

Date:
2026-08-22

Task:
TASK-001

Decision:
MVP là một ứng dụng web nhiều người dùng có lưu trữ tập trung, không phải một
script local hay một app Streamlit một-phiên.

Reason:
Quyết định của chủ dự án: dùng hằng ngày, nhiều người, cùng xem và sửa,
"vận hành như một Google Sheet".

Impact:
Authentication và phân quyền trở thành bắt buộc từ Phase 2 thay vì tùy chọn —
audit trail theo yêu cầu mục 19 đặc tả cần một `ChangedBy` thật. Backup trở
thành bắt buộc ngay khi database chứa override không tồn tại ở đâu khác.

Can Revisit After:
GATE-03.

## DEC-106

Date:
2026-08-22

Task:
TASK-001

Decision:
Tiền được lưu chuẩn dưới dạng VND nguyên kiểu `Decimal`. Đơn vị hiển thị là
cấu hình, mặc định nghìn đồng để khớp báo cáo hiện có.

Reason:
File thô dùng VND đầy đủ (8000000) còn workbook báo cáo dùng nghìn đồng
(11770). Trộn hai đơn vị này khi lưu trữ là cách một báo cáo sai lệch một
nghìn lần. Float không chấp nhận được cho loại tiền quyết định lương.

Impact:
Mọi lần import và export đều đi qua một ranh giới đơn vị rõ ràng, bắt buộc
phải test.

Can Revisit After:
Không bao giờ — đây là ràng buộc về tính đúng đắn.

## DEC-107

Date:
2026-08-22

Task:
TASK-002

Decision:
Sáu lỗi công thức tìm thấy trong workbook mẫu được ghi lại và báo cáo, nhưng
không tái tạo. Công cụ tính ra con số đúng và, khi kết quả khác với báo cáo
mẫu, nêu rõ vì sao.

Reason:
Mục đích của công cụ là một báo cáo đúng, không phải một bản sao trung thành
của một bảng tính đang đếm sai. Âm thầm tái tạo một lỗi đã biết sẽ làm lỗi đó
tồn tại vĩnh viễn và không truy được.

Impact:
Số SP sẽ không khớp chính xác với báo cáo mẫu — mẫu trừ một tỉ lệ phần trăm
khỏi một số lượng, ra số SP lẻ (387,6). Mọi chênh lệch như vậy được liệt kê
trong `docs/analysis/05_EXCEPTIONS.md` để chủ dự án xem lại.

Can Revisit After:
Chủ dự án xem lại ở GATE-00. Nếu chủ dự án muốn khớp y hệt lỗi cho một con số
cụ thể, đó sẽ là một cờ cấu hình, không phải mặc định âm thầm.

## DEC-108

Date:
2026-08-22

Task:
TASK-001

Decision:
Dữ liệu mẫu thật không nằm trong version control (`.gitignore` loại trừ
`data/samples/`). Test chạy trên fixture đã ẩn danh dựng từ dữ liệu đó.

Reason:
Cả hai workbook mang tên khách hàng, số điện thoại, địa chỉ giao hàng, số
serial thiết bị, cộng thêm số liệu lương nhân viên. Một khi đã commit, nó tồn
tại vĩnh viễn trong lịch sử git.

Impact:
Ai clone repository cũng phải tự cung cấp bản sao workbook nguồn của họ.
Fixture test phải được sinh ra với trường dữ liệu cá nhân đã thay thế, và bản
thân trình sinh đó cũng là một phần sản phẩm bàn giao.

Can Revisit After:
Không bao giờ, chừng nào các file còn chứa dữ liệu cá nhân.

## DEC-109

Date:
2026-08-22

Task:
GATE-00 — trả lời câu hỏi mở C1

Decision:
Mọi đơn do `Tín Phát` lên đều quy đổi ở tỉ lệ ADS (7,5%), bất kể ghi chú có
chứa "ADS" hay không. Cài đặt bằng `default_lead_source: ADS` cho
nhân viên đó trong `config/employees.yaml`, không phải một tỉ lệ hard-code.

> **Sửa đổi 2026-08-23 (DEC-119).** Giá trị cấu hình đổi từ `TINPHAT_ADS`
> thành `ADS`. Bản chất quyết định không đổi — Tín Phát vẫn 100% ADS, vẫn
> 7,5% — nhưng 7,5% giờ suy ra từ *nguồn đơn* qua bảng scheme, không phải từ
> *tên nhân viên* nằm trong một giá trị enum. Xem ADR-104.

Reason:
Quyết định của chủ dự án. `Tín Phát` là tài khoản site/ads của chính công ty —
mọi lead nó xử lý đều do công ty tạo ra theo định nghĩa, nên không có gì để
nhân viên đánh dấu. Điều này cũng khớp với workbook mẫu, nơi `Tín Phát` luôn
quy đổi ở 7,5% mà không có công thức tách bucket.

Impact:
Mặc định cấp nhân viên nằm **dưới** rule từ khóa ADS và **trên** mặc định
toàn hệ thống trong chuỗi ưu tiên, nên nó chỉ có thể nâng một đơn lên ADS,
không bao giờ hạ một đơn mà từ khóa đã bắt được. Override tay vẫn thắng cả
hai.

`Tín Phát` sẽ hiện 100% ADS trong phần tách Personal/ADS — đây là bức tranh
chính xác, không phải sự bóp méo. Số liệu lịch sử của `Tín Phát` không cần di
trú: chúng vốn đã là 7,5%.

Không có gì trong code gắn riêng với `Tín Phát`. Bất kỳ nhân viên hay kênh nào
cũng đặt được nguồn mặc định trong cấu hình.

Can Revisit After:
Bất cứ lúc nào — đây chỉ là một dòng cấu hình.

## DEC-110

Date:
2026-08-22

Task:
GATE-00 — trả lời câu hỏi mở C5

Decision:
Các dòng không phải sản phẩm nhưng có giá trị tiền — `Chi phí vận chuyển`,
`Chi phí lắp đặt`, `Chênh VAT`, `Chi phí giao hộ`, `Phí đổi trả` — **có** tính
vào doanh số và lợi nhuận của nhân viên. Chúng không tính là sản phẩm và
không tạo đơn riêng. Mỗi dòng như vậy được đưa ra để duyệt tay, nơi người
duyệt giữ lại hoặc loại khỏi báo cáo.

Reason:
Quyết định của chủ dự án: *"tất cả dòng phụ nếu có liên quan đến giá trị tiền
hàng vẫn thêm vào doanh số từng nhân viên nhưng sẽ được duyệt thủ công bằng
cách xoá dòng hoặc giữ lại dòng"*.

Impact:
"Xoá dòng" là loại trừ mềm, không bao giờ là xoá thật: RAW bất biến theo
ADR-102. Thao tác này đặt `excluded_from_report` kèm lý do và một bản ghi
audit, và hoàn tác được. Khoảng 1.250 dòng trong mẫu 6 tháng rơi vào nhóm
này, nên màn hình duyệt phải xử lý theo lô — duyệt từng dòng một sẽ không ai
dùng nổi.

Số SP giữ theo đúng cách hành xử hiện có của workbook mẫu là loại trừ các
dòng này. Chưa được chủ dự án xác nhận riêng; đánh dấu cho GATE-01.

Can Revisit After:
GATE-01.

## DEC-111

Date:
2026-08-22

Task:
GATE-00 — trả lời câu hỏi mở C6

Decision:
`Diễn giải` giữ nguyên như ERP ghi mặc định (`"Bán hàng " + Tên KH`). Nhân
viên chỉ sửa khi đơn là ADS. Trường này sửa được — đã được chủ dự án xác
nhận — nên rule từ khóa khả thi.

Reason:
Quyết định của chủ dự án. Điều này loại bỏ ẩn số lớn nhất của RISK-01: liệu
dấu hiệu có ghi được vào hay không.

Impact:
Hầu hết đơn giữ ghi chú tự sinh, nên một ghi chú rỗng hoặc theo mẫu là trường
hợp bình thường và không bao giờ được coi là đáng ngờ. Chỉ một ghi chú được
sửa để chứa từ khóa mới làm thay đổi điều gì đó.

Vì đánh dấu là một hành động tự nguyện mà con người phải nhớ làm, một tháng
không có đơn ADS nào vẫn giữ nguyên là một cảnh báo trong review queue
(RISK-01): với `Tín Phát` giờ đã mặc định ADS theo DEC-109, số 0 nghĩa là
không *nhân viên nào khác* đánh dấu gì — điều này có thể xảy ra nhưng đáng để
nhìn thấy hơn là mặc nhiên coi là đúng.

Can Revisit After:
Tháng đầu tiên dưới quy ước mới.

## DEC-112

> **⚠️ ĐÃ BỊ THAY THẾ BỞI DEC-120 (2026-08-23).** Chủ dự án xác nhận không cần
> di trú dữ liệu ADS lịch sử; lịch sử không có dấu hiệu ADS mặc định
> `PERSONAL`. Bảng 14 số dưới đây **vẫn giữ nguyên giá trị làm mốc đối chiếu**,
> nhưng không còn là đầu vào bắt buộc của `conversion_engine`, và mốc
> 13.883.242 không còn là REQUIRED check của TASK-108. Giữ lại nguyên văn vì
> phần "Yêu cầu kỹ thuật kéo theo" vẫn mô tả đúng ràng buộc nếu sau này ai đó
> chọn nhập số di trú. Đọc DEC-120 trước khi hành động theo quyết định này.

Date:
2026-08-22

Task:
GATE-00 — trả lời câu hỏi mở C7

Decision:
Lợi nhuận ADS lịch sử của Hoàng và Kiên (01–08.2026) được nhập dưới dạng 14
số theo từng nhân viên-tháng, đánh dấu là dữ liệu di trú và tách bạch rõ ràng
khỏi số do rule ADS sinh ra. Các giá trị này là những số đã ghi sẵn trong
`docs/analysis/04_HARDCODED_VALUES.md` §2 và
`docs/analysis/06_ADS_RULE_VERIFICATION.md` §8.

Reason:
Quyết định của chủ dự án. Truy lại từng đơn là bất khả thi — không workbook
nào ghi lại đơn nào từng là ADS, và `3770+16190` trong công thức tháng 5 của
Hoàng cho thấy các số này được cộng tay từ một nguồn nằm ngoài hệ thống. Nhập
tổng theo tháng chỉ tốn 14 ô một lần và làm đầu ra của công cụ khớp chính xác
với báo cáo hiện có, để không ai phải giải thích một cú nhảy 6,0% trong doanh
thu quy đổi của hai người.

Impact:
- `conversion_engine` cần một đường nhập di trú: một số lợi nhuận ADS theo
  cặp (nhân viên, tháng) bỏ qua phân loại ở cấp đơn.
- Số di trú phải hiển thị khác biệt rõ ràng với số do rule sinh ra, cả trên
  UI lẫn trong file xuất. Đó là một lời khẳng định về quá khứ, không phải một
  phép tính, và không bao giờ được nhầm là một phép tính.
- Hai đường này phải loại trừ nhau trong cùng một nhân viên-tháng. Nếu một
  tháng vừa có số di trú vừa có đơn được rule phân loại ADS, đó là một xung
  đột đưa vào review queue, không phải một phép cộng.
- Tháng chuyển đổi (cut-over) phải được ghi trong cấu hình: trước tháng đó
  dùng số di trú, từ tháng đó trở đi dùng rule.
- Mốc đối chiếu: với 14 giá trị đã nạp, tổng doanh thu quy đổi của Hoàng và
  Kiên trong 01–08.2026 phải bằng **13.883.242** nghìn đồng. Đây trở thành
  một REQUIRED check ở TASK-108.

Can Revisit After:
Khi quy ước ADS đã chạy đủ lâu để lịch sử năm 2026 không còn quan trọng nữa.

## DEC-113

Date:
2026-08-22

Task:
GATE-00 — trả lời câu hỏi mở C8

Decision:
Dòng phụ có giá trị tiền bị loại khỏi số SP, xác nhận đúng giả định mà
DEC-110 đã nêu. `Tổng số SP` vẫn giữ làm một cột Summary để khớp báo cáo hiện
có, nhưng bị hạ ưu tiên: không tính năng nào xây dựa trên nó và nó không phải
tiêu chí đối chiếu ở bất kỳ gate nào.

Reason:
Quyết định của chủ dự án — *"loại số SP ra. có vẻ dữ liệu này không cần
thiết"*.

Impact:
Xóa bỏ các số SP lẻ của workbook mẫu (387,6 / 178,8 / 62,6), vốn sinh ra từ
việc trừ một tỉ lệ phần trăm khỏi một số lượng — xem
`docs/analysis/05_EXCEPTIONS.md` §A1. Số SP của công cụ sẽ là số nguyên và
cao hơn một chút so với mẫu.

Vì chỉ số này giá trị thấp, chênh lệch đó không cần giải thích từng dòng ở
GATE-01. Mọi chênh lệch đối chiếu khác vẫn cần.

Can Revisit After:
Bất cứ lúc nào — bỏ cột này sau cũng không tốn gì.

## DEC-114

Date:
2026-08-22

Task:
GATE-00 — trả lời câu hỏi mở C4

Decision:
`Chiết khấu` được trừ vào doanh số:

```
TotalSales = SellPrice × Quantity − Discount
```

Reason:
Quyết định của chủ dự án. Đã kiểm chứng với file thô: ở cả 408 dòng có chiết
khấu, `Doanh số bán` đúng bằng `Đơn giá × SL`, chưa từng trừ chiết khấu, nên
cột của ERP là gross và chiết khấu chưa được áp dụng từ trước. Trừ nó là một
phép sửa thật, không phải trừ hai lần.

Impact:
Tổng 6 tháng: 36.750 nghìn đồng trên 408 dòng — 0,03% doanh số công ty. Dồn
vào một người: Ly chiếm 302/408 dòng và 26.300 nghìn, 0,39% doanh số của cô
ấy. Không ai khác vượt quá 0,07%.

**Giả định còn mở, đánh dấu cho GATE-01:** chiết khấu cũng trừ vào lợi nhuận
cùng số đó, tức là
`EligibleKpiProfit = (SellPrice − KpiPurchasePrice) × Quantity − Discount − EligibleCosts + OtherKpiAdjustment`.
Chủ dự án nói "trừ vào doanh số" và chưa nói tới lợi nhuận. Giảm doanh số mà
không giảm lợi nhuận sẽ báo cáo một tỉ suất lợi nhuận cao hơn thực tế công ty
kiếm được — đây là cách hiểu mà dự án này không thể âm thầm chấp nhận, vì
chiết khấu là tiền đã cho đi. Nêu rõ ở đây thay vì mặc định ngầm.

Can Revisit After:
GATE-01, chỉ riêng phần lợi nhuận.

## DEC-115

Date:
2026-08-22

Task:
GATE-00 — trả lời câu hỏi mở C2

Decision:
Phép `/2` trong sheet Nội thành và Gia dụng đã được giải thích: các sheet này
mang một dòng tổng phụ theo ngày nằm **bên trong** vùng dữ liệu, nên một
`SUM` đơn thuần đếm mỗi con số hai lần. Chia đôi tổng là một cách xử lý đúng
cho layout đó.

Công cụ không tái tạo cả dòng tổng phụ nhúng lẫn phép chia đôi. Dòng dữ liệu
chỉ là dữ liệu; tổng phụ được tính riêng và, khi xuất, phát ra dưới dạng dòng
outline/group của Excel mang nhãn `RowType` rõ ràng, giữ chúng nằm ngoài mọi
vùng `SUM`.

Reason:
Chủ dự án giải thích nguyên nhân và yêu cầu một cách thể hiện tốt hơn:
*"nếu có cách thể hiện khoa học hơn, hãy làm"*.

Impact:
- `docs/analysis/05_EXCEPTIONS.md` §A3 chuyển từ "chưa giải thích được, cần
  điều tra" sang "đã giải thích, cố ý không tái tạo".
- Phép chia đôi chưa bao giờ sai với layout nó đang sống trong đó — nhưng nó
  vô hình. Ai thêm một dòng sai chỗ, hoặc đọc sheet mà không biết quy ước
  này, sẽ nhận một con số lệch đúng 2 lần. Một cột `RowType` biến sự khác
  biệt đó thành thứ nhìn thấy và lọc được, thay vì thứ phải ghi nhớ.
- Mọi tổng trong công cụ cộng đúng một lần mỗi con số, không có phép chia bù
  nào trong toàn bộ codebase. Một `/2` xuất hiện trong logic tổng hợp bị coi
  là một lỗi.

Can Revisit After:
Không bao giờ — một phép chia bù ẩn không phải thiết kế mà dự án này chấp
nhận.

## DEC-116

Date:
2026-08-22

Task:
GATE-00 — trả lời câu hỏi mở C3

Decision:
Hoa hồng dựa trên mức đạt target — trả khi đạt và vượt KPI. Việc công thức
hóa được dời sang một phase sau, đúng như kế hoạch ở TASK-403.

Reason:
Quyết định của chủ dự án. Các tỉ lệ quan sát được (0,15%–0,5%, thay đổi theo
người và theo tháng) không suy ra được từ một rule bậc thang duy nhất, nên
chính sách phải được phát biểu đầy đủ trước khi mã hóa.

Impact:
Phase 1 nạp bảng tỉ lệ quan sát được theo từng nhân viên-tháng làm dữ liệu,
đúng như nó xuất hiện trong workbook mẫu. Không suy đoán hay bịa ra logic bậc
thang nào. Số hoa hồng công cụ tạo ra trước TASK-403 tái hiện lịch sử; chúng
không dự đoán một tháng mới nên trả bao nhiêu.

Can Revisit After:
TASK-403, khi chính sách đầy đủ đã được phát biểu.

## DEC-117

Date:
2026-08-23

Task:
Merge PR#4 vào nhánh mặc định `claude/extract-upload-repo-gq2ws4`

Decision:
Renumber toàn bộ quyết định và ADR của dự án Tín Phát: DEC-001..016 →
DEC-101..116 (file này), ADR-001..003 → ADR-101..103
(`docs/adr/ADR-101-architecture-and-stack.md`,
`docs/adr/ADR-102-three-layer-data-model-and-audit.md`,
`docs/adr/ADR-103-currency-unit-standard.md`). Đồng thời khôi phục nguyên văn
16 quyết định gốc của track audit (S001–S007) vào `docs/audit/DECISIONS.md`,
không chỉnh sửa nội dung.

Reason:
Merge PR#4 hợp nhất nhánh dự án Tín Phát với nhánh audit bộ khung quản trị
(S001–S007). Cả hai track tách nhau từ đúng commit đầu tiên của repository và
độc lập đánh số quyết định từ DEC-001, cả hai đều dùng hết tới DEC-016 —
trùng số hoàn toàn. Nghiêm trọng hơn: cả hai đều có một file `ADR-001` nằm
cạnh nhau trong `docs/adr/`. Vì `PROJECT/PROJECT_DECISIONS.md` được giữ lại
cho dự án Tín Phát (dự án đang hoạt động, theo yêu cầu ban đầu của chủ dự án),
16 quyết định gốc của track audit sẽ biến mất khỏi file đó — nhưng 16 file
khác (`docs/audit/`, `docs/sessions/`, `docs/tasks/TASK-REM-*.md`,
`governance/scripts/governance/README.md`) vẫn trích dẫn DEC-001..016 của
riêng track đó. Không renumber, mọi trích dẫn "DEC-005" trong các file đó sẽ
âm thầm trỏ tới quyết định sai — một quyết định hoàn toàn khác của dự án Tín
Phát.

Impact:
- Renumber áp dụng đúng lên các file của dự án Tín Phát: hai file
  `PROJECT/*.md`, bảy tài liệu `docs/analysis/*.md`, ba file ADR (đổi tên file
  bằng `git mv` kèm sửa heading bên trong). Không đụng tới bất kỳ file nào
  thuộc track audit.
- 16 quyết định gốc của track audit được chuyển nguyên văn — không diễn giải
  lại — sang `docs/audit/DECISIONS.md`, giữ đúng số DEC-001..016 để mọi trích
  dẫn hiện có vẫn còn ý nghĩa đúng.
- Sửa một dòng tham chiếu duy nhất trong `governance/scripts/governance/README.md`
  trỏ sang vị trí mới của DEC-012/DEC-013.
- Đã chạy lại cả 5 validator của governance (`validate_structure.py`,
  `validate_project_state.py`, `validate_task_completion.py`,
  `validate_evidence.py`, `validate_reference_integrity.py`) và bộ test
  `tools/analysis/verify_ads_rule.py` sau khi renumber — toàn bộ PASS.
- Nội dung roadmap, business rule và quyết định nghiệp vụ của dự án Tín Phát
  không đổi qua việc renumber này — chỉ có mã số thay đổi.

Can Revisit After:
Không cần — đây là một việc sửa một lần, không lặp lại.

## DEC-118

Date:
2026-08-23

Task:
Hợp nhất hai track công việc bị phân tán (không thuộc riêng task nào —
theo yêu cầu trực tiếp của chủ dự án)

Decision:
1. Khôi phục track Governance Remediation (S001–S007, REM-T05/T06, Phase
   Gate 02/03, 5 finding OPEN) vào lại `PROJECT/PROJECT_PROGRESS.md` dưới
   một mục riêng "Track Governance — Bảo Trì Nền Tảng (PHASE-GOV)", song
   song với roadmap Tín Phát, không chặn nhau trừ khi ghi rõ dependency.
2. Ghi nhận chính thức: `TASK-000` (track Tín Phát) và `REM-T02` (track
   Governance) đã làm trùng cùng một việc — dời gói governance lên
   repository root — trên hai nhánh tách biệt, không biết về nhau. Cả hai
   hội tụ đúng cùng kết quả (xác nhận bằng `validate_structure.py` PASS
   trên HEAD hiện tại). Không cần làm lại; không rollback bên nào.
3. Thêm cơ chế đồng bộ nhánh bắt buộc cho mọi session tương lai:
   - `.claude/hooks/session-start.sh` — SessionStart hook tự động fetch
     nhánh mặc định trên origin và in cảnh báo nếu session đang lỗi thời
     hoặc đứng trên một nhánh cô lập, trong môi trường Claude Code on the
     web (`CLAUDE_CODE_REMOTE=true`).
   - `.claude/settings.json` — đăng ký hook trên.
   - Nới `.gitignore`: `.claude/settings.json` và `.claude/hooks/` giờ ĐƯỢC
     commit (trước đây toàn bộ `.claude/` bị ignore, xem FIND-009); scratch
     state khác của harness tiếp tục bị ignore qua `.claude/*` +
     exception cho hai đường dẫn trên.
   - Thêm bước 0 "Đồng bộ nhánh" vào đầu "Giao thức Mở Phiên" trong
     `governance/core/00_SESSION_ORCHESTRATION.md`.
   - Thêm mục "Đồng Bộ Nhánh" vào `CLAUDE.md`, áp dụng cho mọi session
     (không chỉ Major Task) — vì sự cố vừa xảy ra không giới hạn ở phiên
     Major Task.

Reason:
Một session được yêu cầu rà soát tiến độ dự án phát hiện: nhánh local của
session đang đứng lỗi thời 14 commit so với nhánh mặc định thật trên origin,
khiến câu trả lời đầu tiên về "3 file đặc tả Report" bị đánh giá sai thành
"CONFLICT DETECTED / không tồn tại", trong khi thực ra track Tín Phát đã
hoàn tất phần lớn PHASE-00 trên nhánh mặc định từ trước. Nguyên nhân gốc:
không có bước bắt buộc nào trong `governance/core/00_SESSION_ORCHESTRATION.md`
yêu cầu xác nhận đồng bộ nhánh trước khi đọc `PROJECT_PROGRESS.md`. Hai
track hình thành độc lập vì tách nhánh từ cùng một điểm gốc và không session
nào kiểm tra lại origin trước khi tự tạo roadmap riêng — dẫn tới việc
`TASK-000`/`REM-T02` làm trùng việc, và merge PR#4/#5 sau đó ghi đè (không
hợp nhất) nội dung `PROJECT_PROGRESS.md`, làm mồ côi REM-T05/T06.

Risk:
Thấp cho việc hợp nhất tài liệu (chỉ gộp nội dung đã tồn tại dưới
`docs/audit/`, `docs/tasks/`, không sửa logic nghiệp vụ Tín Phát). Trung
bình cho việc phụ thuộc vào SessionStart hook — hook chỉ hoạt động trong môi
trường Claude Code on the web; giảm thiểu bằng cách cũng ghi rule bằng văn
bản vào `CLAUDE.md` và `governance/core/00_SESSION_ORCHESTRATION.md` làm lớp
phòng vệ thứ hai, không phụ thuộc hoàn toàn vào cơ chế tự động.

Impact:
- `PROJECT/PROJECT_PROGRESS.md`: thêm mục "Đồng Bộ Nhánh", "Hai Track Song
  Song" ở đầu; mục "Track Governance — Bảo Trì Nền Tảng (PHASE-GOV)"; cập
  nhật "Quyết định gần đây", "Lịch sử Session" và "Session tiếp theo".
- `CLAUDE.md`: thêm mục "Đồng Bộ Nhánh (Bắt Buộc Cho Mọi Session)".
- `governance/core/00_SESSION_ORCHESTRATION.md`: thêm bước 0 vào "Giao thức
  Mở Phiên".
- `.gitignore`, `.claude/settings.json`, `.claude/hooks/session-start.sh`:
  file mới/sửa.
- Không sửa nội dung nghiệp vụ Tín Phát (roadmap PHASE-00..04, chấm điểm,
  completion gate sơ bộ) và không sửa nội dung kỹ thuật của track Governance
  (`docs/audit/`, `docs/tasks/TASK-REM-*.md`) — chỉ khôi phục khả năng nhìn
  thấy trong checklist canonical.
- Đã chạy lại cả 5 validator governance sau toàn bộ thay đổi trước khi push.

Can Revisit After:
Nếu owner xác nhận muốn đổi tên nhánh mặc định thành `main` theo nghĩa đen
trên GitHub — khi đó cập nhật lại các đoạn văn bản nêu tên nhánh cụ thể
(`claude/extract-upload-repo-gq2ws4`) trong `CLAUDE.md` và
`PROJECT_PROGRESS.md`; script hook không cần sửa vì nó tự phát hiện động qua
`git ls-remote --symref origin HEAD`, không hard-code tên nhánh.

## DEC-119

Date:
2026-08-23

Task:
Xác nhận nghiệp vụ trước khi chuyển Phase (không thuộc riêng task nào — theo
yêu cầu trực tiếp của chủ dự án)

Decision:
`LeadSource` và `ConversionScheme` là hai khái niệm độc lập, hai trường riêng,
hai bước phân giải riêng.

- `LeadSource` có **đúng hai giá trị**: `PERSONAL` và `ADS`. Giá trị
  `TINPHAT_ADS` bị loại bỏ hoàn toàn khỏi mọi tài liệu và mã nguồn.
- `ConversionScheme` tra từ `config/conversion_rates.yaml` theo khóa
  `(employee, lead_source, ngày của đơn)`, dòng cụ thể nhất thắng, không có
  tỉ lệ mặc định cuối cùng.

Chi tiết đầy đủ, bảng chính sách và chuỗi ưu tiên: ADR-104.

Reason:
Quyết định của chủ dự án, xác nhận ngày 2026-08-23: *"`PERSONAL` không đồng
nghĩa với hệ số 5,5%"*. Thiết kế cũ gộp hai khái niệm và không diễn đạt được
trường hợp có thật: Nội thành bán đơn `PERSONAL` nhưng quy đổi ở 2%, Gia dụng
ở 8%. Tài liệu cũ phải mô tả hai nhóm này như một ngoại lệ nằm ngoài mô hình
("tỉ lệ đặt ở cấp nhân viên, nên `default_lead_source` không ảnh hưởng tới con
số") — đó là dấu hiệu mô hình sai, không phải một chú thích.

Tên `TINPHAT_ADS` còn nói sai sự thật khi Hoàng hoặc Kiên có đơn ADS: đơn đó
không phải của Tín Phát.

Impact:
- Không con số nào của báo cáo thay đổi vì riêng quyết định này. Tín Phát vẫn
  7,5%, Nội thành vẫn 2%, Gia dụng vẫn 8% — chỉ khác ở chỗ 7,5% giờ suy ra từ
  nguồn đơn qua bảng config, không phải từ tên nhân viên nằm trong enum.
- `orders` mang hai cặp trường override song song: `lead_source_*` và
  `conversion_scheme_*`. Người dùng sửa được từng cái độc lập, cả hai qua audit
  trail của ADR-102, cả hai bắt buộc `reason`.
- Báo cáo tách Personal/ADS giờ có nghĩa cho **mọi** nhân viên kể cả kênh, đúng
  yêu cầu §15 và §16 đặc tả. Trước đây phần tách này vô nghĩa với Nội thành và
  Gia dụng.
- Một tổ hợp `(employee, lead_source, date)` không khớp dòng config nào trả về
  `Unresolved` và vào Review Queue — không bao giờ mượn tỉ lệ của người khác.
- Bản cài đặt tham chiếu `tools/analysis/verify_ads_rule.py` tách thành hai hàm
  `classify_lead_source()` và `resolve_conversion_scheme()`, bổ sung 8 case
  A–G do chủ dự án chỉ định. Toàn bộ 31 check PASS.

Can Revisit After:
Không nên — việc gộp hai khái niệm là lỗi mô hình, không phải một lựa chọn
đánh đổi.

## DEC-120

Date:
2026-08-23

Task:
Xác nhận nghiệp vụ trước khi chuyển Phase — thay thế DEC-112

Decision:
Không di trú dữ liệu ADS lịch sử. Đơn lịch sử không có dấu hiệu ADS phân loại
thành `PERSONAL` theo mặc định. Không xây giá trị `UNKNOWN` cho `LeadSource`.

14 số lợi nhuận ADS gõ tay của Hoàng và Kiên
(`docs/analysis/04_HARDCODED_VALUES.md` §2) giữ
lại làm **bảng đối chiếu tham khảo**, không phải đầu vào của
`conversion_engine`.

Mốc **13.883.242** nghìn đồng bị **gỡ khỏi danh sách REQUIRED check của
TASK-108** và thay bằng một check tái lập được từ dữ liệu — xem mục Impact.

Reason:
Quyết định của chủ dự án: *"Không cần làm phức tạp việc migration dữ liệu cũ…
Không cần xây `UNKNOWN LeadSource` chỉ để phục vụ dữ liệu cũ. Mục tiêu chính
là chuẩn hóa dữ liệu mới."* Kết hợp với DEC-121 (2026 là giai đoạn chuyển
đổi), việc số 2026 không khớp tuyệt đối với workbook cũ là hệ quả được chấp
nhận có ý thức, không phải một lỗi cần che.

Impact:
- **Hệ quả bằng số, cần nói rõ:** với lịch sử mặc định `PERSONAL`, tổng doanh
  thu quy đổi 01–08.2026 của Hoàng và Kiên là **14.720.745** nghìn đồng thay vì
  **13.883.242** như workbook đang báo cáo — **cao hơn 837.503 nghìn (~837
  triệu), tức 6,0%**, kéo theo khoảng **2.967 nghìn (~3,0 triệu đồng)** tiền
  thưởng cộng thêm cho hai người trong 8 tháng. Chiều lệch là *có lợi* cho nhân
  viên, vì quy đổi ở 5,5% cho ra số lớn hơn quy đổi ở 7,5%.
- REQUIRED check thay thế cho TASK-108 (E1, tái lập được, không cần dữ liệu di
  trú): nạp lợi nhuận KPI theo nhân viên-tháng **và** 14 giá trị `X` của chính
  workbook vào `conversion_engine`, kết quả phải tái hiện đúng cột `F` của
  `Summary 2026` ở cả 14 kỳ. Check này chứng minh engine cài đúng phép toán mà
  con người đang làm tay, mà không buộc production phải mang dữ liệu di trú.
- `conversion_engine` **không cần** đường nhập di trú riêng, không cần cấu hình
  cut-over theo tháng, không cần logic loại trừ giữa số di trú và số do rule
  sinh ra. Ba yêu cầu kỹ thuật này của DEC-112 được gỡ khỏi phạm vi TASK-108.
- Phần "Yêu cầu kỹ thuật kéo theo" của DEC-112 vẫn được giữ nguyên văn trong
  sổ quyết định, phòng khi sau này chủ dự án đổi ý và muốn nhập số di trú.

Can Revisit After:
GATE-01 — nếu khi đối chiếu số thật, chênh lệch 6,0% của Hoàng và Kiên bị đánh
giá là không chấp nhận được, DEC-112 vẫn còn nguyên vẹn để kích hoạt lại.

## DEC-121

Date:
2026-08-23

Task:
Xác nhận nghiệp vụ trước khi chuyển Phase

Decision:
Giai đoạn hiện tại là **giai đoạn chuyển đổi**. Từ **01/01/2027**, quy trình
mới trở thành chuẩn chính thức.

Mọi business rule có tính chính sách — tỉ lệ quy đổi, mặc định nguồn đơn cấp
nhân viên, danh sách từ khóa ADS, target, tỉ lệ thưởng — mang `effective_from`
và `effective_to`.

Việc tra cứu dùng **ngày nghiệp vụ của đơn / của kỳ báo cáo**, không bao giờ
dùng "hôm nay".

Reason:
Quyết định của chủ dự án. Một chính sách đổi vào 2027 không được phép làm thay
đổi con số của một báo cáo 2026 đã phát hành. Nếu tra cứu dùng thời điểm chạy
báo cáo, in lại báo cáo tháng 3/2026 vào năm 2028 sẽ ra một con số khác — và
không ai biết bản nào đúng.

Impact:
- Là một REQUIRED check kiểm chứng được của TASK-108: chạy lại một kỳ lịch sử
  sau khi thêm một dòng chính sách có `effective_from` trong tương lai phải cho
  ra **kết quả không đổi**. Đã có case trong bản tham chiếu
  (`run_temporal_check()`, 3/3 PASS).
- Tra cứu trước `effective_from` sớm nhất trả về `Unresolved`, không đoán tỉ
  lệ. Đã kiểm chứng: ngày 31/12/2025 → `Unresolved`.
- 2026 được chấp nhận là năm có số liệu không khớp tuyệt đối với workbook cũ
  (xem DEC-120). Đây chính là lý do việc đó chấp nhận được: 2026 là giai đoạn
  chuyển đổi có tuyên bố, không phải một năm bị tính sai.
- Cần một quyết định riêng trước 01/01/2027 nếu chính sách 2027 khác 2026.
  Hiện chưa có thông tin nào về nội dung thay đổi — chỉ có mốc thời gian.

Can Revisit After:
Trước 01/01/2027, khi chính sách của năm 2027 được phát biểu.

## DEC-122

Date:
2026-08-23

Task:
GATE-00 — duyệt chính thức + đóng câu hỏi mở C4b, C9, C10

Decision:
Chủ dự án **duyệt GATE-00**, trực tiếp trong hội thoại, sau khi xem đợt rà
soát nghiệp vụ DEC-119/120/121 và bộ tài liệu phân tích đã cập nhật. Nguyên
văn xác nhận:

- **(a) Chấp nhận chênh lệch +6,0 %** (Hoàng + Kiên, 01–08.2026, hệ quả của
  DEC-120 không di trú) — *"chấp nhận"*.
- **(b) C4b — Chiết khấu trừ vào lợi nhuận:** *"mặc định có"*. Xác nhận đúng
  mặc định đang áp dụng (`EligibleKpiProfit` trừ `Discount`). Đóng C4b, không
  đổi hành vi.
- **(c) C9 — Tỉ lệ ADS cho Nội thành/Gia dụng:** *"đơn nội thành / gia dụng
  luôn không xuất hiện ADS. không cần quan tâm"*. Đóng C9 — **không thêm dòng
  scheme riêng** cho tổ hợp `(Nội thành, ADS)` / `(Gia dụng, ADS)`. Nếu tổ hợp
  này phát sinh ngoài dự kiến, nó vẫn rơi vào dòng `* + ADS` (7,5 %) theo đúng
  hành vi đã ghi ở `docs/analysis/06_ADS_RULE_VERIFICATION.md` §9 — chủ dự án
  đã xác nhận
  không cần một kết quả khác cho trường hợp này.
- **(d) C10 — Chính sách 2027:** *"không đổi"*. Đóng C10 cho hiện tại — chưa
  có chính sách 2027 nào khác 2026 để cấu hình. Giữ nguyên điều kiện "cần
  trước 01/12/2026" phòng khi có thông tin mới, vì đây là xác nhận trạng thái
  hiện tại chứ không phải cam kết 2027 sẽ mãi giống 2026.
- **(e) C11 — 88 dòng nhân viên chưa map:** *"tôi chưa rõ"*. **Vẫn mở** — giữ
  nguyên mặc định Review Queue loại `Missing`, không tính vào KPI của ai.
  Không chặn GATE-00 hay Phase 1, vì mặc định đã an toàn (không âm thầm bỏ,
  không âm thầm gán).

Reason:
Đúng quy trình GATE-00 đã định nghĩa từ TASK-001: *"chủ dự án đọc
`docs/analysis/` và xác nhận mapping cùng business rule là đúng."* Bằng chứng
duyệt là phát biểu trực tiếp của chủ dự án trong hội thoại, ghi nguyên văn ở
trên (E1 — lời khai trực tiếp của chủ dự án, không phải suy luận).

Impact:
- **GATE-00 chuyển từ VERIFYING sang DONE.** Lượt duyệt 1/1.
- **PHASE-01 được mở khóa.** `TASK-101` (importer + normalizer) trở thành
  Current Task / Next Recommended Task.
- Roadmap Track A (`PROJECT_PROGRESS.md`) và bản dễ hiểu
  (`PROJECT/LO_TRINH_DE_HIEU.md`) đều cập nhật đồng thời theo "Giao thức Đóng
  Phiên".
- C4b, C9, C10 chuyển từ "còn mở" sang "đã đóng" trong
  `docs/analysis/10_OPEN_QUESTIONS.md`. C11 giữ nguyên trạng thái mở, không
  chặn.
- Không con số nào trong engine thay đổi vì quyết định này — DEC-119/120/121
  đã mô tả đúng hành vi được duyệt. DEC-122 là bước xác nhận, không phải bước
  sửa logic.

Can Revisit After:
Không cần cho phần GATE-00/C4b/C9 — đã duyệt chính thức, không phải mặc định
tạm thời. Riêng C11 — khi chủ dự án xác định được 88 dòng đó là nhân viên
nghỉ việc, thời vụ, hay lỗi nhập liệu. C10 — trước 01/12/2026 nếu chính sách
2027 được công bố.

## DEC-123

> **Sửa đổi 2026-08-23 (DEC-124).** Mặc định 3 vai trò `viewer`/`editor`/
> `admin` + `employee_scope` mô tả trong quyết định này đã bị thay thế bằng
> quyết định trực tiếp của chủ dự án: chỉ một vai trò `ADMIN` trong MVP. Bản
> chất quyết định DEC-123 không đổi — vẫn cần một bản đồ route và một thiết
> kế phân quyền trước khi đóng băng TASK-203/204 — chỉ nội dung thiết kế cụ
> thể ở ADR-105 §4/§5 đã viết lại. Xem DEC-124.

Date:
2026-08-23

Task:
Roadmap Finalization sơ bộ cho TASK-203 / TASK-204 (không thuộc session
triển khai nào — theo yêu cầu trực tiếp của chủ dự án)

Decision:
Soạn `docs/adr/ADR-105-route-map-and-authorization-model.md` — bản đồ route
backend (24 endpoint), bản đồ route frontend (14 route gán cho TASK-301…306),
ma trận phân quyền 3 vai trò × 13 năng lực, và ba phát biểu ràng buộc về ranh
giới bảo mật backend/frontend. Mở rộng mô tả TASK-203/TASK-204 trong
`PROJECT/PROJECT_PROGRESS.md` từ một dòng một câu thành phạm vi cụ thể, và bổ
sung 6 check PRELIMINARY vào mục "Completion Gate sơ bộ".

**ADR-105 để ở trạng thái `Proposed`, KHÔNG phải `Accepted`. Không freeze
Completion Gate của TASK-203/204.**

Reason:
Chủ dự án hỏi trực tiếp hai câu: roadmap có phần nào bảo mật thông tin qua
backend thay vì để lộ ở frontend không, và đã có kế hoạch phân chia router cho
từng luồng chưa. Rà soát cho kết quả: **nguyên tắc có đủ, thiết kế cụ thể thì
không**. `ADR-101` đã chốt phân lớp và cấm business rule nằm ở router;
`governance/core/04_SECURITY_RULES.md` và `governance/core/02_ROUTING_RULES.md` đều là Mandatory theo profile
PRODUCT và đã cấm thẳng những thứ chủ dự án lo. Nhưng TASK-203 và TASK-204
trong roadmap mỗi cái chỉ là một dòng một câu, ba vai trò `viewer`/`editor`/
`admin` được đặt tên mà chưa ai định nghĩa vai trò nào đọc được gì, và không
có danh sách route nào tồn tại ở bất kỳ đâu trong repo.

Khoảng trống đó thuộc loại dễ bị lấp bằng ứng biến lúc code — đúng thứ
`CLAUDE.md` → "Không code trước rồi tổ chức sau" cấm.

Vì sao **không** freeze: `governance/core/00_SESSION_ORCHESTRATION.md` → "Hoàn
thiện Roadmap" ghi rõ *"Không đóng băng chi tiết của các task còn xa trước khi
việc discovery đã đủ."* TASK-203/204 nằm ở PHASE-02, cách task hiện tại
(TASK-101) hơn một phase và một gate. Quan trọng hơn: ma trận phân quyền chứa
ba câu hỏi **nghiệp vụ**, không phải kỹ thuật, mà chủ dự án chưa được hỏi —
nhân viên có xem được số của nhau không (C12), ai được xem giá nhập (C13), ai
được chốt một lần nạp (C14). Tự quyết ba câu đó rồi đóng băng thành gate sẽ
là bịa ra yêu cầu của chủ dự án. Ba câu được ghi vào
`docs/analysis/10_OPEN_QUESTIONS.md` kèm mặc định đang áp dụng, đúng khuôn mà
C4b đã dùng.

Risk:
Thấp cho hiện tại — không dòng nào ảnh hưởng PHASE-01, và `ADR-101` vẫn cấm
PHASE-01 import `fastapi`/`sqlalchemy`.

Rủi ro thật nằm ở chiều ngược lại: một session sau đọc ADR-105 và tưởng đó là
gate đã chốt. Giảm thiểu bằng ba lớp — trạng thái `Proposed` ghi ở dòng đầu
ADR, đoạn "Lưu ý cho session sau" ngay dưới các check PRELIMINARY trong
`PROJECT_PROGRESS.md`, và mục "Migration / Implementation Notes" của ADR-105
yêu cầu đóng C12/C13/C14 trước khi chuyển sang Accepted.

Mặc định `employee_scope` hạn chế (ADR-105 §5) chặt hơn hiện trạng — hôm nay
cả đội dùng chung một file Excel nên ai cũng thấy số của tất cả. Chọn chiều
chặt trước vì nới ra là một dòng cấu hình, còn siết lại sau khi mọi người đã
quen làm được mọi thứ thì khó hơn nhiều.

Impact:
- File mới: `docs/adr/ADR-105-route-map-and-authorization-model.md`.
- `PROJECT/PROJECT_PROGRESS.md`: TASK-203, TASK-204 có phạm vi cụ thể;
  TASK-301…306 và GATE-03 được gán route; 6 check PRELIMINARY thêm vào
  "Completion Gate sơ bộ" kèm cảnh báo không-phải-gate-đã-freeze.
- `docs/analysis/10_OPEN_QUESTIONS.md`: thêm C12, C13, C14 (còn mở, không chặn
  PHASE-01); phần mở đầu sửa lại vì file giờ chứa cả câu hỏi PHASE-02.
- `PROJECT/LO_TRINH_DE_HIEU.md`: cập nhật theo "Giao thức Đóng Phiên".
- **Không** sửa `ADR-101`, `ADR-102`, `ADR-104` — ADR-105 bổ sung chi tiết
  triển khai cho phân lớp mà ADR-101 đã chốt, không thay thế gì.
- **Không** đổi thứ tự task, không thêm/bớt task, không đổi Current Task.
  TASK-101 vẫn là việc tiếp theo.

Can Revisit After:
PHASE-02 mở. Lúc đó chạy Roadmap Finalization đầy đủ cho TASK-203/204, đóng
C12/C13/C14, rồi mới freeze Completion Gate và chuyển ADR-105 sang Accepted.

## DEC-124

Date:
2026-08-23

Task:
Sửa đổi ADR-105 §4/§5 theo quyết định trực tiếp của chủ dự án (không thuộc
session triển khai nào)

Decision:
Công cụ Báo cáo Kinh doanh là công cụ quản trị nội bộ. **MVP chỉ có một vai
trò: `ADMIN`.** Không triển khai `viewer`, `editor`, hay `employee_scope`.

Quy tắc cụ thể, nguyên văn từ chủ dự án:
- Người dùng không có quyền `ADMIN`: không được mở frontend của công cụ; mọi
  API thuộc `/api/v1/*` phải trả `403`, ngoại trừ các endpoint authentication
  cần thiết (`login`/`logout`/`me`).
- `ADMIN` có toàn quyền: báo cáo, import, override, config, audit, export.
- Authorization vẫn phải kiểm tra ở backend, không chỉ ẩn giao diện.
- Thiết kế database nên vẫn cho phép mở rộng thêm role trong tương lai,
  nhưng không xây trước khi có nhu cầu thực tế.

Điều này đóng cả ba câu hỏi C12 (nhân viên xem số của nhau), C13 (ai xem giá
nhập), C14 (ai chốt import) cùng lúc trong `docs/analysis/10_OPEN_QUESTIONS.md`
— không phải bằng cách chọn một trong các hướng đã đề xuất, mà vì tiền đề
chung của cả ba (nhiều vai trò cùng dùng hệ thống) không còn đúng.

Reason:
Chủ dự án trả lời trực tiếp trong hội thoại, ngay sau khi ADR-105 (bản gốc,
DEC-123) đưa ra ba mặc định tạm cho ba câu hỏi phân quyền. Câu trả lời đơn
giản hơn cả ba mặc định đó — không phải một điểm trên ma trận 3 vai trò, mà
một tiền đề khác hẳn: hệ thống này không phục vụ nhiều cấp người dùng, nó
phục vụ một người (hoặc một nhóm nhỏ) quản trị toàn bộ.

Áp dụng nguyên tắc "Không code trước rồi tổ chức sau" theo chiều ngược: giữ
nguyên ba vai trò trong thiết kế sau khi biết chỉ cần một sẽ là *tổ chức
trước* cho một nhu cầu không tồn tại — cùng loại vi phạm với *code trước*,
chỉ khác ở giai đoạn.

Risk:
Thấp cho việc đơn giản hóa — giảm bề mặt cần test, không tăng. Rủi ro thật
nằm ở nhận định trong ADR-105: khi `ADMIN` = toàn quyền và không có lớp chặn
trung gian, một tài khoản `ADMIN` bị lộ (mật khẩu yếu, thiết bị mất) đồng
nghĩa toàn quyền hệ thống rơi vào tay người khác. Đây là đánh đổi có chủ đích
của chủ dự án, không phải sơ suất kỹ thuật — ghi nhận tường minh trong
ADR-105 để không ai quên nó là một đánh đổi đã cân nhắc, không phải một lỗ
hổng bị bỏ sót.

Impact:
- `docs/adr/ADR-105-route-map-and-authorization-model.md`: mục §4 viết lại
  hoàn toàn (ma trận 3 vai trò → nhị phân ADMIN/không-ADMIN); mục §5 viết lại
  (employee_scope hạn chế → mở rộng vai trò trong tương lai, không xây
  trước). §2 (route backend) và §3 (route frontend) không đổi. **Status
  chuyển từ `Proposed` sang `Accepted`** cho §4/§5 — ba điều kiện chặn
  (C12/C13/C14) đã đóng. Completion Gate của TASK-203/204 vẫn KHÔNG freeze —
  đó là quyết định tách biệt, chờ Roadmap Finalization đầy đủ khi PHASE-02
  mở (không đổi so với DEC-123).
- `PROJECT/PROJECT_PROGRESS.md`: mô tả TASK-204 viết lại; 2 check PRELIMINARY
  liên quan ma trận phân quyền viết lại thành nhị phân; "Ghi chú cho session
  nào mở PHASE-02" cập nhật trạng thái Accepted.
- `PROJECT/PROJECT_PROFILE.md`: trường Authentication cập nhật — bỏ "vai trò:
  viewer/editor/admin", thêm quyết định ADMIN-only.
- `docs/analysis/10_OPEN_QUESTIONS.md`: C12, C13, C14 chuyển từ CÒN MỞ sang
  ĐÃ ĐÓNG, nội dung viết lại phản ánh vì sao câu hỏi hết ý nghĩa (C12) hoặc
  có câu trả lời trực tiếp (C13, C14); chuyển cả ba vào bảng "Đã đóng".
- `PROJECT/LO_TRINH_DE_HIEU.md`: cập nhật theo "Giao thức Đóng Phiên" — mục
  "Bảo mật và phân chia luồng" viết lại cho khớp mô hình một vai trò.
- Không đổi route backend (§2) hay route frontend (§3) — cấu trúc URL không
  phụ thuộc vào số vai trò.
- Không đổi TASK-101…112, không đổi Current Task.

Can Revisit After:
Nếu công ty phát sinh nhu cầu thật cho vai trò thứ hai (ví dụ ban quản lý chỉ
xem, không sửa). Lúc đó là một ADR mới hoặc một sửa đổi tường minh của
ADR-105, không phải bật một cờ có sẵn — hạ tầng nhiều vai trò cố ý chưa được
xây theo đúng chỉ thị của chủ dự án.

## DEC-125

Date:
2026-08-23

Task:
TASK-106 (adjustment_engine) — làm rõ nguồn dữ liệu và cơ chế trước khi
implement, theo cảnh báo để lại ở S011 (`PROJECT/PROJECT_PROGRESS.md` →
"Session tiếp theo" → Track A).

Decision:
`KpiAdjustment` (điều chỉnh giá nhập KPI: `Qua kho`, `NCC giao`, `KHBH`,
`Thợ lắp`) **không có nguồn trong 17 cột raw** (đã xác nhận lại ở S011, đọc
`docs/analysis/01_DATA_MAPPING.md` mục "Field trong Working Data không có
nguồn thô"). Đây là field **nhập tay sau khi import** — phương án (b) trong
hai phương án S011 nêu ra, không phải (a) chờ ERP xuất thêm cột.

Bốn quy tắc nghiệp vụ cụ thể, nguyên văn từ chủ dự án:

1. **Qua kho / NCC giao** — số tiền điều chỉnh phụ thuộc **phương tiện giao
   hàng**, không phụ thuộc model sản phẩm:
   - xe máy, hàng nhẹ (đồ gia dụng nhỏ): `-50`
   - xe máy, hàng cồng kềnh: `-100`
   - ô tô: `-200`
2. **KHBH / Thợ lắp** — chỉ có mặc định khi sản phẩm là **điều hòa**:
   `KHBH = -50`, `Thợ lắp = -200`. Ngoài điều hòa: **không có mặc định**,
   luôn nhập tay (không suy đoán, không coi 0).
3. **Nhận diện điều hòa** — dò trực tiếp trên `ProductRaw` (tên sản phẩm
   thô), vì file thô ghi rõ chữ "điều hòa" ngay trước mã model. Đã xác nhận
   khả thi trên dữ liệu thật tháng 01/2026 và 06/2026 (không cần bảng tra
   ProductCode).
4. **Cơ chế kích hoạt** — người dùng **chọn tay sau khi import** loại điều
   chỉnh áp dụng cho từng dòng/đơn (một dòng có thể cộng dồn nhiều loại,
   đúng như từ vựng thật ở `docs/analysis/03_RULE_CLASSIFICATION.md` §"Bảng
   Adjustment", ví dụ `Thợ lắp -200, KHBH -50`). Không có cơ chế nào tự động
   quét raw data rồi tự áp adjustment — không giống `PendingPriceProvider`
   (TASK-105), nơi "chưa có thì Pending" là đúng cho *mọi* dòng ở Phase 1.

Hệ quả kiến trúc: bốn quy tắc trên định nghĩa một **bộ tính giá trị đề xuất
mặc định** (`suggested amount` theo `adjustment_type` + `delivery_method` +
`is_air_conditioner`) để điền sẵn khi người dùng chọn tay — không phải một
bước tự động trong `run_import()`. Vì điểm 4 đòi hỏi màn hình chọn tay mà
Phase 1 chưa có UI/DB (ADR-101), TASK-106 ở Phase 1 chỉ giao **module tính
toán độc lập** (classifier điều hòa + resolver tra bảng số tiền đề xuất) —
không nối vào pipeline import. Tầng override thủ công + audit trail thật
(Phase 2/3, TASK-202/302/305) sẽ gọi tới module này sau.

Reason:
Chủ dự án trả lời 4 câu hỏi làm rõ (qua AskUserQuestion) sau khi cung cấp
gợi ý ban đầu mơ hồ về nhị phân "tuỳ model". Bốn câu trả lời cho thấy mô hình
đúng không phải "tự động parse từ raw" (giả định ban đầu mà S011 đã tự phát
hiện và sửa trước khi sai lan sang code) mà cũng không đơn giản là "luôn
nhập tay không gợi ý gì" — mà là gợi ý mặc định có điều kiện, người dùng
luôn có quyền ghi đè. Áp dụng đúng nguyên tắc DEC-103 (Pending/mặc định
không bao giờ suy đoán khi thiếu căn cứ) cho ba trường hợp không có mặc định
(non-AC KHBH/Thợ lắp).

Risk:
Trung bình-cao (4/5) — ảnh hưởng trực tiếp `KpiPurchasePrice` và do đó
`EligibleKpiProfit`/lương thưởng nhân viên (mục 11 đặc tả). Rủi ro cụ thể:
(a) từ khóa nhận diện điều hòa trên `ProductRaw` là text-matching, có thể bỏ
sót biến thể chính tả chưa thấy trong 2 tháng dữ liệu mẫu — cần Review Queue
cho case không khớp, không được coi non-AC là mặc định an toàn khi có nghi
ngờ; (b) resolver chỉ *đề xuất*, không tự áp — nếu tầng override tương lai
(Phase 2/3) không tôn trọng ranh giới "đề xuất, không phải final" này, có
thể vô tình biến default thành ghi đè im lặng, lặp lại đúng lỗi mà DEC-103
đang phòng.

Impact:
- `docs/tasks/TASK-106-adjustment-engine.md` — task file mới, phạm vi module
  tính toán độc lập (không nối `run_import()`), thay thế mô tả cũ ở
  `PROJECT/PROJECT_PROGRESS.md` (vốn viết "parse từ vựng điều chỉnh... thành
  kpi_purchase_adjustment" như thể có nguồn raw để parse).
- `config/adjustments.yaml` — file cấu hình mới cho 2 nhóm quy tắc (tier theo
  phương tiện; default theo điều hòa), theo đúng phân loại "B — Business
  rule" ở `docs/analysis/03_RULE_CLASSIFICATION.md`.
- `app/modules/adjustment/` — module mới: classifier điều hòa (dò
  `ProductRaw`) + resolver số tiền đề xuất. Không sửa `app/pipeline.py`.
- `app/modules/domain/models.py` — có thể thêm field liên quan
  `kpi_purchase_adjustment` dạng Optional (không mặc định 0), nhưng không
  điền tự động trong `run_import()`.
- `PROJECT/PROJECT_PROGRESS.md`, `PROJECT/LO_TRINH_DE_HIEU.md` — cập nhật mô
  tả TASK-106 theo phạm vi đã thu hẹp.
- Không đổi TASK-101, TASK-105 (đã DONE), không đổi thứ tự roadmap.

Can Revisit After:
Khi Phase 2/3 xây tầng override thủ công thật (TASK-202/302/305) — lúc đó
resolver này được gọi làm giá trị đề xuất ban đầu trên UI, và cần một ADR
hoặc DEC riêng nếu phát sinh yêu cầu audit trail cụ thể cho việc ghi đè.

## DEC-126

Date:
2026-08-23

Task:
TASK-107 (profit_engine) — nguyên tắc ranh giới trước khi implement, chủ dự
án chốt ngay sau khi chấp nhận TASK-106 DONE.

Decision:
Sáu nguyên tắc, nguyên văn từ chủ dự án, áp dụng cho `profit_engine`
(TASK-107) và cho thiết kế persistence Adjustment tương lai (Phase 2/3):

1. `AccountingProfit` hoàn toàn độc lập với KPI Adjustment — công thức
   `AccountingProfit = (SellPrice − AccountingPurchasePrice) × Quantity`
   không có số hạng nào liên quan `KpiPurchaseAdjustment`, đúng như đã ghi ở
   `docs/analysis/03_RULE_CLASSIFICATION.md` §U (khác `EligibleKpiProfit`,
   công thức có `OtherKpiAdjustment`).
2. Adjustment không ghi đè dữ liệu kế toán — `kpi_purchase_adjustment` (khi
   tồn tại) không bao giờ sửa `accounting_purchase_price`/`accounting_profit`;
   hai luồng số liệu (kế toán vs. KPI) tách biệt hoàn toàn ở mọi tầng, không
   chỉ ở công thức mà cả ở dữ liệu lưu trữ.
3. Persistence tương lai: một `Order` phải hỗ trợ **nhiều** Adjustment
   records — không phải một field đơn `kpi_purchase_adjustment` cộng dồn sẵn
   thành một số. Khớp với từ vựng thật đã quan sát (`docs/analysis/03_RULE_CLASSIFICATION.md`
   §"Bảng Adjustment": `Thợ lắp -200, KHBH -50` là 2 record, không phải 1 số
   -250 không rõ nguồn gốc).
4. Phân biệt `suggested_amount` (giá trị `AdjustmentResolver` đề xuất,
   DEC-125) và `final_amount` (giá trị người dùng xác nhận/ghi đè, lưu thật)
   — hai field khác nhau, không ghi đè lẫn nhau, giữ được cả đề xuất gốc lẫn
   quyết định cuối cùng cho audit trail.
5. Chỉ Adjustment đã được người dùng **xác nhận** (`final_amount` đã chốt)
   mới được dùng để tính `EligibleKpiProfit` — một `suggested_amount` chưa
   xác nhận không bao giờ lọt vào công thức KPI.
6. Không mặc định adjustment chưa xác định bằng 0 — đúng nguyên tắc DEC-103
   áp dụng lại: thiếu dữ liệu adjustment nghĩa là `EligibleKpiProfit` chưa
   tính được cho dòng đó (Pending), không phải bằng `AccountingProfit`.

Hệ quả trực tiếp cho TASK-107: task này **chỉ** triển khai `AccountingProfit`
theo đúng scope TASK-107 đã định (`docs/tasks/TASK-106-adjustment-engine.md`
mục "Ngoài phạm vi" đã tách sẵn ranh giới này). **Không** tự mở rộng sang
`EligibleKpiProfit` — persistence và cơ chế xác nhận (`final_amount`) của
Adjustment record chưa tồn tại (đó là TASK-202/302/305, Phase 2/3), nên chưa
có gì hợp lệ để tính `EligibleKpiProfit` lúc này. Đây không phải một giới
hạn kỹ thuật tạm thời — đây là ranh giới scope đúng, giống cách TASK-105 chỉ
làm `AccountingPurchasePrice`, không đụng `KpiPurchasePrice`.

Reason:
Nguyên tắc 1–2 xác nhận lại đúng những gì đã thiết kế ở TASK-105/106 (hai
luồng số liệu tách biệt), không thay đổi gì mới — chủ dự án nhắc lại tường
minh để không ai vô tình trộn lẫn khi implement TASK-107. Nguyên tắc 3–6 là
thông tin thiết kế mới, quan trọng cho persistence tương lai — ghi lại ngay
bây giờ (dù chưa implement) để TASK-202/302/305 không phải đoán lại từ đầu,
và để `AdjustmentResolver` (đã có từ TASK-106, chỉ trả `amount` +
`source_of_value`) được hiểu đúng là nguồn của `suggested_amount`, không
phải `final_amount`.

Risk:
Thấp cho TASK-107 (thu hẹp scope, giảm rủi ro so với mở rộng sang
`EligibleKpiProfit` khi chưa có persistence thật). Rủi ro nếu bỏ qua nguyên
tắc 5–6 ở Phase 2/3: một implementation vội vàng có thể coi `suggested_amount`
tương đương `final_amount` để "cho xong", làm dữ liệu KPI dùng số chưa ai
xác nhận — đúng lỗi mà DEC-103/125 đã phòng từ đầu. Ghi rõ ở đây để trở
thành tiêu chí kiểm tra bắt buộc khi TASK-202/302/305 mở, không phải điều
phải nhớ lại từ hội thoại.

Impact:
- `docs/tasks/TASK-107-profit-engine.md` — Scope giới hạn đúng
  `AccountingProfit`; Out of Scope nêu rõ `EligibleKpiProfit` bị chặn bởi
  nguyên tắc 3–6, không phải do thiếu thời gian.
- `app/modules/domain/models.py` — thêm `WorkingLine.accounting_profit`
  (Optional, không mặc định 0). **Không** thêm field Adjustment/`suggested_amount`/
  `final_amount` ở task này — đó là persistence thật, thuộc Phase 2/3.
- `app/modules/profit/` — module mới, không phụ thuộc `app/modules/adjustment/`.
- Không sửa `app/modules/adjustment/`, `config/adjustments.yaml` (đã DONE,
  TASK-106).
- Khi TASK-202/302/305 mở (Phase 2/3): thiết kế bảng/entity Adjustment phải
  có `order_id` (quan hệ 1-nhiều), `adjustment_type`, `suggested_amount`,
  `final_amount`, trạng thái xác nhận (confirmed/unconfirmed) — tài liệu
  tham khảo bắt buộc là DEC-126 này, không phải suy luận lại từ đầu.

Can Revisit After:
Không — đây là nguyên tắc kiến trúc nền tảng cho toàn bộ luồng Adjustment,
áp dụng xuyên suốt Phase 1–3, không phải quyết định tạm thời chờ xem lại.

## DEC-127

Date:
2026-08-23

Task:
TASK-108A — hợp nhất quyết định nghiệp vụ sau ba vòng pre-implementation
review (Gate v1 → v2 → v3), chủ dự án phê duyệt trực tiếp.

Decision:

**1. EmployeeGroup trở thành khái niệm tường minh.**
`Nội thành` **không còn** là một Employee. Vinh, Quý, Hiệp là **ba Employee
riêng biệt**, giữ nguyên danh tính, cùng thuộc `employee_group = NOI_THANH`.
Nhóm còn lại là `STANDARD_SALES`. Thêm/ngưng nhân viên là sửa master data,
không sửa mã nguồn; nhân viên nghỉ dùng `active: false` + `effective_to`,
không xóa khỏi lịch sử.

**2. `Gia dụng` là ProductGroup, không phải Employee, không phải
EmployeeGroup.** Không tạo employee tên `Gia dụng`. Chiều mới:
`ProductGroup = DIEN_MAY | GIA_DUNG`, mặc định `DIEN_MAY`.

**3. Chính sách quy đổi hiện hành:**
```
NOI_THANH + PERSONAL + DIEN_MAY → NOI_THANH_2  → 2 %
NOI_THANH + PERSONAL + GIA_DUNG → GIA_DUNG_8   → 8 %
```
**Không** áp `* + GIA_DUNG → 8 %` cho mọi nhân viên. Nhân viên
`STANDARD_SALES` bán cùng model vẫn dùng scheme theo group/nguồn của họ —
ví dụ Ly + PERSONAL = 5,5 %, đúng cách workbook lịch sử đang tính.

**4. ProductGroup ở cấp product line, không phải cấp OrderID.** Một OrderID
có thể chứa cả Điện máy lẫn Gia dụng. `ConversionScheme` do đó cũng xuống
cấp line. `LeadSource` **giữ nguyên cấp Order** (DEC-119 không đổi). Chuỗi
tổng hợp: `Product Line → Order → Employee → Month → Summary`. **Cấm** cộng
lợi nhuận của các line khác scheme rồi chia chung một tỉ lệ.

**5. Phase 1 phân loại ProductGroup hoàn toàn thủ công.** UI sau này có
checkbox `☐ Gia dụng`: không tick → `DIEN_MAY`, tick → `GIA_DUNG`. Checkbox
chỉ đổi `ProductGroup`, **không** hard-code hệ số 8 %; rate luôn tra qua
ConversionScheme/config. **Chưa** dùng danh sách 155 model lịch sử làm
business truth, **chưa** suy luận bằng keyword/tên sản phẩm, **chưa** triển
khai tự học `Model → ProductGroup` — vì cùng một model xuất hiện trong các
luồng có cách tính khác nhau (bằng chứng ở Reason).

**6. Provenance của ProductGroup phải phân biệt được mặc định với xác nhận
của người dùng:** `product_group_final = DIEN_MAY` + `source = DEFAULT` khác
với `= GIA_DUNG` + `source = MANUAL`. Dùng khuôn `_auto/_manual/_final` của
ADR-102; manual override phải có audit.

**7. Năm dimension độc lập:**
`Employee ≠ EmployeeGroup ≠ LeadSource ≠ ProductGroup ≠ ConversionScheme`.
ConversionScheme resolve từ tối thiểu
`Employee/EmployeeGroup + LeadSource + ProductGroup + effective date`.
**Cấm hard-code** tên nhân viên và các số 2 % / 5,5 % / 7,5 % / 8 % trong
business engine; mọi rate nằm ở config có effective-dating.

**8. `Linh`, `Fanpage` và 5 giá trị NVBH chưa map là legacy, không đưa vào
active master data.** Chúng trả `Unresolved` → Review Queue. Chỉ bổ sung kèm
`effective_from`/`effective_to` khi thực sự cần tái tạo lịch sử.

Reason:

Ba vòng review, mỗi vòng đóng một câu hỏi bằng dữ liệu thật chứ không bằng
suy đoán:

- **Vì sao tách Vinh/Quý/Hiệp:** gộp ba người thành một Employee giả tên
  "Nội thành" làm mất danh tính nhân viên, trong khi file thô toàn công ty
  ghi rõ ba giá trị `NVBH` riêng với khối lượng lớn (Hiệp 5.328 dòng, Quý
  2.810, Vinh 1.814). Group là thứ dùng chung scheme, không phải thứ thay
  thế con người.
- **Vì sao `GIA_DUNG_8` khóa trên `NOI_THANH` chứ không trên `*`:** đối
  chiếu file thô toàn công ty với danh sách mã Gia dụng của workbook cho
  thấy 663 dòng khớp, chia **436 (66 %) thuộc NOI_THANH** và **227 (34 %)
  thuộc STANDARD_SALES**. Nếu áp `* + GIA_DUNG → 8 %`, 227 dòng đó sẽ lệch
  khỏi cách workbook lịch sử đang tính (Ly bán cùng model vẫn 5,5 %).
- **Vì sao ProductGroup phải ở cấp line:** đo trên dữ liệu thật, **118 trên
  10.609 OrderID chứa đồng thời cả hai loại**. Gán một scheme cho cả đơn sẽ
  tính sai 118 đơn. Đây là số đo, không phải phòng xa.
- **Vì sao chưa tự học `Model → ProductGroup`:** 50 trong 155 mã Gia dụng
  cũng xuất hiện ở sheet nhân viên cá nhân — cùng một mã máy đi qua hai luồng
  có tỉ lệ khác nhau. Một bộ tự học dựa trên mã sẽ học sai ngay từ đầu.

Risk:

Cao nhất roadmap (5/5) — sai ở đây là sai lương/thưởng của người thật.
Rủi ro cụ thể còn lại:

- **Chưa phân loại được ProductGroup ở Phase 1** → mọi dòng là `DIEN_MAY`,
  nên các dòng Gia dụng của kênh Nội thành sẽ quy đổi ở 2 % thay vì 8 % cho
  tới khi có UI checkbox. Đây là **hệ quả đã biết và được chấp nhận** của
  quyết định 5, không phải lỗi; `source_of_value = DEFAULT` làm nó nhìn thấy
  được, không im lặng.
- **Trộn tầng gộp:** nếu tầng báo cáo (TASK-109/111) vô tình tổng hợp theo
  `employee_group` rồi chia một tỉ lệ, sẽ tái lập đúng lỗi mà quyết định 4
  cấm. Cần một check riêng ở TASK-109.

Impact:
- `config/employees.yaml` — thêm `employee_groups`; 3 dòng đổi `normalized`
  từ `Nội thành` sang `Vinh`/`Quý`/`Hiệp`; 8 dòng thêm `group`.
- `config/conversion_rates.yaml` — file mới, 4 dòng scheme, 4 chiều.
- `app/modules/mapping/employee_mapper.py` — `MappingResult` thêm `group`.
- `app/modules/domain/models.py` — thêm `employee_group`, `product_group_*`,
  `conversion_scheme_*`, `conversion_rate_final`.
- `app/modules/conversion/`, `app/modules/product/` — module mới.
- `app/pipeline.py` — bước 10, chạy ở cấp line.
- `docs/adr/ADR-106-*.md` — ADR mới cho ProductGroup + granularity.
- `tools/analysis/verify_ads_rule.py` — bảng scheme 4 chiều, case E/F đổi
  tên nhân viên, `float` → `Decimal`. Phải giữ 31/31 PASS.
- `tests/test_employee_mapper.py`, `tests/test_pipeline.py` — sửa assert
  `"Nội thành"` thành tên riêng. Đây là **hệ quả của rule mới**, không phải
  sửa test để làm nó PASS.
- `docs/analysis/10_OPEN_QUESTIONS.md` — C11 cập nhật số thật (107 dòng /
  5 người, thay cho 88); thêm **C15** cho `EligibleCosts`.
- **Không** đụng `app/modules/pricing/`, `profit/`, `adjustment/`,
  `orders/`, `lead_source/`, `importing/`.

Can Revisit After:
Quyết định 5 (phân loại thủ công) mở lại khi Phase 2/3 có UI thật và đủ dữ
liệu đã-được-người-dùng-xác-nhận để cân nhắc tự học. Quyết định 1–4, 6–8 là
nền tảng, không dự kiến đổi.

## DEC-128

Date:
2026-08-23

Task:
TASK-110 — Gate / Readiness Review (trước khi có dòng code nào)

Decision:

Bốn khoảng trống nghiệp vụ của mục §18 đặc tả, chủ dự án trả lời trực tiếp
trong phiên Gate Review. Ghi lại nguyên vẹn vì cả bốn đều đổi kết quả mà công
cụ xuất ra, không chỉ đổi cách hiển thị.

**1 — `Missing: thiếu giá nhập` nén thành một mục tổng hợp.**
`price_source == Pending` là **trạng thái hệ thống đã biết** (DEC-103: chưa có
Price Master), không phải lỗi dữ liệu của từng dòng. Review Queue hiển thị
**một** mục duy nhất dạng "N dòng đang chờ giá nhập", không phải N mục. Quy
tắc per-row chỉ bật khi Price Master tồn tại (TASK-401).

**2 — `Suspicious: lợi nhuận âm` tách làm hai loại có cơ sở khác nhau.**
- Loại tính toán: dựa trên `accounting_profit` và `accounting_purchase_price`.
  Viết đúng ngay bây giờ, có test, nhưng **nằm im ở Phase 1** (0 phát hiện, vì
  `accounting_profit is None` ở 100% dòng). Tự sống dậy khi có Price Master.
- Loại ERP: một loại **riêng biệt**, dựa trên `source_profit` (1.912/11.765
  dòng âm), nhãn ghi rõ là tín hiệu từ ERP **chưa kiểm chứng**.
  `docs/analysis/01_DATA_MAPPING.md` §3 đã dự liệu đúng việc này.

**3 — Dòng phụ và Duplicate.**
- `SL ≤ 0` / `giá bán = 0`: dùng một **danh sách từ khóa dòng phụ trong
  config** để hạ 1.261 dòng hợp lệ (`Chi phí vận chuyển`, `Chênh VAT`…) xuống
  `INFO` thay vì `Suspicious`. Đây là biện pháp giảm nhiễu, **không** thay thế
  Product/Transaction Classification đầy đủ — mục §17 vẫn thuộc TASK-103.
- `Duplicate`: định nghĩa của đặc tả (`cùng source_file + source_row`) là bất
  khả thi trong một lần import — cặp đó duy nhất theo cấu tạo. Thay bằng
  **trùng `row_hash` trong cùng một lần import**, mức `WARNING` (hai dòng phụ
  kiện giống hệt nhau có thể hợp lệ). Chống trùng khi **import lại cùng một
  file** cần persistence — dời sang TASK-201, ghi tường minh là out-of-scope.

**4 — Đơn có hai nhân viên khác nhau: chỉ phát hiện, không đổi hành vi.**
`order_builder` hiện lấy nhân viên của **dòng đầu tiên**, nên cả đơn nhận tỉ
lệ quy đổi của người đó. TASK-110 đưa đơn đó vào Review Queue ở mức cao nhất
nhưng **không** đổi cách tính.

Reason:

Điểm 1–3: giữ Review Queue ở mức người thật đọc nổi. Một hàng chờ 11.765 mục
"thiếu giá nhập" và hàng nghìn mục "vận chuyển SL = 0" sẽ bị bỏ qua toàn bộ —
lúc đó cảnh báo thật cũng chết theo. Điểm 2 tách hai cơ sở vì trộn chúng lại
sẽ khiến một con số ERP chưa kiểm chứng trông như đã kiểm chứng, đúng loại
nhầm lẫn DEC-103 tồn tại để chặn.

Điểm 4: chủ dự án chọn giữ ranh giới quy trình. Đổi cách tính tiền là việc của
một quyết định nghiệp vụ riêng, không phải hệ quả phụ của một task validation.

Impact:

Phạm vi TASK-110 thành **7 loại cảnh báo**, không phải 5. Difficulty 2 → 3,
Risk 2 → 3 (Risk 3 kéo theo **E1 bắt buộc** cho mọi check REQUIRED, theo
`governance/core/EVIDENCE_STANDARD.md`).

**Rủi ro tồn dư đã chấp nhận (điểm 4):** cho tới khi có người duyệt hàng chờ,
một đơn có hai nhân viên vẫn xuất ra con số sai KPI cho cả hai người. Công cụ
làm cho nó **nhìn thấy được**, không làm cho nó **không xảy ra**. Cần đo quy
mô thật ở GATE-01.

Điểm 3 tạo một phụ thuộc mềm lên TASK-103: nếu danh sách từ khóa lệch khỏi
bảng Classification khi §17 được làm, hai chỗ sẽ nói hai điều khác nhau về
cùng một dòng. TASK-103 phải kiểm tra lại danh sách này.

Can Revisit After:
Điểm 1 tự hết hiệu lực khi TASK-401 có Price Master. Điểm 3 (Duplicate) mở lại
ở TASK-201 khi có persistence. Điểm 4 nên mở lại ở GATE-01, sau khi đo được
thật sự có bao nhiêu đơn bị mâu thuẫn nhân viên và số tiền liên quan.

## DEC-129

Date:
2026-08-23

Task:
TASK-110 — Independent Review #1 (FAIL, 6 finding)

Decision:

Ba quyết định của chủ dự án trong đợt Independent Review #1. Ghi lại để chúng
trở thành **canonical**, không còn là hành vi triển khai nằm ngoài Scope Lock —
đây chính là Finding 2 của đợt review.

**1 — HD-110-01: F1–F5 được phép vào Review Queue (Scope Expansion APPROVED).**
Bảng phạm vi freeze ban đầu ghi V7 là "F2 và F4". Bản triển khai đưa cả
`hard_failures` (F1/F3/F5) vào hàng chờ ở mức `ERROR`. Reviewer xếp đó là
scope creep — đúng về thủ tục, kể cả khi kết quả là thứ nên có. Chủ dự án
**duyệt chính thức**: F1/F3/F5 là invariant nghiêm trọng và được phép vào
queue. Bảng phạm vi của TASK-110 sửa V7 thành **F1–F6**.

**2 — HD-110-02: heuristic từ khóa dòng phụ được duyệt TẠM THỜI.**
Phase 1 được dùng heuristic từ khóa vì TASK-103 (Product/Transaction
Classification, mục §17 đặc tả) chưa có. Hai ràng buộc kèm theo:
- **Không chấp nhận literal `"phí "`** (dấu cách cuối) làm semantic lâu dài.
  Khớp phải có chuẩn hóa và ngữ nghĩa biên từ rõ ràng.
- **Cấm chỉnh rule để tái tạo con số lịch sử 1.261.** Con số đó do bộ lọc
  regex cũ trong `tools/analysis/extract_evidence.py` đo ra; nó là **mốc tham
  chiếu**, không phải mục tiêu. Chênh lệch phải giải thích, không được tune.
- Đây là **giải pháp tạm**, **TASK-103 phải thay thế** chứ không kế thừa.

**3 — HD-110-03: thêm tiêu chí F6 — nhân viên `inactive` mà vẫn có dòng.**
Finding 3 yêu cầu gỡ `inactive` khỏi `Missing.employee` (đúng: nhân viên đã
được nhận diện, không có gì "thiếu"). Nhưng gỡ xong thì trạng thái đó **không
còn tín hiệu nào ở đâu cả**: `conversion_engine` cho `inactive` đi qua y hệt
`mapped` (chỉ `unmapped` bị chặn về `Unresolved` theo DEC-127 §8), nên doanh
số vẫn chảy vào KPI của người đã bị đánh dấu là nghỉ. Không quyết định nào
(§18, DEC-104, DEC-127, DEC-128, F1–F5) phủ trường hợp này.

Chủ dự án chọn: báo bằng một tiêu chí **F6** trong loại `EmployeeMapping` đã
có, mức `WARNING`, kèm provenance (tên nhân viên, số dòng, dòng nguồn).
**Không** thêm mã loại mới, **không** đổi cách tính, **không** đổi KPI
ownership.

Reason:

Điểm 1: một hành vi đúng nhưng nằm ngoài phạm vi đã freeze vẫn là scope creep.
Cách sửa là làm cho phạm vi nói ra điều đó, không phải biện minh cho hành vi.

Điểm 2: `"phí "` không phải một nghĩa, nó là một mẹo thay cho "hết từ ở đây".
Nó bỏ sót giá trị kết thúc bằng từ đó, và mời người sau gỡ dấu cách — lúc đó
`"phí"` khớp `"bàn phím"` và một sản phẩm thật bị hạ xuống INFO mà không ai
biết. Còn việc khóa danh sách vào con số 1.261 biến một phép kiểm thành một
phép chép: nó chỉ chứng minh rule khớp với rule cũ, không chứng minh rule đúng.

Điểm 3: im lặng ở đây là đúng loại im lặng mà TASK-110 tồn tại để chặn — một
người bị đánh dấu đã nghỉ nhưng vẫn đang bán hàng, và tiền vẫn chạy về tên họ.
Nhưng sửa cách tính là việc của một quyết định riêng, nên F6 chỉ **báo**.

Impact:

- Bảng phạm vi TASK-110: V7 = **F1–F6**, không phải "F2 và F4".
- `app/modules/validation/text.py` (mới) sở hữu chuẩn hóa NFC + gộp khoảng
  trắng + case-folding + khớp biên từ, dùng chung cho cả từ khóa lẫn
  `ProductRaw`.
- `config/validation.yaml`: `"phí "` → `"phí"`; danh sách rút về 5 từ khóa
  mang nghĩa, kèm ghi chú cấm tune theo con số lịch sử.
- **CHECK-110-16 đổi cách đọc, không đổi mức độ nghiêm ngặt:** bảng số trong
  check đó (2 / 52 / 1.912 / **1.261** / 11.765) nay là **mốc tham chiếu**.
  Con số 1.261 do bộ lọc substring cũ đo ra; ngữ nghĩa biên từ mới có thể cho
  con số khác một cách chính đáng. Chênh lệch phải **giải thích bằng văn bản**
  — vẫn cấm chỉnh ngưỡng cho khớp, và nay cấm cả chiều ngược lại.
- F6 tạo một phụ thuộc mềm lên master data: nếu người nào được set
  `active: false` mà `effective_to` chưa đóng, F6 sẽ kêu mỗi lần import cho
  tới khi config được sửa. Đó là hành vi mong muốn, không phải nhiễu.

Can Revisit After:
Điểm 2 hết hiệu lực khi **TASK-103** làm xong — lúc đó heuristic phải bị gỡ,
không phải để lại chạy song song. Điểm 3 nên xem lại ở GATE-01 nếu chủ dự án
muốn `inactive` không nhận tỉ lệ (đó sẽ là đổi business calculation, cần một
DEC riêng và sửa `conversion_engine`). Điểm 1 là nền tảng, không dự kiến đổi.

## DEC-130

Date:
2026-08-23

Task:
TASK-110 — Independent Review #3 (FAIL, 3 finding)

Decision:

**HD-110-04 — Giao dịch thiếu ngày không được phát F6.**

Một dòng thô không có ngày (`date is None`) **không bao giờ** sinh cảnh báo F6
(nhân viên `active: false` mà vẫn có dòng). Lý do: không có ngày thì **không
đủ bằng chứng** để xác định bản ghi master data nào đang có hiệu lực cho dòng
đó.

Ràng buộc kèm theo, chủ dự án nêu tường minh:

- `Missing.date` **vẫn phải phát** — dòng đó vẫn là dữ liệu thiếu, và đó mới
  là việc cần sửa trước.
- **Không** chọn bản ghi đầu tiên (hay bất kỳ bản ghi nào) để suy ra F6.
- **Không** khẳng định giao dịch nằm trong cửa sổ hiệu lực nào khi ngày chưa
  biết.
- **Không** tạo loại business rule mới cho tình huống này.
- **Không** đổi hành vi `EmployeeMapper` / Conversion / KPI trong TASK-110.

Reason:

`select_effective_record` mô phỏng đúng `EmployeeMapper.resolve`, và mapper —
khi `as_of is None` — bỏ qua bộ lọc `effective_rows` rồi chọn prefix dài nhất.
Với một cặp bản ghi bàn giao (bản cũ `active: false` đã đóng `effective_to`,
bản mới `active: true`), điều đó khiến F6 bắn từ bản ghi cũ **chỉ vì dòng
không có ngày** — đo được: mapper trả `inactive`, F6 = 1.

Đó là một cáo buộc dựng lên từ một ẩn số. Cảnh báo "người này đã nghỉ mà vẫn
có doanh số" là cáo buộc về master data của một người thật; phát nó khi không
biết dòng thuộc kỳ nào là biến một dữ liệu thiếu thành một kết luận. Im lặng ở
đây **không** phải nuốt tín hiệu — dòng đó đã được `Missing.date` báo, và khi
ngày được điền thì F6 tự trả lời được ở lần import sau.

Impact:

- `evaluate_inactive_records()` bỏ qua dòng `date is None`, có ghi chú lý do
  ngay tại chỗ.
- Guard đặt ở `evaluate_inactive_records`, **không** ở `select_effective_record`
  — hàm đó phải tiếp tục phản chiếu `EmployeeMapper` nguyên vẹn, và
  `test_f6_record_selection_agrees_with_the_production_employee_mapper` khẳng
  định điều đó.
- Không đổi `employee_mapping_status`, không đổi conversion, không đổi KPI.
- Bảng phạm vi TASK-110, dòng V7: F6 nay ghi rõ **cần có ngày giao dịch**.

Can Revisit After:
Khi có persistence + màn hình sửa dữ liệu (TASK-201/302), một dòng thiếu ngày
sẽ được điền ngày trước khi vào báo cáo, nên tình huống này tự hết. Nếu sau
này chủ dự án muốn một cảnh báo riêng cho "không đủ dữ kiện để chẩn đoán", đó
là một loại mới và cần một quyết định riêng — DEC-130 cố ý **không** tạo nó.

## DEC-131

Date:
2026-08-23

Task:
TASK-110 — Independent Review #4 (FAIL, 2 provenance defect + 1 Human Decision)

Decision:

**HD-110-05 — F3 chỉ được đánh giá khi dòng thô có ngày giao dịch.**

Nếu một dòng thô thiếu ngày:

- **phát `Missing.date`** theo rule hiện tại;
- **KHÔNG phát F3**;
- **không** suy luận những employee/master record nào đang cùng hiệu lực;
- **không** biến các cửa sổ hiệu lực **rời nhau** thành ambiguity;
- **không** tạo thêm loại warning mới trong TASK-110.

Reason:

F3 mang nghĩa **"nhiều master record cùng hợp lệ tại thời điểm của dòng đó"**.
Không có ngày thì không có thời điểm, nên không đủ bằng chứng để khẳng định
điều đó.

Bản trước dùng biểu thức `(when is None or _overlaps(...))` — nghĩa là một
dòng thiếu ngày khớp **mọi** prefix bất kể cửa sổ hiệu lực. Hệ quả: hai bản
ghi bàn giao có cửa sổ **rời nhau** (đúng cách DEC-121 diễn đạt một lần chuyển
giao) bị biến thành một đụng độ, chỉ vì dòng đó thiếu ngày.

Đây là cùng một nguyên tắc đã chốt ở **HD-110-04** cho F6, nay áp cho F3: một
cáo buộc về master data không được dựng lên từ một ẩn số. Dòng đó đã được
`Missing.date` báo — và đó mới là thứ cần sửa; sửa xong thì F3 tự trả lời được
ở lần import sau.

Impact:

- Guard đặt trong `collect_mapping_stats` (bộ thu của **production**), **không**
  trong `evaluate_raw_mapping`. Script phân tích
  `tools/analysis/reconcile_conversion.py` tự dựng `ambiguities` của nó và phải
  giữ nguyên hành vi đã ký ở CHECK-108A1-15.
- Cùng lý do đó, việc **quy một dòng về một bản ghi config** (`rows_by_record`,
  nền của F1 và F6) cũng chỉ làm cho dòng **có ngày**. Không có ngày thì bộ lọc
  cửa sổ hiệu lực không áp dụng được, nên bản ghi chọn ra sẽ là phỏng đoán.
  Đây là hệ quả trực tiếp của HD-110-04/HD-110-05, **không** phải một rule mới:
  nó chỉ khiến `affected_count` của F1 thận trọng hơn, không tạo cảnh báo nào.
- **Không** đổi hành vi `EmployeeMapper` / Conversion / KPI trong TASK-110.
- Bảng phạm vi TASK-110, dòng V7: F3 nay ghi rõ **cần có ngày giao dịch**.

Can Revisit After:
Khi có persistence + màn hình sửa dữ liệu (TASK-201/302), dòng thiếu ngày sẽ
được điền trước khi vào báo cáo nên tình huống tự hết. Nếu chủ dự án muốn một
cảnh báo riêng cho "không đủ dữ kiện để chẩn đoán", đó là một loại mới và cần
quyết định riêng — DEC-131 cố ý **không** tạo nó, đúng như DEC-130.

## DEC-132

Date:
2026-08-23

Task:
TASK-110 — Architecture Repair sau Independent Review #5

Decision:

Ba quyết định của chủ dự án (HD-110-06, HD-110-07, HD-110-08), chốt sau khi
Architecture Audit chỉ ra rằng bốn finding của Review #5 chỉ là bốn biểu hiện
của **một** root cause: validation TÁI TẠO LẠI các sự thật mà production đã
biết, thay vì NHẬN LẠI chúng — cộng thêm việc data model của finding còn chừa
một kênh song song cho provenance đi vào từ ngoài đường dẫn xuất.

**1 — HD-110-06: `raw_prefix` rỗng hoặc thiếu là CẤU HÌNH SAI.**

Master data nhân viên bị từ chối ngay khi load nếu một bản ghi:
thiếu `raw_prefix`, để `raw_prefix` rỗng, hoặc để `raw_prefix` chỉ có khoảng
trắng. Ngữ nghĩa `raw_prefix: "" = catch-all` **không** được hỗ trợ.

Cùng lúc, schema tối thiểu của mỗi bản ghi được cưỡng chế: `raw_prefix` và
`normalized` bắt buộc và không rỗng sau khi trim; `group` bắt buộc; `active`
bắt buộc và phải là boolean thật.

Phần validate này đặt ở `app/modules/mapping/employee_mapper.py`, **không**
đặt vào `app/modules/config/loader.py`: loader tuyên bố ngay trong docstring rằng nó chỉ
giữ cơ chế generic, còn ngữ nghĩa đặc thù domain thuộc về consumer.

**2 — HD-110-07: chỉ còn MỘT nguồn sự thật cho việc chọn employee record.**

`EmployeeMapper` công bố `RecordRef`, `resolve_record()`,
`candidate_records()`, `record()` và `records`. `resolve()` được viết TRÊN
`resolve_record()`. `WorkingData` mang chính instance mapper của production và
truyền nó cho `Validator`; validation hỏi lại mapper thay vì đoán lại bằng
giá trị.

Xóa hẳn: `select_effective_record`, `_record_key`, và vòng khớp prefix riêng
trong `collect_mapping_stats`. `_record_label` chỉ còn dùng để render cho
người đọc, tuyệt đối không làm khóa tra cứu.

**KHÔNG** thêm field nào vào `WorkingLine` / `Order`.

**3 — HD-110-08: F3 dùng đúng matching semantics của production.**

Nếu production coi một chuỗi raw là `unmapped` thì validation không được
normalize theo một bản cài đặt riêng rồi kết luận F3 ambiguity. Thay đổi
diagnostic output do loại bỏ drift này được chấp thuận.

**4 — Provenance phải bất khả biểu diễn sai, không phải "nhớ đừng làm sai".**

`MappingFinding` **không còn** trường `details: dict`. `ReviewItem` **không
còn** field `affected_count` và `source_row` — cả hai là property dẫn xuất từ
`RowProvenance`. Các khóa mang thông tin dòng (`source_rows`, `raw_variants`,
`ambiguous_rows`, `conflicting_records`) thuộc quyền sở hữu của
`RowProvenance` và bị từ chối nếu caller cố ghi vào `diagnostics`.

Reason:

Bốn vòng review liên tiếp đều đóng đúng cái representation mà reviewer chỉ
ra, rồi vòng sau tìm ra cái kế tiếp: `source_row` → `source_rows` →
`raw_variants` → `ambiguous_rows` → `details`. Đó là đóng một cửa trong một
căn phòng còn nhiều cửa. Cơ chế sinh ra chúng vẫn nguyên vẹn suốt cả bốn vòng.

Đoán lại một sự thật bằng giá trị có đúng hai chế độ hỏng, và cả hai đã xảy ra
và đã được đo tại commit `8386d34`:

- **drift** — `EmployeeMapper` nhận `raw_prefix` rỗng, `select_effective_record`
  loại nó; `EmployeeMapper` raise `KeyError` khi thiếu key, validation trả
  `None`; `collect_mapping_stats` khớp trên chuỗi đã normalize còn production
  khớp trên chuỗi thô, nên `'Đức  Kiên 0867'` bị F3 (mức ERROR) kết tội
  ambiguous trong khi production để nó `unmapped`;
- **collision** — hai bản ghi trùng khít `normalized` + `raw_prefix` + cửa sổ
  hiệu lực nhưng khác `active`/`group` cho ra cùng một `_record_key`, nên F6
  của bản ghi đã đóng nhặt đúng các dòng mà production gán cho bản ghi đang
  hoạt động, và tố cáo một nhân viên đang làm việc.

Còn `details` là kênh khóa tùy ý được `validator.py` sao chép nguyên trạng:
`frozen=True` chỉ đóng băng tham chiếu tới dict chứ không đóng băng nội dung
nó, nên "frozen dataclass" ở đây là bảo đảm giả.

Prefix rỗng bị cấm vì `"".startswith` khớp **mọi** chuỗi: nó lặng lẽ biến
thành catch-all và dời quyền sở hữu KPI của mọi dòng chưa map sang một người,
do một lỗi gõ. Nổ to lúc load tốt hơn tính sai lặng lẽ lúc chạy. Việc này
**không** xung đột §18: §18 cấm chặn import vì **dữ liệu xấu**, còn cấu hình
hỏng luôn được phép fail-fast — cùng lằn ranh mà `validator.py` đã phát biểu
từ đầu cho một severity gõ sai trong `validation.yaml`.

Impact:

- Không đổi: employee business mapping result, conversion scheme/rate, KPI
  ownership, pricing, profit, order ownership, lead source, TASK-108B,
  TASK-109. Chứng minh bằng CHECK-110-18 (ma trận 972 tổ hợp raw × as_of) và
  CHECK-110-19 (đầu ra nghiệp vụ đầu-cuối), cả hai so với ảnh chụp lấy tại
  commit `8386d345b04b754c061ce03b79116e75f0dfae4e` **trước** dòng sửa đầu tiên.
- `tools/analysis/reconcile_conversion.py` không sửa một byte; `norm`,
  `_overlaps` và chữ ký vị trí của `evaluate_raw_mapping` giữ nguyên
  (CHECK-110-20, CHECK-110-14, CHECK-108A1-15).
- HD-110-03, HD-110-04, HD-110-05 và DEC-129/130/131 giữ nguyên toàn bộ — audit
  không tìm thấy xung đột canonical nào với chúng.
- `Validator.__init__` nhận `employee_mapper` thay cho `employee_rows`;
  `ReviewItem` nhận `provenance` / `batch_source_file` / `diagnostics` thay cho
  `source_file` / `source_row` / `affected_count` / `details`. `details` vẫn đọc
  được như cũ, dưới dạng property dẫn xuất.
- CHECK-110-16 tiếp tục **BLOCKED** — vẫn cần file thô production.

Can Revisit After:
Khi TASK-201 thêm persistence cho Review Queue, `RowProvenance` sẽ là thứ được
ghi xuống; lúc đó cần xem lại biểu diễn lưu trữ, nhưng bất biến thì không đổi.
Nếu về sau master data nhân viên cần một `id` ổn định (ví dụ để tham chiếu
xuyên file), đó là phương án A trong Architecture Repair Plan và cần một DEC
riêng — DEC-132 cố ý chưa tạo nó, vì `RecordRef` đã đủ để loại bỏ collision
trong phạm vi một mapper instance canonical.

## DEC-133

Date:
2026-08-23

Task:
TASK-110 — Architecture Repair Gate #2, sau Independent Review #6

Decision:

Ba quyết định của chủ dự án (HD-110-09, HD-110-10, HD-110-11), chốt sau
Architecture Repair Gate #2. Gate chỉ ra rằng sáu finding của Review #6 có một
root cause chung, và root cause đó là **của chính bản sửa lần trước**:

> Repair #1 thay giá trị sai bằng giá trị dẫn xuất, nhưng giữ nguyên
> **ENUMERATION** làm cơ chế cưỡng chế ở mọi biên: danh sách đen (4 khoá), chỉ
> số vị trí (`index`), danh sách trắng (9 trường oracle). Một liệt kê chỉ đầy
> đủ do may mắn, và cả sáu finding đều là một chỗ mà liệt kê thiếu.

**1 — HD-110-09: `employee.group` không có trong `employee_groups` là CẤU HÌNH
SAI, fail-fast tại canonical master loader.**

Đây **không** phải luật vệ sinh. `employee_group` là một chiều tra
`config/conversion_rates.yaml`, nên một group gõ sai rơi khỏi dòng cụ thể và
rớt xuống dòng `"*"`. Đo được: `NOI_THANH` → `NOI_THANH_2` rate **2,0 %**;
`NOI_THAN` (thiếu một chữ H) → `PERSONAL_5_5` rate **5,5 %**. Một lỗi gõ dời tỉ
lệ quy đổi 175 %, im lặng, và tín hiệu duy nhất trước đây là một dòng ERROR
trong hàng chờ *không chặn import*.

Quyết định này **thu hẹp DEC-129 §1** (HD-110-01), dựa trên bằng chứng chưa tồn
tại khi DEC-129 được chốt. DEC-129 **không** bị sửa hay xoá; F1 vẫn tồn tại và
vẫn chạy trên đường phân tích và test bypass validate.

Lằn ranh chạy theo đúng một chiều và không được nới: một **dòng giao dịch** hỏng
KHÔNG bao giờ được biến thành config failure — nó vào Review Queue y như trước
(§18 đặc tả).

**2 — HD-110-10: một biên nạp master canonical duy nhất.**

`load_employee_master()` là điểm nghẽn duy nhất. Cho phép sửa **tối thiểu**
`tools/analysis/reconcile_conversion.py`: thay hai đường `load_yaml` employee
master thô bằng `load_employee_master()`. **Không** đổi logic đối chiếu,
**không** đụng vòng khớp prefix riêng đã freeze. Config hợp lệ phải giữ output
byte-identical (CHECK-108A1-15).

**3 — HD-110-11: business oracle structural, không danh sách trắng.**

Oracle L2 dẫn xuất bằng `dataclasses.fields()`, phủ **mọi** trường. Trường
chứa PII lưu **digest**, không lưu giá trị thô. Không được quay lại danh sách
trắng.

Kèm theo, các invariant kiến trúc được freeze ở Gate #2:

- **P — Provenance.** Machine-readable row provenance chỉ tồn tại ở
  `RowProvenance`. `ReviewItem` **không lưu** `dict[str, str]` nào; `details`
  là projection lúc đọc, tính từ payload có kiểu + provenance của chính item.
- **I — Immutability.** Bất biến **sâu**: collection bị ép sang tuple và **sao
  chép** ở biên. `frozen=True` chứa alias mutable không được coi là bất biến.
- **M — Mapper ownership.** `EmployeeMaster` là snapshot bất biến có
  `snapshot_id` dẫn từ nội dung; `RecordRef` mang `snapshot_id`; ref lạ bị từ
  chối; `Validator` nhận nguyên bundle `WorkingData`.
- **C — Configuration integrity.** Master invalid fail trước khi xử lý
  transaction.
- **L — Loader.** Mọi consumer đi qua biên canonical.
- **O — Oracle.** Structural, không liệt kê.

Reason:

Repair #1 (DEC-132) đóng đúng các *thể hiện* mà Review #5 chỉ ra, nhưng để lại
dạng *tổng quát*. Bằng chứng đo tại `ed38fd6`:

- `diagnostics` là `dict[str, str]` của **caller**, nên sửa nó sau khi
  `__post_init__` đã chạy vẫn vào được `details`; một khoá ngoài danh sách
  (`cac_dong_lien_quan`) đi thẳng vào; và với item batch-scoped thì phép
  "provenance đè lên" không chạy nên khoá lạ lọt hẳn.
- `RowProvenance(rows=[...])` nhận list: append vào list đó làm
  `affected_count` nhảy 1 → 2 **sau** khi item đã dựng xong. `AmbiguousRow.
  records` cũng vậy — kể cả trên đường "dẫn xuất".
- `RecordRef(index, label)` nêu một *vị trí* mà không nêu *vật chứa*:
  `A.record(ref)` trả `'Ly'` còn `B.record(ref)` trả `'Kiên'`, im lặng; và hai
  ref của hai master **bằng nhau và cùng hash**.
- Oracle L2 liệt kê 9 trong 34 trường `WorkingLine`: cộng 999.999 vào
  `total_sales` của **mọi** dòng và đổi `price_source` — oracle vẫn PASS.

Vị trí không kèm vật chứa không phải danh tính, nó là offset. Danh sách đen
dài hơn không đóng được một kênh; chỉ có việc **không còn chỗ để đặt khoá** mới
đóng được.

Impact:

- Không đổi: employee business mapping result, conversion scheme/rate, KPI
  ownership, pricing, profit, order ownership, lead source, TASK-108B,
  TASK-109. Chứng minh bằng CHECK-110-19 (972 tổ hợp raw × as_of) và
  CHECK-110-20 (oracle structural 66 trường), cả hai so với ảnh chụp lấy tại
  `ed38fd6` **trước** dòng sửa đầu tiên (commit `4ab3df0` chỉ chứa fixture,
  diff trên `app/` và `tools/` là rỗng — provenance kiểm được bằng git).
- DEC-128 → DEC-132 **không** bị sửa. DEC-129 §1 bị **thu hẹp** bởi quyết định
  1 ở trên, và điều đó được ghi ở đây chứ không ghi đè lên DEC-129.
- `Validator.__init__` nhận `employee_mapper`; `employee_groups` nay thuộc
  chính master snapshot. `ReviewItem` nhận `diagnostics: Diagnostics` có kiểu.
- **Canonical migration của expected failure mode — ĐÃ GIẢI QUYẾT.**
  HD-110-09 va với hai test trong `tests/test_reconcile_raw_integration.py`,
  một file thuộc diện MUST NOT CHANGE:
  `test_group_renamed_out_of_existence_fails` và
  `test_declared_group_deleted_fails`. Chủ dự án duyệt phương án A: nới MUST
  NOT CHANGE cho **đúng hai hàm test đó**, giữ nguyên ý định gốc và cập nhật
  cơ chế kỳ vọng:

      trước   phát hiện SAU khi đối chiếu   -> `reconcile_raw()` exit code > 0
      sau     từ chối TRƯỚC khi đối chiếu   -> `InvalidEmployeeConfig` tại
                                               canonical employee master loader

  Cơ chế mới **mạnh hơn hẳn**: lượt chạy bị từ chối trước khi đọc một giao
  dịch nào, thay vì báo cáo sau khi toàn bộ phép đối chiếu đã tính xong. Ý
  định của hai test — "employee master có group reference hỏng KHÔNG được đi
  lọt" — không đổi một chữ.

  Ràng buộc đã giữ: **không** lùi HD-110-09; **không** tạo bypass referential
  validation; **không** đổi hành vi production để test cũ PASS (diff trên
  `app/` ở bước này là rỗng); **không** đụng reconciliation business logic;
  **không** sửa bất kỳ test TASK-108A-1 nào khác. Sau migration:
  **24/24** test reconciliation của TASK-108A-1 PASS, và L1/L2 vẫn IDENTICAL
  nên hành vi trên config **hợp lệ** byte-identical như L3 yêu cầu.
- CHECK-110-16 tiếp tục **BLOCKED**.

Can Revisit After:
Khi TASK-201 thêm persistence cho Review Queue: `RowProvenance` và
`Diagnostics` là thứ được ghi xuống, nên biểu diễn lưu trữ cần xem lại — bất
biến thì không đổi.

## DEC-134

Date:
2026-08-23

Task:
TASK-110 — Architecture Closure, sau Independent Review #7

Decision:

Hai quyết định của chủ dự án (HD-110-16, HD-110-17), cộng một chấp thuận về
biểu diễn, chốt sau Architecture Closure Audit.

**1 — HD-110-16: nới MUST NOT CHANGE cho đúng một file.**

`tests/test_reconcile_raw_criteria.py` được phép sửa để: chuyển 15 lời gọi
`evaluate_raw_mapping(...)` 8-tham-số-vị-trí sang **một** `MappingStats`
canonical, và migrate đúng 2 test F1 sang `pytest.raises(InvalidEmployeeConfig)`.
Ý định từng test giữ nguyên, không test nào bị xoá: 13 test trước → 13 test sau.

Không được tạo shim 8-tham-số, không giữ hai implementation song song, không
tạo bypass production, không dùng `validate=False`.

**2 — HD-110-17: F1 được SUPERSEDED, không phải bị bỏ.**

Ngữ nghĩa canonical mới:

    master nhân viên không hợp lệ
    → fail-fast tại `load_employee_master()` / `EmployeeMaster`
    → TRƯỚC khi xử lý bất kỳ giao dịch nào
    → Review Queue không bao giờ nhận được trạng thái đó

F1 ("group phải khai trong `employee_groups`") vì thế trở thành bất khả đạt và
được gỡ khỏi bộ tiêu chí. DEC-129 §1 và DEC-133 **không** bị sửa; quyết định
này ghi lại việc thay thế và liên kết lịch sử.

**3 — Biểu diễn `snapshot_id`.**

`snapshot_id` chuyển từ *field caller đặt được* sang *property dẫn xuất từ nội
dung master*. Chấp thuận với điều kiện — và đã chứng minh — rằng: mọi trường
nghiệp vụ IDENTICAL (`normalized`, `status`, `group`, `include_in_kpi`,
`default_lead_source`, `record.index`, `record.label`) trên toàn bộ 972 tổ hợp;
id dẫn từ nội dung; caller không truyền được; cùng logical master → cùng id;
khác logical master → khác id; id không tham gia bất kỳ phép tính nghiệp vụ nào.

**4 — Năm root cause được đóng bằng cấu trúc.**

- **RC-1 — biên canonical là KIỂU, không phải HÀM.** `EmployeeMaster`,
  `EmployeeRecord`, `AffectedRow`, `RowProvenance` đều **sealed**: chỉ factory
  đã parse dựng được. Giữ được object chính là bằng chứng nó hợp lệ.
- **RC-2 — không còn văn bản tự do tại canonical boundary.**
  `ReviewItem.message` không còn là tham số; nó là property do
  `app/modules/validation/renderer.py` sinh ra từ đúng `(Diagnostics,
  RowProvenance)` của chính item. Renderer không có đầu vào nào khác nên không
  thể nêu một dòng ngoài provenance. Không blacklist, không regex.
- **RC-3 — hai sự thật không còn là hai tham số.** `evaluate_raw_mapping(stats)`
  nhận đúng một `MappingStats` sở hữu đồng thời bộ đếm, chỉ mục dòng và mapper.
  Mọi con số "bao nhiêu dòng" trong message đọc từ `provenance`.
- **RC-4 — parse, đừng validate.** `EmployeeRecord` + `DateWindow` là trạng
  thái đã parse; ngày méo mó, sai kiểu, cửa sổ bất khả, group ma, prefix trùng
  khít chồng cửa sổ đều là **parse thất bại tại biên master**.
- **RC-5 — oracle kiểm STRUCTURE.** L1 phủ `MappingResult` bằng
  `dataclasses.fields()`; L2 phủ RawRow + WorkingLine + Order và giữ
  `order_graph` (Order → source_row theo thứ tự); không regex-over-message.

Reason:

Architecture Closure Audit chứng minh một câu: **mọi invariant của TASK-110
được cưỡng chế tại một CHỖ (một hàm, một check, một test) thay vì được MANG bởi
một KIỂU. Một chỗ thì đi vòng được; một kiểu thì không.** Đó là lý do sáu vòng
review không hội tụ — mỗi vòng thêm một chỗ, vòng sau tìm con đường không đi
qua chỗ đó.

Bằng chứng đo tại `2d1da98`, tất cả nay đã đóng: `EmployeeMaster(...)` công
khai nhận prefix rỗng + group ma + `active="no"` + dict thô sửa được từ ngoài;
`ReviewItem(message="…dòng 7777")` dựng được trên item sở hữu dòng 6; một lớp
con của `str` làm `details` trả giá trị khác nhau giữa hai lần đọc;
`AffectedRow("KHONG_TON_TAI.xlsx", 99999)` dựng được; `evaluate_raw_mapping`
nhận Counter nói "50 dòng" cùng provenance nói 0; oracle bỏ sót
`MappingResult.record` và mù hoàn toàn với việc dời một line giữa hai Order.

**Ghi chú thực thi về HD-110-15.** Luật "cấm `raw_prefix` trùng khít" được áp
**chỉ khi hai cửa sổ hiệu lực chồng nhau**. Đó đúng là tình huống gây hại mà
HD-110-15 mô tả (một người mất sạch doanh số trong im lặng). Cùng prefix với
cửa sổ **rời nhau** là cách DEC-121 diễn đạt một lượt **bàn giao** — cấm nó sẽ
phá một quy tắc nghiệp vụ canonical, và không dòng nào bị mất vì bộ lọc hiệu
lực phân biệt được hai bản ghi theo ngày của chính dòng đó.

Impact:

- Không đổi: employee mapping trên config hợp lệ, conversion scheme/rate, KPI
  ownership, pricing, profit, order ownership, lead source, TASK-108B,
  TASK-109, output `reconcile_conversion.py` trên config hợp lệ.
- L1 semantic IDENTICAL (972 tổ hợp), L1 v1 IDENTICAL, L2 scalar IDENTICAL,
  L2 graph IDENTICAL — so với baseline `e221924` chụp tại `2d1da98`.
- 20/20 case falsification của Audit = CLOSED.
- DEC-128 → DEC-133 **không** bị sửa.
- CHECK-110-16 tiếp tục **BLOCKED**.

Can Revisit After:
Khi TASK-201 thêm persistence: `RowProvenance` và `Diagnostics` là thứ được ghi
xuống, nên biểu diễn lưu trữ cần xem lại — bất biến thì không đổi.

---

## DEC-135

Date:
2026-08-25

Task:
TASK-110 — R1-A1 Finite Contract Freeze, sau Independent Review R1-A1 #3

Decision:

Chủ dự án duyệt HD-A1-01 → HD-A1-18 đúng như đề xuất trong
`docs/tasks/TASK-110-R1-A1-FROZEN-CONTRACT.md`. R1-A1 thôi lượng hoá trên
không gian typing/runtime mở của Python và chuyển sang một **hợp đồng đóng,
hữu hạn**.

**1 — Ngữ pháp đóng, bốn dạng.**

    spec := any | none | class | optional

Mọi annotation khác là UNSUPPORTED, nổ `CanonicalContractViolation` lúc
decorate. Mặc định là TỪ CHỐI. Độ rộng do production quyết định: audit 11
canonical type / 72 field cho ra đúng 17 hình thái, quy về ba dạng — `class`
37, `optional` 34, `any` 1. Production KHÔNG dùng generic có tham số, KHÔNG
dùng `Literal`, KHÔNG dùng union nhiều nhánh.

**2 — HD-A1-16: mọi generic có tham số là UNSUPPORTED.**

Quyết định có ảnh hưởng lớn nhất. Không giữ tương thích ngược với phần hỗ trợ
generic mà repair #1/#2/#3 đã xây. Hệ quả: ranh giới tranh cãi R1-A1/R1-D
("parse đủ nhưng không kiểm phần tử") biến mất khỏi R1-A1; trục ĐỘ SÂU không
còn nên `_MAX_ANNOTATION_DEPTH` được gỡ.

**3 — HD-A1-09: xoá `isinstance` khỏi toàn bộ đường validate canonical.**

Phép kiểm class runtime là `type(value) is T`. Bằng chứng đủ điều kiện:
instrument trên toàn bộ 702 test tại `1b0da151` cho **0 divergence** giữa
`isinstance` và phép so định danh — dung sai lớp con mà `isinstance` mua thêm,
production không dùng, còn cái nó bán đi là hai lỗ hổng đo được (`__class__`
nổ làm lỗi thô thoát ra; `__class__` nói dối đưa object giả qua được).

**4 — HD-A1-10: một primitive bổ sung được duyệt.**

`issubclass(type(value), MUTABLE_TUPLE)` cho mutable guard. Nó điều phối theo
metaclass của vế PHẢI (hằng của framework), rơi vào `PyType_IsSubtype` đọc
trường C `tp_mro`, nên không chạy code người dùng — và nó bắt được LỚP CON của
container mutable, thứ phép so định danh bỏ sót.

**5 — HD-A1-13: cổng `type(cls) is type` đứng trước mọi mutation lên class.**

Đóng nhóm V bằng cấu trúc thay vì bằng rollback (bản thân rollback cũng gọi
`setattr`).

**6 — Corpus 105 case là ACCEPTANCE CORPUS, không được bổ sung trong vòng
repair này.**

Attack mới ngoài hợp đồng → HARDENING BACKLOG. Luật "reviewer nghĩ ra attack
mới ⇒ FAIL" hết hiệu lực; Independent Review chỉ BLOCKING theo năm điều kiện ở
§14 hợp đồng.

Rationale:

Ba vòng repair trước đều FAIL vì tiêu chí chấp nhận được phát biểu trên một
không gian không đếm được. Reviewer luôn tạo thêm được một metaclass, một
`__instancecheck__`, một `__hash__` mới. Vòng lặp chỉ kết thúc khi tiêu chí
trở nên hữu hạn — và nó hữu hạn được vì production chỉ cần một tập rất nhỏ.

Consequences:

- DEC-128 → DEC-134 **không** bị sửa.
- R1-A1 = AWAITING_INDEPENDENT_REVIEW. **Chưa** FROZEN, **chưa** chuyển R1-A2,
  **chưa** merge TASK-110. CHECK-110-16 vẫn BLOCKED (workbook production chưa
  tồn tại — không giả lập PASS).
- Ba case `K03`/`L03`/`M02` chờ quyết định của chủ dự án: chúng nhắm vào thuộc
  tính mà CPython `dataclasses._process_class` tự đọc trước khi `@canonical`
  chạy, nên framework không tạo ra được outcome đã freeze. Đề xuất phân loại
  lại thành `OUTSIDE_FRAMEWORK_BOUNDARY`; không tự đổi.

---

## DEC-136

Date:
2026-08-27

Task:
TASK-110 — R1-A1 Finite Contract, finalization sau implementation

Decision:

**1 — PRECEDENCE RULE (luật chung, không chỉ cho TASK-110).**

Trong một artifact có đồng thời **bảng định danh** (bảng case, bảng
requirement, ma trận ID) và **văn xuôi diễn giải**, thì:

    BẢNG ĐỊNH DANH LÀ NGUỒN QUY PHẠM.

Nếu số liệu hoặc diễn giải trong văn xuôi mâu thuẫn với bảng:

    TABLE / IDENTIFIER MATRIX WINS.

Văn xuôi phải được sửa cho đồng bộ với bảng. **Không** được sửa bảng theo văn
xuôi nếu chưa có Owner Decision. Luật này ra đời để không lặp lại lỗi "95 vs
105" của PLAN R1-A1.

**2 — HD-POST-A1-01: FROZEN CORPUS = 105 CASE.**

Con số "95" trong văn xuôi PLAN là lỗi đếm còn sót. Bảng ID §12 là quy phạm.
Phân loại việc sửa: **DOCUMENTATION COUNT CORRECTION**, KHÔNG phải CONTRACT
EXPANSION. Không thêm/xoá/renumber case, không đổi expected outcome để làm
suite xanh.

**3 — HD-POST-A1-02: K03 / L03 / M02 = OUTSIDE_FRAMEWORK_BOUNDARY.**

Biên R1-A1 bắt đầu tại thời điểm code của `@canonical` bắt đầu execution. Nếu
`dataclasses` / `typing` / interpreter / quá trình dựng annotation phát
exception TRƯỚC thời điểm đó, canonical chưa có quyền kiểm soát exception ấy,
và R1-A1 không có trách nhiệm normalize nó.

Phân loại chỉ hợp lệ khi chứng minh đủ bốn mệnh đề: (A) canonical chưa bắt đầu
xử lý class; (B) registry không đổi; (C) class không nhận canonical partial
state; (D) canonical vắng mặt trong traceback và frame chịu trách nhiệm nằm
trong stdlib. Nếu canonical ĐÃ chạy rồi mới leak raw foreign exception thì đó
là **BLOCKING R1-A1 DEFECT** — `OUTSIDE_FRAMEWORK_BOUNDARY` không được dùng để
che lỗi bên trong canonical.

`canonical.py` **không** được sửa để cố bắt các exception này, và biên **không**
được mở ngược vào `dataclasses` / `typing` / interpreter internals.

Phân loại này **ghim theo interpreter**: CPython `3.11.15`. Số dòng
`dataclasses.py` chỉ là evidence của interpreter hiện tại, **không** phải
invariant. Đổi Python minor version ⇒ **RE-VERIFY**, không auto-carry.

**4 — HD-POST-A1-03: K01 / M01 / M02 CASE CONSTRUCTION CORRECTION.**

Ba correction được ratify. Phân loại: **CASE CONSTRUCTION CORRECTION**, KHÔNG
phải EXPECTED OUTCOME CHANGE — mỗi correction làm case chạm đúng boundary mà nó
tuyên bố kiểm tra, thay vì PASS/FAIL vì một cơ chế khác. Bản ghi 8 trường cho
từng case ở §21.2d của
`docs/tasks/TASK-110-R1-A1-FROZEN-CONTRACT.md`.

Từ Review Candidate SHA của phiên này trở đi: **K01 / M01 / M02 CONSTRUCTION =
FROZEN**. Mọi thay đổi construction tiếp theo cần HUMAN ESCALATION.

**5 — CORPUS RESULT SEMANTICS.**

Báo cáo bắt buộc dùng dạng phân rã, không dùng "102/105 PASS" (đọc như 3 case
hỏng) và không dùng "105/105 PASS" (đọc như 3 case ngoài biên cũng là in-scope):

    FROZEN CORPUS               105/105 CLASSIFIED
    IN-SCOPE                    102/102 PASS
    OUTSIDE_FRAMEWORK_BOUNDARY    3/3   correctly classified (K03, L03, M02)
    UNCLASSIFIED                    0
    BLOCKING FAIL                   0

    105 = 102 + 3

**6 — CHECK-110-16 = MERGE GATE, KHÔNG phải REVIEW GATE.**

Khi production workbook không tồn tại, CHECK-110-16 = BLOCKED. Không giả lập
workbook, không synthetic PASS. R1-A1 vẫn đạt được
`READY_FOR_INDEPENDENT_REVIEW` trong khi CHECK-110-16 còn BLOCKED;
CHECK-110-16 chỉ phải giải quyết trước merge/final completion.

**7 — Reference-integrity failure có sẵn được chấp nhận cho review readiness.**

Ba dead reference trong `TASK-REM-T06` là PRE-EXISTING, ngoài touch-area, giữ
tại HB-A1-05. **Cấm sửa** chúng trong task này — sửa là SCOPE VIOLATION. Chúng
KHÔNG chặn `READY_FOR_INDEPENDENT_REVIEW`. Nếu xuất hiện reference-integrity
failure MỚI: STOP.

Rationale:

Bốn quyết định đầu đóng nốt ba escalation mà implementation R1-A1 nêu ra, mà
không mở lại một dòng nào của `canonical.py`. Quyết định 1 là luật chung: hai
lần trong cùng một task, văn xuôi và bảng đã lệch nhau, và cả hai lần bảng mới
là thứ đúng.

Consequences:

- DEC-128 → DEC-135 **không** bị sửa.
- `app/modules/domain/canonical.py` **KHÔNG ĐỔI** trong phiên finalization.
- R1-A1 = **READY_FOR_INDEPENDENT_REVIEW**. Vẫn **chưa** FROZEN, **chưa** chuyển
  R1-A2, **chưa** merge TASK-110.
- R1-A, R1 = NOT FROZEN. R2→R8 = BLOCKED. CHECK-110-16 = BLOCKED (merge gate).
- Backlog thêm HB-A1-06 (B2/B3 defensive boundary, untested) và HB-A1-07
  (`MUTABLES` phụ thuộc invariant metaclass builtin `type`).

---

## DEC-137

Date:
2026-08-27

Task:
TASK-110 — R1-A1 Pre-Review Evidence Reconciliation

Decision:

**1 — BRANCH AUTHORITY.**

    R1-A1 authoritative branch:
        claude/r1-a1-contract-freeze-9lkh3h

    authoritative review candidate:
        SHA finalization của phiên reconciliation này
        (kế thừa aff02405f51ad47e67e8759d2fa097f1277d62d4)

    claude/r1-canonical-object-safety-fon9lb:
        historical ancestor cho unit này;
        NOT review authority;
        NOT merge authority;
        KHÔNG fast-forward trong task này.

Nhánh `fon9lb` đứng tại `1b0da151` và là tổ tiên trực tiếp (behind 0 / ahead N)
của nhánh authoritative, nên không có track song song nào để đối chiếu.

**2 — REVIEW CLEANLINESS.**

`CLEAN` nghĩa là: **không tracked file nào bị modified / staged / deleted bởi
reviewer.**

Những thứ sau **KHÔNG** phải repository modification:

- untracked cache của test runner: `__pycache__/`, `.pytest_cache/`, `.coverage`;
- detached checkout tới một exact SHA.

Reviewer không bị coi là làm bẩn repo chỉ vì chạy test.

**3 — VERDICT SEMANTICS.**

Independent Reviewer chỉ được trả đúng một trong hai:

    PASS — ELIGIBLE_FOR_FREEZE
    FAIL — NOT_ELIGIBLE_FOR_FREEZE

Reviewer **KHÔNG** ghi `FROZEN` vào repository. Nếu verdict là PASS, một
**Freeze Finalization session riêng** mới được phép ghi `R1-A1 = FROZEN` cùng
reviewed SHA vào governance.

**4 — INTERPRETER TRIPWIRE SEMANTICS.**

Test ghim interpreter FAIL vì reviewer dùng minor version khác **không** tự
động là R1-A1 correctness FAIL; nó nghĩa là `ENVIRONMENT_REVERIFY_REQUIRED`.

- Boundary invariant fail (một trong bốn mệnh đề A/B/C/D của `K03`/`L03`/`M02`
  sai) → **BLOCKING**.
- Chỉ version mismatch, bốn mệnh đề vẫn đúng → **NON-BLOCKING environment
  difference**: cập nhật `VERIFIED_*`, ghi evidence, không phải correctness FAIL.

Tripwire buộc re-verify, không tự động fail, và không làm yếu boundary oracle —
bốn assertion A/B/C/D chạy độc lập với version check.

**5 — DEFECT ĐƯỢC PHÁT HIỆN VÀ SỬA TRONG PHIÊN NÀY.**

Three-way reconciliation (PLAN `5a0f27c` ↔ Frozen Contract `aff0240` ↔ pytest
collection) phát hiện: **HD-POST-A1-02 đã được áp vào code và vào văn xuôi
§21.2, nhưng CHƯA được áp vào chính bảng §12** — bảng quy phạm còn ghi
`UNSUPPORTED_AT_DECORATION` cho `K03`/`L03`/`M02`.

Theo precedence rule của DEC-136 thì bảng là quy phạm, nên tại `aff0240` bảng
và implementation tự mâu thuẫn. Sửa bảng cho khớp HD-POST-A1-02 là **thi hành
Owner Decision lên artifact quy phạm**, không phải một thay đổi hợp đồng đơn
phương. `T03` được chuẩn hoá cách viết sang cùng token
(`OUTSIDE_FRAMEWORK_BOUNDARY`) — ngữ nghĩa không đổi.

Để lỗi này không tái diễn, phép đối chiếu bảng ↔ code trở thành **cơ chế**:
`test_the_normative_table_and_the_code_corpus_agree_case_by_case` đọc trực tiếp
bảng §12 và so từng ô với `FROZEN_CORPUS`. Lệch một ô là suite ĐỎ.

Rationale:

Đây là lần thứ ba trong cùng một task mà một artifact tự lệch với chính nó
(95 vs 105; bảng vs code; và một lỗi parser markdown trong chính script đối
chiếu). Cả ba lần đều là lỗi đồng bộ, không phải lỗi thiết kế — nên lời giải
đúng là biến phép đối chiếu thành test, không phải thêm một vòng review nữa.

Consequences:

- DEC-128 → DEC-136 **không** bị sửa.
- `app/modules/domain/canonical.py` **KHÔNG ĐỔI** (SHA256
  `08e74fe226caca98ce46f845475cc386496bf0e3a57eab197f97d09c723d3e3c`).
- Corpus vẫn **105 case**; expected-outcome change duy nhất so với PLAN là ba
  ô do HD-POST-A1-02 cho phép.
- R1-A1 = READY_FOR_INDEPENDENT_REVIEW. Chưa FROZEN, chưa chuyển R1-A2, chưa
  merge. CHECK-110-16 vẫn BLOCKED (merge gate).

---

## DEC-138

Date:
2026-08-27

Task:
TASK-110 — R1-A1, HD-POST-A1-04 (conditional ratification cho T03)

Decision:

**HD-POST-A1-04 = RATIFIED.** `T03` được phân loại
`OUTSIDE_FRAMEWORK_BOUNDARY`, sau khi cả bốn premise có điều kiện đều được
chứng minh:

**A — PLAN đã phát biểu semantics pre-canonical từ trước.** PLAN @ `5a0f27c`,
§10 dòng 402–406 (nguyên văn): "`typing` **tự nó** không dựng nổi object trước
khi framework nhìn thấy … Đó là biên NGOÀI framework: không canonical type nào
được tạo ra, không có trạng thái nửa vời". Ô expected outcome tại bảng §12
dòng 560: "ngoài biên framework — không canonical type nào được tạo".
Ratification dựa trên semantics đã có, không phải câu chuyện dựng sau.

**B — oracle chứng minh đủ A/B/C/D, cùng chuẩn với `K03`/`L03`/`M02`.**
Mệnh đề C được thoả ở dạng **mạnh hơn** chứ không yếu hơn: class mục tiêu chưa
từng được tạo ra. Foreign component: `typing.py:1395 in __hash__`.

**C — không cần sửa `canonical.py`.** TEST-ONLY + DOCS-ONLY.

**D — semantic intent không đổi**; thay đổi là đặt tên token cộng nâng oracle.

**Phân hoạch ngữ nghĩa DUY NHẤT từ đây:**

    105 FROZEN CORPUS IDs
      = 101 IN-FRAMEWORK FROZEN IDs   (BAO GỒM Z01–Z04)
      +   4 OUTSIDE_FRAMEWORK_BOUNDARY IDs (K03, L03, M02, T03)

`102 + 3` **không còn là acceptance equation**.

**Điều phải nói thẳng — asymmetry của T03.** Tại `c183123`, `T03` PASS trong
khi `K03`/`L03`/`M02` XFAIL. Lý do KHÔNG phải oracle T03 mạnh hơn: trong code
`T03.expected` đã là `OUTSIDE_FRAMEWORK_BOUNDARY` ngay từ đầu, còn ba case kia
mang một outcome framework không tạo ra được. Oracle của `T03` khi đó chỉ kiểm
`RecursionError` + registry — nó **PASS đúng kết quả nhưng chưa chứng minh cơ
chế**, và **yếu hơn** oracle mà ba case kia nhận ở HD-POST-A1-02. Vì vậy việc
làm hôm nay **không** chỉ là "chuẩn hoá nhãn": phần nhãn là chuẩn hoá, phần
oracle là một sự siết chặt thật sự.

**Tripwire interpreter** nay phủ **cả bốn** case. Reviewer chạy minor version
khác ⇒ `ENVIRONMENT_REVERIFY_REQUIRED` cho cả bốn, không phải correctness FAIL.

**Parser bảng quy phạm** là một mắt xích evidence, nên có oracle riêng: 9 bất
biến, và dòng méo phải FAIL chứ không bị nuốt.

**SUPERSEDED REVIEW CANDIDATES** (branch authority DEC-137 giữ nguyên):

- `aff02405f51ad47e67e8759d2fa097f1277d62d4` — superseded, lý do:
  normative-table divergence.
- `6f79cbb8a4b9f7355e8b595518326f4eda75ca95` — superseded, lý do:
  T03 authority / oracle / accounting reconciliation pending.

Rationale:

Owner Decision này có điều kiện, và điều kiện có ý nghĩa: nếu PLAN không thật
sự phát biểu semantics pre-canonical cho `T03` thì lời giải đúng là revert
nhãn, không phải hợp thức hoá sau. PLAN có phát biểu, nên ratify — nhưng đúng
lúc kiểm chứng thì lộ ra rằng oracle của `T03` xưa nay yếu hơn ba case kia.
Ghi cả hai điều đó mới là bản ghi trung thực.

Consequences:

- DEC-128 → DEC-137 **không** bị sửa.
- `app/modules/domain/canonical.py` **KHÔNG ĐỔI** — SHA256
  `08e74fe226caca98ce46f845475cc386496bf0e3a57eab197f97d09c723d3e3c`.
- Corpus vẫn **105 ID**; outcome delta so với PLAN đúng **bốn** ô, không có ô
  thứ năm.
- R1-A1 = READY_FOR_INDEPENDENT_REVIEW. Chưa FROZEN, chưa chuyển R1-A2, chưa
  merge. CHECK-110-16 vẫn BLOCKED (merge gate).

## DEC-139

Date:
2026-08-27

Task:
TASK-110 — R1-A1 FREEZE FINALIZATION (session `claude/r1-a1-contract-freeze-9lkh3h`).

Decision:

Tiếp nhận verdict Independent Review đã chốt cho exact reviewed SHA
`a85397106b81799d149d98e71a7fcfd5bc8963ad`:

```
PASS — ELIGIBLE_FOR_FREEZE
BLOCKING findings: 0
HARDENING findings: 1
OUT_OF_SCOPE findings mới: 0
```

Ghi:

```
R1-A1 = FROZEN
```

Đây là finalization state, không phải một review mới — không finding kỹ
thuật nào được sửa trong phiên này (repair budget của lineage `TASK-110` đã
`EXHAUSTED_PRE_V4.1`, `remaining = 0`, xem PROJECT/REVIEW_BUDGET_LEDGER.md — Governance V4.1 overlay, chưa merge vào nhánh này tại thời điểm ghi).

**Interpreter difference:** Independent Review chạy CPython 3.12.13, khác
pinned evidence CPython 3.11.15 trước đó. Tripwire
`ENVIRONMENT_REVERIFY_REQUIRED` kích hoạt cho K03/L03/M02/T03; reviewer đã
re-verify A/B/C/D cho cả bốn — PASS cả bốn. Phân loại:
**NON-BLOCKING ENVIRONMENT DIFFERENCE**. Không sửa test/pinning/canonical.py.

**Corpus:** `105 = 101 IN-FRAMEWORK + 4 OUTSIDE_FRAMEWORK_BOUNDARY`
(K03/L03/M02 → HD-POST-A1-02; T03 → HD-POST-A1-04/DEC-138). Không đổi ID,
expected outcome, construction, numbering, grouping, oracle, corpus size.

**Finding 1 — HARDENING, backlog only (HB-A1-05):**
`docs/reviews/PRE-REVIEW-EVIDENCE-R1A1-collection.md` ghi `Parent SHA:
6f79cbb...` thay vì `Reviewed SHA: a853971...`. Severity LOW, production
path NONE, không blocking. Không sửa raw evidence trong phiên này.
Re-trigger: khi tạo raw collection evidence cho review candidate tiếp
theo — artifact mới nên phân biệt rõ `Parent SHA` / `Reviewed SHA`.

**CHECK-110-16:** giữ nguyên `BLOCKED` — merge gate (không phải review
gate), thiếu production workbook thật. Không synthetic PASS, không bypass.

**Trạng thái không suy diễn tăng theo:**

```
R1-A1 = FROZEN
R1-A  = NOT FROZEN
R1    = NOT FROZEN
TASK-110 = NOT DONE
```

**R1-A2 → R8:** `OWNER_EXTENSION REQUIRED` cho từng unit (theo
PROJECT/REVIEW_BUDGET_LEDGER.md — Governance V4.1 overlay, chưa merge vào
nhánh này tại thời điểm ghi). Không có Owner Extension ⇒ STOP.

Rationale:

Freeze record phải tách bạch rõ hai điều: (1) verdict kỹ thuật của
Independent Review, đã chốt bởi Owner, không phải điều phiên này tái tạo
hay tái diễn giải; và (2) phạm vi finalization thuần state — không mở lại
repair, không mở R1-A2, không đổi implementation. Giữ Finding 1 ở backlog
thay vì sửa ngay tránh việc "biến finding thành biến mất" — đúng như chỉ
thị: sửa artifact evidence để một finding không còn hiển thị là hành vi bị
cấm minh thị.

Impact:
- File sửa: `docs/tasks/TASK-110_REPAIR_PROGRESS.md` (append section
  Freeze Finalization), file này (`PROJECT/PROJECT_DECISIONS.md`, DEC-139).
- Không sửa: `app/modules/domain/canonical.py`, bất kỳ file dưới `tests/`,
  `tools/analysis/`, `docs/reviews/PRE-REVIEW-EVIDENCE-R1A1-collection.md`,
  hay nội dung kỹ thuật của `docs/tasks/TASK-110-R1-A1-FROZEN-CONTRACT.md`.
- Commit Freeze Finalization là commit trạng thái SAU review, không thay
  đổi reviewed implementation — SHA review (`a853971...`) và SHA finalize
  (ghi trong commit log) là hai giá trị khác nhau và phải được phân biệt.

Can Revisit After:
`OWNER_EXTENSION` cho R1-A2 (hoặc bất kỳ unit R1-B…R8 nào), hoặc quyết định
mới về `CHECK-110-16` (merge gate timeout, xem §9 của
PROJECT/REVIEW_BUDGET_LEDGER.md — Governance V4.1 overlay, chưa merge vào
nhánh này tại thời điểm ghi).

## DEC-140

Date:
2026-08-27

Task:
TASK-V4-ADOPTION — Freeze & Execute Governance V4.1 (session V4.1-0).

Decision:

Owner phê duyệt và freeze **Governance V4.1** như một policy overlay
(`governance/core/V4_1_POLICY_FREEZE.md`), áp dụng trên nền governance hiện
có, không thay thế nó. Các điểm sau được freeze tại session này:

1. **TASK-110 budget = `EXHAUSTED_PRE_V4.1`.** Lineage `TASK-110` (bao gồm
   toàn bộ sub-unit R1-A2 → R8 nếu thuộc lineage này) có
   `repair_cycles_remaining = 0` kể từ trước khi V4.1 có hiệu lực. Đây là
   trạng thái chuyển tiếp có chủ ý (transition state), ghi tại
   `PROJECT/REVIEW_BUDGET_LEDGER.md`, không phải một placeholder chờ điền.
2. **R1-A2 → R8 không tự có ngân sách.** Mỗi unit muốn tiếp tục cần một
   `OWNER_EXTENSION` riêng (production path cụ thể + kịch bản nghiệp vụ sai
   + phạm vi + budget được cấp). Không có Owner Extension → `STOP`.
3. **Bảng ngân sách review chuẩn hoá:** `LOW = 1`, `MEDIUM = 1`,
   `HIGH/CRITICAL = 2` blocking repair cycle. Không tồn tại `HIGH = 3`.
4. **Repair cycle tính theo cumulative repair diff** (`base_sha`/`head_sha`
   tiến lên, không reset qua session/branch/sub-unit mới).
5. **Blast Radius chấm theo failure path**, không chấm theo tên
   module/file; `Effective Risk = max(Local Risk, Blast Radius)`.
6. **Golden Baseline chỉ hạ Blast Radius tối đa một bậc** khi có một Golden
   test cụ thể phủ đúng failure path (tên test/fixture/path/expected
   output). Trước `TASK-GOLDEN-BASELINE-001`: không Golden test nào được
   dùng để hạ risk.
7. **Production-realistic input** phải dựng được từ một trong bốn nguồn hữu
   hạn (production annotation/schema inventory hiện tại; config hiện hành;
   Golden fixture đã tồn tại; raw production data đã xác minh). Không dựng
   được → HARDENING BY DEFAULT.
8. **Branch divergence threshold:** `INTEGRATION_DECISION_REQUIRED` khi
   ahead > 10 commit, HOẶC divergence > 3 ngày, HOẶC cumulative LOC >
   5.000. `TASK-110` hiện có nhiều nhánh review vượt các ngưỡng này — ghi
   nhận là **KNOWN PRE-V4.1 DIVERGENCE**, phải xử lý tại V4.1-1, không
   grandfather thành ngoại lệ vĩnh viễn.
9. **Merge gate timeout = 30 ngày.** `CHECK-110-16` tiếp tục `BLOCKED` (merge
   gate — thiếu production workbook thật để đối chiếu). Không giả lập PASS,
   không bypass. Nếu vượt 30 ngày kể từ ngày phát sinh mà chưa có quyết
   định: `OWNER DECISION REQUIRED`.
10. **`ACCEPT_AS_IS` / `DESCOPE` chỉ Owner được ghi** (State Authority
    Matrix, §12 của overlay).
11. **`V4.1 = POLICY_ADOPTED` KHÔNG đồng nghĩa `V4.1 = FULLY_ENFORCED`.**
    `FULLY_ENFORCED` chỉ đạt sau `TASK-GOLDEN-BASELINE-001` (Golden
    fixture + deterministic expected output + one-command diff +
    test suite tests/test_golden_baseline.py, chưa tồn tại, PASS).

Rationale:

Repo có nhiều nhánh review TASK-110 chạy song song (≥8 Independent Review,
≥3 repair) từ trước khi V4.1 tồn tại; nếu V4.1 tự động cấp lại ngân sách
cho lineage này, mọi giới hạn repair-cycle mà V4.1 định ra sẽ vô nghĩa ngay
tại lần áp dụng đầu tiên. Đóng băng TASK-110 ở trạng thái exhausted-nhưng-
không-treo (vẫn có `FINAL_REVIEW_ONLY`/`ACCEPT_AS_IS`/`DESCOPE`/
`OWNER_EXTENSION` làm lối ra) giữ nguyên tắc "V4.1 phải chịu chính V4.1"
đồng thời không chặn đường hoàn tất R1-A1 hiện đang review.

Risk:

Nếu không freeze rõ transition state này, có nguy cơ lặp lại đúng pattern
đã gây ra DEC-118 (hai track không biết về nhau, làm trùng việc) — lần này
là nhiều nhánh TASK-110 độc lập tiếp tục mở repair cycle mới không giới
hạn dưới các tên gọi khác nhau (V4.1-R1, R1-A1A, …).

Impact:
- File mới: `governance/core/V4_1_POLICY_FREEZE.md`,
  `PROJECT/REVIEW_BUDGET_LEDGER.md`, `scripts/branch_authority_check.sh`.
- File sửa: `CLAUDE.md` (thêm pointer tới overlay), file này
  (`PROJECT/PROJECT_DECISIONS.md`), `PROJECT/PROJECT_PROGRESS.md` (ghi
  trạng thái adoption tối thiểu).
- Không sửa production code (`app/`, `tests/`, `config/`, `tools/`).
- Không sửa nội dung kỹ thuật của bất kỳ review TASK-110 nào đang mở trên
  các nhánh khác (`claude/r1-a1-contract-freeze-9lkh3h`,
  `claude/r1-canonical-object-safety-fon9lb`,
  `claude/task-110-gate-readiness-7ui4si`,
  `claude/zealous-bardeen-s8iu2h`) — các nhánh đó nằm ngoài phạm vi
  `TASK-V4-ADOPTION`.

Can Revisit After:
`V4.1-1` (Final R1-A1 Independent Review + Freeze Finalization + Integration
Decision) — không revisit trong chính session V4.1-0.

## DEC-141

Date:
2026-08-27

Task:
V4.1-1 — TASK-110 + Governance V4.1 Integration (phiên integration).

Decision:

Owner phê duyệt bốn quyết định của Integration Plan (OD-1 → OD-4). Ghi lại ở
đây phần có hiệu lực quy phạm lâu dài.

**1 — `CHECK-110-16` đổi Gate Class (OD-1).**

```
CHECK-110-16 — Đối chiếu trên dữ liệu thật
Priority   : REQUIRED                            (KHÔNG đổi)
Status     : BLOCKED                             (KHÔNG đổi)
Gate Class : POST_MERGE_PRODUCTION_ACCEPTANCE    (MỚI — trước đây là pre-merge gate)
```

Chỉ đổi **Gate Class**. Không đổi Priority, không đổi Status, không đổi nội
dung check, không đổi mốc tham chiếu.

Điều kiện Owner đặt ra, bắt buộc giữ:
- Không synthetic PASS.
- Không tạo workbook giả.
- Không bypass kiểm tra production.
- **Merge KHÔNG đồng nghĩa `TASK-110 DONE`.**
- `TASK-110` chỉ `DONE` khi `CHECK-110-16` thực sự `PASS` trên dữ liệu
  production thật, đối chiếu với `docs/analysis/_evidence/evidence.json`
  theo đúng quy tắc HD-110-02 (cấm chỉnh danh sách từ khóa để ép con số về
  1.261).

Rationale:

Dependency của `CHECK-110-16` — file thô production 6 tháng / 11.765 dòng —
nằm hoàn toàn ngoài repo (đúng `governance/product/17_DATA_GOVERNANCE_PRIVACY.md`)
và không có timeline. Bản chất của check là đo *hành vi của code trên dữ liệu
thật*, không đo *trạng thái nhánh*; không có gì trong nội dung check mất hiệu
lực sau merge. Giữ nó làm pre-merge gate biến một dependency mà không agent
nào giải quyết được thành vật cản cho một integration đã được chứng minh an
toàn, đồng thời chặn `TASK-GOLDEN-BASELINE-001` (V4.1 §13 yêu cầu Golden dựng
**trên integration baseline chính thức**) và do đó khoá `V4.1` vĩnh viễn ở
`POLICY_ADOPTED`. Đây là option (B) mà chính `governance/core/V4_1_POLICY_FREEZE.md` §9 liệt
kê cho merge gate timeout.

**2 — Giải `DEC-128` ID collision (OD-2).**

`DEC-128` của `TASK-110` (2026-08-23, Gate/Readiness Review) giữ nguyên;
`DEC-128` của Governance V4.1 (2026-08-27, `TASK-V4-ADOPTION`) đổi thành
`DEC-140`. Semantic content của quyết định V4.1 không đổi — chỉ reconcile
ID và reference. Không rewrite lịch sử `TASK-110`.

**3 — Integration strategy (OD-3).**

`OPTION C` — temporary integration branch `integration/v4-1-task-110`, tạo từ
`c7a1b24e08ff7c03cab06b323110e2a9f05ab363`, hội tụ
`claude/r1-a1-contract-freeze-9lkh3h` (`01a03b0`, 24 commit) và
`claude/governance-v4-1-freeze-36oexq` (`8d79009`, 1 commit), reconcile trạng
thái, validate đầy đủ, rồi merge `--no-ff` về nhánh mặc định.

Các thay đổi tài liệu trạng thái của phiên này được phân loại
**`INTEGRATION STATE RECONCILIATION`**. Chúng KHÔNG phải `TASK-110` repair
cycle, KHÔNG reset review budget, KHÔNG mở `R1-A2`, KHÔNG mở `R2` → `R8`,
KHÔNG đánh giá lại correctness của `R1-A1`, KHÔNG đổi `R1-A1` FROZEN contract.

**4 — `KNOWN PRE-V4.1 DIVERGENCE` (OD-4).**

Integration này là hành động chính thức đóng `KNOWN PRE-V4.1 DIVERGENCE` ghi
tại `PROJECT/REVIEW_BUDGET_LEDGER.md`. Divergence đo được trước integration:
`r1-a1-contract-freeze-9lkh3h` ahead 24 commit / 4 ngày / 40.523 LOC — vượt
cả ba ngưỡng `governance/core/V4_1_POLICY_FREEZE.md` §8. Không grandfather thành ngoại lệ
vĩnh viễn.

Risk:

Nếu `CHECK-110-16` bị đọc nhầm thành đã hoàn tất sau khi đổi Gate Class,
`TASK-110` có thể bị đánh dấu `DONE` mà chưa hề đối chiếu dữ liệu thật. Vì
vậy `Status` giữ nguyên `BLOCKED` và bất biến "merge ≠ DONE" được ghi lặp ở
`PROJECT/PROJECT_PROGRESS.md`, `docs/tasks/TASK-110-validation-review-queue.md`,
`docs/tasks/TASK-110_REPAIR_PROGRESS.md` và `PROJECT/REVIEW_BUDGET_LEDGER.md`.

Impact:
- Không sửa production code (`app/`, `config/`, `tools/`), không sửa test
  (`tests/`), không sửa `app/modules/domain/canonical.py`, không đổi
  `FROZEN_CORPUS`, không đổi expected outcome, không đổi oracle.
- Chỉ sửa tài liệu trạng thái hiện tại (current normative state).
- Không xoá historical artifact; prose lịch sử mâu thuẫn được gắn nhãn
  `SUPERSEDED` hoặc thêm con trỏ tới trạng thái hiện tại, không bị xoá.

Can Revisit After:
`CHECK-110-16` thực sự chạy trên dữ liệu production thật (khi Owner cung cấp
file thô), hoặc một `OWNER_EXTENSION` cho `R1-A2` → `R8`.

## DEC-142

Date:
2026-08-27

Task:
TASK-GOLDEN-BASELINE-001 — Freeze Finalization (phiên "FREEZE FINALIZATION +
CONTROLLED INTEGRATION", thẩm quyền riêng theo
`governance/core/V4_1_POLICY_FREEZE.md` §12).

Decision:

`TASK-GOLDEN-BASELINE-001 = FROZEN`.

```
Technical Reviewed SHA : 85210691702550d83c0fd42fe816be8ca9dde889
Review Verdict Record  : 94b2513d1894dbd58f3b08656e3c7412be191df5
Independent Review #2  : PASS — ELIGIBLE_FOR_FREEZE
GB-IR-01               : CLOSED_BY_REPAIR, INDEPENDENTLY_VERIFIED
BLOCKING                : 0

Review Budget (root task TASK-GOLDEN-BASELINE-001):
    allowed   = 2
    used      = 1
    remaining = 1  (UNUSED — task closure không đồng nghĩa phải dùng hết budget)

HB-GB-01 … HB-GB-06 : HARDENING / BACKLOG — không blocking freeze.
```

Golden Baseline contract, đóng băng kể từ quyết định này:

- Hai fixture `.xlsx` đã ẩn danh tại `tests/fixtures/golden/` (`period_2026_01.xlsx`,
  `period_2026_06.xlsx`) — **frozen**, không sửa ngoài một repair cycle mới có
  thẩm quyền.
- Expected business output tại `tests/fixtures/golden/expected/*.json` —
  **frozen**.
- `tests/test_golden_baseline.py` — strict business comparison (`_strict_bytes()`
  loại đúng ba trường advisory) — **frozen**.
- `_environment.python` / `pyyaml` / `openpyxl` — **advisory only**, không bao
  giờ làm Golden FAIL một mình.
- Không tự động regenerate expected output để ép test xanh.
- Một business mutation (đổi tỉ lệ quy đổi, đổi rule LeadSource, sửa
  `sales_normalized`…) phải làm Golden **FAIL**.
- Một advisory environment mutation (đổi version `python`/`pyyaml`/`openpyxl`
  trong `_environment`) **không** được làm Golden FAIL.
- Golden Baseline là lưới an toàn regression (regression safety net) — **không**
  chứng minh logic mới luôn đúng, chỉ chứng minh nó giống mốc đã xác minh.
- Chỉ những data path (P1/P2/P3/P6/P7/P8/P14 — xem
  `docs/tasks/TASK-GOLDEN-BASELINE-001-PLAN.md` §A.15/§E.3) có tên Golden test
  cụ thể phủ mới được viện dẫn khi đánh giá Blast Radius; các path khác (P4,
  P5, P9–P13, và nhánh unmapped của P7) **không** được hạ risk bằng Golden.
- Effective Risk `P4`/`P5` **không bao giờ** được hạ bằng Golden — Golden so
  output cuối, mù với mutation giữa chừng và với việc lớp enforcement bị vô
  hiệu hoá (V4.1 §4.1, §6).

Rationale:

Independent Review #2 đã ghi verdict `PASS — ELIGIBLE_FOR_FREEZE` tại
`docs/reviews/TASK-GOLDEN-BASELINE-001-INDEPENDENT-REVIEW-2.md`, 0 blocking
finding. Theo State Authority Matrix (`governance/core/V4_1_POLICY_FREEZE.md`
§12), verdict `ELIGIBLE_FOR_FREEZE` thuộc thẩm quyền independent reviewer;
`FROZEN` thuộc một phiên Freeze Finalization có thẩm quyền riêng — đây chính
là phiên đó. Quyết định này **không** review lại technical correctness, chỉ
ghi nhận việc niêm phong dựa trên verdict đã có.

Risk:

Nếu ai đó đọc `FROZEN` thành `DONE` hoặc thành cấp phép mở hardening
(`HB-GB-01…06`)/Review #3/Repair Cycle #2, đó là đọc sai quyết định này. Freeze
chỉ khoá contract; không tự động đóng task, không tự động cấp Governance V4.1
= FULLY_ENFORCED (việc đó cần Integration + reconciliation riêng, xem phần
Integration của phiên này).

Impact:
- Không sửa `app/**`, `config/**`, `tests/test_golden_baseline.py`,
  `tests/fixtures/golden/**`.
- Chỉ ghi quyết định này + cập nhật state/progress cần thiết trong cùng phiên
  (`PROJECT/PROJECT_PROGRESS.md`, `PROJECT/LO_TRINH_DE_HIEU.md`,
  `PROJECT/REVIEW_BUDGET_LEDGER.md`, `docs/tasks/TASK-GOLDEN-BASELINE-001-PLAN.md`).
- Repair cycle còn lại (`remaining = 1`) giữ nguyên **UNUSED** — đóng task không
  bắt buộc phải tiêu hết ngân sách.

Can Revisit After:
Một Repair Cycle #2 hoặc Review #3 mới có thẩm quyền riêng (không tự mở trong
phiên Freeze Finalization/Integration), hoặc một Owner Decision khác thay đổi
Golden Baseline contract.

## DEC-143

Date:
2026-08-27

Task:
TASK-108B (Converted Revenue) — Owner Decision `OD-108B-01`, ghi nhận trong
phiên "OWNER DECISION RECORDING + DEPENDENCY READINESS CHECK". Artifact
discovery đi kèm:
`docs/tasks/TASK-108B-eligible-costs-owner-definition.md` (commit `107dd80`).

Decision:

Chủ dự án phê duyệt định nghĩa nghiệp vụ cho `EligibleCosts` và các số hạng
liên quan của `EligibleKpiProfit`. **Đóng C15** (`docs/analysis/10_OPEN_QUESTIONS.md`).

**1. `EligibleCosts` = CLOSED EMPTY SET.**

```
EligibleCosts = {}
```

Không khoản chi phí nào hiện tại được tính thêm vào `EligibleKpiProfit` chỉ vì
chúng tồn tại trong dữ liệu. Đây là **quyết định nghiệp vụ có thẩm quyền rằng
tập hiện tại là rỗng**, KHÔNG phải fallback kỹ thuật `EligibleCosts = 0` — đúng
sự phân biệt mà C15 và DEC-103 tồn tại để bảo vệ. Thêm một cost sau này cần
Owner Decision riêng + effective date + provenance.

**2. `DeliveryCost` = NOT ELIGIBLE FOR NOW.**

Không cộng/trừ `DeliveryCost` (`Lương chuyến` / `K: Chi phí giao`) vào
`EligibleKpiProfit`. Lý do của chủ dự án: đây là ứng viên duy nhất chưa bị nhúng
vào công thức khác; hiện chưa có authority nghiệp vụ đủ để khẳng định nó phải
tham gia KPI profit; và impact tài chính đã được discovery chứng minh là lớn nên
không được suy đoán (10,94 % / 12,16 % lợi nhuận trên hai kỳ Golden — tương
đương 0,8–1,8 triệu VND thưởng/người/tháng).

Re-trigger: nếu sau này Owner xác nhận `DeliveryCost` phải tham gia KPI profit,
mở decision riêng. **Không sửa lịch sử `OD-108B-01`.**

**3. `OtherKpiAdjustment` = 0 BY DEFINITION**, cho tới khi một Owner Decision
tương lai thay đổi. Đây là định nghĩa nghiệp vụ tường minh, không phải fallback
kỹ thuật khi thiếu dữ liệu. Adjustment mới xuất hiện sau này phải có
source/config/provenance/effective-date và Owner authority riêng.

Quyết định này **đóng B-02** của artifact discovery (`OtherKpiAdjustment` trước
đó xuất hiện đúng một lần trong toàn repo và toàn đặc tả, chỉ bên trong công
thức, không có open question nào theo dõi).

**4. Canonical `EligibleKpiProfit` formula.**

Chủ dự án chốt: `Discount` **có** tham gia công thức lợi nhuận KPI; mọi biến thể
tài liệu thiếu `− Discount` là `STALE/SUPERSEDED` đối với semantics hiện hành.
Không xoá tài liệu lịch sử — dùng normative/current-state pointer.

Dạng canonical (chuẩn hoá số học — xem "Reason" điểm 4 về việc chuẩn hoá này):

```
EligibleKpiProfit = (SellPrice − KpiPurchasePrice) × Quantity
                    − Discount
                    − SUM(EligibleCosts)
                    + OtherKpiAdjustment
```

Theo `OD-108B-01`: `SUM(EligibleCosts) = 0` và `OtherKpiAdjustment = 0`, nên
dạng rút gọn hiện hành là:

```
EligibleKpiProfit = (SellPrice − KpiPurchasePrice) × Quantity − Discount
```

Tương đương, viết theo `NormalizedSales` như trong văn bản Owner:

```
NormalizedSales   = SellPrice × Quantity − Discount        (đã trừ Discount)
EligibleKpiProfit = NormalizedSales − KpiPurchasePrice × Quantity
```

Hai dạng trên là **một**, và `Discount` được trừ **đúng một lần** ở cả hai.

**5. Double-count rule — NO DOUBLE COUNT.**

Một cost không được thêm vào `EligibleCosts` nếu đã được phản ánh trong
`NormalizedSales`, `Discount`, `KpiPurchasePrice`, hay một profit/adjustment
component khác của cùng metric. Mỗi `EligibleCost` tương lai phải chứng minh
đủ 6 điều: source; scope; sign; ownership; effective date; và **không được
nhúng ở nơi khác**.

**6. TASK-109 contract.** `TASK-108B` phải cung cấp **per-line**:
`EligibleKpiProfit`; provenance của `EligibleKpiProfit`; scheme/bucket
classification; effective-date provenance. `TASK-109` aggregate
`SUM EligibleKpiProfit` và `CR` tách `Personal` / `ADS` / `Total`. **Không**
yêu cầu `eligible_cost_total` riêng khi `EligibleCosts` còn là tập rỗng.
**Không** tạo category breakdown khi chưa có production requirement.

**7. Risk & Review Budget.** `Effective Risk = HIGH`;
`repair_cycles_allowed = 2`, `used = 0`, `remaining = 2`; ngân sách thuộc
**toàn lineage `TASK-108B`** (sub-unit không có ngân sách riêng, không reset).

**8. Trạng thái sau quyết định này.**

```
TASK-108B
    SEMANTIC_DEFINITION   = APPROVED
    IMPLEMENTATION        = BLOCKED_BY_DEPENDENCY
    BLOCKED_BY_DEPENDENCY = [ AccountingPurchasePrice / Price Master,
                              confirmed KpiPurchaseAdjustment persistence ]
```

`SEMANTIC_DEFINITION = APPROVED` **không** đồng nghĩa `IMPLEMENTATION = READY`.
Xem "Reason" điểm 5.

Reason:

**1. Vì sao tập rỗng là câu trả lời đúng, không phải né tránh.** Discovery liệt
kê 14 khoản chi phí hiện hữu trong code/config/spec/data model/workbook. Audit
double-count cho thấy **13/14 khoản đã được authority hiện có xử lý ở một chỗ
khác trong công thức**: `Discount` là số hạng riêng (DEC-114, DEC-122);
`KpiPurchaseAdjustment` đã nhúng trong `KpiPurchasePrice` (`F = L + J`, bằng
chứng số học từ `06.2026 Tín Phát` dòng 10–11); các dòng `Chi phí vận chuyển` /
`lắp đặt` / `Chênh VAT` / `giao hộ` / `Phí đổi trả` đã tính vào **cả doanh số
lẫn lợi nhuận** dưới dạng dòng sản phẩm (DEC-110, có mặt thật trong Golden
fixture: 22 dòng ở 01.2026, 12 dòng ở 06.2026); thưởng/lương/phụ cấp là **hệ
quả** của `ConvertedRevenue`, đưa vào sẽ tạo vòng lặp; `SourceProfit` chỉ để
đối chiếu (DEC-103). Đưa bất kỳ khoản nào trong 13 khoản đó vào `EligibleCosts`
là **trừ hai lần**.

**2. Vì sao `DeliveryCost` — ứng viên thứ 14 — vẫn là NOT ELIGIBLE.** Ba bằng
chứng độc lập cùng chỉ một hướng: workbook thật tính `K1 = SUM(K3:K945)` rồi
**không nạp vào Summary** (công ty đã có con số đó và đã chọn không dùng cho
KPI); `docs/analysis/01_DATA_MAPPING.md` xếp nó là cột báo cáo độc lập, không phải số hạng
của công thức lợi nhuận; đặc tả §11 đặt `EligibleCosts` trong ngữ cảnh
adjustment giá nhập, không phải chi phí logistics. Ba bằng chứng này không đủ
để agent tự quyết (C15 cấm chính kiểu suy đoán đó) — nên chúng được trình cho
chủ dự án, và chủ dự án đã quyết.

**3. Vì sao `OtherKpiAdjustment = 0` là định nghĩa chứ không phải fallback.**
DEC-126 §6 cấm mặc định adjustment **chưa xác định** bằng 0. `OD-108B-01` không
vi phạm điều đó: nó **xác định** rằng hiện tại không tồn tại khoản adjustment
nào thuộc loại này. Khác biệt về thẩm quyền, giống hệt phân biệt ở điểm 1.

**4. CHUẨN HOÁ SỐ HỌC CỦA CÔNG THỨC — phải ghi lại tường minh.**

Văn bản `OD-108B-01` §4 viết dạng:

```
EligibleKpiProfit = NormalizedSales − Discount − KpiPurchasePrice
                    − SUM(EligibleCosts) + OtherKpiAdjustment
```

Đọc **nguyên văn** theo đúng định nghĩa các thuật ngữ đang tồn tại trong repo
thì dạng này lệch ở hai điểm số học:

- `NormalizedSales` trong repo **đã trừ `Discount`**. Bằng chứng: `app/modules/
  importing/normalizer.py:27` (`total_sales = sell_price * quantity − discount`)
  và Golden trên dữ liệu production thật — `sales_raw_gross − sales_normalized`
  bằng **đúng** `discount_total` ở cả hai kỳ (2.300.000 ở 01.2026; 400.000 ở
  06.2026). Trừ `Discount` một lần nữa là trừ hai lần.
- `KpiPurchasePrice` là **đơn giá** (`F: Giá nhập TT`, cùng chiều với
  `SellPrice`/`G`), không phải giá trị dòng. Workbook nhân với số lượng:
  `In = (Gn − Fn) * En`. Thiếu `× Quantity` làm sai thứ nguyên.

Ví dụ có số: một dòng `SellPrice = 10.000`, `KpiPurchasePrice = 8.000`,
`Quantity = 3`, `Discount = 500`. Dạng canonical cho `5.500`; đọc nguyên văn
dạng prose cho `21.000` — sai khoảng 3,8 lần.

Chuẩn hoá này **không** đổi ý chí của chủ dự án, mà thực hiện đúng ba điều
chính `OD-108B-01` đã tuyên bố: (a) `Discount` **có** tham gia công thức (§4);
(b) **NO DOUBLE COUNT** — không tính một khoản hai lần khi nó đã phản ánh trong
`NormalizedSales` (§5); (c) khớp authority đã tồn tại trước đó là DEC-122 và
`docs/analysis/03_RULE_CLASSIFICATION.md` §U, vốn đã ghi đúng dạng
`(SellPrice − KpiPurchasePrice) × Quantity − Discount − EligibleCosts +
OtherKpiAdjustment`. Chỉ có **đúng một** cách đọc thoả mãn đồng thời cả ba, và
đó là dạng canonical ghi ở Decision §4.

Ghi lại ở đây theo `governance/core/V4_1_POLICY_FREEZE.md` §11 (Artifact
Internal Precedence: phần quy phạm thắng prose, nhưng divergence **phải được
báo cáo**, không được sửa im lặng). **Chủ dự án cần xác nhận lại chuẩn hoá này
ở lần tương tác kế tiếp**; nếu chủ dự án thực sự muốn dạng prose theo nghĩa
đen, đó là một thay đổi nghiệp vụ khác và cần một DEC mới.

**5. Vì sao `SEMANTIC_DEFINITION = APPROVED` mà `IMPLEMENTATION` vẫn BLOCKED.**
`OD-108B-01` đóng **toàn bộ 4 khoảng trống semantic** mà discovery nêu
(`EligibleCosts`, `DeliveryCost`, `OtherKpiAdjustment`, canonical formula).
Nhưng công thức rút gọn `(SellPrice − KpiPurchasePrice) × Quantity − Discount`
vẫn cần `KpiPurchasePrice`, mà `KpiPurchasePrice = AccountingPurchasePrice +
KpiPurchaseAdjustment` — **cả hai vế phải đều chưa tồn tại**:

- `AccountingPurchasePrice`: `PendingPriceProvider.lookup()` trả `None`
  **vô điều kiện** (`app/modules/pricing/provider.py`), và đó là implementation
  đúng vì chưa có Price Master nào tồn tại (DEC-103). Golden xác nhận trên dữ
  liệu production: `price_source_distribution = {Pending: 351}` (01.2026) và
  `{Pending: 180}` (06.2026) — **100 %**, theo cấu trúc chứ không phải theo dữ
  liệu.
- `KpiPurchaseAdjustment`: **không tồn tại như một field** trên `WorkingLine`;
  `AdjustmentResolver` (TASK-106) cố ý **không** nối vào `run_import()` và chỉ
  trả `suggested_amount`. DEC-126 §5 yêu cầu chỉ `final_amount` đã được người
  dùng xác nhận mới vào công thức KPI; §6 cấm mặc định 0.

Đây là blocker **dữ liệu/cơ chế**, không phải blocker semantic — nên phân biệt
`SEMANTIC_DEFINITION` với `IMPLEMENTATION` là bắt buộc, không phải hình thức.

**6. Số blocker giảm từ 4 xuống 2.** Discovery liệt kê 4; `OD-108B-01` đóng 2
(`EligibleCosts`/C15 và `OtherKpiAdjustment`) cộng conflict công thức B-03. Còn
lại đúng 2, cả hai đều là dependency dữ liệu.

Risk:

`Effective Risk = HIGH`, chấm theo failure path (V4.1 §4), **không** theo tên
file. Failure path: `EligibleCosts` → `EligibleKpiProfit` → chia rate →
`ConvertedRevenue` → `% Target` → `Thưởng` → `Tổng lương` — kết thúc ở **tiền
lương của người thật**.

`Local Risk = MEDIUM` (số học đơn giản); `Blast Radius = HIGH`. **Golden Baseline
KHÔNG được dùng để hạ bậc** (V4.1 §4.1): toàn bộ failure path của TASK-108B nằm
ngoài vùng Golden phủ — profit số học chưa từng được đo (100 % giá nhập Pending),
fixture 100 % `ADS` nên bucket `PERSONAL`, `NOI_THANH_2`, `GIA_DUNG_8` và đơn
trộn scheme đều phủ 0 %.

Rủi ro còn lại của chính quyết định này:

- **Tập rỗng bị đọc nhầm thành `= 0` kỹ thuật.** Nếu một session sau đọc
  `EligibleCosts = 0` rồi kết luận "vậy khỏi cần config, khỏi cần provenance",
  hệ thống mất khả năng phân biệt "không có chi phí nào" với "chưa ai nhập" —
  đúng lỗi DEC-103 phòng. Giảm nhẹ: `config/eligible_costs.yaml` phải tồn tại
  với `eligible_cost_categories: []` tường minh + danh sách `excluded_by_authority`,
  và provenance `Config:EmptySet(OD-108B-01)` phải nhìn thấy được trên mọi dòng.
- **Chuẩn hoá công thức ở Reason điểm 4 chưa được chủ dự án xác nhận lại.** Nếu
  ý chí thật khác với chuẩn hoá, mọi con số KPI sẽ sai theo hệ số. Giảm nhẹ:
  đã ghi tường minh ở đây thay vì áp dụng im lặng; cần xác nhận trước khi
  implementation bắt đầu.
- **`DeliveryCost` re-trigger.** Nếu sau này Owner đổi ý, mọi số lịch sử phải
  đọc lại và `HB-108B-01` (trùng lặp giữa `Lương chuyến` và dòng `Chi phí vận
  chuyển`) phải được đo trước — hiện chưa ai đo tỉ lệ trùng đó.

Impact:
- `PROJECT/PROJECT_DECISIONS.md` — DEC này (ID cấp sau khi quét namespace toàn
  repo, không chỉ một file — bài học va chạm `DEC-128`; `DEC-143` xác nhận trống).
- `PROJECT/PROJECT_PROGRESS.md` — TASK-108B đổi từ `BLOCKED (C15)` sang
  `SEMANTIC_DEFINITION = APPROVED · IMPLEMENTATION = BLOCKED_BY_DEPENDENCY`;
  C15 ghi nhận đã đóng.
- `PROJECT/LO_TRINH_DE_HIEU.md` — cập nhật dòng 12b và phần "việc còn lại".
- `PROJECT/REVIEW_BUDGET_LEDGER.md` — thêm entry lineage mới `TASK-108B`.
- `docs/analysis/10_OPEN_QUESTIONS.md` — **C15 = ĐÃ ĐÓNG**; thêm ghi chú
  `OtherKpiAdjustment` đã được định nghĩa (không cần mở C16).
- `docs/tasks/TASK-108B-eligible-costs-owner-definition.md` — append
  current-state pointer, **không** rewrite phần discovery lịch sử.
- **Không** sửa `app/**`, `config/**`, `tests/**`, Golden fixture/expected,
  `TASK-110`, `CHECK-110-16`, `R1-A1`, `governance/**`.

Can Revisit After:
- Chủ dự án xác nhận (hoặc bác bỏ) chuẩn hoá số học ở Reason điểm 4.
- Chủ dự án quyết định `DeliveryCost` phải tham gia KPI profit — decision riêng,
  không sửa `OD-108B-01`.
- Xuất hiện một khoản adjustment mới cần `OtherKpiAdjustment ≠ 0` — decision
  riêng kèm source/config/provenance/effective-date.
