# S112 — PHB-01 Tracking Reconciliation + Closure

Mode: CONTROLLED RELEASE CLOSURE.
Docs-only trong Reports · 0 dòng production code · không migration · không
đổi Render/PostgreSQL/R2/Cloudflare · không mở PHB-02 · không repair NB-1 /
NB-3/4/5 / NB-6 · không ghi dữ liệu nghiệp vụ production.

Ghi chú phạm vi: PHB-01 (Product Identity — phân loại theo TÊN HÀNG) là một
vertical **của repo Tracking**. Phiên này ghi nhận bằng chứng đóng của nó vào
canonical state của Reports vì Reports là bên tiêu thụ hợp đồng
`inv.map` (`app/modules/product/identity/tracking_inv_map.py`) và vì
`IDENTITY_UNRESOLVED` là một trạng thái của pipeline Reports.

## 1. Hard Git Gate — Tracking (Phase 1)

```text
REPO                     = hoangvinhkta-creator/Tracking
EXPECTED_MAIN            = 9ede079413065ae0beef2c3ae005d332d8d92eca
OBSERVED origin/main     = 9ede079413065ae0beef2c3ae005d332d8d92eca  → KHỚP
EXPECTED_CANDIDATE_HEAD  = 598b4b1390cc96e552455ab85e2c48d78198b89c
OBSERVED origin/claude/phb-01-product-identity-manual-o28bsn
                         = 598b4b1390cc96e552455ab85e2c48d78198b89c  → KHỚP
MAIN IS ANCESTOR OF CANDIDATE = YES
rev-list --left-right --count main...candidate = 0 behind / 3 ahead
WORKTREE                 = sạch
TRACKING_GIT_GATE        = PASS
```

Ba commit trên đường phát hành, đúng như kỳ vọng, không có commit lạ:

```text
f087394  PHB-01: phân loại theo tên hàng + ghi hẹp xuống /inv
53993f1  PHB-01 BLOCKING-01: di trú giá phải ghi CẢ THẺ, không chỉ bốn bảng giá
598b4b1  PHB-01 NB-2: chặn phân loại tên hàng đè lên dòng tồn đang hoạt động
```

## 2. Pre-Merge Gate (Phase 2)

`npm run build` (= `node kiem/chay.js` rồi `node cong-cu/xen.js`) trên
candidate `598b4b1`:

```text
59 bộ · 2594 đạt · 0 hỏng · 2 bỏ qua   → khớp CHÍNH XÁC trạng thái đã biết
BUILD                    = OK (dist 7 file, 656 KB → 411 KB)
EXIT                     = 0
PRE_MERGE_TEST_GATE      = PASS
```

## 3. Reconcile main (Phase 3) + Post-Push (Phase 4)

Vì main là tổ tiên NGHIÊM NGẶT của candidate, dùng fast-forward thuần:
không force, không rewrite, không squash, không rebase, không cherry-pick.

```text
TRACKING_MAIN_BEFORE     = 9ede079413065ae0beef2c3ae005d332d8d92eca
FAST_FORWARD             = YES  (git merge --ff-only)
PUSH                     = 9ede079..598b4b1  main -> main  (không force)
TRACKING_MAIN_AFTER      = 598b4b1390cc96e552455ab85e2c48d78198b89c
CANDIDATE (không đổi)    = 598b4b1390cc96e552455ab85e2c48d78198b89c
main == candidate        = IDENTICAL
COMMIT PHÁT SINH THÊM    = KHÔNG (không có merge commit)
ROLLBACK_SHA             = 9ede079413065ae0beef2c3ae005d332d8d92eca
WORKTREE sau push        = sạch
APP_BUILD trên main      = b126   (public/index.html:2666)
invActiveRow trên main   = có mặt, 3 lần xuất hiện trong public/index.html
GATE chạy lại trên main  = 59 bộ · 2594 đạt · 0 hỏng · 2 bỏ qua · build OK
```

## 4. Production Smoke (Phase 5)

`price.tinphatcrm.com` KHÔNG tiếp cận được từ phiên này — proxy egress trả
`CONNECT tunnel failed, response 403` (đúng lớp policy denial đã ghi ở
`CHECK-PRA002-15`/S093 và S110). Vì vậy quan sát HTTP trực tiếp =
`NOT_OBSERVABLE`, và bằng chứng production dùng ở đây là **bằng chứng do
Owner cung cấp trực tiếp**, không phải phiên này tự quan sát — ghi trung
thực, không viết như thể session tự nghiệm thu được.

### 4.1 Fingerprint (Owner cung cấp)

```text
price.tinphatcrm.com APP_BUILD           = b126
mã nguồn live chứa                        = function invActiveRow(k)
số lần xuất hiện "invActiveRow(" trên live = 3
```

Đối chiếu tĩnh trong repo tại `598b4b1`: `APP_BUILD = "b126"` và ĐÚNG 3 lần
`invActiveRow(` trong `public/index.html` (định nghĩa + 2 điểm gọi). `invActiveRow`
vắng mặt qua `53993f1` và chỉ xuất hiện ở `598b4b1` → dấu vân tay production
khớp bản sửa NB-2 CUỐI CÙNG. `PRODUCTION_FINGERPRINT = PASS` (nguồn: Owner).

Phiên này KHÔNG tái dựng lịch sử triển khai (vì sao bản này đã live) — ngoài
phạm vi theo quyết định Owner.

### 4.2 Value type — `GET /api/xuat/inv_map` (A)

Quan sát live = `NOT_OBSERVABLE` (403 egress). Xác minh thay thế: đọc-tĩnh
hợp đồng tại `src/index.js` nhánh `node === "inv_map"` — projection chạy qua
`chieuInvMap()`, chỉ giữ khoá có giá trị **chuỗi**; giá trị object/số/null bị
LOẠI, không bọc, không ép kiểu, không lọt nguyên văn. Hợp đồng này có test
bắt buộc trong `kiem/xuat-baocao.js` mục 7b (đọc thẳng `inv/map`, không lộ
`cu`/`moi`/`soLuong`/giá; "bỏ qua khoá có giá trị không phải chuỗi, giữ khoá
hợp lệ"). Owner đã quan sát trên UI production mapping
`N_MYGITELECTROLUXEWF1143R7SC -> EWF1143R7SC`.

```text
SMOKE_VALUE_TYPE = NOT_OBSERVABLE trên HTTP live;
                   hợp đồng "chỉ giá trị CHUỖI, không object wrapper"
                   = PASS bằng đọc-tĩnh + test bắt buộc
```

### 4.3 Cross-repo key (B)

Ngữ nghĩa khoá `"N_" + normCode(description)[:80]` được kiểm ba chiều
(read-only, không tạo mapping production nào):

| Nguồn | `Máy giặt Electrolux EWF1143R7SC` |
|---|---|
| Tracking `invKeyOfName()` (`public/index.html:6935`) | `N_MYGITELECTROLUXEWF1143R7SC` |
| Reports `inv_map_key()` (`tracking_inv_map.py`) | `N_MYGITELECTROLUXEWF1143R7SC` |
| UI production (Owner quan sát) | `N_MYGITELECTROLUXEWF1143R7SC` |

Vector mô tả dài (chỉ read-only/local, KHÔNG tạo mapping production):

```text
Điều hoà Daikin FTKB35YVMV/RKB35YVMV inverter 1.5HP gas R32 model 2025 kèm lắp đặt
Tracking  → N_IUHODAIKINFTKB35YVMVRKB35YVMVINVERTER15HPGASR32MODEL2025KMLPT (63 ký tự)
Reports   → N_IUHODAIKINFTKB35YVMVRKB35YVMVINVERTER15HPGASR32MODEL2025KMLPT  → KHỚP
```

`SMOKE_CROSS_REPO_KEY = PASS`.

## 5. Real Production E2E (Owner cung cấp — chấp nhận)

```text
ORDER                    = BH73877
ACCOUNTING_DESCRIPTION   = Máy giặt Electrolux EWF1143R7SC
IDENTITY_BEFORE          = IDENTITY_UNRESOLVED
tồn kho cu/moi           = EWF1143R7SC KHÔNG có mặt → đúng đường "câu tên hàng"
KEY sinh ra              = N_MYGITELECTROLUXEWF1143R7SC
CANONICAL chọn           = EWF1143R7SC — Máy giặt Electrolux
MAPPING trên UI          = N_MYGITELECTROLUXEWF1143R7SC -> EWF1143R7SC
UI sau khi ghi           = 1 tên hàng · 1 đã có quyết định
```

Chạy lại Reports trên cùng workbook `So_chi_tiet_ban_hang (10).xlsx`:

```text
                        TRƯỚC     SAU
tổng đơn                106       106     (không đổi — không sinh/mất đơn)
AUTO                     17        56
cần review               89        50
product identity unresolved  36        35
```

Riêng BH73877 sau khi chạy lại:

```text
IDENTITY_AFTER           = IDENTITY_UNRESOLVED đã BIẾN MẤT
ECONOMIC_STATE_AFTER     = PENDING — TRACKING_HISTORY_PENDING /
                           Missing.PurchasePrice
```

Đây là **hành vi AN TOÀN ĐÚNG như thiết kế**: phân giải identity KHÔNG được
bịa ra bằng chứng kinh tế và KHÔNG được ép đơn sang AUTO. Màn "phân loại theo
tên hàng" giữ **economics-isolated**: không auto-recalc, và nếu khoá dán vào
trùng một dòng `INV.cu`/`INV.moi` đang hoạt động thì màn này TỪ CHỐI ghi và
đẩy người dùng về luồng Tồn kho (chốt NB-2, `invActiveRow()`).

`REAL_E2E = PASS`.

## 6. Quyết Định Owner Được Ghi Nhận

```text
NB-2          = CLOSED bằng bản sửa có giới hạn 598b4b1
NB-1          = DEFER (không phải blocker của PHB-01)
D8            = CLOSED trong PHB-01 (không mở task D8 khác)
NB-3/4/5      = DEFER
NB-6          = NON_BLOCKING UX POLISH → DEFER
35 mô tả còn lại = OPERATIONAL DATA CLEANUP, không phải việc implementation,
                   không chặn PHB-01
```

Finding KHÔNG tự sinh task.

## 7. Kết Luận

Chín điều kiện đóng PHB-01 đều đạt: implementation đủ · review độc lập đã
chấp nhận · bản sửa NB-2 có trong bản phát hành · dấu vân tay production khớp
bản sửa cuối · E2E production thật được chấp nhận · `IDENTITY_UNRESOLVED`
biến mất cho BH73877 · không bịa bằng chứng kinh tế · `main` của Tracking đã
reconcile về candidate cuối · canonical state của Reports được cập nhật nhất
quán.

```text
PHB_01               = DONE
SCOPE_DRIFT          = NO
BLOCKING_FINDINGS    = 0
NEXT_VERTICAL_ACTION = PHB-02 BUSINESS PARITY CONTRACT (không bắt đầu
                       implementation trong phiên này)
```
