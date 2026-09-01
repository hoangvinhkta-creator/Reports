# Reports Web Shared Online Beta (S071) — container tối thiểu.
#
# Đóng gói ĐÚNG Python Reports Core hiện có (app/, tools/, config/) + tầng
# web mỏng (app/web/) chạy qua gunicorn. Không rewrite sang JavaScript, không
# microservice — một process Python duy nhất, nhiều worker/thread.
#
# Yêu cầu khi chạy container này trong production:
#   - Một volume persistent mount vào MỘT thư mục gốc (vd /app/persistent —
#     đúng cấu hình đã chọn trong render.yaml), cộng biến môi trường
#     REPORTS_DATA_ROOT trỏ vào đúng gốc đó. Registry SQLite VÀ artifact
#     .xlsx đều tự đặt dưới gốc này (app/web/server.py, app/web/
#     run_registry.py) — sống qua restart/redeploy (S071 §14). KHÔNG đặt
#     REPORTS_DATA_ROOT: container vẫn chạy được (test/dev), nhưng dùng
#     /app/data + /app/outputs bên trong container — MẤT khi container bị
#     thay thế, không phải lỗi, chỉ là "chưa gắn volume".
#   - Biến môi trường TRACKING_REPORT_SOURCE_URL + TRACKING_REPORT_API_KEY
#     (pull-on-run Tracking, S071 §2/§3/§7) — thiếu thì server vẫn chạy được
#     nhưng dùng local capture path thay vì live pull.
#   - PORT (mặc định 8080) — khớp cổng mà front door (Cloudflare) trỏ vào.
#
# Kiến trúc hosting cụ thể đã chọn: Render Web Service (Docker runtime) +
# một Disk — xem render.yaml (root) + docs/deployment/S071_DEPLOYMENT.md.
# Dockerfile này vẫn chạy được trên bất kỳ host nào hỗ trợ Docker + volume
# (không khoá cứng Render ở tầng image).

FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml ./
COPY app ./app
COPY tools ./tools
COPY config ./config

RUN pip install --no-cache-dir ".[web-prod]"

# Thư mục persistent — mount volume thật đè lên các thư mục này khi deploy.
RUN mkdir -p /app/data /app/outputs/reports

ENV PORT=8080
EXPOSE 8080

CMD ["sh", "-c", "gunicorn --workers 2 --threads 4 --bind 0.0.0.0:${PORT} --timeout 120 app.web.wsgi:application"]
