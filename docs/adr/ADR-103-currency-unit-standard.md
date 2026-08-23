# ADR-103 — Chuẩn đơn vị tiền tệ

## Status
Accepted

## Date
2026-08-22

## Context

Hai file nguồn dùng hai đơn vị khác nhau cho cùng một loại số liệu:

| Nguồn | Đơn vị | Ví dụ |
|---|---|---|
| `So_chi_tiet_ban_hang.xlsx` | **VND nguyên** | `8000000` = tám triệu |
| `Bao_cao_Kinh_doanh_2026.xlsx` | **nghìn đồng** | `11770` = 11,77 triệu |

Tệ hơn, sự lẫn lộn này đã xảy ra **bên trong** file báo cáo. Ở sheet
`DataChart 2026`:

| Ô | Giá trị | Đơn vị thực tế |
|---|---|---|
| `AJ2` — target tháng | `28.789.481.081` | VND |
| `J15` — target năm | `345.474.000` | nghìn đồng |
| `B3:AF14` — doanh số ngày | `789.675.000` | VND |

`J15` phải là nghìn đồng để bằng `12 × AJ2`, trong khi mọi ô khác cùng sheet là
VND. Hai ô cách nhau vài cột, lệch nhau 1.000 lần.

Đây là số liệu quyết định lương và thưởng của nhân viên.

## Decision

**1. Lưu trữ: VND nguyên, kiểu `Decimal`.**

Mọi giá trị tiền trong RAW, WORKING và audit log đều là VND nguyên. Trong
PostgreSQL là `NUMERIC(18, 2)`; trong Python là `decimal.Decimal`.

**Cấm `float` cho tiền ở mọi tầng.** `0.1 + 0.2 != 0.3` là chuyện nhỏ khi in ra
màn hình và là chuyện lớn khi cộng dồn 11.765 dòng thành con số trả lương.

**2. Đơn vị chỉ được chuyển đổi ở hai biên: import và export.**

```
Excel thô (VND) ──[importer]──► VND Decimal ──[engine]──► VND Decimal
                                                              │
                                        [exporter / API serializer]
                                                              ▼
                                              hiển thị theo display_unit
```

Không engine nào biết tới khái niệm "nghìn đồng". Không có phép nhân hay chia
1.000 nào nằm ngoài `importing/` và `reporting/`.

**3. Đơn vị hiển thị là cấu hình, mặc định `THOUSAND`.**

`config/settings.yaml`:
```yaml
currency:
  storage_unit: VND        # không đổi được
  display_unit: THOUSAND   # VND | THOUSAND | MILLION
```

Mặc định `THOUSAND` để khớp thói quen đọc báo cáo hiện tại.

**4. Mọi sheet xuất ra phải ghi rõ đơn vị.** Ô A1 của mỗi sheet ghi
`Đơn vị: nghìn đồng`. File mẫu không ghi ở đâu cả — đó là gốc rễ của lỗi trên.

**5. Quy tắc làm tròn.** Chỉ làm tròn ở bước hiển thị cuối cùng, không làm tròn
giữa chừng. Chế độ `ROUND_HALF_UP`. Doanh thu quy đổi (`profit / rate`) làm
tròn đến đồng khi hiển thị nhưng giữ nguyên độ chính xác khi cộng dồn.

## Alternatives Considered

1. **Lưu bằng số nguyên đơn vị "xu"** (VND × 100).
2. **Lưu bằng nghìn đồng** cho khớp file báo cáo hiện tại.
3. **Dùng `float` cho đơn giản.**

## Rationale

**Vì sao không xu.** VND không có đơn vị nhỏ hơn đồng trong thực tế giao dịch.
Nhân thêm 100 chỉ tạo thêm một hệ số cho người đọc code hiểu nhầm.

**Vì sao không lưu bằng nghìn đồng.** File **thô** — nguồn dữ liệu thật, thứ
duy nhất không thể sửa được — dùng VND nguyên. Lưu bằng nghìn đồng nghĩa là
chia 1.000 ngay ở cửa vào và mất phần lẻ trên 11.765 dòng, để đổi lấy tiện lợi
khi so mắt với file báo cáo cũ. Đổi độ chính xác lấy sự tiện lợi, ở đúng chỗ
không nên đổi.

**Vì sao không `float`.** Xem trên. Đây là số tiền lương.

**Vì sao ghi đơn vị vào file xuất.** Vì `AJ2` và `J15` đã chứng minh rằng không
ghi thì sẽ nhầm — và người nhầm là người tạo ra chính file đó.

## Consequences

### Positive
- Không thể xảy ra lỗi lệch 1.000 lần bên trong hệ thống.
- Đối chiếu trực tiếp với file thô mà không cần chuyển đổi.
- Đổi cách hiển thị không chạm vào dữ liệu đã lưu.

### Negative / Tradeoffs
- Số lưu trong DB dài hơn, khó đọc bằng mắt khi truy vấn trực tiếp.
- `Decimal` chậm hơn `float`. Không đáng kể ở quy mô này.
- Cần test riêng cho ranh giới chuyển đổi ở import và export.

## Migration / Implementation Notes

- Test bắt buộc: một dòng thô `Đơn giá = 8000000` phải xuất ra `8000` khi
  `display_unit = THOUSAND`, và tổng của N dòng phải bằng tổng rồi mới chia,
  không phải chia rồi mới tổng.
- Test bắt buộc: `Decimal` được giữ nguyên qua toàn bộ pipeline — thêm một
  assert kiểu ở biên engine.
- Import từ file báo cáo cũ (nếu có, ở Phase 4) phải nhân 1.000. Đây là đường
  nhập liệu duy nhất dùng nghìn đồng làm đầu vào, và phải được đánh dấu rõ.

## Supersedes
None

## Superseded By
None
