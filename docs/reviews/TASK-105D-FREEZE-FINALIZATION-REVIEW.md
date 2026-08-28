# TASK-105D — FREEZE FINALIZATION REVIEW (Independent)

Artifact Type:
INDEPENDENT FREEZE FINALIZATION REVIEW — Completion Gate của `TASK-105D`.
Đây là **review evidence**, không phải Owner Decision và không phải
implementation.

Session:
`docs/sessions/S036-task-105d-freeze-finalization.md`

Reviewed base SHA:
`9cd871488a6baebf6b80737f42e2137a27887cef`

Review branch:
`review/task-105d-freeze-finalization`

Authority:
`governance/core/V4_1_POLICY_FREEZE.md` §12 (State Authority Matrix — `FROZEN`
chỉ được ghi bởi một phiên Freeze Finalization có thẩm quyền), §7 (Review
Finding Action Gate), §11 (Artifact Internal Precedence),
`governance/core/TASK_COMPLETION_GATE_STANDARD.md` (Kiểm soát thay đổi Gate).

Ghi chú artifact budget (`V4.1` §10): đây là artifact governance thứ 6 của
lineage `TASK-105D`, thuộc diện `OWNER APPROVAL REQUIRED`. Approval là chỉ thị
tường minh của Owner mở phiên này ("create canonical freeze/review evidence …
Commit/push ONLY review/freeze/governance/state documentation"). Ghi lại để
phiên sau không phải suy luận, theo đúng tiền lệ `DEC-156`.

---

## VERDICT

```text
FAIL — READY GATE REMAINS BLOCKED

Completion Gate frozen        : NO
TASK-105D READY               : NO
BLOCKING findings             : 5
HARDENING findings            : 5
OUT_OF_SCOPE findings         : 3
Repair Cycle opened           : NO  (V4.1 — không mở cycle cho gate/doc issue)
Review budget TASK-105D       : 2 allowed / 0 used / 2 remaining (KHÔNG ĐỔI)
```

Freeze bị từ chối vì hai điều kiện `PASS` của `V4.1` §12 không đạt:
`32/32 gates deterministic` (F-02) và `Owner Ratification fully reflected`
(F-01, F-03, F-04). Ba finding còn lại (F-05 và phần còn lại của F-01) là
semantic gap trên đúng failure path `sai identity → sai nguồn giá → sai
KpiPurchasePrice → sai KPI/lương`.

Phiên này **không** sửa gate. `V4.1` §12 tách thẩm quyền `FROZEN` khỏi
reviewer chính là để gate được một bên độc lập kiểm tra trước implementation;
nếu phiên freeze vừa tự viết gate mới vừa tự freeze thì phần gate mới không
được ai review. Vì vậy findings được ghi kèm đề xuất nguyên văn, và việc áp
dụng thuộc một phiên gate-revision có thẩm quyền.

---

## 1. Tiền kiểm (Pre-flight)

```text
branch      : review/task-105d-freeze-finalization   ĐÚNG
HEAD        : 9cd871488a6baebf6b80737f42e2137a27887cef   ĐÚNG (khớp exact SHA)
worktree    : CLEAN
default tip : 573e051e093cd850c9efb13891bf6dee5654f0c6
             (claude/extract-upload-repo-gq2ws4 — nhánh mặc định thật trên origin)
ahead       : 3 commit / behind: 0 / divergence: WITHIN_LIMITS
```

Canonical evidence đã đọc: `CLAUDE.md`, `governance/core/V4_1_POLICY_FREEZE.md`,
`governance/core/TASK_COMPLETION_GATE_STANDARD.md`,
`governance/core/TASK_READY_GATE_STANDARD.md`, `DEC-151`…`DEC-156`,
`TASK-105B`, `TASK-105C`, `TASK-105D`, `TASK-105E`, `TASK-108B`,
`docs/spec/TASK-105D-DATA-CONTRACT.md` (toàn văn, 1511 dòng),
`S032`, `S034`, `S035`, `PROJECT/PROJECT_PROGRESS.md`,
`PROJECT/REVIEW_BUDGET_LEDGER.md`, `app/modules/pricing/file_price_provider.py`,
`docs/adr/ADR-101`.

---

## 2. Owner Ratification — xác minh độc lập

| Mục | Canonical evidence | Khớp báo cáo? | Được gate bảo vệ? |
|---|---|---|---|
| `OR-01` Public Purchase = MỘT canonical versioned source | `DEC-156` §1; data contract §3 (`D-01`/`D-02`, `INV-04`…`INV-10`) | CÓ | **KHÔNG** → F-04 |
| `OR-02` `ALIAS_AID_UNIQUE` = candidate only, không auto-resolve | `DEC-156` §2; `INV-28`/`INV-28b`; §6.6 | CÓ ở §6.6/G23, **KHÔNG** ở khối định nghĩa vận hành của chính task file | Một phần → **F-01** |
| `OR-03` actor khai báo, cấm gọi là authenticated | `DEC-156` §3; `INV-72`/`INV-73`; §12.1 | CÓ | **KHÔNG** → F-03 |
| `HB-154-04` lineage `TASK-105C` độc lập, không rewrite lịch sử/budget | `DEC-156` §4; ledger §"Root Task: TASK-105C" (`2/0/2`) + con trỏ hai chiều; `TASK-105B` giữ `2/1/1` | CÓ | N/A |
| `TASK-105E` được authorize ở mức task registration, chưa implementation | `DEC-156` §5; `docs/tasks/TASK-105E-price-resolution-composition.md` = `PLANNED`/`OUTLINE` | CÓ | N/A |

Kết luận: bốn trong năm mục khớp canonical evidence không sai lệch. `OR-02`
khớp ở tầng quyết định nhưng **chưa được truyền hết** vào task file (F-01).
Hai mục `OR-01`/`OR-03` đúng nội dung nhưng **không có Completion Gate nào
bảo vệ** — điều kiện freeze "Owner Ratification fully reflected" không đạt.

---

## 3. Scope Lock — đánh giá

`TASK-105D` chỉ sở hữu Product Identity Resolution. Xác minh không sở hữu:

```text
HistoricalVendorMin            → TASK-105C   (task file "Ngoài Phạm Vi")
PublicPurchasePrice provider   → TASK-105B   (§16.1 data contract)
P00–P11 composition            → TASK-105E   (DEC-156 §5; §16.3 GRANTED)
KPI calculation                → TASK-108B
Tracking mutation              → CẤM (INV-11…INV-16, G17)
```

Boundary `105D = identity / 105C = Tracking vendor price / 105B = Public
Purchase effective-dated price / 105E = composition / 108B = KPI downstream`
nhất quán ở cả năm task file, `DEC-154` §15, `DEC-156` §5, data contract §16.1
và `PROJECT/PROJECT_PROGRESS.md`. **Không phát hiện overlap hay cạnh ngược.**

Một gap có thật nhưng **không** phải lỗi Scope Lock: `INV-43`/`INV-44` (điều
kiện tiên quyết của Public Purchase fallback) nằm trong scope 105D ở phần
*entity*, nhưng phần *lookup* thuộc 105E. Xem H-02.

---

## 4. Ma trận 32 Completion Gate

Ký hiệu: `DET` = deterministic, `TST` = testable, `OVL` = overlap gate khác,
`CTR` = contradiction. "Assertion" = phát biểu PASS/FAIL mà một reviewer độc
lập rút ra được **mà không phải hỏi lại Owner**.

| Gate | Assertion rút ra được | Nguồn quy phạm | DET | TST | OVL | CTR |
|---|---|---|---|---|---|---|
| G01 | `sale_date < 2026-09-01` → outcome ∈ {`HISTORICAL_CONFIRMED`, `PENDING_HISTORICAL_CONFIRMATION`}; resolver/catalog/price-provider KHÔNG được gọi (spy); phân loại bằng `sale_date`, không `import_date` | `INV-46/47/48` | YES | YES | — | — |
| G02 | `sale_date >= cutover` → outcome ∈ {`RESOLVED(E-E)`, `REQUIRES_CONFIRMATION`, `PENDING_PRODUCT`}; `RESOLVED` mang đủ `(namespace, source_product_code)` | §5 union type | YES | YES | G13 | — |
| G03 | Tập DISTINCT tính theo `(source_system, raw_identity_key)` TRƯỚC khi hiển thị; `count(confirmation_action) <= |D|`, không theo số row | `INV-30`, `INV-87`, §17.1 | YES | YES | G11 | — |
| G04 | Alias đã confirm → 0 "interaction" | §17.1 (gián tiếp) | **NO** | một phần | **G24** | thuật ngữ (H-03) |
| G05 | "Deterministic unique match **có thể** auto-resolve" — **không phải assertion** | §1, §6.6 | **NO** | **NO** | — | **F-02** |
| G06 | Catalog có hai entry khác đúng một model token + raw mang token thứ ba → outcome ∈ {`REQUIRES_CONFIRMATION`, `PENDING_PRODUCT`} và `resolution_method` ∉ tập auto-resolve; 3 fixture | `INV-27`, §17.2 | YES | YES | G07 | **F-01** |
| G07 | `SIMILARITY_RANKED` ∉ tập auto-resolve; fuzzy-only không sinh mapping `CONFIRMED` | `INV-01`, §6.6 | YES | YES | G06(c) | — |
| G08 | Cùng input → cùng thứ tự candidate; mỗi candidate mang `evidence` (§6.7) | §6.7 | YES | YES | — | H-05 |
| G09 | Confirmation ghi bền vững, đọc lại được sau restart | `INV-62/63` | YES | YES | G10 | — |
| G10 | Mapping đã persist được reuse ở import/run mới | `INV-30/33` | YES | YES | G24 | — |
| G11 | Một `confirmation_action` áp cho MỌI row/order cùng distinct identity | `INV-87` | YES | YES | G03, G23 | — |
| G12 | Candidate bị suppress ⟺ cùng `(raw_identity_key, ns, code)` **và** cùng `evidence_fingerprint`; fingerprint đổi → đề xuất lại | `INV-34/35` | YES | YES | — | H-04 (INV-36) |
| G13 | 4 assertion `G13-a`…`G13-d` (kiểu riêng, `reason_code` enum đóng, không mang namespace/code, không chặn identity khác) | §17.3, `INV-24/25` | YES | YES | G02 | — |
| G14 | `product_raw` không bao giờ bị ghi đè | `INV-22` | YES | YES | — | — |
| G15 | Schema `E-F` không có field giá/tiền tệ/đơn vị giá | `INV-23` | YES | YES | — | — |
| G16 | `TASK-105D` không tính/không trả purchase price | §16.1, `INV-03` | YES | YES | G15 | — |
| G17 | Không có đường ghi nào vào Tracking; snapshot read-only | `INV-11`, §4.1 | YES | YES | — | — |
| G18 | Correction → old `SUPERSEDED` (ở lại) + new `CONFIRMED` + `CORRECT_*` event nối hai bản ghi, `reason` REQUIRED | `INV-74/75`, §13.2 | YES | YES | — | — |
| G19 | Import lại cùng file: 0 mapping mới, 0 rejection mới, 0 audit event mới, `current_revision()` KHÔNG đổi | `INV-70` | YES | YES | — | — |
| G20 | `expected_version` sai → `MappingVersionConflict`, KHÔNG ghi gì, cấm LWW | `INV-58/59/60` | YES | YES | — | — |
| G21 | Provenance giữ raw / tuple / `mapping_source` / version / `resolution_method` | §"Provenance Contract" | YES | YES | — | thiếu actor+binding (F-03/F-04) |
| G22 | "Core batch flow thao tác hoàn toàn bằng bàn phím" — bề mặt áp dụng KHÔNG xác định ở Phase 1 | §17.1 `D-14` | **NO** | **NO** | — | **H-01** |
| G23 | `count(confirmation_action) == 1`; một action resolve mọi dòng; lần sau `== 0`; **fixture `ALIAS_AID_UNIQUE` bắt buộc** | §17.4, `DEC-156`/`OR-02` | YES | YES | G11 | — |
| G24 | Store có `CONFIRMED` cho K, batch N≥2 dòng K → `count == 0`, `ALIAS_EXACT`, `current_revision()` không đổi | §17.4, `INV-70` | YES | YES | G04, G10 | — |
| G25 | Golden Business Baseline không đổi | `V4.1` §6 | YES | YES | — | — |
| G26 | Tracking MISS + PP exact unique → `PUBLIC_PURCHASE:<code>` | `DEC-154` §3 | YES | YES | G27, G28 | — |
| G27 | Tracking MISS **không** tự động thành Pending | `DEC-154` §3 | YES | YES | **G26** | — |
| G28 | `PUBLIC_PURCHASE` identity hợp lệ mà không cần Tracking product giả | `DEC-154` §3 | YES | YES | **G26/G27** | — |
| G29 | `namespace` được persist cùng mapping, IMMUTABLE | `INV-17/19` | YES | YES | G30 | — |
| G30 | `TRACKING:X` ≠ `PUBLIC_PURCHASE:X`; không so sánh chỉ bằng code | `INV-18` | YES | YES | G29 | — |
| G31 | Cross-system mapping EXPLICIT (cấm suy ra từ trùng chuỗi), auditable, correctable | `INV-38/41` | YES | YES | — | thiếu `INV-43/44` (H-02) |
| G32 | Mapping cross-system đã confirm reuse không hỏi lại | `INV-42` | YES | YES | G31 | — |

### Tổng hợp ma trận

```text
Testable                    : 30 / 32     (G05, G22 KHÔNG)
Deterministic               : 29 / 32     (G04, G05, G22 KHÔNG)
Contradiction               : 1 gate trực tiếp (G06 qua F-01), lan sang G23
Overlap ghi nhận            : G04⊂G24 ; G07∩G06(c) ; G26≈G27≈G28 ; G10∩G24 ;
                              G29∩G30 ; G31∩G32
```

Overlap **không** phải finding — trong một gate set an toàn, phát biểu cùng
một bất biến ở hai góc là chấp nhận được. Ghi lại để phiên implementation
không đếm trùng evidence.

---

## 5. Bao phủ 20 case đối kháng bắt buộc (A–T)

| Case | Nội dung | Gate bao phủ | Kết luận |
|---|---|---|---|
| A | 10.000 row / 50 distinct identity → xử lý 50 | G03, G11 | **ĐẠT** |
| B | Known confirmed mapping → 0 action | G24 (chính xác), G04 (mờ) | **ĐẠT** |
| C | Catalog exact unique → 0 action | G05 | **KHÔNG ĐẠT** — F-02 |
| D | `ALIAS_AID_UNIQUE` → candidate #1, ≤1 action, lần sau 0 | G23 (fixture bắt buộc) | **ĐẠT** |
| E | Fuzzy only → không production authority | G07, G06(c) | **ĐẠT** |
| F | Ambiguous → không tự chọn sai, ≤1 action cho candidate đúng | G06, G23 | **ĐẠT** |
| G | No match → Pending, không fake Tracking | G13, G28, G17 | **ĐẠT** |
| H | Public Purchase direct product | G26, G27, G28 | **ĐẠT** |
| I | `TRACKING:ABC` vs `PUBLIC_PURCHASE:ABC` | G30 | **ĐẠT** |
| J | Cross-system fallback; không mapping → Pending, không đoán mã | G31/G32 (một phần) | **MỘT PHẦN** — H-02 |
| K | Rejection memory theo evidence fingerprint | G12 | **ĐẠT** |
| L | Correction: supersede, audit preserved, không DELETE | G18 | **ĐẠT** |
| M | Duplicate import → 0 side effect, revision không đổi | G19 | **ĐẠT** |
| N | Concurrency → explicit conflict, không LWW | G20 | **ĐẠT** |
| O | Tracking rename → confirmed mapping vẫn valid | **KHÔNG CÓ** | **KHÔNG ĐẠT** — F-05 |
| P | Tracking product biến mất → mapping lịch sử không mất hiệu lực | **KHÔNG CÓ** | **KHÔNG ĐẠT** — F-05 |
| Q | Pre-cutover → không gọi resolver/catalog/provider | G01 | **ĐẠT** |
| R | Late import 2027, `sale_date` 2026-08-20 → vẫn pre-cutover | G01 | **ĐẠT** |
| S | Actor REQUIRED; không actor → không silently accepted | **KHÔNG CÓ** | **KHÔNG ĐẠT** — F-03 |
| T | Published PP version immutable; identity+price cùng version lineage | **KHÔNG CÓ** | **KHÔNG ĐẠT** — F-04 |

```text
ĐẠT 14 / MỘT PHẦN 1 / KHÔNG ĐẠT 5   trên 20 case bắt buộc
```

Nguyên nhân gốc chung của O, P, S, T (và một phần J): bảng 32 gate được soạn
tại `S032`/`DEC-154`, **trước** khi `S034` dựng các entity `E-A`
(`PublicPurchaseSourceVersion`), `E-D` (`TrackingCatalogSnapshot`), `E-L`
(`ResolutionBinding`) và contract actor §12.1. Khi ratification `S035` chạy,
chỉ `G06`, `G13`, `G23`, `G24` được viết lại theo định nghĩa mới. Các bất biến
sinh ra sau đó — `INV-04`…`INV-10`, `INV-11`…`INV-16`, `INV-43`/`INV-44`,
`INV-55`…`INV-57`, `INV-72`/`INV-73` — không có gate nào tiếp nhận.

---

## 6. UX / action semantics

`confirmation_action` (§17.1 / `D-14`) là **domain command**, không phải số
click/keystroke; đếm đúng bốn loại `CONFIRM_MAPPING` | `REJECT_CANDIDATE` |
`CONFIRM_CROSS_SYSTEM` | `SET_PENDING`, loại trừ tường minh điều hướng/cuộn/
focus/tìm kiếm/lọc/sắp xếp. Định nghĩa này **đạt** yêu cầu §7 của brief và là
phần mạnh nhất của gate set: nó test được mà không cần dựng UI.

| Yêu cầu | Gate | Kết quả |
|---|---|---|
| `KNOWN` = 0 | G24 | ĐẠT (assertion chính xác) |
| `CATALOG_EXACT_UNIQUE` = 0 | G05 | **KHÔNG ĐẠT** — gate cho phép ("có thể"), không assert `== 0` |
| `ALIAS_AID_UNIQUE` ≤ 1 | G23 | ĐẠT |
| `AMBIGUOUS` candidate đúng ≤ 1 | G23 (`== 1`, chặt hơn) | ĐẠT |
| Pending không bị coi là UX failure | G13-d, task prose | ĐẠT |

Ghi chú: G23 assert `== 1` trong khi contract nói `<= 1`. `== 1` chặt hơn và
không mâu thuẫn (một identity AMBIGUOUS theo định nghĩa cần ít nhất một
quyết định của người). Không phải finding.

---

## 7. Persistence / Audit — bao phủ gate

| Cơ chế | Bất biến | Gate | Kết quả |
|---|---|---|---|
| `ProductIdentityMapping` | `INV-30`…`INV-33` | G09, G10, G24 | ĐẠT, trừ `INV-33` (H-04) |
| Alias index | `D-06`, `INV-63` | G09, G10 | ĐẠT |
| `RejectedCandidateMemory` | `INV-34`…`INV-37` | G12 | ĐẠT, trừ `INV-36` (H-04) |
| `CrossSystemProductMapping` | `INV-38`…`INV-45` | G31, G32 | ĐẠT, trừ `INV-43/44` (H-02) |
| `HistoricalConfirmedRegistry` | `INV-46`…`INV-54` | G01 | ĐẠT |
| `MappingAuditEvent` | `INV-74`…`INV-78` | G18 | ĐẠT ở correction; `INV-78` (`REPIN_REPORT`) không gate |
| Optimistic concurrency | `INV-58`…`INV-61` | G20 | ĐẠT |
| Idempotency | `INV-68`…`INV-71` | G19 | ĐẠT (mạnh) |
| Supersession | `INV-32`, `INV-74` | G18 | ĐẠT |
| Immutable report binding / replay | `INV-55`…`INV-57` | **KHÔNG CÓ** | **KHÔNG ĐẠT** — F-04 |
| Actor contract | `INV-72`/`INV-73` | **KHÔNG CÓ** | **KHÔNG ĐẠT** — F-03 |
| Catalog drift | `INV-13`/`INV-14`/`INV-16` | **KHÔNG CÓ** | **KHÔNG ĐẠT** — F-05 |
| Backup/export tương đương bit | `INV-65` | **KHÔNG CÓ** | HARDENING (nằm trong Exit Criteria catch-all) |

`Exit Criteria` có một điều khoản quét ("Toàn bộ invariant `INV-01`…`INV-87`
có assertion tương ứng hoặc có lý do ghi rõ"). Điều khoản đó **giảm nhẹ**
nhưng **không thay thế** một REQUIRED check: nó không có `Evidence Level`,
không có `Status`, và không bị `validate_task_completion` soi như một check.
Với một task Effective Risk `HIGH`, bốn bất biến trên đường lỗi giá/KPI/lương
không thể chỉ dựa vào một dòng Exit Criteria.

---

## 8. Unified Public Purchase contract (`OR-01`)

Contract đúng và đủ ở tầng thiết kế: `D-01`/`D-02` (một version lineage, hai
projection), `INV-06` (mọi `price_rows[*].product_key` phải tồn tại trong
`identity_rows` của **cùng** version), `INV-02`/`INV-03` (loader identity phải
strict và **không** được sửa `FilePriceProvider` đang FROZEN).

`INV-02` đã được xác minh độc lập trên mã nguồn thật:

```text
app/modules/pricing/file_price_provider.py:92-94
    def from_yaml(cls, path: Path) -> "FilePriceProvider":
        data = load_yaml(path)
        return cls(data.get("prices", []))
```

Xác nhận: `from_yaml` bỏ qua mọi khoá top-level ngoài `prices` **trong im
lặng** — rủi ro mà `INV-02` mô tả là có thật, không phải suy đoán.

**Nhưng không có gate nào bảo vệ.** Ranh giới mà `TASK-105D` chịu trách nhiệm
và test được ngay trong scope của chính nó là: (a) loader projection identity
strict — thiếu/sai/rỗng/khoá lạ là **lỗi load**, không phải danh mục rỗng;
(b) `INV-06` được thi hành tại publish/load, không phải lúc tính lương;
(c) `ResolutionBinding` ghim `pp_version_id` và replay cho kết quả bất biến.
Không kéo implementation `TASK-105B` vào scope — cả ba đều nằm ở phía 105D.

Hệ quả nếu freeze nguyên trạng: một implementation có thể PASS 32/32 trong
khi vận hành hai nguồn Public Purchase độc lập và làm mất version/replay
binding — đúng lỗ hổng `HB-154-02` mà `S034` đã đóng ở tầng contract.

---

## 9. Pre-cutover boundary

G01 là gate được soạn tốt: `INV-46` viết dưới dạng pseudo-code định tuyến,
biến thẳng thành test được. Hai kết cục đóng (`HISTORICAL_CONFIRMED` |
`PENDING_HISTORICAL_CONFIRMATION`), cấm gọi resolver/catalog/price-provider
bất kể registry có entry hay không (`INV-47`), phân loại bằng `sale_date`
(`INV-48`), registry không cần khớp catalog hiện tại (`INV-49`),
`confirmed_identity` OPTIONAL không kích hoạt resolver (`INV-50`), cấm backfill
bằng catalog/giá hiện tại (`INV-54`, §14.3).

**Đánh giá: ĐẠT.** Cases Q và R được bao phủ đầy đủ và deterministic. Đây là
phần không có finding nào.

---

## 10. Ranh giới `TASK-105E`

`TASK-105D` **không** implement `P00–P11` — xác nhận đúng: task file "Ngoài
Phạm Vi", data contract §16.1, `DEC-156` §5.

Output contract đủ cho 105E tiêu thụ hay chưa:

```text
ResolutionOutcome = RESOLVED(E-E, provenance)
                  | REQUIRES_CONFIRMATION(candidates, provenance)
                  | PENDING_PRODUCT(reason_code, attempted_sources, provenance)
                  | HISTORICAL_CONFIRMED(identity?, price, provenance)
```

Union type đóng, `reason_code` enum đóng, `namespace` enum đóng, `PENDING`
không bao giờ là `None`/`""`/`0` (`INV-24/25`, G13). **Đủ deterministic và
type-safe** cho lớp composition. Một thiếu sót đã ghi: mã Public Purchase mà
105E cần cho `P03` đến từ `CrossSystemProductMapping`, và biên lookup đó không
có gate (H-02).

---

## 11. Ready-Gate data dependency — review độc lập claim

Claim của readiness report: dataset production thật **không** phải blocker
Ready Gate của `TASK-105D`.

**Xác nhận claim này ĐÚNG.** Lập luận kiểm chứng được:

1. `INV-46` cho `registry` rỗng một kết cục xác định:
   `PENDING_HISTORICAL_CONFIRMATION` — không phải lỗi (§14.3 `M2`).
2. §14.3 cấm tuyệt đối coi "store rỗng" là lỗi cần vá bằng dữ liệu bịa; store
   rỗng là trạng thái khởi đầu ĐÚNG và Pending là kết quả ĐÚNG (`DEC-103`).
3. `M0` đặt `PRODUCT_IDENTITY_RESOLVER = OFF` và giữ `PendingPriceProvider`
   làm default, nên implementation không chạm production path.
4. `M1`/`M2` bỏ qua được khi Owner chưa có bảng/báo cáo (`INV-54`).

Không tìm thấy governance hay business contract nào contradict. Implementation
có thể bắt đầu bằng fixture/synthetic test data mà không invent production
mapping. **Không có finding.**

---

## 12. FINDINGS

### BLOCKING

---

**F-01 — BLOCKING — Owner Decision `DEC-156`/`OR-02` chưa được truyền hết vào
khối định nghĩa quy phạm của Completion Gate; G06 và G23 mâu thuẫn nhau.**

Vị trí: `docs/tasks/TASK-105D-product-identity-resolver.md`, khối
"Định nghĩa vận hành bắt buộc", mục `AMBIGUOUS`:

```text
AMBIGUOUS
    = resolution_method KHÔNG thuộc tập auto-resolve đóng (ALIAS_EXACT,
      ALIAS_AID_UNIQUE, CATALOG_EXACT_UNIQUE — data contract §6.6).
    Ba nguồn ambiguity, mỗi nguồn một fixture bắt buộc: MULTIPLE_EXACT,
      CROSS_NAMESPACE_TIE, ONLY_SIMILARITY.
```

Khối này vẫn liệt kê `ALIAS_AID_UNIQUE` **bên trong** tập auto-resolve và vẫn
nói "Ba nguồn". Cả hai đều là trạng thái **trước** ratification.

Canonical evidence nói ngược lại:

```text
DEC-156 §2 : "INV-28 SỬA — tập auto-resolve còn ĐÚNG HAI phương thức:
              ALIAS_EXACT, CATALOG_EXACT_UNIQUE"
INV-28b    : "ALIAS_AID_UNIQUE KHÔNG BAO GIỜ tự sinh một mapping CONFIRMED"
§6.6       : tập auto-resolve "TẬP ĐÓNG, ĐÚNG HAI PHƯƠNG THỨC"
§17.2      : "Bốn nguồn cần confirmation" — (d) ALIAS_AID_UNIQUE
```

Đây là hai khối `text` quy phạm (V4.1 §11) nói ngược nhau ở hai artifact
canonical — không tự dàn xếp được.

Failure path cụ thể: G06 assert "AMBIGUOUS không bao giờ auto-resolve".
Theo định nghĩa `AMBIGUOUS` trong chính task file, một identity
`ALIAS_AID_UNIQUE` **không phải** AMBIGUOUS ⇒ G06 không ràng buộc nó ⇒ một
implementation auto-resolve `ALIAS_AID_UNIQUE` vẫn PASS G06, trong khi
`DEC-156` cấm tường minh. G23 sẽ FAIL. Hai gate cho hai kết luận trái ngược
trên cùng một hành vi — reviewer tương lai buộc phải hỏi lại Owner gate nào
thắng, tức vi phạm điều kiện freeze.

Bằng chứng propagation thiếu: `git diff d3b73e5..9cd8714` trên task file cho
thấy `S035` đã sửa Authority, Resolution Order và `CHECK-105D-23`, nhưng
**không** chạm khối "Định nghĩa vận hành bắt buộc".

Đề xuất nguyên văn (COMPLETION GATE CHANGE PROPOSAL, cần authority riêng):

```text
AMBIGUOUS
    = resolution_method KHÔNG thuộc tập auto-resolve đóng
      (ALIAS_EXACT, CATALOG_EXACT_UNIQUE — data contract §6.6, INV-28
       đã sửa theo DEC-156/OR-02).
    Bốn nguồn ambiguity, mỗi nguồn một fixture bắt buộc: MULTIPLE_EXACT,
      CROSS_NAMESPACE_TIE, ONLY_SIMILARITY, ALIAS_AID_UNIQUE.
```

Kèm sửa G06 từ "Ba fixture" thành "Bốn fixture" (fixture thứ tư đã có
assertion chi tiết ở G23; G06 chỉ cần trỏ tới, không nhân đôi).

---

**F-02 — BLOCKING — `CHECK-105D-05` (G05) là một phát biểu cho phép, không
phải một assertion; không có PASS/FAIL condition.**

Nguyên văn gate: *"Deterministic unique match **có thể** auto-resolve"*.

"Có thể" không loại trừ điều gì. Một implementation không bao giờ auto-resolve
`CATALOG_EXACT_UNIQUE` (bắt người dùng xác nhận mọi thứ) PASS gate này; một
implementation auto-resolve cũng PASS. Gate không thể FAIL ⇒ không
deterministic ⇒ vi phạm điều kiện freeze "32/32 deterministic enough for
independent verification".

Đây cũng là case C bắt buộc của brief (`CATALOG_EXACT_UNIQUE → 0
confirmation_action`) và là yêu cầu UX §7 duy nhất không có gate assert.

Ngữ nghĩa quy phạm đã tồn tại, chỉ chưa được chép vào gate:

```text
§1     : "DETERMINISTIC (khớp duy nhất) → 0 confirmation_action"
§6.6   : CATALOG_EXACT_UNIQUE thuộc tập auto-resolve đóng
INV-29 : khớp exact ở CẢ HAI namespace → KHÔNG auto-resolve
```

Đề xuất nguyên văn:

```text
CHECK-105D-05 (G05)
    Setup : catalog có ĐÚNG MỘT entry khớp exact (raw_identity_key hoặc aid)
            với raw identity, và chỉ trong MỘT namespace.
    Assert: count(confirmation_action) == 0
            resolution_method == CATALOG_EXACT_UNIQUE
            outcome == RESOLVED(namespace, source_product_code)
    Fixture âm bắt buộc (INV-29): khớp exact ở CẢ HAI namespace
            → resolution_method == CROSS_NAMESPACE_TIE, KHÔNG auto-resolve.
```

---

**F-03 — BLOCKING — `OR-03` (actor contract) không có Completion Gate nào bảo
vệ.**

`INV-72` (actor_id REQUIRED trên mọi command đổi state, không có giá trị mặc
định) và `INV-73` (actor Phase 1 là khai báo, cấm gọi là authenticated) là ba
ràng buộc Owner đặt ra khi phê chuẩn `OR-03` tại `DEC-156` §3.

Quét toàn bộ 32 dòng gate: **0 lần xuất hiện** của `actor`. G21 (provenance)
liệt kê `raw / tuple / source / version / method` — không có actor. G18
(correction audit) nói "giữ old/new mapping", không nói actor.

Failure path: một implementation đặt `actor_id` mặc định `"system"` khi người
vận hành không khai báo, hoặc một artifact/UI mô tả actor là "authenticated
user", PASS 32/32 gate trong khi vi phạm trực tiếp một Owner Decision. Với
`ADR-102` bắt buộc `ChangedBy` trên mọi thay đổi do người kích hoạt, đây là
mất khả năng truy trách nhiệm trên đường lỗi dẫn tới KPI/lương.

Case S là case đối kháng **bắt buộc** của brief.

Đề xuất: bổ sung assertion actor vào G21 (hoặc một gate riêng nếu Owner cho
phép mở rộng gate set):

```text
Assert: mọi command đổi state thiếu actor_id → bị TỪ CHỐI (không ghi event,
        không tăng version, không "system", không anonymous)   [INV-72]
        MappingAuditEvent.actor_id REQUIRED và non-empty       [§13.1]
        không artifact/output nào của TASK-105D mô tả actor Phase 1 bằng
        từ "authenticated"                                     [INV-73]
```

---

**F-04 — BLOCKING — `OR-01` (unified Public Purchase source) và
`ResolutionBinding`/replay không có Completion Gate nào bảo vệ.**

Quét 32 dòng gate: 0 lần xuất hiện của `publish`, `immutable`, `version_id`,
`pp_version`, `binding`, `replay`.

Không gate nào assert:

```text
INV-06  price_rows[*].product_key ∈ identity_rows của CÙNG version
        (vi phạm = lỗi load)
INV-02  loader identity projection STRICT — khối thiếu/rỗng/khoá lạ là lỗi
        load, KHÔNG phải danh mục rỗng
INV-03  không sửa app/modules/pricing/file_price_provider.py (FROZEN, DEC-153)
INV-07  đổi product_name/aliases không đổi kết quả report đã ghim version
INV-55  ResolutionBinding ghim CẢ BỐN revision, không ghim từng phần
INV-56  replay cho kết quả GIỐNG HỆT bất kể store/catalog/giá đã đổi
INV-57  thiếu thành phần binding → lỗi cứng, KHÔNG fallback "mới nhất",
        KHÔNG Pending
```

Brief §9 yêu cầu tường minh: *"Không để implementation sau có thể PASS 105D
nhưng lại tạo hai independent operational sources làm mất version/replay
binding."* Ở trạng thái gate hiện tại, điều đó **làm được**.

Case T là case đối kháng **bắt buộc**. Boundary 105D chịu trách nhiệm được
nêu ở §8 của review này — không kéo implementation `TASK-105B` vào scope.

---

**F-05 — BLOCKING — Ngữ nghĩa catalog drift (`INV-13`/`INV-14`/`INV-16`) không
có Completion Gate nào bảo vệ; cases O và P không đạt.**

Quét 32 dòng gate: 0 lần xuất hiện của `STALE`, `rename`, `đổi tên`,
`biến mất`.

Data contract định nghĩa đầy đủ cơ chế — `status = STALE` (§6.4), event
`MARK_STALE` (§13.2), `reason_code = MAPPING_STALE_TARGET_ABSENT` (§5) —
nhưng **không check nào yêu cầu chúng hoạt động**:

```text
INV-13  Tracking đổi name/alt, tracking_code giữ nguyên
        → mapping đã confirm VẪN hợp lệ (tên không phải identity)     [case O]
INV-14  Product biến mất khỏi board hiện tại
        (a) mapping lịch sử KHÔNG bị vô hiệu hoá, KHÔNG bị xoá
        (b) report ghim capture cũ replay không đổi
        (c) identity MỚI chỉ khớp mã đã biến mất → MAPPING_STALE,
            KHÔNG auto-resolve                                        [case P]
INV-16  Mã bị gộp qua alias.map → KHÔNG tự chuyển mapping đã confirm
            sang mã chính; tạo MAPPING_STALE + candidate #1
INV-12  capture_status = FAILED → LỖI, KHÔNG phải Pending
```

Failure path: Tracking là hệ thống ngoài, và `DEC-147` §3 R4 xác nhận `board`
sửa/xoá được bởi nhiều tài khoản. Một implementation vô hiệu hoá mapping đã
confirm khi capture mới thiếu mã đó sẽ PASS 32/32, đồng thời làm mọi đơn hàng
lịch sử của sản phẩm đó rơi về Pending hoặc bị remap — vi phạm `INV-15` (cấm
retroactive remap) qua một con đường không gate nào chặn. `INV-12` bổ sung một
biến thể nguy hiểm hơn: một lần capture hỏng bị đọc thành "sản phẩm không tồn
tại".

---

### HARDENING

**H-01** — `CHECK-105D-22` (keyboard-first) nhắm một bề mặt UI mà `ADR-101`
đặt ngoài Phase 1 ("Toàn bộ Phase 1 là thư viện Python thuần chạy được bằng
CLI"; "engine trước, API sau, UI sau cùng"). Là REQUIRED/E1, gate này hoặc
vacuous (CLI thì mọi thao tác đều bằng bàn phím) hoặc `NOT_TESTED` vĩnh viễn —
và reviewer không tự phân biệt được. Theo `TASK_COMPLETION_GATE_STANDARD`, một
REQUIRED check `NOT_TESTED` chặn `DONE` trừ khi được đánh dấu `NOT_APPLICABLE`
kèm lý do hợp lệ; hiện chưa có lý do nào được ghi.
*Re-trigger:* phiên xác định bề mặt batch mapping của Phase 1, hoặc phiên
gate-revision xử lý F-01…F-05 — tuỳ phiên nào đến trước.

**H-02** — `INV-43`/`INV-44` (điều kiện tiên quyết fallback: thiếu
`CrossSystemProductMapping` `CONFIRMED` → Pending, TUYỆT ĐỐI không đoán mã
Public Purchase) không có check ở biên mà 105D sở hữu. G31 phủ `INV-38` lúc
**tạo** mapping, không phủ lúc **tra cứu**. Phần test được ngay trong 105D:
API cross-system trả `public_purchase_code` của mapping `CONFIRMED`, hoặc
absence — không bao giờ một mã dẫn xuất, kể cả khi tồn tại một PP product
trùng chuỗi với `tracking_code`.
*Re-trigger:* phiên soạn Completion Gate của `TASK-105E`, hoặc phiên
implementation 105D chạm API cross-system lookup — tuỳ phiên nào đến trước.

**H-03** — `CHECK-105D-04` dùng từ "interaction", một thuật ngữ thứ ba bên
cạnh `confirmation_action` (§17.1) và "normal action". §17.1 đã chuẩn hoá và
tuyên bố bỏ "thao tác bình thường", nhưng bỏ sót "interaction". Đọc theo nghĩa
đen ("0 interaction") thì cả việc mở màn hình batch cũng vi phạm. G24 đã phát
biểu cùng bất biến một cách chính xác, nên G04 hiện dư thừa và mơ hồ.
*Re-trigger:* phiên gate-revision xử lý F-01…F-05.

**H-04** — `INV-36` ("Từ chối A không có nghĩa là chấp nhận B") và `INV-33`
("tìm thấy nhiều hơn một mapping `CONFIRMED` → lỗi toàn vẹn store, KHÔNG được
tự chọn một cái") không có check. Cả hai là ngữ nghĩa chống-map-sai.
*Re-trigger:* phiên implementation 105D chạm rejection workflow hoặc
`read_active_mapping`.

**H-05** — `ranking_method_id` là OPTIONAL ở §6.7 nhưng là một input được hash
vào `evidence_fingerprint` (§7.3). Nếu vắng, chiều "thuật toán xếp hạng đã
đổi" của `INV-35` im lặng biến mất, và một candidate đã bị từ chối sẽ không
được đề xuất lại dù ranking đã thay đổi. Đề xuất: REQUIRED khi
`resolution_method` là loại có ranking, hoặc ghi rõ giá trị sentinel.
*Re-trigger:* phiên implementation `RejectedCandidate`/candidate ranking.

---

### OUT_OF_SCOPE

**O-01** — Biến `P00–P11` thành executable gate → `TASK-105E` (`DEC-156` §5).
Không thuộc contract của `TASK-105D`.

**O-02** — Refreeze Scope Lock/Completion Gate của `TASK-105C` — lineage riêng
(`2/0/2`), phiên riêng.

**O-03** — `OS-154-01` — vẫn mở, vẫn ngoài scope, kế thừa nguyên trạng từ
`DEC-155`/`DEC-156`. Phiên này không chạm.

---

### Quan hệ giữa các finding

```text
F-01 ← nguyên nhân gốc: propagation DEC-156 không đầy đủ (S035)
F-03, F-04, F-05, H-02
     ← nguyên nhân gốc chung: bảng 32 gate soạn tại S032/DEC-154, TRƯỚC khi
       S034 dựng E-A / E-D / E-L và contract actor §12.1; chỉ G06/G13/G23/G24
       được viết lại tại S034/S035
F-02, H-01, H-03 ← độc lập, là khiếm khuyết diễn đạt gate từ bản draft đầu
H-04, H-05 ← độc lập, gap bất biến nhỏ
Không finding nào là duplicate của finding khác.
```

---

## 13. Validators — base vs final

Phiên này không sửa `app/**`, `tests/**`, `config/**`, `tools/**`,
`scripts/**`, `pyproject.toml`; kết quả base và final vì vậy phải bằng nhau.

| Validator | Base (`9cd8714`) | Final | Regression |
|---|---|---|---|
| `validate_structure` | PASS — 21 required paths | PASS | KHÔNG |
| `validate_project_state` | PASS | PASS | KHÔNG |
| `validate_evidence` | PASS — 88 REQUIRED PASS record | PASS | KHÔNG |
| `validate_task_completion` | PASS — 6 DONE task | PASS | KHÔNG |
| `validate_reference_integrity` | FAIL — đúng 3 issue `TASK-REM-T06` | FAIL — đúng 3 issue `TASK-REM-T06` | KHÔNG |
| `branch_authority_check.sh` | `AUTHORITY_OK`, `WITHIN_LIMITS` | `AUTHORITY_OK` | KHÔNG |
| `git diff --check` | sạch | sạch | KHÔNG |

Baseline reference-integrity khớp chính xác kỳ vọng đã công bố (3 issue
`TASK-REM-T06`, nêu không backtick vì đây là output validator chứ không
phải đường dẫn phân giải được: /README.md, CODE_OF_CONDUCT.md,
CONTRIBUTING.md).

Golden + full suite (Effective Risk `HIGH` → chạy đầy đủ):

```text
tests/test_golden_baseline.py : 58 passed, 2 skipped
full suite                    : 756 passed, 11 skipped
```

Golden khớp nguyên văn con số đã công bố ở `CLAUDE.md` (`58 passed, 2
skipped`). Không regression.

---

## 14. Production diff

```text
git diff --stat 573e051..HEAD -- app tests config tools scripts pyproject.toml
→ (rỗng)
```

```text
production implementation changed : NO
test implementation changed       : NO
Tracking changed                  : NO (0 file — repo khác, không chạm)
FilePriceProvider activated       : NO (PendingPriceProvider vẫn default)
```

Toàn bộ diff từ đỉnh nhánh mặc định tới `HEAD` là documentation/governance.

---

## 15. Trạng thái sau review

```text
TASK-105D  = PLANNED / SPEC COMPLETE + DATA CONTRACT COMPLETE + OWNER RATIFIED
             / READY GATE BLOCKED
             Completion Gate 32 check = DRAFT, NOT_TESTED, NOT FROZEN
             Freeze Finalization attempt #1 = FAIL (artifact này)
             implementation = NOT STARTED / NOT AUTHORIZED
             budget = 2 allowed / 0 used / 2 remaining

TASK-105C  = BLOCKED / NOT AUTHORIZED        (khớp canonical evidence)
TASK-105E  = PLANNED / OUTLINE / READY GATE BLOCKED / NOT IMPLEMENTED
             / NOT AUTHORIZED                (khớp canonical evidence)
TASK-108B  = BLOCKED_BY_DEPENDENCY — không đổi; blocker `TASK-105D` vẫn mở,
             nay có lý do cụ thể hơn (gate chưa freeze được, 5 BLOCKING)
```

---

## 16. NEXT AUTHORIZED ACTION

Một phiên **gate revision có thẩm quyền** cho `TASK-105D`, dùng khuôn
`COMPLETION GATE CHANGE PROPOSAL` (`governance/core/TASK_COMPLETION_GATE_STANDARD.md`), xử lý
F-01…F-05 theo thứ tự:

1. **F-01** — sửa khối "Định nghĩa vận hành bắt buộc" cho khớp `DEC-156`/
   `OR-02` (tập auto-resolve = hai phương thức; bốn nguồn ambiguity), rồi sửa
   G06 "Ba fixture" → "Bốn fixture". Đây là hoàn tất propagation một Owner
   Decision đã có, **không** phải quyết định nghiệp vụ mới.
2. **F-02** — viết lại G05 thành assertion (`count == 0`,
   `resolution_method == CATALOG_EXACT_UNIQUE`, + fixture âm `INV-29`).
3. **F-03 / F-04 / F-05** — quyết định của Owner về hình thức: mở rộng
   assertion của G21/G31 và bổ sung gate mới cho catalog drift, **hay** giữ
   đúng 32 gate và nạp các assertion vào gate hiện có. Mở rộng gate set vượt
   32 là thay đổi phạm vi artifact mà Owner đã được thông báo, nên cần Owner
   xác nhận (`V4.1` §10 + §12).
4. Sau khi áp dụng: một phiên **Freeze Finalization** mới re-review **toàn bộ**
   gate set đã sửa (không chỉ phần diff) rồi mới ghi `FROZEN`.

Chỉ sau khi Completion Gate `FROZEN` thì `TASK-105D` mới chuyển được `READY`,
và implementation vẫn cần một phiên cấp phép riêng.

Song song, không bị chặn bởi việc trên: refreeze `TASK-105C`; soạn Scope Lock
+ Completion Gate cho `TASK-105E`; Owner cung cấp dữ liệu thật
(`PublicPurchaseSourceVersion` đầu tiên, `TrackingCatalogSnapshot` đầu tiên,
bảng mapping Owner-confirmed nếu có, báo cáo lịch sử Owner-confirmed).

---

## 16bis. Cảnh Báo Governance Phát Sinh — `V4.1` §8 Branch Divergence Limit

Sau commit của phiên này, `scripts/branch_authority_check.sh` chuyển từ
`WITHIN_LIMITS` sang:

```text
ahead default   : 4 commit          (ngưỡng: > 10)
divergence days : 0                 (ngưỡng: > 3)
cumulative LOC  : 5637              (ngưỡng: > 5.000)  ← VƯỢT
DIVERGENCE      : INTEGRATION_DECISION_REQUIRED [ loc>5000 ]
AUTHORITY       : BRANCH_WITH_UPSTREAM
RESULT          : AUTHORITY_OK
```

`V4.1` §8 yêu cầu Owner chọn một trong ba, và cấm tiếp tục im lặng:

```text
(A) integrate/merge sớm
(B) cắt scope
(C) tiếp tục divergence có lý do + review date
```

Ghi chú để Owner quyết định đúng bối cảnh: toàn bộ 5637 LOC là
documentation/governance (`git diff --shortstat 573e051..HEAD` →
`16 files changed, 5573 insertions(+), 64 deletions(-)`), **0 dòng production**
(`app/**`, `tests/**`, `config/**`, `tools/**`, `scripts/**`, `pyproject.toml`
đều rỗng trong diff). Rủi ro integration vì vậy là rủi ro **xung đột văn bản**,
không phải rủi ro hành vi. `AUTHORITY` vẫn `AUTHORITY_OK` — đây là một quyết
định integration, không phải một vi phạm thẩm quyền.

Phiên này **không** tự chọn phương án nào và **không** merge.

## 17. Điều phiên này KHÔNG làm

```text
- Không sửa app/**, tests/**, config/**, tools/**, scripts/**, pyproject.toml.
- Không implement TASK-105C, TASK-105D, TASK-105E.
- Không sửa một dòng nào của bảng 32 Completion Gate.
- Không ghi FROZEN.
- Không chuyển TASK-105D sang READY.
- Không activate FilePriceProvider; không thay PendingPriceProvider.
- Không sửa repo Tracking; không tạo mapping/dataset production.
- Không merge vào nhánh mặc định.
- Không mở Repair Cycle; không tiêu review budget.
- Không hạ tiêu chuẩn bất kỳ gate nào để đạt PASS.
```
