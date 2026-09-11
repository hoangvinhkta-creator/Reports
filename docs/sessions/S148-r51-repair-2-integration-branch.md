# S148 — Chuẩn bị integration branch cho R5.1 REPAIR-2, tách khỏi R6

Ngày: 2026-09-09
Task Mode: MICRO (thao tác git có kiểm soát; không sửa logic mới)
Kết quả phiên: **Branch `claude/r51-repair-2-integration` đã tạo, cherry-pick
xong cả hai commit repair, xác nhận KHÔNG mang `R6`.** KHÔNG merge, KHÔNG
deploy. Kết luận: `READY_FOR_INDEPENDENT_REVIEW`.

Phiên này KHÔNG viết logic mới. Toàn bộ mã sản phẩm của `R5.1 REPAIR-2` đã
được viết và kiểm chứng ở `S146`/`S147` (trên nhánh
`claude/r6-business-analytics-dashboard-it73x5`, cùng chung với `R6`). Việc
CẦN làm ở đây là tách ĐÚNG hai commit đó ra một nhánh riêng, để Independent
Review của `REPAIR-2` không phải kéo theo toàn bộ `R6` (`R6` đang `BLOCKED`,
`CHECK-R6-31 = FAIL` từ `S144`, và KHÔNG được lẫn vào một PR review khác).

---

## 1. Nguồn đã xác nhận

```text
$ git remote show origin | grep "HEAD branch"
  HEAD branch: claude/extract-upload-repo-gq2ws4
$ git fetch origin claude/extract-upload-repo-gq2ws4
$ git rev-parse origin/claude/extract-upload-repo-gq2ws4
05f2b443e66ee4702d03c003d5f1f960b5765f8d
```

Khớp đúng nguồn Owner đã xác nhận trước khi giao việc.

```text
Commit repair 1   a14df7c32b76a763dca284534b7baa8050807ac6
                  "R5.1 REPAIR-2: luồng chạy báo cáo làm mới bản chiếu hiển thị"
Commit repair 2   f891393f17c82b700b7ad392d451a7dcc8fb590e
                  "R5.1 REPAIR-2 (vòng 2): cảnh báo khi bản chiếu CŨ một phần"
```

Cả hai đang nằm trên `claude/r6-business-analytics-dashboard-it73x5`, PHÍA SAU
5 commit `R6` (từ `05f2b44` tới cha của `a14df7c`):

```text
$ git log --oneline 05f2b443e66ee4702d03c003d5f1f960b5765f8d..a14df7c32b76a763dca284534b7baa8050807ac6
a14df7c R5.1 REPAIR-2: luồng chạy báo cáo làm mới bản chiếu hiển thị
40807ef R6 REPAIR-1: ghi nhận INTEGRATION_DECISION_REQUIRED, cần Owner quyết
419391c R6 REPAIR-1: sửa cả 4 finding Independent Review vòng 1, một repair cycle
b3fa809 S144: Independent Review R6 — REPAIR_REQUIRED (CHECK-R6-31 = FAIL)
56aca4c R6: dọn ranh giới module — sum_optional công khai, bỏ import cục bộ
0adb6d1 R6: dashboard phân tích kinh doanh — 5 package, IMPLEMENTED
```

## 2. Tạo branch, cherry-pick

```text
$ git checkout -b claude/r51-repair-2-integration origin/claude/extract-upload-repo-gq2ws4
$ git cherry-pick -x a14df7c32b76a763dca284534b7baa8050807ac6
$ git cherry-pick -x f891393f17c82b700b7ad392d451a7dcc8fb590e
```

Cả hai commit repair TỰ THÂN chỉ chạm file thuộc `R5.1 REPAIR-2`
(`app/web/catalog_display.py`, `app/web/server.py`, template tab Nhân viên,
test/smoke `R5.1`, tài liệu/governance của riêng nó) — xác nhận bằng
`git show --stat` trên cả hai TRƯỚC khi cherry-pick. Conflict khi cherry-pick
KHÔNG đến từ nội dung repair, mà từ việc hai commit ấy đứng SAU `R6` trong
lịch sử: patch context của chúng (đặc biệt trong ba file governance dùng
chung, `PROJECT/PROJECT_DECISIONS.md`, `PROJECT/PROJECT_PROGRESS.md`,
`PROJECT/REVIEW_BUDGET_LEDGER.md`) bao gồm cả nội dung `R6` đã có sẵn ở nhánh
gốc của chúng.

### 2.1 Conflict + cách giải, từng file

```text
PROJECT/PROJECT_DECISIONS.md   Vùng conflict mang CẢ `DEC-207` (R6 — brief
                                Dashboard phân tích) VÀ `DEC-208` (R5.1). Giữ
                                LẠI đúng `DEC-208`; bỏ `DEC-207`. Cherry-pick 2
                                thêm `DEC-209` (R5.1) — auto-merge sạch, không
                                cần sửa tay.
PROJECT/PROJECT_PROGRESS.md    Vùng conflict mang khối `CANONICAL CURRENT
                                STATE` của `S146` (R5.1) VÀ ba khối `R6` liền
                                sau nó (`S145` REPAIR-1, `S144` Independent
                                Review, `S143` dashboard). Giữ LẠI đúng khối
                                `S146`; bỏ cả ba khối `R6`. Cherry-pick 2 thêm
                                khối `S147` (R5.1) — conflict lần hai vì khối
                                này đã sửa; giải bằng cách giữ đúng thứ tự
                                S147 (mới nhất) → S146 (vòng 1), như tác giả
                                gốc đã viết.
PROJECT/REVIEW_BUDGET_LEDGER.md Vùng conflict mang subsection "REPAIR-2
                                production" (R5.1, dưới "Root Task: R5") VÀ
                                toàn bộ section "Root Task: R6" liền sau. Giữ
                                LẠI đúng subsection R5.1; bỏ "Root Task: R6".
app/web/server.py              Auto-merge SẠCH ở cả hai lần — không có
                                conflict marker. Xác nhận bằng đọc lại diff so
                                nhánh mặc định: một khối liên tục, đúng hai
                                hàm `_catalog_projection_warning`/`_refresh_
                                catalog_display` + một điểm gọi, không sót
                                dòng R6 nào.
```

Hai câu văn RÒ `R6` khác, nằm TRONG chính nội dung `S146` (không phải vùng
conflict, không bị git đánh dấu) nhưng vẫn nhắc `R6` không cần thiết trên một
nhánh không mang nó — SỬA TAY, không phải conflict resolution:

```text
"Smoke R6   29 PASS / 0 FAIL — không hồi quy"          → xoá dòng
"INTEGRATION_DECISION_REQUIRED (V4.1 §8) vẫn MỞ         → xoá đoạn (cờ LOC
 trên nhánh này — xem S145 §8b. REPAIR-2 làm              tích luỹ của R6,
 cumulative LOC tăng thêm."                               không áp dụng ở đây)
"...smoke R5.1 74 PASS/0 FAIL...; smoke R6              → xoá "smoke R6..."
 29 PASS/0 FAIL; Tracking npm test..."                    khỏi câu văn
```

Một đoạn khác, `"S145" ghi "1 failed"` giải thích một vấn đề CLONE NÔNG cụ thể
của nhánh `R6` gốc — không áp dụng cho nhánh này (nhánh mới, checkout đủ) —
cũng bỏ.

Nội dung LỊCH SỬ (`docs/sessions/S146-*.md`, `docs/sessions/S147-*.md`, các
đoạn "Kiểm chứng"/số liệu BÊN TRONG hai khối `CANONICAL CURRENT STATE`
`S146`/`S147` ở `PROJECT/PROJECT_PROGRESS.md`) được giữ NGUYÊN VĂN — đó là bản ghi
CÓ THẬT của việc hai phiên ấy đã đo được gì, TRÊN nhánh `R6` gốc, không phải
một tuyên bố về nhánh integration này. Một dòng chú thích ở đầu
`PROJECT/PROJECT_PROGRESS.md` nói rõ điều này và chỉ tới baseline THẬT của nhánh
integration — đo lại ở §4 dưới đây, không suy ra từ số liệu cũ.

## 3. Xác nhận diff scope — KHÔNG mang `R6`

```text
$ git diff --stat origin/claude/extract-upload-repo-gq2ws4...HEAD
 .gitignore                                              |   8 +
 PROJECT/PROJECT_DECISIONS.md                            | 207 ++++++
 PROJECT/PROJECT_PROGRESS.md                             | 148 ++++
 PROJECT/REVIEW_BUDGET_LEDGER.md                         |  57 ++
 app/web/catalog_display.py                              | 212 +++-
 app/web/server.py                                       | 160 +++
 app/web/templates/kinh_doanh_nhan_vien.html             |  22 +
 docs/sessions/S146-r51-repair-2-run-refreshes-...md     | 366 ++++
 docs/sessions/S147-r51-repair-2-stale-projection-...md  | 322 ++++
 docs/tasks/R5-1-REPAIR-2-run-refreshes-catalog-...md    | 247 ++++
 scripts/r51_crossrepo_smoke.py                          | 230 +++
 tests/test_r51_repair2_run_refreshes_projection.py      | 744 +++++
 tests/test_web_server.py                                |  10 +-
 13 files changed, 2727 insertions(+), 6 deletions(-)

$ git diff origin/claude/extract-upload-repo-gq2ws4...HEAD \
    | grep -E "analysis_range|basket_metrics|dashboard_metrics|product_metrics|product_taxonomy|kinh-doanh/phan-tich"
  → RỖNG

$ git diff --stat origin/claude/extract-upload-repo-gq2ws4...HEAD -- tools/db/migrations/
  → RỖNG

$ git diff --stat origin/claude/extract-upload-repo-gq2ws4...HEAD -- \
    app/modules/pricing/ app/modules/profit/ app/modules/kpi/ \
    app/modules/reporting/ app/modules/exporting/ \
    app/web/period_lock.py app/web/business_store.py \
    app/web/business_queries.py app/web/business_service.py \
    app/web/workspace_presentation.py config/
  → RỖNG

$ ls tests/ | grep -c "^test_r6"
0
```

Không route, module, template, test, migration, hay đường tính giá/MIN/lợi
nhuận của `R6` nào có mặt trên nhánh này. 13 file thay đổi, ĐÚNG bằng danh
sách Scope Lock của `docs/tasks/R5-1-REPAIR-2-run-refreshes-catalog-display.md`
§2 (cộng ba file governance dùng chung và `.gitignore`).

## 4. Kiểm chứng TRÊN nhánh integration (baseline MỚI, đo lại từ đầu)

```text
$ .venv/bin/python -m pytest tests/test_r51_repair2_run_refreshes_projection.py -q
15 passed in 5.17s

$ .venv/bin/python -m pytest tests/ -q
3275 passed, 11 skipped in 203.22s (0:03:23)
```

`3275` — KHÁC `3461` của nhánh `R6` (đúng, và đúng hướng: thiếu ~186 bài test
`R6` không có mặt ở đây, đúng bằng số bài `tests/test_r6_*.py` trên nhánh gốc).
**0 failed.**

```text
$ .venv/bin/python scripts/r51_crossrepo_smoke.py
[…]
5) REPAIR-2: upload/run THẬT, KHÔNG mở bảng chọn phân loại
  … (13 dòng ok)
6) REPAIR-2 (lần 2): bản chiếu CŨ một phần — mã mới thiếu nhãn
  … (7 dòng ok)
KẾT QUẢ SMOKE: 83 PASS, 0 FAIL
```

Cả hai ca "projection trống" (§5) và "projection cũ" (§6) chạy lại được TRÊN
nhánh integration, qua ĐÚNG producer Tracking thật, không cần `R6`.

```text
$ git diff --check origin/claude/extract-upload-repo-gq2ws4...HEAD   → sạch

$ .venv/bin/python governance/scripts/governance/validate_structure.py
GOVERNANCE STRUCTURE: PASS — 21 required paths
$ .venv/bin/python governance/scripts/governance/validate_project_state.py
PROJECT STATE: PASS
$ .venv/bin/python governance/scripts/governance/validate_evidence.py
EVIDENCE VALIDATION: PASS — 161 REQUIRED PASS evidence record(s)
$ .venv/bin/python governance/scripts/governance/validate_task_completion.py
TASK COMPLETION: PASS — 14 DONE task(s)
$ .venv/bin/python governance/scripts/governance/validate_reference_integrity.py
REFERENCE INTEGRITY: FAIL — ĐÚNG 4 finding BASELINE (S136/TASK-REM-T06, không
                            liên quan REPAIR-2, không finding nào mới)
```

## 5. Push

```text
$ git push -u origin claude/r51-repair-2-integration
```

SHA/output nguyên văn: xem xác nhận cuối phiên (ghi lại NGAY SAU khi lệnh
push thực thi).

## 6. Trạng thái cuối

```text
Branch                claude/r51-repair-2-integration
Nguồn                 origin/claude/extract-upload-repo-gq2ws4 @ 05f2b44
Commit repair         d921dc9 (= a14df7c cherry-pick), d6640d4 (= f891393
                       cherry-pick) — cả hai giữ -x, trace về commit gốc
R6                     KHÔNG có mặt — xác nhận bằng diff scope (§3)
Full regression        3275 passed / 11 skipped / 0 failed (nhánh integration,
                       KHÔNG so trực tiếp với 3461 của nhánh R6 — khác tập test)
Smoke R5.1              83 PASS / 0 FAIL
Governance validator    structure/project_state/evidence/task_completion PASS;
                       reference_integrity = 4 baseline cũ, không mới
git diff --check       sạch
Merge / Deploy          KHÔNG thực hiện
Kết luận                READY_FOR_INDEPENDENT_REVIEW
```

**Independent Review của `R5.1 REPAIR-2` nên chạy trên `claude/r51-repair-2-
integration`, không phải trên `claude/r6-business-analytics-dashboard-it73x5`
— để không kéo theo `R6` (đang `BLOCKED`) vào phạm vi review.**
