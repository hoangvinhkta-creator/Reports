# S154 — UI-03 / UI-04 / UI-05: thao tác tại chỗ, bảng theo trang, ghim biểu đồ

Ngày: 2026-09-11
Task: `docs/tasks/UI-03-04-05-thao-tac-tai-cho-windowing-ghim-bieu-do.md`
Task Mode: MAJOR
Nhánh: `claude/ui-03-04-05-reports-px1u9l`
Base: `origin/claude/extract-upload-repo-gq2ws4` @ `a224e6f`
Trạng thái cuối phiên: `IMPLEMENTED` — **chưa push, chưa PR, chưa merge**

## 0. Mở phiên

Đồng bộ nhánh theo `governance/core/00_SESSION_ORCHESTRATION.md` bước 0:

```text
git remote show origin → HEAD branch: claude/extract-upload-repo-gq2ws4
git fetch origin claude/extract-upload-repo-gq2ws4
HEAD cục bộ = a224e6f = DEFAULT_TIP   (ahead 0, behind 0)
```

`scripts/branch_authority_check.sh` báo `BRANCH AUTHORITY UNRESOLVED` với lý
do "nhánh không có upstream". Đây là HỆ QUẢ TRỰC TIẾP của yêu cầu "không
push" trong brief phiên này, không phải một lỗi cần sửa bằng cách push.

Môi trường phải dựng lại từ đầu: `.venv` và `node_modules` không có sẵn
trong container. Sau khi dựng, đo NỀN trước khi sửa một dòng nào:

```text
pytest (trừ bọc Playwright)   3643 passed, 23 skipped
tests/playwright/             13 passed
tests/browser/ (jsdom)        25 passed
```

## 1. Vì sao lát nền (`defa0fb`) phải làm trước cả ba

Trước phiên này, markup của một hàng bảng kê chỉ tồn tại BÊN TRONG vòng lặp
của `kinh_doanh_nhan_vien.html`. Cả `UI-03` (vá một BH sau khi ghi) lẫn
`UI-04` (nối thêm một trang) đều cần đúng những `<tr>` ấy ở giữa một vòng
đời khác, và chỉ có hai đường:

- dựng lại CẢ trang (đúng cái hai lát này tồn tại để bỏ đi), hoặc
- dựng chúng bằng JavaScript ở client.

Đường thứ hai là dựng một BẢN THỨ HAI của bảng kê. Một hàng mang `rowspan`
theo số dòng của BH, ba cột tuỳ chọn ẩn bằng CSS, bốn loại nhãn trạng thái,
hai đường vào phân loại, một ô nhập thuộc về một `<form>` đứng NGOÀI bảng.
Bản thứ hai sẽ lệch khỏi bản thứ nhất ở lần đầu ai đó thêm một cột, và
không test template nào soi tới — cả hai bản đều "đúng" theo chính nó.

Nên markup được chuyển NGUYÊN VĂN vào `_workspace_table.html` và cả trang
đầy đủ lẫn các route JSON gọi CÙNG những macro đó.

## 2. Bằng chứng: tách macro KHÔNG đổi một byte nào của trang

Render cùng một trang (fixture 120 dòng) trước và sau refactor, so sau khi
bỏ thụt đầu dòng và dòng trống:

```text
$ diff <(sed 's/^[[:space:]]*//; /^$/d' /tmp/before.html) \
       <(sed 's/^[[:space:]]*//; /^$/d' /tmp/after.html)
77c77
< <div class="kpi-grid strip">
---
> <div class="kpi-grid strip" data-region="kpi-strip">
142a143,144
> <div data-region="identity-warning">
> </div>
171c173,174
< <tr class="row-total" data-metric="sheet-totals">
---
> <tr class="row-total" data-metric="sheet-totals"
> data-region="sheet-totals">
```

Ba khác biệt, cả ba là các thuộc tính `data-region` CỐ Ý thêm. Không một ô,
một nhãn, một `data-metric` nào đổi. (Hai thuộc tính `data-region` trên
`kpi-strip`/`sheet-totals` sau đó được dời ra vùng bọc ở trang — xem §5.)

## 3. Ba lát dọc

### UI-03 — `b9e97cc`

Ba đường ghi (`phan-loai`, `ngoai-bang`, `loai-dong`) giữ NGUYÊN thân hàm.
`_workspace_answer()` chọn giữa `_workspace_redirect` (trình duyệt) và
payload JSON (`Accept: application/json`, so bằng `request.accept_mimetypes`
chứ không tìm chuỗi — trình duyệt gửi `*/*` cho một form POST thật).

Payload trả ĐỦ mọi dòng bị ảnh hưởng. Với phân loại, đó là MỌI BH có dòng
dùng chung khoá định danh (`INV-76`/`INV-87`) — không riêng dòng vừa bấm.
Mỗi BH đi kèm `{html, after, before}`; hai hàng xóm cần cho một ca có thật:
khôi phục dòng CUỐI của một đơn vừa bị loại, khi cả khối đã biến mất nên
không có hàng nào để THAY, phải CHÈN. Cả hai hàng xóm đều ngoài cửa sổ đang
tải ⟹ client không chèn gì (đúng: BH ấy không thuộc cửa sổ), không nối bừa
vào cuối bảng.

Lỗi này được phát hiện bởi chính bài Playwright "khôi phục đưa dòng trở lại
ĐÚNG khối BH của nó" — bản đầu chỉ có `replaceGroup()` và im lặng bỏ qua
khi không tìm thấy hàng cũ.

### UI-04 — `defa0fb` + `9cabfa8`

`page_of_groups()` cắt theo RANH GIỚI BH. `limit` là một NGƯỠNG, không phải
một con số chính xác: trang dừng ở BH đầu tiên khiến tổng dòng CHẠM hoặc
VƯỢT ngưỡng, và một BH lớn hơn cả ngưỡng vẫn đi trọn trong một trang.

Con trỏ là MÃ BH, không phải offset — offset trỏ sai ngay khi một dòng bị
loại giữa hai lần tải, đúng thao tác mà `UI-03` làm trên cùng màn hình.

Trang đầu vẫn dựng SERVER-SIDE, và `XEM TIẾP` là một `<a href="?…&tu=…">`
THẬT: tắt JavaScript vẫn đi hết được bảng.

### UI-05 — `c98df8a`

Mở rộng CHÍNH `.rev-tooltip` đã có, không thêm phần tử thứ hai. Hai tầng dữ
liệu: giá trị cơ bản hiện NGAY từ `title` mà server đã đặt trên chính điểm;
phân rã tải NỀN. `GET /api/v1/analytics/chart-breakdown` là route ĐỌC và
KHÔNG có một phép tính nào — `dashboard_metrics.totals()` cộng,
`dashboard_presentation.money_cell()` định dạng, `revenue_timeline.
bucket_of()` chia mốc.

## 4. Hai lỗi tự phát hiện và đã sửa trong phiên (`b23d5a5`)

### 4.1 `trimToBudget` không thật sự giữ vị trí cuộn

Bản đầu đo chiều cao vừa mất trên chính cái BẢNG. Mép trên của bảng nằm
PHÍA TRÊN chỗ bị gỡ nên nó không nhúc nhích — phép bù ra `0`, và màn hình
nhảy. Đo được: **lệch 4.777 px**.

Đo trên hàng sống sót ĐẦU TIÊN vẫn chưa đủ: `<table>` dùng bố cục AUTO nên
gỡ một trăm hàng đổi bề rộng cột, đổi cách chữ xuống dòng, và đổi chiều cao
của những hàng CÒN LẠI — bù đúng ở chỗ ấy thì lệch dần xuống dưới. Đo được:
**còn lệch 46,5 px** ở chỗ người dùng đang nhìn.

Nay mốc đo là hàng sống sót ĐẦU TIÊN CÒN TRONG KHUNG NHÌN. Đo được:
**dưới 4 px**, canh bằng bài kiểm mới.

Một chi tiết đi kèm: CSS `overflow-anchor: none` trên `.sheet-table`. Scroll
anchoring của Chrome bù thêm một phần theo heuristic của nó, và hai phép bù
chồng lên nhau là hai cơ chế cho cùng một việc.

### 4.2 `<template>` câu chữ nuốt mất `data-metric` của hộp xác nhận không-JS

Nội dung `<template>` nằm THẬT trong tài liệu, nên phép tìm "phần tử mang
`confirm-question`" bắt được bản trong template TRƯỚC bản đang hiển thị.
Hai bài của hộp không-JS (`test_the_exclusion_asks_for_a_short_confirmation_
first`, `test_the_gia_dung_move_asks_a_short_confirmation_with_two_buttons`)
đỏ vì đúng chuyện đó. Đổi thành `line-confirm-question`/`line-confirm-point`
— hai hộp khác nhau, hai tên khác nhau.

## 5. Một quyết định đi ngược trực giác, ghi lại để review soi

Ba route đọc mới trả HTML trong phong bì JSON, không trả dữ liệu thô. Lý do
đầy đủ ở §3.1 của file task và ở chú thích đầu `_workspace_table.html`.
Con SỐ (`next_cursor`, `total_lines`, `affected`) vẫn là JSON thật — client
cần chúng để quyết định tải tiếp hay dừng, và chúng không phải markup.

## 6. Số đo (`scripts/stab01_baseline.py --lines 5000`)

Máy dev, LOCAL/TEST — **không phải số production** (xem docstring đầu
script). Fixture 5.000 dòng, SQLite trong bộ nhớ, cắt mạng ngoài.

```text
                                    p50        bytes      <tr>
nhan-vien-full                    254,7 ms    322.214      103
  (bản ghi UI-01/UI-02, cùng script, cùng fixture:
   1.417 ms · 15.290.054 byte · 5.002 hàng)
ui03-mo-popover-phan-loai         160,7 ms        126        0
  (đường CŨ cho cùng việc: nhan-vien-fragment, 263,4 ms · 319.736 byte)
ui04-mot-trang-windowing          222,4 ms    343.321      101
ui05-phan-ra-mot-moc              346,3 ms        399        0
api-order-detail (= panel-open)   198,5 ms      1.852        0
PATCH 20 lượt liên tiếp           p50 407,2 ms · p95 427,4 ms
```

`ui05-phan-ra-mot-moc` cao hơn các đường đọc khác vì `_chart_details()` có
thể mở một lượt đọc kỳ THỨ HAI để phủ đủ cửa sổ so sánh của năm trước. Đây
là chi phí ĐÃ CÓ SẴN của `R6` (`FIND-R6-IR-01` repair), không phải một hồi
quy do `UI-05` tạo ra; và nó chạy NỀN sau khi giá trị cơ bản đã hiện.

## 7. Bằng chứng test đầy đủ

```text
pytest (toàn repo, trừ bọc Playwright)  3662 passed, 23 skipped, 0 failed
  nền cùng phiên, cùng máy, trước khi sửa: 3643 passed, 23 skipped
  chênh +19 = đúng số bài MỚI của tests/test_ui030405_workspace_json.py;
  không bài nào bị xoá
tests/browser/ (jsdom, node --test)     25 passed  (không đổi)
tests/playwright/ (Chromium thật)       35 passed  (13 cũ + 22 mới)
```

Ba file Playwright mới: `workspace-inline.spec.mjs` (7), `workspace-window.
spec.mjs` (7), `chart-pin.spec.mjs` (8).

Máy chủ fixture Playwright được sửa hai chỗ, cả hai vì bộ kiểm mới GHI thật:

1. Thẩm quyền Product Identity trỏ vào một thư mục TẠM. Trước khi sửa, các
   lượt thăm dò trong phiên đã ghi thật vào `data/product_identity/
   mappings.jsonl` của repo — đã `git checkout` trả lại và xoá `index.json`
   sinh ra kèm. Không có thay đổi nào của `data/` đi vào commit nào.
2. `reuseExistingServer: false`. Dùng lại một máy chủ còn sống từ lần chạy
   trước làm lần chạy thứ hai thấy dòng ĐÃ phân loại, và các mệnh đề im
   lặng biến mất.

Thêm một máy chủ fixture THỨ HAI (cổng 8932, 5.000 dòng) cho `UI-04`: mọi
mệnh đề ngân sách DOM đều xanh với mọi kiến trúc trên 90 dòng.

## 8. NỢ KIỂM CHỨNG (kế thừa, không phải của phiên này)

`tests/test_p0_single_transaction.py` (11 bài — đồng thời/CAS trên
PostgreSQL thật) CHƯA TỪNG chạy được qua toàn bộ vòng đời `UI-01`/`UI-02`
(review vòng 1, `REPAIR-1`, review vòng 2) lẫn phiên này, vì
`REPORTS_TEST_POSTGRES_URL` không được đặt trong bất kỳ môi trường nào đã
dùng. Ba lát ở đây KHÔNG chạm `MutationGuard`/CAS, nên đây không phải lỗi
của chúng — nhưng nó nằm trong bản ghi chính thức để không bị quên trước
production. Lệnh cần chạy khi có PostgreSQL:

```bash
REPORTS_TEST_POSTGRES_URL=postgresql://... \
  .venv/bin/python -m pytest tests/test_p0_single_transaction.py -q
```

Xem `CHECK-UI345-27`.

## 9. Những gì CỐ Ý KHÔNG làm

1. **Không đụng dải KPI/hàng TỔNG sau một lần PATCH của panel sửa đơn.**
   Giới hạn đã ghi ở `UI-01`/`UI-02` còn nguyên; `UI-03` chỉ trả `regions`
   cho ba đường ghi CỦA NÓ, không mở rộng payload của `api_patch_order`.
2. **Không thêm bước xác nhận cho KHÔI PHỤC ở đường KHÔNG-JS.** Nút
   KHÔI PHỤC trong bảng "đã loại" vẫn gửi thẳng, y như trước `UI-03`. Thêm
   một bước ở đó là đổi hành vi của một luồng đã nghiệm thu, ngoài Scope
   Lock.
3. **Không ghim/phân rã ở biểu đồ trang Báo cáo (`R5`).** Phạm vi của nó
   đọc bằng một bộ tham số khác `_analysis_range()`; gửi tham số của trang
   này sang route kia sẽ phân rã một khoảng thời gian người dùng không
   chọn. Ghim vẫn hoạt động ở đó (giá trị cơ bản), chỉ không có phân rã, và
   popover NÓI RA điều đó thay vì để một ô "đang tải" quay mãi.
4. **Không cập nhật `PROJECT/LO_TRINH_DE_HIEU.md`.** Quy tắc đồng bộ ở
   `governance/core/00_SESSION_ORCHESTRATION.md` §"Giao thức Đóng Phiên" bước 5 gắn với một
   milestone làm ĐỔI trạng thái `DONE`/`CURRENT`/… Phiên này kết thúc ở
   `IMPLEMENTED`, chưa qua review, chưa merge — không trạng thái nào đổi.
   Cùng tiền lệ `UI-01`/`UI-02`, vốn cũng không xuất hiện trong file ấy.
   Việc đồng bộ thuộc về phiên MERGE.
5. **Không có bằng chứng thị giác (ảnh chụp) trên Render thật.** Mọi số ở
   đây là máy dev + Chromium local.

## 10. Trạng thái git cuối phiên

```text
nhánh   claude/ui-03-04-05-reports-px1u9l   (KHÔNG push)
base    origin/claude/extract-upload-repo-gq2ws4 @ a224e6f
commit  defa0fb  UI-04 (nền): tách macro dùng chung + phân trang theo BH
        b9e97cc  UI-03: phân loại/loại/khôi phục tại chỗ
        9cabfa8  UI-04: nối trang qua route JSON + ngân sách DOM
        c98df8a  UI-05: ghim tooltip + phân rã, tải nền
        b23d5a5  bằng chứng server (pytest), đo stab01, hai sửa lỗi
```

Năm commit tách theo lát dọc có chủ ý: vòng Independent Review sau này
review được từng phần độc lập.

## 11. Task khuyến nghị tiếp theo

1. Independent Review lineage `UI-03-UI-04-UI-05` (`CHECK-UI345-25`).
   Ngân sách: 1 allowed / 0 used / 1 remaining.
2. Sau khi PASS: quyết định tích hợp + merge; phiên merge đồng bộ
   `PROJECT/LO_TRINH_DE_HIEU.md`.
3. Trả nợ `CHECK-UI345-27` khi có PostgreSQL.

## 12. Phụ lục — push + tích hợp nhánh mặc định (cùng phiên, sau §11)

Chủ dự án xác nhận trực tiếp bằng văn bản việc push. Đã
`git push -u origin claude/ui-03-04-05-reports-px1u9l` → `99b727e`.

Ngay sau đó, đồng bộ lại theo `governance/core/00_SESSION_ORCHESTRATION.md` phát hiện
nhánh mặc định đã tiến 5 commit (`TASK-OWNER-UIUX-009` + `R7`, hai lineage
độc lập merge trong lúc phiên này chạy), `branch_authority_check.sh` báo
`DIVERGENCE: INTEGRATION_DECISION_REQUIRED [loc>5000]`
(`governance/core/V4_1_POLICY_FREEZE.md` §8). Dò bằng `git merge-tree`
(không ghi gì vào repo) xác nhận xung đột THẬT ở 4 file:

```text
kinh_doanh_nhan_vien.html   TASK-OWNER-UIUX-009 bỏ hẳn vùng hiển thị
                             identity_warning — đè lên đúng chỗ commit
                             `defa0fb` bọc data-region="identity-warning"
_r6_bits.html                R7 chèn khối chart.projection ngay sau
                             chart-legend — sát chỗ UI-05 thêm
                             data-breakdown
server.py                    R7 đổi orders_by_bucket() → count_series()
                             ở hai route biểu đồ số đơn — không đụng route
                             breakdown của UI-05, chỉ gần trong file
tinphat-ui.css                thêm .chart-projection sát .tp-confirm-pop/
                             .rev-tooltip.is-pinned
```

Được hỏi qua `AskUserQuestion` (ba lựa chọn theo đúng V4.1 §8: A/tích hợp
ngay, C/giao review trên nhánh cũ + ghi ledger, hoặc tự xem trước) — chủ
dự án chọn **(A) tích hợp ngay**.

`git merge origin/claude/extract-upload-repo-gq2ws4 --no-edit` → chỉ
`kinh_doanh_nhan_vien.html` + hai file governance (`PROJECT/PROJECT_PROGRESS.md`,
`PROJECT/REVIEW_BUDGET_LEDGER.md`) xung đột thật; `server.py`/`tinphat-ui.css`/
`_r6_bits.html` tự merge sạch bằng 3-way merge thật (đủ xa nhau trong file
dù `merge-tree` preview lo ngại gần nhau).

Giải xung đột:
- `kinh_doanh_nhan_vien.html` — NHẬN quyết định `TASK-OWNER-UIUX-009` (đã
  merge, là quyết định chính thức). Bỏ khoá `"identity-warning"` khỏi
  `_workspace_regions()` (`server.py`) vì không còn host DOM nào để vá
  vào — gửi HTML cho vùng đó là dữ liệu chết. Macro `identity_warning_
  block` KHÔNG xoá khỏi `_workspace_table.html` (một trang khác cần lại
  gọi được ngay). Cập nhật `test_the_write_payload_carries_the_server_
  built_regions`.
- `PROJECT/PROJECT_PROGRESS.md`/`PROJECT/REVIEW_BUDGET_LEDGER.md` — xung đột cơ học (ai
  đứng đầu file, do cấu trúc fenced code block giống nhau đánh lừa thuật
  toán diff theo dòng). Giữ CẢ BA entry nguyên vẹn; đối chiếu bằng
  `git diff origin/...:file file` xác nhận không mất nội dung của R7/
  UIUX-009.
- Đổi số phiên `S153` → `S154` (trùng `S153-r7-...` đã có trên nhánh mặc
  định — hai phiên độc lập cùng lấy số kế tiếp lúc tách nhánh, cùng tình
  huống `DEC-222`→`DEC-223` mà `TASK-OWNER-UIUX-009` đã gặp và tự sửa).

Test SAU tích hợp (không phải trước):

```text
pytest (toàn repo)              3680 passed, 23 skipped, 0 failed
tests/browser/ (jsdom)          25 passed
tests/playwright/ (Chromium)    35 passed (không đổi so với trước tích hợp)
Validators governance           structure/project_state/evidence/
                                task_completion PASS; reference_integrity
                                đúng 4 baseline cũ
```

Commit merge: `97b47dc` (merge commit thật, hai cha — không rebase, không
squash). `branch_authority_check.sh` sau tích hợp:
`behind default: 0 commit` (đã đồng bộ); `DIVERGENCE: INTEGRATION_
DECISION_REQUIRED [loc>5000]` vẫn còn hiện vì cờ này đo TỔNG LOC khác biệt
với nhánh mặc định (bao gồm chính công của lineage này), không đo việc
đồng bộ — nó tự hết khi lineage merge vào nhánh mặc định.

Đã push lại: `git push origin claude/ui-03-04-05-reports-px1u9l` → `97b47dc`.

**Trạng thái cuối cùng của phụ lục này:** đã push, đã tích hợp, sẵn sàng
giao Independent Review trên `97b47dc`. Chưa tạo PR (không ai yêu cầu),
chưa merge vào nhánh mặc định, chưa deploy.

## 13. REPAIR-1 — đóng F-02 (blocking) + F-01 (reference integrity)

Independent Review trên HEAD `c60ae08` kết luận `REQUEST CHANGES` với 2
finding. Ngân sách repair của lineage `UI-03-UI-04-UI-05` còn nguyên
`1 allowed/0 used/1 remaining` — vòng sửa này tiêu ĐÚNG cycle duy nhất đó,
không cần `OWNER_EXTENSION`. Tiếp tục trên CHÍNH nhánh
`claude/ui-03-04-05-reports-px1u9l`, không tạo nhánh mới, không reset base
— đúng `governance/core/V4_1_POLICY_FREEZE.md` §3.

### F-02 (BLOCKING)

`_workspace_write_payload()` (`app/web/server.py`) gọi `_workspace_context(
view, only_orders=order_keys)`, và hàm đó lọc `scoped = view["data"].
for_sheet(sheet)` THEO SHEET ĐANG XEM trước khi cắt `only_orders` qua
`groups_slice`. Một `order_key` thuộc sheet khác không khớp group nào
trong `scoped` — không phải vì nó đã bị loại khỏi báo cáo, mà đơn giản vì
nó không nằm trên trang đang mở. Bản trước đọc sự vắng mặt ấy thành "đã
xoá" (`removed_order_keys`) và đếm thiếu `affected.lines`.

Sửa theo cả hai hướng review nêu:
- `removed_order_keys` kiểm sự tồn tại trên TOÀN KỲ (`view["data"].
  details`), không qua `scoped`.
- `affected.lines` nhận tham số `lines` tường minh từ nơi gọi —
  `len(shared)` ở hai route xác nhận/ngoài-bảng-giá (một BH có thể mang
  nhiều dòng cùng khoá định danh), mặc định `len(order_keys)` cho route
  loại/khôi phục (luôn đúng một dòng một BH).

Test tái hiện (`tests/test_ui030405_workspace_json.py::
test_a_decision_reaching_another_sheet_is_not_reported_as_removed`):
fixture riêng dựng hai dòng cùng `product_raw` chưa phân loại — một BH
sheet `noi-thanh`, một BH sheet `gia-dung` (đẩy sang `gia-dung` bằng ĐÚNG
con đường `service.store.set_line_product_group` mà route Gia dụng dùng;
phát hiện giữa chừng: `sheet_key_of` đọc `classified_product_group` —
kết quả của một QUYẾT ĐỊNH đã lưu — chứ không đọc thẳng `product_group_
final` của pipeline, nên chỉ đặt trường đó trên dòng kết quả KHÔNG đủ để
đẩy dòng sang sheet khác). Xác nhận FAIL trên code trước sửa
(`affected.lines == 1`, đúng lỗi review mô tả), PASS sau khi sửa.

### F-01

`docs/sessions/S154-ui030405-thao-tac-tai-cho.md` (chính file này, §12)
ghi ba tên file TRẦN thay vì đường dẫn đầy đủ. Xác nhận đúng ba đường dẫn
thật trong repo (`ls` từng file) trước khi sửa — không đoán. Sửa thành
`governance/core/00_SESSION_ORCHESTRATION.md`, `PROJECT/
PROJECT_PROGRESS.md`, `PROJECT/REVIEW_BUDGET_LEDGER.md`.

### Bằng chứng SAU cả hai sửa

```text
pytest (toàn repo)              3681 passed, 23 skipped, 0 failed
                                (+1 so với trước repair — đúng test mới)
tests/browser/ (jsdom)          25 passed
tests/playwright/ (Chromium)    35 passed (không đổi)
validate_reference_integrity    7 → 4 lỗi (4 lỗi baseline cũ, không đổi)
Validators khác                 structure/project_state/evidence/
                                task_completion PASS
```

Phạm vi repair diff (`git diff c60ae08..05daf76 --name-only`):
`app/web/server.py`, `docs/sessions/S154-ui030405-thao-tac-tai-cho.md`,
`tests/test_ui030405_workspace_json.py`. Commit repair:
`05daf76` (`base_sha=c60ae08`, `head_sha=05daf76`).
