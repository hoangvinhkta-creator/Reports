# S146 — R5.1 REPAIR-2: luồng chạy báo cáo làm mới bản chiếu hiển thị

Ngày: 2026-09-09
Task Mode: MAJOR (repair lỗi production)
Quyết định: `DEC-208`
Kết quả phiên: **`R5.1 REPAIR-2` = `IMPLEMENTED`.** KHÔNG mở PR, KHÔNG merge,
KHÔNG deploy. Repo Tracking KHÔNG đổi một dòng code nào.

---

## 1. Preflight

```text
Reports   nhánh mặc định: claude/extract-upload-repo-gq2ws4  (KHÔNG phải "main")
          origin tip:     05f2b443e66ee4702d03c003d5f1f960b5765f8d
          nhánh làm việc: claude/r6-business-analytics-dashboard-it73x5
          HEAD trước sửa: 40807efd50e675b71ccd1a14b5801394da4cafc1
Tracking  nhánh mặc định: main @ 66787c0fb0d867a308c632e7f163cddd0c9dd0f2
          local == origin/main

$ git -C Reports  status --porcelain   → RỖNG
$ git -C Tracking status --porcelain   → RỖNG
```

Nhánh mặc định KHÔNG tiến lên; không divergence phải phân tích.

### 1.1 Baseline ĐO TRƯỚC khi sửa mã

```text
$ .venv/bin/python -m pytest tests/ -q
3446 passed, 11 skipped in 208.31s

GOVERNANCE STRUCTURE: PASS
PROJECT STATE:        PASS
EVIDENCE VALIDATION:  PASS
TASK COMPLETION:      PASS
REFERENCE INTEGRITY:  FAIL — ĐÚNG 4 finding BASELINE (S139…S145)
```

**Thay đổi baseline so với `S145`, và nguyên nhân.** `S145` ghi
`1 failed, 3445 passed`, bài đỏ là
`test_105d_boundaries.py::TestG25GoldenBaselineUnchanged` với
`fatal: bad object 740f396…`. Bài đó nay XANH:

```text
$ git cat-file -t 740f396acb11cf279f303f09ea22dffd0ca95462   → commit
```

Object ấy giờ CÓ trong repo cục bộ vì phiên này `git fetch` thêm nhánh review
(`claude/r6-independent-review-dvuiiw`) ở `S145` và fetch lại ở phiên này, nên
clone không còn thiếu nó. Đây là một thay đổi MÔI TRƯỜNG, không phải một bản
sửa của phiên nào — và nó có nghĩa là từ đây baseline là **0 failed**.

---

## 2. Nguyên nhân gốc

Bằng chứng Owner đã xác minh trên production:

```text
cột Nhóm hàng / Hãng / IMEI   ĐÃ hiển thị (không bị ẩn)
cột Hãng                       "—"
cột Mặt hàng                   tên DÀI trên sổ kế toán
```

Đọc mã, nguyên nhân nằm ở đúng một mối nối:

```text
app/web/server.py:_tracking_snapshot()   ← chỗ DUY NHẤT ghi catalog_display,
                                            chỉ chạy khi Owner mở bảng chọn
app/web/server.py:run_report()           ← luồng CHÍNH, KHÔNG ghi gì
```

Hai tầng còn lại đều ĐÚNG từ trước: hợp đồng capture chở đủ ba trường (`R5.1`),
và `workspace_presentation._catalog_field` tra bản chiếu rồi chặn đúng các
trạng thái chưa xác nhận (`R5` §5). Chỉ mối nối trên luồng chính là không tồn
tại — nên trên đĩa ephemeral của Render, trạng thái "chưa có nhãn" là VĨNH VIỄN.

`AR-R5.1-04` vì thế bị phân loại SAI: nó giả định trạng thái ấy tự thoát ra khi
có "lần capture danh mục MỚI đầu tiên". Chi tiết: `DEC-208` §6.

---

## 3. Test ĐỎ TRƯỚC, XANH SAU

`tests/test_r51_repair2_run_refreshes_projection.py` — 12 bài, viết TRƯỚC khi
sửa mã, đi qua ĐÚNG `POST /run` rồi mở tab Nhân viên, **không một lời gọi
`?phan-loai=` nào**.

Trạng thái TRƯỚC repair: **10 ĐỎ**, và hình dạng lỗi trùng khít bằng chứng
production:

```text
E  AssertionError: cột Mặt hàng phải hiện model ngắn '55Q6FA',
E    đang hiện ['Máy lạnh Test-2', 'Tủ lạnh Test-3']
```

Trạng thái SAU repair: **12 XANH.**

### 3.1 Ba lỗi của chính bộ kiểm, tìm ra và sửa trong phiên

Ghi ra thay vì sửa im lặng — cả ba đều là lỗi của tôi, không phải của `R5.1`:

1. **Một bài XANH GIẢ.** Bài kiểm mở `sheet=noi-thanh`, nhưng không gian làm
   việc phân hoạch theo NHÂN VIÊN và `BH0002` thuộc "Lê Mạnh Hoàng" — nên bảng
   rỗng và mọi khẳng định "không thấy tên thô" đều đúng vì không thấy gì cả. Đã
   sửa: mở đúng sheet qua bí danh `nhan-vien=`, và `employee_page()` nay
   **assert bảng có dòng** trước khi khẳng định bất cứ điều gì.
2. **Regex đọc rỗng.** Ô `line-product` chứa một `<a>` khi dòng còn mở bảng
   chọn, nên phép tìm tới dấu `<` đầu tiên trả về chuỗi rỗng. Đã sửa bằng một
   helper bỏ thẻ và cắt tới `</td>`.
3. **Vá toàn cục.** Bài "không ghi được bản chiếu" ban đầu monkeypatch
   `catalog_display.Path.mkdir` — mà `catalog_display.Path` CHÍNH LÀ
   `pathlib.Path`, tức vá cho mọi module trong cùng tiến trình (đúng lớp rò
   trạng thái đã làm đỏ một vertical khác ở `R6 REPAIR-1`). Đã sửa: trỏ bản
   chiếu vào một đường dẫn có cha là FILE, nên `mkdir` ném `NotADirectoryError`
   THẬT.

---

## 4. Kiểm chứng (E1 — output nguyên văn)

### 4.1 Test của REPAIR-2

```text
$ .venv/bin/python -m pytest tests/test_r51_repair2_run_refreshes_projection.py -q
12 passed in 3.20s
```

Bản đồ bài kiểm → check:

```text
CHECK-R51R2-01  test_a_successful_run_writes_the_display_projection
CHECK-R51R2-02  test_the_employee_tab_shows_model_and_brand_without_opening_the_popover
CHECK-R51R2-03  test_the_raw_accounting_name_is_replaced_for_the_confirmed_line
CHECK-R51R2-04  test_a_second_run_refreshes_the_projection_in_place
CHECK-R51R2-05  test_the_run_does_not_pull_tracking_a_second_time_for_display
CHECK-R51R2-06  test_a_legacy_capture_without_the_three_fields_falls_back_safely
CHECK-R51R2-07  test_an_unconfirmed_mapping_never_leaks_metadata
CHECK-R51R2-08  test_an_unwritable_projection_is_reported_in_the_run_evidence
CHECK-R51R2-09  test_money_is_identical_whether_or_not_the_projection_exists
CHECK-R51R2-10  test_an_unwritable_projection_still_lets_the_run_succeed
CHECK-R51R2-11  test_the_employee_tab_warns_when_the_projection_is_missing
CHECK-R51R2-12  test_no_warning_when_the_projection_is_healthy
```

### 4.2 Full regression `R1`–`R6`

```text
$ .venv/bin/python -m pytest tests/ -q
3458 passed, 11 skipped in 209.09s (0:03:29)
```

`3446 → 3458` = **+12 bài, đúng bằng số bài REPAIR-2 thêm vào**. **0 failed.**
Không bài nào của `R1`–`R6` đổi trạng thái.

### 4.3 Một regression THẬT do bản sửa, và cách xử lý

Lần chạy full đầu tiên sau khi sửa cho **38 ĐỎ**:

```text
E  AttributeError: 'types.SimpleNamespace' object has no attribute 'captures'
   app/web/server.py:3759
```

Nhiều bài kiểm cũ thay `run_owner_report` bằng một `SimpleNamespace` gọn hơn,
không có `.captures`. Đây là một regression THẬT của bản sửa, không phải test
cũ sai — và cách sửa ĐÚNG là ở mã sản phẩm, không ở 38 bài kiểm: một tính năng
NHÃN không được phép làm sập cả lần chạy báo cáo vì thiếu một trường.

```python
catalog_status = _refresh_catalog_display(
    getattr(owner_run, "captures", None) or captures)
```

Cả hai vế `None` ⟹ `NO_SNAPSHOT`, run vẫn thành công, và bằng chứng nói ra.
Đây đồng thời là chính hành vi mà yêu cầu số 6 (fallback an toàn, không crash)
đòi hỏi.

Một bài kiểm cũ được cập nhật có chủ ý —
`test_web_server.py::test_run_uses_live_pull_captures_when_tracking_is_configured`
khẳng định `tracking_evidence` bằng ĐÚNG một dict. Bằng chứng của run nay mang
thêm khoá `catalog_display`, đúng theo yêu cầu số 4. Assertion được viết CHẶT
HƠN, không lỏng hơn: nó liệt kê cả hai khoá và cả ba trường con.

### 4.4 Nghiệp vụ `R1`–`R6` không đổi một đồng

```text
$ git diff --stat -- \
    app/modules/pricing/ app/modules/profit/ app/modules/kpi/ \
    app/modules/reporting/ app/modules/exporting/ \
    app/web/period_lock.py app/web/business_store.py \
    app/web/business_queries.py app/web/business_service.py \
    app/web/workspace_presentation.py tools/db/migrations/ config/
  → RỖNG
```

Và đo bằng HÀNH VI, không chỉ bằng diff:

```text
CHECK-R51R2-09  test_money_is_identical_whether_or_not_the_projection_exists
  xoá bản chiếu rồi dựng lại kỳ: doanh thu, lợi nhuận KPI, SL tính KPI,
  số đơn, số dòng — GIỐNG HỆT
```

### 4.5 Smoke xuyên hai repo — producer Tracking THẬT → upload/run THẬT

`scripts/r51_crossrepo_smoke.py` §5 (MỚI) dựng một app HOÀN TOÀN MỚI, XOÁ bản
chiếu trước khi chạy (mô phỏng đĩa ephemeral sau deploy), rồi upload sổ qua
`POST /run` — **không mở bảng chọn của dòng nào**:

```text
5) REPAIR-2: upload/run THẬT, KHÔNG mở bảng chọn phân loại
  ok   trước khi chạy: bản chiếu KHÔNG tồn tại
  ok   upload/run thành công (302)
  ok   run THÀNH CÔNG đã ghi bản chiếu
  ok   bằng chứng của run ghi trạng thái bản chiếu
  ok   KHÔNG mở bảng chọn: cột Mặt hàng hiện MODEL NGẮN từ Tracking
  ok   ...và tên dài trên sổ kế toán đã biến khỏi dòng đã xác nhận
  ok   cột Hãng hiện brand từ Tracking
  ok   cột Nhóm hàng hiện category_label
  ok   dòng CHƯA xác nhận vẫn giữ tên gốc và dấu gạch
  ok   bản chiếu lành ⟹ KHÔNG có cảnh báo
  ok   mất bản chiếu ⟹ tab Nhân viên CẢNH BÁO

KẾT QUẢ SMOKE: 74 PASS, 0 FAIL      (trước REPAIR-2: 63 PASS)
```

Nhãn `FV1412` / `LG` / `Máy giặt` ở §5 đến từ CHÍNH `chieuBoard()` của Tracking
qua producer thật, không từ một dict gõ tay.

```text
$ .venv/bin/python scripts/r6_crossrepo_smoke.py
KẾT QUẢ SMOKE: 29 PASS, 0 FAIL      (không hồi quy)
```

### 4.6 Tracking — chỉ để xác nhận hợp đồng xuyên repo không bị ảnh hưởng

```text
$ git -C Tracking status --porcelain   → RỖNG
$ npm test    → 62 bộ · 2892 đạt · 0 hỏng · 2 bỏ qua · Tất cả đạt
$ npm run build → OK, Đã dựng vào ./dist
```

### 4.7 Validator governance và `git diff --check`

```text
GOVERNANCE STRUCTURE: PASS
PROJECT STATE:        PASS
EVIDENCE VALIDATION:  PASS
TASK COMPLETION:      PASS
REFERENCE INTEGRITY:  FAIL — ĐÚNG 4 finding BASELINE, không finding nào mới
$ git diff --check    → rỗng (sạch)
```

---

## 5. Mã đã đổi

```text
app/web/catalog_display.py      +89/-4   `write()` trả `WriteResult`; ba mã lý
                                         do đóng; `MISSING_PROJECTION_NOTE`
app/web/server.py               +117     `_refresh_catalog_display()` MỚI;
                                         `run_report` gọi trên đường THÀNH CÔNG;
                                         `_catalog_projection_warning()` MỚI
app/web/templates/kinh_doanh_nhan_vien.html  +14   một dòng cảnh báo (notice)
scripts/r51_crossrepo_smoke.py  +120     §5 upload/run THẬT
tests/test_web_server.py        +9/-1    assertion bằng chứng, CHẶT hơn
tests/test_r51_repair2_run_refreshes_projection.py   MỚI, 12 bài
```

Không migration, không bảng mới, không route GHI mới, không kho dữ liệu mới,
không API ngoài, không product key/time engine/taxonomy/decision store thứ hai.

---

## 6. Escalation — trigger ĐÃ MET, đã ghi

`ESCALATION_PROTOCOL` liệt kê *"hành vi ở production khác biệt đáng kể so với
các giả định đã được tài liệu hóa"* — trigger ấy ĐÃ MET. Hành động bắt buộc đã
thực hiện: bảo toàn evidence, ghi blocker, **rà soát nguyên nhân gốc** (§2 —
một mối nối duy nhất, tìm bằng đọc mã), cập nhật kế hoạch (`DEC-208` + task
file). Không có lần vá suy đoán nào, không check nào bị vô hiệu hoá.

Escalate agent tier KHÔNG cần: nguyên nhân gốc xác định chính xác và bản sửa
hẹp. Điều CẦN escalate là câu hỏi ngân sách ở §7.

---

## 7. Ngân sách review — CẦN Owner/reviewer xác nhận

```text
lineage R5 (chứa R5.1)   2 allowed / 2 used / 0 remaining
```

Phiên này **KHÔNG tự tiêu** và **KHÔNG tự miễn** một repair cycle. Lập luận đầy
đủ: `docs/tasks/R5-1-REPAIR-2-run-refreshes-catalog-display.md` §7 và
`PROJECT/REVIEW_BUDGET_LEDGER.md` → "Root Task: R5" → REPAIR-2 production.

Tóm lại: ngân sách của `V4.1` §2–§3 đếm các lần sửa SAU một vòng Independent
Review ra finding `BLOCKING`. `REPAIR-2` đến từ một defect Owner phát hiện trên
production SAU khi merge, không từ một vòng review. Nếu mọi defect production
sau nghiệm thu đều tiêu ngân sách review, một tính năng đã merge sẽ không sửa
được nữa khi lineage hết ngân sách.

Phiên ghi nó là **PRODUCTION DEFECT REPAIR** và đánh dấu **cần xác nhận**. Nếu
Owner/reviewer kết luận nó PHẢI tiêu một cycle, lineage `R5` vượt ngân sách và
phải escalate — quyết định ấy KHÔNG thuộc phiên repair.

---

## 8. `CHECK-R51-26` và `INTEGRATION_DECISION_REQUIRED`

```text
CHECK-R51-26 (Owner nghiệm thu R5.1 trên production)   VẪN NOT_TESTED
```

Đây là chính check mà lỗi này đã CHẶN: Owner không thể nghiệm thu một cột luôn
hiện dấu gạch. Sau `REPAIR-2` nó nghiệm thu ĐƯỢC, nhưng chỉ Owner đóng nó.

`INTEGRATION_DECISION_REQUIRED` (`V4.1` §8) vẫn MỞ trên nhánh này — xem `S145`
§8b. `REPAIR-2` làm cumulative LOC tăng thêm, nên cờ ấy càng cần Owner quyết.

```text
$ bash scripts/branch_authority_check.sh
AUTHORITY: BRANCH_WITH_UPSTREAM   RESULT: AUTHORITY_OK
DIVERGENCE: INTEGRATION_DECISION_REQUIRED [ loc>5000 ]
```

---

## 9. Việc kế tiếp, theo thứ tự

1. **Independent Review của `REPAIR-2`** → `CHECK-R51R2-15`. Reviewer nên đo
   lại chính bằng chứng production: upload/run rồi mở tab Nhân viên, KHÔNG mở
   bảng chọn, và xác nhận `model_label` + `brand` xuất hiện.
2. **Owner/reviewer trả lời câu hỏi ngân sách** ở §7.
3. **Owner quyết `INTEGRATION_DECISION_REQUIRED`** (`V4.1` §8) — xem `S145` §8b.
4. Merge, deploy.
5. **Owner nghiệm thu lại trên production** → `CHECK-R51-26` và
   `CHECK-R51R2-16`.

---

## 10. Trạng thái cuối

```text
R5.1 REPAIR-2               IMPLEMENTED
CHECK-R51R2-01 … -14        PASS (E1)
CHECK-R51R2-15              NOT_TESTED — Independent Review
CHECK-R51R2-16              NOT_TESTED — Owner nghiệm thu lại
CHECK-R51-26                NOT_TESTED — nay nghiệm thu ĐƯỢC, vẫn của Owner
AR-R5.1-04                  ĐÓNG — phân loại sai, xem DEC-208 §6
ACCEPTED_RISK R5.1R2-01     MỚI — mất đĩa giữa hai lần chạy, tự thoát ở lần sau
Repair cycle                KHÔNG tự tiêu, KHÔNG tự miễn — cần xác nhận (§7)
Full regression             3458 passed / 11 skipped / 0 failed
Smoke R5.1                  74 PASS / 0 FAIL   (63 → 74)
Smoke R6                    29 PASS / 0 FAIL
Tracking                    KHÔNG sửa một byte nào; npm test 2892 đạt
Migration mới               0
PR / merge / deploy         KHÔNG thực hiện
```

**`R5.1 REPAIR-2` chỉ được merge/deploy sau Independent Review, sau khi câu hỏi
ngân sách §7 được trả lời, và sau khi Owner quyết
`INTEGRATION_DECISION_REQUIRED`.**
