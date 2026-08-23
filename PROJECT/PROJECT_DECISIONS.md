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
chứa "ADS" hay không. Cài đặt bằng `default_lead_source: TINPHAT_ADS` cho
nhân viên đó trong `config/employees.yaml`, không phải một tỉ lệ hard-code.

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
