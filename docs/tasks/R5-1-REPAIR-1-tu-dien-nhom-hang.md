# R5.1 REPAIR-1 — khoá `category_label` thành từ điển đóng an toàn cho R6

## Metadata

Status:
IMPLEMENTED

Current Status Reason:
Toàn bộ brief `R5.1 REPAIR-1` đã triển khai trên CẢ HAI repo. `category_label`
không còn được cắt ra từ `cat`; nó được CHỌN từ một từ điển đóng trong
`src/index.js` của Tracking. Reports KHÔNG đổi một dòng mã sản phẩm nào — nó
là bên tiêu thụ, và điều đó nay được canh bằng test.

`CHECK-R51R1-01` … `CHECK-R51R1-16` PASS (E1, bằng chứng nguyên văn ở
`docs/sessions/S140-r51-repair-1.md`).

`CHECK-R51R1-17` (Independent Review vòng 2) `PASS` (E1) — chạy ở `S141`
(2026-09-09), kết luận `ACCEPT_WITH_RECORDED_RISK`, **0 finding
`REPAIR_REQUIRED`**, không tiêu repair cycle nào. Bằng chứng:
`docs/reviews/R5-1-REPAIR-1-INDEPENDENT-REVIEW-2-RECORD.md`.

`CHECK-R51-26` (Owner nghiệm thu production) VẪN `NOT_TESTED`. Task vì thế
GIỮ `IMPLEMENTED`, KHÔNG phải `DONE`: Exit Criteria còn một check REQUIRED
chưa chạy, và nghiệm thu ấy là việc của Owner — không phiên nào tự đóng.

Vòng review 2 để lại 2 `ACCEPTED_RISK` mới (`R5.1R1-04`, `R5.1R1-05`), 2 đính
chính tài liệu (`COR-R5.1R1-01`, `COR-R5.1R1-02`) và một
`OWNER_DECISION_REQUIRED` về alias taxonomy — xem mục 6 và mục 7.

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
2/5 (`V4.1` §4 — chấm theo failure path, GIỮ NGUYÊN mức của `R5.1`. Failure
path vẫn là `cat → category_label → bản chiếu → MỘT ô trên bảng kê nhân
viên`, và repair này làm nó HẸP HƠN chứ không rộng ra: tập giá trị có thể đi
qua ranh giới giảm từ "mọi chuỗi lọt luật hình dạng" xuống "13 nhãn đã biết".
Không đường nào chạm tập dòng được cộng, MIN theo ngày bán, giá nhập tay, lợi
nhuận hay vân tay chốt kỳ.)

Effective Risk:
LOW (Blast Radius quyết định — `V4.1` §4.1)

Project Profile:
PRODUCT

Review Budget lineage:
`R5` (`R5.1` và mọi repair của nó thuộc lineage ấy — xem
`PROJECT/REVIEW_BUDGET_LEDGER.md`). Repair cycle này TIÊU cycle cuối cùng của
lineage: số dư sau phiên là `2 allowed / 2 used / 0 remaining`.

ADR:
Không mở ADR mới. `ADR-111` §3 (thẩm quyền metadata sản phẩm thuộc Tracking)
KHÔNG đổi — repair này đổi *cách* Tracking dẫn xuất một trường, không đổi *ai*
có thẩm quyền. Quyết định chiến thuật: `DEC-205` (thay thế `DEC-204` §3, §4).

Owner Authority:
Brief `R5.1 REPAIR-1 — khóa category_label thành taxonomy an toàn cho R6` §1
(điều chỉnh kết luận Independent Review thành `REPAIR_REQUIRED`) và §4 (bảng
ví dụ chuẩn). Base: Reports `dd7cd0461d3d5c8deff9465069bbd2cd0bf55120`
(gồm cả implementation `2c2c139` và tài liệu review), Tracking
`39528ee5260f4cd5a6bdf92c7f020ad5ecbda362`.

---

## 1. Finding được nâng mức, và vì sao

Independent Review (`S139`) xếp `AR-R5.1-05` là `ACCEPTED_RISK` với một lập
luận đúng **cho hệ thống tại thời điểm đó**: hậu quả dừng ở một ô nhãn trên
một cột mặc định ẩn, không đổi một đồng nào.

Điều lập luận ấy chưa tính tới là `R6` sắp dùng chính trường này làm **khoá
gộp** doanh thu và Basket. Khi đó:

```text
trước R6   "Tivi kho anh Ba"  là một ô nhãn xấu trên bảng kê
từ R6      "Tivi kho anh Ba"  là một NHÓM HÀNG GIẢ, đứng ngang hàng với
                              "Tivi" trong báo cáo cơ cấu
```

Tổng tiền của công ty vẫn đúng — và đó chính là điều làm nó nguy hiểm: không
con số nào lệch để báo động, chỉ có một bảng cơ cấu sai mà trông hoàn toàn
bình thường.

Chính bản ghi review đã chỉ ra rằng phép sửa thật "đòi mở lại `DEC-204` —
việc của Owner, không phải của một repair cycle". Owner đã mở lại. Đây không
phải một lần review sai; đây là lần mở lại đó.

---

## 2. Vì sao luật hình dạng không thể sửa được bằng cách siết chặt

`HINH_NHOM` chặn ô nhiễm mang **chữ số, dấu câu, độ dài**. Ô nhiễm nguy hiểm
lại gồm toàn chữ cái:

```text
"Tủ lạnh"          2 từ, toàn chữ cái   ⟹ nhóm hàng THẬT
"Tivi kho anh Ba"  4 từ, toàn chữ cái   ⟹ ghi chú kho
```

Không tham số nào của một luật hình dạng phân biệt được hai dòng ấy. Siết số
từ xuống 2 sẽ giết "Nồi cơm điện" và "Bình nóng lạnh". Vấn đề không nằm ở độ
chặt — nó nằm ở chỗ **đầu ra được dẫn xuất từ chuỗi người dùng gõ**.

Từ điển đóng đổi LOẠI bảo đảm, không chỉ đổi độ chặt:

```text
đầu ra ∈ NHOM ∪ {null}
⟺ không một ký tự nào người dùng gõ rời khỏi Tracking bằng trường này
```

---

## 3. Scope Lock

**ĐƯỢC LÀM**

Tracking:
- Thay `HINH_NHOM` bằng từ điển đóng `NHOM` + tra cứu `NHOM_TRA`/`HANG_TRA`.
- Viết lại `nhomCua()` theo luật "phân tích trọn vẹn".
- Thêm `Vsmart` vào `HANG` (brief §4 đòi).
- Viết lại `kiem/nhom-hang.js`; mở rộng producer xuyên repo.

Reports:
- KHÔNG đổi mã sản phẩm. Hai test MỚI canh ranh giới thẩm quyền.
- Mở rộng `scripts/r51_crossrepo_smoke.py` cho các trường hợp repair.
- Cập nhật `docs/spec/TASK-105D-DATA-CONTRACT.md` §4.6; `DEC-205`; task này;
  bàn giao; ledger; trạng thái check trong bản ghi review.

**KHÔNG ĐƯỢC LÀM**

- `R6`, Basket, KPI theo nhóm hàng, bộ lọc mới.
- Giao diện sửa nhóm hàng hay sửa từ điển trong Reports.
- Một bản sao từ điển ở phía Reports (đó là thẩm quyền thứ hai).
- Backfill lịch sử catalog; migration; đổi giá/MIN/lợi nhuận/product key.
- Sửa `DEC-204` để che sai khác; sửa `governance/core/V4_1_POLICY_FREEZE.md`.
- Merge, deploy.

---

## 4. Luật mới

```text
0  cat rỗng / sentinel quy trình                       ⟹ null
1  tìm MỌI đoạn từ liên tiếp khớp NHOM (đã chuanSo)
2  không đoạn nào                                      ⟹ null
3  đoạn DÀI NHẤT thắng ("Nồi cơm điện" ≻ "Nồi cơm")
4  hai nhãn canonical KHÁC NHAU cùng dài nhất          ⟹ null
5  mọi từ CÒN LẠI phải nằm trong HANG                  ⟹ nếu không, null
6  trả về nhãn CANONICAL của từ điển, không phải lát cắt của cat
```

Bước 5 là chỗ "Tivi kho anh Ba", "Tủ lạnh nợ NCC", "Tivi Đất Việt",
"Tivi hàng gửi" và "Tivi 4K" cùng dừng lại — vì một lý do, không phải năm
luật riêng.

Bước 6 là chỗ bảo đảm được sinh ra: đầu ra không đến từ đầu vào.

---

## 5. Checklist

| Check | Nội dung | Trạng thái | Evidence Level |
|---|---|---|---|
| `CHECK-R51R1-01` | Bảng ví dụ §4 của brief đúng nguyên văn cả 10 dòng | PASS | E1 |
| `CHECK-R51R1-02` | `AR-R5.1-05` đóng — 5 chuỗi bẩn ngữ nghĩa đều `null` | PASS | E1 |
| `CHECK-R51R1-03` | `AR-R5.1-06` đóng — hãng ngoài `HANG` không nằm lại trong nhãn | PASS | E1 |
| `CHECK-R51R1-04` | Đối chứng: cùng tiền tố KHÔNG có đuôi bẩn thì VẪN ra nhãn | PASS | E1 |
| `CHECK-R51R1-05` | Ném rác vào: mọi đầu ra ∈ từ điển ∪ {null} | PASS | E1 |
| `CHECK-R51R1-06` | Đối chứng: luật CŨ cho "Tivi kho anh Ba" đi ra nguyên văn | PASS | E1 |
| `CHECK-R51R1-07` | Đoạn dài nhất thắng; hai nhóm khác nhau ⟹ `null` | PASS | E1 |
| `CHECK-R51R1-08` | Canonical hoá: "Điều hòa"/"Điều hoà"/"Máy lạnh" về một nhãn | PASS | E1 |
| `CHECK-R51R1-09` | Mọi mục từ điển (và mọi cách viết) đều tra được, không mục chết | PASS | E1 |
| `CHECK-R51R1-10` | `Vsmart` vào `HANG`; "Tivi Vsmart" ⟹ brand Vsmart + "Tivi" | PASS | E1 |
| `CHECK-R51R1-11` | Không suy từ `name`; sentinel/rỗng ⟹ `null` | PASS | E1 |
| `CHECK-R51R1-12` | Hợp đồng cũ `name`/`alt`/`model_label`/`brand` giữ nguyên nghĩa | PASS | E1 |
| `CHECK-R51R1-13` | Không rò `cat` thô, ghi chú, NCC, giá, tồn, link | PASS | E1 |
| `CHECK-R51R1-14` | Reports KHÔNG giữ bản sao từ điển (canh bằng cấu trúc) | PASS | E1 |
| `CHECK-R51R1-15` | Smoke xuyên hai repo: mọi nhãn qua ranh giới ∈ từ điển đọc từ `src/index.js` | PASS | E1 |
| `CHECK-R51R1-16` | Tracking `npm test`/`build`; Reports full `pytest`; không hồi quy | PASS | E1 |
| `CHECK-R51R1-17` | Independent Review vòng 2 | PASS | E1 |
| `CHECK-R51-26` | Owner nghiệm thu trên production | NOT_TESTED | — |

Bằng chứng nguyên văn: `docs/sessions/S140-r51-repair-1.md` §4.

`CHECK-R51R1-17` chạy ở `S141` (2026-09-09) trên exact HEAD `11a199b`
(Tracking) + `83b1e07` (Reports), kết luận `ACCEPT_WITH_RECORDED_RISK` với
**0 finding `REPAIR_REQUIRED`** — nên phiên ấy KHÔNG tiêu repair cycle nào.
Bằng chứng: `docs/reviews/R5-1-REPAIR-1-INDEPENDENT-REVIEW-2-RECORD.md`,
`docs/sessions/S141-r51-repair-1-independent-review-2.md`.

`CHECK-R51-26` GIỮ `NOT_TESTED`: nghiệm thu production là việc của Owner, và
không phiên review nào được tự đánh dấu.

---

## 6. Rủi ro đã chấp nhận

`ACCEPTED_RISK R5.1R1-01` — **Độ phủ giảm.** Mọi `cat` mà từ điển chưa biết
nay ra `null`, kể cả những `cat` sạch sẽ mà luật cũ cho đi qua ("Bàn ủi
Philips" nếu "Bàn ủi" chưa có trong từ điển). Đây là đánh đổi CÓ CHỦ ĐÍCH và
đúng chiều: một ô trống là một câu hỏi cho người xếp ngành hàng, còn một nhóm
hàng giả là một câu trả lời sai trong báo cáo `R6`. Giảm nhẹ: đường mở rộng
rẻ (một dòng trong `NHOM`), và `CHECK-R51R1-09` bắt buộc mỗi mục thêm vào
phải tra được.

`ACCEPTED_RISK R5.1R1-02` — **Từ điển là artifact phải bảo trì.** `DEC-204`
§3 đã nêu đúng điểm này khi loại phương án danh sách trắng theo giá trị. Điều
đổi là ta nay biết cái giá của việc KHÔNG bảo trì nó. Không có cơ chế tự động
nào phát hiện "một ngành hàng mới xuất hiện bên Tracking mà từ điển chưa
biết"; nó hiện ra thành một ô trống, và người vận hành báo lại.

`ACCEPTED_RISK R5.1R1-03` — **Hãng ngoài `HANG` làm cả nhãn nhóm hàng biến
mất.** "Tủ lạnh Hòa Phát" ra `null` chứ không phải "Tủ lạnh", vì luật đòi
`cat` phân tích TRỌN VẸN. Bảo thủ hơn mức tối thiểu cần thiết, nhưng nới ra
("bỏ qua từ lạ nếu đã tìm được nhóm hàng") sẽ cho "Tivi kho anh Ba" ra "Tivi"
— tức mở lại đúng lỗ vừa vá. Sửa đúng chỗ: thêm hãng vào `HANG`.

`ACCEPTED_RISK R5.1R1-04` — **Nhắc lại cùng một nhóm trong `cat` ⟹ `null`.**
Ghi bởi Independent Review vòng 2 (`S141`). `cat = "Tivi TV"`, `"TV Tivi"`,
`"Máy lạnh Điều hoà"`, `"Nồi cơm Nồi cơm điện"` đều ra `null` dù nhóm hàng
không hề mơ hồ: hai đoạn khớp cùng độ dài trỏ về CÙNG một canonical, phép chọn
`nhat[0]` lấy đoạn đầu, và các từ của đoạn còn lại rơi xuống phép kiểm "mọi từ
còn lại phải là hãng". Hiếm (phải gõ hai cách gọi cùng một nhóm trong một ô),
chỉ giảm độ phủ, hiện rõ thành "—". Không tạo category giả, không rò dữ liệu,
không sai gộp `R6`.

`ACCEPTED_RISK R5.1R1-05` — **Ngành hàng GHÉP ⟹ `null`, và có ca THẬT.**
Ghi bởi `S141`. `"Máy giặt sấy"` và `"Máy giặt sấy LG"` ra `null`: từ điển có
`"Máy giặt"` và có `"Máy sấy"` nhưng không có mục ghép; đoạn dài nhất khớp là
`"Máy giặt"`, còn `"sấy"` không phải hãng. Đây là `R5.1R1-01` với một ca có
thật thay cho ví dụ giả định — đơn golden `BH62439` gồm `"Máy Giặt Sấy LG"`.
Quan trọng: nó hỏng theo hướng AN TOÀN — KHÔNG xếp nhầm một máy giặt sấy vào
bucket `"Máy giặt"`. Sửa đúng chỗ: thêm một dòng `['Máy giặt sấy', []]` vào
`NHOM` (việc của Owner/phiên sau, không phải của review).

`ACCEPTED_RISK R5.1-01` … `-04` của `R5.1` **giữ nguyên hiệu lực**, trừ
`AR-R5.1-03` (không gộp đồng nghĩa) nay đã ĐÓNG: từ điển chính là cấu hình
cho phép gộp, và "Máy lạnh"/"Điều hoà" đã gộp.

---

## 7. Đính chính và câu hỏi mở sau Independent Review vòng 2 (`S141`)

`COR-R5.1R1-01` — hai chú thích mô tả LUẬT CŨ còn lại trong mã sản phẩm
Reports, nay mâu thuẫn `DEC-205` và hợp đồng §4.6:
`app/web/catalog_display.py:17-18` và
`tools/tracking/capture_tracking_catalog.py:134-135` đều còn nói "lọc hình
dạng"/"danh sách trắng hình dạng". Chỉ là chú thích — 0 tác động hành vi, 0
test đổi. Phiên nào chạm mã Reports lần kế tiếp nên sửa; không mở phiên riêng.

`COR-R5.1R1-02` — bảng quan hệ của `DEC-205` ghi `DEC-204 §5 → GIỮ NGUYÊN`,
nhưng `§5` còn câu *"Gộp tên đồng nghĩa khác: KHÔNG làm"* mà `DEC-205` §4 đã
đảo. Lập luận đảo có tường minh ở `DEC-205` §4 và ở mục 6 trên — chỉ DÒNG TÓM
TẮT là thiếu chính xác. KHÔNG sửa `DEC-204` (artifact lịch sử).

`OWNER_DECISION_REQUIRED` — **alias taxonomy chưa có Owner xác nhận rõ trong
lịch sử.** `Máy lạnh → Điều hoà` có bằng chứng dữ liệu MẠNH nhưng thẩm quyền
Owner chỉ tồn tại dưới dạng lời dẫn brief của phiên triển khai. `TV → Tivi` có
bằng chứng YẾU (chỉ `Tracking/public/kpi-demo.js`, một cấu hình KPI chứ không
phải giá trị `cat`). `Ti vi → Tivi` **không có bằng chứng in-repo nào** và
không `CHECK` nào canh riêng. Đây là quyết định BUCKET BÁO CÁO, không phải
thay đổi tiền, và không thể tạo category giả hay rò dữ liệu — nhưng nên đóng
TRƯỚC khi `R6` dùng `category_label` làm khoá gộp.
