# BÀN GIAO SESSION (SESSION HANDOFF)

Session ID:
S024

Task:
`TASK-105C` — Cross-repo RTDB Price Source Discovery (mở tại `DEC-146`)

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
`cab8aa0026e2342ff8bbd42c272813088110c315`
(nhánh `claude/reports-price-rtdb-audit-bg5y4t`; nhánh mặc định origin =
`claude/extract-upload-repo-gq2ws4`, tip `7e609780c77dd943173db77341bc315589a3a8a7`;
HEAD **chứa** tip mặc định — `git merge-base --is-ancestor` = 0)

Repo B — hệ thống giá / RTDB:
`hoangvinhkta-creator/Tracking` @ `d177363a390d36fe793e0c1c44a6fb6743ca45f5`
(= `origin/main`; git history **shallow**, mốc cũ nhất còn thấy được là
2026-08-18 — xem "Giới hạn của bằng chứng")

Ranh giới:
Hai repo giữ độc lập. Không subtree, không submodule, không copy source,
không merge history. Repo B **không bị sửa một byte nào** trong phiên này.

## Kết Quả (Result)

Năm câu hỏi của `TASK-108B` Phần V §49 nay **trả lời được bằng code**, không
còn phải suy đoán. Kết luận trọng yếu:

1. **RTDB CÓ lưu lịch sử giá** — nhánh `phist`, khoá theo ngày. Điều kiện
   `BLOCKING ARCHITECTURE GAP` mà `DEC-146` §3 nêu **KHÔNG kích hoạt** cho
   loại giá đó.
2. **Nhưng loại giá có lịch sử KHÔNG phải `AccountingPurchasePrice`.** `phist`
   lưu **giá NCC báo trong ngày** (báo giá của nhà cung cấp), không phải giá
   thực trả cho lô hàng. Giá thực nhập (`inv.<slot>.gia` / `.lo`) **không có
   lịch sử**: hai ô cuốn chiếu `cu`/`moi`, ghi bằng `set()` đè cả nhánh.
3. ⇒ **SOURCE MISMATCH**, không phải architecture gap. Đây là một kết luận
   khác hẳn hai nhánh mà `DEC-146` dự trù.

## Subtask Đã Hoàn Thành (Subtasks Completed)

- Định danh repo B, chốt SHA hai repo.
- Quét toàn repo B theo danh sách từ khoá của đề bài (firebase, databaseURL,
  RTDB, `ref(`, `set(`, `update(`, `push(`, price, prices, mkt, product, sku,
  code, timestamp, updated_at, history, snapshot).
- Lập schema thật của mọi nhánh RTDB mang giá.
- Truy vết **mọi** đường ghi và **mọi** đường đọc.
- Trả lời dứt điểm câu hỏi history-vs-overwrite bằng file/hàm cụ thể.
- Chạy Historical Replay Test trên schema thật.
- Đối chiếu khoá sản phẩm RTDB ↔ `product_raw` của Reports.
- Phân loại ngữ nghĩa từng trường giá.
- Audit write semantics (set/update/push/transaction, timestamp, provenance,
  audit trail, deletion).
- Audit security (credential, service account, database rules, public
  read/write, secrets committed).
- Đánh giá 5 option kiến trúc, chọn RECOMMENDED.

## Subtask Còn Lại (Subtasks Remaining)

- Chủ dự án ra quyết định **`AccountingPurchasePrice` là trường nào** (§ "Câu
  hỏi còn lại" trong `DEC-147`). Không tự chọn — đề bài cấm, `OD-105B-01` cấm.
- Sau khi có quyết định đó: mở `TASK-105C` implementation, viết
  `docs/tasks/TASK-105C-*.md`. **Chưa viết trong phiên này** vì file task
  MAJOR phải mang Scope Lock và Completion Gate, mà cả hai phụ thuộc câu trả
  lời trên.

## Tóm Tắt Completion Gate (Completion Gate Summary)

Không áp Completion Gate: đây là SPIKE discovery, không có deliverable code.
Tiêu chí ra khỏi phiên = trả lời được §49 mục 1–4 bằng bằng chứng code, và
xác định được mục 5 đúng hay sai tiền đề.

Required:
Trả lời §49 mục 1–4; kết luận history-vs-overwrite; kết luận historical replay.

PASS:
Cả ba (bằng chứng E1 dưới đây).

FAIL:
Không có.

BLOCKED:
`AccountingPurchasePrice` source selection — cần chủ dự án.

NOT_TESTED:
Bộ test của Reports **chưa chạy** trong phiên này — `pytest` không có trong môi
trường (`python3 -m pytest` → `No module named pytest`). Điều này chấp nhận
được vì phiên không đụng code: `git diff --name-only -- app config tests` = **0
file**. Không được đọc thành "test đã xanh".

Và mọi khẳng định về **dữ liệu sống trong RTDB** (ngày bắt đầu có `phist` thật,
độ phủ theo mã, số mốc thực tế). Phiên này audit **code**, không có credential
để đọc instance. Xem "Giới hạn của bằng chứng".

## Evidence Xác Minh (Verification Evidence)

| Check ID | Status | Evidence Level | Evidence | Executed By | Timestamp |
|---|---|---|---|---|---|
| A-01 SDK trình duyệt | PASS | E1 | `public/index.html:11-14` — Firebase JS SDK `10.12.2` compat (app/auth/database/app-check) | S024 | 2026-08-27 |
| A-02 SDK máy chủ | PASS | E1 | `src/firebase.js:47-93,114-160` — REST `<path>.json` + Bearer từ JWT RS256 ký bằng WebCrypto. `package.json` **không có dependency nào**; không `firebase-admin` | S024 | 2026-08-27 |
| B-01 RTDB endpoint | PASS | E1 | `src/firebase.js` `DB_MAC_DINH` = `https://tinphattracking-default-rtdb.asia-southeast1.firebasedatabase.app`, override bằng `env.FB_DB_URL` | S024 | 2026-08-27 |
| C-01 danh sách nhánh | PASS | E1 | `firebase-database.rules.json` — 13 nhánh gốc: `state hist profiles devices dnhap board meta alias dropped backup phist inv mkt` | S024 | 2026-08-27 |
| C-02 nhánh lịch sử giá | PASS | E1 | `public/index.html:6162-6163` + `BAO-MAT-TRIEN-KHAI.md:368-383` — `phist/<mã>/<NCC>/<YYYY-MM-DD> = giá`, `0` = hết hàng | S024 | 2026-08-27 |
| D-01 writer | PASS | E1 | Mọi lệnh ghi giá phát ra từ **trình duyệt**: `saveBoardPaths()` `public/index.html:3773`, `savePhist()` `:4645`, `saveInv()` `:6831`. Không writer phía máy chủ, không crawler trong repo | S024 | 2026-08-27 |
| D-02 ba đường ghi `phist` | PASS | E1 | `public/index.html:5171` + `:5192` (dán giá hằng ngày), `:6415` (sửa tay một ô), `:8416` (nhập file Excel — mốc khởi đầu) | S024 | 2026-08-27 |
| E-01 reader | PASS | E1 | Worker chỉ đọc `state/<i>/rules` (`src/index.js:663`), `profiles/<uid>` (`src/auth.js:143`), và `board`+`meta` cho `/api/board.csv` (`src/index.js:232,403`). **Không nơi nào ngoài UI trình duyệt đọc `phist`** | S024 | 2026-08-27 |
| F-01 schema `board` | PASS | E1 | `public/index.html:3407-3409`; ô giá dựng tại `:5155`, `:6410` | S024 | 2026-08-27 |
| F-02 schema `inv` | PASS | E1 | `public/index.html:6674-6696` (ba lớp giá `gia`/`lo`/`cong`), `:6705-6712` (`inv.map`) | S024 | 2026-08-27 |
| G-01 khoá sản phẩm | PASS | E1 | `normCode()` `public/index.html:8906` = `toUpperCase()` + `replace(/[^A-Z0-9]/g,"")`; rồi `aliasOf()` `:3939` | S024 | 2026-08-27 |
| H-01 ngữ nghĩa giá | PASS | E1 | `public/index.html:6687-6690` — `gia` = giá **thực nhập** trung bình; `cong` = giá nhập **công khai** (đẩy sang bảng); `p/<NCC>/v` = giá **NCC báo**. `price-engine/src/nghiepvu.js:601-607` — Min = "giá vốn rẻ nhất bán ra được" | S024 | 2026-08-27 |
| H-02 đơn vị tiền | PASS | E1 | `src/index.js:154-158` — *"Bảng giá của app lưu theo NGHÌN (5200)"*; `public/index.html:6761-6764` — *"Giá tồn được lưu theo đơn vị NGHÌN đồng (5.000 = 5 triệu)"*; `public/index.html:9163` — báo cáo ghi *"Đơn vị: nghìn đồng (K)"* | S024 | 2026-08-27 |
| I-01 timestamp | PASS | E1 | `todayStr()` `public/index.html:8864` = `toLocaleDateString("vi-VN")` → `D/M/YYYY`; `dayKey()` `:4640-4644` → `YYYY-MM-DD`. `grep -n "ServerValue\|serverTimestamp"` trên `public/index.html src/*.js` = **0 hit** ⇒ 100% timestamp là đồng hồ **client**, múi giờ client | S024 | 2026-08-27 |
| J-01 provenance | PASS | E1 | `phist` lưu **đúng một số**, không actor/source. `board/<mã>/p/<NCC>` có `d`,`f`,`gd`,`pv`(một bước),`m`(cờ sửa tay). `hist` = nhật ký toàn cục **tối đa 100 dòng**, ghi bằng `db.ref("hist").set()` đè cả nhánh (`public/index.html:9609-9620`) | S024 | 2026-08-27 |
| K-01 lịch sử có bị sửa được không | PASS | E1 | `xoaPhistSau()` `public/index.html:4870-4882` xoá mọi mốc ≥ một ngày; `doiMa` `:4570-4573` dời `phist/<cũ>`→`phist/<mới>` rồi `remove()`; `mergePaths()` `:4301-4325` gộp dòng board **nhưng không chạm `phist`** ⇒ mồ côi; `doRestore()` `:4755` `db.ref("board").set()` **không** chạm `phist` ⇒ hai nhánh lệch nhau | S024 | 2026-08-27 |
| L-01 secrets committed | PASS | E1 | `grep -rn "BEGIN PRIVATE KEY\|private_key\|client_secret\|serviceAccount"` trên toàn bộ mã nguồn và tài liệu của repo B (đuôi `js`, `html`, `json`, `toml`, `md`) = **0 hit**. `FB_SA_EMAIL`/`FB_SA_KEY`/`BOARD_API_KEY` là Cloudflare Secret (`BAO-MAT-TRIEN-KHAI.md:210-216,519`) | S024 | 2026-08-27 |
| L-02 database rules | PASS | E1 | `firebase-database.rules.json:3-4` — gốc `.read:false`/`.write:false`; **không nhánh nào** cho `auth == null`. `phist`/`inv`/`state`/`alias`/`dropped`/`backup` đòi `admin` hoặc `bedit` (đường lùi `edit`) | S024 | 2026-08-27 |
| L-03 App Check | PASS | E1 | `BAO-MAT-TRIEN-KHAI.md:857` — *"App Check — bấm Enforce · đã bấm 13/08/2026"*; kích hoạt tại `public/index.html:2549-2554` | S024 | 2026-08-27 |
| M-01 hợp đồng dữ liệu sẵn có | PASS | E1 | `GET /api/board.csv?key=<BOARD_API_KEY>` (`src/index.js:403-470`) — **chỉ ảnh chụp hiện hành**, không ngày, giá chia 1000 (`mil()` `:184`). Không endpoint nào xuất `phist` | S024 | 2026-08-27 |
| N-01 độ phủ `phist` thật | NOT_TESTED | — | Cần đọc instance RTDB sống. Phiên này không có credential | S024 | 2026-08-27 |

## Giới hạn của bằng chứng

Ba giới hạn phải ghi rõ, không được đọc báo cáo này như thể đã kiểm chứng
chúng:

1. **Không đọc RTDB sống.** Mọi kết luận về *hình dạng* dữ liệu suy ra từ mã
   ghi/đọc, mức E1. Kết luận về *nội dung* (mốc `phist` đầu tiên là ngày nào,
   bao nhiêu mã có lịch sử, có mã nào thủng không) **chưa kiểm chứng** — cần
   một lượt đọc thật.
2. **Git history của repo B là shallow** (`.git/shallow` tồn tại, commit cũ
   nhất còn thấy = 2026-08-18). `phist` xuất hiện từ bản dựng `b59` — **trước**
   mốc cắt — nên không truy được ngày bật tính năng bằng `git log`. Ngày bắt
   đầu có dữ liệu chỉ xác định được từ chính RTDB.
3. **Chỉ audit nhánh `main`/HEAD.** Nếu có Worker/crawler khác ghi vào cùng
   instance RTDB nhưng nằm ngoài hai repo này, phiên này không thấy được.

## File Đã Thay Đổi (Files Changed)

Created:
- `docs/sessions/S024-task-105c-rtdb-price-source-audit.md` (file này)

Modified:
- `PROJECT/PROJECT_DECISIONS.md` — `DEC-147`
- `PROJECT/PROJECT_PROGRESS.md` — trạng thái `TASK-105B` / `TASK-105C` / `TASK-108B`
- `PROJECT/LO_TRINH_DE_HIEU.md` — bước 11b, khối 5 câu hỏi
- `PROJECT/REVIEW_BUDGET_LEDGER.md` — mục nhật ký audit (không tiêu repair cycle)
- `docs/tasks/TASK-108B-eligible-costs-owner-definition.md` — Phần VI

Deleted:
- (không)

Repo B (`Tracking`):
- **0 file** — discovery không sửa repo giá.

## Quyết Định Chính (Key Decisions)

- `DEC-147` — toàn bộ kết luận audit, verdict, option kiến trúc, câu hỏi còn lại.

## Rủi Ro / Vướng Mắc (Risks / Blockers)

- **Blocker duy nhất còn lại của chuỗi giá:** chủ dự án phải chỉ ra trường nào
  là `AccountingPurchasePrice`. Ba ứng viên có ngữ nghĩa **khác nhau về bản
  chất**, và chỉ một trong ba có lịch sử.
- **Rủi ro cao nhất nếu bỏ qua báo cáo này:** lấy `phist` (có lịch sử, dễ lấy,
  trông đúng) làm giá nhập mà không hỏi. Đó đúng là cái bẫy `OD-105B-01` §D và
  đề bài mục 7 tồn tại để chặn.
