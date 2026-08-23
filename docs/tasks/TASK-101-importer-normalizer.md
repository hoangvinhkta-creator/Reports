# TASK-101 — Importer + Normalizer

## Metadata
Status:
VERIFYING — 12/13 REQUIRED check PASS trên fixture tổng hợp; CHECK-101-08
BLOCKED vì thiếu `data/samples/` thật trong môi trường này (không phải lỗi
implementation). Xem "Ghi Chú".

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

#### CHECK-101-05 — Lead source classifier khớp 18 case chuẩn (§29 đặc tả + DEC-109) và 8 case A–G (DEC-119)
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`pytest tests/test_lead_source_classifier.py -q` → 19/19 passed (18 case
LeadSource port nguyên văn từ `tools/analysis/verify_ads_rule.py` + 1 test
propagate). **Không port lại 8 case A–G** vì chúng kiểm cả
`ConversionScheme`, thuộc phạm vi TASK-108 — ngoài scope TASK-101 (chỉ phân
loại `LeadSource`). Đối chiếu hành vi với bản tham chiếu
(`tools/analysis/verify_ads_rule.py`, 31/31 PASS) xác nhận cùng kết quả trên
18 case LeadSource dùng chung.

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
**BLOCKED**

Evidence Level:
E1 (yêu cầu, không đạt được trong session này)

Evidence:
`data/samples/So_chi_tiet_ban_hang.xlsx` không tồn tại trong môi trường thực
thi hiện tại (đúng theo DEC-108 — dữ liệu cá nhân khách hàng không commit vào
git, chỉ tồn tại cục bộ nơi phân tích ban đầu được thực hiện). Không thể chạy
lại `raw_reader`/`pipeline` trên file thật để đối chiếu 254/146 đơn.

Executed By:
—

Timestamp:
—

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
- [x] 100% REQUIRED check PASS **hoặc** BLOCKED có lý do hợp lệ ghi rõ —
      12/13 PASS, CHECK-101-08 BLOCKED (thiếu `data/samples/` thật).
- [x] Không có lỗi nghiêm trọng chưa xử lý.
- [x] Evidence level E1 đạt được cho mọi check thực thi được trên fixture.
- [x] `PROJECT/PROJECT_PROGRESS.md` và `PROJECT/LO_TRINH_DE_HIEU.md` cập
      nhật đồng thời.
- [x] Session handoff đã viết (MAJOR task).
- [x] Task **không** chuyển DONE — dừng ở VERIFYING vì CHECK-101-08 còn
      BLOCKED, chờ chủ dự án cung cấp `data/samples/` hoặc chấp nhận đối
      chiếu này dời sang môi trường có dữ liệu thật.

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

Modified:
- (cập nhật `PROJECT/PROJECT_PROGRESS.md`, `PROJECT/LO_TRINH_DE_HIEU.md` ở
  bước đóng phiên — xem "Ghi Chú")

Deleted:
- Không có.

Migration Impact:
- Không có (chưa có DB ở Phase 1).

## Ghi Chú (Notes)

**Giới hạn quan trọng của session này:** `data/samples/So_chi_tiet_ban_hang.xlsx`
và `data/samples/Bao_cao_Kinh_doanh_2026.xlsx` không tồn tại trong môi trường
thực thi này. Đây không phải lỗi cấu hình — đúng theo DEC-108, hai file này
**không bao giờ được commit** vì chứa dữ liệu cá nhân khách hàng. Chúng chỉ
tồn tại cục bộ nơi TASK-002 (phân tích ban đầu) được thực hiện.

Hệ quả: mọi evidence trong Completion Gate này lấy từ **fixture tổng hợp đã
ẩn danh** (theo đúng yêu cầu của DEC-108 cho test fixture), không phải từ file
thật. Check REQUIRED duy nhất cần file thật (CHECK-101-08 — đối chiếu 254/146
đơn) được đánh dấu **BLOCKED**, không PASS giả, không bịa bằng chứng.

Khi chủ dự án cung cấp lại `data/samples/` (đặt vào thư mục, không commit),
chạy:
```bash
python3 -c "from app.pipeline import run_import; ..."
```
để đối chiếu và cập nhật CHECK-101-08.
