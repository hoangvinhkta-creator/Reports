# 10 — Câu hỏi nghiệp vụ còn mở

Câu hỏi nghiệp vụ mà chủ dự án cần trả lời, không phải câu hỏi kỹ thuật.
C1–C11 liên quan tới phân loại nguồn đơn và quy đổi doanh thu (PHASE-01);
C12–C14 liên quan tới phân quyền truy cập (PHASE-02, thêm 2026-08-23 khi làm
`ADR-105`).

Tính đến **2026-08-23**, sau khi GATE-00 đã được chủ dự án duyệt (DEC-122).

**Trạng thái:** C4b, C9, C10, C12, C13, C14 đã đóng bằng xác nhận trực tiếp
của chủ dự án. **Còn mở: C11** (không chặn gì — mặc định Review Queue đã an
toàn) và **C15** (**chặn TASK-108B**, thêm 2026-08-23 khi review TASK-108A).
Nội dung đầy đủ giữ nguyên bên dưới để giữ mạch lý do; xem DEC-122 cho nhóm
đầu, DEC-124 cho C12/C13/C14, DEC-126 và DEC-127 cho C15.

| # | Câu hỏi | Trạng thái | Quyết định |
|---|---|---|---|
| C4b | `Chiết khấu` có trừ vào lợi nhuận cùng số đó không? | **ĐÃ ĐÓNG** (2026-08-23) | Có — DEC-122 |
| C9 | Đơn của Nội thành / Gia dụng có chữ "ADS" thì quy đổi ở tỉ lệ nào? | **ĐÃ ĐÓNG** (2026-08-23) | Không quan tâm, giữ 7,5 % mặc định — DEC-122 |
| C10 | Chính sách từ 01/01/2027 khác 2026 ở điểm nào? | **ĐÃ ĐÓNG cho hiện tại** (2026-08-23) | Không đổi — DEC-122, mở lại nếu có tin mới trước 01/12/2026 |
| **C11** | **Nhân viên chưa map (107 dòng / 5 người) xử lý thế nào khi lên production?** | **CÒN MỞ** — chủ dự án chưa rõ | Vào Review Queue loại `Missing`, không tính vào KPI |
| C15 | `EligibleCosts` trong công thức `EligibleKpiProfit` là gì, lấy từ đâu? | **ĐÃ ĐÓNG** (2026-08-27) | `EligibleCosts = {}` — closed empty set, **không** phải fallback `= 0`; `DeliveryCost = NOT ELIGIBLE FOR NOW` — DEC-143 / `OD-108B-01` |
| C12 | Nhân viên có được xem số của nhân viên khác không? | **ĐÃ ĐÓNG** (2026-08-23) | Câu hỏi hết ý nghĩa — chỉ `ADMIN` dùng hệ thống, không có "nhân viên khác" để so — DEC-124 |
| C13 | Ai được xem giá nhập và biên lợi nhuận? | **ĐÃ ĐÓNG** (2026-08-23) | Chỉ `ADMIN` — DEC-124 |
| C14 | Ai được chốt (commit) một lần nạp dữ liệu? | **ĐÃ ĐÓNG** (2026-08-23) | Chỉ `ADMIN` — DEC-124 |

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

**Trạng thái: ĐÃ ĐÓNG (DEC-124, 2026-08-23).** Chủ dự án xác nhận: đây là
công cụ quản trị nội bộ, chỉ `ADMIN` được dùng. Câu hỏi tự hết ý nghĩa —
không có "nhân viên" nào đăng nhập vào hệ thống để so sánh số với nhau; nhân
viên vẫn nhận báo cáo của mình qua kênh khác (ví dụ export do `ADMIN` gửi),
không tự truy cập công cụ.

Phát sinh khi soạn `ADR-105` (2026-08-23), không phải từ đợt rà soát GATE-00.
Ba hướng A/B/C từng đề xuất (giữ nguyên toàn xem, chỉ xem của mình, xem tổng
đội) đều không còn áp dụng vì tiền đề "nhiều nhân viên cùng đăng nhập" không
còn đúng.

**Nếu sau này công ty muốn nhân viên tự đăng nhập xem báo cáo của mình:** đó
là một tính năng mới, cần mở lại câu hỏi này thật sự — không phải bật một cờ
có sẵn, vì hạ tầng `employee_scope` chưa được xây theo đúng chỉ thị của chủ
dự án (xem ADR-105 §5).

---

## C13 — Ai được xem giá nhập và biên lợi nhuận?

**Trạng thái: ĐÃ ĐÓNG (DEC-124, 2026-08-23).** Chỉ `ADMIN` — hệ quả trực tiếp
của việc chỉ có một vai trò trong hệ thống. Không cần phân biệt
`kpi_purchase_price` với `accounting_purchase_price` theo vai trò nữa; cả hai
đều chỉ `ADMIN` xem được, đúng như mọi trường khác trong hệ thống.

`governance/core/04_SECURITY_RULES.md` §6 (giá vốn, biên lợi nhuận là dữ liệu
nhạy cảm) vẫn áp dụng — chỉ đơn giản hơn: bảo vệ khỏi *bất kỳ ai không phải
ADMIN*, không cần phân theo cấp độ.

---

## C14 — Ai được chốt một lần nạp dữ liệu?

**Trạng thái: ĐÃ ĐÓNG (DEC-124, 2026-08-23).** Chỉ `ADMIN` — và vì hệ thống
chỉ có một vai trò, không phát sinh tình huống "người chốt số liệu không nên
có toàn quyền admin" mà bản phân tích gốc lo ngại. Ai được cấp tài khoản
`ADMIN` thì có toàn quyền, bao gồm cả chốt import.

**Ghi chú vận hành (không phải câu hỏi kỹ thuật):** vì `ADMIN` = toàn quyền,
số lượng tài khoản `ADMIN` nên giới hạn ở người thực sự cần — đây là quyết
định vận hành của chủ dự án khi cấp tài khoản, không phải thứ hệ thống ép
buộc được.

---

## C15 — `EligibleCosts` là gì và lấy từ đâu?

**Trạng thái: ĐÃ ĐÓNG (DEC-143 / `OD-108B-01`, 2026-08-27).**

> **CURRENT STATE POINTER.** Chủ dự án đã trả lời: `EligibleCosts` = **CLOSED
> EMPTY SET** (`{}`) — một tuyên bố nghiệp vụ có thẩm quyền rằng tập hiện tại
> là rỗng, **không phải** fallback kỹ thuật `EligibleCosts = 0` mà mục này cấm.
> `DeliveryCost` = **NOT ELIGIBLE FOR NOW** (cũng là quyết định, không phải suy
> đoán). `OtherKpiAdjustment` = **0 BY DEFINITION**. Công thức canonical:
> `EligibleKpiProfit = (SellPrice − KpiPurchasePrice) × Quantity − Discount`.
> Thêm bất kỳ cost nào sau này cần Owner Decision riêng + effective date +
> provenance. Bằng chứng và phân tích double-count đầy đủ:
> `docs/tasks/TASK-108B-eligible-costs-owner-definition.md`; quyết định:
> `PROJECT/PROJECT_DECISIONS.md` → `DEC-143`.
>
> `TASK-108B` **vẫn chưa implement được**, nhưng lý do đã đổi: không còn là
> ambiguity nghiệp vụ, mà là **dependency dữ liệu** (Price Master; confirmed
> `KpiPurchaseAdjustment` persistence).

Phần dưới đây giữ nguyên làm **bản ghi lịch sử** của câu hỏi lúc còn mở —
không xoá, không viết lại.

Công thức lợi nhuận KPI (`docs/analysis/03_RULE_CLASSIFICATION.md` §U):

```
EligibleKpiProfit = (SellPrice − KpiPurchasePrice) × Quantity
                    − Discount − EligibleCosts + OtherKpiAdjustment
```

`EligibleCosts` là một số hạng **trừ thẳng vào lợi nhuận KPI**, tức trừ thẳng
vào cơ sở tính thưởng của nhân viên. Nhưng rà soát toàn bộ `docs/analysis/`
cho thấy nó **chưa từng được định nghĩa ở bất kỳ đâu**:

- Không có trong bảng ánh xạ cột của `01_DATA_MAPPING.md`.
- Không có trong bảng "Field trong Working Data không có nguồn thô" — tức nó
  còn chưa được xếp vào loại "biết là thiếu".
- Không có dòng nào trong file thô 17 cột tương ứng.
- Chỉ xuất hiện bên trong chính công thức.

Đây **không phải** "chưa có dữ liệu" mà là **chưa có định nghĩa**.

**Cấm tuyệt đối** (chủ dự án chỉ đạo trực tiếp, 2026-08-23):
- **Cấm** giả định `EligibleCosts = 0` để hoàn thành Conversion Engine.
- **Cấm** suy ra `EligibleCosts` là chi phí giao hàng (cột `Chi phí giao` /
  `Lương chuyến`) — hai khái niệm chưa được chứng minh là một.

**Vì sao nghiêm ngặt tới vậy:** một giả định ở đây cho ra `EligibleKpiProfit`
trông hợp lý, chia cho tỉ lệ ra một doanh thu quy đổi trông hợp lý, rồi con
số đó đi thẳng vào bảng lương. Không ai phát hiện được bằng cách nhìn kết
quả. Cùng loại rủi ro mà DEC-103 và DEC-126 §6 tồn tại để chặn.

**Cần chủ dự án trả lời:** `EligibleCosts` gồm những khoản nào, ai nhập, nhập
ở đâu, và có phải khoản đã nằm trong `KpiAdjustment` (DEC-125) không — nếu có
thì công thức đang trừ hai lần.

**Chặn:** TASK-108B (Converted Revenue). Không chặn TASK-108A-1.
*(Lịch sử — đã gỡ bởi DEC-143. `TASK-108B` nay chặn bởi dependency dữ liệu,
không phải bởi C15.)*

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
| C12 | Nhân viên xem được số của nhau không? | **DEC-124 — chỉ ADMIN dùng hệ thống, câu hỏi hết ý nghĩa** |
| C13 | Ai xem giá nhập / biên lợi nhuận? | **DEC-124 — chỉ ADMIN** |
| C14 | Ai chốt một lần nạp dữ liệu? | **DEC-124 — chỉ ADMIN** |
| **C15** | `EligibleCosts` là gì và lấy từ đâu? | **DEC-143 / `OD-108B-01` — closed empty set; `DeliveryCost` NOT ELIGIBLE; `OtherKpiAdjustment` = 0** |
