# S044 — TASK-105D Controlled Integration (Implementation + RC-1 + Review Evidence)

Session Type:
CONTROLLED INTEGRATION — hợp nhất canonical implementation lineage của
`TASK-105D` (implementation + Repair Cycle #1) cùng **cả hai** artifact
Independent Implementation Review vào nhánh mặc định. Đây **không** phải phiên
implementation, **không** phải phiên repair, **không** phải phiên review,
**không** phải phiên freeze, và **không** phải phiên completion.

Date:
2026-08-28

Current Task Mode:
MAJOR

Selected Profile:
PRODUCT

Risk:
Effective Risk HIGH — max(Local Risk 4, Blast Radius 5)

Evidence Level:
E2

Executed By:
phiên Controlled Integration (S044)

Timestamp:
2026-08-28

Branch:
`integration/v4-1-task-105d-implementation`

Authority:
Owner Decision — `governance/core/V4_1_POLICY_FREEZE.md` §8 Option A
(INTEGRATE EARLY). Đóng `DIVERGENCE = INTEGRATION_DECISION_REQUIRED
[ loc > 5.000 ]` mà `S041`, `S042` và `S043` đều ghi nhận là quyết định thuộc
Owner. `V4.1` §12 (state authority): phiên này có integration authority,
**không** có completion authority và **không** có gate authority.

## Owner Decision

```text
V4.1 §8 — INTEGRATION_DECISION_REQUIRED [ cumulative LOC > 5.000 ]
Owner chọn : (A) INTEGRATE EARLY

Owner CẤP PHÉP : hợp nhất có kiểm soát implementation TASK-105D đã review
                 + lineage RC-1.
Owner KHÔNG cấp phép:
    - TASK-105D = DONE
    - Repair Cycle #2
    - TASK-105E implementation
    - FilePriceProvider activation
    - Tracking mutation
    - hardening repair không liên quan
```

Phiên này **không** thêm quyết định nghiệp vụ nào của riêng nó.

## 1. Pre-flight

```text
$ git rev-parse --abbrev-ref HEAD
integration/v4-1-task-105d-implementation

$ git rev-parse HEAD
222844dfb5cf576238fda4cc913ef2095789b4eb        <-- KHỚP expected default base

$ git status --porcelain
(rỗng — worktree CLEAN)

$ git remote show origin | grep 'HEAD branch'
HEAD branch: claude/extract-upload-repo-gq2ws4

$ git rev-parse origin/claude/extract-upload-repo-gq2ws4
222844dfb5cf576238fda4cc913ef2095789b4eb        <-- default CHƯA di chuyển
```

Năm object tham chiếu — toàn bộ truy xuất được (`git cat-file -t` = `commit`):

```text
e6252c06347ed5305fc32a77706a3a63f5a950cf   implementation
1cc96a99638326513b26280b72bbeb3bce9d454d   RC-1 repair code
a09823506fc17b7903e44be848672a18f92bc6ee   RC-1 final
58323e2e59382e2ce4816453cfaaa5d31deba3db   Independent Review #1
4d44ec4a292513f78614d2040ae1fba802747d7c   Independent Review #2
```

Lineage production tuyến tính, đúng như brief yêu cầu bảo toàn:

```text
222844df → e6252c06 → 1cc96a99 → a0982350
```

Đã kiểm bằng `git merge-base --is-ancestor` trước khi merge: `222844df`,
`e6252c06`, `1cc96a99` đều là ancestor của `a0982350`.

## 2. Kiểm tra nhánh review TRƯỚC khi merge (`§5` của brief)

Brief cấm giả định nhánh review là vô hại. Cả hai diff được liệt kê trước khi
hợp nhất:

```text
$ git diff --stat e6252c06 58323e2e          (Review #1)
 PROJECT/PROJECT_PROGRESS.md                                   |  72 ++
 PROJECT/REVIEW_BUDGET_LEDGER.md                               |  19 +
 docs/reviews/TASK-105D-INDEPENDENT-IMPLEMENTATION-REVIEW-1.md | 916 +++++
 docs/sessions/S041-…-review-1.md                              | 129 +++
 4 files changed, 1136 insertions(+)

$ git diff --stat a0982350 4d44ec4a          (Review #2)
 PROJECT/PROJECT_PROGRESS.md                                   | 104 ++
 PROJECT/REVIEW_BUDGET_LEDGER.md                               |  72 ++
 docs/reviews/TASK-105D-INDEPENDENT-IMPLEMENTATION-REVIEW-2.md | 1232 ++++
 docs/sessions/S043-…-review-2.md                              | 139 +++
 4 files changed, 1547 insertions(+)
```

```text
app/**    trong nhánh review : 0 dòng
tests/**  trong nhánh review : 0 dòng
config/** trong nhánh review : 0 dòng
production mutation          : KHÔNG CÓ
```

⇒ Điều kiện STOP của `§5` **không** kích hoạt. Cả hai nhánh chỉ mang
review/governance evidence.

## 3. Phương pháp hợp nhất

`git merge --no-ff` × 3. **KHÔNG** squash, **KHÔNG** rebase, **KHÔNG**
cherry-pick production code, **KHÔNG** dựng lại diff implementation bằng tay.

```text
merge 1  1b0d7f2  <- a0982350   lineage RC-1 (implementation + Repair Cycle #1)
                                xung đột: 0
merge 2  b11c0c8  <- 4d44ec4a   evidence Independent Review #2
                                xung đột: 0
merge 3  3d0b463  <- 58323e2e   evidence Independent Review #1
                                xung đột: 2 file / 4 hunk
```

Thứ tự này được chọn có chủ đích: `4d44ec4a` là hậu duệ trực tiếp của
`a0982350`, nên hợp nhất RC-1 rồi Review #2 cho ra **0 xung đột**; chỉ nhánh
Review #1 — vốn rẽ nhánh từ `e6252c06`, tức TRƯỚC repair — mới thật sự phân kỳ.
Một thứ tự khác sẽ tạo hai lượt xung đột thay vì một, không thêm bằng chứng nào.

Sau merge 1, cây làm việc được đối chiếu với `a0982350`:

```text
$ git diff a0982350 <merge-1> --stat
(rỗng — cây giống hệt RC-1 đã review)
```

## 4. Xung đột — từng cái một (`§7`)

Toàn bộ xung đột nằm ở **governance/documentation state**, đúng lớp mà `§7` dự
kiến. **Không** xung đột nào chạm `app/**`, `tests/**`, khối frozen gate, hay
ngữ nghĩa nghiệp vụ của TASK-105D Data Contract ⇒ điều kiện STOP của `§7`
**không** kích hoạt.

### 4.1 `PROJECT/REVIEW_BUDGET_LEDGER.md` — 3 hunk

| # | Hai thẩm quyền | Giải quyết |
|---|---|---|
| 1 | `S041`: `0 used / 2 remaining` (tiền-RC-1) vs lineage RC-1+`S043`: `1 used / 1 remaining` | Giữ **RC-1+S043**. `§11` của brief quy định dứt khoát `2 allowed / 1 used / 1 remaining`. Phía `S041` là ảnh chụp trước khi cycle #1 được tiêu thụ. |
| 2 | Cùng một dòng `regression:`, khác đúng một glyph (`→` vs `->`) | Giữ **RC-1+S043**. Cùng một sự kiện, không khác ngữ nghĩa. |
| 3 | Bản ghi `TASK-105D-IMPL-REVIEW-2` chỉ có ở HEAD | Giữ **HEAD**. Phía `S041` không có gì để mất. |

Trước khi giải, phía HEAD được chứng minh là **TẬP CHA THỰC SỰ** của phía
`S041`, không phải bằng lời mà bằng phép so hàng:

```text
$ comm -13 <(sort -u ours) <(sort -u theirs)
      regression: 0 (Golden 58/2 không đổi; full 756 → 930; delta +174)
`cycles: []`.
```

Đúng hai dòng. Dòng đầu là khác biệt glyph. Dòng sau (`cycles: []`) là tuyên bố
"chưa cycle nào được mở" — nay **sai sự thật** vì `TASK-105D-RC-1` đã được tiêu
thụ, và đã được HEAD thay bằng bản ghi cycle đầy đủ. Bản ghi
`last_independent_review` của `S041` nằm **nguyên vẹn** trong phía HEAD.

⇒ **Không một bằng chứng repair-budget nào bị loại bỏ.** (`§7.5`)

### 4.2 `PROJECT/PROJECT_PROGRESS.md` — 1 hunk

Cả hai phía mô tả **cùng một** mục `independent review #1 = FAIL — REPAIR
REQUIRED (S041)`, chỉ khác cách diễn đạt; phía HEAD viết tiếp sang `repair cycle
#1` (`S042`), `independent review #2` (`S043`) và ngân sách đã cập nhật.

```text
Giữ  : phía lineage RC-1+S043 (trạng thái canonical mới nhất). Phía này đã ghi
       đủ verdict của S041: FAIL — REPAIR REQUIRED, 1 BLOCKING (B-01),
       7 HARDENING, 3 OUT_OF_SCOPE, 32/32 frozen check PASS, A–T 20/20,
       Golden 58/2 KHÔNG ĐỔI, regression 0.
Thêm : con trỏ evidence docs/sessions/S041-…-review-1.md mà phía HEAD thiếu
       (phía Review #1 có). Thuần bổ sung, không sửa verdict.
```

**Khối lịch sử `### Trạng thái sau INDEPENDENT REVIEW #1 (S041, 2026-08-28)`
được tự động hợp nhất và giữ NGUYÊN VĂN:**

```text
$ diff <(git show 58323e2e:PROJECT/PROJECT_PROGRESS.md | sed -n '/### Trạng thái sau INDEPENDENT REVIEW #1/,/### Trạng thái sau CONTROLLED INTEGRATION/p') \
       <(sed -n '/### Trạng thái sau INDEPENDENT REVIEW #1/,/### Trạng thái sau CONTROLLED INTEGRATION/p' PROJECT/PROJECT_PROGRESS.md)
(không có khác biệt — 52/52 dòng IDENTICAL)
```

⇒ **Không verdict lịch sử nào bị viết lại.** (`§7.4`)

Một sửa đổi duy nhất nằm ngoài phần verdict: chú thích khung `*(Cập nhật …
S041 …)*` của khối đó vốn tự xưng *"Đoạn ngay dưới đây là trạng thái + hành
động kế tiếp hiện hành"*. Sau merge, câu đó **sai** — trạng thái hiện hành là
khối `S043` — và để hai khối cùng tự xưng "hiện hành" trong một file trạng thái
governance là một mơ hồ thật sự, có thể khiến phiên sau đọc
`NOT ELIGIBLE FOR INTEGRATION` của `S041` như trạng thái đang có hiệu lực.
Chú thích được hạ xuống dạng lịch sử, **đúng quy ước mà chính repo đã áp dụng
cho khối `S040`** khi `S042` thay thế nó. Verdict bên trong: 0 byte thay đổi.

## 5. Frozen Completion Gate (`§8`)

Khối gate được định vị bất biến với dịch chuyển dòng (neo canonical `be835b1`
dòng 567..2295 = 1729 dòng), nên phép đo không phụ thuộc số dòng của file.

```text
                                lines   bytes    GATE_SET_SHA256
neo canonical be835b1            1729   57614    0444e58c…4408a5c877
TRƯỚC integration (222844df)     1729   57614    0444e58c…4408a5c877
tại e6252c06                     1729   57614    0444e58c…4408a5c877
tại a0982350 (RC-1)              1729   57614    0444e58c…4408a5c877
SAU integration                  1729   57614    0444e58c…4408a5c877
```

```text
frozen hash TRƯỚC == frozen hash SAU        KHỚP TUYỆT ĐỐI
0444e58c02b04804a116c140af722ffc29ea64adf468aa6c93794c4408a5c877
```

Phiên này **KHÔNG** sửa định nghĩa frozen gate và **KHÔNG** đổi trường `Status:`
bên trong nó chỉ để ghi nhận việc đã thực thi. 32 trường `Status:` vẫn là
`NOT_TESTED` — xem `§6`.

## 6. `H-07` — thẩm quyền gate (`§9`)

Disposition canonical, theo `§23` của Independent Review #2:

```text
NOT_TESTED trong ĐỊNH NGHĨA frozen gate chặn DONE, KHÔNG chặn controlled
integration.
```

Phiên này **KHÔNG** chặn integration chỉ vì định nghĩa bất biến còn ghi
`NOT_TESTED`. Bản ghi thực thi tách rời được giữ nguyên và nay đã nằm trên
default:

```text
docs/reviews/TASK-105D-GATE-EXECUTION-RECORD.md          32/32 PASS (S040)
docs/reviews/TASK-105D-INDEPENDENT-IMPLEMENTATION-REVIEW-2.md §17.2
                                                         32/32 PASS
                                                         (thực thi ĐỘC LẬP
                                                          tại a0982350 bởi S043)
```

**Ghi nhận tường minh:**

```text
CONTROLLED INTEGRATION của TASK-105D KHÔNG ngụ ý TASK-105D = DONE.
Một phiên reconciliation riêng, do Owner / gate authority thực hiện, là BẮT
BUỘC trước DONE. Hai đường hợp lệ nằm ở §23 của Review #2; khuyến nghị của
reviewer là đường (b) — Owner Decision công nhận bản ghi thực thi tách rời,
giữ nguyên GATE_SET_SHA256 = 0444e58c….
Phiên S044 KHÔNG thực hiện reconciliation này.
```

## 7. `H2-02` — disposition (`§6` của brief)

Review #2 đo: baseline canonical = **3** issue `TASK-REM-T06`; RC-1 = **4**;
issue mới = repair record trỏ tới artifact Review #1, vốn chỉ tồn tại trên
`58323e2e`.

Sau khi hợp nhất **cả hai** artifact review, đo lại trên nhánh integration:

```text
$ python3 governance/scripts/governance/validate_reference_integrity.py
REFERENCE INTEGRITY: FAIL
Quét 159 file .md (loại trừ 10 file trong governance/reference/history/, docs/audit/).
3 reference không phân giải được:
- docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> /README.md
- docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> CODE_OF_CONDUCT.md
- docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> CONTRIBUTING.md
```

Đo lại baseline trên worktree tách riêng tại `222844df` — **giống hệt 3 issue
đó**, cùng nội dung, cùng thứ tự.

```text
H2-02 : RESOLVED_BY_INTEGRATION
```

Bằng chứng đây là phân giải CƠ HỌC, **không** phải suppression:

```text
(a) validator KHÔNG bị sửa:
    $ git diff 222844df HEAD --stat -- governance/scripts/governance/
    (rỗng)
(b) file đích của tham chiếu nay TỒN TẠI trên cây:
    docs/reviews/TASK-105D-INDEPENDENT-IMPLEMENTATION-REVIEW-1.md  (44.994 byte)
    — đến từ merge 3 (58323e2e), không phải do phiên này soạn ra.
(c) tham chiếu trong repair record giữ NGUYÊN VĂN, không bị đổi thành dạng
    chỉ-SHA để né validator.
```

`RESOLVED_BY_INTEGRATION` **KHÔNG** được tính là Repair Cycle #2 (`§10`, `§11`).
Phiên này sửa 0 dòng `app/**`, `tests/**`, `config/**`.

3 issue còn lại = `O2-01` / `O-01`, `OUT_OF_SCOPE`, có trước `TASK-105D`, thuộc
`TASK-REM-T06`. Brief `§6` cấm dọn dẹp reference không liên quan ⇒ **KHÔNG
chạm**.

## 8. HARDENING — dispositions (`§10`)

Toàn bộ finding đang mở được **bảo toàn**, không mục nào bị sửa cơ hội.

| ID | Trạng thái sau S044 | Ghi chú |
|---|---|---|
| `H-01` | **OPEN** | không chạm |
| `H-02` | **OPEN** (contract-level) | không chạm |
| `H-03` | **OPEN** | không chạm |
| `H-04` | **OPEN** | không chạm |
| `H-05` | **OPEN** | không chạm |
| `H-06` | **OPEN** | không chạm |
| `H-07` | **OPEN** | reconciliation bắt buộc TRƯỚC DONE — `§6` ở trên |
| `HB-105D-F2-01` | **OPEN** | data contract KHÔNG sửa |
| `HB-105D-F2-02` | **OPEN** | data contract KHÔNG sửa |
| `HB-105D-F2-03` | **OPEN** | không chạm |
| `H2-01` | **OPEN** | thuộc cumulative repair diff RC-1; sửa (nếu Owner cho) thuộc CÙNG cycle #1 |
| `H2-02` | **RESOLVED_BY_INTEGRATION** | bằng chứng ở `§7` |
| `H2-03` | **OPEN** | hình dạng có sẵn trước repair |
| `H2-04` | **OPEN** | test quality |
| `H2-05` | **OPEN** | durability, ngoài mô hình đe doạ B-01 |

```text
OPEN                    : 14
RESOLVED_BY_INTEGRATION : 1   (H2-02)
REPAIRED bởi S044       : 0
PROMOTED lên BLOCKING   : 0
```

## 9. Ngân sách repair (`§11`)

```text
TASK-105D : 2 allowed / 1 used / 1 remaining      (KHÔNG ĐỔI)
TASK-105D-RC-1 : CONSUMED                          (KHÔNG reset)
Repair Cycle #2 : KHÔNG mở
```

Controlled integration **không** tiêu thụ repair cycle: `V4.1` §3 tính cycle
theo cumulative repair diff của implementation, và phiên này sửa 0 dòng
`app/**`, `tests/**`, `config/**`, `tools/**`, `scripts/**`, `pyproject.toml`.

## 10. Tương đương production với RC-1 đã review (`§16`)

```text
$ git diff a0982350 HEAD --stat -- app/ tests/ config/ tools/ scripts/ \
                                    pyproject.toml docs/spec/ docs/tasks/
(rỗng)

$ sha256sum app/modules/product/identity/store.py
c3d3b09ddb15979bd0dbc255f9938a5da87583be110e85244706c200a7f829aa
$ git show a0982350:app/modules/product/identity/store.py | sha256sum
c3d3b09ddb15979bd0dbc255f9938a5da87583be110e85244706c200a7f829aa   <-- KHỚP
```

```text
Sửa đổi production sau review : KHÔNG CÓ (0 byte)
```

Toàn bộ diff giữa `a0982350` và HEAD chỉ gồm 6 file governance/review evidence.

## 11. Sanity concurrency / security (`§17`)

Không merge conflict nào chạm `store.py` (sha256 khớp tuyệt đối, `§10` ở trên)
⇒ theo `§17`, **không** cần lặp lại toàn bộ 135 vòng review độc lập. Xác minh
ngắn gọn, đo trên cây đã hợp nhất:

```text
1. khoá liên-tiến-trình còn nguyên : fcntl.flock(fd, LOCK_EX) — store.py:367
2. nạp lại TRONG khoá còn nguyên   : _refresh_from_disk() — :370, SAU flock,
                                     TRƯỚC yield
3. kiểm version TRONG khoá         : append() :506 `with self._transaction():`
                                     _require_version :554 nằm trong yield
4. sidecar lock nguyên vẹn         : lock_path = <log_path>.lock,
                                     os.O_NOFOLLOW, chmod 0o600 — :364
5. đường mutation ngoài giao dịch  : KHÔNG CÓ — `_persist_raw` = 0 occurrence
                                     (RC-1 đã XOÁ); append / rebuild_index /
                                     import_bundle đều đi qua _transaction()

tests/test_105d_interprocess_concurrency.py : 25 passed
```

## 12. Test sau integration (`§14`)

```text
                            kỳ vọng                 đo được            kết quả
TASK-105D targeted          199 passed              199 passed         OK
Golden                      58 passed, 2 skipped    58 passed, 2 skip  OK
Full suite                  955 passed, 11 skipped  955 passed, 11 sk  OK
regression                  0                       0                  OK
```

## 13. Validator (`§15`)

```text
validate_structure           : PASS  (21 required path)
validate_project_state       : PASS
validate_evidence            : PASS  (88 REQUIRED PASS record)
validate_task_completion     : PASS  (6 DONE task)
validate_reference_integrity : 3 issue — ĐÚNG BẰNG baseline canonical
                               (chỉ TASK-REM-T06; H2-02 đã RESOLVED_BY_INTEGRATION)
branch_authority_check.sh    : AUTHORITY_OK
git diff --check             : clean (0 cảnh báo whitespace)
```

## 14. Ancestry (`§20`)

```text
$ git merge-base --is-ancestor <SHA> HEAD

222844dfb5cf576238fda4cc913ef2095789b4eb   ancestor  YES
e6252c06347ed5305fc32a77706a3a63f5a950cf   ancestor  YES
1cc96a99638326513b26280b72bbeb3bce9d454d   ancestor  YES
a09823506fc17b7903e44be848672a18f92bc6ee   ancestor  YES
58323e2e59382e2ce4816453cfaaa5d31deba3db   ancestor  YES
4d44ec4a292513f78614d2040ae1fba802747d7c   ancestor  YES
```

Cả năm object của brief đều truy xuất được từ lịch sử default cuối cùng.
Lineage production `222844df → e6252c06 → 1cc96a99 → a0982350` được giữ
nguyên vẹn, không squash, không rebase, không cherry-pick.

## 15. Ranh giới — đã xác minh KHÔNG bị vượt

```text
TASK-105D = DONE                        : KHÔNG
Repair Cycle #2                         : KHÔNG mở
TASK-105E implement                     : KHÔNG (không đổi authorization)
FilePriceProvider activate              : KHÔNG
Tracking                                : KHÔNG CHẠM
production data                         : KHÔNG CHẠM, KHÔNG TẠO
hardening repair không liên quan        : KHÔNG thực hiện
frozen gate definition                  : KHÔNG SỬA (hash khớp)
TASK-105D Data Contract                 : KHÔNG SỬA
app/pipeline.py                         : KHÔNG ĐỔI (PendingPriceProvider
                                          vẫn là default)
reference cleanup không liên quan       : KHÔNG thực hiện
nhánh task/task-105d-* , review/*       : KHÔNG mutate
```

## 16. Trạng thái `TASK-105D` sau phiên này (`§12`)

Dùng đúng từ vựng canonical repo đã dùng cho `TASK-105B`
(`FROZEN + INTEGRATED + RC-1 INTEGRATED / NOT DONE`):

```text
TASK-105D = IMPLEMENTED + RC-1 INTEGRATED
            + INDEPENDENT REVIEW #2 PASS WITH HARDENING
            + CONTROLLED INTEGRATION COMPLETE
            NOT DONE
```

`IMPLEMENTED` là state enum canonical trong vòng đời task của `CLAUDE.md`;
không phát minh enum mới.

## 17. Next authorized action

```text
1. Owner / gate authority reconcile H-07 theo §23 của Review #2 — BẮT BUỘC
   TRƯỚC khi bất kỳ phiên nào đề xuất TASK-105D = DONE. Khuyến nghị đường (b).
2. KHÔNG mở Repair Cycle #2. Nếu Owner muốn đóng H2-01 / H-05 / H-01 / H-03:
   Owner Decision; H2-01 + H-05 cùng vùng mã (_consume) nên sửa MỘT lượt và
   thuộc CÙNG cycle #1 theo V4.1 §3 — không tiêu thêm ngân sách.
3. Song song, không chặn: phiên có thẩm quyền data contract đóng H-02,
   HB-105D-F2-01, HB-105D-F2-02.
4. TASK-105E vẫn NOT IMPLEMENTED / NOT AUTHORIZED. FilePriceProvider vẫn
   không activate. Tracking vẫn không chạm.
```

**STOP.** Phiên này dừng sau controlled integration. Không reconcile `H-07`,
không đánh dấu `DONE`, không mở Repair Cycle #2.
