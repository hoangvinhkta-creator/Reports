# S142 — R5.1: hoàn tất taxonomy Owner chốt, merge có kiểm soát

Ngày: 2026-09-09
Task Mode: MAJOR (bổ sung taxonomy sau review, KHÔNG phải repair cycle)
Quyết định: `DEC-206`
Kết quả phiên: **taxonomy triển khai, ĐÃ MERGE cả hai repo vào nhánh mặc
định.** KHÔNG deploy thủ công. KHÔNG làm `R6`. KHÔNG tự nghiệm thu production.

---

## 1. Preflight

### 1.1 Nhánh mặc định thật và HEAD lúc mở phiên

```text
Tracking  nhánh mặc định: main
          tip: 918183c48c4d4c45b5ce1348d734e073e537c6e4   (KHÔNG đổi từ S140/S141)
Reports   nhánh mặc định: claude/extract-upload-repo-gq2ws4  (KHÔNG phải "main")
          tip: 3b35b7acee2159b007c4398045f4b6f6843f7de8    (KHÔNG đổi từ S140/S141)
```

Cả hai working tree sạch (`git status --porcelain` rỗng) trước khi bắt đầu.

### 1.2 Lineage — xác nhận bằng git

```text
Tracking implementation repair  11a199b222ed1771558cefcdf664aad9de64cfa9
                                = HEAD của claude/r5-1-repair-1-taxonomy
$ git merge-base --is-ancestor origin/main 11a199b && echo YES   → YES
$ git log --oneline origin/main..11a199b
  11a199b R5.1 REPAIR-1 §4: category_label chọn từ từ điển đóng
  39528ee R5.1 §4: /api/xuat/board xuất thêm category_label đã chuẩn hoá

Reports review head  d89ecee6c428e0688edc32b512a96475c70b54ab
                     = HEAD của claude/r51-repair-1-review-2-jtimci
$ git merge-base --is-ancestor origin/claude/extract-upload-repo-gq2ws4 \
    d89ecee && echo YES                                          → YES
$ git log --oneline origin/claude/extract-upload-repo-gq2ws4..d89ecee
  d89ecee S141: Independent Review vòng 2 cho R5.1 REPAIR-1
  83b1e07 S140: SHA của HEAD gồm tài liệu, cho vòng review kế tiếp
  e993fb5 R5.1 REPAIR-1: hợp đồng từ điển đóng, DEC-205, ...
  dd7cd04 S139: Independent Review R5.1
  2c2c139 S138: SHA của HEAD gồm tài liệu, cho vòng review kế tiếp
  f982995 R5.1: hợp đồng, task/checklist, DEC-204, bàn giao S138
  0b8ac31 R5.1 §5: Reports đọc category_label từ hợp đồng catalog Tracking
```

`d89ecee` mang ĐỦ ba lớp lịch sử: implementation `R5.1` gốc, `REPAIR-1`, và
tài liệu Independent Review (cả hai vòng). Không phải chép tay — nhánh làm
việc của phiên này (`claude/r5-1-owner-taxonomy-merge`) tạo TRỰC TIẾP từ
`d89ecee` bằng `git checkout -b`.

### 1.3 Nhánh làm việc

```text
$ git -C Tracking checkout -b claude/r5-1-repair-1-taxonomy 11a199b (đã có sẵn từ S140)
$ git -C Reports  checkout -b claude/r5-1-owner-taxonomy-merge d89ecee
```

---

## 2. Ba quyết định Owner (`DEC-206`)

```text
Máy lạnh / Điều hòa / Điều hoà  →  "Điều hoà"
TV / Ti vi / Tivi               →  "Tivi"
Máy giặt sấy                    →  "Máy giặt" (KHÔNG mở nhóm riêng)
```

Hai alias đầu ĐÃ có trong từ điển từ `REPAIR-1` (`DEC-205` §4) — không cần
sửa mã, chỉ cần đóng `OWNER_DECISION_REQUIRED` mà Independent Review vòng 2
(`S141`) ghi lại (bằng chứng dữ liệu của `TV`/`Ti vi` YẾU/KHÔNG CÓ trong repo,
nên cần chỉ thị chính sách trực tiếp của Owner). Alias thứ ba là thay đổi mã
DUY NHẤT của phiên này: thêm `['Máy giặt sấy']` làm cách viết khác của
canonical `"Máy giặt"` trong `NHOM` (`Tracking/src/index.js`).

Lập luận đầy đủ, quan hệ với `DEC-204`/`DEC-205`, và closure của
`OWNER_DECISION_REQUIRED`/`AR-R5.1R1-05`: `PROJECT/PROJECT_DECISIONS.md` →
`DEC-206`.

---

## 3. File mã đã đổi

### Tracking (`11a199b` → `6d844fd`)

```text
src/index.js                        +31/-4   thêm 'Máy giặt sấy' vào NHOM;
                                             viết lại chú thích để dẫn ĐÚNG
                                             nguồn bằng chứng (COR-R5.1R1-02
                                             phần đính chính nhỏ)
kiem/nhom-hang.js                   +96      section 13 — 32 phép thử mới,
                                             kiểm TRỰC TIẾP nhomCua()/chieuBoard()
kiem/smoke/sinh-catalog-reports.mjs +10      thêm TV-01, MGS-01
```

Không đổi `HANG`, không đổi `HINH_NHOM`/`NHOM_TRA`/`HANG_TRA` (đã bỏ từ
REPAIR-1), không đổi `hangCua()`/`modelCua()`/`chieuBoard()`. **Không đổi một
dòng nào** của `price-engine/`, `src/min-ngay.js`.

### Reports (`d89ecee` → xem §5 cho merge SHA thật)

```text
app/web/catalog_display.py                     2 dòng   COR-R5.1R1-01
tools/tracking/capture_tracking_catalog.py      2 dòng   COR-R5.1R1-01
tests/test_r51_category_label.py               +19      1 bài mới (pass-through)
scripts/r51_crossrepo_smoke.py                 +18      DEC-206 assertions
PROJECT/PROJECT_DECISIONS.md                   +DEC-206, sửa bảng quan hệ DEC-205
PROJECT/PROJECT_PROGRESS.md                    canonical current state
PROJECT/REVIEW_BUDGET_LEDGER.md                mục DEC-206, không tiêu cycle
docs/tasks/R5-1-REPAIR-1-tu-dien-nhom-hang.md  đóng OWNER_DECISION_REQUIRED,
                                                AR-R5.1R1-05, COR-R5.1R1-01
docs/reviews/R5-1-REPAIR-1-INDEPENDENT-REVIEW-2-RECORD.md   annotate (nguyên
                                                văn giữ nguyên)
docs/sessions/S142-r51-owner-taxonomy-merge.md  file này
```

**Đúng hai file mã sản phẩm bị chạm** — cả hai CHỈ đổi chú thích, đúng phạm vi
brief chỉ định. `git diff --stat d89ecee..HEAD -- app/ tools/ config/` xác
nhận không dòng hành vi nào đổi ngoài hai chú thích.

---

## 4. Kiểm chứng trước merge (E1 — output nguyên văn)

### 4.1 Tracking — `npm test` + `npm run build`

```text
$ npm test
  ✓ nhom-hang.js            114 đạt
────────────────────────────────────────────────────
  62 bộ · 2882 đạt · 0 hỏng · 2 bỏ qua
  Tất cả đạt.

$ npm run build
  62 bộ · 2882 đạt · 0 hỏng · 2 bỏ qua
Đã dựng bản phục vụ vào ./dist — 7 file, 658 KB → 411 KB (bớt 37%)
```

Nền `REPAIR-1` là `2850 đạt`; phiên này thêm 32 phép thử ròng (section 13).

### 4.2 Bảng ví dụ DEC-206, chạy qua chính `nhomCua()`

```text
"Máy lạnh"              -> "Điều hoà"
"Điều hòa"              -> "Điều hoà"
"Điều hoà"              -> "Điều hoà"
"TV"                    -> "Tivi"
"Ti vi"                 -> "Tivi"
"Máy giặt sấy"          -> "Máy giặt"
"Máy giặt sấy LG"       -> "Máy giặt"   (brand riêng: "LG")
"Máy giặt sấy kho anh Ba" -> null
"Máy giặt sấy 4K"       -> null
"Tivi kho anh Ba"       -> null   (vẫn null — REPAIR-1 không bị nới lỏng)
"Tủ lạnh nợ NCC"        -> null
"Tivi Đất Việt"         -> null
"Tivi hàng gửi"         -> null
"Tivi 4K"               -> null
"Tivi TV"               -> null   (AR-R5.1R1-04, GIỮ NGUYÊN — không sửa)
"Máy lạnh Điều hoà"     -> null   (AR-R5.1R1-04, GIỮ NGUYÊN)
```

### 4.3 Reports — test R5.1 tập trung

```text
$ .venv/bin/python -m pytest tests/test_r51_category_label.py -q
...........................                                              [100%]
27 passed in 3.69s
```

### 4.4 Reports — full `pytest`

```text
$ .venv/bin/python -m pytest tests/ -q
3260 passed, 11 skipped in 189.86s (0:03:09)
```

Nền `S141` là `3260 passed` trên container CÓ đủ lịch sử git (bài
`TestG25GoldenBaselineUnchanged` PASS ở đây — container review vòng 2 dùng
clone nông, đã ghi rõ đó là baseline môi trường, không phải hồi quy). Phiên
này thêm 1 bài mới, không bài nào của `R1`–`R5.1 REPAIR-1` đổi trạng thái.

### 4.5 Smoke xuyên hai repo — producer THẬT → capture THẬT → route Flask THẬT

```text
$ .venv/bin/python scripts/r51_crossrepo_smoke.py

1) Tracking sinh board/alias bằng chính chieuBoard() thật     [tất cả PASS]
2) Reports capture (mã thật) đọc payload do Tracking sinh
  ok   DEC-206: "TV" ⟹ category_label "Tivi"
  ok   DEC-206: "Máy giặt sấy LG" ⟹ category "Máy giặt", brand "LG"
  ok   DEC-206: TV-01 ⟹ Tivi qua tới snapshot
  ok   DEC-206: MGS-01 ⟹ category Máy giặt + brand LG qua tới snapshot
3) Artifact R5 cũ vẫn đọc được                                 [tất cả PASS]
4) Route web thật: capture → bản chiếu → bảng kê nhân viên
  ok   DEC-206: TV-01/MGS-01 hiện đúng nhãn trong bản chiếu
  ok   tổng tiền KHÔNG đổi sau khi nhóm hàng xuất hiện
  ok   ...và KHÔNG đổi một đồng nào
  ok   sau create_app() mới vẫn đọc đúng

KẾT QUẢ SMOKE: 63 PASS, 0 FAIL
```

### 4.6 Bất biến tiền — MIN/giá nhập/lợi nhuận/coverage/fingerprint/period lock

```text
Tracking   git diff --stat 11a199b..6d844fd -- price-engine/ src/min-ngay.js
           → RỖNG (không đổi công thức MIN)
Reports    git diff --stat d89ecee..HEAD -- app/ tools/ config/
           → CHỈ 2 dòng chú thích (COR-R5.1R1-01), 0 dòng logic
```

`tests/test_r51_category_label.py::test_changing_the_category_moves_no_money`
(có từ REPAIR-1, chạy lại ở §4.3–4.4) đo trực tiếp: đổi `category_label` rồi
so `doanh thu`/`giá nhập`/`lợi nhuận`/`DS quy đổi` — y hệt tới từng ký tự.
Không test/migration nào chạm `fingerprint` hay `period lock` — hai file mã
sản phẩm bị đổi (`catalog_display.py`, `capture_tracking_catalog.py`) không
nằm trên đường đọc/ghi của một trong hai cơ chế đó.

### 4.7 Governance validators

```text
GOVERNANCE STRUCTURE: PASS
PROJECT STATE:        PASS
EVIDENCE VALIDATION:  PASS
TASK COMPLETION:      PASS
REFERENCE INTEGRITY:  FAIL — ĐÚNG 4 finding BASELINE (đã có từ S139/S140/S141,
                      không file nào của phiên này góp thêm):
  docs/sessions/S136-r5-integration.md -> /tmp/.../r5_repair_crossrepo_smoke.py
  docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> /README.md
  docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> CODE_OF_CONDUCT.md
  docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> CONTRIBUTING.md
```

### 4.8 `git diff --check`

```text
$ git -C Tracking diff --check 11a199b..6d844fd   → rỗng (sạch)
$ git -C Reports  diff --check d89ecee..HEAD      → rỗng (sạch)
```

### 4.9 Reports không giữ taxonomy riêng

```text
$ .venv/bin/python -m pytest \
    tests/test_r51_category_label.py::test_reports_keeps_no_category_vocabulary_of_its_own -q
1 passed
```

Bài này quét mã (không phải docstring/comment) của sáu module đọc/tiêu thụ
`category_label` bên Reports và khẳng định không tên nhóm hàng nào của
Tracking xuất hiện như DỮ LIỆU trong mã Reports — canh cấu trúc, không canh
một trường hợp cụ thể.

---

## 5. Merge có kiểm soát

**Điền sau khi PR merge — xem `git log` của nhánh mặc định để xác minh độc
lập nếu bản ghi dưới đây thiếu.**

### 5.1 Tracking

```text
PR                #___  hoangvinhkta-creator/Tracking
head → base       claude/r5-1-repair-1-taxonomy → main
diff kiểm tra     src/index.js, kiem/nhom-hang.js, kiem/smoke/sinh-catalog-reports.mjs
merge commit SHA  ________________________________________
main HEAD sau merge  ________________________________________
```

### 5.2 Reports

```text
PR                #___  hoangvinhkta-creator/Reports
head → base       claude/r5-1-owner-taxonomy-merge → claude/extract-upload-repo-gq2ws4
diff kiểm tra     2 file mã (chú thích), 2 file test, 7 file tài liệu
merge commit SHA  ________________________________________
default HEAD sau merge  ________________________________________
```

### 5.3 Xác nhận sau merge (cả hai repo)

```text
$ git fetch origin <nhánh mặc định>
$ git merge-base --is-ancestor <SHA trước merge> <SHA sau merge> && echo YES
$ git status --porcelain          → rỗng
$ bash scripts/branch_authority_check.sh   → AUTHORITY_OK
```

Điền kết quả thật ở đây sau khi thực hiện.

---

## 6. Deploy

**KHÔNG deploy thủ công trong phiên này.** Nếu Reports có Render auto-deploy
gắn với nhánh mặc định, merge PR #___ có thể đã kích hoạt một lần deploy tự
động — phiên này CHỈ GHI NHẬN khả năng đó (nếu quan sát được từ bằng chứng
gián tiếp), KHÔNG xác nhận production đã chạy đúng, và KHÔNG tuyên bố
`CHECK-R51-26` đạt. Owner là người duy nhất nghiệm thu production.

---

## 7. `CHECK-R51-26` — XÁC NHẬN GIỮ `NOT_TESTED`

```text
CHECK-R51-26 (Owner nghiệm thu trên production)   NOT_TESTED
```

Phiên này — kể cả sau khi merge — KHÔNG tự đóng check này. Không phiên nào
được phép tự đóng nó; đây là hành động dành riêng cho Owner.

---

## 8. Checklist nghiệm thu production cho LẦN CAPTURE MỚI ĐẦU TIÊN sau deploy

Cột "Nhóm hàng" hiện `"—"` cho tới lần capture danh mục MỚI đầu tiên sau khi
Tracking production chạy code đã merge (`AR-R5.1-04`, giữ nguyên từ `R5.1`).
Đây là trạng thái ĐÚNG, không phải lỗi. Khi lần capture đó xảy ra:

```text
[ ] Board production của Tracking trả category_label cho các mã ĐÃ xếp cat
    (không còn "—" cho những mã đó)
[ ] Ba alias DEC-206 xuất hiện ĐÚNG trên dữ liệu THẬT nếu có mã tương ứng:
      cat chứa "Máy lạnh"/"Điều hòa"/"Điều hoà"  → cột hiện "Điều hoà"
      cat chứa "TV"/"Ti vi"/"Tivi"               → cột hiện "Tivi"
      cat chứa "Máy giặt sấy"                    → cột hiện "Máy giặt"
[ ] Không mã nào trước đây hiện "—" nay hiện một nhãn SAI (đối chiếu vài mã
    mẫu với bảng chọn ngành hàng thật trong Tracking)
[ ] Tổng doanh thu/giá nhập/lợi nhuận của kỳ đang xem KHÔNG đổi so với trước
    lần capture này (so hai lần tải trang, trước/sau capture)
[ ] Cột "Nhóm hàng" vẫn nằm sau nút ẩn/hiện — không tự động mở, không rò ra
    trang chỉ tiêu/export nào khác
[ ] Owner xác nhận bằng lời/văn bản rằng cột đã đúng trên dữ liệu thật →
    lúc đó, và CHỈ lúc đó, CHECK-R51-26 mới được đóng (bởi Owner, ghi vào
    PROJECT/PROJECT_DECISIONS.md hoặc PROJECT_PROGRESS.md, không phải bởi
    một phiên Claude tự động)
```

---

## 9. Trạng thái cuối

```text
DEC-206                    Ban hành, taxonomy triển khai đủ ba alias
OWNER_DECISION_REQUIRED    ĐÃ ĐÓNG
AR-R5.1R1-05                ĐÃ ĐÓNG
AR-R5.1R1-04                GIỮ NGUYÊN (không đổi, không yêu cầu sửa)
COR-R5.1R1-01                ĐÃ SỬA
COR-R5.1R1-02                ĐÃ SỬA (bảng quan hệ DEC-205)
CHECK-R51R1-17               PASS (giữ nguyên từ S141)
CHECK-R51-26                 NOT_TESTED (xem mục 7)
Repair cycle tiêu bởi S142   0 — lineage R5 giữ 2 allowed / 2 used / 0 remaining
Merge                        Tracking → main; Reports → claude/extract-upload-repo-gq2ws4
Deploy thủ công               KHÔNG thực hiện
R6                           KHÔNG thực hiện
```
