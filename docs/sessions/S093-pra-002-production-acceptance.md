# S093 — TASK-PRA-002 Production Acceptance (CHECK-PRA002-15)

Mode: PRODUCTION ACCEPTANCE / OWNER-OPERATED REAL SYSTEM.
Docs-only · 0 dòng production code · không migration mới · không sửa Tracking ·
không đổi Render/PostgreSQL/R2/Cloudflare · không mở PRA-003.

## 1. Authority — canonical KHÔNG moved

```text
CANONICAL_BRANCH        = claude/extract-upload-repo-gq2ws4  (HEAD branch thật của origin,
                          xác minh bằng `git remote show origin`)
REQUIRED_SHA            = c2142ddee795d1e4d829cabfd01b1774d3441651
REMOTE_CANONICAL_SHA    = c2142ddee795d1e4d829cabfd01b1774d3441651   → KHỚP CHÍNH XÁC
CANONICAL_MOVED         = NO
SESSION_BRANCH          = claude/pra-002-production-acceptance-8rbm95 (docs-only, không phải
                          production authority)
TRACKING                = READ-ONLY (không gọi, không sửa)
```

Kiểm chứng nội dung SHA deploy (`git log`/`git diff` cục bộ, E1):

```text
d7a1154..c2142dd = 4 commit, TẤT CẢ docs-only:
  1927965  S090 Real Data Acceptance trên workbook thật (docs only)
  f5ea80c  S091 real overlap A -> B trên hai workbook thật (docs only)
  14499dd  S091 closeout: CHECK-PRA002-14 = PASS (docs only)
  c2142dd  S092 Independent Review E2 toàn task = PASS (docs only)

git diff --stat d7a1154 c2142dd -- app/ tools/ alembic.ini render.yaml Dockerfile
  → RỖNG (0 thay đổi production code / hạ tầng)
```

Hệ quả: mã chạy tại `c2142dd` **bằng đúng** cây mã đã được E2 ACCEPT ở S092.
`tools/db/__init__.py::ALEMBIC_HEAD = "0002_snapshots"`.
`Dockerfile` CMD chạy `alembic upgrade head && gunicorn …` → migration lên
schema TRƯỚC khi mở cổng, fail-closed.

## 2. Deploy — KHÔNG thực hiện được từ Claude Cloud (bằng chứng, không suy đoán)

Network policy của environment chặn cả hai host cần thiết:

```text
curl https://reports.tinphatcrm.com/   → curl (56) CONNECT tunnel failed, response 403
curl https://api.render.com/v1/services → curl (56) CONNECT tunnel failed, response 403

$HTTPS_PROXY/__agentproxy/status → recentRelayFailures:
  { kind: "connect_rejected",
    detail: "gateway answered 403 to CONNECT (policy denial or upstream failure)",
    host: "reports.tinphatcrm.com:443" }
  { kind: "connect_rejected",
    detail: "gateway answered 403 to CONNECT (policy denial or upstream failure)",
    host: "api.render.com:443" }
```

Đây là **policy denial cố định**, không phải lỗi mạng tạm thời. Không có
đường vòng hợp lệ; KHÔNG tự chế access, KHÔNG tắt TLS verification, KHÔNG
tạo service/queue/worker mới. Khớp đúng dòng Evidence đã freeze của
`CHECK-PRA002-15`: *"Do Owner thực hiện (session không có egress)."*

## 3. Workbook thật — KHÔNG có trong session

```text
find / -iname "So_chi_tiet_ban_hang*"  → không kết quả
data/samples/                          → rỗng (.gitignore, không commit)
```

Workbook `So_chi_tiet_ban_hang_8.xlsx` (kỳ 2026-09-01 → 2026-09-03) chỉ tồn
tại như attachment trong các phiên S090/S091. KHÔNG sinh file thay thế,
KHÔNG tái dựng, KHÔNG bịa số production.

## 4. Kết luận gate

```text
PRODUCTION_ACCEPTANCE_EXECUTED = NO
CHECK-PRA002-15                = NOT_TESTED  (KHÔNG đổi — không có bằng chứng production)
BLOCKING_FINDINGS              = 0  (không phát hiện defect; đây là chặn ACCESS, không phải defect)
STOP_REASON                    = NO_PRODUCTION_EGRESS + WORKBOOK_NOT_IN_SESSION
TASK-PRA-002                   = IN_PROGRESS
```

Không phân loại `PRODUCTION_DEPLOY_FAILURE` — chưa có lần deploy nào được
thực hiện để mà thất bại. Không phân loại `DATA_INTEGRITY_RISK` — chưa có
số production để đối chiếu.

## 5. Runbook Owner — hành động UI tối thiểu

Ánh xạ 1-1 với mục 16 bước 1–6 của task file. Owner làm đúng ngần này, không
hơn: **không đổi plan, không đổi region, không tạo service/database/bucket,
không sửa Cloudflare, không sửa biến môi trường.**

### Bước 1 — Deploy đúng SHA
Render Dashboard → service Reports (`reports-web`, Virginia) → **Manual Deploy**
→ chọn commit `c2142ddee795d1e4d829cabfd01b1774d3441651` (nhánh
`claude/extract-upload-repo-gq2ws4`) → Deploy.

Ghi lại: **Deploy ID**, **thời điểm**, và **commit SHA mà Render hiển thị**
(đây là bằng chứng SHA deploy — không suy ra từ việc canonical trỏ ở đó).

### Bước 2 — Startup + migration
Trong Logs của deploy đó, chép nguyên văn:
- dòng `alembic` chạy `0001_legacy → 0002_snapshots` (hoặc "already at head"
  nếu 0002 đã có sẵn từ lần trước);
- dòng gunicorn listening;
- xác nhận KHÔNG có `HistoryConfigurationError`, KHÔNG có `Instance failed`.

Service phải Live. Nếu container không lên → **DỪNG**, gửi log, KHÔNG deploy
SHA khác, KHÔNG reset database.

### Bước 3 — Sanity không hồi quy
Mở `https://reports.tinphatcrm.com/du-lieu` → 200, có module "Snapshot kế toán"
(rỗng nếu chưa upload) + legacy import cũ không đổi.
Mở `/nhan-vien` → 200.

### Bước 4 — Upload thật lần 1
Qua `https://reports.tinphatcrm.com/run`, upload đúng file
`So_chi_tiet_ban_hang_8.xlsx` (kỳ 01/09–03/09/2026). **Không sửa file.**
Ghi lại từ trang snapshot: `snapshot_id`, `coverage_state`, `line_count`,
`order_count`, các cờ, AUTO/PENDING, và tổng kế toán.

### Bước 5 — Upload lại đúng file đó
Ghi lại: `n_same`, `n_insert`, `n_source_changed`, `n_collision`, số
source version, tổng current sau lần 2.

### Bước 6 — Metrics + persistence
Render → Metrics: RAM đỉnh lúc upload (< 512 MB), không "Instance failed".
Refresh/mở lại `/du-lieu` → snapshot vẫn còn, tổng không đổi.

## 6. Oracle nghiệm thu (so sánh khi có số production)

```text
line_count      = 61
order_count     = 40
qty             = 71
gross           = 593.750.000
discount        = 200.000
net             = 593.550.000

Upload lại:  n_same = 61 · INSERT = 0 · SOURCE_CHANGED = 0 · COLLISION = 0
             source version KHÔNG tăng · tổng current KHÔNG đổi
             (result version/observation ĐƯỢC PHÉP tăng theo semantics đã freeze;
              RESULT_REVISED > 0 là hợp lệ nếu bằng chứng Tracking thật đổi giữa
              hai lần chạy — KHÔNG ép về 0)

AUTO/PENDING:  KHÔNG có con số bắt buộc. Quan sát thẩm quyền thật.
               PENDING là fail-safe hợp lệ. Không sửa giá để ép AUTO.

coverage:      Chỉ ghi nhận DETECTED_ONLY/HEADER_CONSISTENT theo header thật.
               KHÔNG tự POST xac-nhan-du (mục 14 chỉ thị: no unnecessary mutation).
```

Lệch bất kỳ dòng nào ở khối kế toán → **STOP = DATA_INTEGRITY_RISK**, không tự sửa.

## 7. Ngân sách / phạm vi

```text
CODE_REQUIRED         = NO       PRODUCTION_CODE_ADDED = 0 dòng
CHANGE_BUDGET_STATE   = 1.460 / 1.500   REMAINING = 40 LOC (KHÔNG chạm)
REVIEW_BUDGET_STATE   = 1 / 2 USED · 1 REMAINING (phiên này không tiêu repair cycle)
TRACKING_CHANGED      = NO
SCOPE_CHECK           = OK — docs-only; không feature mới, không refactor,
                        không hardening, không PRA-003
```
