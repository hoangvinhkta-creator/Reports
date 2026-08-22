# ADR-001 — Kiến trúc và công nghệ nền

## Status
Accepted

## Date
2026-08-22

## Context

Công cụ thay thế quy trình lập báo cáo kinh doanh đang làm hoàn toàn thủ công
trong Excel. Ràng buộc thực tế:

- **Nhiều người dùng hằng ngày.** Chủ dự án mô tả: *"sẽ dùng hàng ngày, nhiều
  người dùng và xem, vận hành như 1 google sheet"* (DEC-005). Không phải một
  script chạy một lần rồi thôi.
- **Sửa dữ liệu là chức năng chính, không phải phụ.** Mục 19 và 28 đặc tả yêu
  cầu override được mọi trường quan trọng, có audit trail với `ChangedBy`, và
  Summary phải cập nhật ngay sau khi sửa.
- **Business rule phải cấu hình được.** Tiêu chí nghiệm thu cuối của mục 28:
  không hard-code nhân viên, margin, target, adjustment. Tài liệu 04 liệt kê
  47 giá trị phải chuyển thành config.
- **Đầu vào và đầu ra đều là Excel.** Đọc `.xlsx` thô, xuất `.xlsx` báo cáo.
- **Dữ liệu cá nhân khách hàng** trên mọi dòng — profile PRODUCT, kéo theo
  `governance/product/17_DATA_GOVERNANCE_PRIVACY.md`.
- Đặc tả mục 25 đề xuất: React/Next.js hoặc Streamlit cho MVP, FastAPI, pandas
  + openpyxl, SQLite → PostgreSQL.

## Decision

**Backend**
- Python 3.11+, FastAPI, SQLAlchemy 2.x, Alembic.
- pandas cho biến đổi dữ liệu, openpyxl cho đọc/ghi Excel.
- PostgreSQL cho môi trường dùng chung; SQLite cho dev và test.

**Frontend**
- React + TypeScript + Vite.
- TanStack Table cho lưới sửa inline.
- Cập nhật cho nhiều người xem cùng lúc: polling có điều kiện (ETag) ở MVP,
  nâng lên SSE nếu độ trễ thành vấn đề thật.

**Phân lớp** — theo `governance/core/01_PROJECT_ARCHITECTURE_RULES.md`:

```
UI (React)
  ↓
API routers (FastAPI)          — không chứa business rule
  ↓
Use cases / application services
  ↓
Domain engines                 — thuần, không I/O, không biết DB
  ↓
Repositories
  ↓
PostgreSQL / SQLite / Excel
```

**Module** — mỗi engine trong đặc tả mục 24 là một module riêng:
`importing`, `mapping`, `orders`, `pricing`, `profit`, `conversion`,
`reporting`, `audit`, `config`.

**Thứ tự xây dựng: engine trước, API sau, UI sau cùng.** Toàn bộ Phase 1 là
thư viện Python thuần chạy được bằng CLI, không phụ thuộc DB hay web. Chỉ khi
các con số đã đúng và có bằng chứng đối chiếu mới bọc API và UI lên.

## Alternatives Considered

1. **Streamlit cho MVP** (đặc tả có nêu). Nhanh hơn đáng kể để ra bản chạy được.
2. **Chỉ CLI: Excel vào → Excel ra.** Đơn giản nhất, ít phụ thuộc nhất.
3. **Google Apps Script trên chính Google Sheets.** Bám sát nhất mô tả "vận
   hành như google sheet".
4. **Next.js full-stack (bỏ Python).**

## Rationale

**Vì sao không Streamlit.** Streamlit chạy lại toàn bộ script mỗi lần tương
tác và mỗi phiên là một trạng thái riêng. Với một người dùng thì ổn; với nhiều
người cùng sửa một tháng dữ liệu thì không có mô hình ghi đồng thời, không có
danh tính người dùng để ghi `ChangedBy`, và mỗi lần sửa một ô sẽ tính lại toàn
bộ. Yêu cầu "nhiều người dùng và xem" loại nó ở tầng kiến trúc chứ không phải
ở tầng giao diện.

**Vì sao không chỉ CLI.** Override và audit trail là yêu cầu trung tâm của đặc
tả (mục 19, 26, 28), không phải tính năng thêm. Đưa override vào một file config
để chạy lại sẽ tạo ra đúng vấn đề mà công cụ này sinh ra để giải quyết: một tệp
trạng thái sửa tay không ai kiểm soát được.

**Vì sao không Google Apps Script.** Đưa dữ liệu cá nhân của khách hàng lên
dịch vụ ngoài là một quyết định về quyền riêng tư, không phải về công nghệ, và
không nằm trong phạm vi được yêu cầu. Ngoài ra Apps Script không đủ cho phần
tính toán và kiểm thử.

**Vì sao Python thay vì Next.js full-stack.** Trọng tâm của công cụ là đọc
Excel nhiều biến thể layout và tính toán tài chính chính xác. openpyxl và
pandas là công cụ chín nhất cho việc đó. Đặc tả cũng đã đề xuất Python.

**Vì sao engine trước, UI sau.** Rủi ro lớn nhất của dự án này không phải giao
diện — mà là **ra sai số**. Một engine thuần, không I/O, kiểm thử được bằng
fixture là cách duy nhất chứng minh 254 đơn là 254 đơn trước khi có ai nhìn
thấy màn hình nào.

## Consequences

### Positive
- Engine kiểm thử được độc lập, không cần dựng DB hay trình duyệt.
- Business rule tập trung ở domain layer, UI không biết gì về tỉ lệ quy đổi.
- Đổi PostgreSQL ↔ SQLite không chạm vào engine.
- Có CLI ngay từ Phase 1 → dùng được sớm, trước khi UI xong.

### Negative / Tradeoffs
- Hai ngôn ngữ, hai tiến trình khi chạy — nặng hơn Streamlit đáng kể.
- Thời gian đến bản chạy được lâu hơn.
- Cần tự làm auth và phân quyền.
- Realtime bằng polling không mượt như một bảng tính thật. Chấp nhận ở MVP;
  nâng cấp nếu người dùng thấy vướng.

## Migration / Implementation Notes

- Phase 1 không được import `fastapi`, `sqlalchemy` hay bất kỳ thứ gì liên quan
  đến web trong `app/modules/`. Kiểm chứng bằng một test tĩnh.
- Engine nhận và trả về dataclass/dict thuần, không nhận ORM model.
- `config/` là YAML ở Phase 1; Phase 2 chuyển vào DB nhưng giữ nguyên interface
  đọc, để engine không biết config đến từ đâu.

## Supersedes
None

## Superseded By
None
