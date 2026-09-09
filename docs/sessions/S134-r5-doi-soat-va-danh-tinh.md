# S134 — R5: đối soát sổ, biểu đồ so sánh, thao tác đơn và danh tính sản phẩm

## 0. Tóm tắt cho người đọc vội

R5 làm năm việc trên hai repo. Việc quan trọng nhất sửa một khoảng cách mà
người dùng đã tự tay đóng lại rồi mà hệ thống không nhận: sau khi họ bấm "sổ
này đầy đủ cho khoảng ngày X", một đơn cũ trong X mà sổ đó không có VẪN được
cộng vào doanh thu. Người dùng đã cung cấp đúng căn cứ mà hệ thống nói là nó
còn thiếu, rồi không có gì xảy ra.

`CHECK-R5-01` … `CHECK-R5-26` PASS. `CHECK-R5-27` (Independent Review) và
`CHECK-R5-28` (Owner nghiệm thu) VẪN `NOT_TESTED` — phiên này không tự tuyên
bố hai check đó, đúng kỷ luật đã áp cho R1–R4. Task ở `IMPLEMENTED`.

Task canonical: `docs/tasks/R5-doi-soat-so-bieu-do-thao-tac-danh-tinh.md`.
Quyết định: `PROJECT/PROJECT_DECISIONS.md` → `DEC-202`. Kiến trúc:
`docs/adr/ADR-111-absence-effective-data-imei-scope-and-brand-authority.md`.

**Kết luận phiên: `IMPLEMENTED`.**

---

## 1. Nền và ranh giới

- Reports — nhánh phát triển: `claude/r5-reports-tracking-deploy-o77n7t`.
  Base: nhánh mặc định thật `claude/extract-upload-repo-gq2ws4` @ `b6756fe`.
- Tracking — nhánh phát triển: `claude/r5-reports-tracking-deploy-o77n7t`.
  Base: `main` @ `edeb827`.

Điều kiện mở phiên của brief đã được xác minh TRƯỚC khi sửa một dòng nào:

```text
$ git remote show origin | grep 'HEAD branch'
  HEAD branch: claude/extract-upload-repo-gq2ws4

$ git merge-base --is-ancestor 63a066e9275919df92bceaee58876f2724cf9df0 \
      origin/claude/extract-upload-repo-gq2ws4 && echo YES
YES

$ .venv/bin/python -m alembic heads
0009_line_binding_period_close (head)
```

R4 HEAD mà brief yêu cầu (`63a066e9…`) NẰM TRONG nhánh mặc định — không có
divergence nào để báo, và không có lý do nào để chép tay R4 sang R5. Nhánh mặc
định đã đi tiếp tới `b6756fe` (PR #10 R4 + PR #11 bàn giao `S133`), nên phiên
này rebase lên `b6756fe` chứ không dừng ở `63a066e9`.

Migration: MỘT head duy nhất, đúng head của R3. R5 KHÔNG thêm migration nào —
đây là một ràng buộc của brief và nó được giữ.

### CONFLICT DETECTED — điều kiện mở R5

Documentation:
`S133` §"Tích hợp production R4" ghi *"**R5 CHƯA `READY`** — chỉ mở sau khi
Owner xác nhận Render deploy Live VÀ tự nghiệm thu R3/R4 trên dữ liệu thật
đạt."* Hai điều kiện đó CHƯA xảy ra: `CHECK-R3-20` và `CHECK-R4-24` vẫn
`NOT_TESTED`.

Implementation:
`R5 Audit & Execution Brief — Đối soát sổ, biểu đồ so sánh, thao tác đơn và danh tính sản phẩm` §0 đặt một điều kiện KHÁC và hẹp hơn — nhánh
mặc định chứa R4 HEAD, migration production ở head. Cả hai đã thoả (đo ở trên).
Owner chỉ thị trực tiếp mở phiên triển khai R5 đầy đủ.

Risk:
R5 xây trên một nền Owner CHƯA nghiệm thu trên dữ liệu thật. Nếu nghiệm thu
R3/R4 phát hiện lỗi ở nền, phần R5 chồng lên có thể phải làm lại một phần —
rủi ro cao nhất ở gói 1 (đọc chính cơ chế cờ vắng mặt của PRA-002) và gói 3
(đọc chính engine doanh thu của R4).

Recommended resolution — và là điều phiên này đã làm:
Triển khai theo chỉ thị mới hơn của Owner; KHÔNG merge, KHÔNG deploy, KHÔNG
chạm `CHECK-R3-20`/`CHECK-R4-24`. Điều kiện của `S133` không bị xoá — nó
chuyển từ "điều kiện MỞ R5" thành **điều kiện TÍCH HỢP R5**: R5 không được
merge vào nhánh mặc định trước khi Owner nghiệm thu R3/R4 trên production.
Ghi song song ở `PROJECT/PROJECT_PROGRESS.md`.

Sáu commit của phiên này (Reports):

```text
1621c96  R5 §1: sổ đã xác nhận đầy đủ tạm loại dòng biến mất khỏi mọi số liệu
f106dcb  R5 §2: danh sách thay đổi gọn, có nhân viên và bấm về đúng dòng
1bb8554  R5 §3: biểu đồ so hai cửa sổ liền kề cùng độ dài
294304d  R5 §4: sửa cả BH bằng một lần bấm
3c8093f  R5 §5: model canonical, Hãng/IMEI trên tab nhân viên, popover phân loại
dad8513  R5: smoke qua HTTP thật không còn đo chính cái stub của nó
```

Một commit của phiên này (Tracking):

```text
f958226  R5 §5: /api/xuat/board xuất thêm model_label và brand đã chuẩn hoá
```

HEAD Reports (code): `dad85135270498ad1dca0bf0980463da0519fb8d`
HEAD Reports (gồm tài liệu): `19b853f718e1ed6dbf700468105c9dd38ff4cc2d`
HEAD Tracking: `f958226f6127e6055eb411e4c22e12c58d09654b`

---

## 2. Gói 1 — lỗi trung tâm, tái hiện được

`SnapshotRepository.confirm_coverage` ghi `REMOVED_IN_SOURCE_CANDIDATE` và
docstring của nó nói thẳng cái nó KHÔNG làm: *"xoá dòng, đổi con trỏ hiện
hành, đổi bất kỳ con số analytics nào"*. Điều đó đúng và có chủ đích ở
PRA-002. Nhưng nó cũng có nghĩa là:

```text
lần nạp 1   BH1 8.000.000 · BH2 4.000.000        tổng = 12.000.000
lần nạp 2   sổ chỉ còn BH1
người dùng bấm "sổ này đầy đủ cho 01–30/09"
            → cờ REMOVED_IN_SOURCE_CANDIDATE cho BH2
            → tổng VẪN 12.000.000
```

`tests/test_r5_removed_lines.py::test_a_confirmed_complete_snapshot_drops_the_
missing_line_from_every_figure` tái hiện đúng chuỗi đó qua tầng ráp thật
(`BusinessReportService.period`) và khẳng định con số SAU bản sửa là
`8.000.000`.

Cấu tạo của bản sửa, và vì sao nó không cần ai nhớ gì:

```text
PeriodData.details          các dòng ĐANG được báo cáo
PeriodData.excluded         Owner đã loại        (DEC-PHB02-08 §30)
PeriodData.removed_in_source dòng đã tạm loại    (R5 §1, MỚI)
```

Ba tập rời nhau, và `totals` cộng trên `lines` — tức chỉ tập thứ nhất. Mọi chỉ
tiêu, kể cả những chỉ tiêu chưa được viết ra, đúng vì tập bị loại không nằm
trong tập được cộng. Đó là cùng cấu tạo mà `§30` đã dùng, và R5 cố ý dùng lại
nó thay vì phát minh một cơ chế thứ hai.

"Còn hiệu lực" KHÔNG phải một cột: `_with_absence_state` đã tính nó lúc đọc từ
lịch sử membership từ trước R5. Nhờ vậy "dòng quay lại thì tổng tự khôi phục"
đúng theo cấu tạo — không ai phải nhớ gỡ cờ, và không bản ghi nào bị sửa.

---

## 3. Bốn gói còn lại — điều đáng ghi lại

**Gói 2.** `delivery_cost`/`imei` Ở LẠI trong `line_fingerprint`. Đó không
phải một chi tiết kỹ thuật: nó là điều kiện để một lần xuất sổ bổ sung IMEI
tạo ra source version mới và giá trị ấy được LƯU. Bỏ chúng khỏi vân tay sẽ làm
đúng dữ liệu đó im lặng biến mất giữa hai lần nạp. Nên ranh giới rất hẹp và
được nói ra thành lời trong `snapshot_presentation`: database không đổi, chỉ
danh sách và con số trên màn hình lọc.

**Gói 3.** `paired_series` KHÔNG cộng lại một đồng nào — nó chỉ CHỌN và XẾP
các điểm mà `series()` đã tính. Cửa sổ dựng từ LỊCH chứ không từ dữ liệu: một
cửa sổ dựng từ các mốc CÓ dữ liệu sẽ tự co lại quanh những ngày bán được, và
hai cửa sổ "cùng độ dài" khi ấy trải trên hai khoảng thời gian khác nhau —
đúng phép so sánh sai mà `DEC-R5-02` sinh ra để tránh.

**Gói 4.** `plan_order_edit` / `apply_order_edit` tách hẳn KIỂM khỏi GHI. Đó
là cách làm cho "không có thành công một phần" đúng theo cấu tạo thay vì nhờ
mỗi đường ghi tự nhớ kiểm.

**Gói 5.** Hãng ghép theo một danh sách ĐÓNG và ghép NGUYÊN TỪ. Bốn trường hợp
đối chứng trong `kiem/hang-va-model.js` (BLUESTONE/LG · SHARPNESS/Sharp ·
ARTCLASS/TCL · GREEN/Gree) sẽ trượt nếu ai đó đổi phép ghép thành "chứa chuỗi
con" — không có chúng, bộ kiểm vẫn xanh với một phép ghép lỏng và không chứng
minh gì.

---

## 4. Bằng chứng — Reports

Focused tests của năm gói:

```text
$ .venv/bin/python -m pytest \
    tests/test_r5_removed_lines.py tests/test_r5_change_list.py \
    tests/test_r5_two_window_chart.py tests/test_r5_order_edit_form.py \
    tests/test_r5_product_identity_fields.py tests/test_r5_imei_boundary.py \
    tests/test_r5_workspace_identity_ux.py -q
77 passed in 8.65s
```

Identity · pricing · daily-min:

```text
$ .venv/bin/python -m pytest -q -k "identity or pricing or daily_min or dailymin"
341 passed, 1 skipped, 2893 deselected in 13.62s
```

R2 · R3 · R4 · hàng rào nghiệp vụ · PHB-06 · vắng mặt snapshot:

```text
$ .venv/bin/python -m pytest \
    tests/test_business_boundaries.py tests/test_phb06_brand_reporting.py \
    tests/test_r2_web_workflow.py tests/test_r2_product_classification.py \
    tests/test_r3_import_binding.py tests/test_r3_export_and_period_close.py \
    tests/test_r3_line_types.py tests/test_r3_web_workflow.py \
    tests/test_r4_evaluation_metrics.py tests/test_r4_evaluation_web.py \
    tests/test_snapshot_absence.py tests/test_history_coverage_confirmation.py -q
333 passed in 14.69s
```

Full regression:

```text
$ .venv/bin/python -m pytest -q
3223 passed, 12 skipped in 177.60s (0:02:57)
```

Baseline trước R5 (đo trên chính `b6756fe` lúc mở phiên):
`3146 passed, 12 skipped`. Không có FAIL nào ở baseline, nên KHÔNG có lỗi
baseline cũ để tách khỏi lỗi mới ở phía test.

Smoke qua HTTP THẬT:

```text
$ .venv/bin/python tools/smoke/r1_web_upload_smoke.py \
      --tracking-repo /home/user/Tracking
POST /run → HTTP 302
  [BH7001] giá nhập = 6800000   lợi nhuận = 2200000   nguồn = TRACKING_DAILY_MIN
  [BH7002] giá nhập = 5000000   lợi nhuận = 4000000   nguồn = TRACKING_DAILY_MIN
  [BH7003] giá nhập = None   lợi nhuận = None   nguồn = Pending
  PASS  hợp đồng daily-min-v1 ĐƯỢC GỌI đúng một lượt
  PASS  A. đơn 03/09 nạp 30/09 → 6.800.000 (giá NGÀY BÁN)
  PASS  B. TON_KHO thắng → 5.000.000
  PASS  C. hết hàng → KHÔNG có giá (không phải 0)
KẾT QUẢ SMOKE: TẤT CẢ PASS
```

Smoke này ĐANG HỎNG TRƯỚC R5 và hỏng vì chính nó, không vì sản phẩm — xem §6.

> **ĐÍNH CHÍNH (`S135` §5).** Bản đầu của bàn giao này liệt kê
> `tools/smoke/r1_daily_min_smoke.py` như một lượt chạy đã PASS. Điều đó SAI:
> phiên `S134` đo `EXIT=$?` sau một `| tail`, nên nó đọc mã thoát của `tail`
> chứ không của Python — và công cụ ấy cần một file capture làm tham số nên
> lượt "chạy" đó chỉ in ra thông báo cách dùng. Chạy đúng với fixture có sẵn
> thì nó CRASH, và crash y hệt trên nền `b6756fe` trước R5: một lỗi baseline
> cũ của công cụ kiểm, ghi lại thành `AR-R5-IR-12`. Khẳng định PASS ấy đã
> được rút; smoke qua HTTP thật ở trên KHÔNG bị ảnh hưởng (nó được đo đúng,
> `EXIT=0`).

---

## 5. Bằng chứng — Tracking

```text
$ node kiem/hang-va-model.js
29 đạt, 0 hỏng

$ node kiem/xuat-baocao.js
174 đạt, 0 hỏng

$ npm test
61 bộ · 2767 đạt · 0 hỏng · 2 bỏ qua
Tất cả đạt.

$ npm run build
61 bộ · 2767 đạt · 0 hỏng · 2 bỏ qua
Đã dựng bản phục vụ vào ./dist
  7 file, xén chú thích 1 file HTML
  658 KB → 411 KB  (bớt 37%)
```

Kiểm rò dữ liệu chạy trên JSON ĐÃ SERIALIZE, không trên object, và có một mục
ĐỐI CHỨNG khẳng định các phép thử ấy BẮT ĐƯỢC dữ liệu thô — không có nó thì
một biểu thức hỏng luôn cho "không thấy" và cả khối xanh vĩnh viễn dù dữ liệu
đang chảy ra ngoài.

---

## 6. Governance validators và branch authority

```text
$ .venv/bin/python governance/scripts/governance/validate_evidence.py
EVIDENCE VALIDATION: PASS — Checked 161 REQUIRED PASS evidence record(s).

$ .venv/bin/python governance/scripts/governance/validate_project_state.py
PROJECT STATE: PASS

$ .venv/bin/python governance/scripts/governance/validate_structure.py
GOVERNANCE STRUCTURE: PASS — Checked 21 required paths.

$ .venv/bin/python governance/scripts/governance/validate_task_completion.py
TASK COMPLETION: PASS — Checked 14 DONE task(s).

$ .venv/bin/python governance/scripts/governance/validate_reference_integrity.py
REFERENCE INTEGRITY: FAIL
3 reference không phân giải được:
- docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> /README.md
- docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> CODE_OF_CONDUCT.md
- docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> CONTRIBUTING.md
```

**Lỗi baseline cũ, KHÔNG phải lỗi mới.** Ba reference ấy hỏng Y HỆT trên
`b6756fe` — đo bằng một worktree riêng tại đúng commit đó trước khi sửa gì.
Chúng nằm trong một task hoàn toàn không liên quan tới R5, và R5 không chạm
vào file đó. Sửa chúng ở đây sẽ là một scope expansion không ai yêu cầu.

**Smoke qua HTTP cũng là một lỗi baseline cũ, và phiên này SỬA nó** vì nó là
đúng công cụ mà brief §6 yêu cầu chạy. `r1_web_upload_smoke.py` thay
`run_owner_report` bằng một lambda liệt kê tay `sales`/`captures`; khi R2 thêm
`identity_store_view` vào lời gọi trong `server.py`, lambda ném `TypeError`,
`server.py` nuốt nó ở nhánh "không tạo được báo cáo", và smoke trả HTTP 400 —
nó đo chính cái stub của mình chứ không đo hệ thống. Đo trên `b6756fe`: hỏng y
hệt. Bản sửa (`dad8513`) đổi lambda thành `**kwargs`, và smoke chuyển từ FAIL
sang TẤT CẢ PASS.

Branch authority (chạy SAU commit tài liệu cuối cùng — xem ghi chú bên dưới):

```text
$ bash scripts/branch_authority_check.sh
DEFAULT_BRANCH       : claude/extract-upload-repo-gq2ws4
WORKTREE             : CLEAN
CURRENT_BRANCH       : claude/r5-reports-tracking-deploy-o77n7t
UPSTREAM             : origin/claude/r5-reports-tracking-deploy-o77n7t
behind upstream      : 0 commit
behind default       : 0 commit
divergence days      : 0
cumulative LOC       : 5306
DIVERGENCE           : INTEGRATION_DECISION_REQUIRED [ loc>5000 ]
AUTHORITY            : BRANCH_WITH_UPSTREAM
RESULT               : AUTHORITY_OK
```

**`INTEGRATION_DECISION_REQUIRED` — ghi lại, KHÔNG tự giải quyết.** Ngưỡng
`loc>5000` của `V4.1` bật ở commit tài liệu cuối cùng (sau năm gói code, khi
`DEC-202` + `ADR-111` + task + bàn giao + ledger vào nhánh). Phân rã:

```text
$ git diff --numstat b6756fe..HEAD | awk ...
docs/ + PROJECT/   1.086 dòng
code + test        4.220 dòng   (dưới ngưỡng)
```

Đây là một tín hiệu TÍCH HỢP, không phải một lỗi authority — `RESULT` vẫn
`AUTHORITY_OK`, nhánh không lệch một commit nào so với mặc định, và
`divergence days` = 0. Nó nói đúng một điều: nhánh này đã đủ lớn để việc tích
hợp cần một quyết định tường minh thay vì trôi thêm.

Phiên này KHÔNG tự ra quyết định đó, vì nó va vào đúng ràng buộc đã ghi ở
`CONFLICT DETECTED` §1: R5 không được merge trước khi Owner nghiệm thu R3/R4
trên production. Hai đường ra, và cả hai thuộc thẩm quyền Owner:

1. Owner nghiệm thu R3/R4 trên production ⟹ R5 đi qua Independent Review rồi
   tích hợp NGUYÊN KHỐI.
2. Owner muốn tích hợp sớm hơn ⟹ tách theo gói (`§1` là gói có bán kính lớn
   nhất và nên đi riêng; `§2`–`§5` độc lập với nhau về dữ liệu).

Không phiên triển khai nào được tự chọn giữa hai đường đó.

---

## 7. Test cũ được sửa CÓ CHỦ ĐÍCH

Bảy test cũ đổi khẳng định. Mỗi chỗ đều ghi lý do ngay trong docstring của
chính nó; đây là danh sách để người review không phải đi tìm:

| Test | Đổi gì | Vì sao |
|---|---|---|
| `test_chart_10_…invents_no_days` | chỗ tìm bằng chứng của tháng lịch sử | cửa sổ 12 tháng thay container năm; bằng chứng nằm ở cửa sổ so sánh và ở mức Quý, không mất |
| `test_chart_11_…one_timeline…` | đọc `chart-bar-prev` thay `chart-bar` | như trên |
| `test_f_e_the_chart_says_it_is_not_limited…` | câu `chart-scope` | `F-E` giữ nguyên tinh thần: câu phải nói ĐÚNG phạm vi, nay là hai khoảng thời gian |
| `test_pi_04_…` và `test_e2e_…` | thêm `&tim=` trước khi mong có gợi ý | popover có một ô tìm; chưa gõ gì thì chưa gợi ý gì |
| `test_the_workspace_never_renders_a_prohibited_personal_field` | bỏ `imei` khỏi danh sách cấm | `DEC-202` §10; phạm vi đầy đủ chuyển sang `test_r5_imei_boundary.py` |
| `test_the_business_pages_never_leak_pii` | khẳng định theo GIÁ TRỊ mã máy | nhãn nút chứa chữ "IMEI"; điều cần canh là giá trị, không phải chữ |
| `test_the_route_wires_only_the_canonical_brand_source` | nguồn brand | `DEC-202` §9 — read model canonical thay vì trường trên value object |

Không test nào bị XOÁ, và không khẳng định nào bị nới lỏng mà không có một
khẳng định chặt hơn thay chỗ.

---

## 8. Rủi ro chấp nhận (`ACCEPTED_RISK`)

`AR-R5-01` — **Bản chiếu hiển thị danh mục sống trên đĩa ephemeral.**
`data/product_identity/tracking_display.json` được ghi mỗi khi một lần pull
danh mục đã được cho phép xảy ra vì lý do khác. Trên production (container
không có persistent disk), nó mất sau mỗi lần deploy cho tới lần mở bảng chọn
kế tiếp. Hệ quả: cột Hãng hiện `—` và tên hàng hiện mã Tracking thay vì model
ngắn. **Không con số nào sai** và không hãng nào bị đoán — màn hình chỉ nói ít
đi. Chi phí của một nơi lưu bền cho một bảng nhãn hiển thị không tương xứng.

`AR-R5-02` — **`business_save_line_purchase_price` và
`business_save_order_employee` vẫn tồn tại** dù không nút nào trên màn hình
gọi chúng. Chúng là bề mặt đã nghiệm thu của R2 §4.4 và `DEC-185` §F-02 và
mang bằng chứng test của cả hai vertical đó. Không có thẩm quyền thứ hai: mọi
đường vào đều gọi đúng `store.set_purchase_price`/`set_employee`, nơi ràng
buộc được thi hành MỘT lần cho mọi người gọi. Viết lại mười ba call site của
R2 để gỡ hai route là rủi ro lớn hơn phần thưởng.

`AR-R5-03` — **Danh sách hãng của Tracking là một danh sách đóng và chưa
đầy đủ.** Một hãng chưa có tên trong đó cho ra `null`. Đây là hành vi đã chọn,
không phải một khiếm khuyết: brief §5 nói rõ *"không cố nhận diện mọi hãng/
model hiếm"*. Thêm một dòng vào danh sách là đúng cách; nới quy tắc ghép để
"bắt được nhiều hơn" thì không.

`AR-R5-04` — **`current_totals()` trên trang snapshot vẫn đếm cả dòng đang bị
tạm loại.** Đó là một con số ĐỐI CHIẾU KỸ THUẬT về trạng thái kho lịch sử, và
bất biến đã nghiệm thu của PRA-002 (`test_the_removed_candidate_line_is_still_
current_and_still_counted`) nói đúng về nó. Trang nay NÓI RA điều đó bằng một
câu và chỉ đường tới con số kinh doanh chính thức. Rủi ro còn lại: một người
đọc chỉ nhìn con số mà không đọc câu.

`AR-R5-05` — **Toạ độ popover không được kiểm bằng một trình duyệt thật.**
Test khẳng định `app.js` có `clientX`/`clientY`, `Escape` và `is-anchored`, và
CSS có luật `is-anchored`; nhưng hình học thật (tràn viewport ở một kích thước
màn hình cụ thể) chỉ nhìn thấy bằng mắt. Đây là một finding xác suất thấp, tác
động nhỏ, và người dùng phát hiện ngay trong một lần bấm — đúng nhóm mà brief
§5 nói ghi `ACCEPTED_RISK` thay vì mở rộng scope.

---

## 9. Checklist nghiệm thu Owner — 8 luồng

Tám luồng của brief §7, viết lại thành thao tác. Không luồng nào được đánh dấu
bởi phiên này.

1. **Nạp file một phần thiếu một đơn.** Tổng KHÔNG đổi; trang snapshot nói
   "Không thấy trong sổ này (vẫn tính)".
2. **Bấm "Xác nhận đầy đủ" trên đúng sổ đó.** Thông báo nói rõ N dòng đã được
   TẠM LOẠI. Mở tab Nhân viên: khối "Không còn trong file đầy đủ" liệt kê đơn
   thiếu (Số BH · ngày cũ · sản phẩm · nhân viên), KHÔNG có ô tiền nào; doanh
   thu, lợi nhuận, DS quy đổi, Target và biểu đồ đều đã trừ nó ra; file Excel
   xuất ra không còn dòng đó. **Nạp lại một sổ CÓ đơn đó**: cảnh báo tự mất,
   mọi con số quay về.
3. **Mở một snapshot chỉ đổi phí giao/IMEI.** Ô "Cần soi" = 0 và không mục nào
   được liệt kê. Mở một snapshot có đổi doanh thu thật: mục ấy hiện, mang tên
   nhân viên, và bấm Số BH mở đúng tháng/sheet/dòng.
4. **Chuyển Ngày → Tuần → Tháng → Quý.** Luôn thấy HAI đường; chú thích nói rõ
   cửa sổ hiện tại và cửa sổ so sánh cùng khoảng thời gian của từng cái. Đối
   chiếu tay ba điểm bất kỳ. Ở mức Năm vẫn một đường.
5. **Mở sửa một BH nhiều dòng.** Ô chọn nhân viên nằm ngay hàng đầu; sửa hai
   giá và đổi nhân viên; bấm `XONG` ĐÚNG MỘT LẦN. Refresh và khởi động lại ứng
   dụng: mọi thứ còn nguyên. Thử gõ một giá sai định dạng: KHÔNG ô nào được
   lưu, và ô đúng cũng không.
6. **Một dòng đã phân loại** hiện model ngắn. Bấm `HIỆN HÃNG & IMEI`: hai cột
   hẹp xuất hiện, dữ liệu dài bị cắt MỘT DÒNG (hàng không cao lên), rê chuột
   xem đủ. Bấm `ẨN HÃNG & IMEI`: hai cột biến mất, và lựa chọn được nhớ khi
   chuyển sheet. Một dòng CHƯA phân loại vẫn hiện tên gốc và cột Hãng là `—`.
7. **Bấm phân loại ở một dòng giữa trang.** Popover xuất hiện TẠI CHỖ, trang
   không nhảy lên đầu. Gõ tìm: tối đa một gợi ý. Bấm gợi ý: dòng cập nhật tại
   chỗ. Thử "Không có trên bảng giá" trên một dòng khác.
8. **Chọn một đơn ngày 03/09** và đối chiếu tay: giá MIN của đúng ngày 03/09,
   lợi nhuận, file Excel xuất ra, và kỳ chốt/drift — để chắc R1–R4 không đổi.

---

## 10. Đầu vào cho Independent Review

Exact HEAD để review:

```text
Reports   19b853f718e1ed6dbf700468105c9dd38ff4cc2d
Tracking  f958226f6127e6055eb411e4c22e12c58d09654b
```

Lệnh tái lập, từ gốc mỗi repo:

```text
# Reports
uv venv .venv && VIRTUAL_ENV=$PWD/.venv uv pip install -e ".[dev,web,history]"
.venv/bin/python -m pytest -q
.venv/bin/python tools/smoke/r1_web_upload_smoke.py --tracking-repo <đường/dẫn/Tracking>
# `r1_daily_min_smoke.py` CẦN một file capture làm tham số, và nó đang CRASH
# với fixture có sẵn — lỗi baseline cũ, xem `S135` §5 (`AR-R5-IR-12`).
for v in governance/scripts/governance/validate_*.py; do .venv/bin/python "$v"; done
bash scripts/branch_authority_check.sh

# Tracking
node kiem/hang-va-model.js
npm test && npm run build
```

Bốn chỗ đáng soi kỹ nhất, theo thứ tự hậu quả:

1. `SnapshotRepository.removed_candidate_keys` + `BusinessReportService.
   _removed_in_source` — đây là nơi một lỗi làm TỔNG SAI THEO HƯỚNG THẤP HƠN,
   và thấp hơn thì khó thấy hơn cao hơn. Câu hỏi đúng để hỏi: có tổ hợp nào
   khiến một dòng bị loại mà KHÔNG có một hành động xác nhận tường minh của
   con người đứng phía sau không?
2. `revenue_timeline.paired_series` + `_covered_by_confirmed` — số 0 chỉ được
   vẽ khi mốc nằm TRỌN trong một khoảng đã xác nhận. Câu hỏi: có đường nào một
   khoảng phủ MỘT PHẦN biến thành số 0 không?
3. `BusinessReportService.plan_order_edit` — "không có thành công một phần"
   phải đúng theo cấu tạo. Câu hỏi: có nhánh nào ghi trước khi kiểm hết không?
4. `app/web/workspace_imei.py` và cây import của nó — phạm vi IMEI phải đọc
   được từ mã nguồn, không từ câu văn.

Nhóm `REPAIR_REQUIRED` theo brief §8: tổng sai khó thấy · sửa nhầm dòng/BH ·
mất persistence/audit · IMEI rò ngoài phạm vi · tự map sai · phá bất biến MIN.
