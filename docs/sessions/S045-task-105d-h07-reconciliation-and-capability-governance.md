# S045 — TASK-105D H-07 Gate Execution Reconciliation + Capability-First Delivery Governance Reconciliation

Session Type:
GOVERNANCE / DOCUMENTATION RECONCILIATION — hai mục tiêu độc lập trong một
phiên. **Không** phải phiên implementation, **không** phải phiên repair,
**không** phải phiên review độc lập mới, **không** phải phiên completion.

Date:
2026-08-28

Current Task Mode:
MAJOR

Selected Profile:
PRODUCT

Risk:
Effective Risk HIGH (kế thừa từ `TASK-105D`, Local Risk 4 / Blast Radius 5).
Phiên này không sửa `app/**`/`tests/**`/`config/**` nên không tự phát sinh
risk mới, nhưng quyết định Owner ghi ở đây có hệ quả trực tiếp tới điều kiện
`DONE` của `TASK-105D`.

Evidence Level:
E2 — mọi tuyên bố hash/count/validator dưới đây được đo lại trực tiếp trong
phiên này, không kế thừa mù từ Final Report của phiên trước.

Executed By:
phiên H-07 Reconciliation + Capability Governance (S045)

Timestamp:
2026-08-28

Branch:
`governance/task-105d-gate-execution-reconciliation`

Authority:
Owner Decision — chỉ thị mở phiên này nêu tường minh "Owner preferred Option
(b)" cho `H-07` và đặt toàn bộ khung Capability-First Delivery Governance
(§B1–B16 của brief). Theo tiền lệ `DEC-156`/`DEC-157`/`DEC-158`, chỉ thị mở
phiên chính là `OWNER APPROVAL` cho artifact governance thứ 5+ của lineage
`TASK-105D` (`V4.1` §10). `V4.1` §12 (state authority): phiên này có
**gate-interpretation / Owner-Decision-recording authority** do Owner uỷ
quyền trực tiếp trong chỉ thị mở phiên; phiên **không** có completion
authority (không đánh dấu `DONE`) và **không** có thẩm quyền sửa
`governance/scripts/governance/*.py` hay bất kỳ file `app/**`/`tests/**`.

## 0. Pre-flight

```text
$ git branch --show-current
governance/task-105d-gate-execution-reconciliation

$ git rev-parse HEAD
7464ccaa784f13d887b2d5441d86136ff7d9a61d

$ git remote show origin | grep 'HEAD branch'
HEAD branch: claude/extract-upload-repo-gq2ws4

$ git rev-parse origin/claude/extract-upload-repo-gq2ws4
7464ccaa784f13d887b2d5441d86136ff7d9a61d        <-- KHỚP HEAD

$ git status --porcelain
(rỗng — worktree CLEAN)

$ scripts/branch_authority_check.sh
DEFAULT_BRANCH   : claude/extract-upload-repo-gq2ws4
DEFAULT_TIP      : 7464ccaa784f13d887b2d5441d86136ff7d9a61d
HEAD_SHA         : 7464ccaa784f13d887b2d5441d86136ff7d9a61d
WORKTREE         : CLEAN
AUTHORITY        : BRANCH_WITH_UPSTREAM
RESULT           : AUTHORITY_OK
```

Ghi chú đối chiếu brief: brief liệt kê "EXPECTED BASE / DEFAULT =
7464ccaa784f13d887b2d5441d86136ff7d9a61d" như một giá trị đơn — giá trị này
khớp cả với `HEAD` cục bộ **và** tip của nhánh mặc định thật trên origin
(`claude/extract-upload-repo-gq2ws4`, xác nhận bằng `git remote show origin`
→ "HEAD branch", đúng giao thức `CLAUDE.md` → "Đồng Bộ Nhánh"). SessionStart
hook cảnh báo lệch **tên nhánh** (session đứng trên
`governance/task-105d-gate-execution-reconciliation`, không phải tên nhánh
mặc định) nhưng đồng thời báo `behind = 0` / `ahead = 0` — tức không có phân
kỳ SHA thật. Đây là tình huống bình thường của một session đang mở một
task-branch mới từ đúng tip mặc định, không phải một STOP condition. Tiếp
tục.

DEC ID scan trước khi cấp (tiền lệ `DEC-158`, đã quét MỌI ref):

```text
$ for b in $(git for-each-ref --format='%(refname:short)' refs/remotes/origin/); do
    git show "$b:PROJECT/PROJECT_DECISIONS.md" 2>/dev/null | grep -E '^## DEC-(159|160)\b'
  done
(rỗng trên MỌI branch — DEC-159, DEC-160 trống trước khi cấp)

$ for b in $(git for-each-ref --format='%(refname:short)' refs/remotes/origin/); do
    git show "$b:docs/sessions" 2>/dev/null | grep -oE '^S0(4[5-9]|[5-9][0-9])'
  done | sort -u
(rỗng trên MỌI branch — S045 trống trước khi cấp)
```

---

# PHẦN A — TASK-105D H-07 GATE EXECUTION RECONCILIATION

## A1. Xác minh độc lập các sự kiện H-07

Toàn bộ số đo dưới đây được tái lập trực tiếp trong phiên này, không kế thừa
lời kể của Final Report trước.

```text
$ sed -n '631,2359p' docs/tasks/TASK-105D-product-identity-resolver.md | sha256sum
0444e58c02b04804a116c140af722ffc29ea64adf468aa6c93794c4408a5c877   <-- KHỚP

$ sed -n '631,2359p' docs/tasks/TASK-105D-product-identity-resolver.md | grep -c '^#### CHECK-105D-'
32

$ sed -n '631,2359p' docs/tasks/TASK-105D-product-identity-resolver.md | grep -A1 '^Status:$' | grep -c 'NOT_TESTED'
32
```

Kết luận đo (A):

```text
A. Frozen Completion Gate chứa đúng 32 REQUIRED check          : ĐÚNG
B. 32 trường Status: nhúng trong khối gate                     : NOT_TESTED (32/32)
C. GATE_SET_SHA256 = 0444e58c02b04804a116c140af722ffc29ea64adf468aa6c93794c4408a5c877 : ĐÚNG
D. TASK-105D-GATE-EXECUTION-RECORD.md báo 32/32 PASS            : ĐÚNG
   (E2, executed by S040, bound tới đúng GATE_SET_SHA256 tái lập trong
    chính file đó)
E. Independent Implementation Review #2 độc lập xác nhận 32/32 PASS : ĐÚNG
   (thực thi lại tại a0982350, §17.2 của
    docs/reviews/TASK-105D-INDEPENDENT-IMPLEMENTATION-REVIEW-2.md)
F. Controlled Integration (S044) bảo toàn:
   - frozen gate byte identity                                 : ĐÚNG (hash TRƯỚC = SAU)
   - B-01 CLOSED                                                : ĐÚNG (10/10, Review #2)
   - RC-1 lineage                                                : ĐÚNG (5 object, ancestor-verified)
   - bằng chứng thực thi tách rời                                : ĐÚNG (2 file, không hợp nhất vào khối gate)
   - H-07 OPEN                                                    : ĐÚNG
   - TASK-105D NOT DONE                                           : ĐÚNG
```

Một điểm cần làm rõ literal: brief liệt kê `GATE_SET_SHA256` với tiền tố
`04...4408a5c877` (65 ký tự nếu đếm nguyên văn khối brief — dư một ký tự so
với độ dài SHA-256 chuẩn 64 hex). Giá trị 64-hex thực tế, tái lập được, xuất
hiện đồng nhất trên **mọi** artifact canonical (freeze review, cả hai
Independent Review, RC-1 record, Gate Execution Record, S040-S044, DEC-158)
là:

```text
0444e58c02b04804a116c140af722ffc29ea64adf468aa6c93794c4408a5c877
```

Phiên này dùng giá trị 64-hex canonical này làm tham chiếu chính thức cho
toàn bộ phần A — không phải một hash khác, không phải một sai khác thực chất.

Nguồn tổng hợp đầy đủ 10 artifact (freeze review, cả hai Independent Review,
RC-1 repair record, Gate Execution Record, S040–S044): xem Phụ lục A-1 (§A11)
bên dưới cho bảng đối chiếu SHA-per-file.

## A2. Xung đột governance cần giải quyết

Hai văn bản canonical căng nhau, đúng như `H-07` xác định lần đầu (Independent
Review #1 §2.1) và được thảo luận đầy đủ ở Independent Review #2 §23:

```text
Văn bản 1 — governance/core/TASK_COMPLETION_GATE_STANDARD.md (dòng 75):
  "Bất kỳ REQUIRED check nào là FAIL, BLOCKED, hoặc NOT_TESTED đều ngăn task
   đạt DONE, trừ khi được đánh dấu rõ ràng là NOT_APPLICABLE kèm lý do hợp lệ."

Văn bản 2 — khối freeze trong chính task file (dòng 508 vùng, S038):
  "Thay đổi gate sau thời điểm này — bất kỳ sửa đổi nào làm đổi
   GATE_SET_SHA256 — cần một COMPLETION GATE CHANGE PROPOSAL mới + authority
   ... Không sửa tại chỗ." + "Việc chuyển NOT_TESTED → PASS thuộc phiên
   implementation."
```

Đọc kỹ `governance/core/TASK_COMPLETION_GATE_STANDARD.md` toàn văn (150 dòng, đọc lại trong
phiên này):

```text
- Rule cốt lõi (dòng 6-12): CODE COMPLETE ≠ TASK COMPLETE; DONE cần mọi
  REQUIRED check PASS + evidence level + Exit Criteria.
- Evidence Record fields (dòng 84-106): mỗi check cần Check ID / Priority /
  Status / Evidence Level / Evidence / Executed By / Timestamp — KHÔNG quy
  định các field này phải NẰM VẬT LÝ bên trong khối check đã hash-freeze.
- Cụm từ "Gate Execution Record" KHÔNG xuất hiện trong toàn bộ governance/ —
  đây là quy ước riêng do TASK-105D lineage (S040) tự đặt ra, suy luận từ
  chính điều khoản Change Control của standard này, KHÔNG phải một khái
  niệm standard đã định nghĩa sẵn.
- "Kiểm soát thay đổi Gate" (dòng 129-149): mẫu COMPLETION GATE CHANGE
  PROPOSAL áp dụng cho thay đổi ĐỊNH NGHĨA check (Original check / Proposed
  change / Reason / Risk / Impact) — không có điều khoản nào nói việc GHI
  NHẬN kết quả thực thi (không đổi định nghĩa) phải đi qua cùng thủ tục đó.
```

Kết luận đọc văn bản: `governance/core/TASK_COMPLETION_GATE_STANDARD.md` **im lặng** về việc
Evidence Record của một check REQUIRED có bắt buộc nằm vật lý bên trong khối
đã hash-freeze hay không. Đây **không** phải một điều cấm tường minh —
brief `§A3` cấm áp Option (b) "nếu canonical governance cấm tường minh"; ở
đây không có lệnh cấm tường minh, chỉ có một khoảng trống diễn giải. Nếu đọc
"REQUIRED check ... NOT_TESTED" theo nghĩa hẹp nhất (chỉ trường `Status:`
nhúng trong khối hash-freeze mới là "check status" hợp lệ), `DONE` sẽ **vĩnh
viễn không thể đạt được** cho bất kỳ gate nào từng freeze theo mô hình
byte-identity này, kể cả khi mọi check đã PASS thật — điều này mâu thuẫn với
chính mục đích "freeze định nghĩa, không đóng băng khả năng hoàn thành" mà
`governance/core/TASK_COMPLETION_GATE_STANDARD.md` và `V4.1` §12 (`DONE → Owner / completion
authority`) cùng giả định.

## A3–A4. Owner Option (b) — Authority Analysis

Owner ưu tiên Option (b): giữ khối gate byte-identical, KHÔNG mutate 32
trường `Status:`, công nhận `docs/reviews/TASK-105D-GATE-EXECUTION-RECORD.md` (+ bằng
chứng tái lập độc lập của Independent Review #2 §17.2) là bằng chứng
execution-result authoritative.

**Kết luận authority: Option (b) ĐƯỢC PHÉP, không cần Option (c) (standard
amendment).** Lý do:

```text
1. TASK_COMPLETION_GATE_STANDARD.md KHÔNG tường minh yêu cầu Evidence Record
   phải nằm vật lý trong khối gate đã hash-freeze (§A2).
2. Điều khoản duy nhất ràng buộc "sửa gate cần Change Proposal" nói về sửa
   ĐỊNH NGHĨA (đổi GATE_SET_SHA256) — Option (b) không đổi định nghĩa,
   không đổi GATE_SET_SHA256 (xác nhận lại ở §A5).
3. V4.1 §12 trao quyền "DONE → Owner / completion authority". Phiên này
   không tự tuyên DONE (bị cấm rõ ở §C của brief); phiên chỉ ghi nhận một
   Owner Decision xác định ĐIỀU KIỆN nào thoả mãn yêu cầu PASS của standard
   cho lineage TASK-105D — đúng phạm vi quyền mà §12 trao cho Owner.
4. RULE_PRECEDENCE.md cấm "tự ý giải quyết xung đột quan trọng một cách âm
   thầm" — phiên này KHÔNG áp Option (b) ngầm; nó được ghi tường minh thành
   DEC-159 dưới đây, với đầy đủ lý do, đúng format brief §A2 yêu cầu.
```

⇒ **KHÔNG mở Option (c)** (không sửa `governance/core/TASK_COMPLETION_GATE_STANDARD.md`).
Việc này khác quan trọng với quyết định ở PHẦN B (nơi CORE amendment cũng bị
hoãn — nhưng vì lý do khác: thiếu CORE authority, không phải vì standard đã
cho phép diễn giải).

### DEC-159 — Owner Decision (được ghi canonical tại `PROJECT/PROJECT_DECISIONS.md`)

```text
Owner Decision: "Effective Completion Status" của một REQUIRED check ở
TASK-105D = Status trong bản ghi thực thi tách rời (Gate Execution Record +
Independent Review xác nhận), KHÔNG bắt buộc trùng vật lý với trường Status:
nhúng trong khối gate đã hash-freeze, MIỄN LÀ cả 8 điều kiện ràng buộc của
§A6/A7 dưới đây được thoả mãn. "Frozen Gate Status" (NOT_TESTED, 32/32) tiếp
tục là metadata tại thời điểm freeze — vĩnh viễn KHÔNG đổi cho gate này
theo thiết kế.
```

## A5. Không mutate frozen gate

```text
GATE_SET_SHA256 TRƯỚC phiên này : 0444e58c02b04804a116c140af722ffc29ea64adf468aa6c93794c4408a5c877
GATE_SET_SHA256 SAU phiên này   : 0444e58c02b04804a116c140af722ffc29ea64adf468aa6c93794c4408a5c877
$ git diff HEAD -- docs/tasks/TASK-105D-product-identity-resolver.md
(rỗng — phiên này không chạm file này)
```

Không có `COMPLETION GATE CHANGE PROPOSAL` nào được mở cho `TASK-105D` trong
phiên này — đúng ràng buộc §A5 của brief.

## A6. Kiểm tra binding của Gate Execution Record

`docs/reviews/TASK-105D-GATE-EXECUTION-RECORD.md` được đối chiếu lại:

```text
bound tới TASK-105D                          : CÓ (tiêu đề + §0 metadata)
bound tới đúng GATE_SET_SHA256               : CÓ (tái lập trong chính file, §0/§1)
bound tới đúng 32 CHECK-105D-01..32           : CÓ (bảng §3, từng ID riêng)
PASS/FAIL từng check                          : CÓ (32 PASS, 0 FAIL, 0 NOT_TESTED)
Evidence Level                                : CÓ (E2=19, E1=13 — đúng phân bổ freeze)
Executed By / Timestamp                       : CÓ (S040, 2026-08-28)
implementation/RC-1/review lineage             : CÓ, xác nhận CHÉO qua 3 nguồn độc lập:
     - S040 (thực thi gốc, base 222844df, target e6252c06)
     - Independent Review #1 (S041, tái lập tại e6252c06 — TRƯỚC repair)
     - Independent Review #2 (S043, tái lập tại a0982350 — SAU RC-1)
   Cả ba lần đếm cho ra CÙNG một số: 32/32 PASS, cùng phân bổ Evidence Level.
```

⇒ **Binding hoàn chỉnh** — không thể vô tình áp bằng chứng này cho một phiên
bản gate khác (mọi lần tái lập hash đều khớp tuyệt đối với đúng
`GATE_SET_SHA256` này, không phải một giá trị lân cận).

## A7. Điều kiện đóng H-07 — kiểm từng điều kiện

```text
1. Canonical governance cho phép mô hình hai lớp                : ĐẠT (§A3/A4 —
   Owner Decision DEC-159, KHÔNG cần sửa standard)
2. Execution record bind đúng frozen hash                        : ĐẠT (§A6)
3. Cả 32 REQUIRED check có authoritative PASS evidence            : ĐẠT (§A1/A6,
   3 lần đo độc lập cho cùng kết quả)
4. Independent Review #2 xác nhận 32/32                           : ĐẠT (§17.2 của
   review, tái lập trong phiên này qua §A1)
5. Frozen gate bytes không đổi                                    : ĐẠT (§A5)
6. Không còn mơ hồ giữa frozen NOT_TESTED và effective execution   : ĐẠT SAU
   DEC-159 — "Frozen Gate Status" và "Effective Completion Status" nay là
   hai khái niệm tường minh, tách biệt, ghi canonical.
7. Completion validator/state logic xác định được effective        : **KHÔNG ĐẠT**
   completion state mà không đòi mutate frozen history             — xem chi tiết
   ngay dưới đây. Đây là điều brief §A7 yêu cầu "pay special attention".
```

### A7.7 — Xung đột validator thật, đo trực tiếp trong phiên này

```text
$ python3 governance/scripts/governance/validate_task_completion.py
TASK COMPLETION: PASS
Checked 6 DONE task(s).
```

Validator hiện PASS vì `TASK-105D` **chưa** có `Status: DONE` ở top-level
(vẫn `READY` — xem thảo luận §A9 dưới). Đọc mã nguồn
`governance/scripts/governance/validate_task_completion.py` (150 dòng, đọc
toàn bộ trong phiên này):

```python
# dòng 18-22
status_match = re.search(r"(?mi)^\s*Status:\s*(?:\n\s*)?([A-Z_]+)\s*$", txt)
status = status_match.group(1).strip() if status_match else None
if status != "DONE":
    continue
```

Validator chỉ kích hoạt kiểm tra khối REQUIRED khi top-level `Status: DONE`.
Khi kích hoạt (dòng 47-72), nó đòi **literal**:

```python
st = re.search(
    r"(?mi)^\s*Status:\s*(NOT_TESTED|PASS|FAIL|BLOCKED|NOT_APPLICABLE)\s*$",
    block,
)
state = st.group(1)
if state != "PASS":
    errors.append(f"... DONE task contains REQUIRED check '{check_name}' with Status={state}.")
```

Validator **không có bất kỳ khái niệm nào** về một Gate Execution Record
tách rời — nó chỉ grep trường `Status:` nhúng vật lý trong khối
`#### CHECK-*`. Theo mô hình hai lớp vừa được DEC-159 công nhận, 32 trường
đó được **thiết kế để giữ nguyên `NOT_TESTED` vĩnh viễn** (mutate chúng sẽ
đổi `GATE_SET_SHA256`, đúng điều Option (b) cố tránh). Hệ quả: **nếu một
phiên tương lai đặt `TASK-105D` top-level `Status: DONE` trong khi 32 khối
vẫn `NOT_TESTED`, `validate_task_completion.py` sẽ FAIL cả 32 REQUIRED
check**, bất kể `DEC-159` nói gì.

`validate_evidence.py` cũng được đọc toàn bộ (52 dòng) — nó chỉ kiểm E1/E2
completeness cho các khối `Status: PASS`; nó **im lặng bỏ qua** khối
`NOT_TESTED` (dòng 25-26: `if not st or st.group(1) != "PASS": continue`).
Không validator nào trong `governance/scripts/governance/` đọc
`docs/reviews/TASK-105D-GATE-EXECUTION-RECORD.md`.

**Kết luận — theo đúng chỉ dẫn brief "DO NOT fake closure. Report the exact
conflict":**

```text
Điều kiện #7 KHÔNG thoả. Có một xung đột cơ học thật, không phải diễn giải,
giữa ngữ nghĩa vừa được Owner công nhận (DEC-159) và hành vi hiện tại của
validate_task_completion.py. Đây là một khoảng trống tooling, không phải
một lỗi trong lý luận diễn giải ở §A2-A4.
```

## A8–A9. H-07 disposition & tình trạng còn lại

```text
H-07 = PARTIALLY RECONCILED

  Lớp diễn giải/thẩm quyền governance  : RESOLVED (DEC-159, Option (b),
                                          GATE_SET_SHA256 không đổi)
  Lớp tương thích validator (điều kiện #7) : OPEN — MỚI, phạm vi hẹp,
                                          re-trigger = "TRƯỚC khi bất kỳ
                                          phiên nào đặt TASK-105D top-level
                                          Status: DONE"

H-07 CLOSED?  KHÔNG — một trong bảy điều kiện đóng (§A7) không thoả, và
brief cấm "fake closure".
```

Phiên này **không** sửa `governance/scripts/governance/validate_task_completion.py`
— đây là thay đổi tooling nằm ngoài phạm vi "governance/documentation
reconciliation" của phiên (brief §F: "Do NOT modify validator logic...
If such a validator change would touch production/tooling scope beyond this
session: STOP and report it."). Báo cáo đúng theo yêu cầu đó thay vì tự sửa.

Rà lại 15 finding còn mở (nguồn: bảng dispositions của S044, đối chiếu lại
với văn bản gốc từng review):

| ID | Trạng thái | Risk | Re-trigger | Chặn DONE ngay bây giờ? | Chặn activation/use sau này? |
|---|---|---|---|---|---|
| H-01 | OPEN | HARDENING | phiên sửa data contract có thẩm quyền hoặc implementation chạm `confirmation_action` authority semantics | KHÔNG | CÓ — trước khi coi tập đếm là tập thẩm quyền trong production |
| H-02 | OPEN (contract-level) | HARDENING | phiên có thẩm quyền data contract (`ranking_method_id`) | KHÔNG | CÓ — trước khi TASK-105E/108B dựa vào `evidence_fingerprint` |
| H-03 | OPEN | HARDENING | phiên tiếp theo chạm Gate Execution Record | KHÔNG (không ảnh hưởng PASS validity, chỉ con trỏ evidence) | Nên sửa trước khi một phiên DONE đọc lại record này làm evidence |
| H-04 | OPEN | HARDENING | phiên chạm hiệu năng `rebuild_index()` / bulk import quy mô lớn | KHÔNG | CÓ — trước production bulk-scale |
| H-05 (data contract, `ranking_method_id`) | OPEN | HARDENING | phiên sửa data contract có thẩm quyền hoặc chạm `RejectedCandidate`/ranking | KHÔNG | CÓ — trước TASK-105E compose trên vùng này |
| H-06 | OPEN | HARDENING | phiên làm migration/rollback | KHÔNG | CÓ — trước khi migration schema chạy trên production |
| H-07 | PARTIALLY RECONCILED (xem trên) | HARDENING→governance | trước khi bất kỳ phiên nào đề xuất `TASK-105D = DONE` | **CÓ — vẫn chặn DONE thật sự cho tới khi lớp validator được xử lý** | — |
| HB-105D-F2-01 | OPEN | HARDENING | phiên data-contract-authority hoặc implementation chạm `ResolutionBinding` | KHÔNG | CÓ — trước TASK-105E/108B dựa vào invariant này |
| HB-105D-F2-02 | OPEN | HARDENING | phiên soạn Scope Lock + Completion Gate cho TASK-105E | KHÔNG | **CÓ — trước TASK-105E cụ thể** (đã ghi tường minh trong finding gốc) |
| HB-105D-F2-03 | OPEN (một phần đã phủ test tại S040) | HARDENING | implementation session chạm 13 invariant liệt kê | KHÔNG | Thấp — phần lớn đã có test phủ |
| H2-01 | OPEN | HARDENING | thuộc cumulative repair diff của `TASK-105D-RC-1`; nếu sửa, KHÔNG mở cycle mới | KHÔNG | CÓ — trước production retry-heavy concurrent use |
| H2-02 | **RESOLVED_BY_INTEGRATION** | — | — | — | — |
| H2-03 | OPEN | HARDENING | hình dạng có sẵn trước RC-1 | KHÔNG | CÓ — trước khi caller dựa vào error handling khi index write fail |
| H2-04 | OPEN | HARDENING (test quality) | — | KHÔNG | Thấp — chỉ ảnh hưởng độ tin cậy của một test cụ thể như regression guard |
| H2-05 | OPEN | HARDENING | — | KHÔNG | **CÓ — trước real data / trước FilePriceProvider activation** (rủi ro mất dữ liệu âm thầm nằm ngoài threat model B-01) |

`H2-02 = RESOLVED_BY_INTEGRATION` — khớp đúng kỳ vọng brief §A9.

Không finding HARDENING nào (ngoài `H-07`) tự nó chặn `DONE` ngay bây giờ,
đúng nguyên tắc brief §A8 ("A HARDENING does NOT block DONE merely because
it remains OPEN"). `H-07` là ngoại lệ vì nó **là** chính điều kiện DONE, không
phải một hardening nghiệp vụ thông thường.

## A10. Trạng thái TASK-105D sau phiên này

```text
TASK-105D = IMPLEMENTED + RC-1 INTEGRATED
            + INDEPENDENT REVIEW #2 PASS WITH HARDENING
            + CONTROLLED INTEGRATION COMPLETE
            + H-07 PARTIALLY RECONCILED (interpretive layer RESOLVED qua
              DEC-159; validator-alignment layer OPEN)
            STILL_BLOCKED_BEFORE_DONE
            NOT DONE
```

`STILL_BLOCKED_BEFORE_DONE`, không phải `ELIGIBLE_FOR_DONE_REVIEW` — vì
điều kiện #7 của §A7 không thoả, và `H-07` (khác các HARDENING khác) có
re-trigger trực tiếp gắn với `DONE`. Đây là kết luận trung thực theo đúng
yêu cầu "pay special attention to #7" của brief — không "fake closure" chỉ
vì lớp diễn giải đã được Owner giải quyết.

## A11. Phụ lục — bảng đối chiếu SHA/hash theo từng artifact (đo lại trong phiên này)

| Artifact | GATE_SET_SHA256 báo cáo | Khớp canonical? |
|---|---|---|
| `docs/reviews/TASK-105D-FREEZE-FINALIZATION-REVIEW-2.md` (S038) | `0444e58c…4408a5c877` | CÓ |
| `docs/reviews/TASK-105D-GATE-EXECUTION-RECORD.md` (S040) | `0444e58c…4408a5c877` | CÓ |
| `docs/reviews/TASK-105D-INDEPENDENT-IMPLEMENTATION-REVIEW-1.md` (S041) | `0444e58c…4408a5c877` | CÓ |
| `docs/reviews/TASK-105D-RC-1-REPAIR-RECORD.md` (S042) | `0444e58c…4408a5c877` | CÓ |
| `docs/reviews/TASK-105D-INDEPENDENT-IMPLEMENTATION-REVIEW-2.md` (S043) | `0444e58c…4408a5c877` | CÓ |
| `S044-task-105d-controlled-integration.md` (trước & sau merge) | `0444e58c…4408a5c877` | CÓ |
| `DEC-158` (`PROJECT/PROJECT_DECISIONS.md`) | `0444e58c…4408a5c877` | CÓ |
| **Phiên này (S045), đo trực tiếp trên HEAD hiện tại** | `0444e58c…4408a5c877` | CÓ |

Không một artifact nào trong lineage báo giá trị khác. Không hành động nào
của phiên này thay đổi con số này.

---

# PHẦN B — CAPABILITY-FIRST DELIVERY GOVERNANCE RECONCILIATION

## B1–B2. Nguyên tắc & Capability Root

```text
CAPABILITY ID    : CAP-PRICE-RESOLUTION   (đăng ký CAPABILITY, KHÔNG phải
                    task — xem §B7)
BUSINESS PURPOSE : Từ một dòng bán hàng, xác định tất yếu định danh sản
                    phẩm đúng và cơ sở giá mua áp dụng, để logic nghiệp vụ
                    downstream tiêu thụ một KpiPurchasePrice đã resolve kèm
                    đầy đủ provenance.
MEMBER TASKS     : TASK-105B, TASK-105C, TASK-105D, TASK-105E
OUTSIDE CAPABILITY: TASK-108B (downstream consumer, tiêu thụ output của
                    capability — KHÔNG phải member)
```

Xác nhận bằng chứng chuỗi phụ thuộc (đọc lại 4 task spec + `docs/tasks/TASK-105-price-engine.md`
trong phiên này):

```text
TASK-105        định nghĩa PriceProvider Protocol + PendingPriceProvider mặc định
  TASK-105B     implementation thứ hai của Protocol đó — Public Purchase provider
  TASK-105C     implementation thứ ba — HistoricalVendorMin (Tracking)
  TASK-105D     product identity resolver (namespace, source_product_code)
  TASK-105E     composition layer P00–P11 — điều phối 105B/105C, KHÔNG sở hữu
                nguồn dữ liệu riêng nào, trả KpiPurchasePrice semantics
    TASK-108B   tiêu thụ KpiPurchasePrice để tính EligibleKpiProfit — NGOÀI
                capability, là consumer
```

## B3–B3.4. Vertical Acceptance Slice

```text
CAPABILITY BOUNDARY = RESOLVED PURCHASE PRICE + COMPLETE PRICE PROVENANCE
TASK-108B KHÔNG bắt buộc để capability tự chứng minh acceptance của chính nó.
```

### Dữ liệu thật đã tìm thấy (không tổng hợp, xác nhận qua provenance)

`tests/fixtures/golden/period_2026_01.xlsx`, sheet "SỔ CHI TIẾT BÁN HÀNG",
đối chiếu với `tests/fixtures/golden/expected/period_2026_01.json` →
`orders_detail[0]`. Provenance: `tests/fixtures/golden/anonymize.py`
`VERBATIM_COLUMNS` (dòng 109-112) xác nhận các cột `date/order_id/product/
qty/unit_price/sales/discount` được copy **nguyên văn** từ workbook production
thật của Tín Phát; chỉ `customer`/`customer_code` bị thay bằng surrogate.

```text
SALES_RECORD
  OrderID       : BH62063
  Sale date     : 2026-01-02
  Quantity      : 1
  Sell price    : 7,500,000 VND
  Discount      : 0

PRODUCT
  Raw label (chứng từ) : "Máy giặt LG 10kg FV1410S4W1"
  Expected canonical identity   : KHÔNG có trong repo (chưa có mapping đã
                                   Owner-confirm cho raw label này)
  Expected identity namespace   : KHÔNG có
  Expected source product code  : KHÔNG có
```

### MISSING_DATA (không được bịa — xác nhận bằng chứng phủ định)

```text
$ python3 -c "
import json
d = json.load(open('tests/fixtures/golden/expected/period_2026_01.json'))
print(d['pricing'])
"
{'accounting_profit_pending': 351, 'price_source_distribution': {'Pending': 351}}
```

100% (351/351) dòng bán hàng thật trong kỳ 01.2026 có purchase price =
`Pending` — **không có** bất kỳ dòng nào trong Golden fixture (dữ liệu thật
duy nhất trong repo) mang một giá mua thật đã gắn với một OrderID/product/
ngày cụ thể. Toàn bộ fixture test của `TASK-105B`
(`docs/tasks/TASK-105B-file-price-provider.md:242-243`) và `TASK-105C`
(`docs/tasks/TASK-105C-historical-vendor-price-provider.md:467-468`) được
chính các task đó ghi rõ là **synthetic**, không phải dữ liệu Tín Phát thật.

```text
MISSING_DATA:
- Nguồn giá mua/vendor thật (Public Purchase hoặc Tracking) áp dụng cho
  "Máy giặt LG 10kg FV1410S4W1" tại/trước 2026-01-02.
- Định danh canonical (namespace + source_product_code) mà TASK-105D dự
  kiến resolve cho raw label này — chưa có mapping đã Owner-confirm.
- Giá mua kỳ vọng (số tiền + đơn vị) cho đúng đơn BH62063.
- Provenance chain kỳ vọng (nguồn nào, effective-dated record nào).

REQUIRED_SOURCE:
- Lịch sử giá vendor/Public Purchase thật quanh 2026-01 cho nhóm hàng máy
  giặt LG 10kg, từ hồ sơ kế toán/mua hàng thật của Owner (cùng lớp nguồn mà
  TASK-105B/TASK-105C được thiết kế để đọc).
- Xác nhận của Owner cho mapping định danh canonical của raw label này
  (theo semantics `docs/spec/TASK-105D-DATA-CONTRACT.md`).

OWNER_INPUT_REQUIRED:
- Cung cấp (hoặc chỉ ra) MỘT bản ghi giá mua thật (nhà cung cấp, ngày hiệu
  lực, giá) từng có hiệu lực cho sản phẩm này quanh 2026-01-02 — HOẶC xác
  nhận rằng hiện KHÔNG có bản ghi thật nào tồn tại (trong trường hợp đó,
  KpiPurchasePrice = Pending chính là kết quả oracle kỳ vọng cho đơn này, và
  Owner cần xác nhận tường minh điều đó để dùng làm oracle).
- Xác nhận định danh canonical (namespace, source_product_code) kỳ vọng cho
  "Máy giặt LG 10kg FV1410S4W1".
```

### MANUAL_ORACLE (công thức canonical hiện hành, xác nhận trong phiên này)

Công thức lấy từ `docs/tasks/TASK-108B-eligible-costs-owner-definition.md:1040`
("## 24. Trạng thái sau `DEC-144`", xác nhận cuối cùng của Owner, không có
lần thay đổi nào sau đó trong toàn bộ 2,650+ dòng của file):

```text
EligibleKpiProfit = (SellPrice − KpiPurchasePrice) × Quantity − Discount

Thế số đã có:
EligibleKpiProfit = (7,500,000 − KpiPurchasePrice) × 1 − 0
                   = 7,500,000 − KpiPurchasePrice

KpiPurchasePrice   : CHƯA XÁC ĐỊNH — chờ Owner (xem MISSING_DATA)
```

### Kết luận

```text
END_TO_END_ACCEPTANCE = PENDING_OWNER_DATA
```

KHÔNG đánh dấu `DEFINED`/`READY`/`COMPLETE`. Đây là "business-description
level": không implementation, không production code, không cấp phép
downstream task nào — đúng ràng buộc §B3.2/§B3.4 của brief. Persisted tại
`PROJECT/PROJECT_PROGRESS.md` → `CAP-PRICE-RESOLUTION` → `END_TO_END_ACCEPTANCE`.

## B4–B7. Sibling Task Creation Rule & Registry Evidence

Không phát hiện bất kỳ hạng mục nào trong phiên này thoả mãn đồng thời cả
ba điều kiện của §B5 (independent capability + independent lifecycle +
outside CAP-PRICE-RESOLUTION). `TASK-108B` đã tồn tại sẵn làm consumer
downstream — không cần một task mới để giữ chỗ cho nó. Không finding nào
được rà lại ở PHẦN A (H-01…H2-05) đủ điều kiện độc lập capability — toàn bộ
đều thuộc phạm vi kỹ thuật/data-contract của `TASK-105D` hoặc composition
của `TASK-105E`, đã có chủ.

```text
new_registered_task_ids              = 0
proposals_created                    = 0
proposal_names                       = []
owner_assignment_required_entries_added = 0
```

**Sửa lại phương pháp đo giữa phiên.** Lần đo đầu tiên trong phiên này dùng
`grep -oE "TASK-[A-Z0-9]+(-[A-Z0-9]+)*" PROJECT/PROJECT_PROGRESS.md | sort -u`
— chính XÁC kiểu "grep tự do văn xuôi cho chuỗi TASK-*" mà brief §B8 CẤM
tường minh ("Do NOT grep arbitrary repository prose for TASK-* strings").
Đo lại cho thấy tại sao: BEFORE = 58 token duy nhất, AFTER = 59 — chênh lệch
DUY NHẤT là chuỗi `TASK-105D-RC-1`, vốn KHÔNG phải một task ID mới mà là một
**repair-cycle identifier** đã tồn tại từ `S042` (`id: TASK-105D-RC-1` trong
`PROJECT/REVIEW_BUDGET_LEDGER.md` từ trước phiên này) — nó chỉ chưa từng
xuất hiện dưới dạng token ĐỘC LẬP (không kèm hậu tố) trong chính
`PROJECT/PROJECT_PROGRESS.md` trước khi section Capability-Level Repair Budget của
phiên này trích dẫn nó. Đây đúng là loại false positive brief §B8 cảnh báo:
regex tự do không phân biệt được task ID với sub-artifact ID cùng tiền tố.

Bằng chứng registry BEFORE/AFTER — đo lại đúng theo yêu cầu brief §B8 (SET A
= task ID có khai báo trạng thái tường minh trong các khối trạng thái của
`PROJECT/PROJECT_PROGRESS.md`, KHÔNG phải mọi chuỗi khớp pattern):

```text
SET A — REGISTERED_TASK_SET (task ID có "= STATUS" / "Status:" tường minh):
  TASK-101, TASK-105, TASK-105B, TASK-105C, TASK-105D, TASK-105E, TASK-106,
  TASK-107, TASK-108A-1, TASK-108B, TASK-110, TASK-GOLDEN-BASELINE-001,
  TASK-V4-ADOPTION
  BEFORE = 13 task ID   AFTER = 13 task ID   (KHÔNG đổi — phiên này chỉ cập
  nhật narrative trạng thái CỦA TASK-105D đã có sẵn, không thêm task ID nào)

SET B — TASK_SPEC_SET (docs/tasks/*.md):
$ ls docs/tasks/*.md | wc -l
22   BEFORE = AFTER   (phiên này không tạo/xoá bất kỳ Task Spec nào —
     xác nhận bằng diff rỗng giữa danh sách filename trước/sau)
```

`CAP-PRICE-RESOLUTION` (và `CAP-PRICE-RESOLUTION-CORE-GOVERNANCE-CHANGE-
PROPOSAL`, tên file proposal) không khớp tiền tố `TASK-*`, không có Task
Spec dưới `docs/tasks/`, và không phải một mục trong SET A — đúng ý đồ của
brief §B7 (capability registration ≠ task registration).

## B8. Registered vs. mentioned — làm rõ

`PROJECT/PROJECT_PROGRESS.md` không có một bảng "registry" thống nhất duy nhất; trạng
thái task nằm rải ở nhiều khối theo thời gian (khối "Current Price
Architecture — DEC-154", các heading "### TASK-XXX — DONE", khối lịch sử
S040-S044…). Đây là một đặc điểm cấu trúc đã tồn tại từ trước, không phải
việc phiên này tạo ra hay cần sửa (nằm ngoài Scope của cả hai Objective).
Phép đo BEFORE/AFTER ở trên dùng UNION toàn bộ token `TASK-*` xuất hiện
trong file — một phép đo bảo thủ (dễ phát hiện sai lệch hơn, không dễ bị
"lọt lưới" một ID mới) — chứ không chỉ đếm trong một bảng con.

## B9. Owner Task-Creation Proposal

Không có — không hạng mục nào thoả mãn điều kiện mở proposal (§B4-B7).

## B10–B10.3. Absorption Control

Phiên này **không** phát hiện hạng mục kỹ thuật mới nào cần hấp thụ vào một
task hiện có — Objective B ở phiên này thuần tuý là định nghĩa governance
(capability, vertical slice, registry evidence), không phải một review kỹ
thuật tạo ra finding mới. Do đó:

```text
absorption_items_identified = 0
ABSORPTION_LIMIT_REACHED    = KHÔNG kích hoạt (không có gì để hấp thụ)
```

Cơ chế absorption-limit (§B10.2 A/B/C/D) được ghi lại normative ở §B14/CORE
proposal bên dưới để dùng cho các phiên tương lai có finding kỹ thuật thật.

## B11–B12. Module ≠ Task / Finding Routing

Không áp dụng trực tiếp trong phiên này (không có module/finding mới cần
route) — nguyên tắc được ghi normative tại CORE proposal (§B14).

## B13–B13.2. Capability-Level Repair Budget — RECONSTRUCTION (PROPOSED, NOT ADOPTED)

Tái dựng từng Repair Cycle đã tiêu thụ trong 4 member task, từ đúng ledger
canonical hiện có — **không sửa** bất kỳ con số ledger hiện tại nào:

```text
lineage_root: CAP-PRICE-RESOLUTION   (capability, KHÔNG phải root task —
                                       migration_status = PROPOSED)

capability_repair_cycles_allowed (Owner PROPOSAL, chưa adopt): 4

consumed:
  - task: TASK-105B
    cycle: TASK-105B-RC-1
    base_sha: c22cef8b47ac4cd71ef49609066a362c9e604313
    head_sha: 7f7048d65619c2c2198c99ccbfb073d6cb97ebe2
    ledger evidence: PROJECT/REVIEW_BUDGET_LEDGER.md → "Root Task: TASK-105B"
                      → cycles: (dòng 513-521)
  - task: TASK-105D
    cycle: TASK-105D-RC-1
    base_sha: e6252c06347ed5305fc32a77706a3a63f5a950cf
    head_sha: 1cc96a99638326513b26280b72bbeb3bce9d454d
    ledger evidence: PROJECT/REVIEW_BUDGET_LEDGER.md → "Root Task: TASK-105D"
                      → cycles: (dòng 819-857)
  - task: TASK-105C
    cycles consumed: 0 (BLOCKED / NOT AUTHORIZED — chưa implementation)
  - task: TASK-105E
    cycles consumed: 0 (PLANNED / OUTLINE — chưa có Scope Lock/Completion
                      Gate, chưa READY, chưa implementation)

capability_repair_cycles_used      = 2
capability_repair_cycles_remaining = 2   (CHỈ CÓ HIỆU LỰC NẾU proposal được
                                          Owner adopt — hiện tại KHÔNG có
                                          hiệu lực gì, xem migration_status)

migration_status: PROPOSED
```

**Ngân sách per-task hiện hành GIỮ NGUYÊN, KHÔNG đổi bởi bảng trên:**

```text
TASK-105B : 2 allowed / 1 used / 1 remaining   (KHÔNG đổi)
TASK-105C : 2 allowed / 0 used / 2 remaining   (KHÔNG đổi, root riêng theo DEC-156 §4)
TASK-105D : 2 allowed / 1 used / 1 remaining   (KHÔNG đổi)
TASK-105E : 2 allowed / 0 used / 2 remaining   (KHÔNG đổi, cycles: [])
```

## B13.2. Migration Transition Rule

```text
Cho tới khi migration_status = ADOPTED (một quyết định Owner tường minh
riêng, KHÔNG phải phiên này):
  - Ledger per-task hiện hành (bảng trên) TIẾP TỤC là authoritative.
  - KHÔNG task nào trong CAP-PRICE-RESOLUTION (mới hay đã có, kể cả
    TASK-105E khi nó được authorize) được cấp Repair Cycle budget MỚI chỉ
    vì lineage nay được nhóm lại thành một capability.
  - TASK CREATION APPROVAL ≠ REPAIR-BUDGET ALLOCATION APPROVAL (hai trục
    quyết định tách biệt, kể cả khi Owner đã approve task đó tồn tại).
```

## B14–B15. CORE vs. PROJECT & Canonical Persistence

Phân biệt rõ:

```text
PROJECT-specific (persist trong phiên này, thấy ở §"Xác minh cuối phiên"):
  - CAP-PRICE-RESOLUTION (định nghĩa, member tasks, END_TO_END_ACCEPTANCE)
  - PROJECT/PROJECT_DECISIONS.md → DEC-160
  - PROJECT/REVIEW_BUDGET_LEDGER.md → capability migration analysis (PROPOSED)

CORE reusable (KHÔNG amend trực tiếp governance/core/V4_1_POLICY_FREEZE.md
trong phiên này — xem lý do dưới):
  - nguyên tắc capability-first sibling-proliferation control
  - phân biệt task registration vs. capability registration
  - nguyên tắc ownership-gap (§B6)
  - absorption-limit (§B10.2 A/B/C/D)
  - capability-level repair-budget semantics + migration transition rule
```

**Không có authority rõ ràng trong phiên này để amend trực tiếp một file đã
`FREEZE` (`governance/core/V4_1_POLICY_FREEZE.md`, tên file tự nó tuyên bố
trạng thái freeze).** Đây là một core policy document nắm giữ semantics áp
dụng cho MỌI root task trong repo, không riêng `CAP-PRICE-RESOLUTION` — sửa
nó cần một quyết định ở tầm rộng hơn một phiên reconciliation hai-mục-tiêu.
Theo đúng chỉ dẫn brief §B14 ("If CORE modification requires separate
authority: DO NOT bypass it. Create the canonical governance change
proposal required by V4.1."), phiên này tạo:

```text
docs/reviews/CAP-PRICE-RESOLUTION-CORE-GOVERNANCE-CHANGE-PROPOSAL.md
```

chứa đề xuất §16 mới cho `governance/core/V4_1_POLICY_FREEZE.md` (nguyên văn các nguyên tắc
liệt kê ở trên), sẵn sàng cho một phiên có CORE-amendment authority sau này
adopt — **chưa** merge vào file CORE. `governance/core/V4_1_POLICY_FREEZE.md`
= 0 byte thay đổi bởi phiên này (xác minh ở "Xác minh cuối phiên").

## B15.1. Golden Baseline Relationship

`END_TO_END_ACCEPTANCE` (hiện `PENDING_OWNER_DATA`) là **hạt giống nghiệp
vụ** cho cơ chế Golden Baseline hiện có — KHÔNG phải một framework acceptance
song song. Khi authority triển khai cho phép, case cụ thể (OrderID BH62063 +
dữ liệu giá mua Owner cung cấp) NÊN trở thành một Golden case thực thi được
qua đúng cơ chế `GOLDEN_BASELINE_STRATEGY` hiện có. Phiên này KHÔNG tạo
Capability Acceptance Framework, KHÔNG tạo parallel ground-truth mechanism.
Golden Baseline vẫn là cơ chế regression thực thi được duy nhất.

## B16. Capability Governance Verdict

```text
CAPABILITY_GOVERNANCE_VERDICT = PROPOSED_PENDING_CORE_AUTHORITY
```

Lý do: PROJECT-level persistence được thực hiện đầy đủ trong phiên này
(`CAP-PRICE-RESOLUTION` đăng ký, `END_TO_END_ACCEPTANCE = PENDING_OWNER_DATA`,
`DEC-160`, phân tích ledger capability-level PROPOSED). CORE-level rule
(các nguyên tắc reusable ở §B14) mới ở dạng **canonical governance change
proposal**, chưa được amend vào `governance/core/V4_1_POLICY_FREEZE.md` —
cần một phiên có CORE-amendment authority riêng để `ADOPTED`.

---

# PHẦN C — RANH GIỚI & XÁC MINH CUỐI PHIÊN

## Ranh giới đã xác minh KHÔNG bị vượt

```text
TASK-105B/105C/105E implementation        : KHÔNG chạm
TASK-108B implementation                  : KHÔNG chạm
FilePriceProvider activation              : KHÔNG
Tracking mutation                         : KHÔNG
production pricing behavior               : KHÔNG đổi
Repair Cycle #2 (TASK-105D hay bất kỳ)    : KHÔNG mở
TASK-105D = DONE                          : KHÔNG đánh dấu
new TASK-* registration                   : KHÔNG (0 ID mới)
governance/core/V4_1_POLICY_FREEZE.md     : 0 byte thay đổi
frozen TASK-105D gate bytes               : 0 byte thay đổi
```

## Validator (đo lại sau toàn bộ edit của phiên này)

```text
validate_structure           : PASS
validate_project_state       : PASS
validate_evidence             : PASS
validate_task_completion     : PASS
validate_reference_integrity : 3 issue — ĐÚNG BẰNG baseline canonical
                                (chỉ TASK-REM-T06, không suy giảm)
branch_authority_check.sh    : AUTHORITY_OK
git diff --check             : clean
```

## Production diff

```text
app/**       = 0
tests/**     = 0
config/**    = 0
tools/**     = 0
scripts/**   = 0
pyproject.toml = 0
```

## Next authorized action

```text
1. (Objective A) Một phiên có thẩm quyền tooling/governance-scripts — được
   Owner cấp phép riêng — cần đối chiếu validate_task_completion.py với mô
   hình hai lớp vừa được DEC-159 công nhận, HOẶC Owner chấp nhận rằng DONE
   thật sự của TASK-105D sẽ cần một Completion Gate Change Proposal riêng
   (mutate 32 trường Status:, đổi GATE_SET_SHA256) tại thời điểm đó.
2. (Objective B) Một phiên có CORE-amendment authority xem xét
   docs/reviews/CAP-PRICE-RESOLUTION-CORE-GOVERNANCE-CHANGE-PROPOSAL.md để
   ADOPTED hoá các nguyên tắc reusable vào governance/core/V4_1_POLICY_FREEZE.md.
3. (Objective B) Owner cung cấp dữ liệu còn thiếu ở MISSING_DATA (§B3) để
   END_TO_END_ACCEPTANCE chuyển từ PENDING_OWNER_DATA sang DEFINED.
4. TASK-105E vẫn PLANNED/NOT AUTHORIZED; TASK-105C vẫn BLOCKED; TASK-108B
   vẫn BLOCKED_BY_DEPENDENCY — không đổi bởi phiên này.
```

**STOP.** Phiên này dừng sau khi commit/push artifact reconciliation. Không
merge default, không đánh dấu DONE, không mở TASK-105E/105C implementation,
không activate FilePriceProvider, không tạo task mới.
