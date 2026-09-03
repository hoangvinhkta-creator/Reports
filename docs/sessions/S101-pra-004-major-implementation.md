# S101 — TASK-PRA-004 MAJOR Implementation (Bán Hàng + Chi Tiết Đơn/Dòng)

## Metadata

```
SESSION                  : S101 — PRA-004 MAJOR Implementation
NGÀY                     : 2026-09-03
TASK MODE                : MAJOR
TASK                     : TASK-PRA-004 — Bán Hàng + Chi Tiết Đơn/Dòng + Review Visibility (CHỈ-ĐỌC)
TRẠNG THÁI TASK SAU PHIÊN: IN_PROGRESS (KHÔNG phải DONE)
PROJECT PROFILE          : PRODUCT
RISK                     : 3        BLAST RADIUS : 3/5
BASE_CANONICAL           : claude/extract-upload-repo-gq2ws4 @ 8181cebe0619a9c8d12604168a90914c04b3692f
FROZEN_CONTRACT_SHA      : 46a5cdb08bbac77eb4c6a7a3ad483edba988b7f9
NHÁNH IMPLEMENT          : claude/pra-004-sales-review-detail-0b2z4w
```

Phiên này TRIỂN KHAI hợp đồng đã freeze tại S100. Không thiết kế lại contract,
không mở lại discovery, không thêm yêu cầu.

## Xác Minh Thẩm Quyền (đầu phiên)

```
git rev-parse origin/claude/extract-upload-repo-gq2ws4
  → 8181cebe0619a9c8d12604168a90914c04b3692f   ✓ khớp EXACT BASE_SHA đã freeze
git rev-parse origin/claude/pra-004-sales-review-detail-0b2z4w
  → 46a5cdb08bbac77eb4c6a7a3ad483edba988b7f9   ✓ khớp EXACT HEAD hợp đồng
git merge-base --is-ancestor origin/claude/extract-upload-repo-gq2ws4 HEAD
  → CANONICAL_IS_ANCESTOR_OK
git status --porcelain                          → rỗng (working tree sạch)
```

`CANONICAL_MOVED = KHÔNG`. `CONTRACT_HEAD_MOVED = KHÔNG`.
`scripts/branch_authority_check.sh` → `AUTHORITY_OK`, `DIVERGENCE = WITHIN_LIMITS`.

## Thứ Tự Triển Khai (theo đúng chỉ thị mục 3)

1. `app/web/sales_queries.py` — tầng SQL, viết TRƯỚC mọi thứ khác.
2. Mở rộng `app.beta_presentation.REASON_DISPLAY_LABELS` (14 mã còn lại).
3. `app/web/sales_presentation.py`.
4. Hai route trong `app/web/server.py`.
5. Hai template + macro `reason_row` + tab điều hướng.
6. CSS.
7. 89 test (đơn vị → route → integration).

Không bắt đầu từ HTML rồi suy ngược business semantics.

## Xác Minh Oracle TRƯỚC Khi Viết Mã

Trước khi viết một dòng production nào, phiên này chạy lại ĐƯỜNG PRODUCTION
THẬT trên fixture golden (`build_price_composition` → `run_import_production`
→ `export_report` → `present_lines` → `history_writer.write_run_history`) rồi
truy vấn SQL trên dữ liệu đã persist, để kiểm chứng oracle của S100 còn đúng:

```text
351 dòng · 254 đơn
Đơn TOÀN AUTO        : 1   (BH62063)
Đơn CẦN KIỂM TRA     : 253
Đơn TRỘN AUTO+PENDING: 1   (BH62439 — 1 dòng AUTO + 3 dòng PENDING)
Phân bố số dòng/đơn  : {1: 191, 2: 41, 3: 16, 4: 3, 5: 1, 6: 1, 7: 1}
Reason/dòng          : {0: 2, 5: 341, 6: 8}
BH62439: doanh thu 66.000.000 · LN kế toán 500.000 (1/4) · LN KPI 400.000 (1/4)
```

Toàn bộ khớp EXACT với mục 4.3 / 20.1 / 20.3 của hợp đồng. Oracle KHÔNG bị
viết ngược từ kết quả triển khai.

## Quyết Định Triển Khai Đáng Ghi Lại

### 1. Thứ tự dòng cần khoá phụ ngoài `occurrence_index`

Hợp đồng mục 6 nói sắp xếp theo `occurrence_index`. Đo thực tế: CẢ BỐN dòng
của `BH62439` mang `occurrence_index = 1` — chỉ số này đếm theo *(đơn, sản
phẩm)*, nên các dòng KHÁC sản phẩm trong cùng một đơn đều bằng 1. Riêng
`occurrence_index` vì vậy để lại một `ORDER BY` HOÀ, tức thứ tự dòng không xác
định giữa các lần chạy.

Khoá phụ đã chọn: `current_source_version_id`. Nó nằm trong đúng hai con trỏ
mà hợp đồng cho phép đọc, và tăng dần theo `source_row`
(`extraction.build_source_lines` sắp xếp theo `source_row` trước khi ghi) —
đo được:

```text
svid 45 · occ 1 · source_row 50 · Tủ lạnh Panasonic NR-BX471GPKV
svid 46 · occ 1 · source_row 51 · Máy Giặt Sấy LG FV1414H3BA
svid 47 · occ 1 · source_row 52 · Điều hòa Daikin FTHF25XVMV
svid 48 · occ 1 · source_row 53 · Máy lạnh Daikin Inverter 2 HP FTKB50ZVMV
```

Giới hạn trung thực, đã ghi trong docstring của `order_detail` và KHÔNG được
nới: một dòng bị SỬA nhận version nguồn mới và vì thế chuyển xuống CUỐI đơn.
Thứ tự vẫn ỔN ĐỊNH và vẫn phản ánh trạng thái hiện hành, chỉ không còn trùng
vị trí trong sổ gốc. Không đọc thêm bảng nào để "sửa" điều đó — làm vậy sẽ mở
bề mặt truy vấn ra ngoài hai con trỏ hiện hành.

### 2. `sales_queries` KHÔNG import helper riêng tư của `analytics_queries`

`_joined()`, `_period()` và `_read()` được viết lại trong `sales_queries` thay
vì import từ `analytics_queries`. Lý do KHÔNG phải "tiện": CHECK-PRA004-01
yêu cầu bằng chứng AST rằng **chính** `sales_queries` xuất phát từ
`order_line_current` và đi qua hai con trỏ hiện hành. Nếu phép nối nằm ở
module khác, cây AST của `sales_queries` không còn chứa bằng chứng đó và check
trở thành một khẳng định rỗng.

Sự trùng lặp này được hợp đồng mục 23 giới hạn ở TẦNG TRUY VẤN. Ở tầng trình
bày, `sales_presentation` **import và tái dụng** `money`, `count`, `coverage`,
`profit`, `period_label`, `period_options`, `period_value`, `UNKNOWN_EMPLOYEE`
— không chép lại một hàm nào trong số đó. Rủi ro lệch nhau giữa hai `_period()`
được canh bằng CHECK-PRA004-07 (reconcile trực tiếp với `period_totals()` trên
cả hai loại kỳ).

### 3. `pending_reasons_json` hỏng ⟹ danh sách rỗng, KHÔNG phải HTTP 500

`sales_queries._reasons()` nuốt `ValueError`/`TypeError` khi giải mã JSON. Đây
là lựa chọn có chủ đích và có giới hạn: dòng vẫn hiện đúng trạng thái
`CẦN KIỂM TRA` (trạng thái đến từ cột `status`, không phải từ JSON), nên mất
lý do là mất MỘT PHẦN câu trả lời, còn để cả trang chết là mất TẤT CẢ. Không
có đường nào cho phép trạng thái sai đi kèm.

### 4. Nhãn trạng thái đi kèm cờ boolean, không chỉ chuỗi

`order_row`/`line_row` trả về CẢ `status` (chuỗi hiển thị) và `review`
(boolean). Template dùng boolean để chọn class CSS thay vì so sánh chuỗi
tiếng Việt — so chuỗi hiển thị trong template là con đường quen thuộc dẫn tới
một trạng thái thứ ba lặng lẽ ra đời.

### 5. Cảnh báo coverage một phần là CỜ RIÊNG, không phải suy luận của template

`sales_presentation.order_detail()` tính `partial_coverage` ở tầng Python và
trang in cảnh báo dựa trên nó. Đặt phép so sánh này trong Jinja sẽ khiến
failure path nghiêm trọng nhất của slice (Owner đọc "lãi 500.000" cho một đơn
66 triệu mà chỉ 1/4 dòng có giá trị) phụ thuộc vào một biểu thức template
không test nào của tầng dữ liệu bắt được.

## Kết Quả Kiểm Thử

```
Focused PRA-004 : 89 passed in 6.55s
PRA-003         : 67 passed in 7.07s   (3 file test KHÔNG bị sửa một dòng)
Golden Baseline : 58 passed, 2 skipped in 6.45s
FULL SUITE      : 1962 passed, 11 skipped in 78.83s
Baseline 8181ceb: 1873 passed, 11 skipped in 77.08s   (đo lại bằng git worktree)
                  → chênh +89 = ĐÚNG số test mới; skip KHÔNG đổi
```

Validators:

```
GOVERNANCE STRUCTURE : PASS
PROJECT STATE        : PASS
EVIDENCE VALIDATION  : PASS (128 REQUIRED PASS record)
TASK COMPLETION      : PASS (11 DONE task)
REFERENCE INTEGRITY  : FAIL — ĐÚNG 3 issue REM-T06 pre-existing, KHÔNG thêm issue mới
git diff --check     : sạch trên DẢI COMMIT 8181cebe..HEAD
branch authority     : AUTHORITY_OK
```

## Ghi Chú Môi Trường (KHÔNG phải finding của PRA-004)

Lần chạy full suite ĐẦU TIÊN có một FAIL:

```
tests/test_105d_boundaries.py::TestG25GoldenBaselineUnchanged::
  test_protected_golden_artifacts_match_the_task_105e_review_base
→ fatal: bad object 740f396acb11cf279f303f09ea22dffd0ca95462
```

Nguyên nhân: repo được clone SHALLOW (`git rev-parse --is-shallow-repository`
→ `true`, 58 commit), nên object lịch sử mà test cần không tồn tại cục bộ. Sau
`git fetch --unshallow` (`--is-shallow-repository` → `false`) test PASS và
toàn bộ suite xanh. Đây là vấn đề MÔI TRƯỜNG, phân loại riêng theo chỉ thị
mục 26 — không phải hồi quy do thay đổi của phiên này. Các dependency Python
(`SQLAlchemy`, `Flask`, `pytest`) cũng phải cài vào `.venv` cục bộ trước khi
chạy được test; `.venv` đã có trong `.gitignore`.

## Findings

### FIND-PRA004-04 — `DOC_INCONSISTENCY` · KHÔNG BLOCKING · KHÔNG tự sửa

Dòng mở đầu Completion Gate của file task viết *"13 check: **11 REQUIRED** ·
2 RECOMMENDED"*, nhưng phần liệt kê phía dưới có **14** check, trong đó
CHECK-PRA004-13 là RECOMMENDED và 13 check còn lại là REQUIRED (tức
**13 REQUIRED · 1 RECOMMENDED**). Tiêu chí Exit số 1 cũng viết "11/11 REQUIRED".

Đây là sai lệch SỐ ĐẾM trong tài liệu, KHÔNG phải một check bị thiếu hay bị
làm yếu: cả 14 check đều tồn tại đầy đủ và không check nào bị xoá hay hạ
priority trong phiên này.

Phiên implement KHÔNG tự sửa con số đó: header và Exit Criteria thuộc phần
Completion Gate đã FROZEN, và sửa chúng phải đi qua
`COMPLETION GATE CHANGE PROPOSAL` (mục Completion Gate). Ghi lại để Independent
Reviewer hoặc Owner quyết.

RE-TRIGGER CONDITION: giải quyết trước khi đóng `TASK-PRA-004` = DONE, vì Exit
Criteria số 1 đếm theo con số này.

### Trạng thái các finding của S100

- `FIND-PRA004-01` (TRUTHFULNESS_CONSTRAINT) — GIỮ NGUYÊN. Trang KHÔNG in công
  thức và KHÔNG tuyên bố tự dẫn xuất lợi nhuận; `delivery_cost` vẫn DEFER.
  RE-TRIGGER CONDITION không kích hoạt trong phiên này (2/2 dòng AUTO của
  fixture vẫn có `delivery_cost = NULL`).
- `FIND-PRA004-02` (DOC_INCONSISTENCY) — ĐÃ GIẢI bằng thiết kế:
  `app/web/analytics_queries.py` và `tests/test_analytics_queries.py` KHÔNG bị
  chạm; `sales_queries` mang hàng rào PII RIÊNG, hẹp hơn đúng một trường.
- `FIND-PRA004-03` (HARDENING, DEFER) — GIỮ NGUYÊN. Nhánh nhiều nhân viên đã
  được triển khai cho n ≥ 1 và có test bằng dữ liệu tổng hợp
  (`test_a_multi_employee_order_names_every_employee_on_the_page`), nhưng vẫn
  CHƯA có dữ liệu production để kiểm — RE-TRIGGER CONDITION giữ nguyên.

**BLOCKING_FINDINGS = 0.**

## Điều KHÔNG Làm Trong Phiên Này

- Không pagination (đo được 85,2 ms / 12.000 dòng — xa dưới ngưỡng 3 giây).
- Không lọc/sắp xếp/tìm kiếm, không export, không biểu đồ.
- Không workflow duyệt/từ chối/gán/bình luận; không một câu ghi nào.
- Không chạm `analytics_queries` / `analytics_presentation` / test PRA-003 /
  `tools/db/**` / `app/modules/**` / `tests/fixtures/golden/**` / Tracking.
- Không sửa `governance/core/V4_1_POLICY_FREEZE.md`, không sửa oracle nghiệm
  thu, không đánh dấu Independent Review hay Owner Acceptance là PASS.

## Bàn Giao (Handoff)

```
TASK-PRA-004            : IN_PROGRESS
CHECK PASS              : 12/14 (11/13 REQUIRED + 1/1 RECOMMENDED)
CHECK-PRA004-12         : NOT_TESTED — Independent Review E2 (bước kế tiếp)
CHECK-PRA004-14         : NOT_TESTED — Owner Production Acceptance Tháng 09/2026
repair_cycles_used      : 0 / 1  — phiên implement KHÔNG tiêu cycle
BLOCKING_FINDINGS       : 0
SCOPE_DRIFT             : NO
```

Bước kế tiếp: **PRA-004 Independent Review E2** theo
`governance/templates/E2_INDEPENDENT_REVIEW_TEMPLATE.md`, artifact
`docs/reviews/TASK-PRA-004-INDEPENDENT-REVIEW-RECORD` (file DỰ KIẾN). Reviewer phải
RECOMPUTE ĐỘC LẬP bằng SQL thô (KHÔNG qua `sales_queries`) cho danh sách đơn
và cho chi tiết `BH62439` rồi mới đem so.
