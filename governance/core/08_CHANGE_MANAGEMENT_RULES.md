# 08 — Change Management Rules

## Objective
Giữ cho các thay đổi do AI tạo ra có giới hạn, có thể review, có thể hoàn tác (reversible), và dễ hiểu.

## Mandatory Impact Analysis
Trước khi thay đổi code, xác định:

- kết quả được yêu cầu,
- các file có khả năng bị ảnh hưởng,
- các module bị ảnh hưởng,
- các route bị ảnh hưởng,
- data/schema bị ảnh hưởng,
- API bị ảnh hưởng,
- permissions/security bị ảnh hưởng,
- yêu cầu migration,
- rủi ro regression,
- các test cần thiết.

## Scope Rule
Không thay đổi code không liên quan chỉ vì nó có thể được cải thiện.

Một yêu cầu thêm tính năng không phải là sự cho phép để dọn dẹp toàn bộ codebase.

## Separate Concerns Across Changes
Tránh gộp chung:
- architecture refactor,
- database migration,
- dọn dẹp không liên quan,
- tính năng mới,
- thiết kế lại UI

trong một thay đổi không được kiểm soát.

Ưu tiên các thay đổi theo giai đoạn (staged changes) khi rủi ro đáng kể.

## Example

Không tốt:

Add customer export
+ rewrite customer module
+ rename schema
+ replace router
+ install state library

Tốt:

1. Thêm export contract/service.
2. Thêm permission checks.
3. Thêm UI entry point.
4. Thêm tests.
5. Đề xuất riêng một refactor lớn hơn nếu cần.

## Migration Rule
Các thay đổi dữ liệu đã lưu (persisted data) yêu cầu:
- migration plan,
- compatibility plan,
- validation,
- cân nhắc rollback.

## Backward Compatibility
Cân nhắc các yếu tố hiện tại:
- URLs,
- data,
- APIs,
- users,
- saved bookmarks,
- integrations.

## Change Report
Khi hoàn thành, báo cáo:

Files changed:
...

Why:
...

Behavior changed:
...

Security impact:
...

Data impact:
...

Migration:
...

Tests:
...

Known risks / follow-up:
...

## Rollback Mindset
Ưu tiên các thay đổi có thể hoàn tác mà không gây hại cho các phần không liên quan khác của hệ thống.
