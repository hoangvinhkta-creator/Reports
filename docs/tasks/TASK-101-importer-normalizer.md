# TASK-101 — Importer + Normalizer

## Metadata
Status:
DONE

Status Note:
13/13 REQUIRED check PASS. CHECK-101-08 đối chiếu trên dữ liệu thật Tín Phát
01.2026 và 06.2026 (254/146 đơn khớp tuyệt đối), không sai lệch nghiệp vụ
đáng kể. Xem "Đối Chiếu Dữ Liệu Thật (2026-08-23)".

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
3/5

Project Profile:
PRODUCT

## Mục Tiêu (Objective)

Xây dựng engine Python thuần (không UI, không database — theo ADR-101) đọc
sổ bán hàng thô `.xlsx`, chuẩn hóa dữ liệu, áp employee mapping, nhóm dòng
thành đơn theo `OrderID`, và phân loại `LeadSource` cấp đơn — đúng 7 bước đầu
của import workflow ở mục §22 đặc tả:

1. Đọc `.xlsx` (header dòng 4, bỏ dòng 5, dữ liệu từ dòng 6 —
   `docs/analysis/01_DATA_MAPPING.md` §1).
2. Báo cáo metadata (số dòng, khoảng ngày, tổng doanh số, số đơn, số NVBH)
   trước khi chuẩn hóa/commit.
3. Chuẩn hóa cột — Raw → Working, trừ `Chiết khấu` khỏi doanh số (DEC-114).
4. Áp employee mapping (DEC-104).
5. Nhóm theo `OrderID` thành `Order`.
6. Áp rule ADS ở cấp đơn (DEC-119, ADR-104).
7. Propagate `LeadSourceFinal` xuống từng `WorkingLine` của đơn.

## Phạm Vi (Scope)

- Domain models thuần (dataclass, `Decimal`) cho `RawRow`, `WorkingLine`, `Order`.
- Đọc file `.xlsx` thô đúng layout 17 cột đã xác nhận ở `docs/analysis/01_DATA_MAPPING.md`.
- Metadata preview trước khi chuẩn hóa.
- Chuẩn hóa cột, trừ chiết khấu.
- Employee mapping qua `config/employees.yaml` (DEC-104); dòng chưa map được
  flag, không bị bỏ.
- Nhóm dòng theo `OrderID`.
- Phân loại `LeadSource` cấp đơn theo chuỗi 4 bậc (DEC-109/119, ADR-104) qua
  `config/lead_source.yaml`; propagate xuống line.
- Pipeline orchestration nối các bước trên thành một hàm gọi được.
- Test đơn vị + tích hợp trên fixture tổng hợp đã ẩn danh (DEC-108).

## Ngoài Phạm Vi (Out of Scope)

- Product/transaction classification (dòng phụ có giá trị tiền như `Chi phí
  vận chuyển`) — thuộc TASK-103.
- `price_engine`, `adjustment_engine`, `profit_engine`, `conversion_engine`
  — TASK-105 đến TASK-108.
- Review Queue UI/persistence đầy đủ — TASK-110. TASK-101 chỉ đảm bảo dòng
  chưa map không bị bỏ, chưa xây hàng đợi hoàn chỉnh.
- CLI — TASK-112.
- Đối chiếu với file thô thật (254 đơn 01.2026, 146 đơn 06.2026) — cần
  `data/samples/` thật, **không có trong session này** (DEC-108: dữ liệu cá
  nhân khách hàng không commit). Xem "Ghi Chú" và Completion Gate bên dưới.

## Phụ Thuộc (Dependencies)
- GATE-00 — PASS (DEC-122).
- `docs/analysis/01_DATA_MAPPING.md`, `docs/analysis/03_RULE_CLASSIFICATION.md` — layout và
  business rule đã xác nhận.
- ADR-101 (kiến trúc), ADR-102 (3 lớp dữ liệu), ADR-103 (đơn vị tiền),
  ADR-104 (LeadSource/ConversionScheme).

## Chặn (Blocks)
- TASK-102, TASK-103, TASK-104 (roadmap liệt kê riêng nhưng năng lực lõi của
  chúng — employee mapping, order grouping, lead source — được xây ở đây làm
  module độc lập, có thể mở rộng ở các task sau mà không phá interface).
- TASK-105..112.

## An Toàn Để Chạy Song Song Với (Parallel-Safe With)
- Track B (Governance) — không chạm chung file.

## Phạm Vi Tác Động Dự Kiến (Expected Touch Area)

Allowed:
- `app/modules/domain/`
- `app/modules/config/`
- `app/modules/importing/`
- `app/modules/mapping/`
- `app/modules/orders/`
- `app/modules/lead_source/`
- `app/pipeline.py`
- `config/employees.yaml`, `config/lead_source.yaml`
- `tests/` (mới)
- `docs/tasks/TASK-101-importer-normalizer.md`
- `PROJECT/PROJECT_PROGRESS.md`, `PROJECT/LO_TRINH_DE_HIEU.md`
- `docs/sessions/`

Không được đụng vào nếu chưa có Scope Expansion:
- `docs/analysis/`, `docs/adr/`, `PROJECT/PROJECT_DECISIONS.md` (đã đóng ở
  session trước — không sửa trừ khi phát hiện sai lệch cần CONFLICT DETECTED).
- Bất kỳ file nào của Track B (`docs/audit/`, `docs/tasks/TASK-REM-*.md`).

## Subtask (Subtasks)
- [x] 101.1 Domain models
- [x] 101.2 Config loader + `employees.yaml` + `lead_source.yaml`
- [x] 101.3 Raw reader
- [x] 101.4 Metadata preview
- [x] 101.5 Normalizer (trừ chiết khấu)
- [x] 101.6 Employee mapper
- [x] 101.7 Order builder
- [x] 101.8 Lead source classifier
- [x] 101.9 Pipeline orchestration
- [x] 101.10 Fixture ẩn danh + test suite (49/49 PASS)

## Ready Gate
Dùng `governance/core/TASK_READY_GATE_STANDARD.md`.

- [x] Objective rõ ràng.
- [x] Scope đã được xác định.
- [x] Out-of-scope đã được xác định.
- [x] Dependency (GATE-00) đã DONE.
- [x] Vùng tác động dự kiến đã được xác định.
- [x] Yêu cầu liên quan đã hiểu rõ (đặc tả §22, DEC-104/109/114/119).
- [x] Tác động dữ liệu đã biết rõ: dữ liệu cá nhân khách hàng trong RawRow,
      không log ra ngoài, không commit fixture thật.
- [x] Tác động bảo mật đã biết rõ: không có, chưa có network/DB ở Phase 1.
- [x] Không liên quan routing/API (Phase 1 thuần Python).
- [x] Không có migration (chưa có DB).
- [x] Difficulty/Risk/Blast Radius đã chấm điểm (3/3/3, theo bảng sơ bộ
      `PROJECT/PROJECT_PROGRESS.md`).
- [x] Agent tier đã chỉ định (B, escalation C).
- [x] Escalation trigger đã xác định (xem bên dưới).
- [x] Completion Gate đã hoàn thiện và **frozen** trước khi implement.

## Completion Gate
Dùng `governance/core/TASK_COMPLETION_GATE_STANDARD.md` và
`governance/core/EVIDENCE_STANDARD.md`.

### Functional

#### CHECK-101-01 — Raw reader đọc đúng layout
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Trên **fixture tổng hợp** `tests/fixtures/synthetic_workbook.py`, **không
phải trên file thật** — xem giới hạn ở "Ghi Chú" cuối file.
`pytest tests/test_raw_reader.py -q` → 5/5 passed. Xác nhận: đọc đúng 8/8
dòng dữ liệu (7 đơn), bỏ đúng dòng 5 (header tầng 2), `source_row` bắt đầu từ
6, `date` parse ra `datetime.date`, dòng thiếu SL giữ `quantity = None` (không
phải 0), `source_file`/`source_sheet`/`row_hash` được ghi nhận.

Executed By:
Claude (session này)

Timestamp:
2026-08-23

#### CHECK-101-02 — Normalizer trừ đúng Chiết khấu (DEC-114)
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`pytest tests/test_normalizer.py -q` → 6/6 passed. Xác nhận công thức
`TotalSales = SellPrice × Quantity − Discount`: `300000×2−50000=550000`;
thiếu `Quantity` hoặc `SellPrice` → `total_sales = None` (không phải 0);
thiếu `Discount` → coi là 0.

Executed By:
Claude (session này)

Timestamp:
2026-08-23

#### CHECK-101-03 — Employee mapper: map đúng, dòng chưa map được flag không bị bỏ
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`pytest tests/test_employee_mapper.py -q` → 7/7 passed. Xác nhận: 8 raw
prefix trong `config/employees.yaml` map đúng theo
`docs/analysis/01_DATA_MAPPING.md` §5
(Ly, Hoàng, Kiên, Thắng, Tín Phát; Đức Hiệp/Mr Quý/Mr Vinh → Nội thành); Tín
Phát có `default_lead_source = ADS`; nhân viên không khớp prefix nào →
`status = unmapped`, không raise, không bỏ; ngày trước `effective_from` →
`unmapped` (kiểm chứng effective-dating hoạt động).

Executed By:
Claude (session này)

Timestamp:
2026-08-23

#### CHECK-101-04 — Order builder nhóm đúng theo OrderID (kể cả đơn nhiều dòng)
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`pytest tests/test_order_builder.py -q` → 3/3 passed. Xác nhận nhóm 3 dòng
thành 2 đơn đúng số dòng mỗi đơn, `Order.total_sales` cộng đúng các dòng.

Executed By:
Claude (session này)

Timestamp:
2026-08-23

#### CHECK-101-05 — Lead source classifier khớp 18 case LeadSource chuẩn (§29 đặc tả + §13 + DEC-109)
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`pytest tests/test_lead_source_classifier.py -q` → 19/19 passed (18 case
LeadSource port nguyên văn từ `tools/analysis/verify_ads_rule.py` + 1 test
propagate). Đối chiếu hành vi với bản tham chiếu
(`tools/analysis/verify_ads_rule.py`, 31/31 PASS) xác nhận cùng kết quả trên
18 case LeadSource dùng chung.

**Phạm vi check này chỉ là `LeadSource`.** 8 case A–G của DEC-119 (đối chiếu
2%/5,5%/7,5%/8% và `ConversionScheme`) **không thuộc phạm vi TASK-101** —
TASK-101 chỉ quyết định nguồn đơn (`PERSONAL`/`ADS`), không quyết định tỉ lệ.
8 case A–G đã có sẵn và PASS trong bản tham chiếu, để nguyên cho TASK-108 kế
thừa khi xây `ConversionScheme`; không port lại ở đây vì đó là claim ngoài
scope của task này (sửa theo góp ý review 2026-08-23 — heading cũ nêu "8 case
A–G" gây hiểu nhầm task đã kiểm chúng).

Executed By:
Claude (session này)

Timestamp:
2026-08-23

#### CHECK-101-06 — LeadSourceFinal propagate xuống mọi line cùng OrderID
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`test_apply_propagates_to_every_line` (trong
`tests/test_lead_source_classifier.py`) + `test_order_with_ads_line_propagates_to_all_lines`
(trong `tests/test_pipeline.py`): đơn `BH0002` (2 dòng, dòng 2 có "ADS") →
cả 2 dòng đều nhận `lead_source_final = ADS`.

Executed By:
Claude (session này)

Timestamp:
2026-08-23

#### CHECK-101-07 — Metadata preview đúng số liệu trước khi chuẩn hóa
Priority:
RECOMMENDED

Status:
PASS

Evidence Level:
E1

Evidence:
`pytest tests/test_pipeline.py::test_preview_matches_synthetic_file -q` +
chạy tay `run_import()` trên fixture: `row_count=8`,
`distinct_order_count=7`, `date range=2026-01-15 → 2026-01-21`,
`total_sales_raw=11.600.000`.

Executed By:
Claude (session này)

Timestamp:
2026-08-23

#### CHECK-101-08 — Đối chiếu số đơn thật: Tín Phát 254 đơn (01.2026), 146 đơn (06.2026)
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Chủ dự án cung cấp trực tiếp 2 file thật ngày 2026-08-23:
`So_chi_tiet_ban_hang_TinPhat_01.2026.xlsx` (xuất riêng Tín Phát, tháng
01/2026) và `..._06.2026.xlsx` (tháng 06/2026) — không commit vào git, đặt
tạm ở `data/samples/` trong phiên làm việc theo đúng DEC-108, xóa sau khi
dùng xong.

Chạy `python3 tools/analysis/reconcile_real_data.py <file> --expected-orders <N>`
gọi thẳng `app.pipeline.run_import()` — không phải bản mô phỏng:

```
01.2026: Số OrderID duy nhất: 254  ->  Kỳ vọng: 254 đơn -> PASS
06.2026: Số OrderID duy nhất: 146  ->  Kỳ vọng: 146 đơn -> PASS
```

Đối chiếu chéo độc lập: dòng "Tổng cộng" tự viết trong chính file thô
(không do engine tính) khớp tuyệt đối với tổng do `run_import()` tính —
01.2026: Doanh số bán 3.564.610.000 và Chiết khấu 2.300.000 đều khớp; 06.2026:
1.925.272.000 và 400.000 đều khớp. Xác nhận `raw_reader` đọc đủ, không sót,
không đếm trùng dòng nào.

Đối chiếu đầy đủ (mapping, LeadSource, so sánh doanh số raw vs normalized):
xem mục "Đối chiếu dữ liệu thật (2026-08-23)" ở cuối file.

Executed By:
Claude (session này)

Timestamp:
2026-08-23

### Architecture

#### CHECK-101-09 — Không import fastapi/sqlalchemy/web trong app/modules/ (ADR-101)
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
```
$ grep -rn "^import fastapi\|^from fastapi\|^import sqlalchemy\|^from sqlalchemy\|^import flask\|^from flask" app/
(không có kết quả)
```

Executed By:
Claude (session này)

Timestamp:
2026-08-23

#### CHECK-101-10 — Không hard-code business value (rate, keyword, target) trong code
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Output lệnh `grep` thực thi:
```
$ grep -rnE "0\.0?55|0\.0?75|5\.5\s*%|7\.5\s*%|\"ADS\"|'ADS'" app/
app/modules/domain/models.py:21:ADS = "ADS"
```
Kết quả duy nhất là hằng số cấu trúc `ADS = "ADS"` định nghĩa giá trị enum
`LeadSource` (bất biến kiến trúc theo DEC-119/ADR-104, không phải business
rule). Không có tỉ lệ (5,5%/7,5%), target, hay từ khóa nào bị hard-code —
tất cả nằm trong `config/employees.yaml` và `config/lead_source.yaml`.

Executed By:
Claude (session này)

Timestamp:
2026-08-23

### Data

#### CHECK-101-11 — RAW bất biến, giữ source_file/source_sheet/source_row (ADR-102)
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`app/modules/domain/models.py` — `RawRow` là `@dataclass(frozen=True)`
(không có setter, sửa field sẽ raise `FrozenInstanceError`), giữ đủ
`source_file`, `source_sheet`, `source_row`, `row_hash`. Xác nhận bằng
`test_source_provenance_recorded` (`tests/test_raw_reader.py`) — PASS.

Executed By:
Claude (session này)

Timestamp:
2026-08-23

#### CHECK-101-12 — Tiền lưu Decimal VND nguyên, không float (ADR-103)
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Mọi field tiền trong `RawRow`/`WorkingLine` kiểu `Decimal`.
`app/modules/domain/money.py::to_decimal()` là điểm chuyển đổi duy nhất từ
giá trị ô Excel, quy đổi `float` qua `str()` trước khi vào `Decimal` (tránh
lỗi làm tròn nhị phân), từ chối `bool`. Không có `float(...)` nào coerce một
field tiền ở bất kỳ module nào (grep xác nhận). Test
`test_total_sales_deducts_discount` xác nhận phép trừ chiết khấu chính xác
tuyệt đối trên `Decimal`.

Executed By:
Claude (session này)

Timestamp:
2026-08-23

### Security

#### CHECK-101-13 — Không log dữ liệu cá nhân khách hàng (RISK-04)
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
```
$ grep -rn "print(\|logging\." app/
(không có kết quả)
```
Chưa có lệnh log/print nào trong `app/` ở Phase 1 — không có đường nào để dữ
liệu cá nhân khách hàng (`customer`, `phone`, `address` trong `RawRow`/
`WorkingLine`) bị ghi ra ngoài. Ràng buộc này cần rà lại khi TASK-110/202
thêm logging/audit trail.

Executed By:
Claude (session này)

Timestamp:
2026-08-23

## Tiêu Chí Hoàn Thành (Exit Criteria)
- [x] 100% REQUIRED check PASS — **13/13 PASS** (CHECK-101-08 đối chiếu trên
      dữ liệu thật Tín Phát 01.2026/06.2026, 2026-08-23).
- [x] Không có lỗi nghiêm trọng chưa xử lý.
- [x] Evidence level E1 đạt được cho mọi check, kể cả CHECK-101-08 trên dữ
      liệu thật (không còn giới hạn ở fixture).
- [x] `PROJECT/PROJECT_PROGRESS.md` và `PROJECT/LO_TRINH_DE_HIEU.md` cập
      nhật đồng thời.
- [x] Session handoff đã viết (MAJOR task).
- [x] **TASK-101 chuyển DONE.** Không sai lệch nghiệp vụ đáng kể trên dữ liệu
      thật; mọi chênh lệch quan sát được giải thích bằng DEC-114 đã biết
      trước, không phải lỗi mới. Không sửa business rule nào để ép khớp.

## Điều Kiện Kích Hoạt Leo Thang (Escalation Triggers)
- Số liệu đối chiếu (khi có file thật) lệch quá 3 đơn ở nhiều kỳ liên tiếp,
  không giải thích được bằng loại trừ tay đã biết.
- Phát hiện mâu thuẫn giữa `docs/analysis/01_DATA_MAPPING.md` và layout thật
  của file (nếu và khi có file để đối chiếu).

## Đăng Ký File Đã Thay Đổi (Changed Files Registry)

Created:
- `app/__init__.py`, `app/pipeline.py`
- `app/modules/domain/__init__.py`, `models.py`, `money.py`
- `app/modules/config/__init__.py`, `loader.py`
- `app/modules/importing/__init__.py`, `raw_reader.py`, `preview.py`, `normalizer.py`
- `app/modules/mapping/__init__.py`, `employee_mapper.py`
- `app/modules/orders/__init__.py`, `order_builder.py`
- `app/modules/lead_source/__init__.py`, `classifier.py`
- `config/employees.yaml`, `config/lead_source.yaml`
- `pyproject.toml`
- `tests/__init__.py`, `conftest.py`, `factories.py`
- `tests/fixtures/__init__.py`, `synthetic_workbook.py`
- `tests/test_raw_reader.py`, `test_normalizer.py`, `test_employee_mapper.py`,
  `test_order_builder.py`, `test_lead_source_classifier.py`, `test_pipeline.py`
- `docs/tasks/TASK-101-importer-normalizer.md`
- `tools/analysis/reconcile_real_data.py` (script đối chiếu dữ liệu thật,
  2026-08-23, phiên đóng CHECK-101-08)

Modified:
- `PROJECT/PROJECT_PROGRESS.md`, `PROJECT/LO_TRINH_DE_HIEU.md` — đồng bộ theo
  "Giao thức Đóng Phiên" ở cả hai lần cập nhật (implement, và đóng
  CHECK-101-08)
- `docs/tasks/TASK-101-importer-normalizer.md` — CHECK-101-05 sửa wording,
  CHECK-101-08 PASS, thêm mục "Đối Chiếu Dữ Liệu Thật"

Deleted:
- `data/samples/So_chi_tiet_ban_hang_TinPhat_01.2026.xlsx`,
  `..._06.2026.xlsx` — file thật do chủ dự án cung cấp, dùng xong xóa khỏi
  môi trường làm việc, đúng DEC-108. Không commit vào git tại bất kỳ thời
  điểm nào.

Migration Impact:
- Không có (chưa có DB ở Phase 1).

## Đối Chiếu Dữ Liệu Thật (2026-08-23)

Chủ dự án cung cấp trực tiếp file thô thật của Tín Phát, xuất riêng theo
tháng: `So_chi_tiet_ban_hang_TinPhat_01.2026.xlsx` và
`..._06.2026.xlsx`. Chạy `tools/analysis/reconcile_real_data.py` gọi thẳng
`app.pipeline.run_import()` — kết quả production thật, không phải mô phỏng.
File không commit, đúng DEC-108.

### Tóm tắt hai kỳ

| Chỉ số | 01.2026 | 06.2026 |
|---|---:|---:|
| Dòng dữ liệu trong sheet (kể cả dòng "Tổng cộng") | 352 | 181 |
| Dòng thiếu OrderID (là dòng "Tổng cộng", bị loại đúng ý) | 1 | 1 |
| Dòng có OrderID, đọc vào RawRow | 351 | 180 |
| **Số OrderID duy nhất** | **254** | **146** |
| Kỳ vọng (chủ dự án cho trước) | 254 | 146 |
| **Kết quả** | **KHỚP TUYỆT ĐỐI** | **KHỚP TUYỆT ĐỐI** |
| Dòng employee mapped / unmapped | 351 / 0 | 180 / 0 |
| OrderID có >1 employee_raw khác nhau trong cùng đơn | 0 | 0 |
| Tổng "Doanh số bán" (raw, VND) | 3.564.610.000 | 1.925.272.000 |
| Tổng Chiết khấu (VND) | 2.300.000 | 400.000 |
| Tổng doanh số normalized (SellPrice×Qty−Discount) | 3.562.310.000 | 1.924.872.000 |
| PERSONAL | 0 | 0 |
| ADS qua mặc định Tín Phát (Auto:Employee Default) | 254 | 146 |
| ADS qua từ khóa "ADS" trong ghi chú (Auto:ADS Rule) | 0 | 0 |
| Số dòng lệch raw vs normalized | 22 / 351 | 1 / 180 |
| Tổng chênh lệch (= tổng chiết khấu) | 2.300.000 | 400.000 |

### Đối chiếu chéo độc lập — không phụ thuộc engine

Cả hai file thô có sẵn dòng "Tổng cộng" tự viết ở cuối sheet (không do engine
này tạo ra). Tổng đó khớp tuyệt đối với tổng do `run_import()` tính:

- 01.2026: Doanh số bán `3.564.610.000` và Chiết khấu `2.300.000` — khớp.
- 06.2026: Doanh số bán `1.925.272.000` và Chiết khấu `400.000` — khớp.

Đây là bằng chứng độc lập rằng `raw_reader` đọc đủ mọi dòng, không sót,
không đếm trùng — vì nếu sót hoặc trùng một dòng bất kỳ, tổng sẽ lệch với
dòng "Tổng cộng" của chính file nguồn.

### 100% đơn Tín Phát là ADS, qua mặc định — không qua từ khóa

Cả 254 + 146 = 400 đơn đều phân loại `ADS`, toàn bộ qua
`Auto:Employee Default (Tín Phát)` — đúng DEC-109. **0 đơn** khớp qua từ khóa
"ADS" trong ghi chú, ở cả hai tháng. Xác nhận độc lập bằng
`re.search("ADS", note, IGNORECASE)` trực tiếp trên toàn bộ cột `Diễn giải`
của cả hai file — **0 kết quả** — khớp đúng phát hiện đã ghi ở
`docs/analysis/06_ADS_RULE_VERIFICATION.md` §1 (chuỗi "ADS" không xuất hiện
trong dữ liệu công ty tính đến 06.2026).

### Item 4 — So sánh `Doanh số bán` (raw) với `SellPrice × Quantity − Discount`

**Pattern duy nhất, nhất quán 100% ở cả hai tháng:** mọi dòng lệch đều lệch
đúng bằng số tiền ở cột `Chiết khấu` của chính dòng đó — không hơn, không
kém, không có dòng nào lệch một số khác. 22/351 dòng lệch ở 01.2026 (tất cả
số lệch cộng lại đúng bằng tổng chiết khấu 2.300.000); 1/180 dòng lệch ở
06.2026 (đúng bằng 400.000).

**Đây không phải một phát hiện mới.** Đây chính là hành vi mà TASK-002 đã ghi
nhận và DEC-114 đã quyết định xử lý từ 2026-08-22 — `Doanh số bán` trong file
thô là số **gross**, ERP chưa từng trừ chiết khấu. `TotalSales` do engine
tính (`SellPrice × Quantity − Discount`) mới là con số đã sửa đúng theo
DEC-114. Dữ liệu thật của Tín Phát tháng 01 và 06/2026 xác nhận lại đúng
pattern đó trên một tập dữ liệu hoàn toàn độc lập với 6 tháng dùng để phân
tích ban đầu — **không có pattern lệch nào khác, không có dòng nào lệch bất
thường**. Không cần và không thay đổi business rule.

### Kết luận

Không phát hiện sai lệch nghiệp vụ đáng kể. Mọi chênh lệch quan sát được đều
giải thích được bằng đúng một quy tắc đã biết trước (DEC-114), không phải
lỗi logic mới. CHECK-101-08 chuyển PASS.

## Ghi Chú (Notes)

**Giới hạn ban đầu (2026-08-23, phiên implement) — ĐÃ ĐÓNG.**
`data/samples/So_chi_tiet_ban_hang.xlsx` không tồn tại trong môi trường thực
thi phiên implement — đúng theo DEC-108, không phải lỗi cấu hình. Mọi
evidence CHECK-101-01 đến 07 và 09–13 lấy từ **fixture tổng hợp đã ẩn danh**;
CHECK-101-08 khi đó BLOCKED, không PASS giả, không bịa bằng chứng.

**Cùng ngày, phiên sau:** chủ dự án cung cấp trực tiếp 2 file thật (Tín Phát
01.2026 và 06.2026, xuất riêng theo tháng). Chạy đối chiếu bằng
`tools/analysis/reconcile_real_data.py` — xem mục "Đối Chiếu Dữ Liệu Thật"
ở trên. CHECK-101-08 chuyển **PASS**, không sai lệch nghiệp vụ đáng kể, không
sửa business rule nào để ép khớp. Cả hai file thô đã dùng xong bị xóa khỏi
`data/samples/` sau khi đối chiếu, đúng DEC-108 — không tồn tại vĩnh viễn
trong môi trường làm việc.
