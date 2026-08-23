# Remediation Roadmap — từ S001 Discovery

Project:
`hoangvinhkta-creator/Reports`

Produced by:
S001 — Discovery & Baseline (2026-08-22)

Finalized by:
S002 — Roadmap Finalization (2026-08-22)

Source findings:
`docs/audit/S001_AUDIT_FINDINGS.md`

Source baseline:
`docs/audit/S001_DISCOVERY_BASELINE.md`

Profile:
PRODUCT (chuyển đổi từ AUDIT trong S002 — DEC-005)

Status of this roadmap:
**FINALIZED cho PHASE-01.** Các gate của PHASE-02 và PHASE-03 vẫn còn
PRELIMINARY, theo `governance/core/00_SESSION_ORCHESTRATION.md`: "Không đóng
băng chi tiết các task ở xa trước khi discovery đã đủ."

## Lịch sử chỉnh sửa

| Rev | Session | Change |
|---|---|---|
| 1 | S001 | Roadmap khởi tạo — 3 phase, 7 task, các gate ở trạng thái preliminary |
| 2 | S002 | Profile → PRODUCT; CH-01 và CH-02 được áp dụng; các gate của PHASE-01 được frozen; agent tier được ánh xạ sang A–D |
| 3 | S003 | CH-03 được áp dụng — REM-T02 được thực thi trước REM-T07; REM-T02 DONE; FIND-001 RESOLVED; REM-T03/REM-T04 được gỡ block |
| 4 | S004 | REM-T04 DONE; FIND-003 và FIND-004 RESOLVED; gate MICRO-001 sửa qua COMPLETION GATE CHANGE PROPOSAL (DEC-012) |
| 5 | S005 | REM-T03 và REM-T07 DONE; FIND-007 và FIND-008 RESOLVED; gate CHECK-T03-03 sửa qua COMPLETION GATE CHANGE PROPOSAL (DEC-013); toàn bộ 4 task chính PHASE-01 hoàn tất, chuyển sang Phase Gate 01 |

### ROADMAP CHANGE CH-01 — REM-T01 bị hủy (cancelled, được hấp thụ)

Reason:
Quy trình S000 mà REM-T01 tồn tại để hoàn tất đã được thực thi đầy đủ xuyên
suốt S001 (bootstrap, DEC-001) và S002 (chuyển đổi profile, ánh xạ tier, đóng
băng gate). Không còn bước nào của quy trình S000 gồm 15 bước chính thức
(canonical) còn sót lại. Xem bảng từng bước trong
`docs/tasks/TASK-REM-T01-project-state-init.md`.

Affected tasks:
REM-T01 → CANCELLED. Nó từng là dependency của mọi task khác; cạnh phụ thuộc
(dependency edge) đó đã được gỡ bỏ.

Dependency impact:
PHASE-01 mất đi head node của nó. REM-T07 trở thành điểm vào (entry point).

Risk:
Thấp. Verification Required mà FIND-002 nêu ra đã được đáp ứng với bằng chứng
E1. Rủi ro là một phiên tương lai có thể giả định rằng S000 đã bị bỏ qua;
được giảm thiểu bằng cách giữ lại task file với một Cancellation Record đầy
đủ thay vì xóa nó.

Recommended change:
Đã áp dụng. FIND-002 → RESOLVED (E1, E2 không thu thập được).

### ROADMAP CHANGE CH-02 — REM-T07 được bỏ hoãn (un-deferred) và chuyển vào PHASE-01

Reason:
S001 đã hoãn (deferred) REM-T07 chờ quyết định về profile. PRODUCT giải quyết
vấn đề này: CI không bắt buộc ở profile này nhưng được đánh giá là thực tế
(practical), và đây là nguồn bằng chứng E2 khả thi duy nhất cho một
repository chỉ có một chủ sở hữu (single-owner). CHECK-T02-05 của REM-T02 yêu
cầu E2. Sắp xếp CI lên trước sẽ cho check đó một nguồn bằng chứng và đóng
RSK-004 trước khi task có blast-radius cao nhất chạy.

Affected tasks:
REM-T07 chuyển từ PHASE-03 sang PHASE-01, vị trí 1. REM-T02 nhận thêm một
dependency vào nó.

Dependency impact:
REM-T07 → REM-T02 → (REM-T03 ∥ REM-T04). PHASE-03 giờ chỉ còn chứa REM-T06.

Risk:
REM-T07 tạo ra một file (`.github/workflows/governance.yml`) hard-code các
đường dẫn mà REM-T02 sẽ thay đổi — điều này sẽ buộc REM-T02 phải chỉnh sửa
nội dung và phá vỡ Scope Lock chỉ-đường-dẫn (path-only) của nó. Được giảm
thiểu bằng một Critical Design Constraint trên REM-T07: workflow phải phát
hiện (discover) các validator lúc runtime thay vì hard-code đường dẫn, được
xác minh bởi CHECK-T07-04.

Recommended change:
Đã áp dụng.

### ROADMAP CHANGE CH-03 — REM-T02 được thực thi trước REM-T07

Reason:
CH-02 đã sắp xếp REM-T07 (CI) trước REM-T02 (root promotion) để REM-T02 có
một nguồn E2 dựa trên CI. Trong khoảng thời gian giữa S002 và lúc thực thi
task này, chủ sở hữu đã báo cáo — kèm ảnh chụp màn hình — rằng các liên kết
GitHub trỏ vào `docs/tasks/`, `docs/audit/`, `PROJECT/`, v.v. trả về 404, vì
các đường dẫn đó chỉ tồn tại bên dưới thư mục lồng
`AI_ENGINEERING_CONSTITUTION_TEMPLATE_V3_2_FINAL_COMPACT/`, chứ không phải ở
gốc repository. Đây chính xác là FIND-001, giờ biểu hiện thành một lỗi khả
dụng (usability defect) đang hoạt động thay vì một rủi ro được ghi nhận. Khi
được hỏi trực tiếp là nên giữ nguyên thứ tự đã đóng băng hay sửa ngay lập
tức, chủ sở hữu đã chọn sửa ngay lập tức.

Affected tasks:
REM-T02 được thực thi như task đầu tiên của PHASE-01, trước REM-T07. Ready
Gate và Scope Lock của REM-T07 không bị ảnh hưởng; nó vẫn ở trạng thái READY.

Dependency impact:
REM-T02 → (REM-T07 ∥ REM-T03 ∥ REM-T04). Cả ba giờ đều có thể chạy độc lập,
vì chúng chỉ phụ thuộc vào REM-T02, không phụ thuộc lẫn nhau hay vào REM-T07.

Risk:
CHECK-T02-05 yêu cầu bằng chứng E2. Vì chưa có CI khả dụng, E2 được thu thập
thông qua Solo Independent Review Procedure thay thế
(`docs/reviews/E2-TASK-REM-T02-S003.md`) — một con đường mà frozen gate luôn
cho phép như một phương án thay thế cho CI. Không có REQUIRED check nào bị
làm yếu đi; cùng một gate 5-check đã được thực thi, chỉ khác *nguồn* bằng
chứng cho một check so với dự kiến ban đầu.

Recommended change:
Đã áp dụng. Xem DEC-009 trong `PROJECT/PROJECT_DECISIONS.md`.

## Cách sử dụng file này

File này là kế hoạch remediation **chi tiết**: định nghĩa task, dependency,
gate, ánh xạ mức độ nghiêm trọng (severity).

`PROJECT/PROJECT_PROGRESS.md` là **checklist sống chính thức (canonical)**.
Đây là file mà mọi phiên đọc đầu tiên và là nơi được đánh dấu (tick) khi công
việc hoàn thành.

Quy tắc: đánh dấu một ô **ở đây** và trong `PROJECT/PROJECT_PROGRESS.md` cùng
nhau, trong cùng một phiên, với bằng chứng được ghi lại trong task file dưới
`docs/tasks/`. Nếu hai file mâu thuẫn nhau, `PROJECT/PROJECT_PROGRESS.md`
thắng và file này sẽ được sửa lại cho khớp.

## Ánh xạ Severity → Priority

| Severity | Priority | Target |
|---|---|---|
| CRITICAL | P0 | Ngay lập tức; chặn mọi công việc khác |
| HIGH | P1 | Phase 1 |
| MEDIUM | P2 | Phase 1–2 tùy theo dependency |
| LOW | P3 | Phase 3, hoặc sớm hơn khi nó gỡ block cho một task ưu tiên cao hơn |
| INFO | — | Không có task |

REM-T07 đóng một finding LOW nhưng nằm trong PHASE-01, vì giá trị của nó ở
đây không phải là finding mà nó đóng — mà là con đường E2 mà nó tạo ra cho
REM-T02.

## Tổng quan Phase

| Phase | Name | Tasks | Findings Closed | Gate |
|---|---|---|---|---|
| PHASE-01 | Governance Foundation Repair | REM-T07, REM-T02, REM-T03, REM-T04 | 001, 003, 004, 007, 008 | Phase Gate 01 |
| PHASE-02 | Documentation & Evidence Truth-Up | REM-T05 | 005, 006, 011, 012 | Phase Gate 02 |
| PHASE-03 | Repository Hygiene | REM-T06 | 009 | Phase Gate 03 |

FIND-002 đã được giải quyết trong S002 (CH-01). FIND-010 là INFO và đóng lại
mà không cần task.

## Dependency Graph

Như đã thực thi (post-S005 — toàn bộ PHASE-01 chính đã DONE):

```text
REM-T02 (đưa package lên gốc repo)   [DONE — S003]
    │
    ├──> REM-T07 (CI enforcement — tạo nguồn E2 bền vững)   [DONE — S005]
    │
    ├──> REM-T03 (validator deployment-root + reference)   [DONE — S005]
    │
    ├──> REM-T04 (sửa reference canonical)   [DONE — S004]
    │        │
    │        └──> REM-T05 (documentation & evidence truth-up)   [PLANNED]
    │
    └──> REM-T06 (root README / .gitignore)   [PLANNED]
```

Bước tiếp theo không phải REM-T05/T06 ngay — là **Phase Gate 01**, xác nhận
cả 4 task chính hoạt động cùng nhau đúng trước khi mở PHASE-02.

## Phân công Agent Tier

Theo `governance/core/AGENT_CAPABILITY_MATRIX.md`. Xem DEC-006.

| Task | Difficulty | Risk | Blast | Primary | Escalation |
|---|---|---|---|---|---|
| REM-T07 | 2 | 2 | 2 | Tier B | Tier C |
| REM-T02 | 2 | 3 | **5** | **Tier C** | Tier C + owner |
| REM-T03 | 3 | 2 | 2 | Tier B | Tier C |
| REM-T04 | 1 | 2 | 2 | Tier A | Tier B |
| REM-T05 | 2 | 2 | 3 | Tier B | Tier C |
| REM-T06 | 1 | 1 | 1 | Tier A | Tier B |

Tier D — Design / Creative KHÔNG áp dụng (NOT_APPLICABLE) cho dự án này.

---

# PHASE-01 — Governance Foundation Repair

Objective: làm cho hệ thống governance thực sự có thể tải được, thực sự có
thể kiểm chứng được, và được hậu thuẫn bởi bằng chứng độc lập.

Gate status: **FROZEN** cho cả bốn task tính từ 2026-08-22 (S002).

## REM-T07 — CI enforcement layer  ·  DONE

- [x] REM-T07 hoàn tất — 2026-08-23 (S005)

Closes:
FIND-008 (LOW) — **RESOLVED** · Resolves RSK-004 — **đóng**

Status:
**DONE.** `.github/workflows/governance.yml` chạy trên `push`/`pull_request`,
xác nhận qua 3 lần chạy CI thật trên GitHub Actions:
- Run #1 (`32613467285`) — FAIL đúng, bắt được 2 broken reference thật do
  chính agent đưa vào lúc soạn evidence cho REM-T03 (không phải lỗi giả).
- Run #2 (`32613528195`) — PASS sau khi sửa.
- Run trên nhánh scratch `scratch/ci-failure-test` (`32613562660`) — FAIL
  đúng trên breakage cố ý, xác nhận CI thực sự có thể fail.

Task Mode:
MAJOR · Tier B / escalate Tier C

Difficulty: 2/5 · Risk: 2/5 · Blast Radius: 2/5

Scope:
`.github/workflows/governance.yml` tại gốc git repository. Không gì khác.

Critical design constraint:
Workflow phát hiện (discover) validator bằng
`find . -type d -path '*/governance/scripts/governance'`, không hard-code
đường dẫn — xác nhận resilience qua CHECK-T07-04 (mô phỏng layout lồng cục
bộ).

Frozen Completion Gate — 7/7 check PASS (6 REQUIRED, 1 RECOMMENDED):
CHECK-T07-01 … CHECK-T07-07. Toàn văn evidence trong
`docs/tasks/TASK-REM-T07-ci-enforcement.md`.

**CHECK-T07-03** (không thể thương lượng) — PASS: workflow quan sát thấy
FAILING thật trên breakage cố ý (nhánh scratch, run `32613562660`).

Ghi chú giới hạn (DEC-014): nhánh scratch dùng để test CHECK-T07-03 không
xóa được trên GitHub qua session này — proxy chặn `git push --delete` lẫn
gọi API DELETE trực tiếp (403 "Write access to this GitHub API path is not
permitted through this proxy"). Owner cần xóa thủ công qua GitHub UI.

Task file:
`docs/tasks/TASK-REM-T07-ci-enforcement.md`

## REM-T02 — Đưa governance package lên gốc repository  ·  DONE

- [x] REM-T02 hoàn tất — 2026-08-22 (S003)

Closes:
FIND-001 (HIGH) — **RESOLVED**

Status:
**DONE.** Được thực thi trước REM-T07 theo chỉ thị rõ ràng của chủ sở hữu
(DEC-009, ROADMAP CHANGE CH-03 ở trên), vì FIND-001 đã trở thành một lỗi khả
dụng (usability defect) đang hoạt động (liên kết GitHub bị hỏng vào
`docs/`, `PROJECT/`, v.v.) thay vì một rủi ro tiềm ẩn. E2 cho CHECK-T02-05
được thu thập thông qua Solo Independent Review Procedure thay vì CI. Backup
ref `backup/pre-root-promotion-s003` đã được push trước khi di chuyển, theo
điều kiện tiên quyết (precondition) của Ready Gate.

Task Mode:
MAJOR · **Tier C** / escalate Tier C + owner

Difficulty: 2/5 · Risk: 3/5 · **Blast Radius: 5/5**

Scope:
`git mv` của `CLAUDE.md`, `PROJECT/`, `docs/`, `governance/` vào gốc
repository; xóa bỏ thư mục wrapper đã rỗng.

Out of scope:
**Bất kỳ chỉnh sửa nội dung nào.** Chỉ di chuyển đường dẫn (path-only move),
theo quy tắc bảo toàn nội dung (content-preservation) trong
`governance/README.md`. Việc sửa reference là công việc của REM-T04.

Frozen Completion Gate — 5/5 check REQUIRED PASS:
- CHECK-T02-01 — danh sách gốc hiển thị bốn mục — **PASS, E2**
- CHECK-T02-02 — `validate_structure.py` PASS từ gốc mới — **PASS, E2**
- CHECK-T02-03 — `git diff --stat HEAD~1 -M` chỉ hiển thị rename, không có
  dòng nội dung nào — **PASS, E2** (commit `699b105`: 84 file, 0 insertions,
  0 deletions; được xác minh độc lập ở cấp blob-hash cho toàn bộ 84 file)
- CHECK-T02-04 — `git log --follow` trả về lịch sử trước khi di chuyển cho
  ≥3 file được lấy mẫu — **PASS, E2** (4 file được lấy mẫu)
- CHECK-T02-05 — review độc lập xác nhận không có chỉnh sửa mang tính ngữ
  nghĩa (semantic edit) — **PASS, E2**

Nguồn E2 được sử dụng: một phiên Solo Independent Review trong một git
worktree cô lập, không có ngữ cảnh hội thoại trước đó
(`docs/reviews/E2-TASK-REM-T02-S003.md`), không phải CI — CI (REM-T07) chưa
chạy khi task này được thực thi.

Task file:
`docs/tasks/TASK-REM-T02-root-promotion.md`

## REM-T03 — Deployment-root and reference-integrity validators  ·  DONE

- [x] REM-T03 hoàn tất — 2026-08-23 (S005)

Closes:
FIND-007 (MEDIUM) — **RESOLVED**; hỗ trợ xác minh máy (machine verification)
cho FIND-005 và FIND-011

Status:
**DONE.** `validate_structure.py` mở rộng với deployment-root check +
`validate_reference_integrity.py` mới, cả hai xác nhận bằng test thật (fixture
regression + chạy trên baseline `0394267` qua git worktree cô lập).

Task Mode:
MAJOR · Tier B / escalate Tier C

Difficulty: 3/5 · Risk: 2/5 · Blast Radius: 2/5

Quy tắc phân giải reference được cố định trong S002:
Phân giải từ gốc repository trước, sau đó từ thư mục riêng của file đang
tham chiếu. Một reference chỉ bị coi là hỏng khi cả hai cách đều không phân
giải được. Đây là quy tắc mà quá trình quét thủ công (manual scan) của S001
đã sử dụng, khiến CHECK-T03-03 trở thành một bài test tái tạo (reproduction
test) thực sự.

Các trường hợp loại trừ validator đã triển khai:
- `governance/reference/history/` — kho lưu trữ đã đóng băng (frozen archive)
  (FIND-011)
- `docs/audit/` — bản ghi audit bất biến; nó trích dẫn nguyên văn các token
  lỗi (defect token)
- các mẫu glob (`*`)
- một allowlist nhỏ theo TỪNG CẶP CHÍNH XÁC (file nguồn, reference) cho các
  trích dẫn token lỗi lịch sử / forward-reference đã biết — không phải một
  miễn trừ theo token toàn cục (xem `KNOWN_EXEMPT_PAIRS` trong script)

**Giới hạn đã biết, ghi có chủ đích:** chỉ bắt reference có phần mở rộng
`.md`/`.py`/`.svg`, không bắt reference dạng thư mục (như `templates/`). Đã
thử mở rộng nhưng gây 20 false positive trên HEAD lành mạnh (đa số là ví dụ
minh họa trong văn xuôi, không phải reference thật) — revert, xem DEC-013.

Frozen Completion Gate — 4/4 check REQUIRED PASS:
- CHECK-T03-01 — fixture lồng nhau FAIL với thông báo rõ ràng — **PASS, E1**
- CHECK-T03-02 — bố cục gốc đã sửa (repo hiện tại) exit 0 — **PASS, E1**
- CHECK-T03-03 — chạy trên baseline `0394267` (git worktree cô lập), tái tạo
  **2/2** reference trong phạm vi `.md` — **PASS, E1** (sửa từ yêu cầu gốc
  "3 reference" xuống "2 reference" qua COMPLETION GATE CHANGE PROPOSAL,
  DEC-013 — reference thư mục `templates/` bị loại khỏi phạm vi một cách
  tường minh)
- CHECK-T03-04 — exit 0 trên HEAD (post-REM-T04) — **PASS, E1**

Task file:
`docs/tasks/TASK-REM-T03-validator-hardening.md`

## REM-T04 — Sửa các reference đường dẫn canonical bị gãy  ·  DONE

- [x] REM-T04 hoàn tất — 2026-08-23 (S004)

Closes:
FIND-003 (MEDIUM) — **RESOLVED** · FIND-004 (MEDIUM) — **RESOLVED**

Status:
**DONE.** Ba sửa đổi trong Scope Lock đã được thực hiện tiện thể bên trong
commit `81c115a` (dịch repo sang tiếng Việt, DEC-011), chứ không phải trong
một commit riêng của task này. S004 xác minh kết quả và đóng task.

Task Mode:
MICRO · Tier A / escalate Tier B

Đã xác nhận MICRO trong S002 (DEC-007): Difficulty 1, Risk 2, Blast Radius 2,
không có thay đổi về architecture, auth, schema hay thay đổi mang tính phá
hủy (destructive). Được theo dõi inline trong `PROJECT/PROJECT_PROGRESS.md`
với tên MICRO-001. Quy tắc promotion không kích hoạt — phạm vi thực tế đúng
ba dòng như dự kiến.

Scope — đúng ba dòng, tất cả đã sửa (số dòng theo trạng thái HEAD hiện tại):
- [x] `CLAUDE.md:228` — `OPTIONAL_ENFORCEMENT_LAYER.md` →
  `governance/reference/OPTIONAL_ENFORCEMENT_LAYER.md`
- [x] `governance/core/PROJECT_PROFILE_STANDARD.md:77` — cùng phép thay thế
- [x] `CLAUDE.md:40` — `templates/` → `governance/templates/`

Out of scope:
`governance/reference/history/` (kho lưu trữ đã đóng băng — FIND-011). Bất
kỳ việc diễn đạt lại nào vượt ngoài token đường dẫn. Cả hai đều được tôn
trọng.

Compact Completion Gate — 3/3 REQUIRED PASS (E1):
- T04-C1 — scan reference-integrity báo 0 reference gãy ngoài ngoại lệ — **PASS, E1**
- T04-C2a — cả ba token đích mang đúng giá trị canonical và đích tồn tại — **PASS, E1**
- T04-C2b — so sánh baseline `0394267` ↔ HEAD: 2 broken ref của FIND-003 biến
  mất, token FIND-004 đã sửa, **0 hồi quy** trên file đã tồn tại ở baseline — **PASS, E1**

Evidence đầy đủ: MICRO-001 trong `PROJECT/PROJECT_PROGRESS.md`.

Gate đã sửa qua COMPLETION GATE CHANGE PROPOSAL (DEC-012):
Check gốc "`git diff` chỉ cho thấy thay đổi path-token trên đúng ba dòng" trở
thành **không thể thỏa mãn**, vì các sửa đổi nằm trong commit dịch `81c115a`
vốn viết lại prose trên 78 file — diff cô lập ba dòng không tồn tại và không
thể tạo ra mà không viết lại lịch sử đã push. Thay bằng T04-C2a + T04-C2b, đo
trên toàn repo thay vì ba dòng. Không check REQUIRED nào bị gỡ hay hạ evidence
level.

## Phase Gate 01  ·  PASS

Theo `governance/core/PHASE_RELEASE_GATE_STANDARD.md`. Chạy trong S006,
2026-08-23. Chi tiết đầy đủ: DEC-015 trong `PROJECT/PROJECT_DECISIONS.md`.

- [x] REM-T07, REM-T02, REM-T03, REM-T04 đều DONE với các check REQUIRED PASS
- [x] `validate_structure.py` PASS từ gốc repository
- [x] `validate_project_state.py` PASS
- [x] `validate_task_completion.py` PASS
- [x] `validate_evidence.py` PASS
- [x] Validator reference-integrity mới PASS
- [x] CI xanh (green) trên head commit — run `32613864730` (nhánh làm việc)
      và `32613882668` (nhánh mặc định)
- [x] Bằng chứng E2 được ghi lại cho REM-T02 CHECK-T02-05 —
      `docs/reviews/E2-TASK-REM-T02-S003.md`
- [x] `CLAUDE.md` nằm ở gốc repository và mọi reference chính thức (canonical)
  trong đó đều phân giải được — 40/40 reference resolve
- [x] Không có mục regression mở nào được đưa vào bởi PHASE-01

**PHASE-01 — Governance Foundation Repair: DONE.**

---

# PHASE-02 — Documentation & Evidence Truth-Up

Objective: làm cho mọi tuyên bố (claim) được công bố đều có thể được suy ra
lại (re-derivable) từ repository.

Gate status: PRELIMINARY — đóng băng trước khi REM-T05 trở thành READY.

## REM-T05 — Correct documentation and validation artifacts

- [ ] REM-T05 hoàn tất

Closes:
FIND-005 (MEDIUM), FIND-006 (MEDIUM), FIND-011 (LOW), FIND-012 (LOW)

Task Mode:
MAJOR · Tier B / escalate Tier C

Difficulty: 2/5 · Risk: 2/5 · Blast Radius: 3/5

Depends on:
REM-T02, REM-T03, REM-T04 — các tuyên bố (claim) chỉ có thể được khẳng định
lại một khi chúng đúng và có thể kiểm tra được bằng máy (machine-checkable).

Subtasks:
- [ ] REM-T05.1 Chạy lại validator reference-integrity và thay thế khẳng định
  trống (bare assertion) trong
  `governance/reference/COMPACT_STRUCTURE_VALIDATION.md` bằng lệnh và output
  thực tế
- [ ] REM-T05.2 Nêu rõ các trường hợp loại trừ `history/` và `docs/audit/`
  trong báo cáo đó
- [ ] REM-T05.3 Đối chiếu (reconcile)
  `governance/reference/START_HERE_USAGE_GUIDE_V3_2.md` PHẦN 1/2/3 với bố cục
  compact (dòng 83, 85, 144, 146, 179 tại baseline)
- [ ] REM-T05.4 Làm cho khối xác minh (verification block) ở PHẦN 2 khớp với
  các đường dẫn bắt buộc của `validate_structure.py`
- [ ] REM-T05.5 Ghi lại tài liệu cho toàn bộ validator trong
  `governance/scripts/governance/README.md`, bao gồm cả tham số vị trí
  (positional argument) của `validate_refactor_preservation.py`
- [ ] REM-T05.6 Giữ nguyên `governance/reference/history/`, không chỉnh sửa

Preliminary Completion Gate (CHƯA FROZEN):
- CHECK-T05-01 REQUIRED — mọi kết quả validator được trích dẫn trong báo cáo
  đều tái tạo lại chính xác từng byte (byte-for-byte) khi chạy lại — E1
- CHECK-T05-02 REQUIRED — không còn mục `templates/` hay `scripts/` ở cấp
  gốc nào còn sót lại trong START_HERE guide — E1
- CHECK-T05-03 REQUIRED — README của validator liệt kê chính xác các script
  hiện có — E1
- CHECK-T05-04 REQUIRED — `git diff` xác nhận `governance/reference/history/`
  không bị đụng vào — E1
- CHECK-T05-05 RECOMMENDED — reviewer độc lập suy ra lại (re-derive) được
  các tuyên bố của báo cáo — E2

Task file:
Tạo từ `governance/templates/TASK_DEFINITION_TEMPLATE.md` khi PHASE-02 được
finalize.

## Phase Gate 02

- [ ] REM-T05 DONE với các check REQUIRED PASS
- [ ] Mọi tuyên bố (claim) trong `governance/reference/` có thể suy ra lại
  được từ trạng thái repository
- [ ] Bộ tài liệu nhất quán nội bộ (internally consistent)
- [ ] CI xanh (green)

---

# PHASE-03 — Repository Hygiene

Objective: đóng finding LOW còn lại.

Gate status: PRELIMINARY — đóng băng trước khi REM-T06 trở thành READY.

## REM-T06 — Repository root hygiene

- [ ] REM-T06 hoàn tất

Closes:
FIND-009 (LOW)

Task Mode:
MICRO · Tier A / escalate Tier B

Difficulty: 1/5 · Risk: 1/5 · Blast Radius: 1/5

Depends on:
REM-T02

Subtasks:
- [ ] REM-T06.1 Thêm `README.md` ở gốc trỏ tới `CLAUDE.md` như điểm vào
  (entry point)
- [ ] REM-T06.2 Thêm `.gitignore` bao phủ `__pycache__/` và `*.pyc`
- [ ] REM-T06.3 Đặt câu hỏi về `LICENSE` với chủ sở hữu — không tự ý chọn
  một license nào

Preliminary Completion Gate (CHƯA FROZEN):
- CHECK-T06-01 REQUIRED — `README.md` và `.gitignore` có mặt tại gốc
  repository — E1
- CHECK-T06-02 REQUIRED — `git status` sạch sau khi chạy đầy đủ validator —
  E1

## Phase Gate 03

- [ ] REM-T06 DONE
- [ ] GAP-01 (Backup / DR) được đánh giá lại và hoặc đóng hoặc được chấp
  nhận chính thức (formally accepted)
- [ ] Tất cả finding của S001 ở trạng thái RESOLVED, ACCEPTED_RISK hoặc
  DEFERRED — không còn finding nào OPEN mà không có trạng thái
- [ ] CI xanh (green)

---

# Finding → Task Traceability

| Finding | Severity | Task | Phase | Status |
|---|---|---|---|---|
| FIND-001 | HIGH | REM-T02 | 01 | **RESOLVED** (S003, E2) |
| FIND-002 | HIGH | — (absorbed, CH-01) | — | **RESOLVED** (S002, E1) |
| FIND-003 | MEDIUM | REM-T04 | 01 | **RESOLVED** (S004, E1) |
| FIND-004 | MEDIUM | REM-T04 | 01 | **RESOLVED** (S004, E1) |
| FIND-005 | MEDIUM | REM-T05 (+REM-T03) | 02 | OPEN |
| FIND-006 | MEDIUM | REM-T05 | 02 | OPEN |
| FIND-007 | MEDIUM | REM-T03 | 01 | **RESOLVED** (S005, E1) |
| FIND-008 | LOW | REM-T07 | 01 | **RESOLVED** (S005, E1) |
| FIND-009 | LOW | REM-T06 | 03 | OPEN |
| FIND-010 | INFO | — | — | No action |
| FIND-011 | LOW | REM-T03 + REM-T05 | 02 | OPEN |
| FIND-012 | LOW | REM-T05 | 02 | OPEN |

Đã giải quyết (Resolved): 6 / 12. Mọi finding còn lại đều được ánh xạ tới
một task hoặc được đánh dấu rõ ràng là không cần hành động (no-action).
Không có finding nào bị âm thầm bỏ qua.

# Open Items Not Tied To A Finding

- **GAP-01** — Backup / DR. `governance/product/16_BACKUP_DISASTER_RECOVERY.md`
  là bắt buộc ở PRODUCT; GitHub remote là bản sao (copy) duy nhất. Chưa được
  lên lịch vào PHASE-01; đánh giá lại tại Phase Gate 03. Được ghi lại trong
  `PROJECT/PROJECT_PROFILE.md`.
- **DORMANT domains** — một số nhóm quy tắc bắt buộc ở PRODUCT không có đối
  tượng vì chưa tồn tại code ứng dụng nào. Được liệt kê trong Profile
  Compliance Matrix. Kiểm tra lại khi code ứng dụng xuất hiện; không coi
  DORMANT là một sự miễn trừ (waiver).

# Roadmap Change Rule

Không tái cấu trúc roadmap này một cách âm thầm. Sử dụng định dạng ROADMAP
CHANGE PROPOSAL trong `governance/core/00_SESSION_ORCHESTRATION.md`, ghi lại
kết quả trong `PROJECT/PROJECT_DECISIONS.md`, và thêm một dòng vào Lịch sử
chỉnh sửa ở trên.
