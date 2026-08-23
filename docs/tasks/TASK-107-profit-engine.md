# TASK-107 — Profit Engine (AccountingProfit)

## Metadata
Status:
DONE — 6/6 REQUIRED check PASS. 83/83 test tổng (9 test mới, không
regression).

Phase:
PHASE-01 — Engine tính toán

Task Mode:
MAJOR

Primary Agent Tier:
B

Escalation Tier:
C

Difficulty:
2/5

Risk:
4/5

Blast Radius:
4/5

Project Profile:
PRODUCT

## Mục Tiêu (Objective)

Bước 9 của §22 đặc tả, công thức Universal (`docs/analysis/03_RULE_CLASSIFICATION.md`
§U):

    AccountingProfit = (SellPrice − AccountingPurchasePrice) × Quantity

DEC-126 (chủ dự án chốt ngay sau khi chấp nhận TASK-106) thu hẹp scope task
này một cách tường minh: **chỉ** `AccountingProfit`. `EligibleKpiProfit`
(công thức có `OtherKpiAdjustment`) **không** thuộc task này — persistence
và cơ chế xác nhận (`final_amount`) của Adjustment record chưa tồn tại
(TASK-202/302/305, Phase 2/3), nên chưa có gì hợp lệ để đưa vào công thức
KPI.

## Phạm Vi (Scope)

- Mở rộng `WorkingLine` thêm `accounting_profit: Optional[Decimal]`.
- `app/modules/profit/profit_engine.py`:
  - `compute_accounting_profit(line) -> Optional[Decimal]` — hàm thuần túy,
    `None` khi bất kỳ input nào (`sell_price`, `accounting_purchase_price`,
    `quantity`) là `None`.
  - `apply_accounting_profit(lines) -> list[WorkingLine]` — ghi
    `accounting_profit` cho từng dòng.
- Nối vào `app/pipeline.py` làm bước 9, sau bước 8 (price_engine) đã có ở
  TASK-105.
- Test đơn vị + tích hợp: case tính đúng, case Pending (giá nhập chưa có),
  case thiếu quantity/sell_price, case xác nhận **không** dùng `Discount`
  hay bất kỳ trường nào của `app.modules.adjustment` (DEC-126 điểm 1).

## Ngoài Phạm Vi (Out of Scope)

- **`EligibleKpiProfit`** (`= (SellPrice − KpiPurchasePrice) × Quantity −
  Discount − EligibleCosts + OtherKpiAdjustment`) — chặn bởi DEC-126 điểm
  3–6: cần Adjustment record đã **xác nhận** (`final_amount`, không phải
  `suggested_amount` từ `AdjustmentResolver` của TASK-106), và persistence
  đó chưa tồn tại ở Phase 1. Đây là ranh giới scope đúng, không phải giới
  hạn tạm thời do thiếu thời gian.
- **`KpiPurchasePrice = AccountingPurchasePrice + KpiPurchaseAdjustment`**
  — cùng lý do, cần `kpi_purchase_adjustment` đã xác nhận.
- Bất kỳ import/dependency nào vào `app.modules.adjustment` — `profit_engine`
  độc lập hoàn toàn với luồng Adjustment (DEC-126 điểm 1–2), kiểm chứng
  bằng grep ở Completion Gate.
- `conversion_engine` (TASK-108), Review Queue persistence (TASK-110).
- Bất kỳ thay đổi nào ở `app/modules/adjustment/`, `config/adjustments.yaml`
  (đã DONE, TASK-106).

## Phụ Thuộc (Dependencies)
- TASK-105 — DONE. Cung cấp `accounting_purchase_price` trên `WorkingLine`.
- DEC-103, DEC-126 — quyết định nghiệp vụ nền tảng cho task này.

## Chặn (Blocks)
- TASK-108 (conversion_engine) không phụ thuộc trực tiếp `AccountingProfit`,
  nhưng cùng nằm trong chuỗi bước 9–11 của §22 đặc tả.
- TASK-202/302/305 (Phase 2/3): khi Adjustment persistence + confirmation
  tồn tại, một task profit riêng (hoặc mở rộng `profit_engine`) sẽ cộng
  thêm `EligibleKpiProfit` — không phải task này.

## An Toàn Để Chạy Song Song Với (Parallel-Safe With)
- TASK-101, TASK-105, TASK-106 (đã DONE, không áp dụng).
- Track B (Governance) — không chạm chung file.

## Phạm Vi Tác Động Dự Kiến (Expected Touch Area)

Allowed:
- `app/modules/domain/models.py` (mở rộng, không phá field cũ)
- `app/modules/profit/` (module mới)
- `app/pipeline.py` (thêm bước 9)
- `tests/` (test mới cho profit)
- `docs/tasks/TASK-107-profit-engine.md`
- `PROJECT/PROJECT_PROGRESS.md`, `PROJECT/LO_TRINH_DE_HIEU.md`
- `docs/sessions/`

Không được đụng vào nếu chưa có Scope Expansion:
- `app/modules/adjustment/`, `config/adjustments.yaml` (đã DONE ở TASK-106).
- `app/modules/mapping/`, `app/modules/orders/`, `app/modules/lead_source/`,
  `app/modules/pricing/` (đã DONE).
- `docs/analysis/`, `docs/adr/`, `PROJECT/PROJECT_DECISIONS.md` (DEC-126 đã
  ghi trong phiên này, trước khi implement).
- Bất kỳ file nào của Track B.

## Subtask (Subtasks)
- [x] 107.1 Domain model: `accounting_profit`
- [x] 107.2 `profit_engine.compute_accounting_profit()` + `apply_accounting_profit()`
- [x] 107.3 Nối vào `run_import()` (bước 9)
- [x] 107.4 Test suite (9 test mới, 83/83 tổng PASS)

## Ready Gate
Dùng `governance/core/TASK_READY_GATE_STANDARD.md`.

- [x] Objective rõ ràng.
- [x] Scope đã được xác định (chỉ `AccountingProfit`, DEC-126).
- [x] Out-of-scope đã được xác định (ranh giới rõ với `EligibleKpiProfit`,
      TASK-108, TASK-202/302/305).
- [x] Dependency (TASK-105, DEC-103, DEC-126) đã sẵn sàng.
- [x] Vùng tác động dự kiến đã được xác định.
- [x] Yêu cầu liên quan đã hiểu rõ (đặc tả §22 bước 9, §U công thức
      AccountingProfit, DEC-126).
- [x] Tác động dữ liệu đã biết rõ: không có dữ liệu cá nhân mới; lợi nhuận
      kế toán là dữ liệu nghiệp vụ nhạy cảm nhưng chưa lộ ra UI/API ở Phase 1.
- [x] Tác động bảo mật đã biết rõ: không có, chưa có network/DB.
- [x] Không liên quan routing/API (Phase 1 thuần Python).
- [x] Không có migration (chưa có DB).
- [x] Difficulty/Risk/Blast Radius đã chấm điểm (2/4/4 theo bảng sơ bộ
      `PROJECT/PROJECT_PROGRESS.md` — Risk/Blast giữ nguyên cao vì đây vẫn
      là số liệu lợi nhuận, dù công thức đơn giản hơn TASK-106).
- [x] Agent tier đã chỉ định (B, escalation C).
- [x] Escalation trigger đã xác định (xem bên dưới).
- [x] Completion Gate đã hoàn thiện và **frozen** trước khi implement.

## Completion Gate
Dùng `governance/core/TASK_COMPLETION_GATE_STANDARD.md` và
`governance/core/EVIDENCE_STANDARD.md`.

### Functional

#### CHECK-107-01 — AccountingProfit tính đúng công thức khi đủ input
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`pytest tests/test_profit_engine.py::test_computes_profit_when_price_known -q`
→ 1/1 passed. `(1.000.000 − 700.000) × 2 = 600.000` — khớp
`compute_accounting_profit()`.

Executed By:
Claude (session này)

Timestamp:
2026-08-23

#### CHECK-107-02 — Giá nhập Pending khiến AccountingProfit là None, không phải 0
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`test_pending_purchase_price_leaves_profit_none_not_zero` — dòng mới
normalize (chưa qua `price_engine`) có `accounting_purchase_price is None`
(Pending, TASK-105); sau `apply_accounting_profit()`, `accounting_profit is
None`. `test_missing_quantity_leaves_profit_none`,
`test_missing_sell_price_leaves_profit_none` xác nhận tương tự cho hai input
còn lại.

Executed By:
Claude (session này)

Timestamp:
2026-08-23

#### CHECK-107-03 — Công thức không dùng Discount, không dùng bất kỳ field Adjustment nào
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`test_profit_ignores_discount_and_kpi_adjustment_fields` — đặt `discount =
999.999` (giá trị cực lớn, nếu công thức vô tình trừ discount sẽ ra kết quả
sai rõ rệt), xác nhận `accounting_profit` vẫn đúng
`(1.000.000 − 400.000) × 1 = 600.000`, không bị discount ảnh hưởng — đúng
công thức §U (không có số hạng Discount, khác `TotalSales`).

Executed By:
Claude (session này)

Timestamp:
2026-08-23

#### CHECK-107-04 — run_import() gọi đúng bước 9 sau bước 8, mọi dòng mặc định Pending
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`tests/test_pipeline.py::test_default_run_leaves_every_accounting_profit_pending`
— gọi `run_import()` không truyền `price_provider`, xác nhận mọi dòng có
`accounting_profit is None` (đúng vì `accounting_purchase_price` mặc định
Pending). `test_accounting_profit_computed_when_price_provider_matches` xác
nhận khi `price_provider` khớp sản phẩm, `accounting_profit` tính đúng ngay
trong cùng lần chạy `run_import()`.

Executed By:
Claude (session này)

Timestamp:
2026-08-23

### Architecture

#### CHECK-107-05 — profit_engine không phụ thuộc adjustment; không import framework; không hard-code; tiền Decimal
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
```
$ grep -rn "adjustment" app/modules/profit/*.py
app/modules/profit/profit_engine.py:8:liệu. Module này không phụ thuộc `app.modules.adjustment` theo bất kỳ cách
(chỉ xuất hiện trong docstring giải thích — không có import/dependency thật)

$ grep -rn "^import\|^from" app/modules/profit/profit_engine.py
from __future__ import annotations
from decimal import Decimal
from typing import Optional
from app.modules.domain.models import WorkingLine
(không có app.modules.adjustment, không có fastapi/sqlalchemy/flask)

$ grep -rnE "[0-9]{4,}" app/modules/profit/ app/pipeline.py
(không có kết quả — không hard-code số tiền)

$ grep -rn "float(" app/modules/profit/
(không có kết quả)
```
`accounting_profit: Optional[Decimal]`, `compute_accounting_profit() ->
Optional[Decimal]` — tiền luôn `Decimal`.

Executed By:
Claude (session này)

Timestamp:
2026-08-23

### Regression

#### CHECK-107-06 — Toàn bộ test TASK-101/105/106 vẫn PASS sau khi mở rộng domain model + pipeline
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`pytest tests/ -q` → **83/83 passed** (74 test cũ của TASK-101+105+106 + 9
test mới của TASK-107: 7 profit_engine + 2 pipeline integration). Không
regression — thêm field có default value vào cuối `WorkingLine` và một bước
pipeline mới sau bước 8 không phá constructor/thứ tự nào đã có.

Executed By:
Claude (session này)

Timestamp:
2026-08-23

## Tiêu Chí Hoàn Thành (Exit Criteria)
- [x] 100% REQUIRED check PASS — 6/6.
- [x] Không có lỗi nghiêm trọng chưa xử lý.
- [x] Evidence level E1 đạt được cho mọi check.
- [x] `PROJECT/PROJECT_PROGRESS.md` và `PROJECT/LO_TRINH_DE_HIEU.md` cập
      nhật đồng thời.
- [x] Session handoff đã viết (MAJOR task).
- [x] Toàn bộ 74 test cũ (TASK-101+105+106) vẫn PASS (không regression) —
      83/83 tổng.

## Điều Kiện Kích Hoạt Leo Thang (Escalation Triggers)
- Khi TASK-202/302/305 (Phase 2/3) xây persistence Adjustment thật — cần
  quyết định `EligibleKpiProfit` implement ở đâu: mở rộng `profit_engine`
  hay module riêng. Không tự quyết định lúc đó mà không xem lại DEC-126.
- Phát hiện `EligibleCosts` (một số hạng khác của `EligibleKpiProfit`, chưa
  được định nghĩa nguồn dữ liệu ở bất kỳ đâu trong `docs/analysis/`) — cần
  làm rõ nguồn trước khi bất kỳ task nào chạm tới `EligibleKpiProfit`.

## Đăng Ký File Đã Thay Đổi (Changed Files Registry)

Created:
- `app/modules/profit/__init__.py`, `profit_engine.py`
- `tests/test_profit_engine.py`
- `docs/tasks/TASK-107-profit-engine.md`

Modified:
- `app/modules/domain/models.py` — thêm `WorkingLine.accounting_profit`
- `app/pipeline.py` — thêm bước 9
- `tests/test_pipeline.py` — thêm 2 test tích hợp
- `PROJECT/PROJECT_DECISIONS.md` — thêm DEC-126 (trước implementation)
- `PROJECT/PROJECT_PROGRESS.md`, `PROJECT/LO_TRINH_DE_HIEU.md` — đồng bộ

Deleted:
- Không có.

Migration Impact:
- Không có (chưa có DB ở Phase 1).

## Ghi Chú (Notes)

**Vì sao task này nối được vào `run_import()` như TASK-105, khác TASK-106:**
`AccountingProfit` là hàm thuần túy của các field đã có sẵn trên `WorkingLine`
sau bước 8 (`sell_price`, `quantity`, `accounting_purchase_price`) — không
cần input nào từ người dùng chọn tay. Khi `accounting_purchase_price` còn
Pending, `accounting_profit` tự động cũng Pending (`None`) theo đúng công
thức, không cần logic điều kiện đặc biệt nào. Đây là lý do task này giống
TASK-105 (auto-wire được) hơn là TASK-106 (không auto-wire được).
