# BÀN GIAO SESSION (SESSION HANDOFF)

Session ID:
S083

Task:
TASK-PRA-002 — Slice B (Snapshot Coverage Semantics)

Task Mode:
MAJOR (implementation)

Project Profile:
PRODUCT

Status:
IMPLEMENTED — slice B hoàn tất, chờ Independent Review E2 trước Controlled
Integration. `TASK-PRA-002` tổng thể VẪN đang implementation (slice C chưa làm).

## Thẩm Quyền Git (Git Authority)

```
Repo                        : hoangvinhkta-creator/Reports
Nhánh canonical (origin HEAD): claude/extract-upload-repo-gq2ws4
EXPECTED_BASE_SHA (chỉ thị) : 27b9d1c5a578742450099c53f2f82411f07aa9dc
origin/canonical lúc mở phiên: 27b9d1c5a578742450099c53f2f82411f07aa9dc  (KHỚP — canonical KHÔNG dịch chuyển)
IMPLEMENTATION_BASE_SHA     : 27b9d1c5a578742450099c53f2f82411f07aa9dc
Nhánh làm việc              : claude/pra-002-slice-b-snapshot-8rbwip  (cắt từ đúng SHA trên)
Worktree lúc mở phiên       : CLEAN
Tracking                    : KHÔNG đọc, KHÔNG sửa — TRACKING_CHANGED = NO
```

`scripts/branch_authority_check.sh` lúc mở phiên báo `DEFAULT_TIP == HEAD_SHA ==
27b9d1c5`, `WORKTREE = CLEAN`, và `STOP — BRANCH AUTHORITY UNRESOLVED` với lý do
**duy nhất** là nhánh slice B chưa có upstream (nhánh mới, chưa push lần nào) —
đúng trạng thái mong đợi ở đầu một phiên implementation. Không dùng `main`,
không rebase, không force push.

## Phạm Vi Đã Làm (Slice B) — và phạm vi CỐ Ý chưa làm

Vertical của slice B:

```
snapshot coverage (DETECTED_ONLY / HEADER_CONSISTENT)
 → xác nhận TƯỜNG MINH của người dùng
 → CONFIRMED_COMPLETE
 → bước 4  NOT_SEEN_IN_LATEST_SNAPSHOT
 → bước R  REMOVED_IN_SOURCE_CANDIDATE
 → fail-safe: hiện trạng và mọi con số analytics KHÔNG đổi ở cả hai nhánh
```

KHÔNG làm (đúng exclusion mục 16 của chỉ thị phiên):

- Slice C: cờ `RESULT_REVISED`, Real Data Acceptance cuối, production
  acceptance cuối.
- Phân xử `REMOVED_CANDIDATE`, acknowledgement workflow, ngữ nghĩa huỷ/hoàn
  (D1/D5 — `OWNER_DECISION_REQUIRED`, DEFER sang PRA-004).
- Huỷ xác nhận coverage (D10), `confirmed_by` (D4), coverage calendar (D7).
- Không PRA-003/004/005, không legacy detail import, không đụng Tracking,
  không đổi hạ tầng/Render/Dockerfile/render.yaml.

## Database / Migration

**KHÔNG tạo migration mới.** Schema `0002_snapshots` (đã integrate ở slice A)
đã có sẵn mọi thứ slice B cần — đây là bằng chứng, không phải phỏng đoán:

```text
source_snapshot.coverage_state   CHECK IN ('DETECTED_ONLY','HEADER_CONSISTENT','CONFIRMED_COMPLETE')
source_snapshot.confirmed_range_start / confirmed_range_end / confirmed_at / confirmed_by
source_snapshot.n_not_seen / n_removed_candidate     (NOT NULL DEFAULT 0)
reconciliation_flag.kind         CHECK IN (..., 'NOT_SEEN_IN_LATEST_SNAPSHOT',
                                           'REMOVED_IN_SOURCE_CANDIDATE', ...)
```

```
$ HISTORY_DATABASE_URL=postgresql+psycopg://postgres@127.0.0.1:55432/sliceb \
    python3 -m alembic upgrade head
$ psql -tAc "SELECT version_num FROM alembic_version;"
0002_snapshots                     <-- ALEMBIC_HEAD KHÔNG đổi so với slice A
```

`git status` xác nhận `tools/db/**` (schema + migrations) KHÔNG có một thay đổi
nào trong phiên này.

## Mô Hình Coverage (E1)

Ba mức giữ nguyên như slice A đã freeze; slice B chỉ thêm ĐÚNG một cách đạt tới
mức thứ ba:

```text
DETECTED_ONLY       header không đọc được dạng đã biết, HOẶC header không bao trọn dữ liệu
HEADER_CONSISTENT   header (một trong hai dạng đã đo) BAO TRỌN khoảng ngày đo được
CONFIRMED_COMPLETE  CHỈ qua POST /du-lieu/snapshot/<id>/xac-nhan-du với ô xác nhận được tích
```

Hai bảo đảm bằng test tĩnh (đọc AST, không grep chuỗi):

- `test_confirmed_complete_is_written_by_exactly_one_function` — duyệt toàn bộ
  `app/**/*.py`: chuỗi `CONFIRMED_COMPLETE` chỉ được gán cho `coverage_state`
  tại đúng một file (`app/web/history_store.py`), trong đúng một hàm
  (`SnapshotRepository.confirm_coverage`).
- `test_only_the_confirmation_function_updates_the_snapshot_row` — mọi
  `update(source_snapshot)` đều nằm trong `confirm_coverage`, và tập cột được
  ghi đúng bằng `{coverage_state, confirmed_range_start, confirmed_range_end,
  confirmed_at, n_removed_candidate}` — không cột nào khác của bảng fact bị sửa.

Tầng thuần `app/history/coverage.py` KHÔNG BAO GIỜ trả `CONFIRMED_COMPLETE`
(test duyệt tích 3 header × 3 khoảng ngày, gồm cả "đúng trọn tháng" và "thấy
ngày cuối tháng").

## Bằng Chứng Xác Nhận Tường Minh (E1)

Chạy trên PostgreSQL 16.13 thật, fixture golden `period_2026_01.xlsx` qua ĐÚNG
pipeline authoritative:

```
KHÔNG tick ô xác nhận:
  → CoverageRangeError "Chưa tích ô xác nhận. Hệ thống không bao giờ tự kết luận sổ đã đầy đủ."
  → coverage_state = HEADER_CONSISTENT   (KHÔNG đổi)
Khoảng khai báo 01–10/01 không bao dữ liệu tới 31/01:
  → CoverageRangeError "... có ngày nằm NGOÀI khoảng khai báo (muộn nhất 2026-01-31) ..."
  → coverage_state = HEADER_CONSISTENT   (KHÔNG đổi)
Tick ô + khoảng 01–31/01:
  → coverage_state = CONFIRMED_COMPLETE, range = 2026-01-01 → 2026-01-31, confirmed_by = None
Xác nhận lần 2:
  → CoverageAlreadyConfirmedError; REMOVED_CANDIDATE vẫn = 1 (KHÔNG nhân đôi cờ)
```

Tầng web (Flask test client), đúng các mã trạng thái mục 7.3 quy định:

```
GET  trang snapshot chưa xác nhận  → 200, có <input name="xac_nhan">, KHÔNG có "checked"
POST thiếu xac_nhan                → 400, "Chưa tích ô xác nhận", coverage KHÔNG đổi
POST khoảng không bao dữ liệu      → 400, nêu đúng ngày lệch (2026-01-20), confirmed_at = NULL
POST khoảng > 366 ngày             → 400, coverage KHÔNG đổi
POST hợp lệ                        → 302 (PRG), coverage_state = CONFIRMED_COMPLETE
POST lần 2                         → 409, bản ghi snapshot y hệt trước đó
POST snapshot không tồn tại        → 404
```

Phạm vi hiển thị = phạm vi đã lưu (không phải một mô tả): trang in
`value="2026-01-05"` / `value="2026-01-20"` đúng bằng
`detected_date_min`/`detected_date_max` đọc lại từ database.

## Bằng Chứng NOT_SEEN (E1)

```
B (351 dòng) → B'' (bỏ đúng 1 dòng, khoá BH64081, 20.900.000 VND):
  coverage = HEADER_CONSISTENT (chưa xác nhận)
  n_same = 350   n_not_seen = 1   n_removed_candidate = 0
  cờ NOT_SEEN_IN_LATEST_SNAPSHOT = 1, REMOVED_IN_SOURCE_CANDIDATE = 0
  hiện hành 351 dòng / 254 đơn / 3.562.310.000 VND  →  KHÔNG ĐỔI
```

Cờ mang đủ provenance để giải thích: `raised_by_snapshot_id` = snapshot mới,
`run_id` = run mới, `from_version_id` = ĐÚNG version nguồn đang hiện hành của
khoá vắng mặt, `to_version_id` = NULL (không version nào được tạo),
`detail_json = {"scope": "DETECTED", "range_start": ..., "range_end": ...}`.

`NOT_SEEN` được dựng ở CẢ HAI mức chưa xác nhận (`DETECTED_ONLY` và
`HEADER_CONSISTENT`) — test tham số hoá; `HEADER_CONSISTENT` KHÔNG bao giờ được
đối xử như một sự xác nhận.

## Bằng Chứng REMOVED_CANDIDATE (E1)

```
Sau POST xac-nhan-du (01–31/01) trên chính snapshot B'':
  coverage_state = CONFIRMED_COMPLETE
  REMOVED_IN_SOURCE_CANDIDATE = 1  (đúng khoá BH64081)
  hiện hành 351 dòng / 254 đơn / 3.562.310.000 VND   →  KHÔNG ĐỔI (tới từng đồng)
  bảng fact trước → sau:
    order_line_source_version 351 → 351      order_line_current 351 → 351
    snapshot_line 351 → 701                  order_line_result_version 351 → 701
    reconciliation_flag 0 → 2
  KHÔNG bảng fact nào giảm; KHÔNG dòng nào bị xoá; KHÔNG đơn nào bị đánh dấu huỷ
  cờ NOT_SEEN cũ của cùng khoá GIỮ NGUYÊN bên cạnh cờ REMOVED (append-only)
  acknowledged_at của mọi cờ = NULL (PRA-002 không có resolution — DEFER)
```

Bước R đọc **membership `snapshot_line` của chính snapshot được xác nhận**, chứ
không đọc `last_seen` (DEC-171 #6). Có test riêng cho đúng cái bẫy này
(`test_confirmation_uses_this_snapshots_membership_not_the_latest_state`): xác
nhận một sổ hẹp SAU khi một sổ rộng hơn đã ghi đè `last_seen` của mọi khoá vẫn
tìm ra đúng ứng viên; nếu đọc `last_seen` thì kết quả sẽ là 0 và ứng viên thật
bị bỏ sót.

## Bằng Chứng Ranh Giới Phạm Vi (E1) — điểm quan trọng nhất của slice

Phạm vi giới hạn thẩm quyền. Cùng một cặp dữ liệu, chỉ khác khoảng được khai:

```
B (01–31/01, 351 dòng) đã lưu, rồi upload A (cắt tới 10/01, 89 dòng):
  A detected = 2026-01-02 → 2026-01-10
  n_not_seen = 0                      <-- sổ nửa tháng KHÔNG phát biểu gì về nửa sau
  xác nhận A cho ĐÚNG 01–10/01  → REMOVED_CANDIDATE = 0
  xác nhận A cho CẢ THÁNG 01–31 → REMOVED_CANDIDATE = 262  (= 351 − 89)
  cả hai trường hợp: hiện hành 351 dòng / 3.562.310.000 VND — KHÔNG ĐỔI
```

Bốn điều kiện loại trừ của `reconciler.absent_keys`, mỗi điều kiện là một cách
tạo ra sự vắng mặt GIẢ nếu quên (đều có test thuần riêng, kể cả test ranh giới
tham số hoá ngày 01/10/11/31):

1. khoá có trong snapshot mới → không vắng mặt;
2. `sale_date` là NULL → không kỳ nào có thẩm quyền với nó;
3. ngày ngoài `[start, end]` → snapshot không đại diện cho kỳ đó;
4. khoá đang `ORDER_KEY_COLLISION` → danh tính chưa rõ thì không kết luận vắng mặt.

Phạm vi mở (`start`/`end` là None) trả về RỖNG — không có phạm vi thì không có
thẩm quyền, chứ không phải "vắng mặt tất cả".

**Diễn giải tường minh cần Reviewer biết.** Chỉ thị phiên (mục 12) viết rằng khi
upload A (01–10) sau B (01–30) mà A chưa xác nhận thì "các key 11–30/09 →
NOT_SEEN_IN_LATEST_SNAPSHOT". Frozen contract (mục 8 bước 4) lại giới hạn bước 4
trong khoảng ĐO ĐƯỢC của snapshot mới, nên các khoá 11–30 KHÔNG được dựng cờ.
Implementation theo **frozen contract**, đúng thứ tự thẩm quyền mà chính chỉ thị
đặt ra (mục 2 "Frozen TASK-PRA-002 là authority", mục 6 "ưu tiên frozen
contract", mục 17 "NOT_SEEN only where contract applies") và đúng nguyên tắc
đóng của mục 12–13 ("Absence chỉ có nghĩa trong phạm vi coverage đang được xác
nhận"). Đây cũng là hướng an toàn hơn: im lặng đúng thay vì một cảnh báo sai
phạm vi. Hiện trạng và mọi con số KHÔNG đổi ở cả hai cách hiểu.

## Bằng Chứng Chồng Kỳ (E1)

```
A (89 dòng, ≤10/01) → B (351 dòng, cả tháng):
  n_same = 89, n_insert = 262, n_not_seen = 0, tổng số cờ = 0
  hiện hành 351 dòng — KHÔNG double-count
  xác nhận B cho 01–31/01 → REMOVED_CANDIDATE = 0 (B chứa trọn A)
Đảo thứ tự B → A:
  n_same = 89, n_insert = 0, n_not_seen = 0, hiện hành KHÔNG đổi
```

Đẳng thức `state(A rồi B) == state(B một mình)` của slice A vẫn PASS nguyên vẹn
sau slice B (`test_a_half_month_book_then_the_full_month_equals_the_full_month_alone`).

## Bằng Chứng Xuất Hiện Trở Lại (E1)

Cờ vắng mặt là **BẤT BIẾN**; "còn hiệu lực" được **DẪN XUẤT** lúc đọc, bằng
cách hỏi lịch sử membership "khoá này có xuất hiện ở snapshot nào SAU snapshot
đã dựng cờ không". Không có mutate, không có delete, không có
acknowledgement workflow.

```
trước khi quay lại : [(NOT_SEEN, is_active=True), (REMOVED_CANDIDATE, is_active=True)]
sau khi quay lại   : [(NOT_SEEN, is_active=False), (REMOVED_CANDIDATE, is_active=False)]
                     seen_again_in_snapshot_id = snapshot mới (cả hai cờ)
tổng số cờ 2 → 2   (không cờ nào bị xoá, không cờ nào bị sửa)
snapshot mới n_same = 351; hiện hành 351 dòng / 3.562.310.000 VND
```

So sánh thời gian là **NGẶT** (`created_at` phải LỚN HƠN hẳn). Hai snapshot
trong cùng một giây không có thứ tự đáng tin (`snapshot_id` sắp theo
fingerprint, không theo thời gian), và ở đó implementation nghiêng về phía an
toàn: GIỮ cờ ở trạng thái còn hiệu lực. Một cảnh báo thừa để người dùng tự kiểm
tốt hơn một sự vắng mặt bị âm thầm giấu đi. Không con số nghiệp vụ nào phụ thuộc
nhãn này — hiện trạng và tổng tiền không bao giờ do cờ quyết định.

Cờ KHÔNG nói về vắng mặt (`SOURCE_CHANGED`, `ORDER_KEY_COLLISION`) có
`is_active = None` — không gắn nhãn giả cho thứ không phải phát biểu về sự
vắng mặt.

## Bằng Chứng Hiện Trạng / Tổng Không Đổi (E1)

Mọi test vắng mặt đều kết thúc bằng cùng một phép so trên database thật:

```python
business_state = {current_totals, current_fingerprints,
                  COUNT(order_line_source_version), COUNT(order_line_current)}
```

trước == sau, ở CẢ hai nhánh (`NOT_SEEN` và `REMOVED_CANDIDATE`). Với đường
XÁC NHẬN — nơi không có run pipeline nào chạy — phép so được siết thêm
`COUNT(order_line_result_version)` và `COUNT(snapshot_line)`: tuyệt đối không
bảng nào được nhúc nhích. Lịch sử source version được so **nguyên văn từng
dòng** trước/sau (`test_historical_source_versions_are_untouched_by_any_absence_flag`).

## Sửa FIND-PRA002-A4

Trang snapshot trước đây in cố định "CHƯA XÁC NHẬN ĐỦ" bất kể trạng thái thật.
Nhãn nay đến từ `coverage_state` đã lưu, qua `coverage.COVERAGE_LABELS` (nguồn
sự thật duy nhất cho phần chữ người dùng đọc):

```text
DETECTED_ONLY       → "CHƯA XÁC NHẬN ĐỦ — chỉ phát hiện phạm vi từ dữ liệu"
HEADER_CONSISTENT   → "CHƯA XÁC NHẬN ĐỦ — header khớp phạm vi dữ liệu"
CONFIRMED_COMPLETE  → "ĐÃ XÁC NHẬN ĐẦY ĐỦ cho phạm vi được khai báo"
```

Test tham số hoá dựng snapshot với header dạng đã biết và header dạng lạ, rồi
đọc HTML thật để khẳng định câu trên trang đổi theo trạng thái; một test khác
khẳng định sau khi xác nhận thì trang hiện đúng khoảng đã xác nhận và KHÔNG còn
mời xác nhận lại. Ba nhãn khác nhau đôi một (test khẳng định `len(labels) == 3`).

## Kết Quả Test

```
$ python3 -m pytest -q
1781 passed, 11 skipped in 57.33s

$ python3 -m pytest -q tests/test_golden_baseline.py
58 passed, 2 skipped                      <-- KHÔNG đổi so với baseline

$ python3 -m pytest -q tests/test_legacy_repository.py tests/test_legacy_importer.py \
      tests/test_legacy_source_coverage.py tests/test_history_db.py
81 passed                                 <-- PRA-001 regression PASS

$ python3 -m pytest -q tests/test_history_keys.py tests/test_history_reconciler.py \
      tests/test_snapshot_repository.py tests/test_web_history.py \
      tests/test_pipeline_history_vertical.py tests/test_history_coverage_confirmation.py \
      tests/test_snapshot_absence.py
    (slice A + slice B focused) PASS
```

Baseline tại BASE_SHA `27b9d1c5`: `1711 passed, 11 skipped`. Sau slice B:
`1781 passed, 11 skipped` → **+70 test mới, 0 test bị xoá/làm yếu, số skip
KHÔNG tăng**.

PostgreSQL 16.13 thật (`postgresql+psycopg`): migration `upgrade head` →
`0002_snapshots`; toàn bộ năm kịch bản ở trên chạy trên PG với dữ liệu golden
qua pipeline thật — không kịch bản nào chỉ chạy trên SQLite.

Một guard test của slice A được **CẬP NHẬT (không xoá)**:
`test_the_write_path_contains_no_delete_and_updates_only_the_pointer_table` nay
cho phép `update(source_snapshot)` — đúng ngoại lệ mà mục 4 của task đã freeze —
và ngay lập tức được siết lại bằng HAI test hẹp hơn (chỉ `confirm_coverage`
được UPDATE, và chỉ đúng 5 cột xác nhận). Ràng buộc append-only vì vậy CHẶT
HƠN sau slice B, không lỏng hơn.

Một helper test dùng chung (`tests/test_snapshot_repository.write`) được thêm
tham số `header_text` với giá trị mặc định y như cũ — không test hiện có nào
đổi hành vi.

## Change Budget

```
PRODUCTION PYTHON (dòng logic, bỏ trống/comment/docstring)
   +45  app/history/coverage.py        (nhãn coverage + parse ngày + luật xác nhận)
    +4  app/history/models.py          (2 hằng cờ + ABSENCE_FLAG_KINDS + CurrentKey)
   +22  app/history/reconciler.py      (absent_keys — hàm thuần dùng chung bước 4 và R)
  +142  app/web/history_store.py       (bước 4, confirm_coverage/bước R, dẫn xuất is_active)
   +29  app/web/server.py              (route xac-nhan-du + _snapshot_page)
  +242  TỔNG   → mục tiêu ≤ 500 ĐẠT; cảnh báo mềm 600 và dừng cứng 800 KHÔNG chạm
                 (bằng 22 % của slice A: 1.104 dòng — slice B nhỏ hơn đáng kể như yêu cầu)

TEMPLATE  +52 dòng không trống  (snapshot.html +48, du_lieu.html +4)
TEST      +70 test mới; 2 file test mới (165 + 373 dòng không trống) + 230 dòng thêm vào 3 file cũ
MIGRATION KHÔNG có (schema 0002 đã đủ — bằng chứng ở mục Database)
Dependency mới: KHÔNG
```

Ngân sách lineage `TASK-PRA-002` (mục 17 của task, cấp toàn task): sau slice B
tổng production Python là 1.104 + 242 = **1.346 / mục tiêu 1.200, dừng cứng
1.500**. Vượt mục tiêu mềm nhưng CHƯA chạm dừng cứng; slice C còn 154 dòng
trước ngưỡng 1.500 — đây là điều Reviewer và phiên slice C cần biết trước khi
mở việc, ghi ra đây thay vì để phát hiện muộn.

## Đăng Ký File Đã Thay Đổi

Created:
- `tests/test_history_coverage_confirmation.py`, `tests/test_snapshot_absence.py`
- `docs/sessions/S083-pra-002-slice-b-coverage-semantics.md`

Modified:
- `app/history/coverage.py`, `app/history/models.py`, `app/history/reconciler.py`
- `app/web/history_store.py`, `app/web/server.py`
- `app/web/templates/snapshot.html`, `app/web/templates/du_lieu.html`
- `tests/test_snapshot_repository.py` (1 guard cập nhật + 2 guard mới hẹp hơn + helper),
  `tests/test_web_history.py`, `tests/test_pipeline_history_vertical.py`
- `PROJECT/PROJECT_PROGRESS.md`, `PROJECT/REVIEW_BUDGET_LEDGER.md`,
  `docs/tasks/TASK-PRA-002-pipeline-persistence-reconciliation.md`

Deleted: (không)

## Kiểm Tra Phạm Vi (Scope Check)

`git status --porcelain` KHÔNG chứa: `app/pipeline.py`, `app/composition.py`,
`app/demo.py`, `app/modules/**`, `app/owner_usability.py`,
`app/owner_launcher.py`, `app/web/storage_backend.py`, `app/web/run_registry.py`,
`app/legacy/**`, `tools/db/**` (schema + migration), `tools/storage/**`,
`tools/tracking/**`, `config/**`, `data/**`, `tests/fixtures/**`, `render.yaml`,
`Dockerfile`. `TRACKING_CHANGED = NO`. `git diff --check` sạch.

Ranh giới ADR-101 giữ nguyên: `app/history/**` vẫn KHÔNG import `sqlalchemy`,
`psycopg`, `alembic` hay `flask` — `absent_keys` và `confirmation_error` là hàm
thuần, SQL chỉ thu hẹp đầu vào chứ không định nghĩa nghiệp vụ
(`test_no_module_under_app_imports_a_database_driver_or_alembic` PASS).

Không PII rò rỉ: cờ vắng mặt chỉ mang khoá đơn/dòng và `detail_json` gồm đúng
`{scope, range_start, range_end}` — không trường nghiệp vụ nào, càng không PII.

## Findings

Không có finding BLOCKING (production path + business consequence + evidence).

Sửa tại chỗ trong phiên (local repair, đúng chính sách finding mục 21):

- **Dẫn xuất `is_active` ban đầu tie-break theo `snapshot_id` khi hai snapshot
  cùng `created_at`.** Vì `snapshot_id` sắp theo fingerprint chứ không theo thời
  gian, một cờ vắng mặt CÒN hiệu lực có thể bị hiển thị nhầm thành "đã xuất hiện
  lại" — giấu một sự vắng mặt thật khỏi người vận hành. Phát hiện khi test web
  (hai lần chạy trong cùng một giây) đỏ. Đã sửa thành so sánh NGẶT trên
  `created_at` với ngả về phía giữ cờ còn hiệu lực; test thứ tự thời gian nay
  điều khiển đồng hồ tường minh thay vì trông chờ tốc độ máy. Không ảnh hưởng
  con số nghiệp vụ nào (cờ không bao giờ quyết định hiện trạng).

Đã DEFER:

- **Thứ tự hai snapshot trong cùng một giây** (kế thừa finding DEFER của slice
  A). Nay có thêm một hệ quả hiển thị đã được xử lý fail-safe ở trên.
  Re-trigger: nếu UI cần thứ tự chèn chính xác (PRA-003), hoặc nếu một cột thứ
  tự đơn điệu được thêm vì lý do khác.
- **FIND-PRA002-A2** (`present_lines` chạy hai lần) và **FIND-PRA002-A3**
  (`detected_date_*` nullable) — giữ nguyên DEFER sang slice C/hardening theo
  kết luận Independent Review slice A. Slice B không chạm hai chỗ đó.
- **3 vấn đề reference-integrity của REM-T06** — pre-existing, ngoài slice.
- **Phase D — public ingress `0.0.0.0/0` của `tinphat-reports-db`** —
  OPEN/PENDING, ngoài slice.
- **Ngân sách lineage vượt mục tiêu mềm 1.200** (nay 1.346/1.500) — không phải
  finding về chất lượng mã; là dữ kiện lập kế hoạch cho slice C, ghi ở mục
  Change Budget.

## Trạng Thái Completion Gate Sau Slice B

| Check | Trước | Sau slice B | Ghi chú |
|---|---|---|---|
| CHECK-PRA002-01 | PASS | PASS (không đổi) | không có migration mới; `alembic upgrade head` = `0002_snapshots` trên PG 16.13 |
| CHECK-PRA002-02 | PASS | PASS (không đổi) | |
| CHECK-PRA002-03 | PASS | PASS (không đổi) | |
| CHECK-PRA002-04 | PASS | PASS (không đổi) | đẳng thức `state(A,B) == state(B)` vẫn xanh sau slice B |
| CHECK-PRA002-05 | PASS | PASS (không đổi) | |
| CHECK-PRA002-06 | PARTIAL | **PASS (E1)** | 400/409/404, validate khoảng + 366 ngày, hai test tĩnh "đúng một cửa" |
| CHECK-PRA002-07 | NOT_TESTED | **PASS (E1)** | NOT_SEEN → xác nhận → REMOVED trên PG thật; current/tổng/bảng fact không đổi |
| CHECK-PRA002-08 | NOT_TESTED | NOT_TESTED | slice C |
| CHECK-PRA002-09 | PASS | **PASS (E1, siết chặt hơn)** | guard append-only cập nhật + 2 guard mới hẹp hơn |
| CHECK-PRA002-10 | PASS | PASS (không đổi) | thêm nhánh fail-closed của đường xác nhận |
| CHECK-PRA002-11 | PASS | **PASS (E1)** | Golden 58/2; full 1781 (≥1711); skip không tăng |
| CHECK-PRA002-12 | PASS | **PASS (E1)** | `app/history` vẫn sạch DB/flask; scope audit sạch |
| CHECK-PRA002-13 | PASS | **PASS (E1)** | `detail_json` cờ vắng mặt không mang trường nghiệp vụ nào |
| CHECK-PRA002-14 | NOT_TESTED | NOT_TESTED | Real Data Acceptance — không có workbook thật trong session; gate Owner |
| CHECK-PRA002-15 | NOT_TESTED | NOT_TESTED | Production Acceptance — Owner, sau Controlled Integration |
| CHECK-PRA002-16 | PASS | PASS (không đổi) | slice B không thêm đường đọc workbook nào |
| CHECK-PRA002-17 | NOT_TESTED | NOT_TESTED | Independent Review E2 slice B — bước tiếp theo |

Không check REQUIRED nào bị xoá hay làm yếu. `TASK-PRA-002` KHÔNG được đánh
dấu DONE.

## Hành Động Tiếp Theo (NEXT_VERTICAL_ACTION)

**Independent Review E2 cho slice B trước Controlled Integration.** Reviewer
chạy lại độc lập CHECK-06 và CHECK-07 (và phần regression của 09/11/12/13),
theo `governance/templates/E2_INDEPENDENT_REVIEW_TEMPLATE.md`, ghi vào
`docs/reviews/TASK-PRA-002-SLICE-B-INDEPENDENT-REVIEW-RECORD` (chưa tồn tại —
phiên review tạo). Ngân sách
repair của lineage: 2 cycle, đã dùng 1 (còn 1).

Hai điểm Reviewer nên soi kỹ trước tiên:

1. **Diễn giải phạm vi bước 4** (mục "Bằng Chứng Ranh Giới Phạm Vi") — chỉ thị
   phiên và frozen contract nói khác nhau; implementation theo frozen contract.
2. **Dẫn xuất `is_active`** — quy ước so sánh ngặt trên `created_at` và hệ quả
   của nó khi hai snapshot rơi vào cùng một giây.

KHÔNG bắt đầu slice C trong phiên này.
