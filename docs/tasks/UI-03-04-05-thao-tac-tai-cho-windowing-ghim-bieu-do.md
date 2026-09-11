# UI-03 / UI-04 / UI-05 — Thao tác tại chỗ · Bảng theo trang · Ghim biểu đồ

## Metadata

Status:
IMPLEMENTED

Current Status Reason:
Ba lát dọc đã triển khai đầy đủ và có bằng chứng browser THẬT
(`22` bài Playwright mới trên Chromium, `19` bài pytest mới). Đã push
(`claude/ui-03-04-05-reports-px1u9l`) sau xác nhận trực tiếp bằng văn bản
của chủ dự án; đã tích hợp nhánh mặc định (`TASK-OWNER-UIUX-009` + `R7`,
merge trong lúc phiên chạy — xem `PROJECT/REVIEW_BUDGET_LEDGER.md` §"Đã
push, đã tích hợp…") và chạy lại toàn bộ test SAU tích hợp (`pytest 3680
passed`, `Playwright 35 passed`). CHƯA qua Independent Review, CHƯA merge
vào nhánh mặc định, CHƯA tạo PR (không ai yêu cầu). `CHECK-UI345-25`
(Independent Review) và `CHECK-UI345-26` (Owner nghiệm thu production) là
hai check REQUIRED duy nhất còn `NOT_TESTED`, và phiên này KHÔNG tự đóng
được cái nào. `CHECK-UI345-27` (Postgres concurrency) là một khoản NỢ
KIỂM CHỨNG kế thừa, `BLOCKED` vì thiếu biến môi trường — xem chi tiết ở
chính check đó.

Phase:
PHASE-03 — Giao diện vận hành (Release 2 — thao tác tại chỗ)

Task Mode:
MAJOR (ba tính năng, chạm cả route backend lẫn trạng thái frontend)

Primary Agent Tier:
Claude Code (S154)

Escalation Tier:
Owner

Difficulty:
3/5

Risk:
2/5

Blast Radius:
3/5 (`V4.1` §4 — chấm theo FAILURE PATH, không theo tên file):

```text
workspace_presentation.sheet_detail_groups()   (bản dựng DUY NHẤT của một
  └─ _workspace_table.html                      hàng bảng kê — xác minh bằng
       ├─ kinh_doanh_nhan_vien.html             grep: không nơi nào khác gọi)
       ├─ GET /api/v1/periods/<kỳ>/workspace
       └─ ba đường ghi (`phan-loai`/`ngoai-bang`/`loai-dong`) ở nhánh JSON
```

Nó DỪNG ở MÀN HÌNH. Bốn tính chất CẤU TẠO giữ nó không đi xa hơn:

1. **Không đường ghi mới nào.** Ba route ghi giữ NGUYÊN thân hàm và vẫn gọi
   nguyên `identity_gateway.confirm_identity`/`mark_out_of_catalog`/
   `store.exclude_line`/`store.restore_line`. Chỉ CÂU TRẢ LỜI rẽ đôi ở dòng
   cuối (`_workspace_answer`). Một lỗi ở đây không thể ghi sai một quyết
   định — nó chỉ có thể trả lời sai về một quyết định đã ghi đúng.
2. **Không phép tính mới nào.** `page_of_groups` chỉ CHỌN dòng; hàng TỔNG và
   dải KPI vẫn tính trên `scoped.details` của CẢ kỳ
   (`sheet_detail_totals`/`summary_strip`), không trên trang đã tải. Route
   phân rã `UI-05` gọi `dashboard_metrics.totals()` và
   `dashboard_presentation.money_cell()` — hai hàm mà trang phân tích đã
   dùng cho chính con số đang hiện trên biểu đồ.
3. **Không chạm export / chốt kỳ.** `sheet_detail_groups`/`sheet_detail_
   totals` chỉ phục vụ bảng kê nhân viên (xác minh bằng grep toàn repo);
   `business_export` và `period_lock` không gọi chúng. Khác hẳn lớp lỗi mà
   `R5` được chấm `HIGH` — ở đó quyền LOẠI dòng đổi được vân tay chốt kỳ và
   file Excel, tức lan ra NGOÀI một phiên trình duyệt.
4. **Không migration, không cột mới, không schema đổi.**

Vì sao `3/5` chứ không `2/5`: khác `UI-01/UI-02` (một cache DOM lệch với
nguồn đã đúng, tự khỏi khi tải lại), một lỗi trong `page_of_groups` hoặc
trong macro `detail_rows` là SAI Ở NGUỒN — nó GIẤU MẤT một dòng có thật
khỏi mắt Owner, ở mọi lần tải, và không tự khỏi. Vì sao không `4/5`: hàng
TỔNG vẫn là số toàn kỳ nên một dòng bị giấu tạo ra một MÂU THUẪN NHÌN THẤY
ĐƯỢC ngay trên cùng màn hình (tổng không khớp các dòng), và không con số
nào rời khỏi màn hình.

```
Effective Risk = max(Local Risk, Blast Radius) = max(2, 3) = 3/5 → MEDIUM
```

Golden Baseline KHÔNG được viện dẫn để hạ bậc (`V4.1` §4.1): không Golden
test nào phủ đường "một trang bảng kê" hay "vá một BH tại chỗ".

## 1. Bối cảnh

Ba lát dọc tiếp theo của "Roadmap cải thiện UI/API cho Reports trên Render"
(Release 2 — thao tác tại chỗ), nối trực tiếp `UI-01`/`UI-02` (panel sửa
đơn tại chỗ). Ba vấn đề chúng đóng, đo được trước khi sửa:

```text
UI-03  Mở bảng chọn phân loại, hoặc loại/khôi phục một dòng, đi qua lớp
       mảnh và thay CẢ `#app-content` — tức dựng lại toàn bộ bảng kê để
       hiện một hộp nhỏ cạnh con trỏ chuột, hoặc để đổi một dòng.
UI-04  Bảng kê dựng TRỌN VẸN trong một response: trên fixture 5.000 dòng
       là ~15 MB HTML và 5.002 hàng `<tr>` cho một màn hình chừng bốn mươi
       hàng (`scripts/stab01_baseline.py`, bản ghi `UI-01/UI-02`).
UI-05  Tooltip biểu đồ chỉ sống khi con trỏ còn ở trên điểm; không có
       đường nào xem được "ai đóng góp vào mốc này".
```

## 2. Scope Lock

TRONG phạm vi:
- ba route ghi của bảng kê — chỉ thêm nhánh trả lời JSON;
- một route đọc JSON cho trang bảng kê, một cho bảng chọn phân loại, một
  cho phân rã biểu đồ;
- `workspace_presentation`: tách `group_shades`, thêm `page_of_groups`/
  `groups_slice`/`cursor_for_order`;
- tách macro dựng bảng kê thành `_workspace_table.html`;
- `app.js`: ba khối client tương ứng;
- CSS cho hộp xác nhận neo và tooltip đã ghim.

NGOÀI phạm vi (KHÔNG chạm):
- công thức tài chính; `identity_gateway`, `line_identity`,
  `product_taxonomy`, `dashboard_metrics` ở tầng TÍNH TOÁN;
- hành vi `UI-01`/`UI-02` (panel sửa đơn, deep-link hash, idempotency);
- đường KHÔNG-JavaScript của mọi luồng đã có;
- `business_export`, `period_lock`, schema/migration.

## 3. Quyết định thiết kế đáng ghi lại

### 3.1 Trả HTML trong phong bì JSON, không trả dữ liệu thô

Ba route đọc mới trả về các mảnh HTML do CHÍNH macro của trang dựng. Đây đi
ngược một trực giác phổ biến ("API thì trả dữ liệu"), nên lý do được ghi
thành tài liệu: một hàng bảng kê mang `rowspan` theo số dòng của BH, ba cột
tuỳ chọn ẩn bằng CSS, bốn loại nhãn trạng thái, hai đường vào phân loại và
một ô nhập thuộc về một `<form>` đứng NGOÀI bảng. Ghép lại tất cả những thứ
đó bằng JavaScript là dựng một BẢN THỨ HAI của bảng kê, bằng một ngôn ngữ
khác, không test template nào soi tới — và bản thứ hai sẽ lệch khỏi bản thứ
nhất ở lần đầu ai đó thêm một cột, trong khi CẢ HAI đều "đúng" theo chính
nó. Con SỐ (`next_cursor`, `total_lines`, `affected`) vẫn là JSON thật.

### 3.2 Content negotiation trên CHÍNH route cũ, không route JSON song song

Ba đường GHI không có route mới. `_workspace_answer()` chọn giữa redirect và
JSON bằng `request.accept_mimetypes`. Một route JSON song song sẽ là một bản
thứ hai của cùng một quyết định nghiệp vụ, và hai bản lệch nhau ở đúng cái
nhánh không ai chạy thử.

### 3.3 Con trỏ phân trang là MÃ BH, không phải offset

Một offset trỏ sai ngay khi một dòng bị loại/khôi phục giữa hai lần tải —
đúng thao tác mà `UI-03` làm trên cùng màn hình này. Mã BH không còn tồn tại
⟹ trang dựng lại từ đầu sheet, không ném lỗi vào mặt người đang cuộn.

### 3.4 Nền xen kẽ là tính chất của CẢ sheet

`group_shades()` được tách ra khỏi `sheet_detail_groups()` và được CHÍNH nó
gọi lại, nên chỉ tồn tại MỘT luật xen kẽ. Một lát dựng riêng (`UI-03` vá một
BH, `UI-04` tải một trang) nhận bảng nền của cả sheet, không tự tính lại
trên lát của mình.

### 3.5 `UI-05` chỉ ghim được ở biểu đồ khai `data-breakdown`

Trang Báo cáo (`R5`) cố ý không khai: phạm vi của nó đọc bằng một bộ tham số
khác `_analysis_range()`, và gửi tham số của trang này sang route kia sẽ
phân rã một khoảng thời gian mà người dùng không hề chọn.

## 4. Completion Gate

Dùng `governance/core/TASK_COMPLETION_GATE_STANDARD.md` và
`governance/core/EVIDENCE_STANDARD.md`. Risk 3/5 ⟹ E1 bắt buộc cho mọi check
REQUIRED.

### UI-03

#### CHECK-UI345-01
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Bấm nút phân loại KHÔNG tải lại trang: biến toàn cục `window.__probe` còn
nguyên và `#app-content` vẫn là ĐÚNG phần tử DOM từ trước khi bấm (so bằng
handle, không so nội dung) — `tests/playwright/workspace-inline.spec.mjs`
::"mở bảng chọn phân loại không dựng lại bảng kê".

Executed By:
Claude Code (S154)

Timestamp:
2026-09-11

#### CHECK-UI345-02
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Một quyết định phân loại chạm BA BH khác nhau (fixture `SHARED_IDENTITY_
ORDERS` dựng riêng: cùng `product_raw`, khác `product_key`) được vá ĐỦ cả
ba — `workspace-inline.spec.mjs`::"một quyết định phân loại vá TẤT CẢ các
dòng dùng chung tên hàng". Phía server: payload trả đủ tập BH và mỗi BH kèm
HTML riêng — `tests/test_ui030405_workspace_json.py`::
`test_a_classification_answers_with_EVERY_affected_order`.

Executed By:
Claude Code (S154)

Timestamp:
2026-09-11

#### CHECK-UI345-03
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Fallback KHÔNG-JavaScript nguyên vẹn: lối vào phân loại vẫn là `<a href>`
thật mang `phan-loai=1`, và nút xác nhận vẫn thuộc một `<form method=post>`
trỏ tới `/kinh-doanh/nhan-vien/ngoai-bang` — `workspace-inline.spec.mjs`
::"không JavaScript: nút phân loại/loại vẫn là đường HTTP thật" (chạy trong
`browser.newContext({ javaScriptEnabled: false })`). Đường ghi vẫn trả
`302` + `da-luu=` cho client không xin JSON —
`test_the_browser_path_still_redirects_exactly_as_before`.

Executed By:
Claude Code (S154)

Timestamp:
2026-09-11

#### CHECK-UI345-04
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Loại/khôi phục đi qua MỘT hộp xác nhận NEO cạnh nút, nói hậu quả TRƯỚC khi
ghi; bấm HỦY không ghi gì — `workspace-inline.spec.mjs`::"loại một dòng:
hộp xác nhận nói hậu quả TRƯỚC…" và ::"HỦY trong hộp xác nhận không ghi gì".
Câu chữ do server viết (`EXCLUDE_CONFIRM_*`/`RESTORE_CONFIRM_*`).

Executed By:
Claude Code (S154)

Timestamp:
2026-09-11

#### CHECK-UI345-05
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Lỗi mạng KHÔNG tự gửi lại: route `loai-dong` bị `route.abort('failed')`,
hộp xác nhận Ở LẠI, nút bật lại, và sau `500 ms` chờ thêm vẫn ĐÚNG một lần
gửi; số dòng đã loại không đổi — `workspace-inline.spec.mjs`::"lỗi mạng:
hộp xác nhận Ở LẠI, KHÔNG tự gửi lại".

Executed By:
Claude Code (S154)

Timestamp:
2026-09-11

#### CHECK-UI345-06
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Khôi phục đưa dòng trở lại ĐÚNG khối BH (hàng đầu của khối vẫn là
`bh-head`), kể cả khi khối đã biến mất hoàn toàn khỏi bảng — server gửi hai
hàng xóm (`after`/`before`) để client CHÈN, không chỉ THAY —
`workspace-inline.spec.mjs`::"khôi phục đưa dòng trở lại ĐÚNG khối BH của
nó"; hình dạng payload: `test_a_classification_answers_with_EVERY_affected_
order`.

Executed By:
Claude Code (S154)

Timestamp:
2026-09-11

#### CHECK-UI345-07
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Mọi TỔNG bị ảnh hưởng do SERVER trả về, và nhãn `CHÍNH THỨC`/`CHƯA HOÀN
CHỈNH` đi LIỀN con số trong cùng một mảnh HTML (không tách ra để client tự
ghép) — `test_the_write_payload_carries_the_server_built_regions`.

Executed By:
Claude Code (S154)

Timestamp:
2026-09-11

#### CHECK-UI345-08
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Mở bảng chọn phân loại KHÔNG mang cả trang: response không chứa
`id="app-content"` và dưới `20 KB` —
`test_the_identify_route_returns_only_the_picker`. Đo thật:
`126` byte, `p50 160,7 ms` (`stab01_baseline --lines 5000`), so với
`319.736` byte / `p50 263,4 ms` của lượt fragment mà đường cũ dùng.

Executed By:
Claude Code (S154)

Timestamp:
2026-09-11

### UI-04

#### CHECK-UI345-09
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Route JSON đọc trang bảng kê TÁI DÙNG đúng `sheet_detail_groups` qua
`_workspace_context` (lời gọi DUY NHẤT trong sản phẩm — xác minh bằng grep
toàn repo), và `rows_html` mang đúng khoá ba phần của hàng —
`test_the_json_page_route_reuses_the_same_row_markup`.

Executed By:
Claude Code (S154)

Timestamp:
2026-09-11

#### CHECK-UI345-10
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Cắt theo RANH GIỚI BH, không cắt giữa các dòng của cùng một BH: hàm thuần
kiểm bằng dòng dựng tay (`test_a_page_stops_at_an_order_boundary_not_mid_
order`, `test_an_order_larger_than_the_whole_page_still_travels_whole`), và
trên trình duyệt sau 5 trang: không mã BH nào xuất hiện ở hai khối rời
nhau, mọi khối bắt đầu bằng `bh-head` —
`workspace-window.spec.mjs`::"một BH nhiều dòng KHÔNG bị cắt giữa hai
trang".

Executed By:
Claude Code (S154)

Timestamp:
2026-09-11

#### CHECK-UI345-11
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Trang đầu vẫn dựng SERVER-SIDE và fallback không-JS đi hết được bảng:
`XEM TIẾP` là `<a href="?...&tu=<mã BH>">` thật, trang kế là một trang KHÁC
và hai trang KHÔNG chồng nhau —
`workspace-window.spec.mjs`::"không JavaScript: XEM TIẾP là liên kết THẬT…"
(`javaScriptEnabled: false`) và
`test_the_no_js_more_link_really_serves_a_different_page`.

Executed By:
Claude Code (S154)

Timestamp:
2026-09-11

#### CHECK-UI345-12
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Trên fixture 5.000 dòng (sheet `noi-thanh` giữ trọn 5.000), số hàng
`<tr>` trong DOM LUÔN `<= 308` sau 8 lượt tải trang liên tiếp, và trang đầu
đã nằm trong ngân sách —
`workspace-window.spec.mjs`::"cuộn/tải nhiều trang: số <tr> trong DOM LUÔN
dưới ngân sách" + ::"trang đầu dựng ở SERVER và đã nằm trong ngân sách
DOM" + ::"fixture đúng là 5.000 dòng…".

Executed By:
Claude Code (S154)

Timestamp:
2026-09-11

#### CHECK-UI345-13
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Gỡ nhóm cũ KHÔNG làm mất vị trí cuộn: hàng đang nằm TRONG khung nhìn giữ
nguyên vị trí màn hình trong phạm vi `< 4 px` sau một lượt tải + gỡ —
`workspace-window.spec.mjs`::"gỡ nhóm cũ KHÔNG làm mất vị trí cuộn của
người đang xem".

Executed By:
Claude Code (S154)

Timestamp:
2026-09-11

#### CHECK-UI345-14
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
TỔNG hiển thị là số của TOÀN KỲ, không phải của phần đã tải: tải thêm một
trang KHÔNG làm `totals-sell`, `sales_revenue` hay số dòng của sheet nhúc
nhích — `workspace-window.spec.mjs`::"TỔNG hiển thị là số của TOÀN KỲ…".
Phía server: `detail_totals`/`summary_strip` đọc `scoped.details` của cả
kỳ, không đọc `page["details"]` (xem `_workspace_context`).

Executed By:
Claude Code (S154)

Timestamp:
2026-09-11

#### CHECK-UI345-15
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Con trỏ trỏ vào một BH đã biến mất KHÔNG ném lỗi mà dựng lại từ đầu sheet;
`limit` bị kẹp về trần — `test_a_cursor_pointing_at_a_vanished_order_
restarts_at_the_top`, `test_the_page_limit_is_clamped`,
`test_the_json_page_route_never_exceeds_the_hard_limit`.

Executed By:
Claude Code (S154)

Timestamp:
2026-09-11

#### CHECK-UI345-16
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Nền xen kẽ theo NGÀY giữ đúng nhịp của CẢ sheet trên một lát dựng riêng —
`test_shades_are_a_property_of_the_whole_sheet_not_of_a_slice`. Neo
`#bh-…` của cảnh báo chưa phân loại mang theo con trỏ trang chứa BH ấy —
`test_cursor_for_order_finds_the_page_holding_an_order`.

Executed By:
Claude Code (S154)

Timestamp:
2026-09-11

### UI-05

#### CHECK-UI345-17
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Đường RÊ CHUỘT cũ KHÔNG bị phá: hover vẫn hiện `.rev-tooltip` và nó KHÔNG
mang `is-pinned`; rời con trỏ thì nó biến mất —
`tests/playwright/chart-pin.spec.mjs`::"rê chuột vẫn hiện tooltip cũ, và nó
KHÔNG bị ghim".

Executed By:
Claude Code (S154)

Timestamp:
2026-09-11

#### CHECK-UI345-18
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Bấm ghim (con trỏ rời đi popover vẫn còn); bấm điểm KHÁC thay nội dung
NGAY TRONG popover đang ghim — so bằng HANDLE của chính phần tử tooltip,
không chỉ so nội dung, và popover không hề bị ẩn giữa chừng —
`chart-pin.spec.mjs`::"bấm một điểm GHIM tooltip…" và ::"bấm điểm KHÁC thay
nội dung NGAY TRONG popover đang ghim".

Executed By:
Claude Code (S154)

Timestamp:
2026-09-11

#### CHECK-UI345-19
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Giá trị cơ bản hiện NGAY từ dữ liệu đã có trong trình duyệt, KHÔNG chờ
request: với route phân rã bị trì hoãn 1,5 s, con số tiền của mốc đã có
trong popover trong vòng 1 s trong khi phần phân rã vẫn đang tải —
`chart-pin.spec.mjs`::"giá trị cơ bản hiện NGAY, trước khi phân rã về".

Executed By:
Claude Code (S154)

Timestamp:
2026-09-11

#### CHECK-UI345-20
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Response phân rã của điểm CŨ về muộn bị BỎ QUA: mốc thứ nhất bị trì hoãn
1,5 s, bấm mốc thứ nhất rồi mốc thứ hai, chờ QUA 2 s — popover vẫn hiện số
THẬT của mốc thứ hai và KHÔNG chứa số của mốc thứ nhất (hai số đọc thẳng từ
chính route, đã assert là khác nhau) —
`chart-pin.spec.mjs`::"phân rã của điểm CŨ về muộn thì bị BỎ QUA".

Executed By:
Claude Code (S154)

Timestamp:
2026-09-11

#### CHECK-UI345-21
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Bàn phím: điểm dữ liệu mang `tabindex="0"`/`role="button"` (do JS gắn, không
do template); Enter ghim; ←/→ sang điểm kế và ĐỔI NỘI DUNG tại chỗ; Tab từ
điểm đang ghim đi VÀO popover và quay lại được; Escape bỏ ghim và trả focus
— `chart-pin.spec.mjs`::"bàn phím: Tab tới điểm, Enter ghim, mũi tên đổi
nội dung tại chỗ" và ::"Tab từ điểm đang ghim đi VÀO popover, và quay lại
được".

Executed By:
Claude Code (S154)

Timestamp:
2026-09-11

#### CHECK-UI345-22
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Route phân rã KHÔNG tự cộng: `orders`, `lines` và `revenue` bằng ĐÚNG cái
`dashboard_metrics.totals()` trả cho chính lát dòng của mốc, và phần chia
theo nhân viên cộng lại đúng bằng tổng của mốc —
`test_the_breakdown_route_matches_dashboard_metrics_exactly`. Nó là route
ĐỌC: `POST` trả `405` — `test_the_breakdown_route_never_writes`.

Executed By:
Claude Code (S154)

Timestamp:
2026-09-11

### Regression

#### CHECK-UI345-23
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Không hành vi nào của `UI-01`/`UI-02` bị phá — 13 bài Playwright cũ vẫn
xanh nguyên vẹn trong lần chạy đầy đủ `35 passed`. Bộ pytest toàn repo:
`3662 passed, 23 skipped, 0 failed` (nền phiên này đo được trước khi sửa:
`3643 passed, 23 skipped`; `+19` bài mới, không bài nào bị xoá). jsdom:
`25 passed`.

Executed By:
Claude Code (S154)

Timestamp:
2026-09-11

#### CHECK-UI345-24
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Việc tách macro KHÔNG đổi một byte nào của trang đầy đủ: render trước/sau
refactor chỉ khác đúng các thuộc tính `data-region` mới thêm (diff hai bản
HTML trên fixture 120 dòng — xem `docs/sessions/S154-*.md` §2).

Executed By:
Claude Code (S154)

Timestamp:
2026-09-11

### Còn mở

#### CHECK-UI345-25
Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E0

Evidence:
Independent Review — phiên này KHÔNG tự đóng. Ngân sách repair của root
task `UI-03-UI-04-UI-05`: 1 allowed / 0 used / 1 remaining
(`PROJECT/REVIEW_BUDGET_LEDGER.md`).

Executed By:
—

Timestamp:
—

#### CHECK-UI345-26
Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E0

Evidence:
Owner nghiệm thu trên production sau khi deploy. Chỉ Owner đóng được; phiên
này không có egress tới Render.

Executed By:
—

Timestamp:
—

#### CHECK-UI345-27
Priority:
RECOMMENDED

Status:
BLOCKED

Evidence Level:
E0

Evidence:
Bộ Postgres concurrency (`tests/test_p0_single_transaction.py`, 11 bài)
CHƯA từng chạy được qua toàn bộ vòng đời `UI-01`/`UI-02` (review vòng 1,
REPAIR-1, review vòng 2) lẫn phiên này, vì `REPORTS_TEST_POSTGRES_URL`
không được đặt trong bất kỳ môi trường nào đã dùng. KHÔNG phải lỗi của
`UI-03`/`UI-04`/`UI-05` — ba lát này không chạm `MutationGuard`/CAS — nhưng
nó là một khoản NỢ KIỂM CHỨNG phải trả trước production. Lệnh cần chạy khi
có PostgreSQL:

```bash
REPORTS_TEST_POSTGRES_URL=postgresql://... \
  .venv/bin/python -m pytest tests/test_p0_single_transaction.py -q
```

Executed By:
—

Timestamp:
—

## Tiêu Chí Hoàn Thành (Exit Criteria)
- [x] 24/26 check REQUIRED đã PASS với E1
- [ ] `CHECK-UI345-25` Independent Review — chưa chạy
- [ ] `CHECK-UI345-26` Owner nghiệm thu production — chưa deploy
- [x] Không có lỗi nghiêm trọng chưa xử lý trong phạm vi task
- [x] Đạt mức evidence yêu cầu (Risk 3/5 → E1 cho REQUIRED)
- [x] Tiến độ dự án đã được cập nhật
- [x] Đã viết Session Handoff

## Đăng Ký File Đã Thay Đổi (Changed Files Registry)

Created:
- `app/web/templates/_workspace_table.html`
- `tests/playwright/workspace-inline.spec.mjs`
- `tests/playwright/workspace-window.spec.mjs`
- `tests/playwright/chart-pin.spec.mjs`
- `tests/test_ui030405_workspace_json.py`
- `docs/tasks/UI-03-04-05-thao-tac-tai-cho-windowing-ghim-bieu-do.md`
- `docs/sessions/S154-ui030405-thao-tac-tai-cho.md`

Modified:
- `app/web/server.py`
- `app/web/workspace_presentation.py`
- `app/web/static/js/app.js`
- `app/web/static/css/tinphat-ui.css`
- `app/web/templates/kinh_doanh_nhan_vien.html`
- `app/web/templates/kinh_doanh_phan_tich.html`
- `app/web/templates/_r6_bits.html`
- `playwright.config.mjs`
- `tests/playwright/fixture_server.py`
- `scripts/stab01_baseline.py`
- `PROJECT/PROJECT_PROGRESS.md`, `PROJECT/REVIEW_BUDGET_LEDGER.md`

Deleted:
- không
