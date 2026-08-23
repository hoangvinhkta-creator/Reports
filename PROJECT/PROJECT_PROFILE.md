# HỒ SƠ DỰ ÁN

Status:
INITIALIZED — S000 hoàn tất 2026-08-22

Selected Profile:
PRODUCT

Dự án:
Tín Phát — Công cụ tự động tạo Báo cáo Kinh doanh

## Các yếu tố đầu vào của Profile

Team Size:
1 lập trình viên (có AI hỗ trợ) + 1 chủ dự án đóng vai trò người duyệt.
Người dùng báo cáo: toàn bộ đội bán hàng (~6–10 người) cùng ban quản lý.

Production Data:
CÓ. Công cụ nạp sổ bán hàng thật từ kế toán/ERP và tạo ra những con số quyết
định KPI, hoa hồng và lương của nhân viên. Kết quả sai có hậu quả tài chính
trực tiếp cho người thật.

Personal/Customer Data:
CÓ. Sổ bán hàng thô mang họ tên, số điện thoại di động và địa chỉ giao hàng
của khách trên mọi dòng (11.765 dòng trong mẫu hiện tại), cộng thêm IMEI/số
serial thiết bị. Tên nhân viên và số liệu liên quan lương cũng có mặt.
Vì vậy `governance/product/17_DATA_GOVERNANCE_PRIVACY.md` áp dụng và là bắt
buộc, không phải tuỳ chọn.

Authentication:
BẮT BUỘC. Công cụ nhiều người dùng, mọi lần ghi đè phải lưu `ChangedBy` cho
audit trail theo yêu cầu mục 19 đặc tả. Vai trò: viewer / editor / admin.

External Users:
KHÔNG. Chỉ dùng nội bộ công ty. Không có bề mặt hướng ra khách hàng.

CI/CD:
CHƯA CÓ. Chưa tồn tại pipeline nào. Có điều kiện — sẽ đưa vào khi công cụ
được triển khai lên server dùng chung.

Staging:
CHƯA CÓ. Chỉ có môi trường phát triển local ở giai đoạn MVP.

Backup:
BẮT BUỘC khi database tồn tại (Phase 2). Database trở thành hệ thống lưu trữ
chính cho các override tay không tồn tại ở đâu khác — file xuất ERP thô tải
lại được, nhưng một tháng điều chỉnh KPI thủ công thì không thể dựng lại.

Monitoring:
CƠ BẢN. Log ứng dụng có cấu trúc cộng với audit log ở tầng nghiệp vụ. Công cụ
observability đầy đủ nằm ngoài phạm vi MVP.

Uncertainty Level:
TRUNG BÌNH.
- Business rule đã có bằng chứng rõ ràng từ hai workbook mẫu (độ bất định THẤP).
- Rule phân loại ADS **không có dữ liệu hỗ trợ nào** trong các file hiện tại —
  từ khóa "ADS" xuất hiện 0 lần trong cả hai workbook — và phụ thuộc vào một
  thay đổi trong tương lai ở cách nhập liệu (độ bất định CAO).
- Giá nhập vắng mặt trong file thô và phụ thuộc vào một công cụ bảng giá bên
  ngoài chưa tồn tại (độ bất định TRUNG BÌNH).

## Độ sâu Governance

Mandatory Governance:
- CLAUDE.md
- governance/core/00_SESSION_ORCHESTRATION.md
- governance/core/01_PROJECT_ARCHITECTURE_RULES.md
- governance/core/02_ROUTING_RULES.md
- governance/core/03_DATA_MODEL_RULES.md
- governance/core/04_SECURITY_RULES.md
- governance/core/05_BUSINESS_LOGIC_RULES.md
- governance/core/06_DATABASE_API_RULES.md
- governance/core/07_CODING_RULES.md
- governance/core/08_CHANGE_MANAGEMENT_RULES.md
- governance/core/09_TESTING_RULES.md
- governance/core/10_AI_AGENT_EXECUTION_PROTOCOL.md
- governance/core/11_FORBIDDEN_ACTIONS.md
- governance/core/RULE_PRECEDENCE.md
- governance/core/EVIDENCE_STANDARD.md
- governance/core/TASK_MODE_STANDARD.md
- governance/core/TASK_READY_GATE_STANDARD.md
- governance/core/TASK_COMPLETION_GATE_STANDARD.md
- governance/core/PHASE_RELEASE_GATE_STANDARD.md
- governance/product/12_PRODUCT_REQUIREMENTS_RULES.md
- governance/product/13_ENVIRONMENT_CONFIGURATION.md
- governance/product/15_LOGGING_AUDIT_OBSERVABILITY.md
- governance/product/16_BACKUP_DISASTER_RECOVERY.md
- governance/product/17_DATA_GOVERNANCE_PRIVACY.md

Conditional Governance:
- governance/product/14_CI_CD_RELEASE_RULES.md — áp dụng kể từ lần triển khai
  dùng chung đầu tiên; NOT_APPLICABLE khi còn đang phát triển local-only.
- governance/product/19_DEPENDENCY_MANAGEMENT.md — áp dụng từ Phase 2, khi bề
  mặt dependency vượt ra ngoài bộ công cụ phân tích.
- governance/product/20_API_VERSIONING_COMPATIBILITY.md — áp dụng từ Phase 2,
  khi HTTP API tồn tại.
- governance/product/21_ACCESSIBILITY_UI_RULES.md — áp dụng từ Phase 3.
- governance/product/23_DOCUMENTATION_STANDARDS.md — áp dụng từ Phase 1.

Not Applicable:
- governance/product/18_INCIDENT_RESPONSE.md — chưa triển khai production,
  chưa có người dùng bên ngoài. Đánh giá lại ở Phase 3 release gate.
- governance/product/22_CODE_OWNERSHIP_REVIEW.md — dự án một lập trình viên;
  CODEOWNERS vô nghĩa với một người đóng góp duy nhất. Đánh giá lại nếu đội
  ngũ lớn thêm.

## Lý do lựa chọn

SOLO_LITE bị loại. Đây không phải một tiện ích một-file rủi ro thấp: nó giữ
dữ liệu cá nhân khách hàng, tính ra những con số quyết định lương nhân viên,
cần lưu trữ nhiều người dùng có audit trail, và thay thế một file Excel doanh
nghiệp đang phụ thuộc vào.

TEAM_PRODUCTION bị loại vì còn quá sớm. Chưa có đội nhóm, chưa có CI, chưa có
staging, chưa có người dùng bên ngoài. Áp CODEOWNERS, incident response và kỹ
thuật release ngay lúc này sẽ chỉ là hình thức không tương xứng với rủi ro
thật.

PRODUCT là lựa chọn đúng thực chất: đầy đủ governance sản phẩm/nghiệp
vụ/dữ liệu, với tầng vận hành-triển khai được nâng từ Conditional lên
Mandatory tại release gate của Phase 3, thay vì giả vờ như nó đã tồn tại từ
Phase 0.

## Quy tắc mức bằng chứng cho dự án này

Theo `governance/core/EVIDENCE_STANDARD.md` với Risk 4 trên engine tính toán:
E1 bắt buộc cho mọi REQUIRED check có thể thực thi, và các check kiểm tra độ
đúng số liệu ở Phase 1 NÊN đạt E2. Không có CI và không có người review độc
lập thứ hai, nên E2 được tạo ra qua Solo Independent Review Procedure và lưu
lại dưới `docs/reviews/`.
