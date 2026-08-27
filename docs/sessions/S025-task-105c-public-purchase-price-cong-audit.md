# BÀN GIAO SESSION (SESSION HANDOFF)

Session ID:
S025

Task:
`TASK-105C` — Public Purchase Price History Check (`inv.cong` deep-dive, tiếp
theo `S024`/`DEC-147`)

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
`1ca0902` (branch `claude/reports-price-rtdb-audit-bg5y4t`)

Repo B — hệ thống giá / RTDB:
`hoangvinhkta-creator/Tracking` @ `d177363a390d36fe793e0c1c44a6fb6743ca45f5`
(không đổi so với `S024`; **0 file thay đổi** trong phiên này)

## Kết Quả (Result)

Chủ dự án chỉ định `inv.cong` (giá nhập **công khai**) làm
`AccountingPurchasePrice`, thay vì `inv.gia` (giá thực nhập trung bình,
private). Phiên này audit đầy đủ write/read/lifecycle của `inv.cong` bằng
bằng chứng code — xem `DEC-148`.

Kết luận trọng yếu, khác với kỳ vọng ngầm định của đề bài: **`inv.cong` không
có lịch sử, và không có bất kỳ đảm bảo giữ dữ liệu nào theo thời gian.**
Trường hợp tệ nhất là ghi đè **tức thời** (sửa tay hoặc tải lại file trong
ngày); trường hợp tốt hơn (`qua ngày mới`) chỉ giữ đúng một bước, và bước đó
phụ thuộc một **thao tác tay không theo lịch**, không phải đảm bảo hệ thống.
⇒ **NO GUARANTEED DELAY WINDOW.**

Xác nhận bốn semantics chủ dự án đề xuất — **cả bốn khớp với bằng chứng code**
(chi tiết ở `DEC-148` §61):

```
AccountingPurchasePrice = inv.cong        ✅ khớp — cong là bản DUY NHẤT
                                              rời khỏi `inv` để vào board/Reports
inv.gia  = PRIVATE / OUT OF REPORTS SCOPE ✅ khớp — 0 read site nào đưa `gia`
                                              ra ngoài nhánh `inv`
inv.lo   = LOT PRICE / NOT USED BY DEFAULT ✅ khớp — `lo` chỉ là input tính
                                              `gia`, không tự nó đi đâu khác
phist    = VENDOR QUOTED / NOT ACCOUNTING PURCHASE PRICE
                                           ✅ khớp — xác nhận lại DEC-147 §55
```

## Subtask Đã Hoàn Thành (Subtasks Completed)

- Liệt kê đầy đủ **mọi** write site của `inv.<slot>.cong` (5 chỗ, 4 hàm).
- Liệt kê đầy đủ **mọi** read site của `inv.<slot>.cong` (2 chỗ thật sự đưa
  dữ liệu ra khỏi biến cục bộ: UI render, và ghi sang `board/<mã>/tp/ton`).
- Xác định chính xác semantics của `cong`.
- Trả lời overwrite/append/previous-value cho `cong`.
- Xác nhận **không có** namespace lịch sử riêng cho `cong`.
- Kiểm tra `backup`/`hist`/`phist` có tái dựng được `cong` theo ngày không.
- Chạy lại đúng kịch bản "giá D=X, đổi thành Y, hỏi lại sau 30 ngày" cho
  riêng `cong`.
- Trả lời câu hỏi cửa sổ đảm bảo — bằng bằng chứng, không đoán số ngày.
- Đánh giá reuse `phist` vs namespace riêng.
- Đề xuất schema tối thiểu `PublicPurchasePriceHistory` (không implementation).

## Subtask Còn Lại (Subtasks Remaining)

- Chủ dự án quyết định có xây tầng capture cho `inv.cong` hay không, và tần
  suất — câu hỏi này giờ **cấp thiết hơn** DEC-147 đã nêu, vì window thực tế
  là 0, không phải "ngắn nhưng có".
- Sau khi có quyết định: mở `TASK-105C` implementation với
  `docs/tasks/TASK-105C-*.md`.

## Tóm Tắt Completion Gate (Completion Gate Summary)

Không áp Completion Gate — SPIKE discovery.

Required:
Trả lời 10 câu hỏi của đề bài bằng bằng chứng code; xác nhận/phản bác 4
semantics đề xuất.

PASS:
Cả hai (bằng chứng E1 dưới đây).

BLOCKED:
Quyết định xây capture layer — cần chủ dự án (không đổi so với `DEC-147`,
nhưng nay có thêm một finding mới: `NO GUARANTEED DELAY WINDOW`).

NOT_TESTED:
Dữ liệu sống trong RTDB (giá trị `cong` thật hiện tại, tần suất thực tế click
"qua ngày mới"). Phiên này audit code, không có credential đọc instance.

## Evidence Xác Minh (Verification Evidence)

| Check ID | Status | Evidence Level | Evidence | Executed By | Timestamp |
|---|---|---|---|---|---|
| P-01 write: migration bootstrap | PASS | E1 | `public/index.html:6789` — `s.cong = Object.assign({}, s.gia \|\| {})`, chạy một lần khi nâng cấp dữ liệu cũ lên `giaV3` | S025 | 2026-08-27 |
| P-02 write: day-rollover / file reload | PASS | E1 | `invApply()` `:6961-6966` — giữ giá trị sửa tay ngày trước (`sameTay`/`prevCon`) nếu có, không thì `cong[k] = gia[k]` | S025 | 2026-08-27 |
| P-03 write: auto-recompute | PASS | E1 | `invRecalcAvg()` `:7099-7102` — mỗi lần `lo` (giá lô) đổi, nếu **chưa** khoá tay (`!s.congTay[k]`) thì `cong[k] = gia[k]` | S025 | 2026-08-27 |
| P-04 write: sửa tay trực tiếp | PASS | E1 | `invSetGia()` `:7117-7120`, `kind === "cong"` — set `congTay[k]=true` rồi ghi thẳng `s.cong[k] = n`; debounce 800ms rồi `saveInv()` `:7133` | S025 | 2026-08-27 |
| P-05 write: xoá khi hết hàng | PASS | E1 | `invRecalcAvg()` `:7085-7087` — `x.q` không dương thì `delete s.cong[k]` cùng `gia`/`lo`/`congTay` | S025 | 2026-08-27 |
| Q-01 read → board | PASS | E1 | `invSyncPart()` `:7238,7250` — `u[k+"/tp/ton"] = cong[invRowKey(x)]`, chạy mỗi lượt `buildSync()`/`runSync()` (luồng "Cập nhật từ dữ liệu hôm nay") | S025 | 2026-08-27 |
| Q-02 read → UI | PASS | E1 | `renderInvT()` `:7441,7463,7473-7476` — ô nhập "Giá nhập công khai", tiêu đề cột ghi rõ *"Giá đưa sang Bảng giá để nhân viên xem và tính Min"* (`:7489`) | S025 | 2026-08-27 |
| Q-03 không read site nào khác | PASS | E1 | `grep -n "invCongOf("` = đúng 3 dòng: `:6767` (helper nội bộ `invPriceFrom`, dùng lại trong P-02/P-03), `:7238`, `:7441` — không còn nơi nào khác đọc `cong` | S025 | 2026-08-27 |
| S-01 semantics | PASS | E1 | `:6687-6690` — *"cong: giá nhập CÔNG KHAI — đẩy sang cột Tồn của Bảng giá để tính Min"*; `:6120-6134` — cột board ghi rõ *"KHOÁ không cho gõ tay ... mỗi lần Cập nhật ... invSyncPart() ghi đè toàn bộ"* | S025 | 2026-08-27 |
| S-02 `gia` không lộ ra ngoài `inv` | PASS | E1 | `invValRows()` `:7554` dùng `invGiaOf(s)` (private) cho báo cáo **định giá kho** — khác `board`/CSV. `grep "invGiaOf("` chỉ xuất hiện trong `inv*` helper, không ở `invSyncPart`/CSV export | S025 | 2026-08-27 |
| W-01 overwrite bán phần | PASS | E1 | `db.ref("inv").set(INV)` (`saveInv()` `:6834`) — ghi đè **CẢ nhánh `inv`**, không phải update từng khoá. Trong bộ nhớ, mỗi write ở P-01…P-05 **thay thế** giá trị cũ tại đúng khoá đó — không append | S025 | 2026-08-27 |
| W-02 previous value | PASS | E1 | **Không** có trường `pv`/`prev` nào cho `cong` (khác `board/<mã>/p/<NCC>` có `pv`). Giá trị cũ chỉ "sống sót" gián tiếp qua nhánh `cu` **cho tới lần `invNextDay()` kế tiếp** | S025 | 2026-08-27 |
| H-01 namespace lịch sử riêng | PASS | E1 | `grep -n "cong"` trên toàn `public/index.html`/`firebase-database.rules.json` — không nhánh RTDB nào tên `cong_hist`/`public_price_hist`/tương tự. `phist` cấu trúc `<mã>/<NCC>/<ngày>` — `cong` không có trục NCC, không khớp | S025 | 2026-08-27 |
| B-01 backup không phủ `inv` | PASS | E1 | `snapshotBoard()` `:4670-4676` — `snap = {board: ..., meta: ...}`, **không** có khoá `inv`. `firebase-database.rules.json` nhánh `backup` không liên quan `inv` | S025 | 2026-08-27 |
| B-02 backup bị prune tích cực | PASS | E1 | `BACKUP_KEEP = 10` (`:4630`); `snapshotBoard()` `:4678-4680` — `db.ref("backup/"+old).remove()` cho mọi bản cũ hơn 10 bản gần nhất, chạy **ngay sau mỗi lần snapshot** | S025 | 2026-08-27 |
| B-03 hist không mang giá trị | PASS | E1 | `logHist()`/`logHistAs()` `:9599-9636` — chuỗi mô tả tự do (`"Tồn kho: qua ngày mới..."`), không trường số; tối đa 100 dòng, `db.ref("hist").set()` đè cả nhánh | S025 | 2026-08-27 |
| R-01 rollover phá dữ liệu cũ | PASS | E1 | `invNextDay()` `:7019-7034` — `INV.cu = moi; INV.moi = null;` **thay thế toàn bộ `cu` cũ**, chỉ giữ một bước undo `_invUndo` **trong bộ nhớ JS, không persist** — mất khi tải lại trang/đóng phiên | S025 | 2026-08-27 |
| R-02 không có lịch enforce | PASS | E1 | `invNextDay()` là **hàm gọi từ nút bấm** (`invPickFile`/UI), không nằm trong `scheduled()` (`src/index.js:830-840` — hai cron chỉ đẩy CRM/Sheet, không rotate `inv`). Không cơ chế nào bắt buộc gọi đúng 1 lần/ngày | S025 | 2026-08-27 |
| R-03 overwrite trong ngày là tức thời | PASS | E1 | `invSetGia()` (P-04) ghi `s.cong[k]=n` **ngay lập tức** trong bộ nhớ (debounce chỉ trễ *lượt gọi `saveInv()`*, không trễ *thời điểm giá trị cũ biến mất* — biến `s.cong[k]` bị gán đè ngay khi hàm chạy) | S025 | 2026-08-27 |

## Giới hạn của bằng chứng

- Không đọc RTDB sống — mọi kết luận là mức E1 (đọc code), không phải quan sát
  dữ liệu thật.
- Tần suất thực tế người vận hành bấm "qua ngày mới" **không** xác định được
  từ repo — đây là hành vi con người, không phải cấu hình.

## File Đã Thay Đổi (Files Changed)

Created:
- `docs/sessions/S025-task-105c-public-purchase-price-cong-audit.md` (file này)

Modified:
- `PROJECT/PROJECT_DECISIONS.md` — `DEC-148`
- `PROJECT/PROJECT_PROGRESS.md` — cập nhật trạng thái field candidate + finding
  "NO GUARANTEED DELAY WINDOW"
- `docs/tasks/TASK-108B-eligible-costs-owner-definition.md` — Phần VII

Deleted:
- (không)

Repo B (`Tracking`):
- **0 file**.

## Quyết Định Chính (Key Decisions)

- `DEC-148` — audit `inv.cong`, xác nhận 4 semantics của chủ dự án, kết luận
  `NO GUARANTEED DELAY WINDOW`, đề xuất schema `PublicPurchasePriceHistory`.

## Rủi Ro / Vướng Mắc (Risks / Blockers)

- **Rủi ro cao nhất:** nếu ai đó đọc "`AccountingPurchasePrice = inv.cong` đã
  chốt" mà bỏ qua phần "không có lịch sử", họ có thể tưởng vấn đề chỉ còn là
  nối dây kỹ thuật. Sự thật là: **chưa capture được một byte lịch sử nào của
  đúng trường vừa được chỉ định** — capture layer là điều kiện tiên quyết,
  không phải việc làm sau.
- Blocker không đổi bản chất so với `DEC-147`, nhưng độ khẩn cấp tăng: window
  thực tế = 0 trong trường hợp xấu nhất, không phải "một vài ngày".
