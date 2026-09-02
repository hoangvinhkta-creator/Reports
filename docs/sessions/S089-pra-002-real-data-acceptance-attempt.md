# BÀN GIAO SESSION (SESSION HANDOFF)

Session ID:
S089

Task:
TASK-PRA-002 — Real Data Acceptance (RDA), mục 15 của frozen contract

Task Mode:
MAJOR (evidence / acceptance — KHÔNG phải implementation)

Project Profile:
PRODUCT

Status:
BLOCKED_OWNER_INPUT — `CHECK-PRA002-14` giữ nguyên `NOT_TESTED`. Không có
workbook kế toán thật nào trong session; RDA-1..5 không thể thực thi. RDA-6
(nửa golden) đã chạy và PASS. `TASK-PRA-002` VẪN `IN_PROGRESS`.

## Thẩm Quyền Git (Git Authority)

```
Repo                        : hoangvinhkta-creator/Reports
Nhánh canonical (origin HEAD): claude/extract-upload-repo-gq2ws4
EXPECTED_CANONICAL_SHA      : d7a1154a2892e5869e286e10da49f750aa0611df
origin/canonical lúc mở phiên: d7a1154a2892e5869e286e10da49f750aa0611df  (KHỚP — canonical KHÔNG dịch chuyển)
BASE_SHA                    : d7a1154a2892e5869e286e10da49f750aa0611df
Nhánh làm việc              : claude/pra-002-real-data-acceptance-4smfzv
Worktree lúc mở phiên       : CLEAN
Tracking                    : KHÔNG đọc, KHÔNG sửa — TRACKING_CHANGED = NO
PRODUCTION_CODE_ADDED       : 0 dòng
```

`scripts/branch_authority_check.sh` chạy ở chế độ DETACHED với
`TARGET_SHA=d7a1154a…` (đúng cơ chế V4.1 §0.B dành cho phiên đọc/evidence):

```
DEFAULT_BRANCH       : claude/extract-upload-repo-gq2ws4
DEFAULT_TIP          : d7a1154a2892e5869e286e10da49f750aa0611df
HEAD_SHA             : d7a1154a2892e5869e286e10da49f750aa0611df
WORKTREE             : CLEAN
MODE                 : DETACHED
AUTHORITY            : DETACHED_EXACT_TARGET
RESULT               : AUTHORITY_OK
```

Ở chế độ BRANCH, script báo `STOP — BRANCH AUTHORITY UNRESOLVED` với lý do
**duy nhất** là nhánh phiên chưa có upstream (nhánh mới) — trạng thái mong đợi,
không phải lệch authority: `0 ahead / 0 behind` so với canonical.

## Kiểm Kê Dữ Liệu Thật (Real Data Inventory)

Quét toàn bộ filesystem của session (`find /` cho `*.xlsx`, `*.xls`, `*.xlsm`,
`*So_chi_tiet*`) và toàn bộ lịch sử git (`git log --all --diff-filter=A`).

| FILE | REAL_OR_GENERATED | DATE_RANGE | APPROX_ROWS | KNOWN_RELATIONSHIP | USABLE_FOR_RDA |
|---|---|---|---|---|---|
| `tests/fixtures/golden/period_2026_01.xlsx` | GENERATED (fixture đã ẩn danh, dẫn xuất từ workbook thật qua `tests/fixtures/golden/anonymize.py`) | 01/2026 | 351 dòng / 254 đơn | KHÔNG overlap với `period_2026_06` (khác tháng) | **NO** cho RDA-1..5; YES cho RDA-6 |
| `tests/fixtures/golden/period_2026_06.xlsx` | GENERATED (như trên) | 06/2026 | 180 dòng / 146 đơn | KHÔNG overlap với `period_2026_01` | **NO** cho RDA-1..5; YES cho RDA-6 |

```
sha256  73b519aa930c59fda8b06f0763951b0d1859b53a53f8bde8069b20af76e7adcb  period_2026_01.xlsx
sha256  1025567c1e247863086e59830394cc93cefc3c1ba8aaee0691440949f92e277a  period_2026_06.xlsx
```
SHA256 đo trước và sau khi chạy test — KHÔNG đổi. Không file nào bị sửa.

**Không có `So_chi_tiet_ban_hang*.xlsx` trong session.** `data/` chỉ chứa ba
file JSONL trạng thái runtime (`product_identity`, `confirmed_adjustments`,
`historical_confirmed`), không phải accounting export. `.gitignore:19-20`
(`*.xlsx` + `!tests/fixtures/**/*.xlsx`) khiến workbook thật về mặt cấu trúc
KHÔNG THỂ nằm trong repo — đúng DEC-108. Biến môi trường `GOLDEN_RAW_01` /
`GOLDEN_RAW_06` KHÔNG được đặt.

Hai fixture golden là **dẫn xuất đã ẩn danh** của workbook production, KHÔNG
phải "workbook kế toán thật" theo định nghĩa mục 15. Chúng cũng khác tháng nên
không thoả quan hệ `A ⊂ B` mà RDA-3 đòi. Phiên này KHÔNG gọi chúng là real data.

## Đường Dự Phòng (Controlled Copy) — KHÔNG khả dụng, ba tầng chặn

Mục 15 cho phép dự phòng bằng `tools/analysis/make_snapshot_variants`. Đường
này bị chặn hoàn toàn:

1. **Không có input**: controlled copy vẫn cần MỘT workbook thật làm nguồn — không có.
2. **Không có tool**: `tools/analysis/make_snapshot_variants` chưa tồn tại (`find` → rỗng); nó là hạng mục PRA-002.C2 chưa làm.
3. **Bị cấm trong phiên**: chỉ thị phiên liệt kê `make_snapshot_variants` trong HARD EXCLUSIONS.

Vì vậy KHÔNG viết tool, KHÔNG sinh file. Đúng mục 792–793 của contract:
thiếu workbook thật → `CHECK-PRA002-14 = NOT_TESTED` + gate Owner.

## Bối Cảnh Database

PostgreSQL 16.13 thật, cluster **isolated mới khởi tạo trong scratchpad**
(không phải production, không có dữ liệu từ trước — không có thao tác destructive
nào lên bất kỳ DB nào).

```
PostgreSQL 16.13 (Ubuntu 16.13-0ubuntu0.24.04.1) on x86_64-pc-linux-gnu
alembic upgrade head → alembic_version = 0002_snapshots
```

Sáu bảng PRA-002 tồn tại và RỖNG (baseline sạch cho RDA-1, nếu có dữ liệu thật):

```
source_snapshot            = 0
order_line_source_version  = 0
snapshot_line              = 0
order_line_result_version  = 0
order_line_current         = 0
reconciliation_flag        = 0
```

Đây là bằng chứng PostgreSQL **thật** cho phần DDL/migration (dialect
compatibility của `Date`, `ExactNumeric`, UNIQUE). KHÔNG có dữ liệu thật để
import nên không thể sinh bằng chứng reconciliation trên PG trong phiên này.

## Kết Quả RDA Theo Từng Bước

| Bước | Phân loại | Ghi chú |
|---|---|---|
| RDA-1 First import | `NOT_TESTED` | Không có snapshot A thật |
| RDA-2 Exact reupload | `NOT_TESTED` | Phụ thuộc RDA-1 |
| RDA-3 Overlap `B ⊃ A` | `NOT_TESTED_REAL_DATA` | Không có export thật thứ hai; đường dự phòng bị chặn ba tầng |
| RDA-4 `SOURCE_CHANGED` | `NOT_OBSERVED_IN_REAL_DATA` | Đã chứng minh E2 bằng synthetic ở S087 — KHÔNG đổi nhãn thành real |
| RDA-5 `NOT_SEEN` → `REMOVED_IN_SOURCE_CANDIDATE` | `NOT_TESTED` | Cần xác nhận đủ của Owner trên dữ liệu thật |
| RDA-6 Golden không hồi quy | **`PASS`** (fixture, không phải real data) | `58 passed, 2 skipped` — khớp ĐÚNG kỳ vọng frozen |
| RDA-6 Cohort S068 (58 đơn/83 dòng, 22 AUTO) | `NOT_TESTED` | Cohort không có trên máy; contract để điều kiện "nếu có" |

Output nguyên văn RDA-6:

```
$ python -m pytest tests/test_golden_baseline.py -q
..........................................................ss             [100%]
58 passed, 2 skipped in 6.31s
```

Kiểm tra sức khoẻ canonical SHA (KHÔNG phải bước RDA):

```
$ python -m pytest tests/test_history_db.py tests/test_history_keys.py \
    tests/test_history_reconciler.py tests/test_history_coverage_confirmation.py \
    tests/test_snapshot_absence.py tests/test_snapshot_repository.py \
    tests/test_pipeline_history_vertical.py tests/test_web_history.py -q
211 passed in 30.41s
```

**Đính chính quan trọng về nhãn bằng chứng.** 211 test trên chạy trên **SQLite
in-memory**, KHÔNG phải PostgreSQL: fixture `history_engine` trong
`tests/conftest.py:39` hard-code `create_engine("sqlite://")` và bộ test đã
commit KHÔNG có cơ chế opt-in PostgreSQL — biến `HISTORY_DATABASE_URL` bị bỏ
qua. Bằng chứng "PostgreSQL 16.13 thật" của S087 đến từ script reviewer tự viết
ngoài bộ test, không từ bộ test này. Phiên này KHÔNG dán nhãn PG cho kết quả SQLite.

## Oracle Chưa Kiểm Được

`no-double-count`, đẳng thức `state(A,B) == state(B)`, `RESULT_REVISED` thật,
coverage/`REMOVED_CANDIDATE`, và accounting totals trên dữ liệu thật: tất cả
đều `NOT_TESTED` — chúng chỉ tồn tại khi có import thật. Bằng chứng synthetic
E2 đã có (`CHECK-PRA002-08 = PASS`) giữ nguyên nhãn synthetic.

## Findings

Không phát hiện defect production. Không có `DATA_SHAPE_UNKNOWN` (không có dữ
liệu thật để gặp hình dạng lạ). `CODE_REQUIRED = NO`.

`FIND-PRA002-RDA-N1` (NON_BLOCKING, governance/test-infra, KHÔNG phải production
path): bộ test đã commit không có đường chạy PostgreSQL, nên bằng chứng PG phải
tái tạo thủ công mỗi phiên. Không sửa trong phiên này — ngoài Scope Lock RDA và
là hardening. Ghi nhận cho phiên sau cân nhắc.

## OWNER_ACTION_REQUIRED

```
OWNER_ACTION_REQUIRED (1) — bắt buộc, mở khoá RDA-1..4:
Cung cấp HAI export kế toán thật (So_chi_tiet_ban_hang*.xlsx) của CÙNG MỘT
tháng vào môi trường chạy RDA:
  A = export giữa kỳ
  B = export muộn hơn của cùng tháng đó, chứa toàn bộ khoảng của A
Không sửa, không cắt file trước khi đưa vào — RDA cần đúng file kế toán xuất ra.

OWNER_ACTION_REQUIRED (2) — bắt buộc cho RDA-5:
Sau khi chạy A rồi B, xác nhận TƯỜNG MINH qua POST `xac-nhan-du` rằng snapshot
đã đủ cho range YYYY-MM-DD → YYYY-MM-DD của tháng đó. Không suy từ tên file,
mốc cuối tháng, hay số dòng.
```

RDA-6 đã xong, không cần Owner. Nếu Owner chỉ có MỘT export thật, phiên sau
phải mở CHANGE_BUDGET cho `tools/analysis/make_snapshot_variants` TRƯỚC khi
viết mã (headroom còn 40 LOC, nhiều khả năng không đủ).

## Ngân Sách

```
CHANGE_BUDGET   = 1.460 / 1.500   REMAINING = 40 LOC   (KHÔNG tiêu trong phiên này)
REVIEW_BUDGET   = USED 1 / 2      REMAINING = 1        (KHÔNG tiêu trong phiên này)
```

## Trạng Thái Check

```
CHECK-PRA002-08 = PASS (E2, giữ nguyên)
CHECK-PRA002-14 = NOT_TESTED  — BLOCKED_OWNER_INPUT (thiếu workbook thật)
CHECK-PRA002-15 = NOT_TESTED  — Production Acceptance, phụ thuộc CHECK-14
TASK-PRA-002    = IN_PROGRESS — KHÔNG DONE
```

## NEXT_VERTICAL_ACTION

Owner cung cấp đúng bằng chứng RDA còn thiếu (hai export thật cùng kỳ +
xác nhận đủ). KHÔNG bắt đầu production deployment. KHÔNG bắt đầu slice C2.
