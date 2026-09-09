# R5 — Đối soát sổ, biểu đồ so sánh, thao tác đơn và danh tính sản phẩm

## Metadata

Status:
IMPLEMENTED

Current Status Reason:
Toàn bộ năm gói của `R5 Audit & Execution Brief — Đối soát sổ, biểu đồ so sánh, thao tác đơn và danh tính sản phẩm` đã triển khai, trên CẢ
HAI repo. Không migration mới, không schema mới, không bảng mới.

`CHECK-R5-01` … `CHECK-R5-26` PASS (E1, bằng chứng nguyên văn ở
`docs/sessions/S134-r5-doi-soat-va-danh-tinh.md`; Independent Review vòng 1
đã chạy lại toàn bộ 26 check trên exact HEAD được bàn giao và khớp).

**Independent Review vòng 1 (`S135`, 2026-09-08) → `REPAIR_REQUIRED`.** Bản
ghi: `docs/reviews/R5-INDEPENDENT-REVIEW-RECORD.md`. Hai finding bắt buộc,
cả hai nằm trên đúng failure path chính của R5: `FIND-R5-IR-01` (bấm `XONG`
gán lại cả BH cho nhân viên đầu danh sách khi BH có 0 hoặc ≥2 nhân viên hiệu
lực) và `FIND-R5-IR-02` (dòng quay lại không được khôi phục khi hai lần nạp
rơi vào cùng một giây — mốc snapshot ghi ở độ phân giải giây, phép so ngặt;
tổng kỳ ở lại THẤP HƠN thực tế vĩnh viễn). Review đã HOÀN THÀNH đúng thẩm
quyền của nó; implementation CHƯA được chấp nhận. Repair brief:
`docs/tasks/R5-REPAIR-1-doi-soat-nhan-vien-va-khoi-phuc.md`.

**REPAIR-1 (`S135`, 2026-09-09) đã xong.** Cả hai finding đã sửa và có test
tái hiện đi qua đường production; thêm `AR-R5-IR-11` (docstring hứa một
khẳng định không có trong thân bài) cũng đã sửa. Chi tiết + bằng chứng:
`docs/sessions/S135-r5-repair-1.md`.

**`CHECK-R5-27` (Independent Review) = `FAIL` ở vòng 1, và CHƯA được chạy
LẠI trên HEAD sau repair.** Phiên repair KHÔNG tự đóng nó — đúng kỷ luật đã
áp cho R1, R2, R3 và R4, và đúng lời của chính review vòng 1: check này "chỉ
chuyển sang `PASS` ở lần review thứ hai, sau khi `R5-REPAIR-1` xong." Một
vòng review độc lập thứ hai, TRÊN CHÍNH HEAD SAU REPAIR, vẫn là việc CÒN
PHẢI LÀM trước khi tích hợp — không phiên tích hợp/triển khai nào được thay
thế nó bằng việc tự xác nhận rằng bản sửa "đúng" theo test của chính mình.

`CHECK-R5-28` (Owner nghiệm thu) VẪN `NOT_TESTED`. Điều kiện tích hợp của
`S133` (Owner nghiệm thu R3/R4 trên production trước khi R5 được merge) vẫn
còn nguyên và không có bằng chứng nào cho thấy nó đã thoả.

Phase:
PHASE-01 — Engine tính toán

Task Mode:
MAJOR

Primary Agent Tier:
C

Escalation Tier:
C

Difficulty:
4/5

Risk:
4/5

Blast Radius:
4/5 (V4.1 §4 — chấm theo failure path. Failure path CHÍNH của R5 là
`cờ vắng mặt → effective data → MỌI chỉ tiêu kinh doanh → vân tay chốt kỳ →
export Excel`. Nó đi xa hơn R4 đúng một bậc vì R5 có quyền LOẠI dòng khỏi tập
được cộng: một lỗi ở đó làm tổng SAI THEO HƯỚNG THẤP HƠN, và thấp hơn thì khó
thấy hơn cao hơn. Nó KHÔNG đạt 5/5 vì không đường nào của R5 ghi đè một bản
ghi kế toán, không migration nào chạy, và mọi phép loại đều đảo ngược được
bằng một lần nạp sổ.)

Effective Risk:
HIGH (Blast Radius quyết định — V4.1 §4.1)

Project Profile:
PRODUCT

Review Budget lineage:
`R5` là root lineage RIÊNG, `2 allowed / 0 used / 2 remaining`
(`HIGH = 2` theo bảng đã freeze `V4.1` §2). Xem
`PROJECT/REVIEW_BUDGET_LEDGER.md` → "Root Task: R5". R5 KHÔNG sửa tiếp triển
khai của R4 — nó ĐỌC một R4 đã merge vào nhánh mặc định (`b6756fe`, gồm PR #10
và PR #11). Không repair cycle nào bị tiêu trong phiên triển khai này.

ADR:
`docs/adr/ADR-111-absence-effective-data-imei-scope-and-brand-authority.md` —
ba ranh giới thẩm quyền mà R5 đổi có chủ đích (hiệu lực của cờ vắng mặt, phạm
vi IMEI, và thẩm quyền thương hiệu).

Owner Authority:
`R5 Audit & Execution Brief — Đối soát sổ, biểu đồ so sánh, thao tác đơn và danh tính sản phẩm` §1 (ba quyết định xác nhận 08/09/2026) và §4
(năm gói). Nền đã merge: `claude/extract-upload-repo-gq2ws4` @ `b6756fe`, chứa
R4 HEAD `63a066e9275919df92bceaee58876f2724cf9df0` mà brief yêu cầu.

---

## 1. Vì sao R5 tồn tại

Bốn trong năm gói của R5 đóng cùng một loại khoảng cách: khoảng cách giữa
*điều màn hình nói* và *điều hệ thống biết*.

Cái đắt nhất nằm ở đối soát sổ. `TASK-PRA-002` slice B dựng đúng một bất biến
an toàn — *"không thấy" KHÔNG BAO GIỜ tự động trở thành "đã xoá"* — và nó đúng
tuyệt đối khi file mới có thể là một file một phần. Nhưng slice B cũng dựng
một nút "xác nhận sổ này đầy đủ cho khoảng ngày", và sau khi người dùng bấm
nút ấy, hệ thống vẫn xử sự y như trước: doanh thu của một đơn đã huỷ vẫn nằm
trong tổng. Người dùng đã cung cấp đúng căn cứ mà hệ thống nói là nó còn
thiếu, rồi không có gì xảy ra.

Bốn khoảng cách còn lại: trang snapshot liệt kê mọi thay đổi kể cả những thay
đổi không ai cần soi, làm chìm mất cái cần soi; biểu đồ vẽ một đường và bắt
người đọc nhớ kỳ trước bằng đầu; nút `XONG` của màn hình sửa BH chỉ ĐÓNG chứ
không lưu; và cột sản phẩm in nguyên tên trên sổ kể cả sau khi Owner đã phân
loại xong.

---

## 2. Năm gói của brief

1. **Sổ đầy đủ và dòng biến mất** — snapshot `CONFIRMED_COMPLETE` tạm loại
   dòng vắng mặt khỏi effective data và MỌI số liệu; danh sách cảnh báo riêng
   không mang tiền; tái xuất hiện khôi phục tự động; câu chữ viết lại.
2. **Danh sách thay đổi gọn và tra cứu được** — lọc `{delivery_cost, imei}` ở
   tầng trình bày; bỏ cột "Phiên bản" khỏi UI; mỗi Số BH mang nhân viên hiệu
   lực và là deep link về đúng tháng/sheet/anchor.
3. **Biểu đồ hai kỳ** — hai cửa sổ liền kề cùng độ dài (30 ngày · 12 tuần ·
   12 tháng · 8 quý) trên một trục và một thước đo; thiếu bằng chứng là gap.
4. **Sửa cả BH bằng một lần bấm** — một form cấp BH, `XONG` là nút gửi duy
   nhất, validate toàn bộ trước khi ghi, chỉ ghi trường đổi.
5. **Model, Hãng, IMEI và popover phân loại** — Tracking chuẩn hoá
   `model_label`/`brand`; Reports đọc cả hai hợp đồng; hai cột ẩn mặc định sau
   một nút chung; popover neo tại toạ độ click với một ô tìm và một gợi ý.

---

## 3. Scope Lock

**ĐƯỢC LÀM**

Reports:
- Một truy vấn ĐỌC mới cho cờ vắng mặt (`SnapshotRepository.
  removed_candidate_keys`) và một lớp phủ mới trên `PeriodData`
  (`removed_in_source`).
- Hai module TRÌNH BÀY thuần mới (`snapshot_presentation`, `catalog_display`)
  và một module TRUY VẤN hẹp mới (`workspace_imei`).
- Một route GHI mới cấp BH (`POST /kinh-doanh/nhan-vien/sua-bh`), gọi đúng các
  phương thức store đã nghiệm thu.
- Hai trường TÙY CHỌN trên `TrackingCatalogRow` + capture + loader.
- Mô hình hai cửa sổ trong `revenue_timeline` và một hàm trình bày mới.

Tracking:
- Mở rộng danh sách trắng `/api/xuat/board` bằng đúng hai trường tùy chọn.

**KHÔNG ĐƯỢC LÀM**

- Đổi công thức MIN theo `sale_date`, nguồn `TON_KHO`, sentinel 0, fallback
  R1, resolver sản phẩm, hay ngữ nghĩa hoàn/hủy.
- Migration mới, bảng mới, hard-delete lịch sử, backfill snapshot cũ.
- WebSocket, realtime locking, undo tổng quát, fuzzy auto-mapping.
- Parser hãng/model từ `product_raw` phía Reports; bảng brand riêng của
  Reports.
- Đưa IMEI sang trang quản trị khác, export mới, log hay telemetry.

---

## 4. Completion Gate

| ID | Nội dung | Status | Evidence |
|---|---|---|---|
| `CHECK-R5-01` | Sổ CHƯA xác nhận: `NOT_SEEN` vẫn chỉ cảnh báo, tổng không đổi | PASS | E1 |
| `CHECK-R5-02` | Sổ ĐÃ xác nhận: dòng vắng bị loại khỏi số đơn, số dòng, doanh thu, LN KPI, DS quy đổi | PASS | E1 |
| `CHECK-R5-03` | BH mất TRỌN dòng không được tính vào số đơn | PASS | E1 |
| `CHECK-R5-04` | Biểu đồ, sheet nhân viên, export Excel và vân tay chốt kỳ đọc CÙNG tập đã loại | PASS | E1 |
| `CHECK-R5-05` | Danh sách cảnh báo riêng có Số BH · ngày cũ · sản phẩm · nhân viên, KHÔNG có ô tiền | PASS | E1 |
| `CHECK-R5-06` | Tái xuất hiện ⟹ cảnh báo TỰ mất và số TỰ khôi phục | PASS | E1 |
| `CHECK-R5-07` | Không hard-delete: version/current/flag không giảm một bản ghi nào | PASS | E1 |
| `CHECK-R5-08` | Dòng ngoài khoảng đã xác nhận KHÔNG BAO GIỜ bị loại | PASS | E1 |
| `CHECK-R5-09` | Câu chữ ba chỗ (form xác nhận · thông báo · trang snapshot) nói đúng hệ quả mới | PASS | E1 |
| `CHECK-R5-10` | Thay đổi chỉ gồm `delivery_cost`/`imei` không được liệt kê và không tính vào "cần soi" | PASS | E1 |
| `CHECK-R5-11` | fingerprint, source version và `detail_json` dưới database KHÔNG đổi | PASS | E1 |
| `CHECK-R5-12` | Thay đổi hỗn hợp chỉ ẩn phần nhiễu; phần còn lại vẫn hiện | PASS | E1 |
| `CHECK-R5-13` | Cột "Phiên bản" rời khỏi UI; hai version id còn nguyên trong bảng cờ | PASS | E1 |
| `CHECK-R5-14` | Mỗi BH thay đổi hiện nhân viên HIỆU LỰC và deep link đúng kỳ/sheet/anchor | PASS | E1 |
| `CHECK-R5-15` | Không còn dòng hiện hành ⟹ nói thẳng, KHÔNG đoán nhân viên | PASS | E1 |
| `CHECK-R5-16` | Ngày/Tuần/Tháng/Quý có HAI đường, legend nói rõ hai cửa sổ; Năm giữ một đường | PASS | E1 |
| `CHECK-R5-17` | Hai cửa sổ CÙNG độ dài (30/12/12/8), liền kề, không chồng nhau | PASS | E1 |
| `CHECK-R5-18` | Dùng lại MỘT engine doanh thu; Σ cửa sổ hiện tại = chỉ tiêu kỳ | PASS | E1 |
| `CHECK-R5-19` | Thiếu bằng chứng là GAP; số 0 chỉ khi mốc nằm TRỌN trong khoảng đã xác nhận | PASS | E1 |
| `CHECK-R5-20` | KPI phía trên KHÔNG đổi theo cửa sổ biểu đồ | PASS | E1 |
| `CHECK-R5-21` | Một form cấp BH; `XONG` là nút gửi duy nhất; không `<form>` lồng `<form>` | PASS | E1 |
| `CHECK-R5-22` | Một ô hỏng ⟹ KHÔNG ô nào được ghi (không có thành công một phần) | PASS | E1 |
| `CHECK-R5-23` | Ô không đổi KHÔNG sinh quyết định; lý do override R2 §4.4 vẫn bắt buộc | PASS | E1 |
| `CHECK-R5-24` | Tracking xuất `model_label`/`brand` đã chuẩn hoá; không lộ `cat`/giá/tồn/NCC/note/link | PASS | E1 |
| `CHECK-R5-25` | Reports đọc CẢ artifact cũ lẫn mới; hash mới gồm hai trường; hai trường KHÔNG tham gia nhận diện | PASS | E1 |
| `CHECK-R5-26` | IMEI chỉ ở route nhân viên; hai cột ẩn mặc định, nút chung, cột hẹp cắt một dòng; popover một ô tìm, tối đa một gợi ý | PASS | E1 |
| `CHECK-R5-27` | Independent Review | FAIL (vòng 1) — chờ chạy lại trên HEAD sau REPAIR-1 | `docs/reviews/R5-INDEPENDENT-REVIEW-RECORD.md` (`S135`) |
| `CHECK-R5-28` | Owner nghiệm thu trên production | NOT_TESTED | — |
| `CHECK-R5-29` | `XONG` không gán lại cả BH khi BH có 0 hoặc ≥2 nhân viên hiệu lực | PASS | E1 |
| `CHECK-R5-30` | Mọi ô chọn nhân viên LUÔN có đúng một option được chọn | PASS | E1 |
| `CHECK-R5-31` | Dòng quay lại được khôi phục kể cả khi ba lần nạp cùng một giây | PASS | E1 |
| `CHECK-R5-32` | Mốc snapshot phân giải hơn một giây; mốc cũ hơn HẲN vẫn giữ cờ | PASS | E1 |

Bằng chứng nguyên văn (lệnh + output):
`docs/sessions/S134-r5-doi-soat-va-danh-tinh.md` §4–§7.

`CHECK-R5-27` và `CHECK-R5-28` KHÔNG được tự đánh dấu bởi bất kỳ phiên triển
khai nào — kể cả một phiên REPAIR hay một phiên TÍCH HỢP. `CHECK-R5-27` được
đặt bởi phiên Independent Review `S135` (vòng 1) và chỉ chuyển sang `PASS`
(hoặc `ACCEPT_WITH_RECORDED_RISK`) ở một lần review ĐỘC LẬP thứ hai, chạy
trên HEAD sau repair — chưa phiên nào thực hiện lần review thứ hai đó.

`CHECK-R5-29` … `CHECK-R5-32` là các check MỚI do REPAIR-1 thêm, và chúng
canh đúng hai finding mà review vòng 1 đã tìm ra bằng test đi qua đường
production. Chúng là bằng chứng CHO người review thứ hai đọc, KHÔNG thay thế
việc review đó phải diễn ra: một phiên implementation tự kiểm bằng test của
chính nó không phải là Independent Review.

Bằng chứng REPAIR-1: `docs/sessions/S135-r5-repair-1.md` §2, §3, §6.

---

## 5. Exit Criteria

1. Nạp file một phần thiếu một đơn: tổng chưa đổi, câu cảnh báo dễ hiểu. —
   `CHECK-R5-01`, `CHECK-R5-09`.
2. Xác nhận file đầy đủ: đơn thiếu vào cảnh báo riêng, không góp vào chỉ tiêu
   nào; nạp lại thì cảnh báo tự mất và tổng khôi phục. — `CHECK-R5-02` …
   `CHECK-R5-06`.
3. Snapshot chỉ đổi phí giao/IMEI: không mục nhiễu; đổi doanh thu thật vẫn
   thấy, có tên nhân viên và click về đúng BH. — `CHECK-R5-10`, `CHECK-R5-14`.
4. Chuyển Ngày/Tuần/Tháng/Quý: luôn thấy hai đường, đúng legend và tooltip. —
   `CHECK-R5-16` … `CHECK-R5-19`.
5. Sửa một BH nhiều dòng: đổi giá và nhân viên, bấm `XONG` đúng một lần;
   refresh và restart vẫn đúng. — `CHECK-R5-21` … `CHECK-R5-23`.
6. Dòng đã phân loại hiện model ngắn; `HIỆN HÃNG & IMEI` cho hai cột hẹp cắt
   một dòng; dòng chưa phân loại giữ tên gốc, không có hãng bịa. —
   `CHECK-R5-25`, `CHECK-R5-26`.
7. Popover xuất hiện tại chỗ bấm, gõ tìm thấy một gợi ý, click là cập nhật tại
   chỗ; "Không có trên bảng giá" vẫn chạy. — `CHECK-R5-26`.
8. Đối chiếu MIN ngày 03/09, lợi nhuận, export và kỳ chốt/drift để chắc R1–R4
   không đổi. — full regression + hai smoke, §7 của `S134`.
9. Independent Review kết luận trên exact HEAD. — `CHECK-R5-27`, vòng 1 ĐÃ
   CHẠY (`S135`), kết luận `REPAIR_REQUIRED`. `R5-REPAIR-1` đã xong; VẪN
   CHƯA thoả — cần một vòng review độc lập THỨ HAI trên HEAD sau repair.
10. Owner nghiệm thu trên production. — `CHECK-R5-28`, CHƯA CÓ.

---

## 6. Rủi ro chấp nhận ghi nhận

`AR-R5-01` … `AR-R5-05` — xem `docs/sessions/S134-r5-doi-soat-va-danh-tinh.md`
§8. Không rủi ro nào trong số đó thuộc nhóm `REPAIR_REQUIRED` của brief §8;
Independent Review vòng 1 (`S135`) đã TÁI KIỂM CHỨNG cả năm và giữ nguyên mức
`ACCEPTED_RISK`.

`AR-R5-IR-06` … `AR-R5-IR-12` — bảy rủi ro MỚI do Independent Review vòng 1
(`S135`) ghi nhận, xem `docs/reviews/R5-INDEPENDENT-REVIEW-RECORD.md` §4.
`AR-R5-IR-09` và `AR-R5-IR-12` là lỗi baseline có trước R5 (đo trên
`b6756fe`), không sửa trong REPAIR-1 vì ngoài Scope Lock. Ba mục trong bảy đã
được **REPAIR-1 sửa/đóng** thay vì chỉ ghi nhận:

- `AR-R5-IR-10` (chú thích đã hết đúng ở `_with_absence_state`) — chú thích
  viết lại làm một phần của bản sửa `FIND-R5-IR-02`.
- `AR-R5-IR-11` (docstring hứa một khẳng định không có trong thân bài) —
  thân bài nay kiểm đúng điều docstring hứa.

`AR-R5-IR-06` … `AR-R5-IR-09`, `AR-R5-IR-12` giữ nguyên `ACCEPTED_RISK`,
KHÔNG chạm trong REPAIR-1 (đúng Scope Lock của
`docs/tasks/R5-REPAIR-1-doi-soat-nhan-vien-va-khoi-phuc.md` §1).

`AR-R5-IR-13` (bản ghi CŨ ghi mốc tới giây vẫn không phân giải được thứ tự;
`>=` nghiêng về GIỮ TIỀN cho những bản ghi ấy) — rủi ro MỚI do chính REPAIR-1
ghi nhận, hệ quả trực tiếp của cách sửa `FIND-R5-IR-02`. Xem
`docs/sessions/S135-r5-repair-1.md` §7.
