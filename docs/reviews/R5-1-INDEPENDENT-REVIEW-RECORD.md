# R5.1 — Independent Review (bản ghi review ĐỘC LẬP)

> **TRẠNG THÁI SAU PHIÊN NÀY (`S140`, 2026-09-09).** Owner đã điều chỉnh kết
> luận của bản ghi này từ `ACCEPT_WITH_RECORDED_RISK` thành `REPAIR_REQUIRED`
> **cho mục tiêu sử dụng `category_label` ở `R6`**, và `R5.1 REPAIR-1` đã sửa
> xong. `AR-R5.1-05` và `AR-R5.1-06` **ĐÃ ĐÓNG** — không còn là rủi ro được
> ghi nhận; `AR-R5.1-03` cũng đóng theo. Nội dung dưới đây giữ NGUYÊN VĂN làm
> bản ghi lịch sử của vòng review — nó đo đúng hệ thống tại `2c2c139`, và
> chính nó đã chỉ ra rằng phép sửa thật đòi mở lại `DEC-204`. Xem `DEC-205`,
> `docs/tasks/R5-1-REPAIR-1-tu-dien-nhom-hang.md` và
> `docs/sessions/S140-r51-repair-1.md`.
>
> `CHECK-R51-25` (vòng review NÀY) vẫn `PASS` — nó đã chạy đủ.
> `CHECK-R51R1-17` (Independent Review vòng 2, trên HEAD sau repair) là
> `NOT_TESTED`.

Phiên này chỉ ĐỌC, CHẠY, TẠO PROBE và KIỂM. Không sửa một dòng mã sản phẩm
nào, không merge, không deploy, không triển khai `R6`, không đánh dấu Owner
Acceptance.

Task canonical: `docs/tasks/R5-1-nhom-hang-category-label.md`.
Bàn giao triển khai: `docs/sessions/S138-r51-nhom-hang.md`.
Thẩm quyền: `PROJECT/PROJECT_DECISIONS.md` → `DEC-204`; `ADR-111` §3.
Hợp đồng: `docs/spec/TASK-105D-DATA-CONTRACT.md` §4.4, §4.6.
Bàn giao review này: `docs/sessions/S139-r51-independent-review.md`.

---

## 1. Kết luận

```text
KẾT LUẬN               ACCEPT_WITH_RECORDED_RISK

EXACT HEAD ĐÃ REVIEW   Reports   2c2c139d9d7ec34d8007a463a82a694956496940
                       Tracking  39528ee5260f4cd5a6bdf92c7f020ad5ecbda362
NỀN TÍCH HỢP           Reports   3b35b7acee2159b007c4398045f4b6f6843f7de8
                       Tracking  918183c48c4d4c45b5ce1348d734e073e537c6e4
NHÁNH MẶC ĐỊNH THẬT    Reports   claude/extract-upload-repo-gq2ws4
                       Tracking  main

REPAIR_REQUIRED        0 finding
ACCEPTED_RISK MỚI      2 finding  (AR-R5.1-05, AR-R5.1-06)
ĐÍNH CHÍNH TÀI LIỆU    1          (COR-R5.1-01 — một mệnh đề trong DEC-204 §3
                                  và task §6 mạnh hơn hành vi thật)
AR-R5.1-01 … -04       tái kiểm chứng — cả bốn GIỮ NGUYÊN mức ACCEPTED_RISK

CHECK-R51-25           PASS (E1) — Independent Review ĐÃ CHẠY ĐỦ; kết luận
                       ACCEPT_WITH_RECORDED_RISK
CHECK-R51-26           VẪN NOT_TESTED — Owner nghiệm thu production, KHÔNG
                       phiên nào tự đóng
REPAIR CYCLE TIÊU      0 (lineage R5 giữ nguyên 2 allowed / 1 used /
                       1 remaining)
```

Năm chuỗi bắt buộc đều được kiểm trực tiếp trên exact HEAD, qua chính
`nhomCua()`/`chieuBoard()` của Tracking và chính route Flask của Reports.
**Không tìm được** một category gắn sang mã khác, một nhánh nào suy nhóm hàng
từ `product_raw`, một dòng conflict/stale/OUT_OF_CATALOG/chưa phân loại nào
nhận category của candidate, một đồng tiền nào đổi, hay một đường nào IMEI
rời khỏi tab nhân viên.

Hai finding mới đều nằm đúng trong nhóm mà brief xếp `ACCEPTED_RISK`: hậu quả
dừng ở MỘT ô nhãn trên bảng kê nhân viên (mặc định ẩn), không đổi mapping,
doanh thu, giá nhập, lợi nhuận, coverage hay vân tay chốt kỳ, và cả hai đều
nhận ra được bằng mắt khi đối chiếu.

---

## 2. Điều kiện mở phiên — xác minh bằng git TRƯỚC khi kiểm

```text
$ git -C Tracking remote show origin | grep 'HEAD branch'
  HEAD branch: main
$ git -C Reports remote show origin | grep 'HEAD branch'
  HEAD branch: claude/extract-upload-repo-gq2ws4

$ git -C Tracking rev-parse HEAD
39528ee5260f4cd5a6bdf92c7f020ad5ecbda362
$ git -C Tracking rev-parse origin/main
918183c48c4d4c45b5ce1348d734e073e537c6e4
$ git -C Tracking merge-base --is-ancestor origin/main HEAD && echo YES
YES
$ git -C Tracking log --oneline origin/main..HEAD
39528ee R5.1 §4: /api/xuat/board xuất thêm category_label đã chuẩn hoá

$ git -C Reports rev-parse HEAD
2c2c139d9d7ec34d8007a463a82a694956496940
$ git -C Reports merge-base --is-ancestor 3b35b7a HEAD && echo YES
YES
$ git -C Reports log --oneline 3b35b7a..HEAD
2c2c139 S138: SHA của HEAD gồm tài liệu, cho vòng review kế tiếp
f982995 R5.1: hợp đồng, task/checklist, DEC-204, bàn giao S138
0b8ac31 R5.1 §5: Reports đọc category_label từ hợp đồng catalog Tracking

$ git status --porcelain | wc -l
0
```

`R5` đã merge ở cả hai nền: Tracking `main` chứa `918183c` (`R5 §5`), Reports
default chứa `f5e4e76` (`R5` merge). Không có commit lạ ngoài `R5.1` ở cả hai
repo.

Branch authority (`scripts/branch_authority_check.sh`), chạy ở chế độ
DETACHED trên đúng exact target — chế độ canonical của một phiên review:

```text
MODE                 : DETACHED
TARGET_SHA           : 2c2c139d9d7ec34d8007a463a82a694956496940
TARGET_RESOLVED      : 2c2c139d9d7ec34d8007a463a82a694956496940
WORKTREE             : CLEAN
AUTHORITY            : DETACHED_EXACT_TARGET
RESULT               : AUTHORITY_OK
```

`0b8ac31` (code-only) KHÔNG được review riêng: review chạy trên `2c2c139`,
HEAD có đủ tài liệu handoff/task, đúng chỉ thị.

---

## 3. Chuỗi 1 — Tracking: chuẩn hoá và chống rò dữ liệu

Kiểm bằng probe độc lập cắt CHÍNH `nhomCua`/`chieuBoard`/`hangCua`/`chuanSo`
ra khỏi `src/index.js` và chạy chúng (không đọc bộ kiểm có sẵn):

```text
[1] cat sạch          "Tivi Samsung"  ⟹ brand Samsung, category "Tivi"
                      "Tủ lạnh Samsung" ⟹ "Tủ lạnh"     (dấu tiếng Việt giữ nguyên)
                      "Điều hoà Daikin" ⟹ "Điều hoà"
[2] sentinel          "Chưa phân loại" / "Không sử dụng" / rỗng / null ⟹ null
[3] cat bẩn ⟹ null    giá · giá-chữ · SĐT · link · note · quá nhiều từ ·
                      quá dài · chữ-số lẫn · dấu câu · emoji
[4] KHÔNG đọc name    cat rỗng + name "Tivi Samsung QLED" ⟹ null
                      LA-01 (name "Tivi cũ trưng bày", chưa xếp cat) ⟹ null
[5] không fuzzy       "TV" và "Tivi" ra hai nhóm khác nhau; "Tủ mát" ≠ "Tủ lạnh"
[6] hai hãng          "Tivi Sony Samsung" ⟹ null
                      cat mang hãng A, name mang hãng B ⟹ vẫn cắt theo cat
[7] chieuBoard        đúng NĂM khoá: alt, brand, category_label, model_label, name
                      KHÔNG lộ p, tp, _c, q, cat thô, NCC, note, link

=== probe nhomCua: 33 đạt, 0 hỏng
```

Mục 9 (`/api/xuat/board` chỉ xuất allowlist): xác nhận `chieuBoard()` dựng
object MỚI từ danh sách trắng, không `{...row}`. Probe cho một dòng board đầy
đủ (`p`, `tp`, `q`, `_c`, `ncc`, `note`, `link`, `cat`) xác nhận không giá
trị nào trong số đó xuất hiện trong payload, và chuỗi `"Tivi Samsung"` (cat
thô) cũng không.

**Mục 8 — rủi ro `Tivi 4K` bị null.** Tái hiện: `"Tivi 4K"`, `"Tivi 8K"`,
`"Loa 2.1"`, `"Điều hoà Inverter 2 chiều"` đều ra `null`. Đây là **mất nhãn**,
không đổi mapping và không đổi tiền — đúng điều kiện `ACCEPTED_RISK` mà chỉ
thị nêu. Giữ nguyên `AR-R5.1-02`.

---

## 4. Chuỗi 2 — hợp đồng và backward compatibility

Fixture xuyên repo do **code Tracking sinh** (`kiem/smoke/sinh-catalog-reports.mjs`
cắt chính `chieuBoard()` từ `src/index.js`), không gõ tay. Payload sinh ra
trùng khít ví dụ hợp đồng §4.6, gồm cả `LA-01` với cả ba trường `null` dù
`name` nói rõ chữ "Tivi".

Probe độc lập trên loader thật:

```text
[2.3] artifact R5 CŨ (không có category_label) ⟹ load được, category = None
[2.4] artifact SỬA TAY sau capture ⟹ content_hash_mismatch (cả khi ĐỔI giá
      trị lẫn khi XOÁ về null)
[2.5] category đổi ⟹ hash ĐỔI;  dòng không có category ⟹ hash GIỮ NGUYÊN
      giữa hợp đồng cũ và mới
[2.6] sai KIỂU (int, list, dict, bool) ⟹ từ chối, KHÔNG ép thành chuỗi

=== probe hash/backcompat: 11 đạt, 0 hỏng
```

Mục 7 (client cũ bỏ qua field mới): trường mới là additive, không đổi nghĩa
`name`/`alt`/`model_label`/`brand`, không đổi khoá node — xác nhận trên
payload thật.

---

## 5. Chuỗi 3 — Product Identity và các cổng authority

Kiểm qua production resolver + route thật (smoke xuyên hai repo, mục 2–4):

```text
1. CONFIRMED nhận category của ĐÚNG tracking_code       ✓
2. Conflict KHÔNG nhận category của candidate            ✓
3. Stale target KHÔNG nhận category                      ✓ (alias.map giữ
   nguyên, INV-16 — Tracking không tự gộp)
4. OUT_OF_CATALOG KHÔNG nhận category                    ✓
5. Chưa phân loại KHÔNG nhận category (giữ TÊN THÔ)      ✓
6. Đổi category bên Tracking ⟹ nhãn đổi; product_key,
   mapping, doanh thu, giá nhập, lợi nhuận KHÔNG đổi     ✓
7. Không nhánh nào đọc product_raw để dựng category      ✓ (đọc mã nguồn)
8. Refresh / create_app() mới / restart vẫn giữ category ✓
9. Mất bản chiếu ephemeral ⟹ ô "—", không 500, không
   đổi tiền, không gắn nhãn của mã khác                  ✓
```

Cơ chế đúng như `DEC-204` §6 đòi: `category_label` đi qua **đúng hai cổng đã
giữ `brand`** — `confirmed_identities()` ở `_catalog_labels()` và
`_catalog_field()` (chặn tại `identity.classification != CLASS_MATCHED_TRACKING`).
Không có cổng thứ hai viết riêng.

Mục 7 xác minh bằng đọc mã: `_match_field()` chỉ đọc `tracking_code`, `name`,
`alt` — không đọc `brand`/`model_label`/`category_label`. Nhóm hàng KHÔNG
tham gia identity matching.

---

## 6. Chuỗi 4 — workspace nhân viên và privacy

```text
số cột                14
vị trí 3/4/5          Nhóm hàng · Hãng · IMEI
OPTIONAL_COLUMN_INDEXES (3, 4, 5) — đúng ba cột ấy
nhãn nút              "HIỆN/ẨN NHÓM HÀNG, HÃNG & IMEI"
toggle                theo CLASS `col-optional` + `data-optional-hidden` trên
                      chính bảng ⟹ cột thứ ba tự vào chung MỘT nút, không có
                      trạng thái thứ hai
category null         hiện "—" (không hiện raw cat, không tên bịa)
cột hẹp               col-narrow: max-width 96px, nowrap, ellipsis, title đầy đủ
hàng TỔNG             16 ô = 14 cột + 2 ô hành động — khớp header, không lệch

=== probe DOM/CSS: 17 đạt, 0 hỏng
```

Mục 4/5 (CONFIRMED hiện đúng model/brand/category; chưa phân loại giữ tên
gốc) đã kiểm qua route POST phân loại thật trong smoke.

Mục 6/7 — **IMEI**. `R5.1` không chạm mã IMEI; nó chỉ chèn một cột trước.
`grep` toàn bộ `app/` + `tools/` cho `category_label` cho ra đúng 6 module:
capture tool, loader, `catalog_display`, `workspace_presentation`, `server`
(bản chiếu route) và MỘT template. **Không** module export, summary,
snapshot, dashboard hay log nào. `tests/test_r5_imei_boundary.py` xanh trên
exact HEAD.

Mục 8 — hình học thật (bề rộng cột trên màn hình thật) để Owner nghiệm thu
bằng mắt ở `CHECK-R51-26`; DOM/CSS/JS đã kiểm trước và đúng.

---

## 7. Chuỗi 5 — bất biến R1–R5

Chạy lại trên exact HEAD, không tin số trong bàn giao:

```text
R1 pricing / daily-min      test_daily_min_{contract,vertical,orchestration,
                            capture_tool}.py, test_web_daily_min_integration.py
R2 identity / manual price  test_r2_{product_classification,web_workflow,
                            legacy_history}.py
R3 period close / binding   test_r3_{export_and_period_close,import_binding,
                            ir_repair_fingerprint,golden_reconciliation}.py
                            ⟹ 333 passed

R5 identity/workspace/      test_r5_{imei_boundary,product_identity_fields,
   IMEI/capture             workspace_identity_ux,repair_1,change_list,
                            removed_lines,order_edit_form,two_window_chart}.py,
                            test_tracking_{catalog_capture,authoritative_identity}.py,
                            test_employee_workspace_ux.py
                            ⟹ 225 passed
```

Mục 8 (category đổi không đổi tiền/coverage/fingerprint) được chứng minh
trực tiếp trong smoke mục 4: `totals-purchase`/`totals-sell`/`totals-profit`/
`totals-converted` giữ nguyên từng chuỗi trước và sau khi nhóm hàng xuất hiện,
và sau khi đổi nhóm hàng bên Tracking.

---

## 8. Lệnh kiểm bắt buộc — kết quả nguyên văn

```text
Tracking
  $ npm test
    62 bộ · 2825 đạt · 0 hỏng · 2 bỏ qua
    Tất cả đạt.
  $ npm run build
    62 bộ · 2825 đạt · 0 hỏng · 2 bỏ qua
    Đã dựng bản phục vụ vào ./dist
      7 file, xén chú thích 1 file HTML
      658 KB → 411 KB  (bớt 37%)

Reports
  $ python -m pytest -q tests/test_r51_category_label.py
    24 passed in 2.88s
  $ python -m pytest -q   (toàn bộ)
    3256 passed, 12 skipped in 187.54s

Smoke xuyên hai repo (producer THẬT của Tracking + route Flask THẬT)
  $ python scripts/r51_crossrepo_smoke.py --tracking /home/user/Tracking
    KẾT QUẢ SMOKE: 45 PASS, 0 FAIL

Governance
  structure            GOVERNANCE STRUCTURE: PASS (21 required paths)
  project_state        PROJECT STATE: PASS
  evidence             EVIDENCE VALIDATION: PASS (161 REQUIRED PASS record)
  task_completion      TASK COMPLETION: PASS (14 DONE task)
  reference_integrity  FAIL — 4 reference (xem dưới)
  branch_authority     AUTHORITY_OK (DETACHED_EXACT_TARGET)
```

**`reference_integrity` — baseline, KHÔNG phải lỗi mới.** Chạy lại trên nền
`3b35b7a` trong một worktree riêng cho ra **đúng bốn reference ấy**:

```text
trên 2c2c139 : quét 283 file .md — 4 reference không phân giải được
trên 3b35b7a : quét 280 file .md — 4 reference không phân giải được  (Y HỆT)

- docs/sessions/S136-r5-integration.md -> /tmp/claude-0/smoke/r5_repair_crossrepo_smoke.py
- docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> /README.md
- docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> CODE_OF_CONDUCT.md
- docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> CONTRIBUTING.md
```

`R5.1` thêm 3 file `.md` và **không** thêm một reference hỏng nào.

**Đối chiếu số của bàn giao.** Bàn giao ghi `3257 passed, 11 skipped`; phiên
này đo `3256 passed, 12 skipped` — cùng tổng `3268`. Chênh lệch là
`tests/test_boto3_putobject_ifnonematch_capability.py`, skip vì máy review
không cài extra `storage` (`No module named 'botocore'`). Đây là khác biệt
MÔI TRƯỜNG, không phải hồi quy; mọi số khác của bàn giao tái hiện đúng.

---

## 9. Finding

### `AR-R5.1-05` — ACCEPTED_RISK (mới)

**`cat` bẩn nhưng ĐÚNG HÌNH DẠNG đi ra nguyên văn.** `HINH_NHOM` là một danh
sách trắng theo HÌNH DẠNG, nên nó chặn được ô nhiễm mang chữ số, dấu câu, quá
4 từ hay quá 40 ký tự — nhưng **không** phân biệt được ô nhiễm NGỮ NGHĨA gồm
toàn chữ cái. Tái hiện trên exact HEAD:

```text
cat="Tivi kho anh Ba"     -> "Tivi kho anh Ba"
cat="Tủ lạnh nợ NCC"      -> "Tủ lạnh nợ NCC"
cat="Tivi Đất Việt"       -> "Tivi Đất Việt"      (Đất Việt là NCC có thật)
cat="Tivi hàng gửi"       -> "Tivi hàng gửi"
cat="Tivi trưng bày"      -> "Tivi trưng bày"
```

Đường vào là thật, không giả định: `setCat()` nhận chuỗi từ `prompt()` của
ô "+ Ngành hàng mới...", `.trim()` rồi ghi thẳng `board/<mã>/cat` — **không
một phép kiểm nào**. Chính `DEC-204` đã ghi nhận `cat` bẩn là chuyện có thật.

**Vì sao ACCEPTED_RISK chứ không REPAIR_REQUIRED:**
- Hậu quả dừng ở MỘT ô nhãn, trên cột mặc định ẨN của tab nhân viên. Không
  đổi mapping, product_key, doanh thu, giá nhập, lợi nhuận, coverage hay vân
  tay chốt kỳ — kiểm trực tiếp ở chuỗi 3 mục 6.
- Thứ đi ra là chính TÊN NGÀNH HÀNG mà người của Tracking tự gõ, ở dạng đã
  tách hãng và đã lọc hình dạng. Giá vốn, giá chốt, tồn, số Engine, NCC ở
  trường riêng, note và link **không** đi ra — allowlist của `chieuBoard()`
  vẫn giữ đúng như thiết kế (chuỗi 1 mục 7).
- Nhận ra ngay bằng mắt: một nhãn như "Tivi kho anh Ba" đứng cạnh "Tủ lạnh"
  thì tự nó tố cáo, và sửa nằm đúng nơi có thẩm quyền (đổi tên ngành hàng bên
  Tracking, lần capture kế tiếp chở giá trị mới sang).
- **Không có phép sửa nào nằm trong kiến trúc đã duyệt.** Một luật hình dạng
  không thể phân biệt "Tủ lạnh" với "Tivi kho anh Ba"; siết số từ xuống 2 sẽ
  giết cả nhóm hàng thật ("Nồi cơm điện"), còn danh sách trắng theo GIÁ TRỊ
  đã bị `DEC-204` §3 loại có lập luận. Sửa thật sự đòi mở lại `DEC-204` —
  việc của Owner, không phải của một repair cycle.

**Giảm nhẹ có sẵn:** cột mặc định ẩn; `null` và nhãn lạ đều không ảnh hưởng
tiền; Owner đối chiếu được ở `CHECK-R51-26`.

### `AR-R5.1-06` — ACCEPTED_RISK (mới)

**Hãng ngoài `HANG` ở lại trong nhãn nhóm hàng.** `HANG` là danh sách ĐÓNG 39
hãng; `nhomCua()` chỉ tách được hãng nằm trong đó.

```text
cat="Tivi Vsmart"       -> "Tivi Vsmart"
cat="Tủ lạnh Hòa Phát"  -> "Tủ lạnh Hòa Phát"
cat="Nồi cơm Cuckoo"    -> "Nồi cơm Cuckoo"
```

Hợp đồng §4.6 phát biểu `category_label` "không bao giờ chứa tên hãng"; với
hãng ngoài danh sách, phát biểu ấy mạnh hơn hành vi thật. Hậu quả là một tên
hãng hiện ở cột Nhóm hàng — mà `brand` cho chính dòng đó đằng nào cũng là
`null` và cũng hiện "—", nên không có mâu thuẫn nào trên màn hình. Không đổi
tiền, không đổi mapping. Sửa đúng chỗ: thêm một dòng vào `HANG`.

### `COR-R5.1-01` — đính chính tài liệu (không phải finding mã)

`DEC-204` §3 viết "Không lọt ⟹ `null`, KHÔNG đi ra nguyên văn", và
`AR-R5.1-02` viết đánh đổi ngược lại "mở đúng đường rò mà §4.5 cấm". Hai câu
ấy đọc thành *luật hình dạng chặn được mọi ô nhiễm*, trong khi nó chỉ chặn ô
nhiễm mang chữ số/dấu câu/độ dài. `AR-R5.1-05` ở trên là bản ghi đúng của
hành vi thật. **Không sửa `DEC-204`** (artifact lịch sử của một quyết định đã
ban hành); bản ghi này và mục 6 của task là nơi trạng thái đúng được giữ.

### Tái kiểm chứng `AR-R5.1-01` … `-04`

```text
AR-R5.1-01  mã chưa xếp ngành hàng ⟹ null       GIỮ NGUYÊN (LA-01 tái hiện)
AR-R5.1-02  nhóm hàng có chữ số ⟹ null          GIỮ NGUYÊN ("Tivi 4K" tái hiện)
AR-R5.1-03  không gộp đồng nghĩa                GIỮ NGUYÊN ("TV" ≠ "Tivi")
AR-R5.1-04  bản chiếu trên đĩa ephemeral        GIỮ NGUYÊN (mất file ⟹ "—",
                                                tiền không đổi)
```

---

## 10. Điều phiên này KHÔNG làm

- KHÔNG sửa một dòng mã sản phẩm nào (chỉ thị §"Không sửa code sản phẩm").
- KHÔNG merge, KHÔNG deploy, KHÔNG triển khai `R6`.
- KHÔNG đánh dấu Owner Acceptance. `CHECK-R51-26` giữ `NOT_TESTED`.
- KHÔNG sửa `DEC-204` hay `governance/core/V4_1_POLICY_FREEZE.md`.
