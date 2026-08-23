# BÀN GIAO SESSION (SESSION HANDOFF)

Session ID:
S010

Task:
TASK-101 — importer + normalizer

Task Mode:
MAJOR

Project Profile:
PRODUCT

Status:
VERIFYING — implement xong, 12/13 REQUIRED check PASS trên fixture tổng hợp
ẩn danh. 1 REQUIRED check BLOCKED vì thiếu dữ liệu thật trong môi trường này.

## Kết Quả (Result)

Xây xong engine Python thuần (không UI, không database — ADR-101) đọc sổ bán
hàng thô `.xlsx`, chuẩn hóa dữ liệu, áp employee mapping, nhóm theo OrderID,
và phân loại `LeadSource` cấp đơn — đúng 7 bước đầu của import workflow §22
đặc tả. Phạm vi này trùng với năng lực lõi mà TASK-102 (employee_mapper),
TASK-103 (order_builder) và TASK-104 (lead_source_engine) định xây riêng —
cả ba được xây chung trong session này thay vì tách 3 task/session/gate
riêng biệt, vì roadmap tự mô tả chúng là một phần của "7 bước đầu" TASK-101.

Chạy được ngay bây giờ bằng:
```python
from pathlib import Path
from app.pipeline import run_import
result = run_import(Path("data/samples/So_chi_tiet_ban_hang.xlsx"))
```

**Giới hạn quan trọng, không phải lỗi implementation:**
`data/samples/So_chi_tiet_ban_hang.xlsx` không tồn tại trong môi trường thực
thi này — đúng theo DEC-108 (dữ liệu cá nhân khách hàng không bao giờ được
commit). Mọi bằng chứng trong session này lấy từ fixture tổng hợp đã ẩn danh
(`tests/fixtures/synthetic_workbook.py`), không phải file thật. REQUIRED
check duy nhất cần file thật — đối chiếu 254 đơn (01.2026) / 146 đơn
(06.2026) — bị đánh dấu **BLOCKED**, không PASS giả.

## Subtask Đã Hoàn Thành (Subtasks Completed)
- [x] 101.1 Domain models (`app/modules/domain/models.py`, `money.py`)
- [x] 101.2 Config loader + `config/employees.yaml` + `config/lead_source.yaml`
- [x] 101.3 Raw reader (`app/modules/importing/raw_reader.py`)
- [x] 101.4 Metadata preview (`app/modules/importing/preview.py`)
- [x] 101.5 Normalizer, trừ Chiết khấu (`app/modules/importing/normalizer.py`)
- [x] 101.6 Employee mapper (`app/modules/mapping/employee_mapper.py`)
- [x] 101.7 Order builder (`app/modules/orders/order_builder.py`)
- [x] 101.8 Lead source classifier (`app/modules/lead_source/classifier.py`)
- [x] 101.9 Pipeline orchestration (`app/pipeline.py`)
- [x] 101.10 Fixture ẩn danh + test suite (49/49 PASS)

## Subtask Còn Lại (Subtasks Remaining)
- Đối chiếu với `data/samples/So_chi_tiet_ban_hang.xlsx` thật (CHECK-101-08)
  khi file có sẵn trong môi trường thực thi.

## Tóm Tắt Completion Gate (Completion Gate Summary)

Required:
13 (CHECK-101-01 đến 06, 08 đến 13) + 1 RECOMMENDED (CHECK-101-07)

PASS:
12 (CHECK-101-01 đến 07, 09 đến 13)

FAIL:
0

BLOCKED:
1 (CHECK-101-08 — thiếu `data/samples/` thật)

NOT_TESTED:
0

## Evidence Xác Minh (Verification Evidence)

| Check ID | Status | Evidence Level | Evidence | Executed By | Timestamp |
|---|---|---|---|---|---|
| CHECK-101-01 | PASS | E1 | `pytest tests/test_raw_reader.py -q` → 5/5 | Claude | 2026-08-23 |
| CHECK-101-02 | PASS | E1 | `pytest tests/test_normalizer.py -q` → 6/6 | Claude | 2026-08-23 |
| CHECK-101-03 | PASS | E1 | `pytest tests/test_employee_mapper.py -q` → 7/7 | Claude | 2026-08-23 |
| CHECK-101-04 | PASS | E1 | `pytest tests/test_order_builder.py -q` → 3/3 | Claude | 2026-08-23 |
| CHECK-101-05 | PASS | E1 | `pytest tests/test_lead_source_classifier.py -q` → 19/19 | Claude | 2026-08-23 |
| CHECK-101-06 | PASS | E1 | propagate test trong test_lead_source_classifier.py + test_pipeline.py | Claude | 2026-08-23 |
| CHECK-101-07 | PASS | E1 | `test_preview_matches_synthetic_file` | Claude | 2026-08-23 |
| CHECK-101-08 | **BLOCKED** | — | `data/samples/` không tồn tại trong session này | — | — |
| CHECK-101-09 | PASS | E1 | grep xác nhận không import fastapi/sqlalchemy trong `app/` | Claude | 2026-08-23 |
| CHECK-101-10 | PASS | E1 | grep xác nhận không hard-code rate/target/keyword | Claude | 2026-08-23 |
| CHECK-101-11 | PASS | E1 | `RawRow` là `@dataclass(frozen=True)`, đủ trường provenance | Claude | 2026-08-23 |
| CHECK-101-12 | PASS | E1 | Mọi field tiền là `Decimal`, không `float()` coercion | Claude | 2026-08-23 |
| CHECK-101-13 | PASS | E1 | grep xác nhận không `print`/`logging` trong `app/` | Claude | 2026-08-23 |

Chi tiết đầy đủ: `docs/tasks/TASK-101-importer-normalizer.md`.

## File Đã Thay Đổi (Files Changed)

Created:
- `app/` (toàn bộ package mới — 7 module theo ADR-101)
- `config/employees.yaml`, `config/lead_source.yaml`
- `pyproject.toml`
- `tests/` (toàn bộ — factories, fixture ẩn danh, 6 file test)
- `docs/tasks/TASK-101-importer-normalizer.md`
- `docs/sessions/S010-task-101-importer-normalizer.md` (file này)

Modified:
- `PROJECT/PROJECT_PROGRESS.md` — roadmap TASK-101/102/103/104, "Trạng thái
  Task hiện tại", lịch sử session, "Session tiếp theo"
- `PROJECT/LO_TRINH_DE_HIEU.md` — đồng bộ theo "Giao thức Đóng Phiên"

Deleted:
- Không có.

## Quyết Định Chính (Key Decisions)
- TASK-102/103/104 không tách task/session/gate riêng — năng lực lõi của
  chúng nằm trong phạm vi tự mô tả của TASK-101 ("7 bước đầu"), xây chung để
  tránh trùng lặp interface. Nếu phát sinh yêu cầu mở rộng thật sự riêng biệt
  (UI quản lý mapping, product classification), mở lại task tương ứng lúc đó.
- `ConversionScheme` **không** được xây trong session này — đúng ranh giới
  ADR-104: TASK-101/104 chỉ quyết định `LeadSource`, TASK-108 mới quyết định
  tỉ lệ.
- Fixture test là tổng hợp/ẩn danh hoàn toàn (DEC-108), không dùng bất kỳ dữ
  liệu thật nào — vì `data/samples/` không có trong môi trường này.

## Rủi Ro / Vướng Mắc (Risks / Blockers)
- **CHECK-101-08 BLOCKED** — cần chủ dự án cung cấp lại
  `data/samples/So_chi_tiet_ban_hang.xlsx` (đặt vào thư mục, không commit) để
  đối chiếu 254/146 đơn. Đây là blocker duy nhất giữ TASK-101 ở VERIFYING
  thay vì DONE.
- Số nhân sinh sản phẩm khác (product/transaction classification, dòng phụ
  có giá trị tiền theo DEC-110/113) chưa được xây — đúng phạm vi gốc của
  TASK-103, không phải thiếu sót của session này.

## Hạng Mục Regression (Regression Items)
- Chưa có mã ứng dụng nào tồn tại trước session này ở `app/` — không có
  regression để kiểm tra.

## Chưa Được Thay Đổi (Do Not Change Yet)
- `docs/analysis/`, `docs/adr/` (trừ việc đọc tham khảo)
- `PROJECT/PROJECT_DECISIONS.md`
- Mọi file thuộc Track B (`docs/audit/`, `docs/tasks/TASK-REM-*.md`)

## Session Tiếp Theo Được Khuyến Nghị (Next Recommended Session)
Một trong hai, không bắt buộc thứ tự:
1. Đóng CHECK-101-08 khi có `data/samples/` thật → TASK-101 chuyển DONE.
2. TASK-105 (price_engine + interface PriceProvider) — module độc lập.

## File Agent Tiếp Theo Cần Đọc (Files Next Agent Should Read)
- `CLAUDE.md`
- `PROJECT/PROJECT_PROGRESS.md` (mục "Trạng thái Task hiện tại")
- `docs/tasks/TASK-101-importer-normalizer.md`
- `app/pipeline.py`, `app/modules/` (code đã có, đừng viết lại)
- `docs/adr/ADR-104-lead-source-vs-conversion-scheme.md` (ranh giới
  LeadSource/ConversionScheme khi làm TASK-108)
