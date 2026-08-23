# ADR-104 — Tách LeadSource khỏi ConversionScheme

## Status
Accepted

## Date
2026-08-23

## Context

Thiết kế ban đầu (ADR-102, `docs/analysis/06_ADS_RULE_VERIFICATION.md` bản
2026-08-22) coi nguồn đơn và tỉ lệ quy đổi là **một khái niệm**. Enum nguồn đơn
có hai giá trị: `PERSONAL` và `TINPHAT_ADS`, và tỉ lệ được suy trực tiếp từ giá
trị đó.

Cách đặt tên này che giấu ba vấn đề, cả ba đều lộ ra ngay khi đối chiếu với
dữ liệu thật:

1. **`TINPHAT_ADS` nhét tên một nhân viên vào một enum nguồn đơn.** Khi Hoàng
   hoặc Kiên có đơn ADS, giá trị gán cho đơn đó vẫn là `TINPHAT_ADS` — một cái
   tên nói sai sự thật về chính đơn hàng ấy. Đơn đó không phải của Tín Phát.

2. **`PERSONAL` không hề đồng nghĩa với 5,5%.** Nội thành bán đơn `PERSONAL`
   nhưng quy đổi ở **2%**; Gia dụng ở **8%**. Trong thiết kế cũ, hai nhóm này
   phải được xử lý như một ngoại lệ nằm ngoài enum — tài liệu mô tả là "tỉ lệ
   đặt ở cấp nhân viên, nên `default_lead_source` không ảnh hưởng tới con số".
   Đó là một cách nói khác của "mô hình không diễn đạt được trường hợp này".

3. **Không thay đổi được chính sách theo một chiều mà không đụng chiều kia.**
   Nếu công ty đổi tỉ lệ ADS từ 7,5% sang 7,0%, hoặc cho Nội thành một tỉ lệ
   ADS riêng, mô hình cũ buộc phải thêm giá trị enum mới — tức sửa code — đúng
   thứ mà tiêu chí nghiệm thu cuối của mục 28 đặc tả cấm.

Chủ dự án xác nhận ngày 2026-08-23 rằng đây là hai khái niệm độc lập, kèm bảng
chính sách hiện hành đầy đủ.

## Decision

**Hai trường độc lập, hai bước phân giải riêng.**

```
LeadSource        — đơn này đến từ đâu?        PERSONAL | ADS
ConversionScheme  — tỉ lệ nào quy đổi nó?      một dòng trong config
```

`LeadSource` có **đúng hai giá trị**. `TINPHAT_ADS` bị loại bỏ hoàn toàn.

### Bước 1 — Phân giải LeadSource (cấp OrderID)

```
1. Manual Override                     → "Manual"
2. Rule từ khóa ADS trên Diễn giải     → "Auto:ADS Rule"
3. Mặc định cấp nhân viên              → "Auto:Employee Default (<tên>)"
4. Mặc định toàn hệ thống (PERSONAL)   → "Auto:Default"
```

Rule từ khóa khớp trên **bất kỳ dòng nào** của đơn; kết quả áp cho **mọi dòng**
của đơn đó. Phân loại là quyết định cấp đơn, không bao giờ cấp dòng.

Tín Phát vào ADS qua bậc 3 — `default_lead_source: ADS` trong
`config/employees.yaml`. Đây là khai báo về **nguồn**, không phải về tỉ lệ.

### Bước 2 — Phân giải ConversionScheme (độc lập)

Tra từ `config/conversion_rates.yaml` theo khóa
`(employee, lead_source, ngày của đơn)`:

| employee | lead_source | scheme | rate | effective_from |
|---|---|---|---|---|
| `*` | `PERSONAL` | `PERSONAL_5_5` | 5,5 % | 2026-01-01 |
| `*` | `ADS` | `ADS_7_5` | 7,5 % | 2026-01-01 |
| `Nội thành` | `PERSONAL` | `NOI_THANH_2` | 2 % | 2026-01-01 |
| `Gia dụng` | `PERSONAL` | `GIA_DUNG_8` | 8 % | 2026-01-01 |

Dòng khớp **cụ thể nhất** thắng: dòng ghi đúng tên nhân viên outrank dòng `*`.

**Không có tỉ lệ mặc định cuối cùng.** Một tổ hợp không khớp dòng nào trả về
`Unresolved` và vào Review Queue. Một tỉ lệ thiếu không bao giờ được âm thầm
mượn tỉ lệ của người khác — đó là cách một con số sai đi thẳng vào bảng lương.

### Hệ quả trực tiếp của bảng trên

- **Tín Phát** không cần dòng riêng: nó là ADS, nên rơi vào `* + ADS` → 7,5%.
  Đúng con số workbook mẫu đang dùng, nhưng suy ra từ *nguồn đơn*, không phải
  từ *tên nhân viên*.
- **Hoàng và Kiên** không cần dòng riêng: PERSONAL → 5,5%, ADS → 7,5%. Hai
  bucket trong cùng một tháng là hành vi mặc định, không phải ngoại lệ.
- **Nội thành và Gia dụng** giờ diễn đạt được trực tiếp trong mô hình, không
  còn là ghi chú bên lề.

### Tra theo thời điểm

Mọi dòng mang `effective_from` / `effective_to`. Tra bằng **ngày của đơn**,
không bao giờ bằng "hôm nay". Chạy lại báo cáo 2026 vào năm 2028 phải ra đúng
con số của 2026 (DEC-121).

### Override

`ConversionScheme` là một trường override được **độc lập** với `LeadSource`.
Người dùng có thể sửa nguồn đơn mà giữ nguyên scheme, hoặc ngược lại. Cả hai
đều đi qua audit trail của ADR-102 và đều bắt buộc có `reason`.

## Alternatives Considered

1. **Giữ enum gộp, thêm giá trị mới cho mỗi tổ hợp** (`NOITHANH_PERSONAL`,
   `NOITHANH_ADS`, `GIADUNG_PERSONAL`…).
2. **Giữ enum gộp, đặt tỉ lệ ở cấp nhân viên như một bảng phủ lên** — đúng cách
   tài liệu cũ mô tả.
3. **Bỏ hẳn LeadSource, chỉ giữ ConversionScheme.**

## Rationale

**Vì sao không thêm giá trị enum cho mỗi tổ hợp.** Số giá trị bằng tích của số
nhân viên và số nguồn đơn. Thêm một nhân viên là thêm code, thêm một chính sách
là thêm code. Đây chính xác là thứ tiêu chí 14 của mục 28 đặc tả cấm.

**Vì sao không giữ bảng tỉ lệ phủ lên cấp nhân viên.** Nó chạy được, nhưng
không trả lời được câu hỏi "đơn này của Nội thành, có phải ADS không?" — vì
`default_lead_source` của họ bị vô hiệu hóa bởi lớp phủ. Báo cáo tách
Personal/ADS cho kênh sẽ vô nghĩa. Yêu cầu §15 và §16 đặc tả đòi tách nguồn đơn
cho **mọi** nhân viên, không chỉ cho những người tình cờ dùng tỉ lệ chuẩn.

**Vì sao không bỏ LeadSource.** Nguồn đơn là một sự thật kinh doanh có giá trị
tự thân: mục 15 và 16 đặc tả yêu cầu tách bạch "năng lực tự bán" khỏi "năng lực
xử lý lead do công ty tạo ra", và tỉ trọng ADS trên tổng doanh thu quy đổi của
mỗi người. Xóa nó đi là xóa chính chỉ số mà công cụ sinh ra để đo.

**Vì sao tách là đúng ngay cả khi hôm nay hai bảng gần như song ánh.** Với
chính sách hiện tại, biết `LeadSource` gần như đủ để đoán tỉ lệ — trừ Nội thành
và Gia dụng. Chính hai ngoại lệ đó chứng minh sự song ánh là ngẫu nhiên, không
phải bản chất. Mô hình phải diễn đạt được cái đang có thật, không phải cái
thường đúng.

## Consequences

### Positive

- Đổi tỉ lệ, thêm nhân viên, cho một kênh tỉ lệ ADS riêng — tất cả là sửa một
  dòng YAML, không sửa code.
- Báo cáo tách Personal/ADS có nghĩa cho **mọi** nhân viên, kể cả kênh.
- Một tỉ lệ thiếu trở thành `Unresolved` nhìn thấy được, thay vì một con số
  trông hợp lý.
- Mốc 2027 (DEC-121) triển khai được bằng cách thêm dòng có `effective_from`,
  không đụng tới dữ liệu lịch sử.

### Negative / Tradeoffs

- Hai bước phân giải thay vì một; hai trường override thay vì một; nhiều cột
  hơn trong `orders`.
- Người đọc báo cáo phải hiểu rằng `PERSONAL` không kéo theo một tỉ lệ cố định.
  Giảm thiểu: mọi sheet xuất ra hiển thị cột `ConversionScheme` bên cạnh cột
  `LeadSource`, không để người đọc phải tự suy.
- Bảng config có khả năng thiếu dòng. Đây là đánh đổi có chủ ý: thà
  `Unresolved` ồn ào còn hơn một tỉ lệ mặc định im lặng.

## Migration / Implementation Notes

- `orders` mang `lead_source_auto`, `lead_source_manual`, `lead_source_final`,
  `conversion_scheme_auto`, `conversion_scheme_manual`, `conversion_scheme_final`.
  Cả hai cặp theo đúng khuôn override của ADR-102.
- `conversion_engine` **không được** nhận `LeadSource` rồi tự suy tỉ lệ. Nó
  nhận `(employee, lead_source, date)` và gọi bộ phân giải scheme. Kiểm chứng
  bằng một test tĩnh: không có literal `0.055` / `0.075` / `0.02` / `0.08` nào
  trong `app/modules/`.
- Bản cài đặt tham chiếu chạy được: `tools/analysis/verify_ads_rule.py`,
  hàm `classify_lead_source()` và `resolve_conversion_scheme()`. TASK-104 và
  TASK-108 phải cho kết quả giống hệt trên cùng bộ case.
- Dữ liệu lịch sử trước quy ước ADS phân loại thành `PERSONAL` theo mặc định
  (DEC-120). Không xây giá trị `UNKNOWN`.

## Supersedes
Không thay thế toàn bộ ADR nào. Sửa đổi phần mô hình nguồn đơn của ADR-102
(mục "LeadSource được quyết định ở cấp OrderID rồi lan xuống line") bằng cách
bổ sung cặp trường `conversion_scheme_*` song song.

## Superseded By
None
