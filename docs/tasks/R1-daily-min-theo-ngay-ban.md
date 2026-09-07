# R1 — Giá MIN theo ngày bán (Tracking sở hữu, Reports tiêu thụ)

## Metadata

Status:
IMPLEMENTED

Current Status Reason:
Toàn bộ phạm vi R1 đã triển khai, đã qua một lượt kiểm thử/sửa lỗi riêng
(07/09/2026: bốn chốt fail-closed phía Tracking, hai chốt toàn vẹn phía
Reports, và một luật mang-mốc-qua-ngày được sửa lại), và có bằng chứng E1/E2
trên cả hai repo — kể cả đường xuyên suốt Tracking → hợp đồng → Reports → giá
nhập → lợi nhuận và ba luồng smoke có output trích nguyên văn. Còn chờ đúng
hai việc trước khi `DONE`: (1) một lượt Independent Review, (2) Owner nghiệm
thu trên dữ liệu thật sau khi chạy lượt chụp đầu tiên. Triển khai production
KHÔNG thuộc R1 (brief §2).

Phase:
PHASE-01 — Engine tính toán

Task Mode:
MAJOR

Primary Agent Tier:
C

Escalation Tier:
C

Difficulty:
4/5

Risk:
4/5

Blast Radius:
5/5 (V4.1 §4 — chấm theo data path: `MIN → giá nhập → EligibleKpiProfit →
DS quy đổi → KPI/lương`)

Effective Risk:
HIGH (Blast Radius quyết định, không phải Risk cục bộ — V4.1 §4.1)

Project Profile:
PRODUCT

Review Budget lineage:
**`R1` — root lineage riêng**, `2 allowed / 0 used / 2 remaining`
(`PROJECT/REVIEW_BUDGET_LEDGER.md` §"Root Task: R1"). Bảng đã freeze `V4.1` §2
cho `HIGH/CRITICAL = 2`. Mở task KHÔNG tiêu ngân sách.

Owner Authority:
`R1 Execution Brief — Giá MIN theo ngày bán` (2026-09-07). Đăng ký quyết định:
`PROJECT/PROJECT_DECISIONS.md` → `DEC-199`. Quyết định kiến trúc:
`docs/adr/ADR-110-daily-min-price-authority.md`.

---

## 1. Mục tiêu

Một đơn bán ngày `D` phải được tính bằng giá vốn của ĐÚNG ngày `D`, bất kể sổ
kế toán được nạp ngày nào. Bảng giá đổi mỗi đêm theo crawler, nên "giá hiện
tại" và "giá lúc bán" là hai con số khác nhau — dùng nhầm là sai lợi nhuận cả
tháng mà không có gì đỏ lên.

Giá vốn ấy là **MIN**: rẻ nhất mua được giữa các nhà cung cấp còn hàng và ô Tồn
Tín Phát, do engine Tracking tính. KHÔNG phải giá nhập công khai (`tp/ton`) —
xem `ADR-110` phần Context để biết vì sao hai thứ đó không thay nhau được.

## 2. Scope Lock

### Trong phạm vi

- Tracking: engine MIN trả thêm nguồn thắng; lưu MIN theo ngày; trạng thái
  ngày tạm/chốt; sửa bản ghi có dấu vết; hợp đồng batch cho Reports.
- Reports: model + loader + provider cho `daily-min-v1`; tra bằng `sale_date`;
  provenance; lý do Pending; nối vào composition và luồng Owner.
- Tương thích: dữ liệu cũ giữ nguyên nghĩa cũ; không migrate, không đổi nhãn.
- Test, build, validator, tài liệu, handoff.

### Ngoài phạm vi (KHÔNG làm trong R1)

- Giá thực nhập, giá theo lô, lợi nhuận thực mua.
- Màn hình phân loại mã, `OUT_OF_CATALOG`, luồng giá tay hoàn chỉnh — R2.
- Thiết kế lại bảng nhân viên, xuất Excel, dashboard — R3/R4.
- Triển khai production (deploy Worker, chạy lượt chụp đầu tiên trên dữ liệu
  thật, nối đường web pull-on-run).

## 3. Quyết định thiết kế đáng chất vấn nhất

Ba điểm dưới đây là chỗ Independent Review nên nhìn trước tiên.

### 3.1. Chỉ ghi khi ĐỔI, và "bản ngày" là thứ làm cho điều đó an toàn

`min_ngay/<mã>/<ngày>` chỉ giữ các MỐC ĐỔI. Một mình nó thì "không có bản ghi
ngày D" vừa khớp với "giá giữ nguyên", vừa khớp với "hôm ấy hệ thống không
chạy" — và lấp khoảng chết bằng giá cũ là đúng lớp lỗi R1 sinh ra để chặn.

Nên mỗi lượt chụp ghi thêm một BẢN NGÀY (`min_ngay_ngay/<ngày>`), kể cả khi
không mã nào đổi. Quy tắc thành một mệnh đề kiểm được:

> Giá của mã `M` tại ngày `D` = bản ghi tại mốc `R ≤ D` gần nhất, HỢP LỆ khi và
> chỉ khi ĐÚNG NGÀY `D` có bản ngày.

Ngày `D` không có bản ngày ⇒ `SOURCE_UNAVAILABLE`. Bản ngày
`SOURCE_UNAVAILABLE` cố ý KHÔNG tính là ngày đã quan sát.

Mệnh đề này chỉ đúng nhờ một bất biến của phía ghi: **bản ngày chỉ được ghi khi
engine trả kết quả cho TOÀN BỘ mã của bảng giá** (`CHECK-R1-25`). Khi đó "ngày
`D` đã quan sát, mã `M` không có bản ghi mới" là bằng chứng TRỰC TIẾP rằng
trạng thái của `M` ở `D` bằng trạng thái tại `R`, và các ngày ở giữa không thêm
thông tin gì.

Bản đầu của R1 đòi mọi ngày trong `(R, D]` đều có bản ngày. Đã sửa trong lượt
kiểm thử: luật ấy khoá ngoài VĨNH VIỄN mọi mã giá ổn định chỉ vì lỡ một ngày —
mốc của chúng nằm trước chỗ đứt và chúng không bao giờ sinh mốc mới.

### 3.2. `PROVISIONAL`/`FINAL` nằm ở BẢN NGÀY, không ở từng bản ghi

Một bản ghi có thể có hiệu lực cho nhiều ngày (mốc mang qua), nên đặt cờ trên
nó sẽ khiến cùng một bản ghi vừa FINAL cho ngày này vừa PROVISIONAL cho ngày
kia — không có chỗ nào ghi nổi cả hai. Đặt ở bản ngày thì chốt là MỘT lệnh
ghi, idempotent, và mọi mã của ngày đó cùng trạng thái.

### 3.3. Fail-closed khi thiếu danh sách nhà cung cấp bị bỏ

Luật MIN cần danh sách nhà cung cấp bị ẩn/đã nghỉ/không tính Min. Danh sách ấy
sống ở trình duyệt Tracking (gộp từ ba nguồn, trong đó `NCC_ALIAS` chỉ có ở
đó). Thay vì chép ba danh sách sang Worker — dựng sẵn hai bản để chúng trôi
khỏi nhau, đúng vấp #5 — trình duyệt ĐĂNG danh sách lên `meta.an` kèm vân tay
`meta.k`, và Worker băm lại để đối chiếu.

Lệch vân tay hoặc thiếu `meta.an` ⇒ lượt chụp DỪNG và ghi bản ngày
`SOURCE_UNAVAILABLE`. Thà không có bản ghi hôm nay còn hơn một bản ghi tính
bằng danh sách sai — con số ấy sẽ trông hoàn toàn bình thường.

## 4. Hợp đồng `daily-min-v1`

Vị trí lưu và hình dạng đầy đủ: `src/min-ngay.js` (Tracking, docstring module)
và `app/modules/pricing/daily_min/snapshot.py` (Reports).

```text
Tracking  min_ngay/<mã>/<YYYY-MM-DD>   mốc đổi
          min_ngay_dau/<mã>            con trỏ bản ghi mới nhất
          min_ngay_ngay/<YYYY-MM-DD>   bản ngày + PROVISIONAL/FINAL
          min_ngay_sua/<mã>/<ngày>/<ev>  bản cũ sau khi sửa
          POST /api/min-ngay  (X-Report-Key, batch mã + khoảng ngày, phân trang)

Reports   tools/tracking/capture_daily_min.py   → data/tracking_daily_min/capture.json
          app/modules/pricing/daily_min/         → TrackingDailyMinProvider
```

Đơn vị tiền trong hợp đồng là `VND_THOUSAND` (đúng đơn vị Tracking lưu). Quy
đổi ×1000 xảy ra ĐÚNG MỘT LẦN, ở `daily_min/provider.py::_resolved`.

## 5. Completion Gate

| ID | Check | Priority | Evidence Level | Status |
|---|---|---|---|---|
| `CHECK-R1-01` | Engine trả nguồn thắng, kết quả GIÁ không đổi | REQUIRED | E1 | PASS |
| `CHECK-R1-02` | Bản ghi ngày và cột Min trên bảng là CÙNG một con số | REQUIRED | E1 | PASS |
| `CHECK-R1-03` | Sentinel `MIN = 0` không ra ngoài như một giá | REQUIRED | E1 | PASS |
| `CHECK-R1-04` | Nguồn thắng đủ (đồng giá giữ hết), thứ tự ổn định | REQUIRED | E1 | PASS |
| `CHECK-R1-05` | Min không đổi nhưng nguồn đổi ⇒ vẫn sinh bản ghi mới | REQUIRED | E1 | PASS |
| `CHECK-R1-06` | Chốt ngày idempotent, chỉ sau khi ngày kết thúc UTC+7 | REQUIRED | E1 | PASS |
| `CHECK-R1-07` | Ngày đã chốt bất biến với dữ liệu hiện tại | REQUIRED | E1 | PASS |
| `CHECK-R1-08` | Sửa bản ghi giữ bản cũ + lý do + revision mới | REQUIRED | E1 | PASS |
| `CHECK-R1-09` | Ngày bán KHÔNG có bản ngày ⇒ `SOURCE_UNAVAILABLE`, không lấp giá cũ | REQUIRED | E1 | PASS |
| `CHECK-R1-10` | Batch nhiều mã/ngày, phân trang phủ đủ, không trùng/sót | REQUIRED | E1 | PASS |
| `CHECK-R1-11` | Nhánh mới chỉ máy chủ ghi được (Firebase rules) | REQUIRED | E1 | PASS |
| `CHECK-R1-12` | Reports từ chối schema/đơn vị tiền lạ thay vì đọc sai | REQUIRED | E1 | PASS |
| `CHECK-R1-13` | Tra bằng `sale_date`; không lấy bản ngày khác | REQUIRED | E2 | PASS |
| `CHECK-R1-14` | Quy đổi nghìn VND → VND đúng MỘT lần | REQUIRED | E1 | PASS |
| `CHECK-R1-15` | `OUT_OF_STOCK`/`NO_DATA`/`SOURCE_UNAVAILABLE` Pending đúng mã | REQUIRED | E1 | PASS |
| `CHECK-R1-16` | `min_sources` + revision + rule version còn trong provenance | REQUIRED | E1 | PASS |
| `CHECK-R1-17` | `PROVISIONAL` giữ trạng thái, kỳ chưa được gọi là chốt | REQUIRED | E1 | PASS |
| `CHECK-R1-18` | `tp/ton` cũ KHÔNG được chọn làm MIN, kể cả khi nguồn mới trống | REQUIRED | E2 | PASS |
| `CHECK-R1-19` | Mọi dòng Pending có mục Review Queue canonical phủ | REQUIRED | E1 | PASS |
| `CHECK-R1-20` | Xuyên suốt: Tracking sinh → Reports đọc → giá nhập → lợi nhuận | REQUIRED | E2 | PASS |
| `CHECK-R1-21` | Dữ liệu cũ (`purchase_price_history`/`tp/ton`) giữ nguyên nghĩa | REQUIRED | E1 | PASS |
| `CHECK-R1-22` | Full regression hai repo không hỏng bài nào | REQUIRED | E1 | PASS |
| `CHECK-R1-23` | Owner nghiệm thu trên dữ liệu thật | REQUIRED | E2 | NOT_TESTED |
| `CHECK-R1-24` | Independent Review | REQUIRED | E2 | NOT_TESTED |
| `CHECK-R1-25` | Lượt chụp KHÔNG ghi bản ngày thành công khi engine không trả đủ mọi mã | REQUIRED | E1 | PASS |
| `CHECK-R1-26` | Mã bị gỡ khỏi bảng giá được đóng sổ ĐÚNG MỘT lần, không ghi lại mỗi ngày | REQUIRED | E1 | PASS |
| `CHECK-R1-27` | Sửa bản ghi với nguồn lệch trạng thái bị chặn ở CẢ HAI phía | REQUIRED | E1 | PASS |
| `CHECK-R1-28` | Reports từ chối `AVAILABLE` không nguồn và bản ghi ngoài khoảng đã khai | REQUIRED | E1 | PASS |
| `CHECK-R1-29` | Smoke xuyên hai hệ thống: ảnh chụp CÓ giá hiện tại mà giá vốn vẫn theo ngày bán | REQUIRED | E2 | PASS |

| `CHECK-R1-30` | Đường upload web GỌI hợp đồng và định giá đúng ngày bán | REQUIRED | E2 | PASS |
| `CHECK-R1-31` | Kế hoạch hỏi giá suy từ SỔ: tập mã đã resolve + khoảng ngày bán | REQUIRED | E1 | PASS |
| `CHECK-R1-32` | Chọn ảnh chụp theo KỲ, không theo "mới nhất toàn cục" | REQUIRED | E1 | PASS |
| `CHECK-R1-33` | Phong bì bắt buộc: timezone, `generated_at` có tz, `query_revision` | REQUIRED | E1 | PASS |
| `CHECK-R1-34` | Mọi bản ghi mang đủ dấu vết; error trong khoảng, không trùng | REQUIRED | E1 | PASS |
| `CHECK-R1-35` | Cổng hoàn tất cấp kỳ khác cờ "giá đã chốt" | REQUIRED | E1 | PASS |
| `CHECK-R1-36` | Trang lệch `query_revision` bị TỪ CHỐI gộp | REQUIRED | E1 | PASS |

| `CHECK-R1-37` | Lần chạy hỏng KHÔNG để lại capture tạm trên đĩa | REQUIRED | E1 | PASS |
| `CHECK-R1-38` | Đọc lạc quan hai đầu; con trỏ mang revision | REQUIRED | E1 | PASS |
| `CHECK-R1-39` | Chọn ảnh chụp theo TỪNG CẶP `(mã, ngày)`, không chỉ khoảng ngày | REQUIRED | E1 | PASS |
| `CHECK-R1-40` | Kỳ rộng hơn hợp đồng: chia đoạn + gộp cùng revision, hoặc TỪ CHỐI | REQUIRED | E2 | PASS |
| `CHECK-R1-41` | Sự cố nhánh `tp/ton` LEGACY không chặn báo cáo R1 | REQUIRED | E2 | PASS |

`CHECK-R1-37` … `CHECK-R1-41` được THÊM ở lượt Independent Review vòng 2
(07/09/2026). `CHECK-R1-40` là check đáng chú ý nhất: bản trước bỏ qua lượt hỏi
giá khi kỳ quá rộng, nên lần chạy vẫn ra một báo cáo đầy đủ hình thức mà không
một giá vốn nào — kết cục tệ hơn cả một lỗi, vì nó trông giống thành công.

`CHECK-R1-30` … `CHECK-R1-36` được THÊM ở lượt Independent Review vòng 1
(07/09/2026). `CHECK-R1-30` là check quan trọng nhất của cả bảng: trước nó,
`CHECK-R1-20` (xuyên suốt) PASS bằng một fixture cho sẵn, trong khi đường
upload thật KHÔNG hề gọi hợp đồng — mọi bài kiểm xanh, đường thật đứt.

`CHECK-R1-25` … `CHECK-R1-29` được THÊM trong phiên kiểm thử (07/09/2026), không
phải lúc lập kế hoạch: bốn lỗi đầu chỉ lộ ra khi đi soát từng nhánh có thể cho
ra "một con số hợp lệ nhưng sai", và cả bốn đều đã được sửa trong cùng phiên.
`CHECK-R1-25` là điều kiện mà luật mang mốc qua ngày (`ADR-110` §2) DỰA VÀO —
nếu một lượt chụp hỏng vẫn ghi được bản ngày thì bản ngày không còn chứng minh
được điều gì.

Evidence Level:
E1 = lệnh đã chạy, output trích nguyên văn ở `docs/sessions/S126-r1-daily-min-theo-ngay-ban.md`.
E2 = bài kiểm chạy trên đường production thật với dữ liệu do chính hệ thống kia sinh ra.

Executed By:
Claude Code session S126

Timestamp:
2026-09-07

## 6. Exit Criteria

1. `CHECK-R1-01` … `CHECK-R1-22` và `CHECK-R1-25` … `CHECK-R1-41` PASS —
   **đã đạt**.
2. `CHECK-R1-24` Independent Review PASS — **chưa**.
3. `CHECK-R1-23` Owner nghiệm thu sau lượt chụp đầu tiên trên dữ liệu thật —
   **chưa**.

`R1` KHÔNG được đánh dấu `DONE` khi (2) hoặc (3) còn `NOT_TESTED`. Test đơn vị
đạt hết KHÔNG phải điều kiện đủ (brief §11 câu cuối).

## 7. Khoảng trống ĐÃ BIẾT, ghi ra chứ không im lặng

| Khoảng trống | Vì sao | Hệ quả hôm nay |
|---|---|---|
| Lịch sử MIN bắt đầu từ lượt chụp đầu tiên | Bảng giá cũ đã bị ghi đè; `tp/ton` là đại lượng khác nên KHÔNG backfill được | Đơn bán trước mốc ấy Pending, hoặc dùng `HistoricalConfirmedRegistry` |
| ~~Đường web pull-on-run chưa lấy MIN theo ngày~~ **ĐÃ ĐÓNG 07/09/2026** | `live_pull.py` nay tự lập kế hoạch: đọc sổ → resolve identity → tập mã + khoảng ngày, rồi gọi hợp đồng MỘT lượt | Không còn; `CHECK-R1-30`/`CHECK-R1-31` canh |
| ~~Kỳ rộng hơn 62 ngày không hỏi được trong MỘT lượt~~ **ĐÃ ĐÓNG 07/09/2026 (vòng 2)** | Trần `TRAN_NGAY_XUAT` của hợp đồng | Kỳ nay được CHIA thành các đoạn ≤ 62 ngày và chỉ gộp khi mọi đoạn cùng `query_revision`; rộng quá trần đoạn mỗi lần chạy (12 ≈ hai năm) thì TỪ CHỐI kèm hướng dẫn tách kỳ. `CHECK-R1-40` |
| Database đổi giữa các đoạn của một kỳ rộng | Không có giao dịch đọc nhất quán ở tầng database | Lần chạy TỪ CHỐI gộp và báo "Tracking đang lỗi" — thử lại thật sự có tác dụng, vì đây là sự cố thoáng qua (một lượt cron chạy đúng lúc) |
| Lượt chụp cần `meta.an` | Danh sách nhà cung cấp bị bỏ sống ở trình duyệt | Chưa ai mở app Bảng giá kể từ bản này ⇒ bản ngày `SOURCE_UNAVAILABLE`; tự khỏi ngay lần mở đầu tiên |
| Ảnh chụp gắn với một kỳ | Khác hai capture kia vốn "chụp một lần dùng mãi" | Luồng cục bộ nay chọn ảnh chụp PHỦ ĐÚNG kỳ (`CHECK-R1-32`); không có thì Pending kèm lý do |
| `query_revision` chỉ chặn được lượt ghi ĐÃ xảy ra khi đọc | Không có giao dịch đọc nhất quán ở tầng database | Ảnh ghép luôn bị từ chối (đọc lạc quan hai đầu + con trỏ mang revision); ngược lại, một lượt ghi xảy ra sau lệnh đọc cuối cùng không bị phát hiện — đúng như vậy, vì nó không ảnh hưởng ảnh chụp đã lấy |
| Ảnh chụp cục bộ phải trả lời được TỪNG CẶP `(mã, ngày)` | Phong bì hợp đồng không liệt kê tập mã đã hỏi, nên phải suy từ nội dung | Một ảnh chụp thiếu đúng một cặp bị loại; đúng như vậy — một dòng thiếu giữa một bảng đủ là thứ dễ trôi qua nhất khi đọc |

## 8. Đầu vào cho R2

- `TrackingDailyMinProvider.audit_trail` và `PriceResolutionRecord.daily_min_resolution`
  đã chở đủ `min_sources`, revision, rule version, `day_status`, `carried_from`
  cho màn hình/xuất Excel của vòng sau.
- `PriceResolutionReport.period_is_final` (có dữ liệu + không Pending + không
  PROVISIONAL) là cổng "kỳ đã chốt"; `resolved_prices_are_final` /
  `provisional_count` là hai chỉ số hẹp hơn đi kèm. R1 cố ý KHÔNG tự gắn cổng
  ấy vào một màn hình nào.
- `POST /api/min-ngay/sua` (admin) là đường sửa bản ghi có dấu vết; luồng giá
  tay của Owner (R2) nên đi qua tầng override đã có
  (`kpi_purchase_price_override`), KHÔNG ghi vào nhánh MIN.
- ~~Nối `live_pull.py`~~ — ĐÃ LÀM ở lượt review vòng 1; phần còn lại cho R2 là
  chia một kỳ rộng hơn 62 ngày thành nhiều lượt gọi mà vẫn giữ được MỘT
  `query_revision` chung cho cả ảnh chụp.
- (bản cũ, giữ để đối chiếu) Nối `live_pull.py`: tập mã lấy từ identity đã resolve, khoảng ngày lấy từ
  preview của sổ — cả hai đã có sẵn trong pipeline, chỉ cần đảo thứ tự gọi.
