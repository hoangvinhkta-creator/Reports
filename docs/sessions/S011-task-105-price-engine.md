# BÀN GIAO SESSION (SESSION HANDOFF)

Session ID:
S011

Task:
TASK-105 — price_engine + interface PriceProvider

Task Mode:
MAJOR

Project Profile:
PRODUCT

Status:
DONE — 9/9 REQUIRED check PASS, 57/57 test tổng (không regression).

## Kết Quả (Result)

Xây `PriceProvider` (Protocol) — interface ổn định cho TASK-401 (Phase 4)
tích hợp Price Master thật sau này — và `PendingPriceProvider`, implementation
mặc định trả `None` cho mọi lookup vì chưa có Price Master nào tồn tại ở
Phase 1 (DEC-103). `price_engine.apply_prices()` áp provider vào từng
`WorkingLine`, ghi `accounting_purchase_price` (Decimal hoặc `None`) và
`price_source` (`Pending`/`PriceMaster`). Nối vào `run_import()` làm bước 8,
sau bước 7 (propagate LeadSource) của TASK-101.

**Khác biệt quan trọng với TASK-101:** không có "dữ liệu thật cần đối
chiếu" ở task này — `PendingPriceProvider` là hành vi **đúng** cho 100% dòng
ở Phase 1 vì Price Master thật sự chưa tồn tại ở bất kỳ đâu, không phải một
giới hạn của môi trường test. Task hoàn thành trọn vẹn trên fixture, không
có check nào BLOCKED.

**Phát hiện quan trọng cho phiên sau (TASK-106):** trong lúc soạn note bàn
giao, tự phát hiện một giả định sai đã viết ra trước khi commit — cho rằng
từ vựng adjustment (`Qua kho`, `KHBH`...) nằm ở cột `delivery_cost` của
`RawRow`. Đọc lại `docs/analysis/01_DATA_MAPPING.md` xác nhận: `KpiAdjustment`
**không có nguồn trong 17 cột raw** — từ vựng đó chỉ có trong cột J của
REPORT (gõ tay khi lắp báo cáo thủ công). Đã tự sửa trước khi commit, không
để giả định sai lan sang code. TASK-106 cần làm rõ nguồn dữ liệu trước khi
implement — xem `PROJECT/PROJECT_PROGRESS.md` → "Session tiếp theo" → Track A.

## Subtask Đã Hoàn Thành (Subtasks Completed)
- [x] 105.1 Domain model: `accounting_purchase_price`, `price_source`
- [x] 105.2 `PriceProvider` interface + `PendingPriceProvider`
- [x] 105.3 `price_engine.apply_prices()`
- [x] 105.4 Nối vào `run_import()` (bước 8)
- [x] 105.5 Test suite (8 test mới)

## Subtask Còn Lại (Subtasks Remaining)
- Không có. TASK-105 DONE trọn vẹn.

## Tóm Tắt Completion Gate (Completion Gate Summary)

Required:
9 (CHECK-105-01 đến 09)

PASS:
9

FAIL:
0

BLOCKED:
0

NOT_TESTED:
0

## Evidence Xác Minh (Verification Evidence)

| Check ID | Status | Evidence Level | Evidence | Executed By | Timestamp |
|---|---|---|---|---|---|
| CHECK-105-01 | PASS | E1 | `pytest tests/test_price_provider.py -q` → 2/2 | Claude | 2026-08-23 |
| CHECK-105-02 | PASS | E1 | `pytest tests/test_price_engine.py -q` → 4/4, kể cả case provider thật miss 1 sản phẩm | Claude | 2026-08-23 |
| CHECK-105-03 | PASS | E1 | test xác nhận `price_source` đúng cả 2 nhánh | Claude | 2026-08-23 |
| CHECK-105-04 | PASS | E1 | `test_custom_price_provider_injected_without_touching_price_engine` | Claude | 2026-08-23 |
| CHECK-105-05 | PASS | E1 | `test_default_run_leaves_every_price_pending` + đọc `app/pipeline.py` | Claude | 2026-08-23 |
| CHECK-105-06 | PASS | E1 | grep xác nhận không import fastapi/sqlalchemy | Claude | 2026-08-23 |
| CHECK-105-07 | PASS | E1 | grep xác nhận không hard-code giá trị giá | Claude | 2026-08-23 |
| CHECK-105-08 | PASS | E1 | mọi field tiền kiểu `Decimal`, không `float()` | Claude | 2026-08-23 |
| CHECK-105-09 | PASS | E1 | `pytest tests/ -q` → 57/57, không regression | Claude | 2026-08-23 |

Chi tiết đầy đủ: `docs/tasks/TASK-105-price-engine.md`.

## File Đã Thay Đổi (Files Changed)

Created:
- `app/modules/pricing/__init__.py`, `provider.py`, `price_engine.py`
- `tests/test_price_provider.py`, `test_price_engine.py`
- `docs/tasks/TASK-105-price-engine.md`
- `docs/sessions/S011-task-105-price-engine.md` (file này)

Modified:
- `app/modules/domain/models.py` — thêm `PRICE_SOURCE_*`,
  `WorkingLine.accounting_purchase_price`, `WorkingLine.price_source`
- `app/pipeline.py` — thêm bước 8, tham số `price_provider`
- `tests/test_pipeline.py` — thêm 2 test tích hợp
- `PROJECT/PROJECT_PROGRESS.md`, `PROJECT/LO_TRINH_DE_HIEU.md` — đồng bộ

Deleted:
- Không có.

## Quyết Định Chính (Key Decisions)
- `PendingPriceProvider` là implementation đúng cho toàn bộ Phase 1, không
  phải placeholder chờ dữ liệu test — vì Price Master thật chưa tồn tại.
- `product_raw` dùng làm khóa tra cứu tạm thời cho tới khi TASK-402
  (product_mapper) sinh `ProductCode` thật — ghi rõ trong docstring của
  `provider.py`, không giấu giả định này.
- Không cộng `kpi_purchase_adjustment` vào `accounting_purchase_price` ở
  task này — giữ đúng ranh giới với TASK-106.

## Rủi Ro / Vướng Mắc (Risks / Blockers)
- Không có blocker cho TASK-105.
- **Rủi ro đã phát hiện cho TASK-106:** nguồn dữ liệu cho adjustment
  vocabulary chưa rõ (xem "Kết Quả" ở trên). Không phải blocker của
  TASK-105, nhưng phiên tiếp theo phải xử lý trước khi code TASK-106.

## Hạng Mục Regression (Regression Items)
- `pytest tests/ -q` → 57/57 PASS, gồm toàn bộ 49 test cũ của TASK-101.
  Không regression.

## Chưa Được Thay Đổi (Do Not Change Yet)
- `app/modules/mapping/`, `app/modules/orders/`, `app/modules/lead_source/`
  (TASK-101, đã DONE).
- `docs/analysis/`, `docs/adr/`, `PROJECT/PROJECT_DECISIONS.md`.
- Bất kỳ file nào của Track B.

## Session Tiếp Theo Được Khuyến Nghị (Next Recommended Session)
TASK-106 (adjustment_engine) — **nhưng đọc kỹ mục "Session tiếp theo" →
Track A trong `PROJECT/PROJECT_PROGRESS.md` trước khi code**, vì nguồn dữ
liệu cho từ vựng adjustment chưa rõ (không có trong 17 cột raw).

## File Agent Tiếp Theo Cần Đọc (Files Next Agent Should Read)
- `CLAUDE.md`
- `PROJECT/PROJECT_PROGRESS.md` (mục "Trạng thái Task hiện tại" và "Session
  tiếp theo" → Track A)
- `docs/tasks/TASK-105-price-engine.md`
- `docs/analysis/01_DATA_MAPPING.md` mục "Field trong Working Data không có
  nguồn thô" — đọc trước khi bắt đầu TASK-106
- `app/pipeline.py`, `app/modules/` (code đã có, đừng viết lại)
