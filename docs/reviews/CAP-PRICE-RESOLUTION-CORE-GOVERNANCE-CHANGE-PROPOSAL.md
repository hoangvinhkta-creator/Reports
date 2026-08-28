# CAP-PRICE-RESOLUTION — CORE GOVERNANCE CHANGE PROPOSAL

Loại artifact: GOVERNANCE CHANGE PROPOSAL (CORE-eligible reusable rule),
theo `governance/core/V4_1_POLICY_FREEZE.md` §14 (cơ chế thay đổi
policy đã freeze) và `CLAUDE.md` → "Xung Đột Luật".

Session gốc: S045 (2026-08-28) — TASK-105D H-07 Gate Execution
Reconciliation + Capability-First Delivery Governance Reconciliation.

Trạng thái: **PROPOSED — CHƯA ADOPTED.** Phiên S045 không có CORE-amendment
authority tường minh; đây là đề xuất chờ một phiên có thẩm quyền đó xem xét
và merge (toàn bộ hoặc một phần) vào `governance/core/V4_1_POLICY_FREEZE.md`.

## Vì sao đây là CORE, không phải PROJECT

Các nguyên tắc dưới đây không nhắc tới `CAP-PRICE-RESOLUTION`, `Reports`,
hay bất kỳ task ID cụ thể nào — chúng là quy tắc kiểm soát tổng quát cho
MỌI capability/nhóm task tương lai, đúng ranh giới CORE vs PROJECT mà
`CLAUDE.md` đã đặt ra.

## Đề xuất §16 — Capability-First Delivery & Horizontal Sibling Task Proliferation Control

*(đánh số tiếp theo §15 hiện có của `governance/core/V4_1_POLICY_FREEZE.md`)*

### 16.1 Đơn vị quyết định chính

Đơn vị chính để quyết định một hạng mục kỹ thuật có cần thiết hay không là
**BUSINESS CAPABILITY**, không phải ranh giới của một task riêng lẻ. Một
capability có thể được triển khai qua nhiều task (vertical decomposition đã
được kiểm soát tốt); rủi ro governance nằm ở **horizontal sibling
decomposition** — chia một capability thành nhiều task anh em có thể:

- phân mảnh một capability thành nhiều task nhỏ không cần thiết;
- tạo khoảng trống ownership rồi dùng chính khoảng trống đó biện minh cho
  task mới;
- nhân bản hoặc reset repair budget theo chiều ngang;
- tối ưu ranh giới governance thay vì tối ưu giá trị nghiệp vụ.

### 16.2 Sibling Task Creation Rule

Một phát hiện kỹ thuật KHÔNG được tạo task anh em chỉ vì:

- Scope Lock của task hiện tại đã freeze;
- công việc nằm ngoài scope task hiện tại;
- chưa có task nào sở hữu tường minh;
- ownership mơ hồ;
- thêm việc đó đòi sửa Scope Lock của một task.

Các lý do trên là KHÔNG ĐỦ. Việc có cần task mới hay không phải được đánh
giá so với **capability**, không phải so với một task thành viên riêng lẻ.

### 16.3 Điều kiện ngoại lệ ba-phần

Một task mới chỉ được ĐỀ XUẤT (không phải tự động tạo) khi CẢ BA đúng:

1. **INDEPENDENT CAPABILITY** — tạo ra một outcome người dùng/hệ thống có ý
   nghĩa độc lập.
2. **INDEPENDENT LIFECYCLE** — có thể spec/implement/test/review/deliver
   độc lập một cách hợp lý.
3. **OUTSIDE CURRENT CAPABILITY** — nằm ngoài capability hiện tại về mặt
   nội dung nghiệp vụ.

Các lý do sau đây KHÔNG thoả điều kiện #3: "ngoài task hiện tại", "chưa ai
sở hữu", "Scope Lock đã freeze", "có khoảng trống ownership".

### 16.4 Task Registration vs. Capability Registration

Đăng ký một **capability** (một ID không dùng tiền tố `TASK-*`, ví dụ
`CAP-*`) vào phần trạng thái dự án KHÔNG cấu thành đăng ký task. Đăng ký
task nghĩa là (1) một mục trong khu vực đăng ký task chính thức của
`PROJECT/PROJECT_PROGRESS.md`, hoặc (2) tạo một Task Spec canonical dưới
`docs/tasks/`. Việc nhắc tới một task ID giả định trong một đề xuất, phân
tích, finding, hay bằng chứng lịch sử KHÔNG cấu thành đăng ký.

### 16.5 Ownership Gap Rule

Nếu một hạng mục công việc thuộc về capability nhưng chưa thành viên hiện
tại nào sở hữu tường minh: KHÔNG tạo task. Ghi nhận tại mục
`OWNER_ASSIGNMENT_REQUIRED` của trạng thái dự án (work item, lý do mơ hồ,
candidate owner(s), tác động scope, tác động Effective Risk, có chặn hay
không, khuyến nghị, absorption status nếu áp dụng).

### 16.6 Absorption Control & Hard Limit

Khi một hạng mục mới được đề xuất hấp thụ vào task hiện có: xác định owner
gần nhất, ghi rõ phạm vi hấp thụ, tính lại Local Risk / Blast Radius /
Effective Risk, đánh giá tác động Completion Gate / review depth / repair
budget, so sánh với vertical acceptance slice của capability.

Absorption tự động chỉ được phép vào một task đã có scope baseline được
Owner phê duyệt/frozen. Nếu chưa có baseline đó (ví dụ một task mới được
Owner cấp ID nhưng chưa có Scope Lock): KHÔNG hấp thụ tự động — ghi
`OWNER_ASSIGNMENT_REQUIRED` với `absorption_status =
DEFERRED_UNTIL_<TASK_ID>_SCOPE_APPROVED`.

Sau khi có baseline, absorption tự động PHẢI DỪNG nếu MỘT trong các điều
sau đúng:

- **A. RISK ESCALATION** — Effective Risk tăng ≥ 1 bậc governance vì việc
  hấp thụ.
- **B. ITEM COUNT** — hơn BA hạng mục mới được hấp thụ vào cùng một task kể
  từ baseline được approve/frozen.
- **C. COMPLETION GATE EXPANSION** — số check REQUIRED của Completion Gate
  tăng > 50% so với baseline.
- **D. VERTICAL-SLICE CLASSIFICATION DISPUTE** — một hạng mục đã được xếp
  loại NGOÀI vertical acceptance slice nhưng vẫn bị đề xuất hấp thụ NHƯ THỂ
  nó nằm trên critical path.

Khi kích hoạt: ghi `ABSORPTION_LIMIT_REACHED`, dừng hấp thụ tự động, escalate
Owner để chọn: (A) chấp nhận scope/risk mở rộng, (B) descope/defer về
hardening/backlog, hoặc (C) approve một task mới theo §16.3 (không tự động
chọn nhánh này).

### 16.7 Module ≠ Task

Phân rã kiến trúc (resolver, handler, adapter, orchestration component,
persistence/validation helper, v.v.) KHÔNG mặc nhiên là phân rã governance.
Mặc định biểu diễn dưới dạng module/subtask/work package/hardening/finding/
acceptance criterion — không phải task anh em, trừ khi thoả §16.3.

### 16.8 Finding Routing

Finding từ review KHÔNG tự động tạo task:

- **BLOCKING** → route tới owner capability gần nhất, trừ khi thật sự nằm
  ngoài toàn bộ capability.
- **HARDENING** → giữ nguyên dưới owner hiện có, kèm re-trigger tường minh.
- **OUT_OF_SCOPE** → route tới owner capability gần nhất — KHÔNG phải task
  mới.

Nếu không xác định được owner: ghi `OWNER_ASSIGNMENT_REQUIRED` (§16.5) —
không tạo artifact riêng chỉ để giữ một finding.

### 16.9 Capability-Level Repair Budget Semantics

Review budget hiện hành (`V4.1` §2) gắn với **ROOT TASK LINEAGE**. Việc
nhóm nhiều root task thành một capability (ví dụ để lập kế hoạch, báo cáo)
KHÔNG tự động tạo capacity Repair Cycle mới, và KHÔNG tự động gộp ngân sách
của các root task riêng lẻ. Bất kỳ đề xuất "capability repair ceiling" nào
chỉ có hiệu lực sau khi Owner ADOPT tường minh một migration; cho tới lúc
đó, ledger per-root-task hiện hành vẫn là authoritative duy nhất.

### 16.10 Migration Transition Rule

Trong lúc `migration_status ≠ ADOPTED`: KHÔNG task nào trong capability
(mới hay hiện có) được cấp Repair Cycle budget mới chỉ vì được nhóm lại
theo capability. TASK CREATION APPROVAL và REPAIR-BUDGET ALLOCATION
APPROVAL là hai quyết định tách biệt — approve task mới tồn tại không tự
động approve ngân sách repair mới cho nó.

## Tương thích ngược

Đề xuất này không sửa đổi bất kỳ điều khoản nào hiện có của
`governance/core/V4_1_POLICY_FREEZE.md` §1–§15; nó chỉ thêm §16 mới. Không frozen gate,
không ledger per-task hiện hành nào bị viết lại bởi đề xuất này.

## Trạng thái persistence

- CORE (`governance/core/V4_1_POLICY_FREEZE.md`): CHƯA sửa — proposal này
  là artifact độc lập, chờ phiên có CORE-amendment authority.
- PROJECT: các mục ứng dụng cụ thể cho `CAP-PRICE-RESOLUTION` được ghi tại
  `PROJECT/PROJECT_PROGRESS.md`, `PROJECT/PROJECT_DECISIONS.md` (`DEC-160`),
  `PROJECT/REVIEW_BUDGET_LEDGER.md` — không trùng lặp nội dung CORE ở trên.
