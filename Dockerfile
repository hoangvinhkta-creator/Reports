# Reports Web Shared Online Beta (S071, STATELESS từ S071B) — container
# tối thiểu.
#
# Đóng gói ĐÚNG Python Reports Core hiện có (app/, tools/, config/, data/) +
# tầng web mỏng (app/web/) chạy qua gunicorn. Không rewrite sang JavaScript,
# không microservice — một process Python duy nhất, nhiều worker/thread.
#
# `data/` (Render production regression, S071B follow-up): `app/
# composition.py::run_import_production()` — đường production DUY NHẤT của
# `app/demo.py::run_demo()`, cả CLI lẫn web — nạp KHÔNG ĐIỀU KIỆN vài nguồn
# "canonical committed" cố định dưới `data/` (`HISTORICAL_REGISTRY_PATH`,
# `CONFIRMED_ADJUSTMENTS_PATH`). Thiếu `COPY data` khiến
# `confirmed_adjustments.jsonl` VẮNG MẶT (khác "tồn tại nhưng rỗng") trong
# container — `ConfirmedAdjustmentSource` thành UNAVAILABLE (fail-closed,
# DEC-144 §3) cho MỌI dòng thay vì chỉ những dòng vốn đã Pending vì thiếu
# giá, kéo theo `eligible_kpi_profit = None` toàn bộ và AUTO = 0 dù đúng
# workbook đã accepted có 22 AUTO order (xem `tests/
# test_deployment_canonical_data_packaging.py`). Repo `.gitignore` đã loại
# mọi thư mục con runtime/PII thật của `data/` (`samples/`, `uploads/`,
# `exports/`, `beta_feedback/`, `web_runs/`, `tracking_live_tmp/`) nên
# `COPY data ./data` chỉ mang đúng 3 file nhỏ đã commit — không đổi
# S071B stateless (đây là input tĩnh đọc-only, không phải state runtime).
#
# S071B: KHÔNG cần volume persistent nào nữa. Registry run + artifact .xlsx
# sống trên Cloudflare R2 (app/web/storage_backend.py, tools/storage/
# r2_store.py) — container có thể bị thay thế/restart bất kỳ lúc nào, không
# mất dữ liệu, chạy được trên BẤT KỲ host stateless Python nào (không khoá
# cứng Render).
#
# Yêu cầu khi chạy container này trong production:
#   - `REPORTS_REQUIRE_R2=1` + đủ 4 biến `R2_ACCOUNT_ID`/`R2_BUCKET`/
#     `R2_ACCESS_KEY_ID`/`R2_SECRET_ACCESS_KEY` — thiếu thì server FAIL
#     configuration validation ngay lúc khởi động (fail closed, xem
#     app/web/storage_backend.py:build()), không âm thầm chạy bằng
#     SQLite/đĩa ephemeral bên trong container.
#   - Biến môi trường TRACKING_REPORT_SOURCE_URL + TRACKING_REPORT_API_KEY
#     (pull-on-run Tracking, S071 §2/§3/§7) — thiếu thì server vẫn chạy được
#     nhưng dùng local capture path thay vì live pull.
#   - PORT (mặc định 8080) — khớp cổng mà front door (Cloudflare) trỏ vào.
#
# `REPORTS_DATA_ROOT`/`REPORTS_REQUIRE_R2` KHÔNG đặt cùng lúc — nếu
# `REPORTS_REQUIRE_R2` vắng mặt VÀ R2_* chưa đủ, server rơi về SQLite/file
# cục bộ dưới `REPORTS_DATA_ROOT` (mặc định /app nếu biến đó cũng vắng mặt)
# — CHỈ dùng cho local dev/test/build thử, không phải đường production
# (không sống qua restart container).
#
# Kiến trúc hosting cụ thể đã chọn: Render Web Service (Docker runtime),
# không Disk — xem render.yaml (root) + docs/deployment/S071_DEPLOYMENT.md.

FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml ./
COPY app ./app
COPY tools ./tools
COPY config ./config
COPY data ./data

RUN pip install --no-cache-dir ".[web-prod]"

# mkdir -p không ghi đè data/ đã COPY ở trên — chỉ đảm bảo outputs/reports/
# (artifact tạm trước khi upload R2) có sẵn; data/uploads, data/
# tracking_live_tmp là scratch cho một lần chạy, tự mkdir lúc runtime
# (app/web/server.py, tools/tracking/live_pull.py), không cần tạo trước.
RUN mkdir -p /app/outputs/reports

ENV PORT=8080
EXPOSE 8080

CMD ["sh", "-c", "gunicorn --workers 2 --threads 4 --bind 0.0.0.0:${PORT} --timeout 120 app.web.wsgi:application"]
