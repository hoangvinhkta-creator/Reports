# RÀ SOÁT ĐỘC LẬP E2 (E2 INDEPENDENT REVIEW)

Review ID:
DEC-154-PRODUCT-IDENTITY-PRICE-RESOLUTION-INDEPENDENT-REVIEW

Task / Release:
Governance / Specification Reconciliation — `DEC-154` PRODUCT IDENTITY &
PURCHASE PRICE RESOLUTION (`TASK-105B`, `TASK-105C`, `TASK-105D`,
`TASK-108B` pointer, price-resolution dependency graph).

Reviewer Session:
S033 — Independent Governance / Specification Review (read-only).
Recovery sau một phiên Codex independent-review bị gián đoạn do quota.

Executed By:
Claude Code (independent reviewer session, read-only)

Timestamp:
2026-08-28

```text
reviewed_target_sha = 442404d1fdb24a134625f53c7ede5f3377416177
base_sha            = 573e051e093cd850c9efb13891bf6dee5654f0c6
default_branch      = claude/extract-upload-repo-gq2ws4
default_tip         = 573e051e093cd850c9efb13891bf6dee5654f0c6
review_branch       = review/product-identity-price-resolution-reconciliation
reconciliation_branch = governance/product-identity-price-resolution-reconciliation
```

## Scope

Đánh giá reconciliation tại exact TARGET SHA: tính nhất quán với Governance
V4.1, tính đúng của `DEC-154`, việc bảo toàn `DEC-151`/`DEC-152`/`DEC-153`,
dependency graph, hardening trigger audit, và điều kiện an toàn để mở một
phiên `TASK-105D` readiness/data-contract + persistence/audit design.

Không implementation, không repair, không merge, không freeze, không đổi
trạng thái task, không mở Repair Cycle.

## Xử Lý Phiên Codex Bị Gián Đoạn (Interrupted Session Recovery)

Không kế thừa verdict/finding nào của phiên Codex bị gián đoạn. Review được
thực hiện lại từ đầu trên canonical governance + repository evidence tại
TARGET SHA.

Kiểm tra artifact/diff chưa commit còn sót lại:

```text
git status --porcelain --untracked-files=all  →  rỗng
git worktree list                            →  chỉ một worktree
```

Không có artifact chưa commit nào từ phiên Codex. Target review là sạch.
Handoff `docs/sessions/S032-product-identity-price-resolution-reconciliation.md` (do Codex viết, đã commit trong TARGET)
được coi là **implementer claim**, không phải evidence — mọi số liệu trong
đó đã được chạy lại độc lập ở mục "Xác Minh Độc Lập" bên dưới.

## Tài Liệu Đầu Vào Đã Đọc (Inputs Read)

Canonical governance:
- `CLAUDE.md`
- `governance/core/V4_1_POLICY_FREEZE.md`
- `governance/core/00_SESSION_ORCHESTRATION.md`
- `governance/core/RULE_PRECEDENCE.md`
- `governance/core/EVIDENCE_STANDARD.md`
- `governance/templates/E2_INDEPENDENT_REVIEW_TEMPLATE.md`
- `docs/reviews/README.md`

Repository state / target:
- `git diff 573e051e..442404d1` (toàn bộ 10 file, 1294 insert / 56 delete)
- `PROJECT/PROJECT_DECISIONS.md` — `DEC-151`, `DEC-152` §5/§11, `DEC-153`,
  `DEC-154`
- `PROJECT/PROJECT_PROGRESS.md`, `PROJECT/REVIEW_BUDGET_LEDGER.md`,
  `PROJECT/LO_TRINH_DE_HIEU.md`
- `docs/tasks/TASK-105B-file-price-provider.md`,
  `docs/tasks/TASK-105C-historical-vendor-price-provider.md`,
  `docs/tasks/TASK-105D-product-identity-resolver.md`,
  `docs/tasks/TASK-108B-eligible-costs-owner-definition.md` Phần XII
- `docs/sessions/S032-product-identity-price-resolution-reconciliation.md`
- `app/modules/pricing/provider.py`, `app/modules/pricing/file_price_provider.py`

## Xác Minh Độc Lập (Independent Verification)

| Check ID | Status | Evidence Level | Evidence | Executed By | Timestamp |
|---|---|---|---|---|---|
| R-TARGET | PASS | E2 | `git rev-parse HEAD` = `442404d1fdb24a134625f53c7ede5f3377416177`; worktree CLEAN; upstream 0/0 | Claude reviewer | 2026-08-28 |
| R-ANCESTRY | PASS | E2 | `git merge-base --is-ancestor 573e051e 442404d1` → true; `git log BASE..TARGET` = đúng 1 commit `docs: reconcile product identity and price resolution` | Claude reviewer | 2026-08-28 |
| R-BASE-IS-DEFAULT | PASS | E2 | `origin/claude/extract-upload-repo-gq2ws4` tip = `573e051e…` = BASE | Claude reviewer | 2026-08-28 |
| R-PRODUCTION-DIFF | PASS | E2 | `git diff --name-only BASE..TARGET -- app tests config scripts tools pyproject.toml` → rỗng | Claude reviewer | 2026-08-28 |
| R-DIFF-CHECK | PASS | E2 | `git diff --check BASE..TARGET` → exit 0, không output | Claude reviewer | 2026-08-28 |
| R-STRUCTURE | PASS | E2 | `validate_structure.py` → `GOVERNANCE STRUCTURE: PASS`, 21 required paths | Claude reviewer | 2026-08-28 |
| R-STATE | PASS | E2 | `validate_project_state.py` → `PROJECT STATE: PASS` | Claude reviewer | 2026-08-28 |
| R-EVIDENCE | PASS | E2 | `validate_evidence.py` → `EVIDENCE VALIDATION: PASS`, 88 REQUIRED PASS records | Claude reviewer | 2026-08-28 |
| R-COMPLETION | PASS | E2 | `validate_task_completion.py` → `TASK COMPLETION: PASS`, 6 DONE tasks | Claude reviewer | 2026-08-28 |
| R-REFERENCE | BLOCKED (pre-existing) | E2 | `validate_reference_integrity.py` FAIL với đúng 3 ref của `TASK-REM-T06` (ba token README / CODE_OF_CONDUCT / CONTRIBUTING ở repository root). Chạy lại trên worktree tách rời tại BASE → **cùng đúng 3 lỗi đó**. Pre-existing, không do TARGET tạo ra. TARGET quét 139 file vs BASE 137 (2 file .md mới), không thêm ref hỏng | Claude reviewer | 2026-08-28 |
| R-GOLDEN | PASS | E2 | Python 3.11.15 / pytest 9.1.1: `python3 -m pytest tests/test_golden_baseline.py -q` → `58 passed, 2 skipped` | Claude reviewer | 2026-08-28 |
| R-FULL-SUITE | PASS | E2 | `python3 -m pytest -q` → `756 passed, 11 skipped in 17.52s` | Claude reviewer | 2026-08-28 |
| R-BRANCH-AUTHORITY | PASS | E2 | `scripts/branch_authority_check.sh` → `AUTHORITY_OK`, `BRANCH_WITH_UPSTREAM`, ahead default 1 / behind 0, divergence days 0, cumulative LOC 1350, `DIVERGENCE = WITHIN_LIMITS` (V4.1 §8) | Claude reviewer | 2026-08-28 |
| R-ID-UNIQUE | PASS | E2 | `DEC-154` xuất hiện đúng 1 lần, không tồn tại `DEC-155+`; `TASK-105D` không đụng ID nào có sẵn trong `docs/tasks/` | Claude reviewer | 2026-08-28 |
| R-NO-RC2 | PASS | E2 | Ledger `TASK-105B` giữ `2 allowed / 1 used / 1 remaining`; `TASK-105D` lineage mới `2/0/2`, `cycles: []`. Không cycle nào mở | Claude reviewer | 2026-08-28 |
| R-STATE-AUTHORITY | PASS | E2 | Không có `FROZEN`/`DONE`/`ACCEPT_AS_IS`/`DESCOPE` nào được ghi bởi phiên reconciliation. `TASK-105C → BLOCKED` có nêu rõ gate (Completion Gate change proposal chưa refreeze) — hợp lệ theo V4.1 §12 | Claude reviewer | 2026-08-28 |

## Sai Lệch So Với Tuyên Bố Của Người Triển Khai (Mismatches With Implementer Claims)

Toàn bộ 9 evidence record trong `S032` handoff đã được chạy lại độc lập và
**khớp chính xác** (validators, Golden `58/2`, full suite `756/11`,
`git diff --check`, no production diff, branch authority).

Sai lệch duy nhất, không trọng yếu: khối "Git Checkpoint" của handoff ghi
`final tree: DIRTY — chưa commit`. Đó là ảnh chụp đúng tại thời điểm viết;
tại TARGET SHA cây đã commit và CLEAN. Tên nhánh `governance/product-identity-
price-resolution-reconciliation` trong handoff là **đúng** — ref đó tồn tại
trên origin và trỏ đúng `442404d1`, cùng SHA với nhánh review. Không phải
finding.

## Findings

Không có BLOCKING finding. Căn cứ V4.1 §5/§7: không tồn tại current
production path cho bất kỳ vấn đề nào bên dưới — `PendingPriceProvider` vẫn
là default, `FilePriceProvider` NOT ACTIVATED, `git diff` trên
`app/**`/`tests/**`/`config/**` rỗng, Golden và full suite PASS.

### HARDENING

**HB-154-01 — `P03` thiếu điều kiện tiên quyết `CrossSystemProductMapping`.**
`DEC-154` §7 (prose) quy định identity `TRACKING` chỉ fallback sang Public
Purchase khi *(a)* không có valid vendor candidate tại `sale_date` **và**
*(b)* có cross-system mapping hợp lệ. Bảng chuẩn tắc `P01–P10` ghi `P03` là
"TRACKING + no valid vendor candidates → Public Purchase fallback", bỏ mất
điều kiện *(b)*. Theo V4.1 §11 (ARTIFACT INTERNAL PRECEDENCE) bảng chuẩn tắc
thắng prose khi xung đột, nên một implementer đọc đúng luật precedence có thể
kết luận "luôn fallback" và buộc phải đoán Public Purchase code khi không có
mapping — vi phạm trực tiếp `DEC-154` §5 ("Không giả định code bằng nhau").
`P06` không đóng được lỗ này vì "no valid Public Purchase price" không hiển
ngôn bao gồm "không có mapping để tra".
*Re-trigger:* phải sửa trước khi `P01–P10` được biến thành executable
Completion Gate, và trước khi scope lock của price-resolution composition
được freeze.

**HB-154-02 — Public Purchase identity catalog và price table chưa được
tuyên bố có thể đến từ một nguồn versioned duy nhất.**
`DEC-154` §9 chỉ định nghĩa hợp đồng dữ liệu phía **giá** (`product_code`,
`effective_from`, `effective_to`, `purchase_price`, `source/provenance`).
`TASK-105D` lại tham chiếu một "Public Purchase catalog" riêng cho phía
**identity** (`product_code`, `product_name`, aliases) và liệt kê nó trong
Dependencies là "chưa được cung cấp canonical". Không văn bản nào nói hai mặt
này được phép/nên là hai projection của **cùng một** versioned Public
Purchase source. Hệ quả vận hành: readiness session kế tiếp hoàn toàn có thể
đặc tả hai file phải nhập tay độc lập — đúng loại quy trình thủ công thừa cần
tránh. Kèm theo là một lỗ hổng replay: `DEC-154` §9 yêu cầu replay theo
`sale_date` cho giá và `TASK-105D` yêu cầu catalog snapshot có version,
nhưng **không luật nào ràng buộc catalog version với price version** cho cùng
một lần replay; một `source_product_code` có giá nhưng vắng trong catalog sẽ
là identity không thể tra tới, hành vi chưa định nghĩa.
*Re-trigger:* phiên `TASK-105D` readiness/data-contract phải quyết định
*(a)* một versioned Public Purchase source có cung cấp đồng thời identity
fields và price fields hay không, và *(b)* catalog version ↔ price version
được ràng buộc thế nào khi replay — **trước khi** freeze catalog snapshot
format hoặc Public Purchase schema của `FilePriceProvider`.

**HB-154-03 — `P01–P10` không có rule nào cho nhánh bypass pre-cutover.**
Toàn bộ bảng `P01–P10` là post-cutover. Luồng
`HISTORICAL_CONFIRMED_REPORT` bypass (`sale_date < 2026-09-01`) chỉ tồn tại
trong prose (`DEC-154` §2, `TASK-108B` §98) và trong `CHECK-105D-01`. Vì
`DEC-154` §11 gọi `P01–P10` là "canonical integration contract", một
implementation xây đúng theo bảng có thể định tuyến cả bản ghi pre-cutover
qua resolver/provider.
*Re-trigger:* cùng thời điểm với HB-154-01 — khi `P01–P10` trở thành
executable gate, bổ sung một rule bypass pre-cutover.

**HB-154-04 — `TASK-105C` vẫn dùng chung review-budget lineage của
`TASK-105B` sau khi composition biện minh cho việc dùng chung đã bị
supersede.** `TASK-105C` được đặt vào lineage `TASK-105B` vì kiến trúc cũ
"`HistoricalVendorPriceProvider` compose `FilePriceProvider`" (`DEC-152`
§11). `DEC-154` đã gỡ bỏ composition đó, nhưng lineage giữ nguyên, trong khi
`TASK-105D` lại được cấp lineage mới. Hệ quả: implementation `TASK-105C`
bước vào với chỉ **1 blocking repair cycle còn lại**, đã bị tiêu một phần bởi
`TASK-105B-RC-1` — một repair về `NaN`/vô cực trong `FilePriceProvider`, nay
là code thuộc nhánh khác. Rủi ro `OWNER_EXTENSION REQUIRED` sớm vì lý do
không liên quan tới `TASK-105C`.
Lưu ý: V4.1 §2 cấm tạo lineage mới **để reset ngân sách**, nên đây là quyết
định của Owner, không phải việc reviewer hay implementer tự sửa.
*Re-trigger:* phiên refreeze Scope/Completion Gate của `TASK-105C` phải nêu
câu hỏi lineage này cho Owner trước khi cấp `READY`.

**HB-154-05 — Một số Completion Gate của `TASK-105D` chưa testable như đang
viết.** `CHECK-105D-23` ("≤1 normal action") và `CHECK-105D-24` ("0 normal
action") — cùng `DEC-154` §17 — dựa trên khái niệm "thao tác bình thường"
chưa được định nghĩa ở bất kỳ đâu (Enter có tính không? cuộn trang? xác nhận
hàng loạt?). `CHECK-105D-06` ("model mơ hồ") không có định nghĩa vận hành cho
"mơ hồ". `CHECK-105D-13` ("`PENDING_PRODUCT` được hỗ trợ rõ ràng") là phát
biểu định tính. Gate đang ở trạng thái DRAFT nên đây chưa phải vi phạm.
*Re-trigger:* trước khi freeze Completion Gate `TASK-105D`, phải có định
nghĩa vận hành đo được cho các check này.

**HB-154-06 — `DEC-154` "Impact" không liệt kê `CLAUDE.md` dù commit có sửa
file này.** Mục Impact liệt kê `TASK-105B`, `TASK-105C`, `TASK-108B`,
progress, roadmap, review ledger, session handoff — thiếu `CLAUDE.md`. Bản
thân thay đổi là **đúng sự thật**: đã xác minh tại BASE rằng
`PROJECT/PROJECT_PROGRESS.md:20` đã ghi `V4.1 = FULLY_ENFORCED` từ
2026-08-27, tức `CLAUDE.md` chỉ đang lỗi thời và nay được đồng bộ; và thay
đổi đã được công bố trong "Files Changed" của handoff, không âm thầm. Vấn đề
thuần tuý là bản ghi quyết định chưa đầy đủ so với diff.
*Re-trigger:* phiên có authority kế tiếp chạm `DEC-154` bổ sung `CLAUDE.md`
vào Impact.

**HB-154-07 — Còn con trỏ current-state lỗi thời nói `TASK-105C …
IMPLEMENTATION = READY`.** Cụ thể `PROJECT/PROJECT_PROGRESS.md:369` và
`docs/tasks/TASK-108B-eligible-costs-owner-definition.md:2527`. Cả hai đã
được phủ bởi mệnh đề supersede trọn gói ở đầu file (PROGRESS khối "Current
Price Architecture — DEC-154"; `TASK-108B` header Phần XII), và việc giữ
nguyên văn bản lịch sử là đúng V4.1 §10. Nhưng theo tiền lệ `DEC-118` (hai
nhánh trùng việc thật vì đọc trạng thái lỗi thời), một agent grep
`IMPLEMENTATION = READY` vẫn có thể tiếp đất vào đúng hai dòng đó.
*Re-trigger:* phiên có authority kế tiếp chạm hai file này thêm marker inline
`SUPERSEDED BY DEC-154` tại chỗ — không xoá văn bản lịch sử.

### OUT_OF_SCOPE

**OS-154-01 — Nợ reference integrity của `TASK-REM-T06` (3 ref).** Đã xác
minh pre-existing bằng cách chạy validator trên worktree tách rời tại BASE:
đúng 3 lỗi giống hệt. Không thuộc contract của phiên reconciliation.

### Quan Sát Không Nâng Thành Finding (Observations)

- Chồng lấn nhẹ giữa các gate `TASK-105D`: `G04`/`G10`/`G24` cùng xoay quanh
  "alias đã confirm không tốn thao tác", `G26`/`G28` cùng xoay quanh
  "Public Purchase identity không cần Tracking giả". Chồng lấn, **không mâu
  thuẫn** — chấp nhận được cho một gate DRAFT.
- `sale_date` trong seam `PriceProvider` đã frozen là `datetime.date`
  (`app/modules/pricing/provider.py:24`), nên so sánh biên
  `sale_date >= 2026-09-01` không có mơ hồ timezone. Không cần finding.

## Đánh Giá Theo Từng Mục Tiêu Review

**1. Nhất quán Governance V4.1 — ĐẠT.** Budget theo root task lineage được
tôn trọng (`TASK-105B` giữ `2/1/1`, không reset; `TASK-105D` là root task
thật sự mới, không phải rename/tách nhánh để reset — V4.1 §2). Không mở
Repair Cycle #2 (§3). Effective Risk chấm theo failure path
`sai identity → sai nguồn giá → sai KpiPurchasePrice → sai KPI/lương`, không
chấm theo tên file (§4); Golden không bị dùng để hạ blast radius vì Golden
chỉ phủ `PendingPriceProvider` (§4.1) — reasoning này đúng và được nêu rõ ở
cả ledger lẫn task file. State Authority Matrix được tôn trọng (§12).
Divergence WITHIN_LIMITS (§8).

**2. Phản ánh đúng `DEC-154` — ĐẠT.** `CUTOVER_DATE = 2026-09-01`, phân loại
bằng `sale_date` không dùng `import_date`, pre-cutover confirmed report là
authority và bypass resolver/catalog/provider, không retroactive remap. Hai
namespace `TRACKING`/`PUBLIC_PURCHASE` không collision; Tracking không bắt
buộc cho mọi valid product; Tracking MISS + Public Purchase deterministic
unique match → `PUBLIC_PURCHASE:<code>` không tạo Tracking giả; fuzzy-only
không có production authority; alias memory persistent; rejection/correction
auditable; `CrossSystemProductMapping` explicit/persistent/correctable;
identity không đổi vì price fallback (`P10`, `G16`). Tất cả có mặt và nhất
quán giữa `DEC-154`, `TASK-105D`, `TASK-105C`, `TASK-105B`, PROGRESS và
`TASK-108B` Phần XII.

**3. Không phá `DEC-151`/`152`/`153` — ĐẠT.** `Price(NCC,D)` = record gần
nhất `<= D`; `HistoricalVendorMin` = MIN mọi candidate hợp lệ; sentinel `0` =
HẾT HÀNG và bị loại; không áp ngược trạng thái NCC/config hiện tại — tất cả
được tái khẳng định nguyên văn trong `TASK-105C`. Supersession được giới hạn
đúng và hợp thẩm quyền: `DEC-152` §5 chỉ bị supersede ở **giả định canonical
identity bắt buộc là Tracking `<MÃ>`**, còn lệnh cấm fuzzy giữ nguyên;
`DEC-152` §11 tự nhận là "quyết định kỹ thuật của phiên, không phải Owner
Decision", nên một Owner Decision (`DEC-154`) supersede nó là hợp lệ.
`DEC-153` (`TASK-105B = FROZEN`) được bảo toàn — `TASK-105B` vẫn
`FROZEN + INTEGRATED + RC-1 INTEGRATED + NOT DONE`, RC-1 history không bị
rewrite.

**4. Dependency cycle — KHÔNG CÓ.** `TASK-105D` không consume output của
`105C`/`105B`; `105C` và `105B` consume identity từ `105D`.
`CrossSystemProductMapping` do `105D` định nghĩa và do lớp price-resolution
tiêu thụ, không tạo cạnh ngược `105C → 105D`. Đồ thị acyclic. Không có
ordering bất khả thi: mọi blocker còn lại là input từ Owner (catalog
contract, confirmed-report registry, Public Purchase dataset thật), không
phải deadlock giữa các task. `TASK-105B` có thể đạt DONE độc lập với
`TASK-105D` (DONE blocker của nó là dataset thật + HB triggers), điều này
nhất quán giữa PROGRESS và `TASK-108B` §100. Ownership gap duy nhất — lớp
composition `P01–P10` chưa có task ID/gate/budget — được `DEC-154` §11 công
bố tường minh kèm yêu cầu scope lock riêng trước implementation, nên là gap
đã khai báo chứ không phải ẩn (xem HB-154-01/03 về nội dung bảng).

**5. Không authorize implementation quá sớm — ĐẠT.**
`TASK-105D` Ready verdict = `BLOCKED`, Completion Gate 32 check DRAFT/
NOT_TESTED/chưa freeze. `TASK-105C` = `BLOCKED / NOT AUTHORIZED`,
`SCOPE_LOCK = REOPENED_BY_DEC-154`, `COMPLETION_GATE =
CHANGE_PROPOSAL_OPEN`. `TASK-105B`: `FilePriceProvider` NOT ACTIVATED,
`PendingPriceProvider` vẫn default. `P01–P10` chưa có implementation owner.
Bảng 20 check `CHECK-105C-01..20` được giữ làm historical artifact và ghi rõ
"không được dùng một mình để mở implementation".

**6. Product Identity tách biệt Purchase Price — ĐẠT.** `DEC-154` §6;
`TASK-105D` "Mapping lưu identity, **không lưu fixed purchase price**";
`CHECK-105D-15`; `P10`; `CHECK-105D-16` (price-provider boundary). Phần
"Ngoài Phạm Vi" của `TASK-105D` loại trừ tường minh purchase-price
calculation/precedence.

**7. `TASK-105D` Completion Gate — 32/32 phủ đủ yêu cầu review.** Đã đối
chiếu từng mục bắt buộc: DISTINCT-before-mapping (G03); confirmed alias →
0 thao tác (G04/G10/G24); deterministic unique match (G05); fuzzy-only không
auto-authorize (G07); Pending (G13/G27); rejected-candidate memory (G12);
correction audit (G18); raw accounting data bất biến (G14); mapping không
chứa fixed price (G15); hai namespace (G29/G30); Public Purchase direct
identity (G26/G28); no fake Tracking product (G28); same code khác namespace
(G30); `CrossSystemProductMapping` (G31/G32); duplicate-import idempotency
(G19); concurrency/conflicting confirmation (G20); keyboard-first/batch UX
(G22/G23); một confirmation áp mọi record (G11); Tracking không bị mutate
(G17). Không thiếu mục nào. Không có duplicate thật (chỉ chồng lấn — xem
Observations). Không có mâu thuẫn. Untestable-as-written: xem HB-154-05.
Phân bổ evidence E1/E2 phù hợp `EVIDENCE_STANDARD` cho Effective Risk HIGH.

**8. Hardening trigger audit — ĐẠT.** `HB-105B-03` (invalid shape/root/rows →
canonical load error), `HB-105B-05` (strict required-column, `effective_to`
typo không thành open record), `HB-105B-06` (test/network boundary khi
`TASK-105C` mở `tools/pricing`), `HB-105B-10` (strict schema cho dataset
machine-generated) — cả bốn có classification HARDENING, trigger cụ thể,
`triggered now = NO` đúng (phiên chỉ sửa documentation, không đọc file thật,
không thêm test/tools), và required action trước real usage. `DEC-154` có
làm **hẹp/cụ thể hoá** trigger — `HB-105B-10` nay gắn với Public Purchase
export/snapshot, `HB-105B-03/05` gắn với Public Purchase dataset thật thay vì
`phist` snapshot — nhưng không nới lỏng điều kiện nào và không xoá finding
nào. `HB-105B-07/08` RESOLVED + independently verified (không mở lại);
`09`/`11` SUPERSEDED; `04` OUT_OF_SCOPE — nhất quán giữa `DEC-154` §16,
PROGRESS và handoff. Không Repair Cycle nào được mở.

**9. An toàn để mở phiên `TASK-105D` readiness/data-contract — CÓ**, với điều
kiện HB-154-02 được đưa vào chương trình nghị sự của chính phiên đó.

## Kết Luận (Conclusion)

```text
PASS WITH HARDENING — ELIGIBLE_FOR_NEXT_READINESS
```

E2 PASS. BLOCKING = 0. HARDENING = 7. OUT_OF_SCOPE = 1.

Reconciliation tại `442404d1` là additive và đúng thẩm quyền: nó sửa
current-state architecture mà không rewrite lịch sử, không chạm production,
không tiêu repair budget, và không cấp implementation authority cho bất kỳ
task nào. Bảy finding HARDENING đều là công việc đặc tả phải hoàn tất **trước
khi** freeze gate hoặc trước khi mở implementation, không phải khiếm khuyết
chặn phiên readiness kế tiếp.

## Việc Cần Theo Dõi Tiếp (Required Follow-up)

Đưa vào phiên `TASK-105D` readiness/data-contract + persistence/audit design:
- HB-154-02 (bắt buộc — quyết định unified vs. hai dataset, và ràng buộc
  catalog version ↔ price version cho replay);
- HB-154-05 (định nghĩa đo được cho các UX/ambiguity gate trước freeze).

Đưa vào phiên mở scope lock cho price-resolution composition `P01–P10`:
- HB-154-01 (bổ sung điều kiện `CrossSystemProductMapping` vào `P03`);
- HB-154-03 (bổ sung rule bypass pre-cutover).

Đưa vào phiên refreeze Scope/Completion Gate của `TASK-105C`:
- HB-154-04 (câu hỏi lineage review budget — quyết định thuộc Owner).

Vệ sinh tài liệu, phiên có authority kế tiếp chạm đúng file:
- HB-154-06, HB-154-07.

Reviewer read-only không thực hiện bất kỳ mục nào ở trên trong phiên này.
