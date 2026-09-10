# R5.4 — Nhãn Hãng/Nhóm hàng/Model cho dòng KHỚP TỰ ĐỘNG với Tracking

## Metadata

Status:
DONE

Current Status Reason:
Lỗi LUỒNG CHÍNH trên production đã sửa: dòng khớp TỰ ĐỘNG với Tracking
(`alias.map`/`board` theo mã, `inv.map` theo câu tên hàng) nay nhận
`model_label` · `brand` · `category_label` y như dòng do người xác nhận.
Nguồn mã thứ hai là cột `canonical_product_code` mà LẦN CHẠY đã lưu trên
chính dòng — không lời gọi Tracking nào thêm, không suy một chữ từ tên trên
sổ. `CHECK-R54-01` … `CHECK-R54-10` PASS (E1). Owner chỉ thị trực tiếp
trong phiên: sửa, tạo PR và merge (`DEC-221`).

Phase:
PHASE-01 — Engine tính toán

Task Mode:
MAJOR (repair lỗi production, mở lineage mới theo chỉ thị Owner — xem
`DEC-221` §3 về ngân sách)

Primary Agent Tier:
Claude Code (S152)

Escalation Tier:
Owner

Difficulty:
2/5

Risk:
2/5

Blast Radius:
2/5 (`V4.1` §4 — chấm theo FAILURE PATH):

```text
order_line_result_version.canonical_product_code  (cột ĐÃ CÓ từ TASK-105D)
   └─ business_queries._COLUMNS → details[...]["canonical_product_code"]
        └─ line_identity.tracking_identity_of()
             ├─ server._catalog_labels()            → 3 ô tab Nhân viên
             ├─ product_taxonomy.metadata_of()      → gộp R6 theo nhóm/hãng
             └─ brand_identity.bucket_for()         → báo cáo thương hiệu
```

Nó DỪNG ở đó. Bốn tính chất CẤU TẠO giữ nó không đi xa hơn: (1) hai cột
mới đọc KHÔNG tham gia một phép tính tiền nào — `CHECK-R54-06` đo tổng
trước/sau; (2) cổng `classification == MATCHED_TRACKING` ở cả ba nơi gọi
KHÔNG đổi — dòng OUT_OF_CATALOG/CONFLICT/chưa nhận diện vẫn `—`
(`CHECK-R54-03`, `CHECK-R54-05`); (3) quyết định của người trong Reports
vẫn THẮNG mã đã lưu (`CHECK-R54-04`); (4) không migration, không cột mới,
không đường ghi mới.

Project Profile:
PRODUCT

## 1. Lỗi production và nguyên nhân gốc

Owner báo sau `R5.3`: *"đã phân loại hãng + ngành hàng bên Tracking gần như
đủ cho các mã bán nhiều, chạy lại báo cáo vẫn không hiện ngành hàng + hãng,
tên mã hàng không được rút gọn"* (kèm ảnh chụp tab Nhân viên, 2026-09-10).

Điều tra (S152) đo từng tầng trên đường thật:

```text
Tracking chieuBoard()            ĐÚNG — xuất model_label/brand/category_label
capture_tracking_catalog         ĐÚNG — chở đủ ba trường
catalog_display + bản BỀN R5.3   ĐÚNG — bản chiếu có nhãn của MỌI mã board
resolver (production)            ĐÚNG — dòng khớp qua inv.map → Resolved,
                                 canonical_product_code được ghi vào DB
_catalog_labels/metadata_of/
  bucket_for                     ĐỨT — chỉ tra mã qua confirmed_identities()
                                 (mapping CONFIRMED do người xác nhận)
```

Resolve ở chế độ production là phép đọc thuần (`INV-70`): khớp tự động
KHÔNG tạo mapping trong store Product Identity. Nên mọi dòng khớp tự động —
tức đường sản xuất chính, và đúng tập dòng CÓ giá MIN — không bao giờ có
khoá trong bảng nhãn. `CHECK-R53-07` của `R5.3` đã đo và CHỐT đúng hành vi
này thành spec ("có MIN nhưng không CONFIRMED ⟹ vẫn `—`"), nên `R5.3` xanh
mà production vẫn sai so với brief `R5` §5.

Tái hiện E1 (trước sửa), bài tạm trên bộ khung `R5.3`:

```text
inv.map: N_MAYLANHTEST2 → 55Q6FA ; KHÔNG confirm gì trong Reports ; POST /run
order_line_result_version: canonical_product_code='55Q6FA',
                           pending_reasons KHÔNG có IDENTITY_UNRESOLVED
tab Nhân viên: line-product='Máy lạnh Test-2' · line-brand='—' · line-category='—'
```

## 2. Scope Lock

TRONG phạm vi:

```text
app/web/business_queries.py           _COLUMNS +identity_namespace,
                                      +canonical_product_code (cột ĐÃ CÓ);
                                      details +2 trường cùng tên
app/web/line_identity.py              +tracking_identity_of()
app/web/server.py                     _catalog_labels(details);
                                      _catalog_projection_warning dùng
                                      tracking_identity_of
app/web/product_taxonomy.py           metadata_of dùng tracking_identity_of
app/web/brand_identity.py             bucket_for dùng tracking_identity_of
tests/test_r54_nhan_cho_dong_khop_tu_dong.py   MỚI
tests/test_snapshot_repository.py     fixture result_line: mặc định KHÔNG
                                      có mã Tracking (trước đây gắn mã giả
                                      `A1` cho mọi dòng mà không ai đọc)
tests/test_r53_durable_tracking_labels.py      docstring CHECK-R53-07
docs/**, PROJECT/**                   governance
```

NGOÀI phạm vi:

```text
Tracking (mọi thứ)                    READ-ONLY REFERENCE — KHÔNG đổi
resolver / identity store / mapping   FORBIDDEN — không ghi mapping cho dòng
                                      khớp tự động (INV-70 giữ nguyên)
công thức tiền / MIN / chốt kỳ        FORBIDDEN
schema / migration                    KHÔNG cần — hai cột đã tồn tại
rút mã từ tên trên sổ                 FORBIDDEN (D-04, ADR-111 §3)
```

## 3. Thiết kế

`line_identity.tracking_identity_of(detail, identities)` là nguồn mã DUY
NHẤT cho nhãn, theo thứ tự: (1) mapping `CONFIRMED` của người trong Reports;
(2) `canonical_product_code` lần chạy đã lưu, chỉ khi
`identity_namespace = TRACKING`. Không có (3). Hàm KHÔNG quyết định dòng có
được nhận nhãn hay không — cổng đó vẫn là `classification == MATCHED_
TRACKING` ở từng nơi gọi.

Không phải phương án "ghi mapping cho dòng khớp tự động": làm thế đổi ngữ
nghĩa store Product Identity (một mapping = một quyết định của người) và mở
đường cho `IDENTITY_CONFLICT` giả khi Tracking đổi `inv.map`.

## 4. Vấn đề KHÔNG nằm trong task này (đã điều tra, ghi lại)

- **Độ phủ lớp "câu tên hàng → mã".** Phân loại hãng/ngành trên board
  Tracking KHÔNG làm dòng nào khớp thêm. Dòng chưa khớp cần được phân loại
  qua màn "Phân loại theo tên hàng" của Tracking (`inv/map`) hoặc confirm
  trong Reports. Đây là vận hành, không phải code.
- **Giá MIN `—` ở một số ngày.** Ba dòng `—` trên ảnh chụp rơi vào 06/09 và
  09/09 trong khi 07/08/10-09 có giá — nghi ngờ thiếu bản ngày
  (`TRACKING_DAILY_MIN_SOURCE_UNAVAILABLE`). Chưa xác minh; cần đọc
  `pending_reasons` của lần chạy trên production.

## Completion Gate

Dùng `governance/core/TASK_COMPLETION_GATE_STANDARD.md` và `governance/core/EVIDENCE_STANDARD.md`.

### Functional

#### CHECK-R54-01
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Dòng khớp tự động qua `inv.map` (KHÔNG confirm gì trong Reports, tiền đề
đo bằng SQL: `canonical_product_code='55Q6FA'`, `confirmed_identities()=={}`)
hiện model gọn + hãng + nhóm hàng, tên trên sổ còn ở tooltip —
`test_an_auto_matched_line_shows_model_brand_and_category`.

Executed By:
Claude Code (S152)

Timestamp:
2026-09-10

#### CHECK-R54-02
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Nhãn của dòng khớp tự động sống qua restart (dựng lại từ bản BỀN R5.3) —
`test_an_auto_matched_line_keeps_its_labels_after_a_restart`.

Executed By:
Claude Code (S152)

Timestamp:
2026-09-10

#### CHECK-R54-03
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Owner đánh dấu OUT_OF_CATALOG sau lần chạy ⟹ tên thô + `—`, dù cột đã lưu
còn mã — `test_a_line_the_owner_marks_out_of_catalog_loses_the_stored_code`.

Executed By:
Claude Code (S152)

Timestamp:
2026-09-10

#### CHECK-R54-04
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Owner confirm một mã KHÁC mã lần chạy đã lưu ⟹ màn hình theo Owner ngay —
`test_a_human_confirmation_beats_the_code_the_run_stored`.

Executed By:
Claude Code (S152)

Timestamp:
2026-09-10

#### CHECK-R54-05
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Dòng KHÔNG khớp vẫn tên thô + `—`; `tracking_identity_of` trả `None` cho
namespace khác TRACKING / mã rỗng / mã trắng —
`test_an_unmatched_line_still_shows_the_raw_name_and_dashes`,
`test_tracking_identity_of_never_invents_a_code` (4 ca).

Executed By:
Claude Code (S152)

Timestamp:
2026-09-10

#### CHECK-R54-06
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Tổng giá nhập/giá bán/lợi nhuận/DS quy đổi + số dòng KHÔNG đổi giữa có nhãn
và mất cache — `test_labels_for_auto_matched_lines_change_no_money`. Golden
baseline: xem `CHECK-R54-09`.

Executed By:
Claude Code (S152)

Timestamp:
2026-09-10

#### CHECK-R54-07
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Cảnh báo bản chiếu hình dạng 1 nổi lên cho dòng khớp tự động khi capture
không mang nhãn — `test_the_projection_warning_covers_auto_matched_lines`.

Executed By:
Claude Code (S152)

Timestamp:
2026-09-10

#### CHECK-R54-08
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Hai cổng còn lại đọc mã đã lưu: R6 `metadata_of` → STATE_MATCHED đủ ba
trường và vẫn chặn theo trạng thái nhận diện; PHB-06 `bucket_for` → bucket
hãng, BRAND_ABSENT khi bản chiếu không biết mã —
`test_r6_metadata_reads_the_stored_code`,
`test_r6_metadata_still_gates_on_identity_state`,
`test_brand_bucket_reads_the_stored_code`,
`test_tracking_identity_of_prefers_the_human_decision`.

Executed By:
Claude Code (S152)

Timestamp:
2026-09-10

### Regression

#### CHECK-R54-09
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Full `pytest` (trừ hai suite trình duyệt): 3640 passed / 23 skipped / 0 failed (nền S151: 3628 / 24 / 0; +16 bài mới, không bài nào bị xoá). R5.3 (19 bài)
xanh nguyên, kể cả `CHECK-R53-07` (dòng ở đó CHƯA khớp — chỉ docstring đổi).
Golden `tests/test_golden_baseline.py` xanh trong cùng lượt chạy.

Executed By:
Claude Code (S152)

Timestamp:
2026-09-10

#### CHECK-R54-10
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Validators governance: structure/project_state/evidence/task_completion
PASS; reference_integrity đúng 4 baseline cũ. `git diff --check` sạch.
Nguyên văn: `docs/sessions/S152-r54-nhan-cho-dong-khop-tu-dong.md` §4.

Executed By:
Claude Code (S152)

Timestamp:
2026-09-10

#### CHECK-R54-11
Priority:
RECOMMENDED

Status:
NOT_TESTED

Evidence Level:
E0

Evidence:
Owner nghiệm thu trên production sau deploy: dòng đã có giá MIN hiện model
gọn + Hãng + Nhóm hàng. Chỉ Owner đóng được.

Executed By:
—

Timestamp:
—

## Tiêu Chí Hoàn Thành (Exit Criteria)
- [x] 100% REQUIRED checks PASS
- [x] Không có lỗi nghiêm trọng (critical) chưa xử lý
- [x] Đạt mức evidence yêu cầu (Risk 2/5 → E1 cho REQUIRED)
- [x] Tài liệu bắt buộc đã được cập nhật
- [x] Tiến độ dự án đã được cập nhật
- [x] Đã viết Session Handoff

## Đăng Ký File Đã Thay Đổi (Changed Files Registry)

Created:
- `tests/test_r54_nhan_cho_dong_khop_tu_dong.py`
- `docs/tasks/R5-4-nhan-cho-dong-khop-tu-dong.md`
- `docs/sessions/S152-r54-nhan-cho-dong-khop-tu-dong.md`

Modified:
- `app/web/business_queries.py`
- `app/web/line_identity.py`
- `app/web/server.py`
- `app/web/product_taxonomy.py`
- `app/web/brand_identity.py`
- `tests/test_snapshot_repository.py`
- `tests/test_r53_durable_tracking_labels.py`
- `docs/tasks/R5-3-nhan-hang-nhom-hang-song-qua-restart.md` (ghi chú CHECK-R53-07)
- `PROJECT/PROJECT_PROGRESS.md`, `PROJECT/PROJECT_DECISIONS.md`,
  `PROJECT/REVIEW_BUDGET_LEDGER.md`

Deleted:
- không

Migration Impact:
- không (hai cột đã tồn tại từ `TASK-105D`)
