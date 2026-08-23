# BÀN GIAO SESSION (SESSION HANDOFF)

Session ID:
S012

Task:
TASK-106 — adjustment_engine (AirConditionerClassifier + AdjustmentResolver)

Task Mode:
MAJOR

Project Profile:
PRODUCT

Status:
DONE — 5/5 REQUIRED check PASS, 74/74 test tổng (không regression).

## Kết Quả (Result)

Trước khi code, làm rõ nguồn dữ liệu và cơ chế cho `KpiAdjustment` — điểm mà
S011 để lại làm cảnh báo chặn ("không được tự suy đoán rồi code"). Đặt 4 câu
hỏi cho chủ dự án qua `AskUserQuestion` (Risk 4/5, ảnh hưởng KPI/lương), ghi
câu trả lời thành **DEC-125** trước khi viết bất kỳ dòng code nào.

Kết luận: `KpiAdjustment` **không có nguồn trong 17 cột raw** — đúng phương
án (b) mà S011 nêu, không phải (a). Đây là dữ liệu người dùng **chọn tay sau
khi import**, không phải thứ để "parse" tự động như giả định ban đầu (S011
đã tự phát hiện và sửa nhầm lẫn tương tự trước khi commit). Bốn quy tắc cụ
thể (xem DEC-125 để biết chi tiết đầy đủ):

1. Qua kho / NCC giao — số tiền theo **phương tiện giao hàng** (xe máy nhẹ
   -50k, xe máy cồng kềnh -100k, ô tô -200k), không theo model sản phẩm.
2. KHBH / Thợ lắp — chỉ có mặc định khi sản phẩm là **điều hòa** (-50k/-200k).
   Ngoài điều hòa: không có mặc định, luôn nhập tay.
3. Nhận diện điều hòa — khớp từ khóa trên `ProductRaw`, đã xác nhận khả thi
   trên dữ liệu thật.
4. Kích hoạt — người dùng chọn tay sau khi import, không có quét tự động.

Xây `AirConditionerClassifier.is_air_conditioner(product_raw) -> bool` (dò
từ khóa, NFC-normalize, không phân biệt hoa/thường) và
`AdjustmentResolver.resolve_suggested_amount(adjustment_type, *,
delivery_method=None, is_air_conditioner=None) -> AdjustmentResolution` (tra
`config/adjustments.yaml`). **Không nối vào `app.pipeline.run_import()`,
không thêm field vào domain model** — khác hẳn TASK-105, vì không có "giá
trị đúng cho mọi dòng" nào ở đây để tự động áp mặc định; module chỉ trả giá
trị **đề xuất** cho tầng override thủ công thật (Phase 2/3) gọi tới sau này.
`None` là kết quả đúng khi thiếu ngữ cảnh — không bao giờ suy đoán hay coi 0
(DEC-103).

## Subtask Đã Hoàn Thành (Subtasks Completed)
- [x] 106.1 `config/adjustments.yaml` — từ khóa AC + tier phương tiện + default AC
- [x] 106.2 `AirConditionerClassifier`
- [x] 106.3 `AdjustmentResolver`
- [x] 106.4 Test suite (17 test mới, 74/74 tổng PASS)

## Subtask Còn Lại (Subtasks Remaining)
- Không có. TASK-106 DONE trọn vẹn trong phạm vi đã thu hẹp (module độc lập).

## Tóm Tắt Completion Gate (Completion Gate Summary)

Required:
5 (CHECK-106-01 đến 05)

PASS:
5

FAIL:
0

BLOCKED:
0

NOT_TESTED:
0

## Evidence Xác Minh (Verification Evidence)

| Check ID | Status | Evidence Level | Evidence | Executed By | Timestamp |
|---|---|---|---|---|---|
| CHECK-106-01 | PASS | E1 | `pytest tests/test_adjustment_resolver.py -q` → 11/11, 3 tier phương tiện đúng | Claude | 2026-08-23 |
| CHECK-106-02 | PASS | E1 | KHBH/Thợ lắp default đúng khi AC, `None` khi non-AC/unknown | Claude | 2026-08-23 |
| CHECK-106-03 | PASS | E1 | `pytest tests/test_ac_classifier.py -q` → 6/6, khớp đúng pattern dữ liệu thật | Claude | 2026-08-23 |
| CHECK-106-04 | PASS | E1 | loại/phương tiện không khớp → `None`, không suy đoán | Claude | 2026-08-23 |
| CHECK-106-05 | PASS | E1 | `git diff --stat` xác nhận `app/pipeline.py`/`models.py` không đổi; grep xác nhận không framework import, không hard-code, không float | Claude | 2026-08-23 |

Chi tiết đầy đủ: `docs/tasks/TASK-106-adjustment-engine.md`.

## File Đã Thay Đổi (Files Changed)

Created:
- `app/modules/adjustment/__init__.py`, `ac_classifier.py`, `adjustment_resolver.py`
- `config/adjustments.yaml`
- `tests/test_ac_classifier.py`, `test_adjustment_resolver.py`
- `docs/tasks/TASK-106-adjustment-engine.md`
- `docs/sessions/S012-task-106-adjustment-engine.md` (file này)

Modified:
- `PROJECT/PROJECT_DECISIONS.md` — thêm DEC-125 (trước implementation)
- `PROJECT/PROJECT_PROGRESS.md`, `PROJECT/LO_TRINH_DE_HIEU.md` — đồng bộ

Deleted:
- Không có.

## Quyết Định Chính (Key Decisions)
- DEC-125 — 4 quy tắc nghiệp vụ cho adjustment, từ trả lời trực tiếp của chủ
  dự án qua `AskUserQuestion`.
- `AdjustmentResolver` không nối `run_import()` — khác biệt kiến trúc có chủ
  đích với `PendingPriceProvider` (TASK-105), vì không có nguồn tự động nào
  cho loại điều chỉnh/phương tiện giao.
- Không thêm field `kpi_purchase_adjustment` vào domain model ở task này —
  field chưa có ai điền thì không thêm trước (tránh field chết).
- Ba tier phương tiện dùng chung một bảng cho cả Qua kho và NCC giao (chủ dự
  án xác nhận cùng giá trị) — nhưng cấu hình vẫn khai riêng từng loại trong
  YAML để có thể tách sau mà không sửa code.

## Rủi Ro / Vướng Mắc (Risks / Blockers)
- Không có blocker cho TASK-106.
- **Rủi ro còn mở (ghi trong DEC-125, không chặn task):** từ khóa nhận diện
  điều hòa mới xác nhận trên 2 tháng dữ liệu mẫu (01/2026, 06/2026) — biến
  thể chính tả ngoài phạm vi đó có thể bị bỏ sót (false negative, không phải
  false positive). Khi Phase 2/3 xây UI, nên có Review Queue cho case nghi
  ngờ thay vì chỉ tin classifier tuyệt đối.

## Hạng Mục Regression (Regression Items)
- `pytest tests/ -q` → 74/74 PASS, gồm toàn bộ 57 test cũ (TASK-101 +
  TASK-105). Không regression.

## Chưa Được Thay Đổi (Do Not Change Yet)
- `app/pipeline.py`, `app/modules/domain/models.py` — cố ý không đụng (xem
  Out of Scope trong task file).
- `app/modules/mapping/`, `app/modules/orders/`, `app/modules/lead_source/`,
  `app/modules/pricing/` (đã DONE).
- `docs/analysis/`, `docs/adr/`.
- Bất kỳ file nào của Track B.

## Session Tiếp Theo Được Khuyến Nghị (Next Recommended Session)
TASK-107 (profit_engine) — `AccountingProfit = (SellPrice −
AccountingPurchasePrice) × Quantity` không cần `kpi_purchase_adjustment`,
nên có thể bắt đầu ngay. Đọc kỹ mục "Session tiếp theo" → Track A trong
`PROJECT/PROJECT_PROGRESS.md` trước khi code — có câu hỏi mở về việc
`EligibleKpiProfit` nên xử lý thế nào khi `kpi_purchase_adjustment` chưa tồn
tại trên domain model (đừng tự chọn giả định 0 — DEC-103 cấm).

## File Agent Tiếp Theo Cần Đọc (Files Next Agent Should Read)
- `CLAUDE.md`
- `PROJECT/PROJECT_PROGRESS.md` (mục "Trạng thái Task hiện tại" và "Session
  tiếp theo" → Track A)
- `docs/tasks/TASK-106-adjustment-engine.md`
- `docs/analysis/03_RULE_CLASSIFICATION.md` mục "U — Universal formula"
- `PROJECT/PROJECT_DECISIONS.md` (DEC-103, DEC-125)
- `app/pipeline.py`, `app/modules/domain/models.py` (code đã có, đừng viết lại)
