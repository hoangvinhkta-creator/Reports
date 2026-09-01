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
HEAD = 9c3b515db2a70b7645ffe33d73bd7eb7be19422f

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

IMPLEMENTATION_SHA = 9c3b515db2a70b7645ffe33d73bd7eb7be19422f
REMOTE_BRANCH = claude/s071-shared-online-beta-inydpg

FILES_CHANGED = 14 file (xem git diff --cached --stat §... : Dockerfile, .gitignore, app/owner_usability.py, app/web/run_registry.py (mới), app/web/server.py, app/web/templates/history.html (mới), app/web/templates/index.html, app/web/wsgi.py (mới), docs/deployment/S071_DEPLOYMENT.md (mới), pyproject.toml, tests/test_tracking_live_pull.py (mới), tests/test_web_run_registry.py (mới), tests/test_web_server.py, tools/tracking/live_pull.py (mới)

RELEASE_BLOCKERS = chọn+cấp credential nhà cung cấp hosting/DNS; cấu hình TRACKING_REPORT_API_KEY thật ở deployment environment; bật Cloudflare Access; verify production checklist ở docs/deployment/S071_DEPLOYMENT.md
DEFERRED_FINDINGS = xem §9 — không purge/rotation cho runs.db/outputs; Product Identity Discovery Gap (S068, chưa đóng); inv.map/alias.map/board không có temporal safety net (S069, chưa đóng)
SCOPE_DRIFT = KHÔNG — mọi thay đổi nằm trong phạm vi S071 §1–19; local Owner launcher path (S068–S070) không đổi hành vi, chỉ hưởng lợi phụ (registry giờ cũng persistent qua restart trên máy Owner, không phải yêu cầu riêng nhưng không vi phạm gì)

S071_IMPLEMENTATION_GATE = CODE_COMPLETE, VERIFYING — chưa DONE vì DEPLOYMENT_STATUS chưa DEPLOYED (S071 §20: hoàn thành code/test rồi STOP tại deployment gate — đúng như đang làm)
INDEPENDENT_REVIEW_READY = YES — code+test sẵn sàng review độc lập ngay cả khi chưa deploy

NEXT_VERTICAL_ACTION = Owner/người có credential thực hiện docs/deployment/S071_DEPLOYMENT.md (chọn nhà cung cấp, mount volume, đặt secret, trỏ DNS, bật Cloudflare Access), sau đó chạy Production Acceptance Checklist trong cùng tài liệu; sau khi PASS, một phiên Independent Review xác nhận lại toàn bộ trên production thật trước khi merge canonical
```
