# TASK-105 — Price Engine + Interface PriceProvider

## Metadata
Status:
DONE — 9/9 REQUIRED check PASS. 57/57 test tổng (8 test mới + 49 test
TASK-101, không regression).

Phase:
PHASE-01 — Engine tính toán

Task Mode:
MAJOR

Primary Agent Tier:
B

Escalation Tier:
C

Difficulty:
3/5

Risk:
3/5

Blast Radius:
3/5

Project Profile:
PRODUCT

## Mục Tiêu (Objective)

Bước 8 của import workflow §22 đặc tả: tra `AccountingPurchasePrice` (giá
nhập kế toán) cho từng dòng nếu có Price Master, chưa có thì để **Pending**
— không bao giờ suy đoán, không bao giờ coi là 0 (DEC-103, mục 10 đặc tả).

Vì chưa có Price Master nào tồn tại ở Phase 1 (TASK-401, tích hợp
`PriceMasterProvider` thật, ở Phase 4), TASK-105 giao đúng phần nền tảng:
định nghĩa interface `PriceProvider` ổn định, và một implementation mặc
định trả về Pending cho mọi dòng — để khi Price Master thật xuất hiện ở
TASK-401, chỉ cần cắm một `PriceProvider` khác vào, không sửa `price_engine`
hay bất kỳ chỗ nào gọi nó.

## Phạm Vi (Scope)

- Mở rộng `WorkingLine` (domain model) thêm `accounting_purchase_price` và
  `price_source` — theo đúng nguyên tắc "không ngầm định missing/0" của
  `governance/core/03_DATA_MODEL_RULES.md` §5 và ADR-102.
- Định nghĩa `PriceProvider` (Protocol) — `lookup(product_code, sale_date) ->
  Optional[Decimal]`.
- `PendingPriceProvider` — implementation mặc định, luôn trả `None` (Pending)
  cho mọi dòng, vì chưa có Price Master thật.
- `price_engine.apply_prices()` — áp provider vào danh sách `WorkingLine`,
  ghi `accounting_purchase_price` và `price_source` (`Pending` /
  `PriceMaster`).
- Nối vào `app/pipeline.py` làm bước 8, sau bước 7 (propagate LeadSource) đã
  có ở TASK-101. `run_import()` nhận thêm tham số `price_provider` tùy
  chọn, mặc định `PendingPriceProvider()`.
- Test đơn vị + tích hợp trên fixture đã có của TASK-101 (không cần dữ liệu
  thật — hành vi kỳ vọng là **mọi dòng đều Pending** ở Phase 1, vì thật sự
  chưa có Price Master nào, không phải một giới hạn của môi trường test).

## Ngoài Phạm Vi (Out of Scope)

- `AdjustmentEngine` (TASK-106) — parse `Qua kho -100`, `KHBH -50`... từ ghi
  chú thành `kpi_purchase_adjustment`. TASK-105 không đụng cột `Giao hàng`.
- `kpi_purchase_price = accounting_purchase_price + kpi_purchase_adjustment`
  — cần adjustment từ TASK-106 trước, nên phép cộng này không thuộc
  TASK-105.
- `profit_engine` (TASK-107), `conversion_engine` (TASK-108).
- Tích hợp Price Master thật, schema `ProductCode/ProductName/Supplier/...`
  — đó là TASK-401 (Phase 4). TASK-105 chỉ định nghĩa interface mà TASK-401
  sẽ implement.
- `product_mapper` (TASK-402, Phase 4) — sinh `ProductCode` chuẩn từ
  `ProductRaw`. Vì chưa có, `price_engine` dùng `product_raw` làm khóa tra
  cứu tạm thời; ghi rõ đây là placeholder, không phải quyết định thiết kế
  cuối cùng.
- Manual override giá nhập (nhập tay ở UI/API) — cần audit trail
  (TASK-202, Phase 2). DEC-103 yêu cầu "luôn nhập tay được ở mọi dòng" —
  TASK-105 không cản trở việc đó (field vẫn ghi đè được ở tầng dữ liệu),
  nhưng không xây cơ chế override/audit ở Phase 1.

## Phụ Thuộc (Dependencies)
- TASK-101 — DONE. Cung cấp `WorkingLine`, `app/pipeline.py::run_import()`
  để mở rộng.
- DEC-103 — quyết định nghiệp vụ nền tảng cho task này.

## Chặn (Blocks)
- TASK-107 (profit_engine) cần `accounting_purchase_price` đã có mặt trên
  `WorkingLine` để tính `AccountingProfit`.
- TASK-401 (Phase 4) implement `PriceProvider` thật — cần interface này ổn
  định trước.

## An Toàn Để Chạy Song Song Với (Parallel-Safe With)
- TASK-103/TASK-104 (đã DONE, không áp dụng).
- Track B (Governance) — không chạm chung file.

## Phạm Vi Tác Động Dự Kiến (Expected Touch Area)

Allowed:
- `app/modules/domain/models.py` (mở rộng, không phá field cũ)
- `app/modules/pricing/` (module mới)
- `app/pipeline.py` (thêm bước 8)
- `tests/` (test mới cho pricing)
- `docs/tasks/TASK-105-price-engine.md`
- `PROJECT/PROJECT_PROGRESS.md`, `PROJECT/LO_TRINH_DE_HIEU.md`
- `docs/sessions/`

Không được đụng vào nếu chưa có Scope Expansion:
- `app/modules/mapping/`, `app/modules/orders/`, `app/modules/lead_source/`
  (đã DONE ở TASK-101, không sửa trừ khi phát hiện lỗi thật).
- `docs/analysis/`, `docs/adr/`, `PROJECT/PROJECT_DECISIONS.md`.
- Bất kỳ file nào của Track B.

## Subtask (Subtasks)
- [x] 105.1 Domain model: `accounting_purchase_price`, `price_source`
- [x] 105.2 `PriceProvider` interface + `PendingPriceProvider`
- [x] 105.3 `price_engine.apply_prices()`
- [x] 105.4 Nối vào `run_import()` (bước 8)
- [x] 105.5 Test suite (8 test mới, 57/57 tổng PASS)

## Ready Gate
Dùng `governance/core/TASK_READY_GATE_STANDARD.md`.

- [x] Objective rõ ràng.
- [x] Scope đã được xác định.
- [x] Out-of-scope đã được xác định (ranh giới rõ với TASK-106/107/401/402).
- [x] Dependency (TASK-101) đã DONE.
- [x] Vùng tác động dự kiến đã được xác định.
- [x] Yêu cầu liên quan đã hiểu rõ (đặc tả §10/§20/§22 bước 8, DEC-103).
- [x] Tác động dữ liệu đã biết rõ: không có dữ liệu cá nhân mới; giá nhập là
      dữ liệu nghiệp vụ nhạy cảm (`governance/core/04_SECURITY_RULES.md`)
      nhưng chưa lộ ra
      UI/API ở Phase 1.
- [x] Tác động bảo mật đã biết rõ: không có, chưa có network/DB.
- [x] Không liên quan routing/API (Phase 1 thuần Python).
- [x] Không có migration (chưa có DB).
- [x] Difficulty/Risk/Blast Radius đã chấm điểm (3/3/3, theo bảng sơ bộ
      `PROJECT/PROJECT_PROGRESS.md`).
- [x] Agent tier đã chỉ định (B, escalation C).
- [x] Escalation trigger đã xác định (xem bên dưới).
- [x] Completion Gate đã hoàn thiện và **frozen** trước khi implement.

## Completion Gate
Dùng `governance/core/TASK_COMPLETION_GATE_STANDARD.md` và
`governance/core/EVIDENCE_STANDARD.md`.

### Functional

#### CHECK-105-01 — PendingPriceProvider luôn trả None (không suy đoán)
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`pytest tests/test_price_provider.py -q` → 2/2 passed. Xác nhận
`PendingPriceProvider.lookup()` trả `None` bất kể `product_code`/`sale_date`
là gì, kể cả khi cả hai đều `None`.

Executed By:
Claude (session này)

Timestamp:
2026-08-23

#### CHECK-105-02 — price_engine không bao giờ coi giá thiếu là 0
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`pytest tests/test_price_engine.py -q` → 4/4 passed. Case
`test_pending_provider_leaves_price_none_not_zero` và
`test_unmatched_product_stays_pending_even_with_a_real_provider` xác nhận
`accounting_purchase_price is None` (không phải `Decimal("0")`) khi provider
không tìm thấy giá — kể cả khi provider là một provider "thật" có dữ liệu
cho sản phẩm khác trong cùng lần chạy.

Executed By:
Claude (session này)

Timestamp:
2026-08-23

#### CHECK-105-03 — price_source ghi đúng nguồn (Pending / PriceMaster)
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`test_matched_provider_sets_price_and_source` xác nhận `price_source =
PRICE_SOURCE_PRICE_MASTER` khi có giá; các case còn lại xác nhận
`price_source = PRICE_SOURCE_PENDING` khi không có giá.

Executed By:
Claude (session này)

Timestamp:
2026-08-23

#### CHECK-105-04 — Provider tùy chỉnh cắm được qua dependency injection, không sửa price_engine
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`tests/test_pipeline.py::test_custom_price_provider_injected_without_touching_price_engine`
— truyền `_FixedPriceProvider` (định nghĩa ngay trong test, không sửa
`price_engine.py`/`provider.py`) vào `run_import(price_provider=...)`, xác
nhận giá được áp đúng cho sản phẩm khớp và vẫn Pending cho sản phẩm không
khớp trong cùng lần chạy.

Executed By:
Claude (session này)

Timestamp:
2026-08-23

#### CHECK-105-05 — run_import() gọi đúng bước 8 sau bước 7, mặc định PendingPriceProvider
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`test_default_run_leaves_every_price_pending` — gọi `run_import()` không
truyền `price_provider`, xác nhận mọi dòng trong kết quả đều
`price_source = PRICE_SOURCE_PENDING`, đúng hành vi mặc định
`PendingPriceProvider()`. Đọc `app/pipeline.py` xác nhận `apply_prices()`
được gọi sau `classifier.apply()` (bước 6–7), trước khi trả `ImportResult`.

Executed By:
Claude (session này)

Timestamp:
2026-08-23

### Architecture

#### CHECK-105-06 — Không import fastapi/sqlalchemy/web trong app/modules/pricing/
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
```
$ grep -rn "^import fastapi\|^from fastapi\|^import sqlalchemy\|^from sqlalchemy\|^import flask\|^from flask" app/modules/pricing/
(không có kết quả)
```

Executed By:
Claude (session này)

Timestamp:
2026-08-23

#### CHECK-105-07 — Không hard-code giá trị giá nhập cụ thể nào trong code
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
Output lệnh `grep` thực thi:
```
$ grep -rnE "[0-9]{6,}" app/modules/pricing/ app/pipeline.py
(không có kết quả)
```
`price_engine.py`/`provider.py` không chứa số tiền cụ thể nào — mọi giá trị
giá tới từ `PriceProvider.lookup()` do caller cung cấp.

Executed By:
Claude (session này)

Timestamp:
2026-08-23

### Data

#### CHECK-105-08 — Tiền lưu Decimal, không float
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`accounting_purchase_price: Optional[Decimal]` trong
`app/modules/domain/models.py`.
`PriceProvider.lookup()` khai kiểu trả về `Optional[Decimal]`. Grep xác nhận
không có `float(` nào trong `app/modules/pricing/`.

Executed By:
Claude (session này)

Timestamp:
2026-08-23

### Regression

#### CHECK-105-09 — Toàn bộ test TASK-101 vẫn PASS sau khi mở rộng domain model
Priority:
REQUIRED

Status:
PASS

Evidence Level:
E1

Evidence:
`pytest tests/ -q` → **57/57 passed** (49 test cũ của TASK-101 + 8 test mới
của TASK-105: 2 provider + 4 price_engine + 2 pipeline integration). Không
regression — thêm field có default value vào cuối `WorkingLine` không phá
constructor call nào đã có.

Executed By:
Claude (session này)

Timestamp:
2026-08-23

## Tiêu Chí Hoàn Thành (Exit Criteria)
- [x] 100% REQUIRED check PASS — 9/9.
- [x] Không có lỗi nghiêm trọng chưa xử lý.
- [x] Evidence level E1 đạt được cho mọi check.
- [x] `PROJECT/PROJECT_PROGRESS.md` và `PROJECT/LO_TRINH_DE_HIEU.md` cập
      nhật đồng thời.
- [x] Session handoff đã viết (MAJOR task).
- [x] Toàn bộ 49 test cũ của TASK-101 vẫn PASS (không regression) — 57/57
      tổng.

## Điều Kiện Kích Hoạt Leo Thang (Escalation Triggers)
- Phát hiện cần thay đổi interface `PriceProvider` sau khi TASK-401 thật sự
  tích hợp Price Master (đổi signature `lookup()`).
- Phát hiện `product_raw` không đủ để làm khóa tra cứu tạm thời (yêu cầu
  product_mapper sớm hơn kế hoạch).

## Đăng Ký File Đã Thay Đổi (Changed Files Registry)

Created:
- `app/modules/pricing/__init__.py`, `provider.py`, `price_engine.py`
- `tests/test_price_provider.py`, `test_price_engine.py`
- `docs/tasks/TASK-105-price-engine.md`

Modified:
- `app/modules/domain/models.py` — thêm `PRICE_SOURCE_*`,
  `WorkingLine.accounting_purchase_price`, `WorkingLine.price_source`
- `app/pipeline.py` — thêm bước 8, tham số `price_provider`
- `tests/test_pipeline.py` — thêm 2 test tích hợp pricing
- `PROJECT/PROJECT_PROGRESS.md`, `PROJECT/LO_TRINH_DE_HIEU.md` — đồng bộ
  theo "Giao thức Đóng Phiên"

Deleted:
- Không có.

Migration Impact:
- Không có (chưa có DB ở Phase 1).

## Ghi Chú (Notes)

**Vì sao "chưa có thì Pending" đúng cho 100% dòng ở Phase 1, không phải một
giới hạn tạm thời của test:** không giống TASK-101 (nơi dữ liệu thật tồn tại
nhưng không có trong môi trường), ở đây **không có Price Master nào tồn tại
ở bất kỳ đâu** — kể cả với dữ liệu thật, `PendingPriceProvider` vẫn là
provider đúng cho tới khi TASK-401 (Phase 4) xây xong tích hợp thật. Không
có "đối chiếu số liệu thật" nào cần chờ ở task này.
