# S138 — R5.1: nhóm hàng (`category_label`) trong hợp đồng metadata sản phẩm

Ngày: 2026-09-09
Task Mode: MAJOR
Task: `docs/tasks/R5-1-nhom-hang-category-label.md`
Kết quả phiên: **IMPLEMENTED** — KHÔNG merge, KHÔNG deploy.

---

## 1. Điều kiện mở phiên

### 1.1 Nhánh mặc định thật và exact HEAD đầu phiên

```text
Reports   nhánh mặc định (git remote show origin → HEAD branch):
          claude/extract-upload-repo-gq2ws4        ← KHÔNG phải "main"
          HEAD đầu phiên  3b35b7acee2159b007c4398045f4b6f6843f7de8
          nhánh làm việc  claude/r5-1-category-label-1nnct7

Tracking  nhánh mặc định: main
          HEAD đầu phiên  918183c48c4d4c45b5ce1348d734e073e537c6e4
          nhánh làm việc  claude/r5-1-category-label-1nnct7
```

### 1.2 Kiểm tra ancestry

Nhánh làm việc của Reports lúc mở phiên đang ở `4278c3b` (HEAD của `S135`
REPAIR-1) — **lỗi thời**, và nó KHÔNG mang commit nào chưa có trên nhánh mặc
định:

```text
$ git merge-base --is-ancestor origin/claude/extract-upload-repo-gq2ws4 HEAD
NO                       ← HEAD cũ chưa chứa nhánh mặc định
$ git log --oneline origin/claude/extract-upload-repo-gq2ws4..HEAD
(rỗng)                   ← không có commit nào của riêng nhánh
$ git merge-base --is-ancestor HEAD origin/claude/extract-upload-repo-gq2ws4
YES                      ← toàn bộ nhánh đã nằm trong nhánh mặc định
```

Vì nhánh không mang công việc chưa merge, nó được dựng lại từ nhánh mặc định
(`git checkout -B ... origin/claude/extract-upload-repo-gq2ws4`) thay vì
rebase — không có gì để giữ lại. Tracking đã đúng `origin/main`, 0 ahead /
0 behind.

```text
$ bash scripts/branch_authority_check.sh
DEFAULT_BRANCH  claude/extract-upload-repo-gq2ws4
DEFAULT_TIP     3b35b7acee2159b007c4398045f4b6f6843f7de8
HEAD_SHA        3b35b7acee2159b007c4398045f4b6f6843f7de8
WORKTREE        CLEAN
AUTHORITY       BRANCH_WITH_UPSTREAM
RESULT          AUTHORITY_OK
```

Working tree của CẢ HAI repo: sạch (`git status --porcelain` rỗng).

### 1.3 R5 đã merge đủ — xác nhận bằng mã, không bằng lời

```text
Tracking  918183c "R5 §5: xuất model_label/brand chuẩn hoá qua /api/xuat/board"
          đã nằm trên `main`. `chieuBoard()` trong src/index.js xuất đúng bốn
          trường name/alt/model_label/brand.

Reports   f5e4e76 "R5: đối soát sổ, biểu đồ so sánh, thao tác đơn và danh tính
          sản phẩm (Owner override DEC-203)" đã nằm trên nhánh mặc định.
          `TrackingCatalogRow` có model_label/brand; loader và capture tool đọc
          cả hai; `catalog_display` + `_catalog_labels()` chở chúng ra màn hình.
```

Không có bước chép tay mã R5 nào. R5.1 mở rộng đúng các module ấy tại chỗ.

### 1.4 Tài liệu đã đọc

`docs/tasks/R5-doi-soat-so-bieu-do-thao-tac-danh-tinh.md` (brief + Scope
Lock + checklist), `docs/sessions/S134`/`S135`/`S135-repair-1`/`S136`/`S137`,
`docs/reviews/R5-INDEPENDENT-REVIEW-RECORD.md`,
`docs/adr/ADR-111-absence-effective-data-imei-scope-and-brand-authority.md`,
`docs/spec/TASK-105D-DATA-CONTRACT.md` §4,
`PROJECT/PROJECT_PROGRESS.md`, `PROJECT/REVIEW_BUDGET_LEDGER.md`.

---

## 2. Quyết định thiết kế đáng ghi

### 2.1 Nguồn là `cat`, và CHỈ `cat`

`board/<mã>/cat` là trường ngành hàng có cấu trúc mà người của Tracking tự
tay xếp qua `pickCat()` — đúng trường mà `ADR-111` §3 đã lấy làm căn cứ đặt
thẩm quyền thương hiệu ở Tracking. Nhóm hàng đến từ cùng trường ấy nên thừa
hưởng nguyên vẹn quyết định đó; **R5.1 không mở một ADR mới**.

`name` KHÔNG được đọc. Rút nhóm hàng từ câu tên hàng là đúng phép dò chuỗi tự
do mà `D-04` (`DEC-147` §4) ghi rằng Tracking đã thử bằng máy và **bỏ hẳn** vì
sai trên tài sản thật. Hệ quả chấp nhận được ghi ở `ACCEPTED_RISK R5.1-01`.

### 2.2 Danh sách trắng theo HÌNH DẠNG — khác biệt lớn nhất so với `brand`

Đây là quyết định trọng tâm của R5.1.

```text
brand           ra từ HANG — một danh sách ĐÓNG. Thứ qua ranh giới luôn là
                một trong ~38 từ đã biết.
category_label  ra từ `cat` — chuỗi NGƯỜI DÙNG GÕ TAY qua "+ Ngành hàng mới".
```

Không có gì ngăn một `cat` mang tên NCC, giá, tồn, ghi chú hay link. Chiếu nó
ra ngoài sau khi chỉ cắt tên hãng là **tin rằng chuỗi ấy luôn sạch**.
`HINH_NHOM` (1–4 từ, chỉ chữ cái và dấu, ≤ 40 ký tự) thay niềm tin đó bằng
một phép kiểm. `kiem/nhom-hang.js` §4 chạy bảy chuỗi bẩn mà một người thật có
thể gõ, kèm một **đối chứng** chứng minh chúng không `null` vì lý do khác.

### 2.3 Bảng ánh xạ nhỏ nhất có thể

Hai sentinel `"Chưa phân loại"` và `"Không sử dụng"` (`CAT_JUNK`) ra `null`:
chúng là **trạng thái quy trình**, không phải tên loại hàng hoá. Cả hai đã là
thẩm quyền Tracking từ trước (`public/index.html`), nên đây là "cấu hình có
sẵn" theo đúng nghĩa `§3.6` của brief, không phải một taxonomy mới. Gộp tên
đồng nghĩa khác: KHÔNG làm (`ACCEPTED_RISK R5.1-03`).

### 2.4 `§5.4` thi hành ở hai cổng ĐÃ CÓ, không phải hai cổng mới

```text
_catalog_labels()  → identity_gateway.confirmed_identities()
                     chỉ mapping CONFIRMED mới có khoá trong bảng
_catalog_field()   → chỉ dòng classification == MATCHED_TRACKING mới được tra
```

Conflict, stale target, OUT_OF_CATALOG và chưa phân loại vì thế **không có
đường** nhận nhóm hàng của một candidate — cùng phép chặn đã giữ `brand`, chứ
không phải một phép chặn thứ hai viết riêng. `CHECK-R51-14` đo cả hai trường
cùng lúc để một lần nới ở đây làm đỏ ngay.

### 2.5 Một cột đọc-thuần, dưới ĐÚNG nút ẩn/hiện đã có

"Nhóm hàng" đứng cạnh "Hãng", chung nút với "IMEI". Không nút thứ hai, không
KPI, không bảng gộp theo nhóm, không đường sửa nhóm hàng trong Reports —
`§5.7`/`§9` của brief. Trống hiện dấu gạch.

---

## 3. File mã đã đổi

### Tracking (`918183c` → `39528ee`)

```text
src/index.js                          +82  NHOM_SENTINEL, HINH_NHOM, nhomCua();
                                           trường thứ năm trong chieuBoard()
kiem/nhom-hang.js                    +230  MỚI — 57 phép thử
kiem/smoke/sinh-catalog-reports.mjs  +111  MỚI — producer fixture xuyên repo
kiem/hang-va-model.js                 +13  hình dạng bốn khoá → năm khoá
kiem/xuat-baocao.js                   +11  hình dạng bốn khoá → năm khoá,
                                           thêm phép thử cat đã tách hãng
```

### Reports (`3b35b7a` → `0b8ac31`)

```text
app/modules/product/identity/tracking_catalog.py  +12  trường category_label
app/modules/pricing/resolution/sources.py         +14  loader đọc trường thứ ba
tools/tracking/capture_tracking_catalog.py        +32  capture ghi trường thứ ba
app/web/catalog_display.py                        +73  FIELDS, category_of(),
                                                       rows_of/read theo FIELDS
app/web/server.py                                 +26  _catalog_labels() theo FIELDS
app/web/workspace_presentation.py                 +44  cột + category_label trên dòng
app/web/templates/kinh_doanh_nhan_vien.html       +39  ô "Nhóm hàng"
tests/test_r51_category_label.py                 +533  MỚI — 24 bài
scripts/r51_crossrepo_smoke.py                   +325  MỚI — smoke xuyên hai repo
tests/test_r5_workspace_identity_ux.py            +19  hợp đồng mở rộng: hai bài R5
                                                       cập nhật theo (bản chiếu ba
                                                       trường, nhãn nút mới)
```

Không migration. Không schema database. Không bảng mới. Không product key mới.

---

## 4. Bằng chứng (E1 — output nguyên văn)

### 4.1 Tracking — `npm test`

```text
$ npm test
  ✓ nhom-hang.js             57 đạt
  ✓ hang-va-model.js         29 đạt
  ✓ xuat-baocao.js          175 đạt
  ...
────────────────────────────────────────────────────
  62 bộ · 2825 đạt · 0 hỏng · 2 bỏ qua
  Tất cả đạt.
```

Nền R5 là `2767 đạt`; R5.1 thêm 58 phép thử, không bài nào đỏ.

### 4.2 Tracking — `npm run build`

```text
$ npm run build
  62 bộ · 2825 đạt · 0 hỏng · 2 bỏ qua
  Tất cả đạt.
Đã dựng bản phục vụ vào ./dist
  7 file, xén chú thích 1 file HTML
  658 KB → 411 KB  (bớt 37%)
```

### 4.3 Reports — bộ kiểm R5.1

```text
$ .venv/bin/python -m pytest tests/test_r51_category_label.py -q
........................                                                 [100%]
24 passed in 2.34s
```

### 4.4 Reports — focused identity/catalog/R2–R5 + Golden

```text
$ .venv/bin/python -m pytest tests/test_r51_category_label.py \
    tests/test_r5_product_identity_fields.py tests/test_r5_workspace_identity_ux.py \
    tests/test_r5_repair_1.py tests/test_tracking_catalog_capture.py \
    tests/test_tracking_authoritative_identity.py tests/test_105d_resolution.py \
    tests/test_105d_identity_keys.py tests/test_dec185_nav_chart_identity.py \
    tests/test_employee_workspace_ux.py tests/test_golden_baseline.py -q
354 passed, 2 skipped in 27.54s
```

### 4.5 Reports — full `pytest`

```text
$ .venv/bin/python -m pytest tests/ -q
3257 passed, 11 skipped in 169.95s (0:02:49)
```

Nền trước phiên (cùng máy, cùng venv): `3233 passed, 11 skipped`. Chênh lệch
đúng bằng 24 bài mới của `tests/test_r51_category_label.py` — không bài nào
của R1–R5 đổi trạng thái.

### 4.6 Smoke xuyên hai repo

```text
$ .venv/bin/python scripts/r51_crossrepo_smoke.py

1) Tracking sinh board/alias bằng chính `chieuBoard()` thật
    55Q6FA  model="QLED 55Q6FA"  brand="Samsung"  category="Tivi"
    RT38    model="RT38"         brand="Samsung"  category="Tủ lạnh"
    LA-01   model=null           brand=null       category=null
    XUNG-01 model=null           brand=null       category=null
    alias.map: {"CU-01":"55Q6FA"}
  ok   bốn trường hợp §7 đều có mặt
  ok   Tivi Samsung ⟹ category_label Tivi
  ok   Tủ lạnh Samsung ⟹ category_label Tủ lạnh
  ok   mã chưa xếp ngành hàng ⟹ null
  ok   mã cat hai hãng ⟹ null
  ok   alias.map mang stale target, Tracking KHÔNG gộp sẵn (INV-16)
  ok   không lộ khoá ngành hàng / cat ghép hãng / tên NCC / giá vốn /
       giá chốt / số Engine / tồn kho / giá bán buôn / link nội bộ

2) Reports capture (mã thật) đọc payload do Tracking sinh
  ok   capture COMPLETE
  ok   55Q6FA / RT38: model + hãng + nhóm hàng đúng
  ok   LA-01 / XUNG-01: cả ba đều None
  ok   alias_map qua được nguyên vẹn
  ok   ghép EXACT không đọc nhóm hàng
  ok   envelope không lộ ngành hàng thô / giá vốn / giá chốt / tồn kho / link

3) Artifact R5 cũ (không có category_label) vẫn đọc được
  ok   artifact cũ vẫn load được
  ok   content_hash ĐỔI khi nhóm hàng đổi
  ok   dòng không có nhóm hàng băm y hệt ở cả hai đời hợp đồng
  ok   artifact cũ: model/hãng giữ nguyên
  ok   artifact cũ: nhóm hàng là None, không phải lỗi

4) Route web thật: capture → bản chiếu → bảng kê nhân viên
  ok   bản chiếu chỉ giữ dòng CÓ điều để nói
  ok   trước khi phân loại: KHÔNG dòng nào có nhóm hàng
  ok   phân loại BH1 → 55Q6FA / BH2 → RT38 / BH3 → LA-01
  ok   BH1/BH2 hiện đúng nhóm hàng; BH3 và BH4 để trống
  ok   hãng đi kèm đúng dòng
  ok   model canonical đi kèm đúng dòng
  ok   dòng conflict giữ TÊN THÔ
  ok   tổng tiền KHÔNG đổi sau khi nhóm hàng xuất hiện
  ok   đổi nhóm hàng bên Tracking hiện ra ngay ở lần đọc sau
  ok   ...và KHÔNG đổi một đồng nào
  ok   sau create_app() mới vẫn đọc đúng

KẾT QUẢ SMOKE: 45 PASS, 0 FAIL
```

**Fixture KHÔNG gõ tay.** Payload đi vào Reports do `kiem/smoke/
sinh-catalog-reports.mjs` sinh ra bằng chính `chieuBoard()`/`hangCua()`/
`modelCua()`/`nhomCua()` trích từ `src/index.js`, rồi đi qua chính
`capture.build_capture()` và `load_tracking_catalog_capture()` của Reports.

**Một lần đỏ đáng ghi.** Bản thảo đầu dựng "artifact R5 cũ" bằng cách XOÁ
khoá `category_label` khỏi envelope mới. Loader từ chối với
`content_hash không khớp rows/alias_map` — và nó **đúng**: đó là một file bị
sửa sau khi ghi (`INV-11`), không phải một artifact R5 hợp lệ. Sửa bằng cách
chụp lại từ một `board` không có trường mới, tức mô phỏng đúng một Tracking
đời R5. Đây là lỗi ở SCRIPT SMOKE, không phải hồi quy sản phẩm — và nó có
giá trị: nó chứng minh `content_hash` thật sự phủ `category_label` (`§4.7`).

---

## 5. Ví dụ payload

`GET /api/xuat/board` — xem `docs/spec/TASK-105D-DATA-CONTRACT.md` §4.6 cho
bản đầy đủ kèm giải thích.

```json
{
  "55Q6FA": { "name": "Tivi Samsung QLED 55Q6FA", "alt": ["QN55Q6FA", "55Q6"],
              "model_label": "QLED 55Q6FA", "brand": "Samsung",
              "category_label": "Tivi" },
  "RT38":   { "name": "Tủ lạnh Samsung RT38", "alt": [],
              "model_label": "RT38", "brand": "Samsung",
              "category_label": "Tủ lạnh" },
  "LA-01":  { "name": "Tivi cũ trưng bày", "alt": [],
              "model_label": null, "brand": null, "category_label": null }
}
```

---

## 6. Backward compatibility

```text
Trường mới là TÙY CHỌN            client cũ bỏ qua vẫn chạy đúng như trước
Không đổi nghĩa trường cũ          name/alt/model_label/brand giữ nguyên
Không đổi tracking_code            khoá node không đụng tới
Không đổi công thức MIN            R5.1 không chạm một dòng nào của min-ngay.js
Artifact R5 cũ vẫn đọc được        thiếu trường ⟹ None, KHÔNG phải lỗi
`null` == VẮNG MẶT trong capture    ⟹ cùng content_hash ⟹ nâng cấp hợp đồng
                                     không tự khai là một lần đổi danh mục
Đổi giá trị THẬT ⟹ content_hash đổi ⟹ Reports nhận bản chiếu mới
Thiếu nhóm hàng ở một dòng          KHÔNG làm hỏng cả response
```

Hai chỗ **có** đổi hình dạng đầu ra, cả hai đã cập nhật cùng phiên:
`chieuBoard()` trả năm khoá thay vì bốn (hai bộ kiểm Tracking canh hình dạng
đã sửa theo), và bản chiếu hiển thị của Reports mang ba trường thay vì hai
(`tests/test_r5_workspace_identity_ux.py` cập nhật theo). Cả hai là hợp đồng
NỘI BỘ giữa mã và bộ kiểm của chính nó, không phải hợp đồng với bên thứ ba.

---

## 7. Thứ tự triển khai và rollback

### Thứ tự deploy (KHÔNG thực hiện trong phiên này)

```text
1. Tracking trước.  Nó chỉ THÊM một trường vào response. Reports đời R5 đọc
                    payload mới vẫn chạy đúng — trường lạ bị bỏ qua ở
                    `_rows_from_board()` (danh sách trắng, không phải blacklist).
2. Reports sau.     Reports đời R5.1 đọc payload đời R5 cũng chạy đúng —
                    thiếu trường ⟹ None.
```

Hai chiều đều an toàn, nên thứ tự trên là ưu tiên chứ không phải ràng buộc.
Không có bước migration nào ở giữa.

### Rollback

```text
Tracking   revert 39528ee. `chieuBoard()` quay lại bốn trường. Reports đời
           R5.1 đọc payload ấy ra category_label = None cho mọi dòng — màn
           hình hiện ô trống, không lỗi, không mất tiền.
Reports    revert 0b8ac31. Cột "Nhóm hàng" biến mất; bản chiếu hiển thị cũ
           (ba trường) vẫn đọc được bằng mã hai trường vì `read()` chỉ lấy
           những khoá nó biết.
Một phía   revert riêng phía nào cũng được, không cần phối hợp.
Dữ liệu    KHÔNG có gì để rollback: không migration, không bảng, không cột
           database, không file capture nào bị ghi đè (INV-11).
```

---

## 8. Trạng thái cuối và việc CHƯA làm

```text
Trạng thái task     IMPLEMENTED
CHECK-R51-01..24    PASS (E1)
CHECK-R51-25        NOT_TESTED — Independent Review CHƯA chạy
CHECK-R51-26        NOT_TESTED — Owner CHƯA nghiệm thu trên production
Merge               KHÔNG thực hiện (brief §9)
Deploy              KHÔNG thực hiện (brief §9)
Repair cycle tiêu   0
```

Phiên này **không** tự đánh dấu Independent Review hay Owner Acceptance.

### Exact HEAD cuối phiên

```text
Reports   0b8ac31bb138b08356699f70424cda5dbcb6017b
          nhánh claude/r5-1-category-label-1nnct7
Tracking  39528ee5260f4cd5a6bdf92c7f020ad5ecbda362
          nhánh claude/r5-1-category-label-1nnct7
```

### Ghi chú môi trường

Container phiên này không có sẵn phụ thuộc Python của Reports; phiên tự dựng
`.venv` bằng `python3 -m venv` + `pip install -e ".[dev,web,storage,history]"`.
`.venv/` đã nằm trong `.gitignore` và KHÔNG được commit. Mọi lệnh `pytest` ghi
ở §4 chạy bằng `.venv/bin/python`.
