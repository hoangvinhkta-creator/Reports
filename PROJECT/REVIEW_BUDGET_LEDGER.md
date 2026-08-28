# REVIEW BUDGET LEDGER

Machine Control #2 của Governance V4.1 (`TASK-V4-ADOPTION`, §18).

Ledger này là bản ghi tường minh, đọc được bằng máy lẫn con người, về ngân
sách repair-cycle của từng root task lineage theo bảng đã freeze ở
`governance/core/RULE_PRECEDENCE.md` §... *(bảng ngân sách nằm trong chính
Owner Decision của V4.1 — xem `PROJECT/PROJECT_DECISIONS.md` DEC-140
và các mục liên quan)*. Không phải nơi diễn giải lại luật; chỉ ghi trạng
thái.

## Bảng ngân sách đã freeze (V4.1)

```
LOW              = 1 blocking repair cycle
MEDIUM           = 1 blocking repair cycle
HIGH / CRITICAL  = 2 blocking repair cycles
```

Không tồn tại `HIGH = 3`. Owner được phép đặt budget thấp hơn bảng này cho
một root task cụ thể. Vượt budget → `OWNER_EXTENSION REQUIRED`.

Ngân sách gắn với **ROOT TASK LINEAGE**. Sub-unit (ví dụ R1-A2, R1-B, R2…)
không có ngân sách riêng, không reset ngân sách, và không được tạo lineage
mới chỉ để reset ngân sách.

---

## Root Task: TASK-V4-ADOPTION

```
root_task: TASK-V4-ADOPTION
effective_risk: MEDIUM
repair_cycles_allowed: 1
repair_cycles_used: 0
repair_cycles_remaining: 1
```

Production code changes: FORBIDDEN (theo phạm vi V4.1-0).

Nếu adoption không hoàn thành sau 1 blocking repair cycle: DESCOPE →
MINIMAL V4.1 OVERLAY (không tạo V4.1-R1, V4.1-R1A, V4.1-Repair-2, hay bất kỳ
decomposition nào nhằm reset budget).

cycles:
- id: (chưa mở — adoption hoàn thành trong 0 repair cycle tính đến thời
  điểm ghi ledger này)
  base_sha: N/A
  head_sha: N/A

---

## Root Task: TASK-110

Đây là **transition ledger có chủ ý** cho một root task lineage đã tồn tại
từ trước V4.1, được V4.1 tiếp nhận nguyên trạng — không được cấp lại ngân
sách, không được đưa giá trị `repair_cycles_remaining` về khác 0 chỉ vì V4.1
mới có hiệu lực.

```
root_task: TASK-110
effective_risk: HIGH
repair_cycles_allowed: 2
repair_cycles_used: EXHAUSTED_PRE_V4.1
repair_cycles_remaining: 0

historical_evidence:
    independent_reviews: ">=8"
    repairs: ">=3"

authorized_actions:
    - FINAL_REVIEW_ONLY
    - ACCEPT_AS_IS
    - DESCOPE
    - OWNER_EXTENSION
```

**TASK-110 BUDGET = EXHAUSTED.** Đây là trạng thái chuyển tiếp có chủ ý, ghi
tại thời điểm V4.1 adoption (2026-08-27), không phải placeholder chờ điền
sau.

### Sub-unit lineage — không có ngân sách riêng

R1-A2, R1-A3, R1-A4, R1-B … R1-E, R2 … R8 — nếu thuộc `TASK-110` thì đều
thuộc cùng lineage `TASK-110`. Vì `TASK-110.repair_cycles_remaining = 0`,
**không unit nào trong nhóm này được tự mở**. Mỗi unit muốn tiếp tục phải
có một `OWNER_EXTENSION` riêng, kèm:

- production path cụ thể;
- kịch bản nghiệp vụ sai cụ thể nếu không xử lý;
- phạm vi được phép;
- budget được Owner cấp.

Không có Owner Extension tương ứng → `STOP`.

### Cycle accounting lịch sử (tham chiếu, không phải ngân sách còn lại)

Cumulative repair diff của TASK-110 được ghi trong các session log dưới
`docs/sessions/S015` … `S023` và trong `PROJECT/PROJECT_DECISIONS.md`
(DEC-128 … DEC-139). Kể từ integration `V4.1-1` (2026-08-27) toàn bộ lịch sử
này đã nằm trên nhánh mặc định — không còn phân tán trên các nhánh review
riêng. Ledger này không sao chép lại toàn bộ lịch sử đó — chỉ xác nhận điểm
chốt: ngân sách repair-cycle của lineage `TASK-110` đã cạn TRƯỚC khi V4.1 có
hiệu lực.

cycles:
- id: PRE_V4.1_HISTORICAL
  base_sha: (xem lịch sử session TASK-110 — ngoài phạm vi ghi lại tại đây)
  head_sha: (xem lịch sử session TASK-110 — ngoài phạm vi ghi lại tại đây)
  note: >
    Lịch sử đầy đủ (>=8 Independent Review, >=3 repair) nằm trong
    docs/sessions/ và PROJECT/PROJECT_DECISIONS.md trên các nhánh review
    TASK-110 đang hoạt động. Ledger V4.1 chỉ ghi nhận điểm chốt ngân sách,
    không viết lại lịch sử.

### Merge gate liên quan

**ĐÃ CÓ QUYẾT ĐỊNH — `DEC-141` (2026-08-27, V4.1-1).** Owner chọn option (B)
của §9: `CHECK-110-16` đổi Gate Class thành `POST_MERGE_PRODUCTION_ACCEPTANCE`.

```
CHECK-110-16
Priority   : REQUIRED                            (không đổi)
Status     : BLOCKED                             (không đổi)
Gate Class : POST_MERGE_PRODUCTION_ACCEPTANCE    (đổi từ pre-merge gate)
```

Chỉ Gate Class đổi. Vẫn thiếu production workbook thật để đối chiếu. Không
được giả lập PASS hay bypass. **Merge KHÔNG đồng nghĩa `TASK-110 DONE`** —
`TASK-110` chỉ chuyển `DONE` khi check này thực sự `PASS` trên dữ liệu
production thật. Xem `governance/core/TASK_COMPLETION_GATE_STANDARD.md`,
`DEC-141` và `docs/tasks/TASK-110-validation-review-queue.md`.

Đồng hồ 30 ngày của §9 vì vậy **đã dừng** cho gate này: quyết định Owner đã
được đưa ra ở ngày thứ 4 (phát sinh 2026-08-23 → quyết định 2026-08-27).

### Branch divergence đã biết

**ĐÃ ĐÓNG — `DEC-141` §4 (2026-08-27, V4.1-1).** Owner chọn option (A) của
§8: integrate/merge sớm.

Divergence đo được ngay trước integration, so với nhánh mặc định
`claude/extract-upload-repo-gq2ws4` @ `c7a1b24`:

| Nhánh | ahead | thời gian | LOC | vượt ngưỡng |
|---|---:|---|---:|---|
| `claude/r1-a1-contract-freeze-9lkh3h` | 24 | 4 ngày | 40.523 | cả ba |
| `claude/r1-canonical-object-safety-fon9lb` | 18 | 1 ngày | 37.509 | 2/3 |
| `claude/zealous-bardeen-s8iu2h` | 13 | 0 ngày | 31.126 | 2/3 |
| `claude/task-110-gate-readiness-7ui4si` | 6 | 0 ngày | 7.509 | 1/3 |
| `claude/governance-v4-1-freeze-36oexq` | 1 | 0 ngày | 722 | không |

Ba nhánh review phụ được chứng minh là **ancestor** của nhánh authoritative
`claude/r1-a1-contract-freeze-9lkh3h` (`git rev-list --count <A1>..<phụ>` = 0
cho cả ba) ⇒ 0 commit unique bị bỏ lại khi hợp nhất.

**KNOWN PRE-V4.1 DIVERGENCE = CLOSED tại V4.1-1.** Không grandfather thành
permanent exception.

---

## Root Task: TASK-GOLDEN-BASELINE-001

Lineage **mới**, độc lập với `TASK-110`. Ngân sách `EXHAUSTED_PRE_V4.1` của
`TASK-110` **không** áp vào đây, và task này **không** mở `R1-A2` → `R8`.

```
root_task: TASK-GOLDEN-BASELINE-001
effective_risk: HIGH
repair_cycles_allowed: 2
repair_cycles_used: 1
repair_cycles_remaining: 1
```

`HIGH` không đến từ độ khó của việc code — task chỉ thêm test và fixture. Nó
đến từ **Blast Radius theo failure path** (`governance/core/V4_1_POLICY_FREEZE.md` §4):

- **BR-1** — rò rỉ PII vào git history là **bất khả nghịch** (DEC-108 →
  "Can Revisit After: Không bao giờ"); không gate nào chặn sau khi push.
- **BR-2** — expected output sinh từ code hiện tại; nếu code hiện tại đã sai ở
  một path thì Golden đóng băng cái sai đó thành "chuẩn", và mọi lần sửa đúng
  sau này sẽ đỏ rồi bị "sửa" bằng cách sinh lại expected output.

BR-2 được giảm nhẹ — không loại bỏ — bằng GB-1: mọi aggregate mức kỳ phải
khớp evidence đã commit **trước** khi có code này
(`docs/analysis/_evidence/evidence.json` sinh tại TASK-002; CHECK-101-08 đóng
2026-08-23), cộng dòng "Tổng cộng" do chính ERP ghi trong workbook nguồn.

### Scope Lock

```
app/**                : FORBIDDEN — không sửa production code
config/**             : FORBIDDEN
docs/tasks/TASK-110*  : FORBIDDEN
governance/**         : FORBIDDEN
tests/fixtures/baseline/**, tests/test_task110_non_regression.py : FORBIDDEN
```

### Trạng thái

```
REPAIR CYCLE #1           = COMPLETE
INDEPENDENT REVIEW #2     = PASS — ELIGIBLE_FOR_FREEZE
    reviewed_sha           : 85210691702550d83c0fd42fe816be8ca9dde889
    blocking                : 0
    record                  : docs/reviews/TASK-GOLDEN-BASELINE-001-INDEPENDENT-REVIEW-2.md
GB-IR-01                   = CLOSED_BY_REPAIR, INDEPENDENTLY_VERIFIED
FROZEN = YES (DEC-142, 2026-08-27) · MERGED = YES (default SHA
f332a4cb4410b3ca9c71d659d36a3e8f26aa1fa5) · DONE = YES (GB-12 exit criteria
đủ, 2026-08-27)
```

Sub-unit `GB-1` … `GB-12`, và bất kỳ `GB-IR-xx` nào thuộc cùng lineage này,
**không** có ngân sách riêng và không reset ngân sách.

cycles:
- id: cycle-1
  base_sha: 4bccf469274dc9ffb32f333e6db475055ddda794
  head_sha: 54a575dde15f2650a27e270ae9a13543bd80e3ca
  opened_by: Independent Review trên 4bccf469… — verdict FAIL, đúng 1 BLOCKING
    finding (GB-IR-01)
  finding: >
    `test_golden_expected_output_is_regenerable_byte_identical` so byte-thô
    TOÀN BỘ file expected JSON, gồm cả `_environment.python`/`pyyaml`/
    `openpyxl` — ba trường advisory. Chạy trên Python 3.12.3 + PyYAML 6.0.3
    (khác môi trường sinh fixture: 3.11.15 + 6.0.1) làm test đỏ dù business
    payload giống hệt. False regression signal, tái hiện được:
    `python3.12 -m pytest tests/test_golden_baseline.py -q` trên `4bccf46`
    -> `50 passed, 2 failed, 2 skipped`.
  fix: >
    Thêm `_strict_bytes()` tái dùng `_comparable()` đã có sẵn; test
    byte-identical giờ so phần STRICT BUSINESS CONTRACT, loại đúng ba trường
    advisory. Không đổi `gb.write()`, không đổi
    `tests/fixtures/golden/expected/*.json`, không đổi fixture `.xlsx`.
    Business payload trước/sau IDENTICAL (hai file expected không hề bị
    chạm — `git diff --stat` rỗng trên `tests/fixtures/golden/expected/` và
    `tests/fixtures/golden/*.xlsx`).
  verification: >
    Suite chạy PASS trên cả Python 3.11.15 (venv sẵn có) và Python 3.12.3
    (venv riêng) sau repair: `58 passed, 2 skipped` cả hai. Full
    `pytest -q`: `697 passed, 11 skipped` (trước `691 passed, 11 skipped`,
    baseline `716ae2e1…` = `639 passed, 9 skipped`) — 0 regression. `app/` và
    `config/` diff = 0. `validate_reference_integrity` vẫn đúng 3 lỗi tiền
    tồn của `TASK-REM-T06`, không có lỗi thứ 4.
  scope: chỉ `tests/test_golden_baseline.py` + entry ledger này. Không sửa
    `app/**`, `config/**`, TASK-110, R1-A1, governance V4.1 core, HB-GB-01…06.

review_events:
- id: independent-review-2
  reviewed_sha: 85210691702550d83c0fd42fe816be8ca9dde889
  verdict: PASS — ELIGIBLE_FOR_FREEZE
  blocking: 0
  gb_ir_01: CLOSED_BY_REPAIR, INDEPENDENTLY_VERIFIED
  consumes_repair_cycle: false
  record: docs/reviews/TASK-GOLDEN-BASELINE-001-INDEPENDENT-REVIEW-2.md
  note: >
    Review chạy ngoài canonical repo; verdict do Owner cung cấp và được ghi
    lại nguyên trạng trong phiên "INDEPENDENT REVIEW #2 — VERDICT RECORDING
    ONLY" (2026-08-27). Không phải một repair cycle mới — remaining vẫn 1,
    unused.

---

## Root Task: TASK-108B

Lineage **mới**, độc lập với `TASK-110` (`EXHAUSTED_PRE_V4.1`) và với
`TASK-GOLDEN-BASELINE-001`. Mở tại `DEC-143` / `OD-108B-01` (2026-08-27).

```
root_task: TASK-108B
effective_risk: HIGH
repair_cycles_allowed: 2
repair_cycles_used: 0
repair_cycles_remaining: 2
```

`HIGH` **không** đến từ độ khó của việc code (số học đơn giản, module nhỏ). Nó
đến từ **Blast Radius theo failure path** (`governance/core/V4_1_POLICY_FREEZE.md` §4):

```
EligibleCosts → EligibleKpiProfit → ConvertedRevenue → % Target → Thưởng → Tổng lương
```

Failure path kết thúc ở **tiền lương của người thật**. Đo trên dữ liệu Golden
production: một quyết định CÓ/KHÔNG duy nhất về `DeliveryCost` dịch chuyển
thưởng **0,8–1,8 triệu VND/người/tháng** (10,94 % lợi nhuận ở 01.2026;
12,16 % ở 06.2026).

### Golden KHÔNG hạ Blast Radius (V4.1 §4.1)

Golden Baseline `ACTIVE` nhưng **không phủ path nào** của `TASK-108B`:

| Path | Golden |
|---|---|
| `EligibleKpiProfit` (số học) | ❌ NOT COVERED — `price_source_distribution = {Pending: 351/180}`, 100 % giá nhập Pending nên profit luôn `None` |
| Bucket `PERSONAL` | ❌ NOT COVERED — fixture 100 % `ADS` ở cả hai kỳ |
| `NOI_THANH_2` / `GIA_DUNG_8` | ❌ NOT COVERED — `product_group_distribution = {DIEN_MAY: 351}` |
| Đơn trộn scheme (118 OrderID) | ❌ NOT COVERED — fixture chỉ 1 scheme |
| `DeliveryCost` tham gia profit | 🟡 PARTIAL — `money.delivery_cost_total` được ghi, nhưng không invariant nào khẳng định có/không vào profit |

Vì vậy **không** hạ bậc; `Effective Risk = HIGH` giữ nguyên. Coverage gap được
báo cáo, **không** sửa Golden (phiên `DEC-143` không chạm
`tests/**`).

### Trạng thái

```
SEMANTIC_DEFINITION   = APPROVED       (DEC-143 + DEC-144; OD-108B-01 + OD-108B-02)
                                       đầy đủ — formula đã được Owner xác nhận
IMPLEMENTATION        = BLOCKED_BY_DEPENDENCY
BLOCKED_BY_DEPENDENCY = [ nguồn AccountingPurchasePrice production chưa xác
                          định kiến trúc — schema RTDB cần Owner làm rõ (DEC-146) ]
IN-SCOPE MECHANISM    = [ confirmed-adjustment source khai báo rỗng ]   ← nội bộ,
                          KHÔNG phải blocker chờ Owner (DEC-144 §5)
repair cycle          = CHƯA MỞ (0 used) — chưa có implementation nào để repair
```

Đường mở khoá: `TASK-105B` (lineage riêng bên dưới) → `TASK-108B` → `TASK-109`.

Sub-unit của lineage này (`108B-*`) **không** có ngân sách riêng, **không**
reset ngân sách, và **không** được tạo lineage mới chỉ để reset (V4.1 §2).
`TASK-109` thuộc lineage riêng, **không** dùng chung ngân sách này.

cycles:
- id: (chưa mở — implementation chưa bắt đầu vì blocker dữ liệu)
  base_sha: N/A
  head_sha: N/A

---

## Root Task: TASK-105B

Lineage **mới**, độc lập với `TASK-108B`, `TASK-110` và
`TASK-GOLDEN-BASELINE-001`. Mở tại `DEC-144` §7 (2026-08-27), trạng thái
**discovery**.

```
root_task: TASK-105B
effective_risk: HIGH
repair_cycles_allowed: 2
repair_cycles_used: 1
repair_cycles_remaining: 1
```

> **Cập nhật 2026-08-28 (S035, `DEC-156` §4 — HB-154-04, Owner Option B).**
> `TASK-105C` **không còn** dùng chung lineage này; nó có root lineage riêng
> (mục "Root Task: TASK-105C" bên dưới). Ngân sách của `TASK-105B`
> **KHÔNG ĐỔI**: `2 allowed / 1 used / 1 remaining`. Cycle `TASK-105B-RC-1`
> vẫn CONSUMED, vẫn thuộc `TASK-105B`, **không** được chuyển sang lineage
> mới và **không** được xoá. Toàn bộ nội dung lịch sử của mục này — kể cả
> các dòng bên dưới còn mô tả `TASK-105C` như phần của lineage `TASK-105B`
> theo kiến trúc `DEC-152` §11 — **giữ nguyên văn** làm bản ghi lịch sử
> (`V4.1` §10). Trạng thái hiện hành của `TASK-105C`: xem mục riêng của nó.

`HIGH` chấm theo **data path** (V4.1 §4), **không** theo tên module — một
adapter/file reader **không** được coi là LOW chỉ vì nó là adapter:

```
Price sai → KpiPurchasePrice sai → EligibleKpiProfit sai → CR sai → KPI/lương sai
```

`Local Risk = LOW-MEDIUM` (đọc file, tra bảng); `Blast Radius = HIGH`.

### Golden KHÔNG hạ Blast Radius (V4.1 §4.1)

Golden hiện `price_source_distribution = {Pending: 351/180}` — **100 %**, nên
profit arithmetic chưa từng được đo. Không có test cụ thể nào phủ đúng failure
path này ⇒ **không hạ bậc**.

Ghi chú coverage (không phải cơ sở hạ bậc): `TASK-105B` **không** cần Golden
fixture/test mới — nó không thêm field vào `WorkingLine` nên `lines_digest` và
`_covered_digest_fields` không đổi, và Golden vẫn chạy `PendingPriceProvider`
mặc định. Việc mở rộng Golden sang profit arithmetic thuộc `TASK-108B`.

### Trạng thái

```
SEMANTIC_READINESS (Q1/Q2/Q3) = READY   (DEC-145 / OD-105B-01 — KHÔNG đổi)
IMPLEMENTATION (FilePriceProvider)  = IMPLEMENTED + SELF-VERIFIED (2026-08-28,
                                phiên "TASK-105B — IMPLEMENTATION") — CHƯA
                                DONE, chờ Independent Review. Vẫn là
                                DEPENDENCY CỨNG cho TASK-105C
                                (HistoricalVendorPriceProvider compose
                                FilePriceProvider, DEC-152 §11). Chi tiết:
                                docs/tasks/TASK-105B-file-price-provider.md

HistoricalVendorPriceProvider (TASK-105C, tên chính thức từ DEC-152)
    SEMANTIC_DEFINITION = COMPLETE
    SCOPE_LOCK           = COMPLETE
    IMPLEMENTATION        = READY (chưa bắt đầu)
    Canonical spec: docs/tasks/TASK-105C-historical-vendor-price-provider.md
    (Scope Lock + Completion Gate 20 check, FROZEN tại DEC-152)
    Dependency riêng, chưa mở task: product identity mapping
    (product_raw ↔ <MÃ> Tracking) — không chặn implement/test provider,
    chặn kết quả không-Pending trên dữ liệu thật.
```

**`DEC-151` (2026-08-27, Owner Decision) — đóng dứt điểm 4/5 câu hỏi cũ
bằng THU HẸP PHẠM VI, không phải bằng trả lời từng câu.** Reports dùng
`phist/<mã>/<NCC>/<ngày>` làm nguồn giá lịch sử DUY NHẤT
(`Price(NCC,D)` = record gần nhất ≤ D, MIN qua các NCC có căn cứ); `inv.cong`
loại khỏi scope Phase 1 (không áp ngược, không bắt buộc xây lịch sử); mã
thiếu căn cứ → `Pending` chủ đích. `DEC-149` OPTION B (capture cả
`_c.min` lẫn `inv.cong`) **không còn là khuyến nghị hiện hành**. Chi tiết:
`DEC-151`, `docs/sessions/S028-task-105c-historical-kpi-price-scope-reduction.md`,
`docs/tasks/TASK-108B-eligible-costs-owner-definition.md` Phần X.

**`DEC-152` (2026-08-27, Owner Decision cuối) — đóng Q1/Q2, Scope Lock +
Completion Gate FROZEN.** Q1 (NCC retired/MIN_LOAI hồi tố) và Q2 (outlier
threshold hồi tố) **CLOSED** — cả hai KHÔNG áp ngược; Phase 1 = MIN qua
mọi candidate hợp lệ, loại sentinel `0`, không lọc gì thêm. Kiến trúc thực
thi: `HistoricalVendorPriceProvider` compose `FilePriceProvider` (đọc file
snapshot bất biến do một script export sinh ra, tách khỏi
`app/modules/pricing/`) — thay hẳn `DEC-149` OPTION B. Canonical task spec
mới: `docs/tasks/TASK-105C-historical-vendor-price-provider.md`. Product
identity mapping (`product_raw` ↔ `<MÃ>`) đặt tên tường minh làm dependency
riêng, không tự vá bằng fuzzy matching. Chi tiết: `DEC-152`,
`docs/sessions/S029-task-105c-final-decision-scope-lock.md`.

*(Đoạn dưới đây — từ `DEC-147` — giữ lại nguyên văn làm bản ghi lịch sử.
Trạng thái CURRENT nằm ở khối trên và ở `DEC-151`, không phải ở đây.)*

**Audit chéo repo (DEC-147, 2026-08-27) — đã trả lời 4/5 câu hỏi cũ.** Đã
audit `hoangvinhkta-creator/Tracking` @ `d177363a`. RTDB chạy chế độ **HYBRID**
(ảnh chụp `board` + lịch sử `phist/<mã>/<NCC>/<YYYY-MM-DD>`) ⇒ điều kiện
`BLOCKING ARCHITECTURE GAP` của `DEC-146` **KHÔNG kích hoạt**. Nhưng phát hiện
**SOURCE MISMATCH**: loại giá có lịch sử là *giá NCC báo*, còn *giá thực nhập*
(`inv.<slot>.gia`/`.lo`) không có lịch sử. Kiến trúc khuyến nghị: OPTION C
(capture bất biến) giao hàng bằng định dạng OPTION D (file 4 cột) ⇒
`FilePriceProvider` **được đề cử trở lại làm production path**.
`RTDBPriceProvider` = `NEEDS_SCHEMA_CHANGE`, không được đề cử. Chi tiết:
`DEC-147`, `docs/sessions/S024-task-105c-rtdb-price-source-audit.md`,
`docs/tasks/TASK-108B-eligible-costs-owner-definition.md` Phần VI.

**Architecture correction (DEC-146) — bối cảnh, đã được `DEC-147` cập nhật.**
Owner sửa tiền đề: Price Master không
phải file tĩnh — nguồn sự thật vận hành là **Firebase RTDB**, biến động liên
tục. Repo **không có** integration Firebase nào (đã quét toàn bộ, kể cả
`pyproject.toml` dependencies và đặc tả gốc) — không có gì để audit từ phía
code, cần Owner cung cấp schema thật. **Điều kiện `BLOCKING ARCHITECTURE GAP`
cho `TASK-108B`** nếu RTDB không lưu lịch sử giá: DEC-121 đòi hỏi tra cứu đúng
giá tại ngày quá khứ của đơn, không phải giá hiện hành — "RTDB đang chạy"
không tự động thoả điều kiện đó. Đề xuất: giữ `PriceProvider` Protocol, thêm
`RTDBPriceProvider` song song với `FilePriceProvider` (không thay thế); vai
trò cụ thể của từng cái chờ Owner xác nhận. Chi tiết:
`docs/tasks/TASK-108B-eligible-costs-owner-definition.md` Phần V.

Sub-unit tách riêng, **không** có ngân sách riêng và **không** reset ngân sách:

```
TASK-105B-Q3  (supplementary zero-price policy — OD-105B-01 §C)
    IMPLEMENTATION = BLOCKED_BY [ TASK-103 Product/Transaction Classification,
                                  hoặc danh sách enumerated do Owner cấp ]
```

Lý do blocker (báo cáo theo đúng dự phòng của `OD-105B-01` §C, không tự phát
minh matcher): `TASK-103` chưa làm; `config/classification.yaml` không tồn tại;
cơ chế duy nhất `is_non_product_line()` tự khai là *noise reduction only*,
**tạm thời** theo HD-110-02, **cấm tune**. Đo trên production: keyword set hiện
hành khớp **36** dòng trong khi đúng 3 nhóm Owner nêu chỉ **34** (dôi
`Phụ Phí`, `Phụ Phí Đổi mới`). Chi tiết:
`docs/tasks/TASK-108B-eligible-costs-owner-definition.md` Phần IV §40.

Discovery và ghi Owner Decision **không** tiêu repair cycle. Sub-unit `105B-*` không có ngân sách
riêng, không reset ngân sách.

**2026-08-28 — IMPLEMENTATION session** (`app/modules/pricing/file_price_provider.py`,
`tests/test_file_price_provider.py`, `docs/tasks/TASK-105B-file-price-provider.md`).
Implementation + self-verification **không tự tiêu** repair cycle (đúng
quy tắc §10 của phiên: "Implementation session chỉ BUILD → SELF-VERIFY →
HANDOFF"). `repair_cycles_remaining` giữ nguyên `2` — cycle chỉ mở nếu một
vòng Independent Review sau đó cho verdict FAIL và cần repair. Chi tiết
đầy đủ + 17 check evidence: `docs/tasks/TASK-105B-file-price-provider.md`.

**2026-08-28 — REPAIR CYCLE #1 mở** (phiên "TASK-105B PRICE-PARSER
MICRO-HARDENING"). Không phải phản ứng với một Independent Review FAIL —
mà là RE-TRIGGER CONDITION đã ghi sẵn tại Freeze (`DEC-153`): sửa
`HB-105B-07` (NaN → `decimal.InvalidOperation` thô) và `HB-105B-08`
(`Infinity` được chấp nhận làm giá hợp lệ) **trước** khi `TASK-105C`
implementation bắt đầu hoặc `FilePriceProvider` activation thật — điều
kiện nào tới trước (chưa điều kiện nào xảy ra; phiên này chủ động chạy
trước để không bị chặn sau). `DEC-153` đã nêu rõ hai đường hợp lệ để sửa
mã đã đóng băng: "một repair cycle mới có thẩm quyền riêng" hoặc một
`COMPLETION GATE CHANGE PROPOSAL`. Phiên này KHÔNG thay đổi bất kỳ mục
Scope Lock/Completion Gate nào (17 check REQUIRED giữ nguyên nội dung) —
vì vậy đi theo đường **repair cycle mới có thẩm quyền riêng**, chính phiên
này là phiên có thẩm quyền đó (được đặt tên tường minh làm
"NEXT AUTHORIZED ACTION" tại `DEC-153`, không tự phát sinh).

Thay đổi duy nhất: một `if not price.is_finite(): raise
InvalidPriceMasterError(reason="non_finite_price")` chèn giữa check
`missing_price` và check `negative_price` trong `_parse_price()` — dùng
đúng phép kiểm hữu hạn canonical của `Decimal` (`Decimal.is_finite()`),
không viết lại parser, không đổi normalization/effective-dating. 26 test
hồi quy mới (`tests/test_file_price_provider.py`, đủ NaN/+Infinity/
-Infinity qua string/float/`Decimal`, cả bề mặt YAML `.nan`/`.inf`, và
non-regression cho giá dương hữu hạn/0/âm hữu hạn).

```
Targeted (test_file_price_provider.py) : 33 → 59 passed (+26 test mới)
Golden (test_golden_baseline.py)       : 58 passed, 2 skipped (không đổi)
Full pytest -q                         : 730 → 756 passed, 11 skipped
                                          (chênh lệch = đúng 26 test mới,
                                          0 regression, 0 skip mới)
4 file production lõi (pipeline.py, price_engine.py, provider.py,
models.py) diff                        : 0
PendingPriceProvider vẫn mặc định pipeline; 0 caller FilePriceProvider
ngoài chính module; 0 code TASK-105C được thêm.
```

`repair_cycles_used: 0 → 1`, `repair_cycles_remaining: 2 → 1`.

cycles:
- id: TASK-105B-RC-1
  base_sha: c22cef8b47ac4cd71ef49609066a362c9e604313
  head_sha: 7f7048d65619c2c2198c99ccbfb073d6cb97ebe2
  scope: app/modules/pricing/file_price_provider.py, tests/test_file_price_provider.py
  trigger: RE-TRIGGER CONDITION đã ghi tại DEC-153 (HB-105B-07/HB-105B-08),
    không phải Independent Review FAIL
  status: CLOSED_BY_REPAIR, INDEPENDENTLY_VERIFIED — Codex Independent Review
    PASS — REPAIR VERIFIED tại 9241ccfca9a8b0159b347f4d1171c0caa37eecad;
    reviewed lineage integrated qua integration/v4-1-task-105b-rc1.

**2026-08-28 — `DEC-154` governance/spec reconciliation.** Không sửa
production code/test/config, không activate provider, không mở Repair Cycle
#2. Current role của `TASK-105B` chuyển thành Public Purchase effective-dated
provider foundation; frozen implementation/history không đổi. Remaining
`HB-105B-03/05/06/10` được audit trigger riêng và đều `triggered now = NO`.
Budget giữ nguyên:

```text
repair_cycles_allowed   = 2
repair_cycles_used      = 1
repair_cycles_remaining = 1
```

---

## Root Task: TASK-105C

Lineage **root riêng**, cấp bởi Owner tại `DEC-156` §4 (2026-08-28,
`HB-154-04` — Owner Option B). Ngân sách theo bảng đã freeze `V4.1` §2
(`HIGH/CRITICAL = 2`).

```
root_task: TASK-105C
effective_risk: HIGH
repair_cycles_allowed: 2
repair_cycles_used: 0
repair_cycles_remaining: 2
cycles: []
status: BLOCKED / NOT AUTHORIZED — Scope Lock REOPENED_BY_DEC-154;
        Completion Gate CHANGE_PROPOSAL_OPEN, NOT FROZEN;
        implementation not authorized
```

Failure path:

```text
sai HistoricalVendorMin (ngày/sentinel/candidate)
→ sai KpiPurchasePrice
→ sai EligibleKpiProfit → sai CR → sai KPI/lương
```

Golden hiện dùng `PendingPriceProvider` và không phủ nhánh giá này, nên
không hạ Blast Radius theo `V4.1` §4.1.

### Lineage trước đó — bản ghi lịch sử, KHÔNG xoá

`TASK-105C` từng dùng chung lineage `TASK-105B` (xem mục "Root Task:
TASK-105B" phía trên, giữ nguyên văn). Lý do DUY NHẤT của việc dùng chung là
kiến trúc `DEC-152` §11: `HistoricalVendorPriceProvider` **compose**
`FilePriceProvider`. `DEC-154` §13 đã gỡ composition đó — hai task nay là hai
nhánh provider song song, không còn dependency cứng.

Vì sao đây **không** phải một lineage mở "để reset ngân sách" theo nghĩa
`V4.1` §2 cấm:

```text
(a) Owner cấp tường minh (DEC-156 §4), không phải agent tự tách.
(b) Căn cứ là ARCHITECTURAL — lý do duy nhất của lineage dùng chung đã bị
    DEC-154 §13 gỡ bỏ.
(c) KHÔNG ngân sách đã tiêu nào được hoàn lại: TASK-105B-RC-1 vẫn CONSUMED
    ở TASK-105B (2/1/1). TASK-105C mở ở 0 used vì nó CHƯA TỪNG tiêu cycle
    nào của chính nó — RC-1 là repair NaN/vô cực trong FilePriceProvider,
    code thuộc nhánh Public Purchase, không thuộc TASK-105C.
(d) Historical evidence, review record, freeze record: giữ nguyên toàn bộ.
```

Artifact hiện có của lineage:

- `docs/tasks/TASK-105C-historical-vendor-price-provider.md`
- `DEC-151`, `DEC-152`, `DEC-154` §13, `DEC-156` §4 trong
  `PROJECT/PROJECT_DECISIONS.md`

---

## Root Task: TASK-105E

Lineage **mới**, cấp cùng lúc với task ID tại `DEC-156` §5 (2026-08-28).
Ngân sách theo bảng đã freeze `V4.1` §2 (`HIGH/CRITICAL = 2`) — cấp lineage
là thao tác cơ học theo bảng, không phải một quyết định ngân sách riêng.

```
root_task: TASK-105E
effective_risk: HIGH
repair_cycles_allowed: 2
repair_cycles_used: 0
repair_cycles_remaining: 2
cycles: []
status: PLANNED — task ID và phạm vi trách nhiệm do Owner cấp; Scope Lock
        chưa soạn; Completion Gate chưa soạn/chưa freeze; implementation
        not authorized
```

Failure path:

```text
chọn sai nguồn giá / sai thứ tự P00–P11 / mất provenance
→ sai KpiPurchasePrice
→ sai EligibleKpiProfit → sai CR → sai KPI/lương
```

Golden hiện dùng `PendingPriceProvider` và không phủ price composition path,
nên không hạ Blast Radius theo `V4.1` §4.1.

Artifact hiện có của lineage:

- `docs/tasks/TASK-105E-price-resolution-composition.md`
- `DEC-156` §5 trong `PROJECT/PROJECT_DECISIONS.md`

Không cycle nào được mở bởi việc cấp task ID. `cycles: []`.

---

## Root Task: TASK-105D

```
root_task: TASK-105D
effective_risk: HIGH
repair_cycles_allowed: 2
repair_cycles_used: 0
repair_cycles_remaining: 2
status: PLANNED — specification complete + data contract complete (S034/
        DEC-155) + Owner ratified (S035/DEC-156); Ready Gate blocked bởi
        ĐÚNG MỘT blocker còn lại: Completion Gate freeze bởi một phiên
        Freeze Finalization có thẩm quyền riêng (V4.1 §12);
        Completion Gate draft/not frozen; implementation not authorized
freeze_attempts:
    - id: TASK-105D-FREEZE-1
      session: S036 (2026-08-28)
      reviewed_base_sha: 9cd871488a6baebf6b80737f42e2137a27887cef
      verdict: FAIL — freeze TỪ CHỐI; Ready Gate vẫn BLOCKED
      findings: 5 BLOCKING / 5 HARDENING / 3 OUT_OF_SCOPE
      repair_cycle_consumed: 0
      evidence: docs/reviews/TASK-105D-FREEZE-FINALIZATION-REVIEW.md
```

`repair_cycles_used` giữ nguyên `0`. Một **independent freeze review** không
tiêu repair cycle: `V4.1` §3 tính cycle theo **lần sửa** (cumulative repair
diff), và `S036` không sửa một dòng nào của gate, code hay test — nó chỉ ghi
finding. Cycle chỉ mở khi một phiên gate revision thực sự sửa gate để đáp ứng
`F-01`…`F-05`, và ngay cả khi đó `V4.1` cấm mở Repair Cycle chỉ vì
documentation/gate issue trừ khi Owner quyết định khác.

Failure path:

```text
sai namespace/identity/cutover
→ sai provider/price provenance
→ sai KpiPurchasePrice
→ sai KPI/lương
```

Golden hiện dùng `PendingPriceProvider` và không phủ product-resolution/price
composition path, nên không hạ Blast Radius theo V4.1 §4.1.

Artifact hiện có của lineage (5):

- `docs/tasks/TASK-105D-product-identity-resolver.md` (S032/`DEC-154`)
- `DEC-154` trong `PROJECT/PROJECT_DECISIONS.md`
- `docs/spec/TASK-105D-DATA-CONTRACT.md` (S034/`DEC-155`)
- `DEC-155` trong `PROJECT/PROJECT_DECISIONS.md`
- `DEC-156` trong `PROJECT/PROJECT_DECISIONS.md` (S035, Owner Ratification)

`DEC-156` là artifact thứ 5, tức thuộc diện `OWNER APPROVAL REQUIRED` của
`V4.1` §10. Approval đó chính là chỉ thị trực tiếp của Owner trong phiên
ratification ("ghi nhận các Owner Decisions vào canonical decision/task/
progress artifacts theo đúng governance") — ghi lại tường minh, xem
`DEC-156` phần đầu.

Không cycle nào được mở bởi việc tạo specification hay bởi phiên readiness.
`cycles: []`.

Cập nhật 2026-08-28 (S034, `DEC-155` — readiness/data contract):
`repair_cycles_used` giữ nguyên `0`. Một phiên readiness/documentation
**không phải** repair cycle — V4.1 §3 tính cycle theo LẦN SỬA một defect
BLOCKING, và independent review tại `61a90b4f` ghi `BLOCKING = 0`. Ready Gate
blocker giảm từ 4 xuống 2 (Owner ratification `OR-01`/`OR-02`/`OR-03`;
Completion Gate freeze bởi authority riêng). `status` cập nhật bên dưới.

---

## Cách xác định phạm vi một repair cycle (tham chiếu)

```
git diff <base_sha>..<head_sha> --name-only
```

Cycle được tính theo LẦN SỬA, không theo số review. Nếu repair tiếp tục
trong cùng cycle, `head_sha` phải tiến lên SHA mới; `base_sha` không reset.
Không dùng session mới / sub-unit mới / branch mới để reset `base_sha`.

## Owner Extension log

*(Trống. Mỗi Owner Extension được cấp sau này phải thêm một mục vào đây, kèm
root task, phạm vi, và budget cụ thể.)*

Tính đến `V4.1-1` (2026-08-27): **chưa có Owner Extension nào được cấp.**
`R1-A2` → `R8` của lineage `TASK-110` vì vậy **không unit nào được tự mở**.
`DEC-141` là Owner Decision về Gate Class và integration — **không phải** một
Owner Extension, và **không** cấp thêm repair cycle.

## Cập nhật gần nhất

- 2026-08-27 — Khởi tạo ledger tại `TASK-V4-ADOPTION` (V4.1-0, Policy
  Adoption). `TASK-V4-ADOPTION` mở với 1 repair cycle khả dụng, 0 đã dùng.
  `TASK-110` ghi nhận ở trạng thái transition `EXHAUSTED_PRE_V4.1`, remaining
  = 0.
- 2026-08-27 — `V4.1-1` INTEGRATION. Hợp nhất `TASK-110`/`R1-A1` (`01a03b0`,
  `FROZEN` theo `DEC-139`) và Governance V4.1 (`8d79009`) vào nhánh mặc định
  qua integration branch `integration/v4-1-task-110`. Owner Decision
  `DEC-141`: `CHECK-110-16` → Gate Class `POST_MERGE_PRODUCTION_ACCEPTANCE`
  (Status vẫn `BLOCKED`); `DEC-128` của V4.1 đổi thành `DEC-140` để giải ID
  collision với `DEC-128` của `TASK-110`; `KNOWN PRE-V4.1 DIVERGENCE` đóng.
  **Ngân sách không đổi:** `TASK-110` vẫn `EXHAUSTED_PRE_V4.1`, remaining = 0.
  Thay đổi tài liệu của phiên integration được phân loại
  `INTEGRATION STATE RECONCILIATION`, **không** tính là repair cycle.
- 2026-08-27 — `TASK-GOLDEN-BASELINE-001` mở lineage mới sau Owner Decision
  `OD-GB-1 = A + A1`. Discovery (`b738fa4`) + implementation Golden Business
  Baseline trên hai kỳ Tín Phát 01.2026/06.2026 từ workbook production thật do
  Owner cung cấp. `effective_risk = HIGH`, 2 cycle khả dụng, **0 đã dùng**.
  `TASK-110` **không đổi**: vẫn `EXHAUSTED_PRE_V4.1`, remaining = 0;
  `CHECK-110-16` vẫn `REQUIRED · BLOCKED · POST_MERGE_PRODUCTION_ACCEPTANCE`.
- 2026-08-27 — `TASK-GOLDEN-BASELINE-001` repair cycle #1 (`GB-IR-01`). Sau
  Independent Review trên `4bccf46` (verdict FAIL, đúng 1 BLOCKING finding):
  `test_golden_expected_output_is_regenerable_byte_identical` so byte-thô
  toàn bộ file expected, gồm cả `_environment` advisory
  (`python`/`pyyaml`/`openpyxl`) — false regression signal trên một Python
  hợp lệ khác (tái hiện: Python 3.12.3 → `50 passed, 2 failed, 2 skipped`).
  Sửa bằng `_strict_bytes()` (tái dùng `_comparable()` đã có), loại đúng ba
  trường advisory khỏi phép so byte. Không đổi `expected/*.json`, không đổi
  fixture, business payload trước/sau IDENTICAL. Repair SHA `54a575d`.
  `repair_cycles_used: 1`, `repair_cycles_remaining: 1`. `TASK-110`,
  `CHECK-110-16`, `app/`, `config/` không đổi.
- 2026-08-27 — `TASK-GOLDEN-BASELINE-001` **Independent Review #2 RECORDED**
  (phiên "VERDICT RECORDING ONLY", không phải phiên review mới). Verdict
  `PASS — ELIGIBLE_FOR_FREEZE` tại reviewed SHA `8521069…`, đã được Owner
  cung cấp từ một review chạy ngoài canonical repo, nay ghi vào
  `docs/reviews/TASK-GOLDEN-BASELINE-001-INDEPENDENT-REVIEW-2.md`. `GB-IR-01`
  = `CLOSED_BY_REPAIR, INDEPENDENTLY_VERIFIED`. `BLOCKING = 0`.
  `repair_cycles_used` vẫn `1`, `remaining` vẫn `1` — review này **không**
  tiêu cycle. `FROZEN = NO`, `DONE = NO`, `MERGED = NO`: verdict PASS thuộc
  thẩm quyền independent reviewer, còn `FROZEN` thuộc một phiên Freeze
  Finalization riêng chưa chạy (`governance/core/V4_1_POLICY_FREEZE.md`
  §12). `TASK-110`, `CHECK-110-16`, `app/`, `config/` không đổi.
- 2026-08-27 — `TASK-GOLDEN-BASELINE-001` **FREEZE FINALIZATION** (`DEC-142`,
  phiên "FREEZE FINALIZATION + CONTROLLED INTEGRATION"). `FROZEN = YES` tại
  reviewed SHA `85210691702550d83c0fd42fe816be8ca9dde889` (review verdict
  record `94b2513d1894dbd58f3b08656e3c7412be191df5`). Golden Baseline
  contract (fixture, expected output, strict business comparison) niêm phong.
  `repair_cycles_used` vẫn `1`, `remaining` vẫn `1` — **UNUSED**, đóng task
  không bắt buộc dùng hết ngân sách. `TASK-110`, `CHECK-110-16`, `app/`,
  `config/` không đổi.
- 2026-08-27 — `TASK-GOLDEN-BASELINE-001` **CONTROLLED INTEGRATION + DONE**
  (cùng phiên trên). Merge `--no-ff` qua nhánh trung gian
  `integration/v4-1-golden-baseline` vào nhánh mặc định
  `claude/extract-upload-repo-gq2ws4` tại SHA
  `f332a4cb4410b3ca9c71d659d36a3e8f26aa1fa5`. Trên default: Golden test
  `58 passed, 2 skipped`; `pytest -q` toàn bộ `697 passed, 11 skipped, 0
  failed` (0 regression); business anchors 01/2026 và 06/2026 khớp tuyệt đối;
  `validate_reference_integrity` vẫn đúng 3 lỗi pre-existing (`TASK-REM-T06`).
  `MERGED = YES`. GB-12 Exit Criteria (11 điều kiện) đủ ⇒ `DONE = YES`.
  `V4.1` chuyển `POLICY_ADOPTED` → **`FULLY_ENFORCED`** (ba executable
  enforcement asset đã kiểm chứng chạy được trên default:
  `scripts/branch_authority_check.sh`, ledger này, `tests/test_golden_baseline.py`).
  `TASK-110`, `CHECK-110-16`, `R1-A1`, `app/`, `config/`,
  `tests/fixtures/baseline/**`, `tests/test_task110_non_regression.py`
  **không đổi một byte** qua toàn bộ integration.

- 2026-08-27 — `TASK-108B` **mở lineage mới** sau Owner Decision `OD-108B-01`
  (ghi tại `DEC-143`). `EligibleCosts = {}` (closed empty set),
  `DeliveryCost = NOT ELIGIBLE FOR NOW`, `OtherKpiAdjustment = 0 by definition`,
  canonical formula chốt `(SellPrice − KpiPurchasePrice) × Quantity − Discount`.
  **C15 ĐÓNG.** `effective_risk = HIGH`, 2 cycle khả dụng, **0 đã dùng** —
  phiên ghi quyết định **không** phải repair cycle và **không** tiêu ngân sách.
  `SEMANTIC_DEFINITION = APPROVED` nhưng
  `IMPLEMENTATION = BLOCKED_BY_DEPENDENCY`: số blocker giảm **4 → 2**, cả hai
  còn lại là dependency **dữ liệu** (Price Master; confirmed
  `KpiPurchaseAdjustment` persistence), không phải semantic. `TASK-110`
  **không đổi**: vẫn `EXHAUSTED_PRE_V4.1`, remaining = 0; `CHECK-110-16` vẫn
  `REQUIRED · BLOCKED · POST_MERGE_PRODUCTION_ACCEPTANCE`;
  `TASK-GOLDEN-BASELINE-001` vẫn `remaining = 1` UNUSED. `app/`, `config/`,
  `tests/`, Golden fixture/expected **không đổi một byte**.

- 2026-08-27 — `DEC-144` (`OD-108B-02` + Owner confirmation cho `DEC-143`).
  Canonical `EligibleKpiProfit` được Owner **xác nhận**:
  `(SellPrice − KpiPurchasePrice) × Quantity − Discount` — đóng divergence
  §19.1 đã báo cáo theo V4.1 §11. Confirmed `KpiPurchaseAdjustment` chọn
  phương án A: absence **đã xác định** → `KpiPurchasePrice =
  AccountingPurchasePrice` + provenance `Config:NoConfirmedAdjustment`;
  `UNKNOWN`/`SOURCE_UNAVAILABLE`/`LOOKUP_FAILURE` **giữ Pending**, tuyệt đối
  không thành `0`. `TASK-108B` blocker ngoại lai **2 → 1** (chỉ còn Price
  Master); yêu cầu cơ chế còn lại (source khai báo rỗng) thuộc phạm vi chính
  `TASK-108B`, không phải blocker chờ Owner. **`TASK-105B` mở lineage mới** ở
  trạng thái discovery, `effective_risk = HIGH`, 2 cycle khả dụng, **0 đã
  dùng** — discovery không tiêu cycle. `TASK-110` **không đổi**
  (`EXHAUSTED_PRE_V4.1`, remaining = 0; `CHECK-110-16` vẫn `REQUIRED · BLOCKED ·
  POST_MERGE_PRODUCTION_ACCEPTANCE`); `TASK-GOLDEN-BASELINE-001` vẫn
  `remaining = 1` UNUSED. `app/`, `config/`, `tests/`, Golden fixture/expected
  **không đổi một byte**.

- 2026-08-27 — `DEC-145` (`OD-105B-01`). Owner chốt Q1/Q2/Q3 của `TASK-105B`:
  khoảng hiệu lực **đóng** `[from, to]` với overlap/nhiều-record-mở =
  `INVALID PRICE MASTER` và gap → `Pending` (cấm latest/nearest/current);
  normalization NFC → strip → collapse → casefold (cấm bỏ dấu, fuzzy,
  nearest, contains); dòng phụ `AccountingPurchasePrice = 0 BY DEFINITION` với
  provenance `Policy:SupplementaryExpenseZeroPurchasePrice`. `TASK-105B`
  chuyển `OWNER_DECISION_REQUIRED` → **`SEMANTIC_READINESS = READY`,
  `IMPLEMENTATION = READY`**, chỉ chờ file giá 4 cột. **`TASK-105B-Q3` tách
  riêng và BLOCKED** bởi `TASK-103` — báo cáo theo đúng dự phòng của
  `OD-105B-01` §C, không tự phát minh matcher. `TASK-108B` blocker cập nhật
  thành "FilePriceProvider chưa tồn tại + chưa có bảng giá". Ngân sách
  **không đổi** ở mọi lineage: `TASK-105B` 2/0/2, `TASK-108B` 2/0/2,
  `TASK-110` `EXHAUSTED_PRE_V4.1` remaining = 0,
  `TASK-GOLDEN-BASELINE-001` remaining = 1 UNUSED. `app/`, `config/`,
  `tests/`, Golden fixture/expected **không đổi một byte**.

- 2026-08-27 — `DEC-146` — Architecture Correction Audit cho `TASK-105B`.
  Owner sửa tiền đề đã dùng ở `DEC-144`/`DEC-145`: Price Master **không phải
  file tĩnh** — nguồn sự thật vận hành là **Firebase RTDB**, biến động liên
  tục trong ngày. Quét toàn repo: **0** integration Firebase/RTDB nào tồn tại
  (chỉ 2 chỗ nhắc "Firebase" là boilerplate template governance chung, không
  phải quyết định kỹ thuật của dự án này); `pyproject.toml` không có
  `firebase-admin` hay SDK liên quan; không credential/schema/crawler nào
  được ghi lại ở bất kỳ đâu. `CONFLICT DETECTED` đã báo cáo theo đúng giao
  thức: `ADR-101` nêu tên PostgreSQL/SQLite cho Phase 2, không nơi nào nhắc
  Firebase làm kiến trúc dự án.

  `TASK-105B` chuyển từ `IMPLEMENTATION = READY` (DEC-145) sang **TẠM DỪNG**
  — không phải blocker kỹ thuật (contract §38 vẫn buildable y hệt), mà là
  quyết định phạm vi/vai trò cần Owner xác nhận trước khi tránh làm lại.
  `SEMANTIC_READINESS` (Q1/Q2/Q3, DEC-145) **giữ nguyên đúng** — ba câu hỏi đó
  ràng buộc **hình dạng dữ liệu giá**, độc lập với nơi nó tới từ đâu.

  **Điều kiện `BLOCKING ARCHITECTURE GAP` cho `TASK-108B`** nếu RTDB chỉ lưu
  giá hiện hành (overwrite, không giữ lịch sử) — DEC-121 đòi hỏi tra cứu đúng
  giá tại ngày quá khứ của đơn; "RTDB đang chạy" trả lời câu hỏi khác ("giá
  hiện tại"), không phải câu hỏi `TASK-108B` cần. Chưa xác định — cần Owner
  trả lời trực tiếp, không suy đoán.

  Đề xuất: giữ `PriceProvider` Protocol (đã đúng thiết kế từ DEC-103), thêm
  `TASK-105C` (`RTDBPriceProvider`) **song song** với `TASK-105B`
  (`FilePriceProvider`, vai trò lùi thành bootstrap/test-fixture/snapshot-export
  tuỳ câu trả lời Owner) — không thay thế nhau. `RTDBPriceProvider` **không
  bao giờ** default trong test/Golden (nguyên tắc deterministic).

  `TASK-105B-Q3` (chính sách zero-price dòng phụ) **không đổi**, vẫn `BLOCKED`
  bởi `TASK-103`/enumeration — hoàn toàn độc lập với nguồn giá. Audit evidence
  đang làm dở (30 raw label từ `evidence.json`: `Chi phí vận chuyển` 1.074
  dòng, `Chi phí lắp đặt` 84, `Chênh VAT` 33, cộng biến thể ghép/typo) **không
  mất** — tạm dừng theo yêu cầu Owner, tiếp tục được ở phiên sau.

  Đây là **audit, không phải repair cycle** — ngân sách mọi lineage không đổi:
  `TASK-105B` 2/0/2, `TASK-108B` 2/0/2, `TASK-110` `EXHAUSTED_PRE_V4.1`
  remaining = 0, `TASK-GOLDEN-BASELINE-001` remaining = 1 UNUSED. `app/`,
  `config/`, `tests/`, Golden fixture/expected **không đổi một byte**.

- 2026-08-27 — `DEC-147` — Cross-Repo RTDB Price Source Audit (`TASK-105C`
  discovery, phiên `S024`). Đã audit repository vận hành hệ thống giá
  (`hoangvinhkta-creator/Tracking` @ `d177363a390d36fe793e0c1c44a6fb6743ca45f5`)
  và đối chiếu với contract `PriceProvider`. Hai repo giữ **độc lập** — không
  subtree, không submodule, không copy source, không merge history; repo giá
  **không bị sửa một byte nào**.

  **Bốn trong năm câu hỏi của `DEC-146` §49 đã đóng bằng bằng chứng code (E1).**
  RTDB chạy chế độ **HYBRID**: `board/<mã>/p/<NCC>` là ảnh chụp hiện hành,
  `phist/<mã>/<NCC>/<YYYY-MM-DD>` là lịch sử append theo ngày, chỉ ghi khi giá
  đổi. ⇒ Điều kiện **`BLOCKING ARCHITECTURE GAP` của `DEC-146` §3 KHÔNG kích
  hoạt**.

  **Nhưng kết luận thật là `SOURCE MISMATCH`, không nằm trong hai nhánh
  `DEC-146` dự trù:** loại giá *có* lịch sử là **giá NCC báo** (báo giá nhà
  cung cấp trong ngày), còn loại giá Reports *cần* — **giá thực nhập**
  (`inv.<slot>.gia` / `.lo`) — **không có lịch sử** (hai ô cuốn chiếu
  `cu`/`moi`, ghi bằng `set()` đè cả nhánh; `backup/` không chứa `inv`).

  Ba phát hiện nữa ảnh hưởng trực tiếp tới con số: RTDB lưu tiền theo **nghìn
  đồng** (va `ADR-103` — phép ×1.000 phải nằm ở biên nhập, không nằm trong
  `app/modules/pricing/`); `phist == 0` là **sentinel hết hàng**, phải map
  thành gap → `Pending`, tuyệt đối không thành `purchase_price = 0`
  (`DEC-145` §5); và **lịch sử sửa được** — bốn đường xoá/dời/mồ côi/lệch đang
  chạy trong app ⇒ chỉ một bản ghi **bất biến, đóng băng** mới thoả `DEC-121`.

  **Kiến trúc khuyến nghị: OPTION C (capture bất biến) giao hàng bằng định
  dạng OPTION D (file 4 cột `DEC-145` §4).** Hệ quả:
  `FilePriceProvider` **được đề cử trở lại làm production path** — đảo lại
  nghi vấn của `DEC-146` §6, không huỷ gì của `DEC-145`;
  `RTDBPriceProvider` = **`NEEDS_SCHEMA_CHANGE`, không được đề cử** (đọc thẳng
  va `ADR-101` ranh giới mạng + `ADR-103` §2 đơn vị, và nguồn thì mutable).

  Khoá sản phẩm: RTDB **đã có** mã ổn định (`normCode` + `alias`), nhưng
  Reports dùng `product_raw` = câu tên hàng trên chứng từ ⇒ **cần mapping**.
  Repo giá đã **thử** rút mã từ tên hàng bằng máy (`extractCode()`) và **bỏ
  hẳn** vì đoán sai trên tài sản thật — tiền lệ production ủng hộ đúng lệnh
  cấm fuzzy matching của `OD-105B-01` §B. `DEC-145` §2 **không đổi**.

  Security: **không** có BLOCKING finding — không credential nào committed,
  service account nằm ở Cloudflare Secret, rules gốc `.read/.write = false`,
  không nhánh nào cho `auth == null`, App Check Enforce từ 13/08/2026. Ba mục
  HARDENING thuộc repo giá (nhật ký `hist` tối đa 100 dòng và mọi nhân viên
  ghi đè được; `phist` sửa được bởi mọi tài khoản `edit`; Reports sẽ cần một
  mặt phẳng quản lý secret mới nếu đọc thẳng RTDB) — **ngoài phạm vi** sửa của
  phiên này.

  `TASK-105B-Q3` **không đổi**, vẫn `BLOCKED` bởi `TASK-103`/enumeration —
  hoàn toàn độc lập với nguồn giá, đúng như `DEC-146` §7. Audit evidence 30
  raw label **không mất**.

  Đây là **audit, không phải repair cycle** — ngân sách mọi lineage không đổi:
  `TASK-105B` 2/0/2, `TASK-108B` 2/0/2, `TASK-110` `EXHAUSTED_PRE_V4.1`
  remaining = 0, `TASK-GOLDEN-BASELINE-001` remaining = 1 UNUSED. `app/`,
  `config/`, `tests/`, Golden fixture/expected **không đổi một byte**. Repo
  giá: **0 file thay đổi**.

- 2026-08-27 — `DEC-148` (audit) — `inv.cong` public purchase price audit.
  Xác nhận 4 semantics chủ dự án đề xuất; kết luận `inv.cong` KHÔNG có lịch
  sử, NO GUARANTEED DELAY WINDOW. Không tiêu repair cycle. Chi tiết: xem
  `DEC-148` trong `PROJECT_DECISIONS.md`.

- 2026-08-27 — `DEC-149` (audit) — Market Min Price Path Audit. `CONFLICT
  DETECTED`: business rule "Min ưu tiên, cong fallback" không khớp công
  thức `_c.min` thật (`cong` hoà tan bên trong, không phải fallback độc
  lập). Historical Replay = C (chỉ current snapshot). Không tiêu repair
  cycle. Chi tiết: xem `DEC-149` trong `PROJECT_DECISIONS.md`.

- 2026-08-27 — `DEC-150` (audit fact, không phải Owner Decision) — xác
  minh popup "Lịch sử giá" = vendor-price history thuần từ `phist`, KHÔNG
  phải Min history, không reconstruct Min. Không đổi trạng thái nào của
  `DEC-149`. Không tiêu repair cycle. Chi tiết: xem `DEC-150` trong
  `PROJECT_DECISIONS.md`.

- 2026-08-27 — `DEC-151` (**Owner Decision**) — Historical KPI Purchase
  Price Scope Reduction. Đóng `CONFLICT DETECTED` (`DEC-149` §71) bằng
  **thu hẹp phạm vi**, không phải bằng chọn giữa hai lựa chọn cũ: Reports
  dùng `phist` làm nguồn giá lịch sử DUY NHẤT
  (`Price(NCC,D)` = record gần nhất ≤ D, MIN qua các NCC có căn cứ, loại
  sentinel `0`); `inv.cong` loại khỏi scope Phase 1 (không áp ngược, không
  bắt buộc xây lịch sử); mã thiếu căn cứ → `Pending` chủ đích, xử lý tay
  sau (explicit, có provenance, không rewrite `phist`, không backdating).
  `DEC-149` OPTION B (capture `_c.min` + `inv.cong`) **không còn là
  khuyến nghị hiện hành** — mục tiêu nó phục vụ (tái dựng đúng `_c.min`)
  đã bị loại bỏ, không phải vì sai mà vì không còn cần.
  Audit hẹp bắt buộc trong phiên: `phist` **đủ** cho `HistoricalVendorPrice`
  deterministic theo semantics trên, không cần giả định
  `NCC_RETIRED`/`NCC_MIN_LOAI`/`NGUONG_BAT_THUONG` hiện tại áp cho lịch sử
  (`buildSync()` ghi `phist` bất kể trạng thái loại trừ). Hai câu hỏi
  filtering còn mở, không tự trả lời: Q1 (NCC retired/MIN_LOAI hồi tố),
  Q2 (outlier threshold hồi tố) — KHÔNG chặn mở implementation.
  `TASK-105C` `BLOCKED_BY` hẹp lại còn Q1/Q2 (không chặn) +
  `TASK-105B-Q3` (độc lập, không đổi). `TASK-108B` blocker tương ứng.
  Đây là **Owner Decision recording, không phải repair cycle** — ngân sách
  mọi lineage không đổi: `TASK-105B` 2/0/2, `TASK-108B` 2/0/2, `TASK-110`
  `EXHAUSTED_PRE_V4.1` remaining = 0, `TASK-GOLDEN-BASELINE-001`
  remaining = 1 UNUSED. `app/`, `config/`, `tests/`, Golden fixture/expected
  **không đổi một byte**. Repo giá: **0 file thay đổi**. Chi tiết: `DEC-151`,
  `docs/sessions/S028-task-105c-historical-kpi-price-scope-reduction.md`,
  `docs/tasks/TASK-108B-eligible-costs-owner-definition.md` Phần X.

- 2026-08-27 — `DEC-152` (**Owner Decision cuối** + Scope Lock/Completion
  Gate) — đóng Q1 (NCC retired/MIN_LOAI hồi tố) và Q2 (outlier threshold
  hồi tố), cả hai **CLOSED**: trạng thái NCC/config HIỆN TẠI không được áp
  ngược cho quá khứ; Phase 1 = MIN qua mọi candidate hợp lệ tại D (loại
  sentinel `0`), không lọc gì thêm. Tạo
  `docs/tasks/TASK-105C-historical-vendor-price-provider.md` — canonical
  spec 24 mục, Scope Lock (Phạm Vi/Ngoài Phạm Vi/Vùng Tác Động), Completion
  Gate 20 check (`CHECK-105C-01`…`20`, toàn bộ `NOT_TESTED` — chưa
  implementation). Kiến trúc thực thi: `HistoricalVendorPriceProvider`
  compose `FilePriceProvider` (đọc file snapshot bất biến do
  `tools/pricing/` sinh ra, tách khỏi `app/modules/pricing/` — giữ ranh
  giới `ADR-101`); thay hẳn `DEC-149` OPTION B. Xác định rõ dependency
  chưa đóng: mapping `product_raw` (Reports) ↔ `<MÃ>` (Tracking) — chưa mở
  task, **không** tự vá bằng fuzzy matching (`OD-105B-01` §B, tiền lệ
  `extractCode()` thất bại — `DEC-147` §56). `TASK-105B` trở thành
  dependency CỨNG (chưa DONE) cho `TASK-105C`.
  Verdict: `TASK-105C` `SEMANTIC_DEFINITION = COMPLETE`,
  `SCOPE_LOCK = COMPLETE`, `IMPLEMENTATION = READY`. `TASK-108B`
  `BLOCKED_BY` = [`TASK-105C` implementation (kèm `TASK-105B`), product
  identity mapping, `TASK-105B-Q3`] — không còn câu hỏi nghiệp vụ nào chờ
  Owner.
  Đây là **Owner Decision + Scope Lock recording, không phải repair
  cycle** — ngân sách mọi lineage không đổi: `TASK-105B` 2/0/2 (dùng
  chung cho `TASK-105C`), `TASK-108B` 2/0/2, `TASK-110`
  `EXHAUSTED_PRE_V4.1` remaining = 0, `TASK-GOLDEN-BASELINE-001`
  remaining = 1 UNUSED. `app/`, `config/`, `tests/`, Golden fixture/expected
  **không đổi một byte**. Repo giá: **0 file thay đổi**. Chi tiết: `DEC-152`,
  `docs/tasks/TASK-105C-historical-vendor-price-provider.md`,
  `docs/sessions/S029-task-105c-final-decision-scope-lock.md`.

- 2026-08-28 — `TASK-105B` **IMPLEMENTATION** (phiên "TASK-105B — IMPLEMENTATION").
  `FilePriceProvider` (`app/modules/pricing/file_price_provider.py`, MỚI)
  implement đúng contract `DEC-145`/`OD-105B-01` — khoảng hiệu lực đóng,
  chuẩn hoá NFC+casefold, validation §5 đầy đủ (overlap, >1 open record,
  giá âm/rỗng, ngày lỗi, duplicate hoàn toàn), provenance 3 phần
  (raw/normalized/matched record), `InvalidPriceMasterError` raise khi
  nạp. **Completion Gate frozen tại phiên này**
  (`docs/tasks/TASK-105B-file-price-provider.md`, CHECK-105B-01..17 — 16
  check gốc từ §38.5 của `docs/tasks/TASK-108B-eligible-costs-owner-definition.md`
  + 1 check mới đóng risk note Firebase-import của `DEC-146`). **17/17
  REQUIRED PASS** (self-verify, E1; CHECK-105B-12 đạt E2). Evidence:
  `pytest tests/test_file_price_provider.py -q` → `33 passed`;
  `pytest tests/test_golden_baseline.py -q` → `58 passed, 2 skipped`
  (không đổi); `pytest -q` toàn bộ → `730 passed, 11 skipped` (trước
  phiên `697 passed, 11 skipped` — chênh lệch đúng 33 test mới, **0
  regression**); diff `app/pipeline.py`/`price_engine.py`/`provider.py`/
  `models.py` = **0**; 4 validator PASS,
  `validate_reference_integrity` giữ đúng 3 lỗi tiền tồn `TASK-REM-T06`.
  Provider mặc định **không đổi** (`PendingPriceProvider`, Golden không
  chạm). **Đây là implementation session, KHÔNG tự tiêu repair cycle**
  (`TASK-105B` vẫn `2 allowed / 0 used / 2 remaining`) và **KHÔNG tự
  DONE** — `Effective Risk = HIGH` đòi Independent Review độc lập trước
  (đúng tiền lệ `TASK-GOLDEN-BASELINE-001`). Bảng giá production thật
  **chưa có** — data dependency mở, không phải code blocker.
  `TASK-105C` **vẫn KHÔNG được bắt đầu implementation** cho tới khi
  `TASK-105B` qua Independent Review và chuyển `DONE` (dependency cứng,
  `DEC-152` §11). `app/pipeline.py`, `provider.py`, `price_engine.py`,
  `models.py`, `config/`, Golden fixture/expected **không đổi một byte**.
  Chi tiết đầy đủ: `docs/tasks/TASK-105B-file-price-provider.md`.

- 2026-08-28 — `TASK-105B` **INDEPENDENT REVIEW RECONCILIATION** (phiên
  "TASK-105B — INDEPENDENT REVIEW RECONCILIATION", canonicalization only —
  không phải review lần 3, không remediation). Phát hiện: hai session
  Independent Review #1 độc lập đã chạy **song song** trên hai nhánh khác
  nhau — `review/task-105b-independent-review-1` (SHA
  `be2e35c908921f16e8347ecdfd23e2f9aecf1069`) và
  `claude/file-price-provider-review-negpxw` (SHA
  `b735dace8bdbaea086b37f8c20e091cafbed03e5`) — không biết về nhau, cùng
  review đúng implementation SHA `c22cef8` (`merge-base` của hai review =
  `c22cef8`, xác nhận không drift), cùng ghi artifact tại đúng
  `docs/reviews/TASK-105B-INDEPENDENT-REVIEW-1.md`. Cả hai verdict `PASS —
  ELIGIBLE_FOR_FREEZE`, 17/17 REQUIRED PASS độc lập ở cả hai bên, cùng số
  liệu regression/Golden. Reconciliation: dedupe namespace `HB-105B-*`
  (phát hiện Review B tái dùng nhầm hai ID `HB-105B-01`/`HB-105B-02` vốn đã
  thuộc `TASK-108B` §34 — không liên quan `FilePriceProvider` — sửa canonical
  ID về `HB-105B-07`/`HB-105B-08` từ Review A, không collision, không reuse
  ID); giải quyết một classification disagreement (`HB-105B-04`: HARDENING
  theo Review B vs OUT_OF_SCOPE theo Review A — reconciled = OUT_OF_SCOPE
  theo đúng normative Scope Lock table đã frozen của `TASK-105B`, `V4.1`
  §7/§11 — không ảnh hưởng Freeze eligibility nên không cần Owner Decision).
  0 BLOCKING sau reconciliation ⇒ verdict hội tụ `PASS —
  ELIGIBLE_FOR_FREEZE`. Cả hai artifact gốc bảo toàn nguyên vẹn: Review A
  giữ canonical path, Review B archived byte-identical tại
  `docs/reviews/archive/TASK-105B-INDEPENDENT-REVIEW-1-B-file-price-provider-review-negpxw.md`.
  **Đây KHÔNG phải remediation cycle** — `app/**`/`tests/**`/`config/**` = 0
  trong toàn bộ diff phiên này; `TASK-105B` vẫn `2 allowed / 0 used / 2
  remaining` (**không đổi**, đúng `V4.1` §3 — cycle tính theo lần sửa,
  không theo số review/số artifact reconcile). Chi tiết đầy đủ:
  `docs/reviews/TASK-105B-INDEPENDENT-REVIEW-RECONCILIATION.md`. **NEXT
  AUTHORIZED ACTION = `TASK-105B` FREEZE** (phiên Freeze Finalization có
  thẩm quyền riêng, `V4.1` §12 — reconciliation session read-only không
  được ghi `FROZEN`).

### Branch divergence đã biết — lineage `TASK-105B`/`TASK-105C`

**ĐÃ ĐÓNG (2026-08-27, phiên "CONTROLLED INTEGRATION — TASK-105B/TASK-105C
GOVERNANCE CHECKPOINT").** Owner chọn option (A) của V4.1 §8: integrate/merge
sớm.

Divergence đo được ngay trước integration, so với nhánh mặc định
`claude/extract-upload-repo-gq2ws4` @ `7e60978`:

| Nhánh | ahead | LOC | vượt ngưỡng |
|---|---:|---:|---|
| `claude/reports-price-rtdb-audit-bg5y4t` | 10–11 | 6.936–8.131 | 2/3 (`ahead>10`, `loc>5000`) |

Integrate qua nhánh trung gian `integration/v4-1-price-history-foundation`
(cắt từ default tip `7e60978`), merge `--no-ff` candidate `aaceb883` — **0
conflict**. Merge nhánh trung gian vào default bằng `--ff-only` tại
`abddbe0c8f02330617917516957a26596b8d2dd9`. Không squash, không rebase,
không rewrite history, không force push. Validator chạy đủ trước và sau —
0 regression (đúng 3 lỗi tiền tồn `TASK-REM-T06`, xác nhận không đổi so
với chính default tip cũ).

**KNOWN DIVERGENCE = CLOSED.** Không grandfather thành permanent exception.
`branch_authority_check.sh` sau push: `DIVERGENCE = WITHIN_LIMITS`.

- 2026-08-28 — `TASK-105B` **FREEZE FINALIZATION** (`DEC-153`, phiên "TASK-105B
  — FREEZE + CONTROLLED INTEGRATION"). `FROZEN = YES` tại implementation SHA
  `c22cef8b47ac4cd71ef49609066a362c9e604313`, tham chiếu reconciliation SHA
  `95a7ae6c3c694a7095ecb2adc6041785c3960096`. Verdict reconciled `PASS —
  ELIGIBLE_FOR_FREEZE`, 0 BLOCKING, 17/17 REQUIRED Completion Gate PASS (E1
  tối thiểu, CHECK-105B-12 tại E2). Freeze **không** re-review technical
  correctness — chỉ niêm phong verdict đã có, đúng State Authority Matrix
  (`governance/core/V4_1_POLICY_FREEZE.md` §12). `repair_cycles_used` vẫn
  `0`, `remaining` vẫn `2` — **freeze không tiêu cycle** (không phải repair,
  hai Independent Review PASS song song + reconciliation không phải remediation).
  `HB-105B-07`/`HB-105B-08` re-trigger condition giữ nguyên nội dung, không
  downgrade, không xoá — bắt buộc resolve trước `TASK-105C` implementation
  hoặc trước `FilePriceProvider` activation thật, tuỳ điều kiện nào tới
  trước. `app/**`, `tests/**`, `config/**` **không đổi một byte** qua phiên
  Freeze này.

- 2026-08-28 — `TASK-105B` **CONTROLLED INTEGRATION** (cùng phiên trên).
  Divergence trước integration: ahead=7 commit, LOC=3294, 0 ngày —
  `WITHIN_LIMITS` (`branch_authority_check.sh`, dưới ngưỡng V4.1 §8).
  Qua nhánh trung gian `integration/v4-1-task-105b-price-provider` (cắt từ
  default tip `c49cb67`), merge `--no-ff` `review/task-105b-independent-review-1`
  — **0 conflict** (merge-base = default tip cũ, review branch vốn đã là
  fast-forward-able descendant thuần). Merge nhánh trung gian vào nhánh mặc
  định bằng `--ff-only`. Post-integration validation trên nhánh trung gian:
  production content byte-identical với reviewed SHA `c22cef8`; 4 file
  production lõi diff = 0; `PendingPriceProvider` vẫn default; 0 caller
  `FilePriceProvider` ngoài module/test; 0 code `TASK-105C`; targeted `33
  passed`; Golden `58 passed, 2 skipped`; full `pytest -q` `730 passed, 11
  skipped` (0 regression); 4 validator PASS; `validate_reference_integrity`
  đúng 3 lỗi tiền tồn `TASK-REM-T06`; `git diff --check` sạch; worktree
  CLEAN. `repair_cycles_used` vẫn `0`, `remaining` vẫn `2` — integration
  không tiêu cycle. `TASK-105B = FROZEN + INTEGRATED`, **VẪN CHƯA `DONE`**
  (Exit Criteria còn thiếu: bảng giá production thật nạp được — data
  dependency đang mở). `HB-105B-07`/`HB-105B-08` re-trigger giữ nguyên,
  chưa resolve — bắt buộc trước `TASK-105C` implementation hoặc trước
  `FilePriceProvider` activation thật.

- 2026-08-28 — `TASK-105B` **REPAIR CYCLE #1** (phiên "TASK-105B
  PRICE-PARSER MICRO-HARDENING", nhánh `task/task-105b-price-parser-hardening`,
  cắt từ default tip `89948df42b510e27b80a9a7902e3c07d4a7066e7`). Sửa đúng
  `HB-105B-07` (NaN → `decimal.InvalidOperation` thô) và `HB-105B-08`
  (`Infinity`/`-Infinity` không bị chặn đúng cách) — đúng RE-TRIGGER
  CONDITION đã ghi tại `DEC-153`, không phải phản ứng với Independent
  Review FAIL. Đường thẩm quyền dùng: **repair cycle mới có thẩm quyền
  riêng** (không phải `COMPLETION GATE CHANGE PROPOSAL` — 17 check REQUIRED
  của Completion Gate giữ nguyên nội dung, không sửa). Thay đổi mã nguồn
  duy nhất: một check `price.is_finite()` chèn vào `_parse_price()`
  (`app/modules/pricing/file_price_provider.py`), giữa check
  `missing_price` và `negative_price`, raise
  `InvalidPriceMasterError(reason="non_finite_price")`. 26 test hồi quy mới
  tại `tests/test_file_price_provider.py`. Chi tiết + toàn bộ evidence:
  commit `7f7048d65619c2c2198c99ccbfb073d6cb97ebe2`,
  `docs/tasks/TASK-105B-file-price-provider.md`.

  ```
  Targeted : 33 → 59 passed (+26 test mới)
  Golden   : 58 passed, 2 skipped (không đổi)
  Full     : 730 → 756 passed, 11 skipped (chênh lệch = đúng 26 test mới,
             0 regression, 0 skip mới)
  4 file production lõi diff : 0
  PendingPriceProvider vẫn default; 0 caller FilePriceProvider ngoài
  module/test; 0 code TASK-105C được thêm.
  ```

  `repair_cycles_used: 0 → 1`, `repair_cycles_remaining: 2 → 1`. Cycle
  ghi tại mục "Root Task: TASK-105B" → `cycles:` (`id: TASK-105B-RC-1`,
  `base_sha: c22cef8b47ac4cd71ef49609066a362c9e604313`,
  `head_sha: 7f7048d65619c2c2198c99ccbfb073d6cb97ebe2`). **`status:
  READY_FOR_REVIEW`** — Independent Review độc lập vẫn BẮT BUỘC (Effective
  Risk = HIGH) trước khi cycle này được ghi `CLOSED_BY_REPAIR,
  INDEPENDENTLY_VERIFIED`; phiên này không tự cấp verdict đó cho chính
  mình. `TASK-105B` vẫn `FROZEN + INTEGRATED`, vẫn `NOT DONE` (data
  dependency bảng giá thật vẫn mở, không đổi bởi phiên này). `TASK-105C`
  **KHÔNG** được bắt đầu trong phiên này — `HB-105B-07`/`HB-105B-08` được
  báo cáo là *code-level resolved*, nhưng prerequisite đầy đủ cho
  `TASK-105C` vẫn chờ Independent Review của chính cycle này, cộng
  product identity mapping (dependency riêng, chưa mở task). `TASK-110`,
  `TASK-GOLDEN-BASELINE-001` **không đổi**. `HB-105B-03`, `HB-105B-05`,
  `HB-105B-06`, `HB-105B-10` **không đổi**, không được sửa trong phiên
  này (đúng phạm vi khoá của brief).

- 2026-08-28 — `DEC-154` **PRODUCT IDENTITY & PURCHASE PRICE RESOLUTION**.
  Governance/spec reconciliation only: tạo `TASK-105D` spec/lineage,
  reconcile `TASK-105B` thành Public Purchase branch và `TASK-105C` thành
  Tracking HistoricalVendorMin branch, không sửa/activate code. `TASK-105B`
  budget **không đổi** `2/1/1`; không mở RC-2. Lineage mới `TASK-105D` được
  cấp theo bảng HIGH `2/0/2`, chưa dùng cycle nào. Golden/Tracking không đổi.

- 2026-08-28 — `DEC-155` **TASK-105D READINESS — DATA CONTRACT, PERSISTENCE &
  AUDIT DESIGN** (S034). Readiness/design documentation only: tạo
  `docs/spec/TASK-105D-DATA-CONTRACT.md`, chốt unified
  `PublicPurchaseSourceVersion` (HB-154-02), Tracking read-only capture
  contract, `HistoricalConfirmedRegistry` bypass rule (HB-154-03),
  `CrossSystemProductMapping` precondition cho Public Purchase fallback
  (HB-154-01), persistence/concurrency/idempotency/audit/migration contract,
  và định nghĩa vận hành cho `CHECK-105D-06/13/23/24` (HB-154-05). Sửa
  transcription `P00`/`P03`/`P11` và hai canonical documentation correction
  (HB-154-06, HB-154-07).

  ```
  app/** tests/** config/** tools/** scripts/** governance/** : 0 file thay đổi
  Golden        : 58 passed, 2 skipped (không đổi)
  Full suite    : 756 passed, 11 skipped (không đổi)
  Repair Cycle  : KHÔNG mở
  TASK-105D budget : 2 allowed / 0 used / 2 remaining  (KHÔNG ĐỔI)
  TASK-105B budget : 2 allowed / 1 used / 1 remaining  (KHÔNG ĐỔI)
  TASK-110, TASK-GOLDEN-BASELINE-001, TASK-108B budget : KHÔNG ĐỔI
  ```

  `HB-105B-03/05/06/10` **không** bị trigger bởi phiên này (không dataset
  thật nào được nạp, không code/test/tool nào được thêm); thiết kế mới định vị
  chính xác điểm trigger là lần đầu một `PublicPurchaseSourceVersion` thật
  được nạp qua `FilePriceProvider`. `HB-154-04` (review-budget lineage của
  `TASK-105C`) **KHÔNG được tự sửa** — ghi `OWNER DECISION REQUIRED` kèm ba
  phương án và khuyến nghị tại `DEC-155` §6, theo đúng V4.1 §2/§12.

- 2026-08-28 — `DEC-156` **OWNER RATIFICATION — TASK-105D READINESS;
  TASK-105C LINEAGE RECONCILIATION; TASK-105E AUTHORIZATION** (S035).
  Owner Decision recording, documentation-only.

  ```
  OR-01  APPROVED                              (unified Public Purchase source)
  OR-02  APPROVED WITH CANDIDATE-ONLY POLICY   (ALIAS_AID_UNIQUE = candidate #1,
                                                KHÔNG auto-resolve)
  OR-03  APPROVED FOR PHASE 1                  (actor khai báo, REQUIRED,
                                                cấm gọi là authenticated)
  HB-154-04  CLOSED — Owner Option B
  TASK-105E  Owner cấp task ID (Price Resolution Composition)
  ```

  Tác động ngân sách:

  ```
  TASK-105B : 2 allowed / 1 used / 1 remaining   KHÔNG ĐỔI
              TASK-105B-RC-1 vẫn CONSUMED, không chuyển, không xoá
  TASK-105C : lineage ROOT MỚI — 2 allowed / 0 used / 2 remaining
              (tách theo kiến trúc, KHÔNG phải reset ngân sách đã tiêu)
  TASK-105D : 2 allowed / 0 used / 2 remaining   KHÔNG ĐỔI
  TASK-105E : lineage MỚI — 2 allowed / 0 used / 2 remaining
  TASK-110, TASK-GOLDEN-BASELINE-001, TASK-108B : KHÔNG ĐỔI
  Repair Cycle : KHÔNG mở
  ```

  ```
  app/** tests/** config/** tools/** scripts/** governance/** : 0 file thay đổi
  Golden     : 58 passed, 2 skipped (không đổi)
  Full suite : 756 passed, 11 skipped (không đổi)
  ```

  `TASK-105D` Ready Gate blocker: 2 → **1** (chỉ còn Completion Gate freeze).
  `TASK-105C` trạng thái task **KHÔNG đổi** — vẫn `BLOCKED / NOT AUTHORIZED`.
  `HB-105B-03/05/06/10` không finding nào bị trigger bởi phiên này.
