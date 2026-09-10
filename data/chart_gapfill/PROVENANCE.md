# Nguồn Lấp Lỗ Hổng Biểu Đồ — Xuất Xứ và Luật Trích Xuất

`DEC-216`. File này giải thích `daily_revenue.jsonl` đến từ đâu, được trích
theo luật nào, gặp những bất thường gì và chủ dự án đã quyết ra sao với từng
bất thường. Không đọc file này thì không có cách nào kiểm lại con số.

## Đây KHÔNG phải một nguồn legacy

`DEC-181` (`OWNER_DECISION`, đã freeze) khoá lịch sử ở đúng hai file nguồn và
ghi rõ "Không thêm nguồn legacy nào nữa"; `POST /du-lieu/legacy` trả 409 vô
điều kiện. Quyết định đó KHÔNG bị nới ở đây: dữ liệu này không đi vào bảng
`legacy_*`, không qua route đó, không xuất hiện trong `legacy_reference`, và
mang origin riêng `CHART_GAPFILL`.

Nó cũng KHÔNG phải một định nghĩa doanh thu thứ hai. Thẩm quyền cho tổng một
kỳ số cũ vẫn chỉ có một chỗ: `legacy_reference.authoritative_period_sales`.
Dữ liệu ở đây chỉ để VẼ ở mức Ngày/Tuần, nơi bản ghi lịch sử không có điểm
nào vì nó chỉ lưu tổng tháng.

## Vì sao cần

`app/legacy/parser.py::parse_year_workbook` trả `daily_sales=[]`: 74 sheet
chi tiết của năm 2025 chỉ được ghi TÊN, không đọc một ô nào, theo
`LEGACY_LINE_DETAIL_2025 = DEFERRED` — các sheet ấy chứa tên, số điện thoại
và địa chỉ khách hàng (`governance/product/17_DATA_GOVERNANCE_PRIVACY.md`).
Hệ quả trên màn hình: ở mức Ngày, đường "Cùng kỳ năm trước" trống hoàn toàn.
`§CHART-10` cấm lấp chỗ đó bằng cách chia tổng tháng ra ngày.

## Dữ liệu cá nhân

Chỉ HAI cột được đọc: `Date` và `Tổng bán`. Không cột nào chứa dữ liệu cá
nhân khách hàng được đọc, lưu, hay in ra trong quá trình trích xuất. File
kết quả chỉ có ngày và một con số tổng của cả công ty — không tên nhân viên,
không khách hàng, không đơn hàng.

## Nguồn và phạm vi

Hai workbook kế toán của chủ dự án (`Báo cáo Kinh doanh 2025.xlsx` và
`Báo cáo Kinh doanh 2026.xlsx`) — cùng hai file mà `DEC-181` đã chốt, nhưng
đọc ở các sheet chi tiết mà đường legacy cố ý không đọc. Bản thân workbook
KHÔNG được commit (`.gitignore`: `*.xlsx`).

- 130 sheet chi tiết khớp mẫu tên `MM.YYYY <nhãn>`; 7 biến thể bố cục, tất cả
  có dòng tiêu đề ở hàng 2 và đều có `Date` + `Tổng bán`.
- Cột `Date` thưa (chỉ ghi ở dòng đầu mỗi ngày) → điền xuôi xuống.
- Hệ số chia đọc MÁY MÓC từ công thức ở ô hàng 1 của chính cột `Tổng bán`:
  sheet nhân viên dùng `=SUM(H3:H614)`, sheet kênh (Nội thành / Gia dụng /
  Fanpage) dùng `=SUM(G3:G803)/2`. Không suy đoán: `/2` là một quy ước kế
  toán của chủ dự án, và nó được tôn trọng đúng như file ghi.
- Đơn vị trong workbook là nghìn đồng (`kVND`), giống `Summary`. File
  `daily_revenue.jsonl` lưu VND NGUYÊN (đã nhân 1.000) để tầng vẽ không phải
  đổi đơn vị lần nữa.

## Thẩm quyền tổng tháng

Tổng tháng chính thức lấy từ dòng `MONTH_TOTAL` ĐẦU TIÊN của workbook có thẩm
quyền cho năm đó — đúng phép giải mà `legacy_reference._summary_month_total`
đang chạy trong production. Điều này quan trọng vì hai lý do đã kiểm chứng:

1. `Summary 2026` có khối tháng 8/2026 bị LẶP nguyên văn (hàng 68–73 lặp lại
   thành 75–80, kể cả dòng `MONTH_TOTAL`). Cộng các dòng `SELLER` sẽ cộng đôi
   tháng ấy. Hệ thống thật KHÔNG bị: nó lấy dòng khớp đầu tiên rồi dừng.
2. Năm 2026, `MONTH_TOTAL` chính thức KHÔNG bao gồm dòng `Gia dụng` — đúng
   8/8 tháng, lệch bằng đúng giá trị dòng đó. Năm 2025 không có hiện tượng
   này. 8 sheet `Gia dụng` vì thế bị loại khỏi chuỗi ngày, để chuỗi ngày và
   tổng tháng cùng nói một con số (`DEC-180` §9).

## Bất thường và quyết định của chủ dự án

| Bất thường | Quy mô | Quyết định |
|---|---|---|
| Dòng không ghi ngày | 29 dòng · 775.400 kVND (trong đó 300.600 ở 08/2025) | Không đặt lên biểu đồ, báo riêng |
| Dòng ghi ngày lệch tháng của sheet | 301 dòng · 2.675.800 kVND | Giữ nguyên ngày đã ghi |
| Ngày BẤT KHẢ THI (ngoài 01/2025–08/2026) | 4 ngày: 2024-01-02, 2024-01-03, 2024-01-12, 2026-12-31 | Nắn về năm+tháng của tên sheet, giữ nguyên phần ngày |
| Sheet không có dòng trong `Summary` | `02.2025 Miền Bắc`, `02.2026 Fanpage`, `03.2026 Fanpage` | Loại — bám theo tổng tháng chính thức |

## Đối soát

Gom cùng tập số liệu theo THÁNG CỦA SHEET và so với `MONTH_TOTAL` chính thức:
**18/20 tháng khớp tuyệt đối**. Hai tháng lệch, và mỗi lệch bằng ĐÚNG giá trị
của một sheet mà chủ dự án đã chọn loại:

| Tháng | Lệch (kVND) | Nguyên nhân |
|---|---|---|
| 2025-02 | −490.300 | sheet `02.2025 Miền Bắc` |
| 2026-03 | −114.800 | sheet `03.2026 Fanpage` |

Không còn lệch nào chưa giải thích được.

## Kết quả

579 ngày, 2025-01-02 → 2026-08-31, tổng 362.170.585 nghìn đồng
(362.170.585.000 VND). Ngày không có dòng nào thì KHÔNG có bản ghi — một ngày
vắng mặt là "không có bằng chứng", không phải số 0 (`GAP_NOTE`). Ví dụ
2025-09-02 (Quốc khánh) không có mặt trong file.
