# S156 — Banner Tracking đỏ và sổ 01–03/09 không có giá MIN: xác minh từ code, sửa để hệ thống tự nói lý do

Ngày: 2026-09-11
Nhánh: `claude/reports-category-brand-display-gkpp9b` (nối tiếp `S155`, đã
đồng bộ với nhánh mặc định `claude/extract-upload-repo-gq2ws4` @ `a67e2ec`).
Task Mode: MICRO (khả năng chẩn đoán; không đổi luật giá, không đổi hợp đồng).
Project Profile: PRODUCT
Status: DONE

## 1. Yêu cầu

Owner gửi ba ảnh + một sổ (139 dòng, 01 và 03/09): (1) tải sổ lên gặp
banner "Không lấy được dữ liệu Tracking trực tiếp (nguồn: daily_min)" rồi
"(nguồn: catalog)"; (2) sổ nhẹ 01–03/09 chạy xong nhưng mọi dòng Tracking
đều `—` ở Giá nhập. Yêu cầu: "kiểm tra vấn đề thực sự ở đâu thay vì đoán".

## 2. Kết luận — chỉ những gì đọc được từ code và từ file

Chi tiết + trích dẫn: `PROJECT/PROJECT_DECISIONS.md` → `DEC-226` §1.

```text
Banner          giấu lý do: chỉ có tên node; exc.reason không vào banner,
                không vào reports.timing, không print. HTTPError của urllib
                vứt thân {"ok":false,"ly":...} của Tracking ⟹ 409 cron /
                403 WAF / timeout để lại cùng một dấu vết. Lý do của hai
                lần trong ảnh KHÔNG truy lại được — hệ thống chưa từng ghi.
Sổ 01–03/09     hợp đồng trả SOURCE_UNAVAILABLE cho mọi mã ở ngày không có
                bản ngày; bản ngày cron chỉ có từ 07/09 (R1). Cách duy nhất
                cho 01–06/09 là POST /api/min-ngay/dung-lai (admin, Bearer
                token, KHÔNG có nút trên giao diện) — "Việc của Owner" theo
                khối S154, chưa có bằng chứng đã gọi. File Owner gửi: 104
                đơn, chỉ 2026-09-01 và 2026-09-03, không ngày nào ≥ 07/09.
Màn hình        SOURCE_UNAVAILABLE và NO_DATA cùng hiện một nhãn
                "Chưa có giá nhập cho đúng ngày bán" — không phân biệt
                được "đi gọi dựng lại" với "tra mã".
Không xác minh  dựng lại đã gọi chưa; lý do hai banner cụ thể (đã mất);
được từ đây     Tracking main sau PR #31 đã deploy chưa.
```

## 3. File đã thay đổi

Modified:
- `tools/tracking/capture_purchase_price_history.py` — `mo_ta_loi_http()`,
  `TRAN_THAN_LOI`; `_http_fetcher` dùng nó cho `HTTPError`.
- `tools/tracking/capture_daily_min.py` — `_http_poster` dùng `mo_ta_loi_http()`.
- `tools/tracking/live_pull.py` — `tom_tat_tra_loi()`; bốn khoá bằng chứng
  mới `daily_min_records` / `daily_min_errors` / `daily_min_error_reasons` /
  `daily_min_unobserved_dates`.
- `app/web/server.py` — `_log_tracking_pull()`, `_log_tracking_failed()`,
  `_mot_dong_log()`; banner 503 mang lý do sau tên node.
- `tests/test_tracking_contract_client.py` (+3), `tests/test_daily_min_orchestration.py`
  (+1), `tests/test_web_server.py` (+1, và bài cũ về banner siết thêm).
- `PROJECT/PROJECT_DECISIONS.md` — `DEC-226`; `PROJECT/PROJECT_PROGRESS.md`
  — khối canonical mới.

Created:
- `docs/sessions/S156-chan-doan-tracking-khong-doan.md` (file này)

## 4. Bằng chứng

```text
Bài kiểm mới (6) trên bản TRƯỚC sửa   7 failed (kể cả bài cũ được siết)
Sau sửa, ba file kiểm liên quan        pass toàn bộ
Full pytest                            3665 passed, 23 skipped, 4 deselected in 205.28s (0:03:25)
5 validator governance                 4 PASS; reference_integrity đúng 4
                                       baseline TASK-REM-T06/S136 (S155 §6)
git diff --check                       sạch
```

## 5. Quyết định chính

`DEC-226` — không đoán lý do; sửa để lý do tự đi ra ba nơi (banner, dòng
`reports.tracking_failed`, bằng chứng + dòng `reports.tracking_pull`).
Không thêm thử lại tự động.

## 6. Rủi ro / vướng mắc

Thấp. Thân phản hồi lỗi được đọc có trần và không mang header. Dòng log
mới đi qua `_mot_dong_log()` (không xuống dòng, không nháy kép, có trần).

## 7. Việc của Owner (bắt buộc để sổ 01–03/09 có giá)

Xem `DEC-226` §5: gọi `POST /api/min-ngay/dung-lai` từ Console của app
Tracking (đoạn mã có sẵn ở đó), chạy lại sổ, đọc dòng `reports.tracking_pull`.
