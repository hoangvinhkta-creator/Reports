# 21 — Quy Tắc Accessibility & Chất Lượng UI

## Mục Tiêu
Đảm bảo giao diện luôn dễ sử dụng, dễ hiểu, nhất quán và có khả năng tiếp cận (accessible).

## Quy Tắc

### 1. UI ngữ nghĩa (Semantic)
Sử dụng các element và control ngữ nghĩa phù hợp.

### 2. Khả năng thao tác bằng bàn phím
Các luồng công việc cốt lõi không nên yêu cầu chuột ở nơi tương tác bàn phím tiêu chuẩn được kỳ vọng.

### 3. Nhãn (Labels)
Input và control cần có nhãn dễ hiểu.

### 4. Focus
Dialog, menu, và thay đổi route nên duy trì hành vi focus hợp lý.

### 5. Truyền đạt lỗi
Không chỉ dựa vào màu sắc để truyền đạt lỗi hoặc trạng thái.

### 6. Trạng Thái Loading / Empty / Error
Các view dữ liệu chính cần định nghĩa:
- loading,
- empty,
- error,
- success.

### 7. Hành động phá hủy (Destructive actions)
Phân biệt rõ ràng các thao tác mang tính phá hủy.
Sử dụng xác nhận (confirmation) khi tác động là đáng kể.

### 8. Tính nhất quán
Tái sử dụng design system/component thay vì tạo ra các control có hình thức khác nhau cho cùng một chức năng.

### 9. Hành vi responsive
Các luồng công việc cốt lõi cần duy trì khả năng sử dụng ở các kích thước viewport được hỗ trợ.

### 10. Thoái hóa accessibility (Regression)
Việc refactor UI không được làm mất đi các yếu tố hiện có sau:
- nhãn,
- hỗ trợ bàn phím,
- chỉ báo focus,
- vai trò ngữ nghĩa (semantic roles).

## Quy Tắc Cho AI Agent
Không tối ưu hình thức hiển thị bằng cách loại bỏ các nhãn, trạng thái, cảnh báo, hoặc hành vi accessibility cần thiết.
