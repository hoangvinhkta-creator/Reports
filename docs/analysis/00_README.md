# Phân tích nguồn — Báo cáo Kinh doanh Tín Phát

Bộ tài liệu này là sản phẩm bắt buộc của **mục 27 đặc tả**: *"Chưa code ứng
dụng trước khi hoàn thành bước phân tích này."*

## Nguồn dữ liệu

| File | Vai trò | Ghi chú |
|---|---|---|
| `data/samples/So_chi_tiet_ban_hang.xlsx` | File doanh số thô từ ERP | 11.765 dòng, 8.714 Số BH, 01/01/2026 → 30/06/2026 |
| `data/samples/Bao_cao_Kinh_doanh_2026.xlsx` | File báo cáo mẫu đang dùng thủ công | 59 sheet: 56 sheet nhân viên + Summary 2025 + Summary 2026 + DataChart 2026 |
| `docs/spec/Dac_ta_cong_cu_bao_cao_kinh_doanh.docx` | Đặc tả sản phẩm | 31 mục |

Hai file Excel **không nằm trong git** (chứa dữ liệu cá nhân khách hàng — xem
`.gitignore` và DEC-008). Muốn kiểm chứng lại, đặt file vào `data/samples/`
rồi chạy lệnh dưới.

## Cách tái tạo mọi con số trong bộ tài liệu này

```bash
python tools/analysis/extract_evidence.py \
  --raw data/samples/So_chi_tiet_ban_hang.xlsx \
  --report data/samples/Bao_cao_Kinh_doanh_2026.xlsx \
  --out docs/analysis/_evidence
```

Kết quả ghi vào `docs/analysis/_evidence/evidence.json`. **Mọi con số được
trích dẫn trong 6 tài liệu dưới đây đều lấy từ file đó**, không có con số nào
viết từ trí nhớ.

## Mục lục

| # | Tài liệu | Trả lời cho mục 27 |
|---|---|---|
| 01 | [`01_DATA_MAPPING.md`](01_DATA_MAPPING.md) | Data Mapping: Raw → Processed → Report |
| 02 | [`02_FORMULA_MAPPING.md`](02_FORMULA_MAPPING.md) | Formula Mapping |
| 03 | [`03_RULE_CLASSIFICATION.md`](03_RULE_CLASSIFICATION.md) | Universal / Business rule / Manual-special case |
| 04 | [`04_HARDCODED_VALUES.md`](04_HARDCODED_VALUES.md) | Danh sách hard-coded values |
| 05 | [`05_EXCEPTIONS.md`](05_EXCEPTIONS.md) | Exception và công thức không đồng nhất |
| 06 | [`06_ADS_RULE_VERIFICATION.md`](06_ADS_RULE_VERIFICATION.md) | Xác nhận cách cột Ghi chú/Diễn giải lưu chuỗi ADS |

## Kết luận ngắn gọn cho người duyệt

1. **Mapping nhân viên và cách đếm đơn là đúng.** `COUNT DISTINCT Số BH` khớp
   tuyệt đối với báo cáo ở 8/30 kỳ-nhân-viên và lệch không quá 3 đơn ở 22/30
   kỳ còn lại. Chênh lệch là do loại trừ tay, không phải sai logic.
2. **"Hai hệ quy đổi" trong đặc tả đã tồn tại sẵn — nhưng đang làm tay.**
   Hoàng và Kiên đang dùng `=(G−X)/5.5% + X/7.5%` với `X` gõ tay mỗi tháng.
   Công cụ này thay `X` bằng phép phân loại tự động.
3. **Rule ADS chưa có dữ liệu nào để chạy.** Chuỗi "ADS" xuất hiện **0 lần**
   trong cả hai file. Xem tài liệu 06.
4. **File mẫu có 6 lỗi công thức.** Công cụ sẽ tính đúng và báo cáo chênh lệch,
   không sao chép lỗi. Xem tài liệu 05 và DEC-007.
