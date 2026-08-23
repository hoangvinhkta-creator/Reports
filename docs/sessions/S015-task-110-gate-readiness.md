# BÀN GIAO SESSION (SESSION HANDOFF)

Session ID:
S015

Task:
TASK-110 — Validation + Review Queue (**Gate / Readiness Review**, không triển khai)

Task Mode:
MAJOR

Project Profile:
PRODUCT

Status:
TASK-110 = **PLANNED**. Ready Gate đạt **16/17** mục. Mục còn thiếu duy nhất:
**chủ dự án freeze Completion Gate**. Không viết dòng code ứng dụng nào — đúng
chỉ đạo "chưa code cho tới khi Gate được xác nhận".

## Kết Quả (Result)

Đọc toàn bộ tài liệu điều phối tại checkpoint `c7a1b24`, đối chiếu §18 đặc tả
với mã nguồn thật, và phát hiện **bản đặc tả thiếu 4 business rule có thể làm
sai kết quả**. Đã STOP và hỏi chủ dự án trước khi soạn Gate. Bốn câu trả lời
ghi thành **DEC-128**.

**Đồng bộ nhánh (bước 0):** nhánh mặc định origin =
`claude/extract-upload-repo-gq2ws4`; HEAD cục bộ = `c7a1b24` = origin,
**0 ahead / 0 behind**. Không có track song song nào đang làm TASK-110.

### Bốn khoảng trống nghiệp vụ (đã đóng bằng DEC-128)

| # | Khoảng trống | Bằng chứng | Quyết định của chủ dự án |
|---|---|---|---|
| F-02 | `Missing: thiếu giá nhập` bắn trên **11.765/11.765** dòng — `PendingPriceProvider.lookup()` trả `None` cho mọi dòng theo đúng thiết kế DEC-103 | `app/modules/pricing/provider.py:32-38` | Nén thành **một** mục tổng hợp |
| F-03 | `Suspicious: lợi nhuận âm` không có cơ sở: `accounting_profit is None` ở 100% dòng (`profit_engine.py:27-34`), còn `source_profit` của ERP (**1.912** dòng âm) bị `docs/analysis/01_DATA_MAPPING.md` §3 cấm dùng làm dữ liệu kế toán | `evidence.json:raw.rows_negative_profit = 1912` | Tách làm **hai loại riêng**, loại ERP ghi nhãn "chưa kiểm chứng" |
| F-03b/F-04 | (a) `SL ≤ 0`/`giá bán = 0` không phân biệt được với **1.261** dòng phụ hợp lệ (30 loại) vì TASK-103 chưa làm; (b) `Duplicate: cùng source_file + source_row` **bất khả thi** — cặp đó duy nhất theo cấu tạo | `evidence.json:raw.non_product_line_types`; `raw_reader.py:66-97` | Danh sách từ khóa trong config + `row_hash` trong batch |
| F-05 | Đơn 2 nhân viên: `order_builder` **lặng lẽ lấy dòng đầu tiên** (`order_builder.py:24`), nên cả đơn nhận tỉ lệ của người đó | Comment ngay trong file đã ghi rõ đây là việc của TASK-110 | **Chỉ phát hiện**, không đổi cách tính |

### TD-001 — kiểm tra riêng theo yêu cầu

**Phát hiện quan trọng nhất của phiên này.** F2/F4 hiện **chỉ tồn tại trong
`tools/analysis/reconcile_conversion.py`** — một script phân tích chạy tay,
**không nằm trên đường đi của `run_import()`**. TD-001 yêu cầu chúng hiển thị
trong Review Queue.

Nghĩa là TASK-110 không "hiển thị lại" một thứ đã có, mà phải **đưa logic đó
vào luồng production lần đầu tiên**, đồng thời không làm lệch một artifact
bằng chứng đã ship của TASK-108A-1 (CHECK-108A1-15). Gate đã ràng buộc bằng
ba check: **CHECK-110-12** (F2 trong `ImportResult.review_queue`),
**CHECK-110-13** (F4 + không được raise), **CHECK-110-14**
(`reconcile_conversion.py` giữ nguyên hành vi).

### Chấm điểm lại

Difficulty **2 → 3**, Risk **2 → 3**, Blast Radius giữ **2**. Risk 3 kéo theo
**E1 bắt buộc** cho mọi check REQUIRED (`governance/core/EVIDENCE_STANDARD.md`). Lý do nâng
Risk: TD-001 là rủi ro tiền lương, không phải rủi ro hiển thị.

## Subtask Đã Hoàn Thành (Subtasks Completed)
- [x] Đồng bộ nhánh, xác nhận `c7a1b24` = origin default
- [x] Đọc `PROJECT/PROJECT_PROGRESS.md`, `PROJECT/LO_TRINH_DE_HIEU.md`, ADR-101…106, DEC-101…127, handoff S014
- [x] Trích và đọc nguyên văn §18 từ `docs/spec/*.docx`
- [x] Xác định dependency (5 DONE, 1 miễn trừ tường minh: TASK-103)
- [x] Gate / Readiness Review — Ready Gate 16/17
- [x] Kiểm tra TD-001 — tìm ra khoảng cách `tools/` ↔ production
- [x] STOP và hỏi 4 business rule; ghi DEC-128
- [x] Soạn `docs/tasks/TASK-110-validation-review-queue.md` (17 REQUIRED + 1 RECOMMENDED)

## Subtask Còn Lại (Subtasks Remaining)
- [ ] **Chủ dự án freeze Completion Gate** → TASK-110 chuyển READY
- [ ] 110.1 → 110.10 (toàn bộ triển khai)

## Tóm Tắt Completion Gate (Completion Gate Summary)

Required:
17

PASS:
0

FAIL:
0

BLOCKED:
1 (CHECK-110-16)

NOT_TESTED:
16

## Evidence Xác Minh (Verification Evidence)

Phiên này không đóng check nào của TASK-110 — nó *soạn ra* các check đó. Bằng
chứng dưới đây là bằng chứng của chính phiên Gate Review.

| Hạng mục | Status | Evidence Level | Evidence | Executed By | Timestamp |
|---|---|---|---|---|---|
| Đồng bộ nhánh | PASS | E1 | `git rev-list --left-right --count HEAD...origin/claude/extract-upload-repo-gq2ws4` → `0 0` | Claude | 2026-08-23 |
| Baseline test | PASS | E1 | `python3 -m pytest tests/ -q` → **151 passed in 1.40s** tại `c7a1b24` | Claude | 2026-08-23 |
| Validator governance | PASS | E1 | `validate_structure.py` PASS (21 path), `validate_project_state.py` PASS, `validate_evidence.py` PASS (67 record), `validate_task_completion.py` PASS (6 task DONE) | Claude | 2026-08-23 |
| §18 đặc tả đọc nguyên văn | PASS | E1 | Trích từ `word/document.xml` của `Dac_ta_cong_cu_bao_cao_kinh_doanh.docx`, dòng 320–333 | Claude | 2026-08-23 |
| F-02 (100% dòng Pending) | PASS | E1 | `PendingPriceProvider.lookup()` trả `None` vô điều kiện | Claude | 2026-08-23 |
| F-03 (`accounting_profit is None`) | PASS | E1 | `compute_accounting_profit()` trả `None` khi `accounting_purchase_price is None` | Claude | 2026-08-23 |
| F-03b (1.261 dòng phụ) | PASS | E1 | `evidence.json` → 30 loại, tổng 1.261 dòng | Claude | 2026-08-23 |
| F-05 (lấy dòng đầu tiên) | PASS | E1 | `order_builder.py` — `first = order_lines[0]` | Claude | 2026-08-23 |
| TD-001 (F2/F4 ngoài production) | PASS | E1 | `grep` — F2/F4 chỉ xuất hiện trong `tools/analysis/reconcile_conversion.py`, không có trong `app/` | Claude | 2026-08-23 |

## File Đã Thay Đổi (Files Changed)

Created:
- `docs/tasks/TASK-110-validation-review-queue.md`
- `docs/sessions/S015-task-110-gate-readiness.md` (file này)

Modified:
- `PROJECT/PROJECT_DECISIONS.md` — **DEC-128**
- `PROJECT/PROJECT_PROGRESS.md` — Trạng thái Task hiện tại, Last Updated,
  Next Recommended Task, bullet roadmap TASK-110, bảng chấm điểm (D2/R2 → D3/R3),
  TD-001 nay trỏ tới CHECK-110-12/13/14
- `PROJECT/LO_TRINH_DE_HIEU.md` — mục "Có gì mới" cho bước 14, dòng 14 của bảng
  lộ trình (cập nhật cùng một lần sửa, theo Giao thức Đóng Phiên)

Deleted:
- Không có.

**Không đụng vào `app/`, `config/`, `tests/`, `tools/`.** Không có dòng code
ứng dụng nào trong phiên này.

## Quyết Định Chính (Key Decisions)
- **DEC-128** — 4 quyết định nghiệp vụ đóng khoảng trống §18.
- Nâng Risk 2 → 3, kéo theo E1 bắt buộc cho mọi check REQUIRED.
- Phạm vi thật là **7 loại cảnh báo**, không phải 5 như roadmap ghi.
- TASK-103 được **miễn trừ tường minh** làm dependency, kèm biện pháp thay thế
  và ghi rõ nó vẫn phải làm.

## Rủi Ro / Vướng Mắc (Risks / Blockers)

**BLOCKER cho DONE (không chặn IMPLEMENTED) — CHECK-110-16.** File thô thật
không có trong repo (`.gitignore` loại `*.xlsx` và `data/samples/`, đúng
`governance/product/17_DATA_GOVERNANCE_PRIVACY.md`) và không có trong container
của session này. Đối chiếu số phát hiện từng loại với các con số đã đo
(2 / 52 / 1.912 / 1.261 / 11.765) **chỉ chạy được ở môi trường có file thật**.
Cùng loại điều kiện đã áp cho CHECK-101-08 và CHECK-108A1-14/15.

**RỦI RO TỒN DƯ đã chấp nhận (DEC-128 §4).** Cho tới khi có người duyệt hàng
chờ, một đơn có hai nhân viên vẫn xuất ra con số sai KPI cho cả hai người.
TASK-110 làm nó **nhìn thấy được**, không làm nó **không xảy ra**. Nên đo quy
mô thật ở GATE-01.

**PHỤ THUỘC MỀM tạo ra bởi DEC-128 §3.** Danh sách từ khóa dòng phụ trong
`config/validation.yaml` và bảng Classification của §17 (TASK-103) sẽ nói về
cùng một tập dòng. Nếu lệch nhau, hai chỗ sẽ nói hai điều khác nhau. TASK-103
phải kiểm tra lại danh sách này.

**Ghi chú môi trường.** `pytest`, `openpyxl`, `PyYAML` **không** có sẵn trong
container; phải `pip install` trước khi đo baseline. Session sau nên làm bước
này đầu tiên, trước khi kết luận bất cứ điều gì về trạng thái test.

## Hạng Mục Regression (Regression Items)
- Không có thay đổi mã nguồn → không có bề mặt regression.
- Baseline ghi lại để session sau đối chiếu: **151/151 PASS** tại `c7a1b24`.
- `validate_reference_integrity.py` còn **3 reference chưa phân giải**, tất cả
  thuộc `docs/tasks/TASK-REM-T06-repository-root-hygiene.md` (Track B) — đó là
  forward reference tới ba file ở repository root mà chính task đó sẽ tạo, nên
  chúng chưa tồn tại. **Không phải do phiên này**: mọi reference do phiên này
  sinh ra đã được sửa về đường dẫn đầy đủ và phân giải được.

## Chưa Được Thay Đổi (Do Not Change Yet)
- Toàn bộ `app/`, `config/`, `tests/`, `tools/` — chờ freeze Completion Gate.
- `app/modules/domain/models.py` — TASK-110 **không được** thêm field.
- `app/modules/orders/order_builder.py` — DEC-128 §4 giữ nguyên hành vi.
- `docs/adr/ADR-101…106`.
- Bất kỳ file nào của Track B.

## Session Tiếp Theo Được Khuyến Nghị (Next Recommended Session)

**S016 — triển khai TASK-110**, chỉ sau khi chủ dự án freeze Completion Gate.
Thứ tự: 110.1 → 110.10. Làm 110.8 (TD-001) **sớm**, không để cuối — nó là phần
duy nhất phải chạm vào một artifact bằng chứng đã ship.

Trước khi code: `pip install pytest openpyxl PyYAML` và xác nhận lại 151/151.

**TASK-108B vẫn BLOCKED** — C15 (`EligibleCosts`) chưa có định nghĩa nghiệp
vụ. **TASK-109 bị chặn một phần** — cột "DS quy đổi"/"LN KPI" cần 108B.

## Ghi Chú Về Quy Trình (Process Note)

§18 đặc tả là **một bảng hai cột** — đủ để biết cần làm gì, không đủ để biết
làm thế nào cho đúng. Nếu code thẳng từ bảng đó, kết quả sẽ là một Review Queue
11.765 mục "thiếu giá nhập" cộng hàng nghìn mục "vận chuyển SL = 0" — đúng về
mặt chữ nghĩa, vô dụng về mặt vận hành, và cảnh báo thật sẽ chết chìm trong đó.

Bốn câu hỏi mất một lượt hội thoại. Phát hiện ra chúng sau khi đã code sẽ mất
một vòng viết lại — đúng bài học mà TASK-108A-1 đã trả giá qua 4 vòng
independent review.

## File Agent Tiếp Theo Cần Đọc (Files Next Agent Should Read)
- `CLAUDE.md`
- `PROJECT/PROJECT_PROGRESS.md` (mục "Trạng thái Task hiện tại", "Nợ Kỹ Thuật")
- `docs/tasks/TASK-110-validation-review-queue.md`
- `PROJECT/PROJECT_DECISIONS.md` (**DEC-128**, và DEC-103, DEC-110, DEC-113, DEC-127)
- `docs/analysis/01_DATA_MAPPING.md` §3 (vì sao không dùng `Lợi nhuận` của ERP)
- `tools/analysis/reconcile_conversion.py` (tiêu chí F1–F5)
- `app/pipeline.py`, `app/modules/domain/models.py`
