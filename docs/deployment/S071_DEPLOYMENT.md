# S071 — Triển khai Reports Web Shared Online Beta

Trạng thái tại thời điểm viết tài liệu này: **DEPLOYMENT_READY**, chưa
DEPLOYED. Môi trường Claude Cloud chạy session S071 không có credential của
bất kỳ nhà cung cấp hosting/DNS nào — không tự deploy được. Tài liệu này là
đúng "exact minimal deployment action" mà S071 §18 yêu cầu chuẩn bị sẵn.

## Kiến trúc đã chọn

Một Python process duy nhất (Flask qua gunicorn, `app/web/wsgi.py`), state
được tách khỏi process:

- **Registry cấu trúc** (`app/web/run_registry.py`): SQLite file, mount trên
  volume persistent.
- **Artifact** (`.xlsx` mỗi lần chạy): file trên cùng volume persistent
  (`outputs/reports/`).
- **Tracking**: pull-on-run LIVE (`tools/tracking/live_pull.py`) — không
  mirror database, không sync định kỳ.

Một node (không cluster, không Kubernetes) là đủ cho quy mô Beta (một đội
bán hàng nhỏ, không phải hàng nghìn người dùng đồng thời) — SQLite trên một
volume của một node xử lý được nhiều worker/nhiều viewer cùng lúc mà không
cần Postgres/Redis (S071 §8: ưu tiên giải pháp managed nhỏ nhất).

## Việc Owner cần làm (OWNER_ACTION_REQUIRED)

1. **Chọn nhà cung cấp compute + volume persistent nhỏ nhất còn lại sau khi
   cân nhắc.** `Dockerfile` ở root repo build ra image chạy được trên bất kỳ
   nền tảng nào hỗ trợ Docker + volume gắn kèm (Fly.io Machines + volume,
   Render Web Service + persistent disk, một VPS nhỏ chạy Docker, v.v.) —
   tài liệu này KHÔNG khoá cứng một nhà cung cấp cụ thể, vì session S071
   không có credential nào để xác nhận nhà cung cấp nào Owner đã có sẵn tài
   khoản.
2. Mount volume persistent vào **cả hai** `/app/data` và `/app/outputs`
   trong container (registry SQLite nằm dưới `data/web_runs/`, artifact nằm
   dưới `outputs/reports/`, upload tạm dưới `data/uploads/` — thư mục upload
   không bắt buộc phải persistent vì file bị xoá ngay sau mỗi lần chạy, xem
   S071 §10).
3. Đặt biến môi trường:
   - `TRACKING_REPORT_SOURCE_URL` — base URL hợp đồng Tracking Data Contract
     V1 (ví dụ `https://price.tinphatcrm.com`, KHÔNG có mặc định trong code).
   - `TRACKING_REPORT_API_KEY` — secret Tracking, đặt tại environment của
     nhà cung cấp hosting (Fly secrets / Render env / v.v.), KHÔNG BAO GIỜ
     paste vào chat, KHÔNG commit vào Git.
   - `PORT` — tuỳ nhà cung cấp (Dockerfile mặc định `8080`).
4. Trỏ DNS `reports.tinphatcrm.com` vào endpoint compute đã chọn (Cloudflare
   nếu Owner đã dùng Cloudflare cho domain — chỉ CNAME/A record, không cần
   Worker).
5. Bật **Cloudflare Access** (hoặc cơ chế private-access tương đương của nhà
   cung cấp đã chọn) trước `reports.tinphatcrm.com` — S071 §13 ưu tiên
   phương án này thay vì tự xây signup/password/OAuth. Không public
   anonymous.
6. Sau khi lên production lần đầu: xác nhận `TRACKING_REPORT_API_KEY` hợp lệ
   bằng cách thử chạy MỘT báo cáo thật qua web — nếu Tracking pull-on-run
   thất bại, trang sẽ báo lỗi rõ ràng (không silently dùng dữ liệu cũ), xem
   `app/web/server.py::_select_captures_for_run`.

## Việc KHÔNG cần Owner làm

- Không cần Owner Mac chạy bất kỳ thứ gì — production path hoàn toàn ở
  server (S071 mục tiêu chính: Owner Mac không nằm trên critical path).
- Không cần tự capture Tracking trước (`tools/tracking/capture_*.py` giữ
  nguyên cho luồng local/offline, KHÔNG dùng cho production web).
- Không cần build signup/login riêng — Cloudflare Access xử lý truy cập.

## Build & chạy container cục bộ (kiểm tra trước khi deploy thật)

```bash
docker build -t reports-web .
docker run --rm -p 8080:8080 \
  -v "$(pwd)/data:/app/data" \
  -v "$(pwd)/outputs:/app/outputs" \
  -e TRACKING_REPORT_SOURCE_URL="https://price.tinphatcrm.com" \
  -e TRACKING_REPORT_API_KEY="***" \
  reports-web
```

Không có `TRACKING_REPORT_API_KEY`/`TRACKING_REPORT_SOURCE_URL`: server vẫn
khởi động và phục vụ được — chỉ khác ở chỗ mỗi lần `/run` dùng lại đường local
capture cũ (S068–S070), đúng hành vi fallback đã document ở
`tools/tracking/live_pull.is_configured()`.

## Production acceptance checklist (sau khi Owner deploy thật — S071 §18)

- [ ] HTTPS hoạt động trên `reports.tinphatcrm.com`.
- [ ] Truy cập riêng tư qua Cloudflare Access (không vào được nếu chưa đăng
      nhập).
- [ ] Upload workbook → chạy → thấy kết quả.
- [ ] `/history` hiển thị lịch sử run.
- [ ] Download artifact đúng file của đúng run.
- [ ] Gửi feedback thành công.
- [ ] Viewer thứ hai (máy khác/trình duyệt khác) thấy ĐÚNG run mà Owner vừa
      tạo, không cần Owner làm gì thêm.
- [ ] Restart container (redeploy) → run cũ + artifact cũ vẫn còn.

Session S071 KHÔNG thể tự kiểm các mục trên vì không có môi trường production
thật — checklist này để Owner tick sau khi deploy.
