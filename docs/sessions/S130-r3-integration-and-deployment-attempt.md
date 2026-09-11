# S130 — Tích hợp production R3: merge THẬT, deploy platform KHÔNG thực hiện được

Phiên TÍCH HỢP/TRIỂN KHAI (không phải phiên phát triển). Tiếp theo `S129` sau
khi Independent Review kết luận **`ACCEPT_WITH_RECORDED_RISK`** trên exact
HEAD `5952ce8`. File này trả lời "cái gì đã lên git production, cái gì chưa
lên platform thật, và Owner cần bấm gì" — cùng khuôn với `S127` (R1).

---

## 1. Exact HEAD được review, và xác nhận KHÔNG đổi trước khi merge

```text
Remote HEAD nhánh R3 lúc phiên bắt đầu: 5952ce8cc2d8d1e3a3bebc59cd6701a027f9f98c
Exact HEAD Independent Review yêu cầu:  5952ce8cc2d8d1e3a3bebc59cd6701a027f9f98c
                                         → KHỚP, xác nhận bằng
                                           git ls-remote origin refs/heads/claude/r3-import-to-period-close-nakk8e
```

Default branch xác định ĐỘNG từ `origin/HEAD` (không suy đoán tên):
`claude/extract-upload-repo-gq2ws4`, tại `45f0e1b` trước khi merge.

## 2. Lineage — xác nhận trước merge

```text
R2 (45f0e1b) là ancestor của R3 HEAD                    → YES
Default branch vượt trước R3 (commit thiếu)             → KHÔNG (trống)
File đổi thuộc `tracking/` trong diff R3 vs default      → 0 file
Secret/credential pattern trong diff (AKIA/BEGIN KEY/…)  → không tìm thấy
Database/artifact nhị phân (.db/.sqlite/.xlsx/…) trong diff → không có
```

36 file thay đổi (17 mới, 19 sửa), `+6746/-56` — khớp đúng các commit R3 đã
biết (`6897234` … `5952ce8`).

## 3. Pre-merge — bằng chứng tự chạy lại (không nhận báo cáo suông)

```text
$ .venv/bin/python -m pytest -q tests/test_r3_import_binding.py \
    tests/test_r3_line_types.py tests/test_r3_export_and_period_close.py \
    tests/test_r3_web_workflow.py tests/test_r3_golden_reconciliation.py \
    tests/test_r3_ir_repair_fingerprint.py
111 passed in 7.40s

$ .venv/bin/python -m pytest -q tests/
3058 passed, 12 skipped in 130.01s

$ bash scripts/branch_authority_check.sh
HEAD_SHA  : 5952ce8cc2d8d1e3a3bebc59cd6701a027f9f98c
AUTHORITY : BRANCH_WITH_UPSTREAM
RESULT    : AUTHORITY_OK

$ .venv/bin/alembic heads
0009_line_binding_period_close (head)
```

Cả bốn con số khớp CHÍNH XÁC với báo cáo reviewer.

Governance validators: `validate_evidence` (161 REQUIRED PASS),
`validate_project_state`, `validate_structure` (21 required paths),
`validate_task_completion` (14 DONE) — PASS.
`validate_reference_integrity` FAIL với ĐÚNG 3 reference `TASK-REM-T06` đã
biết từ trước (baseline không đổi — xác minh lại bằng cách chạy chính
validator đó trên `45f0e1b`, ra CÙNG 3 lỗi).

### Migration `0009` — round-trip trên SQLite tạm (mô phỏng, không phải production)

```text
upgrade (từ đầu)  → head = 0009_line_binding_period_close
seed 2 "quyết định Owner" giả lập: 1 giá nhập tay + 1 lần chốt kỳ
downgrade 0008    → period_close biến mất, period_close__owner_backup xuất
                    hiện với đúng 1 dòng; line_binding_exception biến mất
                    (dẫn xuất, không cần backup); kpi_purchase_price_override
                    (bảng có từ trước R3) KHÔNG bị đụng
upgrade head      → period_close__owner_backup được dọn, dữ liệu nạp lại
                    NGUYÊN VẸN vào period_close; giá nhập tay vẫn nguyên
```

### Repair deploy 2026-09-08 — revision ID PostgreSQL

Lần Auto-Deploy production tại commit `dd369e5` dừng khi Alembic ghi revision
sau bước DDL, với `psycopg.errors.StringDataRightTruncation: value too long for
type character varying(32)`. Nguyên nhân là ID cũ
`0009_line_binding_and_period_close` dài 34 ký tự, trong khi Alembic mặc định
tạo `alembic_version.version_num` là `VARCHAR(32)` trên PostgreSQL.

Repair đổi ID và tên file thành `0009_line_binding_period_close` (30 ký tự),
cập nhật `ALEMBIC_HEAD` và các phép pin migration; thêm test canh giới hạn 32.
Migration vẫn additive, `down_revision` vẫn là `0008_purchase_price_reason`.
PostgreSQL chạy DDL trong cùng transaction với lần ghi version này, nên deploy
lỗi phải được kiểm bằng `alembic current` trước khi deploy lại; `create_all(...,
checkfirst=True)` cũng an toàn nếu hai bảng đã tồn tại từ một lần chạy dở dang.

## 4. Cập nhật tài liệu canonical (trước merge)

Commit `f576333` (doc-only, xác nhận bằng `git diff --name-only 5952ce8..f576333`
chỉ đổi 4 file `.md`, không một file `.py`/`.html`/`.yaml` nào):

- `docs/tasks/R3-nhap-so-den-chot-ky.md` — thêm §8b "Independent Review — kết
  luận": `ACCEPT_WITH_RECORDED_RISK`, exact HEAD, bảng bằng chứng reviewer đã
  tự chạy lại. `CHECK-R3-19` → `PASS`. `CHECK-R3-20` giữ `NOT_TESTED`.
- `docs/sessions/S129-r3-nhap-so-den-chot-ky.md` — thêm §12 ghi lại kết luận review + bằng chứng
  đối chiếu.
- `PROJECT/PROJECT_PROGRESS.md` — cập nhật khối trạng thái R3, thêm đoạn kết
  luận Independent Review.
- `PROJECT/REVIEW_BUDGET_LEDGER.md` — ghi repair cycle #1 của lineage R3
  (base `8aa6626` → head `5952ce8`, 2 finding, outcome
  `ACCEPT_WITH_RECORDED_RISK`); `1/2` repair cycle còn lại.

## 5. Pull Request và merge — ĐÃ THỰC HIỆN

```text
PR:        #8  claude/r3-import-to-period-close-nakk8e → claude/extract-upload-repo-gq2ws4
Head SHA:  f57633396cad342a2219b4f09195d403264134c8  (5952ce8 + 1 commit doc-only)
Merge:     merge_method=merge (KHÔNG squash — chuỗi commit là bằng chứng mà
           Review Budget Ledger và S129 tham chiếu trực tiếp theo SHA)
Kết quả:   ff1a6d343044d827401afaf9a89fe6f2e6e3be60
Xác nhận:  git fetch origin claude/extract-upload-repo-gq2ws4 (sạch) →
           origin/claude/extract-upload-repo-gq2ws4 = ff1a6d3
           git merge-base --is-ancestor f576333 origin/... → OK
```

### CI đỏ tại thời điểm merge — không phải lỗi của PR này

Check `governance/validate` FAIL trên HEAD PR (và trên `5952ce8`) vì
`validate_reference_integrity.py` báo đúng 3 reference `TASK-REM-T06` chưa
phân giải. Xác minh TRƯỚC khi merge: chạy validator y hệt trên `45f0e1b`
(default branch, commit merge PR #7 của R2) → CÙNG 3 lỗi. Đây là tình trạng
nền đã có từ trước R3, không có bản sửa nào sẵn có trong scope (task
`TASK-REM-T06` đang `READY`, và ngay cả khi triển khai xong cũng không đóng
hết cả 3 reference vì các file quy ước cộng tác ở repository root vẫn chưa tồn tại).
Ghi một bình luận trên PR #8 nêu rõ điều này trước khi merge, theo đúng tiền
lệ đã áp dụng khi PR #7 (R2) merge vào `45f0e1b` với cùng tình trạng.

## 6. Deploy platform thật — KHÔNG THỰC HIỆN ĐƯỢC, kiểm chứng trực tiếp

Đã kiểm tra trực tiếp trong phiên này, không suy đoán — **lặp lại chính xác
giới hạn đã ghi ở `S071` và `S127`**:

```text
which wrangler render firebase        → không lệnh nào cài
wrangler whoami                        → command not found
env | grep -iE "cloudflare|render|firebase|R2_|DATABASE_URL|POSTGRES"
                                        → RỖNG, không biến nào

curl https://reports.tinphatcrm.com/   → curl: (56) CONNECT tunnel failed, response 403
curl https://price.tinphatcrm.com/     → curl: (56) CONNECT tunnel failed, response 403
curl https://api.render.com/           → curl: (56) CONNECT tunnel failed, response 403
curl https://dashboard.render.com/     → curl: (56) CONNECT tunnel failed, response 403
curl https://api.github.com            → HTTP 200   (đối chứng: mạng phiên vẫn hoạt động)

agent-proxy status → recentRelayFailures liệt kê cả 4 domain trên với
"gateway answered 403 to CONNECT (policy denial or upstream failure)"
```

Đây là chặn theo CHÍNH SÁCH TỔ CHỨC ở tầng proxy (403 khi mở CONNECT tunnel),
không phải bốn domain kia đang down — `api.github.com` phản hồi bình thường
cùng lúc. Hướng dẫn vận hành: không retry một denial chính sách kiểu này,
báo cáo thay vì tìm đường vòng.

**Hệ quả cụ thể cho R3, nghiêm trọng hơn R1:** R1 không có migration database
mới nên rủi ro của việc "không tự deploy được" chỉ là chưa xác nhận code mới
chạy. **R3 CÓ migration mới (`0009_line_binding_period_close`)** chạm
schema production thật (Postgres qua `HISTORY_DATABASE_URL`). Sao lưu database
production TRƯỚC migration — yêu cầu bắt buộc của phiên này — đòi hỏi quyền
truy cập trực tiếp vào Render Postgres (dashboard, CLI, hoặc kết nối
`psql`/pg_dump tới connection string thật), và phiên này có ĐÚNG BA thứ đều
không có: không credential, không CLI cài sẵn, không egress mạng tới bất kỳ
endpoint Render nào. **Không có cách nào trong phiên này tự thực hiện, tự xác
nhận, hay thậm chí TỰ QUAN SÁT được bước sao lưu đó.**

### Cơ chế fail-closed đã có sẵn trong Dockerfile — giảm nhẹ MỘT PHẦN, không thay thế backup

```dockerfile
CMD ["sh", "-c", "alembic upgrade head && gunicorn ... app.web.wsgi:application"]
```

Container production LUÔN chạy `alembic upgrade head` trước khi mở cổng
gunicorn; `&&` ngắt mạch nếu migration lỗi — container không khởi động, code
mới không bao giờ phục vụ traffic với schema sai. Điều này đáp ứng đúng yêu
cầu *"nếu migration fail, không đưa code R3 lên"* MỘT CÁCH TỰ ĐỘNG, ở tầng hạ
tầng, không cần phiên này can thiệp.

**Nhưng nó KHÔNG thay thế được yêu cầu sao lưu trước migration.** Migration
`0009` là ADDITIVE thuần (hai bảng mới, không đổi cột nào đã có — xem
`tools/db/migrations/versions/0009_line_binding_period_close.py`) nên rủi
ro dữ liệu của riêng nó là THẤP, nhưng đây vẫn là lần đầu database production
chạy một migration có `CREATE TABLE`/backup-restore logic (`period_close`
thuộc `OWNER_INPUT_TABLES`, dùng cơ chế B04) kể từ R2 — sao lưu trước khi chạy
là kỷ luật vận hành chuẩn, không phải một bước có thể bỏ qua vì migration
"trông an toàn".

### Rủi ro cần Owner xử lý NGAY, không chờ

Nếu Render đã cấu hình **auto-deploy** trên nhánh `claude/extract-upload-repo-gq2ws4`
(chưa xác nhận được — phiên không truy cập được dashboard), thì **việc merge
PR #8 ở bước 5 có thể đã tự kích hoạt một build mới trên Render NGAY LÚC ĐÓ**,
và build đó sẽ tự chạy `alembic upgrade head` chống lại database production
THẬT mà KHÔNG có bước sao lưu thủ công đứng trước nó — vì phiên này không có
cách nào chèn bước sao lưu vào TRƯỚC khi container mới khởi động.

**Owner cần làm ngay, theo thứ tự:**

1. Mở Render dashboard → service `reports-web` → tab **Events**/**Deploys**.
   Kiểm tra có build nào bắt đầu quanh thời điểm merge PR #8
   (`2026-09-08T09:1x:xxZ`, giờ UTC) không.
2. Nếu CÓ build đang chạy hoặc đã hoàn tất: mở **Logs** của chính deploy đó,
   tìm dòng `alembic upgrade head` — xác nhận nó chạy THÀNH CÔNG (không có
   traceback/`FAILED`) trước khi tin tưởng service đang chạy đúng.
3. **Bất kể build đã chạy hay chưa**, mở Render Postgres (`tinphat-reports-db`)
   → tab **Backups** → xác nhận có một bản snapshot GẦN THỜI ĐIỂM MERGE. Nếu
   Render Postgres đã bật automated backups/point-in-time-recovery theo mặc
   định (thường có ở mọi plan trả phí), bản backup gần nhất TRƯỚC lúc merge
   coi như đã đủ làm mốc rollback — không cần thao tác thêm. Nếu KHÔNG chắc
   plan có bật backup tự động, tạo một **Manual Backup** ngay từ dashboard
   trước khi làm bất kỳ điều gì khác.
4. Nếu migration đã chạy thành công (bước 2 xác nhận): tiếp tục sang mục 7
   (Smoke test) — Owner tự thực hiện, phiên này không thể.
5. Nếu migration THẤT BẠI hoặc build lỗi: Render (theo hành vi mặc định) giữ
   nguyên deploy trước đó đang phục vụ traffic — service KHÔNG bị gián đoạn,
   nhưng R3 chưa lên. Xem mục 8 (rollback) — không cần thao tác gì thêm vì
   container mới chưa bao giờ mở cổng phục vụ traffic.

## 7. Smoke test production — KHÔNG chạy được, checklist cho Owner

Không một mục nào dưới đây chạy được từ phiên này (cùng lý do mục 6):

```text
[ ] health endpoint (GET /)
[ ] mở /kinh-doanh (trang báo cáo kinh doanh)
[ ] upload một workbook thử qua /run
[ ] xem kỳ, nhân viên, hàng đợi (bao gồm HAI hàng đợi mới của R3:
    ?loc=gan-dong, ?loc=loai-chua-ro, ?loc=gia-theo-chinh-sach)
[ ] tải Excel (/kinh-doanh/xuat-excel) và mở được file — kiểm cột
    "Giá nhập KPI" duy nhất, ô trống ≠ 0
[ ] chốt một kỳ THỬ (không phải kỳ có dữ liệu thật quan trọng) →
    xác nhận sửa giá của kỳ đó bị từ chối HTTP 409
[ ] mở lại kỳ đó bằng lý do → xác nhận sửa được sau khi mở lại
[ ] restart service (Render → Manual Deploy → "Clear build cache & deploy",
    hoặc đơn giản đợi lần deploy tự nhiên tiếp theo) → xác nhận quyết định
    Owner đã lưu (giá nhập tay, lần chốt kỳ) còn nguyên sau restart
[ ] kiểm Render Logs: không dòng nào có "schema mismatch", HTTP 500 hàng
    loạt, hay traceback từ alembic
```

`CHECK-R3-19` (Independent Review) đã `PASS` — KHÔNG phụ thuộc vào smoke test
này. `CHECK-R3-20` (Owner nghiệm thu trên production) VẪN `NOT_TESTED` và
CHỈ đóng được sau khi Owner tự chạy đủ checklist trên và xác nhận.

## 8. Đường rollback

**Ở tầng GIT (đã merge, có thể hoàn tác nếu cần):**

```text
git revert --no-edit ff1a6d3            # hoàn merge commit, giữ lịch sử
# HOẶC (chỉ nếu Owner xác nhận muốn quay production về trước R3 hoàn toàn):
git push origin 45f0e1b:claude/extract-upload-repo-gq2ws4   # về đúng preflight
```

Phiên này KHÔNG tự thực hiện rollback git, vì merge đã đúng yêu cầu (exact
HEAD đã review, CI đỏ đã xác minh không phải lỗi R3, lineage sạch) — không có
lý do kỹ thuật nào để hoàn tác ở tầng này.

**Ở tầng PLATFORM (Render), nếu migration/deploy thật thất bại:**

```text
Render → service reports-web → Deploys → chọn lại bản deploy TRƯỚC (Render
giữ lịch sử deploy riêng, không cần đi qua git) — KHÔNG cần rollback git.
```

**KHÔNG downgrade migration `0009`** trừ khi thật sự cần: nó thuộc nhóm
`OWNER_INPUT_TABLES` (bảng `period_close` chứa quyết định chốt kỳ của Owner)
và có cơ chế B04 (cất vào `*_owner_backup` trước khi drop, nạp lại khi
upgrade) — đã kiểm round-trip ở mục 3 trên SQLite tạm, nhưng downgrade một
database PRODUCTION thật vẫn là thao tác một chiều về mặt rủi ro vận hành nếu
có sự cố giữa chừng (mất điện, kill process khi đang `DROP TABLE`). Nếu migration
THẤT BẠI hoàn toàn trước khi tạo bảng nào, không có gì để downgrade — container
mới đơn giản không khởi động, deploy cũ vẫn phục vụ. Chỉ downgrade nếu
migration đã CHẠY THÀNH CÔNG và sau đó phát hiện một lỗi khác cần lùi code —
và ngay cả khi đó, ưu tiên "Render Deploys → chọn bản cũ" trước, vì code cũ
đọc schema mới (additive) vẫn hoạt động bình thường (không cột/bảng nào bị
đổi nghĩa).

## 9. Trạng thái cuối phiên

```text
Git production (claude/extract-upload-repo-gq2ws4):  ff1a6d3  (R3 đã merge)
Platform Render:                                       KHÔNG XÁC NHẬN ĐƯỢC
Database production đã backup:                         KHÔNG XÁC NHẬN ĐƯỢC
Migration 0009 đã chạy trên production:                KHÔNG XÁC NHẬN ĐƯỢC
Smoke test production:                                 KHÔNG CHẠY ĐƯỢC

CHECK-R3-19 (Independent Review)     = PASS
CHECK-R3-20 (Owner nghiệm thu)       = NOT_TESTED
R3 Status                            = IMPLEMENTED (KHÔNG chuyển DONE)
```

Không PASS, không FAIL cho phần platform — đơn giản là CHƯA QUAN SÁT ĐƯỢC,
đúng cách `S127` đã ghi cho R1. Việc còn lại là của Owner (mục 6–7), có
checklist đầy đủ, không rút gọn được xuống một bước.
