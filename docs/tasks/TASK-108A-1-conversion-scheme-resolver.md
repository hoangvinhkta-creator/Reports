# TASK-108A-1 — Conversion Scheme Resolver (EmployeeGroup + ProductGroup)

## Metadata
Status:
IMPLEMENTED

Phase:
PHASE-01 — Engine tính toán

Task Mode:
MAJOR

Primary Agent Tier:
C

Escalation Tier:
—

Difficulty:
4/5

Risk:
5/5

Blast Radius:
5/5

Project Profile:
PRODUCT

## Mục Tiêu (Objective)

Bước 10 của §22 đặc tả: phân giải `ConversionScheme` cho từng **product
line**, độc lập hoàn toàn với `LeadSource`, tra từ config theo
`(employee, employee_group, lead_source, product_group, ngày của đơn)`.

Đây là task rủi ro cao nhất roadmap — một tỉ lệ sai ở đây thành một con số
sai trên bảng lương của người thật.

TASK-108 gốc được tách làm ba (DEC-127, Gate v3):

| Phần | Trạng thái |
|---|---|
| **108A-1** — Scheme Resolver (task này) | READY → IMPLEMENT |
| 108A-2 — ProductGroup Auto Classification | NOT REQUIRED FOR PHASE 1 |
| 108B — Converted Revenue | BLOCKED (4 dependency, gồm C15) |

## Phạm Vi (Scope)

- `config/employees.yaml`: thêm khối `employee_groups`; tách `Nội thành`
  thành ba Employee `Vinh` / `Quý` / `Hiệp` cùng `group: NOI_THANH`; các
  nhân viên còn lại `group: STANDARD_SALES` (DEC-127 §1).
- `EmployeeMapper.MappingResult` thêm `group`.
- Domain model: `employee_group`, `product_group_auto/_manual/_final`,
  `product_group_source_of_value`, `conversion_scheme_auto/_manual/_final`,
  `conversion_rate_final`, `conversion_scheme_source_of_value` trên
  `WorkingLine`; `employee_group` trên `Order`.
- `config/conversion_rates.yaml`: bảng scheme 4 chiều (ADR-106 §3).
- `ProductGroupProvider` (Protocol) + `DefaultProductGroupProvider` — Phase 1
  luôn trả `None` → mọi dòng rơi về `DIEN_MAY` (DEC-127 §5).
- `ConversionSchemeResolver`: lọc cứng theo `lead_source`, chọn dòng cụ thể
  nhất theo specificity, effective-dating theo **ngày của đơn**, hòa điểm là
  lỗi cấu hình, không khớp là `Unresolved`.
- Nối vào `run_import()` làm bước 10, chạy ở **cấp line**.
- Cập nhật `tools/analysis/verify_ads_rule.py` sang bảng 4 chiều + `Decimal`,
  giữ **31/31 PASS**.
- Test suite + reconciliation trên workbook thật và file thô toàn công ty.

## Ngoài Phạm Vi (Out of Scope)

- **Converted Revenue / `EligibleKpiProfit`** (108B) — BLOCKED bởi 4
  dependency: `AccountingPurchasePrice`/Price Master (TASK-401), confirmed
  KPI Adjustment (DEC-126 §3–6), `OtherKpiAdjustment`, và **`EligibleCosts`
  chưa có định nghĩa nghiệp vụ** (C15). Tuyệt đối không giả định `= 0`.
- **Auto-classification ProductGroup** (108A-2) — Phase 1 thủ công 100 %.
  Không dùng 155 model lịch sử, không suy luận keyword, không tự học
  `Model → ProductGroup` (DEC-127 §5).
- UI checkbox `☐ Gia dụng` — Phase 2/3. Task này chỉ để sẵn field + provenance.
- Thêm `Linh` / `Fanpage` / 5 NVBH chưa map vào active master data — legacy,
  trả `Unresolved` (DEC-127 §8).
- Tầng tổng hợp báo cáo (TASK-109/111).
- `app/modules/pricing/`, `profit/`, `adjustment/`, `orders/`,
  `lead_source/`, `importing/` — không đụng.

## Phụ Thuộc (Dependencies)
- TASK-101 — DONE (employee mapping, order grouping, LeadSource).
- DEC-119, DEC-120, DEC-121, ADR-104 — mô hình hai khái niệm độc lập.
- **DEC-127, ADR-106** — quyết định nền tảng cho task này.

## Chặn (Blocks)
- TASK-108B (Converted Revenue) — cần scheme/rate đã phân giải.
- TASK-109/111 (tổng hợp, xuất báo cáo).

## An Toàn Để Chạy Song Song Với (Parallel-Safe With)
- Track B (Governance) — không chạm chung file.

## Phạm Vi Tác Động Dự Kiến (Expected Touch Area)

Allowed:
- `config/employees.yaml`, `config/conversion_rates.yaml`
- `app/modules/domain/models.py`, `app/modules/mapping/employee_mapper.py`
- `app/modules/conversion/`, `app/modules/product/` (module mới)
- `app/pipeline.py`
- `tests/`, `tools/analysis/verify_ads_rule.py`,
  `tools/analysis/reconcile_conversion.py`
- `docs/tasks/`, `docs/sessions/`, `PROJECT/`

**SCOPE EXPANSION ĐÃ KHAI BÁO** — task này sửa file của TASK-101 đã DONE
(`employees.yaml`, `employee_mapper.py`, `models.py`, 2 file test). Được chủ
dự án phê duyệt tường minh trong Gate v3. Hai assert test đổi từ
`"Nội thành"` sang tên riêng là **hệ quả trực tiếp của rule mới**, không phải
sửa test để làm nó PASS.

Không được đụng nếu chưa có Scope Expansion mới:
- `app/modules/pricing/`, `profit/`, `adjustment/`, `orders/`,
  `lead_source/`, `importing/`
- `docs/analysis/` (ngoài C11/C15 đã cập nhật), `docs/adr/ADR-101…105`
- Bất kỳ file nào của Track B.

## Subtask (Subtasks)
- [x] 108A-1.1 `employees.yaml` — `employee_groups` + tách Vinh/Quý/Hiệp
- [x] 108A-1.2 `EmployeeMapper.MappingResult.group`
- [x] 108A-1.3 Domain model — 8 field mới
- [x] 108A-1.4 `conversion_rates.yaml` 4 chiều
- [x] 108A-1.5 `ProductGroupProvider` + `DefaultProductGroupProvider`
- [x] 108A-1.6 `ConversionSchemeResolver`
- [x] 108A-1.7 Nối `run_import()` bước 10 (line-level)
- [x] 108A-1.8 Cập nhật `verify_ads_rule.py` (giữ 31/31)
- [x] 108A-1.9 Test suite 32 case
- [x] 108A-1.10 Reconciliation 55 ô + xác minh trên dữ liệu thô toàn công ty

## Ready Gate
Dùng `governance/core/TASK_READY_GATE_STANDARD.md`.

- [x] Objective rõ ràng.
- [x] Scope đã xác định (chỉ resolver; 108A-2/108B tách riêng).
- [x] Out-of-scope đã xác định, kèm lý do chặn cụ thể cho từng phần.
- [x] Dependency (TASK-101, DEC-127, ADR-106) đã sẵn sàng.
- [x] Vùng tác động đã xác định; Scope Expansion đã khai báo và được duyệt.
- [x] Yêu cầu nghiệp vụ đã hiểu rõ — ba vòng pre-implementation review, mọi
      câu hỏi chặn đã đóng bằng xác nhận trực tiếp của chủ dự án.
- [x] Tác động dữ liệu: không có dữ liệu cá nhân mới; tỉ lệ quy đổi là dữ
      liệu nhạy cảm ảnh hưởng lương, chưa lộ ra UI/API ở Phase 1.
- [x] Tác động bảo mật: không có, chưa có network/DB.
- [x] Không liên quan routing/API (Phase 1 thuần Python).
- [x] Không có migration (chưa có DB).
- [x] Difficulty/Risk/Blast Radius đã chấm (4/5/5).
- [x] Agent tier đã chỉ định (C, không escalation — đã ở tier cao nhất).
- [x] Escalation trigger đã xác định.
- [x] **Completion Gate đã hoàn thiện và FROZEN trước khi implement.**

## Completion Gate

**FROZEN 2026-08-23, trước khi viết dòng code đầu tiên.**
Dùng `governance/core/TASK_COMPLETION_GATE_STANDARD.md` và
`governance/core/EVIDENCE_STANDARD.md`.

### Functional — Bảo toàn hành vi

#### CHECK-108A1-01 — 8 case A–G giữ nguyên scheme và rate sau khi đổi mô hình
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`pytest tests/test_scheme_resolver.py -q` → 25/25 passed, gồm 8 case A–G
parametrize (`test_case_a_to_g_unchanged_after_model_change`). Scheme và rate
**y hệt** trước khi tách EmployeeGroup/ProductGroup — chính sự bằng nhau đó là
bằng chứng mô hình mới bảo toàn hành vi. Case E/F giờ dùng tên thật
(`Vinh`/`Quý`/`Hiệp`) thay vì employee giả `Nội thành`, vẫn ra `NOI_THANH_2` /
2 %. Thêm `test_case_f_covers_all_three_channel_employees` xác nhận cả ba
người giữ ba danh tính riêng.

Executed By:
Claude (session này)

Timestamp:
2026-08-23

#### CHECK-108A1-02 — verify_ads_rule.py giữ 31/31 PASS sau khi chuyển sang 4 chiều và Decimal
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
**Sửa theo Independent Review #1, Finding 4.** Script không còn bảng nhân
viên / từ khóa / tỉ lệ / thuật toán riêng — nó import
`EmployeeMapper`, `LeadSourceClassifier`, `ConversionSchemeResolver` từ
`app.modules` và nạp trực tiếp `config/`. Input là chuỗi `NVBH` thô đúng như
file bán hàng, nên bước mapping cũng được kiểm luôn. Chỉ **expected output**
nằm trong script.

Output `python tools/analysis/verify_ads_rule.py` (exit 0):
```
LeadSource — §29 + §13 edge + DEC-109              : 18/18 passed
ConversionScheme — DEC-119 cases A–G (DEC-127)     :  8/8  passed
ProductGroup + unmapped guard — DEC-127 cases H–L  :  5/5  passed
Case G — hai bucket quy đổi độc lập                :  2/2  passed
Tra tỉ lệ theo thời điểm — DEC-121                 :  3/3  passed
                                              TỔNG : 36/36
```
31/31 cũ giữ nguyên, cộng case L mới cho guard unmapped.

**Falsification (chứng minh không còn oracle song song):** sửa
`rate: "0.020"` → `"0.030"` trong `config/conversion_rates.yaml` → case E, F,
H **FAIL**, exit 1. Sửa từ khóa `"ADS"` → `"QUANGCAO"` trong
`config/lead_source.yaml` → **12 case FAIL**. Bản cũ có bảng riêng nên sẽ
PASS trong cả hai tình huống. Config đã khôi phục sạch.
Executed By:
Claude (session này)

Timestamp:
2026-08-23

### Functional — EmployeeGroup

#### CHECK-108A1-03 — Vinh/Quý/Hiệp là ba Employee riêng, cùng group NOI_THANH, cùng ra 2%
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`test_case_f_covers_all_three_channel_employees` và
`tests/test_employee_mapper.py::test_channel_employees_keep_identity_and_share_a_group`
— `Đức Hiệp`→`Hiệp`, `Mr Quý`→`Quý`, `Mr Vinh`→`Vinh`, cả ba `group =
NOI_THANH`, cả ba ra `NOI_THANH_2` / 2 %. Assert `len(resolved) == 3` xác nhận
ba danh tính riêng biệt, không bị gộp.

Xác minh trên dữ liệu thật (CHECK-108A1-15): Hiệp 5.328 dòng, Quý 2.810,
Vinh 1.814 — ba giá trị NVBH riêng, không phải fixture.

Executed By:
Claude (session này)

Timestamp:
2026-08-23

#### CHECK-108A1-04 — Thêm nhân viên mới chỉ bằng config, không sửa một dòng .py nào
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`test_new_employee_resolves_without_touching_any_python` — một nhân viên không
có dòng nào trong `conversion_rates.yaml` vẫn phân giải qua dòng `*` ra
`PERSONAL_5_5` / 5,5 %. Thêm nhân viên là sửa `config/employees.yaml`, không
sửa `.py`.

Executed By:
Claude (session này)

Timestamp:
2026-08-23

### Functional — ProductGroup

#### CHECK-108A1-05 — Vinh + DIEN_MAY ra 2%, Vinh + GIA_DUNG ra 8%
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`test_same_employee_different_product_group_gives_different_rate` — cùng Vinh,
cùng PERSONAL, chỉ khác ProductGroup: `DIEN_MAY` → 2 %, `GIA_DUNG` → 8 %.
Bản tham chiếu xác nhận độc lập (case H, I, J).

Executed By:
Claude (session này)

Timestamp:
2026-08-23

#### CHECK-108A1-06 — Ly (STANDARD_SALES) + GIA_DUNG vẫn ra 5,5%, không nhảy lên 8%
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`test_standard_sales_selling_gia_dung_keeps_its_own_scheme` và
`test_standard_sales_line_marked_gia_dung_keeps_five_point_five` — Ly
(`STANDARD_SALES`) + `GIA_DUNG` ra `PERSONAL_5_5` / 5,5 %, **không** nhảy lên
8 %. Bản tham chiếu case K.

Đây là điểm mà 227 dòng hàng Gia dụng do nhóm `STANDARD_SALES` bán trên dữ
liệu thật sẽ lệch nếu khóa `GIA_DUNG_8` trên `*` thay vì trên `NOI_THANH`.

Executed By:
Claude (session này)

Timestamp:
2026-08-23

#### CHECK-108A1-07 — Một OrderID với hai line khác ProductGroup ra hai scheme khác nhau
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`tests/test_conversion_engine.py::test_one_order_two_product_groups_gets_two_schemes`
— một `Order` với hai line, một `DIEN_MAY` một `GIA_DUNG`, cho ra
`NOI_THANH_2` (2 %) và `GIA_DUNG_8` (8 %);
`len({line.conversion_scheme_final for line in order.lines}) == 2`.

Đo trên dữ liệu thật: **118 / 10.609 OrderID** chứa đồng thời cả hai loại.

Executed By:
Claude (session này)

Timestamp:
2026-08-23

#### CHECK-108A1-08 — Provenance phân biệt DEFAULT và MANUAL
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`test_default_and_manual_provenance_are_distinguishable` — cùng giá trị
`DIEN_MAY` nhưng một dòng có `source_of_value = DEFAULT` (rơi về mặc định) và
một dòng `MANUAL` (người dùng tick). Thêm
`test_auto_provider_is_pluggable_and_recorded_as_auto` (nguồn `AUTO`) và
`test_manual_beats_auto_provider` (người dùng thắng máy).

`tests/test_pipeline.py::test_every_line_defaults_to_dien_may_with_visible_provenance`
xác nhận ở Phase 1 mọi dòng là `DIEN_MAY` + `DEFAULT` — nhìn thấy được là
mặc định, không giống một quyết định ai đó đã đưa ra.

Executed By:
Claude (session này)

Timestamp:
2026-08-23

### Functional — Effective-dating và Unresolved

#### CHECK-108A1-09 — Tra tỉ lệ theo ngày của đơn; thêm chính sách tương lai không đổi kết quả kỳ cũ
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`test_lookup_uses_the_order_date_not_today` (đơn 15/03/2026 → 7,5 %) và
`test_a_future_policy_row_does_not_change_a_past_period` — đóng dòng cũ
(`effective_to: 2026-12-31`) rồi mở dòng 2027 ở 6 %: chạy lại kỳ 01.2026 vẫn
ra **5,5 %**, kỳ 06.2027 ra 6 %.

**Bổ sung theo Independent Review #1, Finding 2 (HIGH).** `resolve_final()`
trước đây lấy dòng ĐẦU TIÊN mang tên scheme, bỏ qua effective date. Đã sửa:
nhận tham số `as_of` và dùng cùng `effective_rows()` như `resolve_auto`.

Test qua **hai kỳ effective date**:
`test_manual_override_uses_the_period_matching_the_order_date` — cùng scheme
`PERSONAL_5_5` có 5,5 % (2026) và 6,5 % (2027); override trả đúng tỉ lệ theo
ngày đơn, và assert `in_2026.rate != in_2027.rate` để bắt đúng lỗi cũ.
`test_manual_override_before_any_period_has_no_rate`,
`test_manual_override_without_a_date_refuses_to_guess`,
`test_manual_override_with_two_rates_in_one_period_is_ambiguous` (ném
`AmbiguousSchemeConfigError`).
Executed By:
Claude (session này)

Timestamp:
2026-08-23

#### CHECK-108A1-10 — Không khớp dòng nào trả Unresolved, không mượn tỉ lệ của ai
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
**Sửa theo Independent Review #1, Finding 1 (CRITICAL).** Hành vi cũ cho
nhân viên chưa map rơi vào dòng `* + PERSONAL` → 5,5 %. Reviewer xác định vi
phạm DEC-127 §8. Đã sửa: chặn **trước** khi xét universal rule, ở cả hai tầng.

`app/modules/conversion/scheme_resolver.py` — `resolve_auto()` trả
`Unresolved` / `rate=None` / `source="Unresolved:UnmappedEmployee"` khi
`employee is None` hoặc `employee_group is None`.
`app/modules/conversion/conversion_engine.py` — chặn theo
`employee_mapping_status == MAPPING_STATUS_UNMAPPED` trước mọi tra cứu.

Test: `test_unmapped_employee_is_unresolved_not_borrowed`,
`test_employee_without_a_group_is_also_unresolved`,
`test_unmapped_check_runs_before_the_universal_rule` (cả PERSONAL lẫn ADS),
`test_unmapped_employee_line_never_receives_a_rate`,
`test_unmapped_flag_wins_even_if_a_name_and_group_are_present`,
`tests/test_pipeline.py::test_unmapped_employee_line_gets_no_rate_at_all`,
và case L của `verify_ads_rule.py`.

Các check còn lại giữ nguyên: `test_date_before_effective_from_is_unresolved_not_guessed`,
`test_no_matching_row_is_unresolved`, `test_missing_lead_source_is_unresolved`.
Executed By:
Claude (session này)

Timestamp:
2026-08-23

#### CHECK-108A1-11 — Hai dòng config hòa điểm specificity là lỗi cấu hình, không tự chọn
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`test_equally_specific_rows_raise_instead_of_picking_one` — hai dòng cùng
specificity ném `AmbiguousSchemeConfigError` kèm tên cả hai scheme.

`test_an_unclosed_old_row_is_reported_not_silently_resolved` — mô phỏng lỗi
cấu hình thật (thêm dòng chính sách tương lai mà quên đóng dòng cũ): kỳ 2026
vẫn phân giải bình thường, kỳ 2027 ném lỗi thay vì tự chọn. Chính engine đã
bắt được lỗi này trong bản nháp test đầu tiên của phiên — test được sửa cho
đúng cách đổi chính sách, **rule không bị sửa để test PASS**.

Executed By:
Claude (session này)

Timestamp:
2026-08-23

### Architecture

#### CHECK-108A1-12 — Không hard-code tên nhân viên và không hard-code tỉ lệ trong app/
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Output lệnh grep thực thi:
```
$ grep -rnE '"(Tín Phát|Ly|Hoàng|Kiên|Thắng|Vinh|Quý|Hiệp|Nội thành|Gia dụng)"' app/ --include=*.py
app/modules/domain/models.py:151:    product_group_manual: ...  # checkbox "Gia dụng" ghi vào đây

$ grep -rnE '0\.055|0\.075|0\.02|0\.08|5\.5|7\.5' app/ --include=*.py
app/modules/conversion/scheme_resolver.py:10: (docstring giải thích)
```
Cả hai kết quả duy nhất đều nằm trong **comment/docstring**, không phải
business logic. Không tên nhân viên nào và không tỉ lệ nào được hard-code.

Executed By:
Claude (session này)

Timestamp:
2026-08-23

#### CHECK-108A1-13 — Không đường code nào suy tỉ lệ trực tiếp từ LeadSource
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
```
$ grep -rnE 'if.*(lead_source|LeadSource).*(==|is).*(ADS|PERSONAL)' app/modules/conversion/
(không có kết quả)
```
`lead_source` chỉ xuất hiện làm **khóa lọc** trong list comprehension tra
config (`row.get("lead_source") == lead_source`), không có nhánh `if` nào rẽ
từ nguồn đơn ra tỉ lệ. `test_same_lead_source_different_group_gives_different_rate`
xác nhận cùng `PERSONAL` cho hai tỉ lệ khác nhau tùy group.

Executed By:
Claude (session này)

Timestamp:
2026-08-23

### Data — Đối chiếu dữ liệu thật

#### CHECK-108A1-14 — Reconciliation 55 ô cột F của Summary 2026
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
**Sửa theo Independent Review #1, Finding 3 (HIGH).** Bản cũ hard-code
Employee/EmployeeGroup/ProductGroup cho từng nhãn Summary — tạo PASS giả. Đã
bỏ hoàn toàn bảng đó. Mọi dimension nay lấy từ production: nhãn Summary tra
vào `config/employees.yaml` để lấy `normalized`/`group`/`default_lead_source`;
nguồn đơn khả dĩ tính bằng production `LeadSourceClassifier`; tỉ lệ khả dĩ
tính bằng production `ConversionSchemeResolver`.

**Con số giảm so với báo cáo trước, và đây là con số đúng:**
```
Ô đối chiếu ĐỘC LẬP được  : 36
    khớp                  : 36
    LỆCH                  :  0
Ô KHÔNG đối chiếu được    : 19
    Nội thành  8 · Gia dụng 8 · Fanpage 2 · Linh 1
```
Trước đây báo 52 khớp; 16 ô trong đó chỉ "khớp" nhờ mapping tự gán. Nhãn
`Nội thành`/`Gia dụng` là bút toán gộp ở tầng báo cáo, `Linh`/`Fanpage` là
legacy ngoài master data — không artifact production nào nối chúng với
Employee/EmployeeGroup/ProductGroup, và sheet kênh trong workbook cũng không
có cột nhân viên. **Ghi nhận là GIỚI HẠN, không tính là đối chiếu thành công.**

**Falsification:** đổi `PERSONAL_5_5` 5,5 % → 6,0 % ⇒ **28/36 LỆCH**, exit 1.
Đổi group của Ly `STANDARD_SALES` → `NOI_THANH` ⇒ **đúng 8 ô của Ly LỆCH**.
Config đã khôi phục sạch.
Executed By:
Claude (session này)

Timestamp:
2026-08-23

#### CHECK-108A1-15 — Employee mapping đúng trên file thô toàn công ty
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Output cùng lệnh, phần thứ hai (file thô toàn công ty, 10.703 đơn,
01.01.2026–10.09.2026):
```
Dòng map được   : 14389
    Hiệp       NOI_THANH          5328
    Quý        NOI_THANH          2810
    Vinh       NOI_THANH          1814
    Tín Phát   STANDARD_SALES     1771
    Ly         STANDARD_SALES      990
    Kiên       STANDARD_SALES      733
    Hoàng      STANDARD_SALES      532
    Thắng      STANDARD_SALES      411
Dòng KHÔNG map  : 107  -> Review Queue (C11)
    Thảo Linh 83 · Tống Khánh Linh 14 · Lê Quang Trường 7
    Lê Văn Quân 2 · Nguyễn Thị Minh Bảo 1
```
8 employee map đúng với group đúng trên **dữ liệu production thật**, không
phải fixture. 107 dòng chưa map trả về `unmapped` đúng như C11 quy định.
Prefix `"Đức Kiên"` khớp đúng giá trị thật `"Đức Kiên - Tân Á 0867666533"`.

Executed By:
Claude (session này)

Timestamp:
2026-08-23

### Regression

#### CHECK-108A1-16 — Toàn bộ test cũ vẫn PASS
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`pytest tests/ -q` → **127/127 passed** (83 test cũ + 44 test mới). Không
regression.

Sau Independent Review #1: thêm 8 test (3 unmapped ở resolver, 2 unmapped ở
engine, 4 manual-override qua hai kỳ effective date, trừ trùng lặp), và sửa
2 test đang assert hành vi cũ
(`test_unmapped_employee_is_unresolved_not_borrowed`,
`test_unmapped_employee_line_gets_no_rate_at_all`) — **sửa test theo rule đã
được reviewer xác định là đúng, không sửa rule theo test.**
Executed By:
Claude (session này)

Timestamp:
2026-08-23

## Tiêu Chí Hoàn Thành (Exit Criteria)
- [x] 100 % REQUIRED check PASS — 16/16.
- [x] Evidence level E1 cho mọi check.
- [x] Không sửa business rule để làm test PASS — một test của chính tôi bị
      engine bắt lỗi cấu hình; **test được sửa, rule giữ nguyên**.
- [x] `PROJECT/PROJECT_PROGRESS.md` và `PROJECT/LO_TRINH_DE_HIEU.md` cập nhật.
- [x] Session handoff đã viết.
- [x] 5 validator governance chạy (4 PASS; 1 FAIL có sẵn thuộc Track B).
- [x] Commit + push. **KHÔNG merge** — chờ independent review PASS.

## Điều Kiện Kích Hoạt Leo Thang (Escalation Triggers)
- Reconciliation 55 ô lệch ở bất kỳ ô nào → **dừng, báo cáo số liệu và
  nguyên nhân dự kiến trước khi sửa bất cứ thứ gì.** Tuyệt đối không chỉnh
  rule để ép khớp.
- Xuất hiện nhu cầu dimension thứ năm → **không tự mở rộng công thức
  specificity**; mở lại ADR-106 và để chủ dự án quyết định thứ tự ưu tiên.
- Phát hiện tổ hợp `(Nội thành, ADS)` hoặc `(Gia dụng, ADS)` có khối lượng
  đáng kể trong dữ liệu thật → C9/DEC-122 đã chấp nhận 7,5 %, nhưng nếu số
  lượng lớn thì báo lại để chủ dự án xem lại.

## Đăng Ký File Đã Thay Đổi (Changed Files Registry)

Created:
- `config/conversion_rates.yaml`
- `app/modules/conversion/__init__.py`, `scheme_resolver.py`, `conversion_engine.py`
- `app/modules/product/__init__.py`, `product_group.py`
- `tests/test_scheme_resolver.py`, `tests/test_conversion_engine.py`
- `tools/analysis/reconcile_conversion.py`
- `docs/adr/ADR-106-product-group-and-line-level-conversion.md`
- `docs/tasks/TASK-108A-1-conversion-scheme-resolver.md`
- `docs/sessions/S014-task-108a-1-conversion-scheme-resolver.md`

Modified:
- `config/employees.yaml` — `employee_groups`; tách Vinh/Quý/Hiệp; thêm `group`
- `app/modules/mapping/employee_mapper.py` — `MappingResult.group`
- `app/modules/domain/models.py` — hằng ProductGroup + 9 field mới
- `app/pipeline.py` — bước 10, tham số `product_group_provider`
- `tests/test_employee_mapper.py`, `tests/test_pipeline.py` — theo rule mới
- `tools/analysis/verify_ads_rule.py` — bảng 4 chiều, `Decimal`, case H–K
- `PROJECT/PROJECT_DECISIONS.md` — DEC-127
- `docs/analysis/10_OPEN_QUESTIONS.md` — C11 số thật, C15 mới
- `PROJECT/PROJECT_PROGRESS.md`, `PROJECT/LO_TRINH_DE_HIEU.md`

Deleted:
- Không có.

Migration Impact:
- Không có DB. **Nhưng `employee_normalized` đổi giá trị** cho 3 nhân viên
  kênh (`Nội thành` → `Vinh`/`Quý`/`Hiệp`). Bất kỳ dữ liệu nào đã lưu tên cũ
  cần map lại — hiện chưa có dữ liệu nào được persist nên không phát sinh.

## Ghi Chú (Notes)

**Công thức specificity là quy ước phân giải của ADR-106, không phải business
rule bất biến** (chủ dự án ghi rõ khi phê duyệt Gate v3). Trọng số
`4×employee + 2×employee_group + 1×product_group` phản ánh trực giác "cá nhân
cụ thể hơn nhóm, nhóm cụ thể hơn loại hàng". Không tự mở rộng khi có dimension
mới.

**Ba file dữ liệu thật** (workbook báo cáo + 2 file thô) nằm ngoài repo,
không commit, xóa sau phiên (DEC-108).
