# TASK-105D — Product Identity Resolver

## Metadata

Status:
DONE

Ready Transition:
`PLANNED → READY` ngày 2026-08-28, bởi phiên Freeze Finalization retry
`S038` (`docs/reviews/TASK-105D-FREEZE-FINALIZATION-REVIEW-2.md`), sau khi
blocker cuối cùng của Ready Gate — Completion Gate freeze — được đóng.
`READY` **không phải** `IMPLEMENTED` và **không phải** `DONE`: nó chỉ có nghĩa
Ready Gate hết blocker. Implementation vẫn cần một phiên cấp phép riêng, và
`DEC-157` §2 còn ràng buộc: **không** mở implementation trước khi Owner quyết
định divergence review point (`V4.1` §8).

Specification State:
COMPLETE — semantics Owner đã chốt tại `DEC-154`; data contract/persistence/
audit design đã chốt tại `DEC-155` +
`docs/spec/TASK-105D-DATA-CONTRACT.md` (S034). Completion Gate đã qua
GATE REVISION #1 (S037/`DEC-157`, xử lý F-01…F-05 của Freeze Finalization
attempt #1) và nay **ĐÃ FROZEN** bởi Freeze Finalization retry `S038`
(2026-08-28, `V4.1` §12). Implementation vẫn CHƯA được cấp phép.

Canonical Data Contract:
`docs/spec/TASK-105D-DATA-CONTRACT.md` — hợp đồng dữ liệu, persistence,
concurrency, audit, migration và định nghĩa vận hành của các Completion Gate
UX/ambiguity. Đọc file đó TRƯỚC khi mở implementation; các invariant `INV-xx`
trong đó là quy phạm.

Phase:
PHASE-01 — Product identity + price-resolution foundation

Task Mode:
MAJOR

Primary Agent Tier:
C

Escalation Tier:
C

Difficulty:
4/5

Risk:
4/5

Blast Radius:
5/5

Effective Risk:
HIGH — `max(Local Risk 4, Blast Radius 5)`, theo đường lỗi
`sai identity → sai nguồn giá → sai KpiPurchasePrice → sai KPI/lương`.
Golden hiện chỉ phủ `PendingPriceProvider`, nên không hạ bậc theo V4.1 §4.1.

Project Profile:
PRODUCT

Review Budget lineage:
`TASK-105D` — root lineage mới, `2 allowed / 0 used / 2 remaining`.

Authority:
`DEC-154` — PRODUCT IDENTITY & PURCHASE PRICE RESOLUTION (Owner Decision).
`DEC-155` — TASK-105D READINESS DATA CONTRACT (readiness design authority).
`DEC-156` — OWNER RATIFICATION (Owner Decision, 2026-08-28): `OR-01`
APPROVED; `OR-02` APPROVED WITH CANDIDATE-ONLY POLICY (`ALIAS_AID_UNIQUE`
**không** có production auto-resolution authority — chỉ candidate #1);
`OR-03` APPROVED FOR PHASE 1. Không còn mục nào chờ Owner ratification.
`DEC-157` — COMPLETION GATE REVISION #1 + BRANCH DIVERGENCE (Owner Decision,
2026-08-28): giữ **đúng 32 gate** (không mở rộng gate set); nạp F-03/F-04/F-05
vào gate hiện có; `V4.1` §8 Option C — CONTINUE WITH EXPLICIT JUSTIFICATION.

## Mục Tiêu (Objective)

Giải quyết danh tính sản phẩm cho từng **identity khác biệt** của dữ liệu bán
hàng, không lặp thao tác theo từng dòng, rồi trả một identity canonical có
namespace rõ ràng:

```text
(namespace, source_product_code)

namespace ∈ {TRACKING, PUBLIC_PURCHASE}
```

Resolver phải giảm thao tác theo thời gian bằng bộ nhớ mapping bền vững,
nhưng không trao authority production cho fuzzy similarity hay mô hình AI.
Không giải quyết chắc chắn được thì trả `PENDING_PRODUCT`; không invent mã.

## Cutover Contract

```text
CUTOVER_DATE = 2026-09-01
```

### Trước cutover

Với `sale_date < CUTOVER_DATE`, nếu report lịch sử đã được Owner xác nhận
chứa cả product identity và purchase price, report đó là authority:

```text
mapping_source = HISTORICAL_CONFIRMED_REPORT
price_source   = HISTORICAL_CONFIRMED_REPORT
```

Luồng này bypass resolver/catalog/price-provider. Không remap hồi tố và
không dựng lại từ Tracking/Public Purchase nếu chưa có correction authority
tường minh. Bản ghi đến muộn vẫn phân loại bằng `sale_date`, không dùng
`import_date`. Nếu report lịch sử không có confirmation đủ căn cứ, kết quả là
Pending/correction workflow; không tự đưa qua catalog hiện tại để backfill.

### Từ cutover

Với `sale_date >= CUTOVER_DATE`, resolver dùng contract trong task này và
hai namespace hợp lệ. Một sản phẩm không cần tồn tại trong Tracking để hợp lệ
cho Reports.

## Canonical Product Identity

```text
ResolvedProductIdentity:
  namespace           : TRACKING | PUBLIC_PURCHASE
  source_product_code : mã ổn định trong chính namespace đó
```

`TRACKING:ABC` và `PUBLIC_PURCHASE:ABC` là hai identity khác nhau, không
collision. Raw accounting product name là dữ liệu nguồn bất biến; tên đã
normalize/model token chỉ là matching aid, không phải canonical ID.

## Resolution Order và Kết Quả

```text
Reports identity
  → persistent alias memory
  → Tracking catalog
  → Public Purchase catalog
  → candidate ranking / confirmation
```

- Alias đã confirm (khớp `raw_identity_key`, tức `ALIAS_EXACT`): reuse ngay,
  0 thao tác lặp.
- Biến thể chỉ khác ở hoa/thường/khoảng trắng (`ALIAS_AID_UNIQUE`):
  **candidate #1, KHÔNG auto-resolve** — `DEC-156`/`OR-02`. Đúng 1
  `confirmation_action` lần đầu; từ lần sau là 0 vì đã thành `ALIAS_EXACT`.
- Deterministic unique match trong ĐÚNG MỘT namespace (`CATALOG_EXACT_UNIQUE`):
  auto-resolve, `count(confirmation_action) == 0` — assertion quy phạm ở
  `CHECK-105D-05`. Khớp exact ở CẢ HAI namespace (`CROSS_NAMESPACE_TIE`,
  `INV-29`): **KHÔNG** auto-resolve.
- Tracking MISS nhưng Public Purchase deterministic unique match: resolve
  `PUBLIC_PURCHASE:<code>`; đây là kết quả hợp lệ, không tạo Tracking giả.
- Không nguồn nào resolve chắc chắn: `PENDING_PRODUCT`.
- Fuzzy similarity chỉ được xếp hạng candidate; tự nó không được auto-confirm.

## DISTINCT-before-mapping

Resolver lập tập identity khác biệt trước khi hiển thị/confirm. Một lần
confirmation áp cho mọi dòng/order chia sẻ cùng source identity. Identity
nguồn phải bao gồm đủ source-system context và raw product identity để không
gộp nhầm hai model chính xác khác nhau. Duplicate import không tạo lại
mapping hay audit event đã tồn tại.

## Normalization và Conservative Model Extraction

- Unicode NFC, trim, collapse whitespace và casefold được phép dùng làm aid.
- Không bỏ dấu/punctuation/model number nếu việc đó làm hai model khác nhau
  trở thành một identity.
- Model extraction chỉ sinh token/evidence để tìm candidate. Không phải
  authority mapping.
- Exact model differences phải còn phân biệt được trong candidate set và
  persistent alias key.

## Persistent Alias Memory

Conceptual entity `ProductAliasMapping` tối thiểu chứa:

```text
alias_id
source_system
raw_product_identity
normalized_matching_aid
namespace
source_product_code
mapping_status
mapping_source
evidence
version
confirmed_by / confirmed_at
created_at / updated_at
```

Mapping lưu identity, **không lưu fixed purchase price**. Confirmation phải
persist, reuse được, có provenance và version. Raw accounting name không bị
rewrite.

## Rejected Candidate Memory

Conceptual entity `RejectedProductCandidate` lưu ít nhất alias identity,
candidate `(namespace, source_product_code)`, evidence fingerprint, actor,
timestamp và reason. Candidate đã reject không được lặp lại chỉ vì chạy lại
cùng evidence; chỉ được đề xuất lại khi có evidence mới và ghi rõ lý do.

## Cross-system Product Mapping

Conceptual entity `CrossSystemProductMapping`:

```text
TRACKING:<tracking_code> ↔ PUBLIC_PURCHASE:<public_purchase_code>
```

Hai code không được giả định bằng nhau. Mapping phải explicit, persistent,
reusable, auditable, correctable và versioned. Confirmation đã có được reuse
mà không hỏi lại. Mapping này hỗ trợ nhánh giá Public Purchase fallback cho
identity TRACKING; nó không đổi identity của sản phẩm thành PUBLIC_PURCHASE.

**Điều kiện tiên quyết của fallback (S034 / `DEC-155` — giải HB-154-01).**
Với một identity `TRACKING`, giá Public Purchase chỉ được tra khi CẢ BA điều
kiện đúng: (a) không có valid vendor candidate tại `sale_date`; (b) tồn tại
một `CrossSystemProductMapping` `CONFIRMED` đang active cho đúng
`tracking_code` đó; (c) mã dùng để tra là `public_purchase_code` **của chính
mapping đó**. Thiếu (b) → **Pending**, tuyệt đối không đoán mã Public
Purchase. Uniqueness: tại một thời điểm mỗi `tracking_code` và mỗi
`public_purchase_code` có tối đa một mapping `CONFIRMED` (1:1); vi phạm →
trạng thái `CONFLICT` tường minh, cấm silent last-write-wins. Nguyên văn quy
phạm: `docs/spec/TASK-105D-DATA-CONTRACT.md` §8.4 (`INV-38`…`INV-45`).

## Human Confirmation và Batch UX Contract

- Batch/keyboard-first là luồng chính.
- Candidate #1 đúng: tối đa 1 `confirmation_action` (định nghĩa quy phạm ở
  phần Completion Gate → "Định nghĩa vận hành bắt buộc"; assertion ở
  `CHECK-105D-23`).
- Known mapping: 0 `confirmation_action` (`CHECK-105D-04`, `CHECK-105D-24`).
- Một confirmation áp cho toàn bộ affected rows/orders cùng identity.
- Pending là lựa chọn hợp lệ, không phải lỗi UI.
- Confirmation/correction là hành động audit được; UI phải hiển thị namespace,
  code, model evidence và số dòng/order bị tác động trước khi xác nhận.

## Correction Audit và Concurrency

Correction không overwrite lịch sử. `MappingAuditEvent` phải giữ old/new
identity, actor, timestamp, reason, affected scope và version. Update dùng
optimistic concurrency/compare-and-swap hoặc cơ chế tương đương. Hai
confirmation xung đột trên cùng alias/version phải báo conflict và yêu cầu
reconcile; cấm silent last-write-wins.

## Idempotency

- Import trùng dựa trên source row identity/hash không tạo thêm mapping,
  candidate-rejection hoặc audit event tương đương.
- Re-submit cùng confirmation với cùng idempotency key trả cùng kết quả.
- Retry sau lỗi không được áp mapping hai lần hoặc tăng affected count giả.

## Provenance Contract

Mỗi resolved result giữ ít nhất:

```text
raw_product_identity
namespace
source_product_code
mapping_source
mapping_id / mapping_version (nếu có)
resolution_method
resolved_at
```

`PENDING_PRODUCT` giữ reason/evidence đã thử; không invent identity rỗng.

## Price-provider Boundary

Task này chỉ resolve identity. Không tính purchase price. Output của nó là
input cho price resolution theo `DEC-154` P00–P11 (`P00`/`P03`/`P11` đã được
sửa transcription tại S034 để khớp `DEC-154` §2/§7 — xem
`docs/spec/TASK-105D-DATA-CONTRACT.md` §16.2; lớp composition đó **chưa có
implementation owner**, đề xuất task riêng ở §16.3):

- TRACKING identity đi vào TASK-105C trước, rồi có thể fallback qua
  `CrossSystemProductMapping` sang TASK-105B.
- PUBLIC_PURCHASE identity bypass TASK-105C và đi thẳng TASK-105B.
- Identity TRACKING không đổi chỉ vì price source fallback.

## Operational Metrics

- `AUTO_RESOLUTION_RATE`
- `MANUAL_CONFIRMATION_RATE`
- `PENDING_RATE`
- `REUSE_RATE`
- `WRONG_MAPPING_CORRECTION_RATE`
- `MANUAL_CONFIRMATION_ACTIONS_PER_100_ORDERS` (đổi tên từ
  `MANUAL_ACTIONS_PER_100_ORDERS` tại `DEC-155`; cùng một metric, tên chính
  xác hơn vì `confirmation_action` cố ý không đếm thao tác điều hướng)

Metric phải có denominator/version rõ ràng và không log dữ liệu khách hàng
không cần thiết. Denominator/numerator quy phạm của cả sáu metric:
`docs/spec/TASK-105D-DATA-CONTRACT.md` §15 (mẫu số chung `D` = số DISTINCT
identity trong batch sau khi loại nhánh pre-cutover; `INV-83`:
`AUTO + MANUAL + PENDING = 1`; `INV-85`: metric không bao giờ là input của
một quyết định resolution).

## Phạm Vi (Scope)

- Cutover + historical bypass contract.
- Hai namespace và identity tuple.
- DISTINCT-before-mapping.
- Alias/rejection/cross-system mapping persistence contracts.
- Normalization, conservative extraction, deterministic match, candidate
  ranking, confirmation và Pending.
- Correction audit, idempotency, concurrency conflict handling.
- Batch/keyboard-first UX contract và metrics.
- Contract biên với TASK-105B/TASK-105C/price resolution.

## Ngoài Phạm Vi (Out of Scope)

- Autonomous AI authority hoặc fuzzy-only production authority.
- Product-family/successor-model analytics.
- Mutation của Tracking catalog hay tạo Tracking product giả.
- Historical catalog reconstruction/retroactive remapping không có authority.
- `TASK-105C` implementation.
- Purchase-price calculation/precedence implementation.
- Kích hoạt `FilePriceProvider` hoặc thay `PendingPriceProvider`.

## Phụ Thuộc (Dependencies)

- `DEC-154` — DONE ở mức decision recording.
- Catalog contract/snapshot có version của Tracking và Public Purchase —
  **contract đã được cung cấp canonical tại S034**
  (`docs/spec/TASK-105D-DATA-CONTRACT.md` §3/§4). **Dữ liệu thật** (version
  Public Purchase đầu tiên, capture Tracking đầu tiên) vẫn chưa có.
- Registry/report lịch sử Owner-confirmed cho pre-cutover bypass — chưa được
  cung cấp làm dữ liệu production.
- Persistent storage + audit mechanism đủ cho alias/correction/concurrency —
  **đã chọn tại S034** (`docs/spec/TASK-105D-DATA-CONTRACT.md` §11:
  `ProductIdentityStore` Protocol + append-only JSONL event log ở Phase 1;
  §10.3 optimistic concurrency; §13 audit append-only).
- **Auth** — Phase 1 chưa có authentication (`ADR-101`). Actor là **khai báo
  của người vận hành**, không phải danh tính đã xác thực (`OR-03` —
  **APPROVED FOR PHASE 1** tại `DEC-156` §3; không còn chờ ratification). Đây
  là một hạn chế thật, không được mô tả là "authenticated". Gate bảo vệ:
  `CHECK-105D-20` (actor REQUIRED, cấm default im lặng) và `CHECK-105D-21`
  (nội dung audit + cấm từ "authenticated").
- Permission model ADMIN hiện hành (`DEC-124`) phải được nối vào confirmation
  và correction khi implementation.

## Chặn (Blocks)

- Post-cutover price resolution production.
- `TASK-108B` trên dữ liệu thật không-Pending.
- Activation của TASK-105B/TASK-105C trong production composition.

## An Toàn Để Chạy Song Song Với (Parallel-Safe With)

- Hoàn thiện data contract/snapshot của Public Purchase.
- Audit read-only schema/candidate inventories.
- Không parallel-safe với một implementation khác cùng ghi alias/cross-system
  mapping schema.

## Phạm Vi Tác Động Dự Kiến (Expected Touch Area)

Allowed khi có implementation authority riêng:
- module product identity/resolver mới;
- repository/persistence migration cho mapping + audit;
- batch mapping UI;
- tests/fixtures tổng hợp;
- wiring explicit sau cutover.

Không được đụng vào nếu chưa có Scope Expansion:
- Tracking repo/catalog;
- production price data;
- TASK-105C/provider code;
- `FilePriceProvider` frozen code;
- default provider trong `app/pipeline.py`;
- Golden fixture/expected.

## Ready Gate

Cập nhật 2026-08-28 (S034, `DEC-155`). Bốn mục đầu không đổi; ba mục
readiness được đóng bằng `docs/spec/TASK-105D-DATA-CONTRACT.md`; hai blocker
còn lại được nêu chính xác.

- [x] Objective/scope/out-of-scope đã xác định.
- [x] Business semantics/cutover/namespaces đã được Owner chốt (`DEC-154`).
- [x] Difficulty/Risk/Blast Radius/agent tier đã xác định.
- [x] Completion Gate dự thảo đầy đủ.
- [x] Catalog contracts/snapshots và historical-confirmed registry có data
      contract canonical — `docs/spec/TASK-105D-DATA-CONTRACT.md` §3 (unified
      `PublicPurchaseSourceVersion`, hai projection, `INV-04`…`INV-10`), §4
      (`TrackingCatalogSnapshot` read-only, `INV-11`…`INV-16`), §9
      (`HistoricalConfirmedRegistry`, `INV-46`…`INV-54`).
- [x] Persistence/migration/rollback/concurrency mechanism được chọn — §11
      (`ProductIdentityStore` Protocol; Phase 1 = append-only JSONL event log
      + index dẫn xuất, kèm bảng so sánh phương án và hạn chế đã ghi rõ), §10.3
      (optimistic concurrency, `INV-58`…`INV-61`), §14 (migration/rollback
      không phá huỷ).
- [x] Permission + audit contract ở tầng domain đã xác định — §12 (bảy
      permission, năm mức authority), §13 (`MappingAuditEvent` append-only).
- [x] **Owner ratification — ĐÃ ĐÓNG** (`DEC-156`, 2026-08-28). `OR-01`
      APPROVED (Public Purchase = MỘT canonical versioned source, hai
      projection, published version immutable). `OR-02` APPROVED WITH
      CANDIDATE-ONLY POLICY (`ALIAS_AID_UNIQUE` chỉ là candidate #1; đúng 1
      `confirmation_action` lần đầu, 0 từ lần sau qua `ALIAS_EXACT`).
      `OR-03` APPROVED FOR PHASE 1 (actor khai báo, REQUIRED, cấm gọi là
      authenticated, cấm default im lặng; authentication thật là future
      hardening/capability boundary, KHÔNG phải blocker Phase 1).
- [x] **Completion Gate freeze — ĐÃ ĐÓNG** (2026-08-28, `S038`). Freeze
      Finalization attempt #1 (`S036`) = `FAIL` với 5 BLOCKING; GATE REVISION #1
      (`S037`/`DEC-157`) áp dụng đầy đủ F-01…F-05 + `G04`/`G05`/`G22` + overlap
      clarification, giữ đúng 32 gate; **Freeze Finalization retry (`S038`) =
      `PASS WITH HARDENING`** — re-review độc lập toàn bộ 32 gate trên
      `be835b1`, 0 BLOCKING, 32/32 testable, 32/32 deterministic, 20/20
      adversarial PASS → Completion Gate `FROZEN`
      (`GATE_SET_SHA256 = 0444e58c…`). Bằng chứng:
      `docs/reviews/TASK-105D-FREEZE-FINALIZATION-REVIEW-2.md`; proposal:
      `docs/reviews/TASK-105D-COMPLETION-GATE-CHANGE-PROPOSAL.md`.

Không phải blocker của Ready Gate nhưng là **dependency dữ liệu của
implementation** (ghi ở đây để không bị đọc nhầm thành đã có): bảng mapping
Owner-confirmed cho bootstrap (nếu có), báo cáo lịch sử Owner-confirmed cho
registry, `PublicPurchaseSourceVersion` thật đầu tiên, và capture Tracking
đầu tiên. Không có chúng thì implementation vẫn chạy được với store rỗng —
kết quả đúng là Pending, không phải lỗi (§14.3).

**Ready verdict:** `READY` (2026-08-28, `S038`).
Số blocker: 4 (trước S034) → 2 (sau S034) → 1 (sau `DEC-156`/S035) → **0**
(sau freeze `S038`).

Ràng buộc kèm theo, vẫn hiệu lực:

```text
READY ≠ IMPLEMENTED ≠ DONE.
READY chỉ có nghĩa Ready Gate hết blocker.
Implementation cần một phiên cấp phép RIÊNG.
DEC-157 §2: KHÔNG mở implementation trước khi Owner quyết định divergence
            review point (V4.1 §8) — xem §14 của
            docs/reviews/TASK-105D-FREEZE-FINALIZATION-REVIEW-2.md.
```

## Completion Gate (FROZEN — 2026-08-28, S038)

> **Lịch sử freeze.**
>
> **Attempt #1 (S036, 2026-08-28) = FAIL.** Một phiên Freeze Finalization có
> thẩm quyền (`V4.1` §12) đã review độc lập toàn bộ 32 gate trên SHA
> `9cd8714` và **từ chối freeze**: 5 BLOCKING, 5 HARDENING. Ma trận khi đó:
> testable 30/32, deterministic 29/32; `G06` và `G23` mâu thuẫn nhau; 5 trong
> 20 case đối kháng bắt buộc không được gate nào phủ. Bằng chứng đầy đủ:
> `docs/reviews/TASK-105D-FREEZE-FINALIZATION-REVIEW.md`.
>
> ```text
> F-01  DEC-156/OR-02 chưa truyền hết vào khối "Định nghĩa vận hành bắt buộc"
>       — khối đó vẫn liệt kê ALIAS_AID_UNIQUE TRONG tập auto-resolve và vẫn
>       nói "Ba nguồn", trái INV-28/INV-28b và data contract §17.2.
> F-02  CHECK-105D-05 là phát biểu cho phép ("có thể auto-resolve"), không
>       phải assertion — không có PASS/FAIL condition.
> F-03  OR-03 (actor REQUIRED, cấm gọi là authenticated — INV-72/INV-73)
>       không có gate nào bảo vệ.
> F-04  OR-01 (unified Public Purchase source — INV-04…INV-10) và
>       ResolutionBinding/replay (INV-55…INV-57) không có gate nào bảo vệ.
> F-05  Catalog drift (INV-13/INV-14/INV-16) không có gate nào bảo vệ.
> ```
>
> **GATE REVISION #1 (S037, 2026-08-28) — ĐÃ ÁP DỤNG.** Một phiên gate
> revision có thẩm quyền đã xử lý F-01…F-05 và toàn bộ finding ma trận
> (`G04`, `G05`, `G22` chưa deterministic/testable), theo **Owner Decision
> `DEC-157`**: giữ **ĐÚNG 32 gate**, nạp F-03/F-04/F-05 vào gate hiện có,
> không mở rộng gate set. Proposal canonical (before/after từng gate, lý do,
> invariant bị tác động):
> `docs/reviews/TASK-105D-COMPLETION-GATE-CHANGE-PROPOSAL.md`.
>
> ```text
> Gate count           : 32  (KHÔNG ĐỔI)
> Completion Gate      : CHANGE PROPOSAL APPLIED — vẫn NOT FROZEN
> TASK-105D            : PLANNED / READY GATE BLOCKED  (KHÔNG chuyển READY)
> Repair Cycle         : KHÔNG mở (budget 2 allowed / 0 used / 2 remaining)
> production/test code : KHÔNG đổi một dòng nào
> ```
>
> Phiên S037 **không** freeze. `V4.1` §12 tách thẩm quyền `FROZEN` khỏi phiên
> viết gate: một phiên **Freeze Finalization retry** phải re-review **TOÀN BỘ**
> gate set đã sửa (không chỉ phần diff) rồi mới được ghi `FROZEN`.

> **FREEZE FINALIZATION RETRY (attempt #2, S038, 2026-08-28) = PASS WITH
> HARDENING. Completion Gate ĐÃ FROZEN.** Một phiên Freeze Finalization độc
> lập (`V4.1` §12) đã re-review **toàn bộ** 32 gate trên SHA `be835b1` — không
> kế thừa kết luận của `S037`, dựng lại ma trận từ văn bản gate — và ghi
> `FROZEN`. Bằng chứng đầy đủ:
> `docs/reviews/TASK-105D-FREEZE-FINALIZATION-REVIEW-2.md`.
>
> ```text
> Verdict            : PASS WITH HARDENING — TASK-105D READY
> BLOCKING           : 0        (F-01…F-05 đóng, xác minh độc lập)
> HARDENING          : 4        (HB-105D-F2-01/02/03 mới + H-05 kế thừa)
> OUT_OF_SCOPE       : 3        (O-01/O-02/O-03 kế thừa)
> Testable           : 32 / 32
> Deterministic      : 32 / 32
> Contradiction      : 0
> Adversarial A–T    : 20 / 20 PASS
> Gate count         : 32       (KHÔNG ĐỔI)
> Repair Cycle       : KHÔNG mở (2 allowed / 0 used / 2 remaining)
> production/test    : KHÔNG đổi một dòng nào
> ```
>
> **Freeze evidence — khối gate dưới đây là bản đã FROZEN.**
>
> ```text
> exact source SHA  : be835b1b1b03d4e8d21656c3624b6e4bc964b7a1
> gate count        : 32   (CHECK-105D-01 … CHECK-105D-32), 32/32 REQUIRED
> Evidence Level    : E2 = 19, E1 = 13
> GATE_SET_SHA256   : 0444e58c02b04804a116c140af722ffc29ea64adf468aa6c93794c4408a5c877
> TASK_FILE_SHA256  : a6be1ac71ac751eeefae30cf076f90e5d4cad80067c9441f78578e9972e028b1
> reviewer          : S038 — Independent Freeze Finalization retry
> timestamp         : 2026-08-28
> evidence level    : E2
> prior attempt     : #1 — S036, base 9cd8714, FAIL (5 BLOCKING)
> lineage           : S036 findings → S037/DEC-157 gate revision #1 → S038 freeze
> ```
>
> `Status = NOT_TESTED` trên cả 32 check là ĐÚNG sau freeze: freeze đóng băng
> **ngữ nghĩa** của gate, không tuyên bố gate đã được chạy. Việc chuyển
> `NOT_TESTED → PASS` thuộc phiên implementation.
>
> **Thay đổi gate sau thời điểm này** — bất kỳ sửa đổi nào làm đổi
> `GATE_SET_SHA256` — cần một `COMPLETION GATE CHANGE PROPOSAL` mới + authority
> theo `governance/core/TASK_COMPLETION_GATE_STANDARD.md`. Không sửa tại chỗ.

Toàn bộ 32 check là `REQUIRED`, `Status = NOT_TESTED`. Effective Risk `HIGH`
yêu cầu `E1` cho mọi check thực thi được và `E2` cho check thuộc diện
data/cutover/concurrency/audit/Golden critical.

### Định nghĩa vận hành bắt buộc

*(S034 / `DEC-155` — giải HB-154-05. **SỬA S037 / `DEC-157` theo `DEC-156`/
`OR-02` — giải F-01.**)*

Trước khi đọc gate, bốn khái niệm dưới đây là **quy phạm**. Chúng thay các
phát biểu định tính mà independent review chỉ ra là chưa test được. Nguồn đầy
đủ: `docs/spec/TASK-105D-DATA-CONTRACT.md` §6.6 và §17.

```text
confirmation_action
    = MỘT command ở tầng domain, do người dùng phát ra, làm đổi trạng thái
      persistent của mapping store cho MỘT distinct identity.
    Đếm đúng bốn loại: CONFIRM_MAPPING | REJECT_CANDIDATE |
      CONFIRM_CROSS_SYSTEM | SET_PENDING.
    KHÔNG đếm: điều hướng, cuộn, focus, mở/đóng panel, xem evidence, tìm
      kiếm, lọc, sắp xếp, phím tắt điều hướng.
    Đếm command chứ không đếm phím/click: cùng một hành động nghiệp vụ phải
      cho cùng một kết quả gate dù dùng bàn phím hay chuột, dù đổi thư viện
      UI. Yêu cầu keyboard-first vẫn giữ nguyên, ở CHECK-105D-22.

tập auto-resolve (TẬP ĐÓNG — ĐÚNG HAI PHƯƠNG THỨC)
    ALIAS_EXACT
    CATALOG_EXACT_UNIQUE
    Thêm một phương thức vào tập này = quyết định Owner, không phải quyết
      định implementation (INV-28, sửa theo DEC-156).

AMBIGUOUS
    = resolution_method KHÔNG thuộc tập auto-resolve đóng ngay trên
      (ALIAS_EXACT, CATALOG_EXACT_UNIQUE — data contract §6.6, INV-28 đã sửa
      theo DEC-156/OR-02).
    BỐN nguồn ambiguity, mỗi nguồn một fixture bắt buộc:
      (a) MULTIPLE_EXACT
      (b) CROSS_NAMESPACE_TIE
      (c) ONLY_SIMILARITY
      (d) ALIAS_AID_UNIQUE   — candidate-only theo DEC-156/OR-02; INV-28b:
                               KHÔNG BAO GIỜ tự sinh một mapping CONFIRMED.

normal action / interaction
    = đồng nghĩa `confirmation_action`. Cả hai cụm "thao tác bình thường" và
      "interaction" KHÔNG còn được dùng trong gate mà không quy chiếu định
      nghĩa này (giải H-03). Gate chỉ dùng đúng thuật ngữ
      `confirmation_action`.
```

**Sửa gì so với bản trước S037 (F-01).** Bản trước liệt kê `ALIAS_AID_UNIQUE`
**bên trong** tập auto-resolve và nói "Ba nguồn ambiguity" — cả hai là trạng
thái **trước** ratification `DEC-156`. Hệ quả cụ thể: `ALIAS_AID_UNIQUE`
không phải AMBIGUOUS ⇒ `G06` không ràng buộc nó ⇒ một implementation
auto-resolve `ALIAS_AID_UNIQUE` vẫn PASS `G06` trong khi `G23` FAIL. Hai gate
cho hai kết luận trái ngược trên cùng một hành vi. Khối trên đã đóng mâu
thuẫn đó bằng đúng ngữ nghĩa canonical của `DEC-156` §2 / `INV-28` / `INV-28b`
/ data contract §6.6 và §17.2.

### Cách đọc phần gate

- Mỗi gate là một khối `#### CHECK-105D-NN (GNN)`. Khối đó là **quy phạm**:
  `Khẳng định`, `Fixture bắt buộc`, `PASS khi`, `FAIL khi`, `Nguồn quy phạm`.
- Bảng chỉ mục ngay dưới đây chỉ để **điều hướng**. Nó cố ý không lặp lại
  `Status`/`Evidence Level` để không tạo hai nguồn sự thật (`V4.1` §11 —
  ARTIFACT INTERNAL PRECEDENCE).
- Khi khối gate và văn xuôi ở phần trên của file bất đồng: **khối gate
  thắng**, và divergence phải được báo cáo, không tự dàn xếp.
- `count(confirmation_action)` luôn hiểu theo định nghĩa quy phạm ở trên.

### Chỉ mục 32 gate

| ID | Tiêu đề |
|---|---|
| CHECK-105D-01 (G01) | Pre-cutover bypass resolver/catalog/price-provider |
| CHECK-105D-02 (G02) | Post-cutover outcome đúng union type đóng |
| CHECK-105D-03 (G03) | DISTINCT-before-mapping |
| CHECK-105D-04 (G04) | Alias đã confirm: read path 0 confirmation_action, 0 ghi |
| CHECK-105D-05 (G05) | `CATALOG_EXACT_UNIQUE` auto-resolve — assertion hai chiều |
| CHECK-105D-06 (G06) | AMBIGUOUS không bao giờ auto-resolve — bốn fixture |
| CHECK-105D-07 (G07) | Fuzzy/similarity không có production authority |
| CHECK-105D-08 (G08) | Candidate ranking ổn định, có evidence đầy đủ |
| CHECK-105D-09 (G09) | Confirmation persist + toàn vẹn store |
| CHECK-105D-10 (G10) | Reuse qua run mới + ngữ nghĩa catalog drift |
| CHECK-105D-11 (G11) | Một confirmation resolve mọi affected rows/orders |
| CHECK-105D-12 (G12) | Rejected candidate: nhớ theo fingerprint, không suy diễn |
| CHECK-105D-13 (G13) | `PENDING_PRODUCT` là biến thể riêng về kiểu |
| CHECK-105D-14 (G14) | Raw accounting name bất biến |
| CHECK-105D-15 (G15) | Mapping schema không chứa purchase price |
| CHECK-105D-16 (G16) | Price-provider boundary được giữ |
| CHECK-105D-17 (G17) | Tracking không bị mutate |
| CHECK-105D-18 (G18) | Correction audit giữ lịch sử, không viết lại report đã ghim |
| CHECK-105D-19 (G19) | Idempotency: duplicate import 0 side effect |
| CHECK-105D-20 (G20) | Command precondition: version conflict + actor REQUIRED |
| CHECK-105D-21 (G21) | Provenance + actor semantics + ResolutionBinding/replay |
| CHECK-105D-22 (G22) | Keyboard-first trên bề mặt Phase 1 đã xác định |
| CHECK-105D-23 (G23) | AMBIGUOUS candidate #1 đúng: đúng 1 confirmation_action |
| CHECK-105D-24 (G24) | Known mapping trong batch N≥2: 0 action, revision không đổi |
| CHECK-105D-25 (G25) | Golden Business Baseline không đổi |
| CHECK-105D-26 (G26) | Tracking MISS + PP unique match → PUBLIC_PURCHASE |
| CHECK-105D-27 (G27) | Tracking MISS không tự động thành Pending |
| CHECK-105D-28 (G28) | PUBLIC_PURCHASE identity + unified versioned source |
| CHECK-105D-29 (G29) | Namespace persist cùng mapping, IMMUTABLE |
| CHECK-105D-30 (G30) | Cùng code khác namespace không collision |
| CHECK-105D-31 (G31) | Cross-system mapping explicit + lookup không đoán mã |
| CHECK-105D-32 (G32) | Cross-system mapping đã confirm reuse không hỏi lại |

### Gate G01–G08 — Định tuyến, ambiguity và candidate

#### CHECK-105D-01 (G01) — Pre-cutover bypass resolver/catalog/price-provider

Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E2

Khẳng định:

```text
Với sale_date < CUTOVER_DATE (2026-09-01):
  entry = registry.lookup(order_id, raw_identity_key, sale_date)
  entry tồn tại và status == CONFIRMED
      → outcome == HISTORICAL_CONFIRMED(identity?, price,
                                        provenance = HISTORICAL_CONFIRMED_REPORT)
  ngược lại
      → outcome == PENDING_PRODUCT(reason_code = PENDING_HISTORICAL_CONFIRMATION)
Trong CẢ HAI nhánh: resolver, catalog snapshot và price provider KHÔNG được gọi
  lần nào — spy/fake đếm số lời gọi == 0 (INV-47).
Phân loại bằng sale_date, KHÔNG BAO GIỜ bằng import_date (INV-48).
confirmed_identity vắng KHÔNG kích hoạt resolver để "điền vào chỗ trống" (INV-50).
Registry KHÔNG bắt buộc khớp catalog hiện tại (INV-49).
```

Fixture bắt buộc:

1. `sale_date = 2026-08-20`, registry có entry `CONFIRMED` → `HISTORICAL_CONFIRMED`, spy == 0.
2. `sale_date = 2026-08-20`, registry rỗng → `PENDING_HISTORICAL_CONFIRMATION`, spy == 0.
3. Late arrival: `import_date = 2027-01-15`, `sale_date = 2026-08-20` → vẫn nhánh lịch sử.
4. Entry `CONFIRMED` **không có** `confirmed_identity` → vẫn `HISTORICAL_CONFIRMED`, spy == 0.
5. Entry mang mã không còn tồn tại trong catalog hiện tại → vẫn hợp lệ.

PASS khi:
Cả 5 fixture cho đúng outcome và cả 5 đều có `spy_call_count == 0` trên
resolver, catalog snapshot và price provider.

FAIL khi:
Bất kỳ lời gọi nào tới resolver/catalog/price-provider trên nhánh pre-cutover;
phân loại bằng `import_date`; registry rỗng bị coi là lỗi thay vì Pending;
backfill identity/giá lịch sử bằng catalog hoặc giá hiện tại.

Nguồn quy phạm:
`INV-46`…`INV-50`, `INV-54`; data contract §9, §14.3; `DEC-154` §1/§2.

Evidence:
Chưa thực thi — implementation chưa được cấp phép.

Executed By:
Chưa thực thi.

Timestamp:
Chưa thực thi.

#### CHECK-105D-02 (G02) — Post-cutover outcome đúng union type đóng

Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E1

Khẳng định:

```text
Với sale_date >= CUTOVER_DATE:
  outcome ∈ { RESOLVED, REQUIRES_CONFIRMATION, PENDING_PRODUCT }
  RESOLVED mang ĐỦ (namespace ∈ {TRACKING, PUBLIC_PURCHASE},
                    source_product_code non-empty)
  HISTORICAL_CONFIRMED KHÔNG BAO GIỜ xuất hiện ở nhánh post-cutover.
ResolutionOutcome là union type ĐÓNG — không biến thể thứ năm, không string
  rỗng, không None thay cho một biến thể.
namespace là enum đóng; thêm giá trị = quyết định Owner + task riêng (INV-17).
```

Fixture bắt buộc:
Một fixture cho mỗi biến thể hợp lệ (`RESOLVED`, `REQUIRES_CONFIRMATION`,
`PENDING_PRODUCT`) + một assertion kiểu (exhaustive match/type check) chứng
minh không tồn tại nhánh trả về ngoài union.

PASS khi:
Ba fixture đúng biến thể; assertion kiểu chứng minh union đóng; `RESOLVED`
luôn đủ hai trường của tuple.

FAIL khi:
Một đường trả về `None`/`""`/dict tự do; `RESOLVED` thiếu `namespace` hoặc
`source_product_code`; `HISTORICAL_CONFIRMED` rò sang nhánh post-cutover.

Nguồn quy phạm:
Data contract §5 (`ResolutionOutcome`, `INV-17`, `INV-24`, `INV-25`).

Evidence:
Chưa thực thi — implementation chưa được cấp phép.

Executed By:
Chưa thực thi.

Timestamp:
Chưa thực thi.

#### CHECK-105D-03 (G03) — DISTINCT-before-mapping

Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E1

Khẳng định:

```text
Tập DISTINCT D được lập theo (source_system, raw_identity_key) TRƯỚC khi
  hiển thị hay yêu cầu bất kỳ confirmation nào.
Batch 10.000 row chứa 50 distinct identity  ⇒  |D| == 50
count(confirmation_action) <= |D|   — trần theo DISTINCT identity, KHÔNG theo
  số row và KHÔNG theo số order.
D loại bỏ nhánh pre-cutover trước khi tính (INV-46, §15).
```

Fixture bắt buộc:
Batch 10.000 row / 50 distinct identity, có ít nhất một identity xuất hiện ở
nhiều order khác nhau.

PASS khi:
`|D| == 50`; tổng `confirmation_action` của cả batch `<= 50`; không có đường
nào phát sinh action theo từng row.

FAIL khi:
Số lần hỏi người dùng tỉ lệ với số row/order; tập DISTINCT được tính sau khi
đã hỏi; identity gộp nhầm hai model khác nhau vào một phần tử của `D`.

Nguồn quy phạm:
`INV-30`, `INV-87`; data contract §17.1, §15.

Evidence:
Chưa thực thi — implementation chưa được cấp phép.

Executed By:
Chưa thực thi.

Timestamp:
Chưa thực thi.

#### CHECK-105D-04 (G04) — Alias đã confirm: read path 0 confirmation_action, 0 ghi

Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E1

Khẳng định:

```text
Store có một mapping CONFIRMED cho raw_identity_key K.
Một lời gọi resolve MỘT identity K (read path):
  count(confirmation_action cho K) == 0
  resolution_method == ALIAS_EXACT
  0 MappingAuditEvent mới, 0 mapping record mới, 0 lệnh ghi vào store.
Thuật ngữ: gate này KHÔNG dùng từ "interaction" nữa (giải H-03) — chỉ dùng
  confirmation_action theo định nghĩa quy phạm ở đầu phần gate.
```

Ranh giới với `CHECK-105D-24`:
`G04` kiểm **read path của MỘT lời gọi resolve** — bất biến "resolve một alias
đã confirm là một thao tác chỉ-đọc". `G24` kiểm **mức batch**: `N >= 2` dòng
cùng identity và `current_revision()` không đổi sau cả batch. Hai gate bảo vệ
hai bất biến khác nhau (đọc-không-ghi vs. batch-không-tăng-revision); không
gate nào thay được gate kia.

Fixture bắt buộc:
Store seed một mapping `CONFIRMED` cho `K`; resolve đúng một identity `K`;
so sánh `current_revision()` trước/sau và đếm event mới.

PASS khi:
`count(confirmation_action) == 0`, `resolution_method == ALIAS_EXACT`, số
event mới == 0.

FAIL khi:
Resolve một alias đã confirm phát sinh bất kỳ ghi nào (kể cả "touch"
`updated_at`), hoặc phát sinh một `confirmation_action`.

Nguồn quy phạm:
`INV-30`, `INV-33`, `INV-70`; data contract §6.6, §17.1, §17.4.

Evidence:
Chưa thực thi — implementation chưa được cấp phép.

Executed By:
Chưa thực thi.

Timestamp:
Chưa thực thi.

#### CHECK-105D-05 (G05) — `CATALOG_EXACT_UNIQUE` auto-resolve — assertion hai chiều

Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E2

Khẳng định:

```text
Chiều DƯƠNG — phải auto-resolve:
  Setup : catalog có ĐÚNG MỘT entry khớp exact (theo raw_identity_key hoặc
          normalized_matching_aid) với raw identity, và chỉ trong MỘT namespace.
  Assert: count(confirmation_action) == 0
          resolution_method == CATALOG_EXACT_UNIQUE
          outcome == RESOLVED(namespace, source_product_code)
          mapping_source == DETERMINISTIC_CATALOG_MATCH

Chiều ÂM — cấm auto-resolve (INV-29):
  Setup : khớp exact ở CẢ HAI namespace.
  Assert: resolution_method == CROSS_NAMESPACE_TIE
          KHÔNG auto-resolve; outcome ∈ {REQUIRES_CONFIRMATION, PENDING_PRODUCT}
```

Sửa gì so với bản trước S037 (F-02):
Bản trước phát biểu "Deterministic unique match **có thể** auto-resolve" — một
mệnh đề cho phép, không loại trừ điều gì. Một implementation bắt xác nhận mọi
thứ PASS; một implementation auto-resolve cũng PASS. Gate không thể FAIL ⇒
không deterministic. Bản này FAIL được ở **cả hai chiều**.

Fixture bắt buộc:
(1) exact unique trong `TRACKING`; (2) exact unique trong `PUBLIC_PURCHASE`;
(3) fixture âm `INV-29`: exact ở cả hai namespace.

PASS khi:
Hai fixture dương cho `count == 0` + đúng `resolution_method`; fixture âm cho
`CROSS_NAMESPACE_TIE` và **không** auto-resolve.

FAIL khi:
Một `CATALOG_EXACT_UNIQUE` bị bắt xác nhận (`count > 0`); **hoặc** một
`CROSS_NAMESPACE_TIE` bị auto-resolve.

Nguồn quy phạm:
Data contract §1, §6.5, §6.6 (tập auto-resolve đóng), `INV-29`.

Evidence:
Chưa thực thi — implementation chưa được cấp phép.

Executed By:
Chưa thực thi.

Timestamp:
Chưa thực thi.

#### CHECK-105D-06 (G06) — AMBIGUOUS không bao giờ auto-resolve — bốn fixture

Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E2

Khẳng định:

```text
Một identity AMBIGUOUS (định nghĩa quy phạm ở đầu phần gate: resolution_method
KHÔNG thuộc tập auto-resolve ĐÚNG HAI phương thức ALIAS_EXACT,
CATALOG_EXACT_UNIQUE):
  outcome ∈ {REQUIRES_CONFIRMATION, PENDING_PRODUCT}
  resolution_method ∉ {ALIAS_EXACT, CATALOG_EXACT_UNIQUE}
  KHÔNG có "im lặng chọn cái gần nhất".

Case trung tâm: catalog chứa hai entry chỉ khác nhau ở ĐÚNG MỘT model token và
raw identity mang token THỨ BA.

Kèm INV-27: hai identity khác nhau ở đúng một model token PHẢI cho hai
raw_identity_key khác nhau VÀ hai normalized_matching_aid khác nhau.
```

Fixture bắt buộc:

**BỐN** fixture (sửa từ "Ba" theo F-01 / `DEC-156`/`OR-02`):

1. `MULTIPLE_EXACT` — nhiều hơn một entry catalog khớp exact trong một namespace.
2. `CROSS_NAMESPACE_TIE` — khớp exact ở cả hai namespace (`INV-29`).
3. `ONLY_SIMILARITY` — chỉ có evidence similarity/model-token (`INV-01`).
4. `ALIAS_AID_UNIQUE` — khớp aid duy nhất với một alias đã confirm
   (`DEC-156`/`OR-02`, `INV-28b`). Assertion chi tiết của case này nằm ở
   `CHECK-105D-23`; `G06` chỉ yêu cầu nó **không** được auto-resolve, cố ý
   không nhân đôi phần đếm action.

PASS khi:
Cả bốn fixture cho outcome thuộc tập cho phép và `resolution_method` nằm ngoài
tập auto-resolve; fixture `INV-27` cho hai khoá khác nhau.

FAIL khi:
Bất kỳ fixture nào trong bốn sinh ra một mapping `CONFIRMED` mà không có
`confirmation_action`; hoặc `ALIAS_AID_UNIQUE` được xử lý như auto-resolve.

Nguồn quy phạm:
`INV-27`, `INV-28`, `INV-28b`, `INV-29`, `INV-01`; data contract §6.6, §17.2;
`DEC-156` §2.

Evidence:
Chưa thực thi — implementation chưa được cấp phép.

Executed By:
Chưa thực thi.

Timestamp:
Chưa thực thi.

#### CHECK-105D-07 (G07) — Fuzzy/similarity không có production authority

Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E2

Khẳng định:

```text
SIMILARITY_RANKED ∉ tập auto-resolve.
Một identity chỉ có evidence similarity/model-token:
  KHÔNG sinh mapping CONFIRMED nào
  outcome ∈ {REQUIRES_CONFIRMATION,
             PENDING_PRODUCT(reason_code = ONLY_SIMILARITY_EVIDENCE)}
Không đường nào trong hệ thống — resolver, bootstrap (§14), migration, import
  hàng loạt, script vận hành — biến một kết quả similarity thành mapping
  CONFIRMED mà không có confirmation_action.
Không mô hình AI/fuzzy nào được trao production authority.
```

Ranh giới với `CHECK-105D-06(c)`:
`G06(c)` kiểm **outcome của một identity** `ONLY_SIMILARITY`. `G07` kiểm
**bất biến authority của toàn hệ thống**: không tồn tại đường ghi nào biến
similarity thành `CONFIRMED`, kể cả ngoài luồng resolve. Hai gate bảo vệ hai
mức khác nhau (hành vi một case vs. phủ định toàn cục).

Fixture bắt buộc:
(1) identity chỉ có similarity evidence qua luồng resolve; (2) thử nạp
bootstrap/migration một mapping có `resolution_method = SIMILARITY_RANKED` →
bị từ chối.

PASS khi:
Cả hai fixture không sinh mapping `CONFIRMED`; `mapping_source` không bao giờ
là `DETERMINISTIC_CATALOG_MATCH` cho một khớp similarity.

FAIL khi:
Tồn tại bất kỳ đường nào tạo mapping `CONFIRMED` từ evidence similarity mà
không có `confirmation_action`.

Nguồn quy phạm:
`INV-01`, `INV-28`; data contract §6.5, §6.6, §14.

Evidence:
Chưa thực thi — implementation chưa được cấp phép.

Executed By:
Chưa thực thi.

Timestamp:
Chưa thực thi.

#### CHECK-105D-08 (G08) — Candidate ranking ổn định, có evidence đầy đủ

Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E1

Khẳng định:

```text
Cùng input (cùng pp_version_id, tracking_capture_id, catalog và
mapping_store_revision) → CÙNG thứ tự candidate, mọi lần chạy, mọi máy
(deterministic read — INV-64).
Mỗi candidate mang evidence §6.7 đầy đủ:
  matched_on        REQUIRED, thuộc enum đóng §6.7
  matched_value     REQUIRED, nguyên văn giá trị đã khớp
  candidate_set_ids REQUIRED, danh sách candidate đã hiển thị lúc quyết định
Không candidate nào được hiển thị mà thiếu evidence.
```

Fixture bắt buộc:
Chạy cùng một batch hai lần trong hai process khác nhau, so sánh thứ tự
candidate theo từng identity; một fixture kiểm mọi candidate đều có ba trường
evidence REQUIRED.

PASS khi:
Thứ tự candidate giống hệt giữa hai lần chạy; 0 candidate thiếu evidence.

FAIL khi:
Thứ tự phụ thuộc thứ tự dict/hash seed/thời gian; một candidate hiển thị mà
không có `matched_on`/`matched_value`/`candidate_set_ids`.

Nguồn quy phạm:
Data contract §6.7, `INV-64`.

Hạn chế đã ghi (HARDENING `H-05`, **KHÔNG** đóng trong phiên S037):
`ranking_method_id` là `OPTIONAL` ở §6.7 nhưng lại là một input được hash vào
`evidence_fingerprint` (§7.3). Nếu vắng, chiều "thuật toán xếp hạng đã đổi"
của `INV-35` im lặng biến mất. Sửa việc này là một thay đổi **data contract**
(OPTIONAL → REQUIRED, hoặc quy định giá trị sentinel), nằm ngoài thẩm quyền
của một phiên gate revision. Re-trigger: phiên implementation
`RejectedCandidate`/candidate ranking, hoặc một phiên sửa data contract có
thẩm quyền — tuỳ phiên nào đến trước.

Evidence:
Chưa thực thi — implementation chưa được cấp phép.

Executed By:
Chưa thực thi.

Timestamp:
Chưa thực thi.

### Gate G09–G16 — Persistence, drift, kiểu dữ liệu và ranh giới giá

#### CHECK-105D-09 (G09) — Confirmation persist + toàn vẹn store

Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E1

Khẳng định:

```text
Confirmation được ghi bền vững: append event + fsync; index dẫn xuất ghi theo
  write-temp + os.replace (INV-62). Một lần ghi bị ngắt KHÔNG để lại state
  đọc được nhưng sai.
Đọc lại sau khi restart process → cùng mapping, cùng version (INV-63/INV-64).
Index mất/hỏng → dựng lại được từ log; log và index bất đồng → LOG THẮNG.
Lookup "mapping hiện hành" trả ĐÚNG bản ghi CONFIRMED duy nhất theo INV-30.
  Tìm thấy NHIỀU HƠN MỘT CONFIRMED cho cùng (source_system, raw_identity_key)
  → LỖI TOÀN VẸN STORE tường minh; TUYỆT ĐỐI KHÔNG tự chọn một cái
  [INV-33 — nạp từ HARDENING H-04].
Không đường ghi nào bỏ qua domain contract (INV-66); không thao tác DELETE
  trong bất kỳ interface nào (INV-67).
```

Fixture bắt buộc:
(1) confirm → restart → đọc lại; (2) xoá index → dựng lại từ log → kết quả
giống hệt; (3) store bị chèn hai bản ghi `CONFIRMED` cho cùng khoá → lookup
raise lỗi toàn vẹn, không trả một trong hai.

PASS khi:
Ba fixture đúng; không interface nào expose thao tác xoá.

FAIL khi:
Lookup tự chọn một trong nhiều `CONFIRMED`; index được coi là nguồn sự thật;
tồn tại một đường ghi thẳng vào file store.

Nguồn quy phạm:
`INV-30`, `INV-33`, `INV-62`…`INV-64`, `INV-66`, `INV-67`; data contract §11.

Evidence:
Chưa thực thi — implementation chưa được cấp phép.

Executed By:
Chưa thực thi.

Timestamp:
Chưa thực thi.

#### CHECK-105D-10 (G10) — Reuse qua run mới + ngữ nghĩa catalog drift

Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E2

Khẳng định:

```text
PHẦN A — reuse qua import/run mới (nguyên trạng):
  Mapping đã persist được reuse ở một import/run MỚI:
    resolution_method == ALIAS_EXACT
    count(confirmation_action) == 0

PHẦN B — ngữ nghĩa catalog drift (NẠP F-05):
  B1 (INV-13) Capture Tracking mới: tracking_code GIỮ NGUYÊN, name/alt ĐỔI
      → mapping đã confirm VẪN hợp lệ; resolve qua ALIAS_EXACT;
        count(confirmation_action) == 0; status KHÔNG chuyển STALE.
        Tên hiển thị KHÔNG phải identity (INV-21).
  B2 (INV-14a/b) Sản phẩm biến mất khỏi board hiện tại
      (present_in_board == false, hoặc vắng khỏi capture mới):
      (a) mapping lịch sử đã confirm KHÔNG bị vô hiệu hoá, KHÔNG bị xoá,
          KHÔNG tự chuyển PENDING;
      (b) một report đã ghim tracking_capture_id CŨ replay ra kết quả
          GIỐNG HỆT.
  B3 (INV-14c) Một identity MỚI gặp lần đầu chỉ khớp một mã đã biến mất
      → status = STALE và reason_code = MAPPING_STALE_TARGET_ABSENT;
        cần confirmation; KHÔNG auto-resolve.
  B4 (INV-16) Mã bị gộp qua alias.map của Tracking
      → resolver KHÔNG tự chuyển mapping đã confirm sang mã chính;
        sinh event MARK_STALE và đề xuất mã chính làm candidate #1.
  B5 (INV-12) capture_status == FAILED → LỖI CỨNG; resolver TỪ CHỐI chạy trên
        snapshot đó. KHÔNG được đọc thành "sản phẩm không tồn tại",
        KHÔNG được biến thành Pending.
  B6 (INV-15) Catalog HIỆN TẠI KHÔNG BAO GIỜ viết lại identity LỊCH SỬ.
        Cấm retroactive remap; chỉ correction có authority tường minh (§13)
        mới đổi được một mapping đã confirm.
Không nhánh nào ở Phần B ghi vào Tracking (bất biến đó thuộc CHECK-105D-17).
```

Fixture bắt buộc:
Sáu fixture, mỗi fixture cho `B1`…`B6`, cộng một fixture cho Phần A. Mỗi
fixture dựng hai `TrackingCatalogSnapshot` (capture cũ + capture mới) và một
mapping `CONFIRMED` đã tồn tại từ capture cũ.

PASS khi:
Cả bảy fixture đúng; `B2(b)` chứng minh replay bằng cách so sánh output đầy đủ
của report ghim capture cũ trước và sau khi nạp capture mới.

FAIL khi:
Một capture mới thiếu mã làm mapping đã confirm mất hiệu lực hoặc rơi về
Pending; `capture_status = FAILED` bị đọc thành "không tồn tại"; alias.map tự
động di chuyển mapping đã confirm; đổi tên sản phẩm làm mất mapping.

Nguồn quy phạm:
`INV-12`…`INV-16`, `INV-21`, `INV-30`, `INV-70`; data contract §4.5, §6.4,
§13.2 (`MARK_STALE`), §5 (`MAPPING_STALE_TARGET_ABSENT`); `DEC-147` §3 R4;
`DEC-154` §2.

Evidence:
Chưa thực thi — implementation chưa được cấp phép.

Executed By:
Chưa thực thi.

Timestamp:
Chưa thực thi.

#### CHECK-105D-11 (G11) — Một confirmation resolve mọi affected rows/orders

Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E1

Khẳng định:

```text
Một confirmation_action áp cho MỌI dòng và MỌI order chia sẻ cùng distinct
identity (source_system, raw_identity_key) — INV-87.
Sau đúng một action, toàn bộ các dòng đó có outcome RESOLVED với cùng
(namespace, source_product_code); không dòng nào còn chờ.
affected_scope ghi trong audit event khớp đúng tập dòng/order thực tế.
```

Ranh giới với `CHECK-105D-03`:
`G03` kiểm **trần trên** số action theo `|D|` (không hỏi theo row). `G11` kiểm
**hiệu lực lan toả** của một action đã phát ra. Hai chiều khác nhau của cùng
nguyên tắc DISTINCT.

Fixture bắt buộc:
Một identity xuất hiện ở `M >= 3` order và `N >= 5` dòng; phát đúng một
`CONFIRM_MAPPING`.

PASS khi:
Sau một action, `N` dòng đều `RESOLVED`; `affected_scope.affected_line_count
== N`; `affected_order_ids` đúng `M` phần tử.

FAIL khi:
Còn dòng chưa resolve sau action; `affected_scope` sai số lượng; cần thêm
action cho các dòng còn lại.

Nguồn quy phạm:
`INV-30`, `INV-76`, `INV-87`; data contract §13.3, §17.1.

Evidence:
Chưa thực thi — implementation chưa được cấp phép.

Executed By:
Chưa thực thi.

Timestamp:
Chưa thực thi.

#### CHECK-105D-12 (G12) — Rejected candidate: nhớ theo fingerprint, không suy diễn

Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E1

Khẳng định:

```text
Một candidate bị suppress KHI VÀ CHỈ KHI tồn tại một RejectedCandidate cùng
  (raw_identity_key, candidate_namespace, candidate_code) VÀ cùng
  evidence_fingerprint (INV-34).
Đổi pp_version_id | tracking_capture_id | candidate_set_ids | ranking_method_id
  → fingerprint đổi → candidate ĐƯỢC đề xuất lại, kèm chú thích "đã từ chối
  tại <version cũ>" (INV-35). Rejection KHÔNG BAO GIỜ chặn vĩnh viễn bằng
  chứng mới hợp lệ.
Từ chối A KHÔNG BAO GIỜ tự động trở thành một mapping tới B
  [INV-36 — nạp từ HARDENING H-04].
Từ chối TOÀN BỘ candidate của một identity → PENDING_PRODUCT với
  reason_code = CANDIDATE_REJECTED_AND_EVIDENCE_UNCHANGED; KHÔNG ép người dùng
  chọn một candidate sai để thoát màn hình (INV-37).
```

Fixture bắt buộc:
(1) reject rồi chạy lại cùng evidence → candidate bị suppress; (2) đổi
`pp_version_id` → candidate xuất hiện lại kèm chú thích; (3) identity có đúng
hai candidate, reject candidate #1 → **không** tự confirm #2; (4) reject cả
hai → `PENDING_PRODUCT` đúng `reason_code`.

PASS khi:
Cả bốn fixture đúng.

FAIL khi:
Reject một candidate làm hệ thống tự chọn candidate còn lại; rejection chặn cả
khi evidence đã đổi; toàn-bộ-bị-từ-chối không cho `PENDING_PRODUCT`.

Nguồn quy phạm:
`INV-34`…`INV-37`; data contract §7.

Evidence:
Chưa thực thi — implementation chưa được cấp phép.

Executed By:
Chưa thực thi.

Timestamp:
Chưa thực thi.

#### CHECK-105D-13 (G13) — `PENDING_PRODUCT` là biến thể riêng về kiểu

Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E1

Khẳng định:

```text
G13-a  ResolutionOutcome có một biến thể PENDING_PRODUCT RIÊNG BIỆT VỀ KIỂU,
       không phải None/""/0 (INV-25).
G13-b  PENDING_PRODUCT mang reason_code thuộc enum đóng §5 và attempted_sources
       KHÔNG rỗng khi resolver đã chạy.
G13-c  PENDING_PRODUCT KHÔNG mang namespace hay source_product_code (INV-24).
G13-d  Một identity PENDING KHÔNG chặn việc resolve các identity khác trong
       cùng batch; batch hoàn tất với một tập kết quả hỗn hợp.
```

Fixture bắt buộc:
Một batch chứa đồng thời một identity `RESOLVED`, một `REQUIRES_CONFIRMATION`
và một `PENDING_PRODUCT`; assertion kiểu cho `G13-a`/`G13-c`.

PASS khi:
Bốn assertion đúng; batch trả về đủ ba kết quả, không raise, không dừng sớm.

FAIL khi:
Pending biểu diễn bằng giá trị rỗng; `reason_code` ngoài enum; một Pending làm
hỏng cả batch.

Nguồn quy phạm:
`INV-24`, `INV-25`; data contract §5, §17.3.

Evidence:
Chưa thực thi — implementation chưa được cấp phép.

Executed By:
Chưa thực thi.

Timestamp:
Chưa thực thi.

#### CHECK-105D-14 (G14) — Raw accounting name bất biến

Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E2

Khẳng định:

```text
raw_product_identity (product_raw) được lưu NGUYÊN VĂN và KHÔNG BAO GIỜ bị
  ghi đè, ở mọi luồng: confirm, correction, supersede, bootstrap, migration,
  re-import (INV-22, ADR-102 lớp RAW bất biến).
normalized key (fold) và display name KHÔNG phải canonical identity
  (INV-20, INV-21) và không được ghi ngược vào product_raw.
```

Fixture bắt buộc:
Confirm → correction → re-import cùng identity; so sánh `product_raw` byte-wise
ở cả ba thời điểm, kể cả với chuỗi có dấu tiếng Việt và khoảng trắng bất thường.

PASS khi:
`product_raw` giống hệt byte-wise sau cả ba bước.

FAIL khi:
Bất kỳ luồng nào ghi đè, trim, casefold hay chuẩn hoá `product_raw` tại chỗ.

Nguồn quy phạm:
`INV-20`, `INV-21`, `INV-22`; data contract §5, §6.2, §6.3; `ADR-102`.

Evidence:
Chưa thực thi — implementation chưa được cấp phép.

Executed By:
Chưa thực thi.

Timestamp:
Chưa thực thi.

#### CHECK-105D-15 (G15) — Mapping schema không chứa purchase price

Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E2

Khẳng định:

```text
Schema E-F (ProductIdentityMapping) KHÔNG có field giá, KHÔNG có field tiền tệ,
  KHÔNG có field đơn vị giá (INV-23, DEC-154 §6).
Assertion structural: tập tên field của record persist ra store không giao với
  tập {price, purchase_price, cost, amount, currency, unit_price, ...} và
  không có field nào mang kiểu tiền tệ.
Áp cho cả bản ghi đã persist trong log, không chỉ cho dataclass trong bộ nhớ.
```

Fixture bắt buộc:
Đọc một event log thật sau khi confirm và kiểm tập khoá JSON của record.

PASS khi:
Không field giá/tiền tệ nào tồn tại ở cả dataclass lẫn bản ghi đã persist.

FAIL khi:
Một field giá được thêm "để tiện", kể cả nullable hay chỉ dùng cho cache.

Nguồn quy phạm:
`INV-23`; data contract §6.2; `DEC-154` §6.

Evidence:
Chưa thực thi — implementation chưa được cấp phép.

Executed By:
Chưa thực thi.

Timestamp:
Chưa thực thi.

#### CHECK-105D-16 (G16) — Price-provider boundary được giữ

Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E2

Khẳng định:

```text
TASK-105D KHÔNG tính và KHÔNG trả purchase price ở nhánh post-cutover.
  ResolutionOutcome post-cutover không mang giá dưới bất kỳ tên nào.
Module product identity KHÔNG import TASK-105C provider, KHÔNG import
  FilePriceProvider, KHÔNG gọi price provider.
Ngoại lệ DUY NHẤT là nhánh pre-cutover HISTORICAL_CONFIRMED, nơi giá đến TỪ
  registry lịch sử (§9) chứ không do resolver tính (INV-46).
P00–P11 composition thuộc TASK-105E — không implement ở đây (DEC-156 §5).
```

Fixture bắt buộc:
(1) assertion import-graph trên module product identity; (2) kiểm outcome
post-cutover không có trường giá; (3) fixture pre-cutover chứng minh giá đến
từ registry.

PASS khi:
Ba assertion đúng; import-graph sạch.

FAIL khi:
Module identity gọi bất kỳ price provider nào ở nhánh post-cutover; outcome
post-cutover mang giá.

Nguồn quy phạm:
`INV-03`, `INV-23`, `INV-46`; data contract §16.1; `DEC-154` §6; `DEC-156` §5.

Evidence:
Chưa thực thi — implementation chưa được cấp phép.

Executed By:
Chưa thực thi.

Timestamp:
Chưa thực thi.

### Gate G17–G24 — Audit, concurrency, actor, replay và UX contract

#### CHECK-105D-17 (G17) — Tracking không bị mutate

Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E2

Khẳng định:

```text
KHÔNG tồn tại đường ghi nào từ TASK-105D vào Tracking (RTDB hay bất kỳ bề mặt
  ghi nào khác). Snapshot là READ-ONLY (INV-11: không ghi đè một capture_id
  đã tồn tại).
app/modules/** KHÔNG chạm mạng và KHÔNG biết RTDB tồn tại; phần chạm mạng chỉ
  nằm ở tools/tracking/ và chỉ đọc (DEC-152 §6, ADR-101).
KHÔNG tạo Tracking product giả để làm cho một identity "hợp lệ" (giao với
  CHECK-105D-28 — G28 sở hữu chiều "PUBLIC_PURCHASE hợp lệ không cần Tracking";
  G17 sở hữu chiều "cấm ghi/cấm tạo giả").
```

Fixture bắt buộc:
(1) assertion import-graph/network-boundary trên `app/modules/**`; (2) thử ghi
đè một `capture_id` đã tồn tại → bị từ chối; (3) toàn bộ fixture của
`CHECK-105D-10` Phần B chạy với một Tracking fake ghi-nhận-mọi-lệnh-ghi và
xác nhận số lệnh ghi == 0.

PASS khi:
0 lệnh ghi vào Tracking trên mọi fixture; capture immutable; import-graph sạch.

FAIL khi:
Bất kỳ lệnh ghi nào tới Tracking; ghi đè capture; `app/modules/**` import thư
viện mạng.

Nguồn quy phạm:
`INV-11`; data contract §4.1, §4.5; `DEC-152` §6; `ADR-101`.

Evidence:
Chưa thực thi — implementation chưa được cấp phép.

Executed By:
Chưa thực thi.

Timestamp:
Chưa thực thi.

#### CHECK-105D-18 (G18) — Correction audit giữ lịch sử, không viết lại report đã ghim

Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E2

Khẳng định:

```text
Correction = mapping cũ chuyển SUPERSEDED (Ở LẠI VĨNH VIỄN) + mapping mới
  CONFIRMED + MỘT event CORRECT_* nối hai bản ghi. KHÔNG DELETE, KHÔNG UPDATE
  tại chỗ (INV-74, INV-32).
reason REQUIRED cho mọi CORRECT_* và cho REPIN_REPORT (§13.2 / D-13).
actor_id REQUIRED và non-empty trên event (§13.1) — assertion đầy đủ về actor
  nằm ở CHECK-105D-21 (nội dung) và CHECK-105D-20 (điều kiện tiên quyết của
  command).
Audit trả lời được CHỈ TỪ LOG: ai sửa, lúc nào, TỪ GÌ, SANG GÌ, lý do, phạm vi
  bị tác động (INV-75).
affected_scope = {distinct_identity_count, affected_order_ids,
  affected_line_count, computed_at_revision}, tính lại từ dữ liệu tại revision
  đó, KHÔNG cộng dồn qua retry (INV-76, INV-71).
Correction tác động resolution TƯƠNG LAI kể từ revision của nó; nó KHÔNG tự
  động viết lại một report đã ghim ResolutionBinding (INV-77).
Muốn một report đã phát hành phản ánh correction: phải có REPIN_REPORT tường
  minh, có quyền REPORT_REPIN, có reason, được audit. KHÔNG re-pin ngầm,
  KHÔNG "tự cập nhật khi mở lại" (INV-78).
```

Fixture bắt buộc:
(1) correction đầy đủ → kiểm cả hai bản ghi còn trong log + event `CORRECT_*`;
(2) `CORRECT_*` thiếu `reason` → bị từ chối; (3) report đã ghim binding, chạy
correction, replay report → kết quả KHÔNG đổi; (4) `REPIN_REPORT` tường minh →
report mới phản ánh correction, có audit event và reason.

PASS khi:
Bốn fixture đúng; không bản ghi nào bị xoá.

FAIL khi:
Correction xoá hoặc sửa tại chỗ bản ghi cũ; `reason` bị bỏ qua; một report đã
ghim tự đổi kết quả sau correction.

Nguồn quy phạm:
`INV-32`, `INV-71`, `INV-74`…`INV-78`; data contract §13; `ADR-102`; `DEC-121`.

Evidence:
Chưa thực thi — implementation chưa được cấp phép.

Executed By:
Chưa thực thi.

Timestamp:
Chưa thực thi.

#### CHECK-105D-19 (G19) — Idempotency: duplicate import 0 side effect

Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E2

Khẳng định:

```text
Import lại CÙNG một file sales:
  tập DISTINCT identity giống hệt;
  mọi identity đã CONFIRMED resolve qua ALIAS_EXACT;
  0 mapping mới, 0 rejection mới, 0 audit event mới;
  current_revision() KHÔNG đổi        (INV-70)
Lớp command: cùng client_request_id đã xử lý → trả lại KẾT QUẢ CŨ,
  outcome = ALREADY_APPLIED, không ghi event mới (INV-68).
Lớp state: command mà state kết quả BẰNG state hiện tại → no-op,
  outcome = NO_CHANGE, không event, không tăng version (INV-69).
Retry sau lỗi KHÔNG áp mapping hai lần và KHÔNG làm tăng affected_count giả
  (INV-71).
```

Fixture bắt buộc:
(1) import cùng file hai lần; (2) gửi lại cùng `client_request_id`; (3) gửi
command mới không đổi state; (4) mô phỏng lỗi giữa chừng rồi retry.

PASS khi:
Bốn fixture đúng; `current_revision()` bằng nhau trước/sau ở fixture (1).

FAIL khi:
Import trùng tạo event mới; retry nhân đôi mapping hoặc `affected_count`.

Nguồn quy phạm:
`INV-68`…`INV-71`; data contract §11.3.

Evidence:
Chưa thực thi — implementation chưa được cấp phép.

Executed By:
Chưa thực thi.

Timestamp:
Chưa thực thi.

#### CHECK-105D-20 (G20) — Command precondition: version conflict + actor REQUIRED

Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E2

Khẳng định:

```text
PHẦN A — optimistic concurrency (nguyên trạng):
  expected_version != version hiện tại của aggregate
      → từ chối với MappingVersionConflict(current_state)
      → KHÔNG ghi event, KHÔNG tăng version
  TUYỆT ĐỐI KHÔNG silent last-write-wins; không auto-merge; không "force
      write" ở Phase 1 (INV-58, INV-59, INV-60).
  Aggregate boundary đúng theo INV-61: (source_system, raw_identity_key) cho
      E-F; tracking_code cho E-I; entry_id cho E-J.

PHẦN B — actor là điều kiện tiên quyết của command (NẠP F-03):
  Mọi command làm đổi state — CONFIRM_MAPPING | REJECT_CANDIDATE |
      CONFIRM_CROSS_SYSTEM | SET_PENDING | CORRECT_* | BOOTSTRAP_MAPPING |
      MARK_STALE | REPIN_REPORT — THIẾU actor_id thì BỊ TỪ CHỐI:
        0 event được ghi, 0 mapping đổi, version KHÔNG tăng.
  KHÔNG có giá trị mặc định. CẤM "system", CẤM anonymous, CẤM suy ra từ biến
      môi trường / OS user / config / hằng số trong mã (INV-72).
  actor_id rỗng hoặc chỉ chứa khoảng trắng = THIẾU.
```

Fixture bắt buộc:
(1) hai confirmation đồng thời trên cùng alias/version → conflict tường minh,
store không đổi; (2) mỗi loại command đổi state, gửi thiếu `actor_id` → bị từ
chối, `current_revision()` không đổi; (3) gửi `actor_id = ""` và
`actor_id = "   "` → cùng bị từ chối.

PASS khi:
Mọi fixture cho đúng lỗi và `current_revision()` không đổi sau mỗi lần từ chối.

FAIL khi:
Silent last-write-wins; một command thiếu actor được chấp nhận; hệ thống tự
điền `"system"`/OS user/giá trị mặc định nào khác.

Nguồn quy phạm:
`INV-58`…`INV-61`, `INV-72`; data contract §10.3, §12.1, §13.2; `DEC-156` §3
(`OR-03`).

Evidence:
Chưa thực thi — implementation chưa được cấp phép.

Executed By:
Chưa thực thi.

Timestamp:
Chưa thực thi.

#### CHECK-105D-21 (G21) — Provenance + actor semantics + ResolutionBinding/replay

Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E2

Khẳng định:

```text
PHẦN A — provenance của mỗi resolved result (nguyên trạng):
  raw_product_identity, namespace, source_product_code, mapping_source,
  mapping_id / mapping_version (nếu có), resolution_method, resolved_at,
  pp_version_id, tracking_capture_id.
  PENDING_PRODUCT giữ reason_code + attempted_sources; KHÔNG invent identity
  rỗng (INV-24, INV-25).

PHẦN B — actor semantics (NẠP F-03):
  MappingAuditEvent.actor_id REQUIRED, non-empty, IMMUTABLE (§13.1).
  Mọi nơi hiển thị/ghi actor phải nêu rõ đây là KHAI BÁO CỦA NGƯỜI VẬN HÀNH.
  KHÔNG artifact, output, báo cáo, log hay bề mặt điều khiển nào do TASK-105D
      sinh ra được mô tả actor Phase 1 bằng "authenticated", "authenticated
      user", hay "danh tính đã xác thực" (INV-73).
      Assertion thực thi được: một test quét văn bản trên toàn bộ artifact/
      chuỗi hiển thị do task sinh ra, khẳng định 0 lần xuất hiện của các cụm
      đó gắn với actor; cộng một mục checklist trong Independent Review.
  Điều gate này KHÔNG khẳng định: rằng người thao tác thật sự là actor đã khai.
      Đó là CAPABILITY BOUNDARY của Phase 1 (§12.1) và phải được ghi đúng như
      vậy, không được che.

PHẦN C — ResolutionBinding / replay (NẠP F-04):
  ResolutionBinding ghim ĐỦ CẢ BỐN: pp_version_id, tracking_capture_id,
      mapping_store_revision, registry_revision. CẤM ghim từng phần (INV-55).
  Replay một report = đọc lại đúng bộ binding của nó → kết quả GIỐNG HỆT lần
      chạy đầu, BẤT KỂ store/catalog/giá đã đổi thế nào sau đó (INV-56).
  Thiếu BẤT KỲ thành phần binding nào → LỖI CỨNG. KHÔNG fallback "mới nhất",
      KHÔNG trả Pending (INV-57).
```

Fixture bắt buộc:
(1) mỗi biến thể outcome mang đủ trường provenance; (2) audit event thiếu
`actor_id` không tồn tại được trong log; (3) test quét văn bản cho `INV-73`;
(4) binding thiếu một trong bốn thành phần → lỗi cứng, không fallback; (5)
replay sau khi đã đổi store + catalog + giá → output giống hệt byte-wise.

PASS khi:
Năm fixture đúng; fixture (5) so khớp output đầy đủ, không chỉ một trường.

FAIL khi:
Binding ghim từng phần; thiếu binding rơi về "mới nhất" hoặc Pending; một
artifact mô tả actor Phase 1 là authenticated; provenance thiếu trường.

Nguồn quy phạm:
`INV-24`, `INV-25`, `INV-55`…`INV-57`, `INV-72`, `INV-73`; data contract
§10.1, §12.1, §13.1; `DEC-156` §3 (`OR-03`); `ADR-102`.

Evidence:
Chưa thực thi — implementation chưa được cấp phép.

Executed By:
Chưa thực thi.

Timestamp:
Chưa thực thi.

#### CHECK-105D-22 (G22) — Keyboard-first trên bề mặt Phase 1 đã xác định

Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E1

Khẳng định:

```text
BỀ MẶT ÁP DỤNG (điểm sửa của H-01 — bản trước không xác định bề mặt):
  Phase 1 theo ADR-101 là thư viện Python thuần chạy bằng CLI, KHÔNG có UI đồ
  hoạ. Gate này vì vậy assert trên bề mặt Phase 1 THẬT, không assert trên một
  UI chưa tồn tại.

(a) Cả BỐN confirmation_action command, cùng với xem candidate/evidence và
    duyệt hết một batch, thực thi được HOÀN TOÀN qua bề mặt CLI/API dòng lệnh,
    trong một môi trường KHÔNG có display và KHÔNG có thiết bị trỏ
    (test chạy headless).
(b) app/modules/product/** KHÔNG import thư viện GUI/web/pointer-event nào;
    KHÔNG domain operation nào của TASK-105D cần sự kiện chuột/chạm để hoàn tất.
(c) KHÔNG confirmation_action nào chỉ tiếp cận được qua một bề mặt điều khiển
    bằng con trỏ.

Gate này KHÔNG được đánh NOT_APPLICABLE và KHÔNG được để NOT_TESTED với lý do
"Phase 1 chưa có UI": (a)+(b)+(c) test được ngay trên bề mặt CLI của Phase 1.
Khi một UI batch xuất hiện ở Phase 2+, việc mở rộng gate là quyết định của
phiên sở hữu UI đó, KHÔNG phải của gate này.
```

Fixture bắt buộc:
(1) chạy trọn một batch mapping (bao gồm cả bốn loại command) trong test
headless; (2) assertion import-graph cho `(b)`; (3) liệt kê bề mặt gọi được
của mỗi `confirmation_action` và khẳng định không loại nào chỉ có đường
con trỏ.

PASS khi:
Ba fixture đúng trên bề mặt CLI Phase 1.

FAIL khi:
Một `confirmation_action` chỉ chạy được qua GUI; `app/modules/product/**`
import thư viện GUI; gate bị đánh `NOT_APPLICABLE` mà không có Owner decision
tường minh.

Nguồn quy phạm:
Data contract §17.1 (`D-14`); `ADR-101`; `TASK_COMPLETION_GATE_STANDARD`
(REQUIRED check `NOT_TESTED` chặn `DONE`).

Evidence:
Chưa thực thi — implementation chưa được cấp phép.

Executed By:
Chưa thực thi.

Timestamp:
Chưa thực thi.

#### CHECK-105D-23 (G23) — AMBIGUOUS candidate #1 đúng: đúng 1 confirmation_action

Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E1

Khẳng định:

```text
Setup : một identity AMBIGUOUS theo định nghĩa quy phạm (bốn nguồn), candidate
        xếp hạng 1 là đáp án đúng.
Act   : chấp nhận candidate #1.
Assert: count(confirmation_action) == 1
        một action đó resolve MỌI dòng cùng identity (INV-87)
        lần chạy kế tiếp trên CHÍNH identity đó: count == 0, qua ALIAS_EXACT

FIXTURE BẮT BUỘC BỔ SUNG (DEC-156 / OR-02) — ALIAS_AID_UNIQUE:
  Một raw identity chỉ khác một alias đã confirm ở hoa/thường hoặc khoảng trắng.
  Assert: KHÔNG auto-resolve (INV-28b)
          nó xuất hiện ĐÚNG ở candidate #1
          chấp nhận tốn ĐÚNG 1 confirmation_action
          mapping sinh ra có mapping_source = HUMAN_CONFIRMATION và
              evidence.parent_mapping_id trỏ về alias đã confirm sinh ra
              candidate (§6.5, §6.6)
          lần xuất hiện THỨ HAI của chính biến thể đó tốn 0 và đi qua
              ALIAS_EXACT
```

Ghi chú `<= 1` vs `== 1`: data contract nói `<= 1`; gate assert `== 1`. `== 1`
chặt hơn và không mâu thuẫn — một identity AMBIGUOUS theo định nghĩa cần ít
nhất một quyết định của người.

Fixture bắt buộc:
Bốn fixture theo bốn nguồn ambiguity (`MULTIPLE_EXACT`, `CROSS_NAMESPACE_TIE`,
`ONLY_SIMILARITY`, `ALIAS_AID_UNIQUE`), mỗi fixture chạy hai lần liên tiếp.

PASS khi:
Lần một `count == 1` cho cả bốn; lần hai `count == 0` và
`resolution_method == ALIAS_EXACT`.

FAIL khi:
`ALIAS_AID_UNIQUE` auto-resolve; cần nhiều hơn một action cho candidate #1
đúng; lần hai vẫn tốn action.

Nguồn quy phạm:
`INV-28`, `INV-28b`, `INV-87`; data contract §6.5, §6.6, §17.2, §17.4;
`DEC-156` §2.

Evidence:
Chưa thực thi — implementation chưa được cấp phép.

Executed By:
Chưa thực thi.

Timestamp:
Chưa thực thi.

#### CHECK-105D-24 (G24) — Known mapping trong batch N≥2: 0 action, revision không đổi

Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E1

Khẳng định:

```text
Setup : store có một mapping CONFIRMED cho raw_identity_key K.
Act   : resolve một batch chứa N dòng có identity K (N >= 2).
Assert: count(confirmation_action cho K) == 0
        resolution_method == ALIAS_EXACT
        current_revision() KHÔNG đổi trước/sau cả batch   (INV-70)
```

Ranh giới với `CHECK-105D-04` và `CHECK-105D-10`:
`G04` = read path của MỘT lời gọi (không ghi gì). `G24` = mức BATCH `N >= 2` +
revision không đổi. `G10` Phần A = reuse qua một **run/import MỚI** (tiến trình
khác, sau restart). Ba gate phủ ba mức khác nhau của cùng nguyên tắc reuse;
`G24` là mức duy nhất assert `current_revision()` trên một batch.

Fixture bắt buộc:
Batch có `N = 5` dòng identity `K` đã confirm, trộn với ít nhất một identity
chưa biết để chứng minh batch vẫn xử lý bình thường.

PASS khi:
`count == 0` cho `K`; `current_revision()` bằng nhau trước/sau; identity chưa
biết vẫn được xử lý đúng.

FAIL khi:
Batch làm tăng revision dù không có quyết định nào của người; `K` bị hỏi lại.

Nguồn quy phạm:
`INV-30`, `INV-70`, `INV-87`; data contract §17.4.

Evidence:
Chưa thực thi — implementation chưa được cấp phép.

Executed By:
Chưa thực thi.

Timestamp:
Chưa thực thi.

### Gate G25–G32 — Golden, hai namespace và cross-system mapping

#### CHECK-105D-25 (G25) — Golden Business Baseline không đổi

Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E2

Khẳng định:

```text
Golden Business Baseline (tests/test_golden_baseline.py) chạy trước và sau
  implementation TASK-105D cho KẾT QUẢ GIỐNG HỆT.
Không fixture Golden nào bị sửa; không expected value nào bị sửa để "đạt".
PendingPriceProvider vẫn là default; FilePriceProvider KHÔNG được activate bởi
  task này.
Baseline hiện hành đã công bố: 58 passed, 2 skipped.
```

Fixture bắt buộc:
Chạy Golden trên base SHA và trên SHA implementation; so sánh nguyên văn dòng
kết quả và diff của `tests/` phải rỗng ở phần Golden.

PASS khi:
Cùng số passed/skipped; `git diff` trên Golden fixture/expected rỗng.

FAIL khi:
Golden đổi kết quả; Golden fixture/expected bị sửa; default provider bị đổi.

Nguồn quy phạm:
`V4.1` §6 (phạm vi đúng của Golden Baseline); `CLAUDE.md`; `DEC-153`.

Evidence:
Chưa thực thi — implementation chưa được cấp phép.

Executed By:
Chưa thực thi.

Timestamp:
Chưa thực thi.

#### CHECK-105D-26 (G26) — Tracking MISS + PP unique match → PUBLIC_PURCHASE

Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E2

Khẳng định:

```text
Raw identity KHÔNG khớp entry nào trong Tracking catalog, NHƯNG khớp exact duy
  nhất một product trong Public Purchase identity projection:
    outcome == RESOLVED(namespace = PUBLIC_PURCHASE,
                        source_product_code = <PP product_code>)
    resolution_method == CATALOG_EXACT_UNIQUE
Đây là kết quả HỢP LỆ, không phải fallback hạng hai.
```

Ranh giới với `G27`/`G28`:
`G26` = chiều KHẲNG ĐỊNH (Tracking MISS + PP unique ⇒ resolve PP).
`G27` = chiều PHỦ ĐỊNH (Tracking MISS **không** tự động ⇒ Pending).
`G28` = chiều CẤU TRÚC (identity PP hợp lệ mà không cần Tracking giả, và PP
đến từ MỘT canonical versioned source). Ba gate bảo vệ ba mệnh đề khác nhau;
bỏ bất kỳ gate nào cũng để hở một đường lỗi riêng.

Fixture bắt buộc:
Tracking snapshot không chứa mã; PP version chứa đúng một match exact.

PASS khi:
Outcome đúng namespace/code/method.

FAIL khi:
Kết quả là Pending dù PP có match duy nhất; namespace bị gán `TRACKING`.

Nguồn quy phạm:
`DEC-154` §3; data contract §3, §6.6.

Evidence:
Chưa thực thi — implementation chưa được cấp phép.

Executed By:
Chưa thực thi.

Timestamp:
Chưa thực thi.

#### CHECK-105D-27 (G27) — Tracking MISS không tự động thành Pending

Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E1

Khẳng định:

```text
Một MISS ở Tracking KHÔNG được là điều kiện đủ để trả PENDING_PRODUCT.
Resolver PHẢI tiếp tục qua Public Purchase catalog trước khi kết luận Pending
  (Resolution Order: alias memory → Tracking catalog → Public Purchase catalog
   → candidate ranking / confirmation).
Chỉ khi KHÔNG nguồn nào resolve chắc chắn mới trả PENDING_PRODUCT, với
  reason_code phản ánh đúng nguyên nhân (NO_CANDIDATE_IN_ANY_CATALOG, ...).
attempted_sources của Pending PHẢI liệt kê cả hai catalog đã thử.
```

Fixture bắt buộc:
Tracking MISS + PP có match → không Pending (giao với `G26`); Tracking MISS +
PP MISS → Pending với `attempted_sources` chứa cả hai nguồn.

PASS khi:
Cả hai fixture đúng; `attempted_sources` đầy đủ.

FAIL khi:
Resolver dừng ở Tracking MISS; `attempted_sources` chỉ có Tracking.

Nguồn quy phạm:
`DEC-154` §3; data contract §5 (`reason_code`), §6.

Evidence:
Chưa thực thi — implementation chưa được cấp phép.

Executed By:
Chưa thực thi.

Timestamp:
Chưa thực thi.

#### CHECK-105D-28 (G28) — PUBLIC_PURCHASE identity + unified versioned source

Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E2

Khẳng định:

```text
PHẦN A — identity hợp lệ không cần Tracking (nguyên trạng):
  Một identity PUBLIC_PURCHASE:<code> là hợp lệ mà KHÔNG cần tạo hay giả một
  Tracking product. Không ghi gì vào Tracking (bất biến cấm-ghi thuộc G17).

PHẦN B — unified Public Purchase source (NẠP F-04 / OR-01):
  B1 (INV-06) MỌI price_rows[*].product_key PHẢI tồn tại trong identity_rows
      của CÙNG một PublicPurchaseSourceVersion. Vi phạm = LỖI LOAD tại thời
      điểm publish/load — KHÔNG phải lỗi lúc tính giá/KPI/lương, KHÔNG phải
      Pending.
  B2 (INV-02) Loader của identity projection là STRICT: thiếu khối, sai tên
      khối, khối rỗng, hoặc có khoá top-level lạ → LỖI LOAD, KHÔNG được đọc
      thành "danh mục rỗng".
  B3 (INV-03) Đường đi hợp lệ DUY NHẤT là một PublicPurchaseSourceLoader riêng
      validate cả hai projection rồi truyền khối prices đã validate vào
      FilePriceProvider qua constructor rows.
      Assertion: diff của implementation trên
      app/modules/pricing/file_price_provider.py == RỖNG (FROZEN, DEC-153).
  B4 (INV-04/INV-05/INV-09) product_code unique trong version; fold(product_code)
      unique trong version; alias không trùng product_code của một sản phẩm
      KHÁC trong cùng version (sau fold). Mỗi vi phạm = lỗi load.
  B5 (INV-07) Published version IMMUTABLE: đổi product_name/aliases KHÔNG đổi
      kết quả của một report đã ghim version đó.
  B6 (OR-01) MỘT canonical versioned source, HAI projection của CÙNG một
      PublicPurchaseSourceVersion / source-version lineage.
      Một implementation vận hành HAI nguồn Public Purchase độc lập — identity
      và price không chia sẻ version lineage — FAIL gate này, KỂ CẢ khi mọi
      assertion khác PASS.
```

Fixture bắt buộc:
(1) identity `PUBLIC_PURCHASE` hợp lệ, 0 lệnh ghi Tracking; (2) `price_rows`
tham chiếu một `product_key` vắng khỏi `identity_rows` → lỗi load; (3) file
thiếu khối identity / có khoá top-level lạ → lỗi load (không phải danh mục
rỗng); (4) hai `product_code` chỉ khác hoa/thường → lỗi load; (5) alias trùng
`product_code` của sản phẩm khác → lỗi load; (6) đổi `product_name`/`aliases`
rồi replay report đã ghim version → kết quả không đổi; (7) assertion diff rỗng
trên `file_price_provider.py`.

PASS khi:
Bảy fixture đúng; identity projection và price projection đọc ra từ cùng một
`version_id`.

FAIL khi:
Tồn tại hai đường nạp Public Purchase độc lập; một lỗi shape bị nuốt thành
"danh mục rỗng"; `file_price_provider.py` bị sửa; `INV-06` chỉ được kiểm lúc
tính giá thay vì lúc load.

Nguồn quy phạm:
`INV-02`…`INV-10`; data contract §3; `DEC-154` §3; `DEC-153`; `DEC-156` §1
(`OR-01`).

Evidence:
Chưa thực thi — implementation chưa được cấp phép.

Executed By:
Chưa thực thi.

Timestamp:
Chưa thực thi.

#### CHECK-105D-29 (G29) — Namespace persist cùng mapping, IMMUTABLE

Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E2

Khẳng định:

```text
namespace được PERSIST cùng mapping record, là REQUIRED khi status = CONFIRMED
  và IMMUTABLE trong một mapping record (INV-17, INV-19, §6.2).
Sửa namespace hay source_product_code = tạo mapping mới + supersede, KHÔNG
  phải UPDATE tại chỗ.
Một mapping đọc lại từ store luôn mang namespace, không bao giờ suy ra namespace
  lúc đọc.
```

Ranh giới với `G30`:
`G29` = bất biến LƯU TRỮ (namespace được ghi và không đổi). `G30` = bất biến
SO SÁNH (hai identity cùng code khác namespace không bằng nhau). Một
implementation có thể persist namespace đúng mà vẫn so sánh chỉ bằng code —
`G30` bắt đúng lỗi đó.

Fixture bắt buộc:
Confirm một mapping, đọc lại từ log, kiểm `namespace`; thử `UPDATE` namespace
tại chỗ → bị từ chối; correction đổi namespace → supersede.

PASS khi:
Ba fixture đúng.

FAIL khi:
Namespace suy ra lúc đọc; namespace sửa được tại chỗ.

Nguồn quy phạm:
`INV-17`, `INV-19`, `INV-31`, `INV-32`; data contract §5, §6.2.

Evidence:
Chưa thực thi — implementation chưa được cấp phép.

Executed By:
Chưa thực thi.

Timestamp:
Chưa thực thi.

#### CHECK-105D-30 (G30) — Cùng code khác namespace không collision

Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E2

Khẳng định:

```text
TRACKING:X và PUBLIC_PURCHASE:X là HAI identity KHÁC NHAU (INV-18).
  Không collision, không hợp nhất, KHÔNG so sánh chỉ bằng source_product_code.
Hai mapping cùng code khác namespace cùng tồn tại được, độc lập, không ghi đè
  nhau và không kích hoạt INV-30/INV-39.
Mọi so sánh identity trong mã dùng ĐỦ TUPLE (namespace, source_product_code).
```

Fixture bắt buộc:
Seed `TRACKING:X` và `PUBLIC_PURCHASE:X`; resolve hai raw identity khác nhau
trỏ về hai mapping đó; assert hai kết quả khác nhau và không ghi đè nhau.

PASS khi:
Hai mapping cùng tồn tại; hai outcome khác nhau; không cảnh báo trùng khoá.

FAIL khi:
Bất kỳ so sánh, dict key, hay index nào chỉ dùng `source_product_code`.

Nguồn quy phạm:
`INV-18`; data contract §5; `DEC-154` §5.

Evidence:
Chưa thực thi — implementation chưa được cấp phép.

Executed By:
Chưa thực thi.

Timestamp:
Chưa thực thi.

#### CHECK-105D-31 (G31) — Cross-system mapping explicit + lookup không đoán mã

Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E2

Khẳng định:

```text
PHẦN A — lúc TẠO mapping (nguyên trạng):
  Mapping phải EXPLICIT. CẤM suy ra chỉ vì tracking_code và
      public_purchase_code giống chuỗi nhau — KỂ CẢ khi bằng nhau tuyệt đối,
      vẫn cần confirmation một lần (INV-38).
  1:1 tại một thời điểm: mỗi tracking_code và mỗi public_purchase_code có TỐI
      ĐA MỘT mapping CONFIRMED (INV-39). Vi phạm khi ghi → status = CONFLICT +
      lỗi tường minh, KHÔNG silent last-write-wins (INV-40).
  Correction theo khuôn §13: supersede, KHÔNG DELETE (INV-41).

PHẦN B — lúc TRA CỨU (nạp HARDENING H-02, phần biên TASK-105D sở hữu):
  API cross-system lookup cho một tracking_code trả ĐÚNG public_purchase_code
      của mapping CONFIRMED đang active, HOẶC absence.
  KHÔNG BAO GIỜ trả một mã dẫn xuất: không phải tracking_code, không phải một
      biến thể chuẩn hoá của nó, không phải một mã suy ra — KỂ CẢ khi tồn tại
      một PP product có product_code trùng chuỗi với tracking_code (INV-43c).
  Thiếu mapping CONFIRMED → absence; caller KHÔNG có mã nào để đoán (INV-44).

RANH GIỚI PHẠM VI: điều kiện (a) của INV-43 — "không có valid vendor candidate
tại sale_date" — thuộc lớp composition TASK-105E và KHÔNG được gate ở đây.
TASK-105D chỉ gate phần entity + lookup mà nó sở hữu.
```

Fixture bắt buộc:
(1) `tracking_code == public_purchase_code` về chuỗi nhưng chưa confirm →
lookup trả absence, không tự tạo mapping; (2) ghi mapping thứ hai cho cùng
`tracking_code` → `CONFLICT`; (3) correction → supersede, bản cũ còn trong log;
(4) lookup khi có mapping `CONFIRMED` → trả đúng `public_purchase_code` của
chính mapping đó.

PASS khi:
Bốn fixture đúng; không đường nào sinh mã suy ra.

FAIL khi:
Lookup trả một mã không đến từ một mapping `CONFIRMED`; trùng chuỗi bị coi là
mapping; conflict bị giải bằng last-write-wins.

Nguồn quy phạm:
`INV-38`…`INV-44`; data contract §8.3, §8.4; `DEC-154` §5/§7.

Evidence:
Chưa thực thi — implementation chưa được cấp phép.

Executed By:
Chưa thực thi.

Timestamp:
Chưa thực thi.

#### CHECK-105D-32 (G32) — Cross-system mapping đã confirm reuse không hỏi lại

Priority:
REQUIRED

Status:
NOT_TESTED

Evidence Level:
E1

Khẳng định:

```text
Một CrossSystemProductMapping đã CONFIRMED được REUSE mà KHÔNG hỏi lại:
  count(confirmation_action loại CONFIRM_CROSS_SYSTEM) == 0 ở mọi lần dùng sau
  current_revision() KHÔNG đổi vì việc dùng lại
  fallback thành công KHÔNG đổi namespace của identity: một identity TRACKING
      vẫn là TRACKING sau khi lấy giá từ Public Purchase (INV-45, P10)
  provenance giữ PUBLIC_PURCHASE_NO_VENDOR_PRICE để phân biệt với một identity
      PUBLIC_PURCHASE trực tiếp (PUBLIC_PURCHASE_NO_TRACKING) — DEC-154 §10
```

Ranh giới với `G31`:
`G31` bảo vệ **tính đúng** của mapping (explicit, 1:1, lookup không đoán).
`G32` bảo vệ **chi phí vận hành** (đã confirm thì không hỏi lại) và **bất biến
namespace sau fallback**. Hai invariant khác nhau trên cùng entity.

Fixture bắt buộc:
Mapping `CONFIRMED` sẵn có; chạy hai batch liên tiếp cùng `tracking_code`;
kiểm `count == 0`, revision không đổi, namespace vẫn `TRACKING`, provenance
đúng nhãn.

PASS khi:
Bốn assertion đúng ở cả hai batch.

FAIL khi:
Hỏi lại một mapping đã confirm; namespace đổi thành `PUBLIC_PURCHASE` sau
fallback; provenance không phân biệt được hai đường.

Nguồn quy phạm:
`INV-42`, `INV-45`; data contract §8.3, §8.4; `DEC-154` §7/§10.

Evidence:
Chưa thực thi — implementation chưa được cấp phép.

Executed By:
Chưa thực thi.

Timestamp:
Chưa thực thi.

### Ma trận overlap có chủ đích

Independent review `S036` ghi nhận sáu cặp gate chồng lấn. `DEC-157` giữ
nguyên cả sáu — **không giảm coverage chỉ để tránh overlap** — nhưng ghi rõ
invariant riêng của từng gate để reviewer độc lập không phải suy đoán, và để
phiên implementation không đếm trùng evidence.

| Cặp | Gate thứ nhất bảo vệ | Gate thứ hai bảo vệ | Giữ cả hai vì |
|---|---|---|---|
| `G04` ⊂ `G24` | `G04`: resolve một alias đã confirm là thao tác CHỈ-ĐỌC (0 ghi) | `G24`: batch `N>=2` không làm tăng `current_revision()` | Một implementation có thể không ghi ở read path nhưng vẫn tăng revision ở cuối batch, và ngược lại |
| `G07` ∩ `G06(c)` | `G06(c)`: outcome của MỘT identity `ONLY_SIMILARITY` | `G07`: phủ định TOÀN CỤC — không đường nào (bootstrap/migration/script) biến similarity thành `CONFIRMED` | `G06` chỉ phủ luồng resolve; đường bootstrap nằm ngoài nó |
| `G26` ≈ `G27` ≈ `G28` | `G26`: chiều khẳng định (MISS + PP unique ⇒ resolve PP) | `G27`: chiều phủ định (MISS ⇏ Pending); `G28`: chiều cấu trúc (PP identity hợp lệ + MỘT canonical versioned source) | Ba mệnh đề độc lập; bỏ bất kỳ gate nào để hở một đường lỗi riêng |
| `G10` ∩ `G24` | `G10` Phần A: reuse qua **run/import MỚI** (tiến trình khác) | `G24`: reuse trong **cùng một batch**, revision không đổi | Persistence qua process boundary và revision-stability trong batch là hai lỗi khác nhau |
| `G29` ∩ `G30` | `G29`: bất biến LƯU TRỮ (namespace persist, immutable) | `G30`: bất biến SO SÁNH (không so sánh chỉ bằng code) | Persist đúng vẫn có thể so sánh sai |
| `G31` ∩ `G32` | `G31`: tính ĐÚNG của mapping (explicit, 1:1, lookup không đoán mã) | `G32`: chi phí vận hành (không hỏi lại) + namespace không đổi sau fallback | Mapping đúng vẫn có thể bị hỏi lại; reuse đúng vẫn có thể suy ra mã sai |

## Tiêu Chí Hoàn Thành (Exit Criteria)

- [x] 32/32 REQUIRED check PASS với evidence target — Layer 2 qua
      `docs/reviews/TASK-105D-GATE-EXECUTION-RECORD.md` (`DEC-159`/`DEC-161`).
- [x] 0 BLOCKING finding — `B-01` CLOSED (RC-1, xác minh độc lập S043).
- [x] Migration/rollback + permission/audit contract verified — `INV-81`,
      `INV-82` đóng tại `S048`
      (`docs/reviews/TASK-105D-INV81-INV82-EVIDENCE-CLOSURE.md`).
- [x] Golden và full regression PASS — 58 passed/2 skipped; 965 passed/11
      skipped/0 failed (S048).
- [x] Metrics có denominator và validation theo
      `docs/spec/TASK-105D-DATA-CONTRACT.md` §15 (kể cả `INV-83`
      `AUTO + MANUAL + PENDING = 1`) — phủ bởi `HB-105D-F2-03` +
      `CHECK-105D-*` liên quan §15.
- [x] Toàn bộ invariant `INV-01`…`INV-87` của data contract có assertion
      tương ứng hoặc có lý do ghi rõ vì sao không cần — `INV-08` có lý do ghi
      rõ (§3 data contract); `INV-81`/`INV-82` đóng tại `S048`.
- [x] Independent Review E2 PASS — `S041`/`S043` (implementation),
      `S047` (Independent Review cho chính hành động DONE).
- [x] Progress/roadmap/session handoff cập nhật — `PROJECT/PROJECT_PROGRESS.md`,
      `docs/sessions/S048-task-105d-inv81-inv82-evidence-closure.md`.

## DONE Transition

`READY → DONE` ngày 2026-08-29, bởi phiên `S048` (đóng dấu bởi `DEC-162`,
Owner Decision). `S047` (Independent Review cho chính hành động DONE) xác
định `NEAREST_REMAINING_BLOCKING_CONDITION` duy nhất là evidence chưa đủ cho
`INV-81`/`INV-82` (`H-06`). `S048` đóng đúng khoảng trống đó bằng
test-strengthening tối thiểu (không sửa `app/`/`config/`/`Tracking`, không
mở Repair Cycle #2) — chi tiết đầy đủ:
`docs/reviews/TASK-105D-INV81-INV82-EVIDENCE-CLOSURE.md`. `GATE_SET_SHA256`
byte-identical trước/sau (`0444e58c02b04804a116c140af722ffc29ea64adf468aa6c93794c4408a5c877`).

## Điều Kiện Kích Hoạt Leo Thang (Escalation Triggers)

- Hai catalog không cung cấp stable/versioned identity.
- Model normalization làm mất khác biệt model chính xác.
- Persistence không hỗ trợ conflict detection/idempotency.
- Fuzzy/model output bị đề xuất làm production authority.
- Bất kỳ thiết kế nào yêu cầu mutate Tracking hoặc backfill lịch sử bằng giá
  hiện tại.

## Đăng Ký File Đã Thay Đổi (Changed Files Registry)

Created:
- `docs/tasks/TASK-105D-product-identity-resolver.md` (S032/`DEC-154`)
- `docs/spec/TASK-105D-DATA-CONTRACT.md` (S034/`DEC-155`)
- `docs/reviews/TASK-105D-FREEZE-FINALIZATION-REVIEW.md` (S036)
- `docs/reviews/TASK-105D-COMPLETION-GATE-CHANGE-PROPOSAL.md` (S037/`DEC-157`)
- `docs/reviews/TASK-105D-FREEZE-FINALIZATION-REVIEW-2.md` (S038 — freeze
  finalization retry, verdict `PASS WITH HARDENING`, Completion Gate `FROZEN`)
- `docs/reviews/TASK-105D-GATE-EXECUTION-RECORD.md` (S040 — bản ghi thực thi
  32 frozen check: 32/32 PASS, A–T 20/20, Golden/full/validator evidence E2)
- `docs/sessions/S040-task-105d-implementation.md` (S040 — phiên implementation)

Production implementation (S040, nhánh `task/task-105d-implementation` —
**implementation candidate**, chưa qua Independent Review, chưa merge default):
- `app/modules/product/identity/` — 19 module, ánh xạ 1:1 với entity
  `E-A`…`E-L` của data contract (`keys`, `identity`, `evidence`,
  `tracking_catalog`, `public_purchase`, `mapping`, `rejection`,
  `cross_system`, `registry`, `audit`, `store`, `binding`, `commands`,
  `service`, `resolver`, `drift`, `metrics`, `cli`, `__init__`).
- `tests/support/identity_fixtures.py` + 5 file test
  (`tests/test_105d_identity_keys.py`, `…_cutover_registry.py`,
  `…_resolution.py`, `…_persistence.py`, `…_audit_replay.py`,
  `…_boundaries.py`) — 174 test, toàn bộ fixture là dữ liệu TỔNG HỢP.

KHÔNG đổi (xác minh bằng `git diff` rỗng): `app/pipeline.py`,
`app/modules/pricing/file_price_provider.py` (FROZEN — `DEC-153`),
`tests/test_golden_baseline.py`, `tests/fixtures/`.

**Khối Completion Gate ở trên KHÔNG bị sửa một byte nào** — `GATE_SET_SHA256`
tái lập khớp tuyệt đối sau phiên implementation. Vì thế 32 trường `Status:`
trong khối đó vẫn đọc là `NOT_TESTED`: đó là hệ quả của việc giữ nguyên
artifact đã freeze, **không** phải tuyên bố "chưa chạy". Kết quả thực thi thật
(32/32 `PASS`, evidence, test reference, output nguyên văn) nằm ở
`docs/reviews/TASK-105D-GATE-EXECUTION-RECORD.md`, kèm lý do tại §1 của file
đó. Ghi `PASS` trực tiếp vào khối gate sẽ đổi `GATE_SET_SHA256` và vì vậy cần
một `COMPLETION GATE CHANGE PROPOSAL` + authority riêng — ngoài thẩm quyền
phiên implementation.

## Ghi Chú (Notes)

Task này là specification canonical được tạo trong phiên reconciliation.
Không đọc `Specification State = COMPLETE` thành `READY`, `FROZEN`,
`IMPLEMENTED` hoặc `DONE`.
