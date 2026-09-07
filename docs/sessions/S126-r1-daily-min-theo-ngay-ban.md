# S126 — Bàn giao R1: Giá MIN theo ngày bán

Phiên IMPLEMENTATION + KIỂM THỬ, hai repo. Owner authority: `R1 Execution
Brief — Giá MIN theo ngày bán` (2026-09-07). Quyết định: `DEC-199`. Kiến trúc:
`ADR-110`. Task canonical: `docs/tasks/R1-daily-min-theo-ngay-ban.md`.

File này gộp BA lượt của cùng một phiên:

| Lượt | Nội dung | Mục |
|---|---|---|
| 1 — triển khai | toàn bộ phạm vi R1 theo brief | 1–4 |
| 2 — kiểm thử/sửa lỗi | bảy chỗ sửa, không chỗ nào ném ngoại lệ | 5.1, 6 |
| 3 — Independent Review vòng 1 | sáu finding của bên review | **11** |
| 4 — Independent Review vòng 2 | năm finding, review CHƯA ACCEPT | **12** |

Điểm chung của cả ba: mọi lỗi tìm được đều cho ra một con số tiền trông hoàn
toàn bình thường thay vì một ngoại lệ. Riêng lượt 3 tìm được lỗi TỆ NHẤT của
cả phiên — đường upload web KHÔNG hề gọi hợp đồng giá, trong khi 2.776 bài
kiểm đều xanh.

**SHA đầy đủ và gói cho reviewer nằm ở mục 11.5, cập nhật ở mục 12.5.**

---

## 1. Hai repo, nhánh, và HEAD đã kiểm

```text
Reports   github.com/hoangvinhkta-creator/Reports
          nhánh mặc định : claude/extract-upload-repo-gq2ws4
          nhánh làm việc : claude/kiem-tra-tham-chieu-gia-nhap-c57d7z
          BASE_HEAD      : a4c00501d559bda8ec70d8fe1dc1f8e54b46d592
          ahead/behind default trước khi sửa: 0 / 0

Tracking  github.com/hoangvinhkta-creator/Tracking
          nhánh mặc định : main
          nhánh làm việc : claude/kiem-tra-tham-chieu-gia-nhap-c57d7z
          BASE_HEAD      : 598b4b1390cc96e552455ab85e2c48d78198b89c
          (nhánh làm việc đã có sẵn 3 commit trên `main`, giữ nguyên)
```

Commit của R1 trên nhánh làm việc, theo thứ tự:

```text
Tracking  01f505c  R1: MIN theo ngày bán — Tracking sở hữu giá, xuất theo
                   hợp đồng daily-min-v1
          f294edb  R1: ghi nhật ký tiến độ cho MIN theo ngày bán
          6232ce0  R1: chốt fail-closed cho chụp MIN ngày + sửa luật mang
                   mốc qua ngày            ← lượt kiểm thử
          (đã đẩy lên origin: f294edb..6232ce0)

Reports   2b669f5  R1: giá nhập tự động là MIN theo ngày bán, đọc qua hợp
                   đồng daily-min-v1
          + commit mang chính bản bàn giao này  ← lượt kiểm thử
```

`scripts/branch_authority_check.sh` (Reports) sau khi đặt upstream:

```text
AUTHORITY            : BRANCH_WITH_UPSTREAM
RESULT               : AUTHORITY_OK
DIVERGENCE           : WITHIN_LIMITS
```

Lần chạy ĐẦU TIÊN của script này trả `STOP — BRANCH AUTHORITY UNRESOLVED`
(nhánh chưa có upstream trên origin — nó đã bị prune). Đã xử lý đúng cách
script chỉ dẫn: `git push -u origin <nhánh>`, rồi chạy lại. Ghi ra đây vì một
`STOP` bị bỏ qua là chỗ mọi sai lệch nhánh bắt đầu.

## 2. Quy tắc giá ngày cuối cùng đã dùng

```text
Giá nhập tự động của một mã Tracking tại ngày bán D
  = MIN của ngày D, do engine Tracking tính (minCuaDong),
    lấy từ bản ghi tại mốc R ≤ D gần nhất,
    HỢP LỆ khi và chỉ khi ĐÚNG NGÀY D có BẢN NGÀY.
    (Bản ngày chỉ được ghi khi engine trả kết quả cho TOÀN BỘ mã của bảng,
     nên "ngày D đã quan sát, mã M không có bản ghi mới" LÀ bằng chứng
     rằng M không đổi giá. Các ngày ở giữa không thêm thông tin.)

MIN = rẻ nhất trong:
        · giá các nhà cung cấp còn hàng, sau khi loại danh sách bị ẩn/nghỉ/
          không-tính-Min và sau bộ lọc giá thấp bất thường (< 30% giá kế tiếp)
        · ô Tồn Tín Phát khi nó dương
Không có nguồn nào bán được, nhưng đã từng có → OUT_OF_STOCK  (giá null)
Chưa nhà cung cấp nào đụng tới mã                → NO_DATA       (giá null)
Ngày bán không có bản ngày                       → SOURCE_UNAVAILABLE
```

Bốn điều KHÔNG có, và cố ý không có:

- không lấy bản của ngày sau ngày bán;
- không lấy giá tại thời điểm nạp sổ;
- không rơi về lịch sử `board/<mã>/tp/ton`;
- không biến `MIN = 0` (sentinel hết hàng) thành giá vốn 0.

`PROVISIONAL` (ngày chưa kết thúc) vẫn cho ra giá, nhưng trạng thái đi kèm con
số suốt đường; kỳ còn dùng bản tạm thì
`PriceResolutionReport.resolved_prices_are_final` là `False`. (Cờ ấy tên là
`prices_are_final` cho tới lượt review vòng 1 — xem §11.1 finding #4; cổng
hoàn tất cấp kỳ là `period_is_final`, khắt khe hơn.)

## 3. Contract / schema và vị trí lưu

Hợp đồng `daily-min-v1`. Đơn vị tiền `VND_THOUSAND` (đúng đơn vị Tracking
lưu); quy đổi ×1000 sang VND xảy ra ĐÚNG MỘT LẦN, ở
`app/modules/pricing/daily_min/provider.py::_resolved`.

```text
Tracking (Firebase RTDB — cả bốn nhánh: client .write = false)
  min_ngay/<mã>/<YYYY-MM-DD>       {g, ts, ng?, rv, fp, t, by, ev, bt?}
  min_ngay_dau/<mã>                {d, fp, ev}
  min_ngay_ngay/<YYYY-MM-DD>       {t, tDau, ds, n, nGhi, by, rv, k, ly?}
  min_ngay_sua/<mã>/<ngày>/<ev>    bản ghi CŨ, giữ nguyên vẹn

Tracking (HTTP)
  POST /api/min-ngay        X-Report-Key · batch {product_codes, date_from,
                            date_to, cursor?} · trần 100 mã/trang, 62 ngày
  POST /api/min-ngay/chup   admin — chụp tay ngày hôm nay
  POST /api/min-ngay/chot   admin — chốt tay một ngày đã kết thúc
  POST /api/min-ngay/sua    admin — sửa một bản ghi, có lý do + revision mới
  cron "*/20 * * * *"       chốt ngày đã qua rồi chụp ngày hôm nay

Reports
  tools/tracking/capture_daily_min.py  → data/tracking_daily_min/capture.json
  app/modules/pricing/daily_min/{snapshot,capture_file,provider}.py
  price_source = "TRACKING_DAILY_MIN"
```

## 4. File đã thay đổi

### Tracking (commit `01f505c`, sửa tiếp ở `6232ce0`)

| File | Nội dung |
|---|---|
| `price-engine/src/nghiepvu.js` | `nguonGiuMin()`; `minCuaDong()` trả thêm nguồn; `tinhMinNgay()`; `TON_KHO`, `PHIEN_BAN_MIN`, `TRANG_THAI_GIA`. `PHIEN_BAN` GIỮ `pe-6` — kết quả giá không đổi |
| `price-engine/src/index.js` | RPC `tinhMinNgay()` |
| `src/min-ngay.js` | **mới** — chụp/chốt/sửa/xuất, bản ngày, vân tay đầu vào. `6232ce0`: bốn chốt fail-closed trong `chupMinNgay`, đóng sổ mã bị gỡ khỏi bảng, kiểm nguồn trong `suaBanGhi`, và luật mang mốc qua ngày viết lại theo quan sát TRỰC TIẾP |
| `src/index.js` | `xuatMinChoReports()`, ba route admin, cron thứ ba, `CRON_MIN_NGAY` |
| `public/index.html` | `congBoVanTay()` đăng thêm `meta.an` (danh sách NCC bị bỏ, dạng chuỗi) |
| `firebase-database.rules.json` | bốn nhánh mới: đọc như nhánh giá nhập cũ, GHI = false |
| `wrangler.toml` | cron thứ ba `*/20 * * * *` |
| `kiem/min-ngay.js` | **mới** — 93 bài; `6232ce0` thêm khối 15b–15e → **111 bài** |
| `kiem/smoke/xuat-thang-min.mjs` | **mới** (`6232ce0`) — bước 1/2 của smoke xuyên hai hệ thống: dựng cả tháng 09/2026 bằng chính mã thật rồi xuất `daily-min-v1`. KHÔNG nằm trong `npm test` |
| `kiem/chay.js` | vá: bộ TRƯỢT có cảnh báo stderr từng bị báo là "bỏ qua" |
| `kiem/day-ton-sheet.js` | canh hành vi rẽ nhánh cron thay vì hình dạng ba ngôi |

### Reports

| File | Nội dung |
|---|---|
| `app/modules/pricing/daily_min/` | **mới** — `snapshot.py`, `capture_file.py`, `provider.py`, `__init__.py` |
| `tools/tracking/capture_daily_min.py` | **mới** — client batch, đọc hết trang, kiểm phong bì khớp nhau |
| `app/modules/domain/models.py` | `PRICE_SOURCE_TRACKING_DAILY_MIN` |
| `app/modules/pricing/resolution/sources.py` | nguồn + đường dẫn + evidence + cờ `legacy_tracking_history_authority` |
| `app/modules/pricing/resolution/composition.py` | nhánh `_daily_min_branch`, `CompositionRule.TRACKING_DAILY_MIN`, hai reason mới, `report`/`prices_are_final` (đổi tên ở §11) |
| `app/demo.py`, `app/owner_usability.py` | đầu vào `tracking_daily_min` (TUỲ CHỌN) + cờ CLI |
| `app/modules/exporting/excel_exporter.py` | hai cột provenance trỏ về nguồn ĐÃ QUYẾT ĐỊNH |
| `app/beta_presentation.py`, `app/modules/reporting/profit_gate.py` | hai mã lý do mới |
| `tools/analysis/validate_post_cutover.py` | tham số `tracking_daily_min` + `legacy_tracking_history_authority` |
| `tests/support/daily_min_fixtures.py` | **mới** |
| `tests/test_daily_min_contract.py` | **mới** — 38 bài; lượt kiểm thử thêm 3 bài cho `available_without_sources`, `missing_status_with_sources`, `record_outside_declared_range` → **41 bài** |
| `tests/test_daily_min_vertical.py` | **mới** — 18 bài, chạy trên fixture do Tracking sinh |
| `app/modules/pricing/daily_min/snapshot.py` | lượt kiểm thử: thêm hai bất biến — `AVAILABLE` bắt buộc có nguồn, và bản ghi phải nằm TRONG khoảng chụp đã khai |
| `tools/smoke/r1_daily_min_smoke.py` | **mới** — bước 2/2 của smoke: nạp ảnh chụp qua loader production, chạy đường nhập sổ thật, in giá vốn từng đơn kèm provenance |
| `tests/fixtures/daily_min/tracking_contract_export.json` | **mới** — sinh bằng chính mã Tracking |
| `tests/test_105e_price_composition.py`, `tests/test_post_cutover_validation.py`, `tests/test_demo.py`, `tests/test_sales_presentation.py` | ghim nhánh legacy / chuyển sang nguồn mới / cập nhật vũ trụ mã đóng |
| governance | `ADR-110`, `DEC-199`, task R1, ledger, `PROJECT/PROJECT_PROGRESS.md` |

**Migration: KHÔNG CÓ.** Không backfill, không đổi nhãn dữ liệu cũ, không
migration database bên Reports.

## 5. Test, build, validator — kết quả chính xác

Lệnh chạy nguyên văn, thư mục gốc từng repo:

```text
Tracking   npm test
           npm run build
           node kiem/smoke/xuat-thang-min.mjs <file.json>

Reports    python -m pytest -q
           python governance/scripts/governance/validate_structure.py
           python governance/scripts/governance/validate_project_state.py
           python governance/scripts/governance/validate_evidence.py
           python governance/scripts/governance/validate_task_completion.py
           python governance/scripts/governance/validate_reference_integrity.py
           python tools/smoke/r1_daily_min_smoke.py <file.json> <thư-mục-tạm>
```

Kết quả:

```text
Tracking  npm test   (nền R1)     59 bộ · 2594 đạt · 0 hỏng · 2 bỏ qua
          npm test   (sau triển)  60 bộ · 2687 đạt · 0 hỏng · 2 bỏ qua
          npm test   (sau kiểm)   60 bộ · 2705 đạt · 0 hỏng · 2 bỏ qua
          npm run build           "Đã dựng bản phục vụ vào ./dist
                                   7 file, xén chú thích 1 file HTML
                                   658 KB → 411 KB  (bớt 37%)"

Reports   pytest -q  (nền R1)     2720 passed, 12 skipped in 143.78s
          pytest -q  (sau triển)  2776 passed, 12 skipped in 147.83s
          pytest -q  (sau kiểm)   2779 passed, 12 skipped in 153.28s
          bài mới tổng cộng: 111 (Tracking, bộ min-ngay) + 59 (Reports, hai
          bộ daily_min) — chưa kể các bài đã có được cập nhật

Governance validator (Reports, chạy lại SAU lượt kiểm thử)
          validate_structure          PASS  (21 required paths)
          validate_project_state      PASS
          validate_evidence           PASS  (161 REQUIRED PASS)
          validate_task_completion    PASS  (14 DONE task)
          validate_reference_integrity FAIL — ĐÚNG 3 reference TASK-REM-T06
                                      đã biết (/README.md, CODE_OF_CONDUCT.md,
                                      CONTRIBUTING.md). Baseline KHÔNG đổi:
                                      R1 không thêm reference hỏng nào.
```

`scripts/branch_authority_check.sh` → `AUTHORITY_OK / WITHIN_LIMITS`
(chi tiết ở mục 1).

**Không có mục NOT_TESTED nào vì lý do môi trường.** Cả hai bộ test, build, cả
năm validator và cả hai bước smoke đều chạy được trong phiên. Hai check còn
`NOT_TESTED` trong Completion Gate (`CHECK-R1-23` nghiệm thu trên dữ liệu thật,
`CHECK-R1-24` Independent Review) là NGƯỜI phải làm, không phải lệnh — chúng
không thể "chạy" ở đây và không được tính là PASS.

### 5.1 Lượt kiểm thử: bảy chỗ sửa, và vì sao từng chỗ nguy hiểm

Một bộ kiểm xanh không chứng minh mã đúng; nó chứng minh mã đúng ở những chỗ
đã nghĩ ra để hỏi. Lượt này đi soát riêng một câu hỏi: **chỗ nào có thể ra một
con số tiền hợp lệ nhưng SAI, mà không có gì đỏ lên?** Bảy chỗ tìm được:

| # | Chỗ | Nếu để nguyên | Đã sửa |
|---|---|---|---|
| 1 | `chupMinNgay` báo thành công khi engine không trả gì (bảng rỗng / sai hình dạng / thiếu mã) | Bản ngày là BẰNG CHỨNG cho phép mang mốc cũ qua. Một lượt chụp hỏng tự cấp phép cho mình phát giá cũ, im lặng, không giới hạn thời gian | Dừng, ghi bản ngày `SOURCE_UNAVAILABLE` kèm lý do |
| 2 | Mã bị gỡ khỏi bảng giá không được đóng sổ | Mốc cuối ở lại, mọi ngày sau mang qua như thể giá còn nguyên | Ghi ĐÚNG MỘT mốc `NO_DATA`, vân tay `ROI-BANG` (cố ý không kèm ngày) |
| 3 | `suaBanGhi` nhận nguồn lệch trạng thái | Reports từ chối NGUYÊN ảnh chụp — một lần sửa nhầm hỏng cả kỳ | Chặn tại chỗ sửa: `nguon-tren-trang-thai-khong-co-gia`, `thieu-nguon-cho-gia` |
| 4 | Bản ngày hỏng không được xoá lý do khi chụp lại thành công trong ngày | Ngày đã lành vẫn mang nhãn hỏng | Lượt chụp thành công ghi `ly: null` |
| 5 | Luật mang mốc qua ngày đòi MỌI ngày trong `(R, D]` có bản ngày | Lỡ MỘT ngày là mọi mã giá ổn định bị khoá ngoài VĨNH VIỄN — mốc của chúng nằm trước chỗ đứt và không bao giờ có mốc mới | Mốc tại `R ≤ D` hợp lệ cho `D` khi và chỉ khi ĐÚNG NGÀY `D` có bản ngày. Đúng được là NHỜ mục 1 ở trên |
| 6 | Reports nhận `AVAILABLE` mà `min_sources` rỗng | Con số đi hết vào giá vốn nhưng câu "vì sao là 6.800, mua của ai" mất câu trả lời | Từ chối lúc nạp: `available_without_sources` |
| 7 | Reports nhận bản ghi có ngày NGOÀI khoảng phong bì đã khai | Không sinh giá sai (`covers()` chặn trước), nhưng nói ảnh chụp ghép từ hai lần chụp khác nhau ⇒ mất tính tái lập | Từ chối lúc nạp: `record_outside_declared_range` |

Ba điểm cần nói thẳng về lượt sửa này:

- **Chỗ #5 là sửa LUẬT, không phải vá lỗi.** Luật cũ được viết trong cùng
  phiên, đã có hai bài kiểm ghim nó, và hai bài ấy đã được VIẾT LẠI kèm chú
  thích nêu lý do. Đây là chỗ duy nhất trong phiên có bài kiểm bị đổi mong đợi
  — ghi ra để người review kiểm đúng chỗ ấy trước.
- **Chỗ #5 phụ thuộc chỗ #1.** Luật mới chỉ đúng chừng nào bản ngày còn chứng
  minh được "engine đã trả kết quả cho TOÀN BỘ mã". Ai gỡ chốt fail-closed ở
  `chupMinNgay` là gỡ luôn nền của luật đọc. Đã ghi vào `ADR-110` §2.
- **Một lỗi trong chính bản sửa** đã bị bài kiểm mới bắt: vân tay đóng sổ ban
  đầu là `"ROI-BANG:" + ngày`, khiến mã đã gỡ bị ghi lại MỖI NGÀY. Sửa thành
  vân tay không phụ thuộc ngày.

Ngoài ra, một lỗ hổng BẰNG CHỨNG đã được vá ở lượt triển khai và nhắc lại đây
vì nó là loại lỗi làm mọi con số phía trên mất giá trị: `kiem/chay.js` chỉ đọc
DÒNG CUỐI của đầu ra để tìm dòng tổng kết. Một bộ TRƯỢT kèm cảnh báo stderr thì
dòng cuối không còn là dòng ấy, và nhánh dự phòng `/BỎ QUA/` khớp trúng tên một
bài — bộ hỏng được báo là "bỏ qua", tổng vẫn "0 hỏng", CI vẫn xanh. Đã xảy ra
thật trong phiên này với `day-ton-sheet.js` (2 bài hỏng).

## 6. Smoke — bằng chứng nguyên văn

Smoke đi qua CẢ HAI hệ thống, không dùng fixture của bộ kiểm:

```text
bước 1/2  (Tracking)  node kiem/smoke/xuat-thang-min.mjs <file.json>
bước 2/2  (Reports)   python tools/smoke/r1_daily_min_smoke.py <file.json> <tmp>
```

Kịch bản dựng đúng câu Owner hỏi: **đơn bán 03/09, sổ nạp 30/09.** Hai cái bẫy
được cài SẴN để một lỗi im lặng phải lộ ra thành con số:

- ảnh chụp CÓ giá của ngày 30/09 (`5.200` nghìn) — nhánh nào lấy "bản mới
  nhất" sẽ ra `5.200.000`;
- nguồn lịch sử `tp/ton` cũ CÓ MẶT và CÓ GIÁ (`4.444` nghìn) cho đúng những mã
  ấy — nhánh nào rơi về nguồn cũ sẽ ra `4.444.000`.

Bước 1/2 — Tracking sinh ảnh chụp bằng chính mã thật:

```text
TRACKING → capture: records=140 errors=0 window=2026-09-03..2026-09-30 unit=VND_THOUSAND tz=Asia/Ho_Chi_Minh
  TRK-A 2026-09-03 -> {"min_price":6800,"day_status":"FINAL","sources":[{"source_type":"SUPPLIER","source_id":"Tuấn Ngoan"}]}
  TRK-A 2026-09-04 -> {"min_price":6000,"day_status":"FINAL","sources":[{"source_type":"SUPPLIER","source_id":"Tuấn Ngoan"}]}
  TRK-A 2026-09-30 -> {"min_price":5200,"day_status":"PROVISIONAL","sources":[{"source_type":"SUPPLIER","source_id":"Tuấn Ngoan"}]}
  TRK-B 03/09 nguồn -> [{"source_type":"INVENTORY","source_id":"TON_KHO"}]
  TRK-C 03/09 -> {"p":null,"s":"OUT_OF_STOCK"}
  TRK-D 03/09 -> {"p":null,"s":"NO_DATA"}
  TRK-E 03/09 -> {"p":9500,"loai":[{"source_type":"SUPPLIER","source_id":"Đất Việt","price":150,"reference_price":9500,"rule":"ABNORMAL_LOW"}]}
```

Bước 2/2 — Reports nạp ảnh chụp ấy và chạy đường nhập sổ thật:

```text
CAPTURE  id=DMIN-20260930T120000Z-smoke001 captured_at=2026-09-30T12:00:00+00:00 status=COMPLETE
SỔ BÁN   ngày bán = 2026-09-03, kỳ sổ 01/09–30/09 (nạp cuối tháng)

[BH7001] TRK-A
   giá nhập kế toán = Decimal('6800000')   lợi nhuận = Decimal('2200000')
   price_source     = TRACKING_DAILY_MIN   rule = TRACKING_DAILY_MIN   reason = None
   provenance       = sale_date=2026-09-03 observed=2026-09-03 carried_from=None day_status=FINAL
                      nguồn=['SUPPLIER:Tuấn Ngoan'] raw=6800 nghìn → 6800000 VND rv=min-1 fp=cc441b8f9291f407
                      capture_id=DMIN-20260930T120000Z-smoke001

[BH7002] TRK-B
   giá nhập kế toán = Decimal('5000000')   lợi nhuận = Decimal('4000000')
   price_source     = TRACKING_DAILY_MIN   rule = TRACKING_DAILY_MIN   reason = None
   provenance       = sale_date=2026-09-03 observed=2026-09-03 carried_from=None day_status=FINAL
                      nguồn=['INVENTORY:TON_KHO'] raw=5000 nghìn → 5000000 VND rv=min-1 fp=67073e4d9f134d10
                      capture_id=DMIN-20260930T120000Z-smoke001

[BH7003] TRK-C
   giá nhập kế toán = None   lợi nhuận = None
   price_source     = Pending   rule = NOT_RESOLVED   reason = TRACKING_DAILY_MIN_PENDING
   provenance       = sale_date=2026-09-03 observed=2026-09-03 carried_from=None day_status=FINAL
                      nguồn=[] raw=None nghìn → None VND rv=min-1 fp=1605bc745c8d4d5f
                      capture_id=DMIN-20260930T120000Z-smoke001

[BH7004] TRK-D
   giá nhập kế toán = None   lợi nhuận = None
   price_source     = Pending   rule = NOT_RESOLVED   reason = TRACKING_DAILY_MIN_PENDING
   provenance       = sale_date=2026-09-03 observed=2026-09-03 carried_from=None day_status=FINAL
                      nguồn=[] raw=None nghìn → None VND rv=min-1 fp=1c2c8a86896d3561
                      capture_id=DMIN-20260930T120000Z-smoke001

[BH7005] TRK-E
   giá nhập kế toán = Decimal('9500000')   lợi nhuận = Decimal('2500000')
   price_source     = TRACKING_DAILY_MIN   rule = TRACKING_DAILY_MIN   reason = None
   provenance       = sale_date=2026-09-03 observed=2026-09-03 carried_from=None day_status=FINAL
                      nguồn=['SUPPLIER:Tuấn Ngoan'] raw=9500 nghìn → 9500000 VND rv=min-1 fp=82cf3dc593b66db8
                      capture_id=DMIN-20260930T120000Z-smoke001

=== KHẲNG ĐỊNH SMOKE ===
  PASS  A. đơn 03/09 nạp 30/09 → 6.800.000 (giá NGÀY BÁN)
  PASS  A. KHÔNG lấy giá hiện tại 30/09 (5.200.000)
  PASS  A. KHÔNG lấy giá ngày 04/09 (6.000.000)
  PASS  A. KHÔNG rơi về lịch sử tp/ton cũ (4.444.000)
  PASS  A. nguồn thắng là NCC Tuấn Ngoan
  PASS  A. nhãn nguồn = TRACKING_DAILY_MIN
  PASS  B. TON_KHO thắng → 5.000.000
  PASS  B. nguồn thắng là INVENTORY:TON_KHO
  PASS  C. hết hàng → KHÔNG có giá (không phải 0)
  PASS  C. sentinel 0 KHÔNG thành giá vốn 0
  PASS  C. lợi nhuận KHÔNG bằng doanh thu
  PASS  C. Pending với lý do OUT_OF_STOCK
  PASS  D. thiếu lịch sử → Pending, lý do NO_DATA
  PASS  E. NCC báo 150 bị luật lọc → 9.500.000, không phải 150.000
  PASS  Kỳ 03/09 chỉ dùng ngày ĐÃ CHỐT → prices_are_final

=== NGÀY BÁN KHÁC, CÙNG ẢNH CHỤP ===
  bán 2026-09-10 → 6000000 VND  observed=2026-09-04 carried_from=2026-09-04 day_status=FINAL final_kỳ=True tạm=0
  PASS     ngày bán 2026-09-10 → 6000000
  PASS     mốc 10/09 nói rõ nó được mang từ 04/09
  bán 2026-09-30 → 5200000 VND  observed=2026-09-30 carried_from=None day_status=PROVISIONAL final_kỳ=False tạm=1
  PASS     ngày bán 2026-09-30 → 5200000
  PASS     ngày 30/09 còn PROVISIONAL → kỳ KHÔNG được coi là đã chốt

KẾT QUẢ SMOKE: TẤT CẢ PASS
```

Ba luồng Owner yêu cầu, đọc thẳng từ output trên:

1. **Đơn 03/09 nạp 30/09 → giá của 03/09.** `6.800.000 VND`, lợi nhuận
   `(9.000.000 − 6.800.000) × 1 = 2.200.000 VND`. Giá "hiện tại" `5.200` và
   giá `04/09` là `6.000` đều CÓ trong cùng file mà không được dùng.
2. **Một mã NCC thắng, một mã TON_KHO thắng.** `TRK-A` →
   `['SUPPLIER:Tuấn Ngoan']`. `TRK-B` → `['INVENTORY:TON_KHO']`, `5.000.000
   VND`. `TRK-E`: nhà cung cấp báo `150` nghìn cho món `9.500` nghìn (đúng sự
   cố đọc nhầm số trong ngoặc đã xảy ra thật) bị luật lọc, giá vốn `9.500.000
   VND`, nguồn bị loại còn nguyên trong `excluded_sources`.
3. **Thiếu lịch sử / hết hàng KHÔNG thành 0.** `TRK-C` (hết hàng hoàn toàn,
   sentinel `MIN = 0` phía Tracking) và `TRK-D` (chưa ai báo giá) đều ra
   `giá = None`, `lợi nhuận = None`, `price_source = Pending`, với HAI lý do
   khác nhau (`OUT_OF_STOCK` / `NO_DATA`). Không dòng nào biến mất; mọi dòng
   Pending đều có mục Review Queue canonical (`Missing.PurchasePrice`) phủ —
   `test_every_pending_line_is_covered_by_the_canonical_review_queue`.

Hai dòng cuối là hai tính chất mà chỉ ảnh chụp CẢ THÁNG mới hỏi được: mốc mang
qua nói rõ nó đến từ đâu (`carried_from=2026-09-04` cho đơn bán 10/09), và một
kỳ chạm ngày còn `PROVISIONAL` thì cờ ấy là `False`. (Hai dòng output trên
in tên cũ `prices_are_final`, đúng như lúc chạy; lượt review vòng 1 đổi tên nó
thành `resolved_prices_are_final` và thêm `period_is_final` — §11.1 #4. Output
đã trích là bản ghi lịch sử, không viết lại.)

## 7. Mốc bắt đầu lịch sử MIN, và phạm vi chưa thể backfill

**Lịch sử MIN có thẩm quyền bắt đầu từ lượt `chupMinNgay()` ĐẦU TIÊN chạy trên
production.** Tính đến bàn giao này, lượt ấy CHƯA chạy — R1 không deploy
(brief §2). Trước mốc đó không có bản ghi nào, và **không backfill được**:

- bảng giá cũ đã bị ghi đè mỗi đêm, không có ảnh chụp nào để chạy lại engine;
- `purchase_price_history`/`tp/ton` là một ĐẠI LƯỢNG KHÁC (giá công khai Owner
  đặt tay), nên dựng lịch sử MIN từ nó là đổi nhãn một con số — đúng điều
  brief §8 cấm;
- `board` hôm nay càng không dùng được: đó là "lấy bảng của hôm sau rồi gắn
  ngày hôm trước".

Đơn bán trước mốc ấy sẽ Pending với lý do `TRACKING_DAILY_MIN_PENDING` /
`SALE_DATE_OUTSIDE_CAPTURE`, hoặc dùng nguồn xác nhận tay đã có sẵn
(`HistoricalConfirmedRegistry`, `data/historical_confirmed/registry.jsonl`).
Backfill CHỈ hợp lệ nếu sau này tìm được ảnh chụp bảng giá + cấu hình đủ để
chạy lại đúng engine MIN, và khi ấy bản ghi phải mang provenance + revision
riêng của lần backfill.

## 8. Cách tắt / hoàn tác nếu có lỗi

Ba mức, từ nhẹ tới nặng, không mức nào cần sửa mã:

1. **Tắt nguồn mới ở Reports** — xoá/đổi tên
   `data/tracking_daily_min/capture.json` (hoặc không truyền
   `--tracking-daily-min`). Mọi dòng Tracking trở lại Pending với
   `TRACKING_DAILY_MIN_SOURCE_UNAVAILABLE`. KHÔNG có giá sai nào được sinh —
   không nhánh nào rơi về nguồn cũ.
2. **Bật lại nhánh cũ có chủ đích** — dựng `PriceResolutionSources(...,
   legacy_tracking_history_authority=True)`. Chỉ dùng để đối chiếu kết quả
   sinh trước R1; nó KHÔNG phải một chế độ vận hành.
3. **Dừng ghi phía Tracking** — bỏ chuỗi `"*/20 * * * *"` khỏi `[triggers]`
   trong `wrangler.toml` rồi deploy. Dữ liệu đã ghi giữ nguyên, đọc lại được;
   `min_ngay*` là nhánh MỚI, không đụng nhánh nào đang chạy.

Hoàn tác mã: `git revert` commit R1 trên từng repo. Không có migration
database nào phải hoàn tác ở cả hai bên.

## 9. Việc còn lại trước khi R1 = DONE

1. **Independent Review** (`CHECK-R1-24`) — ngân sách `2 allowed / 0 used`.
2. **Owner nghiệm thu trên dữ liệu thật** (`CHECK-R1-23`): deploy Tracking,
   mở app Bảng giá một lần để `meta.an` được đăng, chờ cron chụp ít nhất một
   ngày, rồi chạy `tools/tracking/capture_daily_min.py` và đối chiếu một vài
   đơn thật.

## 10. Đầu vào cho R2

- Provenance đã đủ cho giao diện/xuất của vòng sau: `min_sources`, `revision`,
  `rule_version`, `day_status`, `carried_from`, `source_fingerprint` — tất cả
  nằm trong `PriceResolutionRecord.daily_min_resolution`.
- `PriceResolutionReport.period_is_final` là cổng "kỳ đã chốt" (có dữ liệu +
  không Pending + không PROVISIONAL); `resolved_prices_are_final` /
  `provisional_count` là hai chỉ số hẹp hơn đi kèm. R1 cố ý KHÔNG tự gắn cổng
  ấy vào màn hình nào.
- Nối `tools/tracking/live_pull.py`: tập mã lấy từ identity đã resolve, khoảng
  ngày lấy từ preview của sổ — cả hai đã có trong pipeline, chỉ cần đảo thứ tự
  gọi (fetch giá SAU khi resolve identity, thay vì trước).
- Luồng giá tay của Owner (R2) nên tiếp tục đi qua `kpi_purchase_price_override`
  đã có, KHÔNG ghi vào nhánh MIN — `POST /api/min-ngay/sua` là đường sửa BẢN
  GHI QUAN SÁT, không phải đường nhập giá nghiệp vụ.

## 11. Lượt Independent Review vòng 1 (07/09/2026)

Bên review nêu sáu finding. Tất cả đã được xử lý và kiểm chứng; mục này ghi
từng cái, cùng bằng chứng.

### 11.1 Sáu finding và cách xử lý

| # | Finding | Vì sao nó nguy hiểm | Đã làm |
|---|---|---|---|
| 1 | `_select_captures_for_run()` không truyền `tracking_daily_min` — upload web làm MỌI mã Tracking Pending | **Finding tệ nhất của cả phiên.** Đường thật đứt trong khi 2.776 bài kiểm xanh: mọi bài đều NHẬN sẵn một capture, nên không bài nào đi qua chỗ người dùng bấm nút. Báo cáo vẫn được tạo ra, trông hoàn chỉnh, và không có một giá vốn nào | `live_pull` tự lập kế hoạch (đọc sổ → resolve identity → tập mã + khoảng ngày bán), gọi hợp đồng MỘT lượt, đóng băng capture cho lần chạy, truyền vào `SelectedCaptures`, dọn trong `finally` |
| 2 | Chọn capture cục bộ theo "mới nhất toàn cục" | Ảnh chụp MIN chỉ chứa những cặp (mã, ngày) nó đã hỏi. Mở lại sổ tháng 8 sẽ vớ phải ảnh chụp tháng 9 ⇒ cả kỳ Pending với `SALE_DATE_OUTSIDE_CAPTURE`, và người đọc đi chụp lại tháng 9 lần nữa | Chọn ảnh chụp PHỦ ĐÚNG kỳ của workbook; không có thì `None` + Pending kèm lý do "nguồn chưa nối" |
| 3 | Reader chưa fail-closed đủ | Trường thiếu bị `str(... or "")` biến thành chuỗi rỗng: giá vốn vẫn ra một con số dùng được, chỉ là không ai kiểm lại được nó — và điều đó chỉ lộ ra lúc có tranh chấp | Bắt buộc `business_timezone` đúng, `generated_at` có tz, mọi bản ghi đủ `rule_version`/`source_fingerprint`/`revision`/`recorded_at` (aware)/`recorded_by`; error phải trong khoảng và không trùng; giữ bất biến record⊕error |
| 4 | `prices_are_final` chỉ kiểm `provisional_count == 0` | Một kỳ RỖNG hoặc TOÀN Pending vẫn trả `True`. Bất kỳ cổng "kỳ đã chốt" nào xây trên đó sẽ mở ra cho đúng kỳ tệ nhất | Đổi tên thành `resolved_prices_are_final` (nghĩa hẹp, tên nói đúng) và thêm cổng `period_is_final` = có dữ liệu + không Pending + không PROVISIONAL |
| 5 | Không có gì chứng minh các trang cùng một trạng thái | Con trỏ phân trang chỉ là VỊ TRÍ trong danh sách mã; nó không đóng băng gì cả. Năm trường phong bì kia chỉ lặp lại yêu cầu vừa gửi đi nên chúng khớp nhau kể cả khi dữ liệu đã đổi hoàn toàn | Tracking thêm `min_ngay_rev` (token ngẫu nhiên, đổi sau MỌI lượt ghi, đọc TRƯỚC dữ liệu), trả `query_revision` trên từng trang; Reports đưa nó vào `TRUONG_PHONG_BI` và TỪ CHỐI gộp khi lệch |
| 6 | Smoke chưa đi qua entry point thật | Smoke cũ nhận capture cho sẵn và dùng helper của bộ kiểm, nên nó chứng minh provider/composition — đúng phần KHÔNG hỏng — và mù hoàn toàn với finding #1 | Thêm `tools/smoke/r1_web_upload_smoke.py`: máy chủ HTTP thật, `POST /run` thật, và `/api/min-ngay` được trả lời bằng CHÍNH mã Tracking (`node kiem/smoke/tra-loi-min-ngay.mjs`) |

Ba quyết định đáng chất vấn trong lượt này, ghi ra để reviewer soi đúng chỗ:

1. **Hợp đồng giá hỏng ⇒ DỪNG cả lần chạy (503), không ra báo cáo rỗng giá.**
   Từ R1, MIN theo ngày bán LÀ nguồn giá nhập tự động, nên một báo cáo mà mọi
   dòng Tracking Pending không phải "gần đúng" — nó là một báo cáo không có
   giá vốn, và nó trông y hệt một báo cáo có. Cùng khuôn `purchase_price_
   history`/`catalog` đã REQUIRED từ `S071`.
2. **Ba cảnh KHÔNG phải lỗi Tracking thì KHÔNG dừng lần chạy**, và mỗi cảnh có
   lý do riêng trong bằng chứng của run: không có sổ (`NO_SALES_WORKBOOK`),
   sổ không có dòng nào mang identity Tracking (`NO_TRACKING_IDENTITY_LINES`),
   và sổ không đọc được (`UNREADABLE_SALES_WORKBOOK` — đường nhập sổ ngay sau
   đó báo lỗi ở nơi người dùng hiểu được).

   *(Vòng 1 xếp "kỳ rộng hơn 62 ngày" vào nhóm này với lý do
   `PERIOD_WIDER_THAN_CONTRACT`. Vòng 2 bác đúng chỗ ấy — xem §12.1 finding
   #4 — vì nó cho ra một báo cáo đầy đủ hình thức mà không một giá vốn nào.)*
3. **Đọc workbook thêm MỘT lần để lập kế hoạch.** Hai đường vòng còn lại đắt
   hơn nhiều: chạy cả pipeline hai lượt, hoặc gọi hợp đồng một lượt cho mỗi
   dòng bán.

### 11.2 File đã thay đổi ở lượt này

**Tracking** (`299e031`)

| File | Nội dung |
|---|---|
| `src/min-ngay.js` | `NHANH_REV`/`REV_KHOI_DIEM`/`doiRev`/`docRev`; bump ở `chupMinNgay`, `chotNgay`, `suaBanGhi`, `ghiNgayHong`; `xuatMinNgay` đọc revision TRƯỚC dữ liệu và trả `query_revision` |
| `firebase-database.rules.json` | nhánh thứ năm `min_ngay_rev` — đọc như bốn nhánh kia, GHI = false |
| `kiem/min-ngay.js` | khối 13b (7 bài) + sửa bài dây nối ghim hình dạng → **119 bài** |
| `kiem/smoke/kho-gia.mjs` | **mới** — cổng database giả dùng chung |
| `kiem/smoke/thang-09-2026.mjs` | **mới** — kịch bản cả tháng, dựng bằng mã thật |
| `kiem/smoke/tra-loi-min-ngay.mjs` | **mới** — trả lời `POST /api/min-ngay` bằng chính `xuatMinNgay()` |
| `kiem/smoke/sinh-fixture-reports.mjs` | **mới** — producer của fixture xuyên suốt bên Reports |
| `kiem/smoke/xuat-thang-min.mjs` | dùng lại kịch bản chung; chở `query_revision` ra phong bì |

**Reports**

| File | Nội dung |
|---|---|
| `app/modules/pricing/daily_min/planning.py` | **mới** — kế hoạch hỏi giá; `DailyMinRequestPlan`, `MAX_CONTRACT_DAYS`, `UnreadableSalesWorkbookError` |
| `tools/tracking/live_pull.py` | `_pull_daily_min` (kế hoạch → hợp đồng → file tạm của lần chạy), `LiveSelectedCaptures.tracking_daily_min`, `REPO_ROOT` |
| `app/web/server.py` | `_select_captures_for_run(sales=…)` và truyền workbook từ `POST /run` |
| `app/owner_usability.py` | `select_latest_valid_captures(sales=…)`, `_select_daily_min_capture` chọn theo KỲ, `_latest_complete_capture(accepts=…)` |
| `app/modules/pricing/daily_min/snapshot.py` | `SUPPORTED_BUSINESS_TIMEZONE`; bắt buộc `generated_at`/`query_revision`; bốn trường dấu vết đọc bằng `_text` chứ không `str(... or "")`; error trong khoảng + không trùng |
| `app/modules/pricing/resolution/composition.py` | `resolved_prices_are_final` (đổi tên), `has_priceable_lines`, `period_is_final` |
| `tools/tracking/capture_daily_min.py` | `query_revision` vào `TRUONG_PHONG_BI`; từ chối gộp khi trang 1 thiếu token |
| `tools/smoke/r1_web_upload_smoke.py` | **mới** — smoke qua đúng entry point upload web |
| `tests/test_daily_min_orchestration.py` | **mới** — 19 bài: kế hoạch, chọn theo kỳ, pull-on-run |
| `tests/test_web_daily_min_integration.py` | **mới** — 5 bài: `POST /run` thật → đọc con số trong file Excel |
| `tests/test_daily_min_capture_tool.py` | **mới** — 17 bài: gộp trang và từ chối gộp |
| `tests/test_daily_min_contract.py` | 41 → **70 bài** (fail-closed từng trường) |
| `tests/test_daily_min_vertical.py` | 18 → **22 bài** (bốn hình dạng report cho cổng cấp kỳ) |
| `tests/fixtures/daily_min/tracking_contract_export.json` | sinh lại bằng `kiem/smoke/sinh-fixture-reports.mjs`; khác bản cũ ĐÚNG một trường `query_revision` |

### 11.3 Lệnh và kết quả

```text
Tracking   npm test                    60 bộ · 2713 đạt · 0 hỏng · 2 bỏ qua
           npm run build               ./dist, 7 file, 658 KB → 411 KB

Reports    python -m pytest -q         2853 passed, 12 skipped in 190.68s
                                       (trước lượt này: 2779 passed, 12 skipped)
           validate_structure          PASS (21 required paths)
           validate_project_state      PASS
           validate_evidence           PASS (161 REQUIRED PASS)
           validate_task_completion    PASS (14 DONE task)
           validate_reference_integrity FAIL — ĐÚNG 3 reference TASK-REM-T06
                                       đã biết; baseline KHÔNG đổi
```

### 11.4 Smoke qua đúng entry point người dùng

```text
python tools/smoke/r1_web_upload_smoke.py --tracking-repo /đường/dẫn/Tracking
```

Đường đi: `POST /run` (Flask thật) → `_select_captures_for_run(sales=…)` →
`live_pull` → HTTP thật tới một máy chủ cục bộ → `/api/min-ngay` trả lời bằng
`node kiem/smoke/tra-loi-min-ngay.mjs` (mã Tracking thật) → `run_owner_report`
→ pipeline → xuất Excel → mở file `.xlsx` và ĐỌC con số.

Hai cái bẫy cài sẵn: lịch sử `tp/ton` cũ CÓ giá 4.444 nghìn cho đúng những mã
ấy, và ảnh chụp CÓ giá 04/09 (6.000) lẫn 30/09 (5.200). Cả ba con số sai đều
hợp lệ về kiểu và đi lọt mọi phép nhân.

```text
TRACKING giả: http://127.0.0.1:43439  (POST /api/min-ngay ⇒ node kiem/smoke/tra-loi-min-ngay.mjs)
SỔ BÁN   ngày bán = 2026-09-03, kỳ sổ 01/09–30/09 (nạp cuối tháng)

POST /run → HTTP 302
ARTIFACT report-20260907T070445Z.xlsx
  [BH7001] giá nhập = 6800000   lợi nhuận = 2200000   nguồn = TRACKING_DAILY_MIN
  [BH7002] giá nhập = 5000000   lợi nhuận = 4000000   nguồn = TRACKING_DAILY_MIN
  [BH7003] giá nhập = None   lợi nhuận = None   nguồn = Pending
  bằng chứng run: {"daily_min_status": "COMPLETE", "daily_min_capture_id": "LIVE-DMIN-448f315d696c4a0f844f8985843514be", "daily_min_date_from": "2026-09-03", "daily_min_date_to": "2026-09-03", "daily_min_product_codes": 3, "daily_min_query_revision": "ae27706e-7303-4fe8-9e8d-27f068970071"}

=== KHẲNG ĐỊNH SMOKE ===
  PASS  hợp đồng daily-min-v1 ĐƯỢC GỌI đúng một lượt
  PASS    · và hỏi đúng tập mã suy từ sổ
  PASS    · và đúng khoảng NGÀY BÁN, không phải ngày nạp sổ
  PASS  A. đơn 03/09 nạp 30/09 → 6.800.000 (giá NGÀY BÁN)
  PASS  A. KHÔNG lấy giá hiện tại 30/09
  PASS  A. KHÔNG lấy giá ngày 04/09
  PASS  A. KHÔNG rơi về lịch sử tp/ton cũ
  PASS  A. nhãn nguồn = TRACKING_DAILY_MIN
  PASS  B. TON_KHO thắng → 5.000.000
  PASS  C. hết hàng → KHÔNG có giá (không phải 0)
  PASS  C. lợi nhuận KHÔNG bằng doanh thu
  PASS  bằng chứng run trỏ về đúng lần chụp đã định giá
  PASS  capture tạm KHÔNG ở lại trên đĩa sau lần chạy

KẾT QUẢ SMOKE: TẤT CẢ PASS
```

Smoke cũ (`tools/smoke/r1_daily_min_smoke.py`, mục 6) vẫn giữ và vẫn PASS
19/19 — nó canh provider/composition, còn smoke này canh điều phối. Hai việc
khác nhau, và finding #1 chứng minh vì sao cần cả hai.

### 11.5 SHA đầy đủ, chuỗi commit, và gói cho Independent Review

**Tracking** — `github.com/hoangvinhkta-creator/Tracking`, nhánh mặc định
`main`, nhánh làm việc `claude/kiem-tra-tham-chieu-gia-nhap-c57d7z`:

```text
BASE (main)  598b4b1390cc96e552455ab85e2c48d78198b89c
  01f505c2a9f52fb5c7f754a8d1fe42820c8a336a  R1: MIN theo ngày bán — Tracking sở hữu giá,
                                            xuất theo hợp đồng daily-min-v1
  f294edb7aa6dc16a2e1553d14f2b8043cbcdf036  R1: ghi nhật ký tiến độ cho MIN theo ngày bán
  6232ce08d69706e5404db01dc16eb4ffda46cd81  R1: chốt fail-closed cho chụp MIN ngày
                                            + sửa luật mang mốc qua ngày
  299e03142ffa5f04505ba0892448e447131bfea6  R1: token trạng thái cho phân trang MIN
                                            theo ngày + gói smoke dùng chung   ← HEAD
```

Vì sao bốn commit chứ không một: `01f505c` là bản triển khai theo brief;
`f294edb` chỉ là nhật ký tiến độ của repo Tracking, tách ra để diff mã của
`01f505c` đọc được mà không lẫn văn xuôi; `6232ce0` là lượt kiểm thử (bốn chốt
fail-closed + sửa luật mang mốc qua ngày); `299e031` là lượt review vòng 1
(token phân trang + gói smoke). Mỗi lượt một commit, đúng thứ tự thời gian —
reviewer đọc được từng bước lập luận thay vì một khối 3.345 dòng.

**Reports** — `github.com/hoangvinhkta-creator/Reports`, nhánh mặc định
`claude/extract-upload-repo-gq2ws4`, cùng nhánh làm việc:

```text
BASE         a4c00501d559bda8ec70d8fe1dc1f8e54b46d592
  2b669f5a6cd4fd07abb7713f6962b772a63e19b7  R1: giá nhập tự động là MIN theo ngày bán,
                                            đọc qua hợp đồng daily-min-v1
  78f10be431fd7fcfb6b3bde9bab5c0c8a595aea8  R1: hai bất biến toàn vẹn ảnh chụp
                                            + smoke xuyên hai hệ thống
  <commit mang chính bản bàn giao này>      R1: nối daily-min vào luồng upload web
                                            + fail-closed reader + cổng cấp kỳ   ← HEAD
```

**Gói cho reviewer kiểm trực tiếp engine, day marker, cron, correction và
Firebase rules:**

```bash
# Toàn bộ thay đổi Tracking của R1, một diff:
git -C <Tracking> diff 598b4b1390cc96e552455ab85e2c48d78198b89c..299e03142ffa5f04505ba0892448e447131bfea6

# Hoặc từng lượt:
git -C <Tracking> show 01f505c2a9f52fb5c7f754a8d1fe42820c8a336a   # engine + module ngày + route + cron + rules
git -C <Tracking> show 6232ce08d69706e5404db01dc16eb4ffda46cd81   # fail-closed + luật mang mốc
git -C <Tracking> show 299e03142ffa5f04505ba0892448e447131bfea6   # token phân trang + smoke

# Nhánh trên GitHub (cả hai repo cùng tên nhánh):
#   claude/kiem-tra-tham-chieu-gia-nhap-c57d7z
```

Năm chỗ reviewer nên mở trước, kèm nơi đọc:

| Chủ đề | File | Bộ kiểm |
|---|---|---|
| Luật MIN + nguồn thắng | `price-engine/src/nghiepvu.js` (`minCuaDong`, `nguonGiuMin`, `tinhMinNgay`) | `kiem/gia-bat-thuong.js`, `kiem/min-ngay.js` khối 1–4 |
| Bản ngày (day marker) + luật mang mốc | `src/min-ngay.js` (`chupMinNgay`, `xuatMinNgay`) | `kiem/min-ngay.js` khối 5, 11, 15b–15d |
| Cron | `src/index.js` (`CRON_MIN_NGAY`, `scheduled`), `wrangler.toml` | `kiem/min-ngay.js` khối 15, 16 |
| Sửa bản ghi (correction) | `src/min-ngay.js` (`suaBanGhi`) | `kiem/min-ngay.js` khối 9, 15e |
| Firebase rules | `firebase-database.rules.json` (5 nhánh `min_ngay*`) | `kiem/min-ngay.js` khối 15, 13b |

**Lệnh dựng lại mọi artifact được trích trong file này:**

```bash
# Fixture xuyên suốt của Reports (producer: commit Tracking 299e031)
node kiem/smoke/sinh-fixture-reports.mjs <Reports>/tests/fixtures/daily_min/tracking_contract_export.json

# Ảnh chụp cho smoke mục 6
node kiem/smoke/xuat-thang-min.mjs /tmp/smoke-capture.json
python tools/smoke/r1_daily_min_smoke.py /tmp/smoke-capture.json /tmp/smoke-run

# Smoke qua entry point upload web (mục 11.4) — cần `node` trên PATH
python tools/smoke/r1_web_upload_smoke.py --tracking-repo <Tracking>
```

Hai artifact KHÔNG tái lập byte-cho-byte, và đó là đúng: `query_revision` là
một token ngẫu nhiên mới mỗi lượt ghi, còn `generated_at` là thời điểm thật.
Mọi trường khác giống hệt nhau giữa các lần chạy.

### 11.6 Trạng thái R1 sau lượt này

`R1` GIỮ NGUYÊN `IMPLEMENTED`. Hai check còn `NOT_TESTED` không đổi và không
thể tự đổi bằng một lượt sửa mã: `CHECK-R1-24` (Independent Review PASS —
vòng 1 vừa nêu sáu finding, cả sáu đã xử lý, nhưng KẾT LUẬN review là của bên
review chứ không phải của phiên này) và `CHECK-R1-23` (Owner nghiệm thu trên
dữ liệu thật, sau lượt chụp đầu tiên trên production).


## 12. Lượt Independent Review vòng 2 (07/09/2026)

Bên review **CHƯA ACCEPT** vòng 1 và nêu thêm năm finding trên
`ddf490618a96d6f43d1cbbffbf90139c21827b0d`. Tất cả đã xử lý; mục này ghi từng
cái cùng bằng chứng. `CHECK-R1-24` VẪN `NOT_TESTED` — kết luận review là của
bên review.

### 12.1 Năm finding và cách xử lý

| # | Finding | Vì sao nó đúng | Đã làm |
|---|---|---|---|
| 1 | `pull_live_captures` lỗi sau khi đã ghi file thì bỏ lại capture trên đĩa | `cleanup()` của bên gọi CHỈ chạy khi hàm trả về một handle. Ném ra thì bên gọi không có gì để dọn, và mỗi lần hỏng lại bỏ lại thêm vài file — đúng thứ `S071 §10` cấm giữ lâu hơn một lần chạy | Toàn bộ thân hàm vào một `try`, mọi đường thoát dọn `temp_paths`. Bắt `BaseException` chứ không riêng `TrackingUnavailableError`: một lỗi KHÔNG lường trước từ tận trong kế hoạch hỏi giá cũng phải dọn |
| 2 | `query_revision` mới đọc ở MỘT đầu | Bắt được lượt ghi xen giữa hai TRANG, nhưng MÙ với lượt ghi xen vào giữa các lệnh đọc của MỘT trang: mã đọc trước mang trạng thái cũ, mã đọc sau mang trạng thái mới, phong bì vẫn nhất quán. Phân trang không liên quan | Đọc lạc quan HAI ĐẦU (token → dữ liệu → token, chỉ trả khi bằng nhau, lệch ⇒ 409 `trang-doc-khong-nhat-quan`), và con trỏ MANG THEO revision (`<rev>:<vị trí>`, lệch ⇒ 409 `cursor-lech-revision`) |
| 3 | Chọn capture cục bộ chỉ theo khoảng ngày | Hai ảnh chụp cùng kỳ có thể được chụp cho hai TẬP MÃ khác nhau (sổ nhân viên A / nhân viên B). Cả hai đều "phủ khoảng ngày"; chọn nhầm thì phần lớn dòng ra `NOT_IN_CAPTURE` — một câu trung thực nhưng nói sai vấn đề, trong khi kho ĐANG CÓ ảnh chụp trả lời được | Kế hoạch mang TỪNG CẶP `(mã, ngày)`; `covered_by` hỏi từng cặp đúng bất biến cân sổ của hợp đồng. Cặp nằm ở `errors` VẪN tính là đã trả lời |
| 4 | `PERIOD_WIDER_THAN_CONTRACT` cho ra báo cáo thiếu toàn bộ giá vốn | Kết cục tệ nhất trong ba kết cục có thể — tệ hơn cả một lỗi, vì nó trông giống thành công | Chia kỳ thành các đoạn ≤ 62 ngày, hỏi từng đoạn, gộp CHỈ khi mọi đoạn cùng `query_revision` (`gop_khoang`). Lệch ⇒ 503 (thoáng qua, thử lại có tác dụng). Rộng quá trần đoạn mỗi lần chạy (12 ≈ hai năm) ⇒ **400 kèm hướng dẫn TÁCH KỲ**, không phải "thử lại sau" |
| 5 | `purchase_price_history` còn REQUIRED trong khi thẩm quyền đã là daily MIN | Đúng: nhánh của một mã Tracking đi qua `_daily_min_branch`, và đường lịch sử chỉ chạy khi caller nêu rõ `legacy_tracking_history_authority=True`. Giữ nó REQUIRED là bắt báo cáo hôm nay phụ thuộc vào một nguồn hôm nay không dùng | Thôi REQUIRED ở CẢ hai luồng (web pull-on-run và chọn capture cục bộ). Vẫn được chụp, vẫn vào bằng chứng khi có mặt; vắng mặt thì bằng chứng NÓI RA (`purchase_price_history_status`). Danh mục Tracking VẪN REQUIRED |

**Xác định lại vai trò nguồn cũ (finding #5), có dẫn chứng mã.** Đường quyết
định giá của một mã Tracking:

```text
composition._tracking_branch()
  if not sources.legacy_tracking_history_authority:      # mặc định False
      return self._daily_min_branch(...)                 # ← mọi lần chạy đi lối này
  ...                                                    # TrackingHistoryPriceProvider
```

`self._reader` (đọc `purchase_price_history`) chỉ được dùng bên trong nhánh
`legacy` ấy và trong `_build_tracking_provider`. Không có đường nào khác chạm
tới nó. Nên nguồn cũ hôm nay là **audit/legacy**: giữ để đối chiếu kết quả sinh
trước R1, và để một caller nêu rõ cờ có thể dựng lại chúng.

**Ba bài kiểm bị đổi mong đợi** (chỗ reviewer nên soi trước):
`test_purchase_price_history_failure_is_required_and_raises` và hai bài
timeout/403 trong `tests/test_tracking_live_pull.py`. Chúng được viết ở `S071`,
khi lịch sử `tp/ton` CÒN là nguồn giá — lúc ấy REQUIRED là đúng. R1 đổi thẩm
quyền ấy, nên chúng nay ghim hành vi mới (ghi lý do vào bằng chứng, lần chạy đi
tiếp) và mang tên mới. Bài đối chứng cho danh mục (`catalog`) giữ nguyên
REQUIRED, không đụng.

### 12.2 File đã thay đổi ở lượt này

**Tracking** (`0442e62`)

| File | Nội dung |
|---|---|
| `src/min-ngay.js` | đọc lạc quan hai đầu (`revTruoc`/`revSau`); con trỏ `<rev>:<vị trí>` và từ chối con trỏ lệch revision |
| `kiem/min-ngay.js` | khối 13b viết lại: 119 → **126 bài** |
| nhật ký tiến độ của repo Tracking | mô tả lại cơ chế và số liệu kiểm |

**Reports**

| File | Nội dung |
|---|---|
| `tools/tracking/live_pull.py` | thân tách thành `_pull` + `try/except BaseException` dọn `temp_paths`; chia kỳ thành đoạn ≤ 62 ngày và gộp theo `query_revision`; `DailyMinPeriodTooWideError`; `MAX_CONTRACT_WINDOWS`; lịch sử `tp/ton` thôi REQUIRED |
| `tools/tracking/capture_daily_min.py` | `gop_khoang` + `TRUONG_CHUNG_KHOANG` — gộp nhiều ĐOẠN NGÀY, chỉ khi cùng revision |
| `app/modules/pricing/daily_min/planning.py` | `pairs` trong kế hoạch; `contract_windows()`; `covered_by` hỏi từng cặp |
| `app/owner_usability.py` | `SelectedCaptures.tracking_capture` thành `Optional`; lịch sử chọn với `required=False` |
| `app/demo.py` | `tracking_capture` thành tham số TUỲ CHỌN |
| `app/modules/exporting/excel_exporter.py` | ô tóm tắt nói "Không nối" thay vì để trống khi thiếu capture legacy |
| `app/web/server.py` | bắt `DailyMinPeriodTooWideError` → 400 kèm hướng dẫn tách kỳ |
| `tests/test_daily_min_orchestration.py` | 19 → **33 bài** (cặp mã-ngày, chia đoạn, dọn dẹp, nguồn legacy) |
| `tests/test_daily_min_capture_tool.py` | 17 → **28 bài** (gộp đoạn) |
| `tests/test_web_daily_min_integration.py` | 5 → **7 bài** (kỳ quá rộng, legacy hỏng) |
| `tests/test_tracking_live_pull.py` | ba bài đổi mong đợi theo thẩm quyền mới của R1 |

### 12.3 Lệnh và kết quả

```text
Tracking   npm test                    60 bộ · 2720 đạt · 0 hỏng · 2 bỏ qua
           npm run build               ./dist, 7 file, 658 KB → 411 KB

Reports    python -m pytest -q         2880 passed, 12 skipped in 158.27s
                                       (trước vòng 2: 2853 passed, 12 skipped)
           validate_structure          PASS (21 required paths)
           validate_project_state      PASS
           validate_evidence           PASS (161 REQUIRED PASS)
           validate_task_completion    PASS (14 DONE task)
           validate_reference_integrity FAIL — ĐÚNG 3 reference TASK-REM-T06
                                       đã biết; baseline KHÔNG đổi
```

Hai smoke chạy lại trên mã đã sửa, cả hai PASS:

```text
node kiem/smoke/xuat-thang-min.mjs /tmp/smoke-capture.json
python tools/smoke/r1_daily_min_smoke.py /tmp/smoke-capture.json /tmp/rv2
  → 19/19 PASS

python tools/smoke/r1_web_upload_smoke.py --tracking-repo <Tracking>
  → 13/13 PASS
  bằng chứng run: {"daily_min_status": "COMPLETE", "daily_min_capture_id":
  "LIVE-DMIN-b07fc11a1bf24a12865e0358ecae05cb", "daily_min_date_from":
  "2026-09-03", "daily_min_date_to": "2026-09-03", "daily_min_product_codes": 3,
  "daily_min_windows": 1, "daily_min_query_revision":
  "245a6e02-17a4-47c8-805d-facc3c357588"}
```

Fixture xuyên suốt sinh lại bằng `kiem/smoke/sinh-fixture-reports.mjs` trên
commit Tracking `0442e62`; `tests/test_daily_min_vertical.py` 22/22 PASS trên
bản sinh mới.

### 12.4 Ba chỗ CỐ Ý không làm, và lý do

1. **Không tự thử lại khi các đoạn lệch revision.** Một vòng lặp thử lại giấu
   bên trong sẽ biến một database đang bận thành một lần chạy treo. Bên gọi
   biết nó đang ở trong ngữ cảnh nào và quyết định được; ở web, đó là một 503
   mà thử lại thật sự có tác dụng.
2. **Không nâng trần 62 ngày phía Tracking.** Trần ấy có lý do riêng (một
   Worker, một hạn mức subrequest); nâng nó để tránh chia đoạn là đổi một vấn
   đề nhìn thấy được lấy một vấn đề chết giữa chừng.
3. **Không bỏ hẳn `purchase_price_history` khỏi lần chạy.** Nó vẫn được chụp
   và vẫn vào bằng chứng: đối chiếu kết quả sinh trước R1 là một việc thật, và
   `legacy_tracking_history_authority=True` vẫn là đường được hỗ trợ.

### 12.5 SHA sau vòng 2

```text
Tracking   0442e62a8f701693cae1a983baec59f505e49abd   ← HEAD
             ← 299e03142ffa5f04505ba0892448e447131bfea6 (vòng 1)
             ← 6232ce08d69706e5404db01dc16eb4ffda46cd81 (kiểm thử)
             ← 01f505c2a9f52fb5c7f754a8d1fe42820c8a336a (triển khai)
             ← f294edb7aa6dc16a2e1553d14f2b8043cbcdf036 (nhật ký)
             BASE main 598b4b1390cc96e552455ab85e2c48d78198b89c

Reports    <commit mang chính bản bàn giao này>        ← HEAD
             ← ddf490618a96d6f43d1cbbffbf90139c21827b0d (vòng 1)
             ← 78f10be431fd7fcfb6b3bde9bab5c0c8a595aea8 (kiểm thử)
             ← 2b669f5a6cd4fd07abb7713f6962b772a63e19b7 (triển khai)
             BASE a4c00501d559bda8ec70d8fe1dc1f8e54b46d592
```

Gói cho reviewer (mục 11.5) không đổi cách dùng; chỉ thay mốc cuối:

```bash
git -C <Tracking> diff 598b4b1390cc96e552455ab85e2c48d78198b89c..0442e62a8f701693cae1a983baec59f505e49abd
git -C <Tracking> show 0442e62a8f701693cae1a983baec59f505e49abd   # đọc lạc quan + con trỏ
```

### 12.6 Trạng thái R1 sau vòng 2

`R1` GIỮ NGUYÊN `IMPLEMENTED`. `CHECK-R1-24` (Independent Review) VẪN
`NOT_TESTED`: vòng 2 chưa ACCEPT, và kết luận review là của bên review chứ
không phải của phiên này. `CHECK-R1-23` (Owner nghiệm thu trên dữ liệu thật)
không đổi.
