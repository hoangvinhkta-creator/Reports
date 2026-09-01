# Reports Web Shared Online Beta (S071) — container tối thiểu.
#
# Đóng gói ĐÚNG Python Reports Core hiện có (app/, tools/, config/) + tầng
# web mỏng (app/web/) chạy qua gunicorn. Không rewrite sang JavaScript, không
# microservice — một process Python duy nhất, nhiều worker/thread.
#
# Yêu cầu khi chạy container này trong production:
#   - Volume persistent mount vào /app/data VÀ /app/outputs (registry SQLite
#     + artifact .xlsx phải sống qua restart/redeploy — S071 §14).
#   - Biến môi trường TRACKING_REPORT_SOURCE_URL + TRACKING_REPORT_API_KEY
#     (pull-on-run Tracking, S071 §2/§3/§7) — thiếu thì server vẫn chạy được
#     nhưng dùng local capture path thay vì live pull.
#   - PORT (mặc định 8080) — khớp cổng mà front door (Cloudflare) trỏ vào.

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
