# S052 — GOLDEN ORDER #1 (BH62063) HISTORICAL CONFIRMED IDENTITY DATA

DATA / PERSISTENCE SESSION trên vertical critical path của `BH62063`. Mục
tiêu duy nhất: thiết lập một `HistoricalConfirmedRegistry` entry `CONFIRMED`
cho `BH62063` theo đúng data contract `TASK-105D` §9 — **nhưng chỉ nếu** có
`source_report_ref` đáp ứng `INV-51` (bằng chứng có thể mở lại được, không
phải "chủ dự án đã xác nhận" dưới dạng văn xuôi). Kế tiếp `S051` (wiring
session, `FIRST_FAILING_BOUNDARY = B2`, `DATA_MISSING`).

## 1. Git target

```text
Branch (expected/thực tế) : data/golden-bh62063-historical-identity
Base SHA (expected)       : c6564682ae22da22d78f7f85abdbabda33d2e4dd
HEAD trước phiên          : c6564682ae22da22d78f7f85abdbabda33d2e4dd (khớp,
                             = HEAD cuối của S051)
Upstream                  : origin/data/golden-bh62063-historical-identity
                             (0 ahead / 0 behind trước phiên)
Working tree trước phiên  : clean
```

`bash scripts/branch_authority_check.sh` trước thay đổi:

```text
DEFAULT_BRANCH  : claude/extract-upload-repo-gq2ws4
DEFAULT_TIP     : 7464ccaa784f13d887b2d5441d86136ff7d9a61d
HEAD_SHA        : c6564682ae22da22d78f7f85abdbabda33d2e4dd
WORKTREE        : CLEAN
CURRENT_BRANCH  : data/golden-bh62063-historical-identity
UPSTREAM        : origin/data/golden-bh62063-historical-identity
ahead default   : 8 commit    behind default : 0 commit
cumulative LOC  : 5550
DIVERGENCE      : INTEGRATION_DECISION_REQUIRED [loc>5000]
AUTHORITY       : BRANCH_WITH_UPSTREAM
RESULT          : AUTHORITY_OK
```

`git remote show origin` xác nhận nhánh mặc định thật là
`claude/extract-upload-repo-gq2ws4`. Đọc `PROJECT/PROJECT_PROGRESS.md` trên
`origin/claude/extract-upload-repo-gq2ws4` (0 commit behind so với local
tracking của nhánh đó) trước khi mở phiên: track hiện tại trên default là
`TASK-107`/`TASK-108`/governance `REM-T06` — không liên quan `BH62063`/
`TASK-105D`/`S049`–`S051`. Không có công việc trùng lặp kiểu `DEC-118`.

`DIVERGENCE = INTEGRATION_DECISION_REQUIRED [loc>5000]` là cảnh báo tích luỹ
đã có từ `S051`, không đổi bởi phiên này (S052 không merge default, không tự
tạo integration branch, không reset divergence, không squash/rebase).

## 2. INV-51 — hard evidence gate (§6 của brief)

Đọc `docs/spec/TASK-105D-DATA-CONTRACT.md` §9.3 và
`app/modules/product/identity/registry.py`:

```text
INV-51  source_report_ref IMMUTABLE và phải trỏ tới một bằng chứng có thể
        mở lại được. Không chấp nhận "chủ dự án đã xác nhận" dưới dạng
        prose không có artifact (EVIDENCE_STANDARD — cấm bịa evidence).
INV-54  Registry KHÔNG BAO GIỜ được bootstrap bằng cách suy ra từ catalog
        hay giá hiện tại. Nhập từ báo cáo Owner-confirmed thật, hoặc để
        trống.
```

`SourceReportRef` (dataclass, `registry.py`) đã thi hành `INV-51` bằng code,
không chỉ bằng văn bản: `__post_init__` raise `InvalidSourceReportRefError`
nếu `report_id`/`file_name`/`content_hash` rỗng. Docstring của lỗi này nói
thẳng: *"một xác nhận không mở lại được thì không phải bằng chứng"* — đúng
câu hỏi mà `S052` phải trả lời trước khi gọi constructor này với dữ liệu
thật.

Trả lời 6 câu hỏi bắt buộc của brief §6:

```text
1. Source nào chứng minh raw sales product "Máy giặt LG 10kg FV1410S4W1"?
   → tests/fixtures/golden/period_2026_01.xlsx, sheet "SỔ CHI TIẾT BÁN
     HÀNG", dòng 6 (1-based, kể cả 3 dòng header): Ngày=2026-01-02,
     Số BH=BH62063, Tên hàng="Máy giặt LG 10kg FV1410S4W1", SL=1,
     Đơn giá=7.500.000, Doanh số bán=7.500.000, Chiết khấu=0. File này
     REOPENABLE (có trong repo, hash được).

2. Source nào chứng minh canonical identity TRACKING:FV1410S4W1?
   → KHÔNG CÓ. Không xuất hiện ở bất kỳ đâu ngoài prose trong
     `PROJECT/PROJECT_DECISIONS.md` (DEC-163) và
     `PROJECT/PROJECT_PROGRESS.md` (END_TO_END_ACCEPTANCE). Đây chính là
     "chủ dự án đã xác nhận" dạng văn xuôi mà INV-51 nêu tên và cấm dùng
     làm production provenance.

3. Source có reopenable identifier/reference không? → Đối với identity/giá:
   KHÔNG. Chỉ có coordinate trong file `.md` governance — không phải một
   "báo cáo lịch sử đã duyệt" (report_id + content_hash trỏ tới một file
   bằng chứng độc lập, §9.3).

4. Audit/replay được mà không dựa vào memory/session prompt? → KHÔNG, với
   phần identity/giá — nguồn duy nhất hiện có là bản ghi quyết định
   (DEC-163), tức đúng là "session prompt đã được ghi lại", không phải một
   artifact độc lập với việc Owner phát biểu nó.

5. Required provenance fields (§9.3): `report_id`, `file_name`,
   `content_hash` (REQUIRED), `sheet_name`/`source_row` (OPTIONAL) — trỏ
   tới MỘT BÁO CÁO LỊCH SỬ đã xác nhận identity/giá, không phải tới chính
   bản ghi quyết định dùng để tường thuật lại lời Owner.

6. Evidence hiện có nằm ở đâu? → Đã qua toàn bộ danh sách repo/fixture/
   source export/accounting file/report artifact/external canonical
   reference (§7 dưới đây). Chỉ có (1) sales ledger fixture (xác nhận GIAO
   DỊCH, không xác nhận IDENTITY/GIÁ) và (2) prose quyết định dự án (bị
   INV-51 cấm minh thị).
```

## 3. Source search (§7 của brief, theo đúng thứ tự ưu tiên)

```text
1. canonical source data/fixture thuộc production/test data contract
   → tests/fixtures/golden/{period_2026_01.xlsx, period_2026_06.xlsx,
     expected/*.json} — không chứa bất kỳ trường "purchase price"/giá vốn
     nào cho BH62063; không chứa canonical identity mapping. Xác nhận bằng
     đọc trực tiếp workbook (§2.1) và grep "FV1410S4W1" trên
     tests/fixtures/**/* → 0 match.

2. imported historical sales/report source có stable record identifier
   → không có file nào khác trong repo đóng vai trò "báo cáo lịch sử đã
     xác nhận giá vốn" (không có thư mục kiểu data/historical_reports/,
     không có export kế toán, không có "Tồn"/"phist"/"inv.cong" file nào
     — khớp §14/§16 của brief: các nguồn này vẫn UNRESOLVED, không được
     xâm phạm trong S052).

3. canonical persisted mapping/evidence artifact hiện có
   → `HistoricalConfirmedRegistry` production: rỗng (in-memory, không
     loader) — không có entry nào từ trước để tham chiếu lại.

4. existing project evidence explicitly accepted by Owner/governance
   → CHỈ CÓ: `DEC-163` (`PROJECT/PROJECT_DECISIONS.md`) +
     `END_TO_END_ACCEPTANCE` (`PROJECT/PROJECT_PROGRESS.md`, từ `S049`). Cả hai là
     prose quyết định dự án — đúng loại bằng chứng `INV-51` gọi tên và từ
     chối minh thị, dù chúng có "file_name" kỹ thuật (chính file .md đó)
     và có thể hash được: hash một file ghi lại lời Owner tường thuật lại
     KHÔNG biến lời tường thuật đó thành "một báo cáo lịch sử độc lập".
     `docs/spec/TASK-105D-DATA-CONTRACT.md` §9.3 và code
     (`InvalidSourceReportRefError`) đòi một BÁO CÁO — không phải một BẢN
     GHI QUYẾT ĐỊNH viết lại lời Owner.

5. other reopenable source accepted by existing contract
   → không tìm thấy nguồn nào khác trong repo.
```

`grep -rln "FV1410S4W1"` toàn repo (loại `.git/`) chỉ trả về 8 file `.md`:
`PROJECT/PROJECT_DECISIONS.md`, `PROJECT/PROJECT_PROGRESS.md`,
`docs/tasks/TASK-108B-eligible-costs-owner-definition.md`,
`docs/reviews/GOLDEN-BH62063-AS-IS-TRACE.md`, và các bàn giao session
`S045`/`S047`/`S049`/`S051` — toàn bộ là văn xuôi lịch sử/governance, không
có file dữ liệu/report artifact nào.

## 4. Kết luận — SOURCE_EVIDENCE_MISSING

Không tồn tại `source_report_ref` đáp ứng `INV-51` cho cặp
`(confirmed_identity=TRACKING:FV1410S4W1, confirmed_purchase_price=
7.000.000 VND)` của `BH62063`. Theo brief §20:

```text
KHÔNG persist mapping.
B2 = DATA_MISSING
SUBTYPE = SOURCE_EVIDENCE_MISSING
```

Không gọi `HistoricalConfirmedRegistry.append(ConfirmHistoricalEntry(...))`
với dữ liệu thật. Không viết `SourceReportRef` giả với `content_hash` bịa
(kiểu `"0"*64` mà `tests/support/identity_fixtures.py` dùng cho test) vào
đường production — làm vậy là chính xác hành vi `EVIDENCE_STANDARD` cấm.

**Owner business truth vs production evidence (brief §5) được tôn trọng
đúng như phân biệt yêu cầu:**

```text
BUSINESS_ORACLE           = DEFINED   (S049, DEC-163 — không đổi bởi S052)
PRODUCTION_IDENTITY_EVIDENCE = MISSING (S052, mới xác nhận)
```

Hai trạng thái này không mâu thuẫn nhau: acceptance nghiệp vụ đã chốt "kết
quả mong đợi là gì", nhưng production provenance để TỰ ĐỘNG SUY RA kết quả
đó từ dữ liệu lịch sử độc lập với lời Owner thì chưa tồn tại. Đây đúng là
lý do `TASK-105D` thiết kế `INV-51`: để một Golden acceptance không thể tự
mình trở thành "bằng chứng" cho chính nó.

## 5. Persistence mechanism (brief §9) — không cần dùng, nhưng đã xác định

`app/modules/product/identity/store.py` có `JsonlProductIdentityStore`
(Phase 1, append-only + index) triển khai `ProductIdentityStore` — nhưng đó
là store cho `E-F` (mapping post-cutover), KHÔNG phải cho
`HistoricalConfirmedRegistry` (`E-J`). `registry.py` (E-J) không có bất kỳ
biến thể JSONL/file-backed, loader, hay bootstrap nào — xác nhận lại đúng
quan sát của `S051` §9 (in-memory-only). Vì không có evidence hợp lệ để
persist (§4), câu hỏi "persistence mechanism nào cho E-J" là moot cho phiên
này — không cần trả lời để đóng S052, và S052 KHÔNG implement một seam mới
cho nó (đó sẽ là scope creep ngoài §10/§23 của brief khi không có dữ liệu
để load). Ghi nhận cho phiên kế tiếp nếu/khi evidence xuất hiện.

## 6. Post-change vertical trace (BH62063, AS-IS) — không đổi so với S051

Không có production/config/data nào bị sửa trong S052 (0 byte đổi ngoài
file bàn giao này) nên chạy lại xác nhận trace hệt S051:

```text
$ python3 -c "
from pathlib import Path
from app.pipeline import run_import
result = run_import(Path('tests/fixtures/golden/period_2026_01.xlsx'), config_dir=Path('config'))
order = next(o for o in result.orders if o.order_id == 'BH62063')
line = order.lines[0]
print(line.accounting_purchase_price, line.price_source, line.accounting_profit)
"
None Pending None
```

| Boundary | Status | Ghi chú |
|---|---|---|
| B0 Sales Input | PASS | Không đổi |
| B1 Identity Input | PASS | Không đổi |
| B2 Product Identity Resolution | **DATA_MISSING** (subtype `SOURCE_EVIDENCE_MISSING`) | `resolve_batch()` qua registry rỗng thật → `PendingProduct(PENDING_HISTORICAL_CONFIRMATION)`. Không đổi giá trị so với S051 — S052 xác nhận rằng KHÔNG persist là hành động đúng, không phải một cơ hội bị bỏ lỡ. |
| B3–B9 | NOT_REACHED | Không đổi |

```text
NEW_FIRST_FAILING_BOUNDARY : B2 (không đổi so với S051)
NEW_FAILURE_TYPE            : DATA_MISSING / SOURCE_EVIDENCE_MISSING
ROOT_CAUSE                  : Không có báo cáo lịch sử độc lập, reopenable,
                              nào trong repo xác nhận
                              (identity=TRACKING:FV1410S4W1,
                              price=7.000.000 VND) cho BH62063 — nguồn duy
                              nhất là lời Owner đã ghi lại dưới dạng quyết
                              định dự án (DEC-163), điều mà INV-51 minh thị
                              không chấp nhận làm production provenance.
```

## 7. Validation

```text
$ bash scripts/branch_authority_check.sh
  → AUTHORITY_OK, DIVERGENCE = INTEGRATION_DECISION_REQUIRED [loc>5000]
    (không đổi so với trước phiên — không merge/rebase/squash)

$ python3 governance/scripts/governance/validate_structure.py
GOVERNANCE STRUCTURE: PASS — 21 required paths

$ python3 governance/scripts/governance/validate_project_state.py
PROJECT STATE: PASS

$ python3 governance/scripts/governance/validate_evidence.py
EVIDENCE VALIDATION: PASS — 88 REQUIRED PASS evidence record(s)

$ python3 governance/scripts/governance/validate_task_completion.py
TASK COMPLETION: PASS — 7 DONE task(s)

$ python3 governance/scripts/governance/validate_reference_integrity.py
REFERENCE INTEGRITY: FAIL — 3 reference (TASK-REM-T06, PRE-EXISTING
  baseline, không đổi bởi S052)

$ python3 -m pytest tests/ -k "105d" -q
199 passed  (khớp reference S051)

$ python3 -m pytest tests/test_golden_baseline.py -q
58 passed, 2 skipped  (khớp reference)

$ python3 -m pytest -q
965 passed, 11 skipped  (khớp reference tuyệt đối — 0 regression, vì S052
  không sửa app/, config/, hay bất kỳ file test nào)
```

Delta vs reference trước S052 (199/58+2/965+11/0 failed): **0 thay đổi** ở
mọi con số test/validator — đúng như kỳ vọng cho một DATA SESSION kết luận
`SOURCE_EVIDENCE_MISSING` (không production/test/fixture change nào được
authorize khi evidence không đủ).

## 8. Task Registry — bằng chứng BEFORE/AFTER

```text
SET A (REGISTERED_TASK_SET, PROJECT_PROGRESS.md) BEFORE = 13   AFTER = 13
SET B (TASK_SPEC_SET, docs/tasks/*.md)            BEFORE = 22   AFTER = 22
new_registered_task_ids = 0
```

Không tạo task mới, không mở lại `TASK-105D`, không mở `RC-2`, không adopt
`V4.2`, không sửa `PROJECT/PROJECT_PROGRESS.md` hay
`PROJECT/PROJECT_DECISIONS.md` (đúng
pattern `S050`/`S051` — session hẹp, chỉ ghi bàn giao dưới `docs/sessions/`).

## 9. Kết luận S052

```text
S052 FINAL STATE : PASS
  - INV-51 evidence gate đã được kiểm tra bằng inspect thật (không đoán),
    trả lời đầy đủ 6 câu hỏi §6 của brief
  - Kết luận: reopenable source evidence KHÔNG đủ cho identity+price của
    BH62063 → KHÔNG persist mapping (đúng §20, không fabricate)
  - Post-change vertical trace xác nhận B2 = DATA_MISSING không đổi (đúng
    dự đoán — hành động đúng là KHÔNG đổi state khi thiếu evidence)
  - Không production/test/fixture/task-registry nào bị sửa; toàn bộ
    validator + test suite khớp reference tuyệt đối, 0 regression
  - Divergence branch authority không đổi, không merge/rebase/squash

MINIMUM_NEXT_CHANGE (không thực hiện trong S052):
  Không phải một code change. Cần OWNER DATA: một báo cáo lịch sử độc lập,
  reopenable (ví dụ một export kế toán/"Tồn"/phist NCC có trước ngày hôm
  nay, có thể hash), tự nó xác nhận (a) canonical identity
  TRACKING:FV1410S4W1 cho raw product "Máy giặt LG 10kg FV1410S4W1", và/hoặc
  (b) giá vốn 7.000.000 VND cho giao dịch BH62063 (2026-01-02) — độc lập với
  chính lời Owner đã ghi trong DEC-163. Khi báo cáo đó tồn tại trong repo
  (dưới dạng file thật, không phải văn xuôi quyết định), một DATA SESSION
  kế tiếp có thể persist entry CONFIRMED bằng đúng API
  `HistoricalConfirmedRegistry.append(ConfirmHistoricalEntry(...))` đã có
  sẵn, và (nếu cần) một thin loader/bootstrap seam cho registry (hiện chưa
  tồn tại, §5) — vẫn nằm trong phạm vi "DATA/PERSISTENCE SESSION", không
  phải subsystem redesign.

NEXT_SESSION_CLASSIFICATION : OWNER DATA REQUIRED
  (cần chủ dự án cung cấp MỘT ARTIFACT lịch sử reopenable — không phải một
  câu xác nhận thêm bằng lời — cho identity và/hoặc giá vốn của BH62063;
  "Tồn" technical source mapping vẫn UNRESOLVED, không đổi bởi S052)
```

### Explicit answers

```text
Reopenable source evidence found?           NO
BH62063 persisted as CONFIRMED?             NO
B2 PASS?                                    NO (DATA_MISSING /
                                             SOURCE_EVIDENCE_MISSING)
BH62063 end-to-end PASS?                    NO
Golden expectation used as sole production
  authority?                                NO
Production identity algorithm changed?      NO
Golden-specific production logic added?     NO
"Tồn" mapping invented?                     NO
New task registered?                        NO
V4.2 started?                               NO
TASK-105D reopened?                         NO
RC-2 opened?                                NO
Pricing changed?                            NO
Merge performed?                            NO
```
