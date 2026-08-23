# 10 — Câu hỏi nghiệp vụ còn mở

Danh sách các điểm **chưa đủ thông tin để quyết định**, tính đến 2026-08-23 sau
đợt xác nhận nghiệp vụ của chủ dự án (DEC-119, DEC-120, DEC-121).

Mỗi câu hỏi ghi rõ: mặc định đang áp dụng, hệ quả nếu mặc định sai, và mốc muộn
nhất cần câu trả lời. **Không câu nào trong danh sách này chặn việc bắt đầu
Phase 1** — tất cả đều là một dòng cấu hình hoặc một quyết định ở gate sau.

| # | Câu hỏi | Mặc định đang áp dụng | Cần trước |
|---|---|---|---|
| C4b | `Chiết khấu` có trừ vào lợi nhuận cùng số đó không? | Có — trừ cả doanh số lẫn lợi nhuận | GATE-01 |
| **C9** | **Đơn của Nội thành / Gia dụng có chữ "ADS" thì quy đổi ở tỉ lệ nào?** | **7,5 %** (rơi vào dòng `* + ADS`) | GATE-01 |
| **C10** | **Chính sách từ 01/01/2027 khác 2026 ở điểm nào?** | Không đổi — chưa có dòng config nào cho 2027 | 01/12/2026 |
| **C11** | **Nhân viên chưa map (88 dòng) xử lý thế nào khi lên production?** | Vào Review Queue loại `Missing`, không tính vào KPI | GATE-01 |

---

## C4b — Chiết khấu và lợi nhuận

**Trạng thái:** mở từ 2026-08-22, không đổi qua đợt xác nhận này.

Chủ dự án nói "trừ vào doanh số" (DEC-114) và chưa nói tới lợi nhuận. Công cụ
đang áp dụng:

```
EligibleKpiProfit = (SellPrice − KpiPurchasePrice) × Quantity
                    − Discount − EligibleCosts + OtherKpiAdjustment
```

**Nếu mặc định sai:** tỉ suất lợi nhuận báo cáo sẽ thấp hơn thực tế. Đảo lại chỉ
mất một cờ cấu hình.

**Vì sao chọn mặc định này:** giảm doanh số mà không giảm lợi nhuận sẽ báo một
tỉ suất công ty không thực sự đạt được — chiết khấu là tiền đã cho đi.

**Quy mô:** 408 dòng, 36.750 nghìn đồng, 0,03 % doanh số công ty. Riêng Ly
chiếm 302 dòng và 0,39 % doanh số của cô ấy.

---

## C9 — Nguồn ADS cho nhân viên kênh

**Trạng thái:** mới, phát sinh từ chính DEC-119.

Xác nhận nghiệp vụ nói rõ hai điều, và chúng giao nhau ở một ô chưa được định
nghĩa:

- Rule ADS áp dụng cho **"các nhân viên khác"** — không loại trừ ai. Một đơn của
  Vinh/Quý/Hiệp có chữ "ADS" trong `Diễn giải` sẽ thành `LeadSource = ADS`.
- Bảng tỉ lệ chỉ định nghĩa `(Nội thành, PERSONAL) → 2 %`. Không có dòng nào cho
  `(Nội thành, ADS)`.

Với chuỗi phân giải hiện tại, đơn đó rơi vào dòng `* + ADS` và quy đổi ở
**7,5 %** — gấp gần 4 lần tỉ lệ 2 % thường ngày của kênh.

**Ba hướng, đều là một dòng cấu hình:**

| Hướng | Cấu hình | Hệ quả |
|---|---|---|
| A — giữ nguyên hiện tại | không thêm dòng nào | Đơn ADS của kênh quy đổi 7,5 % |
| B — kênh luôn 2 % bất kể nguồn | thêm `(Nội thành, ADS) → NOI_THANH_2` | Nguồn đơn vẫn ghi nhận được để báo cáo, nhưng không đổi tiền |
| C — kênh có tỉ lệ ADS riêng | thêm `(Nội thành, ADS) → <scheme mới>` | Cần chủ dự án cho con số |

**Vì sao chưa chặn:** chuỗi "ADS" xuất hiện **0 lần** trong toàn bộ dữ liệu 6
tháng (`06_ADS_RULE_VERIFICATION.md` §1), nên tổ hợp này hiện chưa từng xảy ra
lần nào. Nó chỉ thành vấn đề thật khi một nhân viên kênh bắt đầu gõ "ADS".

**Khuyến nghị:** hướng **B**. Tỉ lệ 2 % của kênh phản ánh cấu trúc chi phí của
kênh, không phản ánh nguồn lead; nhảy sang 7,5 % vì một chữ trong ghi chú là
một thay đổi lớn về tiền do một thao tác nhỏ. Hướng B vẫn giữ được thông tin
nguồn đơn cho báo cáo §15/§16.

---

## C10 — Nội dung chính sách 2027

**Trạng thái:** mới, phát sinh từ DEC-121.

Đã biết: **mốc thời gian** 01/01/2027, quy trình mới thành chuẩn chính thức.
Chưa biết: **chính sách 2027 có khác 2026 không**, và khác ở đâu.

Hệ thống đã sẵn sàng cho cả hai khả năng — mọi dòng chính sách mang
`effective_from`/`effective_to`, và việc tra cứu dùng ngày của đơn. Nếu 2027
không đổi gì, không cần làm gì cả.

**Cần trước 01/12/2026** để kịp cấu hình và kiểm thử trước khi mốc có hiệu lực.

---

## C11 — 88 dòng nhân viên chưa map

**Trạng thái:** đã biết từ TASK-002, chưa có quyết định vận hành.

6 giá trị `NVBH` trong file thô chưa có mapping: `Thảo Linh` (63 dòng),
`Tống Khánh Linh` (14), `Lê Quang Trường` (6), `Lê Văn Quân` (2),
`Nguyễn Thị Minh Bảo` (1), và 2 dòng rỗng.

Mặc định hiện tại: vào Review Queue loại `Missing`, không tính vào KPI của ai,
không bị bỏ im lặng.

**Câu hỏi thật:** những người này là nhân viên đã nghỉ, nhân viên thời vụ, hay
lỗi nhập liệu? Câu trả lời quyết định họ cần một dòng trong `employees.yaml` với
`effective_to`, hay chỉ cần một quy tắc gộp.

**Quy mô:** 88/11.765 dòng = 0,75 %. Không chặn Phase 1 — engine xử lý được
bằng Review Queue.

---

## Đã đóng trong đợt xác nhận 2026-08-23

| # | Câu hỏi | Đóng bởi |
|---|---|---|
| C1 | Tín Phát có mặc định ADS không? | DEC-109, sửa đổi bởi DEC-119 |
| C2 | Vì sao sheet kênh chia đôi? | DEC-115 |
| C3 | Rule hoa hồng? | DEC-116 — công thức hóa ở TASK-403 |
| C4 | `Chiết khấu` trừ vào đâu? | DEC-114 (phần lợi nhuận vẫn mở — C4b) |
| C5 | Dòng phụ tính vào đâu? | DEC-110 |
| C6 | Sửa được `Diễn giải` không? | DEC-111 |
| C7 | Đơn ADS lịch sử xử lý thế nào? | **DEC-120 — không di trú** |
| C8 | Số SP loại trừ dòng phụ? | DEC-113 |
