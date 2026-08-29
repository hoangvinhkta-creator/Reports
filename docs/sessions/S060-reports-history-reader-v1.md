# S060 — REPORTS HISTORY READER V1 (Session 1/2)

Nhánh Reports: `claude/reports-history-reader-v1-pnjhdr`
Base SHA: `c1a8cd03e9c454b33b4d9efb3f6e7fbbaccf3e01` (S059, "Batch 50 Real
Orders"). Xác nhận `git rev-parse HEAD` == base khi mở phiên, working tree
sạch.

**Ghi chú về tên nhánh.** Chỉ thị mở phiên nêu nhánh làm việc
`implementation/reports-history-reader-v1`, nhưng harness của Claude Code on
the web đã cấp và ràng buộc phiên này vào nhánh
`claude/reports-history-reader-v1-pnjhdr` (chỉ thị hệ thống: "NEVER push to a
different branch"). Hai chỉ thị mâu thuẫn ở đúng một điểm là TÊN nhánh; cả
hai đồng ý về base SHA, về việc không đụng nhánh mặc định, và về việc không
merge. Phiên chọn nhánh do harness cấp vì đó là nhánh duy nhất phiên này có
quyền đẩy. Không phải `TARGET_AMBIGUITY`: base authority khớp chính xác, chỉ
nhãn nhánh khác.

Nhánh Tracking: `claude/pph-server-timestamp-authority-v1`
Base (accepted main): `91e57a0020088935ec11cc615932d4987eb39c71`
Final SHA: `1821af064694958dc4208b11679f5c787359d461`
`main` (local và `origin/main`) vẫn nguyên `91e57a00…` — không sửa, không
merge.

## 1. Blocker đã xử lý — thẩm quyền dấu thời gian

Trace mã production thật (không đọc tài liệu):

```text
Tracking public/index.html  admBaselineSnapshot()
    t: firebase.database.ServerValue.TIMESTAMP      → MÁY CHỦ gán

Tracking public/index.html  savePpHist()            (trước repair)
    const t = Date.now()                            → MÁY TRẠM gán

firebase-database.rules.json purchase_price_history (trước repair)
    chỉ có `.write` = "!data.exists() && <quyền>"
    KHÔNG có `.validate` nào cho `t`
```

Kết luận: `t` của lịch sử hoàn toàn do client kiểm soát, không có chặn trên,
không có chặn dưới, và không có luật máy chủ nào ràng buộc. **Không tồn tại
bằng chứng nào chứng minh thẩm quyền của nó** — nên nhánh "chứng minh mà
không cần sửa" bị loại bằng bằng chứng, không bằng phỏng đoán.

Một lối tắt đã bị TỪ CHỐI có chủ ý: khoá `push()` của Firebase có nhúng thời
gian đã hiệu chỉnh theo `serverTimeOffset` của SDK. Đó là hành vi SDK, không
phải khẳng định được rules kiểm, và dựa vào nó là dựng thẩm quyền trên một
chi tiết cài đặt. Ghi nhận làm bằng chứng chẩn đoán, KHÔNG cấp thẩm quyền.

### Repair phía Tracking (minimal, local)

1. `savePpHist()` nhánh CLOUD: `t: ServerValue.TIMESTAMP` + `ta: "SERVER"`.
2. Rules `purchase_price_history/$ma/$eid/.validate`:
   `newData.child('t').val() === now && newData.child('ta').val() === 'SERVER'`
   → client không tự dán được nhãn `SERVER`.
3. Nhánh ngoại tuyến giữ `Date.now()` nhưng **tự khai** `ta: "CLIENT"`.

Không rewrite sự kiện cũ; `.write` vẫn `!data.exists()` nên append-only
nguyên vẹn; sự kiện cũ thiếu `ta` → `UNVERIFIED_CLIENT` → Pending phía đọc.
Không nâng thẩm quyền ngược cho quá khứ.

Không deploy. Không merge. Branch riêng, đã push.

## 2. Reader — hợp đồng và thuật toán

`app/modules/pricing/tracking_history/`
- `snapshot.py` — hợp đồng dữ liệu chỉ đọc + kiểm toàn vẹn lúc nạp.
- `reader.py` — thuật toán tái dựng + ngữ nghĩa biên.
- `provider.py` — adapter `PriceProvider`, KHÔNG bao giờ là mặc định.

Thuật toán, theo thứ tự cổng (mỗi cổng fail-safe sang Pending):

```text
1  baseline tồn tại + thẩm quyền SERVER            ngược lại → Pending
2  interval.lo >= baseline.t                        ngược lại → SALE_BEFORE_CUTOVER
3  MỌI sự kiện của mã đều ta="SERVER"               ngược lại → HISTORY_PROVENANCE_NOT_AUTHORITATIVE
4  không sự kiện nào TRÙNG KHÍT baseline.t          ngược lại → EVENT_AT_CUTOVER_INSTANT
5  không hai sự kiện cùng mã trùng dấu thời gian    ngược lại → NON_DETERMINISTIC_EVENT_ORDER
6  không sự kiện nào trong (lo, hi)                 ngược lại → PRICE_CHANGED_WITHIN_SALE_INTERVAL
7  mã vắng baseline khi nInvalid>0                            → BASELINE_ABSENCE_AMBIGUOUS
8  khoá chuỗi prev: baseline → sự kiện đầu tiên sau lo
                                                    lệch    → HISTORY_CHAIN_INCONSISTENT
9  trạng thái tại lo:  không sự kiện → giá baseline (thiếu → NO_BASELINE_PRICE_AT_CUTOVER)
                       có sự kiện    → next của sự kiện cuối (null → PRICE_CLEARED)
10 giá VND = giá nghìn VND × 1000
```

Sự kiện có `t < baseline.t` bị chính ảnh chụp cutover thay thế (baseline là
một lần đọc THẲNG `board` tại `t0`) nên không tham gia chuỗi.

### Vì sao reader nhận một KHOẢNG chứ không một thời điểm

Tracking đóng dấu theo mili-giây; Reports chỉ có `WorkingLine.date` — độ phân
giải NGÀY, không có giờ. Ép một ngày thành một thời điểm là phát minh dữ
liệu. Reader nhận `SaleInterval [lo, hi)` và chỉ trả giá khi trạng thái **hằng
trên toàn khoảng**. Một ngày bán = `[00:00, 00:00 hôm sau)` theo múi giờ
nghiệp vụ, và múi giờ là tham số **bắt buộc**, không có mặc định.

Đây là một BLOCKER thật được phát hiện trong phiên và đã xử lý trong phiên,
không phải một finding để lại.

### Ngữ nghĩa biên chính xác

| Tình huống | Kết quả |
|---|---|
| `sale_time == baseline.t` | dùng giá baseline (mốc có hiệu lực TẠI chính nó) |
| `sale_time = baseline.t - 1ms` | Pending — `SALE_BEFORE_CUTOVER` |
| ngày bán chứa `baseline.t` ở giữa | Pending — `SALE_BEFORE_CUTOVER` |
| `event.t == interval.lo` | ÁP DỤNG (sự kiện hiệu lực tại chính nó) |
| `event.t == interval.hi` | KHÔNG áp dụng (`hi` là đầu MỞ) |
| `lo < event.t < hi` | Pending — `PRICE_CHANGED_WITHIN_SALE_INTERVAL` |
| `event.t == baseline.t` | Pending — `EVENT_AT_CUTOVER_INSTANT` |
| hai sự kiện cùng mã, cùng `t` | Pending — `NON_DETERMINISTIC_EVENT_ORDER` |
| hai sự kiện KHÁC mã, cùng `t` | bình thường (một lượt sync ghi nhiều mã) |

Không có heuristic thứ tự nào được tạo ra. Schema V1 không mang bằng chứng
thứ tự nào ngoài `t`, nên trùng `t` là fail-safe chứ không phải đoán.

## 3. Đơn vị

`THOUSAND_VND_TO_VND = Decimal(1000)`, dùng ĐÚNG MỘT lần trong toàn package
(`reader._resolved`). Provenance mang CẢ `raw_value_thousand_vnd` lẫn
`resolved_price_vnd` — người đọc thấy phép quy đổi đã xảy ra chứ không phải
tin rằng nó đã xảy ra.

## 4. Product Identity — không đụng

`CUTOVER_DATE = 2026-09-01` KHÔNG đổi. Mốc giá Tracking
(`29/08/2026 19:35:37`, một `datetime` có múi giờ) và mốc identity
(`01/09/2026`, một `date`) là hai khái niệm khác kiểu; test khẳng định Python
từ chối so sánh trực tiếp hai giá trị ấy, nên không có đường nào âm thầm hợp
nhất chúng. Khoảng 29/08 → 31/08 KHÔNG được dùng làm lý do dời `01/09`.

Reader chỉ phục vụ `TRACKING:<mã>`. `PUBLIC_PURCHASE:<mã>` → Pending
(`IDENTITY_NOT_TRACKING`), kể cả khi mã trùng chuỗi với một mã CÓ giá trong
baseline. Provider **được trao** identity qua `identity_index`; nó không suy
mã từ tên hàng (`D-04`/`DEC-147` §4).

## 5. Điểm tích hợp pipeline

`app/pipeline.py` KHÔNG đổi. Provider đi vào qua tham số `price_provider` đã
có sẵn của `run_import()`, đúng tiền lệ `FilePriceProvider` (`TASK-105B`,
`CHECK-105-04`): mặc định vẫn là `PendingPriceProvider`, caller phải dựng và
truyền tường minh. `app/composition.py` (`run_import_production`) KHÔNG được
nối reader — composition P00–P11 thuộc `TASK-105E` và task đó vẫn `PLANNED`.

Một thay đổi nhỏ ở `app/modules/pricing/price_engine.py`: provider được phép
tự khai nhãn nguồn qua thuộc tính lớp `price_source`. Provider không khai giữ
nguyên `PriceMaster` như cũ, nên Golden không đổi hành vi. Lý do phải sửa:
gắn nhãn `PriceMaster` cho một giá tái dựng theo thời gian là một lời khai
SAI về nguồn, và nhãn nguồn chính là thứ người kiểm dùng để quyết có tin con
số hay không.

## 6. Review Queue

KHÔNG tạo hàng chờ mới. Pending → `accounting_purchase_price = None` +
`price_source = "Pending"` → luật `detect_missing_purchase_price` hiện hành
sinh mục `Missing.PurchasePrice` của `TASK-110`. Test khẳng định mọi dòng
Pending đều được một mục Review Queue phủ (mức DÒNG, không chỉ mức đơn) và
dòng đã resolve KHÔNG lọt vào hàng chờ.

`ORDER_ACCOUNTING_RATE` giữ 100%, `SILENTLY_DROPPED = 0`,
`PENDING_NOT_QUEUED = 0` — chạy lại chính `tools/analysis/batch_50_real_orders.py`.

## 7. Files changed

Reports (production):
- `app/modules/pricing/tracking_history/__init__.py` (mới)
- `app/modules/pricing/tracking_history/snapshot.py` (mới)
- `app/modules/pricing/tracking_history/reader.py` (mới)
- `app/modules/pricing/tracking_history/provider.py` (mới)
- `app/modules/domain/models.py` (+1 hằng số)
- `app/modules/pricing/price_engine.py` (+1 dòng, +1 dòng đổi)

Reports (test/doc): `tests/test_tracking_history_reader.py`,
`tests/test_tracking_history_pipeline.py`,
`tests/test_tracking_history_batch50_semantics.py`, doc này,
`PROJECT/PROJECT_PROGRESS.md`.

Tracking: `public/index.html`, `firebase-database.rules.json`,
`kiem/lich-su-gia-nhap.js`.

## 8. Kết quả test

```text
Reports focused  tests/test_tracking_history_reader.py            52 passed
Reports focused  tests/test_tracking_history_pipeline.py           9 passed
Reports focused  tests/test_tracking_history_batch50_semantics.py  5 passed
Reports Golden   tests/test_golden_baseline.py         58 passed, 2 skipped
Reports Golden   #1/#3/#4 + safe-pending               74 passed, 2 skipped
Reports FULL     python -m pytest                    1107 passed, 11 skipped
                 (base: 1041 passed, 11 skipped — +66, 0 hồi quy)

Tracking focused kiem/lich-su-gia-nhap.js       53 đạt (base 38), 0 hỏng
Tracking FULL    node kiem/chay.js   55 bộ · 2286 đạt · 0 hỏng · 2 bỏ qua
                 (base: 2271 đạt — +15, 0 hồi quy)
Tracking build   npm run build → dist dựng được, 632 KB → 400 KB
```

## 9. Blocker đã xác nhận (còn mở, KHÔNG chặn phiên này)

- **B-01 — Sự kiện lịch sử đã ghi trước repair vĩnh viễn không đủ thẩm
  quyền.** Chúng thiếu `ta` và không được viết lại. Mọi mã có ít nhất một sự
  kiện như vậy sẽ Pending cho tới khi có một artifact thẩm quyền do Owner xác
  nhận (cùng hạng `HistoricalConfirmedRegistry`). Đây là kết quả ĐÚNG theo
  `SILENT_ERROR_RATE = 0`, không phải một khiếm khuyết cần lách.
- **B-02 — Độ phủ chỉ mở ra sau khi repair Tracking được deploy.** Phiên này
  không deploy (ngoài phạm vi). Trước deploy, độ phủ thực tế của reader =
  các mã KHÔNG có sự kiện lịch sử nào (dùng thẳng giá baseline).
- **B-03 — Reports không có giờ bán.** Một ngày có thay đổi giá ở giữa là
  Pending theo thiết kế. Nâng độ phân giải `sale_date` là thay đổi data
  contract, thuộc Owner.

## 10. Phạm vi hoãn (ghi vào task/capability đang có, KHÔNG sinh task mới)

- Công cụ capture RTDB → file snapshot bất biến (`tools/`, ngoài
  `app/modules/` theo `ADR-101`/`DEC-152` §6). Reader nhận hình dạng export
  đã định nghĩa; công cụ chưa viết vì phiên này không có mạng tới Firebase.
- Nối reader vào `run_import_production` và thứ tự ưu tiên nguồn giá P00–P11:
  thuộc `TASK-105E` (`PLANNED`, `DEC-156` §5). Không lấn.
- Deploy rules + `public/index.html` phía Tracking: thuộc quy trình vận hành
  Tracking.

## 11. Trạng thái

Implementation PASS. **KHÔNG tuyên bố DONE** — capability cần independent
review (Session 2) và cần deploy Tracking trước khi nói được bất cứ điều gì
về độ phủ production.
