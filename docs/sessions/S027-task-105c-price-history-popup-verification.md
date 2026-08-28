# BÀN GIAO SESSION (SESSION HANDOFF)

Session ID:
S027

Task:
`TASK-105C` — Price History Chart / Min Replay Verification (tiếp theo
`S024`–`S026`, `DEC-147`–`DEC-149`)

Task Mode:
SPIKE / EXPLORATORY (discovery, không implementation)

Project Profile:
PRODUCT

Status:
DISCOVERY COMPLETE — không sửa `app/**`, không sửa repo giá.

## Metadata

Ngày:
2026-08-27

Repo A — Reports:
`7cf2960` (branch `claude/reports-price-rtdb-audit-bg5y4t`)

Repo B — hệ thống giá / RTDB:
`hoangvinhkta-creator/Tracking` @ `d177363a390d36fe793e0c1c44a6fb6743ca45f5`
(không đổi so với các phiên trước; **0 file thay đổi** trong phiên này)

## Kết Quả (Result)

Chủ dự án cung cấp bằng chứng UI mới: popup "Lịch sử giá — <MÃ>" trên tab
Bảng giá, hỏi cần xác minh chính xác popup này hiển thị gì trước khi chốt
kiến trúc history. Đã audit trực tiếp `openPhist()`/`loadPhist()`/
`renderPhist()`/`phShow()`.

**Kết luận chính, xác nhận bằng code, không suy luận từ UI:**

```
Popup = OPTION A: raw vendor-price history từ `phist`, MỘT ĐƯỜNG MỖI NCC.
KHÔNG có bất kỳ tính toán Min nào trong toàn bộ đường đi của popup.
KHÔNG đọc `tp.ton`/`inv.cong` ở bất kỳ đâu trong popup.
KHÔNG có persistent Min history record nào tồn tại trong repo B.
```

Điểm gây nhầm lẫn có thể giải thích được: nút mở popup gắn **trên chính ô
Min** của bảng (`public/index.html:6143`, tooltip *"bấm xem biểu đồ lịch sử
giá"*) — khiến việc bấm vào Min trông như "xem lịch sử của Min", nhưng code
xác nhận nó mở đúng `phist/<mã>` (dữ liệu NCC thô), không liên quan gì tới
công thức Min. Đây là một khoảng cách UI-affordance-vs-data-thật đáng ghi
lại, không phải một lỗi cần sửa trong phiên này.

Không có Owner Decision mới trong phiên này — chỉ ghi audit fact, đúng yêu
cầu đề bài.

## Subtask Đã Hoàn Thành (Subtasks Completed)

- Định vị chính xác function mở popup, load data, dựng chart — trích
  file/function/line.
- Kết luận popup hiển thị gì (A/B/C/D/E) bằng bằng chứng code.
- Xác nhận KHÔNG có persistent RTDB record nào của historical Min.
- Xác nhận popup KHÔNG tái tính Min cho bất kỳ ngày lịch sử nào.
- Xác nhận popup KHÔNG đọc `inv.cong`/`tp.ton`.
- Chạy lại Historical Min Replay Experiment thuần code (không cần dữ liệu
  sống) — xác nhận cần current-state input, không deterministic.
- Xác minh step-function semantics của chart khớp đúng chú thích UI.
- Trả lời lại câu hỏi 30 ngày, phân loại YES/PARTIAL/NO.
- Định lượng kiến trúc tối thiểu còn thiếu nếu PARTIAL.
- Xác nhận popup không dùng cả `minCuaDong()` lẫn `soCotTinh()` — không tính
  Min nên câu hỏi client/server không áp dụng cho chính popup, nhưng vẫn áp
  dụng cho bất kỳ replay engine nào được xây sau này.

## Subtask Còn Lại (Subtasks Remaining)

- Không đổi so với `DEC-149`: `CONFLICT DETECTED` §71 (Min ưu tiên vs cong
  hoà tan) vẫn cần chủ dự án xác nhận trước khi chọn kiến trúc capture.
- Phiên này **củng cố thêm** lý do không thể trì hoãn: popup hiện tại không
  hề là một giải pháp thay thế cho việc capture — nó không tính, không lưu,
  không tái dựng được Min ở bất kỳ mức nào.

## Tóm Tắt Completion Gate (Completion Gate Summary)

Không áp Completion Gate — SPIKE discovery.

Required:
Trả lời 21 mục của đề bài bằng bằng chứng code; không đưa ra Owner Decision
mới ngoài ghi nhận fact.

PASS:
Đạt (bằng chứng E1 dưới đây).

NOT_TESTED:
Dữ liệu sống trong RTDB — phiên này audit code, không có credential đọc
instance.

## Evidence Xác Minh (Verification Evidence)

| Check ID | Status | Evidence Level | Evidence | Executed By | Timestamp |
|---|---|---|---|---|---|
| P-01 mở popup | PASS | E1 | `openPhist(key)` `public/index.html:6218-6238` — gọi từ `data-viec="openPhist"` gắn ở ô Min (`:6143`) và bảng đăng ký lệnh UI (`:1931`) | S027 | 2026-08-27 |
| P-02 load data | PASS | E1 | `loadPhist(key)` `:4661-4664` — `db.ref("phist/"+key).once("value")`, trả nguyên `{<NCC>:{<ngày>:giá}}` | S027 | 2026-08-27 |
| P-03 RTDB path | PASS | E1 | `phist/<MÃ>` — đúng một lượt đọc, không lọc, không transform tại tầng đọc | S027 | 2026-08-27 |
| P-04 dựng series | PASS | E1 | `renderPhist(row, data)` `:6243-6314` — `sups = Object.keys(data)` (mỗi NCC một `line`), KHÔNG có bước lọc theo `_ANC`/`NCC_MIN_LOAI`/`NGUONG_BAT_THUONG` nào | S027 | 2026-08-27 |
| P-05 hover card | PASS | E1 | `phShow(td,key,ncc,data)` `:6191-6217` — hiện MỘT NCC (`data[ncc]`) mỗi lần, cùng nguồn `phist`, không tính Min | S027 | 2026-08-27 |
| C-01 popup = option nào | PASS | E1 | **A — raw vendor-price history**. `grep` trong khối `:6218-6314`: 0 tham chiếu `tp.`, `inv.`, `cong`, `.ton` (lệnh grep chạy trực tiếp, 0 kết quả) | S027 | 2026-08-27 |
| M-01 persistent Min history | PASS | E1 | `grep -rniE "minhist|min_hist|history.?min|giaMin|marketmin"` toàn repo B = **0 kết quả liên quan lưu trữ** (chỉ khớp biến `min`/`giá min` trong ngữ cảnh HIỂN THỊ hiện hành, `:4216,6098,6143,8616,8619`) | S027 | 2026-08-27 |
| R-01 popup không reconstruct Min | PASS | E1 | Không hàm nào trong `:6218-6314` gọi `minCuaDong`/`soCotTinh`/`locGiaNcc`/`hetHangHoanToan`. `grep` xác nhận không match | S027 | 2026-08-27 |
| R-02 popup không đọc `inv.cong` | PASS | E1 | Đã grep trực tiếp khối code — 0 hit `tp.`/`inv.`/`cong`/`.ton` | S027 | 2026-08-27 |
| S-01 step-function semantics | PASS | E1 | `renderPhist()` `:6259-6267` — vòng lặp `days.forEach`: `last` giữ giá trị gần nhất khi gặp `data[n][d] !== undefined`, "giữ nguyên" khi ngày đó không có record — khớp CHÍNH XÁC chú thích UI `:6314` | S027 | 2026-08-27 |
| S-02 bảng số KHÔNG carry-forward | PASS | E1 | `rows` `:6296-6303` — ô không có record hiện "·" (KHÔNG điền giá trị gần nhất), khác hẳn chart. Hai chế độ hiển thị CÙNG dữ liệu nhưng KHÁC hành vi — cần phân biệt khi mô tả "step-function" cho đúng phạm vi (chart, không phải bảng) | S027 | 2026-08-27 |
| X-01 replay cần current-state | PASS | E1 (suy luận thuần code, không có dữ liệu sống) | Không hàm nào trong repo B nhận `(ngày lịch sử, dữ liệu phist tới ngày đó)` làm input và trả về Min. `minCuaDong()` (`price-engine/src/nghiepvu.js:632-637`) là hàm THUẦN nhưng CHỈ được gọi trong pipeline hiện tại với `dong` = trạng thái board HIỆN TẠI (`gotDong()` `:3551-3556`); `an` luôn = `_ANC` hiện tại (`:3499-3508`); `NGUONG_BAT_THUONG` là hằng số một giá trị | S027 | 2026-08-27 |

## Giới hạn của bằng chứng

- Không đọc RTDB sống — không xác nhận được dữ liệu `phist` thật của các mã
  Owner nêu (Tuyền Dũng/Tân Thủy, mốc 09/08, 10/08, 25/08) khớp với ví dụ
  đưa ra; chỉ xác nhận CƠ CHẾ đọc/dựng chart đúng như mô tả.
- §6 (Historical Min Replay Experiment) là suy luận THUẦN CODE theo đúng yêu
  cầu đề bài ("CODE ONLY") — không chạy thử trên một mã thật.

## File Đã Thay Đổi (Files Changed)

Created:
- `docs/sessions/S027-task-105c-price-history-popup-verification.md` (file
  này)

Modified:
- `PROJECT/PROJECT_DECISIONS.md` — `DEC-150` (audit fact, không phải Owner
  Decision mới)
- `PROJECT/PROJECT_PROGRESS.md` — ghi rõ popup là vendor-only, không thay
  đổi verdict `CONFLICT DETECTED` của `DEC-149`
- `docs/tasks/TASK-108B-eligible-costs-owner-definition.md` — Phần IX

Deleted:
- (không)

Repo B (`Tracking`):
- **0 file**.

## Quyết Định Chính (Key Decisions)

- `DEC-150` — ghi nhận audit fact về popup "Lịch sử giá": vendor-only, không
  phải Min history, không reconstruct được Min. Không phải Owner Decision
  mới — không thay đổi bất kỳ trạng thái BLOCKED/READY nào đã có.

## Rủi Ro / Vướng Mắc (Risks / Blockers)

- Không đổi so với `DEC-149`. Phiên này chỉ loại bỏ MỘT khả năng nhầm lẫn cụ
  thể: không ai được coi popup "Lịch sử giá" hiện có là bằng chứng rằng hệ
  thống đã capture được lịch sử Min — nó chưa, và không có cơ chế nào âm
  thầm làm việc đó.
