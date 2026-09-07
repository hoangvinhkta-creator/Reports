# ADR-110 — Giá nhập tự động của Reports là MIN theo NGÀY BÁN, do Tracking tính

## Status
Accepted

## Date
2026-09-07

## Context

### Owner đã nói một điều mà repo đang nói khác

`R1 Execution Brief — Giá MIN theo ngày bán` (Owner, 2026-09-07) mở đầu bằng
đúng một câu quy phạm:

> Tracking sở hữu việc tính và lưu giá MIN theo ngày. Reports dùng giá MIN của
> đúng ngày bán để tính giá nhập KPI. Ngày upload file không tham gia chọn giá.

và §3.1 nói thẳng: *"Trong R1, giá nhập tự động duy nhất là MIN do Tracking
tính."*

Trạng thái canonical của repo trước phiên này nói khác:
`PROJECT/PROJECT_PROGRESS.md` ghi `PRICE_AUTHORITY = TRACKING_PP_AT_SALE_DATE_ONLY`,
và `ADR-107` chốt rằng **Public Purchase** — giá nhập công khai Owner sửa tay ở
tab Tồn kho của Tracking, đọc qua `purchase_price_baseline`/
`purchase_price_history` — là `KpiPurchasePrice`.

Đây là một **CONFLICT DETECTED** thật, không phải một khác biệt chữ nghĩa.

```text
Documentation   : ADR-107 + DEC-165 — giá nhập = Public Purchase (`inv.cong`
                  → `board/<mã>/tp/ton`), Owner đặt tay, đọc qua lịch sử sự kiện.
Implementation  : app/modules/pricing/tracking_history/ + composition nhánh
                  TRACKING, đúng như tài liệu.
Owner (R1 brief): giá nhập tự động = MIN của ngày bán — rẻ nhất giữa các nhà
                  cung cấp còn hàng và ô Tồn, do engine Tracking tính.
Risk            : cả hai đều là số tiền hợp lệ, cùng đơn vị, cùng đến từ
                  Tracking, cùng gắn với một mã và một ngày. Một bên đi nhầm
                  vào bảng KPI sẽ trông hoàn toàn bình thường — không có gì đỏ
                  lên, và sai số chảy thẳng vào lợi nhuận rồi vào lương.
```

### Hai đại lượng, không phải hai cách gọi một đại lượng

Trong Tracking, một mặt hàng có ba lớp giá tách rời sẵn trong mã
(`public/index.html`, khối "Ba lớp giá của mỗi thẻ tồn"):

| Khái niệm | Trường | Ai quyết định | Nghĩa nghiệp vụ |
|---|---|---|---|
| Giá thực nhập bình quân | `inv.<thẻ>.gia` | Máy tính (`invRecalcAvg`) | giá vốn tồn kho |
| Giá nhập công khai | `inv.<thẻ>.cong` → `board/<mã>/tp/ton` | **Owner sửa tay** | con số nhân viên được thấy |
| **MIN** | `board/<mã>/_c.min` | **Engine** (`minCuaDong`) | **rẻ nhất MUA ĐƯỢC hôm nay** |

`ADR-107` đúng ở phần nó nói: giá công khai là một đại lượng do Owner quản,
có lịch sử effective-dated, và Reports đọc nó qua hợp đồng. Điều nó không nói
— vì lúc ấy chưa ai hỏi — là **giá nhập tự động của báo cáo có phải nó không**.
Owner nay trả lời: không. Giá nhập tự động là MIN.

Khác biệt không nhỏ: giá công khai được Owner đặt CAO HƠN giá vốn thật một
cách có chủ đích (`ADR-107` Context — để nhân viên không tự hạ giá bán), còn
MIN là giá vốn rẻ nhất mua được. Dùng cái thứ nhất làm giá nhập là báo cáo một
biên lợi nhuận thấp hơn thực tế, đều đặn, trên mọi dòng.

### Vì sao MIN chưa dùng được ngay như nó vốn có

`board/<mã>/_c.min` là số **hiện tại**. Nó bị ghi đè mỗi lần bảng giá đổi, và
crawler đổi giá mỗi đêm. Không có lịch sử nào của nó. Sổ bán hàng thì được nạp
vào cuối tháng. Đọc `_c.min` lúc nạp file là gán giá của ngày 30 cho một đơn
bán ngày 03 — đúng điều brief §3.5 cấm.

`_c.min` cũng không chở nguồn thắng: nó chỉ có con số. Bản ghi giá vốn phải
giải thích được vì sao là con số đó, và "hai nhà cung cấp cùng báo 6.800" là
một sự thật khác "một nhà cung cấp báo 6.800".

## Decision

**Giá nhập tự động của Reports = MIN của ĐÚNG ngày bán, do Tracking tính, lưu
theo ngày, và xuất qua hợp đồng `daily-min-v1`.**

1. **Tracking sở hữu con số.** Engine trả thêm nguồn thắng
   (`nguonGiuMin()`); `tinhMinNgay()` dùng CHUNG `minCuaDong()` với
   `tinhChot()` nên cột Min trên bảng và bản ghi theo ngày không thể lệch
   nhau. Kết quả giá KHÔNG đổi (`PHIEN_BAN` giữ nguyên `pe-6`).

2. **Lưu theo ngày, chỉ ghi khi đổi, và có bằng chứng ngày đã quan sát.**
   `min_ngay/<mã>/<ngày>` giữ các mốc đổi; `min_ngay_ngay/<ngày>` chứng minh
   hôm ấy Tracking có nhìn bảng giá. **Một mốc tại ngày R ≤ D hợp lệ cho ngày
   D khi và chỉ khi ĐÚNG NGÀY D có bản ngày**; ngày D không có bản ngày là
   `SOURCE_UNAVAILABLE`, không phải giá cũ.

   Luật này dựa vào một bất biến của phía ghi, và chỉ đúng chừng nào bất biến
   ấy còn: **bản ngày chỉ được ghi khi engine trả kết quả cho TOÀN BỘ mã của
   bảng giá.** Khi đó "ngày D đã quan sát, mã M không có bản ghi mới" là bằng
   chứng trực tiếp rằng trạng thái của M ở ngày D bằng trạng thái tại R — các
   ngày ở giữa không thêm thông tin gì. Bất biến ấy được ép bằng bốn chốt
   fail-closed trong `chupMinNgay` (bảng rỗng, engine sai hình dạng, engine
   thiếu mã, thiếu phiên bản luật) — trước phiên kiểm thử R1 chúng chưa có,
   và một lượt chụp hỏng vẫn ghi được bản ngày "thành công".

   Bản đầu của R1 đòi mọi ngày trong khoảng `(R, D]` đều có bản ngày. Luật ấy
   sai theo hướng tốn kém: lỡ MỘT ngày là mọi mã giá ổn định bị khoá ngoài
   VĨNH VIỄN — mốc của chúng nằm trước chỗ đứt, chúng không bao giờ sinh mốc
   mới, nên mọi ngày về sau đều `SOURCE_UNAVAILABLE`. Sửa trong cùng phiên
   kiểm thử; xem `docs/sessions/S126-r1-daily-min-theo-ngay-ban.md`.

3. **`PROVISIONAL`/`FINAL` là tính chất của NGÀY**, nằm ở bản ngày. Chốt chỉ
   sau khi ngày kết thúc theo UTC+7, idempotent, và chỉ cho ngày thật sự đã
   được quan sát. Một ngày đã chốt không bị dữ liệu hiện tại sửa; sửa quá khứ
   đi đường `min_ngay_sua` có lý do và revision mới.

4. **`MIN = 0` dừng ở biên xuất bản.** Sentinel "hết hàng hoàn toàn" (`pe-4`)
   ra hợp đồng thành `OUT_OF_STOCK` + `min_price = null`. Bốn tình trạng
   không-có-giá (`AVAILABLE`/`OUT_OF_STOCK`/`NO_DATA` + `SOURCE_UNAVAILABLE`
   ở tầng lỗi) không bao giờ mang một con số.

5. **Reports là bên tiêu thụ, không tính lại.** `TrackingDailyMinProvider` tra
   `(mã Tracking đã resolve, ngày bán)`. Không có nhánh nào lấy bản của ngày
   khác, giá hiện tại, hay giá 0. Quy đổi nghìn VND → VND đúng MỘT lần.

6. **Nhánh `TrackingPriceHistory` (lịch sử `tp/ton`) KHÔNG bị xoá, KHÔNG đổi
   nghĩa, và KHÔNG còn là nguồn giá mặc định.** Nó chỉ chạy khi caller nêu rõ
   `legacy_tracking_history_authority=True`. Không có đường rơi từ MIN sang nó.

   Hệ quả trực tiếp, và nó KHÔNG hiển nhiên: từ R1 nguồn ấy cũng thôi là đầu
   vào BẮT BUỘC của một lần chạy. Nó vẫn được chụp và vẫn vào bằng chứng khi có
   mặt — để đối chiếu kết quả sinh trước R1 — nhưng giữ nó REQUIRED là bắt báo
   cáo hôm nay phụ thuộc vào một nguồn hôm nay không dùng: một sự cố 502 ở
   nhánh legacy sẽ chặn một lần chạy mà mọi giá đều đến từ nguồn khác. Vắng mặt
   thì bằng chứng NÓI RA (`purchase_price_history_status`), không im lặng.
   Danh mục Tracking thì vẫn REQUIRED: không có nó thì không resolve được mã
   nào.

7. **Không backfill.** Không dựng lịch sử MIN từ `tp/ton`, không dựng từ bảng
   giá hôm nay. Lịch sử MIN có thẩm quyền bắt đầu từ lượt chụp đầu tiên.

8. **Một ảnh chụp là ảnh của MỘT trạng thái — kể cả trong MỘT trang.** Hợp
   đồng phân trang theo mã, con trỏ chỉ là VỊ TRÍ trong danh sách mã đã sắp, và
   Firebase RTDB không có ảnh chụp đọc nhất quán qua nhiều lệnh đọc. Tracking
   giữ một token trạng thái (`min_ngay_rev`) và đổi nó sau MỌI lượt ghi vào các
   nhánh MIN theo ngày. Ba lớp bảo vệ, và cả ba đều cần:

   - **Đọc lạc quan HAI ĐẦU.** `xuatMinNgay()` đọc token trước dữ liệu, đọc lại
     sau dữ liệu, chỉ trả kết quả khi hai lần bằng nhau. Chỉ đọc một đầu thì
     bắt được lượt ghi xen giữa hai trang nhưng MÙ với lượt ghi xen vào giữa
     các lệnh đọc của MỘT trang — mã đọc trước mang trạng thái cũ, mã đọc sau
     mang trạng thái mới, phong bì vẫn nhất quán. Phân trang không liên quan:
     một trang duy nhất đã có thể là ảnh ghép.
   - **Con trỏ MANG THEO token** (`<revision>:<vị trí>`). Máy chủ từ chối con
     trỏ mang revision khác revision hiện tại, nên một client viết ẩu cũng
     không tự nối được trang 2 của trạng thái mới vào trang 1 của trạng thái
     cũ. Trách nhiệm nằm ở phía có đủ thông tin để kiểm.
   - **Phong bì chở `query_revision`,** và Reports TỪ CHỐI gộp các trang — hoặc
     các ĐOẠN NGÀY, xem §9 — lệch token.

   Năm trường phong bì cũ không thay được nó: chúng chỉ lặp lại yêu cầu vừa gửi
   đi, nên chúng khớp nhau kể cả khi dữ liệu bên dưới đã đổi hoàn toàn.

9. **Ảnh chụp MIN phụ thuộc KỲ, nên phải được HỎI cho từng lần chạy.** Khác
   `purchase_price_history`/`catalog` — vốn là ảnh chụp toàn bộ một nhánh, chụp
   một lần dùng mãi — hợp đồng `daily-min-v1` nhận `product_codes` và
   `date_from..date_to`, nên một ảnh chụp chỉ trả lời được đúng những cặp nó đã
   hỏi. Hệ quả kiến trúc:

   - Đường upload web LẬP KẾ HOẠCH trước khi gọi: đọc sổ, resolve identity bằng
     chính resolver production, gom tập mã Tracking + từng cặp `(mã, ngày bán)`
     cần trả lời, rồi gọi hợp đồng và đóng băng kết quả cho lần chạy ấy.
   - **Kỳ rộng hơn trần 62 ngày của hợp đồng được CHIA thành các đoạn** ≤ 62
     ngày, hỏi từng đoạn, và chỉ gộp khi mọi đoạn cùng `query_revision`. Bỏ qua
     lượt hỏi giá vì kỳ quá rộng là kết cục tệ nhất: lần chạy vẫn ra một báo
     cáo đầy đủ hình thức, không một giá vốn nào, trông y hệt một báo cáo bình
     thường. Rộng quá mức gộp được (trần đoạn mỗi lần chạy) ⇒ TỪ CHỐI với
     hướng dẫn TÁCH KỲ, không phải "thử lại sau" — thử lại không giúp gì.
   - Luồng Owner cục bộ chọn ảnh chụp trả lời được TỪNG CẶP `(mã, ngày)` của kỳ
     đang chạy, không phải ảnh chụp mới nhất và không chỉ theo khoảng ngày. Hai
     ảnh chụp cùng kỳ có thể được chụp cho hai TẬP MÃ khác nhau; chọn nhầm thì
     phần lớn dòng ra `NOT_IN_CAPTURE` trong khi kho ĐANG CÓ một ảnh chụp trả
     lời được. Một cặp nằm ở `errors` VẪN tính là đã trả lời. Không ảnh chụp
     nào đủ ⇒ `None` ⇒ Pending kèm "nguồn chưa nối" — một câu đúng.

10. **Hoàn tất cấp kỳ là BA điều kiện, không phải một.**
    `resolved_prices_are_final` chỉ nói về những dòng ĐÃ có giá; một kỳ rỗng
    hoặc toàn Pending cũng thoả nó, và điều đó đúng theo nghĩa hẹp ấy. Cổng
    hoàn tất là `period_is_final`: có dữ liệu cần chốt, KHÔNG còn Pending, và
    KHÔNG còn giá đến từ ngày `PROVISIONAL`. Tên cũ (`prices_are_final`) mời
    đúng cách đọc sai kia, nên nó được đổi tên chứ không chỉ được chú thích.

## Alternatives Considered

1. **Reports tự tính MIN từ `board` đã capture.** Bị loại: luật MIN gồm danh
   sách nhà cung cấp bị ẩn/đã nghỉ/không tính Min, ngưỡng giá bất thường, và
   quy ước sentinel — cả bốn đều sống trong Tracking và còn đổi. Chép sang
   Reports là dựng bản thứ hai của một luật đang sống, và hai bản sẽ trôi khỏi
   nhau (vấp #5 trong quy chuẩn của repo Tracking). Khi ấy bảng giá hiện một
   con số, báo cáo hiện con số khác, và không ai nói được bên nào đúng.

2. **Ghi đủ mọi mã mỗi ngày thay vì chỉ ghi khi đổi.** Bị loại: 3.441 mã ×
   365 ngày ≈ 1,2 triệu bản ghi/năm cho một dữ liệu mà phần lớn lặp lại chính
   nó. Bản ngày (`min_ngay_ngay`) cho cùng một bảo đảm với chi phí một bản
   ghi/ngày — và nó còn phân biệt được "giá không đổi" với "hôm ấy hệ thống
   không chạy", điều mà cách kia cũng không làm được nếu job lỡ một ngày.

3. **Đặt `PROVISIONAL`/`FINAL` trên từng bản ghi.** Bị loại: một bản ghi có
   thể có hiệu lực cho nhiều ngày (mốc mang qua), nên nó sẽ vừa là FINAL cho
   ngày này vừa là PROVISIONAL cho ngày kia — và không có chỗ nào ghi nổi cả
   hai. Chốt ngày cũng sẽ thành hàng nghìn lệnh ghi thay vì một.

4. **Giữ `tp/ton` làm nguồn dự phòng khi chưa có ảnh chụp MIN.** Bị loại, và
   đây là phương án nguy hiểm nhất trong danh sách: nó làm báo cáo đầy số,
   không dòng nào Pending, và mọi con số là của một đại lượng khác. Đúng lớp
   lỗi mà cả capability này tồn tại để chặn.

## Rationale

Điểm mấu chốt giống hệt `ADR-107` nhưng ở một cặp khái niệm khác: **hai đại
lượng khác nhau tình cờ cùng đơn vị tiền**. Ở `ADR-107` là giá vốn tồn thực tế
(`Y`) ↔ giá công khai; ở đây là giá công khai ↔ MIN. Cả ba đều là số tiền hợp
lệ của cùng một mã, nên nhầm lẫn giữa chúng không tạo ra ngoại lệ nào, không
làm đỏ ô nào, và chỉ hiện ra ở cuối tháng dưới dạng một biên lợi nhuận "hơi
khác mọi khi".

Cách duy nhất chống lại lớp lỗi ấy là gọi tên nó ở tầng dữ liệu: mỗi nguồn một
nhãn `price_source` riêng, mỗi bản ghi mang nguồn thắng và revision, và không
nhánh nào được rơi từ nguồn này sang nguồn kia.

## Consequences

### Positive

- Một đơn bán ngày 03/09 luôn ra giá của 03/09, dù nạp sổ ngày nào — điều mà
  kiến trúc trước không bảo đảm được cho MIN.
- Giá vốn nay là giá vốn rẻ nhất mua được, đúng nghiệp vụ Owner mô tả.
- Mỗi con số mở lại được: nguồn thắng, revision, phiên bản luật, vân tay đầu
  vào, ngày quan sát, và ngày ấy đã chốt hay chưa.
- Khoảng thời gian hệ thống không chạy hiện ra thành `SOURCE_UNAVAILABLE` thay
  vì được lấp lặng lẽ bằng giá cũ.

### Negative / Tradeoffs

- **Lịch sử MIN bắt đầu từ lượt chụp đầu tiên.** Mọi ngày trước đó không có
  bản ghi và không backfill được: bảng giá cũ đã bị ghi đè, và `tp/ton` là một
  đại lượng khác. Đơn bán trước mốc ấy sẽ Pending, hoặc dùng nguồn xác nhận
  tay đã có sẵn (`HistoricalConfirmedRegistry`).
- **Lượt chụp phụ thuộc `meta.an`** — danh sách nhà cung cấp bị bỏ khỏi công
  thức MIN, do trình duyệt Tracking đăng lên. Chưa ai mở app Bảng giá kể từ
  bản này thì lượt chụp ghi `SOURCE_UNAVAILABLE` cho ngày đó. Fail-closed có
  chủ đích: thà không có bản ghi còn hơn một bản ghi tính bằng danh sách sai.
- **Ảnh chụp gắn với một kỳ** (tập mã + khoảng ngày), khác hai capture kia
  vốn "chụp một lần dùng mãi". Nên nó là đầu vào TUỲ CHỌN của luồng Owner, và
  vắng mặt thì mọi dòng Tracking Pending.
- **Đường web pull-on-run chưa lấy MIN theo ngày.** `tools/tracking/live_pull.py`
  không biết tập mã của kỳ (nó chỉ có sẵn sau khi resolve identity), nên vòng
  này không nối. Hệ quả: bản web trả Pending cho nhánh Tracking cho tới khi
  đường ấy được nối hoặc Owner chạy công cụ chụp. Đây là khoảng trống ĐÃ BIẾT,
  được ghi ra chứ không im lặng, và nằm ngoài phạm vi R1 (brief §2).

## Migration / Implementation Notes

- **Không migration dữ liệu.** `purchase_price_baseline`/`purchase_price_history`
  giữ nguyên nghĩa cũ, vẫn nằm trong hợp đồng xuất, vẫn đọc lại được.
- **Tracking:** engine trả nguồn thắng; `src/min-ngay.js` mới; ba nhánh RTDB
  mới chỉ máy chủ ghi được; cron 20 phút; `POST /api/min-ngay`.
- **Reports:** `app/modules/pricing/daily_min/` mới;
  `tools/tracking/capture_daily_min.py` mới; composition đổi nhánh TRACKING;
  nhãn `price_source = TRACKING_DAILY_MIN`.

## Supersedes

`ADR-107` — **chỉ ở đúng một mệnh đề**: "Public Purchase … là
`KpiPurchasePrice`". Mọi phần còn lại của `ADR-107` giữ nguyên hiệu lực:
Tracking vẫn là nguồn sự thật production duy nhất; Public Purchase vẫn là một
đại lượng do Owner quản, có lịch sử effective-dated; giá vốn tồn thực tế `Y`
vẫn không bao giờ tới Reports; `data/public_purchase/source_version.yaml` vẫn
là LEGACY SUPPORTED FORMAT.

Bản ghi lịch sử của `ADR-107` **không được viết lại**: nó là quyết định đúng
với thông tin có lúc đó, và evidence của các phiên trước dựa vào nguyên văn
của nó.

## Superseded By
None
