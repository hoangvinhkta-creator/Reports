# PHB-03 — Phân Loại Nghiệp Vụ Các Lý Do "CẦN KIỂM TRA" (PENDING)

**Loại phiên:** READ-ONLY BUSINESS AUDIT (chỉ đọc, không sửa code)
**Ngày:** 2026-09-04
**Nhánh review:** `claude/phb-03-pending-reason-audit-ap9z60`
**Commit được soi:** `60adb2ec22efdb4967d6971bbee852db660c8c18`
(trùng đúng `EXPECTED_HEAD`; nội dung y hệt nhánh
`claude/phb-03-summary-employee-parity-7x3uid`, khác 0 dòng)
**TARGET_GATE:** `PASS`
**Mã sản xuất bị sửa:** KHÔNG (`PRODUCTION_CODE_CHANGED = NO`)

---

## 0. Đọc bản này thế nào

Bản này viết cho chủ dự án, không viết cho lập trình viên. Mỗi khi buộc phải
dùng một từ kỹ thuật, từ đó được giải thích ngay tại chỗ bằng tiếng Việt.

Ba từ xuất hiện xuyên suốt, nên giải thích trước:

| Từ | Nghĩa trong bản này |
|---|---|
| **Dòng hàng** | Một dòng trong sổ chi tiết bán hàng: một mặt hàng, trên một số chứng từ (Số BH), bán ngày nào, số lượng bao nhiêu, giá bao nhiêu. |
| **AUTO / PENDING** | Hai trạng thái duy nhất mà hệ thống dán lên một dòng hàng. `AUTO` = "không có gì cần hỏi". `PENDING` = "cần kiểm tra". Trên màn hình, `PENDING` hiện là **CẦN KIỂM TRA**. |
| **Lý do (reason)** | Mã ngắn giải thích **vì sao** một dòng bị dán `PENDING`. Một dòng có thể mang nhiều lý do cùng lúc. |

Một điều cần nắm ngay, vì toàn bộ vấn đề nằm ở đó:

> **`PENDING` không phải một lý do. `PENDING` chỉ là kết quả của phép cộng:
> "dòng này có ít nhất một lý do nào đó" thì dán `PENDING`.**

Câu lệnh thật trong mã nguồn đúng một dòng
(`app/modules/exporting/excel_exporter.py:71-73`):

```
status = "PENDING" nếu có bất kỳ lý do nào, ngược lại "AUTO"
```

Hệ thống hiện đang dùng **kết quả phép cộng đó** làm luật nghiệp vụ để quyết
định có được tính lợi nhuận hay không. Đó là chỗ sai.

---

## 1. Kết luận ngắn gọn (nếu chỉ đọc một mục)

1. Có **19 mã lý do** đang còn hiệu lực có thể khiến một dòng bị `PENDING`
   (cộng 2 mã cũ chỉ còn dùng để đọc lại lịch sử → 21 mã tổng cộng).
   Tập này **đóng** — đã đếm hết, không còn mã nào ngoài danh sách.
2. Trong 19 mã đó, **không mã nào** là lý do kinh tế thật sự khiến không thể
   tính lợi nhuận, **một khi đã có giá bán hợp lệ và giá nhập hợp lệ**.
   Chỉ có **3 tình huống** cần chủ dự án quyết định trước khi chốt hẳn
   (dòng trùng, số lượng ≤ 0, và trường hợp file cấu hình KPI hỏng).
3. **Nguyên nhân gốc của lỗi PHB-03 nặng hơn báo cáo review ban đầu.**
   Không chỉ là "cửa chặn quá rộng". Nó là một **vòng lặp tự khoá**:
   dòng bị `PENDING` **chính vì thiếu giá nhập**; chủ dự án nhập giá vào;
   nhưng nhãn `PENDING` đã được đóng dấu từ lúc chạy máy và **không bao giờ
   được tính lại**. Cửa chặn đọc cái nhãn cũ đó và tiếp tục từ chối.
   ⟹ **Với đúng những dòng mà tính năng nhập giá tay sinh ra để cứu, tính
   năng đó không bao giờ có tác dụng.**
4. Hai ô đếm mà PHB-03 xây để báo cho chủ dự án biết "còn bao nhiêu dòng chỉ
   thiếu mỗi giá nhập" đang **luôn bằng 0 theo cấu tạo**, và toàn bộ số dòng
   thiếu bị dồn sang ô "Review Queue chặn — nhập giá không cứu được".
   Nghĩa là màn hình đang nói với chủ dự án điều **ngược lại sự thật**.
5. Đã có sẵn trong cơ sở dữ liệu **cột lưu danh sách lý do** của từng dòng.
   Việc sửa **không cần** đổi cấu trúc dữ liệu, **không cần** chạy lại máy,
   **không cần** đụng vào Product Identity, Tracking hay Review Queue.

---

## 2. Toàn bộ danh sách lý do đang tồn tại

Danh sách này lấy từ mã nguồn thật, không lấy từ tên trong test.
Kiểm chứng bằng lệnh thực thi (bằng chứng E1, chạy trên chính commit này):

```
PriceResolutionReason:  10
validation CATEGORIES:   8  ['Duplicate', 'EmployeeMapping', 'Missing',
                             'Missing.PurchasePrice', 'OrderInconsistency',
                             'SourceClassification', 'Suspicious',
                             'Suspicious.ERP']
display labels:         21
retired:                ['Pending.accounting_profit',
                         'Pending.accounting_purchase_price']
live reason codes:      19
unlabelled?             set()          ← không mã nào bị bỏ sót nhãn
```

### Nhóm A — 10 mã "không tra được giá nhập tự động"

Cả 10 mã này nói **đúng một chuyện**: máy đã đi tra giá nhập và không tra ra.
Chúng khác nhau ở chỗ **tắc ở khâu nào**, chứ không khác nhau về hệ quả kinh tế.

| Mã | Nhãn tiếng Việt đang hiện | Thực tế nghĩa là gì |
|---|---|---|
| `SALE_DATE_MISSING` | Dòng chưa có ngày bán | Không có ngày thì không biết tra bảng giá của thời điểm nào |
| `RAW_PRODUCT_IDENTITY_EMPTY` | Dòng chưa ghi tên sản phẩm | Ô "Tên hàng trên chứng từ" để trống |
| `IDENTITY_SOURCES_UNAVAILABLE` | Chưa có dữ liệu để nhận diện sản phẩm | Chưa nạp được danh mục sản phẩm |
| `IDENTITY_UNRESOLVED` | Chưa nhận diện sản phẩm | Có tên hàng nhưng không khớp được vào danh mục nào |
| `IDENTITY_REQUIRES_CONFIRMATION` | Sản phẩm cần người xác nhận trước khi lấy giá | Khớp được nhiều hơn một sản phẩm, máy không tự chọn |
| `TRACKING_HISTORY_SOURCE_UNAVAILABLE` | Chưa có nguồn giá lịch sử Tracking | Chưa nạp được file lịch sử giá |
| `TRACKING_HISTORY_PENDING` | Thiếu giá lịch sử Tracking | Có file nhưng không dựng lại được giá tại ngày bán |
| `VENDOR_SOURCE_NOT_AUTHORIZED` | Nguồn giá nhà cung cấp chưa được cho phép dùng | Nguồn giá đó chưa được duyệt |
| `PUBLIC_PURCHASE_SOURCE_UNAVAILABLE` | Chưa có bảng giá PP | Chưa nạp bảng giá mua công khai |
| `PUBLIC_PURCHASE_NO_PRICE_AT_SALE_DATE` | Thiếu giá PP tại ngày bán | Có bảng giá nhưng không có dòng nào phủ ngày bán đó |

### Nhóm B — 8 mã từ hàng chờ kiểm tra (Review Queue)

| Mã | Nhãn tiếng Việt | Có chặn dòng không? |
|---|---|---|
| `Missing` | Thiếu dữ liệu bắt buộc trên dòng | CÓ (5 trường khác nhau gộp chung một mã) |
| `Missing.PurchasePrice` | Thiếu giá mua tham chiếu | CÓ (cố ý ép vào dù mức chỉ là INFO) |
| `Suspicious` | Bất thường | CÓ (4 quy tắc khác nhau gộp chung một mã) |
| `Suspicious.ERP` | ERP báo lợi nhuận âm | **KHÔNG** — mức INFO nên bị bỏ qua |
| `OrderInconsistency` | Đơn có thông tin không thống nhất giữa các dòng | CÓ, và **lây sang mọi dòng của đơn đó** |
| `SourceClassification` | Nguồn khách ghi tay khác kết quả tự động | Về lý thuyết có; thực tế **0 lần** vì chưa có màn hình nào ghi giá trị này |
| `Duplicate` | Có dòng trùng nội dung trong sổ | CÓ |
| `EmployeeMapping` | Chưa khớp được nhân viên với danh sách | CÓ với tiêu chí F3/F4/F5/F6; **không** với F2 |

### Nhóm C — 1 mã "kết quả còn trống" (+2 mã đã nghỉ hưu)

| Mã | Nhãn | Ghi chú |
|---|---|---|
| `Pending.eligible_kpi_profit` | Thiếu lợi nhuận KPI | **Còn hiệu lực** |
| `Pending.accounting_purchase_price` | Thiếu giá nhập kế toán | Đã nghỉ hưu (DEC-PAN-001) — chỉ đọc lịch sử |
| `Pending.accounting_profit` | Thiếu lợi nhuận kế toán | Đã nghỉ hưu (DEC-PAN-001) — chỉ đọc lịch sử |

### Ghi chú quan trọng: 19 mã nhưng 31 tình huống

Bốn mã ở Nhóm B **gộp nhiều tình huống rất khác nhau vào một chữ duy nhất**,
và **chi tiết bị mất khi lưu xuống cơ sở dữ liệu** (phần giải thích chi tiết
đi vào cột "Chi tiết" của file Excel, **không** đi vào cột danh sách lý do):

- `Missing` gộp 5 trường: **ngày**, **số chứng từ**, **nhân viên**,
  **số lượng**, **doanh số**.
- `Suspicious` gộp 4 quy tắc: **số lượng ≤ 0**, **giá bán = 0**,
  **giá nhập > giá bán**, **lợi nhuận kế toán âm**.
- `EmployeeMapping` gộp 5 tiêu chí F2…F6.
- `OrderInconsistency` gộp 2 tiêu chí: **khác nhân viên** và **khác ngày**.

Tổng cộng **19 mã đang che 31 tình huống thật khác nhau**.

Đây là một ràng buộc thật cho việc sửa: hai mã `Missing` và `Suspicious`
**không phân loại an toàn được** nếu chỉ đọc cái mã đó. Mục 9 nói cách xử lý.

---

## 3. Bảng phân loại nghiệp vụ đầy đủ

Cách đọc các cột:

- **TIN GIÁ BÁN / TIN GIÁ NHẬP / TIN GÁN NHÂN VIÊN** — lý do này có làm ta
  nghi ngờ con số đó không?
- **RỦI RO ĐẾM ĐÚP** — có nguy cơ cộng hai lần cùng một khoản tiền không?
- **GIÁ TAY CỨU ĐƯỢC?** — chủ dự án nhập một giá nhập hợp lệ vào thì hết
  nghi ngờ kinh tế chưa?
- **PHÂN LOẠI LỢI NHUẬN**:
  `CHẶN` (BLOCK_PROFIT) · `CHỈ CẢNH BÁO` (WARNING_ONLY) ·
  `TRIỆU CHỨNG` (DERIVED_SYMPTOM) · `CHỜ CHỦ DỰ ÁN` (NOT_ENOUGH_EVIDENCE)
- **PHÂN LOẠI KPI NHÂN VIÊN**:
  `CHẶN KPI` (BLOCK_EMPLOYEE_KPI) · `CHO PHÉP` (ALLOW_EMPLOYEE_KPI) ·
  `KHÔNG LIÊN QUAN` (NOT_APPLICABLE) · `CHỜ CHỦ DỰ ÁN`

### 3.1 Nhóm A — 10 mã giá nhập tự động

| MÃ | NGUYÊN NHÂN GỐC | HIỆN ĐANG GÂY RA | TIN GIÁ BÁN | TIN GIÁ NHẬP | TIN GÁN NHÂN VIÊN | ĐẾM ĐÚP | GIÁ TAY CỨU ĐƯỢC? | PHÂN LOẠI LỢI NHUẬN | PHÂN LOẠI KPI NHÂN VIÊN | LÝ DO | THẨM QUYỀN |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `SALE_DATE_MISSING` | Ô ngày hạch toán trống | PENDING + không tra được giá | TIN | KHÔNG TIN (chưa có) | TIN | KHÔNG | CÓ | `TRIỆU CHỨNG` | `CHO PHÉP` | Dòng không có ngày đã **rơi khỏi mọi kỳ báo cáo** ở tầng truy vấn (`sale_date IS NOT NULL`), nên nó không bao giờ vào tổng dù cửa chặn có mở hay không | `business_queries._period` + PRA-003 |
| `RAW_PRODUCT_IDENTITY_EMPTY` | Ô tên hàng trống | PENDING | TIN | KHÔNG TIN (chưa có) | TIN | KHÔNG | CÓ | `TRIỆU CHỨNG` | `CHO PHÉP` | Công thức lợi nhuận không cần **tên** hàng. Khoá lưu giá tay là `sha256(tên hàng)`, chuỗi rỗng vẫn ra khoá hợp lệ | `app/history/keys.py:70` |
| `IDENTITY_SOURCES_UNAVAILABLE` | Chưa nạp danh mục | PENDING | TIN | KHÔNG TIN (chưa có) | TIN | KHÔNG | CÓ | `TRIỆU CHỨNG` | `CHO PHÉP` | Chỉ nói "chưa tra được", không nói con số nào sai | Mục 4 bản này |
| `IDENTITY_UNRESOLVED` | Tên hàng không khớp danh mục | PENDING | TIN | KHÔNG TIN (chưa có) | TIN | KHÔNG | CÓ | `TRIỆU CHỨNG` | `CHO PHÉP` | Xem mục 4 — nhận diện chỉ cần để **TÌM** giá, không cần để **TÍNH** | Mục 4 bản này |
| `IDENTITY_REQUIRES_CONFIRMATION` | Khớp nhiều candidate | PENDING | TIN | KHÔNG TIN (chưa có) | TIN | KHÔNG | CÓ | `TRIỆU CHỨNG` | `CHO PHÉP` | Như trên | Mục 4 bản này |
| `TRACKING_HISTORY_SOURCE_UNAVAILABLE` | Chưa nạp file lịch sử giá | PENDING | TIN | KHÔNG TIN (chưa có) | TIN | KHÔNG | CÓ | `TRIỆU CHỨNG` | `CHO PHÉP` | Sự cố nạp dữ liệu, không phải sự thật về dòng hàng | `composition.py` |
| `TRACKING_HISTORY_PENDING` | Không dựng lại được giá tại ngày bán | PENDING | TIN | KHÔNG TIN (chưa có) | TIN | KHÔNG | CÓ | `TRIỆU CHỨNG` | `CHO PHÉP` | Đây **chính là** trường hợp DEC-PHB02-02 §2 dựng đường nhập tay để cứu | `DEC-PHB02-02` §2 |
| `VENDOR_SOURCE_NOT_AUTHORIZED` | Nguồn giá chưa được duyệt | PENDING | TIN | KHÔNG TIN (chưa có) | TIN | KHÔNG | CÓ | `TRIỆU CHỨNG` | `CHO PHÉP` | Vấn đề thẩm quyền nguồn, không phải vấn đề dòng hàng | `DEC-154` |
| `PUBLIC_PURCHASE_SOURCE_UNAVAILABLE` | Chưa nạp bảng giá PP | PENDING | TIN | KHÔNG TIN (chưa có) | TIN | KHÔNG | CÓ | `TRIỆU CHỨNG` | `CHO PHÉP` | Như trên | `DEC-154` |
| `PUBLIC_PURCHASE_NO_PRICE_AT_SALE_DATE` | Bảng giá không phủ ngày bán | PENDING | TIN | KHÔNG TIN (chưa có) | TIN | KHÔNG | CÓ | `TRIỆU CHỨNG` | `CHO PHÉP` | Như trên | `DEC-154` |

> **Vì sao cả 10 mã đều là `TRIỆU CHỨNG` chứ không phải `CHẶN`?**
> Chúng là **nguyên nhân gốc** của việc *thiếu giá nhập*. Nhưng với **cửa chặn
> lợi nhuận**, thứ cần kiểm tra là **có giá nhập hay không**, chứ không phải
> *vì sao lúc trước không tra ra*. Khi chủ dự án đã nhập một giá hợp lệ, cả
> 10 lời giải thích đó trở thành lịch sử. Giữ chúng làm cửa chặn nghĩa là
> phạt chủ dự án vì một việc chính chủ dự án vừa sửa xong.

### 3.2 Nhóm B — 8 mã hàng chờ kiểm tra

| MÃ | NGUYÊN NHÂN GỐC | HIỆN ĐANG GÂY RA | TIN GIÁ BÁN | TIN GIÁ NHẬP | TIN GÁN NHÂN VIÊN | ĐẾM ĐÚP | GIÁ TAY CỨU ĐƯỢC? | PHÂN LOẠI LỢI NHUẬN | PHÂN LOẠI KPI NHÂN VIÊN | LÝ DO | THẨM QUYỀN |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `Missing` — thiếu **số lượng** | Ô SL trống | PENDING | TIN | TIN | TIN | KHÔNG | KHÔNG | **`CHẶN`** | `KHÔNG LIÊN QUAN` | Số lượng là một **thừa số** của công thức lợi nhuận. Thiếu thật thì không có phép nhân nào đúng | `DEC-143` |
| `Missing` — thiếu **doanh số** | Ô doanh số trống | PENDING | TIN có điều kiện | TIN | TIN | KHÔNG | KHÔNG | `CHỜ CHỦ DỰ ÁN` | `KHÔNG LIÊN QUAN` | Doanh số **không** nằm trong công thức lợi nhuận (đơn giá và SL mới nằm), nhưng thiếu nó là dấu hiệu dòng lỗi | `DEC-114` |
| `Missing` — thiếu **ngày** | Ô ngày trống | PENDING | TIN | TIN | TIN | KHÔNG | KHÔNG | `TRIỆU CHỨNG` | `CHO PHÉP` | Dòng đã rơi khỏi mọi kỳ ở tầng truy vấn | `business_queries._period` |
| `Missing` — thiếu **số chứng từ** | Ô Số BH trống | PENDING | TIN | TIN | TIN | KHÔNG | KHÔNG | `CHỜ CHỦ DỰ ÁN` | `CHỜ CHỦ DỰ ÁN` | Không có số chứng từ thì không có khoá đơn để nhóm; cần chủ dự án nói dòng đó là gì | — |
| `Missing` — thiếu **nhân viên** | Ô NVBH trống / chưa map | PENDING | TIN | TIN | **KHÔNG TIN** | KHÔNG | KHÔNG | `CHỈ CẢNH BÁO` | **`CHẶN KPI`** | Không biết ai bán **không làm sai một đồng nào** của con số lợi nhuận; nó chỉ làm ta không biết cộng vào KPI của ai | `DEC-104` |
| `Missing.PurchasePrice` | `price_source = "Pending"` trên dòng | PENDING (ép vào dù mức INFO) | TIN | KHÔNG TIN (chưa có) | TIN | KHÔNG | **CÓ** | `TRIỆU CHỨNG` | `CHO PHÉP` | Đây là **bản gộp** của đúng 10 mã Nhóm A. Chính là cái mà giá tay sinh ra để lấp | `DEC-128` §1 + `DEC-PHB02-02` §2 |
| `Suspicious` — **số lượng ≤ 0** | SL = 0 hoặc âm | PENDING | TIN | TIN | TIN | CÓ THỂ (SL âm = trả hàng) | Không đổi gì | **`CHỜ CHỦ DỰ ÁN`** | `CHO PHÉP` | SL = 0 có thể là "thật sự không bán cái nào" (lợi nhuận = 0, đúng) **hoặc** "quên ghi số lượng" (lợi nhuận chưa xác định). Hai nghĩa dẫn tới hai kết quả khác nhau. SL âm nhiều khả năng là hàng trả — dấu âm có đúng ý chủ dự án không thì chưa ai chốt | Mục 5 bản này |
| `Suspicious` — **giá bán = 0** | Hàng tặng kèm | PENDING | TIN (0 là số thật) | TIN | TIN | KHÔNG | Không đổi gì | `CHỈ CẢNH BÁO` | `CHO PHÉP` | Xem mục 5 — bằng chứng thật đã xác nhận đây là dữ liệu đúng | Mục 5 bản này |
| `Suspicious` — **giá nhập > giá bán** | Bán dưới giá vốn | PENDING | TIN | TIN | TIN | KHÔNG | Không đổi gì | `CHỈ CẢNH BÁO` | `CHO PHÉP` | Lợi nhuận vẫn tính được (ra số âm) và con số âm đó **là sự thật kinh doanh**. Ẩn nó đi làm báo cáo đẹp hơn thực tế | `DEC-128` |
| `Suspicious` — **lợi nhuận kế toán âm** | Kết quả phép trừ ra âm | PENDING | TIN | TIN | TIN | KHÔNG | Không đổi gì | `TRIỆU CHỨNG` | `CHO PHÉP` | Đây là **hệ quả** của quy tắc ngay trên, không phải một phát hiện độc lập | `DEC-128` |
| `Suspicious.ERP` | Cột "Lợi nhuận" của ERP âm | **KHÔNG gây PENDING** (mức INFO) | TIN | TIN | TIN | KHÔNG | Không đổi gì | `CHỈ CẢNH BÁO` | `CHO PHÉP` | Xem mục 5 — con số ERP này đã bị loại khỏi mọi báo cáo bởi `D1`, và cấu hình đặt nó ở mức INFO nên nó **vốn đã không chặn** | `DEC-128` §2 + `D1` + `config/validation.yaml` |
| `OrderInconsistency` — **khác nhân viên** | Một đơn có nhiều tên NVBH | PENDING **cho toàn bộ đơn** | TIN | TIN | TIN (ở cấp dòng) | KHÔNG | Không đổi gì | `CHỈ CẢNH BÁO` | `CHO PHÉP` | Xem mục 6 — báo cáo Nhân viên V1 nhóm theo **nhân viên của từng dòng**, nên vấn đề này không làm sai việc gán KPI ở cấp dòng | `DEC-128` §4 |
| `OrderInconsistency` — **khác ngày** | Một đơn có nhiều ngày | PENDING **cho toàn bộ đơn** | TIN | TIN | TIN | KHÔNG | Không đổi gì | `CHỈ CẢNH BÁO` | `CHO PHÉP` | Kỳ báo cáo tính theo ngày của **từng dòng**, không theo ngày của đơn | `business_queries._period` |
| `SourceClassification` | Nguồn khách ghi tay khác kết quả tự động | PENDING **cho toàn bộ đơn** (thực tế 0 lần) | TIN | TIN | TIN | KHÔNG | Không đổi gì | `CHỈ CẢNH BÁO` | `CHO PHÉP` | Xem mục 7 — ảnh hưởng **tỉ lệ quy đổi**, không ảnh hưởng số tiền lợi nhuận | `DEC-PHB02-05` |
| `Duplicate` | Hai dòng nội dung giống hệt trong **một lần** nhập | PENDING | TIN | TIN | TIN | **CÓ** | Không đổi gì | **`CHỜ CHỦ DỰ ÁN`** | `CHỜ CHỦ DỰ ÁN` | Xem mục 8 — đây là rủi ro đếm đúp **thật** duy nhất trong toàn bộ danh sách, và cách xử lý hiện tại đang **mâu thuẫn với chính nó** | `DEC-128` §3 |
| `EmployeeMapping` — F3 (một tên khớp nhiều người) | Master nhân viên nhập nhằng | PENDING | TIN | TIN | **KHÔNG TIN** | KHÔNG | Không đổi gì | `CHỈ CẢNH BÁO` | **`CHẶN KPI`** | Số tiền đúng; **người nhận** thì chưa chắc | `DEC-129` |
| `EmployeeMapping` — F4 (tên lạ, số dòng đáng kể) | Tên chưa có trong master | PENDING | TIN | TIN | **KHÔNG TIN** | KHÔNG | Không đổi gì | `CHỈ CẢNH BÁO` | **`CHẶN KPI`** | Như trên | `DEC-129` |
| `EmployeeMapping` — F5 (không map được ai) | Master hỏng hoàn toàn | PENDING | TIN | TIN | **KHÔNG TIN** | KHÔNG | Không đổi gì | `CHỈ CẢNH BÁO` | **`CHẶN KPI`** | Như trên | `DEC-129` |
| `EmployeeMapping` — F6 (nhân viên `active: false` vẫn có dòng) | Master mâu thuẫn | PENDING | TIN | TIN | TIN | KHÔNG | Không đổi gì | `CHỈ CẢNH BÁO` | `CHO PHÉP` | **Biết rõ ai bán** — chỉ là người đó đã được đánh dấu nghỉ. Chính cấu hình đã ghi: *"KHÔNG đổi cách tính, KHÔNG đổi KPI ownership"* | `HD-110-03` + `config/validation.yaml` |
| `EmployeeMapping` — F2 (nhân viên trong master không có dòng nào) | Master thừa | **KHÔNG gây PENDING dòng** | TIN | TIN | TIN | KHÔNG | Không đổi gì | `CHỈ CẢNH BÁO` | `CHO PHÉP` | Không gắn vào dòng nào (không có dòng nguồn) — đã kiểm chứng bằng golden | Bằng chứng E1 mục 10 |

### 3.3 Nhóm C — kết quả còn trống

| MÃ | NGUYÊN NHÂN GỐC | HIỆN ĐANG GÂY RA | TIN GIÁ BÁN | TIN GIÁ NHẬP | TIN GÁN NHÂN VIÊN | ĐẾM ĐÚP | GIÁ TAY CỨU ĐƯỢC? | PHÂN LOẠI LỢI NHUẬN | PHÂN LOẠI KPI NHÂN VIÊN | LÝ DO | THẨM QUYỀN |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `Pending.eligible_kpi_profit` — vì **thiếu giá nhập** | Không có giá nhập ⟹ không có lợi nhuận KPI | PENDING | TIN | KHÔNG TIN (chưa có) | TIN | KHÔNG | **CÓ** | `TRIỆU CHỨNG` | `CHO PHÉP` | Đây là mã **vòng tròn**: nó nói "chưa có lợi nhuận", rồi được dùng làm lý do để không tính lợi nhuận | `excel_exporter.py:163-168` |
| `Pending.eligible_kpi_profit` — vì **file thẩm quyền KPI hỏng** | `config/eligible_costs.yaml` thiếu/sai, hoặc nguồn điều chỉnh đã duyệt không đọc được | PENDING | TIN | TIN | TIN | KHÔNG | KHÔNG | **`CHẶN`** | `KHÔNG LIÊN QUAN` | Trường hợp này **là lý do chặn thật**: khi file thẩm quyền hỏng, ta **không được phép khẳng định** danh mục chi phí hợp lệ là rỗng, nên không được phép cho ra một con số | `DEC-143` §1 (fail-closed) |
| `Pending.accounting_purchase_price` | (đã nghỉ hưu) | Chỉ còn trong dữ liệu cũ | — | — | — | — | — | `TRIỆU CHỨNG` | `KHÔNG LIÊN QUAN` | `DEC-PAN-001` đã gỡ khỏi đường sinh mã mới | `DEC-PAN-001` |
| `Pending.accounting_profit` | (đã nghỉ hưu) | Chỉ còn trong dữ liệu cũ | — | — | — | — | — | `TRIỆU CHỨNG` | `KHÔNG LIÊN QUAN` | Như trên | `DEC-PAN-001` |

> **Cảnh báo quan trọng:** mã `Pending.eligible_kpi_profit` hiện **một mã cho
> hai tình huống hoàn toàn khác nhau** — một cái phải mở, một cái phải chặn.
> Chỉ nhìn cái mã đó thì không phân biệt được. Mục 9 nêu cách xử lý an toàn.

---

## 4. Trường hợp riêng — NHẬN DIỆN SẢN PHẨM

### 1. Vấn đề là gì?

"Nhận diện sản phẩm" (Product Identity) là việc máy đọc dòng chữ trên chứng
từ — ví dụ `"Máy giặt LG 10kg FV1410S4W1"` — rồi tìm xem trong danh mục nội bộ
thì đó là mã hàng nào. Khi không tìm ra, máy dán mã `IDENTITY_UNRESOLVED`
(hoặc `IDENTITY_REQUIRES_CONFIRMATION` nếu tìm ra nhiều hơn một khả năng).

Hiện nay hai mã đó khiến dòng bị `PENDING`, và `PENDING` khiến lợi nhuận
không được tính — **kể cả sau khi chủ dự án đã tự tay nhập giá nhập**.

### 2. Ví dụ thực tế dễ hiểu

Anh nhân viên bán một cái máy giặt, ghi trên chứng từ là
`"Máy Giặt Panasonic  NA-F10S10BRV"` (hai dấu cách, viết hoa lệch chuẩn).
Danh mục nội bộ ghi tên khác một chút, nên máy không khớp được → không tra
được giá nhập tự động.

Chủ dự án biết rõ cái máy đó nhập 6.200.000đ, mở màn hình lên và gõ vào
6.200.000. Giá bán trên chứng từ là 7.900.000.

Câu hỏi: **có gì cản ta tính 7.900.000 − 6.200.000 = 1.700.000 không?**
Câu trả lời: **không có gì cả.** Máy vẫn chưa biết mã hàng nội bộ là gì,
nhưng phép trừ đó không cần mã hàng.

### 3. Nó có nên chặn tính lợi nhuận không?

**KHÔNG** — một khi đã có giá nhập hợp lệ.

Phải tách rõ hai chuyện khác nhau, và hiện tại chúng đang bị gộp làm một:

| | Nhận diện sản phẩm có cần không? |
|---|---|
| **Để TÌM RA giá nhập tự động** | **CÓ, bắt buộc.** Không biết là mã hàng nào thì tra bảng giá nào? |
| **Để TÍNH lợi nhuận khi đã có giá** | **KHÔNG.** Công thức là `(giá bán − giá nhập) × số lượng − chiết khấu`. Không có chỗ nào cần mã hàng. |

### 4. Vì sao?

Ba bằng chứng cụ thể, đọc từ chính mã nguồn của commit này:

1. **Công thức đã đóng băng không dùng tới nhận diện.** `DEC-143`/`OD-108B-01`:
   `EligibleKpiProfit = (SellPrice − KpiPurchasePrice) × Quantity − Discount`.
   Bốn đại lượng, không đại lượng nào là mã hàng.

2. **Trên dữ liệu thật, mã hàng đang RỖNG ở 100% số dòng — và hệ thống vẫn
   chạy.** Chính chú thích trong `app/web/business_queries.py:21` viết:
   *"`canonical_product_code` rỗng trên dữ liệu thật nên không thay thế được"*.
   Nếu nhận diện thật sự cần cho việc tính toán, hệ thống đã không chạy được
   ngày nào.

3. **Việc lưu giá tay không hề dùng tới nhận diện.** Giá chủ dự án nhập được
   gắn vào dòng bằng khoá `sha256(tên hàng thô)` (`app/history/keys.py:70`),
   tức là gắn thẳng vào **dòng chữ trên chứng từ**, không đi qua mã hàng nội
   bộ. Nghĩa là: giá tay đã hoạt động **độc lập hoàn toàn** với nhận diện.

### 5. Nó có ảnh hưởng việc gán KPI cho nhân viên không?

**KHÔNG.** Nhân viên được xác định từ cột NVBH của chính dòng đó, không liên
quan gì tới sản phẩm là gì.

### 6. Cần sửa gì ở PHB-03?

Bỏ toàn bộ 10 mã Nhóm A ra khỏi tập "lý do chặn lợi nhuận". Thay vào đó cửa
chặn kiểm tra một câu duy nhất: **"dòng này đã có giá nhập hợp lệ chưa?"**
Giá đó đến từ máy hay từ tay chủ dự án đều được — `DEC-PHB02-02` §3 đã quy
định rõ ba nguồn `AUTO` / `MANUAL` / `MANUAL_OVERRIDE` đều hợp lệ, chỉ cần
giữ đúng nhãn nguồn.

### Một lỗ hổng minh bạch cần chủ dự án biết

Có 8 mã lý do chi tiết bên trong khâu nhận diện (ví dụ
`TRACKING_INV_MAP_EXPLICIT_IGNORE` = *"người bên Tracking đã xem và xác nhận
đây không phải sản phẩm cần map"*, so với `NO_CANDIDATE_IN_ANY_CATALOG` =
*"chưa ai xem"*). **Cả 8 mã này đều bị nén thành đúng một chữ
`IDENTITY_UNRESOLVED` khi lưu xuống** (`composition.py:437-444`).

Hệ quả: trên màn hình, một dòng **đã có người xem và kết luận** trông y hệt
một dòng **chưa ai đụng tới**. Đây không phải lỗi chặn lợi nhuận, nhưng là
mất mát thông tin thật, và nên ghi nhận để xử lý sau (**không** thuộc phạm vi
PHB-03).

---

## 5. Trường hợp riêng — BẤT THƯỜNG (Suspicious / Suspicious.ERP)

### 1. Vấn đề là gì?

Hệ thống có hai loại cảnh báo "trông lạ":

- **`Suspicious`** — dựa trên số **do chính công cụ tính**: số lượng ≤ 0,
  giá bán = 0, giá nhập > giá bán, lợi nhuận âm.
- **`Suspicious.ERP`** — dựa trên cột `Lợi nhuận` mà **phần mềm ERP tự ghi**
  trong sổ, khi cột đó âm.

### 2. Ví dụ thực tế dễ hiểu

Bằng chứng thật, đọc trực tiếp từ hai bộ dữ liệu golden đã được nghiệm thu
(`tests/fixtures/golden/period_2026_01.xlsx` và `period_2026_06.xlsx`):

| Dòng | Số BH | Tên hàng | SL | Đơn giá | Cảnh báo |
|---|---|---|---:|---:|---|
| 13 | BH62171 | Giá treo Tivi | 1 | **0** | giá bán = 0 → CHẶN |
| 57 | BH62464 | Giá treo Tivi | 4 | **0** | giá bán = 0 → CHẶN |
| 111 | BH62665 | Giá treo Tivi | 1 | **0** | giá bán = 0 → CHẶN |
| 141 | BH62863 | Giá treo Tivi | 1 | **0** | giá bán = 0 → CHẶN |
| 142 | BH62863 | Chân máy giặt Đa Năng | 1 | **0** | giá bán = 0 → CHẶN |
| 126 | BH70988 | Bình nước nóng Ariston Slim 3 20 RS VN | 1 | **0** | giá bán = 0 → CHẶN |
| 67 | BTL00296 | Kệ máy giặt đa năng inox | **0** | 1.300.000 | số lượng = 0 → CHẶN |
| 94 | BTL00300 | Máy Giặt Panasonic NA-F10S10BRV | **0** | 6.200.000 | số lượng = 0 → CHẶN |
| 258 | BTL00306 | Loa Samsung HW-S700D/XV | **0** | 3.400.000 | số lượng = 0 → CHẶN |
| 64 | BH62511 | Chi phí vận chuyển | 1 | 0 | **KHÔNG chặn** (khớp từ khoá "phí") |
| 86 | BH62606 | Chi phí lắp đặt | 1 | 0 | **KHÔNG chặn** (khớp từ khoá "phí") |

Nhìn bảng này thấy ngay một điều: **"Chi phí lắp đặt" giá 0 thì được tha,
"Giá treo Tivi" tặng kèm giá 0 thì bị chặn** — chỉ vì danh sách từ khoá hạ
mức cảnh báo có chữ `"phí"` mà không có chữ `"giá treo"`. Đó là một bộ lọc
tên hàng tạm thời (chính cấu hình tự gọi nó là *"GIẢI PHÁP TẠM THỜI"*),
**không phải một luật kinh tế**.

### 3. Nó có nên chặn tính lợi nhuận không?

| Quy tắc | Có nên chặn? |
|---|---|
| **giá bán = 0** (hàng tặng kèm) | **KHÔNG.** Con số 0 là một giá bán **thật**, không phải một giá trị thiếu. |
| **giá nhập > giá bán** (bán lỗ) | **KHÔNG.** Lỗ là một sự thật kinh doanh, phải hiện ra chứ không phải giấu đi. |
| **lợi nhuận kế toán âm** | **KHÔNG.** Đây là hệ quả của dòng trên, không phải phát hiện độc lập. |
| **số lượng ≤ 0** | **CHƯA ĐỦ CĂN CỨ — cần chủ dự án quyết.** Xem dưới. |
| **`Suspicious.ERP`** | **KHÔNG** — và thực tế nó **vốn đã không chặn**. |

### 4. Vì sao?

**Về `Suspicious.ERP`:** đây là điểm cần đính chính lại một hiểu lầm đã tồn
tại trong tài liệu.

Tài liệu `TASK-PRA-003` mục (10) viết rằng một dòng có đủ ba số tiền *"vẫn có
thể `PENDING` vì lý do khác (`EmployeeMapping`, `Suspicious.ERP`…)"*.
**Điều đó không còn đúng với cấu hình đang chạy.** Bằng chứng:

- `config/validation.yaml` đặt `suspicious_erp: severity: INFO`.
- `excel_exporter.py:125-127` bỏ qua mọi mục ở mức `INFO`,
  **trừ** đúng một ngoại lệ là `Missing.PurchasePrice`.
- ⟹ `Suspicious.ERP` **chưa bao giờ** gắn vào một dòng nào.
- Kiểm chứng E1 (mục 10): golden kỳ 01/2026 có **22 mục** `Suspicious.ERP`,
  kỳ 06/2026 có **17 mục** — và số dòng bị chúng gắn vào là **0**.

Thêm nữa, `D1` đã quyết định con số `source_profit` của ERP **không được lên
bất kỳ báo cáo nào**, vì *"nó chưa qua bất kỳ quy tắc nào của Reports"*.
Dùng một con số đã bị loại khỏi báo cáo để chặn một con số khác được lên báo
cáo là mâu thuẫn.

**Về `số lượng ≤ 0`:** đây là chỗ duy nhất trong nhóm này thật sự cần chủ dự
án. Số lượng `0` có thể mang hai nghĩa hoàn toàn khác nhau:

- *"Thật sự không giao cái nào"* → lợi nhuận đúng bằng `0`, tính được, đúng.
- *"Quên gõ số lượng"* → lợi nhuận **chưa xác định**, và cho ra `0` là **nói
  dối bằng một con số**.

Nhìn dòng 94 (`Máy Giặt Panasonic`, SL = 0, đơn giá 6.200.000) thì không thể
biết là nghĩa nào. Không có quyết định nào đã duyệt nói rõ. Vì vậy bản này
**không tự chọn hộ** — xếp `CHỜ CHỦ DỰ ÁN`.

Số lượng **âm** gần như chắc chắn là hàng trả lại. Việc lợi nhuận âm tương
ứng có được phép trừ vào KPI của nhân viên hay không cũng là một quyết định
nghiệp vụ chưa ai chốt.

### 5. Nó có ảnh hưởng việc gán KPI cho nhân viên không?

**KHÔNG.** Không quy tắc `Suspicious` nào nói gì về người bán.

### 6. Cần sửa gì ở PHB-03?

- Bỏ `Suspicious.ERP` khỏi mọi suy nghĩ về chặn lợi nhuận (nó vốn đã không
  chặn — chỉ cần **đừng thêm** nó vào).
- Bỏ `giá bán = 0`, `giá nhập > giá bán`, `lợi nhuận âm` khỏi tập chặn.
- **Giữ nguyên** `số lượng ≤ 0` ở trạng thái chặn **cho tới khi chủ dự án
  quyết** — chặn tạm thời là phía an toàn.
- Sửa lại câu `FACT` trong `TASK-PRA-003` mục (10) vì nó đang mô tả sai hành
  vi hiện tại (**việc này không thuộc PHB-03**, chỉ ghi nhận).

---

## 6. Trường hợp riêng — NHÂN VIÊN (EmployeeMapping · OrderInconsistency)

### 1. Vấn đề là gì?

Ở đây phải tách **hai câu hoàn toàn khác nhau** mà hệ thống hiện đang trộn
làm một:

> **Câu A:** *"Không tính được dòng này lãi bao nhiêu."*
> **Câu B:** *"Tính được lãi rồi, nhưng chưa chắc lãi đó là của ai."*

Hiện nay cả hai đều dẫn tới cùng một kết quả: **không tính gì cả**. Đó là lý
do chỉ tiêu "Lợi nhuận KPI" toàn kỳ bị kéo xuống bởi những vấn đề vốn chỉ
liên quan tới việc **gán tên người**.

### 2. Ví dụ thực tế dễ hiểu

Một đơn hàng có 3 dòng. Hai dòng ghi NVBH là `"Vinh"`, dòng thứ ba người ta
gõ nhầm thành `"Vjnh"` — chưa có trong danh sách nhân viên.

Hôm nay: máy dán `OrderInconsistency` lên **cả đơn**, cả 3 dòng thành
`PENDING`, và **toàn bộ lợi nhuận của cả 3 dòng biến mất** khỏi báo cáo — kể
cả hai dòng của `"Vinh"` mà không ai nghi ngờ gì.

Điều đúng phải là: cả 3 dòng đều tính được lãi bình thường (giá bán và giá
nhập đều rõ); riêng dòng thứ ba thì **chưa cộng vào KPI của ai** cho tới khi
biết `"Vjnh"` là ai.

### 3. Nó có nên chặn tính lợi nhuận không?

**KHÔNG.** Không có quy tắc nào của `EmployeeMapping` hay
`OrderInconsistency` nói gì về giá bán, giá nhập hay số lượng.

### 4. Vì sao?

Bốn điểm cụ thể:

1. **Số tiền và người nhận là hai đại lượng độc lập.** Công thức lợi nhuận
   không có biến "nhân viên".

2. **`OrderInconsistency` lây kiểu "vạ lây".** Nó ở phạm vi **ĐƠN**
   (`SCOPE_ORDER`), nên `excel_exporter.py:130-132` gắn nó vào **mọi dòng**
   của đơn đó — kể cả những dòng hoàn toàn bình thường. Một sai sót ở dòng
   thứ ba làm mất luôn lợi nhuận của dòng thứ nhất và thứ hai.

3. **Với báo cáo Nhân viên V1, `OrderInconsistency` thậm chí không phải một
   vấn đề gán người.** Báo cáo Nhân viên nhóm theo `employee_normalized`
   **của từng dòng**, và trường đó được điền từ cột NVBH **của chính dòng
   đó**. Việc "đơn này có nhiều tên nhân viên" chỉ là vấn đề của cách chọn
   một-người-đại-diện-cho-cả-đơn ở tầng cũ — tầng mà báo cáo Nhân viên V1
   không dùng tới. Vì vậy: **`CHO PHÉP`** cả về lợi nhuận lẫn KPI.

4. **Tiêu chí F6 tự nó đã tuyên bố không đụng tới KPI.** `config/validation.yaml`
   viết nguyên văn về F6: *"Mức WARNING; KHÔNG đổi cách tính, KHÔNG đổi KPI
   ownership."* Một quy tắc đã tự nói mình không đổi KPI mà lại đang xoá sổ
   lợi nhuận của dòng là một mâu thuẫn rõ ràng giữa văn bản và hành vi.

### 5. Nó có ảnh hưởng việc gán KPI cho nhân viên không?

**CÓ — và đây mới là chỗ nó thực sự thuộc về.**

| Tiêu chí | Ảnh hưởng lợi nhuận | Ảnh hưởng KPI nhân viên |
|---|---|---|
| F3 — một tên khớp nhiều người | KHÔNG | **CHẶN** — không biết cộng cho ai |
| F4 — tên lạ chưa có trong master | KHÔNG | **CHẶN** — như trên |
| F5 — không map được ai cả | KHÔNG | **CHẶN** — như trên |
| F6 — nhân viên đã nghỉ vẫn có dòng | KHÔNG | **CHO PHÉP** — biết rõ ai bán |
| F2 — nhân viên trong master không có dòng | KHÔNG | CHO PHÉP (không gắn vào dòng nào) |
| `Missing` — thiếu nhân viên | KHÔNG | **CHẶN** |
| `OrderInconsistency` — khác nhân viên | KHÔNG | CHO PHÉP (đã giải thích ở điểm 3) |

### 6. Cần sửa gì ở PHB-03?

Báo cáo phải tách làm hai chỉ tiêu, không gộp:

- **Lợi nhuận KPI toàn kỳ** — cộng mọi dòng tính được, kể cả dòng chưa rõ ai
  bán.
- **Lợi nhuận KPI theo nhân viên** — chỉ cộng dòng đã biết chắc ai bán;
  phần chưa rõ hiện thành một mục riêng, ví dụ *"Chưa xác định người bán:
  X dòng · Y đồng"*.

Như vậy hai con số cộng lại luôn bằng tổng, và chủ dự án nhìn thấy đúng phần
đang treo — thay vì phần đó biến mất không dấu vết như hiện nay.

---

## 7. Trường hợp riêng — PHÂN LOẠI NGUỒN KHÁCH (SourceClassification)

### 1. Vấn đề là gì?

Mỗi đơn được xếp vào một trong hai nguồn: `PERSONAL` (khách cá nhân) hay
`ADS` (khách từ quảng cáo). Máy tự xếp; nếu sau này có người sửa tay và kết
quả sửa khác kết quả máy, cảnh báo `SourceClassification` bật lên.

### 2. Ví dụ thực tế dễ hiểu

Máy xếp đơn `BH62171` là `ADS`. Một người vào sửa thành `PERSONAL`. Cảnh báo
bật, cả đơn thành `PENDING`, lợi nhuận biến mất.

Nhưng nguồn khách **không xuất hiện ở bất kỳ đâu** trong công thức lợi nhuận.
Nó chỉ quyết định **tỉ lệ quy đổi** — ví dụ Tín Phát là 7,5%, nội thành hàng
thường 2%, nội thành gia dụng 8%.

### 3. Nó có nên chặn tính lợi nhuận không?

**KHÔNG.**

### 4. Vì sao?

Ba lý do:

1. Nguồn khách không nằm trong `(giá bán − giá nhập) × số lượng − chiết khấu`.
2. `DEC-PHB02-04` quy định `DS quy đổi = Lợi nhuận KPI ÷ tỉ lệ`. Lợi nhuận là
   **đầu vào**, tỉ lệ là **số chia**. Không tính được đầu vào thì không có gì
   để chia — chặn lợi nhuận vì nghi ngờ **số chia** là làm ngược thứ tự.
3. **Trên thực tế cảnh báo này chưa từng bật lần nào.** Chưa có màn hình nào
   ghi được giá trị sửa tay (`lead_source_manual`), nên nó cho 0 phát hiện
   **theo cấu tạo**, không phải vì rule hỏng. Golden hai kỳ: **0 mục**.

### 5. Nó có ảnh hưởng việc gán KPI cho nhân viên không?

**Không ảnh hưởng ai nhận.** Nhưng **có ảnh hưởng DS quy đổi** — vì tỉ lệ
đổi thì DS quy đổi đổi. Điều đúng là: hiện lợi nhuận bình thường, và **đánh
dấu riêng DS quy đổi của dòng đó là chưa chắc chắn**.

### 6. Cần sửa gì ở PHB-03?

Bỏ khỏi tập chặn lợi nhuận. Ghi nhận nó là một cảnh báo về **tỉ lệ quy đổi**.
Vì hiện tại nó cho 0 phát hiện, thay đổi này **không làm đổi bất kỳ con số
nào hôm nay** — nó chỉ khiến luật đúng trước khi tính năng sửa tay ra đời.

---

## 8. Trường hợp riêng — DÒNG TRÙNG (Duplicate)

### 1. Vấn đề là gì?

Đây là **rủi ro đếm đúp thật duy nhất** trong toàn bộ 19 mã, nên phải xét kỹ
hơn các mã khác.

Máy đánh dấu `Duplicate` khi **hai dòng có nội dung giống hệt nhau** xuất
hiện trong **cùng một lần nhập file**. "Giống hệt" ở đây là giống toàn bộ:
cùng ngày, cùng số chứng từ, cùng tên hàng, cùng số lượng, cùng giá, cùng
nhân viên.

### 2. Ví dụ thực tế dễ hiểu

Một đơn bán tivi kèm **hai** cái giá treo giống hệt nhau. Nhân viên ghi thành
hai dòng thay vì một dòng số lượng 2.

- **Nếu đó là hàng thật** → hai dòng đều đúng, đều phải tính.
- **Nếu đó là gõ nhầm hai lần** → chỉ được tính một, nếu tính cả hai thì
  doanh thu **và** lợi nhuận đều bị cộng đúp.

Máy **không thể** phân biệt hai trường hợp này — chúng giống nhau từng chữ.

### 3. Nó có nên chặn tính lợi nhuận không?

**CHƯA ĐỦ CĂN CỨ ĐỂ QUYẾT — cần chủ dự án.**

Nhưng dù chủ dự án quyết thế nào, **cách xử lý hiện tại chắc chắn sai**, vì
nó tự mâu thuẫn.

### 4. Vì sao?

**Ba dữ kiện, đọc từ mã nguồn:**

1. `DEC-128` §3 đã quyết định rõ đây là **"có thể trùng, cần xem"** chứ không
   phải "chắc chắn trùng". Nguyên văn chú thích: *"hai dòng phụ kiện giống hệt
   nhau trên một đơn có thể hoàn toàn hợp lệ"*. Mức cảnh báo là `WARNING`,
   không phải `ERROR`.

2. Việc chống trùng khi **nhập lại cùng một file** là chuyện khác hẳn, và đã
   được giao cho `TASK-201` — **không** thuộc mã này.

3. **Và đây là điểm mấu chốt: hôm nay hệ thống đang xử lý dòng trùng theo hai
   cách mâu thuẫn nhau.**

   | Chỉ tiêu | Có chặn dòng `Duplicate` không? |
   |---|---|
   | **Doanh thu bán hàng** | **KHÔNG** — cộng cả hai dòng |
   | **Lợi nhuận KPI** | **CÓ** — bỏ cả hai dòng |

   Trong `business_metrics.py:305`, doanh thu cộng thẳng `total_sales` của
   mọi dòng, **không** hỏi trạng thái. Còn lợi nhuận thì hỏi và loại.

   Nghĩa là: **nếu đó thật sự là dòng trùng, doanh thu đã bị đếm đúp rồi mà
   chưa ai chặn.** Còn nếu đó không phải dòng trùng, thì lợi nhuận đang bị
   loại oan. **Không có cách đọc nào khiến hành vi hiện tại là đúng.**

### 5. Nó có ảnh hưởng việc gán KPI cho nhân viên không?

**CÓ, gián tiếp.** Nếu đếm đúp thì nhân viên đó được cộng dư. Nhưng vấn đề
này nằm ở **doanh thu**, và doanh thu hiện đang **không** bị chặn.

### 6. Cần sửa gì ở PHB-03?

**PHB-03 KHÔNG tự quyết chuyện này.** Bản này chỉ trình ra lựa chọn:

| Phương án | Nội dung |
|---|---|
| **A** | Dòng trùng bị loại khỏi **cả** doanh thu **lẫn** lợi nhuận (nhất quán, phía thận trọng) |
| **B** | Dòng trùng vào **cả** doanh thu **lẫn** lợi nhuận, và hiện cảnh báo cho người xem tự xử (nhất quán, phía tin dữ liệu) |
| **C — hiện tại** | Vào doanh thu nhưng không vào lợi nhuận (**không nhất quán — phải bỏ**) |

Trong lúc chờ chủ dự án, giữ `Duplicate` ở trạng thái **chặn lợi nhuận** là
phía an toàn hơn, nhưng phải nói rõ với chủ dự án rằng doanh thu **vẫn đang
đếm đúp**.

---

## 9. Cửa chặn đúng phải có hình dạng nào

Đây là **mô tả khái niệm**, không phải mã nguồn. PHB-03 sẽ hiện thực hoá,
phiên này chỉ định nghĩa.

### 9.1 Quy tắc "có được tính lợi nhuận không"

```
CÓ_ĐƯỢC_TÍNH_LỢI_NHUẬN(dòng) =
        có giá bán                     (sell_price khác rỗng)
    VÀ  có số lượng                    (quantity khác rỗng)
    VÀ  có giá nhập hiệu lực           (AUTO hoặc MANUAL hoặc MANUAL_OVERRIDE)
    VÀ  thẩm quyền KPI đọc được        (config/eligible_costs.yaml hợp lệ)
    VÀ  KHÔNG mang bất kỳ lý do nào thuộc tập CHẶN_THẬT
```

**Tuyệt đối không dùng `status == "AUTO"`** làm cửa chặn, vì `status` chỉ là
kết quả cộng dồn của 19 mã rất khác nhau, và bản audit này đã chứng minh
không phải mã nào cũng là lý do kinh tế.

**Tập `CHẶN_THẬT` — đề xuất, tối thiểu và thận trọng:**

| Lý do trong tập chặn | Vì sao ở đây |
|---|---|
| `Missing` | **Chỉ vì lý do kỹ thuật**: mã này gộp 5 trường, và trường nào thì **không lưu xuống** cơ sở dữ liệu. Trong đó có "thiếu số lượng" là lý do chặn thật. Không tách được thì phải chặn cả cụm |
| `Suspicious` | **Chỉ vì lý do kỹ thuật, cộng một lý do nghiệp vụ**: gộp 4 quy tắc, và "số lượng ≤ 0" đang chờ chủ dự án quyết |
| `Duplicate` | Chờ chủ dự án (mục 8) |
| `Pending.eligible_kpi_profit` **khi thẩm quyền KPI hỏng** | Fail-closed của `DEC-143` §1 — xem 9.3 |

**Và tuyệt đối KHÔNG có trong tập chặn** — đây là phần mở khoá:
cả 10 mã Nhóm A · `Missing.PurchasePrice` · `Suspicious.ERP` ·
`OrderInconsistency` · `SourceClassification` · `EmployeeMapping` ·
`Pending.eligible_kpi_profit` khi chỉ là hệ quả của thiếu giá nhập.

### 9.2 Quy tắc "có được cộng vào KPI của một nhân viên không"

```
CÓ_ĐƯỢC_CỘNG_KPI_NHÂN_VIÊN(dòng) =
        CÓ_ĐƯỢC_TÍNH_LỢI_NHUẬN(dòng)
    VÀ  đã biết tên nhân viên chuẩn hoá
    VÀ  trạng thái map nhân viên = "mapped"
    VÀ  KHÔNG mang lý do EmployeeMapping thuộc {F3, F4, F5}
    VÀ  KHÔNG mang lý do Missing-thiếu-nhân-viên
```

Dòng tính được lợi nhuận nhưng chưa biết ai bán **vẫn vào tổng toàn kỳ**, và
hiện riêng thành *"Chưa xác định người bán"* — không biến mất.

### 9.3 Một cái bẫy phải tránh khi sửa

Hiện tại, khi file `config/eligible_costs.yaml` hỏng, máy trả `None` cho
**mọi** dòng — đó là cơ chế **fail-closed** cố ý của `DEC-143` §1: *thà không
ra số còn hơn ra số sai*.

Nhưng đường tính lại khi có giá tay
(`business_metrics.BusinessLine.kpi_profit`, nhánh có override) **áp thẳng
công thức** mà **không** hỏi thẩm quyền đó có đọc được không.

⟹ Nếu sửa cửa chặn mà không xử lý điểm này, thì trong tình huống file thẩm
quyền hỏng, những dòng có giá tay sẽ **vẫn ra số**, đi vòng qua đúng cái van
an toàn được dựng để chặn. **Việc sửa PHB-03 bắt buộc phải giữ van này.**

---

## 10. Bằng chứng đo được (E1)

Chạy trên chính commit `60adb2ec`, dùng hai bộ dữ liệu golden đã được nghiệm
thu. Kịch bản: *"giả sử mọi dòng đều đã có giá nhập hợp lệ — còn lý do nào
vẫn ép dòng thành `PENDING`?"*

```
==== period_2026_01.xlsx: 351 lines
   reason->line attachments (category, severity):
     Missing.PurchasePrice        INFO     351 lines
     Suspicious                   WARNING  8 lines
   lines STILL forced PENDING after a valid price exists: 8 -> rows [13, 57, 67, 94, 111, 141, 142, 258]

==== period_2026_06.xlsx: 180 lines
   reason->line attachments (category, severity):
     Missing.PurchasePrice        INFO     180 lines
     Suspicious                   WARNING  4 lines
   lines STILL forced PENDING after a valid price exists: 3 -> rows [65, 126, 171]
```

**Đọc kết quả này:**

1. Trên **531 dòng** của hai kỳ golden, sau khi đã có giá nhập, chỉ còn
   **11 dòng** mang một lý do khác — và **cả 11 đều là `Suspicious`**
   (chính là danh sách "Giá treo Tivi giá 0" / "SL = 0" ở mục 5).
2. `Suspicious.ERP` có **22 mục** ở kỳ 01 và **17 mục** ở kỳ 06, nhưng gắn vào
   **0 dòng** — xác nhận nó không chặn.
3. `EmployeeMapping` có **7 mục** mỗi kỳ, tất cả ở phạm vi lô với danh sách
   dòng nguồn **rỗng** — gắn vào **0 dòng**.
4. `Duplicate`, `OrderInconsistency`, `SourceClassification`, `Missing`:
   **0 mục** trên cả hai kỳ.

**Nói cách khác:** ~98% việc chặn lợi nhuận hôm nay đến từ đúng một chuyện —
**thiếu giá nhập** — tức là **chính cái mà tính năng nhập tay của PHB-03 sinh
ra để giải quyết**.

> **Không suy rộng thành tần suất trên production.** Hai kỳ golden có
> `price_source = "Pending"` ở **100% số dòng**, nên chúng không tách được
> hết mọi trường hợp. Con số production duy nhất đã được nghiệm thu là
> `PHB-02` mục 4.4: kỳ 09/2026 coverage lợi nhuận KPI = **34 / 142 dòng**.
> Nghĩa là **108 dòng** đang bị chặn — và theo phân tích trên, phần lớn trong
> số đó bị chặn vì thiếu giá nhập.

---

## 11. Đánh giá lại các phát hiện chặn B01–B03

### Nguyên nhân gốc chung: **C — cả hai**, nhưng phải nói chính xác hơn

Báo cáo review ban đầu nêu hai khả năng: (A) `PENDING` là cửa chặn quá rộng,
(B) giá tay được hợp nhất quá muộn. Cả hai đều đúng, nhưng **chúng không phải
hai lỗi song song — chúng khoá vào nhau thành một vòng lặp**:

```
1. Máy chạy, không tra ra giá nhập của dòng X.
2. Máy ghi vào dòng X các lý do:
       "Missing.PurchasePrice"  và  "Pending.eligible_kpi_profit"
3. Vì có lý do → máy đóng dấu   status = "PENDING"   và LƯU vào cơ sở dữ liệu.
4. Chủ dự án mở màn hình, nhập giá nhập của dòng X. Giá được lưu vào một
   BẢNG RIÊNG (đúng thiết kế — bảng kết quả của máy chỉ ghi thêm, không sửa).
5. Khi đọc báo cáo, giá tay được ghép vào dòng X.
6. NHƯNG  status  vẫn được đọc từ dấu đóng ở bước 3 — không ai tính lại.
7. Cửa chặn thấy  status != "AUTO"  → trả về "không có lợi nhuận".
                                       ↑
        Lý do khiến nó PENDING chính là thứ chủ dự án vừa sửa xong ở bước 4.
```

**Đây là một cửa chặn tự quy chiếu.** Nó không chỉ "quá rộng" — nó đọc một
ảnh chụp cũ của **chính điều kiện mà thao tác của chủ dự án vừa làm cho hết
đúng**. Vì bảng kết quả là **append-only** (chỉ ghi thêm, không sửa — đúng
thiết kế đã nghiệm thu) và giá tay chỉ ghép **lúc đọc**, dấu `PENDING` đó
**không bao giờ** biến mất, dù chủ dự án nhập bao nhiêu giá đi nữa.

**Hệ quả nghiêm trọng nhất:** với **đúng tập dòng** mà đường nhập giá tay
được xây để cứu — dòng `PENDING` vì thiếu giá — đường đó **không bao giờ có
tác dụng lên Lợi nhuận KPI**. Nó chỉ hoạt động trên dòng vốn đã `AUTO`, tức
là dòng **đã có giá rồi** và không cần cứu.

### Hai vấn đề đi kèm, phát hiện thêm trong phiên này

**(1) Hai ô đếm đang nói ngược sự thật.**

PHB-03 xây hai ô đếm để chủ dự án biết còn bao nhiêu việc:

- `missing_price_lines` — *"chỉ thiếu mỗi giá nhập, nhập vào là xong"*
- `review_blocked_lines` — *"đường nhập giá không mở khoá được"*

Ô thứ nhất được định nghĩa là `status == "AUTO" VÀ chưa có giá nhập`
(`business_metrics.py:187`). Nhưng nếu chưa có giá nhập thì `Missing.PurchasePrice`
đã bật → `status` chắc chắn là `"PENDING"`, không bao giờ `"AUTO"`.

⟹ **Ô thứ nhất luôn bằng 0 theo cấu tạo.** Toàn bộ số dòng thiếu giá bị dồn
sang ô thứ hai. Màn hình đang nói với chủ dự án: *"nhập giá không cứu được
những dòng này"* — trong khi sự thật là **nhập giá cứu được gần như tất cả**.

**(2) Bài kiểm thử chứng minh giá tay chạy được đang kiểm một trạng thái
không tồn tại trên thực tế.**

`tests/test_business_metrics.py:201` — bài
`test_a_missing_price_becomes_manual_and_recalculates_the_profit` dựng một
dòng **không có giá nhập** nhưng đặt `status = "AUTO"` (giá trị mặc định của
hàm dựng dòng thử). Như vừa chứng minh, tổ hợp đó **không thể xảy ra** trên
dữ liệu thật.

⟹ Bài kiểm thử này chạy xanh, nhưng nó **không chứng minh** tính năng nhập
giá hoạt động trên production. Ngược lại, bài
`test_a_pending_line_stays_out_of_the_profit_sum_even_with_a_manual_price`
(dòng 185) mới là bài mô tả đúng hành vi thật — và nó đang **cố định hoá
chính cái lỗi này** thành hành vi mong muốn.

### Về thẩm quyền của quy tắc "chỉ cộng dòng AUTO"

Bản audit phải nói rõ chỗ này, vì nhiệm vụ yêu cầu **không được nâng suy diễn
của AI thành thẩm quyền nghiệp vụ**.

Quy tắc `P1` của `TASK-PRA-003` viết: *"Lợi nhuận KPI CHỈ cộng các dòng
`status = 'AUTO'`"*. Nhưng **chính tài liệu đó, ngay dưới bảng, đã tự nói ra
giới hạn của mình** (nguyên văn):

> *"Chiều ngược lại KHÔNG đúng — một dòng có đủ ba số vẫn có thể `PENDING` vì
> lý do khác (`EmployeeMapping`, `Suspicious.ERP`…). Vì vậy "LN KPI chỉ cộng
> dòng AUTO" là **một quy tắc TRÌNH BÀY** có định nghĩa chặt và luôn cộng
> được, không phải một phép lọc tuỳ tiện."*

Tức là `P1` **tự khai mình là một quy tắc trình bày** — chọn cách hiển thị
sao cho luôn cộng được — **chứ không phải một phán quyết kinh tế** rằng
những dòng đó không được có lợi nhuận.

Quyết định `D1` (`OWNER_DECISION`, phiên S095) có mang cụm
`"chỉ cộng dòng status = AUTO"` trong ngoặc. Nhưng chủ đề mà `D1` quyết là
**thứ bậc giữa lợi nhuận KPI và lợi nhuận kế toán, và việc loại
`source_profit`** — cụm trong ngoặc là mô tả hành vi đang có tại thời điểm
đó, không phải một quyết định độc lập rằng "PENDING vì bất kỳ lý do gì đều
không được tính lợi nhuận".

Theo thứ tự thẩm quyền của nhiệm vụ này, **làm rõ của chủ dự án đứng trên
hết**, và làm rõ đó nói:

> *"Nếu một dòng có giá bán hợp lệ và giá nhập hợp lệ, thì phải có một lý do
> nghiệp vụ cụ thể mới được từ chối tính lợi nhuận. Một trạng thái
> PENDING/Review chung chung tự nó KHÔNG phải lý do đủ."*

⟹ **`CURRENT_STATUS_AUTO_GATE = TOO_BROAD` (quá rộng).**

### Ranh giới sửa tối thiểu

**Được đụng vào — 2 file:**

| File | Sửa gì |
|---|---|
| `app/web/business_queries.py` | Thêm cột `pending_reasons_json` vào danh sách cột đọc; giải mã thành danh sách mã (đã có sẵn khuôn mẫu ở `sales_queries._reasons`); truyền vào `BusinessLine` |
| `app/modules/reporting/business_metrics.py` | Thêm trường `pending_reasons` vào `BusinessLine`; thay `if self.status != "AUTO"` bằng phép kiểm tập `CHẶN_THẬT`; giữ van fail-closed của mục 9.3; sửa lại hai ô đếm cho đúng sự thật; tách chỉ tiêu KPI-theo-nhân-viên khỏi chỉ tiêu lợi nhuận toàn kỳ |

Cộng một hằng số đã đóng băng liệt kê tập `CHẶN_THẬT`, mỗi mã kèm thẩm quyền
của nó. Cộng các bài kiểm thử tương ứng, trong đó **bắt buộc** có một bài
dựng đúng trạng thái production thật (`status = "PENDING"` + lý do chỉ là
thiếu giá + có giá tay ⟹ **phải ra số**), thay cho bài hiện đang kiểm một
trạng thái không tồn tại.

**KHÔNG được đụng vào:**

- Cấu trúc cơ sở dữ liệu, migration — **không cần**: cột `pending_reasons_json`
  đã tồn tại (`tools/db/schema.py:294`) và đã được ghi đầy đủ.
- `app/pipeline.py`, `excel_exporter.py`, cách sinh `status` — **không chạy
  lại máy, không ghi đè lịch sử**.
- Product Identity, Tracking, Review Queue, mô hình nhân viên, ProductGroup,
  Target, Legacy, Advanced Analytics, CSRF, parser.
- `app/web/sales_queries.py`, `app/web/analytics_queries.py` — bốn chỗ khác
  cũng dùng cửa chặn `AUTO`, nhưng chúng thuộc PRA-003/PRA-004 và **không**
  hợp nhất giá tay, nên chúng đang tự nhất quán. Sửa chúng là mở rộng phạm vi.

---

## 12. Những gì cần chủ dự án quyết

Không quyết những mục này thì PHB-03 vẫn sửa được (dùng phía thận trọng), như
đã ghi ở mục 9.1. Nhưng nên quyết sớm.

| # | Câu hỏi | Vì sao cần chủ dự án |
|---|---|---|
| **OD-1** | Dòng có **số lượng = 0** thì lợi nhuận là `0` (tính được) hay `chưa xác định` (không tính)? | Hai nghĩa dẫn tới hai con số khác nhau; không quyết định nào đã duyệt nói rõ. Ví dụ: BTL00300, `Máy Giặt Panasonic`, SL = 0, đơn giá 6.200.000 |
| **OD-2** | Dòng có **số lượng âm** (hàng trả) có được trừ vào KPI nhân viên không? | Chưa có quy tắc nào |
| **OD-3** | **Dòng trùng** — chọn phương án A hay B ở mục 8? Và chủ dự án có biết doanh thu hiện **đang** đếm đúp không? | Hành vi hiện tại tự mâu thuẫn, phải bỏ dù chọn phương án nào |
| **OD-4** | Dòng **giá bán = 0** (hàng tặng kèm) có được vào lợi nhuận KPI với con số âm không? | Bản này xếp `CHỈ CẢNH BÁO` vì con số đó là chi phí thật doanh nghiệp chịu. Cần xác nhận |
| **OD-5** | Dòng **chưa biết ai bán** có được vào tổng lợi nhuận toàn kỳ, hiện riêng ở mục *"chưa xác định người bán"* không? | Đây là đề xuất ở mục 6, cần chủ dự án đồng ý |
| **OD-6** | Chủ dự án có xác nhận `P1` của `TASK-PRA-003` là **quy tắc trình bày** (như chính tài liệu đó tự khai), chứ không phải luật kinh tế không? | Cần để tránh việc nới cửa chặn bị coi là vi phạm một quyết định đã đóng băng |

---

## 13. Những gì phiên này **KHÔNG** làm

Đúng chỉ thị mục 10 của nhiệm vụ:

- Không mở việc trong Product Identity, Tracking, hay thiết kế lại Review
  Queue.
- Không đụng mô hình nhân viên, ProductGroup, Target, Legacy, Advanced
  Analytics, CSRF, parser.
- Không tạo task mới. **Phát hiện không tự sinh ra task.**
- Không sửa một dòng mã sản xuất nào.
- Không sửa quyết định đã đóng băng nào.
- Không tuyên bố tần suất trên production khi không có bằng chứng production.

Ba điểm sau đây được **ghi nhận nhưng không xử lý** trong PHB-03, và không mở
task cho chúng:

1. Câu `FACT` trong `TASK-PRA-003` mục (10) mô tả sai hành vi hiện tại
   (`Suspicious.ERP` không còn gây `PENDING`; hai mã `Pending.accounting_*`
   đã nghỉ hưu theo `DEC-PAN-001`).
2. Tám mã lý do chi tiết của khâu nhận diện bị nén thành một chữ
   `IDENTITY_UNRESOLVED` khi lưu, làm mất phân biệt giữa "đã có người xem" và
   "chưa ai xem".
3. Bốn mã `Missing` / `Suspicious` / `EmployeeMapping` / `OrderInconsistency`
   gộp 16 tình huống vào 4 chữ, và chi tiết không được lưu xuống.

---

## 14. Bảng tổng kết

| Trường | Giá trị |
|---|---|
| `TARGET_GATE` | `PASS` |
| `PENDING_REASON_COUNT` | **19** mã còn hiệu lực (+2 đã nghỉ hưu = 21); che **31** tình huống thật |
| `TRUE_PROFIT_BLOCKERS` | `Missing`-thiếu-số-lượng · `Pending.eligible_kpi_profit` khi thẩm quyền KPI hỏng. (Tạm chặn thêm vì lý do kỹ thuật/chờ quyết: cả cụm `Missing`, cả cụm `Suspicious`, `Duplicate`) |
| `WARNING_ONLY_REASONS` | `Suspicious.ERP` · `Suspicious`(giá bán = 0, giá nhập > giá bán) · `OrderInconsistency`(cả 2) · `SourceClassification` · `EmployeeMapping`(F2, F3, F4, F5, F6) · `Missing`-thiếu-nhân-viên |
| `DERIVED_SYMPTOMS` | Toàn bộ 10 mã Nhóm A · `Missing.PurchasePrice` · `Pending.eligible_kpi_profit`(khi chỉ do thiếu giá) · `Suspicious`-lợi-nhuận-âm · `Missing`-thiếu-ngày · 2 mã đã nghỉ hưu |
| `OWNER_DECISION_REQUIRED_REASONS` | `Duplicate` · `Suspicious`-số-lượng-≤-0 · `Missing`-thiếu-doanh-số · `Missing`-thiếu-số-chứng-từ |
| `CURRENT_STATUS_AUTO_GATE` | **`TOO_BROAD`** |
| `B01_B03_ROOT_CAUSE` | **C — cả hai**, khoá vào nhau thành vòng lặp tự quy chiếu (mục 11) |
| `PRODUCTION_CODE_CHANGED` | **NO** |
| `SCOPE_DRIFT` | **NO** |
| `NEXT_VERTICAL_ACTION` | PHB-03 sửa có ranh giới, dùng đúng bảng phân loại này |
