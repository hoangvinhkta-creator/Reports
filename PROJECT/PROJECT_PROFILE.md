# PROJECT PROFILE

Status:
INITIALIZED

Selected Profile:
NOT_A_REAL_PROFILE

Lịch Sử Profile:
- S001 (2026-08-22) — chọn AUDIT làm bootstrap S000. Xem DEC-001.
- S002 (2026-08-22) — chuyển AUDIT → PRODUCT theo chỉ đạo của chủ dự án. Xem DEC-005.

Cơ Sở Chuyển Đổi:
`governance/reference/START_HERE_USAGE_GUIDE_V3_2.md` PHẦN 7 — audit đã hoàn
tất, đã có finding kèm severity và evidence, và đã tạo remediation roadmap.
AUDIT mặc định là read-only và không thể thực thi remediation; PRODUCT thì có.

Team Size:
1 (chủ dự án kiêm vận hành)

Production Data:
KHÔNG CÓ — repo không chứa ứng dụng, không có database, không có runtime.

Personal/Customer Data:
KHÔNG CÓ — không lưu trữ hay xử lý dữ liệu cá nhân/khách hàng.

Authentication:
NOT_APPLICABLE — không có bề mặt authentication nào.

External Users:
KHÔNG CÓ — không có hệ thống deploy, không có người dùng bên ngoài.

CI/CD:
Hiện chưa có. Ở PRODUCT, `governance/product/14_CI_CD_RELEASE_RULES.md` không
bắt buộc, nhưng CI hiện được đánh giá là khả thi và được lên lịch làm REM-T07
trong PHASE-01 — đây là nguồn E2 evidence khả thi duy nhất của dự án (giải
quyết RSK-004). Xem DEC-007.

Staging:
KHÔNG CÓ. Không bắt buộc ở PRODUCT với một repo không có deployable artifact.

Backup:
Git remote `origin` → `https://github.com/hoangvinhkta-creator/Reports`.
Không có cơ chế backup nào khác. Ghi nhận là GAP-01 bên dưới.

Monitoring:
KHÔNG CÓ — không có gì đang chạy để monitor.

Uncertainty Level:
THẤP cho bề mặt hiện tại (tính toàn vẹn gói governance, layout deploy).
CAO cho phạm vi ứng dụng tương lai, vốn chưa tồn tại.

## Governance Bắt Buộc — PROFILE B (PRODUCT)

PRODUCT = SOLO_LITE + governance sản phẩm/kinh doanh/dữ liệu, theo
`governance/core/PROJECT_PROFILE_STANDARD.md`.

### CORE (kế thừa)
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

### SOLO_LITE (kế thừa)
- `governance/core/04_SECURITY_RULES.md`

### PRODUCT (thêm vào ở lần chuyển đổi này)
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

## Ma Trận Tuân Thủ Profile (Profile Compliance Matrix)

Lập theo `governance/reference/START_HERE_USAGE_GUIDE_V3_2.md` PHẦN 19.

"Bắt buộc theo profile" và "hiện có đối tượng để quản" là hai câu hỏi khác
nhau. Một domain chưa có bề mặt được ghi là DORMANT — bắt buộc, nhưng chưa có
gì để quản. DORMANT không phải là miễn trừ; phải kiểm tra lại khi có code ứng
dụng.

| Governance Domain | Yêu Cầu Profile | Áp Dụng Hiện Tại | Được Task Nào Cover | Trạng Thái | Gap |
|---|---|---|---|---|---|
| 00 Session Orchestration | BẮT BUỘC | Có | S001, S002 | ACTIVE | — |
| 01 Architecture | BẮT BUỘC | Có (layout repo) | REM-T02, ADR-001 | ACTIVE | — |
| 02 Routing | BẮT BUỘC | Không — chưa có routing ứng dụng | — | DORMANT | — |
| 03 Data Model | BẮT BUỘC | Không — chưa có data store | — | DORMANT | — |
| 04 Security | BẮT BUỘC | Một phần — không có secret, không có bề mặt auth | — | DORMANT | — |
| 05 Business Logic | BẮT BUỘC | Không — chưa có business logic | — | DORMANT | — |
| 06 Database / API | BẮT BUỘC | Không — chưa có database hay API | — | DORMANT | — |
| 07 Coding Rules | BẮT BUỘC | Có — validator scripts | REM-T03 | ACTIVE | — |
| 08 Change Management | BẮT BUỘC | Có | Tất cả REM-T* | ACTIVE | — |
| 09 Testing | BẮT BUỘC | Có — fixture kiểm thử regression của validator | REM-T03 | ACTIVE | — |
| 10 AI Agent Execution | BẮT BUỘC | Có | Tất cả session | ACTIVE | — |
| 11 Forbidden Actions | BẮT BUỘC | Có | Tất cả session | ACTIVE | — |
| 12 Product Requirements | BẮT BUỘC | Không — chưa có bề mặt sản phẩm | — | DORMANT | — |
| 13 Environment Config | BẮT BUỘC | Không — chưa có environment | — | DORMANT | — |
| 15 Logging / Observability | BẮT BUỘC | Không — chưa có gì đang chạy | — | DORMANT | — |
| 16 Backup / DR | BẮT BUỘC | Có — git remote là bản sao duy nhất | — | **GAP** | GAP-01 |
| 17 Data Governance / Privacy | BẮT BUỘC | Không — chưa có dữ liệu cá nhân | — | DORMANT | — |
| Phase / Release Gate | BẮT BUỘC | Có | Phase Gate 01–03 | ACTIVE | — |
| Evidence Standard | BẮT BUỘC | Có | Tất cả gate | ACTIVE | Thiếu nguồn E2 cho tới khi REM-T07 xong |
| 14 CI/CD | KHÔNG bắt buộc ở PRODUCT | Có — được đánh giá khả thi | REM-T07 | SCHEDULED | — |

### GAP-01 — Backup / Disaster Recovery

Yêu Cầu:
`governance/product/16_BACKUP_DISASTER_RECOVERY.md` bắt buộc ở PRODUCT.

Trạng Thái Hiện Tại:
Git remote trên GitHub là bản sao duy nhất của repo này. Không có backup thứ
hai và không có quy trình khôi phục được tài liệu hóa.

Đánh Giá:
Tác động bị giới hạn — nội dung là văn bản có version, không có production
data, và mỗi bản clone của contributor là một bản sao đầy đủ. Dù vậy đây vẫn
là một gap thật sự với một domain bắt buộc, và được ghi nhận thay vì bỏ qua.

Quyết Định:
Chưa lên lịch vào PHASE-01. Đánh giá lại ở Phase Gate 03. Không đóng gap này
bằng cách xóa dòng.

## Governance Có Điều Kiện
- `governance/product/14_CI_CD_RELEASE_RULES.md` — không bắt buộc ở PRODUCT,
  nhưng được chủ động áp dụng qua REM-T07 vì CI là con đường E2 của dự án.
  Đọc file này khi triển khai REM-T07.
- `governance/product/23_DOCUMENTATION_STANDARDS.md` — chỉ bắt buộc ở
  TEAM_PRODUCTION. Áp dụng mang tính khuyến nghị, vì sản phẩm của repo này
  *chính là* tài liệu. Liên quan tới REM-T05 và REM-T06.

## Không Áp Dụng
- `governance/product/18_INCIDENT_RESPONSE.md` — không có production service
  để mà xảy ra incident.
- `governance/product/19_DEPENDENCY_MANAGEMENT.md` — không có dependency bên
  thứ ba nào; 5 validator chỉ dùng Python standard library.
- `governance/product/20_API_VERSIONING_COMPATIBILITY.md` — không có API.
- `governance/product/21_ACCESSIBILITY_UI_RULES.md` — không có UI.
- `governance/product/22_CODE_OWNERSHIP_REVIEW.md` — chỉ một chủ sở hữu,
  không có review rota để định nghĩa.

Mỗi mục NOT_APPLICABLE được ghi kèm lý do, theo yêu cầu của
`governance/core/PROJECT_PROFILE_STANDARD.md`. Đánh giá lại toàn bộ các mục
này — và mọi dòng DORMANT ở trên — khi có code ứng dụng đầu tiên.

## Agent Capability Tiers

Ánh xạ theo `governance/core/AGENT_CAPABILITY_MATRIX.md`. Xem DEC-006.

- **Tier A — Lightweight**: sửa tài liệu, sửa đường dẫn phạm vi hẹp. → REM-T04, REM-T06
- **Tier B — Implementation**: validator script, CI workflow, refactor phạm vi hẹp. → REM-T03, REM-T05, REM-T07
- **Tier C — Advanced Reasoning**: di chuyển toàn repo, thiết kế gate, phân tích root-cause. → REM-T02
- **Tier D — Design / Creative**: NOT_APPLICABLE. Dự án này không có UI, thiết
  kế thị giác, hay công việc trình bày nội dung. Định nghĩa lại nếu có ứng
  dụng với giao diện người dùng được thêm vào.

## Lý Do Lựa Chọn (Justification)

PRODUCT được chọn theo chỉ đạo của chủ dự án sau khi S001 hoàn tất audit.

Nó chỉ phù hợp lỏng lẻo với mô tả use-case chuẩn của tiêu chuẩn ("ứng dụng
nhiều module nội bộ", "công cụ kinh doanh") vì hiện chưa có ứng dụng nào. Các
yếu tố quyết định mang tính thủ tục hơn là hình dạng sản phẩm:

1. AUDIT mặc định read-only và không thể thực thi remediation roadmap. Ở lại
   AUDIT sẽ chặn cả bảy task REM-T* vô thời hạn.
2. SOLO_LITE là lựa chọn nhẹ hơn, nhưng bỏ đi `PHASE_RELEASE_GATE_STANDARD`
   và nhóm luật data/architecture. Tập remediation bao gồm một thao tác di
   chuyển toàn repo với Blast Radius 5/5 (REM-T02) cần được verify ở mức
   phase, nên profile nặng hơn là lựa chọn an toàn hơn.
3. TEAM_PRODUCTION sẽ thêm nghi thức CODEOWNERS, incident response và API
   versioning mà một repo tài liệu một chủ sở hữu không thể thực sự đáp ứng.

Ghi nhận trung thực: một số domain PRODUCT đang DORMANT vì repo chưa có bề mặt
ứng dụng. Đây là hệ quả đã biết và được ghi lại của lựa chọn này, không phải
một sai sót bị bỏ sót.

## Quy Tắc Release

Áp dụng `governance/core/PHASE_RELEASE_GATE_STANDARD.md`.
Task DONE ≠ Phase DONE. Phase DONE ≠ Release Ready.

Giờ đã cho phép thay đổi production code — hạn chế read-only của AUDIT đã
được gỡ bỏ. Scope Lock vẫn áp dụng cho từng task.
