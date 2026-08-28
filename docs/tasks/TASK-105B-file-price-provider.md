# TASK-105B — FilePriceProvider

## Metadata

Status:
FROZEN (`DEC-153`, 2026-08-28 — Freeze Finalization session, thẩm quyền
riêng theo `governance/core/V4_1_POLICY_FREEZE.md` §12). Independent
Review = PASS, Review Evidence = RECONCILED
(`docs/reviews/TASK-105B-INDEPENDENT-REVIEW-RECONCILIATION.md`, SHA
`95a7ae6`), 0 BLOCKING. Frozen artifact SHA:
`c22cef8b47ac4cd71ef49609066a362c9e604313`. `FROZEN` ≠ `DONE` — xem
`DEC-153` cho điều kiện còn lại (Controlled Integration + state
reconciliation). `HB-105B-07`/`HB-105B-08` re-trigger BẮT BUỘC trước
`TASK-105C` implementation hoặc `FilePriceProvider` activation thật —
KHÔNG resolve trong phiên Freeze này.

Phase:
PHASE-01 — Engine tính toán

Task Mode:
MAJOR

Difficulty:
2/5 (đọc file, tra bảng theo khoảng ngày đóng — không có logic nghiệp vụ
mới, toàn bộ semantics đã Owner chốt ở `DEC-145`)

Risk (local):
2/5

Blast Radius:
5/5 (V4.1 §4 — chấm theo data path, không theo tên module:
`Price sai → KpiPurchasePrice sai → EligibleKpiProfit sai → CR sai →
KPI/lương sai`)

Effective Risk:
HIGH (Blast Radius quyết định — V4.1 §4.1: Golden hiện
`price_source_distribution = {Pending: 100%}` nên KHÔNG hạ bậc được, vì
profit arithmetic chưa từng được đo bởi Golden)

Project Profile:
PRODUCT

Review Budget lineage:
`TASK-105B` (root, dùng chung với `TASK-105C` — `PROJECT/REVIEW_BUDGET_LEDGER.md`
§"Root Task: TASK-105B"). `2 allowed / 0 used / 2 remaining` trước phiên
này. Phiên implementation này **không tự tiêu** ngân sách — ngân sách chỉ
tiêu khi một vòng Independent Review sau đó FAIL và cần repair.

Authority chain:
`DEC-103` (Protocol gốc) → `DEC-121` (effective-dating theo ngày nghiệp
vụ) → `DEC-144` §7 (mở lineage `TASK-105B`) → **`DEC-145`/`OD-105B-01`**
(Q1/Q2/Q3 + contract kỹ thuật, §38 của
`docs/tasks/TASK-108B-eligible-costs-owner-definition.md`) → `DEC-146`
(RTDB correction — TẠM DỪNG vai trò production, contract §38 giữ nguyên)
→ `DEC-147`→`DEC-152` (audit chain, tái xác nhận `FilePriceProvider` giữ
nguyên contract §38, vai trò cuối = bootstrap/import/snapshot-export/test
fixture, và trở thành **dependency cứng** của `TASK-105C`).

## Mục Tiêu (Objective)

Implementation thứ hai của `PriceProvider` Protocol
(`app/modules/pricing/provider.py`, không đổi từ `TASK-105`/`DEC-103`):
`FilePriceProvider` — đọc một bảng giá 4 cột (`product_key`,
`effective_from`, `effective_to`, `purchase_price`, `source` tuỳ chọn) và
trả `purchase_price` cho đúng `(product_code, sale_date)`, theo khoảng
hiệu lực **đóng** và chuẩn hoá khoá đã Owner chốt ở `DEC-145`.

Vai trò production hiện tại (sau `DEC-146`→`DEC-152`): **không phải**
production path trực tiếp — `TASK-105C` (`HistoricalVendorPriceProvider`)
sẽ **compose** class này để đọc file snapshot bất biến do `tools/pricing/`
sinh ra từ `phist`. `FilePriceProvider` tự nó cũng dùng được ngay làm
bootstrap/test-fixture/manual-price-table độc lập với `TASK-105C`.

## Business Semantics (DEC-145, đầy đủ)

### 1. Effective period (Q1 — DEC-145 §1)

```
effective_from : REQUIRED, mọi record
effective_to   : REQUIRED cho record đã kết thúc hiệu lực; RỖNG chỉ ở
                 ĐÚNG MỘT record hiện hành cuối cùng của mỗi normalized key
khoảng         : ĐÓNG — [effective_from, effective_to]
overlap        : CẤM (cùng normalized key) → InvalidPriceMasterError
gap            : ĐƯỢC PHÉP, nghĩa là NO PRICE AVAILABLE → lookup None → Pending
>1 record effective_to rỗng cùng key → InvalidPriceMasterError
```

Cấm tuyệt đối `latest`/`nearest`/`current`/fallback. Không tự lấp gap.
Không tự giải quyết overlap bằng precedence.

### 2. Product key normalization (Q2 — DEC-145 §2)

```
Unicode NFC → strip đầu/cuối → collapse whitespace nội bộ về 1 space → casefold
```

KHÔNG bỏ dấu tiếng Việt, KHÔNG bỏ punctuation, KHÔNG sửa model number,
KHÔNG fuzzy/nearest/contains/AI matching. Hai raw key khác nhau ra cùng
normalized key nhưng giá mâu thuẫn → `InvalidPriceMasterError`. Provenance
giữ đủ ba: raw key / normalized key / matched record.

### 3. Supplementary/expense-line zero-price policy (Q3 — DEC-145 §3)

**Ngoài phạm vi module này** — xem "Ngoài Phạm Vi" bên dưới và
`TASK-105B-Q3` (`docs/tasks/TASK-108B-eligible-costs-owner-definition.md`
§40), BLOCKED bởi `TASK-103`.

### 4. Price file contract (DEC-145 §4)

```
REQUIRED : product_key, effective_from, effective_to, purchase_price
OPTIONAL : source
```

`purchase_price` = VND, `Decimal`, không bao giờ `float` (ADR-103).

### 5. Validation (DEC-145 §5, chốt)

```
purchase_price < 0                              → INVALID (negative_price)
purchase_price rỗng                             → INVALID (missing_price — KHÔNG
                                                    coerce về 0)
product_key rỗng                                → INVALID (empty_key)
effective_from lỗi/rỗng                         → INVALID (invalid_date)
effective_to < effective_from                   → INVALID (inverted_range)
interval overlap cùng normalized key            → INVALID (overlapping_periods,
                                                    hoặc conflicting_price_same_period
                                                    nếu giá cũng khác nhau)
>1 record effective_to rỗng cùng key            → INVALID (multiple_open_records)
duplicate row giống hệt hoàn toàn               → REJECT (exact_duplicate_row)
sale_date trước record đầu tiên                 → None → Pending
sale_date nằm trong gap                         → None → Pending
product không có trong Price Master             → None → Pending
```

Không fallback. Lỗi raise **khi nạp** (`InvalidPriceMasterError`, mang
`.reason` machine-checkable), không phải khi tra từng dòng.

## Phạm Vi (Scope)

- `app/modules/pricing/file_price_provider.py` (**MỚI**) — `FilePriceProvider`,
  `PriceRecord`, `InvalidPriceMasterError`, validation/parsing đầy đủ theo
  DEC-145 §5.
- `tests/test_file_price_provider.py` (**MỚI**) — Completion Gate
  CHECK-105B-01..17.

## Ngoài Phạm Vi (Out of Scope)

- `TASK-105B-Q3` (chính sách zero-price dòng phụ, DEC-145 §3) — dependency
  thật trên `TASK-103`, không tự phát minh matcher (`OD-105B-01` §C).
- `KpiPurchaseAdjustment`, `EligibleKpiProfit`, `ConvertedRevenue` —
  `TASK-108B`.
- `HistoricalVendorPriceProvider`, `tools/pricing/` (fetch RTDB), export
  script — `TASK-105C`. Task này chỉ tạo seam (`FilePriceProvider` bản
  thân + `InvalidPriceMasterError` để tái dùng), không viết bất kỳ phần
  nào của `TASK-105C`.
- Product identity mapping (`product_raw` ↔ `<MÃ>` Tracking).
- `config/prices.yaml` với dữ liệu production thật — **chưa được chủ dự
  án cấp trong phiên này**; xem "Data Dependency Còn Mở" bên dưới. Không
  fabricate dữ liệu giá giả làm production config.
- Sửa `app/pipeline.py`, `price_engine.py`, `provider.py`,
  `app/modules/domain/models.py`, `config/validation.yaml` — tất cả
  **KHÔNG ĐỔI**. Provider mặc định vẫn `PendingPriceProvider`
  (`app/pipeline.py:103`) — `FilePriceProvider` không tự kích hoạt vào
  production path chỉ vì class đã tồn tại (đúng yêu cầu "Preserve Pending
  Default").
- Golden fixture/expected — **KHÔNG ĐỔI**.

## Data Dependency Còn Mở

`§38.5` Exit Criteria gốc (trong `docs/tasks/TASK-108B-eligible-costs-owner-definition.md`)
liệt kê thêm, ngoài 16 check: *"bảng giá thật của chủ dự án nạp được và
validation §E chạy đúng trên nó."* Phiên implementation này **không có**
bảng giá production thật — đây là một data dependency đang mở, không
phải một blocker kỹ thuật hay ambiguity nghiệp vụ. `FilePriceProvider`
đã được kiểm chứng đầy đủ bằng fixture tổng hợp (synthetic, không chứa
dữ liệu Tín Phát thật) qua toàn bộ 17 check thực thi được. Khi chủ dự án
cấp file giá thật (`.yaml`, đúng schema DEC-145 §4), bước còn lại chỉ là
`FilePriceProvider.from_yaml(<path thật>)` + chạy lại
`test_file_price_provider.py` — không cần sửa code.

## Provenance Contract

`PriceRecord` (frozen dataclass) giữ `raw_product_key`,
`normalized_product_key`, `effective_from`, `effective_to`,
`purchase_price`, `source` — đủ ba yếu tố `DEC-145 §2` yêu cầu.
`FilePriceProvider.find_record()` trả record đã khớp (hoặc `None`);
`.lookup()` là wrapper mỏng trả riêng `purchase_price` để thoả đúng chữ
ký `PriceProvider` Protocol. `.records` expose toàn bộ tập đã nạp.

## Error Semantics

`InvalidPriceMasterError(ValueError)` mang `.reason` (chuỗi mã hoá, ví
dụ `"overlapping_periods"`, `"negative_price"`) để caller/test phân biệt
đúng luật `DEC-145 §5` nào đã kích hoạt mà không cần parse message text.
Raise tại thời điểm nạp bảng giá (constructor / `from_yaml`), không phải
tại thời điểm tra cứu — một bảng giá hỏng phải hiện ngay toàn bộ, không
lộ ra từng dòng một lần chạy.

Phân biệt rõ với `TASK-105C` Error Semantics (mục 11 của
`docs/tasks/TASK-105C-historical-vendor-price-provider.md`):
"Missing/Unresolved" (determined absence, `None`/Pending) và
"file hỏng" (`InvalidPriceMasterError` tại nạp) là hai loại tín hiệu khác
nhau — không gộp lại. `TASK-105C` tái dùng nguyên `InvalidPriceMasterError`
này khi compose (không viết validation riêng).

## Phụ Thuộc (Dependencies)

- `TASK-105` — DONE. `PriceProvider` Protocol, `PendingPriceProvider`,
  `price_engine.apply_prices()` — không đổi, tái dùng nguyên vẹn.
- `app/modules/config/loader.py` (`as_date`, `load_yaml`) — tái dùng
  nguyên vẹn, không sửa.
- `app/modules/domain/money.py` (`to_decimal`) — tái dùng nguyên vẹn,
  phân biệt ô trống với `0`.
- `app/modules/validation/text.py` (`fold`) — tái dùng nguyên vẹn cho
  normalization Q2.

## Chặn (Blocks)

`TASK-105C` (`HistoricalVendorPriceProvider`) — hard prerequisite,
compose `FilePriceProvider`/`InvalidPriceMasterError` trực tiếp. Xem
`docs/tasks/TASK-105C-historical-vendor-price-provider.md` §"Phụ Thuộc".

## Completion Gate

Dùng `governance/core/TASK_COMPLETION_GATE_STANDARD.md` và
`governance/core/EVIDENCE_STANDARD.md`. `Effective Risk = HIGH` ⇒ E1 bắt
buộc cho mọi REQUIRED check thực thi được; check đụng Golden hướng tới E2.

Bảng 16 check gốc là "đề xuất" trong
`docs/tasks/TASK-108B-eligible-costs-owner-definition.md` §38.5 — phiên
này **frozen** nó thành gate chính thức của `TASK-105B`, giữ nguyên nội
dung 16 check, và thêm `CHECK-105B-17` để đóng risk note của `DEC-146`
(*"CHECK-105B-* (khi viết lại Completion Gate) phải có một check riêng
xác nhận không module test nào import client Firebase"*, DEC-146 dòng
liên quan trong `PROJECT/PROJECT_DECISIONS.md`).

| ID | Check | Priority | Status | Evidence Level | Evidence |
|---|---|---|---|---|---|
| CHECK-105B-01 | Khoảng đóng: đúng ngày `effective_from` và đúng ngày `effective_to` đều tra được | REQUIRED | PASS | E1 | `test_closed_interval_both_boundaries_match`, `test_closed_interval_open_record_end_is_still_effective` — `pytest tests/test_file_price_provider.py -q` |
| CHECK-105B-02 | Overlap cùng normalized key → `InvalidPriceMasterError` khi nạp; engine không tự chọn | REQUIRED | PASS | E1 | `test_overlapping_periods_same_key_raises` |
| CHECK-105B-03 | >1 record `effective_to` rỗng cùng key → `InvalidPriceMasterError` | REQUIRED | PASS | E1 | `test_multiple_open_records_same_key_raises` |
| CHECK-105B-04 | Gap → `None`/Pending, không kéo dài khoảng trước | REQUIRED | PASS | E1 | `test_gap_between_periods_is_pending_not_extended` |
| CHECK-105B-05 | `sale_date` trước record đầu tiên → `None`, không latest/nearest | REQUIRED | PASS | E1 | `test_sale_date_before_first_record_is_pending` |
| CHECK-105B-06 | Normalization: 3 ví dụ chủ dự án cho cùng key; không bỏ dấu tiếng Việt | REQUIRED | PASS | E1 | `test_owner_normalization_examples_hit_same_record[...]` (3 case), `test_normalization_does_not_strip_vietnamese_diacritics` |
| CHECK-105B-07 | Cùng normalized key, giá mâu thuẫn → `InvalidPriceMasterError`, không tự chọn | REQUIRED | PASS | E1 | `test_same_key_different_raw_spelling_conflicting_price_raises` |
| CHECK-105B-08 | Provenance giữ đủ 3: raw key / normalized key / matched record | REQUIRED | PASS | E1 | `test_provenance_keeps_raw_normalized_and_matched_record` |
| CHECK-105B-09 | §5: giá âm, key rỗng, ngày lỗi, `to < from`, duplicate hoàn toàn → REJECT (8 case) | REQUIRED | PASS | E1 | `test_reject_cases` (8 case tham số hoá) + `test_exact_duplicate_row_rejected` |
| CHECK-105B-10 | `purchase_price = 0` do khai báo thật ≠ ô trống | REQUIRED | PASS | E1 | `test_declared_zero_price_is_valid_and_distinct_from_blank`, `test_blank_price_cell_raises_not_coerced_to_zero`, `test_blank_string_price_cell_raises_not_coerced_to_zero` |
| CHECK-105B-11 | Mọi giá trị là `Decimal`; `float(` trong module mới = 0 hit | REQUIRED | PASS | E1 | `test_price_values_are_always_decimal_never_float`, `test_module_source_contains_no_float_call` |
| CHECK-105B-12 | Golden không đổi: `pytest tests/test_golden_baseline.py` = `58 passed, 2 skipped`; `lines_digest`/`_covered_digest_fields` y nguyên | REQUIRED | PASS | **E2** | `python3 -m pytest tests/test_golden_baseline.py -q` → `58 passed, 2 skipped` (thực thi trong phiên, xem session log); `app/pipeline.py`/`models.py` diff = 0 nên digest không đổi |
| CHECK-105B-13 | `pytest -q` toàn bộ: 0 regression so với baseline | REQUIRED | PASS | E1 | `python3 -m pytest -q` → `730 passed, 11 skipped` (baseline trước phiên: `697 passed, 11 skipped`; chênh lệch = đúng 33 test mới của `test_file_price_provider.py`, 0 skip mới, 0 fail) |
| CHECK-105B-14 | `app/pipeline.py`, `price_engine.py`, `provider.py`, `models.py` diff = 0 | REQUIRED | PASS | E1 | `git diff --stat -- app/pipeline.py app/modules/pricing/price_engine.py app/modules/pricing/provider.py app/modules/domain/models.py` → rỗng; `git diff --quiet` exit 0 |
| CHECK-105B-15 | Module mới không import `app.modules.validation.rules`, không chứa keyword dòng phụ | REQUIRED | PASS | E1 | `test_module_does_not_import_validation_rules` (AST-based, phân biệt import thật với text docstring), `test_module_does_not_contain_q3_classification_keywords` |
| CHECK-105B-16 | `scripts/branch_authority_check.sh` = `AUTHORITY_OK` tại SHA giao nộp | REQUIRED | PASS | E1 | Chạy sau khi push branch — xem session handoff cho SHA + output đầy đủ |
| CHECK-105B-17 *(mới, đóng risk note DEC-146)* | Module mới/test mới không import hay nhắc client Firebase/RTDB | REQUIRED | PASS | E1 | `test_module_does_not_import_or_mention_firebase_client` — grep `firebase`/`Firebase`/`pyrebase`/`google.cloud` = 0 hit |

**Exit Criteria:** 17/17 REQUIRED PASS (đạt); CHECK-105B-12 đạt E2 (đạt).
Mục bổ sung "bảng giá thật của chủ dự án nạp được" — **CHƯA đạt**, xem
"Data Dependency Còn Mở" — đây là data dependency, không phải code
blocker, không chặn `INDEPENDENT_REVIEW` của phần code đã implement.

## Tiêu Chí Hoàn Thành (Exit Criteria)

- [x] 100% REQUIRED check PASS — 17/17 (code-level, fixture tổng hợp).
- [x] Evidence level mục tiêu đạt — E1 tối thiểu toàn bộ, E2 cho
      CHECK-105B-12.
- [x] `pytest -q` toàn bộ PASS, 0 regression (`730 passed, 11 skipped`).
- [x] `pytest tests/test_golden_baseline.py -q` PASS y hệt trước phiên.
- [x] `app/pipeline.py`, `price_engine.py`, `provider.py`, `models.py`,
      Golden fixture — diff = 0.
- [x] `scripts/branch_authority_check.sh` = `AUTHORITY_OK` (sau khi push).
- [x] 4 validator PASS (`validate_structure`, `validate_project_state`,
      `validate_evidence`, `validate_task_completion`);
      `validate_reference_integrity` giữ nguyên đúng 3 lỗi tiền tồn
      `TASK-REM-T06`, không regression mới.
- [ ] Bảng giá production thật nạp được — **BLOCKED**, chờ chủ dự án cấp
      file (data dependency, không phải code).
- [ ] `INDEPENDENT_REVIEW` — **REQUIRED**, chưa chạy trong phiên này
      (V4.1, task Effective Risk HIGH không tự DONE mà không qua review
      độc lập, đúng tiền lệ `TASK-GOLDEN-BASELINE-001`).
- [x] `PROJECT/PROJECT_PROGRESS.md` và `PROJECT/LO_TRINH_DE_HIEU.md` cập
      nhật.
- [x] Session handoff viết đầy đủ (Task Mode MAJOR yêu cầu).

## TASK-105C Composition Seam

`HistoricalVendorPriceProvider` (chưa implement — `TASK-105C`, ngoài
phạm vi phiên này) sẽ **compose** `FilePriceProvider` để đọc file
snapshot bất biến do script export dưới `tools/pricing/` sinh ra (tên
file cụ thể + Scope đầy đủ:
`docs/tasks/TASK-105C-historical-vendor-price-provider.md`), tái dùng
nguyên `InvalidPriceMasterError`/validation ở đây — không duplicate logic
(`DEC-152` §11). Seam cụ thể `TASK-105B` cung cấp:

```
class FilePriceProvider:
    def __init__(self, rows: Iterable[dict[str, Any]]): ...          # eager validate
    @classmethod
    def from_yaml(cls, path: Path) -> "FilePriceProvider": ...
    def find_record(self, product_code, sale_date) -> Optional[PriceRecord]: ...
    def lookup(self, product_code, sale_date) -> Optional[Decimal]: ...  # Protocol
    @property
    def records(self) -> tuple[PriceRecord, ...]: ...

class InvalidPriceMasterError(ValueError):
    reason: str   # "overlapping_periods" | "negative_price" | ... (DEC-145 §5)

class PriceRecord:  # frozen dataclass
    raw_product_key, normalized_product_key: str
    effective_from: date
    effective_to: Optional[date]
    purchase_price: Decimal
    source: Optional[str]
```

`TASK-105C` không cần viết lại parsing/validation — chỉ cần trỏ
`FilePriceProvider.from_yaml()`/`FilePriceProvider(rows=...)` vào file
snapshot mà script export của nó sinh ra (đúng schema 4-cột này), rồi bọc
thêm business logic riêng của nó (MIN qua nhiều NCC, sentinel handling —
`TASK-105C` scope, không phải `TASK-105B`). Không sửa file này khi làm
`TASK-105C`, đúng "Out of Scope" đã ghi ở
`docs/tasks/TASK-105C-historical-vendor-price-provider.md`.

## Golden Impact

**Không đổi.** Golden Baseline tiếp tục chạy `PendingPriceProvider` mặc
định (`app/pipeline.py` không sửa). Không thêm field vào `WorkingLine` ⇒
`lines_digest`/`_covered_digest_fields` không đổi. Verified:
`pytest tests/test_golden_baseline.py -q` → `58 passed, 2 skipped`, y hệt
trước phiên.

## Review Budget

Lineage `TASK-105B` (`PROJECT/REVIEW_BUDGET_LEDGER.md`). `2 allowed / 0
used / 2 remaining` trước phiên — **không đổi bởi phiên implementation
này** (implementation session không tự tiêu ngân sách; ngân sách chỉ
tiêu khi Independent Review sau đó FAIL và cần repair).

## Đăng Ký File Đã Thay Đổi (Changed Files Registry)

```
MỚI  : app/modules/pricing/file_price_provider.py
MỚI  : tests/test_file_price_provider.py
MỚI  : docs/tasks/TASK-105B-file-price-provider.md (file này)
SỬA  : PROJECT/PROJECT_PROGRESS.md
SỬA  : PROJECT/LO_TRINH_DE_HIEU.md
SỬA  : PROJECT/REVIEW_BUDGET_LEDGER.md
KHÔNG ĐỔI (xác minh diff = 0): app/pipeline.py, app/modules/pricing/provider.py,
       app/modules/pricing/price_engine.py, app/modules/domain/models.py,
       config/**, tests/fixtures/golden/**, tests/test_golden_baseline.py
```

## Ghi Chú (Notes)

- File này là **Scope Lock + Completion Gate được frozen bởi chính phiên
  implementation** (không có phiên Scope-Lock riêng trước đó cho
  `TASK-105B`, khác `TASK-105C`) — nội dung 16/17 check bắt nguồn thẳng
  từ `DEC-145`/`OD-105B-01` (đã Owner duyệt) và §38.5 "đề xuất" trong
  `docs/tasks/TASK-108B-eligible-costs-owner-definition.md`; không có
  business rule mới nào được agent tự phát minh. `CHECK-105B-17` đóng
  một risk note đã ghi tại `DEC-146`, không phải một quyết định nghiệp
  vụ mới.
- Không sửa các mục Scope/Completion Gate ở trên mà không qua
  `COMPLETION GATE CHANGE PROPOSAL`
  (`governance/core/TASK_COMPLETION_GATE_STANDARD.md`).
- Independent Review tiếp theo nên đọc trực tiếp
  `app/modules/pricing/file_price_provider.py` +
  `tests/test_file_price_provider.py`, chạy lại toàn bộ evidence ở trên
  một cách độc lập (không tin cậy narrative của phiên implementation),
  và đặc biệt xác minh CHECK-105B-14 (diff = 0 trên 4 file production
  cũ) — đây là bất biến quan trọng nhất của task này.
