# TASK-105D — DATA CONTRACT, PERSISTENCE & AUDIT DESIGN

Artifact Type:
CANONICAL DESIGN / DATA CONTRACT SPECIFICATION (readiness artifact, không
phải implementation).

Status:
`READINESS_DESIGN_COMPLETE — OWNER_RATIFIED (DEC-156) — PENDING_GATE_FREEZE`

Authority:
`DEC-155` (bản ghi quyết định của phiên readiness) trên nền `DEC-154`
(Owner Decision — PRODUCT IDENTITY & PURCHASE PRICE RESOLUTION), **đã được
Owner phê chuẩn tại `DEC-156` (2026-08-28)**.

```text
OR-01  APPROVED                         — §3 giữ nguyên
OR-02  APPROVED WITH CANDIDATE-ONLY POLICY — §6.6 ĐÃ SỬA THEO OWNER
OR-03  APPROVED FOR PHASE 1             — §12.1 giữ nguyên + capability boundary
```

Không còn mục `OWNER_RATIFICATION_REQUIRED` nào mở trong file này. Blocker
duy nhất còn lại của `TASK-105D` là Completion Gate freeze bởi một phiên
Freeze Finalization có thẩm quyền riêng (`governance/core/V4_1_POLICY_FREEZE.md` §12).

Task lineage:
`TASK-105D` — root lineage riêng (`PROJECT/REVIEW_BUDGET_LEDGER.md`).

Effective Risk:
`HIGH` — `max(Local Risk 4, Blast Radius 5)`, theo failure path
`sai identity → sai nguồn giá → sai KpiPurchasePrice → sai KPI/lương`
(V4.1 §4). Golden hiện chỉ phủ `PendingPriceProvider`, không hạ bậc
(V4.1 §4.1).

Session:
`docs/sessions/S034-task-105d-readiness-data-contract.md`.

Phiên tạo file này **không** sửa `app/**`, `tests/**`, `config/**`, Golden
fixture/expected, và **không** implement bất kỳ entity nào bên dưới.

---

## 0. Cách đọc file này

File này là **hợp đồng dữ liệu**, không phải mã nguồn. Mọi khối `text` mô tả
schema là **normative** (quy phạm). Theo `governance/core/V4_1_POLICY_FREEZE.md`
§11 (ARTIFACT INTERNAL PRECEDENCE): khi prose và bảng/schema/enum trong chính
file này mâu thuẫn, **phần quy phạm thắng**, và divergence phải được báo cáo,
không được tự dàn xếp.

Quy ước ký hiệu:

```text
REQUIRED   trường bắt buộc, không được rỗng
OPTIONAL   trường có thể vắng; vắng ≠ rỗng ≠ 0 (03_DATA_MODEL_RULES §5)
IMMUTABLE  không được sửa sau khi ghi; sửa = tạo bản ghi mới + supersede
DERIVED    dẫn xuất, không phải nguồn sự thật, không được dùng làm khoá chính
```

Tên field, tên enum và ID giữ nguyên tiếng Anh theo `CLAUDE.md` §"Ngôn Ngữ
Nội Dung". Tên trong file này là **tên khái niệm (conceptual)**; phiên
implementation được đổi tên theo convention repo miễn là giữ nguyên ngữ
nghĩa và invariant.

Bảng ID quy phạm dùng trong file này:

```text
D-xx     Design Decision của phiên readiness (thẩm quyền phiên này)
OR-xx    mục từng ở trạng thái OWNER_RATIFICATION_REQUIRED; toàn bộ đã
         được Owner phê chuẩn tại DEC-156 (OR-02 kèm sửa đổi)
INV-xx   Invariant bắt buộc (phải trở thành assertion khi implement)
E-x      Entity (A…L theo brief)
```

---

## 1. Nguyên tắc nghiệp vụ điều khiển toàn bộ thiết kế

Thiết kế này tối ưu cho một mục tiêu vận hành duy nhất: **giảm thao tác
người mà không tăng nguy cơ map sai**. Hai vế không được đánh đổi cho nhau.

```text
KNOWN (alias đã confirm)         → 0 confirmation_action
DETERMINISTIC (khớp duy nhất)    → 0 confirmation_action
AMBIGUOUS (candidate #1 đúng)    → <= 1 confirmation_action
SAME IDENTITY xuất hiện N lần    → xử lý 1 lần theo DISTINCT identity
CONFIRMED                        → nhớ, không hỏi lại
REJECTED                         → nhớ, không gợi ý lại khi evidence không đổi
UNKNOWN                          → PENDING_PRODUCT (trạng thái hợp lệ)
```

**INV-01.** Không có cơ chế nào trong file này được phép nâng
`AUTO_RESOLUTION_RATE` bằng cách suy đoán mã sản phẩm. Mọi auto-resolve phải
truy ngược được về một trong ba nguồn: (a) một confirmation của người đã
persist, (b) một khớp **chính xác** (exact) sau chuẩn hoá đã được canonical
authorize, (c) một bản ghi registry lịch sử đã được Owner xác nhận.
Similarity/fuzzy/AI **chỉ** được xếp hạng candidate.

---

## 2. Sơ đồ tổng thể

```text
                    ┌──────────────────────────────────────┐
                    │  PublicPurchaseSourceVersion (E-A)   │
                    │  MỘT nguồn versioned, HAI projection │
                    ├──────────────────┬───────────────────┤
                    │ Identity (E-B)   │ Price (E-C)       │
                    └────────┬─────────┴─────────┬─────────┘
                             │                   │
   TrackingCatalogSnapshot   │                   │
   (E-D, read-only capture)  │                   │
             │               │                   │
             ▼               ▼                   ▼
   ┌───────────────────────────────────┐   ┌──────────────────────┐
   │ TASK-105D PRODUCT IDENTITY        │   │ TASK-105B            │
   │ RESOLVER                          │   │ PublicPurchasePrice  │
   │  ProductIdentityMapping (E-F)     │   └──────────────────────┘
   │  AliasMemory index      (E-G)     │            ▲
   │  RejectedCandidate      (E-H)     │            │
   │  CrossSystemProductMapping (E-I)  │────────────┘ (fallback, chỉ khi
   │  HistoricalConfirmedRegistry(E-J) │               có mapping E-I)
   │  MappingAuditEvent      (E-K)     │
   │  ResolutionBinding      (E-L)     │
   └───────────────┬───────────────────┘
                   │ CanonicalProductIdentity (E-E)
                   ▼
   TRACKING ──► TASK-105C HistoricalVendorMin ──► absence ──► (E-I) ──► 105B
   PUBLIC_PURCHASE ──────────────────────────────────────────────────► 105B
                   │
                   ▼
        PRICE RESOLUTION P00–P11 (chưa có implementation owner — §16)
                   ▼
        KpiPurchasePrice / TASK-108B
```

---

## 3. E-A — `PublicPurchaseSource` và `PublicPurchaseSourceVersion`

### 3.1 Quyết định trọng tâm (giải HB-154-02)

**D-01 — MỘT nguồn Public Purchase versioned, HAI projection.**

Public Purchase identity catalog và Public Purchase price table **KHÔNG**
được vận hành như hai nguồn dữ liệu độc lập do nhân viên duy trì tay riêng
rẽ. Chúng là **hai projection của cùng một `PublicPurchaseSourceVersion`**,
xuất bản cùng lúc, mang cùng `version_id`, và được kiểm tra ràng buộc chéo
tại thời điểm publish.

Lý do (ba lý do độc lập, mỗi lý do đủ để loại phương án hai nguồn):

1. **Vận hành.** Hai file phải nhập tay độc lập tạo ra đúng loại quy trình
   thủ công thừa mà `TASK-105D` tồn tại để loại bỏ, và tạo drift im lặng
   giữa "mã có tên" và "mã có giá".
2. **Replay.** `DEC-154` §9 yêu cầu replay theo `sale_date` cho giá và
   `TASK-105D` yêu cầu catalog snapshot có version. Nếu hai version độc lập,
   một report replay phải ghim hai version và không luật nào ràng buộc chúng
   khớp nhau — lỗ hổng chính xác mà HB-154-02 nêu.
3. **Tính toàn vẹn tham chiếu.** Một `source_product_code` có giá nhưng vắng
   trong catalog là một identity không tra tới được — hành vi chưa định
   nghĩa. Ràng buộc chéo trong cùng một version biến nó thành lỗi load, phát
   hiện ngay lúc publish, không phải lúc tính lương.

**D-02 — Không bắt buộc một file vật lý duy nhất, nhưng bắt buộc một lineage
version duy nhất.** Phiên implementation được chọn biểu diễn vật lý (một file
YAML hai khối, hoặc hai file cùng `version_id` + `content_hash` chung). Điều
**bắt buộc** là: một hành động publish → một `version_id` → cả hai projection
được validate cùng nhau → không projection nào tồn tại độc lập ngoài một
version.

Biểu diễn được khuyến nghị (một file YAML một version):

```yaml
source_id: PUBLIC_PURCHASE
version_id: PP-20260901-01
published_at: 2026-09-01T09:00:00+07:00
published_by: <actor_id>
supersedes: PP-20260828-03      # null cho version đầu tiên
products:                        # identity projection (E-B)
  - product_code: KG36A2
    product_name: "Cây nước Kangaroo KG36A2"
    aliases: ["Kangaroo KG36A2"]
    active_from: 2026-09-01
    active_to: null
prices:                          # price projection (E-C)
  - product_key: KG36A2
    effective_from: 2026-09-01
    effective_to: 2026-09-30
    purchase_price: 3150000
    source: "PUBLIC_PURCHASE/PP-20260901-01"
```

Khối `prices` giữ nguyên schema 4 cột đã frozen tại `DEC-145` §4 để
`FilePriceProvider` (FROZEN, `DEC-153`) đọc được **mà không phải sửa module
đó**. Khối `products` là khối mới, do một loader riêng đọc.

**INV-02 (quan trọng).** `FilePriceProvider.from_yaml()` hiện đọc
`data.get("prices", [])` và **bỏ qua mọi khoá top-level khác**. Vì vậy một
lỗi chính tả ở `products:` sẽ nạp 0 dòng identity **trong im lặng**. Loader
của projection identity **BẮT BUỘC** là strict: thiếu/sai tên khối, khối rỗng,
hay khoá top-level lạ → lỗi load, không phải danh mục rỗng. Đây là lý do
projection identity **không** được nhét vào `FilePriceProvider`.

**INV-03.** Phiên implementation **không được sửa**
`app/modules/pricing/file_price_provider.py` (FROZEN theo `DEC-153`) để đọc
`products`. Đường đi hợp lệ duy nhất là một
`PublicPurchaseSourceLoader` riêng: validate cả hai projection, rồi truyền
khối `prices` đã validate vào `FilePriceProvider` qua constructor `rows`.

**Hardening re-trigger đã được thiết kế này định vị chính xác.** Thiết kế
này **không** trigger `HB-105B-03/05/06/10` ngay bây giờ (không dataset thật
nào được nạp, không code nào đổi), nhưng nó chốt đúng thời điểm trigger:
lần đầu một `PublicPurchaseSourceVersion` **thật** được nạp qua
`FilePriceProvider` là lúc cả bốn finding phải đã được xử lý. Ghi lại nguyên
văn để phiên sau không phải suy luận lại.

### 3.2 Schema

```text
E-A  PublicPurchaseSourceVersion

source_id           REQUIRED IMMUTABLE  enum; Phase 1 = "PUBLIC_PURCHASE"
version_id          REQUIRED IMMUTABLE  "PP-<YYYYMMDD>-<NN>", duy nhất toàn cục
status              REQUIRED            DRAFT | PUBLISHED | ROLLED_BACK
published_at        REQUIRED khi PUBLISHED, IMMUTABLE
published_by        REQUIRED khi PUBLISHED, IMMUTABLE  (actor, §12)
supersedes          OPTIONAL IMMUTABLE  version_id của bản trước
rollback_of         OPTIONAL IMMUTABLE  version_id bị rollback (§14)
content_hash        REQUIRED IMMUTABLE  hash trên CẢ HAI projection đã canonical hoá
identity_rows       REQUIRED            list<E-B>
price_rows          REQUIRED            list<E-C>
note                OPTIONAL            lý do publish, ghi cho người đọc
```

### 3.3 Trả lời 13 câu hỏi bắt buộc

| # | Câu hỏi | Câu trả lời quy phạm |
|---|---|---|
| 1 | Source ID là gì? | `source_id` — enum. Phase 1 có đúng một giá trị `PUBLIC_PURCHASE`. Schema cho phép thêm source sau, nhưng thêm source là quyết định Owner, không phải config. |
| 2 | Version ID là gì? | `version_id` = `PP-<YYYYMMDD>-<NN>`. Đơn điệu tăng trong một `source_id`. IMMUTABLE sau publish. |
| 3 | Snapshot ID là gì? | Với Public Purchase, **version chính là snapshot** — không có ID thứ hai (đây là hệ quả trực tiếp của D-01). Với Tracking, snapshot là `capture_id` riêng (§4) vì Tracking là hệ thống ngoài, không publish version cho Reports. |
| 4 | `product_code` unique ở scope nào? | Unique trong `(source_id, version_id)`. Hai invariant: INV-04 (unique trên giá trị thô) và INV-05 (không đụng độ sau `fold()`). |
| 5 | Identity liên hệ Price thế nào? | Khoá ngoại trong cùng version: `price_rows[*].product_key` phải tồn tại trong `identity_rows[*].product_code` của **chính version đó** (INV-06). |
| 6 | Giá đổi mà identity không đổi? | Publish version mới. Projection identity có thể giống hệt byte-for-byte. Version ở cấp **source**, không ở cấp dòng. Không có "version riêng cho giá". |
| 7 | Tên/alias đổi thì replay report cũ ra sao? | Report cũ ghim `version_id` cũ (E-L) và đọc lại đúng version đó → hiển thị tên cũ, cho ra đúng kết quả cũ. Đổi `product_name`/`aliases` **không bao giờ** làm đổi kết quả của một report đã ghim (INV-07). |
| 8 | Report ghim gì? | `ResolutionBinding` (E-L) = bộ ba `(pp_version_id, tracking_capture_id, mapping_store_revision)`. Ghim cả ba, không ghim từng phần. |
| 9 | Thiếu version thì sao? | Lỗi cứng `SourceVersionNotFound` — **KHÔNG** fallback sang version mới nhất, **KHÔNG** biến thành Pending. Đây là "source failure ≠ determined absence" (tiền lệ `CHECK-105C-17`). Pending là kết luận về dữ liệu; thiếu version là hỏng hệ thống. |
| 10 | Rollback version thế nào? | Không sửa, không xoá version đã publish. Publish một version **mới** với `rollback_of = <version lỗi>` và nội dung khôi phục. Report đã ghim version lỗi vẫn ghim nó cho tới khi có một re-pin được audit (§13.3). |
| 11 | Ai được publish? | Quyền `PUBLIC_PURCHASE_SOURCE_PUBLISH` (§12). Phase 1: role `ADMIN` (`DEC-124`). |
| 12 | DRAFT vs PUBLISHED? | `DRAFT` sửa được tự do, **không** được resolver hay price provider đọc, tối đa **một** DRAFT cho mỗi `source_id` cùng lúc. `PUBLISHED` bất biến. Chuyển DRAFT → PUBLISHED chạy toàn bộ validation §3.4. |
| 13 | Có sửa Published snapshot không? | **KHÔNG.** Published snapshot IMMUTABLE. Không có ngoại lệ, kể cả sửa lỗi chính tả tên hàng — sửa = version mới. |

### 3.4 Invariant khi publish

```text
INV-04  product_code unique trong version (so sánh trên giá trị thô).
INV-05  fold(product_code) unique trong version.
        Hai mã chỉ khác nhau ở hoa/thường/khoảng trắng/dạng Unicode là LỖI
        LOAD, không phải hai sản phẩm. Lý do: DEC-147 §4 ghi nhận normCode
        của Tracking đã từng gộp nhầm hai mã chỉ khác gạch nối. Không lặp lại.
INV-06  mọi price_rows[*].product_key tồn tại trong identity_rows của cùng
        version. Vi phạm = lỗi load (đóng lỗ replay của HB-154-02).
INV-07  đổi product_name/aliases không đổi kết quả của report đã ghim version.
INV-08  khoảng [effective_from, effective_to] tuân thủ nguyên văn DEC-145 §1/§5
        (đóng, không chồng lấn, tối đa một open record mỗi product_key).
        FilePriceProvider đã thi hành phần này — không viết lại logic đó.
INV-09  alias trong identity projection không được trùng với product_code của
        một sản phẩm KHÁC trong cùng version (sau fold). Vi phạm = lỗi load.
INV-10  content_hash tính trên biểu diễn canonical của CẢ HAI projection.
        Hai version có content_hash bằng nhau nhưng version_id khác nhau là
        hợp lệ (republish không đổi nội dung), nhưng phải ghi note lý do.
```

**OR-01 — `APPROVED` (Owner, `DEC-156`, 2026-08-28).** Chủ dự án chấp thuận
vận hành Public Purchase như **MỘT canonical versioned source**: Identity
Projection và Price Projection là hai projection của cùng một
`PublicPurchaseSourceVersion`/source-version lineage; **không** thiết kế
thành hai quy trình nhập liệu vận hành độc lập; published version
**immutable**. Toàn bộ §3 (D-01, D-02, `INV-02`…`INV-10`) giữ nguyên và nay
là contract đã được phê chuẩn, không còn là đề xuất.

---

## 4. E-D — `TrackingCatalogSnapshot` (read-only contract)

### 4.1 Ranh giới

`TASK-105D` **đọc** danh mục Tracking và **không bao giờ** ghi vào Tracking.
Tuân thủ `DEC-152` §6 và `ADR-101`: phần chạm mạng nằm **ngoài**
`app/modules/` (ví dụ `tools/tracking/`), ghi ra một file snapshot bất biến;
`app/modules/` chỉ đọc file snapshot.

```text
tools/tracking/  (chạm mạng, ngoài app/modules/)
      │  đọc RTDB read-only
      ▼
  snapshot file BẤT BIẾN (không ghi đè)
      │
      ▼
app/modules/product/...  (hàm thuần, không mạng, không biết RTDB tồn tại)
```

### 4.2 Canonical Tracking product code

Bằng chứng đã audit (`DEC-147` §4):

```text
Khoá node    : board/<MÃ>, với MÃ = normCode(mã) = toUpperCase() + bỏ mọi ký
               tự ngoài [A-Z0-9], rồi qua aliasOf()
Tên đọc được : board/<MÃ>/name        ví dụ "SJ-X198V-DG"
Cách viết gộp: board/<MÃ>/alt[]
Bảng người duyệt: inv.map (N_<normCode(tên hàng)> → <MÃ>), alias.map (<mã cũ> → <mã chính>)
```

**D-03.** Canonical Tracking product code cho `TASK-105D` là **khoá node
`board/<MÃ>` sau `aliasOf()`** — không phải `name`, không phải `alt`, không
phải kết quả của bất kỳ hàm rút mã nào.

**D-04 — Cấm tuyệt đối tái phát minh `extractCode()`.** `DEC-147` §4 ghi lại
một tiền lệ production thật: Tracking đã thử rút mã từ câu tên hàng bằng máy
("token cuối cùng có chứa số") và **bỏ hẳn** vì sai trên tài sản thật. Reports
không được lặp lại. Đây là nền tảng thực nghiệm của `INV-01`.

### 4.3 Field dùng cho identity matching

```text
DÙNG được làm evidence khớp:
  tracking_code   (khoá node, exact match sau chuẩn hoá đã authorize)
  name            (exact match; là mã người đọc, KHÔNG phải câu tên hàng)
  alt[]           (exact match; danh sách cách viết đã được người duyệt gộp)

KHÔNG được dùng làm authority:
  bất kỳ similarity/edit-distance/token-overlap nào trên câu tên hàng
  bất kỳ suy luận nào từ inv.map mà không có confirmation của người dùng Reports
```

`inv.map` và `alias.map` là bảng do **người của Tracking** duyệt. Chúng là
**evidence rất mạnh**, nhưng phê duyệt của Tracking không phải phê duyệt của
Reports. **D-05:** khi khớp qua `inv.map`/`alias.map`, resolver đưa kết quả
lên **candidate #1** kèm `evidence = TRACKING_ALIAS_MAP` — cần đúng **một**
`confirmation_action`, không auto-resolve.

### 4.4 Schema

```text
E-D  TrackingCatalogSnapshot

capture_id          REQUIRED IMMUTABLE  "TRK-<YYYYMMDDTHHMMSSZ>-<hash8>"
captured_at         REQUIRED IMMUTABLE
captured_by         REQUIRED IMMUTABLE  actor (§12)
source_system_ref   REQUIRED IMMUTABLE  định danh repo/host/nhánh dữ liệu nguồn
content_hash        REQUIRED IMMUTABLE
capture_status      REQUIRED            COMPLETE | FAILED
rows                REQUIRED khi COMPLETE  list<TrackingCatalogRow>
alias_map_rows      REQUIRED khi COMPLETE  list<(old_code, primary_code)>
failure_reason      REQUIRED khi FAILED

TrackingCatalogRow
  tracking_code     REQUIRED IMMUTABLE   khoá node board/<MÃ>
  name              OPTIONAL
  alt               OPTIONAL list<str>
  present_in_board  REQUIRED bool
```

### 4.5 Ngữ nghĩa bắt buộc

```text
INV-11  Snapshot IMMUTABLE. Không ghi đè một capture_id đã tồn tại.
INV-12  capture_status = FAILED  →  LỖI, KHÔNG phải Pending.
        Một lần capture hỏng không được biến thành "sản phẩm không tồn tại".
        Resolver từ chối chạy trên một snapshot FAILED.
INV-13  Sản phẩm bị đổi tên (name/alt đổi, tracking_code giữ nguyên):
        mapping đã confirm VẪN hợp lệ. Tên không phải identity.
INV-14  Sản phẩm biến mất khỏi board hiện tại (present_in_board = false hoặc
        vắng khỏi capture mới):
        (a) mapping lịch sử đã confirm KHÔNG bị vô hiệu hoá, KHÔNG bị xoá;
        (b) report đã ghim capture cũ replay không đổi;
        (c) một identity MỚI gặp lần đầu mà chỉ khớp mã đã biến mất →
            trạng thái MAPPING_STALE → cần confirmation, không auto-resolve.
INV-15  Không dùng catalog HIỆN TẠI để viết lại identity LỊCH SỬ. Cấm
        retroactive remap (DEC-154 §2). Chỉ correction có authority tường
        minh (§13) mới đổi được một mapping đã confirm.
INV-16  Mã bị gộp trong Tracking (alias.map): resolver KHÔNG tự chuyển
        mapping đã confirm sang mã chính. Nó tạo một MAPPING_STALE và đề xuất
        mã chính làm candidate #1 (D-05).
```

**Rủi ro đã biết, ghi lại không giấu.** `DEC-147` §3 R4 xác nhận `phist` và
`board` của Tracking **sửa/xoá được** bởi nhiều tài khoản. Snapshot bất biến
là **cơ chế đối phó**, không phải phủ nhận rủi ro: nó đảm bảo Reports replay
được, nhưng không đảm bảo dữ liệu nguồn tại thời điểm capture là đúng.

---

## 5. E-E — `CanonicalProductIdentity`

```text
E-E  CanonicalProductIdentity   (value object, không có ID riêng)

namespace            REQUIRED IMMUTABLE  enum {TRACKING, PUBLIC_PURCHASE}
source_product_code  REQUIRED IMMUTABLE  mã ổn định TRONG chính namespace đó
```

```text
INV-17  namespace là enum đóng. Thêm giá trị = quyết định Owner + task riêng.
INV-18  TRACKING:X và PUBLIC_PURCHASE:X là HAI identity khác nhau. Không
        collision, không hợp nhất, không so sánh chỉ bằng source_product_code.
INV-19  source_product_code IMMUTABLE trong một mapping record. Sửa mã = tạo
        mapping mới + supersede, không phải UPDATE tại chỗ.
INV-20  normalized key (fold) KHÔNG phải canonical identity — chỉ là aid.
INV-21  display name / product_name KHÔNG phải canonical identity.
INV-22  raw accounting product name (product_raw) KHÔNG phải canonical
        identity và KHÔNG BAO GIỜ bị ghi đè (ADR-102, lớp RAW bất biến).
INV-23  purchase price KHÔNG thuộc identity record (DEC-154 §6).
```

Kết quả resolve là một union type, không phải một string có thể rỗng:

```text
ResolutionOutcome =
    RESOLVED(identity: E-E, provenance: §11)
  | REQUIRES_CONFIRMATION(candidates: list<RankedCandidate>, provenance)
  | PENDING_PRODUCT(reason_code, attempted_sources, provenance)
  | HISTORICAL_CONFIRMED(identity?, price, provenance)   # chỉ pre-cutover, §9
```

```text
INV-24  PENDING_PRODUCT không bao giờ mang namespace hay source_product_code.
INV-25  PENDING_PRODUCT không bao giờ được biểu diễn bằng None/""/0.
        reason_code REQUIRED, attempted_sources REQUIRED (có thể là list rỗng
        chỉ khi resolver chưa được phép chạy — và khi đó reason_code phải nói
        rõ điều đó).
```

`reason_code` — enum đóng:

```text
NO_CANDIDATE_IN_ANY_CATALOG
AMBIGUOUS_MULTIPLE_DETERMINISTIC_CANDIDATES
ONLY_SIMILARITY_EVIDENCE
CANDIDATE_REJECTED_AND_EVIDENCE_UNCHANGED
MAPPING_STALE_TARGET_ABSENT
AWAITING_HUMAN_CONFIRMATION
PENDING_HISTORICAL_CONFIRMATION        (pre-cutover, §9)
```

---

## 6. E-F — `ProductIdentityMapping` (mapping store) và E-G — `AliasMemory`

### 6.1 Một store, hai cách nhìn

**D-06.** `AliasMemory` **không phải** một store thứ hai. Nó là **index tra
cứu trên các bản ghi `ProductIdentityMapping` đang ACTIVE**. Hai store song
song = hai nguồn sự thật = đúng lỗi mà `S021`/`DEC-132` đã phải sửa bằng
architecture repair. Không lặp lại.

### 6.2 Schema

```text
E-F  ProductIdentityMapping

mapping_id             REQUIRED IMMUTABLE  UUID/ULID
source_system          REQUIRED IMMUTABLE  enum; Phase 1 = "REPORTS_SALES"
raw_product_identity   REQUIRED IMMUTABLE  product_raw NGUYÊN VĂN, không sửa
raw_identity_key       REQUIRED IMMUTABLE  DERIVED — §6.3
normalized_matching_aid REQUIRED IMMUTABLE DERIVED — §6.3, chỉ để tìm candidate
namespace              REQUIRED IMMUTABLE  khi status = CONFIRMED
source_product_code    REQUIRED IMMUTABLE  khi status = CONFIRMED
status                 REQUIRED            §6.4
mapping_source         REQUIRED IMMUTABLE  §6.5
resolution_method      REQUIRED IMMUTABLE  §6.6
evidence               REQUIRED IMMUTABLE  §6.7
version                REQUIRED            int, bắt đầu 1, tăng mỗi lần đổi state
supersedes             OPTIONAL IMMUTABLE  mapping_id bị thay thế
superseded_by          OPTIONAL            mapping_id thay thế bản này
pp_version_id          OPTIONAL IMMUTABLE  version Public Purchase lúc quyết định
tracking_capture_id    OPTIONAL IMMUTABLE  capture Tracking lúc quyết định
created_at             REQUIRED IMMUTABLE
created_by             REQUIRED IMMUTABLE  actor (§12)
confirmed_at           REQUIRED khi CONFIRMED, IMMUTABLE
confirmed_by           REQUIRED khi CONFIRMED, IMMUTABLE
audit_event_ids        REQUIRED            list<event_id> (E-K), append-only
```

**Mapping KHÔNG chứa purchase price** (`INV-23`). Không có field giá, không
có field tiền tệ, không có field đơn vị giá.

### 6.3 Hai khoá, hai mục đích khác nhau

```text
raw_identity_key = NFC(product_raw) → collapse whitespace → trim
                   GIỮ NGUYÊN hoa/thường, dấu, dấu câu, mọi model token.
                   Đây là KHOÁ ĐỊNH DANH bền vững.

normalized_matching_aid = fold(product_raw)
                   = raw_identity_key thêm casefold, rồi NFC lại
                     (app/modules/validation/text.py::fold — DEC-145 §2)
                   Đây là AID TÌM CANDIDATE, không phải khoá định danh.
```

**D-07 — Vì sao hai khoá, không phải một.** Chuẩn hoá càng mạnh thì càng dễ
gộp nhầm hai model khác nhau. Tách làm hai cho phép: khoá định danh chỉ mất
thông tin ở mức dạng Unicode và khoảng trắng (an toàn tuyệt đối, không thể
gộp hai model), trong khi vẫn có một aid mạnh hơn để tìm candidate. Nếu chỉ
dùng một khoá, ta buộc phải chọn giữa "bỏ lỡ biến thể hoa/thường" và "gộp
nhầm model" — thiết kế này không phải chọn.

```text
INV-26  raw_identity_key KHÔNG BAO GIỜ bỏ dấu tiếng Việt, không bỏ dấu câu,
        không bỏ/rút gọn model token. Cấm mọi phép chuẩn hoá làm hai model
        chính xác khác nhau trở thành một khoá.
INV-27  Hai identity khác nhau ở đúng một model token phải cho hai
        raw_identity_key khác nhau VÀ hai normalized_matching_aid khác nhau.
        Đây là một assertion bắt buộc (CHECK-105D-06).
```

### 6.4 `status` — enum đóng

```text
CONFIRMED   người đã xác nhận (hoặc auto-resolve theo §6.6), đang có hiệu lực
PENDING     chưa quyết được, đang chờ người xử lý
SUPERSEDED  đã bị một mapping mới thay thế (correction) — GIỮ LẠI, không xoá
CONFLICT    hai confirmation xung đột chưa reconcile (§10)
STALE       target không còn trong catalog hiện tại (INV-14/INV-16)
```

### 6.5 `mapping_source` — enum đóng

```text
HUMAN_CONFIRMATION            người xác nhận trực tiếp (kể cả khi candidate
                              được gợi ý bởi ALIAS_AID_UNIQUE — DEC-156/OR-02;
                              provenance của gợi ý nằm ở
                              evidence.parent_mapping_id, không ở mapping_source)
DETERMINISTIC_CATALOG_MATCH   khớp exact duy nhất trong catalog
OWNER_BOOTSTRAP               nạp từ bảng Owner cung cấp lúc migration (§14)
HISTORICAL_CONFIRMED_REPORT   từ registry lịch sử (§9) — chỉ pre-cutover
```

### 6.6 `resolution_method` và tập được phép auto-resolve

```text
Auto-resolve (0 confirmation_action) — TẬP ĐÓNG, ĐÚNG HAI PHƯƠNG THỨC:
  ALIAS_EXACT           raw_identity_key khớp đúng một mapping CONFIRMED
  CATALOG_EXACT_UNIQUE  raw_identity_key hoặc aid khớp exact đúng MỘT entry
                        catalog (tracking_code | name | alt | PP product_code
                        | PP alias), và chỉ trong MỘT namespace

KHÔNG auto-resolve (>= 1 confirmation_action hoặc PENDING):
  ALIAS_AID_UNIQUE      candidate #1, KHÔNG có production authority  (D-08)
  TRACKING_ALIAS_MAP    khớp qua inv.map/alias.map của Tracking      (D-05)
  SIMILARITY_RANKED     mọi phương thức similarity/model-token       (INV-01)
  CROSS_NAMESPACE_TIE   khớp exact ở CẢ HAI namespace                (INV-29)
  MULTIPLE_EXACT        khớp exact nhiều hơn một entry trong một namespace
```

**D-08 (SỬA THEO OWNER — `DEC-156`, `OR-02` APPROVED WITH CANDIDATE-ONLY
POLICY) — `ALIAS_AID_UNIQUE` là CANDIDATE-ONLY, KHÔNG auto-resolve.**

Bản readiness ban đầu (`DEC-155`) đề xuất cho `ALIAS_AID_UNIQUE` quyền
auto-resolve, lập luận rằng `fold()` là khớp chính xác sau chuẩn hoá đã được
canonical authorize (`DEC-145` §2), không phải similarity. Owner **không**
chấp thuận phần authority đó. Quyết định hiện hành:

```text
ALIAS_AID_UNIQUE
    → chỉ được đưa lên candidate #1
    → candidate đúng  ⇒ tối đa 1 confirmation_action
    → sau confirmation ⇒ persistent confirmed mapping (alias mới, raw_identity_key
                          của chính identity đó, mapping_source =
                          HUMAN_CONFIRMATION, evidence.parent_mapping_id trỏ
                          về alias đã confirm sinh ra candidate)
    → các lần xuất hiện sau ⇒ 0 confirmation_action, qua ALIAS_EXACT
```

Đây là chi phí **một lần cho mỗi biến thể viết**, không phải chi phí lặp lại:
lần đầu tốn đúng một xác nhận, từ lần thứ hai trở đi là 0. Owner chọn đánh
đổi đó thay vì để hệ thống tự tạo một mapping `CONFIRMED` mà không có thao
tác người nào cho chính identity đó.

Quyết định này **không** làm giảm yêu cầu DISTINCT-before-mapping (§1,
`INV-30`, `INV-87`) — một confirmation vẫn áp cho mọi dòng/order cùng
identity — và **không** đổi nguyên tắc fuzzy/similarity-only không có
production authority (`INV-01`, `D-04`).

```text
INV-28  (SỬA — DEC-156) Tập auto-resolve là TẬP ĐÓNG ĐÚNG HAI phương thức:
        ALIAS_EXACT và CATALOG_EXACT_UNIQUE. Thêm phương thức auto-resolve =
        quyết định Owner, không phải quyết định implementation.
INV-28b (MỚI — DEC-156) ALIAS_AID_UNIQUE KHÔNG BAO GIỜ tự sinh một mapping
        CONFIRMED. Nó chỉ sinh candidate. Mapping chỉ tồn tại sau một
        confirmation_action của người dùng.
INV-29  Khớp exact ở CẢ HAI namespace → KHÔNG auto-resolve. Namespace là một
        quyết định nghiệp vụ (hàng này thuộc hệ nào), không suy ra được từ
        việc mã trùng chuỗi (DEC-154 §5).
```

### 6.7 `evidence`

```text
evidence
  matched_on          REQUIRED   enum {RAW_KEY, AID, TRACKING_CODE, TRACKING_NAME,
                                  TRACKING_ALT, TRACKING_ALIAS_MAP,
                                  PP_PRODUCT_CODE, PP_ALIAS, MANUAL_SEARCH}
  matched_value       REQUIRED   giá trị đã khớp, nguyên văn
  candidate_set_ids   REQUIRED   danh sách candidate đã hiển thị lúc quyết định
  ranking_method_id   OPTIONAL   định danh + version của thuật toán xếp hạng
  parent_mapping_id   OPTIONAL   khi DERIVED_FROM_CONFIRMED_ALIAS
```

### 6.8 Invariant của store

```text
INV-30  Với mỗi (source_system, raw_identity_key) có TỐI ĐA MỘT bản ghi
        status = CONFIRMED tại một thời điểm. Đây là khoá đảm bảo idempotency
        và là điều kiện để "một confirmation áp cho mọi dòng cùng identity".
INV-31  Một raw identity KHÔNG được map tới nhiều canonical identity cùng lúc.
        Muốn đổi = correction (supersede), không phải thêm bản ghi thứ hai.
INV-32  Không DELETE. Correction tạo bản ghi mới, bản cũ chuyển SUPERSEDED và
        ở lại vĩnh viễn (ADR-102).
INV-33  Lookup "mapping hiện hành" = bản ghi CONFIRMED duy nhất theo INV-30.
        Nếu tìm thấy nhiều hơn một → lỗi toàn vẹn store, KHÔNG được tự chọn
        một cái (cùng nguyên tắc với AmbiguousSchemeConfigError).
```

---

## 7. E-H — `RejectedCandidate` (bộ nhớ từ chối)

### 7.1 Mục đích

Người dùng đã nói "không phải cái này" một lần thì hệ thống không được hỏi
lại **cùng một câu** — nhưng cũng không được chặn vĩnh viễn khi bằng chứng đã
đổi.

### 7.2 Schema

```text
E-H  RejectedCandidate

rejection_id           REQUIRED IMMUTABLE
source_system          REQUIRED IMMUTABLE
raw_identity_key       REQUIRED IMMUTABLE   khoá alias bị từ chối cho
candidate_namespace    REQUIRED IMMUTABLE
candidate_code         REQUIRED IMMUTABLE
evidence_fingerprint   REQUIRED IMMUTABLE   §7.3
rejected_by            REQUIRED IMMUTABLE   actor (§12)
rejected_at            REQUIRED IMMUTABLE
reason                 OPTIONAL IMMUTABLE   free text
pp_version_id          REQUIRED IMMUTABLE
tracking_capture_id    REQUIRED IMMUTABLE
audit_event_id         REQUIRED IMMUTABLE
```

**D-09.** `reason` là OPTIONAL. Bắt buộc lý do cho mọi lần từ chối sẽ biến
một thao tác đáng lẽ 1 phím thành một form — trực tiếp phá mục tiêu
`<= 1 confirmation_action`. `rejected_by` và `rejected_at` là REQUIRED, đủ để
truy trách nhiệm. (Khác với override tiền tệ ở `ADR-102`, nơi `reason` bắt
buộc — từ chối một candidate không đổi một con số tiền nào.)

### 7.3 `evidence_fingerprint` — cơ chế mở lại

```text
evidence_fingerprint = hash(
    pp_version_id,
    tracking_capture_id,
    sorted(candidate_set_ids),
    ranking_method_id
)
```

```text
INV-34  Một candidate bị suppress khi và chỉ khi tồn tại một RejectedCandidate
        cùng (raw_identity_key, candidate_namespace, candidate_code) VÀ cùng
        evidence_fingerprint.
INV-35  Đổi pp_version_id, tracking_capture_id, tập candidate, hoặc thuật toán
        xếp hạng → fingerprint đổi → candidate ĐƯỢC đề xuất lại, kèm chú thích
        "đã từ chối tại <version cũ>". Rejection KHÔNG BAO GIỜ chặn vĩnh viễn
        bằng chứng mới hợp lệ.
INV-36  Rejection KHÔNG BAO GIỜ tự động biến thành một mapping tới candidate
        khác. Từ chối A không có nghĩa là chấp nhận B.
INV-37  Từ chối TOÀN BỘ candidate của một identity → PENDING_PRODUCT với
        reason_code = CANDIDATE_REJECTED_AND_EVIDENCE_UNCHANGED. Không ép
        người dùng chọn một candidate sai để thoát màn hình.
```

---

## 8. E-I — `CrossSystemProductMapping` (giải HB-154-01)

### 8.1 Khái niệm

```text
TRACKING:<tracking_code>  ↔  PUBLIC_PURCHASE:<public_purchase_code>
```

Đây **không** phải đổi namespace của sản phẩm. Một sản phẩm mang identity
`TRACKING:X` vẫn là `TRACKING:X` sau khi lấy giá từ Public Purchase
(`DEC-154` §7 / `P10`). Mapping này chỉ trả lời **một** câu hỏi: "khi hàng
Tracking này không có giá NCC hợp lệ, tra giá công khai dưới mã nào?"

### 8.2 Schema

```text
E-I  CrossSystemProductMapping

mapping_id             REQUIRED IMMUTABLE
tracking_code          REQUIRED IMMUTABLE
public_purchase_code   REQUIRED IMMUTABLE
status                 REQUIRED   CONFIRMED | SUPERSEDED | CONFLICT
confirmed_by           REQUIRED IMMUTABLE
confirmed_at           REQUIRED IMMUTABLE
reason                 OPTIONAL IMMUTABLE
evidence               REQUIRED IMMUTABLE   như §6.7
version                REQUIRED   int
supersedes             OPTIONAL IMMUTABLE
superseded_by          OPTIONAL
pp_version_id          REQUIRED IMMUTABLE   version PP lúc confirm
tracking_capture_id    REQUIRED IMMUTABLE   capture Tracking lúc confirm
audit_event_ids        REQUIRED   list<event_id>
```

### 8.3 Invariant

```text
INV-38  Mapping phải EXPLICIT. Cấm suy ra chỉ vì tracking_code và
        public_purchase_code giống chuỗi nhau (DEC-154 §5). Kể cả khi bằng
        nhau tuyệt đối, vẫn cần confirmation một lần.
INV-39  Tại một thời điểm, mỗi tracking_code có TỐI ĐA MỘT mapping CONFIRMED,
        và mỗi public_purchase_code có TỐI ĐA MỘT mapping CONFIRMED (1:1).
        Lý do: N:1 làm giá fallback mơ hồ. Muốn N:1 = quyết định Owner riêng.
INV-40  Vi phạm INV-39 khi ghi → status = CONFLICT + lỗi tường minh, KHÔNG
        silent last-write-wins.
INV-41  Correction theo đúng khuôn §13: supersede, không DELETE.
INV-42  Mapping đã confirm được REUSE mà KHÔNG hỏi lại (CHECK-105D-32).
```

### 8.4 Điều kiện tiên quyết của Public Purchase fallback (HB-154-01)

Đây là phần **quy phạm** giải HB-154-01 ở đúng nơi `TASK-105D` có thẩm quyền:

```text
INV-43  Với một identity TRACKING, resolver/price-resolution layer chỉ được
        tra giá Public Purchase khi TẤT CẢ các điều kiện sau đúng:
          (a) không có valid vendor candidate tại sale_date (TASK-105C
              trả absence — DEC-151/152 semantics giữ nguyên);
          (b) TỒN TẠI một CrossSystemProductMapping status = CONFIRMED, active,
              cho đúng tracking_code đó;
          (c) mã Public Purchase dùng để tra là public_purchase_code CỦA CHÍNH
              mapping đó — không phải tracking_code, không phải một biến thể
              chuẩn hoá của nó, không phải một mã suy ra.

INV-44  Thiếu (b)  →  PENDING. TUYỆT ĐỐI không đoán mã Public Purchase.
        Đây là hệ quả trực tiếp của DEC-154 §5 và §7 mục 3 ("… 3. Pending").
INV-45  Fallback thành công KHÔNG đổi namespace của identity (P10). Provenance
        phải giữ PUBLIC_PURCHASE_NO_VENDOR_PRICE để phân biệt với một identity
        PUBLIC_PURCHASE trực tiếp (PUBLIC_PURCHASE_NO_TRACKING) — DEC-154 §10.
```

**Vì sao đây là chỗ đúng để đóng HB-154-01.** Bảng `P01–P10` (`DEC-154` §11)
thuộc integration boundary chưa có implementation owner (§16). Nhưng
`CrossSystemProductMapping` thuộc scope của `TASK-105D`. Bằng cách đặt INV-43/
INV-44 làm invariant **của chính entity đó**, một implementer đọc đúng luật
precedence không còn con đường hợp lệ nào để "luôn fallback": không có mapping
thì không có mã để tra, và việc chế ra mã bị cấm ở tầng entity, không chỉ ở
tầng prose. Việc sửa nguyên văn bảng P được xử lý riêng ở §16.

---

## 9. E-J — `HistoricalConfirmedRegistry` (giải HB-154-03)

### 9.1 Contract

```text
CUTOVER_DATE = 2026-09-01     (DEC-154 §1; phân loại bằng sale_date,
                               KHÔNG dùng import_date)
```

**INV-46 — Quy tắc định tuyến, có thể biến thành test trực tiếp:**

```text
if sale_date < CUTOVER_DATE:
    entry = registry.lookup(order_id, raw_identity_key, sale_date)
    if entry is not None and entry.status == CONFIRMED:
        return HISTORICAL_CONFIRMED(
            identity = entry.confirmed_identity,        # có thể vắng
            price    = entry.confirmed_purchase_price,
            provenance = HISTORICAL_CONFIRMED_REPORT)
        # resolver, catalog và price provider KHÔNG được gọi
    else:
        return PENDING_PRODUCT(
            reason_code = PENDING_HISTORICAL_CONFIRMATION)
        # resolver VẪN KHÔNG được gọi — DEC-154 §2
else:
    → resolver post-cutover (§6), rồi price resolution (§16)
```

```text
INV-47  sale_date < CUTOVER_DATE  →  resolver/catalog/price-provider KHÔNG
        BAO GIỜ được gọi, bất kể registry có entry hay không. Nhánh lịch sử
        chỉ có hai kết cục: HISTORICAL_CONFIRMED hoặc
        PENDING_HISTORICAL_CONFIRMATION.
INV-48  Bản ghi đến muộn (import sau cutover, sale_date trước cutover) đi
        nhánh lịch sử. Phân loại bằng sale_date, không bao giờ import_date.
INV-49  Registry KHÔNG bắt buộc khớp catalog hiện tại. Một entry hợp lệ dù
        mã của nó không còn tồn tại ở đâu (DEC-154 §2).
INV-50  confirmed_identity là OPTIONAL. Một report lịch sử đã xác nhận giá mà
        không xác nhận identity vẫn là authority CHO GIÁ. Vắng identity
        KHÔNG kích hoạt resolver để "điền vào chỗ trống".
```

### 9.2 Schema

```text
E-J  HistoricalConfirmedRegistryEntry

entry_id                 REQUIRED IMMUTABLE
sale_date                REQUIRED IMMUTABLE   phải < CUTOVER_DATE
order_id                 REQUIRED IMMUTABLE
raw_product_identity     REQUIRED IMMUTABLE   product_raw nguyên văn
raw_identity_key         REQUIRED IMMUTABLE   DERIVED (§6.3)
confirmed_identity       OPTIONAL IMMUTABLE   E-E, có thể vắng (INV-50)
confirmed_purchase_price REQUIRED IMMUTABLE   Decimal, đơn vị VND thô (ADR-103)
price_unit_note          OPTIONAL IMMUTABLE
source_report_ref        REQUIRED IMMUTABLE   §9.3
source_row_hash          OPTIONAL IMMUTABLE   RawRow.row_hash nếu có
provenance               REQUIRED IMMUTABLE   = HISTORICAL_CONFIRMED_REPORT
confirmed_by             REQUIRED IMMUTABLE   authority đã xác nhận
confirmed_at             REQUIRED IMMUTABLE
confirmation_authority   REQUIRED IMMUTABLE   OWNER | DELEGATED_<role>
status                   REQUIRED             CONFIRMED | SUPERSEDED
version                  REQUIRED
supersedes / superseded_by  OPTIONAL
audit_event_ids          REQUIRED
```

### 9.3 `source_report_ref` — bằng chứng bất biến

```text
source_report_ref
  report_id       REQUIRED IMMUTABLE   định danh báo cáo lịch sử đã duyệt
  file_name       REQUIRED IMMUTABLE
  sheet_name      OPTIONAL IMMUTABLE
  source_row      OPTIONAL IMMUTABLE   số dòng 1-based
  content_hash    REQUIRED IMMUTABLE   hash của file bằng chứng
```

```text
INV-51  source_report_ref IMMUTABLE và phải trỏ tới một bằng chứng có thể mở
        lại được. Không chấp nhận "chủ dự án đã xác nhận" dưới dạng prose
        không có artifact (EVIDENCE_STANDARD — cấm bịa evidence).
INV-52  Khoá tra cứu = (order_id, raw_identity_key, sale_date). Một entry áp
        cho MỌI dòng của cùng order + cùng identity — nhất quán với nguyên
        tắc DISTINCT (§6, INV-30).
INV-53  Correction một entry = supersede (§13), không DELETE, không sửa
        confirmed_purchase_price tại chỗ.
INV-54  Registry KHÔNG BAO GIỜ được bootstrap bằng cách suy ra từ catalog hay
        giá hiện tại. Nhập từ báo cáo Owner-confirmed thật, hoặc để trống
        (§14).
```

---

## 10. E-L — `ResolutionBinding`, version & concurrency contract

### 10.1 `ResolutionBinding` — cái mà một report ghim

```text
E-L  ResolutionBinding

binding_id             REQUIRED IMMUTABLE
report_run_id          REQUIRED IMMUTABLE
pp_version_id          REQUIRED IMMUTABLE
tracking_capture_id    REQUIRED IMMUTABLE
mapping_store_revision REQUIRED IMMUTABLE   §10.2
registry_revision      REQUIRED IMMUTABLE
bound_at               REQUIRED IMMUTABLE
bound_by               REQUIRED IMMUTABLE
```

```text
INV-55  Ghim CẢ BỐN revision, không ghim từng phần. Ghim giá mà không ghim
        catalog là đúng lỗ hổng replay HB-154-02 nêu.
INV-56  Replay một report = đọc lại đúng bộ binding của nó. Kết quả PHẢI
        giống hệt lần chạy đầu, bất kể store/catalog/giá đã đổi thế nào sau đó.
INV-57  Thiếu bất kỳ thành phần nào của binding → lỗi cứng, KHÔNG fallback
        sang "mới nhất", KHÔNG Pending (xem §3.3 câu 9).
```

### 10.2 `mapping_store_revision`

Store là append-only (§11). `mapping_store_revision` = số thứ tự của event
cuối cùng trong log tại thời điểm bind (monotonic, không tái sử dụng). Đọc
"trạng thái tại revision R" = replay log tới event R. Đây là lý do append-only
được chọn: nó cho **point-in-time read** miễn phí, không cần bảng lịch sử
riêng.

### 10.3 Optimistic concurrency (§16 của brief)

Tình huống bắt buộc phải xử lý đúng:

```text
User A:  raw product X → TRACKING:A
User B (cùng lúc):  raw product X → TRACKING:B
```

```text
INV-58  Mọi command làm đổi state mang expected_version (version hiện tại của
        aggregate mà client đã đọc).
INV-59  expected_version != version hiện tại  →  từ chối với
        MappingVersionConflict(current_state), KHÔNG ghi gì.
        TUYỆT ĐỐI KHÔNG last-write-wins im lặng.
INV-60  Client nhận conflict phải reload và reconcile. Không có cơ chế
        auto-merge, không có "force write" trong Phase 1.
INV-61  Aggregate boundary = (source_system, raw_identity_key) cho E-F;
        = tracking_code cho E-I; = entry_id cho E-J. Concurrency được kiểm
        soát tại đúng biên đó, không phải toàn store.
```

Command shape quy phạm:

```text
ConfirmMappingCommand
  source_system, raw_identity_key      REQUIRED
  target: E-E                          REQUIRED
  expected_version: int                REQUIRED   (0 = "tôi tin chưa có bản ghi")
  actor: actor_id                      REQUIRED
  client_request_id: str               REQUIRED   §11.2
  evidence: §6.7                       REQUIRED
  reason: str                          OPTIONAL
```

---

## 11. Persistence, atomicity và idempotency

### 11.1 Chọn cơ chế (Ready Gate: "persistence mechanism được chọn")

**D-10 — Interface trước, cơ chế sau.** Domain định nghĩa Protocol:

```text
ProductIdentityStore (Protocol — thuần, không I/O trong signature)
  read_active_mapping(source_system, raw_identity_key) -> E-F | None
  read_at_revision(revision) -> StoreView
  append(command) -> AppendResult(new_version, revision, outcome)
  current_revision() -> int
```

`app/modules/` chỉ phụ thuộc Protocol này (đúng tiền lệ `PriceProvider` /
`DEC-103`, và `ADR-101` "Phase 2 chuyển vào DB nhưng giữ nguyên interface").

**D-11 — Cơ chế Phase 1: append-only JSONL event log + index dẫn xuất.**

| Phương án | Đánh giá |
|---|---|
| **JSONL append-only + index (CHỌN)** | Không thêm dependency (stdlib `json`); `app/modules/` giữ nguyên "thư viện Python thuần" mà `ADR-101` bắt kiểm chứng bằng test tĩnh; append-only là yêu cầu gốc của `ADR-102`, không phải thứ phải mô phỏng; point-in-time read miễn phí (§10.2); diff/backup/export bằng công cụ text thường. |
| SQLite | Đúng cho Phase 2 và `ADR-101` đã nêu tên, nhưng ở Phase 1 kéo mô hình quan hệ + migration tool vào một giai đoạn mà `ADR-101` cố ý giữ không-DB. Append-only vẫn phải tự thi hành bằng quy ước. |
| YAML một file | Rewrite toàn file mỗi lần ghi — mất append-only, mất point-in-time, dễ hỏng khi ghi dở. Loại. |
| Ghi thẳng từ UI | Vi phạm `01_PROJECT_ARCHITECTURE_RULES` §3 và `ADR-102` ("mọi ghi do người dùng kích hoạt phải đi qua audit service"). Loại tuyệt đối. |

**Hạn chế phải ghi rõ, không giấu:** JSONL + khoá file cho concurrency **một
máy**. Nhiều người dùng đồng thời trên nhiều máy là bài toán Phase 2 và cần
DB. Contract concurrency ở §10.3 được viết để **cùng một bộ test** chạy đúng
trên cả hai cơ chế — đó là mục đích của việc tách Protocol.

### 11.2 Yêu cầu persistence bắt buộc

```text
INV-62  Atomic write. Append một event = một lần ghi + fsync. Index dẫn xuất
        ghi theo khuôn write-temp + os.replace (đổi tên nguyên tử). Một lần
        ghi bị ngắt KHÔNG được để lại state đọc được nhưng sai.
INV-63  Index là DERIVED. Mất/hỏng index → dựng lại được từ log. Log là nguồn
        sự thật duy nhất. Log và index bất đồng → log thắng.
INV-64  Deterministic read. Cùng revision → cùng kết quả, mọi lúc, mọi máy.
INV-65  Backup/export. Toàn bộ store export được ra một artifact tự mô tả
        (log + manifest + hash) và import lại cho ra store tương đương bit.
INV-66  KHÔNG có đường ghi nào bỏ qua domain contract. Không UI, không script,
        không notebook ghi thẳng vào file store.
INV-67  KHÔNG DELETE. Không có thao tác xoá trong bất kỳ interface nào.
```

### 11.3 Idempotency (§15 của brief)

Hai lớp, cần cả hai:

```text
LỚP 1 — Command-level (chống retry)
  client_request_id REQUIRED trên mọi command làm đổi state.
  INV-68  Cùng client_request_id đã xử lý → trả lại KẾT QUẢ CŨ, không ghi
          event mới. outcome = ALREADY_APPLIED.

LỚP 2 — State-level (chống import trùng)
  INV-69  Một command mà state kết quả BẰNG state hiện tại → no-op,
          outcome = NO_CHANGE, không ghi event, không tăng version.
  INV-70  Import lại cùng một file sales:
            - tập DISTINCT identity giống hệt;
            - mọi identity đã CONFIRMED resolve qua ALIAS_EXACT;
            - 0 mapping mới, 0 rejection mới, 0 audit event mới;
            - current_revision() KHÔNG đổi.
          Đây là assertion trực tiếp cho CHECK-105D-19.
```

**Phân biệt retry và correction — quy phạm:**

```text
retry          : cùng client_request_id            → ALREADY_APPLIED (không event mới)
no-op          : client_request_id mới, state không đổi → NO_CHANGE (không event mới)
correction thật: client_request_id mới, target khác, expected_version = version
                 hiện tại → APPLIED (supersede + audit event + version+1)
conflict       : client_request_id mới, expected_version cũ → CONFLICT (không ghi)
```

```text
INV-71  Retry sau lỗi KHÔNG được áp mapping hai lần và KHÔNG được làm tăng
        affected_count trong audit (số dòng bị tác động tính lại từ dữ liệu,
        không cộng dồn).
```

---

## 12. Permission và authority boundary

`DEC-124`: MVP có đúng một role `ADMIN`. Thiết kế này **đặc tả quyền ở tầng
domain** và **không implement auth** (ngoài scope).

```text
Năm mức authority, KHÔNG được gộp:

1. MACHINE_SUGGESTION      xếp hạng/đề xuất candidate. Không đổi state.
                           Không cần quyền. Không bao giờ là authority.
2. HUMAN_CONFIRMATION      chấp nhận/từ chối một candidate cho một identity.
3. AUTHORIZED_CORRECTION   sửa một mapping đã CONFIRMED (supersede).
4. CATALOG_PUBLICATION     publish PublicPurchaseSourceVersion; chạy capture
                           Tracking.
5. PRICE_PUBLICATION       publish price projection (đi kèm mức 4 do D-01,
                           nhưng vẫn là một quyền riêng trong schema).
```

Permission enum quy phạm:

```text
PRODUCT_MAPPING_CONFIRM
PRODUCT_MAPPING_CORRECT
CROSS_SYSTEM_MAPPING_CONFIRM
HISTORICAL_REGISTRY_CONFIRM
PUBLIC_PURCHASE_SOURCE_PUBLISH
TRACKING_CATALOG_CAPTURE
REPORT_REPIN
```

Phase 1: cả bảy gán cho `ADMIN`. Schema tách riêng để Phase 2 phân quyền
được mà không phải migrate dữ liệu.

### 12.1 Actor ở Phase 1 — một hạn chế thật, không được che

Phase 1 là thư viện Python thuần chạy bằng CLI (`ADR-101`) — **chưa có
authentication**. Nhưng `ADR-102` bắt buộc `ChangedBy` trên mọi thay đổi do
người kích hoạt.

**D-12 — Operator-attested actor.** Mọi command làm đổi state **BẮT BUỘC**
mang `actor_id` do người vận hành khai báo tường minh. Không có mặc định,
không có `"system"`, không có anonymous. Command thiếu `actor_id` bị từ chối.

```text
INV-72  actor_id REQUIRED trên mọi command đổi state. Không có giá trị mặc định.
INV-73  actor_id ở Phase 1 là KHAI BÁO CỦA NGƯỜI VẬN HÀNH, KHÔNG PHẢI DANH
        TÍNH ĐÃ XÁC THỰC. Mọi artifact hiển thị nó phải nói rõ điều đó.
        Cấm gọi nó là "authenticated user".
```

**OR-03 — `APPROVED FOR PHASE 1` (Owner, `DEC-156`, 2026-08-28).** Chủ dự án
chấp thuận actor do người vận hành khai báo ở Phase 1, với ba ràng buộc giữ
nguyên hiệu lực: `actor` là **REQUIRED**; **cấm** gọi nó là authenticated
identity/user; **cấm** default actor im lặng (`INV-72`, `INV-73`).

Authentication thật **không** phải blocker của implementation Phase 1
`TASK-105D`, nhưng phải được ghi nhận đúng là **future hardening /
capability boundary**:

```text
CAPABILITY BOUNDARY — PHASE 1 ACTOR
  Cái audit trail Phase 1 chứng minh được : "bản ghi này khai actor X"
  Cái nó KHÔNG chứng minh được            : "người thật sự thao tác là X"
  Nâng cấp                                : authentication Phase 2 (ADR-101/
                                            ADR-105), khi đó actor_id chuyển
                                            từ khai báo sang danh tính đã xác
                                            thực mà KHÔNG đổi schema E-K
  Điều cấm ngay từ bây giờ                : mọi artifact/UI/báo cáo mô tả
                                            actor Phase 1 là "authenticated"
```

Đây **không còn** là blocker của Ready Gate.

---

## 13. Correction và Audit

### 13.1 `MappingAuditEvent` (E-K)

```text
E-K  MappingAuditEvent          append-only, không sửa, không xoá

event_id             REQUIRED IMMUTABLE
revision             REQUIRED IMMUTABLE   số thứ tự đơn điệu trong log
event_type           REQUIRED IMMUTABLE   §13.2
aggregate_type       REQUIRED IMMUTABLE   PRODUCT_IDENTITY_MAPPING |
                                          CROSS_SYSTEM_MAPPING |
                                          REJECTED_CANDIDATE |
                                          HISTORICAL_REGISTRY_ENTRY
aggregate_id         REQUIRED IMMUTABLE
actor_id             REQUIRED IMMUTABLE
occurred_at          REQUIRED IMMUTABLE
reason               OPTIONAL IMMUTABLE   REQUIRED cho CORRECT_* (§13.2)
old_value            REQUIRED IMMUTABLE   null cho event tạo mới
new_value            REQUIRED IMMUTABLE
affected_scope       REQUIRED IMMUTABLE   §13.3
pp_version_id        REQUIRED IMMUTABLE
tracking_capture_id  REQUIRED IMMUTABLE
client_request_id    REQUIRED IMMUTABLE
resulting_version    REQUIRED IMMUTABLE
```

### 13.2 `event_type` — enum đóng

```text
CONFIRM_MAPPING            CORRECT_MAPPING            (reason REQUIRED)
REJECT_CANDIDATE           SET_PENDING
CONFIRM_CROSS_SYSTEM       CORRECT_CROSS_SYSTEM       (reason REQUIRED)
CONFIRM_HISTORICAL_ENTRY   CORRECT_HISTORICAL_ENTRY   (reason REQUIRED)
BOOTSTRAP_MAPPING          MARK_STALE
REPIN_REPORT               (reason REQUIRED)
```

**D-13.** `reason` bắt buộc cho mọi `CORRECT_*` và `REPIN_REPORT` (sửa một
sự thật đã xác nhận — đúng tinh thần `ADR-102` bắt buộc `reason` cho override
tiền tệ), OPTIONAL cho confirm/reject lần đầu (giữ mục tiêu
`<= 1 confirmation_action`).

### 13.3 Correction giữ nguyên lịch sử

```text
INV-74  Correction = old mapping → SUPERSEDED (ở lại vĩnh viễn) + new mapping
        CONFIRMED + một CORRECT_* event nối hai bản ghi. KHÔNG DELETE, KHÔNG
        UPDATE tại chỗ.
INV-75  Audit phải trả lời được, chỉ từ log: ai sửa, lúc nào, TỪ GÌ, SANG GÌ,
        lý do, phạm vi bị tác động, và replay của report đã ghim thay đổi ra sao.
INV-76  affected_scope = { distinct_identity_count, affected_order_ids,
        affected_line_count, computed_at_revision }. Tính lại từ dữ liệu tại
        revision đó, KHÔNG cộng dồn qua các lần retry (INV-71).
INV-77  Correction tác động resolution TƯƠNG LAI kể từ revision của nó.
        Nó KHÔNG tự động viết lại một report đã ghim ResolutionBinding.
INV-78  Muốn một report đã phát hành phản ánh correction: phải có một
        REPIN_REPORT tường minh, có quyền REPORT_REPIN, có reason, được audit.
        KHÔNG có re-pin ngầm, KHÔNG có "tự cập nhật khi mở lại".
```

`INV-77`/`INV-78` là hiện thân trực tiếp của `DEC-121` (chính sách đổi trong
tương lai không được viết lại một báo cáo đã phát hành).

---

## 14. Migration và Rollback

### 14.1 Các bước

```text
M0  TRẠNG THÁI KHỞI ĐẦU
    - mapping store rỗng, log rỗng, revision = 0;
    - feature flag PRODUCT_IDENTITY_RESOLVER = OFF;
    - app/pipeline.py giữ nguyên PendingPriceProvider làm default
      (TASK-105 CHECK-105-04 — KHÔNG đổi);
    - 0 file production thay đổi cho tới khi implementation được cấp phép.

M1  BOOTSTRAP MAPPING DO OWNER CUNG CẤP  (nếu Owner có bảng)
    - nạp qua BOOTSTRAP_MAPPING event, mapping_source = OWNER_BOOTSTRAP;
    - mỗi dòng có source_report_ref/evidence trỏ về bảng gốc;
    - KHÔNG có bảng thì bỏ qua M1 — TUYỆT ĐỐI KHÔNG tự chế mapping (§14.3).

M2  BOOTSTRAP HISTORICAL CONFIRMED REGISTRY
    - chỉ từ báo cáo lịch sử Owner-confirmed thật, có content_hash;
    - không có → registry rỗng → mọi dòng pre-cutover là
      PENDING_HISTORICAL_CONFIRMATION (đúng INV-46, không phải lỗi).

M3  PUBLIC PURCHASE VERSION ĐẦU TIÊN
    - Owner publish PP-<YYYYMMDD>-01 với CẢ HAI projection;
    - chạy toàn bộ validation §3.4; publish fail = không có version, không
      có version một nửa.

M4  TRACKING CAPTURE ĐẦU TIÊN
    - tools/ chạy capture read-only → snapshot bất biến;
    - capture FAILED → dừng, không tạo snapshot rỗng (INV-12).

M5  KÍCH HOẠT
    - chỉ sau khi M3 + M4 xong và Completion Gate đã frozen + PASS;
    - bật flag; PendingPriceProvider vẫn là fallback cho mọi thứ chưa resolve.
```

### 14.2 Rollback

```text
INV-79  Rollback = tắt feature flag. Pipeline quay về hành vi hiện tại
        (PendingPriceProvider default). KHÔNG xoá dữ liệu store.
INV-80  Migration KHÔNG PHÁ HUỶ. Không bước nào DELETE/TRUNCATE/overwrite.
        Rollback không mất một confirmation nào của người dùng.
INV-81  Rollback của một PublicPurchaseSourceVersion = publish version mới với
        rollback_of, KHÔNG sửa/xoá version cũ (§3.3 câu 10).
INV-82  Report đã ghim binding cũ replay không đổi sau rollback.
```

### 14.3 Điều tuyệt đối cấm khi migration

```text
- Tự suy ra mapping sản phẩm thật từ tên hàng.
- Tạo fake production dataset / fake Tracking product.
- Dùng catalog hoặc giá HIỆN TẠI để backfill lịch sử.
- Coi "store rỗng" là lỗi cần vá bằng dữ liệu bịa. Store rỗng là trạng thái
  khởi đầu ĐÚNG; Pending là kết quả ĐÚNG (DEC-103).
```

---

## 15. Metrics vận hành

Mẫu số chung cho bốn metric đầu, định nghĩa một lần:

```text
D  = số DISTINCT identity trong một import batch, SAU khi loại nhánh
     pre-cutover (INV-46). Distinct theo (source_system, raw_identity_key).
```

```text
AUTO_RESOLUTION_RATE
    = |{ identity ∈ D : resolution_method ∈ tập auto-resolve §6.6 }| / |D|

MANUAL_CONFIRMATION_RATE
    = |{ identity ∈ D : cần >= 1 confirmation_action }| / |D|

PENDING_RATE
    = |{ identity ∈ D : outcome = PENDING_PRODUCT }| / |D|

REUSE_RATE
    = |{ identity ∈ D : resolution_method = ALIAS_EXACT }| / |D|
    (SỬA — DEC-156/OR-02: ALIAS_AID_UNIQUE không còn là reuse tự động; nó là
     một candidate cần confirmation, nên thuộc MANUAL_CONFIRMATION_RATE ở lần
     đầu và chuyển sang ALIAS_EXACT — tức REUSE_RATE — từ lần thứ hai)

WRONG_MAPPING_CORRECTION_RATE
    = số CORRECT_MAPPING event trong cửa sổ thời gian W
      / số mapping CONFIRMED đang active tại đầu W
    (cửa sổ phải ghi rõ; đây KHÔNG dùng mẫu số D)

MANUAL_CONFIRMATION_ACTIONS_PER_100_ORDERS
    = 100 * (số confirmation_action trong batch) / (số DISTINCT order trong batch)
```

```text
INV-83  AUTO_RESOLUTION_RATE + MANUAL_CONFIRMATION_RATE + PENDING_RATE = 1
        trên cùng mẫu số D. Ba tập rời nhau và phủ kín D.
INV-84  Mọi metric mang mapping_store_revision, pp_version_id,
        tracking_capture_id — số liệu không so sánh được qua version khác nhau
        nếu không ghi kèm.
INV-85  Metric là READ-ONLY. Không metric nào được là input của bất kỳ quyết
        định resolution nào. Cấm mọi vòng phản hồi kiểu "hạ ngưỡng để tăng
        AUTO_RESOLUTION_RATE".
INV-86  Metric KHÔNG log dữ liệu cá nhân khách hàng (tên, SĐT, địa chỉ, IMEI)
        — governance/product/17_DATA_GOVERNANCE_PRIVACY.md.
```

Ghi chú đổi tên: `TASK-105D` và `DEC-154` §17 gọi metric cuối là
`MANUAL_ACTIONS_PER_100_ORDERS`. Tên chuẩn từ nay là
`MANUAL_CONFIRMATION_ACTIONS_PER_100_ORDERS` — chữ "CONFIRMATION" là cần
thiết vì `confirmation_action` (§17.1) cố ý KHÔNG đếm thao tác điều hướng.
Cùng một metric, tên chính xác hơn.

---

## 16. Ranh giới sở hữu P00–P11 (Price Resolution)

Phiên này **không** implement price resolution và **không** tự nhận ownership.

### 16.1 Ai sở hữu cái gì

```text
TASK-105D  identity resolution + E-F/E-G/E-H/E-I/E-J/E-K/E-L
           → trả CanonicalProductIdentity | PENDING_PRODUCT | HISTORICAL_CONFIRMED
TASK-105C  TRACKING: HistoricalVendorMin | absence     (DEC-151/152 giữ nguyên)
TASK-105B  PUBLIC_PURCHASE: PublicPurchasePrice | absence
CHƯA CÓ CHỦ  lớp composition P00–P11 → KpiPurchasePrice
```

### 16.2 Sửa transcription cho bảng P (HB-154-01, HB-154-03)

Ba dòng dưới đây **không thêm ngữ nghĩa mới**. Chúng chép lại đúng những gì
`DEC-154` §2 và §7 (prose) đã nói vào bảng quy phạm `P01–P10`, nơi transcription
ban đầu bị thiếu. Đây chính là "divergence phải được báo cáo và sửa bằng
authority hợp lệ" của V4.1 §11.

```text
P00 (MỚI — chép từ DEC-154 §2)
    sale_date < CUTOVER_DATE + entry HistoricalConfirmedRegistry CONFIRMED
    → HISTORICAL_CONFIRMED_REPORT, bypass toàn bộ P01–P11.
    sale_date < CUTOVER_DATE mà KHÔNG có entry → PENDING_HISTORICAL_CONFIRMATION.
    P01–P11 CHỈ áp dụng cho sale_date >= CUTOVER_DATE.

P03 (SỬA — khôi phục điều kiện (b) của DEC-154 §7)
    CŨ : TRACKING + no valid vendor candidates → Public Purchase fallback
    MỚI: TRACKING + no valid vendor candidates + CrossSystemProductMapping
         CONFIRMED active → Public Purchase fallback, tra bằng
         public_purchase_code CỦA mapping đó

P11 (MỚI — chép từ DEC-154 §7 mục "3. Pending")
    TRACKING + no valid vendor candidates + KHÔNG có CrossSystemProductMapping
    → Pending. TUYỆT ĐỐI không đoán mã Public Purchase.
```

Ba dòng này đã được áp dụng vào bảng P ở `PROJECT/PROJECT_DECISIONS.md`
(`DEC-154` §11) và `docs/tasks/TASK-108B-eligible-costs-owner-definition.md`
§99, có đánh dấu inline nguồn transcription. Chúng **chưa** phải executable
gate — việc biến P00–P11 thành gate thuộc về chủ sở hữu composition.

### 16.3 Đề xuất chủ sở hữu

```text
ROADMAP CHANGE PROPOSAL

Lý do:
Lớp composition P00–P11 không có task ID, không có scope lock, không có
Completion Gate và không có review budget lineage. DEC-154 §11 công bố khoảng
trống này tường minh và cấm phiên reconciliation tự lấp.

Task bị ảnh hưởng:
TASK-105B, TASK-105C, TASK-105D, TASK-108B.

Tác động đến dependency:
TASK-108B không thể DONE khi composition chưa có chủ. Đây là blocker thứ 4
trong danh sách blocker hiện tại của TASK-108B.

Risk:
HIGH — cùng failure path giá/KPI/lương.

Đề xuất thay đổi:
Cấp một task mới nhận ownership P00–P11 (ID đề xuất: TASK-105E — Price
Resolution Composition; đã kiểm tra TASK-105E chưa bị chiếm ở bất kỳ đâu
trong repo). Task đó biến P00–P11 thành Completion Gate thực thi được, mở
lineage review budget riêng, và là nơi duy nhất được wire provider vào
pipeline.

Required decision:
OWNER — cấp task ID và authority. Phiên readiness này KHÔNG tự cấp
(DEC-154 §11 cấm tường minh).

**Kết quả: GRANTED (Owner, `DEC-156`, 2026-08-28).** Task ID `TASK-105E —
Price Resolution Composition` đã được Owner cấp. Canonical spec:
`docs/tasks/TASK-105E-price-resolution-composition.md`, trạng thái `PLANNED`,
chưa freeze, chưa implement. `TASK-105E` là lớp orchestration/composition:
nó **không** resolve identity, **không** thay `TASK-105B`/`105C`/`105D`,
**không** tự invent mapping hay giá, **không** mutate Tracking.
```

---

## 17. Định nghĩa vận hành cho Completion Gate (giải HB-154-05)

### 17.1 `confirmation_action` — định nghĩa quy phạm

```text
confirmation_action =
    một COMMAND ở tầng domain, do người dùng phát ra, làm thay đổi trạng thái
    persistent của mapping store cho MỘT distinct identity.

Đếm ĐÚNG bốn loại command:
    CONFIRM_MAPPING
    REJECT_CANDIDATE
    CONFIRM_CROSS_SYSTEM
    SET_PENDING

KHÔNG đếm (bằng 0 confirmation_action):
    điều hướng, cuộn, chuyển focus, mở/đóng panel, xem evidence, tìm kiếm,
    lọc, sắp xếp, mở màn hình, đóng màn hình, phím tắt điều hướng.
```

**D-14 — Vì sao đếm command chứ không đếm phím/click.** Đếm keystroke/click
biến một gate nghiệp vụ thành một gate của framework UI: cùng một hành động
nghiệp vụ sẽ "đạt" hay "trượt" tuỳ bàn phím hay chuột, tuỳ thư viện. Đếm
domain command đo đúng thứ nghiệp vụ quan tâm — **số lần con người phải quyết
định** — và test được mà không cần dựng UI. Yêu cầu keyboard-first vẫn giữ
nguyên, nhưng nó là `CHECK-105D-22`, một gate riêng, không trộn vào G23/G24.

```text
INV-87  Một confirmation_action áp cho MỌI dòng/order chia sẻ cùng distinct
        identity. Đây là hệ quả của INV-30 và là nội dung của CHECK-105D-11.
```

### 17.2 `AMBIGUOUS` — định nghĩa vận hành (cho G06)

```text
Một identity là AMBIGUOUS khi và chỉ khi resolution_method của nó KHÔNG
thuộc tập auto-resolve đóng ở §6.6.

Bốn nguồn cần confirmation, mỗi nguồn là một fixture test bắt buộc:
  (a) MULTIPLE_EXACT      — nhiều hơn một entry catalog khớp exact trong một
                            namespace;
  (b) CROSS_NAMESPACE_TIE — khớp exact ở CẢ HAI namespace (INV-29);
  (c) ONLY_SIMILARITY     — chỉ có evidence similarity/model-token (INV-01);
  (d) ALIAS_AID_UNIQUE    — khớp aid duy nhất với một alias đã confirm
                            (DEC-156/OR-02 — candidate-only, INV-28b).

Assertion cho G06:
  Với một catalog chứa hai entry chỉ khác nhau ở đúng MỘT model token, và một
  raw identity chứa token thứ ba: outcome PHẢI là REQUIRES_CONFIRMATION hoặc
  PENDING_PRODUCT, và resolution_method PHẢI KHÔNG thuộc tập auto-resolve.
  Không có "im lặng chọn cái gần nhất".
```

### 17.3 `PENDING_PRODUCT được hỗ trợ rõ ràng` (cho G13)

Thay phát biểu định tính bằng bốn assertion:

```text
G13-a  ResolutionOutcome có một biến thể PENDING_PRODUCT riêng biệt về kiểu,
       không phải None/""/0 (INV-25).
G13-b  PENDING_PRODUCT mang reason_code thuộc enum đóng §5 và
       attempted_sources không rỗng khi resolver đã chạy.
G13-c  PENDING_PRODUCT KHÔNG mang namespace hay source_product_code (INV-24).
G13-d  Một identity PENDING KHÔNG chặn việc resolve các identity khác trong
       cùng batch; batch hoàn tất với một tập kết quả hỗn hợp.
```

### 17.4 G23 / G24

```text
G24 (known mapping = 0 normal action)
    Setup : store có một mapping CONFIRMED cho raw_identity_key K.
    Act   : resolve một batch chứa N dòng có identity K (N >= 2).
    Assert: count(confirmation_action cho K) == 0
            resolution_method == ALIAS_EXACT
            current_revision() không đổi   (INV-70)

G23 (candidate #1 đúng → <= 1 normal action)
    Setup : identity AMBIGUOUS theo §17.2, candidate xếp hạng 1 là đáp án đúng.
    Act   : chấp nhận candidate #1.
    Assert: count(confirmation_action) == 1
            mọi dòng cùng identity đó được resolve bởi đúng một action (INV-87)
            lần chạy sau trên cùng identity: count == 0 (chuyển sang G24)

    Fixture BẮT BUỘC bổ sung (DEC-156/OR-02): trường hợp ALIAS_AID_UNIQUE —
    một raw identity chỉ khác một alias đã confirm ở hoa/thường hoặc khoảng
    trắng. Assert: KHÔNG auto-resolve (INV-28b); nó xuất hiện đúng ở
    candidate #1; chấp nhận tốn đúng 1 confirmation_action; lần xuất hiện
    thứ hai của CHÍNH biến thể đó tốn 0 và đi qua ALIAS_EXACT.
```

### 17.5 Hệ quả với bảng Completion Gate

`CHECK-105D-06`, `-13`, `-23`, `-24` được viết lại trong
`docs/tasks/TASK-105D-product-identity-resolver.md` để trỏ tới đúng các định
nghĩa trên. Gate vẫn ở trạng thái **DRAFT** — phiên này **không** freeze
(V4.1 §12: `FROZEN` chỉ thuộc một phiên Freeze Finalization có thẩm quyền).

---

## 18. Ánh xạ finding → nơi giải

| Finding | Xử lý trong phiên này | Vị trí |
|---|---|---|
| HB-154-01 | RESOLVED (invariant) + transcription bảng P | §8.4 (INV-43/44/45), §16.2 |
| HB-154-02 | RESOLVED | §3 (D-01/D-02, INV-06), §10.1 (INV-55/56) |
| HB-154-03 | RESOLVED (contract test được) | §9 (INV-46/47/48), §16.2 (P00) |
| HB-154-04 | **CLOSED** — Owner chọn Option B tại `DEC-156`; lineage `TASK-105C` được reconcile | `DEC-156` §4, `PROJECT/REVIEW_BUDGET_LEDGER.md` |
| HB-154-05 | RESOLVED (định nghĩa vận hành) | §17 |
| HB-154-06 | RESOLVED (bổ sung Impact) | `DEC-154` Impact |
| HB-154-07 | RESOLVED (marker inline, giữ nguyên văn lịch sử) | PROGRESS, TASK-108B |
| OS-154-01 | KHÔNG xử lý (out of scope, pre-existing) | — |

---

## 19. Điều phiên này KHÔNG làm

```text
- Không sửa app/**, tests/**, config/**, Golden fixture/expected.
- Không implement TASK-105C, TASK-105D, hay lớp composition.
- Không activate FilePriceProvider; không thay PendingPriceProvider.
- Không sửa repo Tracking; không tạo mapping production thật.
- Không suy diễn một mapping sản phẩm thật nào.
- Không freeze Completion Gate.
- Không merge vào nhánh mặc định.
- Không mở Repair Cycle; không tiêu review budget.
- Không tự đánh TASK-105D là READY hay DONE.
```

---

## 20. Tham chiếu

- `PROJECT/PROJECT_DECISIONS.md` — `DEC-103`, `DEC-121`, `DEC-124`, `DEC-145`,
  `DEC-147`, `DEC-148`, `DEC-151`, `DEC-152`, `DEC-153`, `DEC-154`, `DEC-155`.
- `docs/tasks/TASK-105D-product-identity-resolver.md` — task spec + Completion Gate.
- `docs/tasks/TASK-105C-historical-vendor-price-provider.md` — nhánh Tracking.
- `docs/tasks/TASK-105B-file-price-provider.md` — nhánh Public Purchase.
- `docs/tasks/TASK-108B-eligible-costs-owner-definition.md` §XII — downstream.
- Independent review artifact — nguồn của HB-154-01…07. **Không nằm trên
  nhánh này**: nó sống ở commit `61a90b4fc1d8fc281927536f4e0c32ba6ef703dd`
  trên nhánh `review/product-identity-price-resolution-reconciliation`, tại
  đường dẫn docs/reviews/DEC-154-PRODUCT-IDENTITY-PRICE-RESOLUTION-INDEPENDENT-REVIEW.md
  (viết không backtick vì đây là tham chiếu liên-nhánh, không phải một file
  phân giải được trong cây làm việc hiện tại). Đọc bằng
  `git show 61a90b4f:<đường dẫn trên>`.
- `docs/adr/ADR-101`, `ADR-102`, `ADR-103`, `ADR-105`.
- `governance/core/V4_1_POLICY_FREEZE.md` §2/§3/§4/§10/§11/§12.
- `governance/core/EVIDENCE_STANDARD.md`, `governance/core/03_DATA_MODEL_RULES.md`,
  `governance/core/01_PROJECT_ARCHITECTURE_RULES.md`.
