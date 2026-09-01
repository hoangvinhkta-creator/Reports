# S070 — WEB BETA V1 / THIN WEB DELIVERY LAYER

Ngày: 2026-09-01
Nhánh: `s070/web-beta-v1`, baseline `fad7647a5f07e5eeaa3587a03f0688cb6f7bb904`
Task: cho Owner một web experience chạy được thật trên chính máy (localhost),
reuse nguyên đường production S069 đã ACCEPTED — không tính lại business
rule, không đổi authority Product Identity/PP.

## Audit Trước Khi Chọn Kiến Trúc

- `EXISTING_CORE_ENTRY_POINT` = `app/demo.py:run_demo()` — production
  composition + export, không đổi.
- `EXISTING_OWNER_SERVICE` = `app/owner_usability.py:run_owner_report()` —
  đã tự chọn capture COMPLETE mới nhất + validate `.xlsx` + gọi `run_demo` +
  fail-safe nếu không đối chiếu đủ đơn. Đây chính là adapter
  `owner_launcher.py` (Tkinter) đã dùng — S070 tái dùng NGUYÊN VĂN, không
  nhân đôi.
- `EXISTING_REPORT_RESULT` = `demo.DemoRun` (`result`, `price_records`,
  `summary: ReportSummary`, `output_path`).
- `EXISTING_ARTIFACT_CONTRACT` = `owner_usability.default_output_path()` —
  `outputs/reports/report-<UTC timestamp>[-NN].xlsx`, không bao giờ ghi đè
  (vòng lặp thêm hậu tố khi trùng).
- `EXISTING_FEEDBACK_SERVICE` = `app/beta_feedback.py` (S069) — category cố
  định, JSONL local append-only.
- `EXISTING_TELEMETRY_SERVICE` = `app/beta_telemetry.py` (S069) — đọc DUY
  NHẤT từ `ReportSummary`, JSONL local append-only.
- `EXISTING_SECRET_HANDLING` = Tracking API key qua biến môi trường/header
  trong `tools/tracking/*`, không đổi, S070 không chạm — web layer không gọi
  Tracking trực tiếp, chỉ đọc capture cục bộ đã có qua `run_owner_report`.
- `EXISTING_DEPENDENCIES` = `openpyxl`, `PyYAML` (core); `pytest` (dev).
- `WEB_FRAMEWORK_ALREADY_PRESENT` = KHÔNG. `grep` xác nhận không có
  flask/fastapi/django/bottle trong `app/`; `http.server` chỉ xuất hiện như
  mock server trong `tests/test_tracking_contract_client.py`.

## Chọn Framework

Chọn **Flask 3.x**, thêm dưới `[project.optional-dependencies].web` trong
`pyproject.toml` — KHÔNG thêm vào `dependencies` core, để CLI/Tkinter
(`demo.py`, `owner_launcher.py`) giữ nguyên footprint cũ.

Lý do: cần multipart file upload + routing tối thiểu. Tự viết multipart
parser trên `http.server` sẽ nhiều code hơn, nhiều bề mặt lỗi bảo mật hơn
(malformed multipart, path handling) so với dùng lại parser đã kiểm chứng
của Werkzeug (dependency của Flask). Flask dev server mặc định bind
`127.0.0.1`-compatible, không build step, không Node, một dependency duy
nhất — đúng "phương án nhỏ nhất phù hợp" theo governance.

## Kiến Trúc

```
Browser
  → app/web/server.py (Flask, thin — không business rule)
  → app.owner_usability.run_owner_report()  [KHÔNG ĐỔI]
  → app.demo.run_demo()                      [KHÔNG ĐỔI]
  → pricing/export pipeline đã accepted       [KHÔNG ĐỔI]
  → artifact (outputs/reports/*.xlsx)
```

`app/web/server.py` chỉ: nhận upload → lưu path server-generated (không tin
filename client) → gọi `run_owner_report` → trình bày `ReportSummary` qua
đúng `beta_presentation.REASON_DISPLAY_LABELS` (S069, không nhân đôi
taxonomy) → đăng ký `run_id` (= `output_path.stem`, cùng quy ước
`owner_launcher.py` đã dùng) vào registry in-process → reuse
`beta_feedback`/`beta_telemetry` nguyên văn.

Không session/cookie, không `SECRET_KEY` — trạng thái hiển thị lại sau feedback
dùng Post-Redirect-Get qua query `run_id`, tra registry in-process. Registry
chỉ sống trong vòng đời process (mất khi restart server) — chấp nhận được
cho Beta V1 single-user local; Owner chạy lại là xong, không phải blocker.

`app/web/launcher.py`: bind qua `werkzeug.serving.make_server(...)` (không
`app.run(debug=...)`) — bind đồng bộ, raise `OSError` nếu cổng bận (không
race, không cần `socket` module riêng), và bản thân `make_server` không kèm
Werkzeug debugger/reloader nên "debug off" là bất biến cấu trúc, không chỉ
một cờ có thể quên. `Open Reports Web.command` kiểm tra `flask` đã cài chưa
trước khi chạy, báo lỗi actionable nếu chưa (không traceback).

## Conflict Đã Phát Hiện Và Sửa Cục Bộ

`app/web/launcher.py` bản đầu dùng `import socket` để pre-check cổng — vi
phạm bất biến kiến trúc có sẵn (`tests/test_105e_price_composition.py`,
`tests/test_post_cutover_validation.py`, `tests/test_tracking_contract_client.py`
— `test_no_module_under_app_reaches_the_network`, ADR-101 boundary): không
module nào dưới `app/` được import trực tiếp `socket`/`http`/`requests`/...,
Tracking access phải qua `tools/tracking/`. Đây là **LOCAL + CLEAR + DIRECT
S070 BLOCKER** (regression 3 test) — sửa ngay trong phiên theo Repair
Policy: thay pre-check `socket` bằng bind trực tiếp qua
`werkzeug.serving.make_server` + bắt `OSError`, loại bỏ hoàn toàn `import
socket`. Regression sau sửa: PASS lại đủ 3 test, không hạ thấp bất biến
gốc — port-check giờ chính xác hơn (không còn race check-rồi-bind) thay vì
chỉ né tránh regex.

## Files Mới / Thay Đổi

Mới:
- `app/web/__init__.py`
- `app/web/server.py`
- `app/web/launcher.py`
- `app/web/templates/index.html`
- `Open Reports Web.command`
- `tests/test_web_server.py` (30 test: upload safety, trust boundary,
  privacy response, feedback/telemetry reuse, equivalence field-level)
- `tests/test_web_launcher.py` (4 test: bind, debug-off, reuse cổng bận)

Thay đổi:
- `pyproject.toml` — thêm `[project.optional-dependencies].web = ["Flask>=3.0"]`.

Không đổi: `app/demo.py`, `app/owner_usability.py`, `app/beta_feedback.py`,
`app/beta_telemetry.py`, `app/beta_presentation.py`, mọi module pricing/
identity/export, `app/owner_launcher.py` (Tkinter giữ nguyên, vẫn accepted
reference/fallback).

Production LOC thay đổi ước tính: ~260 dòng (`server.py` + `launcher.py` +
template + `.command`) — dưới ngưỡng ~300 LOC cảnh báo của Change Budget.

## Real Cohort — Web = Local

Cùng workbook (`So_chi_tiet_ban_hang (6).xlsx`), cùng capture evidence local
(copy nguyên từ checkout chính vào worktree S070 — không sửa evidence để ép
PASS), cùng canonical code:

**LOCAL** (`run_owner_report` gọi trực tiếp, không qua web):
```
ORDERS=58  LINES=83  AUTO=22  REVIEW=36
BUSINESS_SEVERITY=3  ACCOUNTING=100%  ACCOUNTED=58 (DROPPED=0)
REASON_COUNTS: IDENTITY_UNRESOLVED=31, Missing.PurchasePrice=44,
  Pending.accounting_purchase_price=44, Pending.accounting_profit=44,
  Pending.eligible_kpi_profit=44, Suspicious=3, TRACKING_HISTORY_PENDING=13
```

**WEB** (server thật trên `127.0.0.1:8765`, upload qua `curl -F`, cùng
workbook, cùng capture evidence — không mock):
```
GET /              → 200, "Có capture hợp lệ trên máy"
POST /run (fake.txt, .txt) → 400, "Chỉ chấp nhận file .xlsx."
GET /artifact/does-not-exist → 404
POST /run (workbook thật)    → 302 Location=/?run_id=report-20260901T085919Z
GET /?run_id=...  → 200: Tổng đơn 58, AUTO 22, Cần xem lại 36,
                    Ưu tiên xem ngay 3, Accounting coverage 100%
                    Review reasons: 44/44/44/44/31/13/3 — khớp tuyệt đối LOCAL
GET /artifact/report-20260901T085919Z → 200, xlsx, SHA256 khớp tuyệt đối
                    file trên đĩa outputs/reports/ (byte-for-byte)
POST /feedback     → 302 feedback=ok; feedback.jsonl có đúng 1 dòng mới,
                    schema {feedback_id, timestamp, run_id, category, comment}
runs.jsonl         → đúng 1 dòng telemetry cho run_id này (không duplicate),
                    order_count=58, auto_orders=22, review_orders=36,
                    error_count=3, accounting_rate=1.0
Response body      → grep không thấy TRACKING_REPORT_API_KEY, content_hash,
                    captured_by, source_system_ref, đường dẫn tuyệt đối
                    /Users/... hay outputs/reports/... nào
Server log         → không traceback, không exception
```

**EQUIVALENCE_RESULT = PASS.** Orders/lines/AUTO/Review/Accounting/business
severity/Review reason counts khớp tuyệt đối giữa LOCAL và WEB, cùng một lần
chạy dữ liệu thật, không phải hai lần chạy riêng biệt có thể trôi giá.

## Regression

`1403 passed, 11 skipped` (baseline trước S070: `1373 passed, 11 skipped`;
+30 test mới cho `app/web/*` — không skip nào đổi, không test cũ nào đổi
hành vi). Ba test kiến trúc (`test_no_module_under_app_reaches_the_network`
×3) từng FAIL tạm thời trong lúc implement do `import socket`; đã sửa cục
bộ (xem "Conflict Đã Phát Hiện Và Sửa Cục Bộ"), PASS lại đủ ở lần chạy cuối.

## Giới Hạn Đã Biết — KHÔNG Che Giấu

- Run/artifact registry sống trong process: restart server mất mapping
  `run_id → path` (Owner chạy lại là có report mới, không mất dữ liệu đã
  xuất — file `.xlsx` cũ vẫn còn trên đĩa, chỉ không tải lại qua UI được
  nữa). Không phải blocker Beta V1 single-user local.
- `Open Reports Web.command` dùng `python3` hệ thống (cùng convention
  `Open Reports.command`); Owner cần cài thêm `flask` một lần
  (`python3 -m pip install flask`) — launcher báo lỗi actionable nếu thiếu,
  không traceback.
- Toàn bộ Known Deferred Findings từ S068/S069 (A1 Product Identity
  Discovery Gap, temporal safety net cho `inv.map`/`alias.map`/`board`, 13
  sản phẩm Pending thật) giữ nguyên DEFERRED — S070 không chạm.

## Git Safety

Commit chỉ các file tracked thuộc S070 (`app/web/`, `Open Reports
Web.command`, `pyproject.toml`, `tests/test_web_server.py`,
`tests/test_web_launcher.py`, tài liệu session/progress). KHÔNG commit:
`data/captures/`, `data/tracking_catalog/`, `data/tracking_inv_map/`,
`data/tracking_price_history/` (runtime evidence, copy thủ công từ checkout
chính để chạy real cohort — cố ý không track), `data/uploads/`,
`data/beta_feedback/`, `outputs/reports/*.xlsx`, `data/product_identity/
mappings.jsonl.lock` (lock file byproduct khi chạy pipeline).

## Independent Review (cùng ngày, sau implementation SHA `026c7db`)

Review độc lập không tin `S070_GATE_RESULT=PASS` của phiên implementation —
tự verify lại bằng git (`fad7647..026c7db` đúng 1 commit, đúng diffstat khai
báo), đọc lại toàn bộ `app/web/server.py` + `launcher.py` + template, chạy
lại `1403 passed, 11 skipped` bằng `python3.11` thật (không phải giả định từ
báo cáo), và chạy server thật trên `127.0.0.1:8765` qua đúng đường
`python3.11 -m app.web.launcher` (launcher thật, không chỉ `test_client`).

### Finding — LOCAL + CLEAR + DIRECT S070 BLOCKER

`app/web/launcher.py` gọi `werkzeug.serving.make_server(HOST, PORT, app)`
KHÔNG truyền `threaded=True`. Mặc định này dựng `BaseWSGIServer`
single-threaded (đã xác nhận bằng `inspect.signature(make_server)`:
`threaded: bool = False`). Verify bằng repro trực tiếp, không suy đoán từ
đọc code: mở một kết nối TCP thô gửi `GET / HTTP/1.1` kèm
`Connection: keep-alive`, giữ kết nối đó mở — trong lúc đó, một request độc
lập hoàn toàn khác (`curl --max-time 5 GET /`) timeout 100% (`http_code=000`)
cho tới khi kết nối đầu đóng. CPU của process ở 0% trong lúc treo (`sample`
xác nhận thread chính block ở `sock_recv_into` trên đúng connection cũ, không
phải đang tính toán) — đây là treo I/O thật, không phải xử lý chậm.

Vì `launcher.py` tự gọi `webbrowser.open(url)` ngay sau khi bind thành công,
tab trình duyệt launcher tự mở CHÍNH LÀ loại kết nối giữ server bị khoá này —
nghĩa là luồng sử dụng bình thường nhất (double-click → browser tự mở →
Owner dùng tiếp) có xác suất cao tự khoá server cho chính Owner: upload lần
hai, bấm refresh, tải Excel, hay gửi phản hồi từ CÙNG tab đó đều có thể treo
vô thời hạn cho tới khi tab đóng kết nối. Đây trực tiếp vi phạm mục tiêu cốt
lõi của S070 ("Owner quen dùng web") và mục 10/17/18 của đề bài review
(multi-run correctness, real smoke, visual experience) — không phải edge
case hiếm, mà là hệ quả gần như chắc chắn của chính flow launcher tạo ra.

### Repair

Thêm `threaded=True` vào lệnh `make_server(...)` trong `app/web/launcher.py`
— tham số chính thức của werkzeug cho đúng lớp vấn đề này, không đổi
`HOST`/`PORT`, không bật debugger/reloader (tham số `threaded` chỉ đổi model
I/O sang một thread/connection, không liên quan `use_debugger`/
`use_reloader` — "debug off" vẫn là bất biến cấu trúc như cũ). Rủi ro đánh
đổi duy nhất: `_RUNS` dict và việc tạo file qua
`owner_usability.default_output_path()` giờ có thể được gọi từ nhiều thread
cùng lúc thay vì tuần tự — chấp nhận được cho Beta single-user local (ghi
key mới vào dict là an toàn dưới GIL; đụng độ tên file chỉ xảy ra nếu hai
request thật sự trùng giây tạo file, xác suất không đáng kể với một Owner
thao tác tay), không mở rộng thành thay đổi kiến trúc nào khác.

Thêm 1 test regression (`tests/test_web_launcher.py`,
`test_server_is_threaded_so_one_open_browser_connection_never_blocks_another_request`)
khẳng định `threaded=True` có mặt trong `launcher.main`, cộng với cập nhật
`fake_make_server` ở 2 test cũ để nhận `**kwargs` (trước đó ký hiệu 3 tham số
dương sẽ vỡ ngay khi `launcher.py` truyền thêm `threaded=True`).

### Regression + Re-verify sau repair

- `python3.11 -m pytest -q` toàn repo: `1404 passed, 11 skipped` (1403 cũ +
  1 test mới, không skip nào đổi).
- Repro treo chạy lại với server đã sửa: giữ đúng kết nối keep-alive như cũ,
  request độc lập thứ hai trả `200` trong `0.018s` (trước đó timeout 100%).
- Rerun toàn bộ battery upload adversarial trên server thật (không phải
  `test_client`): path traversal filename, `.xlsx.exe`, filename rỗng,
  `.xlsx` 0 byte, bytes hỏng nhưng đuôi `.xlsx`, file thật >25MiB
  (`27_000_000` byte, đúng dùng `Content-Length` thật chứ không chunked) —
  tất cả fail-safe (`400`/`413`), không traceback, `data/uploads/` rỗng sau
  mỗi lần (kể cả khi request lỗi).
- 2 run liên tiếp qua server thật (cùng workbook thật, cách nhau ~1.2s):
  2 `run_id` khác nhau, download đúng artifact của đúng run (SHA256 khớp
  byte-for-byte file trên đĩa cho cả hai), `runs.jsonl` đúng 1 dòng/run (kể
  cả sau nhiều lần `GET /?run_id=...` refresh — không duplicate), 2 lần gửi
  `POST /feedback` cho 2 run khác nhau → `feedback.jsonl` đúng 2 dòng, đúng
  `run_id` tương ứng, field đúng schema (`feedback_id, timestamp, run_id,
  category, comment`) — không tự đính kèm business data.
- Xoá thẳng artifact `.xlsx` khỏi đĩa sau khi đã đăng ký `run_id` rồi tải lại
  → `404` fail-safe, không traceback (`path.is_file()` check hoạt động đúng
  như thiết kế).
- Equivalence độc lập: gọi trực tiếp `run_owner_report()` (không qua web)
  trên cùng workbook thật + cùng capture evidence, so với kết quả WEB ở trên
  — khớp tuyệt đối: `ORDERS=58, LINES=83, AUTO=22, REVIEW=36,
  ACCOUNTING=100%, BUSINESS_SEVERITY=3, DROPPED=0`, cùng
  `review_reason_counts` (`IDENTITY_UNRESOLVED=31,
  Missing.PurchasePrice=44, Pending.accounting_purchase_price=44,
  Pending.accounting_profit=44, Pending.eligible_kpi_profit=44,
  Suspicious=3, TRACKING_HISTORY_PENDING=13`) — khớp đúng REAL COHORT kỳ
  vọng của đề bài review.
- Response privacy re-check trên trang kết quả thật (không chỉ
  `test_client`): grep không thấy `TRACKING_REPORT_API_KEY`, `content_hash`,
  `captured_by`, `source_system_ref`, `inv_map`, `alias.map`, `board.json`,
  `purchase_price_baseline`, đường dẫn `/Users/...` hay `outputs/reports/...`
  nào trong response.
- Visual runtime evidence: render thật qua Browser pane (không chỉ suy từ
  HTML string) — trang hiển thị đúng nhãn tiếng Việt, đủ nút hành động (CHẠY
  BÁO CÁO / TẢI BÁO CÁO EXCEL / GỬI PHẢN HỒI), không lộ thông tin kỹ thuật.
- Toàn bộ dữ liệu runtime dùng để test (captures copy thủ công,
  `data/uploads/`, `data/beta_feedback/`, `outputs/reports/*.xlsx`,
  `data/product_identity/mappings.jsonl.lock`) đã dọn sạch khỏi worktree sau
  review — `git status` chỉ còn đúng 2 file sửa
  (`app/web/launcher.py`, `tests/test_web_launcher.py`).

### Giới hạn đã biết — không đổi so với implementation

Registry `run_id → path` vẫn process-local (DEFERRED, không phải blocker);
`Open Reports Web.command` vẫn dùng `python3` hệ thống theo đúng convention
đã accepted của `Open Reports.command` (Tkinter) — không phải rủi ro mới do
S070 tạo ra, ngoài phạm vi Change Budget của review này.

**S070_INDEPENDENT_REVIEW = PASS (sau 1 repair).**
