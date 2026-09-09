# ADR-111 — Cờ vắng mặt có hiệu lực trên dữ liệu hiệu lực; IMEI mở đúng một route; thương hiệu là thẩm quyền của Tracking

## Status
Accepted

## Date
2026-09-08

## Context

R5 đổi ba ranh giới mà các quyết định trước đã vẽ ra một cách có chủ đích.
Ba cái đó nằm chung một ADR vì chúng chia một tính chất: mỗi cái đổi **ai có
thẩm quyền nói một câu**, chứ không chỉ đổi một công thức hay một màn hình.
Ba quyết định chiến thuật tương ứng nằm ở `DEC-202` §1–4, §10 và §8–9.

### 1. Cờ vắng mặt từng KHÔNG BAO GIỜ chạm dữ liệu hiệu lực

`TASK-PRA-002` slice B dựng một bất biến an toàn và nói nó ra thành lời trong
chính docstring của `SnapshotRepository.confirm_coverage`: *"Thứ hàm này KHÔNG
làm, và không bao giờ được làm: xoá dòng, đổi con trỏ hiện hành, đổi bất kỳ
con số analytics nào."* Bất biến ấy đúng tuyệt đối cho câu hỏi mà slice B trả
lời — *hệ thống có được tự kết luận một đơn đã biến mất không?* — và câu trả
lời là KHÔNG, mãi mãi.

Nhưng slice B cũng dựng một nút: *"xác nhận sổ này đầy đủ cho khoảng ngày"*.
Sau khi người dùng bấm nó, hệ thống có thứ nó nói là nó còn thiếu — một lời
khẳng định tường minh của con người về phạm vi — và vẫn không làm gì với nó.
Doanh thu của một đơn đã huỷ tiếp tục nằm trong tổng, và người dùng không có
cách nào khác để nói điều họ vừa nói.

### 2. IMEI từng bị cấm khỏi mọi query nghiệp vụ

`governance/product/17_DATA_GOVERNANCE_PRIVACY.md` và hàng rào PII của
`business_queries` liệt kê `imei` cùng `note_raw`/`employee_raw` là những cột
không có đường nào ra tới một trang chỉ tiêu. Hàng rào ấy được canh bằng chính
mã nguồn (`tests/test_business_boundaries.py`), không bằng một câu văn — và đó
là lý do nó đã giữ được.

Nhân viên thì cần mã máy để đối chiếu máy đã bán với máy trên phiếu, và họ
đang mở sổ Excel song song để làm việc đó.

### 3. Thương hiệu chưa có nguồn nào

`PHB-06` đo lại và ghi: `CanonicalProductIdentity`, `TrackingCatalogRow`,
`PublicPurchaseIdentityRow`, `order_line_result_version` và sổ cũ — KHÔNG cái
nào có trường thương hiệu. `canonical_brand()` vì thế trả `None` cho mọi danh
tính, và `brand_identity.py` nói thẳng bốn cách dựng một thẩm quyền thương
hiệu thứ hai đều bị cấm: bảng ánh xạ riêng, so chuỗi con, so gần đúng, và rút
thương hiệu từ tên hàng.

Nhưng Tracking CÓ bằng chứng: `board/<mã>/cat` là ngành hàng do người của
Tracking tự tay xếp, và nó mang tên hãng ("Tivi Sony"). Bằng chứng ấy chưa bao
giờ rời khỏi Tracking, vì `cat` không có tên trong danh sách trắng của
`/api/xuat/board`.

## Decision

### 1. Một cờ vắng mặt CÓ hiệu lực — nhưng chỉ khi con người đã nói

`REMOVED_IN_SOURCE_CANDIDATE` phát sinh từ một snapshot `CONFIRMED_COMPLETE`
và còn hiệu lực TẠM LOẠI dòng khỏi dữ liệu hiệu lực.
`NOT_SEEN_IN_LATEST_SNAPSHOT` của một sổ chưa xác nhận KHÔNG đổi một đồng nào.

Bất biến của slice B không bị phá — nó được đọc đúng nghĩa của nó. Điều slice
B cấm là *hệ thống tự kết luận*; ở đây kết luận đến từ một hành động tường
minh của con người, và slice B chính là bên dựng cái nút để họ nói.

Ba tính chất giữ cho nó không thành một lệnh xoá:

```text
loại xảy ra LÚC ĐỌC     không hard-delete, không đổi con trỏ, không migration
đảo ngược TỰ ĐỘNG       "còn hiệu lực" tính lại từ lịch sử membership mỗi
                        lần đọc — dòng quay lại thì tổng quay lại
phạm vi ĐÚNG bằng       ngoài khoảng đã xác nhận thì không đụng tới, kể cả
lời người dùng nói      khi sổ ấy có dữ liệu ở đó
```

### 2. IMEI mở trên ĐÚNG một route, và phạm vi đó đọc được từ mã nguồn

Mã máy được đọc và hiển thị ở bảng kê của tab nhân viên. Không trang chỉ tiêu
nào, không bản xuất nào, không trang snapshot nào, không dòng nhật ký hay
telemetry nào.

Ranh giới được thi hành bằng CẤU TRÚC, không bằng lời hứa:

```text
app/web/workspace_imei.py     cánh cửa DUY NHẤT, một module riêng
app/web/business_queries.py   VẪN không biết `imei` tồn tại
tests/test_r5_imei_boundary.py canh cả hai chiều: chỉ `server.py` import cánh
                              cửa đó, và một mã máy CÓ THẬT không xuất hiện
                              trên bất kỳ trang nào khác
```

Vì sao một module riêng thay vì thêm một cột: thêm `imei` vào `_COLUMNS` của
`business_queries` sẽ đưa nó vào MỌI trang dùng `PeriodData` — tổng hợp, cơ
cấu, thương hiệu, đánh giá, export. Không trang nào hiện nó hôm nay, nhưng tất
cả sẽ MANG nó trong bộ nhớ, và trang tiếp theo ai đó viết sẽ có nó trong tay
mà không phải xin phép ai.

### 3. Thương hiệu và model là thẩm quyền của TRACKING

Tracking chuẩn hoá `model_label` và `brand` từ dữ liệu nhóm/tên đã có, và xuất
chúng qua danh sách trắng của `/api/xuat/board`. Reports là bên TIÊU THỤ:
không parser, không bảng brand riêng, không suy từ `product_raw`.

Đây là cùng hình dạng mà `ADR-107` đã chọn cho Public Purchase, và vì cùng một
lý do: bằng chứng nằm ở đâu thì thẩm quyền nằm ở đó. `cat` — thứ mang nhiều
bằng chứng nhất về hãng — không được phép rời khỏi Tracking, nên phép chuẩn
hoá phải xảy ra trước khi dữ liệu đi qua ranh giới.

Tracking ghép theo một danh sách hãng ĐÓNG và ghép NGUYÊN TỪ; khớp nhiều hơn
một hãng ⟹ `null`. `null` là một câu trả lời hợp lệ, không phải một khiếm
khuyết cần vá: sai theo hướng "dám quá" tốn kém hơn hẳn hướng ngược lại — một
nhãn hãng đoán ra cộng doanh thu thật vào sai thương hiệu, trên một màn hình
trông hoàn toàn bình thường.

Phía Reports, `PHB-06` mở lại qua đúng đường thứ hai mà `PHB-06 §4` để ngỏ:
một **read model canonical** (`catalog_display.brand_source`) cắm vào tham số
`brand_source` đã có sẵn — KHÔNG phải một trường mới trên
`CanonicalProductIdentity`. `INV-18` bắt so sánh danh tính bằng đủ tuple, nên
một trường hiển thị đặt ở đó sẽ làm hai danh tính cùng mã khác hãng thành hai
danh tính KHÁC NHAU, và một mapping đã confirm có thể trượt khỏi mục tiêu của
nó vì một lần Tracking sửa tên hãng.

Hai trường mới KHÔNG tham gia nhận diện: `TrackingCatalogSnapshot._match_field`
không đọc chúng. Ghép thêm bằng hãng sẽ làm mọi dòng Sony khớp với nhau
(`INV-13`/`INV-21`).

## Consequences

**Tích cực.** Con số cuối tháng phản ánh đúng điều người dùng đã khẳng định về
sổ của họ. Nhân viên đối chiếu máy ngay trên màn hình vận hành thay vì mở
Excel song song. Báo cáo thương hiệu có nguồn chính danh đầu tiên, và nó đến
từ đúng hệ thống sở hữu bằng chứng.

**Tiêu cực, và đã cân nhắc.** Bán kính ảnh hưởng của Reports tăng một bậc
(`3/5` → `4/5`): một lỗi ở tầng loại dòng làm tổng SAI THEO HƯỚNG THẤP HƠN, và
không ai đi tìm số tiền mình không biết là mình đang thiếu. Đây là lý do
`R5` được cấp `HIGH` effective risk và hai repair cycle.

Quyết định 2 là quyết định khó đảo nhất, và khó theo nghĩa chính sách chứ
không phải kỹ thuật: một khi mã máy đã hiện trên màn hình vận hành, rút nó lại
là một quyết định về quyền truy cập, không phải một lần xoá code.

Quyết định 3 tạo một phụ thuộc hợp đồng mới giữa hai repo. Nó được làm nhẹ
nhất có thể: hai trường TÙY CHỌN, artifact cũ vẫn đọc được, và Reports xử lý
`null` bằng đúng đường mà nó đã xử lý "chưa có thương hiệu" từ `PHB-06`.

## Alternatives considered

**Ghi `REMOVED_IN_SOURCE_CANDIDATE` thành một lần xoá thật.** Bị loại: nó phá
append-only, không đảo ngược được khi dòng quay lại, và cần một migration —
brief nói rõ ưu tiên không thêm migration.

**Một cột `is_removed` trên `order_line_current`.** Bị loại: nó biến một trạng
thái DẪN XUẤT (tính được từ cờ + lịch sử membership) thành một trạng thái phải
duy trì, và mở ra khả năng cột ấy trôi khỏi bảng cờ.

**Thêm `imei` vào `business_queries._COLUMNS` rồi chỉ render ở một chỗ.** Bị
loại: phạm vi khi ấy là một quy ước, không phải một tính chất — xem §2.

**Thêm `brand` vào `CanonicalProductIdentity`.** Bị loại vì `INV-18` — xem §3.

**Để Reports tự rút hãng từ `product_raw`.** Bị loại: đây đúng là một trong
bốn cách mà `PHB-06 §3`/`BR-02`/`BR-10` cấm, và `D-04` (`DEC-147` §4) ghi rằng
Tracking đã thử rút mã từ câu tên hàng bằng máy và BỎ HẲN vì sai trên tài sản
thật.

## References

- `PROJECT/PROJECT_DECISIONS.md` → `DEC-202`
- `docs/tasks/R5-doi-soat-so-bieu-do-thao-tac-danh-tinh.md`
- `docs/sessions/S134-r5-doi-soat-va-danh-tinh.md`
- `docs/tasks/TASK-PRA-002-pipeline-persistence-reconciliation.md` (mục 7.3, bước R)
- `docs/adr/ADR-107-public-purchase-authority-in-tracking.md` (cùng hình dạng thẩm quyền)
- `governance/product/17_DATA_GOVERNANCE_PRIVACY.md`
