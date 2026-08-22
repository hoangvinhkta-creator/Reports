# PROJECT PROGRESS

> File này là checklist sống chính thức (canonical) của dự án.
> Mọi session đọc file này đầu tiên. Không trả lời câu hỏi tiến độ dựa trên
> trí nhớ hội thoại (`CLAUDE.md` → "Câu Hỏi Về Tiến Độ").
> Kế hoạch remediation chi tiết: `docs/audit/REMEDIATION_ROADMAP.md`.

## Tóm Tắt Dự Án

Dự Án:
`hoangvinhkta-creator/Reports` — repo lưu trữ gói governance AI Engineering
Constitution Template V3.2 FINAL COMPACT.

Mục Tiêu:
Đưa repo về trạng thái mà chính khung governance của nó được deploy đúng,
nhất quán nội bộ, và có thể kiểm chứng bằng máy, để công việc ứng dụng sau
này có thể được quản trị bởi nó.

Project Type:
LEGACY

Profile:
PRODUCT

Lịch Sử Profile:
AUDIT (bootstrap S001) → PRODUCT (S002, DEC-005)

Cập Nhật Lần Cuối:
2026-08-22 — cuối S003

Overall Status:
IN_PROGRESS

Phase Hiện Tại:
PHASE-01 — Governance Foundation Repair

Task Hiện Tại:
REM-T07 — CI enforcement layer

Current Task Mode:
MAJOR

Task Đề Xuất Tiếp Theo:
REM-T07 — CI enforcement layer (READY, không còn bị chặn)
REM-T03 và REM-T04 cũng đã hết bị chặn và có thể chạy song song — cả hai chỉ
phụ thuộc REM-T02, mà REM-T02 đã DONE.

## Roadmap Tổng Thể

Chú thích: `[ ]` NOT_STARTED · `[~]` IN_PROGRESS · `[x]` DONE · `[!]` BLOCKED · `[-]` CANCELLED

- [x] PHASE-00 — Audit
  - [x] S000 — Project Open — thực hiện xuyên suốt bootstrap S001 + S002 (xem DEC-008)
  - [x] S001 — Discovery & Baseline — SPIKE — DONE
  - [x] S002 — Roadmap Finalization — MAJOR — DONE

- [~] PHASE-01 — Governance Foundation Repair  ·  gate đã FROZEN
  - [x] **REM-T02** — Dời gói governance lên repository root — MAJOR — Tier C — D2/R3/**B5** — **DONE** (S003) — đóng FIND-001
  - [ ] REM-T07 — CI enforcement layer — MAJOR — Tier B — D2/R2/B2 — **READY** — đóng FIND-008, giải quyết RSK-004
  - [ ] REM-T03 — Validator deployment-root + reference-integrity — MAJOR — Tier B — D3/R2/B2 — **READY** (dependency REM-T02 đã DONE) — đóng FIND-007
  - [ ] REM-T04 — Sửa các reference đường dẫn canonical bị gãy — MICRO — Tier A — D1/R2/B2 — **READY** (dependency REM-T02 đã DONE) — đóng FIND-003, FIND-004
  - [ ] Phase Gate 01
  - [-] ~~REM-T01 — Khởi tạo project state~~ — CANCELLED (absorbed, CH-01/DEC-008)

- [ ] PHASE-02 — Documentation & Evidence Truth-Up  ·  gate PRELIMINARY
  - [ ] REM-T05 — Sửa tài liệu và artifact kiểm chứng — MAJOR — Tier B — D2/R2/B3 — đóng FIND-005, FIND-006, FIND-011, FIND-012
  - [ ] Phase Gate 02

- [ ] PHASE-03 — Repository Hygiene  ·  gate PRELIMINARY
  - [ ] REM-T06 — Vệ sinh repository root — MICRO — Tier A — D1/R1/B1 — đóng FIND-009
  - [ ] Phase Gate 03

Thứ tự dependency — REM-T02 đã DONE, nên REM-T07, REM-T03 và REM-T04 giờ đều
chạy độc lập song song được:
~~REM-T07 → REM-T02~~ → (REM-T07 ∥ REM-T03 ∥ REM-T04) → REM-T05 → REM-T06.

Ghi chú: thứ tự gốc của PHASE-01 (CH-02) đặt REM-T07 trước REM-T02, để REM-T02
có nguồn E2 dựa trên CI. Chủ dự án đã đổi thứ tự ngay tại chỗ (DEC-009) để sửa
một lỗi usability đang hoạt động (link GitHub gãy do FIND-001) thay vì giữ
đúng trình tự ban đầu. E2 cho REM-T02 được lấy qua Solo Independent Review
Procedure thay thế.

## Snapshot Task Hiện Tại

Task:
REM-T07 — CI enforcement layer

Task Mode:
MAJOR

Status:
READY

Tiến Độ Gate Bắt Buộc:
0 / 6 PASS  (6 REQUIRED + 1 RECOMMENDED, tất cả NOT_TESTED)

Task File:
`docs/tasks/TASK-REM-T07-ci-enforcement.md`

Completion Gate:
FROZEN 2026-08-22 (S002)

Primary Agent Tier:
Tier B — Implementation

Escalation Tier:
Tier C — Advanced Reasoning

Scope Lock:
`.github/workflows/governance.yml` ở repository root. Không gì khác.

Ràng Buộc Quan Trọng:
Workflow phải tự phát hiện (discover) validator script lúc chạy, không được
hard-code đường dẫn (RSK-005) — giờ dễ thỏa mãn hơn, vì đường dẫn validator đã
ngắn hơn và ổn định sau REM-T02 (`governance/scripts/governance/*.py` từ repo
root).

Check Không Thể Thương Lượng:
CHECK-T07-03 — phải thực sự quan sát được workflow FAIL trên một breakage cố
ý. Một CI chưa từng thấy fail sẽ tạo ra bằng chứng E2 giả.

Cũng đang READY và không còn bị chặn (chạy song song an toàn với REM-T07 và
với nhau):
- REM-T03 — Validator deployment-root + reference-integrity
- REM-T04 — Sửa các reference đường dẫn canonical bị gãy (MICRO — xem MICRO-001)

## Trạng Thái Gate Freeze

| Task | Ready Gate | Completion Gate | Check REQUIRED |
|---|---|---|---|
| REM-T02 | VERIFIED | **FROZEN** | 5/5 PASS — **DONE** |
| REM-T07 | VERIFIED — READY | **FROZEN** | 6 |
| REM-T03 | VERIFIED — READY (dependency đã DONE) | **FROZEN** | 4 |
| REM-T04 | MICRO compact — READY (dependency đã DONE) | **FROZEN** | xem MICRO-001 |
| REM-T05 | chưa finalize | PRELIMINARY | 5 bản nháp |
| REM-T06 | chưa finalize | PRELIMINARY | 2 bản nháp |

Gate của PHASE-02 và PHASE-03 cố ý chưa freeze, theo
`governance/core/00_SESSION_ORCHESTRATION.md`: "Không freeze chi tiết task còn
xa khi discovery chưa đủ."

## Findings Register (S001)

Chi tiết đầy đủ: `docs/audit/S001_AUDIT_FINDINGS.md` (bản ghi bất biến — theo
dõi trạng thái ở đây, không phải ở đó).

| ID | Severity | Tóm Tắt | Task | Status |
|---|---|---|---|---|
| FIND-001 | HIGH | Gói bị lồng dưới repo root; `CLAUDE.md` không ở root | REM-T02 | **RESOLVED** (S003, E2) |
| FIND-002 | HIGH | S000 chưa từng chạy; project state là placeholder | — | **RESOLVED** (S002, E1) |
| FIND-003 | MEDIUM | Reference canonical gãy tới `OPTIONAL_ENFORCEMENT_LAYER.md` (×2) | REM-T04 | OPEN — READY |
| FIND-004 | MEDIUM | `CLAUDE.md:27` trỏ tới `templates/` không tồn tại | REM-T04 | OPEN — READY |
| FIND-005 | MEDIUM | Báo cáo validation đã ship khẳng định một PASS sai sự thật | REM-T05 | OPEN |
| FIND-006 | MEDIUM | START_HERE guide tự mâu thuẫn về layout | REM-T05 | OPEN |
| FIND-007 | MEDIUM | Validator không phát hiện được root bị deploy sai | REM-T03 | OPEN — READY |
| FIND-008 | LOW | Chưa có CI wiring cho enforcement layer | REM-T07 | OPEN — READY |
| FIND-009 | LOW | Chưa có root README / LICENSE / .gitignore | REM-T06 | OPEN — **một phần đã xử lý** (`.gitignore` thêm ở S003; README/LICENSE còn lại) |
| FIND-010 | INFO | Chưa có code ứng dụng trong phạm vi (ghi nhận, không phải lỗi) | — | Không hành động |
| FIND-011 | LOW | Changelog lịch sử có một bare reference không resolve được | REM-T03/T05 | OPEN |
| FIND-012 | LOW | README của validator chỉ tài liệu hóa 2/5 script | REM-T05 | OPEN |

Tổng — CRITICAL 0 · HIGH 2 · MEDIUM 5 · LOW 4 · INFO 1 · **12 tổng cộng**.
**RESOLVED: 2 / 12.**

## Micro Task (Inline)

Checklist canonical:
`governance/templates/MICRO_TASK_CHECKLIST.md`

KHÔNG lặp lại hay viết lại checklist ở đây.

### MICRO-001 — REM-T04 — Sửa các reference đường dẫn canonical bị gãy
Status:
**READY** (dependency REM-T02 đã DONE)

Agent Tier:
Tier A / escalate Tier B

Bị Chặn Bởi:
Không — REM-T02 đã DONE.

Checklist Reference:
`governance/templates/MICRO_TASK_CHECKLIST.md`

Compact Completion Gate — FROZEN 2026-08-22 (S002).
Ngoài checklist canonical, task này yêu cầu:
- Scan reference-integrity báo cáo 0 reference gãy ngoài các ngoại lệ đã ghi
  nhận — Evidence Level E1
- `git diff` chỉ cho thấy thay đổi path-token trên đúng ba dòng — Evidence Level E1

Quy Tắc Promotion:
Nếu việc sửa cần nhiều hơn ba dòng, DỪNG coi đây là MICRO và promote lên
MAJOR theo `governance/core/TASK_MODE_STANDARD.md`.

Tóm Tắt Evidence:
Cập nhật S003: hai trong ba vị trí đã được **sửa xong** ngoài phạm vi chính
thức của MICRO-001 — như một phần của việc dịch file (CLAUDE.md và
governance/core/PROJECT_PROFILE_STANDARD.md), người thực hiện dịch đã tiện thể
sửa luôn hai reference `OPTIONAL_ENFORCEMENT_LAYER.md`. Cần một session sau
xác nhận lại đầy đủ bằng scan reference-integrity trước khi đánh MICRO-001 là
DONE chính thức — chưa tự động coi là hoàn tất chỉ vì nội dung đã đúng, do
chưa chạy Compact Completion Gate của chính task này. Phạm vi gốc, **giờ ở
repository root**: `CLAUDE.md:215` (đã sửa),
`governance/core/PROJECT_PROFILE_STANDARD.md:77` (đã sửa), `CLAUDE.md:27` (đã
sửa cùng lúc dịch CLAUDE.md). Số dòng gốc tính theo baseline commit `0394267`;
xác định lại theo nội dung, không theo số dòng, vì file đã di chuyển ở commit
`699b105`.

### MICRO-002 — REM-T06 — Vệ sinh repository root
Status:
PLANNED

Agent Tier:
Tier A / escalate Tier B

Bị Chặn Bởi:
Không — REM-T02 đã DONE. Gate chưa finalize; finalize trước PHASE-03.

Checklist Reference:
`governance/templates/MICRO_TASK_CHECKLIST.md`

Compact Completion Gate:
PRELIMINARY — finalize trước PHASE-03.

Tóm Tắt Evidence:
`.gitignore` (bao gồm `.claude/` và `__pycache__/`) đã được thêm ở S003 như
một fix phụ cho một cảnh báo stop-hook local, trước khi task này chính thức
bắt đầu. `README.md` và câu hỏi về `LICENSE` vẫn còn tồn đọng.

## Blocker Đang Hoạt Động

- Không có.

## Rủi Ro Đang Hoạt Động

- **RSK-001** (từ FIND-001, FIND-007) — **Đã giải quyết một phần.** FIND-001
  đã đóng; hệ thống governance không còn bị deploy sai nữa. FIND-007 (validator
  vẫn chưa *phát hiện* được một lần deploy sai trong tương lai) vẫn còn mở —
  REM-T03 hiện đã READY để đóng nó.
- **RSK-002** (từ FIND-005) — Một artifact validation đã ship khẳng định một
  PASS mà repo mâu thuẫn với nó. Cho tới khi REM-T05 hoàn tất, không coi bất
  kỳ điều gì dưới `governance/reference/` là evidence mà không tự derive lại.
- **RSK-003** — REM-T02 mang Blast Radius 5/5. **Đã đóng.** `git mv` thuần
  path (commit `699b105`, 0 dòng thêm/xóa), đã re-verify độc lập bằng E2
  (`docs/reviews/E2-TASK-REM-T02-S003.md`), backup ref
  `backup/pre-root-promotion-s003` đã push trước khi thực hiện, đã xác nhận
  từ chủ dự án qua AskUserQuestion.
- **RSK-004** — Chưa có nguồn E2 evidence bền vững. E2 của REM-T02 lấy qua một
  session Solo Independent Review dùng một lần, không phải CI. REM-T07 vẫn là
  task tạo ra một nguồn *bền vững*; vẫn đang READY.
- **RSK-005** — Workflow của REM-T07 phải tự phát hiện đường dẫn validator lúc
  chạy thay vì hard-code. Rủi ro thấp hơn giờ khi REM-T02 đã DONE: đường dẫn
  validator đã cố định (`governance/scripts/governance/*.py` từ repo root) và
  sẽ không di chuyển nữa nếu không có quyết định tái tổ chức mới.

## Hạng Mục Regression Đang Mở

- Không có.

## Tuân Thủ Profile

Ma trận: `PROJECT/PROJECT_PROFILE.md` → "Ma Trận Tuân Thủ Profile".

- **GAP-01** — Backup / DR. `governance/product/16_BACKUP_DISASTER_RECOVERY.md`
  bắt buộc ở PRODUCT; GitHub remote là bản sao duy nhất của repo. Chưa lên
  lịch vào PHASE-01. Đánh giá lại ở Phase Gate 03.
- **Domain DORMANT** — một số nhóm luật bắt buộc ở PRODUCT chưa có đối tượng
  vì chưa có code ứng dụng. DORMANT không phải là miễn trừ; kiểm tra lại từng
  dòng khi có code ứng dụng.

## Quyết Định Gần Đây

- DEC-001 — Bootstrap S000 thực hiện bên trong S001
- DEC-002 — Phạm vi audit giới hạn ở tính toàn vẹn deployment governance + package
- DEC-003 — Artifact audit lưu dưới `docs/audit/`
- DEC-004 — Artifact S001 viết bên trong thư mục package bị lồng
- DEC-005 — Chuyển profile AUDIT → PRODUCT
- DEC-006 — Agent tier ánh xạ sang Tier A–D; Tier D NOT_APPLICABLE
- DEC-007 — CI được áp dụng chủ động và xếp trước; REM-T04 xác nhận MICRO
- DEC-008 — REM-T01 hủy vì đã được absorbed; FIND-002 RESOLVED
- DEC-009 — REM-T02 xếp trước REM-T07 theo chỉ đạo chủ dự án; E2 qua review
  độc lập thay vì CI

Xem `PROJECT/PROJECT_DECISIONS.md`.

Quyết định kiến trúc:
- ADR-001 — Gói governance đặt tại repository root
  (`docs/adr/ADR-001-governance-package-at-repository-root.md`) — **đã triển khai**
  ở commit `699b105`.

Review độc lập:
- `docs/reviews/E2-TASK-REM-T02-S003.md` — E2 PASS cho REM-T02

## Lịch Sử Session

- S000 — PROJECT OPEN — bootstrap bên trong S001; hoàn tất xuyên suốt S001 + S002.
  Xem DEC-001, DEC-008.
- S001 — DISCOVERY & BASELINE — 2026-08-22 — DONE.
  Output: `docs/audit/S001_DISCOVERY_BASELINE.md`,
  `docs/audit/S001_AUDIT_FINDINGS.md` (12 finding),
  `docs/audit/REMEDIATION_ROADMAP.md` rev 1.
  Bàn giao: `docs/sessions/S001-discovery.md`.
- S002 — ROADMAP FINALIZATION — 2026-08-22 — DONE.
  Profile → PRODUCT. Gate PHASE-01 đã freeze. Áp dụng CH-01 (hủy REM-T01,
  FIND-002 resolved) và CH-02 (REM-T07 vào PHASE-01). ADR-001 accepted.
  REM-T07 đánh dấu READY.
  Bàn giao: `docs/sessions/S002-roadmap-finalization.md`.
- S003 — TRIỂN KHAI REM-T02 — 2026-08-22 — DONE.
  Chủ dự án đổi thứ tự REM-T02 lên trước REM-T07 (DEC-009) để sửa một lỗi
  broken-link đang hoạt động. Gói governance dời lên repository root (commit
  `699b105`, thuần path, 0 dòng thêm/xóa). E2 lấy qua Solo Independent Review
  (`docs/reviews/E2-TASK-REM-T02-S003.md`). FIND-001 RESOLVED. `.gitignore`
  được thêm (phụ, gỡ chặn một phần REM-T06). REM-T03 và REM-T04 giờ READY.
  Bàn giao: `docs/sessions/S003-root-promotion.md`.

## Session Tiếp Theo

Session Đề Xuất:
S004 — REM-T07, REM-T03, và REM-T04 đều đang READY và chạy song song an toàn.
Chọn bất kỳ task nào; khuyến nghị REM-T07 trước vì nó thiết lập nguồn E2 bền
vững (RSK-004) mà các task rủi ro cao trong tương lai nên ưu tiên hơn review
dùng một lần.

Mục Đích:
Triển khai một trong ba task READY đã chọn. Không triển khai nhiều hơn một
Scope Lock trong cùng một session trừ khi được yêu cầu rõ ràng.

File Cần Đọc Trước:
1. `CLAUDE.md`
2. `PROJECT/PROJECT_PROFILE.md`
3. `PROJECT/PROJECT_PROGRESS.md`  ← file này
4. `docs/sessions/S003-root-promotion.md`
5. File task của task được chọn (`docs/tasks/TASK-REM-T07-ci-enforcement.md`, `docs/tasks/TASK-REM-T03-validator-hardening.md`, hoặc §MICRO-001 ở trên trong file này)
6. `governance/core/EVIDENCE_STANDARD.md`
7. `governance/core/TASK_COMPLETION_GATE_STANDARD.md`
