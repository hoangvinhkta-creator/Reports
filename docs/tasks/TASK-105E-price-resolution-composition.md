# TASK-105E — Price Resolution Composition

## Metadata

Status:
PLANNED

Specification State:
OUTLINE — task ID và phạm vi trách nhiệm do Owner cấp tại `DEC-156` §5.
Scope Lock **chưa** soạn, Completion Gate **chưa** soạn, **chưa** freeze,
implementation **chưa** được cấp phép.

Phase:
PHASE-01 — Product identity + price-resolution foundation

Task Mode:
MAJOR

Primary Agent Tier:
C

Escalation Tier:
C

Difficulty:
3/5 (orchestration — không có parsing/matching mới; độ khó nằm ở đúng thứ tự
và đúng provenance, không ở thuật toán)

Risk:
4/5

Blast Radius:
5/5

Effective Risk:
HIGH — `max(Local Risk 4, Blast Radius 5)` theo failure path
`chọn sai nguồn giá → sai KpiPurchasePrice → sai EligibleKpiProfit → sai CR
→ sai KPI/lương` (`governance/core/V4_1_POLICY_FREEZE.md` §4). Golden hiện
chỉ phủ `PendingPriceProvider` nên **không** hạ Blast Radius (§4.1).

Project Profile:
PRODUCT

Review Budget lineage:
`TASK-105E` — root lineage mới, `2 allowed / 0 used / 2 remaining`
(`PROJECT/REVIEW_BUDGET_LEDGER.md`). Cấp theo bảng đã freeze `V4.1` §2
(`HIGH/CRITICAL = 2`). Mở task này **không** tiêu cycle nào.

Authority:
`DEC-154` §11 (bảng `P00–P11`, công bố khoảng trống ownership và cấm phiên
reconciliation tự lấp) → `DEC-155` §5 (`ROADMAP CHANGE PROPOSAL`) →
**`DEC-156` §5 (Owner cấp task ID và authority)**.

## Mục Tiêu (Objective)

Là **canonical owner** của semantics composition `P00–P11`: nhận một product
identity đã resolve, áp đúng thứ tự ưu tiên nguồn giá, điều phối
`HistoricalVendorMin` / `PublicPurchasePrice` / `Pending`, giữ nguyên
provenance, và trả ra `KpiPurchasePrice` semantics cho downstream
`TASK-108B`.

```text
resolved identity (+ sale_date)
  → apply P00–P11
  → coordinate HistoricalVendorMin / PublicPurchasePrice / Pending
  → preserve provenance
  → output resolved KpiPurchasePrice semantics → TASK-108B
```

Đây là **lớp orchestration/composition**. Nó không sở hữu một nguồn dữ liệu
nào của riêng mình.

## Điều TASK-105E KHÔNG Làm (quy phạm — `DEC-156` §5)

```text
KHÔNG resolve/match product identity      → đó là TASK-105D
KHÔNG thay TASK-105D
KHÔNG thay TASK-105B provider
KHÔNG thay TASK-105C provider
KHÔNG tự invent product mapping
KHÔNG tự invent price
KHÔNG mutate Tracking
```

Bổ sung, suy ra trực tiếp từ các quyết định đang có hiệu lực:

```text
KHÔNG đoán mã Public Purchase khi thiếu CrossSystemProductMapping
      (DEC-154 §5; docs/spec/TASK-105D-DATA-CONTRACT.md INV-43/INV-44)
KHÔNG coerce giá vắng thành 0            (DEC-103, DEC-151 §4)
KHÔNG backdate giá hiện tại cho đơn quá khứ (DEC-121, DEC-154 §9)
KHÔNG đổi namespace của identity vì price source đổi (P10)
KHÔNG gọi resolver/catalog/provider cho sale_date < CUTOVER_DATE
      (DEC-154 §2; data contract INV-46/INV-47)
```

## Vị Trí Trong Đồ Thị

```text
SALES
  └─ TASK-105D Product Identity Resolver
       ├─ TRACKING identity ───────────────┐
       │    └─ TASK-105C HistoricalVendorMin
       │          └─ absence + cross-map ─┼─ TASK-105B PublicPurchasePrice
       └─ PUBLIC_PURCHASE identity ────────┘
                         │
                         ▼
              TASK-105E  PRICE RESOLUTION COMPOSITION   ← task này
                         (P00–P11)
                         │
                         ▼
                   KpiPurchasePrice / TASK-108B
```

`TASK-105E` là **consumer** của `105D`, `105C`, `105B`. Không có cạnh ngược:
không task nào trong ba task đó consume output của `TASK-105E`. Đồ thị vẫn
acyclic.

## Acceptance Rules P00–P11 (hiện trạng — CHƯA phải Completion Gate)

Nguồn quy phạm: `DEC-154` §11 (đã sửa transcription `P00`/`P03`/`P11` tại
`DEC-155`/S034). Bảng dưới đây là **bản sao để đọc**; khi lệch, `DEC-154` §11
thắng.

| ID | Rule | Status |
|---|---|---|
| P00 | `sale_date < CUTOVER_DATE` + entry `HistoricalConfirmedRegistry` CONFIRMED → `HISTORICAL_CONFIRMED_REPORT`, bypass P01–P11; không có entry → Pending. P01–P11 chỉ áp dụng cho `sale_date >= CUTOVER_DATE` | NOT_TESTED |
| P01 | TRACKING + valid vendor candidates → `HistoricalVendorMin` | NOT_TESTED |
| P02 | sentinel `0` bị loại | NOT_TESTED |
| P03 | TRACKING + no valid vendor candidates + `CrossSystemProductMapping` CONFIRMED active → Public Purchase fallback, tra bằng `public_purchase_code` của chính mapping đó | NOT_TESTED |
| P04 | PUBLIC_PURCHASE identity → bypass `phist` | NOT_TESTED |
| P05 | Public Purchase lookup dùng `sale_date` | NOT_TESTED |
| P06 | no valid Public Purchase price → Pending | NOT_TESTED |
| P07 | current public price không silently backfill historical sale | NOT_TESTED |
| P08 | provenance `PUBLIC_PURCHASE_NO_TRACKING` được giữ | NOT_TESTED |
| P09 | provenance `PUBLIC_PURCHASE_NO_VENDOR_PRICE` được giữ | NOT_TESTED |
| P10 | identity không đổi chỉ vì price source đổi | NOT_TESTED |
| P11 | TRACKING + no valid vendor candidates + KHÔNG có `CrossSystemProductMapping` → Pending; không đoán mã Public Purchase | NOT_TESTED |

Toàn bộ `Status = NOT_TESTED` — chưa implementation, chưa evidence. Không
được đọc bảng này thành một Completion Gate; biến `P00–P11` thành gate thực
thi được là **công việc của một phiên Scope Lock/Completion Gate riêng**
cho task này.

## Phạm Vi Dự Kiến (Scope — DỰ THẢO, CHƯA LOCK)

- Composition/orchestration semantics `P00–P11`.
- Thứ tự ưu tiên nguồn giá và điều kiện chuyển nhánh.
- Provenance propagation, tối thiểu phân biệt `PUBLIC_PURCHASE_NO_TRACKING`
  và `PUBLIC_PURCHASE_NO_VENDOR_PRICE` (`DEC-154` §10).
- Ngữ nghĩa `Pending` ở tầng composition (phân biệt với `PENDING_PRODUCT` của
  `TASK-105D` và với absence của `TASK-105C`).
- Phân biệt **source failure** và **determined absence** (tiền lệ
  `CHECK-105C-17`) — hỏng nguồn không bao giờ trở thành "giá không tồn tại".
- Contract biên với `TASK-108B` cho `KpiPurchasePrice`.
- Nơi **duy nhất** được phép wire provider vào pipeline, khi có authority.

## Ngoài Phạm Vi Dự Kiến (Out of Scope — DỰ THẢO)

- Product identity resolution/matching (`TASK-105D`).
- Đọc/parse `phist` (`TASK-105C`), đọc/parse price file (`TASK-105B`).
- Tạo/sửa mapping, alias, cross-system mapping, registry lịch sử.
- `KpiPurchaseAdjustment` và mọi thứ thuộc `TASK-108B`.
- `TASK-105B-Q3` (chính sách giá 0 cho dòng phí) — blocker độc lập.
- Mọi thay đổi trên repo `Tracking`.

## Phụ Thuộc (Dependencies)

```text
TASK-105D  Completion Gate frozen + implemented   — CHƯA
TASK-105C  Scope/Completion Gate refrozen + implemented — CHƯA
TASK-105B  DONE (cần Public Purchase dataset thật + HB triggers) — CHƯA
Dữ liệu    PublicPurchaseSourceVersion thật, TrackingCatalogSnapshot,
           HistoricalConfirmedRegistry — CHƯA
```

`TASK-105E` **không thể** đạt Ready Gate trước khi ba task trên có contract
ổn định — nó điều phối chính chúng.

## Chặn (Blocks)

- `TASK-108B` trên dữ liệu thật không-Pending (blocker #4 của `TASK-108B`,
  nay đã có chủ ở mức ownership, chưa có ở mức implementation).
- Post-cutover price resolution production.

## Ready Gate

- [x] Task ID và phạm vi trách nhiệm do Owner cấp (`DEC-156` §5).
- [x] Ranh giới "KHÔNG làm" được ghi quy phạm.
- [x] Difficulty/Risk/Blast Radius/Effective Risk/agent tier đã chấm.
- [x] Review budget lineage đã cấp.
- [ ] Scope Lock được soạn và frozen.
- [ ] Completion Gate được soạn từ `P00–P11` thành assertion thực thi được,
      review và freeze bởi authority riêng.
- [ ] `TASK-105D` / `TASK-105C` / `TASK-105B` đạt trạng thái đủ để điều phối.
- [ ] Dữ liệu thật cho ít nhất một nhánh giá.

**Ready verdict:** `BLOCKED`. Không chuyển thẳng `PLANNED → IN_PROGRESS`.

## Completion Gate

**CHƯA SOẠN.** Sẽ được dựng từ `P00–P11` cộng các check về provenance,
source-failure-vs-absence, và idempotency/replay. Không được dùng bảng
`P00–P11` ở trên làm Completion Gate mà chưa qua một phiên soạn + freeze có
thẩm quyền.

## Điều Kiện Kích Hoạt Leo Thang (Escalation Triggers)

- Bất kỳ thiết kế nào yêu cầu `TASK-105E` tự map identity hoặc tự đoán mã.
- Bất kỳ nhánh nào biến giá vắng thành `0`.
- Bất kỳ nhánh nào để giá hiện tại chảy ngược vào đơn trước `CUTOVER_DATE`.
- Bất kỳ đề xuất nào gộp `TASK-105E` vào `TASK-105C` hoặc `TASK-105D` —
  đó là tái lập chính dependency tuyến tính mà `DEC-154` §13 đã gỡ.

## Đăng Ký File Đã Thay Đổi (Changed Files Registry)

Created:
- `docs/tasks/TASK-105E-price-resolution-composition.md` (S035/`DEC-156`)

Production implementation:
- Không có.

## Ghi Chú (Notes)

Không đọc `Status = PLANNED` cộng "Owner đã cấp task ID" thành `READY`,
`FROZEN`, `IN_PROGRESS`, `IMPLEMENTED` hay `DONE`. Owner cấp **quyền sở
hữu** cho một khoảng trống đã được công bố; việc soạn Scope Lock và
Completion Gate vẫn là công việc của một phiên riêng, và `DEC-156` §5 ghi rõ
"Không implement `TASK-105E` trong session này".
