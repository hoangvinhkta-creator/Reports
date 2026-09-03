# S096 — TASK-PRA-003 MAJOR Implementation (Tổng Quan + Nhân Viên)

## Metadata

```
SESSION                : S096 — PRA-003 MAJOR Implementation
NGÀY                   : 2026-09-03
TASK MODE              : MAJOR
TASK                   : TASK-PRA-003 — Tổng Quan + Nhân Viên
TRẠNG THÁI TASK SAU PHIÊN: IN_PROGRESS (KHÔNG phải DONE)
PROJECT PROFILE        : PRODUCT
RISK                   : 3        BLAST RADIUS : 3/5
BASE_CANONICAL         : claude/extract-upload-repo-gq2ws4 @ facf090c782b022730ecc5f1cf0d0b02e29ca8d7
FROZEN_CONTRACT_SHA    : c12c5635b5e4298a9584b5fa93e21762c0d70c5b
NHÁNH IMPLEMENT        : claude/pra-003-roadmap-finalization-di33bn
```

Phiên này TRIỂN KHAI hợp đồng đã freeze tại S095. Không thiết kế lại task,
không mở lại discovery, không thêm yêu cầu.

## Xác Minh Thẩm Quyền (đầu phiên)

```
git rev-parse origin/claude/extract-upload-repo-gq2ws4
  → facf090c782b022730ecc5f1cf0d0b02e29ca8d7   ✓ khớp BASE_SHA đã freeze
git rev-parse origin/claude/pra-003-roadmap-finalization-di33bn
  → c12c5635b5e4298a9584b5fa93e21762c0d70c5b   ✓ khớp HEAD kỳ vọng
```

`CANONICAL_MOVED = NO`. Ready Gate R1 vẫn ĐẠT tại thời điểm implement.

## Thứ Tự Triển Khai (theo đúng chỉ thị)

1. `app/web/analytics_queries.py` + 22 test ngữ nghĩa truy vấn — PASS trước khi đi tiếp.
2. `app/web/analytics_presentation.py` + 20 test trình bày — PASS trước khi đi tiếp.
3. Route/wiring trong `app/web/server.py`.
4. Template (`tong_quan.html`, `_pipeline_bits.html`, `nhan_vien.html`, `layout.html`).
5. CSS.
6. 25 test route/integration (gồm oracle golden độc lập).

Không bắt đầu từ HTML rồi suy ngược phép tính.

## Quyết Định Triển Khai Đáng Ghi Lại

### 1. "Toàn bộ dữ liệu" LOẠI TRỪ dòng thiếu ngày bán

Bộ lọc kỳ trong `analytics_queries._period()` LUÔN kèm `sale_date IS NOT NULL`,
kể cả khi không có `date_from`/`date_to`.

Đây là điều frozen contract mục 6 nói (`"Toàn bộ dữ liệu"` = khoảng
`min(sale_date) → max(sale_date)`) và mục 9 `FACT #3` nói tiếp ("tổng của
'Toàn bộ dữ liệu' CÓ THỂ nhỏ hơn tổng thật" — chỉ đúng nếu dòng không ngày
bán bị loại). Bản triển khai đầu tiên KHÔNG lọc gì khi không có bounds, và
chính test `test_lines_without_a_sale_date_fall_out_of_every_period_and_are_counted`
bắt được sai lệch đó. `undated_lines()` là chỗ DUY NHẤT phơi các dòng ấy ra.

### 2. Kỳ mặc định = "Toàn bộ dữ liệu"

Frozen contract không chốt kỳ mặc định. Chọn "Toàn bộ dữ liệu" vì nó là kỳ
duy nhất (a) không bao giờ giấu bớt dòng nào, (b) không cần kỳ so sánh, nên
trang mở lần đầu không thể nói sai. `ky` lạ cũng rơi về đây thay vì dựng một
bảng toàn số 0 cho một tháng không tồn tại.

### 3. Coverage viết `N / M dòng`, KHÔNG viết phần trăm

Hai lý do: `0 / 351 dòng` nói thẳng "chưa dòng nào chắc chắn" trong khi `0%`
dễ bị đọc nhầm thành "lãi bằng không"; và hai coverage của D1 có TỬ SỐ khác
nhau — viết cả tử lẫn mẫu buộc người đọc thấy điều đó thay vì so hai phần
trăm như thể chúng cùng nghĩa. Đồng thời tránh mọi nhập nhằng với quy tắc
"không bao giờ hiện `0%`" của ô so kỳ trước.

### 4. Kỳ trước có `lines == 0` ⟹ MỌI ô so sánh để trống

Không đọc `previous["orders"] == 0` như thể "kỳ trước bán được 0 đơn". Nếu
đọc như vậy thì tháng 09/2026 (tháng 08 trống) sẽ hiện `+40 đơn`, một câu
sai. `analytics_presentation._comparison()` chuyển vế "kỳ trước" thành `None`
khi kỳ đó không có dòng nào, và `delta()` trả `—` cho cả Δ lẫn Δ%.

### 5. Khẳng định test neo vào ĐÚNG Ô, không quét cả body

Các ô số mang `data-metric`. "Ô lợi nhuận không được hiện `0`" là khẳng định
về MỘT Ô; một body chứa chữ "0" trong coverage `0 / 351 dòng` vẫn hoàn toàn
đúng. Quét cả body sẽ tạo ra một test hoặc sai (bắt nhầm) hoặc yếu (phải nới
lỏng để pass).

## Finding

### FIND-PRA003-01 — provenance của block `pricing` trong golden expected — NON-BLOCKING

`Phân loại: HARDENING (tài liệu/oracle), không BLOCKING.`

O-C (mục 16) khẳng định: trên kỳ golden, LN KPI = `—` với coverage `0/351`,
lấy tiền đề từ `pricing.price_source_distribution = {Pending: 351}` trong
`tests/fixtures/golden/expected/period_2026_01.json`.

`FACT` đo được trong phiên này: file expected đó do
`tests/fixtures/golden/build_expected.py` sinh bằng `run_import(fixture, CONFIG_DIR)`
TRẦN — không nạp historical-confirmed registry. Đường mà PRA-003 thực sự đọc
là đường production `demo.run_demo` → `app.composition.run_import_production`,
có nạp registry canonical đã commit. Trên CÙNG fixture đó, đường production
cho:

```
status       : AUTO 2 · PENDING 349
price_source : OWNER_MANUAL_LEGACY_CONFIRMATION 2 · Pending 349
```

Hai con số đều ĐÚNG cho cấu hình của mình; không có defect nào trong
`app/history/**`, `app/web/history_store.py` hay `analytics_queries`.

Vì sao KHÔNG blocking (V4.1 §5, task mục 14): dashboard báo cáo đúng SỰ THẬT
của dữ liệu đã lưu — 2 dòng AUTO thật thì coverage `2 / 351` là con số trung
thực. Không đe doạ tính trung thực của kết quả quản lý, no-double-count, tách
nguồn, an toàn NULL/coverage, PII, hay real vertical.

Xử lý trong phiên: test khoá con số THẬT của đường production thay vì mượn
con số của cấu hình khác (mượn sẽ là một oracle nói dối về chính hệ thống
đang chạy). Tính chất mà O-C tồn tại để bảo vệ — "thiếu lợi nhuận ⟹ `—`,
không `0`" — được chứng minh riêng trên dữ liệu có kiểm soát nơi KHÔNG dòng
nào đủ điều kiện (`test_a_period_where_nothing_is_eligible_renders_a_dash_and_zero_coverage`,
coverage `0 / 3 dòng`).

`RE-TRIGGER CONDITION`: nếu Owner hoặc Independent Reviewer muốn O-C đọc
đúng nguyên văn trên kỳ golden, việc cần làm là ghi rõ trong mục 16 rằng
block `pricing` mô tả cấu hình `run_import` trần — KHÔNG phải sửa mã, và
KHÔNG phải đổi registry canonical đã commit.

## Kết Quả Check

```
01 PASS   02 PASS   03 PASS   04 PASS   05 PASS   06 PASS
07 NOT_TESTED (chờ Owner nghiệm thu trên production — không bịa)
08 PASS   09 PASS   10 PASS   11 PASS
12 NOT_TESTED (Independent Review E2 — phiên này KHÔNG tự review mình)
13 PASS   14 PASS (đo thật: chậm nhất 64 ms trên 12.000 dòng)
```

`BLOCKING_FINDINGS = 0` · `repair_cycles_used = 0` (phiên implement KHÔNG
tiêu review repair cycle).

## Bàn Giao (Handoff)

Việc tiếp theo, đúng một việc: **Independent Review E2 (CHECK-PRA003-12)**
theo `governance/templates/E2_INDEPENDENT_REVIEW_TEMPLATE.md`, artifact lưu
tại `docs/reviews/`. Reviewer phải chạy LẠI độc lập tối thiểu CHECK-01, -02,
-03, -04, -05 và phân loại mọi finding theo V4.1 §5/§7.

Sau đó: Controlled Integration vào canonical, deploy, rồi Owner nghiệm thu
CHECK-PRA003-07 trên production tháng 09/2026 (`40 đơn · 61 dòng · AUTO 15 ·
Review 25`, ô so tháng trước TRỐNG). Phiên này KHÔNG tích hợp canonical và
KHÔNG đánh dấu task DONE.

Môi trường chạy test: clone container ban đầu là shallow (58 commit) và làm
`tests/test_105d_boundaries.py::TestG25GoldenBaselineUnchanged` FAIL với
`fatal: bad object 740f396…`. `git fetch --unshallow` khắc phục. Reviewer nên
unshallow trước khi đo baseline.
