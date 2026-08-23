# ADR-105 — Bản đồ route và mô hình phân quyền

## Status

**Accepted** (mục Decision §4/§5) — 2026-08-23, sau quyết định trực tiếp của
chủ dự án đóng C12/C13/C14. Xem "Sửa đổi 2026-08-23" ngay dưới Context.

Mục §2 (route backend) và §3 (route frontend) không đổi, vẫn Accepted.

**Completion Gate của TASK-203/TASK-204 vẫn CHƯA freeze.** Chấp nhận ADR
(quyết định thiết kế) khác với freeze gate (cam kết tiêu chí nghiệm thu).
`governance/core/00_SESSION_ORCHESTRATION.md` → "Hoàn thiện Roadmap" cấm đóng
băng chi tiết của task còn xa khi discovery chưa đủ; TASK-203/204 vẫn cách
task hiện tại (TASK-101) một phase và một gate. Freeze đúng lúc khi PHASE-02
mở, qua một Roadmap Finalization đầy đủ — thiết kế giờ đã đơn giản hơn nhiều
nên bước đó sẽ nhanh.

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
- `PROJECT/PROJECT_PROFILE.md` chốt Authentication = BẮT BUỘC *(tại thời điểm
  này, PROFILE liệt kê ba vai trò `viewer`/`editor`/`admin` — đã được cập
  nhật lại thành chỉ `ADMIN` sau "Sửa đổi 2026-08-23" bên dưới, DEC-124)*.

Nhưng trong `PROJECT/PROJECT_PROGRESS.md`, `TASK-203 — HTTP API` và
`TASK-204 — authentication và phân quyền` mỗi cái chỉ là **một dòng một câu**,
trong khi các task PHASE-01 (TASK-101, TASK-104, TASK-108) đều đã có đặc tả
chi tiết. Ba vai trò được đặt tên nhưng chưa ai định nghĩa vai trò nào đọc
được gì. Không có danh sách route nào tồn tại ở bất kỳ đâu trong repo.

Khoảng trống đó là thật, và nó là loại khoảng trống dễ bị lấp bằng ứng biến
lúc code — đúng thứ mà `CLAUDE.md` → "Không code trước rồi tổ chức sau" cấm.

### Sửa đổi 2026-08-23 — chủ dự án quyết định trực tiếp, đóng C12/C13/C14

Bản gốc của ADR này (cùng ngày, trước sửa đổi) để ba câu hỏi nghiệp vụ mở và
đề xuất mặc định 3 vai trò `viewer`/`editor`/`admin` + `employee_scope`. Chủ
dự án trả lời trực tiếp, không theo hướng nào trong ba hướng đã liệt kê ở
C12/C13/C14 mà đơn giản hơn cả:

> *"Công cụ Báo cáo Kinh doanh là công cụ quản trị nội bộ. Chỉ người dùng có
> quyền `ADMIN` mới được phép truy cập. Không triển khai `viewer`, `editor`
> hoặc `employee_scope` trong MVP. [...] Authorization vẫn phải kiểm tra ở
> backend, không chỉ ẩn giao diện. Thiết kế database nên vẫn cho phép mở rộng
> thêm role trong tương lai, nhưng không xây trước khi có nhu cầu thực tế."*

Điều này đóng cả ba câu cùng lúc — không phải vì chọn một mặc định trong ba,
mà vì tiền đề của cả ba (có nhiều vai trò cùng dùng hệ thống) không còn đúng.
Xem DEC-124. Mục §4 và §5 dưới đây được viết lại theo quyết định này; §2
(route backend) và §3 (route frontend) không đổi.

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

### 4. Phân quyền — MVP chỉ có một vai trò: ADMIN

**Quyết định trực tiếp của chủ dự án (2026-08-23, DEC-124).** Đây là công cụ
quản trị nội bộ. Không triển khai `viewer`, `editor` hay `employee_scope`
trong MVP.

**Quy tắc:**

- **`ADMIN`** — toàn quyền trên mọi endpoint ở §2 và mọi route ở §3: báo cáo,
  import, override, config, audit, export.
- **Bất kỳ danh tính nào khác** (chưa đăng nhập, hoặc đã đăng nhập nhưng
  không phải `ADMIN`):
  - Mọi endpoint dưới `/api/v1/*` trả `403`, **trừ**
    `POST /api/v1/auth/login`, `POST /api/v1/auth/logout`,
    `GET /api/v1/auth/me`.
  - `GET /api/v1/auth/me` vẫn trả `200` cho người đã đăng nhập dù không phải
    `ADMIN` — response chỉ chứa danh tính + role, không chứa gì khác. Đây là
    endpoint duy nhất frontend cần để biết "chặn hay không chặn".
  - **Frontend không mở** — app shell gọi `/api/v1/auth/me` trước khi render
    bất kỳ route nghiệp vụ nào ở §3; nếu role khác `ADMIN`, hiển thị màn hình
    "không có quyền truy cập" thay vì route đó, kể cả khi người dùng gõ thẳng
    URL.

Đây vẫn là **default deny** đúng `governance/core/04_SECURITY_RULES.md` §4 —
chỉ đơn giản hóa: danh sách "được phép" chỉ còn một dòng thay vì một ma trận.

**Vì sao vẫn kiểm tra ở backend dù chỉ một vai trò.** `governance/core/04_SECURITY_RULES.md`
§2 — "Ẩn trên UI không phải là authorization" — không đổi chỉ vì bớt vai trò.
Một danh tính non-ADMIN gọi thẳng API bằng `curl`/Postman vẫn phải bị chặn ở
backend; việc frontend không render route không phải là ranh giới bảo mật, nó
chỉ là trải nghiệm người dùng đi kèm.

### 5. Mở rộng vai trò trong tương lai — thiết kế cho phép, không xây trước

Bảng `users` giữ cột `role` kiểu enum, hiện chỉ có giá trị `ADMIN`. Thêm vai
trò mới sau này (ví dụ nếu công ty muốn thêm `viewer` cho ban quản lý xem
không sửa) là một migration thêm giá trị enum cộng một số điểm kiểm tra quyền
mới — không phải thiết kế lại schema hay route.

**Không dựng sẵn** bảng permission/role-permission, cột `employee_scope`, hay
bất kỳ hạ tầng phân quyền nhiều-vai-trò nào cho một nhu cầu chưa tồn tại —
đúng theo yêu cầu tường minh của chủ dự án, và đúng tinh thần `CLAUDE.md` →
"Không code trước rồi tổ chức sau" áp theo chiều ngược: không tổ chức trước
cho một tính năng chưa ai cần.

## Alternatives Considered

1. **Ba vai trò `viewer`/`editor`/`admin` + `employee_scope`** (bản gốc của
   ADR này, 2026-08-23, trước sửa đổi). Bị thay thế trực tiếp bởi quyết định
   của chủ dự án — xem "Sửa đổi 2026-08-23".
2. **Không xác thực gì ở MVP — mở tự do.** Bị loại: mọi override vẫn cần
   `ChangedBy` thật cho audit trail (đặc tả mục 19); "chỉ ADMIN" vẫn cần đăng
   nhập, khác với "không cần đăng nhập".
3. **Một endpoint `POST /api/v1/query` nhận payload mô tả việc cần làm.**
   Ít route, dễ thêm tính năng.
4. **Phân quyền bằng row-level security của PostgreSQL** thay vì ở tầng
   application.
5. **Frontend một trang, chuyển màn hình bằng tab state.**

## Rationale

**Vì sao chỉ một vai trò ADMIN, không phải ba vai trò như bản gốc.** Quyết
định trực tiếp của chủ dự án: đây là công cụ quản trị nội bộ, không phải một
hệ thống nhiều cấp người dùng. Ba vai trò trong bản gốc là suy đoán hợp lý
dựa trên `PROJECT/PROJECT_PROFILE.md` ghi Authentication BẮT BUỘC — nhưng suy
đoán đó sai tiền đề: BẮT BUỘC có xác thực (để có `ChangedBy` thật) không kéo
theo BẮT BUỘC có nhiều vai trò. Một khi chủ dự án xác nhận chỉ một vai trò,
giữ nguyên ba vai trò sẽ là xây dư thừa cho một nhu cầu không tồn tại — đúng
thứ mục 28 đặc tả và `CLAUDE.md` đều cấm.

**Vì sao vẫn cần đăng nhập dù chỉ một vai trò.** Xem alternative 2 — audit
trail cần `ChangedBy` thật, và bản thân yêu cầu "không được mở frontend" nếu
không phải ADMIN đã ngụ ý phải có một khái niệm đăng nhập để phân biệt.

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

**Vì sao thiết kế cho mở rộng nhưng không xây trước.** Xem mục 5 — chỉ thị
tường minh của chủ dự án, và đúng nguyên tắc chung của dự án là không xây cho
một nhu cầu giả định.

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
- **So với bản gốc 3 vai trò:** TASK-204 nhẹ hơn đáng kể — không ma trận cần
  test từng ô, không `employee_scope` cần thiết kế và di trú sau này. Chỉ hai
  trạng thái cần kiểm: ADMIN (toàn quyền) và không-phải-ADMIN (403 mọi nơi
  trừ ba endpoint auth).

### Negative / Tradeoffs

- Route frontend nhiều hơn một trang duy nhất kéo theo router, guard, trạng
  thái not-found và loading cho từng nhánh — không đổi so với bản gốc, không
  liên quan tới số vai trò.
- Nếu sau này công ty thật sự cần nhiều vai trò (ví dụ ban quản lý chỉ xem),
  đó là công việc mới thật sự — không phải bật một cờ có sẵn. Chấp nhận được:
  chủ dự án đã cân nhắc và chọn không xây trước.
- Toàn bộ tài khoản đăng nhập được đều có toàn quyền như nhau — nếu một tài
  khoản ADMIN bị lộ, kẻ tấn công có toàn quyền hệ thống, không có lớp chặn
  trung gian nào. Đây là đánh đổi có chủ đích của mô hình một-vai-trò, không
  phải sơ suất; giảm thiểu bằng việc số tài khoản ADMIN nên ít.

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
- Test bắt buộc cho TASK-204: với danh tính không phải `ADMIN` (chưa đăng
  nhập, hoặc đăng nhập nhưng role khác), một test gọi thẳng từng endpoint ở
  §2 (trừ ba endpoint auth) và khẳng định `403` — **không phải** khẳng định
  nút bị ẩn trên UI. Với `ADMIN`, test khẳng định từng endpoint trả đúng dữ
  liệu, không bị chặn nhầm.
- Nếu tương lai có vai trò thứ hai (xem mục 5), việc đầu tiên trước khi code
  là một ADR mới hoặc một bản sửa đổi tường minh của ADR này — không âm thầm
  thêm `if role == "editor"` rải rác trong handler.

## Supersedes

None

## Superseded By

None
