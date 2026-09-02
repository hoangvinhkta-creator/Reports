# S078 — Production PostgreSQL Activation (PRE-PRA-002)

Date: 2026-09-02
Task Mode: MICRO (verification + config/doc repair; không code production mới)
Branch: `claude/postgres-production-activation-grvf50`
Base: `90f85a7edfd6acc497db1d18304baef87ab62d99` (HEAD nhánh canonical
`claude/extract-upload-repo-gq2ws4`)

Mục tiêu: đưa Render PostgreSQL production mà Owner vừa provision vào
Reports có kiểm soát, KHÔNG mở rộng sang `TASK-PRA-002`.

Kết quả **tại thời điểm đóng phiên**: `OWNER_DECISION_REQUIRED` — mọi phần
thuộc thẩm quyền session đã PASS (lineage, compatibility, proof trên
PostgreSQL thật), nhưng ba thao tác cuối nằm hoàn toàn trong Render
dashboard và session không có đường tới đó.

> **CẬP NHẬT 2026-09-02 — Independent Review + Owner Decision + Controlled
> Integration.** Independent Review trên `c5e1994` = **ACCEPT**,
> `BLOCKING_FINDINGS = 0`. Owner chính thức **ACCEPT `DEC-170`**: contract
> canonical là `HISTORY_DATABASE_URL` với scheme `postgresql+psycopg://`,
> **không fallback sang `DATABASE_URL`**; Owner cũng đã cấu hình xong biến
> đó trên Render (session KHÔNG yêu cầu và KHÔNG nhận giá trị). S078 đã
> được Controlled Integration (fast-forward, giữ lịch sử) vào nhánh
> canonical `claude/extract-upload-repo-gq2ws4`.
>
> Nghĩa là: **thao tác 1 dưới đây đã XONG**, `RESULT` hiện hành là `PASS`,
> và SHA cần deploy KHÔNG còn là `90f85a7` mà là HEAD canonical sau
> integration. Trạng thái hiện hành có thẩm quyền nằm ở
> `PROJECT/PROJECT_PROGRESS.md` → "PRODUCTION POSTGRESQL ACTIVATION".
> Phần còn lại của tài liệu này giữ nguyên như **bản ghi đúng tại thời
> điểm của nó** và không bị viết lại.

---

## FACT / INFERENCE / ASSUMPTION — phân tách

### FACT (đo được trong session này)

- Nhánh canonical trên origin: `claude/extract-upload-repo-gq2ws4`
  (`git remote show origin` → HEAD branch). HEAD = `90f85a7`.
- `90f85a7`, `3faedfde` (PRA-001 accepted), `741be69` (PRA-001 closeout) đều
  tồn tại và đều là ancestor của canonical.
- `596564b` = `fix: chặn truy cập trực tiếp *.onrender.com — bắt buộc qua
  Cloudflare Access` (2026-09-01), **là ancestor của canonical**, đứng
  **trước** canonical đúng **10 commit** (`git rev-list --count
  596564b..origin/claude/extract-upload-repo-gq2ws4` = 10).
- Toàn bộ 10 commit đó là công việc `TASK-PRA-001` (S072→S077): `tools/db/**`,
  `app/legacy/**`, `app/web/history_store.py`, template legacy, và khối
  `HISTORY_DATABASE_URL` / `REPORTS_REQUIRE_HISTORY_DB` trong `render.yaml`.
- `git show 596564b:render.yaml` KHÔNG chứa `HISTORY_DATABASE_URL` cũng
  không chứa `REPORTS_REQUIRE_HISTORY_DB`.
- Egress của session bị chính sách chặn: `CONNECT` tới `api.render.com:443`
  và `reports.tinphatcrm.com:443` đều trả `403` từ gateway
  (`$HTTPS_PROXY/__agentproxy/status` → `connect_rejected`, `gateway
  answered 403 to CONNECT`). Session KHÔNG có bất kỳ biến môi trường
  Render/PostgreSQL nào.
- `tools/db/__init__.py::resolve_url()` đọc **`HISTORY_DATABASE_URL`**.
  Không có file nào dưới `app/`, `tools/`, `render.yaml`, `alembic.ini`,
  `Dockerfile` đọc `DATABASE_URL`.
- Migration = **Alembic thật** (`alembic.ini` → `tools/db/migrations`,
  revision head `0001_legacy`). Chạy tự động lúc khởi động container:
  `Dockerfile` CMD = `alembic upgrade head && gunicorn …` — migration lỗi
  thì container không start.
- Driver production = **psycopg 3** (`pyproject.toml` extra `history` →
  `psycopg[binary]>=3.1`); psycopg2 KHÔNG được cài.
- Bốn biến thể cấu hình, đo trên PostgreSQL thật:

  | Cấu hình | Kết quả |
  |---|---|
  | `DATABASE_URL` (+ `REPORTS_REQUIRE_HISTORY_DB=1`) | `HistoryConfigurationError: … thiếu HISTORY_DATABASE_URL` |
  | `HISTORY_DATABASE_URL=postgres://…` | `NoSuchModuleError: Can't load plugin: sqlalchemy.dialects:postgres` |
  | `HISTORY_DATABASE_URL=postgresql://…` | `ModuleNotFoundError: No module named 'psycopg2'` |
  | `HISTORY_DATABASE_URL=postgresql+psycopg://…` | OK |

- PostgreSQL thật dùng để chứng minh: `PostgreSQL 16.13 (Ubuntu
  16.13-0ubuntu0.24.04.1) on x86_64-pc-linux-gnu`, instance local dựng bằng
  `initdb`/`pg_ctl` trong session (chi tiết bằng chứng: `CHECK-PRA001-09`
  trong `docs/tasks/TASK-PRA-001-legacy-reference-vertical.md`).
- `render.yaml` (trước session này) ghi `region: singapore`; Owner cho biết
  Web Service và `tinphat-reports-db` đều ở **Virginia (US East)**.

### INFERENCE (suy ra từ FACT, có căn cứ)

- **Vì sao Render đang deploy `596564b`:** `596564b` là commit CUỐI CÙNG
  trước loạt commit PRA-001. Deployment đó có trước khi PRA-001 hội tụ vào
  canonical, và Render chưa build lại kể từ đó. Đây là *stale*, KHÔNG phải
  *divergent*: `596564b` nằm thẳng trên đường tới `90f85a7`, nên đưa
  production về canonical chỉ là một fast-forward deploy — không rebase,
  không force push, không sửa lịch sử, không dùng `main`.
- **Vì sao service vẫn Live dù tên biến sai:** code đang chạy là `596564b`,
  chưa có history store nào cả — nó không đọc `HISTORY_DATABASE_URL` và
  không có `REPORTS_REQUIRE_HISTORY_DB=1`. Nói cách khác, deploy thành công
  vừa rồi KHÔNG chứng minh gì về PostgreSQL. Ngay khi Owner deploy
  `90f85a7`, `REPORTS_REQUIRE_HISTORY_DB=1` có hiệu lực và **container sẽ
  FAIL khởi động** vì `HISTORY_DATABASE_URL` không tồn tại.
- Đây là fail-closed đúng thiết kế (thà không lên còn hơn lên rồi hiện lịch
  sử rỗng), nhưng vẫn là một deploy hỏng nếu không sửa tên biến trước.

### ASSUMPTION (chưa verify được — phải nói rõ)

- Render Managed PostgreSQL **18** hành xử như **16.13** đối với schema này.
  Schema chỉ dùng cấu trúc nền (TEXT/INTEGER/NUMERIC/BOOLEAN, PK/FK/UNIQUE/
  CHECK, `SERIAL`), không tính năng riêng phiên bản nào — nhưng đây là suy
  luận, chưa đo trên chính instance production.
- Render coi `region` là bất biến sau khi service được tạo, nên sửa
  `render.yaml` thành `virginia` là GHI LẠI hiện trạng chứ không yêu cầu di
  chuyển service. Không verify được (không có egress tới `api.render.com`).
- Không xác minh được service Render hiện có đang liên kết blueprint hay
  không, cũng như đang track branch/ref nào — Render lưu cấu hình đó trong
  dashboard, không trong repo. Repo KHÔNG chứa bằng chứng nào về ref được
  track; mọi khẳng định về nó sẽ là bịa.

---

## Phase A — Deployment lineage: PASS (verify), production stale

```text
canonical branch     = claude/extract-upload-repo-gq2ws4
canonical SHA        = 90f85a7edfd6acc497db1d18304baef87ab62d99
production hiện tại  = 596564b  (ancestor, behind 10 commit)
production sau       = CHƯA THAY ĐỔI — cần Owner deploy
```

Cách đưa production về canonical, KHÔNG force push / KHÔNG sửa lịch sử /
KHÔNG dùng `main`: `596564b` là ancestor thẳng của `90f85a7`, nên Owner chỉ
cần **Render → reports-web → Manual Deploy → chọn commit `90f85a7`** (hoặc
bật Auto-Deploy trên đúng nhánh canonical). Không có thao tác Git nào cần
thiết cả.

**Lineage KHÔNG phải là blocker** — nó đã giải thích được và đường về
canonical là fast-forward. Blocker thật nằm ở Phase B (tên biến).

## Phase B — Database compatibility: PASS về code, FAIL về cấu hình Render

| Hạng mục | Kết quả |
|---|---|
| Đường đọc DATABASE_URL | `tools/db/__init__.py::resolve_url()` ← `HISTORY_DATABASE_URL` (KHÔNG đọc `DATABASE_URL`) |
| ORM / driver | SQLAlchemy 2 Core (không ORM session) + psycopg 3 |
| Migration | Alembic thật, head `0001_legacy`, chạy trong Dockerfile CMD trước gunicorn |
| PostgreSQL dependency | Đã có: `pyproject.toml` extra `history`, kéo qua `web-prod` |
| Schema PRA-001 trên PostgreSQL | Tương thích — verify trên PostgreSQL 16.13 thật |
| SQL/type/pragma riêng SQLite | Không có. `ExactNumeric` render `NUMERIC` trên PG, `TEXT` trên SQLite; JSON lưu TEXT; không SQL viết tay theo dialect |
| Startup tự migration | CÓ — `alembic upgrade head &&` trong CMD, fail closed |
| Failure behavior | Fail closed ở cả 3 kiểu sai (thiếu biến / sai tiền tố / schema chưa migrate) — không kiểu nào biến thành "chưa có dữ liệu" |

**Repair đã thực hiện: KHÔNG có code production nào bị sửa.** Code canonical
đã hỗ trợ PostgreSQL đầy đủ — bằng chứng ở `CHECK-PRA001-09`. Sửa duy nhất
là config/doc (xem "Changed files").

## Phase C — Production activation: KHÔNG THỰC HIỆN ĐƯỢC trong session

Chuỗi proof yêu cầu đã được chứng minh **trên PostgreSQL thật**, nhưng là
instance local, KHÔNG phải production:

```text
PostgreSQL 16.13  →  alembic upgrade head  →  write (214 giá trị, 0 sai)
   →  read  →  pg_ctl stop/start + process Python MỚI  →  read lại
   →  snapshot giống hệt  →  GET /nhan-vien = 200, 66 nhãn LEGACY
```

Phần production thật (deploy `90f85a7`, migrate database `tinphat-reports-db`,
render `/nhan-vien` từ đó) **không thể chạm tới**: egress bị chặn 403 và
session không có credential nào. Đây là giới hạn hạ tầng của môi trường
chạy session, không phải của kiến trúc — cùng lý do đã ghi ở
`docs/deployment/S071_DEPLOYMENT.md` → "Vì sao session không tự deploy được".

## Phase D — Security follow-up

- **Internal connectivity proven = NO** trong production. Chứng minh được
  đến đâu: kiến trúc chỉ cần một chuỗi kết nối (không có đường thứ hai ra
  Internet trong code), và Owner đặt Web Service + database cùng region
  Virginia — điều kiện cần của Render Internal URL. Nhưng "Reports đang
  thực sự dùng Internal URL" chỉ chứng minh được sau khi `90f85a7` chạy
  thật với Internal URL và `/nhan-vien` trả dữ liệu.
- **Public inbound còn cần = KHÔNG (dự kiến).** Reports chỉ nói chuyện với
  database từ bên trong container Render cùng region. Không có test,
  script, hay CI nào trong repo kết nối tới database production từ ngoài.
  Owner có thể cần `psql` từ máy mình cho vận hành thủ công — đó là quyết
  định của Owner, không phải yêu cầu của Reports.
- **Thao tác chính xác** (chỉ làm SAU khi `/nhan-vien` production đã xanh):
  Render → `tinphat-reports-db` → Settings → Access Control / allowed IP
  list → xoá `0.0.0.0/0`. Danh sách rỗng = không còn inbound public.
  Kết nối nội bộ cùng region KHÔNG đi qua danh sách này nên không đứt.
  Cần `psql` từ máy Owner thì thêm đúng IP đó, không mở dải rộng.
  Đã viết thành bước 13 trong `docs/deployment/S071_DEPLOYMENT.md`.
- Session KHÔNG yêu cầu và KHÔNG nhận credential nào. Không có
  `DATABASE_URL`, password, hay connection string nào trong Git, docs, test
  fixture, hay log của session này.

---

## Ba thao tác Owner (theo đúng thứ tự này)

*(Bản ghi tại thời điểm đóng phiên. Xem khối CẬP NHẬT ở đầu tài liệu:
thao tác 1 đã hoàn tất, và SHA ở thao tác 2 đã được thay bằng HEAD canonical
sau Controlled Integration.)*

1. **Đổi tên biến** trong Render → `reports-web` → Settings → Environment:
   `DATABASE_URL` → **`HISTORY_DATABASE_URL`**, và **đổi tiền tố giá trị
   thành `postgresql+psycopg://`**. Không cần tạo lại database, không cần
   lấy lại credential, không dán gì vào chat. (Vì sao không sửa code cho
   nhận `DATABASE_URL`: `DEC-170`.)
2. **Deploy `90f85a7`**: Render → `reports-web` → Manual Deploy → chọn
   commit `90f85a7` trên nhánh `claude/extract-upload-repo-gq2ws4`.
   `alembic upgrade head` sẽ tự chạy trước gunicorn.
3. **Kiểm tra** `https://reports.tinphatcrm.com/du-lieu` → nhập workbook →
   tab **Nhân viên** hiện số cũ kèm nhãn `LEGACY`. Xanh rồi mới làm
   Phase D (xoá `0.0.0.0/0`, bước 13).

Nếu bước 2 làm service không lên: đọc log Render. `HistoryConfigurationError`
= bước 1 chưa xong; `NoSuchModuleError`/`ModuleNotFoundError: psycopg2` =
tiền tố URL sai. Cả hai đều fail-closed, không mất dữ liệu.

## Changed files

```text
render.yaml                                          (config)
docs/deployment/S071_DEPLOYMENT.md                   (doc)
docs/tasks/TASK-PRA-001-legacy-reference-vertical.md (evidence CHECK-PRA001-09)
PROJECT/PROJECT_DECISIONS.md                         (DEC-170)
PROJECT/PROJECT_PROGRESS.md                          (trạng thái)
docs/sessions/S078-postgres-production-activation.md (bản ghi này)
```

Không file nào dưới `app/`, `tools/`, `config/`, `data/`, `tests/` bị sửa.
`PROTECTED_CORE_IMPACT = NONE`. Tracking KHÔNG bị chạm.

## Tests

```text
full suite (SQLite)                       1608 passed, 11 skipped
tests/test_golden_baseline.py               58 passed,  2 skipped
test_legacy_repository + test_web_legacy_routes trên PostgreSQL 16.13 thật
                                            56 passed
R2 / storage / run_registry                 55 passed
Tracking                                   210 passed
history_db + web_server + legacy importer  105 passed
deployment packaging                         5 passed
```

## Chưa được làm (Do Not Change Yet)

- KHÔNG bắt đầu `TASK-PRA-002`, không prebuild schema PRA-002.
- KHÔNG sửa code production để nhận `DATABASE_URL` (xem `DEC-170`).
- KHÔNG import/reprocess dữ liệu thật chỉ để test.
- KHÔNG đụng Tracking, R2, connection pool / HA / autoscaling.

## Session tiếp theo

Sau khi Owner deploy HEAD canonical (xem khối CẬP NHẬT ở đầu tài liệu) và
`/nhan-vien` production xanh:
đóng Phase D (xoá `0.0.0.0/0`), rồi mở
**`TASK-PRA-002` — Persistence + overlapping-upload reconciliation**, bắt
đầu bằng Roadmap Finalization + freeze Completion Gate trước khi code.
