# S086 — TASK-PRA-002 Slice C1: RESULT_REVISED (MAJOR)

Ngày: 2026-09-02
Task Mode: MAJOR
Task: `TASK-PRA-002` — slice C1 (`result_fingerprint` + `RESULT_REVISED` +
test hai capture)
Kết quả: **SLICE_C1_RESULT = PASS**

## 1. Base và nhánh

```text
CANONICAL              = claude/extract-upload-repo-gq2ws4  (HEAD branch của origin)
EXPECTED_BASE_SHA      = bfe7008f7dfd42c90465f6d32ca38b4c2dfeaf82
REMOTE_CANONICAL_SHA   = bfe7008f7dfd42c90465f6d32ca38b4c2dfeaf82   → KHỚP, canonical KHÔNG dịch chuyển
BRANCH                 = claude/pra-002-slice-c-plan-jg798m
```

Nhánh planning đứng đúng tại canonical SHA (0 ahead / 0 behind tại lúc mở
phiên), nên phát triển trên nó **là** phát triển từ exact canonical — không có
docs commit nào ngoài canonical để loại trừ. `scripts/branch_authority_check.sh`
→ `AUTHORITY_OK`, `WORKTREE: CLEAN`.

## 2. Hợp đồng đã hiện thực

`RESULT_REVISED` phát sinh khi và chỉ khi giao của bốn điều kiện:

1. khoá đã có `current_result_version`;
2. nguồn KHÔNG đổi ở lần chạy này (`SAME` — đúng là điều kiện
   `source_version_id` mới `== current_source_version_id`, vì `SAME` là nhánh
   duy nhất không ghi source version mới);
3. khoá không `ORDER_KEY_COLLISION`;
4. `result_fingerprint` khác.

`result_fingerprint = sha256(status, accounting_purchase_price,
eligible_kpi_profit)` — đúng ba trường F3, không thêm. `SOURCE_CHANGED` thắng;
`COLLISION` không sinh cờ.

## 3. Đường code đã đụng (minimum touch)

```text
app/history/keys.py         +2   RESULT_FIELDS; changed_fields nhận tham số `fields`
app/history/models.py      +12   FLAG_RESULT_REVISED; ResultLine.result_values;
                                 CurrentState.{result_version_id,result_fingerprint,result_values};
                                 dataclass ResultRevision
app/history/reconciler.py  +21   result_revisions() — hàm THUẦN phân loại
app/web/history_store.py   +32   _load_current join current result version;
                                 write_snapshot tính revisions 1 lần + n_result_revised;
                                 _insert_flags ghi cờ cấp KẾT QUẢ
```

KHÔNG sửa `_insert_result_versions`, KHÔNG sửa `_update_current`, KHÔNG
migration, KHÔNG schema change, KHÔNG template. Template `snapshot.html` render
`kind`, cặp version và `detail_json` một cách tổng quát — đã chứng minh bằng
test web thật, không phải bằng đọc code.

## 4. Bằng chứng (E1/E2)

### 4.1 Con trỏ hiện hành — PostgreSQL 16.13 THẬT

```text
--- RUN 1 — capture A (BH1 PENDING) ---
source_version COUNT = 2
result_version COUNT = 2
  BH1: current_source_version_id=1  current_result_version_id=1
  BH2: current_source_version_id=2  current_result_version_id=2

--- RUN 2 — capture B, cùng sổ, BH1 PENDING -> AUTO ---
source_version COUNT = 2
result_version COUNT = 4
  BH1: current_source_version_id=1  current_result_version_id=3
  BH2: current_source_version_id=2  current_result_version_id=4
  FLAG RESULT_REVISED BH1 from=1 to=3 detail={"status": {"new": "AUTO", "old": "PENDING"}}
  SNAP SNAP-20260202000000-fp-book n_same=2 n_source_changed=0 n_result_revised=1

=== INVARIANT ===
  BH1: source 1 -> 1 (GIỮ NGUYÊN); result 1 -> 3 (ĐỔI)
  BH2: source 2 -> 2 (GIỮ NGUYÊN); result 2 -> 4 (ĐỔI)
  Result version cũ id=1 status=PENDING — VẪN TỒN TẠI NGUYÊN VẸN
```

### 4.2 CHECK-PRA002-08 — nguyên văn yêu cầu

```text
  n_source_changed (run 2)       = 0   (yêu cầu 0)
  COUNT(version_no > 1)          = 0   (yêu cầu 0)
  cờ RESULT_REVISED              = 1   (đúng số dòng đổi)
  detail_json chỉ 3 trường F3    = {"status": {"new": "AUTO", "old": "PENDING"}}
  RUN 3 (kết quả y hệt run 2): result_version COUNT = 6 (vẫn +2/run),
                               tổng cờ RESULT_REVISED = 1 (KHÔNG thêm cờ)
```

`from_version_id`/`to_version_id` trỏ vào `order_line_result_version`, không
phải source version. Schema hiện tại cho phép: hai cột đó **không có FOREIGN
KEY** — kiểm trên schema đã migrate thật:

```text
reconciliation_flag_raised_by_snapshot_id_fkey|FOREIGN KEY (raised_by_snapshot_id) REFERENCES source_snapshot(snapshot_id)
(không có FK nào khác)
ck_reconciliation_flag_kind: CHECK (kind = ANY (ARRAY[... 'RESULT_REVISED' ...]))
```

### 4.3 Test

```text
full suite            : 1806 passed, 11 skipped   (BASE bfe7008: 1784 passed, 11 skipped → +22 test, 0 skip thêm)
Golden Baseline       : 58 passed, 2 skipped      (KHÔNG đổi)
PRA-001 focused       : 81 passed
C1 unit (thuần)       : 11 test mới trong tests/test_history_reconciler.py
C1 persistence        : 10 test mới trong tests/test_snapshot_repository.py
C1 web (hai capture)  : 1 test mới trong tests/test_web_history.py
PostgreSQL 16.13 THẬT : alembic upgrade head → 0002_snapshots; 113 passed
                        (snapshot_repository + absence + coverage_confirmation + vertical + history_db)
```

**Mutation check.** Hoàn nguyên riêng `app/` về BASE và giữ nguyên test: 6 test
mới FAIL (5 persistence + 1 web), các test khẳng định "0 cờ" vẫn PASS như phải
thế. Test mới thật sự đo hành vi mới, không phải khẳng định rỗng.

### 4.4 Transaction

Phát hiện + ghi result version + cờ + con trỏ + counter nằm trong đúng
`engine.begin()` đã có. Test `test_a_failure_after_detection_leaves_no_partial_result_revision`
ép `on_persisted` ném lỗi sau khi mọi bản ghi đã vào transaction: snapshot,
result version, cờ và con trỏ đều quay về nguyên trạng.

## 5. CHANGE_BUDGET

Phương pháp đo **hiệu chuẩn lại từ đầu** trong phiên này (script không được
commit — nó là dụng cụ đo, không phải production code): đếm dòng `+`/`−` trong
`git diff -U0`, loại dòng trống, dòng comment và mọi dòng docstring xác định
bằng AST trên đúng bản BASE/HEAD của từng file; tập file = **`.py` production
dưới `app/` và `tools/`** (không tính test, không tính template).

Hiệu chuẩn — tái lập đúng cả ba con số đã được chấp nhận:

```text
SLICE A   7fad3f7..27b9d1c   1137   33   +1104   ✓ khớp 1.104 đã chấp nhận
SLICE B   27b9d1c..7658c5e    297    8    +289   ✓ khớp 289, khớp cả 5 dòng per-file của S084
LINEAGE   7fad3f7..7658c5e   1426   33   +1393   ✓ khớp PRA002_USED_BEFORE_C1
```

Đo slice C1:

```text
app/history/keys.py            4    2    +2
app/history/models.py         12    0   +12
app/history/reconciler.py     23    2   +21
app/web/history_store.py      34    2   +32
                            ----  ---  -----
ACTUAL_C1_PRODUCTION_LOC      73    6   +67

CUMULATIVE = 7fad3f7..HEAD = 1493 / 33 / +1460   (= 1.393 + 67, khớp hai chiều)
REMAINING_TO_HARD_STOP = 1.500 − 1.460 = 40 LOC
```

`67 <= 107` → **CONTINUE**, không cần `CHANGE_BUDGET_REQUIRED`. Con số rơi
đúng giữa LOW 55 / EXPECTED 73 của planning, và không có dòng nào bị gộp,
minify hay bỏ validation để đạt số.

## 6. REVIEW_BUDGET_STATUS = UNKNOWN_CONFLICT

`PROJECT/REVIEW_BUDGET_LEDGER.md` mâu thuẫn với chính nó cho lineage
`TASK-PRA-002`:

```text
khối máy đọc (đầu mục root task) : repair_cycles_used: 0   /  remaining 2
khối trạng thái S085 (cùng file) : "repair cycle đã dùng : 1 / 2 (còn 1)"
danh sách cycles (cùng file)     : PRA-002-RC-1 — FIND-PRA002-A1 (BLOCKING), đã dùng
```

Phiên C1 **không sửa** governance (không cần thiết cho implementation, và sửa
sai hướng sẽ tiêu oan một cycle). Independent Review C1 phải xác minh trước khi
tiêu bất kỳ repair cycle mới nào.

## 7. Findings

Không có finding BLOCKING (production path + business consequence + evidence).

**FIND-PRA002-C1-N1 — NON_BLOCKING (governance, không phải production).**
Khối máy đọc `repair_cycles_used: 0` của lineage `TASK-PRA-002` mâu thuẫn với
phần prose và danh sách `cycles:` trong cùng file. Hệ quả nghiệp vụ: không có.
Hệ quả governance: một phiên sau có thể tin nhầm là còn 2 cycle. Đề xuất: sửa
khối máy đọc thành `1`/`remaining 1` sau khi Independent Review xác minh.

## 8. Trạng thái sau phiên

```text
Slice A       = INTEGRATED
Slice B       = INTEGRATED
Slice C / C1  = IMPLEMENTED, chờ Independent Review E2   (KHÔNG đánh DONE)
TASK-PRA-002  = IN_PROGRESS
CHECK-PRA002-08 = PASS (E1; bằng chứng persistence + PostgreSQL 16.13 thật đạt mức E2)
CHECK-PRA002-14 = NOT_TESTED (RDA — Owner)
CHECK-PRA002-15 = NOT_TESTED (Production Acceptance — Owner)
```

## 9. Việc KHÔNG làm (đúng Scope Lock)

Không RDA, không production deploy, không C2/C3, không snapshot-variant
tooling, không migration/schema change, không Tracking, không refactor, không
A2/A3/B2/B3/B4, không PRA-003/004/005, không REM-T06, không PostgreSQL Phase D.

## 10. NEXT_VERTICAL_ACTION

**Independent Review E2 Slice C1.** KHÔNG bắt đầu RDA/C2.
