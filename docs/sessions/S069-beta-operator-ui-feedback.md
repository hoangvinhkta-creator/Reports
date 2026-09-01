# S069 — INTERNAL BETA OPERATOR UI + FEEDBACK

Ngày: 2026-09-01
Nhánh: `s069/beta-operator-ui`, baseline `3f92c953b4c6d12834d4d3a0c611a7b27e7e0061`
Task: đưa Internal Beta đã ACCEPTED (S068) vào một giao diện local Owner
dùng được trong công việc thực tế, và thu evidence sử dụng tối thiểu.

## Audit Owner UI Hiện Có Trước Khi Sửa

- `EXISTING_UI_CAPABILITIES`: `app/owner_launcher.py` — cửa sổ Tkinter cục bộ
  duy nhất, chọn workbook → gọi `run_owner_report` → hiện tóm tắt → hỏi mở
  file.
- `EXISTING_RUN_ENTRY_POINT`: `app.owner_usability.run_owner_report`, ủy
  quyền hoàn toàn cho `app.demo.run_demo` (Demo V1) — không tự tính lại gì.
- `EXISTING_FILE_PICKER`: `tkinter.filedialog.askopenfilename`, lọc `*.xlsx`.
- `EXISTING_RESULT_MODEL`: `ReportSummary` (`app/modules/exporting/
  excel_exporter.py`) — trước S069 chỉ có
  `input_orders/accounted_orders/total_lines/auto_orders/review_orders/
  review_lines`, KHÔNG có `error_count` hay review reason aggregate.
- `EXISTING_RESULT_SUMMARY`: launcher V1 dựng một message string từ
  `summary.input_orders/auto_orders/review_orders` — không có Review
  reasons, không có Lỗi.
- `EXISTING_REPORT_OUTPUT_PATH`: `owner_usability.default_output_path` —
  `outputs/reports/report-<UTC timestamp>.xlsx`, không ghi đè.
- `EXISTING_REPORT_OPEN`: `subprocess.run(["open", path])` sau một hộp thoại
  Yes/No, gọi trực tiếp trong lớp Tkinter (không tách adapter test được).
- `EXISTING_CAPTURE_ACQUISITION`: `owner_usability.select_latest_valid_captures`
  quét `data/captures/` + `data/tracking_price_history/` (lịch sử giá) và
  `data/tracking_catalog/` (catalog) — chọn COMPLETE mới nhất theo
  `captured_at`, KHÔNG bao giờ theo tên file/mtime. **PHÁT HIỆN QUAN
  TRỌNG**: launcher V1 KHÔNG chọn/nối `data/tracking_inv_map/` — nghĩa là
  luồng Owner thực tế chưa từng dùng authority `inv.map` mà S068 đã accepted
  (22 AUTO/36 Review); double-click `Open Reports.command` trước S069 sẽ ra
  lại đúng baseline CŨ trước inv.map (`AUTO=0`), không phải baseline đã
  duyệt. Đây là gap trực tiếp chặn Exit Criteria "AUTO/Review hiển thị
  đúng" — thuộc rule 2.A (ngăn Owner dùng đúng kết quả thật), nên sửa trong
  S069.
- `EXISTING_ERROR_HANDLING`: `OwnerUsabilityError` → message tiếng Việt an
  toàn (không payload); `Exception` khác → message chung, không traceback.
  Giữ nguyên nguyên trạng, chỉ tái dùng.

## Thay Đổi

1. **Nối `tracking_inv_map` vào Owner launcher** (`app/owner_usability.py`):
   thêm `INV_MAP_CAPTURE_DIRECTORIES`, tham số `required` cho
   `_latest_complete_capture` (capture tuỳ chọn trả `None` thay vì raise khi
   vắng mặt — đúng khuôn `demo.run_demo`'s "vắng mặt = chưa nối"),
   `SelectedCaptures.tracking_inv_map`, và forward vào `demo.run_demo`. Đây
   là wiring một tham số ĐÃ TỒN TẠI (S068, đã accepted) vào launcher, không
   phải business rule mới.
2. **`ReportSummary` mở rộng** (`app/modules/exporting/excel_exporter.py`):
   thêm `error_count` (đếm từ `result.review_queue.by_severity(SEVERITY_ERROR)`
   có sẵn) và `review_reason_counts` (đếm lại đúng các chuỗi reason
   authoritative đã tính cho Excel — không phân loại lại, không suy đoán
   thêm). Đây là aggregation thuần trên dữ liệu đã tính, đúng charter module
   ("trình bày kết quả đã tính; không tra giá hay tính lại nghiệp vụ").
3. **`app/owner_launcher.py`** mở rộng: data readiness label, Result summary
   đầy đủ (Tổng đơn/AUTO/Cần xem lại/Lỗi/Accounting coverage), Review
   summary (label hiển thị qua `app/beta_presentation.py`, reason gốc không
   đổi), nút "Mở báo cáo Excel" thường trực (`owner_usability.open_report_file`,
   tách để test được), nút "Gửi phản hồi" (dialog nhỏ).
4. **`app/beta_feedback.py`** (mới): schema cố định
   (`feedback_id/timestamp/run_id/category/comment`), category đóng (5 lựa
   chọn cố định, fail-safe nếu khác), append JSONL local, không mạng.
5. **`app/beta_telemetry.py`** (mới): schema cố định đọc DUY NHẤT từ
   `ReportSummary` (không đọc lại workbook), `git_sha` best-effort, append
   JSONL local.
6. **`app/beta_presentation.py`** (mới): nhãn hiển thị Review reason —
   thuần presentation, reason gốc giữ nguyên trong dữ liệu, chỉ đổi cách gọi
   tên khi hiển thị.
7. **`.gitignore`**: thêm `data/beta_feedback/` (đường dẫn S069 tạo ra).

## Real Beta Smoke — Trace Nguyên Nhân Lệch Số Ban Đầu

Lần chạy đầu qua launcher đã nối `tracking_inv_map` cho ra `AUTO=0/REVIEW=58`
thay vì `22/36` đã accepted, dù ORDERS/LINES/ACCOUNTING vẫn đúng 58/83/100%.
Trace: `data/captures/PPH-20260831T080038Z.json` (capture lịch sử giá cục bộ
duy nhất COMPLETE lúc đó) đã STALE so với capture thật đã dùng lúc S068
accept (`PPH-20260901T021755Z-s068.json`, không còn trên máy này). Đây là
**evidence đã thay đổi hợp lệ theo môi trường, không phải regression từ
S069**: giá nhà cung cấp đổi liên tục, dữ liệu Owner chưa refresh trong
phiên này. Dùng lại đúng cơ chế capture đã accepted (`tools/tracking/
capture_purchase_price_history.py`, `tools/tracking/capture_inv_map.py` —
không code mới, không kiến trúc mới), refresh cả hai capture (`inv_map`:
468 entries/18 Ignore — khớp evidence S068; `PPH`: capture mới
`PPH-20260901T080128Z.json`) → rerun ra đúng `58/22/36/100%`.

```text
ORDERS=58
LINES=83
AUTO_ORDERS=22
REVIEW_ORDERS=36
ERRORS=3 (Suspicious, SEVERITY_ERROR, phụ thuộc dữ liệu giá hôm nay — không
          nằm trong bốn số accepted S068, không phải blocker)
ACCOUNTING_RATE=100%
DROPPED=0
OUTPUT=outputs/reports/report-20260901T081206Z.xlsx (tồn tại, mở được)
TELEMETRY=data/beta_feedback/runs.jsonl (ghi thành công)
FEEDBACK=data/beta_feedback/feedback.jsonl (ghi thành công, marker [TEST])
```

## Regression

`1373 passed, 11 skipped` (baseline trước S069: `1349 passed, 11 skipped`;
+24 test mới cho inv_map wiring, open adapter, feedback, telemetry,
presentation — không skip nào đổi, không test cũ nào đổi hành vi).

## Giới Hạn Đã Biết — KHÔNG Che Giấu

`app/owner_launcher.py` dùng Tkinter thật; môi trường chạy test tự động của
phiên này (`python3.11` có `pytest`+`openpyxl` nhưng thiếu `_tkinter`, còn
Python hệ thống có Tkinter nhưng thiếu dependency dự án) không có một
interpreter nào có ĐỦ CẢ HAI. Vì vậy toàn bộ logic thuần (feedback,
telemetry, presentation, wiring capture, adapter mở file) đã được unit test
đầy đủ và độc lập với Tkinter; riêng phần widget-wiring trong
`owner_launcher.py` chỉ được xác minh bằng `py_compile` (cú pháp) và review
thủ công theo đúng API Tkinter/ttk đã dùng ở bản gốc đã accepted — KHÔNG
được xác nhận bằng một lần chạy GUI thật có màn hình. Đây là giới hạn môi
trường đã tồn tại từ trước S069 (bản gốc `owner_launcher.py` cũng chưa từng
có test), không phải việc S069 né tránh.

## Known Deferred Findings — Không Đổi

A1 Product Identity Discovery Gap, 13 sản phẩm Pending thật, 6 dòng
service/cost, PP coverage, AUTO rate target, fuzzy/substring mapping,
generic MDM, web frontend/backend — TẤT CẢ giữ nguyên DEFERRED, không chạm.

## Git Safety

Commit chỉ các file tracked thuộc S069 (liệt kê tường minh, không
`git add -A`/`git add .`). Không add `data/beta_feedback/`, `data/captures/`,
`data/tracking_catalog/`, `data/tracking_inv_map/`, `data/tracking_price_history/`,
`artifacts/`, workbook thật. Không merge canonical trong phiên này.

## Independent Review (phiên #2, 2026-09-01)

Review SHA gốc của implementation: `938a2a8e8b07632eacd2f633d7880e8b13e2bcb3`.
Không tin PASS của implementation session; tự xác minh lại từ Git, code,
test và runtime evidence trên đúng máy Owner sẽ dùng.

**Xác minh lại độc lập, khớp tuyệt đối:**
- Real cohort `/Users/hoangvinh/Downloads/So_chi_tiet_ban_hang (6).xlsx` chạy
  lại qua `run_owner_report` (không qua GUI) trên capture hiện có trên máy
  → `58 đơn / 83 dòng / 22 AUTO / 36 Review / Accounting 100% / Dropped 0 /
  ERRORS 3`, khớp tuyệt đối con số implementation báo và baseline S068 đã
  accept.
- `ERRORS = 3` xác nhận đúng là 3 finding `Suspicious`/`SEVERITY_ERROR`
  (đối chiếu `config/validation.yaml` + `app/modules/validation/rules.py`:
  severity là "nhãn thứ tự đọc", không phải cổng chặn) — không phải lỗi xử
  lý runtime. Regression độc lập: `1373 passed, 11 skipped`, khớp báo cáo.

**Data freshness (mục 3 brief) — trả lời bằng code, không suy luận:**
- A/B: double-click launcher KHÔNG tự lấy dữ liệu Tracking mới — chỉ gọi
  `select_latest_valid_captures()` quét `data/captures/`,
  `data/tracking_catalog/`, `data/tracking_inv_map/`,
  `data/tracking_price_history/` trên đĩa cục bộ. Không có lệnh HTTP/network
  nào trong `app/owner_usability.py`.
- C: nguồn cần freshness — PP history (có temporal validation thật,
  `TrackingPriceHistoryReader` so `captured_at`/interval với `sale_date`,
  fail-safe về Pending nếu capture không phủ ngày bán — CHECK độc lập tại
  `app/modules/pricing/tracking_history/reader.py`); `inv.map`/`alias.map`/
  `board`/catalog KHÔNG có temporal validation nào — đây là bảng khoá-giá
  trị tại một thời điểm, không có timestamp theo từng entry để so sánh.
- D: nhãn "Dữ liệu Tracking: Sẵn sàng" (bản implementation) CHỈ xác nhận có
  capture COMPLETE + schema hợp lệ trên đĩa — KHÔNG xác nhận capture đó đủ
  mới/đủ phủ ngày bán cho workbook Owner sắp chạy. Hai khái niệm khác nhau,
  đúng như brief cảnh báo. Label gây hiểu lầm — ĐÃ SỬA trong review này
  (xem "Repair" bên dưới).
- E: xác nhận bằng bằng chứng SỐNG, không phải suy luận: trong lúc review,
  một phiên GUI thật đã chạy launcher trên đúng SHA `938a2a8` (xác nhận qua
  `git_sha` trong `data/beta_feedback/runs.jsonl`), chọn một workbook cũ hơn
  (`So_chi_tiet_ban_hang (5).xlsx`) trong khi capture hiện tại vẫn "Sẵn
  sàng" — kết quả ra đúng `0 AUTO / 53 Review` (an toàn: vẫn 100% accounting,
  0 dropped, không AUTO sai) nhưng label không hề cảnh báo Owner trước khi
  chạy. Đây là bằng chứng thật, không phải kịch bản giả định.
- F: KHÔNG cần terminal cho luồng an toàn (fail-safe về Pending không cần
  Owner làm gì). Terminal/Python chỉ cần khi Owner muốn TĂNG AUTO rate bằng
  cách refresh capture — đây là tối ưu coverage, không phải blocker đúng
  sai. Ngoại lệ: xem finding `inv.map` staleness bên dưới.

**Finding mới — `inv.map` không có temporal safety net (không phải S069
regression):** audit riêng cho thấy `inv.map` (và `alias.map`/`board` —
cùng kiến trúc, đã được chấp nhận từ Owner Usability V1) là bảng khoá→giá
trị tại một thời điểm, không có timestamp theo từng entry. Nếu Tracking
SỬA một mapping đã có (không phải thêm mới) giữa hai lần capture, Reports
dùng capture cũ sẽ resolve theo giá trị CŨ và coi là AUTO — khác với PP
history (có temporal validation, luôn fail-safe về Pending khi stale).
Đây LÀ rủi ro "wrong AUTO", không chỉ "missed AUTO" — nhưng là đặc tính
kiến trúc kế thừa từ `alias.map`/`board` gốc, S068 chỉ mở rộng cùng mô
hình cho `inv.map`, và S069 không hề chạm resolver — S069 chỉ là session
ĐẦU TIÊN mà launcher thật sự dùng đường `inv.map` này (trước S069 launcher
V1 chưa từng nối). Không phải regression của S069. Không sửa trong review
này (sửa đòi hỏi thêm temporal/versioning cho `inv.map`, một thay đổi kiến
trúc/schema Tracking — bị cấm rõ ở mục 4 của brief). Ghi nhận
DEFERRED — xem entry mới trong `PROJECT/PROJECT_PROGRESS.md`.

**Repair — 3 sửa nhỏ, cục bộ, presentation-only, không đổi business
severity/logic:**
1. `app/owner_launcher.py`: nhãn kết quả `"Lỗi: {N}"` → `"Ưu tiên xem ngay:
   {N}"` — `error_count` là số finding `SEVERITY_ERROR` (nhãn thứ tự đọc
   theo `config/validation.yaml`, gồm cả `missing` field bắt buộc,
   `employee_mismatch`, `employee_mapping` invariant — không chỉ
   `Suspicious`), không phải processing failure; nhãn cũ "Lỗi" dễ khiến
   Owner hiểu nhầm app bị lỗi.
2. `app/owner_launcher.py`: nhãn readiness `"Sẵn sàng"` → `"Có capture hợp
   lệ trên máy"` — đúng những gì check thực sự xác nhận (tồn tại +
   schema), không ngụ ý đã kiểm freshness/temporal coverage.
3. `app/beta_presentation.py`: header `"Lý do cần xem lại:"` →
   `"Lý do cần xem lại (đếm theo dòng, một dòng có thể có nhiều lý do):"` —
   tránh Owner đọc nhầm tổng theo dòng (có thể > số đơn Review) thành tổng
   theo đơn.

Sau sửa: `py_compile` OK, launcher khởi động lại không lỗi (process sống,
đăng ký foreground app qua `lsappinfo`), `1373 passed, 11 skipped` không
đổi. Không sửa `error_count`/`review_reason_counts`/business severity nào.

**GUI runtime (mục 8 brief):** môi trường review không có quyền Screen
Recording/Accessibility (`screencapture`, `osascript System Events` đều bị
từ chối quyền) nên KHÔNG chụp được pixel màn hình hay tự động click.
EVIDENCE_MISSING cho phần click-through tự động. Bù lại có bằng chứng
mạnh hơn suy luận: launcher chạy thật trên đúng SHA `938a2a8` trong lúc
review (`lsappinfo` xác nhận process Python là foreground GUI app thật,
không crash); và một phiên sử dụng thật đã diễn ra sống trong lúc review
— `data/beta_feedback/runs.jsonl` có bản ghi `git_sha=938a2a8`, workbook
khác, output mới; `lsof` xác nhận Microsoft Excel đang mở ĐÚNG file report
vừa tạo (`report-20260901T082842Z.xlsx`), không phải artifact cũ. Điều
này xác nhận: window mở được, chọn file được, run hoạt động, "Mở báo cáo
Excel" mở đúng file vừa chạy. Nút "Gửi phản hồi" không có lượt dùng mới
trong phiên này để quan sát trực tiếp — dựa vào unit test +
`py_compile` + review thủ công (cùng giới hạn implementation session đã
nêu).

**Kết luận review:** S069 PASS với 3 repair truthfulness nhỏ đã áp dụng.
Finding `inv.map` staleness là DEFERRED, không blocker S069 (kế thừa từ
S068, không phải regression), cần Owner biết trước khi mở rộng thêm
authority tương tự trong tương lai.
