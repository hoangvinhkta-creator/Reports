# S126 — Bàn giao R1: Giá MIN theo ngày bán

Phiên IMPLEMENTATION + KIỂM THỬ, hai repo. Owner authority: `R1 Execution
Brief — Giá MIN theo ngày bán` (2026-09-07). Quyết định: `DEC-199`. Kiến trúc:
`ADR-110`. Task canonical: `docs/tasks/R1-daily-min-theo-ngay-ban.md`.

File này gộp cả hai lượt của cùng một phiên: lượt triển khai, và lượt kiểm
thử/sửa lỗi ngay sau đó (mục 5.1 và mục 6). Bảy chỗ sửa ở lượt sau đều là lỗi
KHÔNG ném ngoại lệ — chúng cho ra một con số tiền trông hoàn toàn bình thường,
và đó là lớp lỗi đắt nhất trong một hệ giá vốn.

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
số suốt đường; kỳ còn dùng bản tạm thì `PriceResolutionReport.prices_are_final`
là `False`.

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
| `app/modules/pricing/resolution/composition.py` | nhánh `_daily_min_branch`, `CompositionRule.TRACKING_DAILY_MIN`, hai reason mới, `report`/`prices_are_final` |
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
kỳ chạm ngày còn `PROVISIONAL` thì `prices_are_final = False`.

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
- `PriceResolutionReport.prices_are_final` / `provisional_count` sẵn cho cổng
  "kỳ đã chốt". R1 cố ý KHÔNG tự gắn nó vào cổng UI nào.
- Nối `tools/tracking/live_pull.py`: tập mã lấy từ identity đã resolve, khoảng
  ngày lấy từ preview của sổ — cả hai đã có trong pipeline, chỉ cần đảo thứ tự
  gọi (fetch giá SAU khi resolve identity, thay vì trước).
- Luồng giá tay của Owner (R2) nên tiếp tục đi qua `kpi_purchase_price_override`
  đã có, KHÔNG ghi vào nhánh MIN — `POST /api/min-ngay/sua` là đường sửa BẢN
  GHI QUAN SÁT, không phải đường nhập giá nghiệp vụ.
