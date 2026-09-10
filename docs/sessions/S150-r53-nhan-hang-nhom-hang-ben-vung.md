# BÀN GIAO SESSION (SESSION HANDOFF)

Session ID:
S150

Task:
`R5.3` — `docs/tasks/R5-3-nhan-hang-nhom-hang-song-qua-restart.md`

Task Mode:
MAJOR (repair lỗi production)

Project Profile:
PRODUCT

Status:
IMPLEMENTED — CHƯA `DONE`, CHƯA merge, CHƯA deploy.

## 0. Toạ độ

```text
Reports base           c46e458ef6e6653b7cba210dc4393e1160f158dd
                       (= origin/claude/extract-upload-repo-gq2ws4, nhánh
                        MẶC ĐỊNH THẬT trên origin — xác minh bằng
                        `git remote show origin` → "HEAD branch", KHÔNG giả
                        định là "main")
Reports nhánh làm việc claude/r5-3-reports-brand-category-j37izs
Reports HEAD           (xem commit của phiên này trên nhánh trên)
Tracking dependency    main @ b7c5f3b0ef13548e4d378e392b6ccd2f1be0d946 (R5.2.2)
                       — xác minh là TỔ TIÊN của origin/main hiện tại
                       (0f7347b, R5.2.3) bằng
                       `git merge-base --is-ancestor b7c5f3b origin/main`
Tracking đổi           KHÔNG một dòng nào (chỉ đọc, chỉ chạy producer smoke)
```

## 1. Preflight đã thực hiện

```text
git remote show origin (Reports)  HEAD branch: claude/extract-upload-repo-gq2ws4
git fetch + so HEAD               0 ahead / 0 behind, worktree sạch lúc bắt đầu
git remote show origin (Tracking) HEAD branch: main
git fetch origin main             66787c0..0f7347b
merge-base --is-ancestor b7c5f3b  YES — Tracking main CHỨA b7c5f3b
```

`scripts/branch_authority_check.sh` dừng ở `BRANCH AUTHORITY UNRESOLVED` vì
nhánh làm việc chưa có upstream — đúng như nó phải làm trước lần push đầu
tiên. Nó sẽ phân giải sau `git push -u origin
claude/r5-3-reports-brand-category-j37izs`.

## 2. Audit — chuỗi production, đo từng tầng TRƯỚC khi sửa

Chỉ thị của Owner: *"không được coi R5.1 cũ là đã hoạt động chỉ vì code hoặc
test cũ từng xanh"*. Phiên này vì thế đo lại TỪNG tầng trên đường thật, dùng
một mã đã `CONFIRMED` có đủ ba trường từ producer Tracking thật.

### 2.1 Tracking producer — ĐÚNG

`node kiem/smoke/sinh-catalog-reports.mjs` (chạy `chieuBoard()` THẬT của
`src/index.js` @ `0f7347b`):

```text
55Q6FA   {name, alt, model_label: "QLED 55Q6FA", brand: "Samsung",
          category_label: "Tivi"}
RT38     {..., model_label: "RT38", brand: "Samsung",
          category_label: "Tủ lạnh"}
XUNG-01  {..., brand: null, category_label: "Tivi"}
```

Hợp đồng năm trường còn nguyên sau `R5.2.2`/`R5.2.3`. **Không có blocker hợp
đồng** ⟹ `R5.3` KHÔNG chạm Tracking.

### 2.2 Capture + loader của Reports — ĐÚNG

`tools/tracking/capture_tracking_catalog._rows_from_board` ghi đủ ba trường
tuỳ chọn; `app/modules/pricing/resolution/sources.load_tracking_catalog_
capture` đọc lại đủ ba, từ chối sai kiểu, và đọc artifact đời cũ như cũ.
Đo bằng smoke §2: `[model_label, brand, category_label]` của `MGS-01` =
`["FV1412", "LG", "Máy giặt"]`.

### 2.3 `POST /run` → `catalog_display` → tab Nhân viên — ĐÚNG

`scripts/r51_crossrepo_smoke.py` trên nền `c46e458`: `83 PASS / 0 FAIL`,
bao gồm §5 "upload/run THẬT, KHÔNG mở bảng chọn". `R5.1 REPAIR-2` thật sự đã
sửa đúng thứ nó nói là đã sửa.

### 2.4 Chỗ ĐỨT — đo trực tiếp

Reproduction chạy trên nền `c46e458` (bài kiểm tạm, sau đó thành
`test_the_labels_survive_a_container_restart`):

```text
TRUOC RESTART product: ['55Q6FA', 'Tủ lạnh Test-3']
TRUOC RESTART brand  : ['Samsung', '—']
TRUOC RESTART cat    : ['Tivi', '—']
SAU  RESTART product: ['55Q6FA', 'Tủ lạnh Test-3']
SAU  RESTART brand  : ['—', '—']
SAU  RESTART cat    : ['—', '—']
E   AssertionError: SAU RESTART: nhãn Hãng biến mất dù run snapshot vẫn
    còn trong DB
```

"RESTART" ở đây = xoá thư mục chứa `tracking_display.json` và KHÔNG đụng
database — đúng việc Render làm ở mỗi deploy (`render.yaml`: *"KHÔNG có
`disk:` — S071B stateless"*).

**Nguyên nhân gốc:** nhãn sống trên đĩa EPHEMERAL, tiền sống trong PostgreSQL.
Hai nửa của cùng một màn hình có hai vòng đời khác nhau, và không đường nào
dựng lại nửa đã chết. Chi tiết đầy đủ: task file §1.

**Vì sao bộ kiểm cũ không bắt được:**
`tests/test_r51_repair2_run_refreshes_projection.py` trỏ
`DEFAULT_DISPLAY_PATH` vào `tmp_path` và không bao giờ dọn nó giữa lúc chạy
và lúc render — trong một tiến trình test, đĩa không bao giờ biến mất.

## 3. Dữ liệu đi qua từng tầng SAU sửa

```text
Tracking chieuBoard()                      brand="Samsung" category_label="Tivi"
  → /api/xuat/board                        (hợp đồng 5 trường, KHÔNG đổi)
  → capture_tracking_catalog.build_capture rows[].brand / .category_label
  → POST /run: MỘT lần pull duy nhất       (CHECK-R53-04)
      ├─ pricing / daily-min               KHÔNG đổi
      ├─ resolver mapping                  KHÔNG đổi
      ├─ catalog_display.write()           cache đĩa (R5.1 REPAIR-2, giữ nguyên)
      └─ _persist_tracking_display(run_id) tracking_display_snapshot  ← MỚI
  → GET /kinh-doanh/nhan-vien
      └─ _tracking_display()               cache đĩa nếu còn;
                                           NGƯỢC LẠI dựng lại từ bản BỀN
                                           rồi ghi lại cache          ← MỚI
      └─ _catalog_labels()                 CHỈ mapping CONFIRMED (cổng CŨ)
      └─ _catalog_field()                  CHỈ MATCHED_TRACKING (cổng CŨ)
      → ô Mặt hàng / Hãng / Nhóm hàng
```

Hai cổng chặn (`_catalog_labels`, `_catalog_field`) KHÔNG bị chạm; đường đọc
mới trả về đúng cùng một `dict` mà đường cũ trả về.

## 4. Kết quả kiểm chứng

### 4.1 Bài mới — ĐỎ trước sửa, XANH sau

`git stash push app/web/server.py` (gỡ đúng phần wiring) rồi chạy
`tests/test_r53_durable_tracking_labels.py`:

```text
8 failed, 11 passed
FAILED ...::test_the_run_stores_the_labels_durably_with_the_capture_it_used
FAILED ...::test_the_labels_survive_a_container_restart
FAILED ...::test_the_rebuild_writes_the_disk_cache_back
FAILED ...::test_the_rebuild_never_pulls_tracking
FAILED ...::test_a_legacy_capture_without_the_new_fields_never_crashes_or_guesses
FAILED ...::test_a_legacy_capture_does_not_erase_labels_an_earlier_run_stored
FAILED ...::test_a_confirmed_code_with_no_brand_shows_the_category_and_dashes_the_brand
FAILED ...::test_wiping_or_corrupting_the_cache_moves_no_money
```

Sau khi khôi phục: `19 passed`.

### 4.2 Smoke `R5.3` — xuyên hai repo, producer Tracking THẬT

`.venv/bin/python scripts/r53_crossrepo_smoke.py`:

```text
1) Tracking sinh board/alias bằng chính `chieuBoard()` thật        2 ok
2) Reports chụp capture từ payload THẬT của Tracking               1 ok
3) upload/run THẬT → tab Nhân viên                                 8 ok
4) RESTART container: xoá đĩa ephemeral, KHÔNG đụng database       9 ok
5) Dòng chưa xác nhận: dấu gạch, không suy từ tên kế toán          2 ok
6) Mất cả hai nơi lưu ⟹ cảnh báo, không im lặng                    2 ok

KẾT QUẢ SMOKE: 25 PASS, 0 FAIL
```

Bốn khẳng định trung tâm của §4, nguyên văn:

```text
  ok   lần chạy đã lưu BỀN bản chiếu, kèm capture đã dùng
  ok   bản bền mang NGUYÊN VĂN nhãn của capture Tracking thật
  ok   R5.3: Hãng vẫn hiện sau restart
  ok   restart KHÔNG đổi một đồng nào của bảng kê
```

### 4.3 Full regression

```text
nền (c46e458, cây sạch)   3608 passed / 23 skipped / 0 failed
sau R5.3                  3628 passed / 23 skipped / 0 failed
tests collected           3631 → 3651  (+20, KHÔNG bài nào bị xoá)
```

`+20` = 19 bài của `tests/test_r53_durable_tracking_labels.py` + 1 bài mới
trong `tests/test_r51_repair2_run_refreshes_projection.py`.

### 4.4 Golden và smoke của các vertical khác

```text
tests/test_golden_baseline.py     58 passed / 2 skipped   (KHỚP bản ghi R5.2)
TestG25GoldenBaselineUnchanged    3 passed
smoke R5.1                        86 PASS / 0 FAIL        (nền 83; xem §5)
smoke R6                          29 PASS / 0 FAIL        (KHỚP bản ghi DEC-210)
```

> **Lưu ý môi trường.** Clone của phiên này ban đầu là SHALLOW, nên
> `TestG25GoldenBaselineUnchanged` đỏ với `fatal: bad object 740f396a...` —
> một lỗi MÔI TRƯỜNG, tái hiện y hệt trên cây SẠCH (`git stash`). Đã sửa
> bằng `git fetch --unshallow origin`; sau đó nó PASS. Nó KHÔNG phải một
> finding của `R5.3`, và số nền `3608 passed` ở §4.3 được đo SAU khi
> unshallow, trên cây sạch.

### 4.5 Validator governance

```text
structure            PASS  (Deployment root PASS, 21 required paths)
project_state        PASS
evidence             PASS  (161 REQUIRED PASS records)
task_completion      PASS  (14 DONE tasks)
reference_integrity  4 finding — ĐÚNG 4 baseline cũ (S136 ×1,
                     TASK-REM-T06 ×3). KHÔNG có reference mới hỏng.
git diff --check     sạch
```

## 5. Hai khẳng định đã đổi NGHĨA (không nới lỏng) — nói ra tường minh

`R5.3` đổi hành vi của đúng MỘT ca mà `R5.1 REPAIR-2` đã nghiệm thu, và đổi
theo đúng chiều mà `R5.3` sinh ra để đổi: **mất file cache trên đĩa không
còn là mất bản chiếu.** Hai chỗ khẳng định điều cũ vì thế phải cập nhật:

```text
tests/test_r51_repair2_run_refreshes_projection.py
  ::test_the_employee_tab_warns_when_the_projection_is_missing
      ĐIỀU KIỆN đổi: nay dọn CẢ hai nơi lưu để dựng ca "bản chiếu thật sự
      VẮNG". MỆNH ĐỀ giữ nguyên: vắng bản chiếu mà bảng im lặng là lỗi.
  ::test_losing_only_the_disk_cache_rebuilds_the_labels_and_stays_silent
      BÀI MỚI, đo mặt còn lại: mất cache ⟹ nhãn dựng lại, không cảnh báo.

scripts/r51_crossrepo_smoke.py §5
      "mất bản chiếu ⟹ CẢNH BÁO" tách thành 4 khẳng định: dựng lại được ·
      không cảnh báo · cache được ghi lại · mất CẢ HAI thì VẪN cảnh báo.
```

Không một phép chặn nào được nới. `tests/test_web_server.py` cập nhật hình
dạng `tracking_evidence` (thêm khoá `durable`) — bằng chứng nói thêm, không
nói khác.

## 6. File Đã Thay Đổi (Files Changed)

Created:
- `tools/db/migrations/versions/0012_tracking_display_snapshot.py`
- `tests/test_r53_durable_tracking_labels.py`
- `scripts/r53_crossrepo_smoke.py`
- `docs/tasks/R5-3-nhan-hang-nhom-hang-song-qua-restart.md`
- `docs/sessions/S150-r53-nhan-hang-nhom-hang-ben-vung.md`

Modified:
- `tools/db/schema.py` — `+tracking_display_snapshot`, `+TRACKING_DISPLAY_TABLES`
- `tools/db/__init__.py` — `ALEMBIC_HEAD` → `0012_tracking_display_snapshot`
- `app/web/history_store.py` — `write_tracking_display`,
  `latest_tracking_display`
- `app/web/catalog_display.py` — `normalise()` (tách khỏi `read()`),
  `restore()`, `REASON_NO_STORE`
- `app/web/server.py` — `_durable_tracking_display`, `_tracking_display`,
  `_persist_tracking_display`; `_refresh_catalog_display` trả tuple;
  bốn đường đọc bản chiếu đi qua một cửa duy nhất
- `app/web/workspace_presentation.py` — `_product_title` (tooltip tên trên sổ)
- `app/web/templates/kinh_doanh_nhan_vien.html` — `title` trên ô Mặt hàng
- `scripts/r51_crossrepo_smoke.py` — §5 theo nghĩa mới
- `tests/test_history_db.py`, `tests/test_phb06_brand_reporting.py`,
  `tests/test_phb07_advanced_analytics.py`,
  `tests/test_r51_repair2_run_refreshes_projection.py`,
  `tests/test_web_server.py`
- `PROJECT/PROJECT_PROGRESS.md`, `PROJECT/PROJECT_DECISIONS.md`,
  `PROJECT/REVIEW_BUDGET_LEDGER.md`

Deleted:
- (không)

## 7. Quyết Định Chính (Key Decisions)

- `DEC-217` — nhãn hiển thị Tracking lưu BỀN theo `run_id`; file trên đĩa
  xuống hạng CACHE. Xem `PROJECT/PROJECT_DECISIONS.md`.
- Điều kiện dựng lại là **cache RỖNG**, không phải "cache thiếu vài mã": một
  cache thiếu một phần là ca mà `R5.1 REPAIR-2` vòng 2 đã đo bằng LỊCH SỬ ghi,
  và dựng lại đè lên nó sẽ xoá mất chính bằng chứng ấy.
- Capture không mang nhãn nào ⟹ KHÔNG ghi đè, ở CẢ HAI nơi lưu — hai nơi lệch
  luật sẽ cho hai màn hình khác nhau cho cùng một lần chạy.
- Bảng mới KHÔNG có khoá ngoại tới `source_snapshot`: ghi nhãn là best-effort
  và không được phép rollback một lần nạp sổ đã đúng.

## 8. Rủi Ro / Vướng Mắc (Risks / Blockers)

- `AR-R5.3-01` — bản chiếu đọc là của lần chạy GẦN NHẤT, không tra ngược từ
  dòng về lần chạy đã sinh ra nó (tầng nghiệp vụ không chở `run_id` xuống
  dòng, và luồn nó xuống là sửa đúng những đường `R5.3` bị cấm chạm). Hành vi
  này ĐÚNG BẰNG cache đĩa từ `R5` §5 — không phải hồi quy do `R5.3` gây ra.
- `AR-R5.3-02` — mất database là mất cả tiền lẫn nhãn; nhãn không tệ hơn tiền.
- `AR-R5.3-03` — môi trường không có history store ⟹ hành vi đúng bằng
  `R5.1 REPAIR-2`, và bằng chứng của run ghi `NO_STORE`.
- **Ngân sách review lineage `R5` = `0 remaining`.** Phiên này KHÔNG tự tiêu
  và KHÔNG tự miễn một cycle. Cần Owner/reviewer xác nhận — xem task §8 và
  `PROJECT/REVIEW_BUDGET_LEDGER.md`.

## 9. Cách tái hiện trên production

```text
1. Deploy nhánh này (Alembic tự chạy `upgrade head` trong CMD của Dockerfile;
   0012 là ADDITIVE thuần, không backfill).
2. Mở Reports → tải sổ kế toán → bấm chạy báo cáo.
3. Mở tab Nhân viên, sheet của nhân viên có dòng đã CONFIRMED.
   ⟹ cột Mặt hàng hiện MODEL NGẮN, Hãng và Nhóm hàng hiện giá trị Tracking,
      KHÔNG cần mở bảng chọn phân loại. Rê chuột lên ô Mặt hàng ⟹ tooltip
      hiện tên dài trên sổ kế toán.
4. Kích hoạt một lần restart/deploy của Render (hoặc chờ một lần bất kỳ).
5. Mở LẠI tab Nhân viên, CÙNG kỳ, KHÔNG chạy lại báo cáo.
   ⟹ ba ô vẫn hiện đúng như bước 3. TRƯỚC `R5.3` chúng là `—`.
6. Đối chứng: một dòng CHƯA phân loại vẫn giữ tên thô và `—` ở cả hai cột.
```

## 10. Chưa Được Thay Đổi (Do Not Change Yet)

- Không merge, không deploy — phiên này không có thẩm quyền đó.
- `CHECK-R53-13` (Independent Review) và `CHECK-R53-14` (Owner nghiệm thu)
  giữ `NOT_TESTED`.
- `CHECK-R51R2-15`/`CHECK-R51R2-16` của `R5.1 REPAIR-2` KHÔNG bị `R5.3` đóng.
- `R6` không được mở trong phiên này.

## 11. Session Tiếp Theo Được Khuyến Nghị

Independent Review `R5.3` (`CHECK-R53-13`), trên đúng nhánh
`claude/r5-3-reports-brand-category-j37izs`, kèm câu hỏi ngân sách ở §8 để
Owner/reviewer quyết.

## 12. File Agent Tiếp Theo Cần Đọc

- `CLAUDE.md`
- `PROJECT/PROJECT_PROGRESS.md`
- `docs/tasks/R5-3-nhan-hang-nhom-hang-song-qua-restart.md`
- `docs/tasks/R5-1-REPAIR-2-run-refreshes-catalog-display.md`
- `PROJECT/REVIEW_BUDGET_LEDGER.md` → Root Task `R5`
- `app/web/catalog_display.py`, `app/web/server.py` (`_tracking_display`)
- `tools/db/migrations/versions/0012_tracking_display_snapshot.py`
