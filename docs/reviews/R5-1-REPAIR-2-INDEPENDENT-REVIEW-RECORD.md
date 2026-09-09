# `R5.1 REPAIR-2` — Bản ghi Independent Review (bằng chứng nguyên văn)

Ngày: 2026-09-09
Kết luận: **`ACCEPT_WITH_RECORDED_RISK`**
Phiên chỉ ĐỌC, CHẠY, TẠO PROBE và KIỂM — không sửa một dòng mã sản phẩm nào.

---

## 0. Đối tượng review và preflight

```text
Repo      Reports
Nhánh     claude/r51-repair-2-integration
HEAD      98778bc795dea62e78a23b4afa65c3cee304c890
Nền       origin/claude/extract-upload-repo-gq2ws4 @ 05f2b443e66ee4702d03c003d5f1f960b5765f8d
```

```text
$ git rev-parse claude/r51-repair-2-integration origin/claude/r51-repair-2-integration
98778bc795dea62e78a23b4afa65c3cee304c890
98778bc795dea62e78a23b4afa65c3cee304c890

$ git rev-parse origin/claude/extract-upload-repo-gq2ws4
05f2b443e66ee4702d03c003d5f1f960b5765f8d

$ git merge-base --is-ancestor 05f2b44 98778bc && echo "YES: base is ancestor"
YES: base is ancestor

$ git merge-base 05f2b44 98778bc
05f2b443e66ee4702d03c003d5f1f960b5765f8d

$ git status --porcelain
(rỗng — WORKTREE CLEAN)

$ git log --oneline --no-decorate 05f2b44..98778bc
98778bc S148: chuẩn bị integration branch cho R5.1 REPAIR-2, tách khỏi R6
d6640d4 R5.1 REPAIR-2 (vòng 2): cảnh báo khi bản chiếu CŨ một phần
d921dc9 R5.1 REPAIR-2: luồng chạy báo cáo làm mới bản chiếu hiển thị
```

`branch_authority_check.sh` xác nhận nền đúng là nhánh mặc định thật trên
origin, và `WORKTREE = CLEAN`:

```text
DEFAULT_BRANCH       : claude/extract-upload-repo-gq2ws4
DEFAULT_TIP          : 05f2b443e66ee4702d03c003d5f1f960b5765f8d
HEAD_SHA             : 98778bc795dea62e78a23b4afa65c3cee304c890
WORKTREE             : CLEAN
```

Script trả `STOP` vì **nhánh review cục bộ chưa có upstream** — đó là trạng
thái của nhánh review phiên này, KHÔNG phải của nội dung được review.

### Diff KHÔNG mang `R6`

```text
$ git diff --name-status 05f2b44..98778bc
M	.gitignore
M	PROJECT/PROJECT_DECISIONS.md
M	PROJECT/PROJECT_PROGRESS.md
M	PROJECT/REVIEW_BUDGET_LEDGER.md
M	app/web/catalog_display.py
M	app/web/server.py
M	app/web/templates/kinh_doanh_nhan_vien.html
A	docs/sessions/S146-r51-repair-2-run-refreshes-projection.md
A	docs/sessions/S147-r51-repair-2-stale-projection-warning.md
A	docs/sessions/S148-r51-repair-2-integration-branch.md
A	docs/tasks/R5-1-REPAIR-2-run-refreshes-catalog-display.md
M	scripts/r51_crossrepo_smoke.py
A	tests/test_r51_repair2_run_refreshes_projection.py
M	tests/test_web_server.py
```

Không một module/route/template/test/tài liệu `R6` nào có mặt. Mọi lần xuất
hiện chuỗi `R6` trong diff đều nằm trong VĂN XUÔI của tài liệu phiên
(`S146`/`S147`/`S148`) giải thích việc tách nhánh, hoặc trong đoạn Evidence
trích nguyên văn lịch sử — không phải mã.

```text
$ git diff --check 05f2b44..98778bc
(rỗng)
```

Repo `Tracking` KHÔNG bị đụng tới — bản sửa nằm hoàn toàn trong `Reports`:

```text
$ cd ../Tracking && git diff --stat origin/main...HEAD
(rỗng)
```

Điều này quan trọng cho chuỗi 1: smoke xuyên repo chạy trên mã producer
Tracking NGUYÊN BẢN, không phải một bản đã chỉnh cho vừa bài kiểm.

---

## 1. Luồng chính — producer Tracking thật → `POST /run` → tab Nhân viên

Smoke xuyên hai repo với `node v22.22.2` và repo Tracking thật:

```text
$ .venv/bin/python scripts/r51_crossrepo_smoke.py --tracking ../Tracking

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

KẾT QUẢ SMOKE: 83 PASS, 0 FAIL
```

Probe ĐỘC LẬP của phiên review (viết riêng, không dùng lại assertion của tác
giả) xác nhận cùng kết luận trên đúng luồng người dùng thật — upload → `POST
/run` → mở tab Nhân viên, KHÔNG mở popover phân loại:

```text
test_confirmed_row_shows_model_brand_category_without_popover  PASS
  Mặt hàng   = "55Q6FA"        (model_label ngắn, KHÔNG phải tên sổ kế toán)
  Hãng       = "Samsung"       (brand)
  Nhóm hàng  = "Tivi"          (category_label)
  RAW_PRODUCT "Máy lạnh Test-2" KHÔNG còn xuất hiện ở cột Mặt hàng
  Không có cảnh báo nào (bản chiếu lành)
```

**Lỗi production đã được đóng đúng chỗ.**

---

## 2. Projection trống — tự dựng lại, KHÔNG pull Tracking lần hai

Probe độc lập đếm số lần `live_pull.pull_live_captures` được gọi trong MỘT
`POST /run`:

```text
test_run_does_not_pull_tracking_a_second_time                  PASS
  projection KHÔNG tồn tại trước khi chạy
  POST /run → 302, projection ĐƯỢC dựng lại
  số lần pull Tracking = 1   (đúng MỘT, không có lần thứ hai)
```

Và bản chiếu được dựng từ capture của CHÍNH lần chạy đó, trong khi file
capture còn trên đĩa (tức TRƯỚC `finally: live_handle.cleanup()`):

```text
test_projection_rebuilt_before_capture_cleanup                 PASS
  tại thời điểm load_tracking_catalog_capture: capture file EXISTS = True
```

`_refresh_catalog_display` chỉ đọc `captures.tracking_catalog` đã có; nó không
gọi `_select_captures_for_run` và không gọi `live_pull`. **Xác nhận: không có
lần pull Tracking thứ hai.**

---

## 3. Projection cũ một phần — cảnh báo nói đúng chuyện

Hai ca được dựng độc lập: nhãn CŨ đã có cho một mã, một mã CONFIRMED MỚI chưa
có nhãn, và lần refresh mới thất bại.

```text
test_stale_warning_distinguishes_from_unclassified             PASS
  lần chạy 1 → last_write_status = written=True
  xác nhận mã MỚI (RT38) SAU lần ghi thành công đó
  lần chạy 2 với capture đời cũ → reason = NO_METADATA
  tab Nhân viên: cảnh báo kind="cu"
  câu chữ chứa "CHƯA được nạp" — nói rõ nhãn CŨ/chưa làm mới
  nhãn CŨ (55Q6FA / Samsung) còn nguyên

test_write_failed_case_warns_separately                        PASS
  ghi bản chiếu ném OSError → reason = WRITE_FAILED
  cảnh báo kind="cu", câu chữ chứa "KHÔNG ghi được"
```

Cảnh báo KHÔNG đánh đồng với "chưa phân loại": nó chỉ nổi lên khi có BẰNG
CHỨNG lần ghi gần nhất hỏng (`last_write_status()`), chứ không suy đoán từ
việc thiếu nhãn một mình. Khi không có mapping nào được xác nhận, tab Nhân
viên KHÔNG hiện cảnh báo bản chiếu — đúng, vì ở đó dấu gạch có lý do khác:

```text
test_unconfirmed_rows_keep_raw_name_and_dash                   PASS
  không mapping nào CONFIRMED → giữ tên gốc + "—", KHÔNG có cảnh báo
```

---

## 4. Hàng rào dữ liệu — không suy diễn, không lộ metadata sai

```text
test_out_of_catalog_code_gets_no_metadata_leak                 PASS
  mã CONFIRMED không có trong danh mục → fallback về CHÍNH mã Tracking
  KHÔNG rơi về tên sổ kế toán; brand KHÔNG mượn của dòng khác

test_no_metadata_leak_between_two_codes                        PASS
  products = ['55Q6FA', 'RT38']
  brands   = ['Samsung', '—']
  cats     = ['Tivi', '—']
  bản chiếu trên đĩa KHÔNG tự bịa dòng cho mã không có metadata

test_stale_target_mapping_keeps_raw_name                       PASS
  danh mục bỏ mã (present_in_board=False) → KHÔNG rơi về tên sổ kế toán

test_projection_never_contains_accounting_names                PASS
  file bản chiếu KHÔNG chứa tên sổ kế toán, KHÔNG chứa tên danh mục thô;
  mỗi dòng CHỈ có đúng 3 trường model_label/brand/category_label
```

Smoke xuyên repo bổ sung: `dòng conflict giữ TÊN THÔ`, `ghép EXACT không đọc
nhóm hàng`, và envelope không lộ ngành hàng thô/giá vốn/giá chốt/tồn kho/link
nội bộ.

Cổng lọc là `identity_gateway.confirmed_identities()` (`server.py:1764`): một
dòng tranh chấp, stale target, `OUT_OF_CATALOG` hay chưa phân loại đều KHÔNG
có khoá trong bảng nhãn, nên không có đường nào để metadata chảy vào chúng.
**Không có nhánh nào suy model/hãng từ tên hàng kế toán.**

---

## 5. Bất biến nghiệp vụ — bản chiếu chỉ mang NHÃN

```text
test_money_and_row_counts_identical_before_and_after_projection_loss  PASS
  so sánh line-revenue / line-profit / line-quantity TRƯỚC và SAU khi
  xoá bản chiếu: GIỐNG HỆT
  số dòng: KHÔNG đổi
  sau khi xoá: cảnh báo kind="vang" xuất hiện

test_repeated_runs_are_idempotent_for_money                    PASS
  chạy lần hai KHÔNG đổi một ô nào trên sheet
```

Artifact/capture đời cũ thiếu metadata KHÔNG crash, và quan trọng hơn: nó
KHÔNG xoá nhãn đã có:

```text
test_legacy_capture_without_metadata_does_not_crash_and_keeps_old_labels  PASS
  nội dung bản chiếu SAU lần chạy capture đời cũ == nội dung TRƯỚC đó
```

Smoke xác nhận thêm: `tổng tiền KHÔNG đổi sau khi nhóm hàng xuất hiện`, `đổi
nhóm hàng bên Tracking ... KHÔNG đổi một đồng nào`, `tổng tiền KHÔNG đổi vì
bản chiếu CŨ/thiếu nhãn`, `artifact cũ vẫn load được`.

---

## 6. Độ bền và vận hành

### `.gitignore`

```text
$ git check-ignore -v data/product_identity/tracking_display.json \
                      data/product_identity/tracking_display.status.json
.gitignore:40:data/product_identity/tracking_display.json	...
.gitignore:41:data/product_identity/tracking_display.status.json	...

$ git ls-files data/product_identity/
data/product_identity/mappings.jsonl
```

Cả hai file runtime đều KHÔNG được theo dõi; `mappings.jsonl` (log quyết định
Product Identity — dữ liệu THẬT) vẫn được theo dõi. Đúng.

### Evidence của run

```text
test_run_evidence_records_catalog_display                      PASS
  tracking_evidence["catalog_display"] = {"written": True, "rows": 1,
                                          "reason": None}
  đúng BA trường written / rows / reason

test_evidence_merge_preserves_existing_keys                    PASS
  keys = ['catalog_display', 'tracking_catalog_capture_id']
  khoá evidence có TRƯỚC KHÔNG bị ghi đè
```

### File trạng thái không đọc được

```text
test_unreadable_status_file_degrades_to_silence_not_crash      PASS
  status file hỏng → last_write_status() = None → trang VẪN render,
  nhãn vẫn đúng, tiền vẫn đúng, không cảnh báo (TRUNG TÍNH)

test_torn_projection_file_degrades_to_warning_not_crash        PASS
  bản chiếu rách → read() = {} → trang render + cảnh báo kind="vang"

test_projection_row_with_wrong_types_is_dropped_not_rendered   PASS
  giá trị sai kiểu (int/list/dict) → None, KHÔNG render ra màn hình
```

File trạng thái là file RIÊNG cạnh bản chiếu, không phải một khoá nhồi vào
bản chiếu — nên không thể va với một mã Tracking trùng tên:

```text
test_status_file_is_separate_from_projection                   PASS
```

---

## 7. Bộ kiểm đầy đủ

```text
$ .venv/bin/python -m pytest -q tests/test_r51_repair2_run_refreshes_projection.py
15 passed in 3.82s

$ .venv/bin/python -m pytest -q tests/test_web_server.py \
    tests/test_r5_product_identity_fields.py tests/test_r5_workspace_identity_ux.py \
    tests/test_tracking_authoritative_identity.py tests/test_tracking_catalog_capture.py \
    tests/test_sales_presentation.py tests/test_105d_identity_keys.py \
    tests/test_bh73804_confirmed_identity.py
180 passed in 3.34s

$ .venv/bin/python -m pytest -q
3275 passed, 11 skipped in 175.14s (0:02:55)
```

Con số này TÁI LẬP CHÍNH XÁC bằng chứng `S148` ghi (`3275 passed, 11
skipped`).

Probe độc lập của phiên review: **19/19 PASS** (3 file probe, viết riêng).

### Hai lỗi BASELINE tách ra khỏi nội dung review

1. **`tests/test_105d_boundaries.py::TestG25GoldenBaselineUnchanged`** đỏ ở
   lần chạy đầu với `fatal: bad object 740f396...`. Nguyên nhân: clone của
   môi trường review là clone NÔNG (`.git/shallow` graft tại `4cdfaaf`, 96
   commit). File test này KHÔNG nằm trong diff. Sau `git fetch --unshallow`,
   bài chạy XANH. **Không phải lỗi của `REPAIR-2`.**

2. **`validate_reference_integrity` = FAIL, 4 reference.** Chạy validator này
   trên ĐÚNG nền `05f2b44` (worktree riêng) cho ra **y hệt 4 reference đó**.
   Cả 4 nằm trong file KHÔNG thuộc diff (`S136`, `TASK-REM-T06`). 7 file `.md`
   mới của `REPAIR-2` (289 → 296 file quét) KHÔNG thêm một reference hỏng nào.
   **Có sẵn từ nền, không phải của `REPAIR-2`.**

### Validator còn lại

```text
GOVERNANCE STRUCTURE: PASS   (21 required paths)
PROJECT STATE:        PASS
EVIDENCE VALIDATION:  PASS   (161 REQUIRED PASS evidence record)
TASK COMPLETION:      PASS   (14 DONE task)
```

---

## 8. Finding

```text
REPAIR_REQUIRED     0
ACCEPTED_RISK mới   2   AR-R5.1R2-01, AR-R5.1R2-02
Lỗi BASELINE tách   2   1 bài pytest (clone nông) + 4 reference integrity
Repair cycle tiêu   0   (phiên review không tiêu cycle)
```

### `AR-R5.1R2-01` — `NO_SNAPSHOT` không kích hoạt cảnh báo "CŨ một phần"

Cảnh báo hình dạng 2 chỉ nổi lên khi `reason ∈ {NO_METADATA, WRITE_FAILED}`.
Nếu lần ghi lúc xác nhận mapping thất bại (`WRITE_FAILED`) rồi một lần chạy
SAU đó ghi đè trạng thái bằng `NO_SNAPSHOT`, một mã CONFIRMED thiếu nhãn sẽ
KHÔNG được cảnh báo.

Phiên review đã ĐO khả năng xảy ra trên đường production: một lần chạy KHÔNG
có capture danh mục **thất bại với HTTP 400 ngay tại `run_owner_report`**,
TRƯỚC khi tới bước làm mới bản chiếu — nên `NO_SNAPSHOT` gần như không đạt
tới được trên nhánh live đã cấu hình.

```text
xác suất    RẤT THẤP   (cần HAI lỗi liên tiếp; nhánh live trả 400 trước đó)
tác động    CHỈ NHÃN   (không sai một đồng, không sai mapping)
phát hiện   DỄ         (dòng hiện MÃ Tracking + "—", KHÔNG phải tên sổ kế
                        toán — triệu chứng production ban đầu KHÔNG tái diễn)
```

→ `ACCEPTED_RISK`. Không mở rộng phạm vi cho một lỗi hiếm, ít tác động, nhân
viên nhận ra được.

### `AR-R5.1R2-02` — ghi bản chiếu + trạng thái không nguyên tử

`write_text` không nguyên tử và không có khoá. Hai lần chạy đồng thời có thể
làm rách file. Phiên đã đo ca rách: `read()` trả `{}` → cảnh báo hình dạng
`vang` hiện lên, trang vẫn render, **tiền không đổi**.

```text
xác suất    THẤP       (beta một Owner, chạy tuần tự)
tác động    CHỈ NHÃN   (fail-safe: rách ⟹ nói ÍT đi, không nói SAI)
phát hiện   DỄ         (cảnh báo tự hiện)
```

→ `ACCEPTED_RISK`.

### Ghi nhận thêm (không phải finding)

Khi Tracking BỎ một mã khỏi danh mục, nhãn CŨ của mã đó được GIỮ (không bị
xoá). Đây là hành vi CÓ CHỦ ĐÍCH và đã ghi trong docstring module (ghi đè một
bản rỗng sẽ làm màn hình nói ÍT hơn vì một capture cũ). Nhãn hiển thị vẫn là
điều Tracking đã nói ở lần capture gần nhất — cũ, nhưng không bịa.

---

## 9. Kết luận

**`ACCEPT_WITH_RECORDED_RISK`**

Repair giải quyết ĐÚNG lỗi production đã báo: dòng đã `CONFIRMED` mapping nay
hiện `model_label` ngắn, `brand`, và `category_label` trên tab Nhân viên qua
luồng chính `POST /run`, KHÔNG cần mở popover phân loại — xác minh bằng
producer Tracking THẬT trên mã Tracking NGUYÊN BẢN. Bản chiếu tự dựng lại từ
capture của chính lần chạy, không thêm một lần gọi Tracking nào. Hàng rào dữ
liệu giữ nguyên: không suy diễn model/hãng từ tên sổ kế toán, không lộ
metadata sang dòng chưa xác nhận. Mọi bất biến tiền/mapping/export không đổi.

Hai `ACCEPTED_RISK` được ghi nhận ở trên: cả hai chỉ ảnh hưởng NHÃN và cảnh
báo, không làm sai tiền, và nhân viên nhận ra được.

Phiên review **KHÔNG** đánh dấu Owner Acceptance, **KHÔNG** merge, **KHÔNG**
deploy. Việc ngân sách review (`PROJECT/REVIEW_BUDGET_LEDGER.md` → "REPAIR-2
production (`S146`) — CẦN XÁC NHẬN ngân sách") có tiêu một repair cycle hay
không vẫn thuộc quyền Owner; phiên này không giả định theo chiều nào.

---

## 10. Lệnh tái lập

```bash
# 1. Lấy đúng HEAD được review
git fetch origin claude/r51-repair-2-integration
git checkout 98778bc795dea62e78a23b4afa65c3cee304c890
git status --porcelain          # phải RỖNG
git merge-base --is-ancestor 05f2b44 98778bc && echo "base is ancestor"

# LƯU Ý: nếu clone NÔNG, chạy trước để tránh lỗi baseline giả
git fetch --unshallow origin

# 2. Môi trường
python3 -m venv .venv
.venv/bin/pip install -e ".[dev,web,history,storage]"

# 3. Bộ kiểm
.venv/bin/python -m pytest -q tests/test_r51_repair2_run_refreshes_projection.py
.venv/bin/python -m pytest -q          # kỳ vọng 3275 passed, 11 skipped

# 4. Smoke xuyên hai repo (cần node + repo Tracking cạnh bên)
.venv/bin/python scripts/r51_crossrepo_smoke.py --tracking ../Tracking
#                                        kỳ vọng 83 PASS, 0 FAIL

# 5. Governance
git diff --check 05f2b44..98778bc
bash scripts/branch_authority_check.sh
for v in validate_structure validate_project_state validate_evidence \
         validate_reference_integrity validate_task_completion; do
  .venv/bin/python governance/scripts/governance/$v.py
done
```
