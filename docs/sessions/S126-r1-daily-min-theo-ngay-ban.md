# S126 — Bàn giao R1: Giá MIN theo ngày bán

Phiên IMPLEMENTATION, hai repo. Owner authority: `R1 Execution Brief — Giá MIN
theo ngày bán` (2026-09-07). Quyết định: `DEC-199`. Kiến trúc: `ADR-110`. Task
canonical: `docs/tasks/R1-daily-min-theo-ngay-ban.md`.

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
    HỢP LỆ khi và chỉ khi mọi ngày trong (R, D] đều có BẢN NGÀY.

MIN = rẻ nhất trong:
        · giá các nhà cung cấp còn hàng, sau khi loại danh sách bị ẩn/nghỉ/
          không-tính-Min và sau bộ lọc giá thấp bất thường (< 30% giá kế tiếp)
        · ô Tồn Tín Phát khi nó dương
Không có nguồn nào bán được, nhưng đã từng có → OUT_OF_STOCK  (giá null)
Chưa nhà cung cấp nào đụng tới mã                → NO_DATA       (giá null)
Ngày không quan sát được / chuỗi ngày đứt        → SOURCE_UNAVAILABLE
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

### Tracking (commit `01f505c`)

| File | Nội dung |
|---|---|
| `price-engine/src/nghiepvu.js` | `nguonGiuMin()`; `minCuaDong()` trả thêm nguồn; `tinhMinNgay()`; `TON_KHO`, `PHIEN_BAN_MIN`, `TRANG_THAI_GIA`. `PHIEN_BAN` GIỮ `pe-6` — kết quả giá không đổi |
| `price-engine/src/index.js` | RPC `tinhMinNgay()` |
| `src/min-ngay.js` | **mới** — chụp/chốt/sửa/xuất, chuỗi bản ngày, vân tay đầu vào |
| `src/index.js` | `xuatMinChoReports()`, ba route admin, cron thứ ba, `CRON_MIN_NGAY` |
| `public/index.html` | `congBoVanTay()` đăng thêm `meta.an` (danh sách NCC bị bỏ, dạng chuỗi) |
| `firebase-database.rules.json` | bốn nhánh mới: đọc như nhánh giá nhập cũ, GHI = false |
| `wrangler.toml` | cron thứ ba `*/20 * * * *` |
| `kiem/min-ngay.js` | **mới** — 93 bài |
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
| `tests/test_daily_min_contract.py` | **mới** — 38 bài |
| `tests/test_daily_min_vertical.py` | **mới** — 18 bài, chạy trên fixture do Tracking sinh |
| `tests/fixtures/daily_min/tracking_contract_export.json` | **mới** — sinh bằng chính mã Tracking |
| `tests/test_105e_price_composition.py`, `tests/test_post_cutover_validation.py`, `tests/test_demo.py`, `tests/test_sales_presentation.py` | ghim nhánh legacy / chuyển sang nguồn mới / cập nhật vũ trụ mã đóng |
| governance | `ADR-110`, `DEC-199`, task R1, ledger, `PROJECT/PROJECT_PROGRESS.md` |

**Migration: KHÔNG CÓ.** Không backfill, không đổi nhãn dữ liệu cũ, không
migration database bên Reports.

## 5. Test, build, validator — kết quả chính xác

```text
Tracking  npm test   (nền)  59 bộ · 2594 đạt · 0 hỏng · 2 bỏ qua
          npm test   (sau)  60 bộ · 2687 đạt · 0 hỏng · 2 bỏ qua
          npm run build     "Đã dựng bản phục vụ vào ./dist
                             7 file, xén chú thích 1 file HTML
                             658 KB → 411 KB  (bớt 37%)"

Reports   pytest -q  (nền)  2720 passed, 12 skipped in 143.78s
          pytest -q  (sau)  2776 passed, 12 skipped in 147.83s
          bài mới: 93 (Tracking) + 56 (Reports)

Governance validator (Reports)
          validate_structure          PASS  (21 required paths)
          validate_project_state      PASS
          validate_evidence           PASS  (161 REQUIRED PASS)
          validate_task_completion    PASS  (14 DONE task)
          validate_reference_integrity FAIL — ĐÚNG 3 reference TASK-REM-T06
                                      đã biết (/README.md, CODE_OF_CONDUCT.md,
                                      CONTRIBUTING.md). Baseline KHÔNG đổi.
```

Một bộ Tracking hỏng giữa chừng trong phiên này (`day-ton-sheet.js`, 2 bài) và
bảng tổng kết vẫn báo "Tất cả đạt" — vì `kiem/chay.js` chỉ đọc DÒNG CUỐI của
đầu ra, mà một bộ trượt kèm cảnh báo stderr thì dòng cuối không còn là dòng
tổng kết, và nhánh dự phòng `/BỎ QUA/` khớp trúng tên một bài. Đã vá; ghi ra
đây vì nó là một lỗ hổng bằng chứng, không phải một phiền toái.

## 6. Ba smoke result

**(1) Đơn cũ đúng ngày.** `test_a_sale_on_03_09_is_priced_with_the_03_09_mark`
+ `test_a_price_from_a_different_day_is_never_used`. Ảnh chụp chứa `TRK-A` =
6.800 (nghìn) ở 03/09 và 6.000 ở 04/09. Đơn bán 03/09 ra
`accounting_purchase_price = 6.800.000 VND`; đơn bán 04/09 ra `6.000.000 VND`.
Lợi nhuận đi tiếp đúng: `(9.000.000 − 6.800.000) × 1 = 2.200.000 VND`.

**(2) NCC thắng / Tồn thắng.** `TRK-A` → `min_sources = ("SUPPLIER:Tuấn
Ngoan",)`. `TRK-B` (Tồn 5.000 rẻ hơn mọi nhà cung cấp) → `5.000.000 VND` với
`min_sources = ("INVENTORY:TON_KHO",)`. Đồng giá giữ ĐỦ nguồn, thứ tự ổn định,
Tồn đứng cuối (`kiem/min-ngay.js` mục 1). `TRK-E`: một nhà cung cấp báo 150
nghìn cho món 9.500 nghìn (đúng sự cố đọc nhầm số trong ngoặc đã xảy ra thật)
→ bị luật lọc, MIN = `9.500.000 VND`, và nguồn bị loại còn nguyên dấu vết
trong `excluded_sources`.

**(3) Thiếu giá KHÔNG thành 0.** `TRK-C` hết hàng hoàn toàn →
`accounting_purchase_price = None`, `accounting_profit = None`,
`price_source = "Pending"`, lý do `OUT_OF_STOCK`. `TRK-D` chưa có dữ liệu →
`NO_DATA`. Mọi dòng Pending đều có mục Review Queue canonical
(`Missing.PurchasePrice`) phủ. Không dòng nào biến mất, không con số nào bị
bịa.

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
