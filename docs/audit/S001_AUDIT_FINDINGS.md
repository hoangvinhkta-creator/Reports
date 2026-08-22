# Báo cáo Audit Findings — S001

Project:
`hoangvinhkta-creator/Reports`

Session:
S001 — Discovery & Baseline

Date:
2026-08-22 (UTC)

Profile:
AUDIT (chỉ đọc)

Baseline commit:
`0394267`

Severity standard:
`governance/audit/AUDIT_FINDINGS_TEMPLATE.md`

Evidence standard:
`governance/core/EVIDENCE_STANDARD.md`

Tất cả các đường dẫn bên dưới đều tương đối so với
`AI_ENGINEERING_CONSTITUTION_TEMPLATE_V3_2_FINAL_COMPACT/`, trừ khi đường dẫn
được mô tả rõ là tương đối theo repository root.

## Bảng Tóm tắt (Summary Table)

| ID | Severity | Category | Affected Area | Status |
|---|---|---|---|---|
| FIND-001 | HIGH | Architecture | Repository deployment layout | OPEN |
| FIND-002 | HIGH | Operations | `PROJECT/` state files | OPEN |
| FIND-003 | MEDIUM | Documentation | `CLAUDE.md`, `governance/core/PROJECT_PROFILE_STANDARD.md` | OPEN |
| FIND-004 | MEDIUM | Documentation | `CLAUDE.md` | OPEN |
| FIND-005 | MEDIUM | Operations | `governance/reference/COMPACT_STRUCTURE_VALIDATION.md` | OPEN |
| FIND-006 | MEDIUM | Documentation | `governance/reference/START_HERE_USAGE_GUIDE_V3_2.md` | OPEN |
| FIND-007 | MEDIUM | Operations | `governance/scripts/governance/*.py` | OPEN |
| FIND-008 | LOW | Operations | CI / enforcement layer | OPEN |
| FIND-009 | LOW | Operations | Repository root hygiene | OPEN |
| FIND-010 | INFO | Architecture | Application surface | OPEN |
| FIND-011 | LOW | Documentation | `governance/reference/history/CHANGELOG_V3_1.md` | OPEN |
| FIND-012 | LOW | Documentation | `governance/scripts/governance/README.md` | OPEN |

Số lượng — CRITICAL 0 / HIGH 2 / MEDIUM 5 / LOW 4 / INFO 1. Tổng 12.

---

## FIND-001

Finding ID:
FIND-001

Severity:
HIGH

Category:
Architecture

Affected Area:
Layout triển khai của repository (repository root)

Current Behavior:
Toàn bộ gói governance bị lồng sâu thêm một cấp thư mục dưới repository root,
bên trong `AI_ENGINEERING_CONSTITUTION_TEMPLATE_V3_2_FINAL_COMPACT/`.
Repository root chỉ chứa `.git` và duy nhất thư mục đó. Do đó `CLAUDE.md`
không nằm ở repository root.

Expected Behavior:
`governance/reference/START_HERE_USAGE_GUIDE_V3_2.md` (PHẦN 1) yêu cầu bốn
mục `CLAUDE.md`, `PROJECT/`, `docs/`, `governance/` phải được merge vào
repository root, và đánh dấu rõ ràng layout dạng thư mục lồng dưới một
heading "Không nên" (should not do), với lý do được nêu: "Framework phải
nằm cùng cấp với code của project để agent coi nó là governance của chính
repo."

Evidence:
Danh sách repository root, thực thi lúc 2026-08-22T14:05Z:

```text
$ ls -A /home/user/Reports
.git
AI_ENGINEERING_CONSTITUTION_TEMPLATE_V3_2_FINAL_COMPACT
```

Nguồn của layout kỳ vọng — `governance/reference/START_HERE_USAGE_GUIDE_V3_2.md`,
block "### Không nên":

```text
CRM/
└── AI_ENGINEERING_CONSTITUTION_TEMPLATE_V3_2/
    ├── CLAUDE.md
    ├── PROJECT/
    └── ...
```

Evidence Level:
E1

Risk:
Một agent hoặc con người mở repository sẽ không đến được `CLAUDE.md` và
không có tín hiệu nào cho biết governance tồn tại. Thứ tự read-before-work
bắt buộc được định nghĩa trong `governance/core/00_SESSION_ORCHESTRATION.md`
bị bỏ qua một cách âm thầm thay vì fail rõ ràng. Mọi phiên tiếp theo đều kế
thừa sự thiếu sót này. Lỗi này vô hình đối với các validator được đi kèm
(xem FIND-007).

Likely Cause:
Gói này được commit dưới dạng một thư mục archive đã được giải nén thay vì
được merge vào repository root.

Recommended Fix:
`git mv` cả bốn mục top-level của gói lên repository root và xóa thư mục
wrapper nay đã rỗng. Chỉ move path; không chỉnh sửa nội dung, theo rule
content-preservation trong `governance/README.md`. Chạy lại toàn bộ
validator sau khi move để xác nhận việc resolve ROOT không thay đổi.

Suggested Task:
REM-T02

Dependencies:
Nên được thực hiện trước REM-T04 để các canonical path reference chỉ cần
được sửa một lần, không phải hai lần.

Status:
OPEN

Verification Required:
- `ls -A` tại repository root hiển thị `CLAUDE.md`, `PROJECT/`, `docs/`,
  `governance/`.
- `validate_structure.py` PASS sau khi move (E1).
- `git log --follow` xác nhận history được bảo toàn cho một file mẫu đã
  move (E1).

---

## FIND-002

Finding ID:
FIND-002

Severity:
HIGH

Category:
Operations

Affected Area:
`PROJECT/PROJECT_PROFILE.md`, `PROJECT/PROJECT_PROGRESS.md`,
`PROJECT/PROJECT_DECISIONS.md`

Current Behavior:
Tại baseline S001, cả ba file project state đều là template chưa được
chỉnh sửa. `PROJECT/PROJECT_PROFILE.md` mang giá trị `Status: UNINITIALIZED`
và `Selected Profile: TO_BE_SELECTED_IN_S000`. `PROJECT/PROJECT_PROGRESS.md`
chỉ chứa các giá trị placeholder `...` và một roadmap skeleton rỗng. S000 —
PROJECT OPEN chưa từng được thực thi đối với repository này.

Expected Behavior:
`governance/core/00_SESSION_ORCHESTRATION.md` yêu cầu S000 phải chọn một
profile và khởi tạo `PROJECT/PROJECT_PROFILE.md` cùng
`PROJECT/PROJECT_PROGRESS.md` trước bất kỳ phiên discovery hay task nào.
`CLAUDE.md` yêu cầu mọi phiên implementation phải đọc các file đó và xác
định task hiện tại từ chúng.

Evidence:
`validate_project_state.py`, thực thi lúc 2026-08-22T14:03Z, Python 3.11.15:

```text
PROJECT STATE: FAIL
- PROJECT/PROJECT_PROFILE.md must contain a valid Selected Profile: AUDIT, PRODUCT, SOLO_LITE, TEAM_PRODUCTION
- PROJECT_PROGRESS.md must contain a valid Profile value: AUDIT, PRODUCT, SOLO_LITE, TEAM_PRODUCTION
exit=1
```

Evidence Level:
E1

Risk:
Session Open Protocol không thể hoàn tất. Không có profile nghĩa là không
có governance depth được định nghĩa, nên không có rule set nào có thẩm
quyền và không thể evaluate Ready Gate nào. Bất kỳ phiên nào vẫn tiếp tục
sẽ phải dựa vào conversational memory — điều mà `CLAUDE.md` (mục "Progress
Questions") cấm rõ ràng khi dùng làm cơ sở trả lời các câu hỏi về tiến độ.

Likely Cause:
Gói này được commit mà không chạy S000.

Recommended Fix:
Thực thi S000 đúng cách: chọn và biện minh cho một profile, điền vào file
progress một roadmap thật, và ghi nhận các decision ban đầu. S001 đã thực
hiện bootstrap tối thiểu cần thiết để có thể chạy discovery (chọn profile +
khởi tạo state, được ghi nhận là DEC-001); một lượt S000 đầy đủ vẫn nên xác
nhận việc phân rã phase/task và các gate sơ bộ cho profile hậu-audit.

Suggested Task:
REM-T01

Dependencies:
Không có.

Status:
OPEN — được giảm nhẹ một phần trong S001 nhờ bootstrap DEC-001; việc phân
rã S000 đầy đủ vẫn còn tồn đọng.

Verification Required:
- `validate_project_state.py` → `PROJECT STATE: PASS` (E1).
- `PROJECT/PROJECT_PROGRESS.md` chứa một roadmap không còn là placeholder
  và một Current Task (E1, file inspection).

---

## FIND-003

Finding ID:
FIND-003

Severity:
MEDIUM

Category:
Documentation

Affected Area:
`CLAUDE.md` dòng 215; `governance/core/PROJECT_PROFILE_STANDARD.md` dòng 77

Current Behavior:
Cả hai file đều tham chiếu `OPTIONAL_ENFORCEMENT_LAYER.md` như một đường
dẫn tương đối theo repository root. File này không tồn tại tại đường dẫn
đó. Vị trí thực tế của nó là
`governance/reference/OPTIONAL_ENFORCEMENT_LAYER.md`.

Expected Behavior:
Rule compact refactor trong `governance/README.md` cho phép move file và
cập nhật canonical path, và `governance/reference/PACKAGE_MANIFEST.md` liệt
kê đúng file này tại `governance/reference/OPTIONAL_ENFORCEMENT_LAYER.md`.
Cả hai tham chiếu nên dùng canonical path đó.

Evidence:
Scan resolve tham chiếu tương đối theo repository trên toàn bộ 67 file
`.md` được track (67 md + 5 py + 1 svg = 73), thực thi lúc 2026-08-22T14:04Z.
Một tham chiếu chỉ được báo cáo là bị hỏng khi nó không resolve được từ cả
package root lẫn thư mục chứa chính file tham chiếu:

```text
CLAUDE.md
   -> OPTIONAL_ENFORCEMENT_LAYER.md
governance/core/PROJECT_PROFILE_STANDARD.md
   -> OPTIONAL_ENFORCEMENT_LAYER.md
governance/reference/history/CHANGELOG_V3_1.md
   -> PROJECT_PROFILE.md
```

Grep xác nhận thêm, cùng phiên:

```text
$ grep -rn 'OPTIONAL_ENFORCEMENT_LAYER' --include=*.md .
./governance/reference/PACKAGE_MANIFEST.md:56:- `governance/reference/OPTIONAL_ENFORCEMENT_LAYER.md`
./governance/reference/history/ACCEPTANCE_CHECKLIST_V3_1.md:61:- [ ] `governance/reference/OPTIONAL_ENFORCEMENT_LAYER.md` exists.
./governance/core/PROJECT_PROFILE_STANDARD.md:77:- `OPTIONAL_ENFORCEMENT_LAYER.md` with CI integration where practical.
./CLAUDE.md:215:- `OPTIONAL_ENFORCEMENT_LAYER.md`
```

Evidence Level:
E1

Risk:
`CLAUDE.md` là entry point duy nhất của agent và
`governance/core/PROJECT_PROFILE_STANDARD.md` định nghĩa rule set cho
TEAM_PRODUCTION. Một agent đi theo bất kỳ tham chiếu nào trong hai tham
chiếu này sẽ gặp một file bị thiếu. Chế độ fail nhiều khả năng xảy ra là âm
thầm: agent coi enforcement layer là không tồn tại và tiếp tục mà không có
nó — chính là rule group được dự định để thêm CI enforcement.

Likely Cause:
Việc substitute path trong quá trình compact refactor đã bỏ sót hai lần
xuất hiện này.

Recommended Fix:
Cập nhật cả hai tham chiếu thành
`governance/reference/OPTIONAL_ENFORCEMENT_LAYER.md`. Chỉ chỉnh sửa text;
không thay đổi ngữ nghĩa.

Suggested Task:
REM-T04

Dependencies:
REM-T02 (thực hiện sau root promotion để path chỉ cần được sửa một lần).

Status:
OPEN

Verification Required:
- Scan resolve tham chiếu báo cáo 0 canonical reference bị hỏng (E1).
- `grep -rn 'OPTIONAL_ENFORCEMENT_LAYER'` không cho thấy tham chiếu
  bare-root nào (E1).

---

## FIND-004

Finding ID:
FIND-004

Severity:
MEDIUM

Category:
Documentation

Affected Area:
`CLAUDE.md` dòng 27

Current Behavior:
Section "Core Principle" map "Reusable forms" tới `templates/`. Thư mục đó
không tồn tại. Các template thực sự nằm tại `governance/templates/`.

Expected Behavior:
Section "Compact Directory Layout" (dòng 3–14) của cùng file này nói rằng
static governance được lưu dưới `governance/`, và mọi tham chiếu khác
trong `CLAUDE.md` đều dùng dạng `governance/templates/...`. Dòng 27 nên
khớp với điều đó.

Evidence:
```text
$ grep -rn '`\(templates\|scripts\)/' --include=*.md . | grep -v 'governance/'
./CLAUDE.md:27:- Reusable forms → `templates/`
```

Directory check, same session:

```text
$ ls templates
ls: cannot access 'templates': No such file or directory
$ ls governance/templates
E2_INDEPENDENT_REVIEW_TEMPLATE.md
MICRO_TASK_CHECKLIST.md
PROJECT_DECISIONS_TEMPLATE.md
PROJECT_PROGRESS_TEMPLATE.md
SESSION_HANDOFF_TEMPLATE.md
TASK_DEFINITION_TEMPLATE.md
```

Evidence Level:
E1

Risk:
Thấp hơn FIND-003 vì đường dẫn đúng xuất hiện ở nơi khác trong cùng file,
nên một agent nhiều khả năng sẽ tự phục hồi được. Tuy vậy đây vẫn là một
mâu thuẫn bên trong entry point canonical duy nhất, và là kiểu drift sẽ
tích lũy dần theo thời gian.

Likely Cause:
Cùng một kiểu substitute path chưa hoàn chỉnh như FIND-003.

Recommended Fix:
Đổi dòng 27 thành `governance/templates/`.

Suggested Task:
REM-T04

Dependencies:
REM-T02.

Status:
OPEN

Verification Required:
- Scan resolve tham chiếu báo cáo 0 canonical reference bị hỏng (E1).

---

## FIND-005

Finding ID:
FIND-005

Severity:
MEDIUM

Category:
Operations

Affected Area:
`governance/reference/COMPACT_STRUCTURE_VALIDATION.md` dòng 75

Current Behavior:
Validation report được đi kèm khẳng định:

```text
## Repository-relative Reference Integrity

Broken canonical path references: 0

PASS — no broken canonical repository-relative `.md`/`.py`/`.svg` references detected.
```

Trạng thái thực tế của repository mâu thuẫn với điều này. FIND-003 và
FIND-004 ghi nhận ba canonical reference không thể resolve trong chính gói
mà report này validate.

Expected Behavior:
Theo `governance/core/EVIDENCE_STANDARD.md` (mục "Evidence Integrity"),
một kết quả được ghi nhận phải tương ứng với một check đã thực sự được
thực thi. Một artifact được đi kèm mà khẳng định PASS phải có thể được
re-derive (suy ra lại) từ chính repository như khi được ship.

Evidence:
Khẳng định của report:

```text
$ grep -n 'Broken canonical path references' governance/reference/COMPACT_STRUCTURE_VALIDATION.md
75:Broken canonical path references: 0
```

Output scan mâu thuẫn từ phiên này được tái hiện đầy đủ trong FIND-003 (ba
tham chiếu bị hỏng trải trên hai file hiện tại và một file lịch sử).

Evidence Level:
E1

Risk:
Đây là mối lo ngại nghiêm trọng nhất trong dải MEDIUM. Cam kết trung tâm
của gói này là các gate pass dựa trên evidence chứ không phải trên
narrative. Một validation artifact được đi kèm mà khẳng định một PASS sai
chính là failure mode mà `governance/core/EVIDENCE_STANDARD.md` tồn tại để
ngăn chặn, và nó dạy các phiên trong tương lai tin tưởng các reference
report mà không re-derive.

Likely Cause:
Check reference-integrity hoặc là chưa từng được thực thi, hoặc được thực
thi với một matcher không resolve được các tên file trần được quote bằng
backtick.

Recommended Fix:
Gồm hai phần. (1) Sau khi REM-T04 sửa các reference, chạy lại check và
cập nhật report bằng lệnh và output thực tế thay vì một khẳng định suông.
(2) Implement check này thành một script dưới
`governance/scripts/governance/` để khẳng định có thể được máy tái tạo lại
thay vì viết tay.

Suggested Task:
REM-T05 (truth-up report), REM-T03 (implement script)

Dependencies:
REM-T02, REM-T04.

Status:
OPEN

Verification Required:
- Validator reference-integrity mới exit 0 (E1).
- Nội dung report khớp với output thực tế của validator đó (E1).
- E2 re-derivation bởi một phiên reviewer độc lập, theo mục "Solo
  Independent Review Procedure" của `governance/core/EVIDENCE_STANDARD.md`.

---

## FIND-006

Finding ID:
FIND-006

Severity:
MEDIUM

Category:
Documentation

Affected Area:
`governance/reference/START_HERE_USAGE_GUIDE_V3_2.md` dòng 83, 85, 144, 146, 179

Current Behavior:
File này mở đầu bằng compact layout ("Bản Compact KHÔNG đổ 60+ file
governance ra root", chỉ có bốn mục root), nhưng PHẦN 1, PHẦN 2 và PHẦN 3
ở phía dưới trong cùng file vẫn trình bày layout V3.2 trước-compact với
`templates/` và `scripts/` như các mục ở repository root.

Expected Behavior:
Toàn bộ guide nên mô tả một layout duy nhất. Theo compact structure, các
mục ở root là `CLAUDE.md`, `PROJECT/`, `docs/`, `governance/`.

Evidence:
```text
$ grep -n '├── templates/\|├── scripts/\|- `templates/`' governance/reference/START_HERE_USAGE_GUIDE_V3_2.md
83:├── templates/
85:├── scripts/
179:- `templates/`,

$ grep -n -E '^(templates|scripts)/$' governance/reference/START_HERE_USAGE_GUIDE_V3_2.md
144:templates/
146:scripts/
```

Dòng 144/146 nằm trong block PHẦN 2 "structure check after install", tức
là một người đi theo đúng bước verification của guide sẽ tìm hai thư mục
vốn không được phép tồn tại trong một deployment compact.

Evidence Level:
E1

Risk:
Tài liệu onboarding tự mâu thuẫn chính tại bước mà người dùng verify tính
đúng đắn của deployment. Đây nhiều khả năng là một nguyên nhân góp phần
gây ra FIND-001: một người đọc làm theo một guide không nhất quán sẽ dễ
làm sai layout hơn.

Likely Cause:
Section compact được prepend vào guide V3.2 mà không reconcile (đối
chiếu, thống nhất) lại phần thân bên dưới.

Recommended Fix:
Cập nhật PHẦN 1, PHẦN 2 và PHẦN 3 theo compact layout, và đổi block
verification ở PHẦN 2 để liệt kê bốn mục root của compact.

Suggested Task:
REM-T05

Dependencies:
REM-T02 (để guide tài liệu hóa đúng layout mà repository thực sự có).

Status:
OPEN

Verification Required:
- Không còn xuất hiện `templates/` hay `scripts/` như một mục root-level
  nào trong guide (E1, grep).
- Block verification của guide khớp với các required path của
  `validate_structure.py` (E1).

---

## FIND-007

Finding ID:
FIND-007

Severity:
MEDIUM

Category:
Operations

Affected Area:
`governance/scripts/governance/validate_structure.py`,
`validate_project_state.py`, `validate_evidence.py`,
`validate_task_completion.py`, `validate_refactor_preservation.py`

Current Behavior:
Mọi validator đều resolve ROOT của nó từ vị trí file của chính nó:

```python
ROOT = Path(__file__).resolve().parents[3]
```

`parents[3]` tính từ `governance/scripts/governance/<script>.py` chính là
thư mục của package. Do đó các validator luôn validate thư mục package,
bất kể repository root thực sự nằm ở đâu hay lệnh được gọi từ đâu.
`validate_structure.py` trả về PASS trên repository này dù layout triển
khai bị sai (FIND-001).

Expected Behavior:
Các validator bỏ qua working directory của caller một cách đúng đắn —
phần đó hợp lý và nên được giữ nguyên. Điều còn thiếu là bất kỳ check nào
xác nhận rằng package root *chính là* repository root. Không có validator
nào được đi kèm có thể phát hiện lớp lỗi của FIND-001.

Evidence:
Thực thi từ chính git repository root thực tế, lúc 2026-08-22T14:03Z:

```text
$ cd /home/user/Reports
$ python3 AI_ENGINEERING_CONSTITUTION_TEMPLATE_V3_2_FINAL_COMPACT/governance/scripts/governance/validate_structure.py
GOVERNANCE STRUCTURE: PASS
Checked 21 required paths.
exit=0
```

Một PASS đã được trả về trong khi `CLAUDE.md` lại vắng mặt ở repository
root.

Nguồn, `validate_structure.py` dòng 5:

```python
ROOT = Path(__file__).resolve().parents[3]
```

Evidence Level:
E1

Risk:
Sự đảm bảo giả (false assurance). `validate_structure.py` là check mà
guide START_HERE bảo người dùng chạy để xác nhận một install đúng, và nó
pass trên một install mà chính guide đó đánh dấu là sai. Bất kỳ lỗi triển
khai nào ở cấp độ này đều không bị phát hiện và bị mọi phiên kế thừa.

Likely Cause:
Các validator được viết để robust trước working directory của caller, và
tính đúng đắn của deployment-root được coi là trách nhiệm của con người.

Recommended Fix:
Thêm một assertion cho deployment-root: xác định git root (ví dụ bằng
cách tìm `.git` đi ngược lên) và verify rằng nó bằng với ROOT đã resolve;
FAIL với một message rõ ràng khi không khớp. Khi không có git root nào
tồn tại, báo cáo check này là NOT_APPLICABLE thay vì âm thầm pass. Giữ
nguyên cách resolve dựa trên `__file__` hiện có.

Suggested Task:
REM-T03

Dependencies:
REM-T02 nên được quyết định trước, vì check này mã hóa layout kỳ vọng.

Status:
OPEN

Verification Required:
- Check mới FAIL trên một fixture bị lồng có chủ đích (E1, regression
  fixture).
- Check mới PASS trên layout root đã được sửa (E1).

---

## FIND-008

Finding ID:
FIND-008

Severity:
LOW

Category:
Operations

Affected Area:
CI / enforcement layer (`.github/` tại repository root)

Current Behavior:
Không có thư mục `.github/` nào tồn tại. Năm validator chỉ có thể được
chạy bằng tay. `governance/reference/OPTIONAL_ENFORCEMENT_LAYER.md` được
đi kèm nhưng chưa được wire vào pipeline nào.

Expected Behavior:
`governance/core/PROJECT_PROFILE_STANDARD.md` chỉ yêu cầu optional
enforcement layer "with CI integration where practical" đối với
TEAM_PRODUCTION. Dưới AUDIT hoặc SOLO_LITE, CI có thể hợp lệ được ghi nhận
là NOT_APPLICABLE kèm theo lý giải.

Evidence:
```text
$ ls -A /home/user/Reports/.github
ls: cannot access '/home/user/Reports/.github': No such file or directory
```

Evidence Level:
E1

Risk:
Thấp ở profile hiện tại. Chạy validator bằng tay là chấp nhận được đối
với công việc AUDIT. Rủi ro là enforcement chỉ-bằng-tay sẽ suy giảm dần:
FIND-002 và FIND-005 đều là các ví dụ về một check đáng lẽ phải được chạy
nhưng đã không được chạy.

Likely Cause:
Sự thiếu sót phù hợp với profile; nhưng vì chưa từng có profile nào được
ghi nhận, nên sự thiếu sót này cũng chưa từng được lý giải.

Recommended Fix:
Deferred (hoãn lại). Quyết định khi profile hậu-audit được chọn. Nếu
PRODUCT hoặc TEAM_PRODUCTION được chọn, thêm một workflow chạy cả năm
validator trên push và pull request. Nếu SOLO_LITE, ghi nhận CI là
NOT_APPLICABLE kèm lý giải trong `PROJECT/PROJECT_PROFILE.md` như standard
đó cho phép.

Suggested Task:
REM-T07

Dependencies:
Chuyển đổi profile hậu-audit (xem
`governance/reference/START_HERE_USAGE_GUIDE_V3_2.md` PHẦN 7).

Status:
OPEN — DEFERRED, chờ quyết định profile.

Verification Required:
- Hoặc một lượt chạy CI xanh (green) thực thi cả năm validator (E2), hoặc
  một lý giải NOT_APPLICABLE rõ ràng được ghi nhận trong profile (E0 là đủ
  đối với một quyết định profile đã ghi nhận).

---

## FIND-009

Finding ID:
FIND-009

Severity:
LOW

Category:
Operations

Affected Area:
Root của repository

Current Behavior:
Repository root không có `README.md`, không có `LICENSE`, và không có
`.gitignore`.

Expected Behavior:
`governance/product/23_DOCUMENTATION_STANDARDS.md` áp dụng ở
TEAM_PRODUCTION. Bất kể profile nào, một repository mà toàn bộ nội dung
chỉ là một gói governance có thể tái sử dụng sẽ có lợi từ một README ở
root nói rõ nó là gì và cách deploy nó, cũng như từ một `.gitignore` ngăn
`__pycache__/` sinh ra từ các lượt chạy validator bị commit.

Evidence:
```text
$ ls -A /home/user/Reports
.git
AI_ENGINEERING_CONSTITUTION_TEMPLATE_V3_2_FINAL_COMPACT
```

Evidence Level:
E1

Risk:
Nhỏ. Một người mới không có định hướng gì ở repository root — điều này
càng làm trầm trọng thêm FIND-001, vì hiện tại cũng không có gì ở root trỏ
đến gói governance cả. Thiếu `.gitignore`, các cache bytecode Python sinh
ra từ các lượt chạy validator có thể bị commit nhầm.

Likely Cause:
Repository được tạo chỉ nhằm mục đích chứa gói đã được upload.

Recommended Fix:
Thêm một `README.md` ngắn ở root trỏ đến `CLAUDE.md`, và một `.gitignore`
bao phủ `__pycache__/` và `*.pyc`. `LICENSE` là một quyết định kinh doanh,
không phải kỹ thuật — hãy nêu vấn đề này lên, đừng tự chọn.

Suggested Task:
REM-T06

Dependencies:
REM-T02 (thêm README sau khi layout root đã ổn định).

Status:
OPEN

Verification Required:
- Các file hiện diện tại repository root (E1).
- `git status` sạch sau một lượt chạy validator đầy đủ (E1).

---

## FIND-010

Finding ID:
FIND-010

Severity:
INFO

Category:
Architecture

Affected Area:
Bề mặt ứng dụng (toàn bộ repository)

Current Behavior:
Repository này không chứa mã ứng dụng nào, không có runtime, không có
dependency manifest, không có database, không có bề mặt authentication và
không có external integration. Toàn bộ 73 file được track đều là gói
governance.

Expected Behavior:
Không phải một lỗi. Được ghi nhận để các section 1–8 của Discovery
Baseline được đánh dấu rõ ràng là NOT_APPLICABLE_AT_BASELINE thay vì âm
thầm để trống, và để một phiên trong tương lai có thể phân biệt "chưa được
audit" với "không có gì để audit".

Evidence:
```text
$ git ls-files | wc -l
73
$ find AI_ENGINEERING_CONSTITUTION_TEMPLATE_V3_2_FINAL_COMPACT -type f | wc -l
73
$ grep -n "Total files" .../governance/reference/PACKAGE_MANIFEST.md
3:Total files: 73
$ find . -path ./.git -prune -o -type f \( -name '*.js' -o -name '*.ts' -o -name '*.json' -o -name '*.html' -o -name '*.yml' -o -name '*.yaml' \) -print
(no output)
```

Số lượng file được track, số lượng trên filesystem, và số lượng được khai
báo trong manifest đi kèm đều khớp nhau ở con số 73. Tính toàn vẹn của
package inventory: PASS.

Evidence Level:
E1

Risk:
Không có ở baseline. Ghi chú này tồn tại để ngăn một phiên trong tương lai
đọc nhầm các section inventory rỗng là một audit chưa hoàn chỉnh.

Likely Cause:
N/A — trạng thái được kỳ vọng đối với một repository chỉ chứa governance.

Recommended Fix:
Không cần hành động. Chạy lại discovery cho các section 1–8 khi mã ứng
dụng lần đầu được đưa vào.

Suggested Task:
Không có.

Dependencies:
Không có.

Status:
OPEN — mang tính thông tin, không dự định remediate.

Verification Required:
Không có.

---

## FIND-011

Finding ID:
FIND-011

Severity:
LOW

Category:
Documentation

Affected Area:
`governance/reference/history/CHANGELOG_V3_1.md` dòng 19

Current Behavior:
Tham chiếu `PROJECT_PROFILE.md` như một tên file trần. Nó không resolve
được từ package root; file này thực sự nằm ở `PROJECT/PROJECT_PROFILE.md`.

Expected Behavior:
Các file archive lịch sử là bản ghi đông cứng (frozen) và không được kỳ
vọng phải mang canonical path hiện hành. Tuy nhiên, khẳng định về
reference-integrity trong `governance/reference/COMPACT_STRUCTURE_VALIDATION.md`
(FIND-005) không loại trừ `history/`, nên hoặc tham chiếu, hoặc phạm vi
của khẳng định đó cần được sửa lại.

Evidence:
```text
$ grep -n 'PROJECT_PROFILE.md' governance/reference/history/CHANGELOG_V3_1.md
19:- Runtime `PROJECT_PROFILE.md`.
```

Evidence Level:
E1

Risk:
Không đáng kể về mặt vận hành. Chỉ liên quan vì đây là một trong ba tham
chiếu mâu thuẫn với khẳng định 0-broken-references được đi kèm.

Likely Cause:
Nội dung pre-compact được archive giữ nguyên văn, đây là hành vi đúng đắn
đối với một bản ghi lịch sử.

Recommended Fix:
Không viết lại file lịch sử. Thay vào đó, giới hạn phạm vi của validator
reference-integrity để loại trừ `governance/reference/history/`, và nêu rõ
sự loại trừ đó trong validation report để khẳng định được chính xác.

Suggested Task:
REM-T03 (phạm vi validator), REM-T05 (câu chữ của report)

Dependencies:
Không có.

Status:
OPEN

Verification Required:
- Danh sách loại trừ của validator được tài liệu hóa trong report (E1).

---

## FIND-012

Finding ID:
FIND-012

Severity:
LOW

Category:
Documentation

Affected Area:
`governance/scripts/governance/README.md`

Current Behavior:
README của validator chỉ tài liệu hóa hai trong số năm validator
(`validate_structure.py`, `validate_project_state.py`).
`validate_task_completion.py`, `validate_evidence.py` và
`validate_refactor_preservation.py` không được nhắc đến, bao gồm cả
positional argument bắt buộc của `validate_refactor_preservation.py`.

Expected Behavior:
README là bề mặt discovery cho enforcement tooling. Guide START_HERE
(PHẦN 2) đã bảo người dùng chạy bốn trong số năm validator; README ít
nhất nên khớp với điều đó, và tài liệu hóa argument của script thứ năm.

Evidence:
```text
$ cat governance/scripts/governance/README.md
... documents only:
python governance/scripts/governance/validate_structure.py
python governance/scripts/governance/validate_project_state.py
```

Invocation contract chưa được tài liệu hóa, quan sát lúc 2026-08-22T14:03Z:

```text
$ python3 governance/scripts/governance/validate_refactor_preservation.py
USAGE: validate_refactor_preservation.py <non-compact-v3.2-final-dir>
exit=2
```

Evidence Level:
E1

Risk:
Thấp. Hai check enforcement đang tồn tại ít có khả năng được chạy hơn,
điều này làm suy yếu chính giả định về kỷ luật-thủ-công đã nêu trong
FIND-008.

Likely Cause:
README được viết trước khi các validator sau này được thêm vào.

Recommended Fix:
Liệt kê cả năm validator kèm mục đích, cách invoke và exit code kỳ vọng;
ghi chú rằng `validate_refactor_preservation.py` yêu cầu một thư mục so
sánh và chỉ có ý nghĩa trong khi thực hiện structure refactor.

Suggested Task:
REM-T05

Dependencies:
Không có.

Status:
OPEN

Verification Required:
- README liệt kê cả năm script hiện có trong thư mục (E1, diff so với
  `ls governance/scripts/governance/*.py`).

---

## Evidence Ledger (Sổ ghi Evidence)

| Check | Command | Result | Level | Executed By | Timestamp |
|---|---|---|---|---|---|
| CHK-S001-01 | `python3 governance/scripts/governance/validate_structure.py` | PASS (21 paths) | E1 | S001 agent | 2026-08-22T14:03Z |
| CHK-S001-02 | `python3 governance/scripts/governance/validate_project_state.py` | FAIL (2 errors) | E1 | S001 agent | 2026-08-22T14:03Z |
| CHK-S001-03 | `python3 governance/scripts/governance/validate_task_completion.py` | PASS (0 DONE) | E1 | S001 agent | 2026-08-22T14:03Z |
| CHK-S001-04 | `python3 governance/scripts/governance/validate_evidence.py` | PASS (0 records) | E1 | S001 agent | 2026-08-22T14:03Z |
| CHK-S001-05 | `validate_structure.py` invoked from git root | PASS despite wrong layout | E1 | S001 agent | 2026-08-22T14:03Z |
| CHK-S001-06 | Repository-relative reference resolution scan (67 `.md` files) | 3 broken references | E1 | S001 agent | 2026-08-22T14:04Z |
| CHK-S001-07 | `git ls-files \| wc -l` vs `find \| wc -l` vs manifest count | 73 / 73 / 73 — consistent | E1 | S001 agent | 2026-08-22T14:05Z |
| CHK-S001-08 | Root inventory `ls -A /home/user/Reports` | Only `.git` + package dir | E1 | S001 agent | 2026-08-22T14:05Z |
| CHK-S001-09 | Application-code sweep (`*.js`,`*.ts`,`*.json`,`*.html`,`*.yml`,`*.yaml`) | 0 matches | E1 | S001 agent | 2026-08-22T14:05Z |

E2 status:
NOT_OBTAINED. Không có CI, không có staging và không có phiên reviewer độc
lập nào chạy đối chiếu các finding này. Theo
`governance/core/EVIDENCE_STANDARD.md`, hạn chế này được ghi nhận thay vì
bị che giấu. Các finding mà việc remediation chạm vào read path của agent
(FIND-001, FIND-003, FIND-005, FIND-007) nên đạt được E2 thông qua một
phiên reviewer độc lập trước khi task của chúng được đánh dấu DONE.
