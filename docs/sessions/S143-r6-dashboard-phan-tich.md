# S143 — R6: Dashboard phân tích kinh doanh (triển khai đầy đủ)

Ngày: 2026-09-09
Task Mode: MAJOR
Quyết định: `DEC-207`
Kết quả phiên: **`R6` = `IMPLEMENTED`.** KHÔNG mở PR, KHÔNG merge, KHÔNG
deploy. KHÔNG sửa một dòng nào của repo Tracking. KHÔNG tự đánh dấu
Independent Review hay Owner Acceptance.

---

## 1. Preflight

### 1.1 Nhánh mặc định THẬT và exact HEAD

Nhánh mặc định đọc từ `git remote show origin` → "HEAD branch", KHÔNG giả
định "main":

```text
Reports   nhánh mặc định: claude/extract-upload-repo-gq2ws4  (KHÔNG phải "main")
          origin HEAD:    05f2b443e66ee4702d03c003d5f1f960b5765f8d
          HEAD cục bộ:    05f2b443e66ee4702d03c003d5f1f960b5765f8d  (ĐỒNG BỘ)
Tracking  nhánh mặc định: main
          origin HEAD:    66787c0fb0d867a308c632e7f163cddd0c9dd0f2
          HEAD cục bộ:    66787c0fb0d867a308c632e7f163cddd0c9dd0f2  (ĐỒNG BỘ)
```

Cả hai nhánh làm việc (`claude/r6-business-analytics-dashboard-it73x5`) đứng
ĐÚNG trên tip của nhánh mặc định tương ứng lúc mở phiên.

### 1.2 Merge dependency — xác nhận là ANCESTOR

```text
$ git -C Reports fetch origin claude/extract-upload-repo-gq2ws4
$ git -C Reports merge-base --is-ancestor \
    a59936ce497ddcc9fb63a87dd0524729931a83f9 \
    origin/claude/extract-upload-repo-gq2ws4 && echo YES   → ANCESTOR: YES
  a59936c  Wed Sep 9 15:35:18 2026 +0700
           DEC-206: hoàn tất taxonomy category_label theo quyết định Owner

$ git -C Tracking fetch origin main
$ git -C Tracking merge-base --is-ancestor \
    dc9891087687f25b6f92804f46eba2628ebe788b origin/main && echo YES → ANCESTOR: YES
  dc98910  Wed Sep 9 15:33:56 2026 +0700
           DEC-206: hoàn tất taxonomy category_label theo quyết định Owner
```

Cả hai dependency CÓ trên nhánh mặc định. Không có điểm lệch nào, nên phiên
KHÔNG phải dừng trước khi sửa mã.

### 1.3 Đã đọc trước khi viết một dòng mã nào

```text
docs/sessions/S142-r51-owner-taxonomy-merge.md   (toàn bộ, gồm §7 và §8)
docs/spec/TASK-105D-DATA-CONTRACT.md             (§0–§1, ghi chú SUPERSEDED)
app/web/business_service.py                      PeriodData, service.period
app/modules/reporting/business_metrics.py        BusinessLine, BusinessTotals
app/web/business_queries.py                      build_lines, line_details
app/web/revenue_timeline.py                      engine cửa sổ R5 (DEC-R5-02)
app/web/period_lock.py                           fingerprint / chốt kỳ
app/web/line_identity.py                         Decisions, state_of (R2 §4)
app/web/catalog_display.py                       hợp đồng metadata R5/R5.1
app/modules/reporting/line_type.py + config/line_types.yaml
```

### 1.4 `CHECK-R51-26` — ghi nhận rõ

```text
CHECK-R51-26 (Owner nghiệm thu R5.1 trên production)   NOT_TESTED
```

Điều này **KHÔNG chặn** viết/test `R6`. Nó **CHẶN merge/deploy `R6` lên
production** cho tới khi Owner nghiệm thu `R5.1` trên dữ liệu thật. Lý do đầy
đủ: `docs/spec/R6-EXECUTION-BRIEF.md` §0 và `DEC-207` §10.

---

## 2. Baseline ĐO TRƯỚC khi sửa mã

Đo trên đúng HEAD `05f2b443` của nhánh mặc định, trước commit đầu tiên của
phiên:

```text
$ .venv/bin/python -m pytest tests/ -q
1 failed, 3259 passed, 11 skipped

  bài đỏ DUY NHẤT:
  tests/test_105d_boundaries.py::TestG25GoldenBaselineUnchanged::
    test_protected_golden_artifacts_match_the_task_105e_review_base
  → fatal: bad object 740f396acb11cf279f303f09ea22dffd0ca95462

$ git rev-parse --is-shallow-repository   → true
$ git log --oneline | wc -l               → 96
```

Đây là BASELINE MÔI TRƯỜNG, không phải hồi quy: container phiên này dùng
clone NÔNG nên object gốc của phép so Golden không tồn tại. `S141` §"Kiểm đã
chạy" và `S142` §4.4 đã ghi lại đúng bài này với đúng nguyên nhân đó.

```text
$ governance validators (5 script)
GOVERNANCE STRUCTURE: PASS
PROJECT STATE:        PASS
EVIDENCE VALIDATION:  PASS  (161 record)
TASK COMPLETION:      PASS  (14 task DONE)
REFERENCE INTEGRITY:  FAIL — ĐÚNG 4 finding BASELINE, y hệt S139/S140/S141/S142:
  docs/sessions/S136-r5-integration.md -> /tmp/.../r5_repair_crossrepo_smoke.py
  docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> /README.md
  docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> CODE_OF_CONDUCT.md
  docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> CONTRIBUTING.md
```

---

## 3. Mã đã đổi

### 3.1 File MỚI (thuần, không phụ thuộc Flask/SQL)

```text
app/modules/reporting/analysis_range.py       hợp đồng phạm vi (Package 1)
app/modules/reporting/dashboard_metrics.py    aggregate nền   (Package 1)
app/modules/reporting/product_metrics.py      gộp bucket + giá (Package 3)
app/modules/reporting/basket_metrics.py       giỏ hàng + cặp  (Package 5)
```

### 3.2 File MỚI (tầng web)

```text
app/web/product_taxonomy.py            cửa metadata DUY NHẤT của R6
app/web/dashboard_presentation.py      trình bày, không phép tính nghiệp vụ
app/web/templates/_r6_bits.html        macro dùng chung
app/web/templates/kinh_doanh_phan_tich.html
app/web/templates/kinh_doanh_phan_tich_co_cau.html
app/web/templates/kinh_doanh_phan_tich_nhan_vien.html
app/web/templates/kinh_doanh_phan_tich_gio_hang.html
app/web/templates/kinh_doanh_phan_tich_don_hang.html
```

### 3.3 File CŨ bị chạm — đúng ba, và cả ba chỉ THÊM

```text
app/web/server.py                  +410/-3   5 route GET mới + hàm phụ; import
app/web/business_presentation.py   +132/-2   paired_count_chart, money_text,
                                             money_kvnd; `_slot_title` nhận
                                             thêm `unit` CÓ MẶC ĐỊNH "đồng"
app/web/templates/kinh_doanh.html  +6/-1     một liên kết sang trang phân tích

`git diff --numstat` xác nhận ba con số trên; ba dòng bị XOÁ ở `server.py` và
hai ở `business_presentation.py` đều là dòng bị THAY bằng chính nó cộng thêm
nội dung (khối `import`, chữ ký `_slot_title`, danh sách `__all__`).
```

`_slot_title(unit="đồng")` giữ nguyên từng ký tự cho mọi nơi gọi cũ — bài kiểm
của `DEC-R5-02` chạy lại nguyên trạng (§4.5).

**Không đổi một dòng nào** của: `app/modules/pricing/**`, `app/modules/profit/**`,
`app/modules/kpi/**`, `app/web/period_lock.py`, `app/web/business_store.py`,
`app/web/revenue_timeline.py`, `app/web/business_queries.py`,
`app/web/business_service.py`, `tools/db/migrations/**`, `config/**`.

### 3.4 Công cụ và fixture

```text
scripts/r6_book_reconciliation.py             đối soát sổ kế toán (2 tầng)
scripts/r6_crossrepo_smoke.py                 smoke xuyên hai repo
tests/fixtures/r6_reconciliation_workbook.py  sổ tổng hợp theo vector Owner
tests/test_r6_*.py                            7 file, 138 bài
```

### 3.5 Repo Tracking

```text
$ git -C Tracking status --porcelain   → RỖNG
```

Phiên này KHÔNG sửa một byte nào của Tracking. Nó chỉ ĐỌC hợp đồng metadata
đã merge, và chạy producer `kiem/smoke/sinh-catalog-reports.mjs` ở chế độ chỉ
đọc để lấy payload cho smoke (§4.6).

---

## 4. Kiểm chứng (E1 — output nguyên văn)

### 4.1 Test đơn vị của R6

```text
$ .venv/bin/python -m pytest tests/test_r6_*.py -q
138 passed in 8.00s

  tests/test_r6_analysis_range.py        15 passed
  tests/test_r6_dashboard_metrics.py     28 passed
  tests/test_r6_product_metrics.py       15 passed
  tests/test_r6_basket_metrics.py        16 passed
  tests/test_r6_product_taxonomy.py      19 passed
  tests/test_r6_dashboard_vertical.py    23 passed
  tests/test_r6_book_reconciliation.py   22 passed
```

### 4.2 Full regression R1–R5.1

```text
$ .venv/bin/python -m pytest tests/ -q
1 failed, 3397 passed, 11 skipped in 204.06s (0:03:24)
```

`3259 → 3397` = **+138 bài, đúng bằng số bài R6 thêm vào**. Bài đỏ là **ĐÚNG
BÀI baseline** của §2, cùng thông điệp `fatal: bad object 740f396`, cùng
nguyên nhân clone nông. **Không bài nào của `R1`–`R5.1` đổi trạng thái.**

Smoke của `R5.1` chạy lại nguyên trạng trên cùng HEAD có `R6`:

```text
$ .venv/bin/python scripts/r51_crossrepo_smoke.py
KẾT QUẢ SMOKE: 63 PASS, 0 FAIL
```

`63` là đúng con số mà `S142` §4.5 ghi lại — `R6` không làm lệch một phép thử
xuyên repo nào của `R5.1`.

### 4.3 Governance validators

```text
GOVERNANCE STRUCTURE: PASS
PROJECT STATE:        PASS
EVIDENCE VALIDATION:  PASS
TASK COMPLETION:      PASS
REFERENCE INTEGRITY:  FAIL — ĐÚNG 4 finding BASELINE của §2, không finding nào
                      do file của phiên này góp thêm
$ git diff --check   → rỗng (sạch)
```

### 4.4 Bất biến tiền — đo TRỰC TIẾP, không suy luận

```text
$ git diff --stat -- app/modules/pricing/ app/modules/profit/ app/modules/kpi/ \
      app/web/period_lock.py app/web/business_store.py \
      app/web/revenue_timeline.py app/web/business_queries.py \
      app/web/business_service.py tools/db/migrations/ config/
  → RỖNG
```

Và đo bằng hành vi, không chỉ bằng diff:

```text
tests/test_r6_product_metrics.py::test_changing_a_bucket_moves_no_money_at_the
  _company_level                     → đổi hãng của hai dòng cho nhau: doanh
                                       thu, SL, chiết khấu, số đơn của công ty
                                       GIỐNG HỆT; bucket thì ĐỔI THẬT
tests/test_r6_dashboard_vertical.py::test_a_custom_range_never_claims_a_period
  _lock                              → PeriodData.closed vẫn None
scripts/r6_crossrepo_smoke.py §3     → đổi category_label bên Tracking: bảng
                                       đổi bucket, tổng "KHÔNG đổi một đồng,
                                       một cái, một BH nào"
```

### 4.5 Dòng bị loại / tạm loại không lọt vào một ô nào

```text
tests/test_r6_dashboard_vertical.py
  test_an_owner_excluded_line_leaves_every_total_on_the_analysis_page   PASS
  test_an_owner_excluded_line_leaves_every_bucket_of_every_dimension    PASS
  test_an_owner_excluded_line_leaves_the_basket_and_its_pairs           PASS
  test_an_owner_excluded_line_leaves_the_drilldown                      PASS
  test_a_line_removed_from_a_confirmed_book_leaves_every_r6_figure      PASS
```

Bài cuối đo trên đường `DEC-R5-01` THẬT: nạp sổ lần hai thiếu `BH4`, xác nhận
sổ đầy đủ, rồi đo số đơn giảm đúng 1 và `BH4` biến khỏi bảng gộp lẫn bảng kê —
đồng thời phép đối soát vẫn `yes`.

### 4.6 Smoke xuyên hai repo — producer Tracking THẬT

```text
$ .venv/bin/python scripts/r6_crossrepo_smoke.py

1) Tracking sinh board/alias bằng chính `chieuBoard()` thật
  ok   DEC-206 còn nguyên trên producer thật
2) Reports capture (mã thật) đọc payload do Tracking sinh
  ok   capture COMPLETE
3) Route R6 thật: capture → bản chiếu → dashboard phân tích
  ok   đối soát với bộ chỉ tiêu nghiệp vụ đã nghiệm thu: KHỚP
  ok   trước khi phân loại: KHÔNG nhóm hàng nào chính danh
  ok   phân loại BH1 → 55Q6FA
  ok   phân loại BH2 → RT38
  ok   nhóm hàng canonical của Tracking lên đúng bảng R6
  ok   bảng nhóm hàng ĐỐI SOÁT khớp
  ok   tổng tiền/SL/đơn KHÔNG đổi sau khi nhóm hàng xuất hiện
  ok   đổi nhóm hàng bên Tracking hiện ra ngay ở lần đọc sau
  ok   ...và KHÔNG đổi một đồng, một cái, một BH nào
4) Giỏ hàng, cặp, attachment và drill-down
  ok   BH1 là đơn nhiều mặt hàng; BH2 có dịch vụ kèm
  ok   đơn nhiều dòng đếm cả BH1 lẫn BH2
  ok   phí KHÔNG làm tăng ô nhiều nhóm hàng hoá: chỉ BH1 được đếm
  ok   cặp nhóm hàng dựng được từ dữ liệu đi qua database
  ok   attachment có HAI cột riêng
  ok   drill-down KHÔNG rò tên khách hàng
  ok   drill-down KHÔNG rò số điện thoại
  ok   drill-down KHÔNG rò địa chỉ
  ok   drill-down vẫn hiện đủ bốn cột nghiệp vụ
5) Dòng R5 tạm loại KHÔNG lọt vào một ô nào của R6
  ok   BH3 rời khỏi số đơn của R6
  ok   doanh thu R6 giảm đúng phần của BH3
  ok   ...và trang vẫn ĐỐI SOÁT khớp
  ok   BH3 cũng biến khỏi bảng kê drill-down

KẾT QUẢ SMOKE: 24 PASS, 0 FAIL
```

### 4.7 Đối soát sổ kế toán — công cụ đã được kiểm chứng trên HAI sổ

**Sổ golden đã nghiệm thu** (`tests/fixtures/golden/period_2026_01.xlsx`):

```text
$ .venv/bin/python scripts/r6_book_reconciliation.py \
      --so tests/fixtures/golden/period_2026_01.xlsx

Chỉ tiêu                                Nguồn      Aggregate   Kỳ vọng  Kết quả
Dòng nguồn (có Số BH)                     351            351         —  OK
Số BH khác nhau                           254            254         —  OK
BH có doanh thu sau CK dương              248            248         —  OK
Tổng SL                                   407            407         —  OK
Doanh số bán (dẫn xuất)         3,564,610,000  3,564,610,000         —  OK
Chiết khấu                          2,300,000      2,300,000         —  OK
Doanh thu sau CK                3,562,310,000  3,562,310,000         —  OK
BH có ít nhất hai dòng                     63             63         —  OK
KẾT QUẢ ĐỐI SOÁT: KHỚP TOÀN BỘ
```

`3.562.310.000` là con số Golden đã freeze từ `TASK-PRA-002`
(`tests/fixtures/golden/expected/period_2026_01.json` →
`money.sales_normalized[0]`), tức nó KHÔNG do `R6` sinh ra. Công cụ khớp với
nó là bằng chứng nó đo doanh thu THẬT chứ không đo lại chính đầu ra của mình
(`tests/test_r6_book_reconciliation.py::test_the_harness_matches_the_golden
_baseline_frozen_before_r6`).

**Sổ tổng hợp dựng theo ĐÚNG vector Owner**
(`tests/fixtures/r6_reconciliation_workbook.py`): 466 dòng · 345 BH · 338 BH
doanh thu dương · SL 626 · doanh số bán 4.500.085.001 · chiết khấu 1.550.000 ·
doanh thu sau CK 4.498.535.001 · 85 BH nhiều dòng. Cả **tám** con số được đo
lại bằng HAI đường độc lập (tầng nguồn `raw_reader`, và tầng aggregate qua
`run_demo` → `write_run_history` → `PeriodData` → `dashboard_metrics.totals`)
và khớp tuyệt đối — 22 bài trong `tests/test_r6_book_reconciliation.py`.

Trong đó có một bài đo rằng công cụ **BẮT ĐƯỢC** một ô lệch
(`test_the_harness_reports_the_exact_metric_that_drifted`): một công cụ đối
soát luôn nói "khớp" thì không đối soát gì cả.

### 4.8 Một finding THẬT do smoke bắt được trong phiên

Lần chạy đầu của `scripts/r6_crossrepo_smoke.py` cho `1 FAIL`. Truy nguyên:
**khẳng định trong smoke sai, mã đúng.** `BH1` mua Tivi + Tủ lạnh là một đơn
HAI NHÓM HÀNG HOÁ thật, nên `multi_merchandise_category_orders = 1` là kết quả
đúng; khẳng định `= 0` của smoke đã bỏ quên chính đơn ấy.

Đã sửa khẳng định thành một phép SO SÁNH có nghĩa — `đơn nhiều dòng = 2`
(BH1 và BH2) trong khi `đơn nhiều nhóm hàng hoá = 1` (chỉ BH1), chênh lệch
đúng bằng đơn có phí. Một khẳng định `= 0` sẽ xanh cả khi engine hỏng theo
hướng ngược lại (bỏ sót luôn BH1).

---

## 5. Ngân sách review — ĐO LẠI, không sao chép

```text
Effective Risk        MEDIUM = max(Local Risk 3, Blast Radius 3)
repair_cycles_allowed 1        (V4.1 §2: MEDIUM = 1)
repair_cycles_used    0
Golden hạ bậc         KHÔNG viện dẫn (V4.1 §4.1)
Lineage               ROOT MỚI — lineage R5 giữ nguyên 2/2/0, không bị chạm
```

Lập luận blast radius đầy đủ (vì sao `3/5` chứ không `2/5`, và vì sao không
`4/5` như `R5`): `PROJECT/REVIEW_BUDGET_LEDGER.md` → "Root Task: R6".

---

## 6. Quyết định kỹ thuật đáng ghi lại

**Vị trí khối route `R6` trong `server.py`.** Đặt ngay sau
`business_composition` làm ĐỎ `tests/test_phb07_advanced_analytics.py::
test_the_route_reads_the_official_period_and_the_accepted_assignments`:
helper `route_source` của `PHB-07` cắt mã một route bằng cách đọc tới `@app.`
KẾ TIẾP, nên các hàm phụ chưa decorate của `R6` bị đọc thành mã của route
`PHB-07` (chúng có chữ `legacy` trong văn xuôi).

Cách sửa: **dời khối `R6`**, KHÔNG sửa test của `PHB-07`. Nới lỏng một bài
kiểm ranh giới của vertical khác để mã của mình lọt qua là đúng điều không
được làm. Khối nay nằm sau `business_save_gia_dung`, và một bài kiểm mới của
`R6` canh ràng buộc ấy để một lần dời về sau không âm thầm phá lại
(`test_the_r6_block_never_sits_between_a_route_and_its_next_decorator`).

---

## 7. `CHECK-R51-26` — XÁC NHẬN GIỮ `NOT_TESTED`

```text
CHECK-R51-26 (Owner nghiệm thu R5.1 trên production)   NOT_TESTED
```

Phiên này KHÔNG đóng check này và không có thẩm quyền đóng nó. Nó cũng KHÔNG
được đóng gián tiếp bởi việc `R6` đã chạy đúng trên hợp đồng metadata: `R6`
chạy trên dữ liệu test và trên payload do producer Tracking sinh, KHÔNG phải
trên danh mục production thật của Owner.

---

## 8. Việc kế tiếp, theo thứ tự

1. **Owner nghiệm thu `R5.1` trên production** → `CHECK-R51-26`. Checklist chi
   tiết: `S142` §8. Đây là điều kiện CHẶN đầu tiên của `R6`.

2. **Owner chạy đối soát trên SỔ THẬT** → `CHECK-R6-30`, một lệnh:

   ```text
   .venv/bin/python scripts/r6_book_reconciliation.py \
       --so ~/Downloads/So_chi_tiet_ban_hang.xlsx --so-cua-owner
   ```

   Script in ra bảng ba cạnh (nguồn ↔ aggregate ↔ vector kỳ vọng) và trả mã
   thoát `0` khi khớp toàn bộ. Nếu có ô lệch, nó chỉ ra ĐÚNG ô nào — và lúc đó
   cái sai có thể là sổ, có thể là hệ thống; script cố ý KHÔNG tự quyết bên
   nào đúng.

3. **Independent Review của `R6`** → `CHECK-R6-31`. Đối tượng review: exact
   HEAD của nhánh `claude/r6-business-analytics-dashboard-it73x5` (cả hai
   repo), trên nền `05f2b443` (Reports) / `66787c0f` (Tracking).

4. **Chỉ sau khi (1) và (3) cùng `PASS`**: merge `R6`. Thứ tự merge không quan
   trọng ở đây vì phiên này KHÔNG sửa Tracking — chỉ Reports có gì để merge.

5. Deploy và `CHECK-R6-32` (Owner Acceptance) sau merge.

---

## 9. Trạng thái cuối

```text
R6                          IMPLEMENTED
CHECK-R6-01 … -29           PASS (E1)
CHECK-R6-30                 NOT_TESTED — sổ thật không có trong môi trường
                            (DEC-108); công cụ đã sẵn sàng và đã kiểm chứng
CHECK-R6-31                 NOT_TESTED — Independent Review
CHECK-R6-32                 NOT_TESTED — Owner Acceptance
CHECK-R51-26                NOT_TESTED — GIỮ NGUYÊN, chặn merge/deploy R6
Repair cycle tiêu bởi S143  0 — lineage R6 mới: 1 allowed / 0 used / 1 remaining
                            lineage R5 KHÔNG bị chạm: 2 / 2 / 0
Migration mới               0 — alembic giữ nguyên một head của R3
Route GHI mới               0 — R6 chỉ có 5 route GET
Tracking                    KHÔNG sửa một byte nào
PR / merge / deploy         KHÔNG thực hiện
```

**R6 chỉ được merge/deploy sau khi `CHECK-R51-26` hoàn tất trên production VÀ
`R6` qua Independent Review.**
