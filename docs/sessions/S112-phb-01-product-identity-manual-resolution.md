# S112 — PHB-01 Product Identity Manual Resolution V1 (implementation)

Mode: IMPLEMENTATION (vertical PHB-01, contract PHB-PI-001).
Có sửa production code ở CẢ HAI repo (Reports + Tracking — §5 của contract
cho phép tường minh). Không migration · không schema mới · không service/queue
mới · không deploy · không mở PHB-02.

## 1. Xác Minh Thẩm Quyền (đầu phiên)

```text
REPO                   = hoangvinhkta-creator/Reports
CANONICAL_BRANCH       = claude/extract-upload-repo-gq2ws4  (git remote show origin)
SESSION_BRANCH         = claude/phb-01-product-identity-manual-o28bsn
HEAD_BEFORE            = bc9af2820b785330c3e5688dece9bce6775281f1
BEHIND/AHEAD canonical = 0 / 0  → ĐỒNG BỘ
WORKING_TREE           = sạch (không có công việc dở của phiên khác)

REPO                   = hoangvinhkta-creator/Tracking
DEFAULT_BRANCH         = main
HEAD_BEFORE            = 9ede079413065ae0beef2c3ae005d332d8d92eca
SESSION_BRANCH         = claude/phb-01-product-identity-manual-o28bsn
```

Baseline test TRƯỚC khi sửa dòng nào:

```text
Reports  : 2032 passed, 11 skipped
Tracking : 58 bộ · 2500 đạt · 0 hỏng · 2 bỏ qua
```

Ghi chú môi trường: lần chạy pytest đầu tiên đỏ đúng MỘT bài
(`TestG25GoldenBaselineUnchanged`, `fatal: bad object 740f396a…`). Nguyên
nhân là clone NÔNG của môi trường phiên, không phải mã: sau
`git fetch --depth=2000` bài này xanh. Không sửa gì để nó xanh.

### Không tìm thấy contract PHB-PI-001 trong repo

`grep -ri "PHB"` trên `docs/`, `PROJECT/`, `governance/` → 0 kết quả. Contract
PHB-PI-001 và các quyết định D1/D2/D8 chỉ tồn tại trong prompt của phiên
này, chưa từng được commit. Đây KHÔNG phải authority mismatch (không có bản
ghi nào trong repo mâu thuẫn với nó), nên phiên tiếp tục và ghi lại nguyên
văn các quyết định đã THỰC SỰ triển khai ở mục 4 — để phiên sau đọc được
chúng từ repo thay vì từ trí nhớ.

## 2. Vertical đã triển khai

Luồng nghiệp vụ E2E mục tiêu, và phần nào đã có mã chạy được:

```text
Reports: dòng bán chưa định danh
  → gộp theo KHOÁ inv.map (UNIQUE)                    ✅ S112
  → bản xuất cho người vận hành (sheet Excel)          ✅ S112
  → Tracking: nhập theo TÊN HÀNG (không qua file tồn)  ✅ S112
  → Owner phân loại                                    ✅ S112 (UI + picker cũ)
  → ghi authoritative /inv/map/<khoá>                  ✅ S112 (ghi hẹp)
  → Reports chạy lại → identity resolved               ✅ S112 (test F)
  → PP @ sale_date nếu có                              (không đổi — đường cũ)
  → KPI tiếp tục nếu có bằng chứng PP                  (không đổi — đường cũ)
```

Chưa làm (đúng phạm vi): deploy, và một lượt E2E trên production thật với
một câu tên hàng chưa định danh THẬT — xem mục 7.

## 3. Files đã đổi

### Reports (`claude/phb-01-product-identity-manual-o28bsn`)

```text
app/modules/pricing/resolution/unresolved_descriptions.py   MỚI  164 dòng
app/modules/pricing/resolution/composition.py               +17
app/modules/pricing/resolution/__init__.py                  +8
app/modules/exporting/excel_exporter.py                     +70
app/owner_usability.py                                      +19/-3
app/web/server.py                                           +40/-6
app/web/templates/index.html                                +6
tools/tracking/capture_inv_map.py                           +33/-9
tools/tracking/live_pull.py                                 +54/-19
tests/test_phb01_unresolved_descriptions.py                 MỚI  360 dòng
tests/test_demo.py, test_tracking_inv_map_capture.py,
tests/test_tracking_live_pull.py                            cập nhật hợp đồng
```

### Tracking (`claude/phb-01-product-identity-manual-o28bsn`)

```text
public/index.html            màn "Phân loại theo tên hàng" + ghi hẹp /inv
                             + invKeyOfName() + APP_BUILD b123 → b124
kiem/phan-loai-ten-hang.js   MỚI — 58 khẳng định
kiem/cot-ton-vongdoi.js, kiem/day-ton-sheet.js,
kiem/lich-su-gia-nhap.js     cắt thêm `invKeyOfName` (chúng eval mã thật)
```

## 4. Quyết định đã THỰC SỰ triển khai

### D1 — authority fetch failure phải FAIL LOUD

Lỗ hổng tìm thấy, nguyên văn trong mã cũ (`tools/tracking/live_pull.py`):
`inv_map` FAILED "không chặn lần chạy, chỉ làm `tracking_inv_map=None`". Hệ
quả không dừng ở "thiếu một nguồn phụ": không có `inv.map` thì MỌI câu tên
hàng kế toán trả `PENDING_PRODUCT`, và người vận hành đọc được đúng một câu
— "sản phẩm chưa được phân loại". `inv_map_status` có được ghi vào evidence
nhưng KHÔNG hiển thị ở đâu cả (`tracking_evidence` chỉ được lưu, không render).

Đã sửa, tách đúng hai trạng thái:

| Sự kiện | Trước | Sau |
|---|---|---|
| `{"map": {}}` đúng hợp đồng | `FAILED/EMPTY_SOURCE_NOT_ASSERTABLE` | `COMPLETE`, 0 mục, `empty_reason=EMPTY_VALID_AUTHORITY` — chạy tiếp |
| mất mạng / 403 / 502 | `FAILED` → `None` → chạy tiếp | `TrackingUnavailableError` → 503, không sinh report |
| payload sai hợp đồng | `FAILED` → `None` → chạy tiếp | `TrackingUnavailableError` → 503 |
| payload TRỐNG (`None`/`{}`) | `FAILED/EMPTY_SOURCE_NOT_ASSERTABLE` | KHÔNG ĐỔI (vẫn không assert được) |

Lý do S068 cho `EMPTY_SOURCE_NOT_ASSERTABLE` ("payload trống trông giống sai
URL/sai node") vẫn ĐÚNG cho payload trống thật và được giữ nguyên. Nó không
còn đúng cho `{"map": {}}`: hợp đồng Worker (`src/index.js`, nhánh `inv_map`)
trả `502` khi đọc hỏng, `404` khi sai node, và `200 {"map": {}}` CHỈ khi
nhánh `inv/map` chưa tồn tại — cộng với kiểm hình dạng top-level đã có sẵn ở
`_entries_from_payload()`, một `{"map": {}}` lọt tới đây là một KHẲNG ĐỊNH
của authority.

Trang web có câu báo lỗi RIÊNG cho node `inv_map` (không dùng chung câu với
hai node giá): nói rõ báo cáo dừng CÓ CHỦ ĐÍCH và đây không phải kết luận
"sản phẩm chưa được phân loại".

Đường local Owner (`select_latest_valid_captures`) cũng đổi: KHÔNG có file
capture inv.map nào = "chưa nối" (giữ nguyên, không chặn); CÓ file mà không
file nào COMPLETE = lỗi loud.

### D2 — kiến trúc manual resolution

Đã dùng: Reports xuất tên hàng chưa định danh + Tracking nhập THEO TÊN HÀNG.
KHÔNG dùng "Tải file tồn" làm cửa phân loại. Bằng chứng cho ranh giới toàn
vẹn dữ liệu, đọc trực tiếp trong `public/index.html`: `invImport()` →
`invApply()` ghi `rows`(số lượng)/`gia`/`lo`/`cong`/`congTay`, và `cong` là
giá công khai chảy sang cột Tồn của bảng giá → `tp/ton` → và từ đó
`purchase_price_history`. Màn mới không chạm một đường nào trong số đó
(`kiem/phan-loai-ten-hang.js` mục G quét đúng các tên hàm ấy).

Màn mới cho đúng HAI lựa chọn theo §5B: một mã đã có trên bảng giá, hoặc
`"-"`. Cố ý KHÔNG mang theo `__new` (thêm mã mới) của `invSetCls()`: mã mới ở
đó dựng từ `invCode()` trên tên hàng file tồn, còn câu tên hàng trên chứng
từ bán là văn xuôi kế toán — rút mã từ nó là đoán chữ.

### D8 — an toàn khi ghi phía Tracking

`saveInv()` cũ = `db.ref("inv").set(INV)`, ghi đè CẢ nhánh `/inv` bằng ảnh
chụp RAM lấy từ lúc `loadInv()`. **CHÍN chỗ gọi** — bản ghi đầu của phiên này
đếm "tám", review độc lập đếm lại từ `public/index.html` tại
`9ede079` và ra chín (các dòng 7007, 7015, 7171, 7227, 7234, 7328, 7398,
7554, 7562; định nghĩa ở 7018 không tính). Sửa số liệu, không đổi kết luận:
cả chín đều đã chuyển. Cảnh mất dữ liệu cụ thể: máy A mở tab lúc 9h → máy B
phân loại lúc 10h → máy A gõ một ô giá / tải file tồn / bấm "Qua ngày mới"
lúc 10h30 → mapping của máy B biến mất, không một lời báo, và bên Reports nó
hiện lại thành "chưa được phân loại".

Đã sửa toàn bộ chín chỗ sang `saveInvPaths()` (multi-path `update()`):

```text
phân loại (invSetCls, invUnCls, invTenSet)  → map/<khoá>          (+ 4 bảng
                                               giá của thẻ CHỈ KHI invRecalcAvg
                                               thật sự vừa chạy)
giá tồn kho (invSetGia, invAskSave)         → <thẻ>/gia|lo|cong|congTay
tải file tồn (invApply)                     → <thẻ>
qua ngày / hoàn tác / di trú giá            → cu, moi
```

`saveInv()` đã bỏ HẲN — không còn đường ghi đè cả nhánh nào tồn tại (bài kiểm
F quét bản phục vụ đã bỏ chú thích). Không đổi
`firebase-database.rules.json`: `/inv` đã có `.write` ở cấp node nên ghi hẹp
không cần luật mới. Không refactor Firebase ngoài chín chỗ này.

#### BLOCKING-01 — sửa sau review độc lập (Tracking `53993f1`)

Review độc lập tìm ra MỘT chỗ trượt trong chín chỗ trên: nhánh di trú (cloud)
của `loadInv()` ghi `Object.assign(invGiaDuong("cu"), invGiaDuong("moi"))` —
đúng bốn bảng giá mỗi thẻ — trong khi `invMigrateGia()` còn sửa `giaV2`,
`giaV3`, `tay` và `lotRequired`. Bảng ngay trên đã khai đúng hình dạng cần có
("di trú giá → cu, moi"); mã không khớp bảng.

Hệ quả: hai cờ ĐÃ-DI-TRÚ không bao giờ xuống được máy chủ, nên di trú chạy
lại ở MỖI lần nạp trang, và nhánh `!giaV3` của nó đặt `lo = {}`,
`cong = bản sao gia`, `congTay = {}` rồi ghi đè — giá lô và giá công khai
người dùng gõ tay biến mất sau mỗi lần mở trang, rồi chảy tiếp sang cột Tồn
bảng giá → `tp/ton` → `purchase_price_history`. Bản TRƯỚC D8 (`set` cả `/inv`)
không có lỗi này vì nó ghi luôn hai cờ, nên đây là hồi quy do PHB-01 gây ra.
Điều kiện kích hoạt hẹp: chỉ với thẻ chưa từng di trú (không có `giaV2`/
`giaV3` trên máy chủ).

Đã sửa đúng một dòng — đơn vị ghi của di trú là CẢ THẺ
(`{cu: INV.cu || null, moi: INV.moi || null}`), cùng lối `invUndoDay()`. Luật
ghi hẹp giữ nguyên: `map` vẫn không nằm trong danh sách đường ghi, và không
có lượt ghi đè cả `/inv` nào quay lại. Tám chỗ gọi còn lại không đổi một byte.

Bài kiểm mục H của `kiem/phan-loai-ten-hang.js` chạy CHÍNH `loadInv()` thật
(không tự dựng payload rồi tự canh payload mình vừa dựng): cờ xuống được máy
chủ, lần nạp trang sau không ghi gì nữa, giá người dùng gõ còn nguyên, `map`
không đụng — kèm đối chứng dựng lại hình dạng bốn-bảng cũ để chứng minh bài
kiểm bắt được bản lỗi. `once()` của kho giả nay trả BẢN SAO thay vì tham
chiếu sống: tham chiếu sống làm mọi lượt sửa trong RAM tự động "đã lưu" và
che đúng lớp lỗi này.

## 5. Bằng chứng

### E1 — bộ kiểm

```text
Reports  : 2044 passed, 11 skipped   (baseline 2032; +10 bài PHB-01, +2 bài
                                      đối chứng D1, -0 bài bị xoá)
Tracking : 59 bộ · 2572 đạt · 0 hỏng · 2 bỏ qua   (baseline 58 · 2500;
                                      2558 trước khi sửa BLOCKING-01,
                                      +14 khẳng định mục H)

Governance validators (không đổi so với baseline đã ghi ở PROJECT_PROGRESS):
  validate_structure          PASS
  validate_project_state      PASS
  validate_evidence           PASS (155 REQUIRED PASS)
  validate_task_completion    PASS (13 DONE task)
  validate_reference_integrity FAIL — ĐÚNG 3 reference REM-T06 đã biết
```

### E1 — đối chiếu chéo KHOÁ giữa hai repo

`inv_map_key()` (Reports, Python) vs `invKeyOfName()` (Tracking, JS), chạy
thật trên 10 câu gồm cả biên (dấu tiếng Việt, dấu phẩy trong tên hàng, câu
rỗng, câu 200 ký tự):

```text
'Tivi Samsung 75Q6FA'            -> 'N_TIVISAMSUNG75Q6FA'          KHỚP
'Tủ lạnh Funiki HR-T6185TDG'     -> 'N_TLNHFUNIKIHRT6185TDG'       KHỚP
'Máy giặt Samsung WW10DB7U34GBSV'-> 'N_MYGITSAMSUNGWW10DB7U34GBSV' KHỚP
'Phí vận chuyển'                 -> 'N_PHVNCHUYN'                  KHỚP
'Tivi 75" Q6FA, model 2026'      -> 'N_TIVI75Q6FAMODEL2026'        KHỚP
'A'×200                          -> 'N_' + 80 ký tự                KHỚP
''                               -> 'N_'                           KHỚP
'  a-b_c 1.2  '                  -> 'N_ABC12'                      KHỚP
'Đèn LED 9W'                     -> 'N_NLED9W'                     KHỚP
KẾT LUẬN: 10/10 KHỚP
```

### E1 — điều kiện nghiệm thu của contract §7

| | Kiểm | Kết quả |
|---|---|---|
| A | gộp: unresolved vào, đã resolve ra, trùng gộp xác định | PASS (`test_phb01_*` A) |
| B | xuất: một dòng/khoá, xác định, tương thích intake | PASS (`test_phb01_*` B) |
| C | intake: không đòi số lượng, không gọi đường file tồn | PASS (`phan-loai-ten-hang` B, G) |
| D | ghi `inv.map`; ignore/unclassify trung thực; ảnh chụp cũ không xoá mapping mới | PASS (`phan-loai-ten-hang` D, E + đối chứng lỗi cũ) |
| E | cách ly kinh tế (SL/lô/giá nhập/bình quân/tp-ton/PP history) | PASS (`phan-loai-ten-hang` D — so cả cây dữ liệu trừ nhánh `map`) |
| F | mapping mới tiêu thụ được qua hợp đồng authority ĐANG CÓ | PASS (`test_a_mapping_written_to_inv_map_resolves_the_identity_on_the_next_run`) |
| G | EMPTY_VALID ≠ FETCH_FAILED | PASS (`test_tracking_live_pull`, `test_tracking_inv_map_capture`) |
| H | regression: workflow tồn kho, API inv_map, resolver, PP/KPI | PASS SAU SỬA (2572 + 2044 đều xanh, hợp đồng `/api/xuat/inv_map` không đổi một byte). Review độc lập bác kết quả PASS đầu tiên của dòng này: BLOCKING-01 là một hồi quy thật ở nhánh di trú của `loadInv()` mà bộ kiểm lúc đó không canh. Đã sửa (Tracking `53993f1`) và đã có bài kiểm mục H chạy chính `loadInv()` thật. |

## 6. Findings (thông tin, KHÔNG sinh task — §9)

- **FIND-PHB01-01** — `tracking_evidence` (gồm `inv_map_status`) được lưu vào
  `run_registry` nhưng chưa render ở bất kỳ trang nào. Phiên này đã đóng phần
  nguy hiểm (authority hỏng nay chặn lần chạy), nhưng bằng chứng nguồn của
  một run vẫn chưa đọc được từ giao diện. Không chặn PHB-01.
- **FIND-PHB01-02** — `invGoiY()` bên Tracking xếp mã "gần giống" lên đầu
  picker bằng `includes()` hai chiều. Nó KHÔNG tự chọn (người vẫn phải bấm),
  nên không phải fuzzy authority; ghi lại vì nó là chỗ dễ bị hiểu nhầm thành
  matching tự động. Màn mới KHÔNG dùng gợi ý này.
- **FIND-PHB01-03** — luật khoá `"N_" + normCode[:80]` nay có BA bản: Reports
  (Python), Tracking `public/index.html`, Tracking `src/ton-sheet.js`. Cặp
  thứ hai đã có `kiem/day-ton-sheet.js` canh; cặp Reports↔Tracking mới chỉ
  được đối chiếu THỦ CÔNG trong phiên này (mục 5) vì hai repo không cùng CI.

## 7. Cổng còn lại trước khi PHB-01 = DONE

PHB-01 **CHƯA `DONE`**. Còn thiếu, đúng theo §10:

1. **Independent review** — chưa chạy. `PROJECT/REVIEW_BUDGET_LEDGER.md`
   KHÔNG được thêm mục cho `PHB-01` trong phiên này: chưa tiêu một repair
   cycle nào, và `effective_risk` của một root task là quyết định của Owner/
   người review, không phải của phiên implementation. Mở entry với một con số
   tự đặt là dựng ngân sách trên một giả định.
2. **Deploy an toàn** — chưa deploy bên nào. Tracking build từ `main` trên
   Cloudflare nên nhánh này KHÔNG tự lên production; Reports cũng chưa phát
   hành. Nghi thức phát hành của Tracking (tài liệu `QUY-CHUAN` trong repo
   Tracking, mục 4 — không phải file của repo này) còn nguyên:
   `npm test` xanh (đã có), `APP_BUILD` đã tăng (b124), rules KHÔNG đổi nên
   không cần Publish, và phép kiểm "đường dùng thật vẫn thông" (L2) phải chạy
   trên bản đã deploy.
3. **Một lượt E2E THẬT** với một câu tên hàng chưa định danh có thật, do
   Owner thực hiện: chạy báo cáo → mở sheet "Chưa định danh" → dán sang màn
   "Phân loại theo tên hàng" → chọn mã → chạy lại → mặt hàng đã nhận diện.

   Phiên này KHÔNG có egress tới `reports.tinphatcrm.com`/`price.tinphatcrm
   .com` (cùng policy denial đã ghi ở `CHECK-PRA002-15`/S093 và S110), nên
   không thể tự nghiệm thu — và cũng KHÔNG được giả lập kết quả production.

   `BH73622` KHÔNG được dùng làm oracle nghiệm thu: chưa có bằng chứng
   production nào chứng minh nguyên nhân gốc của nó là identity.

## 8. Trạng thái

```text
IMPLEMENTATION_STATUS = COMPLETE_FOR_REVIEW
SCOPE_DRIFT           = NO
PHB01_STATUS          = IMPLEMENTED (chưa DONE — xem mục 7)
```
