# S145 — R6 REPAIR-1: sửa toàn bộ finding Independent Review vòng 1

Ngày: 2026-09-09
Task Mode: MAJOR (repair cycle)
Quyết định nền: `DEC-207`
Kết quả phiên: **cả BỐN mục của vòng 1 ĐÃ SỬA trong ĐÚNG MỘT repair cycle.**
`R6` trở lại `IMPLEMENTED`. KHÔNG mở PR, KHÔNG merge, KHÔNG deploy, KHÔNG làm
`R7`. Repo Tracking KHÔNG đổi một dòng code nào.

---

## 1. Preflight

### 1.1 Nhánh mặc định THẬT, HEAD, và working tree

```text
Reports   nhánh mặc định: claude/extract-upload-repo-gq2ws4  (KHÔNG phải "main")
          origin HEAD:    05f2b443e66ee4702d03c003d5f1f960b5765f8d
Tracking  nhánh mặc định: main
          origin HEAD:    66787c0fb0d867a308c632e7f163cddd0c9dd0f2

$ git -C Reports  status --porcelain   → RỖNG
$ git -C Tracking status --porcelain   → RỖNG
```

### 1.2 Lineage — implementation + review record, xác nhận bằng git

```text
R6 implementation HEAD đã review   56aca4c91bd788b1e14d7f71b9246d1577255c1a
Review docs-only commit            b3fa809f57778e0ca183a5f32e5a79d34300321e
                                   = HEAD của claude/r6-independent-review-dvuiiw

$ git merge-base --is-ancestor 56aca4c b3fa809 && echo YES      → YES
$ git log --oneline 56aca4c..b3fa809
  b3fa809 S144: Independent Review R6 — REPAIR_REQUIRED (CHECK-R6-31 = FAIL)

$ git diff --stat 56aca4c..b3fa809 -- app/ tests/ config/ scripts/ tools/
  → RỖNG        (xác nhận commit review là DOCS-ONLY)
```

### 1.3 Divergence — không có, nên không chép tay gì

```text
$ git merge-base --is-ancestor origin/claude/extract-upload-repo-gq2ws4 b3fa809
  → YES        (nhánh mặc định LÀ ancestor của b3fa809)
$ git log --oneline b3fa809..origin/claude/extract-upload-repo-gq2ws4
  → RỖNG       (nhánh mặc định KHÔNG tiến lên kể từ khi R6 mở)
```

Vì `b3fa809` chứa ĐỦ implementation + review record và nhánh mặc định không
tiến lên, nhánh làm việc được **fast-forward** tới `b3fa809`:

```text
$ git checkout claude/r6-business-analytics-dashboard-it73x5
$ git merge --ff-only b3fa809     → fast-forward, working tree sạch
```

Không `cherry-pick`, không `rebase`, không chép tay một dòng mã hay tài liệu
nào. Nhánh repair vì thế mang cả ba lớp lịch sử: implementation `R6`, bản ghi
Independent Review, và repair.

### 1.4 Đã đọc trước khi sửa một dòng nào

```text
docs/reviews/R6-INDEPENDENT-REVIEW-RECORD.md   (toàn bộ, đặc biệt §2.4, §4.2, §7)
docs/sessions/S144-r6-independent-review.md
docs/sessions/S143-r6-dashboard-phan-tich.md
docs/spec/R6-EXECUTION-BRIEF.md
docs/tasks/R6-dashboard-phan-tich-kinh-doanh.md
PROJECT/REVIEW_BUDGET_LEDGER.md → "Root Task: R6"
app/web/revenue_timeline.py       paired_series, window_slots, comparison_anchor,
                                  _bucket_span, _covered_by_confirmed
app/web/server.py                 _analysis_view, _orders_chart,
                                  _revenue_chart_for_scope, và dòng 1257 của R5
app/modules/reporting/basket_metrics.py · product_metrics.py
app/web/product_taxonomy.py · dashboard_presentation.py
```

---

## 2. Baseline ĐO TRƯỚC khi sửa mã, trên chính `b3fa809`

```text
$ .venv/bin/python -m pytest tests/ -q
1 failed, 3397 passed, 11 skipped

  bài đỏ DUY NHẤT:
  tests/test_105d_boundaries.py::TestG25GoldenBaselineUnchanged::
    test_protected_golden_artifacts_match_the_task_105e_review_base
  → fatal: bad object 740f396acb11cf279f303f09ea22dffd0ca95462

GOVERNANCE STRUCTURE: PASS
PROJECT STATE:        PASS
EVIDENCE VALIDATION:  PASS
TASK COMPLETION:      PASS
REFERENCE INTEGRITY:  FAIL — ĐÚNG 4 finding BASELINE (S139…S144)
```

Khớp từng con số với baseline mà `S144` §6.2 và `S143` §2 đã ghi. Bài đỏ là
BASELINE MÔI TRƯỜNG (clone nông), không phải hồi quy.

---

## 3. Test ĐỎ TRƯỚC, XANH SAU — không nới một bài nào

Hai file mới, viết TRƯỚC khi sửa mã:

```text
tests/test_r6_repair1_chart_windows.py       21 bài  (FIND-R6-IR-01)
tests/test_r6_repair1_basket_and_price.py    27 bài  (FIND-R6-IR-02, AR-R6-IR-03)
```

Trạng thái TRƯỚC repair: **34 ĐỎ**. Hình dạng lỗi trùng khít bằng chứng của
review, không phải một lỗi gần giống:

```text
$ pytest tests/test_r6_repair1_chart_windows.py -q      → 16 failed, 5 passed
  test_r5_and_r6_agree_on_every_comparison_bucket_of_the_revenue_chart
  E  Differing items:
  E  {'2026-08-20': '0'} != {'2026-08-20': '9000000'}
  E  {'2026-08-10': '0'} != {'2026-08-10': '7000000'}

$ pytest tests/test_r6_repair1_basket_and_price.py -q   → 18 failed, 9 passed
  test_a_line_missing_revenue_leaves_both_sides_of_the_average
  E  AssertionError: assert Decimal('5000000.00') == Decimal('10000000.00')
  E  + where Decimal('5000000.00') = PriceStats(merchandise_lines=2,
  E      merchandise_quantity=Decimal('2'),
  E      merchandise_revenue=Decimal('10000000'), …).average
```

Bài `test_the_r5_report_page_shows_the_real_previous_window_value` là ORACLE và
nó XANH ngay từ trước repair — nếu oracle đỏ thì cả file mất ý nghĩa, nên nó
được đo riêng và chạy đầu tiên.

Trạng thái SAU repair: **48 XANH.**

---

## 4. Kiểm chứng (E1 — output nguyên văn)

### 4.1 Test của REPAIR-1 và cả nhóm R6

```text
$ .venv/bin/python -m pytest tests/test_r6_repair1_chart_windows.py \
      tests/test_r6_repair1_basket_and_price.py -q
48 passed in 2.18s

$ .venv/bin/python -m pytest tests/test_r6_*.py -q
186 passed in 9.77s
```

### 4.2 Full regression R1–R5.1

```text
$ .venv/bin/python -m pytest tests/ -q
1 failed, 3445 passed, 11 skipped in 204.12s (0:03:24)
```

`3397 → 3445` = **+48 bài, đúng bằng số bài REPAIR-1 thêm vào**. Bài đỏ là
ĐÚNG BÀI baseline của §2, cùng thông điệp `fatal: bad object 740f396`.
**Không bài nào của `R1`–`R5.1` đổi trạng thái.**

### 4.3 `FIND-R6-IR-01` — đo qua HTTP THẬT, cùng oracle mà review đã dùng

Bài kiểm dựng một `werkzeug` server nghe trên cổng thật (KHÔNG phải
`test_client`), vì đúng bề mặt ấy là nơi review đo được sai số. Trên cùng server
đó, cùng sổ, cùng kỳ, cùng mức gộp:

```text
R5  /kinh-doanh?ky=2026-09&muc=ngay              10/08/2026 → 7.000.000
R6  /kinh-doanh/phan-tich?ky=2026-09&muc=ngay    10/08/2026 → 7.000.000   (TRƯỚC: 0)
R6  biểu đồ SỐ ĐƠN, cùng mốc                     10/08/2026 → 1 đơn        (TRƯỚC: 0)
```

`test_r5_and_r6_agree_on_every_comparison_bucket_of_the_revenue_chart` so
TOÀN BỘ 30 mốc của cửa sổ so sánh giữa hai trang và đòi chúng bằng nhau tuyệt
đối — không chỉ một mốc.

Bốn mức gộp có cửa sổ so sánh đều được phủ, và kỳ vọng KHÔNG hard-code: bài
kiểm tính lại từ chính `paired_window_span()` và từ sổ, rồi đòi tổng hai cửa sổ
bằng tổng doanh thu/số đơn THẬT trong khoảng ấy.

```text
ngay   (2026-08-02, 2026-09-30)
tuan   (2026-04-20, 2026-10-04)
thang  (2024-10-01, 2026-09-30)
quy    (2022-10-01, 2026-09-30)
nam    None            ← không có cửa sổ so sánh, trang NÓI RA điều đó
```

Luật của `R5` KHÔNG bị nới:

```text
test_a_genuinely_empty_confirmed_bucket_is_still_drawn_as_zero   PASS
  11/08 nằm TRỌN trong khoảng đã xác nhận đầy đủ và sổ không có đơn ⟹ vẽ 0
test_a_bucket_outside_any_confirmed_range_stays_a_gap_not_a_zero PASS
  mốc tuần trước 01/07 nằm NGOÀI khoảng xác nhận ⟹ KHÔNG có chấm nào
```

Custom range neo vào `Đến ngày` của chính nó, và lát mở rộng không mượn chốt kỳ:

```text
test_a_custom_range_anchors_the_window_on_its_own_end_date   PASS
test_a_custom_range_never_borrows_a_period_lock             PASS  (closed is None)
```

Và phần KHÔNG được mở rộng vẫn không mở rộng:

```text
test_the_cards_and_tables_still_use_only_the_selected_scope  PASS
  doanh thu ô chỉ tiêu = 11.600.000 (chỉ tháng 9), số đơn = 2
test_the_group_table_still_reconciles_on_the_selected_scope  PASS
```

### 4.4 Bất biến tiền và phạm vi diff

```text
$ git diff --stat b3fa809..HEAD -- \
    app/modules/pricing/ app/modules/profit/ app/modules/kpi/ \
    app/web/period_lock.py app/web/business_store.py \
    app/web/business_queries.py app/web/business_service.py \
    app/modules/reporting/business_metrics.py tools/db/migrations/ config/
  → RỖNG
```

`app/web/revenue_timeline.py` CÓ bị chạm, và đây là bằng chứng nó thuần THÊM:

```text
$ git diff --numstat -- app/web/revenue_timeline.py
  55  1   app/web/revenue_timeline.py
$ git diff -- app/web/revenue_timeline.py | grep '^-' | grep -v '^---'
  -    "paired_series", "window_slots",        ← dòng __all__ được viết dài ra
```

Đúng MỘT dòng bị xoá, và nó là chính dòng `__all__` được thay bằng bản có thêm
tên mới. Không một dòng hành vi nào của engine `R5` bị đổi. Brief `REPAIR-1`
cho phép tường minh: *"Dùng/làm rõ helper thuộc engine timeline hiện có nếu
cần"*. Đính chính Scope Lock:
`docs/tasks/R6-dashboard-phan-tich-kinh-doanh.md` §1.

### 4.5 `FIND-R6-IR-02` — domain và route thật

```text
test_a_known_category_plus_an_unresolved_line_is_not_a_multi_category_order  PASS
test_a_known_category_plus_an_unresolved_line_creates_no_category_pair       PASS
test_two_different_unknown_reasons_never_pair_with_each_other                PASS
test_no_undecided_state_whatsoever_enters_the_category_basket[5 tham số]     PASS
test_two_genuine_categories_are_still_a_multi_category_order                 PASS
test_product_pair_semantics_are_untouched_by_the_category_repair             PASS
test_a_fee_line_is_not_counted_as_an_unknown_category                       PASS
test_money_is_never_lost_by_the_category_repair                              PASS
test_group_reconciliation_still_keeps_every_undecided_line                   PASS
test_the_basket_route_excludes_unknown_categories                            PASS
test_the_basket_route_shows_the_data_quality_signal                          PASS
test_the_data_quality_signal_leaks_no_customer_field                         PASS
test_the_basket_route_still_reports_money_and_multi_line                     PASS
```

Bài `test_two_genuine_categories_are_still_a_multi_category_order` có mặt để
sửa không xanh bằng cách thôi đếm gì cả: hai nhóm hàng THẬT vẫn phải cho ra
`multi_merchandise_category_orders == 1` và một cặp `Tivi × Tủ lạnh`.

Bài `test_group_reconciliation_still_keeps_every_undecided_line` đo rằng bảng
gộp theo nhóm hàng VẪN giữ đủ ba bucket riêng và đối soát vẫn khớp tuyệt đối —
repair chỉ chạm Basket.

### 4.6 `AR-R6-IR-03`

```text
test_a_line_missing_revenue_leaves_both_sides_of_the_average       PASS  (10.000.000)
test_a_line_missing_quantity_leaves_both_sides_of_the_average      PASS
test_a_line_with_zero_quantity_leaves_both_sides_of_the_average    PASS
test_the_ordinary_case_is_unchanged                                PASS  (495.049,50)
test_a_gift_priced_zero_still_takes_part_in_the_average_and_the_minimum  PASS
test_no_line_with_enough_data_gives_none_and_a_reason_not_zero      PASS
test_a_fee_only_bucket_gives_none_and_a_reason                      PASS
test_the_minimum_and_maximum_read_every_merchandise_line_with_a_price   PASS
test_the_total_business_quantity_is_not_narrowed_by_the_average_repair  PASS
```

### 4.7 Smoke xuyên hai repo

```text
$ .venv/bin/python scripts/r6_crossrepo_smoke.py
  ok   hai nhóm hàng THẬT ⟹ chỉ BH1 được đếm nhiều nhóm hàng hoá
  ok   cặp nhóm hàng là hai nhóm CHÍNH DANH, theo giá trị Tracking HIỆN TẠI
  ok   KHÔNG cặp nhóm hàng nào chứa bucket chưa xác định
  ok   mọi ô của bảng cặp nhóm hàng đều chính danh
  ok   BH3 (chưa khớp mã) hiện ở tín hiệu độ phủ, không ở bảng cặp
  ok   ...kèm số DÒNG là nguyên nhân
KẾT QUẢ SMOKE: 29 PASS, 0 FAIL     (trước REPAIR-1: 24 PASS)

$ .venv/bin/python scripts/r51_crossrepo_smoke.py
KẾT QUẢ SMOKE: 63 PASS, 0 FAIL     (khớp S142 §4.5 — không hồi quy)
```

### 4.8 Tracking — chỉ để xác nhận hợp đồng xuyên repo không bị ảnh hưởng

```text
$ git -C Tracking status --porcelain   → RỖNG
$ npm test    → 62 bộ · 2892 đạt · 0 hỏng · 2 bỏ qua · Tất cả đạt
$ npm run build → 62 bộ · 2892 đạt · 0 hỏng · 2 bỏ qua; Đã dựng vào ./dist
```

### 4.9 Đối soát sổ kế toán

```text
$ .venv/bin/python scripts/r6_book_reconciliation.py \
    --so tests/fixtures/golden/period_2026_01.xlsx
Dòng nguồn (có Số BH)            351            351    OK
Số BH khác nhau                  254            254    OK
BH có doanh thu sau CK dương     248            248    OK
Tổng SL                          407            407    OK
Doanh số bán (dẫn xuất)  3.564.610.000  3.564.610.000  OK
Chiết khấu                   2.300.000      2.300.000  OK
Doanh thu sau CK         3.562.310.000  3.562.310.000  OK
BH có ít nhất hai dòng            63             63    OK
KẾT QUẢ ĐỐI SOÁT: KHỚP TOÀN BỘ
```

`3.562.310.000` là con số Golden freeze TRƯỚC `R6` — repair không dời nó.
`tests/test_r6_book_reconciliation.py` (22 bài) vẫn xanh, gồm cả bài tái tạo
đủ tám con số vector Owner qua pipeline thật.

### 4.10 Validator governance và `git diff --check`

```text
GOVERNANCE STRUCTURE: PASS
PROJECT STATE:        PASS
EVIDENCE VALIDATION:  PASS
TASK COMPLETION:      PASS
REFERENCE INTEGRITY:  FAIL — ĐÚNG 4 finding BASELINE, không finding nào mới
$ git diff --check    → rỗng (sạch)
```

---

## 5. `CHECK-R6-30` — vì sao VẪN `NOT_TESTED`

Lệnh đã chạy đúng nguyên văn như brief yêu cầu:

```text
$ .venv/bin/python scripts/r6_book_reconciliation.py \
    --so /Users/hoangvinh/Downloads/So_chi_tiet_ban_hang.xlsx --so-cua-owner
KHÔNG TÌM THẤY SỔ: /Users/hoangvinh/Downloads/So_chi_tiet_ban_hang.xlsx
Đây KHÔNG phải một lỗi của R6 — file sổ kế toán không được commit vào repo
(DEC-108) và không có mặt trong môi trường này.
$ echo $?   → 2
```

`/Users/hoangvinh/` là đường dẫn trên máy Owner (macOS); container phiên này
là Linux và `DEC-108` cấm commit file ấy. Mã thoát `2` phân biệt "không tìm
thấy sổ" với "đối soát lệch" (`1`) — đúng như `tests/test_r6_book_reconciliation
.py::test_a_missing_workbook_is_reported_as_a_missing_file_not_a_failure` canh.
Owner chạy đúng lệnh trên để đóng check này.

---

## 6. Hai lỗi của chính bộ kiểm, tìm ra và sửa trong phiên

**6.1 Smoke đo sai điều tên gọi của nó gợi ra.** Review §7.2 đã ghi: bài
`phí KHÔNG làm tăng ô nhiều nhóm hàng hoá` XANH, nhưng `BH1` được đếm là nhiều
nhóm hàng CHỈ VÌ một dòng chưa khớp mã. Sau repair bài ấy ĐỎ — và nó ĐÚNG khi
đỏ. Đã sửa gốc: `classify()` chọn dòng theo TÊN HÀNG thay vì theo Số BH (chọn
theo Số BH là không xác định — danh tính khoá theo `raw_identity_key`, nên sau
khi tivi của `BH1` khớp thì tivi của `BH2` khớp theo và lời gọi kế tiếp rơi vào
dòng phí; bản cũ vì thế đã gán một khoản phí vận chuyển cho mã tủ lạnh). Nay
`BH1` có hai nhóm hàng chính danh, và smoke thêm bốn phép thử canh trực tiếp
`FIND-R6-IR-02`.

**6.2 Bài kiểm mới của tôi làm rò trạng thái toàn cục.** Lần chạy full đầu tiên
sau repair có HAI bài đỏ, bài thứ hai là
`tests/test_tracking_live_pull.py::test_is_configured_requires_both_source_url_
and_api_key`. Nguyên nhân: fixture server của tôi gán THẲNG vào module
(`live_pull.is_configured = lambda …`) vì `monkeypatch` là fixture theo HÀM mà
server dựng một lần cho cả module. Các script `scripts/r6_*_smoke.py` gán thẳng
được vì chúng là tiến trình riêng; một file test thì không. Đã sửa bằng
`pytest.MonkeyPatch()` có `undo()` trong `finally`. Đây là lỗi của tôi, không
phải của `R6`, và nó được ghi ra đây thay vì sửa im lặng.

---

## 7. `CHECK-R51-26` — XÁC NHẬN GIỮ `NOT_TESTED`

```text
CHECK-R51-26 (Owner nghiệm thu R5.1 trên production)   NOT_TESTED
```

Phiên này KHÔNG đóng và không có thẩm quyền đóng check này. Nó vẫn là điều kiện
CHẶN merge/deploy `R6`, và repair không làm nó gần hơn một bước nào: bảng
"Nhóm hàng"/"Hãng" của `R6` vẫn gộp TIỀN theo đúng những nhãn mà
`CHECK-R51-26` chưa xác nhận trên dữ liệu thật.

---

## 8. Ngân sách review — cycle DUY NHẤT đã tiêu

```text
Trước REPAIR-1   1 allowed / 0 used / 1 remaining
Sau  REPAIR-1    1 allowed / 1 used / 0 remaining   ← HẾT ngân sách
```

Cả bốn mục (`FIND-R6-IR-01`, `FIND-R6-IR-02`, `AR-R6-IR-03`, `COR-R6-IR-01`)
được sửa trong CÙNG một vòng, đúng như `V4.1` §3 tính (theo LẦN SỬA, không theo
số finding) và đúng cảnh báo của review §8.

Việc dời khối route và hai lỗi ở §6 đều nằm TRONG cumulative repair diff của
cycle này, nên chúng không mở một cycle thứ hai (`V4.1` §3).

**Nếu vòng Independent Review thứ hai lại ra `REPAIR_REQUIRED`, `R6` KHÔNG
được mở repair cycle thứ hai** — phải escalate theo
`governance/core/ESCALATION_PROTOCOL.md`.

---

## 8b. `INTEGRATION_DECISION_REQUIRED` — cần Owner quyết, KHÔNG do phiên này chọn

`scripts/branch_authority_check.sh` trên HEAD sau repair:

```text
DEFAULT_BRANCH       claude/extract-upload-repo-gq2ws4
DEFAULT_TIP          05f2b443e66ee4702d03c003d5f1f960b5765f8d
HEAD_SHA             419391c723be30a027b43519c2e2fc890f5f6d61
WORKTREE             CLEAN
ahead  default       4 commit
behind default       0 commit
divergence days      0
cumulative LOC       10100
DIVERGENCE           INTEGRATION_DECISION_REQUIRED [ loc>5000 ]
AUTHORITY            BRANCH_WITH_UPSTREAM
RESULT               AUTHORITY_OK
```

`AUTHORITY_OK` — nhánh có upstream, working tree sạch, không lệch sau nhánh mặc
định. NHƯNG `cumulative LOC = 10.100` vượt ngưỡng `5.000` của `V4.1` §8, nên
cờ `INTEGRATION_DECISION_REQUIRED` đang MỞ.

**Phiên này ghi nhận và KHÔNG tự chọn.** `V4.1` §8 quy định Owner phải chọn một
trong ba: (A) integrate/merge sớm; (B) cắt scope; (C) tiếp tục divergence có lý
do + ngày review — và nói rõ *"Không được tiếp tục im lặng"*.

Ghi thêm cho trung thực: cờ này **đã mở từ trước phiên này** — phần lớn `10.100`
LOC là của chính `R6` (`S143`), và `REPAIR-1` chỉ góp thêm `2.193` dòng. `S143`,
`S144` và bản ghi Independent Review đều KHÔNG ghi lại cờ này; đây là một khoảng
trống governance mà phiên repair phát hiện, không phải một cờ do repair sinh ra.

Nó KHÔNG phải một finding về mã và KHÔNG chặn `REPAIR-1`: `R6` vốn không được
merge trong phiên nào của lineage này cho tới khi `CHECK-R51-26` và
`CHECK-R6-31` cùng `PASS`. Nhưng nó phải được đặt lên bàn Owner TRƯỚC lần merge
đó, vì lựa chọn (A)/(B)/(C) là một quyết định về tích hợp, không phải một bước
kỹ thuật.

---

## 9. Việc kế tiếp, theo thứ tự

1. **Independent Review vòng 2** trên exact HEAD của
   `claude/r6-business-analytics-dashboard-it73x5` sau repair → `CHECK-R6-31`.
   Reviewer nên đo lại chính hai bằng chứng của vòng 1: giá trị cửa sổ so sánh
   qua HTTP thật, và bảng cặp nhóm hàng trên một đơn có dòng chưa khớp mã.
2. **Owner nghiệm thu `R5.1` trên production** → `CHECK-R51-26` (chặn merge).
3. **Owner chạy đối soát sổ thật** → `CHECK-R6-30`, một lệnh (xem §5).
4. Chỉ khi (1) và (2) cùng `PASS`: merge `R6`. Chỉ Reports có gì để merge.
5. **Owner quyết `INTEGRATION_DECISION_REQUIRED`** theo `V4.1` §8 — (A)
   integrate sớm, (B) cắt scope, hay (C) tiếp tục divergence có lý do + ngày
   review. Xem §8b. Phải quyết TRƯỚC lần merge, không phải sau.
6. Deploy và `CHECK-R6-32` sau merge.

---

## 10. Trạng thái cuối

```text
R6                          IMPLEMENTED
FIND-R6-IR-01               ĐÃ SỬA  (CHECK-R6-33 … -39 PASS, E1)
FIND-R6-IR-02               ĐÃ SỬA  (CHECK-R6-40 … -48 PASS, E1)
AR-R6-IR-03                 ĐÃ SỬA  (CHECK-R6-49 … -53 PASS, E1)
COR-R6-IR-01                ĐÃ SỬA  (CHECK-R6-54 PASS, E1)
CHECK-R6-30                 NOT_TESTED — sổ thật không có trong môi trường
CHECK-R6-31                 NOT_TESTED — chờ Independent Review vòng 2
CHECK-R6-32                 NOT_TESTED — Owner Acceptance
CHECK-R51-26                NOT_TESTED — GIỮ NGUYÊN, chặn merge/deploy R6
Repair cycle                1 allowed / 1 used / 0 remaining
Migration mới               0 — alembic giữ nguyên một head của R3
Route GHI mới               0
Tracking                    KHÔNG sửa một byte nào
PR / merge / deploy         KHÔNG thực hiện
branch_authority_check.sh   AUTHORITY_OK; DIVERGENCE
                            INTEGRATION_DECISION_REQUIRED [loc>5000] — MỞ,
                            cần Owner quyết theo V4.1 §8 (xem §8b)
```

**R6 chỉ được merge/deploy sau khi `CHECK-R51-26` hoàn tất trên production VÀ
`R6` qua Independent Review vòng 2.**
