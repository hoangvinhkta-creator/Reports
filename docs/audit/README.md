# Audit Artifacts

Đầu ra audit runtime được tạo ra dưới hồ sơ AUDIT.

Được thiết lập bởi DEC-003 trong `PROJECT/PROJECT_DECISIONS.md`, vì discovery
baseline và findings là một lớp artifact runtime chưa có nơi lưu trú riêng
trong bố cục `docs/` được cung cấp sẵn, và `docs/reviews/` đã được dành riêng
cho các artifact review độc lập E2 theo `governance/core/EVIDENCE_STANDARD.md`.

## Nội dung

- `S001_DISCOVERY_BASELINE.md` — baseline từ `governance/audit/DISCOVERY_BASELINE_TEMPLATE.md`
- `S001_AUDIT_FINDINGS.md` — findings từ `governance/audit/AUDIT_FINDINGS_TEMPLATE.md`
- `REMEDIATION_ROADMAP.md` — kế hoạch remediation chi tiết được suy ra từ các findings đó

## Quy ước đặt tên

`S<NNN>_DISCOVERY_BASELINE.md` và `S<NNN>_AUDIT_FINDINGS.md`, một cặp cho mỗi
phiên discovery.

## Quy tắc

Findings là một bản ghi bất biến. Không chỉnh sửa nội dung finding trong các
phiên sau. Theo dõi trạng thái thay đổi của một finding trong
`PROJECT/PROJECT_PROGRESS.md` (Findings Register) và trong bảng traceability
của roadmap.

`PROJECT/PROJECT_PROGRESS.md` là checklist sống chính thức (canonical). Nếu nó
và `docs/audit/REMEDIATION_ROADMAP.md` mâu thuẫn nhau, file progress thắng và
roadmap sẽ được sửa lại cho khớp.
