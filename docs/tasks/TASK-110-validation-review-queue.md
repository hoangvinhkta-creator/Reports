# TASK-110 — Validation + Review Queue

## Metadata

Status:
**IMPLEMENTED — awaiting Independent Review.** Completion Gate **FROZEN** bởi
chủ dự án 2026-08-23. 16/17 REQUIRED check PASS; **CHECK-110-16 BLOCKED** (cần
file thô production, đã được chủ dự án cho phép giữ BLOCKED — chặn DONE, không
chặn IMPLEMENTED). 207/207 test PASS (56 mới, không regression).

**Không tự chuyển sang DONE.** Chờ Independent Review.

Phase:
PHASE-01 — Engine tính toán

Task Mode:
MAJOR

Primary Agent Tier:
B

Escalation Tier:
C

Difficulty:
3/5

Risk:
3/5

Blast Radius:
2/5

Lý do chấm lại (sơ bộ là D2/R2/B2):

- **Difficulty 2 → 3.** Phạm vi thật là **7 loại cảnh báo** (5 loại của §18 +
  tách `Suspicious` làm hai cơ sở khác nhau theo DEC-128 §2 + TD-001 F2/F4),
  không phải 5; và toàn bộ ngưỡng/từ khóa phải nằm trong config.
- **Risk 2 → 3.** TD-001. Một cảnh báo F4 bị nuốt nghĩa là một nhân viên thật
  đang bán hàng mà hệ thống không tính doanh số cho ai (DEC-127 §8 →
  `Unresolved` → không vào KPI của ai). Đây là rủi ro tiền lương, không phải
  rủi ro hiển thị. Theo `governance/core/EVIDENCE_STANDARD.md`, Risk 3 →
  **E1 bắt buộc** cho mọi check REQUIRED.
- **Blast Radius giữ 2.** Module mới, chỉ **đọc** `WorkingLine`/`Order`, không
  sửa engine nào đang chạy, không thêm field vào domain model.

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

- [x] 110.1 — `config/validation.yaml`: từ khóa dòng phụ, ngưỡng, bật/tắt từng loại.
- [x] 110.2 — Mô hình `ReviewItem` / `ReviewQueue` (dataclass thuần, mức độ + tham chiếu ngược).
- [x] 110.3 — V1 + V1-P (`Missing`, giá nhập nén tổng hợp).
- [x] 110.4 — V2 + V3 (`Suspicious`, hai cơ sở tách bạch).
- [x] 110.5 — V4 (`Order inconsistency`, chỉ phát hiện).
- [x] 110.6 — V5 (`Source classification`).
- [x] 110.7 — V6 (`Duplicate` theo `row_hash` trong batch).
- [x] 110.8 — V7: trích F2/F4 ra module dùng chung, nối vào `run_import()`; giữ nguyên hành vi `reconcile_conversion.py`.
- [x] 110.9 — Nối vào `app/pipeline.py` làm bước 11.
- [ ] 110.10 — Đối chiếu trên dữ liệu thật (CHECK-110-16) — **BLOCKED**, cần file thô production.

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
- [x] **Completion Gate đã frozen** — chủ dự án duyệt và freeze 2026-08-23,
      kèm làm rõ F-05 (ghi ở mục "Làm rõ F-05" cuối file).

## Completion Gate

Dùng `governance/core/TASK_COMPLETION_GATE_STANDARD.md` và
`governance/core/EVIDENCE_STANDARD.md`. Risk 3 → **E1 bắt buộc** cho mọi
check REQUIRED.

### Functional

#### CHECK-110-01 — Bảy loại cảnh báo tồn tại và phân biệt được
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`tests/test_validation_pipeline.py::test_every_category_code_is_reachable_and_distinct` — dựng bộ dữ liệu chạm đủ **8 mã loại**, khẳng định `set(counts_by_category()) == set(CATEGORIES)` và 8 mã đôi một khác nhau. Tám mã mang bảy *loại* của §18: `Missing` tách per-row (`Missing`) và tổng hợp (`Missing.PurchasePrice`) theo DEC-128 §1.

Executed By:
Claude (S016)

Timestamp:
2026-08-23

#### CHECK-110-02 — Không bao giờ chặn toàn bộ import
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`test_import_completes_even_when_every_row_is_defective` — `run_import()` trên workbook có lỗi ở mọi dòng vẫn trả `ImportResult` đầy đủ (`orders` không rỗng, có `preview`, `review_queue` > 0) và không raise. Không hàm nào trong `app/modules/validation/` raise vì dữ liệu — chỉ vì cấu hình sai.

Executed By:
Claude (S016)

Timestamp:
2026-08-23

#### CHECK-110-03 — `Missing` giá nhập nén thành một mục tổng hợp
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`test_pending_purchase_price_collapses_to_one_aggregate_item` — 25 dòng Pending → **đúng 1** mục, `affected_count == 25`. `test_aggregate_false_restores_per_row_for_task_401` chứng minh cờ config đảo lại được cho TASK-401.

Executed By:
Claude (S016)

Timestamp:
2026-08-23

#### CHECK-110-04 — `Missing` per-row đúng số lượng
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`test_missing_fires_once_per_missing_field` — 4 dòng dựng sẵn → đúng 6 mục, đúng field trên từng dòng (`date`; `quantity`+`total_sales`; `order_id`+`quantity`+`total_sales`). Bổ sung `test_missing_employee_counts_unmapped_not_merely_absent_name`.

Executed By:
Claude (S016)

Timestamp:
2026-08-23

#### CHECK-110-05 — V2 nằm im khi chưa có giá nhập, sống dậy khi có
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
(a) `test_computed_profit_rules_stay_dormant_while_price_is_pending` — với `PendingPriceProvider`, `purchase_price_above_sell_price` và `accounting_profit_negative` cho **0** phát hiện và không crash. (b) `test_computed_profit_rules_fire_once_a_real_price_exists` và `test_a_real_price_provider_wakes_the_dormant_computed_rules` (qua `run_import()` thật, provider trả giá nhập > giá bán) — quy tắc bắn đúng.

Executed By:
Claude (S016)

Timestamp:
2026-08-23

#### CHECK-110-06 — V3 tách bạch khỏi V2, không suy giá nhập từ ERP
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
(a) `test_erp_negative_profit_is_its_own_category_never_merged` — `Suspicious.ERP` là mã riêng, thông điệp mang chữ "CHƯA kiểm chứng"; `test_erp_signal_survives_the_real_pipeline_as_its_own_category` xác nhận hai loại không lẫn nhau qua pipeline thật. (b) `grep -rn "source_profit" app/modules/validation/` → **2 dòng, cả hai trong `detect_suspicious_erp`**, không dòng nào đứng cùng `accounting_purchase_price` hay `accounting_profit`; tự động hóa bằng `test_source_profit_is_never_used_to_derive_a_purchase_price_or_profit`.

Executed By:
Claude (S016)

Timestamp:
2026-08-23

#### CHECK-110-07 — Dòng phụ hạ xuống INFO, dòng sản phẩm thật thì không
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`test_non_product_line_is_downgraded_but_real_product_is_not` — `Chi phí vận chuyển` SL=0 → `INFO`; `Máy giặt Test-1` SL=0 → `WARNING`. `test_keyword_match_is_case_insensitive_and_covers_measured_variants` phủ 4 biến thể đã đo (`Chi phí lắp đặt`, `Chi phí giao hộ …`, `Phí đổi trả`, `CHÊNH VAT 25%`).

Executed By:
Claude (S016)

Timestamp:
2026-08-23

#### CHECK-110-08 — Từ khóa và ngưỡng nằm trong config
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`grep -rnE "Tín Phát|Vũ Hạnh Ly|Lê Mạnh Hoàng|Đức Kiên|Phước Thắng|Mr Vinh|Mr Quý|Đức Hiệp|NOI_THANH|Decimal\(\"0\.[0-9]+\"\)" app/modules/validation/*.py` → **0 kết quả**. Tự động hóa bằng `test_no_business_values_are_hardcoded_in_the_validation_module` (quét tên nhân viên, từ khóa dòng phụ và literal hình dạng tỉ lệ, sau khi bỏ comment/docstring). `test_config_keyword_list_matches_the_measured_evidence_filter` khóa danh sách từ khóa vào đúng bộ lọc đã đo ra 1.261 dòng.

Executed By:
Claude (S016)

Timestamp:
2026-08-23

#### CHECK-110-09 — V4 phát hiện nhưng không đổi kết quả tính
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
(a) `test_multi_employee_order_is_detected` — đơn 2 nhân viên → đúng 1 mục. (b) `test_building_the_queue_changes_nothing_about_the_data` — snapshot 11 trường của mọi dòng (gồm `conversion_scheme_final`, `conversion_rate_final`) **trước và sau** khi dựng queue: giống hệt; `test_order_builder_still_selects_the_first_line_untouched` xác nhận hành vi legacy không đổi. Provenance theo yêu cầu freeze: `test_multi_employee_finding_carries_the_provenance_the_owner_required` (OrderID, `employees_found`, `source_rows`, `legacy_selected`).

Executed By:
Claude (S016)

Timestamp:
2026-08-23

#### CHECK-110-10 — V5 chỉ bắn khi override thật sự khác rule
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`test_source_classification_only_fires_on_a_real_disagreement` — 3 case: `manual is None` → không bắn; `manual == auto` → không bắn; `manual != auto` → bắn. Phase 1 chưa có đường code nào ghi `lead_source_manual`, nên loại này cho 0 phát hiện trên dữ liệu thật **theo cấu tạo**, không phải vì code sai.

Executed By:
Claude (S016)

Timestamp:
2026-08-23

#### CHECK-110-11 — V6 trùng theo `row_hash` trong batch
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`test_identical_rows_are_flagged_once_as_a_warning` — 2 dòng cùng `row_hash` → 1 mục `WARNING`, `affected_count == 2`, liệt kê dòng nguồn `6, 7`. `test_rows_differing_by_one_character_are_not_duplicates` → không bắn.

Executed By:
Claude (S016)

Timestamp:
2026-08-23

#### CHECK-110-12 — TD-001: F2 xuất hiện trong Review Queue của production
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`test_f2_reaches_the_production_review_queue` — nhân viên `active`, hiệu lực trong kỳ, không khớp dòng nào → mục F2 do `Validator.build_queue()` sinh ra, tức trên luồng `run_import()`, không chỉ trong `tools/analysis/`. `test_f2_stays_silent_for_an_employee_legitimately_absent` giữ đúng phân biệt WARNING/INFO của tiêu chí gốc.

Executed By:
Claude (S016)

Timestamp:
2026-08-23

#### CHECK-110-13 — TD-001: F4 xuất hiện, và F2/F4 không làm hỏng import
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
(a) `test_f4_reaches_the_production_review_queue` — tên chưa map có 2 dòng ≥ nhân viên nhỏ nhất (1 dòng) → mục F4 trong queue. (b) `test_f2_and_f4_never_raise_and_never_empty_the_queue_of_other_findings` — không raise. Quan sát trực tiếp trên fixture tổng hợp: `run_import()` trả 3 mục F2 + 1 mục F4.

Executed By:
Claude (S016)

Timestamp:
2026-08-23

#### CHECK-110-14 — `reconcile_conversion.py` không đổi hành vi
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`tests/test_reconcile_raw_criteria.py` và `tests/test_reconcile_raw_integration.py` **không sửa một dòng nào** (`git diff` rỗng trên hai file) và **24/24 PASS** sau khi trích F1–F5 sang `app/modules/validation/employee_mapping.py`. `python3 tools/analysis/reconcile_conversion.py --help` chạy bình thường (exit 0).

Executed By:
Claude (S016)

Timestamp:
2026-08-23

#### CHECK-110-15 — Không regression
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`python3 -m pytest tests/ -q` → **207 passed in 1.30s**. Baseline tại `c7a1b24` là 151 → **56 test mới, 0 regression**.

Executed By:
Claude (S016)

Timestamp:
2026-08-23

#### CHECK-110-16 — Đối chiếu trên dữ liệu thật
Priority:
REQUIRED

Status:
BLOCKED

Evidence Level:
E1

Evidence:
chạy validation trên file thô thật, số phát hiện từng loại đối chiếu
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

Executed By:
—

Timestamp:
—

**Lý do BLOCKED:** file thô thật không có trong repo (`.gitignore` loại
`*.xlsx` và `data/samples/`, đúng `governance/product/17_DATA_GOVERNANCE_PRIVACY.md`) và không
có trong container của session này. Check này chỉ đóng được ở môi trường có
file thật. **Nó chặn DONE, không chặn IMPLEMENTED.**

### Security / Data

#### CHECK-110-17 — Không rò rỉ dữ liệu cá nhân khách hàng
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`test_no_review_item_carries_customer_identifying_data` — thu mọi giá trị `customer`/`customer_code`/`phone`/`address` có thật trên fixture (test tự khẳng định tập này không rỗng, nếu không phép kiểm vô nghĩa), rồi khẳng định không giá trị nào xuất hiện trong `message` hay `details` của bất kỳ mục nào. `test_review_items_reference_rows_not_people` xác nhận tham chiếu ngược chỉ là file + số dòng.

Executed By:
Claude (S016)

Timestamp:
2026-08-23

### Review

#### CHECK-110-18 — Independent review
Priority:
RECOMMENDED

Status:
NOT_TESTED

Evidence Level:
E2

Evidence:
theo `governance/templates/E2_INDEPENDENT_REVIEW_TEMPLATE.md`.
Tiền lệ TASK-108A-1: 119/119 test nội bộ PASS mà reviewer độc lập vẫn tìm ra
8 finding qua 3 vòng, trong đó một lỗi CRITICAL ảnh hưởng tiền lương.

Executed By:
—

Timestamp:
—

### Tổng

REQUIRED: 17 · RECOMMENDED: 1 · **PASS: 16** · **BLOCKED: 1** (CHECK-110-16,
chủ dự án cho phép giữ) · FAIL: 0 · NOT_TESTED: 1 (CHECK-110-18, RECOMMENDED)

## Tiêu Chí Hoàn Thành (Exit Criteria)

- [ ] 17/17 REQUIRED check PASS — **16/17**, CHECK-110-16 BLOCKED (cần dữ liệu thật).
- [x] Không có lỗi critical chưa xử lý.
- [x] Đạt E1 cho mọi check REQUIRED đã chạy.
- [x] `PROJECT/PROJECT_PROGRESS.md` và `PROJECT/LO_TRINH_DE_HIEU.md` cập nhật cùng một lần sửa.
- [x] **TD-001 đóng được** — F2/F4 nay hiển thị trong Review Queue của luồng production (CHECK-110-12/13 PASS); mục "Nợ Kỹ Thuật" đã cập nhật.
- [x] Session Handoff của session triển khai — `docs/sessions/S016-task-110-validation-review-queue.md`. Handoff của phiên Gate Review là `docs/sessions/S015-task-110-gate-readiness.md`.

## Điều Kiện Kích Hoạt Leo Thang (Escalation Triggers)

Leo lên Tier C nếu gặp bất kỳ điều nào:

- Muốn đổi hành vi `order_builder` (V4) — đây là đổi business rule, cần DEC mới.
- Muốn thêm field vào `WorkingLine`/`Order` để chứa kết quả validation.
- Số phát hiện trên dữ liệu thật lệch khỏi bảng CHECK-110-16 mà không giải thích được.
- Xuất hiện cám dỗ suy `accounting_purchase_price` từ `source_profit` để làm V2 chạy được — **cấm tuyệt đối** (DEC-103).
- Muốn hạ một loại cảnh báo xuống `INFO` để queue "đẹp hơn" mà không có quyết định nghiệp vụ chống lưng.

## Đăng Ký File Đã Thay Đổi (Changed Files Registry)

Created:
- `config/validation.yaml`
- `app/modules/validation/__init__.py`
- `app/modules/validation/models.py` — `ReviewItem`, `ReviewQueue`, hằng số loại/mức độ
- `app/modules/validation/rules.py` — bảy detector
- `app/modules/validation/employee_mapping.py` — F1–F5 (dời từ `tools/analysis/`) + `collect_mapping_stats`
- `app/modules/validation/validator.py` — orchestrator
- `tests/test_validation_rules.py` (25 test)
- `tests/test_validation_employee_mapping.py` (11 test)
- `tests/test_validation_pipeline.py` (20 test)

Modified:
- `app/pipeline.py` — bước 11, `ImportResult.review_queue`
- `tools/analysis/reconcile_conversion.py` — **chỉ trích xuất**: F1–F5 dời sang
  `app/modules/validation/employee_mapping.py` và import ngược lại dưới đúng
  tên cũ. Hành vi, output và exit code không đổi (CHECK-110-14).

Deleted:
- Không có.

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

### Làm rõ F-05 khi freeze (chủ dự án, 2026-08-23)

Bổ sung vào DEC-128 §4, ràng buộc trực tiếp lên `detect_order_inconsistency`:

- TASK-110 **chỉ phát hiện và tạo cảnh báo**. Không sửa `order_builder`, không
  tự quyết định ownership hay KPI.
- Nhân viên hiện được lấy từ dòng đầu tiên là **hành vi legacy**, **không**
  được coi là quyền sở hữu đã được xác minh. Thông điệp cảnh báo phải nói ra
  điều này bằng chữ.
- Mỗi cảnh báo phải giữ đủ provenance để sau này quyết định được:
  **OrderID**, **các employee khác nhau được phát hiện**, **dòng nguồn tương
  ứng**, và **employee mà `order_builder` legacy đang chọn**.
- Không tự sửa employee, không tự chia KPI, không tự chọn người nhận doanh số.
- Đổi cách xử lý multi-employee Order phải là một business decision / task riêng.

Hiện thực: `app/modules/validation/rules.py::detect_order_inconsistency` ghi ba
khóa `employees_found` / `legacy_selected` / `source_rows` (hằng số trong
`app/modules/validation/models.py`). Kiểm chứng:
`test_multi_employee_finding_carries_the_provenance_the_owner_required`.

`_selling_identity()` so sánh **danh tính bán hàng**, không chỉ tên đã map:
một dòng đã map đứng cạnh một dòng chưa map trên cùng đơn vẫn là mâu thuẫn —
đó chính là trường hợp tệ nhất, doanh số của người chưa map rơi vào tay người
được chọn trước. So sánh chỉ trên tên đã map sẽ giấu đúng ca này
(`test_unmapped_line_beside_a_mapped_one_is_still_an_inconsistency`).

### Ghi chú triển khai cần reviewer soi

**1 — F1/F3/F5 cũng vào hàng chờ, không chỉ F2/F4.** Bảng phạm vi đã freeze
ghi V7 là "F2 và F4". `evaluate_raw_mapping()` trả cả `hard_failures`
(F1/F3/F5) trong cùng một lượt. Tôi đưa cả ba vào queue ở mức `ERROR` thay vì
bỏ đi. Lý do: chúng là invariant — không thể đúng với master data lành mạnh —
và nuốt một invariant đã vi phạm là đúng thứ TASK-110 tồn tại để chặn. Đây là
**tập cha** của phạm vi đã freeze: không đổi quyết định nào, không đổi check
nào, không chặn import nào. **Ghi ra đây tường minh để reviewer bác nếu thấy
không nên.**

**2 — Tám mã loại cho bảy *loại*.** `Missing` có hai mã (`Missing` per-row và
`Missing.PurchasePrice` tổng hợp) vì DEC-128 §1 tách chúng theo hình dạng.
Đây là đúng bảng phạm vi đã freeze (8 dòng V1, V1-P, V2…V7), không phải thêm
loại mới.

**3 — Chưa nối `note_raw` vào loại `Order inconsistency`.** §18 đặc tả viết
"cùng OrderID nhưng khác nhân viên **hoặc dữ liệu nguồn mâu thuẫn**". Vế sau
chưa có định nghĩa nghiệp vụ nào nói "mâu thuẫn" nghĩa là gì ngoài nhân viên
và ngày. Tôi triển khai hai vế đo được (nhân viên, ngày) và **không đoán** vế
thứ ba. Nếu chủ dự án muốn nó, cần một định nghĩa trước.
