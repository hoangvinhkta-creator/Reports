# TASK-106 — Adjustment Engine (Classifier Điều Hòa + Resolver Số Tiền Đề Xuất)

## Metadata
Status:
DONE — 5/5 REQUIRED check PASS. 74/74 test tổng (17 test mới + 57 test cũ,
không regression).

Phase:
PHASE-01 — Engine tính toán

Task Mode:
MAJOR

Primary Agent Tier:
B

Escalation Tier:
C

Difficulty:
4/5

Risk:
4/5

Blast Radius:
4/5

Project Profile:
PRODUCT

## Mục Tiêu (Objective)

Bước 9 của §22 đặc tả liên quan `KpiPurchaseAdjustment`. DEC-125 làm rõ:
`KpiAdjustment` **không có nguồn trong 17 cột raw** — khác `AccountingPurchasePrice`
(TASK-105), không có cơ chế nào tự động quét raw data rồi tự áp adjustment.
Loại điều chỉnh và phương tiện giao hàng là thứ người dùng **chọn tay sau
khi import** (DEC-125 điểm 4).

TASK-106 giao đúng phần có thể xây ở Phase 1 mà không cần UI/DB: một
**module tính toán độc lập** trả về số tiền điều chỉnh **đề xuất** khi đã
biết loại điều chỉnh + ngữ cảnh (phương tiện giao, hoặc sản phẩm có phải
điều hòa) — để tầng override thủ công thật (Phase 2/3, TASK-202/302/305) gọi
tới và điền sẵn, người dùng luôn ghi đè được, không bao giờ tự động áp.

## Phạm Vi (Scope)

- `AirConditionerClassifier` — dò từ khóa điều hòa (`config/adjustments.yaml`
  → `air_conditioner_keywords`) trên `ProductRaw`, không phân biệt hoa/thường,
  NFC-normalize. Trả `bool`.
- `AdjustmentResolver` — `resolve_suggested_amount(adjustment_type, *,
  delivery_method=None, is_air_conditioner=None) -> AdjustmentResolution`:
  - `Qua kho` / `NCC giao`: tra `delivery_method_tiers` theo phương tiện giao
    (`xe_may_nhe` / `xe_may_cong_kenh` / `o_to`) — DEC-125 điểm 1.
  - `KHBH` / `Thợ lắp`: chỉ có mặc định khi `is_air_conditioner=True` —
    DEC-125 điểm 2. Không có mặc định cho non-AC hoặc trạng thái chưa biết.
  - Loại điều chỉnh không có trong config: không đoán, trả `None`.
- `config/adjustments.yaml` — toàn bộ giá trị số tiền + từ khóa điều hòa,
  đúng phân loại "B — Business rule" (`docs/analysis/03_RULE_CLASSIFICATION.md`).
- Test đơn vị đầy đủ mọi nhánh (3 tier phương tiện × 2 loại, AC/non-AC ×
  2 loại, loại/phương tiện không khớp, loại không xác định).

## Ngoài Phạm Vi (Out of Scope)

- **Nối vào `run_import()` / `app.pipeline`** — không có, vì không có cơ chế
  tự động kích hoạt đúng nghĩa (DEC-125 điểm 4). Khác hẳn TASK-105.
- **Thêm field `kpi_purchase_adjustment` vào `WorkingLine`/`Order`** — chưa
  thêm ở task này. Field lưu giá trị đã chọn/ghi đè thật cần cơ chế override +
  audit trail (TASK-202/302/305, Phase 2/3), nơi UI thật tồn tại để người
  dùng chọn tay. Thêm field vào domain model bây giờ mà không ai điền là một
  field chết — vi phạm nguyên tắc "không tổ chức trước cho nhu cầu chưa có"
  (CLAUDE.md, cùng logic DEC-124 áp cho role).
- `KpiPurchasePrice = AccountingPurchasePrice + KpiPurchaseAdjustment` — công
  thức Universal đã định nghĩa (`docs/analysis/03_RULE_CLASSIFICATION.md`),
  nhưng phép cộng thật chỉ có ý nghĩa khi `kpi_purchase_adjustment` đã tồn
  tại từ override thật — thuộc phạm vi task cộng công thức report sau này.
- Review Queue cho `ProductRaw` không khớp từ khóa nào nhưng "nhìn giống"
  điều hòa (viết tắt lạ, lỗi chính tả ngoài 2 biến thể đã xác nhận) — cần UI
  review, chưa xây ở Phase 1. Rủi ro này ghi nhận ở DEC-125, không chặn task.
- `profit_engine` (TASK-107), `conversion_engine` (TASK-108).
- Parse ghi chú lịch sử ở cột J REPORT (`Qua kho -100`, `KHBH -50`...) —
  đó là dữ liệu **gõ tay khi lắp báo cáo thủ công** trong workbook cũ, không
  phải nguồn của module này (`docs/analysis/01_DATA_MAPPING.md`).

## Phụ Thuộc (Dependencies)
- TASK-105 — DONE. Xác lập ranh giới `accounting_purchase_price` /
  `kpi_purchase_adjustment` (§ Out of Scope).
- DEC-125 — quyết định nghiệp vụ nền tảng cho task này.

## Chặn (Blocks)
- TASK-202/302/305 (Phase 2/3, manual override + audit trail) sẽ gọi
  `AdjustmentResolver` làm giá trị đề xuất ban đầu trên UI.
- `profit_engine`/report formula thật cho `KpiPurchasePrice` cần cả
  `kpi_purchase_adjustment` field (Phase 2/3) lẫn resolver này.

## An Toàn Để Chạy Song Song Với (Parallel-Safe With)
- TASK-101, TASK-105 (đã DONE, không áp dụng).
- Track B (Governance) — không chạm chung file.

## Phạm Vi Tác Động Dự Kiến (Expected Touch Area)

Allowed:
- `app/modules/adjustment/` (module mới)
- `config/adjustments.yaml` (file mới)
- `tests/` (test mới cho adjustment)
- `docs/tasks/TASK-106-adjustment-engine.md`
- `PROJECT/PROJECT_PROGRESS.md`, `PROJECT/LO_TRINH_DE_HIEU.md`
- `docs/sessions/`

Không được đụng vào nếu chưa có Scope Expansion:
- `app/modules/domain/models.py`, `app/pipeline.py` — không sửa (task này
  không nối pipeline, không thêm field domain model — xem Out of Scope).
- `app/modules/mapping/`, `app/modules/orders/`, `app/modules/lead_source/`,
  `app/modules/pricing/` (đã DONE, không sửa trừ khi phát hiện lỗi thật).
- `docs/analysis/`, `docs/adr/`, `PROJECT/PROJECT_DECISIONS.md` (DEC-125 đã
  ghi trong phiên này, trước khi implement — không sửa thêm trừ khi phát
  sinh quyết định mới).
- Bất kỳ file nào của Track B.

## Subtask (Subtasks)
- [x] 106.1 `config/adjustments.yaml` — từ khóa AC + tier phương tiện + default AC
- [x] 106.2 `AirConditionerClassifier`
- [x] 106.3 `AdjustmentResolver`
- [x] 106.4 Test suite (17 test mới, 74/74 tổng PASS)

## Ready Gate
Dùng `governance/core/TASK_READY_GATE_STANDARD.md`.

- [x] Objective rõ ràng.
- [x] Scope đã được xác định.
- [x] Out-of-scope đã được xác định (ranh giới rõ với TASK-105/107/202/302/305).
- [x] Dependency (TASK-105, DEC-125) đã sẵn sàng.
- [x] Vùng tác động dự kiến đã được xác định.
- [x] Yêu cầu liên quan đã hiểu rõ (đặc tả §22 bước 9, DEC-125, DEC-103).
- [x] Tác động dữ liệu đã biết rõ: không có dữ liệu cá nhân mới; số tiền
      điều chỉnh là dữ liệu nghiệp vụ nhạy cảm ảnh hưởng lương/KPI
      (`governance/core/04_SECURITY_RULES.md`) nhưng chưa lộ ra UI/API ở
      Phase 1 — module chỉ trả giá trị đề xuất, không ghi vào bất kỳ record
      nào.
- [x] Tác động bảo mật đã biết rõ: không có, chưa có network/DB.
- [x] Không liên quan routing/API (Phase 1 thuần Python).
- [x] Không có migration (chưa có DB).
- [x] Difficulty/Risk/Blast Radius đã chấm điểm (4/4/4 — cao hơn TASK-105 vì
      ảnh hưởng trực tiếp KPI/lương và có rủi ro nhận diện điều hòa sai —
      xem DEC-125 mục Risk).
- [x] Agent tier đã chỉ định (B, escalation C).
- [x] Escalation trigger đã xác định (xem bên dưới).
- [x] Completion Gate đã hoàn thiện và **frozen** trước khi implement.

## Completion Gate
Dùng `governance/core/TASK_COMPLETION_GATE_STANDARD.md` và
`governance/core/EVIDENCE_STANDARD.md`.

### Functional

#### CHECK-106-01 — Qua kho/NCC giao tra đúng 3 tier theo phương tiện giao
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`pytest tests/test_adjustment_resolver.py -q` → 11/11 passed. Case
`test_qua_kho_motorbike_light_tier`, `test_qua_kho_motorbike_bulky_tier`,
`test_ncc_giao_car_tier` xác nhận đúng 3 mức `-50000`/`-100000`/`-200000`
VND (raw, không phải nghìn đồng) cho cả hai loại điều chỉnh.

Executed By:
Claude (session này)

Timestamp:
2026-08-23

#### CHECK-106-02 — KHBH/Thợ lắp chỉ có default khi is_air_conditioner=True
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`test_khbh_air_conditioner_has_default`, `test_tho_lap_air_conditioner_has_default`
xác nhận default đúng (`-50000`/`-200000`). `test_khbh_non_air_conditioner_has_no_default`
và `test_khbh_unknown_air_conditioner_status_has_no_default` xác nhận trả
`None` (không suy đoán, không coi 0) khi non-AC hoặc chưa biết trạng thái AC.

Executed By:
Claude (session này)

Timestamp:
2026-08-23

#### CHECK-106-03 — AirConditionerClassifier khớp từ khóa đúng trên ProductRaw thật
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`pytest tests/test_ac_classifier.py -q` → 6/6 passed. Case
`test_matches_diacritic_keyword_before_model_code` và
`test_matches_case_insensitively` mô phỏng đúng pattern dữ liệu thật ("Điều
hòa <hãng> <model>") đã quan sát ở dữ liệu tháng 01/2026, 06/2026 (DEC-125).
`test_non_air_conditioner_product_returns_false`,
`test_none_product_raw_returns_false_not_error` xác nhận không false-positive
và không lỗi khi thiếu dữ liệu.

Executed By:
Claude (session này)

Timestamp:
2026-08-23

#### CHECK-106-04 — Loại điều chỉnh/phương tiện không khớp không bao giờ suy đoán
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`test_qua_kho_without_delivery_method_has_no_default`,
`test_qua_kho_unknown_delivery_method_has_no_default`,
`test_unknown_adjustment_type_has_no_default` — cả ba xác nhận `amount is
None` với `source_of_value` mô tả đúng lý do (`Manual:NoDeliveryMethodMatch`
/ `Manual:UnknownAdjustmentType`), không rơi vào nhánh default sai.

Executed By:
Claude (session này)

Timestamp:
2026-08-23

### Architecture

#### CHECK-106-05 — Không nối vào app.pipeline; không import framework; không hard-code; tiền Decimal
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
```
$ git diff --stat HEAD -- app/pipeline.py app/modules/domain/models.py
(không có thay đổi — hai file này không bị đụng, đúng Out of Scope)

$ grep -rn "^import fastapi\|^from fastapi\|^import sqlalchemy\|^from sqlalchemy\|^import flask\|^from flask" app/modules/adjustment/
(không có kết quả)

$ grep -rnE "[0-9]{4,}" app/modules/adjustment/
(không có kết quả — số tiền cụ thể chỉ nằm trong config/adjustments.yaml,
không hard-code trong .py)

$ grep -rn "float(" app/modules/adjustment/
(không có kết quả)
```
`AdjustmentResolution.amount: Optional[Decimal]` — tiền luôn `Decimal`.
`pytest tests/ -q` → **74/74 passed** (57 test cũ + 17 test mới), không
regression.

Executed By:
Claude (session này)

Timestamp:
2026-08-23

## Tiêu Chí Hoàn Thành (Exit Criteria)
- [x] 100% REQUIRED check PASS — 5/5.
- [x] Không có lỗi nghiêm trọng chưa xử lý.
- [x] Evidence level E1 đạt được cho mọi check.
- [x] `PROJECT/PROJECT_PROGRESS.md` và `PROJECT/LO_TRINH_DE_HIEU.md` cập
      nhật đồng thời.
- [x] Session handoff đã viết (MAJOR task).
- [x] Toàn bộ 57 test cũ (TASK-101 + TASK-105) vẫn PASS (không regression) —
      74/74 tổng.

## Điều Kiện Kích Hoạt Leo Thang (Escalation Triggers)
- Phát hiện `ProductRaw` có biến thể viết điều hòa không khớp 2 từ khóa hiện
  tại trên dữ liệu thật ngoài 2 tháng mẫu — cần mở rộng `air_conditioner_keywords`
  và cân nhắc Review Queue thay vì false-negative âm thầm.
- Phát hiện chủ dự án muốn tier phương tiện khác nhau giữa `Qua kho` và
  `NCC giao` (hiện dùng chung bảng) — cần sửa `config/adjustments.yaml`,
  không sửa code.
- Khi TASK-202/302/305 (Phase 2/3) bắt đầu — cần xác nhận lại contract
  `AdjustmentResolution` (đặc biệt `source_of_value`) còn phù hợp với UI
  thật, hay cần mở rộng.

## Đăng Ký File Đã Thay Đổi (Changed Files Registry)

Created:
- `app/modules/adjustment/__init__.py`, `ac_classifier.py`, `adjustment_resolver.py`
- `config/adjustments.yaml`
- `tests/test_ac_classifier.py`, `test_adjustment_resolver.py`
- `docs/tasks/TASK-106-adjustment-engine.md`

Modified:
- `PROJECT/PROJECT_DECISIONS.md` — thêm DEC-125 (trước implementation)
- `PROJECT/PROJECT_PROGRESS.md`, `PROJECT/LO_TRINH_DE_HIEU.md` — đồng bộ
  theo "Giao thức Đóng Phiên"

Deleted:
- Không có.

Migration Impact:
- Không có (chưa có DB ở Phase 1).

## Ghi Chú (Notes)

**Vì sao task này không giống TASK-105 dù cùng nằm giữa TASK-101 và
TASK-107:** TASK-105 (`PendingPriceProvider`) đúng là "None cho mọi dòng" vì
Price Master **thật sự chưa tồn tại ở bất kỳ đâu** — một sự thật cố định.
TASK-106 khác về bản chất: `adjustment_type`/`delivery_method` không phải dữ
liệu còn thiếu chờ nguồn tương lai, mà là **quyết định của người dùng cho
từng đơn** — không có "giá trị đúng duy nhất" nào để tự động quét ra. Vì vậy
resolver ở đây nhận tham số từ caller (tương lai: UI) thay vì tự đọc từ
`RawRow`/`WorkingLine` như `price_engine` đã làm.
