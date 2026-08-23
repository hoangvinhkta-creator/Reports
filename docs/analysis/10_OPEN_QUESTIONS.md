# 10 — Câu hỏi nghiệp vụ còn mở

Câu hỏi nghiệp vụ mà chủ dự án cần trả lời, không phải câu hỏi kỹ thuật.
C1–C11 liên quan tới phân loại nguồn đơn và quy đổi doanh thu (PHASE-01);
C12–C14 liên quan tới phân quyền truy cập (PHASE-02, thêm 2026-08-23 khi làm
`ADR-105`).

Tính đến **2026-08-23**, sau khi GATE-00 đã được chủ dự án duyệt (DEC-122).

**Trạng thái:** C4b, C9, C10 đã đóng bằng xác nhận trực tiếp của chủ dự án.
**Còn mở: C11, C12, C13, C14.** Không câu nào chặn PHASE-01 — C11 đã có mặc
định Review Queue an toàn, và C12–C14 chỉ có hiệu lực từ PHASE-02 trở đi.
Nội dung đầy đủ giữ nguyên bên dưới để giữ mạch lý do; xem DEC-122 cho nguyên
văn câu trả lời của nhóm đầu.

| # | Câu hỏi | Trạng thái | Quyết định |
|---|---|---|---|
| C4b | `Chiết khấu` có trừ vào lợi nhuận cùng số đó không? | **ĐÃ ĐÓNG** (2026-08-23) | Có — DEC-122 |
| C9 | Đơn của Nội thành / Gia dụng có chữ "ADS" thì quy đổi ở tỉ lệ nào? | **ĐÃ ĐÓNG** (2026-08-23) | Không quan tâm, giữ 7,5 % mặc định — DEC-122 |
| C10 | Chính sách từ 01/01/2027 khác 2026 ở điểm nào? | **ĐÃ ĐÓNG cho hiện tại** (2026-08-23) | Không đổi — DEC-122, mở lại nếu có tin mới trước 01/12/2026 |
| **C11** | **Nhân viên chưa map (88 dòng) xử lý thế nào khi lên production?** | **CÒN MỞ** — chủ dự án chưa rõ | Vào Review Queue loại `Missing`, không tính vào KPI |
| **C12** | **Nhân viên có được xem số của nhân viên khác không?** | **CÒN MỞ** — chưa hỏi | Mặc định: chỉ sửa được đơn của chính mình — ADR-105 §5 |
| **C13** | **Ai được xem giá nhập và biên lợi nhuận?** | **CÒN MỞ** — chưa hỏi | Mặc định: chỉ `admin` — ADR-105 §4 |
| **C14** | **Ai được chốt (commit) một lần nạp dữ liệu?** | **CÒN MỞ** — chưa hỏi | Mặc định: chỉ `admin` — ADR-105 §4 |

---

## C4b — Chiết khấu và lợi nhuận

**Trạng thái: ĐÃ ĐÓNG (DEC-122, 2026-08-23).** Chủ dự án xác nhận *"mặc định
có"* — đúng hành vi đang áp dụng, không đổi gì.

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

**Trạng thái: ĐÃ ĐÓNG (DEC-122, 2026-08-23).** Chủ dự án xác nhận: *"đơn nội
thành / gia dụng luôn không xuất hiện ADS. không cần quan tâm."* **Không thêm
dòng scheme riêng** cho `(Nội thành, ADS)` / `(Gia dụng, ADS)`. Nếu tổ hợp này
phát sinh ngoài dự kiến, nó vẫn rơi vào dòng `* + ADS` (7,5 %) — hành vi đó đã
được chấp nhận, không cần một kết quả khác.

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

**Trạng thái: ĐÃ ĐÓNG cho hiện tại (DEC-122, 2026-08-23).** Chủ dự án xác
nhận: *"không đổi."* Đây là xác nhận trạng thái tại thời điểm hỏi, không phải
cam kết 2027 sẽ mãi giống 2026 — mốc "cần trước 01/12/2026" giữ nguyên phòng
khi có chính sách mới cần công bố.

Đã biết: **mốc thời gian** 01/01/2027, quy trình mới thành chuẩn chính thức.
Chưa biết: **chính sách 2027 có khác 2026 không**, và khác ở đâu.

Hệ thống đã sẵn sàng cho cả hai khả năng — mọi dòng chính sách mang
`effective_from`/`effective_to`, và việc tra cứu dùng ngày của đơn. Nếu 2027
không đổi gì, không cần làm gì cả.

**Cần trước 01/12/2026** để kịp cấu hình và kiểm thử trước khi mốc có hiệu lực.

---

## C11 — 88 dòng nhân viên chưa map

**Trạng thái: CÒN MỞ.** Chủ dự án được hỏi ngày 2026-08-23, trả lời *"tôi
chưa rõ"*. Giữ nguyên mặc định Review Queue — an toàn để bắt đầu Phase 1,
không cần câu trả lời ngay.

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

## C12 — Nhân viên có xem được số của nhau không?

**Trạng thái: CÒN MỞ — chưa hỏi chủ dự án.** Phát sinh khi soạn `ADR-105`
(2026-08-23), không phải từ đợt rà soát GATE-00.

**Hiện trạng:** cả đội dùng chung một file `Báo cáo Kinh doanh 2026.xlsx`, nên
trên thực tế ai mở file cũng thấy doanh số, lợi nhuận và phần trăm target của
tất cả mọi người.

**Mặc định đang áp dụng trong thiết kế:** `editor` chỉ **ghi đè** được trên đơn
của nhân viên mà tài khoản họ được gán; phần **xem** thì vẫn thấy toàn bộ, đúng
như hiện trạng. Tức mặc định chỉ siết quyền ghi, chưa siết quyền đọc.

**Câu hỏi thật cho chủ dự án:** khi lên hệ thống web có đăng nhập, một nhân viên
bán hàng có nên tiếp tục thấy con số của đồng nghiệp không?

| Hướng | Hệ quả |
|---|---|
| A — giữ như hiện trạng, ai cũng xem được tất cả | Không ai mất gì so với hôm nay; nhưng lương/KPI của từng người thành thông tin công khai nội bộ |
| B — mỗi người chỉ xem số của mình, quản lý xem tất cả | Kín hơn; nhưng mất khả năng tự so sánh giữa nhân viên mà bảng Summary hiện có |
| C — xem được tổng của đội, không xem được chi tiết từng người khác | Trung gian; tốn thêm việc ở TASK-109/303 |

**Vì sao chưa chặn:** chỉ có hiệu lực từ PHASE-02 (TASK-204). PHASE-01 là thư
viện Python chạy bằng CLI, chưa có khái niệm người dùng.

**Cần trước:** TASK-204 bắt đầu.

---

## C13 — Ai được xem giá nhập và biên lợi nhuận?

**Trạng thái: CÒN MỞ — chưa hỏi chủ dự án.**

`governance/core/04_SECURITY_RULES.md` §6 liệt kê giá vốn và biên lợi nhuận là
dữ liệu nghiệp vụ nhạy cảm phải bảo vệ. Nhưng bảng chi tiết nhân viên theo
tháng (đặc tả mục 14, 22 cột) **có cột giá nhập** — nên nếu chặn hẳn, màn hình
TASK-302 sẽ trống một phần với hầu hết người dùng.

**Mặc định đang áp dụng:** chỉ `admin` xem được `accounting_purchase_price` và
biên lợi nhuận; `viewer`/`editor` thấy các cột còn lại.

**Câu hỏi thật:** nhân viên bán hàng có được biết giá nhập của sản phẩm họ bán
không? Đây là câu hỏi về chính sách công ty, không phải về kỹ thuật — công cụ
làm được cả hai chiều.

**Lưu ý quan trọng:** `kpi_purchase_price` (dùng tính KPI) và
`accounting_purchase_price` (sự thật kế toán) là hai trường khác nhau theo
`ADR-102`. Có thể cho xem cái trước mà giấu cái sau — đây có lẽ là câu trả lời
hợp lý nhất, nhưng cần chủ dự án xác nhận.

**Cần trước:** TASK-204 bắt đầu.

---

## C14 — Ai được chốt một lần nạp dữ liệu?

**Trạng thái: CÒN MỞ — chưa hỏi chủ dự án.**

Quy trình nạp có hai bước tách rời (đặc tả mục 22, và `ADR-105` route
`POST /api/v1/imports` rồi `POST /api/v1/imports/{batchId}/commit`): tải file
lên xem trước metadata, rồi mới chốt. Bước chốt ghi đè dữ liệu của cả một kỳ.

**Mặc định đang áp dụng:** `editor` tải lên và xem trước được; chỉ `admin`
chốt được.

**Câu hỏi thật:** ai trong công ty là người chịu trách nhiệm bấm nút chốt số
liệu hằng tháng? Nếu đó là một nhân viên hành chính chứ không phải chủ dự án,
người đó cần vai trò `admin` — kéo theo họ cũng có toàn quyền sửa cấu hình và
quản trị người dùng, điều có thể không mong muốn.

**Nếu câu trả lời là "một người không nên có toàn quyền admin":** cần tách
thành vai trò thứ tư (ví dụ `operator`), và đó là thay đổi phạm vi thật của
TASK-204 chứ không phải một dòng cấu hình.

**Cần trước:** TASK-204 bắt đầu.

---

## Đã đóng

| # | Câu hỏi | Đóng bởi |
|---|---|---|
| C1 | Tín Phát có mặc định ADS không? | DEC-109, sửa đổi bởi DEC-119 |
| C2 | Vì sao sheet kênh chia đôi? | DEC-115 |
| C3 | Rule hoa hồng? | DEC-116 — công thức hóa ở TASK-403 |
| C4 | `Chiết khấu` trừ vào đâu? | DEC-114 |
| C4b | Chiết khấu trừ vào lợi nhuận? | **DEC-122 — có** |
| C5 | Dòng phụ tính vào đâu? | DEC-110 |
| C6 | Sửa được `Diễn giải` không? | DEC-111 |
| C7 | Đơn ADS lịch sử xử lý thế nào? | DEC-120 — không di trú |
| C8 | Số SP loại trừ dòng phụ? | DEC-113 |
| C9 | Tỉ lệ ADS cho Nội thành/Gia dụng? | **DEC-122 — không quan tâm, giữ 7,5%** |
| C10 | Chính sách 2027 khác gì 2026? | **DEC-122 — không đổi (tính đến 2026-08-23)** |
| **GATE-00** | Chủ dự án duyệt phân tích? | **DEC-122 — ĐÃ DUYỆT, 2026-08-23** |
