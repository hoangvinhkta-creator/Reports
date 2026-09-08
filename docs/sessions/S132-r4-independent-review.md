# S132 — R4: Independent Review (phiên review ĐỘC LẬP)

Phiên này chỉ ĐỌC và KIỂM. Không sửa một dòng mã sản phẩm nào, không merge,
không deploy, không đánh dấu Owner Acceptance của R3 hay của R4.

Task canonical: `docs/tasks/R4-bao-cao-danh-gia.md`.
Bàn giao triển khai: `docs/sessions/S131-r4-bao-cao-danh-gia.md`.
Đặc tả chỉ tiêu: `docs/spec/R4-DAC-TA-KPI.md`.

---

## 1. Kết luận

```text
KẾT LUẬN            ACCEPT_WITH_RECORDED_RISK
EXACT HEAD ĐÃ REVIEW  63a066e9275919df92bceaee58876f2724cf9df0
NỀN                   824b5d742dab07b8b0bd301d56748779e35076aa
REPAIR_REQUIRED       0 finding
ACCEPTED_RISK         4 finding mới (AR-R4-04 … AR-R4-07), không cái nào
                      làm sai một con số tiền hay một kết luận về kỳ
REPAIR CYCLE TIÊU     0  (ngân sách R4 vẫn 1 allowed / 0 used / 1 remaining)
CHECK-R4-23           PASS (phiên này)
CHECK-R4-24           NOT_TESTED — Owner nghiệm thu, KHÔNG phiên nào tự đóng
CHECK-R3-20           NOT_TESTED — R4 và phiên này KHÔNG chạm tới
```

Bảy chuỗi mà brief review yêu cầu (A…G) đều đã kiểm TRỰC TIẾP, và mọi con số
kiểm được đều đã được reviewer **tự tính lại độc lập** rồi mới đối chiếu với
màn hình. Không tìm được một đường nào mà một chỉ tiêu dẫn xuất từ lợi nhuận
ra số khi coverage chưa đủ 100 %, không tìm được một phép cộng sai, và không
tìm được một drill-down nào mở sai tập dòng.

---

## 2. Điều kiện mở phiên — đã xác nhận trước khi kiểm

```text
$ git remote show origin | head -3
* remote origin
  Fetch URL: https://github.com/hoangvinhkta-creator/Reports
  HEAD branch: claude/extract-upload-repo-gq2ws4

$ git rev-parse origin/claude/r4-reports-evaluation-u3vs4d
63a066e9275919df92bceaee58876f2724cf9df0

$ git status --porcelain
(rỗng — working tree SẠCH)

$ git merge-base --is-ancestor 824b5d7 63a066e9 && echo YES
YES

$ git log --oneline 824b5d7..63a066e9
63a066e R4: ghi kết quả branch_authority_check nguyên văn vào bàn giao S131
ea6413d R4: tài liệu — đặc tả KPI, task, bàn giao S131, quyết định DEC-201, ledger
86cee40 R4: báo cáo đánh giá tháng — KPI, target, đóng góp, chất lượng dữ liệu

$ git log -1 --format='%s%nparents=%P' 824b5d7
Merge pull request #9 from hoangvinhkta-creator/fix/r3-alembic-version-id
parents=dd369e5cbb26a599c7fb6e0da970f61a5b4f59e5 27c15d7f6f38a30dd740f4d7164d92eaa7f4fb5f
```

Nền `824b5d7` ĐÚNG là merge commit R3 (PR #9, repair revision Alembic), và nó
là tip hiện tại của nhánh mặc định `claude/extract-upload-repo-gq2ws4`. Đúng
BA commit R4 trên nền đó: một commit MÃ NGUỒN (`86cee40`) và hai commit
TÀI LIỆU.

Diff nền → HEAD: 16 file, `+4843 / −4`. Không migration
(`ALEMBIC_HEAD` vẫn `0009_line_binding_period_close`), không schema mới,
không route ghi mới.

**Lưu ý môi trường:** clone ban đầu của container này là SHALLOW (66 commit),
làm `tests/test_105d_boundaries.py::TestG25GoldenBaselineUnchanged` FAIL vì
object base `740f396…` không có mặt (`fatal: bad object`). Sau
`git fetch --unshallow origin` (345 commit) bài đó PASS. Đây là một tạo tác
của môi trường review, **không** phải một hồi quy của R4 — mọi con số full
regression dưới đây đo SAU khi unshallow.

---

## 3. Đã đọc

`R4 Execution Brief` (qua `docs/tasks/R4-bao-cao-danh-gia.md` §2 và
`PROJECT/PROJECT_DECISIONS.md` `DEC-201`), `docs/sessions/S131-…`,
`S126`, `S128`, `S129`, `S130`, `PROJECT/PROJECT_PROGRESS.md`,
`PROJECT/REVIEW_BUDGET_LEDGER.md`, `docs/spec/R4-DAC-TA-KPI.md`, và TOÀN BỘ
diff `824b5d7..63a066e9`.

---

## 4. Lệnh và kết quả test — nguyên văn

Môi trường: Python 3.11.15, venv riêng của phiên review, cài
`pip install -e ".[dev,web,history]"` (Flask 3.1.3, SQLAlchemy 2.0.52).

### 4.1 Test R4 tập trung

```text
$ python -m pytest -q tests/test_r4_evaluation_metrics.py tests/test_r4_evaluation_web.py
88 passed in 5.21s
```

### 4.2 Nhóm business metrics · reporting · target · period close · R2/R3 pricing · effective data

```text
$ python -m pytest -q tests/test_business_metrics.py tests/test_business_boundaries.py \
    tests/test_business_vertical.py tests/test_employee_workspace_ux.py \
    tests/test_r2_web_workflow.py tests/test_r3_web_workflow.py \
    tests/test_r3_export_and_period_close.py tests/test_web_server.py \
    tests/test_uiux_refinement.py
300 passed in 22.17s
```

### 4.3 Full regression trên HEAD R4

```text
$ python -m pytest -q
3146 passed, 12 skipped in 158.11s (0:02:38)
```

### 4.4 Full regression trên NỀN `824b5d7` (worktree riêng, cùng venv)

```text
$ git worktree add <tmp>/base824 824b5d7
$ cd <tmp>/base824 && python -m pytest -q
3058 passed, 12 skipped in 155.03s (0:02:35)
```

`3146 − 3058 = 88` — đúng bằng số bài R4 thêm. **0 bài hồi quy.** Con số
S131 §4 ghi được reviewer đo lại độc lập và khớp chính xác cả hai vế.

### 4.5 Validator/gate của repo (trên HEAD R4)

```text
$ python governance/scripts/governance/validate_structure.py
GOVERNANCE STRUCTURE: PASS
Deployment root: PASS — /home/user/Reports
Checked 21 required paths.

$ python governance/scripts/governance/validate_project_state.py
PROJECT STATE: PASS

$ python governance/scripts/governance/validate_evidence.py
EVIDENCE VALIDATION: PASS
Checked 161 REQUIRED PASS evidence record(s).

$ python governance/scripts/governance/validate_task_completion.py
TASK COMPLETION: PASS
Checked 14 DONE task(s).

$ python governance/scripts/governance/validate_reference_integrity.py
REFERENCE INTEGRITY: FAIL
Quét 270 file .md (loại trừ 10 file trong governance/reference/history/, docs/audit/).
3 reference không phân giải được:
- docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> /README.md
- docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> CODE_OF_CONDUCT.md
- docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> CONTRIBUTING.md
```

**Baseline đã xác nhận lại trên NỀN**, không tin bản chép của S131:

```text
$ cd <tmp>/base824 && python governance/scripts/governance/validate_reference_integrity.py
REFERENCE INTEGRITY: FAIL
Quét 267 file .md …
3 reference không phân giải được:
- docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> /README.md
- docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> CODE_OF_CONDUCT.md
- docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> CONTRIBUTING.md
```

ĐÚNG ba reference đó, cùng một file, thuộc `TASK-REM-T06`. R4 thêm 3 file
`.md` (267 → 270) và KHÔNG thêm một reference hỏng nào.

### 4.6 `branch_authority_check.sh`

```text
$ bash scripts/branch_authority_check.sh
=== BRANCH AUTHORITY CHECK (Governance V4.1 Machine Control #1) ===
fetch                : OK (origin --prune)
DEFAULT_REMOTE_REF   : refs/remotes/origin/claude/extract-upload-repo-gq2ws4
DEFAULT_BRANCH       : claude/extract-upload-repo-gq2ws4
DEFAULT_TIP          : 824b5d742dab07b8b0bd301d56748779e35076aa
HEAD_SHA             : 63a066e9275919df92bceaee58876f2724cf9df0
WORKTREE             : CLEAN
MODE                 : BRANCH
CURRENT_BRANCH       : claude/r4-independent-review-4fbga6

STOP — BRANCH AUTHORITY UNRESOLVED
Lý do: nhánh 'claude/r4-independent-review-4fbga6' không có upstream; vị trí
authority so với remote không xác định.
```

`STOP` này nói về NHÁNH REVIEW của phiên này, chưa từng được push lúc chạy
lệnh — không phải về nhánh R4 đang được review. Nhánh R4
(`claude/r4-reports-evaluation-u3vs4d`) có upstream và `RESULT: AUTHORITY_OK`
như S131 §7 đã ghi; reviewer xác nhận lại `HEAD_SHA` của nó bằng
`git rev-parse origin/…` ở §2 trên. Lệnh được chạy LẠI sau khi push nhánh
review — kết quả ở §10.

---

## 5. Bảy chuỗi — kiểm trực tiếp, có tự tính lại độc lập

Reviewer dựng 42 phép thử riêng (ngoài repo, không commit) chạy qua ỨNG DỤNG
FLASK THẬT trên dữ liệu tổng hợp do chính reviewer đặt, và tự tính lại con số
từ định nghĩa nghiệp vụ chứ không gọi module R4.

```text
$ python -m pytest -q <reviewer probes>/
42 passed in 5.77s
```

### A. PeriodData hiệu lực → 8 KPI → UI

Sổ dựng: 4 dòng · 3 đơn (`BH01` hai dòng, `BH02`, `BH03`), một dòng có chiết
khấu `100.000`, một dòng LỖ.

| Chỉ tiêu | Reviewer TỰ TÍNH (VND) | Trang hiện (nghìn) |
|---|---|---|
| Doanh thu | `8.000.000 + 1.700.000 + 12.000.000 + 2.000.000 = 23.700.000` | `23.700` |
| Số đơn | `COUNT DISTINCT = 3` | `3` |
| SL đủ ĐK KPI | 3 dòng có đơn giá > 1.000.000 | `3` |
| Doanh thu/đơn | `23.700.000 / 3 = 7.900.000` | `7.900` |
| LN KPI | `3.000.000 + 900.000 + 3.000.000 − 500.000 = 6.400.000` | `6.400` |
| Biên KPI | `6.400.000 / 23.700.000 × 100 = 27,00 %` | `27%` |
| Lãi/đơn | `6.400.000 / 3 = 2.133.333` | `2.133` |
| DS quy đổi | `150 + 45 + 60 − 25 (triệu) = 230.000.000` | `230.000` |

Tám ô khớp tuyệt đối. Thứ tự hiển thị đúng `HEADLINE_ORDER` đã freeze.

`None` KHÔNG thành `0`: kiểm cả hai chiều của bất biến ở
`evaluation.Kpi.__post_init__` — `(value is None) != (reason is not None)`
raise `ValueError`, nên "vừa có số vừa có lý do" và "không có cả hai" đều
không dựng được. Trên màn hình, mọi ô `—` đều mang `data-reason` + một câu
tiếng Việt.

### B. Coverage — con số một phần KHÔNG bao giờ ở vị trí kết quả

Thêm một dòng thiếu giá nhập ⟹ coverage `3 / 4 dòng` = `75 %`,
`quality-verdict = CHƯA ĐỦ`.

```text
eval-kpi_profit       = —   reason=PROFIT_NOT_OFFICIAL
eval-margin_percent   = —   reason=PROFIT_NOT_OFFICIAL
eval-profit_per_order = —   reason=PROFIT_NOT_OFFICIAL
eval-converted_sales  = —   reason=CONVERTED_NOT_OFFICIAL
eval-sales_revenue    = 22.000   (KHÔNG bị cổng chặn theo)
eval-orders           = 3        (KHÔNG bị cổng chặn theo)
```

Reviewer bóc riêng ô `kpi-value` của `eval-kpi_profit` bằng regex và xác nhận
nó chứa **đúng** `—`; con số một phần `6.000` chỉ xuất hiện ở
`kpi-partial` kèm nguyên văn "đây là phần đã biết, KHÔNG phải kết quả cả kỳ".
Khối dòng lỗ bật `loss-partial-scope` khi phạm vi chưa đủ.

### C. Target — sáu tình huống, mỗi tình huống một mã riêng

Kiểm qua `nhom=noi-thanh`, DS quy đổi chính thức `300.000.000`:

| Tình huống | Trang hiện | Reviewer tự tính |
|---|---|---|
| chưa đặt target | `—`, `TARGET_UNSET` | — |
| target = 0 | `—`, `TARGET_ZERO`, ô Target vẫn hiện `0` | — |
| actual chưa official | `—`, `TARGET_ACTUAL_NOT_OFFICIAL`, partial `300.000` | — |
| vượt target (100 tr) | `300%`, còn thiếu `0`, cần/ngày `0`, "Đã đạt/vượt" | `300.000.000/100.000.000` |
| còn thiếu (600 tr) | `50%`, thiếu `300.000`, còn `27` ngày, cần/ngày `11.111` | `300.000.000 / 27 = 11.111.111` |
| hết tháng (kỳ 08) | cần/ngày `—`, `TARGET_NO_DAYS_REMAINING`, còn `0` ngày, **% target vẫn có số** (`25%`) | — |

Không cap ở 100 %; "hết tháng" KHÔNG bị nói thành "đã đạt"; **không chia cho
0** ở bất kỳ nhánh nào.

**Không có target công ty — kiểm bằng cấu tạo và bằng màn hình.**
`BusinessReportService.sheet_target` chỉ đọc `group_targets` (sheet nhóm) hoặc
`employee_targets` (sheet nhân viên), không một phép cộng nào. Ở phạm vi
"Cả kỳ" trang KHÔNG render ô `target-value` nào, và hàng TỔNG của bảng đơn vị
báo cáo để TRỐNG cả hai cột target (`['100.000', '—', '—']` /
`['300%', '—', '—']`, phần tử cuối là hàng TỔNG).

### D. Thời gian

**`_today()` theo `Asia/Ho_Chi_Minh` — kiểm bằng đồng hồ giả:**

```text
UTC 2026-09-30T22:00Z  ->  _today() = 2026-10-01     (đúng: 05:00 giờ VN 01/10)
UTC 2026-09-30T11:00Z  ->  _today() = 2026-09-30     (đúng: 18:00 giờ VN 30/09)
```

Trước repair, mốc thứ nhất trả `2026-09-30` — đúng lỗi lệch một ngày mà S131
§6 mô tả. Chuỗi vùng dùng lại `daily_min.snapshot.SUPPORTED_BUSINESS_TIMEZONE`,
không phải `timedelta(hours=7)` viết cứng.

**Tháng đang chạy tính cả hôm nay:** hôm nay 03/09 ⟹ `elapsed 3 / 30`.
**Không chia cho 0:** kỳ đã kết thúc ⟹ `còn 0 ngày` + `TARGET_NO_DAYS_REMAINING`.

**Cửa sổ "cùng số ngày lịch" — ĐỐI XỨNG, kiểm cả trường hợp tháng trước ngắn hơn:**

```text
hôm nay 31/03/2026, so tháng 02/2026 (28 ngày)
  compare-window   = ngày 01–28 của cả hai tháng
  compare-current  = 5.000   (chỉ dòng 10/03; dòng 30/03 bị cắt)
  compare-previous = 4.000   (dòng 10/02)
  compare-percent  = +25%    (reviewer tự tính: (5−4)/4 = 25,00 %)
  trang NÓI RA: "Tháng trước ngắn hơn nên phép so cắt cả hai vế ở ngày 28
                 thay vì ngày 31…"

hôm nay 03/09/2026, so 08/2026 (cùng dài 31/30)
  compare-window = ngày 01–03 của cả hai tháng
  current 5.000 / previous 4.000   (dòng 20/09 và 25/08 đều bị cắt khỏi CẢ HAI vế)

kỳ 09 đã kết thúc (hôm nay 05/11)
  compare-window = trọn tháng;  current 14.000 / previous 13.900 (không cắt)
```

Vế thiếu được gọi ĐÚNG TÊN: kỳ trước rỗng ⟹ `COMPARE_PREVIOUS_NO_LINES`;
kỳ NÀY chưa có doanh thu trong cửa sổ ⟹ `COMPARE_CURRENT_NO_REVENUE` (không
đổ sang tháng kia). Không nhánh nào in `0 %`, `-100 %` hay vô cực.

**Dòng không có ngày bán:** reviewer `UPDATE … SET sale_date = NULL` trên một
dòng thật rồi mở lại trang. Dòng đó KHÔNG vào doanh thu kỳ (`5.000` thay vì
`8.000`) và được đếm riêng ở khối chất lượng dữ liệu (`quality-undated = 1`),
với nhãn nói rõ đó là con số của TOÀN BỘ DỮ LIỆU. Cấu tạo bảo đảm điều này:
`business_queries._period` luôn kèm `sale_date IS NOT NULL`, nên dòng không
ngày **không thể** lọt vào comparator của bất kỳ kỳ nào.

### E. Run-rate — tự tính lại

```text
doanh thu kỳ 20.000.000, hôm nay 03/09, tháng 30 ngày
reviewer tự tính: 20.000.000 / 3 × 30 = 200.000.000  ->  trang hiện 200.000 ✓

(qua HTTP thật, hôm nay 08/09) 23.700.000 / 8 × 30 = 88.875.000 -> 88.875 ✓
```

Nhãn "Ước tính nếu tốc độ hiện tại giữ nguyên" luôn có mặt và không tắt được;
câu "Đây KHÔNG phải dự báo và KHÔNG phải cam kết" in ngay dưới. Bốn cửa từ
chối đúng thứ tự — kỳ đã kết thúc ⟹ `RUNRATE_NOT_RUNNING` + `—`; nền chưa
chính thức ⟹ `RUNRATE_VALUE_NOT_OFFICIAL` (xác nhận qua HTTP thật ở ô DS quy
đổi). Run-rate KHÔNG được đem vào `% target`, `còn thiếu` hay `cần đạt/ngày`,
và trang không viết một câu nguyên nhân nào cạnh nó.

Một sai khác so với đặc tả §4 được ghi ở `AR-R4-04` (§7).

### F. Phân tích đóng góp

Sổ 5 dòng · 3 đơn · 4 mặt hàng:

```text
=== BẢNG THEO MẶT HÀNG ===
  TV43      đơn=2 dòng=2 DT=16.000 tỉ trọng=50,47% LN=6.000 biên=37,5%
  TU-LANH   đơn=1 dòng=1 DT=12.000 tỉ trọng=37,85% LN=3.000 biên=25%
  MAY-LOC   đơn=1 dòng=1 DT= 2.000 tỉ trọng= 6,31% LN= -500 biên=-25%
  LOA       đơn=1 dòng=1 DT= 1.700 tỉ trọng= 5,36% LN=  900 biên=52,94%
  TỔNG      đơn=3 dòng=5 DT=31.700 tỉ trọng=  100% LN=9.400 biên=29,65%
```

- **PHÂN HOẠCH:** `2+1+1+1 = 5` dòng = số dòng kỳ; doanh thu cộng dọc = TỔNG;
  tỉ trọng cộng lại `99,99 %` (sai số làm tròn hai chữ số).
- **Cột Đơn KHÔNG cộng dọc:** cộng cột ra `5`, hàng TỔNG là `3` — lấy từ tổng
  của PHẠM VI, không cộng cột. Trang in `ORDERS_NOT_ADDITIVE_NOTE` dưới MỌI
  bảng.
- **Biên âm hiện đúng như nó là** (`-25%`), không kẹp về 0.
- **Bảng đơn vị báo cáo dùng mẫu số CẢ KỲ và NÓI RA:** mở trang ở "Cả kỳ" và
  ở `nhom=noi-thanh` cho ra bảng đơn vị GIỐNG HỆT nhau, kèm câu
  "Bảng này LUÔN nói về CẢ KỲ…". Bốn bảng còn lại dùng mẫu số của phạm vi
  đang xem — đúng như đặc tả §6.
- **Chiết khấu CỘNG NGƯỢC, không trừ hai lần:** chiết khấu `100.000`, doanh
  thu NET đầu trang `31.700` KHÔNG đổi, tỉ lệ `0,31 %` = `100.000 / 31.800.000`
  (mẫu số là doanh thu TRƯỚC chiết khấu — reviewer tự tính `0,3145 %`).
  Một dòng `line_type = DISCOUNT` KHÔNG bị đếm vào `discount-lines`
  (vẫn `1`), và đơn ghi bằng cả hai cách bị NÊU TÊN: *"1 đơn vừa có cột chiết
  khấu vừa có dòng \"Chiết khấu\" riêng — nguy cơ trừ hai lần: BH01."*
- **Dòng lỗ:** `1` dòng, tổng `-500`, phạm vi `đã xét 5 / 5 dòng`. Dòng CHƯA
  tính được lợi nhuận KHÔNG bị gộp vào dòng lỗ; coverage chưa đủ ⟹ trang bật
  câu "…KHÔNG phải toàn bộ đơn lỗ của kỳ".
- **Xếp biên là một THỨ TỰ, không phải phán quyết:** với một mặt hàng thiếu
  giá, bảng "Biên KPI thấp nhất" chỉ xếp `['A', 'B']` (`12,5%`, `75%`) — hàng
  chưa đủ coverage của chính nó KHÔNG được xếp, và trong bảng "theo mặt hàng"
  nó hiện `—` kèm lý do "Lợi nhuận KPI chưa chính thức" chứ không phải ô trống.

Cả năm bảng đi qua CÙNG `data.details`/`data.lines` của một `PeriodData` — không
có nguồn số thứ hai.

### G. Drill-down và chốt kỳ

```text
=== DRILL-DOWN THEO MẶT HÀNG ===
  TV43     -> …&loc=tat-ca&mat-hang=8e66512d…   bảng kê 2 dòng | bảng nói 2
  TU-LANH  -> …&loc=tat-ca&mat-hang=3ccecacd…   bảng kê 1 dòng | bảng nói 1
  MAY-LOC  -> …&loc=tat-ca&mat-hang=3f9a8927…   bảng kê 1 dòng | bảng nói 1
  LOA      -> …&loc=tat-ca&mat-hang=b621f916…   bảng kê 1 dòng | bảng nói 1
  Σ = 5  ==  số dòng của kỳ = 5     -> KHỚP
KPI Doanh thu -> …&loc=tat-ca      -> 5 dòng    -> KHỚP
```

- **Giữ kỳ + phạm vi:** ở `nhom=noi-thanh`, MỌI đường drill-down đều mang
  `nhom=noi-thanh` (reviewer liệt kê toàn bộ `href` và xác nhận danh sách
  "đường dẫn KHÔNG mang `nhom=`" là RỖNG).
- **Bucket "chưa phân loại" giữ được khoá RỖNG:** hàng "Chưa phân nhóm" mở
  `…&nhom-hang=` (tham số rỗng CÓ MẶT trong URL) và trả về đúng 1 dòng — không
  im lặng mở về "tất cả". Tương tự `…&nguon=`.
- **Khoá không khớp ⟹ bảng RỖNG:** `mat-hang=khong-ton-tai` ⟹ `0` dòng.
- **Bảng kê NÓI RA phạm vi và cho đường "bỏ thu hẹp":** thu hẹp `1` dòng →
  bấm bỏ thu hẹp → `2` dòng, giữ nguyên kỳ.
- **Ô bị cổng coverage chặn dẫn tới VIỆC PHẢI LÀM** (`loc=thieu-gia`), và
  quay về `loc=tat-ca` ngay khi coverage đủ — đúng cấu tạo
  `gated_loc = "tat-ca" if official else "thieu-gia"`.
- **Kỳ đã chốt:** trang nói `Kỳ ĐÃ CHỐT (lần 1)`, `drift = no`. Sau khi Owner
  sửa một giá nhập, LN KPI trên trang đổi `4.000 → 5.000`, `drift = yes`, và
  trang bật **CẢNH BÁO** dẫn sang trang Chốt kỳ. **Bản chụp lúc chốt KHÔNG
  đổi** (`closed.totals["kpi_profit"] == "4000000"`) — số đã phát hành không
  âm thầm đổi.
- **Trang chỉ ĐỌC:** `POST /kinh-doanh/danh-gia → 405`, và HTML của trang
  trước/sau một lần POST giống nhau từng byte.

---

## 6. Khối chất lượng dữ liệu (§4 của brief review)

Sổ 3 dòng: một AUTO, một PENDING (thiếu giá), một dòng "Phí" (`line_type = FEE`).

```text
=== THẨM QUYỀN GIÁ NHẬP ===
  AUTO         Tự động (MIN theo ngày bán)      1 dòng
  POLICY_ZERO  Giá 0 theo chính sách loại dòng  1 dòng
  PENDING      Chưa có giá nhập                 1 dòng
  tổng các nhóm = 3 = số dòng của kỳ
=== NGUỒN GIÁ PIPELINE ĐÃ DÙNG ===
  TRACKING_PRICE_HISTORY  Lịch sử giá Tracking  3 dòng
=== HÀNG ĐỢI ===
  queue-missing-price = 1   (POLICY_ZERO KHÔNG bị tính là thiếu giá)
  queue-needs-review  = 0   queue-out-of-catalog = 0   queue-conflict = 0
  queue-binding       = 0
  coverage = 2 / 3 dòng (66,67 %)   verdict = CHƯA ĐỦ
  ngày bán mới nhất = 03/09/2026    dòng không ngày = 0
  chốt kỳ = Kỳ CHƯA chốt.
```

`POLICY_ZERO` đứng TÁCH khỏi `PENDING` — đúng điều R3 đã tách ra, và một giá 0
theo chính sách KHÔNG bị đếm vào hàng đợi "thiếu giá nhập". Kết luận
`ĐỦ`/`CHƯA ĐỦ` đọc thẳng `Coverage.is_complete` (phép SO BẰNG), không đọc phần
trăm đã làm tròn.

**`AR-R4-01` (FINAL/PROVISIONAL) — ACCEPTED_RISK được GIỮ NGUYÊN.** Điều kiện
mà brief review đặt ra đã thoả: giao diện nói rõ không có dữ liệu trạng thái
và KHÔNG suy đoán. Nguyên văn trên màn hình:

> Trạng thái FINAL/PROVISIONAL của giá MIN theo ngày KHÔNG được lưu lại trên
> từng dòng: hợp đồng daily-min-v1 mang day_status trong ảnh chụp lúc chạy, và
> ảnh chụp đó không được ghi vào dữ liệu hiệu lực. R4 chỉ ĐỌC dữ liệu hiệu lực
> nên nó KHÔNG dựng lại con số đó và cũng không đoán — thay vào đó là bảng
> THẨM QUYỀN GIÁ ngay dưới… Muốn có FINAL/PROVISIONAL theo dòng thì phải lưu
> thêm nó lúc nạp sổ; đó là một thay đổi ở đường nhập, ngoài phạm vi R4.

Reviewer xác nhận R4 **không mở rộng đường import**: hai trường mới
(`lead_source`, `price_source`) là hai cột ĐÃ CÓ trong `order_line_result`,
chỉ thôi bị vứt đi ở `line_details`; không cột PII nào; và không phép tính
nghiệp vụ nào đọc chúng (`grep` xác nhận `price_source` chỉ được
`price_source_breakdown` đọc, `lead_source` chỉ được `by_lead_source` và bộ lọc
`nguon` đọc). Không migration, `ALEMBIC_HEAD` không đổi.

---

## 7. Findings

### 7.1 REPAIR_REQUIRED — KHÔNG CÓ

Không tìm được finding nào thuộc sáu loại mà brief review bắt buộc repair:
lỗi luồng chính · số sai nhưng trông hợp lệ · coverage bị trình bày sai ·
target/cutoff sai · drill-down không khớp · mất trạng thái chốt/audit hoặc
ảnh hưởng nhầm dòng.

### 7.2 ACCEPTED_RISK mới

#### `AR-R4-04` — Run-rate nhân từ giá trị CẢ KỲ, không phải "giá trị đến `as_of`"

**Điều đặc tả nói.** `docs/spec/R4-DAC-TA-KPI.md` §4 và docstring của
`evaluation.run_rate` đều viết công thức là
`(giá trị đến as_of / ngày đã trôi qua) × ngày trong tháng`.

**Điều mã làm.** `server.py` truyền `totals.sales_revenue` /
`totals.official_converted_sales`, tức tổng CẢ KỲ. Với tháng đang chạy hai con
số này chỉ bằng nhau khi trong kỳ **không có dòng nào mang ngày bán SAU
`as_of`**.

**Tái hiện (reviewer):** hôm nay 03/09; một dòng 8.000.000 ngày 01/09 và một
dòng 30.000.000 ghi nhầm ngày **20/09**.

```text
run-rate trên trang  : 380.000   (= 38.000.000 / 3 × 30)
nếu dùng "đến as_of" :  80.000   (=  8.000.000 / 3 × 30)
```

**Xác suất × tác động × khả năng phát hiện.** Xác suất THẤP — cần một dòng
ghi ngày trong tương lai (gõ nhầm ngày, hoặc đơn đặt trước ghi ngày giao);
repo không có luật chặn ngày tương lai. Tác động HẠN CHẾ — con số này luôn
mang nhãn "ước tính", KHÔNG đi vào `% target`, `còn thiếu`, `cần đạt/ngày`
hay bất kỳ chỉ tiêu công bố nào, và không được ghi xuống đâu cả. Phát hiện
TRUNG BÌNH — chính trang đó hiện "Ngày bán mới nhất trong phạm vi" (sẽ là một
ngày TƯƠNG LAI) và `compare-current` cắt theo cửa sổ (sẽ lệch hẳn khỏi doanh
thu đầu trang).

**Vì sao ACCEPTED_RISK, không REPAIR.** Nó không thuộc sáu loại bắt buộc
repair: không nằm trên luồng chính của dữ liệu bình thường, không công bố một
kết quả kỳ, không làm sai coverage/target/cutoff, không lệch drill-down, không
chạm trạng thái chốt.

**Cách đóng (một dòng, cho phiên sau):** cắt đầu vào run-rate theo `as_of`
trước khi nhân — dùng lại chính `evaluation._lines_up_to_day(data.details,
as_of.day)` rồi `bm.totals(...)`; hoặc thêm một cửa từ chối thứ năm khi
`latest_sale_date > as_of`. Đây là công việc của một task riêng, không phải
của lượt review này.

#### `AR-R4-05` — "Ngoại lệ gắn dòng" trong khối chất lượng là con số TOÀN CỤC, đứng cạnh bốn con số ĐÃ THU HẸP

**Tái hiện (reviewer):** một ngoại lệ gắn dòng còn mở thuộc đơn `BH80` của kỳ
**2026-08**; mở trang đánh giá ở kỳ **2026-09** (kỳ này không có ngoại lệ nào
của chính nó):

```text
Ngoại lệ gắn dòng : 1     <- của kỳ KHÁC
Thiếu giá nhập    : 0     <- đã thu hẹp theo kỳ + sheet
Chưa phân loại mã : 0     <- đã thu hẹp
Ngoài bảng giá    : 0     <- đã thu hẹp
Xung đột mã       : 0     <- đã thu hẹp
```

`PeriodData.binding_exceptions` là `BindingExceptionStore.open_keys()` — TẤT CẢ
ngoại lệ còn mở của MỌI kỳ — và `_slice` chở nguyên vẹn nó sang lát sheet.
`len(...)` vì thế không phải con số của phạm vi đang xem, và nhãn trên trang
("… dòng") không nói ra điều đó.

**Đây là một BỀ MẶT MỚI của `AR-R3-05` đã được chấp nhận**, không phải một lỗi
mới về bản chất: `S129` §11.8 đã ghi đúng biểu thức `len(data.binding_
exceptions)` ở trang Chốt kỳ. R4 dùng lại cùng biểu thức ở một chỗ mới mà
KHÔNG ghi việc mở rộng bề mặt đó vào sổ rủi ro của mình (§9 của task chỉ kế
thừa `AR-R3-06`). Mục này lấp chỗ trống đó.

**Xác suất × tác động × phát hiện.** Xác suất TRUNG BÌNH khi đã có ngoại lệ
gắn dòng. Tác động NHỎ — một con số HÀNG ĐỢI, không phải một con số tiền:
nó không vào coverage, không vào một chỉ tiêu nào, không đổi một kết luận nào
về kết quả tháng. Phát hiện TRUNG BÌNH — dòng ngay trên nó ("Dòng KHÔNG có
ngày bán") đã có sẵn nhãn `(toàn bộ dữ liệu)`, nên sự vắng mặt của một nhãn
tương tự ở dòng này là chỗ dễ đọc nhầm nhất.

**Cách đóng (rẻ nhất, khuyến nghị làm trước trong lần sửa kế tiếp):** thêm
đúng một nhãn `(toàn bộ dữ liệu)` vào dòng đó, y như dòng "Dòng KHÔNG có ngày
bán" đang có. Đóng triệt để thì phải lọc `open_keys()` theo khoá dòng của lát
đang xem — việc của lineage R3 (`AR-R3-05`).

#### `AR-R4-06` — Khối "so kỳ trước" in `01–00` ở khung nhìn "Toàn bộ dữ liệu"

Khi không chọn kỳ nào, `SameDaysComparison.day_cutoff = 0` và template vẫn in
nhãn cửa sổ:

```text
tiêu đề : So với Toàn bộ dữ liệu | ngày 01–00 của cả hai tháng
thẻ     : "Kỳ này (01–00)"   "Toàn bộ dữ liệu (01–00)"
% và hai vế : —   (lý do ĐÚNG: COMPARE_NO_PERIOD)
```

Không con số nào sai — cả ba ô đều `—` và mã lý do đúng. Đây là CHỮ hiển thị
vô nghĩa. Tác động NHỎ, phát hiện DỄ (`01–00` đọc là vô lý ngay).
**Cách đóng:** ẩn nhãn cửa sổ và hai thẻ khi `reason == COMPARE_NO_PERIOD`.

#### `AR-R4-07` — Khoá `nhom` lạ rơi về "Cả kỳ" trong IM LẶNG, trái với docstring của chính route

`_evaluation_scope` có docstring: *"Khoá lạ ⟹ về cả kỳ VÀ nói ra, thay vì dựng
một trang toàn số 0 cho một sheet không tồn tại."* Reviewer mở
`?ky=2026-09&nhom=khong-ton-tai`:

```text
tiêu đề phạm vi              : Cả kỳ
có câu nào nói khoá lạ không : KHÔNG
```

Hành vi (rơi về cả kỳ) là AN TOÀN và đúng ý định; chỉ phần "nói ra" không tồn
tại. Tác động NHỎ — tiêu đề và ô chọn Phạm vi đều hiện "Cả kỳ", nên người đọc
thấy ngay mình đang xem gì; và một khoá lạ chỉ tới từ một đường dẫn cũ/gõ tay.
**Cách đóng:** hoặc thêm một câu, hoặc sửa docstring cho khớp hành vi. Sửa
docstring là đủ và rẻ hơn.

### 7.3 Ba `ACCEPTED_RISK` của S131 — reviewer GIỮ NGUYÊN

- `AR-R4-01` (MIN `FINAL`/`PROVISIONAL`) — điều kiện của brief review đã thoả,
  xem §6. Giữ `ACCEPTED_RISK`.
- `AR-R4-02` ("nguồn đơn" là phân loại suy ra) — trang chỉ ĐẾM và không viết
  một câu nguyên nhân nào; reviewer xác nhận bằng cách đọc toàn bộ câu chữ của
  bảng đó. Giữ.
- `AR-R4-03` (`_slice` chưa chiếu `excluded`) — đúng, và R4 không có bề mặt
  mới cho nó (không ô nào của trang đọc `excluded`). Giữ; thuộc lineage R3.

Ghi nhận thêm, theo hướng TỐT: `AR-R3-06` cảnh báo rằng lát sheet có thể nêu
một đơn "trừ chiết khấu hai lần" NGOÀI lát. R4 **không** thừa hưởng lỗi đó —
`evaluation.discounts` gọi `bm.discount_double_count_orders(list(lines))` trên
chính các dòng của phạm vi, chứ không dùng `data.discount_double_count` của cả
kỳ.

### 7.4 Điều reviewer KHÔNG mở rộng sang

Đúng giới hạn brief review đặt: không đánh giá forecasting ML, pricing, đường
import, target công ty, lương; và không yêu cầu sửa các giới hạn cũ
(`AR-R2-*`, `AR-R3-05`, `AR-R3-06`) — chúng thuộc lineage của chính chúng.

---

## 8. Bằng chứng SMOKE qua HTTP THẬT

Server WSGI thật (`werkzeug.serving.make_server`, KHÔNG phải Flask test
client) trên `127.0.0.1:8099`, SQLite trên đĩa, gọi vào bằng `curl` từ một
tiến trình KHÁC. `_today()` để NGUYÊN (không monkeypatch) — ngày máy chủ
`2026-09-08`, nên `2026-09` là tháng đang chạy thật.

Sổ: 4 dòng tháng 09 (một dòng thiếu giá, một dòng có chiết khấu) + 1 dòng
tháng 08; target nhóm `NOI_THANH = 200.000.000`.

### (A) Trang đánh giá, kỳ đang chạy

```text
$ curl -sS -w "HTTP %{http_code} %{size_download} bytes %{time_total}s\n" \
    "http://127.0.0.1:8099/kinh-doanh/danh-gia?ky=2026-09"
HTTP 200  35274 bytes  0.093408s

  as_of               = Số tính đến 08/09/2026
  ngày đã qua         = 8 / 30
  sales_revenue       = 23.700
  orders              = 3
  qualifying_quantity = 3
  revenue_per_order   = 7.900
  kpi_profit          = —      reason=PROFIT_NOT_OFFICIAL
  margin_percent      = —      reason=PROFIT_NOT_OFFICIAL
  profit_per_order    = —      reason=PROFIT_NOT_OFFICIAL
  converted_sales     = —      reason=CONVERTED_NOT_OFFICIAL
  coverage            = 3 / 4 dòng   75%      verdict = CHƯA ĐỦ
  revenue run-rate    = 88.875
  so kỳ trước         = +295%  | cửa sổ: ngày 01–08 của cả hai tháng
                        kỳ này 23.700 | kỳ trước 6.000
```

Reviewer tự tính: `23.700.000 / 8 × 30 = 88.875.000` ✓;
`(23,7 − 6) / 6 × 100 = 295,00 %` ✓.

### (B) Phạm vi có target

```text
$ curl -sS "…/kinh-doanh/danh-gia?ky=2026-09&nhom=noi-thanh"    HTTP 200

  target-value            = 200.000
  target-percent          = —    reason=TARGET_ACTUAL_NOT_OFFICIAL
  target-partial          = "Đã tính được 345.000 nghìn đồng DS quy đổi —
                             chưa được phép công bố làm kết quả kỳ."
  target-shortfall        = —
  target-required-per-day = —
  target-days-remaining   = còn 22 ngày            (30 − 8)
  target-run-rate         = —    reason=RUNRATE_VALUE_NOT_OFFICIAL
```

Reviewer tự tính DS quy đổi một phần: `3.000.000/0,02 + 900.000/0,02 +
3.000.000/0,02 = 345.000.000` ✓. Cổng coverage đóng đúng trên CẢ `% target`
lẫn run-rate DS quy đổi.

### (C) Drill-down — mọi đường dẫn trên trang, gọi thật

```text
HTTP 200  dòng=4  <- /kinh-doanh/gia-nhap?ky=2026-09&loc=tat-ca
HTTP 200  dòng=1  <- …&loc=thieu-gia
HTTP 200  dòng=4  <- …&loc=tat-ca&nhom=noi-thanh
HTTP 200  dòng=0  <- …&loc=tat-ca&nhom=gia-dung
HTTP 200  dòng=1  <- …&loc=tat-ca&mat-hang=3ccecacd…
HTTP 200  dòng=1  <- …&loc=tat-ca&mat-hang=8e66512d…
HTTP 200  dòng=1  <- …&loc=tat-ca&mat-hang=3f9a8927…
HTTP 200  dòng=1  <- …&loc=tat-ca&mat-hang=b621f916…
HTTP 200  dòng=4  <- …&loc=tat-ca&nhom-hang=DIEN_MAY
HTTP 200  dòng=4  <- …&loc=tat-ca&nguon=PERSONAL
HTTP 200  dòng=1  <- …&loc=co-chiet-khau
HTTP 200  dòng=0  <- …&loc=lo

Σ drill-down theo mặt hàng = 1+1+1+1 = 4 == số dòng của kỳ = 4   -> KHỚP
```

`12/12` đường dẫn trả `200`; không đường nào 404, 500 hay im lặng mở rộng
phạm vi.

---

## 9. Điều reviewer KHÔNG kiểm được — nói ra, không giấu

1. **Dữ liệu nghiệp vụ THẬT.** Cùng giới hạn S131 §8.2: phiên này chạy trên
   dữ liệu tổng hợp do reviewer đặt. Điều đó chứng minh CÔNG THỨC và LUỒNG,
   không chứng minh hình dạng dữ liệu thật (số mặt hàng, độ dài bảng, phân bố
   nguồn đơn) đọc được trên màn hình thật. Owner nên mở trang trên một kỳ
   thật trước khi đóng `CHECK-R4-24`.
2. **Production/Render và migration `0009`.** Không credential, egress bị
   chặn — cùng giới hạn `S127`/`S130`/`S131`. R4 không có migration nên không
   phụ thuộc điều đó; checklist `S130` §6–§7 vẫn là việc của Owner.
3. **Trình duyệt thật.** Kiểm ở mức HTML/HTTP, không chạy JavaScript và không
   kiểm hiển thị trên màn hình hẹp.

---

## 10. `branch_authority_check.sh` sau khi push nhánh review

Kết quả nguyên văn được ghi ở cuối file này trong commit tiếp theo của chính
phiên review (lệnh chỉ phân giải được sau khi nhánh có upstream).

---

## 11. Việc còn lại

```text
CHECK-R4-23 (Independent Review)  = PASS   (phiên này, trên exact HEAD 63a066e9)
CHECK-R4-24 (Owner nghiệm thu)    = NOT_TESTED
CHECK-R3-20 (Owner nghiệm thu R3) = NOT_TESTED — KHÔNG bị chạm tới
R4 STATUS                          = IMPLEMENTED (chưa DONE)
Ngân sách review R4                = 1 allowed / 0 used / 1 remaining
```

Phiên review KHÔNG merge, KHÔNG deploy, KHÔNG chuyển R4 sang `VERIFYING` hay
`DONE`, và KHÔNG tự đánh dấu Owner Acceptance của R3 hay của R4.
