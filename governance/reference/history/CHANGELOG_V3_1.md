# CHANGELOG — V3.1

## Đã sửa (Fixed)
- Thêm các file thực tế cho `docs/tasks/` và `docs/sessions/` để các thư mục này được đưa vào ZIP.
- Chuyển các template tái sử dụng vào `/templates`.
- Giảm sự mơ hồ giữa runtime/template.
- Bỏ giả định trong governance rằng Fable vốn dĩ là một model chuyên biệt cho thiết kế.

## Đã thêm (Added)
- Project Profile: SOLO_LITE, PRODUCT, TEAM_PRODUCTION, AUDIT.
- Rule precedence (thứ tự ưu tiên quy tắc).
- Evidence Level E0/E1/E2.
- Yêu cầu evidence theo risk.
- Chế độ Micro Task.
- Chế độ Spike/Exploratory.
- Template Discovery Baseline.
- Template Audit Findings có severity.
- Lớp enforcement bằng máy tùy chọn (optional machine enforcement layer).
- File runtime `PROJECT_PROFILE.md`.
- Bảng kiểm chấp nhận (acceptance checklist) để rà soát framework.

## Đã thay đổi (Changed)
- S000 giờ đây chọn profile dự án trước khi hoàn thiện roadmap chi tiết.
- Completion Gate là sơ bộ trong giai đoạn lập kế hoạch ban đầu, được hoàn thiện/frozen (đóng băng) khi đạt READY.
- Độ sâu governance tương xứng với risk/quy mô dự án.
- Profile AUDIT mặc định là chỉ đọc (read-only).
