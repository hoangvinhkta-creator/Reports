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
