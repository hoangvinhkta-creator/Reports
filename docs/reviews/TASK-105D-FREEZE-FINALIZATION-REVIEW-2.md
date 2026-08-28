# TASK-105D — FREEZE FINALIZATION REVIEW #2 (Independent, Retry)

Artifact Type:
INDEPENDENT FREEZE FINALIZATION REVIEW — Completion Gate của `TASK-105D`.
Đây là **review evidence + freeze evidence**, không phải Owner Decision và
không phải implementation.

Session:
`docs/sessions/S038-task-105d-freeze-finalization-2.md`

Reviewed base SHA (exact target):
`be835b1b1b03d4e8d21656c3624b6e4bc964b7a1`

Review branch:
`review/task-105d-freeze-finalization-2`

Freeze attempt trước:
`1676e1d173ff6afdbbaa2cedcf07fc06346955ce` — attempt #1 (`S036`) reviewed base
SHA `9cd871488a6baebf6b80737f42e2137a27887cef`, verdict `FAIL`
(5 BLOCKING / 5 HARDENING / 3 OUT_OF_SCOPE),
`docs/reviews/TASK-105D-FREEZE-FINALIZATION-REVIEW.md`.

Authority:
`governance/core/V4_1_POLICY_FREEZE.md` §12 (State Authority Matrix — `FROZEN`
chỉ được ghi bởi một phiên Freeze Finalization có thẩm quyền), §7 (Review
Finding Action Gate), §11 (Artifact Internal Precedence), §5 (Production Path
Decision Rule), §8 (Branch Divergence Limit);
`governance/core/TASK_COMPLETION_GATE_STANDARD.md`;
`DEC-157` §2 (Owner Decision B — Option C cho phép ĐÚNG MỘT Freeze
Finalization retry; đây là retry đó).

## Phân tách vai trò

Phiên này **không** kế thừa kết luận PASS của `S037`. `S037` là phiên
gate-author/revision; phiên này là **independent reviewer**. Toàn bộ 32 gate
được review lại từ đầu trên canonical target, không chỉ review diff, không
chỉ xác minh `F-01`…`F-05`, và **không** mặc định tuyên bố "32/32
testable/deterministic" của `S037` là đúng. Ma trận §5 dưới đây được dựng lại
độc lập từ văn bản gate, không chép từ `S037`.

Ghi chú artifact budget (`V4.1` §10): đây là artifact governance thứ **9** của
lineage `TASK-105D`, thuộc diện `OWNER APPROVAL REQUIRED`. Approval là chỉ thị
tường minh của Owner khi mở phiên này ("If freeze PASS: commit/push
review/freeze/state evidence only to `review/task-105d-freeze-finalization-2`").
Ghi lại theo tiền lệ `DEC-156` / `S036` / `S037`.

---

## VERDICT

```text
PASS WITH HARDENING — TASK-105D READY

Completion Gate frozen        : YES
TASK-105D READY               : YES
BLOCKING findings             : 0
HARDENING findings            : 4   (3 mới + H-05 kế thừa)
OUT_OF_SCOPE findings         : 3   (kế thừa nguyên trạng)
Testable                      : 32 / 32
Deterministic                 : 32 / 32
Contradiction trong gate set  : 0
Adversarial A–T               : 20 / 20 PASS
Repair Cycle opened           : NO
Review budget TASK-105D       : 2 allowed / 0 used / 2 remaining (KHÔNG ĐỔI)
```

Tám điều kiện freeze của `V4.1` §12 + brief §18 đều đạt: `BLOCKING = 0`;
32/32 testable; 32/32 deterministic; 20/20 adversarial PASS; Owner
Ratification (`OR-01`/`OR-02`/`OR-03`) đã được gate bảo vệ; không còn
contradiction chưa giải trong gate set; Completion Gate Change Proposal hợp
lệ; governance authority hợp lệ (`DEC-157` Option C, đúng retry thứ nhất và
duy nhất).

Bốn HARDENING **không** chặn freeze theo `V4.1` §5/§7: không finding nào dựng
được production path hiện tại từ bốn nguồn hữu hạn của §5 (chưa có
implementation, chưa có dataset production, chưa có config, không Golden test
nào phủ path này), và cả bốn đều có re-trigger cụ thể ở §10.

---

## 1. Tiền kiểm (Pre-flight)

```text
branch      : review/task-105d-freeze-finalization-2      ĐÚNG
HEAD        : be835b1b1b03d4e8d21656c3624b6e4bc964b7a1    ĐÚNG (khớp exact target)
worktree    : CLEAN
default     : claude/extract-upload-repo-gq2ws4  (HEAD branch thật trên origin)
default tip : 573e051e093cd850c9efb13891bf6dee5654f0c6
ahead       : 7 commit / behind: 0
```

Canonical evidence đã đọc: `CLAUDE.md`;
`governance/core/V4_1_POLICY_FREEZE.md` (toàn văn);
`DEC-151`…`DEC-157` (`PROJECT/PROJECT_DECISIONS.md`);
`docs/tasks/TASK-105B-file-price-provider.md`,
`docs/tasks/TASK-105C-historical-vendor-price-provider.md`,
`docs/tasks/TASK-105D-product-identity-resolver.md` (toàn văn, 2350 dòng),
`docs/tasks/TASK-105E-price-resolution-composition.md`,
`docs/tasks/TASK-108B-eligible-costs-owner-definition.md`;
`docs/spec/TASK-105D-DATA-CONTRACT.md` (1511 dòng);
`S032`, `S034`, `S035`, `S036`, `S037`;
`docs/reviews/TASK-105D-FREEZE-FINALIZATION-REVIEW.md` (freeze attempt #1);
`docs/reviews/TASK-105D-COMPLETION-GATE-CHANGE-PROPOSAL.md`;
`PROJECT/REVIEW_BUDGET_LEDGER.md`; `PROJECT/PROJECT_PROGRESS.md`.

---

## 2. Authority / Divergence — xác minh `DEC-157`

Xác minh nguyên văn `DEC-157` §2:

```text
V4.1 §8 — INTEGRATION_DECISION_REQUIRED  [ cumulative LOC > 5.000 ]
Owner chọn: (C) CONTINUE WITH EXPLICIT JUSTIFICATION.

Phạm vi được phép tiếp tục dưới Option C:
  1. Phiên Gate Revision này (S037).
  2. MỘT phiên Freeze Finalization retry độc lập.
Review point tiếp theo (bắt buộc): NGAY SAU FREEZE FINALIZATION RETRY VERDICT.
```

**Xác nhận: ĐÚNG NGUYÊN VĂN.** Phiên này là retry thứ nhất và duy nhất được
Option C cho phép. Phiên này **không** mở implementation, **không** tự gia hạn
Option C, và thực hiện divergence review bắt buộc ngay sau verdict (§14).

---

## 3. Completion Gate Change Proposal — xác minh

| Yêu cầu (brief §3) | Kết quả | Bằng chứng |
|---|---|---|
| Trace về Freeze Attempt #1 | ĐẠT | Header "Source freeze attempt" nêu đúng SHA `9cd8714`, verdict, 5/5/3 |
| Trace `F-01`…`F-05` | ĐẠT | §2…§6 của proposal, mỗi finding một mục before/after |
| Ghi Owner decision giữ đúng 32 gate | ĐẠT | §1.1, trích nguyên văn Decision A; bảng "gate nhận" kèm lý do ngữ nghĩa |
| Ghi before/after semantics | ĐẠT | §11 bảng 33 dòng (32 gate + khối định nghĩa) |
| Ghi invariant bị tác động | ĐẠT | Mỗi mục nêu `INV-xx` được nạp; §11 cột thay đổi |
| Không che giấu non-row operational-definition change | ĐẠT | Dòng ĐẦU TIÊN của bảng §11 là khối "Định nghĩa vận hành bắt buộc" — thay đổi ngoài-hàng được công bố tường minh, không giấu |
| Không freeze trong S037 | ĐẠT | Proposal VERDICT: `Completion Gate frozen: KHÔNG`; `DEC-157` §3 |
| Không implementation | ĐẠT | §12; xác minh độc lập bằng git diff (§13 của review này) |
| Gate count 32 trước / 32 sau | ĐẠT | §11: `gates_added 0`, `gates_removed 0` |
| Proposal khớp canonical task/spec | ĐẠT | Đối chiếu từng gate với task file tại `be835b1` — không lệch |

Kiểm tra thêm (không do brief yêu cầu, reviewer tự đặt): **không gate nào bị
hạ tiêu chuẩn**. Xác minh độc lập: 32/32 `Priority = REQUIRED`; 0 lần hạ
Evidence Level; đúng hai lần NÂNG `E1 → E2` (`CHECK-105D-10`,
`CHECK-105D-21`). Phân bố cuối: `E2 = 19`, `E1 = 13`.

**Kết luận: Change Proposal HỢP LỆ.**

---

## 4. `F-01`…`F-05` — independent re-test

### 4.1 `F-01` — auto-resolve set / `ALIAS_AID_UNIQUE`

Không chỉ kiểm dòng mà `S037` nói đã sửa. Quét **toàn bộ** canonical text.

Tập auto-resolve canonical kỳ vọng = ĐÚNG HAI: `ALIAS_EXACT`,
`CATALOG_EXACT_UNIQUE`. Xác minh tại nguồn quy phạm:

```text
DEC-156 §2 / PROJECT_DECISIONS:6321  INV-28 SỬA — đúng hai phương thức
data contract §6.6 (dòng 543)        "TẬP ĐÓNG, ĐÚNG HAI PHƯƠNG THỨC"
data contract §6.6 (dòng 587)        INV-28 SỬA — đúng hai
data contract §6.6 (dòng 590)        INV-28b — không bao giờ tự sinh CONFIRMED
data contract §17.2 (dòng 1394+)     "Bốn nguồn cần confirmation", (d) ALIAS_AID_UNIQUE
data contract §6.6 (dòng 550)        ALIAS_AID_UNIQUE = candidate #1, KHÔNG có production authority
```

Quét stale text ở **sáu** bề mặt mà brief §4 liệt kê:

| Bề mặt | Kết quả |
|---|---|
| Khối "Định nghĩa vận hành bắt buộc" (task file 486–508) | ĐÚNG — tập auto-resolve tách riêng, đúng hai; bốn nguồn ambiguity, (d) = `ALIAS_AID_UNIQUE` candidate-only |
| Resolution Order (task file 120–143) | ĐÚNG — "**candidate #1, KHÔNG auto-resolve** — `DEC-156`/`OR-02`" |
| Gate prose (`G05`, `G06`, `G07`, `G23`) | ĐÚNG — `G06` bốn fixture; `G23` fixture bắt buộc `ALIAS_AID_UNIQUE`; `G05`/`G07` nêu tập đóng hai phương thức |
| Data contract (§6.6, §17.2, §17.4, dòng 1243) | ĐÚNG — dòng 1243 ghi rõ "không còn là reuse tự động" |
| Task file — Metadata/Authority (57), Ready Gate (389) | ĐÚNG — "CANDIDATE-ONLY POLICY" |
| Decision transcription (`DEC-156`, `DEC-157`) + UX semantics (§17.1, "Human Confirmation và Batch UX Contract") | ĐÚNG — UX block trỏ về định nghĩa quy phạm, không tự phát biểu lại |

Quét chuỗi "Ba nguồn" / "Ba fixture" toàn repo: **mọi** lần xuất hiện còn lại
đều nằm trong artifact **lịch sử** (review attempt #1, before/after của
proposal, `S036`/`S037` handoff, `PROJECT_PROGRESS` changelog) — đúng vai trò
bản ghi lịch sử, không phải quy phạm hiện hành. `V4.1` §10 cấm retro-fit tài
liệu lịch sử; giữ nguyên là ĐÚNG.

`ALIAS_AID_UNIQUE` đạt cả bốn yêu cầu brief §4: candidate-only (`INV-28b`,
`G06` fixture 4); không có production auto-resolution authority (ngoài tập
đóng); cần `confirmation_action` (`G23`, đúng 1); confirmed mapping sau đó
reusable (`G23`: lần hai `count == 0` qua `ALIAS_EXACT`).

`G06` và `G23`: **không contradiction**. `G06` ràng buộc "không auto-resolve",
`G23` sở hữu phần đếm action; `G06` cố ý trỏ sang `G23` thay vì nhân đôi.

**`F-01` = ĐÓNG.**

### 4.2 `F-02` / `G05`

`G05` nay có assertion thực sự, hai chiều:

```text
Chiều DƯƠNG : count(confirmation_action) == 0
              resolution_method == CATALOG_EXACT_UNIQUE
              outcome == RESOLVED(namespace, source_product_code)
              mapping_source == DETERMINISTIC_CATALOG_MATCH
Chiều ÂM    : khớp exact CẢ HAI namespace → CROSS_NAMESPACE_TIE,
              KHÔNG auto-resolve  (INV-29)
```

`FAIL khi` phát biểu đủ cả hai chiều. Không còn từ "có thể"/"được phép".
Reviewer kiểm chứng: 0 lần xuất hiện của `có thể auto-resolve` trong gate set.
Resolution method và identity deterministic. Ba fixture bắt buộc, trong đó một
fixture âm.

**`F-02` = ĐÓNG.**

### 4.3 `F-03` — actor

Mười một yêu cầu của brief §6, đối chiếu từng cái:

| # | Yêu cầu | Gate | Kết quả |
|---|---|---|---|
| 1 | `actor_id` REQUIRED cho state-changing command | `G20` B | ĐẠT — liệt kê đủ 8 loại command |
| 2 | empty/whitespace actor invalid | `G20` B + fixture (3) | ĐẠT — `""` và `"   "` |
| 3 | không silent default | `G20` B | ĐẠT — cấm `"system"`, cấm anonymous |
| 4 | không suy ra OS/env user | `G20` B | ĐẠT — cấm env / OS user / config / hằng số |
| 5 | missing actor → no mutation | `G20` B | ĐẠT — 0 mapping đổi |
| 6 | missing actor → no audit event | `G20` B | ĐẠT — 0 event |
| 7 | version không tăng | `G20` B + PASS khi | ĐẠT — `current_revision()` không đổi |
| 8 | audit actor immutable | `G21` B | ĐẠT — REQUIRED, non-empty, IMMUTABLE |
| 9 | Phase 1 actor chỉ là declared actor | `G21` B | ĐẠT — "KHAI BÁO CỦA NGƯỜI VẬN HÀNH" |
| 10 | không artifact/gate claim authenticated identity | `G21` B | ĐẠT — test quét văn bản, 0 lần xuất hiện |
| 11 | capability boundary không bị che | `G21` B | ĐẠT — "Điều gate này KHÔNG khẳng định" |

Fixture/evidence đủ cho independent implementation test: `G20` ba fixture
(conflict; mỗi loại command thiếu actor; actor rỗng/khoảng trắng), `G21` năm
fixture trong đó (2) và (3) thuộc actor. Yêu cầu #10 được cho một
**assertion thực thi được** (text scan) chứ không chỉ prose — đúng chuẩn
`EVIDENCE_STANDARD`.

**`F-03` = ĐÓNG.**

### 4.4 `F-04` — unified Public Purchase + replay

Review lại `OR-01`/shared contract từ đầu (không đọc qua kết luận `S037`).

Contract nguồn: `DEC-156` §1; data contract §3 (`D-01`, `D-02`,
`INV-02`…`INV-10`), §10.1 (`E-L`, `INV-55`…`INV-57`).

| Yêu cầu brief §7 | Gate + assertion | Kết quả |
|---|---|---|
| `product_key` price tồn tại trong identity projection **cùng version** | `G28` B1 (`INV-06`), vi phạm = LỖI LOAD lúc publish/load | ĐẠT |
| strict identity loader semantics | `G28` B2 (`INV-02`) — thiếu khối / sai tên / rỗng / khoá lạ = lỗi load, KHÔNG "danh mục rỗng" | ĐẠT |
| published version immutable | `G28` B5 (`INV-07`) | ĐẠT |
| replay/report binding | `G21` C (`INV-55`/`INV-56`) — ghim đủ **bốn**, replay giống hệt | ĐẠT |
| missing binding = hard error theo contract | `G21` C (`INV-57`) | ĐẠT |
| không fallback latest | `G21` C — "KHÔNG fallback 'mới nhất'" | ĐẠT |
| không biến thành Pending | `G21` C — "KHÔNG trả Pending"; `G28` B1 — không phải Pending | ĐẠT |
| hai independent operational PP sources = FAIL | `G28` B6 — "FAIL gate này, KỂ CẢ khi mọi assertion khác PASS" | ĐẠT |

`G28` B6 là mệnh đề quyết định của `OR-01` và được viết dưới dạng **FAIL
tuyệt đối**, đóng đúng lỗ hổng mà brief §7 nêu ("không để implementation sau
PASS 105D mà vẫn tạo hai nguồn độc lập").

**Ranh giới `TASK-105B` — kiểm tra riêng theo yêu cầu brief §7.**
`TASK-105B` Scope = đúng hai file (`app/modules/pricing/file_price_provider.py`
+ test của nó), trạng thái `FROZEN` (`DEC-153`). Assertion
"`FilePriceProvider` unchanged" trong `G28` B3 là một khẳng định **phủ định /
boundary**: nó chứng minh `TASK-105D` **không** chạm module đã frozen, kiểm
bằng `git diff` rỗng. Nó **không** yêu cầu chạy lại, sửa, hay mở rộng
implementation `TASK-105B`.

`PublicPurchaseSourceLoader` mà `G28` B3 yêu cầu **không** phải implementation
của `TASK-105B`: `TASK-105D` tự nó cần nạp Public Purchase **identity
projection** để resolve identity `PUBLIC_PURCHASE` (`G26`, `G28` A), nên loader
đó là nhu cầu nội tại của 105D. `INV-08` ghi rõ phần logic khoảng ngày là của
`FilePriceProvider` và **không được viết lại**; loader chỉ truyền khối `prices`
đã validate vào constructor `rows`. Kết luận: **đúng vai trò boundary, không
phải dependency implementation thừa.**

**`F-04` = ĐÓNG.**

### 4.5 `F-05` — catalog drift

Sáu điều kiện brief §8, đối chiếu `G10` Phần B:

| Brief | Gate | Assertion | Kết quả |
|---|---|---|---|
| A. rename display name, same canonical code → mapping remains valid | `G10` B1 (`INV-13`, `INV-21`) | `ALIAS_EXACT`, `count == 0`, status KHÔNG chuyển `STALE` | ĐẠT |
| B. absent from current board → historical/confirmed mapping không tự mất hiệu lực | `G10` B2 (`INV-14a/b`) | không vô hiệu hoá / không xoá / không tự `PENDING`; report ghim capture cũ replay GIỐNG HỆT | ĐẠT |
| C. current catalog không retroactively remap identity | `G10` B6 (`INV-15`) | cấm retroactive remap; chỉ correction §13 mới đổi được | ĐẠT |
| D. alias/stale semantics đúng contract | `G10` B3 (`INV-14c`) + B4 (`INV-16`) | `STALE` + `MAPPING_STALE_TARGET_ABSENT`, cần confirmation; alias.map KHÔNG tự chuyển, sinh `MARK_STALE` + candidate #1 | ĐẠT |
| E. capture FAILED → hard error, không silently Pending | `G10` B5 (`INV-12`) | LỖI CỨNG; resolver TỪ CHỐI chạy; KHÔNG đọc thành "không tồn tại", KHÔNG Pending | ĐẠT |
| F. 0 Tracking writes | `G10` cuối Phần B + `G17` fixture (3) | Tracking fake ghi-nhận-mọi-lệnh-ghi, số lệnh ghi == 0 | ĐẠT |

Bảy fixture bắt buộc (B1…B6 + Phần A), mỗi fixture dựng hai
`TrackingCatalogSnapshot`. `B2(b)` yêu cầu so sánh **output đầy đủ** của
report, không chỉ một trường — đủ mạnh để bắt regression replay.

**`F-05` = ĐÓNG.**

---

## 5. Ma trận 32 Completion Gate — dựng lại độc lập

Ký hiệu: `DET` = deterministic, `TST` = testable, `CTR` = contradiction,
`Q?` = independent reviewer có phải hỏi Owner để hiểu nghĩa gate không.
"Assertion" = phát biểu PASS/FAIL rút ra được **mà không hỏi lại Owner**.

Kiểm tra cấu trúc tự động trên cả 32 khối: **32/32** có đủ 11 trường quy phạm
(`Priority`, `Status`, `Evidence Level`, `Khẳng định`, `Fixture bắt buộc`,
`PASS khi`, `FAIL khi`, `Nguồn quy phạm`, `Evidence`, `Executed By`,
`Timestamp`). `Priority`: 32/32 `REQUIRED`. `Status`: 32/32 `NOT_TESTED`.

| Gate | Mục đích | Nguồn quy phạm | Assertion chính | Fixture bắt buộc | DET | TST | CTR | Q? | Overlap | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| G01 | Pre-cutover bypass | `INV-46`…`50`, `54` | outcome ∈ {`HISTORICAL_CONFIRMED`, `PENDING_HISTORICAL_CONFIRMATION`}; spy == 0 cả hai nhánh; phân loại bằng `sale_date` | 5 | YES | YES | — | KHÔNG | — | **PASS** |
| G02 | Union type đóng post-cutover | §5, `INV-17/24/25` | outcome ∈ 3 biến thể; `RESOLVED` đủ tuple; `HISTORICAL_CONFIRMED` không rò | 3 + type check | YES | YES | — | KHÔNG | G13 | **PASS** |
| G03 | DISTINCT-before-mapping | `INV-30`, `INV-87` | `\|D\| == 50`; `count <= \|D\|`; không theo row/order | 10.000 row / 50 distinct | YES | YES | — | KHÔNG | G11 | **PASS** |
| G04 | Alias confirmed = read path chỉ-đọc | `INV-30/33/70` | `count == 0`, `ALIAS_EXACT`, 0 event / 0 ghi (kể cả touch `updated_at`) | 1 (+ so revision) | YES | YES | — | KHÔNG | G24 | **PASS** |
| G05 | `CATALOG_EXACT_UNIQUE` hai chiều | §1, §6.5, §6.6, `INV-29` | dương: `count == 0` + method + `mapping_source`; âm: `CROSS_NAMESPACE_TIE` không auto-resolve | 3 (1 âm) | YES | YES | — | KHÔNG | — | **PASS** |
| G06 | AMBIGUOUS không auto-resolve | `INV-01/27/28/28b/29`, §17.2 | outcome ∈ {`REQUIRES_CONFIRMATION`, `PENDING_PRODUCT`}; method ∉ tập đóng | **4** | YES | YES | — | KHÔNG | G07, G23 | **PASS** |
| G07 | Fuzzy không có production authority | `INV-01/28`, §14 | `SIMILARITY_RANKED` ∉ tập đóng; **không đường nào** (resolver/bootstrap/migration/script) sinh `CONFIRMED` | 2 (gồm bootstrap) | YES | YES | — | KHÔNG | G06(c) | **PASS** |
| G08 | Candidate ranking ổn định | §6.7, `INV-64` | cùng input → cùng thứ tự, hai process; 3 trường evidence REQUIRED | 2 | YES | YES | — | KHÔNG | — | **PASS** (H-05 ghi rõ) |
| G09 | Persist + toàn vẹn store | `INV-30/33/62/63/64/66/67` | fsync + `os.replace`; log thắng index; >1 `CONFIRMED` → lỗi toàn vẹn, cấm tự chọn | 3 | YES | YES | — | KHÔNG | G10 | **PASS** |
| G10 | Reuse + catalog drift | `INV-12`…`16`, `21`, `30`, `70` | A: reuse run mới; B1…B6 drift (rename / biến mất / stale / alias.map / capture FAILED / cấm retroactive remap) | 7 | YES | YES | — | KHÔNG | G24 | **PASS** |
| G11 | Một action → mọi row/order | `INV-30/76/87` | sau 1 action N dòng `RESOLVED`; `affected_scope` khớp M/N | 1 (M≥3, N≥5) | YES | YES | — | KHÔNG | G03 | **PASS** |
| G12 | Rejection theo fingerprint | `INV-34`…`37` | suppress ⟺ cùng khoá **và** cùng fingerprint; fingerprint đổi → đề xuất lại; từ chối A ≠ chấp nhận B | 4 | YES | YES | — | KHÔNG | — | **PASS** (H-05) |
| G13 | `PENDING_PRODUCT` riêng về kiểu | `INV-24/25`, §17.3 | 4 assertion a–d; enum đóng; không chặn batch | 1 hỗn hợp + type check | YES | YES | — | KHÔNG | G02 | **PASS** |
| G14 | Raw name bất biến | `INV-20/21/22`, `ADR-102` | `product_raw` byte-wise giống nhau qua confirm/correction/re-import | 1 (có dấu TV) | YES | YES | — | KHÔNG | — | **PASS** |
| G15 | Schema không chứa giá | `INV-23`, `DEC-154` §6 | tập khoá persist không giao tập field giá/tiền tệ; áp cho bản ghi đã persist | 1 (đọc log thật) | YES | YES | — | KHÔNG | G16 | **PASS** |
| G16 | Price-provider boundary | `INV-03/23/46`, §16.1 | không tính/trả giá post-cutover; import-graph sạch; ngoại lệ duy nhất = pre-cutover registry | 3 | YES | YES | — | KHÔNG | G15 | **PASS** |
| G17 | Tracking không bị mutate | `INV-11`, §4.1, `DEC-152` §6 | 0 đường ghi; capture immutable; `app/modules/**` không chạm mạng; cấm tạo product giả | 3 | YES | YES | — | KHÔNG | G28 | **PASS** |
| G18 | Correction audit | `INV-32`, `71`, `74`…`78` | supersede ở lại vĩnh viễn; `reason` REQUIRED; report đã ghim KHÔNG tự đổi; `REPIN_REPORT` tường minh | 4 | YES | YES | — | KHÔNG | G21 | **PASS** |
| G19 | Idempotency | `INV-68`…`71` | 3 lớp: command (`ALREADY_APPLIED`), state (`NO_CHANGE`), retry; revision không đổi | 4 | YES | YES | — | KHÔNG | G24 | **PASS** |
| G20 | Precondition: version + actor | `INV-58`…`61`, `72` | A: conflict tường minh, cấm LWW/auto-merge/force; B: thiếu actor → từ chối, 0 event, version không tăng | 3 | YES | YES | — | KHÔNG | G21 | **PASS** |
| G21 | Provenance + actor + binding/replay | `INV-24/25/55`…`57/72/73` | A: 9 trường provenance; B: actor immutable + cấm "authenticated" (test quét văn bản); C: ghim đủ **4**, replay giống hệt, thiếu → lỗi cứng | 5 | YES | YES | — | KHÔNG | G18, G20 | **PASS** |
| G22 | Keyboard-first trên bề mặt Phase 1 | §17.1 `D-14`, `ADR-101` | (a) 4 command + xem evidence + duyệt batch chạy headless qua CLI; (b) import-graph không GUI; (c) không action nào chỉ có đường con trỏ | 3 | YES | YES | — | KHÔNG | — | **PASS** |
| G23 | AMBIGUOUS candidate #1 | `INV-28/28b/87`, §17.2/17.4 | `count == 1`; resolve mọi dòng; lần sau `== 0` qua `ALIAS_EXACT`; fixture `ALIAS_AID_UNIQUE` bắt buộc + `parent_mapping_id` | 4 × 2 lần chạy | YES | YES | — | KHÔNG | G06, G11 | **PASS** |
| G24 | Known mapping batch N≥2 | `INV-30/70/87` | `count == 0`; `ALIAS_EXACT`; `current_revision()` không đổi | 1 (N=5 + 1 lạ) | YES | YES | — | KHÔNG | G04, G10 | **PASS** |
| G25 | Golden không đổi | `V4.1` §6, `DEC-153` | Golden trước/sau giống hệt; `58 passed, 2 skipped`; default vẫn `PendingPriceProvider` | 1 (2 SHA) | YES | YES | — | KHÔNG | — | **PASS** |
| G26 | Tracking MISS + PP unique | `DEC-154` §3, §3/§6.6 | `RESOLVED(PUBLIC_PURCHASE, code)`, `CATALOG_EXACT_UNIQUE`; kết quả hợp lệ, không hạng hai | 1 | YES | YES | — | KHÔNG | G27, G28 | **PASS** |
| G27 | Tracking MISS ⇏ Pending | `DEC-154` §3, §5 | phải đi tiếp qua PP trước khi kết luận; `attempted_sources` liệt kê cả hai | 2 | YES | YES | — | KHÔNG | G26 | **PASS** |
| G28 | PP identity + unified versioned source | `INV-02`…`10`, `DEC-153`, `DEC-156` §1 | A: identity hợp lệ không cần Tracking; B1…B6 gồm `INV-06` lúc load, loader strict, diff `file_price_provider.py` rỗng, immutability, **hai nguồn độc lập = FAIL** | 7 | YES | YES | — | KHÔNG | G17, G26 | **PASS** |
| G29 | Namespace persist, immutable | `INV-17/19/31/32` | persist cùng record; REQUIRED khi `CONFIRMED`; sửa = supersede; không suy ra lúc đọc | 3 | YES | YES | — | KHÔNG | G30 | **PASS** |
| G30 | Cùng code khác namespace | `INV-18`, `DEC-154` §5 | `TRACKING:X` ≠ `PUBLIC_PURCHASE:X`; mọi so sánh dùng đủ tuple | 1 | YES | YES | — | KHÔNG | G29 | **PASS** |
| G31 | Cross-system explicit + lookup | `INV-38`…`44`, §8.3/8.4 | A: explicit, 1:1, `CONFLICT` không LWW; B: lookup trả mã của mapping `CONFIRMED` hoặc absence, **không bao giờ** mã dẫn xuất | 4 | YES | YES | — | KHÔNG | G32 | **PASS** |
| G32 | Cross-system reuse | `INV-42/45`, `DEC-154` §7/§10 | `count == 0`; revision không đổi; namespace KHÔNG đổi sau fallback; provenance phân biệt hai đường | 1 (2 batch) | YES | YES | — | KHÔNG | G31 | **PASS** |

### Tổng hợp ma trận (độc lập)

```text
Testable                    : 32 / 32
Deterministic               : 32 / 32
Contradiction               : 0
Cần hỏi Owner để hiểu nghĩa : 0 / 32
Reviewer verdict            : 32 PASS / 0 FAIL
```

Ba gate mà attempt #1 đánh non-deterministic đã được review **riêng** ở §6.

Overlap: sáu cặp `S036` ghi nhận vẫn còn, và task file nay có mục
"Ma trận overlap có chủ đích" nêu invariant riêng của từng gate. Reviewer xác
nhận **không cặp nào là duplicate thật** — mỗi gate trong cặp bắt được một
lỗi mà gate kia bỏ lọt. Overlap **không** phải finding.

---

## 6. `G04` / `G05` / `G22` — review riêng, không kế thừa `S037`

### `G04`

```text
exact assertion : count(confirmation_action cho K) == 0
                  resolution_method == ALIAS_EXACT
                  0 MappingAuditEvent mới, 0 mapping record mới, 0 lệnh ghi
exact fixture   : store seed 1 mapping CONFIRMED cho K; resolve đúng 1 identity K;
                  so current_revision() trước/sau; đếm event mới
PASS            : count == 0 ∧ ALIAS_EXACT ∧ event mới == 0
FAIL            : bất kỳ ghi nào (kể cả "touch" updated_at) hoặc phát sinh action
deterministic   : YES
testable        : YES
hỏi Owner?      : KHÔNG
```

Khiếm khuyết cũ ("0 interaction" — thuật ngữ thứ ba, đọc theo nghĩa đen thì mở
màn hình cũng vi phạm) đã bị loại: gate tuyên bố tường minh không dùng từ
"interaction" nữa, và khối định nghĩa vận hành khai tử thuật ngữ đó. Ranh giới
với `G24` được ghi rõ nên `G04` không còn dư thừa. **`G04` = PASS.**

### `G05`

```text
exact assertion : (dương) count == 0 ∧ CATALOG_EXACT_UNIQUE ∧ RESOLVED(ns, code)
                          ∧ mapping_source == DETERMINISTIC_CATALOG_MATCH
                  (âm)   khớp exact CẢ HAI namespace → CROSS_NAMESPACE_TIE,
                          KHÔNG auto-resolve
exact fixture   : (1) exact unique TRACKING; (2) exact unique PUBLIC_PURCHASE;
                  (3) fixture âm INV-29
PASS            : hai fixture dương count == 0 + đúng method; fixture âm không auto-resolve
FAIL            : CATALOG_EXACT_UNIQUE bị bắt xác nhận (count > 0)
                  HOẶC CROSS_NAMESPACE_TIE bị auto-resolve
deterministic   : YES — FAIL được ở cả hai chiều
testable        : YES
hỏi Owner?      : KHÔNG
```

**`G05` = PASS.** Đây là gate được sửa triệt để nhất so với attempt #1.

### `G22`

```text
bề mặt áp dụng  : Phase 1 theo ADR-101 = thư viện Python thuần + CLI, KHÔNG GUI
exact assertion : (a) bốn confirmation_action command + xem candidate/evidence +
                      duyệt hết batch chạy được HOÀN TOÀN qua CLI/API dòng lệnh,
                      môi trường KHÔNG display, KHÔNG thiết bị trỏ (headless)
                  (b) app/modules/product/** không import thư viện GUI/web/pointer;
                      không domain operation nào cần sự kiện chuột/chạm
                  (c) không confirmation_action nào chỉ tiếp cận được qua con trỏ
exact fixture   : (1) chạy trọn batch (cả bốn command) headless; (2) assertion
                  import-graph; (3) liệt kê bề mặt gọi được của mỗi command
PASS            : ba fixture đúng trên bề mặt CLI Phase 1
FAIL            : một command chỉ chạy được qua GUI; import GUI; gate bị đánh
                  NOT_APPLICABLE mà không có Owner decision tường minh
deterministic   : YES
testable        : YES
hỏi Owner?      : KHÔNG
```

Kiểm tra riêng theo brief §9: headless/keyboard-operable semantics được định
nghĩa ở **domain/tool boundary** (CLI + import-graph + khả năng gọi lệnh),
**không** phụ thuộc GUI/web/pointer — đúng yêu cầu. Gate **cấm tường minh**
`NOT_APPLICABLE` với lý do "Phase 1 chưa có UI", nên canonical Owner
requirement (keyboard-first) vẫn tồn tại và vẫn bị ràng buộc. Việc mở rộng khi
UI Phase 2+ xuất hiện được giao cho phiên sở hữu UI, không làm gate hiện tại
mơ hồ. **`G22` = PASS.**

---

## 7. Adversarial A–T — tự trace, không dùng bảng `S037`

Mỗi case: case → invariant → gate → assertion.

| Case | Invariant | Gate + assertion cụ thể | Kết quả |
|---|---|---|---|
| A DISTINCT-before-mapping | `INV-30`, `INV-87` | `G03` `\|D\| == 50` ∧ `count <= \|D\|`; `G11` lan toả | **PASS** |
| B known confirmed mapping | `INV-30`, `INV-70` | `G04` read path 0 ghi; `G24` batch revision không đổi; `G10` A run mới | **PASS** |
| C catalog exact unique | §1, §6.6 | `G05` chiều dương `count == 0` | **PASS** |
| D alias aid unique | `INV-28b` | `G23` fixture bắt buộc: không auto-resolve, candidate #1, đúng 1 action, lần hai 0 | **PASS** |
| E fuzzy only | `INV-01` | `G07` phủ định toàn cục + `G06(c)` | **PASS** |
| F ambiguous | `INV-27/28` | `G06` bốn fixture; `G23` `count == 1` | **PASS** |
| G no match | `INV-24/25` | `G13` biến thể riêng về kiểu; `G27` `attempted_sources`; `G17` cấm tạo Tracking giả | **PASS** |
| H public purchase direct product | `DEC-154` §3 | `G26` `RESOLVED(PUBLIC_PURCHASE, code)`; `G28` A | **PASS** |
| I same-code cross-namespace | `INV-18` | `G30` đủ tuple; `G29` persist | **PASS** |
| J cross-system fallback | `INV-43c`, `INV-44` | `G31` B lookup trả mã của mapping `CONFIRMED` hoặc absence; cấm mã dẫn xuất kể cả khi trùng chuỗi | **PASS** (phần 105D sở hữu; điều kiện (a) của `INV-43` thuộc 105E, ghi rõ trong gate) |
| K rejection memory | `INV-34`…`37` | `G12` iff-fingerprint; `INV-36` từ chối A ≠ chấp nhận B | **PASS** |
| L correction | `INV-74`…`78` | `G18` supersede ở lại; `reason` REQUIRED; report ghim không tự đổi | **PASS** |
| M duplicate import | `INV-68`…`71` | `G19` ba lớp idempotency; revision không đổi | **PASS** |
| N concurrency | `INV-58`…`61` | `G20` A conflict tường minh, cấm LWW | **PASS** |
| O Tracking rename | `INV-13`, `INV-21` | `G10` B1 mapping vẫn hợp lệ, không chuyển `STALE` | **PASS** |
| P Tracking disappears | `INV-14a/b/c` | `G10` B2/B3 không vô hiệu hoá, replay giống hệt, identity mới → `STALE` | **PASS** |
| Q pre-cutover | `INV-46`/`47` | `G01` spy == 0 cả hai nhánh | **PASS** |
| R late import, pre-cutover `sale_date` | `INV-48` | `G01` fixture 3 (`import_date` 2027-01-15, `sale_date` 2026-08-20) | **PASS** |
| S Phase-1 actor | `INV-72`/`73` | `G20` B từ chối command thiếu actor; `G21` B immutable + cấm "authenticated" | **PASS** |
| T unified PP version/replay | `INV-02`…`10`, `55`…`57` | `G28` B1–B6 (B6 hai nguồn độc lập = FAIL); `G21` C ghim bốn + replay | **PASS** |

```text
ĐẠT 20 / MỘT PHẦN 0 / KHÔNG ĐẠT 0   trên 20 case bắt buộc
```

Ngưỡng freeze 20/20: **ĐẠT**.

---

## 8. Persistence / Audit — review độc lập coverage

| Cơ chế | Bất biến | Gate | Kết quả |
|---|---|---|---|
| `ProductIdentityMapping` | `INV-30`…`33` | `G09`, `G10`, `G24`, `G29` | ĐẠT (`INV-33` nay có assertion ở `G09`) |
| Alias index | `D-06`, `INV-62`/`63` | `G09`, `G10` | ĐẠT (log thắng index; dựng lại được) |
| `RejectedCandidateMemory` | `INV-34`…`37` | `G12` | ĐẠT (`INV-36` nay có assertion) |
| `CrossSystemProductMapping` | `INV-38`…`45` | `G31`, `G32` | ĐẠT (`INV-43c`/`44` nay có assertion ở `G31` B) |
| `HistoricalConfirmedRegistry` | `INV-46`…`54` | `G01` | ĐẠT ở định tuyến (`46`–`50`, `54`); `51`/`52`/`53` chưa có gate → `HB-105D-F2-03` |
| `MappingAuditEvent` | `INV-74`…`78` | `G18`, `G21` B | ĐẠT (`INV-78` `REPIN_REPORT` nay có fixture ở `G18`) |
| Idempotency | `INV-68`…`71` | `G19` | ĐẠT (mạnh — ba lớp) |
| Optimistic concurrency | `INV-58`…`61` | `G20` A | ĐẠT |
| Supersession | `INV-32`, `INV-74` | `G18`, `G29` | ĐẠT |
| Report binding | `INV-55` | `G21` C | ĐẠT (bốn thành phần) |
| Replay | `INV-56`/`57` | `G21` C | ĐẠT |
| Correction | `INV-74`…`77` | `G18` | ĐẠT |
| Rejected candidate reconsideration | `INV-35` | `G12` fixture (2) | ĐẠT ở chiều `pp_version_id`; chiều `ranking_method_id` → `H-05` |

**Semantics trong Data Contract không có gate bảo vệ** (quét tự động: 81
invariant định nghĩa trong data contract, 13 không được tham chiếu ở bất kỳ
đâu trong phần gate):

```text
INV-08                      cố ý — đã do FilePriceProvider (TASK-105B FROZEN)
                            thi hành; INV-08 ghi rõ "không viết lại logic đó"
INV-26                      chuẩn hoá khoá — phủ gián tiếp qua INV-27 (G06) và
                            G14; chiều dấu tiếng Việt/punctuation không có
                            fixture riêng
INV-51, INV-52, INV-53      toàn vẹn + correction của HistoricalConfirmedRegistry
INV-65                      backup/export tương đương bit
INV-79, INV-80, INV-81, INV-82   migration/rollback
INV-84, INV-85, INV-86      metrics (kể cả INV-85 cấm feedback loop và INV-86
                            cấm log PII khách hàng)
```

Cả 13 nằm dưới hai điều khoản `Exit Criteria`: "Migration/rollback +
permission/audit contract verified", "Metrics có denominator và validation
theo §15", và điều khoản quét "Toàn bộ invariant `INV-01`…`INV-87` có
assertion tương ứng hoặc có lý do ghi rõ vì sao không cần" — điều khoản này
**vẫn còn nguyên** trong `Exit Criteria` tại `be835b1` (kiểm tra riêng: `S037`
**không** xoá nó; không tiêu chuẩn nào bị hạ). Chúng vì vậy chặn `DONE`, nhưng
không phải REQUIRED check riêng. Ghi thành `HB-105D-F2-03` (§10).

---

## 9. Các phần còn lại của brief

### 9.1 Scope boundary (§14)

```text
TASK-105D  Product Identity Resolution + E-F/E-G/E-H/E-I/E-J/E-K/E-L
TASK-105C  HistoricalVendorMin  (BLOCKED, lineage riêng 2/0/2)
TASK-105B  Public Purchase effective-dated price provider foundation (FROZEN, DEC-153)
TASK-105E  Price Resolution Composition P00–P11 (PLANNED/OUTLINE)
TASK-108B  downstream KPI semantics (BLOCKED_BY_DEPENDENCY)
```

Xác minh `TASK-105D` **không** absorb logic của 105B/105C/105E/108B:
`G16` cấm tính/trả giá post-cutover và cấm import provider; `G28` B3 chỉ
assert diff rỗng trên module 105B (boundary, không phải implementation);
`G31` ghi **tường minh** rằng điều kiện (a) của `INV-43` thuộc `TASK-105E`;
task file "Ngoài Phạm Vi" + data contract §16.1 nhất quán. **Không phát hiện
absorb.** Một điểm stale văn bản ở §16.1 → `HB-105D-F2-02`.

### 9.2 Pre-cutover (§15)

`sale_date < 2026-09-01` → `G01` bắt buộc `spy_call_count == 0` trên resolver,
catalog snapshot **và** price provider, ở **cả hai** nhánh (có entry và không
có entry). Chỉ hai kết cục: `HISTORICAL_CONFIRMED` |
`PENDING_HISTORICAL_CONFIRMATION`. Late import dùng `sale_date`
(fixture 3), không `import_date` (`INV-48`). Cấm backfill catalog/giá hiện tại
(`INV-54`, §14.3, nêu trong `FAIL khi`). **ĐẠT — không finding.**

### 9.3 Ready data dependency (§16)

Claim: dataset production thật **không** phải blocker của Ready Gate.
**Xác nhận ĐÚNG**, kiểm chứng độc lập:

1. `INV-46` cho registry rỗng một kết cục xác định:
   `PENDING_HISTORICAL_CONFIRMATION` — deterministic, không phải lỗi.
2. §14.3 cấm tuyệt đối coi "store rỗng" là lỗi cần vá bằng dữ liệu bịa; store
   rỗng là trạng thái khởi đầu ĐÚNG và Pending là kết quả ĐÚNG (`DEC-103`).
3. `INV-79` rollback = tắt feature flag; `PendingPriceProvider` vẫn default,
   nên implementation không chạm production path.
4. Ready Gate liệt kê data dependency ở mục riêng, **ngoài** danh sách blocker.

Synthetic fixture được dùng cho implementation test (tiền lệ `TASK-105B`), và
§14.3 cấm invent production mapping. **PASS — không finding.**

### 9.4 Repair budget (§24)

```text
TASK-105D : 2 allowed / 0 used / 2 remaining     (khớp kỳ vọng brief)
```

Independent freeze review **không** tiêu repair cycle (`V4.1` §3 — cycle tính
theo cumulative repair diff của implementation; phiên này sửa 0 dòng code/test).
Phiên này **không** repair BLOCKING (không có BLOCKING để repair).

---

## 10. FINDINGS

### BLOCKING

```text
KHÔNG CÓ.   (0 finding)
```

Cả năm BLOCKING của attempt #1 (`F-01`…`F-05`) đã đóng, xác minh độc lập ở §4.

### HARDENING

**`HB-105D-F2-01` — Data contract §3.3 câu 8 mô tả `ResolutionBinding` là "bộ
ba", trái với schema `E-L` và `INV-55` ("CẢ BỐN").**

```text
§3.3 câu 8 : "ResolutionBinding (E-L) = bộ ba (pp_version_id,
              tracking_capture_id, mapping_store_revision). Ghim cả ba…"
§10.1 E-L  : pp_version_id, tracking_capture_id, mapping_store_revision,
              registry_revision   — bốn trường REQUIRED IMMUTABLE
INV-55     : "Ghim CẢ BỐN revision, không ghim từng phần."
```

Phân loại **HARDENING**, không BLOCKING, vì `V4.1` §11 (Artifact Internal
Precedence) giải quyết xung đột này một cách **cơ học**: trong cùng một
artifact, schema/enum/machine-readable rule thắng prose explanation. §3.3 là
bảng Q&A giải thích; `E-L` + `INV-55` là quy phạm. Reviewer độc lập **không
phải hỏi Owner**. `CHECK-105D-21` Phần C đã assert đúng bốn thành phần, nên
đường lỗi (ghim thiếu `registry_revision` → replay pre-cutover lệch) bị chính
gate chặn. Không dựng được production path theo `V4.1` §5.

`V4.1` §11 yêu cầu divergence **phải được báo cáo và sửa bằng authority hợp
lệ** — đây là báo cáo đó. Sửa §3.3 là thay đổi data contract, ngoài thẩm quyền
một phiên freeze.
*Re-trigger:* phiên sửa data contract có thẩm quyền (cùng phiên đóng `H-05`),
hoặc phiên implementation chạm `ResolutionBinding` — tuỳ phiên nào đến trước.

---

**`HB-105D-F2-02` — Data contract §16.1 stale ở hai điểm.**

```text
(a) §16.1 : "CHƯA CÓ CHỦ  lớp composition P00–P11 → KpiPurchasePrice"
    trái §16.3 ngay dưới ("Kết quả: GRANTED … TASK-105E") và DEC-156 §5.
(b) §16.1 liệt kê TASK-105D sở hữu "E-F/E-G/E-H/E-I/E-J/E-K/E-L" — thiếu
    E-A/E-B/E-C (PublicPurchaseSourceVersion + hai projection) và E-D
    (TrackingCatalogSnapshot), trong khi G10/G17/G26/G28 đặt nghĩa vụ của
    chúng lên TASK-105D.
```

Phân loại **HARDENING**: §16.3 nằm ngay dưới và nói rõ `GRANTED`, nên (a) tự
giải trong cùng artifact; (b) là một bảng tóm tắt không đầy đủ, còn nghĩa vụ
quy phạm đã nằm trong gate (`G28` B3 nói "Đường đi hợp lệ DUY NHẤT là một
`PublicPurchaseSourceLoader` riêng"), nên implementation không có chỗ hiểu
nhầm. Không có production path hiện tại. Rủi ro thật là một phiên sau đọc
§16.1 rồi tranh cãi loader thuộc 105B hay 105E.
*Re-trigger:* phiên soạn Scope Lock + Completion Gate cho `TASK-105E` (phiên
đó phải chạm đúng bảng ownership này).

---

**`HB-105D-F2-03` — 13 invariant của data contract không có gate assertion
riêng; chúng chỉ dựa vào điều khoản quét của `Exit Criteria`.**

```text
INV-51/52/53  toàn vẹn + correction của HistoricalConfirmedRegistry
              (INV-51: source_report_ref phải trỏ tới bằng chứng mở lại được —
               cấm "chủ dự án đã xác nhận" dạng prose không artifact)
INV-65        backup/export tương đương bit
INV-79…82     migration/rollback không phá huỷ
INV-84/85/86  metrics (INV-85 cấm feedback loop hạ ngưỡng; INV-86 cấm log PII)
INV-26        chiều dấu tiếng Việt/punctuation của khoá (model-token đã phủ
              qua INV-27/G06)
INV-08        cố ý ngoài scope — do FilePriceProvider (FROZEN) thi hành
```

Phân loại **HARDENING** theo `V4.1` §5: không dựng được production path hiện
tại từ bốn nguồn (chưa có implementation, chưa có dataset, chưa có config,
không Golden test nào phủ). `Exit Criteria` giữ nguyên điều khoản quét
"Toàn bộ invariant `INV-01`…`INV-87` … có assertion tương ứng hoặc có lý do
ghi rõ" + "Independent Review E2 PASS", nên chúng vẫn chặn `DONE`. Ghi lại
tường minh để phiên implementation không đọc "32/32 PASS" thành "mọi invariant
đã được test".

Ghi chú: đây là finding **mới**, không có trong attempt #1 — attempt #1 chấm
`HistoricalConfirmedRegistry` là "ĐẠT" qua `G01`, nhưng `G01` chỉ phủ
`INV-46`…`50` và `INV-54`.
*Re-trigger:* phiên implementation chạm đường ghi/correction của
`HistoricalConfirmedRegistry`, hoặc migration/rollback, hoặc module metrics —
tuỳ phiên nào đến trước.

---

**`H-05` — `ranking_method_id` OPTIONAL (§6.7) nhưng là input được hash vào
`evidence_fingerprint` (§7.3).** *(Kế thừa — predecessor: `H-05` của
`docs/reviews/TASK-105D-FREEZE-FINALIZATION-REVIEW.md`, giữ OPEN bởi `S037`.)*

Review độc lập phân loại lại theo brief §13, **không** kế thừa nhãn của
`S037`:

```text
BLOCKING?      KHÔNG.
HARDENING?     CÓ.
OUT_OF_SCOPE?  KHÔNG — nó thuộc contract của TASK-105D (§6.7/§7.3).
```

Lập luận: nếu `ranking_method_id` vắng, chiều "thuật toán xếp hạng đã đổi" của
`INV-35` im lặng biến mất và một candidate đã bị từ chối không được đề xuất
lại. Hệ quả là **đề xuất bị thiếu → identity ở lại `PENDING`**, mà `PENDING`
là kết cục **hợp lệ và an toàn** đã định nghĩa (`INV-37`, §14.3, `DEC-103`) —
không phải mapping sai, không phải hỏng dữ liệu, không phải sai tiền. Vì vậy
nó **không** phá production/data-integrity semantics và không được nâng thành
BLOCKING. Đồng thời không được hạ khỏi HARDENING: nó làm mất một chiều của
một invariant quy phạm.

Quan sát bổ sung của phiên này (không có trong attempt #1): bốn fixture bắt
buộc của `CHECK-105D-12` chỉ diễn tập chiều `pp_version_id`; **không** fixture
nào diễn tập chiều `ranking_method_id`. Ghi kèm vào cùng re-trigger.

Sửa `ranking_method_id` `OPTIONAL → REQUIRED` (hoặc quy định sentinel) là thay
đổi **data contract** §6.7 — ngoài thẩm quyền của phiên freeze này, đúng như
`S037` đã kết luận. Phiên này **không** tự sửa.
*Re-trigger (bắt buộc, tường minh):* phiên sửa data contract có thẩm quyền,
**hoặc** phiên implementation chạm `RejectedCandidate`/candidate ranking —
tuỳ phiên nào đến trước. Khi trigger, phải xử lý cả hai phần: (i) trạng thái
`OPTIONAL` của trường; (ii) thiếu fixture chiều `ranking_method_id` ở `G12`.

### OUT_OF_SCOPE

Kế thừa nguyên trạng từ attempt #1, phiên này không chạm:

- **`O-01`** — biến `P00–P11` thành executable gate → `TASK-105E`
  (`DEC-156` §5).
- **`O-02`** — refreeze Scope Lock/Completion Gate của `TASK-105C` — lineage
  riêng (`2/0/2`), phiên riêng.
- **`O-03`** — `OS-154-01` — vẫn mở, vẫn ngoài scope.

### Quan hệ giữa các finding

```text
HB-105D-F2-01, HB-105D-F2-02  ← cùng loại: prose stale trong data contract,
                                 giải được bằng V4.1 §11, gate đã đúng
HB-105D-F2-03                 ← độc lập: coverage gap giữa invariant set và
                                 gate set; predecessor gần nhất là ghi chú
                                 INV-65 của attempt #1 (nay mở rộng)
H-05                          ← kế thừa nguyên trạng, predecessor nêu tường minh
Không finding nào là duplicate không-link của finding khác.
```

---

## 11. FREEZE — thực hiện

Tám điều kiện của brief §18:

```text
BLOCKING = 0                          ĐẠT
32/32 testable                        ĐẠT
32/32 deterministic                   ĐẠT
20/20 adversarial PASS                ĐẠT
Owner Ratification reflected          ĐẠT  (OR-01→G28 B; OR-02→khối định nghĩa
                                            + G06 + G23; OR-03→G20 B + G21 B)
no unresolved contradiction           ĐẠT  (0 trong gate set; 2 prose divergence
                                            của data contract giải bằng V4.1 §11,
                                            ghi thành HARDENING)
gate change proposal valid            ĐẠT  (§3)
governance authority valid            ĐẠT  (DEC-157 Option C, retry #1/1)
```

**FREEZE ĐƯỢC THỰC HIỆN.** Phiên này **không** sửa một dòng semantics nào của
gate trong lúc freeze — freeze chỉ ghi trạng thái.

### Freeze evidence

```text
exact source SHA        : be835b1b1b03d4e8d21656c3624b6e4bc964b7a1
canonical gate artifact : docs/tasks/TASK-105D-product-identity-resolver.md
                          → mục "Completion Gate"
gate count              : 32   (CHECK-105D-01 … CHECK-105D-32)
Priority                : 32/32 REQUIRED
Evidence Level          : E2 = 19, E1 = 13   (0 hạ, 2 nâng tại S037)
Status tại freeze       : 32/32 NOT_TESTED   (freeze là freeze SEMANTICS,
                                              không phải tuyên bố đã test)
GATE_SET_SHA256         : 0444e58c02b04804a116c140af722ffc29ea64adf468aa6c93794c4408a5c877
                          (khối "### Gate G01–G08" … trước "### Ma trận overlap
                           có chủ đích", 57.614 byte UTF-8)
COMPLETION_GATE_SECTION_SHA256
                        : 3027899c5a4534921ed16d7f5737d2abd82c30e11708bb1b18bf74a7b88ba19f
                          ("## Completion Gate" … trước "## Tiêu Chí Hoàn Thành")
TASK_FILE_SHA256        : a6be1ac71ac751eeefae30cf076f90e5d4cad80067c9441f78578e9972e028b1
TASK_FILE_GIT_BLOB      : 804ba8379e0952a2210559c7eec86b4094957026
reviewer                : Independent Freeze Finalization session S038
                          (read-only reviewer đối với gate semantics;
                           thẩm quyền FROZEN theo V4.1 §12)
timestamp               : 2026-08-28
evidence level (review) : E2 — validator + Golden + full suite thực thi, output
                          trích nguyên văn (§13); ma trận gate dựng từ văn bản
                          canonical, không từ báo cáo của phiên trước
prior failed attempt    : #1 — S036, base 9cd8714, FAIL (5 BLOCKING/5 HARDENING/
                          3 OUT_OF_SCOPE)
change proposal lineage : docs/reviews/TASK-105D-COMPLETION-GATE-CHANGE-PROPOSAL.md
                          (S037, DEC-157, base 1676e1d) → gate revision #1
                          → freeze attempt #2 (artifact này)
```

Bất kỳ thay đổi nào sau này lên khối gate làm đổi `GATE_SET_SHA256` đều là
**thay đổi gate đã frozen**, cần một `COMPLETION GATE CHANGE PROPOSAL` mới +
authority theo `governance/core/TASK_COMPLETION_GATE_STANDARD.md`.

---

## 12. Ready transition

Ready Gate của `TASK-105D` liệt kê **đúng một** blocker còn lại: Completion
Gate freeze. Blocker đó nay đóng.

```text
Ready blockers : 4 (trước S034) → 2 (sau S034) → 1 (sau DEC-156) → 0 (phiên này)

TASK-105D = READY
```

Ghi rõ, theo yêu cầu brief §20:

```text
READY  ≠  IMPLEMENTED
READY  ≠  DONE
```

`READY` chỉ có nghĩa: Ready Gate không còn blocker, và một phiên
implementation **có thể được cấp phép**. Phiên này **không** implement.
Ngoài ra `DEC-157` §2 ràng buộc thêm: **không** mở implementation trước khi
divergence review point (§14) có quyết định của Owner.

---

## 13. Validation — base vs final

Phiên này không sửa `app/**`, `tests/**`, `config/**`, `tools/**`,
`scripts/**`, `pyproject.toml`; base và final vì vậy phải bằng nhau.

| Validator | Base (`be835b1`) | Final | Regression |
|---|---|---|---|
| `validate_structure` | PASS — 21 required paths | PASS | KHÔNG |
| `validate_project_state` | PASS | PASS | KHÔNG |
| `validate_evidence` | PASS — 88 REQUIRED PASS record | PASS | KHÔNG |
| `validate_task_completion` | PASS — 6 DONE task | PASS | KHÔNG |
| `validate_reference_integrity` | FAIL — đúng 3 issue `TASK-REM-T06` | FAIL — đúng 3 issue `TASK-REM-T06` | KHÔNG |
| `branch_authority_check.sh` | `AUTHORITY_OK` | `AUTHORITY_OK` | KHÔNG |
| `git diff --check` | sạch | sạch | KHÔNG |

Reference-integrity khớp chính xác baseline đã công bố — đúng 3 issue
`TASK-REM-T06`, nêu không backtick vì đây là output validator: /README.md,
CODE_OF_CONDUCT.md, CONTRIBUTING.md.

Golden + full suite (Effective Risk `HIGH` → chạy đầy đủ):

```text
tests/test_golden_baseline.py : 58 passed, 2 skipped
full suite                    : 756 passed, 11 skipped
```

Khớp nguyên văn baseline kỳ vọng (`58 passed, 2 skipped` / `756 passed,
11 skipped`). **Không regression.**

---

## 14. Divergence review point (`DEC-157` §2 — BẮT BUỘC, ngay sau verdict)

Thực hiện ngay sau freeze verdict, không im lặng đi tiếp.

```text
Đo tại HEAD của phiên review (be835b1, trước commit của chính phiên này):
  ahead default   : 7 commit        (ngưỡng: > 10)      OK
  behind default  : 0 commit
  divergence days : 0               (ngưỡng: > 3)       OK
  cumulative LOC  : 8.703           (ngưỡng: > 5.000)   VƯỢT
  DIVERGENCE      : INTEGRATION_DECISION_REQUIRED [ loc>5000 ]
  AUTHORITY       : BRANCH_WITH_UPSTREAM
  RESULT          : AUTHORITY_OK
```

Phân tách LOC (`git diff --shortstat 573e051..be835b1`):

```text
18 file changed, 8.639 insertions(+), 64 deletions(-)
production LOC    : 0     (app/**, tests/**, config/**, tools/**, scripts/**,
                           pyproject.toml — diff RỖNG, xác minh độc lập)
documentation LOC : 8.639 (governance/state/task/spec/review/session)
```

```text
Trạng thái hiện tại:
  Completion Gate TASK-105D = FROZEN (phiên này)
  TASK-105D                 = READY
  Scope của Option C đã DÙNG HẾT: (1) Gate Revision S037 ✔
                                  (2) MỘT Freeze Finalization retry ✔ (phiên này)
  Merge/conflict risk       : rủi ro XUNG ĐỘT VĂN BẢN, không phải rủi ro hành vi
                              (production diff = 0). 18 file, tập trung ở
                              PROJECT/* và docs/*; nhánh behind = 0 nên chưa có
                              conflict thực tế tại thời điểm đo.
```

**Recommendation của reviewer: (A) INTEGRATE / MERGE SỚM.**

Lý do:

1. Lý do Owner chọn Option C tại `DEC-157` ("phần việc còn lại chỉ là gate
   correction + freeze") **đã hết hiệu lực** — cả hai việc đó nay xong.
2. Scope mà Option C cho phép đã dùng hết đúng hai mục; tiếp tục divergence
   sẽ là **gia hạn**, mà phiên này không có thẩm quyền tự cấp.
3. LOC vượt ngưỡng 74% và chỉ tăng thêm nếu chờ; production diff = 0 nên merge
   là thao tác rủi ro thấp nhất có thể, và `behind = 0` nghĩa là merge ngay
   bây giờ không phải giải conflict nào.
4. Việc tiếp theo của lineage (implementation `TASK-105D`) sẽ **chạm
   production code**. Mở implementation trên một nhánh đã vượt ngưỡng
   documentation làm rủi ro merge chuyển từ "văn bản" sang "hành vi".

```text
OWNER DECISION REQUIRED — V4.1 §8
Phiên này KHÔNG tự chọn phương án, KHÔNG merge, và KHÔNG tự gia hạn Option C.
```

Ràng buộc `DEC-157` §2 vẫn hiệu lực cho tới khi Owner quyết định:
**KHÔNG mở `TASK-105D` implementation trước divergence decision này**, kể cả
khi freeze verdict là PASS và `TASK-105D` đã `READY`.

---

## 15. Production diff

```text
git diff --stat 573e051..be835b1 -- app tests config tools scripts pyproject.toml
→ (rỗng)
```

```text
production implementation changed : NO
test implementation changed       : NO
Tracking changed                  : NO   (repo khác, 0 file)
FilePriceProvider activated       : NO   (PendingPriceProvider vẫn default)
TASK-105D implemented             : NO
```

---

## 16. Trạng thái sau review

```text
TASK-105D  = READY
             Completion Gate 32 check = FROZEN (phiên này)
             Status field = PLANNED → READY
             32/32 NOT_TESTED (freeze semantics, chưa test)
             implementation = NOT STARTED; NOT AUTHORIZED (chờ divergence
                              decision theo DEC-157 §2)
             budget = 2 allowed / 0 used / 2 remaining

TASK-105C  = BLOCKED / NOT AUTHORIZED          (không đổi)
TASK-105B  = FROZEN (DEC-153) / DONE           (không đổi; không chạm)
TASK-105E  = PLANNED / OUTLINE / READY GATE BLOCKED / NOT IMPLEMENTED
                                               (không đổi)
TASK-108B  = BLOCKED_BY_DEPENDENCY — blocker `TASK-105D` chuyển từ
             "gate chưa freeze được" sang "chờ implementation";
             ba blocker còn lại (TASK-105C, TASK-105E, TASK-105B-Q3)
             KHÔNG đổi. TASK-108B vẫn KHÔNG unblocked.
```

---

## 17. NEXT AUTHORIZED ACTION

```text
1. OWNER DECISION — V4.1 §8 divergence (§14 của artifact này).
   Reviewer recommendation: (A) integrate/merge sớm.
   Đây là việc PHẢI làm trước, theo DEC-157 §2.

2. Chỉ SAU quyết định đó: một phiên implementation TASK-105D được cấp phép
   riêng, chạy trên Completion Gate đã FROZEN (32 check, GATE_SET_SHA256
   0444e58c…). Phiên đó phải xử lý HB-105D-F2-03 và H-05 khi chạm đúng vùng
   re-trigger.

Song song, không bị chặn bởi hai việc trên:
   - phiên sửa data contract có thẩm quyền: H-05 + HB-105D-F2-01;
   - phiên soạn Scope Lock + Completion Gate cho TASK-105E: HB-105D-F2-02;
   - refreeze TASK-105C (lineage riêng);
   - Owner cung cấp dữ liệu thật (PublicPurchaseSourceVersion đầu tiên,
     TrackingCatalogSnapshot đầu tiên, báo cáo lịch sử Owner-confirmed).
```

---

## 18. Điều phiên này KHÔNG làm

```text
- Không sửa app/**, tests/**, config/**, tools/**, scripts/**, pyproject.toml.
- Không sửa một dòng semantics nào của 32 gate (freeze chỉ ghi trạng thái).
- Không sửa docs/spec/TASK-105D-DATA-CONTRACT.md — H-05, HB-105D-F2-01,
  HB-105D-F2-02 vì vậy còn mở.
- Không implement TASK-105B, TASK-105C, TASK-105D, TASK-105E, TASK-108B.
- Không activate FilePriceProvider; không thay PendingPriceProvider.
- Không sửa repo Tracking; không tạo mapping/dataset production.
- Không merge vào nhánh mặc định; không đổi nhánh mặc định.
- Không mở Repair Cycle; không tiêu review budget.
- Không tự gia hạn V4.1 §8 Option C; không tự chọn phương án divergence.
- Không mở TASK-105D implementation.
- Không hạ tiêu chuẩn bất kỳ gate nào để đạt PASS.
- Không sửa governance/core/V4_1_POLICY_FREEZE.md hay artifact lịch sử.
```
