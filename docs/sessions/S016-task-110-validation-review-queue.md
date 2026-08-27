# BÀN GIAO SESSION (SESSION HANDOFF)

Session ID:
S016

Task:
TASK-110 — Validation + Review Queue

Task Mode:
MAJOR

Project Profile:
PRODUCT

Status:
**IMPLEMENTED — awaiting Independent Review.** 16/17 REQUIRED check PASS;
CHECK-110-16 **BLOCKED** (thiếu file thô production — chủ dự án cho phép giữ,
chặn DONE không chặn IMPLEMENTED). **207/207 test PASS** (56 mới, 0
regression). **Chưa merge.** Không tự chuyển sang DONE.

## Kết Quả (Result)

Chủ dự án freeze Completion Gate kèm một làm rõ bổ sung cho F-05
(multi-employee Order). Triển khai đúng 7 loại cảnh báo của bảng phạm vi đã
freeze, không mở rộng sang TASK-108B/109.

### Bảy loại, tám mã

`Missing` mang hai mã vì DEC-128 §1 tách nó theo hình dạng: per-row và tổng hợp.

| Mã | Cơ sở | Kết quả Phase 1 |
|---|---|---|
| `Missing` | thiếu ngày / OrderID / nhân viên / SL / doanh số | per-row |
| `Missing.PurchasePrice` | `price_source == Pending` | **1 mục** mang `affected_count` |
| `Suspicious` | SL ≤ 0, giá bán = 0, giá nhập > giá bán, LN kế toán âm | hai quy tắc sau **nằm im** (không có giá nhập) |
| `Suspicious.ERP` | `source_profit < 0` | loại riêng, nhãn "CHƯA kiểm chứng" |
| `OrderInconsistency` | khác nhân viên / khác ngày trên cùng đơn | **chỉ phát hiện** |
| `SourceClassification` | `lead_source_manual != lead_source_auto` | 0 phát hiện thật **theo cấu tạo** |
| `Duplicate` | trùng `row_hash` trong cùng batch | WARNING |
| `EmployeeMapping` | F1–F5 | **TD-001** |

### TD-001 — đã xử lý

F2/F4 trước đây **chỉ tồn tại trong `tools/analysis/reconcile_conversion.py`**,
một script chạy tay ngoài đường đi của `run_import()`. Nay tiêu chí F1–F5 nằm
ở `app/modules/validation/employee_mapping.py` (production), và script phân
tích **import ngược lại đúng các tên đó**. Hai đường dùng chung một bộ tiêu
chí thay vì hai bản cài đặt có thể trôi khỏi nhau.

Chạy `run_import()` trên fixture tổng hợp cho ra **3 mục F2 + 1 mục F4** ngay
trong `ImportResult.review_queue`.

`reconcile_conversion.py` giữ nguyên hành vi: hai file test của TASK-108A-1
**không sửa một dòng nào** và vẫn 24/24 PASS (CHECK-110-14).

### F-05 — làm rõ của chủ dự án khi freeze

Cảnh báo đơn nhiều nhân viên **không** sửa employee, **không** chia KPI,
**không** chọn người nhận doanh số. Nó mang đủ provenance để sau này quyết
định: `OrderID`, `employees_found`, `source_rows`, `legacy_selected` — và
thông điệp nói thẳng rằng nhân viên của dòng đầu tiên là **hành vi legacy**,
không phải quyền sở hữu đã xác minh.

`_selling_identity()` so sánh **danh tính bán hàng**, không chỉ tên đã map:
một dòng đã map cạnh một dòng chưa map trên cùng đơn vẫn là mâu thuẫn — đó là
ca tệ nhất, doanh số của người chưa map rơi vào tay người được chọn trước.

## Subtask Đã Hoàn Thành (Subtasks Completed)
- [x] 110.1 → 110.9

## Subtask Còn Lại (Subtasks Remaining)
- [ ] 110.10 — Đối chiếu dữ liệu thật (CHECK-110-16). **BLOCKED**, cần file thô production.

## Tóm Tắt Completion Gate (Completion Gate Summary)

Required:
17

PASS:
16

FAIL:
0

BLOCKED:
1 (CHECK-110-16)

NOT_TESTED:
1 (CHECK-110-18, RECOMMENDED — Independent Review)

## Evidence Xác Minh (Verification Evidence)

Bảng đầy đủ từng check: `docs/tasks/TASK-110-validation-review-queue.md`.
Tóm tắt các bằng chứng đứng độc lập:

| Hạng mục | Status | Evidence Level | Evidence | Executed By | Timestamp |
|---|---|---|---|---|---|
| Regression | PASS | E1 | `python3 -m pytest tests/ -q` → **207 passed in 1.30s**; baseline `c7a1b24` là 151 | Claude | 2026-08-23 |
| `reconcile_conversion.py` không đổi | PASS | E1 | 24/24 PASS, hai file test **không sửa**; `--help` exit 0 | Claude | 2026-08-23 |
| Không literal nghiệp vụ | PASS | E1 | `grep -rnE "<8 tên NV>\|NOI_THANH\|Decimal(\"0.N\")" app/modules/validation/*.py` → **0 kết quả** | Claude | 2026-08-23 |
| Không suy giá nhập từ ERP | PASS | E1 | `grep -rn "source_profit" app/modules/validation/` → **2 dòng**, cả hai trong `detect_suspicious_erp` | Claude | 2026-08-23 |
| TD-001 F2/F4 trên luồng production | PASS | E1 | `run_import()` fixture tổng hợp → 3 mục F2 + 1 mục F4 trong `review_queue` | Claude | 2026-08-23 |
| Validator governance | PASS | E1 | `validate_structure` / `validate_project_state` / `validate_evidence` / `validate_task_completion` PASS | Claude | 2026-08-23 |

## File Đã Thay Đổi (Files Changed)

Created:
- `config/validation.yaml`
- `app/modules/validation/{__init__,models,rules,employee_mapping,validator}.py`
- `tests/test_validation_rules.py` (25), `tests/test_validation_employee_mapping.py` (11), `tests/test_validation_pipeline.py` (20)
- `docs/sessions/S016-task-110-validation-review-queue.md` (file này)

Modified:
- `app/pipeline.py` — bước 11, `ImportResult.review_queue`
- `tools/analysis/reconcile_conversion.py` — **chỉ trích xuất** F1–F5, import ngược lại
- `docs/tasks/TASK-110-validation-review-queue.md` — freeze, kết quả 16/17, làm rõ F-05
- `PROJECT/PROJECT_PROGRESS.md` — TD-001 đã xử lý, trạng thái task, roadmap
- `PROJECT/LO_TRINH_DE_HIEU.md` — mục "Có gì mới", dòng 14 (cùng một lần sửa)

Deleted:
- Không có.

**Không đụng:** `app/modules/domain/models.py` (không thêm field),
`orders/`, `conversion/`, `profit/`, `pricing/`, `adjustment/`,
`lead_source/`, `mapping/`, `importing/`, `config/employees.yaml`,
`config/conversion_rates.yaml`, `config/lead_source.yaml`, ADR-101…106,
`tests/factories.py`, mọi file Track B.

## Quyết Định Chính (Key Decisions)
- Tiêu chí F1–F5 đặt ở `app/modules/validation/` chứ không ở `app/modules/mapping/` — mapping nằm ngoài Expected Touch Area đã freeze.
- Hướng phụ thuộc: **production sở hữu tiêu chí, script phân tích tiêu thụ**. Ngược lại sẽ khiến `app/` phụ thuộc `tools/`.
- Helper test đặt cục bộ trong các file `test_validation_*.py` thay vì sửa `tests/factories.py` — giữ đúng Scope Lock.

## Rủi Ro / Vướng Mắc (Risks / Blockers)

**BLOCKER cho DONE — CHECK-110-16.** Chưa đối chiếu được số phát hiện từng
loại với các con số đã đo (2 thiếu NV / 52 thiếu SL / 1.912 ERP âm / 1.261
dòng phụ / 11.765 chờ giá nhập). File thô production không có trong repo và
không có trong container. Giảm nhẹ một phần:
`test_config_keyword_list_matches_the_measured_evidence_filter` khóa danh sách
từ khóa vào **đúng bộ lọc regex đã sinh ra con số 1.261**, nên khi có file
thật, phép đối chiếu là so số chứ không phải chỉnh ngưỡng cho khớp.

**CẦN REVIEWER SOI — F1/F3/F5 cũng vào hàng chờ.** Bảng phạm vi freeze ghi V7
là "F2 và F4". `evaluate_raw_mapping()` trả cả `hard_failures` trong cùng một
lượt; tôi đưa cả ba vào queue ở mức `ERROR` thay vì bỏ. Lý do: chúng là
invariant, nuốt một invariant đã vi phạm là đúng thứ task này tồn tại để chặn.
Đây là **tập cha** của phạm vi đã freeze — không đổi quyết định nào, không đổi
check nào, không chặn import nào. **Ghi ra để reviewer bác nếu thấy không nên.**

**CHƯA LÀM, CÓ CHỦ Ý — vế "dữ liệu nguồn mâu thuẫn" của §18.** Đặc tả viết
"cùng OrderID nhưng khác nhân viên **hoặc dữ liệu nguồn mâu thuẫn**". Vế sau
không có định nghĩa nghiệp vụ nào nói "mâu thuẫn" là gì ngoài nhân viên và
ngày. Triển khai hai vế đo được, **không đoán** vế thứ ba. Cần định nghĩa
trước nếu chủ dự án muốn nó.

**RỦI RO TỒN DƯ (DEC-128 §4).** Cho tới khi có người duyệt hàng chờ, đơn hai
nhân viên vẫn xuất ra con số sai KPI cho cả hai. Công cụ làm nó **nhìn thấy
được**, không làm nó **không xảy ra**. Nên đo quy mô thật ở GATE-01.

**PHỤ THUỘC MỀM.** Danh sách từ khóa dòng phụ trong `config/validation.yaml`
và bảng Classification §17 (TASK-103) nói về cùng một tập dòng. TASK-103 phải
rà lại danh sách này khi làm.

**TD-001 chưa đóng hoàn toàn.** F2/F4 nay nằm trong `ImportResult`, nhưng màn
hình duyệt thật là TASK-305. Đóng hẳn khi TASK-305 xong.

## Hạng Mục Regression (Regression Items)
- `python3 -m pytest tests/ -q` → **207/207 PASS** (151 cũ + 56 mới). 0 regression.
- Không sửa một test cũ nào để làm nó PASS.
- `validate_reference_integrity.py` vẫn còn **3 reference chưa phân giải**, tất
  cả thuộc `docs/tasks/TASK-REM-T06-repository-root-hygiene.md` (Track B,
  forward reference tới ba file ở root mà chính task đó sẽ tạo). Tiền tồn,
  không phải do phiên này.

## Chưa Được Thay Đổi (Do Not Change Yet)
- **Không merge TASK-110** — chờ Independent Review.
- `app/modules/orders/order_builder.py` — DEC-128 §4 giữ nguyên hành vi legacy.
- `app/modules/domain/models.py` — không thêm field cho validation.
- TASK-108B (C15 `EligibleCosts` chưa có định nghĩa), TASK-109 (chặn một phần).
- Bất kỳ file nào của Track B.

## Session Tiếp Theo Được Khuyến Nghị (Next Recommended Session)

**S017 — Independent Review cho TASK-110.** Điểm nên soi trước:

1. **F1/F3/F5 vào hàng chờ** — vượt bảng phạm vi đã freeze hay là hệ quả đúng?
2. **`_selling_identity()`** — coi dòng chưa map là một danh tính riêng có làm
   V4 bắn quá tay trên dữ liệu thật không? Chưa đo được vì thiếu file thật.
3. **Danh sách từ khóa dòng phụ** — `"phí "` có dấu cách cuối là thứ tái hiện
   con số 1.261, nhưng nó mong manh. Một tên sản phẩm thật chứa "phí " sẽ bị
   hạ mức nhầm.
4. **`Missing` field `employee`** — hiện coi cả `unmapped` lẫn `inactive` là
   thiếu. `inactive` vẫn là một người có thật; có nên là loại khác không?
5. **CHECK-110-16** — điều kiện duy nhất còn lại để DONE.

Tiền lệ TASK-108A-1: 119/119 test nội bộ PASS mà reviewer độc lập vẫn tìm ra
8 finding qua 3 vòng, gồm một lỗi CRITICAL ảnh hưởng tiền lương.

## Ghi Chú Về Quy Trình (Process Note)

Gate Review ở S015 mất một lượt hội thoại để hỏi 4 câu. Cả 4 đều đổi cách viết
code: nếu code thẳng từ bảng §18, Review Queue sẽ có 11.765 mục "thiếu giá
nhập" cộng hàng nghìn mục "vận chuyển SL = 0" — đúng chữ nghĩa, vô dụng khi
dùng. Chi phí hỏi trước rẻ hơn hẳn một vòng viết lại.

## File Agent Tiếp Theo Cần Đọc (Files Next Agent Should Read)
- `docs/tasks/TASK-110-validation-review-queue.md` (Completion Gate + "Ghi chú triển khai cần reviewer soi")
- `docs/sessions/S015-task-110-gate-readiness.md` (Gate Review)
- `PROJECT/PROJECT_DECISIONS.md` (**DEC-128**, DEC-103, DEC-110, DEC-113, DEC-127)
- `app/modules/validation/` (5 file), `config/validation.yaml`
- `tests/test_validation_*.py` (3 file, 56 test)
- `PROJECT/PROJECT_PROGRESS.md` → "Nợ Kỹ Thuật / Cảnh Báo Vận Hành" (TD-001)
