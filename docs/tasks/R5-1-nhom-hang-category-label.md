# R5.1 — Nhóm hàng (`category_label`) trong hợp đồng metadata sản phẩm

## Metadata

Status:
IMPLEMENTED

Current Status Reason:
Toàn bộ brief `R5.1` đã triển khai trên CẢ HAI repo. Không migration, không
schema mới, không bảng mới, không product key mới — `category_label` là một
trường TÙY CHỌN thêm vào đúng hợp đồng catalog mà `R5` đang dùng.

`CHECK-R51-01` … `CHECK-R51-24` PASS (E1, bằng chứng nguyên văn ở
`docs/sessions/S138-r51-nhom-hang.md`).

`CHECK-R51-25` (Independent Review) — `PASS` (E1) từ 2026-09-09. Vòng review
độc lập đầu tiên chạy trên exact HEAD `2c2c139` (Reports) + `39528ee`
(Tracking) và kết luận **`ACCEPT_WITH_RECORDED_RISK`**: 0 finding
`REPAIR_REQUIRED`, 2 `ACCEPTED_RISK` mới (`AR-R5.1-05`, `AR-R5.1-06`), 1 đính
chính tài liệu (`COR-R5.1-01`). Bằng chứng nguyên văn:
`docs/reviews/R5-1-INDEPENDENT-REVIEW-RECORD.md`. Phiên review KHÔNG tiêu
repair cycle nào.

`CHECK-R51-26` (Owner nghiệm thu trên production) — `NOT_TESTED` →
`ACCEPTED_BY_OWNER_VERBAL` (`DEC-219`, 2026-09-10). Owner tự xác nhận bằng
lời trực tiếp, không đính kèm bằng chứng E1/E2 cụ thể trong repo — không
phiên kỹ thuật nào tự đóng check này.

Phase:
PHASE-01 — Engine tính toán

Task Mode:
MAJOR

Primary Agent Tier:
C

Escalation Tier:
C

Difficulty:
2/5

Risk:
2/5

Blast Radius:
2/5 (`V4.1` §4 — chấm theo failure path. Failure path của R5.1 là
`cat của Tracking → category_label → bản chiếu hiển thị → MỘT ô trên bảng kê
nhân viên`, và nó DỪNG ở đó. Không đường nào của R5.1 chạm vào tập dòng được
cộng, vào MIN theo ngày bán, vào giá nhập tay, vào lợi nhuận hay vào vân tay
chốt kỳ — `CHECK-R51-14`/`CHECK-R51-15` đo đúng điều đó bằng cách ĐỔI nhóm
hàng rồi cộng lại tiền. Nó KHÔNG phải 1/5 vì hai lý do thật: một nhãn nhóm
hàng gắn nhầm mã sẽ dẫn người đọc tới kết luận sai về cơ cấu hàng bán, và
`cat` là chuỗi người dùng gõ tay nên nó là một đường RÒ DỮ LIỆU tiềm năng ra
khỏi Tracking.)

Effective Risk:
LOW (Blast Radius quyết định — `V4.1` §4.1)

Project Profile:
PRODUCT

Review Budget lineage:
`R5.1` thuộc root lineage `R5` (nó mở rộng đúng hợp đồng và đúng module mà
`R5` dựng ra, không phải một root task mới). Xem
`PROJECT/REVIEW_BUDGET_LEDGER.md` → "Root Task: R5". Không repair cycle nào
bị tiêu trong phiên triển khai này.

ADR:
`docs/adr/ADR-111-absence-effective-data-imei-scope-and-brand-authority.md`
§3 — thẩm quyền thương hiệu thuộc về Tracking. R5.1 KHÔNG mở một ADR mới:
nhóm hàng đến từ ĐÚNG trường `board/<mã>/cat` mà `ADR-111` §3 đã lấy làm căn
cứ đặt thẩm quyền ở Tracking, nên nó thừa hưởng nguyên vẹn quyết định ấy chứ
không đặt ra một quyết định kiến trúc thứ hai. Quyết định chiến thuật:
`PROJECT/PROJECT_DECISIONS.md` → `DEC-204`.

Owner Authority:
Brief `R5.1 — bổ sung category_label vào hợp đồng metadata sản phẩm Tracking
→ Reports`. Nền đã merge: Reports `claude/extract-upload-repo-gq2ws4` @
`3b35b7acee2159b007c4398045f4b6f6843f7de8` (chứa R5 merge `f5e4e76`);
Tracking `main` @ `918183c48c4d4c45b5ce1348d734e073e537c6e4` (chứa R5 §5
`918183c`).

---

## 1. Vì sao R5.1 tồn tại

`R5 §5` đóng một nửa của cùng một khoảng cách: sau khi Owner phân loại xong
một dòng, màn hình đã nói được *model gì* và *của hãng nào*. Nó vẫn chưa nói
được *đó là loại hàng gì* — và đó là câu hỏi đầu tiên mọi phép đọc cơ cấu
hàng bán phải trả lời.

Bằng chứng cho câu ấy đã có sẵn và đã nằm đúng chỗ: `board/<mã>/cat` là ngành
hàng do người của Tracking tự tay xếp qua `pickCat()`. Nó chính là trường mà
`ADR-111` §3 đã lấy làm căn cứ để đặt thẩm quyền thương hiệu ở Tracking. Nên
R5.1 không phải một quyết định kiến trúc mới; nó là việc rút nốt cái nghĩa
còn lại của một trường đã có thẩm quyền rõ ràng.

Điều R5.1 phải cẩn thận hơn `R5 §5` đúng một chỗ, và cả brief xoay quanh nó:

> `brand` đi ra từ một DANH SÁCH ĐÓNG (`HANG`), nên thứ qua ranh giới luôn là
> một trong ba mươi mấy từ đã biết. `category_label` đi ra từ `cat` — một
> chuỗi NGƯỜI DÙNG GÕ TAY qua ô "+ Ngành hàng mới...".

Không có gì ngăn một dòng `cat` mang tên NCC, một con số giá, một ghi chú hay
một đường link. Chiếu `cat` ra ngoài sau khi chỉ cắt tên hãng là **tin rằng
chuỗi ấy luôn sạch**. R5.1 thay niềm tin đó bằng một phép kiểm (`HINH_NHOM`).

---

## 2. Ba câu hỏi khác nhau, ba trường khác nhau

```text
brand            ai LÀM RA mặt hàng này      "Samsung"
model_label      đúng DÒNG MÁY nào           "55Q6FA"
category_label   LOẠI HÀNG HOÁ gì            "Tivi"
```

`category_label` **không bao giờ** chứa tên hãng, model, nhà cung cấp, giá
hay tồn. "Tivi Samsung" là một `cat` nội bộ của Tracking, KHÔNG phải một
`category_label` hợp lệ.

`null` nghĩa là **chưa đủ căn cứ**, không phải "chưa kịp làm".

---

## 3. Scope Lock

**ĐƯỢC LÀM**

Tracking:
- `nhomCua()` + hai hằng `NHOM_SENTINEL`/`HINH_NHOM` trong `src/index.js`.
- Trường thứ năm `category_label` trong danh sách trắng của `chieuBoard()`.
- Bộ kiểm `kiem/nhom-hang.js`; cập nhật hai bộ kiểm đang canh hình dạng cũ.
- Producer fixture xuyên repo `kiem/smoke/sinh-catalog-reports.mjs`.

Reports:
- Trường tùy chọn `category_label` trên `TrackingCatalogRow`, trong capture
  tool và trong loader — CÙNG vòng lặp trường tùy chọn mà `R5` đã dựng.
- Bản chiếu hiển thị `catalog_display` mang thêm trường thứ ba; `category_of`.
- `_catalog_labels()` và `_line_row()` chở nó tới tầng trình bày.
- MỘT cột đọc-thuần "Nhóm hàng" trên bảng kê nhân viên, dưới ĐÚNG nút ẩn/hiện
  đã có.
- `tests/test_r51_category_label.py`, `scripts/r51_crossrepo_smoke.py`.
- Cập nhật `docs/spec/TASK-105D-DATA-CONTRACT.md` §4.4 + §4.6.

**KHÔNG ĐƯỢC LÀM** (brief §9, và mỗi dòng dưới đây đã được giữ)

- Dashboard R6, Basket/cross-sell, bộ lọc ngày mới, KPI theo nhóm hàng.
- Giao diện sửa nhóm hàng trong Reports (sửa xảy ra bên Tracking).
- Taxonomy toàn diện cho mọi mã hiếm; gộp tên đồng nghĩa chưa có thẩm quyền.
- Backfill lịch sử catalog cũ.
- Đổi giá, MIN, lợi nhuận, product key, hay bất kỳ con số nào.
- Endpoint thứ hai; store/resolver thứ hai; migration.
- Merge, deploy.

---

## 4. Quy tắc chuẩn hoá đã triển khai (brief §3)

Nguồn DUY NHẤT là `cat`. `name` KHÔNG được đọc để suy nhóm hàng.

```text
1  cat rỗng/vắng                              ⟹ null
2  cat là sentinel quy trình
   ("Chưa phân loại", "Không sử dụng")        ⟹ null
3  cat mang tên hãng nhưng hangCua() không
   khẳng định được (hai hãng cùng dòng)       ⟹ null
4  cat mang ĐÚNG một hãng đã khẳng định       ⟹ cắt nguyên TỪ tên hãng đó
5  còn sót một tên hãng khác sau khi cắt      ⟹ null
6  phần còn lại không lọt HINH_NHOM
   (1–4 từ, chỉ chữ cái, ≤ 40 ký tự)          ⟹ null
7  còn lại                                    ⟹ phần còn lại, GIỮ NGUYÊN
                                                 hoa/thường và dấu tiếng Việt
```

Ghép hãng là ghép **nguyên từ**, không phải chứa chuỗi con — "SHARP" trong
"SHARPNESS" và "GREE" trong "GREEN" không bị cắt (`kiem/nhom-hang.js` §5).

Bảng ánh xạ DUY NHẤT mà R5.1 cho phép là hai sentinel ở quy tắc 2, và chúng
là thẩm quyền Tracking ĐÃ CÓ TỪ TRƯỚC (`public/index.html`: `CAT_JUNK` và giá
trị `loadBoard()` ghi cho mã mới). Gộp "Tivi" với "TV", "Tủ lạnh" với "Tủ
mát" — Tracking chưa có thẩm quyền nào, nên R5.1 không làm.

---

## 5. Checklist

| Check | Nội dung | Trạng thái | Evidence Level |
|---|---|---|---|
| `CHECK-R51-01` | Mã nhóm "Tivi Samsung" + brand Samsung ⟹ `category_label = "Tivi"` | PASS | E1 |
| `CHECK-R51-02` | Mã nhóm "Tủ lạnh Samsung" ⟹ `category_label = "Tủ lạnh"` | PASS | E1 |
| `CHECK-R51-03` | Thiếu/không chắc chắn ⟹ `null`, không đoán (7 trường hợp) | PASS | E1 |
| `CHECK-R51-04` | KHÔNG suy nhóm hàng từ `name` — tên hàng nói "Tivi" mà `cat` chưa xếp vẫn `null` | PASS | E1 |
| `CHECK-R51-05` | Đổi `cat` ⟹ payload đổi ⟹ `content_hash` Reports đổi | PASS | E1 |
| `CHECK-R51-06` | Response KHÔNG rò `cat` thô, giá, tồn, NCC, ghi chú, link | PASS | E1 |
| `CHECK-R51-07` | Danh sách trắng hình dạng chặn `cat` bẩn (7 chuỗi gõ tay thật) | PASS | E1 |
| `CHECK-R51-08` | Hợp đồng cũ `name`/`alt`/`model_label`/`brand` giữ nguyên nghĩa | PASS | E1 |
| `CHECK-R51-09` | Tracking `npm test` + `npm run build` xanh | PASS | E1 |
| `CHECK-R51-10` | Reports đọc artifact R5 CŨ (không có trường) ⟹ `None`, không lỗi | PASS | E1 |
| `CHECK-R51-11` | Reports đọc artifact MỚI có `category_label` | PASS | E1 |
| `CHECK-R51-12` | Nâng cấp hợp đồng KHÔNG đổi `content_hash` của dòng vốn `null` | PASS | E1 |
| `CHECK-R51-13` | CONFIRMED mapping nhận đúng nhóm hàng của `tracking_code` của nó | PASS | E1 |
| `CHECK-R51-14` | Conflict / OUT_OF_CATALOG / chưa phân loại KHÔNG tự nhận nhóm hàng | PASS | E1 |
| `CHECK-R51-15` | Nhóm hàng KHÔNG rò từ mã này sang mã khác | PASS | E1 |
| `CHECK-R51-16` | Đổi nhóm hàng: nhãn đổi, `product_key` KHÔNG đổi | PASS | E1 |
| `CHECK-R51-17` | Đổi nhóm hàng: doanh thu, giá nhập, lợi nhuận, DS quy đổi KHÔNG đổi | PASS | E1 |
| `CHECK-R51-18` | Route web thật chở nhóm hàng từ capture tới bảng kê | PASS | E1 |
| `CHECK-R51-19` | Refresh và `create_app()` mới vẫn đọc đúng | PASS | E1 |
| `CHECK-R51-20` | Mất bản chiếu ⟹ ô trống, tiền không đổi (nói ÍT ĐI, không nói SAI) | PASS | E1 |
| `CHECK-R51-21` | Không nhánh nào suy nhóm hàng từ `product_raw` (đọc mã nguồn) | PASS | E1 |
| `CHECK-R51-22` | Nhóm hàng KHÔNG tham gia identity matching | PASS | E1 |
| `CHECK-R51-23` | Smoke xuyên hai repo bằng producer THẬT của Tracking | PASS | E1 |
| `CHECK-R51-24` | Reports full `pytest` xanh, không hồi quy | PASS | E1 |
| `CHECK-R51-25` | Independent Review | PASS | E1 |
| `CHECK-R51-26` | Owner nghiệm thu trên production | ACCEPTED_BY_OWNER_VERBAL | `DEC-219` |

Bằng chứng nguyên văn: `docs/sessions/S138-r51-nhom-hang.md` §4.

---

## 6. Rủi ro đã chấp nhận

`ACCEPTED_RISK R5.1-01` — **Mã chưa xếp ngành hàng ra `null`.** Một mã mà
Tracking chưa xếp `cat` (hoặc còn ở "Chưa phân loại") hiện ô trống, kể cả khi
tên hàng nói rõ nó là gì. Tác động nhỏ và **dễ phát hiện**: nhân viên nhìn
thấy ngay một ô trống cạnh một dòng đã phân loại. Cách sửa nằm ở đúng nơi có
thẩm quyền — xếp ngành hàng bên Tracking, và lần capture kế tiếp chở giá trị
mới sang mà không ai phải phân loại lại mã sản phẩm.

`ACCEPTED_RISK R5.1-02` — **Nhóm hàng có chữ số trong tên ra `null`.**
`HINH_NHOM` loại chữ số và dấu câu có chủ đích: chúng là dấu hiệu của giá
("5.000k"), mã ("55Q6FA"), ghi chú và link. Cái giá là một nhóm hàng thật như
"Tivi 4K" sẽ ra `null`. Hiếm, hậu quả là một ô trống, và người xếp ngành hàng
đổi được tên nhóm bất cứ lúc nào. Đánh đổi ngược lại — nới luật để "bắt được
nhiều hơn" — mở đúng đường rò mà `§4.5` của brief cấm.

`ACCEPTED_RISK R5.1-03` — **Tên đồng nghĩa KHÔNG được gộp.** "Tivi" và "TV"
đi ra như hai nhóm khác nhau nếu người xếp ngành hàng gõ hai kiểu. R5.1 không
gộp vì Tracking chưa có cấu hình/thẩm quyền nào cho việc ấy, và `§3.3` cấm
phát minh taxonomy mới. Phát hiện được bằng mắt trên chính bảng chọn ngành
hàng của Tracking (`pickCat()` hiện số mã của từng nhóm).

`ACCEPTED_RISK R5.1-05` — **`cat` bẩn nhưng ĐÚNG HÌNH DẠNG đi ra nguyên
văn.** Ghi bởi Independent Review (2026-09-09). `HINH_NHOM` chặn ô nhiễm mang
chữ số, dấu câu, quá 4 từ hay quá 40 ký tự, nhưng KHÔNG phân biệt được ô
nhiễm NGỮ NGHĨA gồm toàn chữ cái: `cat = "Tivi kho anh Ba"`, `"Tủ lạnh nợ
NCC"`, `"Tivi Đất Việt"` đi ra nguyên văn thành `category_label`. Đường vào
là thật — `setCat()` ghi thẳng chuỗi `prompt()` vào `board/<mã>/cat` không
qua phép kiểm nào. Chấp nhận vì hậu quả dừng ở MỘT ô nhãn trên cột mặc định
ẨN: không đổi mapping, product_key, doanh thu, giá nhập, lợi nhuận, coverage
hay vân tay chốt kỳ; giá vốn/giá chốt/tồn/NCC/note/link vẫn KHÔNG đi ra;
nhận ra ngay bằng mắt và sửa được bên Tracking. Không có phép sửa nào nằm
trong kiến trúc đã duyệt — một luật HÌNH DẠNG không thể phân biệt "Tủ lạnh"
với "Tivi kho anh Ba", còn danh sách trắng theo GIÁ TRỊ đã bị `DEC-204` §3
loại; siết thật sự đòi Owner mở lại `DEC-204`.

`ACCEPTED_RISK R5.1-06` — **Hãng ngoài `HANG` ở lại trong nhãn nhóm hàng.**
Ghi bởi Independent Review (2026-09-09). `HANG` là danh sách ĐÓNG 39 hãng, nên
`cat = "Tivi Vsmart"` ra `"Tivi Vsmart"`. Hợp đồng §4.6 nói `category_label`
"không bao giờ chứa tên hãng" — với hãng ngoài danh sách, câu ấy mạnh hơn
hành vi thật (`COR-R5.1-01`). Không đổi tiền, không đổi mapping; `brand` của
chính dòng đó là `None` nên màn hình không tự mâu thuẫn. Sửa đúng chỗ: thêm
một dòng vào `HANG` bên Tracking.

`ACCEPTED_RISK R5.1-04` — **Bản chiếu hiển thị sống trên đĩa ephemeral.** Mất
file (deploy mới) ⟹ màn hình hiện ô trống cho tới lần pull kế tiếp. Đây là
rủi ro `R5` đã ghi và chấp nhận cho `model_label`/`brand`; `category_label`
thừa hưởng nguyên vẹn, và `CHECK-R51-20` chứng minh cái giá là một màn hình
nói ÍT ĐI, không phải một màn hình nói SAI.
