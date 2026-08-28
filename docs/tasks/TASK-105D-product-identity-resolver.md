# TASK-105D — Product Identity Resolver

## Metadata

Status:
PLANNED

Specification State:
COMPLETE — semantics Owner đã chốt tại `DEC-154`; Completion Gate chưa
freeze và implementation chưa được cấp phép.

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
`DEC-154` — PRODUCT IDENTITY & PURCHASE PRICE RESOLUTION.

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

- Alias đã confirm: reuse ngay, 0 thao tác lặp.
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
input cho price resolution theo `DEC-154` P01–P10:

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
- `MANUAL_ACTIONS_PER_100_ORDERS`

Metric phải có denominator/version rõ ràng và không log dữ liệu khách hàng
không cần thiết.

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
  chưa được cung cấp canonical.
- Registry/report lịch sử Owner-confirmed cho pre-cutover bypass — chưa được
  cung cấp làm dữ liệu production.
- Persistent storage + audit/auth mechanism đủ cho alias/correction/
  concurrency — implementation mechanism chưa được chọn/finalize.
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

- [x] Objective/scope/out-of-scope đã xác định.
- [x] Business semantics/cutover/namespaces đã được Owner chốt (`DEC-154`).
- [x] Difficulty/Risk/Blast Radius/agent tier đã xác định.
- [x] Completion Gate dự thảo đầy đủ.
- [ ] Catalog contracts/snapshots và historical-confirmed registry có data
      contract canonical.
- [ ] Persistence/migration/rollback/concurrency mechanism được chọn.
- [ ] Permission + audit implementation dependency sẵn sàng.
- [ ] Completion Gate được review và freeze bởi authority riêng.

**Ready verdict:** `BLOCKED`. Không chuyển thẳng `PLANNED → IN_PROGRESS`.

## Completion Gate (DRAFT — CHƯA FROZEN)

Toàn bộ check REQUIRED, `Status = NOT_TESTED`; Effective Risk HIGH yêu cầu
E1 cho check thực thi được và E2 cho data/cutover/concurrency/Golden critical.

| ID | Check | Status | Evidence target |
|---|---|---|---|
| CHECK-105D-01 (G01) | Pre-cutover Owner-confirmed report bypass resolver/provider; late arrival dùng `sale_date` | NOT_TESTED | E2 |
| CHECK-105D-02 (G02) | Post-cutover resolver trả đúng tuple hoặc Pending | NOT_TESTED | E1 |
| CHECK-105D-03 (G03) | DISTINCT-before-mapping, không thao tác từng row | NOT_TESTED | E1 |
| CHECK-105D-04 (G04) | Alias đã confirm = 0 interaction | NOT_TESTED | E1 |
| CHECK-105D-05 (G05) | Deterministic unique match có thể auto-resolve | NOT_TESTED | E2 |
| CHECK-105D-06 (G06) | Model mơ hồ không silent auto-resolve | NOT_TESTED | E2 |
| CHECK-105D-07 (G07) | Fuzzy-only không auto-confirm | NOT_TESTED | E2 |
| CHECK-105D-08 (G08) | Candidate ranking ổn định, có evidence | NOT_TESTED | E1 |
| CHECK-105D-09 (G09) | Confirmation persist | NOT_TESTED | E1 |
| CHECK-105D-10 (G10) | Persisted mapping reuse qua import/run mới | NOT_TESTED | E1 |
| CHECK-105D-11 (G11) | Một confirmation resolve mọi affected rows/orders | NOT_TESTED | E1 |
| CHECK-105D-12 (G12) | Rejected candidate được nhớ, chỉ tái hiện khi evidence đổi | NOT_TESTED | E1 |
| CHECK-105D-13 (G13) | `PENDING_PRODUCT` được hỗ trợ rõ ràng | NOT_TESTED | E1 |
| CHECK-105D-14 (G14) | Raw accounting name bất biến | NOT_TESTED | E2 |
| CHECK-105D-15 (G15) | Mapping không lưu fixed purchase price | NOT_TESTED | E2 |
| CHECK-105D-16 (G16) | Price-provider boundary được giữ | NOT_TESTED | E2 |
| CHECK-105D-17 (G17) | Tracking không bị mutate | NOT_TESTED | E2 |
| CHECK-105D-18 (G18) | Correction audit giữ old/new mapping | NOT_TESTED | E2 |
| CHECK-105D-19 (G19) | Duplicate import/idempotency không tạo side effect trùng | NOT_TESTED | E2 |
| CHECK-105D-20 (G20) | Concurrent conflicting confirmation bị chặn, không LWW | NOT_TESTED | E2 |
| CHECK-105D-21 (G21) | Provenance đủ raw/tuple/source/version/method | NOT_TESTED | E1 |
| CHECK-105D-22 (G22) | Core batch flow thao tác hoàn toàn bằng bàn phím | NOT_TESTED | E1 |
| CHECK-105D-23 (G23) | Candidate #1 đúng đạt ≤1 normal action | NOT_TESTED | E1 |
| CHECK-105D-24 (G24) | Known mapping đạt 0 normal action | NOT_TESTED | E1 |
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
- [ ] Metrics có denominator và validation.
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
- `docs/tasks/TASK-105D-product-identity-resolver.md`

Production implementation:
- Không có.

## Ghi Chú (Notes)

Task này là specification canonical được tạo trong phiên reconciliation.
Không đọc `Specification State = COMPLETE` thành `READY`, `FROZEN`,
`IMPLEMENTED` hoặc `DONE`.
