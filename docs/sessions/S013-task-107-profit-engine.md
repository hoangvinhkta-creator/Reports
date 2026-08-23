# BÀN GIAO SESSION (SESSION HANDOFF)

Session ID:
S013

Task:
TASK-107 — profit_engine (AccountingProfit)

Task Mode:
MAJOR

Project Profile:
PRODUCT

Status:
DONE — 6/6 REQUIRED check PASS, 83/83 test tổng (không regression).

## Kết Quả (Result)

Ngay sau khi chấp nhận TASK-106 DONE, chủ dự án chốt 6 nguyên tắc ranh giới
cho profit/adjustment trước khi cho phép code TASK-107 — ghi thành
**DEC-126**:

1. `AccountingProfit` độc lập hoàn toàn với KPI Adjustment.
2. Adjustment không ghi đè dữ liệu kế toán.
3. Persistence tương lai: một Order hỗ trợ nhiều Adjustment records.
4. Phân biệt `suggested_amount` (TASK-106) và `final_amount` (xác nhận thật).
5. Chỉ Adjustment đã xác nhận mới dùng cho `EligibleKpiProfit`.
6. Không mặc định adjustment chưa xác định = 0.

Hệ quả trực tiếp: TASK-107 **chỉ** triển khai `AccountingProfit`, không tự
mở rộng sang `EligibleKpiProfit` vì persistence + cơ chế xác nhận Adjustment
chưa tồn tại (đó là TASK-202/302/305, Phase 2/3).

Xây `app/modules/profit/profit_engine.py`:
`compute_accounting_profit(line) -> Optional[Decimal]` (hàm thuần túy) +
`apply_accounting_profit(lines)`. Công thức
`AccountingProfit = (SellPrice − AccountingPurchasePrice) × Quantity` —
không có số hạng Discount, không có bất kỳ tham chiếu nào tới
`app.modules.adjustment` (kiểm chứng bằng grep). Nối vào `run_import()` làm
bước 9 — **tự động**, khác TASK-106, vì đây là hàm thuần túy của các field
đã sẵn có trên `WorkingLine` sau bước 8, không cần lựa chọn thủ công nào.
Khi `accounting_purchase_price` còn Pending (TASK-105), `accounting_profit`
tự động cũng `None` theo đúng công thức.

## Subtask Đã Hoàn Thành (Subtasks Completed)
- [x] 107.1 Domain model: `accounting_profit`
- [x] 107.2 `profit_engine.compute_accounting_profit()` + `apply_accounting_profit()`
- [x] 107.3 Nối vào `run_import()` (bước 9)
- [x] 107.4 Test suite (9 test mới, 83/83 tổng PASS)

## Subtask Còn Lại (Subtasks Remaining)
- Không có. TASK-107 DONE trọn vẹn trong phạm vi đã chốt (chỉ AccountingProfit).

## Tóm Tắt Completion Gate (Completion Gate Summary)

Required:
6 (CHECK-107-01 đến 06)

PASS:
6

FAIL:
0

BLOCKED:
0

NOT_TESTED:
0

## Evidence Xác Minh (Verification Evidence)

| Check ID | Status | Evidence Level | Evidence | Executed By | Timestamp |
|---|---|---|---|---|---|
| CHECK-107-01 | PASS | E1 | công thức tính đúng, `(1.000.000−700.000)×2=600.000` | Claude | 2026-08-23 |
| CHECK-107-02 | PASS | E1 | Pending/thiếu quantity/thiếu sell_price → `None`, không phải 0 | Claude | 2026-08-23 |
| CHECK-107-03 | PASS | E1 | discount cực lớn không ảnh hưởng kết quả — đúng công thức §U | Claude | 2026-08-23 |
| CHECK-107-04 | PASS | E1 | `run_import()` bước 9 đúng thứ tự, mặc định Pending, tính đúng khi có provider | Claude | 2026-08-23 |
| CHECK-107-05 | PASS | E1 | grep xác nhận không phụ thuộc `app.modules.adjustment`, không framework, không hard-code, tiền Decimal | Claude | 2026-08-23 |
| CHECK-107-06 | PASS | E1 | `pytest tests/ -q` → 83/83, không regression trên 74 test cũ | Claude | 2026-08-23 |

Chi tiết đầy đủ: `docs/tasks/TASK-107-profit-engine.md`.

## File Đã Thay Đổi (Files Changed)

Created:
- `app/modules/profit/__init__.py`, `profit_engine.py`
- `tests/test_profit_engine.py`
- `docs/tasks/TASK-107-profit-engine.md`
- `docs/sessions/S013-task-107-profit-engine.md` (file này)

Modified:
- `app/modules/domain/models.py` — thêm `WorkingLine.accounting_profit`
- `app/pipeline.py` — thêm bước 9
- `tests/test_pipeline.py` — thêm 2 test tích hợp
- `PROJECT/PROJECT_DECISIONS.md` — thêm DEC-126 (trước implementation)
- `PROJECT/PROJECT_PROGRESS.md`, `PROJECT/LO_TRINH_DE_HIEU.md` — đồng bộ

Deleted:
- Không có.

## Quyết Định Chính (Key Decisions)
- DEC-126 — 6 nguyên tắc ranh giới AccountingProfit/Adjustment, từ chủ dự án
  trực tiếp sau khi duyệt TASK-106.
- `EligibleKpiProfit` cố ý không làm ở task này — chặn bởi thiếu persistence
  Adjustment đã xác nhận, không phải giới hạn thời gian.
- `profit_engine` nối tự động vào `run_import()` (giống TASK-105, khác
  TASK-106) vì là hàm thuần túy không cần input thủ công.

## Rủi Ro / Vướng Mắc (Risks / Blockers)
- Không có blocker cho TASK-107.
- Không có rủi ro mới phát sinh — DEC-126 đã đóng trước câu hỏi mở mà S012
  để lại (giả định 0 tạm thời hay hoãn hẳn EligibleKpiProfit) bằng lựa chọn
  rõ ràng: hoãn hẳn.

## Hạng Mục Regression (Regression Items)
- `pytest tests/ -q` → 83/83 PASS, gồm toàn bộ 74 test cũ (TASK-101 + 105 +
  106). Không regression.

## Chưa Được Thay Đổi (Do Not Change Yet)
- `app/modules/adjustment/`, `config/adjustments.yaml` (đã DONE, TASK-106).
- `app/modules/mapping/`, `app/modules/orders/`, `app/modules/lead_source/`,
  `app/modules/pricing/` (đã DONE).
- `docs/analysis/`, `docs/adr/`.
- Bất kỳ file nào của Track B.

## Session Tiếp Theo Được Khuyến Nghị (Next Recommended Session)
TASK-108 (conversion_engine) — **rủi ro cao nhất trong roadmap (5/5)**. Đọc
kỹ mục "Completion Gate sơ bộ" trong `PROJECT/PROJECT_PROGRESS.md` (các
REQUIRED check đã ghi sẵn cho task này) và mục "Session tiếp theo" → Track A
trước khi viết Ready Gate.

## File Agent Tiếp Theo Cần Đọc (Files Next Agent Should Read)
- `CLAUDE.md`
- `PROJECT/PROJECT_PROGRESS.md` (mục "Trạng thái Task hiện tại", "Completion
  Gate sơ bộ" phần TASK-108, và "Session tiếp theo" → Track A)
- `docs/tasks/TASK-107-profit-engine.md`
- `docs/adr/ADR-104-lead-source-vs-conversion-scheme.md`
- `PROJECT/PROJECT_DECISIONS.md` (DEC-119, DEC-120, DEC-121)
- `tools/analysis/verify_ads_rule.py` — bản tham chiếu 31/31 case
- `app/pipeline.py`, `app/modules/domain/models.py` (code đã có, đừng viết lại)
