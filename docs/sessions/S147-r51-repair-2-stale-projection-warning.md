# S147 — R5.1 REPAIR-2 (vòng 2): cảnh báo khi bản chiếu CŨ một phần

Ngày: 2026-09-09
Task Mode: MAJOR (tiếp tục repair lỗi production, cùng task `R5.1 REPAIR-2`)
Quyết định: `DEC-209`
Kết quả phiên: **`R5.1 REPAIR-2` VẪN `IMPLEMENTED`, nay bao thêm ca "bản chiếu
CŨ một phần".** KHÔNG mở PR, KHÔNG merge, KHÔNG deploy. Repo Tracking KHÔNG
đổi một dòng code nào.

Phiên này TIẾP TỤC đúng task đã mở ở `S146` (`docs/sessions/S146-r51-
repair-2-run-refreshes-projection.md`), không phải một task mới. Yêu cầu của
Owner trước khi mở Independent Review cho `REPAIR-2`:

1. Push artifact thật lên GitHub và báo chính xác branch/SHA/commit — xem §1.
2. Bổ sung hành vi + test fail-visible cho ca: bản chiếu đã có projection CŨ,
   nhưng run MỚI trả `NO_METADATA` hoặc ghi projection `WRITE_FAILED`, và tab
   Nhân viên có dòng CONFIRMED thiếu `model_label`/`brand`/`category_label` —
   PHẢI cảnh báo, KHÔNG đổi tên hàng/mapping/giá MIN/lợi nhuận/tổng tiền — xem
   §2–§4.
3. Chạy focused tests, full pytest, smoke Tracking producer → `POST /run` →
   tab Nhân viên trên CẢ projection trống VÀ projection cũ, rồi cập nhật
   handoff — xem §5–§7.

---

## 1. Xác minh push (yêu cầu số 1)

```text
$ git status --short --branch
## claude/r6-business-analytics-dashboard-it73x5...origin/claude/r6-business-analytics-dashboard-it73x5

$ git rev-parse HEAD
a14df7c32b76a763dca284534b7baa8050807ac6

$ git rev-parse origin/claude/r6-business-analytics-dashboard-it73x5
a14df7c32b76a763dca284534b7baa8050807ac6

$ git ls-remote --heads origin claude/r6-business-analytics-dashboard-it73x5
a14df7c32b76a763dca284534b7baa8050807ac6	refs/heads/claude/r6-business-analytics-dashboard-it73x5
```

```text
Branch Reports     claude/r6-business-analytics-dashboard-it73x5
Full SHA HEAD       a14df7c32b76a763dca284534b7baa8050807ac6
```

`git show --stat a14df7c3` xác nhận commit này mang chính mã repair (`app/web/
catalog_display.py`, `app/web/server.py`, test `R5.1 REPAIR-2`), không phải
một commit tài liệu. Cục bộ và origin ĐỒNG BỘ tại thời điểm kiểm.

Commit MỚI của vòng 2 (bản sửa + tài liệu trong phiên này) được push SAU khi
ghi mục §1 này — xem §8 cho SHA cuối của vòng 2.

---

## 2. Ca mới: bản chiếu CŨ một phần

`DEC-208` (`S146`) đóng ca bản chiếu VẮNG HOÀN TOÀN. Nó không phân biệt được
ca này, mà cùng đọc `catalog_display.read()` cho ra CÙNG một kết quả (mã
thiếu nhãn là falsy) cho cả hai câu chuyện:

```text
Tracking đơn giản CHƯA phân loại mã này        → hợp lệ, im lặng đúng
                                                  (AR-R5.1-01)
lần chạy GẦN NHẤT không làm mới được bản chiếu,
bản chiếu đang hiện một bản CŨ, có thể thiếu
đúng mã MỚI xác nhận SAU lần ghi thành công
cuối cùng                                       → lỗi luồng chính, cần cảnh
                                                   báo (DEC-209)
```

### 2.1 Mã đã đổi

```text
app/web/catalog_display.py
  + _status_path()/_record_status()/_finish()/last_write_status()
  + STALE_METADATA_NOTE_PREFIX, stale_metadata_note()
  ~ write() đi qua _finish() ở CẢ BỐN nhánh trả về, để MỌI lần gọi đều ghi lại
    trạng thái của chính nó

app/web/server.py
  ~ _catalog_projection_warning() thêm "hình dạng 2" (kind="cu"), gated trên
    last_write_status() — hình dạng 1 (kind="vang") GIỮ NGUYÊN VĂN
  ~ _refresh_catalog_display() cả hai nhánh sớm gọi catalog_display.write(None)
    thay vì tự dựng WriteResult tay, để _record_status luôn chạy

app/web/templates/kinh_doanh_nhan_vien.html
  + data-kind="{{ catalog_projection_warning.kind }}" trên dòng cảnh báo

tests/test_r51_repair2_run_refreshes_projection.py
  + SECOND_RAW_PRODUCT/SECOND_CODE, switch_live_catalog(), force_next_write_
    failure(), và 3 bài MỚI (§4 dưới) — 12 → 15 bài

scripts/r51_crossrepo_smoke.py
  + §6 MỚI: bản chiếu CŨ một phần, qua producer Tracking THẬT
```

Không migration, không route ghi mới, không bảng mới. `catalog_display.write()`
vẫn là hàm DUY NHẤT ghi bản chiếu; `_status_path()` chỉ ghi một file trạng
thái CẠNH nó, KHÔNG chạm vào nội dung bản chiếu.

### 2.2 Vì sao một file trạng thái RIÊNG, không một khoá trong bản chiếu

`catalog_display.read()` coi MỌI khoá top-level của bản chiếu là một mã
Tracking. Một khoá đặc biệt (ví dụ `_status`) nhồi vào đó có nguy cơ — dù nhỏ
— va với một mã Tracking thật trùng tên, và bản chiếu sẽ tự bịa ra một "mã sản
phẩm" không do Tracking nói. File riêng (`<target>.status.json`) loại hẳn khả
năng đó.

---

## 3. Test ĐỎ TRƯỚC, XANH SAU (yêu cầu số 2)

Ba bài mới trong `tests/test_r51_repair2_run_refreshes_projection.py` §4:

```text
CHECK-R51R2-17  test_the_employee_tab_warns_when_a_newly_confirmed_code_stays_unrefreshed_no_metadata
CHECK-R51R2-18  test_the_employee_tab_warns_when_a_newly_confirmed_code_stays_unrefreshed_write_failed
CHECK-R51R2-19  test_no_stale_warning_when_the_second_run_refreshes_every_confirmed_code
```

Dựng đúng thứ tự thời gian của ca production: (1) confirm mã CŨ, chạy thành
công (bản chiếu có dữ liệu THẬT) → (2) confirm mã MỚI SAU đó → (3) lần chạy
KẾ TIẾP trả `NO_METADATA` (bài `-17`) hoặc ghi projection thất bại
(`WRITE_FAILED`, bài `-18`, qua `force_next_write_failure` — patch `Path.
write_text` CHỈ chặn đúng một `target`, không vá toàn cục như đã tránh ở
`S146` §3.1). Cả hai khẳng định: cảnh báo `kind="cu"` xuất hiện; dòng CŨ giữ
nguyên model/hãng; dòng MỚI fallback về MÃ Tracking (không lộ tên thô, không
đổi mapping); và tiền giống hệt khi so kỳ có/không bản chiếu (`business_
service.period()`). Bài `-19` là chiều ngược: hai mã cùng làm mới đầy đủ ⟹
KHÔNG cảnh báo — chứng minh nhánh mới không over-fire.

### 3.1 Bằng chứng red→green

Viết mã sản phẩm và cả 15 bài trước, chạy XANH:

```text
$ .venv/bin/python -m pytest tests/test_r51_repair2_run_refreshes_projection.py -q
15 passed in 6.00s
```

Rồi xác nhận NGƯỢC: hai bài `-17`/`-18` phải ĐỎ trên logic CŨ (trước `DEC-209`)
— tạm vô hiệu hoá đúng nhánh `kind="cu"` trong `_catalog_projection_warning()`
(trả `None` ngay sau `if not unmatched: return None`) rồi chạy lại ba bài mới:

```text
$ .venv/bin/python -m pytest tests/test_r51_repair2_run_refreshes_projection.py -q -k "unrefreshed or no_stale_warning"
FAILED test_the_employee_tab_warns_when_a_newly_confirmed_code_stays_unrefreshed_no_metadata
  AssertionError: assert 'data-metric="catalog-projection-warning"' in html
FAILED test_the_employee_tab_warns_when_a_newly_confirmed_code_stays_unrefreshed_write_failed
  AssertionError: assert 'data-metric="catalog-projection-warning"' in html
2 failed, 1 passed in 2.11s
```

Bài `-19` (chiều ngược) vẫn XANH trên cả hai bản mã — đúng: "không cảnh báo"
là hành vi mà logic CŨ và MỚI đều đồng ý, nó chỉ đo việc nhánh mới không
over-fire, không đo chính nhánh mới.

Khôi phục logic thật, chạy lại toàn file — cả 15 bài XANH:

```text
$ .venv/bin/python -m pytest tests/test_r51_repair2_run_refreshes_projection.py -q
15 passed in 4.70s
```

---

## 4. Full regression (yêu cầu số 3, phần 1)

```text
$ .venv/bin/python -m pytest tests/ -q
3461 passed, 11 skipped in 230.72s (0:03:50)
```

`3458 → 3461` = **+3, đúng bằng số bài vòng 2 thêm vào**. **0 failed.** Không
bài `R1`–`R6` nào đổi trạng thái so với baseline `S146` §4.2.

---

## 5. Smoke xuyên hai repo — CẢ HAI ca: projection trống VÀ projection cũ

`scripts/r51_crossrepo_smoke.py` §5 (đã có từ `S146`) đo ca "trống": bản chiếu
KHÔNG tồn tại trước lần chạy đầu, và bị XOÁ hẳn sau đó. §6 (MỚI, phiên này) đo
đúng ca "cũ" mà `DEC-209` đóng, trên payload THẬT do `chieuBoard()` của
Tracking sinh — không phải dict gõ tay:

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
  ok   dựng lại bản chiếu trước §6 (302)
  ok   bản chiếu đã có dữ liệu THẬT trước §6

6) REPAIR-2 (lần 2): bản chiếu CŨ một phần — mã mới thiếu nhãn
  ok   lần chạy thứ hai (capture NO_METADATA) vẫn thành công (302)
  ok   run evidence ghi đúng lý do NO_METADATA
  ok   nhãn CŨ của MGS-01 còn nguyên sau lần chạy NO_METADATA
  ok   cảnh báo đúng hình dạng CŨ (kind=cu) xuất hiện
  ok   dòng CŨ (MGS-01/FV1412) không bị cảnh báo này xoá nhãn
  ok   mã MỚI xác nhận fallback về mã Tracking, KHÔNG lộ tên thô/mapping đổi
  ok   tổng tiền KHÔNG đổi vì bản chiếu CŨ/thiếu nhãn

KẾT QUẢ SMOKE: 83 PASS, 0 FAIL      (trước vòng 2: 74 PASS)
```

Mã MỚI dùng ở §6 là `BNL-99` — một mã đặt tay, KHÔNG có trong `board` thật của
Tracking, CỐ Ý không tái dùng một mã thật đã sẵn có nhãn từ một lần chạy khác
(`TV-01`/`MGS-01`): dùng lại một mã thật sẽ khiến "matched" giả — bản chiếu đã
có nhãn của mã đó từ một lần chạy KHÁC, không phải từ mapping vừa xác nhận.
Lỗi này bị bắt được ngay ở lần chạy smoke đầu tiên của §6 (2 FAIL trước khi
sửa) — ghi lại làm minh chứng bộ smoke có kiểm thật, không xanh giả:

```text
LỖI  cảnh báo đúng hình dạng CŨ (kind=cu) xuất hiện       được False mong True
LỖI  mã MỚI xác nhận fallback về mã Tracking...           được False mong True
```

### 5.1 Tracking — không đổi

```text
$ git -C /home/user/Tracking status --porcelain   → RỖNG
```

Repo Tracking không được sửa một dòng nào trong phiên này; §6 chỉ ĐỌC payload
do `chieuBoard()` thật của Tracking sinh (cùng cơ chế §1 đã dùng cho §5/§6 từ
trước).

---

## 6. Governance validators và `git diff --check` (yêu cầu số 3, phần 2)

```text
GOVERNANCE STRUCTURE:  PASS — 21 required paths
PROJECT STATE:         PASS
EVIDENCE VALIDATION:   PASS — 161 REQUIRED PASS evidence record(s)
TASK COMPLETION:       PASS — 14 DONE task(s)
REFERENCE INTEGRITY:   FAIL — ĐÚNG 4 finding BASELINE (S136/TASK-REM-T06,
                       không finding nào mới; không file nào của phiên này
                       nằm trong danh sách 4 finding đó)
$ git diff --check     → rỗng (sạch)
```

---

## 7. Nghiệp vụ `R1`–`R6` không đổi một đồng — vòng 2

```text
$ git diff --stat -- \
    app/modules/pricing/ app/modules/profit/ app/modules/kpi/ \
    app/modules/reporting/ app/modules/exporting/ \
    app/web/period_lock.py app/web/business_store.py \
    app/web/business_queries.py app/web/business_service.py \
    app/web/workspace_presentation.py tools/db/migrations/ config/
  → RỖNG
```

Đo bằng HÀNH VI, trên cả hai đường (test + smoke):

```text
CHECK-R51R2-17/-18   so service.period() của kỳ CÓ/KHÔNG bản chiếu (sau khi
                     xoá) — doanh thu, lợi nhuận KPI, SL tính KPI, số đơn,
                     số dòng GIỐNG HỆT
Smoke §6             "tổng tiền KHÔNG đổi vì bản chiếu CŨ/thiếu nhãn" — PASS
```

---

## 8. Push vòng 2

```text
$ git add app/web/catalog_display.py app/web/server.py \
    app/web/templates/kinh_doanh_nhan_vien.html \
    tests/test_r51_repair2_run_refreshes_projection.py \
    scripts/r51_crossrepo_smoke.py \
    docs/tasks/R5-1-REPAIR-2-run-refreshes-catalog-display.md \
    docs/sessions/S147-r51-repair-2-stale-projection-warning.md \
    PROJECT/PROJECT_DECISIONS.md PROJECT/PROJECT_PROGRESS.md
$ git commit -m "..."
$ git push -u origin claude/r6-business-analytics-dashboard-it73x5
```

SHA và output nguyên văn của bước push này: xem xác nhận cuối phiên, ghi lại
NGAY SAU khi lệnh push thực thi — không suy đoán trước khi lệnh chạy.

---

## 9. Trạng thái cuối

```text
R5.1 REPAIR-2                IMPLEMENTED — nay bao thêm ca "bản chiếu CŨ một
                              phần"; vẫn CHƯA merge
CHECK-R51R2-01 … -14          PASS (E1) — không đổi, xem S146 §4
CHECK-R51R2-17                PASS (E1) — cảnh báo "cu" khi NO_METADATA
CHECK-R51R2-18                PASS (E1) — cảnh báo "cu" khi WRITE_FAILED
CHECK-R51R2-19                PASS (E1) — không over-fire khi làm mới đủ
CHECK-R51R2-15                NOT_TESTED — Independent Review, VẪN MỞ
CHECK-R51R2-16                NOT_TESTED — Owner nghiệm thu lại, VẪN MỞ
CHECK-R51-26                  NOT_TESTED — không đổi
DEC-209                       BAN HÀNH — overlay hẹp trên DEC-208, không thay
                              thế
Full regression                3461 passed / 11 skipped / 0 failed (+3)
Smoke R5.1                     83 PASS / 0 FAIL (74 → 83; +9 gồm cả bước dựng
                                lại bản chiếu trước §6)
Tracking                       KHÔNG sửa một byte nào
Migration mới                  0
Ngân sách review (§7 của S146) VẪN cần Owner/reviewer xác nhận — KHÔNG đổi
                                bởi vòng 2 này
PR / merge / deploy            KHÔNG thực hiện
```

**`R5.1 REPAIR-2` (cả hai vòng) chỉ được merge/deploy sau Independent Review,
sau khi câu hỏi ngân sách (`S146` §7) được trả lời, và sau khi Owner quyết
`INTEGRATION_DECISION_REQUIRED`.**
