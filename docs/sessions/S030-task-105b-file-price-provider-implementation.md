# BÀN GIAO SESSION (SESSION HANDOFF)

Session ID:
S030

Task:
TASK-105B — FilePriceProvider

Task Mode:
MAJOR

Project Profile:
PRODUCT

Status:
IMPLEMENTED — SELF-VERIFIED. `INDEPENDENT_REVIEW = REQUIRED`. Không tự
DONE (`Effective Risk = HIGH`, đúng tiền lệ `TASK-GOLDEN-BASELINE-001`).

## Kết Quả (Result)

Implement `FilePriceProvider` (`app/modules/pricing/file_price_provider.py`)
đúng contract `DEC-145`/`OD-105B-01` (§38 của
`docs/tasks/TASK-108B-eligible-costs-owner-definition.md`) — implementation
thứ hai của `PriceProvider` Protocol, đọc bảng giá 4 cột, khoảng hiệu lực
**đóng**, chuẩn hoá NFC+casefold, validation §5 đầy đủ (overlap, >1 open
record, giá âm/rỗng, ngày lỗi, duplicate hoàn toàn), provenance 3 phần
(raw key / normalized key / matched record), `InvalidPriceMasterError`
raise khi **nạp** bảng giá, không phải khi tra từng dòng.

Đồng thời **frozen** Completion Gate chính thức cho `TASK-105B` tại
`docs/tasks/TASK-105B-file-price-provider.md` — trước phiên này gate chỉ
tồn tại dưới dạng "đề xuất" (§38.5 của tài liệu discovery `TASK-108B`).
17 check (16 gốc + 1 mới đóng risk note Firebase-import của `DEC-146`),
toàn bộ nội dung bắt nguồn từ Owner Decision đã có, không phát minh
business rule mới.

**Không đổi provider mặc định** — `app/pipeline.py` vẫn
`PendingPriceProvider`; Golden Baseline không bị chạm (verified: `pytest
tests/test_golden_baseline.py -q` = `58 passed, 2 skipped`, y hệt trước
phiên).

## Subtask Đã Hoàn Thành (Subtasks Completed)

- `FilePriceProvider`, `PriceRecord`, `InvalidPriceMasterError` implement
  đầy đủ (`app/modules/pricing/file_price_provider.py`).
- 33 test mới (`tests/test_file_price_provider.py`), map 1:1 vào
  CHECK-105B-01..17.
- Completion Gate CHECK-105B-01..17 frozen
  (`docs/tasks/TASK-105B-file-price-provider.md`).
- `PROJECT/PROJECT_PROGRESS.md`, `PROJECT/LO_TRINH_DE_HIEU.md`,
  `PROJECT/REVIEW_BUDGET_LEDGER.md` cập nhật đồng bộ (đúng "Giao thức
  Đóng Phiên").
- Full regression + Golden + 4 validator + `git diff --check` +
  `branch_authority_check.sh` — toàn bộ chạy, evidence ghi trong gate.

## Subtask Còn Lại (Subtasks Remaining)

- **Independent Review** của `TASK-105B` — session khác, đọc code từ
  đầu, chạy lại evidence độc lập, ghi verdict
  (`governance/core/EVIDENCE_STANDARD.md` E2,
  `governance/templates/E2_INDEPENDENT_REVIEW_TEMPLATE.md`,
  `docs/reviews/`).
- Bảng giá production thật (`.yaml`, đúng schema `DEC-145` §4) — chủ dự
  án cấp; không phải việc agent tự làm. Khi có, chỉ cần
  `FilePriceProvider.from_yaml(<path>)`, không sửa code.
- Sau khi `TASK-105B` `DONE` (qua review): mở `TASK-105C`
  (`HistoricalVendorPriceProvider`, compose `FilePriceProvider`) — **chưa
  được bắt đầu trong phiên này**, đúng scope lock của prompt.

## Tóm Tắt Completion Gate (Completion Gate Summary)

Required:
17 (CHECK-105B-01..17)

PASS:
17

FAIL:
0

BLOCKED:
0

NOT_TESTED:
0 (mọi check REQUIRED đã thực thi thật trong phiên; xem Evidence bên dưới)

Exit Criteria bổ sung ngoài 17 check — "bảng giá production thật nạp
được": **CHƯA đạt** (data dependency, không phải code blocker — xem
`docs/tasks/TASK-105B-file-price-provider.md` §"Data Dependency Còn Mở").

## Evidence Xác Minh (Verification Evidence)

| Check ID | Status | Evidence Level | Evidence | Executed By | Timestamp |
|---|---|---|---|---|---|
| CHECK-105B-01 | PASS | E1 | `pytest tests/test_file_price_provider.py -q` — `33 passed` | Agent (phiên S030) | 2026-08-28 |
| CHECK-105B-02..11, 15, 17 | PASS | E1 | cùng lệnh trên, xem tên test tương ứng trong `docs/tasks/TASK-105B-file-price-provider.md` §Completion Gate | Agent (phiên S030) | 2026-08-28 |
| CHECK-105B-12 | PASS | E2 | `python3 -m pytest tests/test_golden_baseline.py -q` → `58 passed, 2 skipped` (y hệt baseline trước phiên) | Agent (phiên S030) | 2026-08-28 |
| CHECK-105B-13 | PASS | E1 | `python3 -m pytest -q` → `730 passed, 11 skipped` (baseline trước phiên `697 passed, 11 skipped`; chênh lệch = đúng 33 test mới, 0 fail, 0 skip mới) | Agent (phiên S030) | 2026-08-28 |
| CHECK-105B-14 | PASS | E1 | `git diff --quiet -- app/pipeline.py app/modules/pricing/price_engine.py app/modules/pricing/provider.py app/modules/domain/models.py` → exit 0 | Agent (phiên S030) | 2026-08-28 |
| CHECK-105B-16 | PASS | E1 | `bash scripts/branch_authority_check.sh` sau khi push → `AUTHORITY_OK` (xem SHA cuối phiên bên dưới) | Agent (phiên S030) | 2026-08-28 |

Validators (không phải CHECK-105B riêng, nhưng REQUIRED cho session close):
`validate_structure` PASS, `validate_project_state` PASS,
`validate_evidence` PASS (88 REQUIRED PASS record), `validate_task_completion`
PASS (6 DONE task), `validate_reference_integrity` FAIL đúng 3 lỗi tiền
tồn `TASK-REM-T06` (không lỗi mới — xác nhận trước/sau khi thêm
`docs/tasks/TASK-105B-file-price-provider.md`).

Rule:
- Không được khẳng định một kiểm tra đã được thực thi trừ khi có evidence thực tế.
- Nếu một lệnh/test/kiểm tra chưa được chạy, dùng `NOT_TESTED`.
- Về mức evidence tối thiểu theo rủi ro, tuân theo `governance/core/EVIDENCE_STANDARD.md`.

## File Đã Thay Đổi (Files Changed)

Created:
- `app/modules/pricing/file_price_provider.py`
- `tests/test_file_price_provider.py`
- `docs/tasks/TASK-105B-file-price-provider.md`
- `docs/sessions/S030-task-105b-file-price-provider-implementation.md` (file này)

Modified:
- `PROJECT/PROJECT_PROGRESS.md`
- `PROJECT/LO_TRINH_DE_HIEU.md`
- `PROJECT/REVIEW_BUDGET_LEDGER.md`

Deleted:
- (không có)

Không đổi một byte (xác minh bằng `git diff --stat`/`--quiet`):
`app/pipeline.py`, `app/modules/pricing/provider.py`,
`app/modules/pricing/price_engine.py`, `app/modules/domain/models.py`,
`config/**`, `tests/fixtures/golden/**`, `tests/test_golden_baseline.py`,
`governance/**`.

## Quyết Định Chính (Key Decisions)

- **Freeze Completion Gate ngay trong phiên implementation**, thay vì
  chờ một phiên Scope-Lock riêng: nội dung 16/17 check bắt nguồn thẳng
  từ `DEC-145`/`OD-105B-01` đã Owner duyệt và §38.5 (đã "đề xuất" từ
  trước) — không phải business rule mới, chỉ là chính thức hoá tài liệu
  đã tồn tại. `CHECK-105B-17` đóng risk note đã ghi tại `DEC-146`.
- **Không tạo `config/prices.yaml` với dữ liệu giả** — vì không có bảng
  giá production thật trong phiên này, việc tạo một file giả trong
  `config/` có nguy cơ bị nhầm là dữ liệu thật. Toàn bộ test dùng fixture
  tổng hợp qua `tmp_path`/inline dict, không chạm `config/`.
- **`InvalidPriceMasterError` mang `.reason` (mã chuỗi)** thay vì nhiều
  subclass riêng — giữ đúng tiền lệ `AmbiguousSchemeConfigError` (một
  exception, message rõ ràng), nhưng thêm `.reason` để test/`TASK-105C`
  phân biệt được luật `DEC-145 §5` nào kích hoạt mà không cần parse text.
- **Không viết Vietnamese prose bên trong `file_price_provider.py`**
  (docstring/comment bằng tiếng Anh, theo đúng precedent của
  `provider.py`/`price_engine.py`/`scheme_resolver.py`/`text.py` đã có
  trong repo) — vừa nhất quán với code hiện có, vừa loại bỏ hoàn toàn
  rủi ro va vào keyword dòng phụ cấm ở `CHECK-105B-15` (message lỗi nội
  bộ vẫn tiếng Việt, trích dẫn `DEC-145`, đã grep xác nhận không chứa
  keyword nào).

## Rủi Ro / Vướng Mắc (Risks / Blockers)

- Bảng giá production thật chưa có — xem "Subtask Còn Lại". Không chặn
  Independent Review (review đánh giá code + test, không cần dữ liệu
  thật để xác nhận contract đúng).
- `TASK-105C` **tuyệt đối không được bắt đầu** cho tới khi `TASK-105B`
  qua Independent Review và `DONE` — nhắc lại rõ trong
  `PROJECT/PROJECT_PROGRESS.md` "NEXT AUTHORIZED ACTION".

## Hạng Mục Regression (Regression Items)

- 0 regression trên `pytest -q` toàn bộ (730 passed, 11 skipped — tăng
  đúng 33 test mới so với baseline 697 passed, 11 skipped).
- 0 regression trên Golden Baseline (58 passed, 2 skipped, y hệt).
- 0 regression trên `validate_reference_integrity` (vẫn đúng 3 lỗi tiền
  tồn `TASK-REM-T06`, không lỗi mới — đã tự phát hiện và sửa 2 lỗi mới
  phát sinh từ chính file mới trong phiên này trước khi handoff, xem Key
  Decisions).

## Chưa Được Thay Đổi (Do Not Change Yet)

- `app/pipeline.py`, `app/modules/pricing/provider.py`,
  `app/modules/pricing/price_engine.py`, `app/modules/domain/models.py`
  — bất biến quan trọng nhất của task này, xác minh bằng diff = 0.
- `config/validation.yaml` (`aggregate: true`) — KHÔNG lật `aggregate:
  false`. `DEC-145` Risk section ghi rõ việc lật này chỉ đến **sau khi**
  `FilePriceProvider` trở thành production path thật (chưa xảy ra —
  provider mặc định vẫn `PendingPriceProvider`).
- `TASK-105C`, Product Identity Mapping, `TASK-105B-Q3`, `TASK-108B` —
  ngoài phạm vi phiên này, không implement.

## Session Tiếp Theo Được Khuyến Nghị (Next Recommended Session)

**`TASK-105B` INDEPENDENT REVIEW** — một session khác, đọc
`app/modules/pricing/file_price_provider.py` +
`tests/test_file_price_provider.py` từ đầu (không tin narrative của
phiên này), chạy lại toàn bộ evidence ở
`docs/tasks/TASK-105B-file-price-provider.md` §Completion Gate một cách
độc lập, đặc biệt xác nhận lại CHECK-105B-14 (diff = 0 trên 4 file
production cũ) và đối chiếu §5 validation với `DEC-145` nguyên văn. Ghi
verdict theo `governance/core/EVIDENCE_STANDARD.md` (E2), lưu tại
`docs/reviews/`.

Chỉ sau khi review đó PASS và `TASK-105B` chuyển `DONE` mới được mở
`TASK-105C`.

## File Agent Tiếp Theo Cần Đọc (Files Next Agent Should Read)

- `CLAUDE.md`
- `PROJECT/PROJECT_PROGRESS.md`
- `PROJECT/REVIEW_BUDGET_LEDGER.md`
- `docs/tasks/TASK-105B-file-price-provider.md` (canonical, gate + evidence)
- `PROJECT/PROJECT_DECISIONS.md` — `DEC-145` (dòng ~3117)
- `app/modules/pricing/file_price_provider.py`
- `tests/test_file_price_provider.py`
- `governance/core/EVIDENCE_STANDARD.md`,
  `governance/templates/E2_INDEPENDENT_REVIEW_TEMPLATE.md`
