# BÀN GIAO SESSION (SESSION HANDOFF)

Session ID:
S026

Task:
`TASK-105C` — Market Min Price Path Audit (tiếp theo `S024`/`DEC-147`,
`S025`/`DEC-148`)

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
`d1b0b552b68d456499d2a51872125a82bdff38b2` (branch `claude/reports-price-rtdb-audit-bg5y4t`)

Repo B — hệ thống giá / RTDB:
`hoangvinhkta-creator/Tracking` @ `d177363a390d36fe793e0c1c44a6fb6743ca45f5`
(không đổi so với `S024`/`S025`; **0 file thay đổi** trong phiên này)

## Kết Quả (Result)

Chủ dự án nêu business rule mới: dùng **GIÁ MIN** (`board/<mã>/_c.min`) làm
`AccountingPurchasePrice` khi có căn cứ, chỉ fallback sang `inv.cong` khi mã
"lạ", không có căn cứ tính Min. Phiên này audit đầy đủ field, formula,
writer/reader, và lịch sử của Min — kết luận ở `DEC-149`.

**Hai phát hiện trọng yếu:**

1. **`CONFLICT DETECTED`** — quy tắc ưu tiên tuần tự Owner mô tả ("Min trước,
   `cong` chỉ khi Min bất khả") **không khớp** cách `_c.min` thực sự được
   tính. Công thức thật: `MIN = min(giá NCC rẻ nhất còn hàng đã lọc outlier,
   tp.ton)` — nghĩa là `inv.cong` (chính là `tp.ton`) **luôn** được xét và có
   thể **thắng** giá NCC bất cứ khi nào nó rẻ hơn, kể cả khi NCC vẫn còn hàng
   và Min hoàn toàn "có căn cứ". Đây không phải fallback có điều kiện — đây
   là một thành phần cạnh tranh vô điều kiện trong cùng một công thức.
2. **Historical Replay = C (chỉ current snapshot, không replay được)** —
   không phải vì thiếu MỘT input, mà vì thiếu **nhiều lớp cùng lúc**: `_c`
   không có history riêng; công thức Min không bao giờ đọc `phist` (chỉ đọc
   board hiện tại); ngay cả nếu `phist` hoàn hảo, một trong hai input chính
   của Min (`tp.ton`/`inv.cong`) đã được xác nhận **không có lịch sử** ở
   `DEC-148`; và các danh sách loại trừ NCC (`NCC_RETIRED`, `NCC_MIN_LOAI`)
   với ngưỡng lọc bất thường (`NGUONG_BAT_THUONG`) là **hằng số mã nguồn**,
   không versioned trong RTDB, không có bản ghi "hôm đó danh sách là gì".

## Subtask Đã Hoàn Thành (Subtasks Completed)

- Xác định chính xác field `_c.min` — công thức, input, writer, reader, cả
  phía client (price-engine qua service binding) lẫn phía Worker (fallback
  `soCotTinh()` cho CSV/CRM export).
- Trích nguyên văn thuật toán (INPUT/RULE/OUTPUT), không diễn giải mơ hồ.
- Chạy Historical Replay Test, phân loại đúng A/B/C/D theo yêu cầu đề bài.
- Kiểm tra khả năng tái dựng từ `phist` — xác nhận công thức sống **không
  bao giờ** đọc `phist`; và ngay cả một lượt tái dựng thủ công cũng thiếu
  nhiều input lịch sử.
- Đối chiếu business rule Owner với code hiện có — phát hiện `CONFLICT
  DETECTED`, không tự chọn cách hiểu.
- Định nghĩa `NO MARKET MIN BASIS`, phân biệt `DETERMINED_NO_BASIS` với
  `UNKNOWN`/`SOURCE_FAILURE` — phát hiện code hiện tại **gộp chung** nhiều
  trạng thái khác nhau vào cùng một tín hiệu `null`.
- Đánh giá 4 option kiến trúc lịch sử, chọn option ít thay đổi nhất mà vẫn
  đảm bảo replay 30 ngày/6 tháng đúng.
- Trả lời guaranteed delay window (1 giờ / 1 ngày / 7 ngày / 30 ngày).
- Xác minh taxonomy thuật ngữ Owner đề xuất.

## Subtask Còn Lại (Subtasks Remaining)

- Chủ dự án phải làm rõ ý định của quy tắc ưu tiên (xem `CONFLICT DETECTED`
  ở `DEC-149` §71): dùng đúng `_c.min` như đang hiển thị (chấp nhận `cong` có
  thể thắng), hay cần một field MỚI (chỉ giá NCC, `cong` CHỈ dùng khi không
  NCC nào định giá được).
- Sau khi có câu trả lời: mở `TASK-105C` implementation.

## Tóm Tắt Completion Gate (Completion Gate Summary)

Không áp Completion Gate — SPIKE discovery.

Required:
Trả lời 25 mục của đề bài bằng bằng chứng code; báo cáo `CONFLICT DETECTED`
nếu phát hiện, không tự giải quyết.

PASS:
Cả hai (bằng chứng E1 dưới đây).

BLOCKED:
Ý định thật của quy tắc ưu tiên Min/cong — cần chủ dự án xác nhận trước khi
chọn field nào implement.

NOT_TESTED:
Dữ liệu sống trong RTDB. Phiên này audit code, không có credential đọc
instance.

## Evidence Xác Minh (Verification Evidence)

| Check ID | Status | Evidence Level | Evidence | Executed By | Timestamp |
|---|---|---|---|---|---|
| M-01 field thật | PASS | E1 | `board/<mã>/_c.min` — client đọc qua `bMinOf(row)` `public/index.html:3583`, Worker fallback qua `soCotTinh()` `src/index.js:305-350` | S026 | 2026-08-27 |
| M-02 công thức nguồn | PASS | E1 | `minCuaDong()` `price-engine/src/nghiepvu.js:632-637`, dùng `locGiaNcc()` `:569-583` + `hetHangHoanToan()` `:596-599` | S026 | 2026-08-27 |
| M-03 công thức fallback (Worker) | PASS | E1 | `soCotTinh()` `src/index.js:305-350` — bản SAO Y độc lập, dùng khi `_c.k !== meta.k` (vân tay lệch) | S026 | 2026-08-27 |
| M-04 hai công thức KHÔNG hoàn toàn giống nhau | PASS | E1 | `soCotTinh()` **không** áp bộ lọc outlier `NGUONG_BAT_THUONG`/`locGiaNcc()` (pe-6) — chỉ lấy `cell.v>0` đơn thuần, `src/index.js:326-334` so với `price-engine/src/nghiepvu.js:569-583` | S026 | 2026-08-27 |
| M-05 writer | PASS | E1 | `tinhChot()` `price-engine/src/nghiepvu.js:677-690` → expose qua `price-engine/src/index.js:57-58` → Gateway `POST /api/tinhchot` `src/index.js:795,902` → client `napChot()` `public/index.html:3565-3577` → `saveBoardPaths()` `:3773-3789` (ghi `board/<mã>/_c`) hoặc `queTinhLai()` `:3685-3710` (bù dòng thiếu, chỉ khi `canBoardEdit()`) | S026 | 2026-08-27 |
| M-06 trigger tái tính | PASS | E1 | `canTinhLai()` `:3744-3749` — kích hoạt khi ghi cả dòng, `p/<NCC>` bất kỳ, hoặc `tp/ton`\|`tp/chot`\|`tp/bien` (`CHOT_NHANH` `:3743`) | S026 | 2026-08-27 |
| M-07 input `tp.ton` = `inv.cong` | PASS | E1 | `minCuaDong()` đọc `soCuaO((dong.tp\|\|{}).ton)` `:634`; `tp.ton` được ghi **duy nhất** bởi `invSyncPart()` (`public/index.html:7238,7250`), nguồn = `inv.<slot>.cong` — xác nhận lại `DEC-148` | S026 | 2026-08-27 |
| M-08 outlier filter | PASS | E1 | `locGiaNcc()` `:569-583`, `NGUONG_BAT_THUONG = 0.3` `:545` — loại dần NCC có giá < 30% giá NCC rẻ tiếp theo, ghi vào `batThuong`/`_c.bt` | S026 | 2026-08-27 |
| M-09 exclusion list (an/`_ANC`) | PASS | E1 | `_ANC` = hợp của `nccHidden()` (`NCC_ALIAS`/`NCC_RETIRED`) và `laMinLoai()` (`NCC_MIN_LOAI`), dựng ở `dungVanTay()` `public/index.html:3499-3508` | S026 | 2026-08-27 |
| M-10 exclusion list KHÔNG versioned | PASS | E1 | `NCC_RETIRED`/`NCC_MIN_LOAI` là **hằng số mã nguồn** (`public/index.html:4908,4927`; sao y ở `src/index.js:209,223`) — không lưu ở RTDB, không có bản ghi "ngày nào danh sách là gì". `NGUONG_BAT_THUONG=0.3` cũng vậy | S026 | 2026-08-27 |
| M-11 `_c` KHÔNG mang version formula | PASS | E1 | `ketQua()` gắn `pb: PHIEN_BAN` (`:99-101`), nhưng comment tại `src/index.js:797` xác nhận: *"Chỉ `ds` — `napChot()` bên trình duyệt cũng chỉ đọc đúng `r.ds`"* — `pb` bị **bỏ** trước khi ghi vào `board/<mã>/_c` | S026 | 2026-08-27 |
| M-12 Min KHÔNG BAO GIỜ đọc `phist` | PASS | E1 | `grep -n "phist" price-engine/src/nghiepvu.js src/index.js price-engine/src/index.js` = **0 hit**. `gotDong()` `public/index.html:3551-3556` chỉ gom `row.p`/`row.tp` HIỆN TẠI, không đụng `phist` | S026 | 2026-08-27 |
| M-13 `_c` không có history riêng | PASS | E1 | `board/<mã>/_c` là field đơn, ghi đè mỗi lần tính lại qua `update()`; không nhánh RTDB nào lưu chuỗi giá trị `_c.min` theo thời gian | S026 | 2026-08-27 |
| M-14 client-side lazy staleness | PASS | E1 | `cOf(row)` `:3469-3474` trả `undefined` nếu `c.k !== _VAN_TAY_AN` — trạng thái vận hành (chưa tính lại), KHÔNG phải trạng thái dữ liệu | S026 | 2026-08-27 |
| M-15 propagation CRM mỗi 10 phút | PASS | E1 | `wrangler.toml` cron `"*/10 * * * *"` → `scheduled()` `src/index.js:830-838` → `dayCrm()` `:521` → `gomBangGia()` `:537` → `soCotTinh()` — Min tự động lan sang hệ thống ngoài mỗi 10 phút, độc lập hành động người dùng | S026 | 2026-08-27 |
| M-16 manual override input | PASS | E1 | `oddNoMap()`/`pinOdd()` `public/index.html:5516-5533` — giá NCC bị "chốt giữ nguyên" (từ chối cập nhật) ảnh hưởng nội dung `p/<NCC>/v`, qua đó ảnh hưởng Min gián tiếp; lưu ở `meta.oddNo`, cắt còn `ODD_NO_MAX` mục gần nhất — không phải lịch sử đầy đủ | S026 | 2026-08-27 |
| B-01 CONFLICT DETECTED | PASS | E1 | Xem thân `DEC-149` §71 — trích chính xác dòng code `:632-637` đối chiếu nguyên văn quy tắc Owner | S026 | 2026-08-27 |
| N-01 dữ liệu sống | NOT_TESTED | — | Cần đọc instance RTDB thật. Không có trong phiên này | S026 | 2026-08-27 |

## Giới hạn của bằng chứng

- Không đọc RTDB sống — mọi kết luận mức E1.
- "Tần suất thực tế người vận hành sửa giá/nhập tồn kho trong một ngày"
  không xác định được từ mã nguồn.

## File Đã Thay Đổi (Files Changed)

Created:
- `docs/sessions/S026-task-105c-market-min-price-path-audit.md` (file này)

Modified:
- `PROJECT/PROJECT_DECISIONS.md` — `DEC-149`
- `PROJECT/PROJECT_PROGRESS.md` — cập nhật trạng thái, ghi rõ `CONFLICT
  DETECTED` chưa giải quyết
- `docs/tasks/TASK-108B-eligible-costs-owner-definition.md` — Phần VIII

Deleted:
- (không)

Repo B (`Tracking`):
- **0 file**.

## Quyết Định Chính (Key Decisions)

- `DEC-149` — audit Market Min Price, báo cáo `CONFLICT DETECTED` giữa business
  rule Owner mô tả và công thức thật, kết luận Historical Replay = C, đề xuất
  kiến trúc capture tối thiểu.

## Rủi Ro / Vướng Mắc (Risks / Blockers)

- **Rủi ro cao nhất:** implement quy tắc ưu tiên "Min trước, cong sau" bằng
  cách đọc thẳng `_c.min` mà không biết nó đã **ngầm chứa** `cong` bên trong.
  Kết quả: mọi lần `cong` rẻ hơn giá NCC (dù NCC vẫn còn hàng) sẽ bị hiểu nhầm
  là "Min có căn cứ, dùng Min" trong khi con số đó **chính là** `cong` đã
  thắng trong phép so sánh nội bộ — không phải giá NCC thật.
- Blocker capture layer từ `DEC-148` **không đổi và mở rộng thêm**: giờ không
  chỉ `inv.cong` thiếu lịch sử, mà cả `_c.min`, cả danh sách loại trừ NCC,
  cả ngưỡng lọc outlier — bốn lớp cùng thiếu, không phải một.
