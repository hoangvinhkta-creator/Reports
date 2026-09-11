# S133 — Tích hợp production R4: merge THẬT, deploy platform KHÔNG xác nhận được

Phiên TÍCH HỢP/TRIỂN KHAI (không phải phiên phát triển, không phải một vòng
Independent Review mới, không triển khai nội dung R5). Tiếp theo `S132` sau
khi Independent Review kết luận **`ACCEPT_WITH_RECORDED_RISK`** trên exact
HEAD `63a066e9`. File này trả lời "cái gì đã lên git production, cái gì chưa
lên platform thật, và Owner cần bấm gì" — cùng khuôn với `S127` (R1) và `S130`
(R3).

---

## 1. Preflight và topology

```text
$ git fetch origin
$ git status --short          (rỗng — working tree SẠCH lúc mở phiên)
$ git remote show origin | grep "HEAD branch"
  HEAD branch: claude/extract-upload-repo-gq2ws4
```

Nhánh mặc định THẬT xác nhận lại bằng `git remote show origin`, không suy từ
tên "main"/"master" — đúng `claude/extract-upload-repo-gq2ws4`, tip lúc mở
phiên `824b5d742dab07b8b0bd301d56748779e35076aa` (= nền đã review).

```text
R4 implementation HEAD   63a066e9275919df92bceaee58876f2724cf9df0
Review + tài liệu HEAD   ed419cd78edabae7a93d652add5fdb4f51ee218c

$ git merge-base --is-ancestor 63a066e9… ed419cd7…  → YES
   (review HEAD chứa TRỌN VẸN implementation HEAD — chỉ tích hợp review
   branch MỘT LẦN, không merge thêm implementation branch để tránh trùng
   commit)
$ git merge-base --is-ancestor ed419cd7… 824b5d74…  → NO  (đúng, chưa merge)
$ git merge-base --is-ancestor 824b5d74… ed419cd7…  → YES (nền đúng là gốc)
```

Đúng NĂM commit trên nền `824b5d7` → `ed419cd`: ba commit implementation
(`86cee40`, `ea6413d`, `63a066e`) + hai commit review (`0486871`, `ed419cd`).
Không session nào khác đang ghi cùng checkout (`git branch -a` không có
worktree/lock nào khác của phiên này).

### Phạm vi diff — default → review HEAD

```text
$ git diff --stat 824b5d7..ed419cd
17 file, +5765 / -8
```

Đúng 17 file: 3 tài liệu Independent Review + tài liệu S131/DEC-201/spec/task
(đã có từ trước, không đổi thêm) cộng 12 file mã nguồn/test/CSS/template của
chính R4 implementation. `git diff --name-only` xác nhận:

- **Không** đường dẫn nào chạm `tools/tracking/` hay bất kỳ thứ gì thuộc repo
  Tracking.
- **Không** file nào dưới `tools/db/migrations/versions/` — R4 không có
  migration mới.
- **Không** một dòng nào chạm công thức MIN (`app/modules/pricing/`).
- **Không** nội dung R5 nào (không task/spec/session nào mang tiền tố `R5`).

### R3 migration `0009` và đường chạy production

```text
$ find tools/db/migrations/versions -iname "*0009*"
tools/db/migrations/versions/0009_line_binding_period_close.py   → CÓ MẶT

$ tail -3 Dockerfile (CMD)
CMD ["sh", "-c", "alembic upgrade head && gunicorn --workers 2 --threads 4 \
  --bind 0.0.0.0:${PORT} --timeout 300 app.web.wsgi:application"]
```

Migration chạy TRƯỚC khi gunicorn mở cổng, nối bằng `&&` — `alembic upgrade
head` lỗi thì container KHÔNG khởi động (fail-closed), app không bao giờ
nhận traffic trên schema cũ/thiếu. Chain revision xác nhận `0009` là head
(`down_revision` nối liền từ `0001` → `0009`, không nhánh rẽ). R4 không thêm
migration nào — `alembic upgrade head` sau merge này vẫn dừng đúng ở `0009`.

---

## 2. Gate trước merge — bằng chứng tự chạy lại

Môi trường: venv riêng (Python 3.11.15, Flask 3.1.3, SQLAlchemy 2.0.52),
chạy trên chính review HEAD `ed419cd` trước khi mở PR.

```text
$ python -m pytest -q tests/test_r4_evaluation_metrics.py tests/test_r4_evaluation_web.py
88 passed in 6.24s

$ python -m pytest -q tests/test_business_metrics.py tests/test_business_boundaries.py \
    tests/test_business_vertical.py tests/test_employee_workspace_ux.py \
    tests/test_r2_web_workflow.py tests/test_r3_web_workflow.py \
    tests/test_r3_export_and_period_close.py tests/test_web_server.py \
    tests/test_uiux_refinement.py
300 passed in 20.69s

$ python -m pytest -q
3146 passed, 12 skipped in 145.59s (0:02:25)
```

```text
$ python governance/scripts/governance/validate_structure.py           PASS (21 required paths)
$ python governance/scripts/governance/validate_project_state.py       PASS
$ python governance/scripts/governance/validate_evidence.py            PASS (161 REQUIRED PASS)
$ python governance/scripts/governance/validate_task_completion.py     PASS (14 DONE)
$ python governance/scripts/governance/validate_reference_integrity.py FAIL
  Quét 271 file .md — ĐÚNG BA reference baseline TASK-REM-T06
  (docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> /README.md,
   CODE_OF_CONDUCT.md, CONTRIBUTING.md) — không liên quan R4.
```

```text
$ bash scripts/branch_authority_check.sh
DEFAULT_TIP  824b5d7   HEAD_SHA  ed419cd   MODE  BRANCH  UPSTREAM  OK
DIVERGENCE   INTEGRATION_DECISION_REQUIRED [ loc>5000 ]   (tín hiệu cần
             quyết, không phải STOP — xem S132 §10; quyết định tích hợp
             CHÍNH LÀ phiên này, đã được Owner uỷ quyền trong prompt mở
             phiên)
AUTHORITY    BRANCH_WITH_UPSTREAM   RESULT   AUTHORITY_OK
```

Không finding nào của `AR-R4-01…07` được mở lại thành repair: không cái nào
tái hiện thành sai tổng/KPI, route production hỏng, mất dữ liệu, ghi nhầm kỳ
hay deploy không khởi động — đúng điều kiện brief đặt ra để KHÔNG động vào
chúng trong phiên tích hợp này.

---

## 3. PR và merge

```text
PR      #10  https://github.com/hoangvinhkta-creator/Reports/pull/10
Tiêu đề "R4: báo cáo đánh giá KPI, xu hướng và chất lượng dữ liệu"
head    claude/r4-independent-review-4fbga6 @ ed419cd
base    claude/extract-upload-repo-gq2ws4 @ 824b5d7
```

Mô tả PR nêu đủ tám KPI, target/xu hướng, đóng góp, chất lượng dữ liệu,
drill-down, timezone UTC+7, bảng test, và liệt kê `AR-R4-01…07` là rủi ro đã
ghi nhận — không phải lỗi chặn merge.

### Check CI ("governance" workflow) — đỏ, và ĐÃ XÁC MINH là baseline

```text
Check "validate" trên PR HEAD ed419cd  → FAILURE
  validate_reference_integrity.py crash: PermissionError: [Errno 13]
  Permission denied: '/root/.ccr/README.md'
```

Đây KHÔNG phải một lỗi mới của R4. Reviewer lấy log CI của chính commit nền
`824b5d7` (chạy #396/#397, trước khi R4 tồn tại) và log CI của PR head
`ed419cd` — **cùng traceback, cùng số dòng, cùng thông điệp lỗi** (script
`validate_reference_integrity.py` gọi `(root / ref).exists()` trên một
đường dẫn TUYỆT ĐỐI ghi trong `docs/deployment/S071_DEPLOYMENT.md`
[`/root/.ccr/README.md`, trích dẫn từ bằng chứng của một phiên S071 trước
đây]; runner GitHub Actions chạy bằng user `runner` không có quyền `stat()`
vào `/root/`, nên script crash bằng traceback thay vì in ra báo cáo FAIL
gọn như khi chạy local). Đây là một crash CI đã tồn tại xuyên suốt R1→R3
(merge PR #6, #8, #9 đều có cùng "validate" check đỏ với đúng traceback này)
và KHÔNG phải branch protection bắt buộc — không workflow nào khác tồn tại
trong repo (`governance` là workflow DUY NHẤT). Vì vậy merge được tiến hành
đúng như tiền lệ R1–R3.

### Merge

```text
$ merge_pull_request(pullNumber=10, merge_method="merge",
                     expectedHeadSha=ed419cd78edabae7a93d652add5fdb4f51ee218c)
→ merged: true
  sha: ab5e07d9807c591d6a04584556dacd72689a4ea8
  parents: 824b5d742dab07b8b0bd301d56748779e35076aa
           ed419cd78edabae7a93d652add5fdb4f51ee218c
```

**MERGE COMMIT: `ab5e07d9807c591d6a04584556dacd72689a4ea8`** trên
`claude/extract-upload-repo-gq2ws4`. `git diff ed419cd ab5e07d --stat` rỗng —
merge sạch, không sửa gì thêm ngoài kết hợp hai lịch sử. Xác nhận lại sau khi
fetch: `origin/claude/extract-upload-repo-gq2ws4` tại `ab5e07d`, chứa cả
`63a066e9` (implementation) lẫn `ed419cd` (review) làm ancestor.

Validators + `branch_authority_check.sh` chạy LẠI trên chính `ab5e07d` (không
phải chỉ tin bản review trên `ed419cd`): PASS/PASS/PASS/PASS,
`validate_reference_integrity` FAIL đúng ba reference cũ, `AUTHORITY_OK`,
`DEFAULT_TIP == HEAD_SHA == ab5e07d`, `DIVERGENCE: WITHIN_LIMITS` (0 commit
lệch — chính nó bây giờ LÀ default).

---

## 4. Deploy Render Reports — KHÔNG XÁC NHẬN ĐƯỢC

```text
$ curl https://api.render.com        → CONNECT tunnel failed, 403
$ curl https://dashboard.render.com  → CONNECT tunnel failed, 403
$ curl https://reports.tinphatcrm.com → CONNECT tunnel failed, 403
$ WebFetch(reports.tinphatcrm.com)   → EGRESS_BLOCKED (proxy chính sách tổ chức)
```

Egress mạng của phiên này bị proxy tổ chức từ chối tới CẢ BA domain (Render
admin/API, và chính domain production) — cùng giới hạn đã ghi nhận xuyên
suốt `S127`/`S130`/`S131`/`S132`. Phiên KHÔNG có credential Render. Không
route nào khác (API key, webhook, SSH) được cung cấp trong prompt mở phiên
này để bỏ qua giới hạn egress.

**Vì vậy: phiên này KHÔNG tuyên bố production đã lên.** Trạng thái deploy
Render sau merge `ab5e07d` là **`DEPLOY_NOT_VERIFIED`**.

Repo dùng Render Blueprint tự động deploy khi push lên nhánh liên kết
(`render.yaml`, `services[0].name: reports-web`, region `virginia`) — theo
cấu hình đã ghi, Render SẼ tự kích hoạt build+deploy khi thấy commit mới
trên `claude/extract-upload-repo-gq2ws4`, không cần bấm gì thêm. Nhưng
"sẽ tự chạy" không phải bằng chứng "đã chạy xong và healthy" — Owner phải tự
xác nhận qua Render Dashboard.

### Việc Owner cần làm để xác nhận deploy (ngắn)

1. Mở Render Dashboard → service `reports-web` → tab **Events**. Tìm sự kiện
   deploy gắn với commit `ab5e07d` (hoặc thời điểm merge PR #10).
2. Xác nhận trạng thái **Live** (không phải *Deploy failed* hay đang treo ở
   *Building*).
3. Mở tab **Logs**, tìm dòng `alembic upgrade head` chạy xong KHÔNG lỗi, rồi
   `gunicorn` khởi động và `Listening at: 0.0.0.0:8080` (hoặc tương đương)
   xuất hiện SAU đó — đúng thứ tự Dockerfile CMD.
4. Nếu deploy FAIL: đọc log tới nguyên nhân gốc, dán lại cho phiên sau xử lý.
   **Không** tự sửa bằng cách bỏ qua migration hay khởi động app trước khi
   `alembic upgrade head` xong — đó chính là fail-closed mà Dockerfile cố ý
   dựng.

---

## 5. Production smoke — KHÔNG THỰC HIỆN ĐƯỢC (cùng lý do §4)

Mọi mục ở đây yêu cầu egress tới `reports.tinphatcrm.com`, hiện bị chặn.
Phiên **không** tự ý dùng dữ liệu synthetic để tuyên bố smoke đã qua trên
production — làm vậy sẽ nói dối về "trên dữ liệu thật".

Danh sách route + hành vi Owner cần tự xác nhận (đưa xuống §7 dưới dạng
checklist ngắn), tổng hợp lại đây làm tham chiếu kỹ thuật:

```text
GET /                          → 200 (health/root)
GET /kinh-doanh                → 200, có đường "MỞ BÁO CÁO ĐÁNH GIÁ →"
GET /kinh-doanh/nhan-vien      → 200
GET /kinh-doanh/hang (Hãng)    → 200
GET /kinh-doanh/danh-gia?ky=<kỳ có dữ liệu>
                                → 200, 8 KPI render, không 500
GET /kinh-doanh/gia-nhap?...loc=... (drill-down từ trang đánh giá)
                                → 200, không mở rộng phạm vi ngoài ý muốn
```

Biểu đồ mặc định mức **Ngày**, đổi được Ngày/Tuần/Tháng/Quý/Năm — hành vi kế
thừa từ trang Báo cáo (không đổi bởi R4), Owner tự bấm thử. `as_of` trên
trang đánh giá phải đọc `DD/MM/YYYY` theo giờ Việt Nam — dễ kiểm nhất vào
khung giờ 17:00–24:00 giờ VN, đúng khung giờ mà lỗi `_today()` cũ (đã sửa ở
R4 §5) từng lộ ra.

---

## 6. Trạng thái cuối và handoff

```text
PR                    #10  https://github.com/hoangvinhkta-creator/Reports/pull/10  (MERGED)
Merge commit           ab5e07d9807c591d6a04584556dacd72689a4ea8
Default branch thật    claude/extract-upload-repo-gq2ws4  (tip = merge commit trên)
Render deploy ID/commit  KHÔNG XÁC NHẬN ĐƯỢC — không egress, không credential
Migration              0009_line_binding_period_close vẫn là head; R4 không
                        thêm migration; Dockerfile fail-closed (alembic
                        upgrade head && gunicorn ...)
Test (pre-merge)       R4 focused 88 passed; nhóm business/reporting/target/
                        period-close/pricing 300 passed; full regression
                        3146 passed, 12 skipped (nền: 3058 passed, 12
                        skipped, +88/0 hồi quy — đo ở S132)
Validator/gate         PASS×4, reference_integrity FAIL đúng baseline
                        TASK-REM-T06 (không đổi), branch_authority_check
                        AUTHORITY_OK cả trước và sau merge
Smoke production        KHÔNG THỰC HIỆN ĐƯỢC — không egress tới
                        reports.tinphatcrm.com (curl 403 + WebFetch
                        EGRESS_BLOCKED)
Accepted risks giữ      AR-R4-01 … AR-R4-07 (không cái nào mở lại thành
nguyên                  repair trong phiên này — không tái hiện thành lỗi
                        deploy/luồng chính)
Rollback target         824b5d742dab07b8b0bd301d56748779e35076aa (default
                        tip TRƯỚC merge này) — `git revert -m 1 ab5e07d`
                        trên default nếu cần lùi; KHÔNG force-push, KHÔNG
                        reset --hard nhánh mặc định
```

### `TRẠNG THÁI CUỐI: MERGED_DEPLOY_NOT_VERIFIED`

Merge và mọi gate mã nguồn đã đạt. Render KHÔNG xác nhận được từ phiên này —
không phải vì nghi ngờ nó fail, mà vì phiên không có đường mạng/credential
tới nó. Đây KHÔNG phải `READY_FOR_OWNER_ACCEPTANCE` (chưa xác nhận deploy +
smoke) và KHÔNG phải `INTEGRATION_REPAIR_REQUIRED` (không có lỗi merge/deploy
nào ĐƯỢC PHÁT HIỆN — chỉ là chưa quan sát được).

`CHECK-R4-24` (Owner nghiệm thu R4 trên production) và `CHECK-R3-20` (Owner
nghiệm thu R3 trên production) **VẪN `NOT_TESTED`**. Phiên này KHÔNG tự đánh
dấu Owner Acceptance cho R3 hay R4 — không có thẩm quyền, và không có bằng
chứng trên dữ liệu thật để làm vậy dù có thẩm quyền.

### Điều kiện mở R5

**CHƯA `READY`.** R5 chỉ được ghi `READY` sau khi:

1. Render deploy của `ab5e07d` được Owner (hoặc một phiên có egress/credential
   Render) xác nhận **Live** + log khởi động sạch (§4), **VÀ**
2. Owner tự nghiệm thu R3 (`CHECK-R3-20`) và R4 (`CHECK-R4-24`) trên dữ liệu
   THẬT của production đạt.

Phiên này **không** tạo branch hay code R5 nào — đúng ủy quyền đã nhận.

---

## 7. Checklist Owner — tối đa 6 bước, trên dữ liệu THẬT

1. Mở một kỳ dữ liệu thật, đối chiếu tổng doanh thu/lợi nhuận với file Excel.
2. Kiểm 8 KPI và một nhân viên cụ thể.
3. Đổi các mức biểu đồ và đối chiếu tay vài mốc ngày/tháng.
4. Mở một drill-down đóng góp và kiểm tổng dòng bằng chỉ tiêu nguồn.
5. Kiểm khối chất lượng dữ liệu, Pending và trạng thái kỳ đã chốt/drift.
6. Xác nhận không có lỗi 500, sai ngày UTC+7 hoặc mất quyết định R2/R3 sau
   refresh/restart.

Nếu bất kỳ bước nào KHÔNG đạt: ghi lại chính xác URL, thời điểm (giờ VN), và
ảnh chụp màn hình nếu có, rồi đưa cho phiên sau — đừng tự sửa trên
production.
