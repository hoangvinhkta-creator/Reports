# S071 Deployment Gate — Triển khai Reports Web Shared Online Beta

Trạng thái: **HOSTING ĐÃ CHỌN (Render), KIẾN TRÚC LƯU TRỮ ĐÃ ĐỔI SANG
STATELESS + R2 (S071B), DEPLOYMENT CHƯA THỰC HIỆN.**

> **SUPERSEDED (2026-09-01, S071B):**
> **OLD** — Render Web Service + MỘT persistent Disk (`REPORTS_DATA_ROOT`
> gộp SQLite + artifact vào cùng một mount, xem "Kiến trúc lịch sử (SUPERSEDED
> — trước S071B)" ở cuối file).
> **SUPERSEDED BỞI** — Reports Python web runtime STATELESS + Cloudflare R2
> (registry run + artifact `.xlsx` lưu trên R2, không còn Disk nào).
> **Lý do**: persistent disk là implementation convenience của S071 (giải
> quyết ràng buộc "1 Disk/service" của Render), không phải một Reports Core
> requirement — registry + artifact chỉ cần put/get theo `run_id`, đúng
> hình dạng object store hơn là filesystem. Chi tiết đầy đủ:
> `docs/sessions/S071-shared-online-beta.md` §12.
>
> Session S071 KHÔNG public/deploy được trực tiếp (chưa có credential
> Cloudflare/Render/R2 thật) — lý do chính xác ở mục "Vì sao session không
> tự deploy được" bên dưới.

## So sánh kiến trúc hosting (3 lựa chọn thực tế — vẫn đúng, không đổi ở S071B)

R2 tách rời khỏi lựa chọn hosting compute — bảng dưới đây so sánh NƠI CHẠY
container Python (không đổi ở S071B), không phải nơi lưu dữ liệu (nay luôn
là R2, không phụ thuộc host nào được chọn).

Tiêu chí: Python/Docker, custom domain, env secrets, HTTPS, đơn giản vận
hành, chi phí hợp Beta nội bộ, deploy từ GitHub thuận tiện, không phụ thuộc
Owner Mac, tương thích Cloudflare DNS/Access.

| | **Render** (Web Service, Docker) | Fly.io (Machines) | VPS thô (Hetzner/DO + Docker tay) |
|---|---|---|---|
| Persistent volume | **Không cần nữa (S071B)** — state nằm ở R2, container stateless | Không cần nữa (S071B) | Không cần nữa (S071B) |
| Deploy từ GitHub | **Có sẵn, tự động khi push** (blueprint `render.yaml`) | Có (CLI `flyctl deploy` hoặc GitHub Action) | Không có — Owner tự SSH + `docker compose up` |
| Vận hành hàng ngày | Dashboard, không cần CLI | CLI (`flyctl`) là luồng chính | Owner tự lo update OS, TLS renew (trừ khi tự dựng Caddy/Traefik), firewall |
| Custom domain + HTTPS | Managed cert tự động | Managed cert tự động | Owner tự cài Let's Encrypt/reverse proxy |
| Chi phí compute ước tính | ~US$7/tháng (Starter, không còn cộng thêm Disk) | ~US$2–5/tháng (machine nhỏ) | ~US$4–6/tháng compute, cộng thời gian vận hành |
| Rủi ro vận hành cho Owner không chuyên | Thấp nhất — bấm dashboard | Trung bình — cần quen CLI | Cao nhất — tự chịu trách nhiệm bảo trì server |

**SELECTED_HOSTING = Render** (Web Service, runtime Docker, plan Starter,
KHÔNG còn Disk). Lý do chọn Render giữ nguyên như quyết định gốc (luồng
"kết nối GitHub → tự deploy" hoàn toàn qua dashboard) — S071B không đổi
lựa chọn hosting, chỉ bỏ được phần "+ Disk" khỏi chi phí/cấu hình.

## Kiến trúc triển khai hiện hành (S071B — Stateless + R2)

```
Cloudflare (DNS + Access, trước reports.tinphatcrm.com)
        ↓
Render Web Service (container từ Dockerfile, gunicorn) — KHÔNG Disk
        ↓ (đọc/ghi qua tools/storage/r2_store.py)
Cloudflare R2 (bucket riêng, không phải Render)
   ├── runs/<run_id>.json        (registry — app.web.storage_backend.R2RunStore)
   └── artifacts/<run_id>.xlsx   (artifact .xlsx — sản phẩm cuối)

Scratch space TẠM trong container (không cần sống qua restart):
   ├── data/uploads/             (workbook tạm — xoá ngay sau mỗi lần chạy)
   ├── data/tracking_live_tmp/   (capture Tracking tạm — xoá ngay sau mỗi lần chạy)
   └── outputs/reports/*.xlsx    (artifact tạm TRƯỚC khi upload lên R2 — xoá ngay sau upload)
```

Container có thể bị Render thay thế/restart bất kỳ lúc nào — không mất run
hay artifact nào, vì không có gì thuộc registry/artifact còn nằm trong
container cả.

`render.yaml` (root repo) là blueprint đầy đủ — Render đọc file này khi
Owner chọn "New Blueprint Instance" trỏ vào repo, không cần Owner gõ tay bất
kỳ cấu hình nào ngoài các secret đánh dấu `sync: false`.

## Việc Owner cần làm (OWNER_ACTION_REQUIRED / OWNER_PAYMENT_REQUIRED)

Session S071B KHÔNG tạo được tài khoản/bucket/token thay Owner — đây luôn
là hành động của chủ tài khoản. Các bước chính xác, không cần Owner tự
nghiên cứu gì thêm:

1. **Tạo tài khoản Render** (render.com, đăng nhập bằng GitHub) — **cần
   phương thức thanh toán**. Plan cần: **Starter Web Service (~US$7/tháng)**
   — KHÔNG còn cần mua Disk. Đây là `OWNER_PAYMENT_REQUIRED` cho phần
   compute (không đổi bản chất so với trước S071B, chỉ giảm số tiền).
2. **Tạo R2 bucket + API token trên Cloudflare dashboard** (R2 → Create
   bucket, đặt tên bất kỳ, vd `reports-web-runs`; R2 → Manage API Tokens →
   Create API Token → quyền Object Read & Write, giới hạn đúng bucket vừa
   tạo). Ghi lại 4 giá trị: **Account ID**, **tên bucket**, **Access Key
   ID**, **Secret Access Key** — KHÔNG dán bất kỳ giá trị nào trong 4 giá
   trị này vào chat Claude hay commit vào repo.
3. Trong Render dashboard: **New → Blueprint**, chọn repo Reports, nhánh
   `s071b/stateless-r2` (hoặc nhánh canonical sau khi merge). Render tự
   đọc `render.yaml`.
4. Ở bước review biến môi trường, dán trực tiếp trên Render (KHÔNG bao giờ
   dán vào chat Claude):
   - `TRACKING_REPORT_API_KEY` (secret Tracking Data Contract V1 — không
     đổi từ S071).
   - `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY` (từ bước 2).
   Sửa lại giá trị mặc định trong `render.yaml` cho `R2_ACCOUNT_ID` và
   `R2_BUCKET` thành đúng giá trị thật từ bước 2 (hai biến này không phải
   secret, nhưng cần đúng bucket của Owner) — có thể sửa trực tiếp trong ô
   review biến môi trường trên Render trước khi bấm Deploy.
5. Bấm Deploy. Render build Dockerfile, cấp domain tạm
   `reports-web-xxxx.onrender.com` — mở thử domain này để xác nhận chạy
   được TRƯỚC khi gắn domain thật. Nếu bất kỳ biến `R2_*` nào thiếu, server
   sẽ FAIL khởi động ngay (không chạy được ở trạng thái nửa vời) — đúng
   thiết kế fail-closed của `REPORTS_REQUIRE_R2=1`.
6. Vào Cloudflare (Owner đã có domain `tinphatcrm.com` ở đó):
   - Thêm **CNAME** `reports` → domain Render vừa cấp (`reports-web-xxxx.
     onrender.com`), **DNS-only** (mây xám) lúc đầu để Render verify + cấp
     TLS cert cho `reports.tinphatcrm.com`.
   - Vào Render → service → Settings → **Custom Domain** → thêm
     `reports.tinphatcrm.com`, làm theo hướng dẫn verify của Render.
   - Sau khi Render báo domain đã verify + cert đã cấp: có thể bật lại mây
     cam (proxied qua Cloudflare) nếu muốn Cloudflare Access ở bước sau.
7. Tạo **Cloudflare Access** application cho `reports.tinphatcrm.com`
   (Cloudflare Zero Trust dashboard → Access → Applications → Add an
   application → Self-hosted): giới hạn theo email công ty/domain của Owner
   và sếp — đây là lớp "không public anonymous" bắt buộc (S071 §13), không
   cần Reports tự xây đăng nhập/mật khẩu.

Nếu service Render cũ từ trước S071B còn Disk gắn kèm: xoá Disk đó sau khi
deploy thành công trên cấu hình mới (Render → service → Disks → Delete) —
không còn cần, tránh trả phí Disk không dùng.

### Bổ sung TASK-PRA-001 — Managed PostgreSQL cho history store (ADR-108)

Từ PRA-001, Reports có thêm một nơi lưu **lịch sử có cấu trúc** (số báo cáo
cũ, sau này là snapshot pipeline). R2 **không** thay được vai trò này: R2 giữ
artifact/run JSON bất biến theo `run_id`, không trả lời được câu hỏi "tháng
03/2026, người bán X, tổng bán bao nhiêu". Đây là hai kho khác nhau, cùng
tồn tại — xem `docs/adr/ADR-108-persistent-history-store.md` (Accepted,
DEC-167).

`OWNER_PAYMENT_REQUIRED` — thêm khoảng **US$6–7/tháng**:

8. **Render → New → PostgreSQL.** Đặt tên tuỳ ý, chọn **cùng region với web
   service**. Đây không phải tối ưu độ trễ mà là điều kiện cần: Render
   **Internal Database URL chỉ định tuyến trong cùng region + cùng
   account** — database khác region với service thì kết nối nội bộ không
   tồn tại và buộc phải mở External URL ra Internet. Plan trả phí nhỏ nhất
   là đủ: dữ liệu ở đây là vài chục nghìn dòng, tiêu chí chọn là **an toàn
   ghi + backup**, không phải hiệu năng.
   *Hiện trạng 2026-09-02:* Owner đã tạo `tinphat-reports-db`
   (PostgreSQL 18, Virginia/US East), cùng region với Reports Web Service.
9. Mở database vừa tạo → copy **Internal Database URL** (dạng
   `postgres://user:pass@host/db`).
10. Vào web service `reports-web` → Settings → Environment. **Tên biến và
    tiền tố URL đều phải đúng — sai một trong hai thì service KHÔNG khởi
    động được** (fail closed, không phải lỗi âm thầm). S078 đã chạy thử cả
    bốn biến thể trên PostgreSQL thật; đây là kết quả đo được, không phải
    suy đoán:

    | Cấu hình                                              | Kết quả |
    |-------------------------------------------------------|---------|
    | Tên biến `DATABASE_URL`                               | `HistoryConfigurationError: REPORTS_REQUIRE_HISTORY_DB=1 nhưng thiếu HISTORY_DATABASE_URL` |
    | `HISTORY_DATABASE_URL=postgres://…` (dán nguyên)      | `NoSuchModuleError: Can't load plugin: sqlalchemy.dialects:postgres` |
    | `HISTORY_DATABASE_URL=postgresql://…`                 | `ModuleNotFoundError: No module named 'psycopg2'` |
    | `HISTORY_DATABASE_URL=postgresql+psycopg://…`         | **OK** |

    Nên: đặt biến tên **`HISTORY_DATABASE_URL`** (KHÔNG phải `DATABASE_URL`
    — tên Render gợi ý sẵn khi liên kết database; `tools/db/__init__.py::
    resolve_url()` không đọc tên đó), dán Internal Database URL vào và
    **đổi tiền tố thành `postgresql+psycopg://`**, giữ nguyên phần còn lại.
    Đây là secret — KHÔNG commit, KHÔNG dán vào chat.

    Nếu trước đó đã lỡ tạo biến `DATABASE_URL`: **đổi tên** biến đó thành
    `HISTORY_DATABASE_URL` (hoặc tạo biến mới rồi xoá biến cũ) — không cần
    tạo lại database, không cần lấy lại credential.
11. Deploy lại **đúng commit canonical**, không phải commit cũ đang chạy.
    Container chạy `alembic upgrade head` TRƯỚC gunicorn: schema được tạo
    tự động, và nếu migration lỗi thì service **không** khởi động. Chạy lại
    `upgrade head` ở mỗi lần deploy là idempotent (đã verify trên
    PostgreSQL thật).
12. Kiểm tra: mở `https://reports.tinphatcrm.com/du-lieu` → nhập workbook
    "Báo cáo Kinh doanh 2026.xlsx" → mở tab **Nhân viên** và **Doanh số
    ngày**, chọn kỳ, thấy số cũ kèm nhãn `LEGACY`.
13. **Sau khi bước 12 xanh** — Render → database `tinphat-reports-db` →
    Settings → *Access Control* / allowed IP list: nếu đang có `0.0.0.0/0`
    thì XOÁ. Reports chỉ dùng Internal URL nên không cần cổng PostgreSQL
    công khai; để `0.0.0.0/0` là phơi database KPI/lương ra toàn Internet,
    chỉ còn mật khẩu chắn. Sau khi xoá, danh sách rỗng = không có inbound
    public nào; kết nối nội bộ trong cùng region KHÔNG đi qua danh sách
    này nên không bị ảnh hưởng. Owner cần `psql` từ máy mình thì thêm đúng
    IP của mình, không mở dải rộng.

### Migration `0002_snapshots` (TASK-PRA-002 — bổ sung ở S080)

Từ SHA mang slice A của `TASK-PRA-002`, `ALEMBIC_HEAD` là **`0002_snapshots`**
(trước đó `0001_legacy`). Deploy vẫn đi đúng đường cũ — `alembic upgrade head`
chạy trong `Dockerfile` CMD trước gunicorn — không có bước thủ công nào thêm.

Điều cần biết khi deploy SHA đó:

- Migration **ADDITIVE thuần**: thêm 6 bảng `PIPELINE_GENERATED`
  (`source_snapshot`, `order_line_source_version`, `snapshot_line`,
  `order_line_result_version`, `order_line_current`, `reconciliation_flag`);
  KHÔNG đổi một cột nào của 4 bảng `legacy_*` và KHÔNG backfill. Đã verify
  trên PostgreSQL 16 local với dữ liệu legacy có sẵn: dòng legacy nguyên vẹn
  sau nâng cấp (`docs/sessions/S080-pra-002-slice-a-implementation.md`).
- Sau deploy, kiểm nhanh:
  `SELECT version_num FROM alembic_version;` → `0002_snapshots`.
- **Rollback không phải chỉ deploy lại SHA cũ.** App fail-closed theo
  revision (`assert_schema_current`), nên một SHA PRA-001 gặp database ở
  `0002_snapshots` sẽ KHÔNG khởi động. Rollback đúng =
  `alembic downgrade 0001_legacy` **rồi** mới deploy SHA cũ. Downgrade XOÁ
  6 bảng đó, tức là mất toàn bộ lịch sử snapshot đã ghi — chấp nhận được
  TRƯỚC Production Acceptance (`CHECK-PRA002-15`), sau đó thì cần Owner
  quyết trước khi downgrade.

Fail-closed đã cấu hình sẵn trong `render.yaml`
(`REPORTS_REQUIRE_HISTORY_DB=1`): thiếu `HISTORY_DATABASE_URL` thì service
KHÔNG khởi động. Đây là cố ý — nếu rơi về SQLite trong container, mỗi lần
redeploy sẽ xoá sạch lịch sử trong khi giao diện vẫn trông như bình thường.

Chạy lại được ở máy Owner (không cần Render):

```
pip install -e ".[web,history]"
alembic upgrade head            # tạo data/history/history.db
python3 -m app.web.launcher
```

Đối chiếu fidelity trên file Excel thật (bằng chứng CHECK-PRA001-01):

```
python3 -m tools.analysis.verify_legacy_import "<đường dẫn>/Báo cáo Kinh doanh 2026.xlsx"
# kỳ vọng: matched=<N> mismatched=0
```

## Vì sao session không tự deploy được

Hai giới hạn CỤ THỂ, đã verify trực tiếp trong session S071 gốc, không đổi
ở S071B:

1. **Egress mạng của session bị chặn tới các host hosting/DNS/Cloudflare
   API provisioning provider.** `curl https://api.fly.io` từ session này
   trả về lỗi proxy `403` (chính sách egress của tổ chức từ chối kết nối
   tới host ngoài allowlist nội bộ — xem `/root/.ccr/README.md` "403/407
   from the proxy"). Cùng chính sách áp dụng cho `render.com` và Cloudflare
   API — session không có đường mạng nào tới các API provisioning của bất
   kỳ provider nào. Đây là giới hạn hạ tầng của MÔI TRƯỜNG CHẠY SESSION,
   không phải của kiến trúc đã chọn.
2. **Tạo tài khoản/bucket/token/subscription phải gắn danh tính + thanh
   toán của Owner.** Kể cả nếu mạng không bị chặn, session không có thẩm
   quyền tạo tài khoản, bucket R2, hay nhập thẻ thanh toán thay chủ dự án.

Vì hai lý do trên ĐỘC LẬP với nhau, session tập trung làm mọi việc chuẩn bị
được TRỌN VẸN mà không cần mạng ra ngoài hay tài khoản: viết code hỗ trợ
(`tools/storage/r2_store.py`, `app/web/storage_backend.py`), viết blueprint
(`render.yaml`), viết đúng từng bước Owner cần bấm, verify toàn bộ logic
bằng test với fake R2 client (không cần credential thật). Owner KHÔNG cần
tự nghiên cứu kiến trúc — chỉ cần làm đúng theo các bước ở trên.

## Build & chạy container cục bộ (kiểm tra trước khi deploy thật)

Với R2 thật (production path):

```bash
docker build -t reports-web .
docker run --rm -p 8080:8080 \
  -e REPORTS_REQUIRE_R2=1 \
  -e R2_ACCOUNT_ID="***" \
  -e R2_BUCKET="reports-web-runs" \
  -e R2_ACCESS_KEY_ID="***" \
  -e R2_SECRET_ACCESS_KEY="***" \
  -e TRACKING_REPORT_SOURCE_URL="https://price.tinphatcrm.com" \
  -e TRACKING_REPORT_API_KEY="***" \
  reports-web
```

Không có `R2_*`/`REPORTS_REQUIRE_R2`: server vẫn khởi động và phục vụ
được ở chế độ local/test — dùng SQLite + file cục bộ trong container
(`LocalRunStore`), KHÔNG sống qua restart container, CHỈ dùng để build-test
cục bộ, không phải đường production. Không có
`TRACKING_REPORT_API_KEY`/`TRACKING_REPORT_SOURCE_URL`: mỗi lần `/run` dùng
lại đường local capture cũ (S068–S070), đúng hành vi fallback đã document ở
`tools/tracking/live_pull.is_configured()` — không đổi ở S071B.

## Production acceptance checklist (Owner tick sau khi deploy thật — S071 §8, cập nhật S071B)

- [ ] GATE A — HTTPS hoạt động trên `reports.tinphatcrm.com`.
- [ ] GATE B — Request không qua Cloudflare Access bị chặn; viewer đã xác
      thực (email được phép) vào được.
- [ ] GATE C — Tạo Run A → redeploy service trên Render (hoặc restart) →
      Run A vẫn còn, artifact A vẫn tải được (S071B: đúng theo thiết kế vì
      không có gì thuộc registry/artifact nằm trong container — verify lại
      một lần trên production thật, không chỉ tin thiết kế).
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
- [ ] GATE H (mới, S071B) — Vào Cloudflare R2 dashboard, xác nhận bucket có
      object `runs/<run_id>.json` và `artifacts/<run_id>.xlsx` đúng cho các
      run đã tạo ở GATE C/D — dữ liệu thật sự nằm trên R2, không phải một
      giả định.

Session S071/S071B KHÔNG thể tự tick các mục trên (không có môi trường
production thật) — checklist này để Owner xác nhận sau khi deploy.

---

## Kiến trúc lịch sử (SUPERSEDED — trước S071B, giữ lại làm bản ghi)

Phần dưới đây mô tả kiến trúc S071 gốc (Render + MỘT persistent Disk,
`REPORTS_DATA_ROOT` gộp SQLite + artifact) — KHÔNG còn là đường production.
Giữ nguyên làm bản ghi lịch sử, không sửa lại để giả như S071 từng chọn R2
ngay từ đầu.

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
`REPORTS_DATA_ROOT=/app/persistent`: khi đặt biến này, cả registry lẫn
artifact/upload/tracking-tạm tự trỏ vào cùng gốc mount đó. Biến này vẫn tồn
tại trong code (`app/web/server.py`, `app/web/run_registry.py`) làm
local-only fallback khi R2 chưa cấu hình — xem "Build & chạy container cục
bộ" ở trên — nhưng KHÔNG còn là đường production kể từ S071B.

`OWNER_PAYMENT_REQUIRED` (lịch sử): **Render Starter (~US$7/tháng) + 1GB
Disk (~US$0.25/tháng) ≈ US$7–10/tháng tổng.** S071B bỏ được phần Disk khỏi
chi phí này.

---

## Bản ghi deploy production — TASK-PRA-002 (2026-09-03, S093)

Lần deploy nghiệm thu `CHECK-PRA002-15`. Ghi lại để lần sau không phải dựng
lại bối cảnh từ đầu.

```text
SERVICE        = Render web service "Reports" (reports.tinphatcrm.com, Virginia)
BRANCH         = claude/extract-upload-repo-gq2ws4 (canonical)
COMMIT         = c2142ddee795d1e4d829cabfd01b1774d3441651  (Render hiển thị "c2142dd")
KIỂU DEPLOY    = Manual Deploy (không đổi plan, không đổi kiến trúc, không tạo
                 service/queue/worker, không đổi PostgreSQL/R2/Cloudflare)
THỜI ĐIỂM      = 2026-09-03 10:36:11 GMT+7
THỜI LƯỢNG     = 24,0 s
TRẠNG THÁI     = Live
```

**Migration.** `Dockerfile` CMD chạy `alembic upgrade head && gunicorn …` nên
schema được nâng TRƯỚC khi mở cổng. Head sau lần này là `0002_snapshots`
(TASK-PRA-002, +6 bảng snapshot/version/current, không đụng 4 bảng
`legacy_*`). Không migration phá huỷ, không reset/drop database, không mất
run/lịch sử cũ.

**Vì sao "service Live" đủ để kết luận `alembic_version = 0002_snapshots`.**
`create_app()` → `_build_history()` → `history_store.build()` →
`tools/db.assert_schema_current()`, hàm này ném `HistoryConfigurationError`
nếu bảng `alembic_version` thiếu HOẶC `version_num != ALEMBIC_HEAD`. Trong
production `REPORTS_REQUIRE_HISTORY_DB=1` nên lỗi được ném tiếp và app KHÔNG
khởi động. App Live và ghi được snapshot ⟹ guard đã PASS. Đây là fail-closed
theo thiết kế, không phải may mắn.

**Kết quả nghiệm thu trên production** (chi tiết:
`docs/sessions/S093-pra-002-production-acceptance.md`):

```text
/du-lieu 200 (module "Snapshot kế toán") · /nhan-vien 200 (legacy PRA-001 không hồi quy,
LEG-20260902-4ffe5198 đọc bình thường)
Upload thật #1 → SNAP-20260903034024-7b421983 · HEADER_CONSISTENT · 2026-09-01 → 2026-09-03
                 61 dòng / 40 đơn · INSERT 61 · run COMPLETE · CÓ SNAPSHOT
Upload lại      → SNAP-20260903034120-7b421983 "FILE TRÙNG" · SAME 61 · INSERT 0 ·
                 SOURCE_CHANGED 0 · COLLISION 0 · 0 source version mới
F5              → cả hai snapshot + cả hai run còn nguyên, 61 dòng / 40 đơn không đổi
Tracking        → live thật · AUTO 15 · Review 25 · 0 dòng không nhận ra · coverage 100%
Bộ nhớ          → không OOM, không "Instance failed", service Live liên tục
```

**Giới hạn quan trắc đã biết (OBSERVABILITY_LIMITATION).** Render Metrics của
service này KHÔNG trả data point Memory/CPU (chỉ hiển thị `Limit 512 MB`).
Gate tương lai nếu cần một CON SỐ bộ nhớ production sẽ không lấy được từ dụng
cụ này — đừng mất thời gian tìm lại. Cận trên `< 512 MB` vẫn suy được từ cơ
chế fail-stop: limit cứng 512 MB, vượt ⟹ OOM-kill ⟹ instance failed; hai
upload hoàn tất và service không bị thay thế ⟹ đỉnh chưa chạm ngưỡng.
