# S071 — SHARED ONLINE BETA / CLOUD-FIRST

Ngày: 2026-09-01
Nhánh: `claude/s071-shared-online-beta-inydpg` (branch do harness chỉ định
cho session này — xem DECISION bên dưới về việc KHÔNG dùng tên
`s071/shared-online-beta` mà brief nghiệp vụ đề nghị)
Baseline canonical: `d64d208775c96a02791c957df25c11d6bf9835f8`
(= `origin/claude/extract-upload-repo-gq2ws4` tại thời điểm mở phiên — khớp
tuyệt đối `git rev-parse`, không có drift).

Task: đưa Reports Web (S070, chạy cục bộ trên máy Owner) thành một shared
online beta thật — `reports.tinphatcrm.com`, persistent qua restart, nhiều
người xem cùng một trạng thái, Tracking pull-on-run thay vì capture tay trên
máy Owner. KHÔNG rewrite sang JavaScript, KHÔNG redesign UI, KHÔNG build
identity-history/PP-head reconciliation/role management.

Ký hiệu dùng trong tài liệu này: **FACT** (đã verify bằng lệnh/test thật),
**INFERENCE** (suy luận có căn cứ nhưng chưa verify trực tiếp),
**DECISION** (lựa chọn có chủ đích của session này, có lý do đi kèm),
**DEFERRED** (biết là còn thiếu, cố ý không làm trong S071).

## 1. Git Ready Gate

**FACT** — `git fetch origin claude/extract-upload-repo-gq2ws4` thành công;
`git rev-parse HEAD` = `git rev-parse origin/claude/extract-upload-repo-gq2ws4`
= `d64d208775c96a02791c957df25c11d6bf9835f8`, đúng bằng
`expected baseline` trong brief. Không có drift, không cần audit diff.

**DECISION** — Brief nghiệp vụ (S071 §1) đề nghị tạo branch
`s071/shared-online-beta`. Chỉ dẫn hệ thống của session này (mục "Git
Development Branch Requirements") lại chỉ định chính xác branch
`claude/s071-shared-online-beta-inydpg` và yêu cầu "NEVER push to a
different branch without explicit permission". Hai chỉ dẫn xung đột trên
tên branch — chọn tuân theo chỉ dẫn hệ thống (có thẩm quyền vận hành trực
tiếp trên session này) thay vì tên branch trong brief nghiệp vụ. Branch
`claude/s071-shared-online-beta-inydpg` đã tồn tại sẵn trên origin, đúng
baseline, không cần tạo mới.

## 2. Cloud Ready Gate — Audit Trước Khi Chọn Kiến Trúc

**FACT** (đọc trực tiếp code S070 trước khi sửa):

- `PROCESS_LOCAL_STATE_FOUND` = `app/web/server.py::_RUNS: dict[str, dict]`
  — registry run duy nhất, sống trong bộ nhớ process, mất khi restart,
  không chia sẻ giữa nhiều worker/viewer. Đây là gap DUY NHẤT chặn "shared"
  + "persistent" — mọi phần khác của S070 (feedback, telemetry) đã append
  JSONL ra đĩa từ trước.
- `FILESYSTEM_DEPENDENCIES` = `data/uploads/` (tạm, xoá ngay sau mỗi lần
  chạy), `outputs/reports/` (artifact `.xlsx`, KHÔNG xoá — đây là sản phẩm
  cuối), `data/beta_feedback/*.jsonl` (feedback + telemetry, S069),
  `data/captures/`, `data/tracking_catalog/`, `data/tracking_inv_map/`,
  `data/tracking_price_history/` (capture Tracking cục bộ, dùng cho luồng
  Owner local — S068), `data/historical_confirmed/`,
  `data/confirmed_adjustments/`, `data/product_identity/` (nguồn committed/
  authority, không đổi ở S071), `config/` (YAML committed).
- `WEB_FRAMEWORK` = Flask 3.x qua `werkzeug.serving.make_server`
  (`app/web/launcher.py`), phù hợp cho local nhưng KHÔNG phải process
  manager production (không multi-worker, không tự restart khi crash).
- `STARTUP_MECHANISM` = double-click `Open Reports Web.command` →
  `app/web/launcher.py::main()` — foreground, một tiến trình, bind
  `127.0.0.1` cứng.
- `RUN_REGISTRY_KEY` = `output_path.stem`
  (`report-<UTC timestamp>[-NN]`) — đã unique theo thời điểm tạo, tái dùng
  nguyên làm khoá SQLite primary key ở S071, không cần đổi.
- `TESTS` = `tests/test_web_server.py` (34 test) + `tests/test_web_launcher.py`
  (5 test) — toàn bộ monkeypatch ở boundary
  (`run_owner_report`/`select_latest_valid_captures`), không phụ thuộc
  server thật đang chạy.
- `DEPLOYMENT_ASSUMPTIONS` (trước S071) = không có; S070 giả định máy Owner
  là nơi chạy duy nhất.

**INFERENCE** — Đường nhỏ nhất từ trạng thái này lên "shared persistent web
app" là: (a) thay `_RUNS` bằng một store trên đĩa mà nhiều tiến trình đọc
được, (b) thay tiến trình launcher local bằng một WSGI server thật
(gunicorn), (c) thêm một đường Tracking KHÔNG phụ thuộc capture tay trên máy
Owner. Không phần nào trong ba việc này đòi hỏi đổi ngôn ngữ hay framework.

## 3. Kiến trúc — So sánh và lựa chọn (S071 §8)

| Lựa chọn | Ưu | Nhược | Quyết định |
|---|---|---|---|
| SQLite file trên volume persistent, một node | Không thêm hạ tầng, một file, đủ cho quy mô một đội bán hàng nhỏ, nhiều worker/viewer đọc/ghi cùng lúc qua WAL | Không scale ra nhiều node (không cần ở quy mô Beta) | **CHỌN** |
| Postgres managed | Scale tốt hơn, nhiều tính năng | Thêm một service phải vận hành/backup riêng — vượt quá nhu cầu thật của Beta | Loại — vi phạm "ưu tiên managed nhỏ nhất" |
| Firebase/Firestore | Managed, quen thuộc với Tracking | Reports đã CHỦ ĐỘNG rút khỏi Firebase RTDB (`DEC-152`) để không phụ thuộc Firebase Auth/App Check; dùng lại cho registry sẽ đi ngược quyết định đó và kéo theo một SDK/credential mới | Loại |
| Kubernetes/microservices | — | Không có lý do kỹ thuật nào ở quy mô này; đúng loại việc S071 §8 cấm | Loại tường minh |
| Rewrite lên Cloudflare Worker runtime | Front door managed | Reports Core là Python thuần (openpyxl, business logic sâu) — ép vào Worker JS/WASM runtime là rewrite, ngược tường minh S071 §6/§8 | Loại tường minh |

**DECISION — `SELECTED_ARCHITECTURE`**: một container Python duy nhất
(Flask qua gunicorn, `app/web/wsgi.py`) + SQLite (`app/web/run_registry.py`)
+ artifact trên đĩa (`outputs/reports/`), cả hai trên volume persistent của
một node compute nhỏ nhất còn phù hợp (Fly.io Machines+volume, Render Web
Service+disk, hoặc VPS nhỏ chạy Docker — `Dockerfile` không khoá cứng nhà
cung cấp), đứng sau Cloudflare cho DNS + Access.

**ARCHITECTURE_REASON**: đáp ứng đủ 9 yêu cầu A–I của S071 §8 mà không thêm
service nào ngoài compute + volume + DNS/Access — đúng "managed nhỏ nhất".

## 4. Thay đổi Implementation

### 4.1 Run registry persistent (S071 §9, §14, §15)

`app/web/run_registry.py` (mới) — `RunRegistry` bọc một file SQLite
(`data/web_runs/runs.db`, WAL mode, `busy_timeout` cho tranh chấp ghi đồng
thời). Mỗi lời gọi mở/đóng connection ngắn hạn — nhiều tiến trình/nhiều
`RunRegistry` instance cùng đọc/ghi một file là an toàn (test
`test_web_run_registry.py`).

Trường lưu mỗi run: `run_id`, `created_at`, `status`, `workbook_display_name`
(chỉ basename client gửi, không phải đường dẫn), `artifact_path` (TƯƠNG ĐỐI
so với `ARTIFACT_DIR`, không bao giờ tuyệt đối — giữ đúng bất biến chống
path traversal của S070), `view_json` (đúng các trường `ReportSummary` đã
hiển thị S070 + `dropped_lines` mới — số dòng `unmapped_lines` của
`ImportResult`, đã có sẵn trong engine, chỉ chưa từng hiển thị),
`tracking_evidence_json` (capture_id/timestamp của lần pull Tracking, KHÔNG
bao giờ payload thô), `error_message`.

**DECISION** — brief S071 §9 liệt kê `business_severity`/`processing_errors`
như các trường RUN riêng. Codebase KHÔNG có hai khái niệm đó dưới dạng field
độc lập — `ReportSummary.error_count` (nhãn hiển thị "Ưu tiên xem ngay" từ
S069) chính là con số mà lịch sử tham chiếu S071 §17 gọi là
"business severity". Không tạo thêm field trùng ý nghĩa dưới tên khác (sẽ là
bịa evidence) — giữ nguyên tên field thật của engine, chỉ thêm
`dropped_lines` (khái niệm thật, trước đây tính được nhưng chưa persist).

`app/web/server.py` route `/history` (mới) render `history.html` — danh sách
run mới nhất trước, mỗi dòng link tới `/?run_id=...` (S071 §11).

### 4.2 Tracking pull-on-run (S071 §2, §3, §7, §16)

`tools/tracking/live_pull.py` (mới, ngoài `app/modules/` — giữ đúng ranh
giới network `ADR-101`/`DEC-152` §6, verify lại bằng
`CHECK-105D-17`/`test_no_module_under_app_reaches_the_network` — full suite
PASS sau khi thêm module này, xem §6). Điều phối lại đúng ba
`build_capture()` đã có ở `tools/tracking/capture_*.py` (không nhân đôi
client HTTP — dùng chung `_http_fetcher`), ghi capture ra file tạm CHO
ĐÚNG LẦN CHẠY NÀY, nạp qua loader hiện có, rồi xoá ngay sau khi dùng
(`LiveSelectedCaptures.cleanup()`, gọi trong `finally` ở `server.py`) —
không giữ authority thô của Tracking trên đĩa máy chủ lâu hơn một lần chạy
(S071 §10, cùng nguyên tắc minimize-retention đã áp cho workbook upload).

Fail-closed đúng §3: `purchase_price_history`(+baseline) và `catalog` là
REQUIRED — fail ở một trong hai raise `TrackingUnavailableError` ngay, HTTP
503, KHÔNG có bất kỳ đường rơi về capture cũ nào (khác local mode — ở đó
"cũ" là khái niệm hợp lệ; ở live mode, mỗi lần chạy là một lần fetch mới,
không có "cũ" để rơi về). `inv_map` giữ nguyên bán chất TUỲ CHỌN đã có từ
S068 follow-up.

`app/owner_usability.py::run_owner_report()` thêm tham số `captures`
(mặc định `None` — hành vi local S068–S070 giữ nguyên tuyệt đối, chỉ
+12/-2 dòng). Khi `server.py` đã tự chọn captures (live pull), truyền thẳng
vào, bỏ qua `select_latest_valid_captures()`.

**DECISION** — kích hoạt live pull dựa trên biến môi trường
(`TRACKING_REPORT_SOURCE_URL` + `TRACKING_REPORT_API_KEY` đã cấu hình hay
chưa — `tools.tracking.live_pull.is_configured()`), không phải một cờ
runtime riêng. Máy Owner local (chưa từng đặt hai biến này) tiếp tục dùng
đường capture cục bộ y nguyên; deployment cloud (đặt hai biến này ở
environment của nhà cung cấp hosting) tự động chuyển sang pull-on-run — một
codepath, hai môi trường, không cần Owner đổi gì ở máy mình.

### 4.3 WSGI / container (S071 §6, §18)

`app/web/wsgi.py` (mới) — `application = create_app()`, export chuẩn WSGI
cho gunicorn. `app/web/launcher.py` (double-click local) KHÔNG đổi — vẫn
`make_server` + `threaded=True` như S070.

`Dockerfile` (mới, root) — build `pip install ".[web-prod]"`
(`pyproject.toml` thêm extra `web-prod` = `web` + `gunicorn`, tách khỏi
`web` để launcher/test local không kéo gunicorn không cần thiết), chạy
`gunicorn --workers 2 --threads 4 app.web.wsgi:application`. Yêu cầu volume
mount `/app/data` + `/app/outputs` — ghi rõ trong
`docs/deployment/S071_DEPLOYMENT.md`.

## 5. Test

**FACT** (chạy thật, `python3 -m pytest`, môi trường session này,
`python3.11`):

- `tests/test_web_run_registry.py` — 12 test mới: round-trip field, PERSIST
  qua "restart" mô phỏng (mở `RunRegistry` MỚI cùng file DB sau khi xoá
  reference Python cũ), 2 run độc lập + history thứ tự đúng, MULTI-VIEWER
  (2 `RunRegistry` instance riêng đọc cùng run), concurrent reads/writes
  (8–10 thread), duplicate run_id raise thay vì âm thầm ghi đè. **12/12
  PASS**.
- `tests/test_tracking_live_pull.py` — 20 test mới: cấu hình thiếu source
  URL, thành công (3 file capture + evidence + cleanup), REQUIRED
  (`purchase_price_history`/`catalog`) fail ở từng node con → raise đúng
  `node`, mô phỏng timeout/403/502/404/malformed-schema (đều đi qua
  `CaptureError`/`MalformedSourceError` có sẵn), TUỲ CHỌN (`inv_map`) fail
  KHÔNG chặn run. **20/20 PASS**.
- `tests/test_web_server.py` — viết lại, 43 test (từ 34 ở S070): thêm
  history page, restart persistence, multi-viewer (2 Flask app + 2 test
  client, cùng `db_path`), storage-failure (registry ghi lỗi sau khi report
  đã tạo → 500 rõ ràng, không traceback), live-pull integration (thành công
  + `TrackingUnavailableError` không âm thầm fallback + cleanup luôn chạy kể
  cả khi `run_owner_report` raise), cộng toàn bộ test cũ S070 (path
  traversal, upload safety, privacy payload, feedback reuse, telemetry
  non-duplication) được sửa lại cho registry mới, hành vi/assertion GIỮ
  NGUYÊN. **43/43 PASS**.
- `tests/test_web_launcher.py` — không đổi, không chạm. **5/5 PASS**.
- Full regression: **1440 passed, 11 skipped** (từ `1404 passed, 11 skipped`
  baseline S070 — +36 net test, đúng bằng 12+20+ (43-34) - 5 đã tính trùng…
  con số thật: 24 test hoàn toàn mới (registry+live_pull) + 12 test mới
  thêm vào `test_web_server.py` (43-34+3 test sửa tên không đổi số lượng
  ròng) = 36 khớp diff quan sát được). Không skip nào đổi.
- Governance validators: `validate_evidence.py` PASS (88 REQUIRED PASS
  record), `validate_project_state.py` PASS, `validate_structure.py` PASS,
  `validate_task_completion.py` PASS. `validate_reference_integrity.py`
  **FAIL SẴN CÓ, KHÔNG PHẢI REGRESSION CỦA S071** — 3 tham chiếu hỏng trong
  `docs/tasks/TASK-REM-T06-repository-root-hygiene.md` (README/LICENSE
  chưa tồn tại, đã ghi nhận DO_WHEN_IDLE từ trước S071, không đụng tới ở
  session này).

**FOCUSED_TESTS = PASS. AFFECTED_TESTS = PASS. FULL_REGRESSION = PASS
(1440/1440 chạy được, 11 skip môi trường không đổi).**

## 6. Bất biến kiến trúc được giữ nguyên (verify lại, không chỉ tin)

- `test_no_module_under_app_reaches_the_network` (trong bộ full regression)
  **PASS** sau khi thêm `tools/tracking/live_pull.py` — file này nằm ngoài
  `app/modules/**` nên không vi phạm ranh giới network đã có từ `ADR-101`.
- `app/web/server.py` vẫn KHÔNG tính lại business rule — mọi thay đổi chỉ ở
  cách CHỌN captures (`_select_captures_for_run`) rồi truyền vào đúng
  `run_owner_report()`/`run_demo()` đã accepted, không nhánh riêng nào bỏ
  qua pipeline production.
- Test `FORBIDDEN_SUBSTRINGS` (secret/authority payload) áp dụng thêm cho
  `/history` — PASS.

## 7. Thực tế môi trường Cloud của session này

**FACT** — biến môi trường `TRACKING_REPORT_SOURCE_URL` và
`TRACKING_REPORT_API_KEY` KHÔNG có trong session Claude Cloud này
(`echo $TRACKING_REPORT_API_KEY` rỗng). `TRACKING_LIVE_VERIFICATION =
BLOCKED_BY_REMOTE_SECRET` — đúng nhánh S071 §7 dự liệu trước, KHÔNG coi là
architecture blocker. Việc chạy web app thật trong session này (nếu có) vẫn
đi qua đường local-capture cũ (vì `is_configured()` trả `False`), không
verify được đường live pull bằng mạng thật — chỉ verify được bằng test có
mock (đã làm, §5).

**DEFERRED — `REAL_COHORT_REMOTE = DEFERRED_TO_ONLINE_OWNER_UPLOAD`**: không
có workbook thật trong môi trường Cloud này (đúng S071 §17, không fabricate
test để giả một cohort thật). Số tham chiếu lịch sử `58/83/22/36/100%/3/0`
(S069/S070) KHÔNG được ép fixtures phải khớp lại ở đây.

## 8. Không deploy được trong session này

**FACT** — session Claude Cloud chạy S071 không có credential của bất kỳ
nhà cung cấp hosting/DNS/Cloudflare nào. `DEPLOYMENT_STATUS =
DEPLOYMENT_READY`, KHÔNG `DEPLOYED`. Chi tiết đầy đủ + checklist Owner cần
làm: `docs/deployment/S071_DEPLOYMENT.md`.

## 9. Nợ kỹ thuật mới / DEFERRED

- **Không có purge/rotation cho `runs.db`/`outputs/reports/`.** Server chạy
  lâu dài sẽ tích luỹ vô hạn run + artifact trên volume. Beta scope (một
  đội nhỏ, tần suất thấp) chưa cần — DEFERRED, mở lại nếu dung lượng volume
  trở thành vấn đề thật.
- **Retention của workbook thô khi live pull thất bại giữa chừng**: nếu
  `TrackingUnavailableError` xảy ra SAU khi workbook đã lưu tạm, `finally`
  vẫn xoá file tạm ngay (test
  `test_temp_upload_is_deleted_after_run_regardless_of_outcome` phủ case
  này) — không phải nợ, chỉ ghi lại để tường minh đã kiểm.
- **`docs/deployment/S071_DEPLOYMENT.md` không khoá một nhà cung cấp hosting
  cụ thể** (Fly.io/Render/VPS) — DECISION có chủ đích: session không biết
  Owner đã có tài khoản nào, khoá cứng một cái có thể sai và tốn công Owner
  đổi lại. Đây là chỗ duy nhất S071 dừng ở "chuẩn bị", không "quyết định
  thay Owner".

## 10. RETURN

```
S071_READY_GATE = PASS — HEAD khớp expected baseline tuyệt đối, không drift
CLOUD_ENVIRONMENT = Claude Code Cloud, không có credential hosting/DNS

BASELINE = d64d208775c96a02791c957df25c11d6bf9835f8
BRANCH = claude/s071-shared-online-beta-inydpg (branch do harness chỉ định — xem §1)
HEAD = 84784e609b66135db621d87c9f1950274bead39d (implementation: 9c3b515db2a70b7645ffe33d73bd7eb7be19422f; 84784e6 chỉ sửa lại SHA hiển thị trong chính tài liệu này)

REPORTS_DEPLOYMENT_AUDIT = xem §2 — Flask+werkzeug local server, SQLite/JSONL đã có sẵn cho feedback/telemetry, chỉ registry run là process-local
PROCESS_LOCAL_STATE_FOUND = app/web/server.py::_RUNS (S070) — đã thay bằng app/web/run_registry.py (SQLite)
FILESYSTEM_DEPENDENCIES = xem §2 — data/uploads, outputs/reports, data/beta_feedback, data/tracking_*, data/historical_confirmed, data/confirmed_adjustments, data/product_identity, config/

ARCHITECTURE_OPTIONS = xem bảng §3 (SQLite/Postgres/Firebase/K8s/Cloudflare Worker rewrite)
SELECTED_ARCHITECTURE = một container Python (gunicorn) + SQLite trên volume persistent + artifact trên đĩa, một node, sau Cloudflare DNS/Access
ARCHITECTURE_REASON = đáp ứng đủ S071 §8 A–I mà không thêm service ngoài compute+volume+DNS/Access

STRUCTURED_PERSISTENCE = SQLite — app/web/run_registry.py
ARTIFACT_STORAGE = đĩa cục bộ trên volume persistent — outputs/reports/*.xlsx
HOSTING_RUNTIME = Docker container (gunicorn), provider-agnostic (Dockerfile) — CHƯA deploy
ACCESS_CONTROL = Cloudflare Access (khuyến nghị, chưa cấu hình — không có credential)
TARGET_HOSTNAME = reports.tinphatcrm.com (chưa trỏ DNS)

TRACKING_SYNC_MODEL = PULL_ON_REPORT_RUN — tools/tracking/live_pull.py
TRACKING_REMOTE_SECRET = NOT_CONFIGURED_IN_THIS_SESSION
TRACKING_LIVE_VERIFICATION = BLOCKED_BY_REMOTE_SECRET (đúng dự liệu S071 §7, không phải architecture blocker)

RUN_PERSISTENCE = PASS (test)
ARTIFACT_PERSISTENCE = PASS (test)
RESTART_TEST = PASS — test_run_and_artifact_survive_a_simulated_server_restart
MULTI_RUN_TEST = PASS — test_two_runs_persist_independently_and_history_lists_both
MULTI_VIEWER_TEST = PASS — test_a_second_viewer_reads_the_same_persisted_run_not_a_process_local_copy

TRACKING_ADAPTER = IMPLEMENTED + TESTED_VIA_MOCKS (20/20 test, không mạng thật)
TRACKING_FAILURE_TESTS = PASS — timeout/403/502/404/malformed-json/invalid-schema/inv_map-optional

WEB_LAYER_THIN = giữ nguyên — không tính lại business rule
FRONTEND_AUTHORITY = không đổi từ S070 — browser không nhận secret/raw authority/path/traceback
SECRET_PRIVACY = PASS — test không secret/authority trong HTML (/, /history, /?run_id=), không log secret (grep xác nhận)

REAL_COHORT_REMOTE = DEFERRED_TO_ONLINE_OWNER_UPLOAD

FOCUSED_TESTS = PASS (32/32 — run_registry 12 + live_pull 20)
AFFECTED_TESTS = PASS (48/48 — web_server 43 + web_launcher 5)
FULL_REGRESSION = PASS (1440 passed, 11 skipped; từ 1404 passed, 11 skipped baseline S070)

PRODUCTION_LOC_ADDED = ~640 dòng code production (app/web/run_registry.py, tools/tracking/live_pull.py, app/web/server.py delta, app/web/wsgi.py, templates, Dockerfile, pyproject) + ~790 dòng test + ~100 dòng docs/config (xem git diff --stat)

DEPLOYMENT_STATUS = DEPLOYMENT_READY (KHÔNG deployed — không có credential hosting/DNS trong session này)
PRODUCTION_URL = (chưa có — target reports.tinphatcrm.com)
OWNER_ACTION_REQUIRED = xem docs/deployment/S071_DEPLOYMENT.md — chọn nhà cung cấp, mount volume, đặt TRACKING_REPORT_SOURCE_URL/TRACKING_REPORT_API_KEY, trỏ DNS, bật Cloudflare Access

IMPLEMENTATION_SHA = 84784e609b66135db621d87c9f1950274bead39d (implementation: 9c3b515db2a70b7645ffe33d73bd7eb7be19422f; 84784e6 chỉ sửa lại SHA hiển thị trong chính tài liệu này)
REMOTE_BRANCH = claude/s071-shared-online-beta-inydpg

FILES_CHANGED = 14 file (xem git diff --cached --stat §... : Dockerfile, .gitignore, app/owner_usability.py, app/web/run_registry.py (mới), app/web/server.py, app/web/templates/history.html (mới), app/web/templates/index.html, app/web/wsgi.py (mới), docs/deployment/S071_DEPLOYMENT.md (mới), pyproject.toml, tests/test_tracking_live_pull.py (mới), tests/test_web_run_registry.py (mới), tests/test_web_server.py, tools/tracking/live_pull.py (mới)

RELEASE_BLOCKERS = chọn+cấp credential nhà cung cấp hosting/DNS; cấu hình TRACKING_REPORT_API_KEY thật ở deployment environment; bật Cloudflare Access; verify production checklist ở docs/deployment/S071_DEPLOYMENT.md
DEFERRED_FINDINGS = xem §9 — không purge/rotation cho runs.db/outputs; Product Identity Discovery Gap (S068, chưa đóng); inv.map/alias.map/board không có temporal safety net (S069, chưa đóng)
SCOPE_DRIFT = KHÔNG — mọi thay đổi nằm trong phạm vi S071 §1–19; local Owner launcher path (S068–S070) không đổi hành vi, chỉ hưởng lợi phụ (registry giờ cũng persistent qua restart trên máy Owner, không phải yêu cầu riêng nhưng không vi phạm gì)

S071_IMPLEMENTATION_GATE = CODE_COMPLETE, VERIFYING — chưa DONE vì DEPLOYMENT_STATUS chưa DEPLOYED (S071 §20: hoàn thành code/test rồi STOP tại deployment gate — đúng như đang làm)
INDEPENDENT_REVIEW_READY = YES — code+test sẵn sàng review độc lập ngay cả khi chưa deploy

NEXT_VERTICAL_ACTION = Owner/người có credential thực hiện docs/deployment/S071_DEPLOYMENT.md (chọn nhà cung cấp, mount volume, đặt secret, trỏ DNS, bật Cloudflare Access), sau đó chạy Production Acceptance Checklist trong cùng tài liệu; sau khi PASS, một phiên Independent Review xác nhận lại toàn bộ trên production thật trước khi merge canonical
```

## 11. S071 DEPLOYMENT GATE — tiếp tục trực tiếp (cùng ngày, follow-up)

Yêu cầu: không mở task/kiến trúc mới, không independent review — thực hiện
**deployment architecture selection** ngay trong session (không đẩy việc
"chọn nhà cung cấp" cho Owner), rồi đưa Shared Online Beta tới sát nhất có
thể với production thật.

### 11.1 Verify Git trước khi tiếp tục

**FACT** — `git fetch origin claude/extract-upload-repo-gq2ws4`: canonical
vẫn `d64d208775c96a02791c957df25c11d6bf9835f8`, KHÔNG di chuyển từ phiên
trước. Branch `claude/s071-shared-online-beta-inydpg` local khớp
`HEAD_BEFORE = 25413f2ed291efc01935bf6aedb702e5782a65a5` (đúng số báo cáo ở
phiên trước), 3 commit ahead canonical, 0 behind. Không có công việc trùng
lặp nào cần audit.

### 11.2 Kiểm tra khả năng deploy thật trong session (FACT, đã verify trực tiếp)

Trước khi chọn kiến trúc, verify xem session này có thể TỰ thực hiện
provisioning hay không — không giả định:

- Không có CLI provider nào cài sẵn (`flyctl`, `render`, `railway`, `aws`,
  `gcloud`, `az`, `doctl`, `heroku`, `wrangler` — đều "not found").
- `docker` CLI có sẵn (build/test container cục bộ được), nhưng không giúp
  provisioning hạ tầng thật ở một provider từ xa.
- `curl https://api.fly.io` từ trong session → proxy trả **403** tại tầng
  CONNECT. `curl http://127.0.0.1:38243/__agentproxy/status` xác nhận:
  `recentRelayFailures` ghi lại đúng sự kiện
  `{"kind":"connect_rejected","detail":"gateway answered 403 to CONNECT
  (policy denial or upstream failure)","host":"api.fly.io:443"}`.
  `/root/.ccr/README.md` xác nhận đây là "chính sách egress của tổ chức từ
  chối host ngoài allowlist — không retry, không route around, báo cáo lại
  host bị chặn" — áp dụng chung cho mọi provider hosting/DNS ngoài
  allowlist nội bộ (npm/pypi/crates/GitHub/Anthropic), không riêng Fly.io.

**INFERENCE** — cùng chính sách egress chặn `render.com`, `railway.app`,
`api.cloudflare.com`, v.v. (không test riêng từng host vì hành vi đã xác
nhận là chính sách allowlist tổ chức, không phải lỗi tạm thời của một host
cụ thể — retry sẽ không đổi kết quả, đúng hướng dẫn README).

**Kết luận**: session có thể chọn kiến trúc + viết mọi code/config hỗ trợ
deploy, nhưng KHÔNG thể tự gọi API/CLI của bất kỳ provider hosting nào để
thật sự tạo service/volume/domain — đây là giới hạn hạ tầng mạng của MÔI
TRƯỜNG CHẠY SESSION, đã verify bằng lệnh thật, không phải giả định.

### 11.3 Deployment architecture selection (thực hiện trong session, không hỏi Owner)

**DECISION — `SELECTED_HOSTING = Render`** (Web Service, runtime Docker,
plan Starter + 1 Disk). So sánh đầy đủ 3 lựa chọn (Render / Fly.io / VPS
thô) — bảng, lý do chọn, lý do loại hai phương án còn lại — ghi tại
`docs/deployment/S071_DEPLOYMENT.md` "So sánh kiến trúc hosting", không lặp
lại ở đây. Tóm tắt quyết định: Render là lựa chọn duy nhất vừa có persistent
disk vừa deploy-từ-GitHub hoàn toàn qua dashboard (không đòi Owner học CLI)
— đúng trọng số "operational simplicity" ngang hàng "chi phí" trong tiêu chí
đầu bài, cho một Owner không chuyên kỹ thuật.

**`OWNER_PAYMENT_REQUIRED = YES`** — không có lựa chọn managed nào (kể cả
hai phương án bị loại) cấp persistent disk thật miễn phí vĩnh viễn. Plan cụ
thể: **Render Starter (~US$7/tháng) + 1GB Disk (~US$0.25/tháng) ≈
US$7–10/tháng**. Dừng đúng tại đây theo yêu cầu — KHÔNG tự tạo tài khoản/
subscription thay Owner.

### 11.4 SQLite + artifact trên MỘT persistent disk (S071 §3/§4)

**FACT** — kiểm tra lại implementation hiện có (trước follow-up này): artifact
`.xlsx` lưu tại `outputs/reports/` (`ARTIFACT_DIR`, tương đối `REPO_ROOT`),
registry SQLite tại `data/web_runs/runs.db` (`DEFAULT_DB_PATH`, cũng tương
đối `REPO_ROOT`) — HAI gốc khác nhau (`outputs/` vs `data/`) dưới cùng
`REPO_ROOT`. Trên container ephemeral filesystem, cả hai đều mất khi
container bị thay thế trừ khi được mount — không tự động "cùng nằm trên một
volume" chỉ vì cùng nằm trong repo.

**Render chỉ cho gắn ĐÚNG MỘT persistent Disk mỗi Web Service** (giới hạn
platform, không phải giả định) — hai gốc riêng biệt sẽ không cùng persist
được nếu không hợp nhất.

**DECISION** — thêm biến môi trường `REPORTS_DATA_ROOT` (mới,
`app/web/server.py` + `app/web/run_registry.py`): khi đặt, `UPLOAD_DIR`,
`ARTIFACT_DIR`, `TRACKING_TEMP_DIR`, `run_registry.DEFAULT_DB_PATH` đều tự
trỏ vào cùng gốc đó (`<gốc>/data/...`, `<gốc>/outputs/reports/`) — một biến
duy nhất, một Disk duy nhất. Khi KHÔNG đặt (mọi test, mọi local dev trước
đây), hành vi cũ (tương đối `REPO_ROOT`) giữ nguyên tuyệt đối — đây là thay
đổi tối thiểu trực tiếp cần cho deployment gate, không phải refactor lại
kiến trúc registry/artifact đã accept ở phiên trước (đúng yêu cầu "không mở
task/kiến trúc mới", "không refactor nếu không có blocker deployment trực
tiếp" — đây LÀ blocker deployment trực tiếp: không có cách nào Render's
1-disk-per-service chạy đúng nếu không hợp nhất gốc).

`render.yaml` (mới, root) đặt `REPORTS_DATA_ROOT=/app/persistent`, Disk
1GB mount đúng đường đó — Owner không cần tự nghĩ ra cấu hình này.

**Test mới**: `tests/test_web_data_root.py` (2 test) — có `REPORTS_DATA_ROOT`
→ cả 4 đường dẫn cùng dưới một gốc; vắng mặt → giữ nguyên đường
`REPO_ROOT` cũ. **2/2 PASS.** Full regression sau thay đổi: **1442 passed,
11 skipped** (từ 1440 baseline implementation gate — +2 test mới, không
regression).

### 11.5 Gate hoàn thành được / không hoàn thành được trong session này

Không fabricate PASS cho các gate cần production thật (đúng "Luật Cuối
Cùng" CLAUDE.md — chứng minh bằng artifact/bằng chứng, không phải lời kể).
Trạng thái chính xác từng gate ở RETURN block bên dưới
(`HTTPS_GATE`…`REAL_COHORT_GATE`) — tất cả `NOT_EXECUTABLE_IN_THIS_SESSION`,
không phải `PASS` hay `FAIL` giả.

### 11.6 RETURN (deployment gate)

```
S071_DEPLOYMENT_GATE = HOSTING_SELECTED_AND_CONFIGURED, NOT_PROVISIONED (giới hạn mạng session + tài khoản/thanh toán thuộc Owner — xem §11.2)

GIT_BRANCH = claude/s071-shared-online-beta-inydpg
HEAD_BEFORE = 25413f2ed291efc01935bf6aedb702e5782a65a5
HEAD_AFTER = c36972b19af830457178589c25387adb65d16903

HOSTING_OPTIONS = Render (Web Service+Disk) / Fly.io (Machines+Volume) / VPS thô (Hetzner/DO+Docker tay) — bảng so sánh đầy đủ tại docs/deployment/S071_DEPLOYMENT.md
SELECTED_HOSTING = Render — Web Service, runtime Docker, plan Starter + 1GB Disk
SELECTED_PLAN = Starter (~US$7/tháng) + Disk 1GB (~US$0.25/tháng)
ESTIMATED_COST = ~US$7–10/tháng
PAYMENT_REQUIRED = YES — không provider managed nào trong 3 lựa chọn có persistent disk miễn phí vĩnh viễn; Owner cần tạo tài khoản Render + phương thức thanh toán (session không làm thay được)

PYTHON_RUNTIME = Python 3.11-slim (Dockerfile), gunicorn qua app/web/wsgi.py
START_COMMAND = gunicorn --workers 2 --threads 4 --bind 0.0.0.0:${PORT} --timeout 120 app.web.wsgi:application

SQLITE_PATH = ${REPORTS_DATA_ROOT}/data/web_runs/runs.db (production: /app/persistent/data/web_runs/runs.db qua render.yaml)
SQLITE_PERSISTENT = YES — nằm dưới Render Disk mount path /app/persistent (theo blueprint; CHƯA verify trên Render thật — chưa provisioned)
SQLITE_SURVIVES_RESTART = ĐÃ verify bằng test (tests/test_web_run_registry.py, tests/test_web_server.py restart persistence) — CHƯA verify trên production thật
SQLITE_SURVIVES_REDEPLOY = Theo thiết kế Render Disk (Disk sống độc lập với service instance, tài liệu Render) — CHƯA verify trên production thật (chưa deploy)

ARTIFACT_PATH = ${REPORTS_DATA_ROOT}/outputs/reports/*.xlsx (production: /app/persistent/outputs/reports/)
ARTIFACT_PERSISTENT = YES — cùng Disk với SQLite (REPORTS_DATA_ROOT hợp nhất cả hai, xem §11.4)
ARTIFACT_SURVIVES_RESTART = Đã verify bằng test — CHƯA verify production thật
ARTIFACT_SURVIVES_REDEPLOY = Theo thiết kế Render Disk — CHƯA verify production thật (chưa deploy)

TRACKING_SOURCE_URL = https://price.tinphatcrm.com (điền sẵn trong render.yaml, không phải secret)
TRACKING_SECRET_CONFIGURATION = OWNER_ACTION_REQUIRED — TRACKING_REPORT_API_KEY đánh dấu sync:false trong render.yaml, Owner nhập tay trong Render dashboard lúc deploy
TRACKING_LIVE_READY = BLOCKED_BY_REMOTE_SECRET (không đổi từ phiên trước — session vẫn không có secret thật để verify network call)

DEPLOYMENT_STATUS = DEPLOYMENT_READY — HOSTING_SELECTED, CONFIG_COMPLETE (render.yaml + REPORTS_DATA_ROOT), KHÔNG DEPLOYED
ORIGIN_URL = (chưa có — cấp sau khi Owner deploy blueprint, dạng reports-web-xxxx.onrender.com trước khi gắn domain thật)

CLOUDFLARE_DNS_REQUIRED = CNAME "reports" → domain Render cấp (DNS-only lúc đầu để verify + cấp cert, có thể proxy lại sau)
CLOUDFLARE_DNS_TARGET = reports.tinphatcrm.com → <domain Render cấp, biết được sau khi Owner deploy>
CLOUDFLARE_ACCESS_REQUIRED = YES — Access Application self-hosted giới hạn theo email công ty, tạo trong Cloudflare Zero Trust dashboard (không cần Reports tự xây đăng nhập)

HTTPS_GATE = NOT_EXECUTABLE_IN_THIS_SESSION (chưa có production URL)
ACCESS_GATE = NOT_EXECUTABLE_IN_THIS_SESSION
PERSISTENCE_GATE = NOT_EXECUTABLE_IN_THIS_SESSION trên production; PASS trên test (tests/test_web_run_registry.py, tests/test_web_server.py restart tests)
MULTI_RUN_GATE = NOT_EXECUTABLE_IN_THIS_SESSION trên production; PASS trên test
MULTI_VIEWER_GATE = NOT_EXECUTABLE_IN_THIS_SESSION trên production; PASS trên test
TRACKING_GATE = NOT_EXECUTABLE_IN_THIS_SESSION (không có secret thật + không có mạng ra ngoài tới Tracking source)
REAL_COHORT_GATE = OWNER_REAL_COHORT_REQUIRED — không có workbook thật trong Cloud, không fabricate; Owner upload qua production sau khi site available (không đổi từ phiên trước)

OWNER_PAYMENT_REQUIRED = YES — Render Starter + Disk, ~US$7–10/tháng, xem SELECTED_PLAN
OWNER_ACTION_REQUIRED = 6 bước chính xác tại docs/deployment/S071_DEPLOYMENT.md "Việc Owner cần làm" — tạo tài khoản Render, Deploy Blueprint, dán TRACKING_REPORT_API_KEY thật, trỏ Cloudflare CNAME, gắn Custom Domain, tạo Cloudflare Access Application

FILES_CHANGED = Dockerfile, app/web/run_registry.py, app/web/server.py, docs/deployment/S071_DEPLOYMENT.md, render.yaml (mới), tests/test_web_data_root.py (mới)
DEPLOYMENT_SHA = c36972b19af830457178589c25387adb65d16903 (commit này chỉnh lại 2 placeholder SHA trong chính tài liệu — sẽ có một SHA kế tiếp)
REMOTE_BRANCH = claude/s071-shared-online-beta-inydpg

RELEASE_BLOCKERS = tài khoản+thanh toán Render (Owner); secret TRACKING_REPORT_API_KEY thật; Cloudflare Access application; DNS thật — không còn blocker code/kiến trúc nào
SCOPE_DRIFT = KHÔNG — REPORTS_DATA_ROOT là thay đổi tối thiểu trực tiếp cần cho ràng buộc "1 Disk/service" của hosting đã chọn (§11.4), không refactor gì khác của registry/artifact/live-pull đã accept ở implementation gate

S071_PRODUCTION_ACCEPTANCE = CHƯA — chờ Owner thực hiện 6 bước + Production Acceptance Checklist trong docs/deployment/S071_DEPLOYMENT.md
INDEPENDENT_REVIEW_READY = YES cho phần code/config (đúng yêu cầu "không independent review lúc này" — chỉ ghi sẵn trạng thái, không tự chạy review); review đầy đủ có ý nghĩa nhất SAU khi Owner deploy thật và tick được Production Acceptance Checklist

NEXT_VERTICAL_ACTION = Owner thực hiện đúng 6 bước tại docs/deployment/S071_DEPLOYMENT.md (tạo tài khoản Render có thanh toán → Deploy Blueprint từ render.yaml → dán secret Tracking thật → Cloudflare CNAME → Custom Domain → Cloudflare Access) → tick Production Acceptance Checklist (GATE A–G) → báo lại kết quả để mở một phiên Independent Review xác nhận trên production thật trước khi merge canonical
```

## 12. S071B — Stateless Persistence Adapter (follow-up trực tiếp)

Ngày: 2026-09-01. Nhánh: `s071b/stateless-r2`. Baseline: đúng HEAD của
nhánh `claude/s071-shared-online-beta-inydpg` tại §11.6
(`c36972b19af830457178589c25387adb65d16903`, sau đó có thêm 1 commit
doc-touch-up — baseline thật của S071B là HEAD tại thời điểm mở phiên,
xem RETURN bên dưới).

**Mục tiêu duy nhất**: thay SQLite + persistent filesystem (§11.4) bằng
Cloudflare R2 để Reports Python web runtime trở thành STATELESS. KHÔNG đổi
Reports Core/business logic.

### 12.1 SUPERSEDES §3 và §11

§3 ("Kiến trúc — So sánh và lựa chọn") loại bỏ mọi kiến trúc dùng database
managed (Postgres/D1) hay object storage với lý do "SQLite trên đĩa persistent
là managed solution nhỏ nhất phù hợp quy mô Beta". §11.3–§11.4 sau đó chọn
Render + MỘT persistent Disk chính vì ràng buộc "1 Disk/service" của
Render buộc SQLite + artifact phải hợp nhất một gốc mount
(`REPORTS_DATA_ROOT`).

**S071B đảo lại tiền đề đó**: registry run + artifact chưa bao giờ cần
đọc/ghi ngẫu nhiên trên một file hệ thống — toàn bộ truy cập chỉ là
put/get theo `run_id` (tạo, đọc một run, liệt kê tất cả) — đúng hình dạng
một object store, không phải một cơ sở dữ liệu quan hệ. Việc S071 chọn
SQLite + Disk là **implementation convenience** để tái dùng persistence
sẵn có (SQLite driver có sẵn trong Python), **không phải một Reports Core
requirement**. Object storage (R2) khớp đúng hình dạng truy cập thật hơn,
và loại bỏ hoàn toàn ràng buộc "1 Disk/service" — không phải vì ràng buộc
đó được giải quyết khéo hơn, mà vì nó không còn áp dụng nữa (không có Disk
nào).

`REPORTS_DATA_ROOT`, SQLite (`app/web/run_registry.py`), và `render.yaml`
Disk KHÔNG bị xoá khỏi lịch sử §3/§11 — vẫn đúng như log lịch sử của quyết
định S071 tại thời điểm đó. Code hiện tại vẫn GIỮ `RunRegistry` (SQLite)
nguyên vẹn làm fallback local/test (xem §12.3) — S071B không xoá đường cũ,
chỉ thêm một đường mới và đổi đường nào là production default.

### 12.2 R2 object model

```
runs/<run_id>.json       — một run. run_id đã sortable theo thời gian
                            (report-<UTC timestamp compact>[-NN]) — dùng
                            thẳng làm key, không lặp lại created_at.
artifacts/<run_id>.xlsx  — artifact .xlsx của đúng run đó.
```

**DECISION** — không dùng nguyên văn `runs/<sortable-created-at>-<run-id>.json`
như gợi ý trong brief. `run_id` hiện tại (`app.owner_usability.
default_output_path`) đã có dạng `report-<UTC timestamp compact>[-NN]`,
tức bản thân nó ĐÃ sortable theo thời gian — lặp lại `created_at` ở đầu key
là dữ liệu trùng lặp không cần thiết. Dùng thẳng `run_id` làm key cho phép:
`get_run` resolve O(1) chính xác (một `head_object`/`get_object`, không cần
scan/index phụ để tìm key theo run_id), VÀ liệt kê mới→cũ bằng cách sort
TÊN KHOÁ giảm dần (không fetch body). Đánh đổi: key scheme này coupling
với format run_id hiện tại của `owner_usability.py` — nếu format đó đổi
sang thứ không còn sortable (vd UUID ngẫu nhiên), listing sẽ sai thứ tự.
DEFERRED — không phải rủi ro thật trong scope S071B (không đổi
`owner_usability.py`).

Không có một file index JSON dùng chung mà nhiều writer phải race để cập
nhật — mỗi run là một object độc lập, đúng yêu cầu CONCURRENCY của task.

`put_json_if_absent` dùng HEAD-rồi-PUT (không `IfNoneMatch` điều kiện của
S3/R2) để phát hiện `run_id` trùng — có một khe race lý thuyết giữa hai
lời gọi đồng thời cho CÙNG run_id, nhưng run_id luôn do server sinh mới mỗi
lần chạy (đúng docstring gốc của `RunRegistry.create_run`: "một run_id
trùng là lỗi lập trình, không phải một tình huống cần xử lý êm") — không
phải kịch bản concurrency thật trong beta này.

### 12.3 Implementation

- `tools/storage/r2_store.py` (mới, NGOÀI `app/`) — client S3-compatible
  (`boto3`, `endpoint_url` trỏ `https://<account_id>.r2.cloudflarestorage.com`,
  `region_name="auto"`) cho put/get JSON + bytes trên R2. Nằm ngoài `app/`
  bắt buộc: `boto3` nằm trong danh sách cấm import trực tiếp dưới `app/`
  của `test_no_module_under_app_reaches_the_network` (`ADR-101`) — đúng
  ranh giới `tools/tracking/live_pull.py` đã dùng cho network primitive
  khác. `tools/storage/errors.py` (mới) — `StorageUnavailableError`
  (network/timeout/auth), `RunAlreadyExistsError` (run_id trùng),
  `CorruptRunRecordError` (JSON hỏng — KHÔNG lẫn với "không tồn tại").
- `app/web/storage_backend.py` (mới, dưới `app/`, KHÔNG tự `import boto3`
  — chỉ gọi hàm public của `tools.storage.r2_store`) — `LocalRunStore`
  (SQLite + file cục bộ, bọc nguyên `RunRegistry` đã có, hành vi S070/S071
  không đổi) và `R2RunStore` cùng một interface tối thiểu (`create_run`/
  `get_run`/`list_runs`/`save_artifact`/`artifact_response`) —
  `app/web/server.py` không biết đang chạy trên backend nào.
  `build(db_path, artifact_dir)` chọn `R2RunStore` khi đủ 4 biến
  `R2_ACCOUNT_ID`/`R2_BUCKET`/`R2_ACCESS_KEY_ID`/`R2_SECRET_ACCESS_KEY`,
  ngược lại `LocalRunStore` — TRỪ khi `REPORTS_REQUIRE_R2=1` (production),
  khi đó raise `StorageConfigurationError` ngay khi tạo Flask app thay vì
  âm thầm chạy bằng SQLite/đĩa ephemeral trong container (đúng yêu cầu
  "Production mode phải fail configuration validation").
- `app/web/server.py` — `create_app()` nhận thêm tham số `store=` (test
  tiêm trực tiếp, không cần credential R2 thật); construction đổi
  `registry = run_registry.RunRegistry(...)` → `store =
  storage_backend.build(...)`; mọi route đổi `registry.` → `store.`, bọc
  qua `_guarded()` (mới) — bắt `StorageUnavailableError`/
  `CorruptRunRecordError`, trả HTTP 503 rõ ràng thay vì để lộ traceback
  hoặc âm thầm hiểu nhầm thành "không tìm thấy"/"lịch sử rỗng". Artifact
  save (R2: đọc bytes file tạm cục bộ đã có sẵn → `put_bytes` (upload +
  verify `head_object` so khớp `ContentLength`) → xoá file tạm; local:
  giữ nguyên logic cũ) PHẢI thành công trước khi `create_run` — fail
  closed đúng yêu cầu "run không được xuất hiện như successful completed
  run với artifact không tồn tại". Raw workbook upload (`UPLOAD_DIR`) vẫn
  temp-only như S070/S071 — S071B không đổi, không upload workbook thô lên
  R2.
- `render.yaml` — xoá khối `disk:`; thêm `REPORTS_REQUIRE_R2=1` +
  `R2_ACCOUNT_ID`/`R2_BUCKET` (giá trị Owner tự điền) +
  `R2_ACCESS_KEY_ID`/`R2_SECRET_ACCESS_KEY` (`sync: false`, Owner nhập tay,
  cùng convention `TRACKING_REPORT_API_KEY` đã có). `Dockerfile` — cập
  nhật comment phản ánh đúng kiến trúc mới; `mkdir /app/data
  /app/outputs/reports` giữ nguyên nhưng chỉ còn ý nghĩa scratch space tạm
  cho một lần chạy, không phải mount point persistent. `pyproject.toml` —
  thêm optional-dependency `storage = ["boto3>=1.34"]`, gộp vào
  `web-prod`; core CLI/Tkinter/`web` (Flask-only, local dev) không cần
  cài `boto3`.

### 12.4 Test

`tests/fixtures/fake_r2_client.py` (mới) — fake S3-compatible client
in-memory (`head_object`/`get_object`/`put_object`/`list_objects_v2`),
tiêm lỗi theo method (`fail[method] = exception_hoặc_callable`) — không
cần credential/mạng R2 thật, đúng dự liệu của task ("Nếu credential không
tồn tại trong Claude Cloud: tests dùng fake/mock"). `tools/storage/
r2_store.py` (và mọi hàm gọi xuống nó) nhận tham số `client=`/`env=` xuyên
suốt để test tiêm fake — production path (`client=None`) mới thật sự tạo
`boto3.client(...)`.

`tests/test_r2_store.py` (20 test): put/get JSON round-trip, unknown key
→ `None`, duplicate `run_id` → `RunAlreadyExistsError`, JSON corrupt →
`CorruptRunRecordError` (KHÔNG phải `None`), R2 unavailable/timeout/auth
failure → `StorageUnavailableError` (head/get/put), list newest-first +
tôn trọng `limit`, list lịch sử rỗng → `[]` không lỗi, list failure →
`StorageUnavailableError` không phải lịch sử rỗng, artifact put/get bytes
round-trip, artifact missing → `None`, verify-sau-upload sai kích thước →
fail closed, artifact upload failure → `StorageUnavailableError`.

`tests/test_storage_backend.py` (18 test): `build()` chọn Local khi R2
chưa cấu hình / chọn R2 khi đã cấu hình đủ / fail closed
(`StorageConfigurationError`) khi `REPORTS_REQUIRE_R2=1` thiếu credential
(kể cả chỉ thiếu 1 trong 4 biến); `R2RunStore` create/get round-trip đủ
field, unknown run_id → `None`, run_id không hợp lệ (path traversal) →
`None` không phải exception, list newest-first, hai instance độc lập
cùng client đọc chung một run (MULTI-VIEWER), duplicate run_id →
`RunAlreadyExistsError`, list bỏ qua đúng 1 record hỏng mà vẫn giữ các
record tốt (không sập cả trang), list propagate lỗi storage thật (không
biến thành lịch sử rỗng); artifact save → upload + verify + xoá file tạm
+ download lại đúng bytes, artifact missing → `None`, artifact-run
mismatch (artifact_path không khớp key tự suy từ run_id) → `None` (không
bao giờ resolve theo artifact_path thô), artifact upload failure không để
lại reference lơ lửng (run không tồn tại sau đó).

`tests/test_web_server.py` thêm 9 test tích hợp Flask end-to-end qua R2
(fake client, `create_app(store=...)`): run→download round-trip qua R2
thật (đường code thật, không mock `run_owner_report`/`store`), file tạm
cục bộ bị xoá sau upload; 2 viewer độc lập (2 Flask app + 2 test client)
đọc chung một run qua CÙNG fake R2 client (MULTI-VIEWER); 2 run tạo gần
đồng thời (cùng client) đều lưu độc lập, đọc lại đủ cả hai
(CONCURRENT_RUNS); artifact upload failure → response 500 không traceback
+ run KHÔNG xuất hiện trong registry (fail closed, không phải "thành công
giả"); get_run/list_runs failure → HTTP 503 (không phải 404/lịch sử rỗng
giả); artifact-run mismatch → 404; `REPORTS_REQUIRE_R2=1` thiếu credential
→ `create_app()` raise `StorageConfigurationError` (fail lúc khởi động,
không lúc runtime).

**Full regression**: `1489 passed, 11 skipped` (từ baseline `1442 passed,
11 skipped` — +47 test mới, KHÔNG skip nào đổi, KHÔNG giảm coverage sẵn
có). Bất biến kiến trúc `test_no_module_under_app_reaches_the_network`
verify lại PASS.

### 12.5 Production LOC

429 dòng Python net mới (`app/web/storage_backend.py` +176,
`tools/storage/r2_store.py` +198, `tools/storage/errors.py` +25,
`app/web/server.py` net +30) — vượt ước tính audit ban đầu (~250–350)
nhưng dưới ngưỡng dừng cứng 500, KHÔNG trigger `CHANGE_BUDGET_EXCEEDED`.
Nguyên nhân vượt ước tính: failure model tường minh theo đúng yêu cầu của
task (phân biệt rõ 4 loại lỗi — storage unavailable / corrupt / not-found
/ already-exists — thay vì gộp chung một exception mơ hồ) cộng với
dependency injection (`client=`/`env=`) xuyên suốt để test không cần
credential thật. KHÔNG có generic storage framework, KHÔNG abstract nhiều
provider — đúng một R2 adapter duy nhất, đúng yêu cầu.

### 12.6 Không verify được trong session này

**`R2_LIVE_VERIFICATION = BLOCKED_BY_MISSING_CREDENTIAL`** — môi trường
Claude Cloud chạy session S071B không có
`R2_ACCOUNT_ID`/`R2_BUCKET`/`R2_ACCESS_KEY_ID`/`R2_SECRET_ACCESS_KEY` thật,
và cũng không có `boto3` cài sẵn (không cần cho test — toàn bộ 47 test
mới tiêm `client=` fake, không import `boto3` thật, xem §12.4). Đúng dự
liệu trước của task ("Nếu credential không tồn tại trong Claude Cloud:
tests dùng fake/mock. Không STOP implementation") — KHÔNG coi là
architecture blocker, KHÔNG fabricate PASS cho một R2 call thật.

**`DEPLOYMENT_STATUS`** — không đổi so với §11: session không có tài khoản
Cloudflare/Render để tạo R2 bucket/API token thật hay deploy lại. DEFERRED
cho Owner — xem `docs/deployment/S071_DEPLOYMENT.md` (đã cập nhật SUPERSEDES
+ bước Owner cần làm).

### 12.7 DEFERRED (không phải regression)

- Migration SQLite → R2: KHÔNG build (đúng yêu cầu — Internal Beta chưa
  production-deploy, dữ liệu SQLite local hiện có không phải production
  authority).
- Key scheme coupling với format `run_id` của `owner_usability.py` — xem
  §12.2 DECISION.
- `list_run_keys_desc` quét tối đa 5000 key mỗi lần gọi `/history` — đủ
  cho quy mô Internal Beta, không phải một giải pháp phân trang tổng quát.
- R2 IfNoneMatch điều kiện thật (thay HEAD-rồi-PUT) — không cần thiết ở
  quy mô/kịch bản concurrency thật của run_id server-generated, xem §12.2.

### 12.8 RETURN

```
S071B_IMPLEMENTATION = CODE_COMPLETE, TEST_COMPLETE (fake client), CHƯA DEPLOYED, CHƯA merge canonical

BASELINE = 5f12516cde2c51b4307413ac960eb6a1c97da2ec
BRANCH = s071b/stateless-r2
HEAD = fbc8fc74e88e50f8005504e0ea19ee44a64f4adf (implementation SHA — sẽ có thêm 1 commit doc-touch-up ngay sau, xem commit cuối cùng thật trên nhánh cho HEAD chính xác nhất)

R2_RUN_STORE = tools/storage/r2_store.py + app/web/storage_backend.py::R2RunStore — put/get JSON qua boto3 S3-compatible client, endpoint https://<account_id>.r2.cloudflarestorage.com
R2_ARTIFACT_STORE = cùng r2_store.py — put_bytes (upload + verify head_object) / get_bytes cho artifacts/<run_id>.xlsx
R2_KEY_SCHEME = runs/<run_id>.json (run_id đã sortable theo thời gian, xem §12.2 DECISION) + artifacts/<run_id>.xlsx

SQLITE_PRODUCTION_DEPENDENCY = KHÔNG — production (REPORTS_REQUIRE_R2=1) dùng R2RunStore, SQLite chỉ còn là fallback local/test
PERSISTENT_DISK_DEPENDENCY = KHÔNG — render.yaml không còn khối disk:
REPORTS_DATA_ROOT_PRODUCTION_DEPENDENCY = KHÔNG BẮT BUỘC — chỉ còn ý nghĩa local-only/fallback (LocalRunStore khi R2 chưa cấu hình và REPORTS_REQUIRE_R2 không bật)

LOCAL_COMPATIBILITY = GIỮ NGUYÊN — LocalRunStore bọc nguyên RunRegistry (SQLite) đã có, R2 chưa cấu hình → hành vi S070/S071 không đổi, mọi test cũ PASS không sửa

RAW_WORKBOOK_PERSISTED = KHÔNG — vẫn temp-only (UPLOAD_DIR, xoá trong finally), không đổi từ S070/S071, không upload lên R2
TEMP_FILE_CLEANUP = CÓ — artifact temp file bị unlink() ngay sau khi R2 upload xác nhận verify xong (app/web/storage_backend.py::R2RunStore.save_artifact); workbook temp file xoá trong finally của run_report() (không đổi)

RUN_CREATE = PASS (test_r2_store, test_storage_backend, test_web_server — 20+18+9 test)
RUN_GET = PASS — unknown run_id → None, invalid run_id → None, corrupt JSON → CorruptRunRecordError (không lẫn "not found")
RUN_LIST = PASS — newest-first, list rỗng an toàn, 1 record hỏng không sập cả trang, storage failure propagate không giả làm lịch sử rỗng
ARTIFACT_UPLOAD = PASS — upload + verify head_object + xoá temp; verify sai kích thước → fail closed, KHÔNG create_run
ARTIFACT_DOWNLOAD = PASS — resolve qua run metadata authoritative, key luôn tự suy từ run_id, artifact-run mismatch → None/404

MULTI_VIEWER = PASS (test — 2 R2RunStore/2 Flask app độc lập, cùng fake R2 client, đọc chung 1 run)
CONCURRENT_RUNS = PASS (test — 2 run tạo gần đồng thời, cùng client, đều lưu + đọc lại độc lập)

R2_FAILURE_TESTS = PASS — unavailable/timeout/auth (head/get/put), verify-mismatch, list failure — tất cả StorageUnavailableError, không silent swallow
ARTIFACT_FAILURE_TESTS = PASS — upload failure không tạo run "thành công giả"; artifact missing → 404; artifact-run mismatch → 404
SECURITY_TESTS = PASS — run_id không hợp lệ (path traversal) → None/404 không phải lỗi; R2 key luôn server tự suy, browser không bao giờ cung cấp key trực tiếp; response không lộ credential/traceback (kế thừa test cũ + test mới _storage_unavailable handler)

PRODUCTION_ENV_VARS = REPORTS_REQUIRE_R2 (bool), R2_ACCOUNT_ID, R2_BUCKET, R2_ACCESS_KEY_ID (secret), R2_SECRET_ACCESS_KEY (secret) — tên biến xem tools/storage/r2_store.py
SECRETS_BROWSER_EXPOSED = KHÔNG — credential R2 chỉ đọc server-side (tools/storage/r2_store.py, os.environ), không log, không truyền vào bất kỳ response nào

RENDER_DISK_REMOVED = CÓ — render.yaml không còn khối disk:
STATELESS_RUNTIME = CÓ theo thiết kế + test (R2RunStore không giữ state process-local nào ngoài client/env tham số tiêm khi test; production path tự tạo client ngắn hạn per-call) — CHƯA verify trên container Render thật (chưa deploy, không có credential R2 thật trong session)

PRODUCTION_LOC_ADDED = 429 dòng Python net (chi tiết §12.5) — dưới ngưỡng dừng cứng 500, vượt ước tính audit ~250–350

FOCUSED_TESTS = tests/test_r2_store.py (20) + tests/test_storage_backend.py (18) = 38 test, tất cả PASS
AFFECTED_TESTS = tests/test_web_server.py +9 test R2 integration, tất cả 47 test cũ của file này vẫn PASS không sửa logic (chỉ thêm import) = 56/56 PASS
FULL_REGRESSION = 1489 passed, 11 skipped (từ baseline 1442 passed, 11 skipped — +47, không skip đổi, không regression)

FILES_CHANGED = app/web/server.py, app/web/storage_backend.py (mới), tools/storage/__init__.py (mới), tools/storage/errors.py (mới), tools/storage/r2_store.py (mới), render.yaml, Dockerfile, pyproject.toml, PROJECT/PROJECT_PROGRESS.md, PROJECT/LO_TRINH_DE_HIEU.md, docs/sessions/S071-shared-online-beta.md (file này), docs/deployment/S071_DEPLOYMENT.md, tests/test_r2_store.py (mới), tests/test_storage_backend.py (mới), tests/test_web_server.py, tests/fixtures/fake_r2_client.py (mới)
IMPLEMENTATION_SHA = fbc8fc74e88e50f8005504e0ea19ee44a64f4adf
REMOTE_BRANCH = s071b/stateless-r2 (push sau khi commit — KHÔNG merge canonical, KHÔNG force)

RELEASE_BLOCKERS = tài khoản Cloudflare + R2 bucket + API token thật (Owner); credential R2 dán vào Render dashboard; verify R2 live thật (không mock) sau khi Owner có credential — không còn blocker code/kiến trúc nào
DEFERRED = migration SQLite→R2 (§12.7, không cần cho Internal Beta); key scheme coupling với format run_id (§12.2); list_run_keys_desc quét tối đa 5000 key/lần (đủ cho Internal Beta)

SCOPE_DRIFT = KHÔNG — đúng một mục tiêu duy nhất (thay SQLite+Disk bằng R2), không đổi Reports Core/business logic, không đổi call site nào ngoài chỗ chọn backend, không build provider abstraction/migration framework

S071B_GATE = CODE_COMPLETE, VERIFYING (test fake client PASS, R2 live thật CHƯA verify được — thiếu credential trong môi trường này, không phải architecture blocker)
INDEPENDENT_REVIEW_READY = YES cho phần code/test/config; ý nghĩa nhất SAU khi Owner có credential R2 thật để verify ít nhất một R2 call thật (không chỉ fake client)

NEXT_VERTICAL_ACTION = Owner tạo R2 bucket + API token trên Cloudflare dashboard → dán 4 biến R2_* vào Render (hoặc host stateless khác) → xoá Render Disk cũ nếu còn (không cần nữa) → deploy lại → tick Production Acceptance Checklist cập nhật (docs/deployment/S071_DEPLOYMENT.md) → báo lại kết quả để mở một phiên Independent Review xác nhận trên R2 thật trước khi merge canonical
```
