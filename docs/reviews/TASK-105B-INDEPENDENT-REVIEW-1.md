# RÀ SOÁT ĐỘC LẬP E2 (E2 INDEPENDENT REVIEW) — TASK-105B #1

Review ID:
`105B-IR-01` — Independent Review #1 của `TASK-105B` (`FilePriceProvider`).

Task / Release:
`TASK-105B` — `FilePriceProvider` (`docs/tasks/TASK-105B-file-price-provider.md`)

Reviewer Session:
Phiên "TASK-105B — INDEPENDENT REVIEW #1", nhánh
`claude/file-price-provider-review-negpxw`. Review chạy **trong** canonical
repository, trên một `git worktree` detached tại đúng target SHA — khác với
`docs/reviews/TASK-GOLDEN-BASELINE-001-INDEPENDENT-REVIEW-2.md` vốn chỉ là
bản ghi provenance của một review chạy ngoài repo.

Executed By:
Independent Reviewer session (không phải phiên implementation)

Timestamp:
2026-08-28

## Scope

Review target (exact SHA, không review "latest branch"):

```
Implementation branch : claude/price-provider-foundation-ahix1t
Target SHA            : c22cef8b47ac4cd71ef49609066a362c9e604313
Base SHA              : c49cb67ede3f7ff4af2a49cdc338b4a31c33021c
```

Xác minh trước khi review:

```
$ git rev-parse origin/claude/price-provider-foundation-ahix1t
c22cef8b47ac4cd71ef49609066a362c9e604313        # == target, branch chưa đổi

$ git -C <worktree> rev-parse HEAD
c22cef8b47ac4cd71ef49609066a362c9e604313        # == target, ĐẠT

$ git rev-parse origin/claude/extract-upload-repo-gq2ws4
c49cb67ede3f7ff4af2a49cdc338b4a31c33021c        # == base, nhánh mặc định
```

Base SHA trùng đúng tip của nhánh mặc định trên origin ⇒ diff review là
diff thật so với trạng thái canonical, không có drift trung gian.

## Tài Liệu Đầu Vào Đã Đọc (Inputs Read)

- `CLAUDE.md` (canonical governance entry point), `governance/core/V4_1_POLICY_FREEZE.md`.
- `PROJECT/PROJECT_PROGRESS.md`, `PROJECT/PROJECT_DECISIONS.md`
  (`DEC-103`, `DEC-121`, `DEC-145`/`OD-105B-01`, `DEC-146` → `DEC-152`),
  `PROJECT/REVIEW_BUDGET_LEDGER.md`.
- `docs/tasks/TASK-105B-file-price-provider.md` (canonical artifact + Completion Gate).
- `docs/tasks/TASK-105C-historical-vendor-price-provider.md` — **chỉ** để kiểm
  tra downstream seam, không implement.
- Diff `c49cb67..c22cef8` (7 file, +1358/−20).
- Production code không đổi nhưng đã đọc để xác minh: `app/pipeline.py`,
  `app/modules/pricing/provider.py`, `price_engine.py`,
  `app/modules/domain/money.py`, `app/modules/config/loader.py`,
  `app/modules/validation/text.py`, `app/modules/domain/models.py`.

## Diff Đã Review

```
PROJECT/LO_TRINH_DE_HIEU.md                                   |   3 +-
PROJECT/PROJECT_PROGRESS.md                                   |  71 +++-
PROJECT/REVIEW_BUDGET_LEDGER.md                               |  52 ++-
app/modules/pricing/file_price_provider.py                    | 298 +++++  (MỚI)
docs/sessions/...task-105b-file-price-provider-implementation.md | 215 +++++  (MỚI)
docs/tasks/TASK-105B-file-price-provider.md                   | 365 +++++  (MỚI)
tests/test_file_price_provider.py                             | 374 +++++  (MỚI)
```

Production diff = đúng **một** file mới (`file_price_provider.py`). Không
có file production cũ nào bị sửa. `git diff --check` = sạch (exit 0).

## Xác Minh Độc Lập (Independent Verification)

Toàn bộ evidence dưới đây do phiên review **tự chạy lại**, không copy từ
artifact implementation. Môi trường: `python3.11`, venv riêng
(`pytest 9.1.1`, `PyYAML`, `openpyxl`), worktree detached tại target SHA.

### Bảng Completion Gate CHECK-105B-01…17

| Check ID | Status | Evidence Level | Evidence | Executed By | Timestamp |
|---|---|---|---|---|---|
| CHECK-105B-01 | PASS | E2 | Test PASS + probe độc lập A3/A5: `[2026-01-01,2026-01-31]` tra được cả hai biên; khoảng một ngày `from==to` tra đúng, hai ngày kề = `None`; open record tra tới `9999-12-31` | Reviewer | 2026-08-28 |
| CHECK-105B-02 | PASS | E2 | Test PASS + probe A1/A2/C1/B1: overlap thường, **overlap chạm biên cùng ngày**, nested overlap, open-rồi-closed — tất cả raise `InvalidPriceMasterError`; không có nhánh code nào tự chọn một record | Reviewer | 2026-08-28 |
| CHECK-105B-03 | PASS | E2 | Test PASS + probe B4 → `reason='multiple_open_records'`; đọc `_reject_multiple_open_records()` xác nhận đếm theo từng normalized key | Reviewer | 2026-08-28 |
| CHECK-105B-04 | PASS | E2 | Test PASS + probe: ngày ngay sau khoảng trước và ngay trước khoảng sau đều `None`; không có fallback `latest`/`nearest`/`current` trong `find_record()` (đọc dòng 100–111) | Reviewer | 2026-08-28 |
| CHECK-105B-05 | PASS | E2 | Test PASS + probe B5: `2025-12-31` với record mở từ `2026-01-01` → `None` | Reviewer | 2026-08-28 |
| CHECK-105B-06 | PASS | E2 | 3 case tham số hoá PASS + probe D1/D3: NFD↔NFC khớp nhau; TAB/NBSP/U+3000/newline/space-lặp đều gộp về cùng key; `Cay` không khớp `Cây` (không bỏ dấu) | Reviewer | 2026-08-28 |
| CHECK-105B-07 | PASS | E2 | Test PASS + probe D2/D8/D9: NFC-vs-NFD, `straße`/`STRASSE`, `K`(U+212A)/`K` — mọi va chạm casefold có giá mâu thuẫn đều raise `conflicting_price_same_period` | Reviewer | 2026-08-28 |
| CHECK-105B-08 | PASS | E2 | Test PASS + probe: `find_record()` trả `PriceRecord` mang đủ `raw_product_key` / `normalized_product_key` / matched record; `.records` là `tuple` (immutable); `find_record()` ổn định qua nhiều lần gọi | Reviewer | 2026-08-28 |
| CHECK-105B-09 | PASS | E2 | 8 case + `test_exact_duplicate_row_rejected` PASS; probe bổ sung xác nhận `reason` đúng cho `list`/`dict`/`date`/`bool`/`"5,000,000"`/`2026-02-30`/ISO-có-giờ | Reviewer | 2026-08-28 |
| CHECK-105B-10 | PASS | E2 | 3 test PASS; probe: `0` khai báo thật → `Decimal('0')`; `None` → `missing_price`; `"   "` → `missing_price`; ô trống **không** bị ép về 0 | Reviewer | 2026-08-28 |
| CHECK-105B-11 | PASS | E1 | `grep -c "float(" app/modules/pricing/file_price_provider.py` → `0`; probe xác nhận `int`/`float`/`str` đầu vào đều ra `Decimal` qua `to_decimal()` (đường `str(value)`, ADR-103) | Reviewer | 2026-08-28 |
| CHECK-105B-12 | PASS | E2 | `python -m pytest tests/test_golden_baseline.py -q` → **`58 passed, 2 skipped`**; `git diff` trên `app/pipeline.py`/`price_engine.py`/`provider.py`/`models.py` và `tests/fixtures/`, `config/` = **rỗng** ⇒ `lines_digest`/`_covered_digest_fields` không thể đổi | Reviewer | 2026-08-28 |
| CHECK-105B-13 | PASS | E2 | `pytest -q` @ target → **`730 passed, 11 skipped`**; `pytest -q` @ base `c49cb67` (worktree thứ hai) → **`697 passed, 11 skipped`**. Chênh lệch = đúng 33 test mới, **0 regression, 0 skip mới** | Reviewer | 2026-08-28 |
| CHECK-105B-14 | PASS | E2 | `git diff --quiet c49cb67 c22cef8 -- app/pipeline.py app/modules/pricing/price_engine.py app/modules/pricing/provider.py app/modules/domain/models.py` → exit `0`; `--stat` rỗng | Reviewer | 2026-08-28 |
| CHECK-105B-15 | PASS | E1 | Test AST PASS; grep độc lập 5 keyword Q3 trong module → `0/0/0/0/0` hit; module không import `app.modules.validation.rules` | Reviewer | 2026-08-28 |
| CHECK-105B-16 | PASS | E2 | `TARGET_SHA=c22cef8… bash scripts/branch_authority_check.sh` → `AUTHORITY : DETACHED_EXACT_TARGET`, `RESULT : AUTHORITY_OK`, `WORKTREE : CLEAN` | Reviewer | 2026-08-28 |
| CHECK-105B-17 | PASS | E1 | Test PASS; grep độc lập trên **cả** module lẫn test file: không có import Firebase/RTDB nào (4 hit trong test file là chính danh sách marker của check và comment, không phải import) | Reviewer | 2026-08-28 |

**17/17 REQUIRED PASS — độc lập.** Không có check nào FAIL hoặc BLOCKED.

### Validators

```
validate_structure           PASS  — 21 required path
validate_project_state       PASS
validate_evidence            PASS  — 88 REQUIRED PASS evidence record
validate_task_completion     PASS  — 6 DONE task
validate_reference_integrity FAIL  — đúng 3 lỗi tiền tồn TASK-REM-T06
                                     (/README.md, CODE_OF_CONDUCT.md,
                                     CONTRIBUTING.md)
```

Ba lỗi `reference_integrity` được xác minh là **tiền tồn**: chạy lại đúng
validator đó tại base SHA `c49cb67` cho ra **đúng ba lỗi giống hệt**. Không
có lỗi mới nào do `TASK-105B` sinh ra.

## Adversarial Testing (ngoài 33 test hiện có)

Phiên review viết một harness ad-hoc (~70 case, chạy ngoài repo, **không**
commit vào `tests/`) nhắm đúng các hướng phá mà brief yêu cầu:

| Nhóm | Case | Kết quả |
|---|---|---|
| Biên khoảng đóng | A kết thúc ngày D, B bắt đầu ngày D (cùng giá / khác giá) | **REJECT** đúng — `overlapping_periods` / `conflicting_price_same_period`. **Không có off-by-one**: `a.from <= b_end and b.from <= a_end` trên khoảng đóng là đúng ngữ nghĩa |
| Biên khoảng đóng | Adjacency hợp lệ (kết thúc 01-31, bắt đầu 02-01) | Nạp OK, cả hai biên tra đúng giá riêng |
| Biên khoảng đóng | Khoảng một ngày `from == to` | Nạp OK; ngày kề hai bên = `None` |
| Open record | Open rồi closed sau đó / closed kết thúc đúng ngày open bắt đầu / hai open | REJECT cả ba đúng lý do |
| Open record | Closed trước, open sau (hợp lệ) | Nạp OK; tra `9999-12-31` = giá; trước `effective_from` = `None` |
| Thứ tự nguồn | 6 hoán vị của 3 record + 200 lần xáo trộn ngẫu nhiên bảng 12 record | **1 chữ ký kết quả duy nhất** — deterministic tuyệt đối. Overlap bị cấm ở load nên tối đa 1 record khớp, thứ tự không ảnh hưởng |
| Unicode | NFD trong file ↔ NFC khi tra (và ngược lại) | Khớp đúng cả hai chiều |
| Unicode | TAB / NBSP (U+00A0) / ideographic space (U+3000) / newline / space lặp / space bao ngoài | Gộp đúng về một key |
| Unicode | Key chỉ gồm NBSP | REJECT `empty_key` đúng |
| Unicode | Va chạm casefold `straße`/`STRASSE`, `K`(U+212A)/`K`, `ǅ`/`ǆ`, `İ` | Cùng normalized key; giá mâu thuẫn → REJECT. Đúng `DEC-145` §2 (engine không tự chọn) |
| Duplicate | Trùng hoàn toàn / khác `source` / khác cách viết raw | REJECT cả ba (`exact_duplicate_row` hoặc `overlapping_periods`) |
| Giá malformed | `bool`, `list`, `dict`, `date`, `"5,000,000"` | REJECT `invalid_price` đúng |
| Giá malformed | `NaN` / `.nan` / `sNaN` | **Thoát ra `decimal.InvalidOperation` thô** — xem `HB-105B-01` |
| Giá malformed | `Infinity` / `.inf` | **Nạp OK, `lookup()` trả `Decimal('Infinity')`** — xem `HB-105B-02` |
| Shape | `prices:` null trong YAML / `prices` là dict | Thoát ra `TypeError`/`AttributeError` thô — xem `HB-105B-03` |
| Quy mô | 48.000 dòng / 2.000 key; 3.000 record trên **một** key | Load `0.31s` / `0.35s`; 10.000 lookup `0.026s`. `_reject_overlaps` là O(n²) theo nhóm key nhưng không thành vấn đề ở quy mô thực tế |
| Seam 105C | Snapshot CSV 4 cột + cột provenance thừa, `effective_to` rỗng | Compose qua `FilePriceProvider(csv.DictReader(...))` chạy đúng; ô rỗng → open record đúng |

Không tìm được case nào khiến provider **âm thầm trả sai giá** hoặc **âm
thầm trả `None` cho một bảng giá malformed**. Mọi input hỏng đều dừng ở
load, ồn ào — chỉ khác nhau ở *loại* exception (xem HARDENING).

## Sai Lệch So Với Tuyên Bố Của Người Triển Khai (Mismatches With Implementer Claims)

**Không có.** Cả ba con số evidence được tái lập chính xác:

```
                        Implementation claim      Reviewer actual
targeted                33 passed                 33 passed          KHỚP
Golden                  58 passed, 2 skipped      58 passed, 2 skipped   KHỚP
full regression         730 passed, 11 skipped    730 passed, 11 skipped KHỚP
baseline (base SHA)     697 passed, 11 skipped    697 passed, 11 skipped KHỚP
4 file production diff  0                         0 (exit 0)         KHỚP
branch authority        AUTHORITY_OK              AUTHORITY_OK       KHỚP
validators              4 PASS + 3 lỗi tiền tồn   4 PASS + 3 lỗi tiền tồn KHỚP
```

## Default-Provider Safety

Xác minh **bằng code**, không dựa vào Implementation Report:

- `app/pipeline.py:103` — `apply_prices(lines, price_provider or PendingPriceProvider())`.
  Mặc định vẫn là `PendingPriceProvider`; `app/pipeline.py` diff = 0.
- `grep -rn "FilePriceProvider\|file_price_provider"` trên toàn repo, loại
  trừ `docs/`, chỉ ra **hai** file: chính module đó và
  `tests/test_file_price_provider.py`. **Không** có tham chiếu nào trong
  `app/pipeline.py`, `price_engine.py`, `provider.py`, `config/**`, hay
  bất kỳ test Golden nào.
- `config/` diff = 0 — không có `prices.yaml` nào được thêm, nên không tồn
  tại đường config nào có thể vô tình kích hoạt provider mới.

⇒ Provider mới **không** tự activate ở pipeline, app startup, Golden path,
hay config mặc định. Đúng yêu cầu "Preserve Pending Default".

## Contract Correctness

| Yêu cầu (brief §3) | Kết quả |
|---|---|
| `lookup(product_code, sale_date) -> Optional[Decimal]` | ĐÚNG — khớp `PriceProvider` Protocol không đổi |
| exact match / normalization | ĐÚNG — `fold()` tái dùng nguyên vẹn, không có matcher riêng |
| effective-date, khoảng đóng `[from,to]` | ĐÚNG — `from <= sale_date <= (to or 9999-12-31)` |
| open-ended record | ĐÚNG — `None` → `_FAR_FUTURE` = `date.max` |
| gap → `None`; no match → `None` | ĐÚNG |
| no current/latest/nearest fallback | ĐÚNG — không tồn tại nhánh code nào chọn record ngoài khoảng |
| deterministic | ĐÚNG — 200 hoán vị, 1 kết quả |
| Decimal semantics | ĐÚNG — 0 hit `float(`; `to_decimal()` đi qua `str()` |
| provenance availability | ĐÚNG — `PriceRecord` + `find_record()` + `.records` |
| malformed source ≠ determined absence | ĐÚNG về **hành vi** (luôn raise ở load, không bao giờ hoá `None`); xem `HB-105B-01`/`03` về **loại** exception |

## TASK-105C Composition Seam

Đánh giá (không implement 105C):

- **Không cần sửa lại semantics** — `DEC-152` §11 yêu cầu 105C *compose*
  `FilePriceProvider`; seam `__init__(rows: Iterable[dict])` là đúng thứ
  cần, vì snapshot của 105C là **CSV** chứ không phải YAML. Reviewer đã
  chạy thử một snapshot CSV đúng contract mục 10 của 105C qua
  `csv.DictReader` → nạp và tra đúng, ô `effective_to` rỗng thành open
  record đúng.
- **Không bypass validation** — validation chạy eager trong `__init__`, nên
  mọi đường vào (`from_yaml` hay rows) đều bị validate.
- **Không duplicate normalization** — `fold()` áp cho cả record lẫn lookup.
- **Không cần current-price fallback** — không tồn tại.
- **Pending semantics giữ nguyên** — `None` cho gap/missing, đúng
  "Missing → Pending, KHÔNG phải lỗi" ở Error Semantics mục 11 của 105C.
- **`InvalidPriceMasterError` tái dùng được** — export sẵn, mang `.reason`.

⇒ Seam ĐỦ. Không cần refactor foundation trước 105C. Một điểm ma sát đã
ghi lại tại `HB-105B-04` (cột provenance thừa của 105C bị `PriceRecord` bỏ
qua) — giải được hoàn toàn trong phạm vi 105C bằng side-map khoá
`(normalized_product_key, effective_from)`, khoá này là duy nhất vì overlap
bị cấm; **không** buộc phải sửa `FilePriceProvider`.

## Findings

Phân loại theo `governance/core/V4_1_POLICY_FREEZE.md` §5 (Production Path
Decision Rule) và §7 (Review Finding Action Gate).

### BLOCKING

**KHÔNG CÓ.**

Ghi rõ cơ sở, vì đây là kết luận quan trọng nhất của review: hai defect
thật (`HB-105B-01`, `HB-105B-02`) đều **không** dựng được từ bất kỳ nguồn
nào trong bốn nguồn của §5 —

1. *production annotation/schema inventory* — không có inventory nào khai
   một giá `NaN`/`Infinity`;
2. *config hiện hành trong repo* — `config/` **không có** bảng giá nào;
   diff `config/` = 0 và bảng giá production thật chưa được chủ dự án cấp
   (data dependency đang mở, đã ghi trong artifact);
3. *Golden Baseline fixture đã tồn tại* — không fixture Golden nào chạm
   `FilePriceProvider`;
4. *raw production data đã được xác minh* — chưa tồn tại.

§5 chốt: "Không dựng được từ 1–4 → **HARDENING BY DEFAULT**". Cộng thêm §7:
BLOCKING đòi "production path hiện tại", mà provider này không nằm trên
đường chạy production nào (đã xác minh bằng code ở mục Default-Provider
Safety). Reviewer **không** nâng bậc, đúng chỉ dẫn brief §6/§12.

### HARDENING

**`HB-105B-01` — `NaN` thoát ra `decimal.InvalidOperation` thay vì `InvalidPriceMasterError`.**

- File/hàm/dòng: `app/modules/pricing/file_price_provider.py`, `_parse_price()`,
  **dòng 226** (`if price < 0:`).
- Nguyên nhân: `try/except` chỉ bọc `to_decimal(value)` (dòng 213–219). Phép
  so sánh `price < 0` nằm **ngoài** khối đó, và `Decimal('NaN') < 0` raise
  `decimal.InvalidOperation` (đã xác minh: `Decimal('NaN') < 0` → raise;
  `Decimal('sNaN') < 0` → raise).
- Reproduction tối thiểu:
  ```python
  FilePriceProvider([{"product_key": "P1", "effective_from": "2026-01-01",
                      "effective_to": "2026-01-31", "purchase_price": "NaN"}])
  # decimal.InvalidOperation  (mong đợi: InvalidPriceMasterError, reason="invalid_price")
  ```
  Cũng đạt được từ file YAML bằng `purchase_price: .nan` (PyYAML → `float('nan')`
  → `Decimal(str(nan))` → `Decimal('NaN')`).
- Hệ quả: bảng giá **vẫn từ chối nạp** (ồn ào, không âm thầm) — không có giá
  sai nào đi vào data path. Nhưng hợp đồng "Error Semantics" của chính
  artifact (*raise `InvalidPriceMasterError` mang `.reason`*) bị phá cho đúng
  input này, và `TASK-105C` được thiết kế để `except InvalidPriceMasterError`
  khi compose (mục 11 của spec 105C) — handler đó sẽ **không** bắt được.
- Phạm vi remediation tối thiểu: đưa `price < 0` vào trong khối `try` hiện
  có, hoặc chèn một `if not price.is_finite(): raise InvalidPriceMasterError(..., reason="invalid_price")`
  ngay trước dòng 226. Một dòng, không đụng semantics nào khác.
- **RE-TRIGGER CONDITION:** bắt buộc đóng trước khi (a) một bảng giá
  production thật được nạp qua `FilePriceProvider`, HOẶC (b) `TASK-105C`
  implementation bắt đầu — vì spec 105C dựa vào việc bắt
  `InvalidPriceMasterError` cho "file snapshot hỏng". Cơ chế kiểm tra: một
  test khẳng định `pytest.raises(InvalidPriceMasterError)` cho
  `purchase_price` ∈ {`"NaN"`, `"sNaN"`, `float('nan')`}.

**`HB-105B-02` — `Infinity` được nhận là một giá hợp lệ.**

- File/hàm/dòng: cùng `_parse_price()`, **dòng 226–231**. Điều kiện duy nhất
  là `price < 0`; `Decimal('Infinity') < 0` là `False`, nên giá trị đi lọt.
- Reproduction tối thiểu:
  ```python
  p = FilePriceProvider([{"product_key": "P1", "effective_from": "2026-01-01",
                          "effective_to": "2026-01-31", "purchase_price": "Infinity"}])
  p.lookup("P1", date(2026, 1, 15))     # Decimal('Infinity')  — không phải None, không raise
  ```
  Từ YAML: `purchase_price: .inf` (đã xác minh, `records=1`, `lookup=Infinity`).
- Hệ quả: đây là finding **nghiêm trọng nhất về nguyên tắc** trong review
  này, vì nó là trường hợp duy nhất mà một nguồn malformed trở thành một
  *determined value* thay vì bị từ chối: `lookup()` trả `Decimal('Infinity')`
  → `price_engine.apply_prices()` gán `price_source = PRICE_SOURCE_PRICE_MASTER`
  (**không** phải Pending) → đi thẳng vào số học lợi nhuận. Hiện **chưa**
  có đường production nào chạm tới (§5, xem mục BLOCKING) — đó là lý do duy
  nhất nó không phải BLOCKING.
- Phạm vi remediation tối thiểu: cùng một dòng `is_finite()` đóng luôn cả
  `HB-105B-01` và `HB-105B-02`.
- **RE-TRIGGER CONDITION:** giống `HB-105B-01` — (a) bảng giá production
  thật, hoặc (b) mở `TASK-105C` implementation. Cơ chế: test khẳng định
  `purchase_price` ∈ {`"Infinity"`, `"-Infinity"`, `float('inf')`} → raise.

**`HB-105B-03` — YAML `prices:` rỗng-kiểu-null hoặc sai kiểu thoát ra exception thô.**

- File/hàm/dòng: `from_yaml()` **dòng 92–94** (`data.get("prices", [])`) và
  `_parse_rows()` dòng 125–126.
- Reproduction: file chứa đúng `prices:\n` (khoá tồn tại, giá trị `None`)
  → `list(None)` → `TypeError: 'NoneType' object is not iterable`. File chứa
  `prices: {a: 1}` → `AttributeError: 'str' object has no attribute 'get'`.
  (File rỗng hẳn và file thiếu khoá `prices` thì **đúng**: trả provider rỗng.)
- Hệ quả: chỉ là chất lượng thông báo lỗi khi người dùng gõ sai file YAML;
  không có giá sai nào đi qua. Không nằm trong `DEC-145` §5.
- **RE-TRIGGER CONDITION:** khi `FilePriceProvider.from_yaml()` lần đầu được
  gọi trên một file do **người dùng** soạn (không phải fixture test) —
  tức lúc chủ dự án cấp bảng giá thật.

**`HB-105B-04` — `PriceRecord` bỏ qua cột provenance thừa của snapshot 105C.**

- File/hàm/dòng: `_parse_one_row()` **dòng 131–156** đọc đúng 5 khoá; cột lạ
  bị bỏ qua im lặng (đã xác minh: `supplier`/`updated_at` không gây lỗi).
- Hệ quả: Provenance Contract (mục 10) của `TASK-105C` yêu cầu mỗi record
  mang thêm `contributing_ncc`, `captured_at`, `capture_id`; `PriceRecord`
  không có chỗ chứa, và `TASK-105C` **bị cấm sửa `FilePriceProvider`**
  ("Ngoài Phạm Vi" của spec 105C). Đây là **ma sát**, không phải bế tắc:
  105C tự parse CSV nên đã cầm sẵn dict đầy đủ, và có thể giữ side-map khoá
  `(normalized_product_key, effective_from)` — duy nhất vì overlap bị cấm.
- **RE-TRIGGER CONDITION:** tại `TASK-105C` implementation, nếu side-map tỏ
  ra không đủ thì cần một `COMPLETION GATE CHANGE PROPOSAL` cho `TASK-105B`
  (thêm field provenance mở rộng), **không** được sửa lén foundation.

**`HB-105B-05` — `effective_to` mất/gõ sai tên cột trở thành open record im lặng.**

- Vì `_is_blank()` coi thiếu khoá và ô rỗng là như nhau, một cột `effective_to`
  bị gõ sai tên trong file nguồn biến một record lịch sử đã kết thúc thành
  record "còn hiệu lực", kéo dài giá tới `9999-12-31`. Hầu hết trường hợp bị
  chặn gián tiếp (`multiple_open_records` hoặc `overlapping_periods`), nhưng
  **thoát được** nếu record bị hỏng là record cuối cùng theo thời gian và
  bảng không có record mở hợp lệ nào khác.
- Đây là hệ quả của **chính contract đã frozen** (`DEC-145` §1 dùng "rỗng"
  làm tín hiệu "còn hiệu lực"), không phải lỗi implementation — nên là
  HARDENING chứ không phải FAIL.
- **RE-TRIGGER CONDITION:** khi bảng giá production thật xuất hiện — cân
  nhắc một strict-schema check (từ chối cột lạ, hoặc bắt buộc khoá
  `effective_to` phải tồn tại dù rỗng). Cần `COMPLETION GATE CHANGE PROPOSAL`
  vì nó siết `DEC-145` §4.

**`HB-105B-06` — `CHECK-105B-17` chỉ assert trên module, không assert trên test file.**

- `test_module_does_not_import_or_mention_firebase_client()` (test file dòng
  343–346) chỉ đọc `_MODULE_PATH`. Văn bản check nói "Module mới/**test
  mới**". Reviewer đã grep độc lập cả hai file: **không** có import Firebase
  nào ⇒ nội dung check vẫn đúng trên thực tế, chỉ là độ phủ tự động hẹp hơn
  câu chữ.
- **RE-TRIGGER CONDITION:** khi `TASK-105C` thêm test chạm `tools/pricing/`
  (nơi *được phép* gọi mạng) — lúc đó check này cần nói rõ nó bảo vệ
  `app/modules/pricing/**` chứ không phải `tools/**`.

### OUT_OF_SCOPE

- `-0` được nhận là giá hợp lệ (`Decimal('-0') < 0` là `False`). Về giá trị
  nó **bằng** `0`, mà `0` là hợp lệ theo `DEC-145` §5 — không phải defect.
- `product_key` kiểu `int`/`bool` được `str()` hoá (`12345`, `true`).
  `DEC-145` §4 định nghĩa `product_key` là text thô; ép kiểu là cách đọc
  hợp lý, không có luật nào cấm.
- Key chỉ gồm zero-width space (U+200B) không bị coi là rỗng — `\s` không
  khớp U+200B. Chuẩn hoá được `DEC-145` §2 định nghĩa **chính xác** là
  NFC→strip→collapse→casefold; thêm luật là vượt authority.
- `"1e6"`, `"1_000"`, `"+100"` được nhận. Đều cho `Decimal` đúng và chính
  xác; không có luật format nào trong `DEC-145` §4.
- `FilePriceProvider(None)` / `FilePriceProvider(["str"])` raise thô — lỗi
  lập trình của caller, không phải lỗi nội dung bảng giá.
- `lookup(code, datetime)` raise `TypeError`. **Không tới được** từ production
  seam: `WorkingLine.date` là `Optional[date]` (`app/modules/domain/models.py:113`).
- `_reject_overlaps()` là O(n²) theo nhóm key. Đo thực tế: 3.000 record trên
  một key = `0.35s`. Không phải vấn đề ở quy mô dự án.
- `TASK-105B-Q3` (chính sách zero-price dòng phụ) — `OD-105B-01` §C đặt ra
  ngoài phạm vi module này; module xác nhận không mang matcher nào.

## Review Budget

Xác minh từ `PROJECT/REVIEW_BUDGET_LEDGER.md` §"Root Task: TASK-105B":

```
TRƯỚC review:  repair_cycles_allowed: 2   used: 0   remaining: 2
SAU  review:   repair_cycles_allowed: 2   used: 0   remaining: 2   (KHÔNG ĐỔI)
```

Verdict là PASS ⇒ không có repair nào được yêu cầu ⇒ không cycle nào mở.
Đúng luật đã ghi trong chính ledger: *"cycle chỉ mở nếu một vòng Independent
Review sau đó cho verdict FAIL và cần repair"*, và
`governance/core/V4_1_POLICY_FREEZE.md` §3 (cycle tính theo **lần sửa**, không theo số review).

## Repo Mutation Bởi Phiên Review

```
Files changed by reviewer      : 2  (file này + 1 mục ledger)
Production files changed       : 0
Test files changed             : 0
config/ changed                : 0
Implementation branch mutated  : NO
```

Review chạy trên `git worktree` **detached** tại target SHA; `git status
--porcelain` trên worktree đó = **rỗng** sau toàn bộ phiên;
`origin/claude/price-provider-foundation-ahix1t` vẫn trỏ `c22cef8…` sau khi
fetch lại. Harness adversarial được viết **ngoài** repository (scratchpad) và
không commit.

## Kết Luận (Conclusion)

```
VERDICT = PASS — ELIGIBLE_FOR_FREEZE
```

Cơ sở:

- **0 BLOCKING finding** (phân loại theo `governance/core/V4_1_POLICY_FREEZE.md` §5/§7, có
  chứng minh vì sao không nâng bậc).
- **17/17 REQUIRED Completion Gate check PASS độc lập**, không copy trạng
  thái từ artifact implementation.
- **0 regression**: `730 passed, 11 skipped` @ target so với
  `697 passed, 11 skipped` @ base — chênh lệch đúng bằng 33 test mới.
- **Golden không đổi**: `58 passed, 2 skipped`; 4 file production lõi +
  `config/` + Golden fixture diff = 0 byte.
- **Scope/provenance đủ cho downstream contract**: seam `TASK-105C` compose
  được mà không sửa semantics, không bypass validation, không duplicate
  normalization, không cần current-price fallback, giữ nguyên Pending.

## Việc Cần Theo Dõi Tiếp (Required Follow-up)

1. **NEXT AUTHORIZED ACTION = `TASK-105B` FREEZE.** Phiên freeze (khác phiên
   này) chuyển `TASK-105B` sang `DONE` và cập nhật
   `PROJECT/PROJECT_PROGRESS.md`. Phiên review này **không** freeze, **không**
   merge, **không** remediation.
2. `HB-105B-01` + `HB-105B-02` phải được đóng (một dòng `is_finite()`) trước
   khi `TASK-105C` implementation bắt đầu hoặc trước khi bảng giá production
   thật được nạp — tuỳ điều kiện nào tới trước. Đây là công việc của một
   phiên sau, có thẩm quyền sửa `app/**`; **không** phải của phiên review.
3. `HB-105B-03`…`HB-105B-06` mang RE-TRIGGER CONDITION riêng, đọc lại tại
   thời điểm mở `TASK-105C`.
4. Mục Exit Criteria "bảng giá production thật nạp được" vẫn **BLOCKED** —
   data dependency chờ chủ dự án, không phải code blocker, và không chặn
   freeze phần code đã implement.
