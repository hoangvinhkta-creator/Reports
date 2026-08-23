# TASK-110 — Validation + Review Queue

## Metadata

Status:
**IMPLEMENTED — awaiting Independent Review #2.** Completion Gate **FROZEN**
2026-08-23. **Independent Review #1: FAIL, 6 finding — đã sửa toàn bộ**
(S017); ba Human Decision phát sinh ghi thành **DEC-129**. 16/17 REQUIRED
check PASS; **CHECK-110-16 BLOCKED** (cần file thô production, chủ dự án cho
phép giữ — chặn DONE, không chặn IMPLEMENTED). **260/260 test PASS** (109 mới
so với baseline `c7a1b24`, 0 regression).

**Không tự chuyển sang DONE. Chưa merge.**

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
V7 là TD-001, mở rộng thành F1–F6 theo **DEC-129** (HD-110-01, HD-110-03).

| Mã | Loại | Cơ sở phát hiện | Ghi chú |
|---|---|---|---|
| V1 | `Missing` | Thiếu ngày, OrderID, nhân viên, SL, doanh số | Per-row |
| V1-P | `Missing` — giá nhập | `price_source == Pending` | **Nén thành MỘT mục tổng hợp** (DEC-128 §1) |
| V2 | `Suspicious` — tính toán | `accounting_profit < 0`; `accounting_purchase_price > sell_price`; `quantity <= 0`; `sell_price == 0` | Phase 1 hai điều kiện đầu **nằm im** (0 phát hiện) vì `accounting_profit is None` ở 100% dòng |
| V3 | `Suspicious` — ERP | `source_profit < 0` | **Loại riêng**, nhãn ghi rõ là tín hiệu từ ERP chưa kiểm chứng (DEC-128 §2) |
| V4 | `Order inconsistency` | Cùng `order_id`, khác `employee_normalized` (hoặc khác `date`) | **Chỉ phát hiện**, không đổi cách tính (DEC-128 §4) |
| V5 | `Source classification` | `lead_source_manual` có giá trị và khác `lead_source_auto` | Phase 1 chưa có nguồn ghi override → 0 phát hiện thật, kiểm bằng fixture |
| V6 | `Duplicate` | Trùng `row_hash` **trong cùng một lần import** | WARNING, không phải lỗi (DEC-128 §3) |
| V7 | `Employee mapping` | **F1–F6** — toàn bộ tiêu chí chẩn đoán master data, chạy trong luồng production | **TD-001** + **HD-110-01** (F1/F3/F5) + **HD-110-03** (F6) |

Ngoài ra:
- Mỗi mục trong queue mang: mã loại, mức độ (`INFO`/`WARNING`/`ERROR`), một
  câu mô tả đọc được bằng tiếng Việt, và **tham chiếu ngược bắt buộc**. Sau
  Independent Review #1 (Finding 1, Finding 6), ràng buộc này là **cấu trúc**
  chứ không phải quy ước: `ReviewItem.scope` ∈ `row` | `order` | `batch`, và
  `__post_init__` từ chối dựng một mục không truy vết được —
  `row` cần `source_file` + `source_row`, `order` cần `source_file` +
  `order_id`, `batch` cần `source_file`. Không mục nào được phép để trống
  toàn bộ tham chiếu.
- `affected_count` là **số dòng thô thật** đứng sau mục đó, kể cả khi bằng
  **0** — F2 nói đúng nghĩa "nhân viên này không khớp dòng nào", nên ghi 1 ở
  đó là bịa ra một dòng không tồn tại.
- Toàn bộ **từ khóa dòng phụ** và mọi ngưỡng nghiệp vụ nằm trong
  `config/validation.yaml`. Không literal nào trong `app/`.
- Khớp từ khóa theo **HD-110-02**: chuẩn hóa Unicode NFC + gộp khoảng trắng +
  case-folding, áp cho **cả hai phía**, rồi khớp theo **biên từ** (nguyên một
  từ hoặc nguyên một cụm). Không dùng substring, không dùng dấu cách cuối làm
  mẹo thay cho biên. Ngữ nghĩa này sống ở `app/modules/validation/text.py`.
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
  định dòng nào tính vào đâu. **HD-110-02: đây là giải pháp TẠM THỜI —
  TASK-103 phải THAY THẾ nó, không kế thừa nó.**
- **Chống trùng khi import lại cùng một file** (cần persistence) — TASK-201.
- **Đổi hành vi của `order_builder`** — hiện lấy nhân viên của dòng đầu tiên.
  DEC-128 §4 giữ nguyên hành vi này; đổi nó cần một DEC mới.
- **Đổi cách tính cho nhân viên `inactive`.** F6 chỉ **báo** (HD-110-03).
  `conversion_engine` vẫn cho `inactive` đi qua như `mapped`; đổi điều đó là
  đổi business calculation và KPI ownership, cần một DEC riêng.
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
- `app/modules/validation/` (mới) — gồm `text.py` (chuẩn hóa + khớp biên từ,
  thêm ở vòng sửa Independent Review #1, HD-110-02)
- `config/validation.yaml` (mới)
- `app/pipeline.py` — chỉ thêm bước 11 và trường `review_queue` vào `ImportResult`
- `tests/test_validation_*.py` (mới)
- `tools/analysis/reconcile_conversion.py` — chỉ **trích xuất** logic F2/F4 ra
  chỗ dùng chung; hành vi và output của script phải **không đổi**
- `docs/tasks/TASK-110-validation-review-queue.md`, `docs/sessions/S015-*.md`,
  `docs/sessions/S016-*.md`, `docs/sessions/S017-*.md`
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
- [x] 110.R1 — Sửa 6 finding của Independent Review #1 (S017), xem "Lịch Sử Independent Review".

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
`test_missing_fires_once_per_missing_field` — 4 dòng dựng sẵn → đúng 6 mục, đúng field trên từng dòng.

**Sửa Independent Review #1, Finding 3:** `Missing.employee` nay CHỈ bắn cho `unmapped`. Một nhân viên `inactive` đã được nhận diện — không có gì "thiếu". Kiểm chứng: `test_inactive_employee_is_not_reported_as_missing_employee`, `test_only_unmapped_counts_as_a_missing_employee` (bảng 3 trạng thái), `test_blank_employee_still_counts_as_missing` (C11 vẫn được bảo vệ).

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
`test_non_product_line_is_downgraded_but_real_product_is_not` — `Chi phí vận chuyển` SL=0 → `INFO`; `Máy giặt Test-1` SL=0 → `WARNING`.

**Sửa Independent Review #1, Findings 4 và 5 (HD-110-02).** Khớp nay đi qua `app/modules/validation/text.py`: NFC + gộp khoảng trắng + case-fold trên **cả hai phía**, rồi khớp **biên từ**. `"phí "` đã bị thay bằng `"phí"`.

Falsification (`tests/test_validation_text.py`, 31 test):
- **NFD/NFC**: `test_nfd_and_nfc_spellings_are_the_same_word` (test tự khẳng định hai chuỗi thật sự khác byte trước khi so), `test_a_keyword_written_in_nfd_still_compiles_to_the_same_matcher`.
- **Khoảng trắng**: 4 biến thể (space đôi, tab, thừa hai đầu, newline giữa ô).
- **False positive**: `test_phi_does_not_match_ban_phim` — `Bàn phím cơ Logitech` **KHÔNG** khớp, và test khẳng định trước rằng substring `phí` thật sự nằm trong đó, nên chỉ biên từ mới cứu được. Thêm 4 sản phẩm thật đều không khớp.
- **False negative**: `test_a_keyword_at_the_very_end_of_the_value_still_matches` — `Thu chi phí` khớp, đúng ca mà mẹo dấu-cách-cuối luôn bỏ sót; `test_multiword_keyword_needs_the_whole_phrase`; `test_blank_keywords_are_dropped_rather_than_matching_everything`.
- Ở tầng detector: `test_real_products_keep_their_severity_through_the_detector`.

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
`grep -rnE "<8 tên nhân viên>|NOI_THANH|Decimal(\"0.N\")" app/modules/validation/*.py` → **0 kết quả**. Tự động hóa bằng `test_no_business_values_are_hardcoded_in_the_validation_module`.

**Sửa Independent Review #1 (HD-110-02):** test khóa danh sách từ khóa vào bộ lọc lịch sử đã bị **gỡ bỏ** — nó chính là kiểu tune theo con số 1.261 mà quyết định cấm, và nó chỉ chứng minh rule mới khớp rule cũ chứ không chứng minh rule đúng. Thay bằng `test_keyword_config_expresses_semantics_not_a_historical_count`, khẳng định **hình dạng** mà ngữ nghĩa đòi hỏi: không từ khóa nào được dựa vào khoảng trắng đệm (`keyword == keyword.strip()`), tất cả đã case-fold. Hành vi do `tests/test_validation_text.py` phủ.

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
(a) `test_multi_employee_order_is_detected` — đơn 2 nhân viên → đúng 1 mục. Provenance theo yêu cầu freeze: `test_multi_employee_finding_carries_the_provenance_the_owner_required` (OrderID, `employees_found`, `source_rows`, `legacy_selected`).

(b) **Sửa Independent Review #1, Finding 6.** Bản trước snapshot **11 field liệt kê tay** — một field thêm sau sẽ lặng lẽ thoát khỏi bảo đảm. Nay `_snapshot()` duyệt `dataclasses.fields` **đệ quy** trên toàn bộ `Order` → `WorkingLine` → `RawRow`, nên không thể tụt lại sau model. Hai test bọc quanh nó: `test_the_snapshot_actually_covers_every_frozen_field` (≥30 field, gồm `conversion_rate_final`) và `test_the_non_mutation_snapshot_would_actually_catch_a_write` — cố tình sửa một field sâu và khẳng định snapshot **phát hiện được**, để việc nó PASS có nghĩa. `test_order_builder_still_selects_the_first_line_untouched` giữ nguyên.

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
`test_f2_reaches_the_production_review_queue` — nhân viên `active`, hiệu lực trong kỳ, không khớp dòng nào → mục F2 do `Validator.build_queue()` sinh ra, tức trên luồng `run_import()`, không chỉ trong `tools/analysis/`.

**Sửa Independent Review #1, Finding 1 — provenance.** `test_f2_carries_batch_provenance_and_an_honest_zero_count`: mục F2 mang `scope=batch`, `source_file`, `dataset_range` (`2026-01-05..2026-03-09`), `batch_rows`, và `affected_count == 0` — con số thật, vì F2 nghĩa là *không* khớp dòng nào; ghi 1 sẽ là bịa ra một dòng.

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
(a) `test_f4_reaches_the_production_review_queue`. (b) `test_f2_and_f4_never_raise_and_never_empty_the_queue_of_other_findings` — không raise.

**Sửa Independent Review #1, Finding 1 — provenance.** `test_f4_names_the_rows_it_is_about`: mục F4 mang `scope=row`, `source_row=11` (dòng đầu của tên chưa map), `source_rows="11, 14"`, `raw_value`, và `affected_count == 2` — **số thật**, không phải placeholder 1. Tương tự cho F1 (`test_f1_points_at_the_rows_of_the_employee_whose_group_is_undeclared`) và F5 (`test_f5_is_batch_scoped_and_counts_every_orphaned_row`).

**HD-110-03 — tiêu chí F6:** `test_f6_reports_an_inactive_employee_that_still_has_rows` (WARNING, `source_rows="6, 8"`, `affected_count == 2`), `test_f6_stays_silent_for_an_active_employee`, `test_f6_and_f2_never_describe_the_same_employee_at_once` (F2-INFO và F6 là hai nửa bù nhau).

Bất biến chung: `test_every_employee_mapping_item_satisfies_the_reference_invariant`.

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
`tests/test_reconcile_raw_criteria.py` và `tests/test_reconcile_raw_integration.py` **không sửa một dòng nào** (`git diff --stat HEAD` rỗng trên hai file) và **24/24 PASS**, cả sau vòng sửa Independent Review #1. `python3 tools/analysis/reconcile_conversion.py --help` exit 0.

`RawMappingVerdict` nay giữ `findings` có cấu trúc, nhưng vẫn phơi `hard_failures`/`warnings`/`info` dưới dạng **đúng các list chuỗi cũ, đúng thứ tự cũ** — script không thấy khác biệt nào. F6 mới thêm không thể bắn với master data lành mạnh, kiểm chứng bằng `test_f6_does_not_change_what_the_analysis_script_reports_for_healthy_data`.

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
`python3 -m pytest tests/ -q` → **260 passed in 1.65s**. Baseline tại `c7a1b24` là 151 → **109 test mới, 0 regression**. Vòng Independent Review #1 thêm 53 test so với `e2c0c18` (207).

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

| Loại | **Mốc tham chiếu** (bộ 6 tháng, 11.765 dòng) |
|---|---:|
| `Missing` — thiếu nhân viên | 2 |
| `Missing` — thiếu SL | 52 |
| V3 — ERP báo lợi nhuận âm | 1.912 |
| Dòng phụ (hạ xuống INFO) | 1.261 (30 loại) — **xem cảnh báo bên dưới** |
| V1-P — chờ giá nhập | 11.765 (1 mục tổng hợp) |

Mọi chênh lệch phải giải thích bằng văn bản, **không được** chỉnh ngưỡng cho
khớp — cùng quy tắc đã áp ở CHECK-101-08.

**HD-110-02 làm rõ cách đọc con số 1.261 (không nới lỏng check).** Con số đó
do bộ lọc substring cũ trong `tools/analysis/extract_evidence.py` đo ra
(`chi phí vận chuyển|công lắp đặt|chênh vat|chiết khấu|voucher|phí `). Ngữ
nghĩa biên từ mới **có thể cho ra một con số khác một cách chính đáng** — ví
dụ nó bắt được cả giá trị kết thúc bằng chữ "phí" mà mẹo dấu-cách-cuối luôn
bỏ sót. Vì vậy 1.261 là **mốc tham chiếu**, không phải mục tiêu:

- Chênh lệch phải được **giải thích bằng văn bản**, kèm ví dụ dòng cụ thể.
- **Cấm chỉnh danh sách từ khóa để đưa con số về 1.261.** Làm vậy là biến
  phép kiểm thành phép chép rule cũ.
- Nếu chênh lệch cho thấy ngữ nghĩa mới **sai** (bắt nhầm sản phẩm thật), đó
  là một finding phải sửa — nhưng sửa bằng ngữ nghĩa, không bằng con số.

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
`test_no_review_item_carries_customer_identifying_data` — thu mọi giá trị `customer`/`customer_code`/`phone`/`address` có thật trên fixture (test tự khẳng định tập này không rỗng), rồi khẳng định không giá trị nào xuất hiện trong `message` hay `details` của bất kỳ mục nào — kể cả các mục `EmployeeMapping` mới có thêm `details`.

`test_every_queue_item_from_a_real_import_is_traceable` thay cho `test_review_items_reference_rows_not_people` cũ: khẳng định **mỗi** mục có tham chiếu hợp lệ theo `scope`, thay vì chấp nhận mục có tham chiếu toàn `None` (Review #1, Finding 6). `test_an_untraceable_item_cannot_even_be_constructed` khóa bất biến ở tầng model.

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
- `app/modules/validation/text.py` — chuẩn hóa NFC + gộp khoảng trắng +
  case-fold + khớp biên từ (Review #1, Findings 4/5, HD-110-02)
- `app/modules/validation/models.py` — `ReviewItem`, `ReviewQueue`, hằng số loại/mức độ
- `app/modules/validation/rules.py` — bảy detector
- `app/modules/validation/employee_mapping.py` — F1–F5 (dời từ `tools/analysis/`) + `collect_mapping_stats`
- `app/modules/validation/validator.py` — orchestrator
- `tests/test_validation_rules.py` (33 test)
- `tests/test_validation_employee_mapping.py` (21 test)
- `tests/test_validation_pipeline.py` (24 test)
- `tests/test_validation_text.py` (31 test — falsification cho Findings 4/5)

Modified:
- `app/pipeline.py` — bước 11, `ImportResult.review_queue`
- `PROJECT/PROJECT_DECISIONS.md` — **DEC-129** (HD-110-01/02/03)
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

**1 — F1/F3/F5 vào hàng chờ. ĐÃ GIẢI QUYẾT.** Vòng trước tôi đưa cả
`hard_failures` vào queue trong khi bảng phạm vi freeze chỉ ghi "F2 và F4", và
tự ghi chú "reviewer bác nếu thấy không nên". Independent Review #1 xếp đó là
**Finding 2 — scope creep**, và đúng: một hành vi có thể biện minh được nhưng
nằm ngoài phạm vi đã freeze vẫn là scope creep, ghi chú tự thú không làm nó
hợp lệ. Chủ dự án đã duyệt chính thức (**HD-110-01**); bảng phạm vi V7 nay ghi
**F1–F6** và **DEC-129** là bản ghi canonical.

**2 — Tám mã loại cho bảy *loại*.** `Missing` có hai mã (`Missing` per-row và
`Missing.PurchasePrice` tổng hợp) vì DEC-128 §1 tách chúng theo hình dạng.
Đúng bảng phạm vi đã freeze, không phải thêm loại mới.

**3 — Chưa nối `note_raw` vào loại `Order inconsistency`.** §18 đặc tả viết
"cùng OrderID nhưng khác nhân viên **hoặc dữ liệu nguồn mâu thuẫn**". Vế sau
chưa có định nghĩa nghiệp vụ nào nói "mâu thuẫn" nghĩa là gì ngoài nhân viên
và ngày. Tôi triển khai hai vế đo được và **không đoán** vế thứ ba. Cần một
định nghĩa trước nếu chủ dự án muốn nó.

**4 — F6 là chẩn đoán, không phải cơ chế cưỡng chế.** Một nhân viên
`active: false` vẫn nhận tỉ lệ quy đổi như cũ; F6 chỉ làm mâu thuẫn master
data nhìn thấy được. Nếu chủ dự án muốn `inactive` không nhận tỉ lệ, đó là đổi
business calculation + KPI ownership → cần DEC riêng và sửa
`conversion_engine` (ngoài Expected Touch Area hiện tại).

**5 — `affected_count == 0` là cố ý.** Mục F2 nói "nhân viên này không khớp
dòng nào", nên số dòng thật đứng sau nó là 0. Ghi 1 cho "đẹp" sẽ là bịa ra một
dòng không tồn tại, và `ReviewQueue.affected_rows()` sẽ nói dối về quy mô.

## Lịch Sử Independent Review

### Review #1 — FAIL, 6 finding (2026-08-23, commit `e2c0c18`)

Bản nộp có 207/207 test nội bộ PASS và 16/17 REQUIRED check tự báo PASS.
Reviewer độc lập vẫn tìm ra 6 finding. Ba trong số đó cần chủ dự án quyết
(HD-110-01, HD-110-02, HD-110-03 → **DEC-129**).

| # | Finding | Đã sửa thế nào |
|---|---|---|
| 1 | Mục `EmployeeMapping` **không có provenance** — F4 không truy được file/dòng, `affected_count` không thật, F2 thiếu provenance batch | `RawMappingVerdict` nay giữ `MappingFinding` có cấu trúc (criterion / employee / raw_value / affected_count); `MappingStats` thêm `rows_by_raw_value`, `rows_by_employee`, `source_file`, `total_rows`; `Validator._mapping_item()` dựng mục row-scope khi có dòng thật, batch-scope kèm `dataset_range` + `batch_rows` khi không |
| 2 | F1/F3/F5 trong queue là **scope creep** | HD-110-01 duyệt; bảng phạm vi V7 → **F1–F6**; **DEC-129** ghi canonical |
| 3 | `Missing.employee` báo nhầm cho nhân viên **`inactive`** | Chỉ `unmapped` mới là Missing. Khoảng trống lộ ra (inactive có đơn thì im lặng hoàn toàn) → **STOP và hỏi** → HD-110-03 → tiêu chí **F6** |
| 4 | Thiếu chuẩn hóa Unicode/khoảng trắng/hoa thường | `app/modules/validation/text.py` mới: NFC + gộp khoảng trắng + case-fold, áp **cả hai phía**; test NFD/NFC và 4 biến thể khoảng trắng |
| 5 | Literal `"phí "` làm semantic | Thay bằng khớp **biên từ** `(?<!\w)…(?!\w)`; config `"phí "` → `"phí"`; test false-positive `Bàn phím cơ` và false-negative `Thu chi phí`; **gỡ** test khóa danh sách vào con số 1.261 |
| 6 | Snapshot non-mutation chỉ phủ 11 field liệt kê tay; test provenance chấp nhận reference toàn `None` | Snapshot duyệt `dataclasses.fields` đệ quy toàn `Order`/`WorkingLine`/`RawRow`, kèm test tự-falsify; `ReviewItem.scope` + `__post_init__` khiến mục không truy vết được **không dựng nổi** |

**Bài học.** Vòng trước tôi ghi ra đúng vấn đề của Finding 2 ("ghi ra để
reviewer bác nếu thấy không nên") nhưng vẫn ship nó như một hành vi. Nêu ra
một sai lệch không làm nó hết sai lệch — thứ phải làm là **hỏi trước**, đúng
như đã làm với Finding 3 ở vòng này.
