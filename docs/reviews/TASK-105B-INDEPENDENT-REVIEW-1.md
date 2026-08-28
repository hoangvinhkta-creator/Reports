# RÀ SOÁT ĐỘC LẬP E2 — TASK-105B (FilePriceProvider)

Review ID:
`TASK-105B-INDEPENDENT-REVIEW-1` (canonical re-run — xem "Bối Cảnh Re-run")

Task / Release:
`TASK-105B` — `FilePriceProvider`. Canonical artifact:
`docs/tasks/TASK-105B-file-price-provider.md`.

Reviewer Session:
Phiên "TASK-105B — INDEPENDENT REVIEW #1 — CANONICAL RE-RUN", tách khỏi
phiên implementation (S030). Reviewer **không** viết một dòng nào của
`app/modules/pricing/file_price_provider.py` hay
`tests/test_file_price_provider.py`.

Executed By:
Claude Code (reviewer-agent session độc lập, đúng
`governance/core/EVIDENCE_STANDARD.md` → "Quy trình Review độc lập cho
Solo Developer").

Timestamp:
2026-08-28

## Target Đã Xác Minh (Authoritative Target)

```
Implementation SHA   : c22cef8b47ac4cd71ef49609066a362c9e604313
Base SHA             : c49cb67ede3f7ff4af2a49cdc338b4a31c33021c
Implementation branch: claude/price-provider-foundation-ahix1t
Review branch        : review/task-105b-independent-review-1 (tạo từ implementation SHA)
Default branch origin: claude/extract-upload-repo-gq2ws4 (tip = base SHA)
```

Evidence (E1, thực thi trong phiên):

```
$ git rev-parse c22cef8b47ac4cd71ef49609066a362c9e604313
c22cef8b47ac4cd71ef49609066a362c9e604313
$ git rev-parse origin/claude/price-provider-foundation-ahix1t
c22cef8b47ac4cd71ef49609066a362c9e604313
$ git merge-base --is-ancestor c49cb67ede3f7ff4af2a49cdc338b4a31c33021c c22cef8b47ac4cd71ef49609066a362c9e604313
YES_ANCESTOR
```

Implementation branch **KHÔNG bị mutate** bởi phiên review này: local và
remote của `claude/price-provider-foundation-ahix1t` đều đứng nguyên tại
`c22cef8`; review branch được tạo mới từ chính SHA đó và chỉ thêm một file
dưới `docs/reviews/`.

## Bối Cảnh Re-run — CONFLICT DETECTED

Brief của phiên này khẳng định: *"một review trước đó đã được báo trong chat
nhưng review artifact KHÔNG tồn tại trong Git"*. **Tiền đề này không còn
đúng với trạng thái remote hiện tại.** Reviewer quét namespace theo đúng
yêu cầu §6 của brief và tìm thấy:

```
$ for br in $(git branch -r --format='%(refname:short)'); do
      git grep -h -o "HB-105B-[0-9]\+" "$br" | sort -u; done
origin/claude/file-price-provider-review-negpxw : HB-105B-01 ... HB-105B-06
$ git log --oneline -2 origin/claude/file-price-provider-review-negpxw
b735dac docs(TASK-105B): Independent Review #1 — VERDICT PASS, ELIGIBLE_FOR_FREEZE
c22cef8 docs(TASK-105B): record branch_authority_check.sh AUTHORITY_OK evidence
$ git diff --name-status c22cef8 origin/claude/file-price-provider-review-negpxw
A  docs/reviews/TASK-105B-INDEPENDENT-REVIEW-1.md
```

Documentation (brief phiên này): artifact review #1 không tồn tại trong Git.

Implementation (trạng thái remote thật): artifact review #1 **tồn tại**, tại
`b735dac` trên nhánh `claude/file-price-provider-review-negpxw`, cha trực
tiếp là đúng implementation SHA `c22cef8`, cùng đường dẫn
`docs/reviews/TASK-105B-INDEPENDENT-REVIEW-1.md`.

Risk: hai artifact khác nội dung cùng chiếm một đường dẫn canonical trên hai
nhánh khác nhau — đúng loại lỗi mà `DEC-118` đã ghi nhận một lần
(hai session song song làm trùng công việc mà không biết về nhau).

Recommended resolution (Owner quyết, reviewer **không** tự xử lý):
1. Owner chọn MỘT trong hai artifact làm canonical, hoặc hợp nhất chúng;
2. nhánh còn lại được ghi rõ là superseded;
3. dedupe finding ID theo bảng đối chiếu ở mục "Đối Chiếu Với Artifact
   Review Song Song" bên dưới.

Reviewer **vẫn thực hiện review lại từ đầu** đúng như brief yêu cầu: không
dùng verdict cũ làm evidence, tự dựng harness đối kháng riêng, tự chạy lại
toàn bộ test và validator, tự phân loại finding từ evidence của chính mình.
Artifact song song chỉ được mở ra ở bước cuối để đối chiếu ID, sau khi các
finding của phiên này đã hình thành.

Reviewer giữ đúng đường dẫn `docs/reviews/TASK-105B-INDEPENDENT-REVIEW-1.md`
theo yêu cầu bắt buộc §12 của brief, trên một nhánh review riêng, **không**
chạm vào nhánh kia (không merge, không force-push, không xoá).

## Scope

Review độc lập toàn bộ diff `c49cb67..c22cef8`:

```
$ git diff --name-status c49cb67 c22cef8
M  PROJECT/LO_TRINH_DE_HIEU.md
M  PROJECT/PROJECT_PROGRESS.md
M  PROJECT/REVIEW_BUDGET_LEDGER.md
A  app/modules/pricing/file_price_provider.py
A  docs/sessions/S030-task-105b-file-price-provider-implementation.md
A  docs/tasks/TASK-105B-file-price-provider.md
A  tests/test_file_price_provider.py
7 files changed, 1358 insertions(+), 20 deletions(-)
```

Production diff thực chất = đúng **hai** file mới:
`app/modules/pricing/file_price_provider.py` (298 dòng) và
`tests/test_file_price_provider.py` (374 dòng). Không có file production cũ
nào bị sửa.

Integration point đã đọc (không sửa): `app/modules/pricing/provider.py`,
`app/modules/pricing/price_engine.py`, `app/pipeline.py`,
`app/modules/domain/money.py`, `app/modules/domain/models.py`,
`app/modules/config/loader.py`, `app/modules/validation/text.py`.

## Tài Liệu Đầu Vào Đã Đọc (Inputs Read)

- `CLAUDE.md` (điểm vào governance) — kể cả mục "Đồng Bộ Nhánh".
- `governance/core/EVIDENCE_STANDARD.md`.
- `governance/templates/E2_INDEPENDENT_REVIEW_TEMPLATE.md`.
- `governance/core/V4_1_POLICY_FREEZE.md` (đặc biệt §3 repair cycle, §4/§4.1
  blast radius, §5 production path decision rule, §7 finding action gate,
  §12 state authority matrix).
- `PROJECT/PROJECT_PROGRESS.md`, `PROJECT/PROJECT_DECISIONS.md`
  (`DEC-145`/`OD-105B-01` đọc nguyên văn §1–§7),
  `PROJECT/REVIEW_BUDGET_LEDGER.md` (mục "Root Task: TASK-105B").
- `docs/tasks/TASK-105B-file-price-provider.md` (Scope Lock + Completion
  Gate frozen, CHECK-105B-01..17).
- `docs/tasks/TASK-105C-historical-vendor-price-provider.md` — **chỉ** để
  kiểm tra downstream seam.
- `docs/tasks/TASK-108B-eligible-costs-owner-definition.md` §34 (namespace
  `HB-105B-01`/`HB-105B-02`).
- Actual diff/code + toàn bộ source hai file mới.

## Contract — Kết Quả Xác Minh

Chữ ký Protocol (`app/modules/pricing/provider.py`, KHÔNG đổi):

```
lookup(product_code: Optional[str], sale_date: Optional[date]) -> Optional[Decimal]
```

`FilePriceProvider.lookup()` khớp đúng chữ ký này; `find_record()` là bản
mở rộng trả record để giữ provenance. Toàn bộ frozen semantics `DEC-145`
được xác minh độc lập bằng harness đối kháng riêng (đặt **ngoài** repo, tại
scratchpad; không sửa implementation để làm test PASS):

| Semantics DEC-145 | Kết quả độc lập |
|---|---|
| normalization NFC → strip → collapse → casefold | ĐÚNG |
| khoảng hiệu lực ĐÓNG `[from,to]` | ĐÚNG (cả hai biên tra được) |
| open-ended record (`effective_to` rỗng) | ĐÚNG |
| gap → `None` | ĐÚNG (không kéo dài khoảng trước) |
| no match → `None` | ĐÚNG |
| không `latest`/`nearest`/`current`/fallback | ĐÚNG (grep + hành vi) |
| deterministic lookup | ĐÚNG (6/6 hoán vị cho 1 kết quả duy nhất) |
| provenance (raw / normalized / matched record) | ĐÚNG |
| malformed source ≠ determined absence | ĐÚNG về hành vi (luôn raise, không bao giờ hoá `None`), **nhưng sai loại exception** ở 2 nhóm input — xem `HB-105B-07`/`HB-105B-09` |

## Xác Minh Độc Lập (Independent Verification)

Toàn bộ bảng dưới là kết quả reviewer **tự chạy lại**, không copy
self-verification của phiên implementation. Evidence Level = `E2` vì người
thực thi độc lập với người triển khai (`governance/core/EVIDENCE_STANDARD.md` §E2).

| Check ID | Status | Evidence Level | Evidence | Executed By | Timestamp |
|---|---|---|---|---|---|
| CHECK-105B-01 | PASS | E2 | Reviewer chạy `pytest tests/test_file_price_provider.py -v` → `test_closed_interval_both_boundaries_match` PASSED, `test_closed_interval_open_record_end_is_still_effective` PASSED. Harness riêng B1/B2/B3/B4: `effective_from` và `effective_to` đúng ngày đều trả `Decimal('5000000')`; ngày liền sau `effective_to` và liền trước `effective_from` đều trả `None` | reviewer | 2026-08-28 |
| CHECK-105B-02 | PASS | E2 | `test_overlapping_periods_same_key_raises` PASSED. Harness B6 (khoảng kề nhau chung đúng một ngày biên), B7 (nested overlap khác giá), B8 (nested overlap cùng giá) → tất cả `InvalidPriceMasterError`, reason lần lượt `conflicting_price_same_period` / `conflicting_price_same_period` / `overlapping_periods`. Engine không tự chọn record nào | reviewer | 2026-08-28 |
| CHECK-105B-03 | PASS | E2 | `test_multiple_open_records_same_key_raises` PASSED. Harness B11 → `InvalidPriceMasterError(reason='multiple_open_records')`. Harness B9 (một record mở + một record đóng muộn hơn) cũng bị bắt đúng là overlap, không lọt | reviewer | 2026-08-28 |
| CHECK-105B-04 | PASS | E2 | `test_gap_between_periods_is_pending_not_extended` PASSED. Harness B5 → `None` giữa gap; kiểm thêm ngày liền sau khoảng trước và liền trước khoảng sau đều `None` (không kéo dài khoảng) | reviewer | 2026-08-28 |
| CHECK-105B-05 | PASS | E2 | `test_sale_date_before_first_record_is_pending`, `test_unknown_product_is_pending`, `test_lookup_with_missing_code_or_date_is_pending` PASSED. Harness B4/G1/G2 xác nhận `None`, không có nearest/latest | reviewer | 2026-08-28 |
| CHECK-105B-06 | PASS | E2 | 3 case `test_owner_normalization_examples_hit_same_record[...]` + `test_normalization_does_not_strip_vietnamese_diacritics` PASSED. Harness A1/A2 (file NFC ↔ lookup NFD và ngược lại) đều khớp; A3 xác nhận `normalized_product_key` là NFC; A4 (tab/newline/NBSP) khớp; A10 (bỏ dấu) **không** khớp — đúng lệnh cấm bỏ dấu của `DEC-145` §2 | reviewer | 2026-08-28 |
| CHECK-105B-07 | PASS | E2 | `test_same_key_different_raw_spelling_conflicting_price_raises` PASSED. Harness A7 (casefold collision `Straße`/`STRASSE`, giá khác nhau) và A8 (I có chấm kiểu Thổ Nhĩ Kỳ) → `conflicting_price_same_period`; A6/A9 (cùng giá) → `overlapping_periods`. Không trường hợp nào engine tự chọn | reviewer | 2026-08-28 |
| CHECK-105B-08 | PASS | E2 | `test_provenance_keeps_raw_normalized_and_matched_record` PASSED. Reviewer đọc trực tiếp `PriceRecord` trả về: `raw_product_key`, `normalized_product_key`, `effective_from`/`effective_to`, `purchase_price`, `source` đầy đủ; `.records` expose toàn bộ tập đã nạp | reviewer | 2026-08-28 |
| CHECK-105B-09 | PASS | E2 | 8 case `test_reject_cases[...]` PASSED với đúng `reason` từng case (`negative_price`, `empty_key` ×2, `invalid_date` ×3, `inverted_range`, `missing_price`); `test_exact_duplicate_row_rejected` PASSED. Harness F1 xác nhận một dòng hỏng làm cả bảng từ chối nạp — không âm thầm hoá `None` | reviewer | 2026-08-28 |
| CHECK-105B-10 | PASS | E2 | `test_declared_zero_price_is_valid_and_distinct_from_blank`, `test_blank_price_cell_raises_not_coerced_to_zero`, `test_blank_string_price_cell_raises_not_coerced_to_zero` PASSED. Harness D13 → `Decimal('0')` hợp lệ; ô trống/`"   "` → `missing_price`, không coerce | reviewer | 2026-08-28 |
| CHECK-105B-11 | PASS | E2 | `grep -c "float(" app/modules/pricing/file_price_provider.py` → `0`; `grep -n "float"` → không có hit nào ở bất kỳ dạng nào. `test_price_values_are_always_decimal_never_float` + `test_module_source_contains_no_float_call` PASSED. Reviewer kiểm thêm: mọi giá trị trả ra trong harness đều là `Decimal` | reviewer | 2026-08-28 |
| CHECK-105B-12 | PASS | E2 | Reviewer chạy `python3 -m pytest tests/test_golden_baseline.py -q` → `58 passed, 2 skipped in 5.03s`. `git diff --quiet c49cb67 c22cef8 -- config/ tests/fixtures/ tests/test_golden_baseline.py` → exit `0`; `app/pipeline.py` và `app/modules/domain/models.py` diff = 0 ⇒ `lines_digest`/`_covered_digest_fields` không thể đổi | reviewer | 2026-08-28 |
| CHECK-105B-13 | PASS | E2 | Reviewer chạy `python3 -m pytest -q` tại `c22cef8` → `730 passed, 11 skipped in 13.41s`. Baseline tự dựng lại độc lập: `git archive c49cb67` ra thư mục ngoài repo, chạy `python3 -m pytest -q` → `697 passed, 11 skipped in 13.13s`. Chênh lệch = đúng `+33 passed`, `0` skip mới, `0` fail — khớp chính xác 33 test mới | reviewer | 2026-08-28 |
| CHECK-105B-14 | PASS | E2 | `git diff --quiet c49cb67 c22cef8 -- app/pipeline.py app/modules/pricing/price_engine.py app/modules/pricing/provider.py app/modules/domain/models.py` → exit `0` (DIFF_ZERO). `git diff --name-only c49cb67 c22cef8 -- app tests config` → chỉ `app/modules/pricing/file_price_provider.py` và `tests/test_file_price_provider.py` | reviewer | 2026-08-28 |
| CHECK-105B-15 | PASS | E2 | Reviewer tự parse AST module: import chỉ gồm `datetime`, `dataclasses`, `decimal`, `pathlib`, `typing`, `app.modules.config.loader`, `app.modules.domain.money`, `app.modules.validation.text` — **không** có `app.modules.validation.rules`. Grep 5 keyword Q3 (`phí`, `công lắp đặt`, `chênh vat`, `chiết khấu`, `voucher`) → `0` hit mỗi keyword | reviewer | 2026-08-28 |
| CHECK-105B-16 | PASS | E2 | Reviewer chạy `bash scripts/branch_authority_check.sh` tại đúng `HEAD_SHA = c22cef8b47ac4cd71ef49609066a362c9e604313` → `WORKTREE: CLEAN`, `DIVERGENCE: WITHIN_LIMITS` (ahead default 2 commit, 0 ngày, 1378 LOC), `AUTHORITY: BRANCH_WITH_UPSTREAM`, `RESULT: AUTHORITY_OK`, exit `0` | reviewer | 2026-08-28 |
| CHECK-105B-17 | PASS | E2 | Reviewer grep `firebase\|pyrebase\|google.cloud\|rtdb` (case-insensitive) trên module → `0` hit. Trên test file: 4 hit, **tất cả** là chuỗi marker của chính assertion (`_FIREBASE_MARKERS`, tên test, comment CHECK ID) — không phải import, không phải gọi client. AST của test file: import chỉ gồm `ast`, `datetime`, `decimal`, `pathlib`, `pytest`, và module đang test. Nội dung check đạt. *Hạn chế của assertion tự động được ghi riêng tại `HB-105B-11`* | reviewer | 2026-08-28 |

**Tổng: 17/17 REQUIRED PASS, độc lập.**

### Lệnh Đã Thực Thi (Commands Executed)

```
git fetch --all --prune
git rev-parse c22cef8b47ac4cd71ef49609066a362c9e604313
git rev-parse c49cb67ede3f7ff4af2a49cdc338b4a31c33021c
git rev-parse origin/claude/price-provider-foundation-ahix1t
git merge-base --is-ancestor c49cb67 c22cef8
git diff --stat c49cb67 c22cef8
git diff --name-status c49cb67 c22cef8
git diff --quiet c49cb67 c22cef8 -- app/pipeline.py app/modules/pricing/price_engine.py \
    app/modules/pricing/provider.py app/modules/domain/models.py
git diff --quiet c49cb67 c22cef8 -- config/ tests/fixtures/ tests/test_golden_baseline.py
python3 -m pytest tests/test_file_price_provider.py -q
python3 -m pytest tests/test_file_price_provider.py -v
python3 -m pytest tests/test_golden_baseline.py -q
python3 -m pytest -q
git archive c49cb67 | tar -x -C <scratchpad>/base && (cd <scratchpad>/base && python3 -m pytest -q)
python3 <scratchpad>/adv.py      # harness đối kháng, 60 case, NGOÀI repo
python3 <scratchpad>/adv2.py     # truy vết root cause NaN/Infinity, NGOÀI repo
bash scripts/branch_authority_check.sh
python3 governance/scripts/governance/validate_structure.py
python3 governance/scripts/governance/validate_project_state.py
python3 governance/scripts/governance/validate_evidence.py
python3 governance/scripts/governance/validate_task_completion.py
python3 governance/scripts/governance/validate_reference_integrity.py
```

Môi trường: Python 3.11.15, pytest 9.1.1, PyYAML 6.0.1, openpyxl 3.1.5.

### Kết Quả Test Thực Tế (Actual, không phải expected)

```
targeted : 33 passed in 0.08s
Golden   : 58 passed, 2 skipped in 5.03s
full     : 730 passed, 11 skipped in 13.41s
base     : 697 passed, 11 skipped in 13.13s   (c49cb67, dựng lại độc lập qua git archive)
delta    : +33 passed, +0 skipped, +0 failed
```

Trùng khớp hoàn toàn với con số phiên implementation báo cáo. Không có sai
lệch nào giữa narrative của người triển khai và kết quả reviewer tự đo.

## Review Đối Kháng (Adversarial Review)

Harness riêng của reviewer, 60 case, đặt **ngoài** repository (đúng brief §4),
**không** sửa implementation để làm case PASS.

| Nhóm | Case | Kết quả |
|---|---|---|
| NFC/NFD | file NFC ↔ lookup NFD, và chiều ngược lại | khớp; `normalized_product_key` luôn NFC |
| Whitespace | tab, newline, NBSP `U+00A0`, khoảng trắng thừa đầu/cuối/giữa | collapse đúng, khớp |
| Whitespace | zero-width space `U+200B` | **không** collapse → miss → `None` (đúng: `DEC-145` §2 chỉ cho phép collapse whitespace, `U+200B` không phải whitespace) |
| Casefold collision | `Straße`/`STRASSE`, `İSTANBUL`/`i̇stanbul` | khác giá → `conflicting_price_same_period`; cùng giá → `overlapping_periods` |
| Duplicate normalized key | raw khác nhau, chuẩn hoá trùng | bị bắt, không tự chọn |
| Unordered records | 6 hoán vị của 3 record | **1 kết quả duy nhất** trên cả 6 → deterministic |
| Closed-boundary overlap | hai khoảng chung đúng một ngày biên | bị bắt là overlap (đúng, khoảng ĐÓNG) |
| Nested overlap | khoảng con nằm trong khoảng cha | bị bắt (cả khi cùng giá lẫn khác giá) |
| Multiple open records | 2 record `effective_to` rỗng | `multiple_open_records` |
| Open + closed | record mở + record đóng muộn hơn | bị bắt là overlap |
| Open + closed | record mở + record đóng **sớm hơn**, rời nhau | hợp lệ, tra đúng cả hai |
| Sentinel clash | `effective_to = 9999-12-31` tường minh + record mở | bị bắt là overlap (sentinel không tạo lỗ hổng) |
| Gap | trong gap, ngày liền sau/liền trước biên | `None`, không kéo dài |
| Exact boundary | `effective_from`, `effective_to`, khoảng một ngày | tra được |
| Invalid Decimal | `"abc"`, `bool`, `list` | `InvalidPriceMasterError(reason='invalid_price')` |
| **NaN** | `"NaN"`, `"nan"`, `"sNaN"`, `float('nan')`, `Decimal('NaN')`, YAML `.nan` | **RAW `decimal.InvalidOperation`** → `HB-105B-07` |
| **Infinity** | `"Infinity"`, `"inf"`, `float('inf')`, `Decimal('Infinity')`, YAML `.inf` | **ĐƯỢC CHẤP NHẬN làm giá hợp lệ** → `HB-105B-08` |
| -Infinity | `"-Infinity"`, `float('-inf')` | `negative_price` (bị chặn — do `< 0` đúng với `-Infinity`) |
| Magnitude | `1E+1000` | được chấp nhận → gộp vào `HB-105B-08` |
| Zero | `"0"` | hợp lệ, `Decimal('0')`, khác hẳn ô trống |
| Negative price | `"-100"` | `negative_price` |
| YAML shape | `prices:` null / root là list / row là scalar | RAW `TypeError`/`AttributeError` → `HB-105B-09` |
| Schema tolerance | thiếu hẳn cột `effective_to`; cột gõ sai tên | im lặng thành open record / im lặng bị bỏ → `HB-105B-10` |
| Malformed ≠ absence | bảng có 1 dòng hỏng | raise khi nạp, **không** trả `None` cho dòng lành |

### Tái Hiện NaN — REPRODUCED

Brief §5 yêu cầu tự reproduce, không tin claim cũ. Reviewer reproduce được:

```
NaN -> RAW decimal.InvalidOperation at file_price_provider.py:226  ->  if price < 0:
InvalidOperation MRO        : InvalidOperation, DecimalException, ArithmeticError, Exception
InvalidPriceMasterError MRO : InvalidPriceMasterError, ValueError, Exception
caught by 'except InvalidPriceMasterError'? -> False
caught by 'except ValueError'?              -> False
```

Root cause chính xác: trong `_parse_price()`, `to_decimal()` nằm trong
`try/except (TypeError, InvalidOperation)` nên `Decimal("NaN")` **dựng thành
công** và thoát khỏi khối `try`; phép so sánh `if price < 0:` ở dòng 226 nằm
**ngoài** khối đó, và so sánh thứ tự với `NaN` phát tín hiệu
`InvalidOperation` trong context `decimal` mặc định.

Đánh giá: NaN **không** lọt qua thành giá hợp lệ, và **không** bị hoá thành
`None` — bất biến "malformed source ≠ determined absence" vẫn đứng vững. Sai
lệch là ở **loại exception**: `InvalidOperation` không phải hậu duệ của
`ValueError`, nên một caller bắt `InvalidPriceMasterError` (đúng như
`docs/tasks/TASK-105C-historical-vendor-price-provider.md` mục 11 dự kiến
`TASK-105C` sẽ làm) sẽ **không** bắt được, và không có `.reason`
machine-checkable.

### Tái Hiện Infinity — REPRODUCED

```
Infinity via provider.lookup -> Infinity
  Infinity arithmetic downstream: 1_000_000 - Infinity = -Infinity
  is_finite() = False
```

`Decimal("Infinity") < 0` là `False`, nên `Infinity` đi qua trọn vẹn cả ba
cửa validation (`is None` / `< 0` / kiểu) và được `lookup()` trả về như một
giá hợp lệ. Đây là kết quả nặng hơn NaN: không có exception nào, giá trị vô
nghĩa chảy tiếp vào số học downstream.

`DEC-145` §5 **không** liệt kê một luật riêng cho `NaN`/`Infinity` — bảng
validation đã freeze chỉ nêu `purchase_price < 0 → INVALID` và điều kiện của
`purchase_price = 0`. Vì vậy đây là **khoảng trống của tập luật đã freeze**,
không phải một luật đã freeze bị vi phạm (`V4.1` §7).

## Phân Loại Finding (V4.1 §5/§7)

### Phân tích production path — điều kiện tiên quyết của mọi BLOCKING

`V4.1` §5 cho phép đúng bốn nguồn dựng input CURRENT PRODUCTION-REALISTIC.
Reviewer kiểm từng nguồn cho `FilePriceProvider`:

| Nguồn (V4.1 §5) | Trạng thái | Evidence |
|---|---|---|
| 1. production annotation/schema inventory | KHÔNG có | `FilePriceProvider` không được nối vào bất kỳ đường dữ liệu production nào |
| 2. config hiện hành trong repo | KHÔNG có | `ls config/` → `adjustments.yaml`, `conversion_rates.yaml`, `employees.yaml`, `lead_source.yaml`, `validation.yaml`. **Không có** file bảng giá |
| 3. Golden Baseline fixture | KHÔNG có | Golden chạy `PendingPriceProvider`, `price_source_distribution = {Pending: 100%}`; `git diff --quiet` trên `tests/fixtures/` = 0 |
| 4. raw production data đã xác minh | KHÔNG có | `docs/tasks/TASK-105B-file-price-provider.md` mục "Data Dependency Còn Mở" ghi rõ chủ dự án **chưa** cấp bảng giá thật |

Thêm bằng chứng cách ly: `grep -rn "FilePriceProvider"` trên toàn repo (trừ
chính module và test của nó) → **0 hit**. Không caller nào tồn tại.

Kết luận: **không dựng được production path hiện tại từ bất kỳ nguồn nào
trong bốn nguồn** ⇒ theo `V4.1` §5, HARDENING BY DEFAULT. Reviewer **không**
viện dẫn "nguồn thứ năm", **không** nâng cấp vì `TASK-105C` sắp tới (brief
§9 cấm đúng điều này), và **không** dùng lập luận "Python cho phép" /
"tôi dựng được object" làm bằng chứng production path.

### BLOCKING

**KHÔNG CÓ.**

Không finding nào chỉ ra được một tiêu chí production đã freeze (`V4.1` §5)
bị vi phạm ở trạng thái hiện tại.

### HARDENING

Namespace: `HB-105B-01`…`HB-105B-06` **đã bị chiếm** (01/02 tại
`docs/tasks/TASK-108B-eligible-costs-owner-definition.md` §34; 03–06 tại
artifact review song song). Reviewer quét toàn bộ 120 commit reachable
(`git grep -o "HB-105B-[0-9]\+" $(git rev-list --all)`) và cấp ID mới bắt
đầu từ **07**. Không ID cũ nào bị reuse hay overwrite.

---

**`HB-105B-07` — `purchase_price` là `NaN` thoát ra bằng `decimal.InvalidOperation` thô.**

Mô tả: `Decimal("NaN")` dựng thành công bên trong `try` của `_parse_price()`;
`if price < 0:` (dòng 226) nằm ngoài `try` và phát `InvalidOperation`. Loại
exception này không phải hậu duệ `ValueError`, nên `except
InvalidPriceMasterError` **không** bắt được, và không mang `.reason`.

Vì sao HARDENING chứ không BLOCKING: không có production path hiện tại (bảng
trên); và hành vi vẫn *từ chối* dữ liệu hỏng, không hoá `None` — bất biến
correctness quan trọng nhất không bị phá.

Vì sao vẫn đáng ghi: nó vi phạm Error Semantics do chính
`docs/tasks/TASK-105B-file-price-provider.md` tuyên bố ("raise
`InvalidPriceMasterError`, mang `.reason` machine-checkable"), và
`docs/tasks/TASK-105C-historical-vendor-price-provider.md` mục 11 đã đặt kế
hoạch bắt đúng exception đó.

**RE-TRIGGER CONDITION (cụ thể, gắn cơ chế):** ngay khi **bất kỳ** điều nào
sau xảy ra — (a) một file bảng giá thật xuất hiện trong `config/` và được
nạp bằng `FilePriceProvider`; (b) `TASK-105C` bắt đầu implementation
(provider của nó compose `FilePriceProvider` và bắt
`InvalidPriceMasterError`); (c) `FilePriceProvider` được truyền vào
`price_provider` của `run_import()` ở bất kỳ đường chạy nào không phải test.
Kiểm tra máy đọc được: `grep -rn "FilePriceProvider" app/ tools/ config/`
trả về hit ngoài `app/modules/pricing/file_price_provider.py` → re-trigger.
Khi re-trigger, finding này phải được **nâng lên BLOCKING** và sửa trước khi
kích hoạt.

Hướng sửa gợi ý (không bắt buộc, không phải scope review): đưa `price < 0`
vào trong khối `try`, hoặc chèn kiểm tra `price.is_finite()` trước nó và
raise `InvalidPriceMasterError` với `reason` riêng.

---

**`HB-105B-08` — `Infinity` được chấp nhận làm `purchase_price` hợp lệ.**

Mô tả: `"Infinity"`, `"inf"`, `float('inf')`, `Decimal('Infinity')` và YAML
`.inf` đều vượt qua toàn bộ validation và được `lookup()` trả về. Số học
downstream cho `-Infinity`. Cùng lỗ hổng cho magnitude vô lý (`1E+1000` được
chấp nhận). `-Infinity` tình cờ bị chặn bởi luật `negative_price`, nên lỗ
hổng chỉ hở một phía.

Vì sao HARDENING: không production path hiện tại (bảng trên); `DEC-145` §5
không liệt kê luật cho giá trị không hữu hạn, nên đây là khoảng trống của tập
luật đã freeze chứ không phải luật đã freeze bị vi phạm (`V4.1` §7).

Vì sao nghiêm trọng hơn `HB-105B-07` nếu path mở: đây là con đường duy nhất
trong toàn bộ review mà một giá **vô nghĩa** chảy tiếp mà **không** có tín
hiệu nào — đúng dạng failure path `Price sai → KpiPurchasePrice sai →
EligibleKpiProfit sai → CR sai → KPI/lương sai` đã ghi ở
`PROJECT/REVIEW_BUDGET_LEDGER.md`.

**RE-TRIGGER CONDITION:** giống hệt `HB-105B-07` (a)/(b)/(c) và cùng lệnh
grep. Nếu re-trigger, `HB-105B-08` phải được xử lý **trước**
`HB-105B-07` (nó im lặng, cái kia thì ồn ào).

---

**`HB-105B-09` — YAML sai hình dạng thoát ra `TypeError`/`AttributeError` thô.**

Mô tả: `from_yaml()` gọi `data.get("prices", [])` rồi `list(rows)` mà không
kiểm hình dạng. `prices:` để trống (null) → `TypeError: 'NoneType' object is
not iterable`; root là list → `AttributeError: 'list' object has no attribute
'get'`; một phần tử không phải dict → `AttributeError: 'str' object has no
attribute 'get'`. Cùng loại sai lệch với `HB-105B-07`: một file hỏng phải
hiện ra là `InvalidPriceMasterError` có `.reason`, không phải exception thô.

**RE-TRIGGER CONDITION:** khi `from_yaml()` (hoặc constructor nhận rows) lần
đầu được gọi trên một file **không do test sinh ra** — tức cùng điều kiện
(a)/(b)/(c) của `HB-105B-07`; hoặc sớm hơn, khi `TASK-105C` viết export tool
sinh file snapshot, vì lúc đó một bug trong export tool sẽ hiện ra qua đúng
cửa này.

---

**`HB-105B-10` — dung sai schema im lặng: cột thiếu/gõ sai không bị phát hiện.**

Mô tả: `_parse_one_row()` đọc bằng `row.get(...)`. Hệ quả đo được:
- một row **hoàn toàn thiếu** khoá `effective_to` trở thành **open record im
  lặng** (còn hiệu lực tới `9999-12-31`) thay vì bị từ chối. `DEC-145` §1 nói
  `effective_to` là REQUIRED cho mọi record đã kết thúc hiệu lực và chỉ được
  rỗng ở đúng một record hiện hành — một cột gõ sai tên (`effective_too`) biến
  một record lịch sử thành record vĩnh viễn;
- mọi cột lạ bị bỏ im lặng (đo bằng harness E8/`capture_id`).

Vì sao HARDENING: không production path hiện tại; và trong phạm vi
`TASK-105B`, dữ liệu vào là do người viết tay theo schema đã biết.

**RE-TRIGGER CONDITION:** khi `TASK-105C` bắt đầu sinh file snapshot bằng máy
(`tools/pricing/` export tool) — lúc đó nguồn row không còn là người viết
tay mà là code, và một cột đặt sai tên trong export sẽ im lặng làm sai toàn bộ
lịch sử giá. Kiểm tra máy đọc được: sự tồn tại của bất kỳ file nào dưới
`tools/pricing/` → re-trigger.

---

**`HB-105B-11` — assertion của `CHECK-105B-17` hẹp hơn lời văn của chính gate.**

Mô tả: gate viết *"Module mới/test mới không import hay nhắc client
Firebase/RTDB"*, nhưng `test_module_does_not_import_or_mention_firebase_client`
chỉ đọc `_MODULE_PATH` — không assert gì trên `tests/test_file_price_provider.py`.
Reviewer đã **tự kiểm phần test file bằng tay** (grep + AST) và xác nhận nội
dung check đạt, nên `CHECK-105B-17` được chấm PASS; nhưng nếu ai đó thêm một
import Firebase vào test file sau này, gate sẽ không kêu.

Cùng loại với `HB-105B-07`…`10` về mức độ: không production path, không ảnh
hưởng correctness hôm nay.

**RE-TRIGGER CONDITION:** khi `TASK-105C` thêm test suite mới
(tests/test_historical_vendor_price_provider.py — file chưa tồn tại, theo Scope Lock của nó) —
lúc đó phạm vi "test mới" mở rộng thật sự và assertion cần phủ cả thư mục
test liên quan, không chỉ một file module.

### OUT_OF_SCOPE

1. **`PriceRecord` không mang được cột provenance riêng của `TASK-105C`.**
   Snapshot của `TASK-105C` (mục 10 của
   `docs/tasks/TASK-105C-historical-vendor-price-provider.md`) có thêm
   `contributing_ncc`, `captured_at`, `capture_id`; `PriceRecord` là frozen
   dataclass 6 trường và bỏ im lặng các cột đó. Reviewer phân loại đây là
   **OUT_OF_SCOPE của `TASK-105B`**, không phải HARDENING: `TASK-105B` Scope
   Lock nói rõ task này "chỉ tạo seam", và `TASK-105C` tuyên bố sẽ **compose**
   `FilePriceProvider` rồi "bọc thêm business logic riêng" — mang provenance
   bổ sung chính là phần bọc đó. Seam đã freeze (`__init__(rows)`,
   `from_yaml`, `find_record`, `lookup`, `records`, `InvalidPriceMasterError`,
   `PriceRecord`) khớp **đúng từng dòng** với khối seam trong
   `docs/tasks/TASK-105B-file-price-provider.md`.
   *(Ghi chú: khía cạnh "cột lạ bị bỏ im lặng" — tức rủi ro export tool gõ sai
   tên cột — đã được tách ra và ghi thành `HB-105B-10`, vì đó là hành vi
   parsing của chính `TASK-105B`.)*
2. `TASK-105B-Q3` (chính sách zero-price dòng phụ, `DEC-145` §3) — BLOCKED bởi
   `TASK-103`, đã ghi trong Scope Lock.
3. Bảng giá production thật — data dependency đang mở, không phải code blocker.
4. `TASK-402` product_mapper / product identity mapping — Phase 4.
5. `lookup()` với `datetime` thay vì `date` phát `TypeError` thô — **không** ghi
   thành finding: Protocol khai báo `Optional[date]`, và `WorkingLine.date` là
   `Optional[date]`, nên đây là ngoài contract, không phải khiếm khuyết.
6. 3 lỗi reference-integrity tiền tồn của `TASK-REM-T06` — không thuộc
   `TASK-105B`.

## Đối Chiếu Với Artifact Review Song Song

Chỉ đọc **sau khi** các finding trên đã hình thành từ evidence riêng.
Bảng này để Owner dedupe, **không** phải nguồn evidence của phiên này:

| Finding phiên này | Có vẻ trùng với (nhánh `claude/file-price-provider-review-negpxw`) |
|---|---|
| `HB-105B-09` (YAML shape) | `HB-105B-03` |
| `HB-105B-10` (schema im lặng) | `HB-105B-05` (phần `effective_to`) |
| `HB-105B-11` (`CHECK-105B-17` hẹp) | `HB-105B-06` |
| OUT_OF_SCOPE #1 (provenance 105C) | `HB-105B-04` — **phiên này phân loại khác** (OUT_OF_SCOPE thay vì HARDENING), lý do nêu ở trên |
| `HB-105B-07` (NaN), `HB-105B-08` (Infinity) | không thấy ID tương ứng trong artifact kia |

Reviewer **giữ nguyên** ID mới của mình để không overwrite namespace đã tồn
tại; việc hợp nhất hai artifact là quyết định của Owner.

## Sai Lệch So Với Tuyên Bố Của Người Triển Khai (Mismatches With Implementer Claims)

**Về số liệu test: KHÔNG CÓ sai lệch nào.** Cả bốn con số (targeted 33,
Golden 58+2, full 730+11, base 697+11) reviewer đo lại đều trùng khớp chính
xác. Cả 17 dòng evidence trong bảng gate của phiên implementation đều
tái hiện được.

**Về độ phủ:** phiên implementation không phát hiện `NaN`/`Infinity`
(`HB-105B-07`/`HB-105B-08`) và bốn finding còn lại. Đây là khoảng trống
discovery, **không phải** tuyên bố sai — không dòng nào trong
`docs/tasks/TASK-105B-file-price-provider.md` khẳng định đã kiểm giá trị
không hữu hạn.

**Về hình thức:** phiên implementation ghi `CHECK-105B-12` ở mức `E2` với lý
do "đã thực thi trong phiên". Theo `governance/core/EVIDENCE_STANDARD.md`,
E2 đòi hỏi xác minh **độc lập với người triển khai** — một lần chạy của
chính người triển khai là E1, không phải E2. Sai lệch này **đã được đóng bởi
chính artifact này**: reviewer chạy lại Golden độc lập, nên `CHECK-105B-12`
nay có E2 thật. Ghi lại để bản ghi trung thực, không phải để mở finding.

## Kiểm Tra Mặc Định An Toàn (Default Safety)

```
$ grep -n "PriceProvider" app/pipeline.py
41: from app.modules.pricing.price_engine import apply_prices
42: from app.modules.pricing.provider import PendingPriceProvider, PriceProvider
86:     price_provider: PriceProvider | None = None,
103:    apply_prices(lines, price_provider or PendingPriceProvider())

$ grep -rn "FilePriceProvider" . --include=*.py --include=*.yaml --include=*.toml \
      | grep -v app/modules/pricing/file_price_provider.py \
      | grep -v tests/test_file_price_provider.py
(0 hit)

$ ls config/prices.yaml
ls: cannot access 'config/prices.yaml': No such file or directory
```

- `PendingPriceProvider` **vẫn là default** (`app/pipeline.py:103`) — Status: PASS.
- `FilePriceProvider` **chưa được activate** trong production path; không tồn
  tại caller nào — Status: PASS.
- Golden **không** dùng provider mới; `tests/fixtures/` và
  `tests/test_golden_baseline.py` diff = 0 — Status: PASS.

## Review Budget Accounting (V4.1 §2/§3)

Đọc canonical ledger `PROJECT/REVIEW_BUDGET_LEDGER.md`, mục "Root Task:
TASK-105B" (không suy diễn từ chat, không giả định review trước đã tiêu
budget):

```
TRƯỚC review này:
    root_task: TASK-105B
    effective_risk: HIGH
    repair_cycles_allowed: 2
    repair_cycles_used: 0
    repair_cycles_remaining: 2

SAU review này (verdict PASS):
    repair_cycles_allowed: 2
    repair_cycles_used: 0
    repair_cycles_remaining: 2      ← KHÔNG ĐỔI
```

Căn cứ: `V4.1` §3 tính cycle theo **LẦN SỬA**, không theo số review. Verdict
của phiên này là PASS, **không** mở remediation cycle, **không** phát sinh
repair diff ⇒ không có `base_sha`/`head_sha` nào để ghi, `repair_cycles_used`
giữ nguyên `0`. Đây đúng semantics canonical mà chính ledger đã ghi sẵn:
*"cycle chỉ mở nếu một vòng Independent Review sau đó cho verdict FAIL và cần
repair."* Reviewer **không** tự phát minh cách tính khác.

Vì trạng thái ngân sách không đổi, phiên review này **không** sửa
`PROJECT/REVIEW_BUDGET_LEDGER.md` — `V4.1` không yêu cầu ghi ledger khi 0
cycle bị tiêu. Ngoài ra `V4.1` §12 (State Authority Matrix) cấm reviewer
read-only ghi `FROZEN` vào repo; reviewer chỉ được ghi
`PASS — ELIGIBLE_FOR_FREEZE`, và ghi nó trong chính artifact này.

## Reference Integrity

Baseline đo tại `c22cef8` **trước** khi commit artifact:

```
REFERENCE INTEGRITY: FAIL
Quét 133 file .md (loại trừ 10 file trong governance/reference/history/, docs/audit/).
3 reference không phân giải được:
- docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> /README.md
- docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> CODE_OF_CONDUCT.md
- docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> CONTRIBUTING.md
```

Đúng 3 lỗi tiền tồn `TASK-REM-T06` đã biết. Kết quả sau commit ghi ở mục
"Xác Minh Sau Commit". Reviewer **không** sửa validator để làm review PASS.

Artifact này được đặt trên lineage **chứa** implementation SHA (review branch
tạo từ `c22cef8`), nên mọi reference tới
`app/modules/pricing/file_price_provider.py` và
`tests/test_file_price_provider.py` đều resolvable — không đặt trên base tree
để tránh dangling reference.

Ba validator còn lại, chạy tại `c22cef8`:

```
GOVERNANCE STRUCTURE: PASS   (21 required path)
PROJECT STATE: PASS
EVIDENCE VALIDATION: PASS    (88 REQUIRED PASS evidence record)
TASK COMPLETION: PASS        (6 DONE task)
```

## Kết Luận (Conclusion)

```
E2 PASS
VERDICT: PASS — ELIGIBLE_FOR_FREEZE
```

Căn cứ đầy đủ:
- **0 BLOCKING finding** — không finding nào chỉ ra được production path hiện
  tại theo `V4.1` §5;
- **17/17 REQUIRED gate PASS**, mỗi check có evidence độc lập riêng ở mức E2;
- **regression đạt**: `730 passed, 11 skipped` so với base `697 passed, 11
  skipped`, chênh lệch đúng bằng 33 test mới, 0 fail, 0 skip mới;
- **Golden không regression**: `58 passed, 2 skipped`, fixture và
  `tests/test_golden_baseline.py` diff = 0, `app/pipeline.py` và
  `app/modules/domain/models.py` diff = 0 nên digest bất biến;
- **default safety giữ nguyên**: `PendingPriceProvider` vẫn mặc định,
  `FilePriceProvider` không có caller nào;
- review evidence được **commit + push + đọc lại được từ remote SHA** (mục
  dưới).

## Việc Cần Theo Dõi Tiếp (Required Follow-up)

1. **5 HARDENING** `HB-105B-07`…`HB-105B-11`, mỗi cái có RE-TRIGGER CONDITION
   riêng ở trên. `HB-105B-07` và `HB-105B-08` phải được **nâng lên BLOCKING và
   sửa trước** khi `FilePriceProvider` được nối vào bất kỳ đường chạy
   production nào — đây là điều kiện đi kèm verdict PASS này, không phải gợi ý.
2. **CONFLICT DETECTED** ở mục "Bối Cảnh Re-run" — Owner phải chọn artifact
   canonical giữa nhánh này và `claude/file-price-provider-review-negpxw`, và
   dedupe namespace `HB-105B-*`. Reviewer không tự xử lý.
3. `HB-105B-01`/`HB-105B-02` (đã tồn tại từ `DEC-144`/§34) **được giữ nguyên**,
   không bị reuse hay overwrite bởi phiên này.
4. Bảng giá production thật vẫn là data dependency đang mở — Exit Criteria
   tương ứng trong `docs/tasks/TASK-105B-file-price-provider.md` vẫn chưa đạt.
5. Bước kế tiếp được phép: **TASK-105B FREEZE** bởi một Freeze Finalization
   session có thẩm quyền (`V4.1` §12). Phiên review này **không** Freeze,
   **không** merge, **không** mở remediation, **không** bắt đầu `TASK-105C`.

## Xác Minh Sau Commit (Post-Commit Verification)

Artifact được commit lần đầu tại `fc2f76cab74b24c45add47eda9382a33a029dec3`
trên nhánh `review/task-105b-independent-review-1` (cha = đúng implementation
SHA `c22cef8`), rồi push. Xác minh thực thi ngay sau push:

```
$ git diff --check ; git diff --cached --check
(không output, exit 0)

$ git fetch origin review/task-105b-independent-review-1
$ git rev-parse review/task-105b-independent-review-1
fc2f76cab74b24c45add47eda9382a33a029dec3
$ git rev-parse origin/review/task-105b-independent-review-1
fc2f76cab74b24c45add47eda9382a33a029dec3
MATCH: local review SHA == remote review SHA

$ git show fc2f76ca...:docs/reviews/TASK-105B-INDEPENDENT-REVIEW-1.md
exit=0   bytes=40549   lines=656
(đọc lại được nguyên vẹn từ commit remote; byte-identical với working tree)

$ git rev-parse origin/claude/price-provider-foundation-ahix1t
c22cef8b47ac4cd71ef49609066a362c9e604313
(implementation branch KHÔNG bị mutate — local và remote đều đứng nguyên)

$ git diff --name-status c22cef8 origin/review/task-105b-independent-review-1
A  docs/reviews/TASK-105B-INDEPENDENT-REVIEW-1.md

$ git diff --name-only c22cef8 origin/review/task-105b-independent-review-1 -- app tests config
(rỗng — app/**, tests/**, config/** KHÔNG bị chạm)

$ git status --short
(rỗng — worktree CLEAN)
```

Validator sau khi stage artifact:

```
GOVERNANCE STRUCTURE: PASS      (21 required path)
PROJECT STATE: PASS
EVIDENCE VALIDATION: PASS       (88 REQUIRED PASS evidence record)
TASK COMPLETION: PASS           (6 DONE task)
REFERENCE INTEGRITY: FAIL — Quét 134 file .md, 3 reference không phân giải:
  - docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> /README.md
  - docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> CODE_OF_CONDUCT.md
  - docs/tasks/TASK-REM-T06-repository-root-hygiene.md -> CONTRIBUTING.md
```

Phân biệt rõ: **đúng 3 lỗi tiền tồn `TASK-REM-T06`**, y hệt baseline đo tại
`c22cef8` trước khi commit (133 file → 134 file, cùng 3 lỗi, không lỗi mới).
**0 regression mới.** Validator **không** bị sửa để làm review PASS.

`REVIEW_EVIDENCE = VALID` — artifact đọc lại được từ committed remote SHA,
nên verdict dưới đây đủ điều kiện dùng cho Freeze.

Commit này (commit thứ hai trên nhánh review) chỉ điền chính mục "Xác Minh
Sau Commit" ở trên vào artifact; nó **không** đổi bất kỳ evidence, finding,
gate result hay verdict nào. Cùng bộ xác minh (`local == remote`,
`git show <sha>:<artifact>` đọc được, implementation branch nguyên vẹn,
`app/**`/`tests/**`/`config/**` không bị chạm) được chạy lại cho commit cuối
cùng; SHA review cuối cùng nằm trong final report của phiên.
