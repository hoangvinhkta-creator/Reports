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
