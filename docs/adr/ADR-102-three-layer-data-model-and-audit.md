# ADR-102 — Mô hình dữ liệu 3 lớp và audit trail

## Status
Accepted

## Date
2026-08-22

## Context

Mục 4 đặc tả yêu cầu ba lớp dữ liệu: RAW bất biến, WORKING sửa được, REPORT
tính từ WORKING sau override. Mục 19 yêu cầu audit trail đầy đủ. Mục 30 nói rõ
nguyên tắc quan trọng nhất:

> *"Không thay đổi lịch sử kinh tế thật chỉ để đạt một quy tắc khuyến khích
> nhân viên. Mọi điều chỉnh KPI phải nằm ở lớp riêng, có lý do và audit trail."*

File báo cáo hiện tại vi phạm nguyên tắc này theo cách khó thấy: khi cần cộng
thêm lợi nhuận cho nhân viên, người làm báo cáo **sửa thẳng ô giá nhập**
(`F11 = =5870-250`). Không có nơi nào ghi lại giá gốc, ai sửa, hay vì sao. Sáu
tháng sau không ai phân biệt được đâu là giá nhập thật.

Đồng thời, phần lợi nhuận ADS lại bị nhét thẳng vào công thức Summary
(`=(G8-37270)/5.5%+37270/7.5%`) — một con số không có dòng dữ liệu nào đứng sau.

## Decision

**Ba lớp, tách bằng bảng riêng, không phải bằng cột cờ.**

| Lớp | Bảng | Quyền ghi |
|---|---|---|
| RAW | `raw_rows` | Chỉ ghi khi import. **Không UPDATE, không DELETE.** |
| WORKING | `working_rows`, `orders` | Engine ghi khi tính; người dùng ghi qua override |
| OVERRIDE | `overrides` | Người dùng |
| AUDIT | `audit_log` | Chỉ append |
| REPORT | không lưu | Tính từ WORKING mỗi lần cần |

**RAW bất biến.** Mỗi dòng giữ `source_file`, `source_sheet`, `source_row`,
`imported_at`, `import_batch_id`, và một `row_hash` của toàn bộ giá trị gốc.
Import lại cùng file → phát hiện trùng qua hash, không tạo bản ghi thứ hai.

**Override là bản ghi riêng, không phải ô bị ghi đè.**

```
overrides(entity_type, entity_id, field, value, reason, created_by, created_at, active)
```

Giá trị tự động **không bao giờ bị mất**. `working_rows` giữ cả hai cột cho mỗi
trường có thể override — ví dụ `lead_source_auto` và `lead_source_manual` — và
`lead_source_final` là giá trị dẫn xuất. Reset về Auto = đặt `active = false`
cho override, không phải xóa.

**Ba cặp giá trị phải tách bạch tuyệt đối:**

| Sự thật kế toán | Con số dùng tính KPI |
|---|---|
| `accounting_purchase_price` | `kpi_purchase_price` |
| `accounting_profit` | `eligible_kpi_profit` |
| `source_profit` *(từ ERP, chỉ đọc)* | — |

`kpi_purchase_price = accounting_purchase_price + kpi_purchase_adjustment`.
Điều chỉnh KPI **không bao giờ** được ghi vào cột kế toán.

**Audit trail** theo đúng mục 19: `entity`, `field`, `original_value`,
`new_value`, `changed_at`, `changed_by`, `reason`, `source`. Chỉ append.

**LeadSource được quyết định ở cấp OrderID rồi lan xuống line.** `orders` giữ
`lead_source_final`; `working_rows` tham chiếu tới order chứ không giữ bản sao
độc lập. Không thể xảy ra tình trạng 4 dòng của một đơn có 2 nguồn khác nhau.

**REPORT không được lưu.** Mọi con số Summary tính lại từ WORKING. Một Summary
được lưu là một Summary sẽ lệch với dữ liệu vào lúc nào đó không ai biết.

## Alternatives Considered

1. **Một bảng phẳng, sửa tại chỗ, có cột `is_modified`.** Đơn giản nhất.
2. **Event sourcing đầy đủ** — chỉ lưu chuỗi sự kiện, dựng lại trạng thái.
3. **Lưu Summary đã tính để truy vấn nhanh.**

## Rationale

**Vì sao không sửa tại chỗ.** Đó chính xác là cách file Excel hiện tại đang làm,
và là lý do không ai còn biết `5870` hay `5620` mới là giá nhập thật của dòng
đó. Một cột `is_modified` cho biết *có* sửa, không cho biết sửa từ giá trị nào.

**Vì sao không event sourcing.** Đúng về mặt lý thuyết nhưng quá nặng cho một
công cụ nội bộ vài người dùng. Audit log chỉ-append đã đủ trả lời mọi câu hỏi
mà đặc tả đặt ra, với chi phí bằng một phần nhỏ.

**Vì sao không lưu Summary.** Mục 28 yêu cầu *"Summary cập nhật ngay sau chỉnh
sửa"*. Với khối lượng thực tế — 8.714 đơn cho 6 tháng — tính lại là chuyện của
mili giây. Cache là tối ưu hóa, và chưa có dữ liệu nào nói rằng cần tối ưu.

**Vì sao tách cặp giá trị kế toán/KPI ở tầng schema.** Nếu chúng là cùng một cột
với một cờ đi kèm, sớm muộn sẽ có một truy vấn quên lọc cờ. Hai cột riêng làm
cho việc dùng nhầm trở thành lỗi nhìn thấy được khi đọc code, chứ không phải
một con số sai âm thầm trên bảng lương.

## Consequences

### Positive
- Trả lời được "vì sao con số này là như vậy" cho bất kỳ ô nào.
- Reset override về Auto là thao tác an toàn, không mất dữ liệu.
- Import lại file thô không xóa công sức chỉnh tay.
- Dữ liệu kế toán không thể bị hỏng bởi một điều chỉnh KPI.

### Negative / Tradeoffs
- Nhiều bảng hơn, join nhiều hơn.
- `working_rows` rộng — mỗi trường override được tốn 2–3 cột.
- Tính lại Summary mỗi lần đọc; nếu dữ liệu lớn lên nhiều lần sẽ phải xem lại.
- Import lại cùng một file cần logic đối chiếu hash, không chỉ là chèn thêm.

## Migration / Implementation Notes

- `raw_rows` không có endpoint UPDATE hay DELETE. Không phải quy ước — không
  viết ra.
- Mọi hàm ghi vào `working_rows` do người dùng kích hoạt đều phải đi qua
  `audit_service`. Không có đường vòng.
- `reason` bắt buộc với override trên trường tiền tệ và trên `lead_source`.
- Ở Phase 1 (chưa có DB), ba lớp này tồn tại dưới dạng ba dataclass tách biệt
  trong bộ nhớ và ba sheet riêng trong file export. Ranh giới giống hệt, chỉ
  khác chỗ lưu.

## Supersedes
None

## Superseded By
None
