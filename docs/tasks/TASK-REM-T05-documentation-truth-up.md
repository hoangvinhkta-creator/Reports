# TASK-REM-T05 — Sửa tài liệu và artifact kiểm chứng

## Metadata
Status:
DONE

Phase:
PHASE-02 — Documentation & Evidence Truth-Up

Task Mode:
MAJOR

Primary Agent Tier:
Tier B — Implementation

Escalation Tier:
Tier C — Advanced Reasoning

Difficulty:
2/5

Risk:
2/5

Blast Radius:
3/5

Project Profile:
PRODUCT

Closes Finding:
FIND-005 (MEDIUM), FIND-006 (MEDIUM), FIND-011 (LOW), FIND-012 (LOW)

Ready Gate Verified In:
S007 — Roadmap Finalization (2026-08-23)

Completion Gate Status:
**FROZEN** — 2026-08-23, S007

## Mục Tiêu (Objective)
Làm cho mọi tuyên bố (claim) trong `governance/reference/` có thể được suy ra
lại (re-derivable) từ trạng thái repository thật, thay vì là một khẳng định
viết tay đã lỗi thời — đúng bài học của FIND-005: một báo cáo validation
khẳng định "0 broken reference" trong khi thực tế có 3, và không ai phát hiện
ra cho tới khi S001 tự tay đối chiếu.

Bốn finding cụ thể:
1. **FIND-005** — `governance/reference/COMPACT_STRUCTURE_VALIDATION.md`
   trích dẫn output validator đã lỗi thời (thiếu dòng "Deployment root: ..."
   mới của REM-T03; số DONE task/evidence record sai; khẳng định "0 broken
   reference" là một bare assertion không kèm lệnh/output thật).
2. **FIND-006** — `governance/reference/START_HERE_USAGE_GUIDE_V3_2.md` tự
   mâu thuẫn: phần đầu mô tả đúng layout compact (4 entry ở root), nhưng
   PHẦN 1 (dòng 83, 85) và PHẦN 2 (dòng 144, 146) vẫn liệt kê `templates/` và
   `scripts/` như các entry riêng ở root — layout pre-compact.
3. **FIND-011** — `governance/reference/history/CHANGELOG_V3_1.md` chứa một
   bare reference tới tên file "PROJECT_PROFILE.md" (không có đường dẫn đầy
   đủ) không resolve được. Đây là kho lưu
   trữ đã đóng băng, KHÔNG được sửa nội dung — REM-T03 đã loại trừ thư mục
   này khỏi validator, việc còn lại của FIND-011 chỉ là ghi rõ sự loại trừ đó
   trong báo cáo validation (không viết lại lịch sử).
4. **FIND-012** — README của validator từng chỉ tài liệu hóa 2/5 script.
   **Đã được REM-T03 làm xong tiện thể ở S005** — xem "Tình Trạng Thực Tế
   Của Subtask 05.5" bên dưới. REM-T05 chỉ cần re-verify, không cần viết lại.

## Phạm Vi (Scope)
- `governance/reference/COMPACT_STRUCTURE_VALIDATION.md`
- `governance/reference/START_HERE_USAGE_GUIDE_V3_2.md`
- `governance/scripts/governance/README.md` (chỉ nếu re-verify phát hiện
  thiếu sót mới — xem ghi chú subtask 05.5)

## Ngoài Phạm Vi (Out of Scope)
- `governance/reference/history/**` — kho lưu trữ đã đóng băng, không sửa nội
  dung dưới bất kỳ hình thức nào (kể cả để "sửa" FIND-011 — xử lý FIND-011
  bằng cách ghi rõ sự loại trừ, không phải sửa file lịch sử).
- `docs/audit/**` — bản ghi audit bất biến.
- Logic của bất kỳ validator nào (`governance/scripts/governance/*.py`) —
  đó là việc của REM-T03, đã DONE. REM-T05 chỉ trích dẫn output, không sửa
  script.
- Bất kỳ file `governance/core/` hoặc `governance/product/` nào.

## Phụ Thuộc (Dependencies)
- REM-T02 — DONE (S003)
- REM-T03 — DONE (S005)
- REM-T04 — DONE (S004)

Cả ba đều đã DONE tại thời điểm finalize (S007). Không còn dependency mở.

## Chặn (Blocks)
- Không có task nào khác phụ thuộc trực tiếp vào REM-T05.

## An Toàn Để Chạy Song Song Với (Parallel-Safe With)
- REM-T06 (PHASE-03) — không giao nhau về file (REM-T06 chỉ chạm root
  `README.md`/`.gitignore`/`LICENSE`, REM-T05 chỉ chạm
  `governance/reference/`).

## Phạm Vi Tác Động Dự Kiến (Expected Touch Area)

Allowed:
- `governance/reference/COMPACT_STRUCTURE_VALIDATION.md`
- `governance/reference/START_HERE_USAGE_GUIDE_V3_2.md`
- `governance/scripts/governance/README.md` (chỉ nếu cần, xem trên)

Không được đụng vào nếu chưa có Scope Expansion (Do not touch without Scope Expansion):
- `governance/reference/history/**`
- `governance/core/**`, `governance/product/**`
- Bất kỳ script `.py` nào
- `docs/audit/**`

## Tình Trạng Thực Tế Của Subtask 05.5 (quan trọng — đọc trước khi bắt đầu)

Subtask gốc "05.5 — Ghi lại tài liệu cho toàn bộ validator trong
`governance/scripts/governance/README.md`, bao gồm cả tham số vị trí của
`validate_refactor_preservation.py`" **đã được hoàn tất trong S005**, như một
phần việc của REM-T03 (README được cập nhật tiện thể để tài liệu hóa cả 5
validator + `validate_reference_integrity.py` mới nó tạo ra + fixture).

Đã xác minh lại trong S007 (2026-08-23):
```text
$ find governance/scripts/governance -type f -name '*.py' -printf '%f\n' | \
  while read f; do grep -q "$f" governance/scripts/governance/README.md && echo "OK: $f" || echo "THIẾU: $f"; done
OK: validate_refactor_preservation.py
OK: validate_structure.py
OK: validate_reference_integrity.py
OK: validate_project_state.py
OK: validate_task_completion.py
OK: validate_evidence.py
```
Toàn bộ 6 script (5 validator + fixture) đều được README nhắc tên, kèm mô tả
tham số vị trí bắt buộc của `validate_refactor_preservation.py`.

**Không cần viết lại `governance/scripts/governance/README.md`.** CHECK-T05-03
bên dưới chỉ yêu cầu re-verify tại thời điểm thực thi task (đề phòng có validator
mới xuất hiện giữa S007 và lúc REM-T05 thực sự chạy) — nếu re-verify vẫn PASS
như hôm nay, không có việc gì phải làm ở file này.

## Subtask (Subtasks)
- [x] 05.1 Chạy cả 5 validator, chép output thật vào
      `governance/reference/COMPACT_STRUCTURE_VALIDATION.md` thay cho khẳng
      định trống hiện tại. Cập nhật cả phần "Tính toàn vẹn tham chiếu tương
      đối" bằng lệnh + output thật của `validate_reference_integrity.py`
      (không phải bare assertion "0 broken reference"). DONE — cả 5 output
      thật (structure/project_state/task_completion/evidence/reference_integrity)
      đã dán kèm lệnh đã chạy.
- [x] 05.2 Trong cùng báo cáo, nêu rõ tường minh hai loại trừ mà
      `validate_reference_integrity.py` áp dụng: `governance/reference/history/`
      và `docs/audit/`, kèm lý do (FIND-011, bản ghi audit bất biến). DONE.
- [x] 05.3 Sửa `governance/reference/START_HERE_USAGE_GUIDE_V3_2.md` PHẦN 1
      (dòng 83, 85 tại baseline — cây thư mục "Đúng") và PHẦN 2 (dòng 144,
      146 — khối kiểm tra sau khi thêm) để dùng layout compact
      (`governance/templates/`, `governance/scripts/`) thay vì `templates/`,
      `scripts/` ở cấp root. DONE. **Phát hiện thêm 1 vị trí ngoài 4 dòng đã
      nêu** — PHẦN 3 (dòng 179 tại baseline), cùng lỗi layout pre-compact
      (`templates/` liệt kê riêng thay vì `governance/templates/`). Đã đánh
      giá: cùng file đã trong Scope, cùng loại lỗi, không phải quyết định
      cần chủ dự án — sửa luôn, ghi nhận minh bạch ở đây thay vì dừng lại
      hỏi (đúng escalation trigger: "đánh giá lại phạm vi trước khi tiếp
      tục, không tự ý mở rộng" — đã đánh giá, không mở rộng ra file mới).
- [x] 05.4 Đối chiếu khối xác minh ở PHẦN 2 với danh sách 21 required path
      thật của `validate_structure.py` — khối hiện tại chỉ liệt kê 8 file
      `governance/core/` + 4 thư mục, thiếu `PROJECT/PROJECT_PROFILE.md`,
      `PROJECT/PROJECT_PROGRESS.md`, `PROJECT/PROJECT_DECISIONS.md`,
      `docs/tasks/README.md`, `docs/sessions/README.md`,
      `docs/reviews/README.md`, và 5 file `governance/templates/`. Cập nhật
      cho khớp, hoặc rút gọn thành hướng dẫn "chạy `validate_structure.py`"
      thay vì liệt kê tay (tránh lặp lại vấn đề gốc — hai nguồn sự thật dễ
      lệch nhau). DONE — chọn phương án rút gọn (đúng khuyến nghị của chính
      subtask này), thay khối liệt kê tay bằng hướng dẫn chạy validator; bổ
      sung `validate_reference_integrity.py` vào danh sách lệnh 5 validator
      (trước đó chỉ liệt 4, thiếu script REM-T03 đã thêm).
- [x] 05.5 ~~Ghi lại tài liệu README validator~~ — **đã DONE (REM-T03, S005)**.
      Chỉ re-verify bằng lệnh ở trên, không viết lại nếu vẫn PASS. DONE —
      re-verify PASS, không cần sửa README (script mới
      `regression_nested_layout.py` cũng đã được README nhắc tên sẵn).
- [x] 05.6 Xác nhận `governance/reference/history/**` không bị đụng —
      `git diff` phải trống cho thư mục này khi task kết thúc. DONE — xác
      nhận trống.

## Ready Gate — VERIFIED

Theo `governance/core/TASK_READY_GATE_STANDARD.md`, MAJOR Ready Gate:

- [x] Mục tiêu đã rõ ràng.
- [x] Scope đã được xác định.
- [x] Out-of-scope đã được xác định.
- [x] Dependencies đã DONE — REM-T02, REM-T03, REM-T04 đều DONE.
- [x] Phạm vi tác động dự kiến đã được xác định.
- [x] Các yêu cầu liên quan đã được hiểu rõ — đã đọc lại cả 4 file mục tiêu
      trong S007, xác nhận cả 4 finding vẫn đúng như S001 mô tả (không có
      drift ngoài ý muốn).
- [x] Tác động đến dữ liệu đã được biết rõ — không có.
- [x] Tác động đến bảo mật đã được biết rõ — không có; chỉ sửa văn bản
      hướng dẫn, không có code hay secret.
- [x] Tác động đến routing/API đã được biết rõ nếu liên quan — NOT_APPLICABLE.
- [x] Điều kiện tiên quyết cho migration đã sẵn sàng nếu liên quan — NOT_APPLICABLE.
- [x] Difficulty đã được chấm điểm — 2/5.
- [x] Risk đã được chấm điểm — 2/5.
- [x] Blast Radius đã được chấm điểm — 3/5 (chạm nhiều file tài liệu, nhưng
      không chạm code/data/architecture).
- [x] Primary agent tier đã được gán — Tier B.
- [x] Escalation triggers đã được xác định.
- [x] Completion Gate đã được finalize.
- [x] Completion Gate đã được frozen trước khi implementation.

Status: **READY**

## Completion Gate — FROZEN

Frozen 2026-08-23 tại S007. Không được xóa hoặc làm yếu đi một REQUIRED check
để khiến task này pass. Sử dụng COMPLETION GATE CHANGE PROPOSAL
(`governance/core/TASK_COMPLETION_GATE_STANDARD.md`) nếu một thay đổi là thực
sự chính đáng — như REM-T04 (DEC-012) và REM-T03 (DEC-013) đã từng làm khi
thực tế lệch khỏi kế hoạch.

### Documentation

#### CHECK-T05-01
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Chạy lại cả 5 validator trong session S008 (không copy baseline S007). Lần
chạy đầu (05:00:54Z) phát hiện đúng kiểu lỗi mà chính task này sửa, do chính
session này gây ra: 3 file vừa sửa/tạo (`PROJECT/PROJECT_PROGRESS.md`, session
handoff của chính session này, `governance/reference/COMPACT_STRUCTURE_VALIDATION.md`)
chứa 4 bare reference (tên file trần trụi thiếu đường dẫn đầy đủ, ví dụ
"START_HERE_USAGE_GUIDE_V3_2.md" / "CHANGELOG_V3_1.md" /
"PROJECT_PROGRESS.md") khiến
`validate_reference_integrity.py` FAIL. Đúng Escalation Trigger của task
("nếu kết quả khác baseline... dừng lại, xác định nguyên nhân trước khi viết
CHECK-T05-01") — đã dừng, sửa cả 4 bare reference thành full path, chạy lại.
Output cuối cùng (sau khi sửa), khớp byte-for-byte với những gì đã dán vào
`governance/reference/COMPACT_STRUCTURE_VALIDATION.md`:
```text
$ python3 governance/scripts/governance/validate_structure.py
GOVERNANCE STRUCTURE: PASS
Deployment root: PASS — /home/user/Reports
Checked 21 required paths.

$ python3 governance/scripts/governance/validate_project_state.py
PROJECT STATE: PASS

$ python3 governance/scripts/governance/validate_task_completion.py
TASK COMPLETION: PASS
Checked 4 DONE task(s).

$ python3 governance/scripts/governance/validate_evidence.py
EVIDENCE VALIDATION: PASS
Checked 19 REQUIRED PASS evidence record(s).

$ python3 governance/scripts/governance/validate_reference_integrity.py
REFERENCE INTEGRITY: PASS
Quét 89 file .md (loại trừ 10 file trong governance/reference/history/, docs/audit/).
0 reference bị hỏng.
```

Executed By:
Claude (session S008, Track Governance)

Timestamp:
2026-08-23T05:04:16Z

Yêu cầu:
Mọi kết quả validator được trích dẫn trong
`governance/reference/COMPACT_STRUCTURE_VALIDATION.md` phải tái tạo lại
chính xác từng byte (byte-for-byte) khi chạy lại tại thời điểm task hoàn
thành. Baseline tham khảo (chụp tại S007, 2026-08-23, sẽ khác nếu có
task/evidence mới phát sinh trước khi REM-T05 thực thi — chạy lại, không copy
nguyên si):
```text
GOVERNANCE STRUCTURE: PASS
Deployment root: PASS — /home/user/Reports
Checked 21 required paths.

PROJECT STATE: PASS

TASK COMPLETION: PASS
Checked 3 DONE task(s).

EVIDENCE VALIDATION: PASS
Checked 15 REQUIRED PASS evidence record(s).

REFERENCE INTEGRITY: PASS
Quét 74 file .md (loại trừ 9 file trong governance/reference/history/, docs/audit/).
0 reference bị hỏng.
```

#### CHECK-T05-02
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
```text
$ grep -n '^templates/$\|^scripts/$\|├── templates/\|├── scripts/' governance/reference/START_HERE_USAGE_GUIDE_V3_2.md
(không output — exit code 1)
```
Đã sửa cả 4 dòng gốc (83, 85, 144, 146) và phát hiện thêm 1 dòng ngoài phạm
vi ban đầu (179, PHẦN 3, `templates/` trong danh sách "Agent phải nhìn thấy
cùng lúc") — cùng lỗi layout pre-compact, đã sửa luôn vì cùng file/cùng loại
lỗi (ghi lại ở subtask 05.3 phía trên, không âm thầm).

Executed By:
Claude (session S008, Track Governance)

Timestamp:
2026-08-23T05:00:54Z

Yêu cầu:
Không còn mục `templates/` hay `scripts/` ở cấp gốc nào còn sót lại trong
`governance/reference/START_HERE_USAGE_GUIDE_V3_2.md`. Xác minh bằng:
```bash
grep -n '^templates/$\|^scripts/$\|├── templates/\|├── scripts/' governance/reference/START_HERE_USAGE_GUIDE_V3_2.md
```
Kỳ vọng: không output nào (hoặc chỉ còn các dòng đã sửa thành
`governance/templates/`/`governance/scripts/`).

#### CHECK-T05-03
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
```text
$ find governance/scripts/governance -type f -name '*.py' -printf '%f\n' | \
  while read f; do grep -q "$f" governance/scripts/governance/README.md && echo "OK: $f" || echo "THIẾU: $f"; done
OK: validate_refactor_preservation.py
OK: validate_structure.py
OK: validate_reference_integrity.py
OK: regression_nested_layout.py
OK: validate_project_state.py
OK: validate_task_completion.py
OK: validate_evidence.py
```
Toàn bộ 7 script `.py` hiện có (kể cả `regression_nested_layout.py` mới xuất
hiện từ S007) đều được README nhắc tên. Không sửa file này.

Executed By:
Claude (session S008, Track Governance)

Timestamp:
2026-08-23T05:00:54Z

Yêu cầu:
README của validator (`governance/scripts/governance/README.md`) liệt kê
chính xác các script hiện có. Re-verify bằng lệnh đối chiếu (xem "Tình Trạng
Thực Tế Của Subtask 05.5" ở trên) — dự kiến đã PASS sẵn từ REM-T03, không cần
sửa gì nếu vẫn đúng.

#### CHECK-T05-04
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
```text
$ git diff --stat -- governance/reference/history/
(không output)

$ git status --short
 M governance/reference/COMPACT_STRUCTURE_VALIDATION.md
 M governance/reference/START_HERE_USAGE_GUIDE_V3_2.md
```
Chỉ 2 file trong Scope bị sửa; `governance/reference/history/` không bị đụng.

Executed By:
Claude (session S008, Track Governance)

Timestamp:
2026-08-23T05:00:54Z

Yêu cầu:
`git diff` xác nhận `governance/reference/history/` không bị đụng vào trong
suốt task này.
```bash
git diff --stat -- governance/reference/history/
```
Kỳ vọng: không output nào.

### Independent Review

#### CHECK-T05-05
Priority:
RECOMMENDED

Status:
NOT_TESTED

Evidence Level:
E2

Evidence:
Không có nguồn E2 khả dụng khi thực thi task này — session S008 chạy solo,
không có reviewer thứ hai/worktree cô lập độc lập được yêu cầu bởi
`governance/core/EVIDENCE_STANDARD.md`. Ghi giới hạn tường minh theo đúng
Escalation Trigger đã nêu trong task: không nâng RECOMMENDED thành bắt buộc
rồi bỏ qua, cũng không giả vờ đã có E2. Task DONE với E1 cho toàn bộ 4
REQUIRED check (đúng điều kiện "task có thể DONE với E1 nếu không có nguồn
E2 khả dụng" ghi trong Yêu cầu của check này).

Executed By:
...

Timestamp:
...

Yêu cầu:
Một reviewer độc lập (Solo Independent Review Procedure, isolated worktree,
không có ngữ cảnh trước đó — như REM-T02 đã dùng) suy ra lại (re-derive) được
các tuyên bố trong báo cáo đã sửa. RECOMMENDED, không REQUIRED — task có thể
DONE với E1 nếu không có nguồn E2 khả dụng khi thực thi; ghi rõ giới hạn nếu
bỏ qua, không giả vờ đã có E2.

## Tiêu Chí Hoàn Thành (Exit Criteria)
- [x] 100% REQUIRED checks PASS (CHECK-T05-01 đến 04)
- [x] Không có lỗi nghiêm trọng (critical) chưa xử lý
- [x] Đạt mức evidence yêu cầu (E1 cho REQUIRED, Risk 2/5 không bắt buộc E2 —
      CHECK-T05-05 NOT_TESTED có ghi giới hạn, không chặn DONE)
- [x] `governance/reference/history/**` xác nhận không bị đụng (CHECK-T05-04)
- [x] `PROJECT/PROJECT_PROGRESS.md` đã được cập nhật — FIND-005, FIND-006,
      FIND-011, FIND-012 → RESOLVED
- [x] Đã viết Session Handoff (`docs/sessions/S008-rem-t05-documentation-truth-up.md`)

## Điều Kiện Kích Hoạt Leo Thang (Escalation Triggers)
- Nếu sửa `governance/reference/START_HERE_USAGE_GUIDE_V3_2.md` phát hiện thêm mâu thuẫn ngoài 4
  dòng đã xác định (83, 85, 144, 146) → đánh giá lại phạm vi trước khi tiếp
  tục, không tự ý mở rộng.
- Nếu `validate_reference_integrity.py` cho kết quả khác baseline đã chụp ở
  S007 (ví dụ báo broken reference mới) → dừng lại, xác định nguyên nhân
  trước khi viết CHECK-T05-01 (không trích dẫn output của một lần chạy đang
  FAIL như thể nó PASS).
- Nếu không có nguồn E2 khả dụng cho CHECK-T05-05 khi thực thi → ghi giới hạn,
  không tự ý nâng RECOMMENDED thành bắt buộc rồi bỏ qua nó.

## Đăng Ký File Đã Thay Đổi (Changed Files Registry)

Created:
- `docs/sessions/S008-rem-t05-documentation-truth-up.md`

Modified:
- `governance/reference/COMPACT_STRUCTURE_VALIDATION.md` — thay bare
  assertion bằng lệnh + output thật của cả 5 validator; nêu rõ 2 loại trừ
  của `validate_reference_integrity.py`.
- `governance/reference/START_HERE_USAGE_GUIDE_V3_2.md` — sửa layout
  pre-compact ở 5 vị trí (dòng 83, 85, 144, 146, và 179 phát hiện thêm khi
  thực thi); rút gọn khối "required paths" ở PHẦN 2 thành hướng dẫn chạy
  `validate_structure.py` thay vì liệt kê tay; bổ sung
  `validate_reference_integrity.py` vào danh sách lệnh 5 validator.
- `docs/tasks/TASK-REM-T05-documentation-truth-up.md` — Status → DONE,
  evidence CHECK-T05-01..05, subtask đánh dấu hoàn thành.
- `PROJECT/PROJECT_PROGRESS.md` — REM-T05 → DONE, đóng FIND-005, FIND-006,
  FIND-011, FIND-012.

Deleted:
- Không có.

Migration Impact:
- None. Chỉ sửa văn bản tài liệu tham khảo, không đổi ngữ nghĩa governance
  hay hành vi validator.

## Ghi Chú (Notes)
Task này là ví dụ trực tiếp của chính vấn đề nó sửa: nếu CHECK-T05-01 chỉ copy
nguyên si khối output trong "Yêu cầu" ở trên mà không chạy lại lệnh tại thời
điểm thực thi, nó sẽ tái tạo đúng lỗi của FIND-005 (bằng chứng cũ, không phải
bằng chứng thật tại thời điểm claim được đưa ra). Luôn chạy lại, không copy.
