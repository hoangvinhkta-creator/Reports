# S135 — R5 REPAIR-1: hai finding `REPAIR_REQUIRED` của Independent Review

## 0. Tóm tắt cho người đọc vội

Independent Review R5 kết luận `REPAIR_REQUIRED` với hai finding. Phiên này
sửa cả hai, sửa thêm một `ACCEPTED_RISK` về chất lượng bài kiểm, và **đính
chính một dòng bằng chứng sai trong `S134`** (xem §5 — lỗi của phiên triển
khai, không phải của reviewer).

Cả hai finding có CÙNG hình dạng, và nó đáng được nói ra vì nó là bài học
chứ không phải hai lỗi rời rạc:

> R5 lấy một cơ chế đã ĐÚNG ở ngữ cảnh cũ, đặt nó vào một ngữ cảnh nơi cái
> giá của sai lầm khác hẳn, và không tính lại CHIỀU AN TOÀN của nó.

Trong cả hai trường hợp, mã cũ có một chú thích nói rõ vì sao nó an toàn —
và R5 làm cho chính câu chú thích ấy thôi đúng, mà không ai đọc lại nó.

```text
Reports HEAD  1d971de21a82f5a2ca367180de6ae257133a02b1
Tracking HEAD f958226f6127e6055eb411e4c22e12c58d09654b  (KHÔNG đổi)
Reports test  3232 passed, 12 skipped   (trước repair: 3223)
Tracking test 61 bộ · 2767 đạt · 0 hỏng · 2 bỏ qua      (KHÔNG đổi)
```

**Kết luận phiên: `IMPLEMENTED` (sau repair).** `CHECK-R5-27` vẫn thuộc
thẩm quyền của phiên review độc lập kế tiếp — phiên repair KHÔNG tự đóng nó.

## 1. Điều phiên này KHÔNG đọc được

Bàn giao review — bản ghi review, session review, và file task repair mà tóm
tắt của Owner nhắc tới (`R5-INDEPENDENT-REVIEW-RECORD`,
`S135 · r5-independent-review`, `R5-REPAIR-1-doi-soat-nhan-vien-va-khoi-phuc`,
dẫn bằng TÊN vì chúng không phải file trong nhánh này) — KHÔNG có mặt trên
nhánh `claude/r5-reports-tracking-deploy-o77n7t` và không tìm thấy trên bất
kỳ ref nào của remote:

```text
$ git branch -r | grep -i "r5\|review"      → không có nhánh review R5
$ git log --all --oneline --grep "S135|R5-REPAIR" -i  → không có commit nào
```

Phiên này vì thế làm việc trên **bản tóm tắt review do Owner chuyển tiếp**,
không trên bản ghi gốc. Hệ quả cần biết khi đọc bàn giao này:

- Mọi số hiệu finding (`FIND-R5-IR-01`, `FIND-R5-IR-02`, `AR-R5-IR-11`) được
  dùng ĐÚNG như Owner chuyển tiếp; phiên này không tự đặt lại tên chúng.
- Phiên này KHÔNG thể xác nhận rằng nó đã sửa hết mọi finding của bản ghi
  gốc — nó chỉ xác nhận đã sửa hết những gì được chuyển tiếp.
- Tên file `S135-r5-repair-1.md` được chọn để KHÔNG đụng tên file mà bản ghi
  review sẽ mang (cùng số session `S135`); nếu hai file cùng số gặp nhau lúc
  tích hợp, đây là chỗ giải thích vì sao.

## 2. `FIND-R5-IR-01` — bấm `XONG` gán lại cả BH cho nhân viên đầu danh sách

### Lỗi, tái hiện được

```text
$ pytest tests/test_r5_repair_1.py::test_saving_an_order_split_between_two_employees_reassigns_nobody
E  AssertionError: một cú bấm XONG để lưu giá KHÔNG được gán lại cả đơn cho ai
E  assert ['Hiệp'] == ['Quý', 'Vinh']
```

`assignable_employee_options()` cố ý không có mục trống, và docstring của nó
nói vì sao: *"ô này để GÁN một dòng cho ai đó"*. Đúng — khi ô ấy còn nút gửi
RIÊNG (`GÁN CẢ ĐƠN`). Mở form đó ra và bấm nó nghĩa là bạn muốn gán.

R5 §4 gộp mọi thứ về một nút gửi, và câu trên thôi đúng. `group.employee_value`
là chuỗi RỖNG khi BH chưa có nhân viên hoặc đang chia cho nhiều người; không
option nào mang giá trị rỗng ⟹ không option nào `selected` ⟹ **trình duyệt
gửi option ĐẦU TIÊN**, không phải chuỗi rỗng.

### Sửa

Một mục `— Giữ nguyên —` mang giá trị rỗng, chỉ thêm ở màn hình nào ô chọn đi
cùng nút gửi dùng chung (`keep_option=True`, đúng một call site). Nó đứng ĐẦU
danh sách có chủ đích: đó cũng là thứ trình duyệt rơi về nếu một ngày nào đó
không option nào được chọn sẵn nữa — **fail-safe là "không đổi gì", không phải
"gán cho người đầu bảng chữ cái"**.

Bảng kê chi tiết (`/kinh-doanh/gia-nhap`) giữ nguyên: nút gửi riêng, không mục
trống, đúng `OD-5`.

### Vì sao bài kiểm này bắt được, còn một bài viết cẩu thả thì không

`submit_as_browser_would()` đọc HTML thật, tìm option đang `selected`, và gửi
ĐÚNG giá trị đó — mô phỏng chính hành vi trình duyệt. Một bài gửi thẳng
`nhan_vien_moi=""` sẽ **XANH trên chính bản mã có lỗi**: lỗi không nằm ở
server, nó nằm ở chỗ HTML bảo trình duyệt gửi cái gì.

Bài thứ ba khoá cả LỚP lỗi bằng một bất biến cấu trúc thay vì ba trường hợp
dữ liệu: *mọi ô chọn nhân viên phải LUÔN có đúng một option được chọn*.

## 3. `FIND-R5-IR-02` — dòng quay lại không khôi phục khi hai lần nạp cùng một giây

### Lỗi

`_with_absence_state` so mốc NGẶT (`seen > anchor`), và chú thích ngay tại chỗ
nói rõ vì sao ngặt là an toàn:

> *"Không con số nghiệp vụ nào phụ thuộc vào nhãn này (hiện trạng và tổng tiền
> không bao giờ do cờ quyết định)."*

R5 §1 làm nhãn ấy quyết định tổng tiền. Câu chú thích thôi đúng, và chiều an
toàn ĐẢO NGƯỢC — nhưng phép so thì không đổi. `history_writer` ghi mốc snapshot
ở `timespec="seconds"`, nên hai lần bấm nạp cách nhau vài trăm mili giây ghi ra
hai mốc BẰNG NHAU:

```text
CÁCH NGÀY (điều kiện của test R5 hiện có)      tổng = 12.000.000
SAU 1 GIÂY                                     tổng = 12.000.000
CÙNG GIÂY (độ phân giải THẬT của production)   tổng =  8.000.000  ← mất 4tr
```

Tổng thấp hơn vĩnh viễn, không có nút khôi phục, và màn hình vẫn hứa ngược lại.

### Sửa — hai nửa, và cả hai đều CHỊU LỰC

**Nửa 1: mốc snapshot ghi ở MICRO-giây** (`history_writer._now_iso`). Chuỗi
ISO-8601 vẫn so đúng bằng phép so chuỗi kể cả khi đứng cạnh bản ghi cũ ghi tới
giây (`"…T10:00:00"` < `"…T10:00:00.000001"`, và một mốc chỉ tới giây đúng là
mốc ĐẦU của giây ấy), nên **không cần migrate gì**.

**Nửa 2: ngưỡng đổi thành `>=`**, và sau nửa 1 nó chỉ còn tác dụng ở những bản
ghi CŨ ghi tới giây. Ở đó bằng nhau nghĩa là không phân giải được thứ tự, và
hai cách sai KHÔNG ngang giá nhau:

```text
giữ cờ khi thực ra dòng đã quay lại  ⟹ mất tiền, im lặng, không đường quay lại
bỏ cờ khi thực ra dòng vẫn vắng      ⟹ giữ tiền như TRƯỚC R5; câu xác nhận nói
                                       "đã tạm loại N dòng" còn tổng không đổi,
                                       nên người dùng thấy ngay và nạp lại được
```

Nghiêng về phía thứ hai là cùng kỷ luật mà R5 §3 đã áp cho biểu đồ: chỗ nào
chưa có bằng chứng thì để trống, không tự điền một con số bất lợi.

`seen` KHÔNG BAO GIỜ là chính snapshot đã dựng cờ — `_latest_membership` chỉ
xét snapshot CHỨA khoá, còn snapshot dựng cờ là snapshot KHÔNG chứa nó. Nên
`>=` không tự làm mọi cờ vô hiệu.

### Bằng chứng cả hai nửa đều cần thiết

```text
$ sed -i 's/microseconds/seconds/' history_writer.py   # hoàn nguyên nửa 1
  3 failed  (gồm chính bài tái hiện kịch bản production)

$ sed -i 's/>= anchor/> anchor/' history_store.py      # hoàn nguyên nửa 2
  1 failed  (bài khoá chiều an toàn của bản ghi cũ)

$ (khôi phục cả hai)                                   9 passed
```

### Bài kiểm dùng đúng mốc thật, và có ĐỐI CHỨNG

Bài tái hiện gọi chính `history_writer._now_iso()` mà đường nạp sổ production
gọi, ba lần liên tiếp, và chạy trọn vòng `đủ → thiếu + xác nhận → đủ lại`
(12tr → 8tr → 12tr). Kèm một bài **đối chứng** khẳng định ba mốc ấy thật sự
nằm trong CÙNG một giây đồng hồ — không có nó, bài kia có thể xanh chỉ vì ba
lần ghi tình cờ rơi vào ba giây khác nhau, và khi ấy nó không chứng minh gì.

Bài `test_a_genuinely_older_snapshot_still_leaves_the_flag_active` canh cửa
theo chiều ngược: mốc cũ hơn HẲN vẫn là "chưa quay lại". Không có nó, `>=`
không phân biệt được với "bỏ hẳn phép so", và R5 §1 mất luôn khả năng loại dòng.

## 4. `AR-R5-IR-11` — docstring hứa một khẳng định không có trong thân bài

`test_the_workspace_never_renders_a_prohibited_personal_field` hứa *"không có
một giá trị mã máy nào lọt ra khi sổ không ghi mã máy nào"* mà thân bài không
kiểm. Nay kiểm thật: mọi ô `line-imei` phải là dấu gạch.

Reviewer đúng cả ở phần đánh giá lẫn ở phần phân loại — đây là một khiếm khuyết
CHẤT LƯỢNG BÀI KIỂM, không phải một lỗ hổng phạm vi IMEI (phạm vi ấy do
`tests/test_r5_imei_boundary.py` canh theo GIÁ TRỊ trên 7 trang + export +
snapshot, và bộ đó không đổi).

## 5. ĐÍNH CHÍNH bằng chứng của `S134` — lỗi của phiên triển khai

`S134` §4 liệt kê `tools/smoke/r1_daily_min_smoke.py` trong khối "Chạy kiểm"
và §10 đưa nó vào lệnh tái lập **không kèm tham số**. Cả hai đều sai:

```text
$ .venv/bin/python tools/smoke/r1_daily_min_smoke.py
Chạy (từ gốc repo Reports):
    python tools/smoke/r1_daily_min_smoke.py <file-capture.json> [thư-mục-tạm]
EXIT=2      ← thông báo cách dùng, KHÔNG phải một lần chạy
```

Phiên `S134` đo `EXIT=$?` SAU một `| tail -8`, nên nó đọc mã thoát của `tail`
(luôn 0) chứ không của Python. Đó là một khẳng định PASS **chưa từng được
chứng minh**, và nó là lỗi của phiên triển khai — không phải của reviewer.

Chạy đúng với fixture có sẵn thì công cụ CRASH, và crash y hệt trên nền
trước R5:

```text
$ .venv/bin/python tools/smoke/r1_daily_min_smoke.py \
      tests/fixtures/daily_min/tracking_contract_export.json
  PASS  Kỳ 03/09 chỉ dùng ngày ĐÃ CHỐT → resolved_prices_are_final
  ...
  AttributeError: 'NoneType' object has no attribute 'value'   (dòng 167)
EXIT=1

$ (cùng lệnh, cùng fixture, trên worktree tại b6756fe)
EXIT=1   — cùng traceback
```

**Kết luận: lỗi BASELINE CŨ của công cụ kiểm** (fixture không mang giá cho
ngày bán thứ hai nên `prov2.day_status` là `None`), không do R5 và không do
repair này. Phiên repair KHÔNG sửa nó: nó nằm ngoài phạm vi hai finding, và
reviewer không nêu nó. Ghi lại thành `AR-R5-IR-12` để Owner quyết định.

`S134` đã được sửa tại chỗ ở §4 và §10 để không còn mang khẳng định sai.

## 6. Bằng chứng

```text
$ .venv/bin/python -m pytest tests/test_r5_repair_1.py -q
9 passed in 1.21s

$ .venv/bin/python -m pytest -q
3232 passed, 12 skipped in 156.98s      (trước repair: 3223 passed, 12 skipped)

$ .venv/bin/python tools/smoke/r1_web_upload_smoke.py --tracking-repo ../Tracking
KẾT QUẢ SMOKE: TẤT CẢ PASS

$ npm test            (Tracking, KHÔNG đổi trong phiên này)
61 bộ · 2767 đạt · 0 hỏng · 2 bỏ qua

$ validate_evidence / project_state / structure / task_completion
PASS · PASS · PASS · PASS

$ validate_reference_integrity
FAIL — ĐÚNG BA reference của `TASK-REM-T06`, lỗi baseline đã ghi ở `S134` §6
```

Không test nào bị nới. Chín bài mới đều là bài MỚI; bài duy nhất bị sửa
(`test_the_workspace_never_renders_a_prohibited_personal_field`) được làm CHẶT
hơn, không lỏng hơn.

## 7. Rủi ro chấp nhận mới

`AR-R5-IR-12` — **`r1_daily_min_smoke.py` crash với fixture có sẵn.** Lỗi
baseline cũ, đo được trên `b6756fe`; công cụ kiểm, không phải mã sản phẩm.
Không sửa trong phiên repair (ngoài phạm vi hai finding). Hệ quả: một trong
hai smoke của R1 hiện không chạy được, và luồng nó canh (giá theo ngày bán
trên MỘT ảnh chụp, nhiều ngày bán khác nhau) đang chỉ được canh bởi bộ test
đơn vị + smoke qua HTTP.

`AR-R5-IR-13` — **Bản ghi CŨ ghi mốc tới giây vẫn không phân giải được thứ
tự.** Với chúng, `>=` nghiêng về GIỮ TIỀN, nên một lần xác nhận sổ đầy đủ có
thể KHÔNG loại được dòng đáng loại nếu snapshot liền trước chia cùng một giây.
Hệ quả nhìn thấy được ngay (câu xác nhận nói "đã tạm loại N dòng" trong khi
tổng không đổi), đảo ngược được (nạp lại sổ là có mốc micro-giây), và nó là
chiều sai RẺ HƠN hẳn chiều còn lại. Dữ liệu mới không có vấn đề này.

## 8. Việc còn lại

- `CHECK-R5-27` — Independent Review: thuộc phiên review độc lập kế tiếp, trên
  exact HEAD `1d971de21a82f5a2ca367180de6ae257133a02b1`. Phiên repair KHÔNG tự
  đóng nó.
- `CHECK-R5-28`, `CHECK-R3-20`, `CHECK-R4-24` — không chạm.
- Hai việc reviewer nêu là **chỉ Owner nghiệm thu bằng mắt được** (phiên này
  chỉ kiểm được DOM/CSS/JS, không kiểm được hình học thật): toạ độ popover
  trên màn hình thật, và hai cột Hãng/IMEI cắt đúng một dòng. Chúng vẫn nằm ở
  checklist Owner (`S134` §9, luồng 6 và 7).
- `INTEGRATION_DECISION_REQUIRED` và điều kiện `S133`: KHÔNG đổi. Reviewer
  khuyến nghị tích hợp NGUYÊN KHỐI sau repair (gói 3 và gói 4 đều đọc
  `PeriodData` mà gói 1 định nghĩa lại, nên tách gói tạo một tổ hợp chưa ai
  chạy) — phiên này ghi lại khuyến nghị đó, quyết định vẫn thuộc Owner.
