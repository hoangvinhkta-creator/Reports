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

COPY pyproject.toml alembic.ini ./
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

# TASK-PRA-001: nâng schema history TRƯỚC khi mở cổng. `alembic upgrade head`
# thất bại → container không start (fail closed): thà không deploy còn hơn
# chạy lên với schema cũ/chưa có rồi hiển thị lịch sử rỗng như thể chưa ai
# nhập gì. Migration idempotent nên chạy lại ở mỗi lần deploy là an toàn.
#
# `--timeout 300` (R1, trước là 120): một lượt `/run` giờ gọi Tracking ĐỒNG
# BỘ nhiều lượt trước khi trả lời — purchase_price_history, catalog, inv_map
# (mỗi lượt tự timeout ở 60s, `tools/tracking/capture_purchase_price_
# history.py`), RỒI daily-min theo từng đoạn ≤ 62 ngày (mỗi lượt tự timeout
# ở 120s, `tools/tracking/capture_daily_min.py`). Ba lượt đầu chạy TUẦN TỰ,
# không song song (`tools/tracking/live_pull.py::_pull`), nên riêng chúng đã
# cộng dồn tới 180s ở kịch bản xấu — VƯỢT timeout 120s cũ của chính gunicorn.
# Khi đó gunicorn SIGKILL worker giữa chừng: trình duyệt nhận một kết nối bị
# ngắt đột ngột, không phải một lỗi HTTP tử tế — và JS phía client (app.js)
# đọc đó là lỗi mạng rồi tự gửi lại request thật lần hai (đã chặn cho riêng
# form upload bằng `data-no-ajax`, xem app/web/templates/index.html, nhưng
# gunicorn timeout quá ngắn vẫn là vấn đề gốc cần sửa ở đây). 300s đủ dư cho
# 180s legacy + một cửa sổ daily-min timeout hết 120s + biên độ xử lý pipeline
# thật (vài giây tới vài chục giây), mà không giữ một worker (trong tổng 2
# worker × 4 luồng) treo quá lâu nếu Tracking thật sự hỏng hẳn.
CMD ["sh", "-c", "alembic upgrade head && gunicorn --workers 2 --threads 4 --bind 0.0.0.0:${PORT} --timeout 300 app.web.wsgi:application"]
