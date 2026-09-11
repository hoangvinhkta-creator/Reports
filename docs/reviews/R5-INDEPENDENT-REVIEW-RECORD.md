# R5 — Independent Review (bản ghi review ĐỘC LẬP)

Phiên này chỉ ĐỌC, CHẠY và KIỂM. Không sửa một dòng mã sản phẩm nào, không
merge, không deploy, không đánh dấu Owner Acceptance của R3, R4 hay R5.

Task canonical: `docs/tasks/R5-doi-soat-so-bieu-do-thao-tac-danh-tinh.md`.
Bàn giao triển khai: `docs/sessions/S134-r5-doi-soat-va-danh-tinh.md`.
Kiến trúc: `docs/adr/ADR-111-absence-effective-data-imei-scope-and-brand-authority.md`.
Bàn giao review này: `docs/sessions/S135-r5-independent-review.md`.
Repair brief: `docs/tasks/R5-REPAIR-1-doi-soat-nhan-vien-va-khoi-phuc.md`.

---

## 1. Kết luận

```text
KẾT LUẬN               REPAIR_REQUIRED

EXACT HEAD ĐÃ REVIEW   Reports   949e32df7a876d1f6f8003eb5df39e3d11dcc069
                       Tracking  f958226f6127e6055eb411e4c22e12c58d09654b
NỀN TÍCH HỢP           b6756fef4b43362201a88f8fe13c45488916d3dd
NHÁNH MẶC ĐỊNH THẬT    claude/extract-upload-repo-gq2ws4

REPAIR_REQUIRED        2 finding  (FIND-R5-IR-01, FIND-R5-IR-02)
ACCEPTED_RISK          7 finding mới (AR-R5-IR-06 … AR-R5-IR-12)
AR-R5-01 … AR-R5-05    tái kiểm chứng — cả năm GIỮ NGUYÊN mức ACCEPTED_RISK

CHECK-R5-27            FAIL — Independent Review ĐÃ CHẠY ĐỦ; kết luận là
                       REPAIR_REQUIRED, nên implementation CHƯA được chấp nhận
CHECK-R5-28            NOT_TESTED — Owner nghiệm thu, KHÔNG phiên nào tự đóng
CHECK-R3-20            NOT_TESTED — phiên này KHÔNG chạm tới
CHECK-R4-24            NOT_TESTED — phiên này KHÔNG chạm tới
REPAIR CYCLE TIÊU      0 trong phiên này (ngân sách R5 vẫn 2 allowed / 0 used)
```

Hai finding bắt buộc đều rơi đúng vào nhóm `REPAIR_REQUIRED` mà brief §8 liệt
kê, và cả hai đều **tái hiện được bằng lệnh** trên chính exact HEAD:

1. `FIND-R5-IR-01` — bấm `XONG` trên một BH chưa có nhân viên hiệu lực (hoặc
   có nhiều nhân viên) **gán lại CẢ ĐƠN cho người đứng đầu danh sách**, dù
   người dùng không chạm vào ô nhân viên. Nhóm *"sửa nhầm dòng hoặc nhầm cả
   đơn"*.
2. `FIND-R5-IR-02` — một dòng đã quay lại trong sổ **không được khôi phục**
   khi lần nạp khôi phục rơi vào CÙNG MỘT GIÂY với sổ đã xác nhận đầy đủ.
   Tổng kỳ ở lại **thấp hơn thực tế vĩnh viễn**, và màn hình vẫn hứa điều
   ngược lại. Nhóm *"làm tổng tiền sai mà khó nhận biết"* + *"tạm loại hoặc
   khôi phục nhầm dòng"*.

Ngoài hai chỗ đó, năm gói của R5 **đúng như bàn giao mô tả**. Chuỗi A (trừ
mục khôi phục), B, C và E đã được kiểm trực tiếp qua route thật và không tìm
được một phép cộng sai, một dòng bị loại không có hành động xác nhận của con
người đứng sau, hay một đường nào IMEI rời khỏi tab nhân viên.

---

## 2. Điều kiện mở phiên — xác minh bằng git TRƯỚC khi kiểm

```text
$ git remote show origin | grep 'HEAD branch'
  HEAD branch: claude/extract-upload-repo-gq2ws4

$ git rev-parse origin/claude/r5-reports-tracking-deploy-o77n7t
949e32df7a876d1f6f8003eb5df39e3d11dcc069

$ git rev-parse origin/claude/extract-upload-repo-gq2ws4
b6756fef4b43362201a88f8fe13c45488916d3dd

$ git status --porcelain | wc -l
0

$ git merge-base --is-ancestor b6756fef4b43362201a88f8fe13c45488916d3dd 949e32d && echo YES
YES

$ git merge-base --is-ancestor 63a066e9 949e32d && echo YES
YES

$ git merge-base --is-ancestor 63a066e9 b6756fef4b43362201a88f8fe13c45488916d3dd && echo YES
YES

$ git log --oneline b6756fe..949e32d
949e32d S134: SHA của HEAD gồm tài liệu, cho Independent Review
19b853f S134: ghi lại tín hiệu INTEGRATION_DECISION_REQUIRED của branch authority
1117c39 R5: quyết định DEC-202, ADR-111, task, bàn giao S134 và ledger
dad8513 R5: smoke qua HTTP thật không còn đo chính cái stub của nó
3c8093f R5 §5: model canonical, Hãng/IMEI trên tab nhân viên, popover phân loại
294304d R5 §4: sửa cả BH bằng một lần bấm
1bb8554 R5 §3: biểu đồ so hai cửa sổ liền kề cùng độ dài
f106dcb R5 §2: danh sách thay đổi gọn, có nhân viên và bấm về đúng dòng
1621c96 R5 §1: sổ đã xác nhận đầy đủ tạm loại dòng biến mất khỏi mọi số liệu
```

Tracking — HEAD bàn giao KHÔNG trùng working tree của container (`main` @
`edeb827`), nên phiên này dựng **worktree review riêng** tại đúng
`f958226` thay vì đọc cây hiện có:

```text
$ git rev-parse HEAD                         # cây có sẵn của container
edeb827a7530c4ea10fa2ca542f43bbad767fad0     # ≠ HEAD bàn giao

$ git worktree add <tmp>/tracking-r5 f958226
HEAD is now at f958226 R5 §5: /api/xuat/board xuất thêm model_label và brand đã chuẩn hoá

$ git rev-parse HEAD && git status --porcelain | wc -l   # trong worktree
f958226f6127e6055eb411e4c22e12c58d09654b
0

$ git log --oneline edeb827..f958226
f958226 R5 §5: /api/xuat/board xuất thêm model_label và brand đã chuẩn hoá

$ git log --oneline f958226..edeb827
(rỗng — không có commit nào của main nằm ngoài HEAD bàn giao)
```

**Bốn khẳng định của brief §1 — ĐẠT.** Nền `b6756fe` là ancestor của HEAD R5;
R4 `63a066e9` nằm trong ancestry (và đã ở trong chính nền); chín commit của
diff đều mang tiền tố R5/S134 và không có commit lạ; Tracking đúng một commit
R5 trên `main`, đúng cặp được bàn giao.

Phân rã LOC — khẳng định của `S134` §6 tái lập được:

```text
$ git diff --numstat b6756fe..949e32d | awk '...'
docs+PROJECT: 1116
code+test  : 4220
total      : 5336
```

---

## 3. Finding bắt buộc

### FIND-R5-IR-01 · REPAIR_REQUIRED

**Bấm `XONG` gán lại CẢ ĐƠN cho nhân viên đầu danh sách khi BH chưa có nhân
viên hiệu lực hoặc đang thuộc nhiều người.**

| | |
|---|---|
| Xác suất | **CAO** trong đúng nhóm BH mà người dùng hay mở sửa nhất — đơn chưa gán nhân viên, và đơn nhiều dòng nhiều người |
| Tác động | **CAO** — dời doanh thu, lợi nhuận KPI, DS quy đổi và Target của cả một BH sang một người khác |
| Nhân viên phát hiện | **TRUNG BÌNH** — câu thông báo có nói ra, nhưng nó nói về một việc người dùng không hề yêu cầu, và nó nằm lẫn giữa các phần khác của cùng một lần lưu |
| Đường production | `POST /kinh-doanh/nhan-vien/sua-bh` → `plan_order_edit` → `store.set_employee` |

**Nguyên nhân.** `business_presentation.assignable_employee_options()` cố ý
**không có mục trống** (docstring của chính nó: *"KHÔNG có mục trống: ô này
để GÁN một dòng cho ai đó"*). Trước R5 điều đó an toàn vì ô chọn ấy có nút
gửi RIÊNG (`GÁN CẢ ĐƠN`): không ai bấm thì không có gì được gửi.

R5 §4 gộp mọi thứ về **một** nút gửi. Ô chọn nay đi cùng mọi lần lưu:

- `app/web/templates/kinh_doanh_nhan_vien.html:497-507` — `<select
  name="nhan_vien_moi" form="{{ form_id }}">`, `selected` chỉ được gắn khi
  `option.value == group.employee_value`.
- `app/web/workspace_presentation.py:579-580` — `group["employee_value"]` là
  `""` khi BH có **0 hoặc ≥2** nhân viên hiệu lực.
- Không option nào `selected` ⟹ trình duyệt gửi **option đầu tiên**.
- `app/web/server.py:2225-2235` — `chosen or None` nên chuỗi ấy đi thẳng vào
  `plan_order_edit`.
- `app/web/business_service.py:938-940` — `change_employee` chỉ hỏi *"có dòng
  nào khác tên này không"*, không hỏi *"người dùng có thật sự chọn không"*.

**Tái hiện** (probe độc lập, đi qua route web thật):

```text
$ pytest test_ir_probe_order_edit.py -q -s

  option đầu tiên = 'Hiệp'
  option được đánh dấu selected = []
  giá trị trình duyệt sẽ GỬI khi không ai chạm = 'Hiệp'
  nhân viên TRƯỚC khi bấm XONG = ['Quý', 'Vinh']
  nhân viên SAU khi bấm XONG  = ['Hiệp']
E AssertionError: BẤM XONG ĐÃ GÁN LẠI CẢ ĐƠN: ['Quý', 'Vinh'] → ['Hiệp']

  giá trị trình duyệt sẽ GỬI = 'Hiệp'
  nhân viên TRƯỚC = [None]
  nhân viên SAU   = ['Hiệp']
E AssertionError: BẤM XONG ĐÃ GÁN LẠI CẢ ĐƠN: [None] → ['Hiệp']
```

Câu thông báo trả về: `Đã lưu BH80001: nhân viên của cả đơn → Hiệp (2 dòng).`

**Expected.** Mở sửa một BH, đổi (hoặc không đổi) giá, bấm `XONG` mà không
chạm ô nhân viên ⟹ nhân viên của BH **không đổi**.
**Actual.** Toàn bộ dòng của BH chuyển sang người đứng đầu danh sách.

**Repair nhỏ nhất.** Trong bảng kê tab nhân viên, khi `group.employee_value`
rỗng, chèn một `<option value="">` đứng đầu mang nghĩa *"giữ nguyên"*. Route
đã sẵn sàng: `chosen or None` biến chuỗi rỗng thành *"không đổi nhân viên"*.
Không sửa `assignable_employee_options()` (nó còn phục vụ các bề mặt khác của
`OD-5`); chèn mục trống ở đúng template của form cấp BH.

**Test cần thêm.** Trong `tests/test_r5_order_edit_form.py`: dựng một BH có
hai nhân viên khác nhau và một BH không có nhân viên nào; đọc `<select>` từ
chính HTML, suy ra giá trị mặc định trình duyệt sẽ gửi, POST đúng giá trị đó,
rồi khẳng định tập nhân viên của BH **không đổi**.

---

### FIND-R5-IR-02 · REPAIR_REQUIRED

**Dòng đã quay lại trong sổ KHÔNG được khôi phục khi lần nạp khôi phục rơi
vào cùng một GIÂY với sổ đã xác nhận đầy đủ — tổng kỳ ở lại thấp hơn thực tế
vĩnh viễn.**

| | |
|---|---|
| Xác suất | **THẤP** trong thao tác tay (cần hai lần nạp cách nhau dưới một giây), nhưng **KHÔNG có hàng rào nào**, và cao hơn hẳn ở mọi đường nạp tự động/kịch bản |
| Tác động | **CAO** — doanh thu, lợi nhuận, DS quy đổi, Target, biểu đồ, export và vân tay chốt kỳ đều thiếu đúng số tiền của dòng đó, **theo hướng THẤP HƠN** |
| Nhân viên phát hiện | **THẤP** — không ai đi tìm số tiền mình không biết là mình đang thiếu; và màn hình vẫn hứa *"nạp lại một sổ có chứa dòng đó thì cảnh báo tự mất và các con số tự khôi phục"*, nên người dùng đã làm đúng việc được bảo rồi tin là xong |
| Khôi phục thủ công | **KHÔNG CÓ** — danh sách "Không còn trong file đầy đủ" cố ý không có nút KHÔI PHỤC |
| Đường production | `history_writer.write_run_history` → `source_snapshot.created_at` → `SnapshotRepository._with_absence_state` → `removed_candidate_keys` → `BusinessReportService._removed_in_source` → `PeriodData.lines` → MỌI chỉ tiêu |

**Nguyên nhân — hai mảnh, mỗi mảnh đúng riêng, sai khi ghép.**

1. `app/web/history_writer.py:136` ghi mốc thời gian của snapshot bằng
   `datetime.now(timezone.utc).isoformat(timespec="seconds")` — **độ phân
   giải GIÂY**. Hai snapshot cách nhau dưới một giây mang **cùng một chuỗi**.
2. `app/web/history_store.py:1408-1411` quyết định "dòng đã quay lại chưa"
   bằng một phép so **NGẶT**: `reappeared = seen[0] > anchor`. Bằng nhau ⟹
   **chưa quay lại** ⟹ cờ còn hiệu lực ⟹ R5 loại dòng khỏi mọi con số.

Chú thích ngay trên phép so ấy nói rõ vì sao nó nghiêng về phía "giữ cờ":

> *"nghiêng về phía an toàn có nghĩa là GIỮ cờ ở trạng thái còn hiệu lực:
> một cảnh báo thừa để người dùng tự kiểm còn hơn âm thầm giấu một sự vắng
> mặt thật. **Không con số nghiệp vụ nào phụ thuộc vào nhãn này** (hiện trạng
> và tổng tiền không bao giờ do cờ quyết định)."*

Câu trong ngoặc **đã hết đúng từ R5 §1**: `removed_candidate_keys()` đọc đúng
`is_active` đó, và `_removed_in_source()` dùng nó để rút dòng khỏi `lines`.
Chiều "an toàn" vì thế **đảo ngược** — giữ cờ nay có nghĩa là trừ tiền — mà
phép so và chú thích không được tính lại. Đây là gốc rễ, không phải một lỗi
đánh máy.

**Vì sao bộ kiểm hiện có không bắt được.**
`tests/test_r5_removed_lines.py::test_a_line_that_comes_back_is_restored_to_the_totals_by_itself`
truyền tay ba mốc `2026-10-01`, `2026-10-02`, `2026-10-03` — cách nhau MỘT
NGÀY. Đường production thì chỉ có độ phân giải GIÂY. Fixture vì thế không bao
giờ đi vào nhánh sai.

**Tái hiện A — cô lập, chỉ đổi MỐC THỜI GIAN:**

```text
$ pytest test_ir_probe_absence_clock.py -q -s

  [CÁCH NGÀY  (điều kiện của test R5 hiện có)] tổng = 12000000  đơn = ['BH1', 'BH2']  tạm loại = []
  [SAU 1 GIÂY]                                 tổng = 12000000  đơn = ['BH1', 'BH2']  tạm loại = []
  [CÙNG GIÂY (độ phân giải THẬT của production)] tổng = 8000000  đơn = ['BH1']  tạm loại = ['BH2']

E AssertionError: [CÙNG GIÂY] dòng ĐÃ quay lại trong sổ nhưng KHÔNG được cộng lại
1 failed, 2 passed
```

**Tái hiện B — qua HTTP server THẬT, không dựng mốc thời gian nào.**
Chạy smoke xuyên repo (§7 dưới đây) mà **bỏ** lệnh chờ 1,2 giây trước lần nạp
khôi phục: ba snapshot rơi vào cùng một giây và bước §9.3 hỏng.

```text
  tổng Giá bán sau sổ đầy đủ  = 15.000.000
  tổng Giá bán sau xác nhận   = 11.000.000
  tổng Giá bán sau khi nạp lại = 11.000.000     ← phải là 15.000.000
  FAIL  dòng quay lại ⟹ tổng TỰ khôi phục (§9.3)
  FAIL  cảnh báo TỰ mất, không cần quyết định Owner mới
```

Trạng thái database lúc đó (ba snapshot, một mốc):

```text
created_at = '2026-09-08T17:25:41+00:00'   day-du.xlsx      HEADER_CONSISTENT
created_at = '2026-09-08T17:25:41+00:00'   thieu.xlsx       CONFIRMED_COMPLETE
created_at = '2026-09-08T17:25:41+00:00'   day-du-2.xlsx    HEADER_CONSISTENT
snapshot_line: BH9002 CÓ trong day-du.xlsx và day-du-2.xlsx
reconciliation_flag: REMOVED_IN_SOURCE_CANDIDATE BH9002 — vẫn còn hiệu lực
```

Chỉ cần chèn `sleep(1.2)` trước lần nạp khôi phục là cả hai bước chuyển sang
PASS và tổng trở về `15.000.000`. Không có gì khác thay đổi.

**Expected.** Một dòng có mặt trong một snapshot nạp SAU snapshot đã xác nhận
đầy đủ thì hết bị tạm loại, bất kể hai lần nạp cách nhau bao lâu.
**Actual.** Cách nhau dưới một giây ⟹ dòng ở lại ngoài mọi con số, không có
đường quay lại nào ngoài việc nạp thêm một sổ nữa ở một giây khác.

**Repair nhỏ nhất — hai lựa chọn, khuyến nghị lấy CẢ HAI.**

1. *(bắt buộc — đóng gốc rễ)* `app/web/history_writer.py:136`:
   `timespec="seconds"` → `timespec="microseconds"`. So sánh chuỗi ISO vẫn
   xếp đúng thứ tự với các bản ghi cũ (`…T00:00:00` < `…T00:00:00.000001`),
   nên không cần backfill và không có migration.
2. *(rẻ, và đúng theo cấu tạo)* `app/web/history_store.py:1408`:
   `seen[0] > anchor` → `seen[0] >= anchor`. An toàn vì snapshot dựng cờ theo
   định nghĩa **không chứa** khoá ấy, nên nó không bao giờ có mặt trong
   `_latest_membership` của chính khoá đó — `>=` không thể được thoả bởi
   chính nó. Trường hợp biên còn lại (một snapshot CÓ chứa khoá, nạp cùng
   giây nhưng TRƯỚC sổ đã xác nhận) đổi lỗi từ *"âm thầm trừ tiền"* sang
   *"vẫn tính, kèm một cảnh báo"* — đúng chiều an toàn mà chú thích gốc mô tả.

Đồng thời **sửa chú thích** ở `history_store.py:1405-1407`: câu *"Không con
số nghiệp vụ nào phụ thuộc vào nhãn này"* nay sai, và nó chính là lập luận đã
dẫn tới phép so ngặt.

**Test cần thêm.** Tham số hoá lại
`test_a_line_that_comes_back_is_restored_to_the_totals_by_itself` theo ba mốc
`CÁCH NGÀY · SAU 1 GIÂY · CÙNG GIÂY`, và thêm một khẳng định trên chính
`history_writer` rằng mốc snapshot mang độ phân giải nhỏ hơn giây.

---

## 4. Rủi ro chấp nhận MỚI

### AR-R5-IR-06 — cửa sổ 30 ngày không trùng tháng 31/28/29 ngày

Cửa sổ hiện tại ở mức Ngày luôn dài đúng 30 mốc và kết thúc ở ngày cuối kỳ,
nên với tháng 31 ngày **ngày 1 rơi sang cửa sổ SO SÁNH**, và với tháng 2 cửa
sổ với sang tháng 1:

```text
  kỳ 10/2026 · neo = 2026-10-31
  cửa sổ hiện tại = 2026-10-02 → 2026-10-31
  cửa sổ so sánh  = 2026-09-02 → 2026-10-01
  01/10 nằm trong cửa sổ hiện tại? False

  kỳ 02/2026 · cửa sổ hiện tại = 2026-01-30 → 2026-02-28
```

Đây là hệ quả CÓ CHỦ ĐÍCH của `DEC-R5-02` (hai cửa sổ phải cùng độ dài), và
màn hình **nói ra khoảng ngày thật** trong `chart-scope`. Chỉ tiêu kỳ phía
trên KHÔNG bị cắt theo cửa sổ (đã kiểm: chart đọc `service.period()` toàn bộ,
KPI đọc `view["data"]` của kỳ). Rủi ro còn lại là một người đối chiếu Σ cột
biểu đồ với ô doanh thu tháng và thấy lệch đúng phần ngày đầu tháng.

*Ghi chú về câu chữ:* `CHECK-R5-18` phát biểu *"Σ cửa sổ hiện tại = chỉ tiêu
kỳ"*. Điều đó chỉ đúng với **tháng 30 ngày**, và fixture của bài kiểm tương
ứng đúng là tháng 9. Nên sửa câu chữ của check, không phải sửa mã.

### AR-R5-IR-07 — `modelCua` cắt chuỗi THÔ theo độ dài của `cat` THÔ

`Tracking/src/index.js` so hai chuỗi ĐÃ CHUẨN HOÁ
(`chuanSo(name).startsWith(chuanSo(cat) + ' ')`) rồi cắt chuỗi **thô** bằng
`name.slice(cat.length)`. `chuanSo` gom mọi cụm ký tự không phải chữ/số thành
MỘT khoảng trắng, nên khi `cat` và phần đầu của `name` khác nhau về số khoảng
trắng/dấu câu, hai độ dài lệch nhau và nhãn bị cắt lệch (ví dụ
`cat="Máy giặt LG"`, `name="Máy giặt  LG FV1409S4W"` ⟹ `"G FV1409S4W"`).

Chỉ ảnh hưởng **nhãn hiển thị**. `model_label` không tham gia nhận diện
(`_match_field` chỉ đọc `tracking_code`/`name`/`alt` — đã kiểm bằng mã
nguồn), không đổi `product_key`, không đổi một đồng nào. Nhãn hỏng thì nhìn
là thấy. Sửa đúng là cắt theo độ dài của **tiền tố đã chuẩn hoá** ánh xạ
ngược về chuỗi thô, hoặc dùng regex trên chính chuỗi thô.

### AR-R5-IR-08 — `modelCua` không kiểm biên PHẢI của mã

Quy tắc 2 tìm mã bảng giá trong `name` bằng `indexOf` và chỉ kiểm ký tự đứng
**TRƯỚC** là dấu ngăn. Một mã là tiền tố của một từ dài hơn trong tên sẽ khớp
và nhãn bắt đầu từ giữa từ đó. Cùng nhóm tác động với `AR-R5-IR-07`: hiển thị
thuần, nhìn là thấy.

### AR-R5-IR-09 — `/run` nuốt MỌI ngoại lệ thành HTTP 400 "kiểm tra workbook"

`app/web/server.py:3180-3184` bắt `except Exception` và trả 400 kèm câu *"Không
thể tạo báo cáo. Kiểm tra workbook và thử lại."* — một câu đổ lỗi cho tệp của
người dùng. `app/web/server.py` **không có một dòng logging nào**
(`grep -n "logger\|logging\|traceback" app/web/server.py` → rỗng), nên
traceback biến mất hoàn toàn.

Đây là **lỗi có trước R5** (đo trên `b6756fe`), và commit `dad8513` chỉ sửa
cái stub của smoke chứ không sửa nhánh nuốt lỗi. Phiên review này va vào nó
**hai lần** khi dựng smoke: một `OwnerUsabilityError` thật (câu đúng, 400
đúng) và một `ValueError` lập trình bị che thành *"Báo cáo đã tạo nhưng không
lưu được"* (500) — cả hai lần đều phải tự chèn `traceback.print_exc()` mới
biết chuyện gì xảy ra.

Không nằm trong Scope Lock của R5 và không làm sai một con số nào, nên KHÔNG
mở repair ở đây. Khuyến nghị cho một task vận hành riêng: giữ nguyên câu cho
người dùng, nhưng ghi traceback ra log, và tách `OwnerUsabilityError` (400,
lỗi dữ liệu) khỏi mọi ngoại lệ khác (500, lỗi hệ thống).

### AR-R5-IR-10 — chú thích đã hết đúng ở `_with_absence_state`

Xem `FIND-R5-IR-02`. Ghi riêng vì kể cả khi repair chọn phương án đổi mốc
thời gian, câu chú thích vẫn phải sửa: để nguyên là để lại đúng lập luận sẽ
dẫn người sau quay lại phép so ngặt.

### AR-R5-IR-11 — docstring hứa một khẳng định không có trong thân bài

`tests/test_employee_workspace_ux.py::test_the_workspace_never_renders_a_prohibited_personal_field`
bỏ `assert "imei" not in html.lower()` (đúng — nhãn nút nay chứa chữ ấy), và
docstring nói *"Ở đây chỉ còn khẳng định điều vẫn đúng — không có một giá trị
mã máy nào lọt ra khi sổ không ghi mã máy nào"*. Thân bài **không có** khẳng
định đó; nó chỉ còn kiểm `Vũ Hạnh Ly` và `note_raw`.

Nội dung thì KHÔNG mất: `tests/test_r5_imei_boundary.py` canh theo GIÁ TRỊ mã
máy trên bảy trang, trên export Excel và trên trang snapshot. Đây là lệch
giữa lời và mã, không phải một lỗ hổng.

### AR-R5-IR-12 — `tools/smoke/r1_daily_min_smoke.py` SẬP giữa chừng

`S134` §10 liệt kê nó là một lệnh tái lập của Independent Review. Chạy thật:

```text
$ .venv/bin/python tools/smoke/r1_daily_min_smoke.py \
      tests/fixtures/daily_min/tracking_contract_export.json
... 15 khẳng định PASS ...
=== NGÀY BÁN KHÁC, CÙNG ẢNH CHỤP ===
AttributeError: 'NoneType' object has no attribute 'value'   (dòng 167)
exit=1
```

Đo trên `b6756fe`: **hỏng y hệt, exit=1** ⟹ lỗi baseline cũ, KHÔNG phải hồi
quy của R5. Nhưng nó cùng một lớp lỗi với cái mà `dad8513` vừa sửa cho smoke
kia — một công cụ kiểm hỏng lặng lẽ — và phần khẳng định cuối của nó chưa bao
giờ chạy. Không chặn R5 (các bất biến R1 đã được `r1_web_upload_smoke.py` phủ
đủ, xem §6), nhưng `S134` §10 không nên liệt kê một lệnh đang hỏng mà không
nói ra.

---

## 5. Tái kiểm chứng `AR-R5-01` … `AR-R5-05`

| Mã | Kết luận của phiên review | Bằng chứng |
|---|---|---|
| `AR-R5-01` bản chiếu danh mục trên đĩa ephemeral | **GIỮ ACCEPTED_RISK** | xem dưới |
| `AR-R5-02` hai route cũ còn tồn tại | **GIỮ** — cả hai gọi đúng `store.set_purchase_price`/`set_employee`; không có thẩm quyền thứ hai (đọc mã nguồn) |
| `AR-R5-03` danh sách hãng đóng, chưa đầy đủ | **GIỮ** — hãng ngoài danh sách ra `null`; `hangCua` ghép NGUYÊN TỪ, hai hãng trên một dòng ⟹ `null` |
| `AR-R5-04` `current_totals()` đếm cả dòng tạm loại | **GIỮ** — trang nay nói ra bằng `data-metric="current-totals-scope"` và chỉ đường tới con số kinh doanh |
| `AR-R5-05` toạ độ popover chưa kiểm bằng trình duyệt | **GIỮ, và cần Owner nghiệm thu bằng mắt** — xem §8 |

**`AR-R5-01` — ba điều kiện của brief §6 đều ĐẠT, kiểm bằng mã Tracking thật:**

```text
  PASS  công cụ capture production chụp được danh mục
  PASS  capture MANG model_label/brand do Tracking chuẩn hoá
  PASS  loader Reports đọc đúng model/brand của đúng mã
  PASS  mã Tracking không dám khẳng định ⟹ None, KHÔNG đoán
  PASS  bản chiếu hiển thị giữ đúng hãng của đúng mã
  PASS  MẤT file bản chiếu ⟹ {} (không lỗi, không đoán)
```

- Mất file ⟹ `catalog_display.read()` trả `{}` ⟹ `label_of` trả `None` ⟹
  bảng kê rơi về **mã Tracking**, cột Hãng thành `—`. Không 500.
- Không mapping nào đổi: `model_label`/`brand` không có mặt trong
  `_match_field`, nên `product_key`, doanh thu, giá nhập và lợi nhuận không
  phụ thuộc bản chiếu.
- Lần pull hợp lệ kế tiếp ghi lại file (`server._tracking_snapshot()` →
  `catalog_display.write`).
- **Không nâng lên REPAIR_REQUIRED.** Thêm một quan sát làm nhẹ nó hơn nữa:
  `brand_identity.canonical_brand` — nguồn hãng TRƯỚC R5 — đọc trường `brand`
  trên `CanonicalProductIdentity`, và value object ấy chỉ có `namespace` +
  `source_product_code`. Nghĩa là trước R5 trang thương hiệu **luôn** không
  có hãng. Mất bản chiếu chỉ đưa màn hình về đúng trạng thái tiền-R5.

---

## 6. `INTEGRATION_DECISION_REQUIRED` và điều kiện `S133`

`scripts/branch_authority_check.sh` chạy lại trên đúng nhánh bàn giao:

```text
DEFAULT_BRANCH       : claude/extract-upload-repo-gq2ws4
DEFAULT_TIP          : b6756fef4b43362201a88f8fe13c45488916d3dd
HEAD_SHA             : 949e32df7a876d1f6f8003eb5df39e3d11dcc069
WORKTREE             : CLEAN
UPSTREAM             : origin/claude/r5-reports-tracking-deploy-o77n7t
behind upstream      : 0 commit
ahead  default       : 9 commit
behind default       : 0 commit
divergence days      : 0
cumulative LOC       : 5336
DIVERGENCE           : INTEGRATION_DECISION_REQUIRED [ loc>5000 ]
AUTHORITY            : BRANCH_WITH_UPSTREAM
RESULT               : AUTHORITY_OK
```

**Phân loại: QUYẾT ĐỊNH GOVERNANCE, không phải dấu hiệu code cần chia nhỏ.**
Không tìm được một lỗi luồng chính nào **do khối lượng** gây ra: nhánh không
lệch một commit nào so với mặc định, `divergence days = 0`, phần code+test là
`4220` dòng — **dưới ngưỡng**, và ngưỡng chỉ bật sau commit tài liệu cuối
cùng. Hai finding bắt buộc ở §3 đều là lỗi lập luận cục bộ, không phải hệ quả
của việc gộp năm gói vào một nhánh.

**Khuyến nghị phương án tích hợp cho Owner: phương án 1 (NGUYÊN KHỐI), sau
repair.** Lý do:

- Năm gói **không** độc lập như phương án 2 giả định: gói 3 (biểu đồ) đọc
  `PeriodData` mà gói 1 định nghĩa lại, và gói 4 (`plan_order_edit`) đọc
  `data.removed_in_source` của gói 1. Tách gói 1 ra riêng để lại các gói kia
  ở một trạng thái chưa từng được kiểm cùng nhau.
- Chi phí tách là một lần rebase và **một vòng review nữa** trên một tổ hợp
  chưa ai chạy; lợi ích là giảm một con số LOC vốn đã dưới ngưỡng ở phần code.
- Điều kiện `S133` (Owner nghiệm thu R3/R4 trên production) **vẫn phải giữ**
  là điều kiện TRƯỚC merge. Phiên này KHÔNG có bằng chứng Owner đã nghiệm thu,
  nên `CHECK-R3-20` và `CHECK-R4-24` giữ nguyên `NOT_TESTED` và **không**
  được đóng bởi phiên này.

Thứ tự đúng: repair hai finding → review lại (repair cycle 1/2) → Owner
nghiệm thu R3/R4 trên production → merge nguyên khối → Owner nghiệm thu R5.

---

## 7. Bằng chứng — đã TỰ CHẠY

Mọi con số dưới đây do phiên này chạy, không chép từ `S134`.

### 7.1 Reports — pytest

```text
$ .venv/bin/python -m pytest -q
1 failed, 3222 passed, 12 skipped in 205.36s
FAILED tests/test_105d_boundaries.py::TestG25GoldenBaselineUnchanged::
       test_protected_golden_artifacts_match_the_task_105e_review_base
       AssertionError: fatal: bad object 740f396acb11cf279f303f09ea22dffd0ca95462
```

Đây là **tạo tác môi trường**, không phải hồi quy: clone của container là
SHALLOW (`git rev-list --count HEAD` → 72) nên object base của bài đó vắng
mặt. Sau `git fetch origin 740f396…`:

```text
$ .venv/bin/python -m pytest "tests/test_105d_boundaries.py::TestG25GoldenBaselineUnchanged" -q
3 passed in 0.30s
```

⟹ **full regression = 3223 passed, 12 skipped** — khớp chính xác con số
`S134` §4 báo cáo.

```text
$ ... pytest tests/test_r5_removed_lines.py tests/test_r5_change_list.py \
      tests/test_r5_two_window_chart.py tests/test_r5_order_edit_form.py \
      tests/test_r5_product_identity_fields.py tests/test_r5_imei_boundary.py \
      tests/test_r5_workspace_identity_ux.py -q
77 passed in 8.69s

$ ... pytest tests/test_snapshot_absence.py tests/test_history_coverage_confirmation.py -q
55 passed in 0.99s

$ ... pytest tests/test_r2_web_workflow.py tests/test_r3_web_workflow.py \
      tests/test_employee_workspace_ux.py tests/test_business_vertical.py -q
170 passed in 21.24s

$ ... pytest -q -k "identity or catalog"
257 passed, 1 skipped, 2977 deselected in 13.88s

$ ... pytest -q -k "pricing or daily_min or dailymin"
164 passed, 1 skipped, 3070 deselected in 2.89s

$ ... pytest tests/test_business_boundaries.py tests/test_phb06_brand_reporting.py \
      tests/test_r2_product_classification.py tests/test_r3_import_binding.py \
      tests/test_r3_line_types.py tests/test_r4_evaluation_metrics.py \
      tests/test_r4_evaluation_web.py -q
227 passed in 8.69s

$ ... pytest tests/test_r3_export_and_period_close.py -q
19 passed in 1.14s
```

### 7.2 Reports — smoke qua HTTP server thật

```text
$ .venv/bin/python tools/smoke/r1_web_upload_smoke.py --tracking-repo <worktree f958226>
  PASS  hợp đồng daily-min-v1 ĐƯỢC GỌI đúng một lượt
  PASS    · và hỏi đúng tập mã suy từ sổ
  PASS    · và đúng khoảng NGÀY BÁN, không phải ngày nạp sổ
  PASS  A. đơn 03/09 nạp 30/09 → 6.800.000 (giá NGÀY BÁN)
  PASS  A. KHÔNG lấy giá hiện tại 30/09
  PASS  A. KHÔNG lấy giá ngày 04/09
  PASS  A. KHÔNG rơi về lịch sử tp/ton cũ
  PASS  A. nhãn nguồn = TRACKING_DAILY_MIN
  PASS  B. TON_KHO thắng → 5.000.000
  PASS  C. hết hàng → KHÔNG có giá (không phải 0)
  PASS  C. lợi nhuận KHÔNG bằng doanh thu
  PASS  bằng chứng run trỏ về đúng lần chụp đã định giá
  PASS  capture tạm KHÔNG ở lại trên đĩa sau lần chạy
KẾT QUẢ SMOKE: TẤT CẢ PASS
```

Bản sửa `dad8513` được xác nhận là **đúng phạm vi**: nó chỉ đổi lambda stub
thành `**kwargs` trong công cụ kiểm, không chạm mã sản phẩm, và không che một
`TypeError` nào của production. (Nhánh nuốt lỗi của `server.py` thì vẫn còn —
`AR-R5-IR-09`.)

### 7.3 Tracking — trên worktree `f958226`

```text
$ node kiem/hang-va-model.js
29 đạt, 0 hỏng

$ node kiem/xuat-baocao.js
174 đạt, 0 hỏng

$ npm test
61 bộ · 2767 đạt · 0 hỏng · 2 bỏ qua

$ npm run build
61 bộ · 2767 đạt · 0 hỏng · 2 bỏ qua
Đã dựng bản phục vụ vào ./dist
  7 file, xén chú thích 1 file HTML
  658 KB → 411 KB  (bớt 37%)
```

Khớp `S134` §5.

### 7.4 Governance validators

```text
$ validate_evidence.py          EVIDENCE VALIDATION: PASS — 161 record
$ validate_project_state.py     PROJECT STATE: PASS
$ validate_structure.py         GOVERNANCE STRUCTURE: PASS — 21 path
$ validate_task_completion.py   TASK COMPLETION: PASS — 14 DONE task
$ validate_reference_integrity.py
REFERENCE INTEGRITY: FAIL
Quét 277 file .md
3 reference không phân giải được:
- docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> /README.md
- docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> CODE_OF_CONDUCT.md
- docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> CONTRIBUTING.md
```

Chạy **cùng validator trên worktree tại `b6756fe`**:

```text
REFERENCE INTEGRITY: FAIL
Quét 271 file .md
3 reference không phân giải được:
- docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> /README.md
- docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> CODE_OF_CONDUCT.md
- docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> CONTRIBUTING.md
```

**Ba reference giống hệt ⟹ lỗi baseline cũ, KHÔNG phải lỗi R5.** Khẳng định
của `S134` §6 xác minh được.

---

## 8. Smoke xuyên repo do phiên review tự dựng

`tools/smoke/r1_web_upload_smoke.py` **không** đáp ứng hai yêu cầu của brief
§9, và điều đó được phát hiện bằng cách đọc chính nó:

- nó dùng `app.test_client()` cho phía Reports (`tools/smoke/r1_web_upload_smoke.py:226`),
  HTTP server thật chỉ đóng vai **Tracking**;
- payload `board` của nó là **một dict Python gõ tay** (`get_payload()`), không
  mang `model_label`/`brand`, nên hợp đồng R5 §5 xuyên repo chưa từng được
  chạy đầu-cuối.

Phiên này vì thế dựng một smoke riêng đóng đúng hai khoảng trống ấy:

1. `board` do **chính mã Tracking** sinh — cắt `chieuBoard`/`hangCua`/
   `modelCua` ra khỏi `src/index.js` bằng đúng kỹ thuật của
   `kiem/hang-va-model.js`, chạy trên một bảng giá THÔ có `cat`, `p`, `tp`,
   `q`, NCC, ghi chú và link;
2. Reports chạy sau **`werkzeug.serving.make_server`** trên `127.0.0.1`, mọi
   request đi qua socket bằng `urllib`; history store dựng bằng
   `alembic upgrade head` trên một SQLite thật, không `create_all_for_test`.

```text
=== 1. TRACKING sinh /api/xuat/board ===
{"65S20M2": {"name": "Tivi Sony K-65S20M2", "alt": ["TV65SONY"],
             "model_label": "K-65S20M2", "brand": "Sony"},
 "NR-BX471": {..., "model_label": "NR-BX471", "brand": "Panasonic"},
 "FV1409S4W": {..., "model_label": "FV1409S4W", "brand": "LG"},
 "HANG-LA-01": {..., "model_label": null, "brand": null}}

  PASS  công cụ capture production chụp được danh mục
  PASS  capture MANG model_label/brand do Tracking chuẩn hoá
  PASS  capture KHÔNG mang "cat" / "p" / "tp" / "q" / "ncc" / "note" / "link"
  PASS  capture KHÔNG mang "Tivi Sony\"" / "tinphat.vn" / "Tuấn Ngoan"
  PASS  loader Reports đọc đúng model/brand của đúng mã
  PASS  mã Tracking không dám khẳng định ⟹ None, KHÔNG đoán
  PASS  bản chiếu hiển thị giữ đúng hãng của đúng mã
  PASS  MẤT file bản chiếu ⟹ {} (không lỗi, không đoán)

=== 2. REPORTS sau WSGI HTTP server THẬT ===
  PASS  alembic upgrade head (production path)
  PASS  POST /run (sổ đầy đủ) → HTTP 302
  tổng Giá bán sau sổ đầy đủ = 15.000.000
  PASS  BH9002 có mặt trong bảng kê
  PASS  POST /run (sổ THIẾU BH9002) → HTTP 302
  PASS  sổ CHƯA xác nhận: tổng KHÔNG đổi (§9.1)
  PASS  BH9002 vẫn nằm trong bảng kê
  PASS  POST xác-nhận-đầy-đủ → HTTP 302
  câu thông báo: … 1 dòng cũ trong khoảng này không còn trong sổ vừa xác nhận
                 nên đã được TẠM LOẠI khỏi mọi con số kinh doanh …
  tổng Giá bán sau xác nhận  = 11.000.000
  PASS  sổ ĐÃ xác nhận: tổng GIẢM (§9.2)
  PASS  khối “Không còn trong file đầy đủ” xuất hiện
  PASS  BH9002 nằm trong danh sách tạm loại
  PASS  GET export → HTTP 200
  PASS  GET trang báo cáo (biểu đồ) → HTTP 200
  PASS  POST /run (nạp lại sổ có BH9002) → HTTP 302
  tổng Giá bán sau khi nạp lại = 15.000.000
  PASS  dòng quay lại ⟹ tổng TỰ khôi phục (§9.3)     ← CHỈ khi cách nhau > 1 giây
  PASS  cảnh báo TỰ mất, không cần quyết định Owner mới

=== 2b. SỬA CẢ BH BẰNG MỘT LẦN BẤM ===
  PASS  POST /run (BH9004 hai dòng) → HTTP 302
  PASS  form cấp BH có ĐÚNG 2 ô giá (2)
  PASS  đúng MỘT form gửi cho cả BH
  PASS  XONG là nút submit của form cấp BH
  PASS  payload có một ô sai ⟹ KHÔNG ô nào được ghi (ô 1 = [''])
  PASS  giao diện KHÔNG báo thành công
  PASS  POST sửa-bh hợp lệ → HTTP 302   ("Đã lưu BH9004: 2 giá nhập.")
  PASS  cả HAI giá được lưu ([['6.000.000'], ['3.500.000']])
  PASS  create_app lại vẫn giữ nguyên (persistence)
  PASS  khoá dòng của BH khác KHÔNG sửa được (BH9001 = [''])

=== 3. PHẠM VI IMEI ===
  PASS  IMEI CÓ trên tab nhân viên
  PASS  IMEI KHÔNG có trên trang báo cáo / thương hiệu / dữ liệu / snapshot

=== 4. MODEL / HÃNG TRÊN BẢNG KÊ ===
  PASS  cột Hãng có mặt
  PASS  hai cột mặc định ẨN qua class col-optional
  PASS  dòng CHƯA phân loại giữ TÊN THÔ (không đoán hãng)

=== 5. POPOVER PHÂN LOẠI ===
  PASS  app.js neo popover theo toạ độ click
  PASS  app.js đóng popover bằng Escape
  PASS  app.js xử lý mở popover mà không tải lại trang

KẾT QUẢ SMOKE: 55/55 PASS
```

**Phần visual CHƯA kiểm và cần Owner nghiệm thu bằng mắt** (đúng như brief §9
cho phép ghi riêng): hình học thật của popover ở một kích thước màn hình cụ
thể (tràn viewport, không bắt cuộn lên), và việc hai cột hẹp cắt đúng MỘT
dòng mà không làm hàng cao lên. Phiên này chỉ kiểm được DOM/CSS/JS:
`.identify-pop.is-anchored` là `position: fixed` có kẹp `PAD = 8px` hai
chiều; `.col-narrow` là `max-width: 96px; white-space: nowrap; overflow:
hidden; text-overflow: ellipsis` với `title` mang nội dung đầy đủ; và tầng
`fetch`/`swapContent` của `app.js` khôi phục `window.scrollY` sau mỗi lần
thay nội dung, nên mở popover không tải lại trang và không nhảy lên đầu.

---

## 9. Năm chuỗi — kết quả từng mục

### Chuỗi A — file đầy đủ và dòng biến mất

| Mục | Kết quả |
|---|---|
| 1. Sổ chưa xác nhận: dòng vẫn tính, cảnh báo nói rõ chưa đủ căn cứ | PASS (smoke §9.1 + `test_an_unconfirmed_snapshot_never_removes_a_line`) |
| 2. Sổ `CONFIRMED_COMPLETE`: dòng bị tạm loại, lịch sử không xoá, có trong danh sách riêng | PASS (smoke §9.2; `test_nothing_is_hard_deleted_when_a_line_is_dropped`) |
| 3. Dòng tạm loại không góp vào 12 chỉ tiêu | PASS — `PeriodData.totals` cộng trên `lines`, và ba tập rời nhau (mục 8) |
| 4. Mất TRỌN dòng ⟹ BH rời khỏi số đơn | PASS (`test_a_confirmed_complete_snapshot_drops_the_missing_line_from_every_figure`, smoke) |
| 5. Mất MỘT PHẦN ⟹ phần còn lại đúng | PASS |
| 6. Dòng quay lại ⟹ tự khôi phục | **FAIL — `FIND-R5-IR-02`** khi hai lần nạp trong cùng một giây |
| 7. Phạm vi ngày | PASS — cờ chỉ dựng cho dòng có `sale_date` TRONG khoảng đã xác nhận (SQL ở `_absent_keys_in_range`); bước R đọc membership của CHÍNH snapshot ấy nên hai khoảng chồng lấn không loại nhầm |
| 8. Ba tập rời nhau và reconciliation được | PASS — probe: `lines=['BH1'] excluded=['BH3'] removed=['BH2']`, hợp của ba tập = tập ban đầu, tổng `12.500.000 → 8.000.000` |

*Về mục 7, một biên còn để ngỏ nhưng KHÔNG mở finding:* nạp lại một sổ CŨ HƠN
(xuất trước) sau khi đã xác nhận một sổ mới hơn sẽ khôi phục dòng, vì thứ tự
là thứ tự NẠP chứ không phải thứ tự XUẤT. Đó là ngữ nghĩa đã có từ PRA-002,
nó sai theo chiều **cao hơn** (nhìn thấy được), và cần một người chủ động nạp
một tệp lỗi thời.

### Chuỗi B — danh sách thay đổi và tra cứu

Cả sáu mục PASS. Đáng ghi:

- `delivery_cost`/`imei` **ở lại** trong `line_fingerprint` và `detail_json`
  dưới database (`test_the_source_version_and_the_fingerprint_still_carry_both_fields`
  khẳng định `count(order_line_source_version) == before + 1` và
  `set(flag["detail_json"]) == {"delivery_cost", "imei"}`), chỉ tầng trình
  bày lọc. Số "Cần soi" = 0 và không mục nào được liệt kê.
- Thay đổi hỗn hợp: `sell_price` vẫn hiện, `delivery_cost` bị ẩn.
- Cột "Phiên bản" rời khỏi UI; hai version id còn nguyên trong audit
  (`test_the_two_version_ids_are_still_in_the_audit_record`).
- Deep link `…&sheet=noi-thanh#bh-BH72707` — neo `id="bh-{{ group.order_key }}"`
  tồn tại thật ở `kinh_doanh_nhan_vien.html:391`.
- Cờ không còn dòng hiện hành ⟹ `Không còn trong kỳ hiện tại`, và **không có**
  `data-metric="flag-link"`. Không đoán nhân viên.

### Chuỗi C — biểu đồ hai kỳ

32 khẳng định probe PASS trên bốn mức × sáu ngày neo biên (28/29/30/31 ngày,
năm nhuận, đầu tháng):

- hai cửa sổ **cùng độ dài**, **không chồng nhau**, và **liền kề** — kiểm
  bằng cách dựng một cửa sổ `2×size` rồi khẳng định nó bằng đúng
  `prev + current`;
- thiếu bằng chứng ⟹ `revenue is None` (gap), không phải 0;
- một khoảng đã xác nhận phủ **MỘT PHẦN** một tháng ⟹ mốc tháng đó vẫn là
  gap; chỉ mốc nằm TRỌN trong một khoảng mới được vẽ 0;
- mức Năm không có cửa sổ so sánh (`paired_series` trả `None`);
- `anchor_date` đọc từ **dữ liệu** hoặc từ kỳ, **không** từ `date.today()` —
  nên không có phụ thuộc timezone nào để hỏng ở `Asia/Ho_Chi_Minh`;
- một trục tương đối dùng chung (`_slot_x(index, size)`) cho cả hai chuỗi,
  một trần tròn dùng chung, nên hai đường không lệch bucket và không tự chuẩn
  hoá theo đỉnh riêng;
- legend phân biệt bằng **nét đứt + độ dày + độ mờ**, không chỉ bằng màu;
  tooltip của mỗi chấm mở đầu bằng tên cửa sổ (`_slot_title`);
- **không có công thức doanh thu thứ hai**: `paired_series` chỉ CHỌN và XẾP
  các `Point` mà `series()` đã tính;
- chỉ tiêu kỳ phía trên **không** bị cắt theo cửa sổ (chart đọc
  `service.period()` toàn bộ khi có kỳ; KPI đọc `view["data"]`), và
  `test_the_kpi_strip_above_does_not_move_with_the_chart_window` canh
  điều đó qua HTML.

Một điểm cần Owner biết: `AR-R5-IR-06` (tháng 31/28 ngày).

### Chuỗi D — sửa cả BH bằng một lần bấm

| Mục | Kết quả |
|---|---|
| 1. `Sửa` mở MỘT form cấp BH | PASS |
| 2. Chọn nhân viên áp cho cả đơn | PASS về cơ chế — **`FIND-R5-IR-01`** về giá trị mặc định |
| 3–4. Đổi nhiều giá, bấm XONG một lần, giữ sau refresh/`create_app` | PASS (smoke §2b) |
| 5. Lý do bắt buộc khi thay giá AUTO | PASS (`overrides` chỉ tính write có `auto_price is not None`) |
| 6. Không đổi ⟹ không sinh decision | PASS (`if current is not None and value == current: continue`) |
| 7. Một ô sai ⟹ không ghi một phần, không báo thành công | PASS (smoke: ô đúng vẫn rỗng sau lần POST hỏng; redirect mang `loi=`, không mang `da-luu=`) |
| 8. Line ID của BH khác | PASS — `_submitted_prices` dựng khoá từ `order_key` của form, và `plan_order_edit` chỉ xét dòng của đúng BH đó |
| 9. Gán nhân viên cả đơn không chạm BH khác | PASS |
| 10. Kỳ đã chốt | PASS — probe: `POST chốt kỳ → 302`, rồi `POST sửa-bh → 409` |

*Về transaction boundary:* `apply_order_edit` gọi lần lượt
`set_purchase_price` / `clear_purchase_price` / `set_employee`, mỗi lần một
transaction riêng — **không** phải một transaction chung. "Không có thành
công một phần" vì thế đúng với **lỗi validate** (đã kiểm) nhưng không đúng
với một sự cố database giữa chừng. Không mở finding: `plan_order_edit` đã
đóng mọi cửa kiểm được trước khi ghi, mọi phép ghi đều là upsert theo khoá
nghiệp vụ nên chạy lại là an toàn, và một sự cố database giữa chừng ở đây có
xác suất và hình dạng giống hệt mọi đường ghi khác của vertical (R2 §4.4,
`OD-5`) — R5 không làm nó tệ hơn.

### Chuỗi E — model, hãng, IMEI, popover

Cả 14 mục PASS. Đáng ghi:

- Tracking chỉ xuất **bốn** khoá (`name`, `alt`, `model_label`, `brand`) —
  `chieuBoard` dựng object MỚI từ danh sách trắng, và `kiem/xuat-baocao.js`
  khẳng định trên JSON ĐÃ SERIALIZE rằng mỗi dòng có đúng
  `alt+brand+model_label+name`, cộng một mục ĐỐI CHỨNG chứng minh các phép
  thử ấy bắt được dữ liệu thô.
- Không rò `cat`, giá, tồn, NCC, note, link — kiểm lại độc lập trên capture
  do công cụ production chụp từ mã Tracking thật (§8).
- Artifact cũ thiếu hai trường vẫn đọc được: `load_tracking_catalog_capture`
  coi vắng mặt và `null` như nhau, và `_rows_from_board` không ghi khoá khi
  giá trị rỗng ⟹ `content_hash` của một danh mục chưa biết hãng **không đổi**
  giữa hai phiên bản hợp đồng.
- Hai trường KHÔNG tham gia nhận diện: `_match_field` chỉ đọc
  `tracking_code`/`name`/`alt` — đọc bằng mã nguồn, và
  `tests/test_r5_product_identity_fields.py` canh.
- `_catalog_field` chỉ tra khi `identity.classification ==
  CLASS_MATCHED_TRACKING`; conflict / stale / `OUT_OF_CATALOG` / chưa phân
  loại đều giữ **tên thô** và Hãng `—`.
- Reports không suy hãng từ `product_raw`: nguồn duy nhất được wire là
  `catalog_display.brand_source`, và `test_the_route_wires_only_the_canonical_brand_source`
  khẳng định bằng mã nguồn `calls == ["catalog_display.brand_source"]`.
- Endpoint tìm kiếm không cho ghi bằng payload giả: `confirm_identity` bắt
  buộc `tracking_code` **có thật** trong danh mục Tracking đang đọc được
  (cửa thứ 2 của `identity_gateway.confirm_identity`) — hàng rào của R2, R5
  không nới.

---

## 10. Bất biến R1–R4 — đã chạy lại

| # | Bất biến | Bằng chứng |
|---|---|---|
| 1 | MIN đúng `sale_date` | smoke HTTP: `A. đơn 03/09 nạp 30/09 → 6.800.000` |
| 2 | Không fallback sang ngày hiện tại/tương lai hay `tp/ton` cũ | `KHÔNG lấy giá hiện tại 30/09`, `KHÔNG lấy giá ngày 04/09`, `KHÔNG rơi về lịch sử tp/ton cũ` |
| 3 | MIN=0 không thành giá vốn 0 | `C. hết hàng → KHÔNG có giá (không phải 0)`, `lợi nhuận KHÔNG bằng doanh thu` |
| 4 | Giá tay, mapping, conflict R2 sống qua restart | smoke §2b mục "create_app lại vẫn giữ nguyên"; `pytest -k "identity or catalog"` 257 passed |
| 5 | Line binding R3 không gắn override sang dòng khác | `tests/test_r3_import_binding.py` + smoke mục "khoá dòng của BH khác KHÔNG sửa được" |
| 6 | Period close / fingerprint / drift | `tests/test_r3_export_and_period_close.py` 19 passed; probe `POST sửa-bh vào kỳ đã chốt → 409` |
| 7 | R4 KPI, contribution, drill-down reconciliation | `tests/test_r4_evaluation_metrics.py` + `_web.py` trong 227 passed |
| 8 | Dòng bị R5 tạm loại không làm fingerprint/tổng kỳ sai | `test_the_period_fingerprint_moves_when_a_line_is_dropped`; probe ba-tập-rời-nhau reconcile |

---

## 11. Soi bảy test cũ bị sửa

Đối chiếu từng bài với phiên bản tại `b6756fe`, và với **implementation**,
không với docstring.

| Test | Khẳng định CŨ | Vì sao R5 phải đổi | Khẳng định MỚI mạnh hơn / tương đương? | Có bị nới để che regression? |
|---|---|---|---|---|
| `test_chart_10_…invents_no_days` | không mốc `2025-06-*` nào trong `chart_bars` của trang `ky=2025-06` | cửa sổ đổi từ container-lịch sang hai cửa sổ cùng độ dài | **MẠNH HƠN** — nay quét CẢ hai chuỗi (`chart_bars` + `chart_bars_prev`), và thêm một khẳng định dương ở mức Quý | Không |
| `test_chart_11_…one_timeline…` | đọc `chart-bar` trên một trang `ky=2025-06` riêng | 06/2025 nay nằm trong cửa sổ so sánh của CHÍNH biểu đồ đó | **MẠNH HƠN** — chứng minh trên cùng MỘT trang, cùng một trục; vẫn khẳng định `origin == LEGACY_REFERENCE` | Không |
| `test_f_e_the_chart_says_it_is_not_limited…` | `"Năm 2026" in scope` | phạm vi thật nay là hai khoảng 12 tháng | **MẠNH HƠN** — khẳng định CẢ HAI khoảng thật (`10/2025 → 09/2026` và `10/2024 → 09/2025`), giữ nguyên hai khẳng định phủ định | Không |
| `test_pi_04_…` | `<select>` có `value="EWF1143R7SC"` | popover có một ô tìm, chưa gõ thì chưa gợi ý | **MẠNH HƠN** — thêm khẳng định PHỦ ĐỊNH (chưa gõ ⟹ không có `identify-confirm`) và đổi sang so **bằng danh sách** `== ["EWF1143R7SC"]` | Không |
| `test_e2e_…` | mở panel không có `&tim=` | như trên | tương đương (chỉ thêm `&tim=EWF`); vẫn khẳng định `value="EWF1143R7SC"` | Không |
| `test_the_workspace_never_renders_a_prohibited_personal_field` | `assert "imei" not in html.lower()` | `DEC-R5-03` mở IMEI ở đúng route này; nhãn nút chứa chữ "IMEI" | **YẾU HƠN TẠI CHỖ**, nhưng được thay bằng `tests/test_r5_imei_boundary.py` (7 trang + export + snapshot, khẳng định theo GIÁ TRỊ mã máy) | Không che regression nào; **docstring lệch** — xem `AR-R5-IR-11` |
| `test_the_business_pages_never_leak_pii` | `"imei" not in html` trên 3 trang, gồm workspace | workspace nay được phép hiện | **MẠNH HƠN** trên hai trang chỉ tiêu (giữ phép thử chuỗi **và** thêm phép thử GIÁ TRỊ `356938035643809`); workspace tách ra và vẫn canh `employee_raw` | Không |
| `test_the_route_wires_only_the_canonical_brand_source` | `calls == ["brand_identity.canonical_brand"]` | `DEC-R5-04` chuyển sang read model canonical của Tracking | **tương đương** — vẫn so bằng danh sách MỘT phần tử, vẫn khẳng định "đúng một nguồn" | Không. Xác minh thêm: `CanonicalProductIdentity` chỉ có `namespace` + `source_product_code`, nên `canonical_brand` **luôn** trả `None` — nguồn cũ chưa từng cho ra một hãng nào |

Không test nào bị xoá. Không khẳng định nào bị nới mà không có một khẳng định
chặt hơn thay chỗ.

---

## 12. Việc phiên này KHÔNG làm

- KHÔNG sửa một dòng mã sản phẩm nào (Reports lẫn Tracking).
- KHÔNG merge, KHÔNG deploy, KHÔNG mở PR.
- KHÔNG đóng `CHECK-R3-20`, `CHECK-R4-24`, `CHECK-R5-28`.
- KHÔNG triển khai `category_label` và KHÔNG mở sang R5.1.
- KHÔNG tiêu một repair cycle nào của lineage R5.
