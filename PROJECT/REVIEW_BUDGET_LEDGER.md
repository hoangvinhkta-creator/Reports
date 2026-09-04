# REVIEW BUDGET LEDGER

Machine Control #2 của Governance V4.1 (`TASK-V4-ADOPTION`, §18).

Ledger này là bản ghi tường minh, đọc được bằng máy lẫn con người, về ngân
sách repair-cycle của từng root task lineage theo bảng đã freeze ở
`governance/core/RULE_PRECEDENCE.md` §... *(bảng ngân sách nằm trong chính
Owner Decision của V4.1 — xem `PROJECT/PROJECT_DECISIONS.md` DEC-140
và các mục liên quan)*. Không phải nơi diễn giải lại luật; chỉ ghi trạng
thái.

## Bảng ngân sách đã freeze (V4.1)

```
LOW              = 1 blocking repair cycle
MEDIUM           = 1 blocking repair cycle
HIGH / CRITICAL  = 2 blocking repair cycles
```

Không tồn tại `HIGH = 3`. Owner được phép đặt budget thấp hơn bảng này cho
một root task cụ thể. Vượt budget → `OWNER_EXTENSION REQUIRED`.

Ngân sách gắn với **ROOT TASK LINEAGE**. Sub-unit (ví dụ R1-A2, R1-B, R2…)
không có ngân sách riêng, không reset ngân sách, và không được tạo lineage
mới chỉ để reset ngân sách.

---

## Root Task: TASK-V4-ADOPTION

```
root_task: TASK-V4-ADOPTION
effective_risk: MEDIUM
repair_cycles_allowed: 1
repair_cycles_used: 0
repair_cycles_remaining: 1
```

Production code changes: FORBIDDEN (theo phạm vi V4.1-0).

Nếu adoption không hoàn thành sau 1 blocking repair cycle: DESCOPE →
MINIMAL V4.1 OVERLAY (không tạo V4.1-R1, V4.1-R1A, V4.1-Repair-2, hay bất kỳ
decomposition nào nhằm reset budget).

cycles:
- id: (chưa mở — adoption hoàn thành trong 0 repair cycle tính đến thời
  điểm ghi ledger này)
  base_sha: N/A
  head_sha: N/A

---

## Root Task: TASK-110

Đây là **transition ledger có chủ ý** cho một root task lineage đã tồn tại
từ trước V4.1, được V4.1 tiếp nhận nguyên trạng — không được cấp lại ngân
sách, không được đưa giá trị `repair_cycles_remaining` về khác 0 chỉ vì V4.1
mới có hiệu lực.

```
root_task: TASK-110
effective_risk: HIGH
repair_cycles_allowed: 2
repair_cycles_used: EXHAUSTED_PRE_V4.1
repair_cycles_remaining: 0

historical_evidence:
    independent_reviews: ">=8"
    repairs: ">=3"

authorized_actions:
    - FINAL_REVIEW_ONLY
    - ACCEPT_AS_IS
    - DESCOPE
    - OWNER_EXTENSION
```

**TASK-110 BUDGET = EXHAUSTED.** Đây là trạng thái chuyển tiếp có chủ ý, ghi
tại thời điểm V4.1 adoption (2026-08-27), không phải placeholder chờ điền
sau.

### Sub-unit lineage — không có ngân sách riêng

R1-A2, R1-A3, R1-A4, R1-B … R1-E, R2 … R8 — nếu thuộc `TASK-110` thì đều
thuộc cùng lineage `TASK-110`. Vì `TASK-110.repair_cycles_remaining = 0`,
**không unit nào trong nhóm này được tự mở**. Mỗi unit muốn tiếp tục phải
có một `OWNER_EXTENSION` riêng, kèm:

- production path cụ thể;
- kịch bản nghiệp vụ sai cụ thể nếu không xử lý;
- phạm vi được phép;
- budget được Owner cấp.

Không có Owner Extension tương ứng → `STOP`.

### Cycle accounting lịch sử (tham chiếu, không phải ngân sách còn lại)

Cumulative repair diff của TASK-110 được ghi trong các session log dưới
`docs/sessions/S015` … `S023` và trong `PROJECT/PROJECT_DECISIONS.md`
(DEC-128 … DEC-139). Kể từ integration `V4.1-1` (2026-08-27) toàn bộ lịch sử
này đã nằm trên nhánh mặc định — không còn phân tán trên các nhánh review
riêng. Ledger này không sao chép lại toàn bộ lịch sử đó — chỉ xác nhận điểm
chốt: ngân sách repair-cycle của lineage `TASK-110` đã cạn TRƯỚC khi V4.1 có
hiệu lực.

cycles:
- id: PRE_V4.1_HISTORICAL
  base_sha: (xem lịch sử session TASK-110 — ngoài phạm vi ghi lại tại đây)
  head_sha: (xem lịch sử session TASK-110 — ngoài phạm vi ghi lại tại đây)
  note: >
    Lịch sử đầy đủ (>=8 Independent Review, >=3 repair) nằm trong
    docs/sessions/ và PROJECT/PROJECT_DECISIONS.md trên các nhánh review
    TASK-110 đang hoạt động. Ledger V4.1 chỉ ghi nhận điểm chốt ngân sách,
    không viết lại lịch sử.

### Merge gate liên quan

**ĐÃ CÓ QUYẾT ĐỊNH — `DEC-141` (2026-08-27, V4.1-1).** Owner chọn option (B)
của §9: `CHECK-110-16` đổi Gate Class thành `POST_MERGE_PRODUCTION_ACCEPTANCE`.

```
CHECK-110-16
Priority   : REQUIRED                            (không đổi)
Status     : BLOCKED                             (không đổi)
Gate Class : POST_MERGE_PRODUCTION_ACCEPTANCE    (đổi từ pre-merge gate)
```

Chỉ Gate Class đổi. Vẫn thiếu production workbook thật để đối chiếu. Không
được giả lập PASS hay bypass. **Merge KHÔNG đồng nghĩa `TASK-110 DONE`** —
`TASK-110` chỉ chuyển `DONE` khi check này thực sự `PASS` trên dữ liệu
production thật. Xem `governance/core/TASK_COMPLETION_GATE_STANDARD.md`,
`DEC-141` và `docs/tasks/TASK-110-validation-review-queue.md`.

Đồng hồ 30 ngày của §9 vì vậy **đã dừng** cho gate này: quyết định Owner đã
được đưa ra ở ngày thứ 4 (phát sinh 2026-08-23 → quyết định 2026-08-27).

### Branch divergence đã biết

**ĐÃ ĐÓNG — `DEC-141` §4 (2026-08-27, V4.1-1).** Owner chọn option (A) của
§8: integrate/merge sớm.

Divergence đo được ngay trước integration, so với nhánh mặc định
`claude/extract-upload-repo-gq2ws4` @ `c7a1b24`:

| Nhánh | ahead | thời gian | LOC | vượt ngưỡng |
|---|---:|---|---:|---|
| `claude/r1-a1-contract-freeze-9lkh3h` | 24 | 4 ngày | 40.523 | cả ba |
| `claude/r1-canonical-object-safety-fon9lb` | 18 | 1 ngày | 37.509 | 2/3 |
| `claude/zealous-bardeen-s8iu2h` | 13 | 0 ngày | 31.126 | 2/3 |
| `claude/task-110-gate-readiness-7ui4si` | 6 | 0 ngày | 7.509 | 1/3 |
| `claude/governance-v4-1-freeze-36oexq` | 1 | 0 ngày | 722 | không |

Ba nhánh review phụ được chứng minh là **ancestor** của nhánh authoritative
`claude/r1-a1-contract-freeze-9lkh3h` (`git rev-list --count <A1>..<phụ>` = 0
cho cả ba) ⇒ 0 commit unique bị bỏ lại khi hợp nhất.

**KNOWN PRE-V4.1 DIVERGENCE = CLOSED tại V4.1-1.** Không grandfather thành
permanent exception.

---

## Root Task: TASK-PRA-001

Lineage **mới** (root task riêng, khai ở Metadata của
`docs/tasks/TASK-PRA-001-legacy-reference-vertical.md`). Không kế thừa và
không tiêu ngân sách của bất kỳ lineage nào trước đó.

```
root_task: TASK-PRA-001
effective_risk: MEDIUM
repair_cycles_allowed: 1
repair_cycles_used: 1
repair_cycles_remaining: 0
```

Cycle 1 đã dùng ở **S076** (2026-09-02) cho Independent Review
`CHANGES_REQUIRED` trên `7d84072`: hai blocking finding
`FIND-PRA001-R01` (thiếu dòng nguồn vẫn báo khớp 100%) và
`FIND-PRA001-R02` (sự cố database hiển thị thành lỗi workbook của Owner).
**Ngân sách repair đã hết** — mọi finding blocking tiếp theo phải leo thang
theo `governance/core/ESCALATION_PROTOCOL.md`, không tự mở cycle 2.

`MEDIUM` theo **Blast Radius tính theo failure path**
(`governance/core/V4_1_POLICY_FREEZE.md` §4), không theo độ khó code:

- **BR-1** — số cũ hiển thị sai, hoặc hiển thị thiếu nhãn `LEGACY`, khiến
  Owner đọc nhầm số cũ thành số pipeline và ra quyết định kinh doanh trên
  con số sai nguồn. Giảm nhẹ: mọi giá trị đi qua đúng MỘT macro Jinja gắn
  nhãn, và test trích toàn bộ ô số từ HTML để khẳng định không ô nào thiếu
  nhãn (CHECK-PRA001-04).
- **BR-2** — cấu hình database sai làm production không khởi động. Đây là
  failure path đã được chọn CÓ Ý (fail closed): thà không deploy còn hơn
  chạy lên rồi hiển thị lịch sử rỗng như thể chưa ai nhập gì.
- **KHÔNG** chạm production pipeline, KPI, lương, Product Identity, PP,
  accounting reconciliation, R2, Tracking — nên failure path dừng ở tầng
  đọc lịch sử, không lan vào đường tính toán đang chạy.

### Scope Lock

```
app/modules/**                          : FORBIDDEN
app/pipeline.py, app/composition.py     : FORBIDDEN
app/owner_usability.py, app/demo.py     : FORBIDDEN
app/web/storage_backend.py              : FORBIDDEN
app/web/run_registry.py                 : FORBIDDEN
tools/storage/**, tools/tracking/**     : FORBIDDEN
config/**, data/**                      : FORBIDDEN
tests/fixtures/golden/**                : FORBIDDEN
Tracking (mọi thứ)                      : FORBIDDEN — READ-ONLY REFERENCE
schema PRA-002 (snapshot/version/…)     : FORBIDDEN — không prebuild
```

### Trạng thái (S076, 2026-09-02 — sau repair cycle 1)

```
TASK-PRA-001                 : IMPLEMENTED (KHÔNG phải DONE)
Independent Review #1        : CHANGES_REQUIRED trên 7d84072
repair cycle đã dùng         : 1 / 1  → CÒN 0
CHANGE_BUDGET                : GIẢI QUYẾT — DEC-168 approve ~1.050 LOC;
                               đo sau repair = 1.045 (trong ngân sách)
FIND-PRA001-R01              : ĐÃ SỬA (parser fail to + verifier source
                               coverage; 11 test hồi quy)
FIND-PRA001-R02              : ĐÃ SỬA (except HTTPException: raise;
                               3 test đường ghi)
CHECK-PRA001-01              : NOT_TESTED — cần file Excel thật (gate Owner);
                               evidence viết lại: VALUE MATCH + SOURCE COVERAGE
CHECK-PRA001-09              : BLOCKED — cần PostgreSQL thật (gate deploy)
Re-review                    : CHƯA THỰC HIỆN
```

Bằng chứng thực thi của phiên (E1):

```text
validate_structure           : PASS
validate_project_state       : PASS
validate_evidence            : PASS  (99 REQUIRED PASS record)
validate_task_completion     : PASS  (8 DONE task)
validate_reference_integrity : FAIL — ĐÚNG 3 issue đã biết của TASK-REM-T06,
                               không phát sinh mới (203 file quét)
branch_authority_check.sh    : AUTHORITY_OK
git diff --check             : sạch
Full suite baseline          : 1494 passed, 11 skipped
Full suite cuối S075         : 1586 passed, 11 skipped
Full suite cuối S076 (repair): 1600 passed, 11 skipped
migration 0001_legacy        : upgrade PASS, downgrade PASS (SQLite thật)
verify_legacy_import         : matched=628 mismatched=0 (trên fixture)
```

> **CLARIFICATION HIỆN HÀNH (thêm 2026-09-02, S077 close-out — finding `N08`;
> KHÔNG sửa record S076 phía trên).** Dòng
> `verify_legacy_import : matched=628 mismatched=0 (trên fixture)` ở khối
> trên chỉ ghi **một nửa** của fidelity, và nửa đó chính là nửa đã được
> `FIND-PRA001-R01` chứng minh là không đủ. Ledger là bản ghi immutable
> theo phiên nên dòng đó được giữ nguyên; cách đọc đúng hiện hành là:
>
> ```text
> fidelity = VALUE MATCH + SOURCE COVERAGE   (DEC-168)
>
> VALUE MATCH     : mismatched = 0
> SOURCE COVERAGE : SUMMARY_SOURCE_ROWS_WITH_VALUES == SUMMARY_IMPORTED_ROWS
>                   AND SUMMARY_UNACCOUNTED_ROWS == 0
>                   AND SUMMARY_REFERENCE_ONLY_PERSISTED == 0   (DEC-169)
> ```
>
> `matched=N mismatched=0` đứng MỘT MÌNH không được dùng làm bằng chứng
> completeness — verifier bản cũ duyệt DB → Excel nên không thể thấy dòng
> chưa từng được nhập.

### Trạng thái (S077 close-out, 2026-09-02 — HIỆN HÀNH)

Mục này thay thế mục "Trạng thái (S076…)" phía trên **về trạng thái hiện
tại**; mục S076 giữ nguyên như bản ghi lịch sử của phiên đó.

```
TASK-PRA-001                 : DONE
Independent Review #1        : CHANGES_REQUIRED trên 7d84072
Repair Re-review (cycle 1/1) : PASS trên 5bea87a
Final Independent Delta Review: PASS trên 3faedfde (DEC169_REVIEW = FAITHFUL)
review record durable        : docs/reviews/TASK-PRA-001-INDEPENDENT-REVIEW-RECORD.md
repair cycle đã dùng         : 1 / 1  → CÒN 0 (KHÔNG đổi; DEC-169 là
                               OWNER_SCOPE_CLARIFICATION, không tiêu budget)
FIND-PRA001-R01              : ĐÃ ĐÓNG
FIND-PRA001-R02              : ĐÃ ĐÓNG
CHECK-PRA001-01              : PASS — Real Data Acceptance trên workbook
                               THẬT (VALUE MATCH matched=1508 mismatched=0;
                               SOURCE COVERAGE 71 == 71, unaccounted 0,
                               reference-only persisted 0)
CHECK-PRA001-09              : BLOCKED (RECOMMENDED) — cần PostgreSQL thật,
                               gate deploy Owner, không chặn DONE
REQUIRED_GATES               : 9/9 PASS
BLOCKING_FINDINGS            : NONE
```

Bằng chứng thực thi của phiên close-out (E1), chạy trên `3faedfde`:

```text
validate_structure           : PASS (21 required path)
validate_project_state       : PASS
validate_evidence            : PASS  (100 REQUIRED PASS record)
validate_task_completion     : PASS  (9 DONE task, đã gồm PRA-001)
validate_reference_integrity : FAIL — ĐÚNG 3 issue đã biết của TASK-REM-T06
                               (/README.md, CODE_OF_CONDUCT.md,
                                CONTRIBUTING.md), 204 file quét, 0 finding mới
branch_authority_check.sh    : AUTHORITY_OK
                               (DIVERGENCE = INTEGRATION_DECISION_REQUIRED
                                [loc>5000] → Owner chọn phương án (A)
                                integrate, chính là phiên này — V4.1 §8)
git diff --check             : sạch
Golden                       : 58 passed, 2 skipped
Full suite                   : 1608 passed, 11 skipped
PRA-001 focused suite        : 114 passed
verify_legacy_import (fixture): SUMMARY_SOURCE_ROWS_WITH_VALUES = 13
                                SUMMARY_IMPORTED_ROWS           = 13
                                SUMMARY_UNACCOUNTED_ROWS        = 0
                                SUMMARY_REFERENCE_ONLY_PERSISTED = 0
                                matched=580 mismatched=0, exit=0
```

## Root Task: TASK-PRA-002

Lineage **mới** (root task riêng, khai ở Metadata của
`docs/tasks/TASK-PRA-002-pipeline-persistence-reconciliation.md`). Không kế
thừa và không tiêu ngân sách của `TASK-PRA-001` hay bất kỳ lineage nào khác.
Mở tại phiên Roadmap Finalization S079 (2026-09-02), `BASE_SHA =
553d8a36f578b082128a6e45d2748da2bc371e70`.

```
root_task: TASK-PRA-002
effective_risk: HIGH
repair_cycles_allowed: 2
repair_cycles_used: 1
repair_cycles_remaining: 1
```

> **Đính chính bookkeeping (S087, Independent Review E2 slice C1, 2026-09-02).**
> Khối máy đọc ở trên trước đó ghi `repair_cycles_used: 0` /
> `repair_cycles_remaining: 2`, mâu thuẫn với chính file này. Đã sửa thành
> `1` / `1`. Thẩm quyền hoàn toàn rõ, ba nguồn cùng chỉ một hướng:
> (a) `governance/core/V4_1_POLICY_FREEZE.md` §3 định nghĩa cycle **tính theo
> LẦN SỬA**, và `PRA-002-RC-1` là một lần sửa BLOCKING có đủ `base_sha`/
> `head_sha` như luật bắt buộc ghi; (b) danh sách `cycles:` của chính lineage
> này có ĐÚNG một mục; (c) prose của khối S084 trong cùng file đã ghi
> "lineage vẫn 1/2". Cùng quy ước với `TASK-GOLDEN-BASELINE-001` (một mục
> `cycles:` → `used: 1`). Đây là defect bookkeeping của governance, KHÔNG
> chạm production path → **KHÔNG tiêu repair cycle** (đúng
> `TASK-PRA-002` mục 23 chỉ thị review slice C1). Ngân sách thật còn lại:
> **1 blocking repair cycle**. Đóng `FIND-PRA002-C1-N1` do S086 mở.

`HIGH` theo **Blast Radius tính theo failure path**
(`governance/core/V4_1_POLICY_FREEZE.md` §4), không theo tên module:

- **BR-1** — một dòng bán được đếm hai lần khi hai snapshot chồng kỳ →
  doanh thu/đơn/LN KPI tháng sai → lương/thưởng sai. Giảm nhẹ: PK
  `order_line_current` theo khoá + UNIQUE `(khoá, version_no)`; oracle
  đẳng thức `state(A,B) == state(B)` (CHECK-PRA002-04).
- **BR-2** — một dòng bị âm thầm mất/xoá khi snapshot mới thiếu nó. Giảm
  nhẹ: append-only, `REMOVED_CANDIDATE` vẫn current và vẫn tính
  (CHECK-PRA002-07/09).
- **BR-3** — source version bị ghi đè tại chỗ → mất bằng chứng kế toán đã
  sửa gì. Giảm nhẹ: `changed_fields` + version cũ giữ (CHECK-PRA002-05).
- KHÔNG chạm business rule pipeline (Product Identity, PP, accounting
  reconciliation, AUTO/Pending) — tầng lưu chỉ ghi lại engine đã quyết gì.

### Scope Lock

```
app/modules/**                          : FORBIDDEN — trừ ĐÚNG alias public
                                          present_lines/PresentedLine trong
                                          app/modules/exporting/excel_exporter.py (≤ 4 dòng)
app/pipeline.py, app/composition.py     : FORBIDDEN
app/owner_usability.py, app/owner_launcher.py : FORBIDDEN
app/demo.py                             : CHỈ +2 trường DemoRun (raw_rows, presented_lines)
app/web/storage_backend.py              : FORBIDDEN
app/web/run_registry.py                 : FORBIDDEN
tools/storage/**, tools/tracking/**     : FORBIDDEN
config/**, data/**                      : FORBIDDEN
tests/fixtures/golden/**                : FORBIDDEN (fixture hai snapshot sinh trong test, không commit)
app/legacy/**, 4 bảng legacy_*          : FORBIDDEN
render.yaml, Dockerfile                 : FORBIDDEN
Tracking (mọi thứ)                      : FORBIDDEN — READ-ONLY REFERENCE
DELETE / UPDATE-in-place trên bảng fact : FORBIDDEN — DATA_INTEGRITY_RISK
```

### Trạng thái (S085, 2026-09-02 — HIỆN HÀNH)

```
TASK-PRA-002                 : IN_PROGRESS (gate FROZEN, 17 check / 16 REQUIRED)
Implementation               : SLICE A INTEGRATED; SLICE B INTEGRATED; slice C NEXT
repair cycle đã dùng         : 1 / 2   (còn 1 — integration KHÔNG tiêu cycle)
CHANGE_BUDGET slice B        : 289 dòng logic production / mục tiêu slice ≤ 500 / cảnh báo 600 / dừng cứng 800 → ĐẠT
CHANGE_BUDGET lineage        : 1.104 (A) + 289 (B) = 1.393 / mục tiêu 1.200 / dừng cứng 1.500
                                → VƯỢT mục tiêu mềm, còn **107 dòng** trước dừng cứng (authoritative — không
                                  dùng lại số cũ 1.346/154 của S083, đã bị supersede bởi phép đo hiệu chuẩn của S084)
                                Slice C phải lập BUDGET-AWARE PLAN trong 107 dòng đó trước khi viết mã, hoặc mở
                                  đề xuất CHANGE_BUDGET cho Owner TRƯỚC implementation
Baseline slice B (27b9d1c5)  : Golden 58 passed, 2 skipped; full suite 1711 passed, 11 skipped
Sau slice B                  : Golden 58 passed, 2 skipped; full suite 1781 passed, 11 skipped (+70 test, 0 skip thêm)
Sau review S084 (+3 test)    : full suite 1784 passed, 11 skipped; PostgreSQL 16.13 thật 113 passed
Sau integration S085         : fast-forward, tree == accepted tree; smoke slice B 79 passed, slice A 96 passed;
                                git diff --check sạch; validators PASS (trừ reference_integrity — 3 pre-existing REM-T06, DEFER)
Migration slice B            : KHÔNG có — schema 0002_snapshots đã đủ; ALEMBIC_HEAD không đổi
                                (reviewer xác minh bằng `alembic upgrade head` trên PostgreSQL 16.13 thật)
Nhánh slice B                : claude/pra-002-slice-b-snapshot-8rbwip (BASE_SHA 27b9d1c5, ĐÃ integrate)
Canonical hiện tại           : claude/extract-upload-repo-gq2ws4 @ d2c7691210313ef82016a6c28106885e5f58c19a
                                (fast-forward từ 27b9d1c5, không merge commit, tree == accepted head)
```

Controlled Integration (S085) — `git merge --ff-only` slice B
(`ACCEPTED_SLICE_B_SHA = d2c7691210313ef82016a6c28106885e5f58c19a`, chứa
`7658c5e5` implementation + `d2c7691` independent review) vào
`claude/extract-upload-repo-gq2ws4` từ `27b9d1c5a578742450099c53f2f82411f07aa9dc`.
Fast-forward thuần, không squash/rebase/force/cherry-pick, không merge commit.
Push xong, fetch lại xác nhận `origin/claude/extract-upload-repo-gq2ws4 ==
d2c7691` và working tree sạch. `TASK-PRA-002` vẫn `IN_PROGRESS` — KHÔNG đánh
DONE (slice C + RDA + Production Acceptance chưa xong).

Independent Review E2 TOÀN TASK (S092, 2026-09-03) — canonical
`d7a1154a2892e5869e286e10da49f750aa0611df` (khớp EXPECTED, không moved); RDA
evidence branch `claude/pra-002-rda-continuation-814n4h` @ `14499dd` (docs-only,
0 production LOC). `REVIEW_RESULT = PASS`, `FINAL_ACCEPTANCE = ACCEPT`,
`BLOCKING_FINDINGS = 0` → **0 repair cycle tiêu thụ** (lineage vẫn 1/2, còn 1).
Reviewer tái lập độc lập trên PostgreSQL 16.13 thật CHECK-01/03/04/05/06/07/08/09
+ FIND-PRA002-A1 invariant; LOC đo lại A 1.104 / B 289 / C1 67 = 1.460 / 1.500
(khớp, còn 40). `CHECK-PRA002-17 = PASS (E2)`; `CHECK-PRA002-15 = NOT_TESTED`
(Owner). Task vẫn `IN_PROGRESS`. Bằng chứng:
`docs/reviews/TASK-PRA-002-INDEPENDENT-REVIEW-RECORD.md`.

Controlled Integration slice C1 (S088) — fast-forward `claude/extract-upload-repo-gq2ws4`
từ `bfe7008f7dfd42c90465f6d32ca38b4c2dfeaf82` lên
`579b497ba7427d66838d9b2769863ccca20a104e` (== exact remote HEAD của
`claude/pra-002-slice-c-plan-jg798m` đã qua Independent Review E2 ACCEPT, chứa
`3cd92ea` implementation + `579b497` review docs-only). `git merge --ff-only`,
fast-forward thuần, KHÔNG squash/rebase/force/cherry-pick, KHÔNG merge commit.
Tree sau integration IDENTICAL với accepted tree (cùng tree SHA
`ba9220cc…`) → không rerun full suite; smoke: C1 focused 83 passed, Slice A/B
persistence 97 passed, `git diff --check` sạch. Push xong, fetch lại xác nhận
`origin/claude/extract-upload-repo-gq2ws4 == 579b497` và working tree sạch;
`branch_authority_check.sh` → `AUTHORITY_OK`. Validators: structure /
project_state / task_completion / evidence PASS; `reference_integrity` FAIL với
ĐÚNG 3 lỗi pre-existing `TASK-REM-T06` → DEFER. **0 repair cycle tiêu thụ**
(lineage vẫn 1/2, còn 1); **0 dòng production code thêm** — ngân sách vẫn
1.460 / 1.500, còn 40 LOC. `TASK-PRA-002` vẫn `IN_PROGRESS` — KHÔNG đánh DONE
(RDA `CHECK-PRA002-14` + Production Acceptance `CHECK-PRA002-15` chưa xong).

Independent Review E2 slice C1 (S087) — `REVIEW_BASE_SHA =
bfe7008f7dfd42c90465f6d32ca38b4c2dfeaf82`, `REVIEW_HEAD_SHA =
3cd92eae3035dd40aaf3f64bd3ba96a1d1b49cd0`, `FINAL_ACCEPTANCE = ACCEPT`,
`INTEGRATION_READY = YES`. 0 finding BLOCKING → **0 repair cycle tiêu thụ**
(lineage 1/2, còn 1). Reviewer tái lập độc lập trên PostgreSQL 16.13 thật:
vertical hai lần capture (`n_source_changed = 0`, `n_result_revised = 1`,
source version không đổi, result version mới, con trỏ kết quả dịch, cờ hiện),
SOURCE_CHANGED precedence, COLLISION, rollback ép lỗi, đếm theo khoá, và bất
biến repair `FIND-PRA002-A1` sau collision. Mutation check độc lập: 4 đột biến
ngữ nghĩa (bỏ điều kiện SAME / sai tập trường diff / tính revisions sau khi
dịch con trỏ / trỏ cờ vào source version) đều bị test bắt. `CHANGE_BUDGET` đo
lại độc lập khớp từng file: **+67**, cumulative **1.460 / 1.500**. Một finding
NON_BLOCKING (`FIND-PRA002-C1-N1`, bookkeeping ledger) đã sửa trong phiên
review, không tiêu cycle. Bằng chứng đầy đủ:
`docs/reviews/TASK-PRA-002-SLICE-C1-INDEPENDENT-REVIEW-RECORD.md`.

Independent Review E2 slice B (S084) — `REVIEW_BASE_SHA = 27b9d1c5`,
`REVIEW_HEAD_SHA = 7658c5e5`, `FINAL_ACCEPTANCE = ACCEPT`,
`INTEGRATION_READY = YES`. 0 finding BLOCKING → **0 repair cycle tiêu thụ**
(lineage vẫn 1/2). 4 finding NON_BLOCKING: B1 (số liệu CHANGE_BUDGET — đã sửa
ngay trong phiên review), B2 (nhân đôi cờ khi hai lần xác nhận ĐỒNG THỜI → DEFER
PRA-004), B3 (trần `FLAG_PAGE_LIMIT = 200` trên trang snapshot → DEFER PRA-004),
B4 (không CSRF trên mọi route POST — baseline có sẵn, Cloudflare Access là front
door → DEFER). Bổ sung trong phiên review, được mục 13 chỉ thị cho phép: 3 test
rollback cho transaction xác nhận (`tests/test_snapshot_absence.py` +87 dòng,
KHÔNG sửa production), đã mutation-check. Bằng chứng đầy đủ:
`docs/reviews/TASK-PRA-002-SLICE-B-INDEPENDENT-REVIEW-RECORD.md`.

Slice B (S083) — nhánh `claude/pra-002-slice-b-snapshot-8rbwip`, cắt từ
`IMPLEMENTATION_BASE_SHA = 27b9d1c5a578742450099c53f2f82411f07aa9dc`
(== origin/`claude/extract-upload-repo-gq2ws4` lúc mở phiên; canonical không
dịch chuyển). Bằng chứng đầy đủ:
`docs/sessions/S083-pra-002-slice-b-coverage-semantics.md`. Check chuyển trạng
thái: **CHECK-PRA002-06 PARTIAL → PASS (E1)** và **CHECK-PRA002-07 NOT_TESTED →
PASS (E1)**. BR-2 của bảng blast radius ở trên ("một dòng bị âm thầm mất/xoá
khi snapshot mới thiếu nó") nay có bằng chứng trực tiếp trên PostgreSQL 16.13
thật: ở CẢ hai nhánh `NOT_SEEN` và `REMOVED_CANDIDATE`, `order_line_current`,
`SUM(total_sales)` và `COUNT(*)` của mọi bảng fact đều KHÔNG đổi.

Controlled Integration (S082) — fast-forward `claude/extract-upload-repo-gq2ws4`
từ `7fad3f76908d6d56114a5e2e947d83e15f8eda02` lên
`86f26a0e15b9655d3b0384b59c221f68bc3a1665` (== exact remote HEAD của
`claude/pra-002-slice-a-umygjq` đã qua Independent Review E2 PASS). Sau
integration: `branch_authority_check.sh` → `AUTHORITY_OK`; focused Slice A
tests (116) PASS trên canonical mới; `validate_reference_integrity` vẫn FAIL
với đúng 3 lỗi pre-existing của `TASK-REM-T06` (ngoài scope, DEFER, không
liên quan diff PRA-002).

Slice A (S080) — nhánh `claude/pra-002-slice-a-umygjq`, cắt từ
`IMPLEMENTATION_BASE_SHA = 7fad3f76908d6d56114a5e2e947d83e15f8eda02`
(== origin/`claude/extract-upload-repo-gq2ws4` lúc mở phiên). Bằng chứng đầy
đủ: `docs/sessions/S080-pra-002-slice-a-implementation.md`. Check PASS sau
slice A: 01, 02, 03, 04, 05, 09, 10, 11, 12, 13, 16 (RECOMMENDED); 06 =
PARTIAL; 07 (slice B), 08 (slice C), 14, 15, 17 = NOT_TESTED.

Independent Review E2 slice A (S081) — kết luận **E2 PASS** sau một repair
cycle. Bằng chứng: `docs/reviews/TASK-PRA-002-SLICE-A-INDEPENDENT-REVIEW-RECORD.md`.
Mọi check trong bảng xác minh do phiên review tự chạy (E2), kể cả migration
up/down trên PostgreSQL 16.13 thật.

cycles:
- id: PRA-002-RC-1
  base_sha: 80c6fe1d1c98497d821a8802fdbc9a1ca6a48b60
  head_sha: b0ecab78b5a460f09b78e4b084ab680520920669
  finding: FIND-PRA002-A1 (BLOCKING) — version nguồn mới đánh số theo version
    hiện hành thay vì theo max đã ghi (trái mục 5.3). Sau một
    `ORDER_KEY_COLLISION`, mọi lần ghi version sau trên khoá đó vi phạm UNIQUE
    `(khoá, version_no)` → rollback → `/run` HTTP 500 vĩnh viễn với sổ chứa Số
    BH đó. Tái hiện trên cả SQLite và PostgreSQL 16.13.
  fix: `CurrentState.max_version_no` + `next_version_no`; reconciler dùng
    `next_version_no`; `_load_current` nạp `MAX(version_no)` theo khoá; thêm
    `test_uploading_again_after_a_collision_still_works`.
  result: Golden 58/2, full suite 1711 passed / 11 skipped, PostgreSQL 16.13 PASS

---

## Root Task: TASK-PRA-003

Lineage **mới** (root task riêng, khai ở Metadata của
`docs/tasks/TASK-PRA-003-tong-quan-nhan-vien.md`). KHÔNG kế thừa và KHÔNG
tiêu ngân sách của `TASK-PRA-001`, `TASK-PRA-002` hay bất kỳ lineage nào
khác. Đặc biệt: KHÔNG kế thừa 40 LOC còn lại trong CHANGE_BUDGET của
`TASK-PRA-002` — đó là ngân sách THAY ĐỔI của lineage khác, không phải ngân
sách REVIEW và không chuyển nhượng được.

Mở tại phiên Roadmap Finalization S095 (2026-09-03),
`BASE_SHA = facf090c782b022730ecc5f1cf0d0b02e29ca8d7` (HEAD nhánh canonical
`claude/extract-upload-repo-gq2ws4` lúc freeze gate).

```
root_task: TASK-PRA-003
effective_risk: MEDIUM
repair_cycles_allowed: 1
repair_cycles_used: 0
repair_cycles_remaining: 1
```

`MEDIUM` theo **Blast Radius tính theo failure path**
(`governance/core/V4_1_POLICY_FREEZE.md` §4), KHÔNG theo tên module:

- **BR-1** — một ô dashboard hiển thị sai (cộng cả dòng `PENDING` vào Lợi
  nhuận KPI; hiện `0`/`0%` thay vì `—` cho kỳ trước không có dữ liệu; trộn
  `LEGACY_REFERENCE` với `PIPELINE_GENERATED` trong cùng một ô) → Owner ra
  quyết định quản lý dựa trên số sai. Giảm nhẹ: CHECK-PRA003-03/04/06/08.
- **BR-2** — dòng `sale_date IS NULL` biến mất trong im lặng khỏi mọi kỳ →
  tổng "Toàn bộ dữ liệu" nhỏ hơn tổng thật mà không ai biết. Giảm nhẹ:
  CHECK-PRA003-09.
- **KHÔNG phải HIGH** vì: toàn bộ touch area là tầng CHỈ-ĐỌC (không một câu
  `INSERT`/`UPDATE`/`DELETE` nào); không ghi đè dữ liệu; không đổi KPI/lương
  đã tính; không chạm bất biến no-double-count — bất biến đó thuộc
  `TASK-PRA-002` và PRA-003 chỉ đọc lại kết quả của nó.

### Điều kiện mở repair cycle

Finding KHÔNG tự động trở thành repair work. Chỉ mở cycle khi finding đe doạ
TRỰC TIẾP một trong năm điều:

1. tính trung thực của kết quả quản lý;
2. bất biến no-double-count;
3. sự tách bạch `LEGACY_REFERENCE` ↔ `PIPELINE_GENERATED`;
4. an toàn `NULL` / coverage (`NULL` ≠ `0`);
5. nghiệm thu real vertical (Tháng 09/2026).

Finding ngoài năm nhóm đó: `HARDENING` kèm RE-TRIGGER CONDITION cụ thể
(V4.1 §7) hoặc `OUT_OF_SCOPE`. Vượt 1 cycle → `OWNER_EXTENSION REQUIRED`;
KHÔNG tách sub-unit, KHÔNG đổi tên task, KHÔNG mở nhánh mới để reset ngân
sách (V4.1 §2, §3).

### Scope Lock (tóm tắt — bản đầy đủ ở task file mục 12)

```
tools/db/**, app/history/**                   : FORBIDDEN
app/web/history_store.py, history_writer.py   : FORBIDDEN
app/web/run_registry.py, storage_backend.py   : FORBIDDEN
app/web/legacy_presentation.py                : FORBIDDEN (chỉ đọc/import)
app/modules/**, app/pipeline.py               : FORBIDDEN
config/**, data/**, tests/fixtures/golden/**  : FORBIDDEN
alembic.ini, render.yaml, Dockerfile          : FORBIDDEN
Tracking (mọi thứ)                            : FORBIDDEN — READ-ONLY REFERENCE
Mọi INSERT/UPDATE/DELETE                      : FORBIDDEN — PRA-003 là tầng CHỈ-ĐỌC
```

cycles:
- id: (chưa mở — implementation S096 hoàn tất với 0 BLOCKING finding; repair
  cycle chỉ mở nếu Independent Review E2 tìm ra finding đe doạ 1 trong 5 điều
  ở trên)
  base_sha: N/A
  head_sha: N/A

### Trạng thái (S099, 2026-09-03 — HIỆN HÀNH) — TASK-PRA-003 = DONE

```
TASK-PRA-003          : DONE — Owner đã nghiệm thu CHECK-PRA003-07 trên production
                        thật (Tháng 09/2026); 12/12 REQUIRED check PASS; Exit Criteria
                        thoả đủ 8/8.
CHECK-PRA003-07        : PASS — FROZEN_EXPECTED (40 đơn/61 dòng/AUTO 15/Review 25/so
                        tháng trước trống) khớp ĐÚNG oracle O-G. OBSERVED_ONLY (số
                        lượng 71, doanh thu 593.550.000, LN KPI 8.936.667 (32/61),
                        LN kế toán 8.085.000 (35/61), dòng thiếu ngày bán 0) ghi lại
                        NGUYÊN VĂN, KHÔNG viết ngược thành oracle mới.
repair cycle đã dùng   : 0 / 1   ← closeout KHÔNG tiêu repair cycle
CHANGE_BUDGET cuối cùng: Python 284 · template 191 · CSS 16 — không đổi so với S096/S098
BLOCKING_FINDINGS      : 0
NON_BLOCKING (đóng sổ) : FIND-PRA003-01 đã đối chiếu tài liệu (S098)
                        FIND-PRA003-02 đã đối chiếu tài liệu (S098)
                        FIND-PRA003-03 DEFER/RECORD ONLY — RE-TRIGGER CONDITION còn
                        hiệu lực trong docs/reviews/TASK-PRA-003-INDEPENDENT-REVIEW-RECORD.md
                        cho lineage kế tiếp nếu có
```

### Trạng thái (S098, 2026-09-03 — lịch sử)

```
TASK-PRA-003          : IN_PROGRESS — đối chiếu tài liệu FIND-01/FIND-02 xong (KHÔNG
                        repair), fast-forward vào canonical xong, CHỜ CHECK-07
Đối chiếu tài liệu     : FIND-PRA003-01 — thêm footnote [^oc-context] dưới bảng
                        Acceptance Oracle (mục 16 task file), làm rõ 0/351 (đường
                        golden TRẦN) vs 2/351 (đường giống production) đều đúng cho
                        ngữ cảnh của mình; bất biến có thẩm quyền là NULL ≠ 0, không
                        phải literal cụ thể. KHÔNG đổi Yêu cầu: gốc của CHECK-03/04,
                        KHÔNG đổi Owner Decision, KHÔNG đổi fixture/expected JSON.
                        FIND-PRA003-02 — xoá 1 trailing whitespace ở
                        docs/sessions/S094-…md:341; git diff --check working tree sạch.
                        FIND-PRA003-03 — DEFER/RECORD ONLY, không sửa.
repair cycle đã dùng  : 0 / 1   ← đối chiếu tài liệu KHÔNG tiêu repair cycle
Integration           : PURE FAST-FORWARD claude/pra-003-roadmap-finalization-di33bn
                        → claude/extract-upload-repo-gq2ws4 (không merge/squash/rebase)
```

### Trạng thái (S097, 2026-09-03 — lịch sử)

```
TASK-PRA-003          : IN_PROGRESS — Independent Review E2 ĐÃ ACCEPT, CHỜ Controlled
                        Integration; sau đó CHECK-07 (Owner nghiệm thu production)
Independent Review E2 : XONG — REVIEW_RESULT = ACCEPT_WITH_NON_BLOCKING_FINDINGS
                        artifact: docs/reviews/TASK-PRA-003-INDEPENDENT-REVIEW-RECORD.md
                        BASE facf090c… · TARGET a36f9591… · CONTRACT c12c5635… — cả ba KHỚP
CHECK đã đóng         : 01-06 PASS · 08-11 PASS · 12 PASS · 13-14 PASS  (13/14)
CHECK còn mở          : 07 NOT_TESTED (Owner nghiệm thu production, sau deploy) — việc CUỐI
BLOCKING_FINDINGS     : 0  (reviewer tự chạy lại, không tìm được đường tới số sai)
NON_BLOCKING          : FIND-PRA003-01 CONTRACT_MISMATCH (minh hoạ số học O-C dẫn xuất từ
                        run_import() TRẦN của build_expected.py; đường persist thật là
                        run_import_production ⟹ coverage golden đúng là 2/351. Oracle
                        KHÔNG bị làm yếu: fixture không sửa, test còn assert ngược lại
                        rằng file golden vẫn đọc {Pending: 351}. Khắc phục = sửa DOCS O-C)
                        FIND-PRA003-02 EVIDENCE_DEFECT (git diff --check trên DẢI COMMIT có
                        1 trailing whitespace ở docs/sessions/S094-…md:341, chỉ file docs;
                        dạng working-tree của lệnh đúng là sạch)
                        FIND-PRA003-03 HARDENING (một nhân viên mang hai employee_group sẽ
                        hiện hai dòng; bất biến cộng được vẫn đúng; có RE-TRIGGER CONDITION)
repair cycle đã dùng  : 0 / 1   ← review KHÔNG tiêu cycle; không finding nào đủ điều kiện mở
Reviewer chạy lại     : PRA-003 67 passed · Golden 58 passed 2 skipped · legacy 34 passed
                        PRA-002 vertical 12 passed · FULL SUITE 1873 passed, 11 skipped
                        oracle golden recompute bằng SQL THÔ: 351 dòng / 254 đơn / SL 407 /
                        doanh thu 3.562.310.000 — KHỚP expected JSON và KHỚP implementation
                        budget đo lại độc lập: Python 284 · template 191 · CSS 16 (tái lập ĐÚNG)
                        Scope Lock: 0 vi phạm · tests/fixtures/golden/** KHÔNG bị sửa
```

### Trạng thái (S096, 2026-09-03 — lịch sử)

```
TASK-PRA-003          : IN_PROGRESS — implementation XONG, CHỜ Independent Review E2
                        (gate FROZEN, 14 check / 12 REQUIRED / 2 RECOMMENDED)
Implementation        : XONG — 284 dòng Python production, 191 dòng template, 16 dòng CSS
CHECK đã đóng         : 01-06 PASS · 08-11 PASS · 13-14 PASS  (12/14)
CHECK còn mở          : 07 NOT_TESTED (Owner nghiệm thu production, sau deploy)
                        12 NOT_TESTED (Independent Review E2 — việc TIẾP THEO)
BLOCKING_FINDINGS     : 0
repair cycle đã dùng  : 0 / 1   ← phiên implement KHÔNG tiêu repair cycle
CHANGE_BUDGET đã đo   : Python 284 / mục tiêu 255 / cảnh báo mềm 320 / DỪNG CỨNG 400 → TRONG NGƯỠNG
                        template 191/220 · CSS 16/25 · test mới 67 (≥30) · dependency 0 · schema 0 · migration 0
Baseline TRƯỚC code   : Golden 58 passed, 2 skipped · full suite 1806 passed, 11 skipped
                        validators: structure/project_state/evidence/task_completion = PASS;
                        reference_integrity = FAIL đúng 3 issue REM-T06 đã biết (DEFER)
Đo lại SAU code       : Golden 58 passed, 2 skipped (KHÔNG đổi)
                        full suite 1873 passed, 11 skipped (+67 test, skip KHÔNG tăng)
                        validators GIỐNG HỆT baseline — không issue mới
```

### Trạng thái (S095, 2026-09-03 — lịch sử)

```
TASK-PRA-003          : IN_PROGRESS / READY_FOR_IMPLEMENTATION
Implementation        : CHƯA BẮT ĐẦU — 0 dòng production
repair cycle đã dùng  : 0 / 1
```

---

## Root Task: TASK-PRA-004

Lineage **mới** (root task riêng, khai ở Metadata của
`docs/tasks/TASK-PRA-004-ban-hang-review-detail.md`). KHÔNG kế thừa và KHÔNG
tiêu ngân sách của `TASK-PRA-001`, `TASK-PRA-002`, `TASK-PRA-003` hay bất kỳ
lineage nào khác. Đặc biệt: KHÔNG kế thừa phần CHANGE_BUDGET còn dư của
`TASK-PRA-003` — đó là ngân sách THAY ĐỔI của lineage khác, không phải ngân
sách REVIEW và không chuyển nhượng được.

Mở tại phiên Discovery + Contract Freeze S100 (2026-09-03),
`BASE_SHA = 8181cebe0619a9c8d12604168a90914c04b3692f` (HEAD nhánh canonical
`claude/extract-upload-repo-gq2ws4` lúc freeze contract, đã verify khớp EXACT
kỳ vọng đầu phiên).

```
root_task: TASK-PRA-004
effective_risk: MEDIUM
repair_cycles_allowed: 1
repair_cycles_used: 0
repair_cycles_remaining: 1
```

`MEDIUM` theo **Blast Radius tính theo failure path**
(`governance/core/V4_1_POLICY_FREEZE.md` §4), KHÔNG theo tên module:

- **BR-1** — một đơn có dòng `PENDING` hiện thành `AUTO` (ví dụ triển khai
  lấy trạng thái của dòng đầu tiên thay vì `MAX(CASE WHEN PENDING)`) → Owner
  tin một đơn chưa chắc chắn là đã chắc chắn. Giảm nhẹ: CHECK-PRA004-05, với
  oracle ca TRỘN thật `BH62439` (1 dòng AUTO + 3 dòng PENDING).
- **BR-2** — lợi nhuận đơn hiện đầy đủ trong khi chỉ một phần dòng có giá
  trị. Đo được trên `BH62439`: doanh thu net 66.000.000 nhưng LN kế toán
  500.000 chỉ phủ 1/4 dòng → Owner tin "đơn này lãi 500.000" cho cả đơn 66
  triệu. Giảm nhẹ: CHECK-PRA004-06 (coverage bắt buộc ở CẤP ĐƠN lẫn cấp
  dòng, INV-6/INV-7).
- **BR-3** — trang chi tiết đi sâu hơn PRA-003 nên có bề mặt PII lớn hơn
  (`imei`, `note_raw` — trường mà `tests/fixtures/golden/anonymize.py` xác
  nhận CÓ chứa tên và số điện thoại khách trên dữ liệu thật). Giảm nhẹ:
  CHECK-PRA004-09 (E2) và CHECK-PRA004-10.
- **KHÔNG phải HIGH** vì: toàn bộ touch area CHỈ-ĐỌC (không một câu
  `INSERT`/`UPDATE`/`DELETE` nào, kiểm bằng AST chứ không bằng grep); không
  ghi đè dữ liệu đã lưu; không đổi KPI/lương đã tính; không chạm bất biến
  no-double-count — bất biến đó thuộc `TASK-PRA-002` và PRA-004 chỉ đọc lại
  kết quả của nó.

### Điều kiện mở repair cycle

Finding KHÔNG tự động trở thành repair work. Chỉ mở cycle khi finding đe doạ
TRỰC TIẾP một trong năm điều:

1. tính trung thực của kết quả quản lý ở cấp ĐƠN hoặc DÒNG;
2. bất biến no-double-count (INV-1 … INV-4 của mục 20.5 file task);
3. sự tách bạch `LEGACY_REFERENCE` ↔ `PIPELINE_GENERATED`;
4. an toàn `NULL` / coverage (INV-6, INV-7) hoặc ranh giới PII (mục 14 file task);
5. nghiệm thu real vertical Tháng 09/2026.

Finding ngoài năm nhóm đó: `HARDENING` kèm RE-TRIGGER CONDITION cụ thể
(V4.1 §7) hoặc `OUT_OF_SCOPE`. Vượt 1 cycle → `OWNER_EXTENSION REQUIRED`;
KHÔNG tách sub-unit, KHÔNG đổi tên task, KHÔNG mở nhánh mới để reset ngân
sách (V4.1 §2).

### Trạng thái tại S100

```
Discovery + Contract Freeze  : XONG (docs-only, PRODUCTION_CODE_DELTA = 0)
BLOCKING_FINDINGS            : 0
Non-blocking đã ghi          : FIND-PRA004-01 (TRUTHFULNESS_CONSTRAINT, đã đưa vào contract)
                               FIND-PRA004-02 (DOC_INCONSISTENCY, giải bằng thiết kế)
                               FIND-PRA004-03 (HARDENING, DEFER + RE-TRIGGER)
repair_cycles_used           : 0 / 1  — phiên discovery KHÔNG tiêu cycle
```

### Trạng thái tại S101 (MAJOR Implementation)

```
MAJOR Implementation         : XONG — IMPLEMENTATION_RESULT = PASS
TASK-PRA-004                 : IN_PROGRESS (KHÔNG phải DONE)
CHECK PASS                   : 12/14 — CHECK-PRA004-12 (Independent Review E2) và
                               CHECK-PRA004-14 (Owner Production Acceptance) = NOT_TESTED
BLOCKING_FINDINGS            : 0
Non-blocking THÊM            : FIND-PRA004-04 (DOC_INCONSISTENCY — header Completion
                               Gate đếm "13 check · 11 REQUIRED · 2 RECOMMENDED" trong
                               khi thực tế là 14 check · 13 REQUIRED · 1 RECOMMENDED;
                               KHÔNG tự sửa vì thuộc phần FROZEN, cần
                               COMPLETION GATE CHANGE PROPOSAL)
repair_cycles_used           : 0 / 1
repair_cycles_remaining      : 1
```

Phiên implement **KHÔNG tiêu** repair cycle. Theo chỉ thị §29, việc một phiên
triển khai tự sửa khiếm khuyết trong CHÍNH mã nó vừa viết là công việc bình
thường của phiên đó, KHÔNG phải một repair cycle của Independent Review —
ngân sách 1 cycle được giữ NGUYÊN VẸN cho vòng review E2 sắp tới. Phiên này
cũng không nới hợp đồng, không refactor module ngoài phạm vi, và không sửa
finding lịch sử/DEFER nào.

### Trạng thái tại S102 (Independent Review E2)

```
Independent Review E2        : XONG — REVIEW_RESULT = E2 PASS
FINAL_DECISION               : ACCEPT_WITH_NON_BLOCKING_FINDINGS
BASE_SHA / CONTRACT / TARGET : 8181cebe / 46a5cdb0 / 6a23c328  — cả ba KHỚP
TARGET_MOVED                 : KHÔNG
TASK-PRA-004                 : IN_PROGRESS (KHÔNG phải DONE)
CHECK PASS                   : 13/14 — CHECK-PRA004-12 = PASS (E2);
                               CHECK-PRA004-14 (Owner Production Acceptance) = NOT_TESTED
BLOCKING_FINDINGS            : 0
Non-blocking THÊM            : FIND-PRA004-05 (HARDENING — docstring `_line()` nói sai
                               về `pending_reasons_json`; KHÔNG tới template, DEFER)
                               FIND-PRA004-06 (tử số coverage KPI kế thừa NGUYÊN VẸN
                               từ PRA-003; đổi sẽ vỡ CHECK-PRA004-07, DEFER)
                               FIND-PRA004-07 (trang danh sách 3,7 MB ở 4.000 đơn;
                               dưới ngưỡng RE-TRIGGER 3 giây, DEFER)
                               FIND-PRA004-08 (ổn định thứ tự dòng khi SOURCE_CHANGED;
                               không hệ quả nghiệp vụ, DEFER)
                               FIND-PRA004-09 (DOC_INCONSISTENCY — văn bản `Yêu cầu:`
                               của CHECK-12 và CHECK-13 bị đặt nhầm khối trong file
                               task; bản FROZEN 46a5cdb NGUYÊN VẸN)
FIND-PRA004-04               : reviewer ĐẾM ĐỘC LẬP và XÁC NHẬN phân loại
                               A. DOC_INCONSISTENCY (KHÔNG phải CONTRACT_SEMANTIC_CHANGE)
repair_cycles_used           : 0 / 1
repair_cycles_remaining      : 1
Artifact                     : docs/reviews/TASK-PRA-004-INDEPENDENT-REVIEW-RECORD.md
```

Vòng Independent Review E2 **KHÔNG tiêu** repair cycle: không tồn tại defect
BLOCKING nào trên đường production. Theo §26 chỉ thị và contract mục 24, dọn
số học/văn bản tài liệu (`FIND-PRA004-04`, `FIND-PRA004-09`) **KHÔNG tính**
là blocking repair cycle vì nó không đổi frozen semantics, không đổi phân
loại của bất kỳ requirement nào, và bản FROZEN `46a5cdb` không bị đụng tới.
Hai finding tài liệu đó được gộp vào **MỘT** lần reconciliation ở khâu chuẩn
bị Controlled Integration. Ngân sách `1/1` cycle vẫn còn NGUYÊN cho các vòng
sau (nếu Owner Production Acceptance phát sinh defect).

### Trạng thái tại S103 (Controlled Integration — Docs Reconciliation)

```
Docs Reconciliation          : XONG — FIND-PRA004-04 + FIND-PRA004-09
SEMANTIC_CONTRACT_DELTA      : 0  (14/14 "Yêu cầu:" IDENTICAL; Priority 13
                                REQUIRED · 1 RECOMMENDED không đổi; oracle
                                O-A…O-D, INV-1…INV-7, Owner decisions, Hard
                                Exclusions = IDENTICAL)
PRODUCTION_DELTA_AFTER_E2    : 0  (chỉ 1 file docs bị chạm:
                                docs/tasks/TASK-PRA-004-ban-hang-review-detail.md)
TASK-PRA-004                 : IN_PROGRESS (KHÔNG phải DONE)
CHECK PASS                   : 13/14 — không đổi so với S102
BLOCKING_FINDINGS            : 0
repair_cycles_used           : 0 / 1
repair_cycles_remaining      : 1
```

Docs reconciliation **KHÔNG tiêu** repair cycle — đúng như dự kiến tại S102:
chỉ số học tóm tắt (`FIND-PRA004-04`) và vị trí khối văn bản (`FIND-PRA004-09`)
được sửa; không một `Yêu cầu:`, `Priority:`, oracle hay bất biến nào bị đổi
chữ. Ngân sách `1/1` cycle giữ NGUYÊN cho Owner Production Acceptance.

### Trạng thái tại S104 (Owner Production Acceptance + Final Closeout)

```
Owner Production Acceptance  : XONG — CHECK-PRA004-14 = PASS (E1)
TASK-PRA-004                 : DONE
CHECK PASS                   : 14/14 — 13/13 REQUIRED · 1/1 RECOMMENDED
PRODUCTION_TOTALS            : 40 đơn · 61 dòng · 15 AUTO · 25 CẦN KIỂM TRA
                               (khớp ĐÚNG oracle FROZEN PRA-003)
BLOCKING_FINDINGS            : 0
Non-blocking giữ nguyên      : FIND-PRA004-05/06/07/08 (HARDENING/DEFER,
                               RE-TRIGGER CONDITION không đổi)
FIND-PRA004-04, -09          : RECONCILED (S103, không mở lại)
repair_cycles_used           : 0 / 1  — Owner evidence completion KHÔNG
                               tiêu repair cycle
repair_cycles_remaining      : 1 / 1
Artifact                     : docs/sessions/S104-pra-004-owner-acceptance-closeout.md
```

Owner Production Acceptance **KHÔNG tiêu** repair cycle: không phải một vòng
sửa lỗi, mà là bằng chứng Owner tự thực hiện trên production thật để đóng
một REQUIRED check đã có sẵn trong Completion Gate FROZEN. Ngân sách `1/1`
cycle của `TASK-PRA-004` đóng ở trạng thái **CHƯA TIÊU** — root task lineage
này kết thúc mà không mở một repair cycle nào.

---

## Root Task: TASK-GOLDEN-BASELINE-001

Lineage **mới**, độc lập với `TASK-110`. Ngân sách `EXHAUSTED_PRE_V4.1` của
`TASK-110` **không** áp vào đây, và task này **không** mở `R1-A2` → `R8`.

```
root_task: TASK-GOLDEN-BASELINE-001
effective_risk: HIGH
repair_cycles_allowed: 2
repair_cycles_used: 1
repair_cycles_remaining: 1
```

`HIGH` không đến từ độ khó của việc code — task chỉ thêm test và fixture. Nó
đến từ **Blast Radius theo failure path** (`governance/core/V4_1_POLICY_FREEZE.md` §4):

- **BR-1** — rò rỉ PII vào git history là **bất khả nghịch** (DEC-108 →
  "Can Revisit After: Không bao giờ"); không gate nào chặn sau khi push.
- **BR-2** — expected output sinh từ code hiện tại; nếu code hiện tại đã sai ở
  một path thì Golden đóng băng cái sai đó thành "chuẩn", và mọi lần sửa đúng
  sau này sẽ đỏ rồi bị "sửa" bằng cách sinh lại expected output.

BR-2 được giảm nhẹ — không loại bỏ — bằng GB-1: mọi aggregate mức kỳ phải
khớp evidence đã commit **trước** khi có code này
(`docs/analysis/_evidence/evidence.json` sinh tại TASK-002; CHECK-101-08 đóng
2026-08-23), cộng dòng "Tổng cộng" do chính ERP ghi trong workbook nguồn.

### Scope Lock

```
app/**                : FORBIDDEN — không sửa production code
config/**             : FORBIDDEN
docs/tasks/TASK-110*  : FORBIDDEN
governance/**         : FORBIDDEN
tests/fixtures/baseline/**, tests/test_task110_non_regression.py : FORBIDDEN
```

### Trạng thái

```
REPAIR CYCLE #1           = COMPLETE
INDEPENDENT REVIEW #2     = PASS — ELIGIBLE_FOR_FREEZE
    reviewed_sha           : 85210691702550d83c0fd42fe816be8ca9dde889
    blocking                : 0
    record                  : docs/reviews/TASK-GOLDEN-BASELINE-001-INDEPENDENT-REVIEW-2.md
GB-IR-01                   = CLOSED_BY_REPAIR, INDEPENDENTLY_VERIFIED
FROZEN = YES (DEC-142, 2026-08-27) · MERGED = YES (default SHA
f332a4cb4410b3ca9c71d659d36a3e8f26aa1fa5) · DONE = YES (GB-12 exit criteria
đủ, 2026-08-27)
```

Sub-unit `GB-1` … `GB-12`, và bất kỳ `GB-IR-xx` nào thuộc cùng lineage này,
**không** có ngân sách riêng và không reset ngân sách.

cycles:
- id: cycle-1
  base_sha: 4bccf469274dc9ffb32f333e6db475055ddda794
  head_sha: 54a575dde15f2650a27e270ae9a13543bd80e3ca
  opened_by: Independent Review trên 4bccf469… — verdict FAIL, đúng 1 BLOCKING
    finding (GB-IR-01)
  finding: >
    `test_golden_expected_output_is_regenerable_byte_identical` so byte-thô
    TOÀN BỘ file expected JSON, gồm cả `_environment.python`/`pyyaml`/
    `openpyxl` — ba trường advisory. Chạy trên Python 3.12.3 + PyYAML 6.0.3
    (khác môi trường sinh fixture: 3.11.15 + 6.0.1) làm test đỏ dù business
    payload giống hệt. False regression signal, tái hiện được:
    `python3.12 -m pytest tests/test_golden_baseline.py -q` trên `4bccf46`
    -> `50 passed, 2 failed, 2 skipped`.
  fix: >
    Thêm `_strict_bytes()` tái dùng `_comparable()` đã có sẵn; test
    byte-identical giờ so phần STRICT BUSINESS CONTRACT, loại đúng ba trường
    advisory. Không đổi `gb.write()`, không đổi
    `tests/fixtures/golden/expected/*.json`, không đổi fixture `.xlsx`.
    Business payload trước/sau IDENTICAL (hai file expected không hề bị
    chạm — `git diff --stat` rỗng trên `tests/fixtures/golden/expected/` và
    `tests/fixtures/golden/*.xlsx`).
  verification: >
    Suite chạy PASS trên cả Python 3.11.15 (venv sẵn có) và Python 3.12.3
    (venv riêng) sau repair: `58 passed, 2 skipped` cả hai. Full
    `pytest -q`: `697 passed, 11 skipped` (trước `691 passed, 11 skipped`,
    baseline `716ae2e1…` = `639 passed, 9 skipped`) — 0 regression. `app/` và
    `config/` diff = 0. `validate_reference_integrity` vẫn đúng 3 lỗi tiền
    tồn của `TASK-REM-T06`, không có lỗi thứ 4.
  scope: chỉ `tests/test_golden_baseline.py` + entry ledger này. Không sửa
    `app/**`, `config/**`, TASK-110, R1-A1, governance V4.1 core, HB-GB-01…06.

review_events:
- id: independent-review-2
  reviewed_sha: 85210691702550d83c0fd42fe816be8ca9dde889
  verdict: PASS — ELIGIBLE_FOR_FREEZE
  blocking: 0
  gb_ir_01: CLOSED_BY_REPAIR, INDEPENDENTLY_VERIFIED
  consumes_repair_cycle: false
  record: docs/reviews/TASK-GOLDEN-BASELINE-001-INDEPENDENT-REVIEW-2.md
  note: >
    Review chạy ngoài canonical repo; verdict do Owner cung cấp và được ghi
    lại nguyên trạng trong phiên "INDEPENDENT REVIEW #2 — VERDICT RECORDING
    ONLY" (2026-08-27). Không phải một repair cycle mới — remaining vẫn 1,
    unused.

---

## Root Task: TASK-108B

Lineage **mới**, độc lập với `TASK-110` (`EXHAUSTED_PRE_V4.1`) và với
`TASK-GOLDEN-BASELINE-001`. Mở tại `DEC-143` / `OD-108B-01` (2026-08-27).

```
root_task: TASK-108B
effective_risk: HIGH
repair_cycles_allowed: 2
repair_cycles_used: 0
repair_cycles_remaining: 2
```

`HIGH` **không** đến từ độ khó của việc code (số học đơn giản, module nhỏ). Nó
đến từ **Blast Radius theo failure path** (`governance/core/V4_1_POLICY_FREEZE.md` §4):

```
EligibleCosts → EligibleKpiProfit → ConvertedRevenue → % Target → Thưởng → Tổng lương
```

Failure path kết thúc ở **tiền lương của người thật**. Đo trên dữ liệu Golden
production: một quyết định CÓ/KHÔNG duy nhất về `DeliveryCost` dịch chuyển
thưởng **0,8–1,8 triệu VND/người/tháng** (10,94 % lợi nhuận ở 01.2026;
12,16 % ở 06.2026).

### Golden KHÔNG hạ Blast Radius (V4.1 §4.1)

Golden Baseline `ACTIVE` nhưng **không phủ path nào** của `TASK-108B`:

| Path | Golden |
|---|---|
| `EligibleKpiProfit` (số học) | ❌ NOT COVERED — `price_source_distribution = {Pending: 351/180}`, 100 % giá nhập Pending nên profit luôn `None` |
| Bucket `PERSONAL` | ❌ NOT COVERED — fixture 100 % `ADS` ở cả hai kỳ |
| `NOI_THANH_2` / `GIA_DUNG_8` | ❌ NOT COVERED — `product_group_distribution = {DIEN_MAY: 351}` |
| Đơn trộn scheme (118 OrderID) | ❌ NOT COVERED — fixture chỉ 1 scheme |
| `DeliveryCost` tham gia profit | 🟡 PARTIAL — `money.delivery_cost_total` được ghi, nhưng không invariant nào khẳng định có/không vào profit |

Vì vậy **không** hạ bậc; `Effective Risk = HIGH` giữ nguyên. Coverage gap được
báo cáo, **không** sửa Golden (phiên `DEC-143` không chạm
`tests/**`).

### Trạng thái

```
SEMANTIC_DEFINITION   = APPROVED       (DEC-143 + DEC-144; OD-108B-01 + OD-108B-02)
                                       đầy đủ — formula đã được Owner xác nhận
IMPLEMENTATION        = BLOCKED_BY_DEPENDENCY
BLOCKED_BY_DEPENDENCY = [ nguồn AccountingPurchasePrice production chưa xác
                          định kiến trúc — schema RTDB cần Owner làm rõ (DEC-146) ]
IN-SCOPE MECHANISM    = [ confirmed-adjustment source khai báo rỗng ]   ← nội bộ,
                          KHÔNG phải blocker chờ Owner (DEC-144 §5)
repair cycle          = CHƯA MỞ (0 used) — chưa có implementation nào để repair
```

Đường mở khoá: `TASK-105B` (lineage riêng bên dưới) → `TASK-108B` → `TASK-109`.

Sub-unit của lineage này (`108B-*`) **không** có ngân sách riêng, **không**
reset ngân sách, và **không** được tạo lineage mới chỉ để reset (V4.1 §2).
`TASK-109` thuộc lineage riêng, **không** dùng chung ngân sách này.

cycles:
- id: (chưa mở — implementation chưa bắt đầu vì blocker dữ liệu)
  base_sha: N/A
  head_sha: N/A

---

## Root Task: TASK-105B

Lineage **mới**, độc lập với `TASK-108B`, `TASK-110` và
`TASK-GOLDEN-BASELINE-001`. Mở tại `DEC-144` §7 (2026-08-27), trạng thái
**discovery**.

```
root_task: TASK-105B
effective_risk: HIGH
repair_cycles_allowed: 2
repair_cycles_used: 1
repair_cycles_remaining: 1
```

> **Cập nhật 2026-08-28 (S035, `DEC-156` §4 — HB-154-04, Owner Option B).**
> `TASK-105C` **không còn** dùng chung lineage này; nó có root lineage riêng
> (mục "Root Task: TASK-105C" bên dưới). Ngân sách của `TASK-105B`
> **KHÔNG ĐỔI**: `2 allowed / 1 used / 1 remaining`. Cycle `TASK-105B-RC-1`
> vẫn CONSUMED, vẫn thuộc `TASK-105B`, **không** được chuyển sang lineage
> mới và **không** được xoá. Toàn bộ nội dung lịch sử của mục này — kể cả
> các dòng bên dưới còn mô tả `TASK-105C` như phần của lineage `TASK-105B`
> theo kiến trúc `DEC-152` §11 — **giữ nguyên văn** làm bản ghi lịch sử
> (`V4.1` §10). Trạng thái hiện hành của `TASK-105C`: xem mục riêng của nó.

`HIGH` chấm theo **data path** (V4.1 §4), **không** theo tên module — một
adapter/file reader **không** được coi là LOW chỉ vì nó là adapter:

```
Price sai → KpiPurchasePrice sai → EligibleKpiProfit sai → CR sai → KPI/lương sai
```

`Local Risk = LOW-MEDIUM` (đọc file, tra bảng); `Blast Radius = HIGH`.

### Golden KHÔNG hạ Blast Radius (V4.1 §4.1)

Golden hiện `price_source_distribution = {Pending: 351/180}` — **100 %**, nên
profit arithmetic chưa từng được đo. Không có test cụ thể nào phủ đúng failure
path này ⇒ **không hạ bậc**.

Ghi chú coverage (không phải cơ sở hạ bậc): `TASK-105B` **không** cần Golden
fixture/test mới — nó không thêm field vào `WorkingLine` nên `lines_digest` và
`_covered_digest_fields` không đổi, và Golden vẫn chạy `PendingPriceProvider`
mặc định. Việc mở rộng Golden sang profit arithmetic thuộc `TASK-108B`.

### Trạng thái

```
SEMANTIC_READINESS (Q1/Q2/Q3) = READY   (DEC-145 / OD-105B-01 — KHÔNG đổi)
IMPLEMENTATION (FilePriceProvider)  = IMPLEMENTED + SELF-VERIFIED (2026-08-28,
                                phiên "TASK-105B — IMPLEMENTATION") — CHƯA
                                DONE, chờ Independent Review. Vẫn là
                                DEPENDENCY CỨNG cho TASK-105C
                                (HistoricalVendorPriceProvider compose
                                FilePriceProvider, DEC-152 §11). Chi tiết:
                                docs/tasks/TASK-105B-file-price-provider.md

HistoricalVendorPriceProvider (TASK-105C, tên chính thức từ DEC-152)
    SEMANTIC_DEFINITION = COMPLETE
    SCOPE_LOCK           = COMPLETE
    IMPLEMENTATION        = READY (chưa bắt đầu)
    Canonical spec: docs/tasks/TASK-105C-historical-vendor-price-provider.md
    (Scope Lock + Completion Gate 20 check, FROZEN tại DEC-152)
    Dependency riêng, chưa mở task: product identity mapping
    (product_raw ↔ <MÃ> Tracking) — không chặn implement/test provider,
    chặn kết quả không-Pending trên dữ liệu thật.
```

**`DEC-151` (2026-08-27, Owner Decision) — đóng dứt điểm 4/5 câu hỏi cũ
bằng THU HẸP PHẠM VI, không phải bằng trả lời từng câu.** Reports dùng
`phist/<mã>/<NCC>/<ngày>` làm nguồn giá lịch sử DUY NHẤT
(`Price(NCC,D)` = record gần nhất ≤ D, MIN qua các NCC có căn cứ); `inv.cong`
loại khỏi scope Phase 1 (không áp ngược, không bắt buộc xây lịch sử); mã
thiếu căn cứ → `Pending` chủ đích. `DEC-149` OPTION B (capture cả
`_c.min` lẫn `inv.cong`) **không còn là khuyến nghị hiện hành**. Chi tiết:
`DEC-151`, `docs/sessions/S028-task-105c-historical-kpi-price-scope-reduction.md`,
`docs/tasks/TASK-108B-eligible-costs-owner-definition.md` Phần X.

**`DEC-152` (2026-08-27, Owner Decision cuối) — đóng Q1/Q2, Scope Lock +
Completion Gate FROZEN.** Q1 (NCC retired/MIN_LOAI hồi tố) và Q2 (outlier
threshold hồi tố) **CLOSED** — cả hai KHÔNG áp ngược; Phase 1 = MIN qua
mọi candidate hợp lệ, loại sentinel `0`, không lọc gì thêm. Kiến trúc thực
thi: `HistoricalVendorPriceProvider` compose `FilePriceProvider` (đọc file
snapshot bất biến do một script export sinh ra, tách khỏi
`app/modules/pricing/`) — thay hẳn `DEC-149` OPTION B. Canonical task spec
mới: `docs/tasks/TASK-105C-historical-vendor-price-provider.md`. Product
identity mapping (`product_raw` ↔ `<MÃ>`) đặt tên tường minh làm dependency
riêng, không tự vá bằng fuzzy matching. Chi tiết: `DEC-152`,
`docs/sessions/S029-task-105c-final-decision-scope-lock.md`.

*(Đoạn dưới đây — từ `DEC-147` — giữ lại nguyên văn làm bản ghi lịch sử.
Trạng thái CURRENT nằm ở khối trên và ở `DEC-151`, không phải ở đây.)*

**Audit chéo repo (DEC-147, 2026-08-27) — đã trả lời 4/5 câu hỏi cũ.** Đã
audit `hoangvinhkta-creator/Tracking` @ `d177363a`. RTDB chạy chế độ **HYBRID**
(ảnh chụp `board` + lịch sử `phist/<mã>/<NCC>/<YYYY-MM-DD>`) ⇒ điều kiện
`BLOCKING ARCHITECTURE GAP` của `DEC-146` **KHÔNG kích hoạt**. Nhưng phát hiện
**SOURCE MISMATCH**: loại giá có lịch sử là *giá NCC báo*, còn *giá thực nhập*
(`inv.<slot>.gia`/`.lo`) không có lịch sử. Kiến trúc khuyến nghị: OPTION C
(capture bất biến) giao hàng bằng định dạng OPTION D (file 4 cột) ⇒
`FilePriceProvider` **được đề cử trở lại làm production path**.
`RTDBPriceProvider` = `NEEDS_SCHEMA_CHANGE`, không được đề cử. Chi tiết:
`DEC-147`, `docs/sessions/S024-task-105c-rtdb-price-source-audit.md`,
`docs/tasks/TASK-108B-eligible-costs-owner-definition.md` Phần VI.

**Architecture correction (DEC-146) — bối cảnh, đã được `DEC-147` cập nhật.**
Owner sửa tiền đề: Price Master không
phải file tĩnh — nguồn sự thật vận hành là **Firebase RTDB**, biến động liên
tục. Repo **không có** integration Firebase nào (đã quét toàn bộ, kể cả
`pyproject.toml` dependencies và đặc tả gốc) — không có gì để audit từ phía
code, cần Owner cung cấp schema thật. **Điều kiện `BLOCKING ARCHITECTURE GAP`
cho `TASK-108B`** nếu RTDB không lưu lịch sử giá: DEC-121 đòi hỏi tra cứu đúng
giá tại ngày quá khứ của đơn, không phải giá hiện hành — "RTDB đang chạy"
không tự động thoả điều kiện đó. Đề xuất: giữ `PriceProvider` Protocol, thêm
`RTDBPriceProvider` song song với `FilePriceProvider` (không thay thế); vai
trò cụ thể của từng cái chờ Owner xác nhận. Chi tiết:
`docs/tasks/TASK-108B-eligible-costs-owner-definition.md` Phần V.

Sub-unit tách riêng, **không** có ngân sách riêng và **không** reset ngân sách:

```
TASK-105B-Q3  (supplementary zero-price policy — OD-105B-01 §C)
    IMPLEMENTATION = BLOCKED_BY [ TASK-103 Product/Transaction Classification,
                                  hoặc danh sách enumerated do Owner cấp ]
```

Lý do blocker (báo cáo theo đúng dự phòng của `OD-105B-01` §C, không tự phát
minh matcher): `TASK-103` chưa làm; `config/classification.yaml` không tồn tại;
cơ chế duy nhất `is_non_product_line()` tự khai là *noise reduction only*,
**tạm thời** theo HD-110-02, **cấm tune**. Đo trên production: keyword set hiện
hành khớp **36** dòng trong khi đúng 3 nhóm Owner nêu chỉ **34** (dôi
`Phụ Phí`, `Phụ Phí Đổi mới`). Chi tiết:
`docs/tasks/TASK-108B-eligible-costs-owner-definition.md` Phần IV §40.

Discovery và ghi Owner Decision **không** tiêu repair cycle. Sub-unit `105B-*` không có ngân sách
riêng, không reset ngân sách.

**2026-08-28 — IMPLEMENTATION session** (`app/modules/pricing/file_price_provider.py`,
`tests/test_file_price_provider.py`, `docs/tasks/TASK-105B-file-price-provider.md`).
Implementation + self-verification **không tự tiêu** repair cycle (đúng
quy tắc §10 của phiên: "Implementation session chỉ BUILD → SELF-VERIFY →
HANDOFF"). `repair_cycles_remaining` giữ nguyên `2` — cycle chỉ mở nếu một
vòng Independent Review sau đó cho verdict FAIL và cần repair. Chi tiết
đầy đủ + 17 check evidence: `docs/tasks/TASK-105B-file-price-provider.md`.

**2026-08-28 — REPAIR CYCLE #1 mở** (phiên "TASK-105B PRICE-PARSER
MICRO-HARDENING"). Không phải phản ứng với một Independent Review FAIL —
mà là RE-TRIGGER CONDITION đã ghi sẵn tại Freeze (`DEC-153`): sửa
`HB-105B-07` (NaN → `decimal.InvalidOperation` thô) và `HB-105B-08`
(`Infinity` được chấp nhận làm giá hợp lệ) **trước** khi `TASK-105C`
implementation bắt đầu hoặc `FilePriceProvider` activation thật — điều
kiện nào tới trước (chưa điều kiện nào xảy ra; phiên này chủ động chạy
trước để không bị chặn sau). `DEC-153` đã nêu rõ hai đường hợp lệ để sửa
mã đã đóng băng: "một repair cycle mới có thẩm quyền riêng" hoặc một
`COMPLETION GATE CHANGE PROPOSAL`. Phiên này KHÔNG thay đổi bất kỳ mục
Scope Lock/Completion Gate nào (17 check REQUIRED giữ nguyên nội dung) —
vì vậy đi theo đường **repair cycle mới có thẩm quyền riêng**, chính phiên
này là phiên có thẩm quyền đó (được đặt tên tường minh làm
"NEXT AUTHORIZED ACTION" tại `DEC-153`, không tự phát sinh).

Thay đổi duy nhất: một `if not price.is_finite(): raise
InvalidPriceMasterError(reason="non_finite_price")` chèn giữa check
`missing_price` và check `negative_price` trong `_parse_price()` — dùng
đúng phép kiểm hữu hạn canonical của `Decimal` (`Decimal.is_finite()`),
không viết lại parser, không đổi normalization/effective-dating. 26 test
hồi quy mới (`tests/test_file_price_provider.py`, đủ NaN/+Infinity/
-Infinity qua string/float/`Decimal`, cả bề mặt YAML `.nan`/`.inf`, và
non-regression cho giá dương hữu hạn/0/âm hữu hạn).

```
Targeted (test_file_price_provider.py) : 33 → 59 passed (+26 test mới)
Golden (test_golden_baseline.py)       : 58 passed, 2 skipped (không đổi)
Full pytest -q                         : 730 → 756 passed, 11 skipped
                                          (chênh lệch = đúng 26 test mới,
                                          0 regression, 0 skip mới)
4 file production lõi (pipeline.py, price_engine.py, provider.py,
models.py) diff                        : 0
PendingPriceProvider vẫn mặc định pipeline; 0 caller FilePriceProvider
ngoài chính module; 0 code TASK-105C được thêm.
```

`repair_cycles_used: 0 → 1`, `repair_cycles_remaining: 2 → 1`.

cycles:
- id: TASK-105B-RC-1
  base_sha: c22cef8b47ac4cd71ef49609066a362c9e604313
  head_sha: 7f7048d65619c2c2198c99ccbfb073d6cb97ebe2
  scope: app/modules/pricing/file_price_provider.py, tests/test_file_price_provider.py
  trigger: RE-TRIGGER CONDITION đã ghi tại DEC-153 (HB-105B-07/HB-105B-08),
    không phải Independent Review FAIL
  status: CLOSED_BY_REPAIR, INDEPENDENTLY_VERIFIED — Codex Independent Review
    PASS — REPAIR VERIFIED tại 9241ccfca9a8b0159b347f4d1171c0caa37eecad;
    reviewed lineage integrated qua integration/v4-1-task-105b-rc1.

**2026-08-28 — `DEC-154` governance/spec reconciliation.** Không sửa
production code/test/config, không activate provider, không mở Repair Cycle
#2. Current role của `TASK-105B` chuyển thành Public Purchase effective-dated
provider foundation; frozen implementation/history không đổi. Remaining
`HB-105B-03/05/06/10` được audit trigger riêng và đều `triggered now = NO`.
Budget giữ nguyên:

```text
repair_cycles_allowed   = 2
repair_cycles_used      = 1
repair_cycles_remaining = 1
```

---

## Root Task: TASK-105C

Lineage **root riêng**, cấp bởi Owner tại `DEC-156` §4 (2026-08-28,
`HB-154-04` — Owner Option B). Ngân sách theo bảng đã freeze `V4.1` §2
(`HIGH/CRITICAL = 2`).

```
root_task: TASK-105C
effective_risk: HIGH
repair_cycles_allowed: 2
repair_cycles_used: 0
repair_cycles_remaining: 2
cycles: []
status: BLOCKED / NOT AUTHORIZED — Scope Lock REOPENED_BY_DEC-154;
        Completion Gate CHANGE_PROPOSAL_OPEN, NOT FROZEN;
        implementation not authorized
```

Failure path:

```text
sai HistoricalVendorMin (ngày/sentinel/candidate)
→ sai KpiPurchasePrice
→ sai EligibleKpiProfit → sai CR → sai KPI/lương
```

Golden hiện dùng `PendingPriceProvider` và không phủ nhánh giá này, nên
không hạ Blast Radius theo `V4.1` §4.1.

### Lineage trước đó — bản ghi lịch sử, KHÔNG xoá

`TASK-105C` từng dùng chung lineage `TASK-105B` (xem mục "Root Task:
TASK-105B" phía trên, giữ nguyên văn). Lý do DUY NHẤT của việc dùng chung là
kiến trúc `DEC-152` §11: `HistoricalVendorPriceProvider` **compose**
`FilePriceProvider`. `DEC-154` §13 đã gỡ composition đó — hai task nay là hai
nhánh provider song song, không còn dependency cứng.

Vì sao đây **không** phải một lineage mở "để reset ngân sách" theo nghĩa
`V4.1` §2 cấm:

```text
(a) Owner cấp tường minh (DEC-156 §4), không phải agent tự tách.
(b) Căn cứ là ARCHITECTURAL — lý do duy nhất của lineage dùng chung đã bị
    DEC-154 §13 gỡ bỏ.
(c) KHÔNG ngân sách đã tiêu nào được hoàn lại: TASK-105B-RC-1 vẫn CONSUMED
    ở TASK-105B (2/1/1). TASK-105C mở ở 0 used vì nó CHƯA TỪNG tiêu cycle
    nào của chính nó — RC-1 là repair NaN/vô cực trong FilePriceProvider,
    code thuộc nhánh Public Purchase, không thuộc TASK-105C.
(d) Historical evidence, review record, freeze record: giữ nguyên toàn bộ.
```

Artifact hiện có của lineage:

- `docs/tasks/TASK-105C-historical-vendor-price-provider.md`
- `DEC-151`, `DEC-152`, `DEC-154` §13, `DEC-156` §4 trong
  `PROJECT/PROJECT_DECISIONS.md`

---

## Root Task: TASK-105E

Lineage **mới**, cấp cùng lúc với task ID tại `DEC-156` §5 (2026-08-28).
Ngân sách theo bảng đã freeze `V4.1` §2 (`HIGH/CRITICAL = 2`) — cấp lineage
là thao tác cơ học theo bảng, không phải một quyết định ngân sách riêng.

```
root_task: TASK-105E
effective_risk: HIGH
repair_cycles_allowed: 2
repair_cycles_used: 0
repair_cycles_remaining: 2
cycles: []
status: IMPLEMENTED (Session 1, S061 2026-08-29) — Scope Lock Session 1 đã
        SOẠN (chưa freeze); Completion Gate vẫn CHƯA soạn/CHƯA freeze;
        implementation Session 1 được cấp phép tường minh bởi chỉ thị mở
        phiên "TASK-105E — PRODUCTION PRICE COMPOSITION, SESSION 1/2".
        Independent Review (Session 2) CHƯA chạy.
```

**S061 KHÔNG tiêu cycle nào.** `repair_cycles` đếm các vòng repair SAU một
Independent Review (`V4.1` §3); S061 là implementation Session 1 và chưa có
review nào để repair. `cycles: []` giữ nguyên, `remaining = 2`.

Failure path:

```text
chọn sai nguồn giá / sai thứ tự P00–P11 / mất provenance
→ sai KpiPurchasePrice
→ sai EligibleKpiProfit → sai CR → sai KPI/lương
```

Golden hiện dùng `PendingPriceProvider` và không phủ price composition path,
nên không hạ Blast Radius theo `V4.1` §4.1.

Artifact hiện có của lineage:

- `docs/tasks/TASK-105E-price-resolution-composition.md`
- `DEC-156` §5 trong `PROJECT/PROJECT_DECISIONS.md`

Không cycle nào được mở bởi việc cấp task ID. `cycles: []`.

---

## Root Task: TASK-105D

```
root_task: TASK-105D
effective_risk: HIGH
repair_cycles_allowed: 2
repair_cycles_used: 1
repair_cycles_remaining: 1
last_independent_review:
    - id: TASK-105D-IMPL-REVIEW-1
      session: S041 (2026-08-28)
      branch: review/task-105d-implementation-1
      reviewed_target_sha: e6252c06347ed5305fc32a77706a3a63f5a950cf
      reviewed_base_sha: 222844dfb5cf576238fda4cc913ef2095789b4eb
      role_separation: independent reviewer; KHÔNG kế thừa PASS của S040
      gate_set_sha256_reproduced: true
      frozen_checks: 32 / 32 PASS (thực thi độc lập)
      adversarial_a_to_t: 20 / 20 PASS (bộ test riêng của reviewer)
      regression: 0 (Golden 58/2 không đổi; full 756 -> 930; delta +174)
      verdict: FAIL — REPAIR REQUIRED
      findings: 1 BLOCKING / 7 HARDENING / 3 OUT_OF_SCOPE
      blocking: B-01 — thiếu khoá file; check-then-append race ở đúng biên
                "một máy" mà data contract §11.1 tuyên bố phủ; INV-59 không
                thi hành được qua biên tiến trình
      repair_cycle_consumed: 0   (independent review không tiêu thụ cycle)
      recommendation: mở Repair Cycle #1
      evidence: docs/reviews/TASK-105D-INDEPENDENT-IMPLEMENTATION-REVIEW-1.md
    - id: TASK-105D-IMPL-REVIEW-2
      session: S043 (2026-08-28)
      branch: review/task-105d-implementation-2
      reviewed_target_sha: a09823506fc17b7903e44be848672a18f92bc6ee
      reviewed_repair_sha: 1cc96a99638326513b26280b72bbeb3bce9d454d
      reviewed_original_sha: e6252c06347ed5305fc32a77706a3a63f5a950cf
      reviewed_base_sha: 222844dfb5cf576238fda4cc913ef2095789b4eb
      review1_evidence_read: 58323e2e59382e2ce4816453cfaaa5d31deba3db
                             (đọc bằng git show — KHÔNG merge nhánh review-1)
      role_separation: reviewer KHÔNG phải tác giả S040 và KHÔNG phải tác giả
                       S042; KHÔNG kế thừa tuyên bố "CODE-LEVEL RESOLVED"
      b01_reproduced_on_old_code: true   (10/10 vòng: 2 APPLIED + integrity
                                          error vĩnh viễn khi mở lại)
      b01_contention_after_repair: 135 vòng / 7 kịch bản, tiến trình HĐH thật
                                   (spawn + multiprocessing.Barrier, không sleep)
                                   n=2/4/8; request-id giống và khác;
                                   append vs rebuild_index; 0 bất thường, 0 flake
      b01_closure_matrix: 10 / 10 PASS
      b01_disposition: CLOSED
      mutation_paths_enumerated_independently: true
                       (quét tĩnh toàn app/: store.py là module DUY NHẤT ghi
                        xuống đĩa; 0 đường ghi bền vững bypass biên giao dịch)
      anti_tautology: 25 test mới chạy tại e6252c0 -> 19 failed
      gate_set_sha256_reproduced: true   (0444e58c…, 57.614 byte, khớp tuyệt đối)
      frozen_checks: 32 / 32 PASS (thực thi độc lập)
      adversarial_a_to_t: 20 / 20 PASS (truy vết độc lập; N bổ sung bằng 135
                          vòng đa tiến trình)
      targeted_105d: 199 passed
      golden: 58 passed, 2 skipped (KHÔNG ĐỔI)
      full_suite: 955 passed, 11 skipped (930 -> 955, delta +25 xác minh hai chiều)
      regression: 0
      performance: chi phí khoá KHÔNG đo được trên nhiễu
                   (RC-1 6,795 s vs pre-repair 6,969 s ở n=800) — H-04 KHÔNG mở lại
      validators: 4/5 PASS; reference_integrity 3 (baseline 222844d và e6252c0)
                  -> 4 tại RC-1 = ĐÚNG MỘT lỗi mới (H2-02)
      verdict: PASS WITH HARDENING — RC-1 VERIFIED / ELIGIBLE FOR CONTROLLED
               INTEGRATION
      findings: 0 BLOCKING / 5 HARDENING mới / 4 OUT_OF_SCOPE
      hardening_new: H2-01 (_consume mutate trước khi đẩy _log_offset),
                     H2-02 (1 reference_integrity mới),
                     H2-03 (event commit nhưng caller nhận exception — CÓ SẴN),
                     H2-04 (test_both_orderings_… không assert điều tên nó nói),
                     H2-05 (truncate log về rỗng không bị store mở mới phát hiện)
      hardening_carried_open: H-01, H-02, H-03, H-04, H-05, H-06, H-07,
                     HB-105D-F2-01, HB-105D-F2-02, HB-105D-F2-03  (10/10 OPEN)
      hardening_closed: 0
      promoted_to_blocking: 0
      h07_conclusion: NOT_TESTED trong khối gate chặn DONE, KHÔNG chặn
                      integration; reconciliation bắt buộc TRƯỚC DONE
      repair_cycle_consumed: 0   (review sửa 0 dòng app/**, tests/**, config/**)
      repair_cycle_2_opened: NO
      rc1_branch_mutated: NO
      merged_default: NO
      evidence: docs/reviews/TASK-105D-INDEPENDENT-IMPLEMENTATION-REVIEW-2.md
                docs/sessions/S043-task-105d-independent-implementation-review-2.md
status: READY — specification complete + data contract complete (S034/
        DEC-155) + Owner ratified (S035/DEC-156) + Completion Gate Change
        Proposal applied (S037/DEC-157) + COMPLETION GATE FROZEN (S038,
        2026-08-28, V4.1 §12); Ready Gate blocker = 0;
        READY ≠ IMPLEMENTED ≠ DONE — implementation not authorized, và
        DEC-157 §2 chặn implementation trước divergence decision
freeze_attempts:
    - id: TASK-105D-FREEZE-1
      session: S036 (2026-08-28)
      reviewed_base_sha: 9cd871488a6baebf6b80737f42e2137a27887cef
      verdict: FAIL — freeze TỪ CHỐI; Ready Gate vẫn BLOCKED
      findings: 5 BLOCKING / 5 HARDENING / 3 OUT_OF_SCOPE
      repair_cycle_consumed: 0
      evidence: docs/reviews/TASK-105D-FREEZE-FINALIZATION-REVIEW.md
    - id: TASK-105D-FREEZE-2
      session: S038 (2026-08-28)
      reviewed_base_sha: be835b1b1b03d4e8d21656c3624b6e4bc964b7a1
      authority: V4.1 §12 + DEC-157 §2 (Option C cho phép ĐÚNG MỘT retry;
                 đây là retry đó — scope Option C nay dùng hết)
      role_separation: independent reviewer; KHÔNG kế thừa kết luận S037;
                 ma trận 32 gate dựng lại từ văn bản canonical
      verdict: PASS WITH HARDENING — Completion Gate FROZEN; TASK-105D READY
      findings: 0 BLOCKING / 4 HARDENING / 3 OUT_OF_SCOPE
      hardening_new: HB-105D-F2-01, HB-105D-F2-02, HB-105D-F2-03
      hardening_carried: H-05 (phân loại lại độc lập = HARDENING)
      testable: 32/32
      deterministic: 32/32
      contradiction: 0
      adversarial_A_T: 20/20 PASS
      gate_count: 32
      gate_set_sha256: 0444e58c02b04804a116c140af722ffc29ea64adf468aa6c93794c4408a5c877
      production_diff: 0 dòng
      golden: 58 passed, 2 skipped
      full_suite: 756 passed, 11 skipped
      repair_cycle_consumed: 0
      frozen: YES
      evidence: docs/reviews/TASK-105D-FREEZE-FINALIZATION-REVIEW-2.md
gate_revisions:
    - id: TASK-105D-GATE-REVISION-1
      session: S037 (2026-08-28)
      base_sha: 1676e1d173ff6afdbbaa2cedcf07fc06346955ce
      authority: DEC-157 (Owner Decision A — giữ đúng 32 gate)
      resolved: F-01, F-02, F-03, F-04, F-05  (5/5 BLOCKING)
                + H-01, H-03 (ĐÓNG); H-02 một phần, H-04 nạp thêm
      still_open: H-05 (đổi data contract §6.7 — ngoài thẩm quyền phiên này)
      gate_count_before_after: 32 / 32
      gates_added: 0
      gates_removed: 0
      evidence_level_downgrades: 0
      evidence_level_upgrades: 2   (CHECK-105D-10, CHECK-105D-21: E1 → E2)
      adversarial_cases_covered: 20/20  (trước: 14 ĐẠT / 1 MỘT PHẦN / 5 KHÔNG ĐẠT)
      production_diff: 0 dòng (app/**, tests/**, config/**, tools/**,
                       scripts/**, pyproject.toml)
      repair_cycle_consumed: 0
      frozen: NO
      evidence: docs/reviews/TASK-105D-COMPLETION-GATE-CHANGE-PROPOSAL.md
```

`repair_cycles_used` giữ nguyên `0`. Một **independent freeze review** không
tiêu repair cycle: `V4.1` §3 tính cycle theo **lần sửa** (cumulative repair
diff), và `S036` không sửa một dòng nào của gate, code hay test — nó chỉ ghi
finding.

Cập nhật 2026-08-28 (`S037`, `DEC-157` — Gate Revision #1): `repair_cycles_used`
**vẫn giữ `0`**. `S037` có sửa gate, nhưng `V4.1` §3 tính cycle theo cumulative
**repair diff của implementation** trên một defect `BLOCKING`, và `S037` sửa
0 dòng `app/**`, `tests/**`, `config/**`, `tools/**`, `scripts/**`,
`pyproject.toml`. `V4.1` cấm mở Repair Cycle chỉ vì documentation/gate issue
trừ khi Owner quyết định khác — Owner **không** quyết định khác (`DEC-157` §4).
Ngân sách `TASK-105D`: `2 allowed / 0 used / 2 remaining`.

Cập nhật 2026-08-28 (`S038`, Freeze Finalization retry): `repair_cycles_used`
**vẫn giữ `0`**. Một independent freeze review không tiêu repair cycle
(`V4.1` §3 — cycle tính theo cumulative repair diff của implementation);
`S038` sửa 0 dòng `app/**`, `tests/**`, `config/**`, `tools/**`, `scripts/**`,
`pyproject.toml`, và 0 dòng semantics của gate (`GATE_SET_SHA256` không đổi
trước/sau commit của phiên). Ngân sách `TASK-105D` giữ nguyên
`2 allowed / 0 used / 2 remaining`.

Cập nhật 2026-08-28 (`S041`, Independent Implementation Review #1):
`repair_cycles_used` **vẫn giữ `0`** — review ghi finding, không sửa code.
Verdict `FAIL — REPAIR REQUIRED`, 1 BLOCKING (`B-01`).

Cập nhật 2026-08-28 (`S042`, **Repair Cycle #1 — MỞ VÀ TIÊU THỤ**):
`repair_cycles_used` `0 → 1`; `repair_cycles_remaining` `2 → 1`. Đây là lần
đầu tiên `TASK-105D` tiêu một cycle: `V4.1` §3 tính cycle theo cumulative
repair diff của implementation, và `S042` **có** sửa `app/**` + `tests/**`
để đóng một defect `BLOCKING`. Owner đã cấp phép tường minh khi mở phiên, kèm
Owner Decision cho `B-01` = option (a) (giữ hợp đồng concurrency "một máy",
sửa implementation bằng khoá file thật; KHÔNG thu hẹp `§11.1`; KHÔNG sửa
Completion Gate đã freeze). Toàn bộ các lần lặp bên trong cùng diff repair
này thuộc CÙNG cycle, không mở cycle mới.

Cập nhật 2026-08-28 (`S043`, **Independent Implementation Review #2**):
`repair_cycles_used` **vẫn giữ `1`**; `repair_cycles_remaining` **vẫn giữ `1`**.
Một independent review không tiêu repair cycle (`V4.1` §3 — cycle tính theo
cumulative repair diff của implementation): `S043` sửa 0 dòng `app/**`,
`tests/**`, `config/**`, `tools/**`, `scripts/**`, `pyproject.toml`, và 0 byte
của khối gate (`GATE_SET_SHA256` tái lập khớp tuyệt đối sau khi phiên ghi
artifact). Verdict `PASS WITH HARDENING`; `B-01` = `CLOSED` (10/10 tiêu chí
đóng, xác minh độc lập). **Repair Cycle #2 KHÔNG được mở** — 5 finding mới đều
là `HARDENING`, và `V4.1` §3/§7 không cho reviewer tự mở cycle.

`H2-01` nằm **trong** cumulative repair diff của `TASK-105D-RC-1`
(`store.py::_consume`, mã do chính RC-1 tạo). Theo `V4.1` §3, nếu Owner quyết
định đóng nó thì việc sửa thuộc **CÙNG** `TASK-105D-RC-1`, `base_sha` **không**
reset và **không** mở cycle mới — `head_sha` của cycle tiến lên SHA mới.

Ngân sách `TASK-105D` sau `S043`: `2 allowed / 1 used / 1 remaining` (KHÔNG ĐỔI).

```
cycles:
    - id: TASK-105D-RC-1
      session: S042 (2026-08-28)
      branch: task/task-105d-rc1
      base_sha: e6252c06347ed5305fc32a77706a3a63f5a950cf
      head_sha: 1cc96a99638326513b26280b72bbeb3bce9d454d
      trigger: B-01 (Independent Implementation Review #1, evidence
               58323e2e59382e2ce4816453cfaaa5d31deba3db)
      owner_decision: option (a) — giữ hợp đồng, sửa implementation
      repair_scope: inter-process persistence concurrency / file locking
      files_changed: app/modules/product/identity/store.py
                     tests/test_105d_interprocess_concurrency.py (mới)
      gate_set_sha256: 0444e58c02b04804a116c140af722ffc29ea64adf468aa6c93794c4408a5c877
                       (KHỚP — khối gate 0 byte thay đổi)
      targeted_105d: 174 -> 199 passed (+25)
      golden: 58 passed, 2 skipped (KHÔNG ĐỔI)
      full_suite: 930 -> 955 passed, 11 skipped (delta = đúng 25 test mới)
      regression: 0
      b01_disposition: CODE-LEVEL RESOLVED / READY FOR INDEPENDENT RE-REVIEW
      hardening_repaired: 0 (H-01…H-07, HB-F2-01…03 giữ nguyên OPEN)
      merged_default: NO
      evidence: docs/reviews/TASK-105D-RC-1-REPAIR-RECORD.md
                docs/sessions/S042-task-105d-repair-cycle-1.md
```

Ngân sách `TASK-105D` sau `S042`: `2 allowed / 1 used / 1 remaining`.

Cập nhật 2026-08-28 (`S043`, Independent Implementation Review #2):
`repair_cycles_used` **giữ nguyên `1`** — review sửa 0 dòng `app/**`,
`tests/**`, `config/**`. Verdict `PASS WITH HARDENING`, `B-01` = `CLOSED`,
0 BLOCKING. **KHÔNG** mở Repair Cycle #2.

Cập nhật 2026-08-28 (`S044`, **CONTROLLED INTEGRATION** — `V4.1` §8 Option A):
`repair_cycles_used` **giữ nguyên `1`**; `repair_cycles_remaining` **giữ nguyên
`1`**. Controlled integration KHÔNG tiêu thụ repair cycle: `V4.1` §3 tính cycle
theo cumulative repair diff của implementation, và `S044` sửa 0 dòng `app/**`,
`tests/**`, `config/**`, `tools/**`, `scripts/**`, `pyproject.toml`. Cycle
`TASK-105D-RC-1` giữ nguyên trạng thái CONSUMED — **KHÔNG** reset, **KHÔNG**
mở cycle mới.

```
integration:
    - id: TASK-105D-CONTROLLED-INTEGRATION
      session: S044 (2026-08-28)
      authority: Owner Decision — V4.1 §8 Option A (INTEGRATE EARLY)
      branch: integration/v4-1-task-105d-implementation
      starting_default_sha: 222844dfb5cf576238fda4cc913ef2095789b4eb
      implementation_sha: e6252c06347ed5305fc32a77706a3a63f5a950cf
      rc1_repair_sha: 1cc96a99638326513b26280b72bbeb3bce9d454d
      rc1_final_sha: a09823506fc17b7903e44be848672a18f92bc6ee
      review1_sha: 58323e2e59382e2ce4816453cfaaa5d31deba3db
      review2_sha: 4d44ec4a292513f78614d2040ae1fba802747d7c
      merge_method: git merge --no-ff x3 (ancestry-preserving)
                    KHÔNG squash / KHÔNG rebase / KHÔNG cherry-pick
      conflicts: 2 file / 4 hunk — TOÀN BỘ là governance state
                 (PROJECT_PROGRESS.md, REVIEW_BUDGET_LEDGER.md)
                 0 xung đột chạm app/**, tests/**, frozen gate, data contract
      historical_verdicts_rewritten: NO
                 (khối S041 giữ NGUYÊN VĂN 52/52 dòng — diff vs 58323e2e = rỗng)
      repair_budget_records_discarded: NO
      gate_set_sha256_before: 0444e58c02b04804a116c140af722ffc29ea64adf468aa6c93794c4408a5c877
      gate_set_sha256_after:  0444e58c02b04804a116c140af722ffc29ea64adf468aa6c93794c4408a5c877
      frozen_gate_definition_mutated: NO
      b01: CLOSED (kế thừa từ S043 — closure matrix 10/10)
      gate_execution_evidence: TÁCH RỜI, 32/32 PASS
                 (TASK-105D-GATE-EXECUTION-RECORD.md + Review #2 §17.2)
      h07: VẪN OPEN — reconciliation bắt buộc TRƯỚC DONE, KHÔNG chặn integration
      production_equivalence_to_a0982350: BYTE-IDENTICAL
                 (diff app/tests/config/tools/scripts/pyproject/docs/spec/
                  docs/tasks = rỗng; store.py sha256 c3d3b09d… khớp)
      targeted_105d: 199 passed
      golden: 58 passed, 2 skipped (KHÔNG ĐỔI)
      full_suite: 955 passed, 11 skipped (KHÔNG ĐỔI)
      regression: 0
      validators: structure/project_state/evidence/task_completion = PASS;
                  reference_integrity = 3 issue = ĐÚNG BẰNG baseline canonical
                  222844df (chỉ TASK-REM-T06)
      h2_02: RESOLVED_BY_INTEGRATION (hợp nhất artifact Review #1 làm tham
             chiếu tự phân giải; validator KHÔNG bị sửa, tham chiếu KHÔNG bị
             viết lại để né lỗi) — KHÔNG tính là Repair Cycle #2
      hardening: 14 OPEN + 1 RESOLVED_BY_INTEGRATION; 0 repaired; 0 promoted
      repair_cycle_consumed: 0
      repair_cycle_2_opened: NO
      task_105d_done: NO (integration KHÔNG ngụ ý DONE)
      task_105e_implemented: NO
      file_price_provider_activated: NO
      tracking_touched: NO
      production_data_touched: NO
      merged_default: YES
      evidence: docs/sessions/S044-task-105d-controlled-integration.md
```

Ngân sách `TASK-105D` sau `S044`: `2 allowed / 1 used / 1 remaining`
(**KHÔNG ĐỔI**).
`head_sha` `1cc96a9` là commit mang toàn bộ diff repair (`store.py` +
`tests/test_105d_interprocess_concurrency.py`); commit ghi chính dòng
`head_sha` này nằm ngay sau nó và không chứa thay đổi code/test. Nếu repair
tiếp tục trong CÙNG cycle thì `head_sha` tiến lên, `base_sha` KHÔNG reset và
KHÔNG mở cycle mới (`V4.1` §3). Xác định phạm vi cycle bằng
`git diff e6252c06..1cc96a99 --name-only`.

Cập nhật 2026-08-28 (`S045`, **H-07 GATE EXECUTION RECONCILIATION**):
`repair_cycles_used` **giữ nguyên `1`**; `repair_cycles_remaining` **giữ
nguyên `1`**. Phiên này là governance/documentation reconciliation thuần
tuý — 0 dòng `app/**`, `tests/**`, `config/**`, `tools/**`, `scripts/**`,
`pyproject.toml`. **KHÔNG** mở Repair Cycle #2.

```
h07_reconciliation:
    - id: TASK-105D-H07-RECONCILIATION
      session: S045 (2026-08-28)
      authority: Owner Decision — DEC-159 (Option (b), khuyến nghị của
                 Independent Review #2 §23)
      gate_set_sha256_before: 0444e58c02b04804a116c140af722ffc29ea64adf468aa6c93794c4408a5c877
      gate_set_sha256_after:  0444e58c02b04804a116c140af722ffc29ea64adf468aa6c93794c4408a5c877
      frozen_gate_definition_mutated: NO
      interpretive_layer: RESOLVED — Gate Execution Record tách rời (bind
                 đúng GATE_SET_SHA256, đúng CHECK-105D-01..32, PASS, đúng
                 Evidence Level, tái lập độc lập 2 lần) được công nhận
                 thoả REQUIRED-check-PASS của TASK_COMPLETION_GATE_STANDARD
                 = "Effective Completion Status", tách biệt "Frozen Gate
                 Status" (freeze-time metadata, NOT_TESTED KHÔNG ĐỔI)
      validator_layer: OPEN — governance/scripts/governance/
                 validate_task_completion.py yêu cầu literal Status: PASS
                 trong từng khối REQUIRED, không có khái niệm execution
                 record tách rời; sẽ FAIL nếu TASK-105D.Status=DONE trong
                 khi 32 khối vẫn NOT_TESTED
      h07_disposition: PARTIALLY RECONCILED (interpretive layer RESOLVED,
                 validator-alignment layer OPEN — mới, phạm vi hẹp)
      h07_closed: NO
      task_105d_done: NO (không đổi bởi phiên này)
      task_105d_eligibility: STILL_BLOCKED_BEFORE_DONE (điều kiện đóng #7
                 của H-07 chưa thoả — xem session evidence)
      repair_cycle_consumed: 0
      repair_cycle_2_opened: NO
      production_diff: 0 dòng
      evidence: docs/sessions/S045-task-105d-h07-reconciliation-and-capability-governance.md
                PROJECT/PROJECT_DECISIONS.md DEC-159
```

Ngân sách `TASK-105D` sau `S045`: `2 allowed / 1 used / 1 remaining`

Cập nhật 2026-08-28 (`S046`, **H-07 VALIDATOR ALIGNMENT — tooling**):
`repair_cycles_used` **giữ nguyên `1`**; `repair_cycles_remaining` **giữ
nguyên `1`**. Phiên này sửa đúng một file tooling
(`governance/scripts/governance/validate_task_completion.py`) + thêm một
file test (`tests/test_governance_validate_task_completion.py`) — 0 dòng
`app/**`, `config/**`, `docs/tasks/**`, `governance/core/**`. Không phải
repair diff của implementation `TASK-105D`; **KHÔNG** mở Repair Cycle #2.

```
h07_validator_alignment:
    - id: TASK-105D-H07-VALIDATOR-ALIGNMENT
      session: S046 (2026-08-28)
      authority: Owner Decision — chỉ thị mở phiên "TASK-105D H-07 —
                 VALIDATOR ALIGNMENT", theo đúng "Can Revisit After" của
                 DEC-159
      gate_set_sha256_before: 0444e58c02b04804a116c140af722ffc29ea64adf468aa6c93794c4408a5c877
      gate_set_sha256_after:  0444e58c02b04804a116c140af722ffc29ea64adf468aa6c93794c4408a5c877
      frozen_gate_definition_mutated: NO
      validator_layer: RESOLVED — validate_task_completion.py implement
                 đúng 8 điều kiện binding DEC-159 §1 (Layer 2 / Gate
                 Execution Record); Layer 1 (Status: PASS literal) không
                 đổi hành vi; fail-closed trên thiếu record/sai hash/thiếu
                 check ID/FAIL/thiếu lineage/duplicate-ambiguous
      tests_added: tests/test_governance_validate_task_completion.py
                 (10 test, 10/10 PASS)
      real_data_simulation: chạy trên bản sao trong bộ nhớ/thư mục tạm của
                 chính docs/tasks/TASK-105D-product-identity-resolver.md
                 (patch Status: DONE, không mutate file thật) — 32/32 PASS
                 qua docs/reviews/TASK-105D-GATE-EXECUTION-RECORD.md thật
      bug_found_and_fixed_in_session: CÓ — draft đầu tra cứu check ID bằng
                 nguyên văn heading (có mô tả theo sau ID) thay vì token ID
                 trần; mô phỏng trên dữ liệu thật phát hiện 32/32 FAIL cho
                 tới khi sửa. Thêm test hồi quy khoá lại.
      h07_disposition: RECONCILED (cả hai lớp)
      h07_closed: YES
      task_105d_done: NO (không đổi bởi phiên này — ngoài thẩm quyền)
      task_105d_eligibility: ELIGIBLE_FOR_DONE_REVIEW (điều kiện #7 đóng;
                 4 điều kiện completion khác chưa đánh giá)
      repair_cycle_consumed: 0
      repair_cycle_2_opened: NO
      production_diff: 0 dòng (app/**, config/**, docs/tasks/**, governance/core/**)
      canonical_validators: validate_structure PASS, validate_project_state
                 PASS, validate_reference_integrity FAIL (3 issue tiền tồn
                 TASK-REM-T06, không đổi), validate_evidence PASS,
                 validate_task_completion PASS (Checked 6 DONE task(s),
                 không đổi — TASK-105D vẫn READY nên Layer 2 chưa kích hoạt
                 trên dữ liệu thật)
      full_suite: 965 passed, 11 skipped (0 failed, 0 regression)
      evidence: docs/sessions/S046-task-105d-h07-validator-alignment.md
                PROJECT/PROJECT_DECISIONS.md DEC-161
```

Ngân sách `TASK-105D` sau `S046`: `2 allowed / 1 used / 1 remaining`
(**KHÔNG ĐỔI**).

```
final_completion_review:
    - id: TASK-105D-FINAL-COMPLETION-REVIEW
      session: S047 (2026-08-28)
      authority: chỉ thị mở phiên "TASK-105D FINAL COMPLETION REVIEW" —
                 phiên đóng vai trò Independent Review cho chính hành động
                 "đặt Status: DONE" (điều kiện DEC-161 §6 nêu còn thiếu)
      gate_set_sha256_before: 0444e58c02b04804a116c140af722ffc29ea64adf468aa6c93794c4408a5c877
      gate_set_sha256_after:  0444e58c02b04804a116c140af722ffc29ea64adf468aa6c93794c4408a5c877
      frozen_gate_definition_mutated: NO
      h07: CLOSED (xác minh lại 8/8 điều kiện binding DEC-159 §1 + mô
                 phỏng validator 32/32 PASS, không mutate file task thật)
      unresolved_blocking: 0 (B-01 CLOSED, H2-02 RESOLVED_BY_INTEGRATION)
      open_hardening: 14 (không mục nào promote lên BLOCKING)
      inv_01_87: PARTIAL — INV-81/INV-82 evidence không đủ (H-06, OPEN từ
                 S041, xác minh lại trực tiếp mã test tại S047)
      task_105d_done: NO — NEAREST_REMAINING_BLOCKING_CONDITION = Exit
                 Criteria INV-01…INV-87 chưa thoả cho INV-81/INV-82
      repair_cycle_consumed: 0
      repair_cycle_2_opened: NO
      production_diff: 0 dòng (app/**, config/**, Tracking)
      canonical_validators: validate_structure PASS, validate_project_state
                 PASS, validate_reference_integrity FAIL (3 issue tiền tồn
                 TASK-REM-T06, không đổi), validate_evidence PASS,
                 validate_task_completion PASS (Checked 6 DONE task(s),
                 không đổi — TASK-105D vẫn READY)
      full_suite: 965 passed, 11 skipped (0 failed, 0 regression)
      targeted: 199 passed; golden: 58 passed, 2 skipped
      registration_guard: SET A 13→13, SET B 22→22, new_registered_task_ids = 0
      evidence: docs/sessions/S047-task-105d-final-completion-review.md,
                docs/reviews/TASK-105D-FINAL-COMPLETION-REVIEW.md
```

Ngân sách `TASK-105D` sau `S047`: `2 allowed / 1 used / 1 remaining`
(**KHÔNG ĐỔI**).

Failure path:

```text
sai namespace/identity/cutover
→ sai provider/price provenance
→ sai KpiPurchasePrice
→ sai KPI/lương
```

Golden hiện dùng `PendingPriceProvider` và không phủ product-resolution/price
composition path, nên không hạ Blast Radius theo V4.1 §4.1.

Artifact hiện có của lineage (8):

- `docs/tasks/TASK-105D-product-identity-resolver.md` (S032/`DEC-154`)
- `DEC-154` trong `PROJECT/PROJECT_DECISIONS.md`
- `docs/spec/TASK-105D-DATA-CONTRACT.md` (S034/`DEC-155`)
- `DEC-155` trong `PROJECT/PROJECT_DECISIONS.md`
- `DEC-156` trong `PROJECT/PROJECT_DECISIONS.md` (S035, Owner Ratification)
- `docs/reviews/TASK-105D-FREEZE-FINALIZATION-REVIEW.md` (S036, artifact #6)
- `docs/reviews/TASK-105D-COMPLETION-GATE-CHANGE-PROPOSAL.md` (S037, #7)
- `DEC-157` trong `PROJECT/PROJECT_DECISIONS.md` (S037, artifact #8)
- `docs/reviews/TASK-105D-FREEZE-FINALIZATION-REVIEW-2.md` (S038, artifact #9)

Artifact #6/#7/#8/#9 đều thuộc diện `OWNER APPROVAL REQUIRED` của `V4.1` §10;
approval là chỉ thị tường minh của Owner khi mở từng phiên tương ứng, ghi lại
ở đầu mỗi artifact.

`DEC-156` là artifact thứ 5, tức thuộc diện `OWNER APPROVAL REQUIRED` của
`V4.1` §10. Approval đó chính là chỉ thị trực tiếp của Owner trong phiên
ratification ("ghi nhận các Owner Decisions vào canonical decision/task/
progress artifacts theo đúng governance") — ghi lại tường minh, xem
`DEC-156` phần đầu.

Không cycle nào được mở bởi việc tạo specification hay bởi phiên readiness.
Cycle đầu tiên của lineage là `TASK-105D-RC-1` (`S042`) — xem khối `cycles:`
ở trên.

### Branch divergence — `TASK-105D` lineage (`V4.1` §8)

Ghi theo `DEC-157` §2 (Owner Decision B). `S036` phát hiện
`INTEGRATION_DECISION_REQUIRED` sau commit của chính nó:

```text
ahead default   : 4 commit          (ngưỡng: > 10)      OK
divergence days : 0                 (ngưỡng: > 3)       OK
cumulative LOC  : 5637              (ngưỡng: > 5.000)   VƯỢT
DIVERGENCE      : INTEGRATION_DECISION_REQUIRED [ loc>5000 ]
AUTHORITY       : BRANCH_WITH_UPSTREAM
RESULT          : AUTHORITY_OK
```

```text
OWNER DECISION (DEC-157 §2) : V4.1 §8 Option C — CONTINUE WITH EXPLICIT
                              JUSTIFICATION
JUSTIFICATION               : toàn bộ LOC vượt ngưỡng là documentation/
                              governance; production diff = 0; phần việc còn
                              lại chỉ là gate correction + freeze; merge trước
                              freeze không có lợi ích, chỉ thêm rủi ro xung
                              đột văn bản
SCOPE ĐƯỢC PHÉP             : (1) Gate Revision S037; (2) MỘT Freeze
                              Finalization retry độc lập. Không mở thêm scope.
REVIEW POINT (BẮT BUỘC)     : NGAY SAU FREEZE FINALIZATION RETRY VERDICT
RÀNG BUỘC                   : KHÔNG mở TASK-105D implementation trước review
                              point đó, kể cả khi freeze verdict là PASS
```

Đo lại sau commit của `S037` (SHA `4c9c072990278d6696605ee7dc1b215a0a00d6de`):

```text
ahead default   : 6 commit          (ngưỡng: > 10)      OK
divergence days : 0                 (ngưỡng: > 3)       OK
cumulative LOC  : 8683              (ngưỡng: > 5.000)   VƯỢT
DIVERGENCE      : INTEGRATION_DECISION_REQUIRED [ loc>5000 ]
AUTHORITY       : BRANCH_WITH_UPSTREAM
RESULT          : AUTHORITY_OK
```

Con số tăng từ `5637` lên `8683` **hoàn toàn** do documentation/governance của
`S037`: `git diff --shortstat` từ đỉnh nhánh mặc định tới HEAD cho
`18 files changed, 8619 insertions(+), 64 deletions(-)`, trong đó production
diff (`app/**`, `tests/**`, `config/**`, `tools/**`, `scripts/**`,
`pyproject.toml`) là **rỗng**. Bản chất rủi ro không đổi so với lúc Owner ra
quyết định: rủi ro **xung đột văn bản**, không phải rủi ro hành vi. Option C và
review point giữ nguyên hiệu lực; con số mới là dữ liệu cho chính review point
đó, không phải một trigger mới cần quyết định lại.

Đây là một quyết định integration, **không** phải vi phạm thẩm quyền —
`branch_authority_check.sh` vẫn trả `AUTHORITY_OK`.

### Divergence review point — ĐÃ THỰC HIỆN (`S038`, 2026-08-28)

`DEC-157` §2 đặt review point bắt buộc = **ngay sau freeze finalization retry
verdict**. Verdict đã có (`PASS WITH HARDENING`, Completion Gate `FROZEN`), nên
review point được thực hiện trong chính phiên `S038`:

```text
Đo tại be835b1 (HEAD phiên review, trước commit của S038):
  ahead default     : 7 commit        (ngưỡng > 10)     OK
  behind default    : 0 commit
  divergence days   : 0               (ngưỡng > 3)      OK
  cumulative LOC    : 8.703           (ngưỡng > 5.000)  VƯỢT
    production LOC      : 0
    documentation LOC   : 8.639   (18 file, +8.639 / −64)
  DIVERGENCE        : INTEGRATION_DECISION_REQUIRED [ loc>5000 ]
  AUTHORITY         : BRANCH_WITH_UPSTREAM
  RESULT            : AUTHORITY_OK
  merge/conflict risk : rủi ro XUNG ĐỘT VĂN BẢN, không phải rủi ro hành vi;
                        behind = 0 nên hiện chưa có conflict thực tế

SCOPE OPTION C — ĐÃ DÙNG HẾT:
  (1) Gate Revision S037            ✔
  (2) MỘT Freeze Finalization retry ✔  (S038)

RECOMMENDATION (reviewer S038) : (A) integrate/merge sớm
STATUS                         : OWNER DECISION REQUIRED — V4.1 §8
```

`S038` **không** tự chọn phương án, **không** merge, và **không** tự gia hạn
Option C. Lý do gốc mà Owner ghi khi chọn Option C ("phần việc còn lại chỉ là
gate correction + freeze") nay đã hoàn tất, nên tiếp tục divergence sẽ là một
**gia hạn** cần thẩm quyền Owner, không phải sự tiếp nối của quyết định cũ.

Ràng buộc `DEC-157` §2 vẫn hiệu lực tới khi Owner quyết định: **KHÔNG mở
`TASK-105D` implementation trước divergence decision**, kể cả khi freeze
verdict là `PASS` và `TASK-105D` đã `READY`.

Chi tiết: §14 của `docs/reviews/TASK-105D-FREEZE-FINALIZATION-REVIEW-2.md`.

Cập nhật 2026-08-28 (S034, `DEC-155` — readiness/data contract):
`repair_cycles_used` giữ nguyên `0`. Một phiên readiness/documentation
**không phải** repair cycle — V4.1 §3 tính cycle theo LẦN SỬA một defect
BLOCKING, và independent review tại `61a90b4f` ghi `BLOCKING = 0`. Ready Gate
blocker giảm từ 4 xuống 2 (Owner ratification `OR-01`/`OR-02`/`OR-03`;
Completion Gate freeze bởi authority riêng). `status` cập nhật bên dưới.

---

## Capability-Level Repair Budget — CAP-PRICE-RESOLUTION (S045, PROPOSED — CHƯA ADOPTED)

Tái dựng lịch sử — **không sửa** bất kỳ con số ledger per-task hiện có nào
ở trên. Ghi theo `DEC-160` / `governance/core/V4_1_POLICY_FREEZE.md` §16
đề xuất (`docs/reviews/CAP-PRICE-RESOLUTION-CORE-GOVERNANCE-CHANGE-PROPOSAL.md`).

```
lineage_root: CAP-PRICE-RESOLUTION
migration_status: PROPOSED

capability_repair_cycles_allowed: 4    # Owner PROPOSAL, chưa adopt

consumed:
  - task: TASK-105B
    cycle: TASK-105B-RC-1
    base_sha: c22cef8b47ac4cd71ef49609066a362c9e604313
    head_sha: 7f7048d65619c2c2198c99ccbfb073d6cb97ebe2
    ledger_evidence: "## Root Task: TASK-105B" → cycles: (trên)
  - task: TASK-105D
    cycle: TASK-105D-RC-1
    base_sha: e6252c06347ed5305fc32a77706a3a63f5a950cf
    head_sha: 1cc96a99638326513b26280b72bbeb3bce9d454d
    ledger_evidence: "## Root Task: TASK-105D" → cycles: (trên)
  - task: TASK-105C
    cycles_consumed: 0   # BLOCKED / NOT AUTHORIZED — chưa implementation
  - task: TASK-105E
    cycles_consumed: 0   # PLANNED / OUTLINE — chưa READY, chưa implementation

capability_repair_cycles_used: 2
capability_repair_cycles_remaining: 2   # CHỈ có hiệu lực NẾU migration_status = ADOPTED
```

**Ngân sách per-task hiện hành GIỮ NGUYÊN, authoritative, KHÔNG đổi bởi bảng
trên:**

```
TASK-105B : 2 allowed / 1 used / 1 remaining   (không đổi)
TASK-105C : 2 allowed / 0 used / 2 remaining   (không đổi, root riêng DEC-156 §4)
TASK-105D : 2 allowed / 1 used / 1 remaining   (không đổi)
TASK-105E : 2 allowed / 0 used / 2 remaining   (không đổi, cycles: [])
```

**Migration Transition Rule** (có hiệu lực ngay, không chờ ADOPTED): trong
lúc `migration_status ≠ ADOPTED`, không task nào trong `CAP-PRICE-RESOLUTION`
(kể cả `TASK-105E` khi được authorize sau này) được cấp Repair Cycle budget
mới chỉ vì lineage nay được nhóm lại thành một capability. TASK CREATION
APPROVAL ≠ REPAIR-BUDGET ALLOCATION APPROVAL.

Bằng chứng: `DEC-160`, `PROJECT/PROJECT_PROGRESS.md` →
`CAP-PRICE-RESOLUTION`,
`docs/sessions/S045-task-105d-h07-reconciliation-and-capability-governance.md`
phần B.

---

## Cách xác định phạm vi một repair cycle (tham chiếu)

```
git diff <base_sha>..<head_sha> --name-only
```

Cycle được tính theo LẦN SỬA, không theo số review. Nếu repair tiếp tục
trong cùng cycle, `head_sha` phải tiến lên SHA mới; `base_sha` không reset.
Không dùng session mới / sub-unit mới / branch mới để reset `base_sha`.

## Owner Extension log

*(Trống. Mỗi Owner Extension được cấp sau này phải thêm một mục vào đây, kèm
root task, phạm vi, và budget cụ thể.)*

Tính đến `V4.1-1` (2026-08-27): **chưa có Owner Extension nào được cấp.**
`R1-A2` → `R8` của lineage `TASK-110` vì vậy **không unit nào được tự mở**.
`DEC-141` là Owner Decision về Gate Class và integration — **không phải** một
Owner Extension, và **không** cấp thêm repair cycle.

## Cập nhật gần nhất

- 2026-08-27 — Khởi tạo ledger tại `TASK-V4-ADOPTION` (V4.1-0, Policy
  Adoption). `TASK-V4-ADOPTION` mở với 1 repair cycle khả dụng, 0 đã dùng.
  `TASK-110` ghi nhận ở trạng thái transition `EXHAUSTED_PRE_V4.1`, remaining
  = 0.
- 2026-08-27 — `V4.1-1` INTEGRATION. Hợp nhất `TASK-110`/`R1-A1` (`01a03b0`,
  `FROZEN` theo `DEC-139`) và Governance V4.1 (`8d79009`) vào nhánh mặc định
  qua integration branch `integration/v4-1-task-110`. Owner Decision
  `DEC-141`: `CHECK-110-16` → Gate Class `POST_MERGE_PRODUCTION_ACCEPTANCE`
  (Status vẫn `BLOCKED`); `DEC-128` của V4.1 đổi thành `DEC-140` để giải ID
  collision với `DEC-128` của `TASK-110`; `KNOWN PRE-V4.1 DIVERGENCE` đóng.
  **Ngân sách không đổi:** `TASK-110` vẫn `EXHAUSTED_PRE_V4.1`, remaining = 0.
  Thay đổi tài liệu của phiên integration được phân loại
  `INTEGRATION STATE RECONCILIATION`, **không** tính là repair cycle.
- 2026-09-03 — `TASK-PRA-004` mở lineage MỚI tại phiên Discovery + Contract
  Freeze S100 (`docs/sessions/S100-pra-004-ban-hang-review-detail-discovery.md`),
  `BASE_SHA = 8181cebe0619a9c8d12604168a90914c04b3692f`. `effective_risk = MEDIUM`,
  1 repair cycle khả dụng, 0 đã dùng. Phiên discovery là docs-only
  (`PRODUCTION_CODE_DELTA = 0`) và **KHÔNG** tiêu repair cycle. 0 BLOCKING
  finding. KHÔNG kế thừa ngân sách của `TASK-PRA-003` hay bất kỳ lineage nào.

- 2026-08-27 — `TASK-GOLDEN-BASELINE-001` mở lineage mới sau Owner Decision
  `OD-GB-1 = A + A1`. Discovery (`b738fa4`) + implementation Golden Business
  Baseline trên hai kỳ Tín Phát 01.2026/06.2026 từ workbook production thật do
  Owner cung cấp. `effective_risk = HIGH`, 2 cycle khả dụng, **0 đã dùng**.
  `TASK-110` **không đổi**: vẫn `EXHAUSTED_PRE_V4.1`, remaining = 0;
  `CHECK-110-16` vẫn `REQUIRED · BLOCKED · POST_MERGE_PRODUCTION_ACCEPTANCE`.
- 2026-08-27 — `TASK-GOLDEN-BASELINE-001` repair cycle #1 (`GB-IR-01`). Sau
  Independent Review trên `4bccf46` (verdict FAIL, đúng 1 BLOCKING finding):
  `test_golden_expected_output_is_regenerable_byte_identical` so byte-thô
  toàn bộ file expected, gồm cả `_environment` advisory
  (`python`/`pyyaml`/`openpyxl`) — false regression signal trên một Python
  hợp lệ khác (tái hiện: Python 3.12.3 → `50 passed, 2 failed, 2 skipped`).
  Sửa bằng `_strict_bytes()` (tái dùng `_comparable()` đã có), loại đúng ba
  trường advisory khỏi phép so byte. Không đổi `expected/*.json`, không đổi
  fixture, business payload trước/sau IDENTICAL. Repair SHA `54a575d`.
  `repair_cycles_used: 1`, `repair_cycles_remaining: 1`. `TASK-110`,
  `CHECK-110-16`, `app/`, `config/` không đổi.
- 2026-08-27 — `TASK-GOLDEN-BASELINE-001` **Independent Review #2 RECORDED**
  (phiên "VERDICT RECORDING ONLY", không phải phiên review mới). Verdict
  `PASS — ELIGIBLE_FOR_FREEZE` tại reviewed SHA `8521069…`, đã được Owner
  cung cấp từ một review chạy ngoài canonical repo, nay ghi vào
  `docs/reviews/TASK-GOLDEN-BASELINE-001-INDEPENDENT-REVIEW-2.md`. `GB-IR-01`
  = `CLOSED_BY_REPAIR, INDEPENDENTLY_VERIFIED`. `BLOCKING = 0`.
  `repair_cycles_used` vẫn `1`, `remaining` vẫn `1` — review này **không**
  tiêu cycle. `FROZEN = NO`, `DONE = NO`, `MERGED = NO`: verdict PASS thuộc
  thẩm quyền independent reviewer, còn `FROZEN` thuộc một phiên Freeze
  Finalization riêng chưa chạy (`governance/core/V4_1_POLICY_FREEZE.md`
  §12). `TASK-110`, `CHECK-110-16`, `app/`, `config/` không đổi.
- 2026-08-27 — `TASK-GOLDEN-BASELINE-001` **FREEZE FINALIZATION** (`DEC-142`,
  phiên "FREEZE FINALIZATION + CONTROLLED INTEGRATION"). `FROZEN = YES` tại
  reviewed SHA `85210691702550d83c0fd42fe816be8ca9dde889` (review verdict
  record `94b2513d1894dbd58f3b08656e3c7412be191df5`). Golden Baseline
  contract (fixture, expected output, strict business comparison) niêm phong.
  `repair_cycles_used` vẫn `1`, `remaining` vẫn `1` — **UNUSED**, đóng task
  không bắt buộc dùng hết ngân sách. `TASK-110`, `CHECK-110-16`, `app/`,
  `config/` không đổi.
- 2026-08-27 — `TASK-GOLDEN-BASELINE-001` **CONTROLLED INTEGRATION + DONE**
  (cùng phiên trên). Merge `--no-ff` qua nhánh trung gian
  `integration/v4-1-golden-baseline` vào nhánh mặc định
  `claude/extract-upload-repo-gq2ws4` tại SHA
  `f332a4cb4410b3ca9c71d659d36a3e8f26aa1fa5`. Trên default: Golden test
  `58 passed, 2 skipped`; `pytest -q` toàn bộ `697 passed, 11 skipped, 0
  failed` (0 regression); business anchors 01/2026 và 06/2026 khớp tuyệt đối;
  `validate_reference_integrity` vẫn đúng 3 lỗi pre-existing (`TASK-REM-T06`).
  `MERGED = YES`. GB-12 Exit Criteria (11 điều kiện) đủ ⇒ `DONE = YES`.
  `V4.1` chuyển `POLICY_ADOPTED` → **`FULLY_ENFORCED`** (ba executable
  enforcement asset đã kiểm chứng chạy được trên default:
  `scripts/branch_authority_check.sh`, ledger này, `tests/test_golden_baseline.py`).
  `TASK-110`, `CHECK-110-16`, `R1-A1`, `app/`, `config/`,
  `tests/fixtures/baseline/**`, `tests/test_task110_non_regression.py`
  **không đổi một byte** qua toàn bộ integration.

- 2026-08-27 — `TASK-108B` **mở lineage mới** sau Owner Decision `OD-108B-01`
  (ghi tại `DEC-143`). `EligibleCosts = {}` (closed empty set),
  `DeliveryCost = NOT ELIGIBLE FOR NOW`, `OtherKpiAdjustment = 0 by definition`,
  canonical formula chốt `(SellPrice − KpiPurchasePrice) × Quantity − Discount`.
  **C15 ĐÓNG.** `effective_risk = HIGH`, 2 cycle khả dụng, **0 đã dùng** —
  phiên ghi quyết định **không** phải repair cycle và **không** tiêu ngân sách.
  `SEMANTIC_DEFINITION = APPROVED` nhưng
  `IMPLEMENTATION = BLOCKED_BY_DEPENDENCY`: số blocker giảm **4 → 2**, cả hai
  còn lại là dependency **dữ liệu** (Price Master; confirmed
  `KpiPurchaseAdjustment` persistence), không phải semantic. `TASK-110`
  **không đổi**: vẫn `EXHAUSTED_PRE_V4.1`, remaining = 0; `CHECK-110-16` vẫn
  `REQUIRED · BLOCKED · POST_MERGE_PRODUCTION_ACCEPTANCE`;
  `TASK-GOLDEN-BASELINE-001` vẫn `remaining = 1` UNUSED. `app/`, `config/`,
  `tests/`, Golden fixture/expected **không đổi một byte**.

- 2026-08-27 — `DEC-144` (`OD-108B-02` + Owner confirmation cho `DEC-143`).
  Canonical `EligibleKpiProfit` được Owner **xác nhận**:
  `(SellPrice − KpiPurchasePrice) × Quantity − Discount` — đóng divergence
  §19.1 đã báo cáo theo V4.1 §11. Confirmed `KpiPurchaseAdjustment` chọn
  phương án A: absence **đã xác định** → `KpiPurchasePrice =
  AccountingPurchasePrice` + provenance `Config:NoConfirmedAdjustment`;
  `UNKNOWN`/`SOURCE_UNAVAILABLE`/`LOOKUP_FAILURE` **giữ Pending**, tuyệt đối
  không thành `0`. `TASK-108B` blocker ngoại lai **2 → 1** (chỉ còn Price
  Master); yêu cầu cơ chế còn lại (source khai báo rỗng) thuộc phạm vi chính
  `TASK-108B`, không phải blocker chờ Owner. **`TASK-105B` mở lineage mới** ở
  trạng thái discovery, `effective_risk = HIGH`, 2 cycle khả dụng, **0 đã
  dùng** — discovery không tiêu cycle. `TASK-110` **không đổi**
  (`EXHAUSTED_PRE_V4.1`, remaining = 0; `CHECK-110-16` vẫn `REQUIRED · BLOCKED ·
  POST_MERGE_PRODUCTION_ACCEPTANCE`); `TASK-GOLDEN-BASELINE-001` vẫn
  `remaining = 1` UNUSED. `app/`, `config/`, `tests/`, Golden fixture/expected
  **không đổi một byte**.

- 2026-08-27 — `DEC-145` (`OD-105B-01`). Owner chốt Q1/Q2/Q3 của `TASK-105B`:
  khoảng hiệu lực **đóng** `[from, to]` với overlap/nhiều-record-mở =
  `INVALID PRICE MASTER` và gap → `Pending` (cấm latest/nearest/current);
  normalization NFC → strip → collapse → casefold (cấm bỏ dấu, fuzzy,
  nearest, contains); dòng phụ `AccountingPurchasePrice = 0 BY DEFINITION` với
  provenance `Policy:SupplementaryExpenseZeroPurchasePrice`. `TASK-105B`
  chuyển `OWNER_DECISION_REQUIRED` → **`SEMANTIC_READINESS = READY`,
  `IMPLEMENTATION = READY`**, chỉ chờ file giá 4 cột. **`TASK-105B-Q3` tách
  riêng và BLOCKED** bởi `TASK-103` — báo cáo theo đúng dự phòng của
  `OD-105B-01` §C, không tự phát minh matcher. `TASK-108B` blocker cập nhật
  thành "FilePriceProvider chưa tồn tại + chưa có bảng giá". Ngân sách
  **không đổi** ở mọi lineage: `TASK-105B` 2/0/2, `TASK-108B` 2/0/2,
  `TASK-110` `EXHAUSTED_PRE_V4.1` remaining = 0,
  `TASK-GOLDEN-BASELINE-001` remaining = 1 UNUSED. `app/`, `config/`,
  `tests/`, Golden fixture/expected **không đổi một byte**.

- 2026-08-27 — `DEC-146` — Architecture Correction Audit cho `TASK-105B`.
  Owner sửa tiền đề đã dùng ở `DEC-144`/`DEC-145`: Price Master **không phải
  file tĩnh** — nguồn sự thật vận hành là **Firebase RTDB**, biến động liên
  tục trong ngày. Quét toàn repo: **0** integration Firebase/RTDB nào tồn tại
  (chỉ 2 chỗ nhắc "Firebase" là boilerplate template governance chung, không
  phải quyết định kỹ thuật của dự án này); `pyproject.toml` không có
  `firebase-admin` hay SDK liên quan; không credential/schema/crawler nào
  được ghi lại ở bất kỳ đâu. `CONFLICT DETECTED` đã báo cáo theo đúng giao
  thức: `ADR-101` nêu tên PostgreSQL/SQLite cho Phase 2, không nơi nào nhắc
  Firebase làm kiến trúc dự án.

  `TASK-105B` chuyển từ `IMPLEMENTATION = READY` (DEC-145) sang **TẠM DỪNG**
  — không phải blocker kỹ thuật (contract §38 vẫn buildable y hệt), mà là
  quyết định phạm vi/vai trò cần Owner xác nhận trước khi tránh làm lại.
  `SEMANTIC_READINESS` (Q1/Q2/Q3, DEC-145) **giữ nguyên đúng** — ba câu hỏi đó
  ràng buộc **hình dạng dữ liệu giá**, độc lập với nơi nó tới từ đâu.

  **Điều kiện `BLOCKING ARCHITECTURE GAP` cho `TASK-108B`** nếu RTDB chỉ lưu
  giá hiện hành (overwrite, không giữ lịch sử) — DEC-121 đòi hỏi tra cứu đúng
  giá tại ngày quá khứ của đơn; "RTDB đang chạy" trả lời câu hỏi khác ("giá
  hiện tại"), không phải câu hỏi `TASK-108B` cần. Chưa xác định — cần Owner
  trả lời trực tiếp, không suy đoán.

  Đề xuất: giữ `PriceProvider` Protocol (đã đúng thiết kế từ DEC-103), thêm
  `TASK-105C` (`RTDBPriceProvider`) **song song** với `TASK-105B`
  (`FilePriceProvider`, vai trò lùi thành bootstrap/test-fixture/snapshot-export
  tuỳ câu trả lời Owner) — không thay thế nhau. `RTDBPriceProvider` **không
  bao giờ** default trong test/Golden (nguyên tắc deterministic).

  `TASK-105B-Q3` (chính sách zero-price dòng phụ) **không đổi**, vẫn `BLOCKED`
  bởi `TASK-103`/enumeration — hoàn toàn độc lập với nguồn giá. Audit evidence
  đang làm dở (30 raw label từ `evidence.json`: `Chi phí vận chuyển` 1.074
  dòng, `Chi phí lắp đặt` 84, `Chênh VAT` 33, cộng biến thể ghép/typo) **không
  mất** — tạm dừng theo yêu cầu Owner, tiếp tục được ở phiên sau.

  Đây là **audit, không phải repair cycle** — ngân sách mọi lineage không đổi:
  `TASK-105B` 2/0/2, `TASK-108B` 2/0/2, `TASK-110` `EXHAUSTED_PRE_V4.1`
  remaining = 0, `TASK-GOLDEN-BASELINE-001` remaining = 1 UNUSED. `app/`,
  `config/`, `tests/`, Golden fixture/expected **không đổi một byte**.

- 2026-08-27 — `DEC-147` — Cross-Repo RTDB Price Source Audit (`TASK-105C`
  discovery, phiên `S024`). Đã audit repository vận hành hệ thống giá
  (`hoangvinhkta-creator/Tracking` @ `d177363a390d36fe793e0c1c44a6fb6743ca45f5`)
  và đối chiếu với contract `PriceProvider`. Hai repo giữ **độc lập** — không
  subtree, không submodule, không copy source, không merge history; repo giá
  **không bị sửa một byte nào**.

  **Bốn trong năm câu hỏi của `DEC-146` §49 đã đóng bằng bằng chứng code (E1).**
  RTDB chạy chế độ **HYBRID**: `board/<mã>/p/<NCC>` là ảnh chụp hiện hành,
  `phist/<mã>/<NCC>/<YYYY-MM-DD>` là lịch sử append theo ngày, chỉ ghi khi giá
  đổi. ⇒ Điều kiện **`BLOCKING ARCHITECTURE GAP` của `DEC-146` §3 KHÔNG kích
  hoạt**.

  **Nhưng kết luận thật là `SOURCE MISMATCH`, không nằm trong hai nhánh
  `DEC-146` dự trù:** loại giá *có* lịch sử là **giá NCC báo** (báo giá nhà
  cung cấp trong ngày), còn loại giá Reports *cần* — **giá thực nhập**
  (`inv.<slot>.gia` / `.lo`) — **không có lịch sử** (hai ô cuốn chiếu
  `cu`/`moi`, ghi bằng `set()` đè cả nhánh; `backup/` không chứa `inv`).

  Ba phát hiện nữa ảnh hưởng trực tiếp tới con số: RTDB lưu tiền theo **nghìn
  đồng** (va `ADR-103` — phép ×1.000 phải nằm ở biên nhập, không nằm trong
  `app/modules/pricing/`); `phist == 0` là **sentinel hết hàng**, phải map
  thành gap → `Pending`, tuyệt đối không thành `purchase_price = 0`
  (`DEC-145` §5); và **lịch sử sửa được** — bốn đường xoá/dời/mồ côi/lệch đang
  chạy trong app ⇒ chỉ một bản ghi **bất biến, đóng băng** mới thoả `DEC-121`.

  **Kiến trúc khuyến nghị: OPTION C (capture bất biến) giao hàng bằng định
  dạng OPTION D (file 4 cột `DEC-145` §4).** Hệ quả:
  `FilePriceProvider` **được đề cử trở lại làm production path** — đảo lại
  nghi vấn của `DEC-146` §6, không huỷ gì của `DEC-145`;
  `RTDBPriceProvider` = **`NEEDS_SCHEMA_CHANGE`, không được đề cử** (đọc thẳng
  va `ADR-101` ranh giới mạng + `ADR-103` §2 đơn vị, và nguồn thì mutable).

  Khoá sản phẩm: RTDB **đã có** mã ổn định (`normCode` + `alias`), nhưng
  Reports dùng `product_raw` = câu tên hàng trên chứng từ ⇒ **cần mapping**.
  Repo giá đã **thử** rút mã từ tên hàng bằng máy (`extractCode()`) và **bỏ
  hẳn** vì đoán sai trên tài sản thật — tiền lệ production ủng hộ đúng lệnh
  cấm fuzzy matching của `OD-105B-01` §B. `DEC-145` §2 **không đổi**.

  Security: **không** có BLOCKING finding — không credential nào committed,
  service account nằm ở Cloudflare Secret, rules gốc `.read/.write = false`,
  không nhánh nào cho `auth == null`, App Check Enforce từ 13/08/2026. Ba mục
  HARDENING thuộc repo giá (nhật ký `hist` tối đa 100 dòng và mọi nhân viên
  ghi đè được; `phist` sửa được bởi mọi tài khoản `edit`; Reports sẽ cần một
  mặt phẳng quản lý secret mới nếu đọc thẳng RTDB) — **ngoài phạm vi** sửa của
  phiên này.

  `TASK-105B-Q3` **không đổi**, vẫn `BLOCKED` bởi `TASK-103`/enumeration —
  hoàn toàn độc lập với nguồn giá, đúng như `DEC-146` §7. Audit evidence 30
  raw label **không mất**.

  Đây là **audit, không phải repair cycle** — ngân sách mọi lineage không đổi:
  `TASK-105B` 2/0/2, `TASK-108B` 2/0/2, `TASK-110` `EXHAUSTED_PRE_V4.1`
  remaining = 0, `TASK-GOLDEN-BASELINE-001` remaining = 1 UNUSED. `app/`,
  `config/`, `tests/`, Golden fixture/expected **không đổi một byte**. Repo
  giá: **0 file thay đổi**.

- 2026-08-27 — `DEC-148` (audit) — `inv.cong` public purchase price audit.
  Xác nhận 4 semantics chủ dự án đề xuất; kết luận `inv.cong` KHÔNG có lịch
  sử, NO GUARANTEED DELAY WINDOW. Không tiêu repair cycle. Chi tiết: xem
  `DEC-148` trong `PROJECT_DECISIONS.md`.

- 2026-08-27 — `DEC-149` (audit) — Market Min Price Path Audit. `CONFLICT
  DETECTED`: business rule "Min ưu tiên, cong fallback" không khớp công
  thức `_c.min` thật (`cong` hoà tan bên trong, không phải fallback độc
  lập). Historical Replay = C (chỉ current snapshot). Không tiêu repair
  cycle. Chi tiết: xem `DEC-149` trong `PROJECT_DECISIONS.md`.

- 2026-08-27 — `DEC-150` (audit fact, không phải Owner Decision) — xác
  minh popup "Lịch sử giá" = vendor-price history thuần từ `phist`, KHÔNG
  phải Min history, không reconstruct Min. Không đổi trạng thái nào của
  `DEC-149`. Không tiêu repair cycle. Chi tiết: xem `DEC-150` trong
  `PROJECT_DECISIONS.md`.

- 2026-08-27 — `DEC-151` (**Owner Decision**) — Historical KPI Purchase
  Price Scope Reduction. Đóng `CONFLICT DETECTED` (`DEC-149` §71) bằng
  **thu hẹp phạm vi**, không phải bằng chọn giữa hai lựa chọn cũ: Reports
  dùng `phist` làm nguồn giá lịch sử DUY NHẤT
  (`Price(NCC,D)` = record gần nhất ≤ D, MIN qua các NCC có căn cứ, loại
  sentinel `0`); `inv.cong` loại khỏi scope Phase 1 (không áp ngược, không
  bắt buộc xây lịch sử); mã thiếu căn cứ → `Pending` chủ đích, xử lý tay
  sau (explicit, có provenance, không rewrite `phist`, không backdating).
  `DEC-149` OPTION B (capture `_c.min` + `inv.cong`) **không còn là
  khuyến nghị hiện hành** — mục tiêu nó phục vụ (tái dựng đúng `_c.min`)
  đã bị loại bỏ, không phải vì sai mà vì không còn cần.
  Audit hẹp bắt buộc trong phiên: `phist` **đủ** cho `HistoricalVendorPrice`
  deterministic theo semantics trên, không cần giả định
  `NCC_RETIRED`/`NCC_MIN_LOAI`/`NGUONG_BAT_THUONG` hiện tại áp cho lịch sử
  (`buildSync()` ghi `phist` bất kể trạng thái loại trừ). Hai câu hỏi
  filtering còn mở, không tự trả lời: Q1 (NCC retired/MIN_LOAI hồi tố),
  Q2 (outlier threshold hồi tố) — KHÔNG chặn mở implementation.
  `TASK-105C` `BLOCKED_BY` hẹp lại còn Q1/Q2 (không chặn) +
  `TASK-105B-Q3` (độc lập, không đổi). `TASK-108B` blocker tương ứng.
  Đây là **Owner Decision recording, không phải repair cycle** — ngân sách
  mọi lineage không đổi: `TASK-105B` 2/0/2, `TASK-108B` 2/0/2, `TASK-110`
  `EXHAUSTED_PRE_V4.1` remaining = 0, `TASK-GOLDEN-BASELINE-001`
  remaining = 1 UNUSED. `app/`, `config/`, `tests/`, Golden fixture/expected
  **không đổi một byte**. Repo giá: **0 file thay đổi**. Chi tiết: `DEC-151`,
  `docs/sessions/S028-task-105c-historical-kpi-price-scope-reduction.md`,
  `docs/tasks/TASK-108B-eligible-costs-owner-definition.md` Phần X.

- 2026-08-27 — `DEC-152` (**Owner Decision cuối** + Scope Lock/Completion
  Gate) — đóng Q1 (NCC retired/MIN_LOAI hồi tố) và Q2 (outlier threshold
  hồi tố), cả hai **CLOSED**: trạng thái NCC/config HIỆN TẠI không được áp
  ngược cho quá khứ; Phase 1 = MIN qua mọi candidate hợp lệ tại D (loại
  sentinel `0`), không lọc gì thêm. Tạo
  `docs/tasks/TASK-105C-historical-vendor-price-provider.md` — canonical
  spec 24 mục, Scope Lock (Phạm Vi/Ngoài Phạm Vi/Vùng Tác Động), Completion
  Gate 20 check (`CHECK-105C-01`…`20`, toàn bộ `NOT_TESTED` — chưa
  implementation). Kiến trúc thực thi: `HistoricalVendorPriceProvider`
  compose `FilePriceProvider` (đọc file snapshot bất biến do
  `tools/pricing/` sinh ra, tách khỏi `app/modules/pricing/` — giữ ranh
  giới `ADR-101`); thay hẳn `DEC-149` OPTION B. Xác định rõ dependency
  chưa đóng: mapping `product_raw` (Reports) ↔ `<MÃ>` (Tracking) — chưa mở
  task, **không** tự vá bằng fuzzy matching (`OD-105B-01` §B, tiền lệ
  `extractCode()` thất bại — `DEC-147` §56). `TASK-105B` trở thành
  dependency CỨNG (chưa DONE) cho `TASK-105C`.
  Verdict: `TASK-105C` `SEMANTIC_DEFINITION = COMPLETE`,
  `SCOPE_LOCK = COMPLETE`, `IMPLEMENTATION = READY`. `TASK-108B`
  `BLOCKED_BY` = [`TASK-105C` implementation (kèm `TASK-105B`), product
  identity mapping, `TASK-105B-Q3`] — không còn câu hỏi nghiệp vụ nào chờ
  Owner.
  Đây là **Owner Decision + Scope Lock recording, không phải repair
  cycle** — ngân sách mọi lineage không đổi: `TASK-105B` 2/0/2 (dùng
  chung cho `TASK-105C`), `TASK-108B` 2/0/2, `TASK-110`
  `EXHAUSTED_PRE_V4.1` remaining = 0, `TASK-GOLDEN-BASELINE-001`
  remaining = 1 UNUSED. `app/`, `config/`, `tests/`, Golden fixture/expected
  **không đổi một byte**. Repo giá: **0 file thay đổi**. Chi tiết: `DEC-152`,
  `docs/tasks/TASK-105C-historical-vendor-price-provider.md`,
  `docs/sessions/S029-task-105c-final-decision-scope-lock.md`.

- 2026-08-28 — `TASK-105B` **IMPLEMENTATION** (phiên "TASK-105B — IMPLEMENTATION").
  `FilePriceProvider` (`app/modules/pricing/file_price_provider.py`, MỚI)
  implement đúng contract `DEC-145`/`OD-105B-01` — khoảng hiệu lực đóng,
  chuẩn hoá NFC+casefold, validation §5 đầy đủ (overlap, >1 open record,
  giá âm/rỗng, ngày lỗi, duplicate hoàn toàn), provenance 3 phần
  (raw/normalized/matched record), `InvalidPriceMasterError` raise khi
  nạp. **Completion Gate frozen tại phiên này**
  (`docs/tasks/TASK-105B-file-price-provider.md`, CHECK-105B-01..17 — 16
  check gốc từ §38.5 của `docs/tasks/TASK-108B-eligible-costs-owner-definition.md`
  + 1 check mới đóng risk note Firebase-import của `DEC-146`). **17/17
  REQUIRED PASS** (self-verify, E1; CHECK-105B-12 đạt E2). Evidence:
  `pytest tests/test_file_price_provider.py -q` → `33 passed`;
  `pytest tests/test_golden_baseline.py -q` → `58 passed, 2 skipped`
  (không đổi); `pytest -q` toàn bộ → `730 passed, 11 skipped` (trước
  phiên `697 passed, 11 skipped` — chênh lệch đúng 33 test mới, **0
  regression**); diff `app/pipeline.py`/`price_engine.py`/`provider.py`/
  `models.py` = **0**; 4 validator PASS,
  `validate_reference_integrity` giữ đúng 3 lỗi tiền tồn `TASK-REM-T06`.
  Provider mặc định **không đổi** (`PendingPriceProvider`, Golden không
  chạm). **Đây là implementation session, KHÔNG tự tiêu repair cycle**
  (`TASK-105B` vẫn `2 allowed / 0 used / 2 remaining`) và **KHÔNG tự
  DONE** — `Effective Risk = HIGH` đòi Independent Review độc lập trước
  (đúng tiền lệ `TASK-GOLDEN-BASELINE-001`). Bảng giá production thật
  **chưa có** — data dependency mở, không phải code blocker.
  `TASK-105C` **vẫn KHÔNG được bắt đầu implementation** cho tới khi
  `TASK-105B` qua Independent Review và chuyển `DONE` (dependency cứng,
  `DEC-152` §11). `app/pipeline.py`, `provider.py`, `price_engine.py`,
  `models.py`, `config/`, Golden fixture/expected **không đổi một byte**.
  Chi tiết đầy đủ: `docs/tasks/TASK-105B-file-price-provider.md`.

- 2026-08-28 — `TASK-105B` **INDEPENDENT REVIEW RECONCILIATION** (phiên
  "TASK-105B — INDEPENDENT REVIEW RECONCILIATION", canonicalization only —
  không phải review lần 3, không remediation). Phát hiện: hai session
  Independent Review #1 độc lập đã chạy **song song** trên hai nhánh khác
  nhau — `review/task-105b-independent-review-1` (SHA
  `be2e35c908921f16e8347ecdfd23e2f9aecf1069`) và
  `claude/file-price-provider-review-negpxw` (SHA
  `b735dace8bdbaea086b37f8c20e091cafbed03e5`) — không biết về nhau, cùng
  review đúng implementation SHA `c22cef8` (`merge-base` của hai review =
  `c22cef8`, xác nhận không drift), cùng ghi artifact tại đúng
  `docs/reviews/TASK-105B-INDEPENDENT-REVIEW-1.md`. Cả hai verdict `PASS —
  ELIGIBLE_FOR_FREEZE`, 17/17 REQUIRED PASS độc lập ở cả hai bên, cùng số
  liệu regression/Golden. Reconciliation: dedupe namespace `HB-105B-*`
  (phát hiện Review B tái dùng nhầm hai ID `HB-105B-01`/`HB-105B-02` vốn đã
  thuộc `TASK-108B` §34 — không liên quan `FilePriceProvider` — sửa canonical
  ID về `HB-105B-07`/`HB-105B-08` từ Review A, không collision, không reuse
  ID); giải quyết một classification disagreement (`HB-105B-04`: HARDENING
  theo Review B vs OUT_OF_SCOPE theo Review A — reconciled = OUT_OF_SCOPE
  theo đúng normative Scope Lock table đã frozen của `TASK-105B`, `V4.1`
  §7/§11 — không ảnh hưởng Freeze eligibility nên không cần Owner Decision).
  0 BLOCKING sau reconciliation ⇒ verdict hội tụ `PASS —
  ELIGIBLE_FOR_FREEZE`. Cả hai artifact gốc bảo toàn nguyên vẹn: Review A
  giữ canonical path, Review B archived byte-identical tại
  `docs/reviews/archive/TASK-105B-INDEPENDENT-REVIEW-1-B-file-price-provider-review-negpxw.md`.
  **Đây KHÔNG phải remediation cycle** — `app/**`/`tests/**`/`config/**` = 0
  trong toàn bộ diff phiên này; `TASK-105B` vẫn `2 allowed / 0 used / 2
  remaining` (**không đổi**, đúng `V4.1` §3 — cycle tính theo lần sửa,
  không theo số review/số artifact reconcile). Chi tiết đầy đủ:
  `docs/reviews/TASK-105B-INDEPENDENT-REVIEW-RECONCILIATION.md`. **NEXT
  AUTHORIZED ACTION = `TASK-105B` FREEZE** (phiên Freeze Finalization có
  thẩm quyền riêng, `V4.1` §12 — reconciliation session read-only không
  được ghi `FROZEN`).

### Branch divergence đã biết — lineage `TASK-105B`/`TASK-105C`

**ĐÃ ĐÓNG (2026-08-27, phiên "CONTROLLED INTEGRATION — TASK-105B/TASK-105C
GOVERNANCE CHECKPOINT").** Owner chọn option (A) của V4.1 §8: integrate/merge
sớm.

Divergence đo được ngay trước integration, so với nhánh mặc định
`claude/extract-upload-repo-gq2ws4` @ `7e60978`:

| Nhánh | ahead | LOC | vượt ngưỡng |
|---|---:|---:|---|
| `claude/reports-price-rtdb-audit-bg5y4t` | 10–11 | 6.936–8.131 | 2/3 (`ahead>10`, `loc>5000`) |

Integrate qua nhánh trung gian `integration/v4-1-price-history-foundation`
(cắt từ default tip `7e60978`), merge `--no-ff` candidate `aaceb883` — **0
conflict**. Merge nhánh trung gian vào default bằng `--ff-only` tại
`abddbe0c8f02330617917516957a26596b8d2dd9`. Không squash, không rebase,
không rewrite history, không force push. Validator chạy đủ trước và sau —
0 regression (đúng 3 lỗi tiền tồn `TASK-REM-T06`, xác nhận không đổi so
với chính default tip cũ).

**KNOWN DIVERGENCE = CLOSED.** Không grandfather thành permanent exception.
`branch_authority_check.sh` sau push: `DIVERGENCE = WITHIN_LIMITS`.

- 2026-08-28 — `TASK-105B` **FREEZE FINALIZATION** (`DEC-153`, phiên "TASK-105B
  — FREEZE + CONTROLLED INTEGRATION"). `FROZEN = YES` tại implementation SHA
  `c22cef8b47ac4cd71ef49609066a362c9e604313`, tham chiếu reconciliation SHA
  `95a7ae6c3c694a7095ecb2adc6041785c3960096`. Verdict reconciled `PASS —
  ELIGIBLE_FOR_FREEZE`, 0 BLOCKING, 17/17 REQUIRED Completion Gate PASS (E1
  tối thiểu, CHECK-105B-12 tại E2). Freeze **không** re-review technical
  correctness — chỉ niêm phong verdict đã có, đúng State Authority Matrix
  (`governance/core/V4_1_POLICY_FREEZE.md` §12). `repair_cycles_used` vẫn
  `0`, `remaining` vẫn `2` — **freeze không tiêu cycle** (không phải repair,
  hai Independent Review PASS song song + reconciliation không phải remediation).
  `HB-105B-07`/`HB-105B-08` re-trigger condition giữ nguyên nội dung, không
  downgrade, không xoá — bắt buộc resolve trước `TASK-105C` implementation
  hoặc trước `FilePriceProvider` activation thật, tuỳ điều kiện nào tới
  trước. `app/**`, `tests/**`, `config/**` **không đổi một byte** qua phiên
  Freeze này.

- 2026-08-28 — `TASK-105B` **CONTROLLED INTEGRATION** (cùng phiên trên).
  Divergence trước integration: ahead=7 commit, LOC=3294, 0 ngày —
  `WITHIN_LIMITS` (`branch_authority_check.sh`, dưới ngưỡng V4.1 §8).
  Qua nhánh trung gian `integration/v4-1-task-105b-price-provider` (cắt từ
  default tip `c49cb67`), merge `--no-ff` `review/task-105b-independent-review-1`
  — **0 conflict** (merge-base = default tip cũ, review branch vốn đã là
  fast-forward-able descendant thuần). Merge nhánh trung gian vào nhánh mặc
  định bằng `--ff-only`. Post-integration validation trên nhánh trung gian:
  production content byte-identical với reviewed SHA `c22cef8`; 4 file
  production lõi diff = 0; `PendingPriceProvider` vẫn default; 0 caller
  `FilePriceProvider` ngoài module/test; 0 code `TASK-105C`; targeted `33
  passed`; Golden `58 passed, 2 skipped`; full `pytest -q` `730 passed, 11
  skipped` (0 regression); 4 validator PASS; `validate_reference_integrity`
  đúng 3 lỗi tiền tồn `TASK-REM-T06`; `git diff --check` sạch; worktree
  CLEAN. `repair_cycles_used` vẫn `0`, `remaining` vẫn `2` — integration
  không tiêu cycle. `TASK-105B = FROZEN + INTEGRATED`, **VẪN CHƯA `DONE`**
  (Exit Criteria còn thiếu: bảng giá production thật nạp được — data
  dependency đang mở). `HB-105B-07`/`HB-105B-08` re-trigger giữ nguyên,
  chưa resolve — bắt buộc trước `TASK-105C` implementation hoặc trước
  `FilePriceProvider` activation thật.

- 2026-08-28 — `TASK-105B` **REPAIR CYCLE #1** (phiên "TASK-105B
  PRICE-PARSER MICRO-HARDENING", nhánh `task/task-105b-price-parser-hardening`,
  cắt từ default tip `89948df42b510e27b80a9a7902e3c07d4a7066e7`). Sửa đúng
  `HB-105B-07` (NaN → `decimal.InvalidOperation` thô) và `HB-105B-08`
  (`Infinity`/`-Infinity` không bị chặn đúng cách) — đúng RE-TRIGGER
  CONDITION đã ghi tại `DEC-153`, không phải phản ứng với Independent
  Review FAIL. Đường thẩm quyền dùng: **repair cycle mới có thẩm quyền
  riêng** (không phải `COMPLETION GATE CHANGE PROPOSAL` — 17 check REQUIRED
  của Completion Gate giữ nguyên nội dung, không sửa). Thay đổi mã nguồn
  duy nhất: một check `price.is_finite()` chèn vào `_parse_price()`
  (`app/modules/pricing/file_price_provider.py`), giữa check
  `missing_price` và `negative_price`, raise
  `InvalidPriceMasterError(reason="non_finite_price")`. 26 test hồi quy mới
  tại `tests/test_file_price_provider.py`. Chi tiết + toàn bộ evidence:
  commit `7f7048d65619c2c2198c99ccbfb073d6cb97ebe2`,
  `docs/tasks/TASK-105B-file-price-provider.md`.

  ```
  Targeted : 33 → 59 passed (+26 test mới)
  Golden   : 58 passed, 2 skipped (không đổi)
  Full     : 730 → 756 passed, 11 skipped (chênh lệch = đúng 26 test mới,
             0 regression, 0 skip mới)
  4 file production lõi diff : 0
  PendingPriceProvider vẫn default; 0 caller FilePriceProvider ngoài
  module/test; 0 code TASK-105C được thêm.
  ```

  `repair_cycles_used: 0 → 1`, `repair_cycles_remaining: 2 → 1`. Cycle
  ghi tại mục "Root Task: TASK-105B" → `cycles:` (`id: TASK-105B-RC-1`,
  `base_sha: c22cef8b47ac4cd71ef49609066a362c9e604313`,
  `head_sha: 7f7048d65619c2c2198c99ccbfb073d6cb97ebe2`). **`status:
  READY_FOR_REVIEW`** — Independent Review độc lập vẫn BẮT BUỘC (Effective
  Risk = HIGH) trước khi cycle này được ghi `CLOSED_BY_REPAIR,
  INDEPENDENTLY_VERIFIED`; phiên này không tự cấp verdict đó cho chính
  mình. `TASK-105B` vẫn `FROZEN + INTEGRATED`, vẫn `NOT DONE` (data
  dependency bảng giá thật vẫn mở, không đổi bởi phiên này). `TASK-105C`
  **KHÔNG** được bắt đầu trong phiên này — `HB-105B-07`/`HB-105B-08` được
  báo cáo là *code-level resolved*, nhưng prerequisite đầy đủ cho
  `TASK-105C` vẫn chờ Independent Review của chính cycle này, cộng
  product identity mapping (dependency riêng, chưa mở task). `TASK-110`,
  `TASK-GOLDEN-BASELINE-001` **không đổi**. `HB-105B-03`, `HB-105B-05`,
  `HB-105B-06`, `HB-105B-10` **không đổi**, không được sửa trong phiên
  này (đúng phạm vi khoá của brief).

- 2026-08-28 — `DEC-154` **PRODUCT IDENTITY & PURCHASE PRICE RESOLUTION**.
  Governance/spec reconciliation only: tạo `TASK-105D` spec/lineage,
  reconcile `TASK-105B` thành Public Purchase branch và `TASK-105C` thành
  Tracking HistoricalVendorMin branch, không sửa/activate code. `TASK-105B`
  budget **không đổi** `2/1/1`; không mở RC-2. Lineage mới `TASK-105D` được
  cấp theo bảng HIGH `2/0/2`, chưa dùng cycle nào. Golden/Tracking không đổi.

- 2026-08-28 — `DEC-155` **TASK-105D READINESS — DATA CONTRACT, PERSISTENCE &
  AUDIT DESIGN** (S034). Readiness/design documentation only: tạo
  `docs/spec/TASK-105D-DATA-CONTRACT.md`, chốt unified
  `PublicPurchaseSourceVersion` (HB-154-02), Tracking read-only capture
  contract, `HistoricalConfirmedRegistry` bypass rule (HB-154-03),
  `CrossSystemProductMapping` precondition cho Public Purchase fallback
  (HB-154-01), persistence/concurrency/idempotency/audit/migration contract,
  và định nghĩa vận hành cho `CHECK-105D-06/13/23/24` (HB-154-05). Sửa
  transcription `P00`/`P03`/`P11` và hai canonical documentation correction
  (HB-154-06, HB-154-07).

  ```
  app/** tests/** config/** tools/** scripts/** governance/** : 0 file thay đổi
  Golden        : 58 passed, 2 skipped (không đổi)
  Full suite    : 756 passed, 11 skipped (không đổi)
  Repair Cycle  : KHÔNG mở
  TASK-105D budget : 2 allowed / 0 used / 2 remaining  (KHÔNG ĐỔI)
  TASK-105B budget : 2 allowed / 1 used / 1 remaining  (KHÔNG ĐỔI)
  TASK-110, TASK-GOLDEN-BASELINE-001, TASK-108B budget : KHÔNG ĐỔI
  ```

  `HB-105B-03/05/06/10` **không** bị trigger bởi phiên này (không dataset
  thật nào được nạp, không code/test/tool nào được thêm); thiết kế mới định vị
  chính xác điểm trigger là lần đầu một `PublicPurchaseSourceVersion` thật
  được nạp qua `FilePriceProvider`. `HB-154-04` (review-budget lineage của
  `TASK-105C`) **KHÔNG được tự sửa** — ghi `OWNER DECISION REQUIRED` kèm ba
  phương án và khuyến nghị tại `DEC-155` §6, theo đúng V4.1 §2/§12.

- 2026-08-28 — `DEC-156` **OWNER RATIFICATION — TASK-105D READINESS;
  TASK-105C LINEAGE RECONCILIATION; TASK-105E AUTHORIZATION** (S035).
  Owner Decision recording, documentation-only.

  ```
  OR-01  APPROVED                              (unified Public Purchase source)
  OR-02  APPROVED WITH CANDIDATE-ONLY POLICY   (ALIAS_AID_UNIQUE = candidate #1,
                                                KHÔNG auto-resolve)
  OR-03  APPROVED FOR PHASE 1                  (actor khai báo, REQUIRED,
                                                cấm gọi là authenticated)
  HB-154-04  CLOSED — Owner Option B
  TASK-105E  Owner cấp task ID (Price Resolution Composition)
  ```

  Tác động ngân sách:

  ```
  TASK-105B : 2 allowed / 1 used / 1 remaining   KHÔNG ĐỔI
              TASK-105B-RC-1 vẫn CONSUMED, không chuyển, không xoá
  TASK-105C : lineage ROOT MỚI — 2 allowed / 0 used / 2 remaining
              (tách theo kiến trúc, KHÔNG phải reset ngân sách đã tiêu)
  TASK-105D : 2 allowed / 0 used / 2 remaining   KHÔNG ĐỔI
  TASK-105E : lineage MỚI — 2 allowed / 0 used / 2 remaining
  TASK-110, TASK-GOLDEN-BASELINE-001, TASK-108B : KHÔNG ĐỔI
  Repair Cycle : KHÔNG mở
  ```

  ```
  app/** tests/** config/** tools/** scripts/** governance/** : 0 file thay đổi
  Golden     : 58 passed, 2 skipped (không đổi)
  Full suite : 756 passed, 11 skipped (không đổi)
  ```

  `TASK-105D` Ready Gate blocker: 2 → **1** (chỉ còn Completion Gate freeze).
  `TASK-105C` trạng thái task **KHÔNG đổi** — vẫn `BLOCKED / NOT AUTHORIZED`.
  `HB-105B-03/05/06/10` không finding nào bị trigger bởi phiên này.

---

### Divergence decision — ĐÃ QUYẾT (`S039`, 2026-08-28, `DEC-158`)

Review point bắt buộc của `DEC-157` §2 được **đóng** bằng Owner Decision
`DEC-158`: `V4.1` §8 **Option A — INTEGRATE EARLY**. Option C **không** gia hạn.

```text
Đo tại e271c26 (sau controlled merge, trước push default):
  ahead default     : 9 commit        (ngưỡng > 10)     OK
  behind default    : 0 commit
  divergence days   : 0               (ngưỡng > 3)      OK
  cumulative LOC    : 10.055          (ngưỡng > 5.000)  VƯỢT
    production LOC      : 0     (app/**, tests/**, config/**, tools/**,
                                 scripts/**, pyproject.toml, governance/**)
    documentation LOC   : 10.055  (20 file, +9.991 / −64)
  DIVERGENCE        : INTEGRATION_DECISION_REQUIRED [ loc>5000 ]
                      → GIẢI QUYẾT bằng Option A (integrate), không phải
                        bằng cách tiếp tục divergence
  AUTHORITY         : BRANCH_WITH_UPSTREAM
  RESULT            : AUTHORITY_OK

SCOPE OPTION C — ĐÃ DÙNG HẾT (xác nhận lại):
  (1) Gate Revision S037            ✔
  (2) MỘT Freeze Finalization retry ✔  (S038)
  → không còn allowance; tiếp tục divergence sẽ là GIA HẠN, Owner từ chối

INTEGRATION:
  phương pháp   : git merge --no-ff (ancestry-preserving)
  conflict      : 0
  merge commit  : e271c26770bb6b4cecd9d4a54aea4e12a183012c
  tree == a53af1d : YES (byte-exact)
  squash        : KHÔNG
  cherry-pick   : KHÔNG

KẾT QUẢ SAU PUSH DEFAULT:
  DIVERGENCE    : WITHIN_LIMITS  (behind = 0, ahead = 0)
  bằng chứng divergence lịch sử: GIỮ NGUYÊN, không xoá
                 (§ "Branch divergence — TASK-105D lineage" và
                  § "Divergence review point — ĐÃ THỰC HIỆN (S038)" ở trên)
```

Ngân sách sau phiên — **KHÔNG ĐỔI**:

```text
TASK-105D : 2 allowed / 0 used / 2 remaining
            Repair Cycle KHÔNG mở (V4.1 §3: diff của phiên là
            documentation/governance, BLOCKING = 0)
TASK-105B, TASK-105C, TASK-105E, TASK-110,
TASK-GOLDEN-BASELINE-001, TASK-108B          : KHÔNG ĐỔI
```

Bằng chứng thực thi của phiên (E2):

```text
validate_structure           : PASS
validate_project_state       : PASS
validate_evidence            : PASS  (88 REQUIRED PASS record)
validate_task_completion     : PASS  (6 DONE task)
validate_reference_integrity : FAIL — ĐÚNG 3 issue đã biết của TASK-REM-T06
                               (/README.md, CODE_OF_CONDUCT.md,
                                CONTRIBUTING.md) — không phát sinh mới
branch_authority_check.sh    : AUTHORITY_OK
git diff --check             : sạch
Golden                       : 58 passed, 2 skipped
Full suite                   : 756 passed, 11 skipped
production diff              : 0 dòng
```

### `HARDENING` — trạng thái sau hợp nhất (preserve, KHÔNG repair)

```text
H-05           MỞ  — ranking_method_id OPTIONAL vs hashed; đổi data contract
                     §6.7; re-trigger ghi trong CHECK-105D-08
HB-105D-F2-01  MỞ  — data contract §3.3 câu 8 "bộ ba" vs INV-55 "CẢ BỐN"
HB-105D-F2-02  MỞ  — data contract §16.1 stale ("CHƯA CÓ CHỦ" vs §16.3 GRANTED)
HB-105D-F2-03  MỞ  — 13 invariant chưa có gate assertion riêng
```

Cả bốn **vẫn phân loại `HARDENING`**, không nâng thành `BLOCKING` (không có
evidence mới), không hạ khỏi `HARDENING`. `docs/spec/TASK-105D-DATA-CONTRACT.md`
không bị sửa trong phiên này.
- 2026-09-02 — `TASK-PRA-002` mở lineage mới tại phiên Roadmap Finalization
  S079 (`BASE_SHA = 553d8a3`). `effective_risk = HIGH` (double-count →
  sai KPI/lương), 2 cycle khả dụng, **0 đã dùng**. Task READY, gate FROZEN
  (17 check). `TASK-PRA-001` không đổi: DONE, remaining = 0.
- 2026-09-03 — `TASK-PRA-003` mở lineage mới tại phiên Roadmap Finalization
  S095 (`BASE_SHA = facf090`). `effective_risk = MEDIUM` (tầng chỉ-đọc; hỏng
  = hiển thị sai một số quản lý, không ghi đè dữ liệu), 1 cycle khả dụng,
  **0 đã dùng**. Task READY_FOR_IMPLEMENTATION, gate FROZEN (14 check / 12
  REQUIRED). `TASK-PRA-002` không đổi: DONE, 1/2 used, remaining = 1.
  `TASK-PRA-001` không đổi: DONE.
- 2026-09-03 — `TASK-PRA-005` mở lineage mới tại phiên Contract Freeze S107
  (`BASE_SHA = 1ebb0021e13f85fe7ac7825e1219583e4c682889`, sau Discovery
  S105 + tích hợp S106). Xem chi tiết ở "Root Task: TASK-PRA-005" bên dưới.
  `TASK-PRA-002`/`003`/`004` không đổi: DONE.

---

## Root Task: TASK-PRA-005

Lineage **mới** (root task riêng, khai ở Metadata của
`docs/tasks/TASK-PRA-005-san-pham.md`). KHÔNG kế thừa và KHÔNG tiêu ngân
sách của `TASK-PRA-001`, `TASK-PRA-002`, `TASK-PRA-003`, `TASK-PRA-004` hay
bất kỳ lineage nào khác.

Mở tại phiên Contract Freeze S107 (2026-09-03), sau Discovery S105
(`docs/sessions/S105-pra-005-san-pham-discovery.md`, docs-only) và xác minh +
tích hợp fast-forward S106. `BASE_SHA =
1ebb0021e13f85fe7ac7825e1219583e4c682889` (HEAD nhánh canonical
`claude/extract-upload-repo-gq2ws4` lúc freeze contract, đã verify khớp
EXACT kỳ vọng đầu phiên).

```
root_task: TASK-PRA-005
effective_risk: MEDIUM
repair_cycles_allowed: 1
repair_cycles_used: 0
repair_cycles_remaining: 1
```

`MEDIUM` theo **Blast Radius tính theo failure path**
(`governance/core/V4_1_POLICY_FREEZE.md` §4), KHÔNG theo tên module:

- **BR-1** — một dòng dịch vụ/phí bị lọc âm thầm khỏi bảng mặt hàng, làm
  tổng bảng KHÔNG còn khớp tổng kỳ mà Owner không biết. Giảm nhẹ:
  CHECK-PRA005-04 (Σ nhóm = tổng kỳ) + CHECK-PRA005-08 (dòng dịch vụ/phí vẫn
  nằm trong bảng) + OD-PRA005-02 (DEC-173).
- **BR-2** — ô LN KPI của một mặt hàng bị coalesce về `0` thay vì `—` khi
  không có dòng `AUTO` nào, khiến Owner đọc nhầm "không lãi" thành "không có
  dữ liệu". Giảm nhẹ: CHECK-PRA005-06 (`NULL != 0`, EAC-2/EAC-3).
- **BR-3** — nhãn/khoá gộp ngụ ý canonical Product Identity trong khi thực
  chất là mô tả thô đã chuẩn hoá, khiến Owner tin nhầm hai dòng tách biệt
  (ví dụ `FTKB50ZVMV`) là hai sản phẩm khác nhau thật. Giảm nhẹ:
  CHECK-PRA005-02 + CHECK-PRA005-07 (split được bảo toàn có kiểm chứng) +
  disclosure bắt buộc trên trang (mục 5 file task) + OD-PRA005-01 (DEC-173).
- **KHÔNG phải HIGH** vì: toàn bộ touch area CHỈ-ĐỌC (không một câu
  `INSERT`/`UPDATE`/`DELETE` nào); không ghi đè dữ liệu đã lưu; không đổi
  KPI/lương đã tính; không chạm bất biến no-double-count (thuộc
  `TASK-PRA-002`, PRA-005 chỉ đọc lại kết quả của nó); không tạo product
  identity thứ hai (Tracking vẫn là authority duy nhất).

### Điều kiện mở repair cycle

Finding KHÔNG tự động trở thành repair work. Chỉ mở cycle khi finding đe doạ
TRỰC TIẾP một trong bốn điều:

1. tính trung thực/reconciliation của tổng doanh thu-số lượng-LN KPI cấp
   mặt hàng so với phân tích đã accepted;
2. an toàn `NULL`/coverage (EAC-2/EAC-3);
3. bảo toàn OD-PRA005-01/OD-PRA005-02 (KHÔNG âm thầm gộp/lọc);
4. ranh giới PII (EAC-9, tiền lệ `TASK-PRA-004` mục 14.4).

Finding ngoài bốn nhóm đó: `HARDENING` kèm RE-TRIGGER CONDITION cụ thể
(V4.1 §7) hoặc `OUT_OF_SCOPE`. Vượt 1 cycle → `OWNER_EXTENSION REQUIRED`;
KHÔNG tách sub-unit, KHÔNG đổi tên task, KHÔNG mở nhánh mới để reset ngân
sách (V4.1 §2).

### Trạng thái tại S107

```
Discovery                    : XONG (S105, docs-only, PRODUCTION_CODE_DELTA = 0)
Contract Freeze               : XONG (S107, docs-only, PRODUCTION_CODE_DELTA = 0)
BLOCKING_FINDINGS            : 0
Non-blocking đã ghi          : FIND-PRA005-01 (split product_key, KHÔNG BLOCKING,
                               xử lý bằng cách gọi tên + OD-PRA005-01)
                               FIND-PRA005-02 (nhãn "Số sản phẩm" va chạm EAC-5,
                               đã đổi nhãn)
                               FIND-PRA005-03 (product_group_final là hằng số,
                               không phải category — ghi nhớ cho phiên sau)
Owner Decisions               : OD-PRA005-01, OD-PRA005-02 — khoá tại S107,
                               ghi PROJECT/PROJECT_DECISIONS.md DEC-173
repair_cycles_used            : 0 / 1  — Discovery + Contract Freeze KHÔNG tiêu cycle
cycles: []
```

### Trạng thái tại S108 (Implementation)

```
Implementation                : COMPLETE / REVIEW_PENDING (S108, nhánh
                               claude/pra-005-v1-implementation-3dcd5k,
                               CHƯA tích hợp canonical)
PRODUCTION_PYTHON_LOC_DELTA   : 126 dòng (ngân sách mềm 200)
CHECK PASS (E1)                : 12/14 REQUIRED (CHECK-PRA005-01..12)
CHECK-PRA005-13 (RECOMMENDED)  : NOT_APPLICABLE (drill-down DEFERRED_WITHIN_
                               CONTRACT, mục 18 — không chặn task)
CHECK-PRA005-14/15             : NOT_TESTED (Independent Review E2 +
                               Owner Production Acceptance — chưa chạy)
repair_cycles_used             : 0 / 1  — KHÔNG có Independent Review nào
                               chạy ở S108 để mở repair cycle; một điều chỉnh
                               thiết kế nội bộ (product_summary() chuyển
                               sang tái dụng period_totals()) là tự-review
                               trước khi hoàn tất, KHÔNG phải phản hồi từ
                               review — không tính vào ngân sách repair.
cycles: []
```

### Trạng thái tại S109 (Independent Review E2)

```
Independent Review E2         : ĐÃ CHẠY — ACCEPT (S109)
                               docs/reviews/TASK-PRA-005-INDEPENDENT-REVIEW-RECORD.md
REVIEW_CYCLE_USED             : 1 / 1  — chu kỳ Independent Review E2 DUY NHẤT
                               đã hoạch định cho lineage PRA-005, nay đã dùng
repair_cycles_used            : 0 / 1  — KHÔNG có finding BLOCKING nào ⟹
                               KHÔNG mở repair batch; ngân sách repair còn
                               nguyên
cycles: [
  { id: "PRA-005-V1-IMPLEMENTATION-REVIEW-1", session: "S109",
    target: "18ab5d39a15b224d34aa04e5c6bbe8261f60efeb",
    result: "ACCEPT", blocking: 0, non_blocking: 2, repair: "NO" }
]
BLOCKING_FINDINGS             : 0

### Trạng thái tại S110 (Production Acceptance Attempt)

```
Implementation                : ĐÃ tích hợp canonical (HEAD = commit S109,
                               1a011ee66f9e2b2ffee4d04f6864bfb0eeb45948)
Production Acceptance attempt : STOP — session KHÔNG có egress tới
                               reports.tinphatcrm.com / api.render.com
                               (đúng policy denial đã ghi nhận ở
                               CHECK-PRA002-15/S093); gate CHECK-PRA005-15
                               chỉ định rõ tác nhân Owner
CHECK-PRA005-15                : NOT_TESTED (không đổi)
Owner runbook                  : docs/sessions/S110-pra-005-production-
                               acceptance-attempt.md mục 5
repair_cycles_used             : 0 / 1 (không đổi — đây không phải finding
                               BLOCKING, là giới hạn về ai/ở đâu thực thi)
cycles: [] (không cycle mới)
BLOCKING_FINDINGS              : 0
TASK-PRA-005 overall           : CHƯA DONE (PRODUCTION_ACCEPTANCE_PENDING)
```

### Trạng thái tại S111 (Owner Production Acceptance + Closeout) — CUỐI CÙNG

```
Owner Production Acceptance    : PASS — Owner tự mở reports.tinphatcrm.com
                               thật, kỳ Tháng 09/2026, 4 cặp số reconcile
                               EXACT (quantity 185, revenue 1.470.385.000,
                               kpi 9.586.667, coverage 34/142)
CHECK-PRA005-15                 : NOT_TESTED → PASS
COMPLETION_GATE                 : 14/14 REQUIRED PASS · 1/1 RECOMMENDED
                               NOT_APPLICABLE (drill-down, DEFERRED_WITHIN_
                               CONTRACT)
repair_cycles_used              : 0 / 1 (không đổi — 0 finding BLOCKING)
cycles: [] (không cycle mới)
BLOCKING_FINDINGS               : 0
NON_BLOCKING (giữ nguyên)       : FIND-PRA005-01/02/03, FIND-PRA005-R1/R2 —
                               không repair
TASK-PRA-005 overall            : DONE
Review Budget lineage TASK-PRA-005: ĐÓNG — 1/1 Independent Review đã dùng,
                               0/1 repair cycle đã dùng, không còn hoạt động
                               nào mở trên lineage này
```
NON_BLOCKING_FINDINGS         : 2 (FIND-PRA005-R1 độ chính xác LOC báo cáo ·
                               FIND-PRA005-R2 thứ tự NULL doanh thu
                               SQLite/PostgreSQL — chưa đạt tới trên dữ liệu
                               đã nghiệm thu)
CHECK PASS                    : 13/14 REQUIRED (CHECK-PRA005-01..12 E1 +
                               CHECK-PRA005-14 E2)
CHECK-PRA005-15               : NOT_TESTED (Owner Production Acceptance)
FINAL_REVIEWED_HEAD_SHA       : 18ab5d39a15b224d34aa04e5c6bbe8261f60efeb
INTEGRATION_READY             : YES
CANONICAL_INTEGRATION_STATUS  : NOT_YET_INTEGRATED
```

`TASK-PRA-005` = `IMPLEMENTED` + `REVIEWED` (KHÔNG phải `DONE` — còn
`CHECK-PRA005-15` Owner Production Acceptance).
`NEXT_VERTICAL_ACTION = PRA-005 CONTROLLED INTEGRATION`. Chi tiết:
`docs/reviews/TASK-PRA-005-INDEPENDENT-REVIEW-RECORD.md` và
`docs/sessions/S108-pra-005-major-implementation.md`.

---

## Root Task: PHB-01

Lineage **mới** (Product Identity Manual Resolution V1, contract
`PHB-PI-001`, khai ở `docs/sessions/S112-phb-01-product-identity-manual-
resolution.md`). Vertical này chạm CẢ HAI repo (Reports + Tracking — §5
contract cho phép tường minh).

```
root_task: PHB-01
effective_risk: PENDING_OWNER_DECISION — chưa được Owner/reviewer gán một
    con số chính thức. S112 §7 ghi rõ: "một con số tự đặt là dựng ngân sách
    trên một giả định" — phiên implementation/review KHÔNG tự gán. Ghi
    nhận đây là hành động còn thiếu, không phải giá trị mặc định.
repair_cycles_allowed: PENDING_OWNER_DECISION (phụ thuộc effective_risk
    chưa gán — theo bảng ngân sách đã freeze ở đầu file này)
repair_cycles_used: 1 (lịch sử thực tế đã xảy ra — xem cycles: bên dưới;
    số này ghi những gì đã xảy ra, KHÔNG suy ra được repair_cycles_remaining
    khi chưa có repair_cycles_allowed)
repair_cycles_remaining: PENDING_OWNER_DECISION
```

### Trạng thái (2026-09-04, governance sync sau focused re-review)

```
PHB01_STATUS       = IMPLEMENTED (CODE_REVIEW_CLEARED) — CHƯA DONE
CODE_REVIEW_GATE   = PASS
BLOCKING_01        = CLOSED
D8_FINAL           = PASS
H_REGRESSION       = PASS
PRODUCTION_DEPLOY  = NOT_DONE
PRODUCTION_E2E     = NOT_RUN
SCOPE_DRIFT        = NO
```

Independent Review #1 (S112, trong phiên implementation) — `CODE_REVIEW_GATE
= FAIL`, đúng một finding blocking: `BLOCKING-01` (nhánh di trú của
`loadInv()` bên Tracking ghi thiếu `giaV2`/`giaV3`/`tay`/`lotRequired`, làm
di trú không bao giờ kết thúc và xoá `lo`/`cong`/`congTay` người dùng đã
nhập).

Bounded repair — Tracking `f0873942a419bc2b18431e6a94668a81eb02235f` →
`53993f18f67e76927a2b7e115fdc61301cdfb4ec` (đúng 2 file:
`public/index.html` 1 hunk logic + APP_BUILD b124→b125,
`kiem/phan-loai-ten-hang.js` +121 dòng test).

Focused Independent Re-review (phiên độc lập riêng, read-only, sau repair)
— `CODE_REVIEW_GATE = PASS`, `BLOCKING_01 = CLOSED`, `D8_FINAL = PASS`,
`H_REGRESSION = PASS`, `NEW_BLOCKING_FINDINGS = NONE`. Xác minh bằng
mutation testing trên `public/index.html` thật (revert dòng sửa về hình
dạng cũ → 8 assertion đỏ, đúng hồi quy đã báo cáo), không chỉ đọc báo cáo
sửa lỗi. Bằng chứng đầy đủ:
`docs/reviews/PHB-01-BLOCKING-01-FOCUSED-REVIEW-RECORD.md`.

Phiên governance-sync ghi record này đã độc lập tái xác minh (không chỉ
tin artifact): diff `f0873942..53993f18` đúng 2 file; snippet dòng ~7065
khớp nguyên văn; `db.ref("inv").set(` không còn lời gọi thật; 9 chỗ gọi
`saveInvPaths`; và **chạy thật** `npm test` trên `53993f18` cho đúng kết
quả artifact nêu: `kiem/phan-loai-ten-hang.js` 72 đạt/0 hỏng,
`59 bộ · 2572 đạt · 0 hỏng · 2 bỏ qua`.

```
cycles:
- id: PHB01-RC-1
  base_sha: f0873942a419bc2b18431e6a94668a81eb02235f
  head_sha: 53993f18f67e76927a2b7e115fdc61301cdfb4ec
  finding: BLOCKING-01 — loadInv() cloud migration branch wrote only 4 of 8
    fields (giaV2/giaV3/tay/lotRequired missing), so migration never
    terminated and lo/cong/congTay entered by the operator were wiped on
    every subsequent page load.
  fix: migration write unit changed from four price tables to the whole
    card ({cu, moi}) via saveInvPaths()/update() — matches the invUndoDay()
    precedent already in the codebase. map untouched.
  result: focused re-review PASS (mutation-tested); Tracking full suite
    59 bộ · 2572 đạt · 0 hỏng · 2 bỏ qua; Reports delta = docs-only, 0 dòng
    mã chức năng.
```

**PHB-01 KHÔNG được đánh `DONE`** ở bản ghi này. `PRODUCTION_DEPLOY` và
`PRODUCTION_E2E` vẫn là các gate còn mở, độc lập với `CODE_REVIEW_GATE`.
`NEXT_VERTICAL_ACTION`: (1) Owner gán `effective_risk` chính thức cho
lineage này để đóng phần `PENDING_OWNER_DECISION` ở trên; (2) merge vào
nhánh production của từng repo; (3) deploy; (4) một lượt `PRODUCTION_E2E`
thật do Owner thực hiện (xem
`docs/sessions/S112-phb-01-product-identity-manual-resolution.md` mục 7
cho thủ tục đầy đủ). Không mở `PHB-02` trước khi (1)-(4) xong.
