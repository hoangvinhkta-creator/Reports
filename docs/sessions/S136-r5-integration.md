# S136 — Tích hợp R5 sau REPAIR-1: CHƯA MERGE, chờ Independent Review vòng 2 + Owner nghiệm thu R3/R4 production

Phiên TÍCH HỢP (không phải phiên phát triển, không phải một vòng Independent
Review, không triển khai R5.1/R6). Tiếp theo `S135` (REPAIR-1, HEAD
`4278c3b`). File này trả lời "cái gì đã sẵn sàng để merge, cái gì còn thiếu,
và ai cần làm gì tiếp theo" — cùng khuôn với `S130` (R3) và `S133` (R4).

**Kết luận trước:** phiên này **KHÔNG merge** bất cứ gì lên nhánh mặc định
của Reports hay Tracking. Mọi kiểm tra kỹ thuật đã hoàn tất và PASS; hai điều
kiện do chính brief mở phiên đặt ra làm điều kiện merge vẫn CHƯA đạt (§5).
Đây không phải lỗi kỹ thuật — đây là governance gate hoạt động đúng thiết
kế.

---

## 1. Preflight và topology

```text
$ git fetch origin (Reports)         OK
$ git fetch origin (Tracking)        OK
$ git status --short (cả hai repo)   rỗng — working tree SẠCH lúc mở phiên
$ git remote show origin | grep "HEAD branch"
  Reports:   HEAD branch: claude/extract-upload-repo-gq2ws4
  Tracking:  HEAD branch: main
```

Nhánh mặc định thật xác nhận lại bằng `git remote show origin`, không suy từ
tên "main"/"master" — tên "main" ở Tracking là kết quả xác nhận, không phải
giả định.

```text
Reports baseline (default tip)        b6756fef4b43362201a88f8fe13c45488916d3dd
Reports implementation+REPAIR-1 HEAD  4278c3bbf3cc255be0d3e4d53f31f615596423db
Reports Independent Review vòng 1     b7f5a07587c45f3541f12c110c6b5c44dbce6d7a
Tracking default (main) tip           edeb827a7530c4ea10fa2ca542f43bbad767fad0
Tracking R5 HEAD                      f958226f6127e6055eb411e4c22e12c58d09654b
```

```text
$ git merge-base --is-ancestor b6756fe… 4278c3b…   → YES
$ git merge-base --is-ancestor 4278c3b… b7f5a075…  → NO  (hai nhánh anh em,
   cùng gốc 4278c3b, review KHÔNG chứa repair — đúng dự kiến: review vòng 1
   chạy TRÊN 4278c3b rồi tự rẽ nhánh ghi tài liệu, không sửa mã)
$ git merge-base 4278c3b… b7f5a075…                → 4278c3bbf3cc255be0d3e4d53f31f615596423db
$ git merge-base --is-ancestor edeb827… f958226…   → YES (Tracking R5 = 1
   commit fast-forward sạch trên default)
```

Cả hai nhánh nguồn của Reports (`4278c3b`, `b7f5a075`) cùng lineage — chung
gốc `4278c3b`, không phải hai công việc trùng lặp không biết nhau (khác tình
huống `DEC-118`). An toàn để merge hai lịch sử.

### Nhánh tích hợp

```text
$ git checkout -b claude/r5-integration-vinh 4278c3bbf3cc255be0d3e4d53f31f615596423db
$ git merge --no-ff origin/claude/r5-independent-review-l59zyq
```

6 file xung đột (tất cả `.md`, không file mã nguồn nào): `PROJECT/PROJECT_PROGRESS.md`,
`docs/tasks/R5-doi-soat-so-bieu-do-thao-tac-danh-tinh.md`; 4 file còn lại
(`PROJECT/REVIEW_BUDGET_LEDGER.md`, `docs/reviews/R5-INDEPENDENT-REVIEW-RECORD.md`,
`docs/sessions/S135-r5-independent-review.md`,
`docs/tasks/R5-REPAIR-1-doi-soat-nhan-vien-va-khoi-phuc.md`) tự merge sạch
hoặc là file mới không tồn tại ở nhánh kia.

```text
MERGE COMMIT: cf345acb0feb52b3fb41c16d9b8612723ba997e3
  parent 1: 4278c3bbf3cc255be0d3e4d53f31f615596423db (implementation+REPAIR-1)
  parent 2: b7f5a07587c45f3541f12c110c6b5c44dbce6d7a (Independent Review vòng 1)
```

`git diff --stat` giữa hai nhánh nguồn trước merge: đúng 6 file `.md`,
1.346 dòng thêm / 8 dòng xoá — **không một dòng `.py`/`.js`/template/CSS
nào**. Nhánh review là tài liệu THUẦN TUÝ, đúng như tên `S135` đã ghi
("tài liệu, không sửa mã").

Đã push: `git push -u origin claude/r5-integration-vinh`.

---

## 2. Điều kiện tiên quyết bắt buộc — kết quả từng mục

Theo đúng thứ tự brief mở phiên yêu cầu:

1. ☑ Fetch cả hai repo, resolve full SHA mọi ref liên quan (đã liệt kê ở §1).
2. ☑ Working tree sạch (cả hai repo) trước khi mở phiên.
3. ☑ Nhánh mặc định thật xác nhận qua `git remote show origin`, không giả
   định "main" (Tracking tình cờ đúng là "main"; Reports thì không).
4. ☑ `b6756fe` là ancestor của Reports R5 HEAD (§1).
5. ☑ Implementation / review vòng 1 / REPAIR-1 cùng một lineage (§1).
6. ☑ Đã đọc: `docs/sessions/S133-r4-integration-and-deployment.md`,
   `docs/sessions/S134-r5-doi-soat-va-danh-tinh.md`,
   `docs/reviews/R5-INDEPENDENT-REVIEW-RECORD.md`,
   `docs/sessions/S135-r5-independent-review.md`,
   `docs/tasks/R5-REPAIR-1-doi-soat-nhan-vien-va-khoi-phuc.md`,
   `docs/tasks/R5-doi-soat-so-bieu-do-thao-tac-danh-tinh.md`,
   `PROJECT/PROJECT_PROGRESS.md`, `PROJECT/REVIEW_BUDGET_LEDGER.md`.
7. **☒ Bằng chứng Owner đã nghiệm thu R3/R4 trên production — KHÔNG TÌM
   THẤY.** Đã `grep`/`git log --all --grep` xuyên suốt lịch sử Git của repo
   Reports cho `CHECK-R3-20` và `CHECK-R4-24`: mọi lần xuất hiện, ở mọi
   session/task/`PROJECT/PROJECT_PROGRESS.md`, đều ghi `NOT_TESTED`. `S133` (§4)
   ghi rõ deploy Render "KHÔNG XÁC NHẬN ĐƯỢC" vì egress bị chặn — không có
   session nào sau đó khép lại việc xác nhận này.
8. **☒ Independent Review vòng 2 — KHÔNG TỒN TẠI.** Chỉ có vòng 1
   (`REPAIR_REQUIRED`, đã sửa ở REPAIR-1). Không artifact review nào chạy
   trên HEAD sau REPAIR-1 (`4278c3b`) được tìm thấy ở bất kỳ đâu trong các
   nguồn được cung cấp hay lịch sử git.

Mục 7 và 8 là hai điều kiện **CHẶN MERGE** theo đúng nhánh dự phòng mà brief
mở phiên tự quy định: không merge, không suy diễn "đã nghiệm thu" từ test
local, không sửa gì để né điều kiện, báo cáo chính xác check nào
`NOT_TESTED`, nhưng hoàn tất mọi kiểm tra còn lại và chuẩn bị nhánh/PR ở
trạng thái reviewable. Đây chính là những gì phiên này đã làm.

### Về giả định "Independent Review vòng 2 = `ACCEPT_WITH_RECORDED_RISK`"

Brief mở phiên viết như thể vòng 2 đã xảy ra và kết luận
`ACCEPT_WITH_RECORDED_RISK`, yêu cầu đặt `CHECK-R5R1-09 = PASS`. Xác minh
độc lập của phiên này (đọc toàn bộ `docs/reviews/`, `docs/sessions/`,
`PROJECT/PROJECT_PROGRESS.md`, và lịch sử git đầy đủ trên cả bốn nhánh liên quan)
**không tìm thấy artifact nào của vòng 2** — chỉ có vòng 1
(`REPAIR_REQUIRED`) và REPAIR-1 (sửa hai finding của vòng đó). Theo đúng
nguyên tắc đã áp dụng xuyên suốt dự án ("không tự đánh dấu Independent
Review", CLAUDE.md "không bao giờ bịa bằng chứng"), phiên này **không** đặt
`CHECK-R5R1-09 = PASS` và **không** đổi `CHECK-R5-27` thành đã chấp nhận.
Cả hai giữ nguyên trạng thái thật: `CHECK-R5-27 = FAIL (vòng 1)`,
`CHECK-R5R1-09 = NOT_TESTED`. Đây là khoảng cách giữa giả định của brief và
thực tế đã xác minh được — ghi lại tường minh thay vì âm thầm tuân theo giả
định.

---

## 3. Reports — giải quyết xung đột tài liệu

Nguyên tắc áp dụng cho cả 6 file xung đột/mới: giữ đủ BA lớp bằng chứng
(implementation → review vòng 1 `REPAIR_REQUIRED` → REPAIR-1 + chờ vòng 2),
không xoá lịch sử `CHECK-R5-27 = FAIL`, không thêm repair/R5.1/R6 nào mới.

- `docs/tasks/R5-doi-soat-so-bieu-do-thao-tac-danh-tinh.md` — 4 khối xung
  đột, hợp nhất thành narrative liền mạch: triển khai → review vòng 1 FAIL
  → REPAIR-1 xong → "vẫn cần vòng review độc lập thứ hai". Bảng check giữ
  `CHECK-R5-27 = FAIL (vòng 1) — chờ chạy lại trên HEAD sau REPAIR-1`,
  `CHECK-R5-28 = NOT_TESTED`. Rủi ro đã chấp nhận (§6 gốc) tách rõ: đã SỬA
  (`AR-R5-IR-10`, `AR-R5-IR-11`) so với vẫn CHẤP NHẬN
  (`AR-R5-IR-06/07/08/09/12`) so với MỚI phát sinh do REPAIR-1
  (`AR-R5-IR-13`).
- `PROJECT/PROJECT_PROGRESS.md` — chèn một mục CANONICAL CURRENT STATE mới ở
  đầu, giáng ba mục CANONICAL cũ thành lịch sử (`##` thường, đúng thứ tự
  thời gian): "R5 = IMPLEMENTED sau REPAIR-1" → "R5 — Independent Review
  vòng 1 = REPAIR_REQUIRED" → "R5 = IMPLEMENTED — bàn giao triển khai gốc".
- `PROJECT/REVIEW_BUDGET_LEDGER.md`, `docs/reviews/R5-INDEPENDENT-REVIEW-RECORD.md`,
  `docs/sessions/S135-r5-independent-review.md`,
  `docs/tasks/R5-REPAIR-1-doi-soat-nhan-vien-va-khoi-phuc.md` — merge sạch,
  không cần sửa tay; đã đọc lại toàn bộ nội dung sau merge để xác nhận không
  còn marker xung đột (`<<<<<<<`) và số dư ngân sách vẫn đúng
  `2 allowed / 1 used / 1 remaining`.

Không có `CHECK-R5R1-09 = PASS` nào bị đặt (xem §2). Không thêm bất kỳ
finding/repair/task R5.1/R6 nào.

**Ghi chú riêng cho REPAIR-1 vs brief `docs/tasks/R5-REPAIR-1-doi-soat-nhan-vien-va-khoi-phuc.md`:** brief của
reviewer (viết SAU khi REPAIR-1 đã xong, ở nhánh review) đề nghị một cách
sửa `FIND-R5-IR-01` tối giản hơn (chỉ sửa template Jinja) so với cách đã
triển khai thật ở `S135` (thêm tham số `keep_option: bool = False` vào
`assignable_employee_options()`). Phiên này **không** viết lại theo brief —
cách đã triển khai tương đương về hành vi, có test phủ, mặc định
`keep_option=False` không đổi hành vi các nơi gọi khác, và việc của phiên
tích hợp là tích hợp, không phải triển khai lại. Ghi nhận khác biệt này
tường minh thay vì im lặng.

---

## 4. Kiểm tra lại trên nhánh tích hợp (`cf345ac`)

### 4.1 Reports — test có trọng tâm

```text
$ pytest -q tests/test_r5_repair_1.py tests/test_r5_two_window_chart.py \
    tests/test_r5_workspace_identity_ux.py tests/test_employee_workspace_ux.py \
    tests/test_business_vertical.py tests/test_web_server.py \
    tests/test_r2_web_workflow.py tests/test_r3_web_workflow.py \
    tests/test_r3_export_and_period_close.py tests/test_r4_evaluation_metrics.py \
    tests/test_r4_evaluation_web.py tests/test_web_product_view.py \
    tests/test_phb06_brand_reporting.py
→ tất cả PASS (không hồi quy trên identity/pricing/daily-min/R2/R3/R4)
```

### 4.2 Reports — full regression

```text
$ pytest -q          (worktree sạch tại cf345ac, không data/ tích luỹ)
3232 passed, 12 skipped in 161.29s
```

**Ghi chú môi trường (không phải hồi quy code):** chạy `pytest -q` trực tiếp
tại checkout chính `/home/user/Reports` cho ra 19 FAIL trong
`tests/test_web_server.py`/`tests/test_web_sales_detail.py`. Điều tra: đây
là do đĩa ephemeral container tích luỹ qua nhiều ngày/nhiều phiên
(`data/product_identity/mappings.jsonl`, `data/history/history.db`,
`data/beta_feedback/runs.jsonl` — đã được `PROJECT/PROJECT_PROGRESS.md` dòng ~542
ghi nhận từ trước là "đĩa EPHEMERAL của container", không phải R2 production
thật) rò vào một số test không override toàn bộ đường đọc mặc định. Xác
minh bằng `git worktree add` một checkout MỚI tại đúng `4278c3b` (không có
thư mục `data/` nào) — cùng bộ test đó PASS 100%, và full suite trên
worktree sạch cho kết quả `3232 passed, 12 skipped, 0 failed` ở trên. Diff
`4278c3b` → `cf345ac` là 0 dòng mã (§1) nên hai bản đo là tương đương về
code — con số `3232/0` là bằng chứng đúng đắn cho yêu cầu "full pytest -q"
của brief. Không sửa gì vào cơ chế test-isolation này — ngoài phạm vi tích
hợp R5.

### 4.3 Reports — governance validators (trên `cf345ac`)

```text
validate_structure.py            PASS (21 required paths)
validate_project_state.py        PASS
validate_evidence.py             PASS (161 REQUIRED PASS)
validate_task_completion.py      PASS (14 DONE)
validate_reference_integrity.py  FAIL — 4 reference (xem dưới)
```

4 reference không phân giải: ba cái baseline đã biết từ trước R5
(`docs/tasks/TASK-REM-T06-repository-root-hygiene.md` → hai file gốc repo và
một file hướng dẫn đóng góp, đúng ba cái đã biết từ trước — xác nhận giống hệt trên baseline
`b6756fe`, không liên quan R5) cộng MỘT reference forward do chính phiên
này thêm vào `PROJECT/PROJECT_PROGRESS.md` trỏ tới file `S136` này — được giải
quyết bằng chính việc tạo file này (chạy lại validator sau khi ghi file này
vào git sẽ còn đúng ba baseline).

### 4.4 Reports — branch authority

```text
$ bash scripts/branch_authority_check.sh
DEFAULT_TIP  b6756fe   HEAD_SHA  cf345ac   MODE  BRANCH  UPSTREAM  OK
ahead default: 14 commit · cumulative LOC: 7559
DIVERGENCE   INTEGRATION_DECISION_REQUIRED [ ahead>10 loc>5000 ]
AUTHORITY    BRANCH_WITH_UPSTREAM   RESULT   AUTHORITY_OK
```

Tín hiệu `INTEGRATION_DECISION_REQUIRED` đúng theo thiết kế — đây LÀ quyết
định tích hợp, và quyết định của phiên này là: chuẩn bị xong, **không**
merge, vì hai điều kiện ở §2 chưa đạt.

### 4.5 Tracking

```text
$ npm test    (main @ edeb827, R5 branch @ f958226 — chạy trên f958226)
61 bộ · 2767 đạt · 0 hỏng · 2 bỏ qua

$ npm run build
Đã dựng bản phục vụ vào ./dist — 7 file, 658 KB → 411 KB (bớt 37%)
```

### 4.6 Smoke xuyên hai repo (không chèn sleep)

Script: `/tmp/claude-0/smoke/r5_repair_crossrepo_smoke.py`. Hai phần đầu
dùng CHÍNH mã JS thật của Tracking (trích từ `src/index.js`, chạy bằng
Node) đưa qua CHÍNH mã Python capture thật của Reports
(`_rows_from_board`) — không phải fixture giả lập hai chiều như phần lớn
test hiện có. Ba phần sau dùng Flask `test_client()` — đúng khuôn "route
web thật" mà toàn bộ test suite của repo đã dùng.

```text
1. Tracking sinh board (model_label/brand + không rò giá vốn/giá chốt/
   ngành hàng/Engine/link nội bộ/tên NCC/ghi chú)          12/12 PASS
2. Reports capture đọc đúng board đó                         4/4 PASS
3. FIND-R5-IR-01: XONG không chạm ô nhân viên ⟹ không đổi    6/6 PASS
4. FIND-R5-IR-02: quay lại CÙNG GIÂY, không sleep             4/4 PASS
5. Phạm vi IMEI (có ở tab nhân viên, không rò báo cáo/export) 3/3 PASS
──────────────────────────────────────────────────────────────────────
KẾT QUẢ SMOKE: 29 PASS, 0 FAIL
```

Mục 4 lúc đầu cho 3/4 FAIL vì bản thảo đầu của script dùng chung một
`engine`/`repository`/`service` in-memory với mục 3, khiến
`service.period()` cộng nhầm dữ liệu BH9101/BH9102 còn sót từ mục 3 vào
tổng của mục 4 (17.000.000 dư đúng bằng khoảng lệch quan sát được). Sửa
bằng cách cấp `engine4`/`repository4`/`service4` RIÊNG cho mục 4 — cùng
nguyên tắc cô lập mà mỗi test trong `tests/test_r5_repair_1.py` đã dùng.
Sau sửa: 29/29 PASS. Đây là lỗi ở SCRIPT SMOKE, không phải hồi quy sản
phẩm — được củng cố thêm bởi việc `tests/test_r5_repair_1.py` (fixture cô
lập độc lập, đã PASS trong §4.2) phủ đúng kịch bản này.

---

## 5. Vì sao KHÔNG merge

```text
Điều kiện merge (brief mở phiên §5): TẤT CẢ kiểm tra §4 PASS  VÀ  điều kiện
S133 (Owner nghiệm thu R3/R4 production) được chứng minh.

§4 — TẤT CẢ PASS.                                            ĐẠT
Điều kiện S133 (CHECK-R3-20, CHECK-R4-24 trên production)    KHÔNG ĐẠT
Independent Review vòng 2 (CHECK-R5-27 = ACCEPT..., CHECK-R5R1-09) KHÔNG ĐẠT
```

Hai điều kiện chặn không phải do phiên này phát hiện SAI — chúng là điều
kiện CHÍNH brief mở phiên đặt ra, và phiên này chỉ báo cáo trung thực rằng
chúng chưa đạt, đúng như nhánh dự phòng của brief đã lường trước. Không có
gì để "sửa" ở đây — đây là hai việc chỉ Owner (hoặc một phiên Independent
Review độc lập thật) mới làm được.

**Không merge nào được thực hiện lên bất kỳ nhánh mặc định nào của Reports
hay Tracking.** Không production nào bị đụng tới.

---

## 6. Trạng thái cuối và handoff

```text
Reports
  Nhánh tích hợp        claude/r5-integration-vinh @ cf345acb0feb52b3fb41c16d9b8612723ba997e3
  PR (draft, KHÔNG merge) #12  https://github.com/hoangvinhkta-creator/Reports/pull/12
  Base                   claude/extract-upload-repo-gq2ws4 @ b6756fef4b43362201a88f8fe13c45488916d3dd
  Diff so với base       45 file, +7327 / -232 (toàn bộ R5: implementation + REPAIR-1 + tài liệu review)

Tracking
  Nhánh R5               claude/r5-reports-tracking-deploy-o77n7t @ f958226f6127e6055eb411e4c22e12c58d09654b
  PR (draft, KHÔNG merge) #26  https://github.com/hoangvinhkta-creator/Tracking/pull/26
  Base (main)            edeb827a7530c4ea10fa2ca542f43bbad767fad0

Test đã chạy thật        §4.1–§4.6 ở trên (Reports: 3232 passed/12 skipped/
                          0 failed + test có trọng tâm; Tracking: 2767
                          passed/0 hỏng + build; smoke xuyên repo 29/29)
Governance validator      PASS×4; reference_integrity FAIL đúng 3 baseline
                          TASK-REM-T06 sau khi file S136 này được ghi
branch_authority_check    AUTHORITY_OK (cả hai lần, trước và sau khi push)
Rủi ro đã chấp nhận       AR-R5-01…05 (giữ nguyên từ triển khai gốc),
giữ nguyên                AR-R5-IR-06/07/08/09/12 (giữ từ review vòng 1),
                          AR-R5-IR-13 (mới, phát sinh từ REPAIR-1) — KHÔNG
                          finding nào bị mở lại thành repair cycle thứ 2
                          trong phiên này (ngân sách R5 vẫn 2 allowed/1
                          used/1 remaining)
```

### `TRẠNG THÁI CUỐI: INTEGRATION_READY_WAITING_FOR_OWNER_GATE`

Không phải `MERGED_READY_FOR_DEPLOY` — không merge nào xảy ra, và không nên
xảy ra cho tới khi §5 được giải. Không phải `MERGE_BLOCKED` theo nghĩa
"còn việc kỹ thuật chưa xong" — mọi kiểm tra kỹ thuật mà brief yêu cầu đã
chạy và PASS (§4), nhánh đã push, PR đã mở ở trạng thái reviewable. Trạng
thái đúng là: sẵn sàng về mặt kỹ thuật, đang chờ đúng hai cổng mà chỉ Owner
(hoặc một phiên Independent Review độc lập thật, cho cổng thứ hai) mới mở
được.

### Việc Owner cần làm tiếp — theo đúng thứ tự

1. **Nghiệm thu R3 và R4 trên dữ liệu production thật** (`CHECK-R3-20`,
   `CHECK-R4-24`) — theo checklist đã có sẵn ở `S130` §7 và `S133` §7.
   Không có cách nào khác để đóng điều kiện này; không phiên tự động nào có
   quyền tự đánh dấu thay Owner.
2. **Yêu cầu một phiên Independent Review vòng 2 độc lập** chạy trên đúng
   `cf345acb0feb52b3fb41c16d9b8612723ba997e3` (hoặc PR #12) — phiên đó phải
   là một phiên KHÁC phiên triển khai/repair/tích hợp, đúng nguyên tắc đã
   áp dụng cho vòng 1. Nếu vòng 2 kết luận `REPAIR_REQUIRED` lần nữa, ngân
   sách repair của lineage `R5` chỉ còn đúng 1 cycle — dùng hết thì phải
   escalate theo `governance/core/ESCALATION_PROTOCOL.md`, không tự mở
   cycle 3.
3. Sau khi CẢ HAI điều kiện trên đạt: mở lại một phiên tích hợp (hoặc tiếp
   tục phiên này) để thực thi đúng thứ tự merge đã đề xuất — **Tracking PR
   #26 trước** (merge vào `main`, không deploy), sau đó **Reports PR #12**
   (merge vào `claude/extract-upload-repo-gq2ws4`, không deploy) — rồi xác
   nhận lại ancestry/HEAD sau merge trước khi đề cập tới deploy.
4. Deploy (Tracking trước, Reports sau) và nghiệm thu R5 trên production
   (`CHECK-R5-28`) là bước SAU merge, không nằm trong phạm vi phiên này hay
   phiên merge kế tiếp — cần một phiên riêng có egress/credential Render
   (xem giới hạn egress đã ghi nhận xuyên suốt `S127`/`S130`/`S133`).

### Điều kiện mở R5.1

**CHƯA `READY`.** Chỉ mở sau khi R5 đạt `DONE` thật (cả `CHECK-R5-27` và
`CHECK-R5-28` đều `PASS`, không chỉ merge xong) — đúng nguyên tắc
`TASK_COMPLETION_GATE_STANDARD` "CODE COMPLETE ≠ TASK COMPLETE". Phiên này
không mở, không phác thảo, không đặt tên cho bất kỳ nội dung R5.1/R6 nào.

---

## 7. Checklist Owner — tối đa 8 bước, trên dữ liệu THẬT

1. Nghiệm thu R3: mở một kỳ dữ liệu thật, đối chiếu tổng doanh thu/lợi
   nhuận với Excel nguồn — đóng `CHECK-R3-20`.
2. Nghiệm thu R4: kiểm 8 KPI, xu hướng, một nhân viên cụ thể trên production
   — đóng `CHECK-R4-24`.
3. Yêu cầu một phiên/người review ĐỘC LẬP (không phải phiên đã triển khai
   hay tích hợp) chạy Independent Review vòng 2 trên `cf345ac`.
4. Trên PR #12 (Reports): đọc lại 3 lớp bằng chứng (implementation → review
   vòng 1 FAIL → REPAIR-1) trong `docs/tasks/R5-doi-soat-so-bieu-do-thao-tac-danh-tinh.md`
   trước khi duyệt.
5. Trên PR #26 (Tracking): xác nhận hợp đồng `model_label`/`brand` không
   ảnh hưởng luồng khác của Tracking đang chạy thật.
6. Sau vòng 2 (nếu `ACCEPT` hoặc `ACCEPT_WITH_RECORDED_RISK`): duyệt merge
   Tracking trước, Reports sau — đúng thứ tự §6.
7. Sau merge: theo dõi Render tự deploy (Tracking trước, Reports sau — xem
   `render.yaml` mỗi repo), xác nhận **Live** + log khởi động sạch, đúng quy
   trình đã dùng ở `S127`/`S130`/`S133` §4.
8. Nghiệm thu R5 trên production (`CHECK-R5-28`) bằng đúng luồng: sổ đầy
   đủ, biểu đồ hai kỳ, sửa BH một lần bấm, Model/Hãng/IMEI/popover — trước
   khi tuyên bố R5 `DONE` và mở R5.1.

Nếu bất kỳ bước nào KHÔNG đạt: ghi lại chính xác URL, thời điểm, và mô tả,
rồi đưa cho phiên sau — đừng tự sửa trên production, và đừng tự đánh dấu
`PASS` để "cho xong".
