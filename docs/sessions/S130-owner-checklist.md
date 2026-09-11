# Checklist nghiệm thu R3 cho Owner

Trạng thái tại thời điểm bàn giao: **code đã lên nhánh production trên
GitHub** (`claude/extract-upload-repo-gq2ws4` @ `30d2519`). **Chưa xác nhận
được đã lên Render/production thật** — phiên này không có quyền truy cập
Render/Cloudflare. Chi tiết đầy đủ: `docs/sessions/S130-r3-integration-and-deployment-attempt.md`.

## Việc cần Owner làm, THEO ĐÚNG THỨ TỰ

### 1. Kiểm tra trạng thái deploy hiện tại (làm trước tiên)
- [ ] Mở Render dashboard → service `reports-web` → tab **Events**/**Deploys**.
- [ ] Có build nào bắt đầu quanh lúc merge PR #8 (2026-09-08, giờ UTC ~09:1x)
      không?
- [ ] Nếu CÓ: mở **Logs** của deploy đó, tìm dòng `alembic upgrade head` —
      chạy thành công (không traceback) hay lỗi?

### 2. Sao lưu database (bắt buộc, TRƯỚC khi tự tay deploy nếu chưa tự deploy)
- [ ] Render → Postgres `tinphat-reports-db` → tab **Backups**.
- [ ] Có bản snapshot gần đây (trước thời điểm merge) không? Nếu automated
      backup đã bật → đủ dùng làm mốc rollback, không cần làm gì thêm.
- [ ] Nếu KHÔNG chắc → bấm **Manual Backup** ngay, trước khi làm bước 3.

### 3. Nếu chưa tự deploy — deploy thủ công
- [ ] Render → `reports-web` → **Manual Deploy** → chọn commit mới nhất
      (`30d2519` hoặc mới hơn trên `claude/extract-upload-repo-gq2ws4`).
- [ ] Theo dõi Logs: `alembic upgrade head` phải chạy XONG trước khi thấy
      dòng gunicorn khởi động worker.
- [ ] Xác nhận trong Logs không có `FAILED`/traceback từ alembic.

### 4. Smoke test (bấm thử trên production thật)
- [ ] Mở trang chủ (health check) — tải được, không lỗi 500.
- [ ] Mở `/kinh-doanh` (trang Báo cáo).
- [ ] Upload thử một workbook `.xlsx` qua nút Chạy báo cáo.
- [ ] Xem kỳ, chọn một nhân viên, mở các hàng đợi mới:
      `?loc=gan-dong`, `?loc=loai-chua-ro`, `?loc=gia-theo-chinh-sach`.
- [ ] Tải file Excel (`Tải Excel`) — mở được, có đúng MỘT cột "Giá nhập KPI",
      ô trống (không phải số 0) ở dòng chưa có giá.
- [ ] Chọn MỘT kỳ thử (không phải kỳ có số liệu quan trọng) → bấm **Chốt
      kỳ**.
- [ ] Thử sửa một giá nhập của kỳ vừa chốt → phải bị TỪ CHỐI (báo lỗi, không
      lưu được).
- [ ] Bấm **Mở lại kỳ**, gõ một lý do → sửa lại giá nhập → lần này phải LƯU
      ĐƯỢC.
- [ ] Nếu tiện: kích hoạt một lần restart service (Render → Manual Deploy
      lại, hoặc đợi lần deploy tự nhiên tiếp theo) → mở lại đúng kỳ vừa chốt/
      giá vừa sửa → xác nhận VẪN CÒN (không mất khi restart).
- [ ] Xem Render Logs vài phút đầu sau deploy — không có `schema mismatch`,
      không có chuỗi lỗi HTTP 500 lặp lại.

### 5. Nếu tất cả đạt
- [ ] Báo lại để đóng `CHECK-R3-20` (Owner nghiệm thu) — R3 khi đó mới đủ
      điều kiện chuyển `DONE`.

### 6. Nếu có bước nào KHÔNG đạt
- Migration lỗi ở bước 3 → container không khởi động, Render tự giữ bản
  deploy cũ đang chạy — dịch vụ KHÔNG gián đoạn. Báo lại nguyên văn dòng lỗi
  trong Logs, KHÔNG tự ý downgrade database.
- Smoke test lỗi ở bước 4 → Render → Deploys → chọn lại bản deploy TRƯỚC đó
  (không cần thao tác git). Báo lại bước nào lỗi và ảnh chụp/log nếu có.
