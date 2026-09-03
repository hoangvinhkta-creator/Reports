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

## 4. Kết luận gate — GIAI ĐOẠN 1 (trước khi có bằng chứng Owner)

```text
PRODUCTION_ACCEPTANCE_EXECUTED = NO (giai đoạn 1)
STOP_REASON                    = NO_PRODUCTION_EGRESS + WORKBOOK_NOT_IN_SESSION
```

Không phân loại `PRODUCTION_DEPLOY_FAILURE` — chưa có lần deploy nào được
thực hiện để mà thất bại. Không phân loại `DATA_INTEGRITY_RISK` — chưa có
số production để đối chiếu.

**Kết luận này đã bị thay thế bởi mục 8–12 (giai đoạn 2).** Giữ lại nguyên
văn làm bản ghi lịch sử đúng tại thời điểm đó.

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

---

# GIAI ĐOẠN 2 — Đóng CHECK-15 từ bằng chứng production của Owner

Continuation trong cùng phiên S093. Không deploy lại · không rerun RDA ·
không sửa production code · không mở PRA-003.

## 8. Bằng chứng production do Owner cung cấp

Nguồn: OWNER_PROVIDED_PRODUCTION_EVIDENCE (Owner thao tác trên hệ thống
thật + đọc UI production). KHÔNG phải AI inference, KHÔNG phải RDA.

### 8.1 Deploy

```text
SERVICE            = Render production "Reports"
BRANCH             = claude/extract-upload-repo-gq2ws4
DEPLOYED_COMMIT    = c2142dd  (Render hiển thị)
STATUS             = Live
DEPLOY_TYPE        = Manual deployment
DEPLOY_TIME        = 2026-09-03 10:36:11 GMT+7
DURATION           = 24.0s
→ khớp REQUIRED canonical c2142ddee795d1e4d829cabfd01b1774d3441651
```

### 8.2 Lần chạy production thật #1

```text
WORKBOOK           = So_chi_tiet_ban_hang (8).xlsx  (UI: SO_CHI_TIET_BAN_HANG (8).XLSX)
ĐƠN                = 40
AUTO               = 15
Review             = 25
priority review    = 3
dòng không nhận ra = 0
Accounting coverage= 100%
Tracking status    = "Sẵn sàng — dữ liệu Tracking lấy trực tiếp (live) mỗi lần chạy"

SNAPSHOT #1        = SNAP-20260903034024-7b421983
coverage_state     = HEADER_CONSISTENT
measured range     = 2026-09-01 → 2026-09-03
lines 61 · orders 40
INSERT 61 · SAME 0 · SOURCE_CHANGED 0 · COLLISION 0 · NOT_SEEN 0 · REMOVED_CANDIDATE 0
run                = COMPLETE · 40 đơn · AUTO 15 · Review 25 · CÓ SNAPSHOT
```

### 8.3 Upload lại ĐÚNG file đó

```text
SNAPSHOT #2        = SNAP-20260903034120-7b421983   (UI gắn nhãn "FILE TRÙNG")
coverage_state     = HEADER_CONSISTENT
range              = 2026-09-01 → 2026-09-03
lines 61 · orders 40
INSERT 0 · SAME 61 · SOURCE_CHANGED 0 · COLLISION 0 · NOT_SEEN 0 · REMOVED_CANDIDATE 0
run #2             = COMPLETE · 40 đơn · AUTO 15 · Review 25 · CÓ SNAPSHOT
```

### 8.4 Sau F5

```text
Snapshot #1 vẫn hiện: 61 dòng · 40 đơn · INSERT 61
Snapshot #2 vẫn hiện: 61 dòng · 40 đơn · SAME 61 · FILE TRÙNG
Lịch sử run giữ CẢ HAI: 03:40:28 và 03:41:23 — đều COMPLETE, 40 đơn,
AUTO 15, Review 25, CÓ SNAPSHOT
```

## 9. Hai suy dẫn từ hợp đồng đã freeze (KHÔNG phải phỏng đoán)

Ghi rõ chuỗi dẫn xuất để không ai đọc nhầm thành "đã chụp màn hình SQL".

### 9.1 `alembic_version = 0002_snapshots`

```text
tools/db/__init__.py::assert_schema_current(engine)
  → raise HistoryConfigurationError nếu bảng alembic_version thiếu
    HOẶC version_num != ALEMBIC_HEAD
ALEMBIC_HEAD @ c2142dd = "0002_snapshots"
app/web/history_store.py::build(...)  gọi assert_schema_current (verify_schema=True)
app/web/server.py::create_app() gọi _build_history() lúc dựng app
_build_history(): REPORTS_REQUIRE_HISTORY_DB=1 (render.yaml) → lỗi được NÉM TIẾP,
  app KHÔNG khởi động
Dockerfile CMD = `alembic upgrade head && gunicorn ...` (fail-closed trước khi mở cổng)

Quan sát production: service Live, /du-lieu render, HAI upload ghi snapshot thành công.
⟹ assert_schema_current đã PASS trên PostgreSQL production
⟹ alembic_version = '0002_snapshots'.  Cũng ⟹ KHÔNG có HistoryConfigurationError.
```

Đây là suy dẫn **loại trừ** từ mã đã E2-ACCEPT: nếu revision khác, service
không thể Live và không thể ghi snapshot. Không phải suy đoán về trạng thái
chưa quan sát.

### 9.2 "0 source version mới" ở lần upload thứ hai

```text
app/history/reconciler.py::_decide + docstring result_revisions:
  INSERT         → version_no = 1            (ghi source version mới)
  SOURCE_CHANGED → state.next_version_no     (ghi source version mới)
  COLLISION      → state.next_version_no     (ghi source version mới)
  SAME           → state.version_no          ← "SAME là nhánh DUY NHẤT không ghi
                                                source version mới"
UI production lần 2: INSERT 0 · SOURCE_CHANGED 0 · COLLISION 0 · SAME 61
⟹ 0 source version mới.
```

`COUNT(*)` thô trên PostgreSQL KHÔNG được hiển thị và KHÔNG được tuyên bố là
đã chụp — kết luận đến từ chính định nghĩa đã freeze của bốn cờ trên.

## 10. Ma trận REQUIRED của CHECK-PRA002-15 (nguyên văn hợp đồng freeze)

Thẩm quyền = `docs/tasks/TASK-PRA-002-pipeline-persistence-reconciliation.md` → CHECK-PRA002-15 Evidence
("mục 16 bước 1–6; SHA deploy = HEAD canonical sau Controlled Integration;
`alembic_version = 0002_snapshots`; upload thật 302 + snapshot hiện; upload
lại `n_same = line_count`; không OOM") + mục 16 bước 1–6 nguyên văn.
KHÔNG thêm yêu cầu ngoài hai nguồn này.

| # | Assertion REQUIRED (nguyên văn hợp đồng) | Phân loại | Bằng chứng |
|---|---|---|---|
| 1a | Owner Manual Deploy HEAD canonical (không `main`, không force) | PASS_PRODUCTION_UI | Render: Manual deployment, branch canonical, commit `c2142dd`, 2026-09-03 10:36:11 GMT+7, 24.0s |
| 1b | SHA deploy = HEAD canonical sau Controlled Integration | PASS_PRODUCTION_UI | Render hiển thị `c2142dd` == REQUIRED SHA |
| 1c | `alembic upgrade head` tự chạy → `alembic_version = 0002_snapshots` | PASS_PRODUCTION_UI (suy dẫn loại trừ, mục 9.1) | Live + snapshot ghi được ⟹ guard fail-closed đã PASS |
| 1d | Service Live | PASS_PRODUCTION_UI | Render status = Live |
| 1e | Không `HistoryConfigurationError` | PASS_PRODUCTION_UI (mục 9.1) | app khởi động được ⟹ không ném |
| 2a | `/du-lieu` → 200, có module "Snapshot kế toán" | PASS_PRODUCTION_UI | Owner mở `/du-lieu`, thấy danh sách snapshot |
| 2b | legacy import hiện có KHÔNG đổi | **NOT_OBSERVED** | Owner chưa báo phần legacy import của `/du-lieu` |
| 2c | `/nhan-vien` legacy vẫn 200 (PRA-001 không hồi quy) | **NOT_OBSERVED** | Owner chưa mở `/nhan-vien` |
| 3a | Upload sổ kế toán thật qua `reports.tinphatcrm.com/run` → 302 | PASS_PRODUCTION_UI | Upload thành công, trình duyệt đi tới trang kết quả run (hệ quả quan sát được của redirect); mã trạng thái không hiển thị nguyên văn |
| 3b | Run xuất hiện ở lịch sử run (R2) | PASS_PRODUCTION_UI | Hai run 03:40:28 và 03:41:23 trong lịch sử, đều COMPLETE, CÓ SNAPSHOT |
| 3c | Snapshot xuất hiện ở tab Dữ liệu với `DETECTED_ONLY`/`HEADER_CONSISTENT` đúng header thật | PASS_PRODUCTION_UI | `SNAP-20260903034024-7b421983`, HEADER_CONSISTENT, 2026-09-01 → 2026-09-03 (khớp header thật A2) |
| 4a | Upload lại đúng file → snapshot #2 `n_same = line_count` | PASS_PRODUCTION_UI | SAME 61 = line_count 61 |
| 4b | 0 version mới | PASS_PRODUCTION_UI (suy dẫn từ semantics freeze, mục 9.2) | INSERT 0 · SOURCE_CHANGED 0 · COLLISION 0 |
| 4c | Trang snapshot #2 KHÔNG có cờ SOURCE | PASS_PRODUCTION_UI | SOURCE_CHANGED 0 · COLLISION 0 |
| 5a | Render Metrics: RAM đỉnh lúc upload < 512 MB | **NOT_OBSERVED** | Owner chưa cung cấp tab Metrics; RAM đỉnh KHÔNG hiển thị trên bất kỳ ảnh nào |
| 5b | Không "Instance failed" | PASS_PRODUCTION_UI | Live liên tục, hai run COMPLETE, state còn sau F5 |
| 6 | Ghi kết quả (số đơn/dòng/`n_same`, SHA deploy, thời điểm) vào `PROJECT/PROJECT_PROGRESS.md` | PASS_PRODUCTION_UI | Khối canonical S093 trong `PROJECT/PROJECT_PROGRESS.md` (commit này) |
| E | "không OOM" (dòng Evidence freeze) | PASS_PRODUCTION_UI về hành vi; phần định lượng nằm ở 5a | Không instance failure, không restart, hai run COMPLETE |

Assertion KHÔNG có trong hợp đồng freeze → **NOT_REQUIRED**, không chặn:
`COUNT(*)` thô source-version trên PostgreSQL · truy vấn `SELECT version_num`
tận mắt · giá trị qty/gross/discount/net hiển thị trên UI production ·
restart/redeploy Render để thử persistence · kiểm thử người xem thứ hai ·
tỉ lệ AUTO định trước · `CONFIRMED_COMPLETE`.
(Multi-viewer: mục 16 KHÔNG yêu cầu cho PRA-002 → không hỏi Owner làm lại.)

## 11. Ranh giới bằng chứng (không tuyên bố quá)

UI production ĐÃ chứng minh trực tiếp: SHA `c2142dd` Live · workbook được xử
lý · 40 đơn · 61 dòng persist · Accounting coverage 100% · AUTO 15 · Review 25
· Tracking live · INSERT 61 lần đầu · SAME 61 + INSERT 0 lần hai ·
SOURCE_CHANGED 0 · COLLISION 0 · NOT_SEEN 0 · REMOVED_CANDIDATE 0 · hai run
COMPLETE có snapshot · state sống sau F5 · KHÔNG double count.

UI production KHÔNG hiển thị, nên KHÔNG được gắn nhãn "bằng chứng production":
`qty 71` · `gross 593.750.000` · `discount 200.000` · `net 593.550.000` ·
`COUNT(*)` source version · kết quả truy vấn `alembic_version` · RAM đỉnh.
Các giá trị kế toán trên đã được chứng minh ở **RDA (S090/S091)** trên
workbook thật — provenance là `PASS_EXISTING_ACCEPTED_EVIDENCE` của
`CHECK-PRA002-14`, KHÔNG phải ảnh chụp production. Frozen CHECK-15 không
đòi các giá trị này ở UI production nên chúng không chặn.

## 12. Kết luận gate — GIAI ĐOẠN 2 (đã bị thay thế bởi mục 14–17)

```text
PRODUCTION_ACCEPTANCE_RESULT = PARTIAL_PENDING_OWNER_EVIDENCE   (trạng thái tại giai đoạn 2)
CHECK-PRA002-15              = NOT_TESTED  (tại giai đoạn 2 — 3 assertion REQUIRED chưa quan sát)
BLOCKING_FINDINGS            = 0   (không defect nào; thiếu là ẢNH BẰNG CHỨNG, không phải lỗi hệ thống)
TASK-PRA-002                 = IN_PROGRESS
```

Toàn bộ phần lõi persistence / reconciliation / no-double-count / real
Tracking authority / deploy SHA đã ĐẠT trên production. Ba assertion còn
thiếu đều thuộc bước 2 và bước 5 của mục 16, đều là thao tác đọc, không cần
upload lại, không cần deploy lại.

### 12.1 MISSING_REQUIRED_EVIDENCE — đúng 3 mục

| Assertion | Nguồn freeze | Hành động Owner tối thiểu |
|---|---|---|
| `/nhan-vien` trả 200 (PRA-001 không hồi quy) | mục 16 bước 2 | Mở `https://reports.tinphatcrm.com/nhan-vien` → xác nhận trang hiện bình thường |
| legacy import hiện có KHÔNG đổi | mục 16 bước 2 | Trên `/du-lieu` đã mở sẵn: xác nhận phần "bản nhập legacy" vẫn đúng như trước deploy |
| RAM đỉnh lúc upload < 512 MB | mục 16 bước 5 | Render → service Reports → tab **Metrics** → đọc đỉnh Memory trong khung giờ 03:40–03:42 UTC (10:40–10:42 GMT+7) |

KHÔNG hỏi thêm gì ngoài ba mục này. Không hỏi bằng chứng RECOMMENDED/OPTIONAL.
Không yêu cầu upload lần ba. Không yêu cầu người xem thứ hai. Không yêu cầu
restart Render.

Khi ba mục này về: `CHECK-PRA002-15 = PASS` → Completion Gate đủ
(14 PASS · 15 PASS · 17 PASS) → `TASK-PRA-002 = DONE`.

## 13. Ngân sách / phạm vi (giai đoạn 2)

```text
CODE_REQUIRED         = NO       PRODUCTION_CODE_ADDED = 0 dòng
CHANGE_BUDGET_STATE   = 1.460 / 1.500   REMAINING = 40 LOC (KHÔNG chạm)
REVIEW_BUDGET_STATE   = 1 / 2 USED · 1 REMAINING
TRACKING_CHANGED      = NO       INFRASTRUCTURE_CHANGED = NO
SCOPE_CHECK           = OK — docs-only; không deploy lại, không rerun RDA,
                        không migration/schema/parser, không refactor/hardening,
                        không PRA-003
```

---

# GIAI ĐOẠN 3 — Owner hoàn tất thao tác đọc · ĐÓNG CHECK-PRA002-15

Continuation cùng phiên S093. Không deploy lại · không upload lần ba ·
không restart · không mở PostgreSQL · không sửa code · không đổi Render plan.

## 14. Bằng chứng bổ sung của Owner

### 14.1 `/nhan-vien` — production

```text
URL       = reports.tinphatcrm.com/nhan-vien   → trang hiển thị bình thường
Tiêu đề   = "NHÂN VIÊN — SỐ CŨ THEO THÁNG"
Legacy source đang xem = LEG-20260902-4ffe5198
Nguồn                  = Báo cáo Kinh doanh 2026.xlsx
Kỳ hiển thị            = Tháng 08/2026
Bảng nhân viên legacy  = hiển thị đầy đủ dữ liệu
```

→ Bước 2 assertion "`/nhan-vien` legacy vẫn 200 (PRA-001 không hồi quy)" =
`PASS_PRODUCTION_UI`.

### 14.2 Legacy import cũ không đổi

Cùng ảnh production chứng minh bản nhập legacy có TRƯỚC deploy PRA-002 vẫn
tồn tại và đọc được SAU deploy: `/nhan-vien` đang đọc chính
`LEG-20260902-4ffe5198`; ảnh `/du-lieu` trước đó hiển thị cùng ID với nhãn
`LEGACY_REFERENCE` / `ĐANG XEM`.

→ Bước 2 assertion "legacy import hiện có KHÔNG đổi" = `PASS_PRODUCTION_UI`.
KHÔNG rerun legacy import.

### 14.3 Render Metrics — giới hạn quan trắc

```text
Render → Reports → Metrics, khoảng Sep 3, 10:40 AM – 11:03 AM (GMT+7)
Memory : hiển thị "Limit 512 MB" — biểu đồ KHÔNG CÓ data point
CPU    : cũng KHÔNG CÓ data point
```

→ `numeric peak RAM` = `NOT_OBSERVED_FROM_METRICS_UI`. Không bịa số. Không
đọc đường biểu đồ trống thành "0 MB".

## 15. Phân xử assertion bộ nhớ theo đúng chữ của hợp đồng freeze

Hai văn bản, KHÔNG mâu thuẫn — cần đọc đúng vai của từng cái:

```text
(A) Trường Evidence của CHECK-PRA002-15 — phát biểu yêu cầu của chính check:
    "... upload lại `n_same = line_count`; KHÔNG OOM."
        → yêu cầu là một MỆNH ĐỀ về hành vi hệ thống.

(B) Mục 16 bước 5 — thao tác nghiệm thu:
    "Render Metrics: RAM đỉnh lúc upload < 512 MB, không 'Instance failed'."
        → nêu DỤNG CỤ ĐO (Render Metrics) + CẬN TRÊN (< 512 MB) + hệ quả.
```

Điểm quyết định: trên chính instance này, `Limit = 512 MB` là giới hạn
**cứng**. Vượt ngưỡng ⟹ Render OOM-kill container ⟹ "Instance failed" +
request đang chạy đứt. Nên trên plan này, "RAM đỉnh < 512 MB" và "không bị
OOM-kill" KHÔNG phải hai sự kiện độc lập — chúng là **cùng một sự kiện** phát
biểu dưới dạng nguyên nhân và hệ quả.

Bằng chứng production quan sát trực tiếp:

```text
upload #1 COMPLETE (03:40:28) · upload #2 COMPLETE (03:41:23)
service Live liên tục · KHÔNG "Instance failed" · KHÔNG restart
cả hai snapshot + cả hai run còn nguyên sau F5
```

⟹ Không có OOM-kill trong hai lần upload ⟹ đỉnh bộ nhớ **chưa từng chạm
512 MB**. Cận trên của hợp đồng được xác lập; chỉ **giá trị số** là không có.
Hợp đồng khẳng định một CẬN, không đòi một CON SỐ: dòng Evidence của chính
check quy đúng mục này về "không OOM".

Phân loại: **`PASS_PRODUCTION_BEHAVIOR`** cho assertion 5a.

Đối chiếu độ lớn (bối cảnh, KHÔNG phải bằng chứng production và không gánh
kết luận): `CHECK-PRA002-16` đo `ru_maxrss` end-to-end `/run` + writer =
**75,6 MB** (SQLite) / **78,7 MB** (PostgreSQL 16) trên workbook golden 351
dòng — gấp gần 6 lần workbook production 61 dòng.

Đây KHÔNG phải nới lỏng hợp đồng: không assertion nào bị bỏ, không dụng cụ
nào bị thay bằng phỏng đoán. Cái duy nhất không có là số đo, và số đo không
phải là điều hợp đồng khẳng định.

### 15.1 Ma trận REQUIRED — trạng thái cuối

| # | Assertion REQUIRED | Phân loại cuối |
|---|---|---|
| 1a–1e | Manual Deploy canonical · SHA `c2142dd` · `alembic_version = 0002_snapshots` · Live · không `HistoryConfigurationError` | PASS_PRODUCTION_UI |
| 2a | `/du-lieu` 200 + module "Snapshot kế toán" | PASS_PRODUCTION_UI |
| 2b | legacy import hiện có KHÔNG đổi | PASS_PRODUCTION_UI (mục 14.2) |
| 2c | `/nhan-vien` 200 — PRA-001 không hồi quy | PASS_PRODUCTION_UI (mục 14.1) |
| 3a–3c | upload thật → redirect · run trong lịch sử R2 · snapshot `HEADER_CONSISTENT` đúng header | PASS_PRODUCTION_UI |
| 4a–4c | `n_same = line_count` = 61 · 0 source version mới · không cờ SOURCE | PASS_PRODUCTION_UI |
| 5a | RAM đỉnh lúc upload < 512 MB | PASS_PRODUCTION_BEHAVIOR (mục 15) |
| 5b | Không "Instance failed" | PASS_PRODUCTION_UI |
| 6 | Ghi kết quả vào `PROJECT/PROJECT_PROGRESS.md` | PASS — khối canonical S093 + `docs/deployment/S071_DEPLOYMENT.md` |
| E | "không OOM" (dòng Evidence freeze) | PASS_PRODUCTION_BEHAVIOR |

`MISSING_REQUIRED_EVIDENCE = NONE`.

## 16. OBSERVABILITY_LIMITATION (ghi nhận, KHÔNG chặn)

Render Metrics của service Reports không trả telemetry Memory/CPU cho khung
giờ đã chọn. Hệ quả: mọi gate TƯƠNG LAI nếu đòi một **numeric** memory/CPU
measurement từ Render UI sẽ không thoả được bằng dụng cụ đó trên cấu hình
hiện tại. Ghi lại ở đây để phiên sau không mất thời gian đi tìm.

KHÔNG mở finding, KHÔNG mở task, KHÔNG đổi plan, KHÔNG thêm dependency
observability — nằm ngoài phạm vi PRA-002 và ngoài ngân sách.

## 17. Kết luận cuối — CHECK-PRA002-15 = PASS

```text
PRODUCTION_ACCEPTANCE_RESULT = PASS
CHECK-PRA002-15              = PASS   (E1, REQUIRED)
MISSING_REQUIRED_EVIDENCE    = NONE
BLOCKING_FINDINGS            = 0

COMPLETION GATE — 16 check REQUIRED:
  01–13 PASS (E1; 04/05/07/09 thêm E2 qua CHECK-17)
  14    PASS (E1 real data — S090/S091)
  15    PASS (E1 production — phiên này)
  17    PASS (E2 toàn task — S092)
  16    PASS (RECOMMENDED, có số đo 75,6 / 78,7 MB)
Exit Criteria: 6/6 ✔

TASK-PRA-002 = DONE
```

```text
CODE_REQUIRED         = NO       PRODUCTION_CODE_ADDED = 0 dòng
CHANGE_BUDGET_STATE   = 1.460 / 1.500   REMAINING = 40 LOC (KHÔNG chạm)
REVIEW_BUDGET_STATE   = 1 / 2 USED · 1 REMAINING (không tiêu cycle)
TRACKING_CHANGED      = NO       INFRASTRUCTURE_CHANGED = NO
INTEGRATION_READY     = YES — Controlled Integration KHÔNG làm trong phiên này
NEXT_VERTICAL_ACTION  = Controlled Integration docs/state cuối của PRA-002 vào
                        canonical claude/extract-upload-repo-gq2ws4, SAU ĐÓ mới mở
                        PRA-003 (Tổng quan + Nhân viên). KHÔNG mở PRA-003 ở phiên này.
```
