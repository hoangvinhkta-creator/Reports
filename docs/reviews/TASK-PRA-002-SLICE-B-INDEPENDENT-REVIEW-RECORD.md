# RÀ SOÁT ĐỘC LẬP E2 (E2 INDEPENDENT REVIEW) — TASK-PRA-002 SLICE B

Review ID:
PRA-002-SLICE-B-REVIEW-1

Task / Release:
TASK-PRA-002 — slice B (coverage semantics: `HEADER_CONSISTENT` / xác nhận đủ /
`NOT_SEEN_IN_LATEST_SNAPSHOT` / `REMOVED_IN_SOURCE_CANDIDATE`)

Reviewer Session:
S084 — Independent Review Slice B (nhánh `claude/pra-002-slice-b-snapshot-8rbwip`)

Executed By:
S084 — PRA-002 Slice B Independent Review (2026-09-02)

Timestamp:
2026-09-02

Evidence Level:
E2 (mọi kết luận chức năng đều có lệnh đã chạy + output; phần chỉ đọc mã được
ghi rõ là suy luận tĩnh)

## Scope

Chỉ vertical của slice B: snapshot → coverage detection → xác nhận tường minh →
so sánh vắng mặt → `NOT_SEEN_IN_LATEST_SNAPSHOT` → `REMOVED_IN_SOURCE_CANDIDATE`
→ current/totals vẫn an toàn. KHÔNG review slice C (`RESULT_REVISED`, Real Data
Acceptance, Production Acceptance), KHÔNG mở cancellation semantics, KHÔNG mở
REMOVED resolution / acknowledgement / undo confirmation, KHÔNG chạm PRA-003/004/005,
Tracking, REM-T06, PostgreSQL Phase D, hạ tầng, hay refactor suy đoán.

Lineage đã xác minh TRƯỚC khi đọc bất kỳ dòng mã nào:

```text
REVIEW_BASE_SHA = 27b9d1c5a578742450099c53f2f82411f07aa9dc   (== origin/claude/extract-upload-repo-gq2ws4 — canonical CHƯA dịch chuyển)
REVIEW_HEAD_SHA = 7658c5e5341935c7e3ff4edf31505b8a1d205e85   (== origin/claude/pra-002-slice-b-snapshot-8rbwip)
BASE là tổ tiên của HEAD  : ĐÚNG (git merge-base --is-ancestor → 0)
Working tree lúc mở phiên : sạch
Commit trong khoảng       : 1 (7658c5e "TASK-PRA-002 slice B — coverage semantics + NOT_SEEN/REMOVED_CANDIDATE")
Diff review               : 16 file, +2.254 / −44
branch_authority_check.sh : AUTHORITY_OK (BRANCH_WITH_UPSTREAM, WORKTREE CLEAN, DIVERGENCE WITHIN_LIMITS)
```

## Tài Liệu Đầu Vào Đã Đọc (Inputs Read)

- `docs/tasks/TASK-PRA-002-pipeline-persistence-reconciliation.md` **tại BASE**
  (bản FROZEN — dùng làm authority nghiệp vụ, không dùng implementation):
  mục 3 (Owner Business Contract), 5, 6, 7 (coverage contract + 7.3 UX xác nhận),
  8 (state machine — đặc biệt **bước 4** và **bước R**), 9, 10, 11, 12, 13, 17, 18, 20.
- `docs/sessions/S083-pra-002-slice-b-coverage-semantics.md` (evidence của người triển khai).
- `docs/reviews/TASK-PRA-002-SLICE-A-INDEPENDENT-REVIEW-RECORD.md`,
  `docs/sessions/S079-pra-002-roadmap-finalization.md`,
  `docs/sessions/S080-pra-002-slice-a-implementation.md`.
- `docs/adr/ADR-108-persistent-history-store.md`; DEC-166, DEC-171.
- `PROJECT/PROJECT_PROGRESS.md`, `PROJECT/REVIEW_BUDGET_LEDGER.md`.

## Xác Minh Độc Lập (Independent Verification)

Mọi con số dưới đây do phiên review tự chạy, không lấy lại từ S083.

```text
Full suite (SQLite)          : 1781 passed, 11 skipped        (trước khi review thêm test)
Full suite (sau khi thêm 3 test rollback) : 1784 passed, 11 skipped
Golden Baseline              : 74 passed, 2 skipped  (2 skip = thiếu workbook thô GOLDEN_RAW_01/06 — môi trường, đã có ở BASE)
Slice B focused              : 76 passed  (absence + coverage_confirmation + web_history)
Slice A focused              : 96 passed  (snapshot_repository + pipeline_vertical + reconciler + keys)
PRA-001 / legacy focused     : 115 passed (history_db + legacy_importer + legacy_repository + legacy_source_coverage + web_legacy_routes)

PostgreSQL 16.13 THẬT (cluster cục bộ, initdb + pg_ctl, socket riêng):
  alembic upgrade head       : → 0002_snapshots   (11 bảng; source_snapshot có đủ
                               confirmed_range_start/end (date), confirmed_at, confirmed_by,
                               n_not_seen, n_removed_candidate (not null default 0),
                               CHECK coverage_state 3 giá trị)
  vertical slice B + A       : 113 passed in 35.66s
                               (test_history_coverage_confirmation 31, test_snapshot_absence 24,
                                test_snapshot_repository 22, test_pipeline_history_vertical 12,
                                test_web_history 24)
  bằng chứng bảng thật sau kịch bản rộng:
     source_snapshot: 2 dòng — HEADER_CONSISTENT và CONFIRMED_COMPLETE 2026-01-01→2026-01-31,
                      n_removed_candidate = 262
     reconciliation_flag: REMOVED_IN_SOURCE_CANDIDATE = 262, không cờ nào khác
```

Ghi chú trung thực: cluster PostgreSQL tạm bị hệ điều hành thu hồi quyền thư mục
giữa chừng một lần (PANIC `pg_control: Permission denied`); cluster đã được dựng
lại ở đường dẫn ổn định và TOÀN BỘ số liệu PostgreSQL ở trên là của lần chạy sau
khi dựng lại, trên server khoẻ. Không có con số nào lấy từ lần chạy hỏng.

## Truy Nguyên Thẩm Quyền — Điểm Review #1: RANGE SEMANTICS

Kết luận: **implementation ĐÚNG frozen contract. KHÔNG sửa.**

Frozen `TASK-PRA-002` mục 8 nói nguyên văn (bản tại BASE):

```text
Bước 4  NOT_SEEN: với mỗi khoá c ∈ CUR có sale_date ∈ DETECTED(S_new) và c ∉ S_new và không COLLISION
Bước R  (chỉ khi 7.3 xác nhận CONFIRMED_COMPLETE cho snapshot S):
        với mỗi khoá c ∈ CUR có sale_date ∈ [confirmed_start, confirmed_end] và c ∉ snapshot_line(S) ...
```

Phân loại: đây là **OWNER_DECISION** (bảng contract mục 3.2 + mục 8, Owner chấp
nhận nguyên văn tại S079), không phải INFERENCE của người triển khai.

Đối chiếu ba kịch bản trong chỉ thị review, đo trên mã và trên test thật:

| Kịch bản (B = 01–31/01 trước, A = 01–10/01 sau) | Frozen contract | Implementation | Kết luận |
|---|---|---|---|
| A chưa confirmed | khoá 11–31 có `sale_date ∉ DETECTED(A) = [01,10]` → KHÔNG NOT_SEEN | không dựng (`detected[0], detected[1]` là phạm vi truyền vào `absent_keys`) | KHỚP |
| A confirmed đúng 01–10 | khoá 11–31 `∉ [confirmed_start, confirmed_end]` → KHÔNG REMOVED | không dựng | KHỚP |
| A confirmed 01–31 | khoá 11–31 ∈ khoảng đã xác nhận và ∉ membership(A) → REMOVED_CANDIDATE | dựng 262 cờ (đo trên PostgreSQL thật) | KHỚP |

Câu trong chỉ thị phiên trước ("B→A unconfirmed → later-period keys NOT_SEEN")
KHÔNG được dùng để override frozen contract, và chính chỉ thị review này nói vậy.
Nguyên tắc nền cũng đứng về phía implementation: một sổ 01–10 không có thẩm quyền
phát biểu về 11–31, nên tạo `NOT_SEEN` ngoài phạm vi sẽ là **absence giả**.
Không có mâu thuẫn business semantics nào cần `OWNER_DECISION_REQUIRED`.

## Điểm Review #2 — CONFIRMED_COMPLETE Authority

Đọc trên mã production (không chỉ trên test):

- `app/history/coverage.py::coverage_state` chỉ trả `DETECTED_ONLY` hoặc
  `HEADER_CONSISTENT` — không nhánh nào trả `CONFIRMED_COMPLETE` (FACT, đọc mã).
- Toàn bộ `app/**` chỉ có MỘT nơi gán `coverage_state=CONFIRMED_COMPLETE`:
  `app/web/history_store.py::SnapshotRepository.confirm_coverage` (đã grep toàn repo;
  test tĩnh AST `test_confirmed_complete_is_written_by_exactly_one_function` khoá lại).
- `confirm_coverage` chỉ ghi khi `confirmation_error(...) is None`, mà hàm đó
  fail-closed ở mọi nhánh: chưa tick → từ chối; ngày không parse → từ chối;
  `start > end` → từ chối; khoảng > 366 ngày → từ chối; DETECTED ⊄ khoảng khai báo
  → từ chối kèm ngày lệch; snapshot không có ngày bán → từ chối.
- Không có đường nào từ header, tên file, khoảng đo được, cuối tháng, số dòng,
  lịch, importer hay repository inference tạo ra trạng thái này.
- Route `POST /du-lieu/snapshot/<id>/xac-nhan-du` truyền `confirmed=request.form.get("xac_nhan") == "1"`;
  template render checkbox **không** có thuộc tính `checked` → mặc định chưa tick.
- Ô xác nhận hiển thị đúng phạm vi đang xác nhận (`tu_ngay`/`den_ngay` mặc định =
  DETECTED, và trang in "Phạm vi hệ thống phát hiện: min → max").
- Provenance được ghi: `confirmed_range_start/end`, `confirmed_at`, và mỗi cờ mang
  `raised_by_snapshot_id`, `run_id`, `from_version_id`, `detail_json = {scope, range_start, range_end}`.
- Idempotency: lần xác nhận thứ hai → `CoverageAlreadyConfirmedError` → HTTP 409,
  **không cờ nào bị nhân đôi** (test đo số dòng `reconciliation_flag` trước/sau).
- Test tĩnh AST `test_only_the_confirmation_function_updates_the_snapshot_row`
  chứng minh chỉ `confirm_coverage` được `update(source_snapshot)` và chỉ đúng 5 cột
  `{coverage_state, confirmed_range_start, confirmed_range_end, confirmed_at, n_removed_candidate}`
  — `confirmed_by` KHÔNG nằm trong tập ghi (đúng D4: để NULL khi chưa có danh tính app-level).

## HEADER_CONSISTENT ≠ CONFIRMED_COMPLETE

`HEADER_CONSISTENT` chỉ là bằng chứng kỹ thuật "header bao trọn khoảng đo được".
Hai dạng header được chấp nhận đúng như mục 3.5/7.1 (`Từ ngày … đến ngày …` và
`Nhân viên: …, Tháng M năm YYYY`); dạng thứ ba → `None` → `DETECTED_ONLY`, header
gốc vẫn lưu nguyên văn. Không có generic parser, không nới regex. Header hẹp hơn
dữ liệu rơi về `DETECTED_ONLY` (cảnh báo, không nâng cấp). Không đường nào từ
header sang `CONFIRMED_COMPLETE`.

## Absence Set Logic

`app/history/reconciler.py::absent_keys` là phép toán tập hợp **thuần** (không
import database), loại trừ đúng bốn nhóm: khoá có trong snapshot mới;
`sale_date is None`; ngày ngoài `[start, end]`; `order_key_collision`. Phạm vi mở
(`None`) trả rỗng — "không có phạm vi thì không có thẩm quyền", chứ không phải
"vắng mặt tất cả".

Bất biến quan trọng nhất của mục 7 chỉ thị đã được xác minh trực tiếp:
**bước R dùng `snapshot_line` membership của CHÍNH snapshot đang xác nhận**, không
dùng `last_seen`. Đọc mã: `confirm_coverage` build `present` từ
`select(snapshot_line…).where(snapshot_line.c.snapshot_id == snapshot_id)`.
Test bẫy `test_confirmation_uses_this_snapshots_membership_not_the_latest_state`
(xác nhận sổ hẹp SAU khi sổ rộng đã ghi đè `last_seen`) PASS trên cả SQLite và
PostgreSQL 16.13.

## NOT_SEEN / REMOVED_CANDIDATE / CURRENT / TOTALS

Hệ quả duy nhất của cả hai loại cờ là **một dòng INSERT vào `reconciliation_flag`**:
`_insert_absence_flags` không chạm `order_line_current`, không tạo source version,
không tạo result version, không delete, không cancel, không resolve.
`current_totals()` KHÔNG đổi một dòng nào trong diff và join
`order_line_current → order_line_result_version`, hoàn toàn không tham chiếu bảng cờ —
nên `COUNT`, `SUM(total_sales)` và `current_fingerprints` không thể phụ thuộc vào cờ
ở tầng truy vấn, chứ không chỉ ở tầng test. Đã đo trên PostgreSQL thật: sau khi dựng
262 cờ `REMOVED_IN_SOURCE_CANDIDATE`, `order_line_current` và tổng tiền không đổi.

Đường cho PRA-003 rõ ràng và đã có sẵn: `current_totals(date_from, date_to)` +
`current_fingerprints(date_from, date_to)` đọc thẳng trạng thái hiện hành theo kỳ,
không cộng dồn history và không trừ cờ. (Không implement PRA-003 ở đây.)

## Reappearance / `is_active`

Bản ghi cờ BẤT BIẾN (append-only; `acknowledged_at` luôn NULL). "Còn hiệu lực"
được DẪN XUẤT lúc đọc trong `_with_absence_state` bằng cách hỏi snapshot mới nhất
từng chứa khoá đó. So sánh **NGẶT** trên `created_at`; hai snapshot cùng một giây →
giữ cờ ACTIVE. Reviewer xác nhận hướng fail-safe là đúng: một cảnh báo thừa được
ưu tiên hơn việc âm thầm giấu một sự vắng mặt thật, và không con số nghiệp vụ nào
phụ thuộc nhãn này. Việc S083 bỏ tie-break theo `snapshot_id` là đúng — `snapshot_id`
sắp theo fingerprint, không theo thời gian. Không xây event-sequencing subsystem;
same-second ordering chỉ tạo warning thừa → **DEFER**.

Cờ không nói về sự vắng mặt (`SOURCE_CHANGED`, `ORDER_KEY_COLLISION`) mang
`is_active = None` — không gắn nhãn giả.

## Transaction Safety

`confirm_coverage` chạy nâng coverage + bước R trong MỘT `engine.begin()`.
Chỉ thị mục 13 yêu cầu có test rollback; **local test còn thiếu** → phiên review
bổ sung (xem "Repair/Bổ sung"). Sau khi bổ sung, hai trạng thái nửa vời bị cấm đều
được chứng minh bằng cách ép hỏng từng nửa, và cả hai assert đều đã được
mutation-check (làm hỏng production tạm thời → test ĐỎ đúng như mong đợi).

## Web Input

`POST /du-lieu/snapshot/<snapshot_id>/xac-nhan-du`: `snapshot_id` chỉ đi vào truy
vấn tham số hoá (không nối chuỗi); snapshot không tồn tại → `KeyError` → 404;
ngày không parse được → 400 (không đoán định dạng); `start > end` → 400;
khoảng > 366 ngày → 400; thiếu checkbox → 400; xác nhận lần hai → 409;
history store chưa cấu hình → 503. Mọi nhánh từ chối KHÔNG ghi gì (đã test).
`confirmed_by = NULL` — hợp lệ theo kiến trúc hiện tại (D4). Cloudflare Access vẫn
là front door; không mở lại thiết kế auth.

## Coverage Label — FIND-PRA002-A4

Đã đóng thật. `COVERAGE_LABELS` cho ba nhãn khác nhau đôi một, lấy từ
`coverage_state` đã lưu; template in `{{ coverage_label }}` thay cho câu cố định
"CHƯA XÁC NHẬN ĐỦ" của slice A, và khi `CONFIRMED_COMPLETE` còn in đúng khoảng đã
xác nhận + thời điểm + câu "Ngoài khoảng đó, snapshot này KHÔNG nói gì". Trạng thái
lạ → "Không rõ trạng thái coverage" (không im lặng). Không redesign UI.

## Database / Migration

S083 KHÔNG tạo migration mới và KHÔNG sửa `tools/db/**` (đã xác minh: diff của
`tools/db/schema.py` trong khoảng BASE..HEAD là RỖNG). Schema `0002_snapshots`
thật sự đã đủ cho slice B — xác minh bằng `alembic upgrade head` trên PostgreSQL
16.13 thật rồi `\d source_snapshot`: đủ `confirmed_range_start/end` (date),
`confirmed_at`, `confirmed_by`, `n_not_seen`, `n_removed_candidate`, CHECK
`coverage_state` ba giá trị, `FLAG_KINDS` đã chứa `NOT_SEEN_IN_LATEST_SNAPSHOT`
và `REMOVED_IN_SOURCE_CANDIDATE`, và `ix_order_line_current_sale_date` phục vụ
đúng phép lọc theo ngày của bước 4/R. Không sửa 0002, không tạo 0003.

## Slice A Regression

Chạy lại trên cả SQLite và PostgreSQL 16.13, tất cả PASS:

- A→A không double count (`test_uploading_the_same_book_again_adds_no_version_and_no_money`,
  `test_uploading_the_same_book_twice_never_moves_a_single_dong`).
- A→B đẳng thức `state(A rồi B) == state(B một mình)` — CHECK-PRA002-04
  (`test_a_half_month_book_then_the_full_month_equals_the_full_month_alone`), và
  chiều ngược lại (`test_the_wide_book_first_then_the_narrow_one_adds_nothing_and_changes_nothing`).
- `SOURCE_CHANGED` giữ version cũ đọc được (`test_an_edited_line_keeps_the_old_version_readable_and_moves_current`).
- `ORDER_KEY_COLLISION` giữ nguyên current (`test_a_colliding_key_is_stored_flagged_and_left_out_of_the_current_state`).
- Upload tiếp sau collision KHÔNG lỗi UNIQUE — bất biến của repair `b0ecab7`
  (`test_uploading_again_after_a_collision_still_works`).

Slice B không phá slice A. Ràng buộc append-only còn **chặt hơn** sau slice B nhờ
hai test AST hẹp mới.

## Sai Lệch So Với Tuyên Bố Của Người Triển Khai (Mismatches With Implementer Claims)

Một sai lệch, đã đo lại độc lập — xem FIND-PRA002-B1.

Mọi tuyên bố kỹ thuật khác của S083 đều tái lập được: full suite 1781/11, Golden
58 passed 2 skipped (trong lần chạy Golden riêng của review là 74 passed 2 skipped
vì gồm cả ba file golden BH), 262 REMOVED trong kịch bản xác nhận cả tháng,
không migration mới, `TRACKING_CHANGED = NO`, `git diff --check` sạch.

## Findings

### FIND-PRA002-B1 — NON_BLOCKING (đã sửa số liệu trong phiên này)

**CHANGE_BUDGET của slice B bị báo thiếu 47 dòng; headroom trước dừng cứng bị báo
thừa 47 dòng.**

S083 báo `242` dòng logic production cho slice B và `1.104 + 242 = 1.346` cho
lineage, còn `154` dòng trước dừng cứng `1.500`.

Reviewer đo lại độc lập bằng script riêng (đếm dòng `+`/`−` trong
`git diff -U0`, loại dòng trống, dòng comment, và mọi dòng thuộc docstring xác
định bằng AST trên đúng bản `HEAD`/`BASE` của từng file). Phương pháp này được
**hiệu chuẩn** bằng cách đo lại slice A trên khoảng `7fad3f7..27b9d1c`: kết quả
`net +1104`, **trùng khít** con số 1.104 mà slice A đã được chấp nhận — nên đây
là đúng phương pháp của dự án, không phải một thước đo khác.

```text
                            thêm   xoá    net
app/history/coverage.py       49     0     +49    (S083 báo 45)
app/history/models.py          8     0      +8    (S083 báo  4)
app/history/reconciler.py     23     3     +20    (S083 báo 22)
app/web/history_store.py     179     3    +176    (S083 báo 142)
app/web/server.py             38     2     +36    (S083 báo 29)
                            ----  ----   -----
SLICE B                      297     8    +289    (S083 báo 242)
SLICE A (hiệu chuẩn)        1137    33   +1104    (khớp con số đã chấp nhận)
LINEAGE 7fad3f7..7658c5e    1426    33   +1393    (S083 báo 1.346)
```

Hệ quả nghiệp vụ: không có (không đường production nào sai). Hệ quả governance:
**có** — phiên slice C sẽ lập kế hoạch dựa trên headroom sai. Số đúng:

```text
CHANGE_BUDGET slice B  = 289 / mục tiêu slice ≤ 500  → ĐẠT (cảnh báo 600, dừng cứng 800 không chạm)
CHANGE_BUDGET lineage  = 1.393 / mục tiêu 1.200 / dừng cứng 1.500
REMAINING_TO_HARD_STOP = 107 dòng   (KHÔNG phải 154)
```

Đây KHÔNG phải blocker của slice B: vẫn dưới dừng cứng. Reviewer **không** tăng
budget và **không** refactor để giảm LOC. Chỉ sửa con số trong
`PROJECT/REVIEW_BUDGET_LEDGER.md` và `PROJECT/PROJECT_PROGRESS.md` (bản ghi live),
giữ nguyên `docs/sessions/S083-*.md` như bản ghi lịch sử của phiên đó.

### FIND-PRA002-B2 — NON_BLOCKING → DEFER

**Hai lần `POST xac-nhan-du` ĐỒNG THỜI trên cùng snapshot có thể nhân đôi cờ
`REMOVED_IN_SOURCE_CANDIDATE`.**

Đường tuần tự đã đúng (lần hai → 409, không cờ nào nhân đôi — có test). Nhưng
`confirm_coverage` đọc `coverage_state` bằng `SELECT` không khoá, nên dưới
READ COMMITTED hai transaction song song có thể cùng qua cửa, cùng INSERT cờ, rồi
lần lượt UPDATE (giá trị như nhau). Không có UNIQUE constraint trên
`reconciliation_flag` chặn trùng.

Hệ quả: dòng cảnh báo bị lặp trong danh sách Review. KHÔNG có hệ quả nghiệp vụ:
không xoá, không đổi current, không đổi `n_removed_candidate`, không đổi tổng tiền,
`coverage_state` vẫn idempotent. Theo chính sách finding (mục 20 của chỉ thị) đây
là "rare fail-safe warning" — **không tiêu repair cycle**.

Re-trigger: quan sát thấy cờ vắng mặt trùng trên production, hoặc khi PRA-004 dựng
workflow acknowledge (lúc đó cần khoá hàng bằng `UPDATE … WHERE coverage_state <> 'CONFIRMED_COMPLETE'`
có kiểm `rowcount`, portable cho cả SQLite lẫn PostgreSQL).

### FIND-PRA002-B3 — NON_BLOCKING → DEFER

**Trang snapshot liệt kê tối đa `FLAG_PAGE_LIMIT = 200` cờ, trong khi tiêu đề in
`{{ flags|length }}`.**

Slice B là thay đổi đầu tiên khiến việc chạm trần này thành hiện thực (kịch bản đã
đo dựng 262 cờ). Khi đó ô "Ứng viên đã xoá khỏi nguồn" in đúng 262 nhưng tiêu đề
khối cờ in 200 — hai con số trên cùng một trang không khớp và không có câu giải
thích rằng danh sách đã bị cắt.

`FLAG_PAGE_LIMIT` là hành vi có từ slice A và đã được chấp nhận ở review slice A;
sửa nó ở đây là redesign UI (mục 15 của chỉ thị cấm) và là mở lại một quyết định
slice A đã chấp nhận. Không có con số nghiệp vụ nào sai — số lượng thật vẫn hiển
thị đúng trên cùng trang. **DEFER sang PRA-004 (Review Ops UI, phân trang cờ +
acknowledge)**; ghi ở đây để Owner biết trước khi có snapshot production đầu tiên
vượt 200 cờ.

### FIND-PRA002-B4 — NON_BLOCKING → DEFER (đã biết, không phải hồi quy)

Không route POST nào của app có CSRF token (`/run`, `/feedback`, hai route legacy
của PRA-001, và nay `xac-nhan-du`). Đây là baseline kiến trúc có sẵn với
Cloudflare Access làm front door; chỉ thị review cấm mở lại thiết kế auth và cấm
thêm hệ thống danh tính. Ghi nhận để không bị coi là đã bỏ sót; **không** phải
điều slice B mang vào.

### Đã kiểm và KHÔNG phải finding

- `absent_keys` lọc theo ngày trong SQL trước khi đưa vào hàm thuần: SQL chỉ **thu
  hẹp** đầu vào, luật vắng mặt vẫn nằm ở tầng thuần → ranh giới ADR-101 giữ nguyên
  (`app/history/**` vẫn không import sqlalchemy/psycopg/alembic/flask).
- Bước 4 tính `absent` TRƯỚC khi ghi snapshot/versions/current của chính lần chạy
  đó — đúng, vì mọi khoá của snapshot mới đều nằm trong `present` nên không thể
  bị coi là vắng mặt.
- Khoá được thêm bởi một snapshot MỚI HƠN rồi bị bước R của một snapshot CŨ HƠN
  gắn cờ: đúng contract (người dùng khẳng định sổ cũ đầy đủ cho khoảng đó), và
  dẫn xuất `is_active` tự đánh dấu cờ đó là "đã xuất hiện lại" → không gây hiểu nhầm.
- Upload lại cùng file dựng cờ `NOT_SEEN` mới: đúng append-only contract (mỗi
  snapshot là một sự kiện thật, cờ gắn `raised_by_snapshot_id` riêng); trang chi
  tiết lọc theo snapshot nên không có trùng lặp trong cùng một khung nhìn.
- Không PII: `detail_json` của cờ vắng mặt chỉ chứa `{scope, range_start, range_end}`.
- Bộ nhớ: bước 4/R chỉ nạp `order_line_current` trong đúng khoảng ngày (có index),
  tỉ lệ với kỳ chứ không với toàn bộ lịch sử.

## Repair / Bổ Sung Đã Áp Dụng Trong Phiên

**KHÔNG tiêu repair cycle** (không có finding BLOCKING). Hai việc đã làm:

1. **Bổ sung test rollback cho đường xác nhận** — được mục 13 của chỉ thị cho phép
   tường minh ("Test rollback nếu chưa có… thêm trong review session").
   `tests/test_snapshot_absence.py` +87 dòng, 3 test mới:
   - `test_a_database_failure_midway_leaves_neither_half_of_the_confirmation`
     (parametrize 2 nửa: ép hỏng `update(source_snapshot)`, và ép hỏng
     `insert(reconciliation_flag)`) — sau lỗi: `coverage_state` chưa CONFIRMED,
     `confirmed_range_start`/`confirmed_at` NULL, `n_removed_candidate = 0`,
     số cờ không đổi, và toàn bộ `state()` (tổng tiền, fingerprint, source version,
     current, result version, membership) trở về đúng như trước.
   - `test_the_confirmation_can_still_be_made_after_a_failed_attempt` — rollback
     không để lại snapshot "kẹt".
   Chỉ sửa file test; KHÔNG sửa một dòng production nào.

   Mutation check (chứng minh test có tải trọng, không phải test trang trí):
   - gỡ bước R khỏi `confirm_coverage` → 6 test ĐỎ, gồm 2 test mới;
   - đưa bước R sang một transaction riêng đã commit →
     `…[update-table0]` ĐỎ với `assert 2 == 1` (cờ sống sót qua rollback).
   Khôi phục production nguyên trạng sau mỗi lần mutation (`git diff` rỗng).

2. **Sửa số liệu CHANGE_BUDGET** trong `PROJECT/REVIEW_BUDGET_LEDGER.md` và
   `PROJECT/PROJECT_PROGRESS.md` theo FIND-PRA002-B1. Không đổi ngân sách, chỉ đổi
   phép đo.

## Kết Luận (Conclusion)

```text
REVIEW_RESULT       = PASS
FINAL_ACCEPTANCE    = ACCEPT
INTEGRATION_READY   = YES
REPAIR_CYCLE_USED   = 0 trong phiên này (lineage vẫn 1/2 — còn 1)
BLOCKING findings   = 0
NON_BLOCKING        = 4 (B1 đã sửa số liệu; B2, B3, B4 DEFER có re-trigger)
```

Slice B chứng minh được điều nó phải chứng minh: **"không thấy" không bao giờ tự
biến thành "đã xóa"**. Ở cả hai nhánh `NOT_SEEN_IN_LATEST_SNAPSHOT` và
`REMOVED_IN_SOURCE_CANDIDATE`, hệ quả duy nhất là một dòng trong bảng cờ; con trỏ
hiện hành, các bảng version và mọi con số analytics không nhúc nhích — đo trên
PostgreSQL 16.13 thật, không chỉ trên test SQLite. `CONFIRMED_COMPLETE` có đúng
một cửa và cửa đó đòi một hành động tường minh của con người.

## Việc Cần Theo Dõi Tiếp (Required Follow-up)

1. **Slice C phải lập kế hoạch trong 107 dòng logic production** trước dừng cứng
   1.500 (không phải 154). Nếu không đủ, mở đề xuất CHANGE_BUDGET cho Owner
   **TRƯỚC** khi viết mã — không viết trước rồi xin sau.
2. FIND-PRA002-B2 (nhân đôi cờ khi xác nhận đồng thời) → PRA-004.
3. FIND-PRA002-B3 (trần 200 cờ trên trang snapshot) → PRA-004 Review Ops UI.
4. CHECK-PRA002-08 (`RESULT_REVISED`), 14 (RDA), 15 (Production Acceptance) vẫn
   `NOT_TESTED` — thuộc slice C và Owner. Review này KHÔNG bắt đầu slice C.
