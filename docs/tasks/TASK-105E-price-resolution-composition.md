# TASK-105E — Price Resolution Composition

## Metadata

Status:
IMPLEMENTED

Specification State:
SCOPE LOCK (SESSION 1) ĐÃ SOẠN — xem "Scope Lock — Session 1" bên dưới.
Completion Gate **vẫn chưa** được soạn thành assertion thực thi được và
**chưa** freeze bởi một authority riêng; `P00–P11` dưới đây đã có bằng chứng
thực thi (S061) nhưng **không** vì thế mà trở thành một Completion Gate đã
freeze. `IMPLEMENTED` ở đây đúng nghĩa vòng đời task: code đã tồn tại và chạy
được trên biên production, **chưa** qua Independent Review, **chưa** `DONE`.

Implementation Session 1:
S061 (2026-08-29), nhánh `claude/task-105e-price-composition-sjk4ee`,
base `740f396acb11cf279f303f09ea22dffd0ca95462`.
Bằng chứng: `docs/sessions/S061-task-105e-production-price-composition.md`.

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
| P00 | `sale_date < CUTOVER_DATE` + entry `HistoricalConfirmedRegistry` CONFIRMED → `HISTORICAL_CONFIRMED_REPORT`, bypass P01–P11; không có entry → Pending. P01–P11 chỉ áp dụng cho `sale_date >= CUTOVER_DATE` | PASS (E1) |
| P01 | TRACKING + valid vendor candidates → `HistoricalVendorMin` | NOT_APPLICABLE — nguồn `TASK-105C` `BLOCKED / NOT AUTHORIZED` |
| P02 | sentinel `0` bị loại | NOT_APPLICABLE — thuộc `phist` (`TASK-105C`), chưa có nguồn |
| P03 | TRACKING + no valid vendor candidates + `CrossSystemProductMapping` CONFIRMED active → Public Purchase fallback, tra bằng `public_purchase_code` của chính mapping đó | BLOCKED — điều kiện không thoả được (xem §"P01/P03" bên dưới); có test khẳng định nhánh KHÔNG chạy |
| P04 | PUBLIC_PURCHASE identity → bypass `phist` | PASS (E1) |
| P05 | Public Purchase lookup dùng `sale_date` | PASS (E1) |
| P06 | no valid Public Purchase price → Pending | PASS (E1) |
| P07 | current public price không silently backfill historical sale | PASS (E1) |
| P08 | provenance `PUBLIC_PURCHASE_NO_TRACKING` được giữ | PASS (E1) |
| P09 | provenance `PUBLIC_PURCHASE_NO_VENDOR_PRICE` được giữ | PASS (E1) — hằng số + bảng `PRICE_SOURCE_BY_RULE` tách khỏi `P08`; nhánh chưa có đường tới |
| P10 | identity không đổi chỉ vì price source đổi | PASS (E1) |
| P11 | TRACKING + no valid vendor candidates + KHÔNG có `CrossSystemProductMapping` → Pending; không đoán mã Public Purchase | PASS (E1) — bị bao trùm bởi `P03 BLOCKED`: identity TRACKING không mượn giá công khai trong MỌI trường hợp hiện nay |

Evidence: `tests/test_105e_price_composition.py` (43 test, PASS — S061).
Executed By: S061. Timestamp: 2026-08-29.

**Không được đọc bảng này thành một Completion Gate.** Bảng ghi trạng thái
THỰC THI của các acceptance rule, không phải một gate đã review + freeze.
Biến `P00–P11` thành gate thực thi được vẫn là **công việc của một phiên
Scope Lock/Completion Gate riêng** cho task này.

### `P01`/`P03` — vì sao nhánh fallback bị chặn

`P03` đòi "không có valid vendor candidate tại `sale_date`" — một *absence đã
xác định*: phải hỏi nguồn vendor rồi nhận về "không có". `TASK-105C` hiện
`BLOCKED / NOT AUTHORIZED`, nên nguồn ấy chưa tồn tại và câu hỏi chưa từng
được đặt ra. "Chưa hỏi" không phải "đã hỏi và không có"; đánh đồng hai thứ đó
là đúng phép suy diễn mà Scope của task này cấm (source failure ≠ determined
absence — tiền lệ `CHECK-105C-17`). Hệ quả quy phạm: một identity `TRACKING`
**không bao giờ** lấy giá Public Purchase trong kiến trúc hiện tại, kể cả khi
có `CrossSystemProductMapping` CONFIRMED và bảng giá công khai có đúng mã ấy.

### Nguồn Tracking đang được nối

`Reports History Reader V1` (S060, `ACCEPT_AFTER_REPAIR` + `INTEGRATED`) là
nguồn giá `TRACKING` DUY NHẤT được nối. Vị trí của nó trong bảng `P00–P11`
**chưa được quyết định bởi bất kỳ artifact frozen nào** — `DEC-154` §7 viết
trước khi reader tồn tại. Xem `OWNER_DECISION_REQUIRED` bên dưới.

## Scope Lock — Session 1 (S061, 2026-08-29)

Chỉ thị mở phiên "TASK-105E — PRODUCTION PRICE COMPOSITION, SESSION 1/2"
cấp thẩm quyền implementation cho lát cắt dưới đây. Phạm vi được soạn
TRƯỚC khi code và không mở rộng trong phiên.

### Trong phạm vi (ĐÃ THỰC HIỆN)

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
- Cơ chế thu thập nguồn tối thiểu: loader file capture (`app/modules/`,
  thuần đọc) + công cụ capture RTDB read-only (`tools/`, ngoài
  `app/modules/` theo `ADR-101`/`DEC-152` §6).
- Ngữ nghĩa snapshot/freeze: MỘT lần import = MỘT bộ bằng chứng đóng băng,
  mang đủ định danh nguồn để audit/mở lại (`PriceEvidenceSnapshot`).
- Múi giờ nghiệp vụ như một authority nạp từ config, fail-closed, không
  mặc định ngầm (`config/price_resolution.yaml`).

### Ngoài phạm vi (KHÔNG ĐỘNG TỚI)

- Product identity resolution/matching (`TASK-105D`).
- Đọc/parse `phist` (`TASK-105C`), đọc/parse price file (`TASK-105B`).
- Tạo/sửa mapping, alias, cross-system mapping, registry lịch sử.
- `KpiPurchaseAdjustment` và mọi thứ thuộc `TASK-108B`.
- `TASK-105B-Q3` (chính sách giá 0 cho dòng phí) — blocker độc lập.
- Mọi thay đổi trên repo `Tracking`.
- Mọi thay đổi business rule: `DEC-143`/`DEC-144`, `CUTOVER_DATE`, ngữ nghĩa
  `HistoricalVendorMin`/sentinel `0`, và toàn bộ fail-safe của Reports History
  Reader V1 — giữ nguyên, không sửa một byte.
- Batch 200, Dashboard, UI, redesign Product Identity, data warehouse, hàng
  chờ review thứ hai, deployment, merge nhánh mặc định.

### Bằng chứng phạm vi (S061)

Diff của phiên KHÔNG chạm: `tests/fixtures/golden/**`,
`tests/fixtures/baseline_snapshot.py`, `data/**`,
`app/modules/product/identity/**`,
`app/modules/pricing/{file_price_provider,price_engine,provider}.py`,
`app/modules/pricing/tracking_history/{reader,provider,snapshot}.py`,
`app/modules/kpi/**`, `app/modules/validation/**`, repo `Tracking`.

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
- [x] Scope Lock được soạn (S061, lát cắt Session 1 — **soạn, chưa freeze**).
- [ ] Completion Gate được soạn từ `P00–P11` thành assertion thực thi được,
      review và freeze bởi authority riêng.
- [x] `TASK-105D` đủ để điều phối (`DONE`, `DEC-162`).
- [ ] `TASK-105C` đủ để điều phối — **KHÔNG**, vẫn `BLOCKED / NOT AUTHORIZED`;
      hệ quả là `P01`/`P03`/`P09` không có đường tới (xem §"P01/P03").
- [x] `TASK-105B` đủ để điều phối ở mức provider (`FilePriceProvider` frozen,
      nạp qua `PublicPurchaseSourceVersion.validated_price_rows()`) — dataset
      production thật vẫn CHƯA có.
- [ ] Dữ liệu thật cho ít nhất một nhánh giá — **CHƯA**
      (`WAITING_REAL_POST_CUTOVER_DATA`).

**Ready verdict (Session 1):** implementation được cấp phép tường minh bởi
chỉ thị mở phiên, cho đúng lát cắt trong Scope Lock ở trên. `Ready Gate` đầy
đủ của task **vẫn chưa đóng** — Completion Gate chưa freeze và chưa có dữ liệu
post-cutover thật; vì thế task là `IMPLEMENTED`, **không** phải `DONE`.

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

## `OWNER_DECISION_REQUIRED` (mở, KHÔNG chặn Session 1)

1. **Vị trí của Reports History Reader V1 trong `P00–P11`.** `DEC-154` §7 viết
   trước khi reader tồn tại và không có ô cho nó; S060 tự nhận "bổ sung một
   NGUỒN cho nhánh TRACKING" mà không định vị so với `P01`. S061 đặt reader
   làm nguồn `TRACKING` duy nhất được nối, theo luồng mà chỉ thị mở phiên §5
   mô tả. Hôm nay lựa chọn ấy **không quan sát được** (P01 không có nguồn, P03
   bị chặn), nên nó chưa thay đổi hành vi nào. Nó **trở nên quan sát được**
   ngay khi `TASK-105C` có nguồn thật. **Retrigger: trước khi `TASK-105C`
   được cấp phép implementation.**
2. **Vận hành công cụ capture.** `tools/tracking/capture_purchase_price_history.py`
   nhận `--database-url` và đọc token từ biến môi trường `TRACKING_RTDB_TOKEN`;
   không credential nào được nhúng hay bịa. Ai chạy, ở đâu, với quyền gì, và
   file capture có được commit vào repo hay không — là quyết định vận hành của
   Owner.

## `DEFERRED_BY_MINIMAL_FIX`

| ID | Nội dung | Lý do | Fail-safe hiện tại | Retrigger |
|---|---|---|---|---|
| `D-01` | Không có công cụ capture cho `TrackingCatalogSnapshot` | Hình dạng export danh mục thuộc `TASK-105D`/vận hành Tracking; loader strict đã có | Catalog vắng → `IDENTITY_SOURCES_UNAVAILABLE` → Pending → Review Queue | Lần import post-cutover thật đầu tiên |
| `D-02` | Chưa có `PublicPurchaseSourceVersion` production | DONE blocker của `TASK-105B`; `HB-105B-03/05/10` phải đóng TRƯỚC lần nạp dataset thật | PP vắng → `PUBLIC_PURCHASE_SOURCE_UNAVAILABLE` → Pending | Khi Owner cấp dataset Public Purchase thật |
| `D-03` | `P03`/`P09` chưa có đường tới | `TASK-105C` `BLOCKED / NOT AUTHORIZED` | TRACKING unresolved → Pending, không mượn giá công khai | `TASK-105C` được cấp phép |
| `D-04` | `PriceResolutionRecord` chưa đi vào `ReviewItem` | Mở rộng shape `ReviewItem`/`WorkingLine` thuộc `TASK-110`/`TASK-201` | Bản ghi đầy đủ đi BÊN CẠNH kết quả (`composition.records`); Review Queue vẫn phủ 100% dòng Pending | `TASK-305` (màn hình review) hoặc `TASK-201` (persistence) |

## Đăng Ký File Đã Thay Đổi (Changed Files Registry)

Created:
- `docs/tasks/TASK-105E-price-resolution-composition.md` (S035/`DEC-156`)

Production implementation (S061):
- `app/modules/pricing/resolution/__init__.py` (mới)
- `app/modules/pricing/resolution/sources.py` (mới)
- `app/modules/pricing/resolution/composition.py` (mới)
- `app/modules/pricing/tracking_history/capture_file.py` (mới)
- `tools/tracking/__init__.py` (mới)
- `tools/tracking/capture_purchase_price_history.py` (mới)
- `config/price_resolution.yaml` (mới)
- `app/composition.py` (sửa — nạp nguồn post-cutover, `build_price_composition`)
- `app/pipeline.py` (sửa — tham số DI `price_composition`, mặc định `None`)
- `app/modules/domain/models.py` (sửa — hai hằng số provenance `P08`/`P09`)

Test (S061):
- `tests/test_105e_price_composition.py` (mới, 43 test)
- `tests/test_golden_baseline.py` (sửa — khoá chữ ký `run_import`, +1 tham số)

## Ghi Chú (Notes)

`Status = IMPLEMENTED` KHÔNG phải `DONE`. Completion Gate của task chưa được
soạn thành assertion thực thi được và chưa freeze bởi một authority riêng;
capability còn cần Independent Review (Session 2) và dữ liệu post-cutover
thật. Bảng `P00–P11` ở trên ghi trạng thái THỰC THI, không phải một gate đã
freeze — không được đọc nó thành Completion Gate.

Golden PASS **không** đồng nghĩa capability DONE: Golden chứng minh MỘT đường
E2E (pre-cutover, Owner-confirmed), còn nhánh post-cutover mới chỉ có bằng
chứng qua focused integration fixture cộng một lần chạy production seam trên
dữ liệu post-cutover với nguồn giá đúng như trên đĩa hôm nay.
