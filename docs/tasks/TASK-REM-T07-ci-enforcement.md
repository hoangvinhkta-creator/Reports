# TASK-REM-T07 — Lớp thực thi CI (CI enforcement layer)

## Metadata
Status:
DONE

Phase:
PHASE-01 — Governance Foundation Repair

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
2/5

Project Profile:
PRODUCT

Closes Finding:
FIND-008 (LOW)

Resolves Risk:
RSK-004 (chưa tồn tại đường evidence E2)

Ready Gate Verified In:
S002 — Roadmap Finalization (2026-08-22)

Completion Gate Status:
**FROZEN** — 2026-08-22, S002

## Mục Tiêu (Objective)
Nối năm validator governance vào GitHub Actions để các vi phạm governance
được phát hiện tự động, và để project có được nguồn evidence độc lập (E2) đầu
tiên của mình.

Task này đã bị DEFERRED trong S001 chờ quyết định về profile. Việc chuyển đổi
AUDIT → PRODUCT (DEC-005) đã giải quyết điều đó:
`governance/core/PROJECT_PROFILE_STANDARD.md` không bắt buộc CI ở mức PRODUCT,
nhưng ở đây nó được đánh giá là thực tế, và đó là đường E2 khả thi duy nhất cho
một repository chỉ có một owner (DEC-007).

Được sắp xếp đầu tiên trong PHASE-01 — trước cả REM-T02 — cụ thể để
CHECK-T02-05 của REM-T02 (yêu cầu E2) có một nguồn để dựa vào.

## Phạm Vi (Scope)
- `.github/workflows/governance.yml` tại **gốc git repository**
- Không gì khác

## Ngoài Phạm Vi (Out of Scope)
- Bất kỳ file nào trong `governance/`
- Bất kỳ thay đổi nào đối với logic validator (đó là việc của REM-T03)
- Các quy tắc branch protection và cài đặt repository — những thứ này do owner
  kiểm soát và nằm ngoài thẩm quyền của agent. Nêu ra để owner xem xét; không
  được tự ý thiết lập chúng.

## Phụ Thuộc (Dependencies)
- Không có. Task này độc lập với layout của repository.

## Chặn (Blocks)
- REM-T02 (cung cấp nguồn evidence E2 cho CHECK-T02-05)

## An Toàn Để Chạy Song Song Với (Parallel-Safe With)
- Không có gì khác đang chạy; đây là task đầu tiên của PHASE-01.

## Phạm Vi Tác Động Dự Kiến (Expected Touch Area)

Allowed:
- `.github/workflows/` tại gốc git repository

Không được đụng vào nếu chưa có Scope Expansion (Do not touch without Scope Expansion):
- Mọi thứ khác trong repository

## Ràng Buộc Thiết Kế Then Chốt (Critical Design Constraint)

REM-T02 sẽ di chuyển toàn bộ 73 file được track lên gốc repository và phải
giữ nguyên là một cuộc di chuyển **chỉ-về-đường-dẫn** (path-only) với 0 thay
đổi nội dung. Một workflow hard-code đường dẫn
`AI_ENGINEERING_CONSTITUTION_TEMPLATE_V3_2_FINAL_COMPACT/governance/scripts/...`
sẽ bị hỏng ngay tại thời điểm di chuyển đó và buộc REM-T02 phải chỉnh sửa nội
dung, vi phạm Scope Lock của nó.

Do đó workflow **phải định vị các validator bằng cách discovery**, không phải
bằng đường dẫn hard-code — ví dụ resolve chúng bằng `find` từ gốc repository
và fail rõ ràng nếu không tìm thấy đúng số lượng kỳ vọng.

Ràng buộc này tồn tại để bảo vệ tính thuần khiết (purity) của REM-T02. Không
được "đơn giản hóa" nó đi.

## Subtask (Subtasks)
- [ ] 07.1 Đọc `governance/product/14_CI_CD_RELEASE_RULES.md` trước khi viết workflow
- [ ] 07.2 Tạo `.github/workflows/governance.yml` kích hoạt trên push và pull_request
- [ ] 07.3 Discover các validator script tại runtime; fail job nếu không tìm
      thấy đúng số lượng kỳ vọng
- [ ] 07.4 Chạy cả năm validator; `validate_refactor_preservation.py` được
      skip trừ khi có cung cấp một thư mục so sánh, và việc skip đó phải được
      báo cáo, không được im lặng
- [ ] 07.5 Xác minh workflow vẫn resolve đúng sau một cuộc di chuyển thư mục mô phỏng
- [ ] 07.6 Ghi nhận rằng kết quả CI giờ là một nguồn E2 được chấp nhận trong
      `PROJECT/PROJECT_PROFILE.md`
- [ ] 07.7 Nêu vấn đề branch protection với owner như một khuyến nghị

## Ready Gate — VERIFIED

Theo `governance/core/TASK_READY_GATE_STANDARD.md`, MAJOR Ready Gate:

- [x] Mục tiêu đã rõ ràng.
- [x] Scope đã được xác định.
- [x] Out-of-scope đã được xác định.
- [x] Dependencies đã DONE hoặc được waive rõ ràng — không tồn tại dependency nào.
- [x] Phạm vi tác động dự kiến đã được xác định.
- [x] Các yêu cầu liên quan đã được hiểu rõ.
- [x] Tác động đến dữ liệu đã được biết rõ — không có.
- [x] Tác động đến bảo mật đã được biết rõ — workflow không cần secret nào và
      không cần quyền ghi (write); nó phải khai báo `permissions: contents: read`.
- [x] Tác động đến routing/API đã được biết rõ nếu liên quan — NOT_APPLICABLE.
- [x] Điều kiện tiên quyết cho migration đã sẵn sàng nếu liên quan — NOT_APPLICABLE.
- [x] Difficulty đã được chấm điểm — 2/5.
- [x] Risk đã được chấm điểm — 2/5.
- [x] Blast Radius đã được chấm điểm — 2/5.
- [x] Primary agent tier đã được gán — Tier B.
- [x] Escalation triggers đã được xác định.
- [x] Completion Gate đã được finalize.
- [x] Completion Gate đã được frozen trước khi implementation.

Status: **READY**

## Completion Gate — FROZEN

Frozen 2026-08-22 tại S002. Không được xóa hoặc làm yếu đi một REQUIRED check
để khiến task này pass. Sử dụng COMPLETION GATE CHANGE PROPOSAL
(`governance/core/TASK_COMPLETION_GATE_STANDARD.md`) nếu một thay đổi là thực
sự chính đáng.

### Functional

#### CHECK-T07-01
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Workflow run #1 (`32613467285`, https://github.com/hoangvinhkta-creator/Reports/actions/runs/32613467285) hoàn tất trên nhánh `claude/s001-discovery-pka3fu`, thực thi cả 5 validator vô điều kiện qua bước 'Run required validators'. (Run #1 kết luận FAIL vì bắt được lỗi thật — xem CHECK-T07-02; đây vẫn là bằng chứng hợp lệ cho việc 'một lần chạy hoàn tất và thực thi validator', tách biệt khỏi yêu cầu 'xanh' của CHECK-T07-02.)

Executed By:
S005 agent

Timestamp:
2026-08-23T02:41Z

Yêu cầu:
Một lần chạy workflow hoàn tất trên branch và thực thi cả bốn validator vô
điều kiện. Liên kết (link) đến lần chạy đó.

#### CHECK-T07-02
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Workflow run #2 (`32613528195`, https://github.com/hoangvinhkta-creator/Reports/actions/runs/32613528195) hoàn tất `conclusion: success`. Toàn bộ 5 bước job đều `success`: Checkout, Setup Python, Discover, Run required validators (5/5 validator exit 0), Report skip. Log xác nhận từng validator in '... PASS' trước khi bước tiếp theo chạy.

Executed By:
S005 agent

Timestamp:
2026-08-23T02:42Z

Yêu cầu:
Lần chạy đó xanh (green) — mọi validator đều exit 0.

#### CHECK-T07-03
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Tạo nhánh scratch `scratch/ci-failure-test` (KHÔNG merge), sửa `PROJECT/PROJECT_PROFILE.md` `Selected Profile:` thành giá trị enum không hợp lệ (`NOT_A_REAL_PROFILE`), push. Workflow run (`32613562660`, https://github.com/hoangvinhkta-creator/Reports/actions/runs/32613562660) → `conclusion: failure`, đúng tại bước 'Run required validators', log: `PROJECT STATE: FAIL - PROJECT/PROJECT_PROFILE.md must contain a valid Selected Profile: ...`, `Process completed with exit code 1`. Sau khi quan sát fail, xóa nhánh scratch local (`git branch -D`); xóa trên remote bị chặn bởi proxy (403 — 'Write access to this GitHub API path is not permitted through this proxy', cả `git push --delete` lẫn gọi trực tiếp GitHub API DELETE). Nhánh còn tồn tại trên GitHub, chỉ chứa đúng 1 commit breakage, không merge vào đâu — cần owner xóa thủ công. Ghi nhận là giới hạn môi trường, không phải bỏ sót.

Executed By:
S005 agent

Timestamp:
2026-08-23T02:43Z

Yêu cầu:
Workflow FAIL khi một validator fail. Chứng minh điều này bằng một lỗi tạm
thời được tạo ra có chủ đích trên một scratch branch — một workflow chưa từng
được quan sát thấy fail thì không được coi là đã biết hoạt động đúng. Không
được merge lỗi tạm thời đó.

### Reliability

#### CHECK-T07-04
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Mô phỏng layout lồng cục bộ: copy toàn bộ `validate_*.py` vào `/tmp/simulated-nested-repo/SOME_WRAPPER/governance/scripts/governance/`, chạy đúng logic discovery của workflow (`find . -type d -path '*/governance/scripts/governance'`) từ thư mục gốc giả lập → tìm thấy `./SOME_WRAPPER/governance/scripts/governance` và liệt kê đủ 6 script. Xác nhận cơ chế discovery chịu được việc thư mục bị lồng ở độ sâu bất kỳ.

Executed By:
S005 agent

Timestamp:
2026-08-23T02:3xZ

Yêu cầu:
Cơ chế discovery validator vẫn hoạt động sau một cuộc di chuyển thư mục. Mô
phỏng layout của REM-T02 tại local và xác nhận bước discovery vẫn tìm thấy
đúng năm script.

#### CHECK-T07-05
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Log job của cả 2 run xanh (run #2 `32613528195`) đều có bước 'Report skip of validate_refactor_preservation.py' chạy `success` với `::notice::` nêu rõ lý do skip (cần tham số vị trí, chỉ có ý nghĩa khi đang tái cấu trúc thư mục). Không phải một lần skip im lặng.

Executed By:
S005 agent

Timestamp:
2026-08-23T02:42Z

Yêu cầu:
Việc skip `validate_refactor_preservation.py` được báo cáo trong job log kèm
lý do rõ ràng. Một lần skip im lặng đọc như một lần pass và không thể chấp
nhận được.

### Security

#### CHECK-T07-06
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`.github/workflows/governance.yml`: `permissions:\n  contents: read` (dòng 16-17, không có quyền write nào khác); không step nào tham chiếu `secrets.*`; `actions/checkout` pin tại `11bd71901bbe5b1630ceea73d27597364c9af683` (= tag `v4.2.2`, xác nhận qua `git ls-remote --tags` trực tiếp lên `github.com/actions/checkout`) và `actions/setup-python` pin tại `0b93645e9fea7318ecaed2b359559ac225c90a2b` (= tag `v5.3.0`) — cả hai là full commit SHA, không phải floating tag.

Executed By:
S005 agent

Timestamp:
2026-08-23T02:40Z

Yêu cầu:
Workflow khai báo least privilege (`permissions: contents: read`), không tiêu
thụ secret nào, và pin các action vào một phiên bản cụ thể thay vì một tag trôi
nổi (floating tag).

### Documentation

#### CHECK-T07-07
Priority:
RECOMMENDED

Status:
PASS

Evidence Level:
E0

Evidence:
`PROJECT/PROJECT_PROFILE.md` mục CI/CD đã cập nhật ghi nhận CI là nguồn E2 hợp lệ kèm 3 run thật làm dẫn chứng, và ghi khuyến nghị branch protection cho owner (subtask 07.7) — chưa tự ý thiết lập, đúng Out of Scope.

Executed By:
S005 agent

Timestamp:
2026-08-23T02:4xZ

Yêu cầu:
`PROJECT/PROJECT_PROFILE.md` ghi nhận rằng kết quả CI là một nguồn E2 được
chấp nhận, và vấn đề branch protection đã được nêu ra với owner.

## Tiêu Chí Hoàn Thành (Exit Criteria)
- [x] 100% REQUIRED checks PASS — 6/6 REQUIRED PASS + 1/1 RECOMMENDED PASS
- [x] Không có lỗi nghiêm trọng (critical) chưa xử lý
- [x] Đạt mức evidence yêu cầu — toàn bộ E1, ba lần chạy CI thật
- [x] `PROJECT/PROJECT_PROGRESS.md` đã được cập nhật
- [x] Đã viết Session Handoff — `docs/sessions/S005-ci-and-validators.md`

## Điều Kiện Kích Hoạt Leo Thang (Escalation Triggers)
- Nếu runner không thể thực thi các validator (phiên bản Python, permissions)
  → escalate lên Tier C thay vì làm yếu các check.
- Nếu CI không thể được làm cho fail trên một lỗi tạo ra có chủ đích → dừng
  lại. Một CI không thể fail còn tệ hơn không có CI, vì nó tạo ra evidence E2
  giả.

## Đăng Ký File Đã Thay Đổi (Changed Files Registry)

Created:
- `.github/workflows/governance.yml`

Modified:
- `PROJECT/PROJECT_PROFILE.md` — mục CI/CD ghi nhận CI là nguồn E2 hợp lệ
- File này (`docs/tasks/TASK-REM-T07-ci-enforcement.md`) — kết quả check, status

Deleted:
- Không có trong nhánh làm việc. Một nhánh scratch tạm thời
  (`scratch/ci-failure-test`, chỉ 1 commit breakage, không merge) được tạo để
  chứng minh CHECK-T07-03 rồi xóa local; **xóa trên remote GitHub bị chặn bởi
  proxy** (403 write-access) — cần owner xóa thủ công qua GitHub UI.

Migration Impact:
- None đối với nội dung repo. Từ nay, mọi `push`/`pull_request` sẽ kích hoạt
  workflow `governance` — owner nên cân nhắc bật branch protection (subtask
  07.7, chưa tự thiết lập).

## Ghi Chú (Notes)
Khi task này DONE, output của CI trở thành một nguồn E2 hợp lệ theo
`governance/core/EVIDENCE_STANDARD.md` ("Independent Evidence — CI result").
Điều đó trực tiếp gỡ block cho CHECK-T02-05 của REM-T02 và đóng RSK-004.

Cho đến khi CHECK-T07-03 pass, không được coi bất kỳ CI xanh nào là evidence
cho bất cứ điều gì.
