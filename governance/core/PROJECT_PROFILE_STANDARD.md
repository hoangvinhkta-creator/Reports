# Project Profile Standard

## Mục đích
Lựa chọn độ sâu governance tương xứng với quy mô project, rủi ro kinh doanh, quy mô team, mức độ phơi nhiễm production, và mức độ không chắc chắn.

Profile PHẢI được chọn trong S000 trước khi hoàn thiện roadmap chi tiết.

## Mô hình kế thừa (Inheritance Model)

### CORE
Governance cốt lõi:
- `CLAUDE.md`
- `governance/core/00_SESSION_ORCHESTRATION.md`
- `governance/core/07_CODING_RULES.md`
- `governance/core/08_CHANGE_MANAGEMENT_RULES.md`
- `governance/core/09_TESTING_RULES.md`
- `governance/core/10_AI_AGENT_EXECUTION_PROTOCOL.md`
- `governance/core/11_FORBIDDEN_ACTIONS.md`
- `governance/core/RULE_PRECEDENCE.md`
- `governance/core/EVIDENCE_STANDARD.md`
- `governance/core/TASK_MODE_STANDARD.md`
- `governance/core/TASK_READY_GATE_STANDARD.md`
- `governance/core/TASK_COMPLETION_GATE_STANDARD.md`

### PROFILE A — SOLO_LITE
SOLO_LITE = CORE + bảo mật thiết yếu.

Thêm:
- `governance/core/04_SECURITY_RULES.md`

Dùng cho:
- prototype,
- công cụ một file,
- tiện ích nội bộ nhỏ,
- tự động hóa rủi ro thấp,
- project không có dữ liệu production nhạy cảm.

Mức độ nghi thức (Ceremony):
- Cho phép dùng Micro Task.
- ADR không bắt buộc cho các quyết định nhỏ.
- CI/CD, CODEOWNERS, DR có thể là NOT_APPLICABLE khi profile ghi rõ lý do.

### PROFILE B — PRODUCT
PRODUCT = SOLO_LITE + governance về sản phẩm/kinh doanh/dữ liệu.

Thêm:
- `governance/core/01_PROJECT_ARCHITECTURE_RULES.md`
- `governance/core/02_ROUTING_RULES.md`
- `governance/core/03_DATA_MODEL_RULES.md`
- `governance/core/05_BUSINESS_LOGIC_RULES.md`
- `governance/core/06_DATABASE_API_RULES.md`
- `governance/product/12_PRODUCT_REQUIREMENTS_RULES.md`
- `governance/product/13_ENVIRONMENT_CONFIGURATION.md`
- `governance/product/15_LOGGING_AUDIT_OBSERVABILITY.md`
- `governance/product/16_BACKUP_DISASTER_RECOVERY.md`
- `governance/product/17_DATA_GOVERNANCE_PRIVACY.md`
- `governance/core/PHASE_RELEASE_GATE_STANDARD.md`

Dùng cho:
- CRM,
- công cụ kinh doanh,
- ứng dụng Firebase/Supabase,
- ứng dụng nội bộ nhiều module,
- hệ thống chứa dữ liệu khách hàng/kinh doanh thực.

### PROFILE C — TEAM_PRODUCTION
TEAM_PRODUCTION = PRODUCT + governance vận hành/triển khai chính thức.

Thêm:
- `governance/product/14_CI_CD_RELEASE_RULES.md`
- `governance/product/18_INCIDENT_RESPONSE.md`
- `governance/product/19_DEPENDENCY_MANAGEMENT.md`
- `governance/product/20_API_VERSIONING_COMPATIBILITY.md`
- `governance/product/21_ACCESSIBILITY_UI_RULES.md`
- `governance/product/22_CODE_OWNERSHIP_REVIEW.md`
- `governance/product/23_DOCUMENTATION_STANDARDS.md`
- `governance/reference/OPTIONAL_ENFORCEMENT_LAYER.md` cùng với tích hợp CI khi khả thi.

Dùng cho:
- SaaS hướng tới khách hàng,
- nhiều lập trình viên,
- quy trình release chính thức,
- môi trường production có giá trị cao/chịu quản lý (regulated).

### PROFILE D — AUDIT
AUDIT mặc định là READ-ONLY.

Các quy tắc audit bắt buộc:
- `governance/core/01_PROJECT_ARCHITECTURE_RULES.md`
- `governance/core/03_DATA_MODEL_RULES.md`
- `governance/core/04_SECURITY_RULES.md`
- `governance/core/06_DATABASE_API_RULES.md`
- `governance/core/11_FORBIDDEN_ACTIONS.md`
- `governance/product/17_DATA_GOVERNANCE_PRIVACY.md`
- `governance/core/RULE_PRECEDENCE.md`
- `governance/core/EVIDENCE_STANDARD.md`
- `governance/audit/DISCOVERY_BASELINE_TEMPLATE.md`
- `governance/audit/AUDIT_FINDINGS_TEMPLATE.md`

Output chính:
- Discovery Baseline
- Findings
- Severity
- Evidence
- Remediation Roadmap

Không thay đổi code production cho đến khi AUDIT được đóng lại một cách rõ ràng và việc khắc phục (remediation) bắt đầu dưới một profile khác, thường là PRODUCT.

## Các yếu tố đầu vào để chọn Profile

Đánh giá:
- Quy mô team
- Độ trưởng thành của project
- Dữ liệu production
- Dữ liệu cá nhân/khách hàng
- Authentication
- Mức độ nhạy cảm về tài chính/giá cả
- Người dùng bên ngoài
- Ràng buộc pháp lý/tuân thủ
- CI/CD
- Staging
- Backup
- Monitoring
- Mức độ không chắc chắn
- Vòng đời dự kiến

## Bản ghi Runtime

Ghi vào:

`PROJECT/PROJECT_PROFILE.md`

Ghi lại:
- profile đã chọn,
- các nhóm rule bắt buộc,
- các nhóm rule có điều kiện,
- các nhóm rule không áp dụng,
- lý do lựa chọn (justification).

Không được quyết định lại tính áp dụng từ đầu ở mỗi session.
