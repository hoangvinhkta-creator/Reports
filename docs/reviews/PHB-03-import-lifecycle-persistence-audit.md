# PHB-03 — Kiểm Toán Vòng Đời Import & Lưu Trữ Trước Khi Deploy

**Loại phiên:** READ-ONLY BOUNDED AUDIT (không sửa code, không deploy, không merge, không sửa lỗi)
**Nhánh được kiểm:** `claude/phb-03-bounded-semantics-repair-685gf4`
**HEAD:** `d066d227da852b17a57d4a8492fa79c7fc7b2aff`
**Nhánh phiên làm việc:** `claude/phb-03-import-audit-elqcnb` (trỏ ĐÚNG cùng commit, nội dung giống hệt)
**Ngày:** 2026-09-04
**Câu hỏi của chủ dự án:** một file kế toán KHÔNG chỉ được upload một lần. Vậy khi
upload lại thì chuyện gì thực sự xảy ra với con số, với giá vốn tôi đã tự sửa, và
với dữ liệu tháng cũ?

---

## 1. Kết luận ngắn gọn

**Có thể tiếp tục sang chạy thử production (E2E). Không có lỗi nào chặn deploy.**

Ba câu trả lời quan trọng nhất, đã kiểm bằng cách chạy thật trên chính code của
nhánh này (không phải đọc rồi đoán):

| Câu hỏi | Trả lời |
|---|---|
| Upload sổ 01–10/09 đè lên sổ 01–03/09 — giá nhập tôi gõ tay còn không? | **CÒN.** Giữ nguyên 7.800.000, vẫn mang nhãn "Owner đã nhập". |
| Upload sổ tháng 10 — dữ liệu tháng 9 có mất không? | **KHÔNG MẤT.** Tháng 9 vẫn còn đủ 6/6 dòng, mọi sửa tay của tháng 9 vẫn hiệu lực. |
| "So tháng trước" của tháng 10 có lấy đúng tháng 9 không? | **ĐÚNG.** Lấy đúng doanh thu bán hàng tháng 9, không phải lợi nhuận, không phải DS quy đổi. |

Bốn điểm cần Owner biết, nhưng **không** đủ để chặn deploy:

1. Nếu kế toán **đổi tên hàng** hoặc **đổi số BH** của một dòng rồi xuất lại sổ,
   Reports coi đó là **một dòng mới** và **giữ luôn dòng cũ** → doanh thu bị
   **đếm hai lần** cho tới khi có người xử lý. Hệ thống CÓ dựng cảnh báo
   ("Không thấy") và hiện nó ở tab **Dữ liệu**, nhưng trang **Kinh doanh** thì
   không nhắc gì. Đây là quy tắc đã được đóng băng từ trước (PRA-002 §696:
   *"không đoán ghép"*) — cố tình chọn "thà hiện cảnh báo còn hơn tự ghép nhầm
   hai đơn". Xem mục 13.
2. Hệ thống **không nhớ hộ** rằng một dòng từng bị sửa và **sau đó nguồn đã đổi**.
   Nó có ghi "nguồn đã sửa", nhưng cảnh báo đó nằm ở tab Dữ liệu và không nối
   với việc "dòng này Owner từng gõ giá". Xem mục 6.
3. Nếu **một đơn có hai dòng cùng tên hàng** và thứ tự hai dòng đó bị đảo giữa
   hai lần xuất sổ, giá Owner gõ sẽ **đi theo vị trí, không theo dòng**. Trên
   531 dòng sổ thật đã kiểm, **không có một trường hợp nào** như vậy. Xem mục 4.
4. Mỗi lần upload, hệ thống **tra lại giá vốn cho TOÀN BỘ sổ**, kể cả những dòng
   Owner đã tự gõ giá. Tốn công vô ích nhưng **không sai số**, và ở quy mô thật
   (~350 dòng/tháng) là dưới một giây. Xem mục 10–11.

**Bằng chứng nền:** toàn bộ 2.136 test của repo chạy lại trên đúng HEAD này:
`2136 passed, 11 skipped in 80.16s`. Cộng thêm 5 kịch bản riêng của phiên kiểm
toán này (TEST-A…TEST-E), chạy trực tiếp trên tầng import và tầng lưu thật.

---

## 2. Khi upload file mới, Reports thực sự làm gì?

Reports **KHÔNG** xoá dữ liệu cũ rồi ghi dữ liệu mới. Nó làm việc giống một
**cuốn sổ có ghi ngày**, không giống một cái tủ bị thay ruột.

```
  File .xlsx Owner tải lên
        │
        ├─► đọc từng dòng, chuẩn hoá số/ngày/tên
        │
        ├─► ĐẶT TÊN cho từng dòng hàng  =  (Số BH , Tên hàng , lần xuất hiện thứ mấy)
        │        ví dụ: (BH100 , "Tủ lạnh Panasonic NR-BX41" , #1)
        │        ĐÂY LÀ CHÌA KHOÁ CỦA TOÀN BỘ CÂU CHUYỆN
        │
        ├─► so từng dòng với thứ đang có trong database:
        │        chưa từng thấy tên đó   → THÊM MỚI
        │        thấy rồi, nội dung y hệt → KHÔNG ĐỘNG GÌ  (không cộng thêm đồng nào)
        │        thấy rồi, nội dung khác  → GHI MỘT PHIÊN BẢN MỚI + dựng cờ "NGUỒN ĐÃ SỬA"
        │        có trong database, sổ mới không có → dựng cờ "KHÔNG THẤY" (KHÔNG xoá)
        │
        ├─► ghi tất cả vào database trong MỘT lần cam kết
        │        (hỏng giữa chừng ⇒ huỷ sạch, không bao giờ có nửa lần nhập)
        │
        └─► xoá file .xlsx tạm trên máy chủ
```

Quyết định của Owner **nằm ở ba cái tủ riêng, tách hẳn khỏi đường import**:

```
   TỦ CỦA MÁY  (import ghi vào)          TỦ CỦA OWNER  (chỉ Owner ghi vào)
   ─────────────────────────────         ─────────────────────────────────
   dòng sổ gốc từng phiên bản            giá nhập KPI Owner gõ tay
   kết quả máy tính ra                   phân loại Gia dụng
   con trỏ "bản hiện hành"               gán lại nhân viên
              │                                       │
              └──────────►  GHÉP LẠI LÚC ĐỌC  ◄───────┘
                     (mỗi lần Owner mở trang báo cáo)
```

Điểm mấu chốt: **đường import không hề chạm vào tủ của Owner.** Không có một
câu lệnh nào trong toàn bộ code import đọc hay ghi ba bảng quyết định của Owner.
Nên về mặt cấu trúc, một lần upload **không thể** xoá giá Owner đã gõ.

**Mô hình import chính xác:** không phải A (chỉ thêm), không phải B (thay cả kỳ),
mà là **C + D**: mỗi lần upload tạo **một ảnh chụp (snapshot) mới**, các dòng đã
đổi được ghi thành **phiên bản mới nối tiếp** (không đè lên bản cũ), và một
**bảng con trỏ** được cập nhật để chỉ ra "bản nào đang có hiệu lực hôm nay".
Không có `DELETE` ở bất kỳ đâu trong tầng import.

---

## 3. Upload 01–03 rồi 01–10 cùng tháng có chuyện gì?

Đã chạy thật (TEST-A). Sổ đợt 1 có 3 dòng, sổ đợt 2 cộng dồn có 6 dòng
(3 dòng cũ y nguyên + 3 đơn mới).

Kết quả đo được:

```
  snapshot 1 (03/09):  THÊM MỚI 3 · không đổi 0 · nguồn sửa 0
  snapshot 2 (10/09):  THÊM MỚI 3 · không đổi 3 · nguồn sửa 0

  Số dòng hàng hiện hành sau hai lần upload = 6   (KHÔNG phải 9)
  Doanh thu                                  = cộng đúng phần mới, không nhân đôi
```

Ba dòng cũ được nhận ra là **y hệt** nên hệ thống **không tạo phiên bản mới,
không cộng thêm doanh thu**. Chỉ ba đơn mới được thêm vào.

Kiểm thêm trường hợp cực đoan: **upload lại ĐÚNG file cũ** (bấm nhầm hai lần).
Kết quả: `THÊM MỚI 0 · không đổi 3`, snapshot mới được đánh dấu **"FILE TRÙNG"**,
doanh thu **giữ nguyên 19.000.000** — không nhân đôi.

---

## 4. Giá vốn Owner đã sửa có được giữ không?

**CÓ.** Đây là trường hợp Owner hỏi, và đã được chạy đúng như mô tả:

```
  03/09  upload sổ 01–03/09
         dòng BH100 "Tủ lạnh Panasonic NR-BX41" — máy KHÔNG tra được giá nhập
         → hiển thị "Chưa có"

  Owner gõ 7.800.000
         → lưu vào tủ riêng, nhãn "Owner đã nhập" (MANUAL)

  10/09  upload sổ cộng dồn 01–10/09 (có lại đúng dòng BH100 đó)
         → giá hiệu lực: 7.800.000        ✔ GIỮ NGUYÊN
         → nhãn:          "Owner đã nhập"  ✔ GIỮ NGUYÊN
         → bảng quyết định của Owner: vẫn đúng 1 dòng, không bị đụng tới
```

**Vì sao chắc chắn:** giá của Owner được lưu theo **tên nghiệp vụ của dòng**
(Số BH + Tên hàng + lần xuất hiện), **không** theo số thứ tự dòng trong file,
**không** theo mã kỹ thuật do lần import sinh ra. Import có chạy lại bao nhiêu
lần thì cái tên đó vẫn thế, nên giá vẫn dính đúng dòng.

**Giá Owner gõ có lan sang đơn khác cùng mặt hàng không?** KHÔNG (TEST-E3 đã
kiểm): BH100 và BH110 cùng bán "Tủ lạnh Panasonic NR-BX41"; Owner gõ giá cho
BH100 → BH110 **vẫn "Chưa có giá nhập"**. Đúng như mong đợi: giá gắn với **một
dòng bán**, không gắn với mặt hàng.

**Điểm cần lưu ý (hẹp, đã đo tần suất):** nếu **một đơn có HAI dòng cùng tên
hàng** — ví dụ "Chi phí vận chuyển" xuất hiện hai lần trên cùng một đơn — thì
"lần xuất hiện thứ mấy" được đánh theo **thứ tự dòng trong file**. Nếu lần xuất
sổ sau kế toán **chèn thêm một dòng cùng tên lên phía trên** hoặc **đảo thứ tự
hai dòng đó**, giá Owner gõ cho "lần thứ #1" sẽ **đi theo vị trí #1**, tức là
sang một dòng kế toán khác.

Đã kiểm bằng thật (TEST-E1/E2): giá 100.000 Owner gõ cho dòng bán 200.000 đã
chuyển sang dòng bán 900.000 mới chèn. Hệ thống **có dựng hai cờ "NGUỒN ĐÃ SỬA"**
cho cả hai dòng (thấy ở tab Dữ liệu), nhưng trang Kinh doanh không nhắc gì.

**Tần suất thật:** đã đếm trên **531 dòng sổ kế toán thật** (hai kỳ mẫu chuẩn
`period_2026_01` = 351 dòng và `period_2026_06` = 180 dòng):

```
  Số cặp (đơn, tên hàng) xuất hiện HAI LẦN TRỞ LÊN  =  0 / 531
```

Nghĩa là trên dữ liệu thật của Owner, tình huống này **chưa từng xảy ra một lần
nào**. Vì vậy đây được xếp là **điểm cần theo dõi, không phải lỗi chặn deploy**.

---

## 5. Nếu dòng kế toán thay đổi sau khi Owner sửa thì sao?

Phải tách làm **hai nhóm khác hẳn nhau**, vì hậu quả khác nhau hoàn toàn.

### Nhóm 1 — dòng vẫn là dòng đó, chỉ đổi con số (tên hàng và số BH KHÔNG đổi)

Đã đo thật, có kèm phép tính lợi nhuận:

| Kế toán đổi gì | Giá nhập của Owner | Lợi nhuận KPI | Kết luận |
|---|---|---|---|
| Số lượng 1 → 2 | giữ 7.800.000 | 200.000 → **400.000** | ✔ ĐÚNG (giá là giá **một cái**, nhân lên theo SL) |
| Giá bán 8.000.000 → 8.500.000 | giữ 7.800.000 | 200.000 → **700.000** | ✔ ĐÚNG (lãi tăng đúng phần bán thêm) |
| Đổi nhân viên | giữ 7.800.000 | không đổi | ✔ ĐÚNG |
| Đổi ngày bán (trong tháng) | giữ 7.800.000 | không đổi | ✔ ĐÚNG |
| Không đổi gì (đối chứng) | giữ 7.800.000 | không đổi | ✔ ĐÚNG |

Cả bốn trường hợp đầu đều được hệ thống **ghi nhận là "NGUỒN ĐÃ SỬA"** và dựng
cờ. Quan trọng: **lợi nhuận được tính lại bằng số liệu MỚI NHẤT của sổ**, chỉ
riêng giá nhập là lấy của Owner. Nên giá Owner gõ **vẫn còn an toàn về mặt kinh
tế** ở cả bốn trường hợp — vì giá nhập là **giá một đơn vị hàng**, nó không phụ
thuộc bán bao nhiêu cái hay bán giá bao nhiêu.

Đây là câu trả lời cho lo ngại "áp một quyết định cũ lên một dòng đã đổi": ở
nhóm này, quyết định cũ **vẫn đúng**, vì thứ Owner quyết định (mua vào bao nhiêu
một cái) không bị thay đổi bởi thứ kế toán sửa (bán mấy cái, bán giá nào).

Trường hợp duy nhất nó có thể sai: **kế toán sửa dòng đó thành một mặt hàng khác
mà vẫn giữ nguyên tên hàng cũ**. Nếu tên hàng không đổi thì Reports không có cách
nào biết — nhưng khi đó chính SỔ KẾ TOÁN mới là thứ mâu thuẫn, không phải Reports.

### Nhóm 2 — dòng đổi TÊN HÀNG hoặc đổi SỐ BH (đổi chính cái tên nhận dạng)

Đây là nhóm có hậu quả thật. Đã đo:

```
  Sổ 01–03/09          : 3 dòng · doanh thu 19.000.000
  Sổ 01–10/09, kế toán đổi tên BH100
    "Tủ lạnh Panasonic NR-BX41"  →  "Tủ lạnh Panasonic NR-BX41 (INV)"
                       : 4 dòng · doanh thu 27.000.000     ← ĐẾM HAI LẦN
    THÊM MỚI 1 · không đổi 2 · KHÔNG THẤY 1
    Hai dòng cùng tồn tại:
       'Tủ lạnh Panasonic NR-BX41'        bán 8.000.000  (giá Owner vẫn dính ở đây)
       'Tủ lạnh Panasonic NR-BX41 (INV)'  bán 8.000.000  (Chưa có giá nhập)

  Cùng hiện tượng khi đổi SỐ BH: BH100 → BH100A
                       : 4 dòng · doanh thu 27.000.000
```

Reports **không đoán** rằng hai cái tên đó là cùng một giao dịch — và đó là
**quyết định đã đóng băng có chủ đích** của thiết kế (PRA-002: *"Kế toán đổi tên
hàng trên một dòng → thấy là THÊM MỚI (khoá mới) + KHÔNG THẤY (khoá cũ) — không
đoán ghép"*). Lý do: tự động ghép hai dòng nghi là một sẽ có ngày ghép nhầm hai
đơn thật, và cái sai đó không ai phát hiện được.

Về giá của Owner: nó **không mất**. Nó ở lại đúng dòng có tên cũ. Nếu sau này kế
toán đổi tên **về như cũ**, giá đó **tự động có hiệu lực trở lại** (đã kiểm).
Nhưng dòng mang tên mới thì quay lại "Chưa có giá nhập" và Owner phải gõ lại.

**Hệ thống có báo không?** CÓ — dựng cờ **"KHÔNG THẤY"** cho dòng tên cũ, và số
cờ đó hiện ngay ở cột **"Không thấy"** trên bảng snapshot ở tab **Dữ liệu**.
Nhưng trang **Kinh doanh** — nơi Owner thực sự đọc số — **không nhắc gì**.

---

## 6. Hệ thống có nhớ thay Owner rằng dòng này từng được sửa không?

**MỘT PHẦN.** Cụ thể:

| Owner có thấy được không? | Trả lời | Ở đâu |
|---|---|---|
| Dòng này do Owner gõ giá (MANUAL) | ✔ CÓ | cột "Nguồn giá" = **"Owner đã nhập"** |
| Dòng này Owner đã ghi đè giá máy (MANUAL_OVERRIDE) | ✔ CÓ | cột "Nguồn giá" = **"Owner đã sửa"** |
| Dòng này Owner đã gán lại nhân viên | ✔ CÓ | nhãn **"Owner đã gán"**, di chuột thấy tên sổ ghi |
| Giá máy tính ra **lúc Owner ghi đè** là bao nhiêu | ✘ KHÔNG | *có lưu trong database, chưa hiện ra màn hình nào* |
| Owner sửa **lúc nào** | ✘ KHÔNG | *có lưu, chưa hiện ra* |
| **Nguồn đã đổi SAU KHI Owner sửa dòng này** | ✘ KHÔNG (không nối) | cờ "NGUỒN ĐÃ SỬA" có tồn tại nhưng ở tab Dữ liệu, và nó **không biết** dòng đó từng bị Owner sửa |
| Danh sách "tất cả những dòng tôi từng sửa" | ✘ KHÔNG có bộ lọc riêng | phải xem cột "Nguồn giá" trong "TẤT CẢ DÒNG" |

Vậy nên câu Owner nói — *"tôi có thể quên rằng mình đã sửa dòng này"* — được trả
lời **một nửa**: mở đúng dòng thì thấy ngay là mình đã sửa; nhưng **không có ai
chủ động nhắc** khi sổ mới làm dòng đó thay đổi.

**Điều đó có dẫn tới báo cáo sai âm thầm không?** Theo mục 5 nhóm 1 thì **không**:
những thay đổi giữ nguyên tên dòng đều không làm giá nhập của Owner trở nên sai.
Rủi ro thật nằm ở mục 5 nhóm 2 (đổi tên) và mục 4 (hai dòng cùng tên trong một
đơn) — cả hai đều có cờ, chỉ là cờ không hiện đúng chỗ.

---

## 7. Sang tháng mới, dữ liệu tháng cũ có còn không?

**CÒN NGUYÊN.** Đã chạy đúng kịch bản Owner mô tả (TEST-C):

```
  Tháng 9: upload sổ tháng 9 (6 dòng)
           Owner gõ giá tay dòng BH100                → "Owner đã nhập"
           Owner ghi đè giá máy dòng BH101            → "Owner đã sửa"
           Owner gán lại nhân viên dòng BH102 → "Vinh"
           Owner tick Gia dụng cho "Nồi cơm Cuckoo"

  Tháng 10: upload sổ CHỈ CÓ tháng 10 (2 dòng)
            THÊM MỚI 2 · không đổi 0 · KHÔNG THẤY 0

  KIỂM LẠI THÁNG 9 SAU KHI ĐÃ UPLOAD THÁNG 10:
     số dòng tháng 9              6 → 6            ✔ CÒN NGUYÊN
     BH100 giá nhập  7.800.000 / "Owner đã nhập"   ✔ CÒN
     BH101 giá nhập  5.500.000 / "Owner đã sửa"    ✔ CÒN
     BH102 nhân viên "Vinh" (sổ ghi: VuHanhLy)     ✔ CÒN
     Nồi cơm Cuckoo = GIA_DUNG, tỉ lệ quy đổi 0,080 ✔ CÒN (đã đổi tỉ lệ đúng)
     Tháng 10 có 2 dòng                            ✔ THÊM VÀO, không thay thế
```

**Vì sao chắc chắn:** sổ tháng 10 chỉ "có thẩm quyền" nói về khoảng ngày mà chính
nó chứa (01–31/10). Code lọc theo đúng khoảng ngày đó trước khi so sánh, nên nó
**không thể** kết luận gì về một đơn ngày 15/09. Đây không phải may mắn — nó là
một điều kiện được viết tường minh trong code và có test canh.

**Bốn câu trả lời riêng:**

- `SEP_MANUAL_PRICE` = **PRESERVED**
- `SEP_MANUAL_OVERRIDE` = **PRESERVED**
- `SEP_EMPLOYEE_ATTRIBUTION` = **PRESERVED**
- `SEP_GIA_DUNG` = **PRESERVED**

**Một điểm nữa Owner nên biết:** ngay cả khi kế toán **xoá hẳn một dòng** khỏi
sổ rồi xuất lại, Reports **không xoá** dòng đó khỏi tổng — nó dựng cờ "KHÔNG THẤY"
và để người quyết định. Đã kiểm: 6 dòng, DS 54.000.000 → upload sổ thiếu 1 dòng →
vẫn 6 dòng, DS vẫn 54.000.000, kèm 1 cờ "KHÔNG THẤY". Cố ý như vậy: một dòng bán
thật không được biến mất chỉ vì một lần xuất sổ thiếu.

---

## 8. Reports tính "so tháng trước" bằng cách nào?

Đúng công thức đã đóng băng, không có ngoại lệ:

```
  So tháng trước =  ( Doanh thu bán hàng tháng này  −  Doanh thu bán hàng tháng liền trước )
                    ────────────────────────────────────────────────────────────────────────  × 100 %
                                 Doanh thu bán hàng tháng liền trước
```

Đã kiểm chạy thật sau khi upload tháng 10 lên trên tháng 9:

```
  Các kỳ có dữ liệu   : [(2026,10), (2026,9)]
  Kỳ liền trước của 10/2026 = 09/2026        ✔ đúng
  Doanh thu tháng 9   : 54.000.000
  Doanh thu tháng 10  : 17.500.000
  Reports hiện        : −67,59 %
  Kiểm tay            : (17.500.000 − 54.000.000) / 54.000.000 × 100 = −67,59 %   ✔ KHỚP
```

Xác nhận **KHÔNG** dùng: lợi nhuận, DS quy đổi, số lượng, hay chỉ tiêu — chỉ
**doanh thu bán hàng**.

Trường hợp tháng trước không có dữ liệu (hoặc doanh thu bằng 0): Reports hiện
**"—"** kèm chữ giải thích (*"Chưa có dữ liệu tháng trước"* / *"Tháng trước doanh
thu 0 — không so được"*), **không bao giờ** hiện 0 %, −100 % hay vô cực. Đã kiểm.

`CROSS_MONTH_MOM` = **PASS**.

---

## 9. Những loại dữ liệu nào bị ghi đè và loại nào được bảo lưu?

| Loại dữ liệu | Khi upload file mới thì sao? | Bị ghi đè? | Được bảo lưu? | Có phiên bản? | Hệ quả với Owner |
|---|---|---|---|---|---|
| **File .xlsx Owner tải lên** | dùng xong rồi **XOÁ khỏi máy chủ**; chỉ giữ tên file, kích thước, "dấu vân tay" và dòng tiêu đề | — | **KHÔNG giữ file** | không | Muốn giữ bản gốc thì Owner phải tự lưu trên máy mình |
| **Dòng bán đã chuẩn hoá (sổ gốc)** | dòng y hệt → không ghi gì; dòng đổi nội dung → **ghi thêm một phiên bản mới**, bản cũ vẫn còn | KHÔNG | CÓ | **CÓ** | Luôn tra ngược được "trước kia sổ ghi gì" |
| **Kết quả máy tính ra (lợi nhuận, DS…)** | **ghi thêm một bộ kết quả mới** cho mỗi dòng, mỗi lần chạy | KHÔNG | CÓ | **CÓ** | Đây là phần làm database lớn dần (mục 12) |
| **Con trỏ "bản hiện hành"** | **cập nhật tại chỗ** để trỏ sang bản mới nhất | CÓ (đúng theo thiết kế) | — | không | Đây là thứ quyết định con số Owner nhìn thấy |
| **Giá nhập máy tự tra (AUTO)** | **tra lại từ đầu cho TOÀN BỘ sổ**, kết quả mới ghi thành bản mới | KHÔNG (bản cũ còn) | CÓ | **CÓ** | Nếu Tracking đổi giá, giá AUTO có thể khác lần trước — hệ thống dựng cờ "KẾT QUẢ ĐÃ SỬA" |
| **Giá nhập Owner gõ tay (MANUAL)** | **KHÔNG BỊ ĐỤNG TỚI** — import không đọc, không ghi bảng này | **KHÔNG** | **CÓ, tuyệt đối** | không (giữ 1 quyết định mới nhất) | Gõ một lần, dùng mãi, trừ khi Owner tự sửa hoặc bấm GỠ |
| **Giá Owner ghi đè (MANUAL_OVERRIDE)** | như trên | **KHÔNG** | **CÓ, tuyệt đối** | không | như trên; có lưu kèm giá AUTO tại thời điểm ghi đè |
| **Gán lại nhân viên** | như trên | **KHÔNG** | **CÓ, tuyệt đối** | không | Tên sổ gốc vẫn giữ nguyên bên cạnh, không bị xoá |
| **Tick Gia dụng** | như trên, và **theo MẶT HÀNG** chứ không theo dòng | **KHÔNG** | **CÓ, tuyệt đối** | không | Tick một lần thì **mọi kỳ sau** đều giữ, không phải tick lại |
| **Dữ liệu tháng trước** | sổ tháng mới chỉ có thẩm quyền trong khoảng ngày của chính nó | **KHÔNG** | **CÓ** | — | Tháng cũ mở lại lúc nào cũng còn |
| **Dữ liệu tháng hiện tại** | cộng dồn theo tên dòng; trùng thì bỏ qua, khác thì lên phiên bản mới | KHÔNG | CÓ | **CÓ** | Upload nhiều lần trong tháng không nhân đôi doanh thu |
| **Bằng chứng lịch sử giá (Tracking)** | **tải mới toàn bộ mỗi lần chạy**, dùng xong xoá; chỉ lưu **mã định danh** của lần tải | — | **KHÔNG giữ nội dung** | — | Thẩm quyền giá vẫn thuộc Tracking; Reports chỉ lưu con trỏ để tra ngược |
| **File báo cáo .xlsx đã xuất** | mỗi lần chạy có **mã run riêng**, lưu riêng | **KHÔNG** | CÓ | **CÓ** | Tải lại được từng bản báo cáo cũ ở tab Dữ liệu |

**Không có bảng nào trong tầng import có lệnh xoá.** Chỗ duy nhất được sửa tại
chỗ là bảng con trỏ "bản hiện hành", và mỗi lần nó bị sửa đều có một bản ghi
giải thích vì sao.

---

## 10. Mỗi lần upload có đọc lại lịch sử giá không?

**CÓ — đọc lại toàn bộ, mỗi lần, không có bộ nhớ đệm.** Cụ thể, mười câu hỏi:

| # | Câu hỏi | Trả lời đo được |
|---|---|---|
| 1 | Lịch sử giá có được đọc lại mỗi lần upload? | **CÓ** |
| 2 | Đọc một lần cho cả file? | **CÓ** — tải một ảnh chụp Tracking cho mỗi lần chạy |
| 3 | Một lần cho mỗi mặt hàng? | **KHÔNG** |
| 4 | Một lần cho mỗi DÒNG? | **CÓ** — mỗi dòng sổ tra một lần riêng |
| 5 | Có nạp toàn bộ lịch sử không? | **CÓ** — tải nguyên cả nhánh `purchase_price_history` của Tracking |
| 6 | Có chỉ nạp đúng khoảng ngày / đúng mặt hàng cần không? | **KHÔNG** — không lọc theo ngày, không lọc theo mã |
| 7 | Có bộ nhớ đệm / gom lô không? | **KHÔNG** — mỗi lần tra quét lại toàn bộ danh sách sự kiện |
| 8 | Upload cộng dồn có tra lại giá cho các dòng cũ không? | **CÓ** — tra lại **toàn bộ** sổ, kể cả dòng đã tra tháng trước |
| 9 | Kết quả AUTO lần trước có được dùng lại không? | **KHÔNG** — luôn tính lại từ đầu (cố ý: bằng chứng Tracking có thể đã đổi) |
| 10 | Giá Owner đã gõ có được hỏi trước để khỏi tra thừa không? | **KHÔNG** — import không hề biết bảng quyết định của Owner tồn tại |

Câu 10 nghe như một lỗi nhưng thực ra là **hệ quả của một quyết định thiết kế
tốt**: import và quyết định của Owner được tách hoàn toàn, chính vì thế mà giá
Owner gõ **không thể** bị một lần import làm mất. Cái giá phải trả là tra thừa —
tốn công, không sai số.

Câu 9 cũng cố ý: nếu dùng lại kết quả AUTO cũ, Reports sẽ không phát hiện được
khi Tracking sửa giá quá khứ. Hiện tại nó phát hiện và dựng cờ **"KẾT QUẢ ĐÃ SỬA"**.

---

## 11. Dữ liệu và chi phí tăng theo yếu tố nào?

Ký hiệu: **N** = số dòng của **sổ đang upload** · **ΔN** = số dòng mới thêm so
với lần trước · **U** = số mặt hàng khác nhau · **H** = tổng số sự kiện giá trong
lịch sử Tracking · **M** = số tháng đã lưu.

| Công đoạn | Độ phức tạp | Ghi chú |
|---|---|---|
| Đọc & chuẩn hoá file | **O(N)** | N là **cả sổ**, không phải phần mới |
| Đặt tên dòng (khoá) | **O(N)** | thuần tính toán, không chạm database |
| Tra hiện trạng trong database | **O(N)** đọc, chia lô 400 khoá | **chỉ đọc các đơn có trong sổ**, không quét cả database |
| **Tra giá nhập** | **O(N × H)** | ⬅ **công đoạn tốn nhất**; không cache, không chỉ mục |
| Tải bằng chứng Tracking | **O(H)** tải mạng | tải **toàn bộ** lịch sử mỗi lần chạy |
| Ghi database | **O(N)** ghi | ~2N dòng mới mỗi lần chạy (kết quả + thành viên snapshot) |
| Dò dòng biến mất | **O(số dòng trong khoảng ngày của sổ)** | giới hạn trong đúng kỳ của sổ, **không** cả lịch sử |
| Tra quyết định của Owner | **O(số quyết định Owner)** | đọc trọn 3 bảng mỗi lần tải trang; các bảng này luôn nhỏ |
| Truy vấn "so tháng trước" | **O(số dòng của 2 tháng)** | không đụng tháng khác |
| Danh sách kỳ có dữ liệu | **O(số ngày khác nhau trong toàn bộ lịch sử)** ≈ **O(30 × M)** | vài trăm dòng sau nhiều năm — không đáng kể |

**Không có công đoạn nào quét toàn bộ lịch sử database.** Đó là điều quan trọng
nhất về chi phí: chi phí một lần upload tỉ lệ với **sổ đang upload**, không với
**số liệu đã tích luỹ từ trước**.

**Đo thật công đoạn tốn nhất** (tra giá nhập, chạy trên chính code của nhánh này):

```
  H (sự kiện giá)   N (dòng sổ)    thời gian
           1.000            100         2 ms
           1.000            400         9 ms
          10.000            400       119 ms
          40.000            400       357 ms
```

Quy mô thật của Owner (đo trên hai kỳ mẫu chuẩn lấy từ sổ thật): **351 dòng/tháng**
(kỳ 01/2026, doanh thu 3,56 tỷ) và **180 dòng/tháng** (kỳ 06/2026). Với N ≈ 350
và H vài nghìn sự kiện, mỗi lần upload tốn **dưới một giây** cho công đoạn này.

`CURRENT_SCALE_COST_RISK` = **LOW**.

---

## 12. Sau 4 lần upload cộng dồn trong một tháng, database tăng thế nào?

Đã chạy đúng lịch Owner mô tả (03/09 → 10/09 → 20/09 → 30/09), đếm thật từng bảng:

```
  lần upload        dòng sổ   phiên bản   bộ kết quả   thành viên   dòng      cờ
                              sổ gốc      máy tính     snapshot     hiện hành
  03/09 (01–03)          3          3            3            3         3      0
  10/09 (01–10)          6          6            9            9         6      0
  20/09 (01–20)          8          8           17           17         8      0
  30/09 (01–30)          9          9           26           26         9      0
```

Đọc bảng này:

- **Phiên bản sổ gốc** và **dòng hiện hành**: bằng đúng **9** — số dòng bán thật.
  **CÓ GIỚI HẠN**, không phình. Một dòng không đổi thì **không** sinh bản mới.
- **Bộ kết quả máy tính** và **thành viên snapshot**: **26** dòng cho 9 dòng bán.
  Đây là phần tăng — **tăng tuyến tính theo số lần upload** (mỗi lần upload ghi
  thêm đúng N dòng, với N là kích thước sổ lần đó).
- **Bảng quyết định của Owner**: **không tăng một dòng nào** vì upload.

Quy đổi ra quy mô thật (350 dòng/tháng, 4 lần upload cộng dồn ~90/180/270/350):

```
  Mỗi tháng:  350 dòng bán thật
              → ~350 phiên bản sổ gốc + ~350 dòng hiện hành      (có giới hạn)
              → ~890 bộ kết quả + ~890 thành viên snapshot        (≈ 2,5×)
  Mỗi năm  :  ~4.200 dòng hiện hành
              → ~10.700 bộ kết quả + ~10.700 thành viên snapshot
```

Với PostgreSQL, vài chục nghìn dòng mỗi năm là **rất nhỏ** — không phải mối lo
dung lượng ở bất kỳ nghĩa thực tế nào.

`CUMULATIVE_UPLOAD_STORAGE_GROWTH` = **LINEAR_BY_UPLOAD** đối với hai bảng kết
quả/thành viên; **BOUNDED** đối với dòng sổ gốc, dòng hiện hành và quyết định
của Owner.

**Có tạo dòng kinh tế trùng lặp không?** KHÔNG — số dòng đóng góp vào doanh thu
luôn bằng số dòng bán thật (cấu trúc bảng ép như vậy: mỗi tên dòng chỉ có đúng
một dòng hiện hành). Ngoại lệ duy nhất là trường hợp **đổi tên hàng / đổi số BH**
ở mục 5 nhóm 2, và đó là đổi **tên**, nên nó thành một dòng bán khác chứ không
phải một bản sao.

---

## 13. Có nguy cơ báo cáo sai âm thầm không?

**Mức rủi ro: THẤP.** Không có đường nào làm sai số một cách hoàn toàn không dấu
vết. Có **hai** đường có thể làm số sai mà **trang Kinh doanh không cảnh báo**
(dù tab Dữ liệu có):

### Đường A — kế toán đổi tên hàng hoặc đổi số BH của một dòng đã nhập

- **Hậu quả:** doanh thu và lợi nhuận của dòng đó **bị đếm hai lần**.
  Đo thật: 19.000.000 → **27.000.000** khi lẽ ra vẫn là 19.000.000.
- **Có dấu vết không?** CÓ — cờ **"KHÔNG THẤY"**, hiện ở cột *"Không thấy"* trên
  bảng snapshot ở tab **Dữ liệu**, ngay sau mỗi lần upload.
- **Có nhắc ở trang Kinh doanh không?** **KHÔNG.**
- **Owner tự kiểm được không?** ĐƯỢC, dễ: sau mỗi lần upload, mở tab **Dữ liệu**,
  nhìn cột **"Không thấy"** của dòng snapshot vừa tạo. **Nếu là 0 → không có
  chuyện này.** Khác 0 → bấm "Xem" để biết đơn nào.
- **Đây là thiết kế cố ý**, đã đóng băng ở PRA-002: thà hiện cảnh báo còn hơn tự
  động ghép nhầm hai đơn khác nhau.

### Đường B — một đơn có hai dòng cùng tên hàng, và thứ tự hai dòng đó đổi

- **Hậu quả:** giá nhập Owner gõ chuyển sang dòng khác trong cùng đơn, cùng mặt
  hàng → lợi nhuận của hai dòng đó sai.
- **Có dấu vết không?** CÓ — cờ **"NGUỒN ĐÃ SỬA"** cho cả hai dòng (tab Dữ liệu,
  cột *"Nguồn sửa"*).
- **Tần suất trên dữ liệu thật:** **0 / 531 dòng**. Chưa từng xảy ra.

### Những đường KHÔNG có rủi ro (đã kiểm và loại trừ)

- Upload cộng dồn bình thường → không nhân đôi, không mất giá Owner. ✔
- Upload lại đúng file cũ → không nhân đôi. ✔
- Upload tháng mới → không đụng tháng cũ. ✔
- Đổi số lượng / giá bán / nhân viên / ngày (giữ tên dòng) → giá Owner **vẫn
  đúng về kinh tế**, lợi nhuận tính lại đúng bằng số mới. ✔
- Kế toán xoá một dòng khỏi sổ → Reports **không tự xoá**, chỉ dựng cờ. ✔
- Lỗi database → trang trả lỗi rõ ràng, **không bao giờ** hiển thị thành "chưa
  có dữ liệu". ✔ (đây là bảo vệ tốt nhất chống "trang trống trông như số 0")
- Thiếu giá nhập → hiện **"—" kèm lý do**, **không bao giờ** hiện số 0 giả. ✔

`SILENT_REPORT_ERROR_RISK` = **LOW**.

---

## 14. Có lỗi nào chặn deploy không?

**KHÔNG.**

Đối chiếu từng tiêu chí chặn deploy mà chỉ thị kiểm toán liệt kê:

| Tiêu chí chặn | Kết quả |
|---|---|
| Upload tháng 10 xoá / thay thế tháng 9 | ✔ **KHÔNG XẢY RA** (mục 7) |
| Upload cộng dồn âm thầm làm mất giá Owner gõ | ✔ **KHÔNG XẢY RA** (mục 3, 4) |
| Giá Owner âm thầm gắn nhầm sang dòng khác | ⚠ **CÓ ĐƯỜNG, nhưng 0/531 dòng thật; có cờ** (mục 4) |
| Dòng nguồn đổi rồi âm thầm kế thừa giá cũ làm lợi nhuận sai | ✔ **KHÔNG** — đã chứng minh giá vẫn đúng về kinh tế (mục 5 nhóm 1) |
| "So tháng trước" không chạy được vì không giữ tháng trước | ✔ **KHÔNG XẢY RA** (mục 8) |
| Upload cộng dồn tạo dòng kinh tế trùng → đếm đôi doanh thu | ⚠ **CHỈ khi đổi tên hàng/số BH; có cờ; là thiết kế đã đóng băng** (mục 13 đường A) |

Hai mục ⚠ **không đạt ngưỡng chặn** vì cả hai đều: (a) có cờ cảnh báo hiện ngay
sau mỗi lần upload ở tab Dữ liệu; (b) không phải lỗi do PHB-03 gây ra — đó là
ngữ nghĩa nhận dạng dòng đã được đóng băng và nghiệm thu ở PRA-002; (c) không có
bằng chứng nào cho thấy chúng xảy ra trên dữ liệu thật của Owner.

- `CORRECTNESS_BLOCKERS` = **NONE**
- `PERFORMANCE_BLOCKERS` = **NONE**

**Bằng chứng nền:** `2136 passed, 11 skipped in 80.16s` trên đúng
`d066d227da852b17a57d4a8492fa79c7fc7b2aff`.

---

## 15. Nếu cần sửa, phạm vi sửa nhỏ nhất là gì?

Không bắt buộc trước deploy. Xếp theo giá trị trên công sức. **Phiên này KHÔNG
thực hiện bất kỳ mục nào dưới đây** — chúng chỉ là khuyến nghị để Owner quyết.

### R1 — Đưa cảnh báo lên đúng chỗ Owner đọc (nhỏ, giá trị cao nhất)

Trang **Kinh doanh** hiện một dòng nhắc khi kỳ đang xem có cờ chưa xử lý:

> *"Kỳ này có 1 dòng bị đánh dấu KHÔNG THẤY trong lần nhập sổ mới nhất — con số
> có thể đang đếm hai lần. Xem chi tiết ở tab Dữ liệu."*

Phạm vi: **một câu truy vấn đếm + một dòng chữ trên template.** Không đổi
database, không đổi luật nghiệp vụ, không đổi con số nào. Việc này đóng **cả hai**
đường rủi ro ở mục 13.

### R2 — Hiện đủ dấu vết một lần Owner can thiệp (nhỏ)

Trên cột "Nguồn giá", khi là "Owner đã sửa" thì hiện thêm (dạng chú thích khi di
chuột) **giá máy tính lúc đó** và **thời điểm sửa**. Hai giá trị này **đã có sẵn
trong database**, chỉ chưa được hiển thị. Phạm vi: **chỉ tầng hiển thị**.

### R3 — Bộ lọc "những dòng tôi đã sửa" (nhỏ)

Thêm một nút lọc thứ tư bên cạnh "CHƯA CÓ GIÁ NHẬP" / "CHƯA XÁC ĐỊNH NHÂN VIÊN" /
"TẤT CẢ DÒNG". Trả lời trực tiếp câu *"tôi đã sửa những dòng nào?"*.

### R4 — Bỏ tra giá thừa (chỉ khi nào chậm thật)

Hiện chưa cần: dưới một giây ở quy mô thật. Nếu sau này sổ lớn hơn nhiều, sửa
nhỏ nhất là **đánh chỉ mục lịch sử giá theo mã hàng một lần cho mỗi lần chạy**
(đổi `O(N × H)` thành `O(N + H)`). Sửa **trong đúng một hàm**, không đổi kết quả.

### KHÔNG khuyến nghị

- ✘ Tự động ghép dòng khi kế toán đổi tên hàng — sẽ có ngày ghép nhầm hai đơn thật.
- ✘ Đổi cách đặt tên dòng (khoá nghiệp vụ) — đây là nền của toàn bộ tính bền vững
  của quyết định Owner; động vào là rủi ro lớn hơn nhiều lần vấn đề nó giải quyết.
- ✘ Dựng hệ thống nhật ký kiểm toán đầy đủ — quá lớn so với vấn đề; R2 + R3 đủ.

---

## 16. Có thể tiếp tục production E2E chưa?

**RỒI. `SAFE_TO_CONTINUE_TO_PRODUCTION_E2E = YES`.**

Đề nghị Owner làm ba việc nhỏ trong lần chạy thật đầu tiên (không cần sửa code):

1. Sau **mỗi** lần upload, mở tab **Dữ liệu** và nhìn cột **"Không thấy"** của
   dòng snapshot vừa tạo. **Bằng 0 là mọi thứ bình thường.**
2. Kiểm chéo một lần: upload sổ 01–03, gõ giá tay một dòng, upload sổ 01–10, mở
   lại đúng dòng đó và xác nhận vẫn thấy "Owner đã nhập" + đúng con số.
3. Khi sang tháng mới, mở lại tháng cũ một lần để tự mắt xác nhận số và các sửa
   tay còn nguyên.

---

## Phụ lục — Bảng kết quả phiên kiểm toán

```
TARGET_GATE                              = PASS
AUDIT_BRANCH                             = claude/phb-03-import-audit-elqcnb
                                           (nội dung giống hệt
                                            claude/phb-03-bounded-semantics-repair-685gf4)
AUDIT_HEAD                               = d066d227da852b17a57d4a8492fa79c7fc7b2aff

IMPORT_MODEL                             = SNAPSHOT + phiên bản APPEND-ONLY
                                           + UPSERT con trỏ hiện hành
                                           (KHÔNG phải REPLACE_PERIOD, KHÔNG có DELETE)

SAME_MONTH_STABLE_LINE_OVERRIDE          = PRESERVED
SOURCE_CHANGED_AFTER_OVERRIDE_DETECTION  = YES cho "nguồn đã đổi" (cờ SOURCE_CHANGED),
                                           NO cho việc nối nó với "dòng này Owner
                                           từng sửa"; cờ chỉ hiện ở tab Dữ liệu
CAN_OWNER_SEE_PREVIOUS_INTERVENTION      = PARTIAL
OVERRIDE_KEY_SAFETY                      = NON_BLOCKING_CONCERN
                                           (chỉ khi một đơn có ≥2 dòng CÙNG tên hàng
                                            và thứ tự đổi; đo thật: 0/531 dòng sổ thật;
                                            có cờ SOURCE_CHANGED)

SEP_AFTER_OCT_UPLOAD                     = PRESERVED
SEP_MANUAL_PRICE                         = PRESERVED
SEP_MANUAL_OVERRIDE                      = PRESERVED
SEP_EMPLOYEE_ATTRIBUTION                 = PRESERVED
SEP_GIA_DUNG                             = PRESERVED
CROSS_MONTH_MOM                          = PASS

AUTO_PRICE_RECOMPUTED_ON_CUMULATIVE_UPLOAD = YES (toàn bộ sổ, kể cả dòng Owner đã sửa)
PURCHASE_HISTORY_READ_PATTERN            = tải TOÀN BỘ lịch sử Tracking mỗi lần chạy
                                           (không lọc ngày/mã) + quét tuyến tính
                                           MỘT LẦN CHO MỖI DÒNG ⇒ O(N × H);
                                           không cache, không chỉ mục, không dùng lại
                                           kết quả AUTO lần trước
OWNER_OVERRIDE_LOOKUP_PATTERN            = đọc trọn 3 bảng quyết định Owner đúng MỘT
                                           lần cho mỗi lần dựng kỳ (mỗi lần tải trang),
                                           ghép trong Python; O(số quyết định Owner);
                                           đường IMPORT KHÔNG đọc các bảng này

CUMULATIVE_UPLOAD_STORAGE_GROWTH         = LINEAR_BY_UPLOAD
                                           (order_line_result_version, snapshot_line:
                                            +N dòng mỗi lần upload)
                                           BOUNDED
                                           (order_line_source_version,
                                            order_line_current, 3 bảng Owner)
COMPUTE_COST_PATTERN                     = đọc/chuẩn hoá O(N) · tra hiện trạng O(N)
                                           theo lô 400 · TRA GIÁ O(N × H) ⟵ tốn nhất
                                           · ghi O(N) · dò vắng mặt O(dòng trong kỳ)
                                           · MoM O(dòng 2 tháng)
                                           · KHÔNG có công đoạn nào O(toàn bộ lịch sử)
CLOUD_COST_AMOUNT                        = NOT_DERIVABLE_FROM_REPO
CURRENT_SCALE_COST_RISK                  = LOW
                                           (đo thật: 351 dòng/tháng; tra giá <1 giây;
                                            ~10.700 dòng kết quả/năm)
SILENT_REPORT_ERROR_RISK                 = LOW

CORRECTNESS_BLOCKERS                     = NONE
PERFORMANCE_BLOCKERS                     = NONE
NON_BLOCKING_FINDINGS                    =
  NB-1  Đổi tên hàng / đổi số BH giữa hai lần upload ⇒ đếm hai lần doanh thu
        (19.000.000 → 27.000.000 trong phép đo). CÓ cờ NOT_SEEN ở tab Dữ liệu;
        KHÔNG có cảnh báo ở trang Kinh doanh. Là ngữ nghĩa đã đóng băng ở PRA-002
        ("không đoán ghép"), không phải hồi quy của PHB-03.
  NB-2  Cờ SOURCE_CHANGED không nối với "dòng này Owner từng sửa"; Owner không
        được nhắc chủ động.
  NB-3  Đơn có ≥2 dòng cùng tên hàng + đổi thứ tự ⇒ giá Owner đi theo vị trí.
        Đo tần suất trên sổ thật: 0/531.
  NB-4  auto_price_at_entry / entered_at / assigned_at ĐÃ LƯU nhưng chưa hiển thị
        ở bất kỳ màn hình nào.
  NB-5  Tra lại giá AUTO cho cả những dòng Owner đã gõ tay — thừa, không sai số.
  NB-6  Tra giá O(N × H), không cache. Không đáng lo ở quy mô hiện tại.
  NB-7  File .xlsx gốc Owner tải lên bị XOÁ sau khi chạy; chỉ giữ dấu vân tay và
        tiêu đề. Owner tự lưu bản gốc nếu cần đối chiếu về sau.

OWNER_DECISIONS_REQUIRED                 =
  OD-A  Có làm R1 (nhắc cờ "Không thấy" ngay trên trang Kinh doanh) TRƯỚC hay SAU
        lần chạy production đầu tiên? Khuyến nghị: SAU — chưa cần để deploy, và
        lần chạy thật sẽ cho biết cờ đó có khác 0 trên dữ liệu thật hay không.
  OD-B  Có muốn R2/R3 (hiện đủ dấu vết + bộ lọc "dòng tôi đã sửa") không?
  OD-C  Xác nhận chấp nhận hành vi "đổi tên hàng ⇒ thành dòng mới, không tự ghép"
        (đây là quy tắc đã đóng băng, không phải lỗi mới).

SAFE_TO_CONTINUE_TO_PRODUCTION_E2E       = YES
SCOPE_DRIFT                              = NO
AUDIT_REPORT                             = docs/reviews/PHB-03-import-lifecycle-persistence-audit.md
NEXT_VERTICAL_ACTION                     = Chạy production E2E trên nhánh ứng viên với
                                           sổ thật, kèm ba bước tự kiểm ở mục 16.
                                           Sau lần chạy đầu, đọc cột "Không thấy" và
                                           "Nguồn sửa" ở tab Dữ liệu để quyết OD-A.
```

---

## Phụ lục — Bằng chứng đã thực thi

| Mã | Nội dung | Kết quả |
|---|---|---|
| E-0 | Cổng mục tiêu: `git rev-parse HEAD` | `d066d227da852b17a57d4a8492fa79c7fc7b2aff`; `git diff --stat origin/claude/phb-03-bounded-semantics-repair-685gf4 HEAD` **rỗng**; cây làm việc sạch |
| E-1 | Toàn bộ test của repo trên đúng HEAD | `2136 passed, 11 skipped in 80.16s` |
| E-2 | TEST-A: 01–03/09 → gõ giá tay → 01–10/09 | PASS ×3 (giá giữ, không nhân đôi dòng, bảng override không bị đụng) |
| E-3 | TEST-B: 5 kiểu đổi nguồn sau khi Owner sửa | tất cả giữ khoá, giữ giá, dựng cờ SOURCE_CHANGED; lợi nhuận tính lại đúng bằng số liệu mới |
| E-4 | TEST-C: tháng 9 (4 loại sửa tay) → upload tháng 10 | PASS ×5 (tháng 9 còn 6/6 dòng; MANUAL, MANUAL_OVERRIDE, gán nhân viên, Gia dụng đều PRESERVED) |
| E-5 | TEST-D: MoM tháng 10 so tháng 9 | PASS — −67,59 %, khớp phép tính tay; kỳ trước rỗng → "—" kèm chữ |
| E-6 | TEST-E: trùng/đảo dòng cùng (đơn, mặt hàng) | E1/E2 tái hiện việc override đi theo vị trí; E3 PASS (override không lan sang đơn khác) |
| E-7 | Đổi tên hàng / đổi số BH giữa hai lần upload | doanh thu 19.000.000 → 27.000.000, 1 cờ `NOT_SEEN_IN_LATEST_SNAPSHOT` |
| E-8 | Upload lại đúng file cũ | `duplicate_of` được đặt, doanh thu không đổi |
| E-9 | Sổ upload lại thiếu một dòng | dòng vẫn trong tổng, 1 cờ `NOT_SEEN`, không xoá gì |
| E-10 | Tăng trưởng database qua 4 lần upload cộng dồn | 9 dòng bán → 9 phiên bản sổ gốc / 9 dòng hiện hành / 26 bộ kết quả / 26 thành viên snapshot |
| E-11 | Đo chi phí tra giá nhập | H=1.000/N=400 → 9 ms; H=40.000/N=400 → 357 ms (quan hệ tuyến tính theo N × H) |
| E-12 | Đếm tần suất "một đơn có ≥2 dòng cùng tên hàng" trên sổ thật | **0 / 531** dòng (`period_2026_01` 351 dòng + `period_2026_06` 180 dòng) |

*Toàn bộ kịch bản E-2…E-12 chạy trên chính tầng import, tầng lưu quyết định và
tầng đọc của nhánh này, với database tạm trong bộ nhớ. Không có dòng code
production nào bị sửa trong phiên này.*
