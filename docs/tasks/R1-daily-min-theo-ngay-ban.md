# R1 — Giá MIN theo ngày bán (Tracking sở hữu, Reports tiêu thụ)

## Metadata

Status:
IMPLEMENTED

Current Status Reason:
Toàn bộ phạm vi R1 đã triển khai và có bằng chứng E1/E2 trên cả hai repo, kể
cả đường xuyên suốt Tracking → hợp đồng → Reports → giá nhập → lợi nhuận. Còn
chờ đúng hai việc trước khi `DONE`: (1) một lượt Independent Review, (2) Owner
nghiệm thu trên dữ liệu thật sau khi chạy lượt chụp đầu tiên. Triển khai
production KHÔNG thuộc R1 (brief §2).

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
> chỉ khi MỌI ngày trong khoảng `(R, D]` đều có bản ngày.

Thiếu một ngày trong chuỗi ⇒ `SOURCE_UNAVAILABLE`. Bản ngày
`SOURCE_UNAVAILABLE` cố ý KHÔNG tính là ngày đã quan sát.

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
| `CHECK-R1-09` | Thiếu bản ngày ⇒ `SOURCE_UNAVAILABLE`, không lấp giá cũ | REQUIRED | E1 | PASS |
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

Evidence Level:
E1 = lệnh đã chạy, output trích nguyên văn ở `docs/sessions/S126-r1-daily-min-theo-ngay-ban.md`.
E2 = bài kiểm chạy trên đường production thật với dữ liệu do chính hệ thống kia sinh ra.

Executed By:
Claude Code session S126

Timestamp:
2026-09-07

## 6. Exit Criteria

1. `CHECK-R1-01` … `CHECK-R1-22` PASS — **đã đạt**.
2. `CHECK-R1-24` Independent Review PASS — **chưa**.
3. `CHECK-R1-23` Owner nghiệm thu sau lượt chụp đầu tiên trên dữ liệu thật —
   **chưa**.

`R1` KHÔNG được đánh dấu `DONE` khi (2) hoặc (3) còn `NOT_TESTED`. Test đơn vị
đạt hết KHÔNG phải điều kiện đủ (brief §11 câu cuối).

## 7. Khoảng trống ĐÃ BIẾT, ghi ra chứ không im lặng

| Khoảng trống | Vì sao | Hệ quả hôm nay |
|---|---|---|
| Lịch sử MIN bắt đầu từ lượt chụp đầu tiên | Bảng giá cũ đã bị ghi đè; `tp/ton` là đại lượng khác nên KHÔNG backfill được | Đơn bán trước mốc ấy Pending, hoặc dùng `HistoricalConfirmedRegistry` |
| Đường web pull-on-run chưa lấy MIN theo ngày | `live_pull.py` không biết tập mã của kỳ — chỉ có sau khi resolve identity | Bản web trả Pending nhánh Tracking cho tới khi nối (R2) hoặc Owner chạy công cụ chụp |
| Lượt chụp cần `meta.an` | Danh sách nhà cung cấp bị bỏ sống ở trình duyệt | Chưa ai mở app Bảng giá kể từ bản này ⇒ bản ngày `SOURCE_UNAVAILABLE`; tự khỏi ngay lần mở đầu tiên |
| Ảnh chụp gắn với một kỳ | Khác hai capture kia vốn "chụp một lần dùng mãi" | Đầu vào TUỲ CHỌN của luồng Owner; vắng mặt ⇒ Pending có lý do |

## 8. Đầu vào cho R2

- `TrackingDailyMinProvider.audit_trail` và `PriceResolutionRecord.daily_min_resolution`
  đã chở đủ `min_sources`, revision, rule version, `day_status`, `carried_from`
  cho màn hình/xuất Excel của vòng sau.
- `PriceResolutionReport.prices_are_final` / `provisional_count` sẵn cho cổng
  "kỳ đã chốt" — R1 cố ý KHÔNG tự gắn nó vào một cổng UI nào.
- `POST /api/min-ngay/sua` (admin) là đường sửa bản ghi có dấu vết; luồng giá
  tay của Owner (R2) nên đi qua tầng override đã có
  (`kpi_purchase_price_override`), KHÔNG ghi vào nhánh MIN.
- Nối `live_pull.py`: tập mã lấy từ identity đã resolve, khoảng ngày lấy từ
  preview của sổ — cả hai đã có sẵn trong pipeline, chỉ cần đảo thứ tự gọi.
