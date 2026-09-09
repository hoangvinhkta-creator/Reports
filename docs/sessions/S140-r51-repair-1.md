# S140 — R5.1 REPAIR-1: khoá `category_label` thành từ điển đóng an toàn cho R6

Ngày: 2026-09-09
Task Mode: MAJOR (repair cycle)
Task: `docs/tasks/R5-1-REPAIR-1-tu-dien-nhom-hang.md`
Kết quả phiên: **IMPLEMENTED** — KHÔNG merge, KHÔNG deploy, KHÔNG làm `R6`.

---

## 1. Preflight

### 1.1 Nhánh mặc định thật, và nó có đổi không

```text
Reports   nhánh mặc định: claude/extract-upload-repo-gq2ws4   (KHÔNG phải "main")
          tip: 3b35b7acee2159b007c4398045f4b6f6843f7de8
Tracking  nhánh mặc định: main
          tip: 918183c48c4d4c45b5ce1348d734e073e537c6e4

$ git -C Reports  log --oneline 3b35b7a..origin/claude/extract-upload-repo-gq2ws4
(rỗng)
$ git -C Tracking log --oneline 918183c..origin/main
(rỗng)
```

**Cả hai nhánh mặc định KHÔNG đổi** kể từ `S138`. Không có divergence phải xử
lý, không rebase, không merge lén.

### 1.2 Exact full SHA đã resolve

```text
Reports   implementation  2c2c139d9d7ec34d8007a463a82a694956496940
          review docs     dd7cd0461d3d5c8deff9465069bbd2cd0bf55120
                          = tip của claude/r5-1-category-label-review-bslffx
Tracking  implementation  39528ee5260f4cd5a6bdf92c7f020ad5ecbda362
```

`dd7cd04` là con TRỰC TIẾP của `2c2c139`:

```text
$ git merge-base --is-ancestor 2c2c139 dd7cd04 && echo YES
YES
$ git log --oneline 2c2c139..dd7cd04
dd7cd04 S139: Independent Review R5.1 — ACCEPT_WITH_RECORDED_RISK (không sửa mã)
```

Nên nhánh repair của Reports dựng từ `dd7cd04` mang **cả** implementation
`R5.1` **lẫn** tài liệu review — đúng yêu cầu §3.5 của brief, và không mất
lịch sử review hay trạng thái check.

### 1.3 Working tree và nhánh repair

```text
$ git -C Reports status --porcelain | wc -l    → 0
$ git -C Tracking status --porcelain | wc -l   → 0

$ git -C Reports  checkout -b claude/r5-1-repair-1-taxonomy dd7cd04
$ git -C Tracking checkout -b claude/r5-1-repair-1-taxonomy 39528ee
```

Không một dòng mã nào được chép tay từ nhánh cũ: cả hai nhánh repair đi thẳng
từ exact SHA mà brief chỉ định.

---

## 2. Vì sao luật cũ không sửa được bằng cách siết chặt

`HINH_NHOM` chặn ô nhiễm mang **chữ số, dấu câu, độ dài**. Ô nhiễm nguy hiểm
lại gồm toàn chữ cái:

```text
"Tủ lạnh"          2 từ, toàn chữ cái   ⟹ nhóm hàng THẬT
"Tivi kho anh Ba"  4 từ, toàn chữ cái   ⟹ ghi chú kho
```

Không tham số nào của một luật hình dạng phân biệt được hai dòng ấy; siết số
từ xuống 2 giết cả "Nồi cơm điện" và "Bình nóng lạnh". Vấn đề nằm ở chỗ **đầu
ra được dẫn xuất từ chuỗi người dùng gõ**, không nằm ở độ chặt.

Từ điển đóng đổi LOẠI bảo đảm:

```text
đầu ra ∈ NHOM ∪ {null}
⟺ không một ký tự nào người dùng gõ rời khỏi Tracking bằng trường này
```

Và đó là mức bảo đảm mà một **khoá gộp báo cáo** cần. Lập luận đầy đủ, kèm
quan hệ thay thế với `DEC-204`, nằm ở `DEC-205`.

---

## 3. File mã đã đổi

### Tracking (`39528ee` → `11a199b`)

```text
src/index.js                        +163/-…  bỏ HINH_NHOM; thêm NHOM (13 mục),
                                             NHOM_TRA, HANG_TRA; viết lại
                                             nhomCua(); thêm Vsmart vào HANG
kiem/nhom-hang.js                   viết lại  82 phép thử (trước 57)
kiem/smoke/sinh-catalog-reports.mjs +53      thêm BAN-01/02/03, VS-01, ML-01
kiem/hang-va-model.js               +4       danh sách trích đoạn theo mã mới
```

### Reports (`dd7cd04` → HEAD phiên)

```text
tests/test_r51_category_label.py    +2 bài   canh ranh giới thẩm quyền
scripts/r51_crossrepo_smoke.py      cập nhật  các trường hợp repair + phép đo
                                             "mọi nhãn ∈ từ điển"
docs/, PROJECT/                     tài liệu (mục 6)
```

**Reports KHÔNG đổi một dòng mã sản phẩm nào.** Nó là bên tiêu thụ; hợp đồng
không đổi hình dạng (vẫn là `string | null` tùy chọn), chỉ TẬP GIÁ TRỊ hẹp
lại. `pytest` xanh trước khi thêm test mới đã chứng minh điều đó.

---

## 4. Bằng chứng (E1 — output nguyên văn)

### 4.1 Bảng ví dụ §4 của brief, chạy qua chính `nhomCua()`

```text
--- phải RA nhãn ---
ok    "Tivi Samsung"                   -> "Tivi"
ok    "Tủ lạnh Samsung"                -> "Tủ lạnh"
ok    "Tivi Vsmart"                    -> "Tivi"
ok    "Nồi cơm điện Sharp"             -> "Nồi cơm điện"
--- phải NULL ---
ok    "Tivi kho anh Ba"                -> null
ok    "Tủ lạnh nợ NCC"                 -> null
ok    "Tivi Đất Việt"                  -> null
ok    "Tivi hàng gửi"                  -> null
ok    "Tivi 4K"                        -> null
ok    "Điều hòa Inverter 2 chiều"      -> null
```

### 4.2 Tracking — `npm test` và `npm run build`

```text
$ npm test
  ✓ nhom-hang.js             82 đạt
  ✓ hang-va-model.js         29 đạt
  ✓ xuat-baocao.js          175 đạt
────────────────────────────────────────────────────
  62 bộ · 2850 đạt · 0 hỏng · 2 bỏ qua
  Tất cả đạt.

$ npm run build
  62 bộ · 2850 đạt · 0 hỏng · 2 bỏ qua
Đã dựng bản phục vụ vào ./dist — 7 file, 658 KB → 411 KB (bớt 37%)
```

Nền `R5.1` là `2825 đạt`; repair thêm 25 phép thử ròng.

### 4.3 Reports — full `pytest`

```text
$ .venv/bin/python -m pytest tests/ -q      (TRƯỚC khi thêm test mới)
3257 passed, 11 skipped in 244.94s

$ .venv/bin/python -m pytest tests/ -q      (SAU khi thêm 2 bài)
3259 passed, 11 skipped in 238.99s
```

Lượt chạy đầu là bằng chứng cho một mệnh đề riêng: **Reports không cần đổi mã
để chịu được luật mới.** 3257 → 3257 với Tracking đã đổi hoàn toàn cách dẫn
xuất trường này.

### 4.4 Smoke xuyên hai repo

```text
$ .venv/bin/python scripts/r51_crossrepo_smoke.py

1) Tracking sinh board/alias bằng chính `chieuBoard()` thật
    55Q6FA   model="QLED 55Q6FA"  brand="Samsung"  category="Tivi"
    RT38     model="RT38"         brand="Samsung"  category="Tủ lạnh"
    LA-01    model=null           brand=null       category=null
    XUNG-01  model=null           brand=null       category="Tivi"
    BAN-01   model=null           brand="Samsung"  category=null
    BAN-02   model=null           brand="LG"       category=null
    BAN-03   model=null           brand=null       category=null
    VS-01    model="43KD6600"     brand="Vsmart"   category="Tivi"
    ML-01    model="SC-09TL32"    brand="Casper"   category="Điều hoà"
  ok   mọi trường hợp §7 + REPAIR-1 đều có mặt
  ok   "Tivi kho anh Ba" ⟹ null
  ok   "Tivi Đất Việt" (NCC) ⟹ null
  ok   "Tủ lạnh Hòa Phát" (hãng ngoài HANG) ⟹ null
  ok   hãng đã thêm vào HANG ⟹ nhãn ra bình thường
  ok   đồng nghĩa gộp: "Máy lạnh" ⟹ "Điều hoà"
  ok   cat hai hãng: nhóm hàng CHẮC CHẮN, hãng thì không
  ok   từ điển đọc được từ src/index.js
  ok   MỌI nhãn đi qua ranh giới đều thuộc từ điển đóng
  ok   không lộ ghi chú trong cat / hãng lạ trong cat / tên NCC / giá vốn /
       giá chốt / số Engine / tồn kho / giá bán buôn / link nội bộ
  ok   đối chứng: marker có thật trong BOARD thô của producer

2) Reports capture (mã thật) đọc payload do Tracking sinh
  ok   BAN-01: `cat` bẩn ⟹ nhóm hàng None qua tới snapshot
  ok   ML-01: nhãn canonical qua tới snapshot
  ok   XUNG-01: hãng None, nhóm hàng Tivi

3) Artifact R5 cũ (không có category_label) vẫn đọc được   [5/5 ok]

4) Route web thật: capture → bản chiếu → bảng kê nhân viên
  ok   bản chiếu giữ mọi dòng CÓ ít nhất một trường
  ok   ...và BAN-01/BAN-02 có mặt vì HÃNG, nhóm hàng của chúng vẫn None
  ok   BAN-03 không có gì để nói nên không chiếm chỗ
  ok   tổng tiền KHÔNG đổi sau khi nhóm hàng xuất hiện
  ok   đổi nhóm hàng bên Tracking hiện ra ngay ở lần đọc sau
  ok   ...và KHÔNG đổi một đồng nào
  ok   sau create_app() mới vẫn đọc đúng

KẾT QUẢ SMOKE: 58 PASS, 0 FAIL
```

Phép đo quan trọng nhất là `MỌI nhãn đi qua ranh giới đều thuộc từ điển đóng`,
và nó đọc từ điển **ngược từ `src/index.js`** chứ không gõ lại — gõ lại là hai
danh sách trôi khỏi nhau.

### 4.5 Đối chứng — bộ kiểm này bắt được hành vi CŨ

Một bộ kiểm chỉ khẳng định "nay đã đúng" thì không chứng minh nó bắt được cái
sai. `kiem/nhom-hang.js` mục 5 chạy chính luật cũ:

```text
ok  đối chứng: luật CŨ cho "Tivi kho anh Ba" đi ra nguyên văn
ok  đối chứng: luật CŨ đó KHÔNG thuộc từ điển
ok  đối chứng: cùng tiền tố ấy KHÔNG có đuôi bẩn thì VẪN ra nhãn
```

Dòng thứ ba chặn một cách "sửa" vừa qua hết bài vừa giết tính năng: trả `null`
cho mọi thứ.

### 4.6 Governance validator

```text
GOVERNANCE STRUCTURE: PASS
PROJECT STATE:        PASS
EVIDENCE VALIDATION:  PASS
TASK COMPLETION:      PASS
REFERENCE INTEGRITY:  FAIL — 4 finding baseline có TỪ TRƯỚC phiên
                      (TASK-REM-T06 ×3, một đường /tmp trong S136)
```

---

## 5. Đổi hành vi có chủ đích (không phải hồi quy)

```text
cat = "Tivi Sony Samsung"     R5.1: null        REPAIR-1: "Tivi"
```

`R5.1` cắt nhóm hàng bằng cách bỏ tên hãng, nên hai hãng làm `hangCua()` im và
nhóm hàng im theo. Nay hai câu hỏi tách rời: nhóm hàng ở đó **chắc chắn** (mọi
từ còn lại đều là hãng đã biết), chỉ hãng là không chắc — và `brand` vẫn
`null`. Trả `"Tivi"` đúng hơn và vẫn an toàn.

```text
cat = "Tủ lạnh Hòa Phát"      R5.1: "Tủ lạnh Hòa Phát"   REPAIR-1: null
```

Đây là `AR-R5.1-06` đóng lại: hợp đồng nói nhãn không bao giờ chứa tên hãng,
và nay hành vi khớp câu ấy. Bảo thủ hơn mức tối thiểu — xem
`ACCEPTED_RISK R5.1R1-03`.

---

## 6. Tài liệu đã cập nhật

```text
docs/spec/TASK-105D-DATA-CONTRACT.md   §4.6 — mệnh đề "từ điển đóng", bảng ví
                                       dụ 13 dòng, và điều bên tiêu thụ được
                                       phép dựa vào
PROJECT/PROJECT_DECISIONS.md           DEC-205 MỚI (thay DEC-204 §3, §4);
                                       DEC-204 được gắn con trỏ thay thế,
                                       nội dung GIỮ NGUYÊN VĂN
docs/reviews/R5-1-INDEPENDENT-REVIEW-  gắn trạng thái sau repair; nội dung
RECORD.md                              review GIỮ NGUYÊN VĂN
docs/tasks/R5-1-REPAIR-1-...           task + checklist + ACCEPTED_RISK
PROJECT/REVIEW_BUDGET_LEDGER.md        tiêu 1 cycle → 2 allowed / 2 used / 0
PROJECT/PROJECT_PROGRESS.md            canonical current state
```

Không file lịch sử nào bị sửa để che sai khác. `DEC-204` và bản ghi review giữ
nguyên văn; điều đổi được ghi ở nơi mới, có con trỏ hai chiều.

---

## 7. Rollback

```text
Tracking   revert 11a199b → quay lại luật hình dạng của R5.1. Reports không
           cần đổi gì: hợp đồng cùng hình dạng, chỉ tập giá trị rộng lại.
Reports    revert commit repair → mất 2 bài test và các phép đo smoke mới;
           mã sản phẩm không đụng tới nên không có gì để hoàn.
Dữ liệu    KHÔNG có gì để rollback: không migration, không bảng, không cột,
           không file capture nào bị ghi đè (INV-11).
Thứ tự     Không ràng buộc. Revert một phía cũng an toàn.
```

---

## 8. Trạng thái cuối

```text
Trạng thái task          IMPLEMENTED
CHECK-R51R1-01..16       PASS (E1)
CHECK-R51R1-17           NOT_TESTED — Independent Review vòng 2
CHECK-R51-26             NOT_TESTED — Owner nghiệm thu production
Merge / deploy / R6      KHÔNG thực hiện
Repair cycle tiêu        1 → lineage R5 còn 0 remaining
```

Phiên này **không** tự đánh dấu Independent Review hay Owner Acceptance.

**Cảnh báo ngân sách:** lineage `R5` đã hết repair cycle. Nếu vòng review kế
tiếp lại ra `REPAIR_REQUIRED`, phải escalate theo
`governance/core/ESCALATION_PROTOCOL.md`, không được mở cycle thứ ba.

### Exact HEAD cuối phiên

```text
Tracking  11a199b222ed1771558cefcdf664aad9de64cfa9
          nhánh claude/r5-1-repair-1-taxonomy — commit MÃ, không có commit
          tài liệu nào sau nó ở repo này.

Reports   e993fb5a4a8a655d3cc02a680ea7470a1b5f6788
          nhánh claude/r5-1-repair-1-taxonomy — HEAD GỒM CẢ TÀI LIỆU, và nó
          mang cả ba lớp lịch sử: implementation R5.1 (2c2c139), tài liệu
          Independent Review (dd7cd04), và repair này. Vòng review kế tiếp
          đọc SHA ở đây.
```

Hai commit của phiên:

```text
Tracking  11a199b  R5.1 REPAIR-1 §4: category_label chọn từ từ điển đóng
Reports   e993fb5  R5.1 REPAIR-1: hợp đồng từ điển đóng, DEC-205, bàn giao S140
```

Cả hai nhánh đã `git push -u origin claude/r5-1-repair-1-taxonomy`.
KHÔNG mở pull request, KHÔNG merge, KHÔNG deploy, KHÔNG làm `R6`.

### Ghi chú môi trường

Container không có sẵn phụ thuộc Python của Reports; phiên dùng lại `.venv`
đã dựng ở `S138` (`pip install -e ".[dev,web,storage,history]"`). `.venv/` nằm
trong `.gitignore` và KHÔNG được commit.
