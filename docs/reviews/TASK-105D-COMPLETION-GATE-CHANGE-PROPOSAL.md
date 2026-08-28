# TASK-105D — COMPLETION GATE CHANGE PROPOSAL #1

Artifact Type:
`COMPLETION GATE CHANGE PROPOSAL` theo khuôn
`governance/core/TASK_COMPLETION_GATE_STANDARD.md` → "Kiểm soát thay đổi Gate".
Đây là **bản ghi thay đổi gate**, không phải Owner Decision (Owner Decision là
`DEC-157`), không phải freeze verdict, không phải implementation.

Session:
`docs/sessions/S037-task-105d-gate-revision.md`

Base SHA:
`1676e1d173ff6afdbbaa2cedcf07fc06346955ce`

Branch:
`task/task-105d-gate-revision`

Source freeze attempt:
`docs/reviews/TASK-105D-FREEZE-FINALIZATION-REVIEW.md` — Freeze Finalization
attempt #1 (`S036`, 2026-08-28), reviewed base SHA
`9cd871488a6baebf6b80737f42e2137a27887cef`, verdict `FAIL` (5 BLOCKING /
5 HARDENING / 3 OUT_OF_SCOPE).

Authority:
`DEC-157` (Owner Decision — giữ đúng 32 gate; `V4.1` §8 Option C).
`governance/core/V4_1_POLICY_FREEZE.md` §7 (Review Finding Action Gate), §11
(Artifact Internal Precedence), §12 (State Authority Matrix — `FROZEN` chỉ
thuộc một phiên Freeze Finalization có thẩm quyền).
`governance/core/TASK_COMPLETION_GATE_STANDARD.md` (Kiểm soát thay đổi Gate).

Ghi chú artifact budget (`V4.1` §10): đây là artifact governance thứ **7** của
lineage `TASK-105D`, thuộc diện `OWNER APPROVAL REQUIRED`. Approval là chỉ thị
tường minh của Owner khi mở phiên này ("ghi Completion Gate Change Proposal
canonical"; "Tạo canonical COMPLETION GATE CHANGE PROPOSAL theo governance").
Ghi lại để phiên sau không phải suy luận, theo tiền lệ `DEC-156`/`S036`.

---

## VERDICT

```text
GATE REVISION #1 — ÁP DỤNG ĐẦY ĐỦ

Gate count trước / sau        : 32 / 32        (KHÔNG ĐỔI)
BLOCKING F-01…F-05            : 5 / 5 đã xử lý
Finding ma trận (G04/G05/G22) : 3 / 3 đã xử lý
HARDENING nạp thêm            : H-02 (một phần), H-03, H-04  — không bắt buộc
HARDENING còn mở              : H-01 ĐÃ ĐÓNG qua G22; H-05 CÒN MỞ (đổi data
                                contract — ngoài thẩm quyền phiên gate revision)
32/32 có assertion tường minh : CÓ
32/32 có fixture/evidence     : CÓ
32/32 có PASS + FAIL condition: CÓ
Completion Gate frozen        : KHÔNG
TASK-105D READY               : KHÔNG
Repair Cycle                  : KHÔNG mở  (2 allowed / 0 used / 2 remaining)
production / test code changed: KHÔNG
```

Phiên này **không** freeze. `V4.1` §12 tách thẩm quyền `FROZEN` khỏi phiên
viết gate; một phiên Freeze Finalization retry phải re-review **toàn bộ** gate
set đã sửa trước khi ghi `FROZEN`.

---

## 1. Owner decision được áp dụng

### 1.1 Owner Decision A — GATE COUNT

```text
Giữ ĐÚNG 32 Completion Gate. KHÔNG mở rộng gate set vượt 32.
F-03 / F-04 / F-05 phải được tích hợp vào các gate hiện có phù hợp thay vì
thêm gate mới, trừ khi phát hiện contradiction không thể giải quyết mà không
đổi count — khi đó STOP và báo Owner.
```

**Kết quả: KHÔNG phát hiện contradiction nào buộc phải đổi count.** Cả ba
finding đều tìm được gate chủ phù hợp về mặt ngữ nghĩa, không phải nhét bừa:

| Finding | Gate nhận | Vì sao đây là gate đúng về ngữ nghĩa |
|---|---|---|
| `F-03` actor | `G20` + `G21` | `G20` vốn đã là gate "command bị từ chối, KHÔNG ghi gì" (`expected_version` sai). Điều kiện tiên quyết `actor_id` có **đúng hình dạng đó**. `G21` vốn là gate provenance — nội dung actor trong audit và cấm từ "authenticated" là nội dung provenance. |
| `F-04` unified PP source | `G28` + `G21` | `G28` vốn khẳng định "identity `PUBLIC_PURCHASE` hợp lệ không cần Tracking giả" — nó là gate sở hữu **tính hợp lệ của identity Public Purchase**, nên contract nguồn của identity đó thuộc về nó. `ResolutionBinding`/replay là mở rộng tự nhiên của provenance (`G21`). |
| `F-05` catalog drift | `G10` | `G10` vốn là gate "mapping đã persist reuse qua import/run mới" — tức gate **vòng đời của mapping qua các lần capture**. Drift (rename / biến mất / gộp mã / capture hỏng) chính là tập câu hỏi về vòng đời đó. |

### 1.2 Owner Decision B — DIVERGENCE

```text
V4.1 §8 Option C — CONTINUE WITH EXPLICIT JUSTIFICATION.
Lineage TASK-105D được tiếp tục qua: (1) Gate Revision này; (2) một Freeze
Finalization retry độc lập.
Review divergence lại NGAY SAU freeze verdict.
KHÔNG mở TASK-105D implementation trước divergence review tiếp theo.
```

Ghi canonical tại `DEC-157` §2 và `PROJECT/REVIEW_BUDGET_LEDGER.md`.

---

## 2. F-01 — OR-02 PROPAGATION CONTRADICTION

Original check (nguyên văn, khối "Định nghĩa vận hành bắt buộc" của task file):

```text
AMBIGUOUS
    = resolution_method KHÔNG thuộc tập auto-resolve đóng (ALIAS_EXACT,
      ALIAS_AID_UNIQUE, CATALOG_EXACT_UNIQUE — data contract §6.6).
    Ba nguồn ambiguity, mỗi nguồn một fixture bắt buộc: MULTIPLE_EXACT,
      CROSS_NAMESPACE_TIE, ONLY_SIMILARITY.
```

Và `CHECK-105D-06` (nguyên văn): "… Ba fixture: MULTIPLE_EXACT,
CROSS_NAMESPACE_TIE, ONLY_SIMILARITY".

Proposed change (ĐÃ ÁP DỤNG):

```text
tập auto-resolve (TẬP ĐÓNG — ĐÚNG HAI PHƯƠNG THỨC)
    ALIAS_EXACT
    CATALOG_EXACT_UNIQUE

AMBIGUOUS
    = resolution_method KHÔNG thuộc tập auto-resolve đóng ngay trên.
    BỐN nguồn ambiguity, mỗi nguồn một fixture bắt buộc:
      (a) MULTIPLE_EXACT  (b) CROSS_NAMESPACE_TIE  (c) ONLY_SIMILARITY
      (d) ALIAS_AID_UNIQUE — candidate-only theo DEC-156/OR-02; INV-28b.
```

`CHECK-105D-06` đổi "Ba fixture" → "**BỐN** fixture", với ghi chú rằng
assertion chi tiết của case (d) nằm ở `CHECK-105D-23` và cố ý không nhân đôi.

Reason:
Đây là **hoàn tất propagation một Owner Decision đã có**, không phải quyết định
nghiệp vụ mới. `DEC-156` §2 sửa `INV-28` thành đúng hai phương thức và thêm
`INV-28b`; data contract §6.6 và §17.2 đã mang ngữ nghĩa mới; chỉ khối định
nghĩa vận hành trong task file còn ở trạng thái trước ratification. `S035` đã
sửa Authority, Resolution Order và `CHECK-105D-23` nhưng không chạm khối này.

Risk nếu không sửa:
`ALIAS_AID_UNIQUE` không phải AMBIGUOUS theo định nghĩa trong chính task file
⇒ `G06` không ràng buộc nó ⇒ một implementation auto-resolve `ALIAS_AID_UNIQUE`
**PASS `G06` trong khi FAIL `G23`**. Hai gate cho hai kết luận trái ngược trên
cùng một hành vi; reviewer buộc phải hỏi lại Owner gate nào thắng — đúng điều
kiện freeze bị vi phạm.

Impact:
- Invariant bị tác động: `INV-28`, `INV-28b`, `INV-01`.
- Gate bị sửa: khối định nghĩa vận hành (non-row operational definition),
  `CHECK-105D-06`.
- Gate được làm nhất quán mà không sửa: `CHECK-105D-23` (đã đúng từ `S035`).
- Không đổi gate count. Không đổi implementation.

Sửa non-row operational definition:
**CÓ.** Khối "Định nghĩa vận hành bắt buộc" (không phải một dòng gate) đã bị
sửa. Ghi tường minh tại đây theo yêu cầu §10 của brief. Ngoài ra khối đó được
bổ sung một mục mới `tập auto-resolve` (tách ra để không phải nhắc lại danh
sách ở nhiều chỗ) và mục `normal action / interaction` (xem F-06/H-03 bên dưới).

Audit stale text toàn `TASK-105D` + Data Contract:

| Vị trí | Trạng thái trước | Sau |
|---|---|---|
| Task file — khối định nghĩa vận hành | `ALIAS_AID_UNIQUE` trong tập auto-resolve; "Ba nguồn" | ĐÃ SỬA |
| Task file — `CHECK-105D-06` | "Ba fixture" | ĐÃ SỬA → bốn |
| Task file — "Resolution Order và Kết Quả" | "Tracking deterministic unique match: **có thể** auto-resolve" | ĐÃ SỬA → assertion `CATALOG_EXACT_UNIQUE` + chiều âm `INV-29` |
| Task file — "Human Confirmation và Batch UX Contract" | "thao tác bình thường" không quy chiếu định nghĩa | ĐÃ SỬA → `confirmation_action` + trỏ gate |
| Task file — "Phụ Thuộc" mục **Auth** | "(`OR-03`, chờ Owner ratification)" — trái `DEC-156` | ĐÃ SỬA → APPROVED FOR PHASE 1 + trỏ gate |
| Data contract §6.6 / §17.2 / §15 / §6.5 | Đã đúng từ `S034`+`DEC-156` | KHÔNG SỬA |

Không còn text nào trong hai artifact coi `ALIAS_AID_UNIQUE` là auto-resolve.

---

## 3. F-02 — G05 PHẢI LÀ ASSERTION

Original check:

```text
| CHECK-105D-05 (G05) | Deterministic unique match có thể auto-resolve | NOT_TESTED | E2 |
```

Proposed change (ĐÃ ÁP DỤNG) — `CHECK-105D-05`:

```text
Chiều DƯƠNG — phải auto-resolve:
  Setup : catalog có ĐÚNG MỘT entry khớp exact (theo raw_identity_key hoặc
          normalized_matching_aid), và chỉ trong MỘT namespace.
  Assert: count(confirmation_action) == 0
          resolution_method == CATALOG_EXACT_UNIQUE
          outcome == RESOLVED(namespace, source_product_code)
          mapping_source == DETERMINISTIC_CATALOG_MATCH

Chiều ÂM — cấm auto-resolve (INV-29):
  Setup : khớp exact ở CẢ HAI namespace.
  Assert: resolution_method == CROSS_NAMESPACE_TIE
          KHÔNG auto-resolve; outcome ∈ {REQUIRES_CONFIRMATION, PENDING_PRODUCT}
```

Reason:
"Có thể" không loại trừ điều gì: một implementation không bao giờ auto-resolve
`CATALOG_EXACT_UNIQUE` PASS, một implementation auto-resolve cũng PASS. Gate
không thể FAIL ⇒ không deterministic ⇒ vi phạm điều kiện freeze. Ngữ nghĩa quy
phạm đã tồn tại sẵn (data contract §1: "DETERMINISTIC (khớp duy nhất) → 0
confirmation_action"; §6.6 tập auto-resolve; `INV-29`) — thay đổi này chỉ **chép
ngữ nghĩa đã có vào gate**, không tạo luật mới.

Không dùng wording framework-specific: assertion đếm `confirmation_action`
(domain command, §17.1), không đếm click/phím.

Risk nếu không sửa:
Case C bắt buộc của brief (`CATALOG_EXACT_UNIQUE → 0 confirmation_action`) và
yêu cầu UX §7 duy nhất không có gate assert. Một implementation bắt xác nhận
mọi thứ vẫn PASS 32/32 trong khi phá mục tiêu vận hành trung tâm của task.

Impact:
- Invariant bị tác động: `INV-28`, `INV-29`.
- Gate bị sửa: `CHECK-105D-05` (E2 giữ nguyên).
- Không đổi gate count. Không đổi implementation.

---

## 4. F-03 — ACTOR ASSERTION

Original check:
**Không có.** Quét toàn bộ 32 dòng gate của bản trước: 0 lần xuất hiện của
`actor`. `G21` liệt kê `raw / tuple / source / version / method` — không actor.
`G18` nói "giữ old/new mapping" — không actor.

Proposed change (ĐÃ ÁP DỤNG) — nạp vào **hai** gate hiện có, không thêm gate:

`CHECK-105D-20` (G20) — Phần B, điều kiện tiên quyết của command:

```text
Mọi command làm đổi state — CONFIRM_MAPPING | REJECT_CANDIDATE |
    CONFIRM_CROSS_SYSTEM | SET_PENDING | CORRECT_* | BOOTSTRAP_MAPPING |
    MARK_STALE | REPIN_REPORT — THIẾU actor_id thì BỊ TỪ CHỐI:
      0 event được ghi, 0 mapping đổi, version KHÔNG tăng.
KHÔNG có giá trị mặc định. CẤM "system", CẤM anonymous, CẤM suy ra từ biến
    môi trường / OS user / config / hằng số trong mã (INV-72).
actor_id rỗng hoặc chỉ chứa khoảng trắng = THIẾU.
```

`CHECK-105D-21` (G21) — Phần B, nội dung và ngữ nghĩa:

```text
MappingAuditEvent.actor_id REQUIRED, non-empty, IMMUTABLE (§13.1).
Mọi nơi hiển thị/ghi actor phải nêu rõ đây là KHAI BÁO CỦA NGƯỜI VẬN HÀNH.
KHÔNG artifact/output/báo cáo/log/bề mặt điều khiển nào do TASK-105D sinh ra
    được mô tả actor Phase 1 bằng "authenticated" / "authenticated user" /
    "danh tính đã xác thực" (INV-73).
    Assertion thực thi được: test quét văn bản trên artifact/chuỗi hiển thị do
    task sinh ra, khẳng định 0 lần xuất hiện gắn với actor; cộng một mục
    checklist trong Independent Review.
Điều gate này KHÔNG khẳng định: rằng người thao tác thật sự là actor đã khai.
    Đó là CAPABILITY BOUNDARY của Phase 1 (§12.1), phải ghi đúng, không che.
```

`CHECK-105D-18` (G18) mang một dòng trỏ chéo (`actor_id` REQUIRED trên event)
để reviewer đọc gate audit không phải tự suy; assertion đầy đủ thuộc `G20`/`G21`.

Fixture / evidence cụ thể (ghi theo yêu cầu §5 của brief):
- `G20` fixture (2): với **mỗi** loại command đổi state, gửi thiếu `actor_id`
  → bị từ chối, `current_revision()` không đổi.
- `G20` fixture (3): `actor_id = ""` và `actor_id = "   "` → cùng bị từ chối.
- `G21` fixture (2): audit event thiếu `actor_id` không tồn tại được trong log.
- `G21` fixture (3): test quét văn bản cho `INV-73`.
- Evidence Level: `G20` = `E2` (giữ nguyên); `G21` **nâng `E1` → `E2`**.

Reason:
`OR-03` được Owner phê chuẩn tại `DEC-156` §3 với ba ràng buộc (`actor`
REQUIRED; cấm gọi là authenticated; cấm default im lặng). Điều kiện freeze
"Owner Ratification fully reflected" đòi mỗi ràng buộc phải có gate.

Risk nếu không sửa:
Một implementation đặt `actor_id = "system"` khi người vận hành không khai báo,
hoặc một artifact mô tả actor là "authenticated user", PASS 32/32 trong khi vi
phạm trực tiếp một Owner Decision. Với `ADR-102` bắt buộc `ChangedBy` trên mọi
thay đổi do người kích hoạt, đây là mất khả năng truy trách nhiệm trên đường
lỗi dẫn tới KPI/lương. Case S là case đối kháng bắt buộc.

Impact:
- Invariant được bảo vệ (trước: không gate nào): `INV-72`, `INV-73`.
- Gate bị sửa: `CHECK-105D-20`, `CHECK-105D-21`, `CHECK-105D-18` (trỏ chéo).
- Evidence Level nâng: `CHECK-105D-21` `E1 → E2`. Nâng, không hạ.
- Không đổi gate count. Không đổi implementation.

---

## 5. F-04 — UNIFIED PP SOURCE / REPLAY BINDING

Original check:
**Không có.** Quét 32 dòng gate của bản trước: 0 lần xuất hiện của `publish`,
`immutable`, `version_id`, `pp_version`, `binding`, `replay`.

Proposed change (ĐÃ ÁP DỤNG) — nạp vào **hai** gate hiện có, không thêm gate.

`CHECK-105D-28` (G28) — Phần B, contract nguồn Public Purchase:

```text
B1 (INV-06) MỌI price_rows[*].product_key PHẢI tồn tại trong identity_rows của
    CÙNG một PublicPurchaseSourceVersion. Vi phạm = LỖI LOAD tại publish/load —
    KHÔNG phải lỗi lúc tính giá/KPI/lương, KHÔNG phải Pending.
B2 (INV-02) Loader identity projection STRICT: thiếu khối / sai tên khối /
    khối rỗng / khoá top-level lạ → LỖI LOAD, KHÔNG phải "danh mục rỗng".
B3 (INV-03) Đường hợp lệ DUY NHẤT là PublicPurchaseSourceLoader riêng;
    assertion: diff trên app/modules/pricing/file_price_provider.py == RỖNG.
B4 (INV-04/05/09) product_code unique; fold(product_code) unique; alias không
    trùng product_code của sản phẩm KHÁC (sau fold). Vi phạm = lỗi load.
B5 (INV-07) Published version IMMUTABLE: đổi product_name/aliases KHÔNG đổi
    kết quả report đã ghim version.
B6 (OR-01) MỘT canonical versioned source, HAI projection của CÙNG một
    PublicPurchaseSourceVersion / source-version lineage. Một implementation
    vận hành HAI nguồn Public Purchase độc lập FAIL gate này, KỂ CẢ khi mọi
    assertion khác PASS.
```

`CHECK-105D-21` (G21) — Phần C, binding/replay:

```text
ResolutionBinding ghim ĐỦ CẢ BỐN: pp_version_id, tracking_capture_id,
    mapping_store_revision, registry_revision. CẤM ghim từng phần (INV-55).
Replay một report = đọc lại đúng bộ binding của nó → kết quả GIỐNG HỆT lần
    chạy đầu, BẤT KỂ store/catalog/giá đã đổi thế nào sau đó (INV-56).
Thiếu BẤT KỲ thành phần binding nào → LỖI CỨNG. KHÔNG fallback "mới nhất",
    KHÔNG trả Pending (INV-57).
```

Đối chiếu năm bảo vệ tối thiểu mà brief §6 yêu cầu:

| Yêu cầu brief §6 | Gate | Assertion |
|---|---|---|
| 1. Identity + Price cùng source-version lineage | `G28` B6 | Hai projection của cùng `PublicPurchaseSourceVersion`; hai nguồn độc lập = FAIL |
| 2. Published version immutable | `G28` B5 | `INV-07` — đổi name/alias không đổi report đã ghim |
| 3. `price.product_key` ∈ identity projection cùng version | `G28` B1 | `INV-06`, vi phạm = lỗi load |
| 4. report/snapshot binding đủ để replay cùng version | `G21` C | `INV-55`/`INV-56`/`INV-57` |
| 5. Không PASS nếu tạo hai independent operational sources | `G28` B6 | Điều kiện FAIL tường minh |

Ranh giới scope (theo brief §6 — "Chỉ gate 105D phần identity/shared-contract
boundary"):
Ba thứ được gate đều nằm ở phía `TASK-105D`: (a) loader projection identity
strict; (b) `INV-06` thi hành tại publish/load; (c) `ResolutionBinding` ghim
`pp_version_id` và replay bất biến. **Không** kéo implementation `TASK-105B`
vào scope — `INV-03` chỉ assert rằng `file_price_provider.py` **không bị sửa**,
tức bảo vệ trạng thái FROZEN của nó chứ không mở rộng phạm vi sang nó.

Reason:
`OR-01` được Owner phê chuẩn tại `DEC-156` §1. `INV-02` đã được `S036` xác
minh độc lập trên mã nguồn thật (`file_price_provider.py:92-94` — `from_yaml`
bỏ qua mọi khoá top-level ngoài `prices` **trong im lặng**), nên rủi ro là có
thật, không phải suy đoán.

Risk nếu không sửa:
Một implementation PASS 32/32 trong khi vận hành hai nguồn Public Purchase độc
lập và làm mất version/replay binding — đúng lỗ hổng `HB-154-02` mà `S034` đã
đóng ở tầng contract. Case T là case đối kháng bắt buộc.

Impact:
- Invariant được bảo vệ (trước: không gate nào): `INV-02`…`INV-10`,
  `INV-55`…`INV-57`.
- Gate bị sửa: `CHECK-105D-28`, `CHECK-105D-21`.
- Evidence Level: `G28` = `E2` (giữ nguyên); `G21` `E1 → E2` (đã nêu ở F-03).
- Không đổi gate count. Không đổi implementation.

---

## 6. F-05 — CATALOG DRIFT

Original check:
**Không có.** Quét 32 dòng gate của bản trước: 0 lần xuất hiện của `STALE`,
`rename`, `đổi tên`, `biến mất`.

Proposed change (ĐÃ ÁP DỤNG) — nạp vào **một** gate hiện có
(`CHECK-105D-10`, gate vòng đời/persistence của mapping), không thêm gate:

```text
B1 (INV-13) tracking_code GIỮ NGUYÊN, name/alt ĐỔI → mapping đã confirm VẪN
    hợp lệ; ALIAS_EXACT; 0 confirmation_action; status KHÔNG chuyển STALE.
B2 (INV-14a/b) Sản phẩm vắng khỏi capture mới:
    (a) mapping lịch sử KHÔNG bị vô hiệu hoá, KHÔNG bị xoá, KHÔNG tự PENDING;
    (b) report đã ghim capture CŨ replay ra kết quả GIỐNG HỆT.
B3 (INV-14c) Identity MỚI chỉ khớp mã đã biến mất → STALE +
    MAPPING_STALE_TARGET_ABSENT; cần confirmation; KHÔNG auto-resolve.
B4 (INV-16) Mã bị gộp qua alias.map → KHÔNG tự chuyển mapping đã confirm sang
    mã chính; sinh MARK_STALE + đề xuất mã chính làm candidate #1.
B5 (INV-12) capture_status == FAILED → LỖI CỨNG; resolver TỪ CHỐI chạy.
    KHÔNG đọc thành "sản phẩm không tồn tại", KHÔNG thành Pending.
B6 (INV-15) Catalog HIỆN TẠI KHÔNG BAO GIỜ viết lại identity LỊCH SỬ.
```

Đối chiếu bốn yêu cầu của brief §7:

| Yêu cầu brief §7 | Assertion |
|---|---|
| A. TRACKING rename → mapping vẫn valid | `B1` |
| B. Product vắng board → mapping lịch sử không tự mất hiệu lực | `B2(a)` |
| C. Catalog hiện tại không retroactively rewrite confirmed identity | `B6` (+ `B2(b)` cho replay) |
| D. Stale catalog / capture failure semantics nhất quán data contract | `B3`, `B4`, `B5` |

Không mutate Tracking: mọi fixture của Phần B chạy với một Tracking fake
ghi-nhận-mọi-lệnh-ghi và assert số lệnh ghi `== 0` — bất biến cấm-ghi vẫn
thuộc `CHECK-105D-17`, không nhân đôi ở `G10`.

Reason:
Data contract đã định nghĩa đầy đủ cơ chế (`status = STALE` §6.4; event
`MARK_STALE` §13.2; `reason_code = MAPPING_STALE_TARGET_ABSENT` §5) nhưng
không check nào yêu cầu chúng hoạt động. Cases O và P là case đối kháng bắt
buộc và cả hai đều `KHÔNG ĐẠT` ở bản trước.

Risk nếu không sửa:
Tracking là hệ thống ngoài; `DEC-147` §3 R4 xác nhận `board` sửa/xoá được bởi
nhiều tài khoản. Một implementation vô hiệu hoá mapping đã confirm khi capture
mới thiếu mã đó sẽ PASS 32/32, đồng thời đẩy mọi đơn hàng lịch sử của sản phẩm
đó về Pending hoặc bị remap — vi phạm `INV-15` qua một con đường không gate nào
chặn. `INV-12` là biến thể nguy hiểm hơn: một lần capture hỏng bị đọc thành
"sản phẩm không tồn tại".

Impact:
- Invariant được bảo vệ (trước: không gate nào): `INV-12`, `INV-13`, `INV-14`,
  `INV-15`, `INV-16`.
- Gate bị sửa: `CHECK-105D-10`.
- Evidence Level nâng: `CHECK-105D-10` `E1 → E2` (đường lỗi identity lịch sử /
  replay). Nâng, không hạ.
- Không đổi gate count. Không đổi implementation.

---

## 7. G22 VÀ CÁC GATE CHƯA TESTABLE / CHƯA DETERMINISTIC

Ma trận `S036`: `testable 30/32` (thiếu `G05`, `G22`); `deterministic 29/32`
(thiếu `G04`, `G05`, `G22`). `G05` đã xử lý ở F-02. Còn `G22` và `G04`:

### 7.1 `CHECK-105D-22` (G22) — H-01

Original check:

```text
| CHECK-105D-22 (G22) | Core batch flow thao tác hoàn toàn bằng bàn phím | NOT_TESTED | E1 |
```

Vấn đề: bề mặt áp dụng **không xác định**. `ADR-101` đặt UI ngoài Phase 1
("Toàn bộ Phase 1 là thư viện Python thuần chạy được bằng CLI"). Là
`REQUIRED`/`E1`, gate hoặc vacuous (CLI thì mọi thao tác đều bằng bàn phím)
hoặc `NOT_TESTED` vĩnh viễn — reviewer không tự phân biệt được. Theo
`TASK_COMPLETION_GATE_STANDARD`, một `REQUIRED` check `NOT_TESTED` chặn `DONE`
trừ khi được đánh `NOT_APPLICABLE` kèm lý do hợp lệ; chưa có lý do nào được ghi.

Proposed change (ĐÃ ÁP DỤNG): **ràng buộc gate vào bề mặt Phase 1 THẬT**:

```text
(a) Cả BỐN confirmation_action command, cùng với xem candidate/evidence và
    duyệt hết một batch, thực thi được HOÀN TOÀN qua bề mặt CLI/API dòng lệnh,
    trong môi trường KHÔNG display và KHÔNG thiết bị trỏ (test headless).
(b) app/modules/product/** KHÔNG import thư viện GUI/web/pointer-event nào;
    KHÔNG domain operation nào cần sự kiện chuột/chạm để hoàn tất.
(c) KHÔNG confirmation_action nào chỉ tiếp cận được qua bề mặt điều khiển
    bằng con trỏ.
Gate KHÔNG được đánh NOT_APPLICABLE và KHÔNG được để NOT_TESTED với lý do
"Phase 1 chưa có UI".
```

Reason:
Giữ nguyên **yêu cầu** keyboard-first (không hạ tiêu chuẩn) nhưng phát biểu nó
trên bề mặt tồn tại thật, nên nó test được ngay hôm nay. Đây là lựa chọn chặt
hơn `NOT_APPLICABLE`: `NOT_APPLICABLE` sẽ bỏ hẳn một yêu cầu Owner đã đặt.

Risk nếu không sửa:
`G22` chặn `DONE` vĩnh viễn hoặc bị đánh `NOT_APPLICABLE` tuỳ tiện; cả hai đều
làm gate set không freeze được.

Impact: `H-01` **ĐÓNG**. Gate `E1` giữ nguyên. Không đổi gate count.

### 7.2 `CHECK-105D-04` (G04) — H-03

Original check:

```text
| CHECK-105D-04 (G04) | Alias đã confirm = 0 interaction | NOT_TESTED | E1 |
```

Vấn đề: "interaction" là thuật ngữ **thứ ba** bên cạnh `confirmation_action`
(§17.1) và "normal action". Đọc theo nghĩa đen ("0 interaction") thì cả việc
mở màn hình batch cũng vi phạm. `G24` phát biểu cùng bất biến chính xác hơn,
khiến `G04` vừa dư thừa vừa mơ hồ.

Proposed change (ĐÃ ÁP DỤNG):

```text
Store có mapping CONFIRMED cho K. Một lời gọi resolve MỘT identity K:
  count(confirmation_action cho K) == 0
  resolution_method == ALIAS_EXACT
  0 MappingAuditEvent mới, 0 mapping record mới, 0 lệnh ghi vào store.
Ranh giới với G24: G04 kiểm READ PATH của MỘT lời gọi (đọc-không-ghi);
G24 kiểm mức BATCH N>=2 + current_revision() không đổi.
```

Kèm sửa khối định nghĩa vận hành: mục `normal action` mở rộng thành
`normal action / interaction`, tuyên bố cả hai cụm là đồng nghĩa
`confirmation_action` và không còn được dùng trong gate mà không quy chiếu.

Reason:
Bỏ thuật ngữ thứ ba, đồng thời **giữ** `G04` với một invariant riêng
(đọc-không-ghi) thay vì xoá nó — theo brief §9: không giảm coverage chỉ để
tránh overlap.

Impact: `H-03` **ĐÓNG**. `G04` `deterministic NO → YES`. Gate `E1` giữ nguyên.

### 7.3 Kết quả ma trận sau revision

```text
32/32 có Khẳng định tường minh (assertion)   : ĐẠT
32/32 có Fixture bắt buộc / evidence         : ĐẠT
32/32 có PASS khi                            : ĐẠT
32/32 có FAIL khi                            : ĐẠT
32/32 có Nguồn quy phạm (INV/§/DEC)          : ĐẠT
```

Mỗi gate nay là một khối `#### CHECK-105D-NN (GNN)` theo khuôn
`governance/templates/TASK_DEFINITION_TEMPLATE.md` (`Priority` / `Status` /
`Evidence Level` / `Evidence` / `Executed By` / `Timestamp`), thay cho một
dòng bảng. Bảng chỉ mục còn lại **chỉ để điều hướng** và cố ý không lặp lại
`Status`/`Evidence Level` — tránh tạo hai nguồn sự thật (`V4.1` §11).

---

## 8. HARDENING nạp thêm (không bắt buộc, không mở rộng scope)

| Finding | Xử lý | Gate | Vì sao nạp ngay |
|---|---|---|---|
| `H-02` (một phần) | `INV-43c`/`INV-44` ở **biên lookup** mà 105D sở hữu: API cross-system trả `public_purchase_code` của mapping `CONFIRMED`, hoặc absence — không bao giờ mã dẫn xuất | `G31` Phần B | Entity `CrossSystemProductMapping` thuộc scope 105D; đóng phần "MỘT PHẦN" của case J mà không chạm `TASK-105E`. Điều kiện (a) của `INV-43` (vendor candidate tại `sale_date`) **vẫn ngoài scope**, ghi tường minh trong gate |
| `H-04` | `INV-33` (nhiều `CONFIRMED` → lỗi toàn vẹn, cấm tự chọn) và `INV-36` ("từ chối A ≠ chấp nhận B") | `G09`, `G12` | Hai ngữ nghĩa chống-map-sai, nạp được vào gate hiện có bằng một assertion mỗi gate |
| `H-05` | **KHÔNG đóng** | — | `ranking_method_id` `OPTIONAL` → `REQUIRED` là **thay đổi data contract** (§6.7), ngoài thẩm quyền của một phiên gate revision. Ghi lại nguyên trạng trong `G08` mục "Hạn chế đã ghi", kèm re-trigger |

---

## 9. Overlap — làm rõ, không xoá

Brief §9: không bắt buộc xoá overlap nếu mỗi gate bảo vệ một invariant khác
nhau, nhưng phải làm rõ để reviewer độc lập không phải suy đoán; không giảm
coverage chỉ để tránh overlap.

Kết quả: **giữ cả sáu cặp**, bổ sung một mục "Ma trận overlap có chủ đích" ở
cuối phần gate, cộng các đoạn "Ranh giới với …" đặt ngay trong từng gate liên
quan (`G04`↔`G24`, `G07`↔`G06(c)`, `G26`↔`G27`↔`G28`, `G10`↔`G24`,
`G29`↔`G30`, `G31`↔`G32`, `G03`↔`G11`, `G10`↔`G17`).

Không gate nào bị xoá, không assertion nào bị bỏ.

---

## 10. Bao phủ 20 case đối kháng bắt buộc — trước / sau

| Case | Trước (S036) | Sau (S037) | Gate |
|---|---|---|---|
| A | ĐẠT | ĐẠT | `G03`, `G11` |
| B | ĐẠT | ĐẠT | `G24`, `G04` (nay chính xác) |
| C | **KHÔNG ĐẠT** | **ĐẠT** | `G05` (assertion hai chiều) |
| D | ĐẠT | ĐẠT | `G23` |
| E | ĐẠT | ĐẠT | `G07`, `G06(c)` |
| F | ĐẠT | ĐẠT | `G06` (nay bốn fixture), `G23` |
| G | ĐẠT | ĐẠT | `G13`, `G28`, `G17` |
| H | ĐẠT | ĐẠT | `G26`, `G27`, `G28` |
| I | ĐẠT | ĐẠT | `G30` |
| J | **MỘT PHẦN** | **ĐẠT** (phần 105D sở hữu) | `G31` Phần B |
| K | ĐẠT | ĐẠT | `G12` |
| L | ĐẠT | ĐẠT | `G18` |
| M | ĐẠT | ĐẠT | `G19` |
| N | ĐẠT | ĐẠT | `G20` Phần A |
| O | **KHÔNG ĐẠT** | **ĐẠT** | `G10` `B1` |
| P | **KHÔNG ĐẠT** | **ĐẠT** | `G10` `B2`/`B3` |
| Q | ĐẠT | ĐẠT | `G01` |
| R | ĐẠT | ĐẠT | `G01` |
| S | **KHÔNG ĐẠT** | **ĐẠT** | `G20` Phần B, `G21` Phần B |
| T | **KHÔNG ĐẠT** | **ĐẠT** | `G28` Phần B, `G21` Phần C |

```text
Trước : ĐẠT 14 / MỘT PHẦN 1 / KHÔNG ĐẠT 5
Sau   : ĐẠT 20 / MỘT PHẦN 0 / KHÔNG ĐẠT 0
```

---

## 11. Bảng thay đổi tổng hợp — before / after

| Gate | Trạng thái trước | Thay đổi | Evidence Level |
|---|---|---|---|
| Khối "Định nghĩa vận hành bắt buộc" | `ALIAS_AID_UNIQUE` trong tập auto-resolve; "Ba nguồn"; thiếu "interaction" | SỬA — tập auto-resolve tách riêng, đúng hai phương thức; bốn nguồn ambiguity; `interaction` khai tử | — |
| `G01` | dòng bảng | Viết lại thành khối assertion đầy đủ (5 fixture) | `E2` |
| `G02` | dòng bảng | Viết lại thành khối assertion đầy đủ | `E1` |
| `G03` | dòng bảng | Viết lại; thêm ranh giới với `G11` | `E1` |
| `G04` | "0 interaction" — **không deterministic** | SỬA (H-03): `confirmation_action` + 0 ghi; ranh giới với `G24` | `E1` |
| `G05` | "**có thể** auto-resolve" — **không testable** | SỬA (F-02): assertion hai chiều + fixture âm `INV-29` | `E2` |
| `G06` | "Ba fixture" — mâu thuẫn `G23` | SỬA (F-01): **bốn** fixture; định nghĩa AMBIGUOUS đã sửa | `E2` |
| `G07` | dòng bảng | Viết lại; thêm chiều phủ định toàn cục + ranh giới với `G06(c)` | `E2` |
| `G08` | dòng bảng | Viết lại; ghi rõ hạn chế `H-05` còn mở | `E1` |
| `G09` | dòng bảng | Viết lại; **nạp `INV-33`** (H-04) | `E1` |
| `G10` | "reuse qua import/run mới" | **NẠP F-05**: sáu assertion catalog drift `B1`…`B6` | `E1 → E2` |
| `G11` | dòng bảng | Viết lại; thêm `affected_scope` + ranh giới với `G03` | `E1` |
| `G12` | dòng bảng | Viết lại; **nạp `INV-36`** (H-04) + `INV-37` | `E1` |
| `G13` | 4 assertion | Viết lại nguyên nghĩa thành khối | `E1` |
| `G14` | dòng bảng | Viết lại; thêm `INV-20`/`INV-21` | `E2` |
| `G15` | dòng bảng | Viết lại; assertion structural trên bản ghi đã persist | `E2` |
| `G16` | dòng bảng | Viết lại; import-graph + ngoại lệ pre-cutover | `E2` |
| `G17` | dòng bảng | Viết lại; ranh giới với `G28`; fixture Tracking fake | `E2` |
| `G18` | "giữ old/new mapping" | Viết lại đầy đủ `INV-74`…`INV-78`; trỏ chéo actor | `E2` |
| `G19` | dòng bảng | Viết lại; ba lớp idempotency | `E2` |
| `G20` | chỉ version conflict | **NẠP F-03 Phần B**: actor là điều kiện tiên quyết của command | `E2` |
| `G21` | provenance cơ bản | **NẠP F-03 Phần B + F-04 Phần C**: actor semantics + `ResolutionBinding`/replay | `E1 → E2` |
| `G22` | bề mặt không xác định — **không testable** | SỬA (H-01): ràng buộc vào bề mặt CLI Phase 1; cấm `NOT_APPLICABLE` tuỳ tiện | `E1` |
| `G23` | đã đúng từ `S035` | Viết lại thành khối; thêm `mapping_source`/`parent_mapping_id` | `E1` |
| `G24` | đã đúng | Viết lại thành khối; ranh giới với `G04`/`G10` | `E1` |
| `G25` | dòng bảng | Viết lại; nêu baseline `58 passed, 2 skipped` | `E2` |
| `G26` | dòng bảng | Viết lại; ranh giới với `G27`/`G28` | `E2` |
| `G27` | dòng bảng | Viết lại; thêm `attempted_sources` | `E1` |
| `G28` | chỉ "không cần Tracking giả" | **NẠP F-04 Phần A/B**: unified PP versioned source `B1`…`B6` | `E2` |
| `G29` | dòng bảng | Viết lại; ranh giới với `G30` | `E2` |
| `G30` | dòng bảng | Viết lại; assertion "so sánh đủ tuple" | `E2` |
| `G31` | chỉ lúc TẠO mapping | **NẠP H-02 Phần B**: lookup không đoán mã; ghi rõ ranh giới với `TASK-105E` | `E2` |
| `G32` | dòng bảng | Viết lại; thêm `INV-45` (namespace không đổi sau fallback) | `E1` |

```text
Gate count trước : 32
Gate count sau   : 32
Gate thêm mới    : 0
Gate xoá         : 0
Evidence Level hạ: 0        (chỉ có hai lần NÂNG: G10, G21 — E1 → E2)
```

---

## 12. Điều phiên này KHÔNG làm

```text
- Không sửa app/**, tests/**, config/**, tools/**, scripts/**, pyproject.toml.
- Không implement TASK-105B, TASK-105C, TASK-105D, TASK-105E.
- Không thêm, không xoá gate nào; gate count giữ đúng 32.
- Không hạ Evidence Level hay hạ tiêu chuẩn bất kỳ gate nào.
- Không ghi FROZEN; không thực hiện Freeze Finalization retry.
- Không chuyển TASK-105D sang READY.
- Không sửa data contract (docs/spec/TASK-105D-DATA-CONTRACT.md) — H-05 vì
  vậy còn mở.
- Không activate FilePriceProvider; không thay PendingPriceProvider.
- Không sửa repo Tracking; không tạo mapping/dataset production.
- Không merge vào nhánh mặc định.
- Không mở Repair Cycle; không tiêu review budget.
- Không sửa governance/core/V4_1_POLICY_FREEZE.md hay bất kỳ historical
  adoption artifact nào.
```

---

## 13. NEXT AUTHORIZED ACTION

Một phiên **FREEZE FINALIZATION RETRY** có thẩm quyền (`V4.1` §12) cho
`TASK-105D`:

1. Re-review **TOÀN BỘ** 32 gate đã sửa — không chỉ phần diff.
2. Xác minh `F-01`…`F-05` đã đóng thật, và `G04`/`G22` nay deterministic.
3. Nếu PASS: ghi `FROZEN` → `TASK-105D` mới chuyển được `READY`.
4. **Ngay sau freeze verdict**: review lại branch divergence theo `DEC-157` §2
   (`V4.1` §8 Option C, review point = ngay sau verdict).

`TASK-105D` implementation **không** được mở trước divergence review đó.
