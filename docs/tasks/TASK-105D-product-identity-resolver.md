# TASK-105D — Product Identity Resolver

## Metadata

Status:
PLANNED

Specification State:
COMPLETE — semantics Owner đã chốt tại `DEC-154`; data contract/persistence/
audit design đã chốt tại `DEC-155` +
`docs/spec/TASK-105D-DATA-CONTRACT.md` (S034). Completion Gate vẫn CHƯA
freeze và implementation vẫn CHƯA được cấp phép.

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
- Tracking deterministic unique match: có thể auto-resolve `TRACKING:<code>`.
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
- Candidate #1 đúng: mục tiêu tối đa 1 thao tác bình thường.
- Known mapping: 0 thao tác bình thường.
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
  của người vận hành**, không phải danh tính đã xác thực (`OR-03`, chờ Owner
  ratification). Đây là một hạn chế thật, không được mô tả là "authenticated".
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
- [ ] **BLOCKER DUY NHẤT CÒN LẠI — Completion Gate freeze.** Gate 32 check
      vẫn `DRAFT`. `governance/core/V4_1_POLICY_FREEZE.md` §12: `FROZEN` chỉ
      được ghi bởi một phiên Freeze Finalization có thẩm quyền riêng. Phiên
      readiness và phiên ratification đều KHÔNG tự freeze.

Không phải blocker của Ready Gate nhưng là **dependency dữ liệu của
implementation** (ghi ở đây để không bị đọc nhầm thành đã có): bảng mapping
Owner-confirmed cho bootstrap (nếu có), báo cáo lịch sử Owner-confirmed cho
registry, `PublicPurchaseSourceVersion` thật đầu tiên, và capture Tracking
đầu tiên. Không có chúng thì implementation vẫn chạy được với store rỗng —
kết quả đúng là Pending, không phải lỗi (§14.3).

**Ready verdict:** `BLOCKED`. Không chuyển thẳng `PLANNED → IN_PROGRESS`.
Số blocker: 4 (trước S034) → 2 (sau S034) → **1** (sau `DEC-156`/S035).
Blocker còn lại nằm ngoài thẩm quyền của cả phiên readiness lẫn phiên
ratification — chỉ một phiên Freeze Finalization mới đóng được.

## Completion Gate (DRAFT — CHƯA FROZEN)

Toàn bộ check REQUIRED, `Status = NOT_TESTED`; Effective Risk HIGH yêu cầu
E1 cho check thực thi được và E2 cho data/cutover/concurrency/Golden critical.

### Định nghĩa vận hành bắt buộc (S034 / `DEC-155` — giải HB-154-05)

Trước khi đọc bảng, ba khái niệm dưới đây là **quy phạm**. Chúng thay các
phát biểu định tính mà independent review chỉ ra là chưa test được. Nguồn đầy
đủ: `docs/spec/TASK-105D-DATA-CONTRACT.md` §17.

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

AMBIGUOUS
    = resolution_method KHÔNG thuộc tập auto-resolve đóng (ALIAS_EXACT,
      ALIAS_AID_UNIQUE, CATALOG_EXACT_UNIQUE — data contract §6.6).
    Ba nguồn ambiguity, mỗi nguồn một fixture bắt buộc: MULTIPLE_EXACT,
      CROSS_NAMESPACE_TIE, ONLY_SIMILARITY.

normal action
    = đồng nghĩa `confirmation_action`. Không còn dùng cụm "thao tác bình
      thường" mà không quy chiếu định nghĩa này.
```

| ID | Check | Status | Evidence target |
|---|---|---|---|
| CHECK-105D-01 (G01) | Pre-cutover Owner-confirmed report bypass resolver/provider; late arrival dùng `sale_date` | NOT_TESTED | E2 |
| CHECK-105D-02 (G02) | Post-cutover resolver trả đúng tuple hoặc Pending | NOT_TESTED | E1 |
| CHECK-105D-03 (G03) | DISTINCT-before-mapping, không thao tác từng row | NOT_TESTED | E1 |
| CHECK-105D-04 (G04) | Alias đã confirm = 0 interaction | NOT_TESTED | E1 |
| CHECK-105D-05 (G05) | Deterministic unique match có thể auto-resolve | NOT_TESTED | E2 |
| CHECK-105D-06 (G06) | AMBIGUOUS (định nghĩa §Định nghĩa vận hành) không bao giờ auto-resolve: catalog có hai entry chỉ khác đúng một model token + raw identity mang token thứ ba → outcome ∈ {REQUIRES_CONFIRMATION, PENDING_PRODUCT} và `resolution_method` ∉ tập auto-resolve. Ba fixture: MULTIPLE_EXACT, CROSS_NAMESPACE_TIE, ONLY_SIMILARITY | NOT_TESTED | E2 |
| CHECK-105D-07 (G07) | Fuzzy-only không auto-confirm | NOT_TESTED | E2 |
| CHECK-105D-08 (G08) | Candidate ranking ổn định, có evidence | NOT_TESTED | E1 |
| CHECK-105D-09 (G09) | Confirmation persist | NOT_TESTED | E1 |
| CHECK-105D-10 (G10) | Persisted mapping reuse qua import/run mới | NOT_TESTED | E1 |
| CHECK-105D-11 (G11) | Một confirmation resolve mọi affected rows/orders | NOT_TESTED | E1 |
| CHECK-105D-12 (G12) | Rejected candidate được nhớ, chỉ tái hiện khi evidence đổi | NOT_TESTED | E1 |
| CHECK-105D-13 (G13) | `PENDING_PRODUCT` là một biến thể riêng về KIỂU của `ResolutionOutcome` (a) không phải `None`/`""`/`0`; (b) mang `reason_code` thuộc enum đóng + `attempted_sources` không rỗng khi resolver đã chạy; (c) không mang `namespace`/`source_product_code`; (d) một identity Pending không chặn các identity khác trong cùng batch | NOT_TESTED | E1 |
| CHECK-105D-14 (G14) | Raw accounting name bất biến | NOT_TESTED | E2 |
| CHECK-105D-15 (G15) | Mapping không lưu fixed purchase price | NOT_TESTED | E2 |
| CHECK-105D-16 (G16) | Price-provider boundary được giữ | NOT_TESTED | E2 |
| CHECK-105D-17 (G17) | Tracking không bị mutate | NOT_TESTED | E2 |
| CHECK-105D-18 (G18) | Correction audit giữ old/new mapping | NOT_TESTED | E2 |
| CHECK-105D-19 (G19) | Duplicate import/idempotency không tạo side effect trùng | NOT_TESTED | E2 |
| CHECK-105D-20 (G20) | Concurrent conflicting confirmation bị chặn, không LWW | NOT_TESTED | E2 |
| CHECK-105D-21 (G21) | Provenance đủ raw/tuple/source/version/method | NOT_TESTED | E1 |
| CHECK-105D-22 (G22) | Core batch flow thao tác hoàn toàn bằng bàn phím | NOT_TESTED | E1 |
| CHECK-105D-23 (G23) | Identity AMBIGUOUS có candidate rank 1 đúng: `count(confirmation_action) == 1`; một action đó resolve MỌI dòng cùng identity; lần chạy kế tiếp trên chính identity đó `count == 0`. **Fixture bắt buộc bổ sung (`DEC-156`/`OR-02`):** trường hợp `ALIAS_AID_UNIQUE` — không auto-resolve, xuất hiện ở candidate #1, tốn đúng 1 action, lần hai tốn 0 qua `ALIAS_EXACT` | NOT_TESTED | E1 |
| CHECK-105D-24 (G24) | Store đã có mapping CONFIRMED cho `raw_identity_key` K, batch chứa N≥2 dòng identity K: `count(confirmation_action) == 0`, `resolution_method == ALIAS_EXACT`, và `current_revision()` KHÔNG đổi | NOT_TESTED | E1 |
| CHECK-105D-25 (G25) | Golden Business Baseline không đổi | NOT_TESTED | E2 |
| CHECK-105D-26 (G26) | Tracking MISS + Public Purchase unique match → PUBLIC_PURCHASE | NOT_TESTED | E2 |
| CHECK-105D-27 (G27) | Tracking MISS không tự động thành Pending | NOT_TESTED | E1 |
| CHECK-105D-28 (G28) | PUBLIC_PURCHASE identity không cần Tracking product giả | NOT_TESTED | E2 |
| CHECK-105D-29 (G29) | Namespace persist cùng mapping | NOT_TESTED | E2 |
| CHECK-105D-30 (G30) | Cùng code khác namespace không collision | NOT_TESTED | E2 |
| CHECK-105D-31 (G31) | Cross-system mapping explicit/auditable/correctable | NOT_TESTED | E2 |
| CHECK-105D-32 (G32) | Cross-system mapping đã confirm reuse không hỏi lại | NOT_TESTED | E1 |

## Tiêu Chí Hoàn Thành (Exit Criteria)

- [ ] 32/32 REQUIRED check PASS với evidence target.
- [ ] 0 BLOCKING finding.
- [ ] Migration/rollback + permission/audit contract verified.
- [ ] Golden và full regression PASS.
- [ ] Metrics có denominator và validation theo
      `docs/spec/TASK-105D-DATA-CONTRACT.md` §15 (kể cả `INV-83`
      `AUTO + MANUAL + PENDING = 1`).
- [ ] Toàn bộ invariant `INV-01`…`INV-87` của data contract có assertion
      tương ứng hoặc có lý do ghi rõ vì sao không cần.
- [ ] Independent Review E2 PASS.
- [ ] Progress/roadmap/session handoff cập nhật.

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

Production implementation:
- Không có.

## Ghi Chú (Notes)

Task này là specification canonical được tạo trong phiên reconciliation.
Không đọc `Specification State = COMPLETE` thành `READY`, `FROZEN`,
`IMPLEMENTED` hoặc `DONE`.
