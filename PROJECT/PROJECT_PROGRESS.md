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
2026-08-23 — cuối S007

Overall Status:
IN_PROGRESS

Phase Hiện Tại:
PHASE-01 — Governance Foundation Repair

Task Hiện Tại:
REM-T05 — Sửa tài liệu và artifact kiểm chứng

Current Task Mode:
MAJOR

Task Đề Xuất Tiếp Theo:
REM-T05 — READY, gate đã frozen (S007). Sẵn sàng implement.

## Roadmap Tổng Thể

Chú thích: `[ ]` NOT_STARTED · `[~]` IN_PROGRESS · `[x]` DONE · `[!]` BLOCKED · `[-]` CANCELLED

- [x] PHASE-00 — Audit
  - [x] S000 — Project Open — thực hiện xuyên suốt bootstrap S001 + S002 (xem DEC-008)
  - [x] S001 — Discovery & Baseline — SPIKE — DONE
  - [x] S002 — Roadmap Finalization — MAJOR — DONE

- [x] **PHASE-01 — Governance Foundation Repair — DONE**  ·  Phase Gate 01 PASS (S006, DEC-015)
  - [x] **REM-T02** — Dời gói governance lên repository root — MAJOR — Tier C — D2/R3/**B5** — **DONE** (S003) — đóng FIND-001
  - [x] **REM-T07** — CI enforcement layer — MAJOR — Tier B — D2/R2/B2 — **DONE** (S005) — đóng FIND-008, giải quyết RSK-004
  - [x] **REM-T03** — Validator deployment-root + reference-integrity — MAJOR — Tier B — D3/R2/B2 — **DONE** (S005) — đóng FIND-007
  - [x] **REM-T04** — Sửa các reference đường dẫn canonical bị gãy — MICRO — Tier A — D1/R2/B2 — **DONE** (S004) — đóng FIND-003, FIND-004
  - [x] **Phase Gate 01** — **PASS** (S006) — 10/10 check, xem DEC-015
  - [-] ~~REM-T01 — Khởi tạo project state~~ — CANCELLED (absorbed, CH-01/DEC-008)

- [ ] PHASE-02 — Documentation & Evidence Truth-Up  ·  gate đã FROZEN (S007)
  - [ ] REM-T05 — Sửa tài liệu và artifact kiểm chứng — MAJOR — Tier B — D2/R2/B3 — **READY** — đóng FIND-005, FIND-006, FIND-011, FIND-012
  - [ ] Phase Gate 02

- [ ] PHASE-03 — Repository Hygiene  ·  gate PRELIMINARY
  - [ ] REM-T06 — Vệ sinh repository root — MICRO — Tier A — D1/R1/B1 — đóng FIND-009
  - [ ] Phase Gate 03

Dependency: PHASE-01 DONE. REM-T05 đã qua Roadmap Finalization (S007), gate
frozen, READY để implement. Không có dependency nào còn mở.

## Snapshot Task Hiện Tại

Task:
REM-T05 — Sửa tài liệu và artifact kiểm chứng

Task Mode:
MAJOR

Status:
READY

Tiến Độ Gate Bắt Buộc:
0 / 4 PASS  (4 REQUIRED + 1 RECOMMENDED, tất cả NOT_TESTED — chưa implement)

Task File:
`docs/tasks/TASK-REM-T05-documentation-truth-up.md`

Completion Gate:
FROZEN 2026-08-23 (S007)

Primary Agent Tier:
Tier B — Implementation

Escalation Tier:
Tier C — Advanced Reasoning

Scope Lock:
`governance/reference/COMPACT_STRUCTURE_VALIDATION.md`,
`governance/reference/START_HERE_USAGE_GUIDE_V3_2.md`, và (chỉ nếu re-verify
phát hiện thiếu) `governance/scripts/governance/README.md`. Không được đụng
`governance/reference/history/**`, `docs/audit/**`, hay bất kỳ script `.py`
nào.

Lưu ý quan trọng khi implement:
- Subtask 05.5 (tài liệu hóa README validator) **đã DONE từ REM-T03** — chỉ
  re-verify, không viết lại nếu vẫn đúng.
- CHECK-T05-01 yêu cầu chạy lại validator TẠI THỜI ĐIỂM THỰC THI, không copy
  baseline đã chụp trong task file — chính vấn đề task này đang sửa (FIND-005)
  là hệ quả của việc không làm điều đó.

## Trạng Thái Gate Freeze

| Task | Ready Gate | Completion Gate | Check REQUIRED |
|---|---|---|---|
| REM-T02 | VERIFIED | **FROZEN** | 5/5 PASS — **DONE** |
| REM-T07 | VERIFIED | **FROZEN** | 6/6 PASS + 1/1 RECOMMENDED — **DONE** |
| REM-T03 | VERIFIED | **FROZEN** (CHECK-T03-03 sửa qua DEC-013) | 4/4 PASS — **DONE** |
| REM-T04 | MICRO compact — VERIFIED | **FROZEN** (sửa qua DEC-012) | 3/3 PASS — **DONE** |
| REM-T05 | VERIFIED — READY | **FROZEN** (S007) | 4 REQUIRED + 1 RECOMMENDED |
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
| FIND-003 | MEDIUM | Reference canonical gãy tới `OPTIONAL_ENFORCEMENT_LAYER.md` (×2) | REM-T04 | **RESOLVED** (S004, E1) |
| FIND-004 | MEDIUM | `CLAUDE.md:27` trỏ tới `templates/` không tồn tại | REM-T04 | **RESOLVED** (S004, E1) |
| FIND-005 | MEDIUM | Báo cáo validation đã ship khẳng định một PASS sai sự thật | REM-T05 | OPEN |
| FIND-006 | MEDIUM | START_HERE guide tự mâu thuẫn về layout | REM-T05 | OPEN |
| FIND-007 | MEDIUM | Validator không phát hiện được root bị deploy sai | REM-T03 | **RESOLVED** (S005, E1) |
| FIND-008 | LOW | Chưa có CI wiring cho enforcement layer | REM-T07 | **RESOLVED** (S005, E1) |
| FIND-009 | LOW | Chưa có root README / LICENSE / .gitignore | REM-T06 | OPEN — **một phần đã xử lý** (`.gitignore` thêm ở S003; README/LICENSE còn lại) |
| FIND-010 | INFO | Chưa có code ứng dụng trong phạm vi (ghi nhận, không phải lỗi) | — | Không hành động |
| FIND-011 | LOW | Changelog lịch sử có một bare reference không resolve được | REM-T03/T05 | OPEN — validator REM-T03 loại trừ có chủ đích (`governance/reference/history/`); FIND-011 tự nó chỉ đóng khi REM-T05 xử lý nội dung changelog |
| FIND-012 | LOW | README của validator chỉ tài liệu hóa 2/5 script | REM-T05 | OPEN — README đã được REM-T03 cập nhật đầy đủ 5+1 script/fixture tiện thể, nhưng FIND-012 chính thức thuộc REM-T05 nên chưa tự đóng ở đây |

Tổng — CRITICAL 0 · HIGH 2 · MEDIUM 5 · LOW 4 · INFO 1 · **12 tổng cộng**.
**RESOLVED: 6 / 12.**

## Micro Task (Inline)

Checklist canonical:
`governance/templates/MICRO_TASK_CHECKLIST.md`

KHÔNG lặp lại hay viết lại checklist ở đây.

### MICRO-001 — REM-T04 — Sửa các reference đường dẫn canonical bị gãy
Status:
DONE (S004) — xem chi tiết evidence trong lịch sử file này hoặc
`docs/tasks/TASK-REM-T04...` (task không có file riêng, theo dõi inline —
xem `docs/sessions/S004-reference-repair.md` để có bản ghi đầy đủ).

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
một fix phụ. `README.md` và câu hỏi về `LICENSE` vẫn còn tồn đọng.

## Blocker Đang Hoạt Động

- Không có.

## Rủi Ro Đang Hoạt Động

- **RSK-001** (từ FIND-001, FIND-007) — **Đã đóng.** FIND-001 và FIND-007 đều
  RESOLVED. `validate_structure.py` giờ tự phát hiện được lớp lỗi đã gây ra
  FIND-001, xác nhận qua `governance/scripts/governance/fixtures/regression_nested_layout.py` (CHECK-T03-01).
- **RSK-002** (từ FIND-005) — Chưa đổi. Một artifact validation đã ship khẳng
  định một PASS mà repo mâu thuẫn với nó. Cho tới khi REM-T05 hoàn tất, không
  coi bất kỳ điều gì dưới `governance/reference/` là evidence mà không tự
  derive lại.
- **RSK-003** — REM-T02 mang Blast Radius 5/5. **Đã đóng** (S003).
- **RSK-004** — **Đã đóng (S005).** CI (`.github/workflows/governance.yml`)
  giờ là nguồn E2 bền vững, xác nhận qua 3 lần chạy thật (1 fail đúng do lỗi
  thật, 1 pass thật, 1 fail đúng do breakage cố ý — xem REM-T07). Task rủi ro
  cao trong tương lai nên ưu tiên CI hơn review dùng một lần.
- **RSK-005** — **Đã đóng (S005).** Workflow REM-T07 tự phát hiện validator
  bằng `find`, không hard-code đường dẫn — xác nhận qua CHECK-T07-04 (mô phỏng
  layout lồng, discovery vẫn tìm thấy đúng).
- **RSK-006** (từ S004) — Kỷ luật phạm vi. Chưa đổi — vẫn là bài học đang áp
  dụng. Trong S005, một biến thể của vấn đề này xuất hiện: evidence text tự
  viết trong lúc làm REM-T03 vô tình tạo ra 2 broken reference, bị chính CI
  (REM-T07, vừa build xong) bắt được ở lần chạy đầu tiên — xem RSK-007.
- **RSK-007** (mới, S005) — Không có gì. Việc CI bắt được lỗi thật ngay từ
  run đầu tiên là **bằng chứng tích cực** rằng cả `validate_reference_integrity.py`
  và workflow đều hoạt động đúng, không phải một rủi ro cần theo dõi. Ghi lại
  ở đây chỉ để nhấn mạnh: đừng hoảng khi CI đỏ lần đầu — kiểm tra xem nó đỏ vì
  lý do đúng trước khi coi đó là lỗi của CI.
- **RSK-008** (mới, S005) — Nhánh `scratch/ci-failure-test` trên GitHub không
  xóa được từ session này (proxy chặn write tới path xóa ref — DEC-014). Nhánh
  chỉ chứa 1 commit phá hoại cố ý, không merge vào đâu, rủi ro thực tế gần như
  0, nhưng **cần owner xóa thủ công qua GitHub UI**.

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
- **CI/CD** — chuyển từ DORMANT/NOT_MANDATORY sang **ACTIVE** ở S005. Xem
  `PROJECT/PROJECT_PROFILE.md` mục CI/CD.

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
- DEC-010 — Đóng PR #1; merge nhánh làm việc vào nhánh mặc định
- DEC-011 — Thêm quy tắc Ngôn Ngữ Nội Dung; dịch toàn repo sang tiếng Việt
- DEC-012 — COMPLETION GATE CHANGE PROPOSAL cho MICRO-001; REM-T04 đóng
- DEC-013 — COMPLETION GATE CHANGE PROPOSAL cho CHECK-T03-03 (2/3 thay vì
  3/3 reference tái hiện; loại trừ reference dạng thư mục có chủ đích)
- DEC-014 — Ghi nhận giới hạn: không xóa được nhánh scratch trên GitHub qua
  session này (proxy chặn)
- DEC-015 — Phase Gate 01 PASS; PHASE-01 DONE
- DEC-016 — Roadmap Finalization cho REM-T05; gate frozen, task file tạo,
  READY

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
  Bàn giao: `docs/sessions/S001-discovery.md`.
- S002 — ROADMAP FINALIZATION — 2026-08-22 — DONE.
  Bàn giao: `docs/sessions/S002-roadmap-finalization.md`.
- S003 — TRIỂN KHAI REM-T02 — 2026-08-22 — DONE.
  Bàn giao: `docs/sessions/S003-root-promotion.md`.
- S004 — TRIỂN KHAI REM-T04 — 2026-08-23 — DONE.
  Bàn giao: `docs/sessions/S004-reference-repair.md`.
- S005 — TRIỂN KHAI REM-T03 + REM-T07 — 2026-08-23 — DONE.
  Hai task được thực hiện trong cùng session theo yêu cầu trực tiếp của chủ
  dự án. REM-T03: thêm deployment-root check vào `validate_structure.py` +
  `validate_reference_integrity.py` mới. Phát hành COMPLETION GATE CHANGE
  PROPOSAL (DEC-013) thu hẹp CHECK-T03-03. REM-T07:
  `.github/workflows/governance.yml`, verify bằng 3 lần chạy CI thật. Nhánh
  scratch không xóa được trên GitHub (DEC-014). FIND-007, FIND-008 RESOLVED
  (6/12 tổng).
  Bàn giao: `docs/sessions/S005-ci-and-validators.md`.
- S006 — PHASE GATE 01 — 2026-08-23 — PASS.
  Chạy đủ 10/10 check trong checklist Phase Gate 01, mỗi check tự thực thi
  lại từ đầu (không lấy lời khai của S005 làm evidence). **PHASE-01: DONE.**
  Chi tiết: DEC-015. Bàn giao: `docs/sessions/S006-phase-gate-01.md`.
- S007 — ROADMAP FINALIZATION (REM-T05) — 2026-08-23 — DONE.
  Đọc lại 4 file mục tiêu (FIND-005/006/011/012), xác nhận vẫn đúng như S001
  mô tả (không có drift). Phát hiện subtask 05.5 (tài liệu hóa README
  validator) đã được REM-T03 làm xong từ S005 — xác minh lại bằng lệnh, ghi
  rõ trong task file để tránh làm lại. Tạo file task chính thức từ template,
  finalize + FREEZE Completion Gate (4 REQUIRED + 1 RECOMMENDED). REM-T05
  chuyển PLANNED → READY. Không implement gì trong session này, đúng quy
  trình Roadmap Finalization.
  Bàn giao: `docs/sessions/S007-roadmap-finalization-rem-t05.md`.

## Session Tiếp Theo

Session Đề Xuất:
S008 — **Implement REM-T05**. Completion Gate đã FROZEN (S007), task đã
READY (`docs/tasks/TASK-REM-T05-documentation-truth-up.md`). Không cần
thêm một vòng Roadmap Finalization nữa — bắt tay vào sửa trực tiếp theo
Scope Lock đã ghi trong file task.

Việc cần làm trong S008 (theo subtask 05.1–05.6 trong task file):
- [ ] 05.1 — Rà lại `governance/reference/COMPACT_STRUCTURE_VALIDATION.md`
      so với cấu trúc thật hiện tại, sửa phần lệch (FIND-005/006)
- [ ] 05.2 — Rà lại `governance/reference/START_HERE_USAGE_GUIDE_V3_2.md`,
      loại bỏ path `templates//scripts/` sai và mọi tham chiếu lỗi thời khác
- [ ] 05.3 — Chạy lại các validator liên quan, đối chiếu output thật với nội
      dung tài liệu, sửa cho khớp
- [ ] 05.4 — Xác nhận `governance/scripts/governance/README.md` đã đầy đủ
      (subtask 05.5 gần như đã xong từ REM-T03/S005 — xem "Tình Trạng Thực
      Tế Của Subtask 05.5" trong task file, chỉ cần verify lại, không viết
      lại từ đầu)
- [ ] 05.5 — (xem trên, đã gần xong — chỉ re-verify)
- [ ] 05.6 — Cập nhật task file, PROJECT_PROGRESS.md, viết session handoff
- [ ] Chạy đủ 4 CHECK REQUIRED (CHECK-T05-01..04) lấy evidence E1, cân nhắc
      CHECK-T05-05 (E2 review) nếu Risk yêu cầu
- [ ] Đánh REM-T05 DONE nếu toàn bộ REQUIRED PASS + Exit Criteria thỏa mãn

Việc phụ còn tồn đọng từ trước (không thuộc REM-T05):
- Báo owner xóa thủ công nhánh `scratch/ci-failure-test` trên GitHub
  (DEC-014) — vẫn chưa xử lý.
- Owner cân nhắc bật branch protection cho check `governance` (subtask 07.7)
  — vẫn chưa xử lý.
- MICRO-002 (REM-T06, PHASE-03) vẫn còn gate PRELIMINARY (chưa frozen) — có
  thể cần một session Roadmap Finalization riêng cho nó sau này, không liên
  quan REM-T05.

Mục Đích:
Đóng PHASE-02 bằng cách thực sự sửa nội dung tài liệu bị lệch (FIND-005/
006/011/012), dưới một gate đã frozen từ S007 — tránh vừa implement vừa tự
đặt tiêu chí hoàn thành cùng lúc.

File Cần Đọc Trước:
1. `CLAUDE.md`
2. `PROJECT/PROJECT_PROFILE.md`
3. `PROJECT/PROJECT_PROGRESS.md`  ← file này
4. `docs/sessions/S007-roadmap-finalization-rem-t05.md`
5. `docs/tasks/TASK-REM-T05-documentation-truth-up.md`
6. `governance/core/TASK_COMPLETION_GATE_STANDARD.md`
7. `governance/core/EVIDENCE_STANDARD.md`
