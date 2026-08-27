# Governance V4.1 — Policy Freeze (Adoption Overlay)

Trạng thái tại thời điểm ghi file này:

```
V4.1 = POLICY_ADOPTED
V4.1 = NOT YET FULLY_ENFORCED
```

Đây là **overlay chính sách**, không phải bản viết lại governance hiện có.
Nó KHÔNG thay thế `CLAUDE.md`, không thay thế `governance/core/*`, không
thay thế `RULE_PRECEDENCE.md`. Nó ghi lại các luật/ngân sách/ngưỡng mà
Owner đã phê duyệt cho `TASK-V4-ADOPTION` (session V4.1-0), để các session
sau đọc được trạng thái đã freeze mà không phải suy luận lại từ prose rải
rác.

Được tạo bởi: `TASK-V4-ADOPTION`, session V4.1-0 (2026-08-27).
Machine control đi kèm: `scripts/branch_authority_check.sh`,
`PROJECT/REVIEW_BUDGET_LEDGER.md`.

## 1. Phân biệt hai trạng thái adoption

**POLICY_ADOPTED** đạt được khi:
- V4.1 policy đã freeze (file này);
- entry-point overlay hoạt động;
- branch authority machine control tồn tại và chạy được
  (`scripts/branch_authority_check.sh`);
- review budget ledger tồn tại (`PROJECT/REVIEW_BUDGET_LEDGER.md`);
- trạng thái transition của TASK-110 = `EXHAUSTED_PRE_V4.1`;
- không có production code nào bị thay đổi trong session adoption;
- ngân sách adoption không vượt quá 1 blocking repair cycle.

**FULLY_ENFORCED** chỉ đạt được khi, thêm vào trên:
- có Golden fixture;
- có deterministic expected output;
- có one-command Golden diff;
- test suite tests/test_golden_baseline.py (chưa tồn tại; tạo tại
  `TASK-GOLDEN-BASELINE-001`, không tạo trong session adoption này) PASS.

Hai trạng thái này KHÔNG được đánh đồng. `TASK-GOLDEN-BASELINE-001` là task
duy nhất được phép nâng V4.1 lên `FULLY_ENFORCED`.

## 2. Review Budget — bảng ngân sách đã freeze

```
LOW              = 1 blocking repair cycle
MEDIUM           = 1 blocking repair cycle
HIGH / CRITICAL  = 2 blocking repair cycles
```

Không tồn tại `HIGH = 3`. Owner được phép đặt ngân sách thấp hơn bảng này
cho một root task cụ thể. Vượt ngân sách → `OWNER_EXTENSION REQUIRED`.

Ngân sách gắn với **ROOT TASK LINEAGE**, không gắn với từng review hay từng
sub-unit. Sub-unit không có ngân sách riêng, không reset ngân sách, và
không được tạo lineage mới (đổi tên, tách nhánh, mở "V4.1-R1", v.v.) chỉ để
reset ngân sách.

Trạng thái sống của ngân sách theo từng root task: xem
`PROJECT/REVIEW_BUDGET_LEDGER.md` — đó là nguồn sự thật vận hành (operational
source of truth), file này chỉ ghi lại luật.

## 3. Repair Cycle — tính theo cumulative repair diff

Cycle được tính theo **LẦN SỬA**, không theo số review. Reviewer phải trả
toàn bộ BLOCKING findings đã biết trong một lượt.

Mọi BLOCKING defect nằm trong code, test, helper, parser, governance, hay
artifact — do chính repair cycle hiện tại TẠO hoặc SỬA — là defect của
CÙNG repair cycle đó, không mở cycle mới.

"Vùng code mới" chỉ có thể mở cycle mới khi vùng đó nằm ngoài CUMULATIVE
REPAIR DIFF của mọi repair đang thuộc cycle hiện tại.

Ledger phải ghi:

```
cycles:
    - id: <cycle-id>
      base_sha: <SHA trước repair>
      head_sha: <SHA sau repair>
```

Xác định phạm vi bằng `git diff <base_sha>..<head_sha> --name-only`. Nếu
repair tiếp tục trong cùng cycle, `head_sha` tiến lên SHA mới; `base_sha`
không reset. Không dùng session mới / sub-unit mới / branch mới để reset
`base_sha`.

## 4. Blast Radius — chấm theo failure path, không chấm theo tên file

TUYỆT ĐỐI không chấm risk theo tên module/file (không được viết
"canonical.py = LOW", "framework = LOW", "helper = LOW").

Blast Radius được chấm theo ĐƯỜNG DỮ LIỆU / FAILURE PATH thực tế. Một lỗi
dẫn tới chọn sai employee, sai conversion, sai KPI, hay sai tiền
thưởng/lương có thể là HIGH dù nằm trong helper/framework.

```
Effective Risk = max(Local Risk, Blast Radius của failure path)
```

Không dùng dependency/import graph làm proxy cho blast radius.

### 4.1 Golden Baseline không tự động hạ risk

Blast Radius chỉ được hạ tối đa MỘT bậc khi có một GOLDEN TEST CỤ THỂ phủ
đúng failure path đang xét — phải nêu được tên test, fixture, path nghiệp
vụ được phủ, và expected output. Không được nói "Golden Baseline tồn tại
nên module này an toàn" mà không chỉ ra test cụ thể.

Trước khi `TASK-GOLDEN-BASELINE-001` hoàn tất: KHÔNG CÓ Golden test nào
được phép dùng để hạ Blast Radius.

## 5. Production Path Decision Rule

Một input chỉ được coi là CURRENT PRODUCTION-REALISTIC khi dựng được từ ít
nhất một trong bốn nguồn:

1. production annotation/schema inventory hiện tại;
2. config hiện hành trong repo;
3. Golden Baseline fixture đã tồn tại;
4. raw production data đã được xác minh.

Không dựng được từ 1–4 → HARDENING BY DEFAULT. Muốn nâng thành BLOCKING,
reviewer phải chỉ ra nguồn production thứ năm cụ thể, chứng minh path, và
được Owner chấp thuận. Các câu như "có thể xảy ra", "Python cho phép", "tôi
dựng được object", "một thư viện tương lai có thể…" KHÔNG được coi là bằng
chứng production path.

## 6. Phạm vi đúng của Golden Baseline

Golden Baseline là lưới an toàn REGRESSION NGHIỆP VỤ chính. Nó KHÔNG chứng
minh logic mới đúng, KHÔNG chứng minh baseline vốn đúng, KHÔNG thay thế
exploratory review, và KHÔNG cấm reviewer tìm attack mới.

Golden bắt: "hôm nay khác output đã được xác minh". Golden KHÔNG tự bắt:
"baseline và implementation mới cùng sai". Không dùng các claim định lượng
kiểu "Golden thay 70% adversarial review".

## 7. Review Finding Action Gate

Discovery budget không bị hạn chế bởi repair budget — khuyến khích reviewer
tìm attack mới. Nhưng mỗi finding phải được phân loại:

- **BLOCKING** — có production path hiện tại (theo §5) + tác động
  correctness/data/business/safety.
- **HARDENING** — không có production path hiện tại, hoặc chỉ là
  robustness tương lai. Mỗi HB-xxx phải có RE-TRIGGER CONDITION cụ thể
  (gắn với cơ chế/test/inventory check khi khả thi, không chỉ ghi lời hứa
  trong prose).
- **OUT_OF_SCOPE** — không thuộc contract của task.

Attack mới sau frozen corpus KHÔNG tự động làm task FAIL. Finding BLOCKING
phải chỉ ra tiêu chí production đã freeze (§5) bị vi phạm.

## 8. Branch Divergence Limit

`INTEGRATION_DECISION_REQUIRED` nếu bất kỳ điều kiện nào đúng:

```
ahead > 10 commits
OR divergence > 3 ngày
OR cumulative changed LOC > 5,000
```

Owner phải chọn: (A) integrate/merge sớm; (B) cắt scope; (C) tiếp tục
divergence có lý do + review date. Không được tiếp tục im lặng.

## 9. Merge Gate Timeout

Merge gate BLOCKED quá 30 ngày → `OWNER DECISION REQUIRED`. Owner phải
chọn: (A) cung cấp dependency/data; (B) đổi thành
`POST_MERGE_PRODUCTION_ACCEPTANCE`; (C) gỡ khỏi gate set. Không có "tiếp
tục BLOCKED vô thời hạn".

## 10. Artifact Budget

Không retro-fit/xoá tài liệu governance lịch sử — tài liệu hiện có giữ
nguyên như historical artifacts trừ khi có task riêng.

Artifact governance thứ 5+ của một root task: `OWNER APPROVAL REQUIRED`
trong MỌI trường hợp. Legal/security/compliance chỉ là lý do đề xuất,
không tự cấp quyền.

## 11. Artifact Internal Precedence

Tên chính thức: **ARTIFACT INTERNAL PRECEDENCE**. Không thay thế
`RULE_PRECEDENCE.md` hiện có — `RULE_PRECEDENCE.md` xử lý ưu tiên giữa
Safety/Data Integrity/... theo governance cũ; Artifact Internal Precedence
xử lý xung đột BÊN TRONG cùng một artifact.

Trong cùng một artifact: normative ID table / enum / machine-readable rule
> prose explanation. Nếu xung đột: phần quy phạm thắng, nhưng divergence
phải được báo cáo và sửa bằng authority hợp lệ.

## 12. State Authority Matrix

```
READY_FOR_REVIEW        → implementation agent
PASS — ELIGIBLE_FOR_FREEZE → independent reviewer
FROZEN                  → authorized Freeze Finalization session
BLOCKED                  → agent/reviewer, phải chỉ rõ gate
SUPERSEDED               → Owner / authorized governance action
ACCEPT_AS_IS              → OWNER ONLY
DESCOPE                   → OWNER ONLY
DONE                      → Owner / completion authority
```

Reviewer read-only KHÔNG được ghi `FROZEN` vào repo.

## 13. Rollout Order

```
V4.1-0  POLICY ADOPTION                              (session này)
V4.1-1  FINAL R1-A1 INDEPENDENT REVIEW
        + FREEZE FINALIZATION nếu PASS
        + INTEGRATION DECISION ngay sau đó
        (CHECK-110-16 vẫn là merge gate — không bypass)
V4.1-2  TASK-GOLDEN-BASELINE-001 trên integration baseline chính thức
V4.1-3  APPLY V4.1 PROSPECTIVELY
V4.1-4  PILOT TASK-111 / excel_exporter (nếu roadmap hiện hành xác nhận)
```

V4.1 adoption KHÔNG mở cleanup epic: không rewrite governance cũ, không
rename hàng loạt file, không migrate artifact lịch sử, không xoá
Constitution cũ hay repair artifact, không "làm sạch repo" ngoài touch
area, không sửa TASK-110 code/canonical.py/R1-A1 oracle/business logic.

## 14. Owner Decision — Transition (đã freeze tại V4.1-0)

1. `TASK-110` budget = `EXHAUSTED_PRE_V4.1`.
2. R1-A2 → R8 không tự có budget — cần `OWNER_EXTENSION` riêng cho từng unit.
3. HIGH/CRITICAL max = 2 blocking repair cycles.
4. Cycle tính theo cumulative repair diff (§3).
5. Blast Radius tính theo failure path, không theo tên file (§4).
6. Golden chỉ hạ risk khi có test cụ thể phủ đúng path (§4.1).
7. Production-realistic input theo bốn nguồn hữu hạn (§5).
8. Divergence threshold = 10 commits / 3 ngày / 5.000 LOC (§8).
9. Merge gate timeout = 30 ngày (§9).
10. `ACCEPT_AS_IS`/`DESCOPE` = Owner only (§12).
11. `POLICY_ADOPTED` != `FULLY_ENFORCED` (§1).

Chi tiết đầy đủ của Owner Decision này (bối cảnh, evidence, tham chiếu
session) được ghi trong `PROJECT/PROJECT_DECISIONS.md`.

## 15. Tham chiếu vận hành

- Ngân sách sống theo root task: `PROJECT/REVIEW_BUDGET_LEDGER.md`.
- Branch authority: `scripts/branch_authority_check.sh`.
- Điểm vào governance chính: `CLAUDE.md`.
- Ưu tiên luật liên-artifact: `governance/core/RULE_PRECEDENCE.md`.
