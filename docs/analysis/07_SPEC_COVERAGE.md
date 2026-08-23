# 07 — Ma trận truy vết đặc tả

Đối chiếu **toàn bộ 31 mục** của `docs/spec/Dac_ta_cong_cu_bao_cao_kinh_doanh.docx`
với những gì đã nằm trong repo.

Cập nhật: 2026-08-22.

## Cách đọc trạng thái

| Ký hiệu | Nghĩa |
|---|---|
| **PHÂN TÍCH XONG** | Đã đối chiếu với dữ liệu thật, đã chốt cách làm, có quyết định ghi lại |
| **ĐÃ GHI NHẬN** | Yêu cầu đã nằm trong repo và gắn với một task, chưa phân tích sâu (chưa cần) |
| **CHƯA LÀM** | Chưa có dòng code nào — đúng như kế hoạch, Phase 1 chưa bắt đầu |

**Không mục nào đang ở trạng thái "bỏ sót".** Chưa có dòng mã ứng dụng nào tồn
tại: toàn bộ 31 mục hiện dừng ở mức yêu cầu đã được nắm và giao cho task.

---

## Ma trận

| § | Nội dung đặc tả | Nắm ở đâu trong repo | Task thực thi | Trạng thái |
|---|---|---|---|---|
| 1 | Mục tiêu sản phẩm (8 gạch đầu dòng) | `PROJECT_PROGRESS.md` → Objective; toàn bộ roadmap | Cả 4 phase | PHÂN TÍCH XONG |
| 2 | File đầu vào để đối chiếu | `00_README.md`; `data/samples/` | TASK-002 ✅ | PHÂN TÍCH XONG |
| 3 | Cấu trúc file thô (17 cột) | `01_DATA_MAPPING.md` §1–2 — đủ 17 cột, header 2 tầng dòng 4–5, dữ liệu từ dòng 6 | TASK-101 | PHÂN TÍCH XONG |
| 4 | Ba lớp RAW / WORKING / REPORT | `ADR-002` | TASK-101, TASK-201 | PHÂN TÍCH XONG |
| 5 | **Rule ADS cấp OrderID** | `06_ADS_RULE_VERIFICATION.md`; DEC-002, DEC-009 | TASK-104 | PHÂN TÍCH XONG |
| 6 | **Hai bucket quy đổi PERSONAL / ADS** | `02_FORMULA_MAPPING.md` §4 — tìm ra công thức tách tay của Hoàng/Kiên | TASK-108 | PHÂN TÍCH XONG |
| 7 | Thứ tự ưu tiên LeadSource | `06` §7 — chuỗi 4 bậc sau DEC-009 | TASK-104 | PHÂN TÍCH XONG |
| 8 | Employee Mapping | `01` §5 — 14 NVBH thật, 88 dòng chưa map; DEC-004 | TASK-102 | PHÂN TÍCH XONG |
| 9 | Working Data schema (35 field) | `01` §2 — đủ 35 field, ghi rõ field nào không có nguồn thô | TASK-101 | PHÂN TÍCH XONG |
| 10 | Giá nhập kế toán vs giá nhập KPI | `02` §1 — giải mã được `F` = KPI, `L` = kế toán; DEC-003 | TASK-105 | PHÂN TÍCH XONG |
| 11 | Adjustment nghiệp vụ (qua kho) | `03` — từ vựng thật: `Qua kho`, `KHBH`, `Thợ lắp`, `NCC giao` | TASK-106 | PHÂN TÍCH XONG |
| 12 | Conversion Rule Engine | `04` §1 — 5 tỉ lệ; `03` — bảng config | TASK-108 | PHÂN TÍCH XONG |
| 13 | Xử lý ghi chú ADS (kỹ thuật) | `06` §2–4; DEC-011 | TASK-104 | PHÂN TÍCH XONG |
| 14 | Chi tiết nhân viên theo tháng (22 cột) | `01` §2, §4 — ánh xạ 6 layout về 1 | TASK-111, TASK-302 | PHÂN TÍCH XONG |
| 15 | **Summary tháng Personal/ADS/Total + YTD** | `02` §3; **YTD bổ sung vào TASK-109** | TASK-109 | ĐÃ GHI NHẬN |
| 16 | **Summary năm / Dashboard** | **Bổ sung chi tiết vào TASK-303** | TASK-303 | ĐÃ GHI NHẬN |
| 17 | Product / Transaction Classification | `03` — bảng phân loại; DEC-010, DEC-013 | TASK-103 | PHÂN TÍCH XONG |
| 18 | **Data Validation & Review Queue (5 loại)** | **Bổ sung 5 loại cảnh báo vào TASK-110** | TASK-110 | ĐÃ GHI NHẬN |
| 19 | Manual Override & Audit Trail (8 field) | `03` §M; `ADR-002` | TASK-202 | PHÂN TÍCH XONG |
| 20 | **Price Master (8 field)** | **Bổ sung schema vào TASK-401**; DEC-003 | TASK-401 | ĐÃ GHI NHẬN |
| 21 | Target và Commission | `04` §3–4 — bảng target và tỉ lệ thưởng thật; DEC-016 | TASK-403 | PHÂN TÍCH XONG |
| 22 | Import workflow (15 bước) | **Bổ sung 15 bước vào TASK-101** | TASK-101…112 | ĐÃ GHI NHẬN |
| 23 | **Export Excel (5 loại sheet)** | **Bổ sung danh sách sheet vào TASK-111**; DEC-015 | TASK-111 | ĐÃ GHI NHẬN |
| 24 | Kiến trúc code (13 module) | `ADR-001` — 9 module gộp từ 13 engine | Cả Phase 1 | PHÂN TÍCH XONG |
| 25 | Công nghệ đề xuất | `ADR-001` — chọn FastAPI + React thay Streamlit, có lý do | Cả 4 phase | PHÂN TÍCH XONG |
| 26 | Thứ tự ưu tiên dữ liệu | `03` cuối — `Manual ?? Rule ?? Master ?? Raw ?? Missing` | TASK-104…108 | PHÂN TÍCH XONG |
| 27 | **Phải phân tích trước khi code** | `docs/analysis/` 01–06 + `tools/analysis/` | TASK-002 ✅ | **HOÀN THÀNH** |
| 28 | Tiêu chí nghiệm thu MVP (14 mục) | Xem §"14 tiêu chí" bên dưới | GATE-03 | ĐÃ GHI NHẬN |
| 29 | Test case rule ADS (8 case) | `tools/analysis/verify_ads_rule.py` — **18/18 PASS** | TASK-104 | **HOÀN THÀNH** |
| 30 | Tách dữ liệu kế toán và dữ liệu KPI | `ADR-002`; `02` §1; DEC-003 | TASK-107 | PHÂN TÍCH XONG |
| 31 | Prompt khởi động gợi ý | Đã thực hiện — chính là quy trình S000 → GATE-00 | — | **HOÀN THÀNH** |

---

## 14 tiêu chí nghiệm thu MVP (mục 28)

Không tiêu chí nào đã đạt — Phase 1 chưa bắt đầu. Cột cuối cho biết tiêu chí
được chứng minh ở đâu.

| # | Tiêu chí | Task | Bằng chứng dự kiến |
|---|---|---|---|
| 1 | Upload file thô, giữ nguyên Raw Data | TASK-101 | `ADR-002` — RAW bất biến, có `source_row` |
| 2 | Nhận diện đúng ngày/tháng, NVBH, OrderID | TASK-101/102/103 | Đối chiếu 30 kỳ × nhân viên |
| 3 | **Đếm đúng unique Số BH** | TASK-103 | Tín Phát 01.2026 = 254, 06.2026 = 146 |
| 4 | Rule ADS: 1 dòng có ADS → cả đơn ADS | TASK-104 | Case 4, `verify_ads_rule.py` |
| 5 | Không có ADS → PERSONAL | TASK-104 | Case 5 |
| 6 | Override nguồn đơn theo OrderID, đồng bộ mọi line | TASK-104/202 | Case 6, 7, 15 |
| 7 | **Tách đúng Personal Profit và Ads Profit** | TASK-108 | Case 8a/8b |
| 8 | Áp đúng ConversionScheme theo nguồn đơn | TASK-108 | Bảng tỉ lệ `04` §1 |
| 9 | **Total CR = tổng hai bucket** | TASK-108 | REQUIRED check, Hoàng+Kiên = 13.883.242 |
| 10 | Nhập/sửa được giá nhập và giá nhập KPI | TASK-105 | DEC-003 |
| 11 | Có adjustment nghiệp vụ và audit trail | TASK-106/202 | Từ vựng `03`; 8 field audit |
| 12 | Summary cập nhật ngay sau chỉnh sửa | TASK-205 | Recalc incremental |
| 13 | Summary hiển thị Personal / ADS / Total | TASK-109 | `02` §3 |
| 14 | **Không hard-code nhân viên, margin, target, adjustment** | Mọi phase | `04` §8 — 47 giá trị; check bằng `grep` |

---

## Ba yêu cầu quan trọng nhất — đã nắm chắc đến đâu

### Rule ADS (§5, §7, §13, §29)
Đã có bản cài đặt tham chiếu chạy được: `tools/analysis/verify_ads_rule.py`,
**18/18 case PASS** (8 case bắt buộc của đặc tả + 4 case biên + 5 case cho mặc
định cấp nhân viên của DEC-009). Chạy lại bất cứ lúc nào:

```bash
python tools/analysis/verify_ads_rule.py --raw data/samples/So_chi_tiet_ban_hang.xlsx
```

### Hai bucket quy đổi (§6, §12)
Không chỉ hiểu yêu cầu mà đã **tìm được nó đang tồn tại dưới dạng thủ công**:
Hoàng và Kiên dùng `=(G−X)/5.5% + X/7.5%` với `X` gõ tay 14 lần trong 8 tháng.
Tỉ lệ PERSONAL 5,5 % và ADS 7,5 % lấy từ chính workbook, không phải phỏng đoán.
Mốc đối chiếu **13.883.242 nghìn đồng** đã thành REQUIRED check của TASK-108.

### Tách dữ liệu kế toán và KPI (§10, §30)
Giải mã được hai cột giá nhập bị đặt tên gây nhầm: `Giá nhập TT` (`F`) là giá
**KPI**, `Giá thực nhập` (`L`) là giá **kế toán** — ngược với trực giác từ tên
cột. Bằng chứng: `F` thấp hơn `L` đúng bằng số ghi trong cột điều chỉnh, và
Summary gọi cột lấy từ `L` là "Lợi nhuận thực tế".

---

## Những gì đặc tả không lường trước, phát hiện từ dữ liệu

Đây là phần nằm ngoài 31 mục — không có trong đặc tả nhưng bắt buộc phải xử lý:

| Phát hiện | Ở đâu | Ảnh hưởng |
|---|---|---|
| Chuỗi "ADS" xuất hiện **0 lần** trong cả hai file | `06` §1 | RISK-01 |
| File thô **không có giá nhập**, chỉ có lợi nhuận ERP | `01` §3 | RISK-03, DEC-003 |
| File thô **không có** `Nơi nhập` | `01` §2 | Nhập tay hoặc lấy từ hệ thống kho |
| 6 biến thể layout sheet nhân viên | `01` §4 | Exporter chỉ xuất 1 layout |
| 6 lỗi công thức trong file mẫu | `05` nhóm A | DEC-007 — không tái tạo |
| Tổng tháng bỏ sót **60 %** doanh thu quy đổi | `05` §A2 | Lỗi nặng nhất tìm được |
| Đơn vị tiền lệch 1.000 lần giữa 2 sheet | `02` §5 | ADR-003 |
| 88 dòng có NVBH chưa map | `01` §5 | Review Queue |
| 1.912 dòng lợi nhuận âm | `01` §3 | Review Queue loại `Suspicious` |
| 408 dòng có chiết khấu, 302 của Ly | `03` | DEC-014 |
