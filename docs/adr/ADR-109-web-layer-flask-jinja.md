# ADR-109 — Web layer canonical là Flask + Jinja (amendment cho ADR-101)

## Status
Accepted — Owner decision (DECISION A, S073, 2026-09-02; xem DEC-166).

## Date
2026-09-02

## Context

`docs/adr/ADR-101-architecture-and-stack.md` (2026-08-22) chốt stack dự
kiến: FastAPI + SQLAlchemy + Alembic ở backend, React + TypeScript + Vite ở
frontend. Từ S070 (Web Beta V1) và S071/S071B (Shared Online Beta, Render
stateless + R2), web layer thật của Reports là **Flask + Jinja**, server-
rendered, opt-in dependency `web`, chạy production qua gunicorn
(`app/web/wsgi.py`), đã Independent Review PASS, đã deploy và được Owner
chấp nhận. `TASK-PRA-000` ghi nhận `CONFLICT DETECTED` giữa ADR-101 và
implementation.

## Decision

1. **Web layer canonical = Flask + Jinja, server-rendered.** Không refactor
   sang FastAPI/React để khớp ADR-101. Không mở architecture migration task.
2. Phần **backend data** của ADR-101 (PostgreSQL môi trường dùng chung /
   SQLite dev-test, SQLAlchemy, Alembic) **không bị amendment này thay đổi**;
   việc có áp dụng cho history store hay không được quyết riêng ở
   `ADR-108`.
3. Ranh giới phân lớp của ADR-101 giữ nguyên: engine thuần dưới
   `app/modules/` không import web/DB/network; presentation không chứa
   business rule; driver mạng ở `tools/`.
4. Frontend là presentation layer: Jinja + CSS tĩnh (token thiết kế chép từ
   Tracking, không runtime dependency) + JavaScript tối thiểu không chứa
   business computation. Không đưa React/Vite vào khi chưa có nhu cầu UI
   mà Jinja không đáp ứng được — và nhu cầu đó phải được chứng minh bằng
   một vertical cụ thể, không phải bằng ADR cũ.

## Alternatives Considered

- Refactor sang FastAPI + React cho khớp ADR-101: bị loại — chi phí lớn,
  không có user-visible outcome, vi phạm nguyên tắc "không refactor toàn
  repo trước khi feature cần".
- Giữ ADR-101 nguyên văn và coi Flask là "tạm": bị loại — tài liệu canonical
  sẽ tiếp tục nói dối về production, và session sau có thể "sửa cho đúng".

## Rationale

Tài liệu canonical phải phản ánh production reality. Flask + Jinja đã đủ cho
mọi vertical trong roadmap PRA (bảng, bộ lọc, drill-down, form upload);
mọi tính toán nghiệp vụ nằm ở backend nên lựa chọn framework render không
ảnh hưởng độ đúng dữ liệu.

## Consequences

### Positive
- Một nguồn sự thật về stack; không còn xung đột docs ↔ code.
- Roadmap PRA xây trên web layer đã accepted, không chờ migration.

### Negative / Tradeoffs
- Tương tác phía client (lọc không reload, sparkline) phải làm bằng JS tối
  thiểu hoặc reload trang; chấp nhận cho Beta.

## Migration / Implementation Notes

- Amendment tài liệu tối thiểu: (a) ADR này; (b) thêm dòng "Superseded By:
  ADR-109 (một phần: web layer)" vào ADR-101, không viết lại nội dung lịch
  sử; (c) `PROJECT/PROJECT_DECISIONS.md` DEC-166 ghi Owner decision;
  (d) không sửa `CLAUDE.md`, không sửa governance core.

## Supersedes
ADR-101 — chỉ phần "Frontend: React + TypeScript + Vite" và "API routers
(FastAPI)". Các phần khác của ADR-101 giữ nguyên hiệu lực.

## Superseded By
None
