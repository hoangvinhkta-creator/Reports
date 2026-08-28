# BÀN GIAO SESSION (SESSION HANDOFF)

Session ID:
S029

Task:
`TASK-105C` — Final Owner Decision (Q1/Q2) + Implementation Scope Lock
(`HistoricalVendorPriceProvider`)

Task Mode:
MAJOR (tạo canonical task spec + Scope Lock + Completion Gate — chưa
implementation)

Project Profile:
PRODUCT

Status:
**SEMANTIC_DEFINITION = COMPLETE. SCOPE_LOCK = COMPLETE. IMPLEMENTATION =
READY.** Không implementation trong phiên này. Không sửa repo Tracking.

## Metadata

Ngày:
2026-08-27

Repo A — Reports:
Bắt đầu `e8f4405998dd216bbed56ed03d9227431021b6cc`
Kết thúc: xem commit cuối phiên, cùng branch
`claude/reports-price-rtdb-audit-bg5y4t`

Repo B — hệ thống giá / RTDB:
`hoangvinhkta-creator/Tracking` @ `d177363a390d36fe793e0c1c44a6fb6743ca45f5`
(không đổi; **0 file thay đổi**)

## Kết Quả (Result)

Chủ dự án đóng dứt điểm hai câu hỏi filtering còn mở từ `DEC-151`:

```
Q1 — NCC retired/MIN_LOAI hồi tố: CLOSED. Trạng thái NCC HIỆN TẠI KHÔNG
     được áp ngược. Giá lịch sử hợp lệ tại D vẫn là candidate, bất kể
     NCC đó hôm nay ra sao.
Q2 — Outlier threshold hồi tố: CLOSED. NGUONG_BAT_THUONG hiện tại KHÔNG
     áp ngược. Phase 1 = MIN qua mọi candidate hợp lệ, không lọc gì thêm
     ngoài loại sentinel 0.
```

Trên nền quyết định đó, phiên này tạo
`docs/tasks/TASK-105C-historical-vendor-price-provider.md` — spec canonical
đầy đủ 24 mục theo yêu cầu, Scope Lock, và Completion Gate 20 check (A–T)
map trực tiếp từ đề bài.

**Phát hiện thiết kế quan trọng nhất của phiên:** đường dẫn
`Reports sale line (product_raw) → Tracking <MÃ> → phist` có một khoảng
trống **chưa đóng** — không có bảng mapping production đáng tin cậy nào
dịch được text tự do trên chứng từ bán hàng của Reports sang mã board của
Tracking. Đây là **dependency**, không phải việc `TASK-105C` tự phát minh
cách vá (cấm fuzzy matching, đúng `OD-105B-01` §B và tiền lệ `extractCode()`
đã thất bại bên Tracking, `DEC-147` §56). Provider vẫn **buildable và test
được đầy đủ** với `<MÃ>` tổng hợp; chỉ kết quả **không-Pending ở quy mô
lớn trên dữ liệu thật** phải chờ mapping đó.

**Quyết định kiến trúc của phiên (không phải Owner Decision, quyết định kỹ
thuật trong thẩm quyền viết Scope Lock):** `HistoricalVendorPriceProvider`
**compose** `FilePriceProvider` (đọc file snapshot do một script export
sinh ra), thay vì viết lại validation/parsing từ đầu. Nguồn mạng
(`tools/pricing/export_historical_vendor_prices.py`) tách hẳn khỏi
`app/modules/pricing/` (giữ đúng ranh giới `ADR-101`).

## Subtask Đã Hoàn Thành (Subtasks Completed)

- Ghi Owner Decision cuối cho Q1/Q2, cấp `DEC-152`.
- Tạo `docs/tasks/TASK-105C-historical-vendor-price-provider.md` — 24 mục
  đầy đủ theo yêu cầu đề bài.
- Scope Lock: Phạm Vi / Ngoài Phạm Vi / Phạm Vi Tác Động Dự Kiến.
- Completion Gate: 20 check (CHECK-105C-01…20, map A–T), Status
  `NOT_TESTED` (chưa implementation, đúng `EVIDENCE_STANDARD`).
- Xác định rõ dependency mapping sản phẩm — không tự vá bằng fuzzy
  matching.
- Cập nhật `PROJECT/PROJECT_PROGRESS.md`, `PROJECT/LO_TRINH_DE_HIEU.md`,
  `PROJECT/REVIEW_BUDGET_LEDGER.md`,
  `docs/tasks/TASK-108B-eligible-costs-owner-definition.md` (con trỏ
  ngắn tới file task mới).

## Subtask Còn Lại (Subtasks Remaining)

- Implementation thật của `TASK-105C` (phiên sau, theo đúng Scope Lock +
  Completion Gate đã frozen).
- Mở task mapping sản phẩm (`product_raw` ↔ `<MÃ>` Tracking) — chưa có ID,
  chưa mở trong phiên này.
- Sau `TASK-105C` DONE + mapping có lời giải: mở `TASK-108B`
  implementation.

## Tóm Tắt Completion Gate (Completion Gate Summary)

Completion Gate của CHÍNH PHIÊN NÀY (ghi quyết định + tạo spec, không phải
Completion Gate của `TASK-105C` — cái đó nằm trong file task, tất cả
`NOT_TESTED`):

Required:
Ghi Owner Decision Q1/Q2 đầy đủ; tạo spec canonical đủ 24 mục; Scope Lock
+ Completion Gate; không tự suy đoán mapping; cập nhật toàn bộ tiến độ.

PASS:
Đạt — xem file task, và trạng thái cuối phiên của
`PROJECT/PROJECT_PROGRESS.md`/`PROJECT/LO_TRINH_DE_HIEU.md`.

## File Đã Thay Đổi (Files Changed)

Created:
- `docs/tasks/TASK-105C-historical-vendor-price-provider.md`
- `docs/sessions/S029-task-105c-final-decision-scope-lock.md` (file này)

Modified:
- `PROJECT/PROJECT_DECISIONS.md` — `DEC-152`
- `PROJECT/PROJECT_PROGRESS.md` — đóng Q1/Q2, cập nhật
  `TASK-105C = SEMANTIC_DEFINITION COMPLETE / SCOPE_LOCK COMPLETE /
  IMPLEMENTATION READY`
- `PROJECT/LO_TRINH_DE_HIEU.md` — cập nhật bước 11b, đóng hai câu hỏi nhỏ
- `PROJECT/REVIEW_BUDGET_LEDGER.md` — ghi nhận Owner Decision cuối, không
  tiêu repair cycle
- `docs/tasks/TASK-108B-eligible-costs-owner-definition.md` — Phần XI (con
  trỏ ngắn, không lặp lại nội dung đã ở file task mới)

Deleted:
- (không)

Repo B (`Tracking`):
- **0 file**.

## Quyết Định Chính (Key Decisions)

- `DEC-152` — Owner Decision cuối: đóng Q1 (NCC retired/MIN_LOAI hồi tố) và
  Q2 (outlier threshold hồi tố); Scope Lock + Completion Gate cho
  `TASK-105C` được ghi nhận là FROZEN.

## Rủi Ro / Vướng Mắc (Risks / Blockers)

- **Blocker thật duy nhất còn lại trước khi có số không-Pending trên dữ
  liệu thật:** product identity mapping (`product_raw` ↔ `<MÃ>`). Không
  chặn việc bắt đầu implementation `TASK-105C` (provider test được bằng dữ
  liệu tổng hợp), nhưng chặn giá trị thực tiễn của nó cho tới khi có lời
  giải.
- Credential đọc RTDB Tracking (operational, chủ dự án cấp) — chưa có,
  không chặn việc viết code (test dùng fixture), chặn việc chạy
  `tools/pricing/export_historical_vendor_prices.py` thật.
- `TASK-105B` (`FilePriceProvider`) **chưa DONE** — là dependency cứng cho
  `HistoricalVendorPriceProvider` (compose nó). Phải implement trước hoặc
  cùng lúc.
