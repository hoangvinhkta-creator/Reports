# 01 — Quy tắc Kiến trúc Dự án

## Mục tiêu
Giữ hệ thống modular, dễ dự đoán, dễ kiểm thử, an toàn, và chống lại việc mã nguồn do AI sinh ra phình to mất kiểm soát.

## Phân lớp Bắt buộc
Ưu tiên một cấu trúc về mặt khái niệm tương tự như sau:

UI / Pages
↓
Use Cases / Application Services
↓
Domain / Business Logic
↓
Repository / API Client
↓
Database / External Services

Tên thư mục cụ thể có thể khác nhau, nhưng trách nhiệm (responsibility) phải được tách biệt.

## Quy tắc

### 1. Định nghĩa ranh giới module
Mỗi năng lực nghiệp vụ (business capability) chính nên nằm trong một module riêng biệt.

Ví dụ:
- customers
- quotes
- orders
- care
- pricing
- inventory
- reports
- settings

### 2. Tránh trộn lẫn feature
Một module không được trực tiếp thao tác trạng thái nội bộ hoặc phần triển khai database của một module khác.

Các thao tác liên module nên dùng service/interface công khai (public).

### 3. Tách biệt các mối quan tâm (separation of concerns)
Không được trộn lẫn:
- presentation (trình bày),
- routing,
- business rules (quy tắc nghiệp vụ),
- data access (truy cập dữ liệu),
- authorization (phân quyền),
- persistence (lưu trữ)

trong cùng một component hoặc file.

### 4. Không có dependency vòng (circular dependency)
Module A → Module B → Module A là bị cấm.

Nếu có hành vi dùng chung, hãy tách nó ra thành một lớp shared/domain ổn định.

### 5. Ưu tiên interface công khai ổn định
Cách triển khai nội bộ có thể thay đổi, nhưng các module khác nên phụ thuộc vào interface/service thay vì chi tiết triển khai.

### 6. Không tái thiết kế kiến trúc không liên quan
Một yêu cầu feature không phải là giấy phép để viết lại kiến trúc đang hoạt động tốt.

### 7. Thay đổi kiến trúc cần có lý do rõ ràng
Trước khi thay đổi ranh giới kiến trúc, phải ghi lại tài liệu:
- giới hạn hiện tại,
- thay đổi đề xuất,
- các module bị ảnh hưởng,
- chi phí migration,
- tác động đến khả năng tương thích (compatibility impact),
- chiến lược rollback.

### 8. Code dùng chung phải thực sự là dùng chung
Không đặt code vào `shared/` chỉ vì tiện.

Code dùng chung nên:
- không có giả định đặc thù cho một feature cụ thể,
- có thể tái sử dụng bởi ít nhất hai bên tiêu thụ (consumer) hợp lệ,
- có trách nhiệm ổn định.

## Cấu trúc Ví dụ Được khuyến nghị

src/
├── app/
│   ├── router/
│   ├── auth/
│   └── providers/
├── modules/
│   ├── customers/
│   ├── quotes/
│   ├── orders/
│   └── care/
├── shared/
│   ├── components/
│   ├── hooks/
│   ├── types/
│   └── utils/
├── services/
└── config/

Một module có thể chứa:

module/
├── pages/
├── components/
├── use-cases/
├── services/
├── repositories/
├── schemas/
├── types/
└── tests/

## Câu hỏi Rà soát Kiến trúc
Trước khi triển khai:
- Module nào sở hữu hành vi này?
- Logic này thuộc về UI, business, data, hay infrastructure?
- Đã có service hiện hữu nào sở hữu nó chưa?
- Việc này có tạo ra coupling (kết dính) không?
- Feature khác có cần biết chi tiết triển khai của nó không?
- Việc này có thể được kiểm thử độc lập không?
