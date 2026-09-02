# RÀ SOÁT ĐỘC LẬP E2 (E2 INDEPENDENT REVIEW) — TASK-PRA-002 SLICE C1

Review ID:
PRA-002-SLICE-C1-REVIEW-1

Task / Release:
TASK-PRA-002 — slice C1 (`result_fingerprint` + `RESULT_REVISED` trên
persistence hiện có, không migration)

Reviewer Session:
S087 — Independent Review Slice C1 (nhánh `claude/pra-002-slice-c-plan-jg798m`)

Executed By:
S087 — PRA-002 Slice C1 Independent Review (2026-09-02)

Timestamp:
2026-09-02

Evidence Level:
E2 (mọi kết luận chức năng đều có lệnh đã chạy + output trên PostgreSQL 16.13
thật; phần chỉ đọc mã được ghi rõ là suy luận tĩnh)

## Scope

Chỉ vertical của slice C1: cùng nguồn → evidence/kết quả đổi → result version
mới → `RESULT_REVISED` → source version giữ nguyên → current result dịch →
history giữ nguyên. KHÔNG Real Data Acceptance, KHÔNG C2/C3, KHÔNG production
deploy/acceptance, KHÔNG `make_snapshot_variants`, KHÔNG migration, KHÔNG
architecture redesign, KHÔNG Tracking, KHÔNG PRA-003/004/005, KHÔNG A2/A3,
KHÔNG B2/B3/B4, KHÔNG REM-T06, KHÔNG PostgreSQL Phase D, KHÔNG hạ tầng, KHÔNG
refactor suy đoán.

Lineage đã xác minh TRƯỚC khi đọc bất kỳ dòng mã nào:

```text
REVIEW_BASE_SHA = bfe7008f7dfd42c90465f6d32ca38b4c2dfeaf82   (== origin/claude/extract-upload-repo-gq2ws4 — canonical CHƯA dịch chuyển)
REVIEW_HEAD_SHA = 3cd92eae3035dd40aaf3f64bd3ba96a1d1b49cd0   (== origin/claude/pra-002-slice-c-plan-jg798m)
BASE là tổ tiên của HEAD  : ĐÚNG (git merge-base --is-ancestor → 0)
Working tree lúc mở phiên : sạch
branch_authority_check.sh : AUTHORITY_OK (BRANCH_WITH_UPSTREAM, ahead default 1, DIVERGENCE WITHIN_LIMITS)
Commit trong khoảng       : 1 (3cd92ea "TASK-PRA-002 slice C1: RESULT_REVISED trên persistence hiện có")
Diff review               : 10 file, +878 / −23   (production: 4 file, +126 / −6 thô)
```

Không `CANONICAL_MOVED`, không `REVIEW_LINEAGE_INVALID`.

## Tài Liệu Đầu Vào Đã Đọc (Inputs Read)

`docs/tasks/TASK-PRA-002-pipeline-persistence-reconciliation.md` (frozen
contract — mục 5.2/5.3, mục 6 result-version contract, mục 8 bước 0–5 + bước R,
sơ đồ schema mục 12, CHECK-PRA002-08), `PROJECT/PROJECT_PROGRESS.md`,
`PROJECT/REVIEW_BUDGET_LEDGER.md`, `docs/reviews/TASK-PRA-002-SLICE-A-INDEPENDENT-REVIEW-RECORD.md`,
`docs/reviews/TASK-PRA-002-SLICE-B-INDEPENDENT-REVIEW-RECORD.md`,
`docs/sessions/S086-pra-002-slice-c1-result-revised.md`,
`governance/core/V4_1_POLICY_FREEZE.md` (§2 review budget, §3 repair cycle,
§4 blast radius), `docs/adr/ADR-108`, DEC-166, DEC-171,
`tools/db/schema.py`, `tools/db/migrations/versions/0002_snapshots.py`.

Phân loại thẩm quyền của các mệnh đề quyết định kết luận phiên này:

| Mệnh đề | Loại |
|---|---|
| `from_version_id` = "source hoặc result version cũ (theo kind)" (task mục 12) | **FACT** (frozen contract, văn bản tường minh) |
| `RESULT_REVISED` ⟺ đã có current result ∧ source version không đổi ∧ fingerprint khác (task mục 6) | **FACT** (frozen contract) |
| Bước 3 ghi result version cho mọi khoá "trừ COLLISION" (task mục 8) | **FACT** (frozen contract) |
| F3 = đúng `status`, `accounting_purchase_price`, `eligible_kpi_profit` (task mục 6 + mục 12) | **FACT** (frozen contract) |
| Cycle tính theo LẦN SỬA (V4.1 §3) | **FACT** (policy freeze) |
| `repair_cycles_used: 0` trong khối máy đọc của ledger | **DEFECT bookkeeping** (mâu thuẫn nội bộ — xem `FIND-PRA002-C1-N1`) |
| "Schema không có FK nên DB cho phép" | **INFERENCE** — KHÔNG dùng làm thẩm quyền nghiệp vụ |

## Xác Minh Độc Lập (Independent Verification)

Reviewer dựng cluster PostgreSQL 16.13 THẬT (`initdb` + `pg_ctl`, cổng 5433) và
chạy lại vertical bằng chính đường sản xuất (`SnapshotRepository.write_snapshot`),
không dùng lại test của người triển khai. Script kiểm chứng nằm ngoài repo
(scratchpad phiên) — chúng là dụng cụ review, không phải sản phẩm bàn giao.

## Điểm Review #1 (BẮT BUỘC ĐẦU TIÊN) — VERSION-ID SEMANTICS

Câu hỏi: `from_version_id`/`to_version_id` của cờ `RESULT_REVISED` được frozen
contract định nghĩa là **generic version reference** hay **source-version
reference**?

Trả lời bằng văn bản thẩm quyền, KHÔNG bằng "schema không có FK". Frozen
contract, `docs/tasks/TASK-PRA-002-pipeline-persistence-reconciliation.md`
mục 12, khối `reconciliation_flag`:

```text
from_version_id        INTEGER NULL           -- source hoặc result version cũ (theo kind)
to_version_id          INTEGER NULL
```

Đây là **phương án A — generic version references, ngữ nghĩa do `kind` quyết
định**, và nó tường minh trong chính hợp đồng đã freeze. Cùng dòng
`detail_json` xác nhận cùng một thiết kế: "changed_fields / **(old,new) của 3
trường result** / khoảng ngày lệch (COLLISION)" — một cột, ba ngữ nghĩa, phân
biệt bằng `kind`. Việc cột không có FOREIGN KEY là **hệ quả** của thiết kế đó,
không phải lý lẽ biện minh cho nó.

→ **PASS.** Không phải BLOCKING. Implementation dùng result-version id cho
`RESULT_REVISED` là ĐÚNG hợp đồng, không phải "DB cho phép nên làm". Không
redesign schema, không thêm FK, không thêm cột.

Bằng chứng thực thi cho thấy vì sao câu hỏi này đáng hỏi — hai trục dùng chung
không gian số nguyên, và chỉ `kind` phân biệt được:

```text
flags: [('ORDER_KEY_COLLISION', 1, 2), ('SOURCE_CHANGED', 1, 3), ('RESULT_REVISED', 2, 3)]
       source-version id space: [1, 2, 3]   result-version id space: [1, 2, 3]
```

Kiểm tra máy trên vertical hai lần capture: mọi đầu version của
`RESULT_REVISED` đều nằm trong tập id của `order_line_result_version` →
`True`. Không có trộn ngữ nghĩa.

## FROZEN RESULT_REVISED CONTRACT — đối chiếu từng vế

| Vế hợp đồng (mục 6 / mục 8 bước 3) | Mã hiện thực | Kết luận |
|---|---|---|
| đã có current result | `state is None or state.result_fingerprint is None` → bỏ qua | PASS |
| source outcome = SAME | `unchanged_source = {d.line.key for d in decisions if d.outcome == OUTCOME_SAME}` | PASS |
| source version không đổi | `SAME` là nhánh DUY NHẤT không ghi source version (mục 8 bước 2) → tương đương | PASS |
| fingerprint mới ≠ current | `state.result_fingerprint == result.result_fingerprint` → bỏ qua | PASS |
| SOURCE_CHANGED precedence | `SOURCE_CHANGED` không thuộc tập `SAME` → loại theo cấu trúc | PASS |
| COLLISION không RESULT_REVISED | `COLLISION` không thuộc tập `SAME`; và mục 8 bước 3 loại khỏi result version | PASS |
| F3 đúng 3 trường, không thêm | `RESULT_FIELDS` + `result_fingerprint()` cùng 3 tham số | PASS |

`INSERT` không sinh cờ vì khoá chưa có current (`current.get(...) is None`) —
đúng "đây là lần đầu, không phải sửa".

## F3 FINGERPRINT

`app/history/keys.py::result_fingerprint` băm đúng ba giá trị `canon(status)`,
`canon(accounting_purchase_price)`, `canon(eligible_kpi_profit)` — không hơn.
`RESULT_FIELDS` mới khai đúng ba tên đó, đúng thứ tự tham số, và
`ResultLine.result_values` trả đúng thứ tự ấy. Ba nơi không thể nói về hai tập
trường khác nhau.

Chuẩn hoá Decimal — kiểm chứng ở mức DATABASE, không chỉ ở mức hàm. RUN-B lưu
`5000000.00`, RUN-C lưu `5000000`; hai hàng có **cùng** `result_fingerprint`,
và RUN-C sinh `n_result_revised = 0`:

```text
result versions for BH1:
   (1, 'RUN-A', 'PENDING', Decimal('5000000'),    Decimal('0'),       'ef2347aa…')
   (3, 'RUN-B', 'AUTO',    Decimal('5000000.00'), Decimal('3000000'), '5dfee927…')
   (5, 'RUN-C', 'AUTO',    Decimal('5000000'),    Decimal('3000000'), '5dfee927…')
```

Trường ngoài F3 không ảnh hưởng: đổi `price_source`
`TRACKING_PRICE_HISTORY` → `FILE_PRICE_LIST` trên cùng khoá →
`n_result_revised = 0`, `result_versions = 2`, `flags = 0`. Đúng mục 6 ("vẫn
được lưu đầy đủ ở version mới, chỉ không sinh cờ").

## CHANGED_FIELDS COMPATIBILITY

`changed_fields(before, after)` → `changed_fields(before, after, fields=FINGERPRINT_FIELDS)`.
Tham số mới có **giá trị mặc định đúng bằng tập cũ**, đặt cuối, keyword được.
Điểm gọi đường nguồn (`app/history/reconciler.py:85`) KHÔNG truyền `fields` →
vẫn dùng `FINGERPRINT_FIELDS` nguyên vẹn: không bỏ trường nguồn, không thêm
trường result, không đổi thứ tự, không đổi ngữ nghĩa `canon`. Chỉ có một điểm
gọi mới (đường result) truyền `fields=RESULT_FIELDS`. Regression
`SOURCE_CHANGED` chạy lại: PASS (xem TESTS_RUN).

## CURRENTSTATE EXTENSION + JOIN

Ba trường mới (`result_version_id`, `result_fingerprint`, `result_values`) đều
`Optional[...] = None`, đặt sau các trường sẵn có → tương thích ngược với mọi
điểm dựng `CurrentState` cũ.

Join nạp từ **current result version**, không phải result lịch sử bất kỳ:

```python
.join(order_line_result_version,
      order_line_result_version.c.id == order_line_current.c.current_result_version_id)
```

Rủi ro đã cân nhắc: đây là INNER JOIN thêm vào truy vấn nạp hiện trạng — nếu
`current_result_version_id` có thể NULL thì khoá đó sẽ bị **rơi khỏi**
`current` và bị phân loại nhầm thành `INSERT`. Đã bác bỏ bằng schema:
`Column("current_result_version_id", Integer, ForeignKey(...), nullable=False)`
— NOT NULL + FK, nên tập hàng trả về không đổi. Không phải finding.

Không nhầm trục: `current_source_version_id` vẫn join sang
`order_line_source_version` như cũ, và `max_version_no` (repair
`FIND-PRA002-A1`) vẫn nạp riêng, không bị đụng.

## CURRENT POINTER INVARIANT — vertical hai lần capture (PostgreSQL 16.13)

Cùng bytes workbook (`file_fingerprint = fp-a`), hai khoá; capture A cho BH1
`PENDING`, capture B cho BH1 `AUTO` + `eligible_kpi_profit` mới:

```text
snapshot counters:
   ('SNAP-20260106000000-fp-a', 'RUN-A', n_insert=2, n_same=0, n_source_changed=0, n_collision=0, n_result_revised=0)
   ('SNAP-20260107000000-fp-a', 'RUN-B', n_insert=0, n_same=2, n_source_changed=0, n_collision=0, n_result_revised=1)
   ('SNAP-20260108000000-fp-a', 'RUN-C', n_insert=0, n_same=2, n_source_changed=0, n_collision=0, n_result_revised=0)
source_version count: 2          source_version max version_no: 1
result_version count: 6
flags: ('RESULT_REVISED', 'BH1', from=1, to=3,
        '{"eligible_kpi_profit": {"new": "3000000", "old": "0"}, "status": {"new": "AUTO", "old": "PENDING"}}')
current pointers: ('BH1', source=1, result=5)   ('BH2', source=2, result=6)
```

- `source_changed = 0`, `source_version count = 2`, `max version_no = 1` →
  **trục nguồn không đổi**.
- `result_version count = 6` = 2 khoá × 3 run → **mỗi run thêm một quan sát
  kết quả**.
- `current_result` BH1: `1` (RUN-A) → `3` (RUN-B) → `5` (RUN-C) → **con trỏ
  kết quả dịch**; `current_source` BH1 giữ `1`.
- Version cũ `1` và `3` vẫn còn nguyên trong bảng sau RUN-C → **history bất
  biến, không UPDATE, không DELETE**.

Đây là `RESULT_REVISED`, KHÔNG bị biến thành `SOURCE_CHANGED`, và current/history
không sai.

## SAME WITHOUT REVISION (tương thích slice A)

RUN-C: cùng nguồn, cùng F3 → `n_result_revised = 0`, 0 cờ, NHƯNG vẫn ghi result
version mới (`count` 4 → 6). Không có tối ưu "bỏ quan sát kết quả". Đúng mục 6
("kể cả dòng `SAME` … không 'copy' result cũ").

## SOURCE_CHANGED PRECEDENCE

Nguồn đổi (`sell_price` 8000000 → 9999000) VÀ F3 đổi (`PENDING`→`AUTO`,
LN 0 → 3000000) trong cùng một run:

```text
counters (R2): n_same=0, n_source_changed=1, n_result_revised=0
flags: [('SOURCE_CHANGED',)]
```

Chỉ `SOURCE_CHANGED`, 0 `RESULT_REVISED`. Điều này đến từ **cấu trúc** —
`result_revisions()` chỉ xét tập `OUTCOME_SAME`, nên khoá `SOURCE_CHANGED`
không thể lọt vào — chứ không phải do fixture tình cờ. Đột biến M1 dưới đây
chứng minh chiều ngược lại.

## COLLISION

Khoá `BH9` tái xuất hiện lệch `COLLISION_DAY_THRESHOLD + 1` ngày:

```text
counters (C2): n_collision=1, n_result_revised=0
flags: [('ORDER_KEY_COLLISION',)]
result_version rows: [('C1',)]        ← KHÔNG có hàng nào của run C2
pointers before: [(1, 1)]  after: [(1, 1)]   ← cả hai con trỏ nguyên vẹn
```

Không current mới, không result version, không `RESULT_REVISED`, con trỏ cũ
nguyên. Đúng mục 8 bước 2 + bước 3.

Bất biến repair `FIND-PRA002-A1` vẫn giữ SAU khi C1 thêm join mới vào
`_load_current` — upload tiếp trên khoá đã collision KHÔNG vi phạm UNIQUE:

```text
version_no series: [(1,1), (2,2), (3,3)]
counters: A(insert 1) · B(collision 1) · C(source_changed 1) · D(same 1, result_revised 1)
flags: ('ORDER_KEY_COLLISION',1,2) · ('SOURCE_CHANGED',1,3) · ('RESULT_REVISED',2,3)
current: (source=3, result=3, order_key_collision=True)
```

## FLAG PROVENANCE

`kind = RESULT_REVISED`; `raised_by_snapshot_id` = snapshot của run hiện tại;
`run_id` = run hiện tại; `acknowledged_at = None` (append-only, đúng mục 12).
`detail_json` chỉ chứa trường F3 **thực sự đổi** — trong vertical trên,
`accounting_purchase_price` bị bỏ ra vì `canon` bằng nhau, chỉ còn `status` và
`eligible_kpi_profit`. `old`/`new` là dạng `canon`, xác định, không phụ thuộc
thứ tự dict (`sort_keys=True`). **Không PII**: ba trường F3 không phải
`customer` / `phone` / `address` / `note_raw`; test
`test_no_pra002_table_declares_a_customer_column` vẫn PASS.

`from_version_id`/`to_version_id` = result version cũ/mới, đúng kết luận Điểm
Review #1.

## n_result_revised

Đếm theo **khoá logic**, không theo số version, số trường, hay số cờ lịch sử.
Một khoá đổi CẢ BA trường F3 trong một run:

```text
n_result_revised = 1        flag rows = 1
detail: {"accounting_purchase_price": {...}, "eligible_kpi_profit": {...}, "status": {...}}
```

`len(revisions)` với `revisions` sinh đúng một phần tử cho mỗi khoá (lặp trên
`result_lines`, mỗi khoá đúng một `ResultLine` do UNIQUE `(run_id, khoá)`).

## TRANSACTION

Không tạo transaction mới. `revisions` được tính TRONG `with self._engine.begin()`,
và bốn nhóm ghi (`source_snapshot` kèm counter → source/result versions →
`RESULT_REVISED` flags → con trỏ current) nằm trong CÙNG một
`connection`/transaction đã có từ slice A.

Thứ tự đúng và có ý nghĩa: `result_revisions()` chạy **trước**
`_update_current`, vì sau khi con trỏ dịch thì kết quả cũ không còn so sánh
được. Đột biến M3 xác nhận đây không phải sự tình cờ.

Ép lỗi giữa chừng (`on_persisted` ném exception sau khi mọi bản ghi đã vào
transaction):

```text
raised: Boom
snapshots:      1 -> 1
result_versions: 1 -> 1
RESULT_REVISED flags after rollback: 0
pointer: [(1,)] -> [(1,)]
```

Rollback toàn bộ — không có partial `RESULT_REVISED` state.

## TWO-CAPTURE VERTICAL QUA ĐƯỜNG WEB

Ngoài vertical repository ở trên, test mới
`test_the_snapshot_page_shows_a_result_revised_flag_after_a_second_capture`
đi qua đúng route `/run` hai lần với **cùng bytes workbook** (cùng
`file_fingerprint`), lần hai trả `PresentedLine` đã giải `PENDING → AUTO`.
Reviewer đã chạy lại: PASS, `n_source_changed == 0`, `n_result_revised == 1`.
Đây giải thích vì sao diff KHÔNG có thay đổi template: trang snapshot render
`kind`/cặp version/`detail_json` một cách tổng quát.

**Đây là test evidence (synthetic + integration), KHÔNG phải Real Data
Acceptance.** RDA vẫn `NOT_TESTED` và vẫn thuộc Owner.

## SLICE B REGRESSION

`app/history/coverage.py`, `app/history/extraction.py`, `app/web/history_writer.py`,
`app/web/server.py` — **UNCHANGED** trong `BASE..HEAD`. Coverage / xác nhận đủ /
`NOT_SEEN` / `REMOVED_CANDIDATE` / `is_active` không bị chạm.

Không giao nhau giữa cờ khoá-có-mặt và cờ khoá-vắng-mặt, theo cấu trúc:
`result_revisions()` chỉ lặp trên `result_lines` (khoá CÓ MẶT trong snapshot
mới), còn `_insert_absence_flags` chỉ chạy trên tập `absent` từ
`_absent_keys_in_range` (khoá VẮNG MẶT). Hai tập rời nhau theo định nghĩa.

## DATABASE / MIGRATION

```text
git diff --name-only BASE..HEAD | grep -E "schema|migrat"   → NONE
```

Không migration, không schema change. `0002_snapshots` vẫn là head
(`down_revision = "0001_legacy"`; không có `0003`). Cả `n_result_revised` lẫn
`RESULT_REVISED` trong `FLAG_KINDS` **đã có sẵn ở BASE** — xác minh bằng
`git show bfe7008:tools/db/schema.py`. C1 chỉ điền vào chỗ schema đã chừa sẵn.

## TESTS_RUN

Reviewer tự chạy, không dùng lại output của người triển khai:

```text
Full suite                                        1806 passed, 11 skipped  (66.01s)
Golden (-k golden)                                  81 passed,  2 skipped
C1 focused (reconciler + snapshot_repo + web)       83 passed
Slice A/B persistence (vertical + absence + db + keys)  97 passed
PRA-001 (legacy importer/repository/coverage/routes)   101 passed
PostgreSQL 16.13 thật — vertical A+B+C1 do reviewer viết   PASS (mọi mệnh đề ở trên)
```

Test KHÔNG bị làm yếu hay xoá: `test_history_reconciler.py` 13 → 24,
`test_snapshot_repository.py` 22 → 32, `test_web_history.py` 23 → 24 hàm test
(+22). Toàn bộ dòng bị xoá trong `tests/` là **mở rộng chữ ký helper** có giá
trị mặc định giữ nguyên hành vi cũ (`result_line(..., price_source=…)`,
`write(..., results=None, evidence=None)`), không có assertion nào bị gỡ hay
nới.

## MUTATION QUALITY

Reviewer không dựng mutation framework; thay vào đó áp bốn đột biến NGỮ NGHĨA
vào production và chạy lại đúng ba file test C1/A/B (83 test):

| # | Đột biến | Kết quả |
|---|---|---|
| M1 | Bỏ điều kiện `SAME` (phân loại trên mọi decision) | **4 failed** |
| M2 | Dùng `FINGERPRINT_FIELDS` thay `RESULT_FIELDS` khi diff | **8 failed** |
| M3 | Tính `result_revisions` SAU `_update_current` | **6 failed** |
| M4 | Trỏ `to_version_id` vào SOURCE version thay vì result | **1 failed** |

Cả bốn đều bị bắt → test khẳng định **bất biến nghiệp vụ** (nguồn không đổi /
kết quả đổi / con trỏ / cờ / đếm / precedence), không chỉ khẳng định hiện thực.
M4 chỉ bị một test bắt — đó là mắt lưới mỏng nhất, nhưng vẫn có phủ, và ngữ
nghĩa của nó đã được thẩm quyền frozen chốt ở Điểm Review #1. Cây làm việc đã
khôi phục đúng `3cd92ea` sau khi đo.

## LOC BUDGET

Đo lại độc lập bằng cùng phương pháp đã hiệu chuẩn (dòng thêm/bớt trong `app/`,
loại dòng trắng, dòng `#`, và docstring), khớp **từng file** với S086:

```text
app/history/keys.py                4   2   +2
app/history/models.py             12   0  +12
app/history/reconciler.py         23   2  +21
app/web/history_store.py          34   2  +32
                                 ---  --  ---
ACTUAL_C1_PRODUCTION_LOC          73   6  +67

67 <= 107  → KHÔNG vi phạm budget
CUMULATIVE = 1.393 (A+B) + 67 = 1.460 / 1.500
REMAINING_TO_HARD_STOP = 40 LOC
```

Không refactor để giảm số dòng, không minify, không gộp dòng, không bỏ
validation. Con số rơi giữa LOW 55 / EXPECTED 73 của planning.

## Findings

### FIND-PRA002-C1-N1 — NON_BLOCKING (governance bookkeeping) — ĐÃ SỬA TRONG PHIÊN

`PROJECT/REVIEW_BUDGET_LEDGER.md` mâu thuẫn với chính nó cho lineage
`TASK-PRA-002`: khối máy đọc ghi `repair_cycles_used: 0` /
`repair_cycles_remaining: 2`, trong khi prose khối S084 ghi "lineage vẫn 1/2"
và danh sách `cycles:` có đúng một mục `PRA-002-RC-1`.

Đã truy thẩm quyền, không suy diễn. Ba nguồn cùng chỉ một hướng:

1. `governance/core/V4_1_POLICY_FREEZE.md` §3 — "Cycle được tính theo **LẦN
   SỬA**, không theo số review", và bắt buộc ledger ghi `cycles:` với
   `base_sha`/`head_sha`. `PRA-002-RC-1` có đủ cả hai
   (`80c6fe1d…` → `b0ecab78…`) cho một finding BLOCKING (`FIND-PRA002-A1`) đã
   sửa trong Independent Review slice A. Theo định nghĩa đã freeze, đó **là**
   một repair cycle đã tiêu.
2. Danh sách `cycles:` của chính lineage này có ĐÚNG một mục.
3. Prose trong cùng file (khối S084) ghi "lineage vẫn 1/2".

Quy ước xác nhận bằng lineage so sánh được: `TASK-GOLDEN-BASELINE-001` có một
mục `cycles:` và khối máy đọc ghi `repair_cycles_used: 1` /
`repair_cycles_remaining: 1`.

→ Khối máy đọc là **defect bookkeeping**, không phải nguồn sự thật. Hệ quả
nghiệp vụ: KHÔNG có (không chạm production path). Hệ quả governance: một phiên
sau có thể tin nhầm còn 2 cycle và tiêu quá ngân sách đã freeze.

**Sửa đã áp dụng** (docs-only, đúng mục 23 chỉ thị review slice C1):
`repair_cycles_used: 0 → 1`, `repair_cycles_remaining: 2 → 1`, kèm ghi chú
đính chính nêu đủ thẩm quyền. **KHÔNG tiêu repair cycle cho bookkeeping.**

### BLOCKING findings

**0.** Không có finding nào hội đủ ba điều kiện (production path + business
consequence + valid evidence). Điểm Review #1 — nghi vấn nghiêm trọng nhất khi
mở phiên — được frozen contract giải quyết tường minh theo hướng PASS.

Đã cân nhắc và BÁC BỎ (ghi lại để phiên sau không phải đi lại):

- *INNER JOIN mới trong `_load_current` có thể làm rơi khoá* → bác bỏ:
  `current_result_version_id` là `nullable=False` + FK.
- *`state.result_fingerprint is None` là nhánh chết* → đúng là phòng thủ thừa
  trên schema hiện tại, nhưng vô hại và không phải defect production.
- *`detail_json` có thể rỗng khi fingerprint khác* → không thể: fingerprint
  được tính từ đúng ba giá trị mà `canon` cũng đọc.

## Repair / Bổ Sung Đã Áp Dụng Trong Phiên

Chỉ một, docs-only, không chạm `app/` hay `tools/`:

- `PROJECT/REVIEW_BUDGET_LEDGER.md` — sửa khối máy đọc lineage `TASK-PRA-002`
  thành `used: 1` / `remaining: 1`, thêm ghi chú đính chính và mục Independent
  Review E2 slice C1.
- `PROJECT/PROJECT_PROGRESS.md` — cập nhật trạng thái hiện hành.
- `docs/reviews/TASK-PRA-002-SLICE-C1-INDEPENDENT-REVIEW-RECORD.md` — file này.

Production diff `BASE..HEAD` KHÔNG bị sửa bởi phiên review. `REPAIR_CYCLES
TIÊU THỤ TRONG PHIÊN NÀY = 0`.

## DEFERRED

Giữ nguyên, không mở lại trong phiên này: `FIND-PRA002-B2` (nhân đôi cờ khi hai
lần xác nhận ĐỒNG THỜI → PRA-004), `FIND-PRA002-B3` (`FLAG_PAGE_LIMIT = 200`
→ PRA-004), `FIND-PRA002-B4` (CSRF — baseline có sẵn, Cloudflare Access là
front door), A2/A3. `CHECK-PRA002-14` (RDA) và `CHECK-PRA002-15` (Production
Acceptance) vẫn `NOT_TESTED` — thuộc Owner, ngoài scope C1.

## Kết Luận (Conclusion)

```text
REVIEW_RESULT        = PASS
FINAL_ACCEPTANCE     = ACCEPT
INTEGRATION_READY    = YES
BLOCKING_FINDINGS    = 0
REPAIR_CYCLES_USED_THIS_SESSION = 0
CHECK-PRA002-08      = PASS (E2 — reviewer tái lập trên PostgreSQL 16.13 thật)
NEXT_VERTICAL_ACTION = Controlled integration Slice C1
```

`TASK-PRA-002` vẫn `IN_PROGRESS` — KHÔNG đánh DONE (RDA + Production Acceptance
+ C2/C3 chưa xong). KHÔNG bắt đầu RDA/C2.
