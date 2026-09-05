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

## DEC-144

Date:
2026-08-27

Task:
`TASK-108B` — Owner clarification cho `DEC-143` + Owner Decision `OD-108B-02`
(confirmed `KpiPurchaseAdjustment`), ghi trong phiên "TASK-108B DEPENDENCY
RESOLUTION + TASK-105B READINESS DISCOVERY". Mở discovery cho `TASK-105B`.

Decision:

**1. XÁC NHẬN canonical `EligibleKpiProfit` (đóng §19.1 của artifact TASK-108B).**

Chủ dự án xác nhận chuẩn hoá số học mà `DEC-143` Reason điểm 4 đã báo cáo là
**ĐÚNG**. Công thức canonical, có thẩm quyền:

```
EligibleKpiProfit = (SellPrice − KpiPurchasePrice) × Quantity − Discount
```

**Không** dùng dạng `NormalizedSales − Discount − KpiPurchasePrice` khi
`NormalizedSales` đã trừ `Discount` — trong repo này nó **đã trừ**
(`app/modules/importing/normalizer.py:27`; Golden xác nhận
`sales_raw_gross − sales_normalized` = đúng `discount_total` ở cả hai kỳ).

Hai nguyên tắc bắt buộc:
- **NO DOUBLE COUNT** — `Discount` chỉ được tác động **đúng một lần**.
- `KpiPurchasePrice` là **đơn giá**, bắt buộc nhân `Quantity` khi tính profit
  của line.

`DEC-143` §4 **không bị rewrite**; mục này là current-state confirmation của nó.

**2. `OD-108B-02` — confirmed `KpiPurchaseAdjustment`, phương án A cho Phase 1.**

```
CÓ confirmed record có hiệu lực:
    KpiPurchasePrice = AccountingPurchasePrice + ConfirmedKpiPurchaseAdjustment

ĐÃ XÁC ĐỊNH KHÔNG CÓ confirmed record áp dụng:
    KpiPurchasePrice = AccountingPurchasePrice
    provenance       = Config:NoConfirmedAdjustment
```

**3. ABSENCE ≠ UNKNOWN ≠ ZERO — ba trạng thái, không được gộp.**

"Không có confirmed adjustment" **KHÔNG** đồng nghĩa với: lookup lỗi; source
chưa load; dữ liệu adjustment chưa available; persistence chưa sẵn sàng; trạng
thái unknown; parse failure.

```
DETERMINED_ABSENCE   → source ĐÃ load, 0 record khớp → KpiPurchasePrice = AccountingPurchasePrice
                       provenance = Config:NoConfirmedAdjustment
UNKNOWN /
SOURCE_UNAVAILABLE /
LOOKUP_FAILURE       → Pending. KpiPurchasePrice = None ⇒ EligibleKpiProfit = None
                       TUYỆT ĐỐI KHÔNG tự động thành adjustment = 0
```

Mục tiêu nguyên văn của chủ dự án: *"không biến absence thành unknown, và cũng
không biến unknown thành zero."* Đây là DEC-103 và DEC-126 §6 áp dụng lại, ở
một tầng khác.

**4. Effective-date + provenance của adjustment.** Nếu adjustment tồn tại, phải
xác định được đủ 5 thứ: `source`; `effective date`; `matched record`;
`adjustment amount`; `provenance`. **Không** hardcode adjustment vào engine.
**Không** tạo default adjustment giả. **Không** làm mất khả năng nâng cấp sang
persistence đầy đủ ở Phase 2/3 (DEC-126 §3: một `Order` hỗ trợ **nhiều**
Adjustment record, không phải một field cộng dồn).

**5. Hệ quả — yêu cầu cơ chế còn lại (KHÔNG phải Owner blocker).**

`OD-108B-02` đóng **hoàn toàn** phần semantic. Nhưng để phân biệt
`DETERMINED_ABSENCE` với `SOURCE_UNAVAILABLE` theo đúng điểm 3, hệ thống phải
có một **confirmed-adjustment source được khai báo và load được — kể cả khi
rỗng**. Hiện tại **không tồn tại nguồn nào**: `WorkingLine` không có field
`kpi_purchase_adjustment`, và `AdjustmentResolver` (TASK-106) cố ý không nối
vào `run_import()` và chỉ trả `suggested_amount`.

Nói cách khác: trạng thái hôm nay là `SOURCE_UNAVAILABLE`, **không phải**
`DETERMINED_ABSENCE` — nên chưa được áp nhánh `= AccountingPurchasePrice`.

Đây là **deliverable cơ chế nhỏ**, thuộc phạm vi implementation của
`TASK-108B` (một source khai báo rỗng + loader + provenance, cùng khuôn "closed
empty set" của `OD-108B-01`), **không** cần thêm Owner Decision. Nó **có** chạm
`app/modules/adjustment/` (vùng của TASK-106 đã DONE) — nếu chủ dự án muốn
tách thành `TASK-106B` riêng thì được, nhưng không bắt buộc.

**6. Blocker của `TASK-108B` sau quyết định này.**

```
TASK-108B
    SEMANTIC_DEFINITION = APPROVED          (DEC-143 + DEC-144, đầy đủ)
    IMPLEMENTATION      = BLOCKED_BY_DEPENDENCY
    BLOCKERS            = [ AccountingPurchasePrice / Price Master ]   ← duy nhất, ngoại lai
    IN-SCOPE MECHANISM  = [ confirmed-adjustment source khai báo rỗng ] ← nội bộ TASK-108B
```

Giảm từ 2 blocker ngoại lai xuống **1**.

**7. `TASK-105B` — FilePriceProvider, mở ở trạng thái discovery.**

```
root_task       : TASK-105B
effective_risk  : HIGH
repair_cycles   : 2 allowed / 0 used / 2 remaining
lineage         : MỚI, độc lập TASK-108B / TASK-110 / TASK-GOLDEN-BASELINE-001
state           : DISCOVERY DONE — SEMANTIC_READINESS = OWNER_DECISION_REQUIRED
```

`HIGH` chấm theo **data path**, không theo tên module: giá sai →
`KpiPurchasePrice` sai → `EligibleKpiProfit` sai → `CR` sai → **KPI/lương sai**.
Một file reader **không** được coi là LOW chỉ vì nó là adapter. Golden **không**
hạ bậc (V4.1 §4.1) — Golden hiện 100 % `Pending` nên chưa phủ profit arithmetic.

Discovery **không** tiêu repair cycle.

**8. Ba câu hỏi `TASK-105B` cần chủ dự án trả lời** (chi tiết + bảng schema:
`docs/tasks/TASK-108B-eligible-costs-owner-definition.md` Phần III):

- **Q1 — `effective_to` bắt buộc hay engine tự đóng khoảng?** `effective_rows()`
  (`app/modules/config/loader.py:42`) dùng khoảng **đóng**
  `[effective_from, effective_to]`, `effective_to: null` = còn hiệu lực. Nếu chủ
  dự án chỉ ghi `effective_from` và để trống `effective_to` ở **mọi** dòng thì
  hai mức giá của cùng một mã sẽ **cùng hiệu lực** ⇒ mơ hồ. Tiền lệ
  `scheme_resolver` coi hoà là `AmbiguousSchemeConfigError` và **từ chối tự
  chọn**; bảng giá không có chiều specificity nào để phá hoà. Không được tự
  chọn "latest/nearest/current" (DEC-121).
- **Q2 — khớp tên sản phẩm: exact hay chuẩn hoá?** Trên dữ liệu production
  (Golden 2 kỳ, 528 dòng): **15 tên có khoảng trắng thừa** đầu/cuối và **1 cặp
  chỉ khác nhau đúng một khoảng trắng cuối** (`Cây nước Kangaroo KG36A2` vs
  `Cây nước Kangaroo KG36A2 `). Khớp exact ⇒ những dòng đó **im lặng không tra
  được giá** ⇒ `Pending` ⇒ `EligibleKpiProfit = None`.
- **Q3 — dòng không phải sản phẩm** (`Chi phí vận chuyển`, `Chi phí lắp đặt`,
  `Chênh VAT`, `Chi phí giao hộ`, `Phí đổi trả` — ~1.250 dòng/6 tháng; 22 dòng
  ở 01.2026 và 12 dòng ở 06.2026 trong chính Golden fixture) **có giá nhập
  không?** DEC-110 nói chúng **có** tính vào lợi nhuận. ERP ghi lợi nhuận của
  chúng đúng bằng doanh số, tức giá nhập = 0
  (`docs/analysis/01_DATA_MAPPING.md` §3) — nhưng đó là **quan sát**, và DEC-103
  cấm agent tự suy đoán `0`. Nếu bảng giá bỏ sót nhóm này, chúng `Pending` vĩnh
  viễn và `EligibleKpiProfit` của cả tháng **không bao giờ hoàn tất**.

Reason:

**1. Vì sao xác nhận công thức là bước bắt buộc chứ không phải thủ tục.**
`DEC-143` Reason điểm 4 đã báo cáo divergence theo V4.1 §11 và ghi rõ *"cần chủ
dự án xác nhận lại"*. Chủ dự án đã xác nhận. Không có xác nhận này, mọi
implementation sau đó đứng trên một cách đọc do agent chọn — đúng thứ mà toàn bộ
chuỗi DEC-103/125/126/143 tồn tại để chặn.

**2. Vì sao phương án A hợp lệ mà không vi phạm DEC-126 §6.** DEC-126 §6 cấm mặc
định adjustment **chưa xác định** bằng `0`. `OD-108B-02` không làm thế: nó phân
biệt **absence đã xác định** (source load được, 0 record khớp) với **unknown**
(source chưa có). Chỉ nhánh thứ nhất được dùng `AccountingPurchasePrice`, và
nhánh đó mang provenance riêng `Config:NoConfirmedAdjustment` để nhìn thấy được.
Cùng khuôn thẩm quyền với `OD-108B-01` §1 (closed empty set ≠ fallback = 0).

**3. Vì sao vẫn phải báo cáo một yêu cầu cơ chế còn lại thay vì tuyên bố "chỉ
còn Price Master".** Phiên này được yêu cầu tính lại blocker từ trạng thái mới
và **không** mặc định kết luận. Kiểm chứng bằng code: `grep` cho
`kpi_purchase_adjustment` trên `app/modules/domain/models.py` = 0 hit;
`AdjustmentResolver` không xuất hiện trong `app/pipeline.py`. Vì vậy hôm nay
**không có nguồn nào để "xác định là không có record"**. Đây đúng là trường hợp
`SOURCE_UNAVAILABLE` mà chính điểm 3 cấm biến thành `0`. Bỏ qua chi tiết này
rồi implement sẽ tái lập đúng lỗi mà `OD-108B-02` vừa cấm.

**4. Vì sao `TASK-105B` là `OWNER_DECISION_REQUIRED` chứ không `READY`.** Hai
trong ba câu hỏi (Q1, Q3) **không** có authority trong repo để suy ra, và cả hai
đều thuộc loại "đoán sai thì không ai nhìn thấy bằng mắt": Q1 sai làm cả kỳ dùng
sai mức giá; Q3 sai làm cả tháng không tính được lợi nhuận. Q2 có tiền lệ kỹ
thuật (`ac_classifier._normalize`: NFC + gộp khoảng trắng + không phân biệt
hoa/thường) nhưng áp dụng nó cho **khoá tra cứu tiền** là quyết định nghiệp vụ,
không phải lựa chọn kỹ thuật. Cả ba đều có **production path chứng minh được
bằng dữ liệu Golden thật** (V4.1 §5 nguồn 3 và 4), nên là `BLOCKING SEMANTIC`
chứ không phải hardening.

**5. Vì sao `TASK-105B` không phá Golden.** `FilePriceProvider` là
implementation thứ hai của một Protocol đã tồn tại; nó **không** thêm field vào
`WorkingLine`, nên `lines_digest` và `_covered_digest_fields` không đổi. Golden
tiếp tục chạy với `PendingPriceProvider` mặc định (`app/pipeline.py:103`), và
chữ ký `run_import` không đổi. Focused test là đủ cho `TASK-105B`. Việc mở rộng
Golden sang profit arithmetic thuộc `TASK-108B`, **không** thuộc `TASK-105B` —
không được hạ Blast Radius dựa trên coverage chưa tồn tại.

Risk:

`Effective Risk = HIGH` cho cả `TASK-108B` và `TASK-105B`, chấm theo data path
(V4.1 §4), không theo tên module/file:

```
Price sai → KpiPurchasePrice sai → EligibleKpiProfit sai → CR sai → KPI/lương sai
```

Rủi ro cụ thể của chính quyết định này:

- **Nhánh `Config:NoConfirmedAdjustment` bị dùng sai chỗ.** Nếu một session sau
  áp nhánh này khi source **chưa** tồn tại, mọi dòng sẽ mang `KpiPurchasePrice =
  AccountingPurchasePrice` như thể đã xác định không có adjustment — trong khi
  635/18.148 dòng của workbook thật **có** adjustment. Giảm nhẹ: điểm 5 ghi rõ
  yêu cầu source khai báo rỗng, và provenance phải phân biệt được hai nhánh.
- **Bảng giá thiếu dòng ⇒ im lặng.** Nếu Q2/Q3 chưa chốt mà đã implement, dòng
  không khớp sẽ `Pending` mà không ai để ý — Review Queue hiện gộp
  `Missing.PurchasePrice` thành **một** mục batch (DEC-128 §1) vì Phase 1 mọi
  dòng đều Pending. Giảm nhẹ: khi `TASK-105B` xong, phải lật
  `config/validation.yaml` → `aggregate: false` để một giá thiếu trở lại là bất
  thường từng dòng — cơ chế này DEC-128 §1 đã dự trù sẵn, không cần quyết định
  mới.

Impact:
- `PROJECT/PROJECT_DECISIONS.md` — DEC này (ID cấp sau khi quét namespace toàn
  repo; `DEC-144` xác nhận trống).
- `PROJECT/PROJECT_PROGRESS.md` — `TASK-108B` còn 1 blocker ngoại lai; thêm
  `TASK-105B` vào roadmap PHASE-01.
- `PROJECT/LO_TRINH_DE_HIEU.md` — thêm bước 11b (`TASK-105B`) và ba câu hỏi cần
  chủ dự án trả lời.
- `PROJECT/REVIEW_BUDGET_LEDGER.md` — entry lineage mới `TASK-105B`; cập nhật
  trạng thái dependency của `TASK-108B`.
- `docs/tasks/TASK-108B-eligible-costs-owner-definition.md` — Phần III
  (current-state pointer + discovery `TASK-105B` + price file contract).
- **Không** sửa `app/**`, `config/**`, `tests/**`, Golden fixture/expected,
  `TASK-110`, `CHECK-110-16`, `R1-A1`, `governance/**`.

Can Revisit After:
- Chủ dự án trả lời Q1/Q2/Q3 ⇒ `TASK-105B` chuyển `SEMANTIC_READINESS = READY`.
- Phase 2/3 (`TASK-202`/`302`/`305`) xây persistence adjustment thật ⇒ nhánh
  `Config:NoConfirmedAdjustment` được thay bằng lookup thật, `OD-108B-02` §2
  giữ nguyên semantics.
- `TASK-401`/`TASK-402` (Phase 4) thay `FilePriceProvider` bằng Price Master
  thật theo `ProductCode` — Protocol không đổi.

## DEC-145

Date:
2026-08-27

Task:
`TASK-105B` — Owner Decision `OD-105B-01` (Q1/Q2/Q3) + Implementation Readiness
Finalization. Ghi trong phiên "TASK-105B OWNER DECISION Q1/Q2/Q3". Discovery
tiền nhiệm: `docs/tasks/TASK-108B-eligible-costs-owner-definition.md` Phần III
(`DEC-144` §7–8).

Decision:

**1. Q1 — Effective period.**

```
effective_from : REQUIRED, mọi record
effective_to   : REQUIRED cho mọi record lịch sử đã kết thúc hiệu lực;
                 chỉ được rỗng ở ĐÚNG MỘT record hiện hành cuối cùng
                 của mỗi NORMALIZED product_key
khoảng         : ĐÓNG — [effective_from, effective_to]
overlap        : CẤM (cùng normalized key) → INVALID PRICE MASTER
gap            : ĐƯỢC PHÉP, và có nghĩa NO PRICE AVAILABLE → lookup None → Pending
>1 record effective_to rỗng cùng key → INVALID PRICE MASTER
```

**Cấm tuyệt đối** `latest` / `nearest` / `current` / fallback về record gần nhất
khi `sale_date` không nằm trong một khoảng hiệu lực hợp lệ. Không tự lấp gap.
Không tự giải quyết overlap bằng precedence.

**2. Q2 — Product key normalization.**

Không dùng exact raw string. Canonical normalization:

```
Unicode NFC → strip đầu/cuối → collapse whitespace nội bộ về đúng 1 space → casefold
```

**KHÔNG**: bỏ dấu tiếng Việt; bỏ punctuation; sửa model number; fuzzy matching;
nearest-match; contains-match; AI matching.

Hai raw product khác nhau tạo **cùng** normalized key nhưng mang record giá
**mâu thuẫn** → `INVALID PRICE MASTER`. Không tự chọn một record.

Provenance phải giữ được đủ ba: `raw product_key` từ price file; `normalized
lookup key`; `matched record`.

**3. Q3 — Supplementary / expense lines.**

Dòng mà classification production xác định là chi phí vận chuyển / lắp đặt /
chênh VAT, và thuộc đúng semantic supplementary/expense-line **đã có authority**:

```
AccountingPurchasePrice = 0 BY DEFINITION
provenance = Policy:SupplementaryExpenseZeroPurchasePrice
```

Các dòng này: không cần record trong Price Master; không được lookup rồi coi
missing là lỗi; **không** được đưa vào `EligibleCosts` lần nữa; không được làm
phát sinh double-count.

**Cấm** xác định chúng bằng một substring heuristic **mới** nằm trong
`FilePriceProvider`. Phải **reuse** classification / semantic rule hiện có
trong production.

Product line **thông thường** không có price record: `lookup = None` → `Pending`.
**Không** dùng `purchase_price = 0` thay cho missing.

**4. Price file contract (Phase 1).**

```
REQUIRED : product_key, effective_from, effective_to, purchase_price
OPTIONAL : source
KHÔNG CẦN: product_code, product_name, supplier, updated_at
```

`product_key` = raw key lấy từ `Tên hàng trên chứng từ`, tra bằng normalized key
theo §2. `effective_from`/`effective_to` = `YYYY-MM-DD`; `effective_to` rỗng chỉ
với record hiện hành cuối cùng. `purchase_price` = **VND**, semantics
`Decimal`/integer, **không** float approximation (ADR-103). `source` = text
provenance tuỳ chọn.

**5. Price validation — chốt.**

```
purchase_price < 0                              → INVALID
purchase_price = 0                              → chỉ hợp lệ khi Owner/business source
                                                  thực sự khai giá 0; KHÔNG dùng 0 thay missing
product_key rỗng                                → INVALID
effective_from lỗi                              → INVALID
effective_to < effective_from                   → INVALID
interval overlap cùng normalized key            → INVALID
same normalized key + same period + khác giá    → INVALID
duplicate row giống hệt hoàn toàn               → REJECT (xem Reason điểm 4)
sale_date trước record đầu tiên                 → None → Pending
sale_date nằm trong gap                         → None → Pending
product không có trong Price Master             → None → Pending
```

Không fallback.

**6. Giữ nguyên `DEC-144`** về confirmed `KpiPurchaseAdjustment` (ba trạng thái
`CONFIRMED` / `DETERMINED_ABSENCE` / `UNKNOWN`) và canonical formula
`EligibleKpiProfit = (SellPrice − KpiPurchasePrice) × Quantity − Discount`;
`EligibleCosts = {}`; `DeliveryCost = NOT ELIGIBLE FOR NOW`;
`OtherKpiAdjustment = 0 BY DEFINITION`. Confirmed-adjustment source khai báo
được (kể cả empty) là **deliverable in-scope của `TASK-108B`**, không phải lý do
chờ Phase 2/3.

**7. Trạng thái readiness sau quyết định này.**

```
TASK-105B  (FilePriceProvider — phạm vi §1, §2, §4, §5)
    SEMANTIC_READINESS = READY
    IMPLEMENTATION     = READY

TASK-105B-Q3  (Supplementary zero-price policy — phạm vi §3)
    IMPLEMENTATION = BLOCKED_BY [ TASK-103 Product/Transaction Classification,
                                  enumeration chính xác nhóm dòng phụ ]

TASK-108B
    IMPLEMENTATION = BLOCKED_BY [ FilePriceProvider chưa tồn tại (TASK-105B),
                                  bảng giá thật chưa được cấp ]
```

Đây là **báo cáo dependency mà chính `OD-105B-01` §C yêu cầu**, không phải ép
kết luận. Bằng chứng ở Reason điểm 3.

Reason:

**1. Q1 và Q2 khớp authority đã tồn tại — không phát sinh cơ chế mới.**
Q1 dùng đúng semantics của `effective_rows()` (`app/modules/config/loader.py:42`,
khoảng đóng, `effective_to` rỗng = còn hiệu lực) và DEC-121 (tra theo ngày
nghiệp vụ của đơn). Việc coi overlap là `INVALID` thay vì tự phá hoà lặp lại
đúng tiền lệ `AmbiguousSchemeConfigError` của `ConversionSchemeResolver` —
engine từ chối chọn khi cấu hình mơ hồ.

**2. Q2 đã có implementation đúng, đã kiểm chứng.**
`app/modules/validation/text.py` → `fold()` thực hiện chính xác chuỗi NFC →
collapse whitespace → strip → casefold (kèm một bước re-NFC sau casefold, chặt
hơn spec và không đổi ngữ nghĩa). Kiểm chứng ba ví dụ của chủ dự án: cả ba cho
cùng key `'cây nước kangaroo kg36a2'`. Kiểm chứng trên dữ liệu production
(Golden 2 kỳ, 528 dòng): `331` raw key → `330` normalized key, gộp đúng **một**
cặp `Cây nước Kangaroo KG36A2` / `Cây nước Kangaroo KG36A2 ` — đúng cặp mà
discovery đã nêu. Không cần viết normalizer mới.

Lưu ý kiến trúc (không phải blocker): `text.py` hiện nằm trong
`app/modules/validation/`. Dùng nó từ tầng pricing tạo phụ thuộc chéo module.
Hai cách đều chấp nhận được — import trực tiếp, hoặc nâng `text.py` lên vị trí
dùng chung; đây là lựa chọn kỹ thuật của implementation, không cần Owner quyết.

**3. Q3 CÓ dependency thật — đúng điều `OD-105B-01` §C dự phòng.**

`OD-105B-01` §C yêu cầu **reuse classification hiện có** và **cấm** phát minh
matcher mới trong `FilePriceProvider`. Kiểm chứng bằng code:

- **`TASK-103` (Product/Transaction Classification) CHƯA LÀM.**
  `PROJECT/PROJECT_PROGRESS.md`: *"Product/transaction classification (dòng phụ
  có giá trị tiền) **chưa làm**"*.
- **`config/classification.yaml` KHÔNG TỒN TẠI** — `docs/analysis/03_RULE_CLASSIFICATION.md`
  §B tham chiếu nó, `ls config/` chỉ có 5 file, không có file này.
- Cơ chế **duy nhất** trong production là `is_non_product_line()`
  (`app/modules/validation/rules.py`), và docstring của chính nó nói:
  *"This is **noise reduction only**: deciding what such a line counts toward is
  Product/Transaction Classification, TASK-103."* và *"**Temporary by decision
  (HD-110-02).** This heuristic exists only because TASK-103 does not, and it
  **must never be tuned** to reproduce a historical count."*
- **HD-110-02** (đã được chủ dự án duyệt, ghi trong DEC): *"Đây là **giải pháp
  tạm**, **TASK-103 phải thay thế** chứ không kế thừa."*

⇒ Dùng nó để lái một trường **tiền** (`AccountingPurchasePrice`) là dùng sai
đúng mục đích mà nó tự tuyên bố là không phục vụ. Rủi ro cụ thể: nó nằm trong
tầng **validation severity** và được nối vào Review Queue; ai chỉnh danh sách
từ khoá để giảm nhiễu hàng đợi sau này sẽ **âm thầm đổi lương**.

- **Phạm vi từ khoá lệch, đo được trên dữ liệu production.** Keyword set hiện
  hành là `["phí", "công lắp đặt", "chênh vat", "chiết khấu", "voucher"]`. Trên
  Golden 2 kỳ: khớp **36** dòng, trong khi đúng ba nhóm §3 nêu chỉ **34** dòng.
  Hai dòng dôi ra là `Phụ Phí` và `Phụ Phí Đổi mới` — **không** thuộc ba nhóm
  chủ dự án quyết. Nhỏ về số lượng, nhưng chứng minh tập từ khoá được hiệu
  chỉnh cho *severity*, không phải cho *tiền*.
- **Enumeration chưa khớp giữa hai authority.** `OD-105B-01` §C nêu **ba** nhóm
  (vận chuyển, lắp đặt, chênh VAT). **DEC-110** — authority gốc mà §C viện dẫn —
  liệt kê **năm** nhóm, thêm `Chi phí giao hộ` (~8 dòng/6 tháng) và `Phí đổi trả`
  (2 dòng). Cần một danh sách enumerated chính xác trước khi zero-price bất kỳ
  dòng nào.

**4. `duplicate row giống hệt` → REJECT, theo đúng chỉ dẫn của chủ dự án.**
`OD-105B-01` §E nói dedupe chỉ khi *"existing project policy đã có authority
rõ"*. Đã quét: authority `Duplicate` duy nhất trong repo là loại Review Queue
cho **dòng bán hàng** (`cùng source_file + source_row`), không phải cho file cấu
hình/bảng giá. Không có authority ⇒ **REJECT**, để file lỗi được nhìn thấy —
đúng ưu tiên chủ dự án đã nêu.

**5. Vì sao `TASK-105B` là READY còn `TASK-105B-Q3` thì không — và vì sao tách
được.** `OD-105B-01` §C **cấm** đặt logic Q3 bên trong `FilePriceProvider`. Nên
Q3 vốn dĩ **không thuộc** provider: nó là một tầng policy phía trên, do
classification lái. Contract của Protocol
(`lookup(product_code, sale_date) -> Optional[Decimal]`) hoàn toàn không phụ
thuộc Q3. Vì vậy provider implement được ngay và đúng, còn tầng policy chờ
`TASK-103`.

**Hệ quả phải nói thẳng:** nếu chỉ có provider mà chưa có tầng Q3, các dòng phụ
sẽ **không có giá** → `Pending` → `EligibleKpiProfit = None` cho những dòng đó →
**tổng lợi nhuận KPI của cả tháng không hoàn tất**. An toàn (không có con số
sai), nhưng chưa dùng được để ra báo cáo. Đây chính là lý do Q3 tồn tại.

Risk:

`Effective Risk = HIGH` cho `TASK-105B`, chấm theo **data path** (V4.1 §4),
không theo tên module — một file reader **không** được coi là LOW:

```
Price sai → KpiPurchasePrice sai → EligibleKpiProfit sai → CR sai → KPI/lương sai
```

Golden **không** hạ bậc (V4.1 §4.1): `price_source_distribution = {Pending:
351/180}` = 100 %, nên profit arithmetic chưa từng được đo.

Rủi ro còn lại của chính quyết định này:

- **Tái dùng `is_non_product_line` cho tiền.** Nếu một session sau bỏ qua Reason
  điểm 3 và nối heuristic đó vào zero-price, `Phụ Phí`/`Phụ Phí Đổi mới` bị
  zero-price ngoài ý chủ dự án, và mọi lần tinh chỉnh nhiễu Review Queue về sau
  sẽ đổi lương. Giảm nhẹ: ghi tường minh ở đây; `TASK-105B-Q3` phải có check
  riêng chứng minh nguồn classification **không phải** `app/modules/validation/`.
- **Bảng giá thiếu dòng ⇒ im lặng.** `Missing.PurchasePrice` hiện gộp thành một
  mục batch (DEC-128 §1) vì Phase 1 mọi dòng đều Pending. Sau `TASK-105B` phải
  lật `config/validation.yaml` → `aggregate: false` để giá thiếu trở lại là bất
  thường từng dòng — cơ chế đã dự trù sẵn, chỉ cần nhớ lật.
- **`purchase_price = 0` hợp lệ có điều kiện.** §5 cho phép 0 khi business source
  thực sự khai 0. Nếu implementation không phân biệt được "0 do khai" với "0 do
  ô trống được ép kiểu", nó tái lập đúng lỗi DEC-103. `to_decimal()`
  (`app/modules/domain/money.py`) đã phân biệt ô trống (`None`) với `0` — phải
  dùng đúng nó, không tự parse.

Impact:
- `PROJECT/PROJECT_DECISIONS.md` — DEC này (ID cấp sau khi quét namespace toàn
  repo; `DEC-145` xác nhận trống).
- `PROJECT/PROJECT_PROGRESS.md` — `TASK-105B` = READY; tách `TASK-105B-Q3`
  BLOCKED bởi `TASK-103`; `TASK-108B` cập nhật blocker.
- `PROJECT/LO_TRINH_DE_HIEU.md` — bước 11b chuyển sang "sẵn sàng làm"; nêu rõ
  phần dòng phụ còn chờ.
- `PROJECT/REVIEW_BUDGET_LEDGER.md` — `TASK-105B` chuyển
  `OWNER_DECISION_REQUIRED` → `READY`; ghi `TASK-105B-Q3` và dependency
  `TASK-103`.
- `docs/tasks/TASK-108B-eligible-costs-owner-definition.md` — Phần IV
  (implementation contract + Completion Gate cho `TASK-105B`).
- **Không** sửa `app/**`, `config/**`, `tests/**`, Golden fixture/expected,
  `TASK-110`, `CHECK-110-16`, `R1-A1`, `governance/**`.

Can Revisit After:
- `TASK-103` (Product/Transaction Classification) hoàn thành ⇒ mở
  `TASK-105B-Q3`. Hoặc chủ dự án cấp một danh sách enumerated tường minh các
  dòng phụ (kèm authority) như giải pháp hẹp hơn `TASK-103` đầy đủ.
- `TASK-401`/`TASK-402` (Phase 4) thay `FilePriceProvider` bằng Price Master
  thật theo `ProductCode` — Protocol không đổi, `OD-105B-01` §1–§2 giữ nguyên
  semantics.

## DEC-146

Date:
2026-08-27

Task:
`TASK-105B` — Architecture Correction Audit, ghi trong phiên "TASK-105B OWNER
CORRECTION: PRICE SOURCE IS FIREBASE RTDB". Chủ dự án ngắt phiên đang finalize
`TASK-105B-Q3` để sửa một tiền đề kiến trúc quan trọng chưa từng xuất hiện
trong repo.

Decision:

Đây là **bản ghi CONFLICT DETECTED + audit findings**, không phải một quyết
định nghiệp vụ đã đóng — vì repo hiện **không đủ thông tin** để agent tự thiết
kế giải pháp. Ghi lại để không mất tri thức này ở phiên sau.

**1. CONFLICT DETECTED.**

```
Documentation (authority hiện có):
    ADR-101 §Migration/Implementation Notes: "config/ là YAML ở Phase 1;
    Phase 2 chuyển vào DB" — DB nêu tên là PostgreSQL/SQLite (§Alternatives,
    §Rationale). Không nơi nào trong ADR-101, đặc tả gốc
    (docs/spec/Dac_ta_cong_cu_bao_cao_kinh_doanh.docx), hay bất kỳ ADR/DEC nào
    khác nhắc tới Firebase/RTDB như một thành phần kiến trúc của dự án.
    Hai chỗ DUY NHẤT chứa chữ "Firebase" trong toàn repo là
    `governance/product/13_ENVIRONMENT_CONFIGURATION.md` §9 và
    `governance/core/PROJECT_PROFILE_STANDARD.md` — cả hai là **boilerplate
    template chung của gói governance**, liệt kê Firebase như một VÍ DỤ loại
    dự án ("ứng dụng Firebase/Supabase"), không phải một quyết định kỹ thuật
    cho dự án cụ thể này.

Owner statement (phiên này):
    "Price Master của tôi KHÔNG tồn tại dưới dạng một file giá cố định. Giá
    nhập thay đổi liên tục trong ngày. Nguồn dữ liệu thực tế được cập nhật và
    đẩy lên Firebase Realtime Database (RTDB)... source of truth vận hành
    hiện tại là Firebase RTDB."

Risk:
    Nếu tiếp tục implement TASK-105B theo `DEC-145` (FilePriceProvider là
    implementation chính, source of truth) mà không sửa tiền đề này, công cụ
    sẽ đọc một bản chụp giá tĩnh trong khi giá thật đang biến động liên tục
    trên RTDB — đúng loại sai số mà DEC-103/125/126/143/144/145 tồn tại để
    chặn, chỉ khác là ở tầng kiến trúc thay vì tầng công thức.

Recommended resolution:
    Giữ nguyên `PriceProvider` Protocol (đã đúng, xem điểm 5). Thêm
    `RTDBPriceProvider` làm implementation SONG SONG với `FilePriceProvider`,
    không thay thế nó — vai trò của từng cái tuỳ vào câu trả lời cho điểm 3
    (historical lookup). Không tự chọn — cần Owner cung cấp schema RTDB thật
    (điểm 2) trước khi thiết kế được `RTDBPriceProvider` cụ thể.
```

**2. RTDB integration hiện tại trong repo: KHÔNG CÓ.**

Đã quét toàn repo (`grep -rli` không phân biệt hoa/thường, mọi phần mở rộng
`.md/.py/.yaml/.json/.js/.ts`), toàn bộ `docs/spec/*.docx` (trích XML gốc, kể
cả text không hiển thị dưới dạng backtick), và toàn bộ `pyproject.toml`
(dependencies: chỉ `openpyxl`, `PyYAML`, `pytest` — không có
`firebase-admin`, không có SDK Google Cloud nào). Không tìm thấy:

- credential file, `.env`, service account key nào (`find` cho
  `*credential*`/`*serviceaccount*`/`*firebase*`/`*.env*` = **rỗng**);
- RTDB path, schema, hay endpoint nào được ghi lại ở bất kỳ đâu;
- crawler/updater nào ghi giá vào RTDB được mô tả trong bất kỳ tài liệu nào.

⇒ **Không có gì để audit từ phía repo.** Toàn bộ điểm 2–3 của phiên này
(schema hiện tại; overwrite hay lưu history; timestamp/effective dating; khoá
sản phẩm; provenance; cơ chế crawler ghi dữ liệu) là **thông tin nằm ngoài
repo, chỉ Owner có** — session này không có credential, không có SDK, không
có cách kết nối RTDB để tự kiểm tra.

**3. Historical lookup khả thi hay không: KHÔNG XÁC ĐỊNH ĐƯỢC — cần Owner trả
lời trực tiếp, không suy đoán.**

Nhưng có một ràng buộc **đã có authority**, độc lập với RTDB, mà bất kỳ câu trả
lời nào cũng phải thoả: **DEC-121**. Nguyên văn: *"Việc tra cứu dùng ngày
nghiệp vụ của đơn / của kỳ báo cáo, không bao giờ dùng 'hôm nay'... Một chính
sách đổi vào 2027 không được phép làm thay đổi con số của một báo cáo 2026 đã
phát hành."* Nguyên tắc này áp dụng cho **mọi** business rule mang tính chính
sách trong dự án (tỉ lệ quy đổi đã kiểm chứng bằng `run_temporal_check()`,
3/3 PASS) — giá nhập không phải ngoại lệ, vì nó đi thẳng vào cùng công thức
lợi nhuận KPI.

**⇒ NẾU RTDB chỉ lưu giá hiện hành (bị ghi đè liên tục, không giữ lịch sử):
đây là BLOCKING ARCHITECTURE GAP cho `TASK-108B`.** Lý do cụ thể: chạy lại báo
cáo tháng 01/2026 vào một ngày bất kỳ sau đó phải cho ra **đúng** giá nhập của
tháng 01/2026, không phải giá tại thời điểm chạy lại — nếu không, in lại cùng
một báo cáo hai lần sẽ ra hai con số khác nhau, và không ai biết bản nào đúng
(đúng lo ngại DEC-121 đã nêu cho trường hợp tương tự). "RTDB đang chạy" không
tự động giải quyết được điều này; nó giải quyết bài toán khác ("giá hiện tại
là bao nhiêu ngay bây giờ"), không phải bài toán mà TASK-108B cần ("giá nhập
tại đúng ngày của đơn X trong quá khứ là bao nhiêu").

**4. Đề xuất abstraction — KHÔNG cần đổi seam đã có.**

`PriceProvider` Protocol (`app/modules/pricing/provider.py`, có từ TASK-105,
DEC-103) **đã đúng thiết kế cho tình huống này** — docstring của chính nó ghi
sẵn từ đầu: *"an interface is defined now so an external Price Master can be
plugged in later... without touching `price_engine` or `app.pipeline`."*
Không cần sửa Protocol, không cần sửa `apply_prices()`, không cần sửa
`pipeline.py`.

```
PriceProvider (Protocol, không đổi)
    ├── PendingPriceProvider      — mặc định Phase 1, GIỮ NGUYÊN
    │                                 (Golden Baseline phụ thuộc nó)
    ├── FilePriceProvider         — từ DEC-145, vai trò xem lại (điểm 6)
    └── RTDBPriceProvider (MỚI)   — implementation thứ ba, THIẾT KẾ SAU KHI
                                     có câu trả lời điểm 3
```

**Ràng buộc bắt buộc, không thương lượng:** `RTDBPriceProvider` phải nằm sau
đúng cùng một Protocol, và **không bao giờ** là default trong test/Golden.
Golden Baseline có nguyên tắc xuyên suốt: đầu ra phải **deterministic across
environments** (`test_golden_output_is_deterministic_across_environments`).
Một provider gọi mạng sống tới RTDB phá vỡ đúng nguyên tắc đó nếu vô tình trở
thành default ở bất kỳ đường chạy nào ngoài production thật — kể cả trong lúc
implement, không chỉ ở Golden.

Đây cũng là điểm giao với ADR-101: ADR-101 tuyên bố *"Toàn bộ Phase 1 là thư
viện Python thuần chạy được bằng CLI, không phụ thuộc DB hay web"* và cấm
`app/modules/` import bất kỳ thứ gì liên quan web. `RTDBPriceProvider` **chỉ**
tương thích với ranh giới đó nếu nó nằm hoàn toàn sau Protocol (client Firebase
là chi tiết implementation của module `pricing`, không rò rỉ lên
`price_engine`/`pipeline`/domain layer) — đúng thiết kế mà `PriceProvider` đã
có sẵn để làm việc này.

**5. `FilePriceProvider` (DEC-145) — vai trò xem lại, KHÔNG bị huỷ.**

Toàn bộ semantics đã Owner duyệt ở `DEC-145` (`OD-105B-01` §A/§B/§D/§E) — khoảng
hiệu lực đóng, cấm overlap, normalization NFC+casefold, 4-cột schema, validation
rules §E — **là tính chất của một tập hợp price record hợp lệ, độc lập với nơi
nó đến từ đâu**. Chúng KHÔNG bị đảo ngược bởi correction này.

Vai trò thực tế của file, chờ điểm 3 trả lời:

- Nếu RTDB **có** lưu lịch sử: `FilePriceProvider` lùi thành **bootstrap /
  import / snapshot export** — dùng để nạp dữ liệu ban đầu, hoặc để xuất một
  bản chụp RTDB ra file phục vụ audit/offline reconciliation, hoặc làm
  fixture cho test (deterministic, không phụ thuộc mạng — đúng yêu cầu Golden).
- Nếu RTDB **không** lưu lịch sử: cần một tầng **capture** đứng giữa RTDB
  (nguồn "hiện tại") và hệ thống báo cáo (cần "lịch sử") — file **có thể** là
  định dạng snapshot đó (mỗi lần chụp RTDB ghi thêm một dòng có
  `effective_from`/`effective_to`), nhưng đây là thiết kế mới, chưa được
  Owner xác nhận, và **không tự chọn**.

Cả hai nhánh đều **giữ nguyên giá trị** của `DEC-145`: 4-cột schema và
validation rules áp dụng cho snapshot/export, dù nguồn gốc dữ liệu bây giờ là
RTDB chứ không phải một file Owner gõ tay.

**6. `TASK-105B` implementation — TẠM DỪNG, không phải BLOCKED vĩnh viễn.**

`FilePriceProvider` **về mặt kỹ thuật vẫn implement được y hệt `DEC-145`** —
Protocol không đổi, schema không đổi. Nhưng gán nó làm **production path**
trước khi biết vai trò thật (điểm 5) là hành động dựa trên tiền đề sai mà Owner
vừa sửa. Đây không phải blocker kỹ thuật (`TASK-105B` cũ vẫn `READY` về mặt
code) — đây là quyết định **phạm vi/vai trò** cần Owner xác nhận trước khi
tiếp tục để tránh làm lại.

**7. Semantics Q1/Q2/Q3 — giữ nguyên nguyên vẹn, không phụ thuộc provider.**

- **Q1** (khoảng hiệu lực đóng, cấm overlap, cấm latest/nearest) — áp dụng cho
  bất kỳ tập price record nào, kể cả một snapshot từ RTDB. **Quan trọng hơn
  trước**: nếu RTDB không tự lưu lịch sử, chính Q1 là ràng buộc bắt buộc cho
  tầng capture phải xây.
- **Q2** (chuẩn hoá NFC+casefold cho khoá sản phẩm) — vẫn đúng **nếu** RTDB
  dùng cùng loại khoá text tự do (`product_raw`). Câu hỏi mới phát sinh: RTDB
  có thể đã dùng khoá có cấu trúc hơn (một dạng `ProductCode` thật) — nếu vậy,
  bài toán khớp tên mà TASK-402 (Phase 4) dự kiến giải quyết **có thể đã được
  giải một phần** bởi hệ thống nguồn giá. Cần Owner xác nhận khoá RTDB dùng gì.
- **Q3** (chính sách zero-price cho dòng phụ) — **hoàn toàn độc lập với
  provider**, không bị ảnh hưởng bởi correction này. Việc finalize `Q3` đang
  làm dở (audit evidence 30 raw label từ `evidence.json`, đã xác nhận đúng ba
  con số: `Chi phí vận chuyển` 1.074 dòng, `Chi phí lắp đặt` 84 dòng, `Chênh
  VAT` 33 dòng, cộng các biến thể ghép/typo) **không mất** — tạm dừng theo yêu
  cầu Owner, tiếp tục được ở phiên sau bằng đúng dữ liệu đã audit.

Reason:

**Vì sao đây không phải "chỉ cần đổi FilePriceProvider thành RTDBPriceProvider"
đơn giản.** Nếu RTDB chỉ có giá hiện hành, bài toán không phải "provider nào"
mà là "hệ thống hiện tại có khả năng trả lời câu hỏi lịch sử hay không" — một
câu hỏi kiến trúc, không phải một câu hỏi kỹ thuật nhỏ. Việc thu hẹp sai thành
"đổi provider" sẽ để lại đúng lỗi mà DEC-121 tồn tại để chặn, chỉ là ẩn sau một
lớp trừu tượng trông có vẻ đúng.

**Vì sao không tự thiết kế `RTDBPriceProvider` ngay trong phiên này.** Session
này không có credential, không có SDK, không có cách quan sát dữ liệu RTDB
thật. Thiết kế một provider mà không biết schema là đoán mò — đúng điều
`governance/core/10_AI_AGENT_EXECUTION_PROTOCOL.md`/`CLAUDE.md` cấm ("Không được thay các
trạng thái này chỉ vì prompt nói. Phải xác minh repo" — ở đây mở rộng thành
"phải xác minh hệ thống thật", không có trong repo thì không tự bịa).

**Vì sao vẫn giữ được toàn bộ `DEC-145`.** Owner correction này không nói
"Q1/Q2/Q3 sai" — nó nói "nguồn dữ liệu khác giả định". Ba câu hỏi đó là ràng
buộc lên **hình dạng của dữ liệu giá**, không phải lên **nơi nó tới từ đâu**.
Tách hai khái niệm này ra đúng là cách không phải làm lại discovery đã tốn
nhiều phiên.

Risk:

`Effective Risk = HIGH` giữ nguyên — không đổi so với `DEC-144`/`DEC-145`,
chấm theo data path (V4.1 §4): giá sai → `KpiPurchasePrice` sai →
`EligibleKpiProfit` sai → CR sai → KPI/lương sai. Correction này **làm rủi ro
kiến trúc hiện lên rõ hơn**, không làm nó thấp đi.

Rủi ro cụ thể của chính bản ghi này:

- **Live dependency rò vào test/Golden.** Nếu `RTDBPriceProvider` được thiết
  kế sau này vô tình trở thành import mặc định ở bất kỳ module test nào, mọi
  lần chạy `pytest` sẽ phụ thuộc mạng và trạng thái RTDB tại đúng thời điểm
  chạy — phá nguyên tắc deterministic của Golden Baseline. Giảm nhẹ: ghi tường
  minh ở điểm 4; `CHECK-105B-*` (khi viết lại Completion Gate) phải có một
  check riêng xác nhận không module test nào import client Firebase.
- **Nếu RTDB không lưu lịch sử và không ai xây tầng capture kịp thời**, dự án
  có nguy cơ lặp lại đúng việc workbook cũ đang làm (gõ tay/suy đoán) nhưng ở
  tầng giá thay vì tầng doanh thu quy đổi. Giảm nhẹ: nêu rõ đây là
  `BLOCKING ARCHITECTURE GAP` có điều kiện, cần Owner trả lời trước khi mở lại
  `TASK-105B` implementation.

Impact:
- `PROJECT/PROJECT_DECISIONS.md` — DEC này (ID cấp sau khi quét namespace toàn
  repo; `DEC-146` xác nhận trống).
- `PROJECT/PROJECT_PROGRESS.md` — `TASK-105B` lùi từ `IMPLEMENTATION = READY`
  về trạng thái tạm dừng chờ RTDB schema; `TASK-105B-Q3` finalize tạm dừng
  (không mất tiến độ audit).
- `PROJECT/LO_TRINH_DE_HIEU.md` — cập nhật mô tả bước 11b, thêm câu hỏi RTDB
  schema vào danh sách chờ chủ dự án.
- `PROJECT/REVIEW_BUDGET_LEDGER.md` — ghi chú trạng thái tạm dừng của lineage
  `TASK-105B`; **không** tiêu repair cycle (đây là audit, không phải repair).
- `docs/tasks/TASK-108B-eligible-costs-owner-definition.md` — Phần V
  (RTDB correction pointer), giữ nguyên Phần I–IV.
- **Không** sửa `app/**`, `config/**`, `tests/**`, Golden fixture/expected,
  `TASK-110`, `CHECK-110-16`, `R1-A1`, `governance/**`.

Can Revisit After:
- Chủ dự án cung cấp: schema RTDB thật (path, cấu trúc node, kiểu khoá sản
  phẩm); xác nhận RTDB overwrite hay lưu lịch sử; nếu lưu lịch sử, cấu trúc
  timestamp/effective dating; nếu không, xác nhận có đồng ý xây tầng capture
  snapshot hay không.
- Sau khi có câu trả lời trên: mở lại `TASK-105B` với kiến trúc đã sửa, hoặc mở
  một `TASK-105C` (RTDBPriceProvider / snapshot capture) riêng nếu độ phức tạp
  đủ lớn để tách task.

## DEC-147

Date:
2026-08-27

Task:
`TASK-105C` — Cross-Repo RTDB Price Source Audit. Ghi trong phiên
"TASK-105C — RTDB PRICE SOURCE DISCOVERY" (`docs/sessions/S024-task-105c-rtdb-price-source-audit.md`).
Trả lời trực tiếp năm câu hỏi mở tại `DEC-146` /
`docs/tasks/TASK-108B-eligible-costs-owner-definition.md` Phần V §49.

Repo được audit:
`hoangvinhkta-creator/Tracking` @ `d177363a390d36fe793e0c1c44a6fb6743ca45f5`.
Reports @ `cab8aa0026e2342ff8bbd42c272813088110c315`. Hai repo giữ độc lập —
không subtree, không submodule, không copy source, không merge history. Repo B
**không bị sửa** trong phiên này.

Decision:

Đây là **bản ghi audit findings**, không phải quyết định nghiệp vụ đã đóng.
Nó **đóng** bốn trong năm câu hỏi của §49 bằng bằng chứng code, và **mở** một
câu hỏi mới mà chỉ chủ dự án trả lời được.

**1. Điều kiện `BLOCKING ARCHITECTURE GAP` của `DEC-146` §3: KHÔNG KÍCH HOẠT.**

`DEC-146` §3 đặt điều kiện: *"NẾU RTDB chỉ lưu giá hiện hành (bị ghi đè liên
tục, không giữ lịch sử) → BLOCKING ARCHITECTURE GAP."* Tiền đề đó **sai** với
hệ thống thật.

RTDB đang chạy ở chế độ **HYBRID (kết luận C của Phần 4 đề bài)**:

```
board/<mã>/p/<NCC>   = ảnh chụp HIỆN HÀNH, bị ghi đè mỗi lượt cập nhật
phist/<mã>/<NCC>/<YYYY-MM-DD> = LỊCH SỬ, append theo ngày, chỉ ghi khi giá ĐỔI
```

Bằng chứng: `public/index.html:6162-6163` (chú thích cấu trúc),
`BAO-MAT-TRIEN-KHAI.md:368-383` (tài liệu vận hành), ba đường ghi tại
`public/index.html:5171`, `:5192`, `:6415`, `:8416`, hàm ghi `savePhist()`
`:4645` dùng `db.ref("phist").update(...)` (append từng khoá, **không** đè
nhánh cha).

**2. NHƯNG: SOURCE MISMATCH. Loại giá có lịch sử không phải giá nhập kế toán.**

Đây là kết luận trọng yếu nhất của phiên, và nó **không nằm trong hai nhánh mà
`DEC-146` dự trù**. Repo B mang **ba** loại giá khác nhau về bản chất:

| Trường RTDB | Nghĩa thật (theo chú thích trong chính repo B) | Có lịch sử? |
|---|---|---|
| `phist/<mã>/<NCC>/<ngày>` và `board/<mã>/p/<NCC>/v` | **Giá NCC báo** — con số nhà cung cấp gửi trong bảng giá dán hằng ngày | **CÓ**, theo ngày |
| `inv.<cu\|moi>.gia[<khoá tên hàng>]` | **Giá thực nhập trung bình** — bình quân gia quyền của hàng đang nằm trong kho | **KHÔNG** |
| `inv.<cu\|moi>.lo[<khoá tên hàng>]` | **Giá lô** — giá thực trả cho phần hàng tăng thêm hôm nay, nhân viên gõ tay | **KHÔNG** |
| `board/<mã>/tp/ton` | **Giá nhập công khai** — bản phái sinh của `gia`, đẩy sang bảng cho nhân viên xem | **KHÔNG** |
| `board/<mã>/tp/chot` | **Giá chốt TP** — giá bán nội bộ, nhân viên tự chốt | KHÔNG |
| `board/<mã>/_c.min` | **Min** — rẻ nhất trong (NCC còn hàng ∪ giá kho); repo B gọi là *"giá vốn rẻ nhất bán ra được"* | KHÔNG (dẫn xuất) |
| `board/<mã>/_c.dx` | **Giá đề xuất** = `chot + bien`; giá **BÁN** gợi ý | KHÔNG (dẫn xuất) |

Bằng chứng ngữ nghĩa: `public/index.html:6687-6690` phân biệt ba lớp giá bằng
đúng chữ *"giá **thực nhập** trung bình"* / *"giá thực nhập của phần tăng"* /
*"giá nhập **công khai**"*; `public/index.html:7248-7250` nói thẳng *"Chỉ GIÁ
CÔNG KHAI đi sang cột Tồn/Min. Giá thực nhập trung bình ở lại tab Tồn kho"*;
`price-engine/src/nghiepvu.js:601-607` định nghĩa Min.

⇒ **Giá NCC báo ≠ giá nhập kế toán.** Nó là **báo giá của một nhà cung cấp
trong ngày**, không phải số tiền đã trả cho lô hàng bán ra ở đơn X. Ba khác
biệt cụ thể, không phải chi li câu chữ:

- Một mã có **nhiều** giá NCC cùng một ngày (mỗi NCC một cột). Không có gì
  trong RTDB nói đơn hàng X đã mua của NCC nào.
- Hàng bán hôm nay có thể là hàng **đã nằm trong kho** từ trước, mua theo giá
  cũ. `price-engine/src/nghiepvu.js:603-606` nói rõ đây là tình huống thật và
  thường xuyên (*"Hàng trong kho mua được rẻ hơn giá NCC hôm nay là lợi thế
  cạnh tranh có thật"*).
- Giá NCC là **báo giá**, chưa trừ chiết khấu/điều chỉnh thực tế của lô.

**Nếu áp thẳng `phist` làm `AccountingPurchasePrice` thì đó chính là hành vi mà
đề bài mục 7 và `OD-105B-01` §D cấm: lấy một trường tên `price` rồi mặc định nó
là giá nhập.**

**3. Historical Replay Test — kết quả có điều kiện.**

Bài kiểm của đề bài (giá 8.000.000 ngày 01/01, đổi 8.200.000 ngày 15/01, hỏi
lại vào tháng sau):

```
price(product, 2026-01-10)  → phist/<mã>/<NCC>/2026-01-01 = 8000   (đơn vị nghìn)
price(product, 2026-01-20)  → phist/<mã>/<NCC>/2026-01-15 = 8200
```

**YES — về mặt cấu trúc, cho GIÁ NCC BÁO.** Quy tắc tra: lấy mốc `<ngày>` lớn
nhất còn `≤ sale_date` trong `phist/<mã>/<NCC>`. Đây đúng là ngữ nghĩa hàm bậc
thang mà tài liệu repo B mô tả: *"Ngày để trống trong bảng nghĩa là NCC đó giữ
nguyên giá của mốc gần nhất phía trên"* (`BAO-MAT-TRIEN-KHAI.md:379-381`), và
nó khớp **chính xác** khoảng hiệu lực đóng của `DEC-145` §1 — mỗi mốc là
`effective_from`, `effective_to` = ngày trước mốc kế tiếp.

**NO — cho `AccountingPurchasePrice`**, vì trường mang nghĩa đó
(`inv.<slot>.gia` / `.lo`) không có lịch sử: nhánh `inv` chỉ giữ hai ô cuốn
chiếu `cu`/`moi` và được ghi bằng `db.ref("inv").set(INV)` — đè **cả nhánh**
(`public/index.html:6831-6835`). Ảnh chụp `backup/` chỉ chứa `board` + `meta`,
**không** chứa `inv` (`public/index.html:4670-4676`).

Năm điều kiện phải kèm theo chữ YES ở trên, không được bỏ:

- **R1 — Độ mịn chỉ tới NGÀY.** Hai lần đổi giá trong cùng một ngày ghi đè lên
  cùng một khoá lá; giá cuối ngày thắng. Chủ dự án đã nói *"giá nhập thay đổi
  liên tục trong ngày"* — phần biến động trong ngày **mất**. Với báo cáo tính
  theo ngày nghiệp vụ thì chấp nhận được, nhưng phải ghi nhận, không được coi
  như không có.
- **R2 — `0` là sentinel HẾT HÀNG, không phải giá.** `public/index.html:5192`:
  `ph[...] = 0; // 0 = hết hàng, giá thật không bao giờ bằng 0`. Bên Reports,
  `DEC-145` §5 cấm dùng `0` thay cho missing. Ánh xạ **bắt buộc**:
  `phist == 0` → **gap** → `lookup = None` → `Pending`. Đọc nhầm `0` thành giá
  là biến một mã hết hàng thành lợi nhuận KPI bằng đúng giá bán.
- **R3 — Không có mốc trước ngày bật tính năng.** `phist` chỉ có từ bản dựng
  `b59` trở đi, cộng một mốc khởi đầu do lần nhập file Excel gần nhất sinh ra
  (`public/index.html:8414-8416`). `sale_date` trước đó → không có dữ liệu →
  `Pending`. Ngày bắt đầu thật **chưa xác định** (xem Risk).
- **R4 — Lịch sử SỬA ĐƯỢC, và có bốn đường sửa đang chạy.** `xoaPhistSau()`
  (`:4870-4882`) xoá mọi mốc từ một ngày trở đi; đổi mã (`:4570-4573`) dời cả
  cây `phist` sang khoá mới rồi `remove()` khoá cũ; gộp mã `mergePaths()`
  (`:4301-4325`) gộp dòng `board` **nhưng không đụng `phist`** ⇒ lịch sử mồ
  côi dưới khoá đã biến mất; khôi phục cả bảng `doRestore()` (`:4755`) ghi đè
  `board` **nhưng không đụng `phist`** ⇒ hai nhánh lệch nhau. Rules cho phép
  bất kỳ tài khoản `admin`/`bedit`/`edit` nào làm những việc đó.
  ⇒ **`phist` là sổ có thể sửa, không phải sổ bất biến.** In lại cùng một báo
  cáo hai lần vẫn có thể ra hai số — đúng điều `DEC-121` tồn tại để chặn — trừ
  khi Reports **tự chụp và đóng băng** dữ liệu đã dùng.
- **R5 — Không có đường đọc nào.** Không API, không export nào của repo B đưa
  `phist` ra ngoài. `/api/board.csv` chỉ xuất ảnh chụp hiện hành, không ngày
  (`src/index.js:403-470`). Người đọc `phist` duy nhất hiện nay là giao diện
  trình duyệt (`loadPhist()` `:4661`).

**4. Khoá sản phẩm — cần MAPPING, không khớp trực tiếp.**

```
Khoá RTDB : normCode(mã) = toUpperCase() + bỏ mọi ký tự ngoài [A-Z0-9]
            rồi qua aliasOf() để gom các cách viết đã xác nhận trùng
            ví dụ  "SJ-X198V-DG"  →  "SJX198VDG"
Reports   : product_raw = Tên hàng trên chứng từ (cả câu tiếng Việt)
            ví dụ  "Cây nước Kangaroo KG36A2"
```

| RTDB KEY | REPORTS FIELD | MATCH DIRECTLY? | MAPPING REQUIRED? | COLLISION RISK? |
|---|---|---|---|---|
| `board/<MÃ>` (khoá nút) | `product_raw` | **KHÔNG** | **CÓ** — phải rút mã model ra khỏi câu tên hàng | **CÓ** — `normCode` bỏ hết dấu phân cách: hai mã chỉ khác nhau ở gạch nối/khoảng trắng gộp thành một |
| `board/<MÃ>/name` | `product_raw` | KHÔNG | CÓ | Trung bình — `name` là mã người đọc (`SJ-X198V-DG`), vẫn không phải câu tên hàng |
| `board/<MÃ>/alt` | — | — | — | Danh sách cách viết đã gộp; hữu ích cho mapping |
| `inv.map` (`N_<normCode(tên hàng)>` → `<MÃ>`) | `product_raw` | **GẦN** | CÓ (đối chiếu nguồn tên) | Thấp — bảng do **người** duyệt |
| `alias.map` (`<mã cũ>` → `<mã chính>`) | — | — | — | Bảng gom mã trùng, do người duyệt |

Hai hệ quả:

- **RTDB ĐÃ CÓ mã sản phẩm ổn định** (`normCode` + `alias`). Đây là câu trả
  lời cho §49 mục 3 và cho ghi chú của `DEC-146` §7 Q2: *bài toán `TASK-402`
  đã được giải một phần* — nhưng **ở phía mã**, không ở phía **tên trên chứng
  từ**. Khoảng cách còn lại đúng bằng "câu tên hàng → mã model".
- **Repo B đã thử giải khoảng cách đó bằng máy và ĐÃ BỎ.** `extractCode()`
  (`public/index.html:8908-8915`) rút mã bằng "token cuối cùng có chứa số";
  chú thích tại `:6699-6703` viết: *"Đó là ĐOÁN CHỮ, không hề đối chiếu bảng
  giá — nên có lúc ra đúng mã, có lúc ra '251lít', 'LG', 'Tivi'. Số liệu này đi
  thẳng vào tài sản thật nên không được đoán: đã bỏ hẳn."* Thay bằng bảng
  `inv.map` **người dùng chỉ đích danh từng dòng**.
  ⇒ Đây là **tiền lệ có thật, trên đúng loại dữ liệu này, ở đúng công ty này**,
  ủng hộ nguyên tắc `OD-105B-01` §B (cấm fuzzy/nearest/AI matching). Reports
  **không** được phát minh lại `extractCode`.

**`DEC-145` §2 KHÔNG đổi trong phiên này.** Chuẩn hoá NFC→casefold vẫn là luật
cho khoá dạng text. Việc có chuyển sang khoá bằng mã hay không là quyết định
riêng, cần task riêng.

**5. Write semantics — trả lời mục 8 của đề bài.**

```
overwrite node cũ?     board: CÓ (update theo đường dẫn lá; ghi đè ô giá cũ)
                       inv:   CÓ, đè CẢ NHÁNH (set)
                       phist: KHÔNG với mốc khác ngày; CÓ trong cùng một ngày
append record?         CÓ — phist, một lá mỗi (mã, NCC, ngày)
push()?                Chỉ ở `dnhap` (yêu cầu đăng nhập thiết bị). KHÔNG ở giá
transaction?           KHÔNG dùng ở bất kỳ đường ghi giá nào
có timestamp?          CÓ, nhưng dạng chuỗi tự đặt, không phải kiểu thời gian
client hay server?     100% CLIENT — grep "ServerValue|serverTimestamp" = 0 hit
                       trên public/index.html và src/*.js
có source?             KHÔNG trên bản ghi giá
có actor/provider?     `NCC` có trong khoá phist. Người ghi: KHÔNG
có previous value?     CÓ, đúng MỘT bước, chỉ ở ảnh chụp (`p/<NCC>/pv`)
có audit trail?        CÓ nhưng yếu: `hist`, toàn cục, TỐI ĐA 100 dòng, ghi
                       bằng set() đè cả nhánh, mọi hồ sơ nhân viên đều ghi được
có deletion?           CÓ — bốn đường, xem R4 ở điểm 3
```

Chi tiết timestamp: `board/<mã>/p/<NCC>` mang `d` (ngày cập nhật), `f` (ngày
NCC đó báo giá lần đầu), `gd` (ngày đánh dấu hết hàng) — cả ba là
`todayStr() = new Date().toLocaleDateString("vi-VN")`, tức **`D/M/YYYY`, không
phải ISO, theo múi giờ và đồng hồ của máy nhân viên đang dán giá**
(`public/index.html:8864`). Khoá ngày của `phist` là `dayKey()` → `YYYY-MM-DD`,
cũng từ đồng hồ client (`:4640-4644`).

**6. Đơn vị tiền — KHÔNG khớp `ADR-103`, phải chuyển ở đúng biên.**

RTDB lưu giá theo **NGHÌN đồng**: `src/index.js:154-158` — *"Bảng giá của app
lưu theo NGHÌN (5200)"*; `public/index.html:6761-6764` — *"Giá tồn được lưu
theo đơn vị NGHÌN đồng (5.000 = 5 triệu)"*; báo cáo in *"Đơn vị: nghìn đồng
(K)"* (`:9163`). Reports lưu **VND nguyên, `Decimal`** (`ADR-103` §1).

`ADR-103` §2 nói thẳng: *"Không engine nào biết tới khái niệm 'nghìn đồng'.
Không có phép nhân hay chia 1.000 nào nằm ngoài `importing/` và `reporting/`."*
⇒ Một `RTDBPriceProvider` đặt trong `app/modules/pricing/` mà tự nhân 1.000 là
**vi phạm `ADR-103` §2**. Phép nhân đó phải nằm ở tầng nhập liệu/capture, không
nằm trong provider.

Hai hệ quả nữa cùng loại:

- RTDB trả **số JSON (float64)**. `ADR-103` §1 **cấm `float` cho tiền**. Bất kỳ
  đường nhập nào cũng phải qua `to_decimal()` (`app/modules/domain/money.py`),
  và phải phân biệt ô trống với `0` — đúng cảnh báo `DEC-145` Risk.
- `inv.gia` đã bị **làm tròn LÊN bội 10 ở đơn vị nghìn** ngay tại nguồn
  (`invRoundAvg` `public/index.html:6764`) ⇒ sai số tới **10.000 VND/đơn vị**
  đã nằm sẵn trong dữ liệu, Reports không gỡ lại được.

**7. Security — KHÔNG có BLOCKING finding.**

```
credential trong repo B          : KHÔNG (grep private_key/client_secret/
                                   serviceAccount trên .js/.html/.json/.toml = 0)
service account                  : Cloudflare Secret FB_SA_EMAIL/FB_SA_KEY,
                                   JWT RS256 ký bằng WebCrypto (src/firebase.js)
database rules                   : CÓ, gốc .read=false/.write=false
public read/write                : KHÔNG — không nhánh nào cho auth == null
App Check                        : Enforce, bật 13/08/2026
```

Khoá web Firebase (`apiKey`, `appId`…) **có** nằm trong `public/index.html:2457-2462`
— đây là **cấu hình công khai theo thiết kế** của Firebase, đi tới mọi trình
duyệt dù có commit hay không, và chính repo B ghi rõ điều đó ở `:2464-2467`.
**Không phải credential exposure.** Không in giá trị nào của secret trong báo
cáo này.

Ba mục **HARDENING** (thuộc repo B, **ngoài phạm vi** sửa của Reports — ghi để
chủ dự án biết, không phải việc của phiên này):

- `hist` (nhật ký) cho **mọi** hồ sơ nhân viên quyền ghi
  (`firebase-database.rules.json`, nhánh `hist`), và client ghi bằng
  `db.ref("hist").set(<mảng 100 phần tử>)` ⇒ một nhân viên bất kỳ xoá/viết lại
  được nhật ký. Nhật ký như vậy không đứng được làm bằng chứng kế toán.
- `phist` sửa/xoá được bởi mọi tài khoản `admin`/`bedit`/`edit`, và có bốn
  đường sửa đang chạy (R4). Sổ giá lịch sử **không bất biến**.
- Nếu Reports đọc thẳng RTDB, nó cần một service account key trong môi trường
  triển khai của mình — một mặt phẳng quản lý bí mật **mới**, hiện chưa tồn tại
  trong Reports (`pyproject.toml` không có SDK Google/Firebase nào).

**8. Kiến trúc đề xuất — đánh giá năm option.**

| Option | Pros | Cons | Migration | Data integrity | Historical replay | Chi phí vận hành | Hợp `TASK-108B`? |
|---|---|---|---|---|---|---|---|
| **A** — `RTDBPriceProvider` đọc thẳng `phist` | Không phải xây gì mới ở repo B; dữ liệu tươi nhất | Đọc **giá NCC**, không phải giá nhập kế toán; kéo mạng vào `app/modules/` (va `ADR-101`); ×1.000 trong tầng pricing (va `ADR-103` §2); cần service account trong Reports; `phist` sửa được nên không tái lập được báo cáo cũ | Vừa (client + secret) | **Yếu** — nguồn mutable, không đóng băng | Có (bậc thang), nhưng số **sai loại** | Thấp | **KHÔNG** — sai loại giá |
| **B** — Giữ ảnh chụp RTDB + thêm `price_history` trong RTDB | Lịch sử ở gần nguồn | `phist` **đã tồn tại** cho giá NCC ⇒ B chỉ có nghĩa nếu thêm lịch sử cho **giá nhập kế toán**, tức sửa production repo B; vẫn không giải quyết mutability | Cao — đổi schema production | Trung bình | Có, sau khi xây | Trung bình | Có, sau khi xây |
| **C** — Capture service ghi price history **bất biến** riêng | Tách nguồn vận hành khỏi sổ kế toán; append-only, đóng băng được; chọn được đúng trường giá; đặt được `effective_from/to` theo `DEC-145` §1 | Phải xây và phải chạy đều; capture sót ngày là thủng dữ liệu | Trung bình | **Mạnh nhất** | **Có, và ổn định qua thời gian** | Trung bình | **CÓ** |
| **D** — Xuất snapshot/file định kỳ làm nguồn giá kế toán | Đúng y hợp đồng 4 cột `DEC-145` §4; deterministic — hợp Golden; **không** mạng trong `app/modules/`; đổi 1.000 nằm ở biên nhập | Chỉ là **định dạng giao hàng**, tự nó không tạo ra lịch sử nếu nguồn không có | Thấp | Mạnh (file bất biến, version được) | Có, nếu dữ liệu bên trong có | Thấp | **CÓ** |
| **E** — RTDB không phù hợp làm nguồn | — | Sai: RTDB **có** dữ liệu gốc, chỉ sai hình dạng/ngữ nghĩa | — | — | — | — | — |

**RECOMMENDED OPTION: C, giao hàng bằng định dạng của D.**

```
repo B / RTDB  ──(capture định kỳ, chọn ĐÚNG trường giá)──►  price history
                                                             bất biến, 4 cột
                                                                   │
                                          FilePriceProvider (DEC-145 §4/§5)
                                                                   ▼
                                                        Reports  PriceProvider
```

Vì sao C+D chứ không phải A:

- Trường **có** lịch sử (giá NCC) **không phải** trường Reports cần; trường
  Reports cần (giá thực nhập) **không có** lịch sử. Không option đọc-thẳng nào
  vượt qua được sự thật đó.
- `phist` sửa được (R4). `DEC-121` đòi báo cáo đã phát hành không đổi số. Chỉ
  một bản ghi **bất biến, đóng băng** mới thoả — dù nguồn có lịch sử.
- C+D giữ nguyên ranh giới `ADR-101` (không mạng trong `app/modules/`),
  `ADR-103` §2 (đổi đơn vị ở biên nhập), và tính deterministic của Golden —
  cả ba đều là ràng buộc đã có authority, không phải sở thích.
- Hai repo chỉ giao tiếp qua **data contract**, đúng mục 10 của đề bài. Không
  bên nào import bên nào.

**Đường nhanh, có điều kiện:** nếu chủ dự án xác nhận *"giá nhập = giá NCC báo
trong ngày"*, thì một job **D thuần** — đọc `phist` rồi xuất ra file 4 cột —
đủ dùng ngay, **không cần sửa một dòng nào của repo B**. Rẻ hơn hẳn. Nhưng nó
đòi đúng một quyết định của chủ dự án, và phiên này **không tự quyết**.

**9. Ranh giới hai repo — giữ nguyên.**

Không tạo phụ thuộc code hai chiều. `Reports` không import `Tracking`;
`Tracking` không import `Reports`. Giao tiếp bằng data contract
(file 4 cột `DEC-145` §4, hoặc một endpoint đọc-only nếu sau này cần). Phiên
này không thực hiện thay đổi nào ở repo B.

**10. Trạng thái sau audit.**

```
FilePriceProvider   = KEEP — và ĐƯỢC ĐỀ CỬ làm production path (đảo lại nghi
                      vấn của DEC-146 §6), vì kiến trúc khuyến nghị là C+D.
                      Contract kỹ thuật DEC-145 §4/§5 giữ nguyên 100%.

RTDBPriceProvider   = NEEDS_SCHEMA_CHANGE, và KHÔNG được đề cử.
                      "Schema change" ở đây KHÔNG phải "RTDB thiếu lịch sử" —
                      mà là "trường giá kế toán không có lịch sử, và sổ lịch
                      sử đang có thì sửa được". Đọc thẳng vẫn thêm hai vi phạm
                      ranh giới (ADR-101 mạng, ADR-103 §2 đơn vị).

TASK-105B           = READY (implementation) về mặt kỹ thuật — gỡ trạng thái
                      "TẠM DỪNG" của DEC-146 §6 ở phần *khả thi*. Nhưng vẫn
                      BLOCKED_BY [ chủ dự án chốt trường nào là
                      AccountingPurchasePrice ] trước khi có dữ liệu để nạp.

TASK-105C           = DISCOVERY_COMPLETE.
                      IMPLEMENTATION = OWNER_DECISION_REQUIRED
                      (câu hỏi ở Reason điểm cuối). KHÔNG mở implementation.

TASK-105B-Q3        = KHÔNG ĐỔI — vẫn BLOCKED_BY [TASK-103 / enumeration].
                      Độc lập hoàn toàn với nguồn giá, đúng như DEC-146 §7.
                      Audit evidence 30 raw label KHÔNG mất.

TASK-108B           = BLOCKED_BY [ 1. chủ dự án chốt trường
                      AccountingPurchasePrice; 2. tầng capture/export chưa
                      tồn tại; 3. TASK-105B-Q3 (dòng phụ) ]
                      — BỎ blocker cũ "chưa xác định kiến trúc RTDB".
```

Reason:

**1. Vì sao không dừng ở "RTDB có lịch sử ⇒ hết blocker".**
`DEC-146` đặt câu hỏi nhị phân (có lịch sử / không có lịch sử) và gán sẵn kết
luận cho mỗi nhánh. Hệ thống thật không rơi vào nhánh nào: nó **có** lịch sử,
nhưng cho một **loại giá khác**. Trả lời "CÓ" rồi mở khoá `TASK-108B` là đúng
chữ mà sai việc — và sai theo đúng kiểu `DEC-103`/`DEC-125`/`DEC-143` tồn tại
để chặn: một con số có mặt, trông hợp lý, ở sai chỗ.

**2. Vì sao bảng ba loại giá là bằng chứng chứ không phải diễn giải.**
Chú thích trong repo B phân biệt chúng bằng chính chữ "thực nhập" / "công
khai", và **thi hành** sự phân biệt đó bằng code: `invSyncPart()`
(`public/index.html:7248-7250`) cố ý chỉ đẩy `cong` sang bảng giá và **giữ
`gia` lại**. Đây là một quyết định thiết kế đã có chủ đích ở phía nguồn, không
phải một chi tiết ngẫu nhiên.

**3. Vì sao `extractCode` bị bỏ ở repo B là bằng chứng đáng dùng cho Reports.**
Đó không phải ý kiến; đó là một hệ thống production, trên đúng danh mục hàng
này, đã thử ánh xạ tên→mã bằng máy, thấy sai, và thay bằng bảng người duyệt —
với lý do ghi thẳng trong mã: *"Số liệu này đi thẳng vào tài sản thật nên không
được đoán"*. `OD-105B-01` §B cấm fuzzy matching vì cùng một lý do. Hai bên độc
lập đi tới cùng kết luận là bằng chứng mạnh hơn một bên tự khẳng định.

**4. Vì sao mutability là vấn đề riêng, tách khỏi câu hỏi có/không lịch sử.**
`DEC-121` không đòi "hệ thống có lưu lịch sử", nó đòi *"một báo cáo 2026 đã
phát hành không được đổi số"*. Một sổ lịch sử mà mọi tài khoản `edit` xoá được
theo ngày (`xoaPhistSau`) thoả vế đầu mà không thoả vế sau. Đây chính là lý do
khuyến nghị C (bản ghi bất biến) chứ không phải A (đọc thẳng), kể cả trong
kịch bản chủ dự án chốt "giá nhập = giá NCC".

**5. Vì sao `FilePriceProvider` được đề cử trở lại làm production path.**
`DEC-146` §6 rút vai trò production của nó **vì chưa biết nguồn thật**. Nay
biết: nguồn thật cần một tầng capture ở giữa, và đầu ra của tầng đó là một tập
price record 4 cột — đúng thứ `FilePriceProvider` đọc. `DEC-146` §5 đã dự trù
chính xác nhánh này (*"file CÓ THỂ là định dạng snapshot đó"*). Không có gì
của `DEC-145` phải làm lại.

**Câu hỏi còn lại — chỉ chủ dự án trả lời được (thay §49 mục 1–5):**

Bốn trong năm câu hỏi cũ đã đóng bằng code (schema; có lưu lịch sử; khoá sản
phẩm; provenance). Câu hỏi thật còn lại **không phải** câu hỏi cũ số 5:

1. **`AccountingPurchasePrice` là trường nào?** Ba ứng viên, khác nhau về bản
   chất, không thể suy ra từ dữ liệu:
   (a) **giá NCC báo trong ngày** (`phist` — có lịch sử sẵn, rẻ nhất để làm,
   nhưng là *báo giá*, không phải tiền đã trả, và một mã có nhiều NCC cùng
   ngày);
   (b) **giá thực nhập trung bình** (`inv.<slot>.gia` — bình quân gia quyền
   của hàng trong kho, gần nghĩa kế toán nhất, **chưa có lịch sử**, đã làm
   tròn ±10.000 VND);
   (c) **giá lô** (`inv.<slot>.lo` — tiền thật của lần nhập, đúng nghĩa nhất,
   **chưa có lịch sử**, và không nối được với đơn bán cụ thể).
2. Nếu chọn (a): khi một mã có **nhiều NCC** cùng ngày, lấy NCC nào? (rẻ nhất?
   NCC đã thực mua? một NCC cố định?) — RTDB **không** chứa thông tin "đơn X
   mua của NCC nào".
3. Chấp nhận **độ mịn theo ngày** (mất biến động trong ngày) hay không?
4. Đồng ý xây tầng **capture bất biến** (khuyến nghị C) không, và tần suất bao
   nhiêu?
5. Trước khi có capture, dữ liệu lịch sử **có sẵn từ ngày nào**? — cần một
   lượt đọc RTDB thật; repo không trả lời được (git shallow, mốc `b59` nằm
   trước mốc cắt).

Risk:

`Effective Risk = HIGH` — **không đổi**, chấm theo data path (V4.1 §4):
`Price sai → KpiPurchasePrice sai → EligibleKpiProfit sai → CR sai → KPI/lương
sai`. Audit này làm rủi ro **rõ hơn**, không làm nó thấp đi: nó cho thấy tồn
tại một nguồn dữ liệu **trông đúng và dễ lấy** (`phist`) mà dùng vào là sai.

Rủi ro cụ thể của chính bản ghi này:

- **Đọc tắt thành "RTDB có lịch sử ⇒ xong".** Đây là rủi ro số một. Giảm nhẹ:
  điểm 2 và điểm 10 nói thẳng `SOURCE MISMATCH`; mọi trạng thái vẫn
  `BLOCKED_BY` chủ dự án.
- **`0` bị đọc thành giá.** `phist == 0` nghĩa là hết hàng. Nhầm một lần là một
  dòng lãi bằng đúng giá bán. Giảm nhẹ: R2 ghi tường minh; bất kỳ
  `TASK-105C`/capture nào cũng phải có check riêng cho việc này.
- **Đơn vị nghìn bị bỏ quên.** Sai đúng 1.000 lần, và sai *đều* nên nhìn bảng
  không phát hiện được. Giảm nhẹ: điểm 6; `ADR-103` §2 buộc phép nhân nằm ở
  biên nhập, nơi có thể đặt check.
- **Khẳng định về dữ liệu sống bị coi là đã kiểm chứng.** Phiên này audit
  **code**, không đọc instance. `N-01 = NOT_TESTED`. Giảm nhẹ: mục "Giới hạn
  của bằng chứng" trong `S024`.
- **Provider gọi mạng rò vào test/Golden.** Rủi ro `DEC-146` đã nêu vẫn nguyên
  giá trị, và khuyến nghị C+D làm nó **nhỏ đi** (file deterministic, không
  mạng). Nếu sau này vẫn làm option A, check của `CHECK-105C-*` phải xác nhận
  không module test nào import client Firebase.

Impact:
- `PROJECT/PROJECT_DECISIONS.md` — DEC này (ID cấp sau khi quét namespace toàn
  repo; `DEC-147` xác nhận trống).
- `PROJECT/PROJECT_PROGRESS.md` — `TASK-105B` gỡ "TẠM DỪNG", đổi blocker;
  `TASK-105C` = `DISCOVERY_COMPLETE` / `OWNER_DECISION_REQUIRED`; `TASK-108B`
  đổi danh sách blocker.
- `PROJECT/LO_TRINH_DE_HIEU.md` — bước 11b; thay khối 5 câu hỏi cũ bằng 5 câu
  hỏi mới.
- `PROJECT/REVIEW_BUDGET_LEDGER.md` — mục nhật ký; **không** tiêu repair cycle
  (đây là audit, không phải repair — cùng lệ `DEC-146`).
- `docs/tasks/TASK-108B-eligible-costs-owner-definition.md` — Phần VI; giữ
  nguyên Phần I–V.
- `docs/sessions/S024-task-105c-rtdb-price-source-audit.md` — bàn giao phiên.
- **Không** sửa `app/**`, `config/**`, `tests/**`, Golden fixture/expected,
  `TASK-110`, `CHECK-110-16`, `R1-A1`, `governance/**`.
- **Không** sửa repo B (`Tracking`) — 0 file.

Can Revisit After:
- Chủ dự án trả lời 5 câu hỏi ở cuối phần Reason ⇒ mở `TASK-105C`
  implementation (kèm `docs/tasks/TASK-105C-*.md` với Scope Lock +
  Completion Gate), hoặc mở lại `TASK-105B` nếu chọn đường D thuần.
- Một lượt đọc RTDB thật (có credential) ⇒ nâng `N-01` từ `NOT_TESTED` lên E1
  và chốt ngày bắt đầu có dữ liệu lịch sử.
- `TASK-103` hoặc danh sách enumerated ⇒ mở `TASK-105B-Q3` (độc lập, không
  liên quan phiên này).

## DEC-148

Date:
2026-08-27

Task:
`TASK-105C` — Public Purchase Price History Check. Ghi trong phiên
"TASK-105C — PUBLIC PURCHASE PRICE HISTORY CHECK"
(`docs/sessions/S025-task-105c-public-purchase-price-cong-audit.md`). Trả lời
trực tiếp yêu cầu của chủ dự án sau `DEC-147`: chủ dự án chỉ định
`inv.cong` (giá nhập **công khai**), không phải `inv.gia` (giá thực nhập
private), làm ứng viên cho `AccountingPurchasePrice`.

Repo được audit:
`hoangvinhkta-creator/Tracking` @ `d177363a390d36fe793e0c1c44a6fb6743ca45f5`
(không đổi so với `DEC-147`). **0 file thay đổi** trong phiên này.

Decision:

Đây là **bản ghi audit findings**, tiếp nối `DEC-147`, không thay thế nó.
Xác nhận bốn semantics chủ dự án đề xuất bằng bằng chứng code, và bổ sung một
finding mới — **quan trọng hơn** bản thân câu hỏi field-selection.

**1. Xác nhận bốn semantics — CẢ BỐN KHỚP với code.**

```
AccountingPurchasePrice = inv.cong         ✅ — cong là giá trị DUY NHẤT của
                                               ba lớp giá (gia/lo/cong) từng
                                               rời khỏi nhánh `inv` để đi vào
                                               `board`, và qua đó vào
                                               `/api/board.csv` và mọi màn
                                               hình Reports có thể đọc được.
inv.gia = PRIVATE / OUT OF REPORTS SCOPE   ✅ — chỉ dùng nội bộ cho báo cáo
                                               "Giá trị tồn kho" (`invValRows`,
                                               `public/index.html:7554` dùng
                                               `invGiaOf()`) — báo cáo này
                                               không ghi ra `board`, không qua
                                               CSV, không có route API nào.
inv.lo = LOT PRICE / NOT USED BY DEFAULT   ✅ — `lo` chỉ là INPUT để tính
                                               `gia` (bình quân gia quyền,
                                               `invRecalcAvg()`
                                               `:7089-7096`); bản thân `lo`
                                               không đi tới `board`, không đi
                                               tới `cong` trực tiếp (chỉ đi
                                               gián tiếp qua `gia`).
phist = VENDOR QUOTED / NOT ACCOUNTING     ✅ — xác nhận lại `DEC-147` §55:
        PURCHASE PRICE                        `phist/<mã>/<NCC>/<ngày>` là
                                               báo giá NHÀ CUNG CẤP, một
                                               trục hoàn toàn khác `inv`.
```

Semantics gốc, trích nguyên văn từ chú thích repo B (`public/index.html:6687-6690`):
*"gia: giá thực nhập trung bình — chỉ máy tính, dùng định giá tài sản kho ·
cong: giá nhập công khai — đẩy sang cột Tồn của Bảng giá để tính Min"*. Cột
board tương ứng bị **khoá cứng, không cho gõ tay**, với lý do ghi thẳng trong
mã (`public/index.html:6120-6134`): *"mỗi lần 'Cập nhật từ dữ liệu hôm nay'
là `invSyncPart()` ghi đè toàn bộ theo file tồn cuối ngày ... khoá hẳn để
khỏi ai phải đoán vì sao số biến mất."*

**2. Write sites của `inv.cong` — 5 chỗ, 4 hàm, tất cả OVERWRITE bán phần
trong bộ nhớ, KHÔNG append.**

```
P-01  invMigrateGia()      :6789   bootstrap một lần: cong = copy(gia)
P-02  invApply()           :6961-6966   qua ngày/tải lại file: giữ giá trị
                                   sửa tay ngày trước nếu có, không thì
                                   cong[k] = gia[k]
P-03  invRecalcAvg()       :7099-7102  mỗi lần `lo` đổi, nếu CHƯA khoá tay
                                   (congTay[k] false) thì tự chạy theo `gia`
P-04  invSetGia(kind="cong") :7117-7120  SỬA TAY trực tiếp — set
                                   congTay[k]=true, ghi thẳng giá trị mới
P-05  invRecalcAvg()       :7085-7087  hàng hết SL (q<=0) → delete cong[k]
```

Toàn bộ đi qua `saveInv()` (`:6831-6835`) →
`db.ref("inv").set(INV)` — **ghi đè cả nhánh `inv`**, không phải
`update()` từng khoá.

**3. Read sites — đúng 2 chỗ đưa dữ liệu ra khỏi biến cục bộ.**

```
Q-01  invSyncPart()  :7238,7250   u[k+"/tp/ton"] = cong[invRowKey(x)]
                     → GHI vào board/<mã>/tp/ton, chạy mỗi lượt
                     buildSync()/runSync() (luồng "Cập nhật từ dữ liệu hôm
                     nay" — daily NCC price paste, KHÔNG theo lịch cố định,
                     người vận hành bấm bao nhiêu lần một ngày cũng được)
Q-02  renderInvT()   :7441,7463,7473-7476   hiện ô nhập trên UI tab Tồn kho
```

`grep -n "invCongOf("` = đúng 3 dòng trong toàn `public/index.html`
(`:6767` là helper nội bộ dùng lại trong P-02/P-03, `:7238`, `:7441`) — xác
nhận không còn read site nào khác.

**4. Overwrite vs append vs previous-value.**

```
overwrite giá cũ?    CÓ — mọi write (P-01…P-05) THAY THẾ trực tiếp giá trị
                     cũ tại đúng khoá invRowKey trong bộ nhớ, rồi ghi đè cả
                     nhánh `inv` qua set()
append?              KHÔNG
giữ previous value?  KHÔNG có trường `pv`/`prev` cho `cong` (khác
                     `board/<mã>/p/<NCC>` có `pv` một bước). Giá trị cũ chỉ
                     "sống sót" GIÁN TIẾP qua nhánh `cu`, và CHỈ tới lần
                     `invNextDay()` kế tiếp
```

**5. History riêng cho `inv.cong`? KHÔNG CÓ.**

Không nhánh RTDB nào tên `cong_hist` hay tương tự. `phist` có cấu trúc
`<mã>/<NCC>/<ngày>` — `cong` không có trục NCC (một giá trị mỗi mã mỗi ngày,
không phải mỗi NCC), nên **không khớp cấu trúc `phist`** kể cả về mặt hình
thức, không chỉ về mặt ngữ nghĩa.

**6. `backup`/`hist` có tái dựng được `cong` theo ngày không? KHÔNG.**

```
backup   :  snapshotBoard() (:4670-4676) chỉ chụp {board, meta} —
            KHÔNG có khoá `inv`. Kể cả nếu có, BACKUP_KEEP=10
            (:4630) và snapshotBoard() TỰ XOÁ mọi bản cũ hơn 10 bản
            gần nhất NGAY SAU MỖI LẦN chụp (:4678-4680) — không có
            đảm bảo theo NGÀY, chỉ có đảm bảo theo SỐ LƯỢNG SỰ KIỆN,
            và sự kiện snapshot là ad hoc (trước sync lớn/import/restore),
            không theo lịch.
hist     :  logHist()/logHistAs() (:9599-9636) chỉ lưu CHUỖI MÔ TẢ TỰ DO
            ("Tồn kho: qua ngày mới..."), KHÔNG có trường số nào cho
            `cong`. Tối đa 100 dòng, db.ref("hist").set() đè cả nhánh.
```

**7. Historical Replay Test cho `inv.cong` — KẾT QUẢ: NO.**

Bài kiểm của `TASK-105C` gốc (giá D = X, đổi thành Y, hỏi lại 30 ngày sau)
áp cho `cong`:

```
Ngày D, cong[k] = X.
Sau đó cong[k] đổi thành Y (bất kỳ một trong P-02/P-03/P-04).
Hỏi lại 30 ngày sau: giá trị X còn truy được không?

→ KHÔNG, trong TRƯỜNG HỢP CHUNG.
```

**8. NO GUARANTEED DELAY WINDOW.**

Không được đoán số ngày — và bằng chứng cho thấy **không có gì để đoán**,
vì có một nhánh worst-case đạt overwrite tức thời thật sự:

- **Trong ngày: tức thời.** `invSetGia(kind="cong")` (P-04) ghi đè
  `s.cong[k]` **ngay khi hàm chạy** — debounce 800ms ở `saveInv()` chỉ trễ
  lượt *ghi lên RTDB*, không trễ lượt *giá trị cũ biến mất khỏi bộ nhớ đang
  giữ state*. Tải lại file cùng ngày (`invApply()`, P-02) cũng ghi đè ngay.
  Không có version, không có khoá "đã dùng ở báo cáo, đừng đổi".
- **Qua ngày (`invNextDay()`): giữ đúng MỘT bước, và bước đó không theo
  lịch.** `INV.cu = moi; INV.moi = null` (`:7031`) — nhánh `cu` cũ bị
  **thay thế hoàn toàn**. `invNextDay()` là hàm gọi từ **nút bấm**
  (`:7019`), **không** nằm trong `scheduled()` của Worker
  (`src/index.js:830-840` — hai cron chỉ đẩy CRM/Sheet, không đụng `inv`).
  Không gì bắt buộc gọi đúng một lần mỗi ngày: có thể 0 lần trong một tuần
  (thì "hôm qua" chỉ còn là bản ghi từ lần rotate gần nhất, xa hơn 1 ngày),
  hoặc nhiều lần trong một ngày (thì "hôm qua" chưa từng tồn tại đủ 24 giờ).
  Bản thân một bước undo (`_invUndo`) chỉ sống **trong bộ nhớ JavaScript của
  phiên trình duyệt đang mở** — mất khi tải lại trang hay đóng tab.

⇒ **NO GUARANTEED DELAY WINDOW.** Không phải "cửa sổ ngắn nhưng có" — cửa sổ
tối thiểu đạt được trên thực tế là **0**, vì nhánh tức thời (sửa tay/tải lại
file) luôn khả dụng bất kỳ lúc nào, độc lập với việc rotate ngày có xảy ra
hay không.

**9. Reuse `phist` hay namespace riêng? — NAMESPACE RIÊNG, bắt buộc.**

Ba lý do, không phải một:

- **Sai trục.** `phist` khoá theo `(mã, NCC, ngày)`; `cong` khoá theo
  `(mã, ngày)` — không có NCC. Ép `cong` vào `phist` buộc phải bịa một "NCC
  giả", làm hỏng chính bất biến mà `phist` đang giữ (mọi khoá NCC trong
  `phist` là một nhà cung cấp thật).
- **Sai khoá gốc.** `cong` trong RTDB hiện được lưu tại `invRowKey(x)` =
  `"N_" + normCode(tên hàng)[:80]` — khoá theo **tên hàng chuẩn hoá trong
  file tồn**, KHÔNG phải mã board (`<MÃ>`). Muốn khớp với `product_key` của
  Reports phải đi qua `inv.map` để dịch sang mã board — đây là một bước dịch
  **độc lập** với việc `phist` đã dùng mã board trực tiếp làm khoá lá.
- **Sai đúng bẫy đã tránh ở `DEC-147`.** Gộp hai nguồn ngữ nghĩa khác nhau
  vào cùng một nhánh RTDB là chính hành vi `SOURCE MISMATCH` mà `DEC-147` §55
  cảnh báo — tái tạo nó ở tầng lưu trữ thay vì tầng đọc dữ liệu không giải
  quyết được gì, chỉ giấu vấn đề sâu hơn.

**10. Đề xuất schema tối thiểu — `PublicPurchasePriceHistory`. KHÔNG
implementation.**

Tái dùng đúng 4-cột contract của `DEC-145` §4 (không phát minh format mới),
cộng đúng những trường mà `cong` hiện KHÔNG có và bắt buộc phải có để đóng
băng được:

```
REQUIRED (kế thừa DEC-145 §4, KHÔNG đổi ý nghĩa):
  product_key       — mã board (<MÃ>), SAU KHI dịch qua inv.map — không
                       phải invRowKey thô, vì invRowKey đổi theo cách viết
                       tên hàng trong từng file, còn mã board mới là khoá
                       ổn định để tra theo DEC-145 §2
  effective_from     — YYYY-MM-DD, NGÀY CHỤP (business date của lượt capture)
  effective_to       — YYYY-MM-DD hoặc rỗng cho record hiện hành cuối cùng
                       (đúng khoảng đóng của DEC-145 §1)
  purchase_price     — VND nguyên, Decimal — CHUYỂN ĐỔI TẠI ĐÚNG BIÊN NÀY
                       (RTDB lưu nghìn đồng, xem DEC-147 §6/ADR-103 §2)

BẮT BUỘC THÊM (vì `cong` không tự mang những thứ này):
  source              = "inv.cong"  (cố định, để phân biệt khỏi các nguồn
                         khác nếu sau này có thêm)
  captured_at          — ISO 8601, timestamp THẬT của lượt capture (server-
                          side nếu capture chạy trên Worker; KHÔNG dùng
                          todayStr() kiểu client như phist)
  raw_row_key           — invRowKey thô tại thời điểm capture (audit trail:
                          cho biết record này khớp qua `inv.map` nào, để dò
                          lại nếu `inv.map` đổi sau này)

OPTIONAL:
  captured_by           — id/tên job capture, nếu có nhiều job hoặc nhiều
                          instance chạy song song
```

Đây **không phải** thiết kế mới về mặt hình dạng — nó là schema `DEC-145` §4
với hai trường bổ sung bắt buộc vì nguồn (`cong`) không tự mang timestamp máy
chủ hay provenance, khác `phist` (có ít nhất khoá ngày do client tạo).

Reason:

**1. Vì sao xác nhận 4 semantics mà không tự đặt câu hỏi ngược.** Đây là một
quyết định chủ dự án đưa vào, không phải một suy luận cần verify tính đúng
sai nghiệp vụ — việc của phiên này là kiểm tra nó có **khớp với những gì code
thật đang làm** hay không, và cả bốn khớp. Không có mâu thuẫn nào để báo
`CONFLICT DETECTED`.

**2. Vì sao "NO GUARANTEED DELAY WINDOW" là phát hiện chính, không phải một
chi tiết phụ.** `DEC-147` đã nói `inv.gia`/`.lo` "không có lịch sử" như một
sự kiện tĩnh. Phiên này đào sâu thêm một bậc: `inv.cong` không chỉ "không có
lịch sử" mà còn **không có gì đứng giữa hiện tại và một lần overwrite bất kỳ
lúc nào**. Sự khác biệt quan trọng: "không có lịch sử" gợi ý có thể chờ vài
ngày rồi build capture cũng chưa muộn; "no guaranteed window" nói rằng **mỗi
ngày trôi qua mà chưa có capture là dữ liệu có thể đã mất vĩnh viễn, ngay cả
với dữ liệu của chính ngày hôm đó**.

**3. Vì sao namespace riêng, không phải một field mới trong `phist`.**
Không phải sở thích kiến trúc — `phist` và `cong` khác nhau ở **cấu trúc
khoá** (có/không trục NCC) trước khi khác nhau ở ngữ nghĩa. Ép chung vào một
namespace phá vỡ bất biến hiện có của `phist` mà chính hệ thống giá đang dựa
vào (mọi khoá lá dưới `phist/<mã>/` là một NCC thật).

Risk:

`Effective Risk = HIGH` — **không đổi**, chấm theo data path (V4.1 §4).
Phiên này làm rủi ro **cụ thể và cấp thiết hơn**, không đổi bản chất:

- **Rủi ro lớn nhất: đọc "đã chốt field" thành "đã xong, chỉ còn nối dây".**
  Sự thật ngược lại — trường vừa được chỉ định là trường **hoàn toàn không
  có lịch sử**, và capture layer giờ là điều kiện tiên quyết cấp thiết, không
  phải việc làm sau khi rảnh. Giảm nhẹ: nêu tường minh ở đây và trong
  `PROJECT_PROGRESS.md`.
- **Mỗi ngày trì hoãn capture = dữ liệu ngày đó có nguy cơ mất vĩnh viễn**,
  không phải nguy cơ trừu tượng — vì nhánh overwrite-tức-thời (sửa tay/tải
  lại file) luôn khả dụng độc lập với lịch rotate.
- **`invRowKey` (khoá thô) không ổn định qua thời gian** nếu file tồn kho đổi
  cách viết tên hàng — bất kỳ capture nào cũng phải dịch qua `inv.map` **tại
  đúng thời điểm capture**, không phải dịch lại sau, vì `inv.map` bản thân nó
  cũng có thể đổi.

Impact:
- `PROJECT/PROJECT_DECISIONS.md` — DEC này (ID cấp sau khi quét namespace
  toàn repo; `DEC-148` xác nhận trống).
- `PROJECT/PROJECT_PROGRESS.md` — cập nhật field candidate (không còn "3 ứng
  viên, TBD" mà là "chủ dự án đã chỉ định `inv.cong`") + finding "NO
  GUARANTEED DELAY WINDOW".
- `docs/tasks/TASK-108B-eligible-costs-owner-definition.md` — Phần VII.
- `docs/sessions/S025-task-105c-public-purchase-price-cong-audit.md` — bàn
  giao phiên.
- **Không** sửa `app/**`, `config/**`, `tests/**`, Golden fixture/expected,
  `TASK-110`, `CHECK-110-16`, `R1-A1`, `governance/**`.
- **Không** sửa repo B (`Tracking`) — 0 file.

Can Revisit After:
- Chủ dự án xác nhận xây tầng capture cho `inv.cong` (câu hỏi 4 của
  `DEC-147` §60, nay áp trực tiếp cho `cong`) và tần suất — mở
  `TASK-105C` implementation với `docs/tasks/TASK-105C-*.md` (Scope Lock +
  Completion Gate).
- Một lượt đọc RTDB thật (có credential) ⇒ đo được tần suất thực tế
  `invNextDay()`/`invSetGia()` chạy, để ước lượng mức độ dữ liệu đã mất tính
  tới hiện tại.

## DEC-149

Date:
2026-08-27

Task:
`TASK-105C` — Market Min Price Path Audit. Ghi trong phiên
"TASK-105C — MARKET MIN PRICE PATH AUDIT"
(`docs/sessions/S026-task-105c-market-min-price-path-audit.md`). Trả lời
business rule mới của chủ dự án: ưu tiên **GIÁ MIN** (`_c.min`) làm
`AccountingPurchasePrice`, `inv.cong` chỉ là fallback khi Min "không có căn
cứ".

Repo được audit:
`hoangvinhkta-creator/Tracking` @ `d177363a390d36fe793e0c1c44a6fb6743ca45f5`
(không đổi so với `DEC-147`/`DEC-148`). **0 file thay đổi**.

Decision:

Đây là **bản ghi audit findings**, tiếp nối `DEC-147`/`DEC-148`. Nó trả lời
đầy đủ field/formula/writer/reader của Min, và báo cáo một `CONFLICT
DETECTED` giữa business rule Owner vừa mô tả và cách `_c.min` thực sự vận
hành — theo đúng quy tắc `CLAUDE.md` §"Quy Tắc Xung Đột": không tự giải
quyết.

**1. Field thật — `board/<mã>/_c.min`.**

```
Ghi bởi   : tinhChot() (price-engine) qua saveBoardPaths()/queTinhLai() (client)
Đọc bởi   : bMinOf() (client, mọi màn hình) + soCotTinh() (Worker, fallback
            cho CSV/CRM khi _c stale)
Cache-key : _c.k so với meta.k (vân tay danh sách NCC bị loại) — lệch thì
            client hiện "…" (undefined) và Worker tự tính lại tạm bằng
            soCotTinh()
```

`_c.min` **đúng** là con số Owner mô tả là "Giá Min" trên tab Bảng giá —
xác nhận bằng chính UI: tooltip cột Min ghi *"Giá VỐN rẻ nhất — rẻ nhất giữa
các NCC còn hàng và giá nhập hàng trong kho"* (`public/index.html:6144-6146`).

**2. Formula — trích chính xác, không diễn giải.**

```
INPUT:
  ds[]     = { ncc, gia } — mọi NCC trong board.p KHÔNG thuộc danh sách loại
             trừ `an` (= `_ANC`, hợp của NCC_RETIRED-alias + NCC_MIN_LOAI),
             với cell.s === "ok" và cell.v > 0
  t        = tp.ton  (= inv.cong, xem DEC-148)  — CHỈ khi là số dương
  coDuLieu = có ÍT NHẤT MỘT NCC (ngoài `an`) từng có cell (bất kể s là gì)
  conBan   = có ÍT NHẤT MỘT NCC (ngoài `an`) đang cell.s === "ok"

RULE:
  1. ds.sort(ascending by gia)
  2. while ds.length >= 2 and ds[0].gia < ds[1].gia × 0.3:
       remove ds[0], ghi vào batThuong[]        // lọc outlier, pe-6
  3. m = ds.length ? ds[0].gia : null            // giá NCC rẻ nhất còn sống
  4. if t is number > 0 and (m is null or t < m): m = t
  5. if m !== null: MIN = m
     else: MIN = (coDuLieu and not conBan) ? 0 : null

OUTPUT:
  number > 0  → giá Min thật
  0           → SENTINEL "hoàn toàn hết hàng" — có NCC từng bán, nay
                không ai còn "ok" và không có tp.ton dương
  null        → KHÔNG rõ nghĩa duy nhất — xem §6 "NO MARKET MIN BASIS"
  undefined   → (chỉ ở client, qua cOf()) chưa tính xong / cache lệch vân
                tay — KHÔNG phải kết luận về dữ liệu
```

Nguồn: `minCuaDong()` (`price-engine/src/nghiepvu.js:632-637`),
`locGiaNcc()` (`:569-583`), `hetHangHoanToan()` (`:596-599`).

Worker giữ một **bản sao độc lập** (`soCotTinh()`, `src/index.js:305-350`)
dùng khi `_c` cũ hơn vân tay hiện hành — bản này **không** áp bước 2 (lọc
outlier `NGUONG_BAT_THUONG`), chỉ lấy thẳng `cell.v > 0`. Hai công thức
**không hoàn toàn giống nhau**; khác biệt chỉ lộ ra khi CSV/CRM đọc một dòng
đang stale VÀ dòng đó có giá NCC bất thường — hẹp nhưng có thật, ghi lại để
không ai tưởng chúng là một bản.

**3. Historical Replay Test — kết quả: C (chỉ current snapshot, KHÔNG
replay được).**

```
01/08: MIN = X
10/08: MIN = Y
30/08: reconstruct MIN của 05/08? → KHÔNG.
```

Không phải vì thiếu một input — vì thiếu **bốn lớp cùng lúc**:

```
(a) `_c` không có history riêng — mỗi lần tính lại GHI ĐÈ, không nhánh RTDB
    nào lưu chuỗi `_c.min` theo ngày.
(b) Formula sống KHÔNG BAO GIỜ đọc `phist` — xác nhận bằng
    grep -rn "phist" price-engine/src/nghiepvu.js src/index.js
    price-engine/src/index.js = 0 hit. `gotDong()` (public/index.html:3551)
    chỉ gom board HIỆN TẠI.
(c) Một trong hai input chính, `tp.ton` (= inv.cong), ĐÃ được xác nhận
    KHÔNG có lịch sử (DEC-148 §8, NO GUARANTEED DELAY WINDOW) — dù có tái
    dựng hoàn hảo phần vendor-price từ phist, vẫn thiếu input này.
(d) Danh sách loại trừ NCC (NCC_RETIRED, NCC_MIN_LOAI) và ngưỡng lọc outlier
    (NGUONG_BAT_THUONG=0.3) là HẰNG SỐ MÃ NGUỒN, không lưu ở RTDB, không có
    bản ghi "ngày đó danh sách/ngưỡng là gì" — chỉ suy ra được (một phần)
    từ lịch sử Git, và Git repo B là SHALLOW (DEC-147, mốc cũ nhất còn thấy
    2026-08-18).
```

**4. Reconstruction từ `phist` — Không đủ, dù chỉ xét riêng phần vendor.**

Áp đúng checklist đề bài mục 4 cho riêng phần "giá NCC" của công thức (bỏ
qua phần `tp.ton` đã biết là NO ở (c) trên):

```
mọi input CÓ history?        MỘT PHẦN — chỉ p/<NCC>/v có (qua phist);
                              tp.ton KHÔNG; exclusion list/threshold KHÔNG
0 sentinel                    phist: 0 = NCC hết hàng (khác _c.min: 0 =
                              TOÀN BỘ mã hết hàng) — HAI Ý NGHĨA "0" KHÁC
                              NHAU trên hai field khác nhau, dễ gộp nhầm
NCC gone state                phist ghi được (mốc 0), nhưng chỉ khi phist
                              CÒN NGUYÊN — xem dưới
mapping product                đã audit ở DEC-147 §56 — cần inv.map, ổn
                              định theo thời gian không đảm bảo
config thay đổi theo thời gian NCC_RETIRED/NCC_MIN_LOAI/NGUONG_BAT_THUONG —
                              KHÔNG versioned, xem (d) ở trên — ĐÂY LÀ GAP
                              MỚI, đề bài yêu cầu kiểm minh bạch
manual overrides               oddNoMap()/pinOdd() (public/index.html:5516-
                              5533) — ảnh hưởng NCC price giữ nguyên hay
                              không, lưu ở meta.oddNo, CẮT còn ODD_NO_MAX
                              mục gần nhất — KHÔNG phải lịch sử đầy đủ
tồn kho/public price tham gia? CÓ — tp.ton là input trực tiếp (bước 4 công
                              thức) — và KHÔNG có lịch sử (DEC-148)
deleted/edited historical      CÓ — phist sửa được qua 4 đường (DEC-147 §54
records                      R4): xoaPhistSau/đổi mã/gộp mã/khôi phục bảng
```

⇒ **Không được gọi bất kỳ lượt replay nào là deterministic**, kể cả nếu giới
hạn phạm vi chỉ ở phần vendor-price của công thức.

**5. Đối chiếu business rule Owner — `CONFLICT DETECTED`.**

```
CONFLICT DETECTED

Documentation (Owner statement, phiên này):
    "Nếu sản phẩm có căn cứ tính GIÁ MIN trên tab Bảng giá: dùng GIÁ MIN
     làm giá nhập tính cho nhân viên. Chỉ khi sản phẩm/mã lạ không có căn
     cứ nào để tính GIÁ MIN: fallback sang giá nhập công khai inv.cong."
    → Mô tả một quy tắc ƯU TIÊN TUẦN TỰ: Min trước, cong chỉ được dùng khi
      Min hoàn toàn bất khả (không có bất kỳ căn cứ nào).

Implementation (minCuaDong(), price-engine/src/nghiepvu.js:632-637):
    m = giá NCC rẻ nhất còn hàng (đã lọc outlier)
    NẾU tp.ton (= inv.cong) là số dương VÀ NHỎ HƠN m → m = tp.ton
    → `cong` LUÔN được xét trong MỌI lượt tính, không chỉ khi Min bất khả.
      Nó CẠNH TRANH trực tiếp với giá NCC và THẮNG bất cứ khi nào rẻ hơn —
      kể cả khi NCC vẫn còn hàng, giá NCC vẫn hoàn toàn "có căn cứ" theo
      đúng nghĩa Owner mô tả.

Risk:
    Field `_c.min` (con số hiển thị "Giá Min" trên board hôm nay) KHÔNG
    bằng kết quả của quy tắc IF/ELSE mà Owner vừa mô tả. Nếu Reports lấy
    thẳng `_c.min` làm output của quy tắc ưu tiên đó, MỌI trường hợp `cong`
    tình cờ rẻ hơn giá NCC — dù NCC hoàn toàn có căn cứ, hoàn toàn còn
    hàng — sẽ ÂM THẦM dùng `cong` mà không ai biết đó là `cong` chứ không
    phải giá NCC thật. Đây đúng loại lỗi mà DEC-103/125/143/145 tồn tại để
    chặn: một con số có mặt, trông hợp lý (là "Giá Min" mà!), ở sai lý do.

Recommended resolution:
    KHÔNG tự chọn. Cần Owner xác nhận MỘT trong hai:
    (A) Ý định là "dùng đúng _c.min như đang hiển thị trên board" — chấp
        nhận cong có thể thắng khi rẻ hơn giá NCC, coi đó là ĐÚNG nghiệp vụ
        (giá vốn rẻ nhất, không phân biệt nguồn — đúng triết lý gốc của Min
        ghi trong chính comment code: "GIÁ VỐN RẺ NHẤT BÁN RA ĐƯỢC, không
        phân biệt nguồn"). Nếu vậy, quy tắc ưu tiên Owner mô tả ("Min trước,
        cong sau") thực ra ĐÃ ĐÚNG — nhưng vì cong nằm BÊN TRONG Min, không
        phải vì có một bước fallback riêng biệt sau khi Min thất bại.
    (B) Ý định là một field MỚI — "chỉ giá NCC, cong CHỈ dùng khi không NCC
        nào định giá được" — cần TÁCH `t` (tp.ton) ra khỏi công thức Min
        hiện tại để dựng riêng, một thay đổi kiến trúc bên phía repo B,
        KHÔNG phải đọc thẳng field có sẵn.
```

**6. `NO MARKET MIN BASIS` — định nghĩa, và phát hiện code hiện tại GỘP
CHUNG nhiều trạng thái khác nhau.**

```
DETERMINED_NO_BASIS  =  MIN resolves = 0
    Điều kiện chính xác: hetHangHoanToan(p, an) === true, tức CÓ ít nhất
    một NCC (ngoài an) từng ghi cell cho mã này, và KHÔNG CÒN AI đang
    "ok" — VÀ không có tp.ton dương.
    Đây là trạng thái SẠCH: hệ thống BIẾT CHẮC lý do (đã hết hàng), không
    phải suy đoán.

UNKNOWN (dữ liệu)  =  MIN resolves = null
    Đây KHÔNG phải một nguyên nhân — code hiện tại GỘP ÍT NHẤT BA trường
    hợp khác nhau vào cùng tín hiệu `null`, không phân biệt được từ bên
    ngoài:
    (a) Mã CHƯA TỪNG có NCC nào định giá và không có tp.ton — "chưa từng
        có căn cứ" theo đúng nghĩa Owner dùng.
    (b) Mã CÓ NCC đang "ok" nhưng với giá <= 0 hoặc bị lọc outlier hết sạch
        (locGiaNcc() trả ds rỗng) — đây là VẤN ĐỀ CHẤT LƯỢNG DỮ LIỆU, KHÔNG
        phải "không có căn cứ": hetHangHoanToan() trả false (vì cell vẫn
        "ok"), nên KHÔNG rơi vào nhánh 0 — nhưng ds rỗng nên m vẫn null.
        Trường hợp này bị nguỵ trang thành giống hệt (a).
    (c) Mã KHÔNG TỒN TẠI trên board (chưa map, hoặc bị xoá) — Worker/client
        thậm chí không gọi được minCuaDong() cho mã này; không có `_c`
        nào để đọc, khác hẳn (a)/(b) nhưng từ phía Reports nhìn vào (lookup
        thất bại) sẽ dễ bị xử lý y hệt.

UNKNOWN (vận hành, KHÔNG phải kết luận dữ liệu)  =  client thấy undefined
    (qua cOf()) khi `_c.k !== meta.k` — nghĩa là "chưa kịp tính lại", không
    phải "không có căn cứ". TUYỆT ĐỐI không được đọc như DETERMINED_NO_BASIS
    hay dùng để trigger fallback — đây là staleness thuần tuý.

SOURCE_FAILURE  =  lời gọi /api/tinhchot thất bại (mạng, service binding
    down). saveBoardPaths() (public/index.html:3780-3788) BẮT lỗi này và
    KHÔNG ghi `_c` mới — `_c` cũ (nếu có) hoặc trạng thái "chưa từng tính"
    vẫn giữ nguyên. Ở TẦNG DỮ LIỆU, SOURCE_FAILURE và "chưa từng tính lần
    nào" KHÔNG PHÂN BIỆT ĐƯỢC — cả hai nhìn giống hệt "_c vắng mặt".
```

Theo đúng chỉ dẫn của đề bài: **UNKNOWN không được tự động fallback nếu che
lỗi dữ liệu.** Trường hợp (b) ở trên là bằng chứng cụ thể cho rủi ro đó — một
mã có dữ liệu NCC nhưng HỎNG (giá 0/âm, hoặc bị lọc hết vì outlier) sẽ trông
giống hệt một mã chưa từng có ai định giá, và một quy tắc fallback tự động
sang `cong` sẽ ÂM THẦM che đi sự cố chất lượng dữ liệu NCC — đúng loại lỗi
"con số có mặt, sai lý do" mà governance của dự án này liên tục nhắc.

**7. Fallback rule hiện tại trong code — KHÔNG TỒN TẠI theo đúng hình dạng
Owner mô tả.**

Không có bất kỳ đoạn code nào trong repo B implement:
```
IF MarketMinPrice determinable: dùng nó
ELSE IF PublicPurchasePrice determinable: dùng nó
ELSE: Pending
```
như hai giá trị TÁCH BIỆT với một priority-switch bên ngoài. Thay vào đó,
`tp.ton` (cong) là **một input hoà tan bên trong cùng công thức Min** (§2
bước 4) — không phải một candidate dự phòng độc lập được thử sau khi Min
"thất bại". Đây chính là nội dung của `CONFLICT DETECTED` ở §5.

**8. Guaranteed Delay Window — NO GUARANTEED DELAY WINDOW.**

```
1 giờ    :  KHÔNG chắc — bất kỳ ghi nào khớp canTinhLai() (cả dòng, p/<NCC>,
            tp.ton/chot/bien) TÁI TÍNH và GHI ĐÈ `_c` ngay lập tức, không
            debounce cấp giờ.
1 ngày   :  KHÔNG chắc — cùng lý do; đồng thời board.p bị ghi đè mỗi lượt
            "Cập nhật từ dữ liệu hôm nay" (daily NCC paste, không giới hạn
            số lần/ngày), và tp.ton bị ghi đè mỗi lượt sync tồn kho.
7 ngày   :  KHÔNG chắc — same, cộng dồn nhiều lượt overwrite.
30 ngày  :  KHÔNG chắc — same.
```

`_c.min` được TÁI TÍNH VÀ GHI ĐÈ trên đúng cùng trigger mà `tp.ton`/`inv.cong`
đã được xác nhận không có window đảm bảo nào (`DEC-148` §8) — không có gì
trong cơ chế của `_c` làm window này khá hơn. **NO GUARANTEED DELAY WINDOW.**

**9. Taxonomy Owner đề xuất — xác minh khớp code, với một điều chỉnh.**

```
MarketMinPrice               = board/<mã>/_c.min                    ✅ khớp,
                                nhưng LƯU Ý: đã CHỨA `PublicPurchasePrice`
                                bên trong công thức (§5) — không phải hai
                                khái niệm tách bạch ở tầng dữ liệu hiện tại
PublicPurchasePrice          = inv.cong (qua board/<mã>/tp/ton)      ✅ khớp
                                (DEC-148)
PrivateAveragePurchasePrice  = inv.gia                               ✅ khớp
                                (DEC-148)
VendorQuotedPrice            = phist / board/<mã>/p/<NCC>/v          ✅ khớp
                                (DEC-147)
LotPurchasePrice             = inv.lo                                 ✅ khớp
                                (DEC-148)
AccountingPurchasePrice      = resolved output — CHƯA TỒN TẠI trong code
                                hiện tại dưới bất kỳ hình dạng nào; đây là
                                khái niệm Reports sẽ TẠO RA, không phải một
                                field đã có sẵn ở repo B
```

Taxonomy **dùng được**, nhưng phải đi kèm chú thích ở dòng `MarketMinPrice`:
nó không phải một số "thuần vendor" — nó đã lai với `PublicPurchasePrice`
theo công thức `min(vendor, cong)`, nên gọi hai cái là "hai nguồn độc lập,
Min trước, cong sau" cần được Owner xác nhận đúng ý (§5 Recommended
resolution).

**10. Đề xuất kiến trúc lịch sử — chọn OPTION ít thay đổi nhất mà vẫn đảm
bảo replay đúng.**

Bốn option đề bài đưa ra, đánh giá theo đúng tiêu chí "upload sales file sau
30 ngày/6 tháng → cùng đơn phải ra cùng `AccountingPurchasePrice`":

```
A  chỉ history inv.cong
     KHÔNG đủ nếu quy tắc ưu tiên có ý (B) ở §5 — vì lúc đó cần biết Min
     theo nghĩa THUẦN VENDOR để biết khi nào fallback đúng lúc. Đủ CHỈ NẾU
     Owner xác nhận ý (A) ở §5 (dùng đúng _c.min hiện tại, coi cong-thắng
     là hợp lệ) — nhưng khi đó "MarketMinPrice" không còn là khái niệm cần
     capture riêng, việc capture inv.cong ĐÃ ĐỦ vì nó là input duy nhất cần
     lịch sử (giá NCC vẫn cần lịch sử qua phist, nhưng phist đã tồn tại).
     Vẫn thiếu: exclusion list/threshold versioning (§3(d)) nếu muốn replay
     TUYỆT ĐỐI chính xác quá khứ.

B  history MarketMinPrice + inv.cong
     Capture CẢ HAI số riêng biệt mỗi ngày. Đủ dữ liệu cho cả hai cách hiểu
     ở §5, không cần Owner quyết trước khi bắt đầu capture — nhưng TỐN GẤP
     ĐÔI so với cần thiết nếu cuối cùng chỉ một trong hai được dùng.

C  capture trực tiếp resolved AccountingPurchasePrice + provenance
     ĐÚNG kiến trúc dài hạn (tách biệt "cái gì đang chạy trong repo B" khỏi
     "cái gì Reports cần") nhưng ĐÒI xây rule engine chọn A vs B TRƯỚC —
     tức đòi Owner trả lời CONFLICT §5 TRƯỚC KHI bắt đầu capture bất kỳ gì.
     Rủi ro: nếu bắt đầu capture theo một cách hiểu rồi Owner chỉnh lại,
     dữ liệu đã capture theo cách hiểu cũ không tự sửa được.

D  reconstruct MarketMinPrice từ phist, capture chỉ inv.cong fallback
     KHÔNG khả thi — §3/§4 đã chứng minh: formula sống không đọc phist,
     và ngay cả một lượt tái dựng thủ công cũng thiếu exclusion-list
     history + threshold history + inv.cong history. "Reconstruct từ
     phist" không phải một no-op rẻ tiền — nó đòi viết một cỗ máy replay
     riêng mà chính bằng chứng ở đây cho thấy sẽ KHÔNG deterministic dù
     có viết ra.
```

**RECOMMENDED: OPTION B**, với lý do "ít thay đổi nhất mà vẫn đảm bảo" theo
đúng tiêu chí đề bài đặt ra:

- Không đòi giải quyết `CONFLICT DETECTED` §5 TRƯỚC KHI bắt đầu capture —
  capture cả hai số độc lập, để quyết định "dùng số nào" xảy ra ở TẦNG ĐỌC
  (Reports `PriceProvider`), không phải tầng capture. Nếu sau này Owner chọn
  ý (A), Reports đơn giản đọc cột `market_min_price`; nếu chọn (B), Reports
  đọc `public_purchase_price` khi `market_min_price` là `DETERMINED_NO_BASIS`.
  Không cần capture lại từ đầu trong cả hai kịch bản.
- Không đòi xây rule engine mới trong repo B (khác OPTION C) — capture chỉ
  ĐỌC hai field đã tồn tại (`_c.min`, `tp.ton`) mỗi lượt chụp, không cần hiểu
  ý nghĩa nghiệp vụ của chúng tại thời điểm capture.
- Loại bỏ hẳn OPTION D — đã chứng minh không khả thi, không phải vì thiếu nỗ
  lực mà vì thiếu dữ liệu nguồn không thể tạo lại.

**Điều kiện đi kèm bắt buộc** (không phải optional, để capture không lặp
lại đúng lỗi đang audit): mỗi lượt capture phải ghi luôn `_ANC` (danh sách
loại trừ NCC tại thời điểm đó) và `NGUONG_BAT_THUONG` (giá trị ngưỡng tại
thời điểm đó) làm provenance — nếu không, `market_min_price` được capture
hôm nay vẫn không tái dựng được nếu code sau này đổi hai hằng số đó, lặp lại
đúng vấn đề ở §3(d) một tầng cao hơn.

Reason:

**1. Vì sao báo cáo `CONFLICT DETECTED` thay vì tự chọn cách hiểu.** `Min`
và `cong` không phải hai khái niệm độc lập trong code hiện tại — `cong` là
MỘT THÀNH PHẦN của Min. Business rule Owner mô tả giả định chúng độc lập
(một cái "thắng", cái kia "thua" theo thứ tự). Tự chọn nghĩa nào đúng là
đoán ý Owner ở đúng chỗ có thể sai lệch lương/KPI — governance của dự án này
(`CLAUDE.md` "Quy Tắc Xung Đột") cấm chính việc đó.

**2. Vì sao Historical Replay = C không phải B.** B đòi *"có thể tái dựng
CHÍNH XÁC"*. Ở đây không chỉ một input thiếu (đã đủ để loại B) mà **bốn lớp**
thiếu cùng lúc, hai trong số đó (`tp.ton` không lịch sử, exclusion list
không versioned) là **không thể vá bằng cách đọc thêm dữ liệu có sẵn** — dữ
liệu đó CHƯA TỪNG được ghi lại ở đâu.

**3. Vì sao OPTION B, không phải A hay C.** A giả định đã biết câu trả lời
của `CONFLICT DETECTED` — rủi ro nếu đoán sai. C đúng về mặt kiến trúc dài
hạn nhưng đảo ngược thứ tự: đòi quyết định nghiệp vụ TRƯỚC KHI có dữ liệu để
quyết định dựa trên đó. B tách rời "ghi lại cái gì đang có" khỏi "diễn giải
nó nghĩa là gì" — đúng nguyên tắc audit-trước-implementation mà toàn bộ
`TASK-105C` đang theo.

Risk:

`Effective Risk = HIGH` — không đổi, chấm theo data path (V4.1 §4). Phiên
này làm rủi ro **cụ thể hơn ở đúng một điểm mới**: không chỉ "chưa capture
được lịch sử" (đã biết từ DEC-148), mà **"trường sắp được dùng có thể mang
sai ý nghĩa nghiệp vụ ngay từ hôm nay, kể cả không cần chờ vấn đề lịch sử"**
— vì `CONFLICT DETECTED` ở §5 là vấn đề CỦA HIỆN TẠI, không phải vấn đề
"replay quá khứ".

- **Rủi ro lớn nhất:** implement quy tắc ưu tiên bằng cách đọc thẳng `_c.min`
  mà không biết nó đã ngầm chứa `cong`. Giảm nhẹ: `CONFLICT DETECTED` ghi
  tường minh ở §5, không tự giải quyết.
- **Rủi ro thứ hai:** một `null` bị đọc là "chắc chắn không có căn cứ" rồi tự
  động fallback, trong khi thật ra là dữ liệu NCC hỏng (§6 trường hợp b) —
  che mất một lỗi chất lượng dữ liệu đáng lẽ phải được thấy.
- **Rủi ro thứ ba:** capture theo OPTION C (resolved output) trước khi có
  câu trả lời §5, rồi phải capture lại từ đầu khi Owner làm rõ ý định. Giảm
  nhẹ: khuyến nghị B thay vì C chính vì lý do này.

Impact:
- `PROJECT/PROJECT_DECISIONS.md` — DEC này (ID cấp sau khi quét namespace
  toàn repo; `DEC-149` xác nhận trống).
- `PROJECT/PROJECT_PROGRESS.md` — ghi rõ `CONFLICT DETECTED` chưa giải
  quyết, cập nhật đề xuất kiến trúc capture (OPTION B).
- `docs/tasks/TASK-108B-eligible-costs-owner-definition.md` — Phần VIII.
- `docs/sessions/S026-task-105c-market-min-price-path-audit.md` — bàn giao.
- **Không** sửa `app/**`, `config/**`, `tests/**`, Golden fixture/expected,
  `TASK-110`, `CHECK-110-16`, `R1-A1`, `governance/**`.
- **Không** sửa repo B (`Tracking`) — 0 file.

Can Revisit After:
- Chủ dự án trả lời `CONFLICT DETECTED` §5: dùng đúng `_c.min` (chấp nhận
  cong lai bên trong), hay cần field mới tách riêng vendor-only Min.
- Chủ dự án xác nhận OPTION B (hoặc chọn khác) và tần suất capture — mở
  `TASK-105C` implementation với `docs/tasks/TASK-105C-*.md`.
- Một lượt đọc RTDB thật (có credential) ⇒ đo tần suất thực tế
  `saveBoardPaths()`/`invSyncPart()` chạy trong một ngày vận hành.

## DEC-150

Date:
2026-08-27

Task:
`TASK-105C` — Price History Chart / Min Replay Verification. Ghi trong phiên
"TASK-105C — PRICE HISTORY CHART / MIN REPLAY VERIFICATION"
(`docs/sessions/S027-task-105c-price-history-popup-verification.md`).

**Đây là bản ghi AUDIT FACT, không phải Owner Decision mới.** Không đổi bất
kỳ trạng thái `READY`/`BLOCKED`/`OWNER_DECISION_REQUIRED` nào đã có ở
`DEC-147`–`DEC-149`. Mục đích duy nhất: xác minh chính xác popup "Lịch sử
giá" trên tab Bảng giá — bằng chứng UI Owner vừa cung cấp — hoạt động thế
nào, trước khi bất kỳ ai coi nó là câu trả lời (hoặc một phần câu trả lời)
cho `CONFLICT DETECTED` §71 của `DEC-149`.

Repo được audit:
`hoangvinhkta-creator/Tracking` @ `d177363a390d36fe793e0c1c44a6fb6743ca45f5`
(không đổi). **0 file thay đổi.**

Decision:

**1. Popup — function, path, và transform. Trích chính xác.**

```
Mở popup     : openPhist(key)          public/index.html:6218-6238
               trigger: ô Min trên bảng (data-viec="openPhist", :6143,
               tooltip "bấm xem biểu đồ lịch sử giá") và bảng lệnh UI
               (:1931)
Load data    : loadPhist(key)          :4661-4664
               db.ref("phist/"+key).once("value") — MỘT lượt đọc, KHÔNG lọc
Dựng series  : renderPhist(row, data)  :6243-6314
               sups = Object.keys(data)  — mỗi NCC trong phist thành MỘT
               đường; SVG vẽ tay, không thư viện chart
Hover card   : phShow(td,key,ncc,data) :6191-6217 — MỘT NCC mỗi lần
Transform    : KHÔNG CÓ transform nghiệp vụ nào giữa loadPhist() và render —
               dữ liệu vẽ thẳng là dữ liệu đọc thẳng từ `phist/<mã>`
```

**2. Popup hiển thị gì — OPTION A, chứng minh bằng code, không suy luận UI.**

```
A. raw history của từng NCC từ `phist`             ✅ ĐÚNG — xác nhận
B. history của `_c.min`                             ❌ SAI
C. history của `inv.cong`                           ❌ SAI
D. Min được TÁI TÍNH từ lịch sử NCC                 ❌ SAI
E. hybrid                                            ❌ SAI
```

Bằng chứng phủ định B/C/D/E: `grep` trực tiếp trên toàn khối
`public/index.html:6218-6314` (mọi function của popup) cho `tp\.`, `inv\.`,
`cong`, `\.ton`, `minCuaDong`, `soCotTinh`, `locGiaNcc`, `hetHangHoanToan` —
**0 kết quả cho tất cả**. Popup không đọc, không tính, không tham chiếu bất
kỳ field hay hàm nào liên quan tới Min hay `inv.cong`. Nó chỉ vẽ đúng những
gì `phist/<mã>` đang giữ.

Điểm dễ gây hiểu nhầm, ghi lại để tránh lặp lại: nút mở popup nằm **trên
chính ô Min** (`:6143`), và tooltip dùng chữ *"biểu đồ lịch sử giá"* mà
không nói rõ đó là lịch sử giá NCC hay lịch sử Min. Đây là khoảng cách giữa
UI affordance và dữ liệu thật — hợp lý để giải thích vì sao Owner có thể đã
nghĩ đây là Min history, nhưng bằng chứng code không để lại chỗ mơ hồ.

**3. Có persistent Min history record không? — NO.**

`grep -rniE "minhist|min_hist|history.?min|giaMin|gia.?min|marketmin"` trên
toàn bộ `.js`/`.html`/`.json` của repo B trả về **5 dòng, tất cả đều là
biến `min`/chữ "giá min" trong ngữ cảnh HIỂN THỊ hiện hành**
(`public/index.html:4216,6098,6143`; `:8616,8619` — cột Lệch/xuất XLSX),
**không một dòng nào là write hay read tới một nhánh RTDB lưu trữ lịch sử**.
Không nhánh `minHist`, không field `_c.minHist`, không cấu trúc tương tự
`phist` cho Min ở bất kỳ đâu trong `firebase-database.rules.json` hay mã
nguồn. **Popup này KHÔNG PHẢI Min history** — nó là vendor-price history,
đúng như phần 2 đã chứng minh.

**4. Min có được reconstruct trên popup không? — NO.**

Không một trong bốn bước bắt buộc để tái tính Min cho một ngày lịch sử xuất
hiện ở bất kỳ đâu trong đường đi của popup:

```
NCC filtering (loại trừ _ANC)     : KHÔNG — sups lấy MỌI khoá trong `data`,
                                     kể cả NCC hiện đang bị NCC_RETIRED/
                                     NCC_MIN_LOAI loại khỏi Min
status ok/gone                    : Popup tự suy "gone" từ giá trị `0` để vẽ
                                     dấu ✕ — ĐÂY LÀ HIỂN THỊ, không phải một
                                     bước của công thức Min
outlier filter (NGUONG_BAT_THUONG) : KHÔNG — mọi giá trong phist được vẽ y
                                     nguyên, kể cả giá bất thường mà
                                     locGiaNcc() lẽ ra sẽ loại
inv.cong                          : KHÔNG đọc, đã xác nhận ở mục 2
MIN calculation                   : KHÔNG gọi minCuaDong()/soCotTinh() ở
                                     đâu trong popup
```

⇒ Xác nhận: **"popup chỉ là vendor-price history, không phải historical
MarketMin"** — đúng kết luận mặc định mà đề bài yêu cầu xác minh khi không
tìm thấy các bước trên.

**5. Public Purchase Price History trong popup — NO.**

`inv.cong`/`tp.ton` **không** xuất hiện ở bất kỳ đâu trong `openPhist()`,
`loadPhist()`, `renderPhist()`, `phShow()`, `phHover()`. Ngay cả nếu lịch sử
NCC trong `phist` hoàn hảo tuyệt đối, popup **vẫn không** có đủ input để
dựng lại `_c.min` đúng công thức hiện hành — công thức đó (`DEC-149` §72)
bao gồm `tp.ton` như một input trực tiếp, có thể THẮNG giá NCC.

**6. Historical Min Replay Experiment — CODE ONLY, theo đúng yêu cầu đề bài.**

Câu hỏi: tại một ngày lịch sử D, code hiện tại có trả về `MarketMin(D)` mà
KHÔNG dùng bất kỳ current-state field nào không?

```
KHÔNG CÓ bất kỳ hàm nào trong repo B nhận (ngày lịch sử, phist tới ngày đó)
làm input và trả về Min.

minCuaDong() (price-engine/src/nghiepvu.js:632-637) LÀ một hàm THUẦN (pure
function of its arguments) — về mặt LÝ THUYẾT có thể tái sử dụng cho
replay nếu được truyền đúng input lịch sử. NHƯNG trong PIPELINE HIỆN TẠI,
nó luôn được gọi với:
  - dong = gotDong(row)  — trạng thái board HIỆN TẠI (public/index.html:
    3551-3556), không phải một lát cắt lịch sử
  - an   = _ANC hiện tại  (:3499-3508, dựng từ NCC_RETIRED/NCC_MIN_LOAI
    HIỆN TẠI trong mã nguồn)
  - NGUONG_BAT_THUONG = một hằng số DUY NHẤT (0.3), không có phiên bản
    lịch sử nào khác được lưu ở đâu
```

⇒ **Historical replay = NOT DETERMINISTIC** trong hệ thống HIỆN TẠI, đúng
tiêu chí đề bài đặt ra ("nếu cần current-state field thì NOT DETERMINISTIC")
— xác nhận lại, bằng một góc nhìn khác (audit trực tiếp đường đi của popup
thay vì audit công thức), đúng kết luận Historical Replay = C đã có ở
`DEC-149` §73.

**7. Chart note semantics — xác nhận khớp, với một phân biệt quan trọng.**

Chú thích UI: *"Chỉ ghi mốc khi giá ĐỔI. Ngày không có số nghĩa là giá giữ
nguyên như mốc gần nhất phía trên."*

```
price(product, NCC, D) = last history record with date <= D    ✅ ĐÚNG
                          cho CHART (renderPhist() :6259-6267 — biến `last`
                          giữ giá trị gần nhất qua từng ngày, step-function
                          / last-observation-carried-forward)
```

**Phân biệt phải ghi rõ:** chú thích UI mô tả đúng hành vi của **chart**,
nhưng **KHÔNG đúng cho bảng số bên dưới nó** — `rows` (`:6296-6303`) hiện
`"·"` cho ngày không có record, **không carry-forward**. Cùng một dữ liệu,
hai cách hiển thị khác nhau, chỉ một trong hai khớp mô tả step-function.
Bất kỳ ai xây replay engine dựa trên "logic mà UI tả" phải chọn đúng
`renderPhist()` (chart), không phải bảng, làm tham chiếu — và kể cả khi đó,
đây là logic HIỂN THỊ, không phải một hàm dùng lại được cho tính toán
nghiệp vụ.

**8. Câu hỏi 30 ngày — trả lời lại, sau khi audit trực tiếp popup.**

```
sale_date = 10/08/2026, upload = 10/09/2026 (30 ngày sau)
Hệ thống HIỆN TẠI có lấy chính xác giá Min áp dụng ngày 10/08 không?

→ NO — không đủ history, KHÔNG PHẢI vì popup thiếu chart (nó có), mà vì:
  (a) không hàm nào TÁI TÍNH Min cho một ngày lịch sử tồn tại ở bất kỳ đâu
      trong repo B, kể cả trong chính popup vừa audit;
  (b) input tp.ton/inv.cong không có lịch sử (DEC-148);
  (c) exclusion list + threshold không versioned (DEC-149 §73(d)).
```

Không được trả YES chỉ vì popup có chart — đây chính xác là rủi ro đề bài
cảnh báo, và audit này xác nhận rủi ro đó là có thật: popup CÓ chart, chart
CÓ dữ liệu nhiều mốc (đúng như ảnh Owner cung cấp), nhưng chart đó là của
**giá NCC**, không phải của **Min**.

**9. Nếu PARTIAL — định lượng kiến trúc tối thiểu còn thiếu.**

Xếp hạng NCC-history vào cột "PARTIAL" (có nhưng không đủ), không phải
"đủ" hay "hoàn toàn không có":

```
CÓ SẴN (một phần)  :  phist — lịch sử giá NCC theo ngày, nhưng:
                       - có thể bị sửa/xoá (DEC-147 §54 R4)
                       - không mang trạng thái "NCC có bị loại khỏi Min
                         tại ngày đó không" (chỉ có giá trị giá, không có
                         cờ _ANC lịch sử)

THIẾU HOÀN TOÀN     :  1. inv.cong / tp.ton theo ngày (DEC-148 — 0 lịch sử)
                       2. _ANC (exclusion list NCC) theo ngày — 0 versioning
                       3. NGUONG_BAT_THUONG (ngưỡng outlier) theo ngày —
                          hằng số đơn, 0 versioning
                       4. MỘT HÀM REPLAY thực sự gọi lại minCuaDong() (hay
                          tương đương) với input lịch sử — hiện KHÔNG tồn
                          tại ở bất kỳ đâu, kể cả dưới dạng chưa dùng
```

Không chỉ "cần thêm capture `inv.cong`" như câu hỏi §9 gợi ý — cần thêm
**ba loại capture khác nhau CỘNG một hàm replay mới**. Đây là mức độ thiếu
hụt rộng hơn một chút so với ấn tượng "chỉ thiếu một input" mà việc chỉ xem
qua popum có thể tạo ra.

**10. Client/server Min — không áp dụng cho popup (popup không tính Min),
nhưng áp dụng cho MỌI replay engine tương lai.**

Popup không gọi `minCuaDong()` lẫn `soCotTinh()` — không tính Min nên câu
hỏi "dùng bản nào" không phát sinh cho chính popup. Nhưng đây vẫn là một
ràng buộc thật cho bất kỳ thiết kế replay nào sau này: hai công thức không
hoàn toàn giống nhau (`DEC-149` §72 — `soCotTinh()` bỏ qua bước lọc outlier
pe-6). Một replay engine tương lai dùng lại `minCuaDong()` (client-side,
đầy đủ) sẽ cho số **khác** với những gì CRM/CSV từng nhận trong các giai
đoạn `_c` bị stale (khi `soCotTinh()` chạy fallback) — nghĩa là ngay cả khi
đã capture đủ input lịch sử, "MarketMin(D) mà nhân viên NHÌN THẤY" và
"MarketMin(D) mà CRM ĐÃ NHẬN" có thể là hai số khác nhau tại cùng một ngày,
tuỳ thời điểm `_c` có bị stale hay không lúc đó.

Reason:

**1. Vì sao phiên này ghi là AUDIT FACT, không phải Owner Decision.** Đề bài
yêu cầu tường minh "Không Owner Decision mới trừ khi chỉ ghi audit fact".
Không có quyết định nghiệp vụ nào cần đóng ở đây — chỉ có một khẳng định
kỹ thuật (popup là gì) cần đúng trước khi ai đó dựa vào nó để quyết định gì.

**2. Vì sao kết luận không thay đổi bất kỳ trạng thái nào của `DEC-149`.**
`CONFLICT DETECTED` §71 hỏi về Ý ĐỊNH nghiệp vụ của công thức Min
(`_c.min` có nên bao gồm `cong` hay không). Popup không tính Min nên không
liên quan gì tới công thức đó — nó chỉ là một tính năng hiển thị khác,
song song, đọc một nhánh RTDB khác (`phist` thay vì `board/_c`). Hai câu
hỏi độc lập nhau hoàn toàn.

**3. Vì sao vẫn đáng ghi một DEC dù chỉ là audit fact.** Bằng chứng UI mới
(popup có chart, có nhiều mốc ngày) là loại bằng chứng dễ bị đọc nhầm thành
"vậy là có lịch sử Min rồi, không cần capture gì thêm". Ghi rõ ràng, có
trích dẫn code, ngăn đúng cách đọc nhầm đó lan sang các quyết định sau —
đúng nguyên tắc "agent phải chứng minh bằng artifact và bằng chứng" của
`CLAUDE.md`.

Risk:

`Effective Risk = HIGH` — không đổi. Phiên này không tạo rủi ro mới, nó
**loại bỏ** một khả năng hiểu nhầm cụ thể trước khi nó lan rộng:

- **Rủi ro đã tránh được:** nếu phiên này không audit trực tiếp, và ai đó
  (Owner hoặc một agent khác) coi popup "Lịch sử giá" là bằng chứng đủ để
  bỏ qua việc xây capture layer — hậu quả giống hệt điều `DEC-148`/`DEC-149`
  đã cảnh báo (dữ liệu quá khứ không tái dựng được), chỉ khác là bị trì
  hoãn phát hiện lâu hơn vì "nhìn có vẻ đã có chart rồi".
- **Rủi ro còn lại, không đổi từ DEC-149:** `CONFLICT DETECTED` §71 vẫn
  chưa có câu trả lời từ Owner.

Impact:
- `PROJECT/PROJECT_DECISIONS.md` — DEC này (ID cấp sau khi quét namespace
  toàn repo; `DEC-150` xác nhận trống).
- `PROJECT/PROJECT_PROGRESS.md` — ghi rõ popup là vendor-only; **không** đổi
  bất kỳ trạng thái `BLOCKED`/`READY`/`OWNER_DECISION_REQUIRED` nào.
- `docs/tasks/TASK-108B-eligible-costs-owner-definition.md` — Phần IX.
- `docs/sessions/S027-task-105c-price-history-popup-verification.md` — bàn
  giao phiên.
- **Không** sửa `app/**`, `config/**`, `tests/**`, Golden fixture/expected,
  `TASK-110`, `CHECK-110-16`, `R1-A1`, `governance/**`.
- **Không** sửa repo B (`Tracking`) — 0 file.

Can Revisit After:
- Không đổi so với `DEC-149`: chủ dự án trả lời `CONFLICT DETECTED` §71, và
  xác nhận kiến trúc capture (OPTION B hoặc khác) + tần suất.

## DEC-151

Date:
2026-08-27

Task:
`TASK-105C` — Owner Decision: Historical KPI Purchase Price Scope Reduction.
Ghi trong phiên "TASK-105C — OWNER DECISION: HISTORICAL KPI PURCHASE PRICE
SCOPE REDUCTION" (`docs/sessions/S028-task-105c-historical-kpi-price-scope-reduction.md`).
Diễn ra ngay sau `S027`/`DEC-150` (Reports SHA bắt đầu phiên:
`1908d00f3b578953d68dbcefa80dfd0a816cb000`).

**Đây LÀ một Owner Decision** (khác `DEC-150`, vốn chỉ là audit fact) —
chủ dự án thu hẹp phạm vi nghiệp vụ của `AccountingPurchasePrice` lịch sử,
đóng `CONFLICT DETECTED` mà `DEC-149` §71 để ngỏ.

Repo được audit thêm (một câu hỏi hẹp, xem Reason):
`hoangvinhkta-creator/Tracking` @ `d177363a390d36fe793e0c1c44a6fb6743ca45f5`
(không đổi). **0 file thay đổi.**

Decision:

**1. Reports KHÔNG cố tái dựng `_c.min` lịch sử.** Chủ dự án xác nhận mục
tiêu KHÔNG phải tái dựng chính xác con số `_c.min` đã từng hiển thị trong
Tracking tại mọi thời điểm — đây là một mục tiêu **khác** với mục tiêu thật
của Reports (giá nhập KPI có căn cứ, deterministic, không suy đoán).

**2. Nguồn giá lịch sử duy nhất cho `HistoricalKpiPurchasePrice`:
`phist/<mã>/<NCC>/<YYYY-MM-DD>`.**

```
Price(NCC, D) = record gần nhất có ngày <= D
              (last-observation-carried-forward, đúng khoảng đóng DEC-145 §1)
HistoricalVendorPrice(mã, D) = MIN qua mọi NCC có Price(NCC,D) xác định
                                (loại NCC có Price(NCC,D) = 0 — sentinel
                                "hết hàng", KHÔNG phải giá — DEC-145 §5,
                                DEC-149 §72)
KpiPurchasePrice(mã, D) = HistoricalVendorPrice(mã, D) nếu xác định được
                         = Pending nếu không
```

Không được dùng giá hiện tại áp ngược cho quá khứ — tái xác nhận `DEC-121`.

**3. `inv.cong` (giá nhập công khai) — loại khỏi scope Phase 1.**

Về nghiệp vụ, `inv.cong` VẪN là một nguồn giá độc lập hợp lệ có thể tham
gia Min (không phủ nhận `DEC-148`). Nhưng vì **không có lịch sử**
(`DEC-148` §8, NO GUARANTEED DELAY WINDOW), Owner quyết định:

```
KHÔNG lấy inv.cong HIỆN TẠI áp ngược cho đơn quá khứ.
KHÔNG bắt buộc xây lịch sử inv.cong trong scope hiện tại.
KHÔNG bắt buộc xây MarketMinHistory trong scope hiện tại.
```

**4. Mã không đủ căn cứ lịch sử → `Pending`, KHÔNG suy đoán.**

```
Nếu HistoricalVendorPrice(mã, D) xác định được từ phist → dùng nó.
Nếu KHÔNG (vd. mã lạ chỉ có thể biết giá qua inv.cong hiện tại, mà
inv.cong lịch sử không tồn tại) →
    AccountingPurchasePrice / KpiPurchasePrice = Pending
    KHÔNG tự suy đoán, KHÔNG lấy giá hiện tại,
    KHÔNG nearest/latest ngoài semantics đã duyệt ở mục 2.
    Cho phép xử lý thủ công sau.
```

Chủ dự án xác nhận đây là **hành vi chủ đích**: tần suất Pending thấp và
chi phí xử lý tay thấp hơn đáng kể so với chi phí xây một hệ thống capture
lịch sử chỉ để loại bỏ chúng. Đúng nguyên tắc `DEC-103` (Pending là trạng
thái hệ thống đã biết, không phải lỗi cần vá bằng phỏng đoán).

**5. Manual resolution — ràng buộc bắt buộc, ghi để `TASK-105C`
implementation tuân theo, KHÔNG thiết kế seam trong phiên này.**

```
Phải explicit (một hành động rõ ràng, không suy ra ngầm).
Phải có provenance (ai, khi nào, dựa trên căn cứ gì).
Phải gắn đúng dòng/đơn/mã hàng cụ thể — không áp hàng loạt mù.
KHÔNG được âm thầm sửa nguồn lịch sử (không ghi đè phist).
KHÔNG được rewrite phist.
KHÔNG được biến giá hiện tại thành giá lịch sử (không backdating).
```

**6. `_c.min` — xác nhận KHÔNG phải historical oracle cho Reports.**

`CONFLICT DETECTED` (`DEC-149` §71) được giải — **không phải** bằng cách
chọn (A) hay (B) mà `DEC-149` đưa ra, mà bằng **scope reduction**: câu hỏi
"`_c.min` có đúng nghĩa mà Owner mô tả không" trở nên **không còn liên
quan**, vì Reports không dùng `_c.min` làm nguồn nữa. Lý do chủ dự án nêu,
khớp hoàn toàn với bằng chứng đã audit ở `DEC-148`–`DEC-150`:

```
- _c.min không có lịch sử (DEC-149 §73);
- popup ở ô Min thực tế chỉ hiển thị phist, không phải Min history
  (DEC-150 §81-83);
- _c.min phụ thuộc thêm inv.cong, exclusion list, outlier threshold, và
  current state — các input này không được version đầy đủ (DEC-149 §72-73).
```

**7. Audit hẹp thực hiện TRONG phiên này (yêu cầu bắt buộc của đề bài,
"OUTLIER/NCC FILTERING" mục 1) — `phist` có đủ cho `HistoricalVendorPrice`
deterministic không cần giả định config hiện tại = config lịch sử?**

**Trả lời: CÓ, ĐÚNG NHƯ SEMANTICS Ở MỤC 2 — nhưng bản thân semantics đó cố
ý ĐƠN GIẢN HƠN công thức `_c.min` sống, và điều đó để lại đúng hai câu hỏi
chưa đóng.**

Bằng chứng phần "đủ" (không cần giả định config):
```
- phist GHI BẤT KỂ trạng thái loại trừ: buildSync() xử lý mọi NCC đã dán
  bài, KHÔNG kiểm tra NCC_RETIRED/NCC_MIN_LOAI trước khi ghi ph[...]
  (public/index.html:5100-5203, ghi tại :5171,:5192) — hai danh sách đó
  chỉ ảnh hưởng _c.min, không ảnh hưởng việc phist có ghi hay không.
  ⇒ Dữ liệu giá của một NCC "đã retired hôm nay" hoặc "bị loại khỏi Min
  hôm nay" VẪN có mặt đầy đủ trong phist cho các ngày trước đó — không bị
  thiếu vì lý do exclusion.
- phist key đã fold qua nccKey() TẠI THỜI ĐIỂM GHI (:5119: const ncc =
  nccKey(st.name)) — không cần tra alias "tại thời điểm đọc", record đã
  mang tên chuẩn hoá của chính lúc nó được ghi.
- Semantics mục 2 (Price(NCC,D) = record gần nhất ≤ D, rồi MIN qua mọi NCC
  có giá trị, loại 0-sentinel) là một hàm THUẦN chỉ cần dữ liệu trong
  phist — KHÔNG tham chiếu _ANC, KHÔNG tham chiếu NGUONG_BAT_THUONG. Đây
  chính là lý do nó deterministic: nó CHỦ Ý không đi qua những input
  không-versioned đó.
```

**Hai câu hỏi CÒN MỞ, không tự suy ra (theo đúng yêu cầu đề bài):**

```
Q1 — NCC RETIRED/MIN_LOAI HỒI TỐ:
  Một NCC hiện đang "retired" (NCC_RETIRED) hoặc "loại khỏi Min"
  (NCC_MIN_LOAI) — nếu phist của nó CÓ giá hợp lệ tại ngày D (TRƯỚC khi
  trạng thái đó có hiệu lực), giá đó CÓ được tính vào
  HistoricalVendorPrice(mã, D) hay không?
  Chưa biết TỪ NGÀY NÀO trạng thái retired/MIN_LOAI có hiệu lực (hai danh
  sách này là hằng số mã nguồn, không versioned — DEC-149 §73(d)), nên kể
  cả khi có câu trả lời "có" hay "không", vẫn cần thêm quyết định về
  NGƯỠNG NGÀY áp dụng.

Q2 — OUTLIER THRESHOLD HỒI TỐ:
  Bộ lọc giá bất thường (NGUONG_BAT_THUONG=0.3, thêm pe-6 ngày 24/08/2026,
  vá lỗi đọc nhầm ghi chú trong ngoặc thành giá) — CÓ nên áp dụng cho các
  mốc phist TRƯỚC ngày 24/08/2026 hay không? Lỗi mà pe-6 vá là lỗi ĐỌC DỮ
  LIỆU có thể đã xảy ra trước ngày đó, nên phist trước 24/08 có nguy cơ
  chứa đúng loại giá trị bất thường mà pe-6 tồn tại để loại.
```

Semantics mục 2, đọc đúng nguyên văn, **không lọc gì cả** — đây có thể là
CHỦ Ý của Owner (đơn giản hơn, khác `_c.min` một cách có ý thức) hoặc một
điểm Owner CHƯA nghĩ tới khi mô tả. Không tự chọn cách hiểu nào.

**8. Impact — đánh giá lại `TASK-105B`/`TASK-105C`/`TASK-108B`.**

```
TASK-105B (FilePriceProvider)
    KHÔNG ĐỔI — contract §38 (DEC-145) vẫn là định dạng đúng cho bootstrap/
    fixture/snapshot export, độc lập với quyết định này.

TASK-105C
    Đổi tên khái niệm trọng tâm: KHÔNG còn là "RTDBPriceProvider đọc _c.min
    hay tương đương" — mà là một PROVIDER MỚI đọc TRỰC TIẾP phist theo
    semantics mục 2.
    ĐỀ XUẤT (audit fact, không phải quyết định kỹ thuật mới): tên
    "HistoricalVendorPriceProvider" mô tả đúng bản chất hơn
    "RTDBPriceProvider" — nó không đọc "RTDB nói chung", nó đọc CỤ THỂ
    nhánh phist theo semantics đã chốt. Đặt tên là việc của implementation
    session, không quyết ở đây.
    BLOCKED_BY (còn lại, đã hẹp đáng kể) = [ Q1, Q2 ở mục 7 ]
    KHÔNG còn BLOCKED_BY: schema RTDB (đã audit xong, DEC-147); field nào
    là AccountingPurchasePrice (đã chốt = HistoricalVendorPrice từ phist,
    mục 2-3); capture layer cho inv.cong/_c.min (KHÔNG còn bắt buộc, mục 3).

TASK-108B
    BLOCKED_BY còn lại: [ 1. Q1/Q2 ở mục 7 (ảnh hưởng ĐỘ CHÍNH XÁC, không
    chặn việc mở implementation — có thể dùng mặc định an toàn "không lọc"
    trong lúc chờ); 2. TASK-105B-Q3 (dòng phụ, độc lập, không đổi) ]
    KHÔNG còn BLOCKED_BY: kiến trúc nguồn giá (đã audit xong); capture
    layer (không còn bắt buộc); MarketMinHistory (không còn bắt buộc).
```

**9. Capture-layer/MarketMinHistory/inv.cong-history — KHÔNG bắt buộc
trong Phase 1.** `DEC-149` OPTION B (capture cả `_c.min` lẫn `inv.cong`)
**không còn là khuyến nghị hiện hành** — nó được xây cho một mục tiêu
("tái dựng đúng những gì `_c.min` từng hiển thị") mà mục 1 của quyết định
này vừa loại bỏ. Đây là **Owner Decision làm giảm phạm vi kiến trúc** so
với `DEC-149` §78, không phải một audit tìm ra sai sót ở `DEC-149` — số đo
tại thời điểm đó (thiếu lịch sử `_c.min`/`inv.cong`) vẫn đúng, chỉ là mục
tiêu cần nó đã đổi.

Reason:

**1. Vì sao đây là scope reduction, không phải chọn (A)/(B) của `DEC-149`
§71.** Cả (A) và (B) đều giả định Reports PHẢI dùng `_c.min` (hoặc một biến
thể vendor-only của nó) làm nguồn. Owner bác bỏ chính giả định đó ở mục 1 —
không chọn nhánh nào trong nhị phân cũ, mà đổi câu hỏi. Đây là lý do
`CONFLICT DETECTED` đóng được mà không cần Owner giải thích ý định thật sự
của công thức `min(vendor, cong)` trong `minCuaDong()` — câu hỏi đó không
còn áp dụng.

**2. Vì sao Pending-với-tần-suất-thấp là một quyết định hợp lệ, không phải
né tránh.** `DEC-103` đã xác lập nguyên tắc Pending là trạng thái hệ thống
ĐÃ BIẾT, ưu tiên hơn suy đoán. Quyết định này áp đúng nguyên tắc đó vào một
trường hợp cụ thể: chi phí xây capture layer (nhiều thành phần, theo
`DEC-149`/`DEC-150`: `inv.cong` history + exclusion-list history + threshold
history + một hàm replay mới) so với chi phí xử lý tay một số lượng nhỏ
trường hợp Pending — Owner chọn phương án rẻ hơn, đúng thẩm quyền nghiệp vụ
của Owner, không phải một khoảng trống kỹ thuật.

**3. Vì sao Q1/Q2 phải ở lại là câu hỏi mở, không tự trả lời.** Đề bài yêu
cầu tường minh "Không được tự động giả định rằng current _ANC/NCC_RETIRED/
NCC_MIN_LOAI/NGUONG_BAT_THUONG có thể áp ngược cho toàn bộ lịch sử" và
"Không tự suy ra". Cả hai câu hỏi đều là quyết định NGHIỆP VỤ về việc dữ
liệu lịch sử "đáng tin đến đâu", không phải câu hỏi kỹ thuật có thể suy ra
từ code — code chỉ cho biết CÁC DANH SÁCH ĐÓ KHÔNG VERSIONED (đã xác nhận
ở `DEC-149`), không cho biết Owner MUỐN áp dụng chúng hồi tố hay không.

Risk:

`Effective Risk = HIGH` — **không đổi**, chấm theo data path (V4.1 §4).
Quyết định này **làm giảm rủi ro kiến trúc** (loại bỏ yêu cầu xây capture
layer phức tạp) nhưng **giữ nguyên** rủi ro data-path gốc:

```
Price sai → KpiPurchasePrice sai → EligibleKpiProfit sai → CR sai → KPI/lương sai
```

Rủi ro cụ thể của chính quyết định này:

- **Q1/Q2 để mặc định sai khi implement.** Nếu `TASK-105C` implementation
  tự chọn "có lọc" hay "không lọc" mà không đánh dấu rõ đó là GIẢ ĐỊNH TẠM
  (không phải quyết định Owner), một lượt review sau này có thể tưởng nhầm
  đó đã là quyết định cuối. Giảm nhẹ: khuyến nghị mặc định AN TOÀN (đúng
  y văn bản mục 2, không lọc gì) và ghi provenance `assumption:
  no-retroactive-filtering-pending-owner-answer` trên MỌI record cho tới
  khi có câu trả lời.
- **`phist` vẫn sửa/xoá được** (`DEC-147` §54 R4) — quyết định này KHÔNG
  thay đổi thực tế đó. Một `HistoricalVendorPriceProvider` đọc `phist`
  trực tiếp vẫn kế thừa rủi ro "báo cáo in lại hai lần ra hai số khác nhau"
  nếu `phist` bị sửa giữa hai lần in — `TASK-105C` implementation PHẢI có
  cơ chế đóng băng/snapshot dữ liệu ĐÃ DÙNG cho một báo cáo cụ thể, không
  chỉ đọc `phist` sống mỗi lần chạy lại.
- **`NCC_ALIAS` không hồi tố** (xem Evidence V-03/V-04, `S028`) — rủi ro
  thấp hiện tại (một cặp alias duy nhất) nhưng là món nợ kỹ thuật cần ghi
  vào `TASK-105C` implementation: nếu alias mới thêm sau, cần bước migrate
  `phist`, nếu không `HistoricalVendorPrice` sẽ bỏ sót giá dưới tên cũ.

Impact:
- `PROJECT/PROJECT_DECISIONS.md` — DEC này (ID cấp sau khi quét namespace
  toàn repo; `DEC-151` xác nhận trống).
- `PROJECT/PROJECT_PROGRESS.md` — đóng blocker "kiến trúc nguồn giá chưa rõ"
  và "field nào là AccountingPurchasePrice"; mở blocker mới hẹp hơn (Q1/Q2);
  gỡ yêu cầu capture-layer/MarketMinHistory/inv.cong-history khỏi Phase 1.
- `PROJECT/LO_TRINH_DE_HIEU.md` — cập nhật bước 11b theo scope mới, bằng
  ngôn ngữ phổ thông.
- `PROJECT/REVIEW_BUDGET_LEDGER.md` — ghi nhận Owner Decision làm giảm scope
  kiến trúc của lineage `TASK-105B`/`TASK-105C`; **không** tiêu repair cycle
  (đây là Owner Decision recording, không phải repair).
- `docs/tasks/TASK-108B-eligible-costs-owner-definition.md` — Phần X.
- `docs/sessions/S028-task-105c-historical-kpi-price-scope-reduction.md` —
  bàn giao phiên.
- **Không** sửa `app/**`, `config/**`, `tests/**`, Golden fixture/expected,
  `TASK-110`, `CHECK-110-16`, `R1-A1`, `governance/**`.
- **Không** sửa repo B (`Tracking`) — 0 file.

Can Revisit After:
- Chủ dự án trả lời Q1 (NCC retired/MIN_LOAI hồi tố) và Q2 (outlier
  threshold hồi tố) ở mục 7 ⇒ mở `TASK-105C` implementation với
  `docs/tasks/TASK-105C-*.md` (Scope Lock + Completion Gate), thiết kế seam
  manual-resolution theo ràng buộc mục 5.
- Nếu sau này có nhu cầu nghiệp vụ MỚI cần dùng `inv.cong`/`_c.min` (vd. mở
  rộng ngoài Phase 1) ⇒ `DEC-149` OPTION B quay lại làm khuyến nghị hợp lệ,
  không cần audit lại từ đầu.

## DEC-152

Date:
2026-08-27

Task:
`TASK-105C` — Final Owner Decision + Implementation Scope Lock. Ghi trong
phiên "TASK-105C — FINAL OWNER DECISION + IMPLEMENTATION SCOPE LOCK"
(`docs/sessions/S029-task-105c-final-decision-scope-lock.md`). Diễn ra
ngay sau `S028`/`DEC-151` (Reports SHA bắt đầu phiên:
`e8f4405998dd216bbed56ed03d9227431021b6cc`).

**Đây LÀ một Owner Decision** (đóng hai câu hỏi filtering còn mở từ
`DEC-151` §7) **cộng** một Scope Lock/Completion Gate kỹ thuật (thẩm quyền
của phiên viết task spec, không phải Owner Decision).

Repo được audit thêm (không thay đổi):
`hoangvinhkta-creator/Tracking` @ `d177363a390d36fe793e0c1c44a6fb6743ca45f5`.
**0 file thay đổi.**

Decision:

**1. Q1 — NCC retired/MIN_LOAI hồi tố — CLOSED.**

```
Trạng thái NCC HIỆN TẠI (nghỉ, NCC_RETIRED, NCC_MIN_LOAI, hay không còn
dùng trong bảng giá) KHÔNG được áp ngược về quá khứ.

Nếu tại ngày D, phist/<mã>/<NCC> có record hợp lệ theo
Price(NCC,D) = record gần nhất có date <= D, thì giá đó VẪN là candidate
của HistoricalVendorPrice(D) — bất kể trạng thái NCC đó hôm nay ra sao.
```

**2. Q2 — Outlier threshold hồi tố — CLOSED.**

```
NGUONG_BAT_THUONG (ngưỡng lọc giá bất thường hiện tại, thêm pe-6,
24/08/2026) KHÔNG được áp ngược cho dữ liệu trước khi rule đó có
historical authority.

Phase 1 HistoricalVendorPrice:
  candidates(D) = mọi NCC có historical price hợp lệ tại D (loại sentinel
                  0 = hết hàng)
  HistoricalVendorPrice(D) = MIN(candidates(D))
  Không có candidate hợp lệ → HistoricalVendorPrice = None → Pending

Không dùng: current _c.min; current inv.cong; current NCC exclusion
config; current outlier threshold để sửa quá khứ; nearest future price;
current price; suy đoán.
```

**3. Data quality / outlier — ghi nhận, không mở rộng scope.** Một
historical vendor price cực thấp không được âm thầm loại bỏ bằng outlier
rule hiện tại (đúng Q2). Một tín hiệu diagnostic/review CÓ THỂ được tạo
sau này nếu không đổi kết quả nghiệp vụ, nhưng KHÔNG được tự thay
`HistoricalVendorPrice`, KHÔNG biến warning thành exclusion, và KHÔNG mở
rộng `TASK-105C` để xây hẳn một review system trong Phase 1 — ghi
HARDENING/BACKLOG.

**4. Phase 1 Price Authority — chốt cuối, không đổi từ `DEC-151`.**

```
Canonical: phist/<MÃ>/<NCC>/<YYYY-MM-DD>
Lookup: Price(NCC,D) = giá tại record có max(record_date) <= D
HistoricalVendorPrice = min(valid_prices) nếu valid_prices khác rỗng,
                         else None
KHÔNG dùng _c.min. KHÔNG dùng inv.cong trong Phase 1. KHÔNG backdate.
```

**5. Product identity — dependency được đặt tên tường minh, không tự vá.**
Đường `Reports sale line → canonical product identity → Tracking <MÃ> →
phist` **không có** mapping production đáng tin cậy hôm nay. Xác nhận lại
`DEC-147` §56: Tracking có mã ổn định, nhưng đó là khoá CỦA TRACKING —
không khớp trực tiếp `product_raw` của Reports. Repo B đã thử fuzzy-style
matching (`extractCode()`) trên đúng loại dữ liệu này và **bỏ hẳn** vì sai
trên tài sản thật (`DEC-147` §56) — tiền lệ production ủng hộ lệnh cấm
fuzzy matching của `OD-105B-01` §B.

⇒ **Quyết định:** `HistoricalVendorPriceProvider.lookup(product_code,
sale_date)` đòi `product_code` **đã là** một `<MÃ>` Tracking được giải
quyết chắc chắn. Không tự dịch, không đoán. Mapping không xác định chắc
chắn ⇒ `Pending`. Việc xây bảng dịch `product_raw` ↔ `<MÃ>` là một
**dependency riêng, chưa mở, chưa có task ID** — ghi rõ ở
`docs/tasks/TASK-105C-historical-vendor-price-provider.md`, không phát
minh fuzzy matching để né nó.

**6. Snapshot/reproducibility — minimum mechanism, không xây database
mới.** `fetch (Tracking RTDB, read-only, ngoài app/modules/) → normalize
(hàm thuần trong app/modules/pricing/) → file snapshot BẤT BIẾN (không
ghi đè) → HistoricalVendorPriceProvider đọc đúng một capture_id cụ thể`.
Một report cụ thể ghim vào đúng một `capture_id`; chạy lại sau này đọc lại
đúng file đó, miễn nhiễm với việc `phist` bị sửa/xoá sau đó (`DEC-147` §54
R4 vẫn đúng — đây là cơ chế đối phó, không phải phủ nhận rủi ro). Không
yêu cầu sửa Tracking. Không biến `TASK-105C` thành một hệ database mới.

**7. Manual Pending — chỉ cần seam, không cần implement toàn bộ UI.**
`TASK-105C` xác định **contract** (record đầu ra mang đủ provenance để
resolve tay sau này bám đúng dòng/đơn/mã) nhưng **không bắt buộc** implement
toàn bộ quy trình xử lý tay trong phiên implementation của `TASK-105C`.

**8. Canonical task spec — tạo mới.**
`docs/tasks/TASK-105C-historical-vendor-price-provider.md` — 24 mục đầy đủ
theo yêu cầu (Purpose; Business semantics; Historical authority; Product
identity contract; Date lookup; Sentinel; Multi-NCC MIN; Missing-data/
Pending; Reproducibility/snapshot; Provenance; Error semantics; RTDB
boundary; Reports/Tracking boundary; No-fuzzy-matching; No-backdating;
Test strategy; Golden impact; Risk classification; Review Budget; Scope
Lock; Completion Gate; Out-of-scope; Dependency map; TASK-108B handoff).

**9. Scope Lock — FROZEN.** Phạm Vi / Ngoài Phạm Vi / Phạm Vi Tác Động Dự
Kiến ghi trong file task, cùng thẩm quyền với `DEC-152` này. Sửa sau khi
frozen phải qua `SCOPE EXPANSION REQUIRED`, không âm thầm.

**10. Completion Gate — FROZEN, 20 check.** `CHECK-105C-01`…`CHECK-105C-20`
map trực tiếp A–T của đề bài audit gốc: exact lookup; carry-forward ≤ D;
không lấy future record; loại sentinel 0; multi-NCC MIN; retired NCC
không đổi lịch sử; exclusion config hiện tại không rewrite lịch sử;
outlier rule hiện tại không rewrite lịch sử; `_c.min` không được đọc;
`inv.cong` không backdate; missing history → Pending; mapping mơ hồ →
Pending; không fuzzy matching; VND boundary đúng biên; deterministic
snapshot/replay; provenance đủ truy ngược; source failure ≠ determined
absence; Tracking repo không bị sửa; Golden không bị rewrite; full
regression không phát sinh mới. Toàn bộ `Status = NOT_TESTED` (chưa
implementation, đúng `EVIDENCE_STANDARD` — không được khẳng định PASS mà
không có bằng chứng thật).

**11. Kiến trúc thực thi (quyết định kỹ thuật của phiên, không phải Owner
Decision).** `HistoricalVendorPriceProvider` **compose** `FilePriceProvider`
(đọc file snapshot 4-cột đã sinh) thay vì viết lại validation/parsing.
Script fetch mạng (`tools/pricing/export_historical_vendor_prices.py`)
tách hẳn khỏi `app/modules/pricing/`, giữ đúng ranh giới `ADR-101` (không
mạng trong Phase 1 core). Đây là lựa chọn "ít thay đổi nhất mà vẫn đảm bảo"
đúng tinh thần `DEC-149` §78/OPTION D — tái dùng nguyên vẹn validation đã
có thẩm quyền từ `DEC-145` thay vì nhân đôi logic.

**12. Verdict.**

```
TASK-105C
    SEMANTIC_DEFINITION = COMPLETE
    SCOPE_LOCK           = COMPLETE
    IMPLEMENTATION        = READY
    (chờ TASK-105B DONE trước/cùng lúc — dependency cứng, không phải
    blocker mới)

TASK-105B
    KHÔNG ĐỔI — vẫn READY về kỹ thuật, CHƯA implement. Trở thành
    dependency BẮT BUỘC (không chỉ "khuyến nghị") cho TASK-105C, vì
    HistoricalVendorPriceProvider compose nó.

TASK-108B
    BLOCKED_BY = [ 1. TASK-105C implementation; 2. product identity
                   mapping (dependency mới đặt tên, chưa mở task);
                   3. TASK-105B-Q3 ]
    KHÔNG còn BLOCKED_BY: bất kỳ câu hỏi filtering/kiến trúc/field-
    selection nào — toàn bộ đã đóng qua DEC-147→152.
```

Reason:

**1. Vì sao Q1/Q2 đóng theo hướng "không lọc gì" thay vì thử đoán ý Owner
đã lọc sẵn.** Đề bài (và `DEC-151` trước đó) đã tường minh cấm suy đoán
business rule filtering từ code — hai câu hỏi đó CHỈ có thể đóng bằng lời
Owner trực tiếp, không phải bằng phân tích thêm. Owner chọn "không lọc" —
đơn giản nhất, khớp đúng semantics literal mà chính Owner đã mô tả ở
`DEC-151` §3/§4 mà không thêm điều kiện nào.

**2. Vì sao product identity mapping được đặt tên là dependency thay vì
được "giải quyết tạm" bằng text-matching.** `TASK-105`'s tiền lệ interim
("dùng `product_raw` làm khoá tạm") hoạt động cho `FilePriceProvider` vì
đó là một không gian khoá TỰ NHẤT QUÁN (Reports tự đặt tên trong file của
chính mình). Nó KHÔNG hoạt động cho `HistoricalVendorPriceProvider` vì
`phist` sống trong không gian khoá CỦA TRACKING (`<MÃ>`) — một hệ thống
khác, độc lập. Đánh đồng hai tình huống sẽ lặp lại đúng lỗi
`extractCode()` đã thất bại.

**3. Vì sao chọn compose `FilePriceProvider` thay vì một class hoàn toàn
mới.** Giảm bề mặt cần review/test (validation 4-cột đã qua `CHECK-105B-
01`…`16`), và giữ đúng ranh giới `ADR-101` một cách tự nhiên: phần duy nhất
chạm mạng (`tools/pricing/`) không cần nằm trong `app/modules/`, nên không
đe doạ tính "thư viện Python thuần" của Phase 1.

Risk:

`Effective Risk = HIGH` — không đổi (V4.1 §4, data path). Quyết định này
KHÔNG làm rủi ro cao hơn hay thấp hơn; nó khoá lại chính xác những gì cần
đúng trước khi code chạm vào con số ảnh hưởng lương.

Rủi ro cụ thể của chính bản ghi này:

- **Q1/Q2 "không lọc gì" có thể cho ra giá thấp bất thường (garbage NCC
  quote) làm `HistoricalVendorPrice` sai trong một số ít trường hợp.**
  Đây là đánh đổi CÓ Ý THỨC của Owner (mục 3 ở trên) — chấp nhận trong
  Phase 1, có đường mở review signal sau nếu cần, không tự vá bây giờ.
- **Nếu implementation sau này tự tiện thêm fuzzy matching để "tăng tỉ lệ
  khớp mã"** — vi phạm trực tiếp `CHECK-105C-13` và `OD-105B-01` §B. Giảm
  nhẹ: check đã có sẵn trong Completion Gate frozen, không cần đợi review
  phát hiện.
- **`TASK-105B` chưa DONE nhưng `TASK-105C` đã Scope Lock** — rủi ro thứ tự
  công việc, không phải rủi ro dữ liệu: nếu `TASK-105B` implement khác đi
  so với contract `DEC-145` (không nên xảy ra vì đã frozen từ trước), việc
  compose sẽ phải điều chỉnh. Giảm nhẹ: ghi rõ ở Dependencies/Ready Gate
  của file task, không giả định `TASK-105B` đã xong.

Impact:
- `PROJECT/PROJECT_DECISIONS.md` — DEC này (ID cấp sau khi quét namespace
  toàn repo; `DEC-152` xác nhận trống).
- `docs/tasks/TASK-105C-historical-vendor-price-provider.md` — file MỚI,
  canonical spec, Scope Lock + Completion Gate frozen tại DEC này.
- `PROJECT/PROJECT_PROGRESS.md` — đóng Q1/Q2; `TASK-105C` chuyển
  `SEMANTIC_DEFINITION = COMPLETE`, `SCOPE_LOCK = COMPLETE`,
  `IMPLEMENTATION = READY`.
- `PROJECT/LO_TRINH_DE_HIEU.md` — cập nhật bước 11b, đóng hai câu hỏi nhỏ
  còn lại bằng ngôn ngữ phổ thông.
- `PROJECT/REVIEW_BUDGET_LEDGER.md` — ghi nhận; không tiêu repair cycle
  (Scope Lock recording, không phải repair).
- `docs/tasks/TASK-108B-eligible-costs-owner-definition.md` — Phần XI (con
  trỏ ngắn tới file task mới, không lặp nội dung).
- `docs/sessions/S029-task-105c-final-decision-scope-lock.md` — bàn giao.
- **Không** sửa `app/**`, `config/**`, `tests/**`, Golden fixture/expected,
  `TASK-110`, `CHECK-110-16`, `R1-A1`, `governance/**`.
- **Không** sửa repo B (`Tracking`) — 0 file.

Can Revisit After:
- `TASK-105C` implementation thật chạy — session sau, dùng đúng Scope Lock
  + Completion Gate đã frozen ở đây. Không đổi Completion Gate mà không
  qua `COMPLETION GATE CHANGE PROPOSAL`.
- Product identity mapping có lời giải (task riêng, hoặc Owner cấp bảng
  trực tiếp) ⇒ `TASK-108B` hết blocker thứ 2.

## DEC-153

Date:
2026-08-28

Task:
TASK-105B — Freeze Finalization (phiên "FREEZE + CONTROLLED INTEGRATION",
thẩm quyền riêng theo `governance/core/V4_1_POLICY_FREEZE.md` §12 — State
Authority Matrix: `FROZEN` chỉ được ghi bởi authorized Freeze Finalization
session, không phải bởi reviewer/reconciliation session read-only).

Decision:

`TASK-105B = FROZEN`.

```
Implementation SHA (frozen artifact) : c22cef8b47ac4cd71ef49609066a362c9e604313
Reconciliation SHA (review evidence) : 95a7ae6c3c694a7095ecb2adc6041785c3960096
Review A SHA (preserved, canonical path)     : be2e35c908921f16e8347ecdfd23e2f9aecf1069
Review B SHA (preserved, archived byte-identical) : b735dace8bdbaea086b37f8c20e091cafbed03e5
Reconciled Verdict                    : PASS — ELIGIBLE_FOR_FREEZE
BLOCKING                              : 0
Completion Gate                       : 17/17 REQUIRED PASS (E1 tối thiểu
                                        toàn bộ; CHECK-105B-12, check chạm
                                        Golden, đạt E2 — đúng ngưỡng
                                        `governance/core/EVIDENCE_STANDARD.md`
                                        cho Effective Risk HIGH: E1 bắt buộc,
                                        E2 hướng tới cho check
                                        security/data-adjacent, không phải
                                        toàn bộ 17 check)

Evidence (đọc lại từ canonical, không re-run trong phiên Freeze — reconciliation
đã E2-verify bằng git evidence trực tiếp):
    Targeted (test_file_price_provider.py) : 33 passed
    Golden (test_golden_baseline.py)       : 58 passed, 2 skipped (không đổi)
    Full suite tại implementation          : 730 passed, 11 skipped
    Baseline trước implementation          : 697 passed, 11 skipped
    Regression delta                       : +33 passed, 0 failures, 0 new skips
    Reference integrity                    : đúng 3 lỗi tiền tồn TASK-REM-T06,
                                              0 regression mới
    4 file production lõi (app/pipeline.py, price_engine.py, provider.py,
    models.py) diff so với trước implementation : 0

Review Budget (root task TASK-105B, dùng chung TASK-105C):
    allowed   = 2
    used      = 0
    remaining = 2  (KHÔNG ĐỔI — hai Independent Review PASS song song +
                    một phiên reconciliation không phải remediation cycle,
                    V4.1 §3: cycle tính theo LẦN SỬA, không theo số review)

HARDENING preserved (canonical namespace sau reconciliation,
docs/reviews/TASK-105B-INDEPENDENT-REVIEW-RECONCILIATION.md §3.2):
    HB-105B-03, HB-105B-05, HB-105B-06, HB-105B-07, HB-105B-08, HB-105B-10
    — không blocking freeze.
    HB-105B-04 : reconciled = OUT_OF_SCOPE (không phải HARDENING).
    HB-105B-09 : SUPERSEDED, duplicate_of HB-105B-03.
    HB-105B-11 : SUPERSEDED, duplicate_of HB-105B-06.
    HB-105B-01, HB-105B-02 : thuộc TASK-108B (pre-existing) — không đổi,
    không thuộc lineage HARDENING của TASK-105B.
```

Đóng băng kể từ quyết định này:

- `app/modules/pricing/file_price_provider.py` tại đúng nội dung SHA
  `c22cef8b47ac4cd71ef49609066a362c9e604313` — **frozen**, không sửa ngoài
  một repair cycle mới có thẩm quyền, hoặc `COMPLETION GATE CHANGE
  PROPOSAL` hợp lệ.
- `tests/test_file_price_provider.py` tại cùng SHA — **frozen**.
- Scope Lock + Completion Gate của `docs/tasks/TASK-105B-file-price-provider.md`
  — **frozen** (đã frozen từ phiên implementation, quyết định này không mở
  lại).
- `HB-105B-07` (NaN → `decimal.InvalidOperation` thô) và `HB-105B-08`
  (`Infinity` được chấp nhận làm giá hợp lệ) — **RE-TRIGGER CONDITION giữ
  nguyên, KHÔNG downgrade, KHÔNG xoá**: nâng lên BLOCKING và phải sửa
  **TRƯỚC** khi (a) một bảng giá production thật được nạp qua
  `FilePriceProvider`, HOẶC (b) `TASK-105C` implementation bắt đầu, HOẶC
  (c) `FilePriceProvider` được truyền vào `run_import()` ngoài test — điều
  kiện nào tới trước. Xử lý `HB-105B-08` (im lặng, nặng hơn) trước
  `HB-105B-07` nếu cả hai cùng re-trigger.

Rationale:

Reconciliation session (`95a7ae6`) đã xác minh độc lập bằng git evidence:
cả hai Independent Review target đúng `c22cef8` (`merge-base` = implementation
SHA); 17/17 REQUIRED Completion Gate check PASS ở cả hai bên, cùng số liệu
regression/Golden; namespace `HB-105B-*` đã dedupe, một ID collision thật
(Review B tái dùng `HB-105B-01`/`02` vốn thuộc `TASK-108B`) đã sửa về
canonical ID không collision; một classification disagreement
(`HB-105B-04`) đã giải quyết theo đúng normative Scope Lock table đã
frozen, không ảnh hưởng Freeze eligibility. 0 BLOCKING sau reconciliation.
Theo State Authority Matrix (`governance/core/V4_1_POLICY_FREEZE.md` §12),
verdict `PASS — ELIGIBLE_FOR_FREEZE` thuộc thẩm quyền independent
reviewer/reconciliation; `FROZEN` thuộc một phiên Freeze Finalization có
thẩm quyền riêng — đây chính là phiên đó. Quyết định này **không** review
lại technical correctness, chỉ ghi nhận việc niêm phong dựa trên verdict
reconciled đã có.

Risk:

Nếu ai đó đọc `FROZEN` thành `DONE`, đó là đọc sai — `DONE` còn cần
Controlled Integration + state reconciliation hoàn tất (xem phần Integration
của phiên này, nếu có). Nếu ai đó đọc `FROZEN` thành cấp phép bắt đầu
`TASK-105C` implementation hoặc kích hoạt `FilePriceProvider` thật vào
`run_import()` mà **chưa** sửa `HB-105B-07`/`HB-105B-08` trước, đó là vi
phạm trực tiếp điều kiện re-trigger đi kèm verdict PASS này — không phải
gợi ý, là điều kiện bắt buộc.

Impact:
- Không sửa `app/**`, `tests/**`, `config/**`.
- Chỉ ghi quyết định này + cập nhật state/progress cần thiết trong cùng
  phiên (`PROJECT/PROJECT_PROGRESS.md`, `PROJECT/LO_TRINH_DE_HIEU.md`,
  `PROJECT/REVIEW_BUDGET_LEDGER.md`, `docs/tasks/TASK-105B-file-price-provider.md`
  — chỉ trường `Status` ở Metadata, không sửa Scope Lock/Completion Gate).
- Review Budget lineage `TASK-105B` giữ nguyên `2 allowed / 0 used / 2
  remaining` — freeze không tiêu cycle.

Can Revisit After:
- Một Repair Cycle mới có thẩm quyền riêng (không tự mở trong phiên Freeze
  Finalization/Integration), hoặc một Owner Decision khác thay đổi
  `FilePriceProvider` contract.
- `TASK-105B` PRICE-PARSER MICRO-HARDENING (re-trigger bắt buộc của
  `HB-105B-07`/`HB-105B-08`) — phải chạy **trước** `TASK-105C`
  implementation hoặc trước `FilePriceProvider` activation thật, tuỳ điều
  kiện nào tới trước.

## DEC-154

Title:
PRODUCT IDENTITY & PURCHASE PRICE RESOLUTION

Date:
2026-08-28

Task:
Governance / Specification Reconciliation cho `TASK-105B`, `TASK-105C`,
`TASK-105D` và price-resolution dependency graph.

Decision:

**1. Cutover.**

```text
CUTOVER_DATE = 2026-09-01
```

Phân loại bằng `sale_date`, không dùng `import_date`; do đó bản ghi đến muộn
vẫn đi đúng nhánh lịch sử của ngày bán.

**2. Pre-cutover authority.** Với `sale_date < CUTOVER_DATE`, nếu report
lịch sử đã được Owner xác nhận có product identity và purchase price, report
đó là authority và bypass resolver/catalog/price-provider:

```text
mapping_source = HISTORICAL_CONFIRMED_REPORT
price_source   = HISTORICAL_CONFIRMED_REPORT
```

Không remap/backfill từ catalog hiện tại và không rewrite dữ liệu lịch sử nếu
chưa có correction workflow/authority tường minh. Thiếu confirmation đủ căn
cứ → Pending/correction workflow, không tự dựng lại.

**3. Post-cutover product identity.** Với `sale_date >= CUTOVER_DATE`,
canonical identity là tuple:

```text
(namespace, source_product_code)
namespace ∈ {TRACKING, PUBLIC_PURCHASE}
```

`TRACKING:X` và `PUBLIC_PURCHASE:X` không collision. Sản phẩm hợp lệ cho
Reports **không bắt buộc** tồn tại trong Tracking. Tracking MISS + Public
Purchase deterministic unique match → `PUBLIC_PURCHASE:<code>`, không tạo
Tracking product giả. Không nguồn nào chắc chắn → `PENDING_PRODUCT`.

**4. Product-resolution authority.** Resolution chạy trên DISTINCT product
identities, không trên từng sales row. Alias đã confirm được persist/reuse với
0 thao tác lặp; deterministic unique match có thể auto-resolve; fuzzy/model
similarity chỉ rank candidate và không được tự cấp production authority. Một
confirmation áp cho mọi affected rows/orders cùng identity. Rejection được
nhớ tới khi có evidence mới. Raw accounting product name bất biến; normalized
name/model token chỉ là matching aid, không phải canonical ID. Correction giữ
old/new mapping, actor, timestamp, reason và version. Duplicate import/retry
phải idempotent; conflicting concurrent confirmation không được silent
last-write-wins.

**5. Cross-system product mapping.** Tạo contract persistent tương đương:

```text
TRACKING:<tracking_code> ↔ PUBLIC_PURCHASE:<public_purchase_code>
```

Không giả định code bằng nhau. Mapping explicit, persistent, reusable,
auditable, correctable và versioned. Nó cho phép identity TRACKING dùng giá
Public Purchase fallback mà không đổi namespace của identity.

**6. Identity/price separation.** Product mapping lưu identity, không lưu
fixed purchase price. Price source thay đổi không tự đổi product identity.

**7. Price precedence.**

```text
TRACKING identity:
  1. HistoricalVendorMin (TASK-105C)
  2. PublicPurchasePrice qua CrossSystemProductMapping (TASK-105B)
  3. Pending

PUBLIC_PURCHASE identity:
  1. PublicPurchasePrice (TASK-105B)
  2. Pending
```

`PUBLIC_PURCHASE` identity bypass `phist`. `TRACKING` identity chỉ fallback
sang Public Purchase khi không có valid vendor candidate tại `sale_date` và
có cross-system mapping hợp lệ.

**8. Historical vendor semantics được bảo toàn.** `DEC-151`/`DEC-152` vẫn là
authority cho nhánh Tracking:

```text
Price(NCC,D) = record có ngày gần nhất <= D
HistoricalVendorMin(D) = MIN mọi candidate hợp lệ tại D
phist value 0 = sentinel unavailable / HẾT HÀNG, loại khỏi candidates
```

Trạng thái NCC/config hiện tại không áp ngược. Không candidate → absence để
price resolution thử Public Purchase fallback; nếu fallback cũng không có →
Pending. `0` không bao giờ trở thành zero-cost purchase.

**9. Public Purchase price semantics.** Public Purchase dataset phải
effective-dated hoặc snapshot/versioned đủ để replay:

```text
product_code
effective_from
effective_to
purchase_price
source/provenance
```

Lookup dùng `sale_date`. Current/today price không được backfill sale lịch sử.
Không có valid price tại ngày bán → Pending.

**10. Provenance không được collapse.** Tối thiểu giữ riêng:

```text
PUBLIC_PURCHASE_NO_TRACKING
PUBLIC_PURCHASE_NO_VENDOR_PRICE
```

Tên enum implementation có thể theo convention repo, nhưng audit meaning
phải phân biệt direct Public Purchase identity với fallback price của identity
Tracking.

**11. Price-resolution acceptance rules (P01–P10).** Đây là canonical
integration contract; implementation owner chưa được tự mở trong phiên này:

| ID | Rule |
|---|---|
| P00 | `sale_date < CUTOVER_DATE` + entry `HistoricalConfirmedRegistry` CONFIRMED → `HISTORICAL_CONFIRMED_REPORT`, bypass toàn bộ P01–P11; không có entry → Pending. P01–P11 CHỈ áp dụng cho `sale_date >= CUTOVER_DATE` |
| P01 | TRACKING + valid vendor candidates → `HistoricalVendorMin` |
| P02 | sentinel `0` bị loại |
| P03 | TRACKING + no valid vendor candidates **+ `CrossSystemProductMapping` CONFIRMED active** → Public Purchase fallback, tra bằng `public_purchase_code` **của chính mapping đó** |
| P04 | PUBLIC_PURCHASE identity → bypass `phist` |
| P05 | Public Purchase lookup dùng `sale_date` |
| P06 | no valid Public Purchase price → Pending |
| P07 | current public price không silently backfill historical sale |
| P08 | provenance `PUBLIC_PURCHASE_NO_TRACKING` được giữ |
| P09 | provenance `PUBLIC_PURCHASE_NO_VENDOR_PRICE` được giữ |
| P10 | identity không đổi chỉ vì price source đổi |
| P11 | TRACKING + no valid vendor candidates + **KHÔNG** có `CrossSystemProductMapping` → Pending; tuyệt đối không đoán mã Public Purchase |

> **Sửa transcription 2026-08-28 (S034, `DEC-155` — HB-154-01/HB-154-03).**
> `P00`, `P11` là dòng MỚI và `P03` được bổ sung điều kiện, **không thêm ngữ
> nghĩa mới**: cả ba chép lại đúng những gì §2 và §7 của chính quyết định này
> đã quy định trong prose (§7: "TRACKING identity chỉ fallback sang Public
> Purchase khi không có valid vendor candidate tại `sale_date` **và có
> cross-system mapping hợp lệ**"; §7 danh sách precedence: "3. Pending"; §2:
> pre-cutover confirmed report bypass). Bảng ban đầu chép thiếu. Đây là
> "divergence phải được báo cáo và sửa bằng authority hợp lệ" theo
> `governance/core/V4_1_POLICY_FREEZE.md` §11 (ARTIFACT INTERNAL PRECEDENCE),
> không phải một quyết định nghiệp vụ mới. Bảng vẫn CHƯA là executable gate —
> việc đó thuộc chủ sở hữu composition (`DEC-155` §5).

Các rule này thuộc integration boundary giữa `TASK-105D`, `TASK-105C`,
`TASK-105B` và downstream `TASK-108B`; chúng không mở scope price calculation
trong `TASK-105D`. Trước implementation phải có một implementation task/scope
lock có authority nhận ownership của composition này; phiên hiện tại không
tự invent code-task mới hay activate provider.

**12. TASK-105B — current architectural role.** Frozen implementation/history
giữ nguyên. Từ quyết định này, `FilePriceProvider` là foundation/provider cho
nhánh **Public Purchase effective-dated price**, không còn là dependency cứng
của `TASK-105C`. Cụm “bảng giá production thật” trong DONE blocker được làm
rõ là **Public Purchase price dataset thật**, có effective-date/version và
provenance; không phải bảng tạm không liên quan. `TASK-105B` vẫn `FROZEN +
INTEGRATED + RC-1 INTEGRATED + NOT DONE`; `PendingPriceProvider` vẫn default.

**13. TASK-105C — current architectural role.** Giữ nguyên nhánh Tracking
`phist` và toàn bộ semantics `DEC-151`/`DEC-152`, nhưng supersede hai phần của
kiến trúc cũ: (a) không còn compose/depend cứng vào `FilePriceProvider`; (b)
không còn tự kết luận absence là final Pending — output là
`HistoricalVendorMin | absence` để price-resolution layer có thể fallback.
Input conceptually là resolved `TRACKING` identity + `sale_date`. Không yêu
cầu pre-map toàn bộ catalog; unresolved rows có thể Pending trong khi aliases
đã confirm được reuse. `TASK-105C` không còn `READY`; cần reconcile/freeze lại
Scope/Completion Gate theo quyết định này và audit hardening triggers trước
một implementation authority riêng.

**14. TASK-105D.** `TASK-105D — Product Identity Resolver` là numbering hợp
lệ (không tồn tại task/decision khác chiếm ID). Canonical spec được tạo tại
`docs/tasks/TASK-105D-product-identity-resolver.md`, `Status = PLANNED`,
Completion Gate 32 check là DRAFT/NOT_TESTED, chưa freeze và chưa implement.

**15. Dependency graph — current.**

```text
SALES
  └─ TASK-105D Product Identity Resolver
       ├─ TRACKING identity ───────────────┐
       │    └─ TASK-105C HistoricalVendorMin
       │          └─ absence + cross-map ─┼─ TASK-105B PublicPurchasePrice
       └─ PUBLIC_PURCHASE identity ────────┘
                         │
                         ▼
                  PRICE RESOLUTION (P01–P10)
                         │
                         ▼
                   KpiPurchasePrice / TASK-108B
```

Superseded: tuyến `TASK-105B → TASK-105C` như dependency cứng và giả định mọi
valid identity phải là Tracking `<MÃ>`. Còn hiệu lực: `PriceProvider` seam,
Pending safety, `DEC-151`/`DEC-152` historical vendor semantics, snapshot/
replay requirement, Tracking read-only boundary, frozen historical evidence.

**16. Hardening trigger reconciliation.** Không finding lịch sử nào bị xoá:

- `HB-105B-03`: chưa triggered trong docs session; bắt buộc resolve trước
  lần đầu `FilePriceProvider.from_yaml()` đọc Public Purchase dataset thật.
- `HB-105B-05`: chưa triggered; strict required-column semantics phải resolve
  trước Public Purchase dataset thật/activation.
- `HB-105B-06`: chưa triggered; re-trigger trước khi `TASK-105C` thêm test/
  `tools/pricing`; required action là assertion boundary đúng phạm vi, cho
  phép network chỉ trong intended tool nhưng không trong 105B module/test.
- `HB-105B-10`: chưa triggered; trigger hiện hành được cụ thể hoá thành bất kỳ
  machine-generated dataset nào được nạp qua `FilePriceProvider`, đặc biệt
  Public Purchase export/snapshot; strict schema phải resolve trước usage đó.
- `HB-105B-07`/`08`: RESOLVED + independently verified trong RC-1, không mở lại.
- `HB-105B-09`/`11`: vẫn SUPERSEDED; `HB-105B-04` vẫn OUT_OF_SCOPE;
  `HB-105B-01`/`02` vẫn thuộc TASK-108B.

Không finding nào triggered bởi việc chỉ sửa documentation này. Không mở
Repair Cycle #2; budget `TASK-105B` giữ `2 allowed / 1 used / 1 remaining`.

**17. UX/metrics.** Batch/keyboard-first, candidate #1 đúng mục tiêu ≤1 normal
action, known mapping = 0 action. Theo dõi `AUTO_RESOLUTION_RATE`,
`MANUAL_CONFIRMATION_RATE`, `PENDING_RATE`, `REUSE_RATE`,
`WRONG_MAPPING_CORRECTION_RATE`, `MANUAL_ACTIONS_PER_100_ORDERS` với
denominator/version rõ ràng.

Supersedes:

- `DEC-152` §5 chỉ ở giả định canonical identity bắt buộc là Tracking `<MÃ>`;
  thay bằng two-namespace tuple. Lệnh cấm fuzzy-only authority vẫn giữ nguyên.
- `DEC-152` §11 chỉ ở dependency/composition `TASK-105C` compose
  `FilePriceProvider`; thay bằng hai provider branch song song.
- Các current-state prose nói `TASK-105C IMPLEMENTATION = READY` hoặc chỉ chờ
  bảng `product_raw ↔ <MÃ>` Tracking.
- Cách hiểu `FilePriceProvider` là foundation dành riêng cho `phist` snapshot.

Preserves:

- Toàn bộ historical evidence/commit/review/freeze/RC-1 của `TASK-105B`.
- `DEC-151`/`DEC-152` date lookup, vendor MIN, sentinel `0`, no current-state
  retroactive filtering và snapshot/replay semantics.
- `PendingPriceProvider` default và Golden behavior.
- Tracking repo read-only/no mutation.
- Identity/price unknown không được coerced thành 0 hay invented value.

Reason:

Owner làm rõ mô hình production thật có hai product namespaces và Public
Purchase vừa là identity source độc lập vừa là price fallback. Kiến trúc cũ
đồng nhất “canonical product” với Tracking `<MÃ>` và đặt `FilePriceProvider`
dưới `TASK-105C`; điều đó không biểu diễn được valid product không có trong
Tracking, không phân biệt hai provenance Public Purchase và tạo dependency
tuyến tính lỗi thời. Quyết định additive này sửa current architecture nhưng
không rewrite quyết định lịch sử như thể chúng chưa từng tồn tại.

Risk:

Effective Risk = HIGH. Sai mapping/namespace/cutover/fallback có thể áp sai
purchase price và tác động trực tiếp KPI/lương; Golden hiện 100% Pending ở
price path nên không hạ blast radius.

Impact:

- Tạo `docs/tasks/TASK-105D-product-identity-resolver.md`.
- `CLAUDE.md` — đồng bộ trạng thái `V4.1 = FULLY_ENFORCED` (bổ sung
  2026-08-28, S034/`DEC-155`, HB-154-06: thay đổi này ĐÃ có trong diff của
  phiên `DEC-154` và đã được công bố ở "Files Changed" của `S032`; đây là
  hoàn thiện bản ghi Impact cho khớp diff, không phải sửa lịch sử. Nội dung
  thay đổi đúng sự thật — `PROJECT/PROJECT_PROGRESS.md` đã ghi
  `V4.1 = FULLY_ENFORCED` từ 2026-08-27, `CLAUDE.md` chỉ đang lỗi thời).
- Reconcile current-role/status pointers trong `TASK-105B`, `TASK-105C`,
  `TASK-108B`, progress, roadmap, review ledger và session handoff.
- Không sửa `app/**`, `tests/**`, `config/**`, Golden hay Tracking.
- Không activate provider, không implement `TASK-105C`/`TASK-105D`, không
  merge/freeze.

Can Revisit After:

- Catalog/data contracts và persistence/audit mechanism cho `TASK-105D` sẵn
  sàng, rồi một session Scope Lock/Completion Gate Freeze có authority riêng.
- Remaining HB-105B findings được xử lý đúng trigger trước real Public
  Purchase dataset/activation hoặc `TASK-105C` tools/tests.
- Price-resolution implementation ownership được mở bằng task/scope lock
  riêng, rồi P01–P10 trở thành executable gate.

## DEC-155

Title:
TASK-105D READINESS — DATA CONTRACT, PERSISTENCE & AUDIT DESIGN

Date:
2026-08-28

Task:
`TASK-105D` — Readiness / Data Contract / Persistence & Audit Design. Ghi
trong phiên `docs/sessions/S034-task-105d-readiness-data-contract.md`.
Reports SHA bắt đầu phiên: `442404d1fdb24a134625f53c7ede5f3377416177`.

Loại thẩm quyền — phân biệt tường minh, không gộp:

```text
READINESS DESIGN AUTHORITY (phiên này có)
    D-01 … D-14  : quyết định thiết kế data contract/persistence/audit
    INV-01 … INV-87 : invariant quy phạm của các entity thuộc TASK-105D
    định nghĩa vận hành cho Completion Gate DRAFT (chưa freeze)
    sửa transcription bảng P (chép lại prose đã có, không thêm ngữ nghĩa)
    canonical documentation correction (HB-154-06, HB-154-07)

OWNER AUTHORITY (phiên này KHÔNG có — chỉ ghi yêu cầu)
    OR-01, OR-02, OR-03  (§4 dưới đây)
    HB-154-04 review-budget lineage của TASK-105C  (§6)
    cấp task ID cho lớp composition P00–P11        (§5)
    chuyển TASK-105D sang READY; freeze Completion Gate
```

Bằng chứng đầu vào (independent review E2 đã tiêu thụ, không merge):
nhánh `review/product-identity-price-resolution-reconciliation`, commit
`61a90b4fc1d8fc281927536f4e0c32ba6ef703dd`, artifact
docs/reviews/DEC-154-PRODUCT-IDENTITY-PRICE-RESOLUTION-INDEPENDENT-REVIEW.md
(viết không backtick — file KHÔNG nằm trên nhánh này, đây là tham chiếu
liên-nhánh, không phải một đường dẫn phân giải được trong cây hiện tại),
verdict `PASS WITH HARDENING — ELIGIBLE_FOR_NEXT_READINESS`, reviewed target
`442404d1` (= HEAD phiên này), BLOCKING 0, HARDENING 7, OUT_OF_SCOPE 1.

Decision:

**1. Canonical data contract artifact.**
`docs/spec/TASK-105D-DATA-CONTRACT.md` là hợp đồng dữ liệu canonical của
`TASK-105D`: mười hai entity (`PublicPurchaseSourceVersion`, identity
projection, price projection, `TrackingCatalogSnapshot`,
`CanonicalProductIdentity`, `ProductIdentityMapping`, `AliasMemory`,
`RejectedCandidate`, `CrossSystemProductMapping`,
`HistoricalConfirmedRegistry`, `MappingAuditEvent`, `ResolutionBinding`), mỗi
entity có purpose, fields, key, invariant, lifecycle, mutation authority và
replay semantics. Các khối `text` mô tả schema là quy phạm; prose phục vụ
việc đọc. Trong nội bộ artifact đó, quy phạm thắng prose
(`governance/core/V4_1_POLICY_FREEZE.md` §11).

**2. Unified Public Purchase Source — giải HB-154-02.**

```text
MỘT PublicPurchaseSourceVersion  →  HAI projection publish cùng lúc
    identity projection : product_code, product_name, aliases, active_from/to
    price projection    : product_code, effective_from, effective_to,
                          purchase_price, source
Ràng buộc chéo bắt buộc (INV-06): mọi product_key phía giá phải tồn tại
trong identity projection CỦA CÙNG VERSION.
```

`source_id = PUBLIC_PURCHASE`; `version_id = PP-<YYYYMMDD>-<NN>`; version
`PUBLISHED` là **IMMUTABLE**; rollback = publish version mới mang
`rollback_of`, không sửa/xoá version cũ. Report ghim `ResolutionBinding` =
`(pp_version_id, tracking_capture_id, mapping_store_revision,
registry_revision)` — ghim cả bốn, không ghim từng phần; thiếu bất kỳ thành
phần nào là **lỗi cứng**, không phải Pending và không fallback sang "mới
nhất". `TASK-105D` tiêu thụ identity projection, `TASK-105B` tiêu thụ price
projection, cùng một lineage version.

Khối `prices` giữ nguyên schema 4 cột `DEC-145` §4 để `FilePriceProvider`
(FROZEN theo `DEC-153`) đọc được **mà không sửa module đó**. Vì
`from_yaml()` bỏ qua mọi khoá top-level lạ, projection identity **phải** do
một loader strict riêng đọc (`INV-02`/`INV-03`) — nếu không, một lỗi chính
tả `products:` sẽ nạp danh mục rỗng trong im lặng.

**3. Các quyết định thiết kế còn lại (tóm tắt; nguyên văn ở artifact).**

```text
D-03/D-04  canonical Tracking code = khoá node board/<MÃ> sau aliasOf();
           cấm tái phát minh extractCode() (tiền lệ production, DEC-147 §4)
D-05       khớp qua inv.map/alias.map của Tracking = candidate #1, KHÔNG
           auto-resolve (phê duyệt của Tracking ≠ phê duyệt của Reports)
D-06       AliasMemory là INDEX trên ProductIdentityMapping đang ACTIVE,
           không phải store thứ hai (tránh lặp lỗi hai-nguồn-sự-thật của S021)
D-07       hai khoá tách biệt: raw_identity_key (NFC+whitespace, GIỮ hoa
           thường/dấu — khoá định danh) và normalized_matching_aid (fold —
           chỉ để tìm candidate)
D-09       reason của RejectedCandidate là OPTIONAL; actor/timestamp REQUIRED
D-10/D-11  interface ProductIdentityStore trước; Phase 1 = append-only JSONL
           event log + index dẫn xuất (rationale + bảng so sánh ở §11.1;
           hạn chế single-host được ghi rõ, không giấu)
D-12       actor Phase 1 = KHAI BÁO của người vận hành, REQUIRED, không có
           mặc định, và cấm gọi là "authenticated"
D-13       reason REQUIRED cho mọi CORRECT_* và REPIN_REPORT; OPTIONAL cho
           confirm/reject lần đầu
D-14       confirmation_action đếm ở tầng domain command, không đếm phím/click
```

Idempotency hai lớp: `client_request_id` (chống retry → `ALREADY_APPLIED`) và
so sánh state (chống import trùng → `NO_CHANGE`, không ghi event, không tăng
revision). Concurrency: optimistic `expected_version`; lệch → `CONFLICT` kèm
state hiện tại, **cấm silent last-write-wins**. Correction: supersede, không
DELETE, không UPDATE tại chỗ; correction tác động resolution tương lai và
**không** tự viết lại report đã ghim binding — muốn vậy phải có
`REPIN_REPORT` tường minh, có quyền, có reason, được audit (`DEC-121`).

**4. `OWNER_RATIFICATION_REQUIRED` — ba mục, phiên này KHÔNG tự chốt.**

```text
OR-01  Public Purchase được vận hành như MỘT nguồn xuất bản theo version
       (một lần publish ra cả tên hàng lẫn giá) thay vì hai bảng nhập tay
       rời. Đây là quyết định quy trình của người dùng thật.
OR-02  ALIAS_AID_UNIQUE (khớp exact sau fold, duy nhất, cùng một canonical
       target) được auto-resolve — đây là chỗ DUY NHẤT hệ thống tạo một
       mapping CONFIRMED không có thao tác người cho chính identity đó.
       Nếu Owner không chấp thuận: hạ xuống "candidate #1, cần 1
       confirmation". Thiết kế đặt nó ở chỗ rẻ để đảo — một cờ cấu hình,
       không đổi schema, không đổi invariant nào khác.
OR-03  Chấp nhận rằng confirmation ở Phase 1 là KHAI BÁO của người vận hành,
       không phải danh tính đã xác thực (ADR-101 chưa có auth ở Phase 1) —
       hoặc yêu cầu chờ auth Phase 2 trước khi mở implementation.
```

**5. Ownership của lớp composition P00–P11 — `ROADMAP CHANGE PROPOSAL`.**
Lớp composition không có task ID, scope lock, Completion Gate hay review
budget lineage. `DEC-154` §11 công bố khoảng trống này và cấm phiên
reconciliation tự lấp. Đề xuất cấp một task mới nhận ownership (ID đề xuất
`TASK-105E — Price Resolution Composition`; đã kiểm tra `TASK-105E` chưa bị
chiếm ở bất kỳ đâu trong repo). Phiên này **KHÔNG** tự cấp task ID.

**6. HB-154-04 — `OWNER DECISION REQUIRED`, phiên này KHÔNG tự sửa.**
`TASK-105C` vẫn dùng chung review-budget lineage `TASK-105B` (`2 allowed /
1 used / 1 remaining`) dù `DEC-154` §13 đã supersede chính composition biện
minh cho việc dùng chung. `governance/core/V4_1_POLICY_FREEZE.md` §2 cấm tạo lineage mới **để
reset ngân sách**, và §12 đặt `SUPERSEDED` dưới thẩm quyền Owner/authorized
governance action — nên việc đổi lineage nằm ngoài thẩm quyền phiên readiness.
Đã kiểm tra: không có điều khoản nào trong V4.1 cho phép reconciliation tự
đổi lineage. Ba phương án:

```text
(A) GIỮ NGUYÊN lineage TASK-105B.
    TASK-105C vào implementation với 1 cycle còn lại, đã bị tiêu một phần bởi
    TASK-105B-RC-1 — một repair về NaN/vô cực trong FilePriceProvider, nay là
    code thuộc NHÁNH KHÁC. Rủi ro OWNER_EXTENSION sớm vì lý do không liên quan.
(B) CẤP lineage root riêng cho TASK-105C, HIGH → 2/0/2.  [KHUYẾN NGHỊ]
    Căn cứ: lineage dùng chung được biện minh DUY NHẤT bởi composition
    "HistoricalVendorPriceProvider compose FilePriceProvider" (DEC-152 §11);
    DEC-154 §13 đã gỡ composition đó. Đây là hai root task thật sự khác nhau
    sau DEC-154, không phải một lineage bị tách ra để reset ngân sách. Owner
    phải ghi rõ điều đó khi cấp, để §2 không bị đọc thành đã bị vi phạm.
(C) GIỮ lineage chung + Owner Extension +1 cycle riêng cho TASK-105C.
    Ít thay đổi cấu trúc nhất, nhưng ghi nhận ngân sách kém minh bạch hơn.
```

Quyết định thuộc Owner, và theo independent review nên được đặt ra tại **phiên
refreeze Scope/Completion Gate của `TASK-105C`**, trước khi cấp `READY`.

**7. HB-154-05 — định nghĩa vận hành cho Completion Gate.** `confirmation_action`,
`AMBIGUOUS` và `normal action` được định nghĩa quy phạm (artifact §17, chép
vào `docs/tasks/TASK-105D-product-identity-resolver.md`).
`CHECK-105D-06/13/23/24` được viết lại thành assertion. Gate vẫn `DRAFT` —
phiên này **KHÔNG** freeze (`governance/core/V4_1_POLICY_FREEZE.md` §12).

**8. HB-154-01 / HB-154-03 — giải ở hai tầng.**
Tầng entity (thuộc scope `TASK-105D`, hiệu lực ngay): `INV-43`/`INV-44`/
`INV-45` — fallback Public Purchase cho identity TRACKING đòi một
`CrossSystemProductMapping` CONFIRMED active, và mã tra là
`public_purchase_code` của chính mapping đó; thiếu mapping → Pending, cấm
đoán mã. `INV-46`/`INV-47` — `sale_date < CUTOVER_DATE` không bao giờ gọi
resolver/catalog/provider; chỉ hai kết cục `HISTORICAL_CONFIRMED` hoặc
`PENDING_HISTORICAL_CONFIRMATION`. Tầng bảng P (transcription): `P00`, `P03`,
`P11` — xem `DEC-154` §11 và `TASK-108B` §99, có ghi chú nguồn transcription
tại chỗ.

**9. HB-154-06 / HB-154-07 — canonical documentation correction.**
`CLAUDE.md` được bổ sung vào Impact của `DEC-154`. Hai con trỏ current-state
lỗi thời (`PROJECT/PROJECT_PROGRESS.md`, `docs/tasks/TASK-108B-*.md` Phần XI)
được đánh dấu inline `SUPERSEDED BY DEC-154` — **giữ nguyên văn lịch sử**,
không xoá, đúng `governance/core/V4_1_POLICY_FREEZE.md` §10.

**10. `OS-154-01` — không xử lý.** Ba reference `TASK-REM-T06` hỏng là nợ
tiền tồn, đã xác minh vẫn giống hệt base. Ngoài contract của phiên này.

**11. Trạng thái `TASK-105D` sau phiên.**

```text
TASK-105D = PLANNED / SPEC COMPLETE + DATA CONTRACT COMPLETE
          / READY GATE BLOCKED
Blocker giảm từ 4 xuống 2:
  1. Owner ratification OR-01/OR-02/OR-03
  2. Completion Gate freeze bởi authority riêng
Implementation = NOT STARTED / NOT AUTHORIZED
Review budget lineage TASK-105D = 2 allowed / 0 used / 2 remaining (KHÔNG ĐỔI)
```

Không tự chuyển sang `READY`. Không freeze. Không mở Repair Cycle. Không tiêu
budget — phiên readiness/documentation không phải repair (`governance/core/V4_1_POLICY_FREEZE.md`
§3: cycle tính theo LẦN SỬA một defect BLOCKING, không theo phiên).

Reason:

**1. Vì sao một nguồn chứ không hai.** Ba lý do độc lập, mỗi lý do đủ để loại
phương án hai nguồn: (a) hai file nhập tay độc lập tạo ra đúng loại quy trình
thủ công thừa mà `TASK-105D` tồn tại để loại bỏ; (b) replay cần một mốc
version duy nhất, hai version độc lập không có luật nào ràng buộc chúng khớp
nhau — đúng lỗ hổng HB-154-02 nêu; (c) một mã có giá nhưng vắng trong catalog
là identity không tra tới được, hành vi chưa định nghĩa — ràng buộc chéo biến
nó thành lỗi lúc publish thay vì một con số sai lúc tính lương.

**2. Vì sao append-only JSONL ở Phase 1 chứ không SQLite.** `ADR-101` cố ý
giữ Phase 1 là thư viện Python thuần, kiểm chứng bằng test tĩnh cấm import
web/DB trong `app/modules/`. `ADR-102` yêu cầu audit chỉ-append như một tính
chất, không phải một quy ước phải tự giữ. JSONL cho append-only và
point-in-time read (`mapping_store_revision`) miễn phí, không thêm dependency,
export/backup bằng công cụ text thường. SQLite đúng cho Phase 2 và `ADR-101`
đã nêu tên nó — việc tách `ProductIdentityStore` thành Protocol chính là để
đổi sang nó mà không đụng domain, và để **cùng một bộ test concurrency** chạy
đúng trên cả hai.

**3. Vì sao hai khoá chuẩn hoá chứ không một.** Chuẩn hoá càng mạnh càng dễ
gộp nhầm hai model khác nhau; chuẩn hoá càng yếu càng bỏ lỡ biến thể hoa
thường. Với một khoá duy nhất phải chọn một trong hai thiệt hại. Tách làm hai
thì khoá định danh chỉ mất thông tin ở mức dạng Unicode/khoảng trắng — không
thể gộp hai model — trong khi vẫn có aid mạnh hơn để tìm candidate. Đây là
cách đạt mục tiêu tự động hoá mà không nới lỏng `INV-01`.

**4. Vì sao đếm domain command chứ không đếm thao tác UI.** Đếm keystroke/
click biến một gate nghiệp vụ thành gate của framework UI: cùng một hành động
nghiệp vụ sẽ đạt hay trượt tuỳ bàn phím hay chuột, tuỳ thư viện. Đếm command
đo đúng thứ nghiệp vụ quan tâm — **số lần con người phải quyết định** — và
test được mà không cần dựng UI. Yêu cầu keyboard-first không mất đi; nó là
`CHECK-105D-22`, một gate riêng.

**5. Vì sao HB-154-04 không được tự sửa dù khuyến nghị đã rõ.** Ngân sách
review là cơ chế kiểm soát chính chủ dự án đặt ra để giới hạn việc vá đi vá
lại. Một agent tự cấp thêm ngân sách cho chính công việc của mình — kể cả với
lý do đúng — là đúng thứ `governance/core/V4_1_POLICY_FREEZE.md` §2 tồn tại để chặn. Ghi rõ
phương án và khuyến nghị, rồi dừng, là hành vi đúng.

Risk:

`Effective Risk = HIGH` — không đổi, chấm theo failure path (`governance/core/V4_1_POLICY_FREEZE.md`
§4): `sai identity → sai nguồn giá → sai KpiPurchasePrice → sai KPI/lương`.
Golden hiện chỉ phủ `PendingPriceProvider` nên không hạ bậc (§4.1).

Rủi ro của chính bản ghi này:

- **Đọc "data contract complete" thành "READY".** Không phải. Hai blocker còn
  lại (§11) đều nằm ngoài thẩm quyền phiên readiness. `TASK-105D` vẫn
  `BLOCKED`.
- **`OR-02` bị bỏ qua khi implement.** Nếu implementation bật
  `ALIAS_AID_UNIQUE` auto-resolve mà chưa có ratification của Owner, hệ thống
  sẽ tạo mapping CONFIRMED không có thao tác người. Giảm nhẹ: nó là một cờ
  cấu hình đơn lẻ, và `INV-28` đặt tập auto-resolve thành **tập đóng** —
  thêm phương thức là quyết định Owner, không phải quyết định implementation.
- **`INV-02` bị bỏ sót khi implement.** `FilePriceProvider.from_yaml()` bỏ
  qua khoá top-level lạ, nên một lỗi chính tả `products:` nạp danh mục rỗng
  **trong im lặng**. Đây là rủi ro thật của chính lựa chọn "một file, hai
  khối". Giảm nhẹ: `INV-02`/`INV-03` bắt loader identity phải strict và cấm
  sửa `FilePriceProvider` (FROZEN) để đọc `products`.
- **Cơ chế JSONL bị đọc thành đủ cho nhiều người dùng.** Không đủ. Concurrency
  một máy. Nhiều người dùng đồng thời là bài toán Phase 2 + DB. Đã ghi rõ ở
  §11.1 của artifact, không giấu trong prose.

Hardening trigger audit (`HB-105B-03/05/06/10`): **KHÔNG finding nào được
trigger bởi phiên này** — không dataset thật nào được nạp, không code nào đổi,
không test/tool nào được thêm. Thiết kế này **định vị chính xác** thời điểm
trigger: lần đầu một `PublicPurchaseSourceVersion` thật được nạp qua
`FilePriceProvider`. `HB-105B-07/08` vẫn RESOLVED; `09/11` vẫn SUPERSEDED;
`04` vẫn OUT_OF_SCOPE; `01/02` vẫn thuộc `TASK-108B`. Không mở Repair Cycle;
budget `TASK-105B` giữ `2/1/1`.

Impact:

- `docs/spec/TASK-105D-DATA-CONTRACT.md` — file MỚI, canonical data contract.
- `PROJECT/PROJECT_DECISIONS.md` — `DEC-155` (ID đã quét toàn repo, `DEC-155`
  trống trước khi cấp); `DEC-154` §11 bảng P (`P00`/`P03`/`P11` transcription)
  và `DEC-154` Impact (`CLAUDE.md`, HB-154-06).
- `docs/tasks/TASK-105D-product-identity-resolver.md` — Ready Gate, định nghĩa
  vận hành, `CHECK-105D-06/13/23/24`, cross-system precondition, dependencies,
  metric rename, Exit Criteria.
- `docs/tasks/TASK-108B-eligible-costs-owner-definition.md` — §99 bảng P;
  marker `SUPERSEDED BY DEC-154` ở Phần XI (HB-154-07).
- `PROJECT/PROJECT_PROGRESS.md` — current-state, next authorized action,
  marker `SUPERSEDED BY DEC-154` (HB-154-07).
- `PROJECT/LO_TRINH_DE_HIEU.md` — bước 11a bằng ngôn ngữ phổ thông.
- `PROJECT/REVIEW_BUDGET_LEDGER.md` — lineage `TASK-105D` (budget KHÔNG đổi).
- `docs/sessions/S034-task-105d-readiness-data-contract.md` — bàn giao.
- **Không** sửa `app/**`, `tests/**`, `config/**`, `tools/**`, `scripts/**`,
  Golden fixture/expected, `governance/**`, `TASK-110`, `CHECK-110-16`.
- **Không** sửa repo `Tracking` — 0 file.
- **Không** activate provider, không implement, không freeze, không merge.

Can Revisit After:

- Owner trả lời `OR-01`/`OR-02`/`OR-03` ⇒ gỡ blocker 1 của Ready Gate.
- Một phiên Freeze Finalization có thẩm quyền review + freeze Completion Gate
  32 check ⇒ gỡ blocker 2. `TASK-105D` khi đó mới có thể `READY`.
- Owner quyết HB-154-04 tại phiên refreeze `TASK-105C`.
- Owner cấp task ID cho lớp composition P00–P11 ⇒ `P00`–`P11` trở thành
  executable gate.

## DEC-156

Title:
OWNER RATIFICATION — TASK-105D READINESS; TASK-105C LINEAGE RECONCILIATION;
TASK-105E AUTHORIZATION

Date:
2026-08-28

Task:
Owner Ratification Recording cho `TASK-105D` readiness. Ghi trong phiên
`docs/sessions/S035-owner-ratification-task-105d-readiness.md`.

```text
readiness SHA Owner đã xem : d3b73e59b8f7aa8c1db27ef42ff6e06b2e05690e
session starting SHA        : d3b73e59b8f7aa8c1db27ef42ff6e06b2e05690e
```

**Đây LÀ một Owner Decision.** Nó đóng ba mục `OWNER_RATIFICATION_REQUIRED`
của `DEC-155`, đóng `HB-154-04`, và cấp một task ID mới. Phiên ghi nhận
**không** thêm quyết định nào của riêng mình ngoài phần reconciliation kỹ
thuật bắt buộc để bản ghi khớp với quyết định Owner.

Ghi chú artifact budget (`governance/core/V4_1_POLICY_FREEZE.md` §10): đây là
artifact governance thứ 5 của lineage `TASK-105D`, tức thuộc diện
`OWNER APPROVAL REQUIRED`. Approval đó **chính là** chỉ thị của Owner trong
phiên này ("Ghi nhận các Owner Decisions trên vào canonical decision/task/
progress artifacts theo đúng governance"). Ghi lại tường minh để phiên sau
không phải suy luận.

Decision:

**1. `OR-01` — APPROVED.**

Public Purchase vận hành như **MỘT canonical versioned source**.

```text
Identity Projection và Price Projection = hai projection của CÙNG một
PublicPurchaseSourceVersion / source-version lineage.
KHÔNG thiết kế thành hai quy trình nhập liệu vận hành độc lập.
Published version = IMMUTABLE.
Unified-source contract của readiness giữ nguyên, không sửa.
```

Hiệu lực: `docs/spec/TASK-105D-DATA-CONTRACT.md` §3 (`D-01`, `D-02`,
`INV-02`…`INV-10`) chuyển từ **đề xuất** sang **contract đã phê chuẩn**.
Ràng buộc chéo `INV-06` (mọi `product_key` phía giá phải tồn tại trong
identity projection của cùng version) là quy phạm.

**2. `OR-02` — APPROVED WITH CANDIDATE-ONLY POLICY.**

`ALIAS_AID_UNIQUE` **KHÔNG** có production auto-resolution authority.

```text
ALIAS_AID_UNIQUE
    → chỉ candidate #1
    → candidate đúng ⇒ tối đa 1 confirmation_action
    → sau confirmation ⇒ persistent confirmed mapping/alias
    → các lần xuất hiện sau ⇒ 0 confirmation_action (qua ALIAS_EXACT)

KHÔNG giảm yêu cầu DISTINCT-before-mapping.
KHÔNG đổi nguyên tắc: fuzzy/similarity-only không có production authority.
```

Đây là **sửa đổi** so với `DEC-155` `D-08`, không phải xác nhận nguyên trạng.
`DEC-155` đề xuất cho `ALIAS_AID_UNIQUE` quyền auto-resolve với lập luận
`fold()` là exact-match-after-canonical-normalization chứ không phải
similarity. Owner chấp thuận **cơ chế candidate** nhưng bác **phần authority**.

Hiệu lực trên data contract:

```text
INV-28   SỬA — tập auto-resolve còn ĐÚNG HAI phương thức:
         ALIAS_EXACT, CATALOG_EXACT_UNIQUE
INV-28b  MỚI — ALIAS_AID_UNIQUE không bao giờ tự sinh mapping CONFIRMED;
         mapping chỉ tồn tại sau một confirmation_action của người dùng
mapping_source  — bỏ DERIVED_FROM_CONFIRMED_ALIAS khỏi enum; mapping sinh ra
         từ candidate loại này mang HUMAN_CONFIRMATION, provenance của gợi ý
         nằm ở evidence.parent_mapping_id
REUSE_RATE — chỉ đếm ALIAS_EXACT
CHECK-105D-23 — thêm fixture BẮT BUỘC cho trường hợp ALIAS_AID_UNIQUE
```

**3. `OR-03` — APPROVED FOR PHASE 1.**

```text
Phase 1 cho phép actor do người vận hành khai báo.
actor = REQUIRED.
CẤM gọi actor này là authenticated identity/user.
CẤM default actor im lặng.
Authentication thật KHÔNG phải blocker của Phase 1 TASK-105D implementation,
nhưng phải được ghi nhận đúng là future hardening / capability boundary.
```

`INV-72`/`INV-73` giữ nguyên. Data contract §12.1 bổ sung một khối
`CAPABILITY BOUNDARY — PHASE 1 ACTOR` nêu rõ audit trail Phase 1 chứng minh
được cái gì ("bản ghi này khai actor X") và **không** chứng minh được cái gì
("người thật sự thao tác là X").

**4. `HB-154-04` — OWNER APPROVES OPTION B. CLOSED.**

Owner cho phép reconcile lineage/review-budget semantics của `TASK-105C`
theo architecture `DEC-154` hiện hành. `TASK-105C` **không còn** bị coi là
sub-lineage phụ thuộc `TASK-105B` chỉ vì composition lịch sử `105B → 105C`.

Bốn ràng buộc Owner đặt ra, và cách chúng được thi hành:

```text
KHÔNG rewrite/delete historical evidence
    → DEC-152 §11 (composition cũ), toàn bộ mục "Root Task: TASK-105B" của
      ledger, và mọi bản ghi review/freeze/RC-1 giữ NGUYÊN VĂN. Không một ký
      tự lịch sử nào bị xoá hay sửa nghĩa.

KHÔNG reset consumed review budget
    → TASK-105B giữ nguyên `2 allowed / 1 used / 1 remaining`. Cycle
      TASK-105B-RC-1 vẫn CONSUMED, vẫn thuộc TASK-105B, KHÔNG được chuyển
      sang lineage mới, KHÔNG được xoá, KHÔNG được tính lại.
      Lineage TASK-105C mở ở `0 used` KHÔNG phải vì một cycle đã tiêu được
      xoá, mà vì TASK-105C **chưa từng tiêu cycle nào của chính nó** —
      TASK-105B-RC-1 là một repair về NaN/vô cực trong FilePriceProvider,
      code nay thuộc nhánh Public Purchase, không thuộc TASK-105C.

KHÔNG giả vờ historical relationship chưa từng tồn tại
    → Mục ledger mới của TASK-105C ghi rõ lineage cũ, lý do nó từng tồn tại
      (DEC-152 §11), và vì sao nó không còn áp dụng (DEC-154 §13). Con trỏ
      hai chiều giữa hai mục ledger.

canonical current lineage phản ánh architecture hiện tại
    → TASK-105C = root lineage riêng.
```

Ngân sách lineage `TASK-105C` theo bảng đã freeze (`V4.1` §2,
`HIGH/CRITICAL = 2`):

```text
root_task: TASK-105C
effective_risk: HIGH        (Blast Radius 5 — data path giá/KPI/lương)
repair_cycles_allowed: 2
repair_cycles_used: 0
repair_cycles_remaining: 2
cycles: []
```

Đây **không** phải một lineage mới được tạo "để reset ngân sách" theo nghĩa
`V4.1` §2 cấm: (a) nó do Owner cấp tường minh, không phải do agent tự tách;
(b) căn cứ là architectural — `DEC-154` §13 đã gỡ bỏ composition vốn là lý do
DUY NHẤT của lineage dùng chung; (c) không ngân sách đã tiêu nào bị hoàn lại.

`TASK-105C` **vẫn** `BLOCKED / NOT AUTHORIZED`. Quyết định này chỉ chạm
lineage/budget accounting; Scope Lock vẫn `REOPENED_BY_DEC-154`, Completion
Gate vẫn `CHANGE_PROPOSAL_OPEN, NOT FROZEN`.

**5. `TASK-105E` — OWNER AUTHORIZATION. Task ID được cấp.**

```text
TASK-105E — Price Resolution Composition
Purpose: canonical owner cho P00–P11 price-resolution composition semantics.
Layer  : orchestration / composition.
```

`TASK-105E` **KHÔNG**:

```text
- resolve/match product identity        (đó là TASK-105D)
- thay TASK-105D
- thay TASK-105B provider
- thay TASK-105C provider
- tự invent product mapping
- tự invent price
- mutate Tracking
```

Conceptual responsibility:

```text
resolved identity
  → apply P00–P11
  → coordinate HistoricalVendorMin / PublicPurchasePrice / Pending
  → preserve provenance
  → output resolved KpiPurchasePrice semantics downstream to TASK-108B
```

Canonical spec: `docs/tasks/TASK-105E-price-resolution-composition.md`,
`Status = PLANNED`, Ready Gate `BLOCKED`, Completion Gate chưa soạn/chưa
freeze, implementation **NOT STARTED / NOT AUTHORIZED**. Lineage review
budget mới `TASK-105E`, `HIGH`, `2 allowed / 0 used / 2 remaining`. Cấp
lineage là thao tác cơ học theo bảng đã freeze `V4.1` §2, không phải một
quyết định ngân sách riêng.

Đóng blocker thứ 4 của `TASK-108B` ("price-resolution composition ownership
chưa có") ở mức **ownership**; blocker vẫn mở ở mức **implementation**.

**6. Trạng thái `TASK-105D` sau ratification.**

```text
TASK-105D = PLANNED / SPEC COMPLETE + DATA CONTRACT COMPLETE + OWNER RATIFIED
          / READY GATE BLOCKED
Ready Gate blocker: 2 → 1
    ĐÃ ĐÓNG : Owner ratification OR-01 / OR-02 / OR-03
    CÒN LẠI : Completion Gate freeze bởi một phiên Freeze Finalization có
              thẩm quyền riêng (V4.1 §12 — reviewer/readiness/ratification
              session KHÔNG được ghi FROZEN)
implementation = NOT STARTED / NOT AUTHORIZED
budget = 2 allowed / 0 used / 2 remaining (KHÔNG ĐỔI)
```

Phiên này **không** chuyển `TASK-105D` sang `READY` — Owner đã chỉ thị
tường minh không làm điều đó khi Freeze Finalization chưa hoàn tất.

Reason:

**1. Vì sao `OR-02` bị bác phần authority là một quyết định hợp lý, không
phải thận trọng thừa.** Lập luận kỹ thuật của `DEC-155` `D-08` đúng về mặt
cơ chế: `fold()` là khớp chính xác, không phải similarity. Nhưng nó đánh đổi
một thứ khác — nó tạo ra loại bản ghi `CONFIRMED` duy nhất trong toàn hệ
thống mà **không** có một thao tác người nào cho chính identity đó. Chi phí
của việc bác bỏ là **một** xác nhận cho mỗi biến thể viết, đúng một lần,
sau đó về 0 vĩnh viễn. Đó là chi phí hữu hạn và nhỏ, đổi lấy một bất biến
đơn giản hơn hẳn: *mọi mapping CONFIRMED đều truy được về một con người đã
bấm xác nhận cho chính nó*. Với một hệ thống mà đầu ra quyết định lương,
bất biến đó đáng giá hơn vài thao tác.

**2. Vì sao lineage `TASK-105C` mở ở `0 used` mà không vi phạm "KHÔNG reset
consumed budget".** Hai việc khác nhau về bản chất: *reset* là lấy một cycle
đã tiêu và làm nó chưa tiêu; *tách lineage* là ghi nhận rằng hai root task
khác nhau có ngân sách khác nhau. `TASK-105B-RC-1` vẫn nằm nguyên ở
`TASK-105B`, vẫn `used`, vẫn `remaining = 1`. `TASK-105C` chưa từng có cycle
nào của chính nó để mà reset. Nếu sau này `TASK-105C` cần repair, nó tiêu
ngân sách của chính nó, và `TASK-105B` không được lợi gì từ việc tách.

**3. Vì sao `TASK-105E` phải là task riêng chứ không nhét vào `105D` hay
`105C`.** `P00–P11` là **quyết định chọn nguồn giá**, không phải nhận dạng
sản phẩm và cũng không phải tra giá. Nhét vào `105D` sẽ phá chính ranh giới
`DEC-154` §6 dựng lên (identity tách khỏi price); nhét vào `105C` sẽ tái lập
đúng dependency tuyến tính mà `DEC-154` §13 vừa gỡ. Một lớp orchestration
riêng là chỗ duy nhất mà cả hai nhánh provider và nhánh bypass lịch sử gặp
nhau mà không tạo cạnh ngược trong đồ thị.

Risk:

`Effective Risk = HIGH` — không đổi cho cả `TASK-105C`, `TASK-105D`,
`TASK-105E`; chấm theo failure path (`V4.1` §4)
`sai identity/sai nguồn giá → sai KpiPurchasePrice → sai KPI/lương`. Golden
chỉ phủ `PendingPriceProvider` nên không hạ bậc (§4.1).

Rủi ro của chính bản ghi này:

- **Đọc `OR-01/02/03 APPROVED` thành "được phép implement".** Không phải.
  `TASK-105D` vẫn `BLOCKED` vì Completion Gate chưa freeze. `TASK-105C` vẫn
  `BLOCKED`. `TASK-105E` vừa mới `PLANNED`.
- **Đọc lineage `TASK-105C` mới thành "budget được làm mới".** Không phải —
  xem Reason §2. Ledger ghi con trỏ hai chiều để chống đúng cách đọc sai này.
- **`INV-28b` bị bỏ qua khi implement.** Nếu implementation bật auto-resolve
  cho `ALIAS_AID_UNIQUE`, đó là vi phạm trực tiếp một Owner Decision, không
  phải một lựa chọn kỹ thuật. Giảm nhẹ: `INV-28` là **tập đóng** và
  `CHECK-105D-23` nay có fixture bắt buộc cho đúng trường hợp này — nó sẽ
  fail chứ không im lặng.
- **`TASK-105E` bị hiểu thành nơi "sửa nốt" những gì 105B/105C/105D thiếu.**
  Không phải. Danh sách "KHÔNG" ở §5 là quy phạm.

Hardening trigger audit: `HB-105B-03/05/06/10` **không** finding nào bị
trigger bởi phiên này — không dataset thật nào được nạp, không code/test/tool
nào được thêm. `HB-105B-07/08` vẫn RESOLVED; `09/11` vẫn SUPERSEDED; `04`
vẫn OUT_OF_SCOPE; `01/02` vẫn thuộc `TASK-108B`. `HB-154-01/02/03/05/06/07`
đã đóng tại `DEC-155`; `HB-154-04` đóng tại quyết định này; `OS-154-01` vẫn
mở, vẫn ngoài scope.

Impact:

- `PROJECT/PROJECT_DECISIONS.md` — `DEC-156` (ID đã quét toàn repo, trống
  trước khi cấp).
- `docs/spec/TASK-105D-DATA-CONTRACT.md` — status header; `OR-01`/`OR-02`/
  `OR-03` disposition; `D-08` sửa theo Owner; `INV-28` sửa, `INV-28b` mới;
  `mapping_source` enum; `REUSE_RATE`; §16.3 GRANTED; §17.2/§17.4 fixture;
  §18 bảng finding.
- `docs/tasks/TASK-105D-product-identity-resolver.md` — Ready Gate (blocker
  2 → 1), authority, `CHECK-105D-23`, ghi chú `ALIAS_AID_UNIQUE`.
- `docs/tasks/TASK-105C-historical-vendor-price-provider.md` — Review Budget
  lineage.
- `docs/tasks/TASK-105E-price-resolution-composition.md` — **file MỚI**.
- `docs/tasks/TASK-108B-eligible-costs-owner-definition.md` — blocker 4.
- `PROJECT/PROJECT_PROGRESS.md`, `PROJECT/LO_TRINH_DE_HIEU.md`,
  `PROJECT/REVIEW_BUDGET_LEDGER.md`.
- `docs/sessions/S035-owner-ratification-task-105d-readiness.md` — bàn giao.
- **Không** sửa `app/**`, `tests/**`, `config/**`, `tools/**`, `scripts/**`,
  `governance/**`, Golden fixture/expected.
- **Không** sửa repo `Tracking` — 0 file.
- **Không** implement, không activate provider, không freeze, không merge,
  không mở Repair Cycle.

Can Revisit After:

- Một phiên **Freeze Finalization** có thẩm quyền review + freeze Completion
  Gate 32 check của `TASK-105D` ⇒ `TASK-105D` mới có thể `READY`.
- Một phiên refreeze Scope/Completion Gate của `TASK-105C` (nay chạy trên
  lineage/budget của chính nó).
- Một phiên soạn Scope Lock + Completion Gate cho `TASK-105E`, biến
  `P00–P11` thành executable gate.

---

## DEC-157

Title:
COMPLETION GATE REVISION #1 CHO TASK-105D — GIỮ ĐÚNG 32 GATE;
BRANCH DIVERGENCE V4.1 §8 OPTION C

Date:
2026-08-28

Task:
Owner Decision Recording cho phiên gate revision `TASK-105D`. Ghi trong phiên
`docs/sessions/S037-task-105d-gate-revision.md`.

```text
base SHA phiên này        : 1676e1d173ff6afdbbaa2cedcf07fc06346955ce
freeze attempt #1 (S036)  : reviewed base SHA 9cd871488a6baebf6b80737f42e2137a27887cef
                            verdict FAIL — 5 BLOCKING / 5 HARDENING
```

**Đây LÀ một Owner Decision.** Owner mở phiên gate revision với hai quyết định
tường minh (Decision A — gate count; Decision B — divergence). Phiên ghi nhận
**không** thêm quyết định nghiệp vụ nào của riêng nó; toàn bộ nội dung gate
được sửa là (i) propagation của `DEC-156` đã có, (ii) chép ngữ nghĩa quy phạm
đã tồn tại trong `docs/spec/TASK-105D-DATA-CONTRACT.md` vào gate, hoặc
(iii) lựa chọn **hình thức tích hợp** mà Decision A đã ràng buộc.

Ghi chú artifact budget (`governance/core/V4_1_POLICY_FREEZE.md` §10): đây là
artifact governance thứ **8** của lineage `TASK-105D` (thứ 7 là
`docs/reviews/TASK-105D-COMPLETION-GATE-CHANGE-PROPOSAL.md`), tức thuộc diện
`OWNER APPROVAL REQUIRED`. Approval đó **chính là** chỉ thị của Owner khi mở
phiên này ("ghi Completion Gate Change Proposal canonical"; "Ghi Owner
decision: V4.1 §8 Option C — CONTINUE"). Ghi lại tường minh theo tiền lệ
`DEC-156`.

Decision:

**1. OWNER DECISION A — GATE COUNT: GIỮ ĐÚNG 32.**

```text
Completion Gate của TASK-105D giữ ĐÚNG 32 gate.
KHÔNG mở rộng gate set vượt 32.
F-03 / F-04 / F-05 được tích hợp vào các gate hiện có phù hợp, KHÔNG thêm
gate mới.
Điều kiện dừng đã đặt trước: nếu phát hiện contradiction không thể giải quyết
mà không đổi count → STOP và báo Owner.
```

Kết quả áp dụng: **không** phát hiện contradiction nào buộc phải đổi count.
Phân bổ đã thực hiện:

```text
F-01  → khối "Định nghĩa vận hành bắt buộc" + CHECK-105D-06
F-02  → CHECK-105D-05  (assertion hai chiều, có chiều FAIL)
F-03  → CHECK-105D-20 (điều kiện tiên quyết của command)
        + CHECK-105D-21 (nội dung audit + cấm từ "authenticated")
F-04  → CHECK-105D-28 (unified Public Purchase versioned source)
        + CHECK-105D-21 (ResolutionBinding / replay)
F-05  → CHECK-105D-10 (vòng đời mapping qua các capture — catalog drift)
H-01  → CHECK-105D-22 (ràng buộc vào bề mặt CLI Phase 1 theo ADR-101)
H-03  → CHECK-105D-04 (bỏ thuật ngữ "interaction")
H-02  → CHECK-105D-31 Phần B (một phần — biên lookup mà 105D sở hữu)
H-04  → CHECK-105D-09 (INV-33) + CHECK-105D-12 (INV-36)
H-05  → KHÔNG đóng (đổi data contract §6.7 — ngoài thẩm quyền phiên gate
        revision); ghi lại nguyên trạng kèm re-trigger trong CHECK-105D-08
```

Ràng buộc kèm theo, đã tuân thủ: **không hạ tiêu chuẩn bất kỳ gate nào**.
Không gate nào bị xoá, không assertion nào bị bỏ, không Evidence Level nào bị
hạ. Hai gate được **nâng** `E1 → E2` (`CHECK-105D-10`, `CHECK-105D-21`).

**2. OWNER DECISION B — BRANCH DIVERGENCE: `V4.1` §8 OPTION C.**

```text
V4.1 §8 — INTEGRATION_DECISION_REQUIRED  [ cumulative LOC > 5.000 ]
Owner chọn: (C) CONTINUE WITH EXPLICIT JUSTIFICATION.
```

Lý do Owner ghi nhận:

```text
- cumulative LOC vượt threshold CHỈ là documentation/governance;
- production diff = 0 (app/**, tests/**, config/**, tools/**, scripts/**,
  pyproject.toml đều rỗng trong diff);
- phần việc còn lại của lineage chỉ là gate correction + freeze;
- merge vào nhánh mặc định TRƯỚC freeze không mang lại lợi ích, trong khi
  vẫn phát sinh rủi ro xung đột văn bản.
```

Phạm vi được phép tiếp tục dưới Option C:

```text
1. Phiên Gate Revision này (S037).
2. MỘT phiên Freeze Finalization retry độc lập.
Ngoài hai việc đó: không mở thêm scope trên lineage này.
```

Review point tiếp theo (bắt buộc):

```text
NGAY SAU FREEZE FINALIZATION RETRY VERDICT.
```

**KHÔNG mở `TASK-105D` implementation trước divergence review point đó**, kể
cả khi freeze verdict là PASS.

**3. Trạng thái `TASK-105D` sau quyết định này.**

```text
TASK-105D            = PLANNED / SPEC COMPLETE + DATA CONTRACT COMPLETE
                       + OWNER RATIFIED / READY GATE BLOCKED
Completion Gate      = CHANGE PROPOSAL APPLIED — NOT FROZEN
Gate count           = 32  (không đổi)
TASK-105D READY      = KHÔNG
Repair Cycle         = KHÔNG mở  (2 allowed / 0 used / 2 remaining)
production code      = KHÔNG đổi
test implementation  = KHÔNG đổi
merge                = KHÔNG thực hiện
```

`V4.1` §12 giữ nguyên hiệu lực: `FROZEN` chỉ được ghi bởi một phiên Freeze
Finalization có thẩm quyền. Phiên gate revision **không** tự freeze — nếu nó
vừa viết gate vừa freeze thì phần gate mới không được bên nào review.

**4. Repair Cycle — KHÔNG mở.**

`V4.1` §3 tính repair cycle theo cumulative **repair diff** trên một defect
`BLOCKING` của **implementation**. `S037` không sửa một dòng code hay test
nào; toàn bộ diff là gate/documentation/governance. `V4.1` cấm mở Repair Cycle
chỉ vì documentation/gate issue trừ khi Owner quyết định khác — Owner **không**
quyết định khác. Ngân sách `TASK-105D` giữ nguyên `2 allowed / 0 used /
2 remaining`.

Impact:

- `docs/tasks/TASK-105D-product-identity-resolver.md` — Completion Gate viết
  lại thành 32 khối `#### CHECK-105D-NN (GNN)` có `Khẳng định` /
  `Fixture bắt buộc` / `PASS khi` / `FAIL khi` / `Nguồn quy phạm`; khối
  "Định nghĩa vận hành bắt buộc" sửa theo `DEC-156`/`OR-02`; thêm mục
  "Ma trận overlap có chủ đích"; sửa stale text ở "Resolution Order",
  "Human Confirmation và Batch UX Contract", "Phụ Thuộc" (mục Auth);
  Authority/Specification State/Ready Gate/Changed Files Registry cập nhật.
- `docs/reviews/TASK-105D-COMPLETION-GATE-CHANGE-PROPOSAL.md` — **file MỚI**,
  bản ghi thay đổi gate canonical (before/after từng gate, lý do, risk,
  invariant bị tác động, bảng 20 case đối kháng trước/sau).
- `PROJECT/PROJECT_DECISIONS.md` — `DEC-157` (ID đã quét toàn repo, trống
  trước khi cấp).
- `PROJECT/PROJECT_PROGRESS.md`, `PROJECT/REVIEW_BUDGET_LEDGER.md` —
  trạng thái, next authorized action, divergence record.
- `docs/sessions/S037-task-105d-gate-revision.md` — bàn giao.
- **Không** sửa `app/**`, `tests/**`, `config/**`, `tools/**`, `scripts/**`,
  `pyproject.toml`, `governance/**`, Golden fixture/expected.
- **Không** sửa `docs/spec/TASK-105D-DATA-CONTRACT.md` — vì vậy `H-05` còn mở.
- **Không** sửa repo `Tracking` — 0 file.
- **Không** implement, không activate provider, không freeze, không merge,
  không mở Repair Cycle.

Can Revisit After:

- Một phiên **Freeze Finalization retry** re-review TOÀN BỘ 32 gate đã sửa và
  ghi verdict ⇒ chỉ khi PASS thì `TASK-105D` mới có thể `READY`.
- **Ngay sau verdict đó**: review lại branch divergence theo Option C
  (`V4.1` §8) — đây là review point bắt buộc, không phải tuỳ chọn.
- Một phiên sửa data contract có thẩm quyền cho `H-05` (`ranking_method_id`).
- Một phiên soạn Scope Lock + Completion Gate cho `TASK-105E` (nơi phần còn
  lại của `H-02` — điều kiện (a) của `INV-43` — thuộc về).

## DEC-158

Title:
BRANCH DIVERGENCE `V4.1` §8 — OWNER CHỌN OPTION A (INTEGRATE EARLY);
CONTROLLED INTEGRATION CỦA `TASK-105D` READINESS/FREEZE LINEAGE

Date:
2026-08-28

Task:
Owner Decision recording cho phiên Controlled Readiness Integration
`TASK-105D`. Ghi trong phiên `docs/sessions/S039-task-105d-controlled-integration.md`.

```text
base SHA phiên này        : 573e051e093cd850c9efb13891bf6dee5654f0c6
integration branch        : integration/v4-1-task-105d-readiness
freeze SHA được hợp nhất  : a53af1d193d4023fcf90bcc8e55bb874eaae19fe
gate revision SHA         : be835b1b1b03d4e8d21656c3624b6e4bc964b7a1
```

**Đây LÀ một Owner Decision.** Owner mở phiên này với một quyết định tường
minh duy nhất (Decision A — divergence). Phiên **không** thêm quyết định
nghiệp vụ nào của riêng nó; toàn bộ nội dung được hợp nhất đã tồn tại nguyên
văn trong lineage đã review, và phiên chỉ (i) xác minh lại bằng chứng freeze
một cách độc lập, (ii) thực hiện hợp nhất giữ nguyên ancestry, (iii) ghi lại
bản ghi trạng thái.

Ghi chú artifact budget (`governance/core/V4_1_POLICY_FREEZE.md` §10): đây là
artifact governance thứ **9** của lineage `TASK-105D` (thứ 8 là `DEC-157` +
`S037`), tức thuộc diện `OWNER APPROVAL REQUIRED`. Approval đó **chính là**
chỉ thị của Owner khi mở phiên này ("Ghi canonical evidence: Owner selected
V4.1 §8 Option A — INTEGRATE EARLY"; "§15 FINAL REPORT"). Ghi lại tường minh
theo tiền lệ `DEC-156`/`DEC-157`.

Decision:

**1. OWNER DECISION A — BRANCH DIVERGENCE: `V4.1` §8 OPTION A.**

```text
V4.1 §8 — INTEGRATION_DECISION_REQUIRED  [ cumulative LOC > 5.000 ]
Owner chọn: (A) INTEGRATE EARLY.
Option C của DEC-157: KHÔNG gia hạn.
```

Lý do Owner ghi nhận:

```text
- Option C allowance của DEC-157 đã dùng hết (Gate Revision S037 +
  MỘT Freeze Finalization retry S038);
- Freeze Finalization Retry #2 đã hoàn thành, verdict PASS WITH HARDENING;
- TASK-105D đã READY; BLOCKING = 0;
- branch documentation divergence > 10.000 LOC;
- behind default = 0 tại thời điểm review (chưa có conflict thực tế);
- bước tiếp theo sẽ bắt đầu production implementation, và implementation
  phải xuất phát từ canonical default đã chứa readiness/freeze evidence.
```

Review point bắt buộc của `DEC-157` §2 ("ngay sau freeze finalization retry
verdict") **được đóng bằng chính quyết định này**. Ràng buộc "không mở
`TASK-105D` implementation trước divergence decision" nay đã thoả — nhưng
implementation **vẫn cần một phiên cấp phép riêng của Owner** (§3 dưới đây).

**2. Hợp nhất đã thực hiện — giữ nguyên ancestry.**

```text
phương pháp   : git merge --no-ff  (ancestry-preserving controlled merge)
                KHÔNG squash; KHÔNG cherry-pick rời từng file
conflict      : 0
merge commit  : e271c26770bb6b4cecd9d4a54aea4e12a183012c
tree sau merge: TRÙNG KHỚP BYTE-EXACT với a53af1d (git diff = rỗng)
```

Lineage được bảo toàn đầy đủ, gồm cả **bằng chứng thất bại** của Freeze
Attempt #1 (`7b89d4c`, verdict FAIL) — không rewrite, không loại bỏ:

```text
442404d → d3b73e5 → 9cd8714 → 7b89d4c → 1676e1d → 4c9c072 → be835b1 → a53af1d
```

**3. Trạng thái `TASK-105D` sau quyết định này — KHÔNG ĐỔI bởi hợp nhất.**

```text
TASK-105D            = READY
                       NOT IMPLEMENTED / NOT DONE
Completion Gate      = FROZEN  (32 check, GATE_SET_SHA256 0444e58c…)
Gate count           = 32   (không đổi)
Repair Cycle         = KHÔNG mở  (2 allowed / 0 used / 2 remaining)
production code      = KHÔNG đổi
test implementation  = KHÔNG đổi
merge                = ĐÃ THỰC HIỆN (đây là mục đích của phiên)
implementation       = KHÔNG bắt đầu; vẫn cần phiên cấp phép riêng của Owner
```

Controlled integration **không** tự động cấp quyền implementation.

**4. Bằng chứng freeze — xác minh lại độc lập trong phiên này.**

Phiên **không** dựa vào Final Report của phiên trước; mọi con số dưới đây
được tính lại từ chính văn bản canonical:

```text
GATE_SET_SHA256   : 0444e58c02b04804a116c140af722ffc29ea64adf468aa6c93794c4408a5c877
                    tái lập BYTE-EXACT (57.614 byte UTF-8)
TASK_FILE_SHA256  : a6be1ac71ac751eeefae30cf076f90e5d4cad80067c9441f78578e9972e028b1  KHỚP
TASK_FILE_GIT_BLOB: 804ba8379e0952a2210559c7eec86b4094957026                          KHỚP
gate count        : 32   (CHECK-105D-01…32, đếm từ văn bản, không khuyết ID)
Priority          : 32/32 REQUIRED
Status tại freeze : 32/32 NOT_TESTED
Evidence Level    : E2 = 19, E1 = 13
BLOCKING          : 0
gate semantics    : KHÔNG đổi giữa be835b1b và a53af1d (cùng GATE_SET_SHA256)
                    ⇒ commit freeze chỉ ghi TRẠNG THÁI, không sửa ngữ nghĩa
```

**5. HARDENING — preserve, KHÔNG repair.**

`H-05`, `HB-105D-F2-01`, `HB-105D-F2-02`, `HB-105D-F2-03` giữ nguyên phân
loại `HARDENING`, vẫn mở, re-trigger còn nguyên. Phiên này **không** nâng
chúng thành `BLOCKING` (không có evidence mới) và **không** hạ chúng khỏi
`HARDENING`. `docs/spec/TASK-105D-DATA-CONTRACT.md` **không** bị sửa.

**6. Repair Cycle — KHÔNG mở.**

`V4.1` §3 tính repair cycle theo cumulative **repair diff** trên một defect
`BLOCKING` của **implementation**. Phiên này không sửa một dòng code hay test
nào; toàn bộ diff là documentation/governance, và `BLOCKING = 0`. Ngân sách
`TASK-105D` giữ nguyên `2 allowed / 0 used / 2 remaining`.

Impact:

- Nhánh mặc định `claude/extract-upload-repo-gq2ws4` — nhận toàn bộ lineage
  readiness/freeze của `TASK-105D` qua controlled merge giữ ancestry.
- `PROJECT/PROJECT_DECISIONS.md` — `DEC-158` (ID đã quét toàn repo trên MỌI
  ref, trống trước khi cấp).
- `PROJECT/PROJECT_PROGRESS.md`, `PROJECT/REVIEW_BUDGET_LEDGER.md` —
  trạng thái sau hợp nhất, divergence record, next authorized action.
- `docs/sessions/S039-task-105d-controlled-integration.md` — bàn giao.
- **Không** sửa `app/**`, `tests/**`, `config/**`, `tools/**`, `scripts/**`,
  `pyproject.toml`, `governance/**`, Golden fixture/expected.
- **Không** sửa `docs/spec/TASK-105D-DATA-CONTRACT.md` — `H-05`,
  `HB-105D-F2-01`, `HB-105D-F2-02` còn mở.
- **Không** sửa repo `Tracking` — 0 file.
- **Không** implement, không activate provider, không re-freeze, không mở
  Repair Cycle, không unblock `TASK-108B`.

Can Revisit After:

- Một phiên **implementation `TASK-105D`** được Owner cấp phép riêng, chạy
  trên Completion Gate đã `FROZEN` (32 check, `GATE_SET_SHA256` `0444e58c…`);
  phiên đó phải xử lý `HB-105D-F2-03` và `H-05` khi chạm đúng vùng re-trigger.
- Một phiên sửa data contract có thẩm quyền cho `H-05` + `HB-105D-F2-01`.
- Một phiên soạn Scope Lock + Completion Gate cho `TASK-105E`
  (`HB-105D-F2-02`).
- `TASK-105C` refreeze (lineage riêng) — vẫn `BLOCKED / NOT AUTHORIZED`.

## DEC-159

Title:
`H-07` GATE EXECUTION RECONCILIATION — OWNER DECISION CÔNG NHẬN BẢN GHI
THỰC THI TÁCH RỜI (OPTION (b)), GIỮ NGUYÊN `GATE_SET_SHA256`

Date:
2026-08-28

Task:
Owner Decision recording cho phiên `S045` — TASK-105D H-07 Gate Execution
Reconciliation. Ghi trong
`docs/sessions/S045-task-105d-h07-reconciliation-and-capability-governance.md`
phần A.

```text
base SHA phiên này   : 7464ccaa784f13d887b2d5441d86136ff7d9a61d
branch                : governance/task-105d-gate-execution-reconciliation
GATE_SET_SHA256       : 0444e58c02b04804a116c140af722ffc29ea64adf468aa6c93794c4408a5c877
                         (TRƯỚC == SAU phiên này — tái lập trực tiếp)
```

**Đây LÀ một Owner Decision.** Chỉ thị mở phiên nêu tường minh Owner ưu
tiên Option (b) cho `H-07`. Phiên chỉ (i) xác minh lại độc lập toàn bộ bằng
chứng gate/execution-record, (ii) phân tích thẩm quyền theo
`governance/core/TASK_COMPLETION_GATE_STANDARD.md` và `V4.1` §12, (iii) ghi lại quyết định
tường minh, và (iv) phát hiện một xung đột validator riêng biệt (xem mục
5 dưới đây) mà quyết định này **không** tự đóng.

Ghi chú artifact budget (`governance/core/V4_1_POLICY_FREEZE.md` §10): đây
là artifact governance thứ 10 của lineage `TASK-105D` (nối tiếp `DEC-158` /
artifact #9), thuộc diện `OWNER APPROVAL REQUIRED`. Approval đó **chính là**
chỉ thị của Owner khi mở phiên `S045` ("Owner preferred Option (b)"), ghi
lại tường minh theo tiền lệ `DEC-156`/`DEC-157`/`DEC-158`.

Decision:

**1. OWNER DECISION — HAI LỚP TRẠNG THÁI (Option (b)).**

```text
Frozen Gate Status      = metadata tại thời điểm freeze (NOT_TESTED, 32/32
                           — KHÔNG đổi, vĩnh viễn, cho đúng
                           GATE_SET_SHA256 = 0444e58c…4408a5c877 này)
Effective Completion
  Status (per check)    = trạng thái trong bản ghi thực thi tách rời, MIỄN
                           LÀ thoả cả 8 điều kiện binding dưới đây
```

8 điều kiện ràng buộc cho "Effective Completion Status" hợp lệ (tất cả đã
kiểm chứng lại độc lập cho 32 check của `TASK-105D` trong `S045` §A6/A7):

```text
1. frozen gate definition giữ nguyên byte-identical
2. tồn tại một Gate Execution Record canonical
3. record bind đúng GATE_SET_SHA256
4. record định danh đúng REQUIRED check ID
5. execution result = PASS
6. required Evidence Level được thoả
7. implementation/review lineage được bind
8. không có execution record thẩm quyền sau đó ghi đè bằng FAIL/INVALID
```

**2. LÝ DO — TẠI SAO KHÔNG PHẢI OPTION (c).**

`governance/core/TASK_COMPLETION_GATE_STANDARD.md` (đọc toàn văn 150 dòng
trong `S045`) không quy định Evidence Record của một REQUIRED check phải
nằm vật lý trong khối gate đã hash-freeze — đây là một khoảng trống diễn
giải, không phải một điều cấm tường minh. Vì vậy Option (b) hợp lệ như một
diễn giải được Owner phê chuẩn tường minh, không cần sửa
`governance/core/TASK_COMPLETION_GATE_STANDARD.md` (Option (c)).

**3. `GATE_SET_SHA256` KHÔNG ĐỔI — xác minh lại.**

```text
$ sed -n '631,2359p' docs/tasks/TASK-105D-product-identity-resolver.md | sha256sum
0444e58c02b04804a116c140af722ffc29ea64adf468aa6c93794c4408a5c877
```

Khớp tuyệt đối với giá trị freeze `S038`. 0 byte thay đổi trong khối gate
bởi quyết định này.

**4. `H-07` — disposition sau quyết định này.**

```text
H-07 = PARTIALLY RECONCILED
  lớp diễn giải/thẩm quyền  : RESOLVED (quyết định này)
  lớp validator             : VẪN OPEN (mục 5)
H-07 CLOSED?  KHÔNG.
```

**5. Xung đột validator — KHÔNG tự đóng bằng quyết định này.**

`governance/scripts/governance/validate_task_completion.py` xác định điều
kiện `DONE` bằng cách grep literal trường `Status:` nhúng vật lý trong từng
khối `#### CHECK-*`; nó không có khái niệm Gate Execution Record tách rời.
Theo mô hình hai lớp vừa quyết định, 32 trường đó **giữ nguyên `NOT_TESTED`
vĩnh viễn** theo thiết kế — nghĩa là validator, ở dạng hiện tại, sẽ FAIL cả
32 REQUIRED check nếu một phiên tương lai đặt `TASK-105D` top-level
`Status: DONE`. Quyết định này **không** trao quyền sửa
`governance/scripts/governance/*.py` (nằm ngoài governance/documentation
reconciliation của phiên `S045`) — mục này ghi nhận xung đột để một phiên
có thẩm quyền tooling riêng xử lý.

Impact:

- `PROJECT/PROJECT_PROGRESS.md` — trạng thái `TASK-105D` sau `S045`, ghi
  `H-07 = PARTIALLY RECONCILED`, `TASK-105D = STILL_BLOCKED_BEFORE_DONE`.
- `PROJECT/REVIEW_BUDGET_LEDGER.md` — bổ sung bản ghi `S045` vào
  "Root Task: TASK-105D"; ngân sách `2 allowed / 1 used / 1 remaining`
  **KHÔNG đổi**.
- `docs/sessions/S045-task-105d-h07-reconciliation-and-capability-governance.md`
  — bàn giao đầy đủ Phần A.
- **Không** sửa `app/**`, `tests/**`, `config/**`, `tools/**`, `scripts/**`,
  `pyproject.toml`, `docs/tasks/TASK-105D-product-identity-resolver.md`,
  `docs/spec/TASK-105D-DATA-CONTRACT.md`, `governance/scripts/governance/*.py`.
- **Không** mở Repair Cycle #2. **Không** đánh dấu `TASK-105D = DONE`.

Can Revisit After:

- Một phiên có thẩm quyền tooling/governance-scripts, được Owner cấp phép
  riêng, đối chiếu `validate_task_completion.py` với mô hình hai lớp ở
  quyết định này — HOẶC Owner chấp nhận rằng `DONE` thật sự sẽ cần một
  `COMPLETION GATE CHANGE PROPOSAL` riêng (mutate 32 trường `Status:`, đổi
  `GATE_SET_SHA256`) tại đúng thời điểm đó.

## DEC-160

Title:
CAPABILITY-FIRST DELIVERY GOVERNANCE — ĐĂNG KÝ `CAP-PRICE-RESOLUTION` +
KIỂM SOÁT PHÂN RÃ TASK ANH EM (HORIZONTAL SIBLING PROLIFERATION)

Date:
2026-08-28

Task:
Owner Decision recording cho phiên `S045`, Phần B — Capability-First
Delivery và Horizontal Task Proliferation Control. Ghi trong
`docs/sessions/S045-task-105d-h07-reconciliation-and-capability-governance.md`
phần B.

**Đây LÀ một Owner Decision.** Chỉ thị mở phiên đặt toàn bộ khung §B1-B16
tường minh, gồm capability root, member tasks, vertical acceptance slice
compass, và cơ chế chống phân rã task anh em ngang hàng.

Ghi chú artifact budget: cùng lineage governance-session với `DEC-159`
(artifact governance thứ 11 của `TASK-105D` — do `CAP-PRICE-RESOLUTION`
chưa có lineage ngân sách riêng, phần lớn nội dung DEC này gắn với
`TASK-105D` như root task đang mở phiên). Approval = chỉ thị mở phiên
`S045`.

Decision:

**1. ĐĂNG KÝ CAPABILITY — KHÔNG PHẢI TASK.**

```text
CAP-PRICE-RESOLUTION
  business purpose : từ một dòng bán hàng, xác định tất yếu định danh sản
                      phẩm đúng và cơ sở giá mua áp dụng, trả về
                      KpiPurchasePrice đã resolve + đầy đủ provenance
  member tasks      : TASK-105B, TASK-105C, TASK-105D, TASK-105E
  outside           : TASK-108B (downstream consumer)
```

Đây là **CAPABILITY REGISTRATION**, không phải **TASK REGISTRATION**
(`CAP-PRICE-RESOLUTION` không mang tiền tố `TASK-*`, không có Task Spec
dưới `docs/tasks/`).

**2. VERTICAL ACCEPTANCE SLICE — `END_TO_END_ACCEPTANCE = PENDING_OWNER_DATA`.**

```text
SALES_RECORD có thật : OrderID BH62063, 2026-01-02, qty 1, sell price
                        7.500.000 VND, discount 0
                        (nguồn: tests/fixtures/golden/period_2026_01.xlsx,
                        cột VERBATIM theo anonymize.py)
PRODUCT               : "Máy giặt LG 10kg FV1410S4W1" — CHƯA có canonical
                        identity mapping đã Owner-confirm
PRICE_SOURCE           : KHÔNG có — 100% (351/351) dòng thật kỳ 01.2026 có
                        purchase price = Pending; mọi fixture TASK-105B/
                        TASK-105C hiện có đều synthetic (tự khai trong
                        chính hai task đó)
MANUAL_ORACLE          : EligibleKpiProfit = (SellPrice − KpiPurchasePrice)
                        × Quantity − Discount (xác nhận cuối cùng tại
                        docs/tasks/TASK-108B-eligible-costs-owner-definition.md:1040)
                        = 7.500.000 − KpiPurchasePrice  (KpiPurchasePrice
                        chưa có)
```

Không dữ liệu tổng hợp/bịa nào được dùng thay thế. `MISSING_DATA` +
`OWNER_INPUT_REQUIRED` đầy đủ tại
`PROJECT/PROJECT_PROGRESS.md` → `CAP-PRICE-RESOLUTION` → `END_TO_END_ACCEPTANCE`.

**3. KHÔNG TASK MỚI ĐƯỢC TẠO.**

```text
new_registered_task_ids = 0
proposals_created        = 0
REGISTERED_TASK_SET (task ID có "= STATUS"/"Status:" tường minh trong
    PROJECT/PROJECT_PROGRESS.md — KHÔNG phải grep tự do mọi chuỗi TASK-*,
    brief §B8 cấm cách đo đó) BEFORE = 13   AFTER = 13
TASK_SPEC_SET (docs/tasks/*.md) BEFORE = 22   AFTER = 22
```

Không hạng mục nào trong phiên thoả đồng thời cả ba điều kiện độc lập
capability + độc lập lifecycle + nằm ngoài `CAP-PRICE-RESOLUTION`.

**4. CAPABILITY-LEVEL REPAIR BUDGET — RECONSTRUCTION, PROPOSED, CHƯA ADOPTED.**

```text
capability_repair_cycles_allowed (Owner PROPOSAL) : 4
consumed:
  TASK-105B-RC-1  base c22cef8b47ac4cd71ef49609066a362c9e604313
                  head 7f7048d65619c2c2198c99ccbfb073d6cb97ebe2
  TASK-105D-RC-1  base e6252c06347ed5305fc32a77706a3a63f5a950cf
                  head 1cc96a99638326513b26280b72bbeb3bce9d454d
capability_repair_cycles_used      = 2
capability_repair_cycles_remaining = 2   (chỉ có hiệu lực NẾU ADOPTED)
migration_status                   = PROPOSED
```

Ngân sách per-task hiện hành (`TASK-105B` 2/1/1, `TASK-105C` 2/0/2,
`TASK-105D` 2/1/1, `TASK-105E` 2/0/2) **giữ nguyên, authoritative**, không
đổi bởi bảng trên. Trong lúc `migration_status ≠ ADOPTED`, không task nào
trong capability được cấp Repair Cycle budget mới chỉ vì nay được nhóm lại.

**5. CORE GOVERNANCE CHANGE PROPOSAL — CHƯA ADOPTED.**

```text
docs/reviews/CAP-PRICE-RESOLUTION-CORE-GOVERNANCE-CHANGE-PROPOSAL.md
```

chứa đề xuất §16 (nguyên tắc capability-first sibling-proliferation control,
absorption limit, capability repair-budget semantics, migration transition
rule) cho `governance/core/V4_1_POLICY_FREEZE.md`. Phiên `S045` không có
CORE-amendment authority; `governance/core/V4_1_POLICY_FREEZE.md` = 0 byte
thay đổi.

```text
CAPABILITY_GOVERNANCE_VERDICT = PROPOSED_PENDING_CORE_AUTHORITY
```

Impact:

- `PROJECT/PROJECT_PROGRESS.md` — section `CAP-PRICE-RESOLUTION` mới.
- `PROJECT/REVIEW_BUDGET_LEDGER.md` — section capability-level migration
  analysis mới, đánh dấu `PROPOSED`.
- `docs/reviews/CAP-PRICE-RESOLUTION-CORE-GOVERNANCE-CHANGE-PROPOSAL.md` —
  artifact mới.
- **Không** sửa `governance/core/V4_1_POLICY_FREEZE.md`.
- **Không** implement `TASK-105B/C/E/108B`. **Không** activate
  `FilePriceProvider`. **Không** mutate `Tracking`.

Can Revisit After:

- Owner cung cấp dữ liệu còn thiếu ở `MISSING_DATA` để
  `END_TO_END_ACCEPTANCE` chuyển `DEFINED`.
- Một phiên có CORE-amendment authority xem xét đề xuất §16 để `ADOPTED`.
- Owner quyết định `migration_status` cho ngân sách capability-level.

## DEC-161

Title:
`H-07` VALIDATOR ALIGNMENT — `validate_task_completion.py` NAY CÔNG NHẬN
LAYER 2 (GATE EXECUTION RECORD) THEO 8 ĐIỀU KIỆN BINDING CỦA `DEC-159`

Date:
2026-08-28

Task:
Ghi kết quả phiên `S046` — TASK-105D H-07 Validator Alignment (tooling).
Ghi đầy đủ trong `docs/sessions/S046-task-105d-h07-validator-alignment.md`.

**Đây LÀ một Owner Decision record.** Chỉ thị mở phiên ("TASK-105D H-07 —
VALIDATOR ALIGNMENT") tường minh cấp thẩm quyền tooling/governance-scripts
mà `DEC-159` "Can Revisit After" đã nêu là điều kiện đóng lớp validator
của `H-07`.

Decision:

**1. `governance/scripts/governance/validate_task_completion.py` đã được
sửa để implement đúng 8 điều kiện binding của `DEC-159` §1** cho một
REQUIRED check có embedded `Status: NOT_TESTED` (frozen placeholder theo
thiết kế): tồn tại một Gate Execution Record canonical
(`docs/reviews/TASK-<ID>-GATE-EXECUTION-RECORD*.md`, suy ra `<ID>` từ tên
file task — không hardcode `105D`) bind đúng `GATE_SET_SHA256` + đúng check
ID + kết quả PASS + Evidence Level hợp lệ + Evidence cụ thể + lineage
(`Executed By`) — và fail-closed trên: thiếu record, sai hash, thiếu check
ID, kết quả FAIL/khác PASS, thiếu lineage, và **duplicate/ambiguous
authoritative records** (nếu ≥2 record cùng bind đúng hash + đúng check ID
nhưng cho kết quả khác nhau, validator không đoán — coi là chưa thoả).
Đường đi Layer 1 (`Status: PASS` literal, hành vi validator gốc) giữ
nguyên 100%, không đổi một thông điệp lỗi nào.

**2. Xác nhận bằng 10 test tập trung**
(`tests/test_governance_validate_task_completion.py`) + một mô phỏng trên
chính dữ liệu thật của `TASK-105D` (patch top-level `Status: DONE` trong bộ
nhớ/thư mục tạm, không mutate `docs/tasks/TASK-105D-product-identity-resolver.md`)
cho kết quả `32/32 PASS`, `0 lỗi`, qua đúng
`docs/reviews/TASK-105D-GATE-EXECUTION-RECORD.md` thật.

**3. Một bug thật phát hiện và sửa trong chính phiên này** (không phải bởi
người review khác): bản draft đầu dùng nguyên văn heading khối check
(`"CHECK-105D-01 (G01) — mô tả..."`) làm khoá tra cứu Gate Execution
Record, trong khi bảng record dùng ID trần (`CHECK-105D-01`) — khiến mô
phỏng trên dữ liệu thật FAIL cả 32/32 dù 9 test fixture tối giản ban đầu
đều PASS (fixture không tái lập đúng hình dạng heading thật). Sửa bằng cách
tách riêng token ID khỏi heading đầy đủ; thêm test hồi quy
`test_check_heading_with_trailing_description_resolves`. Chi tiết đầy đủ:
`docs/sessions/S046-task-105d-h07-validator-alignment.md` §5.1/§8.

**4. `GATE_SET_SHA256` KHÔNG ĐỔI — xác minh lại trước và sau.**

```text
$ sed -n '631,2359p' docs/tasks/TASK-105D-product-identity-resolver.md | sha256sum
0444e58c02b04804a116c140af722ffc29ea64adf468aa6c93794c4408a5c877
```

Khớp tuyệt đối TRƯỚC và SAU phiên này. `docs/tasks/TASK-105D-product-identity-resolver.md`
0 byte thay đổi.

**5. `H-07` — disposition sau quyết định này.**

```text
H-07 = RECONCILED (cả hai lớp)
  lớp diễn giải/thẩm quyền  : RESOLVED (DEC-159, không đổi bởi phiên này)
  lớp validator             : RESOLVED (quyết định này)
H-07 mechanical blocker CLOSED? CÓ.
```

**6. `TASK-105D` vẫn KHÔNG `DONE`.** Đóng điều kiện #7 của `DEC-159` chỉ
giải quyết đúng một trong nhiều điều kiện `Tiêu Chí Hoàn Thành`
(`governance/core/TASK_COMPLETION_GATE_STANDARD.md`) — 0 BLOCKING finding
re-verify, Independent Review cho chính hành động DONE, INV-01…INV-87, và
progress/handoff cho DONE đều **chưa** được phiên này đánh giá (ngoài thẩm
quyền, brief cấm). `TASK-105D` **eligible for DONE review** (blocker cơ
học cuối cùng đã đóng) nhưng **không phải DONE**.

Impact:

- `governance/scripts/governance/validate_task_completion.py` — sửa (xem
  §3 của session log cho diff đầy đủ). Layer 1 không đổi hành vi.
- `tests/test_governance_validate_task_completion.py` — file test mới,
  10 test.
- `PROJECT/PROJECT_PROGRESS.md` — cập nhật trạng thái `H-07` sau `S046`.
- `docs/sessions/S046-task-105d-h07-validator-alignment.md` — bàn giao đầy
  đủ.
- **Không** sửa `app/**`, `config/**`, `docs/tasks/TASK-105D-product-identity-resolver.md`,
  `docs/spec/TASK-105D-DATA-CONTRACT.md`, `governance/core/**`, `Tracking`.
- **Không** mở Repair Cycle #2. **Không** tạo task mới. **Không** đánh dấu
  `TASK-105D = DONE`. **Không** chạm `TASK-105B/C/E/108B`. **Không** thực
  hiện V4.2 migration. **Không** merge nhánh này vào nhánh mặc định.

Can Revisit After:

- Một phiên DONE-review có thẩm quyền completion đánh giá 4 điều kiện còn
  lại (0 BLOCKING re-verify, Independent Review cho hành động DONE,
  INV-01…INV-87, progress/handoff) rồi mới được đặt `TASK-105D` top-level
  `Status: DONE`.

## DEC-162

Title:
`TASK-105D = DONE` — ĐÓNG `INV-81`/`INV-82` EVIDENCE GAP (`H-06`), ĐÓNG
ĐIỀU KIỆN CUỐI CÙNG CỦA `S047`

Date:
2026-08-29

Task:
Ghi kết quả phiên `S048` — TASK-105D INV-81/INV-82 Evidence Closure. Ghi đầy
đủ trong `docs/reviews/TASK-105D-INV81-INV82-EVIDENCE-CLOSURE.md` và
`docs/sessions/S048-task-105d-inv81-inv82-evidence-closure.md`.

**Đây LÀ một Owner Decision record.** Chỉ thị mở phiên ("S048 — TASK-105D
INV-81 / INV-82 EVIDENCE CLOSURE") tường minh liệt kê toàn bộ điều kiện DONE
còn lại theo `DEC-161` §6, yêu cầu phiên tự đối chiếu lại từng điều kiện, và
tường minh cấp phép: *"Nếu authority cho phép: → cập nhật minimum canonical
state/evidence → TASK-105D = DONE."* Cùng cấu trúc chỉ thị mà `DEC-161` đã
công nhận là Owner Decision cấp thẩm quyền cho phạm vi hẹp của chính phiên
đó (§ "Đây LÀ một Owner Decision record" của `DEC-161`). Áp dụng đúng tiền lệ
đó ở đây.

Decision:

**1. `INV-81`.** Classification A (production behavior đã tồn tại: `rollback_of`
được `PublicPurchaseSourceLoader.load()` đọc trực tiếp từ `data`, dòng 219 —
không có API "rollback" riêng, rollback = một `publish()` thường với
`rollback_of` set; test cũ dùng `object.__setattr__` bơm field sau khi dựng
fixture, bỏ qua đường parse thật). Sửa: `tests/support/identity_fixtures.py`
thêm tham số `rollback_of` cho `pp_version()` (đi đúng khoá loader đọc);
`tests/test_105d_boundaries.py::test_inv81_…` viết lại để dựng version
rollback qua loader thật, cộng assertion mới `repo.get(PP_V1) == original`
chứng minh version cũ 0 byte đổi. `INV-81 = PASS`.

**2. `INV-82`.** Classification B (test G21 —
`tests/test_105d_audit_replay.py::TestG21ProvenanceActorAndReplay::test_part_c_replay_is_identical_after_store_catalog_and_price_change`
— đã chứng minh đầy đủ qua đường replay thật; xác minh độc lập tại `S048`
rằng `rollback_of` không được rẽ nhánh ở bất kỳ đường nào khác trong `app/`
ngoài parse/khai báo khoá, nên một publish có `rollback_of` và một publish
thường đi qua CÙNG một đường replay — G21 là trường hợp tổng quát hơn, chứng
minh luôn trường hợp rollback). KHÔNG viết test trùng lặp. Evidence binding
ghi tại `docs/reviews/TASK-105D-INV81-INV82-EVIDENCE-CLOSURE.md` §5.
`INV-82 = PASS`.

**3. `H-06` = RESOLVED.** Cả hai vế của finding gốc (`object.__setattr__` ở
`test_inv81_…`, và claim "chứng minh đầy đủ nằm ở G21" của `test_inv82_…`
chưa được xác minh độc lập) đã được xử lý trực tiếp, không chỉ vì test suite
PASS. Mapping đầy đủ: `docs/reviews/TASK-105D-INV81-INV82-EVIDENCE-CLOSURE.md`
§6.

**4. `GATE_SET_SHA256` KHÔNG ĐỔI — xác minh lại trước và sau.**

```text
$ sed -n '631,2359p' docs/tasks/TASK-105D-product-identity-resolver.md | sha256sum
0444e58c02b04804a116c140af722ffc29ea64adf468aa6c93794c4408a5c877
```

Khớp tuyệt đối TRƯỚC và SAU phiên này. Thay đổi Status field (dòng 5-6) và
Exit Criteria (dòng 2378-2396) đều nằm NGOÀI vùng frozen 631-2359.

**5. `TASK-105D` chuyển `Status: DONE`.** 8 điều kiện đóng gói trong `DEC-159`
§1 cho `H-07` vẫn `PASS` (không đổi bởi phiên này). 4 điều kiện `DEC-161` §6
để ngỏ nay đối chiếu lại đầy đủ tại `docs/reviews/TASK-105D-INV81-INV82-EVIDENCE-CLOSURE.md`
§9: 0 BLOCKING re-verify PASS (không đổi), Independent Review cho hành động
DONE PASS (thực hiện tại `S047`, không lặp lại), `INV-01`…`INV-87` PASS
(thay đổi duy nhất so với `S047` — `INV-81`/`INV-82` nay PASS),
progress/handoff cập nhật PASS (khối này + `S048`). `validate_task_completion.py`
xác nhận Layer 2 PASS thật trên dữ liệu thật sau khi mutate Status field
(`Checked 7 DONE task(s)`, `0 lỗi`).

```text
TASK-105D = DONE
```

**6. Repair Budget KHÔNG ĐỔI.** `allowed = 2, used = 1, remaining = 1`. Toàn
bộ thay đổi ở `S048` là test-strengthening + evidence-binding +
completion-evidence correction — không phải production repair
(`V4.1` §12) — nên không tiêu Repair Cycle. Repair Cycle #2 KHÔNG mở.

**7. HARDENING mở còn lại (14 mục) KHÔNG chặn DONE.** Không mục nào có
production path hiện tại (`V4.1` §5) — kết luận này không đổi qua `S044`…
`S048`. `H-06` chuyển từ 14 xuống còn phần của danh sách đã RESOLVED (§3) —
13 mục HARDENING còn lại vẫn OPEN, không mục nào chặn DONE.

Impact:

- `tests/support/identity_fixtures.py`, `tests/test_105d_boundaries.py` —
  sửa (evidence, không phải production).
- `docs/tasks/TASK-105D-product-identity-resolver.md` — `Status: READY →
  DONE`, Exit Criteria đánh dấu `[x]`, thêm mục `## DONE Transition` — tất cả
  NGOÀI vùng frozen 631-2359.
- `docs/reviews/TASK-105D-INV81-INV82-EVIDENCE-CLOSURE.md`,
  `docs/sessions/S048-task-105d-inv81-inv82-evidence-closure.md` — tài liệu
  mới.
- `PROJECT/PROJECT_PROGRESS.md` — cập nhật trạng thái sau `S048`.
- **Không** sửa `app/**`, `config/**`, `Tracking`, `governance/core/**`,
  vùng frozen của `docs/tasks/TASK-105D-product-identity-resolver.md`.
- **Không** mở Repair Cycle #2. **Không** tạo task mới. **Không** chạm
  `TASK-105B/C/E/108B`. **Không** thực hiện V4.2 migration. **Không** merge
  nhánh này vào nhánh mặc định.

Can Revisit After:

- Golden Order `BH62063` — vertical critical path kế tiếp
  (`CAP-PRICE-RESOLUTION`), KHÔNG mở trong `S048`.

## DEC-163

Title:
`GOLDEN ORDER #1 (BH62063) CANONICAL ACCEPTANCE` — `END_TO_END_ACCEPTANCE`
CHUYỂN `PENDING_OWNER_DATA` → `DEFINED`

Date:
2026-08-29

Task:
Ghi kết quả phiên `S049` — Golden Order #1 Canonical Acceptance. Ghi đầy đủ
trong `docs/sessions/S049-golden-order-1-canonical-acceptance.md`.

**Đây LÀ một Owner Decision record.** Chỉ thị mở phiên ("S049 — GOLDEN
ORDER #1 CANONICAL ACCEPTANCE") cung cấp trực tiếp toàn bộ dữ liệu
Owner-confirmed còn thiếu mà `PROJECT/PROJECT_PROGRESS.md` →
`CAP-PRICE-RESOLUTION` → `END_TO_END_ACCEPTANCE` liệt kê ở
`MISSING_DATA`/`OWNER_INPUT_REQUIRED` (S045), và yêu cầu tường minh: persist
dữ liệu này thành canonical project truth với thay đổi nhỏ nhất có thể. Áp
dụng cùng tiền lệ cấp thẩm quyền hẹp mà `DEC-161`/`DEC-162` đã công nhận
cho brief mở phiên của chính chúng.

Decision:

**1. `END_TO_END_ACCEPTANCE = DEFINED`.** Toàn bộ `MISSING_DATA` mà S045
liệt kê nay có giá trị Owner-confirmed — xem
`PROJECT/PROJECT_PROGRESS.md` → `CAP-PRICE-RESOLUTION` →
`END_TO_END_ACCEPTANCE` (đã cập nhật tại chỗ, cùng một canonical location,
KHÔNG tạo framework acceptance song song).

```text
OrderID                  : BH62063
SaleDate                 : 2026-01-02
RawProductName            : "Máy giặt LG 10kg FV1410S4W1"
TrackingCode              : FV1410S4W1
PublicPurchaseCode        : FV1410S4W1
ExpectedCanonicalIdentity : TRACKING:FV1410S4W1
ExpectedPriceSource       : "Tồn"
ApplicablePriceDate       : 2026-01-02
ExpectedPurchasePrice     : 7.000.000 VND
Quantity                  : 1
SellPrice                 : 7.500.000 VND
Discount                  : 0 VND
ExpectedEligibleKpiProfit : 500.000 VND
```

**2. "Tồn" semantic guard — giữ nguyên, KHÔNG suy diễn mapping kỹ thuật.**
`ExpectedPriceSource = "Tồn"` là business oracle Owner xác nhận. Repo
KHÔNG tự gán "Tồn" cho phist NCC, Public Purchase, hay inv.cong.

```text
OWNER_EXPECTED_SOURCE     = "Tồn"
TECHNICAL_SOURCE_MAPPING  = UNRESOLVED
```

Điều này KHÔNG khiến acceptance quay lại `PENDING_OWNER_DATA` — business
oracle đã `DEFINED`; technical path cho "Tồn" là việc của session AS-IS kế
tiếp (`S050`), không phải của `S049`.

**3. Public Purchase = fallback được authorize, KHÔNG phải preferred
source.** Owner cho phép dùng Public Purchase code (`FV1410S4W1`) CHỈ khi
preferred price path (nguồn "Tồn") không có giá phù hợp áp dụng tại
`2026-01-02`. Không coi Public Purchase là default/preferred cho Golden
Order #1.

**4. Identity guard — mapping riêng cho `BH62063`, KHÔNG phải quy tắc
toàn cục.** `TrackingCode == PublicPurchaseCode == FV1410S4W1` và
`ExpectedCanonicalIdentity = TRACKING:FV1410S4W1` là Owner-confirmed
**cho đúng đơn này**. Đây KHÔNG thiết lập giả định "mọi Tracking code
trùng Public Purchase code đều là cùng sản phẩm" cho production path.
Không thêm production mapping record — đây là dữ liệu acceptance, không
phải hành vi implementation.

**5. Price unit guard.** Giá trị hiển thị Owner mô tả (`7.000` nghìn VND)
được normalize DUY NHẤT MỘT LẦN thành `7.000.000 VND` (canonical, dùng
trong toàn bộ oracle). Không nhân ×1000 lần thứ hai ở bất kỳ chỗ nào khác
đề cập tới con số này.

```text
SOURCE_DISPLAY_VALUE = 7.000
SOURCE_UNIT          = THOUSAND_VND
CANONICAL_VALUE      = 7.000.000 VND
```

**6. Golden relationship — hạt giống, không phải framework thứ hai.**
`BH62063` là business seed / end-to-end oracle mà Golden Baseline hiện có
(58 passed, 2 skipped, KHÔNG đổi trong `S049`) có thể bao phủ về sau, khi
authority triển khai cho phép. Không tạo Golden framework song song.

**7. `TASK-105D` giữ nguyên `DONE`.** Không reopen, không re-review
`H-06`/`H-07`/`INV-01`…`INV-87`/`B-01`. `DEC-162` giữ nguyên là bản ghi
DONE canonical.

**8. Không đăng ký task mới.** `CAP-PRICE-RESOLUTION` là capability
registration đã có từ `DEC-160` (S045) — `S049` không thêm task ID, không
mở `TASK-105C`/`TASK-105E`/`TASK-108B`, không thực hiện V4.2 adoption.

```text
new_registered_task_ids = 0
SET A (REGISTERED_TASK_SET) BEFORE = 13   AFTER = 13
SET B (TASK_SPEC_SET)       BEFORE = 22   AFTER = 22
```

**9. Critical path kế tiếp — trace, không phải implementation.** Sau
`S049`, bước kế tiếp là `RUN BH62063 THROUGH CURRENT SYSTEM AS-IS` để xác
định `FIRST_FAILING_BOUNDARY` thật (`S050 — GOLDEN ORDER #1 AS-IS
VERTICAL TRACE`). Không tự gán trước `TASK-105C`/`TASK-105E`/`TASK-108B`
là bước kế tiếp — chỉ AS-IS execution mới được xác nhận boundary đó.

Impact:

- `PROJECT/PROJECT_PROGRESS.md` — `END_TO_END_ACCEPTANCE` cập nhật tại chỗ
  (`PENDING_OWNER_DATA → DEFINED`), thêm mục "Trạng thái sau GOLDEN ORDER
  #1 CANONICAL ACCEPTANCE (S049...)" và "HÀNH ĐỘNG KẾ TIẾP ĐƯỢC PHÉP (S049
  → …)".
- `PROJECT/PROJECT_DECISIONS.md` — `DEC-163` (bản ghi này).
- `docs/sessions/S049-golden-order-1-canonical-acceptance.md` — tài liệu
  mới (bàn giao session).
- **Không** sửa `app/**`, `config/**`, `Tracking`, `governance/core/**`,
  bất kỳ file test nào.
- **Không** mở task mới, không mở Repair Cycle, không thực hiện V4.2
  migration, không chạm `TASK-105B/C/E/108B`.
- **Không** merge nhánh `governance/golden-order-1-canonicalize` vào nhánh
  mặc định trong phiên `S049`.

Can Revisit After:

- `S050 — GOLDEN ORDER #1 AS-IS VERTICAL TRACE` chạy `BH62063` qua hệ
  thống hiện tại và xác định `FIRST_FAILING_BOUNDARY` thật.
- Một session sau đó xác định technical source mapping cho `"Tồn"` (hiện
  `UNRESOLVED`), dựa trên boundary mà `S050` phát hiện.

## DEC-164

Title:
`GOLDEN #3 — QUANTITY + DISCOUNT` — Owner-confirmed purchase price cho đơn
thật thứ hai (`BH62439`), đăng ký entry `HistoricalConfirmedRegistry` mới.

Date:
2026-08-29

Task:
Ghi kết quả phiên `S057` — Golden #3 (`docs/sessions/S057-golden-3-quantity-discount.md`).
Nhánh `implementation/golden-3-quantity-discount`, base `89c0a27a`.

**Đây LÀ một Owner Decision record.** Golden #3 yêu cầu MỘT đơn hàng thật
với `Quantity > 1 AND Discount != 0` chạy qua `run_import_production()` và
cho ra `AccountingPurchasePrice`/`AccountingProfit`/`KpiPurchasePrice`/
`EligibleKpiProfit` khớp oracle. Quét cả hai kỳ thật (`period_2026_01.xlsx`,
`period_2026_06.xlsx`) tìm được đúng 3 dòng thoả điều kiện, nhưng CẢ BA đều
`Pending` vì `data/historical_confirmed/registry.jsonl` (nguồn giá vốn duy
nhất cho mọi dòng pre-cutover) khi đó chỉ có một entry, khoá riêng cho
`BH62063` (`INV-52`). Đây chính là lớp blocker khiến Golden #2
(`implementation/golden-2-historical-vendor`) `WAITING_REAL_DATA` — session
này KHÔNG bịa giá vốn để né blocker, mà hỏi trực tiếp Owner qua
`AskUserQuestion` và nhận được giá vốn thật cho một trong ba candidate.

Decision:

**1. Chọn `BH62439` — Điều hòa Daikin FTHF25XVMV làm Golden #3 case.**
Owner chọn candidate này trong ba candidate thật được liệt kê
(`BH62439`/Daikin, `BH63153`/Tivi LG, `BH63608`/Tivi Samsung).

```text
OrderID              : BH62439
SaleDate             : 2026-01-08
RawProductName       : "Điều hòa Daikin FTHF25XVMV" (source_row=52, 1 trong 4 dòng của đơn)
TrackingCode         : FTHF25XVMV
ExpectedIdentity     : TRACKING:FTHF25XVMV
Quantity             : 2
SellPrice            : 10.500.000 VND
Discount             : 100.000 VND
ExpectedPurchasePrice: 10.250.000 VND
ExpectedAccountingProfit  = (10.500.000 - 10.250.000) × 2            = 500.000 VND
ExpectedEligibleKpiProfit = (10.500.000 - 10.250.000) × 2 - 100.000  = 400.000 VND
```

**2. Provenance — cùng cơ chế `BH62063`, KHÔNG phải historical replay đã
verify.** Owner xác nhận giá vốn 10.250.000 VND là giá "Tồn"/giá mua công
khai của mã `FTHF25XVMV` trên Tracking tại thời điểm bán (2026-01-08);
Tracking hiện không giữ snapshot lịch sử reopenable cho ngày đó (LEGACY DATA
GAP). Entry ghi `provenance = OWNER_MANUAL_LEGACY_CONFIRMATION` (KHÔNG
`HISTORICAL_CONFIRMED_REPORT`) — đúng tiền lệ `BH62063` (`DEC-163`).

**3. Registry entry mới, KHÔNG sửa entry `BH62063`.** Thêm ĐÚNG một dòng
`HCR-BH62439-20260108-1` vào `data/historical_confirmed/registry.jsonl`,
dựng qua `HistoricalConfirmedRegistryEntry.__post_init__` (validate PASS)
rồi `to_record()` — không viết tay JSON, không sửa entry `BH62063` hiện có.
Khoá tra cứu `(order_id, raw_identity_key, sale_date)` (`INV-52`) đảm bảo
entry mới không ảnh hưởng bất kỳ đơn nào khác, kể cả 3 dòng còn lại của
CHÍNH đơn `BH62439` (Tủ lạnh Panasonic, Máy Giặt Sấy LG, Máy lạnh Daikin
Inverter 2HP) — cả ba vẫn `Pending`.

**4. Không đây là mapping toàn cục.** Giống `DEC-163` §4: identity
`TRACKING:FTHF25XVMV` là Owner-confirmed CHO ĐÚNG đơn `BH62439` ngày
2026-01-08, không thiết lập quy tắc chung cho mọi lần gặp mã này.

**5. Golden Baseline không đổi.** `tests/test_golden_baseline.py` gọi
`run_import()` KHÔNG truyền `identity_registry=`, nên không đọc
`data/historical_confirmed/registry.jsonl` — 58 passed/2 skipped giữ
nguyên, đo lại sau khi thêm entry.

**6. Golden #2 không bị chạm.** Không đọc/sửa nhánh
`implementation/golden-2-historical-vendor`, không reopen
`TASK-105C`/`TASK-105E`.

**7. Không đăng ký task mới, không mở Repair Cycle, không V4.2 migration.**

Impact:

- `data/historical_confirmed/registry.jsonl` — +1 dòng (entry `BH62439`).
- `tests/test_golden_bh62439_kpi.py` — file mới, 7 test tập trung.
- `docs/sessions/S057-golden-3-quantity-discount.md` — tài liệu session mới.
- `PROJECT/PROJECT_DECISIONS.md` — `DEC-164` (bản ghi này).
- **Không** sửa `app/**`, `config/**`, entry `BH62063`, hay bất kỳ test có
  sẵn nào.
- Full suite: 1035 passed, 11 skipped, 0 failed (trước: 1028 passed — delta
  đúng 7 test mới). Golden Baseline 58 passed/2 skipped không đổi.

Can Revisit After:

- Nếu cần Golden #4/#5, lặp lại đúng mẫu hình này: quét candidate thật, xin
  Owner-confirmed purchase price qua `AskUserQuestion` khi registry chưa có
  entry, KHÔNG bịa số.

---

## DEC-165

Title:
`PUBLIC PURCHASE AUTHORITY CORRECTION` — Public Purchase là giá Owner quản
trong Tracking (effective-dated), KHÔNG phải nguồn YAML độc lập của Reports;
supersede `DEC-156 D-01/OR-01`

Date:
2026-08-30

Task:
Tiếp tục lineage `CAP-PRICE-RESOLUTION` (`TASK-105D`/`105E`/`110`). **Không**
đăng ký task mới (`DEC-160` §HORIZONTAL SIBLING PROLIFERATION): đây là một
architecture correction bên trong capability đã có, không phải một capability
mới.

**Đây LÀ một Owner Decision.** Owner đã chốt nghiệp vụ trong chỉ thị phiên và
cấm hỏi lại; phiên này thực thi, không tự quyết định business semantics.

### Nghiệp vụ Owner đã chốt

```text
inv.gia   = giá vốn tồn THỰC TẾ (Y) — máy tính bình quân gia quyền
inv.cong  = Public Purchase — Owner tự đặt, có quyền đặt CAO HƠN Y
KpiPurchasePrice = Public Purchase tại thời điểm bán, KHÔNG PHẢI Y
```

Ví dụ Owner đưa: `Y = 4.500.000`, Public Purchase `= 5.000.000` →
`KpiPurchasePrice = 5.000.000`. Lý do nghiệp vụ: nhân viên nhìn thấy giá vốn
thật thấp sẽ tự hạ giá bán và bỏ mất lợi nhuận.

### Kết quả trace (bằng chứng, không phải suy đoán)

Chỉ thị cấm mặc định `inv.cong`/`tp.ton` là Public Purchase chỉ vì tên nghe
hợp. Đã trace đủ chuỗi Owner UI → handler → state → Firebase → board →
employee-visible value:

```text
invSetGia(el) kind="cong"   -> s.congTay[k]=true; s.cong[k]=n   (Owner sửa tay)
invRecalcAvg(s,x)           -> s.gia[k]=bình quân; CHỈ khi !congTay mới kéo cong theo
invSyncPart(upd)            -> u[k+"/tp/ton"] = cong[...]        (CHỈ giá công khai)
applySync()  -> savePpHist(stats.pph) -> purchase_price_history/<mã>/<pushId>
                { prev, next, t=ServerValue.TIMESTAMP, ta:"SERVER", by, src:"sync" }
```

Chú thích nguyên văn trong `public/index.html`:
`"Chỉ GIÁ CÔNG KHAI đi sang cột Tồn/Min. Giá thực nhập trung bình ở lại tab
Tồn kho và tab Giá trị tồn kho."`

**Phân loại gap = CASE A.** `purchase_price_history` đang ghi lịch sử của
`board/<mã>/tp/ton`, tức lịch sử của Public Purchase — KHÔNG phải của `Y`.
Reuse; không dựng nhánh history thứ hai, không dựng baseline thứ hai, không
backfill.

### Quyết định

**1. Tracking là production source of truth DUY NHẤT cho Public Purchase.**
Đường production: `inv.cong` → `board/<mã>/tp/ton` →
`purchase_price_baseline`/`purchase_price_history` → Data Contract →
`TrackingPriceHistoryReader` → `KpiPurchasePrice`.

**2. `data/public_purchase/source_version.yaml` KHÔNG còn là production source
authority.** Nó chuyển sang tư cách `LEGACY SUPPORTED FORMAT`. Loader, schema
`E-A`/`E-B`/`E-C`, các invariant `INV-02`/`INV-04`…`INV-09` và namespace
identity `PUBLIC_PURCHASE` giữ nguyên, không xoá.

**3. Catalog `PUBLIC_PURCHASE` không còn là điều kiện cần để resolve mã
Tracking.** `ProductIdentityResolver(pp_version=...)` thành `Optional`; cổng
`AND` của `PostCutoverPriceComposition._resolve_eligible` chỉ còn
`TrackingCatalogSnapshot` + `ProductIdentityStore view`. `pp_version=None` ghi
vào provenance là `pp_version_id=None` — "chưa nối", không phải "rỗng".

**4. `Y` không bao giờ thay Public Purchase.** Không có fallback. Public
Purchase không xác định được tại ngày bán → `Pending` → Review Queue canonical
(`TASK-110`). `Y` cũng không có đường tới Reports: hợp đồng chiếu `board`
xuống đúng `{name, alt}`, allowlist không có nhánh `inv`.

**5. Supersede `DEC-156 D-01/OR-01`** đúng ở phần "Public Purchase là nguồn
độc lập do chủ dự án cấp". Phần còn lại của `DEC-156` không đổi. **Không**
viết lại bản ghi `DEC-156`: nó là quyết định đúng với thông tin có lúc đó.
Provenance đầy đủ ở `docs/adr/ADR-107-public-purchase-authority-in-tracking.md`.

**6. Không sửa Firebase Rules, không mở rộng allowlist hợp đồng.** Bốn nhánh
`board`/`alias`/`purchase_price_baseline`/`purchase_price_history` đã đủ.

### Nợ kỹ thuật ghi nhận (không sửa trong quyết định này)

Hai đường phụ ghi `board/<mã>/tp/ton` mà KHÔNG sinh mốc lịch sử:
`mergePaths()` (gộp mã — chỉ lấp ô đang trống) và nhập bảng giá từ Excel.
Khoá chuỗi `prev` của `TrackingPriceHistoryReader` bắt đúng loại lỗ hổng này
và trả `Pending`, nên nó **không** sinh số sai — chỉ giảm độ phủ.

Impact:

- `app/modules/product/identity/resolver.py` — `pp_version` thành `Optional`
  + ba accessor chịu được vắng mặt.
- `app/modules/pricing/resolution/composition.py` — bỏ `pp_version` khỏi cổng
  `AND`.
- `docs/adr/ADR-107-public-purchase-authority-in-tracking.md` — file MỚI.
- `tests/test_public_purchase_authority.py` — file MỚI, 11 test.
- Repo `Tracking`: `kiem/gia-cong-khai-tham-quyen.js` — file MỚI, 27 bài kiểm.
  **0 dòng production Tracking.**
- **Không** sửa `config/**`, `data/**`, `governance/**`, Golden fixture/expected,
  Firebase Rules, allowlist hợp đồng.
- Reports full suite: 1286 passed, 11 skipped, 0 failed (trước: 1275 passed —
  delta đúng 11 test mới).
- Tracking: 57 bộ · 2461 đạt · 0 hỏng · 2 bỏ qua (trước: 56 bộ · 2434 đạt).
  `npm run build` PASS.

Can Revisit After:

- Nếu Owner sau này muốn hai đường phụ (`mergePaths`, nhập Excel) cũng sinh
  mốc lịch sử, đó là một thay đổi Tracking riêng — mở quyết định mới, không
  sửa quyết định này.

## DEC-166

Title:
`PRA FINALIZATION` — Owner chốt 5 quyết định nền cho Persistent Reporting &
Analytics (A web architecture, B snapshot coverage, C SOURCE_CHANGED,
D REMOVED, E legacy); persistence CHƯA approve, chờ ADR-108

Date:
2026-09-02

Task:
`TASK-PRA-000` (planning, S072) → finalization S073; mở `TASK-PRA-001`
(PLANNED, gate frozen). Không mở task cho PRA-002+.

**Đây LÀ một Owner Decision** cho A–E (Owner chốt trong chỉ thị phiên S073
sau khi review kế hoạch S072: `PLANNING_REVIEW = PASS`, `SCOPE_DRIFT = NO`).
Persistence (mục "Còn phải giải quyết") KHÔNG nằm trong quyết định này —
chỉ có decision audit tại `docs/adr/ADR-108-persistent-history-store.md`
(Status Proposed).

### Quyết định

**A. Web architecture.** KEEP Flask + Jinja làm production web layer canonical.
Không refactor sang FastAPI/React để khớp `ADR-101`. Không mở architecture
migration task. Amendment tài liệu tối thiểu:
`docs/adr/ADR-109-web-layer-flask-jinja.md` (Accepted) + dòng "Superseded
By" trong `docs/adr/ADR-101-architecture-and-stack.md`. Phần DB của ADR-101
không đổi.

**B. Snapshot coverage.** Coverage được AUTO-DETECT từ dữ liệu
(`DETECTED_DATE_RANGE` = min/max ngày bán). Người dùng không nhập tay ở
normal path. Hệ thống phân biệt `DETECTED_DATE_RANGE` với
`CONFIRMED_COMPLETE_COVERAGE`; min/max không mặc nhiên chứng minh file
complete. Khi coverage không chắc, có gap đáng ngờ, hoặc file không đại
diện đủ khoảng thời gian → cảnh báo / yêu cầu xác nhận khi thực sự cần,
không tự suy diễn completeness.

**C. SOURCE_CHANGED.** Cùng ORDER/ORDER_LINE xuất hiện với source values khác:
không silent overwrite, không mất version cũ, lưu `SOURCE_CHANGED` +
`changed_fields` + provenance; bản mới có thể là current candidate theo
reconciliation policy; lịch sử phải truy được và UI phải hiển thị được.

**D. REMOVED.** Record có ở snapshot trước, vắng ở snapshot mới →
`REMOVED_CANDIDATE`. Không silent delete, không tự coi là đơn huỷ, không tự
loại khỏi analytics chỉ vì biến mất. Vào Cần kiểm tra cho tới khi semantics
đủ chắc. `DETECTED_DATE_RANGE` không đủ authority để kết luận REMOVED; chỉ
coverage/completeness đủ mạnh mới tạo removed candidate đáng tin. Không tự
tạo business rule để resolve REMOVED.

**E. Legacy.** `LEGACY_REFERENCE` giữ nguyên dữ liệu cũ; không chạy lại bằng
pipeline; không sửa lỗi công thức cũ; known defects ghi metadata; luôn phân
biệt với `PIPELINE_GENERATED`.

**Order identity.** Giữ candidate `ORDER_KEY = normalize(Số BH)`,
`ORDER_LINE_KEY = ORDER_KEY + product_key + occurrence_index`. BH reset theo
năm vẫn UNKNOWN, không chặn PRA-001; schema phải hỗ trợ namespace năm bằng
một migration mà không áp business rule.
`OWNER_CONFIRMATION_REQUIRED_BEFORE = historical pipeline reconciliation
xuyên nhiều năm`.

**Analytics priority** giữ nguyên NOW/LATER/DEFER của TASK-PRA-000 mục L;
không mở task cho LATER/DEFER.

### Hệ quả

- Policy reconciliation được viết thành bảng tại `TASK-PRA-000` phụ lục F3;
  PRA-002 implement đúng bảng đó ở mức capability cần, không generic
  event-sourcing.
- `TASK-PRA-001` scope hẹp: legacy reference vertical + nền persistence tối
  thiểu + extension point; không "build toàn bộ analytics database".
- Quyết định còn blocking duy nhất: Owner approve `ADR-108`. Khi approve,
  ghi DEC mới (không sửa DEC này) và chuyển ADR-108 sang Accepted.

## DEC-168

Title:
`PRA-001_CHANGE_BUDGET_EXCEPTION = APPROVED` (~1.050 LOC) + hợp đồng nghiệp
vụ cho dòng Summary không phân loại được: FAIL TO, KHÔNG đoán semantics

Date:
2026-09-02

Task:
`TASK-PRA-001` — Independent Review trên
`7d84072765288b7a9dc28679a09325fce7860b48` = `CHANGES_REQUIRED`; repair
cycle 1/1 (S076). Không mở lại architecture, không mở PRA-002.

**Đây LÀ một Owner Decision.** Owner quyết hai việc:

```text
1. PRA-001_CHANGE_BUDGET_EXCEPTION = APPROVED
   NEW PRODUCTION LOGIC BUDGET = ~1.050 LOC
   (thay ngưỡng cứng 600 đã freeze ở S073, CHỈ cho TASK-PRA-001)

2. SOURCE ROW WITH BUSINESS VALUES
        → contract phân loại nhận ra?
             ├─ CÓ    → IMPORT
             └─ KHÔNG → FAIL TO (LegacyImportError / acceptance failure)
   Không auto-guess row_kind.
   Không suy SELLER / MONTH_TOTAL / YEAR_TOTAL / PROGRESS từ numeric values.
```

### Cơ sở của quyết định 1

Independent review phân loại 1.024 dòng logic của bản
`7d84072`: `ESSENTIAL ≈ 950`, `REASONABLE_HARDENING ≈ 60`,
`OUT_OF_SCOPE = 0 material`, `SPECULATIVE ≈ 15`. Không có capability nào
thừa để cắt, và nén code chỉ để quay về con số 600 sẽ đánh đổi tính đọc
được lấy một chỉ tiêu — nên ngân sách được chỉnh theo thực tế đã kiểm
chứng, KHÔNG phải capability bị cắt theo ngân sách.

Ngưỡng 600 ở S073 là ước lượng đặt trước khi viết dòng nào, cho một vertical
đi hết từ Excel tới UI với `DATA_MODEL_MINIMUM` 4 bảng / ~30 cột đã freeze.

**Ngân sách mới KHÔNG được dùng để mở thêm scope.** Nó chỉ hợp thức hoá
implementation đã được review xác minh là essential. Mọi capability mới vẫn
là `SCOPE EXPANSION REQUIRED`.

### Cơ sở của quyết định 2

Review chứng minh một lỗ hổng thật (`FIND-PRA001-R01`): một sheet Summary có
thể mất TOÀN BỘ dòng khi import mà verifier vẫn in `matched>0 mismatched=0`,
vì verifier duyệt từ DB → Excel nên không bao giờ thấy thứ chưa từng được
nhập. Một bản nhập thiếu hẳn kỳ 2025 mà báo "khớp 100%" là bằng chứng còn
tệ hơn không có bằng chứng.

Hai hướng sai đều bị loại tường minh:
- Bỏ qua im lặng dòng không phân loại được → mất số của Owner, không ai biết.
- Đoán `row_kind` vì "dòng có số" → công cụ tự gán ý nghĩa nghiệp vụ mà nó
  không có thẩm quyền gán, đúng chiều đảo ngược mà governance cấm
  (`CODE → AI INFERENCE → BUSINESS RULE`).

Nên: **fail to**. Nếu workbook thật về sau chứng minh có legitimate
value-only row, REAL DATA ACCEPTANCE phải DỪNG, ghi
`UNKNOWN / OWNER_DECISION_REQUIRED`, và contract được bổ sung bằng một
quyết định riêng dựa trên evidence thật — không tự mở rộng parser semantics.

### Hệ quả

- `CHANGE_BUDGET` của `TASK-PRA-001` cập nhật lên ~1.050 dòng logic; đo
  được sau repair: **1.045**.
- `app/legacy/parser.py` raise `LegacyImportError` khi một sheet Summary bắt
  buộc có dòng mang giá trị nghiệp vụ nhưng không khớp contract phân loại,
  nêu đích danh sheet và số dòng.
- `tools/analysis/verify_legacy_import.py` kiểm tra **SOURCE COVERAGE** từ
  phía Excel và in `SUMMARY_SOURCE_ROWS_WITH_VALUES` /
  `SUMMARY_IMPORTED_ROWS` / `SUMMARY_UNACCOUNTED_ROWS`; thiếu dòng nguồn =
  FAIL (exit khác 0) ngang hàng với lệch giá trị.
- Evidence `CHECK-PRA001-01` không còn được dùng riêng `628/0`: fidelity kể
  từ đây gồm **VALUE MATCH + SOURCE COVERAGE**.
- `Expected Touch Area` của task bổ sung hai file mà frozen gate thực sự
  cần: `tools/analysis/verify_legacy_import.py` (CHECK-01) và
  `app/web/legacy_presentation.py` (CHECK-04).

## DEC-167

Title:
`ADR-108 APPROVED` — Persistence cho Persistent Reporting & Analytics:
Managed PostgreSQL (structured history) + R2 (artifact) + SQLite (local/test)

Date:
2026-09-02

Task:
Close-out S074 cho `TASK-PRA-000` → mở `TASK-PRA-001` (READY). Không mở
task khác; roadmap đã freeze không đổi.

**Đây LÀ một Owner Decision.** Owner approve nguyên văn:

```text
ADR-108 = APPROVED
- Production structured history = Managed PostgreSQL
- Artifacts / existing run JSON / XLSX = R2
- Local/test = SQLite
- PRA-001 database scope = minimum legacy schema only
- Không prebuild schema PRA-002
- Tracking = READ-ONLY REFERENCE
- Tracking change required = NO
```

### Hệ quả

- `docs/adr/ADR-108-persistent-history-store.md` → Accepted.
- `TASK-PRA-001` → READY; Ready Gate còn hai điều kiện vận hành (file Excel
  legacy có trên máy chạy acceptance; đồng bộ nhánh đầu session), không còn
  quyết định nào chặn.
- Schema PRA-001 giới hạn đúng bốn bảng `legacy_import`,
  `legacy_summary_row`, `legacy_daily_sales`, `legacy_monthly_reference`
  (+ bảng version của Alembic). Mọi bảng snapshot/version/current của
  PRA-002 là out of scope — đề xuất tạo trước = `SCOPE EXPANSION REQUIRED`.
- `TASK-PRA-000` = DONE / architecture finalized.

## DEC-169

Title:
`Summary 2025` = REFERENCE_ONLY — làm rõ business scope import production
của PRA-001 (Owner scope clarification, KHÔNG phải repair)

Date:
2026-09-02

Task:
`TASK-PRA-001` — Legacy Reference Vertical. Phát sinh trong Real Data
Acceptance trên workbook thật, tại `5bea87a`.

**Đây LÀ một Owner Decision.** Owner xác nhận nguyên văn:

```text
Summary 2025 chỉ là REFERENCE_ONLY.
Mục đích của sheet này trong workbook cũ là làm dữ liệu tham chiếu
cho báo cáo 2026.

Owner KHÔNG yêu cầu:
- import Summary 2025;
- persist Summary 2025;
- query Summary 2025;
- display Summary 2025;
- xây parser cho value-only rows của Summary 2025.

Production business scope của PRA-001 là:
REQUIRED:      Summary 2026, DataChart 2026
REFERENCE_ONLY: Summary 2025
```

### Vì sao có quyết định này

Real Data Acceptance (S075, workbook thật `Báo cáo Kinh doanh 2026.xlsx`,
SHA256 `4ffe5198…d11f72`) đo được hình dạng thật:

| Sheet | Formula rows | Value-only business rows |
|---|---|---|
| `Summary 2026` | 71 | 0 |
| `Summary 2025` | **0** | **99** |

`Summary 2025` không có MỘT ô công thức nào trên toàn sheet (quét đủ 755
dòng × 27 cột). Contract phân loại dòng của parser bám hoàn toàn vào cấu
trúc công thức, nên không dòng nào của sheet đó phân loại được.

Importer đã hành xử ĐÚNG: nó raise `LegacyImportError` và trả
`OWNER_DECISION_REQUIRED` theo DEC-168 thay vì đoán `row_kind` từ việc
"dòng có số". Đây chính là guard mà FIND-PRA001-R01 dựng lên.

Cái sai không nằm ở code, mà ở một **giả định chưa từng được Owner xác
nhận**: "Summary 2025 phải được production-import". Owner nay bác bỏ giả
định đó. Vì vậy sửa **contract/scope** cho khớp thẩm quyền Owner, KHÔNG sửa
parser để hiểu 99 dòng kia.

### Phân loại thay đổi

- `OWNER_SCOPE_CLARIFICATION` = YES
- `REPAIR_CYCLE_2` = NO — không phải repair của implementation defect.
  Repair budget PRA-001 giữ nguyên `0 remaining`, không bị tiêu.
- Không xây "Static Legacy Summary Contract". Không thêm parser semantics
  cho value-only rows.

### Hệ quả

- `app/legacy/parser.py`: tách tường minh `SUMMARY_IMPORT_SHEETS`
  (`Summary 2026`) khỏi `SUMMARY_REFERENCE_ONLY_SHEETS` (`Summary 2025`).
  `REQUIRED_SHEETS` = `Summary 2026` + `DataChart 2026`. Sheet
  REFERENCE_ONLY không được parse, không vào `summary_rows`, không xuất
  hiện trong `sheets_imported`. Loại trừ là **explicit**, không phải nuốt
  lỗi: không có nhánh nào bắt rồi bỏ qua `LegacyImportError`.
- `tools/analysis/verify_legacy_import.py`: chỉ đối chiếu fidelity trên
  sheet REQUIRED_IMPORT, và kiểm CHỦ ĐỘNG rằng sheet REFERENCE_ONLY không
  để lại bản ghi nào trong bảng production — in
  `SUMMARY_REFERENCE_ONLY_PERSISTED`, khác 0 thì exit 1.
- Kỳ 2025 không còn trong `available_periods()` — đúng với "không query,
  không display".
- Guard DEC-168 / FIND-PRA001-R01 **không bị nới lỏng**, chỉ đổi phạm vi áp
  dụng: toàn bộ test guard đã được chĩa sang `Summary 2026`, nơi một dòng
  value-only không phân loại được vẫn FAIL TO.
- `CHECK-PRA001-01` chỉ yêu cầu fidelity + source coverage cho
  `Summary 2026` và `DataChart 2026`. `Summary 2025` không còn là REQUIRED
  acceptance gate.

### Ranh giới (không được suy rộng)

Quyết định này KHÔNG cho phép: bỏ qua sheet REQUIRED_IMPORT, hạ ngưỡng
source coverage, đoán semantics dòng, hay mở PRA-002 / đổi Tracking /
đổi kiến trúc. `PROTECTED_CORE_IMPACT` = NONE.

---

## DEC-170

Title:
Giữ `HISTORY_DATABASE_URL` làm tên biến duy nhất — KHÔNG thêm fallback đọc
`DATABASE_URL`

Date:
2026-09-02

Task:
`PRE-PRA-002` / Production PostgreSQL Activation (S078).

Authority:
OWNER_ACCEPTED

**Đây LÀ một Owner Decision.** Owner đã chính thức ACCEPT quyết định này
(2026-09-02, cùng lúc với Independent Review ACCEPT của S078) và đã cấu
hình Render production theo đúng contract: biến `HISTORY_DATABASE_URL`,
scheme `postgresql+psycopg://`. Contract canonical là
`HISTORY_DATABASE_URL`, **không có fallback sang `DATABASE_URL`**.

Phần dưới đây giữ nguyên lập luận kỹ thuật đã trình bày khi đề xuất — nó
là căn cứ của quyết định, không phải trạng thái thẩm quyền. Bối cảnh:
Owner đã provision `tinphat-reports-db` (PostgreSQL 18, Virginia) và dán
Internal Database URL vào Render Environment dưới **tên biến `DATABASE_URL`**
— tên Render gợi ý sẵn. Code canonical đọc `HISTORY_DATABASE_URL`
(`tools/db/__init__.py::resolve_url()`), nên hai bên không gặp nhau.

Có đúng hai cách đóng khoảng cách này:

1. **Owner đổi tên biến trong Render** thành `HISTORY_DATABASE_URL`.
2. **Sửa code** cho `resolve_url()` đọc `DATABASE_URL` khi thiếu
   `HISTORY_DATABASE_URL`.

Chọn (1). Lý do:

- `DATABASE_URL` là tên chung của cả nền tảng: Render tự đặt nó cho **mọi**
  database liên kết vào service. Nếu sau này Reports liên kết thêm một
  database khác (hoặc Render tự inject), fallback sẽ âm thầm trỏ history
  store vào SAI database — đúng loại lỗi im lặng mà `REPORTS_REQUIRE_HISTORY_DB`
  được dựng lên để chặn. Tên riêng `HISTORY_DATABASE_URL` nói rõ *kho nào*.
- Đổi tên một biến trong Render dashboard là thao tác một phút, không cần
  tạo lại database, không cần lấy lại credential, không đụng Git.
- Sửa code để nhận một tên biến rộng hơn là nới lỏng một ràng buộc
  fail-closed đã freeze ở `ADR-108`/`TASK-PRA-001`, để đổi lấy đúng một lần
  tiện tay. Rule không được tự biến thành Owner requirement, và ngược lại,
  sự tiện tay của một lần cấu hình không được biến thành nới lỏng luật.

Chi phí của lựa chọn này rơi hoàn toàn vào Owner (một thao tác đổi tên) và
đã được viết thành bước cụ thể ở `docs/deployment/S071_DEPLOYMENT.md` bước
10, kèm bảng bốn biến thể cấu hình đã đo thật. **Owner đã thực hiện thao
tác đó** — biến `HISTORY_DATABASE_URL` với scheme `postgresql+psycopg://`
đã có mặt trong Render Environment (Owner xác nhận; session KHÔNG yêu cầu
và KHÔNG nhận giá trị của biến này).

### Ranh giới (không được suy rộng)

Quyết định này KHÔNG cho phép: đổi tên biến trong code, thêm biến môi trường
mới, sửa `REPORTS_REQUIRE_HISTORY_DB`, hay đụng bất kỳ đường nào của R2 /
Tracking. `PROTECTED_CORE_IMPACT` = NONE. Phương án (2) đã bị loại bỏ bởi
chính Owner Decision này; nếu về sau Owner đổi ý, đó là một task riêng có
Ready Gate riêng, không phải một sửa đổi âm thầm ở đây.

---

## DEC-171

Title:
`TASK-PRA-002` contract freeze — các quyết định chiến thuật của phiên
Roadmap Finalization S079 (KHÔNG phải Owner Decision; nằm trong thẩm quyền
session theo authority/risk/budget đã cấp)

Date:
2026-09-02

Task:
`TASK-PRA-002` — Pipeline Persistence + Overlapping Snapshot Reconciliation.
Phiên S079 chỉ lập kế hoạch / freeze contract; không implementation.
Task file: `docs/tasks/TASK-PRA-002-pipeline-persistence-reconciliation.md`.
`BASE_SHA = 553d8a36f578b082128a6e45d2748da2bc371e70`.

Authority:
SESSION_TACTICAL — Owner có thể bác bỏ từng mục bằng một DEC mới; không mục
nào ở đây đổi business rule của pipeline, đổi kiến trúc ADR-108, hay đụng
Tracking.

### Những gì ĐÃ là Owner Decision (chỉ tham chiếu, không quyết lại)

- Contract reconcile INSERT / SAME / SOURCE_CHANGED / REMOVED_CANDIDATE /
  NOT_SEEN_IN_LATEST_SNAPSHOT / RESULT_REVISED; hai trục version tách
  riêng — DEC-166 C/D + chỉ thị S079 (Owner chấp nhận nguyên văn).
- Coverage ba mức, chỉ explicit user confirmation nâng
  `CONFIRMED_COMPLETE` — DEC-166 B + chỉ thị S079.
- Hai origin `LEGACY_REFERENCE` / `PIPELINE_GENERATED` tách biệt — DEC-166 E.
- PostgreSQL + R2 + SQLite test — DEC-167/ADR-108; `HISTORY_DATABASE_URL` — DEC-170.
- Render 512 MB đủ, không mở task nâng compute — chỉ thị S079 (sau S078R).
- Candidate khoá `ORDER_KEY = normalize(BH)`,
  `ORDER_LINE_KEY = ORDER_KEY + product_key + occurrence_index` — DEC-166.

### Quyết định chiến thuật của S079 (INFERENCE / implementation-local)

1. **`normalize(BH)` = đúng chuẩn hoá engine đang dùng** (`NFC + strip`,
   `app/modules/importing/raw_reader.py::_normalize_text`), KHÔNG thêm
   upper/bỏ khoảng trắng như PRA-000 I.2 gợi ý. Lý do: tầng lưu trữ mà
   chuẩn hoá khác engine sẽ tạo hai "sự thật" về cùng một đơn (engine coi
   là hai đơn, DB coi là một). `product_key` cũng theo đúng `product_raw`
   engine (không casefold — DEFER D9).
2. **`line_fingerprint`** = bộ trường nguồn nghiệp vụ của PRA-000 I.2 +
   `source_profit`; KHÔNG gồm PII, `source_row`, `row_hash`; Decimal
   canonical hoá bằng `normalize()` để `1000` ≡ `1000.0`.
3. **Không persist PII** trong PRA-002 (`customer`, `customer_code`,
   `phone`, `address`, `shipper_raw`) — vertical không cần, và
   `RULE_PRECEDENCE` đặt Privacy (3) trên Architecture/UX. N.5 của
   PRA-000 DEFER sang PRA-004.
4. **Xác nhận coverage là hành động riêng sau upload** (`POST
   /du-lieu/snapshot/<id>/xac-nhan-du`, khai báo khoảng ngày + checkbox,
   validate `DETECTED ⊆ khoảng`, 409 khi xác nhận lại) — không phải ô nhập
   tay ở normal path upload (đúng DEC-166 B), không phải UI PRA-004.
   Bước REMOVED chạy trong cùng transaction với xác nhận.
5. **Guard `ORDER_KEY_COLLISION` 90 ngày giữ** làm fail-safe cho UNKNOWN
   BH reset: version mới KHÔNG current, current cũ giữ, cờ; lần đầu xuất
   hiện trên production → `OWNER_DECISION_REQUIRED` N.13.
6. **Bảng membership `snapshot_line`** (dòng nào có trong snapshot nào)
   được thêm vào data model để bước REMOVED đúng với mọi thứ tự upload và
   không phụ thuộc `last_seen` (một snapshot chồng kỳ sau đó có thể đổi
   `last_seen` và gây REMOVED giả). Bỏ `order_source_version` và
   `review_item` khỏi PRA-002 (DEFER D6) — cấp đơn là `GROUP BY`.
7. **`result_fingerprint` chỉ gồm 3 trường F3** (`status`,
   `accounting_purchase_price`, `eligible_kpi_profit`); result version vẫn
   lưu đủ mọi trường.
8. **Đơn vị công việc**: history transaction bao cả `save_artifact` +
   `create_run` (R2) và commit sau cùng; R2 lỗi → rollback → 500 (đúng
   thông điệp hiện có). Residual: commit lỗi sau R2 → run không có snapshot
   → hiển thị "KHÔNG CÓ LỊCH SỬ (ghi lỗi)" (fail-visible).
9. **Ba slice** A/B/C thay cho năm slice A–E của chỉ thị (A+B+C của chỉ
   thị là một thuật toán, tách ra chỉ tạo thêm task); mỗi slice có check
   riêng trong cùng một Completion Gate frozen.
10. **Change budget** mục tiêu ≤ 1.200 dòng logic, dừng cứng 1.500 (đặt
    theo thực tế PRA-001 = 1.045 cho một vertical nhỏ hơn). **Review budget
    HIGH = 2 blocking repair cycles** (Effective Risk = Blast Radius theo
    failure path: double-count → sai KPI/lương).
11. **Chạm `app/modules/exporting/excel_exporter.py` chỉ bằng alias public**
    (`present_lines`, `PresentedLine`) và `app/demo.py` chỉ thêm 2 trường
    `DemoRun` — không đổi hành vi, không đổi XLSX; đây là khoảng cách nhỏ
    nhất để tầng lưu dùng đúng MỘT nguồn sự thật AUTO/PENDING.

### Hệ quả

- `TASK-PRA-002` = `READY`, Completion Gate FROZEN (17 check, 16 REQUIRED).
- `PRA002_READY_FOR_IMPLEMENTATION = YES`; không `OWNER_DECISION_REQUIRED`
  chặn vertical tháng 09/2026. UNKNOWN/ASSUMPTION có fail-safe và
  re-trigger ghi ở mục 18 của task file.
- Ledger mở lineage `TASK-PRA-002` (HIGH, 2 cycle, 0 dùng).

## DEC-172

Title:
`PRICE_AUTHORITY_NORMALIZATION` + `ACCOUNTING_REASON_NORMALIZATION` — Tracking
PP tại ngày bán là authority DUY NHẤT của giá mua trong Reports; tên trường
legacy `accounting_*` KHÔNG tạo ra business authority

Date:
2026-09-03

Task:
Sửa ngữ nghĩa nghiệp vụ theo chỉ thị Owner (OWNER-DIRECTED BUSINESS SEMANTIC
CORRECTION / MINIMAL VERTICAL REPAIR). Reports = phạm vi ghi DUY NHẤT;
Tracking = READ-ONLY REFERENCE. `BASE_SHA =
522a093ff952702b479d975aab42d0e10deb461a`.
`TASK-PRA-004` giữ nguyên `DONE`; `PRA-005` NOT STARTED.

Authority:
**OWNER_DECISION** — thẩm quyền cao nhất. Quyết định này SUPERSEDES ngữ nghĩa
hiện hành khi có xung đột về price authority, KỂ TỪ THỜI ĐIỂM NÀY TRỞ ĐI.

Classify:
`OWNER_DECISION` / `PRICE_AUTHORITY_NORMALIZATION`

### 1. Nội dung quyết định

1. Trong Reports chỉ có **MỘT** authority cho giá mua phục vụ phân tích bán
   hàng: **Tracking PP có hiệu lực tại ngày bán**.
2. Sổ bán hàng / accounting workbook **KHÔNG** phải nguồn giá nhập. Owner chưa
   từng yêu cầu Reports truy xuất một nguồn giá nhập kế toán độc lập.
3. Reports dùng thông tin bán hàng để xác định `sản phẩm + ngày bán`, sau đó
   đối chiếu Tracking để resolve PP.
4. PP này được gọi ở business/UI là **"Giá mua tham chiếu"**.
5. Lợi nhuận quản trị chính là **LN KPI**.
6. Owner **KHÔNG** yêu cầu một hệ `Accounting Purchase Price Authority` hoặc
   `Accounting Profit` management metric chạy song song với Tracking PP/KPI.
7. Các field legacy `accounting_purchase_price` / `accounting_profit` **được
   tiếp tục tồn tại nội bộ** để tránh refactor/migration không cần thiết.
8. Nhưng tên `accounting_*` **KHÔNG được phép tự tạo thêm** business
   requirement, business authority hay management-facing semantic.
9. Sự thật implementation hiện tại: `accounting_purchase_price` đang làm
   **carrier** của Tracking PP đã resolve theo `sale_date`.
10. **Không tồn tại hai nguồn giá.** `Tracking PP` và "Accounting Purchase
    Price" KHÔNG phải hai authority độc lập trong implementation hiện tại.
11. Historical specs/DEC vẫn giữ nguyên như historical artifacts.

### 2. Business flow được FREEZE

    Sổ bán hàng → Product + sale_date → Product Identity → Tracking
    → PP effective at sale_date → Giá mua tham chiếu → KPI calculation → LN KPI

KHÔNG tạo thêm nhánh `Sổ bán hàng → Giá nhập kế toán → LN kế toán`.

### 3. Phân loại lại field legacy (KHÔNG rename, KHÔNG xoá)

| Field | Phân loại mới |
|---|---|
| `accounting_purchase_price` | `LEGACY_INTERNAL_PP_CARRIER` |
| `accounting_profit` | `LEGACY_DERIVED_FIELD` |

Lý do không rename: đổi tên carrier nội bộ lúc này tạo blast radius ngang
(schema, persistence, history, query, presentation, fixture) mà không đổi được
một con số nào cho người dùng.

### 4. Hệ quả hành vi DUY NHẤT — `ACCOUNTING_REASON_NORMALIZATION`

Hai mã Pending sau **không còn được SINH RA** cho kết quả MỚI:

- `Pending.accounting_purchase_price` ("Thiếu giá nhập kế toán")
- `Pending.accounting_profit` ("Thiếu lợi nhuận kế toán")

Điểm sinh DUY NHẤT đã được truy vết và sửa: vòng lặp `Pending.<field>` trong
`app/modules/exporting/excel_exporter.py::_present_lines`. Đây cũng là nguồn
sự thật duy nhất cho `status` AUTO/PENDING, `review_reason_counts`, và
`pending_reasons` được persist — nên chuẩn hoá tại đây là chuẩn hoá ở tầng
reason-generation/business, KHÔNG phải giấu trong template (yêu cầu §10).

Nguyên tắc trình bày mới: **MỘT NGUYÊN NHÂN GỐC → MỘT LÝ DO QUẢN TRỊ
ACTIONABLE.** Không trình bày nhiều hệ quả dẫn xuất như thể chúng là các vấn
đề độc lập.

KHÔNG đụng tới: công thức, storage, schema, PP resolution, temporal rule
(`PricingEffectiveDate = sale date`), KPI formula, identity algorithm.

### 5. `Pending.eligible_kpi_profit` — GIỮ LẠI, có bằng chứng

Câu hỏi §7 của chỉ thị: mã này là lý do ĐỘC LẬP hay luôn là hệ quả dẫn xuất?

**Bằng chứng (không phỏng đoán):** tồn tại case reachable trong đó identity đã
nhận diện, PP đã resolve, mọi input actionable phía trên đều hợp lệ, nhưng
`eligible_kpi_profit` vẫn `None`:

- `config/eligible_costs.yaml` thiếu/hỏng → `EligibleCostsAuthority.is_valid`
  = `False` → fail-closed (B02). `kpi_purchase_price` vẫn resolve bình thường,
  nên KHÔNG mã nào khác báo lỗi này.
- `confirmed_adjustment_source` UNAVAILABLE (DEC-144 §3) → `kpi_purchase_price`
  = `None` → KPI `None`, dù PP đã resolve.

Ở cả hai case, `Pending.eligible_kpi_profit` là mã **DUY NHẤT** nói cho người
vận hành biết có một authority cần được sửa. Nó thoả đúng tiêu chuẩn Owner:
"CẦN KIỂM TRA phải đại diện cho một vấn đề input/authority mà con người thật
sự phải xử lý". Gỡ nó đi sẽ **giấu một lỗi authority thật**.

Bằng chứng đã tồn tại TRƯỚC quyết định này:
`tests/test_demo.py::test_kpi_unavailable_is_queued_even_with_resolved_price`.
Bằng chứng bổ sung: hai test `test_kpi_reason_is_independent_when_*` trong
`tests/test_price_authority_normalization.py`.

→ `KPI_REASON_DECISION = KEEP`. Không cần `KPI_REASON_OWNER_DECISION_REQUIRED`.

### 6. Lịch sử đã persist — KHÔNG BACKFILL

`pending_reasons_json` của các result version đã lưu vẫn chứa hai mã kế toán.
Quyết định: **DO NOT BACKFILL** — không migration, không rewrite result version
cũ, không mutate historical evidence. Một lần chạy cũ là bằng chứng của luật
đang hiệu lực LÚC ĐÓ.

Hệ quả hiển thị được chấp nhận tường minh: **UI hiển thị một kết quả CŨ đã
persist sẽ vẫn hiện các mã reason lịch sử**, vì kiến trúc hiện hành render
trung thực lịch sử đã lưu. Đây không phải bug. Vì vậy hai nhãn tiếng Việt
được **GIỮ LẠI** trong `REASON_DISPLAY_LABELS`, và được đánh dấu tường minh
bằng `app/beta_presentation.py::RETIRED_PENDING_REASONS`.

Vũ trụ mã reason vì thế có HAI TẦNG, cả hai đều dẫn xuất từ mã nguồn:

- `reason_universe()` = 19 mã — tập pipeline CÓ THỂ sinh cho kết quả MỚI.
- `renderable_universe()` = 21 mã = 19 + `RETIRED_PENDING_REASONS` — tập UI
  CÓ THỂ phải hiển thị khi đọc lịch sử.

### 7. Đo tác động (fixture Golden, đường production thật)

| Chỉ số | Trước | Sau | Delta |
|---|---|---|---|
| `period_2026_01` total lines | 351 | 351 | 0 |
| `period_2026_01` AUTO / PENDING lines | 2 / 349 | 2 / 349 | 0 |
| `period_2026_01` AUTO / Review orders | 1 / 253 | 1 / 253 | 0 |
| `period_2026_01` `Pending.accounting_purchase_price` | 349 | 0 | −349 |
| `period_2026_01` `Pending.accounting_profit` | 349 | 0 | −349 |
| `period_2026_06` total lines | 180 | 180 | 0 |
| `period_2026_06` AUTO / PENDING lines | 0 / 180 | 0 / 180 | 0 |
| `period_2026_06` AUTO / Review orders | 0 / 146 | 0 / 146 | 0 |
| `period_2026_06` `Pending.accounting_purchase_price` | 180 | 0 | −180 |
| `period_2026_06` `Pending.accounting_profit` | 180 | 0 | −180 |

`accounting-only Pending lines` = **0** ở cả hai fixture, TRƯỚC lẫn SAU. Đây là
lý do cấu trúc khiến status không đổi: mọi dòng từng mang mã kế toán đều còn ít
nhất một mã actionable khác (`Missing.PurchasePrice`), nên không dòng nào có
thể lật `PENDING → AUTO`. Điều kiện này được canh bằng test
(`test_k_removing_the_two_codes_changes_no_line_status`), không phải bằng một
con số đếm cứng.

**Số Review KHÔNG giảm, và đó KHÔNG phải thất bại** — mục tiêu là
`SEMANTIC CORRECTNESS + REASON CLARITY`, đúng như audit đã cảnh báo (audit fact
F: accounting-only Pending không tìm thấy trong fixture đã audit).

### 8. Oracle số học — KHÔNG ĐỔI

Không giá trị số nào bị đụng. `BH73844` (9.550.000 / 9.450.000 / 100.000),
`BH73877` (32.800.000 / 456.667 / coverage 2/3), và toàn bộ oracle Golden giữ
nguyên. Golden baseline: `58 passed, 2 skipped` — đúng con số authority đang
ghi trong `CLAUDE.md`.

Với `BH73877`, kết quả MỚI (khi xử lý lại nguồn) sẽ mang:

    Chưa nhận diện sản phẩm
    Thiếu giá mua tham chiếu
    Thiếu lợi nhuận KPI

Bản đã persist của `BH73877` KHÔNG bị sửa (mục 6).

### 9. Bài học governance

**SOURCE FIELD / LEGACY FIELD NAME does not automatically create BUSINESS
AUTHORITY.**

Một cái tên trường có sẵn trong code (`accounting_*`) đã âm thầm sinh ra một
"authority kế toán" mà Owner chưa bao giờ yêu cầu, rồi từ đó sinh ra hai mã
reason quản trị, rồi hiện lên màn hình như hai việc phải làm. Không bước nào
trong chuỗi ấy đi qua một quyết định nghiệp vụ.

Luật rút ra: **một metric/status/reason mới có tác động tới business state đòi
hỏi authority classification tường minh** — không được suy ra từ tên field,
tên cột nguồn, hay tên module.

### 10. Phạm vi KHÔNG làm

Không `PRA-005`; không Tracking write; không schema/database migration; không
rename campaign; không xoá field `accounting_*`; không backfill/rewrite lịch
sử; không đổi PP algorithm / KPI formula / identity algorithm; không subsystem
mới; không Review workflow; không pagination; không export redesign; không sửa
`REM-T06`; không refactor tổng quát.

## DEC-173

Title:
`OD-PRA005-01` (khoá gộp mặt hàng = mô tả thô đã chuẩn hoá trên chứng từ) +
`OD-PRA005-02` (bao gồm toàn bộ dòng chứng từ, kể cả dịch vụ/phí) — hai
Owner Decision khoá Contract của `TASK-PRA-005` "SẢN PHẨM"

Date:
2026-09-03

Task:
`TASK-PRA-005` — Sản phẩm (Mặt hàng trên chứng từ) — Aggregation View
(CHỈ-ĐỌC). Phiên Contract Freeze S107 (nhánh
`claude/pra-005-contract-freeze-99nuai`), sau Discovery S105
(`docs/sessions/S105-pra-005-san-pham-discovery.md`) và tích hợp S106.
Task file: `docs/tasks/TASK-PRA-005-san-pham.md`.
`BASE_SHA = 1ebb0021e13f85fe7ac7825e1219583e4c682889`.

Authority:
`OWNER_DECISION`. Cả hai quyết định làm đổi Ý NGHĨA NGHIỆP VỤ của con số
Owner đọc trên trang Sản phẩm (khoá gộp và tập dòng tham gia), nên không
thuộc thẩm quyền tự quyết của session. Discovery S105 §28 đã đề xuất đúng
phương án A cho cả hai mục kèm phân tích trade-off; phiên Contract Freeze
này khoá A/A thành `OWNER_DECISION` chính thức theo brief Contract Freeze
đã nhận.

### OD-PRA005-01 — Khoá gộp mặt hàng

```
GROUPING_CONTRACT = NORMALIZED_RAW_DOCUMENT_DESCRIPTION
RAW_PRODUCT_GROUP = NFC(product_raw).strip()
```

Về kỹ thuật, đây CHÍNH LÀ `product_key` đã tồn tại và đã nghiệm thu ở
`TASK-PRA-002` (`app/history/keys.py:70`, DEC-166, DEC-171) — tái dụng
nguyên vẹn, KHÔNG dựng hàm chuẩn hoá thứ hai.

Đây **KHÔNG PHẢI** canonical Product Identity, SKU authority, hay Tracking
Product Identity. Tracking vẫn là Product Identity Authority duy nhất
(DEC-103/ADR-106) — không bị thay thế hay đụng chạm.

Lý do: Discovery đo được `canonical_product_code` = 0/349 trên fixture
golden (identity chỉ điền khi có Tracking capture, không nằm trong repo
theo đúng thiết kế); bằng chứng thật S068 cho thấy trên production nó cũng
không phủ hết (`identity unresolved 31/83`). Một khoá gộp có thể `NULL`
trên phần lớn dòng không thể là khoá phân hoạch của một bảng "toàn bộ mặt
hàng trong kỳ". Owner chấp nhận **SPLIT trung thực thay vì MERGE không an
toàn** — ví dụ đo được: `FTKB50ZVMV` tách thành hai dòng (`Điều hoà Daikin
FTKB50ZVMV` và `Máy lạnh Daikin Inverter 2 HP FTKB50ZVMV`, gộp lại sẽ là
mặt hàng doanh thu #1 của kỳ 01/2026).

Cấm tường minh: fuzzy merge, substring merge, model-code merge, hybrid
`COALESCE(product_raw_key, canonical_product_code)`. Bằng chứng bác bỏ
model-code merge: ca `TD-H80SEV(SK)` / `TD-H80SEV(WK)` là hai SKU màu khác
nhau — một quy tắc gộp theo mã model sẽ sửa đúng ca `FTKB50ZVMV` nhưng làm
HỎNG ca này.

Hệ quả chấp nhận: các tên gọi khác nhau trên chứng từ của CÙNG một sản phẩm
thực tế có thể tiếp tục hiển thị thành các dòng riêng biệt trong PRA-005 V1
— hành vi ĐÃ CHẤP NHẬN, ghi lại là `FIND-PRA005-01`, không mở task repair.

### OD-PRA005-02 — Bao gồm toàn bộ dòng chứng từ

```
SERVICE_FEE_TREATMENT = INCLUDE_ALL
```

PRA-005 V1 gồm TẤT CẢ dòng chứng từ, kể cả mô tả không giống hàng tồn kho
thật (`Chi phí vận chuyển`, `Chênh VAT`, `Phụ Phí`, `Giá treo Tivi`…), nếu
tồn tại trong dữ liệu nguồn đã accepted.

Lý do: Reports hiện KHÔNG có phân loại có thẩm quyền cho
`product`/`service`/`fee`/`adjustment` (đã đóng băng ở EAC-5/EAC-8 của
`TASK-PRA-003`/`TASK-PRA-004`). `is_non_product_line()`
(`app/modules/validation/rules.py`) là heuristic GIẢM NHIỄU validation,
docstring của chính nó nói rõ *"must never be tuned to reproduce a
historical count"* — dùng nó để lọc bảng sản phẩm sẽ biến một công cụ giảm
nhiễu thành một authority phân loại nó chưa từng được thiết kế để làm, và
sẽ vừa thiếu (bỏ sót phụ kiện thật như "Giá treo Tivi") vừa thừa.

Cấm tường minh: heuristic exclusion, `is_product`/`is_service`/`is_fee`
authority mới nào.

Mặc định trình bày: `DEFAULT_SORT = REVENUE DESC` — mặc định TRÌNH BÀY,
không phải phân loại nghiệp vụ. Đo được (Discovery S105 §13/§28): dòng
dịch vụ/phí chiếm 6,3%–7,8% SỐ DÒNG nhưng chỉ 0,14%–0,25% DOANH THU của kỳ
— sắp theo doanh thu khiến chúng tự chìm xuống mà không cần luật loại trừ
nào.

### Hệ quả

- `TASK-PRA-005` Contract = FROZEN tại phiên S107; task file
  `docs/tasks/TASK-PRA-005-san-pham.md`, Status = READY, Completion Gate
  FROZEN (15 check: 14 REQUIRED · 1 RECOMMENDED).
- Ledger mở lineage `TASK-PRA-005` (MEDIUM, 1 cycle, 0 dùng) tại
  `PROJECT/REVIEW_BUDGET_LEDGER.md`.
- `IMPLEMENTATION_READY = YES`. Không `OWNER_DECISION_REQUIRED` nào còn
  treo chặn PRA-005 V1. `TASK-PRA-002`/`003`/`004` không đổi: DONE.

## DEC-174 — PHB-02 Business Parity: bảy quyết định Owner (`DEC-PHB02-01…07`)

Date:
2026-09-04

Task:
PHB-02 (Business Parity Contract)

Decision:
Owner ban hành bảy quyết định nghiệp vụ đóng toàn bộ bảy câu hỏi mà audit
`S113` mở. Chúng **thay thế** suy diễn của agent và **thay thế** mọi suy diễn
ngược lại rút ra từ workbook tay cũ. Giữ nguyên mã định danh của Owner:

- **`DEC-PHB02-01` — Parity Oracle.** Reports được xây để THAY THẾ báo cáo thủ
  công; báo cáo production dẫn xuất từ sổ kế toán thô + nguồn có thẩm quyền đã
  chấp nhận + business rule đã duyệt. Báo cáo tay cũ = `BUSINESS REQUIREMENT /
  SEMANTIC REFERENCE`, **không** phải `FINAL NUMERIC AUTHORITY`. Cấm sửa
  Reports chỉ để tái tạo con số tay không tái tạo được từ nguồn đã chấp nhận.
- **`DEC-PHB02-02` — Giá nhập / coverage.** AUTO-fill bằng thuật toán khớp giá
  đã chấp nhận; thiếu dữ liệu ⟹ cảnh báo tường minh + nhập tay; ô AUTO vẫn
  **sửa được**; provenance tối thiểu `AUTO` vs `MANUAL / MANUAL_OVERRIDE`, cấm
  âm thầm coi override là AUTO. Lợi nhuận KPI **chính thức** chỉ khi
  `PROFIT_COVERAGE = 100 %` — **không** ngưỡng 90/95 % hay bất kỳ ngưỡng nào.
- **`DEC-PHB02-03` — Tổng số SP.** `SUM(quantity)` của sản phẩm có **giá bán >
  1.000.000 VND**. Ngưỡng giá, **không** phải taxonomy, **không** phải đếm SKU
  hay đếm dòng. Đóng `N.7` cho chỉ tiêu này.
- **`DEC-PHB02-04` — DS quy đổi.** Chỉ tiêu **cốt lõi** đánh giá hiệu suất
  nhân viên. `CONVERTED_SALES = PROFIT / CONVERSION_RATE` — **phép chia**;
  `profit * rate` bị cấm tuyệt đối. Phạm vi = **tất cả** đơn đủ điều kiện
  trong tháng, không phải tập con chọn tay. Không bịa từ giá nhập chưa phân
  giải. `PROFIT` ở đây là `EligibleKpiProfit` của `DEC-143` (dòng
  `sale_price − purchase_price` là minh hoạ theo một đơn vị sản phẩm).
- **`DEC-PHB02-05` — Định tuyến tỉ lệ.** Tín Phát `7,5 %`; Vinh/Quý/Hiệp
  (wholesale/nội-thành) `2 %`, hoặc `8 %` khi sản phẩm được **tick**
  `GIA_DUNG`; bán lẻ khác `5,5 %`. `GIA_DUNG` là **product-level override**
  bên trong đúng luồng wholesale/nội-thành, **không** phải một loại nhân
  viên; cấm suy ra tự động từ tên hàng; bán lẻ thường **không** cần luồng đó.
- **`DEC-PHB02-06` — Target.** Cấu hình được **theo từng nhân viên**, có chỗ
  nhập và sửa; cấm hard-code giá trị target vào logic tính. PHB-02 chỉ freeze
  yêu cầu nghiệp vụ; implementation ở PHB-05.
- **`DEC-PHB02-07` — So tháng trước.** `%` thay đổi của **doanh thu bán hàng**
  tháng này so tháng liền trước. **Không** phải DS quy đổi / lợi nhuận / số
  lượng SP / mức đạt target. Mẫu số `0` xử lý tường minh, không bịa vô cực.

Reason:
Audit `S113` chứng minh báo cáo tay không phải hàm của bất kỳ đầu vào nào
Reports có: `01.2026` thấp hơn ERP 0,58 % ở doanh số, `06.2026` thấp hơn 6,5 %
ở doanh số nhưng **cao hơn 24,3 %** ở lợi nhuận, và 635/18.148 ô giá bị gõ tay
không dấu vết. Không có bảy quyết định này thì mọi chỉ tiêu `MUST_MATCH` sẽ
được implement với một mốc so sánh không tồn tại, và DS quy đổi — chỉ tiêu
quản trị chính — sẽ được implement với ngữ nghĩa đoán.

Impact:
Bảy câu hỏi Owner của `S113` đóng hết (`OWNER_DECISIONS_REMAINING = 0`); hai
blocking finding `FIND-PHB02-B01`/`B02` đóng; `BUSINESS_PARITY_CONTRACT =
FROZEN`; `PHB_03_READY = YES`. Thêm bốn ngữ nghĩa bắt buộc mới vào hợp đồng
(`S13` giá nhập sửa được có provenance · `S14` gate coverage 100 % · `S15`
phạm vi tick `GIA_DUNG` · `S16` target cấu hình được) và hai loại trừ mới
(`X9` cột `I` tính trên DS quy đổi · `X10` dòng Summary "Gia dụng" như một
thực thể nhân viên). `D2` của `TASK-PRA-003` (Target = DEFER trong PRA-003)
**không** bị mở lại: `DEC-PHB02-06` chỉ freeze yêu cầu nghiệp vụ, và lệnh cấm
sao chép `legacy_summary_row.target` vào chỉ tiêu `PIPELINE_GENERATED` vẫn
nguyên hiệu lực. `D3` của `TASK-PRA-003` (cấm nhãn "Tổng số SP" cho tới khi có
quy tắc phân loại có thẩm quyền) nay đã có điều kiện gỡ: `DEC-PHB02-03` **là**
quy tắc có thẩm quyền đó — nhưng UI hiện tại **không đổi trong PHB-02**, việc
áp dụng thuộc PHB-03.

Evidence:
Đo trong phiên `S114` trên `tests/fixtures/golden/period_2026_*.xlsx`:
`DEC-PHB02-03` cho `358` (01.2026, loại 45 dòng) và `178` (06.2026, loại 27
dòng), so với `SUM(quantity)` mọi dòng là `407`/`210`. Đọc "giá bán" là đơn
giá hay tổng dòng cho **cùng một kết quả** ở cả hai kỳ (chênh lệch `0`). Các
mô tả bị loại nhiều nhất đúng nhóm Owner nêu: `Chi phí vận chuyển`, `Giá treo
Tivi`, `Chân máy giặt Đa Năng`, `Chi phí lắp đặt`, `Phụ Phí`.

Can Revisit After:
`DEC-PHB02-01` là nguyên tắc nền, không dự kiến mở lại. `DEC-PHB02-02` mở lại
nếu Owner chấp nhận một mức coverage khác `100 %`. `DEC-PHB02-03` mở lại nếu
ngưỡng `1.000.000 VND` cần đổi hoặc Owner muốn một taxonomy thật.
`DEC-PHB02-05` mở lại khi có nhóm nhân viên mới hoặc khi Gia dụng cần cho
nhóm ngoài wholesale/nội-thành. `DEC-PHB02-06` chi tiết hoá ở PHB-05.

Chi tiết đầy đủ, ma trận parity và bằng chứng:
`docs/tasks/PHB-02-business-parity-contract.md`;
bàn giao phiên: `docs/sessions/S114-phb-02-owner-decisions-freeze.md`.

---

## DEC-175

Title:
PHB-03 — ba quyết định TRIỂN KHAI mà hợp đồng `PHB-02` để mở: phạm vi đường
ghi giá nhập, định nghĩa `PROFIT_COVERAGE`, và nơi lưu quyết định của Owner

Date:
2026-09-04

Task:
`PHB-03` — Summary + Employee Business Parity V1. Phiên implementation S115
(nhánh `claude/phb-03-summary-employee-parity-7x3uid`), đứng trên hợp đồng
FROZEN của `PHB-02` (`DEC-174`). Task file:
`docs/tasks/PHB-03-summary-employee-business-parity.md`.
`BASE_SHA = c996ca8f92a5abd7d004ffb85a802992dd3c367f`.

Authority:
`TACTICAL_DECISION` (session), **không** `OWNER_DECISION`. Cả ba quyết định
nằm trong khoảng trống mà hợp đồng cố ý để lại cho tầng triển khai: mục 11.1
gọi câu hỏi phạm vi là *"quyết định ROADMAP, KHÔNG phải quyết định ngữ
nghĩa"*, và mục 10.11 liệt kê chỗ lưu như *"ý tưởng triển khai — KHÔNG phải
yêu cầu"*. Không quyết định nào ở đây đổi một chỉ tiêu nghiệp vụ đã freeze.
Điểm cần Independent Review chất vấn trước tiên là §2 dưới đây.

### 1. Phạm vi — PHB-03 BAO GỒM đường ghi giá nhập

```
QUYẾT ĐỊNH = BOUNDED WRITE PATH TRONG PHB-03
```

Chỉ thị phiên (`PHB-03 §3`) chốt điều này. Lý do đứng độc lập với chỉ thị:
`giá nhập → EligibleKpiProfit → lợi nhuận KPI chính thức → DS quy đổi`. Tách
đường ghi ra một vertical riêng sẽ giao một PHB-03 mà **chỉ tiêu quyết định**
— DS quy đổi, thứ `DEC-PHB02-04` gọi là *"chỉ tiêu cốt lõi đánh giá hiệu suất
nhân viên"* — không chạy được trên dữ liệu thật (coverage đo được hôm nay:
`0–2/351` golden, `34/142` production 09/2026).

"Bounded" nghĩa là: hai bảng, mỗi bảng giữ đúng MỘT quyết định hiện hành, ghi
đè tại chỗ. KHÔNG hệ thống quản lý giá nhập, KHÔNG luồng duyệt, KHÔNG
version-control, KHÔNG audit service, KHÔNG trình soạn dữ liệu kinh tế tổng
quát.

### 2. `PROFIT_COVERAGE` — 100 % của cái gì

`DEC-PHB02-02` §4 chốt **gate 100 %** và cấm ngưỡng khác, nhưng không nói
`100 %` **của cái gì**. Câu đó phải được trả lời trước khi chữ "CHÍNH THỨC"
có nghĩa.

```
PROFIT_COVERAGE = (số dòng THỰC SỰ góp một giá trị lợi nhuận KPI)
                / (tổng số dòng hiện hành của kỳ)

Một dòng góp giá trị  ⟺  status = "AUTO"                (D1/P1, TASK-PRA-003)
                     VÀ  có giá nhập KPI phân giải được (AUTO | MANUAL |
                                                         MANUAL_OVERRIDE)
                     VÀ  có sell_price và quantity
```

**Tử số đúng bằng tập được cộng.** Đó là toàn bộ lý lẽ: `coverage = 100 %`
khi đó tương đương *"mọi dòng của kỳ đều đã có mặt trong con số này"*, nên
nhãn CHÍNH THỨC không thể nói dối. Định nghĩa rộng hơn — *"số dòng có giá
nhập"* — sẽ cho `100 %` trong khi tổng vẫn bỏ sót các dòng `PENDING`, và
Owner sẽ ký một con số thiếu. Đó là đúng lớp lỗi mà `DEC-PHB02-02` tồn tại
để chặn.

**Hệ quả đã lường trước, nói thẳng.** `D1/P1` của `TASK-PRA-003` (dòng
`PENDING` KHÔNG vào tổng lợi nhuận KPI, kể cả khi có sẵn giá trị) **giữ
nguyên** — PHB-03 không nới nó, vì giá nhập do Owner nhập bù đúng MỘT input
còn thiếu, nó không phải một lượt duyệt Review Queue. Nên một kỳ còn dòng
`PENDING` sẽ **không** đạt `100 %` dù Owner nhập đủ giá nhập. Hai lý do "chưa
đủ" vì vậy được đếm và hiển thị **RIÊNG** (`missing_price_lines` vs
`review_blocked_lines`): gộp lại là hứa với Owner rằng nhập nốt giá là xong,
trong khi không phải. Ghi lại thành `FIND-PHB03-N01`, NON-BLOCKING, không mở
task.

### 3. Nơi lưu — không mở authority thứ hai

```
PURCHASE_PRICE_AUTHORITY = kpi_purchase_price_override  (migration 0003_business)
GIA_DUNG_AUTHORITY       = product_group_classification (khoá theo product_key)
PURCHASE_PRICE_AUTHORITY_CONFLICT = KHÔNG PHÁT SINH
```

Ba thẩm quyền hiện có **không bị chạm**: `accounting_purchase_price` /
`price_source` (PriceProvider, `TASK-105`/`105B`–`105E`);
`HistoricalConfirmedRegistry` (E-J — **chỉ pre-cutover**, seed từ báo cáo
Owner-confirmed thật, `INV-47`/`INV-51`/`INV-54`, nên **không** tái dụng làm
chỗ chứa giá nhập tay post-cutover); và `order_line_result_version`
(**append-only**, mỗi dòng là kết quả của MỘT lần chạy engine).

Giá do Owner nhập sống ở bảng riêng và được hợp nhất **lúc ĐỌC**, nơi
provenance vẫn nhìn thấy được. Đây đúng là slot mà
`app/modules/domain/models.py` đã chừa từ `TASK-105`
(`PRICE_SOURCE_MANUAL` — *"for when override/audit trail exists"*) và đúng ý
tưởng triển khai đã ghi ở mục 10.11 hợp đồng.

Provenance do **SERVER** quyết, từ giá AUTO đọc lại tại chỗ ngay trước khi
ghi — không do form của trình duyệt khai. Nhập lại **đúng bằng** giá AUTO vẫn
là `MANUAL_OVERRIDE`: Owner đã ra một quyết định, và xoá dấu vết quyết định
đó là nói dối về nguồn con số, đúng điều `DEC-PHB02-02` §3 cấm.

Cả hai bảng khoá theo **KHOÁ NGHIỆP VỤ**, không theo `id` version, để một lần
kế toán gửi lại sổ không xoá sạch việc Owner đã làm.

Evidence:
`FULL_TEST_SUITE = 2106 passed, 11 skipped`; `GOLDEN_BASELINE = 58 passed,
2 skipped` (KHÔNG ĐỔI); `13/13` vector nghiệm thu A–M PASS; `14/14` Exit
Criteria PASS. Bốn test của `tests/test_history_db.py` được cập nhật vì bản
kiểm kê schema/migration là danh sách ĐÓNG đã freeze và `DEC-PHB02-02`/
`DEC-PHB02-05` yêu cầu persistence mới — chúng vẫn khẳng định danh sách ĐÓNG,
chỉ dài thêm đúng hai bảng và một revision.

Can Revisit After:
Điểm §2 mở lại nếu Independent Review hoặc Owner cho rằng gate nên đọc coverage
**giá nhập** thay vì coverage **đóng góp**; đổi nó là đổi ý nghĩa của chữ
"CHÍNH THỨC" nên cần một quyết định tường minh, không phải một lần sửa code.
Điểm §3 mở lại nếu dự án có một Price Master thật (`TASK-401`) — lúc đó
`kpi_purchase_price_override` có thể trở thành lớp override MỎNG trên nó thay
vì nơi duy nhất giữ giá nhập tay. Điểm §1 đã đóng, không dự kiến mở lại.

Chi tiết đầy đủ và bằng chứng:
`docs/tasks/PHB-03-summary-employee-business-parity.md`;
bàn giao phiên: `docs/sessions/S115-phb-03-summary-employee-parity.md`;
ngân sách review: `PROJECT/REVIEW_BUDGET_LEDGER.md` → Root Task `PHB-03`.

---

## DEC-176

Title:
PHB-04 — Legacy Reference V1: ranh giới legacy THEO ORIGIN (không theo ngày),
`COMPARABLE = rỗng` ở V1, và không dựng cơ chế lưu trữ mới

Date:
2026-09-04

Task:
`PHB-04` — Legacy Reference V1. Phiên implementation S119 (nhánh
`claude/phb-04-legacy-reference-v1-widtzf`), đứng trên hợp đồng FROZEN của
`PHB-02` mục 5.6 `L1`–`L6` và trên `DEC-169`. Task file:
`docs/tasks/PHB-04-legacy-reference-v1.md`.
`BASE_SHA = 51d8fef4499642290398d795e7639e13792bee45`.

Authority:
`TACTICAL_DECISION` (session), **không** `OWNER_DECISION`. Cả ba quyết định
dưới đây suy ra từ bằng chứng đã được chấp nhận; không quyết định nào đổi một
chỉ tiêu nghiệp vụ đã freeze, và không quyết định nào nới lỏng `DEC-169`.

### 1. Ranh giới cutover là THEO ORIGIN, không phải một mốc ngày

```
CUTOVER_BOUNDARY = ORIGIN_BASED_NOT_DATE_BASED
```

Chỉ thị PHB-04 mục 10 cấm đoán một ngày và cấm suy ra ngày từ timestamp của
repo. Audit cho kết quả: repo **không có** quyết định nào định nghĩa một mốc
ngày cho báo cáo. Cái repo có là ranh giới theo nguồn dữ liệu, tính theo từng
kỳ — `origin = LEGACY_REFERENCE` (bốn bảng `legacy_*`) và
`origin = PIPELINE_GENERATED` (`order_line_*`, `snapshot_*`). Một kỳ 2026 có
thể mang cả hai; 2025 chỉ mang legacy.

`CUTOVER_DATE = 2026-09-01` **không** được tái sử dụng: đó là mốc giá /
Product Identity, và `PROJECT_PROGRESS.md` đã ghi rõ *"Hai cutover, không
gộp"*.

Vì V1 không bao giờ hợp nhất hai origin thành một con số, V1 chạy đúng mà
KHÔNG cần một mốc ngày ⟹ đây **không** phải `OWNER_DECISION_REQUIRED` chặn
PHB-04. Câu hỏi hợp nhất được ghi lại thành `OD-PHB04-A` / `OD-PHB04-B` (task
file mục 6), không chặn phần nào của V1.

### 2. `COMPARABLE` = rỗng ở V1 — kết luận, không phải sự thận trọng

```
LEGACY↔CURRENT COMPARISON = KHÔNG CHỈ TIÊU NÀO ĐƯỢC PHÉP (V1)
```

Mỗi cặp đều vướng một phân kỳ ngữ nghĩa ĐÃ FREEZE ở `PHB-02`: chiết khấu
(`S3`, `DEC-114`), DS quy đổi bằng phép chia và dòng tổng cộng thiếu (`S4`,
`X2`, `X6`), lợi nhuận KPI chỉ chính thức khi coverage 100 % (`S14`,
`DEC-PHB02-02`), số SP mang lỗi `A1` (`X1`), cột `I` so trên sai chỉ tiêu
(`X9`). `D2` của hợp đồng ("Cùng kỳ năm trước / YTD") vì vậy đóng lại theo
hướng **hiện cạnh nhau, không trừ nhau**, chứ không mở ra một phép so.

Cổng `legacy_reference.compare()` đọc bảng `CROSS_ORIGIN_CONTRACT` qua tham
số, nên mở một cặp trong tương lai là một thay đổi DỮ LIỆU, không phải sửa
nhánh điều khiển — và người mở phải bác được đúng lý do đã ghi ở dòng đó.
`test_the_gate_reads_the_contract_instead_of_hardcoding_a_refusal` chứng minh
cổng thật sự đọc hợp đồng.

Tỉ lệ `vs_last_year_ratio` (cột `AI`) vẫn hiện như trước: đó là số CŨ do Excel
tính, legacy↔legacy, không phải phép so do công cụ thực hiện.

### 3. Không dựng cơ chế lưu trữ legacy mới

```
LEGACY_STORAGE_MODEL = TÁI DÙNG bốn bảng legacy_* của TASK-PRA-001
                       KHÔNG bảng mới · KHÔNG migration · KHÔNG cột mới
```

PHB-04 mục 6 yêu cầu *audit trước, thiết kế sau*. Audit cho thấy đường lưu đã
tồn tại và đã được nghiệm thu, kèm CHECK constraint `origin = 'LEGACY_REFERENCE'`
ở tầng schema và idempotency theo fingerprint. Phần thêm của PHB-04 là một
phép CHIẾU CHỈ-ĐỌC (`legacy_monthly_reference.sales_prev_year_vnd` khoá theo
năm workbook → kỳ của năm `year - 1`; đổi khoá, KHÔNG tính lại) cộng một hợp
đồng ngữ nghĩa và một trang đọc.

Hệ quả về an toàn dữ liệu là **cấu trúc, không phải kỷ luật**: không tồn tại
đường ghi nào để tạo dòng hàng giả, chạm Product Identity/Tracking, hay sinh
KPI-profit eligibility. Nguồn của kỳ tham chiếu là `DataChart 2026!AH`
(`PHB-02` mục 5.6 `L2`) — **không phải** `Summary 2025`, nên `DEC-169` được
giữ nguyên vẹn, không nới lỏng, không suy rộng.

Evidence:
`FOCUSED = 35 passed` (`tests/test_phb04_legacy_reference.py`);
`FULL_TEST_SUITE = 2171 passed, 11 skipped` (baseline trước phiên
`2136 passed, 11 skipped` ⟹ chênh `+35` đúng bằng số test mới, không test cũ
nào bị sửa/bỏ/tắt); `GOLDEN = 74 passed, 2 skipped` (KHÔNG ĐỔI);
`15/15` Exit Criteria PASS trừ `E14` (Independent Review) = PENDING.
Validator: `validate_structure`/`validate_project_state`/`validate_evidence`/
`validate_task_completion` PASS; `validate_reference_integrity` FAIL với ĐÚNG
3 reference `REM-T06` đã biết (baseline không đổi).

Can Revisit After:
Điểm §2 mở lại khi một chỉ tiêu được CHỨNG MINH là cùng nghĩa ở hai bên —
thêm một dòng vào `CROSS_ORIGIN_CONTRACT`, kèm bằng chứng bác lý do đang ghi.
Điểm §1 mở lại nếu chủ dự án yêu cầu hiển thị MỘT con số duy nhất cho một kỳ
có cả hai origin (`OD-PHB04-A`). Điểm §3 mở lại nếu xuất hiện bằng chứng
legacy ở mức DÒNG (line-level) mà mô hình period/metric hiện tại không chứa
được — hôm nay không có bằng chứng nào như vậy.

Chi tiết đầy đủ và bằng chứng:
`docs/tasks/PHB-04-legacy-reference-v1.md`;
báo cáo cho chủ dự án:
`docs/reviews/PHB-04-legacy-reference-v1-implementation.md`.

---

## DEC-177

Title:
PHB-04 — Đính chính của chủ dự án: `Summary 2025` KHÔNG bị cấm, nó là
OPTIONAL_IMPORT. Làm rõ nghĩa thật của `DEC-169` và mở lại phạm vi 2025

Date:
2026-09-04

Task:
`PHB-04` — Legacy Reference V1, phiên S119 (tiếp tục, nhánh
`claude/phb-04-legacy-reference-v1-widtzf`). Phát sinh khi chủ dự án đọc
báo cáo PHB-04 lần đầu và bác bỏ kết luận *"với năm 2025 — đúng một chỉ
tiêu: doanh số tháng"*.

Authority:
**`OWNER_DECISION`.** Chủ dự án xác nhận nguyên văn rằng 2025 có (1) một
Summary riêng, (2) báo cáo chi tiết theo nhân viên, (3) cấu trúc gần giống
báo cáo tay 2026. Tuyên bố hiện tại của chủ dự án có thẩm quyền nghiệp vụ
CAO HƠN một cách diễn giải của AI về một quyết định cũ.

### 1. `DEC-169` thật sự có nghĩa gì

Đọc đúng nguyên văn `DEC-169`, không diễn giải rộng thêm:

```text
"Owner KHÔNG yêu cầu: import / persist / query / display Summary 2025;
 xây parser cho value-only rows của Summary 2025."
```

Đó là *"chưa cần"* — một tuyên bố **PHẠM VI**. Nó KHÔNG phải *"không được
có"* — một lệnh **CẤM SẢN PHẨM**. Chính `DEC-169` tự đặt tên mình là
`OWNER_SCOPE_CLARIFICATION` và ghi rõ `REPAIR_CYCLE_2 = NO`.

Chiếu theo bốn khả năng mà chỉ thị đính chính nêu:

```text
A. cấm dùng làm CURRENT_ENGINE / production accounting input   → ĐÚNG, vẫn giữ
B. cấm dùng làm thẩm quyền số cho parity validation            → ĐÚNG, vẫn giữ
C. cấm parse qua contract phân loại dòng THEO CÔNG THỨC        → ĐÚNG, vẫn giữ
D. loại khỏi sản phẩm hoàn toàn, kể cả LEGACY_REFERENCE        → **SAI**
```

Bản triển khai PHB-04 đầu tiên đã đọc `DEC-169` theo nghĩa `D`. Đó là một
**diễn giải quá rộng của phiên làm việc**, không phải nội dung quyết định.
`DEC-177` sửa đúng chỗ đó và KHÔNG lật `A`/`B`/`C`.

Bối cảnh kỹ thuật của `DEC-169` cũng cần đọc cho đúng: `Summary 2025` bị dán
cứng thành giá trị tĩnh (0 ô công thức / 99 dòng value-only), nên contract
phân loại dòng **theo công thức** không áp dụng được. Đó là một giới hạn của
CÁCH ĐỌC, không phải một tuyên bố rằng dữ liệu không tồn tại.

### 2. Vì sao bản triển khai đầu tiên chỉ thấy 12 số của 2025

Cả chuỗi bằng chứng đều **bị chặn bởi công thức**, ở ba tầng độc lập:

1. `tools/analysis/extract_evidence.py` chỉ ghi một dòng Summary khi cột `F`
   của dòng đó **là một công thức**. `Summary 2025` không có công thức nào ⟹
   `evidence.json` chứa **0 lần xuất hiện chuỗi "2025"**.
2. `app/legacy/parser.py::_classify()` phân loại `row_kind` hoàn toàn từ
   cấu trúc công thức ⟹ không dòng 2025 nào phân loại được.
3. Vì (1) và (2), bằng chứng 2025 DUY NHẤT còn nhìn thấy được là cột `AH`
   của `DataChart 2026` — 12 ô doanh số tháng.

Kết luận "2025 chỉ có một chỉ tiêu" vì vậy là **kết luận về công cụ đọc**,
bị trình bày nhầm thành **kết luận về dữ liệu**. Đó là lỗi thật của bản báo
cáo đầu, và nó được sửa ở đây chứ không được giữ lại.

### 3. `Summary 2025` = OPTIONAL_IMPORT

```text
SUMMARY_IMPORT_SHEETS   = ("Summary 2026",)            REQUIRED_IMPORT
SUMMARY_OPTIONAL_SHEETS = ("Summary 2025",)            OPTIONAL_IMPORT
```

Ngữ nghĩa `OPTIONAL_IMPORT`:

- dòng contract phân loại được → **NHẬP**, `origin = LEGACY_REFERENCE`;
- dòng không phân loại được → **KHÔNG đoán**, nhưng cũng **KHÔNG bỏ im
  lặng**: đếm, lưu vào `sheets_imported`, và hiện lên trang `/lich-su`;
- sheet vắng mặt hoặc không đọc được dòng nào → **KHÔNG** làm trượt cả
  workbook.

Nhánh cuối là điều kiện để `DEC-177` không lật ngược `DEC-169` thành một hồi
quy: hình dạng value-only của workbook thật vẫn phải nhập được phần 2026.

**Guard `DEC-168` / `FIND-PRA001-R01` KHÔNG bị nới lỏng.** Trên sheet
REQUIRED_IMPORT, một dòng có giá trị nghiệp vụ mà contract không phân loại
được vẫn FAIL TO. Bất đối xứng là có chủ đích: thiếu một dòng production
nghĩa là **số hiển thị sai**; thiếu một dòng lịch sử nghĩa là **còn một phần
chưa đọc được** — cần nói ra, không cần chặn.

### 4. Không đổi schema

```text
SCHEMA_CHANGE_REQUIRED = NO
```

`legacy_summary_row` vốn đã khoá theo `(year, month, seller_label, row_kind)`
với đủ 16 cột `C..S` và **không hề gắn với năm 2026**. Nó lưu được ngay cả
period-level lẫn employee-level của 2025 mà không thêm một cột nào. Vì vậy
`DEC-177` KHÔNG dùng quyền mở rộng schema mà chỉ thị đính chính cho phép:
quyền đó chỉ được dùng khi có nhu cầu thật, và ở đây không có.

Hệ quả kèm theo: trang `/nhan-vien` (chi tiết theo nhân viên) vốn đã
year-agnostic, nên nó phục vụ 2025 **ngay khi có dòng 2025**, không cần sửa.

### 5. Hiển thị ≠ so sánh

`DEC-177` mở phạm vi **HIỂN THỊ**. Nó KHÔNG đổi kết luận của `DEC-176` §2:
`COMPARABLE` vẫn rỗng, không tỉ lệ tăng trưởng liên-origin nào được sinh ra.
Một chỉ tiêu 2025 có thể vừa **xem được** vừa **không so được** — hai câu
hỏi khác nhau, và loại bỏ dữ liệu lịch sử hữu ích chỉ vì phép so không an
toàn là trả lời nhầm câu hỏi.

### 6. Phần còn thiếu — `NEED_OWNER_SOURCE`

Workbook thật KHÔNG có trong repo (`data/samples/` nằm trong `.gitignore` vì
chứa dữ liệu cá nhân khách hàng) và không có trên đĩa của phiên. Vì vậy nội
dung thật của 99 dòng `Summary 2025` **chưa từng được quan sát** bởi bất kỳ
artifact bằng chứng nào của repo. Năng lực đã sẵn sàng và đã có test; dữ
liệu thì cần chủ dự án cấp. Xem `docs/tasks/PHB-04-legacy-reference-v1.md`
mục 10.

Evidence:
`FOCUSED = 50 passed` (`tests/test_phb04_legacy_reference.py`);
`FULL_TEST_SUITE = 2187 passed, 11 skipped`;
`GOLDEN = 74 passed, 2 skipped` (KHÔNG ĐỔI).
10 test cũ mã hoá phạm vi `DEC-169` đã được cập nhật sang phạm vi
`DEC-177` — liệt kê đầy đủ ở task file mục 11; không test guard nào bị bỏ.
Validator giữ nguyên baseline (reference integrity vẫn đúng 3 mục `REM-T06`).

Can Revisit After:
Mục §3 mở lại nếu chủ dự án cấp nguồn 2025 và contract phân loại vẫn không
đọc được — lúc đó câu hỏi là "phân loại dòng value-only bằng NHÃN cột A/B
theo từ vựng nào", và từ vựng đó phải đến từ file thật, không từ phỏng đoán.
Mục §5 mở lại theo đúng điều kiện của `DEC-176` §2.

Chi tiết đầy đủ và bằng chứng:
`docs/tasks/PHB-04-legacy-reference-v1.md`;
báo cáo cho chủ dự án:
`docs/reviews/PHB-04-legacy-reference-v1-implementation.md`.

---

## DEC-178

Title:
2025 Legacy Source Authority — workbook lịch sử một năm độc lập là NGUỒN
CHUẨN của năm đó; bản sao Summary nhúng trong workbook năm hiện hành là bằng
chứng THỨ CẤP

Date:
2026-09-05

Task:
`PHB-04` — Legacy Reference V1. Phiên S119 (pass triển khai cuối), nhánh
`claude/phb-04-legacy-reference-v1-widtzf`. Chủ dự án cấp hai workbook thật
và ra quyết định nguồn.

Authority:
**`OWNER_DECISION` — FROZEN.** Đây không còn là câu hỏi mở; phiên sau KHÔNG
được hỏi lại "workbook 2025 nào thắng".

### 1. Quyết định

```text
AUTHORITATIVE_2025_LEGACY_SOURCE = Báo cáo Kinh doanh 2025.xlsx (workbook độc lập)
SECONDARY_2025_LEGACY_SOURCE     = sheet `Summary 2025` nhúng trong
                                   Báo cáo Kinh doanh 2026.xlsx
KHI LỆCH NHAU                    = workbook độc lập THẮNG
```

Bản thứ cấp **KHÔNG** được ghi đè, thay thế, hoà trộn hay lấy trung bình với
bản chuẩn, và **KHÔNG** được trở thành nguồn chính chỉ vì nó dễ parse hơn.
Nó vẫn được giữ lại làm bằng chứng đối chiếu — không xoá.

### 2. Ranh giới — điều quyết định này KHÔNG cho phép

"Nguồn chuẩn LỊCH SỬ" **không** đồng nghĩa "thẩm quyền của engine hiện tại".
2025 vẫn là `LEGACY_REFERENCE`. Workbook độc lập có thẩm quyền trả lời
*"hệ thống báo cáo cũ đã ghi gì cho 2025?"*, **không** trả lời
*"engine hiện tại sẽ tính ra gì cho 2025?"*. Không chạy lại 2025 qua công
thức nghiệp vụ hiện hành. `DEC-176` §2 (`COMPARABLE` rỗng) **giữ nguyên**:
hiển thị và so sánh vẫn là hai hợp đồng khác nhau.

### 3. Hình dạng thật của nguồn chuẩn (đo trực tiếp trên file, S119)

```text
TỔNG SHEET                  = 76
  sheet chi tiết MM.2025 X  = 74   (đủ 12 tháng: 7·6·5·5·6·6·6·7·7·7·6·6)
  Summary                   =  1   1005 ô công thức, liên kết chéo tới 74 sheet
  BestStaff                 =  1   bảng thi đua nhân viên theo quý
NGUỒN THỨ CẤP `Summary 2025` = 0 ô công thức (value-only), cùng bố cục 755 dòng
```

Nhập qua đường production: **93 dòng Summary** — 74 `SELLER` (khớp ĐÚNG 74
sheet chi tiết) + 12 `MONTH_TOTAL` + 7 `PROGRESS`; **0 dòng chưa phân loại
được**; 6 dòng khối tổng kết KPI bị loại trừ tường minh (xem §5).

### 4. Cơ chế thực thi — quy tắc sống ở TẦNG TRUY VẤN

Một cột `legacy_import.source_authority` (`AUTHORITATIVE_YEAR` /
`WORKBOOK_SNAPSHOT`, `NULL` = bản nhập trước quyết định này ⟹ đọc như thứ
cấp), migration `0005_legacy_source_authority` — ADDITIVE thuần, một cột
nullable.

`SCHEMA_CHANGE_REQUIRED = YES`, và đây là chỗ duy nhất PHB-04 dùng quyền mở
rộng schema. Lý do: `is_current` là con trỏ MỘT bản cho toàn history, không
phải thẩm quyền THEO NĂM — dùng nó sẽ khiến nhập workbook 2025 làm biến mất
mọi kỳ 2026. `version_label`/`notes` là văn bản tự do; giải quyết một quy tắc
thẩm quyền bằng cách so chuỗi tự do là để quyết định của chủ dự án phụ thuộc
vào lỗi chính tả. Suy từ tên sheet thì biến thẩm quyền thành hệ quả tình cờ
của cách đặt tên — đúng kiểu ngầm định mà quyết định này cấm.

Quy tắc được thực thi ở `LegacyRepository._import_for_year()`: đọc một năm
thì **thẩm quyền TRƯỚC, "đang xem" SAU**. Vì nó nằm ở tầng truy vấn chứ
không ở lời dặn trong tài liệu, không có đường nào để bản thứ cấp âm thầm
thay thế bản chuẩn. Workbook một-năm cũng **không** cướp con trỏ `is_current`
(trừ khi nó là bản nhập đầu tiên), nên nhập 2025 không làm mất 2026.

### 5. Khối tổng kết KPI bị loại trừ — tường minh, không phải nuốt lỗi

Dưới 12 khối tháng, sheet `Summary` có một khối tổng kết cuối năm mở đầu bằng
ô `C = "Tổng KPI"` (quan sát: đúng MỘT lần mỗi sheet Summary 2025, và KHÔNG
có trong `Summary 2026`). Ở đó **các cột mang ý nghĩa khác hẳn**: `C` là
"Tổng KPI" (cộng cột `N` của 12 tháng), `D` là "KPI trung bình" — không phải
"Tổng đơn" và "Tổng số SP". Nhập chúng vào cùng bộ cột sẽ ghi ra
"Tổng đơn của Ly = 10,79".

Guard `DEC-168` đã bắt đúng khối này ngay lần chạy đầu trên file thật. Khối
được loại trừ theo TIÊU ĐỀ mà workbook tự viết, và số dòng bị loại được ghi
vào `sheets_imported` (`recap_rows_excluded`) để kiểm chứng được.

### 6. Đối chiếu hai nguồn (bằng chứng, không phải sản phẩm)

`tools/analysis/compare_legacy_2025_sources.py`, so theo từng ô:

```text
TOTAL_CELLS_COMPARED   = 1132
EXACT_MATCH            =  573
ROUNDING_ONLY          =  505   (B == round(A, n) — bản sao lưu số đã làm tròn)
SUBSTANTIVE_DIFFERENCE =   42   trên 12 dòng
MISSING_IN_A           =    0
MISSING_IN_B           =   12
```

"Chỉ là làm tròn" xác định bằng CƠ CHẾ (`B == round(A, n)`), không bằng một
ngưỡng tự chọn — nên một đơn hàng lệch (105 so với 104) không bao giờ bị xếp
nhầm vào đó.

Khác biệt nghiệp vụ thật tập trung ở **tháng 12/2025** (`Ly`, `Nội thành`, và
dòng tổng tháng), cộng các ô lương `Q`/`R` mà bản thứ cấp để 0. Ăn khớp với
giả thuyết: bản sao nhúng được lấy trước khi 12/2025 chốt sổ. Mọi con số chủ
dự án nêu trong chỉ thị đều được xác nhận trên file thật, gồm dòng tổng
tháng 12 (`A = 23.016.871`, `B = 23.097.181`).

### 7. Chi tiết từng dòng bán hàng — DEFERRED

```text
LEGACY_LINE_DETAIL_2025 = DEFERRED
BESTSTAFF               = OUT_OF_SCOPE
```

74 sheet chi tiết chứa **62.802 dòng** trên **6 biến thể bố cục**, và mọi
biến thể đều có cột `Tên khách hàng`, `Số điện thoại`, `Địa chỉ`. Đưa chúng
vào history store là một quyết định **quản trị dữ liệu cá nhân**
(`governance/product/17_DATA_GOVERNANCE_PRIVACY.md`), không phải một chi
tiết triển khai của PHB-04 — và §10 của chỉ thị cho phép hoãn đúng khi cần
parser tổng quát cho nhiều bố cục. Tên sheet vẫn được ghi lại
(`scope = DETAIL_NOT_INGESTED`, `imported_rows = 0`) để chúng hiện ra là
"hoãn có chủ đích", không phải "bị bỏ quên".

`BestStaff` là bảng thi đua nhân viên theo quý — tính năng xếp hạng nhân sự,
ngoài phạm vi. Finding không tạo task.

Evidence:
`FOCUSED = 79 passed` (`tests/test_phb04_legacy_reference.py`);
`FULL_TEST_SUITE = 2216 passed, 11 skipped`;
`GOLDEN = 74 passed, 2 skipped` (KHÔNG ĐỔI);
`tests/test_history_db.py = 17 passed` (round-trip migration qua alembic thật,
chain `0001 → 0005`). Validator giữ nguyên baseline (reference integrity vẫn
đúng 3 mục `REM-T06`).

Can Revisit After:
§7 mở lại khi có một quyết định quản trị dữ liệu cá nhân cho phép lưu dòng
chi tiết lịch sử, kèm phạm vi cột được lưu. §1 KHÔNG dự kiến mở lại — đây là
quyết định đã freeze của chủ dự án.

Chi tiết đầy đủ và bằng chứng:
`docs/tasks/PHB-04-legacy-reference-v1.md`;
báo cáo cho chủ dự án:
`docs/reviews/PHB-04-legacy-reference-v1-implementation.md`.

## DEC-179

Date:
2026-09-05

Task:
S120 — PHB-03/PHB-04 production follow-up audit

Decision:
Bảng kê chi tiết `/kinh-doanh/gia-nhap` có bộ lọc **MẶC ĐỊNH = `tat-ca`**
(toàn bộ dòng của kỳ/nhân viên đang xem), thay cho mặc định cũ `thieu-gia`.
Ba chế độ thu hẹp — `thieu-gia`, `chua-ro-nv`, và `owner-sua` (`R3`, mới) —
vẫn giữ nguyên hành vi và phải được chọn TƯỜNG MINH. Khi một chế độ thu hẹp
đang bật, trang phải NÓI RA rằng danh sách bên dưới là một tập con.

Đường dẫn từ khối coverage của trang Tổng hợp và trang Nhân viên trỏ tới
`thieu-gia` khi coverage < 100 % và `tat-ca` khi coverage = 100 %. Trang Nhân
viên có thêm một đường vào cố định "XEM TẤT CẢ DÒNG CỦA NHÂN VIÊN NÀY".

Reason:
Chủ dự án mở trang nhân viên trên production và chỉ thấy các dòng CHƯA hoàn
thiện; các dòng đã đủ thông tin không xuất hiện. Nguyên nhân không phải dữ
liệu và không phải phép tính — tổng, coverage và KPI luôn đọc TOÀN BỘ dòng —
mà là bộ lọc mặc định của đúng trang mà mọi đường dẫn từ trang nhân viên đều
dẫn tới. Một khung nhìn BÁO CÁO không được âm thầm trở thành hàng đợi việc
tồn: chủ dự án phải nhìn được trọn tập dữ liệu liên quan rồi mới thu hẹp.

Hệ quả thứ hai của mặc định cũ: khi coverage đã đạt 100 %, cùng một nút "MỞ
BẢNG KÊ CHI TIẾT" cho ra một bảng RỖNG — đúng lúc mọi thứ đã hoàn tất thì
màn hình trông như mất dữ liệu.

Impact:
Chỉ đổi KHUNG NHÌN. Không chỉ tiêu nghiệp vụ nào đổi giá trị: bộ lọc chỉ tác
động lên danh sách dòng, còn `coverage` và mọi tổng đều tính từ tập dữ liệu
CHƯA lọc (`data.totals`). Không thêm trạng thái, không thêm workflow, không
đổi thẩm quyền nguồn, không đổi schema.

Evidence:
`tests/test_phb03_followup_repairs.py` (32 passed) — trong đó bốn khẳng định
tham số hoá chứng minh coverage `1 / 2 dòng · 50%` KHÔNG đổi ở cả bốn chế độ
lọc; `FULL_TEST_SUITE = 2248 passed, 11 skipped`;
`GOLDEN = 74 passed, 2 skipped` (KHÔNG ĐỔI so với baseline).

Can Revisit After:
Mở lại nếu chủ dự án muốn một mặc định khác cho riêng luồng hoàn thiện giá
nhập. Điều KHÔNG mở lại: một khung nhìn thu hẹp mà không nói ra rằng nó thu
hẹp.

---

## DEC-180

Title:
Chủ dự án đính chính: sổ tay cũ KHÔNG báo cáo doanh số gộp — nó trừ chiết
khấu bằng MỘT DÒNG ÂM. `Tổng bán` cũ và `Doanh thu bán hàng` mới là CÙNG
một chỉ tiêu nghiệp vụ

Date:
2026-09-05

Task:
S121 — bản sửa có ràng buộc theo thẩm quyền chủ dự án, trên nhánh
`claude/phb-04-legacy-reference-v1-widtzf`.
`BASE_SHA = e1458862adfd8a945ac2b1df6b42b336fb390b30`.

Authority:
`OWNER_DECISION`. Đây KHÔNG phải một suy luận của phiên làm việc: chủ dự án
đã cung cấp trực tiếp ngữ nghĩa nghiệp vụ của sổ tay cũ, và ngữ nghĩa đó bác
một giả định mà các bản audit trước đã suy sai.

Supersedes:
`DEC-176` §2 ở PHẦN liên quan tới `Tổng bán` (`sales` / `sales_vnd` →
`sales_revenue`), và các dòng lý do tương ứng trong `REFERENCE_YEAR_CONTRACT`
/ `SUMMARY_SHEET_CONTRACT`. Bản ghi `DEC-176` KHÔNG bị sửa tại chỗ — nó là
bản ghi lịch sử của kết luận ĐÚNG tại thời điểm đó, và `DEC-176` §2 đã viết
sẵn con đường mở: *"thêm một dòng vào `CROSS_ORIGIN_CONTRACT`, kèm bằng chứng
bác lý do đang ghi"*. `DEC-180` đi đúng con đường đó.

Không phần nào của `DEC-176` §1 (ranh giới theo origin) hay §3 (không dựng
lưu trữ mới) bị đụng tới. `DEC-177`, `DEC-178`, `DEC-179` giữ nguyên vẹn.

### 1. Bằng chứng nghiệp vụ — sổ tay cũ trừ chiết khấu bằng một dòng âm

```
Tủ lạnh      SL 1   giá bán 5.000.000   Tổng bán   5.000.000
Chiết khấu   SL 1   giá bán 0           Tổng bán    -100.000   (giá nhập KPI = 100.000)
------------------------------------------------------------
                                        còn lại    4.900.000
```

Sổ kế toán hiện hành ghi CÙNG nghiệp vụ đó bằng một CỘT `discount`, và
pipeline đã trừ nó rồi (`DEC-114` cho doanh thu, `DEC-143` cho lợi nhuận KPI).

```
LEGACY_TOTAL_SALES  ==  CURRENT_TOTAL_SALES   (cùng chỉ tiêu nghiệp vụ)
LEGACY_REPRESENTATION  !=  CURRENT_REPRESENTATION   (khác cách GHI)
```

Lý do chặn cũ — *"báo cáo tay trừ chiết khấu khác cách công cụ hiện tại
trừ"* (`PHB-02` §5.2 `S3`) — vì vậy bị BÁC. Nó mô tả đúng một khác biệt về
CÁCH GHI và suy sai ra một khác biệt về NGHĨA.

Điều bản sửa này KHÔNG làm, và mỗi điều đóng một cách hỏng:

```
KHÔNG bỏ chiết khấu khỏi phép tính hiện hành
KHÔNG dựng ranh giới phương pháp luận Gross-vs-Net
KHÔNG trừ chiết khấu hai lần
```

### 2. Trình bày — phân rã, KHÔNG phải một số hạng mới

Bảng kê chi tiết dựng lại hình dạng của sổ cũ bằng cách CHIA con số canonical
đã có làm hai phần cộng lại đúng bằng chính nó:

```
canonical  =  (canonical + discount)  +  (− discount)
               └── dòng sản phẩm ──┘     └── dòng "Chiết khấu" ──┘
```

Bất biến bắt buộc, đúng cho cả ba chỉ tiêu tiền và cho mọi dòng (kể cả dòng
chưa tính được lợi nhuận, nơi CẢ HAI phần đều là `—` chứ không phải `0`):

```
Σ(DISPLAY_TOTAL_SALES)      ==  CANONICAL_TOTAL_SALES
Σ(DISPLAY_KPI_PROFIT)       ==  CANONICAL_KPI_PROFIT
Σ(DISPLAY_CONVERTED_SALES)  ==  CANONICAL_CONVERTED_SALES
```

DS quy đổi là chỗ DUY NHẤT có làm tròn (`quantize` tới 0,01 VND), nên nó có
một quy ước để bất biến đúng TUYỆT ĐỐI chứ không "xấp xỉ": phần chiết khấu
dùng ĐÚNG công thức và ĐÚNG tỉ lệ của dòng cha (`converted_sales(−discount,
rate)`), và dòng sản phẩm nhận phần CÒN LẠI. Chênh lệch làm tròn (≤ 0,01 VND)
nằm trong tổng thay vì rơi ra ngoài.

Dòng `"Chiết khấu"` là DỮ LIỆU TRÌNH BÀY suy ra từ nguồn. Nó KHÔNG phải: một
mặt hàng tồn kho · một đầu vào Product Identity · một ứng viên tra giá nhập ·
một dòng thiếu giá nhập · một ô nhập giá tay · một vấn đề gán nhân viên · một
đơn hàng · một sản phẩm đủ điều kiện · một `order_line_current` mới. Ranh giới
này là CẤU TRÚC, không phải kỷ luật: dòng đó không tồn tại ở tầng mà bộ lọc và
phép cộng đọc (`BusinessLine`), và template không dựng form nào cho nó ⟹
không có đường ghi nào từ nó xuống database.

Cột `discount` của nguồn giữ nguyên vai trò bằng chứng thô có thẩm quyền.
Không bản ghi nào bị sửa, không bảng nào được thêm, không migration nào chạy.

### 3. Liên-origin — mở ĐÚNG hai cặp Tổng bán, không mở lây

```
sales      → sales_revenue   =  ĐƯỢC PHÉP SO
sales_vnd  → sales_revenue   =  ĐƯỢC PHÉP SO

profit             → kpi_profit           =  VẪN CHẶN
converted_revenue  → converted_sales      =  VẪN CHẶN
orders             → orders               =  VẪN CHẶN
products           → qualifying_quantity  =  VẪN CHẶN
```

Bốn cặp còn lại vướng những phân kỳ KHÁC (giá nhập sửa tay trong Excel, dòng
tổng cộng thiếu người bán, hai cách đếm đơn, lỗi `A1`) mà chủ dự án KHÔNG
bác. Mở lây sang chúng là làm đúng điều `DEC-176` cấm.

`MetricRule.metric_class` của `sales`/`sales_vnd` đổi từ `REFERENCE_ONLY`
sang `COMPARABLE` để hai biểu diễn của cùng một phán quyết không mâu thuẫn
nhau trên màn hình.

### 4. So tháng trước bắc qua ranh giới bàn giao

```
MỘT kỳ  ⟹  MỘT nguồn có thẩm quyền  ⟹  MỘT giá trị Tổng bán
```

Khi kỳ đang xem có dữ liệu số mới và tháng LIỀN TRƯỚC không có dòng số mới
nào, mốc so sánh lấy Tổng bán chuẩn của tháng đó từ sổ cũ. Thứ tự thẩm quyền,
nguồn đầu tiên CÓ SỐ thắng và không nguồn nào bổ sung cho nguồn nào:

```
1. dòng MONTH_TOTAL của sheet Summary cho đúng (năm, tháng)   [kVND]
2. ô tháng của DataChart (`sales_current_year_vnd`)           [VND]
```

Bản nhập nào được đọc cho một năm đã do `DEC-178` chốt ở tầng history store —
`DEC-180` không đổi quy tắc đó. KHÔNG cộng hai nguồn, KHÔNG trộn dòng thô,
KHÔNG tự cộng lại các dòng người bán (tự cộng lại là công cụ TÍNH LẠI số cũ,
điều `TASK-PRA-001` §20 cấm; lỗi `A2` đã biết của dòng tổng tháng được NÓI RA
qua `defects`, không được vá lén).

Origin phải HIỆN RA: trang Tổng hợp hiện nhãn `SỐ CŨ`, tên nguồn, và một câu
nói rõ mốc so đến từ đâu.

Trang NHÂN VIÊN cố ý KHÔNG dùng đường này: số cũ của một tháng là tổng của CẢ
CÔNG TY, nên đem nó làm mẫu số cho doanh thu của một người là một phép so sai.
Ghép tên người bán trong sổ cũ với nhân viên hiện hành là một bài toán ánh xạ
riêng, chưa có quyết định nào cho phép.

### 5. An toàn đơn vị — `Summary` là kVND, số mới là VND

Chừng nào hai bên không gặp nhau trong một phép tính, chênh lệch 1.000 lần đó
vô hại. `DEC-180` cho phép chúng gặp nhau, nên nó lập tức trở thành một lỗi
im lặng hạng nặng: quên nhân 1.000 thì `1.000 kVND` vào mẫu số dưới dạng
`1.000`, và "So tháng trước" ra `+489.900 %` — một con số TRÔNG NHƯ một con
số, không như một lỗi.

Vì vậy mọi giá trị legacy đi vào một phép tính của số mới phải qua `to_vnd()`,
và một `unit_kind` lạ là LỖI (`UnknownUnitError`) chứ không phải một hệ số
mặc định — mặc định `1` chính là cách quên nhân 1.000 sống sót.

Impact:
KHÔNG chỉ tiêu gộp nào đổi giá trị. Đo trực tiếp: cùng một tập 5 dòng có
chiết khấu ở bốn hình dạng khác nhau, chạy script gộp ở `e145886` và ở
`FINAL_HEAD`, hai file JSON GIỐNG NHAU TỪNG BYTE (`lines`, `orders`,
`sales_revenue`, `qualifying_quantity`, `kpi_profit`, `converted_sales`,
`employee_attributed_profit`, `unattributed_profit`, toàn bộ `coverage`,
`state`, và bảng phân hoạch theo nhân viên).

Không schema, không migration, không bảng mới, không cột mới, không đường ghi
mới, không workflow mới. Phần thêm là: một phép phân rã THUẦN ở
`business_metrics`, cách render của nó ở `business_presentation` + template,
một bộ phân giải nguồn kỳ THUẦN ở `legacy_reference`, và một điểm ráp ở
`server.py`.

Evidence:
`FOCUSED = 57 passed` (`tests/test_dec180_discount_parity.py`);
`FULL_TEST_SUITE = 2307 passed, 11 skipped` (baseline trước phiên
`2248 passed, 11 skipped` ⟹ chênh `+59`, đúng bằng 57 test mới cộng 2 test
được TÁCH ĐÔI khi cập nhật `test_phb04_legacy_reference.py` — không test nào
bị xoá, bỏ qua hay tắt);
`GOLDEN = 74 passed, 2 skipped` (KHÔNG ĐỔI);
`PHB-03 = 133 passed`; `PHB-04 = 183 passed`.
Ba phép thử đột biến chứng minh khẳng định có răng: bỏ hệ số kVND→VND ⟹ 6
FAIL; để dòng cha hiện số NET trong khi vẫn thêm dòng `−discount` (trừ hai
lần) ⟹ 3 FAIL; thay phần dư làm tròn của DS quy đổi bằng hai phép chia độc
lập ⟹ 1 FAIL.
Validator: `validate_structure` / `validate_project_state` /
`validate_evidence` / `validate_task_completion` PASS;
`validate_reference_integrity` FAIL với ĐÚNG 3 reference `REM-T06` đã biết
(baseline không đổi).

Can Revisit After:
Mở lại phần §3 cho một cặp KHÁC chỉ khi lý do chặn đang ghi của chính cặp đó
bị bác bằng bằng chứng — đúng cùng một tiêu chuẩn mà `DEC-180` vừa phải đáp
ứng. Mở lại §4 cho trang nhân viên chỉ sau khi có một quyết định về ánh xạ
tên người bán lịch sử ↔ nhân viên hiện hành. Điều KHÔNG mở lại: trừ chiết
khấu hai lần, gộp hai origin vào một con số, và dùng một giá trị legacy chưa
chuẩn hoá đơn vị trong một phép tính của số mới.

---

## DEC-181

Title:
Chủ dự án đơn giản hoá mô hình sản phẩm: KHÔNG còn "chọn bản legacy". Có
ĐÚNG MỘT nguồn lịch sử logic `LEGACY_HISTORY`, ghép từ HAI file provenance
cố định — và `is_current` thôi làm thẩm quyền nghiệp vụ

Date:
2026-09-05

Task:
R2 — `UNIFIED LEGACY_HISTORY`. Bản sửa có ràng buộc, nhánh R2 tách từ
`BASE_HEAD = f0c644fd828b37d35a8363c01f11530727272f01`.

Authority:
**`OWNER_DECISION` — FROZEN.** Đây không phải suy luận của phiên làm việc:
chủ dự án ra quyết định sản phẩm và bác thẳng luồng UX đang có.

Supersedes:
Luồng UX "chọn bản legacy đang xem" (`Bản đang xem` / `CHỌN BẢN NÀY` /
`POST /du-lieu/legacy/<id>/chon`) và vai trò của `is_current` như thẩm quyền
đọc lịch sử — vai trò đó đến từ `TASK-PRA-001` và được `DEC-178` §4 vá một
phần. Các bản ghi lịch sử KHÔNG bị sửa tại chỗ: `DEC-169`, `DEC-176`,
`DEC-177`, `DEC-178`, `DEC-179`, `DEC-180` giữ nguyên văn. Quy tắc thẩm
quyền của `DEC-178` (workbook một năm độc lập THẮNG bản sao nhúng) được GIỮ
NGUYÊN và nay là bậc 1 của bộ giải nguồn thống nhất.

### 1. Quyết định

```text
LEGACY_LOGICAL_SOURCES           = 1        (LEGACY_HISTORY)
LEGACY_PHYSICAL_PROVENANCE_FILES = 2

LEGACY_HISTORY
    2025-01 .. 2025-12  →  Báo cáo Kinh doanh 2025.xlsx (workbook một năm độc lập)
    2026-01 .. 2026-08  →  Báo cáo Kinh doanh 2026.xlsx (workbook năm hiện hành)
```

Bản sao `Summary 2025` nhúng trong workbook 2026 **KHÔNG** là thẩm quyền của
2025 và **KHÔNG** được ghi đè workbook 2025 độc lập (`DEC-178` giữ nguyên).

Hai file là **PROVENANCE**, không phải hai bộ dữ liệu để chọn. Với hệ thống
nghiệp vụ: `2025 + 01–08/2026 = MỘT` nguồn lịch sử.

### 2. Điều bị gỡ khỏi hành vi sản phẩm bình thường

- "Bản đang xem" / "Chọn bản này" / mọi nút chọn một bản nhập legacy;
- `is_current` quyết định kỳ lịch sử nào tồn tại;
- đổi workbook để một năm khác hiện ra;
- Summary/MoM/lịch sử xuất hiện hay biến mất vì người dùng chọn một file.

Người dùng **không bao giờ** phải chọn workbook 2025 hay 2026 để xem lịch sử.

### 3. `is_current` — metadata tương thích ngược, KHÔNG phải thẩm quyền

Cột `legacy_import.is_current` được GIỮ (không migration để xoá — xoá một
cột là rủi ro lớn hơn hẳn giá trị của việc xoá). Sau R2 nó KHÔNG điều khiển:
danh mục kỳ lịch sử, `query_summary()`, `query_monthly_reference()`,
`query_daily()`, fallback MoM, hay bất kỳ trang báo cáo bình thường nào.
Đổi giá trị của nó phải cho ra kết quả **GIỐNG HỆT** — có test canh
(`tests/test_r2_legacy_history.py`, CASE 5 · 6 · 7).

### 4. Sự cố production được chữa — `CODE_PATH_FAILURE`, không phải mất dữ liệu

Production có ĐỦ cả hai bản nhập. Khi cờ "đang xem" trỏ vào workbook 2025,
mọi kỳ 2026 biến mất, vì `available_periods()` / `query_summary()` /
`query_monthly_reference()` cuối cùng đều đọc **một bản nhập được chọn**.
Dữ liệu không thiếu ⟹ **KHÔNG nhập lại** để "chữa", và **KHÔNG** chạy lại
lịch sử qua pipeline hiện hành.

### 5. Cơ chế — bộ giải nguồn THEO KỲ, ở tầng truy vấn

`LegacyRepository._history_sources_by_year()` dựng bản đồ `{năm → bản nhập}`
từ bằng chứng THẬT trên cả ba bảng sự kiện (Summary, DataChart tháng,
DataChart ngày), theo hai bậc:

1. `AUTHORITATIVE_YEAR` — workbook một năm độc lập (`DEC-178`);
2. `WORKBOOK_SNAPSHOT` — workbook năm hiện hành, cho chính năm của nó.

Mọi hàm đọc lịch sử đi qua bản đồ đó. `SCHEMA_CHANGE_REQUIRED = NO`:
không bảng mới, không cột mới, không kho dữ liệu mới, không kiến trúc
đa-nguồn tổng quát.

### 6. Nhập nhằng — FAIL LOUD, không thay một heuristic bằng heuristic khác

Hai bản nhập cùng đủ tư cách cho MỘT năm ⟹ `LegacyHistoryAmbiguityError`
(HTTP 409 kèm câu nói rõ năm nào, những bản nhập nào). **Không** chọn "mới
nhất", "cũ nhất", "đang xem", "thứ tự nhập" hay "sắp tên file". Không có
khái niệm "current" nào được dựng lại dưới một cái tên khác. Không có bằng
chứng cho một kỳ vẫn là *"chưa có dữ liệu"* như hợp đồng cũ, KHÔNG phải 0.

### 7. Không thêm nguồn legacy nào nữa

Đây là các nguồn lịch sử CUỐI CÙNG. Giao diện bình thường vì vậy không còn
ô "NHẬP BẢN LEGACY" và không còn luồng thêm/thay/chọn Legacy. Endpoint
`POST /du-lieu/legacy` được GIỮ cho tương thích/vận hành — siết nó thành
lỗi cứng sẽ phải đụng tới toàn bộ đường nhập đang có test, tức mở rộng phạm
vi mà không thêm an toàn nào cho đường sản phẩm (đường đó đã bịt). Luồng số
mới "CHẠY BÁO CÁO MỚI" **không** bị đụng tới.

### 8. Provenance CÓ, bộ chọn KHÔNG

```text
PROVENANCE                = YES
SOURCE_SELECTION_WORKFLOW = NO
```

`/du-lieu` và `/lich-su` vẫn ghi rõ số 2025 đọc từ file nào, số 2026 đọc từ
file nào, kèm nhãn thẩm quyền — để đối chiếu được. Không dòng nào trong đó
bấm được để đổi nguồn.

### 9. Ranh giới — điều quyết định này KHÔNG cho phép

Không đổi bất kỳ công thức nghiệp vụ nào (Tổng bán, chiết khấu, KPI Profit,
DS quy đổi, tỉ lệ quy đổi, đếm đơn, số lượng SP đủ điều kiện, PP coverage,
gán nhân viên, Product Identity, cách hiển thị tiền của R1, thanh tab chính
của R1). Không mở ánh xạ *người bán lịch sử ↔ nhân viên hiện hành*: MoM bắc
qua ranh giới cho MỘT nhân viên vẫn KHÔNG được triển khai, vì tổng tháng của
sổ cũ là số của CẢ CÔNG TY (`DEC-180` §4 giữ nguyên). Không dựng framework
đa nguồn, không auth/roles, không engine phân tích mới, không kho dữ liệu.

### 10. `/` — kỳ mới nhất của dòng thời gian báo cáo

Kỳ mới nhất của Current Engine vẫn LUÔN thắng (production: các kỳ số mới đều
mới hơn 08/2026 ⟹ hành vi R1 không đổi). Chỉ khi KHÔNG có kỳ số mới nào mà
lịch sử lại có kỳ, `/` mở kỳ lịch sử mới nhất — dùng LẠI bộ giải nguồn của
R2, không dựng engine hợp nhất hai nguồn.

Impact:
`BUSINESS_FORMULAS_CHANGED = NO`. `BUSINESS_TOTALS_CHANGED = NO`.
`SCHEMA_CHANGE_REQUIRED = NO`. Thay đổi nằm ở: bộ giải nguồn theo kỳ trong
`app/web/history_store.py`, ngữ cảnh provenance ở `app/web/legacy_presentation.py`,
điểm ráp + xử lý 409 + landing ở `app/web/server.py`, và bốn template legacy.
Một route bị gỡ: `POST /du-lieu/legacy/<id>/chon` (chính luồng bị bác).

Evidence:
`R2_FOCUSED = 34 passed` (`tests/test_r2_legacy_history.py`);
`FULL_TEST_SUITE = 2355 passed, 11 skipped` (baseline trước phiên
`2321 passed, 11 skipped`).
Ba phép thử đột biến chứng minh khẳng định có răng: dựng lại cổng
`is_current` ⟹ 14 FAIL; cho bản `Summary 2025` nhúng thắng nguồn chuẩn ⟹
8 FAIL; bỏ hệ số kVND→VND ⟹ 3 FAIL.

Can Revisit After:
Chỉ mở lại khái niệm "nhiều nguồn lịch sử để chọn" khi chính chủ dự án ra
một quyết định mới bác `DEC-181`. Điều KHÔNG mở lại: `is_current` làm thẩm
quyền nghiệp vụ, bản sao nhúng ghi đè nguồn chuẩn, chọn thầm lặng một trong
hai nguồn ngang nhau, và chạy lại lịch sử qua pipeline hiện hành.

## DEC-182

Title:
OWNER AUTHORITY CORRECTION — DEC-181 §7 sai: gỡ UI KHÔNG đủ để khóa
`LEGACY_HISTORY`. Write boundary của `POST /du-lieu/legacy` phải tự khóa

Date:
2026-09-05

Task:
R2-B01 — LOCK LEGACY_HISTORY WRITE BOUNDARY (bounded blocking repair theo
đúng MỘT finding BLOCKING của Independent Review R2, tại `BASE_HEAD =
08cf42ceb4399fc1cc87b41f748b95bd9e63887f`).

Authority:
**`OWNER_DECISION` — FROZEN.** Chủ dự án xác nhận trực tiếp: đây không phải
suy luận của phiên làm việc.

Supersedes:
`DEC-181` §7 — **CHỈ đúng phần rationale** ("siết `POST /du-lieu/legacy`
thành lỗi cứng ... đường đó đã bịt"). Toàn bộ phần còn lại của `DEC-181`
(§1–§6, §8–§10) và các quyết định khác giữ NGUYÊN VĂN, không mở lại.
Bản ghi gốc của `DEC-181` KHÔNG bị sửa tại chỗ — đúng như governance
(`CLAUDE.md` → "Ngôn Ngữ Nội Dung") yêu cầu với lịch sử coi là bất biến.

### 1. Điều bị bác

`DEC-181` §7 lập luận: gỡ ô "NHẬP BẢN LEGACY" khỏi `/du-lieu` là đủ để niêm
phong đường sản phẩm ("đường đó đã bịt"), nên giữ nguyên hành vi tạo import
của `POST /du-lieu/legacy` không thêm rủi ro nào — chỉ UI bị gỡ, route vẫn
hoạt động bình thường phía sau.

Independent Review R2 (finding BLOCKING, E2) chứng minh lập luận đó **SAI**:
route vẫn ĐĂNG KÝ và vẫn nhận `POST` trực tiếp qua HTTP (curl, script, form
dựng tay ngoài UI bình thường) — gỡ nút bấm trên `/du-lieu` không chặn được
đường đó. Một workbook 2026 hợp lệ về định dạng nhưng khác fingerprint bản
đã có vẫn tạo được import thứ BA qua đúng route production, phá thẳng bất
biến "chỉ đúng hai nguồn cố định" mà chính `DEC-181` §1 công bố. **UI removal
KHÔNG đồng nghĩa write boundary removal.**

### 2. Thẩm quyền mới

```text
UI_REMOVAL_SUFFICIENT                 = NO
LEGACY_IMPORT_WRITE_BOUNDARY          = LOCKED — thực thi tại chính route,
                                        không chỉ ở UI
THIRD_LEGACY_SOURCE_ALLOWED           = NO — dù qua UI hay HTTP trực tiếp
LEGACY_HISTORY_FIXED_SOURCE_INVARIANT = ENFORCED_IN_APPLICATION
```

`POST /du-lieu/legacy` **GIỮ ĐĂNG KÝ** (đúng tinh thần tương thích/vận hành
mà `DEC-181` §7 dự định) nhưng từ chối **MỌI** request bằng HTTP 409 —
"Dữ liệu lịch sử đã khóa. Hệ thống chỉ sử dụng nguồn lịch sử 2025 và
01-08/2026 đã được chốt." — **TRƯỚC** khi đọc file, parse workbook, hay chạm
`LegacyRepository`: không `create_import()`, không DB write, không đổi
`is_current`, không side effect nào khác. Đây là một **RÀNG BUỘC NGHIỆP VỤ**
(business invariant do chủ dự án ra), **không phải** access-control/auth/
CSRF — không thêm cơ chế xác thực/phân quyền nào cho route này.

`LegacyRepository.create_import()` ở tầng repository **không** bị vô hiệu
hóa toàn cục — vẫn cần cho test/fixture/dựng dữ liệu khởi tạo (`DEC-181` §7
đã lường trước nhu cầu này cho mục đích vận hành nội bộ). Quyết định này chỉ
khóa **đường ghi sản xuất qua HTTP**, không phải toàn bộ tầng repository.

### 3. Không mở lại

Không mở lại bất kỳ semantics nào khác của `DEC-181` (§1–§6, §8–§10 giữ
nguyên: một nguồn logic hai file provenance, `is_current` không còn là thẩm
quyền, bộ giải nguồn theo kỳ, fail-loud khi nhập nhằng, không ánh xạ nhân
viên lịch sử ↔ hiện hành, `/` ưu tiên kỳ Current Engine). Không đổi resolver
nguồn (`LegacyRepository._history_sources_by_year()`), không đổi công thức
nghiệp vụ, không thêm UI nào ngoài phạm vi đã có.

Impact:
Sửa `app/web/server.py::import_legacy()` — route trả `409` trước mọi side
effect thay vì parse + `create_import()`. `BUSINESS_FORMULAS_CHANGED = NO`.
`BUSINESS_TOTALS_CHANGED = NO`. `R2_RESOLVER_CHANGED = NO`.
`SCHEMA_CHANGE_REQUIRED = NO`. Test seed nội bộ (fixtures của
`tests/test_web_legacy_routes.py`, `tests/test_web_pipeline_analytics.py`,
`tests/test_phb04_legacy_reference.py`) chuyển từ seed qua HTTP
(`client.post("/du-lieu/legacy", ...)`) sang seed thẳng qua
`LegacyRepository.create_import()` — route production không còn đường nào
để test "nhập qua HTTP" theo đúng thẩm quyền mới; các test đã sửa để seed
qua đúng tầng repository mà `DEC-181` §7 xác nhận vẫn cần được giữ.

Evidence:
Regression test tái hiện đúng E2 (BLOCKING) của Independent Review R2 —
`tests/test_r2_legacy_history.py::test_r2_b01_post_legacy_cannot_create_a_third_eligible_legacy_source`
và `::test_r2_b01_can_create_third_eligible_source_via_http_is_no`, đi qua
route Flask ĐÃ ĐĂNG KÝ (không phải helper nội bộ). Đếm import trước/sau một
`POST /du-lieu/legacy` với workbook hợp lệ nhưng khác fingerprint:
`IMPORT_COUNT_BEFORE = 2`, `IMPORT_COUNT_AFTER = 2`. Số liệu suite đầy đủ
(R2 focused / full suite / mutation check) nằm ở bản ghi session tương ứng
của repair R2-B01.

Can Revisit After:
Chỉ khi chính chủ dự án ra một quyết định mới cho phép một nguồn Legacy thứ
ba, hoặc thay write boundary này bằng một cơ chế khác (vd. một quy trình
nhập lịch sử có kiểm soát riêng) — không phải suy luận của một phiên làm
việc. Không mở lại `DEC-181` §7 rationale cũ ("gỡ UI là đủ").
