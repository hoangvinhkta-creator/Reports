# RÀ SOÁT ĐỘC LẬP E2 (E2 INDEPENDENT REVIEW) — TASK-PRA-003 TOÀN TASK

Review ID:
PRA-003-WHOLE-TASK-REVIEW-1

Task / Release:
TASK-PRA-003 — Tổng Quan + Nhân Viên (màn hình quản lý đọc từ nền dữ liệu
PRA-002), đối chiếu với Completion Gate FROZEN tại S095

Reviewer Session:
S097 — Independent Review E2 (nhánh
`claude/pra-003-roadmap-finalization-di33bn`, docs-only)

Executed By:
S097 — TASK-PRA-003 Independent Review E2 (2026-09-03)

Timestamp:
2026-09-03

Evidence Level:
E2 — mọi kết luận chức năng đều do reviewer TỰ CHẠY LẠI trong phiên. Các
khẳng định về tổng số được recompute bằng SQL THÔ trong Python, độc lập với
`analytics_queries`, rồi mới đem so với module triển khai. Phần chỉ đọc mã
(cấu trúc bảng, ràng buộc CHECK) được ghi rõ là suy luận tĩnh có dẫn nguồn.

## Scope

Independent Review E2 cấp TOÀN TASK để quyết định `CHECK-PRA003-12`. Không
implementation, không repair, không rerun Production Acceptance, không
`CHECK-PRA003-07`, không migration/schema, không Tracking, không REM-T06,
không refactor, không mở PRA-004/PRA-005.

### Authority — xác minh TRƯỚC khi đọc bất kỳ file governance nào

```
Nhánh mặc định thật trên origin : claude/extract-upload-repo-gq2ws4
BASE_SHA (kỳ vọng / thực tế)    : facf090c782b022730ecc5f1cf0d0b02e29ca8d7  ✓ KHỚP
REVIEW_TARGET (kỳ vọng/thực tế) : a36f95917ce35acee0a05e215fbfa08df3a9ebe9  ✓ KHỚP
CONTRACT_SHA (kỳ vọng/thực tế)  : c12c5635b5e4298a9584b5fa93e21762c0d70c5b  ✓ KHỚP
REVIEW_TARGET_MOVED             : KHÔNG
branch_authority_check.sh       : AUTHORITY_OK · DIVERGENCE = WITHIN_LIMITS
```

Clone ban đầu là shallow; đã `git fetch --unshallow` (252 commit) TRƯỚC khi đo
để commit lịch sử tồn tại cục bộ.

### Frozen contract có bị sửa giữa freeze và implementation không?

CÓ — và reviewer đã đọc nguyên văn diff `c12c563..a36f959` trên file task.
Kết luận: **mọi thay đổi đều nằm ở trường ghi bằng chứng**
(`Status: NOT_TESTED → PASS`, `Executed By`, `Timestamp`, khối "Kết quả S096")
và ở bảng touch-area cuối file. **KHÔNG một dòng `Yêu cầu:` nào, KHÔNG một
oracle O-A…O-K nào, KHÔNG một Owner Decision D1–D3 nào bị sửa chữ.** Đây là
luồng ghi evidence bình thường, không phải nới lỏng gate.

`CHECK-PRA003-07` và `CHECK-PRA003-12` được giữ đúng `NOT_TESTED` tại
`a36f959` — implementer KHÔNG tự chấm hai check thuộc thẩm quyền khác.

## Xác Minh Độc Lập (Independent Verification)

### Oracle golden — recompute bằng SQL thô, không qua module triển khai

Nạp `tests/fixtures/golden/period_2026_01.xlsx` qua đường production
(`demo.run_demo` → `run_import_production`) → `history_writer.write_run_history`,
rồi recompute bằng SQL thô trên `order_line_current` + hai con trỏ hiện hành:

```
=== INDEPENDENT raw-SQL recomputation ===
 lines=351 orders=254 qty=407 sales=3562310000
 status: AUTO=2 PENDING=349  (total=351)
 AUTO lines with non-null kpi_profit = 2
 lines with accounting_profit NOT NULL = 2
=== GOLDEN expected JSON (oracle độc lập, sinh TRƯỚC PRA-003) ===
 orders=254 lines=351 qty=407 sales=3562310000
=== analytics_queries.period_totals (implementation) ===
  lines=351  orders=254  quantity=407  total_sales=3562310000
  kpi_profit=900000  kpi_lines=2  accounting_profit=1000000  accounting_lines=2
  auto_orders=1  review_orders=253
```

Ba nguồn KHỚP tới từng đơn vị. `auto_orders + review_orders = 1 + 253 = 254 =
orders`.

### Chứng minh CẤU TRÚC: không thể nhân bản cardinality

Đọc `tools/db/schema.py` (suy luận tĩnh, có dẫn nguồn):

- `order_line_current` PK = `(order_key, product_key, occurrence_index)` ⟹ mỗi
  khoá góp ĐÚNG MỘT dòng.
- `_joined()` nối sang `order_line_result_version.id` và
  `order_line_source_version.id` — CẢ HAI là `primary_key=True` ⟹ mỗi join là
  many-to-one nghiêm ngặt. **Không có đường nào nhân bản dòng.**
- `current_source_version_id` / `current_result_version_id` đều
  `nullable=False` ⟹ inner join KHÔNG âm thầm đánh rơi dòng nào.
- `CheckConstraint(status IN ('AUTO','PENDING'))` ở cấp DB ⟹ `status` là một
  PHÂN HOẠCH thật. Nhờ đó `auto = orders − review` và `kpi_lines = COUNT(AUTO)`
  đúng theo cấu trúc, không phụ thuộc quy ước đặt tên ở tầng exporter.
- Ba bảng mà truy vấn đọc đều mang `CheckConstraint(origin = 'PIPELINE_GENERATED')`
  ⟹ **một dòng legacy KHÔNG THỂ tồn tại trong đó về mặt vật lý.** Đây là bằng
  chứng tách nguồn mạnh hơn grep.
- Toàn bộ cột PII (`imei`, `note_raw`, `employee_raw`, `product_raw`) và
  `source_profit` nằm trên `order_line_source_version`; truy vấn chỉ lấy
  `quantity` từ bảng đó. Schema KHÔNG có cột `customer`/`phone`/`address` nào.

### Kiểm tra ngữ nghĩa do reviewer tự viết khẳng định

```
### CHECK-01  no-double-count / current-state
  PASS  A→B totals == B alone  (A=4L/4O sales=32000000, B=4L/4O)
  PASS  re-upload same book moves nothing
  PASS  SOURCE_CHANGED: only current version counted (sales=9000000, lines=1)
### CHECK-03  NULL != 0
  PASS  empty period → None (not Decimal 0) for all money
  PASS  lines present but no profit → None
  PASS  presentation: None→'—'  Decimal(0)→'0'
### CHECK-04  KPI profit only AUTO + both coverages
  PASS  PENDING line w/ kpi=5,000,000 EXCLUDED (kpi_profit=3000000)
  PASS  coverages differ in numerator, same denominator: kpi 1/2, acct 2/2
### CHECK-04b AUTO/Review BY ORDER (multi-line order)
  PASS  order w/ ANY pending line is Review (auto=1 review=1 orders=2)
  PASS  auto + review == total orders
### CHECK-05  employee additive reconciliation
  PASS  Σ employee[lines] == period_totals[lines]  (3 == 3)
  PASS  Σ employee[quantity] == period_totals[quantity]  (3 == 3)
  PASS  Σ employee[total_sales] == period_totals[total_sales]  (24000000 == 24000000)
  PASS  Σ employee[kpi_profit] == period_totals[kpi_profit]  (6000000 == 6000000)
  PASS  Σ employee[accounting_profit] == period_totals[accounting_profit]  (4000000 == 4000000)
  PASS  NULL employee kept as its own row (rows=3)
### CHECK-05b order column deliberately NOT additive
  PASS  multi-employee order: period orders=1 but Σemployee orders=2
  PASS  TOTAL row counts each order ONCE (=1)
### CHECK-09  missing sale_date
  PASS  undated line not in month period (lines=1)
  PASS  undated line not in 'Toàn bộ dữ liệu' either (lines=1)
  PASS  undated_lines() surfaces it = 1
### CHECK-08  period model / year boundary
  PASS  Jan → previous = (2025, 12) (Dec prev year)
  PASS  leap Feb 2024 → 29 days
  PASS  missing previous → '—'/'—' not 0%/-100%
  PASS  previous==0 → ratio '—' (no div-by-zero, no fake %)
  PASS  Jan 2026 vs absent Dec 2025 → blank comparison
  PASS  comparison label crosses year correctly = Tháng 12/2025
  PASS  'Toàn bộ dữ liệu' → no comparison at all
```

Biên đã dò thêm ngoài yêu cầu tối thiểu:

```
EDGE  Decimal(0) → '0' / missing=False   ·  None → '—' / missing=True   (phân biệt được)
EDGE  lợi nhuận âm → '-500.000' (đúng dấu)
EDGE  employee '' và NULL gộp thành ĐÚNG 1 dòng "Chưa xác định nhân viên"
EDGE  đơn trải hai tháng → 'Toàn bộ dữ liệu' vẫn đếm 1 đơn, auto+review==orders
```

### Kiểm tra tầng route (PII / tách nguồn / input lạ)

PII được dò bằng **giá trị THẬT đọc ngược từ DB**, không bằng từ khoá:

```
### PII universe actually persisted: imei=0 note_raw=1 employee_raw=1
                                    product_raw=226 source_profit=218
  PASS  no note_raw / employee_raw / product_raw value appears in any page
  PASS  no source_profit value rendered
  PASS  'snapshot_id' 'run_id' 'coverage_state' 'source_version'
        'result_version' 'reconciliation_flag' 'PIPELINE_GENERATED'
        'LEGACY_REFERENCE' 'SNAP-' đều VẮNG MẶT
  PASS  không đường dẫn tuyệt đối
### CHECK-06  legacy / pipeline separation
  PASS  /nhan-vien (không tham số) là trang legacy
  PASS  no <table> ever carries both LEGACY and SỐ MỚI labels
  PASS  nguon ∈ {cu, xyz, '', "moi'; DROP TABLE", MOI, Moi, ' moi'} → 200, về legacy
  PASS  nguon độc hại được escape, không phản chiếu thô (không XSS)
### D1/D2/D3
  PASS  nhãn 'Tổng số lượng'; 'Tổng số SP'/'Số lượng sản phẩm' vắng khỏi header
  PASS  không Target / So target / DS quy đổi
```

Ghi chú phương pháp: hai FAIL thô ban đầu của script reviewer đều là NHIỄU CỦA
CHÍNH PHÉP ĐO, đã truy tận nơi và loại: (a) "source_profit leak" là giá trị
`'0'` một ký tự khớp chuỗi con bên trong `value="2026-01"` của bộ chọn kỳ —
không một giá trị `source_profit` dài nào được render; (b) "legacy badge" vắng
vì harness của reviewer chỉ nạp dữ liệu pipeline, chưa nhập workbook legacy nào
— trang legacy đúng ra phải hiện "Chưa nhập bản báo cáo cũ nào".

### Test chạy lại độc lập

```
tests/test_analytics_queries.py + test_analytics_presentation.py
  + test_web_pipeline_analytics.py    : 67 passed in 9.23s
tests/test_golden_baseline.py         : 58 passed, 2 skipped in 8.32s   ← khớp O-K
tests/test_web_legacy_routes.py       : 34 passed in 3.37s              ← non-regression PRA-001
tests/test_pipeline_history_vertical.py: 12 passed in 33.64s            ← regression PRA-002
FULL SUITE                            : 1873 passed, 11 skipped in 97.61s (exit 0)
```

Validators:

```
validate_structure          : GOVERNANCE STRUCTURE: PASS (21 required paths)
validate_project_state      : PROJECT STATE: PASS
validate_evidence           : EVIDENCE VALIDATION: PASS (126 record)
validate_task_completion    : TASK COMPLETION: PASS (10 DONE task)
validate_reference_integrity: FAIL — ĐÚNG 3 issue đã biết của REM-T06, không phát sinh mới
```

### Ngân sách — đo lại độc lập (AST code-lines ∩ git-added-lines)

```
app/web/analytics_queries.py       117
app/web/analytics_presentation.py  105
app/web/server.py                   62
PYTHON PRODUCTION TOTAL            284   (mục tiêu 255 · cảnh báo mềm 320 · DỪNG CỨNG 400)
TEMPLATE TOTAL                     191   (trần 220)
CSS added                           16   (trần 25)
```

Reviewer tái lập ĐÚNG ba con số implementer báo cáo (284 / 191 / 16). Vượt mục
tiêu 255 là 29 dòng nhưng DƯỚI cảnh báo mềm ⟹ không kích hoạt BUDGET-AWARE PLAN,
không kích hoạt `STOP`.

Scope Lock: `git diff --name-only facf090..a36f959` đối chiếu với danh sách
FORBIDDEN ⟹ **0 vi phạm**. `tests/fixtures/golden/**` KHÔNG bị sửa — oracle
golden còn nguyên.

```
schema 0 · migration 0 · index 0 · dependency 0 (pyproject.toml không đổi)
config 0 · Tracking 0 · protected persistence core KHÔNG đổi
ALEMBIC_HEAD = 0002_snapshots (không đổi)
```

## Sai Lệch So Với Tuyên Bố Của Người Triển Khai (Mismatches With Implementer Claims)

| Tuyên bố S096 | Kết quả reviewer | Kết luận |
|---|---|---|
| Golden `58 passed, 2 skipped` | tái lập ĐÚNG | KHỚP |
| Full suite `1873 passed, 11 skipped` | tái lập ĐÚNG | KHỚP |
| Python 284 · template 191 · CSS 16 | tái lập ĐÚNG bằng phép đo riêng | KHỚP |
| 3 issue `reference_integrity` của REM-T06, không phát sinh mới | tái lập ĐÚNG | KHỚP |
| Coverage kỳ golden `2 / 351` | tái lập ĐÚNG (status AUTO=2, PENDING=349) | KHỚP |
| `git diff --check` **sạch** | **KHÔNG sạch trên dải commit** — 1 trailing whitespace | LỆCH → FIND-PRA003-02 |

## Findings

### FIND-PRA003-01 — phân loại: `CONTRACT_MISMATCH` · NON_BLOCKING

Reviewer điều tra ĐỘC LẬP, chạy CẢ HAI đường trên CÙNG fixture golden:

```
--- BARE run_import (đường mà build_expected.py dùng) ---
  price_source dist: {'Pending': 351}
  accounting_profit IS NULL: 351   eligible_kpi_profit IS NULL: 351
--- run_import_production (nạp registry canonical đã commit) ---
  price_source dist: {'OWNER_MANUAL_LEGACY_CONFIRMATION': 2, 'Pending': 349}
  accounting_profit IS NULL: 349   eligible_kpi_profit IS NULL: 349
```

Và trạng thái ĐÃ PERSIST (không chỉ `price_source`): `AUTO=2, PENDING=349`.

**A. Phân biệt có đúng sự thật không?** CÓ. `tests/fixtures/golden/build_expected.py:261`
gọi `run_import(fixture, CONFIG_DIR)` TRẦN — `identity_registry=None`. Trong khi
`app/composition.py:72` `run_import_production` nạp
`load_registry_from_jsonl(HISTORICAL_REGISTRY_PATH)` + confirmed adjustments +
eligible-cost authority + price composition.

**B. `2 / 351` có phải hành vi ĐÚNG của đường production không?** CÓ. Reviewer
truy nguyên chuỗi ingest thật: upload web → `run_owner_report`
(`app/owner_usability.py:170`) → `demo.run_demo` → `run_import_production`
(`app/demo.py:92`) → `history_writer.write_run_history`. **Mọi dòng từng được
persist đều đi qua đường production.** Đường `run_import()` trần KHÔNG BAO GIỜ
sinh ra dữ liệu mà PRA-003 đọc. Vậy `2 / 351` là coverage THẬT của hệ thống
đang chạy.

**C. O-C đòi literal `0/351` hay đòi tính chất an toàn?** Câu khẳng định quy
phạm của O-C là *"Lợi nhuận thiếu hiển thị `—`, KHÔNG hiển thị `0`"*, và cột
thẩm quyền của nó ghi *"oracle về TÍNH TRUNG THỰC"*. Cặp số `0/351` được O-C
dẫn xuất TƯỜNG MINH từ `pricing.price_source_distribution = {Pending: 351}` —
tức từ block `pricing` của file golden, vốn là bản ghi của đường TRẦN. **Tiền
đề đó không đúng cho đường đọc của PRA-003.** Tính chất an toàn thì vẫn phải
giữ, và nó ĐƯỢC giữ: reviewer đã tự dựng dữ liệu không dòng nào đủ điều kiện và
xác nhận cả hai ô render `—` với coverage `0 / N`.

**D. Implementation có test đường production, hay âm thầm làm yếu oracle?**
TEST ĐÚNG ĐƯỜNG PRODUCTION, và KHÔNG làm yếu oracle. Ba bằng chứng:
(1) `tests/fixtures/golden/**` KHÔNG bị sửa một byte nào (đã đối chiếu Scope
Lock); (2) test còn ASSERT NGƯỢC LẠI rằng file golden vẫn đọc ra
`{"Pending": 351}` — tức nó BẢO TỒN giá trị oracle gốc thay vì viết đè;
(3) tính chất O-C được chứng minh RIÊNG trên dữ liệu có kiểm soát. Việc lệch
được ghi rõ ràng trong docstring của test, không giấu.

**Kết luận:** đây là sai lệch giữa MINH HOẠ SỐ HỌC của frozen contract và thực
tế đường production, KHÔNG phải lỗi triển khai và KHÔNG phải lỗi test. Không có
con số quản lý nào sai. Khắc phục đúng là **sửa TÀI LIỆU O-C** trong một lượt
docs sau, không phải sửa mã. KHÔNG tiêu repair cycle.

### FIND-PRA003-02 — `EVIDENCE_DEFECT` · NON_BLOCKING

`CHECK-PRA003-11(d)` ghi `git diff --check : sạch (không output)`. Trên dải
commit thì KHÔNG sạch:

```
docs/sessions/S094-pra-003-vertical-slice-discovery.md:341: trailing whitespace.
```

ĐÚNG MỘT lần xuất hiện, trong file tài liệu phiên S094. **Không file
production/test/tool nào dính.** `git diff --check` KHÔNG tham số (dạng
working-tree) đúng là sạch — đó là lý do implementer báo sạch; hai dạng lệnh đo
hai thứ khác nhau. Không đe doạ điều nào trong 5 điều kiện mở repair cycle
(mục 14) ⟹ NON_BLOCKING. RE-TRIGGER: gộp vào lượt docs sửa O-C của FIND-01.

### FIND-PRA003-03 — `HARDENING` · NON_BLOCKING

`employee_totals()` `GROUP BY (employee, employee_group)`. Nếu MỘT
`employee_normalized` mang HAI `employee_group` khác nhau trong cùng kỳ, nhân
viên đó hiện thành HAI dòng cùng tên:

```
rows = [('A','NOI_THANH',8000000), ('A','STANDARD_SALES',8000000)]
bất biến cộng được VẪN ĐÚNG (Σlines = 2 = total)
```

Không sinh con số sai, không double-count, mỗi dòng vẫn được gắn nhãn nhóm
trung thực, và dòng TỔNG vẫn đếm mỗi đơn một lần. Khả năng xảy ra thấp:
`group` là thuộc tính của bản ghi nhân viên trong `EmployeeMaster` (một nhóm
cho một nhân viên), nên chỉ chạm tới khi master ĐỔI nhóm giữa kỳ.
RE-TRIGGER CONDITION: khi dữ liệu thật lần đầu xuất hiện một
`employee_normalized` mang hai `employee_group` trong cùng một kỳ.

### Quan sát không phải finding

`<title>` của `/nhan-vien` đổi từ `Reports — Nhân viên (số cũ)` thành
`Reports — Nhân viên`. Cần thiết vì route nay phục vụ CẢ HAI nhánh; `h1` vẫn là
`NHÂN VIÊN — SỐ CŨ THEO THÁNG`, badge `LEGACY` giữ nguyên chuỗi, và 34 test
legacy PASS không sửa dòng nào. Nhãn hiển thị vẫn trung thực.

### BLOCKING findings

**KHÔNG CÓ.** Reviewer không tìm được đường nào dẫn tới: con số quản lý sai ·
double-count âm thầm · `NULL` hiện thành `0` · sai thẩm quyền lợi nhuận · trộn
nguồn · lộ PII · vi phạm frozen contract · hỏng vertical production.

## Kết Luận (Conclusion)

```
FINAL_DECISION       = ACCEPT_WITH_NON_BLOCKING_FINDINGS
CHECK-PRA003-12      = PASS
TASK-PRA-003         = IN_PROGRESS  (KHÔNG phải DONE — CHECK-07 còn NOT_TESTED)
repair_cycles_used   = 0   (review không tiêu cycle; không finding nào mở cycle)
repair_cycles_remaining = 1
NEXT_VERTICAL_ACTION = Controlled Integration
```

## Việc Cần Theo Dõi Tiếp (Required Follow-up)

1. `CHECK-PRA003-07` — Owner nghiệm thu real vertical Tháng 09/2026 trên
   production sau deploy. Ngoài thẩm quyền reviewer; giữ `NOT_TESTED`.
2. Một lượt DOCS (không phải repair) gộp FIND-PRA003-01 + FIND-PRA003-02: sửa
   minh hoạ số học của O-C cho khớp đường production, và dọn 1 trailing
   whitespace ở `S094`.
3. FIND-PRA003-03 giữ ở trạng thái HARDENING với RE-TRIGGER CONDITION đã ghi.
