# 22 — Quy Tắc Ownership & Review Code

## Mục Tiêu
Làm rõ trách nhiệm giải trình đối với các khu vực rủi ro cao và ngăn chặn các thay đổi không được review.

## Ownership
Các dự án nên xác định owner cho các domain quan trọng khi quy mô đội ngũ cho phép.

Ví dụ:
- authentication/security,
- data model/migrations,
- pricing,
- infrastructure,
- integrations.

## Các Mức Review

### Standard Review
Các thay đổi bình thường, có phạm vi giới hạn.

### Elevated Review
Được khuyến nghị cho:
- authentication,
- authorization,
- xuất dữ liệu khách hàng,
- logic pricing,
- thao tác phá hủy (destructive operations),
- migrations,
- hạ tầng production,
- secrets/configuration.

## Các Câu Hỏi Khi Review
Reviewer cần xác nhận:
- yêu cầu (requirement) là đúng,
- phạm vi (scope) được giới hạn,
- kiến trúc được tuân thủ,
- data migration an toàn,
- quyền hạn (permissions) được thực thi đầy đủ,
- tests đầy đủ,
- có thể rollback được.

## Code Do AI Tạo Ra
Các thay đổi do AI tạo ra không được miễn trừ khỏi việc review.

Đối với code rủi ro cao, hãy review kết quả implementation thực tế thay vì tin tưởng vào giải thích do AI đưa ra.

## CODEOWNERS
Ở những nơi được hỗ trợ, sử dụng quy tắc ownership của repository cho các đường dẫn quan trọng.

Ví dụ ownership mang tính khái niệm:
- `/security/**`
- `/migrations/**`
- `/infra/**`
- `/modules/pricing/**`

## Phân Tách Trách Nhiệm (Separation of Duties)
Đối với các thao tác nhạy cảm cao, hãy cân nhắc yêu cầu một phê duyệt (approval) thứ hai từ con người thay vì để một người/công cụ vừa tạo ra vừa tự phê duyệt thay đổi.
