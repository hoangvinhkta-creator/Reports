# S071 Deployment Gate — Triển khai Reports Web Shared Online Beta

Trạng thái: **HOSTING ĐÃ CHỌN, DEPLOYMENT CHƯA THỰC HIỆN.** Session S071
không public/deploy được trực tiếp — lý do chính xác ở mục "Vì sao session
không tự deploy được" bên dưới (KHÔNG phải "chưa quyết định được", mà là một
giới hạn mạng/tài khoản cụ thể, có thể verify).

## So sánh kiến trúc hosting (3 lựa chọn thực tế)

Tiêu chí: Python/Docker, persistent volume, custom domain, env secrets,
HTTPS, đơn giản vận hành, chi phí hợp Beta nội bộ, deploy từ GitHub thuận
tiện, không phụ thuộc Owner Mac, tương thích Cloudflare DNS/Access.

| | **Render** (Web Service, Docker + Disk) | Fly.io (Machines + Volume) | VPS thô (Hetzner/DO + Docker tay) |
|---|---|---|---|
| Persistent volume | Disk gắn kèm service, 1 disk/service | Volume gắn kèm machine | Ổ đĩa VPS — luôn "persistent" nhưng Owner tự quản lý |
| Deploy từ GitHub | **Có sẵn, tự động khi push** (blueprint `render.yaml`) | Có (CLI `flyctl deploy` hoặc GitHub Action) | Không có — Owner tự SSH + `docker compose up` |
| Vận hành hàng ngày | Dashboard, không cần CLI | CLI (`flyctl`) là luồng chính | Owner tự lo update OS, TLS renew (trừ khi tự dựng Caddy/Traefik), firewall |
| Custom domain + HTTPS | Managed cert tự động | Managed cert tự động | Owner tự cài Let's Encrypt/reverse proxy |
| Chi phí ước tính | ~US$7–10/tháng (Starter + 1GB Disk) | ~US$2–5/tháng (machine nhỏ + volume) | ~US$4–6/tháng compute, cộng thời gian vận hành |
| Rủi ro vận hành cho Owner không chuyên | Thấp nhất — bấm dashboard | Trung bình — cần quen CLI | Cao nhất — tự chịu trách nhiệm bảo trì server |

**SELECTED_HOSTING = Render** (Web Service, runtime Docker, plan Starter +
1 Disk).

**REASON**: Render là lựa chọn duy nhất trong ba vừa có persistent disk vừa
có luồng "kết nối GitHub repo → tự deploy khi push" hoàn toàn qua dashboard,
không đòi Owner cài/học một CLI mới. Rẻ hơn (Fly.io) đổi lấy việc Owner phải
tự chạy lệnh `flyctl` là một đánh đổi KHÔNG đáng cho một internal Beta có
lưu lượng thấp — chênh lệch chi phí (~$5/tháng) không đủ lớn để bỏ qua tiêu
chí "operational simplicity" mà brief xếp ngang hàng chi phí. VPS thô bị
loại tường minh theo yêu cầu brief ("Không mặc định VPS") và vì nó chuyển
toàn bộ gánh nặng vận hành (bảo mật OS, TLS, restart khi crash) sang Owner —
đúng loại việc governance dự án này cố tránh cho một người không chuyên kỹ
thuật.

**REJECTED_OPTIONS**: Fly.io (rẻ hơn nhưng CLI-first, không đúng "không yêu
cầu Owner tự vận hành"), VPS thô (bị brief loại tường minh + gánh vận hành
cao nhất), Postgres/Redis/Kubernetes/Firebase/Cloudflare Worker rewrite —
loại tường minh từ khi chọn kiến trúc tổng thể ở phiên trước
(`docs/sessions/S071-shared-online-beta.md` §3), không đánh giá lại ở đây.

## Kiến trúc triển khai cụ thể

```
Cloudflare (DNS + Access, trước reports.tinphatcrm.com)
        ↓
Render Web Service (container từ Dockerfile, gunicorn)
        ↓
Render Disk (1 GB) mount tại /app/persistent
   ├── data/web_runs/runs.db        (registry SQLite — app.web.run_registry)
   ├── data/uploads/                (workbook tạm — xoá ngay sau mỗi lần chạy)
   ├── data/tracking_live_tmp/      (capture Tracking tạm — xoá ngay sau mỗi lần chạy)
   └── outputs/reports/*.xlsx       (artifact — KHÔNG xoá, sản phẩm cuối)
```

Registry + artifact BẮT BUỘC cùng một Disk vì Render chỉ cho gắn đúng một
persistent disk mỗi service — giải quyết bằng biến môi trường
`REPORTS_DATA_ROOT=/app/persistent` (mới thêm ở session này,
`app/web/server.py` + `app/web/run_registry.py`): khi đặt biến này, cả
registry lẫn artifact/upload/tracking-tạm tự trỏ vào cùng gốc mount đó. Khi
KHÔNG đặt (mọi test, mọi môi trường dev/local trước đây), hành vi cũ
(đường tương đối `REPO_ROOT`) giữ nguyên tuyệt đối — verify bằng
`tests/test_web_data_root.py`, 2/2 PASS.

`render.yaml` (root repo) là blueprint đầy đủ — Render đọc file này khi
Owner chọn "New Blueprint Instance" trỏ vào repo, không cần Owner gõ tay bất
kỳ cấu hình nào ngoài secret Tracking.

## Việc Owner cần làm (OWNER_ACTION_REQUIRED / OWNER_PAYMENT_REQUIRED)

Session S071 KHÔNG tạo được tài khoản hay thanh toán thay Owner — đây luôn
là hành động của chủ tài khoản, bất kể provider nào được chọn. Các bước
chính xác, không cần Owner tự nghiên cứu gì thêm:

1. **Tạo tài khoản Render** (render.com, đăng nhập bằng GitHub) — **cần
   phương thức thanh toán**. Plan cần: **Starter Web Service (~US$7/tháng)
   + 1GB Disk (~US$0.25/tháng)** ≈ **~US$7–10/tháng tổng**. Đây là
   `OWNER_PAYMENT_REQUIRED` — không có gói miễn phí nào của bất kỳ provider
   managed nào hỗ trợ persistent disk thật (đã so sánh cả ba lựa chọn ở
   trên, không riêng Render).
2. Trong Render dashboard: **New → Blueprint**, chọn repo Reports, nhánh
   `claude/s071-shared-online-beta-inydpg` (hoặc nhánh canonical sau khi
   merge). Render tự đọc `render.yaml`.
3. Ở bước review biến môi trường, dán giá trị thật cho
   `TRACKING_REPORT_API_KEY` (secret Tracking Data Contract V1) — KHÔNG bao
   giờ dán vào chat Claude, chỉ dán trực tiếp vào ô này trên Render.
   `TRACKING_REPORT_SOURCE_URL` đã điền sẵn `https://price.tinphatcrm.com`
   trong blueprint.
4. Bấm Deploy. Render build Dockerfile, tạo Disk, cấp domain tạm
   `reports-web-xxxx.onrender.com` — mở thử domain này để xác nhận chạy
   được TRƯỚC khi gắn domain thật.
5. Vào Cloudflare (Owner đã có domain `tinphatcrm.com` ở đó):
   - Thêm **CNAME** `reports` → domain Render vừa cấp (`reports-web-xxxx.
     onrender.com`), **DNS-only** (mây xám) lúc đầu để Render verify + cấp
     TLS cert cho `reports.tinphatcrm.com`.
   - Vào Render → service → Settings → **Custom Domain** → thêm
     `reports.tinphatcrm.com`, làm theo hướng dẫn verify của Render.
   - Sau khi Render báo domain đã verify + cert đã cấp: có thể bật lại mây
     cam (proxied qua Cloudflare) nếu muốn Cloudflare Access ở bước sau.
6. Tạo **Cloudflare Access** application cho `reports.tinphatcrm.com`
   (Cloudflare Zero Trust dashboard → Access → Applications → Add an
   application → Self-hosted): giới hạn theo email công ty/domain của Owner
   và sếp — đây là lớp "không public anonymous" bắt buộc (S071 §13), không
   cần Reports tự xây đăng nhập/mật khẩu.

## Vì sao session không tự deploy được

Hai giới hạn CỤ THỂ, đã verify trực tiếp trong session này, không phải suy
đoán:

1. **Egress mạng của session bị chặn tới các host hosting/DNS provider.**
   `curl https://api.fly.io` từ session này trả về lỗi proxy `403` (chính
   sách egress của tổ chức từ chối kết nối tới host ngoài allowlist nội bộ —
   xem `/root/.ccr/README.md` "403/407 from the proxy" và
   `/root/.ccr/__agentproxy/status` ghi lại đúng sự kiện `connect_rejected`
   cho `api.fly.io:443`). Cùng chính sách áp dụng cho `render.com` — session
   không có đường mạng nào tới các API provisioning của bất kỳ provider
   nào trong bảng so sánh trên. Đây là giới hạn hạ tầng của MÔI TRƯỜNG
   CHẠY SESSION, không phải của kiến trúc đã chọn.
2. **Tạo tài khoản/subscription phải gắn danh tính + thanh toán của Owner.**
   Kể cả nếu mạng không bị chặn, session không có thẩm quyền tạo tài khoản
   hay nhập thẻ thanh toán thay chủ dự án.

Vì hai lý do trên ĐỘC LẬP với nhau (mất một trong hai vẫn đủ để chặn tự
deploy), session tập trung làm mọi việc chuẩn bị được TRỌN VẸN mà không cần
mạng ra ngoài hay tài khoản: chọn kiến trúc, viết code hỗ trợ
(`REPORTS_DATA_ROOT`), viết blueprint (`render.yaml`), viết đúng từng bước
Owner cần bấm. Owner KHÔNG cần tự nghiên cứu kiến trúc — chỉ cần làm đúng
theo 6 bước ở trên.

## Build & chạy container cục bộ (kiểm tra trước khi deploy thật)

```bash
docker build -t reports-web .
docker run --rm -p 8080:8080 \
  -v "$(pwd)/local-persistent:/app/persistent" \
  -e REPORTS_DATA_ROOT=/app/persistent \
  -e TRACKING_REPORT_SOURCE_URL="https://price.tinphatcrm.com" \
  -e TRACKING_REPORT_API_KEY="***" \
  reports-web
```

Không có `TRACKING_REPORT_API_KEY`/`TRACKING_REPORT_SOURCE_URL`: server vẫn
khởi động và phục vụ được — chỉ khác ở chỗ mỗi lần `/run` dùng lại đường
local capture cũ (S068–S070), đúng hành vi fallback đã document ở
`tools/tracking/live_pull.is_configured()`.

## Production acceptance checklist (Owner tick sau khi deploy thật — S071 §8)

- [ ] GATE A — HTTPS hoạt động trên `reports.tinphatcrm.com`.
- [ ] GATE B — Request không qua Cloudflare Access bị chặn; viewer đã xác
      thực (email được phép) vào được.
- [ ] GATE C — Tạo Run A → redeploy service trên Render (hoặc restart) →
      Run A vẫn còn, artifact A vẫn tải được.
- [ ] GATE D — Tạo Run B → `/history` hiện cả A và B.
- [ ] GATE E — Mở `reports.tinphatcrm.com` trên một máy/trình duyệt khác →
      thấy đúng Run A/B mà không cần làm gì thêm.
- [ ] GATE F — Kiểm tra log Render KHÔNG thấy nhánh dùng local capture (xem
      `_readiness_text()` phải hiện "Sẵn sàng — dữ liệu Tracking lấy trực
      tiếp (live)") — xác nhận pull-on-run LIVE đang chạy, không phải local
      capture path.
- [ ] GATE G — Owner upload một workbook thật qua `reports.tinphatcrm.com`,
      xác nhận kết quả hợp lý (không fabricate số liệu trước — xem
      `docs/sessions/S071-shared-online-beta.md` §7 "REAL_COHORT_REMOTE").

Session S071 KHÔNG thể tự tick các mục trên (không có môi trường production
thật) — checklist này để Owner xác nhận sau khi deploy.
