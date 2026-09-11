# S153 — `R7`: liên hệ dòng SAME · biểu đồ container lịch + dự phóng · số đơn lấp lỗ hổng

Ngày: 2026-09-11
Nhánh: `claude/reports-category-brand-display-gkpp9b` (dựng lại từ nhánh mặc
định `claude/extract-upload-repo-gq2ws4` @ `a224e6f` sau khi PR #16 đã merge).
Task: `R7` — `docs/tasks/R7-lien-he-bieu-do-container-so-don.md`
Task Mode: MAJOR
Project Profile: PRODUCT
Status: DONE (code + test + governance); `CHECK-R7-13` chờ Owner.

## 1. Đầu vào của Owner

Ba sổ thô (`Sổ chi tiết bán hàng` 2025; 2026 01/01 → 31/08; tháng 9/2026
xuất tới 20/09 — bản đang nạp) và ảnh chụp tab Nhân viên 01–05/09/2026.
Không dữ liệu cá nhân nào từ ba sổ được ghi vào repo; xem
`data/chart_gapfill/PROVENANCE.md` → "Nguồn số đơn".

## 2. Điều tra

```text
Khách hàng/SĐT `—`     sổ tháng 9 CÓ đủ ở BH73884/73914/73700/73922/73923
                       (609 dòng, 0 dòng trống tên) ⟹ lỗi Reports: dòng SAME
                       giữ version cũ, ba cột liên hệ ngoài fingerprint.
Giá MIN `—` trước 07/09 Tracking chụp MIN ngày từ R1 (2026-09-07); ngày không
                       có bản ngày ⟹ SOURCE_UNAVAILABLE ⟹ `—`, đúng thiết kế
                       R1 (không dự phòng). KHÔNG sửa code; Owner chọn hướng
                       (DEC-222 §4).
```

## 3. Sửa

Xem task file §1–§2. Tóm tắt: `_refresh_contact_fields` (§A);
`container_slots`/`project()`/`count_series` + dòng dự phóng ở hai template
(§C/§D); `extract_daily_orders.py` → `daily_orders.jsonl` 579 ngày, 29.883 đơn.

## 4. Test cũ đổi nghĩa (không nới lỏng)

- `test_r5_two_window_chart.py`: cửa sổ 31/13/12/4/5 mốc ⟹ container
  30/14/12/4/5 (neo 30/09/2026); scope Tháng "01/2026 → 12/2026".
- `test_r6_repair1_chart_windows.py`: helper `window_spans` dựng từ
  `container_slots`; cận trên cửa sổ hiện tại là mốc neo.
- `test_dec216_chart_gapfill.py`: "biểu đồ Số đơn KHÔNG đọc nguồn lấp" ⟹
  "đọc nguồn lấp RIÊNG của nó".
- `test_snapshot_repository.py`: thêm `order_line_source_version` vào tập
  bảng được UPDATE, kèm bài canh AST hẹp cho ba cột.
- `tests/conftest.py`: cắt cả nguồn số đơn khỏi workspace tổng hợp.

## 5. Bằng chứng

```text
tests/test_r7_lam_moi_lien_he_dong_same.py        4 passed
tests/test_r7_bieu_do_container_du_phong.py       10 passed
Bộ biểu đồ (R5/R6/DEC-216/DEC-185/…)              249 passed
Full pytest (trừ 2 suite trình duyệt)             3658 passed / 23 skipped / 0 failed (nền S152: 3640 / 23 / 0; +18 bài mới, không bài nào bị xoá)
Validators governance                             structure/project_state/evidence/task_completion PASS; reference_integrity 4 finding — đúng 4 baseline cũ
git diff --check                                  sạch
```

## 6. Rủi ro / vướng mắc

- `CHECK-R7-13` chỉ Owner đóng sau deploy.
- §A chỉ có hiệu lực ở LẦN NẠP SỔ KẾ TIẾP (làm mới xảy ra lúc nạp); không
  có backfill cho dữ liệu đang nằm trong DB.
- Giá MIN trước 07/09: chờ Owner chọn (DEC-222 §4).
- Không xác nhận được deploy Render trong phiên.

## 7. Session tiếp theo được khuyến nghị

Owner nạp lại sổ tháng 9 (bản mới nhất) rồi mở tab Nhân viên: 5 đơn đầu
tháng phải có tên/SĐT. Mở trang Báo cáo mức Ngày: trục 01 → 30/09, đường năm
trước từ nguồn lấp (2025), dòng dự phóng dưới legend. Quyết định hướng cho
giá MIN trước 07/09.
