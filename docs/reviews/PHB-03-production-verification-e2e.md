# PHB-03 — Triển Khai Production + Kiểm Thử Thật (E2E)

**Loại:** Báo cáo triển khai + xác minh production
**Ngày:** 2026-09-04
**Phiên:** S118 — PHB-03 Production Deployment + Real E2E
**Nhánh làm việc:** `claude/phb-03-production-e2e-b8bsad`
**Bản được duyệt (candidate):** `d066d227da852b17a57d4a8492fa79c7fc7b2aff`

---

## 1. Kết luận

**PHB-03 CHƯA thể đóng là DONE.** Không phải vì mã nguồn có lỗi — mà vì
**phiên làm việc này không có đường mạng ra tới máy chủ thật**.

Nói cho gọn, có hai nửa công việc:

| Nửa việc | Ai làm được | Kết quả |
|---|---|---|
| **Chuẩn bị + kiểm tra trước khi lên** | Phiên này làm được hết | ✅ **ĐẠT TOÀN BỘ** |
| **Bấm deploy + mở web thật để kiểm** | **Chỉ chủ dự án làm được** | ⏳ **CHƯA LÀM ĐƯỢC** |

Cụ thể:

- Bản được duyệt **đúng y hệt** bản đã qua soát xét độc lập và qua kiểm toán
  vòng đời import — đã đối chiếu từng file, không lệch một dòng mã nào.
- Toàn bộ bài kiểm tự động **chạy lại và đạt đúng bằng con số đã ghi nhận**:
  **2.136 đạt / 11 bỏ qua** (toàn bộ), **74 đạt / 2 bỏ qua** (bài chuẩn vàng),
  **101 đạt** (đường tính toán production).
- Bước **nâng cấp cơ sở dữ liệu đã được diễn tập thật**, đi đúng từ trạng thái
  hiện tại của máy chủ (`0002_snapshots`) lên trạng thái mới
  (`0004_employee_attribution`): **thêm 3 bảng mới, KHÔNG xoá bảng nào, KHÔNG
  sửa bảng nào đang có**. Nghĩa là bước nâng cấp này **không thể** làm mất dữ
  liệu cũ.
- Nhánh chính thức (canonical) **đã được cập nhật** đến đúng bản được duyệt, để
  chủ dự án chỉ còn một việc: bấm Deploy.

Việc còn thiếu — và là việc **duy nhất** còn thiếu — là **chủ dự án bấm Deploy
trên Render rồi mở `reports.tinphatcrm.com` làm 8 bước kiểm ở mục 17**.

> **Vì sao phiên này không tự làm được?**
> Máy chạy phiên Claude này bị chặn ra ngoài internet theo chính sách. Đã thử
> thật và bị từ chối:
>
> ```
> reports.tinphatcrm.com:443   → CONNECT tunnel failed, response 403
> api.render.com:443           → không kết nối được
> dashboard.render.com:443     → không kết nối được
> price.tinphatcrm.com:443     → không kết nối được
> ```
>
> Đây **không phải lỗi mới**. Đúng lớp chặn đã ghi nhận ở các phiên S093, S110,
> S112 trước đây — và các lần đó cũng đúng theo cách này: phiên chuẩn bị, chủ
> dự án bấm và xác nhận.

**Không phát hiện lỗi production mới nào.** Không có gì chặn việc bấm Deploy.

---

## 2. Candidate nào đã được deploy?

Chưa deploy — nhưng bản **được phép** deploy đã chốt và đã đưa lên nhánh chính
thức:

```
Bản được duyệt        = d066d227da852b17a57d4a8492fa79c7fc7b2aff
Nhánh chính thức      = claude/extract-upload-repo-gq2ws4
```

**Bấm Deploy commit nào?** Bấm **commit trên cùng danh sách** (mới nhất) của
nhánh `claude/extract-upload-repo-gq2ws4`. Không cần đi tìm `d066d22`.

**Bảo đảm:** mọi commit trên nhánh chính thức **từ `d066d22` trở về sau** đều có
**mã chạy giống hệt** bản được duyệt — các commit sau đó **chỉ thêm tài liệu**.
Nên bấm cái mới nhất là an toàn, và không phải dò số.

### Đã kiểm rằng đây đúng là bản đã được soát xét

Ba nhánh khác nhau từng chạm vào PHB-03. Đã so từng file giữa chúng:

| So sánh | Kết quả |
|---|---|
| Bản duyệt ↔ nhánh soát xét độc lập lần 2 (`5bdd838`) | **Không lệch một dòng mã nào** |
| Bản duyệt ↔ nhánh kiểm toán import (`c02d42a`) | **Không lệch một dòng mã nào** (nhánh kia chỉ thêm đúng 1 file báo cáo) |

Nói cách khác: cái được soát xét, cái được kiểm toán, và cái sắp deploy — **là
cùng một thứ**.

### Phiên này có thêm gì vào không?

Có, nhưng **chỉ là giấy tờ, không phải mã chạy**:

1. Ba báo cáo cũ vốn nằm rải rác ở các nhánh khác, nay gom về nhánh chính thức
   (báo cáo soát xét lần 2, báo cáo kiểm toán import, báo cáo phân loại lý do
   PENDING).
2. Chính báo cáo bạn đang đọc.
3. Cập nhật sổ tiến độ dự án.

**Đã kiểm bằng máy: phần mã chạy thật (`app/`, `tools/`, `config/`,
`Dockerfile`, `render.yaml`, `alembic.ini`, `pyproject.toml`) giữa bản được
duyệt và bản trên nhánh chính thức — LỆCH BẰNG KHÔNG.** Không có một dòng mã
nào bị sửa sau soát xét.

---

## 3. Production trước và sau deploy

```
Bản production ĐANG chạy      = KHÔNG QUAN SÁT ĐƯỢC từ phiên này (không có mạng)
Bản đã được chủ dự án nghiệm  = 1a011ee66f9e2b2ffee4d04f6864bfb0eeb45948 (phiên S111)
   thu lần gần nhất
Nhánh chính thức trước phiên  = eaa3fdeb4ffdfd2d5772314ac24cf8a1273cc67e
Bản để quay lui nếu hỏng      = eaa3fdeb4ffdfd2d5772314ac24cf8a1273cc67e
Bản sau khi deploy            = CHƯA CÓ — chờ chủ dự án bấm
```

### Vì sao chắc rằng "quay lui về `eaa3fde`" là an toàn?

Đã kiểm: giữa bản chủ dự án nghiệm thu lần gần nhất (`1a011ee`) và nhánh chính
thức trước phiên này (`eaa3fde`), **phần mã chạy lệch bằng không** — ba commit
ở giữa chỉ sửa tài liệu.

Nghĩa là: `eaa3fde` **chính là** cái đang chạy trên máy chủ, chỉ khác phần giấy
tờ. Quay lui về nó là quay về đúng trạng thái chủ dự án đã nghiệm thu và đang
dùng hằng ngày.

---

## 4. Migration có thành công không?

```
MIGRATION (trên production) = CHƯA CHẠY — chờ deploy
MIGRATION (diễn tập thật)   = ĐẠT
```

### Điều quan trọng: máy chủ tự nâng cấp, không cần ai gõ lệnh

Lệnh khởi động của máy chủ là:

```
alembic upgrade head && gunicorn ... app.web.wsgi:application
```

Đọc là: **nâng cấp cơ sở dữ liệu xong xuôi rồi mới mở cổng cho người dùng vào.**
Nếu nâng cấp hỏng, web **không lên** — chứ không lên nửa vời rồi hiện số sai.
Đây là điều tốt: hỏng thì thấy ngay, không âm thầm.

### Một điểm cần nói rõ: có HAI bước nâng cấp, không phải một

Chỉ thị ban đầu ghi PHB-03 có migration `0004_employee_attribution`. Kiểm lại
thì máy chủ hiện đang ở `0002_snapshots`, nên lần deploy này thực tế chạy **hai
bước liên tiếp**:

```
0002_snapshots  →  0003_business  →  0004_employee_attribution
```

Cả hai bước đều thuộc PHB-03 và đều đã có trong bản được duyệt. Không có gì
bất thường — chỉ là con số phải ghi cho đúng.

### Diễn tập đã làm gì?

Dựng một cơ sở dữ liệu trống, đưa nó về **đúng trạng thái máy chủ đang có**
(`0002_snapshots`), rồi chạy đúng lệnh khởi động của máy chủ:

```
Trước : alembic_version = 0002_snapshots   ·  11 bảng
Sau   : alembic_version = 0004_employee_attribution  ·  14 bảng

Bảng bị XOÁ            : (không có)
Bảng đang có bị SỬA    : (không có)
Bảng được THÊM         : kpi_purchase_price_override
                         product_group_classification
                         employee_attribution_override
```

**Đọc bảng trên như sau:** ba cái tên được thêm chính là ba nơi cất **quyết
định của chủ dự án** (giá vốn gõ tay · tick Gia dụng · gán nhân viên). Trước
đây chưa có chỗ nào cất được. Còn dòng "Bảng bị XOÁ: không có" và "Bảng đang có
bị SỬA: không có" là bằng chứng máy móc rằng bước nâng cấp này **chỉ thêm vào,
không đụng vào bất cứ thứ gì đang có**.

### Còn nếu cần quay lui thì dữ liệu gõ tay có mất không?

Không. Đã chạy thật vòng nâng-lên → hạ-xuống → nâng-lên-lại qua công cụ thật:
khi hạ xuống, dữ liệu chủ dự án nhập được **cất vào bảng lưu tạm cùng cơ sở dữ
liệu**; khi nâng lên lại thì **nạp về đủ**. 3 bài kiểm về việc này đều đạt.

*(Lưu ý: chưa và sẽ không chạy thử hạ cấp trên dữ liệu thật của máy chủ — đúng
theo yêu cầu an toàn.)*

---

## 5. Làm sao biết production đang chạy đúng bản?

```
PRODUCTION_FINGERPRINT = CHƯA KIỂM ĐƯỢC (không có mạng tới máy chủ)
```

Nhưng đã chuẩn bị sẵn một cách kiểm **nhìn bằng mắt trên điện thoại, không cần
công cụ kỹ thuật nào**.

### Dấu hiệu nhận biết: một thẻ mới trên thanh menu

Bản mới thêm đúng một thẻ vào thanh menu trên cùng, tên là **"Kinh doanh"**,
nằm **giữa "Tổng quan" và "Bán hàng"**:

```
BẢN CŨ:   Chạy báo cáo · Dữ liệu · Tổng quan ·                Bán hàng · Sản phẩm · Nhân viên
BẢN MỚI:  Chạy báo cáo · Dữ liệu · Tổng quan · [Kinh doanh] · Bán hàng · Sản phẩm · Nhân viên
                                                ▲▲▲▲▲▲▲▲▲▲▲
                                                thẻ này CHỈ có ở bản mới
```

**Cách kiểm:** mở `reports.tinphatcrm.com` → nhìn thanh menu trên cùng.

- **Thấy thẻ "Kinh doanh"** → máy chủ đã chạy bản mới. ✅
- **Không thấy** → máy chủ vẫn đang chạy bản cũ, deploy chưa ăn. ❌

Đây là dấu hiệu đáng tin vì thẻ này **không tồn tại** trong bản cũ `eaa3fde` —
đã kiểm bằng máy. Không thể "thấy nhầm".

**Đừng chỉ tin vào việc Render báo "Live" màu xanh.** Render báo build xong,
không báo bạn đang xem đúng bản nào. Phải nhìn thấy chữ "Kinh doanh" bằng mắt.

---

## 6. Kiểm coverage giá vốn

```
E2E1_PRICE_COVERAGE = CHƯA CHẠY TRÊN MÁY CHỦ THẬT
```

Không mở được kỳ kinh doanh thật nên không có con số thật để ghi:

```
kỳ                        = chưa có
độ phủ                    = chưa có
số dòng thiếu giá vốn     = chưa có
số dòng bị chặn           = chưa có
```

### Bằng chứng đã có (chạy trên máy, không phải trên máy chủ)

Các bài kiểm sau đã chạy và đạt:

- Kỳ chưa đủ 100% giá vốn thì **không bao giờ** được gọi là số chính thức.
- Đủ 100% mới đánh dấu chính thức.
- Ô đếm dòng thiếu giá vốn **đếm ra số thật** (trước bản sửa nó luôn bằng 0 do
  lỗi cấu tạo — đây chính là lỗi B02 đã sửa).
- Khối "độ phủ" liệt kê **từng loại lý do bị chặn kèm số dòng**, không gộp
  chung một câu chung chung.
- Thiếu giá vốn hiện **"—"**, không hiện số 0 giả.

### Việc chủ dự án cần làm (mục 17, bước 3)

Mở **Kinh doanh** → chọn một tháng thật → đọc khối "độ phủ" và xác nhận:

- Có thấy tỉ lệ phủ (ví dụ `34/142 dòng`) không?
- Số dòng thiếu giá vốn có **lớn hơn 0** khi thực tế đang thiếu không?
- Chỗ thiếu có hiện **"—"** chứ không phải **"0"** không?

---

## 7. Kiểm một giá vốn Owner nhập thật

```
E2E2_MANUAL_PP = CHƯA CHẠY TRÊN MÁY CHỦ THẬT
```

Không thực hiện được, và **kể cả có mạng cũng không được phép tự làm**: yêu cầu
ghi rõ chỉ được nhập giá vốn khi chủ dự án **biết chắc con số đúng**. Phiên này
không biết, và **tuyệt đối không đoán giá vốn**.

### Bằng chứng đã có

Đã chạy và đạt: gõ giá → lưu → **nhãn đổi thành "Owner đã nhập"** → **lợi nhuận
và doanh thu quy đổi tính lại ngay**, không cần nạp lại sổ; ô suy ra **không gõ
vào được**; giá vô lý **bị từ chối** thay vì đoán bừa.

Đây chính là lỗi **B01** mà bản sửa đã chữa: trước đây gõ giá tay xong lợi
nhuận **vẫn không tính**, vì hệ thống nhìn cái nhãn cũ thay vì nhìn con số thật.

### Việc chủ dự án cần làm (mục 17, bước 4)

Chọn **một dòng mà bạn biết chắc giá vốn đúng**. Trước khi gõ, chụp màn hình
hoặc ghi lại: số đơn · tên hàng · số lượng · giá bán · lợi nhuận hiện tại. Gõ
giá → Lưu → xác nhận ngay trên màn hình đó:

- Giá vốn hiện đúng con số vừa gõ.
- Nhãn thành **"Owner đã nhập"**.
- **Lợi nhuận đổi ngay**, không phải bấm "tính" gì thêm.

**Nếu không có dòng nào biết chắc giá — DỪNG, đừng gõ đại.** Thà chưa kiểm còn
hơn nhập một con số sai vào sổ thật.

---

## 8. Kiểm giá Owner sau cumulative re-upload

```
E2E2B_CUMULATIVE_REUPLOAD = CHƯA CHẠY TRÊN MÁY CHỦ THẬT
   → xếp loại: NOT_APPLICABLE_NO_SAFE_REAL_CASE
     (dựa vào bằng chứng kiểm toán vòng đời import đã hoàn tất)
```

Đây là câu hỏi chủ dự án hỏi trực tiếp: **"upload sổ 01–03/09, tôi sửa giá một
dòng, rồi upload sổ 01–10/09 — giá tôi sửa có mất không?"**

**Câu trả lời: KHÔNG MẤT.** Việc này **đã được chạy thật** trong phiên kiểm toán
vòng đời import trước đó, đúng theo kịch bản trên:

```
03/09  upload sổ 01–03/09
       dòng BH100 "Tủ lạnh Panasonic NR-BX41" — máy không tra được giá vốn
       → hiện "Chưa có"

       Owner gõ 7.800.000  → nhãn "Owner đã nhập"

10/09  upload sổ CỘNG DỒN 01–10/09 (có lại đúng dòng BH100 đó)
       → giá hiệu lực : 7.800.000        ✔ GIỮ NGUYÊN
       → nhãn         : "Owner đã nhập"  ✔ GIỮ NGUYÊN
```

Và quan trọng không kém — **doanh thu không bị nhân đôi**:

```
Sổ đợt 1 (3 dòng) rồi sổ cộng dồn đợt 2 (6 dòng, gồm 3 dòng cũ y nguyên)
   → tổng số dòng hiện hành = 6   (KHÔNG phải 9)
   → doanh thu cộng đúng phần mới

Bấm nhầm upload LẠI ĐÚNG FILE CŨ
   → 0 dòng mới · 3 dòng "không đổi" · snapshot ghi "FILE TRÙNG"
   → doanh thu giữ nguyên 19.000.000, không nhân đôi
```

**Vì sao chắc chắn:** giá của chủ dự án được cất theo **tên nghiệp vụ của dòng**
(Số BH + Tên hàng + lần xuất hiện thứ mấy) — **không** theo số thứ tự dòng trong
file, **không** theo mã máy sinh ra lúc nạp. Nạp lại bao nhiêu lần thì cái tên
đó vẫn thế, nên giá vẫn dính đúng dòng.

Cũng đã kiểm: giá gõ cho BH100 **không lan sang** BH110 dù hai đơn bán cùng một
mặt hàng. Giá gắn với **một dòng bán**, không gắn với mặt hàng.

Vì vậy các ô kết quả:

```
OWNER_PRICE_AFTER_CUMULATIVE_REUPLOAD = PRESERVED  (bằng chứng kiểm toán)
MANUAL_PROVENANCE_AFTER_REUPLOAD      = PRESERVED  (bằng chứng kiểm toán)
PROFIT_AFTER_CUMULATIVE_REUPLOAD      = CORRECT    (bằng chứng kiểm toán)
NO_DUPLICATE_REVENUE                  = YES        (bằng chứng kiểm toán)
```

### Một điểm cần theo dõi (không chặn deploy)

Nếu **một đơn có HAI dòng cùng y hệt tên hàng** (ví dụ "Chi phí vận chuyển" xuất
hiện hai lần trên cùng một đơn), và lần xuất sổ sau kế toán **đảo thứ tự** hoặc
**chèn thêm một dòng cùng tên lên trên**, thì giá gõ cho "lần thứ nhất" sẽ đi
theo **vị trí thứ nhất**, tức có thể sang một dòng khác.

**Tần suất thật đã đo trên 531 dòng sổ kế toán thật: 0/531 — chưa xảy ra lần
nào.** Và khi xảy ra thì hệ thống **có dựng cờ "Nguồn sửa"** ở tab Dữ liệu để
nhìn thấy. Vì vậy đây xếp là **điểm theo dõi**, không phải lỗi chặn.

---

## 9. Kiểm "Không thấy" / "Nguồn sửa" sau upload

```
LATEST_SNAPSHOT_NOT_SEEN       = CHƯA ĐO ĐƯỢC (chưa có lần upload thật nào)
LATEST_SNAPSHOT_SOURCE_CHANGED = CHƯA ĐO ĐƯỢC
UNEXPLAINED_NOT_SEEN           = CHƯA ĐO ĐƯỢC
NOT_SEEN_EXPLANATION           = chưa có, vì chưa có lần upload nào để quan sát
```

### Đây là việc chủ dự án phải làm sau MỖI lần upload

Vào tab **Dữ liệu** → nhìn dòng snapshot vừa tạo → xem hai cột:

| Cột | Ý nghĩa | Đọc thế nào |
|---|---|---|
| **Không thấy** | Dòng có ở sổ trước nhưng **không có** trong sổ vừa nạp | `0` = bình thường |
| **Nguồn sửa** | Kế toán đã sửa con số của một dòng đã nạp trước đó | Không tự nó là lỗi — nhưng **cần xem** |

### Nếu "Không thấy" = 0

Bình thường. Đi tiếp.

### Nếu "Không thấy" > 0 — ĐỪNG duyệt tổng ngay

Mở từng dòng bị đánh cờ ra xem, và xếp nó vào một trong các nhóm:

- **A.** Dòng kế toán mới / thiếu thật.
- **B.** Kế toán **đổi tên hàng**.
- **C.** Kế toán **đổi số BH** (số chứng từ).
- **D.** Sửa lại nguồn.
- **E.** Nguyên nhân khác đã biết.

**Kỳ chỉ được coi là đã kiểm xong khi không còn cờ "Không thấy" nào chưa giải
thích được.**

### Vì sao hệ thống KHÔNG tự ghép giúp?

Đây là quyết định **OD-C** mà chủ dự án đã đóng băng, và bản này giữ đúng:

> Nếu kế toán **đổi tên hàng** hoặc **đổi số BH**, Reports **KHÔNG được đoán**
> rằng dòng cũ và dòng mới là cùng một lần bán.

Hệ quả là: **dòng cũ có thể còn nằm đó, dòng mới thành một dòng riêng, và cờ
"Không thấy" nổi lên.** Nghe có vẻ phiền — nhưng đó là **cố ý**. Đoán mò rồi
gộp nhầm hai lần bán khác nhau sẽ làm sai tiền một cách **âm thầm**, còn cách
này thì sai chỗ nào **nhìn thấy được ngay**.

Một cái cờ để bạn kiểm tra thì tốt hơn một con số sai mà không ai biết.

---

## 10. Kiểm nhân viên chưa xác định

```
E2E3_UNKNOWN_EMPLOYEE = CHƯA CHẠY TRÊN MÁY CHỦ THẬT
```

Không tự gán được — yêu cầu ghi rõ **chỉ gán khi biết đúng người**, và phiên này
không biết. **Không bịa gán nhân viên.**

### Bằng chứng đã có

Đã chạy và đạt: chọn đúng người → lưu → **bằng chứng gốc trong sổ vẫn còn nguyên,
không bị ghi đè** · nhóm "Chưa xác định" **giảm đi** · KPI người được chọn **tăng
lên** · **tổng lợi nhuận của kỳ KHÔNG đổi** · **gỡ gán được** để trả dòng về đúng
như sổ ghi · gán cho một cái tên không phải nhân viên thật thì **bị từ chối**.

Điểm quan trọng của **OD-5**: dòng chưa biết ai bán thì lợi nhuận **vẫn vào tổng
của kỳ**, chỉ là **chưa cộng cho ai**. Trước đây không trả lời được câu "ai bán"
thì **mất luôn** phần lợi nhuận đó.

---

## 11. Kiểm số lượng = 0

```
E2E4_QUANTITY_ZERO = CHƯA CHẠY TRÊN MÁY CHỦ THẬT
```

### Bằng chứng đã có

Đã chạy và đạt: dòng số lượng 0 **hiện cảnh báo**, lợi nhuận để **trống** chứ
**không chốt bằng 0**, và nó **chặn** kỳ đạt 100% chính thức. Gõ thêm giá vốn
vào **cũng không** biến nó thành dòng có lợi nhuận hợp lệ — vì thiếu sót ở đây
là **số lượng**, không phải giá vốn.

Đúng theo **OD-1**. Và **không được sửa số lượng chỉ để kiểm thử**.

---

## 12. Kiểm số lượng âm

```
E2E5_NEGATIVE_QUANTITY = CHƯA CHẠY TRÊN MÁY CHỦ THẬT
```

### Bằng chứng đã có

Đã chạy và đạt: dòng số lượng âm **hiện cảnh báo**, **không vào KPI nhân viên**,
và **cũng không vào tổng lợi nhuận công ty**.

Vế cuối là phía **thận trọng** theo **OD-2**: hệ thống **không tự suy** rằng số
âm nghĩa là trả hàng / hoàn tiền. Tự suy như vậy là **phát minh ra ngữ nghĩa kế
toán** mà không ai ra lệnh. Hành vi doanh thu kế toán giữ **nguyên như đang
đóng băng** — phiên này không đổi.

---

## 13. Kiểm tháng cũ và "So tháng trước"

```
E2E_CROSS_MONTH = CHƯA CHẠY TRÊN MÁY CHỦ THẬT
```

### Bằng chứng đã có

Kiểm toán vòng đời import đã chạy thật và ghi `CROSS_MONTH_MOM = PASS`, với:

```
Tháng 9 sau khi đã upload sổ tháng 10:
   số liệu tháng 9        ✔ còn nguyên, mở lại xem được
   giá vốn gõ tay tháng 9 ✔ còn
   giá đè tay tháng 9     ✔ còn
   gán nhân viên tháng 9  ✔ còn
   tick Gia dụng tháng 9  ✔ còn
```

Tháng mới **không thay thế** tháng cũ — mỗi lần upload là **thêm một lớp**, không
xoá lớp trước.

Về công thức **"So tháng trước"**, đã kiểm và đạt:

```
(doanh thu tháng này − doanh thu tháng trước) ÷ doanh thu tháng trước × 100%
```

Đọc đúng **DOANH THU BÁN HÀNG** của tháng liền trước — **không** dùng lợi nhuận,
**không** dùng doanh thu quy đổi, **không** dùng số lượng, **không** dùng chỉ
tiêu. Và nếu tháng trước doanh thu bằng 0 thì hiện **N/A**, không hiện một phần
trăm vô nghĩa.

---

## 14. Dữ liệu Owner cũ có được bảo toàn không?

```
OWNER_DATA_PRESERVED = CHƯA XÁC NHẬN ĐƯỢC TRÊN MÁY CHỦ THẬT
                       (nhưng bước nâng cấp KHÔNG THỂ làm mất — xem dưới)
```

Có hai nguồn rủi ro khác nhau, và chỉ một cái là đã loại trừ được chắc chắn:

**Rủi ro 1 — bước nâng cấp cơ sở dữ liệu làm mất dữ liệu cũ. → ĐÃ LOẠI TRỪ.**

Đã chứng minh bằng máy ở mục 4: bước nâng cấp **chỉ thêm 3 bảng mới**, **không
xoá bảng nào**, **không sửa cấu trúc bảng nào đang có**. Nó **không đọc và không
ghi** vào dữ liệu cũ. Về mặt cơ chế, nó **không có đường nào** để làm hỏng dữ
liệu sẵn có.

**Rủi ro 2 — sau khi chạy thật thì có gì đó lệch. → CHỦ DỰ ÁN PHẢI TỰ MẮT XEM.**

Cần xác nhận bốn thứ vẫn còn (mục 17, bước 8):

- Giá vốn **gõ tay** (nhãn "Owner đã nhập").
- Giá vốn **đè tay** lên giá máy.
- **Gán nhân viên** đã sửa.
- Tick **Gia dụng**.

Lưu ý: ba trong bốn thứ này được cất trong **các bảng mới toanh** vừa tạo, nên
trước lần deploy này chúng **chưa từng tồn tại trên máy chủ**. Với lần deploy
đầu tiên, thứ cần soi kỹ nhất là **số liệu và bản nhập legacy cũ** vẫn đọc được
bình thường.

---

## 15. Có phát hiện lỗi production mới không?

**Không có lỗi chặn nào.** Đã tìm và không thấy.

```
NEW_PRODUCTION_BLOCKERS = KHÔNG CÓ
```

Phát hiện **một** điểm nhỏ, thuộc loại **giấy tờ, không phải mã chạy**:

> **F-S118-01 — hai đường dẫn tài liệu bị gãy trong sổ tiến độ.**
>
> Sổ tiến độ và báo cáo bản sửa cùng trỏ tới file
> `docs/reviews/PHB-03-pending-reason-business-classification.md`, nhưng file
> đó nằm ở một nhánh khác nên trên nhánh chính thức nó **không tồn tại**. Bộ
> kiểm tra tài liệu vì vậy báo **5 đường dẫn gãy** thay vì mức nền đã biết là
> **3**.
>
> **Phân loại:** F — điều kiện có sẵn, không chặn. Không liên quan mã chạy.
> **Đã xử lý:** gom file đó (cùng hai báo cáo liên quan) về nhánh chính thức.
> Kiểm lại: **về đúng 3 đường dẫn gãy đã biết** (mức nền cũ, không phát sinh
> mới).

### Các mục KHÔNG làm trong phiên này (đúng như yêu cầu)

Giữ nguyên hoãn lại, không đụng tới:

```
R1  cảnh báo "Không thấy" trên trang Kinh doanh   → HOÃN (quyết định OD-A)
R2  hiện giá máy lúc chủ dự án đè + giờ can thiệp → HOÃN (quyết định OD-B)
R3  bộ lọc "những dòng tôi đã sửa"                → HOÃN (quyết định OD-B)
```

Cũng **không** làm: bộ nhớ đệm giá vốn · tối ưu tốc độ · hệ thống ghi vết mới ·
ghép nhận dạng mờ · thiết kế lại tên trùng · thiết kế lại Product Identity ·
đụng vào Tracking.

```
SCOPE_DRIFT = KHÔNG
```

---

## 16. PHB-03 đã DONE chưa?

**CHƯA.**

```
PHB_03 = PRODUCTION_VERIFICATION_INCOMPLETE
```

Cửa đóng PHB-03 có 15 điều kiện. Tình trạng:

| # | Điều kiện | Kết quả |
|---|---|---|
| 1 | Đúng bản đã duyệt được deploy | ⏳ đã sẵn sàng trên nhánh chính thức, **chưa bấm deploy** |
| 2 | Migration đạt | ⏳ diễn tập **đạt**, chưa chạy thật |
| 3 | Dấu vân tay production đạt | ⏳ chưa kiểm được |
| 4 | E2E-1 độ phủ giá vốn | ⏳ chưa chạy thật |
| 5 | E2E-2 giá vốn nhập tay | ⏳ chưa chạy thật |
| 6 | E2E-2B giá sau cộng dồn | ✅ **chấp nhận** bằng bằng chứng kiểm toán |
| 7 | E2E-3 nhân viên chưa xác định | ⏳ chưa chạy thật |
| 8 | E2E-4 số lượng 0 | ⏳ chưa chạy thật |
| 9 | E2E-5 số lượng âm | ⏳ chưa chạy thật |
| 10 | Kiểm chéo tháng | ⏳ chưa chạy thật (kiểm toán đã đạt) |
| 11 | Dữ liệu Owner được bảo toàn | ⏳ cơ chế **an toàn**, chưa xác nhận mắt thường |
| 12 | Không còn lỗi production chưa giải thích | ✅ **đạt** |
| 13 | Đã soi cờ "Không thấy" của snapshot mới nhất | ⏳ chưa có upload nào |
| 14 | Không còn "Không thấy" chưa giải thích | ⏳ chưa có upload nào |
| 15 | Tài liệu dự án đã cập nhật | ✅ **đạt** (chính báo cáo này + sổ tiến độ) |

**3 đạt / 12 còn chờ.** Và **cả 12 cái còn chờ đều chờ đúng một việc: chủ dự án
bấm Deploy rồi mở web kiểm.**

Không cái nào trong 12 cái đó chờ sửa mã. Mã đã sẵn sàng.

---

## 17. Việc tiếp theo là gì?

```
NEXT_VERTICAL_ACTION = Chủ dự án deploy trên Render + chạy 8 bước kiểm dưới đây.
                       Xong 8 bước thì PHB-03 = DONE, và việc kế tiếp là
                       PHB-04 — Legacy Reference V1.
```

### 8 bước — làm được trên điện thoại

**Bước 1 — Deploy.**
Vào Render → service `reports-web` → **Manual Deploy** → chọn **commit trên
cùng danh sách** của nhánh `claude/extract-upload-repo-gq2ws4` → Deploy.
Chờ đến khi hiện **Live**.

> Nếu deploy **hỏng**: web cũ **vẫn chạy bình thường**, không mất gì. Chụp màn
> hình phần log lỗi gửi lại. Muốn quay lui hẳn thì Manual Deploy commit
> `eaa3fde`.

**Bước 2 — Kiểm đúng bản (quan trọng nhất).**
Mở `reports.tinphatcrm.com`. Nhìn thanh menu trên cùng.
**Có thẻ "Kinh doanh"** giữa "Tổng quan" và "Bán hàng" chưa?
→ **Chưa có thì DỪNG**, các bước sau vô nghĩa.

**Bước 3 — Độ phủ giá vốn.**
Bấm **Kinh doanh** → chọn một tháng thật. Đọc khối độ phủ:
tỉ lệ phủ · số dòng thiếu giá vốn · chỗ thiếu hiện **"—"** (không phải "0").

**Bước 4 — Gõ một giá vốn thật.**
Chọn **một dòng biết chắc giá vốn đúng**. Ghi lại số hiện tại trước khi gõ.
Gõ → Lưu → xác nhận **ngay**: nhãn thành "Owner đã nhập", **lợi nhuận đổi ngay**.
→ **Không có dòng nào biết chắc thì bỏ qua bước này**, đừng gõ đại.

**Bước 5 — Upload sổ + soi cờ.**
Upload một sổ thật → vào tab **Dữ liệu** → dòng snapshot vừa tạo →
đọc cột **"Không thấy"** và **"Nguồn sửa"**.
→ **"Không thấy" > 0 thì mở từng dòng ra xem** trước khi tin tổng (mục 9).

**Bước 6 — Kiểm giá sau khi upload cộng dồn.**
Sau bước 5, mở lại **đúng dòng đã gõ giá ở bước 4**.
Vẫn thấy **"Owner đã nhập"** và **đúng con số** chứ?

**Bước 7 — Mở lại tháng cũ.**
Chọn tháng trước → số liệu còn nguyên chứ? Các sửa tay còn nguyên chứ?
Xem ô **"So tháng trước"** — đang so **doanh thu**, và tháng trước bằng 0 thì
hiện **N/A**.

**Bước 8 — Soi các trường hợp đặc biệt (nếu tình cờ gặp).**
- Dòng **số lượng 0** → lợi nhuận phải **trống**, không phải 0.
- Dòng **số lượng âm** → có cảnh báo, không vào KPI ai.
- Nhóm **"Chưa xác định nhân viên"** → mở được, gán được, và **tổng lợi nhuận
  của kỳ không đổi** sau khi gán.

→ **Không gặp trường hợp nào thì ghi "không có ca thật"** — hoàn toàn bình
thường, không phải lỗi. **Tuyệt đối đừng sửa số lượng hay giá bán chỉ để tạo ra
ca kiểm thử.**

### Gửi lại gì?

Ảnh chụp màn hình của bước 2, 3, 5 (cột "Không thấy"), và bước 6. Có chừng đó
là đủ để đóng PHB-03 = DONE.

---

## Phụ lục — Bảng kết quả phiên

```
TARGET_GATE                = PASS
CANDIDATE_SHA              = d066d227da852b17a57d4a8492fa79c7fc7b2aff
WORKTREE                   = CLEAN
CANDIDATE_UNCHANGED        = PASS — không lệch một dòng mã nào so với nhánh
                             soát xét (5bdd838) và nhánh kiểm toán (c02d42a)

PRODUCTION_BEFORE_SHA      = NOT_OBSERVABLE_FROM_SESSION
                             (bản nghiệm thu gần nhất: 1a011ee, S111;
                              nhánh chính thức trước phiên: eaa3fde;
                              1a011ee ↔ eaa3fde lệch mã chạy = 0)
ROLLBACK_SHA               = eaa3fdeb4ffdfd2d5772314ac24cf8a1273cc67e
PRODUCTION_DEPLOYED_SHA    = NOT_DEPLOYED_BY_SESSION (chờ chủ dự án)

CANONICAL_INTEGRATION      = DONE — fast-forward từ eaa3fde (không force ·
                             không rewrite · không squash · không merge commit)
DEPLOY_THIS_COMMIT         = commit MỚI NHẤT trên canonical. Mọi commit từ
                             d066d22 trở về sau có mã chạy IDENTICAL với bản
                             được duyệt; phần thêm chỉ là docs.
PRODUCTION_CODE_DELTA      = 0 (app/ tools/ config/ Dockerfile render.yaml
                             alembic.ini pyproject.toml — lệch bằng không so
                             với d066d22; phần thêm vào chỉ là tài liệu)

FULL_TESTS                 = PASS — 2136 passed, 11 skipped (88.87s)
GOLDEN_TESTS               = PASS — 74 passed, 2 skipped
PRODUCTION_PATH_TESTS      = PASS — 101 passed
MIGRATION_ROLLBACK_SAFETY  = PASS — 3 passed (round-trip qua alembic thật)

ALEMBIC_CHAIN              = 0001 → 0002 → 0003 → 0004 (một head duy nhất)
PRODUCTION_DB_CURRENT      = 0002_snapshots
MIGRATION_REQUIRED         = 0003_business + 0004_employee_attribution (HAI bước)
MIGRATION_DRY_RUN          = PASS — 0002_snapshots → 0004_employee_attribution
                             11 bảng → 14 bảng · 0 xoá · 0 sửa bảng cũ
MIGRATION (production)     = NOT_RUN — chạy tự động lúc container khởi động
                             (`alembic upgrade head && gunicorn ...`), fail-closed

APP_BOOT_SMOKE             = PASS (cục bộ, trên DB đã migrate) —
                             / · /kinh-doanh · /kinh-doanh/gia-nhap ·
                             /kinh-doanh/nhan-vien · /du-lieu  → 200
                             /kinh-doanh/gia-dung → 404 ĐÚNG THIẾT KẾ
                             (chưa chọn nhân viên Nội thành)

PRODUCTION_FINGERPRINT     = NOT_VERIFIABLE_FROM_SESSION
FINGERPRINT_MECHANISM      = thẻ menu "Kinh doanh" (vắng ở eaa3fde, có ở d066d22)

E2E1_PRICE_COVERAGE        = NOT_EXECUTED_NO_SESSION_EGRESS
E2E2_MANUAL_PP             = NOT_EXECUTED_NO_SESSION_EGRESS
E2E2B_CUMULATIVE_REUPLOAD  = NOT_APPLICABLE_NO_SAFE_REAL_CASE
                             (bằng chứng kiểm toán import được chấp nhận)
E2E3_UNKNOWN_EMPLOYEE      = NOT_EXECUTED_NO_SESSION_EGRESS
E2E4_QUANTITY_ZERO         = NOT_EXECUTED_NO_SESSION_EGRESS
E2E5_NEGATIVE_QUANTITY     = NOT_EXECUTED_NO_SESSION_EGRESS
E2E_CROSS_MONTH            = NOT_EXECUTED_NO_SESSION_EGRESS
                             (kiểm toán import: CROSS_MONTH_MOM = PASS)

LATEST_SNAPSHOT_NOT_SEEN       = NOT_MEASURED (chưa có upload thật)
LATEST_SNAPSHOT_SOURCE_CHANGED = NOT_MEASURED
UNEXPLAINED_NOT_SEEN           = NOT_MEASURED

OWNER_DATA_PRESERVED       = NOT_VERIFIED_ON_PRODUCTION
                             (migration ADDITIVE thuần ⟹ không có đường làm mất)

EGRESS_EVIDENCE            = reports.tinphatcrm.com:443 → CONNECT 403
                             api.render.com:443 · dashboard.render.com:443 ·
                             price.tinphatcrm.com:443 → không kết nối được
                             (cùng lớp denial đã ghi ở S093 / S110 / S112)

GOVERNANCE_VALIDATORS      = validate_structure PASS · validate_project_state
                             PASS · validate_evidence PASS (155 REQUIRED) ·
                             validate_task_completion PASS (13 DONE task) ·
                             validate_reference_integrity FAIL với ĐÚNG 3
                             reference REM-T06 đã biết (mức nền, không mới)

NEW_PRODUCTION_BLOCKERS    = NONE
NON_BLOCKING_FINDINGS      = F-S118-01 (2 đường dẫn tài liệu gãy — ĐÃ SỬA,
                             docs-only, về đúng mức nền 3)
OWNER_DECISIONS_REQUIRED   = NONE
DEFERRED_UNCHANGED         = R1 (OD-A) · R2 · R3 (OD-B)
OD_C_SEMANTICS             = GIỮ NGUYÊN — không fuzzy-merge, không tự đối soát
SCOPE_DRIFT                = NO

PHB_03                     = PRODUCTION_VERIFICATION_INCOMPLETE
NEXT_VERTICAL_ACTION       = Chủ dự án deploy + 8 bước kiểm (mục 17);
                             sau đó PHB-03 = DONE → PHB-04 Legacy Reference V1
```
