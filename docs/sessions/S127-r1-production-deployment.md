# S127 — Triển khai production R1: SOURCE LOCK đã duyệt bởi Independent Review

Phiên TRIỂN KHAI (không phải phiên phát triển). Tiếp theo `S126` sau khi
Independent Review kết luận **ACCEPT**. Đây là bàn giao triển khai — mọi câu
hỏi "cái gì đã sửa, tại sao" nằm ở `S126`; file này chỉ trả lời "cái gì đã lên
production, cái gì chưa, và Owner cần bấm gì".

---

## 1. SOURCE LOCK đã duyệt

```text
Tracking   f9caaa036cc6fbc9a021aeea99158ba6fce9d20e
Reports    eafcb08eb56ca89068d4e91e0c0a126dbab906df
           (mã R1 nằm ở 4b6006e362696dc97e0bb48cd04aeb8ae4556188;
            eafcb08 chỉ bổ sung tài liệu, không đổi hành vi)
```

Independent Review: **ACCEPT**. `CHECK-R1-24` = PASS (ghi ở
`docs/tasks/R1-daily-min-theo-ngay-ban.md`, commit `6e2620e` — xem mục 3).

## 2. Preflight — HEAD production TRƯỚC khi đổi (mốc rollback)

```text
Tracking   nhánh main                             598b4b1390cc96e552455ab85e2c48d78198b89c
Reports    nhánh claude/extract-upload-repo-gq2ws4 a4c00501d559bda8ec70d8fe1dc1f8e54b46d592
```

Cả hai xác nhận bằng `git fetch` sạch từ `origin` trước khi đổi bất cứ gì.
SOURCE LOCK là fast-forward THUẦN từ hai mốc trên ở cả hai repo — không có
commit lạ xen giữa, không cần merge/rebase, không có xung đột. Diff của cả hai
đã quét theo mẫu khoá/secret/token thật (`API_KEY=`, `-----BEGIN`, `AKIA…`,
`AIza…`, chuỗi kết nối Postgres có mật khẩu) — không có gì khớp ngoài các
tham chiếu TÊN biến môi trường (`env.REPORT_API_KEY`,
`TRACKING_REPORT_API_KEY`) và giá trị placeholder trong test (`api_key="k"`,
`api_key="secret"` trên domain test `tracking.test`/`tracking.example`).

## 3. Cổng trước deploy — kết quả THẬT, chạy lại ở đúng SOURCE LOCK

```text
Tracking (tại f9caaa0)
  npm test         60 bộ · 2737 đạt · 0 hỏng · 2 bỏ qua   (≥ ngân sách yêu cầu)
  npm run build    "Đã dựng bản phục vụ vào ./dist
                    7 file, xén chú thích 1 file HTML
                    658 KB → 411 KB (bớt 37%)"

Reports (tại eafcb08, trước khi thêm commit CHECK-R1-24)
  python -m pytest -q                     2880 passed, 12 skipped (130.64s)
  nhóm daily-min + smoke liên quan:
    test_daily_min_contract.py
    test_daily_min_vertical.py
    test_daily_min_orchestration.py
    test_daily_min_capture_tool.py
    test_web_daily_min_integration.py
    test_tracking_live_pull.py            176 passed (1.87s)

  tools/smoke/r1_daily_min_smoke.py       19/19 PASS (ảnh chụp sinh lại bằng
                                           kiem/smoke/xuat-thang-min.mjs ở
                                           đúng Tracking f9caaa0)
  tools/smoke/r1_web_upload_smoke.py      13/13 PASS (POST /run thật, HTTP
                                           thật tới máy chủ cục bộ giả lập
                                           Tracking bằng chính mã Tracking)
```

Không regression nào thuộc R1. Không việc "tối ưu lỗi hiếm" nào được mở thêm —
đúng chỉ dẫn: chỉ chặn deploy nếu lỗi làm luồng chính không chạy, ra số tiền
sai khó phát hiện, mất dữ liệu, hoặc phá đường quay lui; không trường hợp nào
trong số đó xuất hiện.

## 4. Merge SOURCE LOCK vào nhánh production — ĐÃ THỰC HIỆN, ĐÃ XÁC NHẬN

Cách làm: fast-forward THUẦN (không rebase, không force-push, không rewrite
history), fetch xác nhận lại từ `origin` NGAY SAU khi push — không tin vào bộ
nhớ cục bộ.

```text
Tracking:  git push origin f9caaa0:main
           → 598b4b1..f9caaa0  main -> main   (GitHub xác nhận)
           git fetch origin main (lần 2, sạch) → origin/main = f9caaa036c…

Reports:   thêm ĐÚNG một commit trên SOURCE LOCK: 6e2620e (mục 5 dưới)
           git push origin 6e2620e:claude/extract-upload-repo-gq2ws4
           → a4c0050..6e2620e  claude/extract-upload-repo-gq2ws4 -> ...
           git fetch origin claude/extract-upload-repo-gq2ws4 (lần 2, sạch)
           → origin/claude/extract-upload-repo-gq2ws4 = 6e2620e3ee…
```

Đây là **toàn bộ phần triển khai mà phiên này có thể tự thực hiện được** —
xem mục 6 để biết vì sao không đi xa hơn.

## 5. Commit tài liệu thêm trên SOURCE LOCK

`6e2620e3eedf7ad7ae4b4b29ddacd21c97ab70dd` — CHỈ sửa
`docs/tasks/R1-daily-min-theo-ngay-ban.md`:
- `CHECK-R1-24`: `NOT_TESTED` → `PASS`, kèm câu trích SOURCE LOCK đã ACCEPT.
- Exit Criteria mục 1 gộp `CHECK-R1-24` vào danh sách PASS; mục 2 (Owner
  nghiệm thu) giữ nguyên `NOT_TESTED`.
- Metadata `Status`: `IMPLEMENTED` → `VERIFYING` — việc còn lại không còn là
  code hay review, chỉ còn bước Owner tự tay xác nhận trên sản phẩm thật.

Không đổi một dòng mã nào. Governance validator chạy lại sau commit này:
`validate_structure`/`validate_project_state`/`validate_evidence`/
`validate_task_completion` PASS; `validate_reference_integrity` FAIL với
ĐÚNG 3 reference `TASK-REM-T06` đã biết từ trước — baseline không đổi.

## 6. Vì sao phiên KHÔNG tự deploy được xa hơn bước 4 — kiểm chứng, không suy đoán

Đã kiểm tra trực tiếp trong phiên này, không suy đoán:

```text
wrangler whoami        → "You are not authenticated. Please run `wrangler login`."
env | grep -i cloudflare / render / firebase   → RỖNG, không biến nào
which render / firebase → không có lệnh nào cài
.github/workflows/*.yml (cả hai repo) → không có bước wrangler deploy /
                                          Render deploy hook nào
```

Đây không phải giới hạn mới của phiên này. `docs/deployment/S071_DEPLOYMENT.md`
đã ghi từ trước: *"Session S071 KHÔNG public/deploy được trực tiếp (chưa có
credential Cloudflare/Render/R2 thật)"* — vẫn đúng nguyên văn ở phiên này.

**Thêm một lớp chặn nữa, mới phát hiện ở phiên này:** egress mạng của phiên bị
chính sách tổ chức chặn thẳng ở tầng proxy đối với cả hai domain production:

```text
curl https://price.tinphatcrm.com/    → curl: (56) CONNECT tunnel failed, response 403
curl https://reports.tinphatcrm.com/  → curl: (56) CONNECT tunnel failed, response 403
curl https://api.github.com           → HTTP 200   (đối chứng: mạng phiên vẫn hoạt động)
```

Đây là chặn theo domain ở tầng chính sách (403 khi mở CONNECT tunnel, không
phải lỗi từ server đích), không phải hai domain kia đang down. Hướng dẫn vận
hành của phiên nói rõ: không được retry một denial chính sách kiểu này, phải
báo cáo thay vì tìm đường vòng — nên **không có bất kỳ smoke check production
nào (mục 7 của yêu cầu triển khai) chạy được trong phiên này**, kể cả những
kiểm tra không cần secret (reachability, mã lỗi 403/404 của endpoint xuất dữ
liệu).

Hệ quả: mọi việc từ đây trở xuống — Cloudflare Worker có build bản mới từ
`main` không, Secret `REPORT_API_KEY`/service binding `PRICE_ENGINE`/
`INV_ENGINE` có tồn tại không, `firebase-database.rules.json` của SOURCE LOCK
đã publish chưa, cron `*/20 * * * *` có đăng ký/chạy không, Render có build
bản mới không, biến môi trường Render có đủ/đúng không, hai domain có phục vụ
đúng bản mới không — **CHƯA CÓ BẰNG CHỨNG nào từ phiên này**, không PASS
không FAIL, đơn giản là chưa quan sát được.

## 7. Đường rollback (ghi lại, chưa cần dùng)

```text
Tracking:  git push origin 598b4b1390cc96e552455ab85e2c48d78198b89c:main
           (Cloudflare sẽ build lại từ commit này nếu git-integration hoạt
           động; dữ liệu min_ngay*/min_ngay_rev đã ghi KHÔNG bị xoá — nhánh
           mới, không đụng nhánh cũ. Có thể vô hiệu riêng hợp đồng bằng cách
           xoá Secret REPORT_API_KEY nếu cần fail-closed ngay lập tức mà chưa
           kịp rollback code.)

Reports:   Render → chọn lại Deploy trước đó trong lịch sử deploy của service
           (KHÔNG cần rollback qua git, Render giữ lịch sử deploy riêng), HOẶC
           git push origin a4c00501d559bda8ec70d8fe1dc1f8e54b46d592:claude/extract-upload-repo-gq2ws4
           R1 KHÔNG có migration database mới (không bảng, không cột đổi) —
           rollback code không cần downgrade schema.
```

## 8. Checklist Owner — ĐÚNG những gì cần làm trên Cloudflare + Firebase + Render

Không có cách nào rút gọn xuống một bước duy nhất: mã đã lên `main`/nhánh
production ở tầng Git, nhưng ba nền tảng (Cloudflare Worker, Firebase Realtime
Database rules, Render) mỗi cái có một mặt cấu hình riêng không đi theo git
push. Danh sách dưới đây là TOÀN BỘ phần còn lại — không hơn.

### 8.1 Cloudflare — Worker `tracking`

1. Mở Cloudflare dashboard → Workers & Pages → `tracking` → tab **Deployments**.
   Xác nhận có một deployment MỚI ứng với commit `f9caaa036c…` (thời điểm gần
   với lúc phiên này chạy). Nếu KHÔNG có deployment mới nào xuất hiện sau vài
   phút: git-integration có thể chưa bật cho nhánh `main`, hoặc build đã lỗi
   — mở tab **Build log** đọc nguyên nhân (khả năng cao nhất: `npm test` hỏng
   trong `npm run build`, nhưng phiên này đã xác nhận `npm test` PASS ở đúng
   commit này nên khó xảy ra).
2. **Settings → Variables and Secrets**: xác nhận Secret **`REPORT_API_KEY`**
   tồn tại (không cần xem giá trị, chỉ cần thấy tên trong danh sách với biểu
   tượng đã mã hoá). Nếu thiếu: bấm **Add** → chọn **Secret** → dán giá trị
   khoá (KHÔNG dán vào chat Claude ở bất kỳ đâu) → Save → Deploy lại.
3. **Settings → Bindings**: xác nhận có Service binding `PRICE_ENGINE` →
   service `price-engine` và `INV_ENGINE` → service `inv-engine`. Nếu một
   trong hai thiếu, `wrangler deploy`/Cloudflare build sẽ tự báo lỗi — build
   log ở bước 1 sẽ nói rõ.
4. **Settings → Triggers → Cron Triggers**: xác nhận có đủ BA lịch:
   `*/10 * * * *`, `0 11 * * *`, `*/20 * * * *`. Lịch thứ ba (20 phút) là
   lịch mới của R1 — nếu thiếu, thêm tay đúng chuỗi đó (không gõ lại, copy từ
   `wrangler.toml` dòng `[triggers] crons = [...]` để không lệch một ký tự).

### 8.2 Firebase Console — publish rules cho 5 nhánh `min_ngay*`

**Đây là bước KHÔNG đi theo git push và KHÔNG đi theo Cloudflare build — phải
làm riêng.** File nguồn: `firebase-database.rules.json` tại
`f9caaa036cc6fbc9a021aeea99158ba6fce9d20e` (repo Tracking).

1. Mở Firebase Console → dự án Tracking → Realtime Database → tab **Rules**.
2. So khớp nội dung hiện tại trên Console với file trong repo ở đúng commit
   trên. Nếu khác — đặc biệt nếu THIẾU một trong năm nhánh
   `min_ngay`, `min_ngay_dau`, `min_ngay_ngay`, `min_ngay_sua`,
   `min_ngay_rev` — dán nguyên nội dung file vào ô Rules rồi bấm **Publish**.
3. Xác nhận cả năm nhánh đều `".write": false` (chỉ service account của
   Worker ghi được) và `".read"` khớp đúng quyền của nhánh giá nhập cũ
   (`purchase_price_history`) — đây là điều `kiem/min-ngay.js` khối 15/13b đã
   kiểm ở tầng mã nguồn, nhưng chỉ Publish trên Console mới làm nó có hiệu
   lực thật.
4. **KHÔNG nới quyền bất kỳ nhánh nào khác** ngoài năm nhánh trên khi Publish
   — nếu Console cho thấy khác biệt ở nhánh khác `min_ngay*`, dừng lại và đối
   chiếu, đừng Publish đè.

### 8.3 Mở app Bảng giá — MỘT lần bấm, cần tài khoản có quyền

`meta.an`/`meta.k` (danh sách nhà cung cấp bị ẩn khỏi MIN + vân tay đối
chiếu) chỉ được đăng lên khi có người có quyền `edit`/`bedit`/`admin` MỞ màn
Bảng giá trên trình duyệt — đây là hành vi đã có từ trước R1, không phải bước
mới, nhưng R1 phụ thuộc vào nó: thiếu `meta.an` thì lượt chụp đầu tiên tự
dừng với bản ngày `SOURCE_UNAVAILABLE` (fail-closed, không phải lỗi).

**Việc Owner cần làm:** mở `https://price.tinphatcrm.com` bằng tài khoản có
quyền, vào tab Bảng giá một lần, đợi trang tải xong rồi có thể đóng lại. Chỉ
cần một lần; sau đó `meta.an` giữ nguyên tới lần danh sách NCC bị ẩn thay đổi.

### 8.4 Xác nhận lượt chụp MIN đầu tiên

Sau khi 8.1–8.3 xong, đợi tới lượt cron `*/20 * * * *` kế tiếp (tối đa 20
phút) hoặc kích hoạt tay theo runbook nội bộ hiện có của Cloudflare (Cron
Triggers → **Trigger manually**, nếu dashboard hỗ trợ cho Worker này).

Xác nhận qua Cloudflare **Logs** (Real-time Logs hoặc Logpush nếu đã cấu
hình) của Worker `tracking`:
- có một lượt gọi `chupMinNgay`/`chuKyMinNgay` chạy xong với `ok: true`;
- nhánh `min_ngay_rev` trên Firebase Console (Realtime Database → Data,
  đường `min_ngay_rev`) kết thúc ở `{"s": "READY", "n": "<một chuỗi>", ...}` —
  **KHÔNG** dừng ở `"s": "WRITING"` (nếu dừng ở đó, lượt chụp đã hỏng giữa
  chừng — đọc log để biết lý do, KHÔNG sửa giá trị này bằng tay để giả lập
  thành công, đúng ràng buộc của R1).

### 8.5 Render — service `reports-web`

1. Render dashboard → `reports-web` → tab **Events**/**Deploys**: xác nhận có
   một deploy MỚI ứng với commit `6e2620e3eedf7ad7ae4b4b29ddacd21c97ab70dd`
   (nếu Render đang theo dõi nhánh `claude/extract-upload-repo-gq2ws4`; nếu
   Render đang theo dõi một nhánh khác, đây là chỗ cần đối chiếu — phiên này
   không có cách xác nhận Render đang theo dõi nhánh nào).
2. **Settings → Environment**: xác nhận đủ và đúng:
   - `TRACKING_REPORT_SOURCE_URL = https://price.tinphatcrm.com`
   - `TRACKING_REPORT_API_KEY` = **CÙNG giá trị** với `REPORT_API_KEY` của
     Cloudflare Worker (mục 8.1 bước 2) — hai bên phải khớp, nhưng không dán
     giá trị vào đâu để so, chỉ cần biết chúng được set từ cùng một lần tạo
     khoá.
   - `REPORTS_REQUIRE_R2 = 1` cùng đủ bốn biến `R2_ACCOUNT_ID`, `R2_BUCKET`,
     `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY` — giữ nguyên giá trị hiện có,
     không đổi.
   - `REPORTS_REQUIRE_HISTORY_DB = 1`, `HISTORY_DATABASE_URL` với tiền tố
     ĐÚNG `postgresql+psycopg://` (không phải `postgres://` hay
     `postgresql://` trần — xem `docs/deployment/S071_DEPLOYMENT.md` mục
     10, đây là lỗi đã xảy ra thật và có bảng đối chiếu bốn biến thể).
3. Mở `https://reports.tinphatcrm.com/` (qua Cloudflare Access nếu đã bật) —
   xác nhận trang tải được, KHÔNG rơi về thông báo lỗi cấu hình R2/History DB
   (những lỗi đó fail-closed ngay lúc khởi động container — nếu service
   không "Live" trên Render dashboard, đọc log khởi động ở đó trước).

### 8.6 Smoke production — thực hiện bởi Owner (phiên này KHÔNG chạy được)

Sau khi 8.1–8.5 đều xanh:

1. Trong Firebase Console → Realtime Database → Data, mở `min_ngay_ngay` →
   tìm một ngày ĐÃ có bản ghi (từ lượt chụp ở mục 8.4) → ghi lại ngày đó.
2. Chuẩn bị (hoặc dùng lại) một workbook `.xlsx` nhỏ có ít nhất một dòng bán
   với NGÀY BÁN đúng bằng ngày ở bước 1, mã hàng trùng một mã có trong bảng
   giá Tracking.
3. Mở `https://reports.tinphatcrm.com/du-lieu` → upload workbook đó → bấm
   Chạy báo cáo.
4. Kỳ vọng: hoàn tất, KHÔNG trả lỗi 503/400 từ Tracking; mở artifact `.xlsx`
   ra, cột "Giá nhập kế toán / công khai" của dòng đó CÓ số (không rỗng),
   cột "Nguồn giá" = `TRACKING_DAILY_MIN`.
5. Nếu có một dòng với mã hết hàng/thiếu dữ liệu: cột giá phải RỖNG (không
   phải số `0`), trạng thái Pending có lý do — không phải một hàng "biến
   mất" khỏi báo cáo.
6. Nếu có một mã mà ô Tồn Tín Phát rẻ hơn mọi nhà cung cấp: nguồn phải là
   `INVENTORY:TON_KHO`, không phải tên một nhà cung cấp.
7. **Không dùng dữ liệu TRƯỚC lượt chụp đầu tiên (mục 8.4) để kết luận R1
   sai** — R1 không backfill theo thiết kế (`ADR-110` mục "Không backfill").
   Những ngày trước mốc đó phải Pending, không phải fallback sang giá hiện
   tại hay `tp/ton` cũ; đó là hành vi ĐÚNG, không phải một lỗi cần báo lại.

## 9. Trạng thái R1 sau phiên này

```text
CHECK-R1-24 (Independent Review)     = PASS   (ACCEPT, ghi ở commit 6e2620e)
CHECK-R1-23 (Owner nghiệm thu thật)  = NOT_TESTED — CHƯA, chờ mục 8 ở trên
Status                               = VERIFYING (đổi từ IMPLEMENTED)
R1 DONE                              = CHƯA — không tự tuyên bố
```

`R1` chỉ chuyển `DONE` sau khi Owner tự tay hoàn tất mục 8 và xác nhận mục 8.6
trên sản phẩm thật — không phải bằng bất kỳ bằng chứng nào phiên này tạo ra.
