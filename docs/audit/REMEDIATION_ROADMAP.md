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

Như đã thực thi (post-S003, theo CH-03 — REM-T02 chạy trước REM-T07):

```text
REM-T02 (promote package to repo root)   [DONE — Blast Radius 5/5]
    │
    ├──> REM-T07 (CI enforcement — creates the durable E2 path)   [READY]
    │
    ├──> REM-T03 (deployment-root + reference validators)   [READY]
    │        │
    ├──> REM-T04 (repair canonical path references)   [READY]
    │        │
    │        └──> REM-T05 (documentation & evidence truth-up)
    │
    └──> REM-T06 (root README / .gitignore)
```

REM-T07, REM-T03 và REM-T04 chỉ phụ thuộc vào REM-T02, không phụ thuộc lẫn
nhau — vì vậy cả ba đều có thể chạy độc lập ngay bây giờ khi REM-T02 đã
DONE. REM-T03 chỉ chạm vào `governance/scripts/`; REM-T04 chỉ chạm vào prose
`.md`; REM-T07 chỉ chạm vào `.github/workflows/`. Bất kỳ task nào, hoặc cả ba
song song.

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

## REM-T07 — CI enforcement layer  ·  READY

- [ ] REM-T07 hoàn tất

Closes:
FIND-008 (LOW) · Resolves RSK-004

Status:
**READY** — Ready Gate đã được xác minh trong S002; không còn dependency mở.

Task Mode:
MAJOR · Tier B / escalate Tier C

Difficulty: 2/5 · Risk: 2/5 · Blast Radius: 2/5

Scope:
`.github/workflows/governance.yml` tại gốc git repository. Không gì khác.

Critical design constraint:
Workflow phải **phát hiện (discover)** các script validator lúc runtime,
không hard-code đường dẫn của chúng — nếu không, việc di chuyển chỉ-đường-dẫn
(path-only) của REM-T02 sẽ làm hỏng nó và buộc phải chỉnh sửa nội dung bên
trong một Scope Lock vốn cấm điều đó.

Frozen Completion Gate — 7 check (6 REQUIRED, 1 RECOMMENDED):
CHECK-T07-01 … CHECK-T07-07. Toàn văn trong
`docs/tasks/TASK-REM-T07-ci-enforcement.md`.

Không thể thương lượng trong số đó: **CHECK-T07-03** — workflow phải được
quan sát thấy FAILING trên một sự cố hỏng hóc (breakage) có chủ đích. Một CI
chưa từng được thấy fail sẽ tạo ra bằng chứng E2 giả mạo.

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

## REM-T03 — Deployment-root and reference-integrity validators

- [ ] REM-T03 hoàn tất

Closes:
FIND-007 (MEDIUM); hỗ trợ xác minh máy (machine verification) cho FIND-005 và
FIND-011

Status:
**READY** — REM-T02 đã DONE (S003).

Task Mode:
MAJOR · Tier B / escalate Tier C

Difficulty: 3/5 · Risk: 2/5 · Blast Radius: 2/5

Quy tắc phân giải reference được cố định trong S002:
Phân giải từ gốc repository trước, sau đó từ thư mục riêng của file đang
tham chiếu. Một reference chỉ bị coi là hỏng khi cả hai cách đều không phân
giải được. Đây là quy tắc mà quá trình quét thủ công (manual scan) của S001
đã sử dụng, khiến CHECK-T03-03 trở thành một bài test tái tạo (reproduction
test) thực sự.

Các trường hợp loại trừ validator phải triển khai:
- `governance/reference/history/` — kho lưu trữ đã đóng băng (frozen archive)
  (FIND-011)
- `docs/audit/` — bản ghi audit bất biến; nó trích dẫn nguyên văn các token
  lỗi (defect token)
- các mẫu glob và các reference hướng tới các file mà một task PLANNED sẽ tạo
  ra trong tương lai

Frozen Completion Gate — 4 check REQUIRED:
- CHECK-T03-01 — fixture lồng nhau (nested fixture) FAIL với một thông báo
  rõ ràng — E1
- CHECK-T03-02 — bố cục gốc đã sửa (corrected root layout) exit 0 — E1
- CHECK-T03-03 — tái tạo chính xác ba reference của S001 trên cây thư mục
  trước-REM-T04 — E1
- CHECK-T03-04 — exit 0 trên cây thư mục sau-REM-T04 — E1

Task file:
`docs/tasks/TASK-REM-T03-validator-hardening.md`

## REM-T04 — Repair broken canonical path references

- [ ] REM-T04 hoàn tất

Closes:
FIND-003 (MEDIUM), FIND-004 (MEDIUM)

Status:
**READY** — REM-T02 đã DONE (S003).

Task Mode:
MICRO · Tier A / escalate Tier B

Đã xác nhận MICRO trong S002 (DEC-007): Difficulty 1, Risk 2, Blast Radius 2,
không có thay đổi về architecture, auth, schema hay thay đổi mang tính phá
hủy (destructive). Được theo dõi inline trong `PROJECT/PROJECT_PROGRESS.md`
với tên MICRO-001.

Scope — đúng ba dòng:
- [ ] `CLAUDE.md:215` — `OPTIONAL_ENFORCEMENT_LAYER.md` →
  `governance/reference/OPTIONAL_ENFORCEMENT_LAYER.md`
- [ ] `governance/core/PROJECT_PROFILE_STANDARD.md:77` — cùng phép thay thế
- [ ] `CLAUDE.md:27` — `templates/` → `governance/templates/`

Out of scope:
`governance/reference/history/` (kho lưu trữ đã đóng băng — FIND-011). Bất
kỳ việc diễn đạt lại nào vượt ngoài token đường dẫn.

Frozen compact Completion Gate — xem MICRO-001 trong
`PROJECT/PROJECT_PROGRESS.md`; checklist chính thức (canonical) là
`governance/templates/MICRO_TASK_CHECKLIST.md`.

Quy tắc promotion:
Nếu việc sửa chữa cần nhiều hơn ba dòng này, DỪNG việc coi nó là MICRO và
promote lên MAJOR theo `governance/core/TASK_MODE_STANDARD.md`.

Note:
Số dòng tính theo baseline commit `0394267`. Định vị lại theo nội dung, không
theo số dòng.

## Phase Gate 01

Theo `governance/core/PHASE_RELEASE_GATE_STANDARD.md`.

- [ ] REM-T07, REM-T02, REM-T03, REM-T04 đều DONE với các check REQUIRED PASS
- [ ] `validate_structure.py` PASS từ gốc repository
- [ ] `validate_project_state.py` PASS
- [ ] `validate_task_completion.py` PASS
- [ ] `validate_evidence.py` PASS
- [ ] Validator reference-integrity mới PASS
- [ ] CI xanh (green) trên head commit
- [ ] Bằng chứng E2 được ghi lại cho REM-T02 CHECK-T02-05
- [ ] `CLAUDE.md` nằm ở gốc repository và mọi reference chính thức (canonical)
  trong đó đều phân giải được
- [ ] Không có mục regression mở nào được đưa vào bởi PHASE-01

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
| FIND-003 | MEDIUM | REM-T04 | 01 | OPEN |
| FIND-004 | MEDIUM | REM-T04 | 01 | OPEN |
| FIND-005 | MEDIUM | REM-T05 (+REM-T03) | 02 | OPEN |
| FIND-006 | MEDIUM | REM-T05 | 02 | OPEN |
| FIND-007 | MEDIUM | REM-T03 | 01 | OPEN |
| FIND-008 | LOW | REM-T07 | 01 | OPEN |
| FIND-009 | LOW | REM-T06 | 03 | OPEN |
| FIND-010 | INFO | — | — | No action |
| FIND-011 | LOW | REM-T03 + REM-T05 | 02 | OPEN |
| FIND-012 | LOW | REM-T05 | 02 | OPEN |

Đã giải quyết (Resolved): 2 / 12. Mọi finding còn lại đều được ánh xạ tới
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
