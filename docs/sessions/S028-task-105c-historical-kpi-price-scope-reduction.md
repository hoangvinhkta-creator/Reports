# BÀN GIAO SESSION (SESSION HANDOFF)

Session ID:
S028

Task:
`TASK-105C` — Owner Decision: Historical KPI Purchase Price Scope Reduction
(tiếp theo `S024`–`S027`, `DEC-147`–`DEC-150`)

Task Mode:
MICRO (ghi nhận Owner Decision + audit hẹp một câu hỏi, không implementation)

Project Profile:
PRODUCT

Status:
DECISION RECORDED. Không implementation. Không sửa repo giá.

## Metadata

Ngày:
2026-08-27

Repo A — Reports:
Bắt đầu `1908d00f3b578953d68dbcefa80dfd0a816cb000`
Kết thúc: xem commit cuối phiên, cùng branch
`claude/reports-price-rtdb-audit-bg5y4t`

Repo B — hệ thống giá / RTDB:
`hoangvinhkta-creator/Tracking` @ `d177363a390d36fe793e0c1c44a6fb6743ca45f5`
(không đổi; **0 file thay đổi**)

## Kết Quả (Result)

Chủ dự án chốt: Reports **KHÔNG** cố tái dựng chính xác `_c.min` lịch sử.
Thay vào đó, xây `HistoricalKpiPurchasePrice` từ **duy nhất** nguồn có bằng
chứng lịch sử thật — `phist/<mã>/<NCC>/<ngày>` — với semantics
`Price(NCC,D) = record gần nhất ≤ D`, lấy MIN qua các NCC có căn cứ tại D.
`inv.cong` **loại khỏi scope hiện tại** (không có lịch sử, không bắt buộc
xây). Mã không đủ căn cứ lịch sử → `Pending`, cho xử lý tay sau, có
provenance, không rewrite `phist`.

Điều này **giải quyết `CONFLICT DETECTED` (DEC-149 §71)** — không phải bằng
cách chọn (A) hay (B) như hai lựa chọn DEC-149 đưa ra, mà bằng cách **đổi
scope**: Reports không cần trả lời "ý định thật của `_c.min`" nữa, vì nó
không dùng `_c.min` làm nguồn nữa.

**Audit hẹp thực hiện trong phiên (yêu cầu đề bài mục "OUTLIER/NCC
FILTERING"):** `phist` có đủ dữ liệu để dựng `HistoricalVendorPrice`
deterministic đúng NHƯ SEMANTICS ĐÃ CHỐT (min qua mọi NCC có ghi nhận,
không lọc) — nhưng còn **hai câu hỏi filtering chưa đóng**, không tự suy ra:
(1) NCC đã "retired"/"loại khỏi Min" ngày hôm nay có nên bị loại khỏi
`HistoricalVendorPrice` cho những ngày TRƯỚC KHI trạng thái đó có hiệu lực
không; (2) bộ lọc giá bất thường (`NGUONG_BAT_THUONG`, thêm 24/08/2026) có
nên áp dụng hồi tố cho các mốc TRƯỚC ngày đó không. Ghi rõ ở `DEC-151`, đưa
vào `PROJECT/PROJECT_PROGRESS.md`.

## Subtask Đã Hoàn Thành (Subtasks Completed)

- Ghi nhận Owner Decision đầy đủ, cấp `DEC-151`.
- Đóng `CONFLICT DETECTED` `DEC-149` §71 bằng con trỏ superseded (không
  rewrite).
- Audit `phist` cho khả năng xây `HistoricalVendorPrice` không cần giả định
  config hiện tại = config lịch sử — xác định PARTIAL, nêu đúng hai câu hỏi
  còn mở, không tự trả lời.
- Đánh giá lại `TASK-105B`/`TASK-105C`/`TASK-108B` theo scope mới.
- Xác nhận capture-layer/MarketMinHistory/inv.cong-history KHÔNG còn bắt
  buộc trong Phase 1.
- Đề xuất `HistoricalVendorPriceProvider` thay `RTDBPriceProvider` làm tên
  abstraction — ghi nhận, không implement.
- Cập nhật `PROJECT/PROJECT_PROGRESS.md`, `PROJECT/LO_TRINH_DE_HIEU.md`,
  `PROJECT/REVIEW_BUDGET_LEDGER.md`,
  `docs/tasks/TASK-108B-eligible-costs-owner-definition.md` Phần X.

## Subtask Còn Lại (Subtasks Remaining)

- Chủ dự án trả lời hai câu hỏi filtering còn mở (đóng ở trên).
- Sau đó: mở `TASK-105C` implementation với
  `docs/tasks/TASK-105C-*.md` (Scope Lock + Completion Gate).
- Thiết kế seam cho manual Pending resolution (câu hỏi mở, xem DEC-151 §13).

## Tóm Tắt Completion Gate (Completion Gate Summary)

Không áp Completion Gate — MICRO, ghi nhận quyết định + audit hẹp.

Required:
Ghi Owner Decision đầy đủ; audit đúng một câu hỏi phist-sufficiency; không
tự suy ra business rule filtering; cập nhật toàn bộ tiến độ trước khi kết
thúc phiên.

PASS:
Đạt — xem Evidence bên dưới và trạng thái cuối phiên của
`PROJECT/PROJECT_PROGRESS.md`/`PROJECT/LO_TRINH_DE_HIEU.md`.

## Evidence Xác Minh (Verification Evidence)

| Check ID | Status | Evidence Level | Evidence | Executed By | Timestamp |
|---|---|---|---|---|---|
| V-01 phist ghi bất kể exclusion | PASS | E1 | `buildSync()` `public/index.html:5100-5203` — vòng lặp `feeds.forEach` xử lý MỌI tab NCC đã dán, không kiểm tra `NCC_RETIRED`/`NCC_MIN_LOAI` trước khi ghi `ph[...]` (`:5171,5192`) — hai danh sách đó chỉ ảnh hưởng `_c.min`, không ảnh hưởng việc phist có ghi hay không | S028 | 2026-08-27 |
| V-02 phist key đã fold qua nccKey tại thời điểm ghi | PASS | E1 | `buildSync()` `:5119` — `const ncc = nccKey(st.name)` — MỌI write `ph[key+"/"+ncc+...]` dùng biến đã fold; `editPrice()` `:6363` nhận `ncc` từ cột board (đã fold khi thêm vào `BMETA.ncc`) | S028 | 2026-08-27 |
| V-03 `NCC_ALIAS` là hằng số đơn, không versioned | PASS | E1 | `const NCC_ALIAS = [["NCC 179", "Điện tử 179"]];` `:1860` — một mảng cứng trong mã nguồn, cùng loại với `NCC_RETIRED`/`NCC_MIN_LOAI`/`NGUONG_BAT_THUONG` đã xác nhận ở `DEC-149` | S028 | 2026-08-27 |
| V-04 hệ quả: alias thêm sau không hồi tố | PASS | E1 (suy luận từ V-02+V-03) | Nếu một cặp alias được thêm vào `NCC_ALIAS` SAU KHI đã có `phist` ghi dưới tên thô cũ, các bản ghi cũ đó VẪN nằm dưới khoá cũ vĩnh viễn — không cơ chế migrate nào trong repo B (`grep` không thấy hàm nào duyệt lại `phist` khi `NCC_ALIAS` đổi) | S028 | 2026-08-27 |

## File Đã Thay Đổi (Files Changed)

Created:
- `docs/sessions/S028-task-105c-historical-kpi-price-scope-reduction.md`

Modified:
- `PROJECT/PROJECT_DECISIONS.md` — `DEC-151`
- `PROJECT/PROJECT_PROGRESS.md` — đóng blocker cũ, mở blocker mới (đúng 2
  câu hỏi filtering), gỡ yêu cầu capture-layer/MarketMinHistory/inv.cong-
  history khỏi Phase 1
- `PROJECT/LO_TRINH_DE_HIEU.md` — cập nhật bước 11b theo scope mới
- `PROJECT/REVIEW_BUDGET_LEDGER.md` — ghi nhận Owner Decision làm giảm
  scope kiến trúc lineage `TASK-105B`/`TASK-105C`
- `docs/tasks/TASK-108B-eligible-costs-owner-definition.md` — Phần X

Deleted:
- (không)

Repo B (`Tracking`):
- **0 file**.

## Quyết Định Chính (Key Decisions)

- `DEC-151` — Owner Decision: Historical KPI Purchase Price Scope Reduction.
  Đóng `DEC-149` §71 bằng scope reduction (không phải bằng chọn A/B).

## Rủi Ro / Vướng Mắc (Risks / Blockers)

- Hai câu hỏi filtering (NCC retired/MIN_LOAI hồi tố, outlier threshold hồi
  tố) — không blocking cho việc MỞ `TASK-105C` implementation (Owner đã nói
  rõ Pending là hành vi chủ đích, chấp nhận tần suất thấp), nhưng ảnh hưởng
  ĐỘ CHÍNH XÁC của kết quả không-Pending nếu để mặc định sai. Khuyến nghị:
  mặc định AN TOÀN (không lọc gì, đúng y văn bản Owner §3/§4) cho tới khi có
  câu trả lời, ghi rõ giả định này trong provenance của mọi record.
- `NCC_ALIAS` không hồi tố (V-04) — rủi ro thấp (danh sách hiếm khi đổi,
  hiện chỉ 1 cặp) nhưng đáng ghi lại làm HARDENING cho `TASK-105C`
  implementation sau này: nếu alias mới được thêm, cần một bước migrate
  `phist` đi kèm, không thì HistoricalVendorPrice sẽ bỏ sót giá của "tên cũ".
