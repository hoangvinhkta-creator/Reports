# ADR-107 — Public Purchase là giá do Owner quản trong Tracking, Reports là bên tiêu thụ

## Status
Accepted

## Date
2026-08-30

## Context

### Giả định cũ và nó đến từ đâu

`DEC-156` (`D-01`/`OR-01`) chốt rằng Public Purchase là một **nguồn giá độc
lập** với Tracking, do chủ dự án cấp trực tiếp cho Reports dưới dạng một file
YAML đã ký version (`data/public_purchase/source_version.yaml`,
`PublicPurchaseSourceVersion`). `TASK-108B` gọi nó là "bảng giá chủ dự án
cấp"; quyền publish là `PUBLIC_PURCHASE_SOURCE_PUBLISH` (`DEC-124`).

Giả định ấy được đưa ra khi Reports **chưa** có đường đọc dữ liệu Tracking.
Nó hợp lý vào lúc đó, và toàn bộ phần triển khai theo nó
(`PublicPurchaseSourceLoader`, schema `E-A`/`E-B`/`E-C`, các invariant
`INV-02`/`INV-04`…`INV-09`, wiring composition) là đúng với giả định ấy.

Hệ quả quan sát được: vì file YAML chưa từng được cấp, `TASK-105E` không chỉ
thiếu giá — nó thiếu **identity**. `ProductIdentityResolver.__init__` nhận
`pp_version` không `Optional`, và `PostCutoverPriceComposition._resolve_eligible`
để `pp_version` trong cùng một cổng `AND` với catalog Tracking và store
identity. Một mã Tracking có đủ bằng chứng vẫn Pending, vì một file thuộc một
hệ thống khác vắng mặt.

### Nghiệp vụ thật, do Owner xác nhận

Trong Tracking, mỗi mặt hàng có **hai** con số tiền khác nhau, và chúng đã tách
rời sẵn trong mã từ trước:

| Khái niệm | Trường | Ai quyết định | Đi đâu |
|---|---|---|---|
| Giá vốn tồn thực tế (`Y`) | `inv.<thẻ>.gia[<khoá tên hàng>]` | Máy tính — bình quân gia quyền tồn cũ + lô nhập mới (`invRecalcAvg`) | Ở LẠI tab Tồn kho / Giá trị tồn kho |
| Giá công khai (Public Purchase) | `inv.<thẻ>.cong[<khoá tên hàng>]` | **Owner**, sửa tay; `inv.congTay` khoá không cho `Y` ghi đè | `invSyncPart()` → `board/<mã>/tp/ton` → nhân viên nhìn thấy |

Trích đúng lời chú thích trong `public/index.html` (Tracking):

```
· gia   giá thực nhập trung bình — chỉ máy tính, dùng định giá tài sản kho
· cong  giá nhập công khai — đẩy sang cột Tồn của Bảng giá để tính Min
```

```
/* Chỉ GIÁ CÔNG KHAI đi sang cột Tồn/Min. Giá thực nhập trung bình ở lại
   tab Tồn kho và tab Giá trị tồn kho. */
```

Owner có quyền đặt Public Purchase **cao hơn** `Y`. Lý do là nghiệp vụ, không
phải kỹ thuật: nếu nhân viên nhìn thấy giá vốn thật thấp, họ có xu hướng tự hạ
giá bán và bỏ mất phần lợi nhuận đáng lẽ giữ được. Ví dụ đã được Owner chốt:
`Y = 4.500.000`, Public Purchase `= 5.000.000` → `KpiPurchasePrice =
5.000.000`.

### Lịch sử effective-dated đã tồn tại sẵn

Mỗi lần `invSyncPart()` đổi `board/<mã>/tp/ton`, `savePpHist()` ghi một sự kiện
vào `purchase_price_history/<mã>/<pushId>` với `t = ServerValue.TIMESTAMP`,
`ta = "SERVER"`, `prev`, `next`, `by`, `src`. Rules ép `t === now &&
ta === 'SERVER'` và `!data.exists()` (chỉ tạo, không sửa/xoá). Mốc
`purchase_price_baseline/cutover` là ảnh chụp bất biến, một lần duy nhất, cũng
dấu thời gian máy chủ.

Nghĩa là: **`purchase_price_baseline` + `purchase_price_history` chính là lịch
sử effective-dated của Public Purchase** — không phải lịch sử của `Y`. Hai
nhánh này đã nằm trong allowlist hợp đồng dữ liệu Tracking → Reports từ trước,
và `TrackingPriceHistoryReader` (Reports History Reader V1) đã dựng lại giá tại
`SaleInterval` từ chúng.

## Decision

**Public Purchase = giá do Owner quản trong Tracking, effective-dated, và là
`KpiPurchasePrice`. Tracking là nguồn sự thật production DUY NHẤT. Reports là
bên tiêu thụ qua Data Contract.**

Cụ thể:

1. Đường production của Public Purchase là
   `inv.cong` → `board/<mã>/tp/ton` → `purchase_price_baseline` /
   `purchase_price_history` → `GET /api/xuat/<nhánh>` → `TrackingPriceHistoryReader`
   → `TrackingHistoryPriceProvider` → `PostCutoverPriceComposition` →
   `KpiPurchasePrice`.

2. `data/public_purchase/source_version.yaml` **KHÔNG còn là production source
   authority**. Nó giữ nguyên tư cách **LEGACY SUPPORTED FORMAT**: loader,
   schema và invariant không bị xoá, và namespace identity `PUBLIC_PURCHASE`
   vẫn phục vụ các mã ngoài danh mục Tracking.

3. Catalog `PUBLIC_PURCHASE` **không còn là điều kiện cần để resolve một mã
   Tracking**. `ProductIdentityResolver(pp_version=...)` trở thành `Optional`,
   và cổng `AND` của composition chỉ còn `TrackingCatalogSnapshot` +
   `ProductIdentityStore view`.

4. Giá vốn tồn thực tế `Y` **không bao giờ** được dùng thay Public Purchase.
   Không có fallback nào từ Public Purchase sang `Y`. Nếu Public Purchase
   không xác định được tại ngày bán → `Pending` / `Missing.PurchasePrice` →
   Review Queue canonical (`TASK-110`).

## Alternatives Considered

1. **Giữ nguyên YAML làm production source, chờ Owner cấp file.** Bị loại: nó
   yêu cầu Owner duy trì bằng tay một bản sao thứ hai của những con số họ đã
   quản trong Tracking. Hai nguồn sự thật cho cùng một đại lượng là một sai
   lệch chỉ chờ ngày xảy ra, và không có gì đối chiếu chúng.

2. **Dựng một nhánh lịch sử Public Purchase MỚI trong Tracking**
   (`public_purchase_history/...`) rồi mở rộng allowlist. Bị loại sau khi
   trace: `purchase_price_history` **đã** ghi đúng lịch sử của
   `board/<mã>/tp/ton`, tức đúng Public Purchase. Dựng nhánh thứ hai là tạo
   một baseline thứ hai cho cùng một đại lượng — đúng thứ mục IX của chỉ thị
   cấm.

3. **Bỏ hẳn `PublicPurchaseSourceVersion` và mọi thứ quanh nó.** Bị loại: nó
   phá test, fixture và bằng chứng lịch sử, và namespace `PUBLIC_PURCHASE` vẫn
   có công dụng cho identity ngoài Tracking. Phân biệt *legacy supported* với
   *production authority* đạt được cùng mục tiêu mà không phá gì.

## Rationale

Quyết định này không phát minh kiến trúc mới — nó **công nhận kiến trúc đã có**
trong Tracking và gỡ một ràng buộc sai ở Reports. Chi phí đúng bằng: một tham
số thành `Optional`, một cổng `AND` bớt một vế. Không có nhánh dữ liệu mới,
không có Rules mới, không có migration, không có cutover thứ hai.

Điểm mấu chốt là phân biệt **hai đại lượng khác nhau tình cờ cùng đơn vị tiền**.
Nhầm chúng là loại lỗi tệ nhất trong hệ này: cả hai đều là số tiền hợp lệ, nên
một `Y` đi nhầm vào bảng KPI sẽ trông hoàn toàn bình thường và không có gì đỏ
lên. Tracking đã tách đúng từ đầu; Reports chưa từng gọi tên sự tách ấy.

## Consequences

### Positive

- Owner quản Public Purchase ở đúng MỘT nơi — nơi họ đã quản.
- Public Purchase có lịch sử effective-dated, dấu thời gian máy chủ, append-only,
  rules ép — mạnh hơn hẳn một file YAML do người cấp.
- Mã Tracking có đủ bằng chứng không còn Pending vì một file không liên quan.
- `Y` không có đường nào tới Reports: hợp đồng chiếu `board` xuống đúng
  `{name, alt}`, và nhánh `inv` chưa bao giờ nằm trong allowlist.

### Negative / Tradeoffs

- Sự kiện lịch sử ghi TRƯỚC bản vá thẩm quyền thời gian phía Tracking
  (29/08/2026) không có `ta:"SERVER"` và vĩnh viễn không đủ thẩm quyền →
  Pending. Đây là đáp án đúng, không phải hạn chế cần lách.
- Public Purchase chỉ có mốc lịch sử khi đi qua `invSyncPart()`. Hai đường phụ
  ghi `board/<mã>/tp/ton` mà KHÔNG sinh mốc: `mergePaths()` (gộp mã, chỉ lấp ô
  đang trống) và nhập bảng giá từ Excel. Reader đã có khoá chuỗi `prev` để bắt
  đúng loại lỗ hổng này và trả Pending — nên nó **không** sinh ra số sai, chỉ
  làm giảm độ phủ. Ghi nhận là nợ kỹ thuật đã biết, không sửa trong ADR này.
- `PublicPurchaseSourceVersion` vẫn còn trong mã dù không còn là production
  authority. Phải đọc được điều đó từ tài liệu, không từ việc mã vắng mặt.

## Migration / Implementation Notes

- **Không có migration dữ liệu.** Nhánh `purchase_price_baseline`/
  `purchase_price_history` đã đúng ngữ nghĩa; không backfill, không dựng baseline
  thứ hai, không gán thẩm quyền ngược cho quá khứ.
- **Tracking: 0 dòng production.** Kiến trúc đã đúng; phiên này chỉ thêm bộ kiểm
  `kiem/gia-cong-khai-tham-quyen.js` khoá ranh giới `Y` ↔ Public Purchase.
- **Reports:** `pp_version` thành `Optional` trong `ProductIdentityResolver`;
  bỏ `pp_version` khỏi cổng `AND` của `_resolve_eligible`.
- Cutover Public Purchase = mốc `purchase_price_baseline/cutover` ĐÃ có sẵn của
  Tracking. Không tạo mốc mới.

## Supersedes

`DEC-156` `D-01`/`OR-01` — **chỉ ở phần "Public Purchase là nguồn độc lập do
chủ dự án cấp cho Reports"**. Phần còn lại của `DEC-156` không đổi. Bản ghi
lịch sử của `DEC-156` giữ nguyên, không viết lại: nó là quyết định đúng với
thông tin có lúc đó.

## Superseded By
None
