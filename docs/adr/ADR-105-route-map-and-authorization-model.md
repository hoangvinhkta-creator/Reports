# ADR-105 — Bản đồ route và mô hình phân quyền

## Status

**Proposed** — chưa Accepted.

Đây là thiết kế sơ bộ (PRELIMINARY), **không phải gate đã đóng băng**. Lý do
giữ ở Proposed thay vì Accepted: quyết định này chứa ba câu hỏi nghiệp vụ mà
chủ dự án chưa trả lời (C12, C13, C14 trong `docs/analysis/10_OPEN_QUESTIONS.md`).
Chuyển sang Accepted khi PHASE-02 mở và ba câu đó đã đóng.

`governance/core/00_SESSION_ORCHESTRATION.md` → "Hoàn thiện Roadmap" cấm đóng
băng chi tiết của task còn xa khi discovery chưa đủ. TASK-203/TASK-204 nằm ở
PHASE-02, còn cách hiện tại (TASK-101) hơn một phase và một gate. Tài liệu này
thực hiện bước 1–7 của quy trình đó và **cố ý dừng trước bước 8 (freeze)**.

## Date

2026-08-23

## Context

Chủ dự án đặt hai câu hỏi trực tiếp về roadmap:

1. Có phần nào bảo mật thông tin, lưu trữ qua backend thay vì để lộ toàn bộ ở
   frontend không?
2. Có kế hoạch phân chia router cho từng luồng thay vì xử lý trên một link duy
   nhất chưa?

Rà soát cho thấy **nguyên tắc đã có đủ, thiết kế cụ thể thì chưa**:

- `ADR-101` đã chốt phân lớp `UI → API routers → use cases → domain engines →
  repositories → DB`, và ghi rõ API router **không chứa business rule**.
- `governance/core/04_SECURITY_RULES.md` (Mandatory theo profile PRODUCT) nêu:
  client là untrusted; ẩn trên UI không phải authorization; không tin
  `role`/`userId`/`price` do client gửi lên; giá vốn, biên lợi nhuận và dữ
  liệu cá nhân khách hàng là dữ liệu nhạy cảm phải bảo vệ.
- `governance/core/02_ROUTING_RULES.md` (Mandatory) cấm thẳng: *"Không ẩn toàn
  bộ ứng dụng phía sau một route duy nhất."*
- `PROJECT/PROJECT_PROFILE.md` chốt Authentication = BẮT BUỘC, ba vai trò
  `viewer` / `editor` / `admin`.

Nhưng trong `PROJECT/PROJECT_PROGRESS.md`, `TASK-203 — HTTP API` và
`TASK-204 — authentication và phân quyền` mỗi cái chỉ là **một dòng một câu**,
trong khi các task PHASE-01 (TASK-101, TASK-104, TASK-108) đều đã có đặc tả
chi tiết. Ba vai trò được đặt tên nhưng chưa ai định nghĩa vai trò nào đọc
được gì. Không có danh sách route nào tồn tại ở bất kỳ đâu trong repo.

Khoảng trống đó là thật, và nó là loại khoảng trống dễ bị lấp bằng ứng biến
lúc code — đúng thứ mà `CLAUDE.md` → "Không code trước rồi tổ chức sau" cấm.

## Decision

### 1. Ranh giới bảo mật: backend là nơi quyết định, frontend chỉ hiển thị

Ba phát biểu ràng buộc, không có ngoại lệ:

- **Frontend không bao giờ nhận field mà vai trò đang đăng nhập không được
  phép đọc.** Lọc ở tầng repository/serializer, không phải bằng cách ẩn cột
  trên UI. Một `curl` với token của `viewer` phải không thấy field đó trong
  JSON.
- **Mọi phép tính quyết định tiền đều chạy ở backend.** Frontend không tính
  lại lợi nhuận, doanh thu quy đổi hay hoa hồng — kể cả để hiển thị tạm.
  Không có tỉ lệ quy đổi nào được gửi xuống client dưới dạng hằng số để client
  tự nhân.
- **Không có secret nào trong bundle frontend.** Chuỗi kết nối DB, khóa ký
  token, thông tin đăng nhập SMTP — tất cả chỉ tồn tại phía server, theo
  `governance/product/13_ENVIRONMENT_CONFIGURATION.md`.

### 2. Route backend — nhóm theo module của ADR-101

Tiền tố `/api/v1` theo `governance/product/20_API_VERSIONING_COMPATIBILITY.md`
(áp dụng từ PHASE-02).

| Method + Path | Module | Mục đích |
|---|---|---|
| `POST /api/v1/auth/login` | auth | Đăng nhập, phát token |
| `POST /api/v1/auth/logout` | auth | Thu hồi phiên |
| `GET /api/v1/auth/me` | auth | Danh tính + vai trò của phiên hiện tại |
| `POST /api/v1/imports` | importing | Nạp `.xlsx`, trả metadata xem trước — **chưa ghi vào WORKING** |
| `POST /api/v1/imports/{batchId}/commit` | importing | Chốt batch sau khi xem trước |
| `GET /api/v1/imports` | importing | Danh sách batch |
| `GET /api/v1/imports/{batchId}` | importing | Chi tiết batch |
| `GET /api/v1/orders` | orders | Lọc theo kỳ / nhân viên / nguồn đơn |
| `GET /api/v1/orders/{orderId}` | orders | Chi tiết đơn + các line |
| `POST /api/v1/orders/{orderId}/overrides` | orders | Ghi đè `lead_source` hoặc `conversion_scheme` — bắt buộc `reason` |
| `DELETE /api/v1/orders/{orderId}/overrides/{overrideId}` | orders | Reset về Auto — đặt `active = false`, **không xóa bản ghi** |
| `GET /api/v1/rows/{rowId}` | orders | Chi tiết một dòng WORKING |
| `POST /api/v1/rows/{rowId}/overrides` | pricing/profit | Ghi đè giá nhập, adjustment — bắt buộc `reason` |
| `GET /api/v1/summary` | reporting | Summary tháng, tham số `period`, `employee` |
| `GET /api/v1/dashboard` | reporting | Tổng hợp năm, tham số `year` |
| `GET /api/v1/review` | reporting | Hàng chờ kiểm tra tay (5 loại cảnh báo, TASK-110) |
| `POST /api/v1/review/{itemId}/resolve` | reporting | Đóng một mục review |
| `GET /api/v1/audit` | audit | Đọc audit log — **chỉ đọc, chỉ append ở tầng dưới** |
| `GET /api/v1/config/{section}` | config | `employees`, `conversion`, `adjustments`, `targets` |
| `PUT /api/v1/config/{section}` | config | Sửa cấu hình — sinh bản ghi audit |
| `POST /api/v1/exports` | reporting | Tạo file `.xlsx` |
| `GET /api/v1/exports/{exportId}` | reporting | Tải file đã tạo |
| `GET /api/v1/users` | auth | Quản trị người dùng |
| `PATCH /api/v1/users/{userId}` | auth | Đổi vai trò |

**Không tồn tại route ghi vào RAW.** `ADR-102` đã quy định `raw_rows` không có
UPDATE và không có DELETE; ở đây điều đó thành hệ quả cụ thể: **không viết
endpoint nào cả**. Đây không phải quy ước để tuân thủ — nó là code không được
phép tồn tại.

### 3. Route frontend — mỗi luồng một URL

| Path | Task | Màn hình |
|---|---|---|
| `/dashboard` | TASK-303 | Tổng quan năm |
| `/summary/{period}` | TASK-303 | Summary tháng, `period` dạng `YYYY-MM` |
| `/employees/{employeeId}/{period}` | TASK-302 | Lưới chi tiết nhân viên theo tháng, sửa inline |
| `/imports` | TASK-301 | Danh sách lần nạp |
| `/imports/new` | TASK-301 | Tải file + xem trước |
| `/imports/{batchId}` | TASK-301 | Chi tiết một lần nạp |
| `/review` | TASK-305 | Hàng chờ kiểm tra tay |
| `/audit` | TASK-305 | Nhật ký thay đổi |
| `/settings/employees` | TASK-304 | Cấu hình nhân viên |
| `/settings/conversion` | TASK-304 | Bảng tỉ lệ quy đổi |
| `/settings/adjustments` | TASK-304 | Quy tắc adjustment |
| `/settings/targets` | TASK-304 | Target và hoa hồng |
| `/settings/users` | TASK-204 | Người dùng và vai trò |
| `/exports` | TASK-306 | Xuất Excel |

Ràng buộc theo `governance/core/02_ROUTING_RULES.md`: mỗi route phải mở trực
tiếp được, refresh được, back/forward đúng. Tab chỉ dùng cho view phụ **bên
trong** một resource — ví dụ tab "Personal / ADS / Total" trong cùng một
`/summary/{period}` là hợp lệ; chuyển giữa Summary và Review Queue bằng tab
thì không.

### 4. Ma trận phân quyền

Ba vai trò theo `PROJECT/PROJECT_PROFILE.md`. Mặc định **default deny** theo
`governance/core/04_SECURITY_RULES.md` §4 — không có dòng nào trong bảng nghĩa là từ chối.

| Năng lực | viewer | editor | admin |
|---|---|---|---|
| Xem Summary / Dashboard | ✅ | ✅ | ✅ |
| Xem lưới chi tiết nhân viên | ✅ | ✅ | ✅ |
| Xem `accounting_purchase_price`, biên lợi nhuận | ❌ | ❌ | ✅ |
| Xem dữ liệu cá nhân khách hàng (tên, SĐT, địa chỉ) | ❌ | ✅ | ✅ |
| Tải file lên + xem trước | ❌ | ✅ | ✅ |
| Chốt (commit) một lần nạp | ❌ | ❌ | ✅ |
| Ghi đè `lead_source` / `conversion_scheme` | ❌ | ✅ | ✅ |
| Ghi đè giá nhập / adjustment | ❌ | ❌ | ✅ |
| Đóng mục trong Review Queue | ❌ | ✅ | ✅ |
| Đọc audit log | ❌ | ✅ | ✅ |
| Sửa cấu hình (`employees`, `conversion`, `targets`) | ❌ | ❌ | ✅ |
| Xuất Excel | ✅ | ✅ | ✅ |
| Quản trị người dùng và vai trò | ❌ | ❌ | ✅ |

**Bốn thao tác được xếp vào admin vì chúng đổi tiền của người khác một cách
khó truy vết**: chốt import (ghi đè cả một tháng), ghi đè giá nhập (đổi trực
tiếp lợi nhuận), sửa cấu hình (đổi tỉ lệ cho mọi người cùng lúc), và quản trị
vai trò. Đây là áp dụng `governance/core/04_SECURITY_RULES.md` §13.

### 5. Phạm vi dữ liệu theo người dùng — mặc định hạn chế

`editor` chỉ ghi đè được trên đơn thuộc nhân viên mà tài khoản của họ được gán
(`employee_scope`). `viewer` và `admin` xem được toàn bộ.

Đây là **mặc định an toàn đang áp dụng**, không phải câu trả lời từ chủ dự án
— xem C12. Thực tế hiện nay cả đội dùng chung một file Excel nên ai cũng thấy
số của tất cả; mặc định này chặt hơn hiện trạng và có thể phải nới ra. Nới ra
là một dòng cấu hình; siết lại sau khi đã nới thì khó hơn nhiều, nên chọn
chiều chặt trước.

## Alternatives Considered

1. **Không phân vai trò ở MVP — ai đăng nhập cũng làm được mọi thứ.** Nhanh
   hơn hẳn, và khớp với hiện trạng file Excel dùng chung.
2. **Một endpoint `POST /api/v1/query` nhận payload mô tả việc cần làm.**
   Ít route, dễ thêm tính năng.
3. **Phân quyền bằng row-level security của PostgreSQL** thay vì ở tầng
   application.
4. **Frontend một trang, chuyển màn hình bằng tab state.**

## Rationale

**Vì sao không bỏ phân vai trò ở MVP.** `PROJECT/PROJECT_PROFILE.md` đã ghi
Authentication là BẮT BUỘC vì mọi override phải có `ChangedBy` thật cho audit
trail (đặc tả mục 19). Một khi đã phải có danh tính, chi phí thêm ba vai trò
là nhỏ. Ngược lại, việc gắn phân quyền vào một hệ thống đã chạy — nơi mọi
người đã quen làm được mọi thứ — là thay đổi tốn kém và gây tranh cãi hơn
nhiều. Điểm quyết định: dữ liệu ở đây quyết định **lương của người thật**,
không phải một dashboard nội bộ đọc cho vui.

**Vì sao không gộp về một endpoint.** `governance/core/02_ROUTING_RULES.md` cấm gộp toàn bộ
ứng dụng sau một URL, và lý do kỹ thuật còn nặng hơn lý do hình thức: một
endpoint đa năng làm cho việc phân quyền trở thành đọc-hiểu-payload thay vì
kiểm tra tại điểm vào, và làm rate limit, log, cache, kiểm thử đều mất chỗ
bám. Nó cũng phá vỡ `governance/core/06_DATABASE_API_RULES.md` §5 — "API contract phải tường
minh".

**Vì sao phân quyền ở tầng application chứ không phải row-level security.**
Cả hai đều là ranh giới server hợp lệ. Chọn tầng application vì `ADR-101` đã
đặt SQLite cho dev/test và PostgreSQL cho dùng chung — RLS chỉ tồn tại ở
PostgreSQL, nên quy tắc phân quyền sẽ không kiểm thử được trên chính môi
trường mà test chạy. Một quy tắc bảo mật không chạy trong test là một quy tắc
sẽ hỏng mà không ai biết. RLS vẫn có thể thêm sau như một lớp phòng vệ thứ
hai; nó không mâu thuẫn với quyết định này.

**Vì sao mặc định hạn chế cho `employee_scope`.** Xem mục 5.

## Consequences

### Positive

- TASK-203 và TASK-204 có phạm vi cụ thể để ước lượng và để viết Completion
  Gate, thay vì một dòng một câu.
- Mỗi endpoint có sẵn chỗ để điền `API Contract Template` của
  `governance/core/06_DATABASE_API_RULES.md` khi implement.
- Ràng buộc "không có route ghi vào RAW" trở thành thứ kiểm chứng được bằng
  `grep`, giống cách tiêu chí 14 của mục 28 đặc tả được kiểm chứng.
- Frontend route có sẵn danh sách để gán cho TASK-301…306, nên PHASE-03 không
  phải tự nghĩ ra cấu trúc điều hướng giữa chừng.

### Negative / Tradeoffs

- Ba vai trò và một `employee_scope` là công việc thật ở TASK-204, task vốn đã
  mang Risk 5 / Blast Radius 5.
- Ma trận phân quyền cần test cho từng ô, không chỉ cho đường đi thuận lợi.
  Số lượng test tăng đáng kể.
- Mặc định hạn chế ở mục 5 nhiều khả năng sẽ phải nới sau khi C12 được trả
  lời — tức có thể mất công làm hai lần ở phần cấu hình scope.
- Route frontend nhiều hơn một trang duy nhất kéo theo router, guard, trạng
  thái not-found và loading cho từng nhánh.

## Migration / Implementation Notes

- **PHASE-01 không bị ảnh hưởng.** Không có dòng nào trong ADR này áp dụng cho
  TASK-101…112. `ADR-101` đã cấm PHASE-01 import `fastapi`/`sqlalchemy` trong
  `app/modules/`; quyết định này không đổi điều đó.
- Kiểm tra phân quyền phải nằm ở tầng use case hoặc dependency của router,
  **không nằm trong domain engine**. Engine vẫn phải thuần và không biết ai
  đang gọi nó, đúng `ADR-101`.
- Mỗi endpoint khi implement phải điền đủ `API Contract Template`
  (`governance/core/06_DATABASE_API_RULES.md`), trong đó Authorization là mục
  bắt buộc, không được để trống.
- Test bắt buộc cho TASK-204: với mỗi ô ❌ trong ma trận, một test gọi thẳng
  API bằng token của vai trò đó và khẳng định `403`, **không phải** khẳng định
  nút bị ẩn trên UI.
- Ba câu hỏi C12/C13/C14 phải đóng trước khi ADR này chuyển sang Accepted.
  Nếu PHASE-02 bắt đầu mà chúng vẫn mở, mặc định trong tài liệu này được áp
  dụng và phải ghi rõ là mặc định chưa xác nhận, không được ghi là yêu cầu của
  chủ dự án.

## Supersedes

None

## Superseded By

None
