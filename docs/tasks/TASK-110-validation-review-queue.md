# TASK-110 — Validation + Review Queue

## Metadata

Status:
PLANNED — Ready Gate đã rà soát đầy đủ, Completion Gate đã hoàn thiện,
**chờ chủ dự án freeze** trước khi chuyển READY.

Phase:
PHASE-01 — Engine tính toán

Task Mode:
MAJOR

Primary Agent Tier:
B

Escalation Tier:
C

Difficulty:
3/5 — nâng từ 2/5 khi chấm sơ bộ. Lý do: phạm vi thật là **7 loại cảnh báo**
(5 loại của §18 + tách `Suspicious` làm hai cơ sở khác nhau theo DEC-128 §2 +
TD-001 F2/F4), không phải 5; và toàn bộ ngưỡng/từ khóa phải nằm trong config.

Risk:
3/5 — nâng từ 2/5 khi chấm sơ bộ. Lý do: TD-001. Một cảnh báo F4 bị nuốt
nghĩa là một nhân viên thật đang bán hàng mà hệ thống không tính doanh số cho
ai (DEC-127 §8 → `Unresolved` → không vào KPI của ai). Đây là rủi ro tiền
lương, không phải rủi ro hiển thị. Theo `governance/core/EVIDENCE_STANDARD.md`,
Risk 3 → **E1 bắt buộc** cho mọi check REQUIRED.

Blast Radius:
2/5 — giữ nguyên. Module mới, chỉ **đọc** `WorkingLine`/`Order`, không sửa
engine nào đang chạy, không thêm field vào domain model.

Project Profile:
PRODUCT

## Mục Tiêu (Objective)

Triển khai mục §18 đặc tả: phát hiện dữ liệu bất thường trong một lần import
và đưa vào một **Review Queue trong bộ nhớ**, để không một dòng dữ liệu lỗi
nào âm thầm đi vào báo cáo.

Ràng buộc cứng của đặc tả §18: **không bao giờ chặn toàn bộ import**. Review
Queue là kết quả *bên cạnh* dữ liệu đã xử lý, không phải cổng chặn nó.

## Phạm Vi (Scope)

Bảy loại cảnh báo. Năm loại đầu là §18 đặc tả; V3 tách ra theo DEC-128 §2;
V7 là TD-001.

| Mã | Loại | Cơ sở phát hiện | Ghi chú |
|---|---|---|---|
| V1 | `Missing` | Thiếu ngày, OrderID, nhân viên, SL, doanh số | Per-row |
| V1-P | `Missing` — giá nhập | `price_source == Pending` | **Nén thành MỘT mục tổng hợp** (DEC-128 §1) |
| V2 | `Suspicious` — tính toán | `accounting_profit < 0`; `accounting_purchase_price > sell_price`; `quantity <= 0`; `sell_price == 0` | Phase 1 hai điều kiện đầu **nằm im** (0 phát hiện) vì `accounting_profit is None` ở 100% dòng |
| V3 | `Suspicious` — ERP | `source_profit < 0` | **Loại riêng**, nhãn ghi rõ là tín hiệu từ ERP chưa kiểm chứng (DEC-128 §2) |
| V4 | `Order inconsistency` | Cùng `order_id`, khác `employee_normalized` (hoặc khác `date`) | **Chỉ phát hiện**, không đổi cách tính (DEC-128 §4) |
| V5 | `Source classification` | `lead_source_manual` có giá trị và khác `lead_source_auto` | Phase 1 chưa có nguồn ghi override → 0 phát hiện thật, kiểm bằng fixture |
| V6 | `Duplicate` | Trùng `row_hash` **trong cùng một lần import** | WARNING, không phải lỗi (DEC-128 §3) |
| V7 | `Employee mapping` | F2 và F4 của `reconcile_conversion.py`, chuyển vào luồng production | **TD-001** |

Ngoài ra:
- Mỗi mục trong queue mang: mã loại, mức độ (`INFO`/`WARNING`/`ERROR`), tham
  chiếu ngược `source_file` + `source_row` (hoặc `order_id`), và một câu mô tả
  đọc được bằng tiếng Việt.
- Toàn bộ **từ khóa dòng phụ** và mọi ngưỡng nghiệp vụ nằm trong
  `config/validation.yaml`. Không literal nào trong `app/`.
- `run_import()` trả thêm `review_queue` trong `ImportResult`.

## Ngoài Phạm Vi (Out of Scope)

Không được đụng tới nếu chưa có SCOPE EXPANSION:

- **Lưu trữ Review Queue** (bảng, migration) — TASK-201, PHASE-02.
- **Audit trail / override thật** (`excluded_from_report`, hoàn tác, ai sửa
  gì) — TASK-202. DEC-110 mô tả một màn hình duyệt giữ/loại ~1.261 dòng phụ;
  TASK-110 chỉ **phát hiện và phân loại**, không xây cơ chế duyệt.
- **Màn hình Review Queue** — TASK-305, PHASE-03.
- **Product / Transaction Classification đầy đủ** (§17 đặc tả, bảng cấu hình
  từng loại tính vào SP/doanh số/lợi nhuận/DS quy đổi) — TASK-103. TASK-110
  chỉ dùng một danh sách từ khóa để **hạ mức cảnh báo**, không phải để quyết
  định dòng nào tính vào đâu.
- **Chống trùng khi import lại cùng một file** (cần persistence) — TASK-201.
- **Đổi hành vi của `order_builder`** — hiện lấy nhân viên của dòng đầu tiên.
  DEC-128 §4 giữ nguyên hành vi này; đổi nó cần một DEC mới.
- **TASK-108B** (Converted Revenue) và **TASK-109** (summary_engine).
- Thêm bất kỳ field nào vào `WorkingLine` / `Order`.

## Phụ Thuộc (Dependencies)

| Task | Trạng thái | Ghi chú |
|---|---|---|
| TASK-101 | **DONE** | `RawRow.row_hash`, `source_file`, `source_row` — đầu vào của V6 |
| TASK-105 | **DONE** | `price_source` — đầu vào của V1-P |
| TASK-107 | **DONE** | `accounting_profit` — đầu vào của V2 |
| TASK-108A-1 | **DONE** | `employee_mapping_status`, `conversion_scheme_final` |
| GATE-00 | **PASS** (DEC-122) | |
| TASK-106 | DONE | Không phải phụ thuộc thật — `adjustment` không tham gia validation |

**Phụ thuộc được miễn trừ tường minh (waived):**

- **TASK-103 — Product/Transaction Classification.** Chưa làm. Nếu không có
  nó, V2 không phân biệt được `SL ≤ 0` / `giá bán = 0` của một dòng lỗi thật
  với 1.261 dòng phụ hợp lệ (`Chi phí vận chuyển` 1.074, `Chi phí lắp đặt` 84,
  `Chênh VAT` 33…). **Miễn trừ theo DEC-128 §3**: dùng danh sách từ khóa
  trong config để hạ các dòng đó xuống `INFO`. Đây là biện pháp giảm nhiễu,
  **không** thay thế §17 — TASK-103 vẫn phải làm.

**Câu hỏi mở còn liên quan (không chặn):**

- **C11** — 107 dòng nhân viên chưa map trên file toàn công ty 14.389 dòng
  (88 dòng / 6 giá trị trên bộ 6 tháng 11.765 dòng). Mặc định hiện tại đã
  đúng: vào Review Queue loại `Missing`, không tính KPI cho ai. TASK-110
  hiện thực hóa đúng mặc định đó, không cần C11 đóng trước.
- **C15** — `EligibleCosts`. Chặn TASK-108B, **không** chặn TASK-110.

## Chặn (Blocks)

- TASK-111 (excel_exporter) — sheet Audit/Overrides cần đầu ra của Review Queue.
- TASK-305 (màn hình review queue) — cần mô hình dữ liệu của queue.

## An Toàn Để Chạy Song Song Với (Parallel-Safe With)

- TASK-108B, TASK-109. TASK-110 chỉ **đọc** kết quả của các engine đó, không
  sửa chúng. Nếu TASK-109 chạy trước và đổi `ImportResult`, hai task sẽ đụng
  nhau ở đúng một chỗ — `app/pipeline.py` — cần merge tay.

## Phạm Vi Tác Động Dự Kiến (Expected Touch Area)

Allowed:
- `app/modules/validation/` (mới)
- `config/validation.yaml` (mới)
- `app/pipeline.py` — chỉ thêm bước 11 và trường `review_queue` vào `ImportResult`
- `tests/test_validation_*.py` (mới)
- `tools/analysis/reconcile_conversion.py` — chỉ **trích xuất** logic F2/F4 ra
  chỗ dùng chung; hành vi và output của script phải **không đổi**
- `docs/tasks/TASK-110-validation-review-queue.md`, `docs/sessions/S015-*.md`
- `PROJECT/PROJECT_PROGRESS.md`, `PROJECT/LO_TRINH_DE_HIEU.md`

Không được đụng vào nếu chưa có Scope Expansion:
- `app/modules/domain/models.py` — **không thêm field**
- `app/modules/conversion/`, `profit/`, `pricing/`, `adjustment/`,
  `orders/`, `lead_source/`, `mapping/`, `importing/`
- `config/employees.yaml`, `config/conversion_rates.yaml`, `config/lead_source.yaml`
- `docs/adr/ADR-101…106`
- Bất kỳ file nào của Track B (governance remediation)

## Subtask (Subtasks)

- [ ] 110.1 — `config/validation.yaml`: từ khóa dòng phụ, ngưỡng, bật/tắt từng loại.
- [ ] 110.2 — Mô hình `ReviewItem` / `ReviewQueue` (dataclass thuần, mức độ + tham chiếu ngược).
- [ ] 110.3 — V1 + V1-P (`Missing`, giá nhập nén tổng hợp).
- [ ] 110.4 — V2 + V3 (`Suspicious`, hai cơ sở tách bạch).
- [ ] 110.5 — V4 (`Order inconsistency`, chỉ phát hiện).
- [ ] 110.6 — V5 (`Source classification`).
- [ ] 110.7 — V6 (`Duplicate` theo `row_hash` trong batch).
- [ ] 110.8 — V7: trích F2/F4 ra module dùng chung, nối vào `run_import()`; giữ nguyên hành vi `reconcile_conversion.py`.
- [ ] 110.9 — Nối vào `app/pipeline.py` làm bước 11.
- [ ] 110.10 — Đối chiếu trên dữ liệu thật (CHECK-110-16).

## Ready Gate

Dùng `governance/core/TASK_READY_GATE_STANDARD.md` — MAJOR Ready Gate.

- [x] Objective rõ ràng.
- [x] Scope đã được xác định — 7 loại, bảng ở trên.
- [x] Out-of-scope đã được xác định — 8 mục, kèm task chủ quản.
- [x] Dependency đã DONE hoặc được miễn trừ rõ ràng — TASK-103 miễn trừ theo DEC-128 §3.
- [x] Vùng tác động dự kiến đã được xác định.
- [x] Yêu cầu liên quan đã được hiểu rõ — §18 đặc tả đọc nguyên văn; 4 khoảng trống nghiệp vụ đã hỏi và đã có câu trả lời (DEC-128).
- [x] Tác động dữ liệu đã biết rõ — chỉ đọc, không ghi, không thêm field, RAW bất biến (ADR-102).
- [x] Tác động bảo mật đã biết rõ — mục Review Queue **không được** chứa tên/SĐT/địa chỉ khách hàng; chỉ tham chiếu `source_file` + `source_row` (`governance/core/04_SECURITY_RULES.md` §6, `governance/product/17_DATA_GOVERNANCE_PRIVACY.md`).
- [x] Tác động routing/API — không có ở Phase 1. `GET /api/v1/review` là TASK-203 (ADR-105 §2).
- [x] Điều kiện tiên quyết migration — không áp dụng, chưa có database.
- [x] Difficulty đã chấm — 3/5 (nâng từ 2, có lý do).
- [x] Risk đã chấm — 3/5 (nâng từ 2, có lý do: TD-001).
- [x] Blast Radius đã chấm — 2/5.
- [x] Agent tier chính đã chỉ định — B.
- [x] Escalation trigger đã xác định — mục dưới.
- [x] Completion Gate đã hoàn thiện — 17 check bên dưới.
- [ ] **Completion Gate đã frozen** — chờ chủ dự án. **Đây là mục duy nhất còn thiếu.**

## Completion Gate

Dùng `governance/core/TASK_COMPLETION_GATE_STANDARD.md` và
`governance/core/EVIDENCE_STANDARD.md`. Risk 3 → **E1 bắt buộc** cho mọi
check REQUIRED.

### Functional

#### CHECK-110-01 — Bảy loại cảnh báo tồn tại và phân biệt được
Priority: REQUIRED · Evidence Level: E1 · Status: NOT_TESTED

Evidence: chạy `run_import()` trên fixture tổng hợp chứa đủ 7 tình huống; mỗi
loại trả về đúng mã loại riêng, không loại nào nuốt loại nào.

#### CHECK-110-02 — Không bao giờ chặn toàn bộ import
Priority: REQUIRED · Evidence Level: E1 · Status: NOT_TESTED

Evidence: fixture mà **mọi** dòng đều sinh cảnh báo → `run_import()` vẫn trả
`ImportResult` đầy đủ, không raise, `orders` không rỗng. Ràng buộc nguyên văn
của §18 đặc tả.

#### CHECK-110-03 — `Missing` giá nhập nén thành một mục tổng hợp
Priority: REQUIRED · Evidence Level: E1 · Status: NOT_TESTED

Evidence: fixture N dòng đều `price_source == Pending` → **đúng 1** mục trong
queue, mang `affected_count == N`, **không phải** N mục. DEC-128 §1.

#### CHECK-110-04 — `Missing` per-row đúng số lượng
Priority: REQUIRED · Evidence Level: E1 · Status: NOT_TESTED

Evidence: fixture với số dòng thiếu ngày / OrderID / nhân viên / SL / doanh số
đã biết trước → số mục khớp chính xác từng loại.

#### CHECK-110-05 — V2 nằm im khi chưa có giá nhập, sống dậy khi có
Priority: REQUIRED · Evidence Level: E1 · Status: NOT_TESTED

Evidence: (a) với `PendingPriceProvider`, hai điều kiện `accounting_profit < 0`
và `giá nhập > giá bán` cho **0** phát hiện và không crash; (b) inject một
`PriceProvider` trả giá nhập > giá bán → cảnh báo bắn đúng. Chứng minh quy tắc
được viết đúng chứ không phải bị bỏ quên.

#### CHECK-110-06 — V3 tách bạch khỏi V2, không suy giá nhập từ ERP
Priority: REQUIRED · Evidence Level: E1 · Status: NOT_TESTED

Evidence: (a) V3 mang mã loại và nhãn riêng, ghi rõ nguồn là ERP chưa kiểm
chứng; (b) `grep` chứng minh không đường code nào dùng `source_profit` để suy
ra `accounting_purchase_price` hay `accounting_profit` — DEC-103,
`docs/analysis/01_DATA_MAPPING.md` §3.

#### CHECK-110-07 — Dòng phụ hạ xuống INFO, dòng sản phẩm thật thì không
Priority: REQUIRED · Evidence Level: E1 · Status: NOT_TESTED

Evidence: `Chi phí vận chuyển` với `SL = 0` → `INFO`; một sản phẩm thật với
`SL = 0` → `WARNING`/`ERROR`. DEC-128 §3.

#### CHECK-110-08 — Từ khóa và ngưỡng nằm trong config
Priority: REQUIRED · Evidence Level: E1 · Status: NOT_TESTED

Evidence: `grep` trên `app/modules/validation/` — 0 literal từ khóa dòng phụ,
0 tên nhân viên, 0 tỉ lệ, 0 ngưỡng nghiệp vụ. Cùng chuẩn đã áp cho TASK-108A-1
(CHECK-108A1-12).

#### CHECK-110-09 — V4 phát hiện nhưng không đổi kết quả tính
Priority: REQUIRED · Evidence Level: E1 · Status: NOT_TESTED

Evidence: (a) đơn có hai `employee_normalized` khác nhau → đúng 1 mục V4;
(b) `conversion_scheme_final` và `conversion_rate_final` của mọi dòng **giống
hệt** khi bật và khi tắt validation. DEC-128 §4 — validation không được là
đường lén đổi business rule.

#### CHECK-110-10 — V5 chỉ bắn khi override thật sự khác rule
Priority: REQUIRED · Evidence Level: E1 · Status: NOT_TESTED

Evidence: fixture 3 case — `manual is None` → không bắn; `manual == auto` →
không bắn; `manual != auto` → bắn. Ghi rõ trong báo cáo: Phase 1 chưa có
nguồn ghi `lead_source_manual`, nên loại này cho 0 phát hiện trên dữ liệu
thật **theo cấu tạo**, không phải vì code sai.

#### CHECK-110-11 — V6 trùng theo `row_hash` trong batch
Priority: REQUIRED · Evidence Level: E1 · Status: NOT_TESTED

Evidence: hai dòng nội dung giống hệt → 1 mục V6 mức `WARNING`; hai dòng khác
dù chỉ một ký tự → không bắn. Báo cáo ghi rõ chống trùng khi import lại file
là TASK-201.

#### CHECK-110-12 — TD-001: F2 xuất hiện trong Review Queue của production
Priority: REQUIRED · Evidence Level: E1 · Status: NOT_TESTED

Evidence: `employees.yaml` fixture có một nhân viên `active`, hiệu lực trong
kỳ, không khớp dòng nào → mục F2 có mặt trong `ImportResult.review_queue`,
**không chỉ** trong output của `tools/analysis/reconcile_conversion.py`.

#### CHECK-110-13 — TD-001: F4 xuất hiện, và F2/F4 không làm hỏng import
Priority: REQUIRED · Evidence Level: E1 · Status: NOT_TESTED

Evidence: (a) một tên chưa map có số dòng ≥ nhân viên đã map nhỏ nhất → mục F4
trong queue; (b) `run_import()` không raise và trả đủ dữ liệu khi có F2/F4 —
đúng bản chất WARNING của TD-001.

#### CHECK-110-14 — `reconcile_conversion.py` không đổi hành vi
Priority: REQUIRED · Evidence Level: E1 · Status: NOT_TESTED

Evidence: `tests/test_reconcile_raw_criteria.py` và
`tests/test_reconcile_raw_integration.py` PASS không sửa đổi sau khi trích
logic F2/F4 ra dùng chung. Đây là artifact bằng chứng của TASK-108A-1
(CHECK-108A1-15) — làm lệch nó là làm hỏng bằng chứng đã ship.

#### CHECK-110-15 — Không regression
Priority: REQUIRED · Evidence Level: E1 · Status: NOT_TESTED

Evidence: `python3 -m pytest tests/ -q` — 151 test hiện có vẫn PASS.
Baseline đã đo tại `c7a1b24`: **151 passed in 1.40s**.

#### CHECK-110-16 — Đối chiếu trên dữ liệu thật
Priority: REQUIRED · Evidence Level: E1 · Status: **BLOCKED**

Evidence: chạy validation trên file thô thật, số phát hiện từng loại đối chiếu
với các con số đã đo trong `docs/analysis/_evidence/evidence.json`:

| Loại | Số đã đo (bộ 6 tháng, 11.765 dòng) |
|---|---:|
| `Missing` — thiếu nhân viên | 2 |
| `Missing` — thiếu SL | 52 |
| V3 — ERP báo lợi nhuận âm | 1.912 |
| Dòng phụ (hạ xuống INFO) | 1.261 (30 loại) |
| V1-P — chờ giá nhập | 11.765 (1 mục tổng hợp) |

Mọi chênh lệch phải giải thích bằng văn bản, **không được** chỉnh ngưỡng cho
khớp — cùng quy tắc đã áp ở CHECK-101-08.

**Lý do BLOCKED:** file thô thật không có trong repo (`.gitignore` loại
`*.xlsx` và `data/samples/`, đúng `governance/product/17_DATA_GOVERNANCE_PRIVACY.md`) và không
có trong container của session này. Check này chỉ đóng được ở môi trường có
file thật. **Nó chặn DONE, không chặn IMPLEMENTED.**

### Security / Data

#### CHECK-110-17 — Không rò rỉ dữ liệu cá nhân khách hàng
Priority: REQUIRED · Evidence Level: E1 · Status: NOT_TESTED

Evidence: kiểm tra mọi `ReviewItem` sinh ra trên fixture — không mục nào chứa
`customer`, `phone`, `address`, `customer_code`. Tham chiếu ngược chỉ dùng
`source_file` + `source_row` + `order_id`.
`governance/core/04_SECURITY_RULES.md` §6.

### Review

#### CHECK-110-18 — Independent review
Priority: RECOMMENDED · Evidence Level: E2 · Status: NOT_TESTED

Evidence: theo `governance/templates/E2_INDEPENDENT_REVIEW_TEMPLATE.md`.
Tiền lệ TASK-108A-1: 119/119 test nội bộ PASS mà reviewer độc lập vẫn tìm ra
8 finding qua 3 vòng, trong đó một lỗi CRITICAL ảnh hưởng tiền lương.

### Tổng

REQUIRED: 17 · RECOMMENDED: 1 · PASS: 0 · BLOCKED: 1 (CHECK-110-16) ·
NOT_TESTED: 16

## Tiêu Chí Hoàn Thành (Exit Criteria)

- [ ] 17/17 REQUIRED check PASS (gồm CHECK-110-16 — cần dữ liệu thật).
- [ ] Không có lỗi critical chưa xử lý.
- [ ] Đạt E1 cho mọi check REQUIRED.
- [ ] `PROJECT/PROJECT_PROGRESS.md` và `PROJECT/LO_TRINH_DE_HIEU.md` cập nhật cùng một lần sửa.
- [ ] **TD-001 đóng được** — nêu rõ trong mục "Nợ Kỹ Thuật" rằng F2/F4 nay hiển thị trong Review Queue của luồng production, kèm check ID làm bằng chứng.
- [ ] Session Handoff của session triển khai (S016 trở đi). Handoff của phiên Gate Review là `docs/sessions/S015-task-110-gate-readiness.md`.

## Điều Kiện Kích Hoạt Leo Thang (Escalation Triggers)

Leo lên Tier C nếu gặp bất kỳ điều nào:

- Muốn đổi hành vi `order_builder` (V4) — đây là đổi business rule, cần DEC mới.
- Muốn thêm field vào `WorkingLine`/`Order` để chứa kết quả validation.
- Số phát hiện trên dữ liệu thật lệch khỏi bảng CHECK-110-16 mà không giải thích được.
- Xuất hiện cám dỗ suy `accounting_purchase_price` từ `source_profit` để làm V2 chạy được — **cấm tuyệt đối** (DEC-103).
- Muốn hạ một loại cảnh báo xuống `INFO` để queue "đẹp hơn" mà không có quyết định nghiệp vụ chống lưng.

## Đăng Ký File Đã Thay Đổi (Changed Files Registry)

Created:
- (chưa triển khai)

Modified:
- (chưa triển khai)

Deleted:
- (chưa triển khai)

Migration Impact:
- Không có. Phase 1 chưa có database.

## Ghi Chú (Notes)

### Vì sao TD-001 là phần rủi ro nhất của task này

F2/F4 hiện **chỉ tồn tại trong `tools/analysis/reconcile_conversion.py`** —
một script phân tích chạy tay, không nằm trên đường đi của `run_import()`.
TD-001 yêu cầu chúng hiển thị trong Review Queue. Nghĩa là TASK-110 không chỉ
"hiển thị lại" một thứ đã có, mà phải **đưa logic đó vào luồng production lần
đầu tiên**, đồng thời không làm lệch một artifact bằng chứng đã ship của
TASK-108A-1 (CHECK-108A1-15). Đó là lý do có cả CHECK-110-12/13 lẫn
CHECK-110-14.

### Bốn khoảng trống nghiệp vụ đã đóng trước khi Gate

`§18` đặc tả liệt kê 5 loại cảnh báo bằng một bảng hai cột — đủ để biết cần
làm gì, không đủ để biết làm thế nào cho đúng. Bốn chỗ được hỏi và đã có câu
trả lời của chủ dự án, ghi thành **DEC-128**. Không chỗ nào được tự đoán.
