# BÀN GIAO SESSION (SESSION HANDOFF)

Session ID:
S014

Task:
TASK-108A-1 — ConversionSchemeResolver (EmployeeGroup + ProductGroup)

Task Mode:
MAJOR

Project Profile:
PRODUCT

Status:
DONE — 16/16 REQUIRED check PASS, 151/151 test. **Independent Review #1→#4,
#4 PASS**, đã merge vào nhánh chính.

## Kết Quả (Result)

Ba vòng pre-implementation review (Gate v1 → v2 → v3) trước khi viết dòng
code nào. Mỗi vòng đóng một câu hỏi bằng **đo trên dữ liệu thật**, không bằng
suy đoán. Kết quả chốt thành **DEC-127** (8 quyết định) và **ADR-106**.

**Thay đổi mô hình:**
- `Nội thành` không còn là Employee. Vinh, Quý, Hiệp là **ba Employee thật**,
  cùng `employee_group = NOI_THANH`. Group là thứ dùng chung ConversionScheme,
  không phải thứ thay thế con người.
- Thêm dimension **`ProductGroup`** (`DIEN_MAY` / `GIA_DUNG`) ở **cấp product
  line** — vì đo được **118/10.609 OrderID** chứa đồng thời cả hai loại.
- `ConversionScheme` **hạ từ cấp Order xuống cấp line**; `LeadSource` giữ
  nguyên cấp Order (DEC-119 không đổi).

**Resolver:** tra 4 chiều `(employee, employee_group, lead_source,
product_group, ngày của đơn)`. `lead_source` là **lọc cứng**; trong số dòng
còn lại chọn dòng cụ thể nhất theo `specificity = 4×employee + 2×group +
1×product_group`; **hòa điểm là lỗi cấu hình** (engine từ chối chọn); không
khớp là `Unresolved` (không fallback).

## Subtask Đã Hoàn Thành (Subtasks Completed)
- [x] 108A-1.1 → 108A-1.10 (toàn bộ 10 subtask)

## Subtask Còn Lại (Subtasks Remaining)
- Không có. Independent Review #4 PASS, đã merge.

## Tóm Tắt Completion Gate (Completion Gate Summary)

Required:
16 (CHECK-108A1-01 đến 16)

PASS:
16

FAIL:
0

BLOCKED:
0

NOT_TESTED:
0

## Evidence Xác Minh (Verification Evidence)

| Check ID | Status | Evidence Level | Evidence | Executed By | Timestamp |
|---|---|---|---|---|---|
| CHECK-108A1-01 | PASS | E1 | 8 case A–G giữ nguyên scheme/rate sau đổi mô hình | Claude | 2026-08-23 |
| CHECK-108A1-02 | PASS | E1 | `verify_ads_rule.py` dùng production resolver/config, 36/36 | Claude | 2026-08-23 |
| CHECK-108A1-03 | PASS | E1 | Vinh/Quý/Hiệp ba danh tính riêng, cùng group, cùng 2 % | Claude | 2026-08-23 |
| CHECK-108A1-04 | PASS | E1 | Thêm NV mới chỉ bằng config | Claude | 2026-08-23 |
| CHECK-108A1-05 | PASS | E1 | Vinh + DIEN_MAY → 2 %, + GIA_DUNG → 8 % | Claude | 2026-08-23 |
| CHECK-108A1-06 | PASS | E1 | Ly + GIA_DUNG vẫn 5,5 %, không nhảy 8 % | Claude | 2026-08-23 |
| CHECK-108A1-07 | PASS | E1 | 1 OrderID 2 ProductGroup → 2 scheme | Claude | 2026-08-23 |
| CHECK-108A1-08 | PASS | E1 | Provenance DEFAULT ≠ MANUAL ≠ AUTO | Claude | 2026-08-23 |
| CHECK-108A1-09 | PASS | E1 | Effective-dating theo ngày đơn, kỳ cũ không đổi | Claude | 2026-08-23 |
| CHECK-108A1-10 | PASS | E1 | Không khớp **và unmapped** → `Unresolved`, không mượn tỉ lệ | Claude | 2026-08-23 |
| CHECK-108A1-11 | PASS | E1 | Hòa specificity → `AmbiguousSchemeConfigError` | Claude | 2026-08-23 |
| CHECK-108A1-12 | PASS | E1 | grep: 0 tên NV, 0 literal tỉ lệ trong business logic | Claude | 2026-08-23 |
| CHECK-108A1-13 | PASS | E1 | grep: không nhánh nào suy tỉ lệ từ LeadSource | Claude | 2026-08-23 |
| CHECK-108A1-14 | PASS | E1 | **55 ô cột F: 36 khớp độc lập, 0 lệch, 19 LIMITED** | Claude | 2026-08-23 |
| CHECK-108A1-15 | PASS | E1 | **14.389 dòng map đúng, 107 unmapped**; tiêu chí F1/F3/F5 hard-fail + F2/F4 warning | Claude | 2026-08-23 |
| CHECK-108A1-16 | PASS | E1 | `pytest tests/ -q` → 151/151, không regression | Claude | 2026-08-23 |

Chi tiết đầy đủ: `docs/tasks/TASK-108A-1-conversion-scheme-resolver.md`.

## File Đã Thay Đổi (Files Changed)

Created:
- `config/conversion_rates.yaml`
- `tests/test_reconcile_raw_criteria.py`, `tests/test_reconcile_raw_integration.py`
- `app/modules/conversion/` (`scheme_resolver.py`, `conversion_engine.py`)
- `app/modules/product/product_group.py`
- `tests/test_scheme_resolver.py`, `tests/test_conversion_engine.py`
- `tools/analysis/reconcile_conversion.py`
- `docs/adr/ADR-106-product-group-and-line-level-conversion.md`
- `docs/tasks/TASK-108A-1-conversion-scheme-resolver.md`
- `docs/sessions/S014-task-108a-1-conversion-scheme-resolver.md` (file này)

Modified:
- `config/employees.yaml`, `app/modules/mapping/employee_mapper.py`,
  `app/modules/domain/models.py`, `app/pipeline.py`
- `tests/test_employee_mapper.py`, `tests/test_pipeline.py`
- `tools/analysis/verify_ads_rule.py`
- `PROJECT/PROJECT_DECISIONS.md` (DEC-127),
  `docs/analysis/10_OPEN_QUESTIONS.md` (C11 số thật, C15 mới)
- `PROJECT/PROJECT_PROGRESS.md`, `PROJECT/LO_TRINH_DE_HIEU.md`

Deleted:
- Không có.

## Quyết Định Chính (Key Decisions)
- DEC-127 — 8 quyết định nghiệp vụ hợp nhất từ ba vòng review.
- ADR-106 — ProductGroup + hạ granularity ConversionScheme xuống cấp line.
- Specificity là **quy ước phân giải của ADR-106, không phải business rule bất
  biến**. Không tự mở rộng khi có dimension mới — phải mở lại ADR.
- `GIA_DUNG_8` khóa trên `NOI_THANH`, không trên `*` — 34 % dòng Gia dụng do
  `STANDARD_SALES` bán sẽ lệch nếu làm khác.

## Rủi Ro / Vướng Mắc (Risks / Blockers)

**ĐÃ GIẢI QUYẾT — Independent Review #1, Finding 1 (CRITICAL).** Tôi từng để
nhân viên chưa map rơi vào dòng `*` và nhận 5,5 %, rồi báo cáo đó là "đúng
luật, cần reviewer xác nhận". Reviewer xác định đây là **vi phạm DEC-127 §8**:
`unmapped` phải trả `Unresolved` / `rate=None` và vào Review Queue **trước**
khi xét universal rule. Đã sửa ở cả hai tầng (resolver + engine), có test.

Bài học ghi lại: khi tôi thấy một hành vi "có thể biện minh được" nhưng lệch
khỏi quyết định nghiệp vụ đã chốt, mặc định đúng là **theo quyết định đã
chốt**, không phải giữ nguyên rồi hỏi.

**RESIDUAL RISK — TD-001 (ghi theo yêu cầu Review #4):** F2/F4 là WARNING,
không làm exit non-zero. Chúng **phải được hiển thị rõ trong Review Queue/UI**
(TASK-110 trở đi), **không được âm thầm bỏ qua** — một F4 bị nuốt nghĩa là
một nhân viên thật đang bán hàng mà hệ thống không tính doanh số cho ai.
Xem `PROJECT/PROJECT_PROGRESS.md` → "Nợ Kỹ Thuật / Cảnh Báo Vận Hành".

**Rủi ro đã biết, đã chấp nhận (DEC-127 §5):** Phase 1 mọi dòng là
`DIEN_MAY`, nên dòng Gia dụng của kênh Nội thành quy đổi ở 2 % thay vì 8 %
cho tới khi có UI checkbox. `source_of_value = DEFAULT` làm điều này nhìn
thấy được.

**Chưa xác minh được:** hai chênh lệch số đơn giữa file thô và Summary (±1..8
đơn NV cá nhân; kênh Nội thành 1.250 đơn thật vs 0 trong báo cáo tay). Thuộc
TASK-101/109, không chặn 108A-1, đã ghi ở Gate v3.

## Hạng Mục Regression (Regression Items)
- `pytest tests/ -q` → **151/151** PASS (83 cũ + 68 mới). Không regression.
- Hai assert đổi từ `"Nội thành"` sang tên riêng là **hệ quả của DEC-127 §1**,
  rule đổi trước, test theo sau.
- **Engine bắt lỗi trong test của chính tôi:** bản nháp test effective-dating
  thêm dòng chính sách 2027 mà quên đóng dòng cũ → hai dòng cùng specificity
  → `AmbiguousSchemeConfigError`. **Test được sửa cho đúng cách đổi chính
  sách; rule giữ nguyên.** Đã thêm hẳn một test cho chính tình huống lỗi đó.

## Chưa Được Thay Đổi (Do Not Change Yet)
- `app/modules/pricing/`, `profit/`, `adjustment/`, `orders/`,
  `lead_source/`, `importing/`.
- `docs/adr/ADR-101…105`.
- Bất kỳ file nào của Track B.

## Session Tiếp Theo Được Khuyến Nghị (Next Recommended Session)

**TASK-110 — validation + Review Queue.** Là task PHASE-01 duy nhất còn lại
không phụ thuộc `EligibleKpiProfit`/`ConvertedRevenue`. Cũng là nơi bắt buộc
hiển thị F2/F4 (TD-001).

**TASK-109 (summary_engine) bị chặn một phần** — cột "DS quy đổi" và "LN KPI"
cần TASK-108B. Khi làm, **cần một check riêng** cấm gộp profit của các line
khác scheme rồi chia chung một tỉ lệ (ADR-106 §2).

**TASK-108B vẫn BLOCKED** — `EligibleCosts` (C15) chưa có định nghĩa nghiệp
vụ, không được giả định `= 0`.

## Ghi Chú Về Quy Trình (Process Note)

Bốn vòng independent review trên một task đã "xong" theo test nội bộ. Bản đầu
(`98142af`) có 119/119 test PASS và reconciliation tự báo "52 khớp, 0 lệch".
Reviewer độc lập vẫn tìm ra 8 finding qua 3 vòng, gồm một lỗi CRITICAL ảnh
hưởng tiền lương và một trường hợp "khớp giả" 16/52 ô. Chi tiết từng vòng:
`docs/tasks/TASK-108A-1-conversion-scheme-resolver.md` → "Lịch Sử Independent
Review".

## File Agent Tiếp Theo Cần Đọc (Files Next Agent Should Read)
- `CLAUDE.md`
- `PROJECT/PROJECT_PROGRESS.md` (mục "Trạng thái Task hiện tại")
- `docs/tasks/TASK-108A-1-conversion-scheme-resolver.md`
- `docs/adr/ADR-106-product-group-and-line-level-conversion.md`
- `PROJECT/PROJECT_DECISIONS.md` (DEC-127)
- `docs/analysis/10_OPEN_QUESTIONS.md` (C15)
- `app/modules/conversion/`, `app/modules/product/` (code đã có)
