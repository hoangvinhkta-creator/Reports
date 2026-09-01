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
